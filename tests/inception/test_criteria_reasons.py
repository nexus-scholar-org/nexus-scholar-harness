"""A reason code on every exclusion (M10b, ``05-criteria``).

Strict run 2026-11-13, finding 5: every exclusion of the protocol carried
``OUT_OF_SCOPE``, because out-of-scope lines and the paradigm default had no
reason of their own in the draft. The draft now holds one for each, the
criteria step offers a list, and the compiled criteria carry them.
"""

from __future__ import annotations

import pytest
from test_steps_proof_optional import TS, ready_draft

from scholar_harness.inception import steps
from scholar_harness.inception.intent import CriterionDraft


def _exclusions(draft: dict) -> list[tuple[str, str]]:
    return [(c["criterion"], c["reason_category"]) for c in steps.preview(draft, genesis_timestamp=TS)["intent"]["exclusion_criteria"]]


def test_out_of_scope_lines_carry_their_own_reason_into_the_protocol():
    draft = {
        **ready_draft(),
        "extra_exclusions": [],
        "out_of_scope": ["Satellite imagery", "Greenhouse trials"],
        "out_of_scope_reasons": {"Satellite imagery": "WRONG_PLATFORM"},
    }
    # H-run-small-fixes (finding 2): each out-of-scope line is accepted on its own.
    draft["criteria_decisions"] = {
        c["id"]: True for c in steps.run_step("criteria", draft)["criteria"] if c["source"] == "out_of_scope"
    }
    assert _exclusions(draft) == [("Satellite imagery", "WRONG_PLATFORM"), ("Greenhouse trials", "OUT_OF_SCOPE")]
    protocol = steps.preview(draft, genesis_timestamp=TS)["protocol"]
    assert [e["reason_category"] for e in protocol["screening_criteria"]["exclusion"]] == ["WRONG_PLATFORM", "OUT_OF_SCOPE"]


def test_the_paradigm_default_takes_the_researchers_reason():
    draft = {**ready_draft(), "extra_exclusions": [], "default_exclusion_reason": "NO_EMPIRICAL_EVALUATION"}
    row = [c for c in steps.run_step("criteria", draft)["criteria"] if c["source"] == "paradigm_default"][0]
    assert row["reason_category"] == "NO_EMPIRICAL_EVALUATION"


def test_a_reason_changes_the_id_and_nothing_else_does():
    plain = CriterionDraft("exclusion", "Satellite imagery", "out_of_scope", "OUT_OF_SCOPE")
    coded = CriterionDraft("exclusion", "Satellite imagery", "out_of_scope", "WRONG_PLATFORM")
    assert plain.id != coded.id
    # A draft that sets no reason keeps the ids it had before M10b.
    draft = {**ready_draft(), "extra_exclusions": [], "out_of_scope": ["Satellite imagery"]}
    row = [c for c in steps.run_step("criteria", draft)["criteria"] if c["source"] == "out_of_scope"][0]
    assert row["id"] == plain.id


def test_the_suggestions_come_from_the_engine_used_codes_first_none_selected():
    draft = {**ready_draft(), "out_of_scope": ["Satellite imagery"], "out_of_scope_reasons": {"Satellite imagery": "MY_OWN_CODE"}}
    suggestions = steps.run_step("criteria", draft)["reason_suggestions"]
    codes = [s["code"] for s in suggestions]
    assert codes[:2] == ["WRONG_REPORT_TYPE", "MY_OWN_CODE"]  # used in this draft, in draft order
    assert {"OUT_OF_SCOPE", "WRONG_POPULATION", "NO_EMPIRICAL_EVALUATION"} <= set(codes)
    assert len(codes) == len(set(codes))
    by_code = {s["code"]: s for s in suggestions}
    assert by_code["NO_EMPIRICAL_EVALUATION"]["phrases"] is True
    assert by_code["WRONG_POPULATION"]["phrases"] is False
    assert all("selected" not in s for s in suggestions)


@pytest.mark.parametrize("code", ["out_of_scope", "AB", "A" * 41, "1ABC", "WRONG-TASK", "WRONG TASK"])
def test_a_code_outside_the_rule_is_refused_when_saved(code):
    draft = {**ready_draft(), "extra_exclusions": [{"criterion": "x", "reason_category": code}]}
    with pytest.raises(steps.StepRefused) as exc:
        steps.parse_draft(draft, saving=True)
    assert exc.value.code == "DRAFT_INVALID"
    assert exc.value.details["errors"][0]["loc"] == ["extra_exclusions", 0, "reason_category"]


def test_the_new_fields_are_checked_on_save_too():
    for extra, loc in (
        ({"out_of_scope": ["x"], "out_of_scope_reasons": {"x": "bad"}}, ["out_of_scope_reasons", "x"]),
        ({"default_exclusion_reason": "bad"}, ["default_exclusion_reason"]),
    ):
        with pytest.raises(steps.StepRefused) as exc:
            steps.parse_draft({**ready_draft(), **extra}, saving=True)
        assert exc.value.details["errors"][0]["loc"] == loc


def test_an_older_code_is_read_and_flagged_not_refused():
    """A draft saved before the rule stays readable; its row says the code breaks it."""
    draft = {**ready_draft(), "extra_exclusions": [{"criterion": "Simulation only", "reason_category": "sim"}]}
    rows = steps.run_step("criteria", draft)["criteria"]
    row = [c for c in rows if c["criterion"] == "Simulation only"][0]
    assert row["reason_category"] == "sim" and row["reason_valid"] is False
    assert all(c["reason_valid"] for c in rows if c["kind"] == "exclusion" and c is not row)
