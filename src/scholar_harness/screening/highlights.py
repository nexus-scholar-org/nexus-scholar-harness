"""What the Triage record marks: search terms and the agent's quotes (M8b-triage-highlights).

Both are read-only views for the record pane (``docs/decisions.md`` 2026-11-21,
M8b items 12 and 13). Offsets count UTF-16 code units in the title or the
abstract exactly as ``GET /records/{study_id}`` serves them, so the browser
slices its strings without converting. Nothing here is stored or journaled.
"""

from __future__ import annotations

from typing import Any

from ..term_match import concept_marks, concept_terms, utf16_offset
from .agent_runs import _text
from .proposals import record_text

FIELDS = ("title", "abstract")


def search_terms(protocol: dict[str, Any], title: str | None, abstract: str | None) -> dict[str, Any]:
    """The protocol's concepts in order, each with its words and mentions, and the marks per field."""
    raw = (protocol.get("search_strategy") or {}).get("core_concepts") or []
    concepts = [c for c in raw if isinstance(c, dict) and concept_terms(c)]
    texts = {"title": title or "", "abstract": abstract or ""}
    mentions = [0] * len(concepts)
    marks: list[dict[str, Any]] = []
    for field in FIELDS:
        text = texts[field]
        spans, counts = concept_marks(text, concepts)
        mentions = [a + b for a, b in zip(mentions, counts, strict=True)]
        marks.extend(
            {"field": field, "start": utf16_offset(text, s), "end": utf16_offset(text, e), "concept": c}
            for s, e, c in spans
        )
    return {
        "concepts": [
            {"concept": concept_terms(c)[0], "terms": concept_terms(c), "mentions": n}
            for c, n in zip(concepts, mentions, strict=True)
        ],
        "marks": marks,
    }


def quote_places(criteria: Any, paper: dict[str, Any]) -> list[dict[str, Any]]:
    """For each answer that quotes the record, whether the quote is at its offsets, and where it shows.

    The record text is rebuilt as the run built it (title, blank line, stripped
    abstract, the year line). A found quote inside the title or the abstract
    gets its place in that field as served; one in the year line, or across
    the two fields, is found with no place.
    """
    title, abstract, year = _text(paper)
    text = record_text(title, abstract, year)
    served_title = str(paper.get("title") or "")
    served_abstract = str(paper.get("abstract") or "")
    lead = len(served_abstract) - len(served_abstract.lstrip())
    abstract_at = len(title or "") + 2
    out: list[dict[str, Any]] = []
    for answer in criteria if isinstance(criteria, list) else []:
        if not isinstance(answer, dict) or answer.get("answer") == "not_reported":
            continue
        evidence = answer.get("evidence") if isinstance(answer.get("evidence"), dict) else {}
        quote, start, end = evidence.get("text"), evidence.get("start"), evidence.get("end")
        if not (isinstance(quote, str) and quote):
            continue
        found = (
            isinstance(start, int) and isinstance(end, int) and 0 <= start < end and text[start:end] == quote
        )
        place: dict[str, Any] = {"field": None, "start": None, "end": None}
        if found and end <= len(title or ""):
            place = {"field": "title", "start": utf16_offset(served_title, start), "end": utf16_offset(served_title, end)}
        elif found and abstract and start >= abstract_at and end <= abstract_at + len(abstract):
            s, e = start - abstract_at + lead, end - abstract_at + lead
            place = {
                "field": "abstract",
                "start": utf16_offset(served_abstract, s),
                "end": utf16_offset(served_abstract, e),
            }
        out.append({"criterion_id": answer.get("id"), "answer": answer.get("answer"), "found": found, **place})
    return out
