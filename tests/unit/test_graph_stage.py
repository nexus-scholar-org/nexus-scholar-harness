"""Focused HCM-04j tests for the neutral graph stage.

Stage 8 (citation knowledge graph and PageRank over included studies) lives
in ``scholar_harness.pipeline.graph``; the orchestrator delegates and maps
the outcome identically. Every test is hermetic (``tmp_path`` only, no
network; the builder/visualizer are faked, never a live OpenAlex client;
real ``nx.DiGraph`` seeding is offline-fine) and asserts zero behavior
change: verbatim client construction, verbatim DOI collection via the
canonical ``_study_doi``, empty-DOI seeding, byte-identical
``literature/`` publication, identical results mapping, no audit or
registry writes, identical client lifecycle (per call, no close -- the
base never closed the graph client), and identical error propagation.

Mapping to the HCM-04j packet (A1-6/B7-12/C13-16):

- HCM4J-01 shim identity (``orch.X is stage.X`` for all four names)
- HCM4J-02 construction parity (client name/rate_limit + positional
  builder arg + DOI filtering + awaited build_graph + class-level
  pagerank + export/visualizer shapes + no close)
- HCM4J-03 results mapping identical (DONE + nodes/edges)
- HCM4J-04 no audit or registry from the stage
- HCM4J-05 empty-DOI seeding (empty graph, truthful 0/0, files written,
  build_graph never called)
- HCM4J-06 ``_study_doi`` canonical home (imported, never duplicated)
- HCM4J-07 move-not-duplicate (Stage 8 region has no inline kit logic)
- HCM4J-08 minimal signature + outcome names + transport guard
- HCM4J-09 byte parity probe (orch vs direct stage json/html bytes agree)
- HCM4J-10 error propagation (kit raise propagates, no fabricated DONE)

Negatives (each tmp_path-only, byte-identical restored):

- NEG-01 invalid-row routing (DOI-less rows filtered, never reach build_graph)
- NEG-02 builder-arg change (client kwargs must stay name/rate_limit exact)
- NEG-03 output path/serialization/order change (paths + bytes + node order)
- NEG-04 failure-into-success (raise is never mapped to DONE/0)
- NEG-05 seam bypass (orchestrator-namespace patches take effect)
- NEG-06 byte-identical probe restore (direct stage restores orch bytes)

Carry-forward debt TD-HCM-TEST-SEAMS x3 untouched
(``SearchEngine`` / ``Deduplicator`` / ``DocumentVerifier`` shims stay);
this packet adds two NARROW seams only (``CitationGraphBuilder`` /
``GraphVisualizer`` via ``orchestrator.__dict__`` honoring, HCM-04i
matrix precedent). networkx is imported directly (no ``orch.nx`` patch
exists anywhere); ``AcademicHttpClient`` is imported at the stage top
(hydration precedent; fakes take the client opaquely). No broad layer, no
other seams. TD-E3-CURRENTNESS-01 and the MCP docs failure stay
base-proven and untouched.
"""

from __future__ import annotations

import asyncio
import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import networkx as nx
import pytest

from scholar_harness import orchestrator as orch
from scholar_harness.pipeline import extraction as ext_mod
from scholar_harness.pipeline import graph as graph_mod

FIXTURE_WORKSPACE_ID = "WSP-" + "0" * 32


def _record_workspace_identity(ws: Path, project_id: str) -> None:
    (ws / "project.json").write_text(
        json.dumps(
            {"project_id": project_id, "registered_workspace_id": FIXTURE_WORKSPACE_ID}
        ),
        encoding="utf-8",
    )


def _write_protocol(ws: Path, slug: str = "graph-stage-test") -> Path:
    from scholar_protocol.canonical import canonical_json
    from scholar_protocol.compiler import compile_protocol
    from scholar_protocol.intent import IntentPacket

    data = {
        "protocol_id": "graph-stage",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": slug,
        "playbook_type": "DESIGN_SCIENCE",
        "title": "Graph Stage Parity",
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


def _journal_rows(ws: Path) -> list[dict]:
    p = ws / "audit" / "journal.jsonl"
    if not p.exists():
        return []
    return [
        json.loads(line)
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


SEEN_CLIENTS: list[object] = []
SEEN_DOIS: list[list[str]] = []
SEEN_HTML_PATHS: list[object] = []
SEEN_JSON_PATHS: list[object] = []
BUILD_CALLS: list[list[str]] = []


class _FakeGraph:
    """Fake builder mirroring the fidelity stubs (client-opaque)."""

    def __init__(self, client):
        SEEN_CLIENTS.append(client)
        self.client = client

    async def build_graph(self, dois):
        BUILD_CALLS.append(list(dois))
        SEEN_DOIS.append(list(dois))
        G = nx.DiGraph()
        for d in dois:
            G.add_node(d, label=d)
        return G

    @staticmethod
    def compute_pagerank(G):
        ranks = {n: 1.0 / max(len(G), 1) for n in G.nodes}
        nx.set_node_attributes(G, ranks, "pagerank")
        return ranks

    def export_json(self, G, path):
        SEEN_JSON_PATHS.append(Path(path))
        # Mirror the kit: export_json assures the parent directory.
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(
            json.dumps({"nodes": list(G.nodes), "links": list(G.edges)}),
            encoding="utf-8",
        )


class _FakeVis:
    def __init__(self, html_path):
        SEEN_HTML_PATHS.append(html_path)
        self.html_path = html_path

    def generate_html(self, G):
        # Mirror the kit: generate_html assures the parent directory.
        Path(self.html_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.html_path).write_text("<html></html>", encoding="utf-8")


def _clear_seen():
    SEEN_CLIENTS.clear()
    SEEN_DOIS.clear()
    SEEN_HTML_PATHS.clear()
    SEEN_JSON_PATHS.clear()
    BUILD_CALLS.clear()


# ---------------------------------------------------------------------------
# HCM4J-01 shim identity
# ---------------------------------------------------------------------------


def test_shim_identity_all_four_names():
    """HCM4J-01: orchestrator names ARE the stage objects (move, not copy)."""
    assert orch.CitationGraphBuilder is graph_mod.CitationGraphBuilder
    assert orch.GraphVisualizer is graph_mod.GraphVisualizer
    assert orch.run_graph is graph_mod.run_graph
    assert orch.GraphOutcome is graph_mod.GraphOutcome


def test_stage_canonical_kit_classes():
    """Stage globals are the kit classes (no vendored copy)."""
    from scholar_graph.builder import CitationGraphBuilder as _KitBuilder
    from scholar_graph.visualizer import GraphVisualizer as _KitVis
    from scholar_search.http_client import AcademicHttpClient as _KitClient

    assert graph_mod.CitationGraphBuilder is _KitBuilder
    assert graph_mod.GraphVisualizer is _KitVis
    assert graph_mod.AcademicHttpClient is _KitClient
    assert graph_mod._REAL_BUILDER is _KitBuilder
    assert graph_mod._REAL_VISUALIZER is _KitVis


# ---------------------------------------------------------------------------
# HCM4J-06 _study_doi canonical home (imported, never duplicated)
# ---------------------------------------------------------------------------


def test_study_doi_imported_from_canonical_home():
    """HCM4J-06: the stage reuses extraction's helper; no duplicate def."""
    assert graph_mod._study_doi is ext_mod._study_doi
    assert graph_mod._study_doi is orch._study_doi
    text = Path(graph_mod.__file__).read_text(encoding="utf-8")
    assert "def _study_doi" not in text
    assert "from .extraction import" in text or "from scholar_harness" in text


# ---------------------------------------------------------------------------
# HCM4J-02 construction parity (+ NEG-02 builder args, lifecycle, NEG-01)
# ---------------------------------------------------------------------------


def test_construction_parity_client_dois_build_pagerank_export(tmp_path, monkeypatch):
    """HCM4J-02: verbatim client/builder/build/pagerank/export/visualizer."""
    _clear_seen()
    monkeypatch.setattr(orch, "CitationGraphBuilder", _FakeGraph)
    monkeypatch.setattr(orch, "GraphVisualizer", _FakeVis)

    seen_client_kwargs: list[dict] = []

    class _RecorderClient:
        def __init__(self, **kwargs):
            seen_client_kwargs.append(dict(kwargs))

    monkeypatch.setattr(graph_mod, "AcademicHttpClient", _RecorderClient)

    docs = [
        {"workspace_id": "SCI-000001", "external_ids": {"doi": "10.1000/aaa"}},
        {"workspace_id": "SCI-000002", "doi": "10.1000/bbb"},
    ]
    lit = tmp_path / "literature"
    outcome = asyncio.run(
        graph_mod.run_graph(included_documents=docs, literature_dir=lit)
    )

    # Client built with the exact base arguments.
    assert seen_client_kwargs == [{"name": "openalex-graph", "rate_limit": 10}]
    # Builder took the client positionally (fake __init__(self, client)).
    assert len(SEEN_CLIENTS) == 1
    assert isinstance(SEEN_CLIENTS[0], _RecorderClient)
    # DOI collection verbatim: external_ids.doi first, then doi, in order.
    assert BUILD_CALLS == [["10.1000/aaa", "10.1000/bbb"]]
    # Outcome counts + paths.
    assert outcome.nodes == 2
    assert outcome.edges == 0
    assert outcome.json_path == lit / "knowledge_graph.json"
    assert outcome.html_path == lit / "knowledge_graph.html"
    assert outcome.json_path.is_file()
    assert outcome.html_path.is_file()
    # Visualizer constructed with str(html_path).
    assert SEEN_HTML_PATHS == [str(lit / "knowledge_graph.html")]
    assert SEEN_JSON_PATHS == [lit / "knowledge_graph.json"]


def test_invalid_rows_filtered_never_reach_build_graph(tmp_path, monkeypatch):
    """NEG-01: DOI-less / falsy-DOI rows are filtered, never built."""
    _clear_seen()
    monkeypatch.setattr(orch, "CitationGraphBuilder", _FakeGraph)
    monkeypatch.setattr(orch, "GraphVisualizer", _FakeVis)

    docs = [
        {"workspace_id": "SCI-000001", "external_ids": {"doi": "10.1000/aaa"}},
        {"workspace_id": "SCI-000002"},  # no DOI anywhere
        {"workspace_id": "SCI-000003", "doi": ""},  # falsy DOI
        {"workspace_id": "SCI-000004", "external_ids": {}},  # empty ids
        {"workspace_id": "SCI-000005", "doi": None, "external_ids": {"doi": ""}},
        {"workspace_id": "SCI-000006", "doi": "10.1000/bbb"},
    ]
    outcome = asyncio.run(
        graph_mod.run_graph(
            included_documents=docs, literature_dir=tmp_path / "literature"
        )
    )
    # Only the two truthy DOIs reach build_graph, in input order.
    assert BUILD_CALLS == [["10.1000/aaa", "10.1000/bbb"]]
    assert outcome.nodes == 2
    # A mutation that builds from unfiltered rows would fail both asserts.


def test_client_kwargs_exact_not_defaults(tmp_path, monkeypatch):
    """NEG-02: a builder-arg change (name/rate_limit) fails here."""
    _clear_seen()
    monkeypatch.setattr(orch, "CitationGraphBuilder", _FakeGraph)
    monkeypatch.setattr(orch, "GraphVisualizer", _FakeVis)

    seen: list[dict] = []

    class _RecorderClient:
        def __init__(self, **kwargs):
            seen.append(dict(kwargs))

    monkeypatch.setattr(graph_mod, "AcademicHttpClient", _RecorderClient)
    asyncio.run(
        graph_mod.run_graph(
            included_documents=[{"external_ids": {"doi": "10.1000/aaa"}}],
            literature_dir=tmp_path / "literature",
        )
    )
    assert seen[0].get("name") == "openalex-graph"
    assert seen[0].get("rate_limit") == 10
    assert set(seen[0]) == {"name", "rate_limit"}


def test_stage_never_closes_graph_client():
    """Lifecycle parity: the base never closed the graph client; neither do we."""
    text = Path(graph_mod.__file__).read_text(encoding="utf-8")
    assert ".close(" not in text
    assert "aclose(" not in text


# ---------------------------------------------------------------------------
# HCM4J-05 empty-DOI seeding
# ---------------------------------------------------------------------------


def test_empty_dois_seed_empty_graph_with_truthful_zero_counts(tmp_path, monkeypatch):
    """HCM4J-05: no DOIs -> seeded empty graph, 0/0, files still written."""
    _clear_seen()
    monkeypatch.setattr(orch, "CitationGraphBuilder", _FakeGraph)
    monkeypatch.setattr(orch, "GraphVisualizer", _FakeVis)

    docs = [
        {"workspace_id": "SCI-000001", "title": "No DOI study"},
        {"workspace_id": "SCI-000002", "doi": ""},
    ]
    lit = tmp_path / "literature"
    outcome = asyncio.run(
        graph_mod.run_graph(included_documents=docs, literature_dir=lit)
    )
    # build_graph is never called; the seeded nx.DiGraph flows through.
    assert BUILD_CALLS == []
    assert outcome.nodes == 0
    assert outcome.edges == 0
    assert json.loads((lit / "knowledge_graph.json").read_text(encoding="utf-8")) == {
        "nodes": [],
        "links": [],
    }
    assert (lit / "knowledge_graph.html").read_text(encoding="utf-8") == "<html></html>"


# ---------------------------------------------------------------------------
# HCM4J-04 no audit or registry
# ---------------------------------------------------------------------------


def test_stage_emits_no_audit_and_no_registry(tmp_path, monkeypatch):
    """HCM4J-04: Stage 8 emits no audit event and no registry state."""
    _clear_seen()
    monkeypatch.setattr(orch, "CitationGraphBuilder", _FakeGraph)
    monkeypatch.setattr(orch, "GraphVisualizer", _FakeVis)

    ws = tmp_path / "ws"
    ws.mkdir()
    asyncio.run(
        graph_mod.run_graph(
            included_documents=[{"external_ids": {"doi": "10.1000/aaa"}}],
            literature_dir=ws / "literature",
        )
    )
    assert _journal_rows(ws) == []
    assert list(ws.rglob("journal.jsonl")) == []
    assert list(ws.rglob("artifact_registry.json")) == []
    names = sorted(p.name for p in (ws / "literature").iterdir())
    assert names == ["knowledge_graph.html", "knowledge_graph.json"]


# ---------------------------------------------------------------------------
# HCM4J-07 move-not-duplicate + HCM4J-08 signature/guard
# ---------------------------------------------------------------------------


def test_stage_8_region_has_no_inline_kit_logic():
    """HCM4J-07: orchestrator delegates; kit logic lives in the stage."""
    source = Path(orch.__file__).read_text(encoding="utf-8")
    region = source.split("Stage 8: Citation Knowledge Graph", 1)[1]
    region = region.split("Stage 9:", 1)[0]
    body = region.split('results["stages"]["graph_nodes"]', 1)[0]
    assert "CitationGraphBuilder(" not in body
    assert "build_graph(" not in body
    assert "compute_pagerank(" not in body
    assert "export_json(" not in body
    assert "GraphVisualizer(" not in body
    assert "generate_html(" not in body
    assert "AcademicHttpClient(" not in body
    assert "DiGraph(" not in body
    assert "run_graph(" in body
    assert "graph_outcome" in body
    mapping = region.split('results["stages"]["graph_nodes"]', 1)[1]
    assert '"DONE"' in mapping
    assert "graph_outcome.nodes" in mapping
    assert "graph_outcome.edges" in mapping


def test_orchestrator_source_has_no_direct_graph_kit_import():
    """Move-not-duplicate: orchestrator must not bind kit modules directly."""
    text = Path(orch.__file__).read_text(encoding="utf-8")
    assert "from scholar_graph.builder import" not in text
    assert "from scholar_graph.visualizer import" not in text
    assert "from scholar_search.http_client import" not in text
    assert "import networkx" not in text


def test_signature_minimal_and_outcome_names():
    """HCM4J-08: minimal keyword-only pair; outcome carries four names."""
    sig = inspect.signature(graph_mod.run_graph)
    params = list(sig.parameters.values())
    assert [p.name for p in params] == ["included_documents", "literature_dir"]
    assert all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in params)
    assert all(p.default is inspect.Parameter.empty for p in params)
    assert inspect.iscoroutinefunction(graph_mod.run_graph)
    import dataclasses

    assert sorted(f.name for f in dataclasses.fields(graph_mod.GraphOutcome)) == [
        "edges",
        "html_path",
        "json_path",
        "nodes",
    ]


def test_stage_has_no_console_transport_import():
    """HCM4J-08: neutral stage imports no console/FastAPI transport."""
    text = Path(graph_mod.__file__).read_text(encoding="utf-8")
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
    assert any("scholar_graph" in s and "scholar_harness" not in s for s in out), (
        "stage must import the scholar-graph kit"
    )
    assert any("scholar_search" in s and "scholar_harness" not in s for s in out), (
        "stage must import the search-kit HTTP client"
    )


def test_narrow_seams_only_two_orchestrator_fallbacks():
    """Only CitationGraphBuilder/GraphVisualizer consult orchestrator.__dict__."""
    text = Path(graph_mod.__file__).read_text(encoding="utf-8")
    assert text.count("orchestrator.__dict__.get(") == 2
    assert '"CitationGraphBuilder"' in text
    assert '"GraphVisualizer"' in text
    assert "_REAL_BUILDER" in text
    assert "_REAL_VISUALIZER" in text
    # No broad __dict__ snooping beyond the two narrow resolvers.
    assert "orchestrator.__dict__" not in text.replace("orchestrator.__dict__.get(", "")
    # networkx and the HTTP client take no orchestrator seam (no patch exists).
    assert text.count("import networkx") == 1
    assert "AcademicHttpClient" in text
    assert '"AcademicHttpClient"' not in text


# ---------------------------------------------------------------------------
# HCM4J-03 orchestrator delegation (fidelity seam) + NEG-05 seam bypass
# ---------------------------------------------------------------------------


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


class _RecorderRetriever:
    def __init__(self, **kwargs):
        self.kw = kwargs


class _FakeMatrix:
    def __init__(self, protocol=None, retriever=None, **kw):
        self.retriever = retriever

    def extract_all(self, output_dir):
        from pathlib import Path as _P

        out = _P(output_dir)
        return [], out / "synthesis_matrix.csv", out / "synthesis_matrix.json"


class _FakeSynth:
    def __init__(self, retriever=None, **kw):
        self.retriever = retriever

    def synthesize(self, **kw):
        return SimpleNamespace(
            synthesis_markdown="# Synthesis\n",
            verified_claims_count=0,
            claims=[],
            entailment_rate=0.0,
        )


def _stub_upstream(monkeypatch):
    _clear_seen()
    monkeypatch.setattr(orch, "SearchEngine", _FakeEngine)
    monkeypatch.setattr(orch, "Deduplicator", _FakeDedup)
    monkeypatch.setattr(orch, "DocumentVerifier", _FakeVerifier)
    monkeypatch.setattr(orch, "ScholarRetriever", _RecorderRetriever)
    monkeypatch.setattr(orch, "MatrixExtractor", _FakeMatrix)
    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _FakeSynth)
    monkeypatch.setattr(orch, "CitationGraphBuilder", _FakeGraph)
    monkeypatch.setattr(orch, "GraphVisualizer", _FakeVis)
    monkeypatch.setattr(
        "scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None
    )


def _two_doi_included() -> list[dict]:
    return [
        {
            "workspace_id": "SCI-000001",
            "title": "Graph Study One",
            "external_ids": {"doi": "10.1000/aaa"},
            "abstract": "Abstract one.",
            "authors": [],
            "year": 2024,
        },
        {
            "workspace_id": "SCI-000002",
            "title": "Graph Study Two",
            "doi": "10.1000/bbb",
            "abstract": "Abstract two.",
            "authors": [],
            "year": 2023,
        },
    ]


def _write_included(ws: Path, docs: list[dict]) -> None:
    (ws / "literature").mkdir(parents=True, exist_ok=True)
    (ws / "literature" / "included.json").write_text(json.dumps(docs), encoding="utf-8")


def test_orchestrator_delegation_maps_done_counts(tmp_path, monkeypatch):
    """HCM4J-03: DONE mapping with the stage's node/edge counts."""
    _stub_upstream(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    _record_workspace_identity(ws, "graph-stage-test")
    _write_included(ws, _two_doi_included())

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert results["status"] == "SUCCESS"
    assert results["stages"]["graph_nodes"] == {
        "status": "DONE",
        "nodes": 2,
        "edges": 0,
    }
    assert BUILD_CALLS == [["10.1000/aaa", "10.1000/bbb"]]


def test_orchestrator_patch_sites_work_unmodified_through_stage(tmp_path, monkeypatch):
    """NEG-05: fidelity patch sites work UNMODIFIED through the stage."""
    _clear_seen()
    # Patch ONLY the orchestrator namespace (exact fidelity :196-197 lines).
    monkeypatch.setattr(orch, "CitationGraphBuilder", _FakeGraph)
    monkeypatch.setattr(orch, "GraphVisualizer", _FakeVis)

    lit = tmp_path / "literature"
    outcome = asyncio.run(
        graph_mod.run_graph(included_documents=_two_doi_included(), literature_dir=lit)
    )
    assert isinstance(outcome, graph_mod.GraphOutcome)
    assert (outcome.nodes, outcome.edges) == (2, 0)
    assert SEEN_CLIENTS and SEEN_HTML_PATHS and SEEN_JSON_PATHS
    # A seam bypass (stage hardcoding the kit classes) would write real
    # OpenAlex-backed files or raise -- never these fake bytes.
    assert json.loads((lit / "knowledge_graph.json").read_text()) == {
        "nodes": ["10.1000/aaa", "10.1000/bbb"],
        "links": [],
    }
    assert (lit / "knowledge_graph.html").read_text() == "<html></html>"


# ---------------------------------------------------------------------------
# HCM4J-09 byte parity probe + NEG-03 order + NEG-06 restore
# ---------------------------------------------------------------------------


def test_orchestrator_mapping_matches_direct_stage_bytes(tmp_path, monkeypatch):
    """HCM4J-09/NEG-03/NEG-06: orch bytes == direct-stage bytes; order kept."""
    _stub_upstream(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    _record_workspace_identity(ws, "graph-stage-test")
    included = _two_doi_included()
    _write_included(ws, included)

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())
    mapping = results["stages"]["graph_nodes"]
    assert mapping["status"] == "DONE"
    assert mapping["nodes"] == 2
    assert mapping["edges"] == 0

    orch_json = (ws / "literature" / "knowledge_graph.json").read_bytes()
    orch_html = (ws / "literature" / "knowledge_graph.html").read_bytes()

    # Byte-identical probe: direct stage over the same included documents
    # reproduces the orchestrator's files byte for byte (restore).
    _clear_seen()
    # Re-apply the fakes for the direct call (cleared above).
    monkeypatch.setattr(orch, "CitationGraphBuilder", _FakeGraph)
    monkeypatch.setattr(orch, "GraphVisualizer", _FakeVis)
    direct_lit = tmp_path / "direct-literature"
    direct_outcome = asyncio.run(
        graph_mod.run_graph(
            included_documents=[dict(d) for d in included],
            literature_dir=direct_lit,
        )
    )
    assert (direct_outcome.nodes, direct_outcome.edges) == (
        mapping["nodes"],
        mapping["edges"],
    )
    assert (direct_lit / "knowledge_graph.json").read_bytes() == orch_json
    assert (direct_lit / "knowledge_graph.html").read_bytes() == orch_html
    # Order preserved: aaa before bbb in the node-link serialization.
    direct_nodes = json.loads(
        (direct_lit / "knowledge_graph.json").read_text(encoding="utf-8")
    )["nodes"]
    assert direct_nodes == ["10.1000/aaa", "10.1000/bbb"]
    # NEG-06 restore: delete + re-run restores identical bytes.
    (direct_lit / "knowledge_graph.json").unlink()
    (direct_lit / "knowledge_graph.html").unlink()
    asyncio.run(
        graph_mod.run_graph(
            included_documents=[dict(d) for d in included],
            literature_dir=direct_lit,
        )
    )
    assert (direct_lit / "knowledge_graph.json").read_bytes() == orch_json
    assert (direct_lit / "knowledge_graph.html").read_bytes() == orch_html
    # A path/serialization/order mutation would fail the byte + order asserts.


# ---------------------------------------------------------------------------
# HCM4J-10 error propagation + NEG-04 failure-into-success
# ---------------------------------------------------------------------------


def test_kit_raise_propagates_no_fabricated_done(tmp_path, monkeypatch):
    """HCM4J-10/NEG-04: kit raise propagates; never mapped to DONE/0."""
    ws = tmp_path / "ws"
    ws.mkdir()
    docs = [{"external_ids": {"doi": "10.1000/aaa"}}]

    class _BoomBuilder:
        def __init__(self, client):
            raise RuntimeError("builder boom")

    monkeypatch.setattr(orch, "CitationGraphBuilder", _BoomBuilder)
    monkeypatch.setattr(orch, "GraphVisualizer", _FakeVis)
    with pytest.raises(RuntimeError, match="builder boom"):
        asyncio.run(
            graph_mod.run_graph(
                included_documents=docs, literature_dir=ws / "literature"
            )
        )
    # No publication on builder failure.
    assert not (ws / "literature" / "knowledge_graph.json").exists()
    assert not (ws / "literature" / "knowledge_graph.html").exists()

    class _BoomBuild:
        def __init__(self, client):
            pass

        async def build_graph(self, dois):
            raise RuntimeError("build_graph boom")

        @staticmethod
        def compute_pagerank(G):
            return {}

        def export_json(self, G, path):
            raise AssertionError("must not export after build failure")

    monkeypatch.setattr(orch, "CitationGraphBuilder", _BoomBuild)
    with pytest.raises(RuntimeError, match="build_graph boom"):
        asyncio.run(
            graph_mod.run_graph(
                included_documents=docs, literature_dir=ws / "literature2"
            )
        )

    class _BoomVis:
        def __init__(self, html_path):
            pass

        def generate_html(self, G):
            raise RuntimeError("visualizer boom")

    monkeypatch.setattr(orch, "CitationGraphBuilder", _FakeGraph)
    monkeypatch.setattr(orch, "GraphVisualizer", _BoomVis)
    with pytest.raises(RuntimeError, match="visualizer boom"):
        asyncio.run(
            graph_mod.run_graph(
                included_documents=docs, literature_dir=ws / "literature3"
            )
        )
    # An empty-as-success mapping (catch + DONE/0) would fail all three raises.
