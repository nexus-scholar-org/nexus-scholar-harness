"""The charting table's rows and counts, and the writes behind its routes (M12a Part A).

Pure reads of the published kept set (``kept.py``) and the charting events
(``events.py``); the writes go through ``events.intake`` or, for a file, the
attachment path below. Nothing here sends a request (DoD 7).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scholar_harness.workspace.audit import append_event

from . import CHARTING_DIR, ChartingRefused
from . import attachments as att
from . import events as ev
from .kept import CHARTING_PROTOCOL_REPLACED, KeptState, as_dict, protocol_replaced, read_kept
from .lock import LockBusy, locked

logger = logging.getLogger(__name__)

SHAPE = "charting.table-v1"
EXPORT_ACTION = "CHARTING_EXPORTED"
EXPORT_FORMAT_INVALID = "CHARTING_EXPORT_FORMAT_INVALID"
ROUND_LABEL = {"databases": "Databases", "citation_searching": "Citation chasing"}


def now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def screener_id(ws: Path) -> str:
    from scholar_harness.console.api.screening_v1 import _stored_settings

    return str(_stored_settings(ws).get("screener_id") or "researcher:local")


def reason_options(ws: Path) -> list[dict[str, Any]]:
    """The full-text exclusion reasons: the protocol's ``EXC-n``, ``FAILS-INC-n``, then Other (screening's codes)."""
    try:
        protocol = json.loads((Path(ws) / "protocol.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        protocol = {}
    criteria = protocol.get("screening_criteria") or {}

    def _label(item: dict[str, Any]) -> str:
        return str(item.get("description") or item.get("text") or item.get("criterion") or item.get("id"))

    options = [
        {"code": str(c["id"]), "label": _label(c), "kind": "exclusion", "category": c.get("reason_category")}
        for c in criteria.get("exclusion") or [] if isinstance(c, dict) and c.get("id")
    ]
    options += [
        {"code": f"FAILS-{c['id']}", "label": _label(c), "kind": "fails_inclusion", "category": None}
        for c in criteria.get("inclusion") or [] if isinstance(c, dict) and c.get("id")
    ]
    options.append({"code": ev.OTHER, "label": "Other", "kind": "other", "category": None})
    return options


def _binding(ws: Path, state: KeptState) -> dict[str, Any]:
    from scholar_harness.corpus_accept import AcceptCorpusRefused, _protocol_fingerprint

    newest = max(state.sources, key=lambda s: s.round)
    try:
        fingerprint = _protocol_fingerprint(ws)
    except AcceptCorpusRefused:
        fingerprint = None
    return {
        "protocol_fingerprint": fingerprint,
        "generation_id": newest.generation_id,
        "generation_sha256": newest.generation_sha256,
        "round": newest.round,
        "form_version": None,  # Part B: the charting form's version
    }


def context(ws: Path, state: KeptState) -> ev.Context:
    return ev.Context(
        screener_id=screener_id(ws),
        kept=frozenset(state.kept_ids),
        reason_codes=frozenset(o["code"] for o in reason_options(ws) if o["code"] != ev.OTHER),
        binding=_binding(ws, state),
    )


def _value(events: list[dict[str, Any]], study_id: str, who: str, kind: str) -> tuple[Any, str | None]:
    head = ev.current(events, study_id, who, kind)
    return (head.get("value"), head["event_id"]) if head is not None else (None, None)


def row(record: dict[str, Any], events: list[dict[str, Any]], who: str, *, kept: bool, new_since: str | None) -> dict[str, Any]:
    study_id = record["study_id"]
    status, status_event = _value(events, study_id, who, "fulltext_status")
    decision, decision_event = _value(events, study_id, who, "fulltext_decision")
    attachment, attachment_event = _value(events, study_id, who, "attachment")
    link, link_event = _value(events, study_id, who, "link")
    return {
        **record,
        "round_label": ROUND_LABEL.get(str(record.get("arm")), str(record.get("arm") or "")),
        "kept": kept,
        "new_since": new_since,
        "fulltext": {
            "status": (status or {}).get("status", "to_get"),
            "requested_on": (status or {}).get("requested_on"),
            "reason": (status or {}).get("reason"),
            "reason_text": (status or {}).get("reason_text"),
            "attachment": attachment,
            "link": (link or {}).get("url") if isinstance(link, dict) else None,
        },
        "ft_decision": decision,
        # The events that hold each value now: what an undo supersedes.
        "heads": {
            "fulltext_status": status_event, "fulltext_decision": decision_event,
            "attachment": attachment_event, "link": link_event,
        },
    }


def counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    live = [r for r in rows if r["kept"]]

    def _n(test) -> int:
        return sum(1 for r in live if test(r))

    return {
        "kept": len(live),
        "to_get": _n(lambda r: r["fulltext"]["status"] == "to_get"),
        "requested": _n(lambda r: r["fulltext"]["status"] == "requested"),
        "retrieved": _n(lambda r: r["fulltext"]["status"] == "retrieved"),
        "not_retrieved": _n(lambda r: r["fulltext"]["status"] == "not_retrieved"),
        "included": _n(lambda r: (r["ft_decision"] or {}).get("outcome") == "INCLUDE"),
        "excluded": _n(lambda r: (r["ft_decision"] or {}).get("outcome") == "EXCLUDE"),
        "to_decide": _n(lambda r: not r["ft_decision"]),
    }


def table(ws: Path | str) -> dict[str, Any]:
    """``GET /api/v1/charting``: every kept row, the counts and what the screen needs to explain them."""
    ws = Path(ws)
    state = read_kept(ws)
    who = screener_id(ws)
    events = ev.read_events(ws)
    rows = [
        row(as_dict(r), events, who, kept=True, new_since=state.new_since.get(r.study_id)) for r in state.records
    ]
    rows += [
        row({"study_id": sid, "authors": [], "abstract": None, "venue": None, "url": None, "arxiv_id": None,
             "ta_reason": "", "generation_id": summary.get("generation_id"), **summary},
            events, who, kept=False, new_since=None)
        for sid, summary in sorted(state.no_longer_kept.items())
    ]
    replaced = protocol_replaced(ws, state)
    return {
        "shape": SHAPE,
        "screener_id": who,
        "publication": state.publication,
        "rounds": [{"round": s.round, "arm": s.arm, "generation_id": s.generation_id, "published_at": s.published_at}
                   for s in sorted(state.sources, key=lambda s: s.round)],
        "chasing_pending": state.chasing_pending,
        "stale": state.publication.get("status") == "STALE",
        "changes": state.changes,
        "read_only": replaced,
        "read_only_code": CHARTING_PROTOCOL_REPLACED if replaced else None,
        "reason_options": reason_options(ws),
        "not_retrieved_reasons": list(ev.NOT_RETRIEVED_REASONS),
        "counts": counts(rows),
        "rows": rows,
    }


def _writable(ws: Path) -> KeptState:
    state = read_kept(ws)
    if protocol_replaced(ws, state):
        raise ChartingRefused(
            409, CHARTING_PROTOCOL_REPLACED,
            "This table belongs to the old protocol. It is kept, read-only, with that protocol.",
        )
    return state


def _after_commit(ws: Path):
    def sync(stored: list[dict[str, Any]]) -> None:
        for record in stored:
            if record["kind"] == "attachment":
                try:
                    att.sync_file(ws, record["study_id"], record.get("value"))
                except OSError as exc:
                    # Review finding 9: the events stand; the file is put in step on its
                    # next read (``attachment_file``), and is served by its hash meanwhile.
                    logger.warning("attachment file of %s not moved yet: %s", record["study_id"], exc)
    return sync


def post_events(ws: Path | str, events: Any) -> dict[str, Any]:
    """``POST /api/v1/charting/events``: one result per event; one journal row for the request."""
    ws = Path(ws)
    refusal = ev.request_refusal(events)
    if refusal is not None:
        raise ChartingRefused(422, refusal["code"], refusal["message"])
    state = _writable(ws)
    results = ev.intake(ws, events, context(ws, state), received_at=now(), after_commit=_after_commit(ws))
    touched = {str(e.get("study_id")) for e in events if isinstance(e, dict)}
    view = table(ws)
    return {
        "results": [r.as_dict() for r in results],
        "counts": view["counts"],
        "rows": [r for r in view["rows"] if r["study_id"] in touched],
    }


def check_attach(ws: Path | str, study_id: str, event_ids: Iterable[str | None] = ()) -> ev.Context:
    """Everything an attachment is refused for before its body is read."""
    ws = Path(ws)
    ctx = context(ws, _writable(ws))
    att.attached_path(ws, study_id)  # refuses an unsafe study id
    if study_id not in ctx.kept:
        raise ChartingRefused(409, ev.RECORD_NOT_KEPT, "That study is not in the kept set any more. Reload the table.")
    for given in event_ids:
        if given is not None and not ev._UUID.match(given):
            raise ChartingRefused(422, ev.BODY_INVALID, "event ids are lowercase UUIDs")
    return ctx


def attach_pdf(
    ws: Path | str, study_id: str, chunks: Iterable[bytes], *, name: str | None, declared_size: int | None,
    event_id: str | None = None, status_event_id: str | None = None, limit: int | None = None,
) -> dict[str, Any]:
    """Stage and attach in one call (the bytes are in hand)."""
    check_attach(ws, study_id, (event_id, status_event_id))
    staged = att.stage(Path(ws), chunks, declared_size=declared_size, limit=limit)
    return attach_staged(ws, study_id, staged, name=name, event_id=event_id, status_event_id=status_event_id)


def attach_staged(
    ws: Path | str, study_id: str, staged: tuple[Path, int, str], *, name: str | None,
    event_id: str | None = None, status_event_id: str | None = None,
) -> dict[str, Any]:
    """Store a staged PDF as ``pdfs/<study_id>.pdf``; a ``To get`` row becomes Retrieved (undoable)."""
    ws = Path(ws)
    staging, size, sha256 = staged
    try:
        ctx = check_attach(ws, study_id, (event_id, status_event_id))
    except BaseException:
        staging.unlink(missing_ok=True)
        raise
    at = now()
    value = {"name": att.display_name(name), "size": size, "sha256": sha256,
             "path": att.attached_path(ws, study_id).relative_to(ws).as_posix(), "origin": "attached"}
    try:
        with locked(ws / ev.EVENTS_DIR / ".lock"):
            stored = ev.read_events(ws)
            first = {"event_id": event_id or str(uuid.uuid4()), "study_id": study_id, "screener_id": ctx.screener_id,
                     "at": at, "kind": "attachment", "value": value}
            known = next((e for e in stored if e["event_id"] == first["event_id"]), None)
            if known is not None:  # a retried upload: the same bytes are a duplicate, others a conflict
                staging.unlink(missing_ok=True)
                same = known.get("kind") == "attachment" and known.get("study_id") == study_id and (
                    (known.get("value") or {}).get("sha256") == sha256)
                if not same:
                    raise ChartingRefused(409, ev.IDEMPOTENCY_CONFLICT, "event_id reused with different content")
                return {"result": "duplicate", "event_ids": [known["event_id"]],
                        "events": [{"event_id": known["event_id"], "kind": "attachment"}], **_one(ws, study_id)}
            before = ev.current(stored, study_id, ctx.screener_id, "attachment")
            pending = [{**first, "method": "HUMAN", "binding": dict(ctx.binding), "received_at": at}]
            previous_status = ev.current(stored, study_id, ctx.screener_id, "fulltext_status")
            status_value = (previous_status or {}).get("value") or {"status": "to_get"}
            if status_value.get("status") == "to_get":
                pending.append({
                    "event_id": status_event_id or str(uuid.uuid4()), "study_id": study_id,
                    "screener_id": ctx.screener_id, "at": at, "kind": "fulltext_status",
                    "value": {"status": "retrieved"}, "method": "HUMAN", "binding": dict(ctx.binding),
                    "received_at": at,
                    **({"supersedes": previous_status["event_id"]} if previous_status else {}),
                })
            if before is not None:
                pending[0]["supersedes"] = before["event_id"]
            try:
                att.place(ws, study_id, staging, sha256)
            except OSError as exc:  # review finding 9: e.g. the earlier PDF is open in a viewer
                raise ChartingRefused(
                    503, ev.ATOMIC_COMMIT_FAILED,
                    "The earlier PDF of this study could not be moved aside (is it open in another program?). "
                    "Close it and attach again.",
                ) from exc
            results = [ev.Result(p["event_id"], "accepted") for p in pending]
            ev.commit(
                ws, pending, results, action=att.JOURNAL_ACTION,
                description=f"Attached {value['name']} ({size} bytes) to {study_id}",
                extra_parameters={"study_id": study_id, "sha256": sha256, "size": size, "name": value["name"]},
                extra_outputs=[value["path"]],
            )
            if any(r.result == "refused" for r in results):
                att.sync_file(ws, study_id, (before or {}).get("value"))  # put the earlier file back
                raise ChartingRefused(500, ev.ATOMIC_COMMIT_FAILED,
                                      "the attachment's events and their journal row could not be written together")
    except LockBusy as exc:
        staging.unlink(missing_ok=True)
        raise ChartingRefused(503, ev.ATOMIC_COMMIT_FAILED, "the charting log is busy; retry") from exc
    finally:
        staging.unlink(missing_ok=True)
    return {"result": "accepted", "event_ids": [p["event_id"] for p in pending],
            "events": [{"event_id": p["event_id"], "kind": p["kind"]} for p in pending], **_one(ws, study_id)}


def set_link(ws: Path | str, study_id: str, url: str | None, *, event_id: str | None, supersedes: str | None = None) -> dict[str, Any]:
    """A pasted link, stored as text (no request is made to it)."""
    ws = Path(ws)
    state = _writable(ws)
    ctx = context(ws, state)
    event = {"event_id": event_id or str(uuid.uuid4()), "study_id": study_id, "screener_id": ctx.screener_id,
             "at": now(), "kind": "link", "value": {"url": url.strip()} if isinstance(url, str) else None}
    if supersedes:
        event["supersedes"] = supersedes
    results = ev.intake(ws, [event], ctx, received_at=now())
    result = results[0]
    if result.result == "refused":
        code = result.refusal["code"]
        status = 409 if code in (ev.RECORD_NOT_KEPT, ev.IDEMPOTENCY_CONFLICT) else 422
        raise ChartingRefused(status, code, result.refusal["message"])
    return {"result": result.result, "event_ids": [result.event_id],
            "events": [{"event_id": result.event_id, "kind": "link"}], **_one(ws, study_id)}


def _one(ws: Path, study_id: str) -> dict[str, Any]:
    view = table(ws)
    return {"row": next((r for r in view["rows"] if r["study_id"] == study_id), None), "counts": view["counts"]}


def attachment_file(ws: Path | str, study_id: str) -> tuple[Path, str] | None:
    """The PDF of the study's current attachment and its display name (``GET …/attachment``)."""
    ws = Path(ws)
    state = read_kept(ws, remember=False)
    if study_id not in state.kept_ids and study_id not in state.no_longer_kept:
        raise ChartingRefused(409, ev.RECORD_NOT_KEPT, "That study is not in the kept set.")
    value, _ = _value(ev.read_events(ws), study_id, screener_id(ws), "attachment")
    try:
        att.sync_file(ws, study_id, value)  # finish a move an earlier undo could not make
    except OSError:
        pass
    path = att.serve_path(ws, study_id, value)
    return (path, str(value.get("name") or f"{study_id}.pdf")) if path is not None and value else None


# --------------------------------------------------------------------------- the Full text view as a CSV

FULLTEXT_COLUMNS = (
    "study_id", "first_author", "year", "title", "doi", "round", "ta_decision", "fulltext_status",
    "requested_on", "not_retrieved_reason", "file_name", "file_sha256", "link", "ft_decision", "ft_reason",
)
STATUS_WORDS = {"to_get": "To get", "requested": "Requested", "retrieved": "Retrieved", "not_retrieved": "Not retrieved"}
REASON_WORDS = {"no_access": "No access or paywalled", "not_found": "Not found", "no_reply": "Authors did not reply"}


def fulltext_rows(view: dict[str, Any]) -> list[list[str]]:
    out: list[list[str]] = [list(FULLTEXT_COLUMNS)]
    for r in view["rows"]:
        if not r["kept"]:
            continue  # a record no longer kept is left out of exports (DoD 2)
        ft, decision = r["fulltext"], r["ft_decision"] or {}
        reason = ft["reason_text"] if ft["reason"] == "other" else REASON_WORDS.get(ft["reason"] or "", "")
        ft_reason = decision.get("reason_text") if decision.get("reason_code") == ev.OTHER else decision.get("reason_code")
        out.append([
            r["study_id"], (r.get("authors") or [""])[0] if r.get("authors") else "", str(r.get("year") or ""),
            r.get("title") or "", r.get("doi") or "", r["round_label"],
            "Unclear" if r.get("ta_decision") == "MAYBE" else "Include", STATUS_WORDS[ft["status"]],
            ft.get("requested_on") or "", reason or "", (ft.get("attachment") or {}).get("name", ""),
            (ft.get("attachment") or {}).get("sha256", ""), ft.get("link") or "",
            {"INCLUDE": "Include", "EXCLUDE": "Exclude"}.get(decision.get("outcome") or "", ""), ft_reason or "",
        ])
    return out


def render_csv(rows: list[list[str]]) -> bytes:
    """UTF-8 with a BOM and CRLF line ends, so the file opens in Excel (screening export's convention)."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerows(rows)
    return ("﻿" + buffer.getvalue()).encode("utf-8")


def export(ws: Path | str, *, fmt: str, view: str) -> tuple[bytes, str]:
    """``GET /api/v1/charting/export?format=csv&view=fulltext``: the Full text view; journaled with its SHA-256."""
    ws = Path(ws)
    if fmt != "csv" or view != "fulltext":
        raise ChartingRefused(422, EXPORT_FORMAT_INVALID,
                              "Part A exports the Full text view as CSV (format=csv&view=fulltext).")
    data = table(ws)
    body = render_csv(fulltext_rows(data))
    digest = hashlib.sha256(body).hexdigest()
    name = f"charting-fulltext-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.csv"
    append_event(
        ws, EXPORT_ACTION, f"Exported the Full text view ({sum(1 for r in data['rows'] if r['kept'])} rows) as CSV",
        agent="scholar-harness/charting",
        parameters={"format": "csv", "view": "fulltext", "file_name": name, "sha256": digest},
        metrics={"rows": sum(1 for r in data["rows"] if r["kept"])},
        refresh_index=False,
    )
    return body, name


CHARTING_PATHS = (CHARTING_DIR,)
