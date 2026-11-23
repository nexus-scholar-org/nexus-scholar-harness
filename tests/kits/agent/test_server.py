"""Unit tests for FastMCP Server in scholar-agent-kit."""

import json
import pytest

from scholar_agent.server import (
    nexus_protocol_compile,
    nexus_protocol_validate,
    nexus_protocol_render_criteria,
    nexus_dedup,
    nexus_screen,
)


@pytest.fixture
def sample_intent_json():
    return json.dumps({
        "protocol_id": "proto-agent-test",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": "agent-test-review",
        "playbook_type": "DESIGN_SCIENCE",
        "title": "Agent Test Evaluation",
        "lead_researcher": "Agent Tester",
        "unit_of_analysis": "Autonomous Agents",
        "epistemological_rationale": "Empirical Benchmark",
        "research_questions": [
            {
                "text": "How do agents perform on benchmark X?",
                "target_facet": "evaluation_metrics",
                "required_evidence_type": "Quantitative Benchmark"
            }
        ],
        "core_concepts": [
            {"concept": "Agent", "synonyms": ["autonomous assistant"]}
        ],
        "inclusion_criteria": [
            {"criterion": "Reports benchmark pass rates", "maps_to_rqs": ["RQ1"]}
        ],
        "exclusion_criteria": [
            {"criterion": "Non-English", "reason_category": "LANGUAGE", "maps_to_rqs": ["RQ1"]}
        ],
        "matrix_dimensions": [
            {"id": "sample_size", "name": "Sample Size", "description": "Number of runs"}
        ]
    })


def test_nexus_protocol_compile_and_validate(tmp_path, sample_intent_json):
    # 1. Compile
    compile_res_raw = nexus_protocol_compile(sample_intent_json)
    compile_res = json.loads(compile_res_raw)
    assert compile_res["status"] == "SUCCESS"
    assert compile_res["protocol_id"] == "proto-agent-test"
    assert "fingerprint" in compile_res

    # Save to temp protocol file
    proto_file = tmp_path / "protocol.json"
    proto_file.write_text(json.dumps(compile_res["protocol"]), encoding="utf-8")

    # 2. Validate
    validate_res_raw = nexus_protocol_validate(str(proto_file))
    validate_res = json.loads(validate_res_raw)
    assert validate_res["status"] == "VALID"
    assert validate_res["title"] == "Agent Test Evaluation"

    # 3. Render Criteria
    criteria_md = nexus_protocol_render_criteria(str(proto_file))
    assert "Screening Criteria" in criteria_md
    assert "Agent Test Evaluation" in criteria_md


def test_nexus_dedup_and_screen(tmp_path, sample_intent_json):
    # Setup protocol
    compile_res = json.loads(nexus_protocol_compile(sample_intent_json))
    proto_file = tmp_path / "protocol.json"
    proto_file.write_text(json.dumps(compile_res["protocol"]), encoding="utf-8")

    # Setup raw docs
    raw_docs = [
        {"title": "Agent Benchmark Evaluation", "authors": ["Alice"], "year": 2024, "doi": "10.1038/s1", "abstract": "Reports benchmark pass rates of 95%."},
        {"title": "Agent Benchmark Evaluation", "authors": ["Alice"], "year": 2024, "doi": "10.1038/s1", "abstract": "Duplicate copy."},
        {"title": "Non-English Editorial", "authors": ["Bob"], "year": 2024, "doi": "10.1038/s2", "abstract": "Non-English commentary."}
    ]
    raw_file = tmp_path / "raw.json"
    raw_file.write_text(json.dumps(raw_docs), encoding="utf-8")

    # Deduplicate
    dedup_file = tmp_path / "deduped.json"
    dedup_res = nexus_dedup(str(raw_file), str(dedup_file))
    assert "Successfully deduplicated 3 papers into 2 unique" in dedup_res
    assert dedup_file.exists()

    # Screen
    lit_dir = tmp_path / "literature"
    screen_res = nexus_screen(str(dedup_file), str(proto_file), str(lit_dir))
    # AGT-16 (M1a): MCP screening writes proposals only, never the published partition.
    assert "Proposals only" in screen_res
    assert (lit_dir / "screening_proposals.json").exists()
    for name in ("included.json", "excluded.json", "conflicts.json", "prisma_report.json", "prisma_screening_report.md"):
        assert not (lit_dir / name).exists(), name
