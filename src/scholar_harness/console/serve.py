"""FastAPI application factory for the Harness Console server.

`scholar-harness serve --workspace <path>` runs this app over uvicorn
(loopback only by default). The app reads canonical workspace files and
dispatches mutations to kit CLIs via the job runner. All state is derived
from the workspace or the in-memory JobRunner — the API is stateless between
process restarts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import jobs as jobs_api
from .api import workspace as workspace_api
from .runtimes.job_runner import JobRunner

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(workspace: str | Path) -> FastAPI:
    ws = Path(workspace).resolve()
    if not ws.is_dir():
        raise ValueError(f"workspace path does not exist: {ws}")

    app = FastAPI(
        title="scholar-harness console",
        version="0.1.0",
        description="Local observability and job-control surface for the Nexus Scholar harness.",
    )

    broadcast = jobs_api.JobStreamBroadcast()

    def on_job_event(event: dict[str, Any]) -> None:
        broadcast.put(event)

    runner = JobRunner(ws, on_event=on_job_event)

    app.state.workspace = ws
    app.state.job_runner = runner
    app.state.job_broadcast = broadcast

    app.include_router(workspace_api.router)
    app.include_router(jobs_api.router)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "workspace": str(ws)}

    # Static console (visual prototype). In production the vendored JS lives
    # under static/lib/; the app currently serves the committed index.html.
    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return app
