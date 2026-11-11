"""What the pool says about the draft's concepts, and which papers to keep as seeds (M4d).

No language model: every number is a count of pool records whose title or
abstract contains a term as whole words (the INC-21 rule of
:func:`~scholar_harness.recon.session.term_occurs`).

* :func:`concept_report` gives, per concept, how many records anchor it and
  the pool terms that co-occur with it, which the researcher may tick one by
  one as synonyms (DoD 4). A term is offered only when it occurs in at least
  two of the records anchoring the concept and is neither a term of some
  concept nor a piece or an extension of one.
* :func:`seed_candidates` lists the records that anchor a direction or a
  concept, as candidate recall seeds (DoD 5).
"""

from __future__ import annotations

from typing import Any

from .distiller import _term_candidates
from .session import _normalize, term_occurs

#: A co-occurring term must occur in at least this many anchoring records.
SUGGESTION_MIN_RECORDS = 2
#: At most this many suggestions per concept.
SUGGESTION_LIMIT = 10


def _docs(pool: dict[str, Any]) -> list[dict[str, Any]]:
    return [d for d in pool.get("docs") or [] if isinstance(d, dict) and d.get("doi")]


def _text(doc: dict[str, Any]) -> str:
    return f"{doc.get('title') or ''} {doc.get('abstract') or ''}"


def _related(a: str, b: str) -> bool:
    """True when one term contains the other as whole words (hyphens ignored)."""
    na, nb = _normalize(a), _normalize(b)
    return na in nb or nb in na


def concept_report(pool: dict[str, Any], concepts: list[dict[str, Any]], source: str) -> list[dict[str, Any]]:
    """Per concept: its terms with counts, the records anchoring any of them, and pool suggestions.

    ``concepts`` are ``{concept, synonyms}``; ``source`` is ``draft`` or ``suggested``.
    """
    docs = _docs(pool)
    texts = [(str(d["doi"]), _text(d)) for d in docs]
    every_term = [t for c in concepts for t in [c.get("concept") or "", *(c.get("synonyms") or [])] if t.strip()]
    out = []
    for concept in concepts:
        terms = [t for t in [concept.get("concept") or "", *(concept.get("synonyms") or [])] if t.strip()]
        rows = []
        anchoring: list[tuple[str, str]] = []
        for term in terms:
            dois = sorted({doi for doi, text in texts if term_occurs(term, text)})
            rows.append({"term": term, "observed_in": len(dois), "anchor_dois": dois})
        for doi, text in texts:
            if any(term_occurs(t, text) for t in terms):
                anchoring.append((doi, text))
        counts: dict[str, int] = {}
        for _doi, text in anchoring:
            for candidate in _term_candidates(text.lower()):
                counts[candidate] = counts.get(candidate, 0) + 1
        suggestions = [
            {"term": term, "observed_in": n}
            for term, n in counts.items()
            if n >= SUGGESTION_MIN_RECORDS and not any(_related(term, known) for known in every_term)
        ]
        suggestions.sort(key=lambda s: (-s["observed_in"], s["term"]))
        out.append({
            "concept": concept.get("concept") or "",
            "source": source,
            "terms": rows,
            "anchored_in": len(anchoring),
            "suggestions": suggestions[:SUGGESTION_LIMIT],
        })
    return out


def seed_candidates(
    pool: dict[str, Any], directions: list[dict[str, Any]], concepts: list[str]
) -> list[dict[str, Any]]:
    """Pool records with a DOI that anchor at least one direction or concept, most anchors first."""
    papers = []
    for doc in _docs(pool):
        doi = str(doc["doi"])
        text = _text(doc)
        anchored_directions = [d["label"] for d in directions if doi in (d.get("anchor_dois") or [])]
        anchored_concepts = [c for c in concepts if c and term_occurs(c, text)]
        if not anchored_directions and not anchored_concepts:
            continue
        papers.append({
            "doi": doi,
            "title": doc.get("title"),
            "year": doc.get("year"),
            "provider": doc.get("provider"),
            "anchors": {"directions": anchored_directions, "concepts": anchored_concepts},
        })
    papers.sort(key=lambda p: (-(len(p["anchors"]["directions"]) + len(p["anchors"]["concepts"])), str(p["title"] or "")))
    return papers
