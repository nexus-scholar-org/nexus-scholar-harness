"""Closed-chain conformance validation for cross-kit artifact handoffs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import Field, ValidationError

from .canonical import canonical_fingerprint
from .models import (
    ArtifactEnvelope,
    ClaimEvidenceLedger,
    ContractModel,
    CorpusSnapshotArtifact,
    DocumentContentStatus,
    DocumentManifestArtifact,
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


class ArtifactChainIssue(ContractModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    artifact_id: str | None = None
    related_id: str | None = None


class ArtifactChainReport(ContractModel):
    valid: bool
    artifact_count: int = Field(ge=0)
    study_count: int = Field(ge=0)
    issues: list[ArtifactChainIssue] = Field(default_factory=list)


def _issue(
    issues: list[ArtifactChainIssue],
    code: str,
    message: str,
    *,
    artifact_id: str | None = None,
    related_id: str | None = None,
) -> None:
    issues.append(
        ArtifactChainIssue(
            code=code,
            message=message,
            artifact_id=artifact_id,
            related_id=related_id,
        )
    )


def _has_cycle(parents: dict[str, set[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(parent) for parent in parents.get(node, ())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in parents)


def validate_artifact_chain(
    artifacts: Sequence[Mapping[str, Any]], *, closed: bool = True
) -> ArtifactChainReport:
    """Validate a contract-v1 artifact graph and its scientific identities.

    ``closed=True`` requires every direct parent to be present, enabling exact
    hash and lineage validation for golden fixtures and handoff packages.
    """

    issues: list[ArtifactChainIssue] = []
    parsed: dict[str, ArtifactEnvelope[Any]] = {}
    raw_by_id: dict[str, Mapping[str, Any]] = {}

    for index, raw in enumerate(artifacts):
        artifact_type = raw.get("artifact_type")
        artifact_id = raw.get("artifact_id")
        if not isinstance(artifact_type, str) or artifact_type not in _ARTIFACT_MODELS:
            _issue(
                issues,
                "UNSUPPORTED_ARTIFACT_TYPE",
                f"artifact {index} has unsupported artifact_type {artifact_type!r}",
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
            )
            continue
        model = _ARTIFACT_MODELS[artifact_type]
        try:
            artifact = model.model_validate(raw)
        except ValidationError as exc:
            _issue(
                issues,
                "SCHEMA_VALIDATION_ERROR",
                str(exc),
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
            )
            continue
        if artifact.artifact_id in parsed:
            _issue(
                issues,
                "DUPLICATE_ARTIFACT_ID",
                f"artifact ID {artifact.artifact_id} occurs more than once",
                artifact_id=artifact.artifact_id,
            )
            continue
        parsed[artifact.artifact_id] = artifact
        raw_by_id[artifact.artifact_id] = raw

    if not parsed:
        return ArtifactChainReport(
            valid=False,
            artifact_count=0,
            study_count=0,
            issues=issues,
        )

    first = next(iter(parsed.values()))
    parents: dict[str, set[str]] = {}
    for artifact_id, artifact in parsed.items():
        if artifact.workspace_id != first.workspace_id:
            _issue(
                issues,
                "WORKSPACE_MISMATCH",
                "all artifacts in a closed chain must share workspace_id",
                artifact_id=artifact_id,
            )
        if artifact.protocol_fingerprint != first.protocol_fingerprint:
            _issue(
                issues,
                "PROTOCOL_FINGERPRINT_MISMATCH",
                "all artifacts in a closed chain must share protocol_fingerprint",
                artifact_id=artifact_id,
            )
        if artifact.corpus_fingerprint != first.corpus_fingerprint:
            _issue(
                issues,
                "CORPUS_FINGERPRINT_MISMATCH",
                "all artifacts in a closed chain must share corpus_fingerprint",
                artifact_id=artifact_id,
            )

        parents[artifact_id] = {parent.artifact_id for parent in artifact.inputs}
        for parent in artifact.inputs:
            parent_raw = raw_by_id.get(parent.artifact_id)
            if parent_raw is None:
                if closed:
                    _issue(
                        issues,
                        "MISSING_PARENT_ARTIFACT",
                        f"direct parent {parent.artifact_id} is absent",
                        artifact_id=artifact_id,
                        related_id=parent.artifact_id,
                    )
                continue
            actual_hash = canonical_fingerprint(parent_raw)
            if actual_hash != parent.sha256:
                _issue(
                    issues,
                    "PARENT_HASH_MISMATCH",
                    f"declared hash for {parent.artifact_id} does not match parent payload",
                    artifact_id=artifact_id,
                    related_id=parent.artifact_id,
                )

        required_parent_type = _REQUIRED_PARENT_TYPE.get(artifact.artifact_type)
        if required_parent_type:
            parent_types = {
                parsed[parent_id].artifact_type
                for parent_id in parents[artifact_id]
                if parent_id in parsed
            }
            if required_parent_type not in parent_types:
                _issue(
                    issues,
                    "REQUIRED_PARENT_TYPE_MISSING",
                    f"{artifact.artifact_type} requires parent type {required_parent_type}",
                    artifact_id=artifact_id,
                )

    if _has_cycle(parents):
        _issue(issues, "ARTIFACT_LINEAGE_CYCLE", "artifact input graph contains a cycle")

    corpus_artifacts = [
        artifact
        for artifact in parsed.values()
        if isinstance(artifact, CorpusSnapshotArtifact)
    ]
    if len(corpus_artifacts) != 1:
        _issue(
            issues,
            "CORPUS_SNAPSHOT_CARDINALITY",
            f"closed chain requires exactly one corpus snapshot; found {len(corpus_artifacts)}",
        )
        study_ids: set[str] = set()
    else:
        study_ids = {study.study_id for study in corpus_artifacts[0].data.studies}

    batches = {
        artifact.artifact_id: artifact
        for artifact in parsed.values()
        if isinstance(artifact, ScreeningBatchArtifact)
    }
    for artifact in batches.values():
        for candidate in artifact.data.candidates:
            if candidate.study_id not in study_ids:
                _issue(
                    issues,
                    "UNKNOWN_SCREENING_STUDY",
                    f"screening candidate {candidate.study_id} is absent from corpus",
                    artifact_id=artifact.artifact_id,
                    related_id=candidate.study_id,
                )

    for artifact in parsed.values():
        if not isinstance(artifact, ScreeningDecisionsArtifact):
            continue
        parent_batches = [
            batches[parent.artifact_id]
            for parent in artifact.inputs
            if parent.artifact_id in batches
        ]
        if len(parent_batches) != 1:
            continue
        batch = parent_batches[0]
        if artifact.data.batch_id != batch.data.batch_id:
            _issue(
                issues,
                "SCREENING_BATCH_ID_MISMATCH",
                "screening decisions batch_id does not match its parent batch",
                artifact_id=artifact.artifact_id,
                related_id=batch.artifact_id,
            )
        if artifact.data.binding != batch.data.binding:
            _issue(
                issues,
                "SCREENING_BINDING_MISMATCH",
                "screening decisions binding does not match its parent batch",
                artifact_id=artifact.artifact_id,
                related_id=batch.artifact_id,
            )
        candidate_ids = {candidate.study_id for candidate in batch.data.candidates}
        for decision in artifact.data.decisions:
            if decision.study_id not in candidate_ids:
                _issue(
                    issues,
                    "DECISION_OUTSIDE_BATCH",
                    f"decision study {decision.study_id} is absent from parent batch",
                    artifact_id=artifact.artifact_id,
                    related_id=decision.study_id,
                )

    documents: dict[str, Any] = {}
    for artifact in parsed.values():
        if not isinstance(artifact, DocumentManifestArtifact):
            continue
        for document in artifact.data.documents:
            if document.study_id not in study_ids:
                _issue(
                    issues,
                    "UNKNOWN_DOCUMENT_STUDY",
                    f"document {document.document_id} references an unknown study",
                    artifact_id=artifact.artifact_id,
                    related_id=document.study_id,
                )
            documents[document.document_id] = document

    for artifact in parsed.values():
        if not isinstance(artifact, ClaimEvidenceLedger):
            continue
        for claim in artifact.data.claims:
            for study_id in claim.study_ids:
                if study_id not in study_ids:
                    _issue(
                        issues,
                        "UNKNOWN_CLAIM_STUDY",
                        f"claim {claim.claim_id} references an unknown study",
                        artifact_id=artifact.artifact_id,
                        related_id=study_id,
                    )
        for evidence in artifact.data.evidence:
            document = documents.get(evidence.document_id)
            if document is None:
                _issue(
                    issues,
                    "UNKNOWN_EVIDENCE_DOCUMENT",
                    f"evidence {evidence.evidence_id} references an unknown document",
                    artifact_id=artifact.artifact_id,
                    related_id=evidence.document_id,
                )
                continue
            if document.study_id != evidence.study_id:
                _issue(
                    issues,
                    "EVIDENCE_DOCUMENT_STUDY_MISMATCH",
                    "evidence study_id differs from its document study_id",
                    artifact_id=artifact.artifact_id,
                    related_id=evidence.evidence_id,
                )
            if document.source_hash != evidence.source_hash:
                _issue(
                    issues,
                    "EVIDENCE_SOURCE_HASH_MISMATCH",
                    "evidence source_hash differs from its document source_hash",
                    artifact_id=artifact.artifact_id,
                    related_id=evidence.evidence_id,
                )
            if document.content_status not in {
                DocumentContentStatus.VALID,
                DocumentContentStatus.PARTIAL,
            }:
                _issue(
                    issues,
                    "UNUSABLE_EVIDENCE_DOCUMENT",
                    "evidence cannot be grounded in a failed or OCR-pending document",
                    artifact_id=artifact.artifact_id,
                    related_id=evidence.document_id,
                )

    return ArtifactChainReport(
        valid=not issues,
        artifact_count=len(parsed),
        study_count=len(study_ids),
        issues=issues,
    )
