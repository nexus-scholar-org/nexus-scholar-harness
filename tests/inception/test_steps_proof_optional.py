"""The proof answer may be empty (M10b, R4; ``04-shape``).

When the draft holds an inclusion the researcher typed (or imported) and has
not dropped, the wizard needs no proof answer: it writes no proof criterion,
offers no template research question and leaves the "Convincing evidence"
sentence out of the rationale. Without such an inclusion the proof is required
as before.
"""

from __future__ import annotations

import pytest

from scholar_harness.inception import steps
from scholar_harness.inception.intent import CriterionDraft

TS = "2026-11-18T09:00:00+00:00"
TYPED = "Field studies with UAV imagery"


def ready_draft() -> dict:
    """A draft that compiles: one typed inclusion, one typed exclusion, no proof."""
    return {
        "topic": "UAV crop-weed mapping",
        "paradigm": "Positivist",
        "playbook": "PRISMA_SLR",
        "unit_of_analysis": "field trials",
        "rqs": ["How reliable is UAV weed mapping across fields?"],
        "concepts": [{"concept": "weed mapping", "synonyms": ["weed detection"]}],
        "extra_inclusions": [TYPED],
        "extra_exclusions": [{"criterion": "Simulation only", "reason_category": "WRONG_REPORT_TYPE"}],
        "title": "UAV weed mapping",
        "lead_researcher": "A. Researcher",
    }


def _typed_id(text: str = TYPED) -> str:
    return CriterionDraft("inclusion", text, "manual").id


def test_a_draft_with_a_typed_inclusion_needs_no_proof():
    draft = ready_draft()
    assert steps.run_step("shape", draft)["proof_required"] is False
    criteria = steps.run_step("criteria", draft)
    assert "proof" not in {c["source"] for c in criteria["criteria"]}
    assert criteria["undecided"] == []
    out = steps.preview(draft, genesis_timestamp=TS)
    assert "Convincing evidence" not in out["intent"]["epistemological_rationale"]
    assert [c["criterion"] for c in out["intent"]["inclusion_criteria"]] == [TYPED]


def test_no_template_question_without_a_proof():
    assert steps.run_step("shape", ready_draft())["rq_draft"] is None


def test_dropping_the_last_typed_inclusion_makes_the_proof_required_again():
    draft = {**ready_draft(), "criteria_decisions": {_typed_id(): False}}
    assert steps.run_step("shape", draft)["proof_required"] is True
    with pytest.raises(steps.StepRefused) as exc:
        steps.preview(draft, genesis_timestamp=TS)
    assert exc.value.code == "DRAFT_INCOMPLETE"
    assert "proof" in exc.value.details["missing"]


def test_a_draft_without_a_typed_inclusion_still_needs_the_proof():
    draft = {**ready_draft(), "extra_inclusions": []}
    with pytest.raises(steps.StepRefused) as exc:
        steps.run_step("criteria", draft)
    assert exc.value.code == "DRAFT_INCOMPLETE" and exc.value.details["missing"] == ["proof"]


def test_a_typed_proof_beside_a_typed_inclusion_writes_no_criterion():
    """H-run-small-fixes (finding 1): the proof answer is not a screening rule; beside a typed
    inclusion it writes no criterion, and still drafts the template question."""
    draft = {**ready_draft(), "proof": "field-validated accuracy"}
    criteria = steps.run_step("criteria", draft)
    assert [c for c in criteria["criteria"] if c["source"] == "proof"] == []
    assert steps.run_step("shape", draft)["rq_draft"]


def test_a_typed_proof_alone_still_writes_the_fallback_criterion_waiting_for_the_researcher():
    draft = {**ready_draft(), "extra_inclusions": [], "proof": "field-validated accuracy"}
    proof_rows = [c for c in steps.run_step("criteria", draft)["criteria"] if c["source"] == "proof"]
    assert len(proof_rows) == 1 and proof_rows[0]["status"] == "undecided"


def test_blank_answers_count_as_missing():
    """Review of Part A, finding 4: a proof of spaces is no proof; a blank inclusion makes nothing optional."""
    draft = {**ready_draft(), "extra_inclusions": [], "proof": "   "}
    with pytest.raises(steps.StepRefused) as exc:
        steps.run_step("criteria", draft)
    assert exc.value.details["missing"] == ["proof"]
    assert steps.run_step("shape", {**ready_draft(), "extra_inclusions": ["  "]})["proof_required"] is True
