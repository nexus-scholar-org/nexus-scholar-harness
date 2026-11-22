"""Part K item 9 (PDF-22): the paper's identity is looked for on its first two pages.

Neither stack looked at the bytes: whatever validated as a PDF was saved under
the DOI asked. Now, with PyMuPDF installed (the ``pdf`` extra), the DOI and the
title's words are looked for on the first two pages and the result is recorded:
"doi found", "title found" or "not found: check it"; without PyMuPDF, "not
checked". It never blocks a file (Part F shows it to the researcher).

The PDFs are generated here with PyMuPDF, holding a known DOI and title.
"""

from __future__ import annotations

import pytest

from scholar_pdf import identity
from scholar_pdf.downloader import AsyncPDFDownloader
from scholar_pdf.validator import MIN_PDF_SIZE_BYTES

from .test_acquisition_contract import pdf_bytes
from .test_open_copy_resolver import FakeLookups, FakePdfHosts, closed_unpaywall

pymupdf = pytest.importorskip("pymupdf")

DOI = "10.1234/UAV.weeds.2024.017"
TITLE = "Mapping Weeds in Maize Fields from Low-Altitude Drone Imagery"
ADDRESS = "https://repository.example.org/weeds.pdf"


def make_pdf(*page_texts: str) -> bytes:
    """A real PDF above the size floor, one page per text."""
    document = pymupdf.open()
    for text in page_texts or ("",):
        page = document.new_page()
        y = 72
        for line in text.splitlines():
            page.insert_text((72, y), line, fontsize=10)
            y += 14
    document.set_metadata({"keywords": "padding " * 1600})
    data = document.tobytes()
    document.close()
    assert len(data) >= MIN_PDF_SIZE_BYTES
    return data


def write(tmp_path, data: bytes):
    path = tmp_path / "paper.pdf"
    path.write_bytes(data)
    return path


def test_the_doi_on_the_first_page_is_found(tmp_path):
    path = write(tmp_path, make_pdf(f"{TITLE}\nhttps://doi.org/{DOI.lower()}"))
    assert identity.check_identity(path, DOI, TITLE) == "doi found"


def test_the_doi_on_the_second_page_is_found(tmp_path):
    path = write(tmp_path, make_pdf("Cover page", f"DOI: {DOI}"))
    assert identity.check_identity(path, f"https://doi.org/{DOI}", None) == "doi found"


def test_the_doi_on_the_third_page_is_not_looked_for(tmp_path):
    path = write(tmp_path, make_pdf("Cover", "Contents", f"DOI: {DOI}"))
    assert identity.check_identity(path, DOI, None) == "not found: check it"


def test_the_title_words_are_found_without_the_doi(tmp_path):
    path = write(tmp_path, make_pdf("Mapping weeds in maize fields from\nlow-altitude drone imagery\nA. Author"))
    assert identity.check_identity(path, DOI, TITLE) == "title found"


def test_another_paper_is_not_found_check_it(tmp_path):
    path = write(tmp_path, make_pdf("Deep learning for protein folding\ndoi:10.9999/other.1"))
    assert identity.check_identity(path, DOI, TITLE) == "not found: check it"


def test_without_pymupdf_it_is_not_checked(tmp_path, monkeypatch):
    path = write(tmp_path, make_pdf(f"{TITLE}\n{DOI}"))
    monkeypatch.setattr(identity, "_pdf_reader", lambda: None)
    assert identity.check_identity(path, DOI, TITLE) == "not checked"


def test_an_unreadable_pdf_is_not_found_check_it(tmp_path):
    path = write(tmp_path, b"%PDF-1.4\n" + b"garbage" * 3000 + b"\n%%EOF\n")
    assert identity.check_identity(path, DOI, TITLE) == "not found: check it"


@pytest.mark.asyncio
async def test_the_download_records_the_identity_and_never_blocks(tmp_path):
    openalex = {
        "title": TITLE,
        "open_access": {"is_oa": True},
        "locations": [{"is_oa": True, "pdf_url": ADDRESS, "version": "publishedVersion"}],
    }
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out")

    found = await downloader.process_doi(
        FakePdfHosts({ADDRESS: make_pdf(f"{TITLE}\n{DOI}")}), FakeLookups(openalex, closed_unpaywall()), DOI
    )
    other = await downloader.process_doi(
        FakePdfHosts({ADDRESS: make_pdf("Something else entirely")}),
        FakeLookups(openalex, closed_unpaywall()),
        DOI,
    )

    assert found.success is True and found.identity == "doi found"
    # A file that does not show the paper is still stored, and says so.
    assert other.success is True and other.identity == "not found: check it"


@pytest.mark.asyncio
async def test_the_callers_title_is_used_when_the_lookups_give_none(tmp_path):
    openalex = {"open_access": {"is_oa": True}, "locations": [{"is_oa": True, "pdf_url": ADDRESS}]}
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out")

    result = await downloader.process_doi(
        FakePdfHosts({ADDRESS: make_pdf("Mapping weeds in maize fields from low-altitude drone imagery")}),
        FakeLookups(openalex, closed_unpaywall()),
        "10.1/no-doi-printed",
        title=TITLE,
    )

    assert result.identity == "title found"


@pytest.mark.asyncio
async def test_ingest_records_the_identity(tmp_path):
    source = tmp_path / "mine.pdf"
    source.write_bytes(pdf_bytes())  # a blank page: nothing to find
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out")

    result = await downloader.ingest_pdf(FakeLookups({"title": TITLE}, closed_unpaywall()), source, DOI)

    assert result.success is True
    assert result.identity == "not found: check it"
