"""M3i-harvest-robustness: the stages after a search are recorded, can be stopped and can be finished.

Offline, as ``test_discovery_api.py`` (whose doubles and helpers this file
loads): the databases are in-memory doubles run by the real engine, and the
abstract and verification clients are replaced. Nothing reaches the network.

The finding (strict acceptance run, 2026-11-13): a harvest returned 1,074
records and 1,050 works and the Hand-off said there was nothing to hand off.
One job runs search, deduplication, abstracts and verification; the run is
archived as published after the search, only verification writes
``literature/verified.json``, and nothing said the later stages had not ended.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import shutil
import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scholar_harness.console import create_app
from scholar_harness.pipeline import coordinator
from scholar_harness.pipeline import hydration as hyd_mod
from scholar_harness.pipeline import verification as ver_mod
from scholar_harness.workspace import catalog

_SPEC = importlib.util.spec_from_file_location(
    "_discovery_api_helpers", Path(__file__).resolve().parent / "test_discovery_api.py"
)
h = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(h)

env = h.env
BASE = h.BASE
ACCEPT = "/api/v1/screening/corpus/accept"


class _VerifierDown(h._PassthroughVerifier):
    async def process_batch(self, docs, verify=True, enrich=True):
        raise RuntimeError("verifier down")


def _hydrator_until(ready):
    """An abstracts double that ends only once ``ready()`` is true (no timing; a 30 s guard)."""

    class Held(h._PassthroughHydrator):
        async def hydrate_missing_abstracts(self, docs, batch_size=50):
            deadline = time.time() + 30
            while not ready() and time.time() < deadline:
                await asyncio.sleep(0.01)
            return await super().hydrate_missing_abstracts(docs, batch_size)

    return Held


def _stop_requested(client) -> bool:
    return any(job.cancel_requested for job in client.app.state.discovery_jobs.jobs.values())


def _run_dir(ws: Path, run: str = "run_001") -> Path:
    return ws / "literature" / "search_runs" / run


def _marker(ws: Path, run: str = "run_001") -> dict:
    return json.loads((_run_dir(ws, run) / "pipeline.json").read_text(encoding="utf-8"))


def _preparation(client, run: str = "run_001") -> dict:
    return client.get(f"{BASE}/runs/{run}").json()["preparation"]


def _finish(client, run: str = "run_001") -> tuple[dict, list[tuple[str, dict]]]:
    started = client.post(f"{BASE}/runs/{run}/prepare")
    assert started.status_code == 202, started.text
    job = started.json()["job"]
    events = h._events(client, job["job_id"])
    return client.get(f"{BASE}/jobs/{job['job_id']}").json()["job"], events


def _fail_verification_once(client, monkeypatch, body: dict | None = None) -> dict:
    """A harvest whose search ends and whose verification raises; the double is put back after."""
    monkeypatch.setattr(ver_mod, "DocumentVerifier", _VerifierDown)
    job, _ = h._run(client, body or {"providers": ["openalex", "crossref"]})
    monkeypatch.setattr(ver_mod, "DocumentVerifier", h._PassthroughVerifier)
    assert job["state"] == "failed" and job["error"]["code"] == "DISCOVERY_FAILED", job
    return job


# --------------------------------------------------------------------------- D1 the marker


def test_pipeline_marker_written_by_each_stage(env, monkeypatch):
    """The run's pipeline.json follows the stages: what a stage reads is what ended before it."""
    client, ws, _ = env
    seen: dict[str, dict] = {}

    class Hydrator(h._PassthroughHydrator):
        async def hydrate_missing_abstracts(self, docs, batch_size=50):
            seen["hydration"] = _marker(ws)
            return await super().hydrate_missing_abstracts(docs, batch_size)

    class Verifier(h._PassthroughVerifier):
        async def process_batch(self, docs, verify=True, enrich=True):
            seen["verification"] = _marker(ws)
            return await super().process_batch(docs, verify, enrich)

    monkeypatch.setattr(hyd_mod, "AbstractHydrator", Hydrator)
    monkeypatch.setattr(ver_mod, "DocumentVerifier", Verifier)
    job, _ = h._run(client, {"providers": ["openalex"]})
    assert job["state"] == "succeeded", job

    during_hydration, during_verification = seen["hydration"], seen["verification"]
    assert list(during_hydration["stages"]) == ["deduplication"] and during_hydration["ended"] is None
    assert list(during_verification["stages"]) == ["deduplication", "hydration"]
    assert during_verification["ended"] is None and during_verification["verified_run"] is None

    marker = _marker(ws)
    assert marker["schema"] == "nexus.harvest-pipeline.v1" and marker["run"] == "run_001"
    assert list(marker["stages"]) == ["deduplication", "hydration", "verification"]
    assert {s["status"] for s in marker["stages"].values()} == {"DONE", "SUCCESS"}
    assert all(s["at"] for s in marker["stages"].values())
    assert marker["ended"]["status"] == "DONE" and marker["verified_run"] == "run_001"
    # Written atomically: no temporary file is left beside it.
    assert sorted(p.name for p in _run_dir(ws).iterdir()) == ["legs.json", "pipeline.json", "raw.json", "search_report.md"]

    preparation = _preparation(client)
    # The public shape (packet "preparation"); the UI's fake engine carries the same keys.
    assert sorted(preparation) == [
        "can_finish", "cannot_finish", "ended_at", "job_id", "marker", "message", "stage", "stages", "state",
    ]
    assert preparation["state"] == "ready" and preparation["stage"] is None and preparation["marker"] is True
    assert preparation["can_finish"] is False
    assert client.get(f"{BASE}/runs").json()["runs"][0]["preparation"]["state"] == "ready"
    assert client.get(f"{BASE}/handoff").json()["preparation"]["state"] == "ready"


def test_a_stopped_search_has_nothing_to_prepare(env):
    """A search the researcher stopped is not published; its run says there is nothing to finish."""
    client, ws, providers = env
    providers.set("openalex", h.FakeProvider("openalex", [h._doc("openalex", i) for i in range(500)], delay=0.02))
    job_id = client.post(f"{BASE}/runs", json={"providers": ["openalex"]}).json()["job"]["job_id"]
    time.sleep(0.4)
    assert client.post(f"{BASE}/jobs/{job_id}/cancel").json()["job"]["state"] == "cancelled"
    assert not (_run_dir(ws) / "pipeline.json").exists()
    preparation = _preparation(client)
    assert preparation["state"] == "none" and preparation["can_finish"] is False
    refused = client.post(f"{BASE}/runs/run_001/prepare")
    assert refused.status_code == 409 and h._code(refused) == "PREPARATION_NOT_AVAILABLE"
    assert refused.json()["detail"]["details"]["reason"] == "not_published"


# --------------------------------------------------------------------------- D2 a failure after the search


def test_a_run_that_dies_after_search_says_so(env, monkeypatch):
    """(a), (b), (d): the search is published, verification fails, and the run and the hand-off say it."""
    client, ws, _ = env
    _fail_verification_once(client, monkeypatch)
    manifest = json.loads((_run_dir(ws) / "legs.json").read_text(encoding="utf-8"))
    assert manifest["raw_published"] is True  # (a) published after the search, as before
    assert not (ws / "literature" / "verified.json").exists()  # (b) only verification writes it

    marker = _marker(ws)
    assert list(marker["stages"]) == ["deduplication", "hydration"]
    assert marker["ended"]["status"] == "FAILED" and marker["ended"]["stage"] == "verification"
    assert "verifier down" in marker["ended"]["message"] and marker["verified_run"] is None

    for preparation in (
        _preparation(client),
        client.get(f"{BASE}/runs").json()["runs"][0]["preparation"],
        client.get(f"{BASE}/handoff").json()["preparation"],
    ):
        assert preparation["state"] == "failed" and preparation["stage"] == "verification"
        assert "verifier down" in preparation["message"] and preparation["can_finish"] is True
    aborted = [e for e in h._journal(ws) if e["action"] == "PIPELINE_RUN_ABORTED"]
    assert len(aborted) == 1 and "verification" in aborted[0]["description"] and "run_001" in aborted[0]["description"]
    assert aborted[0]["status"] == "FAILED"
    preparation = _preparation(client)
    assert preparation["cannot_finish"] is None


# --------------------------------------------------------------------------- D3 stop between stages


def test_a_stop_after_the_search_is_honoured_before_the_next_stage(env, monkeypatch):
    """(c): a stop that arrives while abstracts are added ends the job before verification."""
    client, ws, _ = env

    monkeypatch.setattr(hyd_mod, "AbstractHydrator", _hydrator_until(lambda: _stop_requested(client)))
    job_id = client.post(f"{BASE}/runs", json={"providers": ["openalex"]}).json()["job"]["job_id"]
    deadline = time.time() + 30
    while not (ws / "literature" / "deduped.json").exists() and time.time() < deadline:
        time.sleep(0.05)
    assert (ws / "literature" / "deduped.json").exists(), "the search and the deduplication did not end"

    cancelled = client.post(f"{BASE}/jobs/{job_id}/cancel")
    assert cancelled.status_code == 200 and cancelled.json()["job"]["state"] == "cancelled", cancelled.text
    result = cancelled.json()["job"]["result"]
    assert result["status"] == "CANCELLED" and result["run"] == "run_001"

    assert not (ws / "literature" / "verified.json").exists()
    marker = _marker(ws)
    assert list(marker["stages"]) == ["deduplication", "hydration"]
    assert marker["ended"]["status"] == "STOPPED" and marker["ended"]["stage"] == "verification"
    preparation = _preparation(client)
    assert preparation["state"] == "stopped" and preparation["stage"] == "verification" and preparation["can_finish"] is True
    stages = [d["stage"] for name, d in h._events(client, job_id) if name == "stage"]
    assert stages == ["discovery", "deduplication", "hydration"]
    actions = [e["action"] for e in h._journal(ws)]
    assert "PIPELINE_RUN_ABORTED" in actions and "PIPELINE_RUN_PAUSED_FOR_CORPUS_ACCEPT" not in actions
    # Review finding 5: a stopped run's row never reads as a success.
    stopped = next(e for e in h._journal(ws) if e["action"] == "PIPELINE_RUN_ABORTED")
    assert stopped["status"] == "PARTIAL" and "stopped by the researcher before verification" in stopped["description"]
    # The records are kept: the same run can be finished, and then accepted.
    job, _ = _finish(client)
    assert job["state"] == "succeeded", job
    assert client.post(ACCEPT).status_code == 200


# --------------------------------------------------------------------------- D4 finish without a search


def test_finish_preparing_resumes_from_the_marker_without_a_search(env, monkeypatch):
    client, ws, providers = env
    _fail_verification_once(client, monkeypatch)
    asked_before = {name: list(p.queries) for name, p in providers.by_name.items()}
    deduped_before = (ws / "literature" / "deduped.json").read_bytes()

    job, events = _finish(client)

    assert job["kind"] == "prepare" and job["state"] == "succeeded", job
    assert job["result"]["run"] == "run_001" and job["result"]["status"] == "PENDING_CORPUS_ACCEPT"
    assert job["result"]["resumed_from"] == "hydration"
    # Deduplication ended before the failure, so it is not run again; nothing is searched.
    assert [d["stage"] for name, d in events if name == "stage"] == ["hydration", "verification", "corpus_snapshot"]
    assert {name: list(p.queries) for name, p in providers.by_name.items()} == asked_before
    assert [p.name for p in (ws / "literature" / "search_runs").iterdir()] == ["run_001"]
    assert (ws / "literature" / "deduped.json").read_bytes() == deduped_before

    marker = _marker(ws)
    assert list(marker["stages"]) == ["deduplication", "hydration", "verification"]
    assert marker["ended"]["status"] == "DONE" and marker["verified_run"] == "run_001"
    assert [r["from_stage"] for r in marker["resumed"]] == ["hydration"]
    assert _preparation(client)["state"] == "ready"

    journal = h._journal(ws)
    resumed = [e for e in journal if e["action"] == "HARVEST_PREPARATION_RESUMED"]
    assert len(resumed) == 1 and "run_001" in resumed[0]["description"] and "hydration" in resumed[0]["description"]
    assert [e["action"] for e in journal].count("DISCOVERY_SEARCH") == 1
    assert journal[-1]["action"] == "PIPELINE_RUN_PAUSED_FOR_CORPUS_ACCEPT"

    handoff = client.get(f"{BASE}/handoff").json()
    assert handoff["corpus"]["state"] == "STAGED" and handoff["corpus"]["from_discovery"] is True
    assert handoff["run"] == "run_001" and sum(m["records"] for m in handoff["provider_mix"]) == 8
    accepted = client.post(ACCEPT)
    assert accepted.status_code == 200 and accepted.json()["accepted"]["studies"] == 8


def test_a_failed_deduplication_is_finished_from_the_saved_records(env, monkeypatch):
    client, ws, _ = env
    real = coordinator.run_deduplication

    def broken(**kwargs):
        raise RuntimeError("no room")

    monkeypatch.setattr(coordinator, "run_deduplication", broken)
    job, _ = h._run(client, {"providers": ["openalex"]})
    assert job["state"] == "failed", job
    monkeypatch.setattr(coordinator, "run_deduplication", real)
    preparation = _preparation(client)
    assert preparation["state"] == "failed" and preparation["stage"] == "deduplication"
    assert not (ws / "literature" / "deduped.json").exists()

    job, events = _finish(client)
    assert job["state"] == "succeeded" and job["result"]["resumed_from"] == "deduplication", job
    assert [d["stage"] for name, d in events if name == "stage"] == [
        "deduplication", "hydration", "verification", "corpus_snapshot",
    ]
    assert len(json.loads((ws / "literature" / "verified.json").read_text(encoding="utf-8"))) == 4


def _second_workspace(tmp_path: Path, name: str):
    root = tmp_path / "root"
    catalog.create(root, name)
    ws = root / name.lower().replace(" ", "-")
    shutil.copy2(h.GOLDEN_PROTOCOL, ws / "protocol.json")
    return ws, create_app(ws, token=h.TOKEN, workspaces_root=root)


def test_finished_preparation_equals_an_uninterrupted_run(env, tmp_path):
    """The same saved records give the same verified.json, byte for byte, with or without an interruption.

    The second workspace holds only the first run's search files (no marker, as
    a run made before the marker existed), so it is finished from ``raw.json``.
    """
    client, ws, providers = env
    providers.set("openalex", h.FakeProvider("openalex", [h._doc("openalex", i, doi=f"10.9/shared.{i}") for i in range(6)]))
    providers.set("crossref", h.FakeProvider("crossref", [
        h._doc("crossref", i, doi=f"10.9/shared.{i}", abstract=None, title=f"UAV weed mapping study openalex {i}")
        for i in range(3)
    ]))
    job, _ = h._run(client, {"providers": ["openalex", "crossref"]})
    assert job["state"] == "succeeded", job
    asked = {name: list(p.queries) for name, p in providers.by_name.items()}

    ws2, app2 = _second_workspace(tmp_path, "Review two")
    run2 = _run_dir(ws2)
    run2.mkdir(parents=True)
    for name in ("raw.json", "legs.json", "search_report.md"):
        shutil.copy2(_run_dir(ws) / name, run2 / name)
    with TestClient(app2, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {h.TOKEN}"}) as client2:
        before = _preparation(client2)
        assert before == {**before, "state": "interrupted", "stage": None, "marker": False, "can_finish": True}
        job2, _ = _finish(client2)
        assert job2["state"] == "succeeded" and job2["result"]["resumed_from"] == "deduplication", job2
        assert _preparation(client2)["state"] == "ready"

    for name in ("deduped.json", "verified.json"):
        assert (ws2 / "literature" / name).read_bytes() == (ws / "literature" / name).read_bytes(), name
    assert len(json.loads((ws / "literature" / "verified.json").read_text(encoding="utf-8"))) == 6
    assert {name: list(p.queries) for name, p in providers.by_name.items()} == asked  # no search for the second


# --------------------------------------------------------------------------- D5 after a restart


def test_after_a_restart_the_marker_answers(env, monkeypatch, tmp_path):
    """A new console has no job in memory; the run's state is read from its marker."""
    client, ws, _ = env
    failed = _fail_verification_once(client, monkeypatch, {"providers": ["openalex"]})
    app = create_app(ws, token=h.TOKEN, workspaces_root=ws.parent)
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {h.TOKEN}"}) as again:
        assert again.get(f"{BASE}/jobs/{failed['job_id']}").status_code == 404
        runs = again.get(f"{BASE}/runs").json()
        assert runs["active_job"] is None
        preparation = runs["runs"][0]["preparation"]
        assert preparation["state"] == "failed" and preparation["stage"] == "verification" and preparation["can_finish"] is True
        assert again.get(f"{BASE}/handoff").json()["preparation"]["state"] == "failed"


def test_a_preparation_that_never_ended_reads_as_interrupted(env):
    """The process died: the marker was opened and has no end. No job, so nothing is running."""
    from scholar_harness.pipeline import harvest_marker

    client, ws, _ = env
    run = h._write_run(ws, 1, started="2026-11-13T08:00:00Z")
    (run / "raw.json").write_text("[]", encoding="utf-8")
    harvest_marker.start(run)
    harvest_marker.record_stage(run, "deduplication", "DONE")
    preparation = _preparation(client)
    assert preparation["state"] == "interrupted" and preparation["stage"] == "hydration"
    assert preparation["can_finish"] is True and preparation["marker"] is True
    handoff = client.get(f"{BASE}/handoff").json()
    assert handoff["preparation"]["state"] == "interrupted" and handoff["corpus"]["state"] == "EMPTY"


def test_a_run_made_before_the_marker_with_its_verified_json_reads_as_ready(env):
    """No marker and a verified.json: an earlier version's finished harvest. Nothing is guessed."""
    client, ws, _ = env
    h._write_run(ws, 1, started="2026-11-10T08:00:00Z")
    (ws / "literature" / "verified.json").write_text(json.dumps([{"title": "A", "provider": "openalex"}]), encoding="utf-8")
    preparation = _preparation(client)
    assert preparation["state"] == "ready" and preparation["marker"] is False and preparation["can_finish"] is False
    assert client.get(f"{BASE}/handoff").json()["corpus"]["from_discovery"] is True


# --------------------------------------------------------------------------- D6 hand-off and accept


def test_the_handoff_never_offers_an_earlier_runs_works_as_a_later_runs(env, monkeypatch):
    """Run 1 ended; run 2's verification failed. verified.json is still run 1's, and is not run 2's corpus."""
    client, ws, _ = env
    first, _ = h._run(client, {"providers": ["openalex"]})
    assert first["state"] == "succeeded"
    run_one = (ws / "literature" / "verified.json").read_bytes()
    _fail_verification_once(client, monkeypatch, {"providers": ["crossref"]})
    assert (ws / "literature" / "verified.json").read_bytes() == run_one

    runs = {r["run"]: r["preparation"] for r in client.get(f"{BASE}/runs").json()["runs"]}
    assert runs["run_001"]["state"] == "superseded" and runs["run_001"]["can_finish"] is False
    assert runs["run_002"]["state"] == "failed"

    handoff = client.get(f"{BASE}/handoff").json()
    assert handoff["run"] == "run_002" and handoff["preparation"]["state"] == "failed"
    assert handoff["provider_mix"] == [] and handoff["abstracts"]["with_abstract"] == 0
    assert handoff["corpus"]["state"] == "EMPTY" and handoff["corpus"]["from_discovery"] is False
    assert client.get("/api/v1/screening/corpus").json()["from_discovery"] is False

    refused = client.post(ACCEPT)
    assert refused.status_code == 409 and h._code(refused) == "PREPARATION_UNFINISHED", refused.text
    assert refused.json()["detail"]["details"]["run"] == "run_002"
    assert not (ws / "audit" / "artifact_registry.json").exists() or "corpus_snapshot" not in (
        ws / "audit" / "artifact_registry.json"
    ).read_text(encoding="utf-8")

    old = client.post(f"{BASE}/runs/run_001/prepare")
    assert old.status_code == 409 and old.json()["detail"]["details"]["reason"] == "superseded"

    job, _ = _finish(client, "run_002")
    assert job["state"] == "succeeded", job
    handoff = client.get(f"{BASE}/handoff").json()
    assert handoff["corpus"]["state"] == "STAGED" and handoff["preparation"]["state"] == "ready"
    assert [m["provider"] for m in handoff["provider_mix"]] == ["crossref"]
    accepted = client.post(ACCEPT)
    assert accepted.status_code == 200, accepted.text
    event = next(e for e in h._journal(ws) if e["action"] == "CORPUS_SNAPSHOT_ACCEPTED")
    assert "run_002" in event["description"]


def test_the_accept_refuses_an_unfinished_preparation(env, monkeypatch):
    """Without any verified.json the accept names the unfinished harvest, not an empty staging area."""
    client, _ws, _ = env
    _fail_verification_once(client, monkeypatch)
    refused = client.post(ACCEPT)
    assert refused.status_code == 409 and h._code(refused) == "PREPARATION_UNFINISHED", refused.text
    details = refused.json()["detail"]["details"]
    assert details == {**details, "run": "run_001", "state": "failed", "stage": "verification"}


def test_the_engine_accept_refuses_while_the_marker_has_no_end(env):
    """The engine's own guard (any caller of the hand-off accept), read from the marker alone."""
    from scholar_harness.corpus_accept import AcceptCorpusRefused
    from scholar_harness.pipeline import harvest_marker

    _client, ws, _ = env
    run = h._write_run(ws, 1, started="2026-11-13T08:00:00Z")
    (ws / "literature" / "verified.json").write_text(json.dumps([{"title": "A", "provider": "openalex"}]), encoding="utf-8")
    harvest_marker.start(run)
    with pytest.raises(AcceptCorpusRefused) as caught:
        coordinator.accept_discovery_corpus(ws)
    assert caught.value.code == "PREPARATION_UNFINISHED"


# --------------------------------------------------------------------------- the route's refusals


def test_finish_preparing_refusals(env, monkeypatch):
    from scholar_search.config import settings

    client, ws, _ = env
    missing = client.post(f"{BASE}/runs/run_009/prepare")
    assert missing.status_code == 404 and h._code(missing) == "RUN_NOT_FOUND"

    done, _ = h._run(client, {"providers": ["openalex"]})
    assert done["state"] == "succeeded"
    ready = client.post(f"{BASE}/runs/run_001/prepare")
    assert ready.status_code == 409 and h._code(ready) == "PREPARATION_NOT_AVAILABLE"
    assert ready.json()["detail"]["details"]["reason"] == "already_prepared"

    _fail_verification_once(client, monkeypatch, {"providers": ["crossref"]})
    monkeypatch.setattr(settings, "mailto", "")
    no_contact = client.post(f"{BASE}/runs/run_002/prepare")
    assert no_contact.status_code == 409 and h._code(no_contact) == "MAILTO_NOT_SET"
    monkeypatch.setattr(settings, "mailto", "console@example.invalid")

    raw = _run_dir(ws, "run_002") / "raw.json"
    kept = raw.read_bytes()
    raw.unlink()
    gone = client.post(f"{BASE}/runs/run_002/prepare")
    assert gone.status_code == 409 and gone.json()["detail"]["details"]["reason"] == "records_missing"
    raw.write_bytes(kept)

    job, _ = _finish(client, "run_002")
    assert job["state"] == "succeeded"
    assert client.post(ACCEPT).status_code == 200
    frozen = client.post(f"{BASE}/runs/run_002/prepare")
    assert frozen.status_code == 409 and h._code(frozen) == "CORPUS_ALREADY_ACCEPTED"


def test_one_job_at_a_time_also_for_finishing(env, monkeypatch):
    client, _ws, _ = env
    _fail_verification_once(client, monkeypatch, {"providers": ["openalex"]})

    release = threading.Event()
    monkeypatch.setattr(hyd_mod, "AbstractHydrator", _hydrator_until(release.is_set))
    started = client.post(f"{BASE}/runs/run_001/prepare")
    assert started.status_code == 202
    job_id = started.json()["job"]["job_id"]
    runs = client.get(f"{BASE}/runs").json()
    assert runs["active_job"]["kind"] == "prepare" and runs["runs"][0]["preparation"]["state"] == "running"
    assert runs["runs"][0]["preparation"]["stage"] == "hydration"
    busy = client.post(f"{BASE}/runs/run_001/prepare")
    assert busy.status_code == 409 and h._code(busy) == "DISCOVERY_JOB_ACTIVE"
    search = client.post(f"{BASE}/runs", json={"providers": ["openalex"]})
    assert search.status_code == 409 and h._code(search) == "DISCOVERY_JOB_ACTIVE"
    release.set()
    h._events(client, job_id)
    assert client.get(f"{BASE}/jobs/{job_id}").json()["job"]["state"] == "succeeded"


def test_the_browser_allowlist_carries_the_finish_route():
    from scholar_harness.console.browser import POST_PATHS

    assert any(p.fullmatch("api/v1/discovery/runs/run_001/prepare") for p in POST_PATHS)
    assert not any(p.fullmatch("api/v1/discovery/runs/run_001/legs") for p in POST_PATHS)


# --------------------------------------------------------------------------- review round 1 (2026-11-17)


def test_finishing_names_its_own_run_in_the_deduplication_record(env, monkeypatch):
    """Finding 2: a later search that was stopped is the newest folder, but not the run being deduplicated."""
    client, ws, providers = env
    real = coordinator.run_deduplication

    def broken(**kwargs):
        raise RuntimeError("no room")

    monkeypatch.setattr(coordinator, "run_deduplication", broken)
    first, _ = h._run(client, {"providers": ["crossref"]})
    assert first["state"] == "failed"
    monkeypatch.setattr(coordinator, "run_deduplication", real)
    providers.set("openalex", h.FakeProvider("openalex", [h._doc("openalex", i) for i in range(500)], delay=0.02))
    job_id = client.post(f"{BASE}/runs", json={"providers": ["openalex"]}).json()["job"]["job_id"]
    time.sleep(0.4)
    assert client.post(f"{BASE}/jobs/{job_id}/cancel").json()["job"]["state"] == "cancelled"
    assert _run_dir(ws, "run_002").is_dir() and _preparation(client, "run_002")["state"] == "none"
    assert _preparation(client, "run_001")["state"] == "failed"  # still the corpus run

    job, _ = _finish(client, "run_001")
    assert job["state"] == "succeeded", job
    clusters = json.loads((ws / "literature" / "dedup" / "clusters.json").read_text(encoding="utf-8"))
    assert clusters["run"] == "run_001"
    assert client.get(f"{BASE}/dedup").json()["run"] == "run_001"


def test_a_deduplication_record_of_another_run_is_not_reused(env, monkeypatch):
    """The marker says deduplication ended, but deduped.json is another run's: start from this run's raw.json."""
    client, ws, _ = env
    _fail_verification_once(client, monkeypatch, {"providers": ["openalex"]})
    path = ws / "literature" / "dedup" / "clusters.json"
    clusters = json.loads(path.read_text(encoding="utf-8"))
    assert clusters["run"] == "run_001"
    path.write_text(json.dumps({**clusters, "run": "run_009"}), encoding="utf-8")
    job, _ = _finish(client)
    assert job["state"] == "succeeded" and job["result"]["resumed_from"] == "deduplication", job
    assert json.loads(path.read_text(encoding="utf-8"))["run"] == "run_001"


def test_changed_deduplication_tiers_start_again_from_the_saved_records(env, monkeypatch):
    """Finding 11: deduped.json made under other tiers is not what the protocol asks for now."""
    client, ws, _ = env
    _fail_verification_once(client, monkeypatch, {"providers": ["openalex"]})
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    protocol["method"] = {
        "dedup": {"doi": True, "title_similarity": 0.9, "first_author": True, "year_tolerance": 0},
        "rules_version": "screening-rules-v1", "not_reported": "unclear", "blinding": "reveal_after_decision",
    }
    (ws / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    job, events = _finish(client)
    assert job["state"] == "succeeded" and job["result"]["resumed_from"] == "deduplication", job
    assert next(d["stage"] for name, d in events if name == "stage") == "deduplication"
    method = json.loads((ws / "literature" / "dedup" / "clusters.json").read_text(encoding="utf-8"))["method"]
    assert method["title_similarity"] == 0.9 and method["year_tolerance"] == 0 and method["source"] == "protocol"


def test_a_new_search_does_not_make_an_earlier_unfinished_run_read_as_running(env):
    """Finding 6: `running` belongs to the run a job is preparing, not to any marker without an end."""
    from scholar_harness.pipeline import harvest_marker

    client, ws, providers = env
    run = h._write_run(ws, 1, started="2026-11-13T08:00:00Z")
    (run / "raw.json").write_text("[]", encoding="utf-8")
    harvest_marker.start(run)
    providers.set("openalex", h.FakeProvider("openalex", [h._doc("openalex", i) for i in range(500)], delay=0.02))
    job_id = client.post(f"{BASE}/runs", json={"providers": ["openalex"]}).json()["job"]["job_id"]
    time.sleep(0.3)
    runs = client.get(f"{BASE}/runs").json()
    assert runs["active_job"]["job_id"] == job_id  # the new search is still fetching
    preparation = runs["runs"][0]["preparation"]
    assert preparation["state"] == "interrupted" and preparation["job_id"] is None
    assert client.get(f"{BASE}/handoff").json()["preparation"]["state"] == "interrupted"
    assert client.post(f"{BASE}/jobs/{job_id}/cancel").json()["job"]["state"] == "cancelled"


def test_a_frozen_corpus_says_why_a_run_cannot_be_finished(env, monkeypatch):
    """Finding 3: exports accepted beside an unfinished harvest; the run says the corpus is accepted."""
    from scholar_harness.corpus_accept import stage_ris_source

    client, ws, _ = env
    _fail_verification_once(client, monkeypatch, {"providers": ["openalex"]})
    assert _preparation(client)["cannot_finish"] is None
    fixture = h.ROOT / "tests" / "kits" / "search" / "fixtures" / "imports" / "rejections.ris"
    stage_ris_source(ws, "Scopus", fixture.read_bytes(), file_name="scopus.ris", searched_on="2026-11-10")
    assert client.post(ACCEPT).status_code == 200  # the staged exports are the corpus
    preparation = _preparation(client)
    assert preparation["state"] == "failed" and preparation["can_finish"] is False
    assert preparation["cannot_finish"] == "corpus_accepted"
    raw = _run_dir(ws) / "raw.json"
    raw.unlink()
    assert _preparation(client)["cannot_finish"] == "corpus_accepted"  # the frozen corpus comes first
