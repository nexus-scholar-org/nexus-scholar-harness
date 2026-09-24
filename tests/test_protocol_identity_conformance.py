"""Cross-kit conformance tests for Packet A: Protocol identity producer."""

from __future__ import annotations

import json
from pathlib import Path

from scholar_harness.contracts import (
    IdentifierKind,
    Producer,
    validate_identifier,
)
from scholar_protocol import (
    ProtocolIdentity,
    get_protocol_identity,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = (
    Path(__file__).parents[1]
    / "tools"
    / "scholar-protocol-kit"
    / "tests"
    / "fixtures"
    / "canonical"
)


def test_protocol_identity_emits_valid_contract_identifiers():
    base_fixture = FIXTURES / "identity_base.json"
    ident = get_protocol_identity(base_fixture)

    assert isinstance(ident, ProtocolIdentity)
    # 1. PRT-* ID must pass harness identifier validation
    validated_id = validate_identifier(IdentifierKind.PROTOCOL, ident.protocol_id)
    assert validated_id == ident.protocol_id
    assert validated_id.startswith("PRT-")

    # 2. Producer metadata must conform to Contract v1 Producer schema
    producer_dict = ident.producer.model_dump(mode="json")
    contract_producer = Producer.model_validate(producer_dict)
    assert contract_producer.package == "scholar-protocol-kit"
    assert contract_producer.version == "1.0.0"
    assert len(contract_producer.commit) >= 7

    # 3. Protocol fingerprint must match sha256 pattern
    assert ident.protocol_fingerprint.startswith("sha256:")
    assert len(ident.protocol_fingerprint) == 71

    plugins = json.loads(
        (ROOT / ".agents" / "plugins" / "nexus-scholar" / "plugins.json").read_text(
            encoding="utf-8"
        )
    )
    expected_commit = next(
        item["default_rev"]
        for item in plugins["plugins"]
        if item["name"] == "scholar-protocol-kit"
    )
    assert ident.producer.commit == expected_commit


def test_protocol_identity_minting_from_legacy_satisfies_contract():
    legacy_protocol = {
        "$schema": "schemas/v1/protocol.schema.json",
        "protocol_id": "proto-legacy-2026",
        "created_at": "2026-09-20T12:00:00+00:00",
        "project_slug": "test-legacy",
        "playbook_type": "SCOPING_REVIEW",
        "metadata": {"title": "Legacy Protocol Test"},
        "epistemology": {
            "primary_paradigm": "Positivist",
            "unit_of_analysis": "Papers",
            "trustworthiness_framework": "PRISMA",
            "epistemological_rationale": "Testing",
        },
        "research_questions": [
            {
                "id": "RQ1",
                "text": "Legacy question?",
                "target_facet": "facet",
                "required_evidence_type": "evidence",
            }
        ],
        "search_strategy": {
            "core_concepts": [{"concept": "Test", "synonyms": []}]
        },
        "screening_criteria": {
            "inclusion": [{"id": "INC-01", "criterion": "Include all"}],
            "exclusion": [{"id": "EXC-01", "criterion": "Exclude none"}],
        },
    }

    ident = get_protocol_identity(legacy_protocol)
    assert ident.protocol_id.startswith("PRT-")
    validate_identifier(IdentifierKind.PROTOCOL, ident.protocol_id)
    assert ident.protocol_fingerprint.startswith("sha256:")


def test_protocol_identity_formatting_invariance_and_semantic_divergence():
    base_path = FIXTURES / "identity_base.json"
    variant_path = FIXTURES / "identity_formatting_variant.json"
    semantic_path = FIXTURES / "identity_semantic_variant.json"

    base_ident = get_protocol_identity(base_path)
    variant_ident = get_protocol_identity(variant_path)
    semantic_ident = get_protocol_identity(semantic_path)

    # Formatting invariance: identical protocol ID and fingerprint
    assert base_ident.protocol_id == variant_ident.protocol_id
    assert base_ident.protocol_fingerprint == variant_ident.protocol_fingerprint
    assert base_ident.canonical_bytes == variant_ident.canonical_bytes

    # Semantic divergence: distinct fingerprint and distinct minted IDs
    assert base_ident.protocol_fingerprint != semantic_ident.protocol_fingerprint
    assert base_ident.canonical_bytes != semantic_ident.canonical_bytes
