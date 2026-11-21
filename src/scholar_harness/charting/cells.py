"""The charting cells of one study, as the form and its amendments make them read (M12a DoD 11 to 13).

A cell is the last stored ``cell`` event of its column that no later event
supersedes: a value, Not reported, Not applicable, or cleared (empty). It is
marked "Chart again" when an amendment made after it touched it (record (f)):
a changed type, a removed option its value uses, or a column replaced, split or
merged; a column made from others shows their earlier values as history. Cells
are never deleted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import events as ev
from .form import CHART_AGAIN, read_amendments

HISTORY_LIMIT = 5


def amendment_info(ws: Path, form: dict[str, Any]) -> dict[str, Any]:
    """What the projection needs from the amendments, read once per answer."""
    again_after: dict[str, int] = {}
    removed: dict[str, list[tuple[int, list[str]]]] = {}
    for row in read_amendments(ws):
        change, version = row.get("change"), int(row.get("form_version_to") or 0)
        if change == "options_removed":
            removed.setdefault(str(row.get("column_id")), []).append((version, list(row.get("options") or [])))
        elif change in CHART_AGAIN:
            targets = list(row.get("columns") or []) if change == "split" else [row.get("column_id")]
            for cid in targets:
                if cid:
                    again_after[str(cid)] = max(again_after.get(str(cid), 0), version)
    parents = {c["column_id"]: list(c.get("derived_from") or []) for c in form.get("columns") or []}
    names: dict[str, str] = {}
    for row in read_amendments(ws):  # names of columns that no longer exist, for the history
        change, before = row.get("change"), row.get("from")
        if change == "split" and isinstance(before, str):
            names[str(row.get("column_id"))] = before
        elif change == "replaced" and isinstance(before, str) and row.get("columns"):
            names[str(row["columns"][0])] = before
        elif change == "merged" and isinstance(before, list):
            names.update({str(p): str(n) for p, n in zip(row.get("columns") or [], before)})
    return {"again_after": again_after, "removed": removed, "parents": parents, "names": names}


def _entry(event: dict[str, Any], column_name: str | None = None) -> dict[str, Any]:
    value = event.get("value") or {}
    out = {
        "state": value.get("state"), "value": value.get("value"), "note": event.get("note"),
        "where_from": event.get("where_from"), "at": event.get("at"),
        "form_version": (event.get("binding") or {}).get("form_version"), "event_id": event["event_id"],
    }
    if column_name:
        out["column"] = column_name
    return out


def _uses(value: Any, options: list[str]) -> bool:
    values = value if isinstance(value, list) else [value]
    return any(v in options for v in values)


def project(events: list[dict[str, Any]], study_id: str, who: str, form: dict[str, Any], info: dict[str, Any]) -> dict[str, Any]:
    cells: dict[str, Any] = {}
    for column in form.get("columns") or []:
        cid = column["column_id"]
        slot = f"cell:{cid}"
        mine = [e for e in events if e.get("study_id") == study_id and e.get("screener_id") == who and ev.slot(e) == slot]
        head = ev.current(events, study_id, who, slot)
        value = (head or {}).get("value") or {}
        state = value.get("state")
        version = int(((head or {}).get("binding") or {}).get("form_version") or 0)
        history = [_entry(e) for e in mine if head is None or e["event_id"] != head["event_id"]]
        history = [h for h in history if h["state"] is not None]
        chart_again = False
        if head is not None and state is not None:
            if info["again_after"].get(cid, 0) > version:
                chart_again = True
            for removed_at, options in info["removed"].get(cid, []):
                if removed_at > version and state == "value" and _uses(value.get("value"), options):
                    chart_again = True
        elif info["parents"].get(cid):
            for parent in info["parents"][cid]:
                earlier = ev.current(events, study_id, who, f"cell:{parent}")
                if earlier is not None and (earlier.get("value") or {}).get("state") is not None:
                    history.append(_entry(earlier, info["names"].get(parent, parent)))
                    chart_again = True
        cells[cid] = {
            "state": state,
            "value": value.get("value") if state == "value" else None,
            "note": (head or {}).get("note") if state is not None else None,
            "where_from": (head or {}).get("where_from") if state is not None else None,
            "pilot": bool((head or {}).get("pilot")) if state is not None else False,
            "chart_again": chart_again,
            "history": history[-HISTORY_LIMIT:],
            "event_id": (head or {}).get("event_id"),
            "form_version": version or None,
        }
    return cells


def charted(row: dict[str, Any], form: dict[str, Any]) -> bool:
    """Every column holds a value, Not reported or Not applicable, and none waits to be charted again."""
    columns = form.get("columns") or []
    if not columns or not row.get("kept") or (row.get("ft_decision") or {}).get("outcome") == "EXCLUDE":
        return False
    return all(
        (row["cells"].get(c["column_id"]) or {}).get("state") is not None
        and not (row["cells"].get(c["column_id"]) or {}).get("chart_again")
        for c in columns
    )


def has_values(events: list[dict[str, Any]]) -> bool:
    """True once any cell holds something (the form then changes only by recorded amendment)."""
    gone = {str(e["supersedes"]) for e in events if e.get("supersedes")}
    return any(
        e.get("kind") == "cell" and (e.get("value") or {}).get("state") is not None and e["event_id"] not in gone
        for e in events
    )
