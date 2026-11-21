"""The query workbench's pure core (M11a; `docs/roadmap/milestones/M11a-query-workbench.md`).

A *version* of the query is what the researcher edits before (Inception) or
after (Plan) the protocol freezes: concepts joined by AND, each an OR group of
terms (its name first), a year window and languages, under a ``query_key``
(always ``main`` today; several queries per review are M3j).

* :func:`parse_version` validates a version sent by the browser.
* :func:`compile_version` builds the :class:`Query` with the genesis compiler
  (``protocol_adapter.compile_protocol_search`` on a protocol-shaped dict), so
  the workbench never writes a query string of its own.
* :func:`count_variants` lists what one Count asks of a database: the full
  query and, for two or more concepts, the query with each concept left out.
  :func:`synonym_variants` lists "what each synonym adds" for one concept.
* :func:`gain`, :func:`doubles` and :func:`largest` are the arithmetic the
  screen prints (the browser computes none of it).
* :func:`term_matches` and :func:`concepts_found` are the workbench's word
  match (decision 2026-11-20, M11a item 8): whole words, case, hyphens and
  punctuation ignored (as ``recon.session.term_occurs``), and English plurals
  folded by :func:`fold_word`. The direction rule (INC-21) is not changed.

Nothing here sends a request or writes a file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Any

from .models import Query
from .protocol_adapter import compile_protocol_search

#: The only query a protocol holds today; M3j may add others (contract decision).
DEFAULT_QUERY_KEY = "main"
QUERY_KEYS: tuple[str, ...] = (DEFAULT_QUERY_KEY,)
#: The concept note: leaving a concept out at least doubles a count (decision 2026-11-20, M11a item 6).
NOTE_RATIO = 2.0
#: "Read what this concept removes": how many records the one request reads.
REMOVED_SAMPLE = 25
#: The size of a version the engine takes (the draft's own limits).
MAX_CONCEPTS = 50
MAX_TERMS = 51
MAX_TERM_CHARS = 200
MIN_YEAR, MAX_YEAR = 1800, 2200


class VersionInvalid(ValueError):
    """A version that cannot be searched; the message names the first error."""


@dataclass(frozen=True)
class Concept:
    #: The concept's name, which is also its first term (as the compiler reads it).
    name: str
    terms: tuple[str, ...]


@dataclass(frozen=True)
class Version:
    concepts: tuple[Concept, ...]
    start_year: int | None = None
    end_year: int | None = None
    languages: tuple[str, ...] = ("en",)
    query_key: str = DEFAULT_QUERY_KEY

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_key": self.query_key,
            "concepts": [{"concept": c.name, "synonyms": list(c.terms[1:])} for c in self.concepts],
            "start_year": self.start_year, "end_year": self.end_year, "languages": list(self.languages),
        }

    @property
    def term_count(self) -> int:
        return sum(len(c.terms) for c in self.concepts)


@dataclass(frozen=True)
class Variant:
    #: ``full`` (the version itself), ``drop`` (one concept left out) or ``synonym`` (one term left out).
    kind: str
    version: Version
    concept_index: int | None = None
    concept: str | None = None
    term: str | None = None


def _year(value: Any, label: str) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not MIN_YEAR <= value <= MAX_YEAR:
        raise VersionInvalid(f"the {label} must be a year from {MIN_YEAR} to {MAX_YEAR}")
    return value


def _concept(item: Any, index: int) -> Concept | None:
    if not isinstance(item, dict):
        raise VersionInvalid(f"concept {index} is not a concept")
    raw = [item.get("concept") or ""] + list(item.get("synonyms") or [])
    terms: list[str] = []
    for value in raw:
        if not isinstance(value, str):
            raise VersionInvalid(f"concept {index} holds a term that is not text")
        term = " ".join(value.split())
        if len(term) > MAX_TERM_CHARS:
            raise VersionInvalid(f"a term of concept {index} is over {MAX_TERM_CHARS} characters")
        if term and term.casefold() not in {t.casefold() for t in terms}:
            terms.append(term)
    if not terms:
        return None
    if len(terms) > MAX_TERMS:
        raise VersionInvalid(f"concept {index} has more than {MAX_TERMS} terms")
    return Concept(terms[0], tuple(terms))


def parse_version(data: Any) -> Version:
    """A version from the browser's JSON; blank and repeated terms are dropped, a blank concept is skipped."""
    if not isinstance(data, dict):
        raise VersionInvalid("a version is an object")
    key = data.get("query_key") or DEFAULT_QUERY_KEY
    if key not in QUERY_KEYS:
        raise VersionInvalid(f"the only query of a review is 'main' (got {key!r})")
    items = data.get("concepts") or []
    if not isinstance(items, list) or len(items) > MAX_CONCEPTS:
        raise VersionInvalid(f"a version holds at most {MAX_CONCEPTS} concepts")
    concepts = tuple(c for i, item in enumerate(items) if (c := _concept(item, i)) is not None)
    if not concepts:
        raise VersionInvalid("a version needs at least one concept with a term")
    start, end = _year(data.get("start_year"), "start year"), _year(data.get("end_year"), "end year")
    if start is not None and end is not None and start > end:
        raise VersionInvalid("the start year is after the end year")
    languages = tuple(str(x).strip() for x in data.get("languages") or [] if str(x).strip()) or ("en",)
    return Version(concepts, start, end, languages, key)


def protocol_dict(version: Version) -> dict[str, Any]:
    """The protocol-shaped dict the genesis compiler reads (search fields only)."""
    return {
        "search_strategy": {
            "core_concepts": [{"concept": c.name, "synonyms": list(c.terms[1:]), "boolean_operator": "OR"}
                              for c in version.concepts],
            "date_range": {"start_year": version.start_year, "end_year": version.end_year},
            "languages": list(version.languages),
        },
    }


def compile_version(version: Version, *, cap: int | None = None) -> Query:
    """The :class:`Query` a harvest of this version would send (``max_results`` is ``cap``)."""
    query, _ = compile_protocol_search(protocol_dict(version))
    return replace(query, id=f"workbench-{version.query_key}", max_results=cap,
                   cap_source="protocol" if cap else "query")


def without_concept(version: Version, index: int) -> Version:
    _check_index(version, index)
    return replace(version, concepts=tuple(c for i, c in enumerate(version.concepts) if i != index))


def without_term(version: Version, index: int, term: str) -> Version | None:
    """The version without one term; a concept's only term leaves the concept out; ``None`` when nothing is left."""
    _check_index(version, index)
    concept = version.concepts[index]
    rest = tuple(t for t in concept.terms if t != term)
    if not rest:
        return None if len(version.concepts) == 1 else without_concept(version, index)
    concepts = list(version.concepts)
    concepts[index] = Concept(rest[0], rest)
    return replace(version, concepts=tuple(concepts))


def _check_index(version: Version, index: int) -> None:
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(version.concepts):
        raise VersionInvalid(f"this version has no concept {index}")


def count_variants(version: Version) -> list[Variant]:
    """What one Count asks a database: the full query, then each concept left out (two or more concepts)."""
    variants = [Variant("full", version)]
    if len(version.concepts) >= 2:
        variants += [Variant("drop", without_concept(version, i), i, c.name) for i, c in enumerate(version.concepts)]
    return variants


def synonym_variants(version: Version, index: int) -> list[Variant]:
    """The full query, then the query without each term of one concept (one request per term)."""
    _check_index(version, index)
    concept = version.concepts[index]
    out = [Variant("full", version)]
    for term in concept.terms:
        smaller = without_term(version, index, term)
        if smaller is not None:
            out.append(Variant("synonym", smaller, index, concept.name, term))
    return out


def gain(full: int | None, without: int | None) -> dict[str, Any]:
    """``without - full`` and ``without / full`` to one decimal (``None`` when it cannot be said)."""
    if not isinstance(full, int) or not isinstance(without, int):
        return {"gain": None, "ratio": None}
    return {"gain": without - full, "ratio": round(without / full, 1) if full > 0 else None}


def doubles(full: int | None, without: int | None) -> bool:
    """Whether leaving a concept out at least doubles the count (the note on the concept)."""
    if not isinstance(full, int) or not isinstance(without, int):
        return False
    return without > 0 if full == 0 else without >= NOTE_RATIO * full


def largest(cells: list[dict[str, Any]]) -> int | None:
    """The index of the cell with the largest positive gain, the first of a tie."""
    best: int | None = None
    for i, cell in enumerate(cells):
        value = cell.get("gain")
        if isinstance(value, int) and value > 0 and (best is None or value > cells[best]["gain"]):
            best = i
    return best


# --------------------------------------------------------------------------- the word match

_NON_WORD = re.compile(r"[^0-9a-z]+")


def fold_word(word: str) -> str:
    """One word's English singular for matching: ``-ies`` to ``-y``; ``-sses``, ``-xes``, ``-zes``,
    ``-ches``, ``-shes`` lose ``-es``; else a final ``-s`` goes, except after ``s``, ``u`` or ``i``.

    Words of three letters or fewer are kept. Both sides of a match are folded,
    so an irregular fold (``series`` to ``sery``) still matches itself.
    """
    w = word.casefold()
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith(("sses", "xes", "zes", "ches", "shes")):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "us", "is")):
        return w[:-1]
    return w


def words(text: str) -> list[str]:
    """The folded words of a text (case, hyphens and punctuation ignored)."""
    return [fold_word(w) for w in _NON_WORD.sub(" ", (text or "").casefold()).split()]


def _occurs(needle: list[str], hay: list[str]) -> bool:
    n = len(needle)
    return n > 0 and any(hay[i:i + n] == needle for i in range(len(hay) - n + 1))


def term_matches(term: str, text: str) -> bool:
    """``term`` occurs in ``text`` as consecutive whole words, plurals folded."""
    return _occurs(words(term), words(text))


def concepts_found(version: Version, text: str) -> list[bool]:
    """Per concept, whether a term of it occurs in ``text``."""
    hay = words(text)
    return [any(_occurs(words(t), hay) for t in c.terms) for c in version.concepts]


def lacking(version: Version, text: str) -> list[str]:
    """The names of the concepts no term of which occurs in ``text``."""
    return [c.name for c, found in zip(version.concepts, concepts_found(version, text)) if not found]


def matches(version: Version, text: str) -> bool:
    """Whether ``text`` holds a term of every concept (the query's AND by words)."""
    return all(concepts_found(version, text))
