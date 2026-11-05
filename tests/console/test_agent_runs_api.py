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
