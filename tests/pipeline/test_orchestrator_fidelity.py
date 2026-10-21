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
from scholar_harness.pipeline import deduplication as dedup_mod
from scholar_harness.pipeline import discovery as disc_mod
from scholar_harness.pipeline import graph as graph_mod
from scholar_harness.pipeline import matrix as mat_mod
from scholar_harness.pipeline import synthesis as synth_mod
from scholar_harness.pipeline import verification as ver_mod

# Registered workspace identity this fixture workspace records. Stage 6 states the
# value recorded in project.json and refuses to index under anything else, so a
# fixture workspace that reaches Stage 6 must record one.
FIXTURE_WORKSPACE_ID = "WSP-" + "0" * 32


def _record_workspace_identity(ws: Path, project_id: str) -> None:
    (ws / "project.json").write_text(
        json.dumps(
            {"project_id": project_id, "registered_workspace_id": FIXTURE_WORKSPACE_ID}
        ),
        encoding="utf-8",
    )


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


class _FakeEngine:
    def __init__(self, providers=None):
        self.providers = providers or []

    async def search_all(self, query, dedup=False):
        return []

    async def close(self):
        pass


class _FailingProvider:
    """A provider that raises -- the kit swallows it, the harness must not."""

    name = "crossref"

    async def search(self, query):
        raise RuntimeError("crossref exploded")
        yield  # pragma: no cover - unreachable, keeps this an async generator


class _FailingEngine:
    """Every provider fails: the harvest produced nothing and broke."""

    def __init__(self, providers=None):
        self.providers = [_FailingProvider()]

    async def search_all(self, query, dedup=False):
        results = []
        for provider in self.providers:
            try:
                async for doc in provider.search(query):
                    results.append(doc)
            except Exception:  # noqa: BLE001 - the kit's swallow behavior
                continue
        return results

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
            json.dumps({"nodes": list(G.nodes), "links": list(G.edges)}),
            encoding="utf-8",
        )


class _FakeVis:
    def __init__(self, html_path):
        self.html_path = html_path

    def generate_html(self, G):
        Path(self.html_path).write_text("<html></html>", encoding="utf-8")


def _stub_kit_engines(monkeypatch):
    monkeypatch.setattr(disc_mod, "SearchEngine", _FakeEngine)
    monkeypatch.setattr(dedup_mod, "Deduplicator", _FakeDedup)
    monkeypatch.setattr(ver_mod, "DocumentVerifier", _FakeVerifier)
    monkeypatch.setattr(orch, "ScholarIndexer", _FakeIndexer)
    monkeypatch.setattr(mat_mod, "ScholarRetriever", _RecorderRetriever)
    monkeypatch.setattr(mat_mod, "MatrixExtractor", _FakeMatrix)
    monkeypatch.setattr(synth_mod, "GroundedSynthesisEngine", _FakeSynth)
    monkeypatch.setattr(graph_mod, "CitationGraphBuilder", _FakeGraph)
    monkeypatch.setattr(graph_mod, "GraphVisualizer", _FakeVis)
    monkeypatch.setattr(
        "scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None
    )
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
    assert not list((ws / "extracted").glob("*.md")), (
        "no extraction may occur before collect"
    )
    assert not (ws / "synthesis" / "literature_review.md").exists()

    journal = (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8")
    assert "PIPELINE_RUN_PAUSED_FOR_SCREENING" in journal


# ---------------------------------------------------------------------------
# After collect: real extraction (metadata frontmatter), no invented prose
# ---------------------------------------------------------------------------


def test_pipeline_after_collect_writes_metadata_extraction_not_placeholder(
    tmp_path, monkeypatch
):
    _stub_kit_engines(monkeypatch)
    ws = tmp_path
    _write_protocol(ws)
    _record_workspace_identity(ws, "fidelity-test-workspace")

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

    # T-TRUTH-COUNTS-01: the fake engine returns no documents, so the
    # harvest is EMPTY_RESULT and the pipeline must NOT report SUCCESS
    # ("empty output is not automatically success"). The old assertion
    # expected "SUCCESS" -- that was the defect this task closes.
    assert results["status"] == "EMPTY_RESULT"
    assert results["discovery"]["status"] == "EMPTY_RESULT"
    assert results["stages"]["extraction"]["status"] == "DONE"

    md = ws / "extracted" / "SCI-000001.md"
    assert md.is_file()
    text = md.read_text(encoding="utf-8")
    assert 'extraction_engine: "metadata"' in text
    assert "Empirically measured latency under load." in text
    assert "Methodology" not in text.replace("## Abstract", "")
    assert (
        "Evaluated using standard benchmarks and controlled baseline comparisons."
        not in text
    )


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
    _record_workspace_identity(ws, "fidelity-test-workspace")

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

    assert any(
        call.get("collection_name") == "scholar_docs" for call in RETRIEVER_CALLS
    )
    assert any(
        str(call.get("db_path") or "").endswith("chroma_db") for call in RETRIEVER_CALLS
    )
    assert SEEN_MATRIX_RETRIEVERS and SEEN_SYNTH_RETRIEVERS
    assert SEEN_MATRIX_RETRIEVERS[-1] is SEEN_SYNTH_RETRIEVERS[-1]


# ---------------------------------------------------------------------------
# T-TRUTH-COUNTS-01: declared counts must reconcile with physical artifacts
# ---------------------------------------------------------------------------


def test_pipeline_sync_repairs_a_stale_declared_count(tmp_path):
    """AC-2/N-3: ``sync`` repairs an under-reported summary from the files."""
    from scholar_harness.doctor import Status, check_layout

    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps(
            {
                "project_id": "fidelity-test-workspace",
                "registered_workspace_id": FIXTURE_WORKSPACE_ID,
                "title": "Reconciliation",
                "stats": {"discovered_papers": 0},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    corpus = ws / "calibration"
    corpus.mkdir()
    payload = {"documents": [{"title": f"study {i}"} for i in range(5)]}
    (corpus / "raw_union.json").write_text(json.dumps(payload), encoding="utf-8")

    stats_check = next(r for r in check_layout(ws) if r.name == "project.json-stats")
    assert stats_check.status is Status.FAIL  # declared 0 vs 5 physical records

    result = orch.ResearchOrchestrator(ws).sync_state()
    assert result["stats"]["discovered_papers"] == 5

    manifest = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    assert manifest["stats"]["discovered_papers"] == 5
    assert manifest["registered_workspace_id"] == FIXTURE_WORKSPACE_ID

    stats_check = next(r for r in check_layout(ws) if r.name == "project.json-stats")
    assert stats_check.status is Status.PASS


def test_pipeline_failure_does_not_publish_authoritative_output(tmp_path, monkeypatch):
    """COMPASS section 7: failure does not publish authoritative output.

    A FAILED harvest must not leave a corpus artifact behind, must not run
    the downstream stages, and must not be reported as a successful run.
    """
    _stub_kit_engines(monkeypatch)
    monkeypatch.setattr(disc_mod, "SearchEngine", _FailingEngine)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    _record_workspace_identity(ws, "fidelity-test-workspace")

    results = _run(ws)

    assert results["status"] == "FAILED"
    assert results["discovery"]["status"] == "FAILED"
    assert results["discovery"]["corpus_published"] is False

    # No authoritative corpus artifact was published.
    assert not (ws / "literature" / "raw_search.json").exists()
    assert not (ws / "literature" / "all_raw_search.json").exists()
    assert not (ws / "literature" / "deduped.json").exists()
    assert not (ws / "literature" / "verified.json").exists()
    assert not list((ws / "extracted").glob("*.md"))
    assert not (ws / "synthesis" / "literature_review.md").exists()

    # The downstream stages are skipped with an explicit reason.
    assert results["stages"]["extraction"]["status"] == "SKIPPED"
    assert "discovery failed" in results["stages"]["extraction"]["reason"]

    # The journal records the abort -- never a "completed" row.
    journal = (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8")
    assert "PIPELINE_RUN_ABORTED" in journal
    assert "PIPELINE_RUN_COMPLETED" not in journal


def test_pipeline_run_records_the_discovery_event(tmp_path, monkeypatch):
    """AC-5: a pipeline run leaves a canonical DISCOVERY_SEARCH journal row."""
    _stub_kit_engines(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    _record_workspace_identity(ws, "fidelity-test-workspace")

    _run(ws)

    journal = ws / "audit" / "journal.jsonl"
    events = [
        json.loads(line)
        for line in journal.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    discovery = [e for e in events if e.get("action") == "DISCOVERY_SEARCH"]
    assert discovery, "the discovery stage must leave a canonical audit event"
    event = discovery[-1]
    assert event["agent_or_tool"]
    assert event["inputs"] and event["outputs"]
    assert event["metrics"]["raw_hits"] == 0  # the fake engine returns nothing
    assert event["status"] != "SUCCESS"  # an empty harvest is never a success


# ---------------------------------------------------------------------------
# Provider resolution map (Stage 1, D1) and PDF/slug helpers
# ---------------------------------------------------------------------------


def test_provider_resolution_resolves_names_to_instances():
    from scholar_search.providers import OpenAlexProvider

    resolved = orch._resolve_providers(["openalex", "crossref"])
    assert len(resolved) == 2
    assert isinstance(resolved[0], OpenAlexProvider)
    assert orch._resolve_providers(
        ["openalex", "not-a-provider"]
    )  # unknown names dropped
    assert orch._resolve_providers([]) is None


def test_extraction_file_stem_and_pdf_helpers(tmp_path):
    """The stem is a FILENAME, not an identity.

    ``_extraction_file_stem`` and ``_study_pdf`` exist to locate a file on disk.
    They are deliberately not wired to any typed request: Stage 6 takes both
    identity limbs from the accepted document manifest instead. A stem derived
    from ``workspace_id`` therefore names a file and nothing more -- it never
    becomes a ``document_id`` or ``study_id``.
    """
    doc = {"workspace_id": "SCI-000009", "external_ids": {"doi": "10.1/aa/bb"}}
    assert orch._study_doi(doc) == "10.1/aa/bb"
    assert orch._extraction_file_stem(doc) == "SCI-000009"
    assert (
        orch._extraction_file_stem({"external_ids": {}, "doi": "10.1/aa"}) == "10.1_aa"
    )

    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    hit = pdf_dir / "SCI-000009.pdf"
    hit.write_bytes(b"%PDF-1.4")
    assert orch._study_pdf(pdf_dir, doc) == hit
    assert orch._study_pdf(pdf_dir, {"workspace_id": "SCI-000999", "doi": "x"}) is None


# ---------------------------------------------------------------------------
# T-TRUTH-COUNTS-01 (final narrow repair): the STATE_SYNC row carries the
# reconciliation status, not a generic SUCCESS
# ---------------------------------------------------------------------------


def _sync_events(ws: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in (ws / "audit" / "journal.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]


def test_state_sync_row_status_expresses_the_reconciliation_status(tmp_path):
    """F-8: the STATE_SYNC row's status IS the reconciliation's status.

    The row's purpose is the reconciliation, so a generic ``SUCCESS`` next
    to a ``STALE`` payload was a false history entry. The row now carries
    the reconciliation status itself (``STALE`` -> ``OK`` after the repair).
    """
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps(
            {
                "project_id": "fidelity-test-workspace",
                "registered_workspace_id": FIXTURE_WORKSPACE_ID,
                "title": "Reconciliation",
                "stats": {"discovered_papers": 0},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    corpus = ws / "calibration"
    corpus.mkdir()
    (corpus / "raw_union.json").write_text(
        json.dumps({"documents": [{"title": f"study {i}"} for i in range(5)]}),
        encoding="utf-8",
    )

    orch.ResearchOrchestrator(ws).sync_state()

    rows = [e for e in _sync_events(ws) if e.get("action") == "STATE_SYNC"]
    assert rows
    event = rows[-1]
    # The declared 0 contradicts the 5 physical records -> STALE, and the
    # row says so.
    assert event["metrics"]["reconciliation"]["status"] == "STALE"
    assert event["status"] == "STALE"
    assert event["status"] != "SUCCESS"

    # The second sync repairs the summary -> the row now says OK.
    orch.ResearchOrchestrator(ws).sync_state()
    rows = [e for e in _sync_events(ws) if e.get("action") == "STATE_SYNC"]
    assert rows[-1]["status"] == "OK"
    assert rows[-1]["metrics"]["reconciliation"]["status"] == "OK"


def test_state_sync_payload_carries_the_unclassified_and_unreadable_evidence(
    tmp_path,
):
    """F-7: the payload carries the evidence for the non-OK states.

    The doc listed ``unclassified`` / ``unreadable`` / ``undetermined`` as
    payload keys, but the row did not carry them -- the states could be
    stated, never justified. The keys are ADDED (not removed from the doc):
    they are the evidence a reader needs.
    """
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps(
            {
                "project_id": "fidelity-test-workspace",
                "registered_workspace_id": FIXTURE_WORKSPACE_ID,
                "title": "Evidence",
                "stats": {},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    corpus = ws / "calibration"
    corpus.mkdir()
    (corpus / "raw_union.json").write_text(
        json.dumps({"documents": [{"title": "study"}]}), encoding="utf-8"
    )
    # A record-bearing artifact with no known role -> UNCLASSIFIED ...
    (corpus / "mystery_blob.json").write_text(
        json.dumps({"documents": [{"title": "mystery"}]}), encoding="utf-8"
    )
    # ... and an artifact that cannot be read at all -> UNREADABLE.
    (corpus / "broken.json").write_text("{ not json", encoding="utf-8")

    orch.ResearchOrchestrator(ws).sync_state()

    rows = [e for e in _sync_events(ws) if e.get("action") == "STATE_SYNC"]
    payload = rows[-1]["metrics"]["reconciliation"]
    assert "unclassified" in payload
    assert "unreadable" in payload
    assert "undetermined" in payload
    assert payload["unclassified"], "the unclassified artifact must be listed"
    assert payload["unreadable"], "the unreadable artifact must be listed"
    assert payload["status"] == "UNCLASSIFIED"
    assert rows[-1]["status"] == "UNCLASSIFIED"
