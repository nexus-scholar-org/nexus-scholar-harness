"""The charting table's rows and counts, and the writes behind its routes (M12a Part A).

Pure reads of the published kept set (``kept.py``) and the charting events
(``events.py``); the writes go through ``events.intake`` or, for a file, the
attachment path below. Nothing here sends a request (DoD 7).
"""

from __future__ import annotations

import csv
import hashlib
import io
import logging
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scholar_harness.workspace.audit import append_event

from . import CHARTING_DIR, ChartingRefused
from . import attachments as att
from . import cells as cl
from . import events as ev
from . import fetch as fx
from . import form as fm
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
    """The full-text exclusion reasons: ``EXC-n``, ``FAILS-INC-n``, then Other (screening's codes).

    Read through the one reader of the criteria in force (M11b part A, DoD 2):
    a criterion revised before the first approval gives the wording in force,
    and a retired one is not offered.
    """
    from scholar_harness.screening import criteria as criteria_reader

    in_force = criteria_reader.criteria_in_force(ws)
    options = [
        {"code": c.id, "label": c.text or c.id, "kind": "exclusion", "category": c.reason_category}
        for c in in_force.exclusion
    ]
    options += [
        {"code": f"FAILS-{c.id}", "label": c.text or c.id, "kind": "fails_inclusion", "category": None}
        for c in in_force.inclusion
    ]
    options.append({"code": ev.OTHER, "label": "Other", "kind": "other", "category": None})
    return options


def _binding(ws: Path, state: KeptState, form: dict[str, Any] | None = None) -> dict[str, Any]:
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
        "form_version": (form or {}).get("version"),
    }


def context(ws: Path, state: KeptState) -> ev.Context:
    who = screener_id(ws)
    form = fm.ensure_form(ws, who)
    return ev.Context(
        screener_id=who,
        kept=frozenset(state.kept_ids),
        reason_codes=frozenset(o["code"] for o in reason_options(ws) if o["code"] != ev.OTHER),
        binding=_binding(ws, state, form),
        form=form,
        pilot=bool((form.get("pilot") or {}).get("on")),
        fetch=fx.Hooks(ws, who),
    )


def _value(events: list[dict[str, Any]], study_id: str, who: str, kind: str) -> tuple[Any, str | None]:
    head = ev.current(events, study_id, who, kind)
    return (head.get("value"), head["event_id"]) if head is not None else (None, None)


def row(
    record: dict[str, Any], events: list[dict[str, Any]], who: str, *, kept: bool, new_since: str | None,
    form: dict[str, Any] | None = None, info: dict[str, Any] | None = None,
    index: dict[tuple[str, str, str], list[dict[str, Any]]] | None = None,
    fetched: fx.TableState | None = None,
) -> dict[str, Any]:
    study_id = record["study_id"]
    index = index if index is not None else cl.build_index(events)

    def _held(kind: str) -> tuple[Any, str | None]:
        head = cl.head_of(index.get((study_id, who, kind), []))
        return (head.get("value"), head["event_id"]) if head is not None else (None, None)

    status, status_event = _held("fulltext_status")
    decision, decision_event = _held("fulltext_decision")
    attachment, attachment_event = _held("attachment")
    link, link_event = _held("link")
    _, confirm_event = _held("fetched_confirm")
    _, discard_event = _held("fetched_discard")
    fetched = fetched or fx.TableState()
    cells = cl.project(events, study_id, who, form, info, index) if form is not None and info is not None else {}
    out = {
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
            # Part F: a fetched file waiting for the researcher ("Fetched, to confirm"); the status
            # above keeps the earlier one, and the row is counted apart (spec 03, question 1).
            "pending_fetch": fetched.pending.get(study_id),
            "last_lookup": fetched.last.get(study_id),
            "discarded_fetch": fetched.discarded.get(study_id),
        },
        "ft_decision": decision,
        # The events that hold each value now: what an undo supersedes.
        "heads": {
            "fulltext_status": status_event, "fulltext_decision": decision_event,
            "attachment": attachment_event, "link": link_event,
            "fetched_confirm": confirm_event, "fetched_discard": discard_event,
        },
        # Part B: one cell per form column; "No full text" when the row is charted without a retrieved copy.
        "cells": cells,
        "no_full_text": (status or {}).get("status", "to_get") != "retrieved",
    }
    out["charted"] = cl.charted(out, form) if form is not None else False
    out["pilot"] = any(c.get("pilot") for c in cells.values())
    return out


def counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    live = [r for r in rows if r["kept"]]

    def _n(test) -> int:
        return sum(1 for r in live if test(r))

    def _waiting(r: dict[str, Any]) -> bool:
        return bool(r["fulltext"].get("pending_fetch"))

    return {
        "kept": len(live),
        # Part F (spec 03, question 1): a row whose fetched file waits leaves To get, Requested and
        # Not retrieved and is counted in "to confirm", so the counts still add up to the kept total.
        "to_get": _n(lambda r: r["fulltext"]["status"] == "to_get" and not _waiting(r)),
        "requested": _n(lambda r: r["fulltext"]["status"] == "requested" and not _waiting(r)),
        "retrieved": _n(lambda r: r["fulltext"]["status"] == "retrieved"),
        "not_retrieved": _n(lambda r: r["fulltext"]["status"] == "not_retrieved" and not _waiting(r)),
        "to_confirm": _n(_waiting),
        # The PRISMA full-text counts read the status alone: a file waiting is neither retrieved nor
        # assessed, and these do not move until it is confirmed (DoD F5).
        "prisma": {
            "sought": len(live),
            "not_retrieved": _n(lambda r: r["fulltext"]["status"] == "not_retrieved"),
            "retrieved": _n(lambda r: r["fulltext"]["status"] == "retrieved"),
            "assessed": _n(lambda r: bool(r["ft_decision"])),
        },
        "included": _n(lambda r: (r["ft_decision"] or {}).get("outcome") == "INCLUDE"),
        "excluded": _n(lambda r: (r["ft_decision"] or {}).get("outcome") == "EXCLUDE"),
        "to_decide": _n(lambda r: not r["ft_decision"]),
        # Part B: rows excluded at full text are not counted as charted or not charted.
        "charted": _n(lambda r: r.get("charted", False)),
        "not_charted": _n(lambda r: not r.get("charted", False) and (r["ft_decision"] or {}).get("outcome") != "EXCLUDE"),
        "pilot": _n(lambda r: r.get("pilot", False)),
    }


def table(ws: Path | str) -> dict[str, Any]:
    """``GET /api/v1/charting``: every kept row, the counts and what the screen needs to explain them."""
    ws = Path(ws)
    state = read_kept(ws)
    who = screener_id(ws)
    replaced = protocol_replaced(ws, state)
    # The form is seeded at the first visit (DoD 10), not while the table is read-only.
    form = (fm.read_form(ws) if replaced else fm.ensure_form(ws, who)) or {"columns": [], "version": 0, "pilot": {"on": False}}
    info = cl.amendment_info(ws, form)
    events = ev.read_events(ws)
    index = cl.build_index(events)
    # The records no longer kept keep their waiting file and last look-up on the row (spec 03, "Stale").
    fetched = fx.table_state(ws, events, who, [r.study_id for r in state.records] + sorted(state.no_longer_kept))
    rows = [
        row(as_dict(r), events, who, kept=True, new_since=state.new_since.get(r.study_id), form=form, info=info,
            index=index, fetched=fetched)
        for r in state.records
    ]
    rows += [
        row({"study_id": sid, "authors": [], "abstract": None, "venue": None, "url": None, "arxiv_id": None,
             "ta_reason": "", "generation_id": summary.get("generation_id"), **summary},
            events, who, kept=False, new_since=None, form=form, info=info, index=index, fetched=fetched)
        for sid, summary in sorted(state.no_longer_kept.items())
    ]
    _warn_duplicates(rows)
    summary = counts(rows)
    summary.update(open_cells(rows, form))
    from . import report as rp

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
        "counts": summary,
        "form": {**form, "amendments": fm.read_amendments(ws), "has_values": cl.has_values(events)},
        # Part C: what the last export wrote ("Exported 21 Nov 14:32: 68 rows"); None before the first.
        "last_export": rp.last_export(ws),
        "rows": rows,
    }


def open_cells(rows: list[dict[str, Any]], form: dict[str, Any]) -> dict[str, int]:
    """Cells not charted yet, and those of required columns (the screen's ``openCells`` rule; record (h))."""
    columns = form.get("columns") or []
    open_all = open_required = 0
    for r in rows:
        if not r["kept"] or (r["ft_decision"] or {}).get("outcome") == "EXCLUDE":
            continue
        for c in columns:
            cell = (r.get("cells") or {}).get(c["column_id"]) or {}
            if cell.get("state") is None or cell.get("chart_again"):
                open_all += 1
                open_required += 1 if c.get("required") else 0
    return {"cells_open": open_all, "required_open": open_required}


def _warn_duplicates(rows: list[dict[str, Any]]) -> None:
    """The same bytes waiting or attached on two kept rows are named on both (record (d2), check 5)."""
    by_hash: dict[str, set[str]] = {}
    for r in rows:
        if not r["kept"]:
            continue
        ft = r["fulltext"]
        for sha in ((ft.get("pending_fetch") or {}).get("sha256"), (ft.get("attachment") or {}).get("sha256")):
            if sha:
                by_hash.setdefault(sha, set()).add(r["study_id"])
    for r in rows:
        pending = r["fulltext"].get("pending_fetch")
        if pending:
            pending["duplicate_of"] = sorted(by_hash.get(pending["sha256"], set()) - {r["study_id"]})


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
    if ctx.fetch is not None and ctx.fetch.waiting(study_id, ev.read_events(ws)) is not None:
        raise ChartingRefused(409, fx.FETCH_FILE_WAITING,
                              "A fetched file is waiting on this row. Confirm it or discard it first.")
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
    # Part C, with Part F (record (h)): where the file in use came from, and the fetched copy's version and licence.
    "file_origin", "file_source", "file_version", "file_licence",
)
ORIGIN_WORDS = {"attached": "Attached", "fetched": "Fetched"}
STATUS_WORDS = {"to_get": "To get", "requested": "Requested", "retrieved": "Retrieved", "not_retrieved": "Not retrieved"}
#: A row whose fetched file waits: never "Retrieved" in an export (spec 03, "Copy", export words).
TO_CONFIRM_WORDS = "Fetched, to confirm"


def status_words(fulltext: dict[str, Any]) -> str:
    return TO_CONFIRM_WORDS if fulltext.get("pending_fetch") else STATUS_WORDS[fulltext["status"]]
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
            "Unclear" if r.get("ta_decision") == "MAYBE" else "Include", status_words(ft),
            ft.get("requested_on") or "", reason or "", (ft.get("attachment") or {}).get("name", ""),
            (ft.get("attachment") or {}).get("sha256", ""), ft.get("link") or "",
            {"INCLUDE": "Include", "EXCLUDE": "Exclude"}.get(decision.get("outcome") or "", ""), ft_reason or "",
            *_file_words(ft.get("attachment") or {}),
        ])
    return out


def _file_words(attachment: dict[str, Any]) -> list[str]:
    """Origin, source, version and licence of the file in use; a researcher's own file has the first only."""
    if not attachment:
        return ["", "", "", ""]
    origin = str(attachment.get("origin") or "attached")
    if origin != "fetched":
        return [ORIGIN_WORDS.get(origin, origin), "", "", ""]
    return ["Fetched", str(attachment.get("source") or ""), str(attachment.get("version_label") or attachment.get("version") or ""),
            str(attachment.get("licence") or "")]


def render_csv(rows: list[list[str]]) -> bytes:
    """UTF-8 with a BOM and CRLF line ends, so the file opens in Excel (screening export's convention)."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerows(rows)
    return ("﻿" + buffer.getvalue()).encode("utf-8")


CELL_WORDS = {"not_reported": "Not reported", "not_applicable": "Not applicable"}


def _cell_text(cell: dict[str, Any]) -> str:
    """A cell as the file writes it: the value, "Not reported", "Not applicable", or empty when not charted."""
    state = cell.get("state")
    if state in CELL_WORDS:
        return CELL_WORDS[state]
    if state != "value":
        return ""
    value = cell.get("value")
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def charting_rows(view: dict[str, Any]) -> list[list[str]]:
    """The Charting view as rows: one per record kept and not excluded at full text (record (h))."""
    columns = (view.get("form") or {}).get("columns") or []
    header = ["study_id", "first_author", "year", "title", "doi", "round", "fulltext_status", "no_full_text", "pilot"]
    for c in columns:
        header += [c["name"], f"{c['name']} (note)", f"{c['name']} (where from)"]
    out: list[list[str]] = [header]
    for r in view["rows"]:
        if not r["kept"] or (r["ft_decision"] or {}).get("outcome") == "EXCLUDE":
            continue
        line = [
            r["study_id"], (r.get("authors") or [""])[0] if r.get("authors") else "", str(r.get("year") or ""),
            r.get("title") or "", r.get("doi") or "", r["round_label"], status_words(r["fulltext"]),
            "No full text" if r.get("no_full_text") else "", "Pilot" if r.get("pilot") else "",
        ]
        for c in columns:
            cell = r["cells"].get(c["column_id"]) or {}
            line += [_cell_text(cell), cell.get("note") or "", cell.get("where_from") or ""]
        out.append(line)
    return out


def export(ws: Path | str, *, fmt: str, view: str | None) -> tuple[bytes, str]:
    """``GET /api/v1/charting/export?format=csv&view=fulltext|charting`` or ``format=xlsx``.

    Every export writes ``charting/prisma_fulltext.json``, the ``CHARTING_EXPORTED`` journal row with the
    file's SHA-256 (DoD 16, 18) and the last export the screen shows. Nothing blocks an export: it says
    how many cells are not charted yet and how many required cells are empty (record (h)).
    """
    from . import report as rp

    ws = Path(ws)
    if fmt == "xlsx":
        view = None
    elif fmt != "csv" or (view or "fulltext") not in ("fulltext", "charting"):
        raise ChartingRefused(422, EXPORT_FORMAT_INVALID,
                              "The table exports a CSV of the Full text view or the Charting view "
                              "(format=csv&view=fulltext|charting), or the spreadsheet (format=xlsx).")
    else:
        view = view or "fulltext"
    data = table(ws)
    at = rp.now_iso()
    stamp = datetime.fromisoformat(at).strftime("%Y%m%dT%H%M%SZ")
    if fmt == "xlsx":
        body = rp.xlsx(ws, data, at)
        rows = len(charting_rows(data)) - 1
        name, words = f"charting-{stamp}.xlsx", "the spreadsheet"
    else:
        lines = fulltext_rows(data) if view == "fulltext" else charting_rows(data)
        body, rows = render_csv(lines), len(lines) - 1
        name = f"charting-{view}-{stamp}.csv"
        words = f"the {'Full text' if view == 'fulltext' else 'Charting'} view as CSV"
    digest = hashlib.sha256(body).hexdigest()
    prisma_path = rp.write_prisma(ws, rp.prisma_fulltext(data), at)
    counts_now = data["counts"]
    metrics = {"rows": rows, "not_charted": counts_now["not_charted"], "cells_open": counts_now["cells_open"],
               "required_open": counts_now["required_open"]}
    append_event(
        ws, EXPORT_ACTION, f"Exported {words} ({rows} rows)",
        agent="scholar-harness/charting", outputs=[prisma_path],
        parameters={"format": fmt, "view": view, "file_name": name, "sha256": digest},
        metrics=metrics, refresh_index=False,
    )
    rp.write_last_export(ws, {"at": at, "format": fmt, "view": view, "file_name": name, "sha256": digest, **metrics})
    return body, name


# --------------------------------------------------------------------------- the form (Part B)


def get_form(ws: Path | str) -> dict[str, Any]:
    """``GET /api/v1/charting/form``: the form (seeded at the first visit) and its amendments."""
    return table(Path(ws))["form"]


def put_form(ws: Path | str, columns: Any, *, base_version: Any, reason: Any) -> dict[str, Any]:
    """``PUT /api/v1/charting/form``: a new version; after any value exists, a recorded amendment with its reason."""
    ws = Path(ws)
    state = _writable(ws)
    ctx = context(ws, state)
    # Review of Part B, finding 7: "has values" is read, and the form saved, while no cell can be
    # stored (the events lock is held; the form's own lock is taken inside, always in this order).
    try:
        with locked(ws / ev.EVENTS_DIR / ".lock"):
            fm.save(
                ws, columns, base_version=base_version, reason=reason, screener_id=ctx.screener_id,
                has_values=cl.has_values(ev.read_events(ws)),
                protocol_fingerprint=ctx.binding.get("protocol_fingerprint"),
                generation_id=ctx.binding.get("generation_id"),
            )
    except LockBusy as exc:
        raise ChartingRefused(503, ev.ATOMIC_COMMIT_FAILED, "the charting log is busy; retry") from exc
    return get_form(ws)


def end_pilot(ws: Path | str, *, base_version: Any) -> dict[str, Any]:
    """``POST /api/v1/charting/form/pilot/end``: "End pilot", recorded once."""
    ws = Path(ws)
    _writable(ws)
    fm.end_pilot(ws, screener_id=screener_id(ws), base_version=base_version)
    return get_form(ws)


def record(ws: Path | str, study_id: str) -> dict[str, Any]:
    """``GET /api/v1/charting/records/{study_id}``: one study for the one-study view, with the form."""
    view = table(Path(ws))
    found = next((r for r in view["rows"] if r["study_id"] == study_id), None)
    if found is None:
        raise ChartingRefused(409, ev.RECORD_NOT_KEPT, "That study is not in the kept set any more. Back to the table.")
    return {"shape": "charting.record-v1", "screener_id": view["screener_id"], "row": found, "form": view["form"],
            "read_only": view["read_only"],
            "reason_options": view["reason_options"], "not_retrieved_reasons": view["not_retrieved_reasons"],
            "publication": view["publication"], "counts": view["counts"]}


CHARTING_PATHS = (CHARTING_DIR,)
