"""SRCH-16/17/35 and AGT-18: no imputed decisions or votes; provenance recorded."""

from __future__ import annotations

import json

import pytest

from scholar_search.models import Author, Document, ExternalIds
from scholar_search.screening import (
    ScreeningDecision,
    _parse_llm_screening_response,
    calculate_fleiss_kappa,
    evaluate_heuristic_screening,
    reconcile_multi_screener_decisions,
)

PROTOCOL = {"screening_criteria": {"inclusion": [], "exclusion": []}}


def _doc(i: int) -> Document:
    return Document(
        title=f"Doc {i}",
        year=2024,
        provider="crossref",
        provider_id=f"d{i}",
        external_ids=ExternalIds(doi=f"10.1/d{i}"),
        authors=[Author("A")],
        workspace_id=f"SCI-00000{i}",
    )


@pytest.mark.parametrize(
    ("entry", "expected"),
    [
        ({"workspace_id": "SCI-000001"}, "MAYBE"),
        ({"workspace_id": "SCI-000001", "decision": "UNCLEAR"}, "MAYBE"),
        ({"workspace_id": "SCI-000001", "decision": "maybe"}, "MAYBE"),
        ({"workspace_id": "SCI-000001", "decision": "include"}, "INCLUDE"),
        ({"workspace_id": "SCI-000001", "decision": "EXCLUDE"}, "EXCLUDE"),
    ],
    ids=["missing", "unclear", "maybe", "include", "exclude"],
)
def test_srch16_llm_uncertainty_goes_to_a_human(entry, expected):
    """A missing or unclear answer is MAYBE, never INCLUDE or EXCLUDE by default."""
    decisions = _parse_llm_screening_response(json.dumps([entry]), [_doc(1)], PROTOCOL)
    assert decisions[0].decision == expected
    assert decisions[0].method == "LLM"


def test_srch16_no_invented_confidence_or_reason():
    decision = _parse_llm_screening_response(
        json.dumps([{"workspace_id": "SCI-000001", "decision": "INCLUDE"}]), [_doc(1)], PROTOCOL
    )[0]
    assert decision.confidence is None
    assert decision.screening_reasoning != "LLM screened."


def test_srch35_heuristic_decisions_are_labelled():
    decision = evaluate_heuristic_screening(_doc(1), PROTOCOL)
    assert decision.method == "HEURISTIC"


def test_srch35_decision_carries_provenance_fields():
    decision = ScreeningDecision(workspace_id="x", decision="INCLUDE", confidence=None, screening_reasoning="r")
    assert {"method", "screener_id", "model_id", "prompt_version"} <= set(vars(decision))


def test_srch17_a_missing_vote_is_not_an_exclude():
    result = reconcile_multi_screener_decisions(
        {"s1": {"a": "INCLUDE", "b": "INCLUDE"}, "s2": {"a": "INCLUDE"}, "s3": {"a": "INCLUDE", "b": "INCLUDE"}}
    )
    # b has two INCLUDE votes and one missing: it is incomplete, not 2-1 against.
    assert result["reconciled"]["b"] == "CONFLICT"
    assert result["incomplete"] == ["b"]
    assert result["reconciled"]["a"] == "INCLUDE"


def test_srch17_an_unadjudicated_tie_is_a_conflict_not_an_exclude():
    result = reconcile_multi_screener_decisions({"s1": {"a": "INCLUDE"}, "s2": {"a": "EXCLUDE"}})
    assert result["reconciled"]["a"] == "CONFLICT"
    adjudicated = reconcile_multi_screener_decisions(
        {"s1": {"a": "INCLUDE"}, "s2": {"a": "EXCLUDE"}}, {"a": "include"}
    )
    assert adjudicated["reconciled"]["a"] == "INCLUDE"


@pytest.mark.parametrize("ratings", [[], [["INCLUDE"], ["EXCLUDE"]]], ids=["no-subjects", "one-rater"])
def test_agt18_kappa_is_undefined_below_two_raters(ratings):
    assert calculate_fleiss_kappa(ratings) is None


def test_agt18_reconcile_reports_undefined_kappa_for_one_screener():
    assert reconcile_multi_screener_decisions({"s1": {"a": "INCLUDE"}})["fleiss_kappa"] is None
    assert reconcile_multi_screener_decisions({})["fleiss_kappa"] is None


def test_review_4_unclear_is_a_category_in_reconcile_and_kappa():
    both = reconcile_multi_screener_decisions({"s1": {"a": "MAYBE"}, "s2": {"a": "MAYBE"}})
    assert both["reconciled"]["a"] == "MAYBE"
    majority = reconcile_multi_screener_decisions(
        {"s1": {"a": "MAYBE"}, "s2": {"a": "MAYBE"}, "s3": {"a": "INCLUDE"}}
    )
    assert majority["reconciled"]["a"] == "MAYBE"
    agree = reconcile_multi_screener_decisions(
        {"s1": {"a": "MAYBE", "b": "INCLUDE"}, "s2": {"a": "MAYBE", "b": "INCLUDE"}}
    )
    assert agree["fleiss_kappa"] == 1.0
