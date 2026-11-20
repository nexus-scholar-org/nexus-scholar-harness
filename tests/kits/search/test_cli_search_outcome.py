"""H-run-small-fixes Part B, finding 29: `scholar-search search` says when it was cut and fails loudly.

The acceptance run of 2026-11-20 used `scholar-search search --protocol …`:
the command stopped at 100 records by default and printed "Saved 100
documents" with no word that more existed, and an arXiv timeout saved an
empty file and exited 0. The engine's legs (`SearchEngine.last_legs`) already
know both facts; the command now says them.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from scholar_search.cli import app
from scholar_search.models import Document, ExternalIds, SearchLeg

runner = CliRunner()


def _doc(i: int, provider: str = "openalex") -> Document:
    return Document(title=f"Record {i}", year=2024, provider=provider, external_ids=ExternalIds(doi=f"10.1/{i}"))


def _engine(docs: list[Document], legs: list[SearchLeg]):
    async def search_all(self, query, dedup=True, progress_callback=None):  # noqa: ARG001
        self.last_legs = legs
        return docs

    return search_all


def _invoke(monkeypatch, docs, legs, *args: str):
    monkeypatch.setattr("scholar_search.cli.SearchEngine.search_all", _engine(docs, legs))
    return runner.invoke(app, ["search", "weed AND uav", *args])


def _flat(text: str) -> str:
    return " ".join(text.split())


def test_finding_29_a_result_stopped_at_the_limit_says_more_exist(monkeypatch, tmp_path: Path):
    legs = [SearchLeg(provider="openalex", query_id="Q", reported_total=781, fetched=100, cap=100, cap_hit=True, status="completed")]
    out = tmp_path / "r.ris"
    result = _invoke(monkeypatch, [_doc(i) for i in range(100)], legs, "--provider", "openalex", "--limit", "100",
                     "--output", str(out), "--format", "ris")
    assert result.exit_code == 0, result.stdout
    text = _flat(result.stdout)
    assert "Saved 100 documents" in text
    assert "openalex stopped at the limit of 100 records; it reports 781" in text
    assert "--limit" in text


def test_finding_29_a_failed_database_with_nothing_saved_exits_non_zero(monkeypatch, tmp_path: Path):
    legs = [SearchLeg(provider="arxiv", query_id="Q", status="failed", error="arxiv did not answer within 30 s",
                      error_code="PROVIDER_TIMEOUT")]
    out = tmp_path / "r.ris"
    result = _invoke(monkeypatch, [], legs, "--provider", "arxiv", "--output", str(out), "--format", "ris")
    assert result.exit_code == 1, result.stdout
    text = _flat(result.stdout)
    assert "arxiv failed (PROVIDER_TIMEOUT)" in text
    assert "Nothing was saved" in text
    assert not out.exists()


def test_a_failed_database_beside_a_working_one_saves_and_exits_2(monkeypatch, tmp_path: Path):
    legs = [
        SearchLeg(provider="openalex", query_id="Q", reported_total=3, fetched=3, status="completed"),
        SearchLeg(provider="arxiv", query_id="Q", status="failed", error="timeout", error_code="PROVIDER_TIMEOUT"),
    ]
    out = tmp_path / "r.json"
    result = _invoke(monkeypatch, [_doc(i) for i in range(3)], legs, "--output", str(out))
    # Some records were saved, so the result is partial, not failed: exit 2 says so.
    assert result.exit_code == 2, result.stdout
    assert out.exists()
    assert "arxiv failed (PROVIDER_TIMEOUT)" in _flat(result.stdout)


def test_a_complete_result_says_nothing_more(monkeypatch, tmp_path: Path):
    legs = [SearchLeg(provider="openalex", query_id="Q", reported_total=3, fetched=3, cap=100, status="completed")]
    result = _invoke(monkeypatch, [_doc(i) for i in range(3)], legs, "--provider", "openalex",
                     "--output", str(tmp_path / "r.json"))
    assert result.exit_code == 0
    assert "stopped at the limit" not in result.stdout and "failed" not in result.stdout
