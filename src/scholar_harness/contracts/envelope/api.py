"""Module API for ``Envelope@1``: validate, verify_parents, diff, ids.

Validation order follows spec 02 §8 exactly:

1. schema (pydantic model; unknown closed-vocabulary strings name themselves),
2. invariants (§3 status algebra),
3. hashes (§4: ``output_sha256`` and ``envelope_id`` recomputation),
4. parent binding (§5, only when ``verify_parents=True``),
5. role existence / version compatibility against ``roles/*.json``.

The schema-name check (``output.schema`` and ``inputs[*].schema`` against the
declared schemas of the role record, and the payload-model registry) sits in
step 5 with the other role-record cross-checks: it is the role record that
declares which schemas a role may produce and consume, so the near-miss refusal
needs the record. The spec's §8 step order is unchanged.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any

from pydantic import ValidationError

from ..canonical import canonical_json_bytes
from ..models import (
    ClaimEvidenceData,
    CorpusSnapshotData,
    DocumentManifestData,
    ScreeningBatchData,
    ScreeningDecisionsData,
)
from .model import (
    BLOCKED_STATUSES,
    Envelope,
    EnvelopeStatus,
    PayloadStatuses,
    RefusalStatuses,
)
from .registry import ANY_EMITTER_CODES, RefusalCode, allowed_emitter_roles

ENVELOPE_ID_ALGORITHM_VERSION = "v1"
_ENVELOPE_ID_HEX = 16

#: Payload schemas this module can bind to a Contract v1 data model.
#:
#: A name that is *declared by the role record* but absent here is refused with
#: a named INVALID_OUTPUT at the role-compatibility step: an envelope whose
#: payload nobody in the harness can validate must not pass silently. A name
#: that the record does not declare at all is refused as a schema-name mismatch.
#: Only when ``roles_dir`` is unavailable (library use without role records)
#: does an unregistered name still travel opaquely — see decision record D11.
PAYLOAD_MODELS: dict[str, type] = {
    "ScreeningDecisions@1": ScreeningDecisionsData,
    "ScreeningBatch@1": ScreeningBatchData,
    "CorpusSnapshot@1": CorpusSnapshotData,
    "DocumentManifest@1": DocumentManifestData,
    "ClaimsLedger@1": ClaimEvidenceData,
}


class EnvelopeRefusalError(Exception):
    """Raised with the *right* refusal code, never a generic wrapper.

    Attributes:
        refusal_code: registry code a consumer should record (e.g.
            ``PARENT_HASH_MISMATCH`` or ``BLOCKED_INPUT``).
        detail: human-readable finding. Schema/invariant/hash defects are
            ``INVALID_OUTPUT``-family findings (spec 02 §5 wording).
    """

    def __init__(self, refusal_code: RefusalCode, detail: str) -> None:
        self.refusal_code = refusal_code
        self.code = refusal_code
        self.detail = detail
        super().__init__(f"{refusal_code}: {detail}")


# ---------------------------------------------------------------------------
# Hashing (spec 02 §4)
# ---------------------------------------------------------------------------


def _hash_source(envelope: Mapping[str, Any] | Envelope) -> dict[str, Any]:
    if isinstance(envelope, Mapping):
        return dict(envelope)
    return envelope.model_dump()


def envelope_id(envelope: Mapping[str, Any] | Envelope) -> str:
    """Deterministic identity over the immutable envelope fields.

    Covers ``role``, ``role_version``, ``task_id``, ``arm``, ``status``,
    ``inputs[*].sha256``, ``parents[*].sha256`` and ``output_sha256``.
    ``created_at``, ``duration_ms`` and ``provenance.adapter*`` are excluded:
    timing must never change identity, so a retried attempt (the adapter
    retries, never the role) with identical inputs yields the same logical
    envelope.
    """

    raw = _hash_source(envelope)
    status = raw.get("status")
    if isinstance(status, EnvelopeStatus):
        status = status.value
    fabric = {
        "algorithm_version": ENVELOPE_ID_ALGORITHM_VERSION,
        "role": raw.get("role"),
        "role_version": raw.get("role_version"),
        "task_id": raw.get("task_id"),
        "arm": raw.get("arm"),
        "status": status,
        "input_hashes": [entry.get("sha256") for entry in raw.get("inputs") or []],
        "parent_hashes": [entry.get("sha256") for entry in raw.get("parents") or []],
        "output_sha256": raw.get("output_sha256"),
    }
    digest = sha256(canonical_json_bytes(fabric)).hexdigest()
    return f"ENV-{digest[:_ENVELOPE_ID_HEX]}"


def output_sha256(envelope: Mapping[str, Any] | Envelope) -> str | None:
    """Canonical JSON hash of ``output.data`` only; ``None`` when no payload.

    Two runs producing identical payloads agree here even if they differ in
    timing.
    """

    raw = _hash_source(envelope)
    output = raw.get("output")
    if not isinstance(output, Mapping) or output.get("data") is None:
        return None
    return sha256(canonical_json_bytes(output["data"])).hexdigest()


# ---------------------------------------------------------------------------
# Role records (Phase A artifacts; read-only cross-check)
# ---------------------------------------------------------------------------


def _role_record(role: str, roles_dir: Path) -> dict[str, Any]:
    record_path = roles_dir / f"{role}.json"
    if not record_path.is_file():
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT,
            f"unknown role {role!r}: no roles/{role}.json under {roles_dir}",
        )
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT, f"role record for {role!r} unreadable: {exc}"
        ) from exc
    if not isinstance(record, dict) or record.get("id") != role:
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT,
            f"roles/{role}.json does not declare id {role!r}",
        )
    return record


def find_roles_dir(start: Path) -> Path | None:
    """Locate the ``roles/`` directory by walking up from ``start``."""

    for candidate in (start, *start.parents):
        if (candidate / "roles" / "screener.json").is_file():
            return candidate / "roles"
    return None


def _version_major(version: str) -> int | None:
    head = version.split(".")[0]
    return int(head) if head.isdigit() else None


def _refusal_allowed_for_role(
    code: str, role: str, record_codes: set[str]
) -> str | None:
    """Return a finding string, or ``None`` when ``role`` may emit ``code``."""

    if code not in {member.value for member in RefusalCode}:
        return f"unknown refusal code {code!r}"
    emitter_roles = allowed_emitter_roles(RefusalCode(code))
    if emitter_roles is not None and role not in emitter_roles:
        return (
            f"role {role!r} may not emit {code!r}; "
            f"registry allows {sorted(emitter_roles)}"
        )
    if code not in record_codes and code not in ANY_EMITTER_CODES:
        return (
            f"role {role!r} does not declare {code!r} in its refusal_codes, and "
            "the registry does not mark it emittable by any role"
        )
    return None


def _declared_schemas(record: dict[str, Any], field: str) -> set[str]:
    """Schemas a role record declares under ``outputs``/``inputs``.

    An empty return means the record declares *nothing* under ``field`` (field
    absent, non-list, or no entry carrying a string ``schema``). All eleven
    shipped role records declare both fields; for a record that does not, the
    legacy behaviour holds — the name travels opaquely (D11), we do not guess.
    """

    entries = record.get(field)
    if not isinstance(entries, list):
        return set()
    return {
        entry["schema"]
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("schema"), str)
    }


def _check_role_compatibility(envelope: Envelope, roles_dir: Path | None) -> None:
    if roles_dir is None:
        return
    record = _role_record(envelope.role, roles_dir)
    record_version = record.get("version")
    if not isinstance(record_version, str):
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT,
            f"roles/{envelope.role}.json has no semver 'version' field",
        )
    envelope_major = _version_major(envelope.role_version)
    record_major = _version_major(record_version)
    if envelope_major is None or record_major is None or envelope_major != record_major:
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT,
            f"role_version {envelope.role_version!r} is incompatible with "
            f"{envelope.role}@{record_version} (major versions must match)",
        )

    record_codes = {
        code for code in (record.get("refusal_codes") or []) if isinstance(code, str)
    }
    claimed: list[str] = []
    if envelope.refusal is not None:
        claimed = [envelope.refusal.code, *envelope.refusal.codes]
    for name in claimed:
        finding = _refusal_allowed_for_role(name, envelope.role, record_codes)
        if finding:
            raise EnvelopeRefusalError(RefusalCode.INVALID_OUTPUT, finding)

    # Spec 02 §2 field rule: arm present whenever isolation is not none;
    # §5 blinded_from consistency against the role declaration.
    if envelope.provenance.isolation != "none" and envelope.arm is None:
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT,
            f"arm is required when isolation is {envelope.provenance.isolation!r}",
        )
    record_blinded = set(record.get("independence", {}).get("blinded_from") or [])
    for entry in envelope.provenance.blinded_from or []:
        peer, _, suffix = entry.partition("@")
        peer_arm = suffix if suffix in {"A", "B"} else None
        same_role = peer == envelope.role and peer_arm != envelope.arm
        if peer not in record_blinded and not same_role:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT,
                f"blinded_from claims {entry!r}, which the {envelope.role!r} "
                "declaration does not grant",
            )

    # Schema-name compatibility (role records are the schema-name authority).
    # A typo such as `ScreeningDecisions@2` must defeat acceptance loudly: the
    # refusal names both the claimed and the declared names, so a consumer can
    # render it — silent-accept-by-misspelling is not the contract.
    declared_outputs = _declared_schemas(record, "outputs")
    if envelope.output is not None:
        claimed = envelope.output.schema_
        if declared_outputs and claimed not in declared_outputs:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT,
                f"output.schema {claimed!r} is not one that role "
                f"{envelope.role!r} declares (declared: {sorted(declared_outputs)})",
            )
        if claimed in declared_outputs and claimed not in PAYLOAD_MODELS:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT,
                f"payload schema {claimed!r} is declared by role "
                f"{envelope.role!r} but is not registered with the harness "
                "(no Contract v1 data model): no validator can bind it, so it "
                "is refused rather than accepted unvalidated",
            )
    declared_inputs = _declared_schemas(record, "inputs")
    if declared_inputs:
        for index, entry in enumerate(envelope.inputs):
            if entry.schema_ not in declared_inputs:
                raise EnvelopeRefusalError(
                    RefusalCode.INVALID_OUTPUT,
                    f"inputs[{index}].schema {entry.schema_!r} is not one that "
                    f"role {envelope.role!r} declares "
                    f"(declared: {sorted(declared_inputs)})",
                )


# ---------------------------------------------------------------------------
# Loading and schema step
# ---------------------------------------------------------------------------


def _load(payload: Mapping[str, Any] | str | bytes | Path) -> dict[str, Any]:
    if isinstance(payload, Mapping):
        return dict(payload)
    try:
        if isinstance(payload, Path):
            text = payload.read_text(encoding="utf-8")
        elif isinstance(payload, bytes):
            text = payload.decode("utf-8")
        else:
            text = payload
    except (OSError, UnicodeDecodeError) as exc:
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT, f"envelope file unreadable: {exc}"
        ) from exc
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT,
            f"envelope is not valid JSON: {exc}",
        ) from exc
    if not isinstance(value, dict):
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT, "envelope must be a JSON object"
        )
    return value


def _schema_step(payload: dict[str, Any]) -> Envelope:
    statuses = {item.value for item in EnvelopeStatus}
    status = payload.get("status")
    if not isinstance(status, str) or status not in statuses:
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT,
            f"unknown status {status!r}; allowed: {sorted(statuses)}",
        )
    refusal = payload.get("refusal")
    if isinstance(refusal, Mapping):
        registered = {member.value for member in RefusalCode}
        code = refusal.get("code")
        if code is not None and code not in registered:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT,
                f"unknown refusal code {code!r}; allowed: {sorted(registered)}",
            )
        for listed in refusal.get("codes") or []:
            if listed not in registered:
                raise EnvelopeRefusalError(
                    RefusalCode.INVALID_OUTPUT,
                    f"unknown refusal code {listed!r}; allowed: {sorted(registered)}",
                )
    try:
        return Envelope.model_validate(payload)
    except ValidationError as exc:
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT,
            "envelope schema validation failed: "
            + "; ".join(
                f"{'/'.join(str(part) for part in error['loc'])}: {error['msg']}"
                for error in exc.errors(include_url=False)
            ),
        ) from exc


# ---------------------------------------------------------------------------
# Payload schema validation (the envelope never rescues a payload)
# ---------------------------------------------------------------------------


def _validate_payload_schema(envelope: Envelope) -> None:
    model = PAYLOAD_MODELS.get(envelope.output.schema_)
    if model is None:
        return
    try:
        model.model_validate(envelope.output.data)
    except ValidationError as exc:
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT,
            f"payload {envelope.output.schema_} failed its Contract v1 schema: "
            + "; ".join(
                f"{'/'.join(str(part) for part in error['loc'])}: {error['msg']}"
                for error in exc.errors(include_url=False)[:5]
            ),
        ) from exc
    # The Contract v1 data models are forward-compatible at nested levels
    # (extra="allow" for unknown minor-version fields), so the payload's own
    # schema cannot reject a contraband field. Spec 02 §8 still demands the
    # envelope does not rescue it: the top-level payload object is checked
    # strictly against the fields the frozen schema defines, while nested
    # forward-compat fields keep flowing under the frozen policy.
    declared = set(model.model_fields)
    contraband = sorted(set(envelope.output.data) - declared)
    if contraband:
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT,
            f"payload {envelope.output.schema_} carries fields the schema does "
            f"not define: {contraband}",
        )


# ---------------------------------------------------------------------------
# Invariant step (spec 02 §3 status algebra)
# ---------------------------------------------------------------------------


def _invariant_step(envelope: Envelope) -> None:
    state = envelope.status
    has_output = envelope.output is not None
    refusal = envelope.refusal
    findings = (refusal.validation_findings or []) if refusal else []
    registered = {member.value for member in RefusalCode}

    # Unknown code in the multi-code list; the scalar is closed at schema step.
    for name in (envelope.refusal.codes if envelope.refusal else None) or []:
        if name not in registered:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT,
                f"unknown refusal code {name!r}; allowed: {sorted(registered)}",
            )

    if (
        state not in PayloadStatuses
        and state is not EnvelopeStatus.GATE_FAILED
        and has_output
    ):
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT,
            f"{state.value} must ship no payload; a blocked envelope that "
            "carries one invites downstream use of data the role did not "
            "stand behind",
        )

    if state is EnvelopeStatus.OK:
        if refusal is not None:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT, "refusal must be null for OK"
            )
        if not has_output or envelope.coverage is None:
            missing = "output" if not has_output else "coverage"
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT, f"OK requires {missing}"
            )
        _validate_payload_schema(envelope)
        if envelope.coverage.produced != envelope.coverage.expected:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT,
                "OK requires coverage.produced == expected; "
                f"{envelope.coverage.produced} != {envelope.coverage.expected} "
                "(that is PARTIAL, not OK)",
            )
    elif state is EnvelopeStatus.PARTIAL:
        if not has_output:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT, "PARTIAL requires an output"
            )
        if envelope.coverage is None:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT, "PARTIAL requires coverage"
            )
        if envelope.coverage.produced >= envelope.coverage.expected:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT,
                f"PARTIAL requires coverage.produced < expected "
                f"({envelope.coverage.produced} >= {envelope.coverage.expected})",
            )
        if refusal is None or not (refusal.codes or refusal.code):
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT,
                "PARTIAL requires refusal codes naming the gap",
            )
        _validate_payload_schema(envelope)
    elif state in BLOCKED_STATUSES:
        if refusal is None:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT, f"{state.value} requires a refusal"
            )
        if not envelope.human_action_required:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT,
                f"{state.value} requires human_action_required",
            )
    elif state is EnvelopeStatus.PROVIDER_TRANSIENT:
        if refusal is None:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT, "PROVIDER_TRANSIENT requires a refusal"
            )
        if refusal.code != RefusalCode.PROVIDER_TRANSIENT.value:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT,
                f"PROVIDER_TRANSIENT requires refusal.code PROVIDER_TRANSIENT; "
                f"received {refusal.code!r}",
            )
        if not envelope.retryable:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT,
                "PROVIDER_TRANSIENT is retryable (the adapter retries, never the role)",
            )
        if envelope.human_action_required:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT,
                "a transient provider failure requires no human action",
            )
    elif state is EnvelopeStatus.REFUSED:
        if refusal is None:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT, "REFUSED requires a refusal"
            )
    elif state is EnvelopeStatus.INVALID_OUTPUT:
        if refusal is None:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT, "INVALID_OUTPUT requires a refusal"
            )
        if not findings:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT,
                "INVALID_OUTPUT requires non-empty validation findings",
            )
    elif state is EnvelopeStatus.GATE_FAILED:
        if refusal is None:
            raise EnvelopeRefusalError(
                RefusalCode.INVALID_OUTPUT,
                "GATE_FAILED requires a refusal recording the gate evidence",
            )

    # Refusal with a non-refusal status is a defect (§8 matrix).
    if state not in RefusalStatuses and refusal is not None:
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT,
            f"refusal present with a non-refusal status ({state.value})",
        )


# ---------------------------------------------------------------------------
# Hash step (spec 02 §4)
# ---------------------------------------------------------------------------


def _hash_step(envelope: Envelope) -> None:
    expected = output_sha256(envelope)
    if envelope.output_sha256 != expected:
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT,
            f"output_sha256 does not match the payload (expected {expected}, "
            f"envelope claims {envelope.output_sha256})",
        )
    recomputed = envelope_id(envelope)
    if envelope.envelope_id != recomputed:
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT,
            f"envelope_id tampered: envelope claims {envelope.envelope_id}, "
            f"recomputed {recomputed}",
        )


# ---------------------------------------------------------------------------
# Parent binding (spec 02 §5)
# ---------------------------------------------------------------------------


def _binding_failure(relative: str, *, missing: bool, detail: str) -> None:
    if missing:
        raise EnvelopeRefusalError(
            RefusalCode.BLOCKED_INPUT,
            f"parent {relative!r} is absent from disk ({detail})",
        )
    raise EnvelopeRefusalError(
        RefusalCode.PARENT_HASH_MISMATCH,
        f"parent {relative!r} declared hash does not match disk ({detail}) — "
        "lineage broken; silent re-binding rejected",
    )


def verify_parents(
    envelope: Envelope | Mapping[str, Any], root: str | Path
) -> list[str]:
    """Verify ``parents[*]``/``inputs[*]`` hashes against the files on disk.

    Returns the verified relative paths. A missing file raises
    ``BLOCKED_INPUT``; a present file whose raw content hash differs from the
    declared one raises ``PARENT_HASH_MISMATCH`` — never a warning, never a
    silent re-bind.
    """

    if not isinstance(envelope, Envelope):
        envelope = _schema_step(
            envelope if isinstance(envelope, Mapping) else _load(envelope)
        )
    base = Path(root)
    verified: list[str] = []
    verified.extend(
        _verify_one(base, entry.artifact, entry.sha256) for entry in envelope.parents
    )
    verified.extend(
        _verify_one(base, entry.path, entry.sha256)
        for entry in envelope.inputs
        if entry.path
    )
    return verified


_verify_parents = verify_parents  # aliased: a validate() kwarg shadows the name


def _verify_one(base: Path, relative: str, declared: str) -> str:
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise EnvelopeRefusalError(
            RefusalCode.SCOPE_VIOLATION,
            f"envelope references a path outside its root: {relative!r}",
        )
    path = base / Path(*candidate.parts)
    try:
        content = path.read_bytes()
    except OSError as exc:
        _binding_failure(relative, missing=True, detail=str(exc))
    digest = sha256(content).hexdigest()
    if digest != declared:
        _binding_failure(
            relative,
            missing=False,
            detail=f"disk hash {digest}, envelope declares {declared}",
        )
    return relative


# ---------------------------------------------------------------------------
# Full validation
# ---------------------------------------------------------------------------


def validate(
    envelope: Mapping[str, Any] | str | bytes | Path,
    *,
    verify_parents: bool = False,
    root: str | Path | None = None,
    roles_dir: str | Path | None = None,
) -> Envelope:
    """Validate one ``Envelope@1``; raise ``EnvelopeRefusalError`` on any defect."""

    payload = _load(envelope)
    model = _schema_step(payload)
    _invariant_step(model)
    _hash_step(model)
    if verify_parents:
        if root is None:
            raise EnvelopeRefusalError(
                RefusalCode.BLOCKED_INPUT, "verify_parents requires a root"
            )
        _verify_parents(model, root)
    _check_role_compatibility(model, Path(roles_dir) if roles_dir else None)
    return model


# ---------------------------------------------------------------------------
# diff (spec 02 §4)
# ---------------------------------------------------------------------------

IDENTITY_FIELDS = ("role", "role_version", "task_id", "arm", "status")


class EnvelopeDiff:
    """Structured result of ``diff(a, b)``."""

    def __init__(self) -> None:
        self.differing_fields: list[str] = []
        self.hash_changes: dict[str, dict[str, Any]] = {}
        self.timing_only: list[str] = []
        self.same_output_different_identifiers: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "differing_fields": self.differing_fields,
            "timing_only": self.timing_only,
            "hash_changes": self.hash_changes,
            "same_output_different_identifiers": self.same_output_different_identifiers,
        }


def diff(
    envelope_a: Mapping[str, Any] | str | bytes,
    envelope_b: Mapping[str, Any] | str | bytes,
) -> EnvelopeDiff:
    """Report the differing fields of two envelopes, naming hash changes.

    §4 surfacing: when ``output_sha256`` matches but ``envelope_id`` differs,
    the report names *which* immutable field or input differed — two different
    ``envelope_id``s with an identical payload mean the inputs differed.
    """

    if not isinstance(envelope_a, Mapping):
        envelope_a = _load(envelope_a)
    if not isinstance(envelope_b, Mapping):
        envelope_b = _load(envelope_b)
    parsed_a = _schema_step(envelope_a)
    parsed_b = _schema_step(envelope_b)
    report = EnvelopeDiff()

    for name in (
        *IDENTITY_FIELDS,
        "retryable",
        "human_action_required",
        "coverage",
    ):
        if getattr(parsed_a, name) != getattr(parsed_b, name):
            report.differing_fields.append(name)
    if parsed_a.refusal != parsed_b.refusal:
        report.differing_fields.append("refusal")
    provenance_a, provenance_b = parsed_a.provenance, parsed_b.provenance
    timing_pairs = {
        "created_at": (parsed_a.created_at, parsed_b.created_at),
        "provenance.duration_ms": (provenance_a.duration_ms, provenance_b.duration_ms),
        "provenance.adapter": (provenance_a.adapter, provenance_b.adapter),
        "provenance.adapter_version": (
            provenance_a.adapter_version,
            provenance_b.adapter_version,
        ),
    }
    for name, (value_a, value_b) in timing_pairs.items():
        if value_a != value_b:
            report.timing_only.append(name)
    for key in ("isolation", "blinded_from"):
        if getattr(provenance_a, key) != getattr(provenance_b, key):
            report.differing_fields.append(f"provenance.{key}")

    for digest_field in ("envelope_id", "output_sha256"):
        value_a = getattr(parsed_a, digest_field)
        value_b = getattr(parsed_b, digest_field)
        if value_a == value_b:
            continue
        report.hash_changes[digest_field] = {"a": value_a, "b": value_b}
        report.differing_fields.append(digest_field)

    if parsed_a.output_sha256 == parsed_b.output_sha256 and (
        parsed_a.envelope_id != parsed_b.envelope_id
    ):
        causes: list[str] = []

        def plain(value: object) -> object:
            return value.value if isinstance(value, EnvelopeStatus) else value

        for name in IDENTITY_FIELDS:
            value_a = plain(getattr(parsed_a, name))
            value_b = plain(getattr(parsed_b, name))
            if value_a != value_b:
                causes.append(f"{name}: {value_a!r} vs {value_b!r}")
        if parsed_a.inputs != parsed_b.inputs:
            hashes_a = [entry.sha256 for entry in parsed_a.inputs]
            hashes_b = [entry.sha256 for entry in parsed_b.inputs]
            if len(hashes_a) == len(hashes_b):
                for index, (hash_a, hash_b) in enumerate(zip(hashes_a, hashes_b)):
                    if hash_a != hash_b:
                        causes.append(f"inputs[{index}].sha256: {hash_a} vs {hash_b}")
                if [entry.role_version for entry in parsed_a.inputs] != [
                    entry.role_version for entry in parsed_b.inputs
                ]:
                    causes.append("inputs[*].role_version differ")
                if [entry.path for entry in parsed_a.inputs] != [
                    entry.path for entry in parsed_b.inputs
                ]:
                    causes.append("inputs[*].path differ")
            else:
                causes.append(
                    f"inputs length differs: {len(hashes_a)} vs {len(hashes_b)}"
                )
        if parsed_a.parents != parsed_b.parents:
            causes.append("parents[*] differ")
        if not causes:
            # No §4-field reason found: the reported id does not match its own
            # recomputation (a tampered id or an id-algorithm bug).
            recomputed_a, recomputed_b = envelope_id(parsed_a), envelope_id(parsed_b)
            if parsed_a.envelope_id != recomputed_a:
                causes.append(
                    f"envelope_id(a) {parsed_a.envelope_id!r} does not match its "
                    f"own recomputation {recomputed_a!r}"
                )
            if parsed_b.envelope_id != recomputed_b:
                causes.append(
                    f"envelope_id(b) {parsed_b.envelope_id!r} does not match its "
                    f"own recomputation {recomputed_b!r}"
                )
        report.same_output_different_identifiers = (
            "identical payload (output_sha256 agrees) but different envelope_id: "
            "the inputs differed — " + "; ".join(causes)
        )
    return report
