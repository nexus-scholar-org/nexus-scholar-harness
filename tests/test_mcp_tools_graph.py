"""Hermetic tests for the nexus_* MCP tools in scholar-agent-kit.

The vision-report sweep flagged these tools as silently broken (0-edge
graphs, dropped metadata, lint-only bib cleaning, screen artifacts never
written, a verify-claims schema mismatch).  Each fix ships a regression
test here; the suite targets the tool functions directly with fake
engines / in-memory fixtures, never the network.
"""

from __future__ import annotations

import json
from pathlib import Path

import networkx as nx
from scholar_agent.server import (
    nexus_extract_pdf,
    nexus_graph_build,
)
from scholar_graph.builder import CitationGraphBuilder


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


# ---------------------------------------------------------------------------
# nexus_extract_pdf: metadata enrichment + engine routing
# ---------------------------------------------------------------------------


def test_nexus_extract_pdf_passes_path_metadata(tmp_path, monkeypatch):
    from scholar_pdf.extract import PyMuPDFEngine

    pdf = tmp_path / "10.2307_4152972.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    captured = {}

    def fake_extract(pdf_path, output_dir, metadata=None):
        captured["metadata"] = metadata
        out_file = Path(output_dir) / f"{Path(pdf_path).stem}.md"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text("# extracted", encoding="utf-8")
        return out_file

    monkeypatch.setattr(PyMuPDFEngine, "extract_markdown", staticmethod(fake_extract))

    result = nexus_extract_pdf(str(pdf), str(tmp_path / "extracted"))

    assert captured["metadata"]["doi"] == "10.2307_4152972"
    assert captured["metadata"]["title"] == "10.2307 4152972"
    assert "Extracted 10.2307_4152972.pdf" in result


def test_nexus_extract_pdf_doi_regex_from_plain_name(tmp_path, monkeypatch):
    from scholar_pdf.extract import DoclingEngine

    pdf = tmp_path / "scott2020.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    captured = {}

    def fake_extract(pdf_path, output_dir, metadata=None):
        captured["metadata"] = metadata
        out_file = Path(output_dir) / f"{Path(pdf_path).stem}.md"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text("# extracted", encoding="utf-8")
        return out_file

    monkeypatch.setattr(DoclingEngine, "extract_markdown", staticmethod(fake_extract))

    nexus_extract_pdf(str(pdf), str(tmp_path / "extracted"), engine="docling")

    assert captured["metadata"]["doi"] == ""
    assert captured["metadata"]["title"] == "scott2020"