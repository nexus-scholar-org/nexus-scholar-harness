"""The charting table's routes (M12a Part A; `docs/ux/phase3-extraction/final/01-charting-table.md`).

``GET /api/v1/charting`` lists every kept record of every published round
with its full-text status, file or link and full-text decision;
``POST /api/v1/charting/events`` stores status, decision and link events (and
their undo); ``POST /api/v1/charting/records/{study_id}/attachment`` takes the
researcher's PDF as the raw request body (``application/pdf``) or a link as
JSON; ``GET`` on the same path serves the PDF back; ``GET /api/v1/charting/export``
writes the Full text view as CSV.

Part F (``charting/fetch.py``) adds the look-up of open-access copies, the
only routes here that make the console send requests, and only once the
researcher starts a run: ``GET /api/v1/charting/fetch/plan`` (sends nothing),
``POST /api/v1/charting/fetch`` (``dry: true`` answers the plan; otherwise
starts the run, 202), ``GET /api/v1/charting/fetch`` (the run's state),
``POST /api/v1/charting/fetch/cancel``, ``GET …/records/{id}/fetch`` (what
was tried) and ``GET …/records/{id}/fetched`` (the waiting file). Confirm and
discard are event kinds on ``POST /api/v1/charting/events``.

Desktop only: none of these is on the phone allowlist.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from starlette.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from ...charting import ChartingRefused
from ...charting import attachments as att
from ...charting import fetch as fx
from ...charting import table as tb

router = APIRouter(prefix="/api/v1/charting", tags=["charting"])


def _ws(request: Request):
    return request.app.state.workspace


def _error(exc: ChartingRefused) -> HTTPException:
    return HTTPException(status_code=exc.status, detail={"code": exc.code, "message": exc.message, **exc.details})


class EventsBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[Any] = Field(min_length=1, max_length=200)


class FormBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base_version: int
    columns: list[Any] = Field(max_length=40)
    reason: str | None = Field(default=None, max_length=500)


class PilotBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base_version: int


class LinkBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    link: str | None = Field(default=None, max_length=2_000)
    event_id: str | None = None
    supersedes: str | None = None


class FetchBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    #: The selected records; absent: every record To get (spec 03, question 5).
    ids: list[str] | None = Field(default=None, max_length=5_000)
    scope: str | None = Field(default=None, pattern="^to_get$")
    #: The plan, sending nothing.
    dry: bool = False
    #: The researcher confirmed the plan (Enter on its line); required to start.
    confirm: bool = False


@router.get("")
def get_table(request: Request) -> dict[str, Any]:
    """The kept rows of every published round, their full-text state and the counts line."""
    try:
        return tb.table(_ws(request))
    except ChartingRefused as exc:
        raise _error(exc) from exc


@router.get("/form")
def get_form(request: Request) -> dict[str, Any]:
    """The charting form beside the protocol (seeded at the first visit) and its amendments."""
    try:
        return tb.get_form(_ws(request))
    except ChartingRefused as exc:
        raise _error(exc) from exc


@router.put("/form")
def put_form(body: FormBody, request: Request) -> dict[str, Any]:
    """A new form version; once any cell holds a value, a recorded amendment that needs a one-sentence reason."""
    try:
        return tb.put_form(_ws(request), body.columns, base_version=body.base_version, reason=body.reason)
    except ChartingRefused as exc:
        raise _error(exc) from exc


@router.post("/form/pilot/end")
def end_pilot(body: PilotBody, request: Request) -> dict[str, Any]:
    """"End pilot", recorded once (``CHARTING_PILOT_ENDED``)."""
    try:
        return tb.end_pilot(_ws(request), base_version=body.base_version)
    except ChartingRefused as exc:
        raise _error(exc) from exc


@router.get("/records/{study_id}")
def get_record(study_id: str, request: Request) -> dict[str, Any]:
    """One study for the one-study view."""
    try:
        return tb.record(_ws(request), study_id)
    except ChartingRefused as exc:
        raise _error(exc) from exc


@router.post("/events")
def post_events(body: EventsBody, request: Request) -> dict[str, Any]:
    """Status (one or many records), a full-text decision (one study per request), a link, or an undo."""
    try:
        return tb.post_events(_ws(request), body.events)
    except ChartingRefused as exc:
        raise _error(exc) from exc


@router.post("/records/{study_id}/attachment")
async def post_attachment(
    study_id: str, request: Request, name: str | None = None, event_id: str | None = None,
    status_event_id: str | None = None,
) -> dict[str, Any]:
    """The researcher's PDF (raw ``application/pdf`` body, at most 100 MB) or a link (JSON ``{link}``)."""
    ws = _ws(request)
    content_type = (request.headers.get("content-type") or "").split(";", 1)[0].strip().lower()
    try:
        if content_type == "application/json":
            body = LinkBody.model_validate_json(await request.body())
            return await run_in_threadpool(
                tb.set_link, ws, study_id, body.link, event_id=body.event_id, supersedes=body.supersedes)
        # Review finding 5: the lock, the hashing and the file moves run off the event loop.
        await run_in_threadpool(tb.check_attach, ws, study_id, (event_id, status_event_id))
        declared = request.headers.get("content-length")
        stager = att.Stager(ws, declared_size=int(declared) if declared and declared.isdigit() else None)
        try:
            async for chunk in request.stream():
                stager.write(chunk)
        except BaseException:
            stager.abort()
            raise
        staged = stager.finish()
        return await run_in_threadpool(
            tb.attach_staged, ws, study_id, staged, name=name, event_id=event_id, status_event_id=status_event_id)
    except ChartingRefused as exc:
        raise _error(exc) from exc
    except ValueError as exc:  # a link body pydantic refuses
        raise HTTPException(status_code=422, detail={"code": "BODY_INVALID", "message": str(exc)[:500]}) from exc


@router.get("/records/{study_id}/attachment")
def get_attachment(study_id: str, request: Request) -> Response:
    """The attached PDF, served by the local console to open in a new tab."""
    try:
        found = tb.attachment_file(_ws(request), study_id)
    except ChartingRefused as exc:
        raise _error(exc) from exc
    if found is None:
        raise HTTPException(status_code=404, detail={"code": "ATTACHMENT_MISSING", "message": "No PDF is attached."})
    path, name = found
    return FileResponse(path, media_type="application/pdf", filename=name, content_disposition_type="inline")


@router.get("/export")
def get_export(request: Request, format: str = "csv", view: str = "fulltext") -> Response:  # noqa: A002
    """The Full text view as CSV (UTF-8 with BOM, CRLF); journaled with the file's SHA-256."""
    try:
        body, name = tb.export(_ws(request), fmt=format, view=view)
    except ChartingRefused as exc:
        raise _error(exc) from exc
    return Response(
        content=body, media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


# --------------------------------------------------------------------------- Part F: open-access copies


@router.get("/fetch/plan")
def get_fetch_plan(request: Request, ids: str | None = None) -> dict[str, Any]:
    """The look-up plan for every To get record, or ``ids`` (comma-separated). No request is sent."""
    chosen = [i for i in (ids or "").split(",") if i] or None
    try:
        return fx.plan(_ws(request), chosen)
    except ChartingRefused as exc:
        raise _error(exc) from exc


@router.post("/fetch")
def post_fetch(body: FetchBody, request: Request, response: Response) -> dict[str, Any]:
    """``dry``: the plan. Otherwise one run for the workspace (``FETCH_ALREADY_ACTIVE``), started in the background."""
    ids = body.ids if body.ids is not None else None
    if body.ids is not None and body.scope is not None:
        raise HTTPException(status_code=422, detail={"code": "BODY_INVALID", "message": "send ids or scope, not both"})
    try:
        if body.dry:
            return fx.plan(_ws(request), ids)
        if not body.confirm:
            raise ChartingRefused(422, "BODY_INVALID", "A look-up starts only with confirm: true, after its plan.")
        run = fx.start(
            _ws(request), ids,
            executor=getattr(request.app.state, "fetch_executor", None),
            deps=getattr(request.app.state, "fetch_deps", None),
        )
    except ChartingRefused as exc:
        raise _error(exc) from exc
    response.status_code = 202
    return fx._view(_ws(request), run, just_started=True)


@router.get("/fetch")
def get_fetch(request: Request) -> dict[str, Any]:
    """The running look-up, else the newest one (``interrupted`` when this console did not finish it), else idle."""
    return fx.current(_ws(request))


@router.post("/fetch/cancel")
def post_fetch_cancel(request: Request) -> dict[str, Any]:
    """Stop the look-up after the record in hand; the records it reached keep their manifest rows."""
    return fx.cancel(_ws(request))


@router.get("/records/{study_id}/fetch")
def get_fetch_tried(study_id: str, request: Request) -> dict[str, Any]:
    """What was tried for one record: its rows of ``charting/fetch_manifest.jsonl``."""
    try:
        return fx.tried(_ws(request), study_id)
    except ChartingRefused as exc:
        raise _error(exc) from exc


@router.get("/records/{study_id}/fetched")
def get_fetched_file(study_id: str, request: Request) -> Response:
    """The fetched file waiting on a record, to open before confirming it (``FETCH_NOT_PENDING`` when none)."""
    try:
        path, name = fx.fetched_file(_ws(request), study_id)
    except ChartingRefused as exc:
        raise _error(exc) from exc
    return FileResponse(path, media_type="application/pdf", filename=name, content_disposition_type="inline",
                        headers={"X-Content-Type-Options": "nosniff"})
