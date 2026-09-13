"""Hermetic tests for the nexus_* MCP tools in scholar-agent-kit.

The vision-report sweep flagged these tools as silently broken (0-edge
graphs, dropped metadata, lint-only bib cleaning, screen artifacts never
written, a verify-claims schema mismatch).  Each fix ships a regression
test here; the suite targets the tool functions directly with fake
engines / in-memory fixtures, never the network.
"""

from __future__ import annotations

import json

import networkx as nx
import pytest

from scholar_graph.builder import CitationGraphBuilder

from scholar_agent.server import (
    nexus_extract_pdf,
    nexus_graph_build,
    nexus_verify_claims,
)


def _di_graph(dois: list[str], *edges: tuple[str, str]) -> nx.DiGraph:
    G = nx.DiGraph()
    for doi in dois:
        G.add_node(doi, title=f"Study {doi}", year=None, citations=0, group=1, label=doi)
    for src, dst in edges:
        G.add_edge(src, dst)
    return G


# ---------------------------------------------------------------------------
# nexgraph: the tool must drive a real OpenAlex HTTP client (not http_client=None)
# ---------------------------------------------------------------------------


def test_nexus_graph_build_uses_real_http_client(tmp_path, monkeypatch):
    inp = tmp_path / "included.json"
    inp.write_text(
        json.dumps(
            [
                {"external_ids": {"doi": "10.1000/aaa"}},
                {"doi": "10.1000/bbb"},
            ]
        ),
        encoding="utf-8",
    )
    out_html = tmp_path / "graph.html"
    out_json = tmp_path / "graph.json"

    captured: dict = {}

    async def fake_build_graph(self, dois, progress_callback=None):
        captured["http_client"] = self.http_client
        captured["dois"] = dois
        return _di_graph(dois, ("10.1000/aaa", "10.1000/bbb"))

    monkeypatch.setattr(CitationGraphBuilder, "build_graph", fake_build_graph)

    result = nexus_graph_build(str(inp), str(out_html), str(out_json))

    assert captured["dois"] == ["10.1000/aaa", "10.1000/bbb"]
    assert captured["http_client"] is not None
    assert captured["http_client"].name == "openalex-graph"
    assert out_json.exists()
    assert out_html.exists()
    assert "2 nodes, 1 edges" in result


def test_nexus_graph_build_accepts_results_dict(tmp_path, monkeypatch):
    inp = tmp_path / "corpus.json"
    inp.write_text(
        json.dumps(
            {"results": [{"doi": "10.1000/aaa"}, {"doi": "10.1000/bbb"}]},
        ),
        encoding="utf-8",
    )
    out_html = tmp_path / "g.html"
    out_json = tmp_path / "g.json"

    captured: dict = {}

    async def fake_build_graph(self, dois, progress_callback=None):
        captured["dois"] = dois
        return _di_graph(dois)

    monkeypatch.setattr(CitationGraphBuilder, "build_graph", fake_build_graph)

    nexus_graph_build(str(inp), str(out_html), str(out_json))

    assert captured["dois"] == ["10.1000/aaa", "10.1000/bbb"]


def test_nexus_graph_build_no_dois_is_an_error(tmp_path):
    inp = tmp_path / "empty.json"
    inp.write_text(json.dumps([{"title": "no doi"}]), encoding="utf-8")

    result = nexus_graph_build(str(inp), str(tmp_path / "g.html"), str(tmp_path / "g.json"))

    assert result.startswith("Error:")