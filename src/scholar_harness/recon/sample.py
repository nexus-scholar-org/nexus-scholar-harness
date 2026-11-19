"""Sample curation (M10b Part C, ``02-explore`` "Sample curation (M10b)").

The researcher can leave a paper of the Explore sample out ("Not relevant").
The pool file is content-addressed and shared between drafts, so it is never
rewritten: the exclusions are kept on the draft record and applied when the
pool is read. :func:`effective_pool` is that reading: the first
:data:`~scholar_harness.recon.engine.POOL_MAX` papers of ``docs`` then
``reserve`` (the records the probe fetched beyond the first 25, in the order
the sample would have taken them next) that are not left out.

The fingerprint of a pool stays the raw pool's (``session.pool_fingerprint``);
a bound direction learns about a changed sample through
:func:`exclusions_digest` (``SAMPLE_CHANGED`` in ``grounding.check_binding``).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from typing import Any

from .engine import POOL_MAX
from .gates import POOL_THIN_FLOOR

#: The reason recorded for every exclusion (the only one the screen offers).
NOT_RELEVANT = "NOT_RELEVANT"
#: Keys a draft can hold (``SAMPLE_EXCLUSIONS_FULL``).
SAMPLE_EXCLUSIONS_MAX = 200
#: Keys one call may add or remove.
SAMPLE_CALL_MAX = POOL_MAX
#: Below this many papers the engine recommends another search (the floor of the thin-pool tile).
SAMPLE_RECOMMEND_SEARCH_BELOW = POOL_THIN_FLOOR
#: At or above this share of left-out papers the engine recommends changing the question.
SAMPLE_OFFTOPIC_SHARE = 0.5

BELOW_FLOOR = "BELOW_FLOOR"
MOSTLY_OFF_TOPIC = "MOSTLY_OFF_TOPIC"


def paper_key(doc: dict[str, Any]) -> str:
    """The engine's key of a pool paper: its DOI, else its pool ``id`` (``provider|provider_id``)."""
    doi = doc.get("doi")
    return str(doi) if doi else str(doc.get("id") or "")


def keys_of(exclusions: dict[str, Any] | None) -> list[str]:
    """The left-out keys of a draft record's ``sample_exclusions``, in the order they were left out."""
    items = (exclusions or {}).get("items") or []
    return [str(i["key"]) for i in items if isinstance(i, dict) and i.get("key")]


def exclusions_digest(keys: Iterable[str]) -> str:
    """``sha256:`` of the sorted keys; the digest of no key is the digest of ``[]``."""
    canonical = json.dumps(sorted(set(keys)), separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _candidates(pool: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for doc in [*(pool.get("docs") or []), *(pool.get("reserve") or [])]:
        if not isinstance(doc, dict):
            continue
        key = paper_key(doc)
        if key and key not in seen:
            seen.add(key)
            out.append(doc)
    return out


def effective_pool(pool: dict[str, Any], exclusions: Iterable[str] | None) -> dict[str, Any]:
    """The pool the later steps read: at most 25 papers of ``docs + reserve`` that are not left out.

    A copy of ``pool`` with ``docs`` replaced and ``reserve`` dropped, so no
    reader counts a reserve paper. A paper that came in from the reserve
    carries ``added_for``: the key of the left-out paper it replaced (the
    first left-out sample paper without a replacement, in sample order). With
    no exclusion the docs are the pool's own, in its order.
    """
    left = set(exclusions or ())
    raw_docs = [d for d in pool.get("docs") or [] if isinstance(d, dict)]
    candidates = _candidates(pool)
    if not left & {paper_key(d) for d in candidates}:
        # Nothing of this pool is left out: its own sample, as stored (two papers without
        # a DOI or a provider id share a key and must not replace each other; review of Part C, finding 4).
        return {**{k: v for k, v in pool.items() if k != "reserve"}, "docs": raw_docs}
    kept = [d for d in candidates if paper_key(d) not in left][:POOL_MAX]
    in_sample = {paper_key(d) for d in raw_docs}
    replaced = [paper_key(d) for d in raw_docs if paper_key(d) in left]
    docs: list[dict[str, Any]] = []
    for doc in kept:
        if paper_key(doc) in in_sample:
            docs.append(doc)
        else:
            docs.append({**doc, "added_for": replaced.pop(0) if replaced else None})
    out = {k: v for k, v in pool.items() if k != "reserve"}
    out["docs"] = docs
    return out


def view(pool: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    """The ``sample`` object of ``GET``/``POST .../recon/sample`` for a draft record and its latest pool."""
    items = [i for i in ((record.get("sample_exclusions") or {}).get("items") or []) if isinstance(i, dict)]
    keys = [str(i.get("key")) for i in items]
    effective = effective_pool(pool, keys)
    candidates = {paper_key(d) for d in _candidates(pool)}
    raw_n = len([d for d in pool.get("docs") or [] if isinstance(d, dict)])
    used = {paper_key(d) for d in effective["docs"]}
    reserve_left = sum(1 for d in _candidates(pool) if paper_key(d) not in used and paper_key(d) not in set(keys))
    excluded = [
        {
            "key": i.get("key"), "doi": i.get("doi"), "title": i.get("title"), "year": i.get("year"),
            "provider": i.get("provider"), "excluded_at": i.get("excluded_at"), "in_pool": str(i.get("key")) in candidates,
        }
        for i in items
    ]
    n = len(effective["docs"])
    marked = sum(1 for e in excluded if e["in_pool"])
    share = round(marked / (marked + n), 4) if marked + n else 0.0
    reasons = []
    if n < SAMPLE_RECOMMEND_SEARCH_BELOW:
        reasons.append(BELOW_FLOOR)
    if marked and share >= SAMPLE_OFFTOPIC_SHARE:
        reasons.append(MOSTLY_OFF_TOPIC)
    return {
        "n_docs": n,
        "n_docs_raw": raw_n,
        "max_docs": POOL_MAX,
        "reserve_n": reserve_left,
        # A pool stored before replacements were kept has no ``reserve`` key (02-explore "Refill").
        "has_reserve": "reserve" in pool,
        "excluded": excluded,
        "excluded_in_pool": marked,
        "recommend": {
            "search": bool(reasons),
            "reason": reasons[0] if reasons else None,
            "reasons": reasons,
            "threshold": {"floor": SAMPLE_RECOMMEND_SEARCH_BELOW, "share": SAMPLE_OFFTOPIC_SHARE},
            "marked_share": share,
        },
        "exclusions_digest": exclusions_digest(keys),
    }


class SampleRefused(RuntimeError):
    def __init__(self, code: str, message: str, status: int = 422, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code, self.message, self.status, self.details = code, message, status, details or {}


#: Refusal codes (also in ``console/refusals.py``).
PAPER_UNKNOWN = "PAPER_UNKNOWN"
SAMPLE_EXCLUSIONS_FULL = "SAMPLE_EXCLUSIONS_FULL"


def change(
    record: dict[str, Any], pool: dict[str, Any], pool_fp: str, *, add: list[str], remove: list[str], now: str,
) -> None:
    """Leave ``add`` out and put ``remove`` back, on ``record`` (inside the draft lock).

    Idempotent: leaving out a paper already left out, or putting back one that
    is not left out, changes nothing. A key to leave out must be a paper of
    the current sample (``PAPER_UNKNOWN`` otherwise, nothing changed); a key
    to put back must be left out or in the pool. Past
    :data:`SAMPLE_EXCLUSIONS_MAX` keys: ``SAMPLE_EXCLUSIONS_FULL``.
    """
    current = (record.get("sample_exclusions") or {}).get("items") or []
    items = [dict(i) for i in current if isinstance(i, dict)]
    have = {str(i.get("key")) for i in items}
    shown = {paper_key(d): d for d in effective_pool(pool, have)["docs"]}
    known = {paper_key(d) for d in _candidates(pool)}
    unknown = sorted({k for k in add if k not in shown and k not in have} | {k for k in remove if k not in have and k not in known})
    if unknown:
        raise SampleRefused(PAPER_UNKNOWN, "That paper is not in this sample.", details={"keys": unknown})
    drop = set(remove)
    items = [i for i in items if str(i.get("key")) not in drop]
    have = {str(i.get("key")) for i in items}
    for key in dict.fromkeys(add):
        if key in have or key in drop:
            continue
        doc = shown[key]
        items.append({
            "key": key, "doi": doc.get("doi"), "title": doc.get("title"), "year": doc.get("year"),
            "provider": doc.get("provider"), "reason": NOT_RELEVANT, "excluded_at": now, "pool_fingerprint": pool_fp,
        })
        have.add(key)
    if len(items) > SAMPLE_EXCLUSIONS_MAX:
        raise SampleRefused(
            SAMPLE_EXCLUSIONS_FULL, f"A draft can record {SAMPLE_EXCLUSIONS_MAX} papers left out.",
            details={"limit": SAMPLE_EXCLUSIONS_MAX},
        )
    record["sample_exclusions"] = {"items": items}


def genesis_context(record: dict[str, Any], pool: dict[str, Any] | None) -> dict[str, Any]:
    """The ``sample_exclusions`` block of ``recon_context`` (``audit/recon_context.json``)."""
    items = [i for i in ((record.get("sample_exclusions") or {}).get("items") or []) if isinstance(i, dict)]
    keys = [str(i.get("key")) for i in items]
    raw_n = len((pool or {}).get("docs") or [])
    effective = effective_pool(pool or {}, keys)["docs"] if pool else []
    return {
        "n": len(items),
        "reason": NOT_RELEVANT,
        "decided_by": "researcher",
        "pool_n_docs_raw": raw_n,
        "effective_n_docs": len(effective),
        "refilled_from_reserve": sum(1 for d in effective if "added_for" in d),
        "items": [{k: i.get(k) for k in ("key", "doi", "title", "provider", "excluded_at", "pool_fingerprint")} for i in items],
    }
