"""Where a search term occurs in a text, as spans (M8b-triage-highlights).

The rule (``docs/decisions.md`` 2026-11-21, M8b items 3 and 10):

- a word is a run of Unicode letters and digits; words compare after ``casefold``;
- two words are one word when equal, or when one is the other plus ``s`` or
  ``es``, or ends ``ies`` where the other ends ``y``; the shorter is at least
  three characters long ("weed"/"weeds", "uav"/"uavs"; never "ga"/"gas");
- between the words of a phrase only spaces and hyphens may stand, so
  "multi-spectral" and "multi spectral" are one term, "multispectral" another
  word, and a comma, full stop, slash or bracket ends a phrase;
- no other stemming and no partial words.

Pure functions with no I/O, so the query workbench (M11a) can reuse them. The
direction rule (INC-21, ``recon.session.term_occurs``) is a different matcher
and is not changed.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from typing import Any

_WORD = re.compile(r"[^\W_]+")
#: What may stand between two words of a phrase: spaces and hyphens only.
_JOIN = re.compile(r"[\s\-‐‑]+")
_MIN_STEM = 3

Span = tuple[int, int]


def _stems(word: str) -> set[str]:
    """The word and the singular forms it could be the plural of."""
    forms = {word}
    if word.endswith("ies") and len(word) - 3 >= _MIN_STEM - 1:
        forms.add(word[:-3] + "y")
    if word.endswith("es") and len(word) - 2 >= _MIN_STEM:
        forms.add(word[:-2])
    if word.endswith("s") and not word.endswith("ss") and len(word) - 1 >= _MIN_STEM:
        forms.add(word[:-1])
    return forms


def same_word(a: str, b: str) -> bool:
    """True when ``a`` and ``b`` are one word under the plural rule (case ignored)."""
    a, b = a.casefold(), b.casefold()
    if a == b:
        return True
    return b in _stems(a) or a in _stems(b)


def _words(text: str) -> list[tuple[int, int, str, bool]]:
    """``(start, end, folded word, joined to the previous word)`` for each word."""
    out: list[tuple[int, int, str, bool]] = []
    previous_end: int | None = None
    for m in _WORD.finditer(text):
        joined = previous_end is not None and _JOIN.fullmatch(text[previous_end : m.start()]) is not None
        out.append((m.start(), m.end(), m.group().casefold(), joined))
        previous_end = m.end()
    return out


def _find(term_words: Sequence[str], words: Sequence[tuple[int, int, str, bool]]) -> list[Span]:
    n = len(term_words)
    found: list[Span] = []
    if n == 0:
        return found
    for i in range(len(words) - n + 1):
        if all(same_word(term_words[k], words[i + k][2]) for k in range(n)) and all(
            words[i + k][3] for k in range(1, n)
        ):
            found.append((words[i][0], words[i + n - 1][1]))
    return found


def _term_words(term: str) -> list[str]:
    return [m.group().casefold() for m in _WORD.finditer(term or "")]


def find_term(term: str, text: str) -> list[Span]:
    """Every ``(start, end)`` of ``term`` in ``text`` (code points), left to right."""
    return _find(_term_words(term), _words(text or ""))


def concept_terms(concept: Any) -> list[str]:
    """A protocol concept's words: its name, then its synonyms (as the search compiles them)."""
    if not isinstance(concept, dict):
        return []
    raw = [concept.get("concept")] + list(concept.get("synonyms") or [])
    terms: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, str):
            continue
        term = item.strip().strip('"').strip()
        key = " ".join(_term_words(term))
        if key and key not in seen:
            seen.add(key)
            terms.append(term)
    return terms


def _non_overlapping(found: Iterable[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    """Longest first, then leftmost, then the first concept; overlaps dropped; sorted by start."""
    kept: list[tuple[int, int, int]] = []
    for start, end, concept in sorted(set(found), key=lambda m: (-(m[1] - m[0]), m[0], m[2])):
        if all(end <= s or start >= e for s, e, _ in kept):
            kept.append((start, end, concept))
    return sorted(kept)


def concept_marks(text: str, concepts: Sequence[Any]) -> tuple[list[tuple[int, int, int]], list[int]]:
    """The marks ``(start, end, concept index)`` in ``text`` and each concept's mentions.

    Marks never overlap (the longest match wins, then the leftmost, then the
    concept listed first). A concept's mentions count its own non-overlapping
    matches, so a concept shadowed by a longer term of another is still
    mentioned.
    """
    words = _words(text or "")
    found: list[tuple[int, int, int]] = []
    mentions: list[int] = []
    for index, concept in enumerate(concepts):
        own = [(s, e, index) for term in concept_terms(concept) for s, e in _find(_term_words(term), words)]
        mentions.append(len(_non_overlapping(own)))
        found.extend(own)
    return _non_overlapping(found), mentions


def utf16_offset(text: str, index: int) -> int:
    """The UTF-16 code-unit offset of code point ``index`` in ``text`` (what a browser string counts)."""
    return index + sum(1 for ch in text[:index] if ord(ch) > 0xFFFF)
