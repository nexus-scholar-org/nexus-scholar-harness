"""K0 (M12a): ``download`` and ``ingest`` are production, with four repairs.

Decision 2026-11-21, M12a items 21 and 27 ("Production from now"; "Label plus
four repairs"): the contact e-mail is required (``SCHOLAR_MAILTO`` read as
well as the kit's ``MAILTO``), every request names the app rather than a
browser, no guessed publisher URL is requested, and a set institutional proxy
is refused with a message naming item 25. DoD K1, K2 and K3, done early.

Every network test here talks to a stub server on 127.0.0.1 or to mocks; the
suite's guard fails any other connection.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiohttp import web
from scholar_search.http_client import AcademicHttpClient
from typer.testing import CliRunner

from scholar_pdf import config as pdf_config
from scholar_pdf.cli import app
from scholar_pdf.downloader import AsyncPDFDownloader, DownloadResult

from .test_acquisition_contract import pdf_bytes

runner = CliRunner()
PACKAGE_DIR = Path(pdf_config.__file__).resolve().parent
CONTACT = "reviewer@example.org"


@pytest.fixture
def no_contact(monkeypatch):
    """Neither the app's ``SCHOLAR_MAILTO`` nor the kit's ``MAILTO`` is set."""
    from scholar_search import config as search_config

    monkeypatch.setattr(search_config.settings, "mailto", None)
    monkeypatch.setattr(pdf_config.settings, "mailto", "")


@pytest.fixture
def app_contact_only(monkeypatch):
    """Only the app's ``SCHOLAR_MAILTO`` is set (the researcher's usual setup)."""
    from scholar_search import config as search_config

    monkeypatch.setattr(search_config.settings, "mailto", CONTACT)
    monkeypatch.setattr(pdf_config.settings, "mailto", "")


def _metadata_client(pdf_url: str | None) -> MagicMock:
    client = MagicMock(spec=AcademicHttpClient)
    answer = MagicMock()
    answer.status_code = 200
    answer.json.return_value = {"best_oa_location": {"is_oa": True, "pdf_url": pdf_url}}
    client.get = AsyncMock(return_value=answer)
    return client


# --------------------------------------------------------------------- K1: the e-mail


def test_the_placeholder_contact_email_is_gone_from_the_kit():
    offenders = [
        str(path.relative_to(PACKAGE_DIR))
        for path in PACKAGE_DIR.rglob("*.py")
        if "student@university.edu" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_download_refuses_without_a_contact_email(no_contact, tmp_path):
    with patch(
        "scholar_pdf.cli.AsyncPDFDownloader.process_doi", new_callable=AsyncMock
    ) as process_doi:
        result = runner.invoke(
            app, ["download", "--doi", "10.1234/x", "--output", str(tmp_path)]
        )
    assert result.exit_code != 0
    assert "MAILTO_NOT_SET" in result.output
    assert "SCHOLAR_MAILTO" in result.output
    process_doi.assert_not_called()


def test_ingest_refuses_without_a_contact_email(no_contact, tmp_path):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(pdf_bytes())
    with patch(
        "scholar_pdf.cli.AsyncPDFDownloader.ingest_pdf", new_callable=AsyncMock
    ) as ingest_pdf:
        result = runner.invoke(
            app,
            ["ingest", str(pdf), "--doi", "10.1234/x", "--output", str(tmp_path / "o")],
        )
    assert result.exit_code != 0
    assert "MAILTO_NOT_SET" in result.output
    ingest_pdf.assert_not_called()


@pytest.mark.asyncio
async def test_the_library_refuses_before_any_request_without_a_contact_email(
    no_contact, tmp_path
):
    client = _metadata_client("https://example.test/a.pdf")
    session = AsyncMock(spec=aiohttp.ClientSession)
    downloader = AsyncPDFDownloader(output_dir=tmp_path)
    with pytest.raises(pdf_config.MailtoNotSetError):
        await downloader.process_doi(session, client, "10.1234/x")
    with pytest.raises(pdf_config.MailtoNotSetError):
        pdf = tmp_path / "in.pdf"
        pdf.write_bytes(pdf_bytes())
        await downloader.ingest_pdf(client, pdf, "10.1234/x")
    client.get.assert_not_called()
    session.get.assert_not_called()


@pytest.mark.asyncio
async def test_the_apps_scholar_mailto_is_what_the_providers_receive(
    app_contact_only, tmp_path
):
    client = _metadata_client(None)
    downloader = AsyncPDFDownloader(output_dir=tmp_path)
    await downloader.process_doi(AsyncMock(spec=aiohttp.ClientSession), client, "10.1/x")
    sent = [call.kwargs.get("params") or {} for call in client.get.call_args_list]
    assert {"email": CONTACT} in sent  # Unpaywall reads its e-mail on every call
    assert all("student@" not in str(params) for params in sent)


def test_scholar_mailto_wins_over_the_kits_own_mailto(monkeypatch):
    from scholar_search import config as search_config

    monkeypatch.setattr(search_config.settings, "mailto", CONTACT)
    monkeypatch.setattr(pdf_config.settings, "mailto", "kit@example.org")
    assert pdf_config.contact_email() == CONTACT
    monkeypatch.setattr(search_config.settings, "mailto", None)
    assert pdf_config.contact_email() == "kit@example.org"


# --------------------------------------------------------------------- K2: the app's name


def test_no_browser_user_agent_remains_in_the_kit():
    offenders = [
        str(path.relative_to(PACKAGE_DIR))
        for path in PACKAGE_DIR.rglob("*.py")
        if any(word in path.read_text(encoding="utf-8") for word in ("Mozilla/", "Chrome/"))
    ]
    assert offenders == []


@pytest.mark.asyncio
async def test_a_download_names_the_app_and_its_contact_on_a_stub_server(
    app_contact_only, tmp_path
):
    seen: list[str] = []
    body = pdf_bytes()

    async def serve(request: web.Request) -> web.Response:
        seen.append(request.headers.get("User-Agent", ""))
        return web.Response(body=body, content_type="application/pdf")

    server = web.Application()
    server.router.add_get("/paper.pdf", serve)
    runner_ = web.AppRunner(server)
    await runner_.setup()
    site = web.TCPSite(runner_, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    try:
        downloader = AsyncPDFDownloader(output_dir=tmp_path / "out")
        async with aiohttp.ClientSession() as session:
            ok = await downloader.download_pdf(
                session, f"http://127.0.0.1:{port}/paper.pdf", tmp_path / "out" / "a.pdf"
            )
    finally:
        await runner_.cleanup()
    assert ok is True
    assert len(seen) == 1
    agent = seen[0]
    assert agent.startswith("nexus-scholar/"), agent
    assert agent.endswith(f"(mailto:{CONTACT})"), agent
    assert "Mozilla" not in agent and "Chrome" not in agent


@pytest.mark.asyncio
async def test_the_provider_lookups_name_the_app_and_its_contact(app_contact_only, tmp_path):
    client = _metadata_client(None)
    downloader = AsyncPDFDownloader(output_dir=tmp_path)
    await downloader.process_doi(AsyncMock(spec=aiohttp.ClientSession), client, "10.1/x")
    agents = [(call.kwargs.get("headers") or {}).get("User-Agent", "") for call in client.get.call_args_list]
    assert agents and all(a.startswith("nexus-scholar/") and a.endswith(f"(mailto:{CONTACT})") for a in agents)


# --------------------------------------------------------------------- K3: no guessed URL, no proxy


def test_the_publisher_patterns_are_off_by_default():
    assert pdf_config.Settings.model_fields["enable_publisher_direct_patterns"].default is False


@pytest.mark.asyncio
async def test_no_guessed_publisher_url_is_requested_even_when_the_setting_asks(
    app_contact_only, monkeypatch, tmp_path
):
    monkeypatch.setattr(pdf_config.settings, "enable_publisher_direct_patterns", True)
    landing = "https://ieeexplore.ieee.org/document/10209481"
    client = _metadata_client(landing)

    async def html_page(*args, **kwargs):
        yield b"<html><body>Checking your browser...</body></html>"

    response = AsyncMock()
    response.raise_for_status = MagicMock()
    response.__aenter__ = AsyncMock(return_value=response)
    response.content.iter_chunked = html_page
    session = AsyncMock(spec=aiohttp.ClientSession)
    session.get.return_value = response

    downloader = AsyncPDFDownloader(output_dir=tmp_path)
    result = await downloader.process_doi(session, client, "10.1109/ICCV.2023.01234")

    requested = [call.args[0] for call in session.get.call_args_list]
    assert requested == [landing], requested  # only the provider's own location
    assert result.success is False


@pytest.mark.parametrize("command", ["download", "ingest"])
def test_a_production_command_refuses_the_publisher_pattern_setting(
    command, app_contact_only, monkeypatch, tmp_path
):
    monkeypatch.setattr(pdf_config.settings, "enable_publisher_direct_patterns", True)
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(pdf_bytes())
    args = (
        ["download", "--doi", "10.1/x", "--output", str(tmp_path / "o")]
        if command == "download"
        else ["ingest", str(pdf), "--doi", "10.1/x", "--output", str(tmp_path / "o")]
    )
    with patch("scholar_pdf.cli.AsyncPDFDownloader", autospec=True) as downloader:
        result = runner.invoke(app, args)
    assert result.exit_code != 0
    text = " ".join(result.output.split())
    assert "ENABLE_PUBLISHER_DIRECT_PATTERNS" in text
    assert "item 24" in text
    assert "removed" in text  # Part K: a stale setting is refused, not silently ignored
    downloader.assert_not_called()


@pytest.mark.parametrize("command", ["download", "ingest"])
@pytest.mark.parametrize("source", ["flag", "setting"])
def test_a_production_command_refuses_a_set_proxy_with_a_message(
    command, source, app_contact_only, monkeypatch, tmp_path
):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(pdf_bytes())
    args = (
        ["download", "--doi", "10.1/x", "--output", str(tmp_path / "o")]
        if command == "download"
        else ["ingest", str(pdf), "--doi", "10.1/x", "--output", str(tmp_path / "o")]
    )
    if source == "flag":
        args += ["--proxy", "https://proxy.example.edu"]
    else:
        monkeypatch.setattr(pdf_config.settings, "proxy_url", "https://proxy.example.edu")
    with patch("scholar_pdf.cli.AsyncPDFDownloader", autospec=True) as downloader:
        result = runner.invoke(app, args)
    assert result.exit_code != 0
    text = " ".join(result.output.split())
    assert "PROXY_REFUSED" in text
    assert "item 25" in text
    downloader.assert_not_called()


def test_a_download_with_contact_and_no_proxy_still_runs(app_contact_only, tmp_path):
    with patch(
        "scholar_pdf.cli.AsyncPDFDownloader.process_doi", new_callable=AsyncMock
    ) as process_doi:
        process_doi.return_value = DownloadResult(
            doi="10.1/x", success=True, file_path=tmp_path / "x.pdf"
        )
        result = runner.invoke(
            app, ["download", "--doi", "10.1/x", "--output", str(tmp_path)]
        )
    assert result.exit_code == 0, result.output
    process_doi.assert_called_once()


def test_the_library_does_not_read_proxy_url(monkeypatch, tmp_path):
    """Review finding 2: PROXY_URL in the environment or .env never reaches the library."""
    monkeypatch.setattr(pdf_config.settings, "proxy_url", "https://proxy.example.edu")
    downloader = AsyncPDFDownloader(output_dir=tmp_path)
    assert downloader.institutional_gateway_url == "" and downloader.proxy_url == ""
