"""Part K item 10, PDF-17: the 10 KB floor is reported as a size floor, not "invalid PDF".

A genuine short PDF (a 6-page text-only report of 4,498 bytes in the
assessment) was refused as "not a valid PDF". The floor stays (it keeps small
HTML block pages out), but each check is now named, and the message says which
one failed: the header, the trailer, or the size floor.
"""

from __future__ import annotations

import io

import aiohttp
import pytest
from pypdf import PdfWriter

from scholar_pdf.downloader import AsyncPDFDownloader
from scholar_pdf.validator import MIN_PDF_SIZE_BYTES, check_failure, pdf_checks

from .test_acquisition_contract import pdf_bytes
from .test_part_k_retries import one_location
from .stub_server import Answer, StubPdfHost


def short_pdf() -> bytes:
    """A genuine PDF below the floor: header and trailer are a PDF's."""
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    buffer = io.BytesIO()
    writer.write(buffer)
    data = buffer.getvalue()
    assert len(data) < MIN_PDF_SIZE_BYTES
    return data


def test_each_check_is_named_and_a_short_pdf_fails_only_the_size_floor(tmp_path):
    path = tmp_path / "short.pdf"
    path.write_bytes(short_pdf())

    checks = {check.name: check.passed for check in pdf_checks(path)}

    assert checks == {"pdf_header": True, "pdf_trailer": True, "size_floor": False}
    assert "size floor" in check_failure(pdf_checks(path))
    assert "not a PDF" not in check_failure(pdf_checks(path))


def test_an_html_page_fails_the_header_check_and_says_not_a_pdf(tmp_path):
    path = tmp_path / "page.pdf"
    path.write_bytes(b"<html><body>Sign in</body></html>")

    checks = pdf_checks(path)

    assert [check.name for check in checks if not check.passed][0] == "pdf_header"
    assert check_failure(checks).startswith("not a PDF")


def test_the_structural_check_is_named_when_asked(tmp_path):
    path = tmp_path / "ok.pdf"
    path.write_bytes(pdf_bytes())

    checks = pdf_checks(path, structural=True)

    assert [(c.name, c.passed) for c in checks] == [
        ("pdf_header", True),
        ("pdf_trailer", True),
        ("size_floor", True),
        ("structure", True),
    ]
    assert check_failure(checks) is None


@pytest.mark.asyncio
async def test_ingest_of_a_short_genuine_pdf_names_the_size_floor(tmp_path):
    pdf = tmp_path / "report.pdf"
    pdf.write_bytes(short_pdf())
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out")

    from .test_open_copy_resolver import FakeLookups, closed_unpaywall

    result = await downloader.ingest_pdf(FakeLookups({"title": "T"}, closed_unpaywall()), pdf, "10.1/short")

    assert result.success is False
    assert "size floor" in result.error_message
    assert "not a valid PDF" not in result.error_message


@pytest.mark.asyncio
async def test_a_download_below_the_floor_names_the_size_floor(tmp_path):
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out")
    async with StubPdfHost({"/short.pdf": [Answer(body=short_pdf())]}) as host:
        async with aiohttp.ClientSession() as session:
            result = await downloader.process_doi(session, one_location(host.url("/short.pdf")), "10.1/short")

    assert result.success is False
    assert "size floor" in result.error_message
    assert [(c.name, c.passed) for c in result.attempts[0].checks] == [
        ("pdf_header", True),
        ("pdf_trailer", True),
        ("size_floor", False),
    ]
