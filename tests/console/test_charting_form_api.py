"""M12a Part B: the charting form beside the protocol, cells, pilot and amendments (DoD 10 to 13).

The workspace is the published screening of ``tests/console/test_export_api.py``
under a protocol that names four charting columns (one per protocol data
type). Two records are kept (one Include, one Unclear). Offline.
"""

from __future__ import annotations

import importlib.util
import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scholar_harness.charting import events as cev
from scholar_harness.console import create_app
from scholar_harness.console.browser import POST_PATHS, PUT_PATHS

_SPEC = importlib.util.spec_from_file_location(
    "_export_api_helpers_charting_form", Path(__file__).resolve().parent / "test_export_api.py"
)
tea = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(tea)

TOKEN = "desk-token"
BASE = "/api/v1/charting"
WHO = "researcher:local"
DIMENSIONS = [
    {"id": "sensor_problems", "name": "Sensor problems addressed", "description": "Misregistration, missing band, change of camera",
     "data_type": "list", "required": True},
    {"id": "cameras", "name": "Cameras and evaluation design", "description": "Cameras, splits, cross-camera tests",
     "data_type": "free_text", "required": False},
    {"id": "n_images", "name": "Images", "description": "Number of images", "data_type": "numeric", "required": False},
    {"id": "split", "name": "Data split", "description": "How the data are split", "data_type": "categorical", "required": False},
]


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


def _cell(study: str, column: str, state, value=None, **extra) -> dict:
    return {"event_id": str(uuid.uuid4()), "study_id": study, "screener_id": WHO, "at": "2026-11-21T10:00:00Z",
            "kind": "cell", "value": {"column_id": column, "state": state, "value": value}, **extra}


def _post(client, *events) -> dict:
    response = client.post(f"{BASE}/events", json={"events": list(events)})
    assert response.status_code == 200, response.text
    return response.json()


def _journal(ws: Path, action: str) -> list[dict]:
    rows = [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r for r in rows if r.get("action") == action]


def _row(client, study: str) -> dict:
    return next(r for r in client.get(BASE).json()["rows"] if r["study_id"] == study)


def _form(client) -> dict:
    return client.get(f"{BASE}/form").json()


def _put(client, columns, *, reason=None, base=None):
    form = _form(client)
    return client.put(f"{BASE}/form", json={"base_version": form["version"] if base is None else base,
                                             "columns": columns, "reason": reason})


# ------------------------------------------------------------------ DoD 10: seeded once, protocol untouched


def test_the_form_is_seeded_once_from_the_protocol_and_the_protocol_is_never_written(env):
    client, ws, _ = env
    before = (ws / "protocol.json").read_bytes()
    table = client.get(BASE).json()
    form = table["form"]
    assert form["version"] == 1 and form["pilot"]["on"] is True and form["has_values"] is False
    assert [(c["column_id"], c["type"], c["required"]) for c in form["columns"]] == [
        ("sensor_problems", "several", True), ("cameras", "text", False), ("n_images", "number", False), ("split", "one", False)]
    assert form["columns"][0]["definition"] == DIMENSIONS[0]["description"]
    client.get(BASE)
    client.get(f"{BASE}/form")
    assert len(_journal(ws, "CHARTING_FORM_CREATED")) == 1
    assert (ws / "protocol.json").read_bytes() == before


def test_a_protocol_without_columns_seeds_an_empty_form(tmp_path):
    ws, _ = tea.published_workspace(tmp_path)
    with TestClient(create_app(ws, token=TOKEN), base_url="http://127.0.0.1",
                    headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        form = client.get(f"{BASE}/form").json()
    assert form["columns"] == [] and form["version"] == 1


# ------------------------------------------------------------------ DoD 11: cells of five types


def _with_options(client):
    columns = _form(client)["columns"]
    columns[0]["options"] = ["Misregistration", "Missing band", "Change of camera"]
    columns[3]["options"] = ["Random tiles", "By field", "By date", "By camera"]
    columns.append({"column_id": "cross_camera", "name": "Test camera absent from training", "definition": "",
                    "type": "yes_no", "options": [], "required": False})
    assert _put(client, columns).status_code == 200  # no value yet: free
    return columns


def test_cells_of_every_type_with_not_reported_not_applicable_note_and_where_from(env):
    client, ws, ids = env
    _with_options(client)
    study = ids["included"]
    result = _post(client,
                   _cell(study, "sensor_problems", "value", ["Misregistration", "Change of camera"]),
                   _cell(study, "cameras", "value", "RedEdge-M and Sequoia", note="One model per camera", where_from="Methods, p. 4"),
                   _cell(study, "n_images", "value", 1260),
                   _cell(study, "split", "not_reported"),
                   _cell(study, "cross_camera", "value", "No"))
    assert [r["result"] for r in result["results"]] == ["accepted"] * 5
    cells = _row(client, study)["cells"]
    assert cells["sensor_problems"]["value"] == ["Misregistration", "Change of camera"]
    assert (cells["cameras"]["note"], cells["cameras"]["where_from"]) == ("One model per camera", "Methods, p. 4")
    assert cells["n_images"]["value"] == 1260 and cells["split"]["state"] == "not_reported"
    assert cells["cross_camera"]["value"] == "No"
    assert all(c["pilot"] for c in cells.values())  # the pilot is on at first visit
    stored = [json.loads(line) for line in cev.screener_file(ws, WHO).read_text(encoding="utf-8").splitlines()]
    assert {e["binding"]["form_version"] for e in stored} == {2} and all(e["pilot"] for e in stored)
    na = _post(client, _cell(ids["unclear"], "n_images", "not_applicable"))
    assert na["rows"][0]["cells"]["n_images"]["state"] == "not_applicable"


@pytest.mark.parametrize(("column", "state", "value", "code"), [
    ("sensor_problems", "value", ["Not an option"], "CHARTING_VALUE_INVALID"),
    ("sensor_problems", "value", [], "CHARTING_VALUE_INVALID"),
    ("split", "value", "By planet", "CHARTING_VALUE_INVALID"),
    ("n_images", "value", "many", "CHARTING_VALUE_INVALID"),
    ("n_images", "value", True, "CHARTING_VALUE_INVALID"),
    ("cross_camera", "value", "Maybe", "CHARTING_VALUE_INVALID"),
    ("cameras", "value", "   ", "CHARTING_VALUE_INVALID"),
    ("no_such_column", "value", "x", "CHARTING_COLUMN_UNKNOWN"),
    ("split", "not_reported", "By date", "BODY_INVALID"),
    ("split", "guessed", None, "BODY_INVALID"),
    ("sensor_problems", "value", [{"x": 1}], "CHARTING_VALUE_INVALID"),  # review of Part B, finding 2
    ("sensor_problems", "value", [["Misregistration"]], "CHARTING_VALUE_INVALID"),
    ("n_images", "value", 10**400, "CHARTING_VALUE_INVALID"),
])
def test_a_value_that_does_not_fit_its_column_is_refused(env, column, state, value, code):
    client, ws, ids = env
    _with_options(client)
    result = _post(client, _cell(ids["included"], column, state, value))
    assert result["results"][0]["refusal"]["code"] == code
    assert not cev.screener_file(ws, WHO).exists()


def test_where_from_goes_only_with_a_cell(env):
    client, _, ids = env
    event = {"event_id": str(uuid.uuid4()), "study_id": ids["included"], "screener_id": WHO, "at": "2026-11-21T10:00:00Z",
             "kind": "fulltext_status", "value": {"status": "retrieved"}, "where_from": "p. 3"}
    assert _post(client, event)["results"][0]["refusal"]["code"] == "BODY_INVALID"


def test_undo_of_a_cell_follows_its_own_column(env):
    client, _, ids = env
    first = _cell(ids["included"], "cameras", "value", "Sequoia")
    other = _cell(ids["included"], "n_images", "value", 10)
    _post(client, first, other)
    wrong_column = _cell(ids["included"], "n_images", None, None, supersedes=first["event_id"])
    assert _post(client, wrong_column)["results"][0]["refusal"]["code"] == "BODY_INVALID"
    undo = _cell(ids["included"], "cameras", None, None, supersedes=first["event_id"])
    cells = _post(client, undo)["rows"][0]["cells"]
    assert cells["cameras"]["state"] is None and cells["n_images"]["value"] == 10


# ------------------------------------------------------------------ DoD 12: amendments


def test_a_change_before_any_value_is_free_and_journaled(env):
    client, ws, _ = env
    columns = _form(client)["columns"]
    columns[1]["name"] = "Cameras"
    response = _put(client, columns)
    assert response.status_code == 200 and response.json()["version"] == 2
    assert len(_journal(ws, "CHARTING_FORM_CHANGED")) == 1
    assert not (ws / "charting" / "form_amendments.jsonl").exists()


def test_after_a_value_a_change_needs_a_reason_and_is_recorded(env):
    client, ws, ids = env
    _post(client, _cell(ids["included"], "cameras", "value", "Sequoia"))
    columns = _form(client)["columns"]
    columns[1]["name"] = "Cameras"
    refused = _put(client, columns)
    assert refused.status_code == 422 and refused.json()["detail"]["code"] == "CHARTING_AMENDMENT_REASON_REQUIRED"
    stale = _put(client, columns, reason="Shorter name.", base=0)
    assert stale.status_code == 409 and stale.json()["detail"]["code"] == "CHARTING_FORM_STALE"
    ok = _put(client, columns, reason="Shorter name.")
    assert ok.status_code == 200
    rows = [json.loads(line) for line in (ws / "charting" / "form_amendments.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1 and rows[0]["change"] == "renamed" and rows[0]["reason"] == "Shorter name."
    assert rows[0]["pilot"] is True and rows[0]["amended_by"] == WHO
    assert rows[0]["from"] == "Cameras and evaluation design" and rows[0]["to"] == "Cameras"
    assert {"protocol_fingerprint", "generation_id", "form_version_from", "form_version_to"} <= set(rows[0])
    assert len(_journal(ws, "CHARTING_FORM_AMENDED")) == 1
    cell = _row(client, ids["included"])["cells"]["cameras"]
    assert cell["value"] == "Sequoia" and cell["chart_again"] is False  # a rename keeps its values


def test_a_changed_type_or_a_removed_option_marks_chart_again_and_keeps_the_history(env):
    client, _, ids = env
    columns = _with_options(client)
    study, other = ids["included"], ids["unclear"]
    _post(client, _cell(study, "split", "value", "By date"), _cell(other, "split", "value", "By field"),
          _cell(study, "cameras", "value", "Sequoia"))
    columns = _form(client)["columns"]
    columns[3]["options"] = ["Random tiles", "By field", "By camera"]  # "By date" removed
    columns[1]["type"] = "one"
    columns[1]["options"] = ["One camera", "Several cameras"]
    assert _put(client, columns, reason="Split and cameras become countable.").status_code == 200
    a, b = _row(client, study)["cells"], _row(client, other)["cells"]
    assert a["split"]["chart_again"] is True and a["split"]["value"] == "By date"
    assert b["split"]["chart_again"] is False  # its option still exists
    assert a["cameras"]["chart_again"] is True
    again = _post(client, _cell(study, "split", "value", "By camera", supersedes=a["split"]["event_id"]))
    cell = again["rows"][0]["cells"]["split"]
    assert cell["chart_again"] is False and cell["history"][-1]["value"] == "By date"


def test_a_split_marks_the_new_columns_with_the_earlier_value_as_history(env):
    client, ws, ids = env
    _post(client, _cell(ids["included"], "cameras", "value", "RedEdge-M; no cross-camera test; tiles"))
    columns = [c for c in _form(client)["columns"] if c["column_id"] != "cameras"]
    columns += [
        {"column_id": "camera_models", "name": "Cameras", "definition": "", "type": "text", "options": [],
         "required": False, "derived_from": ["cameras"]},
        {"column_id": "cross_test", "name": "Test camera absent from training", "definition": "", "type": "yes_no",
         "options": [], "required": False, "derived_from": ["cameras"]},
    ]
    assert _put(client, columns, reason="One value per question makes the table countable.").status_code == 200
    rows = [json.loads(line) for line in (ws / "charting" / "form_amendments.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["change"] for r in rows] == ["split"]
    cells = _row(client, ids["included"])["cells"]
    for cid in ("camera_models", "cross_test"):
        assert cells[cid]["chart_again"] is True and cells[cid]["state"] is None
        assert cells[cid]["history"][-1]["value"] == "RedEdge-M; no cross-camera test; tiles"
        assert cells[cid]["history"][-1]["column"] == "Cameras and evaluation design"
    assert (ws / "charting" / "events").is_dir()  # the old column's cell is kept in the log


def _split_cameras(client):
    columns = [c for c in _form(client)["columns"] if c["column_id"] != "cameras"]
    columns += [
        {"column_id": "camera_models", "name": "Cameras", "definition": "", "type": "text", "options": [],
         "required": False, "derived_from": ["cameras"]},
        {"column_id": "cross_test", "name": "Test camera absent from training", "definition": "", "type": "yes_no",
         "options": [], "required": False, "derived_from": ["cameras"]},
    ]
    return columns


def test_after_a_split_the_form_still_saves_and_the_split_history_stays(env):
    """Review of Part B, finding 1: the new columns keep naming their source, and later saves pass."""
    client, ws, ids = env
    _post(client, _cell(ids["included"], "cameras", "value", "RedEdge-M"))
    assert _put(client, _split_cameras(client), reason="One value per question.").status_code == 200
    columns = _form(client)["columns"]
    assert next(c for c in columns if c["column_id"] == "camera_models")["derived_from"] == ["cameras"]
    next(c for c in columns if c["column_id"] == "camera_models")["name"] = "Camera models"
    renamed = _put(client, columns, reason="Clearer name.")
    assert renamed.status_code == 200, renamed.text
    cell = _row(client, ids["included"])["cells"]["camera_models"]
    assert cell["chart_again"] is True and cell["history"][-1]["value"] == "RedEdge-M"
    columns = _form(client)["columns"]
    columns.append({"column_id": "orphan", "name": "Orphan", "definition": "", "type": "text", "options": [],
                    "required": False, "derived_from": ["cameras"]})  # a new column may not name a column that is gone
    refused = _put(client, columns, reason="x")
    assert refused.status_code == 422 and refused.json()["detail"]["code"] == "BODY_INVALID"


def test_a_free_split_before_any_value_also_keeps_saving(env):
    client, _, _ = env
    assert _put(client, _split_cameras(client)).status_code == 200
    columns = _form(client)["columns"]
    columns[0]["name"] = "Sensor problems"
    assert _put(client, columns).status_code == 200


def test_a_replaced_column_and_a_merge_are_recorded_and_mark_chart_again(env):
    """Review of Part B, finding 5: replacement and merge are tested on the real engine."""
    client, ws, ids = env
    study = ids["included"]
    _post(client, _cell(study, "cameras", "value", "Sequoia"), _cell(study, "n_images", "value", 1260),
          _cell(study, "split", "not_reported"))
    columns = [c for c in _form(client)["columns"] if c["column_id"] != "cameras"]
    columns.append({"column_id": "camera_list", "name": "Cameras used", "definition": "", "type": "text",
                    "options": [], "required": False, "derived_from": ["cameras"]})
    assert _put(client, columns, reason="One column for the cameras.").status_code == 200
    columns = [c for c in _form(client)["columns"] if c["column_id"] not in ("n_images", "split")]
    columns.append({"column_id": "data", "name": "Images and split", "definition": "", "type": "text",
                    "options": [], "required": False, "derived_from": ["n_images", "split"]})
    assert _put(client, columns, reason="Size and split read together.").status_code == 200
    rows = [json.loads(line) for line in (ws / "charting" / "form_amendments.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["change"] for r in rows] == ["replaced", "merged"]
    assert rows[1]["from"] == ["Images", "Data split"] and rows[1]["columns"] == ["n_images", "split"]
    cells = _row(client, study)["cells"]
    assert cells["camera_list"]["chart_again"] is True and cells["camera_list"]["history"][-1]["value"] == "Sequoia"
    merged = cells["data"]
    assert merged["chart_again"] is True
    assert {h["column"] for h in merged["history"]} == {"Images", "Data split"}


def test_a_form_file_this_version_cannot_read_is_refused_and_kept(env):
    """Review of Part B, finding 8: never seeded over."""
    client, ws, _ = env
    client.get(BASE)
    path = ws / "charting" / "form.json"
    path.write_text(json.dumps({"schema": "nexus.charting-form.v9", "columns": []}), encoding="utf-8")
    response = client.get(BASE)
    assert response.status_code == 409 and response.json()["detail"]["code"] == "CHARTING_FORM_STALE"
    assert json.loads(path.read_text(encoding="utf-8"))["schema"] == "nexus.charting-form.v9"


def test_a_form_save_whose_journal_row_fails_changes_nothing(env, monkeypatch):
    """Review of Part B, finding 7: the amendment rows, the form and its journal row together or not at all."""
    client, ws, ids = env
    _post(client, _cell(ids["included"], "cameras", "value", "Sequoia"))
    before = (ws / "charting" / "form.json").read_bytes()
    from scholar_harness.charting import form as fm

    def broken(*args, **kwargs):
        raise OSError("the journal cannot be written")

    monkeypatch.setattr(fm, "append_event", broken)
    columns = _form(client)["columns"]
    columns[1]["name"] = "Cameras"
    response = _put(client, columns, reason="Shorter.")
    assert response.status_code == 503 and response.json()["detail"]["code"] == "ATOMIC_COMMIT_FAILED"
    assert (ws / "charting" / "form.json").read_bytes() == before
    assert not (ws / "charting" / "form_amendments.jsonl").exists()


# ------------------------------------------------------------------ DoD 13: pilot


def test_end_pilot_is_recorded_once_and_later_cells_are_not_pilot(env):
    client, ws, ids = env
    _post(client, _cell(ids["included"], "cameras", "value", "Sequoia"))
    form = _form(client)
    ended = client.post(f"{BASE}/form/pilot/end", json={"base_version": form["version"]})
    assert ended.status_code == 200 and ended.json()["pilot"]["on"] is False
    client.post(f"{BASE}/form/pilot/end", json={"base_version": form["version"]})
    assert len(_journal(ws, "CHARTING_PILOT_ENDED")) == 1
    _post(client, _cell(ids["unclear"], "cameras", "value", "RedEdge-M"))
    assert _row(client, ids["included"])["cells"]["cameras"]["pilot"] is True  # kept as final
    assert _row(client, ids["unclear"])["cells"]["cameras"]["pilot"] is False
    assert client.get(BASE).json()["counts"]["pilot"] == 1


# ------------------------------------------------------------------ counts, CSV, allow-lists


def test_a_row_is_charted_when_every_column_is_filled_and_an_excluded_row_is_not_counted(env):
    client, _, ids = env
    study = ids["included"]
    _post(client, *[_cell(study, c, "not_reported") for c in ("sensor_problems", "cameras", "n_images", "split")])
    table = client.get(BASE).json()
    assert table["counts"]["charted"] == 1 and table["counts"]["not_charted"] == 1
    assert _row(client, study)["no_full_text"] is True
    _post(client, {"event_id": str(uuid.uuid4()), "study_id": ids["unclear"], "screener_id": WHO, "at": "2026-11-21T10:00:00Z",
                   "kind": "fulltext_decision", "value": {"outcome": "EXCLUDE", "reason_code": ids["code"]}})
    assert client.get(BASE).json()["counts"]["not_charted"] == 0


def test_the_charting_csv_writes_words_for_not_reported_and_leaves_uncharted_cells_empty(env):
    client, ws, ids = env
    _post(client, _cell(ids["included"], "cameras", "value", "Sequoia", note="n", where_from="p. 2"),
          _cell(ids["included"], "n_images", "not_reported"), _cell(ids["included"], "split", "not_applicable"))
    response = client.get(f"{BASE}/export", params={"format": "csv", "view": "charting"})
    assert response.status_code == 200 and response.content.startswith(b"\xef\xbb\xbf")
    text = response.content.decode("utf-8-sig")
    lines = text.split("\r\n")
    header = lines[0].split(",")
    assert header[:9] == ["study_id", "first_author", "year", "title", "doi", "round", "fulltext_status", "no_full_text", "pilot"]
    assert "Cameras and evaluation design (where from)" in lines[0]
    row = next(line for line in lines if line.startswith(ids["included"]))
    assert "Sequoia,n,p. 2" in row and "Not reported" in row and "Not applicable" in row and "No full text" in row
    import csv
    import io

    parsed = list(csv.reader(io.StringIO(text)))
    cells = dict(zip(parsed[0], next(r for r in parsed if r and r[0] == ids["included"])))
    assert cells["Sensor problems addressed"] == "" and cells["Data split"] == "Not applicable"  # not charted: empty
    # A row excluded at full text is left out (review of Part B, finding 6).
    _post(client, {"event_id": str(uuid.uuid4()), "study_id": ids["unclear"], "screener_id": WHO, "at": "2026-11-21T10:00:00Z",
                   "kind": "fulltext_decision", "value": {"outcome": "EXCLUDE", "reason_code": ids["code"]}})
    again = client.get(f"{BASE}/export", params={"format": "csv", "view": "charting"}).content.decode("utf-8-sig")
    assert ids["unclear"] not in again and ids["included"] in again
    assert _journal(ws, "CHARTING_EXPORTED")[-1]["parameters"]["view"] == "charting"


def test_the_one_study_route_answers_the_row_and_the_form(env):
    client, _, ids = env
    answer = client.get(f"{BASE}/records/{ids['included']}").json()
    assert answer["row"]["study_id"] == ids["included"] and answer["form"]["version"] == 1
    assert answer["screener_id"] == WHO
    refused = client.get(f"{BASE}/records/{ids['excluded']}")
    assert refused.status_code == 409 and refused.json()["detail"]["code"] == "RECORD_NOT_KEPT"


def test_the_form_routes_are_in_both_allow_lists():
    assert any(p.fullmatch("api/v1/charting/form") for p in PUT_PATHS)
    assert any(p.fullmatch("api/v1/charting/form/pilot/end") for p in POST_PATHS)
    route = (Path(__file__).resolve().parents[2] / "apps" / "research-ui" / "app" / "api" / "console" / "[...path]" / "route.ts")
    text = route.read_text(encoding="utf-8")
    assert "charting\\/form$" in text and "charting\\/form\\/pilot\\/end" in text
