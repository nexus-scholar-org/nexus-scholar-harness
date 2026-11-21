"""The charting table's routes (M12a Part A; `docs/ux/phase3-extraction/final/01-charting-table.md`).

``GET /api/v1/charting`` lists every kept record of every published round
with its full-text status, file or link and full-text decision;
``POST /api/v1/charting/events`` stores status, decision and link events (and
their undo); ``POST /api/v1/charting/records/{study_id}/attachment`` takes the
researcher's PDF as the raw request body (``application/pdf``) or a link as
JSON; ``GET`` on the same path serves the PDF back; ``GET /api/v1/charting/export``
writes the Full text view as CSV. No route here sends an outgoing request.

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
from ...charting import table as tb

router = APIRouter(prefix="/api/v1/charting", tags=["charting"])


def _ws(request: Request):
    return request.app.state.workspace


def _error(exc: ChartingRefused) -> HTTPException:
    return HTTPException(status_code=exc.status, detail={"code": exc.code, "message": exc.message, **exc.details})


class EventsBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[Any] = Field(min_length=1, max_length=200)


class LinkBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    link: str | None = Field(default=None, max_length=2_000)
    event_id: str | None = None
    supersedes: str | None = None


@router.get("")
def get_table(request: Request) -> dict[str, Any]:
    """The kept rows of every published round, their full-text state and the counts line."""
    try:
        return tb.table(_ws(request))
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
