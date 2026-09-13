"""Hermetic tests for M0.7 T7.1 recon evaluation gates (Anchor Provenance Rate).

``13_evaluation.md`` Dimension 1 makes APR a first-class contract: the
fraction of shipped concepts/synonyms that carry at least one literature
anchor DOI.  The M0.3 grounded wizard already guarantees ``1.0`` at emission
time (DoD 3); these tests pin the measurable functions used by the CI/eval
surfaces and prove the grounded recon context clears the gate.
"""

import pytest
from scholar_search.models import Document, ExternalIds

from scholar_harness.inception import _run_grounded_recon
from scholar_harness.recon import ReconEngine
from scholar_harness.recon.gates import (
    POOL_THIN_FLOOR,
    TOPIC_COHERENCE_TOP3_SHARE,
    assert_apr,
    compute_apr,
    compute_pool_sufficiency,
    compute_topic_purity,
)

TOPIC = "grape disease detection for vineyard robots"


def _doc(doi: str, title: str, abstract: str) -> Document:
    return Document(
        title=title,
        year=2023,
        provider="openalex",
        provider_id="W" + doi.replace("/", "").replace(":", "")[:20],
        external_ids=ExternalIds(doi=doi),
        abstract=abstract,
        citations_count=5,
        url=f"https://example.org/{doi}",
    )


def _fake_docs() -> list[Document]:
    return [
        _doc(
            "10.1000/ground-001",
            "Fake Doc 1",
            "We benchmark grape disease detection on an embedded orchard "
            "vision system with aerial field images.",
        ),
        _doc(
            "10.1000/ground-002",
            "Fake Doc 2",
            "Automated grape disease detection improves yield monitoring "
            "accuracy for precision agriculture practitioners.",
        ),
        _doc(
            "10.1000/ground-003",
            "Fake Doc 3",
            "A review of grape disease detection techniques for vineyard "
            "robots reports open challenges.",
        ),
    ]


class _SilentResponder:
    """Never consulted in headless mode; raises if a prompt sneaks in."""

    def __getattr__(self, name):
        raise AssertionError(f"headless grounded recon must not prompt ({name})")


def _grounded_context(tmp_path) -> dict:
    engine = ReconEngine(
        cache_root=tmp_path / "cache", search_fn=lambda q, p: _fake_docs()
    )
    return _run_grounded_recon(_SilentResponder(), TOPIC, engine, auto_select=True)


# ---------------------------------------------------------------------------
# Pure gate math
# ---------------------------------------------------------------------------


def test_empty_anchor_map_is_vacuously_anchored():
    assert compute_apr({}) == 1.0
    assert assert_apr({}) == 1.0


def test_all_terms_anchored_scores_one():
    anchored = {
        "grape disease detection": ["10.1000/a", "10.1000/b"],
        "vineyard blight": ["10.1000/c"],
    }
    assert compute_apr(anchored) == 1.0
    assert assert_apr(anchored) == 1.0


def test_unanchored_keys_lower_the_rate():
    anchored = {
        "grape disease detection": ["10.1000/a"],
        "phantom concept": [],
        "ghost synonym": None,
    }
    assert compute_apr(anchored) == pytest.approx(1 / 3)
    assert compute_apr(anchored) < 1.0
    try:
        assert_apr(anchored)
    except AssertionError as exc:
        assert "APR 0.3333 < required threshold 1.0000" in str(exc)
    else:
        raise AssertionError("assert_apr must reject a 1/3 map at threshold 1.0")


def test_zero_anchors_scores_zero():
    assert compute_apr({"a": [], "b": None, "c": []}) == 0.0
    try:
        assert_apr({"a": []}, threshold=0.5)
    except AssertionError as exc:
        assert "APR 0.0000" in str(exc)
    else:
        raise AssertionError("assert_apr must reject a 0.0 map at threshold 0.5")


def test_lower_threshold_accepts_partial():
    anchored = {"a": ["10.1000/a"], "b": []}
    assert assert_apr(anchored, threshold=0.5) == 0.5


# ---------------------------------------------------------------------------
# The M0.3 grounded context is itself gate-clean (DoD 3 as a metric)
# ---------------------------------------------------------------------------


def test_grounded_recon_context_achieves_perfect_apr(tmp_path):
    rc = _grounded_context(tmp_path)
    assert rc["anchored_terms"]
    assert compute_apr(rc["anchored_terms"]) == 1.0
    assert assert_apr(rc["anchored_terms"]) == 1.0


def test_tampered_anchor_map_fails_the_gate(tmp_path):
    rc = _grounded_context(tmp_path)
    tampered = dict(rc["anchored_terms"])
    tampered["unverified extra concept"] = []
    assert compute_apr(tampered) < 1.0
    try:
        assert_apr(tampered)
    except AssertionError as exc:
        assert "APR" in str(exc)
    else:
        raise AssertionError("assert_apr must reject the tampered map")


# ---------------------------------------------------------------------------
# P5 (pool-size floor) + P2 (topical coherence), 16_inception_improvements.md
# ---------------------------------------------------------------------------


def test_pool_sufficiency_threshold_and_labels():
    assert POOL_THIN_FLOOR == 12
    # Thin pools: fintech n=8 and materials n=6 produced fragmentary
    # directions and no topics layer in the 2026-09-13 multi-domain trial.
    for n_docs in (0, 1, 8, 11):
        gate = compute_pool_sufficiency(n_docs)
        assert gate["label"] == "thin"
        assert gate["sufficient"] is False
        assert gate["n_docs"] == n_docs
    for n_docs in (12, 13, 25):
        gate = compute_pool_sufficiency(n_docs)
        assert gate["label"] == "sufficient"
        assert gate["sufficient"] is True
    assert compute_pool_sufficiency(12)["threshold"] == POOL_THIN_FLOOR


def _topic(n_docs: int, label: str = "T") -> dict:
    return {"label": label, "n": n_docs, "score": 0.9, "anchor_dois": []}


def test_topic_purity_empty_is_indeterminate_not_zero():
    gate = compute_topic_purity([])
    assert gate["label"] == "indeterminate"
    assert gate["purity"] is None
    assert gate["top1_share"] is None
    assert gate["top3_share"] is None
    assert gate["n_topics"] == 0
    # Absence of the signal is a fact, not a "0 coherence" verdict.
    assert gate["threshold"] == TOPIC_COHERENCE_TOP3_SHARE


def test_topic_purity_all_zero_counts_is_indeterminate():
    gate = compute_topic_purity([_topic(0, "A"), _topic(0, "B")])
    assert gate["label"] == "indeterminate"
    assert gate["purity"] is None


def test_topic_purity_coherent_when_top3_dominate():
    # Trial-calibrated: oncology/climate/education pools had top-3 topic
    # shares of 0.53-0.80; e.g. oncology n=(5,4,3,1,1,1) -> 12/15 = 0.8.
    topics = [_topic(1, "F"), _topic(5, "A"), _topic(1, "E"),
              _topic(4, "B"), _topic(3, "C"), _topic(1, "D")]
    gate = compute_topic_purity(topics)  # input order must not matter (sorted)
    assert gate["label"] == "coherent"
    assert gate["purity"] == pytest.approx(0.8)
    assert gate["top3_share"] == pytest.approx(0.8)
    assert gate["top1_share"] == pytest.approx(5 / 15, abs=1e-4)
    assert gate["n_topics"] == 6


def test_topic_purity_coherent_at_boundary():
    topics = [_topic(1, f"T{i}") for i in range(6)]  # top3 share = 3/6 = 0.5 >= 0.5
    gate = compute_topic_purity(topics)
    assert gate["label"] == "coherent"
    assert gate["purity"] == pytest.approx(0.5)


def test_topic_purity_fragmented_when_spread_thin():
    topics = [_topic(1, f"T{i}") for i in range(10)]  # top3 share = 0.3 < 0.5
    gate = compute_topic_purity(topics)
    assert gate["label"] == "fragmented"
    assert gate["purity"] == pytest.approx(0.3)
    assert gate["n_topics"] == 10