"""Hermetic tests for the Harness Console server (M5.1).

These tests never hit the network or a real kit CLI. The HTTP layer is driven
through a stubbed JobRunner; the async job-runner lifecycle is exercised
directly in an asyncio loop with a fast, side-effect-free subprocess so it is
deterministic and portable (real subprocesses need a proactor event loop,
which TestClient does not provide on all platforms).
"""

from __future__ import annotations

import importlib
import json
import sys

import pytest
from fastapi.testclient import TestClient

from scholar_harness.console import create_app


def _bootstrap(tmp):
    """Create a minimal workspace with canonical files + a journal."""
    ws = tmp / "ws"
    (ws / "literature" / "screening").mkdir(parents=True)
    (ws / "synthesis").mkdir(parents=True)
    (ws / "phase4").mkdir(parents=True)
    (ws / "audit").mkdir(parents=True)

    (ws / "literature" / "included.json").write_text(json.dumps([{"id": 1}]), encoding="utf-8")
    (ws / "literature" / "excluded.json").write_text(json.dumps([{"id": 2}]), encoding="utf-8")
    (ws / "literature" / "raw_search.json").write_text(
        json.dumps([{"workspace_id": "a"}, {"workspace_id": "b"}]), encoding="utf-8"
    )
    (ws / "literature" / "screening" / "batch_001.json").write_text(
        json.dumps({"items": [{"workspace_id": "a"}]}), encoding="utf-8"
    )
    (ws / "synthesis" / "literature_review.md").write_text("# Review", encoding="utf-8")

    journal = ws / "audit" / "journal.jsonl"
    journal.write_text(
        json.dumps(
            {
                "timestamp": "2026-09-01T00:00:00+00:00",
                "event_id": "EVT-000",
                "action": "SEED",
                "agent_or_tool": "test",
                "description": "seed",
                "parameters": {},
                "inputs": [],
                "outputs": [],
                "metrics": {},
                "status": "SUCCESS",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (ws / "project.json").write_text(json.dumps({"title": "Test WS", "stats": {}}), encoding="utf-8")
    return ws


# ---------------------------------------------------------------------------
# Read endpoints (workspace as source of truth)
# ---------------------------------------------------------------------------

def test_healthz_and_index(tmp_path):
    ws = _bootstrap(tmp_path)
    app = create_app(ws)
    client = TestClient(app)
    assert client.get("/healthz").json()["status"] == "ok"
    assert client.get("/").status_code == 200


def test_literature_included_and_excluded(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))
    inc = client.get("/api/v1/literature/included")
    assert inc.status_code == 200
    assert inc.json() == [{"id": 1}]
    exc = client.get("/api/v1/literature/excluded")
    assert exc.json() == [{"id": 2}]


def test_literature_candidates_pagination(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))
    r = client.get("/api/v1/literature/candidates?limit=1&offset=1")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1
    assert body["items"][0]["workspace_id"] == "b"


def test_screening_batches(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))
    r = client.get("/api/v1/screening/batches")
    body = r.json()
    assert body["count"] == 1
    assert body["batches"][0]["name"] == "batch_001.json"
    assert body["batches"][0]["collected"] is False
    # single batch detail
    b = client.get("/api/v1/screening/batch/1")
    assert b.status_code == 200
    assert b.json()["items"] == {"items": [{"workspace_id": "a"}]}


def test_missing_literature_file_returns_404(tmp_path):
    ws = _bootstrap(tmp_path)
    (ws / "literature" / "included.json").unlink()
    client = TestClient(create_app(ws))
    assert client.get("/api/v1/literature/included").status_code == 404


def test_audit_events_read_and_filter(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))
    all_events = client.get("/api/v1/audit/events").json()
    assert all_events["total"] == 1
    filtered = client.get("/api/v1/audit/events?action=SEED").json()
    assert filtered["total"] == 1
    none = client.get("/api/v1/audit/events?action=UNKNOWN").json()
    assert none["total"] == 0


def test_agent_actions_table(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))
    body = client.get("/api/v1/agents/actions").json()
    rows = body["rows"]
    ids = {r["action_id"] for r in rows}
    # D6 parity: status + trust_context must be present and self-consistent.
    assert "status" in ids
    assert "trust_context" in ids
    for r in rows:
        assert r["command"].startswith("uv run ")
        assert isinstance(r["mutates"], bool)


# ---------------------------------------------------------------------------
# Job runner lifecycle (pure-asyncio; real subprocess works in a proactor loop)
# ---------------------------------------------------------------------------

class _FakeJob:
    """A minimal job dict-able record for the stubbed runner."""

    def __init__(self, action_id: str, state: str = "running"):
        self.job_id = f"job_{action_id}_{id(self)}"
        self.action_id = action_id
        self.state = state
        self.pid = None
        self.exit_code = None
        self.command = ["fake"]
        self.cwd = "."
        self.log_path = None
        self.started_at = "2026-09-01T00:00:00+00:00"
        self.finished_at = None
        self.journal_event_id = None
        self.error = None

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "action_id": self.action_id,
            "state": self.state,
            "pid": self.pid,
            "exit_code": self.exit_code,
            "command": self.command,
            "cwd": self.cwd,
            "log_path": self.log_path,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "journal_event_id": self.journal_event_id,
            "error": self.error,
        }


class _StubRunner:
    """Injected runner: no real subprocess, so tests stay portable/CI-safe."""

    def __init__(self) -> None:
        self.jobs: dict[str, _FakeJob] = {}
        self._counter = 0
        self.start_ok = True

    async def start(self, action_id, query=None, workspace=None, pipeline_id=None):
        from scholar_harness.console.runtimes.actions import get_action

        get_action(action_id)  # raises KeyError for unknown actions (mirrors real runner)
        self._counter += 1
        job = _FakeJob(action_id)
        job.job_id = f"job_{self._counter}"
        self.jobs[job.job_id] = job
        return job

    def get(self, job_id):
        if job_id not in self.jobs:
            raise KeyError(job_id)
        return self.jobs[job_id]

    async def cancel(self, job_id):
        job = self.get(job_id)
        job.state = "cancelled"
        return job


@pytest.fixture
def stub_app(tmp_path):
    """App with a stub JobRunner injected into app.state (real broadcast)."""
    ws = _bootstrap(tmp_path)
    app = create_app(ws)
    app.state.job_runner = _StubRunner()
    return app, app.state.job_runner


def test_runner_lifecycle_writes_journal(tmp_path, monkeypatch):
    """Hermetic end-to-end through JobRunner (real subprocess, proactor loop)."""
    import asyncio

    from scholar_harness.console.runtimes.job_runner import JobRunner

    ws = _bootstrap(tmp_path)
    target = importlib.import_module("scholar_harness.console.runtimes.job_runner")

    def fast_command(action, workspace=".", query=None):
        return [sys.executable, "-c", "print('ok')"]

    monkeypatch.setattr(target, "render_command", fast_command)

    async def scenario():
        runner = JobRunner(ws)
        job = await runner.start("trust_context", workspace=str(ws))
        assert job.state in ("running", "success")
        for _ in range(100):
            await asyncio.sleep(0.05)
            if job.state in ("success", "failed", "cancelled"):
                break
        assert job.state == "success", job.state
        assert job.exit_code == 0
        assert job.journal_event_id is not None
        return job

    job = asyncio.run(scenario())

    # Exit criterion: completion lands in audit/journal.jsonl under TRUST_CONTEXT.
    events = [l for l in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()
              if l.strip()]
    tail = json.loads(events[-1])
    assert tail["action"] == "TRUST_CONTEXT"
    assert tail["status"] == "SUCCESS"

    # Exit criterion: job log captured.
    assert (ws / ".harness-console" / "jobs" / job.job_id / "stdout.log").exists()


def test_start_get_cancel_http(stub_app):
    app, _runner = stub_app
    client = TestClient(app)

    resp = client.post("/api/v1/jobs/start", json={"action_id": "sync"})
    assert resp.status_code == 202
    job = resp.json()["job"]
    jid = job["job_id"]
    assert job["state"] == "running"

    got = client.get(f"/api/v1/jobs/{jid}").json()["job"]
    assert got["job_id"] == jid

    cancelled = client.post(f"/api/v1/jobs/{jid}/cancel").json()["job"]
    assert cancelled["state"] == "cancelled"

    # Unknown job -> 404.
    assert client.get("/api/v1/jobs/nope").status_code == 404


def test_unknown_action_400(stub_app):
    app, _ = stub_app
    client = TestClient(app)
    assert client.post("/api/v1/jobs/start", json={"action_id": "does_not_exist"}).status_code == 400


# ---------------------------------------------------------------------------
# SSE primitives (hermetic; infinite streams deadlock the sync TestClient)
# ---------------------------------------------------------------------------

def test_sse_formatting():
    from scholar_harness.console.api.jobs import _sse

    msg = _sse({"event": "snapshot", "data": {"job": {"job_id": "j1"}}})
    assert "event: snapshot" in msg
    assert '"job_id": "j1"' in msg
    assert msg.endswith("\n\n")


def test_sse_broadcast_fanout_and_unsubscribe():
    import asyncio

    from scholar_harness.console.api.jobs import JobStreamBroadcast

    async def scenario():
        bcast = JobStreamBroadcast()
        q1 = bcast.subscribe()
        q2 = bcast.subscribe()
        bcast.put({"event": "job", "data": {"job": {"job_id": "j1"}}})
        assert (await asyncio.wait_for(q1.get(), 2))["event"] == "job"
        assert (await asyncio.wait_for(q2.get(), 2))["event"] == "job"
        # Unsubscribe one; it must not receive further events.
        bcast.unsubscribe(q2)
        bcast.put({"event": "job", "data": {"job": {"job_id": "j2"}}})
        assert (await asyncio.wait_for(q1.get(), 2))["data"]["job"]["job_id"] == "j2"
        assert q2.empty()
        return True

    assert asyncio.run(scenario())


def test_job_stream_replays_snapshot_then_terminates(stub_app):
    """The stream generator must emit a snapshot then yield on cancellation."""
    import asyncio
    from types import SimpleNamespace

    app, runner = stub_app
    from scholar_harness.console.api.jobs import job_stream
    from scholar_harness.console.runtimes.job_runner import Job

    # Seed a job directly so the stream can snapshot it.
    job = Job(job_id="j1", action_id="sync", command=["x"], cwd=".", timeout_s=30)
    job.state = "success"
    runner.jobs["j1"] = job

    req = SimpleNamespace(app=app)

    async def scenario():
        resp = await job_stream("j1", req)
        gen = resp.body_iterator
        first = await gen.__anext__()
        assert "event: snapshot" in first
        assert "j1" in first
        # Subsequent reads block until a broadcast event; close cleanly.
        await gen.aclose()
        return True

    assert asyncio.run(scenario())


