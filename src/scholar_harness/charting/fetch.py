"""Fetching open-access copies into the charting table (M12a Part F, record (d2)).

The researcher starts a run for a set of kept records; the app asks the PDF
kit's downloader, as a library (Part K), for each one in turn:

- a record with a DOI: Unpaywall (with ``SCHOLAR_MAILTO``) and OpenAlex (only
  with ``SCHOLAR_OPENALEX_KEY``), then the listed open copies, best version first;
- a record with no DOI and an arXiv id: arXiv's own API (``id_list``, several
  ids per request, one request every three seconds), then the ``pdf`` link
  arXiv gives; when arXiv's answer carries a journal DOI, that DOI goes to the
  services too and the best open copy wins (answer F3);
- a record with neither: skipped and counted, with its manifest row.

Every record a run reaches has a row in ``charting/fetch_manifest.jsonl``
(the kit writes it, with this run's id and the row's id); files are stored by
content under ``pdfs/fetched/`` (the kit's ``DOC-<sha256[:32]>.pdf`` names).
No file is stored without its row. Each body stops at 100 MB, at most five
redirects are followed, each recorded; no proxy is used and no address is
built (the kit's rules, K0 and Part K).

A stored file is **Fetched, to confirm** on its row: not Retrieved, counted
apart. The researcher confirms it (``fetched_confirm``: Part A's attachment
event with ``origin: fetched``, the file copied to ``pdfs/<study_id>.pdf``,
the row Retrieved) or discards it (``fetched_discard``, one reason); both
are events in Part A's events file, undoable. Nothing is deleted.

One run per workspace (``FETCH_ALREADY_ACTIVE``), held by a lock file that
names its engine, as the agent runs do; a cancel stops between records. The
run is started only by the researcher; nothing here runs in the background
on its own or on a schedule.
"""

from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import os
import shutil
import threading
import time
import uuid
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from scholar_harness.workspace.audit import append_event

from . import CHARTING_DIR, ChartingRefused
from . import attachments as att
from . import events as ev

MANIFEST = CHARTING_DIR / "fetch_manifest.jsonl"
RUNS_DIR = CHARTING_DIR / "fetch_runs"
LOCK_FILE = RUNS_DIR / "active.lock"
FETCHED_DIR = att.PDFS_DIR / "fetched"

#: Part A's limit on a PDF in the workspace (record (d2), check 3).
MAX_BYTES = att.MAX_BYTES
#: At most five redirects, each recorded (check 2).
MAX_REDIRECTS = 5
#: The pause between two requests to the same PDF host (arXiv's hosts: its own three seconds).
SAME_HOST_PAUSE = 1.0
#: The lookup client's pace for Unpaywall and OpenAlex (one request at a time in any case).
LOOKUP_RATE = 5.0
#: How many of the last PDF requests the run's state keeps, for the progress line.
RECENT_REQUESTS = 8

STARTED = "CHARTING_FETCH_STARTED"
FINISHED = "CHARTING_FETCH_FINISHED"
CONFIRMED_WORDS = "Confirmed the fetched PDF"
DISCARDED_WORDS = "Discarded the fetched PDF"

# Refusal codes (console refusal set, screening-api-contract.md §7).
MAILTO_NOT_SET = "MAILTO_NOT_SET"
FETCH_ALREADY_ACTIVE = "FETCH_ALREADY_ACTIVE"
FETCH_NOT_PENDING = "FETCH_NOT_PENDING"
DISCARD_REASON_REQUIRED = "DISCARD_REASON_REQUIRED"
FETCH_FILE_WAITING = "FETCH_FILE_WAITING"

KINDS = ("fetched_confirm", "fetched_discard")
#: The licence words of an arXiv copy whose answer names none (record (d2)).
ARXIV_NO_LICENCE = "arXiv; licence not given"
DISCARD_REASONS = ("wrong_paper", "not_full_text", "unreadable", "other")
#: The kit's outcome for a record with neither a DOI nor an arXiv id.
SKIPPED_NO_ID = "SKIPPED_NO_ID"
#: The statuses a selected record may have to be looked up (spec 03, question 5).
LOOKUP_STATUSES = ("to_get", "requested", "not_retrieved")

_ARXIV_HOSTS = ("arxiv.org", "export.arxiv.org", "www.arxiv.org")
_ARXIV_API = "https://export.arxiv.org/api/query"


def now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _refuse(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


# --------------------------------------------------------------------------- the manifest


def read_manifest(ws: Path | str) -> list[dict[str, Any]]:
    """Every row of ``charting/fetch_manifest.jsonl``, in order; a line still being written is skipped."""
    path = Path(ws) / MANIFEST
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out


def rows_for(ws: Path | str, study_id: str) -> list[dict[str, Any]]:
    """What was tried for one record: its manifest rows, oldest first (``GET …/fetch``)."""
    return [row for row in read_manifest(ws) if row.get("study_id") == study_id]


def stored_file(ws: Path, row: dict[str, Any]) -> Path | None:
    """The file a manifest row names, when it is inside ``pdfs/fetched/``; else ``None``."""
    entry = row.get("file")
    if not isinstance(entry, str) or not entry:
        return None
    base = (Path(ws) / MANIFEST).parent
    path = (base / entry).resolve() if not Path(entry).is_absolute() else Path(entry).resolve()
    folder = (Path(ws) / FETCHED_DIR).resolve()
    try:
        path.relative_to(folder)
    except ValueError:
        return None
    return path


# --------------------------------------------------------------------------- what waits on each row


def _slot_events(events: list[dict[str, Any]], study_id: str, who: str, kind: str) -> list[dict[str, Any]]:
    return [e for e in events if e.get("study_id") == study_id and e.get("screener_id") == who and e.get("kind") == kind]


def effective_discards(events: list[dict[str, Any]], study_id: str, who: str) -> list[dict[str, Any]]:
    """Discards that stand: a ``fetched_discard`` with a value that no undo (a null value) superseded."""
    mine = _slot_events(events, study_id, who, "fetched_discard")
    undone = {str(e.get("supersedes")) for e in mine if e.get("value") is None and e.get("supersedes")}
    return [e for e in mine if isinstance(e.get("value"), dict) and e["event_id"] not in undone]


def _named(head: dict[str, Any] | None) -> str | None:
    value = (head or {}).get("value")
    return str(value.get("manifest_row")) if isinstance(value, dict) and value.get("manifest_row") else None


def pending_row(
    manifest: list[dict[str, Any]], events: list[dict[str, Any]], study_id: str, who: str
) -> dict[str, Any] | None:
    """The manifest row whose file waits on this record, or ``None``.

    The newest row of the record with a stored file waits unless the current
    confirm or discard names it, or a discard that stands named the same
    bytes (spec 03, question 4: the same file is never offered again).
    """
    newest = None
    for row in manifest:
        if row.get("study_id") == study_id and row.get("row_id") and row.get("file") and row.get("sha256"):
            newest = row
    if newest is None:
        return None
    row_id = str(newest["row_id"])
    if row_id in (_named(ev.current(events, study_id, who, "fetched_confirm")),
                  _named(ev.current(events, study_id, who, "fetched_discard"))):
        return None
    discarded = {(e.get("fetched") or {}).get("sha256") for e in effective_discards(events, study_id, who)}
    if newest.get("sha256") in discarded:
        return None
    return newest


def _identity_words(row: dict[str, Any]) -> str | None:
    return (row.get("checks") or {}).get("identity")


def pending_view(row: dict[str, Any]) -> dict[str, Any]:
    """``fulltext.pending_fetch`` on a table row (spec 03 "Data in")."""
    address = row.get("address") or ""
    provider = row.get("provider")
    names = {"openalex": "OpenAlex", "unpaywall": "Unpaywall", "arxiv": "arXiv"}
    licence = row.get("license")
    if licence is None and provider == "arxiv":
        licence = ARXIV_NO_LICENCE
    return {
        "manifest_row": row.get("row_id"),
        "run_id": row.get("run_id"),
        "source": names.get(str(provider), provider),
        "source_name": row.get("source_name"),
        "host": urlsplit(address).hostname if address else None,
        "host_type": row.get("host_type"),
        "address": address or None,
        "version": row.get("version"),
        "version_label": row.get("version_label") or row.get("version"),
        "licence": licence,
        "size": row.get("size"),
        "sha256": row.get("sha256"),
        "identity": _identity_words(row),
        "at": row.get("time"),
        "duplicate_of": [],
    }


def _try_later(row: dict[str, Any]) -> bool:
    if any(str(r.get("error") or "").startswith("HTTP 429") for r in row.get("requests") or []):
        return True
    return any(
        lookup.get("state") == "FAILED" and lookup.get("http_status") in (409, 429, 503)
        for lookup in row.get("lookups") or []
    )


def last_lookup_view(row: dict[str, Any]) -> dict[str, Any]:
    """``fulltext.last_lookup`` on a table row: the newest manifest row of the record."""
    return {
        "run_id": row.get("run_id"),
        "manifest_row": row.get("row_id"),
        "at": row.get("time"),
        "outcome": row.get("outcome"),
        "message": row.get("message"),
        "try_later": _try_later(row),
    }


@dataclass
class TableState:
    """What the table shows of the fetch, per study."""

    pending: dict[str, dict[str, Any]] = field(default_factory=dict)
    last: dict[str, dict[str, Any]] = field(default_factory=dict)
    discarded: dict[str, dict[str, Any]] = field(default_factory=dict)


def table_state(ws: Path, events: list[dict[str, Any]], who: str, study_ids: list[str]) -> TableState:
    manifest = read_manifest(ws)
    state = TableState()
    newest: dict[str, dict[str, Any]] = {}
    for row in manifest:
        if row.get("study_id"):
            newest[str(row["study_id"])] = row
    for sid in study_ids:
        row = pending_row(manifest, events, sid, who)
        if row is not None:
            state.pending[sid] = pending_view(row)
        standing = effective_discards(events, sid, who)
        if sid in newest:
            state.last[sid] = last_lookup_view(newest[sid])
            # Spec 03, question 4: the same bytes as a discarded file are never offered again; say so.
            shas = {(e.get("fetched") or {}).get("sha256") for e in standing}
            state.last[sid]["same_as_discarded"] = bool(newest[sid].get("sha256") and newest[sid]["sha256"] in shas)
        if standing:
            value = standing[-1].get("value") or {}
            state.discarded[sid] = {"reason": value.get("reason"), "reason_text": value.get("reason_text"),
                                    "at": standing[-1].get("at"), "manifest_row": value.get("manifest_row")}
    return state


# --------------------------------------------------------------------------- confirm, discard, undo (Part A's events)


class Hooks:
    """What the charting intake asks of Part F: which row has a file waiting, and what a confirm writes.

    Read under the events lock (the intake holds it); the manifest is read once per request.
    """

    def __init__(self, ws: Path, who: str) -> None:
        self.ws, self.who = Path(ws), who
        self._manifest: list[dict[str, Any]] | None = None

    def manifest(self) -> list[dict[str, Any]]:
        if self._manifest is None:
            self._manifest = read_manifest(self.ws)
        return self._manifest

    def waiting(self, study_id: str, events: list[dict[str, Any]]) -> dict[str, Any] | None:
        return pending_row(self.manifest(), events, study_id, self.who)

    # -- refusals ------------------------------------------------------------

    def refusal(self, raw: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, str] | None:
        """The refusal of a status, decision or fetched event on a row with (or without) a file waiting."""
        kind, value, study_id = raw.get("kind"), raw.get("value"), str(raw.get("study_id"))
        guarded = kind == "fulltext_status" or (kind in ("fulltext_decision", "attachment") and value is not None)
        if guarded:
            if self.waiting(study_id, events) is not None:
                return _refuse(FETCH_FILE_WAITING,
                               "A fetched file is waiting on this row. Confirm it or discard it first.")
            return None
        if kind not in KINDS:
            return None
        if value is None:
            if not raw.get("supersedes"):
                return _refuse(ev.BODY_INVALID, "an undo of a confirm or a discard names the event it undoes")
            return None
        allowed = {"manifest_row"} if kind == "fetched_confirm" else {"manifest_row", "reason", "reason_text"}
        if not isinstance(value, dict) or set(value) - allowed or not isinstance(value.get("manifest_row"), str):
            return _refuse(ev.BODY_INVALID, f"a {kind} value is {{{', '.join(sorted(allowed))}}} with the manifest row")
        if kind == "fetched_discard":
            reason, words = value.get("reason"), value.get("reason_text")
            if reason is None:
                return _refuse(DISCARD_REASON_REQUIRED, "Choose one reason first, then discard.")
            if reason not in DISCARD_REASONS:
                return _refuse(ev.BODY_INVALID, f"a discard reason is one of {', '.join(DISCARD_REASONS)}")
            if reason == "other" and ev._text(words, ev.MAX_REASON_TEXT) is None:
                return _refuse(DISCARD_REASON_REQUIRED, "Other needs a few words.")
            if reason != "other" and words is not None:
                return _refuse(ev.BODY_INVALID, "words go only with the reason Other")
        waiting = self.waiting(study_id, events)
        if waiting is None or str(waiting.get("row_id")) != value["manifest_row"]:
            return _refuse(FETCH_NOT_PENDING, "That file is not waiting for you any more. Reload the table.")
        if kind == "fetched_confirm":
            source = stored_file(self.ws, waiting)
            if source is None or not source.is_file() or _sha256(source) != waiting.get("sha256"):
                return _refuse(FETCH_NOT_PENDING, "The fetched file is no longer on disk as it was fetched.")
        return None

    # -- what a confirm (or its undo) writes besides itself -------------------

    def expand(self, record: dict[str, Any], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Stamp the engine's fields on ``record`` and return the events it brings with it."""
        kind, study_id = record["kind"], record["study_id"]
        base = {"study_id": study_id, "screener_id": record["screener_id"], "at": record["at"],
                "method": "HUMAN", "binding": dict(record["binding"]), "received_at": record["received_at"]}
        if record.get("value") is not None:
            waiting = self.waiting(study_id, events) or {}
            record["fetched"] = {"sha256": waiting.get("sha256"), "size": waiting.get("size"),
                                 "run_id": waiting.get("run_id")}
            if kind == "fetched_discard":
                return []
            attachment = self._attachment_value(study_id, waiting)
            before = ev.current(events, study_id, self.who, "attachment")
            status = ev.current(events, study_id, self.who, "fulltext_status")
            extra = [{"event_id": str(uuid.uuid4()), "kind": "attachment", "value": attachment, **base,
                      **({"supersedes": before["event_id"]} if before else {})},
                     {"event_id": str(uuid.uuid4()), "kind": "fulltext_status", "value": {"status": "retrieved"},
                      **base, **({"supersedes": status["event_id"]} if status else {})}]
            record["links"] = {"attachment": extra[0]["event_id"], "fulltext_status": extra[1]["event_id"]}
            return extra
        if kind != "fetched_confirm":
            return []
        # An undo of a confirm takes back the attachment and the Retrieved it wrote, when they still hold.
        undone = next((e for e in events if e["event_id"] == record.get("supersedes")), None)
        links = (undone or {}).get("links") or {}
        extra = []
        for slot, fallback in (("attachment", None), ("fulltext_status", {"status": "to_get"})):
            linked = links.get(slot)
            head = ev.current(events, study_id, self.who, slot)
            if not linked or head is None or head["event_id"] != linked:
                continue  # changed since the confirm: left as the researcher set it
            earlier = next((e for e in events if e["event_id"] == head.get("supersedes")), None)
            value = earlier.get("value") if earlier is not None else fallback
            extra.append({"event_id": str(uuid.uuid4()), "kind": slot, "value": value, "supersedes": linked, **base})
        return extra

    def _attachment_value(self, study_id: str, row: dict[str, Any]) -> dict[str, Any]:
        address = str(row.get("address") or "")
        tail = unquote(urlsplit(address).path.rsplit("/", 1)[-1]) if address else ""
        name = att.display_name(tail if tail.lower().endswith(".pdf") else f"{study_id}.pdf")
        view = pending_view(row)
        return {
            "name": name, "size": row.get("size"), "sha256": row.get("sha256"),
            "path": att.attached_path(self.ws, study_id).relative_to(self.ws).as_posix(),
            "origin": "fetched", "manifest_row": row.get("row_id"), "run_id": row.get("run_id"),
            "source": view["source"], "host": view["host"], "version": row.get("version"),
            "version_label": view["version_label"], "licence": view["licence"], "identity": view["identity"],
        }

    # -- the file --------------------------------------------------------------

    def place(self, record: dict[str, Any], events: list[dict[str, Any]]) -> Callable[[], None] | None:
        """Copy a confirmed file to ``pdfs/<study_id>.pdf`` before the events are stored.

        Returns how to put the earlier file back if the events then cannot be
        stored. ``OSError`` when the copy or the move fails (nothing is stored).
        """
        if record["kind"] != "fetched_confirm" or record.get("value") is None:
            return None
        study_id = record["study_id"]
        waiting = self.waiting(study_id, events) or {}
        source = stored_file(self.ws, waiting)
        if source is None:
            raise OSError("the fetched file is not where its manifest row says")
        before = ev.current(events, study_id, self.who, "attachment")
        staging = self.ws / att.PDFS_DIR / f".attach-{uuid.uuid4().hex}.tmp"
        staging.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copyfile(source, staging)
            if _sha256(staging) != waiting.get("sha256"):
                raise OSError("the copy does not match the fetched bytes")
            att.place(self.ws, study_id, staging, str(waiting.get("sha256")))
        finally:
            staging.unlink(missing_ok=True)
        earlier = (before or {}).get("value")
        return lambda: att.sync_file(self.ws, study_id, earlier)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --------------------------------------------------------------------------- the plan (no request)


def contact_email() -> str:
    """The contact address the kit sends (``SCHOLAR_MAILTO``, then the kit's ``MAILTO``)."""
    from scholar_pdf.config import contact_email as kit_contact

    return kit_contact()


def openalex_key_set() -> bool:
    """Whether ``SCHOLAR_OPENALEX_KEY`` is set; its value is never read out of the kit."""
    from scholar_pdf.config import openalex_key

    return bool(openalex_key())


def require_mailto() -> str:
    address = contact_email()
    if not address:
        raise ChartingRefused(
            409, MAILTO_NOT_SET,
            "A look-up needs a contact email for Unpaywall, OpenAlex and arXiv. Set SCHOLAR_MAILTO "
            "for the console (environment or .env) and start it again.",
        )
    return address


def _arxiv_id(value: Any) -> tuple[str | None, bool]:
    """``(id, given)``: the id without its version, and whether a value was there at all."""
    from scholar_search.providers.arxiv import split_arxiv_id

    text = str(value or "").strip()
    found, _ = split_arxiv_id(text) if text else (None, None)
    return found, bool(text)


@dataclass
class Selection:
    scope: str
    asked: list[dict[str, Any]]
    counts: dict[str, int]


def select(ws: Path, ids: list[str] | None) -> Selection:
    """Which kept records a run would ask, and what it leaves out (spec 03, questions 4 and 5)."""
    from . import table as tb

    view = tb.table(ws)
    rows = {r["study_id"]: r for r in view["rows"] if r["kept"]}
    counts = Counter()
    if ids is None:
        scope = "to_get"
        candidates = [r for r in rows.values() if r["fulltext"]["status"] == "to_get"]
    else:
        scope = "ids"
        missing = [sid for sid in ids if sid not in rows]
        if missing:
            raise ChartingRefused(409, ev.RECORD_NOT_KEPT,
                                  f"{missing[0]} is not in the kept set any more. Reload the table.")
        candidates = [rows[sid] for sid in dict.fromkeys(ids)]
    asked: list[dict[str, Any]] = []
    for r in candidates:
        ft = r["fulltext"]
        if ft.get("pending_fetch"):
            counts["waiting"] += 1
        elif ft.get("attachment") or ft["status"] not in LOOKUP_STATUSES:
            counts["already_have_file"] += 1
        elif ids is None and ft.get("discarded_fetch"):
            counts["discarded"] += 1  # asked again only when selected on purpose
        else:
            asked.append(r)
    for r in asked:
        arxiv, given = _arxiv_id(r.get("arxiv_id"))
        if r.get("doi"):
            counts["with_doi"] += 1
        elif arxiv:
            counts["with_arxiv_only"] += 1
        else:
            counts["neither"] += 1
            if given:
                counts["arxiv_id_incomplete"] += 1
    counts["total"] = len(candidates)
    counts["asked"] = len(asked)
    return Selection(scope, asked, dict(counts))


def plan(ws: Path | str, ids: list[str] | None = None) -> dict[str, Any]:
    """The look-up plan: counts, the services that would be asked and the e-mail used. Sends nothing."""
    ws = Path(ws)
    email = require_mailto()
    chosen = select(ws, ids)
    c = chosen.counts
    key = openalex_key_set()
    by_doi = c.get("with_doi", 0) > 0
    arxiv_doi_possible = c.get("with_arxiv_only", 0) > 0
    services = {
        "unpaywall": "asked" if by_doi or arxiv_doi_possible else "not_needed",
        "openalex": ("asked" if key else "not_asked") if by_doi or arxiv_doi_possible else "not_needed",
        "arxiv": "asked" if c.get("with_arxiv_only", 0) else "not_needed",
    }
    notes = []
    if services["openalex"] == "not_asked":
        notes.append("OpenAlex is not asked: SCHOLAR_OPENALEX_KEY is not set. Unpaywall is asked alone.")
    return {
        "shape": "charting.fetch-plan-v1",
        "scope": chosen.scope,
        "total": c.get("total", 0),
        "asked": c.get("asked", 0),
        "with_doi": c.get("with_doi", 0),
        "with_arxiv_only": c.get("with_arxiv_only", 0),
        "neither": c.get("neither", 0),
        "arxiv_id_incomplete": c.get("arxiv_id_incomplete", 0),
        "already_have_file": c.get("already_have_file", 0),
        "waiting": c.get("waiting", 0),
        "discarded": c.get("discarded", 0),
        "email": email,
        "openalex_key_set": key,
        "services": services,
        "notes": notes,
        "limits": {"max_bytes": MAX_BYTES, "max_redirects": MAX_REDIRECTS,
                   "arxiv_seconds_between_requests": 3, "same_host_pause_seconds": SAME_HOST_PAUSE},
    }


# --------------------------------------------------------------------------- the run: lock, record, worker


class _Live:
    def __init__(self, ws: Path, run: dict[str, Any]) -> None:
        self.ws, self.run = ws, run
        self.lock = threading.Lock()
        self.cancel = threading.Event()


_LIVE: dict[tuple[str, str], _Live] = {}
_LIVE_GUARD = threading.Lock()
_START_GUARD = threading.RLock()
_ENGINE_ID = uuid.uuid4().hex


def _key(ws: Path, run_id: str) -> tuple[str, str]:
    return (str(Path(ws).resolve()), run_id)


def _live(ws: Path, run_id: str) -> _Live | None:
    with _LIVE_GUARD:
        return _LIVE.get(_key(ws, run_id))


def _run_path(ws: Path, run_id: str) -> Path:
    return Path(ws) / RUNS_DIR / f"{run_id}.json"


def _write_run(ws: Path, run: dict[str, Any]) -> None:
    path = _run_path(ws, run["run_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.stem}.{uuid.uuid4().hex[:8]}.tmp")
    tmp.write_text(json.dumps(run, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for attempt in range(20):  # Windows: a reader may hold the file a moment
        try:
            tmp.replace(path)
            return
        except PermissionError:
            if attempt == 19:
                tmp.unlink(missing_ok=True)
                raise
            time.sleep(0.05)


def _read_run_file(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _pid_alive(pid: int) -> bool:
    from scholar_harness.screening.agent_runs import _pid_alive as alive

    return alive(pid)


def _read_lock(ws: Path) -> dict[str, Any] | None:
    try:
        text = (Path(ws) / LOCK_FILE).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    except OSError:
        return {}
    try:
        info = json.loads(text) if text else {}
    except ValueError:
        info = {}
    return info if isinstance(info, dict) else {}


def _lock_is_stale(ws: Path, info: dict[str, Any]) -> bool:
    if not info.get("run_id") or not isinstance(info.get("pid"), int):
        try:
            return time.time() - (Path(ws) / LOCK_FILE).stat().st_mtime > 30
        except FileNotFoundError:
            return True
    if info["pid"] == os.getpid():
        return info.get("engine") != _ENGINE_ID or _live(ws, info["run_id"]) is None
    return not _pid_alive(info["pid"])


def _acquire(ws: Path, run_id: str) -> None:
    """Take the workspace's fetch lock for ``run_id`` (under ``_START_GUARD``); ``FETCH_ALREADY_ACTIVE`` otherwise.

    A lock whose engine is gone is taken over without writing anything about
    the old run: its state is read as interrupted (spec 03, question 8).
    """
    lock = Path(ws) / LOCK_FILE
    lock.parent.mkdir(parents=True, exist_ok=True)
    owner = json.dumps({"run_id": run_id, "pid": os.getpid(), "engine": _ENGINE_ID})
    for _ in range(2):
        try:
            with lock.open("x", encoding="utf-8") as handle:
                handle.write(owner)
            return
        except FileExistsError as exc:
            info = _read_lock(ws)
            if info is None:
                continue
            if not _lock_is_stale(ws, info):
                raise ChartingRefused(
                    409, FETCH_ALREADY_ACTIVE,
                    "A look-up is already running for this workspace. Wait for it to finish, or cancel it.",
                    run_id=info.get("run_id"),
                ) from exc
            lock.unlink(missing_ok=True)
    raise ChartingRefused(409, FETCH_ALREADY_ACTIVE, "A look-up is already running for this workspace.")


def _release(ws: Path, run_id: str) -> None:
    info = _read_lock(ws)
    if info and info.get("run_id") == run_id:
        (Path(ws) / LOCK_FILE).unlink(missing_ok=True)


@dataclass
class Deps:
    """What a run is built with; the console's tests give stubs (never a live service)."""

    lookup_client: Callable[[], Any] | None = None
    arxiv_client: Callable[[], Any] | None = None
    session: Callable[[], Any] | None = None
    pacer: Callable[[Callable[[str, float], None]], Any] | None = None
    downloader: Callable[..., Any] | None = None


def _default_lookup_client() -> Any:
    from scholar_search.http_client import AcademicHttpClient

    # No on-disk cache: the lookup addresses carry the OpenAlex key and the e-mail (Part K item 2).
    return AcademicHttpClient(name="charting-fetch", rate_limit=LOOKUP_RATE, cache_enabled=False)


def _default_arxiv_client() -> Any:
    from scholar_search.http_client import ARXIV_RATE, AcademicHttpClient

    return AcademicHttpClient(name="arxiv-lookup", rate_limit=ARXIV_RATE, cache_enabled=False)


def _default_session() -> Any:
    import aiohttp

    # trust_env=False: no proxy from the environment either (F5; K3 at the app's level).
    return aiohttp.ClientSession(trust_env=False)


class HostPacer:
    """One request at a time per host, with a pause between two requests to the same host.

    arXiv's hosts share the API's budget (one request every three seconds,
    ``ARXIV_RATE``), so the look-up and the PDFs are paced together.
    """

    def __init__(self, on_wait: Callable[[str, float], None] | None = None, *, pause: float = SAME_HOST_PAUSE,
                 clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], Any] = asyncio.sleep) -> None:
        self.on_wait, self.pause, self.clock, self.sleep = on_wait, pause, clock, sleep
        self.last: dict[str, float] = {}

    async def __call__(self, url: str) -> None:
        from scholar_search.http_client import host_budget

        host = (urlsplit(url).hostname or "").lower()
        if host in _ARXIV_HOSTS or host.endswith(".arxiv.org"):
            budget = host_budget(_ARXIV_API)
            if budget is not None:
                if self.on_wait is not None:
                    self.on_wait(host, 1 / budget.rate if budget.rate > 0 else 0.0)
                await budget.wait()
        else:
            last = self.last.get(host)
            if last is not None:
                wait = self.pause - (self.clock() - last)
                if wait > 0:
                    if self.on_wait is not None:
                        self.on_wait(host, wait)
                    await self.sleep(wait)
            self.last[host] = self.clock()
        if self.on_wait is not None:
            self.on_wait(host, 0.0)  # the request goes now


def _empty_counts() -> dict[str, Any]:
    return {"reached": 0, "found": 0, "downloaded": 0, "failed_checks": 0, "errors": {}, "no_open_copy": 0,
            "no_direct_pdf": 0, "try_later": 0, "skipped_no_id": 0}


def start(
    ws: Path | str,
    ids: list[str] | None = None,
    *,
    executor: Callable[[Callable[[], None]], None] | None = None,
    deps: Deps | None = None,
) -> dict[str, Any]:
    """Start one run for the workspace; returns its record (state ``running``)."""
    from . import table as tb

    ws = Path(ws)
    tb._writable(ws)  # CHARTING_PROTOCOL_REPLACED, SCREENING_NOT_PUBLISHED
    email = require_mailto()  # before anything else: no socket without the contact e-mail
    chosen = select(ws, ids)
    if not chosen.asked:
        raise ChartingRefused(422, ev.BODY_INVALID, "No record of this selection can be looked up.",
                              plan=plan(ws, ids))
    key = openalex_key_set()
    run_id = "FR-" + uuid.uuid4().hex[:24]
    with_arxiv = chosen.counts.get("with_arxiv_only", 0)
    providers = ["unpaywall"] + (["openalex"] if key else []) + (["arxiv"] if with_arxiv else [])
    run = {
        "run_id": run_id, "state": "running", "scope": chosen.scope,
        "study_ids": [r["study_id"] for r in chosen.asked],
        "total": len(chosen.asked), **_empty_counts(), "not_reached": 0,
        "with_doi": chosen.counts.get("with_doi", 0), "with_arxiv_only": with_arxiv,
        "neither": chosen.counts.get("neither", 0),
        "left_out": {k: chosen.counts.get(k, 0) for k in ("already_have_file", "waiting", "discarded")},
        "providers": providers, "email": email, "openalex_key_set": key,
        "now": {"phase": "starting", "host": None}, "recent_requests": [],
        "started_at": now(), "finished_at": None, "cancel_requested": False, "error": None,
    }
    live = _Live(ws, run)
    with _START_GUARD:
        _acquire(ws, run_id)
        with _LIVE_GUARD:
            _LIVE[_key(ws, run_id)] = live
    try:
        _write_run(ws, run)
        append_event(
            ws, STARTED,
            f"Started a look-up of open-access copies for {len(chosen.asked)} record(s)",
            agent="scholar-harness/charting-fetch",
            outputs=[str(RUNS_DIR / f"{run_id}.json").replace("\\", "/"), MANIFEST.as_posix()],
            parameters={"run_id": run_id, "scope": chosen.scope, "providers": providers,
                        "email": email, "openalex_key_set": key,
                        "max_bytes": MAX_BYTES, "max_redirects": MAX_REDIRECTS},
            metrics={"records_asked": len(chosen.asked), "with_doi": run["with_doi"],
                     "with_arxiv_only": with_arxiv, "neither": run["neither"], **run["left_out"]},
            refresh_index=False,
        )
    except BaseException as exc:
        _finish(live, f"{type(exc).__name__}")
        raise
    records = [dict(r) for r in chosen.asked]

    def work() -> None:
        error = None
        try:
            asyncio.run(_execute(live, records, deps or Deps()))
        except BaseException as exc:  # noqa: BLE001 - a crashed run is recorded, never left running
            error = type(exc).__name__
        finally:
            _finish(live, error)

    (executor or (lambda fn: threading.Thread(target=fn, name=f"charting-fetch-{run_id}", daemon=True).start()))(work)
    return read_run(ws, run_id)


def _classify(result: Any, run: dict[str, Any]) -> None:
    """Count one record's result on the run (spec 03, "Running" and the summary)."""
    outcome = getattr(result, "outcome", None)
    run["reached"] += 1
    errors = run["errors"]
    if outcome == SKIPPED_NO_ID:
        run["skipped_no_id"] += 1
        return
    if outcome == "ACQUIRED":
        run["found"] += 1
        run["downloaded"] += 1
        return
    if outcome == "NO_OPEN_COPY_LISTED":
        run["no_open_copy"] += 1
        return
    if outcome == "OPEN_NO_DIRECT_PDF":
        run["no_direct_pdf"] += 1
        return
    attempts = list(getattr(result, "attempts", ()) or ())
    if outcome == "PDF_NOT_FETCHED":
        run["found"] += 1
        if any(a.error and str(a.error).startswith("HTTP 429") for a in attempts):
            run["try_later"] += 1
        elif any(any(not c.passed for c in (a.checks or ())) for a in attempts):
            run["failed_checks"] += 1
        else:
            words = next((str(a.error) for a in reversed(attempts) if a.error), "no PDF")
            kind = words.split(":", 1)[0]
            errors[kind] = errors.get(kind, 0) + 1
        return
    if outcome == "LOOKUP_FAILED":
        lookups = list(getattr(result, "lookups", ()) or ())
        if any(lk.state == "FAILED" and lk.http_status in (409, 429, 503) for lk in lookups):
            run["try_later"] += 1
        else:
            errors["lookup failed"] = errors.get("lookup failed", 0) + 1
        return
    kind = "manifest not written" if outcome == "MANIFEST_NOT_WRITTEN" else "failed"
    errors[kind] = errors.get(kind, 0) + 1


async def _execute(live: _Live, records: list[dict[str, Any]], deps: Deps) -> None:
    from scholar_pdf.downloader import AsyncPDFDownloader, DownloadResult
    from scholar_pdf.open_copies import ANSWERED, FAILED, NOT_FOUND, LookupOutcome, OpenCopy
    from scholar_search.providers.arxiv import ID_LIST_CHUNK, ArxivProvider

    ws, run_id = live.ws, live.run["run_id"]

    def update(**changes: Any) -> None:
        with live.lock:
            live.run.update(changes)
            _write_run(ws, live.run)

    def on_wait(host: str, seconds: float) -> None:
        with live.lock:
            live.run["now"] = (
                {"phase": "waiting", "host": host, "seconds": round(seconds, 1)} if seconds > 0
                else {"phase": "downloading", "host": host}
            )

    pacer = deps.pacer(on_wait) if deps.pacer is not None else HostPacer(on_wait)
    make = deps.downloader or AsyncPDFDownloader
    downloader = make(
        output_dir=ws / FETCHED_DIR, manifest_path=ws / MANIFEST, max_bytes=MAX_BYTES,
        max_redirects=MAX_REDIRECTS, pacer=pacer,
    )
    lookup_client = (deps.lookup_client or _default_lookup_client)()
    arxiv_client = (deps.arxiv_client or _default_arxiv_client)()
    session = (deps.session or _default_session)()

    def extra(record: dict[str, Any], arxiv_id: str | None) -> dict[str, Any]:
        return {"run_id": run_id, "row_id": "FMR-" + uuid.uuid4().hex[:24],
                "arxiv_id": arxiv_id, "record_doi": record.get("doi")}

    try:
        # arXiv's answers first, several ids per request, for the records with no DOI.
        arxiv_only = []
        for record in records:
            found, _ = _arxiv_id(record.get("arxiv_id"))
            if not record.get("doi") and found:
                arxiv_only.append(found)
        answers: dict[str, Any] = {}
        failed: dict[str, LookupOutcome] = {}
        provider = ArxivProvider() if arxiv_only else None
        for begin in range(0, len(arxiv_only), ID_LIST_CHUNK):
            if live.cancel.is_set():
                break
            chunk = arxiv_only[begin:begin + ID_LIST_CHUNK]
            update(now={"phase": "asking", "host": "export.arxiv.org"})
            try:
                answers.update(await provider.lookup_ids(chunk, client=arxiv_client))
            except Exception as error:  # noqa: BLE001 - the ids of this request failed; the rest goes on
                status = getattr(error, "status_code", None)
                for arxiv_id in chunk:
                    failed[arxiv_id] = LookupOutcome("arxiv", FAILED, status if isinstance(status, int) else None,
                                                     type(error).__name__)

        for index, record in enumerate(records):
            if live.cancel.is_set():
                update(not_reached=len(records) - index)
                break
            study_id, title, doi = record["study_id"], record.get("title"), record.get("doi")
            arxiv_id, given = _arxiv_id(record.get("arxiv_id"))
            fields = extra(record, arxiv_id)
            try:
                if doi:
                    update(now={"phase": "asking", "host": "api.unpaywall.org"})
                    result = await downloader.process_doi(session, lookup_client, doi, title=title,
                                                          study_id=study_id, manifest_extra=fields)
                elif arxiv_id and arxiv_id in failed:
                    outcome = failed[arxiv_id]
                    result = downloader.record_outcome(DownloadResult(
                        doi="", success=False, status="FAILED", outcome="LOOKUP_FAILED", study_id=study_id,
                        access_status="UNRESOLVED", lookups=(outcome,),
                        error_message=f"Lookup failed, so the answer is incomplete: arXiv {outcome.failure()}. "
                                      "Run the look-up again later. This is not a paywall determination."),
                        manifest_extra=fields)
                elif arxiv_id and arxiv_id not in answers:
                    result = downloader.record_outcome(DownloadResult(
                        doi="", success=False, status="UNRESOLVED", outcome="NO_OPEN_COPY_LISTED",
                        study_id=study_id, access_status="UNRESOLVED",
                        lookups=(LookupOutcome("arxiv", NOT_FOUND),),
                        error_message="No open copy is listed: arXiv does not know this id. "
                                      "This is not a paywall determination."),
                        manifest_extra=fields)
                elif arxiv_id:
                    entry = answers[arxiv_id]
                    asked = LookupOutcome("arxiv", ANSWERED, 200)
                    copies = []
                    if entry.pdf_url:
                        copies.append(OpenCopy(
                            # Record (d2): "arXiv; licence not given" unless the answer carries one.
                            url=entry.pdf_url, version="submittedVersion",
                            license=entry.license or ARXIV_NO_LICENCE,
                            host_type="repository", source_name="arXiv", provider="arxiv",
                            version_label=f"preprint (arXiv {entry.version or 'version not given'})",
                        ))
                    fields["arxiv_version"] = entry.version
                    fields["arxiv_doi"] = entry.doi
                    if entry.doi:
                        # A journal DOI in arXiv's answer: the services are asked too; the best copy wins (F3).
                        update(now={"phase": "asking", "host": "api.unpaywall.org"})
                        result = await downloader.process_doi(
                            session, lookup_client, entry.doi, title=title, study_id=study_id,
                            extra_copies=copies, prior_lookups=(asked,), manifest_extra=fields)
                    else:
                        update(now={"phase": "downloading", "host": urlsplit(entry.pdf_url or "").hostname})
                        result = await downloader.process_copies(
                            session, copies, title=title, study_id=study_id, lookups=(asked,),
                            manifest_extra=fields)
                else:
                    words = ("its arXiv id has no archive (an old-style id stored without it)" if given
                             else "it has neither a DOI nor an arXiv id")
                    result = downloader.record_outcome(DownloadResult(
                        doi="", success=False, status="SKIPPED", outcome=SKIPPED_NO_ID, study_id=study_id,
                        error_message=f"Not looked up: {words}."), manifest_extra=fields)
            except Exception as error:  # noqa: BLE001 - one record's failure never stops the run
                result = downloader.record_outcome(DownloadResult(
                    doi=doi or "", success=False, status="FAILED", outcome="FAILED", study_id=study_id,
                    error_message=f"failed ({type(error).__name__})"), manifest_extra=fields)
            with live.lock:
                _classify(result, live.run)
                for attempt in getattr(result, "attempts", ()) or ():
                    stored = bool(result.success and attempt.url == result.source_url and attempt.error is None)
                    live.run["recent_requests"].append({"host": attempt.host, "answer": attempt.answer(stored)})
                live.run["recent_requests"] = live.run["recent_requests"][-RECENT_REQUESTS:]
                _write_run(ws, live.run)
    finally:
        for closer in (getattr(session, "close", None), getattr(lookup_client, "close", None),
                       getattr(arxiv_client, "close", None)):
            if closer is not None:
                try:
                    await closer()
                except Exception:  # noqa: BLE001 - closing a client never fails the run
                    pass


def _finish(live: _Live, error: str | None) -> None:
    ws = live.ws
    with live.lock:
        run = live.run
        cancelled = live.cancel.is_set()
        run["state"] = "failed" if error else ("cancelled" if cancelled else "finished")
        run["error"] = error
        run["finished_at"] = now()
        run["now"] = {"phase": "done", "host": None}
        if cancelled and run["not_reached"] == 0:
            run["not_reached"] = max(0, run["total"] - run["reached"])
        try:
            _write_run(ws, run)
        except OSError:
            pass
        snapshot = copy.deepcopy(run)
    try:
        errors = snapshot["errors"]
        append_event(
            ws, FINISHED,
            f"Look-up {snapshot['run_id']} {snapshot['state']}: {snapshot['downloaded']} file(s) to confirm "
            f"of {snapshot['total']} record(s)",
            agent="scholar-harness/charting-fetch",
            outputs=[str(RUNS_DIR / f"{snapshot['run_id']}.json").replace("\\", "/"), MANIFEST.as_posix()],
            parameters={"run_id": snapshot["run_id"], "state": snapshot["state"],
                        "cancelled": snapshot["state"] == "cancelled", "errors_by_kind": errors,
                        "error": error},
            metrics={"asked": snapshot["total"], "reached": snapshot["reached"], "found": snapshot["found"],
                     "downloaded": snapshot["downloaded"], "failed_checks": snapshot["failed_checks"],
                     "errors": sum(errors.values()), "no_open_copy": snapshot["no_open_copy"],
                     "no_direct_pdf": snapshot["no_direct_pdf"], "try_later": snapshot["try_later"],
                     "skipped": snapshot["skipped_no_id"], "not_reached": snapshot["not_reached"]},
            refresh_index=False,
        )
    finally:
        with _START_GUARD:
            _release(ws, snapshot["run_id"])
            with _LIVE_GUARD:
                _LIVE.pop(_key(ws, snapshot["run_id"]), None)


def read_run(ws: Path | str, run_id: str) -> dict[str, Any]:
    ws = Path(ws)
    live = _live(ws, run_id)
    if live is not None:
        with live.lock:
            return copy.deepcopy(live.run)
    data = _read_run_file(_run_path(ws, run_id)) if run_id.startswith("FR-") else None
    if data is None:
        raise ChartingRefused(404, "UNKNOWN_RUN", f"no look-up {run_id}")
    return data


def _view(ws: Path, run: dict[str, Any]) -> dict[str, Any]:
    out = dict(run)
    out.pop("study_ids", None)
    state = run.get("state")
    if state == "running" and run.get("cancel_requested"):
        out["state"] = "cancelling"
    if state == "running" and _live(ws, run["run_id"]) is None:
        # Spec 03, question 8: a run this console did not finish is read as interrupted; nothing is written.
        out["state"] = "interrupted"
    return out


def current(ws: Path | str) -> dict[str, Any]:
    """``GET /charting/fetch``: the running run, else the newest one, else ``idle``."""
    ws = Path(ws)
    info = _read_lock(ws)
    if info and info.get("run_id"):
        live = _live(ws, info["run_id"])
        if live is not None:
            with live.lock:
                return _view(ws, copy.deepcopy(live.run))
    folder = ws / RUNS_DIR
    runs = [r for r in (_read_run_file(p) for p in folder.glob("FR-*.json")) if r] if folder.is_dir() else []
    if not runs:
        return {"state": "idle", "run_id": None}
    newest = max(runs, key=lambda r: (str(r.get("started_at") or ""), str(r.get("run_id"))))
    return _view(ws, newest)


def cancel(ws: Path | str) -> dict[str, Any]:
    """``POST /charting/fetch/cancel``: the run stops after the record in hand."""
    ws = Path(ws)
    info = _read_lock(ws)
    live = _live(ws, info["run_id"]) if info and info.get("run_id") else None
    if live is not None:
        with live.lock:
            if live.run["state"] == "running":
                live.run["cancel_requested"] = True
                live.cancel.set()
                _write_run(ws, live.run)
    return current(ws)


def fetched_file(ws: Path | str, study_id: str) -> tuple[Path, str]:
    """The waiting file of a record, to open (``GET …/fetched``); ``FETCH_NOT_PENDING`` when none."""
    from . import table as tb

    ws = Path(ws)
    att.attached_path(ws, study_id)  # refuses an unsafe study id
    state = tb.read_kept(ws, remember=False)
    if study_id not in state.kept_ids:
        raise ChartingRefused(409, ev.RECORD_NOT_KEPT, "That study is not in the kept set.")
    row = pending_row(read_manifest(ws), ev.read_events(ws), study_id, tb.screener_id(ws))
    path = stored_file(ws, row) if row is not None else None
    if row is None or path is None or not path.is_file():
        raise ChartingRefused(409, FETCH_NOT_PENDING, "No fetched file is waiting on this record.")
    return path, f"{study_id}-fetched.pdf"


def tried(ws: Path | str, study_id: str) -> dict[str, Any]:
    """``GET /charting/records/{id}/fetch``: what was tried for one record (its manifest rows)."""
    from . import table as tb

    ws = Path(ws)
    att.attached_path(ws, study_id)
    state = tb.read_kept(ws, remember=False)
    if study_id not in state.kept_ids and study_id not in state.no_longer_kept:
        raise ChartingRefused(409, ev.RECORD_NOT_KEPT, "That study is not in the kept set.")
    return {"shape": "charting.fetch-tried-v1", "study_id": study_id, "rows": rows_for(ws, study_id)}
