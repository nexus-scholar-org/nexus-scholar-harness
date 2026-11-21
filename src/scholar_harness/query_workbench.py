"""The query workbench's counts: the count log, the daily budget and the quota memory (M11a Part A).

Spec: `docs/roadmap/milestones/M11a-query-workbench.md` (a) and (b); decisions
2026-11-20 "M11a query workbench" items 4 to 7. The pure part (versions,
variants, gains, the word match) is ``scholar_search.workbench``; each count is
``scholar_search.estimate.count_one`` (one request, no record body).

* **The count log** (``counts.jsonl``) is append-only: one row per request sent,
  keyed by database and the exact string sent (with the years and the
  language). A counted row younger than :data:`CACHE_SECONDS` answers the same
  string without a request; a failed row is kept as a record and never
  answers. Before genesis it lives beside the draft record
  (``<root>/.drafts/<id>/query_development/``); after genesis under the
  workspace (``audit/query_development/``). It is not journaled.
* **The budget**: a daily number of workbench requests per database (UTC day),
  shared by every draft and workspace under the workspaces root, because a
  provider's quota belongs to the key. A Count that would pass it is refused
  before any request (``WORKBENCH_BUDGET_SPENT``).
* **The quota memory**: a database that answered ``QuotaExhaustedError`` is
  sent nothing more from the workbench until its ``resets_at``.

The shared state is ``<workspaces root>/.query_workbench/state.json``.
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scholar_search import estimate as est
from scholar_search import workbench as wb
from scholar_search.models import Query
from scholar_search.plan import DEFAULT_PROVIDERS, IGNORES_AND, translate_provider

#: Daily workbench requests per database (decision 2026-11-20, M11a item 4); a database not named gets the default.
BUDGETS: dict[str, int] = {"openalex": 200, "semanticscholar": 100, "arxiv": 100, "pubmed": 100, "crossref": 20}
DEFAULT_BUDGET = 20
#: The remaining budget is shown when this share or less is left.
LOW_SHARE = 0.25
#: A counted row answers the same string for this long (decision item 5).
CACHE_SECONDS = 24 * 3600
#: The longest a whole Count may take, under the browser proxy's 120 s.
DEADLINE_SECONDS = 100.0
STATE_DIRNAME = ".query_workbench"
STATE_FILE = "state.json"
DEVELOPMENT_DIR = "query_development"
COUNTS_FILE = "counts.jsonl"
LOG_SHAPE = "workbench.count-v1"
#: Row kinds a cached count may answer.
COUNT_KINDS = ("full", "drop", "synonym")
#: A failed count's row status, by its code (the harvest's codes, E5).
STATUS_BY_CODE = {
    "PROVIDER_RATE_LIMITED": "rate_limited",
    "PROVIDER_REFUSED": "refused",
    "PROVIDER_UNAVAILABLE": "unavailable",
    "PROVIDER_TIMEOUT": "timeout",
}
#: Statuses of a cell that holds a number.
NUMBERED = ("counted", "cached")

#: Reads of the shared state before it is refused as unreadable.
STATE_READ_TRIES = 5

WORKBENCH_BUDGET_SPENT = "WORKBENCH_BUDGET_SPENT"
WORKBENCH_VERSION_INVALID = "WORKBENCH_VERSION_INVALID"
WORKBENCH_STATE_UNREADABLE = "WORKBENCH_STATE_UNREADABLE"


class WorkbenchRefused(Exception):
    def __init__(self, status: int, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details


def utcnow() -> datetime:
    return datetime.now(UTC)


def _parse(value: Any) -> datetime | None:
    try:
        stamp = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=UTC)


def renews_at(now: datetime) -> str:
    """The next UTC midnight: when a day's budget renews."""
    return (now.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).isoformat()


def resets_in(until: str | None, now: datetime) -> dict[str, int] | None:
    """Hours and minutes from ``now`` to ``until`` (the screen prints them; it computes no difference)."""
    stamp = _parse(until)
    if stamp is None:
        return None
    minutes = max(0, int((stamp - now).total_seconds() // 60))
    return {"hours": minutes // 60, "minutes": minutes % 60}


def draft_log_path(drafts_dir: Path, session_id: str) -> Path:
    return Path(drafts_dir) / session_id / DEVELOPMENT_DIR / COUNTS_FILE


def workspace_log_path(workspace: Path) -> Path:
    return Path(workspace) / "audit" / DEVELOPMENT_DIR / COUNTS_FILE


_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


def _lock(path: Path) -> threading.Lock:
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(str(Path(path).resolve()), threading.Lock())


def version_key(version: wb.Version) -> str:
    """A short digest of one version (concepts, years, languages, query key), on every count log row (M11a Part B)."""
    import hashlib

    text = json.dumps(version.to_dict(), sort_keys=True, ensure_ascii=False)
    return "v_" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def version_counted(log: "CountLog", version: wb.Version) -> bool:
    """Whether a Count of this very version reached a database (any age): the check ``QUERY_NOT_COUNTED``."""
    key = version_key(version)
    return any(r.get("version_key") == key and r.get("kind") == "full" and r.get("status") == "counted" for r in log.rows())


def cache_key(name: str, executed: str, query: Query) -> str:
    """The log's key: the database, the exact string sent, the years and the language."""
    return json.dumps([name, executed, query.year_min, query.year_max, query.language], ensure_ascii=False)


class CountLog:
    """The append-only count log of one draft or one workspace."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def append(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        with _lock(self.path):
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    def rows(self) -> list[dict[str, Any]]:
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        out = []
        for line in lines:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                out.append(row)
        return out

    def _counted(self, key: str) -> list[dict[str, Any]]:
        return [r for r in self.rows() if r.get("key") == key and r.get("status") == "counted"
                and r.get("kind") in COUNT_KINDS and isinstance(r.get("total"), int)]

    def fresh(self, key: str, now: datetime) -> dict[str, Any] | None:
        """The newest counted row for ``key`` younger than :data:`CACHE_SECONDS`."""
        for row in reversed(self._counted(key)):
            stamp = _parse(row.get("counted_at"))
            if stamp is not None and 0 <= (now - stamp).total_seconds() < CACHE_SECONDS:
                return row
        return None

    def last(self, key: str) -> dict[str, Any] | None:
        """The newest counted row for ``key``, of any age."""
        rows = self._counted(key)
        return rows[-1] if rows else None


class SharedState:
    """The budget and the quota memory shared by every draft and workspace under one root."""

    def __init__(self, workspaces_root: Path):
        self.path = Path(workspaces_root) / STATE_DIRNAME / STATE_FILE

    def _read(self) -> dict[str, Any]:
        """The state; ``{}`` only when the file does not exist yet.

        A file that cannot be read (held by another program for a moment, or
        damaged) is tried again a few times and then refused
        (``WORKBENCH_STATE_UNREADABLE``): reading it as empty and writing that
        back would erase every database's pause and the day's spending (review P3).
        """
        for attempt in range(STATE_READ_TRIES):
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                return {}
            except (OSError, ValueError):
                if attempt + 1 < STATE_READ_TRIES:
                    time.sleep(0.05)
                    continue
                raise WorkbenchRefused(
                    503, WORKBENCH_STATE_UNREADABLE,
                    f"The workbench's budget file cannot be read ({self.path}); nothing was sent. Try again; "
                    "if it stays unreadable, move the file away and the budget starts again.",
                ) from None
            if isinstance(data, dict):
                return data
            raise WorkbenchRefused(503, WORKBENCH_STATE_UNREADABLE,
                                   f"The workbench's budget file is not a JSON object ({self.path}); nothing was sent.")
        return {}  # pragma: no cover - the loop returns or raises

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(f".{STATE_FILE}.{os.getpid()}.{threading.get_ident()}.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)

    @staticmethod
    def _day(now: datetime) -> str:
        return now.astimezone(UTC).date().isoformat()

    def spent(self, name: str, now: datetime) -> int:
        data = self._read()
        if data.get("day") != self._day(now):
            return 0
        return int((data.get("spent") or {}).get(name, 0))

    def spend(self, name: str, requests: int, now: datetime) -> None:
        """Add ``requests`` (negative: give back a reservation not used) to today's spending."""
        with _lock(self.path):
            data = self._read()
            if data.get("day") != self._day(now):
                data["day"], data["spent"] = self._day(now), {}
            spent = data.setdefault("spent", {})
            spent[name] = max(0, int(spent.get(name, 0)) + requests)
            self._write(data)

    def reserve(self, costs: dict[str, int], now: datetime) -> list[str]:
        """Take ``costs`` from today's budgets in one step, or nothing: the databases that would pass it.

        Checking and spending under one lock means two Counts sent at once
        (two tabs, Inception and Plan) cannot both pass the check (review P3).
        """
        with _lock(self.path):
            data = self._read()
            if data.get("day") != self._day(now):
                data["day"], data["spent"] = self._day(now), {}
            spent = data.setdefault("spent", {})
            over = [n for n, c in costs.items() if c and int(spent.get(n, 0)) + c > BUDGETS.get(n, DEFAULT_BUDGET)]
            if over:
                return over
            for name, cost in costs.items():
                if cost:
                    spent[name] = int(spent.get(name, 0)) + cost
            self._write(data)
            return []

    def budget(self, name: str, now: datetime) -> dict[str, Any]:
        limit = BUDGETS.get(name, DEFAULT_BUDGET)
        spent = self.spent(name, now)
        left = max(0, limit - spent)
        return {"limit": limit, "spent": spent, "left": left, "renews_at": renews_at(now),
                "low": left <= limit * LOW_SHARE}

    def pause(self, name: str, until: str, now: datetime) -> None:
        with _lock(self.path):
            data = self._read()
            data.setdefault("paused", {})[name] = {"until": until, "since": now.isoformat()}
            self._write(data)

    def paused_until(self, name: str, now: datetime) -> str | None:
        entry = (self._read().get("paused") or {}).get(name) or {}
        until = _parse(entry.get("until"))
        return entry["until"] if until is not None and until > now else None


def _quietly(fn: Any, *args: Any) -> Any:
    """A shared-state call made after requests were sent: its failure must not lose the answer (review round 2).

    The answer then carries ``None`` where the call's value would be (the budget
    line is left out); a refund or a pause not stored is the cost of an
    unreadable file, which the next Count refuses before sending anything.
    """
    try:
        return fn(*args)
    except (WorkbenchRefused, OSError):
        return None


# --------------------------------------------------------------------------- one Count


@dataclass
class Cell:
    """One request of a Count: a variant of the version for one database."""

    variant: wb.Variant
    query: Query
    string: str | None
    key: str | None
    status: str = "to_count"
    total: int | None = None
    counted_at: str | None = None
    from_cache: bool = False
    error: str | None = None
    error_code: str | None = None
    http_status: int | None = None
    resets_at: str | None = None
    sent: bool = False

    def public(self) -> dict[str, Any]:
        v = self.variant
        return {
            "kind": v.kind, "concept_index": v.concept_index, "concept": v.concept, "term": v.term,
            "status": self.status, "total": self.total, "string": self.string, "counted_at": self.counted_at,
            "from_cache": self.from_cache, "error": self.error, "error_code": self.error_code,
            "http_status": self.http_status, "resets_at": self.resets_at,
        }


@dataclass
class Row:
    name: str
    status: str | None = None
    cells: list[Cell] = field(default_factory=list)
    any_words: bool = False
    last: dict[str, Any] | None = None
    resets_at: str | None = None
    #: The requests this database needs, fixed when the Count is planned (review P2: never recomputed after sending).
    planned: int = 0

    @property
    def cost(self) -> int:
        return sum(1 for c in self.cells if c.status == "to_count") if self.status is None else 0


def _translate(name: str, cells: list[tuple[wb.Variant, Query]]) -> tuple[bool, list[str | None]]:
    """``(countable, strings)`` from the database's own translation (E1); nothing is sent."""
    from scholar_search.plan import _provider as make
    from scholar_search.plan import _close_quietly
    from scholar_search.providers.base import BaseAPIProvider

    provider = make(name)
    try:
        countable = getattr(type(provider), "count", None) is not BaseAPIProvider.count
        strings: list[str | None] = []
        for _variant, query in cells:
            try:
                strings.append(str(translate_provider(provider, query)["executed_query"]))
            except NotImplementedError:
                strings.append(None)
        return countable, strings
    finally:
        close = getattr(getattr(provider, "client", None), "close", None)
        if close is not None:
            _close_quietly(close)


def _plan_rows(
    version: wb.Version, names: list[str], variants_for: Any, *, log: CountLog, state: SharedState,
    now: datetime, cap: int | None, crossref_anyway: bool, openalex_key: bool,
) -> list[Row]:
    joined = len(version.concepts) >= 2
    rows: list[Row] = []
    for name in names:
        row = Row(name)
        rows.append(row)
        variants: list[wb.Variant] = variants_for(name)
        if joined and name in IGNORES_AND:
            if not crossref_anyway:
                row.status = "not_comparable"
                continue
            row.any_words = True
            variants = [v for v in variants if v.kind == "full"]
        pairs = [(v, wb.compile_version(v.version, cap=cap)) for v in variants]
        countable, strings = _translate(name, pairs)
        for (variant, query), string in zip(pairs, strings):
            key = cache_key(name, string, query) if string is not None else None
            cell = Cell(variant, query, string, key)
            cached = log.fresh(key, now) if key is not None else None
            if cached is not None:
                cell.status, cell.total, cell.counted_at, cell.from_cache = "cached", cached["total"], cached["counted_at"], True
            row.cells.append(cell)
        full_key = row.cells[0].key if row.cells else None
        if not countable or (row.cells and row.cells[0].string is None):
            row.status = "not_countable"
        elif name == "openalex" and not openalex_key:
            row.status = "key_missing"
        elif (until := state.paused_until(name, now)) is not None:
            row.status, row.resets_at = "quota_used_up", until
        elif row.cost > state.budget(name, now)["left"]:
            row.status = "budget_spent"
        if row.status is not None:
            for cell in row.cells:
                if cell.status == "to_count":
                    cell.status = row.status
            row.last = log.last(full_key) if full_key else None
        row.planned = row.cost
    return rows


async def _send(row: Row, *, log: CountLog, state: SharedState, deadline: float, scope: dict[str, Any],
                query_key: str, counted_version: str | None = None) -> None:
    """Ask one database its cells in order; stop at its first failure (the rest are not sent).

    What was sent is logged even when something fails half-way (review P3).
    """
    logged: list[dict[str, Any]] = []
    try:
        await _send_cells(row, logged, state=state, deadline=deadline, scope=scope, query_key=query_key,
                          counted_version=counted_version)
    except Exception as exc:  # noqa: BLE001 - one database's error is its row, never the Count's
        for cell in row.cells:
            if cell.status == "to_count":
                cell.status, cell.error = "failed", f"{type(exc).__name__}: {str(exc)[:200]}"
    finally:
        log.append(logged)


async def _send_cells(row: Row, logged: list[dict[str, Any]], *, state: SharedState, deadline: float,
                      scope: dict[str, Any], query_key: str, counted_version: str | None = None) -> None:
    stop: Cell | None = None
    for cell in row.cells:
        if cell.status != "to_count":
            continue
        if stop is not None:
            cell.status, cell.error_code, cell.resets_at = stop.status, stop.error_code, stop.resets_at
            continue
        left = deadline - time.monotonic()
        if left <= 1:
            cell.status, cell.error_code = "timeout", "PROVIDER_TIMEOUT"
            cell.error = "the Count ran out of time before this request was sent"
            stop = cell
            continue
        answer = await est.count_one(row.name, cell.query, timeout=min(est.COUNT_TIMEOUT, left))
        now = utcnow()
        cell.sent, cell.counted_at = True, now.isoformat()
        status = answer["status"]
        if status == "counted":
            cell.status, cell.total = "counted", int(answer["reported_total"])
        elif status == "not_countable":
            cell.status = "not_countable"
        else:
            code = answer.get("error_code")
            cell.error, cell.error_code, cell.http_status = answer.get("error"), code, answer.get("http_status")
            if answer.get("quota_exhausted"):
                cell.status, cell.resets_at = "quota_used_up", answer.get("resets_at")
            else:
                cell.status = STATUS_BY_CODE.get(code or "", "failed")
            stop = cell
        logged.append({
            "shape": LOG_SHAPE, "query_key": query_key, "provider": row.name, "kind": cell.variant.kind,
            "concept": cell.variant.concept, "term": cell.variant.term, "string": cell.string,
            "year_min": cell.query.year_min, "year_max": cell.query.year_max, "language": cell.query.language,
            "status": "counted" if cell.status == "counted" else ("not_countable" if cell.status == "not_countable" else "failed"),
            "total": cell.total, "error_code": cell.error_code, "http_status": cell.http_status,
            "resets_at": cell.resets_at, "counted_at": cell.counted_at, "requests": 1, "key": cell.key,
            "version_key": counted_version, **scope,
        })
        if cell.status == "quota_used_up" and cell.resets_at:
            _quietly(state.pause, row.name, cell.resets_at, now)


def _row_public(row: Row, now: datetime, mode: str, year_window: bool) -> dict[str, Any]:
    full = row.cells[0] if row.cells else None
    status = row.status or (full.status if full else "not_countable")
    out: dict[str, Any] = {
        "name": row.name, "status": status, "any_words": row.any_words,
        "upper_bound": bool(year_window) and row.name in est.UPPER_BOUND_WITH_YEARS,
        "string": full.string if full else None, "total": full.total if full and full.status in NUMBERED else None,
        "counted_at": full.counted_at if full and full.status in NUMBERED else None,
        "from_cache": bool(full and full.from_cache), "error": full.error if full else None,
        "error_code": full.error_code if full else None, "http_status": full.http_status if full else None,
        "resets_at": row.resets_at or (full.resets_at if full else None), "cost": row.planned,
        "requests": sum(c.sent for c in row.cells),
        "last": {"total": row.last["total"], "counted_at": row.last["counted_at"]} if row.last else None,
        "stopped": None,
    }
    # Review P3: a database that answered the full query and then failed is stopped; the row says so.
    if row.status is None and full is not None and full.status in NUMBERED:
        failed = next((c for c in row.cells[1:] if c.status not in NUMBERED and c.status != "to_count"), None)
        if failed is not None:
            out["stopped"] = {"status": failed.status, "error_code": failed.error_code,
                              "http_status": failed.http_status, "resets_at": failed.resets_at,
                              "resets_in": resets_in(failed.resets_at, now) if failed.status == "quota_used_up" else None}
    out["resets_in"] = resets_in(out["resets_at"], now) if status == "quota_used_up" else None
    full_total = out["total"]
    others = [c for c in row.cells[1:]]
    cells = []
    for cell in others:
        item = cell.public()
        if mode == "synonyms":
            # Gain of a term: the records reached only through it (full minus without it).
            known = isinstance(full_total, int) and cell.status in NUMBERED and isinstance(cell.total, int)
            item["gain"] = full_total - cell.total if known else None
            item["adds_nothing"] = item["gain"] == 0
        else:
            item.update(wb.gain(full_total, cell.total if cell.status in NUMBERED else None))
            item["note"] = row.name not in IGNORES_AND and wb.doubles(full_total, cell.total if cell.status in NUMBERED else None)
        cells.append(item)
    if mode == "counts":
        best = wb.largest(cells)
        for i, item in enumerate(cells):
            item["largest"] = i == best
        out["drops"] = cells
    else:
        out["synonyms"] = cells
    return out


def _size(rows: list[dict[str, Any]], size: dict[str, Any], year_window: bool) -> dict[str, Any]:
    """The size line (M10b Part D's ``estimate.summarize``) for the full query's rows."""
    est_rows = []
    for row in rows:
        if row["status"] in ("not_comparable", "not_asked") or row["any_words"]:
            est_rows.append({"name": row["name"], "status": "not_selected", "reported_total": None})
        elif isinstance(row["total"], int):  # the full query's number, current or cached (review P2)
            est_rows.append({"name": row["name"], "status": "counted", "reported_total": row["total"]})
        else:
            est_rows.append({"name": row["name"], "status": "failed", "reported_total": None})
    summary = est.summarize(est_rows, cap=size["cap"], limit=size["limit"]["value"],
                            pace_seconds=size.get("pace_seconds", est.DEFAULT_PACE_SECONDS), year_window=year_window)
    summary["warn"]["limit"] = size["limit"]
    return {k: summary[k] for k in ("estimate", "effort", "warn", "recommendation")} | {"cap": size["cap"]}


async def run(
    version: wb.Version,
    names: list[str],
    *,
    log: CountLog,
    state: SharedState,
    dry_run: bool,
    size: dict[str, Any],
    mode: str = "counts",
    concept_index: int | None = None,
    crossref_anyway: bool = False,
    openalex_key: bool = True,
    scope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """One Count (``mode="counts"``) or "what each synonym adds" (``mode="synonyms"``).

    The dry run sends nothing and states the cost per database. A real run is
    refused before any request when a database's budget would be passed
    (``WORKBENCH_BUDGET_SPENT``); else each database is asked in parallel, its
    own requests one after another, and a database's failure is its row.
    """
    now = utcnow()
    if mode == "synonyms":
        variants = wb.synonym_variants(version, int(concept_index if concept_index is not None else -1))

        def variants_for(_name: str) -> list[wb.Variant]:
            return variants
    else:
        variants = wb.count_variants(version)

        def variants_for(_name: str) -> list[wb.Variant]:
            return variants
    cap = size.get("query_cap")
    rows = _plan_rows(version, names, variants_for, log=log, state=state, now=now, cap=cap,
                      crossref_anyway=crossref_anyway, openalex_key=openalex_key)
    spent = [r.name for r in rows if r.status == "budget_spent"]
    if not dry_run and not spent:
        # Checked and taken in one step, so two Counts at once cannot both pass (review P3).
        spent = state.reserve({r.name: r.planned for r in rows if r.status is None}, now)
    if spent and not dry_run:
        raise WorkbenchRefused(409, WORKBENCH_BUDGET_SPENT,
                               "Today's counting budget would be passed for " + ", ".join(spent) + "; nothing was sent.",
                               details={"databases": [{"name": n, **state.budget(n, now)} for n in spent]})
    if not dry_run:
        deadline = time.monotonic() + DEADLINE_SECONDS
        sending = [r for r in rows if r.status is None and r.planned]
        try:
            await asyncio.gather(*(_send(r, log=log, state=state, deadline=deadline, scope=scope or {},
                                         query_key=version.query_key, counted_version=version_key(version))
                                   for r in sending))
        finally:
            # A reserved request that was not sent (a stopped database) is given back.
            back = utcnow()
            for r in sending:
                unused = r.planned - sum(c.sent for c in r.cells)
                if unused:
                    _quietly(state.spend, r.name, -unused, back)
    later = utcnow()
    year_window = bool(version.start_year or version.end_year)
    public = [_row_public(r, later, mode, year_window) for r in rows]
    if mode == "counts":
        for name in DEFAULT_PROVIDERS:
            if name not in names:
                public.append({"name": name, "status": "not_asked", "any_words": False, "upper_bound": False,
                               "string": None, "total": None, "counted_at": None, "from_cache": False,
                               "error": None, "error_code": None, "http_status": None, "resets_at": None,
                               "resets_in": None, "cost": 0, "requests": 0, "last": None, "drops": []})
    cost = {r.name: r.planned for r in rows if r.status is None}
    answer: dict[str, Any] = {
        "shape": f"workbench.{mode}-v1",
        "query_key": version.query_key,
        "dry_run": dry_run,
        "version": version.to_dict(),
        "concepts": len(version.concepts),
        "terms": version.term_count,
        "cost": {"total": sum(cost.values()), "by_database": cost,
                 "cached": sum(cost.values()) == 0 and any(r.status is None for r in rows)},
        "requests": sum(p["requests"] for p in public),
        "databases": public,
        "budget": {r.name: _quietly(state.budget, r.name, later) for r in rows},
    }
    if mode == "counts":
        answer["notes"] = [
            {"concept_index": d["concept_index"], "concept": d["concept"], "database": p["name"],
             "total": p["total"], "without": d["total"]}
            for p in public for d in p.get("drops", []) if d.get("note")
        ]
        answer["size"] = _size(public, size, year_window)
        # Decision 2026-11-20, M11a item 10: the version written for Scopus and Web of Science, to copy.
        answer["external"] = wb.external_strings(version)
    else:
        answer["concept_index"] = concept_index
    return answer


# --------------------------------------------------------------------------- read what a concept removes


async def read_removed(
    version: wb.Version, index: int, *, log: CountLog, state: SharedState, dry_run: bool,
    openalex_key: bool, scope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The first records of the query without one concept, minus those the full query's words match (OpenAlex)."""
    name = "openalex"
    now = utcnow()
    smaller = wb.without_concept(version, index)
    if len(version.concepts) < 2:
        raise wb.VersionInvalid("one concept: there is no concept to leave out")
    query = wb.compile_version(smaller, cap=wb.REMOVED_SAMPLE)
    _countable, (string,) = _translate(name, [(wb.Variant("drop", smaller, index), query)])
    status: str | None = None
    resets_at = state.paused_until(name, now)
    if not openalex_key:
        status = "key_missing"
    elif resets_at is not None:
        status = "quota_used_up"
    elif state.budget(name, now)["left"] < 1:
        status = "budget_spent"
    answer: dict[str, Any] = {
        "shape": "workbench.removed-v1", "query_key": version.query_key, "dry_run": dry_run,
        "database": name, "concept_index": index, "concept": version.concepts[index].name, "string": string,
        "cost": 0 if status else 1, "requests": 0, "status": status or ("to_read" if dry_run else "read"),
        "resets_at": resets_at, "resets_in": resets_in(resets_at, now) if resets_at else None,
        "read": 0, "records": [], "error": None, "error_code": None, "http_status": None,
        "budget": {name: state.budget(name, now)},
    }
    if status == "budget_spent" and not dry_run:
        raise WorkbenchRefused(409, WORKBENCH_BUDGET_SPENT, f"Today's counting budget for {name} is used; nothing was sent.",
                               details={"databases": [{"name": name, **state.budget(name, now)}]})
    if dry_run or status:
        return answer
    if state.reserve({name: 1}, now):
        raise WorkbenchRefused(409, WORKBENCH_BUDGET_SPENT, f"Today's counting budget for {name} is used; nothing was sent.",
                               details={"databases": [{"name": name, **state.budget(name, now)}]})
    from scholar_search.engine import provider_error_code
    from scholar_search.exceptions import ProviderError, QuotaExhaustedError

    try:
        provider = est._provider(name)
    except BaseException:
        _quietly(state.spend, name, -1, utcnow())  # nothing was sent: the reservation is given back
        raise
    docs: list[Any] = []
    try:
        async def collect() -> None:
            async for doc in provider.search(query):
                docs.append(doc)
                if len(docs) >= wb.REMOVED_SAMPLE:
                    break
        await asyncio.wait_for(collect(), timeout=est.COUNT_TIMEOUT)
    except (TimeoutError, asyncio.TimeoutError):
        answer.update(status="timeout", error_code="PROVIDER_TIMEOUT", error=f"{name} did not answer within {est.COUNT_TIMEOUT:g} s")
    except Exception as exc:  # noqa: BLE001 - the database's failure is the answer's status
        code = provider_error_code(exc)
        answer.update(error=str(exc)[:300], error_code=code, status=STATUS_BY_CODE.get(code or "", "failed"))
        if isinstance(exc, ProviderError) and exc.status_code is not None:
            answer["http_status"] = exc.status_code
        if isinstance(exc, QuotaExhaustedError):
            answer.update(status="quota_used_up", resets_at=exc.resets_at, resets_in=resets_in(exc.resets_at, utcnow()))
    finally:
        await est._close(provider)
    later = utcnow()
    answer["requests"] = 1
    records = []
    for doc in docs:
        text = " ".join(str(x) for x in (doc.title, doc.abstract or "", " ".join(getattr(doc, "mesh_terms", None) or [])))
        if wb.matches(version, text):
            continue
        records.append({"title": doc.title, "doi": getattr(doc.external_ids, "doi", None), "year": doc.year,
                        "lacks": wb.lacking(version, text)})
    answer.update(read=len(docs), records=records, budget={name: _quietly(state.budget, name, later)})
    log.append([{
        "shape": LOG_SHAPE, "query_key": version.query_key, "provider": name, "kind": "removed",
        "concept": version.concepts[index].name, "term": None, "string": string, "year_min": query.year_min,
        "year_max": query.year_max, "language": query.language,
        "status": "read" if answer["status"] == "read" else "failed", "total": len(docs),
        "error_code": answer["error_code"], "http_status": answer["http_status"], "resets_at": answer["resets_at"],
        "counted_at": later.isoformat(), "requests": 1, "key": None, **(scope or {}),
    }])
    if answer["status"] == "quota_used_up" and answer["resets_at"]:
        _quietly(state.pause, name, answer["resets_at"], later)
    return answer


# --------------------------------------------------------------------------- the estimate reads the log


def logged_rows(log_path: Path, query: Query, names: list[str]) -> dict[str, dict[str, Any]]:
    """Counts of ``query`` the workbench logged in the last 24 hours, as the estimate's rows (decision item 5)."""
    log = CountLog(log_path)
    if not log.path.is_file():
        return {}
    now = utcnow()
    out: dict[str, dict[str, Any]] = {}
    for name in names:
        variant = wb.Variant("full", wb.Version((wb.Concept("x", ("x",)),)))
        _countable, (string,) = _translate(name, [(variant, query)])
        if string is None:
            continue
        row = log.fresh(cache_key(name, string, query), now)
        if row is not None:
            out[name] = {"name": name, "status": "counted", "reported_total": row["total"], "error": None,
                         "error_code": None, "from_count_log": row["counted_at"]}
    return out
