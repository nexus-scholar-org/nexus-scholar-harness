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

from fastapi import APIRouter, HTTPException, Request, Response
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
    # The order the queue is shown in (M5-slim, spec 10): a setting, so a
    # change is journaled and the methods paragraph can state the order used.
    "queue_order": "seeded",
}
QUEUE_ORDERS = ("seeded", "agent_uncertainty")
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
    events = [
        e for e in ev.current_events(ev.read_events(ws), context)
        if e.get("screener_id") == settings["screener_id"]
    ]
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
    order: str | None = None,
) -> dict[str, Any]:
    if view not in VIEWS:
        raise _error(422, "INVALID_OUTPUT", f"view must be one of {VIEWS}")
    ws = _ws(request)
    context, settings, _events, winners = _state(ws)
    # The order is the journaled setting; a request for another one is
    # refused, so the order shown is always the order recorded.
    if order is not None and order != settings["queue_order"]:
        raise _error(422, "INVALID_OUTPUT", f"the queue order is the setting ({settings['queue_order']}); change it with PUT /settings")
    order = settings["queue_order"]
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
            {"id": c["id"], "text": c.get("description") or c.get("text") or c.get("criterion") or "", "kind": kind}
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
    try:
        # M1b-0: recorded before it is shown, so a later change is stamped.
        ev.record_reveal(
            ws, study_id=study_id, screener_id=settings["screener_id"], proposal_id=proposal["proposal_id"],
            context=context, revealed_at=_now(),
        )
    except ev.LockBusy as exc:
        raise _error(503, ev.ATOMIC_COMMIT_FAILED, "the event log is busy; retry") from exc
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
    ws = _ws(request)
    return {"items": ev.conflicts(ev.current_events(ev.read_events(ws), ev.load_context(ws)))}


class ResolveBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    keep_event_id: str


@router.post("/decisions/conflicts/{study_id}/resolve")
def resolve_conflict(study_id: str, body: ResolveBody, request: Request) -> dict[str, Any]:
    """Keep one event: a new superseding decision that names every rival head."""
    ws = _ws(request)
    context = ev.load_context(ws)
    current = ev.current_events(ev.read_events(ws), context)
    match = next((c for c in ev.conflicts(current) if c["study_id"] == study_id), None)
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
    queue_order: str | None = None
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
    if update.get("queue_order") not in (None, *QUEUE_ORDERS):
        raise _error(422, "INVALID_OUTPUT", f"queue_order must be one of {QUEUE_ORDERS}")
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
        {
            "name": "projections_current",
            "ok": not (stale := ev.stale_projections(ws)),
            "detail": (
                f"{ev.PROJECTION_STALE}: batch(es) {', '.join(f'{i:03d}' for i in stale)} differ from the decision events"
                if stale else "every decisions file matches the decision events"
            ),
        },
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


@router.get("/export")
def export_decisions(request: Request, format: str = "ris", set: str | None = None) -> Response:
    """The published decisions as RIS or CSV (spec 10). Read-only; no journal row."""
    from ...screening import export as ex

    try:
        body, filename, media = ex.build_export(_ws(request), format, set)
    except ex.ExportRefused as exc:
        raise _error(exc.status, exc.code, exc.message, **exc.details) from exc
    return Response(
        content=body, media_type=media, headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/methods")
def methods_paragraph(request: Request) -> dict[str, Any]:
    """The methods paragraph of the published screening (spec 10). Read-only; no journal row."""
    from ...screening import export as ex

    try:
        return ex.build_methods(_ws(request))
    except ex.ExportRefused as exc:
        raise _error(exc.status, exc.code, exc.message, **exc.details) from exc


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


# --- M1b-2: agent runs, calibration, agreement (contract §4, spec 06/07) -------


class RunConsent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: str
    accepted_at: str


class RunScope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    view: str | None = None
    study_ids: list[str] | None = None


class RunBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    driver: str = "api"
    provider: str = "anthropic"
    model: str = "claude-opus-5-5"
    effort: str = "low"
    scope: RunScope = Field(default_factory=RunScope)
    consent: RunConsent | None = None
    cost_ceiling_usd: float | None = None
    base_url: str | None = None
    dry_run: bool = False
    estimate_only: bool = False


def _scope_ids(ws: Path, scope: RunScope) -> list[str]:
    context, _settings, _events, winners = _state(ws)
    if scope.study_ids:
        return list(dict.fromkeys(scope.study_ids))
    order = [s for index in sorted(context.batches) for s in context.batches[index].candidates]
    proposed = {p["study_id"] for p in pr.read_proposals(ws) if p.get("protocol_fingerprint") == context.protocol_fingerprint}
    view = scope.view or "needs_you"
    if view == "needs_you":
        return [s for s in order if s not in winners]
    if view == "no_proposal":
        return [s for s in order if s not in winners and s not in proposed]
    raise _error(422, "INVALID_OUTPUT", "scope.view must be needs_you or no_proposal")


def _run_error(exc: Any) -> HTTPException:
    return _error(exc.status, exc.code, exc.message)


@router.post("/proposals/runs")
def start_proposal_run(body: RunBody, request: Request) -> dict[str, Any]:
    """Estimate, or start, an agent run over the scope; nothing leaves the machine without consent."""
    from scholar_agent import prompt_gate as pg

    from ...screening import agent_runs as runs

    ws = _ws(request)
    ids = _scope_ids(ws, body.scope)
    if body.dry_run:
        ids = ids[: pg.DIRECT_LIMIT]
    if body.estimate_only:
        protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
        spec = pg.run_spec(protocol, model=body.model, effort=body.effort, max_tokens=4096)
        context = ev.load_context(ws)
        papers = runs._papers(ws, context)
        records = [pg.EvalRecord(s, "", *runs._text(papers.get(s, {}))) for s in ids]
        batch = body.provider == "anthropic" and len(ids) > pg.DIRECT_LIMIT
        return {"run_id": None, "estimate": pg.estimate(records, spec, provider=body.provider, batch=batch)}
    if not ids:
        raise _error(422, "INVALID_OUTPUT", "the scope has no records")
    try:
        if body.consent is not None:
            if body.consent.provider != body.provider:
                raise _error(422, "INVALID_OUTPUT", "consent.provider must match provider")
            from scholar_agent.tasks import screening as task_mod

            runs.record_consent(
                ws, body.provider, model=body.model, prompt_sha256=task_mod.load_task().prompt_sha256,
                accepted_at=body.consent.accepted_at,
            )
        run = runs.start_run(
            ws, provider=body.provider, model=body.model, effort=body.effort, study_ids=ids,
            cost_ceiling_usd=body.cost_ceiling_usd,
            driver_factory=getattr(request.app.state, "driver_factory", None),
            executor=getattr(request.app.state, "run_executor", None),
            base_url=body.base_url,
        )
    except runs.RunRefused as exc:
        raise _run_error(exc) from exc
    return {"run_id": run["run_id"], "estimate": run["estimate"]}


def _run_view(run: dict[str, Any]) -> dict[str, Any]:
    keys = ("run_id", "kind", "state", "code", "provider", "model", "effort", "records", "done", "failed", "refused",
            "truncated", "invalid", "check_failures", "cost_so_far", "cost_ceiling_usd", "started_at", "finished_at")
    view = {k: run.get(k) for k in keys}
    if "calibration" in run:
        view["calibration"] = run["calibration"]
    return view


@router.get("/proposals/setup")
def proposal_setup(request: Request) -> dict[str, Any]:
    """What the run screen needs before a run: key presence (never a key), the task, consent, runs."""
    from scholar_agent import keys
    from scholar_agent.tasks import screening as task_mod

    from ...screening import agent_runs as runs

    ws = _ws(request)
    task = task_mod.load_task()
    consent = runs.read_consent(ws)
    providers = [
        {"provider": p, "key": keys.key_status(p).source, "consent": consent.get(p)}
        for p in keys.ENV_VARS
    ]
    recorded = runs.list_runs(ws)
    latest = max(recorded, key=lambda r: (r.get("started_at") or "", r["run_id"]), default=None)
    return {
        "task": {
            "task_version": task.task_version,
            "prompt_sha256": task.prompt_sha256,
            "model": task.defaults.get("model"),
            "effort": task.defaults.get("effort"),
        },
        "providers": providers,
        "data_flow": runs.DATA_FLOW,
        "active_run": runs.active_run(ws),
        "latest_run": _run_view(latest) if latest else None,
    }


@router.get("/proposals/runs/{run_id}")
def proposal_run_status(run_id: str, request: Request) -> dict[str, Any]:
    from ...screening import agent_runs as runs

    try:
        return _run_view(runs.read_run(_ws(request), run_id))
    except runs.RunRefused as exc:
        raise _run_error(exc) from exc


@router.post("/proposals/runs/{run_id}/cancel")
def cancel_proposal_run(run_id: str, request: Request) -> dict[str, Any]:
    from ...screening import agent_runs as runs

    try:
        run = runs.request_cancel(_ws(request), run_id)
    except runs.RunRefused as exc:
        raise _run_error(exc) from exc
    return {"run_id": run_id, "state": "cancelled" if run["state"] == "running" else run["state"]}


class CalibrationBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    study_ids: list[str]
    provider: str = "anthropic"
    model: str = "claude-opus-5-5"
    effort: str = "low"
    cost_ceiling_usd: float | None = None
    base_url: str | None = None


@router.post("/proposals/calibrations")
def start_calibration(body: CalibrationBody, request: Request) -> dict[str, Any]:
    """Check the agent on records you have decided (advisory; never blocks a run)."""
    from ...screening import agent_runs as runs

    ws = _ws(request)
    _context, _settings, _events, winners = _state(ws)
    if not body.study_ids or any(s not in winners for s in body.study_ids):
        raise _error(422, "INVALID_OUTPUT", "calibration uses records you have already decided")
    try:
        run = runs.start_run(
            ws, provider=body.provider, model=body.model, effort=body.effort,
            study_ids=list(dict.fromkeys(body.study_ids)), cost_ceiling_usd=body.cost_ceiling_usd, kind="calibration",
            driver_factory=getattr(request.app.state, "driver_factory", None),
            executor=getattr(request.app.state, "run_executor", None),
            base_url=body.base_url,
        )
    except runs.RunRefused as exc:
        raise _run_error(exc) from exc
    return {"run_id": run["run_id"]}


_PAIRS = {
    ("INCLUDE", "INCLUDE"): "both_include",
    ("INCLUDE", "EXCLUDE"): "you_include_agent_exclude",
    ("EXCLUDE", "INCLUDE"): "you_exclude_agent_include",
    ("EXCLUDE", "EXCLUDE"): "both_exclude",
}


@router.get("/agreement")
def agreement(request: Request) -> dict[str, Any]:
    """Your decisions beside the agent drafts, counting only decisions made before the reveal."""
    from collections import Counter

    ws = _ws(request)
    context, settings, events, winners = _state(ws)
    screener = settings["screener_id"]
    reveals: dict[str, str] = {}
    for r in ev.read_reveals(ws):
        if r.get("screener_id") == screener and ev.is_current(r, context):
            first = reveals.get(r["study_id"])
            reveals[r["study_id"]] = min(first, r["revealed_at"]) if first else r["revealed_at"]
    current = [p for p in pr.read_proposals(ws) if p.get("protocol_fingerprint") == context.protocol_fingerprint]
    latest = {p["study_id"]: p for p in sorted(current, key=lambda p: (p.get("created_at") or "", p["proposal_id"]))}
    table = dict.fromkeys(_PAIRS.values(), 0)
    unclear, compared, after_seeing = 0, 0, 0
    splits: Counter[str] = Counter()
    for study, proposal in latest.items():
        if study not in winners:
            continue
        revealed_at = reveals.get(study)
        before = [
            e for e in events
            if e["study_id"] == study and (revealed_at is None or str(e.get("received_at") or "") < revealed_at)
        ]
        if not before:
            after_seeing += 1  # decided with the draft already in view (blinding off)
            continue
        decision = max(before, key=lambda e: str(e.get("received_at") or ""))
        compared += 1
        you, agent = decision["outcome"], proposal["derived_outcome"]
        if "MAYBE" in (you, agent):
            unclear += 1
        else:
            table[_PAIRS[(you, agent)]] += 1
        output = proposal.get("output") if isinstance(proposal.get("output"), dict) else {}
        agent_answers = {a.get("id"): a.get("answer") for a in output.get("criteria", []) if isinstance(a, dict)}
        for answer in decision.get("criteria") or []:
            if agent_answers.get(answer["id"]) not in (None, answer["answer"]):
                splits[answer["id"]] += 1
    pairs = sum(table.values())
    return {
        "decided_with_proposal": compared,
        "decided_after_seeing_the_draft": after_seeing,
        "agreement_pct": round(100 * (table["both_include"] + table["both_exclude"]) / pairs, 1) if pairs else None,
        "table_2x2": table,
        "splits_by_criterion": [{"criterion_id": k, "n": v} for k, v in sorted(splits.items())],
        "unclear_either_side": unclear,
        "kappa": None,
        "kappa_note": "needs a second human screener",
    }
