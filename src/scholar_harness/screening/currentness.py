"""Published means current (M6-beta, decision 2026-11-07; review T-P1-1).

`require_current_generation` checks the publication against what it binds: the
batch files, the published outputs, the approval and the protocol. It does not
bind the decision files, so a decision made after publish left it CURRENT.
Export and methods already refused that case (`export._check_decisions_unchanged`).
This wrapper runs the same check for every caller that reports the status, so
one answer reaches the status route, Home, the workspaces list, export and
methods. Pure read; the authority gate itself is unchanged.
"""

from __future__ import annotations

from pathlib import Path

from scholar_harness.authority.generations import (
    GENERATION_STALE,
    CurrentnessResult,
    GenerationStatus,
    require_current_generation,
)


def screening_currentness(workspace: Path | str) -> CurrentnessResult:
    """The publication status, STALE when a decision changed after publish."""
    from .export import ExportRefused, load_published

    ws = Path(workspace)
    result = require_current_generation(ws)
    if result.status is not GenerationStatus.CURRENT or result.record is None:
        return result
    try:
        load_published(ws, purpose="status")
    except ExportRefused as exc:
        if exc.code != GENERATION_STALE:
            # A published file that cannot be read back is not current either.
            return CurrentnessResult(
                status=GenerationStatus.MISMATCHED,
                code=exc.code,
                message=exc.message,
                details={"generation_id": result.record.generation_id, **exc.details},
                record=result.record,
            )
        return CurrentnessResult(
            status=GenerationStatus.STALE,
            code=GENERATION_STALE,
            message=exc.message,
            details={"generation_id": result.record.generation_id, **exc.details},
            record=result.record,
        )
    return result
