"""Tests for the retraction checker (OpenAlex + Crossref)."""

from __future__ import annotations

from scholar_verify import retraction
from scholar_verify.http_client import VerifyHttpClient


def test_openalex_by_doi_cache_and_crossref_shape():
    """A clean record should produce non-flagged rows with datacite-aware Crossref."""
    records = [
        {
            "workspace_id": "S001",
            "study": {"title": "Weed segmentation with UAVs", "year": 2023},
        }
    ]
    included = [
        {
            "workspace_id": "S001",
            "external_ids": {"doi": "10.1000/xyz123"},
        }
    ]
    # monkeypatch fetch to avoid hitting the network
    calls = {}
    http = VerifyHttpClient()

    def fake_fetch(url):
        calls[url] = True
        if "openalex.org" in url:
            return {"is_retracted": False, "last_status_in_oa": "available", "id": "W123"}
        if "crossref.org" in url:
            return {"message": {"update-to": []}}
        return {}

    http.fetch_json = fake_fetch
    checker = retraction.RetractionChecker(http=http, sleep_s=0)
    out = checker.check(records, included)

    row = out["results"][0]
    assert row["flagged"] is False
    assert row["openalex"]["is_retracted"] is False
    assert row["openalex"]["lookup"] == "via_doi"
    assert row["crossref"]["update_to"] == []
    assert "openalex.org" in "".join(calls) and "crossref.org" in "".join(calls)


def test_flagged_when_openalex_retracted():
    http = VerifyHttpClient()
    http.fetch_json = (
        lambda url: {"is_retracted": True, "last_status_in_oa": "retracted", "id": "W9"}
        if "openalex" in url
        else {"message": {"update-to": []}}
    )
    checker = retraction.RetractionChecker(http=http, sleep_s=0)
    out = checker.check(
        [{"workspace_id": "S1", "study": {"title": "t", "year": 2020}}],
        [{"workspace_id": "S1", "external_ids": {"doi": "10.1/x"}}],
    )
    row = out["results"][0]
    assert row["flagged"] is True
    assert "openalex:retracted" in row["flag_reasons"]
    assert out["summary"]["retracted_openalex"] == 1


def test_flagged_from_crossref_expression_of_concern():
    http = VerifyHttpClient()
    http.fetch_json = (
        lambda url: {"is_retracted": False, "last_status_in_oa": None, "id": "W2"}
        if "openalex" in url
        else {"message": {"update-to": [{"type": "expression-of-concern", "label": "EoC", "updated": "2024-01-01"}]}}
    )
    checker = retraction.RetractionChecker(http=http, sleep_s=0)
    out = checker.check(
        [{"workspace_id": "S2", "study": {"title": "t", "year": 2021}}],
        [{"workspace_id": "S2", "external_ids": {"doi": "10.1/x"}}],
    )
    row = out["results"][0]
    assert row["flagged"] is True
    assert "crossref:expression-of-concern" in row["flag_reasons"]


def test_unresolved_openalex_marks_error_and_none():
    """A 404'd lookup must surface as unresolved, not silently skipped."""
    http = VerifyHttpClient()
    http.fetch_json = lambda url: {"_status": 404}
    checker = retraction.RetractionChecker(http=http, sleep_s=0)
    out = checker.check(
        [{"workspace_id": "S3", "study": {"title": "t", "year": 2022}}],
        [{"workspace_id": "S3", "external_ids": {}}],
    )
    row = out["results"][0]
    assert row["openalex"]["error"]["_status"] == 404
    assert row["openalex"]["is_retracted"] is None


def test_arxiv_when_no_doi():
    http = VerifyHttpClient()
    calls = []

    def fake(url: str):
        calls.append(url)
        if "abs/" in url:
            return {"id": "W-arxiv", "is_retracted": False}
        return {}

    http.fetch_json = fake
    checker = retraction.RetractionChecker(http=http, sleep_s=0)
    out = checker.check(
        [{"workspace_id": "S4", "study": {"title": "arxiv paper", "year": 2023}}],
        [{"workspace_id": "S4", "external_ids": {"arxiv_id": "2301.00001"}}],
    )
    assert calls and any("arxiv.org" in c for c in calls)
    assert out["results"][0]["openalex"]["is_retracted"] is False


def test_render_report_contains_summary():
    rows = [{"workspace_id": "S1", "year": 2020, "flagged": False, "openalex": {"is_retracted": False}, "crossref": {"update_to": []}, "doi": "10.1/x"}]
    out = {
        "run_metadata": {"run_date_utc": "2024-06-01T00:00:00S"},
        "summary": {
            "studies_checked": 1,
            "flagged_any": 0,
            "retracted_openalex": 0,
            "crossref_update_events": {},
            "openalex_provenance_status": {"available": 1},
            "unresolved_lookups": [],
        },
        "results": rows,
    }
    md = retraction.render_retraction_report(out)
    assert "# Retraction & Publication-Status Check" in md
    assert "| Studies checked | 1 |" in md
