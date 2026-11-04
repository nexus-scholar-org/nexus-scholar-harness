"""Screening API, M1a routes (screening API contract §4).

Reads and writes over the decision-event log (`screening/events.py`) and the
proposal store (`screening/proposals.py`). Decisions enter only through
`POST /decisions/events`; each accepted request regenerates the affected
`batch_NNN_decisions.json` projections, which the existing collector,
acceptance and approval path consume unchanged.

Agent proposals are advice. With blinding on (the default), a proposal and
any view that reveals the agent's call are available only after the
researcher has decided that study (`PROPOSAL_HIDDEN`).
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from ...screening import events as ev
from ...screening import proposals as pr
from .. import refusals

router = APIRouter(prefix="/api/v1/screening", tags=["screening"])

MAX_EVENTS_PER_REQUEST = 200  # contract §9.4
SETTINGS_FILE = Path("literature") / "screening" / "settings.json"
DEFAULT_SETTINGS: dict[str, Any] = {
    "blinding": "reveal_after_decision",
    "mode": "human_sees_every_record",
    "sample_audit_size": None,
    "screener_id": "researcher:local",
}
VIEWS = ("needs_you", "proposal_ready", "no_proposal", "title_only", "decided")


def _error(status: int, code: str, message: str, **extra: Any) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message, **extra})


def _ws(request: Request) -> Path:
    return request.app.state.workspace


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _workspace_id(ws: Path) -> str:
    manifest = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    return str(manifest.get("registered_workspace_id") or manifest.get("project_id") or "")


def load_settings(ws: Path) -> dict[str, Any]:
    path = ws / SETTINGS_FILE
    stored = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    return {**DEFAULT_SETTINGS, **stored}


def _papers(ws: Path, context: ev.ScreeningContext) -> dict[str, dict[str, Any]]:
    """Record content from the prepared batch files, keyed by study id."""
    out: dict[str, dict[str, Any]] = {}
    for index in context.batches:
        path = ws / "literature" / "screening" / f"batch_{index:03d}.json"
        if path.is_file():
            for paper in json.loads(path.read_text(encoding="utf-8")).get("papers", []):
                out[str(paper["workspace_id"])] = paper
    return out


def _has_abstract(paper: dict[str, Any]) -> bool:
    abstract = str(paper.get("abstract") or "").strip()
    return bool(abstract) and abstract != "No abstract available."


def _state(ws: Path) -> tuple[ev.ScreeningContext, dict[str, Any], list[dict], dict[str, dict]]:
    if not (ws / "protocol.json").is_file():
        raise _error(409, refusals.SNAPSHOT_NOT_ACCEPTED, "no protocol.json in this workspace")
    context = ev.load_context(ws)
    if not context.batches:
        raise _error(409, refusals.SNAPSHOT_NOT_ACCEPTED, "no prepared batches; accept the corpus and prepare")
    settings = load_settings(ws)
    events = [e for e in ev.read_events(ws) if e.get("screener_id") == settings["screener_id"]]
    winners = {
        study: winner
        for study in context.study_batch
        if (winner := ev.winning_event(events, study, settings["screener_id"])) is not None
    }
    return context, settings, events, winners


@router.get("/summary")
def summary(request: Request) -> dict[str, Any]:
    ws = _ws(request)
    context, settings, events, winners = _state(ws)
    proposed = {p["study_id"] for p in pr.read_proposals(ws)}
    by_outcome = {"INCLUDE": 0, "EXCLUDE": 0, "MAYBE": 0}
    for winner in winners.values():
        by_outcome[winner["outcome"]] += 1
    open_conflicts = ev.conflicts(events)
    total = len(context.study_batch)
    return {
        "total": total,
        "decided": len(winners),
        "by_outcome": by_outcome,
        "agent_proposed": len(proposed & set(context.study_batch)),
        "needs_you": total - len(winners),
        "conflicts": len(open_conflicts),
        "lanes": {"agent": len(proposed), "you": len(winners), "second_screener": "PARKED"},
    }


@router.get("/queue")
def queue(
    request: Request,
    view: str = "needs_you",
    cursor: int = 0,
    limit: int = 50,
    order: str = "seeded",
) -> dict[str, Any]:
    if view not in VIEWS:
        raise _error(422, "INVALID_OUTPUT", f"view must be one of {VIEWS}")
    ws = _ws(request)
    context, settings, _events, winners = _state(ws)
    papers = _papers(ws, context)
    latest = {p["study_id"]: p for p in sorted(pr.read_proposals(ws), key=lambda p: p.get("created_at") or "")}
    order_ids = [s for index in sorted(context.batches) for s in context.batches[index].candidates]

    def keep(study: str) -> bool:
        decided = study in winners
        has_proposal = study in latest
        return {
            "needs_you": not decided,
            "proposal_ready": not decided and has_proposal,
            "no_proposal": not decided and not has_proposal,
            "title_only": not decided and not _has_abstract(papers.get(study, {})),
            "decided": decided,
        }[view]

    chosen = [s for s in order_ids if keep(s)]
    if order == "agent_uncertainty":
        # How unsure the agent was, never its call: Unclear drafts first, then
        # drafts with failed checks; the methods paragraph discloses this order.
        def unsure(study: str) -> tuple[int, int]:
            proposal = latest.get(study)
            if proposal is None:
                return (2, 0)
            failed = sum(1 for c in proposal.get("validators", []) if not c.get("ok"))
            return (0 if proposal.get("derived_outcome") == "MAYBE" else 1, -failed)

        chosen.sort(key=unsure)
    page = chosen[cursor : cursor + max(1, min(limit, 200))]
    items = [
        {
            "study_id": s,
            "title": papers.get(s, {}).get("title", ""),
            "batch_id": context.batches[context.study_batch[s]].batch_id,
            "has_proposal": s in latest,
            "decided": s in winners,
            "flags": [] if _has_abstract(papers.get(s, {})) else ["title_only"],
        }
        for s in page
    ]
    next_cursor = cursor + len(page) if cursor + len(page) < len(chosen) else None
    return {"items": items, "next_cursor": next_cursor}


@router.get("/records/{study_id}")
def record(study_id: str, request: Request) -> dict[str, Any]:
    ws = _ws(request)
    context, settings, events, winners = _state(ws)
    if study_id not in context.study_batch:
        raise _error(404, refusals.UNKNOWN_STUDY, f"{study_id} is not in the bound corpus")
    paper = _papers(ws, context).get(study_id, {})
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    criteria = protocol.get("screening_criteria") or {}
    batch = context.batches[context.study_batch[study_id]]
    return {
        "study_id": study_id,
        "title": paper.get("title", ""),
        "year": paper.get("year"),
        "venue": paper.get("venue"),
        "doi": paper.get("doi"),
        "abstract": paper.get("abstract") if _has_abstract(paper) else None,
        "highlights": [],  # criterion highlights arrive with the M1b triage UI
        "criteria": [
            {"id": c["id"], "text": c.get("description") or c.get("text") or "", "kind": kind}
            for kind in ("inclusion", "exclusion")
            for c in criteria.get(kind) or []
            if isinstance(c, dict) and c.get("id")
        ],
        "binding": {
            "protocol_fingerprint": context.protocol_fingerprint,
            "batch_id": batch.batch_id,
            "batch_sha256": batch.batch_sha256,
        },
        "my_decision": winners.get(study_id),
        "history": [e for e in events if e["study_id"] == study_id],
    }


@router.get("/records/{study_id}/proposal")
def record_proposal(study_id: str, request: Request) -> dict[str, Any]:
    ws = _ws(request)
    context, settings, _events, winners = _state(ws)
    if study_id not in context.study_batch:
        raise _error(404, refusals.UNKNOWN_STUDY, f"{study_id} is not in the bound corpus")
    if settings["blinding"] == "reveal_after_decision" and study_id not in winners:
        raise _error(403, refusals.PROPOSAL_HIDDEN, "decide this record first; the agent's draft is hidden until then")
    proposal = pr.latest_proposal(ws, study_id)
    if proposal is None:
        return {"proposal": None}
    output = proposal.get("output") if isinstance(proposal.get("output"), dict) else {}
    return {
        "proposal": {
            "proposal_id": proposal["proposal_id"],
            "task_version": proposal.get("task_version"),
            "model": proposal.get("model"),
            "prompt_sha256": proposal.get("prompt_sha256"),
            "criteria": output.get("criteria", []),
            "derived_outcome": proposal["derived_outcome"],
            "reason_code": proposal.get("reason_code"),
            "validators": proposal.get("validators", []),
            "cannot_decide": proposal.get("cannot_decide", False),
        }
    }


class EventsBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[dict[str, Any]] = Field(default_factory=list)


def _project(ws: Path, context: ev.ScreeningContext, events: list[dict[str, Any]]) -> None:
    workspace_id = _workspace_id(ws)
    touched = {
        (context.study_batch[e["study_id"]], e["screener_id"])
        for e in events
        if e.get("study_id") in context.study_batch
    }
    for index, screener in sorted(touched):
        ev.write_projection(ws, index, screener, workspace_id=workspace_id, context=context)


@router.post("/decisions/events")
def post_events(body: EventsBody, request: Request) -> dict[str, Any]:
    if len(body.events) > MAX_EVENTS_PER_REQUEST:
        raise _error(413, "INVALID_OUTPUT", f"at most {MAX_EVENTS_PER_REQUEST} events per request")
    ws = _ws(request)
    context = ev.load_context(ws)
    scope = getattr(request.state, "token_scope", "desktop")
    results = ev.intake(
        ws, body.events, token_scope=scope, received_at=_now(), device=scope, context=context,
        after_commit=lambda stored: _project(ws, context, stored),
    )
    return {"results": [r.as_dict() for r in results]}


@router.get("/decisions/conflicts")
def get_conflicts(request: Request) -> dict[str, Any]:
    return {"items": ev.conflicts(ev.read_events(_ws(request)))}


class ResolveBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    keep_event_id: str


@router.post("/decisions/conflicts/{study_id}/resolve")
def resolve_conflict(study_id: str, body: ResolveBody, request: Request) -> dict[str, Any]:
    """Keep one event: a new superseding decision that names every rival head."""
    ws = _ws(request)
    context = ev.load_context(ws)
    match = next((c for c in ev.conflicts(ev.read_events(ws)) if c["study_id"] == study_id), None)
    if match is None:
        raise _error(404, refusals.UNKNOWN_STUDY, f"{study_id} has no open conflict")
    kept = next((e for e in match["events"] if e["event_id"] == body.keep_event_id), None)
    if kept is None:
        raise _error(422, "INVALID_OUTPUT", "keep_event_id is not one of the conflicting events")
    scope = getattr(request.state, "token_scope", "desktop")
    resolution = {
        key: value for key, value in kept.items() if key not in ev.ENGINE_FIELDS
    } | {
        # Derived from the kept and rival events, so resolving the same
        # conflict twice is a duplicate, not a second decision.
        "event_id": str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                "nexus-scholar:resolve:" + kept["event_id"] + ":" + ",".join(
                    sorted(e["event_id"] for e in match["events"] if e["event_id"] != kept["event_id"])
                ),
            )
        ),
        "decided_at": _now(),
        "device": scope,
        "supersedes": kept["event_id"],
        "resolves": [e["event_id"] for e in match["events"] if e["event_id"] != kept["event_id"]],
        "note": kept.get("note") or f"Conflict resolved: kept {kept['event_id']}",
    }
    results = ev.intake(
        ws, [resolution], token_scope=scope, received_at=_now(), device=scope, context=context,
        after_commit=lambda stored: _project(ws, context, stored),
    )
    return {"results": [r.as_dict() for r in results]}


@router.get("/settings")
def get_settings(request: Request) -> dict[str, Any]:
    return load_settings(_ws(request))


class SettingsBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    blinding: str | None = None
    mode: str | None = None
    sample_audit_size: int | None = None
    screener_id: str | None = None
    confirm_ai_agreed_exclusion: bool = False


@router.put("/settings")
def put_settings(body: SettingsBody, request: Request) -> dict[str, Any]:
    from ...workspace.audit import append_event

    ws = _ws(request)
    current = load_settings(ws)
    update = {k: v for k, v in body.model_dump().items() if v is not None and k != "confirm_ai_agreed_exclusion"}
    if update.get("blinding") not in (None, "reveal_after_decision", "show"):
        raise _error(422, "INVALID_OUTPUT", "blinding must be reveal_after_decision or show")
    if update.get("mode") not in (None, "human_sees_every_record", "ai_agreed_exclusion"):
        raise _error(422, "INVALID_OUTPUT", "mode must be human_sees_every_record or ai_agreed_exclusion")
    if update.get("mode") == "ai_agreed_exclusion" and current["mode"] != "ai_agreed_exclusion":
        if not body.confirm_ai_agreed_exclusion or not update.get("sample_audit_size", current["sample_audit_size"]):
            raise _error(
                422,
                "INVALID_OUTPUT",
                "AI-agreed exclusion needs confirm_ai_agreed_exclusion=true and a sample_audit_size",
            )
    new = {**current, **update}
    path = ws / SETTINGS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(new, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_event(
        ws,
        "SCREENING_SETTINGS_CHANGED",
        "Changed screening settings: " + ", ".join(f"{k}={update[k]}" for k in sorted(update)),
        agent="scholar-harness/console",
        outputs=[str(SETTINGS_FILE).replace("\\", "/")],
        parameters={"before": {k: current[k] for k in update}, "after": update},
        refresh_index=False,
    )
    return new


class PrepareBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    batch_size: int = 20


@router.post("/prepare", status_code=202)
async def prepare(body: PrepareBody, request: Request) -> dict[str, Any]:
    """Start the allowlisted `screen_prepare` job; refuses without an accepted corpus."""
    ws = _ws(request)
    registry = ws / "audit" / "artifact_registry.json"
    accepted = registry.is_file() and any(
        e.get("artifact_type") == "corpus_snapshot"
        for e in json.loads(registry.read_text(encoding="utf-8")).get("artifacts", {}).values()
    )
    if not accepted:
        raise _error(409, refusals.SNAPSHOT_NOT_ACCEPTED, "no accepted corpus snapshot; run `nexus-scholar accept-corpus`")
    job = await request.app.state.job_runner.start("screen_prepare")
    return {"job_id": job.job_id}


@router.get("/prisma/preview")
def prisma_preview(request: Request) -> dict[str, Any]:
    ws = _ws(request)
    context, settings, events, winners = _state(ws)
    registry = json.loads((ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8"))["artifacts"]
    corpora = sorted(
        (e for e in registry.values() if e.get("artifact_type") == "corpus_snapshot"),
        key=lambda e: e.get("accepted_at", ""),
    )
    corpus = json.loads((ws / corpora[-1]["path"]).read_text(encoding="utf-8"))["data"]
    identified = len(corpus["record_to_study"])
    by_reason: dict[str, int] = {}
    counts = {"INCLUDE": 0, "EXCLUDE": 0, "MAYBE": 0}
    for winner in winners.values():
        counts[winner["outcome"]] += 1
        if winner["outcome"] == "EXCLUDE":
            code = str(winner.get("reason_code") or "UNSPECIFIED")
            by_reason[code] = by_reason.get(code, 0) + 1
    open_conflicts = ev.conflicts(events)
    screened = len(context.study_batch)
    checks = [
        {
            "name": "human_provenance",
            "ok": all(w.get("method") == "HUMAN" for w in winners.values()),
            "detail": "every decision is a human decision event",
        },
        {"name": "no_open_conflicts", "ok": not open_conflicts, "detail": f"{len(open_conflicts)} open"},
        {
            "name": "bound_to_current_protocol",
            "ok": all(
                (w.get("binding") or {}).get("protocol_fingerprint") == context.protocol_fingerprint
                for w in winners.values()
            ),
            "detail": context.protocol_fingerprint,
        },
        {"name": "every_record_decided", "ok": len(winners) == screened, "detail": f"{screened - len(winners)} not yet decided"},
    ]
    return {
        "identified": identified,
        "duplicates_removed": identified - len(corpus["studies"]),
        "screened": screened,
        "excluded": {"total": counts["EXCLUDE"], "by_reason": by_reason},
        "unclear_to_full_text": counts["MAYBE"],
        "included": counts["INCLUDE"],
        "not_yet_decided": screened - len(winners),
        "checks": checks,
    }


class PairingBeginBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    batch: int


@router.post("/actions/pairing/begin")
def pairing_begin(body: PairingBeginBody, request: Request) -> dict[str, Any]:
    """Stage approval pairing for one batch generation (desktop only).

    The plaintext code is printed to the terminal running the console and is
    never returned over HTTP (the existing pairing invariant). The researcher
    reads it there and types it into the publish screen.
    """
    from ...authority.pairing import begin_pairing

    ws = _ws(request)
    try:
        staged = begin_pairing(ws, body.batch)
    except Exception as exc:  # typed authority refusals carry a stable code
        code = getattr(exc, "code", None)
        if code is None:
            raise
        raise _error(409, str(code), str(getattr(exc, "message", exc))) from exc
    print(f"[nexus-scholar] approval code for batch {body.batch}: {staged['code']} (expires {staged['expires_at']})", flush=True)
    return {
        "batch_index": staged["batch_index"],
        "snapshot_fingerprint": staged["snapshot_fingerprint"],
        "code_expires_at": staged["expires_at"],
        "attempt_cap": staged["attempt_cap"],
        "code_shown_on": "terminal",
    }
