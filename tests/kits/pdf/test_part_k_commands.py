"""Part K item 10: honest commands (PDF-15, PDF-18, PDF-05).

- PDF-15: ``ingest`` exited 0 when it stored nothing, and ``download --input
  <missing file>`` exited 0 with "No DOIs provided". Both now exit non-zero;
  ``download``'s codes 3, 4 and 5 (H-pdf-resolver-locations item 9) keep their
  meaning.
- PDF-18: a missing year became the text ``'None'`` and reached the BibTeX
  export as ``year={None}``; the BibTeX export appended duplicates; the JSON
  export was rewritten in place. Now no ``'None'`` year, one entry per DOI, and
  both exports are written whole or not at all.
- PDF-05: ``--smart-names`` was accepted and did nothing, ``_safe_filename`` was
  never called and ``models.py`` was imported by nothing. They are removed.
"""

from __future__ import annotations

import importlib.util
import json
import re
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from scholar_pdf import cli as cli_module
from scholar_pdf.cli import app
from scholar_pdf.downloader import AsyncPDFDownloader, DownloadResult

from .test_acquisition_contract import pdf_bytes
from .test_open_copy_resolver import FakeLookups, closed_unpaywall

runner = CliRunner()

# Typer draws a usage error in a Rich box: colour codes on GitHub Actions (Typer forces a
# terminal there), border characters, and lines wrapped at the box width, which can split a
# long path in the middle. The first CI run with `pytest -n auto` (H-gate-and-ci, 2026-11-23)
# failed on that. The searches below read the text without styling, borders or line breaks.
_STYLE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_BOX = re.compile(r"[─-╿]")


def text_of(result) -> str:
    """The output as words: no colour codes, no box borders, whitespace collapsed."""
    return " ".join(_BOX.sub(" ", _STYLE.sub("", result.output)).split())


def compact_of(result) -> str:
    """The output with no whitespace at all, so a path the box wrapped mid-name reads whole."""
    return "".join(text_of(result).split())


# ------------------------------------------------------------------ PDF-15


def test_ingest_of_a_missing_file_exits_non_zero(tmp_path):
    result = runner.invoke(app, ["ingest", str(tmp_path / "absent.pdf"), "--doi", "10.1/x", "--output", str(tmp_path / "o")])
    assert result.exit_code == 1, text_of(result)
    assert "Failed to ingest" in text_of(result)


def test_ingest_of_a_file_that_is_not_a_pdf_exits_non_zero(tmp_path, monkeypatch):
    page = tmp_path / "page.pdf"
    page.write_bytes(b"<html><body>Sign in</body></html>")
    lookups = FakeLookups({"title": "T"}, closed_unpaywall())
    monkeypatch.setattr("scholar_search.http_client.AcademicHttpClient", lambda **kwargs: lookups)

    result = runner.invoke(app, ["ingest", str(page), "--doi", "10.1/x", "--output", str(tmp_path / "o")])

    assert result.exit_code == 1, text_of(result)
    assert "not a PDF" in text_of(result)


def test_ingest_that_stores_its_file_exits_zero(tmp_path, monkeypatch):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(pdf_bytes())
    lookups = FakeLookups({"title": "T"}, closed_unpaywall())
    monkeypatch.setattr("scholar_search.http_client.AcademicHttpClient", lambda **kwargs: lookups)

    result = runner.invoke(app, ["ingest", str(pdf), "--doi", "10.1/x", "--output", str(tmp_path / "o")])

    assert result.exit_code == 0, text_of(result)


def test_download_with_a_missing_input_file_exits_non_zero(tmp_path):
    with patch("scholar_pdf.cli.AsyncPDFDownloader.process_doi", new_callable=AsyncMock) as process_doi:
        result = runner.invoke(app, ["download", "--input", str(tmp_path / "absent.json"), "--output", str(tmp_path / "o")])
    assert result.exit_code == 2, text_of(result)
    assert "absent.json" in compact_of(result)
    assert "No DOIs provided" not in text_of(result)
    process_doi.assert_not_called()


def test_a_missing_input_file_is_named_even_when_the_error_box_wraps_its_name(tmp_path):
    """A name longer than the error box is split across lines; it is still found whole."""
    name = f"absent-{'x' * 90}.json"
    with patch("scholar_pdf.cli.AsyncPDFDownloader.process_doi", new_callable=AsyncMock) as process_doi:
        result = runner.invoke(app, ["download", "--input", str(tmp_path / name), "--output", str(tmp_path / "o")])
    assert result.exit_code == 2, text_of(result)
    assert name in compact_of(result)
    process_doi.assert_not_called()


def test_the_text_helpers_drop_colour_codes_and_box_borders():
    class Out:
        output = "\x1b[31m│\x1b[0m C:\\tmp\\abse \x1b[31m│\x1b[0m\n\x1b[31m│\x1b[0m nt.json does not exist \x1b[31m│\x1b[0m\n"

    assert text_of(Out) == "C:\\tmp\\abse nt.json does not exist"
    assert "absent.json" in compact_of(Out)


def test_download_with_an_input_file_that_is_not_a_list_exits_non_zero(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"doi": "10.1/x"}), encoding="utf-8")
    result = runner.invoke(app, ["download", "--input", str(bad), "--output", str(tmp_path / "o")])
    assert result.exit_code == 1, text_of(result)
    assert "Error parsing input file" in text_of(result)


# ------------------------------------------------------------------ PDF-18


@pytest.mark.parametrize(
    ("payload", "source"),
    [({"title": "T", "publication_year": None}, "openalex"), ({"title": "T", "year": None}, "unpaywall")],
)
def test_a_missing_year_is_empty_not_none(payload, source, tmp_path):
    metadata = AsyncPDFDownloader(output_dir=tmp_path).extract_metadata(payload, source)
    assert metadata["year"] == ""


def _acquired(doi: str, year: str = "", author: str = "Smith") -> DownloadResult:
    return DownloadResult(
        doi=doi,
        success=True,
        file_path=None,
        metadata={"title": f"Title {doi}", "author": author, "year": year},
    )


def test_the_bibtex_export_has_one_entry_per_doi_and_no_none_year(tmp_path):
    cli_module._export_results("bibtex", tmp_path, [_acquired("10.1/a"), _acquired("10.1/b", "2021")])
    cli_module._export_results("bibtex", tmp_path, [_acquired("10.1/a"), _acquired("10.1/c", "2022")])

    text = (tmp_path / "download_summary.bibtex").read_text(encoding="utf-8")
    assert text.count("doi={10.1/a}") == 1
    assert text.count("doi={10.1/b}") == 1 and text.count("doi={10.1/c}") == 1
    assert "None" not in text
    assert "year={2021}" in text


def test_the_json_export_is_written_whole_or_not_at_all(tmp_path):
    cli_module._export_results("json", tmp_path, [_acquired("10.1/a", "2020")])
    before = (tmp_path / "download_summary.json").read_bytes()
    broken = _acquired("10.1/b")
    broken.metadata["title"] = object()  # cannot be written as JSON

    with pytest.raises(TypeError):
        cli_module._export_results("json", tmp_path, [broken])

    assert (tmp_path / "download_summary.json").read_bytes() == before
    assert json.loads(before) == [
        {"doi": "10.1/a", "file_path": None, "metadata": {"title": "Title 10.1/a", "author": "Smith", "year": "2020"}}
    ]


def test_the_bibtex_export_is_written_whole_or_not_at_all(tmp_path, monkeypatch):
    cli_module._export_results("bibtex", tmp_path, [_acquired("10.1/a", "2020")])
    before = (tmp_path / "download_summary.bibtex").read_bytes()

    def fail(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(cli_module.os, "replace", fail)
    with pytest.raises(OSError):
        cli_module._export_results("bibtex", tmp_path, [_acquired("10.1/b", "2021")])

    assert (tmp_path / "download_summary.bibtex").read_bytes() == before
    assert not [p for p in tmp_path.iterdir() if p.name.endswith(".tmp")]


# ------------------------------------------------------------------ PDF-05


@pytest.mark.parametrize("command", ["download", "ingest"])
def test_the_no_op_smart_names_option_is_gone(command, tmp_path):
    pdf = tmp_path / "p.pdf"
    pdf.write_bytes(pdf_bytes())
    args = ["download", "--doi", "10.1/x"] if command == "download" else ["ingest", str(pdf), "--doi", "10.1/x"]
    with patch("scholar_pdf.cli.AsyncPDFDownloader", autospec=True):
        result = runner.invoke(app, [*args, "--output", str(tmp_path / "o"), "--smart-names"])
    assert result.exit_code == 2  # no such option


def test_the_dead_code_is_gone():
    assert not hasattr(AsyncPDFDownloader, "_safe_filename")
    assert importlib.util.find_spec("scholar_pdf.models") is None
    with pytest.raises(TypeError):
        AsyncPDFDownloader(use_smart_names=True)


def test_the_parked_pipeline_template_no_longer_passes_smart_names():
    from scholar_harness.console.api import pipelines

    source = importlib.util.find_spec(pipelines.__name__).origin
    with open(source, encoding="utf-8") as stream:
        assert "smart-names" not in stream.read()
