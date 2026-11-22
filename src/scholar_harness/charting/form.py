"""The charting form beside the protocol (M12a DoD 10, 12, 13; decision 2026-11-21, M12a items 2 and 9).

``charting/form.json`` is seeded once, at the table's first read, from the
protocol's ``matrix_dimensions`` (id, name, description, data type, required)
and then holds what the protocol cannot: the options of a list column, the
Yes/No type and the order. ``protocol.json`` is never written, so its
fingerprint and every binding stay as they are.

Every save names the version it was made from and raises the version by one.
Before any cell holds a value a change is free (journaled
``CHARTING_FORM_CHANGED``); after, it needs a one-sentence reason and writes
one row per change to ``charting/form_amendments.jsonl`` and one
``CHARTING_FORM_AMENDED`` journal row. Cells are never deleted: a removed
option, a changed type, or a column split or merged marks the cells it touches
"Chart again" (computed from the amendments, see :func:`chart_again_after`).

The pilot is on at first visit; "End pilot" is one recorded action
(``CHARTING_PILOT_ENDED``). A cell saved while it is on is marked Pilot.
"""

from __future__ import annotations

import json
import math
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scholar_harness.workspace.audit import append_event

from . import CHARTING_DIR, ChartingRefused
from .lock import locked

FORM_FILE = CHARTING_DIR / "form.json"
AMENDMENTS_FILE = CHARTING_DIR / "form_amendments.jsonl"
FORM_SCHEMA = "nexus.charting-form.v1"
AMENDMENT_SCHEMA = "nexus.charting-form-amendment.v1"
TYPES = ("text", "number", "one", "several", "yes_no")
YES_NO = ("Yes", "No")
FROM_PROTOCOL = {"free_text": "text", "numeric": "number", "categorical": "one", "list": "several"}
MAX_NAME = 200
MAX_DEFINITION = 2_000
MAX_OPTION = 200
MAX_OPTIONS = 50
MAX_COLUMNS = 40
MAX_REASON = 500
MAX_TEXT_VALUE = 5_000

CHARTING_VALUE_INVALID = "CHARTING_VALUE_INVALID"
CHARTING_COLUMN_UNKNOWN = "CHARTING_COLUMN_UNKNOWN"
CHARTING_AMENDMENT_REASON_REQUIRED = "CHARTING_AMENDMENT_REASON_REQUIRED"
CHARTING_FORM_STALE = "CHARTING_FORM_STALE"
BODY_INVALID = "BODY_INVALID"
ATOMIC_COMMIT_FAILED = "ATOMIC_COMMIT_FAILED"

_COLUMN_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _protocol_fingerprint(ws: Path) -> str | None:
    from scholar_harness.corpus_accept import AcceptCorpusRefused, _protocol_fingerprint as fp

    try:
        return fp(ws)
    except AcceptCorpusRefused:
        return None


def _seed_columns(ws: Path) -> list[dict[str, Any]]:
    try:
        protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        protocol = {}
    columns: list[dict[str, Any]] = []
    seen: set[str] = set()
    for dim in protocol.get("matrix_dimensions") or []:
        if not isinstance(dim, dict) or not dim.get("id"):
            continue
        column_id = re.sub(r"[^A-Za-z0-9_-]+", "_", str(dim["id"]))[:64] or f"col_{len(columns) + 1}"
        if column_id in seen:
            continue
        seen.add(column_id)
        columns.append({
            "column_id": column_id,
            "name": str(dim.get("name") or dim["id"])[:MAX_NAME],
            "definition": str(dim.get("description") or "")[:MAX_DEFINITION],
            "type": FROM_PROTOCOL.get(str(dim.get("data_type") or "free_text"), "text"),
            "options": [],
            "required": bool(dim.get("required")),
            "from_protocol": str(dim["id"]),
            "derived_from": [],
        })
    return columns


def read_form(ws: Path) -> dict[str, Any] | None:
    """The form, None when there is none yet; a file that is not a form this version reads is refused, never replaced."""
    path = Path(ws) / FORM_FILE
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ChartingRefused(409, CHARTING_FORM_STALE,
                              f"charting/form.json cannot be read ({type(exc).__name__}); it is kept as it is.") from exc
    if not (isinstance(data, dict) and data.get("schema") == FORM_SCHEMA):
        # Review of Part B, finding 8: a hand-edited or newer form is never seeded over.
        raise ChartingRefused(409, CHARTING_FORM_STALE,
                              "charting/form.json is not a charting form this version reads; it is kept as it is.")
    return data


def _write_form(ws: Path, form: dict[str, Any]) -> None:
    from scholar_harness.workspace.atomic import atomic_write_text

    path = Path(ws) / FORM_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, json.dumps(form, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def ensure_form(ws: Path, screener_id: str) -> dict[str, Any]:
    """The form, seeded once from the protocol (version 1, ``CHARTING_FORM_CREATED``)."""
    ws = Path(ws)
    form = read_form(ws)
    if form is not None:
        return form
    with locked(ws / CHARTING_DIR / ".lock"):
        form = read_form(ws)
        if form is not None:
            return form
        columns = _seed_columns(ws)
        form = {
            "schema": FORM_SCHEMA,
            "version": 1,
            "created_at": now(),
            "created_by": screener_id,
            "protocol_fingerprint": _protocol_fingerprint(ws),
            "columns": columns,
            "pilot": {"on": True, "ended_at": None, "ended_by": None, "ended_at_version": None},
            "updated_at": now(),
        }
        _write_form(ws, form)
        append_event(
            ws, "CHARTING_FORM_CREATED",
            f"Charting form created from the protocol's {len(columns)} charting column(s); the pilot is on",
            agent="scholar-harness/charting", outputs=[FORM_FILE.as_posix()],
            parameters={"version": 1, "columns": [c["column_id"] for c in columns],
                        "protocol_fingerprint": form["protocol_fingerprint"], "screener_id": screener_id},
            metrics={"columns": len(columns)}, refresh_index=False,
        )
    return form


def read_amendments(ws: Path) -> list[dict[str, Any]]:
    path = Path(ws) / AMENDMENTS_FILE
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    return rows


# --------------------------------------------------------------------------- columns


def _clean_text(value: Any, limit: int, what: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not value.strip() and not allow_empty) or len(value) > limit:
        raise ChartingRefused(422, BODY_INVALID, f"{what} is text of at most {limit} characters")
    return value.strip()


def validate_columns(raw: Any) -> list[dict[str, Any]]:
    """The columns a client sends, checked and normalised (refuses ``BODY_INVALID``)."""
    if not isinstance(raw, list) or len(raw) > MAX_COLUMNS:
        raise ChartingRefused(422, BODY_INVALID, f"columns is a list of at most {MAX_COLUMNS}")
    out: list[dict[str, Any]] = []
    ids: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise ChartingRefused(422, BODY_INVALID, "a column is an object")
        extra = set(item) - {"column_id", "name", "definition", "type", "options", "required", "from_protocol", "derived_from"}
        if extra:
            raise ChartingRefused(422, BODY_INVALID, f"unknown column field(s): {', '.join(sorted(extra))}")
        column_id = str(item.get("column_id") or "")
        if not _COLUMN_ID.match(column_id) or column_id in ids:
            raise ChartingRefused(422, BODY_INVALID, "a column_id is unique: letters, digits, '-' and '_'")
        ids.add(column_id)
        kind = item.get("type")
        if kind not in TYPES:
            raise ChartingRefused(422, BODY_INVALID, f"a column type is one of {', '.join(TYPES)}")
        options = item.get("options") or []
        if not isinstance(options, list) or len(options) > MAX_OPTIONS:
            raise ChartingRefused(422, BODY_INVALID, f"options is a list of at most {MAX_OPTIONS}")
        options = [_clean_text(o, MAX_OPTION, "an option") for o in options]
        if len(set(options)) != len(options):
            raise ChartingRefused(422, BODY_INVALID, "options are distinct")
        if kind == "yes_no":
            options = list(YES_NO)
        elif kind in ("text", "number"):
            if options:
                raise ChartingRefused(422, BODY_INVALID, "only a list column has options")
        derived = item.get("derived_from") or []
        if not isinstance(derived, list) or not all(isinstance(d, str) for d in derived):
            raise ChartingRefused(422, BODY_INVALID, "derived_from is a list of column ids")
        out.append({
            "column_id": column_id,
            "name": _clean_text(item.get("name"), MAX_NAME, "a column name"),
            "definition": _clean_text(item.get("definition") or "", MAX_DEFINITION, "a definition", allow_empty=True),
            "type": kind,
            "options": options,
            "required": bool(item.get("required")),
            "from_protocol": item.get("from_protocol") if isinstance(item.get("from_protocol"), str) else None,
            "derived_from": derived,
        })
    return out


def diff(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One change per thing that differs: added, removed, renamed, definition, type, options, required, split, merged, order."""
    old = {c["column_id"]: c for c in before}
    new = {c["column_id"]: c for c in after}
    changes: list[dict[str, Any]] = []
    sources: dict[str, list[str]] = {}
    for c in after:
        for parent in c.get("derived_from") or []:
            if parent in old and parent not in new:
                sources.setdefault(parent, []).append(c["column_id"])
    targets: dict[str, list[str]] = {}
    for parent, children in sources.items():
        for child in children:
            targets.setdefault(child, []).append(parent)
    for parent, children in sources.items():
        if len(children) > 1:
            changes.append({"change": "split", "column_id": parent, "from": old[parent]["name"],
                            "to": [new[c]["name"] for c in children], "columns": children})
    for child, parents in targets.items():
        if len(parents) > 1:
            changes.append({"change": "merged", "column_id": child, "from": [old[p]["name"] for p in parents],
                            "to": new[child]["name"], "columns": parents})
        elif len(sources[parents[0]]) == 1:
            changes.append({"change": "replaced", "column_id": child, "from": old[parents[0]]["name"],
                            "to": new[child]["name"], "columns": parents})
    for cid, c in new.items():
        if cid not in old and cid not in targets:
            changes.append({"change": "added", "column_id": cid, "from": None, "to": c["name"]})
    for cid, c in old.items():
        if cid not in new and cid not in sources:
            changes.append({"change": "removed", "column_id": cid, "from": c["name"], "to": None})
    for cid in [c["column_id"] for c in after if c["column_id"] in old]:
        a, b = old[cid], new[cid]
        if a["name"] != b["name"]:
            changes.append({"change": "renamed", "column_id": cid, "from": a["name"], "to": b["name"]})
        if a["definition"] != b["definition"]:
            changes.append({"change": "definition", "column_id": cid, "from": a["definition"], "to": b["definition"]})
        if a["type"] != b["type"]:
            changes.append({"change": "type", "column_id": cid, "from": a["type"], "to": b["type"]})
        added = [o for o in b["options"] if o not in a["options"]]
        removed = [o for o in a["options"] if o not in b["options"]]
        if added and a["type"] == b["type"] and b["type"] != "yes_no":
            changes.append({"change": "options_added", "column_id": cid, "from": a["options"], "to": b["options"], "options": added})
        if removed and a["type"] == b["type"] and b["type"] != "yes_no":
            changes.append({"change": "options_removed", "column_id": cid, "from": a["options"], "to": b["options"], "options": removed})
        if a["required"] != b["required"]:
            changes.append({"change": "required", "column_id": cid, "from": a["required"], "to": b["required"]})
    order_before = [c["column_id"] for c in before if c["column_id"] in new]
    order_after = [c["column_id"] for c in after if c["column_id"] in old]
    if order_before != order_after:
        changes.append({"change": "order", "column_id": None, "from": order_before, "to": order_after})
    return changes


#: Changes that mark the cells they touch "Chart again" (record (f)).
CHART_AGAIN = frozenset({"type", "options_removed", "split", "merged", "replaced"})


def save(
    ws: Path, columns_raw: Any, *, base_version: Any, reason: Any, screener_id: str, has_values: bool,
    protocol_fingerprint: str | None, generation_id: str | None,
) -> dict[str, Any]:
    """Save a new form version; after any value exists, the change needs a reason and is an amendment."""
    ws = Path(ws)
    columns = validate_columns(columns_raw)
    with locked(ws / CHARTING_DIR / ".lock"):
        form = read_form(ws)
        if form is None:
            raise ChartingRefused(409, CHARTING_FORM_STALE, "The charting form was not created yet. Reload the table.")
        if base_version != form["version"]:
            raise ChartingRefused(409, CHARTING_FORM_STALE,
                                  "The form changed since you opened it. Reload the table.", version=form["version"])
        changes = diff(form["columns"], columns)
        if not changes:
            return form
        current = {x["column_id"]: x for x in form["columns"]}
        for c in columns:
            # A column new in this save, or whose sources change, may only derive from a column of
            # this form; a column made by an earlier split keeps naming its source (review of Part B,
            # finding 1: the panel sends it back, and the split's history is read from it).
            prior = current.get(c["column_id"])
            if prior is not None and list(prior.get("derived_from") or []) == c["derived_from"]:
                continue
            unknown = [p for p in c["derived_from"] if p not in current]
            if unknown:
                raise ChartingRefused(422, BODY_INVALID, f"derived_from names no column of the form: {', '.join(unknown)}")
        text = reason.strip() if isinstance(reason, str) else ""
        if has_values and (not text or len(text) > MAX_REASON):
            raise ChartingRefused(422, CHARTING_AMENDMENT_REASON_REQUIRED, "Say in one sentence why the form changes.")
        version = int(form["version"]) + 1
        at = now()
        pilot = bool((form.get("pilot") or {}).get("on"))
        previous = form
        path = ws / AMENDMENTS_FILE
        size = path.stat().st_size if path.exists() else None
        try:
            if has_values:
                path.parent.mkdir(parents=True, exist_ok=True)
                amendment_id = f"amd_{uuid.uuid4().hex[:12]}"
                with path.open("a", encoding="utf-8", newline="\n") as handle:
                    for n, change in enumerate(changes, start=1):
                        row = {
                            "schema": AMENDMENT_SCHEMA, "amendment_id": amendment_id, "change_no": n, **change,
                            "reason": text, "pilot": pilot, "amended_by": screener_id, "amended_at": at,
                            "form_version_from": form["version"], "form_version_to": version,
                            "protocol_fingerprint": protocol_fingerprint, "generation_id": generation_id,
                        }
                        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            form = {**form, "columns": columns, "version": version, "updated_at": at}
            _write_form(ws, form)
            append_event(
                ws, "CHARTING_FORM_AMENDED" if has_values else "CHARTING_FORM_CHANGED",
                (f"Charting form amended to version {version}: " if has_values else f"Charting form changed to version {version} (no value yet): ")
                + "; ".join(c["change"] for c in changes),
                agent="scholar-harness/charting",
                outputs=[FORM_FILE.as_posix()] + ([AMENDMENTS_FILE.as_posix()] if has_values else []),
                parameters={"version": version, "changes": changes, "reason": text or None, "pilot": pilot,
                            "screener_id": screener_id},
                metrics={"changes": len(changes)}, refresh_index=False,
            )
        except Exception as exc:  # review of Part B, finding 7: all three writes or none
            _roll_back(ws, previous, path, size)
            raise ChartingRefused(503, ATOMIC_COMMIT_FAILED,
                                  "The form change and its journal row could not be written together; nothing changed.") from exc
    return form


def _roll_back(ws: Path, previous: dict[str, Any], amendments: Path, size: int | None) -> None:
    """Put the form and the amendments file back as they were before a failed save."""
    try:
        if size is None:
            amendments.unlink(missing_ok=True)
        elif amendments.exists():
            with amendments.open("r+b") as handle:
                handle.truncate(size)
        _write_form(ws, previous)
    except OSError:
        pass  # the refusal still says nothing changed; the next read shows what is on disk


def end_pilot(ws: Path, *, screener_id: str, base_version: Any) -> dict[str, Any]:
    """"End pilot": one recorded action (``CHARTING_PILOT_ENDED``); values charted in the pilot stay final."""
    ws = Path(ws)
    with locked(ws / CHARTING_DIR / ".lock"):
        form = read_form(ws)
        if form is None or base_version != form["version"]:
            raise ChartingRefused(409, CHARTING_FORM_STALE, "The form changed since you opened it. Reload the table.")
        if not (form.get("pilot") or {}).get("on"):
            return form
        at = now()
        previous = form
        form = {**form, "pilot": {"on": False, "ended_at": at, "ended_by": screener_id,
                                  "ended_at_version": form["version"]}, "updated_at": at}
        try:
            _write_form(ws, form)
            append_event(ws, "CHARTING_PILOT_ENDED", "The charting pilot ended",
                         agent="scholar-harness/charting", outputs=[FORM_FILE.as_posix()],
                         parameters={"version": form["version"], "screener_id": screener_id}, refresh_index=False)
        except Exception as exc:
            _roll_back(ws, previous, Path(ws) / AMENDMENTS_FILE, (Path(ws) / AMENDMENTS_FILE).stat().st_size
                       if (Path(ws) / AMENDMENTS_FILE).exists() else None)
            raise ChartingRefused(503, ATOMIC_COMMIT_FAILED,
                                  "The end of the pilot and its journal row could not be written together.") from exc
    return form


# --------------------------------------------------------------------------- cells


def cell_refusal(value: Any, form: dict[str, Any]) -> dict[str, str] | None:
    """The refusal for one cell value, or None. ``value`` is ``{column_id, state, value?}``; state null clears."""
    if not isinstance(value, dict):
        return {"code": BODY_INVALID, "message": "a cell is {column_id, state, value}"}
    extra = set(value) - {"column_id", "state", "value"}
    if extra:
        return {"code": BODY_INVALID, "message": f"unknown cell field(s): {', '.join(sorted(extra))}"}
    column = next((c for c in form["columns"] if c["column_id"] == value.get("column_id")), None)
    if column is None:
        return {"code": CHARTING_COLUMN_UNKNOWN, "message": "That column is not in the charting form."}
    state = value.get("state")
    if state is None:
        return None if value.get("value") is None else {"code": BODY_INVALID, "message": "a cleared cell holds no value"}
    if state in ("not_reported", "not_applicable"):
        return None if value.get("value") is None else {
            "code": BODY_INVALID, "message": "Not reported and Not applicable hold no value"}
    if state != "value":
        return {"code": BODY_INVALID, "message": "a cell state is value, not_reported, not_applicable or null"}
    v, kind = value.get("value"), column["type"]
    bad = {"code": CHARTING_VALUE_INVALID, "message": "That value does not fit the column."}
    if kind == "text":
        return None if isinstance(v, str) and v.strip() and len(v) <= MAX_TEXT_VALUE else bad
    if kind == "number":
        try:
            ok = isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
        except OverflowError:  # review of Part B, finding 2: an integer beyond a float's range
            ok = False
        return None if ok else bad
    if kind in ("one", "yes_no"):
        return None if isinstance(v, str) and v in column["options"] else {
            "code": CHARTING_VALUE_INVALID, "message": "That value is not one of the options."}
    if kind == "several":
        ok = (isinstance(v, list) and v and all(isinstance(x, str) for x in v)  # strings first (review, finding 2)
              and len(set(v)) == len(v) and all(x in column["options"] for x in v))
        return None if ok else {"code": CHARTING_VALUE_INVALID, "message": "Those values are not all options."}
    return bad


def chart_again_after(ws: Path) -> dict[str, int]:
    """For each column, the form version from which earlier cells must be charted again (record (f))."""
    out: dict[str, int] = {}
    for row in read_amendments(ws):
        if row.get("change") not in CHART_AGAIN:
            continue
        version = int(row.get("form_version_to") or 0)
        cols = [row["column_id"]] if row.get("change") in ("type", "options_removed", "merged", "replaced") else []
        if row.get("change") == "split":
            cols = list(row.get("columns") or [])
        for cid in cols:
            if cid:
                out[cid] = max(out.get(cid, 0), version)
    return out
