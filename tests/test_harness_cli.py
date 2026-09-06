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


def test_sync_command_rebuilds_project_state(tmp_path):
    workspace = tmp_path
    lit = workspace / "literature"
    (workspace / "pdfs").mkdir(parents=True)
    (workspace / "extracted").mkdir()
    lit.mkdir()

    # Seed minimal literature state
    raw = [{"workspace_id": f"W{i:04d}"} for i in range(10)]
    (lit / "raw_search.json").write_text(json.dumps(raw), encoding="utf-8")
    verified = raw[:8]
    (lit / "verified.json").write_text(json.dumps(verified), encoding="utf-8")
    included = raw[:3]
    (lit / "included.json").write_text(json.dumps(included), encoding="utf-8")
    excluded = raw[3:8]
    (lit / "excluded.json").write_text(json.dumps(excluded), encoding="utf-8")
    (lit / "prisma_report.json").write_text(json.dumps({
        "total_identified": 10, "records_screened": 8, "records_included": 3,
        "records_excluded": 5, "conflicts_flagged": 2,
    }), encoding="utf-8")
    for i in range(2):
        (workspace / "pdfs" / f"p{i}.pdf").write_bytes(b"%PDF-")
    for i in range(2):
        (workspace / "extracted" / f"e{i}.md").write_text("# doc", encoding="utf-8")

    result = runner.invoke(app, ["sync", "--workspace", str(workspace)])
    assert result.exit_code == 0

    manifest = json.loads((workspace / "project.json").read_text(encoding="utf-8"))
    stats = manifest["stats"]
    assert stats["discovered_papers"] == 10
    assert stats["verified_papers"] == 8
    assert stats["included_papers"] == 3
    assert stats["excluded_papers"] == 5
    assert stats["records_screened"] == 8
    assert stats["downloaded_pdfs"] == 2
    assert stats["extracted_markdowns"] == 2

    assert (workspace / "INDEX.md").exists()
    index_content = (workspace / "INDEX.md").read_text(encoding="utf-8")
    assert "Project Index" in index_content

    # No temp residue after atomic write
    assert not list(workspace.glob("*.tmp"))


def test_sync_command_dry_run_writes_nothing(tmp_path):
    workspace = tmp_path
    lit = workspace / "literature"
    lit.mkdir()
    raw = [{"workspace_id": f"W{i:04d}"} for i in range(5)]
    (lit / "raw_search.json").write_text(json.dumps(raw), encoding="utf-8")

    result = runner.invoke(app, ["sync", "--workspace", str(workspace), "--dry-run"])
    assert result.exit_code == 0
    assert "DRY RUN" in result.stdout
    assert not (workspace / "project.json").exists()
    assert not (workspace / "INDEX.md").exists()
