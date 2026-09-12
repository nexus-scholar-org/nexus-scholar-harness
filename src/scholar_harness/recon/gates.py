"""Recon evaluation gates (M0.7).

Anchor Provenance Rate (APR, ``13_evaluation.md`` section 2): the fraction of
shipped concepts/synonyms that carry at least one literature anchor DOI.  The
M0.3 wizard already enforces this per-term at emission time
(``inception._enforce_grounded_anchors``); this module exposes the invariant
as measurable, CI-callable functions so evaluation Dimension 1 can assert it.
"""

from __future__ import annotations


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