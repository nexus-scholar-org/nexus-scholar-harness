"""Focused HCM-04k tests for the neutral synthesis stage.

Stage 9 (grounded evidence synthesis and entailment over the
vector-indexed corpus) lives in ``scholar_harness.pipeline.synthesis``;
the orchestrator delegates and maps the outcome identically. Every test
is hermetic (``tmp_path`` only, no network; the synthesis engine is
faked, never a live model; real RQ selection runs on a controlled
compiled protocol) and asserts zero behavior change: verbatim engine
construction, verbatim first-RQ selection with fallbacks, verbatim
synchronous ``synthesize`` call shape, byte-identical
``synthesis/literature_review.md`` publication, identical results
mapping, carried retriever binding from Stage 7, no audit or registry
writes, and identical error propagation.

Mapping to the HCM-04k packet (A1-7/B8-14/C15-18):

- HCM4K-01 shim identity (``orch.X is stage.X`` for all three names)
- HCM4K-02 construction parity (retriever kw + RQ passthrough + engine
  args + sync call shape)
- HCM4K-03 RQ fallbacks identical (first RQ vs default text/id)
- HCM4K-04 results mapping identical (verified/total/rate)
- HCM4K-05 no audit or registry from the stage
- HCM4K-06 retriever binding (SAME object Stage 7 -> engine)
- HCM4K-07 move-not-duplicate (Stage 9 region has no inline kit logic)
- HCM4K-08 minimal signature + outcome names + transport guard
- HCM4K-09 byte parity probe (orch vs direct stage bytes agree)
- HCM4K-10 error propagation (kit raise propagates, no fabricated DONE)

Negatives (each tmp_path-only, byte-identical restored):

- NEG-01 RQ change (second-RQ or hardcoded query fails)
- NEG-02 upstream omission (required limbs missing -> TypeError, no file)
- NEG-03 engine-arg/binding change (retriever kw / synthesize kwargs exact)
- NEG-04 output/location change (path + encoding + content exact)
- NEG-05 failure-into-success (raise is never mapped to DONE/0)
- NEG-06 evidence fabrication/strip (file bytes == engine markdown exactly)
- NEG-07 byte-identical probe restore (delete + re-run restores bytes)

Carry-forward debt TD-HCM-TEST-SEAMS x3 untouched
(``SearchEngine`` / ``Deduplicator`` / ``DocumentVerifier`` shims stay);
this packet adds ONE NARROW seam only (``GroundedSynthesisEngine`` via
``orchestrator.__dict__`` honoring, HCM-04b precedent). No broad layer,
no other seams. TD-E3-CURRENTNESS-01 and the MCP docs failure stay
base-proven and untouched.
"""

from __future__ import annotations

import asyncio
import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scholar_harness import orchestrator as orch
from scholar_harness.pipeline import synthesis as synth_mod

FIXTURE_WORKSPACE_ID = "WSP-" + "0" * 32

DEFAULT_RQ_TEXT = "What are the primary empirical findings?"
DEFAULT_RQ_ID = "RQ1"


def _record_workspace_identity(ws: Path, project_id: str) -> None:
    (ws / "project.json").write_text(
        json.dumps(
            {"project_id": project_id, "registered_workspace_id": FIXTURE_WORKSPACE_ID}
        ),
        encoding="utf-8",
    )


def _write_protocol(ws: Path, slug: str = "synthesis-stage-test") -> Path:
    from scholar_protocol.canonical import canonical_json
    from scholar_protocol.compiler import compile_protocol
    from scholar_protocol.intent import IntentPacket

    data = {
        "protocol_id": "synthesis-stage",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": slug,
        "playbook_type": "DESIGN_SCIENCE",
        "title": "Synthesis Stage Parity",
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


def _load_protocol(ws: Path):
    from scholar_protocol.models import ResearchProtocol

    p = ws / "protocol.json"
    if not p.exists():
        _write_protocol(ws)
        p = ws / "protocol.json"
    return ResearchProtocol.model_validate_json(p.read_text(encoding="utf-8"))


def _journal_rows(ws: Path) -> list[dict]:
    p = ws / "audit" / "journal.jsonl"
    if not p.exists():
        return []
    return [
        json.loads(line)
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


SEEN_ENGINE_RETRIEVERS: list[object] = []
SEEN_SYNTHESIZE_KWARGS: list[dict] = []


class _FakeEngine:
    """Fake synthesis engine mirroring the fidelity stubs (retriever-opaque)."""

    def __init__(self, retriever=None, **kw):
        SEEN_ENGINE_RETRIEVERS.append(retriever)
        self.retriever = retriever
        self.extra_kw = kw

    def synthesize(self, **kwargs):
        SEEN_SYNTHESIZE_KWARGS.append(dict(kwargs))
        return SimpleNamespace(
            synthesis_markdown="# Synthesis\n\n- finding one [tok]\n",
            verified_claims_count=2,
            claims=[{"a": 1}, {"b": 2}],
            entailment_rate=0.5,
        )


def _clear_seen():
    SEEN_ENGINE_RETRIEVERS.clear()
    SEEN_SYNTHESIZE_KWARGS.clear()


# ---------------------------------------------------------------------------
# HCM4K-01 shim identity
# ---------------------------------------------------------------------------


def test_shim_identity_all_three_names():
    """HCM4K-01: orchestrator names ARE the stage objects (move, not copy)."""
    assert orch.GroundedSynthesisEngine is synth_mod.GroundedSynthesisEngine
    assert orch.run_synthesis is synth_mod.run_synthesis
    assert orch.SynthesisOutcome is synth_mod.SynthesisOutcome


def test_stage_canonical_kit_class():
    """Stage global is the kit class (no vendored copy)."""
    from scholar_rag.synthesis import GroundedSynthesisEngine as _KitEngine

    assert synth_mod.GroundedSynthesisEngine is _KitEngine
    assert synth_mod._REAL_ENGINE is _KitEngine


# ---------------------------------------------------------------------------
# HCM4K-02 construction parity + HCM4K-03 RQ fallbacks + HCM4K-06 binding
# ---------------------------------------------------------------------------


def test_construction_parity_retriever_rq_and_call_shape(tmp_path, monkeypatch):
    """HCM4K-02/03/06: verbatim retriever kw, first-RQ passthrough, sync call."""
    _clear_seen()
    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _FakeEngine)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    protocol = _load_protocol(ws)
    first = protocol.research_questions[0]
    retriever = object()
    synth_dir = ws / "synthesis"

    outcome = synth_mod.run_synthesis(
        protocol=protocol,
        retriever=retriever,
        synthesis_dir=synth_dir,
    )

    # Engine took the carried retriever via the exact keyword.
    assert SEEN_ENGINE_RETRIEVERS == [retriever]
    assert len(SEEN_SYNTHESIZE_KWARGS) == 1
    kw = SEEN_SYNTHESIZE_KWARGS[0]
    assert kw == {
        "query": first.text,
        "rq_id": first.id,
        "section_category": "results_empirical",
    }
    # Real RQ selection on the controlled protocol (never hardcoded).
    assert kw["query"] == "What is the pipeline throughput?"
    assert kw["rq_id"] == "RQ1"
    # Outcome counts mirror the kit result limbs.
    assert outcome.verified_claims == 2
    assert outcome.total_claims == 2
    assert outcome.entailment_rate == 0.5
    assert outcome.review_path == synth_dir / "literature_review.md"
    # run_synthesis is sync, matching the base call (never awaited).
    assert not inspect.iscoroutinefunction(synth_mod.run_synthesis)


def test_rq_fallbacks_when_no_research_questions(tmp_path, monkeypatch):
    """HCM4K-03: empty RQs fall back to the base default text/id."""
    _clear_seen()
    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _FakeEngine)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    protocol = _load_protocol(ws)
    empty = protocol.model_copy(update={"research_questions": []})
    retriever = object()

    outcome = synth_mod.run_synthesis(
        protocol=empty,
        retriever=retriever,
        synthesis_dir=ws / "synthesis",
    )

    assert SEEN_SYNTHESIZE_KWARGS[0]["query"] == DEFAULT_RQ_TEXT
    assert SEEN_SYNTHESIZE_KWARGS[0]["rq_id"] == DEFAULT_RQ_ID
    assert SEEN_SYNTHESIZE_KWARGS[0]["section_category"] == "results_empirical"
    assert outcome.review_path.name == "literature_review.md"


def test_second_rq_is_never_selected(tmp_path, monkeypatch):
    """NEG-01: an RQ change (second RQ or hardcoded query) fails here."""
    _clear_seen()
    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _FakeEngine)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    protocol = _load_protocol(ws)
    # Append a decoy second RQ; the stage must still select the first.
    second = protocol.research_questions[0].model_copy(
        update={"id": "RQ2", "text": "Decoy second question?"}
    )
    two = protocol.model_copy(
        update={"research_questions": [protocol.research_questions[0], second]}
    )

    synth_mod.run_synthesis(
        protocol=two,
        retriever=object(),
        synthesis_dir=ws / "synthesis",
    )

    assert SEEN_SYNTHESIZE_KWARGS[0]["query"] == "What is the pipeline throughput?"
    assert SEEN_SYNTHESIZE_KWARGS[0]["rq_id"] == "RQ1"


def test_engine_binding_is_exact_retriever_keyword(tmp_path, monkeypatch):
    """NEG-03: the retriever kw must stay ``retriever=retriever`` exact."""
    _clear_seen()

    seen_init_kwargs: list[dict] = []

    class _RecorderEngine(_FakeEngine):
        def __init__(self, *args, **kwargs):
            seen_init_kwargs.append(dict(kwargs))
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _RecorderEngine)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    protocol = _load_protocol(ws)
    retriever = object()
    synth_mod.run_synthesis(
        protocol=protocol,
        retriever=retriever,
        synthesis_dir=ws / "synthesis",
    )

    assert seen_init_kwargs == [{"retriever": retriever}]
    # A binding change (positional, renamed kw, fresh retriever) fails here.


def test_synthesize_kwargs_exact_not_defaults(tmp_path, monkeypatch):
    """NEG-03: synthesize kwargs must stay query/rq_id/section exact."""
    _clear_seen()
    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _FakeEngine)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    protocol = _load_protocol(ws)
    synth_mod.run_synthesis(
        protocol=protocol,
        retriever=object(),
        synthesis_dir=ws / "synthesis",
    )

    kw = SEEN_SYNTHESIZE_KWARGS[0]
    assert set(kw) == {"query", "rq_id", "section_category"}
    assert kw["section_category"] == "results_empirical"


# ---------------------------------------------------------------------------
# HCM4K-05 no audit or registry + HCM4K-04 file publication
# ---------------------------------------------------------------------------


def test_stage_emits_no_audit_and_no_registry(tmp_path, monkeypatch):
    """HCM4K-05: Stage 9 emits no audit event and no registry state."""
    _clear_seen()
    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _FakeEngine)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    protocol = _load_protocol(ws)

    synth_mod.run_synthesis(
        protocol=protocol,
        retriever=object(),
        synthesis_dir=ws / "synthesis",
    )

    assert _journal_rows(ws) == []
    assert list(ws.rglob("journal.jsonl")) == []
    assert list(ws.rglob("artifact_registry.json")) == []
    names = sorted(p.name for p in (ws / "synthesis").iterdir())
    assert names == ["literature_review.md"]


def test_file_bytes_equal_engine_markdown_exactly(tmp_path, monkeypatch):
    """NEG-06: no fabrication, no stripping -- file == engine markdown bytes."""
    _clear_seen()

    markdown = "# Title\n\n- claim one [WSP-000001#sec#CHK-001]\n- claim two [WSP-000001#sec#CHK-002]\n"

    class _ExactEngine:
        def __init__(self, retriever=None, **kw):
            pass

        def synthesize(self, **kw):
            return SimpleNamespace(
                synthesis_markdown=markdown,
                verified_claims_count=1,
                claims=[{"a": 1}],
                entailment_rate=1.0,
            )

    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _ExactEngine)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    protocol = _load_protocol(ws)
    outcome = synth_mod.run_synthesis(
        protocol=protocol,
        retriever=object(),
        synthesis_dir=ws / "synthesis",
    )

    raw = (ws / "synthesis" / "literature_review.md").read_bytes()
    # Windows text-mode translates \n to \r\n on write; read_text with
    # universal newlines recovers the exact engine string (same as the base
    # write_text path did). Byte identity orch-vs-stage is proven by the
    # HCM4K-09 probe below, which compares raw bytes to raw bytes.
    assert (ws / "synthesis" / "literature_review.md").read_text(
        encoding="utf-8"
    ) == markdown
    assert outcome.review_path.read_bytes() == raw
    # A mutation that wraps, strips, or appends prose fails the byte assert.


def test_output_path_encoding_exact(tmp_path, monkeypatch):
    """NEG-04: path, filename, and utf-8 encoding stay exact."""
    _clear_seen()
    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _FakeEngine)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    protocol = _load_protocol(ws)
    synth_dir = ws / "custom-synth"
    outcome = synth_mod.run_synthesis(
        protocol=protocol,
        retriever=object(),
        synthesis_dir=synth_dir,
    )

    assert outcome.review_path == synth_dir / "literature_review.md"
    assert outcome.review_path.is_file()
    assert outcome.review_path.read_text(encoding="utf-8") == (
        "# Synthesis\n\n- finding one [tok]\n"
    )


# ---------------------------------------------------------------------------
# HCM4K-07 move-not-duplicate + HCM4K-08 signature/guard
# ---------------------------------------------------------------------------


def test_stage_9_region_has_no_inline_kit_logic():
    """HCM4K-07: orchestrator delegates; kit logic lives in the stage."""
    source = Path(orch.__file__).read_text(encoding="utf-8")
    region = source.split("Stage 9: Grounded Evidence Synthesis", 1)[1]
    region = region.split("Stage 10:", 1)[0]
    body = region.split('results["stages"]["synthesis"]', 1)[0]
    assert "GroundedSynthesisEngine(" not in body
    assert ".synthesize(" not in body
    assert "research_questions" not in body
    assert "synthesis_markdown" not in body
    # The path is constructed in the stage (synth_dir / "..." lives there);
    # the orchestrator must not construct or write it.
    assert "synth_dir /" not in body
    assert ".write_text(" not in body
    assert "What are the primary empirical findings?" not in body
    assert "run_synthesis(" in body
    assert "synthesis_outcome" in body
    mapping = region.split('results["stages"]["synthesis"]', 1)[1]
    assert "synthesis_outcome.verified_claims" in mapping
    assert "synthesis_outcome.total_claims" in mapping
    assert "synthesis_outcome.entailment_rate" in mapping
    # synth_file binding for Stage 10 is retained.
    assert "synth_file = synthesis_outcome.review_path" in region


def test_orchestrator_source_has_no_direct_synthesis_kit_import():
    """Move-not-duplicate: orchestrator must not bind the kit module directly."""
    text = Path(orch.__file__).read_text(encoding="utf-8")
    assert "from scholar_rag.synthesis import" not in text


def test_signature_minimal_and_outcome_names():
    """HCM4K-08: minimal keyword-only triplet; outcome carries four names."""
    sig = inspect.signature(synth_mod.run_synthesis)
    params = list(sig.parameters.values())
    assert [p.name for p in params] == ["protocol", "retriever", "synthesis_dir"]
    assert all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in params)
    assert all(p.default is inspect.Parameter.empty for p in params)
    assert not inspect.iscoroutinefunction(synth_mod.run_synthesis)
    import dataclasses

    assert sorted(f.name for f in dataclasses.fields(synth_mod.SynthesisOutcome)) == [
        "entailment_rate",
        "review_path",
        "total_claims",
        "verified_claims",
    ]


def test_stage_has_no_console_transport_import():
    """HCM4K-08: neutral stage imports no console/FastAPI transport."""
    text = Path(synth_mod.__file__).read_text(encoding="utf-8")
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
    assert any("scholar_rag" in s and "scholar_harness" not in s for s in out), (
        "stage must import the scholar-rag kit"
    )


def test_narrow_seam_only_one_orchestrator_fallback():
    """Only GroundedSynthesisEngine consults orchestrator.__dict__."""
    text = Path(synth_mod.__file__).read_text(encoding="utf-8")
    assert text.count("orchestrator.__dict__.get(") == 1
    assert '"GroundedSynthesisEngine"' in text
    assert "_REAL_ENGINE" in text
    # No broad __dict__ snooping beyond the narrow resolver.
    assert "orchestrator.__dict__" not in text.replace("orchestrator.__dict__.get(", "")


def test_upstream_omission_is_type_error_no_file(tmp_path, monkeypatch):
    """NEG-02: required limbs omitted -> TypeError, no file, no success."""
    _clear_seen()
    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _FakeEngine)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    protocol = _load_protocol(ws)

    with pytest.raises(TypeError):
        synth_mod.run_synthesis(
            protocol=protocol,
            retriever=object(),
            # synthesis_dir omitted
        )
    with pytest.raises(TypeError):
        synth_mod.run_synthesis(
            protocol=protocol,
            # retriever omitted
            synthesis_dir=ws / "synthesis",
        )
    with pytest.raises(TypeError):
        synth_mod.run_synthesis(
            # protocol omitted
            retriever=object(),
            synthesis_dir=ws / "synthesis",
        )
    # No review is fabricated when the call is refused.
    assert not (ws / "synthesis" / "literature_review.md").exists()


# ---------------------------------------------------------------------------
# HCM4K-04/06 orchestrator delegation + retriever binding (fidelity seam)
# ---------------------------------------------------------------------------


class _FakeSearchEngine:
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
        SEEN_MATRIX_RETRIEVERS.append(retriever)

    def extract_all(self, output_dir):
        from pathlib import Path as _P

        out = _P(output_dir)
        return [], out / "synthesis_matrix.csv", out / "synthesis_matrix.json"


SEEN_MATRIX_RETRIEVERS: list[object] = []


class _FakeGraph:
    def __init__(self, client):
        self.client = client

    async def build_graph(self, dois):
        import networkx as nx

        G = nx.DiGraph()
        for d in dois:
            G.add_node(d, label=d)
        return G

    @staticmethod
    def compute_pagerank(G):
        import networkx as nx

        ranks = {n: 1.0 / max(len(G), 1) for n in G.nodes}
        nx.set_node_attributes(G, ranks, "pagerank")
        return ranks

    def export_json(self, G, path):
        path.write_text(
            json.dumps({"nodes": list(G.nodes), "links": list(G.edges)}),
            encoding="utf-8",
        )


class _FakeVis:
    def __init__(self, html_path):
        self.html_path = html_path

    def generate_html(self, G):
        Path(self.html_path).write_text("<html></html>", encoding="utf-8")


class _FakeSynth:
    def __init__(self, retriever=None, **kw):
        self.retriever = retriever
        SEEN_ENGINE_RETRIEVERS.append(retriever)

    def synthesize(self, **kw):
        SEEN_SYNTHESIZE_KWARGS.append(dict(kw))
        return SimpleNamespace(
            synthesis_markdown="# Synthesis\n",
            verified_claims_count=1,
            claims=[{"a": 1}, {"b": 2}],
            entailment_rate=0.5,
        )


def _stub_upstream(monkeypatch):
    _clear_seen()
    SEEN_MATRIX_RETRIEVERS.clear()
    monkeypatch.setattr(orch, "SearchEngine", _FakeSearchEngine)
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


def test_orchestrator_mapping_and_retriever_binding(tmp_path, monkeypatch):
    """HCM4K-04/06: mapping identical + SAME retriever to Matrix and Synthesis."""
    _stub_upstream(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    _record_workspace_identity(ws, "synthesis-stage-test")

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

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())

    assert results["status"] == "SUCCESS"
    mapping = results["stages"]["synthesis"]
    assert mapping == {
        "verified_claims": 1,
        "total_claims": 2,
        "entailment_rate": 0.5,
    }
    # Retriever binding: Matrix-seen object IS Synthesis-seen object.
    assert SEEN_MATRIX_RETRIEVERS and SEEN_ENGINE_RETRIEVERS
    assert SEEN_MATRIX_RETRIEVERS[-1] is SEEN_ENGINE_RETRIEVERS[-1]
    # RQ passthrough used the controlled protocol's first RQ.
    assert SEEN_SYNTHESIZE_KWARGS[-1]["query"] == "What is the pipeline throughput?"
    assert SEEN_SYNTHESIZE_KWARGS[-1]["rq_id"] == "RQ1"
    assert SEEN_SYNTHESIZE_KWARGS[-1]["section_category"] == "results_empirical"
    # File published byte-identically.
    assert (ws / "synthesis" / "literature_review.md").read_text(
        encoding="utf-8"
    ) == "# Synthesis\n"
    # NEG-02 companion: a binding break (different objects) would fail here.


def test_orchestrator_stage_resolves_patch_site_unmodified(tmp_path, monkeypatch):
    """NEG-05 seam bypass: orchestrator-namespace patch takes effect."""
    _clear_seen()
    # Patch ONLY the orchestrator namespace (exact fidelity :195 line).
    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _FakeEngine)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    protocol = _load_protocol(ws)
    retriever = object()

    outcome = synth_mod.run_synthesis(
        protocol=protocol,
        retriever=retriever,
        synthesis_dir=ws / "synthesis",
    )
    assert SEEN_ENGINE_RETRIEVERS[0] is retriever
    assert outcome.verified_claims == 2
    # A seam bypass (stage hardcoding the kit class) would fail both asserts.


# ---------------------------------------------------------------------------
# HCM4K-09 byte parity probe + NEG-07 restore
# ---------------------------------------------------------------------------


def test_orchestrator_mapping_matches_direct_stage_bytes(tmp_path, monkeypatch):
    """HCM4K-09/NEG-07: orch delegation maps identically; bytes agree + restore."""
    _stub_upstream(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    _record_workspace_identity(ws, "synthesis-stage-test")

    included = [
        {
            "workspace_id": "SCI-000001",
            "title": "Graph Study",
            "external_ids": {"doi": "10.1000/zzz"},
            "abstract": "Abstract.",
            "authors": [],
            "year": 2024,
        }
    ]
    (ws / "literature").mkdir(parents=True, exist_ok=True)
    (ws / "literature" / "included.json").write_text(
        json.dumps(included), encoding="utf-8"
    )

    results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())
    mapping = results["stages"]["synthesis"]
    assert mapping == {
        "verified_claims": 1,
        "total_claims": 2,
        "entailment_rate": 0.5,
    }

    orch_bytes = (ws / "synthesis" / "literature_review.md").read_bytes()

    # Byte-identical probe: direct stage over the same protocol/retriever
    # reproduces the orchestrator's file byte for byte (restore).
    _clear_seen()
    # Re-apply the deterministic fake for the direct call (cleared above).
    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _FakeEngine)
    direct_synth = tmp_path / "direct-synthesis"
    protocol = _load_protocol(ws)
    direct_outcome = synth_mod.run_synthesis(
        protocol=protocol,
        retriever=object(),
        synthesis_dir=direct_synth,
    )
    assert direct_outcome.verified_claims == 2
    # The direct fake writes its own markdown; the orch bytes came from the
    # orch fake -- both are deterministic, so compare shape, then restore
    # the orch bytes through the direct stage with the orch fake.
    _clear_seen()
    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _FakeSynth)
    restore_dir = tmp_path / "restore-synthesis"
    restore_outcome = synth_mod.run_synthesis(
        protocol=protocol,
        retriever=object(),
        synthesis_dir=restore_dir,
    )
    assert (restore_dir / "literature_review.md").read_bytes() == orch_bytes
    assert (restore_outcome.verified_claims, restore_outcome.total_claims) == (
        mapping["verified_claims"],
        mapping["total_claims"],
    )
    # NEG-07 restore: delete + re-run restores identical bytes.
    (restore_dir / "literature_review.md").unlink()
    synth_mod.run_synthesis(
        protocol=protocol,
        retriever=object(),
        synthesis_dir=restore_dir,
    )
    assert (restore_dir / "literature_review.md").read_bytes() == orch_bytes
    # A path/serialization/content mutation would fail the byte asserts.


# ---------------------------------------------------------------------------
# HCM4K-10 error propagation + NEG-05 failure-into-success
# ---------------------------------------------------------------------------


def test_kit_raise_propagates_no_fabricated_done(tmp_path, monkeypatch):
    """HCM4K-10/NEG-05: kit raise propagates; never mapped to DONE/0."""
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    protocol = _load_protocol(ws)

    class _BoomEngine:
        def __init__(self, retriever=None, **kw):
            raise RuntimeError("engine boom")

    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _BoomEngine)
    with pytest.raises(RuntimeError, match="engine boom"):
        synth_mod.run_synthesis(
            protocol=protocol,
            retriever=object(),
            synthesis_dir=ws / "synthesis",
        )
    # No publication on engine-construction failure.
    assert not (ws / "synthesis" / "literature_review.md").exists()

    class _BoomSynthesize:
        def __init__(self, retriever=None, **kw):
            pass

        def synthesize(self, **kw):
            raise RuntimeError("synthesize boom")

    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _BoomSynthesize)
    with pytest.raises(RuntimeError, match="synthesize boom"):
        synth_mod.run_synthesis(
            protocol=protocol,
            retriever=object(),
            synthesis_dir=ws / "synthesis2",
        )
    assert not (ws / "synthesis2" / "literature_review.md").exists()
    # An empty-as-success mapping (catch + DONE/0) would fail both raises.
