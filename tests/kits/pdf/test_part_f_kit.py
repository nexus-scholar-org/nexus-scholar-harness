"""M12a Part F: what the app needs from the kit's downloader, as library parameters.

- a hard stop on a body at ``max_bytes`` (Part F passes 100 MB; the limit is
  lowered here), whether the answer declares its length or streams it;
- at most ``max_redirects`` redirects, each recorded; one more ends the address;
- a ``pacer`` called before every request to a PDF address, retries included;
- open copies the caller found itself (the ``pdf`` link arXiv's answer gives),
  fetched with every check (``process_copies``) or ranked with the services'
  copies (``process_doi(extra_copies=...)``), the best version first (F3);
- the caller's fields on the manifest row, never replacing the kit's own.

The defaults are unchanged for the commands (no size stop, aiohttp's ten
redirects, no pacer). Stub servers on 127.0.0.1 only; nothing leaves the machine.
"""

from __future__ import annotations

import json

import aiohttp
import pytest
from aiohttp import web
from tenacity import wait_none

from scholar_pdf.downloader import AsyncPDFDownloader
from scholar_pdf.open_copies import LookupOutcome, OpenCopy

from .stub_server import Answer, StubPdfHost
from .test_acquisition_contract import pdf_bytes
from .test_open_copy_resolver import FakeLookups

PDF = pdf_bytes()


def arxiv_copy(url: str) -> OpenCopy:
    return OpenCopy(
        url=url, version="submittedVersion", license=None, host_type="repository",
        source_name="arXiv", provider="arxiv", version_label="preprint (arXiv v3)",
    )


def rows(path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


@pytest.fixture
def no_backoff(monkeypatch):
    monkeypatch.setattr(AsyncPDFDownloader.download_pdf.retry, "wait", wait_none())


# ----------------------------------------------------------------------------- the body limit


@pytest.mark.asyncio
async def test_a_declared_body_over_the_limit_is_stopped_and_fails(tmp_path):
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out", max_bytes=len(PDF) - 1)
    async with StubPdfHost({"/big.pdf": [Answer(body=PDF)]}) as host:
        async with aiohttp.ClientSession() as session:
            result = await downloader.process_copies(session, [arxiv_copy(host.url("/big.pdf"))], study_id="S1")
    assert result.success is False and result.outcome == "PDF_NOT_FETCHED"
    [attempt] = result.attempts
    assert attempt.error == f"the body is over the limit of {len(PDF) - 1} bytes"
    assert [(c.name, c.passed) for c in attempt.checks] == [("size_limit", False)]
    assert host.hits["/big.pdf"] == 1  # not retried
    assert not list((tmp_path / "out").glob("*.pdf"))


@pytest.mark.asyncio
async def test_a_streamed_body_is_cut_at_the_limit_while_it_is_read(tmp_path):
    """No ``Content-Length``: the stop happens on the bytes read, and the rest is not read."""
    sent = {"chunks": 0}

    async def stream(request: web.Request) -> web.StreamResponse:
        response = web.StreamResponse(headers={"Content-Type": "application/pdf"})
        response.enable_chunked_encoding()
        await response.prepare(request)
        try:
            for _ in range(400):  # 400 x 16 KB = 6.4 MB if it were all read
                await response.write(b"%PDF-1.4\n" + b"x" * (16 * 1024 - 9))
                sent["chunks"] += 1
        except (ConnectionResetError, RuntimeError):
            pass
        return response

    app = web.Application()
    app.router.add_get("/endless.pdf", stream)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    try:
        limit = 64 * 1024
        downloader = AsyncPDFDownloader(output_dir=tmp_path / "out", max_bytes=limit)
        async with aiohttp.ClientSession() as session:
            ok = await downloader.download_pdf(
                session, f"http://127.0.0.1:{port}/endless.pdf", tmp_path / "out" / "a.pdf", attempts=(seen := []),
            )
    finally:
        await runner.cleanup()
    assert ok is False
    assert seen[0].error == f"the body is over the limit of {limit} bytes"
    assert sent["chunks"] < 400
    assert not (tmp_path / "out" / "a.pdf").exists()
    assert not list((tmp_path / "out").glob(".pdf-acquisition-*"))  # the staging file is gone


def test_the_commands_keep_no_size_stop_and_aiohttps_redirects_by_default(tmp_path):
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out")
    assert downloader.max_bytes is None and downloader.max_redirects is None and downloader.pacer is None
    with pytest.raises(ValueError):
        AsyncPDFDownloader(output_dir=tmp_path / "out", max_bytes=0)


# ----------------------------------------------------------------------------- redirects


def chain(hops: int) -> dict[str, list[Answer]]:
    routes = {f"/r{n}": [Answer(redirect_to=f"/r{n + 1}")] for n in range(hops)}
    routes[f"/r{hops}"] = [Answer(body=PDF)]
    return routes


@pytest.mark.asyncio
async def test_five_redirects_are_followed_and_each_is_recorded(tmp_path):
    manifest = tmp_path / "m.jsonl"
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out", max_redirects=5, manifest_path=manifest)
    async with StubPdfHost(chain(5)) as host:
        async with aiohttp.ClientSession() as session:
            result = await downloader.process_copies(session, [arxiv_copy(host.url("/r0"))], study_id="S1")
        hops = [host.url(f"/r{n}") for n in range(5)]
    assert result.success is True, result.error_message
    [row] = rows(manifest)
    assert row["redirects"] == hops and row["final_url"].endswith("/r5")


@pytest.mark.asyncio
async def test_a_sixth_redirect_ends_the_address_with_the_redirects_recorded(tmp_path, no_backoff):
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out", max_redirects=5)
    async with StubPdfHost(chain(6)) as host:
        async with aiohttp.ClientSession() as session:
            result = await downloader.process_copies(session, [arxiv_copy(host.url("/r0"))])
        assert host.hits["/r6"] == 0 and host.hits["/r0"] == 1  # stopped, and not retried
    assert result.success is False
    [attempt] = result.attempts
    assert attempt.error == "too many redirects"
    assert len(attempt.redirects) == 6
    assert "too many redirects" in result.error_message


# ----------------------------------------------------------------------------- pacing


@pytest.mark.asyncio
async def test_the_pacer_is_called_before_every_pdf_request_retries_included(tmp_path, no_backoff):
    paced: list[str] = []

    async def pacer(url: str) -> None:
        paced.append(url)

    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out", pacer=pacer)
    script = [Answer(status=503, body=b"busy", content_type="text/html"), Answer(body=PDF)]
    async with StubPdfHost({"/a.pdf": script}) as host:
        async with aiohttp.ClientSession() as session:
            result = await downloader.process_copies(session, [arxiv_copy(host.url("/a.pdf"))])
        url = host.url("/a.pdf")
    assert result.success is True
    assert paced == [url, url]


# ----------------------------------------------------------------------------- the caller's copies


@pytest.mark.asyncio
async def test_a_copy_from_arxivs_answer_is_fetched_with_every_check_and_its_row(tmp_path):
    manifest = tmp_path / "m.jsonl"
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out", manifest_path=manifest)
    arxiv = LookupOutcome("arxiv", "ANSWERED", 200)
    async with StubPdfHost({"/pdf/2101.01234v3": [Answer(body=PDF)]}) as host:
        async with aiohttp.ClientSession() as session:
            result = await downloader.process_copies(
                session, [arxiv_copy(host.url("/pdf/2101.01234v3"))], title="A title", study_id="STU-1",
                lookups=(arxiv,), manifest_extra={"run_id": "FR-1", "row_id": "FMR-1", "arxiv_id": "2101.01234"},
            )
    assert result.success is True and result.file_path is not None
    [row] = rows(manifest)
    assert row["study_id"] == "STU-1" and row["doi"] == ""
    assert (row["provider"], row["version"], row["version_label"]) == ("arxiv", "submittedVersion", "preprint (arXiv v3)")
    assert row["license"] is None and row["source_name"] == "arXiv"
    assert row["lookups"] == [{"service": "arxiv", "state": "ANSWERED", "http_status": 200, "error": None}]
    assert (row["run_id"], row["row_id"], row["arxiv_id"]) == ("FR-1", "FMR-1", "2101.01234")
    assert row["checks"]["pdf_header"] == "pass" and "identity" in row["checks"]
    assert row["file"].endswith(".pdf") and row["sha256"] == result.sha256


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [b"<html><body>Sign in</body></html>" * 400, b"%PDF-1.4\n<html><body>an error page</body></html>" * 300],
    ids=["html named pdf", "html after a pdf header"],
)
async def test_a_page_that_is_not_a_pdf_fails_its_checks_and_is_not_stored(tmp_path, body):
    manifest = tmp_path / "m.jsonl"
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out", manifest_path=manifest)
    async with StubPdfHost({"/paper.pdf": [Answer(body=body, content_type="application/pdf")]}) as host:
        async with aiohttp.ClientSession() as session:
            result = await downloader.process_copies(session, [arxiv_copy(host.url("/paper.pdf"))], study_id="S")
    assert result.success is False and result.file_path is None
    [row] = rows(manifest)
    assert row["file"] is None and row["outcome"] == "PDF_NOT_FETCHED"
    assert not list((tmp_path / "out").glob("*.pdf"))


@pytest.mark.asyncio
async def test_no_copy_from_the_caller_writes_a_row_and_sends_nothing(tmp_path):
    manifest = tmp_path / "m.jsonl"
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out", manifest_path=manifest)
    async with aiohttp.ClientSession() as session:
        result = await downloader.process_copies(session, [], study_id="S", lookups=(LookupOutcome("arxiv", "NOT_FOUND"),))
    assert result.outcome == "NO_OPEN_COPY_LISTED" and result.request_count == 0
    assert rows(manifest)[0]["outcome"] == "NO_OPEN_COPY_LISTED"


@pytest.mark.asyncio
async def test_a_published_version_listed_for_the_journal_doi_wins_over_the_arxiv_preprint(tmp_path):
    async with StubPdfHost({"/published.pdf": [Answer(body=PDF)], "/arxiv.pdf": [Answer(body=PDF)]}) as host:
        unpaywall = {
            "is_oa": True,
            "best_oa_location": {"url_for_pdf": host.url("/published.pdf"), "version": "publishedVersion",
                                 "host_type": "publisher", "license": "cc-by"},
            "oa_locations": [],
        }
        lookups = FakeLookups({"open_access": {"is_oa": False}}, unpaywall)
        downloader = AsyncPDFDownloader(output_dir=tmp_path / "out")
        async with aiohttp.ClientSession() as session:
            result = await downloader.process_doi(
                session, lookups, "10.1234/journal.2021.001", extra_copies=[arxiv_copy(host.url("/arxiv.pdf"))],
                prior_lookups=(LookupOutcome("arxiv", "ANSWERED", 200),),
            )
        assert host.hits["/arxiv.pdf"] == 0
    assert result.success is True
    assert result.open_copy.version == "publishedVersion" and result.open_copy.license == "cc-by"
    assert [lookup.provider for lookup in result.lookups] == ["arxiv", "openalex", "unpaywall"]


@pytest.mark.asyncio
async def test_the_arxiv_preprint_is_taken_when_the_services_list_no_copy(tmp_path):
    async with StubPdfHost({"/arxiv.pdf": [Answer(body=PDF)]}) as host:
        lookups = FakeLookups({"open_access": {"is_oa": False}}, {"is_oa": False, "oa_locations": []})
        downloader = AsyncPDFDownloader(output_dir=tmp_path / "out")
        async with aiohttp.ClientSession() as session:
            result = await downloader.process_doi(
                session, lookups, "10.1234/x", extra_copies=[arxiv_copy(host.url("/arxiv.pdf"))]
            )
    assert result.success is True and result.open_copy.provider == "arxiv"
    assert result.open_copy.label().startswith("preprint (arXiv v3)")


@pytest.mark.asyncio
async def test_the_callers_fields_never_replace_the_kits_own(tmp_path):
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out", manifest_path=tmp_path / "m.jsonl")
    async with aiohttp.ClientSession() as session:
        with pytest.raises(ValueError, match="sha256"):
            await downloader.process_copies(session, [], manifest_extra={"sha256": "forged"})
    assert not (tmp_path / "m.jsonl").exists()
