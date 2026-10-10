"""Focused HCM-04i tests for the neutral matrix stage.

Stage 7 (dynamic protocol matrix extraction over the vector-indexed
corpus) lives in ``scholar_harness.pipeline.matrix``; the orchestrator
delegates and maps the outcome identically. Every test is hermetic
(``tmp_path`` only, no network; retriever/extractor are faked, never a
real Chroma backend) and asserts zero behavior change: verbatim
retriever/extractor construction, byte-identical ``literature/``
publication, identical results mapping, carried retriever binding for
Stage 9, no audit or registry writes, and identical error propagation.

Mapping to the HCM-04i packet (A1-8/B7-12/C13-16/D14-16):

- HCM4I-01 shim identity (``orch.X is stage.X`` for all four names)
- HCM4I-02 construction parity (db_path/collection/embedder + protocol passthrough)
- HCM4I-03 outcome carries retriever for Stage 9 (same object to Matrix + Synth)
- HCM4I-04 results mapping identical (DONE + rows len)
- HCM4I-05 no audit or registry from the stage
- HCM4I-06 MinimalIndexer compat (refusal shapes still bind)
- HCM4I-07 move-not-duplicate (Stage 7 region has no inline kit logic)
- HCM4I-08 minimal signature + outcome names + transport guard
- HCM4I-09 byte parity probe (orch vs direct stage csv/json bytes agree)
- HCM4I-10 error propagation (kit raise propagates, no fabricated DONE)

Negatives (each tmp_path-only, byte-identical restored):

- NEG-01 refused-row routing (indexer limbs passed verbatim, no fallback)
- NEG-02 binding break (outcome.retriever must be the Matrix-seen object)
- NEG-03 serialization/order change (row order + csv/json bytes preserved)
- NEG-04 empty-as-success (kit raise is never mapped to DONE/0 rows)
- NEG-05 seam bypass (orchestator-namespace patches take effect)

Carry-forward debt TD-HCM-TEST-SEAMS x3 untouched
(``SearchEngine`` / ``Deduplicator`` / ``DocumentVerifier`` shims stay);
this packet adds two NARROW seams only (``ScholarRetriever`` /
``MatrixExtractor`` via ``orchestrator.__dict__`` honoring, HCM-04b
precedent). No broad layer, no other seams. TD-E3-CURRENTNESS-01 and the
MCP docs failure stay base-proven and untouched.
"""

from __future__ import annotations

import asyncio
import csv
import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scholar_harness import orchestrator as orch
from scholar_harness.pipeline import matrix as mat_mod

FIXTURE_WORKSPACE_ID = "WSP-" + "0" * 32


def _record_workspace_identity(ws: Path, project_id: str) -> None:
    (ws / "project.json").write_text(
        json.dumps(
            {"project_id": project_id, "registered_workspace_id": FIXTURE_WORKSPACE_ID}
        ),
        encoding="utf-8",
    )


def _write_protocol(ws: Path, slug: str = "matrix-stage-test") -> Path:
    from scholar_protocol.canonical import canonical_json
    from scholar_protocol.compiler import compile_protocol
    from scholar_protocol.intent import IntentPacket

    data = {
        "protocol_id": "matrix-stage",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": slug,
        "playbook_type": "DESIGN_SCIENCE",
        "title": "Matrix Stage Parity",
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


class _FakeIndexerCompat:
    collection_name = "scholar_docs"
    embedder_kwargs = {
        "provider": "sentence-transformers",
        "model_name": "all-MiniLM-L6-v2",
    }

    def get_collection_count(self) -> int:
        return 0


SEEN_RETRIEVER_KWARGS: list[dict] = []
SEEN_MATRIX_RETRIEVERS: list[object] = []
SEEN_EXTRACTOR_PROTOCOLS: list[object] = []
SEEN_OUTPUT_DIRS: list[object] = []


class _RecorderRetriever:
    def __init__(self, **kwargs):
        SEEN_RETRIEVER_KWARGS.append(dict(kwargs))
        self.kw = kwargs


class _DeterministicMatrix:
    """Fake extractor that writes deterministic csv/json bytes."""

    def __init__(self, protocol=None, retriever=None, **kw):
        self.protocol = protocol
        self.retriever = retriever
        SEEN_MATRIX_RETRIEVERS.append(retriever)
        SEEN_EXTRACTOR_PROTOCOLS.append(protocol)

    def extract_all(self, output_dir):
        from pathlib import Path as _P

        out = _P(output_dir)
        SEEN_OUTPUT_DIRS.append(out)
        out.mkdir(parents=True, exist_ok=True)
        rows = [
            {"study_id": "STU-001", "throughput": "10 ops/s"},
            {"study_id": "STU-002", "throughput": "20 ops/s"},
        ]
        json_path = out / "synthesis_matrix.json"
        json_path.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
        csv_path = out / "synthesis_matrix.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            for r in rows:
                w.writerow(r)
        # Kit also writes md as inherited side effect; mirror it so the
        # byte-parity probe covers the full publication surface.
        (out / "synthesis_matrix.md").write_text(
            "# Synthesis Matrix\n\n| Study ID |\n| :--- |\n| STU-001 |\n| STU-002 |\n",
            encoding="utf-8",
        )
        return rows, csv_path, json_path


def _clear_seen():
    SEEN_RETRIEVER_KWARGS.clear()
    SEEN_MATRIX_RETRIEVERS.clear()
    SEEN_EXTRACTOR_PROTOCOLS.clear()
    SEEN_OUTPUT_DIRS.clear()


# ---------------------------------------------------------------------------
# HCM4I-01 shim identity
# ---------------------------------------------------------------------------


def test_shim_identity_all_four_names():
    """HCM4I-01: orchestrator names ARE the stage objects (move, not copy)."""
    assert orch.ScholarRetriever is mat_mod.ScholarRetriever
    assert orch.MatrixExtractor is mat_mod.MatrixExtractor
    assert orch.run_matrix is mat_mod.run_matrix
    assert orch.MatrixOutcome is mat_mod.MatrixOutcome


def test_stage_canonical_kit_classes():
    """Stage globals are the kit classes (no vendored copy)."""
    from scholar_rag.matrix import MatrixExtractor as _KitMatrix
    from scholar_rag.retriever import ScholarRetriever as _KitRetriever

    assert mat_mod.ScholarRetriever is _KitRetriever
    assert mat_mod.MatrixExtractor is _KitMatrix
    assert mat_mod._REAL_RETRIEVER is _KitRetriever
    assert mat_mod._REAL_MATRIX is _KitMatrix


# ---------------------------------------------------------------------------
# HCM4I-02 construction parity
# ---------------------------------------------------------------------------


def test_construction_parity_db_collection_embedder_and_protocol(tmp_path, monkeypatch):
    """HCM4I-02: verbatim retriever/extractor construction + output_dir."""
    _clear_seen()
    monkeypatch.setattr(orch, "ScholarRetriever", _RecorderRetriever)
    monkeypatch.setattr(orch, "MatrixExtractor", _DeterministicMatrix)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    protocol = _load_protocol(ws)
    chroma_dir = ws / "chroma_db"
    lit_dir = ws / "literature"
    lit_dir.mkdir(parents=True)

    outcome = mat_mod.run_matrix(
        protocol=protocol,
        indexer_compat=_FakeIndexerCompat(),
        chroma_dir=chroma_dir,
        literature_dir=lit_dir,
    )

    assert len(SEEN_RETRIEVER_KWARGS) == 1
    kw = SEEN_RETRIEVER_KWARGS[0]
    assert kw["db_path"] == str(chroma_dir)
    assert kw["collection_name"] == "scholar_docs"
    assert kw["embedder_kwargs"] == {
        "provider": "sentence-transformers",
        "model_name": "all-MiniLM-L6-v2",
    }
    # Protocol passthrough: same object, not re-parsed.
    assert SEEN_EXTRACTOR_PROTOCOLS[0] is protocol
    # Output dir is the literature dir.
    assert SEEN_OUTPUT_DIRS[0] == lit_dir
    assert outcome.rows == [
        {"study_id": "STU-001", "throughput": "10 ops/s"},
        {"study_id": "STU-002", "throughput": "20 ops/s"},
    ]
    assert outcome.csv_path == lit_dir / "synthesis_matrix.csv"
    assert outcome.json_path == lit_dir / "synthesis_matrix.json"
    assert isinstance(outcome.retriever, _RecorderRetriever)


def test_indexer_compat_limbs_used_verbatim_not_defaults(tmp_path, monkeypatch):
    """NEG-01: refusal-shaped indexer limbs are passed verbatim (no fallback)."""
    _clear_seen()

    class _CustomIndexer:
        collection_name = "custom_collection"
        embedder_kwargs = {"provider": "mock", "model_name": "mock-384"}

    monkeypatch.setattr(orch, "ScholarRetriever", _RecorderRetriever)
    monkeypatch.setattr(orch, "MatrixExtractor", _DeterministicMatrix)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    protocol = _load_protocol(ws)

    mat_mod.run_matrix(
        protocol=protocol,
        indexer_compat=_CustomIndexer(),
        chroma_dir=ws / "chroma_db",
        literature_dir=ws / "literature",
    )

    kw = SEEN_RETRIEVER_KWARGS[0]
    assert kw["collection_name"] == "custom_collection"
    assert kw["embedder_kwargs"] == {"provider": "mock", "model_name": "mock-384"}
    # A mutation that hardcodes scholar_docs / sentence-transformers would fail here.


# ---------------------------------------------------------------------------
# HCM4I-05 no audit or registry
# ---------------------------------------------------------------------------


def test_stage_emits_no_audit_and_no_registry(tmp_path, monkeypatch):
    """HCM4I-05: Stage 7 emits no audit event and no registry state."""
    _clear_seen()
    monkeypatch.setattr(orch, "ScholarRetriever", _RecorderRetriever)
    monkeypatch.setattr(orch, "MatrixExtractor", _DeterministicMatrix)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    protocol = _load_protocol(ws)

    mat_mod.run_matrix(
        protocol=protocol,
        indexer_compat=_FakeIndexerCompat(),
        chroma_dir=ws / "chroma_db",
        literature_dir=ws / "literature",
    )

    assert _journal_rows(ws) == []
    assert list(ws.rglob("journal.jsonl")) == []
    assert list(ws.rglob("artifact_registry.json")) == []
    # Only the matrix publication lives under literature/.
    names = sorted(p.name for p in (ws / "literature").iterdir())
    assert "synthesis_matrix.csv" in names
    assert "synthesis_matrix.json" in names


# ---------------------------------------------------------------------------
# HCM4I-06 MinimalIndexer compat
# ---------------------------------------------------------------------------


def test_minimal_indexer_refusal_shapes_bind(tmp_path, monkeypatch):
    """HCM4I-06: MinimalIndexer refusal shapes carry collection/embedder limbs."""
    _clear_seen()
    monkeypatch.setattr(orch, "ScholarRetriever", _RecorderRetriever)
    monkeypatch.setattr(orch, "MatrixExtractor", _DeterministicMatrix)

    class MinimalIndexer:
        collection_name = "scholar_docs"
        embedder_kwargs = {
            "provider": "sentence-transformers",
            "model_name": "all-MiniLM-L6-v2",
        }

        def get_collection_count(self) -> int:
            return 0

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    protocol = _load_protocol(ws)

    outcome = mat_mod.run_matrix(
        protocol=protocol,
        indexer_compat=MinimalIndexer(),
        chroma_dir=ws / "chroma_db",
        literature_dir=ws / "literature",
    )

    assert outcome.rows != []
    assert SEEN_RETRIEVER_KWARGS[0]["collection_name"] == "scholar_docs"


# ---------------------------------------------------------------------------
# HCM4I-07 move-not-duplicate + HCM4I-08 signature/guard
# ---------------------------------------------------------------------------


def test_stage_7_region_has_no_inline_kit_logic():
    """HCM4I-07: orchestrator delegates; kit logic lives in the stage."""
    source = Path(orch.__file__).read_text(encoding="utf-8")
    region = source.split("Stage 7: Dynamic Protocol Matrix Extraction", 1)[1]
    region = region.split("Stage 8:", 1)[0]
    body = region.split('results["stages"]["matrix_rows"]', 1)[0]
    assert "ScholarRetriever(" not in body
    assert "MatrixExtractor(" not in body
    assert "extract_all(" not in body
    assert ".write_text(" not in body
    assert "csv.DictWriter" not in body
    assert "run_matrix(" in body
    assert "matrix_outcome" in body
    mapping = region.split('results["stages"]["matrix_rows"]', 1)[1]
    assert '"DONE"' in mapping
    assert "len(matrix_rows)" in mapping
    # Retriever binding for Stage 9 is retained.
    assert "retriever = matrix_outcome.retriever" in region


def test_orchestrator_source_has_no_direct_matrix_retriever_import():
    """Move-not-duplicate: orchestrator must not bind kit modules directly."""
    text = Path(orch.__file__).read_text(encoding="utf-8")
    assert "from scholar_rag.matrix import" not in text
    assert "from scholar_rag.retriever import" not in text


def test_signature_minimal_and_outcome_names():
    """HCM4I-08: minimal keyword-only quartet; outcome carries four names."""
    sig = inspect.signature(mat_mod.run_matrix)
    params = list(sig.parameters.values())
    assert [p.name for p in params] == [
        "protocol",
        "indexer_compat",
        "chroma_dir",
        "literature_dir",
    ]
    assert all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in params)
    assert all(p.default is inspect.Parameter.empty for p in params)
    import dataclasses

    assert sorted(f.name for f in dataclasses.fields(mat_mod.MatrixOutcome)) == [
        "csv_path",
        "json_path",
        "retriever",
        "rows",
    ]


def test_stage_has_no_console_transport_import():
    """HCM4I-08: neutral stage imports no console/FastAPI transport."""
    text = Path(mat_mod.__file__).read_text(encoding="utf-8")
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


def test_narrow_seams_only_two_orchestrator_fallbacks():
    """Only ScholarRetriever/MatrixExtractor consult orchestrator.__dict__."""
    text = Path(mat_mod.__file__).read_text(encoding="utf-8")
    assert text.count("orchestrator.__dict__.get(") == 2
    assert '"ScholarRetriever"' in text
    assert '"MatrixExtractor"' in text
    assert "_REAL_RETRIEVER" in text
    assert "_REAL_MATRIX" in text
    # No broad __dict__ snooping beyond the two narrow resolvers.
    assert "orchestrator.__dict__" not in text.replace("orchestrator.__dict__.get(", "")


# ---------------------------------------------------------------------------
# HCM4I-03/04 orchestrator delegation + retriever binding (fidelity seam)
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


SEEN_SYNTH_RETRIEVERS: list[object] = []


def _stub_upstream(monkeypatch):
    import networkx as nx

    _clear_seen()
    SEEN_SYNTH_RETRIEVERS.clear()

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

        def export_json(self, G, path):
            import json as _j

            path.write_text(
                _j.dumps({"nodes": list(G.nodes), "links": list(G.edges)}),
                encoding="utf-8",
            )

    class _FakeVis:
        def __init__(self, html_path):
            self.html_path = html_path

        def generate_html(self, G):
            Path(self.html_path).write_text("<html></html>", encoding="utf-8")

    monkeypatch.setattr(orch, "SearchEngine", _FakeEngine)
    monkeypatch.setattr(orch, "Deduplicator", _FakeDedup)
    monkeypatch.setattr(orch, "DocumentVerifier", _FakeVerifier)
    monkeypatch.setattr(orch, "ScholarRetriever", _RecorderRetriever)
    monkeypatch.setattr(orch, "MatrixExtractor", _DeterministicMatrix)
    monkeypatch.setattr(orch, "GroundedSynthesisEngine", _FakeSynth)
    monkeypatch.setattr(orch, "CitationGraphBuilder", _FakeGraph)
    monkeypatch.setattr(orch, "GraphVisualizer", _FakeVis)
    monkeypatch.setattr(
        "scholar_harness.agent_screen.cmd_prepare", lambda *a, **k: None
    )


def test_orchestrator_mapping_and_retriever_binding(tmp_path, monkeypatch):
    """HCM4I-03/04: DONE mapping + SAME retriever to Matrix and Synthesis."""
    _stub_upstream(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    _record_workspace_identity(ws, "matrix-stage-test")

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
    mapping = results["stages"]["matrix_rows"]
    assert mapping == {"status": "DONE", "rows": 2}
    # Retriever binding: Matrix-seen object IS Synthesis-seen object.
    assert SEEN_MATRIX_RETRIEVERS and SEEN_SYNTH_RETRIEVERS
    assert SEEN_MATRIX_RETRIEVERS[-1] is SEEN_SYNTH_RETRIEVERS[-1]
    # NEG-02 companion: a binding break (different objects) would fail here.


def test_orchestrator_stage_resolves_both_patch_sites_unmodified(tmp_path, monkeypatch):
    """NEG-05: fidelity patch sites work UNMODIFIED through the stage."""
    # Patch ONLY the orchestrator namespace (exact fidelity :193-194 lines).
    _clear_seen()
    SEEN_SYNTH_RETRIEVERS.clear()
    monkeypatch.setattr(orch, "ScholarRetriever", _RecorderRetriever)
    monkeypatch.setattr(orch, "MatrixExtractor", _DeterministicMatrix)

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    protocol = _load_protocol(ws)

    # Direct stage call honors the orchestrator-namespace overrides.
    outcome = mat_mod.run_matrix(
        protocol=protocol,
        indexer_compat=_FakeIndexerCompat(),
        chroma_dir=ws / "chroma_db",
        literature_dir=ws / "literature",
    )
    assert isinstance(outcome.retriever, _RecorderRetriever)
    assert SEEN_MATRIX_RETRIEVERS[0] is outcome.retriever
    # A seam bypass (stage hardcoding the kit class) would fail both asserts.


# ---------------------------------------------------------------------------
# HCM4I-09 byte parity probe + NEG-03 order preservation
# ---------------------------------------------------------------------------


def test_orchestrator_mapping_matches_direct_stage_bytes(tmp_path, monkeypatch):
    """HCM4I-09/NEG-03: orch delegation maps identically; csv/json bytes agree."""
    _stub_upstream(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    _record_workspace_identity(ws, "matrix-stage-test")

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
    mapping = results["stages"]["matrix_rows"]
    assert mapping["status"] == "DONE"
    assert mapping["rows"] == 2

    orch_csv = (ws / "literature" / "synthesis_matrix.csv").read_bytes()
    orch_json = (ws / "literature" / "synthesis_matrix.json").read_bytes()

    # Byte-identical probe: direct stage over the same protocol/indexer
    # reproduces the orchestrator's files byte for byte (restore).
    _clear_seen()
    # Re-apply the deterministic fakes for the direct call (cleared above).
    monkeypatch.setattr(orch, "ScholarRetriever", _RecorderRetriever)
    monkeypatch.setattr(orch, "MatrixExtractor", _DeterministicMatrix)
    direct_lit = tmp_path / "direct-literature"
    direct_chroma = tmp_path / "direct-chroma"
    protocol = _load_protocol(ws)
    direct_outcome = mat_mod.run_matrix(
        protocol=protocol,
        indexer_compat=_FakeIndexerCompat(),
        chroma_dir=direct_chroma,
        literature_dir=direct_lit,
    )
    assert direct_outcome.rows is not None
    assert len(direct_outcome.rows) == mapping["rows"]
    assert (direct_lit / "synthesis_matrix.csv").read_bytes() == orch_csv
    assert (direct_lit / "synthesis_matrix.json").read_bytes() == orch_json
    # Order preserved: STU-001 before STU-002 in both serializations.
    direct_rows = json.loads((direct_lit / "synthesis_matrix.json").read_text())
    assert [r["study_id"] for r in direct_rows] == ["STU-001", "STU-002"]
    orch_rows = json.loads((ws / "literature" / "synthesis_matrix.json").read_text())
    assert [r["study_id"] for r in orch_rows] == ["STU-001", "STU-002"]
    # A serialization/order mutation would fail the byte + order asserts.


# ---------------------------------------------------------------------------
# HCM4I-10 error propagation + NEG-04 empty-as-success
# ---------------------------------------------------------------------------


def test_kit_raise_propagates_no_fabricated_done(tmp_path, monkeypatch):
    """HCM4I-10/NEG-04: kit raise propagates; never mapped to DONE/0 rows."""
    _clear_seen()

    class _BoomRetriever:
        def __init__(self, **kw):
            raise RuntimeError("retriever boom")

    class _BoomMatrix:
        def __init__(self, protocol=None, retriever=None, **kw):
            raise RuntimeError("extractor boom")

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    protocol = _load_protocol(ws)

    monkeypatch.setattr(orch, "ScholarRetriever", _BoomRetriever)
    monkeypatch.setattr(orch, "MatrixExtractor", _DeterministicMatrix)
    with pytest.raises(RuntimeError, match="retriever boom"):
        mat_mod.run_matrix(
            protocol=protocol,
            indexer_compat=_FakeIndexerCompat(),
            chroma_dir=ws / "chroma_db",
            literature_dir=ws / "literature",
        )
    # No publication on retriever failure.
    assert not (ws / "literature" / "synthesis_matrix.json").exists()

    monkeypatch.setattr(orch, "ScholarRetriever", _RecorderRetriever)
    monkeypatch.setattr(orch, "MatrixExtractor", _BoomMatrix)
    with pytest.raises(RuntimeError, match="extractor boom"):
        mat_mod.run_matrix(
            protocol=protocol,
            indexer_compat=_FakeIndexerCompat(),
            chroma_dir=ws / "chroma_db",
            literature_dir=ws / "literature2",
        )

    class _BoomExtract:
        def __init__(self, protocol=None, retriever=None, **kw):
            self.retriever = retriever

        def extract_all(self, output_dir):
            raise RuntimeError("extract_all boom")

    monkeypatch.setattr(orch, "MatrixExtractor", _BoomExtract)
    with pytest.raises(RuntimeError, match="extract_all boom"):
        mat_mod.run_matrix(
            protocol=protocol,
            indexer_compat=_FakeIndexerCompat(),
            chroma_dir=ws / "chroma_db",
            literature_dir=ws / "literature3",
        )
    # An empty-as-success mapping (catch + DONE/0) would fail all three raises.
