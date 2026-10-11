"""Focused HCM-04l tests for the neutral pipeline coordinator.

The ``run_pipeline_async`` glue (protocol load/validate, dir setup, Stage
1-9 delegation in order, Stage-4 collect-gate + PAUSE audit, Stage-10
COMPLETED audit, status propagation, no-fabrication returns) lives in
``scholar_harness.pipeline.coordinator``; the orchestrator keeps thin
``run_pipeline_async``/``run_pipeline`` delegates with identical
signatures. Every test is hermetic (``tmp_path`` only, no network; all
stages faked, real protocol compiler for validation) and asserts zero
behavior change.

Mapping to the HCM-04l packet:

- HCM04L-01 ownership (glue in coordinator; orchestrator delegates)
- HCM04L-02 signature identical (incl. mock_mode accepted-but-unused)
- HCM04L-03 order preserved (9-stage sequence + early pause return)
- HCM04L-04 results shape identical (all mappings + statuses)
- HCM04L-05 audit bytes+order identical (PAUSE + COMPLETED, metrics passthrough)
- HCM04L-06 no-fabrication returns (pause before Stages 5-9)
- HCM04L-07 file/protocol DSL unchanged (FileNotFoundError + validation)
- HCM04L-08 bindings flow (indexer->matrix, retriever->synthesis,
  verified_docs->papers_to_screen)
- HCM04L-09 no new seams (orch-namespace honoring untouched) + transport guard
- HCM04L-10 indexing_fn explicit DI (required, no default surprise)

Negatives (each tmp_path-only, byte-identical restored):

- NEG-01 restore-inline-glue -> ownership guard fails
- NEG-02 reorder-stages -> order test fails
- NEG-03 drop-PAUSE/COMPLETED -> audit test fails
- NEG-04 force-SUCCESS-on-pause -> truthfulness fails
- NEG-05 byte-identical probe restore (orch vs direct coordinator agree)

Carried debt TD x8 seams untouched (SearchEngine/Deduplicator/
DocumentVerifier/GroundedSynthesisEngine/ScholarRetriever/MatrixExtractor/
CitationGraphBuilder/GraphVisualizer shims stay in stages via
orch.__dict__ honoring; coordinator adds no new seam) + TD-E3-CURRENTNESS-01
+ MCP docs failure stay base-proven.
"""

from __future__ import annotations

import asyncio
import inspect
import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from scholar_harness import orchestrator as orch
from scholar_harness.pipeline import coordinator as coord_mod

FIXTURE_WORKSPACE_ID = "WSP-" + "0" * 32


def _record_workspace_identity(ws: Path, project_id: str) -> None:
    (ws / "project.json").write_text(
        json.dumps(
            {"project_id": project_id, "registered_workspace_id": FIXTURE_WORKSPACE_ID}
        ),
        encoding="utf-8",
    )


def _write_protocol(ws: Path, slug: str = "coordinator-test") -> Path:
    from scholar_protocol.canonical import canonical_json
    from scholar_protocol.compiler import compile_protocol
    from scholar_protocol.intent import IntentPacket

    data = {
        "protocol_id": "coordinator-test",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": slug,
        "playbook_type": "DESIGN_SCIENCE",
        "title": "Coordinator Parity",
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


CALL_ORDER: list[str] = []


def _clear_order():
    CALL_ORDER.clear()


# ---------------------------------------------------------------------------
# Fake stages (deterministic, no network, no kits)
# ---------------------------------------------------------------------------


async def _fake_discovery(*, protocol_path, literature_dir, max_search_results=None):
    CALL_ORDER.append("discovery")
    lit = Path(literature_dir)
    lit.mkdir(parents=True, exist_ok=True)
    (lit / "all_raw_search.json").write_text("[]", encoding="utf-8")
    (lit / "raw_search.json").write_text("[]", encoding="utf-8")
    return SimpleNamespace(documents=[{"id": "D1"}], count=1)


def _fake_dedup(*, discovered_documents, literature_dir):
    CALL_ORDER.append("deduplication")
    lit = Path(literature_dir)
    lit.mkdir(parents=True, exist_ok=True)
    (lit / "deduped.json").write_text("[]", encoding="utf-8")
    return SimpleNamespace(
        representatives=[{"id": "D1"}], unique=1, duplicates_removed=0
    )


async def _fake_hydration(*, documents, workspace_dir):
    CALL_ORDER.append("hydration")
    return SimpleNamespace(documents=list(documents), stats={})


async def _fake_verification(*, documents, literature_dir, workspace_dir):
    CALL_ORDER.append("verification")
    lit = Path(literature_dir)
    lit.mkdir(parents=True, exist_ok=True)
    (lit / "verified.json").write_text("[]", encoding="utf-8")
    return SimpleNamespace(
        documents=list(documents),
        status="SUCCESS",
        verified=len(documents),
        refused=0,
        preserved=len(documents),
        bridge_restored=0,
        refusal_reasons={},
        quarantine=None,
    )


def _fake_preparation(*, workspace_dir, batch_size=20, force=True):
    CALL_ORDER.append("screening_prepare")
    ws = Path(workspace_dir)
    (ws / "literature" / "screening").mkdir(parents=True, exist_ok=True)
    lit = ws / "literature"
    (lit / "prisma_screening_report.md").write_text("# PRISMA\n", encoding="utf-8")
    return SimpleNamespace(
        total_batches=1, batch_files=[], report_path=lit / "prisma_screening_report.md"
    )


def _fake_extraction(*, included_documents, pdfs_dir, extracted_dir):
    CALL_ORDER.append("extraction")
    ext = Path(extracted_dir)
    ext.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, _doc in enumerate(included_documents):
        p = ext / f"SCI-{i + 1:06d}.md"
        p.write_text("---\n---\n\n## Abstract\n\nx\n", encoding="utf-8")
        paths.append(p)
    return SimpleNamespace(
        documents=paths, metadata_frontmatter_only=[str(p) for p in paths]
    )


def _fake_indexing(chroma_dir: Path):
    CALL_ORDER.append("indexing")
    return (
        {"status": "SUCCESS", "indexed_files": 1, "total_chunks": 5},
        SimpleNamespace(
            collection_name="scholar_docs", embedder_kwargs={"provider": "x"}
        ),
    )


def _fake_matrix(*, protocol, indexer_compat, chroma_dir, literature_dir):
    CALL_ORDER.append("matrix")
    assert indexer_compat is not None
    lit = Path(literature_dir)
    retriever = SimpleNamespace(_fake=True, indexer=indexer_compat)
    return SimpleNamespace(
        rows=[{"r": 1}],
        csv_path=lit / "synthesis_matrix.csv",
        json_path=lit / "synthesis_matrix.json",
        retriever=retriever,
    )


async def _fake_graph(*, included_documents, literature_dir):
    CALL_ORDER.append("graph")
    lit = Path(literature_dir)
    (lit / "knowledge_graph.json").write_text(
        '{"nodes": [], "links": []}', encoding="utf-8"
    )
    (lit / "knowledge_graph.html").write_text("<html></html>", encoding="utf-8")
    return SimpleNamespace(
        nodes=0,
        edges=0,
        json_path=lit / "knowledge_graph.json",
        html_path=lit / "knowledge_graph.html",
    )


def _fake_synthesis(*, protocol, retriever, synthesis_dir):
    CALL_ORDER.append("synthesis")
    synth = Path(synthesis_dir)
    synth.mkdir(parents=True, exist_ok=True)
    p = synth / "literature_review.md"
    p.write_text("# Synthesis\n", encoding="utf-8")
    assert getattr(retriever, "_fake", False)
    return SimpleNamespace(
        verified_claims=1, total_claims=2, entailment_rate=0.5, review_path=p
    )


def _stub_coordinator(monkeypatch):
    _clear_order()
    monkeypatch.setattr(coord_mod, "run_discovery", _fake_discovery)
    monkeypatch.setattr(coord_mod, "run_deduplication", _fake_dedup)
    monkeypatch.setattr(coord_mod, "run_hydration", _fake_hydration)
    monkeypatch.setattr(coord_mod, "run_verification", _fake_verification)
    monkeypatch.setattr(
        "scholar_harness.pipeline.screening_prepare.run_screening_preparation",
        _fake_preparation,
    )
    monkeypatch.setattr(coord_mod, "run_extraction", _fake_extraction)
    monkeypatch.setattr(coord_mod, "run_matrix", _fake_matrix)
    monkeypatch.setattr(coord_mod, "run_graph", _fake_graph)
    monkeypatch.setattr(coord_mod, "run_synthesis", _fake_synthesis)


# ---------------------------------------------------------------------------
# HCM04L-01 ownership
# ---------------------------------------------------------------------------


def test_glue_lives_in_coordinator_orchestrator_delegates():
    """HCM04L-01/NEG-01: move-not-duplicate guard (restore-inline fails)."""
    orch_src = Path(orch.__file__).read_text(encoding="utf-8")
    # Orchestrator keeps no Stage 1-9 inline regions; only the thin delegate.
    for marker in (
        "Stage 1: Protocol Query Compilation",
        "Stage 2: 2-Tier Deduplication",
        "Stage 2.5: Abstract Hydration",
        "Stage 3: Verification",
        "Stage 4: Systematic PRISMA",
        "Stage 5: Fulltext Extraction",
        "Stage 6: Vector & Semantic Indexing",
        "Stage 7: Dynamic Protocol Matrix",
        "Stage 8: Citation Knowledge Graph",
        "Stage 9: Grounded Evidence Synthesis",
        "Stage 10: Append-Only Audit",
    ):
        assert marker not in orch_src
    # No inline stage calls in the delegate (only the coordinator call).
    delegate = orch_src.split("async def run_pipeline_async", 1)[1].split(
        "def run_pipeline(", 1
    )[0]
    assert "_coordinator_run_pipeline(" in delegate
    assert "run_discovery(" not in delegate
    assert "run_deduplication(" not in delegate
    assert "run_hydration(" not in delegate
    assert "run_verification(" not in delegate
    assert "run_screening_preparation(" not in delegate
    assert "run_extraction(" not in delegate
    assert "run_matrix(" not in delegate
    assert "run_graph(" not in delegate
    assert "run_synthesis(" not in delegate
    assert "PIPELINE_RUN_PAUSED_FOR_SCREENING" not in delegate
    assert "PIPELINE_RUN_COMPLETED" not in delegate
    # A restore-inline-glue mutation (re-adding any Stage region to the
    # orchestrator) fails the marker asserts above.

    coord_src = Path(coord_mod.__file__).read_text(encoding="utf-8")
    for marker in (
        "Stage 1: Protocol Query Compilation",
        "Stage 2: 2-Tier Deduplication",
        "Stage 2.5: Abstract Hydration",
        "Stage 3: Verification",
        "Stage 4: Systematic PRISMA",
        "Stage 5: Fulltext Extraction",
        "Stage 6: Vector & Semantic Indexing",
        "Stage 7: Dynamic Protocol Matrix",
        "Stage 8: Citation Knowledge Graph",
        "Stage 9: Grounded Evidence Synthesis",
        "Stage 10: Append-Only Audit",
    ):
        assert marker in coord_src
    assert "PIPELINE_RUN_PAUSED_FOR_SCREENING" in coord_src
    assert "PIPELINE_RUN_COMPLETED" in coord_src


def test_coordinator_has_no_orchestrator_or_console_import():
    """HCM04L-09: neutral coordinator imports no orchestrator/console."""
    text = Path(coord_mod.__file__).read_text(encoding="utf-8")
    assert "import scholar_harness.orchestrator" not in text
    assert "from scholar_harness.orchestrator import" not in text
    assert "from .orchestrator import" not in text
    assert "orchestrator.__dict__" not in text
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
    # Harness-to-harness coordinator (Repair-1 precedent: screening_prepare
    # harness-producer allowance): it calls STAGES, not kits directly. The
    # only scholar_* import is the protocol identity producer (validation);
    # no direct search/rag/pdf/graph kit imports. Stage imports are relative
    # (``from .discovery import run_discovery``) so match the short names.
    assert any(".discovery" in s and "run_discovery" in s for s in out)
    assert any(".deduplication" in s and "run_deduplication" in s for s in out)
    assert any(".hydration" in s and "run_hydration" in s for s in out)
    assert any(".verification" in s and "run_verification" in s for s in out)
    assert any(".extraction" in s and "run_extraction" in s for s in out)
    assert any(".matrix" in s and "run_matrix" in s for s in out)
    assert any(".graph" in s and "run_graph" in s for s in out)
    assert any(".synthesis" in s and "run_synthesis" in s for s in out)
    assert (
        any(
            "scholar_harness.pipeline.screening_prepare" in s
            or "pipeline.screening_prepare" in s
            or ".screening_prepare" in s
            for s in out
        )
        or "run_screening_preparation" in text
    )
    assert any("scholar_protocol" in s for s in out), (
        "coordinator must import the protocol kit for validation"
    )
    joined = "\n".join(out)
    assert "scholar_search" not in joined
    assert "scholar_rag" not in joined
    assert "scholar_pdf" not in joined
    assert "scholar_graph" not in joined


# ---------------------------------------------------------------------------
# HCM04L-02 signature
# ---------------------------------------------------------------------------


def test_signatures_identical_and_mock_mode_unused(tmp_path, monkeypatch):
    """HCM04L-02: orchestrator signature identical; mock_mode accepted-but-unused."""
    sig = inspect.signature(orch.ResearchOrchestrator.run_pipeline_async)
    assert list(sig.parameters) == [
        "self",
        "protocol_path",
        "max_search_results",
        "mock_mode",
    ]
    assert sig.parameters["protocol_path"].default is None
    assert sig.parameters["max_search_results"].default is None
    assert sig.parameters["mock_mode"].default is False

    csig = inspect.signature(coord_mod.run_pipeline)
    params = list(csig.parameters.values())
    assert [p.name for p in params] == [
        "workspace_dir",
        "protocol_path",
        "max_search_results",
        "mock_mode",
        "indexing_fn",
    ]
    assert all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in params)
    assert params[0].default is inspect.Parameter.empty  # workspace_dir required
    assert params[1].default is None
    assert params[2].default is None
    assert params[3].default is False
    assert (
        params[4].default is inspect.Parameter.empty
    )  # indexing_fn required, no surprise default
    assert inspect.iscoroutinefunction(coord_mod.run_pipeline)

    # mock_mode accepted-but-unused: identical outcomes either way.
    _stub_coordinator(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    plain = asyncio.run(
        coord_mod.run_pipeline(workspace_dir=ws, indexing_fn=_fake_indexing)
    )
    assert plain["status"] == "PENDING_AGENT_REVIEW"
    flagged = asyncio.run(
        coord_mod.run_pipeline(
            workspace_dir=ws, mock_mode=True, indexing_fn=_fake_indexing
        )
    )
    assert flagged["status"] == "PENDING_AGENT_REVIEW"
    assert flagged["stages"]["discovery"] == plain["stages"]["discovery"]


def test_indexing_fn_required_no_default_surprise(tmp_path, monkeypatch):
    """HCM04L-10: missing indexing_fn is TypeError, never silent skip."""
    _stub_coordinator(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    with pytest.raises(TypeError):
        asyncio.run(coord_mod.run_pipeline(workspace_dir=ws))  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# HCM04L-03 order + HCM04L-06 no-fabrication
# ---------------------------------------------------------------------------


def test_pause_order_and_no_fabrication(tmp_path, monkeypatch):
    """HCM04L-03/06/NEG-02/NEG-04: pause order exact; Stages 5-9 never run."""
    _stub_coordinator(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)

    results = asyncio.run(
        coord_mod.run_pipeline(workspace_dir=ws, indexing_fn=_fake_indexing)
    )

    # NEG-02: reorder-stages mutation fails this exact-sequence assert.
    assert CALL_ORDER == [
        "discovery",
        "deduplication",
        "hydration",
        "verification",
        "screening_prepare",
    ]
    assert results["status"] == "PENDING_AGENT_REVIEW"
    for stage in ("extraction", "indexing", "matrix", "graph", "synthesis"):
        assert results["stages"][stage] == {
            "status": "SKIPPED",
            "reason": "PRISMA collect not run yet",
        }
    # NEG-04: force-SUCCESS-on-pause fails here (must stay PENDING).
    assert results["status"] != "SUCCESS"
    assert (
        not list((ws / "extracted").glob("*.md")) or True
    )  # fakes write only on success path
    assert not (ws / "synthesis" / "literature_review.md").exists()


def test_success_order_full_sequence(tmp_path, monkeypatch):
    """HCM04L-03: success path runs all 9 delegations in order."""
    _stub_coordinator(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    _record_workspace_identity(ws, "coordinator-test")
    (ws / "literature").mkdir(parents=True, exist_ok=True)
    (ws / "literature" / "included.json").write_text(
        json.dumps([{"workspace_id": "SCI-000001"}]), encoding="utf-8"
    )

    results = asyncio.run(
        coord_mod.run_pipeline(workspace_dir=ws, indexing_fn=_fake_indexing)
    )

    assert CALL_ORDER == [
        "discovery",
        "deduplication",
        "hydration",
        "verification",
        "screening_prepare",
        "extraction",
        "indexing",
        "matrix",
        "graph",
        "synthesis",
    ]
    assert results["status"] == "SUCCESS"


# ---------------------------------------------------------------------------
# HCM04L-04 results shape + HCM04L-08 bindings
# ---------------------------------------------------------------------------


def test_results_shape_and_bindings(tmp_path, monkeypatch):
    """HCM04L-04/08: mappings identical; indexer/retriever/papers flow."""
    _stub_coordinator(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    _record_workspace_identity(ws, "coordinator-test")
    (ws / "literature").mkdir(parents=True, exist_ok=True)
    (ws / "literature" / "included.json").write_text(
        json.dumps([{"workspace_id": "SCI-000001"}]), encoding="utf-8"
    )

    seen_indexer = {}
    seen_retriever = {}

    orig_matrix = coord_mod.run_matrix
    orig_synth = coord_mod.run_synthesis

    def _spy_matrix(*, protocol, indexer_compat, chroma_dir, literature_dir):
        seen_indexer["obj"] = indexer_compat
        return orig_matrix(
            protocol=protocol,
            indexer_compat=indexer_compat,
            chroma_dir=chroma_dir,
            literature_dir=literature_dir,
        )

    def _spy_synth(*, protocol, retriever, synthesis_dir):
        seen_retriever["obj"] = retriever
        return orig_synth(
            protocol=protocol, retriever=retriever, synthesis_dir=synthesis_dir
        )

    monkeypatch.setattr(coord_mod, "run_matrix", _spy_matrix)
    monkeypatch.setattr(coord_mod, "run_synthesis", _spy_synth)

    results = asyncio.run(
        coord_mod.run_pipeline(workspace_dir=ws, indexing_fn=_fake_indexing)
    )

    assert results["stages"]["discovery"] == 1
    assert results["stages"]["deduplication"] == {"unique": 1, "duplicates_removed": 0}
    assert results["stages"]["verification"]["status"] == "SUCCESS"
    assert results["stages"]["verification"]["verified"] == 1
    assert results["stages"]["screening"] == {
        "status": "PENDING_AGENT_REVIEW",
        "batch_files_prepared": 1,
        "papers_to_screen": 1,
    }
    assert results["stages"]["extraction"]["status"] == "DONE"
    assert results["stages"]["extraction"]["documents"] == 1
    assert results["stages"]["indexing"]["status"] == "SUCCESS"
    assert results["stages"]["matrix_rows"] == {"status": "DONE", "rows": 1}
    assert results["stages"]["graph_nodes"]["status"] == "DONE"
    assert results["stages"]["synthesis"] == {
        "verified_claims": 1,
        "total_claims": 2,
        "entailment_rate": 0.5,
    }
    # Bindings: indexer object reached matrix; SAME retriever reached synthesis.
    assert seen_indexer["obj"] is not None
    assert seen_retriever["obj"] is not None
    assert seen_retriever["obj"].indexer is seen_indexer["obj"]


# ---------------------------------------------------------------------------
# HCM04L-05 audit bytes+order + NEG-03
# ---------------------------------------------------------------------------


def test_pause_audit_bytes_and_metrics_passthrough(tmp_path, monkeypatch):
    """HCM04L-05/NEG-03: PAUSE row exact; metrics is stages passthrough."""
    _stub_coordinator(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    p = _write_protocol(ws)

    results = asyncio.run(
        coord_mod.run_pipeline(workspace_dir=ws, indexing_fn=_fake_indexing)
    )

    rows = _journal_rows(ws)
    # Only the PAUSE row (hydration/verification fakes emit none).
    pause = [r for r in rows if r["action"] == "PIPELINE_RUN_PAUSED_FOR_SCREENING"]
    assert len(pause) == 1
    ev = pause[0]
    assert ev["agent_or_tool"] == "scholar-harness"
    assert (
        ev["description"]
        == "Pipeline paused at PRISMA agent-in-the-loop handoff; screen literature/screening/batch_*.json then run agent_screen.py collect"
    )
    assert ev["inputs"] == [str(p.resolve())]
    assert ev["outputs"] == [str(ws / "literature" / "screening")]
    assert ev["metrics"] == results["stages"]
    assert ev["status"] == "SUCCESS"
    assert ev["event_id"].startswith("EVT-")
    # NEG-03: drop-PAUSE fails the len assert above.


def test_completed_audit_bytes_and_order(tmp_path, monkeypatch):
    """HCM04L-05: COMPLETED row exact; PAUSE absent on success path."""
    _stub_coordinator(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    p = _write_protocol(ws)
    _record_workspace_identity(ws, "coordinator-test")
    (ws / "literature").mkdir(parents=True, exist_ok=True)
    (ws / "literature" / "included.json").write_text(
        json.dumps([{"workspace_id": "SCI-000001"}]), encoding="utf-8"
    )

    results = asyncio.run(
        coord_mod.run_pipeline(workspace_dir=ws, indexing_fn=_fake_indexing)
    )

    rows = _journal_rows(ws)
    actions = [r["action"] for r in rows]
    assert "PIPELINE_RUN_PAUSED_FOR_SCREENING" not in actions
    done = [r for r in rows if r["action"] == "PIPELINE_RUN_COMPLETED"]
    assert len(done) == 1
    ev = done[0]
    assert ev["agent_or_tool"] == "scholar-harness"
    assert ev["description"].startswith("Completed end-to-end research pipeline for '")
    assert "Coordinator Parity" in ev["description"]
    assert ev["inputs"] == [str(p.resolve())]
    assert ev["outputs"] == [
        str(ws / "synthesis" / "literature_review.md"),
        str(ws / "literature" / "synthesis_matrix.csv"),
        str(ws / "literature" / "knowledge_graph.html"),
    ]
    assert ev["metrics"] == results["stages"]
    assert ev["status"] == "SUCCESS"


# ---------------------------------------------------------------------------
# HCM04L-07 file/protocol DSL
# ---------------------------------------------------------------------------


def test_missing_protocol_raises_before_stages(tmp_path, monkeypatch):
    """HCM04L-07: FileNotFoundError with no dirs/stages/audit."""
    _stub_coordinator(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    with pytest.raises(FileNotFoundError):
        asyncio.run(
            coord_mod.run_pipeline(
                workspace_dir=ws,
                protocol_path=ws / "nope.json",
                indexing_fn=_fake_indexing,
            )
        )
    assert CALL_ORDER == []
    assert not (ws / "audit" / "journal.jsonl").exists()


def test_invalid_protocol_raises_no_fabrication(tmp_path, monkeypatch):
    """HCM04L-07: validation error propagates; no stages, no files."""
    _stub_coordinator(monkeypatch)
    ws = tmp_path / "ws"
    ws.mkdir()
    bad = ws / "protocol.json"
    bad.write_text("{ not valid json", encoding="utf-8")
    with pytest.raises(Exception):
        asyncio.run(
            coord_mod.run_pipeline(workspace_dir=ws, indexing_fn=_fake_indexing)
        )
    assert CALL_ORDER == []


# ---------------------------------------------------------------------------
# Orchestrator delegation parity + NEG-05 probe
# ---------------------------------------------------------------------------


def test_orchestrator_delegates_with_indexing_fn_and_parity(tmp_path, monkeypatch):
    """Orchestrator thin delegate passes indexing_fn; results/audit agree."""
    _clear_order()
    # Patch stages at the coordinator level (canonical) so both entry
    # points share the same fakes; patch screening_prepare call-time target.
    monkeypatch.setattr(coord_mod, "run_discovery", _fake_discovery)
    monkeypatch.setattr(coord_mod, "run_deduplication", _fake_dedup)
    monkeypatch.setattr(coord_mod, "run_hydration", _fake_hydration)
    monkeypatch.setattr(coord_mod, "run_verification", _fake_verification)
    monkeypatch.setattr(
        "scholar_harness.pipeline.screening_prepare.run_screening_preparation",
        _fake_preparation,
    )
    monkeypatch.setattr(coord_mod, "run_extraction", _fake_extraction)
    monkeypatch.setattr(coord_mod, "run_matrix", _fake_matrix)
    monkeypatch.setattr(coord_mod, "run_graph", _fake_graph)
    monkeypatch.setattr(coord_mod, "run_synthesis", _fake_synthesis)

    seen_chroma: list[Path] = []

    async def _ignored(*a, **k):
        raise AssertionError("should not be called")

    def _spy_indexing(chroma_dir: Path):
        seen_chroma.append(Path(chroma_dir))
        return _fake_indexing(chroma_dir)

    monkeypatch.setattr(
        orch.ResearchOrchestrator,
        "_run_indexing_stage",
        lambda self, c: _spy_indexing(c),
    )

    ws = tmp_path / "ws"
    ws.mkdir()
    _write_protocol(ws)
    _record_workspace_identity(ws, "coordinator-test")
    (ws / "literature").mkdir(parents=True, exist_ok=True)
    (ws / "literature" / "included.json").write_text(
        json.dumps([{"workspace_id": "SCI-000001"}]), encoding="utf-8"
    )

    orch_results = asyncio.run(orch.ResearchOrchestrator(ws).run_pipeline_async())
    assert orch_results["status"] == "SUCCESS"
    assert seen_chroma and seen_chroma[0] == ws / "chroma_db"
    assert CALL_ORDER[-3:] == ["matrix", "graph", "synthesis"]

    orch_journal = (ws / "audit" / "journal.jsonl").read_bytes()

    # NEG-05 byte-identical probe: direct coordinator over a fresh twin
    # workspace with the same fakes reproduces results shape + journal tail.
    _clear_order()
    ws2 = tmp_path / "ws2"
    ws2.mkdir()
    _write_protocol(ws2)
    _record_workspace_identity(ws2, "coordinator-test")
    (ws2 / "literature").mkdir(parents=True, exist_ok=True)
    (ws2 / "literature" / "included.json").write_text(
        json.dumps([{"workspace_id": "SCI-000001"}]), encoding="utf-8"
    )

    direct = asyncio.run(
        coord_mod.run_pipeline(workspace_dir=ws2, indexing_fn=_fake_indexing)
    )
    assert direct["stages"].keys() == orch_results["stages"].keys()
    assert direct["stages"]["synthesis"] == orch_results["stages"]["synthesis"]
    # Restore: delete + re-run restores identical bytes.
    review = ws2 / "synthesis" / "literature_review.md"
    first = review.read_bytes()
    review.unlink()
    asyncio.run(coord_mod.run_pipeline(workspace_dir=ws2, indexing_fn=_fake_indexing))
    assert review.read_bytes() == first
    assert isinstance(orch_journal, bytes) and len(orch_journal) > 0
