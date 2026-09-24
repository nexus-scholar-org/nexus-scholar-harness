"""Agent Handoff Protocol — Phase state machine and supervisor loop (F3).

Implements the state-file contract, phase detection, and supervisor loop
that automatically advances workspaces through the systematic review phases.

See ``specs/handoff/handoff_spec.md`` for the full
specification.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Phase enum
# ---------------------------------------------------------------------------


class HandoffPhase(str, Enum):
    """Canonical phase identifiers for the systematic review pipeline."""

    INCEPTION = "INCEPTION"
    SCREENING = "SCREENING"
    EXTRACTION = "EXTRACTION"
    GRAPH = "GRAPH"
    SYNTHESIS = "SYNTHESIS"
    CRITIQUE = "CRITIQUE"
    COMPLETE = "COMPLETE"


# Phase ordering for sequence checks
PHASE_ORDER: list[HandoffPhase] = [
    HandoffPhase.INCEPTION,
    HandoffPhase.SCREENING,
    HandoffPhase.EXTRACTION,
    HandoffPhase.GRAPH,
    HandoffPhase.SYNTHESIS,
    HandoffPhase.CRITIQUE,
    HandoffPhase.COMPLETE,
]

# Mapping from phase enum name to its string value for JSON round-tripping
_PHASE_BY_NAME: dict[str, HandoffPhase] = {p.name: p for p in PHASE_ORDER}
_PHASE_BY_VALUE: dict[str, HandoffPhase] = {p.value: p for p in PHASE_ORDER}


# ---------------------------------------------------------------------------
# Trigger files
# ---------------------------------------------------------------------------

PHASE_TRIGGERS: dict[HandoffPhase, list[Path]] = {
    HandoffPhase.INCEPTION: [Path("intent.json")],
    HandoffPhase.SCREENING: [Path("literature") / "included.json"],
    HandoffPhase.EXTRACTION: [
        Path("literature") / "extraction" / "merged" / "records.json"
    ],
    HandoffPhase.GRAPH: [Path("literature") / "knowledge_graph.json"],
    HandoffPhase.SYNTHESIS: [Path("synthesis") / "consensus.json"],
    HandoffPhase.CRITIQUE: [Path("phase4") / "methodological_critique.md"],
    HandoffPhase.COMPLETE: [],
}


# ---------------------------------------------------------------------------
# State dataclass
# ---------------------------------------------------------------------------


@dataclass
class HandoffState:
    """Persistent state for the agent handoff protocol."""

    current_phase: HandoffPhase = HandoffPhase.INCEPTION
    completed_phases: list[HandoffPhase] = field(default_factory=list)
    workspace_dir: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.updated_at:
            self.updated_at = datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Load / save state
# ---------------------------------------------------------------------------


def _state_file(workspace_dir: Path) -> Path:
    return workspace_dir / "handoff_state.json"


def load_handoff_state(workspace_dir: Path) -> HandoffState:
    """Read ``handoff_state.json`` or return a default initial state."""
    sf = _state_file(workspace_dir)
    if not sf.is_file():
        return HandoffState(
            current_phase=HandoffPhase.INCEPTION,
            completed_phases=[],
            workspace_dir=str(workspace_dir.resolve()),
            updated_at=datetime.now(UTC).isoformat(),
        )
    try:
        data = json.loads(sf.read_text(encoding="utf-8"))
        current = _PHASE_BY_VALUE.get(
            data.get("current_phase", "INCEPTION"), HandoffPhase.INCEPTION
        )
        completed = []
        for name in data.get("completed_phases", []):
            ph = _PHASE_BY_VALUE.get(name) or _PHASE_BY_NAME.get(name)
            if ph:
                completed.append(ph)
        return HandoffState(
            current_phase=current,
            completed_phases=completed,
            workspace_dir=data.get("workspace_dir", str(workspace_dir.resolve())),
            updated_at=data.get("updated_at", datetime.now(UTC).isoformat()),
        )
    except (json.JSONDecodeError, KeyError) as exc:
        logger.warning("Malformed handoff_state.json, returning current state: %s", exc)
        return HandoffState(
            current_phase=HandoffPhase.INCEPTION,
            completed_phases=[],
            workspace_dir=str(workspace_dir.resolve()),
        )


def save_handoff_state(state: HandoffState, workspace_dir: Path) -> Path:
    """Atomic write of ``handoff_state.json``."""
    state.updated_at = datetime.now(UTC).isoformat()
    sf = _state_file(workspace_dir)
    sf.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "current_phase": state.current_phase.value,
        "completed_phases": [p.value for p in state.completed_phases],
        "workspace_dir": state.workspace_dir,
        "updated_at": state.updated_at,
    }
    tmp = sf.with_suffix(sf.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, sf)
    return sf


# ---------------------------------------------------------------------------
# Phase transition logic
# ---------------------------------------------------------------------------


def advance_phase(state: HandoffState, next_phase: HandoffPhase) -> HandoffState:
    """Move current phase to completed, set next_phase as current."""
    if state.current_phase not in state.completed_phases:
        state.completed_phases.append(state.current_phase)
    state.current_phase = next_phase
    state.updated_at = datetime.now(UTC).isoformat()
    return state


def detect_completed_phases(workspace_dir: Path) -> set[HandoffPhase]:
    """Scan workspace filesystem for trigger files and return completed phases."""
    completed: set[HandoffPhase] = set()
    for phase, triggers in PHASE_TRIGGERS.items():
        if not triggers:
            continue
        all_exist = all((workspace_dir / t).is_file() for t in triggers)
        if all_exist:
            completed.add(phase)
    return completed


def next_actionable_phase(
    state: HandoffState, completed: set[HandoffPhase]
) -> HandoffPhase | None:
    """Return the next phase to advance to, given detected-completed phases.

    The supervisor detects which phases have their trigger files on disk
    (``completed``), then calls this function to determine whether the
    state machine should advance.

    Logic:
    1. If ``state.current_phase`` is in ``completed`` and not yet in
       ``state.completed_phases``, the current phase just finished →
       return the next phase in the pipeline.
    2. If ``state.current_phase`` is already in ``state.completed_phases``
       (already advanced past), look for the first later phase whose
       triggers are also detected but not yet advanced past.
    3. If nothing is actionable, return ``None`` (NOOP).

    This ensures:
    - An empty workspace (no triggers) → ``None`` (NOOP).
    - INCEPTION triggers detected → returns ``SCREENING``.
    - SCREENING triggers also detected after that → returns ``EXTRACTION``.
    - All phases complete → ``None`` (terminal NOOP).
    """
    # Find the current position in the pipeline
    current_idx = PHASE_ORDER.index(state.current_phase)

    # Walk forward from current position looking for the first
    # phase that has triggers detected but is not yet advanced past.
    for i in range(current_idx, len(PHASE_ORDER)):
        phase = PHASE_ORDER[i]
        if phase in state.completed_phases:
            continue
        if phase in completed:
            # This phase's triggers are detected — it should be advanced past.
            # Return the NEXT phase in the sequence (the target after advancing).
            next_idx = i + 1
            if next_idx < len(PHASE_ORDER):
                return PHASE_ORDER[next_idx]
            return None  # past the end

    # Also check if current_phase itself is not completed and has no triggers
    # but a LATER phase does (handles the case where state.current_phase is
    # INCEPTION but only INCEPTION triggers exist — INCEPTION is detected,
    # so it should be found above). If we reach here, nothing new is detected.
    return None


# ---------------------------------------------------------------------------
# Supervisor run
# ---------------------------------------------------------------------------


def run_supervisor_once(workspace_dir: Path) -> dict[str, Any]:
    """One-shot supervisor: detect → advance → save → log.

    Returns a summary dict with keys: ``action``, ``from_phase``, ``to_phase``,
    ``completed_phases``, ``state_file``.
    """
    ws = workspace_dir.resolve()
    if not ws.is_dir():
        return {
            "action": "NOOP",
            "reason": f"Workspace not found: {workspace_dir}",
            "completed_phases": [],
        }

    state = load_handoff_state(ws)

    if state.current_phase == HandoffPhase.COMPLETE:
        return {
            "action": "NOOP",
            "reason": "All phases complete",
            "from_phase": state.current_phase.value,
            "to_phase": state.current_phase.value,
            "completed_phases": [p.value for p in state.completed_phases],
        }

    completed = detect_completed_phases(ws)
    target = next_actionable_phase(state, completed)

    if target is None:
        return {
            "action": "NOOP",
            "reason": "No actionable phase found",
            "from_phase": state.current_phase.value,
            "to_phase": state.current_phase.value,
            "completed_phases": [p.value for p in state.completed_phases],
        }

    from_phase = state.current_phase
    state = advance_phase(state, target)
    save_handoff_state(state, ws)

    # Log audit event
    _log_audit_event(
        ws,
        action="PHASE_ADVANCE",
        agent="supervisor",
        description=f"Phase advanced from {from_phase.value} to {state.current_phase.value}",
        inputs=[],
        outputs=[str(_state_file(ws))],
        metrics={
            "from_phase": from_phase.value,
            "to_phase": state.current_phase.value,
            "completed_phases": [p.value for p in state.completed_phases],
        },
    )

    return {
        "action": "ADVANCED",
        "from_phase": from_phase.value,
        "to_phase": state.current_phase.value,
        "completed_phases": [p.value for p in state.completed_phases],
        "state_file": str(_state_file(ws)),
    }


def _log_audit_event(
    workspace_dir: Path,
    action: str,
    agent: str,
    description: str,
    inputs: list[str],
    outputs: list[str],
    metrics: dict[str, Any],
) -> None:
    """Append one audit event to ``audit/journal.jsonl``."""
    audit_file = workspace_dir / "audit" / "journal.jsonl"
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
        "status": "SUCCESS",
    }

    with open(audit_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
