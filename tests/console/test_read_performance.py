"""H-screening-read-performance: the engine reads once and keeps what it computed.

On a generated workspace of the sensor-stress review's size (54 batches, 1,062
decided records, 1,100 events; ``_sensor_stress.py``) the read routes open few
files (DoD 1 and 8: a count of files opened, never a time limit), the store
kept between requests never hides a change (DoD 3), and an accepted corpus is
not de-duplicated again (DoD 4).
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import pytest
from _sensor_stress import SCREENER, WS_ID, build
from fastapi.testclient import TestClient

from scholar_harness.console import create_app
from scholar_harness.screening import events as ev

pytestmark = pytest.mark.slow

DESKTOP = "desktop-token"
MAX_FILES = 150


class _Opens:
    """Counts the files opened under one folder (an audit hook: every ``open`` of the process)."""

    root: str | None = None
    paths: list[str] = []


def _hook(event: str, args: tuple) -> None:
    if event == "open" and _Opens.root is not None and args and isinstance(args[0], str | bytes | os.PathLike):
        path = os.fsdecode(args[0]).replace("\\", "/").lower()
        if path.startswith(_Opens.root):
            _Opens.paths.append(path)


sys.addaudithook(_hook)


def _opened(ws: Path, call) -> tuple[object, list[str]]:
    _Opens.paths = []
    _Opens.root = str(ws.resolve()).replace("\\", "/").lower() + "/"
    try:
        result = call()
    finally:
        _Opens.root = None
    return result, list(_Opens.paths)


@pytest.fixture(scope="session")
def sensor_stress(tmp_path_factory) -> Path:
    return build(tmp_path_factory.mktemp("sensor-stress"))


@pytest.fixture
def ws(sensor_stress: Path, tmp_path: Path) -> Path:
    """A fresh copy per test: another path, so nothing a test before kept applies."""
    root = tmp_path / "root"
    root.mkdir()
    return Path(shutil.copytree(sensor_stress, root / "ws"))


def _client(ws: Path) -> TestClient:
    return TestClient(
        create_app(ws, token=DESKTOP, workspaces_root=ws.parent),
        base_url="http://127.0.0.1",
        headers={"Authorization": f"Bearer {DESKTOP}"},
    )


# --- DoD 1 and 8: files opened per call ------------------------------------------------------


@pytest.mark.parametrize(
    "route",
    ["/api/v1/ui/publication-status", "/api/v1/review/next-step", "/api/v1/screening/prisma/preview"],
)
def test_a_read_route_opens_at_most_150_files_on_the_sensor_stress_fixture(ws, route):
    client = _client(ws)
    client.get("/api/v1/screening/settings")  # the app's own first reads
    response, opened = _opened(ws, lambda: client.get(route))
    assert response.status_code == 200, response.text
    assert len(opened) <= MAX_FILES, (len(opened), len(set(opened)))
    # A second call answers the same, from what the first kept.
    again, reopened = _opened(ws, lambda: client.get(route))
    assert _without_clock(again.json()) == _without_clock(response.json())
    assert len(reopened) <= len(opened)


def _without_clock(body: dict) -> dict:
    return {k: v for k, v in body.items() if k != "computed_at"}


def test_the_fixture_is_the_sensor_stress_size_and_published(ws):
    context = ev.load_context(ws)
    events = ev.read_events(ws)
    assert len(context.batches) == 54
    assert len(context.study_batch) == 1062
    assert len(events) == 1100
    status = _client(ws).get("/api/v1/ui/publication-status").json()
    assert status["status"] == "CURRENT", status


# --- DoD 3: the store never hides a change ------------------------------------------------------


def _change_one_decision(ws: Path, *, project: bool) -> str:
    """Intake one decision that supersedes a published one (as the decisions route stores it)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_rp_events_helpers", Path(__file__).resolve().parents[1] / "test_screening_events.py")
    se = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(se)
    included = json.loads((ws / "literature" / "included.json").read_text(encoding="utf-8"))
    study = included[0]["screening"]["workspace_id"]
    head = ev.winning_event(ev.read_events(ws), study, SCREENER)
    event = se._event(ws, study, "EXCLUDE", decided_at="2026-11-21T12:00:00.000Z")
    event["screener_id"] = SCREENER
    event["supersedes"] = head["event_id"]
    assert se._intake(ws, [event]) == ["accepted"]
    if project:
        index = ev.load_context(ws).study_batch[study]
        ev.write_projection(ws, index, SCREENER, workspace_id=WS_ID)
    return study


@pytest.mark.parametrize("project", [True, False], ids=["projected", "not-projected"])
def test_a_decision_changed_between_two_calls_is_reported_by_the_second(ws, project):
    client = _client(ws)
    assert client.get("/api/v1/ui/publication-status").json()["status"] == "CURRENT"
    assert client.get("/api/v1/review/next-step").json()["state"] == "PUBLISHED"
    preview = client.get("/api/v1/screening/prisma/preview").json()
    assert {c["name"]: c["ok"] for c in preview["checks"]}["projections_current"] is True

    _change_one_decision(ws, project=project)

    status = client.get("/api/v1/ui/publication-status").json()
    assert status["status"] == "STALE", status
    assert client.get("/api/v1/review/next-step").json()["state"] == "PUBLISHED_STALE"
    preview = client.get("/api/v1/screening/prisma/preview").json()
    assert {c["name"]: c["ok"] for c in preview["checks"]}["projections_current"] is project


def _decisions_file(ws: Path, index: int = 7) -> Path:
    return ws / "literature" / "screening" / f"batch_{index:03d}_decisions.json"


def test_a_decision_file_edited_by_hand_is_reported_stale(ws):
    client = _client(ws)
    assert client.get("/api/v1/ui/publication-status").json()["status"] == "CURRENT"
    path = _decisions_file(ws)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["decisions"][0]["screening_reasoning"] = "Edited by hand after publication, a longer reason."
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    status = client.get("/api/v1/ui/publication-status").json()
    assert status["status"] == "STALE", status
    preview = client.get("/api/v1/screening/prisma/preview").json()
    check = {c["name"]: c for c in preview["checks"]}["projections_current"]
    assert check["ok"] is False and "007" in check["detail"]
    assert client.get("/api/v1/review/next-step").json()["state"] == "PUBLISHED_STALE"


def test_a_same_size_hand_edit_with_a_new_modification_time_is_reported_stale(ws):
    client = _client(ws)
    assert client.get("/api/v1/ui/publication-status").json()["status"] == "CURRENT"
    path = _decisions_file(ws)
    raw = path.read_bytes()
    edited = raw.replace(b'"decision": "EXCLUDE"', b'"decision": "INCLUDE"', 1)
    if edited == raw:
        edited = raw.replace(b'"decision": "INCLUDE"', b'"decision": "EXCLUDE"', 1)
    assert len(edited) == len(raw) and edited != raw
    stat = path.stat()
    path.write_bytes(edited)
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 2_000_000_000))
    assert client.get("/api/v1/ui/publication-status").json()["status"] == "STALE"


def test_approve_and_publish_recompute_from_disk_even_where_the_store_cannot_see_the_edit(ws):
    """Question 3's known cost, and its limit: a same-size edit that keeps the modification time
    is not seen by a display route, but the publication's own checks read the disk."""
    from scholar_harness.screening.collector import cmd_collect

    client = _client(ws)
    assert client.get("/api/v1/ui/publication-status").json()["status"] == "CURRENT"
    path = _decisions_file(ws)
    raw = path.read_bytes()
    edited = raw.replace(b'"decision": "EXCLUDE"', b'"decision": "INCLUDE"', 1)
    assert len(edited) == len(raw) and edited != raw
    stat = path.stat()
    path.write_bytes(edited)
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))

    assert ev.stale_projections(ws) == [7]
    assert not ev.projection_is_current(ws, 7, path)
    with pytest.raises(Exception) as refused:
        cmd_collect(ws)
    assert ev.PROJECTION_STALE in str(refused.value) or "007" in str(refused.value) or "7" in str(refused.value)


# --- DoD 4: an accepted corpus is read, not rebuilt --------------------------------------------


class _CountDedup:
    calls = 0


@pytest.fixture
def counted_dedup(monkeypatch):
    from scholar_search import dedup

    real = dedup.Deduplicator.deduplicate
    _CountDedup.calls = 0

    def counting(self, *args, **kwargs):
        _CountDedup.calls += 1
        return real(self, *args, **kwargs)

    monkeypatch.setattr(dedup.Deduplicator, "deduplicate", counting)
    return _CountDedup


def test_the_corpus_of_an_accepted_snapshot_is_not_deduplicated_again(ws, counted_dedup):
    from scholar_harness.corpus_accept import preview_staged

    body = _client(ws).get("/api/v1/screening/corpus").json()
    assert counted_dedup.calls == 0
    assert body["state"] == "ACCEPTED"
    # The answer is today's: the counts the staged exports give.
    full = preview_staged(ws)
    assert body["preview"] == {k: full[k] for k in ("identified", "duplicates", "unique_studies")}
    assert body["preview"] == {"identified": 2181, "duplicates": 1119, "unique_studies": 1062}
    assert body["sources"] == full["sources"] and body["databases"] == full["databases"]


def test_a_staged_corpus_not_yet_accepted_is_still_deduplicated(tmp_path, counted_dedup):
    from _sensor_stress import PROTOCOL

    from scholar_harness.corpus_accept import stage_ris_source

    ws = tmp_path / "ws"
    (ws / "literature").mkdir(parents=True)
    (ws / "audit").mkdir()
    (ws / "audit" / "journal.jsonl").write_text("", encoding="utf-8")
    (ws / "project.json").write_text(json.dumps({"project_id": "p", "registered_workspace_id": WS_ID}), encoding="utf-8")
    (ws / "protocol.json").write_text(PROTOCOL.read_text(encoding="utf-8"), encoding="utf-8")
    ris = "TY  - JOUR\nTI  - Strain sensing in bridges\nPY  - 2024\nDO  - 10.1/a\nER  - \n"
    stage_ris_source(ws, "Scopus", ris.encode(), file_name="s.ris")
    stage_ris_source(ws, "IEEE", ris.replace("10.1/a", "10.1/A").encode(), file_name="i.ris")
    counted_dedup.calls = 0
    body = _client(ws).get("/api/v1/screening/corpus").json()
    assert body["state"] == "STAGED"
    assert counted_dedup.calls >= 1
    assert body["preview"] == {"identified": 2, "duplicates": 1, "unique_studies": 1}


def test_a_staged_export_changed_on_disk_after_acceptance_is_parsed_again(ws, counted_dedup):
    """The accepted fast path holds only while the staged files are the ones accepted."""
    from scholar_harness.corpus_accept import preview_staged

    sources = json.loads((ws / "literature" / "raw" / "ris" / "sources.json").read_text(encoding="utf-8"))["sources"]
    stored = ws / sources[0]["stored_as"]
    stored.write_bytes(stored.read_bytes().replace(b"ER  - \n", b"ER  - \n", 1) + b"TY  - JOUR\nTI  - One more record\nER  - \n")
    body = _client(ws).get("/api/v1/screening/corpus").json()
    assert counted_dedup.calls >= 1
    full = preview_staged(ws)
    assert body["preview"] == {k: full[k] for k in ("identified", "duplicates", "unique_studies")}
    assert body["preview"]["identified"] == 2182
