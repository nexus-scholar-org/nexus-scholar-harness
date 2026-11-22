"""Part K, from the live check after PR 278: every PDF request is visible.

A live check could not count the PDF requests a DOI cost. Now the result and
its manifest row list each request sent to a PDF address (the address, its
host, the HTTP status or the error, whether it was a retry, the redirects),
with a count and the hosts, and ``download`` prints them per DOI. When a
higher-ranked address gives no PDF and a lower one does (PubMed Central's
published version refused, a repository's submitted version taken, in that
check), the command and the row say what the first address answered. Nothing
poses as a browser to get past it (decision items 24 and 27, K0).

Two stub servers on 127.0.0.1 (two ports, two hosts); nothing leaves the machine.
"""

from __future__ import annotations

import json

import aiohttp
import pytest
from tenacity import wait_none
from typer.testing import CliRunner

from scholar_pdf.cli import app
from scholar_pdf.downloader import AsyncPDFDownloader

from .stub_server import Answer, StubPdfHost
from .test_acquisition_contract import pdf_bytes
from .test_open_copy_resolver import (
    DOI,
    PMC_PDF,
    REPOSITORY_PDF,
    FakeLookups,
    FakePdfHosts,
    openalex_answer,
    unpaywall_answer,
)

runner = CliRunner()


def two_locations(first: str, second: str) -> FakeLookups:
    openalex = {
        "open_access": {"is_oa": True},
        "locations": [
            {"is_oa": True, "pdf_url": first, "version": "publishedVersion"},
            {"is_oa": True, "pdf_url": second, "version": "submittedVersion"},
        ],
    }
    return FakeLookups(openalex, {"is_oa": False, "oa_locations": []})


@pytest.mark.asyncio
async def test_each_pdf_request_is_on_the_result_and_its_row(tmp_path):
    manifest = tmp_path / "m.jsonl"
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out", manifest_path=manifest)
    async with StubPdfHost({"/pub.pdf": [Answer(status=403, body=b"no", content_type="text/html")]}) as refusing:
        async with StubPdfHost({"/sub.pdf": [Answer(body=pdf_bytes())]}) as giving:
            first, second = refusing.url("/pub.pdf"), giving.url("/sub.pdf")
            async with aiohttp.ClientSession() as session:
                result = await downloader.process_doi(session, two_locations(first, second), "10.1/two")
            hosts = (f"127.0.0.1:{refusing.port}", f"127.0.0.1:{giving.port}")

    assert result.success is True, result.error_message
    assert result.request_count == 2
    assert [(a.url, a.host, a.http_status, a.retry) for a in result.attempts] == [
        (first, hosts[0], 403, False),
        (second, hosts[1], 200, False),
    ]
    assert result.request_hosts() == {hosts[0]: 1, hosts[1]: 1}
    assert refusing.hits["/pub.pdf"] == 1  # the 403 is not retried

    [row] = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines()]
    assert row["request_count"] == 2
    assert row["request_hosts"] == {hosts[0]: 1, hosts[1]: 1}
    assert [(r["url"], r["host"], r["http_status"], r["retry"], r["error"]) for r in row["requests"]] == [
        (first, hosts[0], 403, False, "HTTP 403"),
        (second, hosts[1], 200, False, None),
    ]
    # The higher-ranked address was tried first, and what it answered is kept.
    assert row["address"] == second and row["version"] == "submittedVersion"


@pytest.mark.asyncio
async def test_a_retry_is_marked_as_one(tmp_path, monkeypatch):
    monkeypatch.setattr(AsyncPDFDownloader.download_pdf.retry, "wait", wait_none())
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out")
    script = [Answer(status=503, body=b"busy", content_type="text/html"), Answer(body=pdf_bytes())]
    async with StubPdfHost({"/a.pdf": script}) as host:
        url = host.url("/a.pdf")
        async with aiohttp.ClientSession() as session:
            result = await downloader.process_doi(session, two_locations(url, url + "?copy=2"), "10.1/retry")

    assert result.success is True
    assert [(a.http_status, a.retry) for a in result.attempts] == [(503, False), (200, True)]
    assert result.request_count == 2 and result.request_hosts() == {f"127.0.0.1:{host.port}": 2}


def test_the_command_prints_the_requests_per_doi_and_what_the_first_address_answered(tmp_path, monkeypatch):
    lookups = FakeLookups(openalex_answer(), unpaywall_answer())
    hosts = FakePdfHosts({REPOSITORY_PDF: pdf_bytes()})  # PubMed Central's address answers an HTML page
    monkeypatch.setattr("scholar_search.http_client.AcademicHttpClient", lambda **kwargs: lookups)
    monkeypatch.setattr(aiohttp, "ClientSession", lambda *args, **kwargs: hosts)

    result = runner.invoke(app, ["download", "--doi", DOI, "--output", str(tmp_path / "out")])

    text = " ".join(result.output.split())
    assert result.exit_code == 0, text
    assert hosts.requested == [PMC_PDF, REPOSITORY_PDF]
    assert f"{DOI}: 2 PDF requests" in text
    assert "pmc.ncbi.nlm.nih.gov: not a PDF" in text
    assert "umontreal.scholaris.ca: stored" in text
