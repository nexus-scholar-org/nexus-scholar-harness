"""Executable conformance tests for the WP-00 cross-kit contract baseline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from scholar_harness.contracts import (
    ArtifactEnvelope,
    ArtifactReference,
    ClaimEvidenceLedger,
    IdentifierKind,
    OperationOutcome,
    OperationStatus,
    RunManifest,
    ScreeningBatchArtifact,
    ScreeningDecisionsArtifact,
    canonical_fingerprint,
    canonical_json_bytes,
    deterministic_id,
    identifier_registry,
    load_schema,
    normalize_doi,
    render_schema_files,
    validate_identifier,
)

FIXTURES = Path(__file__).parent / "fixtures" / "contracts" / "v1"
SCHEMAS = (
    Path(__file__).parents[1]
    / "src"
    / "scholar_harness"
    / "contracts"
    / "schemas"
    / "v1"
)


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("filename", "model"),
    [
        ("artifact_envelope.json", ArtifactEnvelope[dict]),
        ("operation_outcome_partial.json", OperationOutcome[dict]),
        ("claim_evidence_ledger.json", ClaimEvidenceLedger),
        ("screening_batch.json", ScreeningBatchArtifact),
        ("screening_decisions.json", ScreeningDecisionsArtifact),
        ("run_manifest.json", RunManifest),
    ],
)
def test_golden_contract_fixture_validates(filename, model):
    parsed = model.model_validate(_fixture(filename))
    assert parsed.model_dump(mode="json")


def test_generated_schema_catalog_is_current_and_loadable():
    rendered = render_schema_files()
    assert rendered
    for filename, expected in rendered.items():
        assert (SCHEMAS / filename).read_text(encoding="utf-8") == expected
        loaded = load_schema(filename)
        assert loaded["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_identifier_registry_has_unique_mint_prefixes_and_registered_legacy_ids():
    registry = identifier_registry()
    mint_prefixes = [entry["mint_prefix"] for entry in registry.values()]
    assert len(mint_prefixes) == len(set(mint_prefixes))
    assert "SCI-" in registry["study"]["legacy_prefixes"]
    assert "EVT-" in registry["audit_event"]["legacy_prefixes"]
    assert validate_identifier(IdentifierKind.STUDY, "SCI-000001") == "SCI-000001"


def test_deterministic_ids_are_stable_namespaced_and_semantically_typed():
    first = deterministic_id(
        IdentifierKind.STUDY,
        "WSP-example",
        {"doi": "10.1000/example"},
    )
    second = deterministic_id(
        IdentifierKind.STUDY,
        "WSP-example",
        {"doi": "10.1000/example"},
    )
    other_workspace = deterministic_id(
        IdentifierKind.STUDY,
        "WSP-other",
        {"doi": "10.1000/example"},
    )
    assert first == second
    assert first.startswith("STU-")
    assert first != other_workspace


@pytest.mark.parametrize(
    "raw",
    [
        "10.1000/ABC",
        " doi:10.1000/ABC ",
        "https://doi.org/10.1000/ABC",
        "http://dx.doi.org/10.1000/ABC",
    ],
)
def test_doi_normalization_is_idempotent_and_preserves_comparison_identity(raw):
    normalized = normalize_doi(raw)
    assert normalized == "10.1000/abc"
    assert normalize_doi(normalized) == normalized


def test_canonical_json_normalizes_maps_whitespace_and_integral_numbers():
    left = {"z": 1.0, "a": {"b": True, "a": None}}
    right = {"a": {"a": None, "b": True}, "z": 1}
    assert canonical_json_bytes(left) == canonical_json_bytes(right)
    assert canonical_fingerprint(left) == canonical_fingerprint(right)

    with pytest.raises(TypeError, match="keys must be strings"):
        canonical_json_bytes({1: "ambiguous", "1": "collision"})


def test_canonical_json_preserves_semantic_array_order_unless_registered_set_like():
    forward = {"study_ids": ["STU-a", "STU-b"]}
    reverse = {"study_ids": ["STU-b", "STU-a"]}
    assert canonical_fingerprint(forward) != canonical_fingerprint(reverse)
    assert canonical_fingerprint(
        forward, set_like_arrays=["/study_ids"]
    ) == canonical_fingerprint(reverse, set_like_arrays=["/study_ids"])


def test_unknown_major_rejected_but_v1_minor_fields_round_trip():
    payload = _fixture("artifact_envelope.json")
    payload["schema_version"] = "1.4.0"
    payload["future_field"] = {"preserve": True}
    model = ArtifactEnvelope[dict].model_validate(payload)
    assert model.model_dump(mode="json")["future_field"] == {"preserve": True}

    payload["schema_version"] = "2.0.0"
    with pytest.raises(ValidationError, match="unsupported schema_version"):
        ArtifactEnvelope[dict].model_validate(payload)


def test_versions_and_typed_artifact_discriminators_are_explicit():
    artifact = _fixture("artifact_envelope.json")
    del artifact["schema_version"]
    with pytest.raises(ValidationError, match="schema_version"):
        ArtifactEnvelope[dict].model_validate(artifact)

    outcome = _fixture("operation_outcome_partial.json")
    del outcome["contract_version"]
    with pytest.raises(ValidationError, match="contract_version"):
        OperationOutcome[dict].model_validate(outcome)

    ledger = _fixture("claim_evidence_ledger.json")
    ledger["artifact_type"] = "screening_batch"
    with pytest.raises(ValidationError, match="claims_ledger"):
        ClaimEvidenceLedger.model_validate(ledger)


@pytest.mark.parametrize("status", [OperationStatus.ERROR, OperationStatus.FAILED])
def test_hard_failure_outcome_requires_structured_error(status):
    payload = _fixture("operation_outcome_partial.json")
    payload["status"] = status
    payload["errors"] = []
    with pytest.raises(ValidationError, match="must include at least one error"):
        OperationOutcome[dict].model_validate(payload)


def test_partial_and_success_outcomes_cannot_hide_diagnostics():
    payload = _fixture("operation_outcome_partial.json")
    payload["warnings"] = []
    payload["errors"] = []
    with pytest.raises(ValidationError, match="must explain the degradation"):
        OperationOutcome[dict].model_validate(payload)

    payload["status"] = "SUCCESS"
    payload["errors"] = [
        {"code": "NETWORK_ERROR", "message": "hidden", "retryable": False}
    ]
    with pytest.raises(ValidationError, match="SUCCESS outcomes cannot contain errors"):
        OperationOutcome[dict].model_validate(payload)


@pytest.mark.parametrize(
    "path",
    [
        "../outside.json",
        "/absolute.json",
        "C:/absolute.json",
        ".",
        "literature\\windows.json",
    ],
)
def test_artifact_paths_must_be_workspace_relative_posix(path):
    with pytest.raises(ValidationError, match="workspace|POSIX"):
        ArtifactReference.model_validate(
            {
                "artifact_id": "ART-example",
                "path": path,
                "sha256": "sha256:" + "a" * 64,
            }
        )


def test_screening_binding_mismatch_fails_closed():
    payload = _fixture("screening_batch.json")
    payload["data"]["binding"]["corpus_fingerprint"] = "sha256:" + "c" * 64
    with pytest.raises(ValidationError, match="corpus_fingerprint"):
        ScreeningBatchArtifact.model_validate(payload)


def test_claim_ledger_rejects_unresolved_evidence_and_untyped_citation_tokens():
    payload = _fixture("claim_evidence_ledger.json")
    payload["data"]["evidence"] = []
    with pytest.raises(ValidationError, match="missing evidence IDs"):
        ClaimEvidenceLedger.model_validate(payload)

    payload = _fixture("claim_evidence_ledger.json")
    payload["data"]["claims"][0]["citation_tokens"] = ["[SCI-000001]"]
    with pytest.raises(ValidationError, match="rag:v2"):
        ClaimEvidenceLedger.model_validate(payload)


def test_claim_ledger_rejects_cross_study_evidence_contamination():
    payload = _fixture("claim_evidence_ledger.json")
    payload["data"]["evidence"][0]["study_id"] = "STU-beta"
    with pytest.raises(ValidationError, match="unlisted study"):
        ClaimEvidenceLedger.model_validate(payload)


def test_run_manifest_rejects_reverse_time():
    payload = _fixture("run_manifest.json")
    payload["data"]["ended_at"] = "2026-09-17T23:59:59Z"
    with pytest.raises(ValidationError, match="cannot precede"):
        RunManifest.model_validate(payload)
