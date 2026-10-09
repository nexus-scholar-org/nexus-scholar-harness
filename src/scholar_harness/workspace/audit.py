"""Neutral workspace audit service (HCM-02).

Sole owner of append-only journal discipline. Two entry points, both
transport-neutral (no FastAPI, no Typer, no console import):

* :func:`append_event` -- canonical writer (console/CLI/acceptance/index
  compatible): ``EVT-<ts>-<uuid6>`` provenance minted server-side,
  ``action``/``status`` uppercased, ``ensure_ascii=False`` journal line,
  atomic ``project.json`` projection (pre-existing stats keys only),
  best-effort ``INDEX.md`` refresh through the portable loader. Journal
  ``OSError`` propagates so acceptance maps it to ``ATOMIC_COMMIT_FAILED``;
  projection/INDEX failures are swallowed.

* :func:`append_legacy_event` -- orchestrator/handoff byte-compatible writer:
  preserves the observed ``hex(hash(action + description))[-6:]`` event-id
  scheme, no uppercasing, ``json.dumps`` default encoding, no manifest update,
  no INDEX refresh, returns ``None``. HCM-01 characterizes this odd scheme;
  HCM-02 preserves it and regression-tests it. Do not "normalize" it without a
  separate behavior-decision packet.

``refresh_index`` (best-effort, void) and ``refresh_index_atomic``
(orchestrator-compatible, backup/restore, ``bool``) share the portable loader
with injectable seams for hermetic tests. ``resolve_workspace`` implements the
strict ``audit_log`` slug/path policy (plain dirs refused, no ledger created).

Direction: contracts / screening / pipelines / console / CLI -> this service.
This module imports only ``loader``, ``manifest``, ``errors``, stdlib.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from . import loader as _loader
from .errors import NotWorkspaceError
from .manifest import update_manifest_for_event

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Workspace resolution (strict audit_log policy)
# ---------------------------------------------------------------------------


def resolve_workspace(project_path_or_slug: str | Path) -> Path:
    """Resolve a workspace by path or slug.

    Mirrors ``audit_log._resolve_workspace`` (the strict variant): the input is
    used directly when it is a directory holding ``project.json``; otherwise the
    CWD-relative ``workspaces/<slug>`` candidate is tried when it is an existing
    directory. A plain non-workspace dir or a missing target raises
    :class:`NotWorkspaceError` and must never gain an ``audit/`` ledger -- the
    deliberate divergence from the lenient ``log_event.py`` script, which would
    otherwise create one inside any plain dir.
    """
    path = Path(project_path_or_slug)
    if path.is_dir():
        if (path / "project.json").exists():
            return path
        raise NotWorkspaceError(str(project_path_or_slug))
    candidate = Path("workspaces") / str(project_path_or_slug)
    if candidate.is_dir():
        return candidate
    raise NotWorkspaceError(str(project_path_or_slug))


# ---------------------------------------------------------------------------
# INDEX refresh (best-effort vs atomic)
# ---------------------------------------------------------------------------


def refresh_index(
    workspace: Path | str,
    *,
    refresher: Callable[[Path], Any] | None = None,
) -> None:
    """Regenerate ``INDEX.md`` via the workspace-manager skill (best effort).

    Never raises: a missing skill or a raising renderer is swallowed with a
    debug log so the journal append it follows is never blocked (HC1-5).
    ``refresher`` injects the renderer for hermetic tests; when ``None`` the
    portable loader resolves it (``NEXUS_SKILLS_SRC``/wheel/repo).
    """
    ws = Path(workspace)
    fn = refresher
    if fn is None:
        fn = _loader.load_index_refresher_uncached()
    if fn is None:
        return
    try:
        fn(ws)
    except Exception:
        logger.debug("INDEX.md refresh failed", exc_info=True)


def refresh_index_atomic(
    workspace: Path | str,
    *,
    refresher: Callable[[Path], Any] | None = None,
) -> bool:
    """Regenerate ``INDEX.md`` with orchestrator backup/restore discipline.

    Byte/behavior-compatible with
    ``ResearchOrchestrator._refresh_index_md_atomic``: snapshots the previous
    file, restores it when the render raises or leaves an empty result without
    ``Project Index``, returns ``True`` only on a valid render, ``False``
    otherwise (including missing skill). Appends no journal row (HCM2-06).
    """
    ws = Path(workspace)
    fn = refresher
    if fn is None:
        fn = _loader.load_index_refresher_uncached()
    if fn is None:
        return False
    try:
        index_path = ws / "INDEX.md"
        backup: str | None = None
        if index_path.exists():
            backup = index_path.read_text(encoding="utf-8")

        fn(ws)

        rendered = index_path.read_text(encoding="utf-8")
        if not rendered.strip() or ("Project Index" not in rendered):
            if backup is not None:
                index_path.write_text(backup, encoding="utf-8")
            return False
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Canonical append (console/CLI/acceptance/index compatible)
# ---------------------------------------------------------------------------


def append_event(
    workspace: Path | str,
    action: str,
    description: str,
    *,
    agent: str = "scholar-harness",
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    parameters: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    status: str = "SUCCESS",
    refresh_index: bool = True,
    _refresher: Callable[[Path], Any] | None = None,
    _now: datetime | None = None,
) -> dict[str, Any]:
    """Append one canonical event; update ``project.json``; refresh ``INDEX.md``.

    Compatible with ``console.api.audit.log_event`` call sites (acceptance
    ``:196``/``:538``, index ``:895``, extraction ``:1454``, screening,
    pipelines): ``(workspace, action, description, *, agent, inputs, outputs,
    parameters, metrics, status, refresh_index)``. ``action``/``status`` are
    uppercased; ``event_id``/``timestamp`` are minted by the writer.

    Guarantees: append-only (fresh OS append, never read-modify-write);
    prior rows byte-preserved; exactly one whole JSON line per call;
    ``OSError`` from the journal append propagates (acceptance maps it to
    ``ATOMIC_COMMIT_FAILED`` with zero publication); manifest/INDEX failures
    are best-effort and never block the append.

    ``_refresher``/``_now`` are hermetic seams (tests only).
    """
    ws = Path(workspace).resolve()
    audit_dir = ws / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    journal = audit_dir / "journal.jsonl"
    now = _now if _now is not None else datetime.now(UTC)

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
    # OSError propagates -- acceptance relies on it for atomic rollback.
    with open(journal, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    update_manifest_for_event(ws, now_iso=now.isoformat(), metrics=metrics)

    if refresh_index:
        if _refresher is not None:
            try:
                _refresher(ws)
            except Exception:
                logger.debug("INDEX.md refresh failed", exc_info=True)
        else:
            refresh_index_no_fail(ws)

    return event


def refresh_index_no_fail(workspace: Path | str) -> None:
    """Best-effort INDEX refresh used by :func:`append_event` (no raise)."""
    refresh_index(workspace)


# Backwards/forwards-compatible alias: acceptance and pipeline-adjacent modules
# import ``log_event`` by that name so existing ``monkeypatch.setattr(...,
# "log_event", ...)`` fault-injection seams keep working after migration.
log_event = append_event


# ---------------------------------------------------------------------------
# Legacy append (orchestrator/handoff byte-compatible)
# ---------------------------------------------------------------------------


def append_legacy_event(
    workspace: Path | str,
    action: str,
    agent: str,
    description: str,
    inputs: list[str],
    outputs: list[str],
    metrics: dict[str, Any],
    status: str = "SUCCESS",
) -> None:
    """Append one legacy orchestrator/handoff event (byte-compatible).

    Replicates ``ResearchOrchestrator._log_audit_event`` / ``handoff._log_audit_event``
    exactly: ``hex(hash(action + description))[-6:]`` event-id limb (observed odd
    scheme, hash-randomized, preserved per HCM-02 packet), no uppercasing, plain
    ``json.dumps`` (default ``ensure_ascii``), no ``project.json`` update, no
    ``INDEX.md`` refresh, returns ``None``. ``OSError`` from the append
    propagates (no silent success).

    Handoff callers pass ``status="SUCCESS"`` explicitly (hardcoded
    SUCCESS-for-phase-advance, preserved); orchestrator callers pass through
    the observed ``status`` (a refused run must not log ``SUCCESS``).
    """
    ws = Path(workspace)
    audit_file = ws / "audit" / "journal.jsonl"
    audit_file.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_id": f"EVT-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{hex(hash(action + description))[-6:]}",
        "action": action,
        "agent_or_tool": agent,
        "description": description,
        "parameters": {},
        "inputs": inputs,
        "outputs": outputs,
        "metrics": metrics,
        "status": status,
    }

    with open(audit_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
