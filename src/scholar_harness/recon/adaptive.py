"""Adaptive probe horizon (M0.4).

Two capabilities, pure stdlib:

1. :func:`plan_followups` -- detect thin sub-schools (``n <= 2`` and
   DOI-anchored in the pool) from a distilled terms dict plus its source
   pool, and return ordered follow-up probe candidates.  The distiller's
   schools ARE keyword term-clusters, so the thin-school rule covers the
   "school (or term-cluster)" signal of task T4.1.  Each candidate carries
   an explicit confidence ``reason`` string with the exact format::

       "<n> direct hits, <m> adjacent"

   where ``n`` is the number of pool docs directly anchored to the school
   (equals the school's ``n`` for distiller-emitted schools) and ``m`` is
   the residual "total docs in school minus ``n``" clamped at 0: every
   OTHER pool doc that shares at least one micro-taxonomy term with the
   school's anchors counts as modernization-adjacent evidence, so
   ``m = total docs in school - n``.  The string is non-empty whenever the
   school has at least one pool doc.  Both counts are always integers and
   never inflected (regex ``^\\d+ direct hits, \\d+ adjacent$``), keeping
   the string machine-parseable for later gap-direction merging.

2. :func:`execute_followups` -- boundedly probe the thin candidates
   (``max_followups`` probes, default 3, mirroring the M0.3 Step-5 budget),
   merge each follow-up pool into the ORIGINAL pool by DOI-union capped at
   :data:`POOL_MAX` (25) via :func:`merge_pools`, and re-distill the merged
   pool (with the caller's lexicon).

Merged result shape (stable contract, documented for consumers)::

    {
        "pool": dict,               # merged pool; docs capped at 25
        "distilled": dict,          # re-distilled terms over the merged pool
        "followups": list[dict],    # executed (probed) candidate dicts
        "cache_keys_merged": [str], # follow-up cache keys, in probe order
        "dropped_n": int,           # new follow-up docs discarded by the cap
    }

When the plan is empty no probe runs: the ORIGINAL pool and distilled dict
are returned unchanged with empty ``followups``/``cache_keys_merged`` and
``dropped_n == 0``.

``merge_pools`` preserves the FIRST (original) pool's ``cache_key`` and
``created_at``, appends previously-unseen DOIs in input-pool order until the
cap, and records every follow-up pool's ``cache_key`` in
``merged_from_cache_keys`` (follow-up probe lineage is preserved even when
the cap drops docs).  Each merged doc keeps its full pool entry
(``id/provider/doi/title/abstract/year/citations/oa_url``) untouched.

Workspace discipline: merging is purely in-memory -- no write path exists
here, so no ``workspaces/`` guard is needed.  The only on-disk writes in the
M0.4 flow are ``engine.probe``'s own ``pools/<sha>_pool.json`` writes, which
already carry the ``_assert_safe_output`` guard from :mod:`engine`.
"""

from __future__ import annotations

import json
from typing import Any

from .distiller import distill_pool
from .engine import POOL_MAX, ReconEngine
from .lexicon import DomainLexicon

_DOI_PREFIXES = ("https://doi.org/", "http://doi.org/", "doi:")


def _canon_doi(doi: Any) -> str | None:
    """Canonical, case-folded DOI or ``None`` when absent."""
    if doi is None:
        return None
    value = str(doi).strip().casefold()
    for prefix in _DOI_PREFIXES:
        value = value.removeprefix(prefix)
    return value or None


def _pool_dois(pool: dict[str, Any]) -> set[str]:
    dois: set[str] = set()
    docs = pool.get("docs")
    if not isinstance(docs, list):
        return dois
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        canon = _canon_doi(doc.get("doi"))
        if canon is not None:
            dois.add(canon)
    return dois


def _adjacent_count(school: dict[str, Any], distilled: dict[str, Any]) -> int:
    """Pool docs sharing a taxonomy term with the school's anchors.

    These are the "modernization-adjacent" evidence docs: they are IN the
    school's evidence neighborhood (sharing micro-taxonomy vocabulary with
    its anchors) without matching the school pattern themselves.
    """
    anchors = {_canon_doi(d) for d in (school.get("anchor_dois") or [])}
    anchors.discard(None)
    if not anchors:
        return 0
    term_to_dois: list[set[str]] = []
    for entry in distilled.get("micro_taxonomy") or []:
        if not isinstance(entry, dict):
            continue
        dois = {_canon_doi(d) for d in (entry.get("anchor_dois") or [])}
        dois.discard(None)
        if dois:
            term_to_dois.append(dois)
    neighbors: set[str] = set()
    for doi in anchors:
        for dois in term_to_dois:
            if doi in dois:
                neighbors |= dois
    neighbors -= anchors
    return len(neighbors)


def _reason(direct: int, adjacent: int) -> str:
    return f"{direct} direct hits, {adjacent} adjacent"


def plan_followups(distilled: dict[str, Any], pool: dict[str, Any]) -> list[dict[str, Any]]:
    """Plan follow-up probes for thin (``n <= 2``) DOI-anchored sub-schools.

    A candidate is emitted only when the school's label carries at least one
    anchor DOI that actually exists in ``pool``'s docs.  The ``reason`` field
    follows the exact format ``"<n> direct hits, <m> adjacent"`` (see the
    module docstring); ``m`` is the school's evidence neighborhood minus the
    direct hits, i.e. total docs in school minus ``n``, clamped at 0.

    Ordering is a fixed deterministic rule: ascending ``school_n`` (scarcest
    first), then lexicographic by case-folded term.
    """
    pool_dois = _pool_dois(pool)
    candidates: list[dict[str, Any]] = []
    for school in distilled.get("schools") or []:
        if not isinstance(school, dict):
            continue
        label = school.get("label")
        if not label:
            continue
        try:
            n = int(school.get("n", 0))
        except (TypeError, ValueError):
            n = 0
        anchors = [
            _canon_doi(d) for d in (school.get("anchor_dois") or [])
        ]
        anchored = [d for d in anchors if d is not None and d in pool_dois]
        if n > 2 or not anchored:
            continue
        direct = len(anchored)
        candidates.append(
            {
                "term": str(label),
                "reason": _reason(direct, _adjacent_count(school, distilled)),
                "school_n": n,
                "triggered": True,
            }
        )
    candidates.sort(key=lambda c: (c["school_n"], c["term"].casefold()))
    return candidates


def merge_pools(
    pools: list[dict[str, Any]], cap: int = POOL_MAX
) -> dict[str, Any]:
    """Merge pools by DOI-union, capped at ``cap`` (default 25).

    The FIRST pool's metadata is preserved and its docs keep their order;
    follow-up pools append previously-unseen DOIs in pool order until the
    cap.  A doc without a DOI cannot be keyed for dedup and passes through
    once each (still counting against the cap).  Follow-up pools' cache keys
    are recorded in ``merged_from_cache_keys`` even when no new doc fits, so
    the probe lineage is never lost to the cap.
    """
    if not pools:
        return {"docs": [], "merged_from_cache_keys": []}

    cache_keys_merged: list[str] = []
    for followup in pools[1:]:
        key = followup.get("cache_key")
        if key and key not in cache_keys_merged:
            cache_keys_merged.append(str(key))

    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for pool in pools:
        docs = pool.get("docs")
        if not isinstance(docs, list):
            continue
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            if len(merged) >= cap:
                break
            canon = _canon_doi(doc.get("doi"))
            if canon is not None:
                if canon in seen:
                    continue
                seen.add(canon)
            merged.append(dict(doc))

    result = dict(pools[0])
    result["docs"] = merged
    result["merged_from_cache_keys"] = cache_keys_merged
    return result


def _count_new_followup_docs(
    original: dict[str, Any], followups: list[dict[str, Any]]
) -> int:
    """Count follow-up docs that are new after DOI-union with the original pool.

    Mirrors ``merge_pools``' dedup semantics: a doc with a DOI is new iff its
    canonical DOI was not seen before; a doc without a DOI passes through
    once per occurrence.  The count is independent of the pool cap, so the
    driver can derive ``dropped_n`` from it.
    """
    seen = _pool_dois(original)
    new_total = 0
    for followup in followups:
        docs = followup.get("docs")
        if not isinstance(docs, list):
            continue
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            canon = _canon_doi(doc.get("doi"))
            if canon is None or canon not in seen:
                new_total += 1
                if canon is not None:
                    seen.add(canon)
    return new_total


async def execute_followups(
    pool: dict[str, Any],
    distilled: dict[str, Any],
    engine: ReconEngine,
    max_followups: int = 3,
    providers: list[str] | None = None,
    year_min: int = 2000,
    year_max: int | None = None,
    max_results: int = 25,
    lexicon: DomainLexicon | None = None,
) -> dict[str, Any]:
    """Probe the thin candidates, merge, and re-distill.

    ``engine.probe`` is called per candidate term (bounded by
    ``max_followups``); the engine cache reuses identical probes with no
    network calls.  ``lexicon`` (if given) is passed to the re-distillation;
    ``None`` means the distiller default, which keeps the CV/LLM tables.

    Returns the merged structure documented in the module docstring.  When
    the plan is empty, the unchanged ``pool``/``distilled`` are returned and
    no probe is issued (cheap path).
    """
    candidates = plan_followups(distilled, pool)
    executed = candidates[:max_followups]

    if not executed:
        return {
            "pool": pool,
            "distilled": distilled,
            "followups": [],
            "cache_keys_merged": [],
            "dropped_n": 0,
        }

    followup_pools: list[dict[str, Any]] = []
    for candidate in executed:
        pool_path, _n = await engine.probe(
            candidate["term"],
            providers=providers,
            year_min=year_min,
            year_max=year_max,
            max_results=max_results,
        )
        followup_pools.append(json.loads(pool_path.read_text(encoding="utf-8")))

    merged = merge_pools([pool, *followup_pools])
    new_total = _count_new_followup_docs(pool, followup_pools)
    original_n = len(pool.get("docs") or [])
    slots = max(0, POOL_MAX - original_n)
    dropped_n = max(0, new_total - slots)
    return {
        "pool": merged,
        "distilled": distill_pool(merged, lexicon),
        "followups": executed,
        "cache_keys_merged": list(merged.get("merged_from_cache_keys") or []),
        "dropped_n": dropped_n,
    }