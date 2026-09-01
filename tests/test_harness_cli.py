"""Unit tests for scholar-harness CLI and Orchestrator."""

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from scholar_harness.cli import app
from scholar_harness.orchestrator import ResearchOrchestrator
from scholar_protocol.compiler import compile_protocol
from scholar_protocol.intent import IntentPacket
from scholar_protocol.canonical import canonical_json

runner = CliRunner()


@pytest.fixture
def mock_protocol_workspace(tmp_path):
    # Compile a canonical protocol
    intent = IntentPacket.model_validate({
        "protocol_id": "proto-harness-test",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": "harness-test-workspace",
        "playbook_type": "DESIGN_SCIENCE",
        "title": "Harness CLI Pipeline Evaluation",
        "lead_researcher": "Test Lead",
        "unit_of_analysis": "Harness Pipelines",
        "epistemological_rationale": "Empirical Benchmark",
        "research_questions": [
            {
                "text": "What is the pipeline throughput?",
                "target_facet": "evaluation_metrics",
                "required_evidence_type": "Quantitative Benchmark"
            }
        ],
        "core_concepts": [
            {"concept": "Pipeline", "synonyms": ["orchestrator"]}
        ],
        "inclusion_criteria": [
            {"criterion": "Reports benchmark pass rates", "maps_to_rqs": ["RQ1"]}
        ],
        "exclusion_criteria": [
            {"criterion": "Non-English", "reason_category": "LANGUAGE", "maps_to_rqs": ["RQ1"]}
        ],
        "matrix_dimensions": [
            {"id": "throughput", "name": "Throughput", "description": "Operations per second"}
        ]
    })
    protocol = compile_protocol(intent)
    proto_file = tmp_path / "protocol.json"
    proto_file.write_text(json.dumps(json.loads(canonical_json(protocol).decode("utf-8"))), encoding="utf-8")

    return tmp_path, proto_file


def test_status_command(mock_protocol_workspace):
    workspace, proto_file = mock_protocol_workspace
    result = runner.invoke(app, ["status", "--workspace", str(workspace)])
    assert result.exit_code == 0
    assert "Harness CLI Pipeline Evaluation" in result.stdout
    assert "DESIGN_SCIENCE" in result.stdout
    assert "Discovered Candidates" in result.stdout


def test_export_command(mock_protocol_workspace):
    workspace, proto_file = mock_protocol_workspace

    # Setup literature & synthesis mock data
    lit_dir = workspace / "literature"
    synth_dir = workspace / "synthesis"
    lit_dir.mkdir(exist_ok=True)
    synth_dir.mkdir(exist_ok=True)

    included = [{"workspace_id": "SCI-000001", "title": "Test Title", "year": 2024, "authors": ["Alice"], "doi": "10.1234/test"}]
    (lit_dir / "included.json").write_text(json.dumps(included), encoding="utf-8")
    (synth_dir / "literature_review.md").write_text("# Review\nEmpirical evaluation [SCI-000001].", encoding="utf-8")

    # 1. Export LaTeX
    res_latex = runner.invoke(app, ["export", "latex", "--workspace", str(workspace)])
    assert res_latex.exit_code == 0
    assert (synth_dir / "literature_review.tex").exists()

    # 2. Export Typst
    res_typst = runner.invoke(app, ["export", "typst", "--workspace", str(workspace)])
    assert res_typst.exit_code == 0
    assert (synth_dir / "literature_review.typ").exists()

    # 3. Export Obsidian
    res_obsidian = runner.invoke(app, ["export", "obsidian", "--workspace", str(workspace)])
    assert res_obsidian.exit_code == 0
    assert (lit_dir / "obsidian_vault" / "Map of Content.md").exists()

    # 4. Export Zotero
    res_zotero = runner.invoke(app, ["export", "zotero", "--workspace", str(workspace)])
    assert res_zotero.exit_code == 0
    assert (lit_dir / "zotero_manifest.json").exists()


def test_orchestrator_get_status(mock_protocol_workspace):
    workspace, proto_file = mock_protocol_workspace
    orchestrator = ResearchOrchestrator(workspace)
    status = orchestrator.get_status()

    assert status["protocol_found"] is True
    assert status["title"] == "Harness CLI Pipeline Evaluation"
    assert status["playbook_type"] == "DESIGN_SCIENCE"
    assert status["phase"] == "PHASE_1_DISCOVERY"
