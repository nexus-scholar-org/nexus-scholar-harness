"""Part K item 4 (M12a): OpenAlex is asked only with its key.

OpenAlex has required a key since 2026-02-13: keyless calls share a small daily
budget per address and then answer 409 (decision 2026-11-10, "OpenAlex needs its
API key"). The kit sent only ``mailto``, which OpenAlex no longer reads. Now:

- with ``SCHOLAR_OPENALEX_KEY`` set (read from ``scholar_search``'s settings,
  as the search kit reads it) the key is sent as OpenAlex's ``api_key``
  parameter, and both services are asked (H-pdf-resolver-locations item 4);
- without it OpenAlex is not asked, only Unpaywall, and the result and the
  command say so;
- a 409 from OpenAlex reads "the daily budget is spent", not as any other failure.

The key's value is never in a message, a result or the command's output.
Mocked lookup clients only; no request leaves the process.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from urllib.parse import urlsplit

import pytest
from scholar_search import config as search_config
from scholar_search.exceptions import ProviderError
from typer.testing import CliRunner

from scholar_pdf.cli import app
from scholar_pdf.downloader import AsyncPDFDownloader

from .conftest import TEST_OPENALEX_KEY
from .test_acquisition_contract import pdf_bytes
from .test_open_copy_resolver import (
    DOI,
    PMC_PDF,
    FakePdfHosts,
    closed_unpaywall,
    openalex_answer,
    unpaywall_answer,
)

runner = CliRunner()


class RecordingLookups:
    """A lookup client that keeps the address and the parameters of each call."""

    def __init__(self, openalex, unpaywall):
        self.answers = {"api.openalex.org": openalex, "api.unpaywall.org": unpaywall}
        self.calls: list[tuple[str, dict]] = []

    @property
    def hosts(self) -> list[str]:
        return [urlsplit(url).hostname for url, _ in self.calls]

    def params_for(self, host: str) -> list[dict]:
        return [params for url, params in self.calls if urlsplit(url).hostname == host]

    async def get(self, url, params=None, headers=None, **kwargs):
        self.calls.append((url, dict(params or {})))
        answer = self.answers[urlsplit(url).hostname]
        if isinstance(answer, Exception):
            raise answer
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = answer
        return response

    async def close(self):
        return None


@pytest.fixture
def no_openalex_key(monkeypatch):
    monkeypatch.setattr(search_config.settings, "openalex_key", None)


@pytest.fixture
def downloader(tmp_path):
    return AsyncPDFDownloader(output_dir=tmp_path / "out")


@pytest.mark.asyncio
async def test_the_key_is_sent_as_openalexs_api_key_parameter(downloader):
    lookups = RecordingLookups(openalex_answer(), unpaywall_answer())

    result = await downloader.process_doi(FakePdfHosts({PMC_PDF: pdf_bytes()}), lookups, DOI)

    assert result.success is True, result.error_message
    assert lookups.hosts == ["api.openalex.org", "api.unpaywall.org"]
    assert lookups.params_for("api.openalex.org") == [{"api_key": TEST_OPENALEX_KEY}]
    # The key goes to OpenAlex only, never to Unpaywall.
    assert all("api_key" not in params for params in lookups.params_for("api.unpaywall.org"))
    assert TEST_OPENALEX_KEY not in repr(result)


@pytest.mark.asyncio
async def test_without_the_key_openalex_is_not_asked_and_the_result_says_so(
    no_openalex_key, downloader
):
    lookups = RecordingLookups(openalex_answer(), unpaywall_answer())

    result = await downloader.process_doi(FakePdfHosts({PMC_PDF: pdf_bytes()}), lookups, DOI)

    assert lookups.hosts == ["api.unpaywall.org"]
    assert result.success is True, result.error_message
    assert result.open_copy.provider == "unpaywall"
    assert [(look.provider, look.state) for look in result.lookups] == [
        ("openalex", "NOT_ASKED"),
        ("unpaywall", "ANSWERED"),
    ]


@pytest.mark.asyncio
async def test_without_the_key_no_open_copy_names_openalex_as_not_asked(
    no_openalex_key, downloader
):
    lookups = RecordingLookups(openalex_answer(), closed_unpaywall())

    result = await downloader.process_doi(FakePdfHosts(), lookups, "10.1/closed")

    assert lookups.hosts == ["api.unpaywall.org"]
    # Not asking is not a failed lookup: running again would not change it.
    assert result.outcome == "NO_OPEN_COPY_LISTED"
    assert "OpenAlex was not asked (SCHOLAR_OPENALEX_KEY is not set)" in result.error_message
    assert "Unpaywall lists no open copy" in result.error_message


@pytest.mark.asyncio
async def test_a_409_from_openalex_reads_as_the_budget_spent(downloader):
    budget = ProviderError("openalex-pdf", "HTTP request failed", status_code=409)
    other = ProviderError("openalex-pdf", "HTTP request failed", status_code=503)

    spent = await downloader.process_doi(
        FakePdfHosts(), RecordingLookups(budget, closed_unpaywall()), "10.1/x"
    )
    failed = await downloader.process_doi(
        FakePdfHosts(), RecordingLookups(other, closed_unpaywall()), "10.1/x"
    )

    assert spent.outcome == failed.outcome == "LOOKUP_FAILED"
    assert "OpenAlex failed (HTTP 409: the daily budget is spent)" in spent.error_message
    assert "budget" not in failed.error_message
    assert "OpenAlex failed (HTTP 503)" in failed.error_message
    assert spent.lookups[0].budget_spent is True
    assert failed.lookups[0].budget_spent is False


@pytest.mark.asyncio
async def test_a_409_from_unpaywall_is_an_ordinary_failure(downloader):
    lookups = RecordingLookups(
        openalex_answer(), ProviderError("openalex-pdf", "x", status_code=409)
    )

    result = await downloader.process_doi(FakePdfHosts({PMC_PDF: pdf_bytes()}), lookups, DOI)

    assert result.lookups[1].budget_spent is False
    assert result.lookups[1].failure() == "failed (HTTP 409)"


@pytest.mark.asyncio
async def test_ingest_without_the_key_asks_unpaywall_only(no_openalex_key, downloader, tmp_path):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(pdf_bytes())
    lookups = RecordingLookups(openalex_answer(), unpaywall_answer())

    result = await downloader.ingest_pdf(lookups, pdf, DOI)

    assert result.success is True
    assert lookups.hosts == ["api.unpaywall.org"]
    assert [(look.provider, look.state) for look in result.lookups] == [
        ("openalex", "NOT_ASKED"),
        ("unpaywall", "ANSWERED"),
    ]


def test_the_download_command_says_openalex_is_not_asked_without_the_key(
    no_openalex_key, tmp_path, monkeypatch
):
    import aiohttp

    lookups = RecordingLookups(openalex_answer(), unpaywall_answer())
    hosts = FakePdfHosts({PMC_PDF: pdf_bytes()})
    monkeypatch.setattr("scholar_search.http_client.AcademicHttpClient", lambda **kwargs: lookups)
    monkeypatch.setattr(aiohttp, "ClientSession", lambda *args, **kwargs: hosts)

    result = runner.invoke(app, ["download", "--doi", DOI, "--output", str(tmp_path / "out")])

    text = " ".join(result.output.split())
    assert result.exit_code == 0, text
    assert "OpenAlex is not asked: SCHOLAR_OPENALEX_KEY is not set" in text
    assert lookups.hosts == ["api.unpaywall.org"]


def test_the_download_command_never_prints_the_key(tmp_path, monkeypatch):
    import aiohttp

    failing = ProviderError("openalex-pdf", "HTTP request failed", status_code=409)
    lookups = RecordingLookups(failing, closed_unpaywall())
    monkeypatch.setattr("scholar_search.http_client.AcademicHttpClient", lambda **kwargs: lookups)
    monkeypatch.setattr(aiohttp, "ClientSession", lambda *args, **kwargs: FakePdfHosts())

    result = runner.invoke(app, ["download", "--doi", DOI, "--output", str(tmp_path / "out")])

    assert result.exit_code == 3
    assert "daily budget is spent" in " ".join(result.output.split())
    assert TEST_OPENALEX_KEY not in result.output
