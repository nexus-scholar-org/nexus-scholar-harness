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
    nexus_bib_clean,
    nexus_extract_pdf,
    nexus_graph_build,
    nexus_screen,
    nexus_verify_claims,
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


# ---------------------------------------------------------------------------
# nexus_bib_clean: full pipeline (lint + generate-keys + dedup)
# ---------------------------------------------------------------------------

BIB_WITH_DUPLICATES = """\
@article{dummy_key_1,
  author = {Smith, John and Doe, Jane},
  title = {A study of citation networks},
  year = {2020},
  doi = {10.1000/abc123},
  journal = {Test Journal}
}

@article{DummyKey-2,
  author = {Smith, John and Doe, Jane},
  title = {A study of citation networks},
  year = {2020},
  doi = {10.1000/abc123},
  journal = {Test Journal}
}
"""


def test_nexus_bib_clean_standardizes_keys_and_deduplicates(tmp_path):
    bib = tmp_path / "library.bib"
    bib.write_text(BIB_WITH_DUPLICATES, encoding="utf-8")
    out = tmp_path / "cleaned.bib"

    result = nexus_bib_clean(str(bib), str(out))

    assert out.exists()
    assert "2 entries -> 1 unique" in result

    from scholar_bib.parser import BibParser

    cleaned = BibParser.load(out)
    keys = [e.key for e in cleaned.entries]
    assert len(cleaned.entries) == 1, keys
    assert keys == ["Smith2020"]


def test_nexus_bib_clean_inplace_when_no_output(tmp_path):
    bib = tmp_path / "library.bib"
    bib.write_text(BIB_WITH_DUPLICATES, encoding="utf-8")

    result = nexus_bib_clean(str(bib))

    assert "1 unique" in result
    from scholar_bib.parser import BibParser

    library = BibParser.load(bib)
    assert len(library.entries) == 1


# ---------------------------------------------------------------------------
# nexus_screen: write conflicts.json + prisma_report.json (matrix finding #8)
# ---------------------------------------------------------------------------

_CONFLICTING_PROTOCOL = {
    "screening_criteria": {
        "inclusion": [{"id": "INC-01", "criterion": "study uses machine learning"}],
        "exclusion": [{"id": "EXC-01", "reason_category": "OTHER", "negative_signals": ["systematic review"]}],
    },
    "research_questions": [{"id": "RQ1"}],
}


def _write_screening_fixtures(tmp_path, *, candidates, protocol=None):
    candidates_path = tmp_path / "candidates.json"
    candidates_path.write_text(json.dumps(candidates, indent=2), encoding="utf-8")
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(json.dumps(protocol or _CONFLICTING_PROTOCOL, indent=2), encoding="utf-8")
    return candidates_path, protocol_path


def test_nexus_screen_writes_conflicts_and_prisma_json(tmp_path):
    """Conflicting-signal doc (inclusion AND exclusion hit) must be written to
    conflicts.json, and prisma_report.json must reflect the flag count."""
    candidates_path, protocol_path = _write_screening_fixtures(
        tmp_path,
        candidates=[{
            "title": "A machine learning approach",
            "abstract": "This systematic review applies machine learning methods.",
            "workspace_id": "SCI-0001",
        }],
    )
    out_dir = tmp_path / "output"
    result = nexus_screen(str(candidates_path), str(protocol_path), str(out_dir))

    conflicts = json.loads((out_dir / "conflicts.json").read_text(encoding="utf-8"))
    prisma = json.loads((out_dir / "prisma_report.json").read_text(encoding="utf-8"))
    included = json.loads((out_dir / "included.json").read_text(encoding="utf-8"))
    excluded = json.loads((out_dir / "excluded.json").read_text(encoding="utf-8"))

    assert (out_dir / "prisma_screening_report.md").exists()
    assert len(conflicts) >= 1
    assert len(conflicts) == prisma["conflicts_flagged"]
    assert prisma["records_screened"] == len(included) + len(excluded)
    assert prisma["records_screened"] == 1
    assert "conflicts flagged" in result


def test_nexus_screen_empty_candidates_still_writes_prisma(tmp_path):
    candidates_path, protocol_path = _write_screening_fixtures(tmp_path, candidates=[])
    out_dir = tmp_path / "output"
    result = nexus_screen(str(candidates_path), str(protocol_path), str(out_dir))
    prisma = json.loads((out_dir / "prisma_report.json").read_text(encoding="utf-8"))
    assert prisma["records_screened"] == 0
    assert "0 conflicts flagged" in result


# ---------------------------------------------------------------------------
# nexus_verify_claims: digest scholar-rag claims.json + per-claim verdicts
# (matrix finding #6)
# ---------------------------------------------------------------------------

_VERIFIED_QUOTE = "The group that received the intervention improved on the primary outcome."


def _write_extracted_source(tmp_path):
    src_dir = tmp_path / "extracted"
    src_dir.mkdir(exist_ok=True)
    (src_dir / "SCI-0001.md").write_text(
        "---\n"
        'title: "Intervention trial"\n'
        'workspace_id: "SCI-0001"\n'
        "---\n\n"
        f"{_VERIFIED_QUOTE}\n",
        encoding="utf-8",
    )
    return src_dir


def test_nexus_verify_claims_digests_rag_claims_json(tmp_path):
    """SynthesisClaim-shaped claims (claim_text/study_id, no evidence_quote) must
    be verified and each claim must get a per-claim verdict."""
    src_dir = _write_extracted_source(tmp_path)
    claims = {
        "rq_id": "RQ1",
        "claims": [
            {
                "claim_text": _VERIFIED_QUOTE,
                "citation_tokens": ["[@doi:10.1000/example]"],
                "entailment_status": "VERIFIED",
                "study_id": "SCI-0001",
            },
            {
                "claim_text": "A wholly unrelated sentence that never appears in the document.",
                "study_id": "SCI-0001",
            },
            {
                "claim_text": _VERIFIED_QUOTE,
                "study_id": "SCI-9999",
            },
        ],
    }
    claims_path = tmp_path / "claims.json"
    claims_path.write_text(json.dumps(claims, indent=2), encoding="utf-8")

    payload = json.loads(nexus_verify_claims(str(claims_path), str(src_dir)))

    assert payload["status"] == "SUCCESS"
    assert payload["metrics"]["total_claims"] == 3
    assert payload["metrics"]["verified_claims"] == 1
    assert len(payload["claims"]) == 3
    assert payload["claims"][0]["is_verified"] is True
    assert payload["claims"][0]["rag_entailment_status"] == "VERIFIED"
    assert payload["claims"][1]["failure_reason"] == "INSUFFICIENT_COVERAGE"
    assert payload["claims"][2]["failure_reason"] == "SOURCE_TEXT_NOT_FOUND"
    assert payload["failures_by_reason"].get("SOURCE_TEXT_NOT_FOUND") == 1
    assert payload["failures_by_reason"].get("INSUFFICIENT_COVERAGE") == 1


def test_nexus_verify_claims_accepts_bare_list_and_missing_study_id(tmp_path):
    src_dir = _write_extracted_source(tmp_path)
    claims_path = tmp_path / "claims.json"
    claims_path.write_text(
        json.dumps([{"claim_text": _VERIFIED_QUOTE}], indent=2), encoding="utf-8"
    )

    payload = json.loads(nexus_verify_claims(str(claims_path), str(src_dir)))

    assert payload["metrics"]["total_claims"] == 1
    verdict = payload["claims"][0]
    assert verdict["claim_id"] == "CLAIM-0001"
    assert verdict["study_id"] == ""
    assert verdict["is_verified"] is False


def test_nexus_verify_claims_missing_input_returns_error(tmp_path):
    payload = json.loads(
        nexus_verify_claims(str(tmp_path / "nope.json"), str(tmp_path))
    )
    assert payload["status"] == "ERROR"