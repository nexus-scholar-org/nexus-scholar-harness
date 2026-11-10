"""Discovery over HTTP for the open workspace (M3b-api; screens 01–08 of Phase 1).

The routes are fixed by `docs/architecture/research_ui/DISCOVERY_API_PACKET.md`
§4 (shapes), §4.7 (codes) and §6 (the researcher's decisions of 2026-11-10).

Layer R reads what the engine already writes (`literature/search_runs/`,
`literature/recall_checks/`, `deduped.json`, `verified.json`):

* ``GET /plan`` — the protocol's query and cap, the contact-address state and
  the providers (``executed_query`` stays ``null`` until the E1 dry run).
* ``GET /runs``, ``GET /runs/{run}``, ``GET /runs/{run}/report`` — the search runs.
* ``GET /report``, ``PUT /report/methods`` — the PRISMA-S style report of a run
  and its reviewed methods paragraph.
* ``GET /handoff`` — what the corpus looks like before screening.

Layer J starts work in this console process, as recon does (decision 1): one
running discovery job per workspace, ``MAILTO_NOT_SET`` and
``CORPUS_ALREADY_ACCEPTED`` refused before anything starts.

* ``POST /runs`` — the search run (``run_pipeline``); ``POST /recall`` — the
  check-only recall (``scholar_search.recall.check_seeds``, decision 3).
* ``GET /recall``, ``GET /jobs/{id}``, ``GET /jobs/{id}/events`` (SSE replayed
  on connect), ``POST /jobs/{id}/cancel``.
"""

from __future__ import annotations

import asyncio
import json
import re
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from scholar_search.config import settings

from ...pipeline import discovery as disc
from ...workspace.audit import append_event
from .. import refusals

router = APIRouter(prefix="/api/v1/discovery", tags=["discovery"])

AGENT = "scholar-harness-console"
ENGINE_CEILING = 10_000
#: Every database the engine can search, in the order the screens list them.
KNOWN_PROVIDERS = ("openalex", "semanticscholar", "crossref", "arxiv", "pubmed", "biorxiv")
DEFAULT_PROVIDERS = ("openalex", "semanticscholar", "crossref", "arxiv", "pubmed")
TERMINAL = ("succeeded", "failed", "cancelled")
#: Finished jobs kept per workspace; their results are on disk.
KEEP_FINISHED = 10
#: A leg event every this many records (and at the first and the last), so a
#: 10,000-record leg does not put 10,000 events in the replayed stream.
LEG_EVENT_EVERY = 25
#: How long a cancel waits for the job to stop before it answers.
CANCEL_WAIT_SECONDS = 30.0
RUN_NAME = re.compile(r"run_\d{3,}")
CHECK_NAME = re.compile(r"check_(\d{3,})\.json")


def _now() -> str:
    return datetime.now(UTC).isoformat()


class Refused(Exception):
    def __init__(self, status: int, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details


def _http(exc: Refused) -> HTTPException:
    detail: dict[str, Any] = {"code": exc.code, "message": exc.message}
    if exc.details:
        detail["details"] = exc.details
    return HTTPException(status_code=exc.status, detail=detail)


# --------------------------------------------------------------------------- jobs


@dataclass
class DiscoveryJob:
    job_id: str
    workspace: str
    kind: str
    state: str = "running"
    started_at: str = field(default_factory=_now)
    finished_at: str | None = None
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    cancel_requested: bool = False
    events: list[dict[str, Any]] = field(default_factory=list)
    changed: asyncio.Event = field(default_factory=asyncio.Event)
    task: asyncio.Task | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
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


class DiscoveryJobs:
    """In-memory discovery jobs of this console process; one running job per workspace."""

    def __init__(self) -> None:
        self.jobs: dict[str, DiscoveryJob] = {}

    def active(self, workspace: Path) -> DiscoveryJob | None:
        key = str(workspace)
        return next((j for j in self.jobs.values() if j.workspace == key and j.state not in TERMINAL), None)

    def _evict(self, workspace: Path) -> None:
        finished = [j for j in self.jobs.values() if j.workspace == str(workspace) and j.state in TERMINAL]
        finished.sort(key=lambda j: j.finished_at or "")
        for job in finished[: max(0, len(finished) - KEEP_FINISHED)]:
            self.jobs.pop(job.job_id, None)

    def start(self, workspace: Path, kind: str, work) -> DiscoveryJob:
        self._evict(workspace)
        job = DiscoveryJob(job_id="djob_" + uuid.uuid4().hex[:16], workspace=str(workspace), kind=kind)
        self.jobs[job.job_id] = job
        job.emit("snapshot", {"job": job.to_dict()})

        async def run() -> None:
            try:
                state, result, error = await work(job)
                job.state, job.result, job.error = state, result, error
            except Refused as exc:
                job.state = "failed"
                job.error = {"code": exc.code, "message": exc.message, "details": exc.details}
            except Exception as exc:  # noqa: BLE001 - a job reports its failure, never crashes the console
                job.state = "failed"
                job.error = {"code": refusals.DISCOVERY_FAILED, "message": f"{type(exc).__name__}: {str(exc)[:300]}"}
            job.finished_at = _now()
            job.emit("done" if job.state == "succeeded" else "failed", {"job": job.to_dict()})

        job.task = asyncio.get_running_loop().create_task(run())
        return job


    async def stop_all(self, timeout: float = CANCEL_WAIT_SECONDS) -> None:
        """Cancel every running job and wait for it (decision 1: a closed console
        keeps the fetched records as a ``PARTIAL`` run). A killed process cannot."""
        running = [j for j in self.jobs.values() if j.state not in TERMINAL and j.task is not None]
        for job in running:
            job.cancel_requested = True
        if running:
            await asyncio.wait({j.task for j in running}, timeout=timeout)


@asynccontextmanager
async def lifespan(app):
    """The console's lifespan: on shutdown, running discovery jobs are cancelled cleanly."""
    yield
    jobs = getattr(app.state, "discovery_jobs", None)
    if jobs is not None:
        await jobs.stop_all()


def _jobs(request: Request) -> DiscoveryJobs:
    jobs = getattr(request.app.state, "discovery_jobs", None)
    if jobs is None:
        jobs = request.app.state.discovery_jobs = DiscoveryJobs()
    return jobs


def _leg_reporter(job: DiscoveryJob):
    """A ``leg_callback`` that emits ``leg`` events, thinned to every ``LEG_EVENT_EVERY`` records."""
    last: dict[str, tuple[int, str]] = {}

    def on_leg(leg: Any) -> None:
        key = (int(leg.fetched), str(leg.status))
        if last.get(leg.provider) == key:
            return
        running = leg.status == "running"
        if running and leg.fetched != 1 and leg.fetched % LEG_EVENT_EVERY:
            return
        last[leg.provider] = key
        job.emit("leg", {
            "job_id": job.job_id, "provider": leg.provider, "fetched": leg.fetched,
            "reported_total": leg.reported_total, "cap": leg.cap, "cap_hit": leg.cap_hit,
            "status": leg.status, "error_code": leg.error_code,
        })

    return on_leg


# --------------------------------------------------------------------------- workspace reads


def _ws(request: Request) -> Path:
    return Path(request.app.state.workspace)


def _lit(ws: Path) -> Path:
    return ws / "literature"


def _canonical(name: str) -> str:
    key = str(name).lower().strip().replace("-", "_").replace(" ", "_")
    return "semanticscholar" if key == "semantic_scholar" else key


@dataclass
class _Protocol:
    path: Path
    query: Any
    providers: list[str]
    fingerprint: str


def _protocol(ws: Path) -> _Protocol:
    from pydantic import ValidationError
    from scholar_protocol.canonical import canonical_fingerprint
    from scholar_protocol.models import ResearchProtocol
    from scholar_search.protocol_adapter import compile_protocol_search

    path = ws / "protocol.json"
    if not path.is_file():
        raise Refused(409, refusals.PROTOCOL_MISSING, "This workspace has no protocol.json; finish inception first.")
    try:
        model = ResearchProtocol.model_validate_json(path.read_text(encoding="utf-8"))
        query, providers = compile_protocol_search(path)
    except (ValidationError, ValueError, TypeError) as exc:
        raise Refused(422, refusals.PROTOCOL_INVALID, f"protocol.json is not a valid protocol: {str(exc)[:300]}") from exc
    return _Protocol(path, query, [_canonical(p) for p in providers], canonical_fingerprint(model))


def _mailto_set() -> bool:
    return bool(settings.mailto)


def _require_mailto() -> None:
    if not _mailto_set():
        raise Refused(
            409, refusals.MAILTO_NOT_SET,
            "A search needs a contact email for the literature databases. Set SCHOLAR_MAILTO "
            "for the console (environment or .env) and start it again.",
        )


def _openalex_key_set() -> bool:
    return bool(settings.openalex_key)


def _require_openalex_key(providers: list[str]) -> None:
    """F12 (M3h-providers): OpenAlex requires an API key since 2026-02-13."""
    if "openalex" in providers and not _openalex_key_set():
        raise Refused(
            409, refusals.OPENALEX_KEY_NOT_SET,
            "OpenAlex needs an API key. Set SCHOLAR_OPENALEX_KEY for the console "
            "(environment or .env) and start it again, or leave OpenAlex out of this run.",
        )


def _check_providers(names: list[str] | None) -> list[str] | None:
    if names is None:
        return None
    unknown = [n for n in names if _canonical(n) not in KNOWN_PROVIDERS]
    if unknown or not names:
        raise Refused(422, refusals.PROVIDER_UNKNOWN, "Unknown or empty database list.",
                      details={"unknown": unknown, "known": list(KNOWN_PROVIDERS)})
    return [_canonical(n) for n in names]


def _run_dirs(ws: Path) -> list[Path]:
    """The archived search runs, newest first."""
    root = _lit(ws) / disc.SEARCH_RUNS_DIR
    if not root.is_dir():
        return []
    runs = [p for p in root.iterdir() if p.is_dir() and RUN_NAME.fullmatch(p.name) and (p / "legs.json").is_file()]
    return sorted(runs, key=lambda p: int(p.name[4:]), reverse=True)


def _manifest(run_dir: Path) -> dict[str, Any]:
    try:
        data = json.loads((run_dir / "legs.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {"run": run_dir.name, "status": "UNREADABLE", "legs": []}
    data.setdefault("legs", [])
    return data


def _run_dir(ws: Path, run: str) -> Path:
    if RUN_NAME.fullmatch(run):
        path = _lit(ws) / disc.SEARCH_RUNS_DIR / run
        if (path / "legs.json").is_file():
            return path
    raise Refused(404, refusals.RUN_NOT_FOUND, f"No search run {run} in this workspace.")


def _published(manifest: dict[str, Any]) -> bool:
    return bool(manifest.get("corpus_published", manifest.get("raw_published")))


def _run_summaries(ws: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    later_published = False
    for run_dir in _run_dirs(ws):
        manifest = _manifest(run_dir)
        legs = manifest["legs"]
        started = sorted(str(leg.get("started_at")) for leg in legs if leg.get("started_at"))
        finished = sorted(str(leg.get("finished_at")) for leg in legs if leg.get("finished_at"))
        out.append({
            "run": run_dir.name,
            "status": manifest.get("status"),
            "started_at": started[0] if started else None,
            "finished_at": finished[-1] if finished else None,
            "legs_total": len(legs),
            "fetched_total": sum(int(leg.get("fetched") or 0) for leg in legs),
            "raw_published": bool(manifest.get("raw_published")),
            "cap_override": manifest.get("cap_override"),
            # A later run whose records became the corpus makes this one's files stale.
            "stale": later_published,
        })
        later_published = later_published or _published(manifest)
    return out


def _runs_payload(request: Request) -> dict[str, Any]:
    ws = _ws(request)
    active = _jobs(request).active(ws)
    return {"shape": "discovery.runs-v1", "runs": _run_summaries(ws), "active_job": active.to_dict() if active else None}


def _checks(ws: Path) -> list[Path]:
    root = _lit(ws) / "recall_checks"
    if not root.is_dir():
        return []
    return sorted((p for p in root.iterdir() if CHECK_NAME.fullmatch(p.name)), key=lambda p: int(p.name[6:-5]))


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _preceding_check(ws: Path, started_at: str | None) -> dict[str, Any] | None:
    found = None
    for path in _checks(ws):
        check = _read_json(path, {})
        if started_at is None or str(check.get("checked_at") or "") <= started_at:
            found = {"check": path.stem, **{k: check.get(k) for k in ("checked_at", "found", "total", "missed_everywhere")}}
    return found


def _outside_window(rows: list[dict[str, Any]], query: Any) -> int:
    low, high = getattr(query, "year_min", None), getattr(query, "year_max", None)
    count = 0
    for row in rows:
        year = row.get("year", row.get("publication_year"))
        if not isinstance(year, int):
            continue
        if (low is not None and year < low) or (high is not None and year > high):
            count += 1
    return count


def _verified(ws: Path) -> list[dict[str, Any]]:
    rows = _read_json(_lit(ws) / "verified.json", [])
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


# --------------------------------------------------------------------------- Layer R routes


@router.get("/plan")
def plan(request: Request) -> dict[str, Any]:
    try:
        proto = _protocol(_ws(request))
    except Refused as exc:
        raise _http(exc) from exc
    query = proto.query
    if query.max_results and query.cap_source == "protocol":
        cap = {"value": int(query.max_results), "source": "protocol", "ceiling": ENGINE_CEILING}
    else:
        cap = {"value": ENGINE_CEILING, "source": "engine_ceiling", "ceiling": ENGINE_CEILING}
    from scholar_search.plan import compile_plan

    # E1 (M3d-engine): each selected database's translation, made without a request.
    providers = compile_plan(proto.path, KNOWN_PROVIDERS)["providers"]
    return {
        "shape": "discovery.plan-v1",
        "protocol_fingerprint": proto.fingerprint,
        "query": {"id": query.id, "text": query.text, "year_min": query.year_min,
                  "year_max": query.year_max, "language": query.language},
        "cap": cap,
        "mailto_set": _mailto_set(),
        "openalex_key_set": _openalex_key_set(),
        # M3h-providers: set, not verified; a rejected key fails the S2 leg.
        "s2_key_set": bool(settings.s2_key),
        "providers": providers,
        "imports_hint": ["scopus", "wos"],
    }


@router.get("/runs")
def runs(request: Request) -> dict[str, Any]:
    return _runs_payload(request)


@router.get("/runs/{run}")
def run_detail(run: str, request: Request) -> dict[str, Any]:
    ws = _ws(request)
    try:
        run_dir = _run_dir(ws, run)
    except Refused as exc:
        raise _http(exc) from exc
    manifest = _manifest(run_dir)
    started = sorted(str(leg.get("started_at")) for leg in manifest["legs"] if leg.get("started_at"))
    return {
        **manifest,
        "report_path": (run_dir / "search_report.md").relative_to(ws).as_posix(),
        "recall_check": _preceding_check(ws, started[0] if started else None),
        "cap_override": manifest.get("cap_override"),
    }


@router.get("/runs/{run}/report")
def run_report(run: str, request: Request) -> PlainTextResponse:
    try:
        run_dir = _run_dir(_ws(request), run)
    except Refused as exc:
        raise _http(exc) from exc
    path = run_dir / "search_report.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    return PlainTextResponse(text, media_type="text/markdown; charset=utf-8")


def _front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    head, _, body = text[4:].partition("\n---\n")
    meta = {}
    for line in head.splitlines():
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.strip()
    return meta, body.lstrip("\n")


def _stored_methods(run_dir: Path) -> dict[str, Any] | None:
    path = run_dir / "methods.md"
    if not path.is_file():
        return None
    meta, body = _front_matter(path.read_text(encoding="utf-8"))
    return {"text": body.rstrip("\n"), "reviewed": meta.get("reviewed") == "true", "reviewed_at": meta.get("reviewed_at") or None}


def _no_abstract_rates(run_dir: Path, legs: list[dict[str, Any]]) -> dict[str, float | None]:
    """Per database, the share of fetched records without an abstract, from ``raw.json``.

    The raw list is in provider order (the engine keeps it reproducible), so a
    leg's records are the next ``fetched`` rows; when the counts do not add up
    the rate is not given.
    """
    raw = _read_json(run_dir / "raw.json")
    if not isinstance(raw, list) or len(raw) != sum(int(leg.get("fetched") or 0) for leg in legs):
        return {}
    rates: dict[str, float | None] = {}
    start = 0
    for leg in legs:
        n = int(leg.get("fetched") or 0)
        rows = raw[start:start + n]
        start += n
        rates[leg.get("provider")] = (
            round(sum(1 for r in rows if not str((r or {}).get("abstract") or "").strip()) / n, 4) if n else None
        )
    return rates


def _completeness(leg: dict[str, Any]) -> str:
    if leg.get("status") == "failed":
        return "failed"
    if leg.get("status") == "stopped":
        return "stopped"
    if leg.get("cap_hit"):
        return "lower_bound"
    return "full"


DEDUP_TIERS = ("identifier", "exact_title", "fuzzy_title")


def _dedup_summary(ws: Path) -> dict[str, Any] | None:
    """Counts from ``literature/dedup/clusters.json`` (E4a), or ``None`` before any deduplication.

    ``tiers`` counts the records each tier removed (a member merged into a
    cluster), so the three add up to ``removed``.
    """
    from ...pipeline.deduplication import CLUSTERS_FILE

    data = _read_json(_lit(ws) / CLUSTERS_FILE)
    if not isinstance(data, dict) or not isinstance(data.get("clusters"), list):
        return None
    clusters = [c for c in data["clusters"] if isinstance(c, dict)]
    members = [m for c in clusters for m in (c.get("members") or []) if isinstance(m, dict)]
    tiers = dict.fromkeys(DEDUP_TIERS, 0)
    for member in members:
        if member.get("merged_by") in tiers:
            tiers[member["merged_by"]] += 1
    total, unique = len(members), len(clusters)
    return {
        "shape": "discovery.dedup-v1",
        "run": data.get("run"),
        "input_records": total,
        "unique_works": unique,
        "removed": total - unique,
        "removed_rate": round((total - unique) / total, 4) if total else 0.0,
        "tiers": tiers,
        "method": data.get("method"),
        "near_twins": None,  # E4b (M3e-neartwins)
    }


@router.get("/dedup")
def dedup_counts(request: Request) -> dict[str, Any]:
    summary = _dedup_summary(_ws(request))
    if summary is None:
        raise _http(Refused(404, refusals.DEDUP_NOT_RUN, "No deduplication has run in this workspace yet."))
    return summary


@router.get("/report")
def report(request: Request, run: str | None = None) -> dict[str, Any]:
    from scholar_search.search_report import render_methods_text

    from ...corpus_accept import staged_sources

    ws = _ws(request)
    try:
        proto = _protocol(ws)
        dirs = _run_dirs(ws)
        if run is None and not dirs:
            raise Refused(404, refusals.RUN_NOT_FOUND, "No search run yet in this workspace.")
        run_dir = _run_dir(ws, run) if run is not None else dirs[0]
    except Refused as exc:
        raise _http(exc) from exc
    manifest = _manifest(run_dir)
    legs = manifest["legs"]
    rates = _no_abstract_rates(run_dir, legs)
    identification = [{
        "database": leg.get("provider"), "kind": "search", "executed_query": leg.get("executed_query"),
        "reported_total": leg.get("reported_total"), "fetched": int(leg.get("fetched") or 0),
        "completeness": _completeness(leg), "no_abstract_rate": rates.get(leg.get("provider")),
        "cache": None, "error_code": leg.get("error_code"), "searched_at": leg.get("started_at"),
        "notes": list(leg.get("notes") or []),
    } for leg in legs]
    imports = [{
        "label": s.get("label"), "searched_on": s.get("searched_on"), "query": s.get("query"),
        # E3 (M3d-engine): the limits the researcher applied there and the lines the importer could not use.
        "limits": s.get("limits"), "records": s.get("records"), "rejected": list(s.get("rejected") or []),
    } for s in staged_sources(ws)]
    identification += [{
        "database": imp["label"], "kind": "import", "executed_query": imp["query"], "reported_total": None,
        "fetched": imp["records"], "completeness": "full", "no_abstract_rate": None, "cache": None,
        "error_code": None, "searched_at": imp["searched_on"], "notes": [],
    } for imp in imports]
    searched = {leg.get("provider") for leg in legs}
    not_searched = [
        {"database": name, "reason": "off by default" if name not in DEFAULT_PROVIDERS else "not selected in the protocol"}
        for name in KNOWN_PROVIDERS if name not in searched
    ]
    # deduped.json is the newest corpus run's; it describes this run only when this run is that one.
    newest_corpus = next((d for d in dirs if _published(_manifest(d))), None)
    deduped = _read_json(_lit(ws) / "deduped.json") if newest_corpus == run_dir else None
    fetched_total = sum(int(leg.get("fetched") or 0) for leg in legs)
    unique = len(deduped) if isinstance(deduped, list) else None
    summary = _dedup_summary(ws)
    dedup = {
        "removed": fetched_total - unique if unique is not None else None,
        # E4a (M3d-engine): only when clusters.json is this run's deduplication.
        "by_tier": summary["tiers"] if summary and summary["run"] == run_dir.name and deduped is not None else None,
        "near_twins": None,  # E4b (M3e-neartwins)
        "unique_works": unique,
    }
    try:
        from .screening_v1 import prisma_preview

        prisma = prisma_preview(request)
    except Exception:  # noqa: BLE001 - no prepared screening yet: the preview is absent, not an error
        prisma = None
    stored = _stored_methods(run_dir)
    if stored is not None:
        methods = {"text": stored["text"], "built_from": run_dir.name, "reviewed": stored["reviewed"],
                   "reviewed_at": stored["reviewed_at"]}
    else:
        methods = {
            "text": render_methods_text(
                legs, imports, dedup, query_text=manifest.get("query_text"),
                years=(manifest.get("year_min"), manifest.get("year_max")), cap_override=manifest.get("cap_override"),
            ),
            "built_from": run_dir.name, "reviewed": False, "reviewed_at": None,
        }
    earlier = None
    for other in dirs:
        if int(other.name[4:]) < int(run_dir.name[4:]):
            found = _stored_methods(other)
            if found and found["reviewed"]:
                earlier = {"run": other.name, "text": found["text"], "reviewed_at": found["reviewed_at"]}
                break
    methods["earlier_reviewed"] = earlier
    return {
        "shape": "discovery.report-v1",
        "run": run_dir.name,
        "status": manifest.get("status"),
        "cap_override": manifest.get("cap_override"),
        "identification": identification,
        "not_searched": not_searched,
        "imports": imports,
        "dedup": dedup,
        "outside_year_window": _outside_window(_verified(ws), proto.query),
        "prisma": prisma,
        "methods_text": methods,
        "runs": _runs_payload(request),
    }


class MethodsBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=20_000)
    # Required (review finding 2): a save that does not say it was reviewed is never recorded as a review.
    reviewed: bool
    run: str | None = None


@router.put("/report/methods")
def put_methods(body: MethodsBody, request: Request) -> dict[str, Any]:
    ws = _ws(request)
    try:
        dirs = _run_dirs(ws)
        if body.run is None and not dirs:
            raise Refused(404, refusals.RUN_NOT_FOUND, "No search run yet in this workspace.")
        run_dir = _run_dir(ws, body.run) if body.run is not None else dirs[0]
    except Refused as exc:
        raise _http(exc) from exc
    now = _now()
    text = body.text.strip()
    path = run_dir / "methods.md"
    path.write_text(
        f"---\nrun: {run_dir.name}\nreviewed: {'true' if body.reviewed else 'false'}\n"
        f"reviewed_at: {now if body.reviewed else ''}\n---\n\n{text}\n",
        encoding="utf-8",
    )
    append_event(
        ws, "METHODS_TEXT_REVIEWED",
        f"Methods text of {run_dir.name} saved ({'reviewed' if body.reviewed else 'draft'}, {len(text)} characters)",
        agent=AGENT, inputs=[str(run_dir / "legs.json")], outputs=[str(path)],
        parameters={"run": run_dir.name, "reviewed": body.reviewed, "method": "HUMAN"},
        metrics={"characters": len(text)},
    )
    return {"text": text, "built_from": run_dir.name, "reviewed": body.reviewed, "reviewed_at": now if body.reviewed else None}


@router.get("/handoff")
def handoff(request: Request) -> dict[str, Any]:
    from .screening_v1 import _corpus_view

    ws = _ws(request)
    try:
        proto = _protocol(ws)
    except Refused as exc:
        raise _http(exc) from exc
    rows = _verified(ws)
    mix: dict[str, int] = {}
    for row in rows:
        names = {str(s.get("provider")) for s in (row.get("sources") or []) if isinstance(s, dict) and s.get("provider")}
        if not names and row.get("provider") and row.get("provider") != "unknown":
            names = {str(row["provider"])}
        for name in names:
            mix[name] = mix.get(name, 0) + 1
    total = len(rows)
    with_abstract = sum(1 for row in rows if str(row.get("abstract") or "").strip())
    # verified.json belongs to the newest run published as the corpus; its
    # lower-bound warnings come from that run, not from a later failed one.
    corpus_run = next((d for d in _run_dirs(ws) if _published(_manifest(d))), None)
    legs = _manifest(corpus_run)["legs"] if corpus_run else []
    return {
        "shape": "discovery.handoff-v1",
        "corpus": _corpus_view(ws),
        "run": corpus_run.name if corpus_run else None,
        "provider_mix": [
            {"provider": name, "records": n, "share": round(n / total, 4) if total else 0.0}
            for name, n in sorted(mix.items(), key=lambda kv: (-kv[1], kv[0]))
        ],
        "abstracts": {
            "with_abstract": with_abstract, "title_only": total - with_abstract,
            "share_with_abstract": round(with_abstract / total, 4) if total else 0.0,
        },
        "outside_year_window": _outside_window(rows, proto.query),
        "near_twins_undecided": None,  # E4b (M3e-neartwins)
        "lower_bound_databases": sorted(str(leg.get("provider")) for leg in legs if leg.get("cap_hit")),
        "protocol_fingerprint": proto.fingerprint,
    }


# --------------------------------------------------------------------------- Layer J routes


class RunBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cap_override: int | None = None
    providers: list[str] | None = None
    note: str | None = Field(default=None, max_length=2_000)


def _refuse_busy(jobs: DiscoveryJobs, ws: Path) -> None:
    active = jobs.active(ws)
    if active is not None:
        raise Refused(409, refusals.DISCOVERY_JOB_ACTIVE, "A discovery job is already running for this workspace.",
                      details={"job": active.to_dict()})


def _no_indexing(_ws: Path):  # pragma: no cover - stages 5-9 need a collected screening, never reached here
    raise RuntimeError("indexing is not run from the console's discovery job")


def _run_error(results: dict[str, Any]) -> dict[str, Any]:
    stages = results.get("stages") or {}
    snapshot = stages.get("corpus_snapshot") or {}
    discovery = results.get("discovery") or {}
    if results.get("code"):
        code = results["code"]
        message = (stages.get("screening") or {}).get("reason") or code
    elif snapshot.get("status") == "REFUSED":
        code, message = snapshot.get("code") or refusals.DISCOVERY_FAILED, snapshot.get("reason") or ""
    elif discovery.get("status") == "FAILED":
        code, message = refusals.PROVIDERS_FAILED, discovery.get("reason") or "every database failed"
    else:
        reasons = [s.get("reason") for s in stages.values() if isinstance(s, dict) and s.get("reason")]
        code, message = refusals.DISCOVERY_FAILED, reasons[0] if reasons else "the run failed"
    return {"code": code, "message": message}


@router.post("/runs", status_code=202)
async def start_run(body: RunBody, request: Request) -> dict[str, Any]:
    from ...corpus_accept import _accepted_snapshot, staged_sources
    from ...pipeline.coordinator import run_pipeline

    ws, jobs = _ws(request), _jobs(request)
    try:
        proto = _protocol(ws)
        if body.cap_override is not None and not 1 <= body.cap_override <= ENGINE_CEILING:
            raise Refused(422, refusals.CAP_INVALID, f"A run cap must be 1 to {ENGINE_CEILING} records per database.")
        providers = _check_providers(body.providers)
        _require_mailto()
        _require_openalex_key(providers if providers is not None else proto.providers)
        if _accepted_snapshot(ws):
            raise Refused(409, refusals.CORPUS_ALREADY_ACCEPTED,
                          "The corpus snapshot is accepted; a frozen corpus is never searched again from the browser.")
        if staged_sources(ws):
            # The run would end at the snapshot with this refusal (M3a review
            # finding 2); say it before any request instead.
            raise Refused(409, refusals.STAGED_IMPORT_PENDING,
                          "Database exports are staged for import; accept or remove them before a search run.")
        _refuse_busy(jobs, ws)
    except Refused as exc:
        raise _http(exc) from exc

    async def work(job: DiscoveryJob):
        def on_stage(name: str, status: str, detail: Any) -> None:
            job.emit("stage", {"job_id": job.job_id, "stage": name, "status": status,
                               "detail": json.loads(json.dumps(detail, default=str))})

        results = await run_pipeline(
            workspace_dir=ws, max_search_results=body.cap_override, indexing_fn=_no_indexing,
            providers=providers, leg_callback=_leg_reporter(job), stage_callback=on_stage,
            should_stop=lambda: job.cancel_requested, notes=[body.note] if body.note else None,
            # M3d-engine: the hand-off screen's accept freezes the corpus (decision 2026-11-10).
            freeze_corpus=False,
        )
        result = json.loads(json.dumps({
            "run": (results.get("discovery") or {}).get("search_run") or None,
            "status": results.get("status"),
            "stages": results.get("stages"),
        }, default=str))
        if results.get("status") == "CANCELLED":
            return "cancelled", result, None
        if results.get("status") == "FAILED":
            return "failed", result, _run_error(results)
        return "succeeded", result, None

    return {"job": jobs.start(ws, "run", work).to_dict()}


class RecallBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seeds: list[dict[str, Any]]
    providers: list[str] | None = None


def _next_check(ws: Path) -> Path:
    root = _lit(ws) / "recall_checks"
    root.mkdir(parents=True, exist_ok=True)
    taken = [int(m.group(1)) for p in root.iterdir() if (m := CHECK_NAME.fullmatch(p.name))]
    return root / f"check_{max(taken, default=0) + 1:03d}.json"


@router.post("/recall", status_code=202)
async def start_recall(body: RecallBody, request: Request) -> dict[str, Any]:
    from scholar_search import recall as recall_mod

    ws, jobs = _ws(request), _jobs(request)
    try:
        proto = _protocol(ws)
        try:
            seeds = recall_mod.validate_seeds(body.seeds)
        except recall_mod.SeedsInvalid as exc:
            raise Refused(422, refusals.SEEDS_INVALID, str(exc)) from exc
        names = _check_providers(body.providers) or proto.providers
        _require_mailto()
        _refuse_busy(jobs, ws)
    except Refused as exc:
        raise _http(exc) from exc

    async def work(job: DiscoveryJob):
        providers = disc._resolve_providers(names) or []
        cap = proto.query.max_results if proto.query.max_results else None
        check = await recall_mod.check_seeds(
            proto.query, seeds, providers, cap, leg_callback=_leg_reporter(job),
            should_stop=lambda: job.cancel_requested,
        )
        if job.cancel_requested:
            return "cancelled", None, None
        record = {"shape": "discovery.recall-v1", "protocol_fingerprint": proto.fingerprint, **check}
        path = _next_check(ws)
        with open(path, "x", encoding="utf-8") as handle:  # never overwrite an earlier check
            handle.write(json.dumps(record, indent=2, ensure_ascii=False, default=str))
        append_event(
            ws, "DISCOVERY_RECALL_CHECK",
            f"Recall check {path.stem}: {check['found']} of {check['total']} seed(s) found by the protocol query",
            agent=AGENT, inputs=[str(proto.path)], outputs=[str(path)],
            parameters={k: check[k] for k in ("seeds", "found", "total", "missed_everywhere", "legs")},
            metrics={"found": check["found"], "total": check["total"]},
        )
        return "succeeded", {"check": path.stem, "found": check["found"], "total": check["total"]}, None

    return {"job": jobs.start(ws, "recall", work).to_dict()}


@router.get("/recall")
def last_recall(request: Request) -> dict[str, Any]:
    checks = _checks(_ws(request))
    if not checks:
        raise _http(Refused(404, refusals.RECALL_NOT_RUN, "No recall check has been run in this workspace."))
    return _read_json(checks[-1], {})


def _job(request: Request, job_id: str) -> DiscoveryJob:
    job = _jobs(request).jobs.get(job_id)
    if job is None or job.workspace != str(_ws(request)):
        raise _http(Refused(404, refusals.DISCOVERY_JOB_NOT_FOUND, f"No discovery job {job_id} in this workspace."))
    return job


@router.get("/jobs/{job_id}")
def read_job(job_id: str, request: Request) -> dict[str, Any]:
    return {"job": _job(request, job_id).to_dict()}


def _sse(event: dict[str, Any]) -> str:
    return f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"


@router.get("/jobs/{job_id}/events")
async def job_events(job_id: str, request: Request) -> StreamingResponse:
    job = _job(request, job_id)

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


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str, request: Request) -> dict[str, Any]:
    job = _job(request, job_id)
    if job.state not in TERMINAL:
        job.cancel_requested = True
        if job.task is not None:
            await asyncio.wait({job.task}, timeout=CANCEL_WAIT_SECONDS)
    return {"job": job.to_dict()}
