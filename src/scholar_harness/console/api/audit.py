"""Audit journal writes + timeline (SPECS §3, §8; mirrors log_event.py).

The console's mutation endpoints route through `log_event()` so agent-driven
and console-driven events stay byte-compatible with
`.agents/skills/workspace-manager/scripts/log_event.py`:

  - event_id / timestamp are minted server-side (ED4: never trust the client
    for provenance fields),
  - the journal is append-only (a line per event, no rewrites),
  - `project.json` gets `updated_at` refreshed,
  - `INDEX.md` is regenerated through the workspace-manager skill so the
    heartbeat mtime drives the SSE change-tick for every console mutation.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

REPO_ROOT = Path(__file__).resolve().parents[4]
LOG_EVENT_SCRIPT = (
    REPO_ROOT / ".agents" / "skills" / "workspace-manager" / "scripts" / "log_event.py"
)

_INDEX_MD_REFRESH: Any | None = None


def _load_index_refresher():
    """Lazily resolve refresh_index_md through the neutral loader.

    Thin adapter over :func:`workspace.loader.load_index_refresher_uncached`
    (``NEXUS_SKILLS_SRC``/wheel/repo precedence, CWD-independent). The
    module-level ``_INDEX_MD_REFRESH`` cache is retained so existing
    fault-injection seams (``monkeypatch.setattr(console_audit,
    "_load_index_refresher", ...)``) keep working.
    """
    global _INDEX_MD_REFRESH
    if _INDEX_MD_REFRESH is not None:
        return _INDEX_MD_REFRESH
    try:
        from scholar_harness.workspace import loader as _neutral_loader

        refresher = _neutral_loader.load_index_refresher_uncached()
        _INDEX_MD_REFRESH = refresher if refresher is not None else False
    except Exception:
        logger.debug(
            "workspace-manager skill unavailable; skipping INDEX.md refresh",
            exc_info=True,
        )
        _INDEX_MD_REFRESH = False
    return _INDEX_MD_REFRESH or None


def refresh_index_md(workspace: Path) -> None:
    """Regenerate INDEX.md via the workspace-manager skill (best effort)."""
    refresher = _load_index_refresher()
    if refresher is None:
        return
    try:
        refresher(Path(workspace))
    except Exception:
        logger.debug("INDEX.md refresh failed", exc_info=True)


def log_event(
    workspace: Path,
    action: str,
    description: str,
    agent: str = "scholar-harness-console",
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    parameters: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    status: str = "SUCCESS",
    refresh_index: bool = True,
) -> dict[str, Any]:
    """Append a canonical event; update project.json; refresh INDEX.md.

    Thin adapter over :func:`workspace.audit.append_event` for the journal +
    manifest projection; INDEX refresh routes through the local
    :func:`refresh_index_md` so the existing best-effort/refresher-failure
    seam is preserved.
    """
    from scholar_harness.workspace.audit import append_event as _neutral_append

    event = _neutral_append(
        workspace,
        action,
        description,
        agent=agent,
        inputs=inputs,
        outputs=outputs,
        parameters=parameters,
        metrics=metrics,
        status=status,
        refresh_index=False,
    )
    if refresh_index:
        refresh_index_md(Path(workspace).resolve())
    return event


class NewEventBody(BaseModel):
    action: str
    description: str = ""
    agent_or_tool: str = "scholar-harness-console"
    inputs: list[str] | None = None
    outputs: list[str] | None = None
    parameters: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None
    status: str = "SUCCESS"


@router.post("/events", status_code=201)
def post_event(body: NewEventBody, request: Request) -> dict[str, Any]:
    event = log_event(
        workspace=request.app.state.workspace,
        action=body.action,
        description=body.description,
        agent=body.agent_or_tool,
        inputs=body.inputs,
        outputs=body.outputs,
        parameters=body.parameters,
        metrics=body.metrics,
        status=body.status,
    )
    return event
