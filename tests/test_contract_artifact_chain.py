"""Cross-kit identity and lineage tests using the two-study golden chain."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from scholar_harness.contracts import validate_artifact_chain

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "contracts"
    / "v1"
    / "two_study_artifact_chain.json"
)


def _artifacts() -> list[dict]:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return payload["artifacts"]


def _by_type(artifacts: list[dict], artifact_type: str) -> dict:
    return next(item for item in artifacts if item["artifact_type"] == artifact_type)


def _codes(report) -> set[str]:
    return {issue.code for issue in report.issues}


def test_two_same_title_studies_remain_distinct_across_closed_chain():
    artifacts = _artifacts()
    report = validate_artifact_chain(artifacts)
    assert report.valid, report.model_dump(mode="json")
    assert report.artifact_count == 5
    assert report.study_count == 2

    corpus = _by_type(artifacts, "corpus_snapshot")
    assert {study["study_id"] for study in corpus["data"]["studies"]} == {
        "STU-alpha",
        "STU-beta",
    }
    assert {study["title"] for study in corpus["data"]["studies"]} == {
        "Shared short title"
    }


def test_parent_payload_mutation_invalidates_declared_child_hash():
    artifacts = _artifacts()
    batch = _by_type(artifacts, "screening_batch")
    batch["data"]["candidates"][0]["title"] = "Mutated after decisions were made"
    report = validate_artifact_chain(artifacts)
    assert not report.valid
    assert "PARENT_HASH_MISMATCH" in _codes(report)


def test_corpus_fingerprint_is_derived_from_identity_graph():
    artifacts = _artifacts()
    corpus = _by_type(artifacts, "corpus_snapshot")
    corpus["data"]["studies"][0]["title"] = "Identity graph mutation"
    report = validate_artifact_chain(artifacts)
    assert not report.valid
    assert "SCHEMA_VALIDATION_ERROR" in _codes(report)


def test_missing_parent_is_explicit_in_closed_mode():
    artifacts = _artifacts()[1:]
    report = validate_artifact_chain(artifacts, closed=True)
    assert not report.valid
    assert "MISSING_PARENT_ARTIFACT" in _codes(report)
    assert "CORPUS_SNAPSHOT_CARDINALITY" in _codes(report)


def test_cross_workspace_or_stale_fingerprint_chain_is_rejected():
    artifacts = _artifacts()
    documents = _by_type(artifacts, "document_manifest")
    documents["workspace_id"] = "WSP-other"
    documents["protocol_fingerprint"] = "sha256:" + "9" * 64
    report = validate_artifact_chain(artifacts)
    assert not report.valid
    assert {"WORKSPACE_MISMATCH", "PROTOCOL_FINGERPRINT_MISMATCH"} <= _codes(report)


def test_decision_cannot_target_a_study_outside_its_parent_batch():
    artifacts = _artifacts()
    batch = _by_type(artifacts, "screening_batch")
    batch["data"]["candidates"] = [batch["data"]["candidates"][0]]
    report = validate_artifact_chain(artifacts)
    assert not report.valid
    assert "DECISION_OUTSIDE_BATCH" in _codes(report)


def test_evidence_cannot_cross_document_study_boundaries():
    artifacts = _artifacts()
    claims = _by_type(artifacts, "claims_ledger")
    beta_evidence = claims["data"]["evidence"][1]
    beta_evidence["document_id"] = "DOC-alpha-pdf"
    report = validate_artifact_chain(artifacts)
    assert not report.valid
    assert "EVIDENCE_DOCUMENT_STUDY_MISMATCH" in _codes(report)


def test_evidence_cannot_use_failed_or_ocr_pending_document():
    artifacts = _artifacts()
    documents = _by_type(artifacts, "document_manifest")
    documents["data"]["documents"][0]["content_status"] = "NEEDS_OCR"
    documents["data"]["documents"][0]["extracted_path"] = None
    report = validate_artifact_chain(artifacts)
    assert not report.valid
    assert "UNUSABLE_EVIDENCE_DOCUMENT" in _codes(report)


def test_duplicate_artifact_ids_and_lineage_cycles_are_rejected():
    artifacts = _artifacts()
    duplicate = copy.deepcopy(artifacts[-1])
    artifacts.append(duplicate)
    report = validate_artifact_chain(artifacts)
    assert not report.valid
    assert "DUPLICATE_ARTIFACT_ID" in _codes(report)

    artifacts = _artifacts()
    corpus = _by_type(artifacts, "corpus_snapshot")
    claims = _by_type(artifacts, "claims_ledger")
    corpus["inputs"] = [
        {"artifact_id": claims["artifact_id"], "sha256": "sha256:" + "0" * 64}
    ]
    report = validate_artifact_chain(artifacts)
    assert not report.valid
    assert "ARTIFACT_LINEAGE_CYCLE" in _codes(report)
