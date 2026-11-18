"""Wording the Review step showed in the strict run of 2026-11-13 (M10b, item A5).

Finding 7: the suggested "Sample Size" column pasted the unit of analysis into
its sentence ("Number of A primary empirical study ... sampled / evaluated").
Finding 9: the rationale read "Convincing evidence is A primary ...".
"""

from __future__ import annotations

from test_steps_proof_optional import TS, ready_draft

from scholar_harness.inception import steps
from scholar_harness.inception.genesis import _default_matrix_dimensions
from scholar_harness.inception.intent import CriterionDraft

UNIT = "A primary empirical study or dataset report."


def test_the_sample_size_column_quotes_the_unit_instead_of_pasting_it():
    sample = [d for d in _default_matrix_dimensions("PRISMA_SLR", UNIT) if d["id"] == "sample_size"][0]
    assert sample["description"] == f"How many were sampled or evaluated (unit of analysis: {UNIT})"


def test_the_rationale_quotes_each_answer_after_a_colon_without_a_double_full_stop():
    proof = "A primary empirical study."
    proof_id = CriterionDraft("inclusion", f"Reports the gold-standard proof — {proof}", "proof").id
    draft = {**ready_draft(), "unit_of_analysis": UNIT, "proof": proof, "criteria_decisions": {proof_id: True}}
    rationale = steps.preview(draft, genesis_timestamp=TS)["intent"]["epistemological_rationale"]
    assert "Convincing evidence: A primary empirical study. " in rationale
    assert "Convincing evidence is" not in rationale
    assert f"Unit of analysis: {UNIT[:-1]}. " in rationale
    assert ".." not in rationale
