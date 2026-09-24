"""Conformance tests for scholar-search-kit identity contracts."""

import json
from datetime import UTC, datetime
from pathlib import Path

from scholar_harness.contracts import CorpusSnapshotArtifact, OperationOutcome
from scholar_harness.contracts.identifiers import IdentifierKind, validate_identifier
from scholar_search.identity import (
    CorpusProducer,
    build_corpus_snapshot_artifact,
    get_corpus_identity,
)
from scholar_search.models import Author, Document, ExternalIds


def test_corpus_identity_conformance():
    """Verify CorpusSnapshotIdentity matches harness Contract v1 constraints."""
    fixture_path = (
        Path(__file__).parent.parent
        / "tools"
        / "scholar-search-kit"
        / "tests"
        / "fixtures"
        / "canonical"
        / "identity_base.json"
    )

    ident = get_corpus_identity(fixture_path, commit="abc1234")

    # 1. Identifier constraints (XC-001)
    validate_identifier(IdentifierKind.CORPUS, ident.corpus_id)

    # 2. Fingerprint constraints (XC-036 envelope prep)
    assert ident.corpus_fingerprint.startswith("sha256:")
    assert len(ident.corpus_fingerprint) == 7 + 64

    # 3. Producer schema
    assert isinstance(ident.producer, CorpusProducer)
    assert ident.producer.package == "scholar-search-kit"
    assert ident.producer.version
    assert ident.producer.commit == "abc1234"

    # 4. Schema version
    assert ident.schema_version == "1.0.0"

    # 5. Envelope context serialization
    env = ident.as_envelope_context()
    assert env["corpus_id"] == ident.corpus_id
    assert env["corpus_fingerprint"] == ident.corpus_fingerprint

    plugins = json.loads(
        (
            Path(__file__).parents[1]
            / ".agents"
            / "plugins"
            / "nexus-scholar"
            / "plugins.json"
        ).read_text(encoding="utf-8")
    )
    expected_commit = next(
        item["default_rev"]
        for item in plugins["plugins"]
        if item["name"] == "scholar-search-kit"
    )
    assert get_corpus_identity(fixture_path).producer.commit == expected_commit


def test_search_producer_emits_typed_corpus_snapshot_and_outcome():
    documents = [
        Document(
            title="Contract producer",
            year=2026,
            provider="crossref",
            provider_id="record-1",
            external_ids=ExternalIds(doi="10.1000/contract"),
            authors=[Author("Scholar")],
        )
    ]
    result = build_corpus_snapshot_artifact(
        documents,
        workspace_id="WSP-search-contract",
        run_id="RUN-search-contract",
        protocol_fingerprint="sha256:" + "a" * 64,
        created_at=datetime(2026, 9, 21, tzinfo=UTC),
        commit="2" * 40,
    )

    artifact = CorpusSnapshotArtifact.model_validate(result.artifact)
    outcome = OperationOutcome[dict].model_validate(result.outcome)
    assert artifact.data.record_to_study
    assert outcome.status.value == "SUCCESS"
