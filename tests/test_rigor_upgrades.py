"""Tests for verbatim claim verifier and multi-screener adjudication."""

from pathlib import Path
from scholar_verify.verbatim import (
    VerbatimClaimVerifier,
    char_window_coverage,
    normalize_scientific_text,
    token_ngram_coverage,
)
from scholar_search.screening import (
    calculate_fleiss_kappa,
    reconcile_multi_screener_decisions,
)


def test_normalize_scientific_text():
    raw = "Multi-agent sys-\n tems  •  evaluate [“retrieval”]"
    norm = normalize_scientific_text(raw)
    assert "sys- tems" not in norm
    assert "systems" in norm
    assert "-" in norm
    assert '"retrieval"' in norm


def test_verbatim_coverage_exact_match():
    source = "Large language models demonstrate strong potential in systematic review screening but suffer from hallucinations."
    quote = "strong potential in systematic review screening"
    
    char_cov = char_window_coverage(quote, source)
    token_cov = token_ngram_coverage(quote, source)
    assert char_cov >= 0.95
    assert token_cov >= 0.95


def test_verbatim_claim_verifier():
    verifier = VerbatimClaimVerifier(threshold=0.90)
    claims = [
        {
            "claim_id": "C-01",
            "study_id": "SCI-001",
            "evidence_quote": "OpenScholar-8B produced zero hallucinated cited papers."
        },
        {
            "claim_id": "C-02",
            "study_id": "SCI-001",
            "evidence_quote": "Completely fabricated text that does not exist."
        }
    ]
    sources = {
        "SCI-001": "In empirical benchmarks, OpenScholar-8B produced zero hallucinated cited papers compared to baselines."
    }
    results, metrics = verifier.verify_claims_ledger(claims, sources)
    assert metrics["total_claims"] == 2
    assert metrics["verified_claims"] == 1
    assert metrics["failed_claims"] == 1
    assert results[0].is_verified is True
    assert results[1].is_verified is False


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

