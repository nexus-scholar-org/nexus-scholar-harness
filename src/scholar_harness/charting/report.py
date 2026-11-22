"""The PRISMA full-text counts, the methods paragraph and the spreadsheet (M12a Part C, record (h)).

Pure reads of the table (``table.table``), the form and its amendments, and the
journal's look-up rows; the only writes are the export's own: the file the
researcher downloads, ``charting/prisma_fulltext.json``, ``charting/last_export.json``
and the ``CHARTING_EXPORTED`` journal row (DoD 15 to 18). Screening's own
``prisma_report.json`` is never read for writing nor rewritten (DoD 16).

Every count is of **reports**, as the record says (scope (c)): reports of one
study are not linked in M12a, and the paragraph says so.
"""

from __future__ import annotations

import io
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import CHARTING_DIR
from . import events as ev
from . import form as fm

PRISMA_FILE = CHARTING_DIR / "prisma_fulltext.json"
PRISMA_SCHEMA = "nexus.charting-prisma-fulltext.v1"
LAST_EXPORT_FILE = CHARTING_DIR / "last_export.json"
JOURNAL_FILE = Path("audit") / "journal.jsonl"
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

ARMS = (("databases", "Databases"), ("citation_searching", "Citation chasing"))
NOT_RETRIEVED_WORDS = {
    "no_access": "No access or paywalled", "not_found": "Not found", "no_reply": "Authors did not reply", "other": "Other",
}
DISCARD_WORDS = {"wrong_paper": "the wrong paper", "not_full_text": "not the full text", "unreadable": "unreadable", "other": "other"}
SERVICE_NAMES = {"unpaywall": "Unpaywall", "openalex": "OpenAlex", "arxiv": "arXiv"}
CHANGE_WORDS = {
    "added": 'added "{to}"',
    "removed": 'removed "{from}"',
    "renamed": 'renamed "{from}" to "{to}"',
    "definition": 'changed the definition of "{name}"',
    "type": 'changed the type of "{name}"',
    "options_added": 'added options to "{name}"',
    "options_removed": 'removed options from "{name}"',
}


# --------------------------------------------------------------------------- the PRISMA full-text counts


def _empty() -> dict[str, Any]:
    return {
        "sought": 0, "not_retrieved": 0, "not_retrieved_reasons": {}, "assessed": 0, "excluded": 0,
        "exclusion_reasons": {}, "included": 0,
        # The working state: what is still open, so the numbers add up before the stage ends.
        "awaiting_retrieval": 0, "to_confirm": 0, "retrieved_not_assessed": 0, "assessed_without_full_text": 0,
    }


def _add(group: dict[str, Any], r: dict[str, Any]) -> None:
    ft, decision = r["fulltext"], r["ft_decision"] or {}
    status, waiting = ft["status"], bool(ft.get("pending_fetch"))
    group["sought"] += 1
    if status == "not_retrieved":
        group["not_retrieved"] += 1
        key = NOT_RETRIEVED_WORDS.get(str(ft.get("reason") or ""), "Other")
        group["not_retrieved_reasons"][key] = group["not_retrieved_reasons"].get(key, 0) + 1
    if decision:
        group["assessed"] += 1
        if status != "retrieved":
            group["assessed_without_full_text"] += 1
        if decision.get("outcome") == "EXCLUDE":
            group["excluded"] += 1
            code = str(decision.get("reason_code") or ev.OTHER)
            group["exclusion_reasons"][code] = group["exclusion_reasons"].get(code, 0) + 1
        elif decision.get("outcome") == "INCLUDE":
            group["included"] += 1
    elif status == "retrieved":
        group["retrieved_not_assessed"] += 1
    elif status != "not_retrieved":
        group["awaiting_retrieval"] += 1
    if waiting:
        group["to_confirm"] += 1


def prisma_fulltext(view: dict[str, Any]) -> dict[str, Any]:
    """Per round, per arm (Databases / Citation chasing) and in total, from the kept rows (DoD 16)."""
    rounds: dict[int, dict[str, Any]] = {}
    arms = {arm: _empty() for arm, _ in ARMS}
    total = _empty()
    for source in view.get("rounds") or []:
        rounds[int(source["round"])] = {"round": int(source["round"]), "arm": source["arm"],
                                        "label": dict(ARMS).get(source["arm"], str(source["arm"])),
                                        "generation_id": source.get("generation_id"),
                                        "published_at": source.get("published_at"), **_empty()}
    for r in view["rows"]:
        if not r["kept"]:
            continue  # a record no longer kept is not sought (DoD 2)
        number = int(r.get("round") or 0)
        if number not in rounds:
            rounds[number] = {"round": number, "arm": r.get("arm"), "label": r.get("round_label") or "",
                              "generation_id": r.get("generation_id"), "published_at": None, **_empty()}
        _add(rounds[number], r)
        _add(arms.setdefault(str(r.get("arm") or ""), _empty()), r)
        _add(total, r)
    return {
        "schema": PRISMA_SCHEMA,
        "unit": "reports",
        "rounds": [rounds[k] for k in sorted(rounds)],
        "arms": arms,
        "total": total,
    }


# --------------------------------------------------------------------------- the methods paragraph


def _series(parts: list[str]) -> str:
    if len(parts) <= 1:
        return "".join(parts)
    return f"{', '.join(parts[:-1])} and {parts[-1]}"


def _reasons(counts: dict[str, int], labels: dict[str, str] | None = None) -> str:
    """``label (code): n`` for a criterion (the code kept for tracing), ``word: n`` otherwise; most frequent first."""
    labels = labels or {}

    def name(key: str) -> str:
        label = labels.get(key)
        return f"{label} ({key})" if label and label != key and key != ev.OTHER else ("Other" if key == ev.OTHER else key)

    return "; ".join(f"{name(k)}: {v}" for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def _were(n: int) -> str:
    return f"{n} was" if n == 1 else f"{n} were"


def _reports(n: int) -> str:
    return f"{n} report" if n == 1 else f"{n} reports"


def _studies(n: int) -> str:
    return f"{n} study" if n == 1 else f"{n} studies"


def _reviewers(ws: Path, kinds: tuple[str, ...]) -> int:
    """How many reviewers recorded events of these kinds (each events file is one screener's)."""
    return len({str(e.get("screener_id")) for e in ev.read_events(ws) if e.get("kind") in kinds and e.get("value") is not None})


def _by(n: int) -> str:
    return "one reviewer" if n <= 1 else f"{n} reviewers, each decision recorded by one of them"


def _journal_rows(ws: Path, action: str) -> list[dict[str, Any]]:
    path = Path(ws) / JOURNAL_FILE
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if action not in line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and row.get("action") == action:
            out.append(row)
    return out


def _services(ws: Path) -> list[str]:
    """The services the look-ups asked, from their start rows in the journal (Part F)."""
    from .fetch import STARTED

    seen: list[str] = []
    for row in _journal_rows(ws, STARTED):
        for p in (row.get("parameters") or {}).get("providers") or []:
            name = SERVICE_NAMES.get(str(p), str(p))
            if name not in seen:
                seen.append(name)
    order = list(SERVICE_NAMES.values())
    return sorted(seen, key=lambda s: order.index(s) if s in order else len(order))


def amendment_list(amendments: list[dict[str, Any]], columns: dict[str, str]) -> list[dict[str, Any]]:
    """One entry per recorded amendment (its rows share an ``amendment_id``), in order, with its words."""
    grouped: dict[str, dict[str, Any]] = {}
    for row in amendments:
        key = str(row.get("amendment_id") or row.get("amended_at") or len(grouped))
        entry = grouped.setdefault(key, {"amendment_id": key, "at": row.get("amended_at"), "reason": row.get("reason"),
                                         "pilot": bool(row.get("pilot")), "changes": []})
        entry["changes"].append(_change_words(row, columns))
    return list(grouped.values())


def _quoted(names: Any) -> str:
    return _series([f'"{n}"' for n in names]) if isinstance(names, list) else f'"{names}"'


def _change_words(row: dict[str, Any], columns: dict[str, str]) -> str:
    kind = row.get("change")
    # The column's name now; for a change of definition, type, options or "required", ``to`` is not a name.
    name = columns.get(str(row.get("column_id")), row.get("column_id"))
    if kind == "order":
        return "changed the order of the columns"
    if kind == "required":
        return f'made "{name}" ' + ("required" if row.get("to") else "optional")
    if kind == "split":
        return f'split "{row.get("from")}" into {_quoted(row.get("to") or [])}'
    if kind == "merged":
        return f'merged {_quoted(row.get("from") or [])} into "{row.get("to")}"'
    if kind == "replaced":
        return f'replaced "{row.get("from")}" with "{row.get("to")}"'
    template = CHANGE_WORDS.get(str(kind), f"{kind} " + '"{name}"')
    return template.format(**{"from": row.get("from"), "to": row.get("to"), "name": name})


def _date(value: Any) -> str:
    return str(value or "")[:10]


def methods(ws: Path | str, view: dict[str, Any] | None = None) -> dict[str, Any]:
    """The methods block of record (h): every number computed, the reviewer sentence from the events (DoD 17)."""
    from . import table as tb

    ws = Path(ws)
    view = view if view is not None else tb.table(ws)
    prisma = prisma_fulltext(view)
    t = prisma["total"]
    live = [r for r in view["rows"] if r["kept"]]
    form = view.get("form") or {}
    columns = form.get("columns") or []
    labels = {o["code"]: (o["label"] if o["code"] != ev.OTHER else "Other") for o in view.get("reason_options") or []}
    sentences: list[str] = []
    caveats: list[str] = []
    not_stated: list[str] = []

    # 1. Retrieval.
    retrieval = f"Of {_reports(t['sought'])} sought for retrieval, {_were(t['not_retrieved'])} not retrieved"
    retrieval += f" ({_reasons(t['not_retrieved_reasons'])})." if t["not_retrieved"] else "."
    sentences.append(retrieval)

    # 2. Open-access copies (Part F): confirmed copies in use, and those discarded.
    fetched = [r for r in live if ((r["fulltext"].get("attachment") or {}).get("origin") == "fetched")]
    discarded = [r for r in live if r["fulltext"].get("discarded_fetch")]
    services = _services(ws)
    if fetched or discarded:
        where = _series(services) if services else "open-access services"
        reasons = Counter(DISCARD_WORDS.get(str((r["fulltext"]["discarded_fetch"] or {}).get("reason")), "other") for r in discarded)
        tail = f"; {_were(len(discarded))} discarded ({_reasons(dict(reasons))})" if discarded else ""
        if fetched:
            sentences.append(
                f"Open-access copies of {_reports(len(fetched))} were located with {where} "
                f"and each was checked by the reviewer before use{tail}."
            )
        else:
            sentences.append(f"Open-access copies were looked up with {where}; none was used{tail}.")

    # 3. Eligibility at full text.
    deciders = _reviewers(ws, ("fulltext_decision",))
    if t["assessed"]:
        excluded = f"{_were(t['excluded'])} excluded ({_reasons(t['exclusion_reasons'], labels)})" if t["excluded"] else "none was excluded"
        sentences.append(
            f"{_reports(t['assessed'])} {'was' if t['assessed'] == 1 else 'were'} assessed at full text by {_by(deciders)}; "
            f"{excluded} and {_were(t['included'])} included."
        )
    else:
        sentences.append("No report has been assessed at full text yet.")

    # 4. Charting: the form, its pilot and its amendments.
    charters = _reviewers(ws, ("cell",))
    cells = [c for r in live for c in (r.get("cells") or {}).values() if c.get("state") is not None]
    names = {c["column_id"]: c["name"] for c in columns}
    amended = amendment_list(fm.read_amendments(ws), names)
    if cells:
        piloted = view["counts"].get("pilot", 0)
        sentence = f"Data were charted by {_by(charters)} using a form"
        sentence += f" piloted on {_studies(piloted)}" if piloted else " that was not piloted"
        if amended:
            listed = [f"on {_date(a['at'])} ({'; '.join(a['changes'])}" + (f": {a['reason']}" if a.get("reason") else "") + ")"
                      for a in amended]
            sentence += f" and revised {_series(listed)}"
        sentences.append(sentence + ".")
        states = {c.get("state") for c in cells}
        if "not_reported" in states:
            sentences.append("'Not reported' was recorded when a study did not report an item.")
        if "not_applicable" in states:
            sentences.append("'Not applicable' was recorded when an item did not apply to a study.")
        abstract_only = [
            r for r in live
            if (r["ft_decision"] or {}).get("outcome") != "EXCLUDE" and r["fulltext"]["status"] != "retrieved"
            and any(c.get("state") is not None for c in (r.get("cells") or {}).values())
        ]
        if abstract_only:
            sentences.append(
                f"{_studies(len(abstract_only))} {'was' if len(abstract_only) == 1 else 'were'} charted from the abstract only "
                "because no full text was retrieved."
            )
        if (form.get("pilot") or {}).get("on"):
            caveats.append("The pilot of the charting form has not been ended.")
    elif columns:
        sentences.append("No data have been charted yet.")
    sentences.append("The counts are of reports; reports of the same study were not linked.")

    # What is still open: the export never blocks, it says so (record (h)).
    open_now = t["awaiting_retrieval"] + t["retrieved_not_assessed"]
    if open_now:
        caveats.append(
            f"{_reports(open_now)} {'is' if open_now == 1 else 'are'} not yet retrieved or not yet assessed "
            f"({t['awaiting_retrieval']} awaiting retrieval, {t['retrieved_not_assessed']} retrieved and not assessed); "
            "the counts describe the work so far."
        )
    if t["to_confirm"]:
        caveats.append(f"{t['to_confirm']} fetched {'copy waits' if t['to_confirm'] == 1 else 'copies wait'} for the reviewer's confirmation "
                       f"and {'is' if t['to_confirm'] == 1 else 'are'} not counted as retrieved.")
    if t["assessed_without_full_text"]:
        caveats.append(f"{_reports(t['assessed_without_full_text'])} {'was' if t['assessed_without_full_text'] == 1 else 'were'} decided "
                       "at full text without a retrieved full text.")
    counts = view["counts"]
    if counts.get("cells_open"):
        caveats.append(
            f"{counts['cells_open']} {'cell is' if counts['cells_open'] == 1 else 'cells are'} not charted yet, "
            f"{counts.get('required_open', 0)} of them in required columns."
        )
    if len(view.get("rounds") or []) > 1:
        not_stated.append("The sentences give totals over every round; the PRISMA counts are split by round.")
    figures = {
        "prisma": prisma,
        "open_access": {"used": len(fetched), "discarded": len(discarded), "services": services},
        "reviewers": {"fulltext_decisions": deciders, "charting": charters},
        "charted": counts.get("charted", 0), "not_charted": counts.get("not_charted", 0),
        "cells_open": counts.get("cells_open", 0), "required_open": counts.get("required_open", 0),
        "pilot": counts.get("pilot", 0), "amendments": amended,
    }
    return {
        "shape": "charting.methods-v1",
        "sentences": sentences,
        "paragraph": " ".join(sentences),
        "figures": figures,
        "caveats": caveats,
        "not_stated": not_stated,
    }


# --------------------------------------------------------------------------- the spreadsheet


def _text(value: Any) -> str:
    from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

    return ILLEGAL_CHARACTERS_RE.sub("", "" if value is None else str(value))


def _sheet(book: Any, title: str, rows: list[list[Any]], *, header: bool = True, widths: dict[int, int] | None = None) -> Any:
    """A sheet whose text cells are always text: a value starting with "=" is never a formula."""
    from openpyxl.styles import Font

    sheet = book.create_sheet(title)
    for r, line in enumerate(rows, start=1):
        for c, value in enumerate(line, start=1):
            cell = sheet.cell(row=r, column=c)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                cell.value = _text(value)
                cell.data_type = "s"
            else:
                cell.value = value
            if header and r == 1:
                cell.font = Font(bold=True)
    if header and rows:
        sheet.freeze_panes = "A2"
    for c, width in (widths or {}).items():
        sheet.column_dimensions[_letter(c)].width = width
    return sheet


def _letter(n: int) -> str:
    from openpyxl.utils import get_column_letter

    return get_column_letter(n)


def prisma_rows(prisma: dict[str, Any], labels: dict[str, str]) -> list[list[Any]]:
    arms = prisma["arms"]
    keys = [arm for arm, _ in ARMS] + [a for a in arms if a not in dict(ARMS)]
    header = ["Count (reports)"] + [dict(ARMS).get(a, a) for a in keys] + ["Total"]
    rows: list[list[Any]] = [header]

    def line(label: str, key: str) -> None:
        rows.append([label] + [arms[a][key] for a in keys] + [prisma["total"][key]])

    line("Reports sought for retrieval", "sought")
    line("Reports not retrieved", "not_retrieved")
    for reason in sorted({k for a in keys for k in arms[a]["not_retrieved_reasons"]} | set(prisma["total"]["not_retrieved_reasons"])):
        rows.append([f"  not retrieved: {reason}"] + [arms[a]["not_retrieved_reasons"].get(reason, 0) for a in keys]
                    + [prisma["total"]["not_retrieved_reasons"].get(reason, 0)])
    line("Reports assessed for eligibility", "assessed")
    line("Reports excluded", "excluded")
    for code in sorted({k for a in keys for k in arms[a]["exclusion_reasons"]} | set(prisma["total"]["exclusion_reasons"])):
        word = labels.get(code, code)
        rows.append([f"  excluded: {code}" + (f" ({word})" if word != code else "")]
                    + [arms[a]["exclusion_reasons"].get(code, 0) for a in keys] + [prisma["total"]["exclusion_reasons"].get(code, 0)])
    line("Reports included", "included")
    rows.append([])
    rows.append(["Still open (not PRISMA counts)"])
    line("Awaiting retrieval", "awaiting_retrieval")
    line("Fetched, to confirm", "to_confirm")
    line("Retrieved, not assessed", "retrieved_not_assessed")
    line("Assessed without a retrieved full text", "assessed_without_full_text")
    if len(prisma["rounds"]) > 1:
        rows.append([])
        rows.append(["By round", "Round", "Sought", "Not retrieved", "Assessed", "Excluded", "Included"])
        for r in prisma["rounds"]:
            rows.append([r["label"], r["round"], r["sought"], r["not_retrieved"], r["assessed"], r["excluded"], r["included"]])
    return rows


def form_rows(form: dict[str, Any], amended: list[dict[str, Any]]) -> list[list[Any]]:
    rows: list[list[Any]] = [["Column", "Definition", "Type", "Options", "Required", "Column id"]]
    for c in form.get("columns") or []:
        rows.append([c["name"], c.get("definition") or "", c.get("type") or "", "; ".join(c.get("options") or []),
                     "Yes" if c.get("required") else "No", c["column_id"]])
    rows.append([])
    rows.append(["Amendments", "Date", "Changes", "Reason", "During the pilot"])
    if not amended:
        rows.append(["None recorded"])
    for n, a in enumerate(amended, start=1):
        rows.append([f"Amendment {n}", _date(a["at"]), "; ".join(a["changes"]), a.get("reason") or "", "Yes" if a["pilot"] else "No"])
    return rows


def _corpus_snapshot(ws: Path) -> str:
    path = ws / "audit" / "artifact_registry.json"
    try:
        artifacts = json.loads(path.read_text(encoding="utf-8")).get("artifacts") or {}
    except (OSError, ValueError):
        return "not recorded"
    corpora = sorted(
        ((k, e) for k, e in artifacts.items() if isinstance(e, dict) and e.get("artifact_type") == "corpus_snapshot"),
        key=lambda ke: str(ke[1].get("accepted_at") or ""),
    )
    if not corpora:
        return "not recorded"
    key, entry = corpora[-1]
    return f"{entry.get('artifact_id') or key} (accepted {_date(entry.get('accepted_at'))})"


def about_rows(ws: Path, view: dict[str, Any], exported_at: str) -> list[list[Any]]:
    from scholar_harness import __version__

    form = view.get("form") or {}
    counts = view["counts"]
    rows: list[list[Any]] = [["Item", "Value"]]
    rows.append(["Workspace", ws.name])
    rows.append(["Protocol fingerprint", form.get("protocol_fingerprint") or "not recorded"])
    rows.append(["Corpus snapshot", _corpus_snapshot(ws)])
    for source in view.get("rounds") or []:
        rows.append([f"Screening round {source['round']} ({dict(ARMS).get(source['arm'], source['arm'])})",
                     f"generation {source.get('generation_id') or 'not recorded'}, published {source.get('published_at') or 'not recorded'}"])
    rows.append(["Charting form version", form.get("version") or ""])
    rows.append(["Exported at", exported_at])
    rows.append(["App version", __version__])
    rows.append(["Rows in the Charting sheet", counts.get("kept", 0) - counts.get("excluded", 0)])
    rows.append(["Cells not charted yet", counts.get("cells_open", 0)])
    rows.append(["Required cells not charted yet", counts.get("required_open", 0)])
    rows.append(["Working export", "Changes after the export time are not in this file. Nothing here blocks: open cells are counted above."])
    rows.append(["Unit", "Counts are of reports; reports of the same study are not linked."])
    return rows


def methods_rows(block: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = [["Methods paragraph (draft: check every number before you submit)"]]
    rows.append([block["paragraph"]])
    rows.append([])
    rows.append(["Sentences"])
    rows += [[s] for s in block["sentences"]]
    if block["caveats"]:
        rows.append([])
        rows.append(["Notes"])
        rows += [[c] for c in block["caveats"]]
    if block["not_stated"]:
        rows.append([])
        rows.append(["Not stated"])
        rows += [[c] for c in block["not_stated"]]
    return rows


def xlsx(ws: Path, view: dict[str, Any], exported_at: str) -> bytes:
    """The workbook of record (h): Charting, Full text, PRISMA counts, Charting form, About, and Methods."""
    from openpyxl import Workbook

    from . import table as tb

    labels = {o["code"]: o["label"] for o in view.get("reason_options") or []}
    names = {c["column_id"]: c["name"] for c in (view.get("form") or {}).get("columns") or []}
    amended = amendment_list(fm.read_amendments(ws), names)
    block = methods(ws, view)
    book = Workbook()
    book.remove(book.active)
    _sheet(book, "Charting", tb.charting_rows(view))
    _sheet(book, "Full text", tb.fulltext_rows(view))
    _sheet(book, "PRISMA counts", prisma_rows(block["figures"]["prisma"], labels), widths={1: 48})
    _sheet(book, "Charting form", form_rows(view.get("form") or {}, amended), widths={1: 28, 2: 60, 3: 60})
    _sheet(book, "About", about_rows(ws, view, exported_at), widths={1: 34, 2: 90})
    _sheet(book, "Methods", methods_rows(block), widths={1: 120})
    # Fixed document dates, so the workbook's bytes depend on the data and the export time only.
    stamp = datetime.fromisoformat(exported_at).replace(tzinfo=None)
    book.properties.created = stamp
    book.properties.modified = stamp
    book.properties.creator = "Nexus Scholar"
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


# --------------------------------------------------------------------------- what the export writes beside the file


def write_prisma(ws: Path, prisma: dict[str, Any], exported_at: str) -> str:
    from scholar_harness.workspace.atomic import atomic_write_text

    path = ws / PRISMA_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, json.dumps({**prisma, "written_at": exported_at}, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    return PRISMA_FILE.as_posix()


def write_last_export(ws: Path, entry: dict[str, Any]) -> None:
    from scholar_harness.workspace.atomic import atomic_write_text

    path = ws / LAST_EXPORT_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, json.dumps(entry, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def last_export(ws: Path) -> dict[str, Any] | None:
    try:
        data = json.loads((Path(ws) / LAST_EXPORT_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
