"""M3i-harvest-robustness: the stage marker of a harvest (``search_runs/run_NNN/pipeline.json``).

The marker is a run record written by the pipeline coordinator; these tests
drive the module alone, on scratch folders, and the coordinator's own use of
it through stage doubles. Nothing reaches the network.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scholar_harness.pipeline import coordinator, harvest_marker
from scholar_harness.pipeline import discovery as disc


def _run(tmp_path: Path, number: int = 1, *, published: bool = True, raw: bool = True) -> tuple[Path, Path]:
    lit = tmp_path / "literature"
    run = lit / "search_runs" / f"run_{number:03d}"
    run.mkdir(parents=True)
    (run / "legs.json").write_text(json.dumps({"run": run.name, "raw_published": published, "legs": []}), encoding="utf-8")
    if raw:
        (run / "raw.json").write_text("[]", encoding="utf-8")
    return lit, run


def _view(lit: Path, run: Path, **options) -> dict:
    return harvest_marker.preparation_view(lit, run, **{"published": True, "newest_published": True, **options})


def test_a_new_marker_has_no_stage_and_no_end(tmp_path):
    lit, run = _run(tmp_path)
    harvest_marker.start(run)
    marker = harvest_marker.read(run)
    assert marker == {
        "schema": "nexus.harvest-pipeline.v1", "run": "run_001", "stages": {}, "ended": None,
        "verified_run": None, "resumed": [],
    }
    assert harvest_marker.first_unfinished(marker) == "deduplication"
    view = _view(lit, run)
    assert view["state"] == "interrupted" and view["stage"] == "deduplication" and view["can_finish"] is True
    assert _view(lit, run, job_running=True)["state"] == "running"


def test_stages_are_recorded_in_order_and_the_end_names_the_run(tmp_path):
    lit, run = _run(tmp_path)
    harvest_marker.start(run)
    harvest_marker.record_stage(run, "deduplication", "DONE")
    assert harvest_marker.first_unfinished(harvest_marker.read(run)) == "hydration"
    harvest_marker.record_stage(run, "hydration", "DONE")
    assert _view(lit, run, job_running=True) == {
        **_view(lit, run, job_running=True), "state": "running", "stage": "verification",
    }
    (lit / "verified.json").write_text("[]", encoding="utf-8")
    harvest_marker.complete(run, "PARTIAL")
    marker = harvest_marker.read(run)
    assert list(marker["stages"]) == ["deduplication", "hydration", "verification"]
    assert marker["stages"]["verification"]["status"] == "PARTIAL"
    assert marker["ended"]["status"] == "DONE" and marker["verified_run"] == "run_001"
    view = _view(lit, run)
    assert view["state"] == "ready" and view["stage"] is None and view["can_finish"] is False
    assert [p.name for p in run.iterdir() if ".tmp" in p.name] == []


def test_a_failure_and_a_stop_name_their_stage(tmp_path):
    lit, run = _run(tmp_path)
    harvest_marker.start(run)
    harvest_marker.record_stage(run, "deduplication", "DONE")
    harvest_marker.end(run, harvest_marker.FAILED, stage="hydration", message="TimeoutError: slow")
    view = _view(lit, run)
    assert (view["state"], view["stage"], view["message"], view["can_finish"]) == ("failed", "hydration", "TimeoutError: slow", True)
    harvest_marker.end(run, harvest_marker.STOPPED, stage="hydration")
    view = _view(lit, run)
    assert (view["state"], view["stage"], view["message"]) == ("stopped", "hydration", None)
    # A frozen corpus, or records that are gone, leave nothing to finish, and the view says which.
    assert view["cannot_finish"] is None
    frozen = _view(lit, run, frozen=True)
    assert (frozen["can_finish"], frozen["cannot_finish"]) == (False, "corpus_accepted")
    (run / "raw.json").unlink()
    gone = _view(lit, run)
    assert (gone["can_finish"], gone["cannot_finish"]) == (False, "records_missing")


def test_a_later_attempt_keeps_the_earlier_stages_and_says_it_resumed(tmp_path):
    _lit, run = _run(tmp_path)
    harvest_marker.start(run)
    harvest_marker.record_stage(run, "deduplication", "DONE")
    harvest_marker.record_stage(run, "hydration", "DONE")
    harvest_marker.end(run, harvest_marker.FAILED, stage="verification", message="boom")
    harvest_marker.start(run, from_stage="hydration")
    marker = harvest_marker.read(run)
    assert list(marker["stages"]) == ["deduplication"] and marker["ended"] is None
    assert [r["from_stage"] for r in marker["resumed"]] == ["hydration"]
    harvest_marker.start(run, from_stage="deduplication")
    marker = harvest_marker.read(run)
    assert marker["stages"] == {} and [r["from_stage"] for r in marker["resumed"]] == ["hydration", "deduplication"]


def test_a_run_without_a_marker_is_not_guessed(tmp_path):
    lit, run = _run(tmp_path)
    view = _view(lit, run)
    assert (view["state"], view["stage"], view["marker"], view["can_finish"]) == ("interrupted", None, False, True)
    (lit / "verified.json").write_text("[]", encoding="utf-8")
    view = _view(lit, run)
    assert (view["state"], view["marker"], view["can_finish"]) == ("ready", False, False)
    assert harvest_marker.pending_preparation(tmp_path) is None


def test_a_done_marker_without_its_verified_json_is_not_ready(tmp_path):
    lit, run = _run(tmp_path)
    harvest_marker.start(run)
    harvest_marker.complete(run, "SUCCESS")
    view = _view(lit, run)
    assert (view["state"], view["stage"]) == ("interrupted", "verification")


def test_an_unreadable_marker_reads_as_interrupted_at_an_unknown_stage(tmp_path):
    lit, run = _run(tmp_path)
    (run / "pipeline.json").write_text("{not json", encoding="utf-8")
    (lit / "verified.json").write_text("[]", encoding="utf-8")
    view = _view(lit, run)
    assert (view["state"], view["stage"], view["marker"]) == ("interrupted", None, True)


def test_unpublished_and_superseded_runs_have_nothing_to_finish(tmp_path):
    lit, run = _run(tmp_path, published=False)
    assert _view(lit, run, published=False)["state"] == "none"
    assert harvest_marker.corpus_run_dir(lit) is None and harvest_marker.pending_preparation(tmp_path) is None
    _lit, second = _run(tmp_path, 2)
    assert harvest_marker.corpus_run_dir(lit) == second
    view = harvest_marker.preparation_view(lit, run, published=True, newest_published=False)
    assert view["state"] == "superseded" and view["can_finish"] is False


def test_pending_preparation_names_the_corpus_run(tmp_path):
    lit, _first = _run(tmp_path, 1)
    (lit / "verified.json").write_text("[]", encoding="utf-8")
    _lit, second = _run(tmp_path, 2)
    harvest_marker.start(second)
    pending = harvest_marker.pending_preparation(tmp_path)
    assert pending["run"] == "run_002" and pending["state"] == "interrupted" and pending["stage"] == "deduplication"
    harvest_marker.record_stage(second, "deduplication", "DONE")
    harvest_marker.record_stage(second, "hydration", "DONE")
    harvest_marker.complete(second, "SUCCESS")
    assert harvest_marker.pending_preparation(tmp_path) is None


def test_the_writers_do_nothing_without_a_run_folder(tmp_path):
    harvest_marker.start(None)
    harvest_marker.record_stage(None, "deduplication", "DONE")
    harvest_marker.complete(tmp_path / "missing", "SUCCESS")
    harvest_marker.end(None, harvest_marker.FAILED, stage="hydration")
    assert harvest_marker.read(None) is None and not (tmp_path / "missing").exists()


def test_saved_records_that_are_not_a_list_are_refused(tmp_path):
    path = tmp_path / "raw.json"
    path.write_text(json.dumps({"records": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="not a list"):
        harvest_marker.load_saved_documents(path)


# --------------------------------------------------------------------------- the coordinator's use of it


def _doubles(monkeypatch, tmp_path: Path, *, fail_in: str | None = None):
    """Stage doubles: a search that archives a real run folder, and three counted later stages."""
    ws = tmp_path / "ws"
    (ws / "literature").mkdir(parents=True)
    golden = Path(__file__).resolve().parents[2] / "workspaces" / "golden-uav-30" / "protocol.json"
    (ws / "protocol.json").write_text(golden.read_text(encoding="utf-8"), encoding="utf-8")
    calls: list[str] = []

    async def search(**kwargs):
        run_name, _files = disc._archive_search_run(
            ws / "literature", legs=[], query=SimpleNamespace(id="Q", text="q", year_min=None, year_max=None),
            status="SUCCESS", payload="[]", corpus_published=True,
        )
        return SimpleNamespace(
            documents=[], count=0, status="SUCCESS", reason="", published=True, search_run=run_name,
            cancelled=False, provider_errors={},
        )

    def dedup(**kwargs):
        calls.append("deduplication")
        if fail_in == "deduplication":
            raise RuntimeError("dedup broke")
        return SimpleNamespace(representatives=[], unique=0, duplicates_removed=0)

    async def hydrate(**kwargs):
        calls.append("hydration")
        if fail_in == "hydration":
            raise RuntimeError("hydration broke")
        return SimpleNamespace(documents=[])

    async def verify(**kwargs):
        calls.append("verification")
        (ws / "literature" / "verified.json").write_text("[]", encoding="utf-8")
        return SimpleNamespace(documents=[], status="SUCCESS", verified=0, refused=0, preserved=0,
                               bridge_restored=0, refusal_reasons={}, quarantine=None)

    monkeypatch.setattr(coordinator, "run_discovery", search)
    monkeypatch.setattr(coordinator, "run_deduplication", dedup)
    monkeypatch.setattr(coordinator, "run_hydration", hydrate)
    monkeypatch.setattr(coordinator, "run_verification", verify)
    return ws, calls


def _pipeline(ws: Path, **options) -> dict:
    return asyncio.run(coordinator.run_pipeline(
        workspace_dir=ws, freeze_corpus=False, **options,
    ))


def test_the_coordinator_marks_each_stage_and_the_end(monkeypatch, tmp_path):
    ws, calls = _doubles(monkeypatch, tmp_path)
    seen: list[tuple[str, list[str]]] = []
    run = ws / "literature" / "search_runs" / "run_001"
    results = _pipeline(ws, stage_callback=lambda name, status, detail: seen.append(
        (name, list((harvest_marker.read(run) or {}).get("stages", {})))
    ))
    assert results["status"] == "PENDING_CORPUS_ACCEPT" and calls == ["deduplication", "hydration", "verification"]
    # The marker is written before the stage is announced.
    assert seen[1:4] == [
        ("deduplication", ["deduplication"]),
        ("hydration", ["deduplication", "hydration"]),
        ("verification", ["deduplication", "hydration", "verification"]),
    ]
    marker = harvest_marker.read(run)
    assert marker["ended"]["status"] == "DONE" and marker["verified_run"] == "run_001"


def test_a_stage_error_ends_the_marker_and_still_propagates(monkeypatch, tmp_path):
    ws, calls = _doubles(monkeypatch, tmp_path, fail_in="hydration")
    with pytest.raises(RuntimeError, match="hydration broke"):
        _pipeline(ws)
    assert calls == ["deduplication", "hydration"]
    marker = harvest_marker.read(ws / "literature" / "search_runs" / "run_001")
    assert list(marker["stages"]) == ["deduplication"]
    assert marker["ended"]["status"] == "FAILED" and marker["ended"]["stage"] == "hydration"
    assert "hydration broke" in marker["ended"]["message"]
    journal = [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [e["action"] for e in journal] == ["PIPELINE_RUN_ABORTED"] and journal[0]["status"] == "FAILED"


@pytest.mark.parametrize(("stop_after", "expected_calls", "stopped_before"), [
    (0, [], "deduplication"),
    (1, ["deduplication"], "hydration"),
    (2, ["deduplication", "hydration"], "verification"),
])
def test_the_stop_is_read_before_each_stage(monkeypatch, tmp_path, stop_after, expected_calls, stopped_before):
    ws, calls = _doubles(monkeypatch, tmp_path)
    results = _pipeline(ws, should_stop=lambda: len(calls) >= stop_after)
    assert calls == expected_calls
    assert results["status"] == "CANCELLED" and results["stopped_before"] == stopped_before
    assert results["stages"]["verification"]["status"] == "SKIPPED"
    marker = harvest_marker.read(ws / "literature" / "search_runs" / "run_001")
    assert marker["ended"]["status"] == "STOPPED" and marker["ended"]["stage"] == stopped_before
    assert not (ws / "literature" / "verified.json").exists()


def test_a_stop_during_the_last_stage_lets_it_end(monkeypatch, tmp_path):
    """Verification is never interrupted: a stop that arrives while it runs changes nothing."""
    ws, calls = _doubles(monkeypatch, tmp_path)
    results = _pipeline(ws, should_stop=lambda: len(calls) >= 3)
    assert results["status"] == "PENDING_CORPUS_ACCEPT"
    assert harvest_marker.read(ws / "literature" / "search_runs" / "run_001")["ended"]["status"] == "DONE"


def test_finishing_refuses_a_run_with_nothing_to_finish(monkeypatch, tmp_path):
    ws, _calls = _doubles(monkeypatch, tmp_path)
    _pipeline(ws)
    refusal = coordinator.preparation_refusal(ws, "run_001")
    assert refusal is not None and refusal.reason == "already_prepared"
    with pytest.raises(coordinator.PreparationRefused):
        asyncio.run(coordinator.finish_harvest_preparation(workspace_dir=ws, run="run_001"))
    assert coordinator.preparation_refusal(ws, "run_007").reason == "not_published"


def test_the_marker_is_written_when_the_search_is_published(tmp_path):
    """Review finding 1: the marker exists from the moment the run is published.

    Otherwise a process that died between the run's ``legs.json`` and the first
    stage would leave a published run without a marker, which reads as a run
    made by an earlier version: ready, with an earlier run's ``verified.json``.
    """
    from scholar_harness.corpus_accept import AcceptCorpusRefused

    lit = tmp_path / "literature"
    lit.mkdir()
    (lit / "verified.json").write_text("[]", encoding="utf-8")  # an earlier run's works
    query = SimpleNamespace(id="Q", text="q", year_min=None, year_max=None)
    name, _files = disc._archive_search_run(lit, legs=[], query=query, status="SUCCESS", payload="[]", corpus_published=True)
    marker = harvest_marker.read(lit / "search_runs" / name)
    assert marker is not None and marker["run"] == name and marker["ended"] is None and marker["resumed"] == []
    pending = harvest_marker.pending_preparation(tmp_path)
    assert (pending["run"], pending["state"], pending["stage"]) == (name, "interrupted", "deduplication")
    with pytest.raises(AcceptCorpusRefused) as caught:
        coordinator.accept_discovery_corpus(tmp_path)
    assert caught.value.code == "PREPARATION_UNFINISHED"

    # A search that was stopped keeps its records and is not the corpus: no marker.
    kept, _files = disc._archive_search_run(lit, legs=[], query=query, status="PARTIAL", payload="[]", corpus_published=False)
    assert harvest_marker.read(lit / "search_runs" / kept) is None
    assert harvest_marker.pending_preparation(tmp_path)["run"] == name


def test_a_new_run_has_no_resumed_entry_when_the_coordinator_takes_it_over(monkeypatch, tmp_path):
    ws, _calls = _doubles(monkeypatch, tmp_path)
    _pipeline(ws)
    assert harvest_marker.read(ws / "literature" / "search_runs" / "run_001")["resumed"] == []
