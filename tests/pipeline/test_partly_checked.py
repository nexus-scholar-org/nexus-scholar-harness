"""H-quota-hang review F3: "Finish preparing" checks only the records left, and only when that is safe.

``coordinator._partly_checked`` decides whether an ``INCOMPLETE`` verification
can be finished from ``verified.json`` and ``literature/verification_checks.json``
(checking only the records not fully checked) or must run again from the
saved records as before. These tests pin the fallbacks: a stale, mismatched,
missing or garbled checks file, a quarantine file, a marker that did not end
``INCOMPLETE`` or names another run, all give ``({}, None)``.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from scholar_harness.pipeline import coordinator, harvest_marker
from scholar_harness.pipeline.verification import CHECKS_FILENAME, CHECKS_SCHEMA
from scholar_harness.verification_identity import QUARANTINE_FILENAME
from scholar_search.models import Document, ExternalIds


def _doc(i: int) -> dict:
    return asdict(Document(
        title=f"Weed mapping study {i}", year=2024, provider="openalex", provider_id=f"W{i}",
        external_ids=ExternalIds(doi=f"10.1/w.{i}"), workspace_id=f"SCI-{i:06d}",
    ))


def _row(i: int, not_done: list[str]) -> dict:
    return {
        "position": i, "workspace_id": f"SCI-{i:06d}", "code": "NOT_CHECKED" if "verification" in not_done else "VERIFIED",
        "verified": "verification" not in not_done, "not_done": not_done,
        "reason": "PROVIDER_QUOTA_EXHAUSTED" if not_done else None, "status": "",
    }


def _incomplete_run(tmp_path: Path) -> tuple[Path, Path]:
    """An INCOMPLETE run_001: four records in verified.json, the last two not fully checked."""
    lit = tmp_path / "literature"
    run = lit / "search_runs" / "run_001"
    run.mkdir(parents=True)
    harvest_marker.start(run)
    harvest_marker.record_stage(run, "deduplication", "DONE")
    harvest_marker.record_stage(run, "hydration", "DONE")
    harvest_marker.incomplete(
        run, "PARTIAL", unchecked=2, unverified=1, unenriched=1, records=4,
        reason="PROVIDER_QUOTA_EXHAUSTED", paused=[], message="m",
    )
    (lit / "verified.json").write_text(json.dumps([_doc(i) for i in range(4)]), encoding="utf-8")
    rows = [_row(0, []), _row(1, []), _row(2, ["verification"]), _row(3, ["enrichment"])]
    (lit / CHECKS_FILENAME).write_text(json.dumps({"schema": CHECKS_SCHEMA, "rows": rows}), encoding="utf-8")
    return lit, run


def _decide(lit: Path, run: Path):
    return coordinator._partly_checked(lit, run, harvest_marker.read(run))


def test_an_incomplete_run_keeps_its_fully_checked_rows_and_rechecks_the_rest(tmp_path):
    lit, run = _incomplete_run(tmp_path)
    keep, documents = _decide(lit, run)
    assert sorted(keep) == ["SCI-000000", "SCI-000001"]
    assert [d.workspace_id for d in documents] == [f"SCI-{i:06d}" for i in range(4)]


def _rewrite_checks(lit: Path, change) -> None:
    data = json.loads((lit / CHECKS_FILENAME).read_text(encoding="utf-8"))
    change(data)
    (lit / CHECKS_FILENAME).write_text(json.dumps(data), encoding="utf-8")


@pytest.mark.parametrize("spoil", [
    "rows_reordered", "row_missing", "row_extra", "other_schema", "garbled", "missing", "duplicate_id",
    "quarantine", "marker_done", "marker_other_run", "verified_missing",
])
def test_anything_stale_or_mismatched_falls_back_to_the_full_preparation(tmp_path, spoil):
    lit, run = _incomplete_run(tmp_path)
    if spoil == "rows_reordered":
        _rewrite_checks(lit, lambda d: d["rows"].reverse())
    elif spoil == "row_missing":
        _rewrite_checks(lit, lambda d: d["rows"].pop())
    elif spoil == "row_extra":
        _rewrite_checks(lit, lambda d: d["rows"].append(_row(4, [])))
    elif spoil == "other_schema":
        _rewrite_checks(lit, lambda d: d.update(schema="nexus.verification-checks.v0"))
    elif spoil == "garbled":
        (lit / CHECKS_FILENAME).write_text("{not json", encoding="utf-8")
    elif spoil == "missing":
        (lit / CHECKS_FILENAME).unlink()
    elif spoil == "duplicate_id":
        docs = [_doc(0), _doc(0), _doc(2), _doc(3)]
        (lit / "verified.json").write_text(json.dumps(docs), encoding="utf-8")
        _rewrite_checks(lit, lambda d: d["rows"].__setitem__(1, _row(0, [])))
    elif spoil == "quarantine":
        (lit / QUARANTINE_FILENAME).write_text("[]", encoding="utf-8")
    elif spoil == "marker_done":
        harvest_marker.complete(run, "SUCCESS")
    elif spoil == "marker_other_run":
        marker = harvest_marker.read(run)
        marker["verified_run"] = "run_000"
        (run / harvest_marker.MARKER_NAME).write_text(json.dumps(marker), encoding="utf-8")
    elif spoil == "verified_missing":
        (lit / "verified.json").unlink()
    assert _decide(lit, run) == ({}, None)
