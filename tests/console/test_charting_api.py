"""M12a Part A: the charting table's rows, full-text status and decision, attachments and links.

The workspace is the published screening of ``tests/console/test_export_api.py``
(three records: one EXCLUDE, one MAYBE, one INCLUDE), so two records are kept.
Offline: the suite's socket guard fails any outgoing connection (DoD 7).
"""

from __future__ import annotations

import importlib.util
import json
import socket
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scholar_harness.charting import attachments as att
from scholar_harness.charting import events as cev
from scholar_harness.console import create_app
from scholar_harness.console.browser import POST_PATHS
from scholar_harness.screening import events as ev

_SPEC = importlib.util.spec_from_file_location(
    "_export_api_helpers_charting", Path(__file__).resolve().parent / "test_export_api.py"
)
tea = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(tea)

TOKEN = "desk-token"
BASE = "/api/v1/charting"
WHO = "researcher:local"
MINI_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n" + b"x" * 2048


@pytest.fixture
def env(tmp_path):
    ws, ids = tea.published_workspace(tmp_path)
    app = create_app(ws, token=TOKEN)
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        yield client, ws, ids


def _event(study: str, kind: str, value, **extra) -> dict:
    return {"event_id": str(uuid.uuid4()), "study_id": study, "screener_id": WHO,
            "at": "2026-11-21T10:00:00Z", "kind": kind, "value": value, **extra}


def _code(response) -> str:
    return response.json()["detail"]["code"]


def _journal(ws: Path, action: str) -> list[dict]:
    path = ws / "audit" / "journal.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r for r in rows if r.get("action") == action]


def _row(table: dict, study: str) -> dict:
    return next(r for r in table["rows"] if r["study_id"] == study)


# ------------------------------------------------------------------ DoD 1: rows of every published round


def test_the_full_text_reasons_are_the_criteria_in_force(env, monkeypatch):
    """The reasons follow the criteria in force, not the signed list read on its own (M11b part A, DoD 2)."""
    from scholar_harness.charting import table as tb
    from scholar_harness.screening import criteria as cr

    _client, ws, _ids = env
    signed = cr.criteria_in_force(ws)
    assert signed.exclusion and signed.inclusion, "anti-vacuity: the fixture has criteria on both sides"
    reworded = cr.CriteriaInForce(
        2,
        signed.inclusion,
        tuple(cr.Criterion(c.id, c.side, "Reworded: " + c.text, c.reason_category, c.maps_to_rqs, 2) for c in signed.exclusion),
        (),
        (),
        signed.protocol_fingerprint,
        signed.used,
    )
    monkeypatch.setattr(cr, "criteria_in_force", lambda workspace, **_kw: reworded)
    options = tb.reason_options(ws)
    labels = {o["code"]: o["label"] for o in options}
    for c in signed.exclusion:
        assert labels[c.id] == "Reworded: " + c.text
    for c in signed.inclusion:
        assert f"FAILS-{c.id}" in labels
    assert options[-1]["code"] == "OTHER"


def test_the_table_lists_the_published_include_and_unclear_records_with_their_round(env):
    client, ws, ids = env
    table = client.get(BASE).json()
    assert table["shape"] == "charting.table-v1"
    assert {r["study_id"] for r in table["rows"]} == {ids["included"], ids["unclear"]}
    included, unclear = _row(table, ids["included"]), _row(table, ids["unclear"])
    assert (included["ta_decision"], unclear["ta_decision"]) == ("INCLUDE", "MAYBE")
    assert included["round"] == 1 and included["round_label"] == "Databases"
    assert included["fulltext"]["status"] == "to_get" and included["ft_decision"] is None
    assert table["counts"] == {"kept": 2, "to_get": 2, "requested": 0, "retrieved": 0, "not_retrieved": 0,
                               "included": 0, "excluded": 0, "to_decide": 2}
    assert table["publication"]["status"] == "CURRENT"
    assert [o["code"] for o in table["reason_options"]][-1] == "OTHER"
    assert any(o["code"] == ids["code"] for o in table["reason_options"])


def test_without_a_publication_the_table_refuses(tmp_path):
    ws = tea.se._build(tmp_path)
    tea.decide(ws)
    with TestClient(create_app(ws, token=TOKEN), base_url="http://127.0.0.1",
                    headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        response = client.get(BASE)
    assert response.status_code == 409 and _code(response) == "SCREENING_NOT_PUBLISHED"
    assert not (ws / "charting").exists()


def test_an_archived_round_and_the_current_round_both_give_rows(env):
    client, ws, ids = env
    from scholar_harness.screening import rounds

    record = rounds.archive_round(ws, number=1, arm=rounds.ARM_DATABASES, generation_id="g1", corpus_artifact_id=None)
    rounds.start_round(ws, record, number=2, arm=rounds.ARM_CITATION_SEARCHING, chase="chase_001", corpus_artifact_id=None)
    table = client.get(BASE).json()
    assert table["chasing_pending"] is True  # round 2 is being screened, round 1 stays readable
    assert {r["study_id"] for r in table["rows"]} == {ids["included"], ids["unclear"]}
    assert {r["round"] for r in table["rows"]} == {1}


# ------------------------------------------------------------------ DoD 2: a new publication


def _earlier_publication(ws: Path, kept: dict[str, dict]) -> None:
    """A kept set the table saw at an earlier publication of round 1.

    The engine refuses a changed decision file in an accepted batch
    (``CONTENT_CHANGED``), so a fixture cannot publish round 1 again with other
    decisions; the history row stands for that earlier publication.
    """
    path = ws / "charting" / "kept_history.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"schema": "nexus.charting-kept-history.v1", "round": 1, "generation_id": "gen-earlier",
           "published_at": "2026-11-01T09:00:00+00:00", "seen_at": "2026-11-01T09:05:00Z", "kept": kept}
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")


def _summary(title: str) -> dict:
    return {"title": title, "year": 2024, "doi": None, "round": 1, "arm": "databases", "ta_decision": "INCLUDE"}


def test_a_record_that_left_the_kept_set_keeps_its_events_and_leaves_counts_and_exports(env):
    client, ws, ids = env
    gone_id = "STU-left0000000000000000000000000"
    _earlier_publication(ws, {gone_id: _summary("A record kept earlier"),
                              ids["included"]: _summary("x"), ids["unclear"]: _summary("y")})
    events_file = cev.screener_file(ws, WHO)
    events_file.parent.mkdir(parents=True, exist_ok=True)
    stored = {**_event(gone_id, "fulltext_status", {"status": "requested"}), "method": "HUMAN", "binding": {},
              "received_at": "2026-11-01T10:00:00Z"}
    events_file.write_text(json.dumps(stored) + "\n", encoding="utf-8")
    table = client.get(BASE).json()
    gone = _row(table, gone_id)
    assert gone["kept"] is False and gone["title"] == "A record kept earlier"
    assert gone["fulltext"]["status"] == "requested"  # its events are kept
    assert table["counts"]["kept"] == 2 and table["counts"]["requested"] == 0
    assert table["changes"]["no_longer_kept"] == 1
    body = client.get(f"{BASE}/export", params={"format": "csv", "view": "fulltext"}).content.decode("utf-8-sig")
    assert gone_id not in body and ids["included"] in body
    refused = client.post(f"{BASE}/events", json={"events": [_event(gone_id, "fulltext_status", {"status": "retrieved"})]})
    assert refused.json()["results"][0]["refusal"]["code"] == "RECORD_NOT_KEPT"
    assert len(events_file.read_text(encoding="utf-8").splitlines()) == 1


def test_a_record_that_joined_is_marked_with_the_publication_date(env):
    client, ws, ids = env
    _earlier_publication(ws, {ids["included"]: _summary("x")})
    table = client.get(BASE).json()
    published = json.loads((ws / "literature" / "screening" / "generation.json").read_text(encoding="utf-8"))["published_at"]
    assert _row(table, ids["unclear"])["new_since"] == published
    assert _row(table, ids["included"])["new_since"] is None
    assert table["changes"] == {"published_at": published, "added": 1, "no_longer_kept": 0}
    history = (ws / "charting" / "kept_history.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(history) == 2
    client.get(BASE)
    assert len((ws / "charting" / "kept_history.jsonl").read_text(encoding="utf-8").splitlines()) == 2  # seen once


def test_the_first_visit_marks_nothing_new(env):
    client, _, _ = env
    table = client.get(BASE).json()
    assert all(r["new_since"] is None for r in table["rows"]) and table["changes"] is None


# ------------------------------------------------------------------ DoD 3 and 4: status, one or many


def test_status_events_are_stored_append_only_and_a_replay_is_a_silent_duplicate(env):
    client, ws, ids = env
    event = _event(ids["included"], "fulltext_status", {"status": "not_retrieved", "reason": "no_access"})
    first = client.post(f"{BASE}/events", json={"events": [event]}).json()
    again = client.post(f"{BASE}/events", json={"events": [event]}).json()
    assert first["results"][0]["result"] == "accepted" and again["results"][0]["result"] == "duplicate"
    stored = [json.loads(line) for line in cev.screener_file(ws, WHO).read_text(encoding="utf-8").splitlines()]
    assert len(stored) == 1 and stored[0]["method"] == "HUMAN"
    assert set(stored[0]["binding"]) >= {"protocol_fingerprint", "generation_id", "generation_sha256", "form_version"}
    changed = {**event, "value": {"status": "retrieved"}}
    conflict = client.post(f"{BASE}/events", json={"events": [changed]}).json()
    assert conflict["results"][0]["refusal"]["code"] == "IDEMPOTENCY_CONFLICT"


@pytest.mark.parametrize(("value", "code"), [
    ({"status": "not_retrieved"}, "FULLTEXT_REASON_REQUIRED"),
    ({"status": "not_retrieved", "reason": "other"}, "FULLTEXT_REASON_REQUIRED"),
    ({"status": "not_retrieved", "reason": "lost"}, "FULLTEXT_REASON_INVALID"),
    ({"status": "retrieved", "reason": "no_access"}, "FULLTEXT_REASON_INVALID"),
    ({"status": "not_retrieved", "reason": "no_reply", "reason_text": "x"}, "FULLTEXT_REASON_INVALID"),
    ({"status": "got_it"}, "BODY_INVALID"),
    ({"status": "retrieved", "requested_on": "2026-11-20"}, "BODY_INVALID"),
])
def test_a_status_reason_missing_or_not_allowed_is_refused(env, value, code):
    client, ws, ids = env
    result = client.post(f"{BASE}/events", json={"events": [_event(ids["included"], "fulltext_status", value)]}).json()
    assert result["results"][0]["refusal"]["code"] == code
    assert not cev.screener_file(ws, WHO).exists()


def test_other_with_words_is_a_reason(env):
    client, _, ids = env
    value = {"status": "not_retrieved", "reason": "other", "reason_text": "Library loan pending"}
    result = client.post(f"{BASE}/events", json={"events": [_event(ids["included"], "fulltext_status", value)]}).json()
    assert result["results"][0]["result"] == "accepted"
    assert result["rows"][0]["fulltext"]["reason_text"] == "Library loan pending"


def test_a_status_on_many_records_is_one_request_one_event_each_and_one_journal_row(env):
    client, ws, ids = env
    events = [_event(s, "fulltext_status", {"status": "retrieved"}) for s in (ids["included"], ids["unclear"])]
    events.append(_event(ids["excluded"], "fulltext_status", {"status": "retrieved"}))  # excluded at title and abstract
    before = len(_journal(ws, "CHARTING_EVENTS_RECEIVED"))
    result = client.post(f"{BASE}/events", json={"events": events}).json()
    assert [r["result"] for r in result["results"]] == ["accepted", "accepted", "refused"]
    assert result["results"][2]["refusal"]["code"] == "RECORD_NOT_KEPT"
    assert result["counts"]["retrieved"] == 2
    rows = _journal(ws, "CHARTING_EVENTS_RECEIVED")
    assert len(rows) == before + 1 and rows[-1]["metrics"]["events"] == 2


# ------------------------------------------------------------------ DoD 5: the full-text decision


def test_a_decision_is_include_or_exclude_with_exactly_one_reason(env):
    client, _, ids = env
    post = lambda value: client.post(f"{BASE}/events", json={"events": [_event(ids["included"], "fulltext_decision", value)]}).json()  # noqa: E731
    assert post({"outcome": "EXCLUDE"})["results"][0]["refusal"]["code"] == "FULLTEXT_REASON_REQUIRED"
    assert post({"outcome": "EXCLUDE", "reason_code": "OTHER"})["results"][0]["refusal"]["code"] == "FULLTEXT_REASON_REQUIRED"
    assert post({"outcome": "EXCLUDE", "reason_code": "EXC-99"})["results"][0]["refusal"]["code"] == "FULLTEXT_REASON_INVALID"
    assert post({"outcome": "INCLUDE", "reason_code": ids["code"]})["results"][0]["refusal"]["code"] == "FULLTEXT_REASON_INVALID"
    ok = post({"outcome": "EXCLUDE", "reason_code": ids["code"]})
    assert ok["results"][0]["result"] == "accepted" and ok["counts"]["excluded"] == 1
    other = post({"outcome": "EXCLUDE", "reason_code": "OTHER", "reason_text": "Same study as another report"})
    assert other["rows"][0]["ft_decision"]["reason_text"] == "Same study as another report"


def test_a_bulk_decision_is_refused_whole(env):
    client, ws, ids = env
    events = [_event(s, "fulltext_decision", {"outcome": "INCLUDE"}) for s in (ids["included"], ids["unclear"])]
    response = client.post(f"{BASE}/events", json={"events": events})
    assert response.status_code == 422 and _code(response) == "BODY_INVALID"
    assert not cev.screener_file(ws, WHO).exists()


# ------------------------------------------------------------------ DoD 6: undo


def test_undo_supersedes_and_restores_the_previous_value_for_the_same_study_and_kind(env):
    client, _, ids = env
    first = _event(ids["included"], "fulltext_status", {"status": "requested"})
    second = _event(ids["included"], "fulltext_status", {"status": "not_retrieved", "reason": "not_found"})
    client.post(f"{BASE}/events", json={"events": [first]})
    client.post(f"{BASE}/events", json={"events": [second]})
    undo = _event(ids["included"], "fulltext_status", {"status": "requested"}, supersedes=second["event_id"])
    row = client.post(f"{BASE}/events", json={"events": [undo]}).json()["rows"][0]
    assert row["fulltext"]["status"] == "requested" and row["heads"]["fulltext_status"] == undo["event_id"]
    wrong_study = _event(ids["unclear"], "fulltext_status", {"status": "to_get"}, supersedes=first["event_id"])
    wrong_kind = _event(ids["included"], "fulltext_decision", None, supersedes=first["event_id"])
    results = client.post(f"{BASE}/events", json={"events": [wrong_study, wrong_kind]}).json()["results"]
    assert [r["refusal"]["code"] for r in results] == ["BODY_INVALID", "BODY_INVALID"]
    undecided = _event(ids["included"], "fulltext_decision", {"outcome": "INCLUDE"})
    client.post(f"{BASE}/events", json={"events": [undecided]})
    back = _event(ids["included"], "fulltext_decision", None, supersedes=undecided["event_id"])
    assert client.post(f"{BASE}/events", json={"events": [back]}).json()["rows"][0]["ft_decision"] is None


def test_an_event_for_another_screener_is_refused(env):
    client, _, ids = env
    event = {**_event(ids["included"], "fulltext_status", {"status": "retrieved"}), "screener_id": "someone:else"}
    assert client.post(f"{BASE}/events", json={"events": [event]}).json()["results"][0]["refusal"]["code"] == "BODY_INVALID"


# ------------------------------------------------------------------ DoD 7: a PDF or a link, no outgoing request


def _attach(client, study: str, body: bytes, **params):
    return client.post(f"{BASE}/records/{study}/attachment", content=body,
                       headers={"content-type": "application/pdf"}, params={"name": "Sa 2018.pdf", **params})


def test_a_pdf_is_stored_by_study_with_its_size_and_hash_and_a_to_get_row_becomes_retrieved(env):
    client, ws, ids = env
    response = _attach(client, ids["included"], MINI_PDF)
    assert response.status_code == 200, response.text
    payload = response.json()
    stored = ws / "pdfs" / f"{ids['included']}.pdf"
    assert stored.read_bytes() == MINI_PDF
    attachment = payload["row"]["fulltext"]["attachment"]
    import hashlib

    assert attachment == {"name": "Sa 2018.pdf", "size": len(MINI_PDF), "sha256": hashlib.sha256(MINI_PDF).hexdigest(),
                          "path": f"pdfs/{ids['included']}.pdf", "origin": "attached"}
    assert payload["row"]["fulltext"]["status"] == "retrieved" and len(payload["event_ids"]) == 2
    assert [e["kind"] for e in payload["events"]] == ["attachment", "fulltext_status"]  # each id with its kind
    row = _journal(ws, "CHARTING_ATTACHMENT_ADDED")[-1]
    assert row["parameters"]["sha256"] == attachment["sha256"]
    served = client.get(f"{BASE}/records/{ids['included']}/attachment")
    assert served.status_code == 200 and served.content == MINI_PDF
    assert served.headers["content-type"] == "application/pdf"
    assert served.headers["content-disposition"].startswith("inline")


def test_undo_of_an_attachment_takes_the_file_aside_and_never_deletes_it(env):
    client, ws, ids = env
    first = _attach(client, ids["included"], MINI_PDF).json()
    attach_id, status_id = first["event_ids"]
    undo = [
        _event(ids["included"], "attachment", None, supersedes=attach_id),
        _event(ids["included"], "fulltext_status", {"status": "to_get"}, supersedes=status_id),
    ]
    row = client.post(f"{BASE}/events", json={"events": undo}).json()["rows"][0]
    assert row["fulltext"]["attachment"] is None and row["fulltext"]["status"] == "to_get"
    assert not (ws / "pdfs" / f"{ids['included']}.pdf").exists()
    assert len(list((ws / "pdfs" / "replaced").glob(f"{ids['included']}.*.pdf"))) == 1
    assert client.get(f"{BASE}/records/{ids['included']}/attachment").status_code == 404


def test_a_second_file_keeps_the_first_aside_and_a_retried_upload_is_a_duplicate(env):
    client, ws, ids = env
    event_id = str(uuid.uuid4())
    _attach(client, ids["included"], MINI_PDF, event_id=event_id)
    assert _attach(client, ids["included"], MINI_PDF, event_id=event_id).json()["result"] == "duplicate"
    other = MINI_PDF + b"second"
    assert _attach(client, ids["included"], other, event_id=event_id).status_code == 409
    second = _attach(client, ids["included"], other).json()
    assert second["row"]["fulltext"]["status"] == "retrieved" and len(second["event_ids"]) == 1  # no second status event
    assert (ws / "pdfs" / f"{ids['included']}.pdf").read_bytes() == other
    assert len(list((ws / "pdfs" / "replaced").glob("*.pdf"))) == 1


def test_anything_but_a_pdf_and_a_body_over_the_limit_are_refused(env, monkeypatch):
    client, ws, ids = env
    html = _attach(client, ids["included"], b"<html><body>Sign in</body></html>")
    assert html.status_code == 422 and _code(html) == "ATTACHMENT_NOT_PDF"
    monkeypatch.setattr(att, "MAX_BYTES", 1024)
    big = _attach(client, ids["included"], MINI_PDF)
    assert big.status_code == 413 and _code(big) == "ATTACHMENT_TOO_LARGE"
    assert not (ws / "pdfs" / f"{ids['included']}.pdf").exists()
    assert not list((ws / "pdfs").glob(".attach-*.tmp"))
    assert not cev.screener_file(ws, WHO).exists()
    excluded = _attach(client, ids["excluded"], MINI_PDF)
    assert excluded.status_code == 409 and _code(excluded) == "RECORD_NOT_KEPT"


def test_a_link_is_stored_as_text_and_a_bad_one_is_refused(env):
    client, _, ids = env
    path = f"{BASE}/records/{ids['included']}/attachment"
    ok = client.post(path, json={"link": "https://www.mdpi.com/2072-4292/10/9/1423"}).json()
    assert ok["row"]["fulltext"]["link"] == "https://www.mdpi.com/2072-4292/10/9/1423"
    assert ok["row"]["fulltext"]["status"] == "to_get"  # a link is not a retrieved full text
    for bad in ("javascript:alert(1)", "ftp://x.org/a.pdf", "not a link"):
        response = client.post(path, json={"link": bad})
        assert response.status_code == 422 and _code(response) == "LINK_INVALID"


def test_no_part_a_route_opens_a_socket(env, monkeypatch):
    client, _, ids = env
    opened: list[object] = []
    real = socket.socket.connect

    def spy(self, address):
        opened.append(address)
        return real(self, address)

    monkeypatch.setattr(socket.socket, "connect", spy)
    client.get(BASE)
    client.post(f"{BASE}/events", json={"events": [_event(ids["included"], "fulltext_status", {"status": "requested"})]})
    _attach(client, ids["included"], MINI_PDF)
    client.post(f"{BASE}/records/{ids['unclear']}/attachment", json={"link": "https://example.org/paper"})
    client.get(f"{BASE}/records/{ids['included']}/attachment")
    client.get(f"{BASE}/export", params={"format": "csv", "view": "fulltext"})
    assert opened == []


# ------------------------------------------------------------------ the CSV, the protocol, the allow-lists


def test_the_full_text_csv_has_a_bom_crlf_and_is_journaled_with_its_hash(env):
    client, ws, ids = env
    response = client.get(f"{BASE}/export", params={"format": "csv", "view": "fulltext"})
    assert response.status_code == 200 and response.content.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" in response.content
    import hashlib

    assert _journal(ws, "CHARTING_EXPORTED")[-1]["parameters"]["sha256"] == hashlib.sha256(response.content).hexdigest()
    bad = client.get(f"{BASE}/export", params={"format": "xlsx", "view": "fulltext"})
    assert bad.status_code == 422 and _code(bad) == "CHARTING_EXPORT_FORMAT_INVALID"


def test_a_replaced_protocol_makes_the_table_read_only(env):
    """Review of Part A, finding 2: the read-only path is asserted exactly."""
    client, ws, ids = env
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    protocol["metadata"] = {**(protocol.get("metadata") or {}), "replaced_by": "a re-inception"}
    (ws / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    table = client.get(BASE)
    assert table.status_code == 200
    assert table.json()["read_only"] is True and table.json()["read_only_code"] == "CHARTING_PROTOCOL_REPLACED"
    response = client.post(f"{BASE}/events", json={"events": [_event(ids["included"], "fulltext_status", {"status": "retrieved"})]})
    assert response.status_code == 409 and _code(response) == "CHARTING_PROTOCOL_REPLACED"
    attach = _attach(client, ids["included"], MINI_PDF)
    assert attach.status_code == 409 and _code(attach) == "CHARTING_PROTOCOL_REPLACED"
    assert not cev.screener_file(ws, WHO).exists()
    assert not (ws / "pdfs" / f"{ids['included']}.pdf").exists()


def test_a_hand_edited_included_file_is_never_read_as_published(env):
    """Review of Part A, finding 1: only the bytes the publication recorded are read."""
    client, ws, ids = env
    path = ws / "literature" / "included.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    forged = {**rows[0], "workspace_id": "STU-forged", "title": "Not published"}
    forged["screening"] = {**rows[0]["screening"], "workspace_id": "STU-forged"}
    path.write_text(json.dumps([*rows, forged]), encoding="utf-8")
    response = client.get(BASE)
    assert response.status_code == 409 and _code(response) == "SCREENING_NOT_PUBLISHED"
    assert "not the file" in response.json()["detail"]["message"]
    refused = client.post(f"{BASE}/events", json={"events": [_event("STU-forged", "fulltext_status", {"status": "retrieved"})]})
    assert refused.status_code == 409 and _code(refused) == "SCREENING_NOT_PUBLISHED"
    assert not cev.screener_file(ws, WHO).exists()


def test_an_archived_round_whose_file_was_edited_is_refused(env):
    client, ws, ids = env
    from scholar_harness.screening import rounds

    record = rounds.archive_round(ws, number=1, arm=rounds.ARM_DATABASES, generation_id="g1", corpus_artifact_id=None)
    rounds.start_round(ws, record, number=2, arm=rounds.ARM_CITATION_SEARCHING, chase="chase_001", corpus_artifact_id=None)
    assert client.get(BASE).status_code == 200
    archived = ws / record["path"] / "included.json"
    archived.write_text(archived.read_text(encoding="utf-8").replace("Event record", "Edited record"), encoding="utf-8")
    response = client.get(BASE)
    assert response.status_code == 409 and _code(response) == "SCREENING_NOT_PUBLISHED"


def test_a_busy_history_lock_still_answers_the_table(env, monkeypatch):
    """Review finding 7: a lock that cannot be taken reads the history instead of failing."""
    client, ws, ids = env
    from scholar_harness.charting import kept
    from scholar_harness.charting.lock import LockBusy

    def busy(*args, **kwargs):
        raise LockBusy("held by another program")

    monkeypatch.setattr(kept, "_remember", busy)
    table = client.get(BASE)
    assert table.status_code == 200 and table.json()["counts"]["kept"] == 2


def test_an_earlier_pdf_that_cannot_be_moved_aside_is_a_typed_refusal(env, monkeypatch):
    """Review finding 9: an OSError while placing the file stores nothing and answers a typed code."""
    client, ws, ids = env
    first = _attach(client, ids["included"], MINI_PDF)
    assert first.status_code == 200

    def locked_file(*args, **kwargs):
        raise PermissionError("the file is open in another program")

    monkeypatch.setattr(att, "place", locked_file)
    lines_before = cev.screener_file(ws, WHO).read_text(encoding="utf-8").count("\n")
    second = _attach(client, ids["included"], MINI_PDF + b"other")
    assert second.status_code == 503 and _code(second) == "ATOMIC_COMMIT_FAILED"
    assert cev.screener_file(ws, WHO).read_text(encoding="utf-8").count("\n") == lines_before
    assert (ws / "pdfs" / f"{ids['included']}.pdf").read_bytes() == MINI_PDF
    assert not list((ws / "pdfs").glob(".attach-*.tmp"))


def test_the_new_routes_are_in_both_post_allow_lists():
    for path in ("api/v1/charting/events", "api/v1/charting/records/STU-abc_1/attachment"):
        assert any(p.fullmatch(path) for p in POST_PATHS), path
    route = (Path(__file__).resolve().parents[2] / "apps" / "research-ui" / "app" / "api" / "console" / "[...path]" / "route.ts")
    text = route.read_text(encoding="utf-8")
    assert "charting\\/events" in text and "charting\\/records" in text


def test_the_protocol_file_is_never_written(env):
    client, ws, ids = env
    before = (ws / "protocol.json").read_bytes()
    client.get(BASE)
    client.post(f"{BASE}/events", json={"events": [_event(ids["included"], "fulltext_decision", {"outcome": "INCLUDE"})]})
    _attach(client, ids["unclear"], MINI_PDF)
    assert (ws / "protocol.json").read_bytes() == before


def test_the_packaged_browser_path_carries_the_pdf_and_the_csv_as_bytes(tmp_path):
    """The console's own `/api/console` path (static export) passes the raw PDF body and serves bytes back."""
    from scholar_harness.console import browser

    ws, ids = tea.published_workspace(tmp_path)
    app = create_app(ws, token=TOKEN, browser_session="session-secret",
                     launch_codes=browser.LaunchCodes("session-secret"), workspaces_root=ws.parent)
    raw = MINI_PDF + bytes([0xFF, 0xFE, 0x00, 0x80, 0xC3, 0x28])  # not UTF-8: a text decode would change it
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        client.cookies.set(browser.SESSION_COOKIE, "session-secret")
        same = {"Origin": "http://127.0.0.1:8765", "content-type": "application/pdf"}
        posted = client.post(f"/api/console{BASE}/records/{ids['included']}/attachment",
                             content=raw, headers=same, params={"name": "a.pdf"})
        assert posted.status_code == 200, posted.text
        assert (ws / "pdfs" / f"{ids['included']}.pdf").read_bytes() == raw
        served = client.get(f"/api/console{BASE}/records/{ids['included']}/attachment")
        assert served.content == raw and served.headers["content-type"] == "application/pdf"
        csv_body = client.get(f"/api/console{BASE}/export", params={"format": "csv", "view": "fulltext"})
        assert csv_body.content.startswith(b"\xef\xbb\xbf")
        assert csv_body.headers["content-disposition"].startswith("attachment")
