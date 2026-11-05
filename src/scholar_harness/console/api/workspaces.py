"""Workspaces routes (M5-slim; `docs/architecture/workspaces-api.md` §3).

List the workspaces under the root, create one, and open one. Open never
rebinds this app: it answers, then asks the launcher (`app.state.on_open`) to
restart the server on the other folder, so nothing crosses workspaces.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from scholar_harness.workspace import catalog

router = APIRouter(prefix="/api/v1", tags=["workspaces"])


def _error(exc: catalog.WorkspaceRefused) -> HTTPException:
    detail: dict[str, Any] = {"code": exc.code, "message": exc.message}
    if exc.details:
        detail["details"] = exc.details
    return HTTPException(status_code=exc.status, detail=detail)


def _root(request: Request) -> tuple[Path, str]:
    return request.app.state.workspaces_root, request.app.state.workspaces_root_source


@router.get("/workspaces")
def list_workspaces(request: Request, include_invalid: bool = False) -> dict[str, Any]:
    root, source = _root(request)
    try:
        return catalog.listing(root, source, request.app.state.workspace, include_invalid=include_invalid)
    except catalog.WorkspaceRefused as exc:
        raise _error(exc) from exc


class CreateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str


@router.post("/workspaces", status_code=201)
def create_workspace(body: CreateBody, request: Request) -> dict[str, Any]:
    root, _source = _root(request)
    try:
        return catalog.create(root, body.title.strip())
    except catalog.WorkspaceRefused as exc:
        raise _error(exc) from exc


class OpenBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slug: str


@router.post("/workspaces/open")
def open_workspace(body: OpenBody, request: Request, background: BackgroundTasks) -> JSONResponse:
    root, _source = _root(request)
    current: Path | None = request.app.state.workspace
    try:
        target = catalog.check_open(root, body.slug, current)
    except catalog.WorkspaceRefused as exc:
        raise _error(exc) from exc
    if current is not None and target == current.resolve():
        return JSONResponse({"slug": target.name, "path": str(target), "restarting": False}, status_code=200)
    on_open = getattr(request.app.state, "on_open", None)
    if on_open is None:
        raise HTTPException(
            status_code=501,
            detail={"code": "RESTART_UNSUPPORTED", "message": "this server was not started by `nexus-scholar ui`, so it cannot restart on another workspace"},
        )
    # Answer first; the launcher stops this server and starts one on `target`.
    background.add_task(on_open, target)
    return JSONResponse({"slug": target.name, "path": str(target), "restarting": True}, status_code=202)
