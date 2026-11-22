"""Part K (M12a), review round 1: no lookup cache, no forward proxy, definitive errors, one lookup per DOI."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from typer.testing import CliRunner

from scholar_pdf import cli as pdf_cli
from scholar_pdf.downloader import AsyncPDFDownloader, DownloadResult, _transient


def test_the_kits_lookup_clients_keep_no_disk_cache(tmp_path, monkeypatch):
    """Finding 1: the lookup addresses carry the OpenAlex key and the e-mail."""
    made: list[dict] = []

    class Spy:
        def __init__(self, *args, **kwargs):
            made.append(kwargs)

        async def close(self):
            return None

    monkeypatch.setattr("scholar_search.http_client.AcademicHttpClient", Spy)
    with patch("scholar_pdf.cli.AsyncPDFDownloader.process_doi", new_callable=AsyncMock) as process_doi:
        process_doi.return_value = DownloadResult(doi="10.1/x", success=False)
        CliRunner().invoke(pdf_cli.app, ["download", "--doi", "10.1/x", "--output", str(tmp_path)])
    assert made and all(kwargs.get("cache_enabled") is False for kwargs in made)


def test_the_downloader_refuses_a_forward_proxy(tmp_path):
    """Finding 2: a file through a proxy would be labelled open access (item 25)."""
    with pytest.raises(ValueError, match="PROXY_REFUSED"):
        AsyncPDFDownloader(output_dir=tmp_path, forward_proxy_url="http://proxy.example.edu:3128")


@pytest.mark.parametrize("error", [aiohttp.InvalidURL("not a url"), aiohttp.ClientSSLError(None, OSError("bad certificate"))])
def test_an_invalid_address_or_a_certificate_error_is_not_retried(error):
    """Finding 6."""
    assert _transient(error) is False


def test_the_input_file_is_deduplicated_on_the_bare_doi(tmp_path):
    """Finding 8: one lookup and one row per DOI however it is written."""
    source = tmp_path / "in.json"
    source.write_text(json.dumps([{"doi": "10.1/x"}, {"doi": "https://doi.org/10.1/x"}, {"external_ids": {"doi": "doi:10.1/x"}}]),
                      encoding="utf-8")
    with patch("scholar_pdf.cli.AsyncPDFDownloader.process_doi", new_callable=AsyncMock) as process_doi:
        process_doi.return_value = DownloadResult(doi="10.1/x", success=False)
        CliRunner().invoke(pdf_cli.app, ["download", "--input", str(source), "--output", str(tmp_path / "o")])
    assert process_doi.call_count == 1
