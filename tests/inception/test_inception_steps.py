"""The stateless inception step API and the compile-preview (M4a).

The steps map a draft onto the wizard's own functions, so the same answers give
the same protocol through the CLI wizard and through the API. The preview
compiles in memory and writes nothing.
"""

from __future__ import annotations

import json

import pytest
from conftest import E2E_ANSWERS, GENESIS_TS, ScriptedResponder

from scholar_harness.inception import run_wizard, steps
from scholar_harness.inception.intent import CriterionDraft


def _e2e_draft() -> dict:
    """The conftest E2E interview, as a web-wizard draft."""
    a = E2E_ANSWERS
    proof = a[5]
    proof_id = CriterionDraft("inclusion", f"Reports the gold-standard proof — {proof}", "proof").id
    return {
        "topic": a[0],
        "paradigm": a[1],
        "playbook": a[2],
        "unit_of_analysis": a[4],
        "proof": proof,
        "out_of_scope": [s.strip() for s in a[6].split(",")],
        "rqs": [a[8]],
        "concepts": [{"concept": "weed detection"}, {"concept": "on-device inference"}],
        "criteria_decisions": {proof_id: True},
        "verification_checks": True,
        "title": "On-Device Weed Detection for Embedded Agriculture",
        "lead_researcher": "Dr. Mouadh",
    }


def _tree(path):
    return sorted(p.relative_to(path).as_posix() for p in path.rglob("*")) if path.exists() else []


def test_scope_proposes_what_the_wizard_proposes():
    out = steps.run_step("scope", {"topic": E2E_ANSWERS[0]})
    assert out["recommended_paradigm"] == "Design Science"
    assert {p["name"] for p in out["paradigms"]} >= {"Positivist", "Interpretivist", "Design Science"}
    assert len(out["refraction"]) == 4
    assert out["default_concepts"]


def test_shape_drafts_rq1_from_the_paradigm_template():
    draft = {"topic": "edge AI", "paradigm": "Design Science", "unit_of_analysis": "drones", "proof": "FPS"}
    out = steps.run_step("shape", draft)
    assert out["recommended_playbook"] == "DESIGN_SCIENCE"
    assert out["rq_draft"] == "Can a novel edge AI artifact achieve FPS for drones, compared to a defined baseline?"


def test_criteria_step_lists_each_criterion_with_source_and_status():
    draft = _e2e_draft()
    draft["criteria_decisions"] = {}
    out = steps.run_step("criteria", draft)
    items = out["criteria"]
    assert [(i["kind"], i["source"], i["status"]) for i in items] == [
        ("inclusion", "proof", "undecided"),
        ("exclusion", "out_of_scope", "accepted"),
        ("exclusion", "out_of_scope", "accepted"),
    ]
    assert items[0]["criterion"].startswith("Reports the gold-standard proof — ")
    assert items[0]["generated"] is True
    assert out["undecided"] == [items[0]["id"]]
    assert out["missing_sides"] == ["inclusion"]


def test_a_step_refuses_an_incomplete_draft_and_an_unknown_step():
    with pytest.raises(steps.StepRefused) as exc:
        steps.run_step("shape", {"topic": "x"})
    assert exc.value.code == "DRAFT_INCOMPLETE" and exc.value.details["missing"] == ["paradigm"]
    with pytest.raises(steps.StepRefused) as exc:
        steps.run_step("nope", {})
    assert exc.value.code == "STEP_UNKNOWN"
    with pytest.raises(steps.StepRefused) as exc:
        steps.run_step("scope", {"topic": "x", "surprise": 1})
    assert exc.value.code == "DRAFT_INVALID"


def test_preview_writes_nothing(tmp_path):
    before = _tree(tmp_path)
    out = steps.preview(_e2e_draft(), workspaces_root=tmp_path, genesis_timestamp=GENESIS_TS)
    assert _tree(tmp_path) == before
    assert out["written"] == []
    assert out["protocol_fingerprint"].startswith("sha256:")
    assert "Reports the gold-standard proof" in out["screening_criteria"]
    assert out["target"] == {
        "slug": "on-device-weed-detection-for-embedded-agriculture",
        "path": str(tmp_path / "on-device-weed-detection-for-embedded-agriculture"),
        "exists": False,
        "workspace": False,
        "screening": None,
    }


def test_preview_and_the_cli_wizard_compile_the_same_protocol(tmp_path):
    """No second copy of the wizard logic: same answers, same fingerprint."""
    wizard = run_wizard(ScriptedResponder(list(E2E_ANSWERS)), tmp_path, genesis_timestamp=GENESIS_TS)
    out = steps.preview(_e2e_draft(), genesis_timestamp=GENESIS_TS)
    assert out["intent"] == wizard["intent"]
    assert out["protocol_fingerprint"] == wizard["protocol_fingerprint"]


def test_preview_refuses_undecided_generated_criteria():
    draft = _e2e_draft()
    draft["criteria_decisions"] = {}
    with pytest.raises(steps.StepRefused) as exc:
        steps.preview(draft)
    assert exc.value.code == "CRITERIA_UNDECIDED"


def test_preview_refuses_an_empty_side():
    draft = _e2e_draft()
    draft["criteria_decisions"] = {k: False for k in draft["criteria_decisions"]}
    with pytest.raises(steps.StepRefused) as exc:
        steps.preview(draft)
    assert exc.value.code == "CRITERIA_MISSING"
    assert exc.value.details["missing_sides"] == ["inclusion"]


def test_a_rejected_criterion_leaves_the_preview():
    draft = _e2e_draft()
    reject = steps.run_step("criteria", draft)["criteria"][2]["id"]
    draft["criteria_decisions"][reject] = False
    draft["extra_inclusions"] = ["Evaluates on embedded hardware"]
    out = steps.preview(draft, genesis_timestamp=GENESIS_TS)
    assert [c["criterion"] for c in out["intent"]["exclusion_criteria"]] == ["closed-source models"]
    assert "pre-2022 studies" not in out["screening_criteria"]


def test_genesis_writes_through_the_gate_and_refuses_a_second_time(tmp_path):
    result = steps.genesis(_e2e_draft(), workspaces_root=tmp_path, agent="nexus-scholar/ui")
    ws = tmp_path / result["slug"]
    assert result["replaced"] is False
    assert (ws / "protocol.json").is_file() and (ws / ".mcp.json").is_file()
    genesis = [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()]
    assert genesis[-1]["action"] == "GENESIS" and genesis[-1]["agent_or_tool"] == "nexus-scholar/ui"

    with pytest.raises(steps.StepRefused) as exc:
        steps.genesis(_e2e_draft(), workspaces_root=tmp_path, agent="nexus-scholar/ui")
    assert exc.value.code == "WORKSPACE_EXISTS"


def test_genesis_needs_the_typed_slug_to_discard_a_screening_binding(tmp_path):
    first = steps.genesis(_e2e_draft(), workspaces_root=tmp_path, agent="nexus-scholar/ui")
    ws = tmp_path / first["slug"]
    (ws / "literature" / "screening" / "events").mkdir(parents=True)
    (ws / "literature" / "screening" / "events" / "r.jsonl").write_text('{"e": 1}\n', encoding="utf-8")

    with pytest.raises(steps.StepRefused) as exc:
        steps.genesis(_e2e_draft(), workspaces_root=tmp_path, agent="ui", replace=True)
    assert exc.value.code == "SCREENING_BOUND" and exc.value.details["decision_events"] == 1

    with pytest.raises(steps.StepRefused) as exc:
        steps.genesis(_e2e_draft(), workspaces_root=tmp_path, agent="ui", replace=True, confirm_discard_screening_binding="yes")
    assert exc.value.code == "CONFIRMATION_MISMATCH"

    out = steps.genesis(
        _e2e_draft(), workspaces_root=tmp_path, agent="ui", replace=True, confirm_discard_screening_binding=first["slug"]
    )
    assert out["replaced"] is True and out["previous_fingerprint"] == first["protocol_fingerprint"]
