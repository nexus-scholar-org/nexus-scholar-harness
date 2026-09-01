"""End-to-End Phase 3 Multi-Modal Integration Test.

Validates the complete research harness lifecycle across:
1. Canonical Protocol Compilation & Fingerprinting
2. Master Orchestrator Execution across all pipeline stages
3. Full FastMCP Server Tool Invocations (scholar-agent-kit)
4. Multi-Format Academic Authoring Exports (LaTeX, Typst, Obsidian, Zotero)
5. Reproducible Jupyter Notebook Structural Validation
"""

import json
from pathlib import Path
import pytest

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
                "required_evidence_type": "Quantitative Benchmark"
            }
        ],
        "core_concepts": [
            {"concept": "Research Interface", "synonyms": ["orchestrator", "harness", "agent"]}
        ],
        "inclusion_criteria": [
            {"criterion": "Evaluates systematic literature workflows and empirical benchmarks", "maps_to_rqs": ["RQ1"]}
        ],
        "exclusion_criteria": [
            {"criterion": "Non-English studies without empirical verification", "reason_category": "METHODOLOGY", "maps_to_rqs": ["RQ1"]}
        ],
        "matrix_dimensions": [
            {"id": "throughput", "name": "Pipeline Throughput", "description": "Papers processed per second"},
            {"id": "entailment_rate", "name": "Entailment Rate", "description": "Percentage of verified claims"}
        ]
    }

    intent = IntentPacket.model_validate(intent_dict)
    protocol = compile_protocol(intent)

    proto_file = workspace / "protocol.json"
    proto_file.write_bytes(canonical_json(protocol))

    return workspace, proto_file


def test_phase3_e2e_full_lifecycle(phase3_test_workspace):
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
            "abstract": "Evaluates systematic literature workflows and empirical benchmarks with 99% throughput."
        },
        {
            "title": "Benchmarking Multi-Modal Research Interfaces",
            "year": 2024,
            "provider": "semanticscholar",
            "provider_id": "S2001",
            "external_ids": {"doi": "10.1038/interface1"},
            "authors": [{"family_name": "Smith", "given_name": "John"}],
            "abstract": "Duplicate copy from secondary provider."
        },
        {
            "title": "Non-English Opinion Piece",
            "year": 2024,
            "provider": "crossref",
            "provider_id": "C3001",
            "external_ids": {"doi": "10.1038/editorial"},
            "authors": [{"family_name": "Dupont", "given_name": "Pierre"}],
            "abstract": "Theoretical essay without empirical verification."
        }
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
        "workspace_id: \"SCI-000001\"\n"
        "doi: \"10.1038/interface1\"\n"
        "title: \"Benchmarking Multi-Modal Research Interfaces\"\n"
        "authors: \"John Smith\"\n"
        "year: 2024\n"
        "---\n\n"
        "# Benchmarking Multi-Modal Research Interfaces\n\n"
        "## Abstract\nEvaluates systematic literature workflows with 99% throughput.\n\n"
        "## Results\nEmpirical accuracy reached 98.5% across evaluated test suites.\n",
        encoding="utf-8"
    )

    db_path = str(workspace / "chroma_db")
    idx_msg = nexus_rag_index(docs_dir=str(ext_dir), db_path=db_path, workspace_id="phase3-benchmark")
    assert "Successfully indexed 1 files" in idx_msg

    # Grounded Query & Synthesis
    query_res = nexus_rag_query(query="empirical accuracy", db_path=db_path)
    assert "Result 1" in query_res

    synth_res = nexus_rag_synthesize(query="What is the empirical accuracy?", db_path=db_path)
    assert "Grounded Synthesis" in synth_res

    synth_dir = workspace / "synthesis"
    synth_dir.mkdir(exist_ok=True)
    (synth_dir / "literature_review.md").write_text(synth_res, encoding="utf-8")

    # Dynamic Matrix Extraction
    matrix_msg = nexus_matrix_extract(workspace_dir=str(workspace), protocol_path=str(proto_file), output_dir=str(lit_dir))
    assert "Successfully extracted dynamic matrix" in matrix_msg
    assert (lit_dir / "synthesis_matrix.csv").exists()

    # Citation Graph Build
    graph_msg = nexus_graph_build(
        input_path=str(lit_dir / "included.json"),
        output_html=str(lit_dir / "knowledge_graph.html"),
        json_output=str(lit_dir / "knowledge_graph.json")
    )
    assert "Citation graph built" in graph_msg
    assert (lit_dir / "knowledge_graph.html").exists()

    # =========================================================================
    # Step 3: Export to Academic Ecosystem Modalities
    # =========================================================================
    # 1. LaTeX
    tex_out = synth_dir / "literature_review.tex"
    AcademicTypesettingExporter.export_latex(synth_dir / "literature_review.md", lit_dir / "references.bib", tex_out)
    assert tex_out.exists()
    assert "\\documentclass{article}" in tex_out.read_text(encoding="utf-8")

    # 2. Typst
    typ_out = synth_dir / "literature_review.typ"
    AcademicTypesettingExporter.export_typst(synth_dir / "literature_review.md", lit_dir / "references.bib", typ_out)
    assert typ_out.exists()
    assert "#set page" in typ_out.read_text(encoding="utf-8")

    # 3. Obsidian PKM Vault
    vault_out = lit_dir / "obsidian_vault"
    ObsidianVaultExporter.export_vault(workspace, vault_out)
    assert (vault_out / "Map of Content.md").exists()
    assert len(list((vault_out / "literature_notes").glob("*.md"))) >= 1

    # 4. Zotero Bridge
    bridge = ZoteroBridge()
    manifest = bridge.sync_included_papers(lit_dir / "included.json", project_slug="phase3-benchmark")
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


def test_notebooks_valid_json():
    """Verify all 4 Jupyter notebooks are structurally sound and parse as valid JSON."""
    notebook_paths = [
        Path("notebooks/00_research_inception.ipynb"),
        Path("notebooks/01_federated_discovery_and_screening.ipynb"),
        Path("notebooks/02_grounded_synthesis_and_matrices.ipynb"),
        Path("notebooks/03_knowledge_graph_and_cartography.ipynb"),
    ]

    for nb_path in notebook_paths:
        assert nb_path.exists(), f"Missing notebook: {nb_path}"
        data = json.loads(nb_path.read_text(encoding="utf-8"))
        assert "cells" in data
        assert len(data["cells"]) >= 3
        assert data["nbformat"] == 4
