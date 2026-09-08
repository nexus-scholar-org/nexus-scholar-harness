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

import importlib.util
import json
import logging
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

REPO_ROOT = Path(__file__).resolve().parents[4]
LOG_EVENT_SCRIPT = REPO_ROOT / ".agents" / "skills" / "workspace-manager" / "scripts" / "log_event.py"

_INDEX_MD_REFRESH: Any | None = None


def _load_index_refresher():
    """Lazily import refresh_index_md from the workspace-manager skill."""
    global _INDEX_MD_REFRESH
    if _INDEX_MD_REFRESH is not None:
        return _INDEX_MD_REFRESH
    try:
        spec = importlib.util.spec_from_file_location("log_event", LOG_EVENT_SCRIPT)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _INDEX_MD_REFRESH = module.refresh_index_md
    except Exception:
        logger.debug("workspace-manager skill unavailable; skipping INDEX.md refresh", exc_info=True)
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
    """Append a canonical event; update project.json; refresh INDEX.md."""
    ws = Path(workspace).resolve()
    audit_dir = ws / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    journal = audit_dir / "journal.jsonl"
    now = datetime.now(UTC)

    event = {
        "timestamp": now.isoformat(),
        "event_id": f"EVT-{now.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}",
        "action": action.upper(),
        "agent_or_tool": agent,
        "description": description,
        "parameters": parameters or {},
        "inputs": inputs or [],
        "outputs": outputs or [],
        "metrics": metrics or {},
        "status": status.upper(),
    }

    # Append (append-only: a fresh OS append, never a read-modify-write).
    with open(journal, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    manifest_path = ws / "project.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["updated_at"] = now.isoformat()
            if metrics:
                for key, value in metrics.items():
                    if key in manifest.get("stats", {}):
                        manifest["stats"][key] = value
            tmp = manifest_path.with_name(manifest_path.name + f".tmp-{uuid.uuid4().hex[:8]}")
            tmp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(manifest_path)
        except Exception:
            logger.debug("project.json refresh failed", exc_info=True)

    if refresh_index:
        refresh_index_md(ws)

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