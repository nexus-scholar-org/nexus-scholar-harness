"""Asyncio subprocess job runner with lifecycle tracking and journal writes.

A job maps a console action to a `uv run` subprocess (job_runner executes
argv directly; the actions table in runtimes/actions.py is the source of the
command). Lifecycle: queued -> running -> success|failed|cancelled.

On completion the runner appends a canonical event to `audit/journal.jsonl`
using the same schema as `.agents/skills/workspace-manager/scripts/log_event.py`
so that agents and the console agree on what happened.
"""

from __future__ import annotations

import asyncio
import json
import logging
import signal
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .actions import Action, get_action, render_command

logger = logging.getLogger(__name__)

JOB_RUN_DIR = ".harness-console"
DEFAULT_TIMEOUT_S = 30 * 60
LONG_RUNNING_ACTIONS = {"download", "extract"}
LONG_RUNNING_TIMEOUT_S = 12 * 60 * 60


class Job:
    """Mutable job state shared across the runner and the API."""

    def __init__(self, job_id: str, action_id: str, command: list[str], cwd: Path, timeout_s: int):
        self.job_id = job_id
        self.action_id = action_id
        self.command = command
        self.cwd = cwd
        self.timeout_s = timeout_s
        self.state = "queued"
        self.pid: int | None = None
        self.exit_code: int | None = None
        self.started_at: str | None = None
        self.finished_at: str | None = None
        self.log_path: str | None = None
        self.journal_event_id: str | None = None
        self.error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "action_id": self.action_id,
            "state": self.state,
            "pid": self.pid,
            "exit_code": self.exit_code,
            "command": self.command,
            "cwd": str(self.cwd),
            "log_path": self.log_path,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "journal_event_id": self.journal_event_id,
            "error": self.error,
        }


class JobRunner:
    """Executes actions as asyncio subprocesses; single-flight per action."""

    def __init__(self, workspace: Path, on_event: Any | None = None):
        self.workspace = Path(workspace).resolve()
        self.on_event = on_event
        self.jobs: dict[str, Job] = {}
        self._processes: dict[str, asyncio.subprocess.Process] = {}
        self._active_actions: set[str] = set()
        self._lock = asyncio.Lock()

    def _publish(self, job: Job) -> None:
        if self.on_event is not None:
            self.on_event({"event": "job", "data": {"job": job.to_dict()}})

    def _publish_log(self, job_id: str, line: str) -> None:
        if self.on_event is not None:
            self.on_event({"event": "log", "data": {"job_id": job_id, "line": line}})

    def _job_dir(self, job_id: str) -> Path:
        return self.workspace / JOB_RUN_DIR / "jobs" / job_id

    def _timeout_for(self, action_id: str) -> int:
        if action_id in LONG_RUNNING_ACTIONS:
            return LONG_RUNNING_TIMEOUT_S
        return DEFAULT_TIMEOUT_S

    async def start(
        self,
        action_id: str,
        query: str | None = None,
        workspace: str | None = None,
    ) -> Job:
        """Create (queued) and spawn a job for the given action. Single-flight."""
        async with self._lock:
            if action_id in self._active_actions:
                raise JobConflict(action_id)

            action: Action = get_action(action_id)
            ws = workspace or str(self.workspace)
            command = render_command(action, workspace=ws, query=query)

            job_id = f"job_{uuid.uuid4().hex[:8]}"
            job = Job(
                job_id=job_id,
                action_id=action.action_id,
                command=command,
                cwd=self.workspace,
                timeout_s=self._timeout_for(action.action_id),
            )
            job.log_path = str(self._job_dir(job_id) / "stdout.log")
            self.jobs[job_id] = job
            self._active_actions.add(action_id)

        # Spawn outside the lock so long setup never blocks single-flight checks.
        self._job_dir(job_id).mkdir(parents=True, exist_ok=True)
        job.started_at = _utc_now()
        job.state = "running"
        job.error = None
        self._publish(job)
        proc = await asyncio.create_subprocess_exec(
            *command,
            cwd=str(self.workspace),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        job.pid = proc.pid
        self._processes[job_id] = proc

        # Drain output to the job log, then finalize.
        asyncio.create_task(self._run_to_completion(job, proc))
        return job

    async def _run_to_completion(self, job: Job, proc: asyncio.subprocess.Process) -> None:
        try:
            chunks: list[bytes] = []
            async for line in proc.stdout:
                chunks.append(line)
                if job.state != "cancelled":
                    self._publish_log(job.job_id, line.decode(errors="replace").rstrip("\r\n"))
            try:
                exit_code = await asyncio.wait_for(proc.wait(), timeout=job.timeout_s)
            except TimeoutError:
                self._terminate(job, proc)
                exit_code = -signal.SIGTERM
                job.error = f"timed out after {job.timeout_s}s"
                job.state = "failed"
        except Exception as exc:  # noqa: BLE001
            exit_code = -1
            job.error = str(exc)
            job.state = "failed"

        # Write the log file before finalizing state.
        try:
            log = self._job_dir(job.job_id) / "stdout.log"
            log.write_bytes(b"".join(chunks))
        except Exception:
            logger.debug("failed to persist job stdout for %s", job.job_id, exc_info=True)

        if job.state != "failed":
            job.state = "success" if exit_code == 0 else "failed"
        job.exit_code = exit_code
        job.finished_at = _utc_now()

        # Journal the result.
        status = "SUCCESS" if job.state == "success" else ("PARTIAL" if job.state == "cancelled" else "FAILED")
        event_id = _journal_event(
            workspace=self.workspace,
            action_id=job.action_id,
            description=f"{job.action_id} job {job.job_id} finished with state '{job.state}'",
            status=status,
            inputs=[job.action_id],
            outputs=[job.job_id, f"exit={exit_code}"],
            metrics={"exit_code": exit_code, "state": job.state},
        )
        job.journal_event_id = event_id

        async with self._lock:
            self._active_actions.discard(job.action_id)
            self._processes.pop(job.job_id, None)
        self._publish(job)

    def _terminate(self, job: Job, proc: asyncio.subprocess.Process) -> None:
        try:
            proc.terminate()
        except ProcessLookupError:
            return
        try:
            # Grace period, then SIGKILL.
            asyncio.get_running_loop().call_later(5, self._kill, job, proc)
        except RuntimeError:
            pass

    def _kill(self, job: Job, proc: asyncio.subprocess.Process) -> None:
        try:
            proc.kill()
        except ProcessLookupError:
            pass

    async def cancel(self, job_id: str) -> Job:
        job = self.jobs.get(job_id)
        if job is None:
            raise KeyError(job_id)
        if job.state not in ("queued", "running"):
            return job
        proc = self._processes.get(job_id)
        if proc is not None and proc.returncode is None:
            self._terminate(job, proc)
            try:
                await asyncio.wait_for(proc.wait(), timeout=10)
            except TimeoutError:
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass
                await proc.wait()
        job.state = "cancelled"
        job.exit_code = -signal.SIGTERM
        job.finished_at = _utc_now()
        _journal_event(
            workspace=self.workspace,
            action_id=job.action_id,
            description=f"{job.action_id} job {job.job_id} cancelled",
            status="PARTIAL",
            inputs=[job.action_id],
            outputs=[job.job_id],
        )
        async with self._lock:
            self._active_actions.discard(job.action_id)
            self._processes.pop(job_id, None)
        self._publish(job)
        return job

    def get(self, job_id: str) -> Job:
        return self.jobs[job_id]


class JobConflict(Exception):
    """Raised when an action is already running (single-flight per action)."""


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _journal_event(
    workspace: Path,
    action_id: str,
    description: str,
    status: str,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    metrics: dict[str, Any] | None = None,
) -> str:
    """Append a canonical event to audit/journal.jsonl; return its event_id."""
    try:
        audit_dir = workspace / "audit"
        audit_dir.mkdir(parents=True, exist_ok=True)
        journal = audit_dir / "journal.jsonl"
        now = datetime.now(UTC)
        event_id = f"EVT-{now.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        event = {
            "timestamp": now.isoformat(),
            "event_id": event_id,
            "action": action_id.upper(),
            "agent_or_tool": "scholar-harness-console",
            "description": description,
            "parameters": {},
            "inputs": inputs or [],
            "outputs": outputs or [],
            "metrics": metrics or {},
            "status": status.upper(),
        }
        with open(journal, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event_id
    except Exception:  # noqa: BLE001 - journaling failure must not crash jobs
        return f"EVT-{uuid.uuid4().hex[:12]}"
