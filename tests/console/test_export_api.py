"""Decision export of the published screening (spec 10, `GET /export`).

The workspace is published the way `tests/test_screening_events.py` does it
(events through `intake`, the projection, a staged approval, `cmd_collect`),
then exported over HTTP. The export reads the published files only.
"""

from __future__ import annotations

import csv
import importlib.util
import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scholar_harness.console import create_app
from scholar_harness.screening import events as ev
from scholar_harness.screening.collector import cmd_collect

_SPEC = importlib.util.spec_from_file_location(
    "_screening_events_helpers", Path(__file__).resolve().parents[1] / "test_screening_events.py"
)
se = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(se)

BASE = "/api/v1/screening"
DESKTOP, PHONE = "desktop-token", "phone-token"


def client_for(ws: Path) -> TestClient:
    return TestClient(
        create_app(ws, token=DESKTOP, phone_tokens={PHONE}),
        base_url="http://127.0.0.1",
        headers={"Authorization": f"Bearer {DESKTOP}"},
    )


def decide(ws: Path, *, note: str | None = "Not about UAVs.") -> dict[str, str]:
    """One exclusion failing an inclusion criterion (with a note), one unclear, one include."""
    studies = se._studies(ws)
    inclusion = min(ev.load_context(ws).inclusion_ids)
    se._intake(ws, [
        se._event(ws, studies[0], "EXCLUDE", reason_code=f"FAILS-{inclusion}", note=note),
        se._event(ws, studies[1], "MAYBE"),
        se._event(ws, studies[2], "INCLUDE"),
    ])
    return {"excluded": studies[0], "unclear": studies[1], "included": studies[2], "code": f"FAILS-{inclusion}"}


def publish(ws: Path) -> None:
    for index in ev.load_context(ws).batches:
        ev.write_projection(ws, index, se.SCREENER, workspace_id=se.WS_ID)
    se._stage_approval(ws)
    cmd_collect(ws)


def published_workspace(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    ws = se._build(tmp_path)
    ids = decide(ws)
    publish(ws)
    return ws, ids


def change_after_publish(ws: Path, study: str, *, project: bool = True) -> None:
    head = ev.winning_event(ev.read_events(ws), study, se.SCREENER)
    se._intake(ws, [se._event(ws, study, "EXCLUDE", supersedes=head["event_id"], decided_at="2026-11-04T12:01:00.000Z")])
    if project:
        ev.write_projection(ws, 1, se.SCREENER, workspace_id=se.WS_ID)


@pytest.fixture
def published(tmp_path):
    return published_workspace(tmp_path)


def _literature(ws: Path, name: str) -> list[dict]:
    return json.loads((ws / "literature" / name).read_text(encoding="utf-8"))


def _ris_blocks(body: bytes) -> list[list[str]]:
    text = body.decode("utf-8")
    blocks, current = [], []
    for line in text.split("\r\n"):
        if not line:
            continue
        current.append(line)
        if line.startswith("ER  -"):
            blocks.append(current)
            current = []
    assert not current
    return blocks


def _ris_ids(body: bytes) -> list[str]:
    return [line[6:] for block in _ris_blocks(body) for line in block if line.startswith("ID  - ")]


def _csv_rows(body: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(body.decode("utf-8-sig"), newline="")))


def test_ris_default_holds_included_and_unclear_and_set_excluded_adds_them(published):
    ws, ids = published
    client = client_for(ws)
    response = client.get(f"{BASE}/export", params={"format": "ris"})
    assert response.status_code == 200, response.text
    assert sorted(_ris_ids(response.content)) == sorted([ids["included"], ids["unclear"]])
    generation = json.loads((ws / "literature" / "screening" / "generation.json").read_text(encoding="utf-8"))
    disposition = response.headers["content-disposition"]
    assert disposition == f'attachment; filename="ws-screening-{generation["generation_id"]}-included+unclear.ris"'

    every = client.get(f"{BASE}/export", params={"format": "ris", "set": "excluded,included,unclear"})
    assert sorted(_ris_ids(every.content)) == sorted([ids["included"], ids["unclear"], ids["excluded"]])
    only = client.get(f"{BASE}/export", params={"format": "ris", "set": "excluded"})
    assert _ris_ids(only.content) == [ids["excluded"]]


def test_ris_shape_no_bom_no_empty_field_and_reason_from_the_decision_file(published):
    ws, ids = published
    body = client_for(ws).get(f"{BASE}/export", params={"format": "ris", "set": "included,unclear,excluded"}).content
    assert not body.startswith(b"\xef\xbb\xbf")
    blocks = _ris_blocks(body)
    assert len(blocks) == 3
    for block in blocks:
        assert block[0] == "TY  - JOUR"
        assert block[-1] == "ER  - "
        for line in block[1:-1]:
            assert len(line) > 6 and line[2:6] == "  - ", line  # never an empty field
        assert {line[:2] for line in block} <= {"TY", "TI", "AU", "PY", "T2", "DO", "UR", "AB", "ID", "N1", "ER"}
    excluded = next(b for b in blocks if f"ID  - {ids['excluded']}" in b)
    # The published excluded.json does not carry this code (its reasoning is the note).
    screening = _literature(ws, "excluded.json")[0]["screening"]
    assert screening["violated_exclusion_criteria"] == [] and screening["screening_reasoning"] == "Not about UAVs."
    note = next(line for line in excluded if line.startswith("N1"))
    assert note.startswith(f"N1  - Screening: EXCLUDE; reason: {ids['code']}; generation GEN-")


def test_csv_shape_bom_crlf_and_sets_partition_the_published_records(published):
    ws, ids = published
    response = client_for(ws).get(f"{BASE}/export", params={"format": "csv"})
    assert response.status_code == 200, response.text
    body = response.content
    assert body.startswith(b"\xef\xbb\xbf")
    text = body.decode("utf-8-sig")
    assert text.split("\r\n")[0] == (
        "study_id,decision,reason_code,title,authors,year,venue,doi,url,abstract,generation_id"
    )
    assert "\n" not in text.replace("\r\n", "")
    rows = _csv_rows(body)
    prisma = json.loads((ws / "literature" / "prisma_report.json").read_text(encoding="utf-8"))
    by_decision = {d: [r for r in rows if r["decision"] == d] for d in ("include", "unclear", "exclude")}
    assert len(by_decision["include"]) == prisma["records_included"]
    assert len(by_decision["unclear"]) == prisma["records_unclear"]
    assert len(by_decision["exclude"]) == prisma["records_excluded"]
    assert len(rows) == prisma["records_screened"]
    published_ids = {r["workspace_id"] for r in _literature(ws, "included.json") + _literature(ws, "excluded.json")}
    assert {r["study_id"] for r in rows} == published_ids
    for row in by_decision["exclude"]:
        assert row["reason_code"]
    assert by_decision["exclude"][0]["reason_code"] == ids["code"]
    assert all(r["reason_code"] == "" for r in by_decision["include"] + by_decision["unclear"])
    # Each set alone gives exactly its part: the sets partition the records.
    client = client_for(ws)
    parts = {
        name: {r["study_id"] for r in _csv_rows(client.get(f"{BASE}/export", params={"format": "csv", "set": name}).content)}
        for name in ("included", "unclear", "excluded")
    }
    assert parts["included"] | parts["unclear"] | parts["excluded"] == published_ids
    assert not (parts["included"] & parts["unclear"]) and not (parts["included"] & parts["excluded"])
    assert parts["unclear"] == {ids["unclear"]}


def test_zero_excluded_still_exports_an_empty_file_with_its_header(tmp_path):
    ws = se._build(tmp_path)
    se._intake(ws, [se._event(ws, s, "INCLUDE") for s in se._studies(ws)])
    publish(ws)
    body = client_for(ws).get(f"{BASE}/export", params={"format": "csv", "set": "excluded"}).content
    assert body.decode("utf-8-sig") == "study_id,decision,reason_code,title,authors,year,venue,doi,url,abstract,generation_id\r\n"


def test_export_not_published_before_publish(tmp_path):
    ws = se._build(tmp_path)
    decide(ws)
    for path in ("/export?format=ris", "/methods"):
        response = client_for(ws).get(BASE + path)
        assert response.status_code == 409, response.text
        assert response.json()["detail"]["code"] == "EXPORT_NOT_PUBLISHED"


def test_a_decision_after_publish_is_generation_stale_on_both_routes(published):
    from scholar_harness.authority.generations import require_current_generation

    ws, ids = published
    client = client_for(ws)
    head = ev.winning_event(ev.read_events(ws), ids["included"], se.SCREENER)
    event = {k: v for k, v in se._event(
        ws, ids["included"], "EXCLUDE", supersedes=head["event_id"], decided_at="2026-11-04T12:01:00.000Z"
    ).items()}
    assert client.post(f"{BASE}/decisions/events", json={"events": [event]}).json()["results"][0]["result"] == "accepted"
    # The authority gate alone still reads CURRENT: the generation binds the
    # batch files, not the decisions. The export's own check catches it.
    assert require_current_generation(ws).status.value == "CURRENT"
    for path in ("/export?format=csv", "/methods"):
        response = client.get(BASE + path)
        assert response.status_code == 409, response.text
        assert response.json()["detail"]["code"] == "GENERATION_STALE"


def test_an_unprojected_decision_after_publish_is_also_stale(published):
    ws, ids = published
    change_after_publish(ws, ids["unclear"], project=False)
    response = client_for(ws).get(f"{BASE}/export", params={"format": "ris"})
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "GENERATION_STALE"


def test_a_tampered_excluded_json_is_a_source_mismatch(published):
    ws, _ids = published
    path = ws / "literature" / "excluded.json"
    path.write_text(path.read_text(encoding="utf-8").replace("Not about UAVs.", "Edited."), encoding="utf-8")
    response = client_for(ws).get(f"{BASE}/export", params={"format": "csv"})
    assert response.status_code == 409, response.text
    detail = response.json()["detail"]
    assert detail["code"] == "EXPORT_SOURCE_MISMATCH" and detail["output"] == "excluded.json"
    assert str(ws) not in response.text


@pytest.mark.parametrize(
    "params",
    [{"format": "bibtex"}, {"format": "ris", "set": "included,maybe"}, {"format": "csv", "set": ""}],
    ids=["format", "unknown-set", "empty-set"],
)
def test_export_format_invalid(published, params):
    ws, _ids = published
    response = client_for(ws).get(f"{BASE}/export", params=params)
    assert response.status_code == 422, response.text
    assert response.json()["detail"]["code"] == "EXPORT_FORMAT_INVALID"


def test_phone_token_is_refused(published):
    ws, _ids = published
    phone = {"Authorization": f"Bearer {PHONE}"}
    for path in ("/export?format=ris", "/methods"):
        response = client_for(ws).get(BASE + path, headers=phone)
        assert response.status_code == 403, response.text
        assert response.json()["detail"]["code"] == "TOKEN_SCOPE_REFUSED"


def _tree(ws: Path) -> dict[str, bytes]:
    return {str(p.relative_to(ws)): p.read_bytes() for p in sorted(ws.rglob("*")) if p.is_file()}


def test_a_download_writes_no_file_and_no_journal_row(published):
    ws, _ids = published
    before = _tree(ws)
    client = client_for(ws)
    assert client.get(f"{BASE}/export", params={"format": "ris"}).status_code == 200
    assert client.get(f"{BASE}/export", params={"format": "csv"}).status_code == 200
    assert _tree(ws) == before
