"""Module API for ``HumanConfirmation@1``: validate, verify_artifacts, CLI.

Validation order mirrors the envelope package (spec ``02`` §8, Phase B
convention):

1. schema (pydantic model; unknown closed-vocabulary values name themselves),
2. invariants (spec ``06`` §2 counts / §5 honesty pricing),
3. hashes + artifact coverage (§3 — only when ``verify_artifacts=True``).

Refusals reuse the *frozen* envelope registry codes only —
``INVALID_OUTPUT``, ``BLOCKED_INPUT``, ``PARENT_HASH_MISMATCH``, plus
``SCOPE_VIOLATION`` for out-of-root paths (all read-only imports; the registry
enum is never modified here). The export gate (§4) is implemented in this
module as ``export_gate`` and refuses with ``REFUSED_UNSUPPORTED``; the
bound ``scholar-harness export --claim-confirmed`` path surfaces it.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any

from pydantic import ValidationError

from ..canonical import canonical_json_bytes
from ..envelope.registry import RefusalCode
from .model import SCHEMA_NAME, DecisionRow, HumanConfirmation

#: Timing metadata deliberately excluded from any identity digest (spec `06`
#: §2, reusing the Phase B convention). This module computes no identity digest
#: of its own, so the exclusion is structural: nothing derived from this
#: record ever covers ``created_at``.
TIMING_METADATA_FIELDS = ("provenance.created_at",)


class ConfirmationRefusalError(Exception):
    """Raised with the *right* refusal code, never a generic wrapper."""

    def __init__(self, refusal_code: RefusalCode | str, detail: str) -> None:
        self.refusal_code = refusal_code
        self.code = refusal_code
        self.detail = detail
        super().__init__(f"{refusal_code}: {detail}")


# ---------------------------------------------------------------------------
# Loading and schema step
# ---------------------------------------------------------------------------


def _load(
    record: Mapping[str, Any] | str | bytes | Path,
) -> dict[str, Any]:
    if isinstance(record, Mapping):
        return dict(record)
    try:
        if isinstance(record, Path):
            text = record.read_text(encoding="utf-8")
        elif isinstance(record, bytes):
            text = record.decode("utf-8")
        else:
            text = record
    except (OSError, UnicodeDecodeError) as exc:
        raise ConfirmationRefusalError(
            RefusalCode.INVALID_OUTPUT, f"confirmation file unreadable: {exc}"
        ) from exc
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfirmationRefusalError(
            RefusalCode.INVALID_OUTPUT,
            f"confirmation is not valid JSON: {exc}",
        ) from exc
    if not isinstance(value, dict):
        raise ConfirmationRefusalError(
            RefusalCode.INVALID_OUTPUT, "confirmation must be a JSON object"
        )
    return value


def _schema_step(payload: dict[str, Any]) -> HumanConfirmation:
    name = payload.get("schema")
    if name != SCHEMA_NAME:
        # Named refusal for a schema near-miss (e.g. "HumanConfirmation@2"):
        # a typo must fail loudly, never validate as a different version.
        raise ConfirmationRefusalError(
            RefusalCode.INVALID_OUTPUT,
            f"schema {name!r} is not {SCHEMA_NAME!r} "
            "(a near-miss schema name is a defect, not a version)",
        )
    try:
        return HumanConfirmation.model_validate(payload)
    except ValidationError as exc:
        raise ConfirmationRefusalError(
            RefusalCode.INVALID_OUTPUT,
            "confirmation schema validation failed: "
            + "; ".join(
                f"{'/'.join(str(part) for part in error['loc'])}: {error['msg']}"
                for error in exc.errors(include_url=False)
            ),
        ) from exc


# ---------------------------------------------------------------------------
# Invariant step (spec 06 §2 counts, §5 honesty pricing)
# ---------------------------------------------------------------------------


def _non_empty(value: str | None) -> bool:
    return value is not None and value.strip() != ""


def _invariant_step(model: HumanConfirmation) -> None:
    # §2 disjoint data + §5 rationale pricing.
    for index, row in enumerate(model.decisions):
        label = f"decisions[{index}] ({row.study_id})"
        if row.verdict == "changed":
            if not _non_empty(row.amended):
                raise ConfirmationRefusalError(
                    RefusalCode.INVALID_OUTPUT,
                    f"{label}: verdict 'changed' requires a non-empty 'amended' "
                    "(the amendment is the reviewer's output, not an intent)",
                )
            if not _non_empty(row.rationale):
                raise ConfirmationRefusalError(
                    RefusalCode.INVALID_OUTPUT,
                    f"{label}: verdict 'changed' requires a non-empty "
                    "'rationale'; an override without a reason is a rubber stamp",
                )
            if _non_empty(row.defer_reason):
                raise ConfirmationRefusalError(
                    RefusalCode.INVALID_OUTPUT,
                    f"{label}: a changed row may not partially defer "
                    "('defer_reason' must be empty)",
                )
        elif row.verdict == "deferred":
            if not _non_empty(row.defer_reason):
                raise ConfirmationRefusalError(
                    RefusalCode.INVALID_OUTPUT,
                    f"{label}: a deferral is a decision, not an omission — "
                    "a non-empty 'defer_reason' is required",
                )
            if row.amended is not None:
                raise ConfirmationRefusalError(
                    RefusalCode.INVALID_OUTPUT,
                    f"{label}: a deferred row may not carry an amendment "
                    "('amended' must be empty)",
                )
        else:  # confirmed
            contraband = [
                field
                for field, value in (
                    ("amended", row.amended),
                    ("rationale", row.rationale),
                    ("defer_reason", row.defer_reason),
                )
                if value is not None
            ]
            if contraband:
                raise ConfirmationRefusalError(
                    RefusalCode.INVALID_OUTPUT,
                    f"{label}: a confirmed row carries no amendments "
                    f"(set: {contraband})",
                )

    # §2: study ids are unique (a row reviewed twice is two judgements).
    seen: set[str] = set()
    for row in model.decisions:
        if row.study_id in seen:
            raise ConfirmationRefusalError(
                RefusalCode.INVALID_OUTPUT,
                f"duplicate study_id {row.study_id!r} in decisions",
            )
        seen.add(row.study_id)

    # §2 counts.
    counts = {verdict: 0 for verdict in ("confirmed", "changed", "deferred")}
    for row in model.decisions:
        counts[row.verdict] += 1
    summary = model.summary
    if summary.considered != len(model.decisions):
        raise ConfirmationRefusalError(
            RefusalCode.INVALID_OUTPUT,
            f"summary.considered ({summary.considered}) != len(decisions) "
            f"({len(model.decisions)})",
        )
    for bucket in sorted(counts):
        claimed = getattr(summary, bucket)
        actual = counts[bucket]
        if claimed != actual:
            raise ConfirmationRefusalError(
                RefusalCode.INVALID_OUTPUT,
                f"summary.{bucket} ({claimed}) disagrees with the decision rows "
                f"(actual {actual})",
            )
    if sum(counts.values()) != summary.considered:
        raise ConfirmationRefusalError(
            RefusalCode.INVALID_OUTPUT,
            "summary.confirmed + changed + deferred != summary.considered",
        )


# ---------------------------------------------------------------------------
# Hash + coverage step (spec 06 §3)
# ---------------------------------------------------------------------------


def _verify_one(root: Path, relative: str, declared: str) -> str:
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ConfirmationRefusalError(
            RefusalCode.SCOPE_VIOLATION,
            f"confirmation references a path outside its workspace root: {relative!r}",
        )
    path = root / Path(*candidate.parts)
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise ConfirmationRefusalError(
            RefusalCode.BLOCKED_INPUT,
            f"decision artifact {relative!r} is absent from disk ({exc}); the "
            "reviewer's binding cannot be checked against missing bytes",
        ) from exc
    digest = sha256(content).hexdigest()
    if digest != declared:
        raise ConfirmationRefusalError(
            RefusalCode.PARENT_HASH_MISMATCH,
            f"artifact {relative!r} changed after the reviewer saw it "
            f"(disk {digest}, confirmation binds {declared}) — the binding "
            "cannot silently follow the mutation; sign a fresh confirmation",
        )
    return relative


def verify_artifacts(
    record: Mapping[str, Any] | str | bytes | Path, root: str | Path
) -> list[str]:
    """Verify every bound ``sha256`` against the current on-disk bytes.

    Returns the verified workspace-relative paths. A missing artifact raises
    ``BLOCKED_INPUT``; present-but-mutated bytes raise
    ``PARENT_HASH_MISMATCH`` — never a warning, never a silent re-hash to the
    new bytes (spec `06` §3.3).
    """

    if not isinstance(record, HumanConfirmation):
        record = _schema_step(record if isinstance(record, Mapping) else _load(record))
    base = Path(root)
    return [
        _verify_one(base, artifact.path, artifact.sha256)
        for artifact in record.artifacts
    ]


# ---------------------------------------------------------------------------
# Full validation + coverage enforcement (spec 06 §3.1)
# ---------------------------------------------------------------------------

DECISION_GLOBS = (
    "batch_*_decisions.json",
    "batch_*_decisions_screener2.json",
    # Arm-tagged dual-screen artifacts (spec 04 §4: ``…_decisions_A.json`` /
    # ``…_decisions_B.json``). Deliberately explicit: a bare
    # ``batch_*_decisions_*.json`` would also bless informal side files.
    "batch_*_decisions_A.json",
    "batch_*_decisions_B.json",
    "_adjudication_resolved_group_*.json",
)


def discover_decision_artifacts(root: str | Path) -> list[str]:
    """Return the decision artifacts present under ``literature/screening/``.

    Spec `06` §3.1: every artifact present at sign time must be covered —
    batches, dual-screen screener2 files, and adjudication group files.
    Workspace-relative POSIX paths, sorted.
    """

    screening = Path(root) / "literature" / "screening"
    names: set[str] = set()
    for pattern in DECISION_GLOBS:
        for path in screening.glob(pattern):
            names.add(path.relative_to(screening.parent.parent).as_posix())
    return sorted(names)


def enforce_coverage(
    covered: Sequence[str] | Mapping[str, Any] | str | bytes | Path | HumanConfirmation,
    root: str | Path,
) -> list[str]:
    """Refuse ``BLOCKED_INPUT`` naming every uncovered decision artifact.

    Accepts either the explicit artifact list or a record from which it is
    read. This is the §3.1 rule that a signing run never partially blesses a
    set.
    """

    if isinstance(covered, HumanConfirmation):
        covered = [artifact.path for artifact in covered.artifacts]
    elif isinstance(covered, (str, bytes, Path, Mapping)):
        record = _schema_step(
            covered if isinstance(covered, Mapping) else _load(covered)
        )
        covered = [artifact.path for artifact in record.artifacts]
    elif isinstance(covered, Sequence):
        # Explicit artifact list (spec §3.1 caller-provided sign set).
        covered = [str(item) for item in covered]
    else:
        raise ConfirmationRefusalError(
            RefusalCode.BLOCKED_INPUT,
            f"unsupported coverage argument type: {type(covered).__name__}",
        )

    present = discover_decision_artifacts(root)
    missing = sorted(set(present) - set(covered))
    if missing:
        raise ConfirmationRefusalError(
            RefusalCode.BLOCKED_INPUT,
            "decision artifacts discovered under literature/screening/ are not "
            "covered by the confirmation; the reviewer does not partially "
            "bless a set — missing: " + ", ".join(missing),
        )
    extra = sorted(set(covered) - set(present))
    if extra:
        raise ConfirmationRefusalError(
            RefusalCode.BLOCKED_INPUT,
            "confirmation binds artifacts that are not decision artifacts of "
            "this workspace: " + ", ".join(extra),
        )
    return list(covered)


def validate(
    record: Mapping[str, Any] | str | bytes | Path,
    *,
    verify_artifacts: bool = False,
    root: str | Path | None = None,
) -> HumanConfirmation:
    """Validate one ``HumanConfirmation@1``; refuse any defect by name."""

    payload = _load(record)
    model = _schema_step(payload)
    _invariant_step(model)
    if verify_artifacts:
        if root is None:
            raise ConfirmationRefusalError(
                RefusalCode.BLOCKED_INPUT,
                "verify_artifacts requires a workspace root",
            )
        # Coverage first (§3.1), then the byte checks: a sign that misses an
        # artifact is refused before any hash compare can mislead.
        enforce_coverage(model, root)
        _verify(model, root)
    return model


_verify = verify_artifacts  # aliased: the validate() kwarg shadows the name


# Canonical-JSON helper shared with the envelope (reuse, not a second copy):
def confirmation_fingerprint(record: Mapping[str, Any] | Path) -> str:
    """Deterministic digest over the record minus timing metadata.

    ``provenance.created_at`` is dropped before hashing; this is the Phase B
    "timing never changes identity" convention applied to the confirmation
    payload. No hash here covers ``created_at``.
    """

    if isinstance(record, Path):
        record = _load(record)
    raw = dict(record)
    provenance = dict(raw.get("provenance") or {})
    provenance.pop("created_at", None)
    stripped = {**raw, "provenance": provenance}
    from hashlib import sha256 as _sha256

    return _sha256(canonical_json_bytes(stripped)).hexdigest()


# ---------------------------------------------------------------------------
# Export gate (spec 06 §4)
# ---------------------------------------------------------------------------

#: The authoritative confirmation path under a workspace (spec 06 §4).
CONFIRMATION_RELPATH = "literature/screening/HUMAN_CONFIRMATION.json"


def export_gate(root: str | Path) -> HumanConfirmation:
    """The export gate for an export claiming ``confirmed`` (spec `06` §4).

    An export claiming "confirmed" requires a valid, non-retrospective
    ``HUMAN_CONFIRMATION.json`` whose every artifact hash verifies against the
    current on-disk tree at gate time. Fail closed:

    * no confirmation artifact → ``REFUSED_UNSUPPORTED`` ("no human
      confirmation artifact");
    * invalid record, uncovered artifact, or mutated bytes after review →
      the named validation refusal (``INVALID_OUTPUT`` / ``BLOCKED_INPUT`` /
      ``PARENT_HASH_MISMATCH``);
    * a ``retrospective: true`` record → ``REFUSED_UNSUPPORTED`` — retrospective
      signatures may never satisfy the export gate (owner decision 2026-10-26:
      label, not backfill).

    Returns the accepted confirmation model on success.
    """

    base = Path(root)
    record_path = base / Path(*PurePosixPath(CONFIRMATION_RELPATH).parts)
    if not record_path.is_file():
        raise ConfirmationRefusalError(
            RefusalCode.REFUSED_UNSUPPORTED,
            "no human confirmation artifact: an export claiming 'confirmed' "
            f"requires {CONFIRMATION_RELPATH} (sign one with "
            "scripts/confirm_screening.py)",
        )
    model = validate(record_path, verify_artifacts=True, root=base)
    if model.retrospective:
        raise ConfirmationRefusalError(
            RefusalCode.REFUSED_UNSUPPORTED,
            "the confirmation artifact is retrospective=true; a retrospective "
            "signature may never satisfy the export gate — the pilot corpus is "
            "labelled, not backfilled (owner decision 2026-10-26)",
        )
    return model


# ---------------------------------------------------------------------------
# CLI (envelope-style refusal JSON on stderr + exit 1)
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scholar_harness.contracts.confirmation",
        description="Validate HumanConfirmation@1 records.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    validate_parser = commands.add_parser("validate", help="validate one confirmation")
    validate_parser.add_argument("path")
    validate_parser.add_argument(
        "--verify-artifacts",
        action="store_true",
        help="also verify bound sha256 hashes against --root",
    )
    validate_parser.add_argument("--root", default=None)

    commands.add_parser(
        "render-schema", help="print the rendered HumanConfirmation@1 JSON schema"
    )

    args = parser.parse_args(argv)
    if args.command == "render-schema":
        from .schema import render_confirmation_schema

        sys.stdout.write(render_confirmation_schema())
        return 0
    try:
        root = Path(args.root) if args.root else None
        model = validate(
            Path(args.path), verify_artifacts=args.verify_artifacts, root=root
        )
    except ConfirmationRefusalError as error:
        print(
            json.dumps(
                {
                    "result": "rejected",
                    "status": str(error.refusal_code),
                    "refusal_code": str(error.refusal_code),
                    "detail": error.detail,
                }
            ),
            file=sys.stderr,
        )
        return 1
    print(
        json.dumps(
            {
                "result": "accepted",
                "schema": str(model.schema_),
                "retrospective": model.retrospective,
                "reviewer": model.reviewer.name,
                "artifacts": len(model.artifacts),
                "decisions": len(model.decisions),
            }
        )
    )
    return 0
