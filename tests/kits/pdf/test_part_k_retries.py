"""Part K item 6 (PDF-06): a definitive answer from a PDF address is not retried.

Before, ``download_pdf`` retried every ``aiohttp.ClientError`` three times with
a 2 to 10 s backoff, so a 404 cost about 6 s and three requests per address.
Now only what can pass is retried: a connection error, a timeout, a 5xx, and a
429 whose ``Retry-After`` is within the HTTP client's cap (60 s, the cap the
search kit uses; M12a item 14). A 429 with a longer wait, or with none, ends
at once with "try later". 400, 401, 403, 404, 410 and 451 are asked once.

A stub server on 127.0.0.1 counts the requests; nothing leaves the machine.
"""

from __future__ import annotations

import aiohttp
import pytest
from tenacity import wait_none

from scholar_pdf.downloader import AsyncPDFDownloader

from .test_acquisition_contract import pdf_bytes
from .test_open_copy_resolver import FakeLookups
from .stub_server import Answer, StubPdfHost

DEFINITIVE = (400, 401, 403, 404, 410, 451)


@pytest.fixture
def downloader(tmp_path):
    return AsyncPDFDownloader(output_dir=tmp_path / "out")


@pytest.fixture
def no_backoff(monkeypatch):
    """The retries that remain wait 2 to 10 s; the tests do not."""
    monkeypatch.setattr(AsyncPDFDownloader.download_pdf.retry, "wait", wait_none())


def one_location(url: str) -> FakeLookups:
    openalex = {"open_access": {"is_oa": True}, "locations": [{"is_oa": True, "pdf_url": url, "version": "publishedVersion"}]}
    return FakeLookups(openalex, {"is_oa": False, "oa_status": "closed", "oa_locations": []})


@pytest.mark.asyncio
@pytest.mark.parametrize("status", DEFINITIVE)
async def test_a_definitive_answer_is_asked_once(status, downloader, no_backoff, tmp_path):
    async with StubPdfHost({"/paper.pdf": [Answer(status=status, body=b"no", content_type="text/html")]}) as host:
        async with aiohttp.ClientSession() as session:
            with pytest.raises(aiohttp.ClientResponseError):
                await downloader.download_pdf(session, host.url("/paper.pdf"), tmp_path / "out" / "a.pdf")
    assert host.hits["/paper.pdf"] == 1


@pytest.mark.asyncio
async def test_a_404_costs_one_request_and_says_so_in_the_result(downloader, no_backoff):
    async with StubPdfHost({"/gone.pdf": [Answer(status=404, body=b"gone", content_type="text/html")]}) as host:
        async with aiohttp.ClientSession() as session:
            result = await downloader.process_doi(session, one_location(host.url("/gone.pdf")), "10.1/gone")
    assert host.hits["/gone.pdf"] == 1
    assert result.success is False and result.outcome == "PDF_NOT_FETCHED"
    assert "HTTP 404" in result.error_message
    assert "127.0.0.1" not in result.error_message  # the words, not the error's text


@pytest.mark.asyncio
async def test_a_server_error_is_retried(downloader, no_backoff, tmp_path):
    script = [Answer(status=503, body=b"busy", content_type="text/html"), Answer(body=pdf_bytes())]
    async with StubPdfHost({"/busy.pdf": script}) as host:
        async with aiohttp.ClientSession() as session:
            ok = await downloader.download_pdf(session, host.url("/busy.pdf"), tmp_path / "out" / "a.pdf")
    assert ok is True
    assert host.hits["/busy.pdf"] == 2


@pytest.mark.asyncio
async def test_a_429_with_a_short_retry_after_is_waited_out_once(downloader, tmp_path):
    script = [
        Answer(status=429, body=b"slow down", content_type="text/plain", headers={"Retry-After": "0"}),
        Answer(body=pdf_bytes()),
    ]
    async with StubPdfHost({"/busy.pdf": script}) as host:
        async with aiohttp.ClientSession() as session:
            ok = await downloader.download_pdf(session, host.url("/busy.pdf"), tmp_path / "out" / "a.pdf")
    assert ok is True
    assert host.hits["/busy.pdf"] == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("headers", [{"Retry-After": "3600"}, {}], ids=["beyond-the-cap", "no-retry-after"])
async def test_a_429_beyond_the_cap_or_without_retry_after_ends_with_try_later(headers, downloader, no_backoff):
    script = [Answer(status=429, body=b"slow down", content_type="text/plain", headers=headers)]
    async with StubPdfHost({"/busy.pdf": script}) as host:
        async with aiohttp.ClientSession() as session:
            result = await downloader.process_doi(session, one_location(host.url("/busy.pdf")), "10.1/busy")
    assert host.hits["/busy.pdf"] == 1
    assert result.success is False
    assert "HTTP 429" in result.error_message
    assert "try later" in result.error_message


@pytest.mark.asyncio
async def test_a_refused_address_does_not_stop_the_next_one(downloader):
    """No backoff patched: a 403 must not cost any wait before the next address."""
    import time

    openalex = {
        "open_access": {"is_oa": True},
        "locations": [
            {"is_oa": True, "pdf_url": "PLACEHOLDER-1", "version": "publishedVersion"},
            {"is_oa": True, "pdf_url": "PLACEHOLDER-2", "version": "acceptedVersion"},
        ],
    }
    routes = {
        "/refused.pdf": [Answer(status=403, body=b"no", content_type="text/html")],
        "/open.pdf": [Answer(body=pdf_bytes())],
    }
    async with StubPdfHost(routes) as host:
        openalex["locations"][0]["pdf_url"] = host.url("/refused.pdf")
        openalex["locations"][1]["pdf_url"] = host.url("/open.pdf")
        lookups = FakeLookups(openalex, {"is_oa": False, "oa_locations": []})
        started = time.monotonic()
        async with aiohttp.ClientSession() as session:
            result = await downloader.process_doi(session, lookups, "10.1/two")
        elapsed = time.monotonic() - started
    assert result.success is True, result.error_message
    assert host.hits["/refused.pdf"] == 1 and host.hits["/open.pdf"] == 1
    assert elapsed < 2.0, elapsed
