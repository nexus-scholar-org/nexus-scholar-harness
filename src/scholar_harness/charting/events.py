"""Charting events (M12a DoD 3 to 6; decision 2026-11-21, M12a item 10).

Every change is an event, minted on the client (its ``event_id`` is the
idempotency key), appended to ``charting/events/<screener_id>.jsonl`` under an
OS lock, never edited: the screening design (``screening/events.py``). A
request's events and its one ``CHARTING_EVENTS_RECEIVED`` journal row are
written together or not at all.

Undo is a later event of the same kind that ``supersedes`` an earlier one for
the same study and screener and carries the value to go back to. The value of
a (study, kind) is the last stored event no later event supersedes.

Kinds in Part A: ``fulltext_status``, ``fulltext_decision``, ``attachment``
(written by the attachment route; through this intake only to undo or
restore one already stored) and ``link``. Part B adds ``cell``: one value of
one charting column for one study, with an optional note and "where from";
its undo chain is per column (the slot ``cell:<column_id>``), and the engine
stamps the form version and whether the pilot was on.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from scholar_harness.workspace.audit import append_event

from . import CHARTING_DIR
from .lock import LockBusy, locked

EVENTS_DIR = CHARTING_DIR / "events"
JOURNAL_ACTION = "CHARTING_EVENTS_RECEIVED"
MAX_EVENTS = 200
MAX_NOTE_CHARS = 2_000
MAX_REASON_TEXT = 500
MAX_LINK_CHARS = 2_000
MAX_FUTURE_SKEW = timedelta(minutes=5)

KINDS = ("fulltext_status", "fulltext_decision", "attachment", "link", "cell")
MAX_WHERE_FROM = 500
STATUSES = ("to_get", "requested", "retrieved", "not_retrieved")
NOT_RETRIEVED_REASONS = ("no_access", "not_found", "no_reply", "other")
OUTCOMES = ("INCLUDE", "EXCLUDE")
OTHER = "OTHER"

# Refusal codes (console refusal set, screening-api-contract.md §7).
BODY_INVALID = "BODY_INVALID"
RECORD_NOT_KEPT = "RECORD_NOT_KEPT"
FULLTEXT_REASON_REQUIRED = "FULLTEXT_REASON_REQUIRED"
FULLTEXT_REASON_INVALID = "FULLTEXT_REASON_INVALID"
LINK_INVALID = "LINK_INVALID"
IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
ATOMIC_COMMIT_FAILED = "ATOMIC_COMMIT_FAILED"

#: Fields the engine stamps; the client cannot set them and a replay ignores them.
ENGINE_FIELDS = frozenset({"received_at", "binding", "method", "pilot"})
CLIENT_FIELDS = frozenset({"event_id", "study_id", "screener_id", "at", "kind", "value", "note", "where_from", "supersedes"})

_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_SAFE_SCREENER = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass
class Result:
    event_id: str
    result: str  # accepted | duplicate | refused
    refusal: dict[str, str] | None = None

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"event_id": self.event_id, "result": self.result}
        if self.refusal is not None:
            out["refusal"] = self.refusal
        return out


@dataclass(frozen=True)
class Context:
    """What an event is checked against: who may write, which studies are kept, which reasons exist."""

    screener_id: str
    kept: frozenset[str]
    reason_codes: frozenset[str]
    binding: dict[str, Any]
    #: Part B: the charting form a cell is checked against, and whether its pilot is on.
    form: dict[str, Any] | None = None
    pilot: bool = False


def _refuse(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def screener_file(ws: Path, screener_id: str) -> Path:
    safe = _SAFE_SCREENER.sub("_", screener_id).strip("._") or "screener"
    return Path(ws) / EVENTS_DIR / f"{safe}.jsonl"


def read_events(ws: Path) -> list[dict[str, Any]]:
    """Every stored event, across screener files, in file order."""
    directory = Path(ws) / EVENTS_DIR
    out: list[dict[str, Any]] = []
    if not directory.is_dir():
        return out
    for path in sorted(directory.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
    return out


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _text(value: Any, limit: int) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() and len(value) <= limit else None


def _status_refusal(value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict) or value.get("status") not in STATUSES:
        return _refuse(BODY_INVALID, f"a full-text status is one of {', '.join(STATUSES)}")
    extra = set(value) - {"status", "requested_on", "reason", "reason_text"}
    if extra:
        return _refuse(BODY_INVALID, f"unknown field(s) in a full-text status: {', '.join(sorted(extra))}")
    status, reason, words = value["status"], value.get("reason"), value.get("reason_text")
    if value.get("requested_on") is not None:
        if status != "requested":
            return _refuse(BODY_INVALID, "a request date goes only with Requested")
        try:
            date.fromisoformat(str(value["requested_on"]))
        except ValueError:
            return _refuse(BODY_INVALID, "the request date is a calendar date (YYYY-MM-DD)")
    if status != "not_retrieved":
        if reason is not None or words is not None:
            return _refuse(FULLTEXT_REASON_INVALID, "only Not retrieved takes a reason")
        return None
    if reason is None:
        return _refuse(FULLTEXT_REASON_REQUIRED, "Not retrieved needs exactly one reason")
    if reason not in NOT_RETRIEVED_REASONS:
        return _refuse(FULLTEXT_REASON_INVALID, f"a Not retrieved reason is one of {', '.join(NOT_RETRIEVED_REASONS)}")
    if reason == "other":
        if _text(words, MAX_REASON_TEXT) is None:
            return _refuse(FULLTEXT_REASON_REQUIRED, "Other needs a few words")
    elif words is not None:
        return _refuse(FULLTEXT_REASON_INVALID, "words go only with the reason Other")
    return None


def _decision_refusal(value: Any, context: Context) -> dict[str, str] | None:
    if value is None:
        return None  # no decision (an undo back to undecided)
    if not isinstance(value, dict) or value.get("outcome") not in OUTCOMES:
        return _refuse(BODY_INVALID, "a full-text decision is INCLUDE or EXCLUDE")
    extra = set(value) - {"outcome", "reason_code", "reason_text"}
    if extra:
        return _refuse(BODY_INVALID, f"unknown field(s) in a full-text decision: {', '.join(sorted(extra))}")
    code, words = value.get("reason_code"), value.get("reason_text")
    if value["outcome"] == "INCLUDE":
        if code is not None or words is not None:
            return _refuse(FULLTEXT_REASON_INVALID, "an Include takes no reason")
        return None
    if code is None:
        return _refuse(FULLTEXT_REASON_REQUIRED, "an Exclude needs exactly one reason")
    if code == OTHER:
        if _text(words, MAX_REASON_TEXT) is None:
            return _refuse(FULLTEXT_REASON_REQUIRED, "Other needs a few words")
        return None
    if code not in context.reason_codes:
        return _refuse(FULLTEXT_REASON_INVALID, f"{code} is not one of the protocol's exclusion reasons")
    if words is not None:
        return _refuse(FULLTEXT_REASON_INVALID, "words go only with the reason Other")
    return None


def link_refusal(value: Any) -> dict[str, str] | None:
    if value is None:
        return None
    url = value.get("url") if isinstance(value, dict) and set(value) == {"url"} else None
    if not isinstance(url, str) or not url.strip() or len(url) > MAX_LINK_CHARS:
        return _refuse(LINK_INVALID, "a link is one http or https address")
    parts = urlsplit(url.strip())
    if parts.scheme not in ("http", "https") or not parts.netloc or any(c.isspace() for c in url.strip()):
        return _refuse(LINK_INVALID, "a link is one http or https address")
    return None


def _attachment_refusal(value: Any, study_id: str, stored: list[dict[str, Any]]) -> dict[str, str] | None:
    """Through the events route an attachment can only be removed (undo) or put back as it was stored."""
    if value is None:
        return None
    for event in stored:
        if event.get("study_id") == study_id and event.get("kind") == "attachment" and event.get("value") == value:
            return None
    return _refuse(BODY_INVALID, "a file is attached through the attachment route; here it can only be undone or restored")


def shape_refusal(raw: Any, context: Context, stored: list[dict[str, Any]], received_at: str) -> dict[str, str] | None:
    """The typed refusal for one event, or None when it may be stored."""
    if not isinstance(raw, dict):
        return _refuse(BODY_INVALID, "an event is an object")
    unknown = set(raw) - CLIENT_FIELDS
    if unknown:
        return _refuse(BODY_INVALID, f"unknown or engine-only field(s): {', '.join(sorted(unknown))}")
    if not _UUID.match(str(raw.get("event_id") or "")):
        return _refuse(BODY_INVALID, "event_id is a lowercase UUID")
    if raw.get("kind") not in KINDS:
        return _refuse(BODY_INVALID, f"kind is one of {', '.join(KINDS)}")
    if raw.get("screener_id") != context.screener_id:
        return _refuse(BODY_INVALID, f"events are recorded for the workspace's screener ({context.screener_id})")
    at, now = _parse_time(raw.get("at")), _parse_time(received_at)
    if at is None:
        return _refuse(BODY_INVALID, "at is an ISO 8601 time")
    if now is not None and at - now > MAX_FUTURE_SKEW:
        return _refuse(BODY_INVALID, "at is in the future")
    if raw.get("note") is not None and _text(raw.get("note"), MAX_NOTE_CHARS) is None:
        return _refuse(BODY_INVALID, f"a note is text of at most {MAX_NOTE_CHARS} characters")
    if raw.get("where_from") is not None and (raw.get("kind") != "cell" or _text(raw.get("where_from"), MAX_WHERE_FROM) is None):
        return _refuse(BODY_INVALID, f"where_from goes with a cell and is text of at most {MAX_WHERE_FROM} characters")
    if raw.get("supersedes") is not None and not _UUID.match(str(raw.get("supersedes"))):
        return _refuse(BODY_INVALID, "supersedes is an event_id")
    if str(raw.get("study_id") or "") not in context.kept:
        return _refuse(RECORD_NOT_KEPT, "That study is not in the kept set any more. Reload the table.")
    kind, value = raw["kind"], raw.get("value")
    if kind == "fulltext_status":
        return _status_refusal(value)
    if kind == "fulltext_decision":
        return _decision_refusal(value, context)
    if kind == "link":
        return link_refusal(value)
    if kind == "cell":
        if context.form is None:
            return _refuse("CHARTING_COLUMN_UNKNOWN", "The charting form was not created yet. Reload the table.")
        from .form import cell_refusal

        return cell_refusal(value, context.form)
    return _attachment_refusal(value, str(raw["study_id"]), stored)


def request_refusal(events: Any) -> dict[str, str] | None:
    """A refusal of the whole request (DoD 5: a full-text decision is one study per request)."""
    if not isinstance(events, list) or not events:
        return _refuse(BODY_INVALID, "events is a non-empty list")
    if len(events) > MAX_EVENTS:
        return _refuse(BODY_INVALID, f"at most {MAX_EVENTS} events per request")
    decided = {
        str(e.get("study_id")) for e in events if isinstance(e, dict) and e.get("kind") == "fulltext_decision"
    }
    if len(decided) > 1:
        return _refuse(BODY_INVALID, "Decide at full text one study at a time.")
    return None


def _client_content(event: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in event.items() if k not in ENGINE_FIELDS and k != "received_at"}


def slot(event: dict[str, Any]) -> str:
    """What an event's value belongs to: its kind, or ``cell:<column_id>`` for a cell."""
    if event.get("kind") == "cell":
        value = event.get("value") if isinstance(event.get("value"), dict) else {}
        return f"cell:{value.get('column_id')}"
    return str(event.get("kind"))


def heads(events: list[dict[str, Any]], study_id: str, screener_id: str, kind: str) -> list[dict[str, Any]]:
    """The (study, screener, slot) events no later event supersedes, in stored order (``kind`` is a slot)."""
    mine = [
        e for e in events
        if e.get("study_id") == study_id and e.get("screener_id") == screener_id and slot(e) == kind
    ]
    gone = {str(e["supersedes"]) for e in mine if e.get("supersedes")}
    return [e for e in mine if e["event_id"] not in gone]


def current(events: list[dict[str, Any]], study_id: str, screener_id: str, kind: str) -> dict[str, Any] | None:
    """The event that holds the value now: the last stored head."""
    live = heads(events, study_id, screener_id, kind)
    return live[-1] if live else None


def intake(
    ws: Path,
    events: list[Any],
    context: Context,
    *,
    received_at: str,
    journal_description: str | None = None,
    after_commit: Any = None,
) -> list[Result]:
    """Judge and store a request's events; one journal row for the request."""
    try:
        with locked(Path(ws) / EVENTS_DIR / ".lock"):
            return _intake_locked(Path(ws), events, context, received_at, journal_description, after_commit)
    except LockBusy:
        return [
            Result(str(raw.get("event_id") or "") if isinstance(raw, dict) else "", "refused",
                   _refuse(ATOMIC_COMMIT_FAILED, "the charting log is busy; retry"))
            for raw in events
        ]


def _intake_locked(ws, events, context, received_at, journal_description, after_commit) -> list[Result]:
    stored = read_events(ws)
    known = {e["event_id"]: e for e in stored}
    pending: list[dict[str, Any]] = []
    results: list[Result] = []
    for raw in events:
        event_id = str(raw.get("event_id") or "") if isinstance(raw, dict) else ""
        previous = known.get(event_id)
        if previous is not None and isinstance(raw, dict):
            same = _client_content(previous) == _client_content(raw)
            results.append(Result(event_id, "duplicate") if same else Result(
                event_id, "refused", _refuse(IDEMPOTENCY_CONFLICT, "event_id reused with different content")))
            continue
        refusal = shape_refusal(raw, context, stored + pending, received_at)
        if refusal is not None:
            results.append(Result(event_id, "refused", refusal))
            continue
        supersedes = raw.get("supersedes")
        if supersedes and not any(
            e["event_id"] == supersedes and e["study_id"] == raw["study_id"]
            and e["screener_id"] == raw["screener_id"] and slot(e) == slot(raw)
            for e in stored + pending
        ):
            results.append(Result(event_id, "refused", _refuse(
                BODY_INVALID, "supersedes names no earlier event of this kind (and column) for this study")))
            continue
        record = {**raw, "method": "HUMAN", "binding": dict(context.binding), "received_at": received_at}
        if raw["kind"] == "cell":
            record["pilot"] = context.pilot
        pending.append(record)
        known[event_id] = record
        results.append(Result(event_id, "accepted"))
    if pending:
        commit(ws, pending, results, description=journal_description)
        if after_commit is not None and any(r.result == "accepted" for r in results):
            after_commit([p for p in pending if any(r.event_id == p["event_id"] and r.result == "accepted" for r in results)])
    return results


def commit(
    ws: Path,
    pending: list[dict[str, Any]],
    results: list[Result],
    *,
    description: str | None = None,
    action: str = JOURNAL_ACTION,
    extra_parameters: dict[str, Any] | None = None,
    extra_outputs: list[str] | None = None,
) -> None:
    """Append the events and their one journal row, or neither (called under the lock)."""
    sizes: dict[Path, int] = {}
    try:
        by_file: dict[Path, list[dict[str, Any]]] = {}
        for record in pending:
            by_file.setdefault(screener_file(ws, record["screener_id"]), []).append(record)
        for path, records in by_file.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            sizes[path] = path.stat().st_size if path.exists() else 0
            with path.open("a", encoding="utf-8", newline="\n") as handle:
                for record in records:
                    handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
        kinds: dict[str, int] = {}
        for record in pending:
            kinds[record["kind"]] = kinds.get(record["kind"], 0) + 1
        append_event(
            ws,
            action,
            description or f"Received {len(pending)} charting event(s)",
            agent="scholar-harness/charting",
            outputs=sorted({str(p.relative_to(ws)).replace("\\", "/") for p in by_file} | set(extra_outputs or [])),
            parameters={
                "first_event_id": pending[0]["event_id"],
                "last_event_id": pending[-1]["event_id"],
                "screener_id": pending[0]["screener_id"],
                **(extra_parameters or {}),
            },
            metrics={"events": len(pending), **{f"kind_{k}": n for k, n in sorted(kinds.items())}},
            refresh_index=False,
        )
    except Exception:  # any failure rolls the events back
        for path, size in sizes.items():
            with path.open("r+b") as handle:
                handle.truncate(size)
        stored_ids = {record["event_id"] for record in pending}
        for i, result in enumerate(results):
            if result.event_id in stored_ids:
                results[i] = Result(result.event_id, "refused", _refuse(
                    ATOMIC_COMMIT_FAILED, "the events and their journal row could not be written together"))
