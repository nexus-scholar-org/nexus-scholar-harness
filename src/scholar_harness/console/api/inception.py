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
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from scholar_harness.inception import steps
from scholar_harness.inception.drafts import DraftRefused, DraftStore
from scholar_harness.inception.grounding import refuse_stale, scope_of
from scholar_harness.recon.session import ReconRefused, ReconSessions

router = APIRouter(prefix="/api/v1/inception", tags=["inception"])

#: The journal agent for writes made from the browser (as the workspaces routes).
UI_AGENT = "nexus-scholar/ui"


def _error(exc: DraftRefused | steps.StepRefused | ReconRefused) -> HTTPException:
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


class SaveBody(DraftBody):
    #: The ``updated_at`` the client last read; a newer save on disk refuses with DRAFT_CONFLICT.
    base_updated_at: str | None = None


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
        steps.parse_draft(body.draft)
        return _store(request).create(body.draft)
    except (DraftRefused, steps.StepRefused) as exc:
        raise _error(exc) from exc


@router.get("/drafts/{session_id}")
def read_draft(session_id: str, request: Request) -> dict[str, Any]:
    try:
        return _store(request).load(session_id)
    except DraftRefused as exc:
        raise _error(exc) from exc


@router.put("/drafts/{session_id}")
def save_draft(session_id: str, body: SaveBody, request: Request) -> dict[str, Any]:
    try:
        steps.parse_draft(body.draft)
        return _store(request).save(session_id, body.draft, base_updated_at=body.base_updated_at)
    except (DraftRefused, steps.StepRefused) as exc:
        raise _error(exc) from exc


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
            grounding = _store(request).load(body.session_id).get("grounding")
            if grounding:
                refuse_stale(_recon(request), grounding, scope_of(steps.parse_draft(body.draft)))
        return steps.preview(body.draft, workspaces_root=_root(request), grounding=grounding)
    except (DraftRefused, steps.StepRefused, ReconRefused) as exc:
        raise _error(exc) from exc


@router.post("/drafts/{session_id}/genesis", status_code=201)
def genesis(session_id: str, body: GenesisBody, request: Request) -> dict[str, Any]:
    store = _store(request)
    try:
        record = store.load(session_id)
        if record.get("emitted"):
            raise DraftRefused("DRAFT_EMITTED", "this draft already created a workspace", details={"emitted": record["emitted"]})
        grounding = record.get("grounding")
        if grounding:
            refuse_stale(_recon(request), grounding, scope_of(steps.parse_draft(record["draft"])))
        result = steps.genesis(
            record["draft"],
            grounding=grounding,
            workspaces_root=_root(request),
            agent=UI_AGENT,
            replace=body.replace,
            confirm_discard_screening_binding=body.confirm_discard_screening_binding,
        )
        # The backup and the previous fingerprint too, so Done shows them after a reload (M4b).
        kept = ("slug", "path", "protocol_fingerprint", "replaced", "previous_fingerprint", "backup_dir", "archived")
        store.mark_emitted(session_id, {k: result[k] for k in kept if result.get(k) is not None})
    except (DraftRefused, steps.StepRefused, ReconRefused) as exc:
        raise _error(exc) from exc
    return {"session_id": session_id, **result}
