"""Hermetic tests for the UI-07 paged corpus reads.

`GET /api/v1/ui/corpus/{kind}` replaces the screen's direct download of
`literature/included.json` / `excluded.json` (the excluded set is ~27 MB on the
pilot workspace). The contract under test:

  - one typed projection per stored record, never the raw dump shape;
  - filtering happens server-side over the whole stored set, before paging;
  - `total` is the matched count, `corpus_total` the stored count;
  - a missing corpus file is an explicit `missing` entry, not a transport error;
  - the read is pure: bytes and mtime are unchanged after the call;
  - caller-minted identities and out-of-range paging are refused.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from scholar_harness.console import create_app

INCLUDED = [
    {
        "workspace_id": "SCI-INC-001",
        "title": "UAV weed mapping with multispectral imagery",
        "year": 2024,
        "provider": "crossref",
        "doi": "10.0000/inc1",
        "abstract": "A precision agriculture study.",
        "screening": {
            "decision": "INCLUDE",
            "confidence": 0.9,
            "screening_reasoning": "matches the population",
            "matched_inclusion_criteria": ["INC-01"],
            "violated_exclusion_criteria": [],
        },
        "screening_provenance": {"lane": "mutual_include", "reason_code": "INC-01"},
    },
    {
        "workspace_id": "SCI-INC-002",
        "title": "Aerial survey replication",
        "year": 2022,
        "provider": "openalex",
        "doi": "10.0000/inc2",
        "abstract": None,
        "screening": {
            "decision": "INCLUDE",
            "confidence": "high",
            "matched_inclusion_criteria": [],
            "violated_exclusion_criteria": [],
        },
        "screening_provenance": {},
    },
]

EXCLUDED = [
    {
        "workspace_id": "SCI-EXC-001",
        "title": "Soil chemistry only",
        "year": 2019,
        "provider": "crossref",
        "doi": None,
        "abstract": "No UAV involved.",
        "screening": {
            "decision": "EXCLUDE",
            "confidence": 0.8,
            "screening_reasoning": "wrong intervention",
            "matched_inclusion_criteria": [],
            "violated_exclusion_criteria": ["EXC-02"],
        },
        "screening_provenance": {"lane": "mutual_exclude", "reason_code": "WRONG_TASK"},
    },
    {
        "workspace_id": "SCI-EXC-002",
        "title": "UAV review without an outcome",
        "year": 2021,
        "provider": "openalex",
        "doi": "10.0000/exc2",
        "abstract": "No measured yield.",
        "screening": {
            "decision": "EXCLUDE",
            "confidence": 0.7,
            "matched_inclusion_criteria": [],
            "violated_exclusion_criteria": ["EXC-03"],
        },
        "screening_provenance": {"lane": "third_lane", "reason_code": "NO_USABLE_ABSTRACT_NOT_RETRIEVED"},
    },
    {
        "workspace_id": "SCI-EXC-003",
        "title": "Duplicate record",
        "year": 2021,
        "provider": "arxiv",
        "doi": None,
        "abstract": "duplicate",
        "screening": {
            "decision": "EXCLUDE",
            "confidence": 0.99,
            "matched_inclusion_criteria": [],
            "violated_exclusion_criteria": [],
        },
        "screening_provenance": {"lane": "dedup"},
    },
]


def _make_ws(tmp: Path, *, write_files: bool = True) -> Path:
    ws = tmp / "ws"
    (ws / "literature").mkdir(parents=True)
    if write_files:
        (ws / "literature" / "included.json").write_text(
            json.dumps(INCLUDED), encoding="utf-8"
        )
        (ws / "literature" / "excluded.json").write_text(
            json.dumps(EXCLUDED), encoding="utf-8"
        )
    return ws


def test_corpus_page_projects_and_pages(tmp_path):
    ws = _make_ws(tmp_path)
    client = TestClient(create_app(ws))

    response = client.get("/api/v1/ui/corpus/included?limit=1&offset=0")
    assert response.status_code == 200
    page = response.json()
    assert page["shape"] == "ui07.corpus-page-v1"
    assert page["kind"] == "included"
    assert page["total"] == 2
    assert page["corpus_total"] == 2
    assert page["limit"] == 1
    assert page["offset"] == 0
    assert page["missing"] == []
    assert len(page["records"]) == 1

    record = page["records"][0]
    assert record["shape"] == "ui07.corpus-record-v1"
    assert record["workspace_id"] == "SCI-INC-001"
    assert record["decision"] == "INCLUDE"
    assert record["confidence"] == 0.9
    assert record["reason_code"] == "INC-01"
    assert record["criterion"] == "INC-01"
    assert record["lane"] == "mutual_include"

    second = client.get("/api/v1/ui/corpus/included?limit=1&offset=1").json()
    assert [r["workspace_id"] for r in second["records"]] == ["SCI-INC-002"]
    # A non-numeric confidence and an absent reason stay absent, never invented.
    assert second["records"][0]["confidence"] is None
    assert second["records"][0]["reason_code"] is None
    assert second["records"][0]["abstract"] is None


def test_corpus_filter_runs_before_pagination(tmp_path):
    ws = _make_ws(tmp_path)
    client = TestClient(create_app(ws))

    by_query = client.get("/api/v1/ui/corpus/excluded?q=YIELD").json()
    assert by_query["total"] == 1
    assert by_query["corpus_total"] == 3
    assert [r["workspace_id"] for r in by_query["records"]] == ["SCI-EXC-002"]

    by_reason = client.get("/api/v1/ui/corpus/excluded?reason=wrong_task").json()
    assert by_reason["total"] == 1
    assert [r["workspace_id"] for r in by_reason["records"]] == ["SCI-EXC-001"]

    by_criterion = client.get("/api/v1/ui/corpus/excluded?reason=EXC-03").json()
    assert [r["workspace_id"] for r in by_criterion["records"]] == ["SCI-EXC-002"]

    # Filter + page compose: one match filtered, then paged.
    page = client.get("/api/v1/ui/corpus/excluded?q=uav&limit=1&offset=1").json()
    assert page["total"] == 2
    assert len(page["records"]) == 1


def test_corpus_missing_file_is_an_explicit_missing_entry(tmp_path):
    ws = _make_ws(tmp_path, write_files=False)
    client = TestClient(create_app(ws))

    response = client.get("/api/v1/ui/corpus/excluded")
    assert response.status_code == 200
    page = response.json()
    assert page["total"] == 0
    assert page["corpus_total"] == 0
    assert page["records"] == []
    assert page["missing"] == [
        {"file": "literature/excluded.json", "reason": "CORPUS_MISSING"}
    ]


def test_corpus_refusals(tmp_path):
    ws = _make_ws(tmp_path)
    client = TestClient(create_app(ws))

    unknown = client.get("/api/v1/ui/corpus/other")
    assert unknown.status_code == 404
    assert unknown.json()["detail"]["code"] == "CORPUS_KIND_UNKNOWN"

    forged = client.get("/api/v1/ui/corpus/included?workspace_id=WSP-forged")
    assert forged.status_code == 422
    assert forged.json()["detail"]["code"] == "CALLER_IDENTITY_REFUSED"

    assert client.get("/api/v1/ui/corpus/included?limit=0").status_code == 422
    assert client.get("/api/v1/ui/corpus/included?limit=201").status_code == 422
    assert client.get("/api/v1/ui/corpus/included?offset=-1").status_code == 422


def test_corpus_read_is_pure(tmp_path):
    ws = _make_ws(tmp_path)
    path = ws / "literature" / "excluded.json"
    before = (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
    client = TestClient(create_app(ws))

    assert client.get("/api/v1/ui/corpus/excluded?q=uav").status_code == 200

    after = (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
    assert after == before
