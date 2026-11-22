"""The criteria wording checks of Inception's step 5 (M11b part D, record (f); DoD 19).

Plain word rules, no model, never blockers. They compare the accepted criteria's
words, not their meaning: "RGB only" against "multispectral imagery from a UAV"
share no word and are not caught; a contradiction of meaning ("uses a learned
model" beside "or a dataset paper") is not caught either. Those are found after a
pilot (the pilot's rules on the agent's answers) or by the M10c critic. A clean
list means "no repeated words", never "the criteria are sound".

The stop words, the negation words and the full-text word list are English. For
criteria in another language only the two equality checks run
(``CRITERIA_DUPLICATE``, ``CRITERIA_CONTRADICT``), and the caller says so.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

#: At least this share of one criterion's content words found in the other (record (f)).
MIRROR_SHARE = 0.6
#: A list of at least this many items joined by commas and "or"/"and" is a lumped criterion.
LUMP_ITEMS = 3

STOP_WORDS = frozenset(
    """a an the of in on at to for from by with and or as is are be been being was were that which who whom
    this these those it its their there into onto per via any all each either both such than then also must
    should may can will would has have had do does did paper papers study studies record records article articles
    report reports reported""".split()
)
#: "other than" is a negation only as the two-word phrase (review D round 1, finding 8); "other" alone is a word.
NEGATIONS = frozenset({"not", "no", "without", "only", "non", "except", "excluding"})
_OTHER_THAN = re.compile(r"\bother\s+than\b", re.IGNORECASE)
#: Things an abstract rarely reports (a constant; record (f)). Matched as whole phrases.
FULL_TEXT_PHRASES = (
    "full text", "full-text", "results section", "table", "sample size", "code available", "data available",
    "statistical test", "reports the",
)
#: Words that say a criterion is English, and words that say it is not (common function words of
#: other languages the reviews here are written in). Short criteria often hold neither.
ENGLISH_MARKERS = frozenset({"the", "of", "a", "an", "in", "on", "for", "with", "that", "is", "are", "from", "and",
                             "or", "not", "no", "only", "without", "uses", "using", "based"})
FOREIGN_MARKERS = frozenset({
    "de", "la", "le", "les", "des", "du", "et", "ou", "pour", "avec", "sur", "sans", "pas", "une", "un", "seulement",
    "der", "die", "das", "und", "oder", "mit", "ohne", "nur", "el", "los", "las", "y", "con", "para", "sin", "solo",
})

_WORD = re.compile(r"[^\W_]+(?:-[^\W_]+)*", re.UNICODE)


@dataclass(frozen=True)
class Item:
    id: str
    side: str
    text: str


def words(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text or "")]


def normalised(text: str) -> tuple[str, ...]:
    """Lower case, punctuation and stop words removed (the equality checks)."""
    return tuple(w for w in words(text) if w not in STOP_WORDS)


def content(text: str) -> frozenset[str]:
    """The content words: no stop word and no negation word (the mirror check)."""
    return frozenset(w for w in words(_OTHER_THAN.sub(" ", text or "")) if w not in STOP_WORDS and w not in NEGATIONS)


def is_english(items: Iterable[Item]) -> bool:
    """English unless the criteria show another language: a function word of one, or a letter outside
    ASCII, with no English function word (record (f): the word lists are English)."""
    items = list(items)
    found = {w for i in items for w in words(i.text)}
    if found & ENGLISH_MARKERS:
        return True
    return not (found & FOREIGN_MARKERS or any(not ch.isascii() for i in items for ch in i.text if ch.isalpha()))


def duplicates(items: list[Item]) -> list[tuple[Item, Item]]:
    out = []
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            if a.side == b.side and normalised(a.text) and normalised(a.text) == normalised(b.text):
                out.append((a, b))
    return out


def contradictions(items: list[Item]) -> list[tuple[Item, Item]]:
    """(inclusion, exclusion) pairs with equal normalised texts."""
    inc = [i for i in items if i.side == "inclusion"]
    exc = [i for i in items if i.side == "exclusion"]
    return [(a, b) for a in inc for b in exc if normalised(a.text) and normalised(a.text) == normalised(b.text)]


def mirrors(items: list[Item]) -> list[tuple[Item, Item, float, frozenset[str]]]:
    """(exclusion, inclusion, share, shared words): the exclusion's content words cover at least
    ``MIRROR_SHARE`` of the inclusion's, or the reverse. Equal texts are contradictions, not mirrors."""
    out = []
    for e in (i for i in items if i.side == "exclusion"):
        for n in (i for i in items if i.side == "inclusion"):
            if normalised(e.text) == normalised(n.text):
                continue
            ce, cn = content(e.text), content(n.text)
            if not ce or not cn:
                continue
            shared = ce & cn
            share = max(len(shared) / len(cn), len(shared) / len(ce))
            if share >= MIRROR_SHARE:
                out.append((e, n, round(share, 2), frozenset(shared)))
    return out


def lumped(item: Item) -> bool:
    """A semicolon, or a list of ``LUMP_ITEMS`` or more items joined by commas and "or"/"and"."""
    text = item.text or ""
    if ";" in text:
        return True
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) < 2:
        return False
    if re.match(r"^(?:or|and)\s+", parts[-1], re.IGNORECASE):  # "A, B, or C"
        return len(parts) >= LUMP_ITEMS
    tail = re.split(r"\s+(?:or|and)\s+", parts[-1], maxsplit=1, flags=re.IGNORECASE)  # "A, B or C"
    return len(tail) == 2 and len(parts) + 1 >= LUMP_ITEMS


def needs_full_text(item: Item) -> list[str]:
    """The phrases of ``FULL_TEXT_PHRASES`` the criterion names, whole words only."""
    joined = " " + " ".join(words(item.text)) + " "
    return [p for p in FULL_TEXT_PHRASES if f" {p} " in joined]
