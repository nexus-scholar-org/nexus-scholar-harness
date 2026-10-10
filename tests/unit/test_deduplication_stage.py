"""Focused HCM-04c tests for the neutral deduplication stage.

Stage 2 (2-tier dedup over ALL discovered docs -> deduped publication) lives
in ``scholar_harness.pipeline.deduplication``; the orchestrator delegates.
Every test is hermetic (``tmp_path`` only, real ``Deduplicator`` unless a
fake is explicitly patched, real protocol compiler where needed) and asserts
zero behavior change: byte-identical deduped files, identical counts,
preserved ALL-docs semantics, no audit or registry writes, and unchanged
hydration binding.

Mapping to the HCM-04c packet:

- HCM4C-01 duplicate-pair count
- HCM4C-02 empty input incl. current JSON behavior
- HCM4C-03 subset-input mutation detected (ALL docs, never a subset)
- HCM4C-04 count-calc mutation detected (unique + removed == len(in))
- HCM4C-05 serialization/filename mutation detected (deduped.json, indent=2)
- HCM4C-06 audit-write mutation detected (no journal/registry)
- HCM4C-07 console-import mutation detected (no console transport)
- HCM4C-08 orchestrator<->stage byte+outcome parity
- HCM4C-09 kit-raise propagates with no fabricated files/success
- HCM4C-10 shim + legacy orchestrator-namespace seam preserved

Carry-forward note: the fidelity stubs still patch
``scholar_harness.orchestrator.Deduplicator`` (legacy seam). A later packet
should migrate them to patch
``scholar_harness.pipeline.deduplication.Deduplicator`` directly and drop the
orchestrator fallback in ``_deduplicator_class``.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from scholar_harness import orchestrator as orch
from scholar_harness.pipeline import deduplication as dedup


def _make_duplicate_docs():
    """3 docs in -> 2 unique out (first two share a DOI). All have abstracts."""
    from scholar_search.models import Author, Document, ExternalIds

    return [
        Document(
            title="Grounded Code Generation with LLMs",
            year=2023,
            provider="openalex",
            provider_id="W4001",
            external_ids=ExternalIds(doi="10.1000/dup"),
            authors=[Author(family_name="Chen", given_name="Alex")],
            abstract="First abstract with content.",
        ),
        Document(
            title="Grounded Code Generation with LLMs.",
            year=2023,
            provider="arxiv",
            provider_id="2308.01234",
            external_ids=ExternalIds(doi="10.1000/dup", arxiv_id="2308.01234"),
            authors=[Author(family_name="Chen", given_name="A.")],
            abstract="Second abstract, longer content for scoring.",
        ),
        Document(
            title="Evaluating Python Code Synthesis",
            year=2024,
            provider="crossref",
            provider_id="10.1145/3002",
            external_ids=ExternalIds(doi="10.1145/3002"),
            authors=[Author(family_name="Smith", given_name="Jane")],
            abstract="Distinct study abstract.",
        ),
    ]


def _make_distinct_docs():
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


def _golden_text(docs) -> str:
    return json.dumps(
        [asdict(d) if hasattr(d, "__dataclass_fields__") else d for d in docs],
        indent=2,
        default=str,
    )


def _write_protocol(ws: Path, slug: str = "dedup-stage-test") -> Path:
    from scholar_protocol.canonical import canonical_json
    from scholar_protocol.compiler import compile_protocol
    from scholar_protocol.intent import IntentPacket

    data = {
        "protocol_id": "dedup-stage",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": slug,
        "playbook_type": "DESIGN_SCIENCE",
        "title": "Dedup Stage Parity",
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


def _stub_screening_prepare(monkeypatch):
    monkeypatch.setattr(
        "scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None
    )


# ---------------------------------------------------------------------------
# HCM4C-01 duplicate-pair count
# ---------------------------------------------------------------------------


def test_duplicate_pair_collapses_to_single_representative(tmp_path):
    docs = _make_duplicate_docs()
    outcome = dedup.run_deduplication(
        discovered_documents=docs, literature_dir=tmp_path / "lit"
    )

    assert outcome.unique == 2
    assert outcome.duplicates_removed == 1
    assert len(outcome.representatives) == 2
    # Duplicate DOI merged: representative keeps the DOI and both sources.
    merged = next(d for d in outcome.representatives if "Grounded" in d.title)
    assert merged.external_ids.doi == "10.1000/dup"
    assert len(merged.sources) == 2
    # Workspace IDs assigned here (SCI-XXXXXX).
    assert merged.workspace_id is not None and merged.workspace_id.startswith("SCI-")


def test_distinct_documents_preserved(tmp_path):
    docs = _make_distinct_docs()
    outcome = dedup.run_deduplication(
        discovered_documents=docs, literature_dir=tmp_path / "lit"
    )

    assert outcome.unique == 2
    assert outcome.duplicates_removed == 0
    assert len(outcome.representatives) == 2


# ---------------------------------------------------------------------------
# HCM4C-02 empty input incl. current JSON behavior
# ---------------------------------------------------------------------------


def test_empty_input_preserves_count_and_file(tmp_path):
    lit = tmp_path / "lit"
    outcome = dedup.run_deduplication(discovered_documents=[], literature_dir=lit)

    assert outcome.unique == 0
    assert outcome.duplicates_removed == 0
    assert outcome.representatives == []
    # Current JSON behavior: empty list serializes to "[]".
    assert (lit / "deduped.json").read_text(encoding="utf-8") == _golden_text([])
    assert (lit / "deduped.json").read_text(encoding="utf-8") == "[]"


# ---------------------------------------------------------------------------
# HCM4C-05 serialization/filename mutation detected
# ---------------------------------------------------------------------------


def test_deduped_file_is_byte_identical_and_matches_golden(tmp_path):
    docs = _make_duplicate_docs()
    lit = tmp_path / "lit"

    outcome = dedup.run_deduplication(discovered_documents=docs, literature_dir=lit)

    # Text-mode read equals the golden serialization exactly.
    assert (lit / "deduped.json").read_text(encoding="utf-8") == _golden_text(
        outcome.representatives
    )
    # Exactly one file, exact filename.
    written = sorted(p.name for p in lit.iterdir())
    assert written == ["deduped.json"]
    # Typed outcome aliases agree.
    assert outcome.documents is outcome.representatives
    assert outcome.unique_docs is outcome.representatives


# ---------------------------------------------------------------------------
# HCM4C-03 subset-input mutation detected
# ---------------------------------------------------------------------------


def test_all_documents_reach_deduplicator_not_subset(tmp_path, monkeypatch):
    seen: list[list] = []

    from scholar_search.dedup import Deduplicator as RealDedup

    class _RecordingDedup(RealDedup):
        def deduplicate(self, documents):
            seen.append(list(documents))
            return super().deduplicate(documents)

    monkeypatch.setattr(dedup, "Deduplicator", _RecordingDedup)
    docs = _make_duplicate_docs()
    lit = tmp_path / "lit"

    outcome = dedup.run_deduplication(discovered_documents=docs, literature_dir=lit)

    assert len(seen) == 1
    # The stage passed ALL discovered docs, never a subset/slice.
    assert len(seen[0]) == 3
    assert seen[0] == docs
    assert outcome.unique == 2


# ---------------------------------------------------------------------------
# HCM4C-04 count-calc mutation detected
# ---------------------------------------------------------------------------


def test_counts_match_len_formula(tmp_path):
    for docs in (_make_duplicate_docs(), _make_distinct_docs(), []):
        lit = tmp_path / f"lit-{len(docs)}-{id(docs) % 100000}"
        outcome = dedup.run_deduplication(
            discovered_documents=list(docs), literature_dir=lit
        )
        assert outcome.unique == len(outcome.representatives)
        assert outcome.duplicates_removed == len(docs) - len(outcome.representatives)
        assert outcome.unique + outcome.duplicates_removed == len(docs)


# ---------------------------------------------------------------------------
# HCM4C-06 audit-write mutation detected
# ---------------------------------------------------------------------------


def test_stage_emits_no_audit_event_and_no_registry_writes(tmp_path):
    docs = _make_duplicate_docs()
    ws = tmp_path / "ws"
    lit = ws / "lit"

    dedup.run_deduplication(discovered_documents=docs, literature_dir=lit)

    assert not (ws / "audit").exists()
    assert not (lit / "audit").exists()
    assert list(ws.rglob("journal.jsonl")) == []
    assert list(ws.rglob("artifact_registry.json")) == []
    written = sorted(p.name for p in lit.iterdir())
    assert written == ["deduped.json"]


# ---------------------------------------------------------------------------
# HCM4C-07 console-import mutation detected
# ---------------------------------------------------------------------------


def test_stage_has_no_console_transport_import():
    # Repair-1 pattern: import-statement guard (prose may mention "console").
    import re

    text = Path(dedup.__file__).read_text(encoding="utf-8")
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


def test_stage_2_region_has_no_direct_kit_use():
    source = Path(orch.__file__).read_text(encoding="utf-8")
    stage2 = source.split("Stage 2: 2-Tier Deduplication", 1)[1]
    stage2 = stage2.split("Stage 2.5:", 1)[0]
    # No direct construction or direct deduplicate call in the region.
    assert "Deduplicator()" not in stage2
    assert "deduplicator.deduplicate" not in stage2.lower()
    assert "run_deduplication" in stage2


# ---------------------------------------------------------------------------
# HCM4C-10 shim + legacy seam
# ---------------------------------------------------------------------------


def test_shim_preserves_deduplicator_identity():
    assert orch.Deduplicator is dedup.Deduplicator
    assert orch.run_deduplication is dedup.run_deduplication
    assert orch.DeduplicationOutcome is dedup.DeduplicationOutcome


def test_legacy_orchestrator_seam_honored(tmp_path, monkeypatch):
    """Transitional seam: an orchestrator-namespace fake is honored.

    Carry-forward: migrate fidelity stubs to patch
    ``pipeline.deduplication.Deduplicator`` directly in a later packet.
    """

    class _EmptyDedup:
        def deduplicate(self, docs):
            return []

    monkeypatch.setattr(orch, "Deduplicator", _EmptyDedup)
    docs = _make_duplicate_docs()
    outcome = dedup.run_deduplication(
        discovered_documents=docs, literature_dir=tmp_path / "lit"
    )
    assert outcome.unique == 0
    assert outcome.duplicates_removed == 3

    # Direct-module patch also works (future canonical seam).
    monkeypatch.setattr(dedup, "Deduplicator", _EmptyDedup)
    outcome2 = dedup.run_deduplication(
        discovered_documents=docs, literature_dir=tmp_path / "lit2"
    )
    assert outcome2.unique == 0


# ---------------------------------------------------------------------------
# HCM4C-08 orchestrator<->stage byte+outcome parity
# ---------------------------------------------------------------------------


def test_orchestrator_path_matches_direct_stage_bytes(tmp_path, monkeypatch):
    from scholar_search import enrichment as _enrich
    from scholar_search import http_client as _http

    class _FakeEngine:
        def __init__(self, providers=None):
            self.providers = providers

        async def search_all(self, query, dedup=False):
            assert dedup is False
            return _make_duplicate_docs()

        async def close(self):
            pass

    class _PassthroughVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return list(docs), []

    class _PassthroughHydrator:
        def __init__(self, client):
            pass

        async def hydrate_missing_abstracts(self, docs, batch_size=50):
            return list(docs), {"attempted": 0, "hydrated": 0, "failed": 0}

    class _DummyClient:
        def __init__(self, *a, **k):
            pass

        async def close(self):
            pass

    monkeypatch.setattr(orch, "SearchEngine", _FakeEngine)
    monkeypatch.setattr(orch, "DocumentVerifier", _PassthroughVerifier)
    monkeypatch.setattr(_enrich, "AbstractHydrator", _PassthroughHydrator)
    monkeypatch.setattr(_http, "AcademicHttpClient", _DummyClient)
    _stub_screening_prepare(monkeypatch)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    # Orchestrator mapping preserved (unique + duplicates_removed).
    assert results["stages"]["deduplication"]["unique"] == 2
    assert results["stages"]["deduplication"]["duplicates_removed"] == 1
    orch_bytes = (ws / "literature" / "deduped.json").read_bytes()
    assert (ws / "literature" / "deduped.json").read_text(
        encoding="utf-8"
    ) == _golden_text(
        json.loads((ws / "literature" / "deduped.json").read_text(encoding="utf-8"))
    )

    # Direct stage with equivalent fresh docs is byte-identical.
    direct_lit = tmp_path / "direct" / "literature"
    direct_outcome = dedup.run_deduplication(
        discovered_documents=_make_duplicate_docs(), literature_dir=direct_lit
    )
    assert direct_outcome.unique == 2
    assert direct_outcome.duplicates_removed == 1
    assert (direct_lit / "deduped.json").read_bytes() == orch_bytes


def test_orchestrator_empty_matches_direct_empty_bytes(tmp_path, monkeypatch):
    from scholar_search import enrichment as _enrich
    from scholar_search import http_client as _http

    class _EmptyEngine:
        def __init__(self, providers=None):
            pass

        async def search_all(self, query, dedup=False):
            return []

        async def close(self):
            pass

    class _EmptyVerifier:
        async def process_batch(self, docs, verify=True, enrich=True):
            return [], []

    class _PassthroughHydrator:
        def __init__(self, client):
            pass

        async def hydrate_missing_abstracts(self, docs, batch_size=50):
            return list(docs), {"attempted": 0, "hydrated": 0, "failed": 0}

    class _DummyClient:
        def __init__(self, *a, **k):
            pass

        async def close(self):
            pass

    monkeypatch.setattr(orch, "SearchEngine", _EmptyEngine)
    monkeypatch.setattr(orch, "DocumentVerifier", _EmptyVerifier)
    monkeypatch.setattr(_enrich, "AbstractHydrator", _PassthroughHydrator)
    monkeypatch.setattr(_http, "AcademicHttpClient", _DummyClient)
    _stub_screening_prepare(monkeypatch)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert results["stages"]["deduplication"] == {
        "unique": 0,
        "duplicates_removed": 0,
    }
    orch_bytes = (ws / "literature" / "deduped.json").read_bytes()
    assert (ws / "literature" / "deduped.json").read_text(
        encoding="utf-8"
    ) == _golden_text([])

    direct_lit = tmp_path / "direct" / "literature"
    direct_outcome = dedup.run_deduplication(
        discovered_documents=[], literature_dir=direct_lit
    )
    assert direct_outcome.unique == 0
    assert (direct_lit / "deduped.json").read_bytes() == orch_bytes


# ---------------------------------------------------------------------------
# HCM4C-09 kit-raise propagates with no fabricated files/success
# ---------------------------------------------------------------------------


def test_kit_failure_propagates_without_fabricated_files(tmp_path, monkeypatch):
    class _FailingDedup:
        def deduplicate(self, docs):
            raise RuntimeError("dedup boom")

    monkeypatch.setattr(dedup, "Deduplicator", _FailingDedup)
    lit = tmp_path / "lit"

    with pytest.raises(RuntimeError, match="dedup boom"):
        dedup.run_deduplication(
            discovered_documents=_make_duplicate_docs(), literature_dir=lit
        )

    # Failure publishes nothing: no fabricated deduped file.
    assert not (lit / "deduped.json").exists()


def test_orchestrator_kit_failure_propagates_without_success(tmp_path, monkeypatch):
    class _FailingDedup:
        def deduplicate(self, docs):
            raise RuntimeError("dedup boom")

    class _FakeEngine:
        def __init__(self, providers=None):
            pass

        async def search_all(self, query, dedup=False):
            return _make_duplicate_docs()

        async def close(self):
            pass

    monkeypatch.setattr(orch, "SearchEngine", _FakeEngine)
    monkeypatch.setattr(orch, "Deduplicator", _FailingDedup)
    _stub_screening_prepare(monkeypatch)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)

    with pytest.raises(RuntimeError, match="dedup boom"):
        asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert not (ws / "literature" / "deduped.json").exists()
