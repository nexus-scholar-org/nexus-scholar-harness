"""The keyword query a topic is probed with (M10a OBS-1; decisions 2026-11-14 item 4).

OpenAlex ``search=`` and Semantic Scholar's bulk ``query=`` require every
word, so a topic sentence sent as written finds nothing, and a plain
``and``/``or``/``not`` in it is read as an operator. :func:`keyword_query`
keeps the topic's own words in order without stopwords and question or
framing words, at most :data:`MAX_TERMS`. Deterministic; no language model.

The topic is NFC-normalised first, and combining marks belong to their word,
so a word with accents or vowel signs is never split. A word of one base
letter is dropped. An all-caps word of two or more letters (an acronym such
as ``NO`` or ``IT``) is kept even when it spells a stopword, unless the whole
topic is in capitals. The stopwords are English.

A topic with a double quote, or with ``AND``, ``OR`` or ``NOT`` in capitals
as a word (punctuation around it aside: ``(OR``, ``AND,``, ``NOT.``), is a
query already and is sent as written. A hyphenated word such as
``NOT-gate`` is one word, not an operator. Parentheses alone are punctuation.
A keyworded query therefore never holds ``and``, ``or`` or ``not`` in any case.

A hyphen, a zero-width non-joiner (U+200C, as in Persian) or a zero-width
joiner (U+200D) between two word characters stays inside the word.
"""

from __future__ import annotations

import unicodedata

from .distiller import _STOPWORDS

MAX_TERMS = 6

#: Question and research-framing words: they say what is asked, not what is searched.
FRAMING = frozenset({
    "achieve", "affect", "affected", "affecting", "affects", "approach", "approaches",
    "assess", "assessing", "based", "can", "compare", "comparing", "comparison",
    "could", "did", "do", "does", "effect", "effects", "evaluate", "evaluating",
    "explore", "exploring", "extent", "how", "impact", "impacts", "influence",
    "influences", "investigate", "investigating", "literature", "method", "methods",
    "overview", "relationship", "review", "reviews", "role", "should", "studies",
    "study", "systematic", "toward", "towards", "use", "used", "using", "what",
    "whether", "which", "why", "would",
})

_OPERATOR_WORDS = frozenset({"and", "or", "not"})
_OPERATORS = frozenset({"AND", "OR", "NOT"})
#: Kept inside a word when between two word characters: hyphen, ZWNJ, ZWJ.
_JOINERS = frozenset({"-", "‌", "‍"})


def _word_char(ch: str) -> bool:
    """A letter, a digit or a combining mark."""
    return unicodedata.category(ch)[0] in "LNM"


def _base_len(word: str) -> int:
    """Letters and digits, not counting combining marks or hyphens."""
    return sum(1 for ch in word if unicodedata.category(ch)[0] in "LN")


def _words(text: str) -> list[str]:
    """Runs of word characters; a single joiner between two of them stays (on-device, ZWNJ)."""
    words: list[str] = []
    current: list[str] = []
    for i, ch in enumerate(text):
        if _word_char(ch):
            current.append(ch)
        elif ch in _JOINERS and current and _word_char(current[-1]) and i + 1 < len(text) and _word_char(text[i + 1]):
            current.append(ch)
        elif current:
            words.append("".join(current))
            current = []
    if current:
        words.append("".join(current))
    return words


def is_query(text: str) -> bool:
    """True when ``text`` has a double quote or a capital ``AND``/``OR``/``NOT`` word (punctuation aside)."""
    return '"' in text or any(word in _OPERATORS for word in _words(text))


def keyword_query(topic: str) -> str:
    """The query to probe ``topic`` with; the topic itself when nothing is left."""
    text = unicodedata.normalize("NFC", topic or "").strip()
    if is_query(text):
        return text
    all_caps = text.isupper()
    seen: set[str] = set()
    terms: list[str] = []
    for word in _words(text):
        key = word.casefold()
        size = _base_len(word)
        if size < 2 or key in seen:
            continue
        acronym = word.isupper() and not all_caps
        if not acronym and (key in _STOPWORDS or key in FRAMING or key in _OPERATOR_WORDS):
            continue
        seen.add(key)
        terms.append(word)
        if len(terms) == MAX_TERMS:
            break
    return " ".join(terms) or text
