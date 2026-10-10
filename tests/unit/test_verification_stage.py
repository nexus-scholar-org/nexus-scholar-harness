"""Focused HCM-04e tests for the neutral verification stage.

Stage 3 (verifier check -> DOI-bridge bridge-or-refuse -> verified/quarantine
publication -> VERIFICATION_IDENTITY_RESOLVED audit) lives in
``scholar_harness.pipeline.verification``; the orchestrator delegates.
Every test is hermetic (``tmp_path`` only, fake verifiers/engines/hydrators,
real protocol compiler and real Deduplicator where lineage matters) and
asserts zero behavior change: Option B policy preserved exactly through the
stage entry, byte-identical verified/quarantine files, identical counts and
audit order/payload, unchanged downstream ``papers_to_screen`` binding, and
exception propagation with no fabricated state.

Mapping to the HCM-04e packet:

- HCM4E-01 preserve valid through stage
- HCM4E-02 bridge restore through stage
- HCM4E-03 missing-DOI refusal (no mint, quarantine, FAILED)
- HCM4E-04 changed/unmatched-DOI refusal (BRIDGE_MISS)
- HCM4E-05 ambiguous-DOI refusal (defensive, stage-level)
- HCM4E-06 mixed PARTIAL with counts
- HCM4E-07 all-refused never SUCCESS
- HCM4E-08 no-SCI-mint proof + stale-quarantine removal + empty input
- HCM4E-09 orchestrator<->stage parity (mapping, papers_to_screen, bytes,
  quarantine evidence, audit order+payload)
- HCM4E-10 shim + legacy orchestrator-namespace seam + region guards
- HCM4E-11 exceptions propagate (verifier raise, audit raise)
- HCM4E-12 negatives (mint/bridge/quarantine source guards)

Carry-forward note: the fidelity stubs still patch
``scholar_harness.orchestrator.DocumentVerifier`` (legacy seam). A later
coordinator packet should migrate them to patch
``scholar_harness.pipeline.verification.DocumentVerifier`` directly and drop
the orchestrator fallback in ``_verifier_class``.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from scholar_harness import orchestrator as orch
from scholar_harness.pipeline import verification as ver_mod
from scholar_harness.verification_identity import (
    QUARANTINE_FILENAME,
    VERIFICATION_IDENTITY_AMBIGUOUS_DOI,
    VERIFICATION_IDENTITY_BRIDGE_MISS,
    VERIFICATION_IDENTITY_MISSING_DOI,
)


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


def _make_three_distinct_docs():
    from scholar_search.models import Document, ExternalIds

    return [
        Document(
            title="Alpha Verification Study",
            year=2024,
            provider="openalex",
            provider_id="W1",
            external_ids=ExternalIds(doi="10.1000/aaa"),
            abstract="Alpha abstract.",
        ),
        Document(
            title="Beta Verification Study",
            year=2023,
            provider="crossref",
            provider_id="C2",
            external_ids=ExternalIds(doi="10.1000/bbb"),
            abstract="Beta abstract.",
        ),
        Document(
            title="Gamma Verification Study",
            year=2022,
            provider="arxiv",
            provider_id="A3",
            external_ids=ExternalIds(doi="10.1000/ccc"),
            abstract="Gamma abstract.",
        ),
    ]


def _deduped_docs(docs):
    from scholar_search.dedup import Deduplicator

    return [c.representative for c in Deduplicator().deduplicate(list(docs))]


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


def _golden_verified_text(docs) -> str:
    return json.dumps(
        [asdict(d) if hasattr(d, "__dataclass_fields__") else d for d in docs],
        indent=2,
        default=str,
    )


def _write_protocol(ws: Path, slug: str = "verification-stage-test") -> Path:
    from scholar_protocol.canonical import canonical_json
    from scholar_protocol.compiler import compile_protocol
    from scholar_protocol.intent import IntentPacket

    data = {
        "protocol_id": "verification-stage",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": slug,
        "playbook_type": "DESIGN_SCIENCE",
        "title": "Verification Stage Parity",
        "lead_researcher": "Test Lead",
        "unit_of_analysis": "Harness Pipelines",
        "epistemological_rationale": "Empirical Benchmark",
        "research_questions": [
            {
                "text": "Does bridge-or-refuse hold through the stage?",
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


def _stub_screening_prepare(monkeypatch):
    monkeypatch.setattr(
        "scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None
    )


def _install_passthrough_hydration(monkeypatch):
    from scholar_harness.pipeline import hydration as hyd_mod

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


def _run_stage(docs, lit, ws):
    return asyncio.run(
        ver_mod.run_verification(documents=docs, literature_dir=lit, workspace_dir=ws)
    )


def _journal_rows(ws: Path) -> list[dict]:
    p = ws / "audit" / "journal.jsonl"
    if not p.exists():
        return []
    return [
        json.loads(line)
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _verification_rows(ws: Path) -> list[dict]:
    return [
        r
        for r in _journal_rows(ws)
        if r.get("action") == "VERIFICATION_IDENTITY_RESOLVED"
    ]


# ---------------------------------------------------------------------------
# HCM4E-01 preserve valid through the stage entry
# ---------------------------------------------------------------------------


def test_stage_preserves_valid_workspace_id(tmp_path, monkeypatch):
    """HCM4E-01: verifier keeping workspace_id never enters bridge/refusal."""
    deduped = _deduped_docs(_make_two_distinct_docs())
    assert [d.workspace_id for d in deduped] == ["SCI-000001", "SCI-000002"]

    class _PassthroughVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            assert verify is True and enrich is True
            return list(docs), []

    monkeypatch.setattr(ver_mod, "DocumentVerifier", _PassthroughVerifier)
    ws = tmp_path / "ws"
    lit = ws / "literature"

    outcome = _run_stage(list(deduped), lit, ws)

    assert outcome.status == "SUCCESS"
    assert outcome.verified == 2 and outcome.refused == 0
    assert outcome.preserved == 2 and outcome.bridge_restored == 0
    assert outcome.refusal_reasons == {}
    assert outcome.quarantine is None
    assert [d.workspace_id for d in outcome.documents] == [
        "SCI-000001",
        "SCI-000002",
    ]
    assert (lit / "verified.json").read_text(encoding="utf-8") == _golden_verified_text(
        outcome.documents
    )
    assert not (lit / QUARANTINE_FILENAME).exists()
    rows = _verification_rows(ws)
    assert len(rows) == 1
    assert rows[0]["status"] == "SUCCESS"
    assert rows[0]["metrics"]["preserved"] == 2


# ---------------------------------------------------------------------------
# HCM4E-02 bridge restore through the stage entry
# ---------------------------------------------------------------------------


def test_stage_bridge_restores_via_doi(tmp_path, monkeypatch):
    """HCM4E-02: dropping verifier + same DOI restores dedup IDs, no mint."""
    deduped = _deduped_docs(_make_two_distinct_docs())

    class _DroppingVerifierSameDOI:
        async def process_batch(self, docs, verify=True, enrich=True):
            return [_fresh_doc_without_workspace(d) for d in docs], []

    monkeypatch.setattr(ver_mod, "DocumentVerifier", _DroppingVerifierSameDOI)
    ws = tmp_path / "ws"
    lit = ws / "literature"

    outcome = _run_stage(list(deduped), lit, ws)

    assert outcome.status == "SUCCESS"
    assert outcome.verified == 2 and outcome.refused == 0
    assert outcome.preserved == 0 and outcome.bridge_restored == 2
    assert [d.workspace_id for d in outcome.documents] == [
        "SCI-000001",
        "SCI-000002",
    ]
    assert not (lit / QUARANTINE_FILENAME).exists()
    rows = _verification_rows(ws)
    assert len(rows) == 1
    assert rows[0]["metrics"]["bridge_restored"] == 2
    assert rows[0]["status"] == "SUCCESS"


# ---------------------------------------------------------------------------
# HCM4E-03 missing-DOI refusal (no mint, quarantine, FAILED)
# ---------------------------------------------------------------------------


def test_stage_refuses_when_no_doi(tmp_path, monkeypatch):
    """HCM4E-03: stripping verifier is refused with MISSING_DOI, never minted."""
    from scholar_search.models import Document

    deduped = _deduped_docs(_make_two_distinct_docs())

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

    monkeypatch.setattr(ver_mod, "DocumentVerifier", _StrippingVerifier)
    ws = tmp_path / "ws"
    lit = ws / "literature"

    outcome = _run_stage(list(deduped), lit, ws)

    assert outcome.status == "FAILED"
    assert outcome.verified == 0 and outcome.refused == 2
    assert outcome.refusal_reasons == {VERIFICATION_IDENTITY_MISSING_DOI: 2}
    assert outcome.documents == []
    assert outcome.quarantine == f"literature/{QUARANTINE_FILENAME}"
    assert json.loads((lit / "verified.json").read_text(encoding="utf-8")) == []
    assert "SCI-" not in (lit / "verified.json").read_text(encoding="utf-8")
    quarantined = json.loads((lit / QUARANTINE_FILENAME).read_text(encoding="utf-8"))
    assert len(quarantined) == 2
    assert {q["code"] for q in quarantined} == {VERIFICATION_IDENTITY_MISSING_DOI}
    for q in quarantined:
        assert set(q.keys()) >= {"position", "code", "reason", "record"}
        assert q["record"].get("workspace_id") in (None, "")
        assert q["record"]["external_ids"]["doi"] is None
    rows = _verification_rows(ws)
    assert len(rows) == 1
    assert rows[0]["status"] == "FAILED"
    assert rows[0]["metrics"]["refused"] == 2


# ---------------------------------------------------------------------------
# HCM4E-04 changed/unmatched-DOI refusal (BRIDGE_MISS)
# ---------------------------------------------------------------------------


def test_stage_refuses_when_verifier_changes_doi(tmp_path, monkeypatch):
    """HCM4E-04: changed DOI misses the bridge -> BRIDGE_MISS, never published."""
    from scholar_search.models import Document, ExternalIds

    deduped = _deduped_docs(_make_two_distinct_docs())

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

    monkeypatch.setattr(ver_mod, "DocumentVerifier", _ChangingVerifier)
    ws = tmp_path / "ws"
    lit = ws / "literature"

    outcome = _run_stage(list(deduped), lit, ws)

    assert outcome.status == "FAILED"
    assert outcome.verified == 0 and outcome.refused == 2
    assert outcome.refusal_reasons == {VERIFICATION_IDENTITY_BRIDGE_MISS: 2}
    assert json.loads((lit / "verified.json").read_text(encoding="utf-8")) == []
    quarantined = json.loads((lit / QUARANTINE_FILENAME).read_text(encoding="utf-8"))
    assert [q["record"]["external_ids"]["doi"] for q in quarantined] == [
        "10.9999/changed-0",
        "10.9999/changed-1",
    ]
    assert all(q["record"].get("workspace_id") in (None, "") for q in quarantined)
    assert "SCI-" not in (lit / "verified.json").read_text(encoding="utf-8")


def test_stage_refuses_unmatched_doi_shape(tmp_path, monkeypatch):
    """HCM4E-04b: unmatched DOI (no recorded parent) is the same BRIDGE_MISS."""
    from scholar_search.models import Document, ExternalIds

    deduped = _deduped_docs(_make_two_distinct_docs())

    class _UnmatchedVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return [
                Document(
                    title=d.title,
                    year=d.year,
                    provider=d.provider,
                    provider_id=d.provider_id,
                    external_ids=ExternalIds(doi="10.1234/unmatched-shape"),
                    abstract=d.abstract,
                )
                for d in docs
            ], []

    monkeypatch.setattr(ver_mod, "DocumentVerifier", _UnmatchedVerifier)
    ws = tmp_path / "ws"
    lit = ws / "literature"

    outcome = _run_stage(list(deduped), lit, ws)

    assert outcome.status == "FAILED"
    assert outcome.refusal_reasons == {VERIFICATION_IDENTITY_BRIDGE_MISS: 2}


# ---------------------------------------------------------------------------
# HCM4E-05 ambiguous-DOI refusal (stage-level defensive rule)
# ---------------------------------------------------------------------------


def test_stage_refuses_ambiguous_doi(tmp_path, monkeypatch):
    """HCM4E-05: one DOI claimed by two dedup parents refuses, never picks one."""
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

    class _SameDOIVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return [
                Document(
                    title="Ambiguous Return",
                    provider="x",
                    provider_id="9",
                    external_ids=ExternalIds(doi="10.1000/same"),
                )
            ], []

    monkeypatch.setattr(ver_mod, "DocumentVerifier", _SameDOIVerifier)
    ws = tmp_path / "ws"
    lit = ws / "literature"

    outcome = _run_stage(list(parents), lit, ws)

    assert outcome.status == "FAILED"
    assert outcome.verified == 0 and outcome.refused == 1
    assert outcome.refusal_reasons == {VERIFICATION_IDENTITY_AMBIGUOUS_DOI: 1}
    quarantined = json.loads((lit / QUARANTINE_FILENAME).read_text(encoding="utf-8"))
    assert quarantined[0]["code"] == VERIFICATION_IDENTITY_AMBIGUOUS_DOI
    assert "multiple dedup parents" in quarantined[0]["reason"]


# ---------------------------------------------------------------------------
# HCM4E-06 mixed PARTIAL + HCM4E-07 all-refused never SUCCESS
# ---------------------------------------------------------------------------


def test_stage_mixed_batch_is_partial_with_counts(tmp_path, monkeypatch):
    """HCM4E-06: one bridge-restored + one stripped -> PARTIAL with reasons."""
    from scholar_search.models import Document

    deduped = _deduped_docs(_make_two_distinct_docs())

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

    monkeypatch.setattr(ver_mod, "DocumentVerifier", _MixedVerifier)
    ws = tmp_path / "ws"
    lit = ws / "literature"

    outcome = _run_stage(list(deduped), lit, ws)

    assert outcome.status == "PARTIAL"
    assert outcome.verified == 1 and outcome.refused == 1
    assert outcome.preserved == 0 and outcome.bridge_restored == 1
    assert outcome.refusal_reasons == {VERIFICATION_IDENTITY_MISSING_DOI: 1}
    assert outcome.quarantine == f"literature/{QUARANTINE_FILENAME}"
    verified = json.loads((lit / "verified.json").read_text(encoding="utf-8"))
    assert len(verified) == 1
    assert verified[0]["workspace_id"] == "SCI-000001"
    quarantined = json.loads((lit / QUARANTINE_FILENAME).read_text(encoding="utf-8"))
    assert len(quarantined) == 1
    assert quarantined[0]["code"] == VERIFICATION_IDENTITY_MISSING_DOI
    rows = _verification_rows(ws)
    assert rows[0]["status"] == "PARTIAL"
    assert rows[0]["metrics"]["verified"] == 1
    assert rows[0]["metrics"]["refused"] == 1
    assert "First Verification Study" not in json.dumps(rows[0]["metrics"])


def test_stage_all_refused_is_never_success(tmp_path, monkeypatch):
    """HCM4E-07: all-refused run is FAILED at the stage, never SUCCESS."""
    from scholar_search.models import Document

    deduped = _deduped_docs(_make_two_distinct_docs())

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

    monkeypatch.setattr(ver_mod, "DocumentVerifier", _StrippingVerifier)
    ws = tmp_path / "ws"
    lit = ws / "literature"

    outcome = _run_stage(list(deduped), lit, ws)

    assert outcome.status == "FAILED"
    assert outcome.status != "SUCCESS"
    rows = _verification_rows(ws)
    assert rows[0]["status"] == "FAILED"


# ---------------------------------------------------------------------------
# HCM4E-08 no-mint + stale removal + empty input
# ---------------------------------------------------------------------------


def test_stage_three_stripped_rows_never_mint(tmp_path, monkeypatch):
    """HCM4E-08: three stripped docs -> 3 refusals, empty verified, no SCI-."""
    from scholar_search.models import Document

    deduped = _deduped_docs(_make_three_distinct_docs())

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

    monkeypatch.setattr(ver_mod, "DocumentVerifier", _StrippingVerifier)
    ws = tmp_path / "ws"
    lit = ws / "literature"

    outcome = _run_stage(list(deduped), lit, ws)

    assert outcome.status == "FAILED"
    assert outcome.verified == 0 and outcome.refused == 3
    assert json.loads((lit / "verified.json").read_text(encoding="utf-8")) == []
    assert "SCI-" not in (lit / "verified.json").read_text(encoding="utf-8")


def test_stage_clean_run_removes_stale_quarantine(tmp_path, monkeypatch):
    """HCM4E-08b: a clean run removes a stale quarantine file."""
    deduped = _deduped_docs(_make_two_distinct_docs())

    class _PassthroughVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return list(docs), []

    monkeypatch.setattr(ver_mod, "DocumentVerifier", _PassthroughVerifier)
    ws = tmp_path / "ws"
    lit = ws / "literature"
    lit.mkdir(parents=True, exist_ok=True)
    (lit / QUARANTINE_FILENAME).write_text("[]", encoding="utf-8")

    outcome = _run_stage(list(deduped), lit, ws)

    assert outcome.status == "SUCCESS"
    assert not (lit / QUARANTINE_FILENAME).exists()


def test_stage_empty_input_is_success_with_empty_verified(tmp_path, monkeypatch):
    """HCM4E-08c: empty input preserves the observed SUCCESS-with-0 semantics."""

    class _EmptyVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return [], []

    monkeypatch.setattr(ver_mod, "DocumentVerifier", _EmptyVerifier)
    ws = tmp_path / "ws"
    lit = ws / "literature"

    outcome = _run_stage([], lit, ws)

    assert outcome.status == "SUCCESS"
    assert outcome.verified == 0 and outcome.refused == 0
    assert outcome.documents == []
    assert (lit / "verified.json").read_text(encoding="utf-8") == "[]"
    assert not (lit / QUARANTINE_FILENAME).exists()
    rows = _verification_rows(ws)
    assert len(rows) == 1
    assert rows[0]["status"] == "SUCCESS"


# ---------------------------------------------------------------------------
# HCM4E-09 orchestrator<->stage parity
# ---------------------------------------------------------------------------


def test_orchestrator_mapping_and_papers_to_screen_follow_outcome(
    tmp_path, monkeypatch
):
    """HCM4E-09a: orchestrator maps the stage outcome; Stage 4 counts identified."""
    _install_passthrough_hydration(monkeypatch)
    _install_fake_engine(monkeypatch, _make_two_distinct_docs())
    _stub_screening_prepare(monkeypatch)

    class _MixedVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            kept = _fresh_doc_without_workspace(docs[0])
            from scholar_search.models import Document

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
    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    stage = results["stages"]["verification"]
    assert stage["status"] == "PARTIAL"
    assert stage["verified"] == 1 and stage["refused"] == 1
    assert stage["preserved"] == 0 and stage["bridge_restored"] == 1
    assert stage["refusal_reasons"] == {VERIFICATION_IDENTITY_MISSING_DOI: 1}
    assert stage["quarantine"] == f"literature/{QUARANTINE_FILENAME}"
    assert results["stages"]["screening"]["papers_to_screen"] == 1
    assert results["stages"]["screening"]["papers_to_screen"] == stage["verified"]


def test_orchestrator_verified_bytes_match_golden_and_direct_stage(
    tmp_path, monkeypatch
):
    """HCM4E-09b: verified.json bytes are golden-serialized and stage-identical."""
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
    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert results["stages"]["verification"]["status"] == "SUCCESS"
    orch_bytes = (ws / "literature" / "verified.json").read_bytes()
    # Text-mode read normalizes Windows CRLF so the golden comparison is
    # platform-stable; read_bytes below proves byte identity between paths.
    orch_text = (ws / "literature" / "verified.json").read_text(encoding="utf-8")
    parsed = json.loads(orch_text)
    assert orch_text == _golden_verified_text(parsed)
    assert [d["workspace_id"] for d in parsed] == ["SCI-000001", "SCI-000002"]

    # Direct stage over equivalent fresh deduped docs is byte-identical.
    monkeypatch.setattr(ver_mod, "DocumentVerifier", _DroppingVerifierSameDOI)
    direct_lit = tmp_path / "direct" / "literature"
    direct_ws = tmp_path / "direct" / "ws"
    direct_outcome = _run_stage(
        _deduped_docs(_make_two_distinct_docs()), direct_lit, direct_ws
    )
    assert direct_outcome.status == "SUCCESS"
    assert (direct_lit / "verified.json").read_bytes() == orch_bytes


def test_quarantine_evidence_unchanged_between_paths(tmp_path, monkeypatch):
    """HCM4E-09c: quarantine records carry position/code/reason/record verbatim."""
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
    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert results["stages"]["verification"]["status"] == "FAILED"
    orch_quarantine = json.loads(
        (ws / "literature" / QUARANTINE_FILENAME).read_text(encoding="utf-8")
    )
    assert len(orch_quarantine) == 2
    for entry in orch_quarantine:
        assert set(entry.keys()) >= {"position", "code", "reason", "record"}
        assert entry["record"].get("workspace_id") in (None, "")
    titles = sorted(q["record"]["title"] for q in orch_quarantine)
    assert titles == ["First Verification Study", "Second Verification Study"]

    # Direct stage quarantine over the same stripped shape matches key-for-key.
    monkeypatch.setattr(ver_mod, "DocumentVerifier", _StrippingVerifier)
    direct_outcome = _run_stage(
        _deduped_docs(_make_two_distinct_docs()),
        tmp_path / "direct-lit",
        tmp_path / "direct-ws",
    )
    direct_quarantine = json.loads(
        (tmp_path / "direct-lit" / QUARANTINE_FILENAME).read_text(encoding="utf-8")
    )
    assert direct_outcome.refusal_reasons == {VERIFICATION_IDENTITY_MISSING_DOI: 2}
    for key in ("position", "code", "reason"):
        assert [q[key] for q in direct_quarantine] == [
            q[key] for q in orch_quarantine
        ], key


def test_audit_order_and_payload_preserved(tmp_path, monkeypatch):
    """HCM4E-09d: ABSTRACT_HYDRATION -> VERIFICATION -> PAUSE order + payload."""
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
    asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    rows = _journal_rows(ws)
    actions = [r.get("action") for r in rows]
    assert "ABSTRACT_HYDRATION" in actions
    assert "VERIFICATION_IDENTITY_RESOLVED" in actions
    assert "PIPELINE_RUN_PAUSED_FOR_SCREENING" in actions
    assert actions.index("ABSTRACT_HYDRATION") < actions.index(
        "VERIFICATION_IDENTITY_RESOLVED"
    )
    assert actions.index("VERIFICATION_IDENTITY_RESOLVED") < actions.index(
        "PIPELINE_RUN_PAUSED_FOR_SCREENING"
    )
    event = next(r for r in rows if r.get("action") == "VERIFICATION_IDENTITY_RESOLVED")
    assert event["agent_or_tool"] == "scholar-harness"
    assert event["description"] == (
        "Stage 3 verification identity bridge-or-refuse: "
        "0 preserved, 2 bridge-restored, 0 refused"
    )
    assert event["inputs"] == [str(ws / "literature" / "deduped.json")]
    assert event["outputs"] == [str(ws / "literature" / "verified.json")]
    assert event["metrics"] == {
        "preserved": 0,
        "bridge_restored": 2,
        "refused": 0,
        "verified": 2,
        "refusal_reasons": {},
        "status": "SUCCESS",
    }
    assert event["status"] == "SUCCESS"
    assert event["event_id"].startswith("EVT-")
    assert "First Verification Study" not in json.dumps(event["metrics"])


# ---------------------------------------------------------------------------
# HCM4E-10 shim + legacy seam + region guards
# ---------------------------------------------------------------------------


def test_shim_preserves_verification_identity():
    assert orch.DocumentVerifier is ver_mod.DocumentVerifier
    assert orch.run_verification is ver_mod.run_verification
    assert orch.VerificationOutcome is ver_mod.VerificationOutcome


def test_legacy_orchestrator_seam_honored(tmp_path, monkeypatch):
    """Transitional seam: an orchestrator-namespace fake is honored by the stage.

    Carry-forward: migrate fidelity stubs to patch
    ``pipeline.verification.DocumentVerifier`` directly in a later coordinator
    packet.
    """

    class _EmptyVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return [], []

    monkeypatch.setattr(orch, "DocumentVerifier", _EmptyVerifier)
    ws = tmp_path / "ws"
    lit = ws / "literature"

    outcome = _run_stage(_deduped_docs(_make_two_distinct_docs()), lit, ws)

    assert outcome.verified == 0 and outcome.refused == 0
    assert outcome.status == "SUCCESS"

    # Direct-module patch also works (future canonical seam): reset the legacy
    # override first so the stage falls through to its own global.
    monkeypatch.setattr(orch, "DocumentVerifier", ver_mod._REAL_VERIFIER)

    class _PassthroughVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return list(docs), []

    monkeypatch.setattr(ver_mod, "DocumentVerifier", _PassthroughVerifier)
    outcome2 = _run_stage(
        _deduped_docs(_make_two_distinct_docs()), tmp_path / "lit2", tmp_path / "ws2"
    )
    assert outcome2.verified == 2


def test_stage_has_no_console_transport_import():
    # Repair-1 pattern: import-statement guard (prose may mention "console").
    text = Path(ver_mod.__file__).read_text(encoding="utf-8")
    lines = text.splitlines()
    out, buf, depth = [], "", 0
    for line in lines:
        stripped = line.strip()
        if not buf and not stripped.startswith(("from ", "import ")):
            continue
        buf += line + "\n"
        depth += line.count("(") - line.count(")")
        if line.rstrip().endswith("\\"):
            continue
        if depth <= 0:
            out.append(buf)
            buf, depth = "", 0
    if buf:
        out.append(buf)
    for stmt in out:
        low = stmt.lower()
        assert "console" not in low
        assert "fastapi" not in low
        assert "uvicorn" not in low
    # Neutral stage calls the search kit (Repair-1 pattern).
    assert any("scholar_search" in s and "scholar_harness" not in s for s in out), (
        "stage must import the scholar-search kit"
    )


def test_stage_3_region_has_no_direct_kit_use():
    source = Path(orch.__file__).read_text(encoding="utf-8")
    stage3 = source.split("Stage 3: Verification", 1)[1]
    stage3 = stage3.split("Stage 4:", 1)[0]
    # No direct construction or bridge/quarantine/audit logic in the region.
    assert "DocumentVerifier(" not in stage3
    assert "process_batch" not in stage3
    assert "build_doi_bridge" not in stage3
    assert "VERIFICATION_IDENTITY_" not in stage3
    assert "verified_unresolved" not in stage3
    assert "asdict" not in stage3
    assert 'f"SCI-' not in stage3 and "f'SCI-" not in stage3
    assert "run_verification" in stage3


def test_no_broad_compat_layer():
    # Only the narrow re-export remains; the bridge vocabulary lives in the stage.
    assert not hasattr(orch, "build_doi_bridge")
    assert not hasattr(orch, "VERIFICATION_IDENTITY_MISSING_DOI")
    assert not hasattr(orch, "VERIFICATION_IDENTITY_BRIDGE_MISS")
    assert not hasattr(orch, "VERIFICATION_IDENTITY_AMBIGUOUS_DOI")


# ---------------------------------------------------------------------------
# HCM4E-11 exceptions propagate (no client resource; no fabricated state)
# ---------------------------------------------------------------------------


def test_verifier_exception_propagates_without_files_or_audit(tmp_path, monkeypatch):
    class _FailingVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            raise RuntimeError("verify boom")

    monkeypatch.setattr(ver_mod, "DocumentVerifier", _FailingVerifier)
    ws = tmp_path / "ws"
    lit = ws / "literature"

    with pytest.raises(RuntimeError, match="verify boom"):
        _run_stage(_deduped_docs(_make_two_distinct_docs()), lit, ws)

    # Failure publishes nothing: no fabricated verified/quarantine/audit.
    assert not (lit / "verified.json").exists()
    assert not (lit / QUARANTINE_FILENAME).exists()
    assert _verification_rows(ws) == []
    assert not (ws / "audit" / "journal.jsonl").exists()


def test_orchestrator_verifier_failure_propagates_without_success(
    tmp_path, monkeypatch
):
    class _FailingVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            raise RuntimeError("verify boom")

    class _FakeEngine:
        def __init__(self, providers=None):
            pass

        async def search_all(self, query, dedup=False):
            return _make_two_distinct_docs()

        async def close(self):
            pass

    monkeypatch.setattr(orch, "DocumentVerifier", _FailingVerifier)
    monkeypatch.setattr(orch, "SearchEngine", _FakeEngine)
    _install_passthrough_hydration(monkeypatch)
    _stub_screening_prepare(monkeypatch)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)

    with pytest.raises(RuntimeError, match="verify boom"):
        asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert not (ws / "literature" / "verified.json").exists()
    assert _verification_rows(ws) == []


def test_audit_exception_propagates_after_files_written(tmp_path, monkeypatch):
    """NEG: audit failure propagates; verified/quarantine files remain."""

    class _PassthroughVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return list(docs), []

    monkeypatch.setattr(ver_mod, "DocumentVerifier", _PassthroughVerifier)

    def _raising_audit(*args, **kwargs):
        raise RuntimeError("audit boom")

    monkeypatch.setattr(ver_mod, "append_legacy_event", _raising_audit)
    ws = tmp_path / "ws"
    lit = ws / "literature"

    with pytest.raises(RuntimeError, match="audit boom"):
        _run_stage(_deduped_docs(_make_two_distinct_docs()), lit, ws)

    # Files were written before the audit failure escaped; no outcome returned.
    assert (lit / "verified.json").exists()
    assert _verification_rows(ws) == []


# ---------------------------------------------------------------------------
# HCM4E-12 negatives: mint/bridge/quarantine source guards
# ---------------------------------------------------------------------------


def test_stage_source_has_no_sci_mint_and_keeps_bridge_and_quarantine():
    """NEG-01/02/03: reintroducing a mint, bypassing the bridge, or omitting
    quarantine breaks the guards below (and the policy tests above)."""
    text = Path(ver_mod.__file__).read_text(encoding="utf-8")
    # No SCI- mint formula anywhere in the stage (the Deduplicator remains the
    # only legitimate SCI- producer; the stage only preserves/restores).
    assert 'f"SCI-' not in text and "f'SCI-" not in text
    assert "SCI-{" not in text
    # Bridge vocabulary is the only restore path.
    assert "build_doi_bridge" in text
    assert "ambiguous_dois" in text
    assert "wsid_by_doi" in text
    assert VERIFICATION_IDENTITY_MISSING_DOI in text
    assert VERIFICATION_IDENTITY_BRIDGE_MISS in text
    assert VERIFICATION_IDENTITY_AMBIGUOUS_DOI in text
    # Quarantine publication + stale removal + audit are owned by the stage.
    assert QUARANTINE_FILENAME in text or "QUARANTINE_FILENAME" in text
    assert "verified_unresolved" in text
    assert "VERIFICATION_IDENTITY_RESOLVED" in text
    assert "append_legacy_event" in text


def test_orchestrator_source_has_no_verification_mint():
    """NEG-04: the orchestrator Stage-3 region cannot mint or bridge."""
    text = Path(orch.__file__).read_text(encoding="utf-8")
    assert "from scholar_search.verifier import" not in text
    assert "from .verification_identity import" not in text
    assert "from dataclasses import asdict" not in text
