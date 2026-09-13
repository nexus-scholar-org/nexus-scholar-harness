"""Recon evaluation gates (M0.7).

Anchor Provenance Rate (APR, ``13_evaluation.md`` section 2): the fraction of
shipped concepts/synonyms that carry at least one literature anchor DOI.  The
M0.3 wizard already enforces this per-term at emission time
(``inception._enforce_grounded_anchors``); this module exposes the invariant
as measurable, CI-callable functions so evaluation Dimension 1 can assert it.

Pool sufficiency and topical coherence (P5/P2, ``16_inception_improvements.md``
section E/F): ``compute_pool_sufficiency`` and ``compute_topic_purity`` gate the
recon signal independent of QEI, which is a dispersion index only.  Thresholds
are module constants (documented in ``13_evaluation.md`` section 3.5) so they
are configurable without touching the callers.
"""

from __future__ import annotations

from typing import Any

# P5 -- pool-size floor (thin pools: fintech n=8, materials n=6 in the 2026-09-13
# trial produced fragmentary directions and no topics layer; the coherent pools
# were all n=25).  Directions should not be proposed below this.
POOL_THIN_FLOOR = 12

# P2 -- topical coherence boundary (top-3 topic share).  Trial-calibrated on
# 2026-09-13: coherent oncology/climate/education pools ranged 0.53-0.80; a
# spread pool (robotics n_topics=10, top-3 share 0.53) sits right at the edge.
TOPIC_COHERENCE_TOP3_SHARE = 0.50


def compute_apr(anchored_terms: dict[str, list[str]]) -> float:
    """Return the Anchor Provenance Rate for a ``term -> anchor_dois`` map.

    1.0 when every key has at least one anchor DOI, ratio otherwise.  An empty
    map is vacuously anchored (returns 1.0).  Keys whose value is ``None`` or
    an empty list count as unanchored.
    """
    if not anchored_terms:
        return 1.0
    anchored = sum(1 for dois in anchored_terms.values() if dois)
    return anchored / len(anchored_terms)


def assert_apr(
    anchored_terms: dict[str, list[str]], *, threshold: float = 1.0
) -> float:
    """Compute APR; raise ``AssertionError`` when it falls below ``threshold``.

    Returns the computed APR (always ``>= threshold``) on success.
    """
    apr = compute_apr(anchored_terms)
    if apr < threshold - 1e-9:
        raise AssertionError(
            f"APR {apr:.4f} < required threshold {threshold:.4f}"
        )
    return apr


def compute_pool_sufficiency(n_docs: int) -> dict[str, Any]:
    """Assess whether a probe pool is large enough to anchor directions (P5).

    ``label`` is ``"sufficient"`` when ``n_docs >= POOL_THIN_FLOOR`` and
    ``"thin"`` otherwise.  Always returns the observed count and its threshold
    so consumers can apply their own cutoffs.  A thin pool should block or
    warn before directions are proposed (its taxonomy degrades into
    fragmentary n-grams -- see the fintech/materials rows of the multi-domain
    trial).
    """
    return {
        "n_docs": n_docs,
        "sufficient": n_docs >= POOL_THIN_FLOOR,
        "label": "sufficient" if n_docs >= POOL_THIN_FLOOR else "thin",
        "threshold": POOL_THIN_FLOOR,
    }


def compute_topic_purity(topics: list[dict]) -> dict[str, Any]:
    """Score a distilled ``topics`` layer for topical coherence (P2).

    ``label`` is one of:

    - ``"coherent"`` -- topics present and the top-3 labels cover at least
      ``TOPIC_COHERENCE_TOP3_SHARE`` of the anchored topic DOIs (few dominant
      in-field subfields);
    - ``"fragmented"`` -- topics present but spread thin (the pool spans many
      subfields);
    - ``"indeterminate"`` -- no topics at all (small or non-OpenAlex pools;
      the coherence signal is *absent*, not zero).

    ``purity`` is the rounded top-3 share (``None`` when indeterminate);
    ``top1_share``/``top3_share`` expose the raw concentration so consumers can
    apply their own cutoffs.  This is the signal QEI cannot provide: QEI is a
    lexical dispersion index that *inverts* on well-scoped semantic seeds.
    """
    if not isinstance(topics, list) or not topics:
        return {
            "label": "indeterminate",
            "purity": None,
            "n_topics": 0,
            "top1_share": None,
            "top3_share": None,
            "threshold": TOPIC_COHERENCE_TOP3_SHARE,
        }
    ordered = sorted(
        (t for t in topics if isinstance(t, dict) and isinstance(t.get("n"), int)),
        key=lambda t: -t["n"],
    )
    total = sum(t["n"] for t in ordered)
    if not ordered or total <= 0:
        return {
            "label": "indeterminate",
            "purity": None,
            "n_topics": len(ordered),
            "top1_share": None,
            "top3_share": None,
            "threshold": TOPIC_COHERENCE_TOP3_SHARE,
        }
    top1_share = ordered[0]["n"] / total
    top3_share = sum(t["n"] for t in ordered[:3]) / total
    label = "coherent" if top3_share >= TOPIC_COHERENCE_TOP3_SHARE else "fragmented"
    return {
        "label": label,
        "purity": round(top3_share, 4),
        "n_topics": len(ordered),
        "top1_share": round(top1_share, 4),
        "top3_share": round(top3_share, 4),
        "threshold": TOPIC_COHERENCE_TOP3_SHARE,
    }