"""Tests for the F2 nexus_graph_narrative MCP tool."""

from __future__ import annotations

import json

import pytest

from scholar_agent.server import nexus_graph_narrative


@pytest.fixture()
def graph_workspace(tmp_path):
    """Create a workspace with fixture graph data for narrative testing."""
    ws = tmp_path / "test-ws"
    ws.mkdir()
    synth_dir = ws / "synthesis"
    synth_dir.mkdir()

    # Graph JSON with 5 nodes, edges, pagerank, and community groups
    graph_data = {
        "nodes": [
            {
                "id": "n1",
                "title": "Foundational Methods Paper",
                "doi": "10.1000/alpha",
                "group": "0",
            },
            {
                "id": "n2",
                "title": "Empirical Validation Study",
                "doi": "10.1000/beta",
                "group": "0",
            },
            {
                "id": "n3",
                "title": "Theoretical Framework",
                "doi": "10.1000/gamma",
                "group": "1",
            },
            {
                "id": "n4",
                "title": "Meta-Analysis Review",
                "doi": "10.1000/delta",
                "group": "1",
            },
            {
                "id": "n5",
                "title": "Novel Algorithm Design",
                "doi": "10.1000/epsilon",
                "group": "2",
            },
        ],
        "links": [
            {"source": "n1", "target": "n2"},
            {"source": "n1", "target": "n3"},
            {"source": "n3", "target": "n4"},
            {"source": "n5", "target": "n1"},
            {"source": "n2", "target": "n5"},
        ],
        "pagerank": {
            "n1": 0.35,
            "n2": 0.20,
            "n3": 0.18,
            "n4": 0.12,
            "n5": 0.15,
        },
    }

    graph_path = ws / "literature" / "knowledge_graph.json"
    graph_path.parent.mkdir(parents=True)
    graph_path.write_text(json.dumps(graph_data, indent=2), encoding="utf-8")

    return ws, graph_path


def test_graph_narrative_success(graph_workspace):
    ws, graph_path = graph_workspace
    result_str = nexus_graph_narrative(
        workspace_dir=str(ws),
        graph_json_path=str(graph_path),
    )
    result = json.loads(result_str)
    assert result["status"] == "SUCCESS"
    assert result["n_hubs"] == 5  # 5 nodes, all returned as hubs (top_n=10 default)
    assert result["n_communities"] == 3  # 3 groups

    # Check output file
    out_path = ws / "synthesis" / "visual_synthesis.md"
    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert "Visual Synthesis" in content
    assert "Hub Papers" in content
    assert "Thematic Communities" in content


def test_graph_narrative_top_hubs(graph_workspace):
    ws, graph_path = graph_workspace
    result_str = nexus_graph_narrative(
        workspace_dir=str(ws),
        graph_json_path=str(graph_path),
        top_hubs=2,
    )
    result = json.loads(result_str)
    assert result["status"] == "SUCCESS"
    assert result["n_hubs"] == 2


def test_graph_narrative_missing_file(tmp_path):
    result_str = nexus_graph_narrative(
        workspace_dir=str(tmp_path),
        graph_json_path=str(tmp_path / "nonexistent.json"),
    )
    result = json.loads(result_str)
    assert result["status"] == "ERROR"


def test_graph_narrative_missing_workspace(tmp_path, graph_workspace):
    ws, graph_path = graph_workspace
    result_str = nexus_graph_narrative(
        workspace_dir=str(tmp_path / "nonexistent"),
        graph_json_path=str(graph_path),
    )
    result = json.loads(result_str)
    assert result["status"] == "ERROR"
