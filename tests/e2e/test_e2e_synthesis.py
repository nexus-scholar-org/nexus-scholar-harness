"""End-to-End Phase 3 Multi-Modal Integration Test.

Validates the complete research harness lifecycle across:
1. Canonical Protocol Compilation & Fingerprinting
2. Master Orchestrator Execution across all pipeline stages
3. Full FastMCP Server Tool Invocations (scholar-agent-kit)
4. Multi-Format Academic Authoring Exports (LaTeX, Typst, Obsidian, Zotero)
"""

import json
from pathlib import Path

import pytest

import scholar_rag.cli as scholar_rag_cli
import scholar_rag.retriever as scholar_rag_retriever
from scholar_rag.chunker import text_fingerprint
from scholar_rag.cli import run_typed_index
from scholar_rag.embedder import MockEmbeddingFunction
from scholar_harness.orchestrator import ResearchOrchestrator
from scholar_harness.integrations.latex_typst import AcademicTypesettingExporter
from scholar_harness.integrations.obsidian import ObsidianVaultExporter
from scholar_harness.integrations.zotero import ZoteroBridge
from scholar_protocol.compiler import compile_protocol
from scholar_protocol.intent import IntentPacket
from scholar_protocol.canonical import canonical_json, canonical_fingerprint
from scholar_agent.server import (
    nexus_protocol_compile,
    nexus_protocol_validate,
    nexus_protocol_render_criteria,
    nexus_dedup,
    nexus_screen,
    nexus_rag_index,
    nexus_rag_query,
    nexus_rag_synthesize,
    nexus_matrix_extract,
    nexus_graph_build,
)


def _pinned_rag_commit() -> str:
    """The vendored rag-kit commit, read from the manifest that pins it.

    Provenance must name the build that actually ran, so this is derived instead
    of hard-coded: a hand-copied SHA would keep claiming a superseded rag-kit
    revision after the pin moves.
    """
    manifest = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / ".agents"
            / "plugins"
            / "nexus-scholar"
            / "plugins.json"
        ).read_text(encoding="utf-8")
    )
    pins = {p["name"]: p["default_rev"] for p in manifest["plugins"]}
    return pins["scholar-rag-kit"]


@pytest.fixture
def phase3_test_workspace(tmp_path):
    """Creates a temporary Phase 3 research workspace with a canonical protocol."""
    workspace = tmp_path / "phase3-e2e-project"
    workspace.mkdir()

    intent_dict = {
        "protocol_id": "proto-phase3-benchmark",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": "phase3-benchmark",
        "playbook_type": "DESIGN_SCIENCE",
        "title": "Benchmarking Multi-Modal Research Interfaces",
        "lead_researcher": "Dr. Agent",
        "unit_of_analysis": "Interactive Interfaces",
        "epistemological_rationale": "Empirical validation of multi-modal research synthesis workflows.",
        "research_questions": [
            {
                "text": "What is the end-to-end entailment rate across multi-modal interfaces?",
                "target_facet": "evaluation_metrics",
                "required_evidence_type": "Quantitative Benchmark",
            }
        ],
        "core_concepts": [
            {
                "concept": "Research Interface",
                "synonyms": ["orchestrator", "harness", "agent"],
            }
        ],
        "inclusion_criteria": [
            {
                "criterion": "Evaluates systematic literature workflows and empirical benchmarks",
                "maps_to_rqs": ["RQ1"],
            }
        ],
        "exclusion_criteria": [
            {
                "criterion": "Non-English studies without empirical verification",
                "reason_category": "METHODOLOGY",
                "maps_to_rqs": ["RQ1"],
            }
        ],
        "matrix_dimensions": [
            {
                "id": "throughput",
                "name": "Pipeline Throughput",
                "description": "Papers processed per second",
            },
            {
                "id": "entailment_rate",
                "name": "Entailment Rate",
                "description": "Percentage of verified claims",
            },
        ],
    }

    intent = IntentPacket.model_validate(intent_dict)
    protocol = compile_protocol(intent)

    proto_file = workspace / "protocol.json"
    proto_file.write_bytes(canonical_json(protocol))

    return workspace, proto_file


def test_phase3_e2e_full_lifecycle(phase3_test_workspace, monkeypatch):
    workspace, proto_file = phase3_test_workspace

    # =========================================================================
    # Step 1: Initialize Orchestrator & Inspect Initial State
    # =========================================================================
    orchestrator = ResearchOrchestrator(workspace)
    init_status = orchestrator.get_status()

    assert init_status["protocol_found"] is True
    assert init_status["title"] == "Benchmarking Multi-Modal Research Interfaces"
    assert init_status["playbook_type"] == "DESIGN_SCIENCE"
    assert init_status["phase"] == "PHASE_1_DISCOVERY"

    # =========================================================================
    # Step 2: Seed Mock Literature Data & Execute Pipeline Stages
    # =========================================================================
    lit_dir = workspace / "literature"
    lit_dir.mkdir(exist_ok=True)

    seed_raw = [
        {
            "title": "Benchmarking Multi-Modal Research Interfaces",
            "year": 2024,
            "provider": "openalex",
            "provider_id": "W1001",
            "external_ids": {"doi": "10.1038/interface1"},
            "authors": [{"family_name": "Smith", "given_name": "John"}],
            "abstract": "Evaluates systematic literature workflows and empirical benchmarks with 99% throughput.",
        },
        {
            "title": "Benchmarking Multi-Modal Research Interfaces",
            "year": 2024,
            "provider": "semanticscholar",
            "provider_id": "S2001",
            "external_ids": {"doi": "10.1038/interface1"},
            "authors": [{"family_name": "Smith", "given_name": "John"}],
            "abstract": "Duplicate copy from secondary provider.",
        },
        {
            "title": "Non-English Opinion Piece",
            "year": 2024,
            "provider": "crossref",
            "provider_id": "C3001",
            "external_ids": {"doi": "10.1038/editorial"},
            "authors": [{"family_name": "Dupont", "given_name": "Pierre"}],
            "abstract": "Theoretical essay without empirical verification.",
        },
    ]
    (lit_dir / "raw_search.json").write_text(json.dumps(seed_raw), encoding="utf-8")

    # Deduplicate
    dedup_file = lit_dir / "deduped.json"
    dedup_msg = nexus_dedup(str(lit_dir / "raw_search.json"), str(dedup_file))
    assert "Successfully deduplicated" in dedup_msg
    assert dedup_file.exists()

    # Screen
    screen_msg = nexus_screen(str(dedup_file), str(proto_file), str(lit_dir))
    assert "Screening complete" in screen_msg
    assert (lit_dir / "included.json").exists()
    assert (lit_dir / "excluded.json").exists()
    assert (lit_dir / "prisma_screening_report.md").exists()

    # Extract Markdown & Index
    ext_dir = workspace / "extracted"
    ext_dir.mkdir(exist_ok=True)
    (ext_dir / "SCI-000001.md").write_text(
        "---\n"
        'workspace_id: "SCI-000001"\n'
        'doi: "10.1038/interface1"\n'
        'title: "Benchmarking Multi-Modal Research Interfaces"\n'
        'authors: "John Smith"\n'
        "year: 2024\n"
        "---\n\n"
        "# Benchmarking Multi-Modal Research Interfaces\n\n"
        "## Abstract\nEvaluates systematic literature workflows with 99% throughput.\n\n"
        "## Results\nEmpirical accuracy reached 98.5% across evaluated test suites.\n",
        encoding="utf-8",
    )

    db_path = str(workspace / "chroma_db")

    # E3 boundary: the MCP surface refuses indexing outright, and the refusal is
    # observable rather than a silently absent tool. Nothing was indexed here.
    idx_envelope = json.loads(
        nexus_rag_index(
            docs_dir=str(ext_dir), db_path=db_path, workspace_id="phase3-benchmark"
        )
    )
    assert idx_envelope["operation"] == "rag_index"
    assert idx_envelope["status"] == "FAILED"
    assert idx_envelope["artifacts"] == []
    assert idx_envelope["warnings"] == []
    assert len(idx_envelope["errors"]) == 1
    assert idx_envelope["errors"][0]["code"] == "UNSUPPORTED_CAPABILITY"
    assert "scholar-rag index" in json.dumps(idx_envelope["errors"][0]["details"])

    # The supported surface is the kit's own typed service -- the exact function
    # `scholar-rag index` calls. Identity comes from an ACCEPTED parent view the
    # test states; nothing is inferred from the filename, the DOI, or project.json.
    study_id = "STU-" + "4" * 32
    document_id = "DOC-" + "1" * 32
    extracted_body = (ext_dir / "SCI-000001.md").read_text(encoding="utf-8")
    (ext_dir / f"{document_id}.md").write_text(extracted_body, encoding="utf-8")
    (ext_dir / "SCI-000001.md").unlink()

    parent_view = {
        "artifact_id": "ART-" + "1" * 32,
        "artifact_type": "document_manifest",
        "sha256": "sha256:" + "1" * 64,
        "workspace_id": "WSP-" + "0" * 32,
        "protocol_fingerprint": "sha256:" + "2" * 64,
        "corpus_fingerprint": "sha256:" + "3" * 64,
        "documents": [
            {
                "document_id": document_id,
                "study_id": study_id,
                "extracted_path": f"extracted/{document_id}.md",
                "extracted_content_sha256": text_fingerprint(extracted_body),
                "extraction_method": "DETERMINISTIC_RULE",
            }
        ],
    }
    # The typed service states its journal destination and refuses to create it,
    # so the destination's parent directory has to exist beforehand.
    (workspace / "audit").mkdir(parents=True, exist_ok=True)
    parent_view_file = workspace / "accepted_parent_view.json"
    parent_view_file.write_text(json.dumps(parent_view), encoding="utf-8")

    # One deterministic, offline embedding identity for both the write side
    # (`run_typed_index`) and the read side (`ScholarRetriever` behind the MCP
    # retrieval tools), so the vectors compared at query time share a space.
    # It is the kit's own `MockEmbeddingFunction` rather than a local stub: it is
    # deterministic and hermetic, it returns plain floats the typed write path
    # accepts, and it carries the `name()`/`get_config()` shape ChromaDB reads
    # back. `ScholarRetriever` otherwise defaults to `sentence-transformers`,
    # which would need a model download.
    embedding_dimension = 384
    offline_embedder = MockEmbeddingFunction(dim=embedding_dimension)

    monkeypatch.setattr(
        scholar_rag_cli, "get_embedder", lambda **kwargs: offline_embedder
    )
    monkeypatch.setattr(
        scholar_rag_retriever, "get_embedder", lambda **kwargs: offline_embedder
    )

    index_result = run_typed_index(
        docs_path=ext_dir,
        parent_view_path=parent_view_file,
        journal_path=workspace / "audit" / "rag_index_runs.jsonl",
        workspace_root=workspace,
        run_id="RUN-" + "a" * 32,
        created_at="2026-09-01T00:00:00Z",
        producer_version="0.2.0",
        # The producer is the vendored rag-kit build, so this must track the pin
        # rather than a hand-copied SHA that silently goes stale on the next bump.
        producer_commit=_pinned_rag_commit(),
        db_path=db_path,
        collection="scholar_docs",
        hnsw_space="cosine",
        embedder="mock",
        model_name=None,
        embedder_provider="mock",
        embedder_model="mock-384",
        embedder_dimension=embedding_dimension,
        embedder_distance_metric="cosine",
        embedder_model_revision=None,
        recovery_probe_run_id=None,
    )

    assert index_result.outcome == "SUCCESS", index_result.envelope()
    assert index_result.counts.accepted_documents == 1
    assert index_result.counts.rejected_documents == 0
    assert index_result.counts.visible_chunks >= 1
    assert index_result.live_set_matches is True
    assert index_result.journaled is True
    assert (workspace / "audit" / "rag_index_runs.jsonl").is_file()

    # Grounded Query & Synthesis over the index the typed service just wrote.
    query_res = nexus_rag_query(query="empirical accuracy", db_path=db_path)
    assert "Result 1" in query_res

    synth_res = nexus_rag_synthesize(
        query="What is the empirical accuracy?", db_path=db_path
    )
    assert "Grounded Synthesis" in synth_res

    synth_dir = workspace / "synthesis"
    synth_dir.mkdir(exist_ok=True)
    (synth_dir / "literature_review.md").write_text(synth_res, encoding="utf-8")

    # Dynamic Matrix Extraction
    matrix_msg = nexus_matrix_extract(
        workspace_dir=str(workspace),
        protocol_path=str(proto_file),
        output_dir=str(lit_dir),
    )
    assert "Successfully extracted dynamic matrix" in matrix_msg
    assert (lit_dir / "synthesis_matrix.csv").exists()

    # Citation Graph Build
    graph_msg = nexus_graph_build(
        input_path=str(lit_dir / "included.json"),
        output_html=str(lit_dir / "knowledge_graph.html"),
        json_output=str(lit_dir / "knowledge_graph.json"),
    )
    assert "Citation graph built" in graph_msg
    assert (lit_dir / "knowledge_graph.html").exists()

    # =========================================================================
    # Step 3: Export to Academic Ecosystem Modalities
    # =========================================================================
    # 1. LaTeX
    tex_out = synth_dir / "literature_review.tex"
    AcademicTypesettingExporter.export_latex(
        synth_dir / "literature_review.md", lit_dir / "references.bib", tex_out
    )
    assert tex_out.exists()
    assert "\\documentclass{article}" in tex_out.read_text(encoding="utf-8")

    # 2. Typst
    typ_out = synth_dir / "literature_review.typ"
    AcademicTypesettingExporter.export_typst(
        synth_dir / "literature_review.md", lit_dir / "references.bib", typ_out
    )
    assert typ_out.exists()
    assert "#set page" in typ_out.read_text(encoding="utf-8")

    # 3. Obsidian PKM Vault
    vault_out = lit_dir / "obsidian_vault"
    ObsidianVaultExporter.export_vault(workspace, vault_out)
    assert (vault_out / "Map of Content.md").exists()
    assert len(list((vault_out / "literature_notes").glob("*.md"))) >= 1

    # 4. Zotero Bridge
    bridge = ZoteroBridge()
    manifest = bridge.sync_included_papers(
        lit_dir / "included.json", project_slug="phase3-benchmark"
    )
    assert manifest["items_synced"] >= 1
    assert (lit_dir / "zotero_manifest.json").exists()

    # =========================================================================
    # Step 4: Final Workspace Status Verification
    # =========================================================================
    final_status = orchestrator.get_status()
    assert final_status["included_count"] >= 1
    assert final_status["extracted_count"] == 1
    assert final_status["matrix_rows"] >= 1
    assert final_status["graph_nodes"] >= 1
    assert final_status["synthesis_generated"] is True
    assert final_status["phase"] == "PHASE_3_COMPLETE"
