"""Global change-tick SSE stream (SPECS section 8).

Cheap heartbeat: the mtime of `INDEX.md` (fallback `project.json`, then the
workspace directory) is the global change signal. The SPA keeps one EventSource
open and refetches the current screen on every tick, so it stays live while
agents edit the same files concurrently. No long-lived caches anywhere.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/v1/events", tags=["streams"])

HEARTBEAT_FILES = ("INDEX.md", "project.json")


def _heartbeat_mtime(workspace: Path) -> float | None:
    for name in HEARTBEAT_FILES:
        path = workspace / name
        if path.is_file():
            try:
                return path.stat().st_mtime
            except OSError:
                return None
    try:
        return workspace.stat().st_mtime
    except OSError:
        return None


def _tick_sse(ts: float | None, n: int) -> str:
    payload = {"ts": ts, "n": n}
    return f"event: tick\ndata: {json.dumps(payload)}\n\n"


async def gen_ticks(workspace: Path, interval: float = 2.0):
    """Yield SSE tick frames whenever the workspace heartbeat mtime changes.

    Emits an initial tick immediately, then `: keepalive` comments until the
    mtime changes. Bounded by the caller (the SPA can drop the connection
    at any time; a closed EventSource simply stops reading).
    """
    ws = Path(workspace).resolve()
    last = _heartbeat_mtime(ws)
    counter = 0
    yield _tick_sse(last, counter)
    while True:
        await asyncio.sleep(interval)
        counter += 1
        current = _heartbeat_mtime(ws)
        if current != last:
            last = current
            yield _tick_sse(current, counter)
        else:
            yield ": keepalive\n\n"


@router.get("/tick")
async def tick(request: Request) -> StreamingResponse:
    workspace: Path = request.app.state.workspace
    return StreamingResponse(gen_ticks(workspace), media_type="text/event-stream")