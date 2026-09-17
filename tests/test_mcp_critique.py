"""Tests for the F1 nexus_critique_methodology MCP tool."""

from __future__ import annotations

import json

import pytest

from scholar_agent.server import nexus_critique_methodology


@pytest.fixture()
def critique_workspace(tmp_path):
    """Create a workspace with fixture data for critique testing."""
    ws = tmp_path / "test-ws"
    ws.mkdir()

    # records.json
    rec_dir = ws / "literature" / "extraction" / "merged"
    rec_dir.mkdir(parents=True)
    records = [
        {
            "workspace_id": "SCI-000001",
            "title": "Test Study Alpha",
            "year": 2023,
            "abstract": "A test study on methodology.",
            "segmentation": {},
        },
        {
            "workspace_id": "SCI-000002",
            "title": "Test Study Beta",
            "year": 2022,
            "abstract": "Another test study.",
            "segmentation": {},
        },
    ]
    (rec_dir / "records.json").write_text(json.dumps(records), encoding="utf-8")

    # _manifest.json
    p4_dir = ws / "phase4"
    p4_dir.mkdir()
    manifest = [
        {"workspace_id": "SCI-000001", "title": "Test Study Alpha", "year": 2023},
        {"workspace_id": "SCI-000002", "title": "Test Study Beta", "year": 2022},
    ]
    (p4_dir / "_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    return ws


def test_critique_methodology_success(critique_workspace):
    result_str = nexus_critique_methodology(
        workspace_dir=str(critique_workspace),
    )
    result = json.loads(result_str)
    assert result["status"] == "SUCCESS"
    assert result["per_study_count"] == 2
    assert "domain_ratings" in result
    assert result["overall_risk"] in ("HIGH", "UNCLEAR", "LOW")

    # Check output file exists
    out_path = critique_workspace / "phase4" / "methodological_critique.md"
    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert "Methodological Critique" in content
    assert "SCI-000001" in content


def test_critique_methodology_missing_workspace(tmp_path):
    result_str = nexus_critique_methodology(
        workspace_dir=str(tmp_path / "nonexistent"),
    )
    result = json.loads(result_str)
    assert result["status"] == "ERROR"


def test_critique_methodology_missing_records(tmp_path):
    ws = tmp_path / "test-ws"
    ws.mkdir()
    p4 = ws / "phase4"
    p4.mkdir()
    (p4 / "_manifest.json").write_text("[]", encoding="utf-8")

    result_str = nexus_critique_methodology(workspace_dir=str(ws))
    result = json.loads(result_str)
    assert result["status"] == "ERROR"
    assert "records.json" in result["error"]
