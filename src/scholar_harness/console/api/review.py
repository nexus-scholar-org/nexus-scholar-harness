"""``GET /api/v1/review/next-step``: the next-step bar of a workspace (M10b Part C, ``04-next-step``).

Workspace-free: with no workspace open it answers the state ``NO_REVIEW``
(not ``409 WORKSPACE_NOT_VALID``). A pure read: no ETag, no journal row, no file
written. The builder is ``console/next_step.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request

from ...screening.read_store import display_route
from .. import next_step

router = APIRouter(prefix="/api/v1/review", tags=["review"])


def _listing_empty(request: Request) -> bool:
    from scholar_harness.workspace import catalog

    try:
        root = request.app.state.workspaces_root
        source = getattr(request.app.state, "workspaces_root_source", "default")
        return not catalog.listing(root, source, None)["items"]
    except Exception:  # noqa: BLE001 - an unreadable root lists nothing; the bar still answers
        return True


@router.get("/next-step")
@display_route
def review_next_step(request: Request) -> dict[str, Any]:
    ws = getattr(request.app.state, "workspace", None)
    if ws is None:
        return next_step.no_review(_listing_empty(request))
    ws = Path(ws)
    discovery = getattr(request.app.state, "discovery_jobs", None)
    active = discovery.active(ws) if discovery is not None else None
    runner = getattr(request.app.state, "job_runner", None)
    jobs = [j.to_dict() for j in runner.jobs.values()] if runner is not None else None
    return next_step.build_workspace(ws, active=active, screening_jobs=jobs)
