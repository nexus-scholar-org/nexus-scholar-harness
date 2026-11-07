"""M6-beta: what a console job runs with (review U-1, T-P1-4).

- Prepare's batch size reaches the job (the dialog promised a size the job
  ignored: it always prepared batches of 20).
- A job never imports code from the workspace folder: it runs with the
  workspace as its folder, and `python -m` puts the folder first on sys.path,
  so a shared workspace holding `scholar_harness/` would run its own code.
- A job does not inherit the console's bearer token.
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scholar_harness.console.serve import create_app
from scholar_harness.console.runtimes.actions import executable_argv, get_action, render_command
from scholar_harness.console.runtimes.job_runner import JobRunner, job_environment

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "workspaces" / "golden-uav-30"
BASE = "/api/v1/screening"
DESKTOP = "desktop-token"


def _golden(tmp_path: Path) -> Path:
    ws = tmp_path / "golden"
    shutil.copytree(GOLDEN, ws, ignore=shutil.ignore_patterns("screening", "jobs"))
    return ws


def _run_prepare(ws: Path, body: dict) -> tuple[int, dict]:
    with TestClient(create_app(ws, token=DESKTOP), base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {DESKTOP}"}) as client:
        response = client.post(f"{BASE}/prepare", json=body)
        if response.status_code != 202:
            return response.status_code, response.json()
        job_id = response.json()["job_id"]
        for _ in range(600):
            job = client.get(f"/api/v1/jobs/{job_id}").json()["job"]
            if job["state"] not in ("queued", "running"):
                break
            time.sleep(0.1)
        return 202, job


def test_prepare_honours_batch_size(tmp_path):
    ws = _golden(tmp_path)
    status, job = _run_prepare(ws, {"batch_size": 10})
    assert status == 202 and job["state"] == "success", job
    batches = sorted((ws / "literature" / "screening").glob("batch_[0-9][0-9][0-9].json"))
    assert len(batches) == 3


@pytest.mark.parametrize("size", [4, 101])
def test_prepare_refuses_a_batch_size_out_of_bounds(tmp_path, size):
    ws = _golden(tmp_path)
    status, body = _run_prepare(ws, {"batch_size": size})
    assert (status, body["detail"]["code"]) == (422, "BATCH_SIZE_INVALID")
    assert not (ws / "literature" / "screening").exists()


def test_jobs_do_not_import_from_the_workspace(tmp_path):
    ws = tmp_path / "shared workspace"
    planted = ws / "scholar_harness"
    planted.mkdir(parents=True)
    marker = tmp_path / "planted-code-ran"
    (planted / "__init__.py").write_text(f"open({str(marker)!r}, 'w').write('ran')\n", encoding="utf-8")
    argv = executable_argv(render_command(get_action("screen_prepare"), workspace=str(ws)))
    assert argv[:2] == [sys.executable, "-P"]
    subprocess.run([*argv[:4], "--help"], cwd=ws, capture_output=True, timeout=120, check=False)
    assert not marker.exists()


def test_jobs_do_not_inherit_the_console_token(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_CONSOLE_TOKEN", "secret-launch-token")
    monkeypatch.setenv("NEXUS_UNRELATED", "kept")
    env = job_environment()
    assert "NEXUS_CONSOLE_TOKEN" not in env
    assert env["NEXUS_UNRELATED"] == "kept"

    seen: dict = {}

    async def fake_exec(*argv, **kwargs):
        seen.update(kwargs)
        raise RuntimeError("stop before running")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    runner = JobRunner(_golden(tmp_path))
    with pytest.raises(RuntimeError, match="stop before running"):
        asyncio.run(runner.start("screen_prepare"))
    assert "NEXUS_CONSOLE_TOKEN" not in seen["env"]


def test_a_free_text_query_cannot_become_an_option():
    command = render_command(get_action("discovery"), workspace="ws", query="--help")
    assert command[command.index("--help") - 1] == "--"
