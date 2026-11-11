"""Recon over HTTP for an inception draft (M4c; screens 02 Explore and 03 Direction).

The draft's id is its recon session id (``rec_<hex>``). Every route is under
``/api/v1/inception/drafts/{session_id}/recon`` and calls the recon session
store the CLI wizard and the MCP tools use (``scholar_harness.recon.session``).

* ``GET  .../recon`` — the session: its probes (fingerprint, ``created_at``,
  status, one leg per provider), narrower searches left, whether the console
  has a contact address, and the draft's binding with ``stale``.
* ``POST .../recon/probe`` — start a probe as a job (202). Body:
  ``refresh``, ``semantic``, ``narrower`` (a direction label: the one narrower
  search the wizard allows). The topic and years come from the saved draft.
* ``POST .../recon/delta`` — start the gap check (up to 3 follow-ups) as a job.
* ``GET  .../recon/jobs/{job_id}`` and ``.../events`` (SSE: ``snapshot``,
  ``leg``, ``done`` or ``failed``).
* ``POST .../recon/distill`` — Explore: pool health, schools, topics, papers.
* ``GET  .../recon/directions`` — Direction: up to three directions with
  their anchor DOIs and occurrence counts.
* ``POST .../recon/bind`` — choose a direction (or write one) into the draft.

The contact address is the console's own setting (``SCHOLAR_MAILTO`` in the
environment or ``.env`` of the console process); there is no default, and a
probe without it refuses ``MAILTO_NOT_SET`` before any request.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from scholar_search.config import settings

from scholar_harness.inception import steps
from scholar_harness.inception.drafts import DraftRefused, DraftStore
from scholar_harness.inception.grounding import build_grounding, check_binding, scope_changes, scope_of
from scholar_harness.inception.intent import draft_default_concepts
from scholar_harness.recon.session import (
    DELTA_BUDGET,
    DIRECTION_UNKNOWN,
    MAILTO_NOT_SET,
    NARROW_BUDGET_SPENT,
    ReconRefused,
    ReconSessions,
    key_state,
    pool_fingerprint,
    refuse_unusable_pool,
    term_evidence,
)
from scholar_harness.recon.vocabulary import concept_report, seed_candidates

router = APIRouter(prefix="/api/v1/inception/drafts/{session_id}/recon", tags=["inception-recon"])

RECON_JOB_ACTIVE = "RECON_JOB_ACTIVE"
RECON_JOB_NOT_FOUND = "RECON_JOB_NOT_FOUND"
TERM_EMPTY = "TERM_EMPTY"
TERMINAL = ("succeeded", "failed")
#: Finished jobs kept per draft; older ones answer RECON_JOB_NOT_FOUND (their results stay in the session).
KEEP_FINISHED = 10


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class ReconJob:
    job_id: str
    session_id: str
    kind: str
    state: str = "running"
    started_at: str = field(default_factory=_now)
    finished_at: str | None = None
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    changed: asyncio.Event = field(default_factory=asyncio.Event)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "session_id": self.session_id,
            "kind": self.kind,
            "state": self.state,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "result": self.result,
            "error": self.error,
        }

    def emit(self, event: str, data: dict[str, Any]) -> None:
        self.events.append({"event": event, "data": data})
        self.changed.set()


class ReconJobs:
    """In-memory recon jobs of this console process; one running job per draft."""

    def __init__(self) -> None:
        self.jobs: dict[str, ReconJob] = {}
        self.tasks: set[asyncio.Task] = set()

    def active(self, session_id: str) -> ReconJob | None:
        return next((j for j in self.jobs.values() if j.session_id == session_id and j.state not in TERMINAL), None)

    def _evict(self, session_id: str) -> None:
        """Keep the last ``KEEP_FINISHED`` finished jobs of a draft (review #5); results are in the session."""
        finished = [j for j in self.jobs.values() if j.session_id == session_id and j.state in TERMINAL]
        finished.sort(key=lambda j: j.finished_at or "")
        for job in finished[: max(0, len(finished) - KEEP_FINISHED)]:
            self.jobs.pop(job.job_id, None)

    def start(self, session_id: str, kind: str, work) -> ReconJob:
        self._evict(session_id)
        job = ReconJob(job_id="rjob_" + uuid.uuid4().hex[:16], session_id=session_id, kind=kind)
        self.jobs[job.job_id] = job
        job.emit("snapshot", {"job": job.to_dict()})

        async def run() -> None:
            try:
                job.result = await work(job)
                job.state = "succeeded"
            except ReconRefused as exc:
                job.state = "failed"
                job.error = {"code": exc.code, "message": exc.message, "details": exc.details}
            except Exception as exc:  # noqa: BLE001 - a job reports its failure, never crashes the console
                job.state = "failed"
                job.error = {"code": "RECON_FAILED", "message": f"{type(exc).__name__}: {str(exc)[:300]}"}
            job.finished_at = _now()
            job.emit("done" if job.state == "succeeded" else "failed", {"job": job.to_dict()})

        task = asyncio.get_running_loop().create_task(run())
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return job


# --------------------------------------------------------------------------- helpers


def _error(exc: ReconRefused | DraftRefused | steps.StepRefused) -> HTTPException:
    detail: dict[str, Any] = {"code": exc.code, "message": exc.message}
    if exc.details:
        detail["details"] = exc.details
    return HTTPException(status_code=exc.status, detail=detail)


def _jobs(request: Request) -> ReconJobs:
    jobs = getattr(request.app.state, "recon_jobs", None)
    if jobs is None:
        jobs = request.app.state.recon_jobs = ReconJobs()
    return jobs


def _sessions(request: Request) -> ReconSessions:
    """The recon root and search seam of this console; tests inject both on ``app.state``."""
    return ReconSessions(
        root=getattr(request.app.state, "recon_root", None),
        search_fn=getattr(request.app.state, "recon_search_fn", None),
    )


def _store(request: Request) -> DraftStore:
    return DraftStore(Path(request.app.state.workspaces_root))


def _draft(request: Request, session_id: str) -> tuple[dict[str, Any], steps.Draft]:
    record = _store(request).load(session_id)
    return record, steps.parse_draft(record.get("draft"))


def _mailto_set(request: Request) -> bool:
    return getattr(request.app.state, "recon_search_fn", None) is not None or bool(settings.mailto)


def _require_mailto(request: Request) -> None:
    if not _mailto_set(request):
        raise ReconRefused(
            MAILTO_NOT_SET,
            "A search needs a contact email for the literature databases. Set SCHOLAR_MAILTO "
            "for the console (environment or .env) and start it again.",
        )


def _sse(event: dict[str, Any]) -> str:
    return f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"


# --------------------------------------------------------------------------- routes


class ProbeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refresh: bool = False
    semantic: bool = False
    #: A direction label of the current pool: run the one narrower search on it.
    narrower: str | None = None


class DeltaBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    followups: int = Field(default=DELTA_BUDGET, ge=0, le=DELTA_BUDGET)


class BindBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    direction: str | None = None
    own: str | None = None
    #: Go on without a direction, recorded as not grounded (spec 03 Q1, M4d).
    skip: bool = False
    accept_thin_pool: bool = False
    base_updated_at: str | None = None


@router.get("")
def recon_state(session_id: str, request: Request) -> dict[str, Any]:
    try:
        record, _draft_model = _draft(request, session_id)
        sessions = _sessions(request)
        session = sessions.current(session_id) if sessions.exists(session_id) else None
    except (ReconRefused, DraftRefused, steps.StepRefused) as exc:
        raise _error(exc) from exc
    grounding = record.get("grounding")
    active = _jobs(request).active(session_id)
    changes = _scope_changes(sessions, session_id, session, _draft_model) if session else []
    return {
        "session_id": session_id,
        "mailto_set": _mailto_set(request),
        # M4d DoD 1: whether OpenAlex and Semantic Scholar have their keys (as GET /discovery/plan says).
        "keys": key_state(),
        # The draft's question changed since the session searched it (review #8; spec 02 Q3).
        "topic_changed": bool(session and session.get("topic") and session["topic"] != _draft_model.topic),
        "session": session,
        "grounding": grounding,
        # M4d (spec 02 Q3, 03 Q3): the saved question, years or languages differ from the latest pool's.
        "scope_changed": bool(changes),
        "scope_changes": changes,
        "binding": check_binding(sessions, grounding, scope_of(_draft_model)) if grounding else None,
        "active_job": active.to_dict() if active else None,
    }


def _scope_changes(sessions: ReconSessions, session_id: str, session: dict[str, Any], draft: Any) -> list[str]:
    """The parts of the draft's scope that differ from what the latest pool was searched for."""
    try:
        pool, _path = sessions.latest_pool(session_id)
    except ReconRefused:
        return []
    then: dict[str, Any] = {"topic": session.get("topic"), "year_min": pool.get("year_min"), "year_max": pool.get("year_max")}
    if "languages" in pool and pool["languages"] is not None:
        then["languages"] = pool["languages"]
    return scope_changes(scope_of(draft), then)


@router.post("/probe", status_code=202)
async def start_probe(session_id: str, body: ProbeBody, request: Request) -> dict[str, Any]:
    jobs = _jobs(request)
    try:
        _record, draft = _draft(request, session_id)
        if not draft.topic:
            raise steps.StepRefused("DRAFT_INCOMPLETE", "a probe needs the draft's topic", details={"missing": ["topic"]})
        _require_mailto(request)
        sessions = _sessions(request)
        query, purpose = draft.topic, "topic"
        if body.narrower is not None:
            if not sessions.exists(session_id):
                raise ReconRefused("RECON_NO_POOL", "Run the first search before a narrower one.")
            if sessions.current(session_id)["narrower_left"] <= 0:
                raise ReconRefused(NARROW_BUDGET_SPENT, "The one narrower search of this draft is used.")
            labels = [d["label"] for d in sessions.directions(session_id)["directions"]]
            if body.narrower not in labels:
                raise ReconRefused(
                    DIRECTION_UNKNOWN, f"'{body.narrower}' is not one of the directions of the current pool.",
                    status=422, details={"directions": labels},
                )
            query, purpose = body.narrower, "narrower"
        if jobs.active(session_id):
            raise ReconRefused(RECON_JOB_ACTIVE, "A search for this draft is already running.", details={"job": jobs.active(session_id).to_dict()})
    except (ReconRefused, DraftRefused, steps.StepRefused) as exc:
        raise _error(exc) from exc

    async def work(job: ReconJob) -> dict[str, Any]:
        def progress(provider: str, fetched: int) -> None:
            job.emit("leg", {"job_id": job.job_id, "provider": provider, "fetched": fetched})

        result = await sessions.probe(
            query, session_id=session_id, topic=draft.topic, purpose=purpose,
            year_min=draft.start_year or 2000, year_max=draft.end_year,
            semantic=body.semantic, refresh=body.refresh, progress=progress,
            languages=list(draft.languages),
        )
        refuse_unusable_pool(result)
        return result

    return {"job": jobs.start(session_id, "probe", work).to_dict()}


@router.post("/delta", status_code=202)
async def start_delta(session_id: str, body: DeltaBody, request: Request) -> dict[str, Any]:
    jobs = _jobs(request)
    try:
        _record, draft = _draft(request, session_id)
        _require_mailto(request)
        sessions = _sessions(request)
        sessions.latest_pool(session_id)
        if jobs.active(session_id):
            raise ReconRefused(RECON_JOB_ACTIVE, "A search for this draft is already running.")
    except (ReconRefused, DraftRefused, steps.StepRefused) as exc:
        raise _error(exc) from exc

    async def work(job: ReconJob) -> dict[str, Any]:
        return await sessions.delta(
            session_id, followups=body.followups, year_min=draft.start_year or 2000, year_max=draft.end_year
        )

    return {"job": jobs.start(session_id, "delta", work).to_dict()}


def _job(request: Request, session_id: str, job_id: str) -> ReconJob:
    job = _jobs(request).jobs.get(job_id)
    if job is None or job.session_id != session_id:
        raise HTTPException(status_code=404, detail={"code": RECON_JOB_NOT_FOUND, "message": f"no recon job {job_id} for this draft"})
    return job


@router.get("/jobs/{job_id}")
def read_job(session_id: str, job_id: str, request: Request) -> dict[str, Any]:
    return {"job": _job(request, session_id, job_id).to_dict()}


@router.get("/jobs/{job_id}/events")
async def job_events(session_id: str, job_id: str, request: Request) -> StreamingResponse:
    job = _job(request, session_id, job_id)

    async def gen():
        sent = 0
        while True:
            while sent < len(job.events):
                yield _sse(job.events[sent])
                sent += 1
            if job.state in TERMINAL and sent >= len(job.events):
                return
            job.changed.clear()
            if sent < len(job.events):
                continue
            try:
                await asyncio.wait_for(job.changed.wait(), timeout=15)
            except TimeoutError:
                yield ": keepalive\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/distill")
def distill(session_id: str, request: Request) -> dict[str, Any]:
    try:
        _draft(request, session_id)
        out = _sessions(request).distill(session_id)
    except (ReconRefused, DraftRefused, steps.StepRefused) as exc:
        raise _error(exc) from exc
    terms = out.pop("distilled")
    return {
        **out,
        "metrics": [{"label": k, "count": v} for k, v in sorted((terms.get("metrics") or {}).items())],
        "datasets": [{"label": k, "count": v} for k, v in sorted((terms.get("datasets") or {}).items())],
        "schools": terms.get("schools") or [],
        "topics": terms.get("topics") or [],
        "micro_taxonomy_top": (terms.get("micro_taxonomy") or [])[:10],
    }


@router.get("/directions")
def directions(session_id: str, request: Request) -> dict[str, Any]:
    try:
        _draft(request, session_id)
        out = _sessions(request).directions(session_id)
    except (ReconRefused, DraftRefused, steps.StepRefused) as exc:
        raise _error(exc) from exc
    out.pop("distilled")
    return out


def _concept_rows(draft: steps.Draft) -> tuple[list[dict[str, Any]], str]:
    """The draft's concepts, or the scope step's suggested words when it has none yet."""
    if draft.concepts:
        return [{"concept": c.concept, "synonyms": list(c.synonyms)} for c in draft.concepts], "draft"
    return [{"concept": w, "synonyms": []} for w in draft_default_concepts(draft.topic)], "suggested"


@router.get("/concepts")
def concepts(session_id: str, request: Request) -> dict[str, Any]:
    """M4d DoD 3 and 4: per concept, the pool records anchoring it and co-occurring pool terms."""
    try:
        _record, draft = _draft(request, session_id)
        pool, _path = _sessions(request).latest_pool(session_id)
    except (ReconRefused, DraftRefused, steps.StepRefused) as exc:
        raise _error(exc) from exc
    rows, source = _concept_rows(draft)
    return {
        "session_id": session_id,
        "fingerprint": pool_fingerprint(pool),
        "n_docs": len(pool.get("docs") or []),
        "concepts": concept_report(pool, rows, source),
    }


@router.get("/evidence")
def evidence(session_id: str, request: Request, term: str = "") -> dict[str, Any]:
    """Spec 03 Q4 (M4d): does a phrase occur in the latest pool? Reads only."""
    try:
        _draft(request, session_id)
        if not term.strip():
            raise ReconRefused(TERM_EMPTY, "Type a phrase to check.", status=422)
        pool, _path = _sessions(request).latest_pool(session_id)
    except (ReconRefused, DraftRefused, steps.StepRefused) as exc:
        raise _error(exc) from exc
    return {"term": term, **term_evidence(pool, term.strip()), "n_docs": len(pool.get("docs") or [])}


@router.get("/seeds")
def seeds(session_id: str, request: Request) -> dict[str, Any]:
    """M4d DoD 5: the pool records that anchor a direction or a concept, offered as recall seeds."""
    try:
        _record, draft = _draft(request, session_id)
        sessions = _sessions(request)
        found = sessions.directions(session_id)
        pool, _path = sessions.latest_pool(session_id)
    except (ReconRefused, DraftRefused, steps.StepRefused) as exc:
        raise _error(exc) from exc
    rows, _source = _concept_rows(draft)
    return {
        "session_id": session_id,
        "fingerprint": pool_fingerprint(pool),
        "papers": seed_candidates(pool, found["directions"], [r["concept"] for r in rows]),
    }


@router.post("/bind")
def bind(session_id: str, body: BindBody, request: Request) -> dict[str, Any]:
    try:
        _record, draft = _draft(request, session_id)
        grounding = build_grounding(
            _sessions(request), session_id, direction=body.direction, own=body.own,
            accept_thin_pool=body.accept_thin_pool, scope=scope_of(draft), skip=body.skip,
        )
        return _store(request).bind_grounding(session_id, grounding, base_updated_at=body.base_updated_at)
    except (ReconRefused, DraftRefused, steps.StepRefused) as exc:
        raise _error(exc) from exc
