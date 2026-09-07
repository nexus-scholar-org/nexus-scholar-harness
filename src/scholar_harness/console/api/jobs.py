"""Job control + Server-Sent Events stream (SPECS §3, §6).

Endpoints:
  POST /api/v1/jobs/start  {action_id, query?, workspace?} -> {job}
  GET  /api/v1/jobs/{id}   -> job state
  POST /api/v1/jobs/{id}/cancel -> job state
  GET  /api/v1/jobs        -> all jobs (newest first)
  GET  /api/v1/jobs/{id}/stream -> SSE of lifecycle transitions
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..runtimes.job_runner import JobConflict, JobRunner

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


class StartJobBody(BaseModel):
    action_id: str
    query: str | None = None
    workspace: str | None = None


class JobStreamBroadcast:
    """Fan-out of lifecycle events to zero-or-more SSE subscribers."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()

    def put(self, event: dict[str, Any]) -> None:
        for q in list(self._subscribers):
            q.put_nowait(event)

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers.discard(q)


def _runner(request: Request) -> JobRunner:
    return request.app.state.job_runner


def _broadcast(request: Request) -> JobStreamBroadcast:
    return request.app.state.job_broadcast


def _sse(event: dict[str, Any]) -> str:
    return f"event: {event.get('event', 'update')}\ndata: {json.dumps(event.get('data', {}))}\n\n"


@router.post("/start", status_code=202)
async def start_job(body: StartJobBody, request: Request) -> dict[str, Any]:
    runner = _runner(request)
    try:
        job = await runner.start(body.action_id, query=body.query, workspace=body.workspace)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"unknown action: {exc}") from exc
    except JobConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _broadcast(request).put({"event": "sync", "data": {"job": job.to_dict()}})
    return {"job": job.to_dict()}


@router.get("")
def list_jobs(request: Request, limit: int = 50) -> dict[str, Any]:
    runner = _runner(request)
    jobs = sorted(runner.jobs.values(), key=lambda j: j.started_at or "", reverse=True)
    return {"total": len(jobs), "items": [j.to_dict() for j in jobs[:limit]]}


@router.get("/{job_id}")
def get_job(job_id: str, request: Request) -> dict[str, Any]:
    try:
        job = _runner(request).get(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"unknown job: {job_id}") from exc
    return {"job": job.to_dict()}


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str, request: Request) -> dict[str, Any]:
    try:
        job = await _runner(request).cancel(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"unknown job: {job_id}") from exc
    _broadcast(request).put({"event": "sync", "data": {"job": job.to_dict()}})
    return {"job": job.to_dict()}


@router.get("/{job_id}/stream")
async def job_stream(job_id: str, request: Request) -> StreamingResponse:
    runner = _runner(request)
    if job_id not in runner.jobs:
        raise HTTPException(status_code=404, detail=f"unknown job: {job_id}")

    broadcast = _broadcast(request)
    queue = broadcast.subscribe()

    async def event_gen():
        try:
            # Replay the current state first.
            yield _sse({"event": "snapshot", "data": {"job": runner.jobs[job_id].to_dict()}})
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30)
                except TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                data = msg.get("data", {})
                if data.get("job", {}).get("job_id") == job_id:
                    yield _sse(msg)
        finally:
            broadcast.unsubscribe(queue)

    return StreamingResponse(event_gen(), media_type="text/event-stream")
