"""M12a Part C: the spreadsheet, the PRISMA full-text counts, the methods block and the export journal.

The workspace is the published screening of ``tests/console/test_export_api.py`` with the
four charting columns of ``test_charting_form_api.py``; two records are kept (INCLUDE and
MAYBE). Offline: the suite's socket guard fails any outgoing connection.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

from scholar_harness.charting import report as rp
from scholar_harness.console import create_app

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_export_api_helpers_charting_c", _HERE / "test_export_api.py")
tea = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(tea)

TOKEN = "desk-token"
BASE = "/api/v1/charting"
WHO = "researcher:local"
MINI_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n" + b"x" * 2048
DIMENSIONS = [
    {"id": "sensor_problems", "name": "Sensor problems addressed", "description": "Misregistration, missing band",
     "data_type": "list", "required": True},
    {"id": "cameras", "name": "Cameras and evaluation design", "description": "Cameras, splits, cross-camera tests",
     "data_type": "free_text", "required": False},
    {"id": "n_images", "name": "Images", "description": "Number of images", "data_type": "numeric", "required": False},
    {"id": "split", "name": "Data split", "description": "How the data are split", "data_type": "categorical", "required": False},
]
SHEETS = ["Charting", "Full text", "PRISMA counts", "Charting form", "About", "Methods"]


@pytest.fixture
def env(tmp_path, monkeypatch):
    protocol = json.loads(tea.se.PROTOCOL.read_text(encoding="utf-8"))
    protocol["matrix_dimensions"] = DIMENSIONS
    with_columns = tmp_path / "protocol_with_columns.json"
    with_columns.write_text(json.dumps(protocol), encoding="utf-8")
    monkeypatch.setattr(tea.se, "PROTOCOL", with_columns)
    ws, ids = tea.published_workspace(tmp_path)
    app = create_app(ws, token=TOKEN)
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        yield client, ws, ids


def _event(study: str, kind: str, value, **extra) -> dict:
    return {"event_id": str(uuid.uuid4()), "study_id": study, "screener_id": WHO,
            "at": "2026-11-21T10:00:00Z", "kind": kind, "value": value, **extra}


def _cell(study: str, column: str, state, value=None, **extra) -> dict:
    return _event(study, "cell", {"column_id": column, "state": state, "value": value}, **extra)


def _post(client, *events) -> dict:
    response = client.post(f"{BASE}/events", json={"events": list(events)})
    assert response.status_code == 200, response.text
    results = response.json()["results"]
    assert all(r["result"] == "accepted" for r in results), results
    return response.json()


def _journal(ws: Path, action: str) -> list[dict]:
    rows = [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r for r in rows if r.get("action") == action]


def _charted_review(client, ids) -> dict:
    """One report not retrieved, decided Include and charted from its abstract; one retrieved and excluded.

    The pilot is on (Part B's default), one cell says Not reported, and one column is renamed after a
    value, which records an amendment. Returns the exclusion option used.
    """
    table = client.get(BASE).json()
    option = next(o for o in table["reason_options"] if o["kind"] == "exclusion")
    _post(client,
          _event(ids["included"], "fulltext_status", {"status": "not_retrieved", "reason": "no_access"}),
          _cell(ids["included"], "cameras", "value", "=HYPERLINK(\"http://x.test\",\"Sequoia\")"),
          _cell(ids["included"], "split", "not_reported"),
          _event(ids["unclear"], "fulltext_status", {"status": "retrieved"}))
    # Full-text decisions are made one study at a time (Part A).
    _post(client, _event(ids["included"], "fulltext_decision", {"outcome": "INCLUDE"}))
    _post(client, _event(ids["unclear"], "fulltext_decision", {"outcome": "EXCLUDE", "reason_code": option["code"]}))
    form = client.get(f"{BASE}/form").json()
    columns = form["columns"]
    columns[1]["name"] = "Cameras"
    renamed = client.put(f"{BASE}/form", json={"base_version": form["version"], "columns": columns, "reason": "Shorter name."})
    assert renamed.status_code == 200, renamed.text
    return option


# ------------------------------------------------------------------ DoD 15: the spreadsheet, read back


def test_the_spreadsheet_has_every_sheet_and_reads_back(env):
    client, ws, ids = env
    option = _charted_review(client, ids)
    response = client.get(f"{BASE}/export", params={"format": "xlsx"})
    assert response.status_code == 200
    assert response.headers["content-type"] == rp.XLSX_TYPE
    assert response.headers["content-disposition"].endswith('.xlsx"')
    book = load_workbook(io.BytesIO(response.content))
    assert book.sheetnames == SHEETS

    def rows(name: str) -> list[list]:
        return [[c for c in r] for r in book[name].iter_rows(values_only=True)]

    charting = rows("Charting")
    assert charting[0][:9] == ["study_id", "first_author", "year", "title", "doi", "round", "fulltext_status", "no_full_text", "pilot"]
    assert "Cameras" in charting[0] and "Cameras (note)" in charting[0] and "Cameras (where from)" in charting[0]
    assert [r[0] for r in charting[1:]] == [ids["included"]], "the report excluded at full text is not charted"
    line = dict(zip(charting[0], charting[1], strict=True))
    assert line["fulltext_status"] == "Not retrieved" and line["no_full_text"] == "No full text" and line["pilot"] == "Pilot"
    assert line["Data split"] == "Not reported" and line["Images"] is None  # not charted: empty in the file

    fulltext = rows("Full text")
    assert fulltext[0][-4:] == ["file_origin", "file_source", "file_version", "file_licence"]
    by_id = {r[0]: dict(zip(fulltext[0], r, strict=True)) for r in fulltext[1:]}
    assert by_id[ids["unclear"]]["ft_decision"] == "Exclude" and by_id[ids["unclear"]]["ft_reason"] == option["code"]
    assert by_id[ids["included"]]["not_retrieved_reason"] == "No access or paywalled"

    prisma = {r[0]: r[1:] for r in rows("PRISMA counts") if r and r[0]}
    assert prisma["Count (reports)"] == ["Databases", "Citation chasing", "Total"]
    assert list(prisma["Reports sought for retrieval"]) == [2, 0, 2]
    assert list(prisma["Reports not retrieved"]) == [1, 0, 1]
    assert list(prisma["  not retrieved: No access or paywalled"]) == [1, 0, 1]
    # The report not retrieved and decided from its abstract stays under "not retrieved" (review, finding 1).
    assert list(prisma["Reports assessed for eligibility"]) == [1, 0, 1]
    assert list(prisma["Reports excluded"]) == [1, 0, 1]
    assert list(prisma["Reports included"]) == [0, 0, 0]
    assert list(prisma["Decided from the abstract"]) == [1, 0, 1] and list(prisma["  included"]) == [1, 0, 1]
    assert any(k.startswith(f"  excluded: {option['code']}") for k in prisma)

    form = rows("Charting form")
    assert form[0] == ["Column", "Definition", "Type", "Options", "Required", "Column id"]
    assert [r[0] for r in form[1:5]] == ["Sensor problems addressed", "Cameras", "Images", "Data split"]
    amendment = next(r for r in form if r[0] == "Amendment 1")
    assert amendment[2] == 'renamed "Cameras and evaluation design" to "Cameras"' and amendment[3] == "Shorter name."
    assert amendment[4] == "Yes", "made during the pilot"

    about = {r[0]: r[1] for r in rows("About")[1:]}
    for key in ("Workspace", "Protocol fingerprint", "Corpus snapshot", "Exported at", "App version", "Working export",
                "Cells not charted yet", "Required cells not charted yet", "Unit"):
        assert key in about, key
    assert about["Workspace"] == ws.name and about["Cells not charted yet"] == 2 and about["Required cells not charted yet"] == 1
    assert any(k.startswith("Screening round 1") for k in about)

    methods = rows("Methods")
    assert methods[1][0] == client.get(f"{BASE}/methods").json()["paragraph"]


def test_every_text_cell_is_text_never_a_formula(env):
    """A value from a record or a cell that starts with "=" is written as text (formula injection)."""
    client, _ws, ids = env
    _charted_review(client, ids)
    book = load_workbook(io.BytesIO(client.get(f"{BASE}/export", params={"format": "xlsx"}).content))
    sheet = book["Charting"]
    header = [c.value for c in sheet[1]]
    cell = sheet.cell(row=2, column=header.index("Cameras") + 1)
    assert cell.value == '=HYPERLINK("http://x.test","Sequoia")' and cell.data_type == "s"
    assert all(c.data_type != "f" for name in SHEETS for r in book[name].iter_rows() for c in r)


def test_the_full_text_csv_says_where_the_file_came_from(env):
    client, _ws, ids = env
    attached = client.post(f"{BASE}/records/{ids['included']}/attachment", content=MINI_PDF,
                           headers={"content-type": "application/pdf"}, params={"name": "paper.pdf"})
    assert attached.status_code == 200, attached.text
    body = client.get(f"{BASE}/export", params={"format": "csv", "view": "fulltext"}).content.decode("utf-8-sig")
    header, *lines = [line.split(",") for line in body.strip().split("\r\n")]
    assert header[-4:] == ["file_origin", "file_source", "file_version", "file_licence"]
    by_id = {line[0]: dict(zip(header, line, strict=True)) for line in lines}
    assert by_id[ids["included"]]["file_origin"] == "Attached" and by_id[ids["included"]]["file_source"] == ""
    assert by_id[ids["unclear"]]["file_origin"] == ""


def test_a_format_other_than_csv_or_xlsx_is_refused_and_writes_nothing(env):
    client, ws, _ids = env
    for params in ({"format": "ods"}, {"format": "csv", "view": "form"}):
        bad = client.get(f"{BASE}/export", params=params)
        assert bad.status_code == 422 and bad.json()["detail"]["code"] == "CHARTING_EXPORT_FORMAT_INVALID"
    assert not _journal(ws, "CHARTING_EXPORTED")
    assert not (ws / rp.PRISMA_FILE).exists() and not (ws / rp.LAST_EXPORT_FILE).exists()


# ------------------------------------------------------------------ DoD 16: the PRISMA full-text counts


def test_the_prisma_full_text_counts_are_written_and_screenings_report_is_unchanged(env):
    client, ws, ids = env
    option = _charted_review(client, ids)
    screening_report = ws / "literature" / "prisma_report.json"
    before = screening_report.read_bytes()
    client.get(f"{BASE}/export", params={"format": "csv", "view": "charting"})
    written = json.loads((ws / rp.PRISMA_FILE).read_text(encoding="utf-8"))
    assert written["schema"] == rp.PRISMA_SCHEMA and written["unit"] == "reports"
    total = written["total"]
    assert (total["sought"], total["not_retrieved"], total["assessed"], total["excluded"], total["included"]) == (2, 1, 1, 1, 0)
    assert (total["not_retrieved_decided"], total["not_retrieved_included"], total["not_retrieved_excluded"]) == (1, 1, 0)
    assert total["not_retrieved_reasons"] == {"No access or paywalled": 1}
    assert total["exclusion_reasons"] == {option["code"]: 1}
    assert total["assessed_without_full_text"] == 0, "a report not retrieved is never counted as assessed"
    assert total["sought"] == total["not_retrieved"] + total["assessed"] + total["awaiting_retrieval"] + total["retrieved_not_assessed"]
    assert written["arms"]["databases"]["sought"] == 2 and written["arms"]["citation_searching"]["sought"] == 0
    assert [r["round"] for r in written["rounds"]] == [1] and written["rounds"][0]["label"] == "Databases"
    assert screening_report.read_bytes() == before


def test_a_waiting_or_open_report_is_counted_apart_so_the_counts_add_up():
    view = {"rounds": [{"round": 1, "arm": "databases"}, {"round": 2, "arm": "citation_searching"}], "rows": [
        _view_row("A", 1, "databases", "to_get"),
        _view_row("B", 1, "databases", "requested", pending=True),
        _view_row("C", 2, "citation_searching", "retrieved"),
        _view_row("D", 2, "citation_searching", "retrieved", decision={"outcome": "INCLUDE"}),
        {**_view_row("E", 2, "citation_searching", "retrieved"), "kept": False},
        # Review of Part C, finding 1: not retrieved and decided from the abstract; and finding 3: a copy
        # waiting on a Not retrieved row, and a decision taken before the full text came (To get).
        _view_row("F", 1, "databases", "not_retrieved", decision={"outcome": "EXCLUDE", "reason_code": "EXC-1"}),
        _view_row("G", 1, "databases", "not_retrieved", pending=True),
        _view_row("H", 1, "databases", "to_get", decision={"outcome": "INCLUDE"}),
    ]}
    counts = rp.prisma_fulltext(view)
    total = counts["total"]
    assert total["sought"] == 7, "a record no longer kept is not sought"
    assert (total["awaiting_retrieval"], total["to_confirm"], total["retrieved_not_assessed"], total["assessed"]) == (2, 2, 1, 2)
    assert (total["not_retrieved"], total["not_retrieved_decided"], total["not_retrieved_excluded"]) == (2, 1, 1)
    assert total["exclusion_reasons"] == {}, "an exclusion of a report not retrieved is not a PRISMA exclusion"
    assert total["assessed_without_full_text"] == 1
    assert total["sought"] == total["not_retrieved"] + total["assessed"] + total["awaiting_retrieval"] + total["retrieved_not_assessed"]
    assert counts["arms"]["citation_searching"]["included"] == 1 and counts["arms"]["databases"]["sought"] == 5
    assert [r["label"] for r in counts["rounds"]] == ["Databases", "Citation chasing"]


def _view_row(sid: str, number: int, arm: str, status: str, *, pending: bool = False, decision=None, attachment=None,
              discarded=None, cells=None) -> dict:
    return {"study_id": sid, "round": number, "arm": arm, "kept": True, "ft_decision": decision, "cells": cells or {},
            "fulltext": {"status": status, "reason": None, "pending_fetch": {"manifest_row": "M"} if pending else None,
                         "attachment": attachment, "discarded_fetch": discarded}}


# ------------------------------------------------------------------ DoD 17: the methods block


def test_the_methods_block_states_every_number_from_the_events(env):
    client, ws, ids = env
    option = _charted_review(client, ids)
    journal_before = (ws / "audit" / "journal.jsonl").read_bytes()
    block = client.get(f"{BASE}/methods").json()
    amended_on = json.loads((ws / "charting" / "form_amendments.jsonl").read_text(encoding="utf-8").splitlines()[0])["amended_at"][:10]
    assert block["sentences"] == [
        "Of 2 reports sought for retrieval, 1 was not retrieved (No access or paywalled: 1).",
        f"1 report was assessed at full text by one reviewer; 1 was excluded ({option['label']} ({option['code']}): 1) "
        "and 0 were included.",
        "1 report not retrieved was decided from the abstract: 1 was included and 0 were excluded.",
        f'Data were charted by one reviewer using a form piloted on 1 study and revised on {amended_on} '
        '(renamed "Cameras and evaluation design" to "Cameras": Shorter name.).',
        "'Not reported' was recorded when a study did not report an item.",
        "1 study was charted from the abstract only because no full text was retrieved.",
        "The counts are of reports; reports of the same study were not linked.",
    ]
    assert block["paragraph"] == " ".join(block["sentences"])
    assert "The pilot of the charting form has not been ended." in block["caveats"]
    assert not any("before a full text was retrieved" in c for c in block["caveats"])
    assert "2 cells are not charted yet; 1 in a required column." in block["caveats"]
    assert block["figures"]["reviewers"] == {"fulltext_decisions": 1, "charting": 1}
    listed = {s["path"]: s["digest"] for s in block["sources"]}
    assert {"charting/form.json", "charting/form_amendments.jsonl", "literature/included.json"} <= set(listed)
    assert any(p.startswith("charting/events/") for p in listed)
    import hashlib as _h

    assert listed["charting/form.json"] == "sha256:" + _h.sha256((ws / "charting" / "form.json").read_bytes()).hexdigest()
    # A pure read: no journal row, no file.
    assert (ws / "audit" / "journal.jsonl").read_bytes() == journal_before
    assert not (ws / rp.PRISMA_FILE).exists()


def test_the_open_access_sentence_names_the_services_asked_and_the_discards(tmp_path):
    ws = tmp_path / "ws"
    (ws / "audit").mkdir(parents=True)
    rows = [{"action": "CHARTING_FETCH_STARTED", "parameters": {"providers": ["unpaywall", "openalex"]}},
            {"action": "CHARTING_FETCH_STARTED", "parameters": {"providers": ["unpaywall", "arxiv"]}}]
    (ws / "audit" / "journal.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    fetched = {"origin": "fetched", "source": "Unpaywall", "version_label": "published", "licence": "cc-by"}
    view = {"rounds": [{"round": 1, "arm": "databases"}], "reason_options": [], "form": {"columns": []},
            "counts": {"pilot": 0, "cells_open": 0, "required_open": 0, "charted": 0, "not_charted": 0},
            "rows": [
                _view_row("A", 1, "databases", "retrieved", attachment=fetched),
                _view_row("B", 1, "databases", "retrieved", attachment=fetched),
                _view_row("C", 1, "databases", "to_get", discarded={"reason": "wrong_paper"}),
            ]}
    block = rp.methods(ws, view)
    assert ("Open-access copies of 2 reports were located with Unpaywall, OpenAlex and arXiv and each was checked "
            "by the reviewer before use; 1 was discarded (the wrong paper: 1).") in block["sentences"]
    assert block["figures"]["open_access"] == {"used": 2, "discarded": 1, "services": ["Unpaywall", "OpenAlex", "arXiv"]}


def test_amendments_are_listed_in_words():
    names = {"a": "Alpha", "b": "Beta"}
    rows = [
        {"amendment_id": "x", "amended_at": "2026-11-21T10:00:00Z", "reason": "One.", "pilot": True,
         "change": "definition", "column_id": "a", "from": "old words", "to": "new words"},
        {"amendment_id": "x", "amended_at": "2026-11-21T10:00:00Z", "reason": "One.", "pilot": True,
         "change": "required", "column_id": "b", "from": False, "to": True},
        {"amendment_id": "y", "amended_at": "2026-11-22T09:00:00Z", "reason": "Two.", "pilot": False,
         "change": "split", "column_id": "a", "from": "Alpha", "to": ["A1", "A2"]},
        {"amendment_id": "z", "amended_at": "2026-11-22T09:30:00Z", "reason": None, "pilot": False,
         "change": "merged", "column_id": "c", "from": ["A1", "A2"], "to": "Alpha"},
    ]
    listed = rp.amendment_list(rows, names)
    assert [a["changes"] for a in listed] == [
        ['changed the definition of "Alpha"', 'made "Beta" required'],
        ['split "Alpha" into "A1" and "A2"'],
        ['merged "A1" and "A2" into "Alpha"'],
    ]
    assert [a["pilot"] for a in listed] == [True, False, False]


# ------------------------------------------------------------------ DoD 18: every export journaled; the screen's last export


def test_every_export_is_journaled_with_its_hash_and_the_table_shows_the_last(env):
    client, ws, ids = env
    _charted_review(client, ids)
    assert client.get(BASE).json()["last_export"] is None
    answers = [client.get(f"{BASE}/export", params=p) for p in
               ({"format": "csv", "view": "fulltext"}, {"format": "csv", "view": "charting"}, {"format": "xlsx"})]
    rows = _journal(ws, "CHARTING_EXPORTED")
    assert [r["parameters"]["format"] for r in rows] == ["csv", "csv", "xlsx"]
    assert [r["parameters"]["sha256"] for r in rows] == [hashlib.sha256(a.content).hexdigest() for a in answers]
    assert rows[-1]["metrics"] == {"rows": 1, "not_charted": 1, "cells_open": 2, "required_open": 1}
    assert rows[-1]["outputs"] == [rp.PRISMA_FILE.as_posix()]
    last = client.get(BASE).json()["last_export"]
    assert last["format"] == "xlsx" and last["rows"] == 1 and last["sha256"] == rows[-1]["parameters"]["sha256"]
    assert last["cells_open"] == 2 and last["required_open"] == 1 and last["at"]


def test_the_table_counts_open_and_required_cells(env):
    client, _ws, ids = env
    counts = client.get(BASE).json()["counts"]
    assert (counts["cells_open"], counts["required_open"]) == (8, 2), "two rows, four columns, one required"
    _post(client, _cell(ids["included"], "cameras", "value", "Sequoia"))
    counts = client.get(BASE).json()["counts"]
    assert (counts["cells_open"], counts["required_open"]) == (7, 2)


def test_the_methods_block_on_a_table_never_opened_writes_nothing(env):
    """Review of Part C, finding 2: the first read is /methods; no form is seeded, no history kept, no journal row."""
    client, ws, _ids = env
    journal = (ws / "audit" / "journal.jsonl").read_bytes()
    charting_before = sorted(p.relative_to(ws).as_posix() for p in (ws / "charting").rglob("*")) if (ws / "charting").exists() else []
    answer = client.get(f"{BASE}/methods")
    assert answer.status_code == 200
    assert answer.json()["sentences"][0] == "Of 2 reports sought for retrieval, none is recorded as not retrieved."
    assert (ws / "audit" / "journal.jsonl").read_bytes() == journal
    charting_after = sorted(p.relative_to(ws).as_posix() for p in (ws / "charting").rglob("*")) if (ws / "charting").exists() else []
    assert charting_after == charting_before
    assert not (ws / "charting" / "form.json").exists()
