"""Tests for multi-screener adjudication.

(The verbatim claim verifier tests left with ``scholar_verify``, H-remove-rag-verify.)
"""

from scholar_search.screening import (
    calculate_fleiss_kappa,
    reconcile_multi_screener_decisions,
)


def test_calculate_fleiss_kappa():
    # 3 raters, 4 subjects, perfect agreement
    ratings_perfect = [
        ["INCLUDE", "INCLUDE", "INCLUDE"],
        ["EXCLUDE", "EXCLUDE", "EXCLUDE"],
        ["INCLUDE", "INCLUDE", "INCLUDE"],
        ["EXCLUDE", "EXCLUDE", "EXCLUDE"],
    ]
    kappa = calculate_fleiss_kappa(ratings_perfect)
    assert kappa == 1.0

    # Disagreeing ratings
    ratings_mixed = [
        ["INCLUDE", "EXCLUDE", "INCLUDE"],
        ["EXCLUDE", "EXCLUDE", "EXCLUDE"],
    ]
    kappa_mixed = calculate_fleiss_kappa(ratings_mixed)
    assert -1.0 <= kappa_mixed <= 1.0


def test_reconcile_multi_screener_decisions():
    screeners = {
        "s1": {"SCI-01": "INCLUDE", "SCI-02": "INCLUDE", "SCI-03": "INCLUDE"},
        "s2": {"SCI-01": "INCLUDE", "SCI-02": "EXCLUDE", "SCI-03": "INCLUDE"},
        "s3": {"SCI-01": "EXCLUDE", "SCI-02": "EXCLUDE", "SCI-03": "INCLUDE"},
        "s4": {"SCI-01": "INCLUDE", "SCI-02": "EXCLUDE", "SCI-03": "EXCLUDE"},
    }
    # SCI-01: 3 inc, 1 exc -> INCLUDE
    # SCI-02: 1 inc, 3 exc -> EXCLUDE
    # SCI-03: 3 inc, 1 exc -> INCLUDE
    res = reconcile_multi_screener_decisions(screeners)
    assert res["reconciled"]["SCI-01"] == "INCLUDE"
    assert res["reconciled"]["SCI-02"] == "EXCLUDE"
    assert res["reconciled"]["SCI-03"] == "INCLUDE"
    assert len(res["ties"]) == 0
    assert "fleiss_kappa" in res

