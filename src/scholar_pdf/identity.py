"""Is this the paper that was asked for? The first two pages are looked at (PDF-22).

Part K item 9 (M12a): neither stack inspected the bytes, so any valid PDF was
saved under the DOI asked (PDF-11 saved another paper that way). With PyMuPDF
installed (the ``pdf`` extra) the DOI and the title's words are looked for on
the first two pages and one of four results is recorded:

- ``doi found``: the DOI is printed there;
- ``title found``: at least 80% of the title's distinct words of three or more
  letters are there (the DOI is not);
- ``not found: check it``: neither, or the text could not be read;
- ``not checked``: PyMuPDF is not installed (the base install does not parse PDFs).

The result never blocks a file: Part F shows it to the researcher, who confirms.
"""

from __future__ import annotations

import re
from pathlib import Path

DOI_FOUND = "doi found"
TITLE_FOUND = "title found"
NOT_FOUND = "not found: check it"
NOT_CHECKED = "not checked"

#: How many pages are read from the start of the file.
PAGES = 2
#: The share of the title's words that must be on those pages.
TITLE_WORDS_NEEDED = 0.8

_DOI_PREFIX = re.compile(r"^\s*(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.IGNORECASE)
_WORD = re.compile(r"[^\W_]+")


def _pdf_reader():
    """PyMuPDF's module, or ``None`` on the base install."""
    try:
        import pymupdf

        return pymupdf
    except ImportError:
        try:
            import fitz

            return fitz
        except ImportError:
            return None


def _first_pages_text(reader, path: Path) -> str | None:
    try:
        with reader.open(path) as document:
            return "\n".join(
                document[index].get_text() for index in range(min(PAGES, document.page_count))
            )
    except Exception:  # noqa: BLE001 - any parser failure: the text is not known
        return None


def _bare_doi(doi: str) -> str:
    return _DOI_PREFIX.sub("", doi.strip()).strip().lower()


def _title_words(title: str) -> set[str]:
    return {word for word in _WORD.findall(title.lower()) if len(word) >= 3}


def check_identity(path: Path, doi: str | None, title: str | None) -> str:
    """One of ``DOI_FOUND``, ``TITLE_FOUND``, ``NOT_FOUND`` or ``NOT_CHECKED``."""
    reader = _pdf_reader()
    if reader is None:
        return NOT_CHECKED
    text = _first_pages_text(reader, path)
    if not text:
        return NOT_FOUND
    lowered = text.lower()
    if doi and _bare_doi(doi):
        wanted = _bare_doi(doi)
        # A DOI broken over two lines on the page still counts.
        if wanted in lowered or wanted in re.sub(r"\s+", "", lowered):
            return DOI_FOUND
    words = _title_words(title or "")
    if words:
        on_pages = set(_WORD.findall(lowered))
        if len(words & on_pages) >= TITLE_WORDS_NEEDED * len(words):
            return TITLE_FOUND
    return NOT_FOUND
