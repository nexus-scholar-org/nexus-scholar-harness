"""Grounded evidence on an inception draft (M4c).

Binding a direction writes ``grounding`` onto the draft record (beside
``draft``, never inside it): the client saves the draft, the engine alone
writes the grounding, so a ``PUT`` of the draft can neither forge nor drop it.
A draft that was never bound has no ``grounding`` and behaves as in M4b.

The grounding names the pool it was shaped on by its fingerprint and
``created_at``. :func:`check_binding` refuses with ``STALE_BINDING`` when the
recon session's latest pool is no longer that pool (a refresh, a narrower
search or a gap check ran after binding) or the pool file changed.

Per-RQ evidence is computed when the draft is previewed or emitted, because
the research questions are written after the direction is chosen.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..recon.directions import _grounded_default_concepts
from ..recon.gates import POOL_THIN_FLOOR, compute_apr_observed
from ..recon.session import (
    DIRECTION_UNKNOWN,
    NO_DIRECTION,
    POOL_TOO_SMALL,
    ReconRefused,
    ReconSessions,
    pool_fingerprint,
    term_evidence,
    term_occurs,
)

STALE_BINDING = "STALE_BINDING"
#: A direction the researcher wrote is grounded once it occurs in this many records (as a pool direction).
OWN_DIRECTION_MIN_ANCHORS = 2


def _now() -> str:
    return datetime.now(UTC).isoformat()


def build_grounding(
    sessions: ReconSessions,
    session_id: str,
    *,
    direction: str | None = None,
    own: str | None = None,
    accept_thin_pool: bool = False,
) -> dict[str, Any]:
    """The grounding for one chosen direction on the session's latest pool.

    ``direction`` is the label of a proposed direction; ``own`` is a direction
    the researcher wrote, recorded as ungrounded unless it occurs in at least
    two records of the pool. A pool under the floor of 12 refuses
    ``POOL_TOO_SMALL`` unless ``accept_thin_pool``.
    """
    if bool(direction) == bool(own):
        raise ReconRefused(NO_DIRECTION, "Choose one of the proposed directions or write your own.", status=422)
    found = sessions.directions(session_id)
    pool_summary = found["pool"]
    n_docs = pool_summary["n_docs"]
    if n_docs < POOL_THIN_FLOOR and not accept_thin_pool:
        raise ReconRefused(
            POOL_TOO_SMALL,
            f"The pool has {n_docs} papers, under the floor of {POOL_THIN_FLOOR}; directions from it are often "
            "fragments. Widen the search, or confirm that you accept a thin pool.",
            details={"n_docs": n_docs, "floor": POOL_THIN_FLOOR},
        )
    pool = json.loads(Path(pool_summary["path"]).read_text(encoding="utf-8"))
    distilled = found["distilled"]
    if direction:
        chosen = next((d for d in found["directions"] if d["label"] == direction), None)
        if chosen is None:
            raise ReconRefused(
                DIRECTION_UNKNOWN,
                f"'{direction}' is not one of the directions of the current pool.",
                status=422,
                details={"directions": [d["label"] for d in found["directions"]]},
            )
        chosen = {**chosen, "source": "pool", "grounded": True}
    else:
        own = (own or "").strip()
        ev = term_evidence(pool, own)
        chosen = {
            "label": own,
            "concept": own,
            "anchor_dois": ev["anchor_dois"],
            "observed_in": ev["observed_in"],
            "n_docs": n_docs,
            "schools": [],
            "detail": f"your direction; it occurs in {ev['observed_in']} of {n_docs} titles or abstracts",
            "source": "researcher",
            "grounded": ev["observed_in"] >= OWN_DIRECTION_MIN_ANCHORS,
        }
    anchored_terms: dict[str, list[str]] = {}
    if chosen["anchor_dois"]:
        anchored_terms[chosen["concept"]] = list(chosen["anchor_dois"])
    for t in distilled.get("micro_taxonomy", []):
        if t["anchor_dois"]:
            anchored_terms.setdefault(t["term"], list(t["anchor_dois"]))
    session = sessions.load(session_id)
    evidence = {
        chosen["concept"]: term_evidence(pool, chosen["concept"]),
    }
    topic = session.get("topic")
    if topic:
        evidence[topic] = term_evidence(pool, topic)
    return {
        "session_id": session_id,
        "bound_at": _now(),
        "pool": {k: pool_summary[k] for k in ("fingerprint", "created_at", "cache_key", "path", "status", "query", "n_docs", "legs")},
        "direction": chosen,
        "anchors": sorted(chosen["anchor_dois"]),
        "default_concepts": _grounded_default_concepts(distilled, chosen["concept"]),
        "anchored_terms": anchored_terms,
        "term_evidence": evidence,
    }


def check_binding(sessions: ReconSessions, grounding: dict[str, Any]) -> dict[str, Any]:
    """``{"stale": False}``, or ``{"stale": True, "reason", "bound", "current"}``."""
    bound = (grounding.get("pool") or {}).get("fingerprint")
    path = Path((grounding.get("pool") or {}).get("path") or "")
    try:
        on_disk = pool_fingerprint(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return {"stale": True, "reason": "the bound pool file is gone", "bound": bound, "current": None}
    if on_disk != bound:
        return {"stale": True, "reason": "the bound pool file changed", "bound": bound, "current": on_disk}
    try:
        latest, _ = sessions.latest_pool(grounding["session_id"])
    except ReconRefused:
        return {"stale": True, "reason": "the recon session is gone", "bound": bound, "current": None}
    current = pool_fingerprint(latest)
    if current != bound:
        return {"stale": True, "reason": "the session searched again after this direction was chosen", "bound": bound, "current": current}
    return {"stale": False, "bound": bound, "current": current}


def refuse_stale(sessions: ReconSessions, grounding: dict[str, Any]) -> None:
    state = check_binding(sessions, grounding)
    if state["stale"]:
        raise ReconRefused(
            STALE_BINDING,
            f"The direction was chosen on a pool that no longer matches ({state['reason']}). "
            "Choose the direction again on the current pool.",
            details=state,
        )


def rq_evidence(rqs: list[str], grounding: dict[str, Any]) -> list[dict[str, Any]]:
    """For each RQ, the anchored terms of the bound pool that occur in its text, with their DOIs."""
    out = []
    anchored = grounding.get("anchored_terms") or {}
    for rq in rqs:
        terms = [
            {"term": term, "anchor_dois": sorted(dois)}
            for term, dois in anchored.items()
            if dois and term_occurs(term, rq)
        ]
        terms.sort(key=lambda t: (-len(t["term"].split()), -len(t["anchor_dois"]), t["term"]))
        dois = sorted({d for t in terms for d in t["anchor_dois"]})
        out.append({"rq": rq, "terms": terms, "anchor_dois": dois})
    return out


def concept_evidence(concepts: list[str], grounding: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Each concept's occurrence in the bound pool (no new search)."""
    path = Path((grounding.get("pool") or {}).get("path") or "")
    try:
        pool = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {c: term_evidence(pool, c) for c in concepts if c}


def recon_context(grounding: dict[str, Any], rqs: list[str], concepts: list[str]) -> dict[str, Any]:
    """The ``recon_context`` genesis writes to ``audit/recon_context.json`` for a bound draft."""
    pool = grounding.get("pool") or {}
    direction = grounding.get("direction") or {}
    evidence = {**(grounding.get("term_evidence") or {}), **concept_evidence(concepts, grounding)}
    return {
        "session_id": grounding.get("session_id"),
        "source": "console",
        "bound_at": grounding.get("bound_at"),
        "cache_keys": [pool.get("cache_key")] if pool.get("cache_key") else [],
        "pool_sizes": [pool.get("n_docs", 0)],
        "pool_created_at": [pool.get("created_at")],
        "pool_fingerprints": [pool.get("fingerprint")],
        "pool_legs": pool.get("legs") or [],
        "anchor_dois": list(grounding.get("anchors") or []),
        "direction": direction.get("label"),
        "direction_source": direction.get("source"),
        "direction_grounded": direction.get("grounded"),
        "concept": direction.get("concept"),
        "default_concepts": list(grounding.get("default_concepts") or []),
        "anchored_terms": dict(grounding.get("anchored_terms") or {}),
        "term_evidence": evidence,
        "apr_observed": compute_apr_observed({c: evidence[c] for c in concepts if c in evidence}),
        "rq_evidence": rq_evidence(rqs, grounding),
    }

