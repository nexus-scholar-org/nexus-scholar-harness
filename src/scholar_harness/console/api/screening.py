"""Screening decision writer (SPECS §3, §7, §8).

`POST /api/v1/screening/batch/{n}/decisions` writes the canonical
`batch_NNN_decisions.json` in the §7 wrapper shape the agent handoff expects:

    {"batch": n, "decisions": [...], "reviewed_by": "...", "timestamp": "..."}

Dual-compatibility: each decision accepts `study_id` or `workspace_id`, and
`cmd_collect` (agent_screen.py) accepts both the wrapper and the legacy raw
array, so GUI-written and agent-written files stay interchangeable.

All writes are atomic: `<file>.tmp-<uuid>` then `os.replace`, followed by one
append-only audit journal event (SPECS §8).
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, field_validator

from .audit import log_event

router = APIRouter(prefix="/api/v1/screening", tags=["screening"])

_DECISION_CODES = ("INCLUDE", "EXCLUDE")
_CONFIDENCE_WORDS = {"high": 0.9, "medium": 0.7, "low": 0.5}


class Decision(BaseModel):
    model_config = ConfigDict(extra="ignore")

    workspace_id: str | None = None
    study_id: str | None = None
    decision: str
    confidence: float | str = 0.8
    matched_inclusion_criteria: list[str] = []
    violated_exclusion_criteria: list[str] = []
    relevant_rqs: list[str] = []
    screening_reasoning: str = ""

    @field_validator("decision")
    @classmethod
    def _decision_upper(cls, v: str) -> str:
        raw = (v or "").strip().upper()
        if raw not in _DECISION_CODES:
            raise ValueError(f"decision must be INCLUDE or EXCLUDE, got {v!r}")
        return raw

    @property
    def resolved_id(self) -> str:
        return self.workspace_id or self.study_id or ""

    def to_record(self) -> dict[str, Any]:
        confidence = self.confidence
        if isinstance(confidence, str):
            confidence = _CONFIDENCE_WORDS.get(confidence.strip().lower(), 0.8)
        c = float(confidence)
        if not 0 <= c <= 1:
            raise ValueError(f"confidence must be in [0,1], got {confidence!r}")
        return {
            "workspace_id": self.resolved_id,
            "decision": self.decision,
            "confidence": c,
            "matched_inclusion_criteria": list(self.matched_inclusion_criteria),
            "violated_exclusion_criteria": list(self.violated_exclusion_criteria),
            "relevant_rqs": list(self.relevant_rqs),
            "screening_reasoning": self.screening_reasoning
            or f"{self.decision.lower()} during console verification review",
        }


class DecisionsBody(BaseModel):
    model_config = ConfigDict(extra="ignore")

    batch: int | None = None
    decisions: list[Decision]
    reviewed_by: str = "console"
    timestamp: str | None = None


def _batch_file(ws: Path, n: int) -> Path:
    return ws / "literature" / "screening" / f"batch_{n:03d}.json"


def _atomic_write_json(path: Path, payload: Any) -> None:
    tmp = path.with_name(path.name + f".tmp-{uuid.uuid4().hex[:8]}")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


@router.post("/batch/{n}/decisions", status_code=200)
def post_batch_decisions(body: DecisionsBody, n: int, request: Request) -> dict[str, Any]:
    ws: Path = request.app.state.workspace
    batch_path = _batch_file(ws, n)
    if not batch_path.is_file():
        raise HTTPException(status_code=404, detail=f"missing file: literature/screening/batch_{n:03d}.json")

    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    known_ids = {str(p.get("workspace_id", "")) for p in batch.get("papers", [])}
    known_ids.discard("")

    if body.batch is not None and body.batch != n:
        raise HTTPException(status_code=400, detail=f"body batch={body.batch} disagrees with path batch={n}")

    if not body.decisions:
        raise HTTPException(status_code=400, detail="decisions list must not be empty")

    records: list[dict[str, Any]] = []
    unknown: list[str] = []
    for dec in body.decisions:
        try:
            record = dec.to_record()
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=f"invalid decision: {exc}") from exc
        if record["workspace_id"] not in known_ids:
            unknown.append(record["workspace_id"])
        records.append(record)

    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"decisions reference unknown workspace_ids (not in batch {n}): {sorted(set(unknown))}",
        )

    timestamp = body.timestamp or datetime.now(UTC).isoformat()
    payload = {
        "batch": n,
        "decisions": records,
        "reviewed_by": body.reviewed_by,
        "timestamp": timestamp,
    }

    decisions_file = ws / "literature" / "screening" / f"batch_{n:03d}_decisions.json"
    _atomic_write_json(decisions_file, payload)

    inc = sum(1 for r in records if r["decision"] == "INCLUDE")
    exc = len(records) - inc
    log_event(
        workspace=ws,
        action="SCREEN_DECISIONS",
        description=f"Saved {len(records)} screening decisions for batch {n} ({inc} INCLUDE / {exc} EXCLUDE)",
        inputs=[batch_path.name],
        outputs=[decisions_file.name],
        parameters={"batch": n, "reviewed_by": body.reviewed_by},
        metrics={"included": inc, "excluded": exc, "total": len(records)},
    )

    return {"batch": n, "decisions_written": len(records), "decisions_file": decisions_file.name}