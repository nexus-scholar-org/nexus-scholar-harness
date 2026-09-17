"""Hermetic fidelity tests for the orchestrator Stages 5-9 refactor.

The pipeline's discovery/dedup/verification stages hit the network, so every
kit interaction is monkeypatched in the orchestrator module namespace.  What is
verified offline is the *orchestration* contract fixed under matrix finding #9:

- the run pauses at the PRISMA agent-in-the-loop handoff (PENDING_AGENT_REVIEW,
  stages 5-9 SKIPPED) instead of reporting SUCCESS on empty/fabricated output;
- Stage 5 never invents Methodology/Results/Limitations prose — it writes
  metadata-frontmatter documents derived from real records (or PyMuPDF output);
- Stages 7/9 receive a real ScholarRetriever bound to the same Chroma db (no
  `indexer.retriever`); Stage 8 drives a real OpenAlex HTTP client.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import networkx as nx

from scholar_harness import orchestrator as orch


def _write_protocol(ws: Path, slug: str = "fidelity-test-workspace") -> Path:
    from scholar_protocol.canonical import canonical_json
    from scholar_protocol.compiler import compile_protocol
    from scholar_protocol.intent import IntentPacket

    data = {
        "protocol_id": "fidelity-test",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": slug,
        "playbook_type": "DESIGN_SCIENCE",
        "title": "Orchestrator Fidelity",
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
            {"criterion": "Non-English", "reason_category": "LANGUAGE", "maps_to_rqs": ["RQ1"]}
        ],
        "matrix_dimensions": [
            {"id": "throughput", "name": "Throughput", "description": "Operations per second"}
        ],
    }
    intent = IntentPacket.model_validate(data)
    proto = json.loads(canonical_json(compile_protocol(intent)).decode("utf-8"))
    p = ws / "protocol.json"
    p.write_text(json.dumps(proto), encoding="utf-8")
    return p


class _FakeEngine:
    def __init__(self, providers=None):
        self.providers = providers or []

    async def search_all(self, query, dedup=False):
        return []

    async def close(self):
        pass


class _FakeDedup:
    def deduplicate(self, docs):
        return []


class _FakeVerifier:
    async def process_batch(self, docs, verify=True, enrich=True):
        return [], []


class _FakeIndexer:
    def __init__(
        self, db_path=".", collection_name="scholar_docs", embedder_kwargs=None, **kw
    ):
        self.collection_name = collection_name
        self.embedder_kwargs = embedder_kwargs or {"provider": "sentence-transformers"}

    def index_directory(self, docs_dir, workspace_id=None, **kw):
        return {"indexed": 0}


RETRIEVER_CALLS: list[dict] = []


class _RecorderRetriever:
    def __init__(self, **kwargs):
        RETRIEVER_CALLS.append(kwargs)
        self.kw = kwargs


class _FakeMatrix:
    def __init__(self, protocol=None, retriever=None, **kw):
        self.retriever = retriever
        SEEN_MATRIX_RETRIEVERS.append(retriever)

    def extract_all(self, output_dir):
        out = Path(output_dir)
        return [], out / "synthesis_matrix.csv", out / "synthesis_matrix.json"


class _FakeSynth:
    def __init__(self, retriever=None, **kw):
        self.retriever = retriever
        SEEN_SYNTH_RETRIEVERS.append(retriever)

    def synthesize(self, **kw):
        return SimpleNamespace(
            synthesis_markdown="# Synthesis\n",
            verified_claims_count=0,
            claims=[],
            entailment_rate=0.0,
        )


SEEN_MATRIX_RETRIEVERS: list[object] = []
SEEN_SYNTH_RETRIEVERS: list[object] = []


class _FakeGraph:
    def __init__(self, client):
        self.client = client

    async def build_graph(self, dois):
        G = nx.DiGraph()
        for d in dois:
            G.add_node(d, label=d)
        return G

    @staticmethod
    def compute_pagerank(G):
        ranks = {n: 1.0 / max(len(G), 1) for n in G.nodes}
        nx.set_node_attributes(G, ranks, "pagerank")
        return ranks

    def export_json(self, G, path: Path):
        path.write_text(
            json.dumps({"nodes": list(G.nodes), "links": list(G.edges)}), encoding="utf-8"
        )


class _FakeVis:
    def __init__(self, html_path):
        self.html_path = html_path

    def generate_html(self, G):
        Path(self.html_path).write_text("<html></html>", encoding="utf-8")


def _stub_kit_engines(monkeypatch):
    monkeypatch.setattr(orch, "SearchEngine", _FakeEngine)
    monkeypatch.setattr(orch, "Deduplicator", _FakeDedup)
    monkeypatch.setattr(orch, "DocumentVerifier", _FakeVerifier)
    monkeypatch.setattr(orch, "ScholarIndexer", _FakeIndexer)
    monkeypatch.setattr(orch, "ScholarRetriever", _RecorderRetriever)
    monkeypatch.setattr(orch, "MatrixExtractor", _FakeMatrix)
    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _FakeSynth)
    monkeypatch.setattr(orch, "CitationGraphBuilder", _FakeGraph)
    monkeypatch.setattr(orch, "GraphVisualizer", _FakeVis)
    monkeypatch.setattr("scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None)
    return orch


def _run(ws: Path, **kw) -> dict:
    return asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async(**kw))


# ---------------------------------------------------------------------------
# Gating: no literature/included.json -> PENDING_AGENT_REVIEW, never fabricate
# ---------------------------------------------------------------------------


def test_pipeline_pauses_for_collect_and_skips_stages_5_9(tmp_path, monkeypatch):
    _stub_kit_engines(monkeypatch)
    ws = tmp_path
    _write_protocol(ws)

    results = _run(ws)

    assert results["status"] == "PENDING_AGENT_REVIEW"
    for stage in ("extraction", "indexing", "matrix", "graph", "synthesis"):
        assert results["stages"][stage]["status"] == "SKIPPED"
    assert not list((ws / "extracted").glob("*.md")), "no extraction may occur before collect"
    assert not (ws / "synthesis" / "literature_review.md").exists()

    journal = (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8")
    assert "PIPELINE_RUN_PAUSED_FOR_SCREENING" in journal


# ---------------------------------------------------------------------------
# After collect: real extraction (metadata frontmatter), no invented prose
# ---------------------------------------------------------------------------


def test_pipeline_after_collect_writes_metadata_extraction_not_placeholder(tmp_path, monkeypatch):
    _stub_kit_engines(monkeypatch)
    ws = tmp_path
    _write_protocol(ws)

    (ws / "literature").mkdir(parents=True, exist_ok=True)
    (ws / "literature" / "included.json").write_text(
        json.dumps(
            [
                {
                    "workspace_id": "SCI-000001",
                    "title": "Real Study Title",
                    "doi": None,
                    "external_ids": {},
                    "abstract": "Empirically measured latency under load.",
                    "authors": [{"family_name": "Doe", "given_name": "Jane"}],
                    "year": 2024,
                }
            ]
        ),
        encoding="utf-8",
    )

    results = _run(ws)

    assert results["status"] == "SUCCESS"
    assert results["stages"]["extraction"]["status"] == "DONE"

    md = (ws / "extracted" / "SCI-000001.md")
    assert md.is_file()
    text = md.read_text(encoding="utf-8")
    assert 'extraction_engine: "metadata"' in text
    assert "Empirically measured latency under load." in text
    assert "Methodology" not in text.replace("## Abstract", "")
    assert "Evaluated using standard benchmarks and controlled baseline comparisons." not in text


# ---------------------------------------------------------------------------
# Stages 7-9 wiring: real retriever bound to the chroma db; real graph client
# ---------------------------------------------------------------------------


def test_stages_7_9_bind_retriever_and_8_uses_real_client(tmp_path, monkeypatch):
    _stub_kit_engines(monkeypatch)
    RETRIEVER_CALLS.clear()
    SEEN_MATRIX_RETRIEVERS.clear()
    SEEN_SYNTH_RETRIEVERS.clear()

    ws = tmp_path
    _write_protocol(ws)

    (ws / "literature").mkdir(parents=True, exist_ok=True)
    (ws / "literature" / "included.json").write_text(
        json.dumps(
            [
                {
                    "workspace_id": "SCI-000001",
                    "title": "Graph Study",
                    "external_ids": {"doi": "10.1000/zzz"},
                    "abstract": "Abstract.",
                    "authors": [],
                    "year": 2024,
                }
            ]
        ),
        encoding="utf-8",
    )

    results = _run(ws)

    assert results["stages"]["extraction"]["status"] == "DONE"
    assert results["stages"]["graph_nodes"]["status"] == "DONE"
    assert (ws / "literature" / "knowledge_graph.json").is_file()
    assert (ws / "literature" / "knowledge_graph.html").is_file()

    assert any(call.get("collection_name") == "scholar_docs" for call in RETRIEVER_CALLS)
    assert any(str(call.get("db_path") or "").endswith("chroma_db") for call in RETRIEVER_CALLS)
    assert SEEN_MATRIX_RETRIEVERS and SEEN_SYNTH_RETRIEVERS
    assert SEEN_MATRIX_RETRIEVERS[-1] is SEEN_SYNTH_RETRIEVERS[-1]


# ---------------------------------------------------------------------------
# Provider resolution map (Stage 1, D1) and PDF/slug helpers
# ---------------------------------------------------------------------------


def test_provider_resolution_resolves_names_to_instances():
    from scholar_search.providers import OpenAlexProvider

    resolved = orch._resolve_providers(["openalex", "crossref"])
    assert len(resolved) == 2
    assert isinstance(resolved[0], OpenAlexProvider)
    assert orch._resolve_providers(["openalex", "not-a-provider"])  # unknown names dropped
    assert orch._resolve_providers([]) is None


def test_study_slug_and_pdf_helpers(tmp_path):
    doc = {"workspace_id": "SCI-000009", "external_ids": {"doi": "10.1/aa/bb"}}
    assert orch._study_doi(doc) == "10.1/aa/bb"
    assert orch._study_slug(doc) == "SCI-000009"
    assert orch._study_slug({"external_ids": {}, "doi": "10.1/aa"}) == "10.1_aa"

    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    hit = pdf_dir / "SCI-000009.pdf"
    hit.write_bytes(b"%PDF-1.4")
    assert orch._study_pdf(pdf_dir, doc) == hit
    assert orch._study_pdf(pdf_dir, {"workspace_id": "SCI-000999", "doi": "x"}) is None