"""Inception routes (M4a; plan §2, Phase 0 screens 00–08).

They answer with or without an open workspace, like the workspaces routes.

* Drafts (screens 00 and 08): ``POST/GET /inception/drafts``,
  ``GET/PUT/DELETE /inception/drafts/{session_id}``. A draft is stored under the
  workspaces root (decision 2026-11-08, inception drafts).
* Stateless steps (screens 01–05): ``POST /inception/steps/{step}`` with the
  whole draft; nothing is stored.
* Compile-preview (screen 06): ``POST /inception/preview``; nothing is written.
* Genesis (screen 06, the only write gate): ``POST
  /inception/drafts/{session_id}/genesis`` creates
  ``<workspaces root>/<slug>`` from the saved draft through the overwrite guard
  (decision 2026-11-08, re-inception).
* Recon (M4c): ``console/api/recon.py`` under ``/inception/drafts/{id}/recon``.
  A draft bound to a direction carries ``grounding``; preview (with the
  draft's ``session_id``) shows it, and genesis writes it to
  ``audit/recon_context.json`` or refuses ``STALE_BINDING`` when the session
  searched again after the direction was chosen.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from scholar_harness.inception import steps
from scholar_harness.inception import importer
from scholar_harness.inception import checks, proposals
from scholar_harness.inception.drafts import DraftRefused, DraftStore
from scholar_harness.inception.grounding import refuse_stale, scope_of
from scholar_harness.recon.session import ReconRefused, ReconSessions

router = APIRouter(prefix="/api/v1/inception", tags=["inception"])

#: The journal agent for writes made from the browser (as the workspaces routes).
UI_AGENT = "nexus-scholar/ui"


def _error(exc: Any) -> HTTPException:
    """``{code, message, details}`` for every refusal these routes answer."""
    detail: dict[str, Any] = {"code": exc.code, "message": exc.message}
    if exc.details:
        detail["details"] = exc.details
    return HTTPException(status_code=exc.status, detail=detail)


def _root(request: Request) -> Path:
    return Path(request.app.state.workspaces_root)


def _store(request: Request) -> DraftStore:
    return DraftStore(_root(request))


class DraftBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    draft: dict[str, Any] = Field(default_factory=dict)


class AcceptedFrom(BaseModel):
    """An engine suggestion the researcher accepted with this save (M10b, R1)."""

    model_config = ConfigDict(extra="forbid")
    mechanism: Literal[proposals.MECHANISMS]  # type: ignore[valid-type]
    field: str = Field(max_length=steps.MAX_NAME_CHARS + 20)
    value: Any


class SaveBody(DraftBody):
    #: The ``updated_at`` the client last read; a newer save on disk refuses with DRAFT_CONFLICT.
    base_updated_at: str | None = None
    #: Engine suggestions this save accepts; recorded as ``engine:<mechanism>`` (M10b).
    accepted_from: list[AcceptedFrom] = Field(default_factory=list, max_length=steps.MAX_LIST_ITEMS)


class PreviewBody(DraftBody):
    #: The draft's id, to show its grounded evidence (M4c). Without it the preview is as in M4b.
    session_id: str | None = None


def _recon(request: Request) -> ReconSessions:
    return ReconSessions(
        root=getattr(request.app.state, "recon_root", None),
        search_fn=getattr(request.app.state, "recon_search_fn", None),
    )


class GenesisBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    replace: bool = False
    #: The workspace slug, typed by the researcher, to discard a screening binding.
    confirm_discard_screening_binding: str | None = None


@router.get("/drafts")
def list_drafts(request: Request) -> dict[str, Any]:
    return {"root": str(_root(request)), "items": _store(request).listing()}


@router.post("/drafts", status_code=201)
def create_draft(body: DraftBody, request: Request) -> dict[str, Any]:
    try:
        steps.parse_draft(body.draft, saving=True)
        return _store(request).create(body.draft)
    except (DraftRefused, steps.StepRefused) as exc:
        raise _error(exc) from exc


class ImportSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str = Field(pattern="^(workspace|file)$")
    slug: str | None = Field(default=None, max_length=200)
    file_name: str | None = Field(default=None, max_length=255)
    #: The file's bytes, base64. Over 1 MiB decoded the engine answers
    #: ``IMPORT_SOURCE_TOO_LARGE`` (413); this cap (about 3 MB decoded) only stops a
    #: body far past that before it is read (``BODY_INVALID``).
    content_base64: str | None = Field(default=None, max_length=4_000_000)


class ImportBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: ImportSource
    dry_run: bool = True
    #: On the creating call: the fingerprint the report showed (``IMPORT_SOURCE_CHANGED`` otherwise).
    expect_fingerprint: str | None = None


@router.post("/drafts/import")
def import_draft(body: ImportBody, request: Request, response: Response) -> dict[str, Any]:
    """Start a draft from an existing protocol (M10b, ``09-start-from-protocol``); the source is only read."""
    try:
        source = importer.read_source(body.source.model_dump(), _root(request))
        mapped = importer.map_source(source)
        if body.dry_run:
            return importer.report(source, mapped)
        if body.expect_fingerprint != source.fingerprint:
            raise DraftRefused(
                "IMPORT_SOURCE_CHANGED", "the protocol changed since it was read; read it again",
                details={"expected": body.expect_fingerprint, "found": source.fingerprint},
            )
        origin = importer.origin_record(source, mapped)
        record = _store(request).create(mapped["draft"], extra={"origin": origin})
        response.status_code = 201
        return {**record, "report": origin["report"]}
    except (DraftRefused, steps.StepRefused) as exc:
        raise _error(exc) from exc


class CheckedBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    step: str = Field(max_length=40)


@router.post("/drafts/{session_id}/origin/checked")
def origin_checked(session_id: str, body: CheckedBody, request: Request) -> dict[str, Any]:
    """Mark an imported step as opened (M10b); a side write: ``updated_at`` does not change."""
    if body.step not in importer.IMPORTED_STEPS:
        raise _error(steps.StepRefused("STEP_UNKNOWN", f"unknown step {body.step!r}", status=404, details={"steps": list(importer.IMPORTED_STEPS)}))

    def mark(origin: Any) -> Any:
        if not isinstance(origin, dict):
            return origin
        return {**origin, "checked": {**(origin.get("checked") or {}), body.step: True}}

    try:
        record = _store(request).update_side(session_id, "origin", mark)
    except DraftRefused as exc:
        raise _error(exc) from exc
    return {"session_id": session_id, "origin": record.get("origin")}


@router.get("/drafts/{session_id}")
def read_draft(session_id: str, request: Request) -> dict[str, Any]:
    try:
        return _store(request).load(session_id)
    except DraftRefused as exc:
        raise _error(exc) from exc


def _left_out(record: dict[str, Any]) -> list[str]:
    """The papers the draft left out of the sample (M10b Part C)."""
    from scholar_harness.recon.sample import keys_of

    return keys_of(record.get("sample_exclusions"))


def _pool_facts(request: Request, session_id: str, mechanisms: set[str]) -> tuple[dict | None, list | None]:
    """The draft's latest pool (and directions) when an accepted entry needs them; none without a pool."""
    if not mechanisms & {"pool_synonym", "anchor_seed"}:
        return None, None
    from scholar_harness.recon.sample import keys_of

    sessions = _recon(request)
    left = keys_of((_store(request).load(session_id)).get("sample_exclusions"))
    try:
        pool, _raw, _path = sessions.effective(session_id, left)
    except ReconRefused:
        return None, None
    directions = None
    if "anchor_seed" in mechanisms:
        try:
            directions = sessions.directions(session_id, exclusions=left)["directions"]
        except ReconRefused:
            directions = []
    return pool, directions


@router.put("/drafts/{session_id}")
def save_draft(session_id: str, body: SaveBody, request: Request) -> dict[str, Any]:
    try:
        steps.parse_draft(body.draft, saving=True)
        store = _store(request)
        if not body.accepted_from:
            return store.save(session_id, body.draft, base_updated_at=body.base_updated_at)
        entries = [e.model_dump() for e in body.accepted_from]
        pool, directions = _pool_facts(request, session_id, {e["mechanism"] for e in entries})

        def change(record: dict[str, Any]) -> list[dict[str, Any]]:
            # Judged on the stored draft, before this save replaces it (01-proposals, Data out).
            missed = proposals.record_accepted(record, entries, pool=pool, directions=directions, saved=body.draft)
            record["draft"] = body.draft
            return missed

        record, not_recorded = store.transact(session_id, change, answer=True, base_updated_at=body.base_updated_at)
        return {**record, "not_recorded": not_recorded}
    except (DraftRefused, steps.StepRefused) as exc:
        raise _error(exc) from exc


# --- checks (M10b, docs/ux/shared/final/02-checks.md) -------------------------


def _compute_checks(request: Request, session_id: str, record: dict[str, Any]) -> tuple[list, list, list, list]:
    """Every inception check of the saved draft, from the draft record and its recon session."""

    def make(**kw: Any) -> dict[str, Any]:
        return proposals.make(draft_id=session_id, draft=record.get("draft") or {}, **kw)

    return draft_checks(_root(request), _recon(request), session_id, record, make_proposal=make)


def draft_checks(
    root: Path, sessions: ReconSessions, session_id: str, record: dict[str, Any], *, make_proposal: Any = None,
) -> tuple[list, list, list, list]:
    """The checks of a saved draft record without a request (the routes and the MCP assistant, M10c).

    The fixed checks, then the assistant's findings (``source: "agent"``). With
    ``make_proposal=None`` a recommending check links to its field and nothing
    is made, so a read records nothing (M10c decision item 12).
    """
    from scholar_harness import assistant
    from scholar_harness.console.api.recon import _scope_changes
    from scholar_harness.inception.grounding import check_binding
    from scholar_harness.recon import sample as sample_mod

    draft = steps.parse_draft(record.get("draft"))
    left = sample_mod.keys_of(record.get("sample_exclusions"))
    pool = raw = None
    sample = None
    changes: list[str] = []
    try:
        if sessions.exists(session_id):
            pool, raw, _path = sessions.effective(session_id, left)
            sample = sample_mod.view(raw, record)
            changes = _scope_changes(sessions, session_id, sessions.current(session_id), draft)
    except ReconRefused:
        pool = None
    grounding = record.get("grounding")
    binding = None
    if grounding:
        try:
            binding = check_binding(sessions, grounding, scope_of(draft), left)
        except ReconRefused:
            binding = None

    items, waiting, partial, made = checks.inception_checks(
        record, pool=pool, scope_changes=changes, binding=binding, workspaces_root=root, make_proposal=make_proposal,
        sample=sample, raw_pool=raw,
    )
    try:
        items.extend(assistant.draft_rows(record))
    except Exception as exc:  # noqa: BLE001 - a broken finding must not hide the fixed checks
        partial.append({"kind": "check_failed", "check_id": checks.AGENT_CHECK_ID, "error": type(exc).__name__})
    return items, waiting, partial, made


def _checks_answer(record: dict[str, Any], items: list, waiting: list, partial: list, step: str | None) -> dict[str, Any]:
    checks.with_dismissals(items, record.get("check_dismissals") or [])
    ready = not any(c["level"] == "blocker" and c["status"] == "open" for c in items)
    return checks.respond(
        items, steps_order=checks.INCEPTION_STEPS, step=step, waiting=waiting, partial=partial, ready=ready,
        scope={"kind": "draft", "id": record["session_id"], "updated_at": record["updated_at"]},
    )


class ChecksBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    step: str | None = None


def _check_step(step: str | None) -> None:
    if step is not None and step not in checks.INCEPTION_STEPS:
        raise _error(steps.StepRefused(
            "STEP_UNKNOWN", f"unknown step {step!r}", status=404, details={"steps": list(checks.INCEPTION_STEPS)},
        ))


@router.post("/drafts/{session_id}/checks")
def run_checks(session_id: str, body: ChecksBody, request: Request) -> dict[str, Any]:
    """The checks of the saved draft (a POST: it records the proposals the checks recommend, once)."""
    _check_step(body.step)
    store = _store(request)
    try:
        record = store.load(session_id)
        items, waiting, partial, made = _compute_checks(request, session_id, record)
        known = {p["proposal_id"] for p in record.get("proposals") or []}
        if [p for p in made if p["proposal_id"] not in known] and not record.get("emitted"):
            seen = record.get("draft")

            def add(current: dict[str, Any]) -> None:
                if current.get("draft") == seen:  # made against this draft; a newer save waits for the next run
                    for proposal in made:
                        proposals.add_open(current, proposal)

            record, _ = store.transact(session_id, add, answer=False)
            # The open-suggestions note counts what this very run recorded.
            items = [c for c in items if c["check_id"] != "REVIEW_PROPOSALS_OPEN"] + checks._proposals_open(record)
    except (DraftRefused, steps.StepRefused) as exc:
        raise _error(exc) from exc
    return _checks_answer(record, items, waiting, partial, body.step)


class DismissBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: str = Field(default="", max_length=steps.MAX_TEXT_CHARS)
    evidence_digest: str = Field(max_length=100)
    reason: str | None = Field(default=None, max_length=steps.MAX_TEXT_CHARS * 2)


class CheckRestoreBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: str = Field(default="", max_length=steps.MAX_TEXT_CHARS)


def _dismissal(request: Request, session_id: str, check_id: str, action: str, **kw: Any) -> dict[str, Any]:
    store = _store(request)

    def append(current: dict[str, Any]) -> tuple:
        # Judged on the record read inside the lock: a save landing between a read and
        # this write cannot make a dismissal of the old evidence (review of Part B, finding 3).
        computed = _compute_checks(request, session_id, current)
        checks.with_dismissals(computed[0], current.get("check_dismissals") or [])
        entry = checks.dismissal_entry(computed[0], current.get("check_dismissals") or [], check_id, action, **kw)
        current["check_dismissals"] = [*(current.get("check_dismissals") or []), entry]
        return computed

    try:
        record, (items, waiting, partial, _made) = store.transact(session_id, append, answer=False)
    except (DraftRefused, steps.StepRefused, checks.CheckRefused) as exc:
        raise _error(exc) from exc
    for item in items:
        item.update(status="open", dismissal=None, previously_dismissed=None)
    step = checks.CATALOGUE.get(check_id) or next(
        (c["step"] for c in items if c["check_id"] == check_id and c["subject"] == kw.get("subject", "")), None,
    )
    return _checks_answer(record, items, waiting, partial, step)


@router.post("/drafts/{session_id}/checks/{check_id}/dismiss")
def dismiss_check(session_id: str, check_id: str, body: DismissBody, request: Request) -> dict[str, Any]:
    """A side write: only ``check_dismissals`` changes, ``updated_at`` does not."""
    return _dismissal(
        request, session_id, check_id, "dismissed",
        subject=body.subject, evidence_digest=body.evidence_digest, reason=body.reason,
    )


@router.post("/drafts/{session_id}/checks/{check_id}/restore")
def restore_check(session_id: str, check_id: str, body: CheckRestoreBody, request: Request) -> dict[str, Any]:
    return _dismissal(request, session_id, check_id, "restored", subject=body.subject)


# --- proposals (M10b, docs/ux/shared/final/01-proposals.md) -------------------


@router.get("/drafts/{session_id}/next-step")
def draft_next_step(session_id: str, request: Request) -> dict[str, Any]:
    """The next-step bar of a draft (M10b Part C, ``04-next-step`` rows 2 to 5); a read that records nothing."""
    from scholar_harness.console import next_step

    try:
        record = _store(request).load(session_id)
    except DraftRefused as exc:
        raise _error(exc) from exc
    answer = None
    if not record.get("emitted"):
        try:
            items, waiting, partial, _made = _compute_checks(request, session_id, record)
            answer = _checks_answer(record, items, waiting, partial, None)
        except Exception:  # noqa: BLE001 - checks that cannot be computed are "unknown", never a 5xx
            answer = None
    return next_step.build_draft(record, answer)


@router.get("/drafts/{session_id}/proposals")
def list_proposals(session_id: str, request: Request, step: str | None = None) -> dict[str, Any]:
    if step is not None and step not in proposals.PROPOSAL_STEPS:
        raise _error(steps.StepRefused(
            "STEP_UNKNOWN", f"unknown step {step!r}", status=404, details={"steps": list(proposals.PROPOSAL_STEPS)},
        ))
    try:
        return proposals.listing(_store(request).load(session_id), step)
    except DraftRefused as exc:
        raise _error(exc) from exc


class ApplyBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base_updated_at: str


class ApplyEditedBody(ApplyBody):
    value: Any


class RejectBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str | None = Field(default=None, max_length=steps.MAX_TEXT_CHARS)


class RestoreBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _decide(
    request: Request, session_id: str, proposal_id: str, action: str, *, answer: bool,
    base_updated_at: str | None = None, value: Any = None, reason: str | None = None,
) -> dict[str, Any]:
    def change(record: dict[str, Any]) -> None:
        proposals.decide(record, proposal_id, action, value=value, reason=reason)

    try:
        record, _ = _store(request).transact(session_id, change, answer=answer, base_updated_at=base_updated_at)
    except (DraftRefused, steps.StepRefused, proposals.ProposalRefused) as exc:
        raise _error(exc) from exc
    return {
        "session_id": session_id, "draft": record["draft"], "updated_at": record["updated_at"],
        **{k: v for k, v in proposals.listing(record).items() if k in ("proposals", "by_step")},
    }


@router.post("/drafts/{session_id}/proposals/{proposal_id}/apply")
def apply_proposal(session_id: str, proposal_id: str, body: ApplyBody, request: Request) -> dict[str, Any]:
    """An answer write: the value goes through the same validation as a save of the field."""
    return _decide(request, session_id, proposal_id, "apply", answer=True, base_updated_at=body.base_updated_at)


@router.post("/drafts/{session_id}/proposals/{proposal_id}/apply-edited")
def apply_edited_proposal(session_id: str, proposal_id: str, body: ApplyEditedBody, request: Request) -> dict[str, Any]:
    return _decide(
        request, session_id, proposal_id, "apply_edited", answer=True,
        base_updated_at=body.base_updated_at, value=body.value,
    )


@router.post("/drafts/{session_id}/proposals/{proposal_id}/reject")
def reject_proposal(session_id: str, proposal_id: str, body: RejectBody, request: Request) -> dict[str, Any]:
    """A side write: no field and no ``updated_at`` change."""
    return _decide(request, session_id, proposal_id, "reject", answer=False, reason=body.reason)


@router.post("/drafts/{session_id}/proposals/{proposal_id}/restore")
def restore_proposal(session_id: str, proposal_id: str, body: RestoreBody, request: Request) -> dict[str, Any]:
    return _decide(request, session_id, proposal_id, "restore", answer=False)


@router.delete("/drafts/{session_id}", status_code=204)
def discard_draft(session_id: str, request: Request) -> Response:
    try:
        _store(request).discard(session_id)
    except DraftRefused as exc:
        raise _error(exc) from exc
    return Response(status_code=204)


@router.post("/steps/{step}")
def run_step(step: str, body: DraftBody) -> dict[str, Any]:
    try:
        return steps.run_step(step, body.draft)
    except steps.StepRefused as exc:
        raise _error(exc) from exc


@router.post("/preview")
def preview(body: PreviewBody, request: Request) -> dict[str, Any]:
    try:
        grounding = None
        if body.session_id is not None:
            stored = _store(request).load(body.session_id)
            grounding = stored.get("grounding")
            if grounding:
                refuse_stale(_recon(request), grounding, scope_of(steps.parse_draft(body.draft)), _left_out(stored))
        answer = steps.preview(body.draft, workspaces_root=_root(request), grounding=grounding)
        if body.session_id is not None:
            # M11a (DoD 15): the files genesis writes from the draft's query development.
            from scholar_harness import query_workbench_sets as qs

            answer["files"] += [f for f in qs.development_files(_store(request).dir / body.session_id / "query_development")
                                if f not in answer["files"]]
        return answer
    except (DraftRefused, steps.StepRefused, ReconRefused) as exc:
        raise _error(exc) from exc


def _running_job(request: Request, target: Path) -> str | None:
    """A discovery or console job of this process still running in ``target`` (M4d, F1 review)."""
    resolved = Path(target).resolve()
    discovery = getattr(request.app.state, "discovery_jobs", None)
    if discovery is not None:
        job = discovery.active(resolved) or discovery.active(Path(target))
        if job is not None:
            return f"discovery job {job.job_id} ({job.kind})"
    runner = getattr(request.app.state, "job_runner", None)
    if runner is not None and Path(runner.workspace).resolve() == resolved:
        for job in runner.jobs.values():
            if job.state in ("queued", "running"):
                return f"console job {job.job_id} ({job.action_id})"
    return None


@router.post("/drafts/{session_id}/genesis", status_code=201)
def genesis(session_id: str, body: GenesisBody, request: Request) -> dict[str, Any]:
    store = _store(request)
    try:
        record = store.load(session_id)
        if record.get("emitted"):
            raise DraftRefused("DRAFT_EMITTED", "this draft already created a workspace", details={"emitted": record["emitted"]})
        grounding = record.get("grounding")
        if grounding:
            refuse_stale(_recon(request), grounding, scope_of(steps.parse_draft(record["draft"])), _left_out(record))
        result = steps.genesis(
            record["draft"],
            grounding=grounding,
            workspaces_root=_root(request),
            agent=UI_AGENT,
            replace=body.replace,
            confirm_discard_screening_binding=body.confirm_discard_screening_binding,
            busy=lambda target: _running_job(request, target),
            origin=record.get("origin"),
            record=record,
            # M11a (DoD 15): the search's development beside the draft goes into the workspace.
            query_development=store.dir / session_id / "query_development",
        )
        # The backup and the previous fingerprint too, so Done shows them after a reload (M4b).
        kept = ("slug", "path", "protocol_fingerprint", "replaced", "previous_fingerprint", "backup_dir", "archived")
        store.mark_emitted(session_id, {k: result[k] for k in kept if result.get(k) is not None})
    except (DraftRefused, steps.StepRefused, ReconRefused) as exc:
        raise _error(exc) from exc
    return {"session_id": session_id, **result}
