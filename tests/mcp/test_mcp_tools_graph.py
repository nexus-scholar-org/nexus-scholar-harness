"""Hermetic tests for the nexus_* MCP tools in scholar-agent-kit.

The vision-report sweep flagged these tools as silently broken (dropped
metadata, lint-only bib cleaning, screen artifacts never written). The graph
tool's tests left with ``nexus_graph_build`` (H-remove-graph, 2026-11-23); the
file keeps its name because the docs cite it.  Each fix ships a regression
test here; the suite targets the tool functions directly with fake
engines / in-memory fixtures, never the network.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scholar_agent.server import (
    nexus_extract_pdf,
    nexus_screen,
)


@pytest.fixture(autouse=True)
def _mcp_workspace(tmp_path, monkeypatch):
    """Tool paths must resolve inside NEXUS_MCP_WORKSPACE (AGT-01)."""
    monkeypatch.setenv("NEXUS_MCP_WORKSPACE", str(tmp_path))


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


def test_nexus_screen_flags_conflicts_in_its_proposals(tmp_path):
    """A conflicting-signal doc (inclusion AND exclusion hit) is flagged in the
    proposals preview. AGT-16 (M1a): proposals only, no published partition."""
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

    proposals = json.loads((out_dir / "screening_proposals.json").read_text(encoding="utf-8"))
    preview = proposals["preview"]
    assert proposals["status"] == "PROPOSALS_ONLY"
    assert preview["conflicts_flagged"] >= 1
    assert preview["records_screened"] == len(proposals["proposals"]) == 1
    assert "1 flagged" in result
    for name in ("included.json", "excluded.json", "conflicts.json", "prisma_report.json", "prisma_screening_report.md"):
        assert not (out_dir / name).exists(), name


def test_nexus_screen_empty_candidates_still_writes_proposals(tmp_path):
    candidates_path, protocol_path = _write_screening_fixtures(tmp_path, candidates=[])
    out_dir = tmp_path / "output"
    result = nexus_screen(str(candidates_path), str(protocol_path), str(out_dir))
    proposals = json.loads((out_dir / "screening_proposals.json").read_text(encoding="utf-8"))
    assert proposals["preview"]["records_screened"] == 0
    assert "0 flagged" in result


_VERIFIED_QUOTE = "The group that received the intervention improved on the primary outcome."


# ---------------------------------------------------------------------------
# nexus_* path args: anchor relative paths to the workspace anchor
# (matrix finding #1 -- CWD-relative defaults must NOT land in the kit dir)
# ---------------------------------------------------------------------------

def test_nexus_relative_paths_resolve_to_anchor(tmp_path, monkeypatch):
    from scholar_agent import server

    anchor = tmp_path / "anchor"
    anchor_inputs = anchor / "inputs"
    anchor_inputs.mkdir(parents=True)
    _write_screening_fixtures(anchor_inputs, candidates=[])
    monkeypatch.setattr(server, "_mcp_anchor", lambda: anchor)

    result = nexus_screen("inputs/candidates.json", "inputs/protocol.json", "literature")

    assert (anchor / "literature" / "screening_proposals.json").exists()
    assert "flagged" in result
    assert not (Path.cwd() / "literature").exists()


def test_nexus_mcp_workspace_env_anchors_relative_args(tmp_path, monkeypatch):
    # The anchor comes from NEXUS_MCP_WORKSPACE itself, not a patched helper.
    monkeypatch.setenv("NEXUS_MCP_WORKSPACE", str(tmp_path))
    inputs = tmp_path / "inputs"
    inputs.mkdir(parents=True)
    _write_screening_fixtures(inputs, candidates=[])

    result = nexus_screen("inputs/candidates.json", "inputs/protocol.json", "literature")

    assert (tmp_path / "literature" / "screening_proposals.json").exists()
    assert "flagged" in result


def test_nexus_resolve_path_keeps_inside_absolute_and_inline_json(tmp_path, monkeypatch):
    from scholar_agent import server

    assert server._resolve_path(str(tmp_path)) == str(tmp_path.resolve())
    # Inline JSON is kept only by the JSON-capable resolver (AGT-01 review).
    assert server._resolve_path_or_json('{"a": 1}') == '{"a": 1}'
    assert server._resolve_path(None) is None


# ---------------------------------------------------------------------------
# nexus_protocol_validate: inline mode runs the full cross-field rule set
# (matrix finding #5)
# ---------------------------------------------------------------------------

def _compiled_protocol_dict(intent_extra):
    from scholar_protocol.canonical import canonical_json
    from scholar_protocol.compiler import compile_protocol
    from scholar_protocol.intent import IntentPacket

    data = {
        "protocol_id": "proto-validate-test",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": "validate-test-workspace",
        "playbook_type": "DESIGN_SCIENCE",
        "title": "Inline Cross-Field Validation",
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
            {"criterion": "Non-English", "reason_category": "LANGUAGE", "maps_to_rqs": ["RQ1"]}
        ],
        "matrix_dimensions": [
            {"id": "throughput", "name": "Throughput", "description": "Operations per second"}
        ],
    }
    if intent_extra:
        data.update(intent_extra)
    intent = IntentPacket.model_validate(data)
    return json.loads(canonical_json(compile_protocol(intent)).decode("utf-8"))


def test_nexus_protocol_validate_inline_runs_cross_field_rules():
    from scholar_agent.server import nexus_protocol_validate

    pristine = _compiled_protocol_dict(None)
    assert json.loads(nexus_protocol_validate(json.dumps(pristine)))["status"] == "VALID"

    dup = _compiled_protocol_dict(None)
    dup["research_questions"].append(dup["research_questions"][0])
    payload = json.loads(nexus_protocol_validate(json.dumps(dup)))
    assert payload["status"] == "INVALID"
    assert any("appears more than once" in err for err in payload["errors"])


def test_nexus_protocol_validate_inline_and_file_modes_agree(tmp_path):
    from scholar_agent.server import nexus_protocol_validate

    dup = _compiled_protocol_dict(None)
    dup["research_questions"].append(dup["research_questions"][0])
    inline = json.loads(nexus_protocol_validate(json.dumps(dup)))

    proto_file = tmp_path / "protocol.json"
    proto_file.write_text(json.dumps(dup), encoding="utf-8")
    filed = json.loads(nexus_protocol_validate(str(proto_file)))

    assert inline["status"] == filed["status"] == "INVALID"
    assert sorted(inline["errors"]) == sorted(filed["errors"])
