"""Hermetic tests for M5.4 JobRunner DAG integration (pipeline jobs).

Covers:
  - `pipeline` action in the actions table + `{pipeline}` command expansion.
  - POST /api/v1/jobs with action_id "pipeline" + pipeline_id: validation
    (missing / unknown id), live DAG execution to `success`, `requires_decision`
    halt -> failed, cooperative cancel -> cancelled, single-flight conflict,
    log + pipeline_results persistence, and journal events.
  - The builtin prisma_slr_default spec is loadable by the runner.

Subprocess-backed tests run the app with httpx/ASGITransport inside a single
`asyncio.run` loop. TestClient is avoided for those: real subprocesses spawned
through `loop.run_in_executor` never finalize under TestClient's portal loop on
Windows (the same limitation documented in test_console_m52/m53).
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from scholar_harness.console import create_app
from scholar_harness.console.runtimes.actions import get_action, render_command
from scholar_harness.console.runtimes.job_runner import JobRunner

CODE_WRITE = (
    "import pathlib,argparse,sys;"
    "p=argparse.ArgumentParser();p.add_argument('--out');p.add_argument('--content');"
    "a=p.parse_args(sys.argv[1:]);"
    "pathlib.Path(a.out).parent.mkdir(parents=True,exist_ok=True);"
    "pathlib.Path(a.out).write_text(a.content)"
)
CODE_BATCH = (
    "import pathlib,argparse,sys;"
    "p=argparse.ArgumentParser();p.add_argument('--out');"
    "a=p.parse_args(sys.argv[1:]);"
    "p=pathlib.Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);"
    "p.write_text('{}')"
)
CODE_SLOW = "import time;time.sleep(2)"


def _node(node_id: str, code: str, args: dict, outputs: list[str] | None = None,
          on_fail: str = "abort", requires_decision: bool = False) -> dict:
    return {
        "id": node_id,
        "kit": "test",
        "command": ["python", "-c", code],
        "args": args,
        "inputs": [],
        "outputs": outputs or [],
        "on_fail": on_fail,
        "requires_decision": requires_decision,
    }


def _dag_spec(spec_id: str, nodes: list[dict], edges: list[list[str]]) -> dict:
    return {
        "schema_version": "0.1.0",
        "id": spec_id,
        "name": f"DAG {spec_id}",
        "archetype": "PRISMA_SLR",
        "workspace_slug": "test-ws",
        "settings": {},
        "nodes": nodes,
        "edges": edges,
        "dry_run": {},
        "created_by": "test",
    }


def _bootstrap(tmp) -> Path:
    ws = tmp / "ws"
    ws.mkdir(parents=True)
    return ws


def _async_client(app) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def _async_wait_terminal(runner: JobRunner, job_id: str, timeout: float = 60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = runner.jobs[job_id]
        if job.state in ("success", "failed", "cancelled"):
            return job
        await asyncio.sleep(0.05)
    raise AssertionError(f"job {job_id} not terminal; state={job.state}")


def _journal_events(ws: Path) -> list[dict]:
    path = ws / "audit" / "journal.jsonl"
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


# ---------------------------------------------------------------------------
# actions table + command expansion (no subprocess)
# ---------------------------------------------------------------------------

def test_pipeline_action_in_actions_payload(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))
    r = client.get("/api/v1/agents/actions")
    assert r.status_code == 200
    rows = {row["action_id"]: row for row in r.json()["rows"]}
    assert "pipeline" in rows
    assert rows["pipeline"]["mutates"] is True
    assert "run --pipeline" in rows["pipeline"]["command"]


def test_render_command_expands_pipeline_token():
    action = get_action("pipeline")
    argv = render_command(action, workspace="W", pipeline="specs/dag.json")
    assert argv[0:2] == ["uv", "run"]
    assert "--pipeline" in argv and "specs/dag.json" in argv
    assert "-w" in argv and "W" in argv
    assert "{pipeline}" not in argv


# ---------------------------------------------------------------------------
# start validation (no subprocess)
# ---------------------------------------------------------------------------

def test_start_pipeline_requires_pipeline_id(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))
    r = client.post("/api/v1/jobs/start", json={"action_id": "pipeline"})
    assert r.status_code == 400
    assert "pipeline_id" in r.json()["detail"]


def test_start_pipeline_unknown_pipeline_id(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))
    client.post("/api/v1/pipelines", json={"spec": _dag_spec(
        "known", [_node("n1", CODE_WRITE, {"out": "gen.txt", "content": "x"}, ["gen.txt"])], [])})
    r = client.post("/api/v1/jobs/start", json={"action_id": "pipeline", "pipeline_id": "nope"})
    assert r.status_code == 400
    assert "missing pipeline spec" in r.json()["detail"]


def test_runner_loads_builtin_default_spec(tmp_path):
    ws = _bootstrap(tmp_path)
    runner = JobRunner(ws)
    spec = runner._load_pipeline_spec("prisma_slr_default")
    assert spec.id == "prisma_slr_default"
    assert len(spec.nodes) >= 3


def test_pipeline_export_script_endpoint(tmp_path):
    ws = _bootstrap(tmp_path)
    client = TestClient(create_app(ws))
    client.post("/api/v1/pipelines", json={"spec": _dag_spec(
        "exportpipe", [_node("n1", CODE_WRITE, {"out": "literature/n1.json", "content": "x"},
                            ["literature/n1.json"])], [])})
    r = client.get("/api/v1/pipelines/exportpipe/export")
    assert r.status_code == 200
    assert r.text.startswith("#!/usr/bin/env bash")
    assert "run_node 'n1'" in r.text
    assert "'uv' 'run' 'python' '-c'" in r.text
    assert "literature/n1.json" in r.text
    # builtin template is also exportable with no saved file
    rb = client.get("/api/v1/pipelines/prisma_slr_default/export")
    assert rb.status_code == 200
    assert "n3_screen" in rb.text
    # unknown id -> 404; unsupported format -> 400
    assert client.get("/api/v1/pipelines/nope/export").status_code == 404
    assert client.get("/api/v1/pipelines/exportpipe/export?script_format=bat").status_code == 400


# ---------------------------------------------------------------------------
# live DAG execution through the job runner (httpx + asyncio.run)
# ---------------------------------------------------------------------------

def test_pipeline_job_success_streams_and_persists(tmp_path):
    ws = _bootstrap(tmp_path)
    app = create_app(ws)
    spec = _dag_spec("dag_ok", [
        _node("n1", CODE_WRITE, {"out": "gen/a.txt", "content": "hello"}, ["gen/a.txt"]),
        _node("n2", CODE_WRITE, {"out": "gen/b.txt", "content": "world"}, ["gen/b.txt"]),
    ], [["n1", "n2"]])

    async def case() -> None:
        async with _async_client(app) as c:
            assert (await c.post("/api/v1/pipelines", json={"spec": spec})).status_code == 201
            r = await c.post("/api/v1/jobs/start",
                             json={"action_id": "pipeline", "pipeline_id": "dag_ok"})
            assert r.status_code == 202, r.text
            await _async_wait_terminal(app.state.job_runner, r.json()["job"]["job_id"])

    asyncio.run(case())
    runner = app.state.job_runner
    job = list(runner.jobs.values())[-1]
    assert job.state == "success", job.error
    assert job.exit_code == 0
    assert job.pipeline_id == "dag_ok"
    assert (ws / "gen" / "a.txt").read_text() == "hello"
    assert (ws / "gen" / "b.txt").read_text() == "world"

    node_states = {r["node_id"]: r["state"] for r in job.node_results or []}
    assert node_states == {"n1": "success", "n2": "success"}

    job_dir = ws / ".harness-console" / "jobs" / job.job_id
    log = (job_dir / "stdout.log").read_text(encoding="utf-8")
    assert "▶ node n1:" in log and "▶ node n2:" in log
    results = json.loads((job_dir / "pipeline_results.json").read_text(encoding="utf-8"))
    assert results["pipeline_id"] == "dag_ok"
    assert len(results["results"]) == 2

    journal = _journal_events(ws)
    assert journal[-1]["action"] == "PIPELINE"
    assert journal[-1]["status"] == "SUCCESS"
    assert journal[-1]["metrics"]["node_states"] == {"n1": "success", "n2": "success"}


def test_pipeline_job_halted_on_requires_decision(tmp_path):
    ws = _bootstrap(tmp_path)
    app = create_app(ws)
    spec = _dag_spec("dag_halt", [
        _node("n1", CODE_WRITE, {"out": "gen/a.txt", "content": "x"}, ["gen/a.txt"]),
        _node("screen", CODE_BATCH, {"out": "literature/screening/batch_001.json"},
              ["literature/screening/batch_*.json"], requires_decision=True),
    ], [["n1", "screen"]])

    async def case() -> None:
        async with _async_client(app) as c:
            assert (await c.post("/api/v1/pipelines", json={"spec": spec})).status_code == 201
            r = await c.post("/api/v1/jobs/start",
                             json={"action_id": "pipeline", "pipeline_id": "dag_halt"})
            assert r.status_code == 202, r.text
            await _async_wait_terminal(app.state.job_runner, r.json()["job"]["job_id"])

    asyncio.run(case())
    runner = app.state.job_runner
    job = list(runner.jobs.values())[-1]
    assert job.state == "failed"
    assert job.exit_code == 1
    assert "halt" in (job.error or "").lower()
    assert (ws / "literature" / "screening" / "batch_001.json").exists()

    journal = _journal_events(ws)
    assert journal[-1]["status"] == "FAILED"
    assert journal[-1]["metrics"]["state"] == "failed"


def test_pipeline_job_cancel_cooperative(tmp_path):
    ws = _bootstrap(tmp_path)
    app = create_app(ws)
    spec = _dag_spec("dag_cancel", [
        _node("n1", CODE_WRITE, {"out": "gen/a.txt", "content": "x"}, ["gen/a.txt"]),
        _node("slow", CODE_SLOW, {}, []),
        _node("n3", CODE_WRITE, {"out": "gen/c.txt", "content": "y"}, ["gen/c.txt"]),
    ], [["n1", "slow"], ["slow", "n3"]])

    async def case() -> None:
        async with _async_client(app) as c:
            assert (await c.post("/api/v1/pipelines", json={"spec": spec})).status_code == 201
            r = await c.post("/api/v1/jobs/start",
                             json={"action_id": "pipeline", "pipeline_id": "dag_cancel"})
            assert r.status_code == 202, r.text
            job_id = r.json()["job"]["job_id"]
            await c.post(f"/api/v1/jobs/{job_id}/cancel")
            await _async_wait_terminal(app.state.job_runner, job_id, timeout=90)
            while not _journal_events(ws) or _journal_events(ws)[-1]["action"] != "PIPELINE":
                await asyncio.sleep(0.05)

    asyncio.run(case())
    runner = app.state.job_runner
    job = list(runner.jobs.values())[-1]
    assert job.state == "cancelled", job.error
    assert not (ws / "gen" / "c.txt").exists()
    journal = _journal_events(ws)
    assert journal[-1]["action"] == "PIPELINE"
    assert journal[-1]["status"] == "PARTIAL"


def test_pipeline_job_single_flight(tmp_path):
    ws = _bootstrap(tmp_path)
    app = create_app(ws)
    spec = _dag_spec("dag_flight", [
        _node("slow", CODE_SLOW, {}, []),
        _node("n2", CODE_WRITE, {"out": "gen/z.txt", "content": "z"}, ["gen/z.txt"]),
    ], [["slow", "n2"]])

    async def case() -> None:
        async with _async_client(app) as c:
            assert (await c.post("/api/v1/pipelines", json={"spec": spec})).status_code == 201
            r = await c.post("/api/v1/jobs/start",
                             json={"action_id": "pipeline", "pipeline_id": "dag_flight"})
            assert r.status_code == 202, r.text
            job_id = r.json()["job"]["job_id"]
            r2 = await c.post("/api/v1/jobs/start",
                              json={"action_id": "pipeline", "pipeline_id": "dag_flight"})
            assert r2.status_code == 409, r2.text
            await _async_wait_terminal(app.state.job_runner, job_id, timeout=90)

    asyncio.run(case())
    runner = app.state.job_runner
    job = list(runner.jobs.values())[-1]
    assert job.state == "success", job.error
    assert (ws / "gen" / "z.txt").exists()