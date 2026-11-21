"""The query workbench over HTTP (M11a Part A; spec `docs/ux/phase0-inception/final/10-query-workbench.md`).

Two places, one engine (``scholar_harness.query_workbench``):

* Inception, before the freeze: ``POST /api/v1/inception/drafts/{id}/workbench/{counts,synonyms,removed}``.
  The version is sent by the browser and need not be saved; the count log is
  beside the draft record.
* Plan, after the freeze: ``POST /api/v1/discovery/workbench/{counts,synonyms,removed}``
  for the open workspace; the count log is ``audit/query_development/counts.jsonl``.
  Counting still works after the corpus is accepted: it changes nothing in the
  protocol or the corpus; the count log under ``audit/`` still gets its rows (DoD 22).

Part B adds ``…/workbench/seeds`` (the seed check), ``…/workbench/comparison``
(``GET`` the sets, ``POST`` stage one) and ``…/workbench/comparison/{cmp}/remove``
and ``…/report``.

Every route that can send a request takes ``dry_run``: it sends nothing and states the requests a real
call would send. Nothing is counted on a keystroke: the browser sends a real
call only on Count. Refusals are sent before any request: ``BODY_INVALID``,
``WORKBENCH_VERSION_INVALID`` (422), ``PROVIDER_UNKNOWN`` (422),
``MAILTO_NOT_SET`` and ``DISCOVERY_JOB_ACTIVE`` (409, real calls only),
``WORKBENCH_BUDGET_SPENT`` (409), the draft refusals and the protocol refusals.
"""

from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from scholar_search import workbench as wb
from scholar_search.config import settings
from scholar_search.estimate import SIZE_WARN_WORKS
from scholar_search.plan import DEFAULT_PROVIDERS

from ... import query_workbench as qw
from ... import query_workbench_sets as qs
from ...inception.drafts import DraftRefused, DraftStore
from .. import refusals
from . import discovery as disc_api

router = APIRouter(tags=["workbench"])

ENGINE_CEILING = disc_api.ENGINE_CEILING


class ConceptBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    concept: str = Field(default="", max_length=wb.MAX_TERM_CHARS)
    synonyms: list[str] = Field(default_factory=list, max_length=wb.MAX_TERMS)


class VersionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query_key: str = Field(default=wb.DEFAULT_QUERY_KEY, max_length=40)
    concepts: list[ConceptBody] = Field(default_factory=list, max_length=wb.MAX_CONCEPTS)
    start_year: int | None = None
    end_year: int | None = None
    languages: list[str] = Field(default_factory=lambda: ["en"], max_length=20)


class CountsBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: VersionBody
    #: The databases to ask, in order; default: the four at Inception, the protocol's list on Plan.
    providers: list[str] | None = Field(default=None, max_length=10)
    dry_run: bool = False
    #: Count Crossref's full query for a query of two or more concepts ("Count anyway").
    crossref_anyway: bool = False


class SynonymsBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: VersionBody
    concept_index: int
    provider: str = "openalex"
    dry_run: bool = False


class RemovedBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: VersionBody
    concept_index: int
    dry_run: bool = False


@dataclass
class _Place:
    log: qw.CountLog
    cap: int | None
    limit: dict[str, Any]
    default_providers: list[str]
    scope: dict[str, Any]
    workspace: Path | None


def _refusal(status: int, code: str, message: str, details: dict[str, Any] | None = None) -> HTTPException:
    detail: dict[str, Any] = {"code": code, "message": message}
    if details:
        detail["details"] = details
    return HTTPException(status_code=status, detail=detail)


def _state(request: Request) -> qw.SharedState:
    return qw.SharedState(Path(request.app.state.workspaces_root))


def _version(body: VersionBody) -> wb.Version:
    try:
        return wb.parse_version(body.model_dump())
    except wb.VersionInvalid as exc:
        raise _refusal(422, refusals.WORKBENCH_VERSION_INVALID, f"This version cannot be searched: {exc}.") from exc


def _draft_place(request: Request, session_id: str) -> _Place:
    store = DraftStore(Path(request.app.state.workspaces_root))
    try:
        record = store.load(session_id)
    except DraftRefused as exc:
        raise _refusal(exc.status, exc.code, exc.message, exc.details) from exc
    if record.get("emitted"):
        raise _refusal(409, "DRAFT_EMITTED", "this draft already created a workspace; count on Plan",
                       {"emitted": record["emitted"]})
    planned = (record.get("draft") or {}).get("pool_max")
    limit = ({"value": planned, "source": "planned"} if isinstance(planned, int) and not isinstance(planned, bool)
             and planned > 0 else {"value": SIZE_WARN_WORKS, "source": "general"})
    return _Place(qw.CountLog(qw.draft_log_path(store.dir, session_id)), None, limit, list(DEFAULT_PROVIDERS),
                  {"draft": session_id}, None)


def _workspace_place(request: Request) -> _Place:
    from ...size_limit import size_limit

    ws = Path(request.app.state.workspace)
    try:
        proto = disc_api._protocol(ws)
    except disc_api.Refused as exc:
        raise disc_api._http(exc) from exc
    query = proto.query
    cap = int(query.max_results) if query.max_results and query.cap_source == "protocol" else None
    return _Place(qw.CountLog(qw.workspace_log_path(ws)), cap, size_limit(ws), list(proto.providers),
                  {"workspace": ws.name, "protocol_fingerprint": proto.fingerprint}, ws)


def _names(providers: list[str] | None, default: list[str]) -> list[str]:
    try:
        chosen = disc_api._check_providers(providers)
    except disc_api.Refused as exc:
        raise disc_api._http(exc) from exc
    return chosen if chosen is not None else default


def _guard_send(request: Request, place: _Place) -> None:
    """A real call: the contact email, and no harvest or recall check running (their rate limits)."""
    try:
        disc_api._require_mailto()
        ws = place.workspace if place.workspace is not None else getattr(request.app.state, "workspace", None)
        if ws is not None:
            disc_api._refuse_busy(disc_api._jobs(request), Path(ws))
    except disc_api.Refused as exc:
        raise disc_api._http(exc) from exc


def _size(place: _Place) -> dict[str, Any]:
    return {"cap": place.cap if place.cap is not None else ENGINE_CEILING, "limit": place.limit, "query_cap": place.cap}


async def _counts(request: Request, place: _Place, body: CountsBody) -> dict[str, Any]:
    version = _version(body.version)
    names = _names(body.providers, place.default_providers)
    if not body.dry_run:
        _guard_send(request, place)
    try:
        answer = await qw.run(version, names, log=place.log, state=_state(request), dry_run=body.dry_run,
                              size=_size(place), crossref_anyway=body.crossref_anyway,
                              openalex_key=bool(settings.openalex_key), scope=place.scope)
    except qw.WorkbenchRefused as exc:
        raise _refusal(exc.status, exc.code, exc.message, exc.details) from exc
    return answer | {"mailto_set": bool(settings.mailto)}


async def _synonyms(request: Request, place: _Place, body: SynonymsBody) -> dict[str, Any]:
    version = _version(body.version)
    names = _names([body.provider], place.default_providers)
    if not 0 <= body.concept_index < len(version.concepts):
        raise _refusal(422, refusals.WORKBENCH_VERSION_INVALID,
                       f"This version cannot be searched: it has no concept {body.concept_index}.")
    if not body.dry_run:
        _guard_send(request, place)
    try:
        answer = await qw.run(version, names, log=place.log, state=_state(request), dry_run=body.dry_run,
                              size=_size(place), mode="synonyms", concept_index=body.concept_index,
                              openalex_key=bool(settings.openalex_key), scope=place.scope)
    except qw.WorkbenchRefused as exc:
        raise _refusal(exc.status, exc.code, exc.message, exc.details) from exc
    return answer | {"mailto_set": bool(settings.mailto)}


async def _removed(request: Request, place: _Place, body: RemovedBody) -> dict[str, Any]:
    version = _version(body.version)
    if len(version.concepts) < 2 or not 0 <= body.concept_index < len(version.concepts):
        raise _refusal(422, refusals.WORKBENCH_VERSION_INVALID,
                       "This version cannot be searched: reading what a concept removes needs two or more concepts "
                       "and one of them.")
    if not body.dry_run:
        _guard_send(request, place)
    try:
        answer = await qw.read_removed(version, body.concept_index, log=place.log, state=_state(request),
                                       dry_run=body.dry_run, openalex_key=bool(settings.openalex_key),
                                       scope=place.scope)
    except qw.WorkbenchRefused as exc:
        raise _refusal(exc.status, exc.code, exc.message, exc.details) from exc
    return answer | {"mailto_set": bool(settings.mailto)}


# --------------------------------------------------------------------------- Inception (a draft)


@router.post("/api/v1/inception/drafts/{session_id}/workbench/counts")
async def draft_counts(session_id: str, body: CountsBody, request: Request) -> dict[str, Any]:
    return await _counts(request, _draft_place(request, session_id), body)


@router.post("/api/v1/inception/drafts/{session_id}/workbench/synonyms")
async def draft_synonyms(session_id: str, body: SynonymsBody, request: Request) -> dict[str, Any]:
    return await _synonyms(request, _draft_place(request, session_id), body)


@router.post("/api/v1/inception/drafts/{session_id}/workbench/removed")
async def draft_removed(session_id: str, body: RemovedBody, request: Request) -> dict[str, Any]:
    return await _removed(request, _draft_place(request, session_id), body)


# --------------------------------------------------------------------------- Plan (the open workspace)


@router.post("/api/v1/discovery/workbench/counts")
async def workspace_counts(body: CountsBody, request: Request) -> dict[str, Any]:
    return await _counts(request, _workspace_place(request), body)


@router.post("/api/v1/discovery/workbench/synonyms")
async def workspace_synonyms(body: SynonymsBody, request: Request) -> dict[str, Any]:
    return await _synonyms(request, _workspace_place(request), body)


@router.post("/api/v1/discovery/workbench/removed")
async def workspace_removed(body: RemovedBody, request: Request) -> dict[str, Any]:
    return await _removed(request, _workspace_place(request), body)


# --------------------------------------------------------------------------- Part B: known papers and comparison sets


class SeedsBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: VersionBody
    #: The known papers' DOIs; default: the draft's saved ``golden_seeds`` (Inception) or the protocol's (Plan).
    seeds: list[str] | None = Field(default=None, max_length=25)
    #: Read the title and abstract of a seed this computer has not seen, from OpenAlex (one request per 50).
    lookup: bool = False
    #: "Check seeds in OpenAlex": found or not by the query (one request per 50; behind the switch).
    openalex: bool = False
    dry_run: bool = False


class StageBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_name: str = Field(max_length=300)
    content_base64: str
    database: str = Field(min_length=1, max_length=200)
    string: str | None = Field(default=None, max_length=20_000)
    exported_on: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class ReportBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: VersionBody
    measure: Literal["harvest", "words", "openalex"] = "words"
    page: int = Field(default=1, ge=1, le=1000)
    #: The run to compare with on Plan (``run_NNN``); default the newest, or the accepted corpus.
    run: str | None = Field(default=None, pattern=r"^run_\d{3,}$")
    dry_run: bool = False


def _known_for_draft(request: Request, session_id: str) -> tuple[list[dict[str, Any]], list[str]]:
    """The first search's pool records (title, abstract, DOI) and the draft's saved seeds."""
    from ...recon.session import ReconRefused, ReconSessions

    record = DraftStore(Path(request.app.state.workspaces_root)).load(session_id)
    seeds = list((record.get("draft") or {}).get("golden_seeds") or [])
    sessions = ReconSessions(root=getattr(request.app.state, "recon_root", None),
                             search_fn=getattr(request.app.state, "recon_search_fn", None))
    docs: list[dict[str, Any]] = []
    try:
        if sessions.exists(session_id):
            _pool, raw, _path = sessions.effective(session_id, None)
            docs = [d for d in (raw.get("docs") or []) if isinstance(d, dict)]
    except ReconRefused:
        docs = []
    return [qs.row_record(d) for d in docs], seeds


def _known_for_workspace(ws: Path) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        protocol = {}
    seeds = [str(s) for s in ((protocol.get("search_strategy") or {}).get("golden_seeds") or [])]
    _label, records = qs.harvest_records(ws)
    return records, seeds


async def _seeds(request: Request, place: _Place, body: SeedsBody, known: list[dict[str, Any]], saved: list[str]) -> dict[str, Any]:
    version = _version(body.version)
    dois = list(body.seeds) if body.seeds is not None else saved
    if not body.dry_run and (body.lookup or body.openalex):
        # Review B7: refuse for the contact email or a running job only when a request will be sent.
        try:
            planned = await qs.seeds(version, dois, log=place.log, state=_state(request), known=known,
                                     lookup=body.lookup, openalex=body.openalex,
                                     openalex_key=bool(settings.openalex_key), dry_run=True, scope=place.scope)
        except qw.WorkbenchRefused as exc:
            raise _refusal(exc.status, exc.code, exc.message, exc.details) from exc
        if planned["cost"]["lookup"] or planned["cost"]["openalex"]:
            _guard_send(request, place)
    try:
        answer = await qs.seeds(version, dois, log=place.log, state=_state(request), known=known, lookup=body.lookup,
                                openalex=body.openalex, openalex_key=bool(settings.openalex_key),
                                dry_run=body.dry_run, scope=place.scope)
    except qw.WorkbenchRefused as exc:
        raise _refusal(exc.status, exc.code, exc.message, exc.details) from exc
    return answer | {"mailto_set": bool(settings.mailto)}


def _stage(place: _Place, body: StageBody) -> dict[str, Any]:
    try:
        content = base64.b64decode(body.content_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise _refusal(422, refusals.WORKBENCH_COMPARISON_FORMAT, f"{body.file_name} did not arrive as base64 file content") from exc
    try:
        return qs.stage_set(place.log, file_name=body.file_name, content=content, database=body.database,
                            string=body.string, exported_on=body.exported_on)
    except qw.WorkbenchRefused as exc:
        raise _refusal(exc.status, exc.code, exc.message, exc.details) from exc


def _remove(place: _Place, set_id: str) -> dict[str, Any]:
    try:
        qs.remove_set(place.log, set_id)
    except qw.WorkbenchRefused as exc:
        raise _refusal(exc.status, exc.code, exc.message, exc.details) from exc
    return {"sets": qs.list_sets(place.log)}


async def _report(request: Request, place: _Place, set_id: str, body: ReportBody) -> dict[str, Any]:
    version = _version(body.version)
    harvest = qs.harvest_records(place.workspace, body.run) if place.workspace is not None else None
    if body.measure == "openalex" and not body.dry_run and qs.openalex_ids_enabled():
        _guard_send(request, place)
    try:
        return await qs.report(place.log, set_id, version, measure=body.measure, page=body.page, state=_state(request),
                               harvest=harvest, openalex_key=bool(settings.openalex_key), dry_run=body.dry_run,
                               scope=place.scope)
    except qw.WorkbenchRefused as exc:
        raise _refusal(exc.status, exc.code, exc.message, exc.details) from exc


# Inception (a draft)


@router.post("/api/v1/inception/drafts/{session_id}/workbench/seeds")
async def draft_seeds(session_id: str, body: SeedsBody, request: Request) -> dict[str, Any]:
    place = _draft_place(request, session_id)
    known, saved = _known_for_draft(request, session_id)
    return await _seeds(request, place, body, known, saved)


@router.get("/api/v1/inception/drafts/{session_id}/workbench/comparison")
def draft_sets(session_id: str, request: Request) -> dict[str, Any]:
    return {"sets": qs.list_sets(_draft_place(request, session_id).log)}


@router.post("/api/v1/inception/drafts/{session_id}/workbench/comparison", status_code=201)
def draft_stage(session_id: str, body: StageBody, request: Request) -> dict[str, Any]:
    return _stage(_draft_place(request, session_id), body)


@router.post("/api/v1/inception/drafts/{session_id}/workbench/comparison/{set_id}/remove")
def draft_remove(session_id: str, set_id: str, request: Request) -> dict[str, Any]:
    return _remove(_draft_place(request, session_id), set_id)


@router.post("/api/v1/inception/drafts/{session_id}/workbench/comparison/{set_id}/report")
async def draft_report(session_id: str, set_id: str, body: ReportBody, request: Request) -> dict[str, Any]:
    return await _report(request, _draft_place(request, session_id), set_id, body)


# Plan (the open workspace)


@router.post("/api/v1/discovery/workbench/seeds")
async def workspace_seeds(body: SeedsBody, request: Request) -> dict[str, Any]:
    place = _workspace_place(request)
    known, saved = _known_for_workspace(place.workspace)
    return await _seeds(request, place, body, known, saved)


@router.get("/api/v1/discovery/workbench/comparison")
def workspace_sets(request: Request) -> dict[str, Any]:
    return {"sets": qs.list_sets(_workspace_place(request).log)}


@router.post("/api/v1/discovery/workbench/comparison", status_code=201)
def workspace_stage(body: StageBody, request: Request) -> dict[str, Any]:
    return _stage(_workspace_place(request), body)


@router.post("/api/v1/discovery/workbench/comparison/{set_id}/remove")
def workspace_remove(set_id: str, request: Request) -> dict[str, Any]:
    return _remove(_workspace_place(request), set_id)


@router.post("/api/v1/discovery/workbench/comparison/{set_id}/report")
async def workspace_report(set_id: str, body: ReportBody, request: Request) -> dict[str, Any]:
    return await _report(request, _workspace_place(request), set_id, body)
