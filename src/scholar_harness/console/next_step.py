"""The next-step bar's answer (M10b Part C, ``docs/ux/shared/final/04-next-step.md``).

One builder for ``GET /api/v1/review/next-step`` (a workspace) and
``GET /api/v1/inception/drafts/{id}/next-step`` (a draft). It reads the
engine's own functions, never the HTTP routes, and computes the first row of
the spec's table 1 that holds, with an independent ``waiting`` variant (table
2) when a job runs or the newest run ended without a usable result. The bar
writes nothing; this module writes nothing.

The browser receives a state code, the copy parameters as the engine wrote
them and a destination screen name; it never inspects a file or a count.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SHAPE = "review.next-step-v1"

#: Table 1, in order.
STATES = (
    "NO_REVIEW", "DRAFT_STARTED", "DRAFT_INCOMPLETE", "DRAFT_READY", "DRAFT_CREATED", "NO_PROTOCOL",
    "PROTOCOL_INVALID", "PROTOCOL_PLACEHOLDER", "SETUP_NEEDED", "READY_TO_SEARCH", "STAGED_EXPORTS",
    "SEARCH_CHANGED", "CORPUS_READY", "SEARCH_UNFINISHED", "CORPUS_PENDING", "NOT_PREPARED",
    "PROTOCOL_CHANGED_AFTER_BATCHES", "CONFLICTS", "SCREENING", "READY_TO_PUBLISH", "PUBLISHED_STALE",
    "PUBLISHED", "CHASE_READY_TO_SEND", "CHASE_NOTHING_NEW", "ROUND_ACCEPTED", "DONE",
)
#: Table 2 ``waiting.stage`` values (``accepting_chase`` is not computed: it is a refusal of the accept).
WAITING_STAGES = ("searching", "deduplicating", "adding_abstracts", "verifying", "preparing", "chasing", "accepting_chase")
WAITING_KINDS = ("running", "stopped", "failed", "interrupted")
#: The engine's preparation stages, as the bar names them (decision 2026-11-17 item 1).
STAGE_NAMES = {"deduplication": "deduplicating", "hydration": "adding_abstracts", "verification": "verifying"}
#: Reason labels that are not refusals (not in ``console/refusals.py``).
STOPPED_BY_RESEARCHER = "STOPPED_BY_RESEARCHER"
INTERRUPTED = "INTERRUPTED"

#: The inception steps in order, and the step of each field a protocol needs (the browser's ``FIELD_STEP``).
DRAFT_STEPS = ("scope", "explore", "direction", "shape", "criteria", "review")
FIELD_STEP = {
    "topic": "scope", "paradigm": "shape", "playbook": "shape", "unit_of_analysis": "shape", "proof": "shape",
    "rqs": "shape", "concepts": "criteria", "criteria_decisions": "criteria", "title": "review", "lead_researcher": "review",
}
REQUIRED_FIELDS = ("topic", "paradigm", "playbook", "unit_of_analysis", "proof", "rqs", "concepts", "title", "lead_researcher")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _action(key: str, screen: str, **query: Any) -> dict[str, Any]:
    return {"key": key, "to": {"screen": screen, "query": {k: v for k, v in query.items() if v is not None}}}


def answer(
    scope: str, state: str, *, phase: str | None, params: dict[str, Any] | None = None,
    action: dict[str, Any] | None = None, also: list[dict[str, Any]] | None = None,
    waiting: dict[str, Any] | None = None, unknown: list[str] | None = None, round_: int = 1,
    fingerprint: str | None = None,
) -> dict[str, Any]:
    assert state in STATES, state
    return {
        "shape": SHAPE, "scope": scope, "phase": phase, "round": round_, "state": state,
        "params": dict(params or {}), "waiting": waiting, "action": action, "also": list(also or []),
        "unknown": list(unknown or []), "protocol_fingerprint": fingerprint, "computed_at": _now(),
    }


def no_review(listing_empty: bool) -> dict[str, Any]:
    """Row 1: no workspace open (the route is workspace-free and answers this itself)."""
    return answer("workspace", "NO_REVIEW", phase=None,
                  action=_action("chooseReview", "inception.list" if listing_empty else "workspaces"))


# --------------------------------------------------------------------------- draft scope (rows 2 to 5)


def _blank(value: Any) -> bool:
    return not (value.strip() if isinstance(value, str) else value)


def draft_missing(draft: Any) -> list[str]:
    """The fields a protocol needs that the draft leaves empty, without a genesis attempt (``_require``'s rule)."""
    from scholar_harness.inception.steps import proof_required

    fields = [f for f in REQUIRED_FIELDS if not (f == "proof" and not proof_required(draft))]
    return [f for f in fields if _blank(getattr(draft, f))]


def _first_step(steps: list[str]) -> str:
    return min(steps, key=lambda s: DRAFT_STEPS.index(s) if s in DRAFT_STEPS else len(DRAFT_STEPS))


def build_draft(record: dict[str, Any], checks_answer: dict[str, Any] | None) -> dict[str, Any]:
    """Rows 2 to 5 for one draft record; ``checks_answer`` is the checks list response (``ready`` and the blockers)."""
    from scholar_harness.inception import steps

    sid = record.get("session_id")
    emitted = record.get("emitted")
    if emitted:
        return answer("draft", "DRAFT_CREATED", phase="inception",
                      params={"title": (record.get("draft") or {}).get("title") or emitted.get("slug"),
                              "slug": emitted.get("slug")},
                      action=_action("goToDone", "inception.done", draft=sid))
    draft = steps.parse_draft(record.get("draft"))
    if _blank(draft.topic):
        return answer("draft", "DRAFT_STARTED", phase="inception", action=_action("goToStep", "inception.scope", draft=sid),
                      params={"step": "scope"})
    missing = draft_missing(draft)
    unknown: list[str] = []
    if checks_answer is None:
        unknown.append("checks")
    blockers = [c for c in (checks_answer or {}).get("checks") or []
                if c.get("level") == "blocker" and c.get("status") == "open"]
    if missing or blockers:
        fields = list(missing)
        step_of = [FIELD_STEP.get(f, "review") for f in missing]
        for c in blockers:
            act = c.get("action") or {}
            name = act.get("field") or c.get("check_id")
            if name not in fields:
                fields.append(name)
            step_of.append(act.get("step") or c.get("step") or "review")
        step = _first_step(step_of)
        return answer("draft", "DRAFT_INCOMPLETE", phase="inception", params={"fields": fields, "step": step},
                      action=_action("goToStep", f"inception.{step}", draft=sid), unknown=unknown)
    if checks_answer is not None and checks_answer.get("ready") is True:
        return answer("draft", "DRAFT_READY", phase="inception", action=_action("goToReview", "inception.review", draft=sid))
    # The checks could not be read: the engine's best reading, hedged.
    return answer("draft", "DRAFT_INCOMPLETE", phase="inception", params={"fields": [], "step": "review"},
                  action=_action("goToStep", "inception.review", draft=sid), unknown=unknown)


# --------------------------------------------------------------------------- workspace scope (rows 6 to 26)


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _protocol_origin(ws: Path) -> str:
    """``project.json`` ``protocol_origin``; a workspace without it is read as ``inception``, never as a placeholder."""
    manifest = _read_json(ws / "project.json")
    origin = manifest.get("protocol_origin") if isinstance(manifest, dict) else None
    return str(origin) if origin else "inception"


def _works(ws: Path) -> int | None:
    rows = _read_json(ws / "literature" / "deduped.json")
    return len(rows) if isinstance(rows, list) else None


def _verified_works(ws: Path) -> int | None:
    rows = _read_json(ws / "literature" / "verified.json")
    return len(rows) if isinstance(rows, list) else None


def _job_view(job: Any) -> dict[str, Any] | None:
    if job is None:
        return None
    return {"job_id": job.job_id, "kind": job.kind, "state": job.state, "started_at": job.started_at}


def _waiting(kind: str, stage: str, *, job: Any = None, reason: dict[str, Any] | None = None, since: str | None = None,
             details: dict[str, Any] | None = None) -> dict[str, Any]:
    assert kind in WAITING_KINDS and stage in WAITING_STAGES, (kind, stage)
    out = {"kind": kind, "stage": stage, "job": _job_view(job), "reason": reason,
           "since": since or (job.started_at if job is not None else None)}
    if details:
        out["details"] = details
    return out


def _answered(job: Any) -> int:
    """Databases whose leg ended, from the job's own ``leg`` events (no file read)."""
    done: set[str] = set()
    for event in getattr(job, "events", None) or []:
        data = event.get("data") or {}
        if event.get("event") == "leg" and data.get("status") not in (None, "running"):
            done.add(str(data.get("provider")))
    return len(done)


def _finish_or_search(prep: dict[str, Any], run: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if prep.get("can_finish"):
        return _action("finishPreparing", "discovery.harvest", run=run), [_action("searchAgain", "discovery.harvest")]
    return _action("searchAgain", "discovery.harvest"), []


def build_workspace(
    ws: Path, *, active: Any = None, screening_jobs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Rows 6 to 26 for the open workspace.

    ``active`` is the workspace's live discovery job (``DiscoveryJobs.active``),
    ``screening_jobs`` the console job runner's jobs as dicts (``GET /jobs``).
    Each source that cannot be read goes to ``unknown``; the state is computed
    from what was readable.
    """
    from .api import discovery as disc
    from .api.screening_v1 import _corpus_view, summary_of

    unknown: list[str] = []
    if not (ws / "protocol.json").is_file():
        return answer("workspace", "NO_PROTOCOL", phase="inception", action=_action("goToInception", "inception.list"))
    try:
        proto = disc._protocol(ws)
    except disc.Refused:
        return answer("workspace", "PROTOCOL_INVALID", phase="inception", action=_action("goToInception", "inception.list"))
    fp = proto.fingerprint

    def done(state: str, phase: str, **kw: Any) -> dict[str, Any]:
        return answer("workspace", state, phase=phase, unknown=unknown, fingerprint=fp, **kw)

    if _protocol_origin(ws) == "placeholder":
        return done("PROTOCOL_PLACEHOLDER", "inception", action=_action("goToInception", "inception.list"))

    try:
        runs = disc._run_summaries(ws, active)
    except Exception:  # noqa: BLE001 - one unreadable source is "unknown", never a 5xx
        runs, unknown = [], [*unknown, "runs"]
    try:
        corpus = _corpus_view(ws)
    except Exception:  # noqa: BLE001
        corpus, unknown = {"state": "EMPTY", "sources": [], "from_discovery": False}, [*unknown, "corpus"]
    state = corpus.get("state")
    sources = corpus.get("sources") or []
    from_discovery = bool(corpus.get("from_discovery"))
    run_job = active if active is not None and active.kind in disc.PREPARING_KINDS else None
    chase_job = active if active is not None and active.kind == "chase" else None
    newest = runs[0] if runs else None
    corpus_run = next((r for r in runs if r.get("raw_published")), None)

    # Rows 9 and 10: before any search (and with nothing imported).
    if not runs and run_job is None and state == "EMPTY":
        need_email = not disc._mailto_set()
        need_key = "openalex" in [disc._canonical(p) for p in proto.providers] and not disc._openalex_key_set()
        if need_email or need_key:
            what = "both" if need_email and need_key else ("email" if need_email else "key")
            return done("SETUP_NEEDED", "discovery", params={"what": what}, action=_action("seeWhatToSet", "discovery.plan"))
        return done("READY_TO_SEARCH", "discovery", action=_action("goToHarvest", "discovery.harvest"))

    if state != "ACCEPTED":
        # Row 11: staged exports win over an unfinished harvest (M3i decision item 10).
        if state == "STAGED" and not from_discovery and sources:
            return done("STAGED_EXPORTS", "discovery", params={"n": len(sources)},
                        action=_action("reviewExports", "discovery.handoff"))
        # A live job says what runs before any other row (the bar's purpose: "when something is running, say that").
        if run_job is not None and not run_job.preparing_run:
            # Row 14, variant A: the search is still fetching.
            return done("SEARCH_UNFINISHED", "discovery",
                        params={"answered": _answered(run_job), "databases": len(proto.providers)},
                        waiting=_waiting("running", "searching", job=run_job),
                        action=_action("followSearch", "discovery.harvest", job=run_job.job_id))
        if run_job is not None:
            # Row 15, variants B to D: a job prepares a published run.
            row = next((r for r in runs if r.get("run") == run_job.preparing_run), corpus_run) or {}
            prep = row.get("preparation") or {}
            stage = STAGE_NAMES.get(str(prep.get("stage"))) or "deduplicating"
            return done("CORPUS_PENDING", "discovery",
                        params={"run": row.get("run"), "records": row.get("fetched_total"), "works": _works(ws),
                                "databases": row.get("legs_total")},
                        waiting=_waiting("running", stage, job=run_job),
                        action=_action("followSearch", "discovery.harvest", job=run_job.job_id))
        prep = (corpus_run or {}).get("preparation") or {}
        if corpus_run is not None:
            run = corpus_run["run"]
            # Row 12: the search changed after the corpus run; the accept would be refused.
            if corpus_run.get("search_changed"):
                return done("SEARCH_CHANGED", "discovery", params={"run": run},
                            action=_action("goToHarvest", "discovery.harvest"))
            # Row 13: the corpus run is prepared and staged.
            if prep.get("state") == "ready" and state == "STAGED" and from_discovery:
                params = {"run": run, "records": corpus_run.get("fetched_total"),
                          "works": _verified_works(ws) if _verified_works(ws) is not None else _works(ws)}
                if corpus_run.get("protocol_changed"):
                    params["protocol_changed"] = True
                return done("CORPUS_READY", "discovery", params=params,
                            action=_action("reviewCorpus", "discovery.handoff"))
        # Row 14: the newest search ended without publishing (variants G(a) and H).
        if newest is not None and not newest.get("raw_published"):
            run = newest["run"]
            if newest.get("status") == "FAILED":
                wait = _waiting("failed", "searching", reason={"code": "PROVIDERS_FAILED", "message": None},
                                since=newest.get("finished_at"))
            else:
                wait = _waiting("stopped", "searching", reason={"code": STOPPED_BY_RESEARCHER, "message": None},
                                since=newest.get("finished_at"))
            return done("SEARCH_UNFINISHED", "discovery", params={"run": run}, waiting=wait,
                        action=_action("searchAgain", "discovery.harvest"))
        # Row 15: the corpus run's preparation failed, stopped or never ended (the Hand-off case).
        if corpus_run is not None and prep.get("state") in ("failed", "stopped", "interrupted"):
            run = corpus_run["run"]
            stage = STAGE_NAMES.get(str(prep.get("stage")))
            params = {"run": run, "records": corpus_run.get("fetched_total"), "works": _works(ws),
                      "databases": corpus_run.get("legs_total"), "stage": stage}
            if prep.get("cannot_finish"):
                params["cannot_finish"] = prep["cannot_finish"]
            action, also = _finish_or_search(prep, run)
            if prep["state"] == "failed":
                wait = _waiting("failed", stage or "verifying", since=prep.get("ended_at"),
                                reason={"code": "DISCOVERY_FAILED", "message": prep.get("message")})
            elif prep["state"] == "stopped":
                wait = _waiting("stopped", stage or "deduplicating", since=prep.get("ended_at"),
                                reason={"code": STOPPED_BY_RESEARCHER, "message": None})
            else:
                # The cause of an interruption is not recorded; the stage is named only when the marker has one.
                wait = _waiting("interrupted", stage or "verifying", since=corpus_run.get("finished_at"),
                                reason={"code": INTERRUPTED, "message": None}, details={"stage_known": stage is not None})
            return done("CORPUS_PENDING", "discovery", params=params, waiting=wait, action=action, also=also)
        if state == "STAGED" and sources:
            return done("STAGED_EXPORTS", "discovery", params={"n": len(sources)},
                        action=_action("reviewExports", "discovery.handoff"))
        return done("READY_TO_SEARCH", "discovery", action=_action("goToHarvest", "discovery.harvest"))

    # Screening (rows 16 to 21), then publication and chase (22 to 26).
    try:
        chase = disc._chase_view(ws)
    except Exception:  # noqa: BLE001
        chase, unknown = None, [*unknown, "chase"]
    round_ = int(((chase or {}).get("screening") or {}).get("round") or 1)

    def at(state_: str, phase: str, **kw: Any) -> dict[str, Any]:
        if round_ > 1:
            kw["params"] = {"round": round_, **(kw.get("params") or {})}  # a row's own round wins (the chase sends the next one)
        return answer("workspace", state_, phase=phase, unknown=unknown, fingerprint=fp, round_=round_, **kw)

    if chase_job is not None:
        return at("PUBLISHED", "screening", waiting=_waiting("running", "chasing", job=chase_job),
                  action=_action("followChase", "discovery.chase", job=chase_job.job_id))
    try:
        summary = summary_of(ws)
    except Exception:  # noqa: BLE001
        summary, unknown = None, [*unknown, "screening"]
    if screening_jobs is None:
        unknown.append("jobs")
    preparing = next((j for j in screening_jobs or [] if j.get("action_id") == "screen_prepare"
                      and j.get("state") in ("queued", "running")), None)
    total = int((summary or {}).get("total") or 0)
    if summary is not None and total == 0:
        state_ = "ROUND_ACCEPTED" if round_ > 1 else "NOT_PREPARED"
        if preparing is not None:
            wait = {"kind": "running", "stage": "preparing", "job": {k: preparing.get(k) for k in ("job_id", "action_id", "state", "started_at")},
                    "reason": None, "since": preparing.get("started_at")}
            return at(state_, "screening", waiting=wait, action=_action("followPreparation", "screening.home"))
        return at(state_, "screening", action=_action("goToScreening", "screening.home"))
    if summary is not None:
        if summary.get("protocol_changed"):
            return at("PROTOCOL_CHANGED_AFTER_BATCHES", "screening", action=_action("openInception", "inception.list"))
        if int(summary.get("conflicts") or 0) > 0:
            return at("CONFLICTS", "screening", params={"n": int(summary["conflicts"])},
                      action=_action("goToScreeningHome", "screening.home"))
        if int(summary.get("needs_you") or 0) > 0:
            return at("SCREENING", "screening", params={"needs_you": int(summary["needs_you"]), "total": total},
                      action=_action("openTriage", "screening.triage"))
    published_file = (ws / "literature" / "screening" / "generation.json").is_file()
    if not published_file:
        return at("READY_TO_PUBLISH", "screening", action=_action("goToPublish", "screening.publish"))
    try:
        from scholar_harness.authority.generations import GenerationStatus
        from scholar_harness.screening.currentness import screening_currentness

        currentness = screening_currentness(ws)
        current = currentness.status is GenerationStatus.CURRENT
    except Exception:  # noqa: BLE001
        current, currentness, unknown = False, None, [*unknown, "publication"]
    if not current:
        # The engine does not count the studies that changed, so the sentence names no number.
        return at("PUBLISHED_STALE", "published", params={"code": getattr(currentness, "code", None)},
                  action=_action("publishAgain", "screening.publish"))
    seeds = (chase or {}).get("seeds") or {}
    chase_runs = (chase or {}).get("runs") or []
    latest = chase_runs[0] if chase_runs else None
    if chase is not None and not chase_runs and int(seeds.get("chaseable") or 0) > 0:
        return at("PUBLISHED", "published", action=_action("goToChase", "discovery.chase"))
    if latest is not None and latest.get("published") and not latest.get("accepted"):
        new = int(((latest.get("counts") or {}).get("new")) or 0)
        if new > 0:
            return at("CHASE_READY_TO_SEND", "published", params={"new": new, "round": round_ + 1},
                      action=_action("reviewChase", "discovery.chase"))
        return at("CHASE_NOTHING_NEW", "published", action=_action("goToChase", "discovery.chase"))
    params = {"chaseable": int(seeds.get("chaseable") or 0)} if chase is not None else {}
    return at("DONE", "published", params=params, action=_action("goToPublish", "screening.publish"))
