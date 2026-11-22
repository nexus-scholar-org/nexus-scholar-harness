"""Part K item 8 (PDF-07, the kit's half): a manifest row for every DOI asked.

The kit stored files as ``DOC-<sha256>.pdf`` and kept no record of which DOI or
study a file belongs to. Now the downloader writes one JSON line per DOI asked,
at the path its caller gives (``AsyncPDFDownloader(manifest_path=...)``,
``download --manifest PATH``); ``download`` writes ``download-manifest.jsonl``
in its output folder when none is given. No file is kept without its row: if
the row cannot be written, a file this call created is removed and the DOI
fails. The legacy ``literature/pdf_manifest.json`` is never written.

A stub server on 127.0.0.1 gives the redirects; the lookups are in memory.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import aiohttp
import pytest
from typer.testing import CliRunner

from scholar_pdf.cli import app
from scholar_pdf.downloader import AsyncPDFDownloader

from .conftest import TEST_CONTACT, TEST_OPENALEX_KEY
from .stub_server import Answer, StubPdfHost
from .test_acquisition_contract import pdf_bytes
from .test_open_copy_resolver import (
    DOI,
    PMC_PDF,
    FakeLookups,
    FakePdfHosts,
    closed_openalex,
    closed_unpaywall,
    openalex_answer,
    unpaywall_answer,
)

runner = CliRunner()


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def located(url: str) -> FakeLookups:
    openalex = {
        "title": "A paper",
        "open_access": {"is_oa": True},
        "locations": [
            {
                "is_oa": True,
                "pdf_url": url,
                "version": "acceptedVersion",
                "license": "cc-by",
                "source": {"display_name": "A Repository", "type": "repository"},
            }
        ],
    }
    return FakeLookups(openalex, closed_unpaywall())


@pytest.mark.asyncio
async def test_a_stored_file_has_its_row_with_the_redirects_and_the_checks(tmp_path):
    body = pdf_bytes()
    manifest = tmp_path / "run" / "fetch.jsonl"
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "run" / "pdfs", manifest_path=manifest)
    routes = {"/r/paper.pdf": [Answer(redirect_to="/files/paper.pdf")], "/files/paper.pdf": [Answer(body=body)]}
    async with StubPdfHost(routes) as host:
        async with aiohttp.ClientSession() as session:
            result = await downloader.process_doi(
                session, located(host.url("/r/paper.pdf")), "10.1/a", study_id="SCI-000007"
            )
        asked, landed = host.url("/r/paper.pdf"), host.url("/files/paper.pdf")

    assert result.success is True, result.error_message
    [row] = rows(manifest)
    assert row["doi"] == "10.1/a" and row["study_id"] == "SCI-000007"
    assert row["outcome"] == "ACQUIRED"
    assert row["file"] == "pdfs/" + result.file_path.name  # relative to the manifest's folder
    assert row["size"] == len(body)
    assert row["sha256"] == hashlib.sha256(body).hexdigest()
    assert row["address"] == asked
    assert row["final_url"] == landed
    assert row["redirects"] == [asked]
    assert row["http_status"] == 200
    assert row["content_type"].startswith("application/pdf")
    assert (row["version"], row["license"], row["host_type"]) == ("acceptedVersion", "cc-by", "repository")
    assert (row["source_name"], row["provider"]) == ("A Repository", "openalex")
    assert row["route"] == "open_location"
    assert row["access_status"] == "VERIFIED_OPEN_ACCESS"
    assert row["checks"]["pdf_header"] == "pass"
    assert row["checks"]["pdf_trailer"] == "pass"
    assert row["checks"]["size_floor"] == "pass"
    assert row["checks"]["identity"] in {"doi found", "title found", "not found: check it", "not checked"}
    assert [look["service"] for look in row["lookups"]] == ["openalex", "unpaywall"]
    assert row["lookups"][0]["state"] == "ANSWERED"
    assert row["time"].endswith("Z") or row["time"].endswith("+00:00")
    assert row["app_version"]
    assert [request["url"] for request in row["requests"]] == [asked]


@pytest.mark.asyncio
async def test_a_doi_without_a_file_has_its_row_too(tmp_path):
    manifest = tmp_path / "m.jsonl"
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out", manifest_path=manifest)

    await downloader.process_doi(FakePdfHosts(), FakeLookups(closed_openalex(), closed_unpaywall()), "10.1/closed")
    await downloader.process_doi(FakePdfHosts({PMC_PDF: pdf_bytes()}), FakeLookups(openalex_answer(), unpaywall_answer()), DOI)

    first, second = rows(manifest)
    assert (first["doi"], first["outcome"], first["file"], first["sha256"]) == ("10.1/closed", "NO_OPEN_COPY_LISTED", None, None)
    assert "No open copy is listed" in first["message"]
    assert first["study_id"] is None
    assert (second["doi"], second["outcome"]) == (DOI, "ACQUIRED")


@pytest.mark.asyncio
async def test_the_row_holds_neither_the_contact_nor_the_key(tmp_path):
    manifest = tmp_path / "m.jsonl"
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out", manifest_path=manifest)

    await downloader.process_doi(FakePdfHosts({PMC_PDF: pdf_bytes()}), FakeLookups(openalex_answer(), unpaywall_answer()), DOI)

    text = manifest.read_text(encoding="utf-8")
    assert TEST_CONTACT not in text and TEST_OPENALEX_KEY not in text
    assert "api.openalex.org" not in text and "api.unpaywall.org" not in text


@pytest.mark.asyncio
async def test_no_file_is_kept_without_its_row(tmp_path):
    manifest = tmp_path / "not-a-file"
    manifest.mkdir()  # the row cannot be appended to a folder
    out = tmp_path / "out"
    downloader = AsyncPDFDownloader(output_dir=out, manifest_path=manifest)

    result = await downloader.process_doi(
        FakePdfHosts({PMC_PDF: pdf_bytes()}), FakeLookups(openalex_answer(), unpaywall_answer()), DOI
    )

    assert result.success is False
    assert result.outcome == "MANIFEST_NOT_WRITTEN"
    assert result.file_path is None
    assert list(out.glob("*.pdf")) == []
    assert "manifest" in result.error_message


@pytest.mark.asyncio
async def test_a_file_stored_before_is_not_removed_when_the_row_fails(tmp_path):
    out = tmp_path / "out"
    lookups = FakeLookups(openalex_answer(), unpaywall_answer())
    first = await AsyncPDFDownloader(output_dir=out, manifest_path=tmp_path / "ok.jsonl").process_doi(
        FakePdfHosts({PMC_PDF: pdf_bytes()}), lookups, DOI
    )
    folder = tmp_path / "folder"
    folder.mkdir()

    second = await AsyncPDFDownloader(output_dir=out, manifest_path=folder).process_doi(
        FakePdfHosts({PMC_PDF: pdf_bytes()}), lookups, DOI
    )

    assert first.success is True and second.success is False
    assert first.file_path.exists()  # not this call's file: kept, with its earlier row


@pytest.mark.asyncio
async def test_ingest_writes_its_row(tmp_path):
    source = tmp_path / "mine.pdf"
    source.write_bytes(pdf_bytes())
    manifest = tmp_path / "m.jsonl"
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out", manifest_path=manifest)

    result = await downloader.ingest_pdf(FakeLookups(openalex_answer(), unpaywall_answer()), source, DOI)

    [row] = rows(manifest)
    assert result.success is True
    assert (row["doi"], row["outcome"], row["route"]) == (DOI, "ACQUIRED", "user_provided")
    assert row["access_status"] == "USER_PROVIDED"
    assert row["address"] is None and row["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()


def _offline_command(monkeypatch, lookups, hosts):
    monkeypatch.setattr("scholar_search.http_client.AcademicHttpClient", lambda **kwargs: lookups)
    monkeypatch.setattr(aiohttp, "ClientSession", lambda *args, **kwargs: hosts)


def test_download_writes_its_manifest_in_the_output_folder_by_default(tmp_path, monkeypatch):
    _offline_command(monkeypatch, FakeLookups(openalex_answer(), unpaywall_answer()), FakePdfHosts({PMC_PDF: pdf_bytes()}))
    included = tmp_path / "literature" / "included.json"
    included.parent.mkdir()
    included.write_text(
        json.dumps([{"workspace_id": "SCI-000002", "doi": DOI, "title": "t"}, {"workspace_id": "SCI-000003", "title": "no doi"}]),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["download", "--input", str(included), "--output", str(tmp_path / "pdfs")])

    assert result.exit_code == 0, result.output
    [row] = rows(tmp_path / "pdfs" / "download-manifest.jsonl")
    assert (row["doi"], row["study_id"], row["outcome"]) == (DOI, "SCI-000002", "ACQUIRED")
    assert not (tmp_path / "literature" / "pdf_manifest.json").exists()
    assert not list(tmp_path.rglob("pdf_manifest.json"))


def test_download_writes_its_manifest_where_the_caller_says(tmp_path, monkeypatch):
    _offline_command(monkeypatch, FakeLookups(closed_openalex(), closed_unpaywall()), FakePdfHosts())
    manifest = tmp_path / "runs" / "one.jsonl"

    result = runner.invoke(
        app, ["download", "--doi", "10.1/x", "--doi", "10.1/y", "--output", str(tmp_path / "pdfs"), "--manifest", str(manifest)]
    )

    assert result.exit_code == 5, result.output
    assert sorted(row["doi"] for row in rows(manifest)) == ["10.1/x", "10.1/y"]
    assert not (tmp_path / "pdfs" / "download-manifest.jsonl").exists()
