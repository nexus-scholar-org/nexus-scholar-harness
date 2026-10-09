"""Focused HCM-04b tests for the neutral discovery stage.

Stage 1 (protocol-query compile -> search -> raw-result publication) lives in
``scholar_harness.pipeline.discovery``; the orchestrator delegates. Every test
is hermetic (``tmp_path`` only, faked engine, real protocol compiler) and
asserts zero behavior change: byte-identical raw files, identical provider
resolution, preserved overrides/edge cases, no audit or registry writes, and
unchanged ``mock_mode`` semantics.
"""

from __future__ import annotations

import asyncio
import inspect
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from scholar_harness import orchestrator as orch
from scholar_harness.pipeline import discovery as disc


def _write_protocol(ws: Path, slug: str = "discovery-stage-test") -> Path:
    from scholar_protocol.canonical import canonical_json
    from scholar_protocol.compiler import compile_protocol
    from scholar_protocol.intent import IntentPacket

    data = {
        "protocol_id": "discovery-stage",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": slug,
        "playbook_type": "DESIGN_SCIENCE",
        "title": "Discovery Stage Parity",
        "lead_researcher": "Test Lead",
        "unit_of_analysis": "Harness Pipelines",
        "epistemological_rationale": "Empirical Benchmark",
        "research_questions": [
            {
                "text": "What is the pipeline throughput?",
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


SEEN_QUERIES: list[tuple[object, bool]] = []
ENGINE_INSTANCES: list[object] = []


def _make_docs():
    from scholar_search.models import Document, ExternalIds

    return [
        Document(
            title="First Study",
            year=2024,
            provider="openalex",
            provider_id="W1",
            external_ids=ExternalIds(doi="10.1000/aaa"),
            abstract="First abstract.",
        ),
        Document(
            title="Second Study",
            year=2023,
            provider="crossref",
            provider_id="C2",
            external_ids=ExternalIds(doi="10.1000/bbb"),
            abstract="Second abstract.",
        ),
    ]


class _FakeEngine:
    def __init__(self, providers=None):
        self.providers = providers
        self.closed = False
        ENGINE_INSTANCES.append(self)

    async def search_all(self, query, dedup=False):
        SEEN_QUERIES.append((query, dedup))
        return list(_make_docs())

    async def close(self):
        self.closed = True


class _EmptyEngine(_FakeEngine):
    async def search_all(self, query, dedup=False):
        SEEN_QUERIES.append((query, dedup))
        return []


class _FailingEngine(_FakeEngine):
    async def search_all(self, query, dedup=False):
        SEEN_QUERIES.append((query, dedup))
        raise RuntimeError("provider boom")

    async def close(self):  # pragma: no cover - close is never reached
        self.closed = True


@pytest.fixture(autouse=True)
def _reset_captures():
    SEEN_QUERIES.clear()
    ENGINE_INSTANCES.clear()
    yield
    SEEN_QUERIES.clear()
    ENGINE_INSTANCES.clear()


def _golden_text(docs) -> str:
    return json.dumps(
        [asdict(d) if hasattr(d, "__dataclass_fields__") else d for d in docs],
        indent=2,
        default=str,
    )


def _stub_screening_prepare(monkeypatch):
    # Mirror tests/pipeline/test_orchestrator_fidelity.py: Stage 4's real
    # batch preparation refuses without an accepted corpus snapshot, which is
    # downstream of discovery and out of scope here.
    monkeypatch.setattr(
        "scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None
    )


def test_raw_files_are_byte_identical_and_match_golden(tmp_path, monkeypatch):
    monkeypatch.setattr(disc, "SearchEngine", _FakeEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    proto = _write_protocol(ws)
    lit = ws / "literature"

    outcome = asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=lit))

    assert outcome.count == 2
    assert len(outcome.documents) == 2
    raw_bytes = (lit / "raw_search.json").read_bytes()
    combined_bytes = (lit / "all_raw_search.json").read_bytes()
    assert raw_bytes == combined_bytes
    # Text-mode read reverses the platform newline translation that
    # Path.write_text applies on write (verbatim orchestrator behavior);
    # the content must equal the golden serialization exactly.
    assert (lit / "raw_search.json").read_text(encoding="utf-8") == _golden_text(
        outcome.documents
    )
    # The fake engine saw the verbatim call shape and was closed.
    assert SEEN_QUERIES and SEEN_QUERIES[-1][1] is False
    assert ENGINE_INSTANCES and ENGINE_INSTANCES[-1].closed is True


def test_orchestrator_path_matches_direct_stage_bytes(tmp_path, monkeypatch):
    # Legacy seam: the orchestrator delegates, and the stage honors the
    # orchestrator-namespace fake engine.
    monkeypatch.setattr(orch, "SearchEngine", _EmptyEngine)
    _stub_screening_prepare(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert results["stages"]["discovery"] == 0
    orch_bytes = (ws / "literature" / "raw_search.json").read_bytes()
    assert orch_bytes == (ws / "literature" / "all_raw_search.json").read_bytes()
    assert (ws / "literature" / "raw_search.json").read_text(
        encoding="utf-8"
    ) == _golden_text([])

    direct_lit = tmp_path / "direct" / "literature"
    outcome = asyncio.run(
        disc.run_discovery(
            protocol_path=ws / "protocol.json", literature_dir=direct_lit
        )
    )
    assert outcome.count == 0
    assert (direct_lit / "raw_search.json").read_bytes() == orch_bytes


def test_provider_resolution_identical_via_shim():
    assert orch._resolve_providers is disc._resolve_providers
    assert orch._PROVIDER_MAP is disc._PROVIDER_MAP

    from scholar_search.providers import OpenAlexProvider, SemanticScholarProvider

    resolved = disc._resolve_providers(["openalex", "crossref"])
    assert len(resolved) == 2
    assert isinstance(resolved[0], OpenAlexProvider)
    # Unknown names are dropped (warning, not failure).
    assert disc._resolve_providers(["openalex", "not-a-provider"]) is not None
    assert disc._resolve_providers(["not-a-provider"]) is None
    assert disc._resolve_providers([]) is None
    assert disc._resolve_providers(None) is None
    # Normalization is verbatim: case/space/dash variants resolve.
    normalized = disc._resolve_providers(["Semantic Scholar", "semantic-scholar"])
    assert len(normalized) == 2
    assert all(isinstance(p, SemanticScholarProvider) for p in normalized)
    # Existing instances pass through untouched.
    existing = OpenAlexProvider()
    mixed = disc._resolve_providers([existing, "crossref"])
    assert mixed[0] is existing


def test_max_search_results_override(tmp_path, monkeypatch):
    monkeypatch.setattr(disc, "SearchEngine", _FakeEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    proto = _write_protocol(ws)

    asyncio.run(
        disc.run_discovery(
            protocol_path=proto,
            literature_dir=ws / "lit-a",
            max_search_results=7,
        )
    )
    assert SEEN_QUERIES[-1][0].max_results == 7

    SEEN_QUERIES.clear()
    asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=ws / "lit-b"))
    from scholar_search.protocol_adapter import compile_protocol_search

    default_query, _ = compile_protocol_search(proto)
    assert SEEN_QUERIES[-1][0].max_results == default_query.max_results

    # Falsy overrides preserve the original `if max_search_results:` semantics.
    SEEN_QUERIES.clear()
    asyncio.run(
        disc.run_discovery(
            protocol_path=proto, literature_dir=ws / "lit-c", max_search_results=0
        )
    )
    assert SEEN_QUERIES[-1][0].max_results == default_query.max_results


def test_empty_results_preserve_count_and_files(tmp_path, monkeypatch):
    monkeypatch.setattr(disc, "SearchEngine", _EmptyEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    proto = _write_protocol(ws)
    lit = ws / "literature"

    outcome = asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=lit))

    assert outcome.count == 0
    assert outcome.documents == []
    assert (lit / "raw_search.json").read_text(encoding="utf-8") == _golden_text([])
    assert (lit / "all_raw_search.json").read_text(encoding="utf-8") == _golden_text([])


def test_stage_emits_no_audit_event_and_no_registry_writes(tmp_path, monkeypatch):
    monkeypatch.setattr(disc, "SearchEngine", _FakeEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    proto = _write_protocol(ws)

    asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=ws / "lit"))

    assert not (ws / "audit").exists()
    assert not (ws / "literature" / "audit").exists()
    assert list((ws).rglob("journal.jsonl")) == []
    assert list((ws).rglob("artifact_registry.json")) == []
    written = sorted(p.name for p in (ws / "lit").iterdir())
    assert written == ["all_raw_search.json", "raw_search.json"]


def test_stage_1_region_has_no_direct_kit_use():
    source = Path(orch.__file__).read_text(encoding="utf-8")
    stage1 = source.split("Stage 1: Protocol Query Compilation & Search", 1)[1]
    stage1 = stage1.split("Stage 2:", 1)[0]
    assert "SearchEngine" not in stage1
    assert "compile_protocol_search" not in stage1
    assert "run_discovery" in stage1


def test_missing_protocol_raises_before_engine_or_files(tmp_path, monkeypatch):
    constructed: list[bool] = []

    class _SpyEngine(_FakeEngine):
        def __init__(self, providers=None):
            constructed.append(True)
            super().__init__(providers)

    monkeypatch.setattr(disc, "SearchEngine", _SpyEngine)
    lit = tmp_path / "lit"

    with pytest.raises(FileNotFoundError):
        asyncio.run(
            disc.run_discovery(
                protocol_path=tmp_path / "no-such-protocol.json",
                literature_dir=lit,
            )
        )

    assert constructed == []
    assert not lit.exists()


def test_provider_failure_propagates_without_empty_success(tmp_path, monkeypatch):
    monkeypatch.setattr(disc, "SearchEngine", _FailingEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    proto = _write_protocol(ws)
    lit = ws / "literature"

    with pytest.raises(RuntimeError, match="provider boom"):
        asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=lit))

    # Failure closes over nothing: no fabricated raw files survive.
    assert not (lit / "raw_search.json").exists()
    assert not (lit / "all_raw_search.json").exists()
    assert ENGINE_INSTANCES and ENGINE_INSTANCES[-1].closed is False


def test_invalid_protocol_fails_without_fabricated_files(tmp_path, monkeypatch):
    monkeypatch.setattr(disc, "SearchEngine", _FakeEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    bad = ws / "protocol.json"
    bad.write_text("{ not valid json", encoding="utf-8")
    lit = ws / "literature"

    with pytest.raises(Exception):
        asyncio.run(disc.run_discovery(protocol_path=bad, literature_dir=lit))

    assert not (lit / "raw_search.json").exists()
    assert not (lit / "all_raw_search.json").exists()


def test_mock_mode_signature_and_behavior_unchanged(tmp_path, monkeypatch):
    sig = inspect.signature(orch.ResearchOrchestrator.run_pipeline_async)
    assert "mock_mode" in sig.parameters
    assert sig.parameters["mock_mode"].default is False

    # mock_mode is accepted but unused: identical outcomes either way.
    monkeypatch.setattr(orch, "SearchEngine", _EmptyEngine)
    _stub_screening_prepare(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)

    plain = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())
    assert plain["stages"]["discovery"] == 0
    first = (ws / "literature" / "raw_search.json").read_bytes()

    flagged = asyncio.run(
        orch.ResearchOrchestrator(ws).run_pipeline_async(mock_mode=True)
    )
    assert flagged["stages"]["discovery"] == 0
    assert (ws / "literature" / "raw_search.json").read_bytes() == first
