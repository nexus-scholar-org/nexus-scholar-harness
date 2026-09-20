"""Fail-closed acceptance and publication gate for Contract v1 artifacts."""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from scholar_harness.console.api.audit import log_event

from .canonical import canonical_fingerprint, canonical_json_bytes
from .identifiers import IdentifierKind, validate_identifier
from .models import (
    ArtifactEnvelope,
    ClaimEvidenceLedger,
    CorpusSnapshotArtifact,
    DocumentManifestArtifact,
    Producer,
    RunManifest,
    ScreeningBatchArtifact,
    ScreeningDecisionsArtifact,
)

_ARTIFACT_MODELS: dict[str, type[ArtifactEnvelope[Any]]] = {
    "claims_ledger": ClaimEvidenceLedger,
    "corpus_snapshot": CorpusSnapshotArtifact,
    "document_manifest": DocumentManifestArtifact,
    "run_manifest": RunManifest,
    "screening_batch": ScreeningBatchArtifact,
    "screening_decisions": ScreeningDecisionsArtifact,
}

_REQUIRED_PARENT_TYPE = {
    "screening_batch": "corpus_snapshot",
    "screening_decisions": "screening_batch",
    "document_manifest": "screening_decisions",
    "claims_ledger": "document_manifest",
}

_REGISTRY_PATH = PurePosixPath("audit/artifact_registry.json")
_MAX_ISSUES = 20
_MAX_MESSAGE_LENGTH = 500
_SHA256_PATTERN = r"^sha256:[0-9a-f]{64}$"


class AcceptanceContext(BaseModel):
    """Workspace generation that an inbound artifact must match."""

    model_config = ConfigDict(extra="forbid")

    workspace_id: str
    protocol_fingerprint: str = Field(pattern=_SHA256_PATTERN)
    corpus_fingerprint: str = Field(pattern=_SHA256_PATTERN)

    @field_validator("workspace_id")
    @classmethod
    def workspace_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.WORKSPACE, value)


class RegistryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_type: str = Field(min_length=1)
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=_SHA256_PATTERN)
    accepted_at: datetime
    run_id: str
    producer: Producer


class ArtifactRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = "1.0.0"
    artifacts: dict[str, RegistryEntry] = Field(default_factory=dict)


class AcceptanceIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    artifact_id: str | None = None
    related_id: str | None = None


class AcceptanceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted: bool
    payload_hash: str
    artifact_id: str | None = None
    artifact_type: str | None = None
    published_path: str | None = None
    rejection_path: str | None = None
    event_id: str | None = None
    idempotent: bool = False
    issues: list[AcceptanceIssue] = Field(default_factory=list)


def _issue(code: str, message: str, **ids: str | None) -> AcceptanceIssue:
    bounded = message[:_MAX_MESSAGE_LENGTH]
    return AcceptanceIssue(code=code, message=bounded, **ids)


def _load_payload(payload: Mapping[str, Any] | str | bytes) -> tuple[dict[str, Any], bytes]:
    if isinstance(payload, Mapping):
        raw = dict(payload)
        return raw, canonical_json_bytes(raw)
    encoded = payload.encode("utf-8") if isinstance(payload, str) else payload
    loaded = json.loads(encoded)
    if not isinstance(loaded, dict):
        raise TypeError("artifact payload must be a JSON object")
    return loaded, canonical_json_bytes(loaded)


def _read_registry(workspace: Path) -> ArtifactRegistry:
    path = workspace / _REGISTRY_PATH
    if not path.is_file():
        return ArtifactRegistry()
    value = json.loads(path.read_text(encoding="utf-8"))
    return ArtifactRegistry.model_validate(value)


def _write_temp(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f"{path.name}.tmp-{uuid.uuid4().hex[:8]}")
    with open(temp, "wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    return temp


def _atomic_write(path: Path, content: bytes) -> None:
    temp = _write_temp(path, content)
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def _restore_registry(path: Path, previous: bytes | None) -> None:
    if previous is None:
        path.unlink(missing_ok=True)
    else:
        _atomic_write(path, previous)


def _prune_empty_directories(path: Path, *, stop: Path) -> None:
    current = path
    while current != stop:
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def _rejection(
    workspace: Path,
    *,
    payload_hash: str,
    artifact_id: str | None,
    artifact_type: str | None,
    issues: list[AcceptanceIssue],
    actor: str,
) -> AcceptanceResult:
    bounded = issues[:_MAX_ISSUES]
    record = {
        "contract_version": "1.0.0",
        "payload_hash": payload_hash,
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "rejected_at": datetime.now(UTC).isoformat(),
        "issues": [item.model_dump(mode="json") for item in bounded],
    }
    relative = PurePosixPath("audit/rejections") / f"{payload_hash.removeprefix('sha256:')}.json"
    path = workspace / relative
    rejection_path: str | None = None
    try:
        _atomic_write(path, json.dumps(record, indent=2, sort_keys=True).encode("utf-8") + b"\n")
        rejection_path = relative.as_posix()
    except OSError:
        pass
    event_id: str | None = None
    try:
        event = log_event(
            workspace,
            "ARTIFACT_REJECTED",
            f"Rejected Contract v1 artifact payload with {len(bounded)} issue(s)",
            agent=actor,
            inputs=[],
            outputs=[rejection_path] if rejection_path else [],
            parameters={
                "artifact_id": artifact_id,
                "artifact_type": artifact_type,
                "payload_hash": payload_hash,
            },
            metrics={"issue_count": len(bounded)},
            status="FAILED",
        )
        event_id = event["event_id"]
    except OSError:
        pass
    return AcceptanceResult(
        accepted=False,
        payload_hash=payload_hash,
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        rejection_path=rejection_path,
        event_id=event_id,
        issues=bounded,
    )


def accept_artifact(
    workspace: Path,
    payload: Mapping[str, Any] | str | bytes,
    *,
    expected: AcceptanceContext,
    actor: str = "scholar-harness-contract-gate",
) -> AcceptanceResult:
    """Validate and atomically publish one inbound Contract v1 artifact.

    Rejected payload bodies are never retained. Their canonical hash and bounded
    diagnostics are persisted under ``audit/rejections``.
    """

    workspace = Path(workspace).resolve()
    try:
        raw, canonical_payload = _load_payload(payload)
        payload_hash = canonical_fingerprint(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
        encoded = payload if isinstance(payload, bytes) else str(payload).encode("utf-8")
        payload_hash = "sha256:" + sha256(encoded).hexdigest()
        return _rejection(
            workspace,
            payload_hash=payload_hash,
            artifact_id=None,
            artifact_type=None,
            issues=[_issue("INVALID_JSON", str(exc))],
            actor=actor,
        )

    artifact_id = raw.get("artifact_id") if isinstance(raw.get("artifact_id"), str) else None
    artifact_type = raw.get("artifact_type") if isinstance(raw.get("artifact_type"), str) else None
    model = _ARTIFACT_MODELS.get(artifact_type or "")
    if model is None:
        return _rejection(
            workspace,
            payload_hash=payload_hash,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            issues=[_issue("UNSUPPORTED_ARTIFACT_TYPE", f"unsupported artifact_type {artifact_type!r}")],
            actor=actor,
        )

    try:
        artifact = model.model_validate(raw)
    except ValidationError as exc:
        issues = [
            _issue(
                "SCHEMA_VALIDATION_ERROR",
                error["msg"],
                artifact_id=artifact_id,
                related_id=".".join(str(part) for part in error["loc"]),
            )
            for error in exc.errors(include_url=False)[:_MAX_ISSUES]
        ]
        return _rejection(
            workspace,
            payload_hash=payload_hash,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            issues=issues,
            actor=actor,
        )

    issues: list[AcceptanceIssue] = []
    for field, expected_value, actual in (
        ("workspace_id", expected.workspace_id, artifact.workspace_id),
        ("protocol_fingerprint", expected.protocol_fingerprint, artifact.protocol_fingerprint),
        ("corpus_fingerprint", expected.corpus_fingerprint, artifact.corpus_fingerprint),
    ):
        if actual != expected_value:
            issues.append(
                _issue(
                    f"{field.upper()}_MISMATCH",
                    f"expected {field} {expected_value!r}, received {actual!r}",
                    artifact_id=artifact.artifact_id,
                )
            )

    registry_path = workspace / _REGISTRY_PATH
    try:
        registry = _read_registry(workspace)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        issues.append(_issue("REGISTRY_INVALID", str(exc), artifact_id=artifact.artifact_id))
        registry = ArtifactRegistry()

    entries = registry.artifacts
    existing = entries.get(artifact.artifact_id)
    idempotent = False
    if existing:
        if existing.sha256 == payload_hash:
            idempotent = True
        else:
            issues.append(
                _issue(
                    "IDEMPOTENCY_CONFLICT",
                    "artifact_id is already registered with a different payload hash",
                    artifact_id=artifact.artifact_id,
                )
            )

    registered_parents: dict[str, tuple[RegistryEntry, dict[str, Any]]] = {}
    for parent in artifact.inputs:
        registered = entries.get(parent.artifact_id)
        if registered is None:
            issues.append(
                _issue(
                    "MISSING_PARENT_ARTIFACT",
                    "direct parent is absent from the workspace artifact registry",
                    artifact_id=artifact.artifact_id,
                    related_id=parent.artifact_id,
                )
            )
            continue
        if registered.sha256 != parent.sha256:
            issues.append(
                _issue(
                    "PARENT_HASH_MISMATCH",
                    "declared parent hash differs from the accepted workspace artifact",
                    artifact_id=artifact.artifact_id,
                    related_id=parent.artifact_id,
                )
            )
            continue
        parent_path = workspace / PurePosixPath(registered.path)
        try:
            parent_raw, _ = _load_payload(parent_path.read_bytes())
        except (OSError, json.JSONDecodeError, TypeError, UnicodeDecodeError) as exc:
            issues.append(
                _issue(
                    "REGISTERED_PARENT_INVALID",
                    f"registered parent payload cannot be loaded: {exc}",
                    artifact_id=artifact.artifact_id,
                    related_id=parent.artifact_id,
                )
            )
            continue
        if canonical_fingerprint(parent_raw) != registered.sha256:
            issues.append(
                _issue(
                    "REGISTERED_PARENT_HASH_MISMATCH",
                    "registered parent payload differs from its registry hash",
                    artifact_id=artifact.artifact_id,
                    related_id=parent.artifact_id,
                )
            )
            continue
        parent_model = _ARTIFACT_MODELS.get(registered.artifact_type)
        try:
            if parent_model is None:
                raise ValueError(
                    f"unsupported registered artifact_type {registered.artifact_type!r}"
                )
            parent_model.model_validate(parent_raw)
        except (ValidationError, ValueError) as exc:
            issues.append(
                _issue(
                    "REGISTERED_PARENT_INVALID",
                    f"registered parent type does not match its payload: {exc}",
                    artifact_id=artifact.artifact_id,
                    related_id=parent.artifact_id,
                )
            )
            continue
        registered_parents[parent.artifact_id] = (registered, parent_raw)

    required_parent_type = _REQUIRED_PARENT_TYPE.get(artifact.artifact_type)
    matching_parents = [
        (parent_id, entry, raw)
        for parent_id, (entry, raw) in registered_parents.items()
        if entry.artifact_type == required_parent_type
    ]
    if required_parent_type and not matching_parents:
        issues.append(
            _issue(
                "REQUIRED_PARENT_TYPE_MISSING",
                f"{artifact.artifact_type} requires parent type {required_parent_type}",
                artifact_id=artifact.artifact_id,
            )
        )

    if isinstance(artifact, ScreeningDecisionsArtifact) and len(matching_parents) == 1:
        try:
            parent_batch = ScreeningBatchArtifact.model_validate(matching_parents[0][2])
        except ValidationError as exc:
            issues.append(
                _issue(
                    "REGISTERED_PARENT_INVALID",
                    f"registered screening batch is invalid: {exc}",
                    artifact_id=artifact.artifact_id,
                    related_id=matching_parents[0][0],
                )
            )
        else:
            if artifact.data.batch_id != parent_batch.data.batch_id:
                issues.append(
                    _issue(
                        "SCREENING_BATCH_ID_MISMATCH",
                        "screening decisions batch_id does not match its parent batch",
                        artifact_id=artifact.artifact_id,
                        related_id=parent_batch.artifact_id,
                    )
                )
            if artifact.data.binding != parent_batch.data.binding:
                issues.append(
                    _issue(
                        "SCREENING_BINDING_MISMATCH",
                        "screening decisions binding does not match its parent batch",
                        artifact_id=artifact.artifact_id,
                        related_id=parent_batch.artifact_id,
                    )
                )
            candidate_ids = {candidate.study_id for candidate in parent_batch.data.candidates}
            for decision in artifact.data.decisions:
                if decision.study_id not in candidate_ids:
                    issues.append(
                        _issue(
                            "DECISION_OUTSIDE_BATCH",
                            f"decision study {decision.study_id} is absent from parent batch",
                            artifact_id=artifact.artifact_id,
                            related_id=decision.study_id,
                        )
                    )

    if idempotent and existing is not None:
        registered_path = workspace / PurePosixPath(existing.path)
        try:
            registered_payload = registered_path.read_bytes()
        except OSError as exc:
            issues.append(
                _issue(
                    "REGISTERED_ARTIFACT_MISSING",
                    f"registered artifact payload cannot be read: {exc}",
                    artifact_id=artifact.artifact_id,
                )
            )
        else:
            try:
                registered_raw, _ = _load_payload(registered_payload)
            except (json.JSONDecodeError, TypeError, UnicodeDecodeError) as exc:
                issues.append(
                    _issue(
                        "REGISTERED_ARTIFACT_INVALID",
                        f"registered artifact payload is invalid: {exc}",
                        artifact_id=artifact.artifact_id,
                    )
                )
            else:
                if canonical_fingerprint(registered_raw) != existing.sha256:
                    issues.append(
                        _issue(
                            "REGISTERED_ARTIFACT_HASH_MISMATCH",
                            "registered artifact payload differs from its registry hash",
                            artifact_id=artifact.artifact_id,
                        )
                    )

    if issues:
        return _rejection(
            workspace,
            payload_hash=payload_hash,
            artifact_id=artifact.artifact_id,
            artifact_type=artifact.artifact_type,
            issues=issues,
            actor=actor,
        )

    if idempotent and existing is not None:
        return AcceptanceResult(
            accepted=True,
            payload_hash=payload_hash,
            artifact_id=artifact.artifact_id,
            artifact_type=artifact.artifact_type,
            published_path=existing.path,
            idempotent=True,
        )

    relative = PurePosixPath("artifacts") / artifact.artifact_type / f"{artifact.artifact_id}.json"
    destination = workspace / relative
    if destination.exists():
        return _rejection(
            workspace,
            payload_hash=payload_hash,
            artifact_id=artifact.artifact_id,
            artifact_type=artifact.artifact_type,
            issues=[
                _issue(
                    "ORPHAN_ARTIFACT_PATH",
                    "artifact destination exists without a matching registry entry",
                    artifact_id=artifact.artifact_id,
                )
            ],
            actor=actor,
        )
    previous_registry = registry_path.read_bytes() if registry_path.is_file() else None
    entries[artifact.artifact_id] = RegistryEntry(
        artifact_type=artifact.artifact_type,
        path=relative.as_posix(),
        sha256=payload_hash,
        accepted_at=datetime.now(UTC),
        run_id=artifact.run_id,
        producer=artifact.producer,
    )
    registry_bytes = (
        json.dumps(registry.model_dump(mode="json"), indent=2, sort_keys=True).encode("utf-8")
        + b"\n"
    )
    artifact_temp: Path | None = None
    registry_temp: Path | None = None
    try:
        artifact_temp = _write_temp(destination, canonical_payload + b"\n")
        registry_temp = _write_temp(registry_path, registry_bytes)
        os.replace(artifact_temp, destination)
        os.replace(registry_temp, registry_path)
        event = log_event(
            workspace,
            "ARTIFACT_ACCEPTED",
            f"Accepted Contract v1 {artifact.artifact_type} artifact",
            agent=actor,
            inputs=[parent.artifact_id for parent in artifact.inputs],
            outputs=[relative.as_posix(), _REGISTRY_PATH.as_posix()],
            parameters={
                "artifact_id": artifact.artifact_id,
                "artifact_type": artifact.artifact_type,
                "payload_hash": payload_hash,
            },
            metrics={"parent_count": len(artifact.inputs)},
            status="SUCCESS",
        )
    except OSError as exc:
        destination.unlink(missing_ok=True)
        if artifact_temp is not None:
            artifact_temp.unlink(missing_ok=True)
        if registry_temp is not None:
            registry_temp.unlink(missing_ok=True)
        _prune_empty_directories(destination.parent, stop=workspace)
        _restore_registry(registry_path, previous_registry)
        return _rejection(
            workspace,
            payload_hash=payload_hash,
            artifact_id=artifact.artifact_id,
            artifact_type=artifact.artifact_type,
            issues=[_issue("ATOMIC_COMMIT_FAILED", str(exc), artifact_id=artifact.artifact_id)],
            actor=actor,
        )
    finally:
        if artifact_temp is not None:
            artifact_temp.unlink(missing_ok=True)
        if registry_temp is not None:
            registry_temp.unlink(missing_ok=True)

    return AcceptanceResult(
        accepted=True,
        payload_hash=payload_hash,
        artifact_id=artifact.artifact_id,
        artifact_type=artifact.artifact_type,
        published_path=relative.as_posix(),
        event_id=event["event_id"],
    )
