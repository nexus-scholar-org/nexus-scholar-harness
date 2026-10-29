"""Coherent publication generations for authorized screening (AG-03C).

A shared authorization gate plus a coherent generation record for the
screening publication path. Extends AG-03A (:mod:`scholar_harness.authority.binding`,
approval mint/verify/promote with 8 typed refusal codes) and AG-03B
(:mod:`scholar_harness.authority.lifecycle`, immutable review snapshots,
durable refusals) — both reused here, never rewritten.

What this module owns
---------------------
* :class:`GenerationRecord` (``harness-screening-generation-v1``): the commit
  record for one authorized publication of the five screening outputs plus
  itself (six files, one commit point).
* :func:`publish_generation`: verify-first gate (no approval means no write),
  tmp+rename staging of all five content files, history retention, and the
  rename of ``generation.json`` LAST as the single commit point. A best-effort
  lock file serializes two competing writers on one host.
* :func:`require_current_generation`: honest currentness reporting
  (``CURRENT`` / ``STALE`` / ``SUPERSEDED`` / ``MISMATCHED`` /
  ``LEGACY_UNVERIFIED``) with typed refusal codes. Consumers branch on it.
* :func:`recover_partial`: crash-recovery sweep (stale tmps + orphan lock).

What this module does NOT do
----------------------------
* It never mints a legacy generation: ``publish_generation`` always requires
  a valid operator approval. Whether a workspace *without* authorized material
  keeps its pre-authorization file behavior is each caller's explicit,
  documented compatibility decision — this module only reports
  ``LEGACY_UNVERIFIED`` for that state, honestly.
* Revocation/expiry enforcement is structural but vacuous until a revocation
  store and an expiry policy exist: both parameters are plumbed through and
  default to unenforced. Approval scope/content mismatches ARE enforced.
* No filesystem atomicity/durability is claimed beyond what tmp+rename on one
  host provides. The lock file is best-effort exclusive-create: it serializes
  writers that honor this protocol on one host and says nothing about a writer
  that ignores it, a second host, an administrator, or POSIX hosts (Windows
  MIC remains the proven deployment in
  :mod:`scholar_harness.authority.isolation`).
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping

from scholar_harness.authority.binding import (
    APPROVAL_CONTENT_CHANGED,
    APPROVAL_MISSING,
    APPROVAL_POLICY_MISMATCH,
    APPROVAL_SCOPE_MISMATCH,
    PROMOTION_AUDIT_FAILED,
    ApprovalBinding,
    ApprovalRecord,
    AuthorityRefused,
    OperatorIdentity,
    canonical_json_bytes,
    content_sha256,
    mint_approval,
    verify_approval,
)
from scholar_harness.authority.lifecycle import capture_snapshot, record_refusal

#: Sidecar identity for one authorized screening publication generation.
GENERATION_SCHEMA = "harness-screening-generation-v1"

#: Sidecar identity for the canonical publication snapshot under review.
PUBLICATION_SNAPSHOT_SCHEMA = "harness-screening-publication-snapshot-v1"

#: Sidecar identity for the staged publication approval file.
PUBLICATION_APPROVAL_SCHEMA = "harness-screening-publication-approval-v1"

#: Policy version the collect publication path mints and verifies under.
SCREENING_PUBLICATION_POLICY_VERSION = "screening-publication-v1"

#: The five content files one generation commits, in commit order.
PUBLICATION_OUTPUTS = (
    "included.json",
    "excluded.json",
    "conflicts.json",
    "prisma_screening_report.md",
    "prisma_report.json",
)

#: The generation manifest: renamed LAST, the single commit point.
GENERATION_FILENAME = "generation.json"

#: The staged operator approval the collect gate reads (resident after publish).
PUBLICATION_APPROVAL_FILENAME = "publication_approval.json"

#: Best-effort single-host serialization for competing publishers.
COLLECT_LOCK_FILENAME = ".collect.lock"

#: Retained superseded generation records (historical evidence, never current).
GENERATION_HISTORY_DIRNAME = "generations"

#: Publication snapshots have no revision chain of their own: a changed retry
#: is a new review bound by new content hashes, not a bumped counter. The
#: constant keeps the approval binding comparable across idempotent retries.
PUBLICATION_RECOMMENDATION_REVISION = 0

# --- typed refusal codes (generation layer) -------------------------------- #
# Binding-layer codes (APPROVAL_MISSING, APPROVAL_CONTENT_CHANGED,
# APPROVAL_SCOPE_MISMATCH, ...) keep their meaning end to end; the codes below
# name generation states for consumers that branch on currentness.

GENERATION_STALE = "GENERATION_STALE"
GENERATION_SUPERSEDED = "GENERATION_SUPERSEDED"
GENERATION_MISMATCHED = "GENERATION_MISMATCHED"
GENERATION_LEGACY_UNVERIFIED = "GENERATION_LEGACY_UNVERIFIED"
GENERATION_LOCKED = "GENERATION_LOCKED"


class GenerationStatus(str, Enum):
    """Currentness of a workspace's screening publication."""

    CURRENT = "CURRENT"
    STALE = "STALE"
    SUPERSEDED = "SUPERSEDED"
    MISMATCHED = "MISMATCHED"
    LEGACY_UNVERIFIED = "LEGACY_UNVERIFIED"


_STATUS_CODES: dict[GenerationStatus, str | None] = {
    GenerationStatus.CURRENT: None,
    GenerationStatus.STALE: GENERATION_STALE,
    GenerationStatus.SUPERSEDED: GENERATION_SUPERSEDED,
    GenerationStatus.MISMATCHED: GENERATION_MISMATCHED,
    GenerationStatus.LEGACY_UNVERIFIED: GENERATION_LEGACY_UNVERIFIED,
}


@dataclass(frozen=True)
class CurrentnessResult:
    """The honest answer to "may this workspace's outputs be consumed?".

    ``code`` is the stable machine-readable refusal (``None`` when CURRENT);
    ``message`` is the human half; ``details`` carries the evidence a caller
    needs to report or branch (generation id, mismatched files, underlying
    approval code). ``record`` is the on-disk generation when one parsed.
    """

    status: GenerationStatus
    code: str | None
    message: str
    details: dict[str, Any]
    record: GenerationRecord | None = None


# --- generation record ------------------------------------------------------ #


def _batch_set_hash8(batch_bindings: list[dict[str, Any]]) -> str:
    """First 8 hex of the canonical batch-binding set digest."""
    canonical = sorted(
        (
            {
                "batch_artifact_id": b["batch_artifact_id"],
                "batch_index": b["batch_index"],
                "batch_sha256": b["batch_sha256"],
            }
            for b in batch_bindings
        ),
        key=lambda b: (b["batch_index"], b["batch_artifact_id"]),
    )
    return sha256(canonical_json_bytes({"batch_bindings": canonical})).hexdigest()[:8]


def _slug(value: str, *, keep_dash: bool = False, limit: int = 32) -> str:
    allowed = "A-Za-z0-9_-" if keep_dash else "A-Za-z0-9"
    return re.sub(f"[^{allowed}]", "", value)[:limit] or "X"


def compute_generation_id(
    workspace_id: str, run_id: str, batch_bindings: list[dict[str, Any]]
) -> str:
    """Deterministic generation id: identical scope re-collects identically."""
    ws_short = _slug(workspace_id.removeprefix("WSP-"), limit=8)
    run_slug = _slug(run_id, keep_dash=True, limit=32)
    return f"GEN-{ws_short}-{run_slug}-{_batch_set_hash8(batch_bindings)}"


@dataclass(frozen=True)
class GenerationRecord:
    """One authorized screening publication generation (packet §3 shape)."""

    generation_id: str
    workspace_id: str
    run_id: str
    batch_bindings: tuple[dict[str, Any], ...]
    protocol_fingerprint: str
    corpus_fingerprint: str
    snapshot_fingerprint: str
    approval_fingerprint: str
    operator_identity: str
    policy_version: str
    outputs: tuple[tuple[str, str], ...]
    supersedes: str | None
    published_at: str
    schema: str = GENERATION_SCHEMA

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generation_id": self.generation_id,
            "workspace_id": self.workspace_id,
            "run_id": self.run_id,
            "batch_bindings": [dict(b) for b in self.batch_bindings],
            "protocol_fingerprint": self.protocol_fingerprint,
            "corpus_fingerprint": self.corpus_fingerprint,
            "snapshot_fingerprint": self.snapshot_fingerprint,
            "approval_fingerprint": self.approval_fingerprint,
            "operator_identity": self.operator_identity,
            "policy_version": self.policy_version,
            "outputs": {name: digest for name, digest in self.outputs},
            "supersedes": self.supersedes,
            "published_at": self.published_at,
        }

    def fingerprint(self) -> str:
        return content_sha256(canonical_json_bytes(self.as_dict()))

    @property
    def output_digests(self) -> dict[str, str]:
        return {name: digest for name, digest in self.outputs}

    @classmethod
    def from_dict(cls, payload: Any) -> GenerationRecord:
        if not isinstance(payload, dict):
            raise ValueError("generation record is not a JSON object")
        if payload.get("schema") != GENERATION_SCHEMA:
            raise ValueError(f"unexpected generation schema {payload.get('schema')!r}")
        try:
            bindings = tuple(
                {
                    "batch_index": b["batch_index"],
                    "batch_artifact_id": b["batch_artifact_id"],
                    "batch_sha256": b["batch_sha256"],
                }
                for b in payload["batch_bindings"]
            )
            outputs = tuple(
                (name, payload["outputs"][name]) for name in PUBLICATION_OUTPUTS
            )
            if set(payload["outputs"]) != set(PUBLICATION_OUTPUTS):
                raise KeyError("outputs")
            return cls(
                generation_id=str(payload["generation_id"]),
                workspace_id=str(payload["workspace_id"]),
                run_id=str(payload["run_id"]),
                batch_bindings=bindings,
                protocol_fingerprint=str(payload["protocol_fingerprint"]),
                corpus_fingerprint=str(payload["corpus_fingerprint"]),
                snapshot_fingerprint=str(payload["snapshot_fingerprint"]),
                approval_fingerprint=str(payload["approval_fingerprint"]),
                operator_identity=str(payload["operator_identity"]),
                policy_version=str(payload["policy_version"]),
                outputs=outputs,
                supersedes=(
                    None
                    if payload["supersedes"] is None
                    else str(payload["supersedes"])
                ),
                published_at=str(payload["published_at"]),
            )
        except (KeyError, TypeError, AttributeError) as exc:
            raise ValueError(f"generation record is incomplete ({exc})") from exc


def generation_file_bytes(record: GenerationRecord) -> bytes:
    """Deterministic manifest bytes (formatting never affects the fingerprint)."""
    return json.dumps(record.as_dict(), indent=2, sort_keys=True).encode("utf-8")


# --- publication snapshot + binding ------------------------------------------ #


def build_publication_snapshot(
    *,
    workspace_id: str,
    run_id: str,
    batch_bindings: list[dict[str, Any]],
    protocol_fingerprint: str,
    corpus_fingerprint: str,
    output_digests: Mapping[str, str],
) -> bytes:
    """Canonical bytes the operator reviews and the approval binds.

    The snapshot commits to the exact scope (workspace/run/batch parents) and
    to the exact output bytes (via digests), so any post-review swap of scope
    or content invalidates the approval at verification.
    """
    payload = {
        "schema": PUBLICATION_SNAPSHOT_SCHEMA,
        "workspace_id": workspace_id,
        "run_id": run_id,
        "batch_bindings": sorted(
            (
                {
                    "batch_artifact_id": b["batch_artifact_id"],
                    "batch_index": b["batch_index"],
                    "batch_sha256": b["batch_sha256"],
                }
                for b in batch_bindings
            ),
            key=lambda b: (b["batch_index"], b["batch_artifact_id"]),
        ),
        "protocol_fingerprint": protocol_fingerprint,
        "corpus_fingerprint": corpus_fingerprint,
        "outputs": {name: output_digests[name] for name in PUBLICATION_OUTPUTS},
    }
    return canonical_json_bytes(payload)


def publication_binding(
    *,
    workspace_id: str,
    run_id: str,
    batch_bindings: list[dict[str, Any]],
    protocol_fingerprint: str,
    corpus_fingerprint: str,
    policy_version: str = SCREENING_PUBLICATION_POLICY_VERSION,
) -> ApprovalBinding:
    """The exact scope a publication approval is good for.

    One binding covers the whole batch set: ``batch_id`` names the run plus
    the batch-set hash, so replaying an approval across workspaces, runs, or
    batch sets refuses with ``APPROVAL_SCOPE_MISMATCH``.
    """
    return ApprovalBinding(
        workspace_id=workspace_id,
        run_id=run_id,
        batch_id=f"screening-publication:{run_id}:{_batch_set_hash8(batch_bindings)}",
        protocol_fingerprint=protocol_fingerprint,
        corpus_fingerprint=corpus_fingerprint,
        recommendation_revision=PUBLICATION_RECOMMENDATION_REVISION,
        policy_version=policy_version,
    )


def mint_publication_approval(
    *,
    operator: OperatorIdentity,
    binding: ApprovalBinding,
    snapshot_bytes: bytes,
    approved_at: str,
) -> ApprovalRecord:
    """Bind an operator approval to the exact publication snapshot.

    The snapshot is frozen into an AG-03B single-buffer snapshot first, so the
    reviewed and authorized bytes are provably the same object; the reviewed
    content and the authorized final content are both that snapshot (it
    already commits to the output bytes via digests).
    """
    snapshot = capture_snapshot(bytes(snapshot_bytes), bytes(snapshot_bytes), binding)
    reviewed = snapshot.bytes_for("hash")
    return mint_approval(
        operator=operator,
        binding=binding,
        reviewed_bytes=reviewed,
        final_decision_bytes=snapshot.final_bytes_for("hash"),
        approved_at=approved_at,
    )


# --- publication scope resolution --------------------------------------------- #


@dataclass(frozen=True)
class PublicationScope:
    """The collected scope a publication snapshot/binding is built from."""

    workspace_id: str
    run_id: str
    batch_bindings: tuple[dict[str, Any], ...]
    protocol_fingerprint: str
    corpus_fingerprint: str


def resolve_publication_scope(workspace_dir: Path) -> PublicationScope:
    """Resolve the unanimous publication scope from manifest + registry.

    Every batch handoff file must resolve to a registered parent batch
    artifact, and all batches must agree on workspace/protocol/corpus. A mixed
    or unresolvable scope refuses fail-closed: no snapshot is built, so no
    approval can be minted or verified against it.
    """
    ws = Path(workspace_dir).resolve()
    screening_dir = ws / "literature" / "screening"
    try:
        manifest = json.loads((screening_dir / "MANIFEST.json").read_text("utf-8"))
        registry = json.loads(
            (ws / "audit" / "artifact_registry.json").read_text("utf-8")
        )
    except (OSError, ValueError) as exc:
        raise AuthorityRefused(
            APPROVAL_SCOPE_MISMATCH,
            f"cannot resolve publication scope (manifest/registry unreadable: {exc})",
        ) from exc
    run_id = manifest.get("screening_run_id")
    if not run_id:
        raise AuthorityRefused(
            APPROVAL_SCOPE_MISMATCH,
            "cannot resolve publication scope (MANIFEST.json carries no screening_run_id)",
        )
    batches = manifest.get("batches", [])
    if not batches:
        raise AuthorityRefused(
            APPROVAL_SCOPE_MISMATCH,
            "cannot resolve publication scope (MANIFEST.json lists no batches)",
        )
    bindings: list[dict[str, Any]] = []
    scopes: set[tuple[str, str, str]] = set()
    for batch in batches:
        idx = batch["batch_index"]
        try:
            batch_data = json.loads(
                (screening_dir / f"batch_{idx:03d}.json").read_text("utf-8")
            )
            entry = registry.get("artifacts", {}).get(batch_data.get("artifact_id"))
            batch_env = json.loads((ws / entry["path"]).read_text("utf-8"))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise AuthorityRefused(
                APPROVAL_SCOPE_MISMATCH,
                f"cannot resolve publication scope for batch {idx} ({exc})",
                batch_index=idx,
            ) from exc
        bindings.append(
            {
                "batch_index": idx,
                "batch_artifact_id": batch_data["artifact_id"],
                "batch_sha256": entry["sha256"],
            }
        )
        scopes.add(
            (
                str(batch_env.get("workspace_id")),
                str(batch_env.get("protocol_fingerprint")),
                str(batch_env.get("corpus_fingerprint")),
            )
        )
    if len(scopes) != 1:
        raise AuthorityRefused(
            APPROVAL_SCOPE_MISMATCH,
            "batches disagree on workspace/protocol/corpus parents; "
            "no single publication scope exists",
            parent_scopes=sorted(scopes),
        )
    workspace_id, protocol_fp, corpus_fp = sorted(scopes)[0]
    bindings.sort(key=lambda b: b["batch_index"])
    return PublicationScope(
        workspace_id=workspace_id,
        run_id=str(run_id),
        batch_bindings=tuple(bindings),
        protocol_fingerprint=protocol_fp,
        corpus_fingerprint=corpus_fp,
    )


# --- staged approval sidecar --------------------------------------------------- #


def write_publication_approval(
    screening_dir: Path,
    record: ApprovalRecord,
    *,
    policy_version: str = SCREENING_PUBLICATION_POLICY_VERSION,
    staged_at: str,
) -> Path:
    """Stage the operator approval the collect gate will verify (test/operator aid)."""
    path = Path(screening_dir) / PUBLICATION_APPROVAL_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": PUBLICATION_APPROVAL_SCHEMA,
                "approval": record.as_dict(),
                "policy_version": policy_version,
                "staged_at": staged_at,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def load_publication_approval(screening_dir: Path) -> ApprovalRecord | None:
    """Load the staged publication approval, or ``None`` when none is staged.

    Absent file means no authorization was attempted (callers apply their
    documented legacy disposition). A present-but-unusable file is an attempted
    authorization that fails closed — never a silent legacy pass.
    """
    path = Path(screening_dir) / PUBLICATION_APPROVAL_FILENAME
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AuthorityRefused(
            APPROVAL_SCOPE_MISMATCH,
            f"staged publication approval is unreadable ({exc})",
        ) from exc
    if not isinstance(payload, dict) or payload.get("schema") != (
        PUBLICATION_APPROVAL_SCHEMA
    ):
        raise AuthorityRefused(
            APPROVAL_SCOPE_MISMATCH,
            "staged publication approval carries an unexpected schema",
            schema=payload.get("schema") if isinstance(payload, dict) else None,
        )
    record_payload = payload.get("approval")
    if record_payload is None:
        raise AuthorityRefused(
            APPROVAL_MISSING,
            "staged publication approval carries no approval record",
        )
    try:
        return _approval_from_dict(record_payload)
    except (KeyError, TypeError, ValueError) as exc:
        raise AuthorityRefused(
            APPROVAL_SCOPE_MISMATCH,
            f"staged publication approval is not a valid approval record ({exc})",
        ) from exc


# --- filesystem discipline ------------------------------------------------------ #


def _write_tmp(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _write_tmp_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def publication_file_bytes(text: str) -> bytes:
    """File bytes for publication text on this host.

    Exactly what ``Path.write_text(text, encoding="utf-8")`` writes: on
    Windows the text-mode layer translates ``\\n`` to CRLF, on POSIX it is
    the UTF-8 encoding unchanged. The collect legacy path and the authorized
    path both stage through ``write_text``, so their files are byte-identical
    by construction; digests anywhere (snapshot minting, record building,
    currentness checks) MUST be computed over these bytes, never over a bare
    ``str.encode``. Carriage returns are refused fail-closed: a ``\\r`` would
    translate differently than a plain encode and silently break digest
    agreement (JSON payloads never contain one — the encoder escapes it).

    Digest input mirrors CPython ``Path.write_text(newline=None)``: LF becomes
    ``os.linesep`` on Windows and the UTF-8 encoding is unchanged on POSIX.
    Pinned by the byte-identity test; if the stdlib default ever changes,
    digests must be recomputed from staged tmp bytes instead.
    """
    if "\r" in text:
        raise ValueError(
            "publication text must not contain carriage returns "
            "(newline translation would diverge from the digest)"
        )
    return text.replace("\n", os.linesep).encode("utf-8")


def _rename_tmp(tmp: Path, final: Path) -> None:
    os.replace(tmp, final)


def _acquire_lock(lock_path: Path, timeout_s: float) -> None:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + max(0.0, timeout_s)
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, str(os.getpid()).encode("ascii"))
            finally:
                os.close(fd)
            return
        except (FileExistsError, PermissionError) as exc:
            if time.monotonic() >= deadline:
                if isinstance(exc, PermissionError):
                    detail = (
                        f"{lock_path.name} could not be acquired (access denied); "
                        "on Windows an existing directory or an exclusively opened "
                        "lock file reports this instead of 'already exists' — "
                        "refusing to mix generations; inspect the path and remove "
                        "a stale lock only once no live writer remains"
                    )
                else:
                    detail = (
                        f"another publisher holds {lock_path.name}; refusing to mix "
                        "generations (remove the stale lock via recover_partial and "
                        "re-collect once no live writer remains)"
                    )
                raise AuthorityRefused(
                    GENERATION_LOCKED,
                    detail,
                    lock_path=str(lock_path),
                ) from exc
            time.sleep(0.02)


def _release_lock(lock_path: Path) -> None:
    try:
        lock_path.unlink(missing_ok=True)
    except OSError:
        pass


def _tmp_paths(literature_dir: Path, screening_dir: Path) -> list[Path]:
    paths = [literature_dir / f"{name}.tmp" for name in PUBLICATION_OUTPUTS]
    paths.append(screening_dir / f"{GENERATION_FILENAME}.tmp")
    history_dir = screening_dir / GENERATION_HISTORY_DIRNAME
    if history_dir.is_dir():
        paths.extend(sorted(history_dir.glob("*.tmp")))
    return paths


def _remove_paths(paths: list[Path]) -> list[str]:
    removed: list[str] = []
    for path in paths:
        try:
            if path.is_file() or path.is_symlink():
                path.unlink()
                removed.append(path.name)
        except OSError:
            pass
    return removed


def _history_path(screening_dir: Path, record: GenerationRecord) -> Path:
    fp12 = record.fingerprint().removeprefix("sha256:")[:16]
    return (
        screening_dir
        / GENERATION_HISTORY_DIRNAME
        / f"{record.generation_id}.{fp12}.json"
    )


def _load_record_and_bytes(path: Path) -> tuple[GenerationRecord | None, bytes | None]:
    try:
        raw = path.read_bytes()
    except OSError:
        return None, None
    try:
        return GenerationRecord.from_dict(json.loads(raw.decode("utf-8"))), raw
    except (ValueError, UnicodeDecodeError):
        return None, raw


def _iter_history(screening_dir: Path) -> list[GenerationRecord]:
    history_dir = screening_dir / GENERATION_HISTORY_DIRNAME
    records: list[GenerationRecord] = []
    if not history_dir.is_dir():
        return records
    for path in sorted(history_dir.glob("*.json")):
        record, _ = _load_record_and_bytes(path)
        if record is not None:
            records.append(record)
    return records


# --- publication ----------------------------------------------------------------- #


@dataclass(frozen=True)
class GenerationPublishResult:
    """The outcome of one authorized publication attempt."""

    record: GenerationRecord
    generation_id: str
    generation_fingerprint: str
    output_digests: dict[str, str]
    idempotent: bool
    supersedes: str | None
    audit_event: dict[str, Any] | None


def publish_generation(
    *,
    workspace: Path,
    snapshot_bytes: bytes,
    binding: ApprovalBinding,
    record: ApprovalRecord | None,
    content: Mapping[str, str],
    published_at: str,
    policy_version: str = SCREENING_PUBLICATION_POLICY_VERSION,
    audit_append: Callable[[dict[str, Any]], None],
    refusal_sink: Callable[[dict[str, Any]], None] | None = None,
    revoked_fingerprints: frozenset[str] = frozenset(),
    max_age_seconds: int | None = None,
    lock_timeout_s: float = 10.0,
) -> GenerationPublishResult:
    """Verify approval, then coherently publish one screening generation.

    Fail-closed ordering: the approval gate runs before the lock, before any
    tmp staging, before any rename. On refusal none of the five content files
    nor ``generation.json`` is written or left staged (tmps removed). Pre-gate
    review records — MANIFEST.json status/lineage rows, registry
    screening_decisions entries, ``legacy/`` archive copies, and the refusal
    audit row itself — already exist by design and are review evidence, not
    publication. The presented ``content`` must agree with the
    reviewed snapshot's output digests — content the approval never reviewed
    refuses with ``APPROVAL_CONTENT_CHANGED`` before anything is staged. On
    success the five content files are staged to tmp with the same
    ``write_text`` call the legacy path uses (byte-identical by construction,
    including host newline translation) and renamed, history is retained, and
    ``generation.json`` is renamed LAST as the single commit point — nothing
    is CURRENT until it lands. An audit-sink failure removes everything staged
    (including tmps and any pre-existing outputs at those paths, which can no
    longer be treated as authorized) and raises ``PROMOTION_AUDIT_FAILED``.

    Identical retries (same generation id, same outputs, same approval) are
    idempotent: the existing record is returned, no file is rewritten, and no
    new audit event is appended. A lock loser re-reads under the lock and
    joins the identical generation (idempotent) or refuses on scope mismatch
    — concurrent attempts never silently mix generations.
    """
    if set(content) != set(PUBLICATION_OUTPUTS):
        raise ValueError(
            "content must carry exactly the five publication outputs "
            f"({sorted(PUBLICATION_OUTPUTS)}); got {sorted(content)}"
        )
    try:
        snapshot_payload = json.loads(bytes(snapshot_bytes).decode("utf-8"))
        scope_bindings = _bindings_from_payload(snapshot_payload)
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as exc:
        raise AuthorityRefused(
            APPROVAL_SCOPE_MISMATCH,
            f"publication snapshot is malformed ({exc}); no approval can be "
            "verified against it",
        ) from exc
    generation_id = compute_generation_id(
        binding.workspace_id, binding.run_id, scope_bindings
    )
    try:
        content_text = {name: str(content[name]) for name in PUBLICATION_OUTPUTS}
        digests = {
            name: content_sha256(publication_file_bytes(text))
            for name, text in content_text.items()
        }
    except ValueError as exc:
        raise AuthorityRefused(
            APPROVAL_CONTENT_CHANGED,
            f"publication content is not committable ({exc})",
        ) from exc

    # 1. Gate FIRST: no approval verification, no filesystem effect.
    snapshot = capture_snapshot(bytes(snapshot_bytes), bytes(snapshot_bytes), binding)
    gate_bytes = snapshot.bytes_for("hash")

    def _record_and_raise(refusal: AuthorityRefused) -> None:
        if refusal_sink is not None:
            try:
                record_refusal(refusal, binding, refusal_sink, recorded_at=published_at)
            except Exception as sink_exc:  # noqa: BLE001 - must surface, never mask
                raise AuthorityRefused(
                    refusal.code,
                    f"{refusal.message} (refusal audit also failed: "
                    f"{type(sink_exc).__name__}: {sink_exc})",
                    **refusal.details,
                    audit_error=type(sink_exc).__name__,
                ) from sink_exc
        raise refusal

    try:
        verified = verify_approval(
            record=record,
            expected_binding=binding,
            reviewed_bytes=gate_bytes,
            final_decision_bytes=snapshot.final_bytes_for("hash"),
            policy_version=policy_version,
            now=published_at,
            revoked_fingerprints=revoked_fingerprints,
            max_age_seconds=max_age_seconds,
        )
    except AuthorityRefused as refusal:
        _record_and_raise(refusal)

    # 2. Content agreement BEFORE the lock: the staged bytes must be exactly
    # the bytes the approval reviewed (host newline translation included).
    if snapshot_payload.get("outputs") != digests:
        _record_and_raise(
            AuthorityRefused(
                APPROVAL_CONTENT_CHANGED,
                "publication content does not match the reviewed snapshot; "
                "content staged for publication was never approved",
                expected_digests=snapshot_payload.get("outputs"),
                presented_digests=digests,
            )
        )

    ws = Path(workspace).resolve()
    literature_dir = ws / "literature"
    screening_dir = literature_dir / "screening"
    lock_path = screening_dir / COLLECT_LOCK_FILENAME

    _acquire_lock(lock_path, lock_timeout_s)
    try:
        # A previous crashed run's tmps are never consumable; clear them now
        # that serialization is held so they cannot be mistaken for staging.
        _remove_paths(_tmp_paths(literature_dir, screening_dir))

        generation_path = screening_dir / GENERATION_FILENAME
        previous, previous_raw = _load_record_and_bytes(generation_path)
        if (
            previous is not None
            and previous.generation_id == generation_id
            and previous.output_digests == digests
            and previous.approval_fingerprint == verified.fingerprint()
            and previous.snapshot_fingerprint == content_sha256(gate_bytes)
            and previous.workspace_id == binding.workspace_id
            and previous.run_id == binding.run_id
            and previous.protocol_fingerprint == binding.protocol_fingerprint
            and previous.corpus_fingerprint == binding.corpus_fingerprint
            and previous.policy_version == policy_version
            and previous.operator_identity == verified.operator_identity
        ):
            # Idempotent join: the authorized content is already committed
            # (the chain link and timestamp may differ — they are not content).
            return GenerationPublishResult(
                record=previous,
                generation_id=previous.generation_id,
                generation_fingerprint=previous.fingerprint(),
                output_digests=dict(digests),
                idempotent=True,
                supersedes=previous.supersedes,
                audit_event=None,
            )
        candidate = GenerationRecord(
            generation_id=generation_id,
            workspace_id=binding.workspace_id,
            run_id=binding.run_id,
            batch_bindings=tuple(scope_bindings),
            protocol_fingerprint=binding.protocol_fingerprint,
            corpus_fingerprint=binding.corpus_fingerprint,
            snapshot_fingerprint=content_sha256(gate_bytes),
            approval_fingerprint=verified.fingerprint(),
            operator_identity=verified.operator_identity,
            policy_version=policy_version,
            outputs=tuple((name, digests[name]) for name in PUBLICATION_OUTPUTS),
            supersedes=previous.fingerprint() if previous is not None else None,
            published_at=published_at,
        )

        manifest_bytes = generation_file_bytes(candidate)
        staged: list[tuple[Path, Path]] = []
        try:
            for name in PUBLICATION_OUTPUTS:
                tmp = literature_dir / f"{name}.tmp"
                # Same write_text call the legacy path uses: byte-identical
                # files by construction, on every host.
                _write_tmp_text(tmp, content_text[name])
                staged.append((tmp, literature_dir / name))
            history_path = _history_path(screening_dir, candidate)
            if not (
                history_path.is_file() and history_path.read_bytes() == manifest_bytes
            ):
                history_tmp = history_path.with_name(history_path.name + ".tmp")
                _write_tmp(history_tmp, manifest_bytes)
                staged.append((history_tmp, history_path))
            if previous is not None and previous_raw is not None:
                previous_history = _history_path(screening_dir, previous)
                if not previous_history.is_file():
                    previous_tmp = previous_history.with_name(
                        previous_history.name + ".tmp"
                    )
                    _write_tmp(previous_tmp, previous_raw)
                    staged.append((previous_tmp, previous_history))
            generation_tmp = screening_dir / f"{GENERATION_FILENAME}.tmp"
            _write_tmp(generation_tmp, manifest_bytes)
            # Commit order: contents, history, and the generation manifest LAST.
            for tmp, final in staged:
                _rename_tmp(tmp, final)
            _rename_tmp(generation_tmp, generation_path)
        except Exception:
            _remove_paths([tmp for tmp, _ in staged])
            _remove_paths([generation_tmp])
            raise

        event = {
            "action": "SCREENING_GENERATION_PUBLISHED",
            "description": (
                f"Published authorized screening generation {generation_id} "
                f"for run {binding.run_id}"
            ),
            "status": "SUCCESS",
            "agent": "agent_screen.collect",
            "operator_identity": verified.operator_identity,
            "generation_id": generation_id,
            "generation_fingerprint": candidate.fingerprint(),
            "approval_fingerprint": verified.fingerprint(),
            "workspace_id": binding.workspace_id,
            "run_id": binding.run_id,
            "output_digests": dict(digests),
            "supersedes": candidate.supersedes,
            "declared_at": published_at,
        }
        try:
            audit_append(event)
        except Exception as exc:  # noqa: BLE001 - any audit failure fails closed
            _remove_paths([literature_dir / name for name in PUBLICATION_OUTPUTS])
            _remove_paths(
                [
                    generation_path,
                    _history_path(screening_dir, candidate),
                ]
            )
            _remove_paths(_tmp_paths(literature_dir, screening_dir))
            raise AuthorityRefused(
                PROMOTION_AUDIT_FAILED,
                "audit append failed; refusing to leave consumable output "
                "without provenance",
                generation_id=generation_id,
                cause=type(exc).__name__,
            ) from exc

        return GenerationPublishResult(
            record=candidate,
            generation_id=candidate.generation_id,
            generation_fingerprint=candidate.fingerprint(),
            output_digests=dict(digests),
            idempotent=False,
            supersedes=candidate.supersedes,
            audit_event=event,
        )
    finally:
        _release_lock(lock_path)


def _bindings_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Recover the canonical batch bindings embedded in a snapshot payload."""
    return [
        {
            "batch_index": b["batch_index"],
            "batch_artifact_id": b["batch_artifact_id"],
            "batch_sha256": b["batch_sha256"],
        }
        for b in payload["batch_bindings"]
    ]


# --- currentness ------------------------------------------------------------------ #


def _workspace_identity(workspace: Path) -> str | None:
    path = workspace / "project.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(manifest, dict):
        return None
    recorded = manifest.get("registered_workspace_id")
    return recorded if isinstance(recorded, str) and recorded.strip() else None


def _protocol_fingerprint(workspace: Path) -> str | None:
    try:
        from scholar_protocol.canonical import (
            canonical_fingerprint as protocol_fingerprint,
        )
        from scholar_protocol.models import ResearchProtocol

        raw = json.loads((workspace / "protocol.json").read_text(encoding="utf-8"))
        return protocol_fingerprint(ResearchProtocol.model_validate(raw))
    except (OSError, ValueError):
        return None


def _manifest_run_id(workspace: Path) -> str | None:
    try:
        manifest = json.loads(
            (workspace / "literature" / "screening" / "MANIFEST.json").read_text(
                encoding="utf-8"
            )
        )
    except (OSError, ValueError):
        return None
    run_id = manifest.get("screening_run_id") if isinstance(manifest, dict) else None
    return run_id if isinstance(run_id, str) and run_id else None


def _approval_from_dict(payload: Any) -> ApprovalRecord:
    binding_payload = payload["binding"]
    return ApprovalRecord(
        binding=ApprovalBinding(
            workspace_id=str(binding_payload["workspace_id"]),
            run_id=str(binding_payload["run_id"]),
            batch_id=str(binding_payload["batch_id"]),
            protocol_fingerprint=str(binding_payload["protocol_fingerprint"]),
            corpus_fingerprint=str(binding_payload["corpus_fingerprint"]),
            recommendation_revision=int(binding_payload["recommendation_revision"]),
            policy_version=str(binding_payload["policy_version"]),
        ),
        recommendation_sha256=str(payload["recommendation_sha256"]),
        final_decision_sha256=str(payload["final_decision_sha256"]),
        operator_identity=str(payload["operator_identity"]),
        approved_at=str(payload["approved_at"]),
    )


def _fail(
    status: GenerationStatus,
    message: str,
    record: GenerationRecord | None = None,
    **details: Any,
) -> CurrentnessResult:
    return CurrentnessResult(
        status=status,
        code=_STATUS_CODES[status],
        message=message,
        details=details,
        record=record,
    )


def _downgrade_evidence(ws: Path, screening_dir: Path) -> list[str]:
    """Name the authorized-material evidence surviving without a generation.

    Each signal means an authorized-collect pipeline ran in this workspace, so
    an absent ``generation.json`` is either unapproved review lineage (review
    evidence recorded before — or without — any authorization, no generation
    ever published) or a post-authorization deletion: both are MISMATCHED,
    never a true-legacy state. Which absence it is comes from whether a prior
    generation fingerprint is recorded anywhere (see
    ``_prior_generation_recorded`` and the ``lineage_without_generation`` /
    ``prior_generation_deleted`` detail flags); this helper only names the
    surviving material.

    * ``staged-approval``: ``publication_approval.json`` is resident (staged
      by review and left resident after publish; its mere presence is
      evidence, even when its bytes are unusable — a present-but-unusable
      file is an attempted authorization that fails closed elsewhere);
    * ``registry-lineage``: a registry ``screening_decisions`` envelope
      carrying ``decision_file_sha256`` lineage (written only by the
      post-review acceptance path);
    * ``manifest-lineage``: a MANIFEST batch row carrying accepted lineage
      (``decision_file_sha256`` / ``decisions_artifact_id``, merged only on
      per-batch acceptance — ``cmd_prepare`` rows never carry these keys).

    Old-format fixtures (E4 golden: MANIFEST rows and registry envelopes
    without those keys, no staged approval) match none of these signals and
    still read as true-legacy. Every read is guarded: an unreadable file is
    no evidence from that source, never a refusal by itself.
    """
    evidence: list[str] = []
    if (screening_dir / PUBLICATION_APPROVAL_FILENAME).is_file():
        evidence.append("staged-approval")
    try:
        manifest = json.loads(
            (screening_dir / "MANIFEST.json").read_text(encoding="utf-8")
        )
        batches = manifest.get("batches", []) if isinstance(manifest, dict) else []
        for batch in batches:
            if not isinstance(batch, dict):
                continue
            if "decision_file_sha256" in batch or "decisions_artifact_id" in batch:
                evidence.append("manifest-lineage")
                break
    except (OSError, ValueError):
        pass
    try:
        registry = json.loads(
            (ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return evidence
    artifacts = registry.get("artifacts", {}) if isinstance(registry, dict) else {}
    if not isinstance(artifacts, dict):
        return evidence
    for entry in artifacts.values():
        if not isinstance(entry, dict):
            continue
        if entry.get("artifact_type") != "screening_decisions":
            continue
        rel = entry.get("path")
        if not isinstance(rel, str) or not rel:
            continue
        try:
            envelope = json.loads((ws / rel).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(envelope, dict) and "decision_file_sha256" in envelope:
            evidence.append("registry-lineage")
            break
    return evidence


def _prior_generation_recorded(ws: Path, screening_dir: Path) -> bool:
    """True iff a generation fingerprint is recorded anywhere.

    Wording-only distinction for the absent-generation MISMATCHED branch (no
    behavior change: both outcomes refuse identically): a retained history
    record (``supersedes`` links chain prior generations), a
    ``SCREENING_GENERATION_PUBLISHED`` journal event, or a registry entry
    carrying a generation fingerprint means a generation was published and the
    absent ``generation.json`` is a post-authorization deletion. Otherwise the
    surviving material is unapproved review lineage — review evidence recorded
    before (or without) any authorization — and no generation was ever
    published. Every read is guarded: an unreadable file is no evidence from
    that source, never a refusal by itself.
    """
    try:
        history_dir = screening_dir / GENERATION_HISTORY_DIRNAME
        if history_dir.is_dir() and any(history_dir.glob("*.json")):
            return True
    except OSError:
        pass
    try:
        journal_text = (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8")
        if "SCREENING_GENERATION_PUBLISHED" in journal_text:
            return True
    except (OSError, ValueError):
        pass
    try:
        registry = json.loads(
            (ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return False
    artifacts = registry.get("artifacts", {}) if isinstance(registry, dict) else {}
    if not isinstance(artifacts, dict):
        return False
    for entry in artifacts.values():
        if not isinstance(entry, dict):
            continue
        if entry.get("artifact_type") == "screening_generation":
            return True
        if "generation_fingerprint" in entry:
            return True
    return False


def require_current_generation(
    workspace_dir: Path,
    *,
    presented: GenerationRecord | dict[str, Any] | None = None,
    revoked_fingerprints: frozenset[str] = frozenset(),
    max_age_seconds: int | None = None,
) -> CurrentnessResult:
    """Report whether the workspace's screening publication is CURRENT.

    Pure read: no writes, no clock reads (approval re-verification is anchored
    at the generation's own ``published_at``), no network. A generation is
    CURRENT iff the manifest parses under the expected schema, names this
    workspace/run, every listed output exists with the recorded digest, the
    resident approval resolves to a scope-matching approval for the recorded
    binding, the protocol parent is unchanged, and — when ``presented`` names
    an older record — no newer generation supersedes it.

    Downgrade prevention: an absent ``generation.json`` beside surviving
    authorized material (staged approval, registry/MANIFEST accepted lineage)
    reports MISMATCHED — either as unapproved review lineage (no generation
    was ever published; details carry ``lineage_without_generation: True``)
    or as a post-authorization deletion (a prior generation fingerprint is
    recorded; details carry ``prior_generation_deleted: True``). Deleting the
    record must never silently convert a workspace into consumable LEGACY.
    Only a workspace with no authorized material anywhere reports
    LEGACY_UNVERIFIED.
    """
    ws = Path(workspace_dir).resolve()
    literature_dir = ws / "literature"
    screening_dir = literature_dir / "screening"
    generation_path = screening_dir / GENERATION_FILENAME

    if not generation_path.is_file():
        evidence = _downgrade_evidence(ws, screening_dir)
        if evidence:
            # R3 wording distinction (no behavior change): unapproved review
            # lineage vs post-authorization deletion both refuse as MISMATCHED;
            # only the message and detail flags name which absence this is.
            if _prior_generation_recorded(ws, screening_dir):
                return _fail(
                    GenerationStatus.MISMATCHED,
                    "screening generation record is absent while a prior "
                    "authorized generation is recorded; refusing a "
                    "post-authorization deletion/downgrade, never legacy",
                    downgrade_evidence=evidence,
                    prior_generation_deleted=True,
                    lineage_without_generation=False,
                    generation_path=str(generation_path),
                )
            return _fail(
                GenerationStatus.MISMATCHED,
                "screening generation record is absent while unapproved review "
                "lineage survives (reviewed pre-authorization, no generation "
                "ever published); refusing, never legacy",
                downgrade_evidence=evidence,
                lineage_without_generation=True,
                prior_generation_deleted=False,
                generation_path=str(generation_path),
            )
        return _fail(
            GenerationStatus.LEGACY_UNVERIFIED,
            "no screening generation record beside the outputs; "
            "legacy outputs are not authorized-current",
            generation_path=str(generation_path),
        )
    try:
        raw_text = generation_path.read_bytes().decode("utf-8")
        payload = json.loads(raw_text)
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        return _fail(
            GenerationStatus.STALE,
            f"generation record is unreadable ({exc}); refusing to treat "
            "the outputs as current",
            generation_path=str(generation_path),
        )
    if not isinstance(payload, dict) or payload.get("schema") != GENERATION_SCHEMA:
        return _fail(
            GenerationStatus.MISMATCHED,
            "generation record carries an unexpected schema; refusing to "
            "consume it as an authorized generation",
            schema=payload.get("schema") if isinstance(payload, dict) else None,
            generation_path=str(generation_path),
        )
    try:
        record = GenerationRecord.from_dict(payload)
    except ValueError as exc:
        return _fail(
            GenerationStatus.STALE,
            f"generation record is incomplete ({exc})",
            generation_path=str(generation_path),
        )

    registered = _workspace_identity(ws)
    if registered is None:
        return _fail(
            GenerationStatus.MISMATCHED,
            "workspace records no registered identity, so the generation "
            "scope cannot be confirmed",
            generation_id=record.generation_id,
            record=record,
        )
    if registered != record.workspace_id:
        return _fail(
            GenerationStatus.MISMATCHED,
            "generation was published for a different workspace; refusing "
            "cross-workspace replay",
            generation_id=record.generation_id,
            expected_workspace_id=registered,
            record_workspace_id=record.workspace_id,
            record=record,
        )

    manifest_run = _manifest_run_id(ws)
    if manifest_run is not None and manifest_run != record.run_id:
        return _fail(
            GenerationStatus.MISMATCHED,
            "generation was published for a different screening run",
            generation_id=record.generation_id,
            expected_run_id=manifest_run,
            record_run_id=record.run_id,
            record=record,
        )

    history = _iter_history(screening_dir)
    for name in PUBLICATION_OUTPUTS:
        expected = record.output_digests[name]
        path = literature_dir / name
        try:
            actual = content_sha256(path.read_bytes()) if path.is_file() else None
        except OSError:
            actual = None
        if actual == expected:
            continue
        for older in history:
            if older.fingerprint() == record.fingerprint():
                continue
            if older.output_digests.get(name) == actual:
                return _fail(
                    GenerationStatus.MISMATCHED,
                    f"{name} matches retained generation {older.generation_id}, "
                    "not the current one; refusing mixed-generation assembly",
                    generation_id=record.generation_id,
                    output=name,
                    matched_generation_id=older.generation_id,
                    record=record,
                )
        return _fail(
            GenerationStatus.STALE,
            f"{name} is missing or no longer matches the recorded digest",
            generation_id=record.generation_id,
            output=name,
            expected_digest=expected,
            actual_digest=actual,
            record=record,
        )

    approval_path = screening_dir / PUBLICATION_APPROVAL_FILENAME
    if not approval_path.is_file():
        return _fail(
            GenerationStatus.STALE,
            "resident publication approval is missing; the generation can no "
            "longer be resolved to its authorization",
            generation_id=record.generation_id,
            record=record,
        )
    try:
        sidecar = json.loads(approval_path.read_text(encoding="utf-8"))
        if not isinstance(sidecar, dict):
            raise ValueError("approval sidecar is not a JSON object")
        if sidecar.get("schema") != PUBLICATION_APPROVAL_SCHEMA:
            raise ValueError(
                f"unexpected approval sidecar schema {sidecar.get('schema')!r}"
            )
        approval = _approval_from_dict(sidecar["approval"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return _fail(
            GenerationStatus.STALE,
            f"resident publication approval is unreadable ({exc})",
            generation_id=record.generation_id,
            record=record,
        )
    if approval.fingerprint() != record.approval_fingerprint:
        return _fail(
            GenerationStatus.STALE,
            "resident approval no longer matches the recorded approval fingerprint",
            generation_id=record.generation_id,
            record=record,
        )
    expected_binding = publication_binding(
        workspace_id=record.workspace_id,
        run_id=record.run_id,
        batch_bindings=[dict(b) for b in record.batch_bindings],
        protocol_fingerprint=record.protocol_fingerprint,
        corpus_fingerprint=record.corpus_fingerprint,
        policy_version=record.policy_version,
    )
    snapshot = build_publication_snapshot(
        workspace_id=record.workspace_id,
        run_id=record.run_id,
        batch_bindings=[dict(b) for b in record.batch_bindings],
        protocol_fingerprint=record.protocol_fingerprint,
        corpus_fingerprint=record.corpus_fingerprint,
        output_digests=record.output_digests,
    )
    try:
        verify_approval(
            record=approval,
            expected_binding=expected_binding,
            reviewed_bytes=snapshot,
            final_decision_bytes=snapshot,
            policy_version=record.policy_version,
            now=record.published_at,
            revoked_fingerprints=revoked_fingerprints,
            max_age_seconds=max_age_seconds,
        )
    except AuthorityRefused as refusal:
        if refusal.code in (APPROVAL_SCOPE_MISMATCH, APPROVAL_POLICY_MISMATCH):
            return _fail(
                GenerationStatus.MISMATCHED,
                f"recorded approval no longer resolves ({refusal.code})",
                generation_id=record.generation_id,
                approval_code=refusal.code,
                record=record,
            )
        return _fail(
            GenerationStatus.STALE,
            f"recorded approval no longer resolves ({refusal.code})",
            generation_id=record.generation_id,
            approval_code=refusal.code,
            record=record,
        )

    protocol_fp = _protocol_fingerprint(ws)
    if protocol_fp is None:
        return _fail(
            GenerationStatus.STALE,
            "workspace protocol is unreadable, so the recorded protocol "
            "parent cannot be confirmed",
            generation_id=record.generation_id,
            record=record,
        )
    if protocol_fp != record.protocol_fingerprint:
        return _fail(
            GenerationStatus.STALE,
            "workspace protocol changed after publication",
            generation_id=record.generation_id,
            expected_protocol_fingerprint=record.protocol_fingerprint,
            actual_protocol_fingerprint=protocol_fp,
            record=record,
        )

    if presented is not None:
        try:
            presented_record = (
                presented
                if isinstance(presented, GenerationRecord)
                else GenerationRecord.from_dict(presented)
            )
        except ValueError as exc:
            return _fail(
                GenerationStatus.MISMATCHED,
                f"presented generation record is unreadable ({exc})",
                generation_id=record.generation_id,
                record=record,
            )
        if presented_record.fingerprint() == record.fingerprint():
            return CurrentnessResult(
                status=GenerationStatus.CURRENT,
                code=None,
                message="presented generation is the current one",
                details={"generation_id": record.generation_id},
                record=record,
            )
        if presented_record.supersedes == record.fingerprint():
            # The workspace manifest was reverted: the caller holds a newer
            # generation whose chain links the on-disk one. The workspace is
            # not current.
            return _fail(
                GenerationStatus.SUPERSEDED,
                "the on-disk generation is superseded by a newer generation "
                "the caller holds (manifest was reverted, not re-published)",
                newer_generation_id=presented_record.generation_id,
                workspace_generation_id=record.generation_id,
                record=record,
            )
        chain: GenerationRecord | None = record
        seen = {record.fingerprint()}
        while chain is not None and chain.supersedes is not None:
            if chain.supersedes == presented_record.fingerprint():
                return _fail(
                    GenerationStatus.SUPERSEDED,
                    "a newer generation supersedes the presented one",
                    current_generation_id=record.generation_id,
                    presented_generation_id=presented_record.generation_id,
                    record=record,
                )
            parent = next(
                (older for older in history if older.fingerprint() == chain.supersedes),
                None,
            )
            if parent is None or parent.fingerprint() in seen:
                break
            seen.add(parent.fingerprint())
            chain = parent
        return _fail(
            GenerationStatus.MISMATCHED,
            "presented generation is neither current nor superseded by the "
            "current chain",
            current_generation_id=record.generation_id,
            presented_generation_id=presented_record.generation_id,
            record=record,
        )

    return CurrentnessResult(
        status=GenerationStatus.CURRENT,
        code=None,
        message="screening generation is current",
        details={"generation_id": record.generation_id},
        record=record,
    )


# --- crash recovery ----------------------------------------------------------- #


def recover_partial(workspace_dir: Path) -> dict[str, Any]:
    """Remove a crashed publish's uncommittable staging (tmps + stale lock).

    Tmp files are never consumable, and an orphaned lock only ever belongs to
    a dead publisher (a live holder is released by its own ``finally``), so
    both are safe to sweep explicitly. Committed outputs are never touched:
    after recovery, outputs without a matching generation are still reported
    as not-current until an authorized re-collect publishes one.
    """
    ws = Path(workspace_dir).resolve()
    literature_dir = ws / "literature"
    screening_dir = literature_dir / "screening"
    removed = _remove_paths(_tmp_paths(literature_dir, screening_dir))
    lock_path = screening_dir / COLLECT_LOCK_FILENAME
    try:
        if lock_path.is_file() or lock_path.is_symlink():
            lock_path.unlink()
            removed.append(lock_path.name)
    except OSError:
        pass
    return {"removed": sorted(removed)}
