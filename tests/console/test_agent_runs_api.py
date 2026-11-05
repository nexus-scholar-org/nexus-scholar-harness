"""Agent runs, calibration and agreement over the screening API (M1b-2, contract §4).

A fake driver stands in for the provider and the run executes synchronously,
so no test reaches a network or spends a key.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from scholar_agent.drivers import DriverResult, Usage
from scholar_agent.tasks import screening as task_mod
from scholar_harness.console import create_app
from scholar_harness.console.refusals import CONSOLE_REFUSALS
from scholar_harness.screening import agent_runs as runs
from scholar_harness.screening import events as ev
from scholar_harness.screening import proposals as pr
from test_screening_api_v1 import BASE, DESKTOP, PHONE, _event, _post, _studies, _workspace

CONSENT = {"provider": "anthropic", "accepted_at": "2026-11-05T09:00:00Z"}


class FakeDriver:
    """Answers each record by a per-study plan; `refusal` and `error` carry no output."""

    def __init__(self, plan=None, usage=Usage(input_tokens=1000, output_tokens=200)):
        self.plan, self.usage, self.seen = plan or {}, usage, []

    def run(self, requests, spec, *, on_result=None, cancelled=lambda: False):
        results = []
        for request in requests:
            if cancelled():
                break
            self.seen.append(request.custom_id)
            kind = self.plan.get(request.custom_id, "include")
            if kind in ("refusal", "error", "truncated", "invalid"):
                result = DriverResult(request.custom_id, kind, detail="test", usage=self.usage, model=spec.model)
            else:
                ids = spec.schema["properties"]["criteria"]["items"]["properties"]["id"]["enum"]
                answers = [{"id": i, "answer": "not_reported", "quote": ""} for i in ids]
                result = DriverResult(request.custom_id, "ok", output={"criteria": answers, "cannot_decide": False, "reasoning": "r"}, usage=self.usage, model=spec.model)
            results.append(result)
            if on_result:
                on_result(result)
        return results


def _client(ws, driver=None, executor=None):
    app = create_app(ws, token=DESKTOP, phone_tokens={PHONE})
    app.state.driver_factory = lambda provider, key: driver or FakeDriver()
    app.state.run_executor = executor or (lambda fn: fn())
    return TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {DESKTOP}"})


@pytest.fixture
def ws(tmp_path):
    return _workspace(tmp_path)


def _journal(ws):
    return [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()]


def test_an_estimate_needs_no_consent_and_writes_nothing(ws):
    client = _client(ws)
    before = (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8")
    body = client.post(f"{BASE}/proposals/runs", json={"estimate_only": True}).json()
    assert body["run_id"] is None and body["estimate"]["records"] == 3 and body["estimate"]["prices_as_of"]
    assert (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8") == before
    assert not (ws / runs.RUNS_DIR).exists()


def test_a_run_without_consent_is_refused_and_nothing_leaves(ws):
    driver = FakeDriver()
    response = _client(ws, driver).post(f"{BASE}/proposals/runs", json={})
    assert response.status_code == 409 and response.json()["detail"]["code"] == "CONSENT_REQUIRED"
    assert driver.seen == []


def test_every_record_gets_a_proposal_and_a_refusal_is_unclear_never_dropped(ws):
    studies = _studies(_client(ws))
    driver = FakeDriver(plan={studies[0]: "refusal", studies[1]: "error"})
    client = _client(ws, driver)
    started = client.post(f"{BASE}/proposals/runs", json={"consent": CONSENT}).json()
    status = client.get(f"{BASE}/proposals/runs/{started['run_id']}").json()
    assert (status["state"], status["done"], status["refused"], status["failed"]) == ("completed", 3, 1, 1)
    stored = {p["study_id"]: p for p in pr.read_proposals(ws)}
    assert sorted(stored) == sorted(studies)
    assert stored[studies[0]]["derived_outcome"] == "MAYBE" and stored[studies[0]]["driver_status"] == "refusal"
    assert stored[studies[2]]["run_id"] == started["run_id"] and stored[studies[2]]["prompt_sha256"] == task_mod.load_task().prompt_sha256
    rows = _journal(ws)
    actions = [r["action"] for r in rows]
    assert "SCREENING_AGENT_CONSENT" in actions and "AGENT_RUN_STARTED" in actions and "AGENT_RUN_COMPLETED" in actions
    completed = next(r for r in rows if r["action"] == "AGENT_RUN_COMPLETED")
    assert completed["metrics"]["refused"] == 1
    # No outcome ever reaches the journal (it is readable before a decision).
    assert "MAYBE" not in json.dumps(rows) and "derived" not in json.dumps(rows)
    # A proposal is never a decision.
    assert ev.read_events(ws) == []
    assert runs.active_run(ws) is None


def test_one_run_at_a_time_and_cancel_keeps_finished_proposals(ws):
    pending = []
    client = _client(ws, FakeDriver(), executor=pending.append)
    first = client.post(f"{BASE}/proposals/runs", json={"consent": CONSENT}).json()
    second = client.post(f"{BASE}/proposals/runs", json={})
    assert second.status_code == 409 and second.json()["detail"]["code"] == "RUN_ALREADY_ACTIVE"
    assert client.post(f"{BASE}/proposals/runs/{first['run_id']}/cancel").json()["state"] == "cancelled"
    pending[0]()  # the run notices the cancel before its first record
    status = client.get(f"{BASE}/proposals/runs/{first['run_id']}").json()
    assert status["state"] == "cancelled" and status["done"] == 0
    assert runs.active_run(ws) is None


def test_the_cost_ceiling_refuses_an_estimate_above_it_and_stops_a_run_that_reaches_it(ws):
    client = _client(ws, FakeDriver(usage=Usage(input_tokens=1_000_000, output_tokens=100_000)))
    too_low = client.post(f"{BASE}/proposals/runs", json={"consent": CONSENT, "cost_ceiling_usd": 0.0001})
    assert too_low.status_code == 409 and too_low.json()["detail"]["code"] == "COST_CEILING_REACHED"
    started = client.post(f"{BASE}/proposals/runs", json={"cost_ceiling_usd": 1.0}).json()
    status = client.get(f"{BASE}/proposals/runs/{started['run_id']}").json()
    assert (status["state"], status["code"]) == ("stopped", "COST_CEILING_REACHED")
    assert 0 < status["done"] < 3 and status["cost_so_far"] >= 1.0


def test_a_provider_without_a_key_is_refused(ws, monkeypatch):
    app = create_app(ws, token=DESKTOP)
    monkeypatch.setattr("scholar_agent.keys.resolve_key", lambda provider: None)
    client = TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {DESKTOP}"})
    response = client.post(f"{BASE}/proposals/runs", json={"consent": CONSENT})
    assert response.status_code == 409 and response.json()["detail"]["code"] == "PROVIDER_KEY_MISSING"
    assert {"PROVIDER_KEY_MISSING", "UNKNOWN_RUN", "CONSENT_REQUIRED", "RUN_ALREADY_ACTIVE", "COST_CEILING_REACHED"} <= CONSOLE_REFUSALS


def test_unknown_run_and_phone_scope(ws):
    client = _client(ws)
    missing = client.get(f"{BASE}/proposals/runs/RUN-nope")
    assert missing.status_code == 404 and missing.json()["detail"]["code"] == "UNKNOWN_RUN"
    phone = client.post(f"{BASE}/proposals/runs", json={"estimate_only": True}, headers={"Authorization": f"Bearer {PHONE}"})
    assert phone.status_code == 403 and phone.json()["detail"]["code"] == "TOKEN_SCOPE_REFUSED"


def test_calibration_uses_decided_records_and_reports_missed_includes(ws):
    client = _client(ws)
    studies = _studies(client)
    refused = client.post(f"{BASE}/proposals/calibrations", json={"study_ids": studies[:1]})
    assert refused.status_code == 422  # undecided records are not calibration material
    _post(client, [_event(client, s, "INCLUDE") for s in studies])
    runs.record_consent(ws, "anthropic", model="m", prompt_sha256="sha256:x", accepted_at="2026-11-05T09:00:00Z")
    # The fake agent answers not_reported everywhere -> Unclear, so no include is missed.
    run_id = client.post(f"{BASE}/proposals/calibrations", json={"study_ids": studies}).json()["run_id"]
    status = client.get(f"{BASE}/proposals/runs/{run_id}").json()
    assert status["kind"] == "calibration" and status["calibration"]["include_recall"] == 1.0
    assert status["calibration"]["advisory"] is True and status["calibration"]["missed_includes"] == []


def test_agreement_counts_only_decisions_made_before_the_reveal(ws):
    client = _client(ws)
    studies = _studies(client)
    runs.record_consent(ws, "anthropic", model="m", prompt_sha256="sha256:x", accepted_at="2026-11-05T09:00:00Z")
    client.post(f"{BASE}/proposals/runs", json={})  # Unclear drafts for every record
    first = _event(client, studies[0], "INCLUDE")
    _post(client, [first])
    client.get(f"{BASE}/records/{studies[0]}/proposal")  # reveal after the decision
    _post(client, [_event(client, studies[0], "EXCLUDE", supersedes=first["event_id"])])  # changed after seeing
    body = client.get(f"{BASE}/agreement").json()
    assert body["decided_with_proposal"] == 1 and body["unclear_either_side"] == 1  # the pre-reveal INCLUDE vs an Unclear draft
    assert body["kappa"] is None and body["kappa_note"]
    assert body["table_2x2"] == {"both_include": 0, "you_include_agent_exclude": 0, "you_exclude_agent_include": 0, "both_exclude": 0}


def test_setup_names_key_sources_never_keys_and_the_latest_run(ws, monkeypatch):
    monkeypatch.setattr("scholar_agent.keys._from_keychain", lambda provider: "sk-secret" if provider == "anthropic" else None)
    for var in ("OPENAI_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    client = _client(ws)
    empty = client.get(f"{BASE}/proposals/setup").json()
    assert empty["active_run"] is None and empty["latest_run"] is None
    assert empty["task"]["prompt_sha256"] == task_mod.load_task().prompt_sha256
    started = client.post(f"{BASE}/proposals/runs", json={"consent": CONSENT}).json()
    body = client.get(f"{BASE}/proposals/setup")
    assert "sk-secret" not in body.text
    setup = body.json()
    keys = {p["provider"]: p["key"] for p in setup["providers"]}
    assert keys == {"anthropic": "keychain", "openai_compatible": "none", "gemini": "none"}
    assert next(p for p in setup["providers"] if p["provider"] == "anthropic")["consent"]["accepted_at"] == CONSENT["accepted_at"]
    assert setup["latest_run"]["run_id"] == started["run_id"] and setup["latest_run"]["state"] == "completed"
    phone = client.get(f"{BASE}/proposals/setup", headers={"Authorization": f"Bearer {PHONE}"})
    assert phone.status_code == 403


# --- review findings (M1b-2): the lock, the ceiling and concurrent access ---------


def _thread_like(pending):
    """Runs the work like a thread does: an exception ends the thread, nothing propagates."""

    def run(fn):
        def body():
            try:
                fn()
            except BaseException:  # noqa: BLE001 - a dead thread, as in production
                pass

        pending.append(body)

    return run


@pytest.mark.parametrize(("error", "status"), [(ImportError("No module named 'anthropic'"), 409), (ValueError("the OpenAI-compatible driver needs a base URL"), 422)])
def test_a_driver_that_cannot_be_built_is_refused_and_never_holds_the_lock(ws, error, status):
    app = create_app(ws, token=DESKTOP, phone_tokens={PHONE})

    def raising(provider, key):
        raise error

    app.state.driver_factory = raising
    app.state.run_executor = lambda fn: fn()
    client = TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {DESKTOP}"})
    refused = client.post(f"{BASE}/proposals/runs", json={"consent": CONSENT})
    assert refused.status_code == status and refused.json()["detail"]["code"] == "DRIVER_UNAVAILABLE"
    assert runs.active_run(ws) is None
    app.state.driver_factory = lambda provider, key: FakeDriver()
    assert client.post(f"{BASE}/proposals/runs", json={}).status_code == 200


def test_a_run_that_crashes_in_its_thread_ends_failed_and_frees_the_lock(ws):
    class Crashing(FakeDriver):
        def run(self, requests, spec, **kwargs):
            raise RuntimeError("provider SDK blew up")

    pending = []
    client = _client(ws, Crashing(), executor=_thread_like(pending))
    run_id = client.post(f"{BASE}/proposals/runs", json={"consent": CONSENT}).json()["run_id"]
    pending.pop()()
    status = client.get(f"{BASE}/proposals/runs/{run_id}").json()
    assert status["state"] == "failed" and runs.active_run(ws) is None
    assert any(e.get("action") == "AGENT_RUN_COMPLETED" and e["parameters"]["state"] == "failed" for e in _journal(ws))
    client.app.state.driver_factory = lambda provider, key: FakeDriver()
    assert client.post(f"{BASE}/proposals/runs", json={}).status_code == 200


def test_a_lock_left_by_a_stopped_engine_is_recovered_by_the_next_run_or_a_cancel(ws):
    pending = []
    client = _client(ws, FakeDriver(), executor=pending.append)
    stale = client.post(f"{BASE}/proposals/runs", json={"consent": CONSENT}).json()["run_id"]
    # The engine stops: the worker never runs and this process forgets the run.
    runs._LIVE.clear()
    pending.clear()
    assert client.get(f"{BASE}/proposals/runs/{stale}").json()["state"] == "running"
    assert client.post(f"{BASE}/proposals/runs/{stale}/cancel").json()["state"] == "cancelled"
    assert runs.active_run(ws) is None and runs.read_run(ws, stale)["state"] == "cancelled"

    again = client.post(f"{BASE}/proposals/runs", json={}).json()["run_id"]
    runs._LIVE.clear()
    pending.clear()
    fresh = client.post(f"{BASE}/proposals/runs", json={})
    assert fresh.status_code == 200, fresh.json()
    assert runs.read_run(ws, again)["state"] == "failed"
    assert "engine stopped" in runs.read_run(ws, again)["error"]


def test_an_unpriced_provider_refuses_a_ceiling_and_reports_its_cost_as_unknown(ws):
    gemini = {"provider": "gemini", "accepted_at": "2026-11-05T09:00:00Z"}
    client = _client(ws, FakeDriver(usage=Usage(input_tokens=10_000_000, output_tokens=1)))
    refused = client.post(f"{BASE}/proposals/runs", json={"provider": "gemini", "model": "gemini-x", "consent": gemini, "cost_ceiling_usd": 0.0001})
    assert refused.status_code == 422 and refused.json()["detail"]["code"] == "CEILING_NOT_PRICED"
    run_id = client.post(f"{BASE}/proposals/runs", json={"provider": "gemini", "model": "gemini-x"}).json()["run_id"]
    status = client.get(f"{BASE}/proposals/runs/{run_id}").json()
    assert status["state"] == "completed" and status["cost_so_far"] is None
    assert {"DRIVER_UNAVAILABLE", "CEILING_NOT_PRICED"} <= CONSOLE_REFUSALS


def test_a_real_threaded_run_survives_concurrent_reads_and_keeps_a_mid_run_cancel(ws):
    import threading
    import time

    gate = threading.Event()

    class Slow(FakeDriver):
        def run(self, requests, spec, *, on_result=None, cancelled=lambda: False):
            for i, request in enumerate(requests):
                if cancelled():
                    break
                ids = spec.schema["properties"]["criteria"]["items"]["properties"]["id"]["enum"]
                answers = [{"id": c, "answer": "not_reported", "quote": ""} for c in ids]
                on_result(DriverResult(request.custom_id, "ok", output={"criteria": answers, "cannot_decide": False, "reasoning": "r"}, usage=self.usage, model=spec.model))
                if i == 0:
                    gate.wait(5)  # hold after the first record until the cancel is sent
            return []

    app = create_app(ws, token=DESKTOP, phone_tokens={PHONE})
    app.state.driver_factory = lambda provider, key: Slow()
    client = TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {DESKTOP}"})
    run_id = client.post(f"{BASE}/proposals/runs", json={"consent": CONSENT}).json()["run_id"]
    errors, stop = [], threading.Event()

    def poll():
        while not stop.is_set():
            try:
                runs.read_run(ws, run_id)
                runs.list_runs(ws)
            except Exception as exc:  # noqa: BLE001 - collected and asserted below
                errors.append(exc)

    readers = [threading.Thread(target=poll) for _ in range(4)]
    for t in readers:
        t.start()
    assert client.post(f"{BASE}/proposals/runs/{run_id}/cancel").json()["state"] == "cancelled"
    gate.set()
    deadline = time.time() + 10
    while runs.active_run(ws) is not None and time.time() < deadline:
        time.sleep(0.02)
    stop.set()
    for t in readers:
        t.join()
    status = client.get(f"{BASE}/proposals/runs/{run_id}").json()
    assert errors == []
    assert status["state"] == "cancelled" and status["done"] == 1 and runs.active_run(ws) is None
    assert json.loads((ws / runs.RUNS_DIR / f"{run_id}.json").read_text(encoding="utf-8"))["state"] == "cancelled"


def test_calibration_passes_the_base_url_to_the_driver(ws, monkeypatch):
    client = _client(ws)
    studies = _studies(client)
    _post(client, [_event(client, s, "INCLUDE") for s in studies])
    runs.record_consent(ws, "openai_compatible", model="m", prompt_sha256="sha256:x", accepted_at="2026-11-05T09:00:00Z")
    client.app.state.driver_factory = None
    seen = {}

    def make(provider, *, api_key, base_url=None, **options):
        seen["base_url"] = base_url
        return FakeDriver()

    monkeypatch.setattr("scholar_agent.drivers.make_driver", make)
    monkeypatch.setattr("scholar_agent.keys.resolve_key", lambda provider: None)
    body = {"study_ids": studies, "provider": "openai_compatible", "model": "local", "base_url": "http://127.0.0.1:9/v1"}
    assert client.post(f"{BASE}/proposals/calibrations", json=body).status_code == 200
    assert seen["base_url"] == "http://127.0.0.1:9/v1"


def test_concurrent_starts_never_give_two_runs_the_lock(ws):
    # Re-review finding 1: a fresh lock was taken for stale before its run was registered.
    import threading

    runs.record_consent(ws, "anthropic", model="m", prompt_sha256="sha256:x", accepted_at="2026-11-05T09:00:00Z")
    ids = [s for s in ev.load_context(ws).study_batch]
    for _ in range(30):
        pending, outcomes, barrier = [], [], threading.Barrier(4)

        def start():
            barrier.wait()
            try:
                outcomes.append(runs.start_run(ws, provider="anthropic", model="claude-opus-5-5", effort="low", study_ids=ids,
                                               cost_ceiling_usd=None, driver_factory=lambda p, k: FakeDriver(), executor=pending.append)["run_id"])
            except runs.RunRefused as exc:
                outcomes.append(exc.code)

        threads = [threading.Thread(target=start) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        started = [o for o in outcomes if o.startswith("RUN-")]
        assert len(started) == 1 and outcomes.count("RUN_ALREADY_ACTIVE") == 3
        assert runs.active_run(ws) == started[0]
        for work in pending:
            work()
        assert runs.active_run(ws) is None


def test_a_lock_held_by_another_live_engine_is_never_taken_and_a_dead_one_is_recovered(ws):
    # Re-review finding 2: "stale" meant "no worker in this process".
    import os

    client = _client(ws, FakeDriver(), executor=lambda fn: None)
    run_id = client.post(f"{BASE}/proposals/runs", json={"consent": CONSENT}).json()["run_id"]
    lock = ws / runs.LOCK_FILE
    runs._LIVE.clear()
    # Another engine process that is still alive owns the run (this test's parent process).
    lock.write_text(json.dumps({"run_id": run_id, "pid": os.getppid(), "engine": "other"}), encoding="utf-8")
    refused = client.post(f"{BASE}/proposals/runs", json={})
    assert refused.status_code == 409 and refused.json()["detail"]["code"] == "RUN_ALREADY_ACTIVE"
    cancel = client.post(f"{BASE}/proposals/runs/{run_id}/cancel")
    assert cancel.status_code == 409 and runs.read_run(ws, run_id)["state"] == "running"
    # A lock still being written is held, not stale.
    lock.write_text("", encoding="utf-8")
    assert client.post(f"{BASE}/proposals/runs", json={}).status_code == 409
    # The owning process is gone: the next run recovers it, journaling its end once.
    lock.write_text(json.dumps({"run_id": run_id, "pid": 2**22 + 12345, "engine": "gone"}), encoding="utf-8")
    assert client.post(f"{BASE}/proposals/runs", json={}).status_code == 200
    assert runs.read_run(ws, run_id)["state"] == "failed"
    completed = [r for r in _journal(ws) if r["action"] == "AGENT_RUN_COMPLETED" and r["parameters"]["run_id"] == run_id]
    assert len(completed) == 1


def test_pid_liveness_fails_safe(ws):
    # Third review: an engine this one may not inspect was read as gone, and a
    # pid out of range raised. Both now answer without taking a live run.
    import os
    import subprocess
    import sys

    assert runs._pid_alive(os.getpid()) and runs._pid_alive(os.getppid())
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()
    assert runs._pid_alive(child.pid) is False
    assert runs._pid_alive(2**40) is False and runs._pid_alive(0) is False and runs._pid_alive(-1) is False
    if os.name == "nt":
        assert runs._pid_alive(4)  # System: exists, and not ours to open
