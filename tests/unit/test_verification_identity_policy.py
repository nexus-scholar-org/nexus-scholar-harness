"""HCM-04e-1 policy: Stage 3 verification identity bridge-or-refuse (Option B).

Hermetic (``tmp_path`` only, no network). Every verifier/provider interaction
is a controlled double or a pure local call; doubles are never presented as
production frequency evidence.

Policy under test (approved Option B):

* Preserve a valid verifier-returned ``workspace_id``.
* Restore ONLY via a DOI bridge to a recorded dedup parent (case/prefix
  insensitive through kit ``ExternalIds`` normalization).
* No identity after the bridge -> NO ``SCI-`` mint, NO inference, NO
  downstream publication of the row; the row is quarantined to
  ``literature/verified_unresolved.json`` with its exact refusal reason.
* Mixed batch -> verification stage ``PARTIAL`` with counts+reasons; all
  refused -> ``FAILED``, never ``SUCCESS``; top-level pipeline status is
  never ``SUCCESS`` for an all-refused run (it remains
  ``PENDING_AGENT_REVIEW`` at the screening handoff, which is not success).
* Collector parity: no independent mint; a verified row without a
  ``workspace_id`` is refused fail-closed with the same typed vocabulary
  before any publication.

Covers REQUIRED BEHAVIOR A (preserve+bridge), B (refusal, never mint), C
(audit truthfulness, verifier evidence unmutated), D (collector parity,
determinism).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from scholar_harness import orchestrator as orch
from scholar_harness.pipeline import hydration as hyd_mod
from scholar_harness.verification_identity import (
    QUARANTINE_FILENAME,
    VERIFICATION_IDENTITY_AMBIGUOUS_DOI,
    VERIFICATION_IDENTITY_BRIDGE_MISS,
    VERIFICATION_IDENTITY_MISSING_DOI,
    VerificationIdentityRefused,
    build_doi_bridge,
)

_POLICY_ROOT = Path(__file__).resolve().parents[2]
_POLICY_PROTOCOL_FIXTURE = (
    _POLICY_ROOT
    / "tools"
    / "scholar-protocol-kit"
    / "tests"
    / "fixtures"
    / "canonical"
    / "identity_base.json"
)


# ---------------------------------------------------------------------------
# Helpers (mirroring the VEI characterization harness; tmp_path only)
# ---------------------------------------------------------------------------


def _write_protocol(ws: Path, slug: str = "hcm-04e-1-test") -> Path:
    from scholar_protocol.canonical import canonical_json
    from scholar_protocol.compiler import compile_protocol
    from scholar_protocol.intent import IntentPacket

    data = {
        "protocol_id": "hcm-04e-1",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": slug,
        "playbook_type": "DESIGN_SCIENCE",
        "title": "HCM-04e-1 Verification Identity Policy",
        "lead_researcher": "Test Lead",
        "unit_of_analysis": "Harness Pipelines",
        "epistemological_rationale": "Empirical Benchmark",
        "research_questions": [
            {
                "text": "Does bridge-or-refuse hold?",
                "target_facet": "evaluation_metrics",
                "required_evidence_type": "Quantitative Benchmark",
            }
        ],
        "core_concepts": [{"concept": "Pipeline", "synonyms": ["orchestrator"]}],
        "inclusion_criteria": [
            {"criterion": "Reports benchmark pass rates", "maps_to_rqs": ["RQ1"]}
        ],
        "exclusion_criteria": [
            {
                "criterion": "Non-English",
                "reason_category": "LANGUAGE",
                "maps_to_rqs": ["RQ1"],
            }
        ],
        "matrix_dimensions": [
            {
                "id": "throughput",
                "name": "Throughput",
                "description": "Operations per second",
            }
        ],
    }
    intent = IntentPacket.model_validate(data)
    proto = json.loads(canonical_json(compile_protocol(intent)).decode("utf-8"))
    p = ws / "protocol.json"
    p.write_text(json.dumps(proto), encoding="utf-8")
    return p


def _make_two_distinct_docs():
    from scholar_search.models import Document, ExternalIds

    return [
        Document(
            title="First Verification Study",
            year=2024,
            provider="openalex",
            provider_id="W1",
            external_ids=ExternalIds(doi="10.1000/aaa"),
            abstract="First abstract with content.",
        ),
        Document(
            title="Second Verification Study",
            year=2023,
            provider="crossref",
            provider_id="C2",
            external_ids=ExternalIds(doi="10.1000/bbb"),
            abstract="Second abstract with content.",
        ),
    ]


def _stub_screening_prepare(monkeypatch):
    monkeypatch.setattr(
        "scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None
    )


def _install_passthrough_hydration(monkeypatch):
    class _FakeHydrator:
        def __init__(self, client):
            pass

        async def hydrate_missing_abstracts(self, docs, batch_size=50):
            return list(docs), {"attempted": 0, "hydrated": 0, "failed": 0}

    class _FakeClient:
        def __init__(self, *a, **k):
            pass

        async def close(self):
            pass

    monkeypatch.setattr(hyd_mod, "AbstractHydrator", _FakeHydrator)
    monkeypatch.setattr(hyd_mod, "AcademicHttpClient", _FakeClient)


def _install_fake_engine(monkeypatch, docs):
    class _FakeEngine:
        def __init__(self, providers=None):
            pass

        async def search_all(self, query, dedup=False):
            import copy

            return copy.deepcopy(docs)

        async def close(self):
            pass

    monkeypatch.setattr(orch, "SearchEngine", _FakeEngine)


def _run_pipeline(ws: Path) -> dict:
    return asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())


def _verified_json(ws: Path) -> list[dict]:
    return json.loads((ws / "literature" / "verified.json").read_text(encoding="utf-8"))


def _quarantine_json(ws: Path) -> list[dict]:
    path = ws / "literature" / QUARANTINE_FILENAME
    assert path.exists(), f"expected quarantine at {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def _journal_rows(ws: Path) -> list[dict]:
    journal = ws / "audit" / "journal.jsonl"
    assert journal.exists()
    return [
        json.loads(line)
        for line in journal.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _fresh_doc_without_workspace(src):
    from scholar_search.models import Document, ExternalIds

    return Document(
        title=src.title,
        year=src.year,
        provider=src.provider,
        provider_id=src.provider_id,
        external_ids=ExternalIds(doi=src.external_ids.doi),
        abstract=src.abstract,
    )


# ---------------------------------------------------------------------------
# A: preserve valid + bridge-only restore
# ---------------------------------------------------------------------------


def test_policy_preserves_valid_workspace_id(tmp_path, monkeypatch):
    """A verifier that keeps workspace_id never enters the bridge or refusal."""
    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    _stub_screening_prepare(monkeypatch)

    class _PassthroughVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return list(docs), []

    monkeypatch.setattr(orch, "DocumentVerifier", _PassthroughVerifier)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    results = _run_pipeline(ws)

    stage = results["stages"]["verification"]
    assert stage["status"] == "SUCCESS"
    assert stage["verified"] == 2 and stage["refused"] == 0
    assert stage["preserved"] == 2 and stage["bridge_restored"] == 0
    verified = _verified_json(ws)
    assert [d["workspace_id"] for d in verified] == ["SCI-000001", "SCI-000002"]
    assert not (ws / "literature" / QUARANTINE_FILENAME).exists()


def test_policy_bridge_restores_via_doi(tmp_path, monkeypatch):
    """Dropping verifier + same DOI restores dedup IDs; no mint, no quarantine."""
    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    _stub_screening_prepare(monkeypatch)

    class _DroppingVerifierSameDOI:
        async def process_batch(self, docs, verify=True, enrich=True):
            return [_fresh_doc_without_workspace(d) for d in docs], []

    monkeypatch.setattr(orch, "DocumentVerifier", _DroppingVerifierSameDOI)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    results = _run_pipeline(ws)

    stage = results["stages"]["verification"]
    assert stage["status"] == "SUCCESS"
    assert stage["verified"] == 2 and stage["refused"] == 0
    assert stage["bridge_restored"] == 2
    verified = _verified_json(ws)
    assert [d["workspace_id"] for d in verified] == ["SCI-000001", "SCI-000002"]
    assert not (ws / "literature" / QUARANTINE_FILENAME).exists()
    rows = _journal_rows(ws)
    actions = [r.get("action") for r in rows]
    assert "VERIFICATION_IDENTITY_RESOLVED" in actions
    event = next(r for r in rows if r.get("action") == "VERIFICATION_IDENTITY_RESOLVED")
    assert event["status"] == "SUCCESS"
    assert event["metrics"]["bridge_restored"] == 2


# ---------------------------------------------------------------------------
# B: miss / changed-DOI -> typed refusal, never mint, never publish
# ---------------------------------------------------------------------------


def test_policy_refuses_when_no_doi(tmp_path, monkeypatch):
    """Stripping verifier (no DOI, no workspace_id) is refused, not minted."""
    from scholar_search.models import Document

    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    _stub_screening_prepare(monkeypatch)

    class _StrippingVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return [
                Document(
                    title=d.title,
                    year=d.year,
                    provider=d.provider,
                    provider_id=d.provider_id,
                    abstract=d.abstract,
                )
                for d in docs
            ], []

    monkeypatch.setattr(orch, "DocumentVerifier", _StrippingVerifier)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    results = _run_pipeline(ws)

    stage = results["stages"]["verification"]
    assert stage["status"] == "FAILED"
    assert stage["verified"] == 0 and stage["refused"] == 2
    assert stage["refusal_reasons"] == {VERIFICATION_IDENTITY_MISSING_DOI: 2}
    # No authoritative publication for refused rows.
    assert _verified_json(ws) == []
    assert results["stages"]["screening"]["papers_to_screen"] == 0
    # Top level is the screening pause, never SUCCESS for an all-refused run.
    assert results["status"] != "SUCCESS"
    # Quarantine carries the exact reason; verifier evidence is unmutated
    # (no invented workspace_id, titles/DOI preserved as returned).
    quarantined = _quarantine_json(ws)
    assert len(quarantined) == 2
    assert {q["code"] for q in quarantined} == {VERIFICATION_IDENTITY_MISSING_DOI}
    for q in quarantined:
        assert q["record"].get("workspace_id") in (None, "")
        assert q["record"]["external_ids"]["doi"] is None
    titles = sorted(q["record"]["title"] for q in quarantined)
    assert titles == ["First Verification Study", "Second Verification Study"]
    # No SCI- text is fabricated anywhere in the authoritative outputs.
    raw_verified = (ws / "literature" / "verified.json").read_text(encoding="utf-8")
    assert "SCI-" not in raw_verified


def test_policy_refuses_when_verifier_changes_doi(tmp_path, monkeypatch):
    """Changed DOI misses the bridge and is refused with BRIDGE_MISS."""
    from scholar_search.models import Document, ExternalIds

    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    _stub_screening_prepare(monkeypatch)

    class _ChangingVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return [
                Document(
                    title=d.title,
                    year=d.year,
                    provider=d.provider,
                    provider_id=d.provider_id,
                    external_ids=ExternalIds(doi=f"10.9999/changed-{i}"),
                    abstract=d.abstract,
                )
                for i, d in enumerate(docs)
            ], []

    monkeypatch.setattr(orch, "DocumentVerifier", _ChangingVerifier)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    results = _run_pipeline(ws)

    stage = results["stages"]["verification"]
    assert stage["status"] == "FAILED"
    assert stage["verified"] == 0 and stage["refused"] == 2
    assert stage["refusal_reasons"] == {VERIFICATION_IDENTITY_BRIDGE_MISS: 2}
    assert _verified_json(ws) == []
    quarantined = _quarantine_json(ws)
    assert [q["record"]["external_ids"]["doi"] for q in quarantined] == [
        "10.9999/changed-0",
        "10.9999/changed-1",
    ]
    assert all(q["record"].get("workspace_id") in (None, "") for q in quarantined)
    assert "SCI-" not in (ws / "literature" / "verified.json").read_text(
        encoding="utf-8"
    )


def test_policy_bridge_is_ambiguous_safe():
    """A DOI claimed by two dedup parents refuses instead of picking one.

    Unreachable through the real Deduplicator today (one DOI -> one
    cluster), so this is a pure helper proof of the defensive rule: the
    builder reports the DOI as ambiguous and no singleton mapping is made.
    """
    from scholar_search.models import Document, ExternalIds

    parents = [
        Document(
            title="A",
            provider="x",
            provider_id="1",
            external_ids=ExternalIds(doi="10.1000/same"),
            workspace_id="SCI-000001",
        ),
        Document(
            title="B",
            provider="x",
            provider_id="2",
            external_ids=ExternalIds(doi="10.1000/same"),
            workspace_id="SCI-000002",
        ),
    ]
    singletons, ambiguous = build_doi_bridge(parents)
    assert singletons == {}
    assert ambiguous == {"10.1000/same"}


def test_policy_bridge_builder_is_order_independent():
    """Singleton map and ambiguous set do not depend on input order."""
    from scholar_search.models import Document, ExternalIds

    first = Document(
        title="A",
        provider="x",
        provider_id="1",
        external_ids=ExternalIds(doi="10.1000/aaa"),
        workspace_id="SCI-000001",
    )
    second = Document(
        title="B",
        provider="x",
        provider_id="2",
        external_ids=ExternalIds(doi="10.1000/bbb"),
        workspace_id="SCI-000002",
    )
    forward, forward_amb = build_doi_bridge([first, second])
    backward, backward_amb = build_doi_bridge([second, first])
    assert (
        forward
        == backward
        == {"10.1000/aaa": "SCI-000001", "10.1000/bbb": "SCI-000002"}
    )
    assert forward_amb == backward_amb == set()


# ---------------------------------------------------------------------------
# C: audit truthfulness (PARTIAL mixed batch, never SUCCESS for all-refused)
# ---------------------------------------------------------------------------


def test_policy_mixed_batch_is_partial_with_counts(tmp_path, monkeypatch):
    """One bridge-restored row + one stripped row -> PARTIAL with reasons."""
    from scholar_search.models import Document

    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    _stub_screening_prepare(monkeypatch)

    class _MixedVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            kept = _fresh_doc_without_workspace(docs[0])
            stripped = Document(
                title=docs[1].title,
                year=docs[1].year,
                provider=docs[1].provider,
                provider_id=docs[1].provider_id,
                abstract=docs[1].abstract,
            )
            return [kept, stripped], []

    monkeypatch.setattr(orch, "DocumentVerifier", _MixedVerifier)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    results = _run_pipeline(ws)

    stage = results["stages"]["verification"]
    assert stage["status"] == "PARTIAL"
    assert stage["verified"] == 1 and stage["refused"] == 1
    assert stage["bridge_restored"] == 1
    assert stage["refusal_reasons"] == {VERIFICATION_IDENTITY_MISSING_DOI: 1}
    verified = _verified_json(ws)
    assert len(verified) == 1
    assert verified[0]["workspace_id"] == "SCI-000001"
    assert results["stages"]["screening"]["papers_to_screen"] == 1
    quarantined = _quarantine_json(ws)
    assert len(quarantined) == 1
    assert quarantined[0]["code"] == VERIFICATION_IDENTITY_MISSING_DOI
    # Audit event carries counts+reasons with PARTIAL status; metrics carry
    # no titles (no PII), only codes and counts.
    rows = _journal_rows(ws)
    event = next(r for r in rows if r.get("action") == "VERIFICATION_IDENTITY_RESOLVED")
    assert event["status"] == "PARTIAL"
    assert event["metrics"]["verified"] == 1
    assert event["metrics"]["refused"] == 1
    assert event["metrics"]["refusal_reasons"] == {VERIFICATION_IDENTITY_MISSING_DOI: 1}
    assert "First Verification Study" not in json.dumps(event["metrics"])


def test_policy_all_refused_is_never_success(tmp_path, monkeypatch):
    """All-refused run: verification FAILED, top level never SUCCESS."""
    from scholar_search.models import Document

    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    _stub_screening_prepare(monkeypatch)

    class _StrippingVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return [
                Document(
                    title=d.title,
                    year=d.year,
                    provider=d.provider,
                    provider_id=d.provider_id,
                    abstract=d.abstract,
                )
                for d in docs
            ], []

    monkeypatch.setattr(orch, "DocumentVerifier", _StrippingVerifier)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    results = _run_pipeline(ws)

    assert results["stages"]["verification"]["status"] == "FAILED"
    assert results["status"] != "SUCCESS"
    rows = _journal_rows(ws)
    event = next(r for r in rows if r.get("action") == "VERIFICATION_IDENTITY_RESOLVED")
    assert event["status"] == "FAILED"
    # The pause event still exists (pipeline reached the screening handoff);
    # the refusal itself is carried by the Stage-3 event, not hidden.
    assert any(r.get("action") == "PIPELINE_RUN_PAUSED_FOR_SCREENING" for r in rows)


# ---------------------------------------------------------------------------
# D: collector parity (no independent mint) + determinism
# ---------------------------------------------------------------------------


def test_policy_collector_refuses_missing_workspace_id(tmp_path):
    """Collector raises typed refusal on an unresolved row; publishes nothing."""
    from scholar_harness.screening.collector import cmd_collect
    from scholar_harness.screening.batcher import cmd_prepare
    from scholar_protocol.canonical import canonical_fingerprint
    from scholar_protocol.models import ResearchProtocol
    from scholar_search.identity import build_corpus_snapshot_artifact
    from scholar_search.models import Author, Document, ExternalIds
    from scholar_harness.contracts import AcceptanceContext, accept_artifact
    from datetime import UTC, datetime

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "project.json").write_text(
        json.dumps({"project_id": "policy-collector", "stats": {}}), encoding="utf-8"
    )
    protocol = json.loads(_POLICY_PROTOCOL_FIXTURE.read_text(encoding="utf-8"))
    (workspace / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    protocol_hash = canonical_fingerprint(ResearchProtocol.model_validate(protocol))
    source = Document(
        title="Contract-bound screening",
        year=2026,
        provider="crossref",
        provider_id="screening-record",
        external_ids=ExternalIds(doi="10.1000/screening"),
        authors=[Author("Reviewer")],
    )
    built = build_corpus_snapshot_artifact(
        [source],
        workspace_id="WSP-screening-migration",
        run_id="RUN-search-screening",
        protocol_fingerprint=protocol_hash,
        created_at=datetime(2026, 9, 21, tzinfo=UTC),
        commit="3" * 40,
    )
    corpus = built.artifact
    result = accept_artifact(
        workspace,
        corpus,
        expected=AcceptanceContext(
            workspace_id=corpus["workspace_id"],
            protocol_fingerprint=protocol_hash,
            corpus_fingerprint=corpus["corpus_fingerprint"],
        ),
    )
    assert result.accepted
    study = corpus["data"]["studies"][0]
    literature = workspace / "literature"
    literature.mkdir()
    (literature / "verified.json").write_text(
        json.dumps(
            [
                {
                    "workspace_id": study["study_id"],
                    "title": study["title"],
                    "year": study["publication_year"],
                    "external_ids": {"doi": "10.1000/screening"},
                },
                {
                    "title": "Unresolved verification row",
                    "year": 2024,
                    "provider": "openalex",
                    "provider_id": "W9",
                    "external_ids": {"doi": None},
                    "authors": [],
                },
            ]
        ),
        encoding="utf-8",
    )

    cmd_prepare(workspace, batch_size=20)
    screening = workspace / "literature" / "screening"
    (screening / "batch_001_decisions.json").write_text(
        json.dumps(
            {
                "batch": 1,
                "reviewed_by": "human-reviewer-1",
                "timestamp": "2026-09-21T12:00:00Z",
                "decisions": [
                    {
                        "workspace_id": study["study_id"],
                        "decision": "INCLUDE",
                        "method": "HUMAN",
                        "screening_reasoning": "Matches the frozen criteria.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert issubclass(VerificationIdentityRefused, RuntimeError)
    with pytest.raises(VerificationIdentityRefused) as exc_info:
        cmd_collect(workspace)
    assert exc_info.value.code == VERIFICATION_IDENTITY_MISSING_DOI
    assert exc_info.value.details["position"] == 1
    # Fail-closed: no authoritative screening outputs are published.
    assert not (literature / "included.json").exists()
    assert not (literature / "excluded.json").exists()
    assert not (literature / "conflicts.json").exists()
    assert not (literature / "prisma_screening_report.md").exists()
    assert not (literature / "prisma_report.json").exists()
    # Also catchable as RuntimeError (existing collector guard shape).
    with pytest.raises(RuntimeError, match="collection blocked"):
        cmd_collect(workspace)


def test_policy_collector_refuses_missing_workspace_id_with_doi(tmp_path):
    """A DOI on the unresolved row does not authorize a collector mint."""
    from scholar_harness.screening.collector import cmd_collect
    from scholar_harness.screening.batcher import cmd_prepare
    from scholar_protocol.canonical import canonical_fingerprint
    from scholar_protocol.models import ResearchProtocol
    from scholar_search.identity import build_corpus_snapshot_artifact
    from scholar_search.models import Author, Document, ExternalIds
    from scholar_harness.contracts import AcceptanceContext, accept_artifact
    from datetime import UTC, datetime

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "project.json").write_text(
        json.dumps({"project_id": "policy-collector-doi", "stats": {}}),
        encoding="utf-8",
    )
    protocol = json.loads(_POLICY_PROTOCOL_FIXTURE.read_text(encoding="utf-8"))
    (workspace / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    protocol_hash = canonical_fingerprint(ResearchProtocol.model_validate(protocol))
    source = Document(
        title="Contract-bound screening",
        year=2026,
        provider="crossref",
        provider_id="screening-record",
        external_ids=ExternalIds(doi="10.1000/screening"),
        authors=[Author("Reviewer")],
    )
    built = build_corpus_snapshot_artifact(
        [source],
        workspace_id="WSP-screening-migration",
        run_id="RUN-search-screening",
        protocol_fingerprint=protocol_hash,
        created_at=datetime(2026, 9, 21, tzinfo=UTC),
        commit="3" * 40,
    )
    corpus = built.artifact
    assert accept_artifact(
        workspace,
        corpus,
        expected=AcceptanceContext(
            workspace_id=corpus["workspace_id"],
            protocol_fingerprint=protocol_hash,
            corpus_fingerprint=corpus["corpus_fingerprint"],
        ),
    ).accepted
    study = corpus["data"]["studies"][0]
    literature = workspace / "literature"
    literature.mkdir()
    (literature / "verified.json").write_text(
        json.dumps(
            [
                {
                    "workspace_id": study["study_id"],
                    "title": study["title"],
                    "year": study["publication_year"],
                    "external_ids": {"doi": "10.1000/screening"},
                },
                {
                    "title": "Changed-DOI row",
                    "year": 2024,
                    "provider": "openalex",
                    "provider_id": "W9",
                    "external_ids": {"doi": "10.9999/changed-0"},
                    "authors": [],
                },
            ]
        ),
        encoding="utf-8",
    )
    cmd_prepare(workspace, batch_size=20)
    screening = workspace / "literature" / "screening"
    (screening / "batch_001_decisions.json").write_text(
        json.dumps(
            {
                "batch": 1,
                "reviewed_by": "human-reviewer-1",
                "timestamp": "2026-09-21T12:00:00Z",
                "decisions": [
                    {
                        "workspace_id": study["study_id"],
                        "decision": "INCLUDE",
                        "method": "HUMAN",
                        "screening_reasoning": "Matches the frozen criteria.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(VerificationIdentityRefused) as exc_info:
        cmd_collect(workspace)
    assert exc_info.value.code == VERIFICATION_IDENTITY_BRIDGE_MISS
    assert not (literature / "included.json").exists()


def test_policy_refusal_set_is_order_independent(tmp_path, monkeypatch):
    """Rerun with swapped verifier order refuses the same set (no positions)."""
    from scholar_search.models import Document

    titles = ["Alpha Order Study", "Beta Order Study"]

    def _stripped_in_order(order):
        return [
            Document(title=t, year=2024, provider="x", provider_id=f"p-{t}")
            for t in order
        ]

    def _run_with_order(order, ws):
        _install_passthrough_hydration(monkeypatch)
        _install_fake_engine(monkeypatch, _make_two_distinct_docs())
        _stub_screening_prepare(monkeypatch)

        class _OrderedVerifier:
            async def process_batch(self, docs, verify=True, enrich=True):
                return _stripped_in_order(order), []

        monkeypatch.setattr(orch, "DocumentVerifier", _OrderedVerifier)
        _write_protocol(ws)
        results = _run_pipeline(ws)
        quarantine = json.loads(
            (ws / "literature" / QUARANTINE_FILENAME).read_text(encoding="utf-8")
        )
        return results, quarantine

    ws_a = tmp_path / "ws-a"
    ws_a.mkdir()
    _, quarantine_a = _run_with_order(titles, ws_a)
    ws_b = tmp_path / "ws-b"
    ws_b.mkdir()
    _, quarantine_b = _run_with_order(list(reversed(titles)), ws_b)

    titles_a = sorted(q["record"]["title"] for q in quarantine_a)
    titles_b = sorted(q["record"]["title"] for q in quarantine_b)
    assert titles_a == titles_b == sorted(titles)
    assert all(
        q["code"] == VERIFICATION_IDENTITY_MISSING_DOI
        for q in quarantine_a + quarantine_b
    )
