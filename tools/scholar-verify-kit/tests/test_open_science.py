"""Tests for the deterministic DAS/CAS open-science scanner."""

from __future__ import annotations

from pathlib import Path

from scholar_verify import open_science
from scholar_verify.open_science import DATA_PATTERNS, classify, links_near, scan_record

RECORD = {
    "workspace_id": "W1",
    "study": {"title": "UAV weed detection", "year": 2023, "extracted_md": "W1.md"},
}


def test_classify_matrix():
    assert classify([{"signal": "X"}], [], []) == "statement-only"
    assert classify([{"signal": "X"}], [], [{"url": "https://github.com/a/b"}]) == "public+link"
    assert classify([{"signal": "avail_on_request"}], [], []) == "request-only"
    assert classify([], [{"signal": "negation"}], []) == "explicitly-unavailable"
    assert classify([], [], []) == "not-stated"


def test_links_near_rejects_non_repo_hosts():
    found = links_near("See https://example.com/data and https://github.com/foo/bar")
    urls = [f["url"] for f in found]
    assert urls == ["https://github.com/foo/bar"]


def test_scan_record_classifies_das_cas(tmp_path: Path):
    fulltext = """
    Data Availability Statement: The datasets generated during the study
    are available at https://zenodo.org/records/1234.
    Code is available on request from the corresponding author.
    """
    row = scan_record(RECORD, fulltext)
    assert row["das"] == "public+link"
    # CAS shares the whole-text repo-link list; "code is available" + zenodo link -> public+link (per rule)
    assert row["cas"] == "public+link"
    assert any(s["signal"] == "data_avail_kw" for s in row["data_signals"])
    assert any(s["signal"] == "code_is_available" for s in row["code_signals"])


def test_scan_record_explicit_unavailable():
    fulltext = "The data are not publicly available, and the code will not be published."
    row = scan_record(RECORD, fulltext)
    assert row["das"] == "explicitly-unavailable"
    assert row["cas"] == "explicitly-unavailable"


def test_run_summary_counts(tmp_path: Path):
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    (extracted / "W1.md").write_text(
        "Data available at https://github.com/user/data; our code is released.", encoding="utf-8"
    )
    out = open_science.run([RECORD], extracted)
    assert out["summary"]["studies_scanned"] == 1
    assert out["summary"]["das"]["public+link"] == 1
    assert out["summary"]["cas"]["public+link"] == 1
    assert out["summary"]["repo_link_present"] == 1
    assert out["run_metadata"]["missing_extractions"] == []


def test_run_reports_missing_extraction(tmp_path: Path):
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    out = open_science.run([RECORD], extracted, drop_missing=True)
    assert out["results"] == []
    assert out["run_metadata"]["missing_extractions"] == ["W1"]


def test_render_report_structure():
    out = {
        "run_metadata": {"run_date_utc": "2024-06-01T00:00:00S", "missing_extractions": []},
        "summary": {
            "studies_scanned": 1,
            "das": {"public+link": 1, "request-only": 0, "statement-only": 0, "explicitly-unavailable": 0, "not-stated": 0},
            "cas": {"public+link": 0, "request-only": 0, "statement-only": 1, "explicitly-unavailable": 0, "not-stated": 0},
            "both_public_link": 0,
            "any_das_or_cas_statement": 1,
            "repo_link_present": 1,
        },
        "results": [
            {
                "workspace_id": "W1",
                "title": "UAV weed detection",
                "year": 2023,
                "das": "public+link",
                "cas": "statement-only",
                "data_signals": [],
                "code_signals": [],
                "repo_links": [{"url": "https://github.com/user/data", "snippet": "available at this repo"}],
            }
        ],
    }
    md = open_science.render_report(out)
    assert "| public+link | 1 | 0 |" in md


def test_data_patterns_importable():
    assert len(DATA_PATTERNS) >= 10
