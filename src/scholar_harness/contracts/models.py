"""Typed reference models for Nexus Scholar cross-kit contract v1."""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .canonical import corpus_snapshot_fingerprint
from .identifiers import IdentifierKind, validate_identifier

CONTRACT_VERSION = "1.0.0"
_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_CITATION_TOKEN_RE = re.compile(
    r"^\[rag:v2:([^:\]]+):([^:\]]+):([^:\]]+)\]$"
)


def _supported_v1(value: str, *, field_name: str) -> str:
    match = _VERSION_RE.fullmatch(value)
    if match is None or int(match.group(1)) != 1:
        raise ValueError(f"unsupported {field_name} {value!r}; expected major version 1")
    return value


def _sha256(value: str, *, field_name: str) -> str:
    if _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be sha256:<64 lowercase hex chars>")
    return value


def _utc(value: datetime, *, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must include an RFC3339 UTC offset")
    if value.utcoffset().total_seconds() != 0:
        raise ValueError(f"{field_name} must be UTC")
    return value


class ContractModel(BaseModel):
    """Forward-compatible base: preserve unknown minor-version fields."""

    model_config = ConfigDict(extra="allow")


class OperationStatus(StrEnum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    WAITING_FOR_DECISION = "WAITING_FOR_DECISION"
    CANCELLED = "CANCELLED"

    @property
    def is_hard_failure(self) -> bool:
        return self in {self.ERROR, self.FAILED}


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    PATH_OUTSIDE_WORKSPACE = "PATH_OUTSIDE_WORKSPACE"
    SCHEMA_VERSION_UNSUPPORTED = "SCHEMA_VERSION_UNSUPPORTED"
    PROTOCOL_FINGERPRINT_MISMATCH = "PROTOCOL_FINGERPRINT_MISMATCH"
    CORPUS_FINGERPRINT_MISMATCH = "CORPUS_FINGERPRINT_MISMATCH"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    CONFLICT = "CONFLICT"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    ATOMIC_COMMIT_FAILED = "ATOMIC_COMMIT_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class MethodProvenance(StrEnum):
    HUMAN = "HUMAN"
    DETERMINISTIC_RULE = "DETERMINISTIC_RULE"
    HEURISTIC = "HEURISTIC"
    LLM = "LLM"
    EXTERNAL_PROVIDER = "EXTERNAL_PROVIDER"
    COMPOSED = "COMPOSED"


class ScreeningDecisionValue(StrEnum):
    INCLUDE = "INCLUDE"
    EXCLUDE = "EXCLUDE"
    MAYBE = "MAYBE"
    CONFLICT = "CONFLICT"


class RetrievalState(StrEnum):
    SOURCE_AVAILABLE = "SOURCE_AVAILABLE"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"


class LexicalSupport(StrEnum):
    SUPPORTED_VERBATIM = "SUPPORTED_VERBATIM"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    NOT_FOUND = "NOT_FOUND"
    NOT_CHECKED = "NOT_CHECKED"


class EntailmentState(StrEnum):
    ENTAILED = "ENTAILED"
    CONTRADICTED = "CONTRADICTED"
    UNCERTAIN = "UNCERTAIN"
    NOT_ASSESSED = "NOT_ASSESSED"


class TrustState(StrEnum):
    CLEAR = "CLEAR"
    FLAGGED = "FLAGGED"
    UNRESOLVED = "UNRESOLVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_CHECKED = "NOT_CHECKED"


class DocumentContentStatus(StrEnum):
    VALID = "VALID"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    NEEDS_OCR = "NEEDS_OCR"


class Producer(ContractModel):
    package: str = Field(min_length=1)
    version: str = Field(min_length=1)
    commit: str = Field(min_length=1)


class InputArtifact(ContractModel):
    artifact_id: str
    sha256: str

    @field_validator("artifact_id")
    @classmethod
    def artifact_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.ARTIFACT, value)

    @field_validator("sha256")
    @classmethod
    def content_hash(cls, value: str) -> str:
        return _sha256(value, field_name="sha256")


class ArtifactReference(InputArtifact):
    path: str

    @field_validator("path")
    @classmethod
    def portable_workspace_path(cls, value: str) -> str:
        if not value or "\\" in value:
            raise ValueError("artifact path must be a workspace-relative POSIX path")
        path = PurePosixPath(value)
        if (
            not path.parts
            or path.is_absolute()
            or re.match(r"^[A-Za-z]:/", value)
            or ".." in path.parts
            or path.parts[0] in {"", "."}
        ):
            raise ValueError("artifact path must remain inside the workspace")
        return value


class ContractError(ContractModel):
    code: ErrorCode | str
    message: str = Field(min_length=1)
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


DataT = TypeVar("DataT")


class ArtifactEnvelope(ContractModel, Generic[DataT]):
    schema_version: str
    artifact_type: str = Field(min_length=1)
    artifact_id: str
    created_at: datetime
    producer: Producer
    workspace_id: str
    run_id: str
    protocol_fingerprint: str
    corpus_fingerprint: str
    inputs: list[InputArtifact] = Field(default_factory=list)
    data: DataT

    @field_validator("schema_version")
    @classmethod
    def supported_schema(cls, value: str) -> str:
        return _supported_v1(value, field_name="schema_version")

    @field_validator("artifact_id")
    @classmethod
    def artifact_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.ARTIFACT, value)

    @field_validator("workspace_id")
    @classmethod
    def workspace_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.WORKSPACE, value)

    @field_validator("run_id")
    @classmethod
    def run_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.RUN, value)

    @field_validator("protocol_fingerprint", "corpus_fingerprint")
    @classmethod
    def fingerprints(cls, value: str) -> str:
        return _sha256(value, field_name="fingerprint")

    @field_validator("created_at")
    @classmethod
    def utc_created_at(cls, value: datetime) -> datetime:
        return _utc(value, field_name="created_at")


class OperationOutcome(ContractModel, Generic[DataT]):
    contract_version: str
    operation: str = Field(min_length=1)
    run_id: str
    status: OperationStatus
    data: DataT
    artifacts: list[ArtifactReference] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[ContractError] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)

    @field_validator("contract_version")
    @classmethod
    def supported_contract(cls, value: str) -> str:
        return _supported_v1(value, field_name="contract_version")

    @field_validator("run_id")
    @classmethod
    def run_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.RUN, value)

    @model_validator(mode="after")
    def coherent_status(self) -> OperationOutcome[DataT]:
        if self.status.is_hard_failure and not self.errors:
            raise ValueError("ERROR/FAILED outcomes must include at least one error")
        if self.status is OperationStatus.SUCCESS and self.errors:
            raise ValueError("SUCCESS outcomes cannot contain errors")
        if self.status is OperationStatus.PARTIAL and not (self.warnings or self.errors):
            raise ValueError("PARTIAL outcomes must explain the degradation")
        return self


class VerificationAxes(ContractModel):
    retrieval: RetrievalState
    lexical_support: LexicalSupport = LexicalSupport.NOT_CHECKED
    entailment: EntailmentState = EntailmentState.NOT_ASSESSED
    trust: TrustState = TrustState.NOT_CHECKED
    semantic_similarity_score: float | None = Field(default=None, ge=-1.0, le=1.0)
    algorithm_version: str | None = None
    threshold: float | None = None


class EvidenceItem(ContractModel):
    evidence_id: str
    study_id: str
    document_id: str
    locator: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    extraction_method: MethodProvenance
    source_hash: str

    @field_validator("evidence_id")
    @classmethod
    def evidence_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.EVIDENCE, value)

    @field_validator("study_id")
    @classmethod
    def study_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.STUDY, value)

    @field_validator("document_id")
    @classmethod
    def document_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.DOCUMENT, value)

    @field_validator("source_hash")
    @classmethod
    def source_content_hash(cls, value: str) -> str:
        return _sha256(value, field_name="source_hash")


class ClaimItem(ContractModel):
    claim_id: str
    claim_text: str = Field(min_length=1)
    claim_kind: str = Field(min_length=1)
    study_ids: list[str] = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    citation_tokens: list[str] = Field(default_factory=list)
    generation_method: MethodProvenance
    rq_ids: list[str] | None = None
    verification: VerificationAxes | None = None

    @field_validator("claim_id")
    @classmethod
    def claim_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.CLAIM, value)

    @field_validator("study_ids")
    @classmethod
    def study_identifiers(cls, values: list[str]) -> list[str]:
        return [validate_identifier(IdentifierKind.STUDY, value) for value in values]

    @field_validator("evidence_ids")
    @classmethod
    def evidence_identifiers(cls, values: list[str]) -> list[str]:
        return [validate_identifier(IdentifierKind.EVIDENCE, value) for value in values]

    @field_validator("citation_tokens")
    @classmethod
    def citation_tokens_are_typed(cls, values: list[str]) -> list[str]:
        for value in values:
            match = _CITATION_TOKEN_RE.fullmatch(value)
            if match is None:
                raise ValueError("citation token must use [rag:v2:workspace:study:chunk]")
            workspace_id, study_id, chunk_id = match.groups()
            validate_identifier(IdentifierKind.WORKSPACE, workspace_id)
            validate_identifier(IdentifierKind.STUDY, study_id)
            validate_identifier(IdentifierKind.CHUNK, chunk_id)
        return values


class ClaimEvidenceData(ContractModel):
    claims: list[ClaimItem] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def references_resolve(self) -> ClaimEvidenceData:
        claim_ids = [item.claim_id for item in self.claims]
        evidence_item_ids = [item.evidence_id for item in self.evidence]
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("claim IDs must be unique within a ledger")
        if len(evidence_item_ids) != len(set(evidence_item_ids)):
            raise ValueError("evidence IDs must be unique within a ledger")

        evidence_by_id = {item.evidence_id: item for item in self.evidence}
        missing = sorted(
            {
                evidence_id
                for claim in self.claims
                for evidence_id in claim.evidence_ids
                if evidence_id not in evidence_by_id
            }
        )
        if missing:
            raise ValueError(f"claims reference missing evidence IDs: {missing}")
        cross_study = sorted(
            {
                f"{claim.claim_id}->{evidence_id}"
                for claim in self.claims
                for evidence_id in claim.evidence_ids
                if evidence_by_id[evidence_id].study_id not in claim.study_ids
            }
        )
        if cross_study:
            raise ValueError(
                "claim evidence belongs to an unlisted study: " + ", ".join(cross_study)
            )
        return self


class ClaimEvidenceLedger(ArtifactEnvelope[ClaimEvidenceData]):
    artifact_type: Literal["claims_ledger"]


class CorpusStudy(ContractModel):
    study_id: str
    source_record_ids: list[str] = Field(min_length=1)
    alias_ids: list[str] = Field(default_factory=list)
    external_ids: dict[str, list[str]] = Field(default_factory=dict)
    title: str = Field(min_length=1)
    publication_year: int | None = Field(default=None, ge=1000, le=9999)

    @field_validator("study_id")
    @classmethod
    def study_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.STUDY, value)

    @field_validator("source_record_ids")
    @classmethod
    def source_record_identifiers(cls, values: list[str]) -> list[str]:
        return [
            validate_identifier(IdentifierKind.SOURCE_RECORD, value)
            for value in values
        ]

    @model_validator(mode="after")
    def unique_identity_values(self) -> CorpusStudy:
        if len(self.source_record_ids) != len(set(self.source_record_ids)):
            raise ValueError("source record IDs must be unique within a study")
        for provider, values in self.external_ids.items():
            if not provider or not values or any(not value for value in values):
                raise ValueError("external ID providers and values must be non-empty")
            if len(values) != len(set(values)):
                raise ValueError(f"external IDs for {provider!r} must be unique")
        return self


class CorpusSnapshotData(ContractModel):
    corpus_id: str
    identity_algorithm_version: str = Field(min_length=1)
    studies: list[CorpusStudy] = Field(min_length=1)
    record_to_study: dict[str, str]

    @field_validator("corpus_id")
    @classmethod
    def corpus_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.CORPUS, value)

    @model_validator(mode="after")
    def identity_map_is_total_and_unambiguous(self) -> CorpusSnapshotData:
        study_ids = [study.study_id for study in self.studies]
        if len(study_ids) != len(set(study_ids)):
            raise ValueError("corpus study IDs must be unique")

        declared_records = {
            record_id for study in self.studies for record_id in study.source_record_ids
        }
        mapped_records = set(self.record_to_study)
        if declared_records != mapped_records:
            missing = sorted(declared_records - mapped_records)
            unknown = sorted(mapped_records - declared_records)
            raise ValueError(
                f"record_to_study must be total; missing={missing}, unknown={unknown}"
            )
        unknown_studies = sorted(set(self.record_to_study.values()) - set(study_ids))
        if unknown_studies:
            raise ValueError(
                f"record_to_study references unknown study IDs: {unknown_studies}"
            )
        for study in self.studies:
            wrong = [
                record_id
                for record_id in study.source_record_ids
                if self.record_to_study[record_id] != study.study_id
            ]
            if wrong:
                raise ValueError(
                    f"source records mapped to the wrong study {study.study_id}: {wrong}"
                )
        return self


class CorpusSnapshotArtifact(ArtifactEnvelope[CorpusSnapshotData]):
    artifact_type: Literal["corpus_snapshot"]

    @model_validator(mode="after")
    def fingerprint_matches_identity_graph(self) -> CorpusSnapshotArtifact:
        expected = corpus_snapshot_fingerprint(self.data)
        if self.corpus_fingerprint != expected:
            raise ValueError(
                "corpus_fingerprint does not match the canonical corpus identity graph"
            )
        return self


class DocumentRecord(ContractModel):
    document_id: str
    study_id: str
    source_hash: str
    content_status: DocumentContentStatus
    extracted_path: str | None = None
    extraction_method: MethodProvenance

    @field_validator("document_id")
    @classmethod
    def document_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.DOCUMENT, value)

    @field_validator("study_id")
    @classmethod
    def study_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.STUDY, value)

    @field_validator("source_hash")
    @classmethod
    def source_content_hash(cls, value: str) -> str:
        return _sha256(value, field_name="source_hash")

    @field_validator("extracted_path")
    @classmethod
    def portable_extracted_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        ArtifactReference.portable_workspace_path(value)
        return value

    @model_validator(mode="after")
    def usable_content_has_a_path(self) -> DocumentRecord:
        if self.content_status in {
            DocumentContentStatus.VALID,
            DocumentContentStatus.PARTIAL,
        } and self.extracted_path is None:
            raise ValueError("VALID/PARTIAL documents require extracted_path")
        return self


class DocumentManifestData(ContractModel):
    documents: list[DocumentRecord] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_documents(self) -> DocumentManifestData:
        document_ids = [document.document_id for document in self.documents]
        if len(document_ids) != len(set(document_ids)):
            raise ValueError("document IDs must be unique within a manifest")
        return self


class DocumentManifestArtifact(ArtifactEnvelope[DocumentManifestData]):
    artifact_type: Literal["document_manifest"]


class ScreeningBinding(ContractModel):
    screening_run_id: str
    protocol_fingerprint: str
    corpus_fingerprint: str
    criteria_renderer_version: str = Field(min_length=1)
    dedup_configuration_hash: str
    preparation_run_id: str

    @field_validator("screening_run_id", "preparation_run_id")
    @classmethod
    def run_identifiers(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.RUN, value)

    @field_validator(
        "protocol_fingerprint", "corpus_fingerprint", "dedup_configuration_hash"
    )
    @classmethod
    def binding_hashes(cls, value: str) -> str:
        return _sha256(value, field_name="screening binding hash")


class ScreeningCandidate(ContractModel):
    study_id: str
    title: str = Field(min_length=1)
    abstract: str | None = None

    @field_validator("study_id")
    @classmethod
    def study_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.STUDY, value)


class ScreeningBatchData(ContractModel):
    binding: ScreeningBinding
    batch_id: str = Field(min_length=1)
    batch_index: int = Field(ge=0)
    candidates: list[ScreeningCandidate] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_candidates(self) -> ScreeningBatchData:
        study_ids = [candidate.study_id for candidate in self.candidates]
        if len(study_ids) != len(set(study_ids)):
            raise ValueError("screening batch study IDs must be unique")
        return self


class ScreeningBatchArtifact(ArtifactEnvelope[ScreeningBatchData]):
    artifact_type: Literal["screening_batch"]

    @model_validator(mode="after")
    def envelope_matches_binding(self) -> ScreeningBatchArtifact:
        _validate_screening_binding(self)
        return self


class ScreeningDecision(ContractModel):
    decision_id: str
    study_id: str
    screener_id: str = Field(min_length=1)
    method: MethodProvenance
    decision: ScreeningDecisionValue
    reason: str = Field(min_length=1)
    decided_at: datetime
    model_id: str | None = None
    prompt_version: str | None = None
    parent_decision_ids: list[str] = Field(default_factory=list)

    @field_validator("decision_id")
    @classmethod
    def decision_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.SCREENING_DECISION, value)

    @field_validator("study_id")
    @classmethod
    def study_identifier(cls, value: str) -> str:
        return validate_identifier(IdentifierKind.STUDY, value)

    @field_validator("parent_decision_ids")
    @classmethod
    def parent_identifiers(cls, values: list[str]) -> list[str]:
        return [
            validate_identifier(IdentifierKind.SCREENING_DECISION, value)
            for value in values
        ]

    @field_validator("decided_at")
    @classmethod
    def utc_decided_at(cls, value: datetime) -> datetime:
        return _utc(value, field_name="decided_at")


class ScreeningDecisionsData(ContractModel):
    binding: ScreeningBinding
    batch_id: str = Field(min_length=1)
    decisions: list[ScreeningDecision] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_decisions(self) -> ScreeningDecisionsData:
        decision_ids = [decision.decision_id for decision in self.decisions]
        if len(decision_ids) != len(set(decision_ids)):
            raise ValueError("screening decision IDs must be unique")
        return self


class ScreeningDecisionsArtifact(ArtifactEnvelope[ScreeningDecisionsData]):
    artifact_type: Literal["screening_decisions"]

    @model_validator(mode="after")
    def envelope_matches_binding(self) -> ScreeningDecisionsArtifact:
        _validate_screening_binding(self)
        return self


def _validate_screening_binding(
    artifact: ScreeningBatchArtifact | ScreeningDecisionsArtifact,
) -> None:
    binding = artifact.data.binding
    mismatches: list[str] = []
    if artifact.run_id != binding.screening_run_id:
        mismatches.append("run_id")
    if artifact.protocol_fingerprint != binding.protocol_fingerprint:
        mismatches.append("protocol_fingerprint")
    if artifact.corpus_fingerprint != binding.corpus_fingerprint:
        mismatches.append("corpus_fingerprint")
    if mismatches:
        raise ValueError(
            "screening envelope/binding mismatch: " + ", ".join(mismatches)
        )


class RunManifestData(ContractModel):
    operation: str = Field(min_length=1)
    status: OperationStatus
    idempotency_key: str
    started_at: datetime
    ended_at: datetime | None = None
    staged_artifacts: list[ArtifactReference] = Field(default_factory=list)
    committed_artifacts: list[ArtifactReference] = Field(default_factory=list)
    audit_event_id: str | None = None

    @field_validator("idempotency_key")
    @classmethod
    def idempotency_hash(cls, value: str) -> str:
        return _sha256(value, field_name="idempotency_key")

    @field_validator("started_at", "ended_at")
    @classmethod
    def utc_times(cls, value: datetime | None, info: Any) -> datetime | None:
        if value is None:
            return None
        return _utc(value, field_name=info.field_name)

    @field_validator("audit_event_id")
    @classmethod
    def audit_identifier(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_identifier(IdentifierKind.AUDIT_EVENT, value)

    @model_validator(mode="after")
    def chronological(self) -> RunManifestData:
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError("ended_at cannot precede started_at")
        return self


class RunManifest(ArtifactEnvelope[RunManifestData]):
    artifact_type: Literal["run_manifest"]
