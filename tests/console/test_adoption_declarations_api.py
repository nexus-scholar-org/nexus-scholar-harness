"""H-adopted-decisions-disclosure: decisions stored from the agent's drafts are declared.

The acceptance run of 2026-11-20 stored 996 of 1,062 decisions in bulk from the
agent's drafts as ``method: HUMAN`` events with a note; Publish then passed
"Every decision is a human decision", Agreement counted them as blind agreement
and said "You saw every record. No sample needed.", and the methods text said one
reviewer screened every record (findings 43 and 44). Decision 2026-11-22: the
reviewer declares such decisions in ``audit/adoption_declarations.jsonl``; the
events are never rewritten and the Contract v1 model is unchanged.

The workspace is the three-record API fixture of ``test_screening_api_v1.py``.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
import test_screening_api_v1 as api
from fastapi.testclient import TestClient
from test_screening_api_v1 import BASE, DESKTOP, PHONE, _event, _post, _propose, _studies

from scholar_harness.console import browser, create_app
from scholar_harness.console.refusals import CONSOLE_REFUSALS
from scholar_harness.screening import adoption
from scholar_harness.screening import events as ev
from scholar_harness.screening import read_store

BULK = "Adopted in bulk from the agent's draft (proposal P-1); not reviewed individually"
ROUTE = f"{BASE}/adoption-declarations"


@pytest.fixture
def ws(tmp_path) -> Path:
    root = tmp_path / "root"
    root.mkdir()
    return api._workspace(root)


def _client(ws: Path, token: str = DESKTOP) -> TestClient:
    app = create_app(ws, token=DESKTOP, phone_tokens={PHONE})
    return TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {token}"})


def _journal(ws: Path, action: str) -> list[dict]:
    rows = [json.loads(x) for x in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    return [r for r in rows if r.get("action") == action]


def _bulk(client: TestClient) -> dict[str, dict]:
    """Records 0 and 1 stored in bulk (Exclude, Include), record 2 read by the reviewer (Include)."""
    studies = _studies(client)
    events = [
        _event(client, studies[0], "EXCLUDE", note=BULK),
        _event(client, studies[1], "INCLUDE", note="Stored in bulk from the agent's draft"),
        _event(client, studies[2], "INCLUDE", note="Read it; about weed mapping."),
    ]
    _post(client, events)
    return {e["study_id"]: e for e in events}


def _declare(client: TestClient, event_ids: list[str], **extra):
    return client.post(ROUTE, json={"event_ids": event_ids, "confirm": True, **extra})


def _check(client: TestClient, name: str) -> dict:
    return next(c for c in client.get(f"{BASE}/prisma/preview").json()["checks"] if c["name"] == name)


# --- DoD 1: the refusals, each with its code --------------------------------------------


def test_a_declaration_without_confirm_is_refused_and_writes_nothing(ws):
    client = _client(ws)
    events = _bulk(client)
    journal = (ws / "audit" / "journal.jsonl").read_bytes()
    response = client.post(ROUTE, json={"event_ids": [next(iter(events.values()))["event_id"]]})
    assert (response.status_code, response.json()["detail"]["code"]) == (422, "ADOPTION_CONFIRM_REQUIRED")
    assert not (ws / adoption.DECLARATIONS_FILE).exists()
    assert (ws / "audit" / "journal.jsonl").read_bytes() == journal


def test_a_declaration_from_a_phone_is_refused(ws):
    events = _bulk(_client(ws))
    response = _declare(_client(ws, token=PHONE), [e["event_id"] for e in events.values()])
    assert (response.status_code, response.json()["detail"]["code"]) == (403, "TOKEN_SCOPE_REFUSED")
    assert not (ws / adoption.DECLARATIONS_FILE).exists()


def test_an_event_that_is_not_a_current_winning_decision_is_refused(ws):
    client = _client(ws)
    events = _bulk(client)
    first = next(iter(events.values()))
    # Superseded: the reviewer decided the record again.
    _post(client, [_event(client, first["study_id"], "INCLUDE", supersedes=first["event_id"],
                          decided_at="2026-11-04T11:00:00.000Z")])
    for event_id in (first["event_id"], str(uuid.uuid4())):
        response = _declare(client, [event_id])
        assert (response.status_code, response.json()["detail"]["code"]) == (409, "ADOPTION_EVENT_NOT_WINNING"), event_id
    assert not (ws / adoption.DECLARATIONS_FILE).exists()


def test_the_same_record_twice_is_refused_in_one_request_and_in_a_second_declaration(ws):
    client = _client(ws)
    events = _bulk(client)
    bulk = [e["event_id"] for e in events.values() if e["note"] != "Read it; about weed mapping."]
    twice = _declare(client, [bulk[0], bulk[0]])
    assert (twice.status_code, twice.json()["detail"]["code"]) == (409, "ADOPTION_ALREADY_DECLARED")
    assert _declare(client, bulk).status_code == 200
    again = _declare(client, [bulk[1]])
    assert (again.status_code, again.json()["detail"]["code"]) == (409, "ADOPTION_ALREADY_DECLARED")
    assert len(_journal(ws, "SCREENING_ADOPTION_DECLARED")) == 1


def test_the_codes_are_console_refusals_and_the_route_passes_only_the_browser_guard():
    for code in adoption.CODES:
        assert code in CONSOLE_REFUSALS, code
    paths = {p.pattern for p in browser.POST_PATHS}
    assert {"api/v1/screening/adoption-declarations", "api/v1/screening/adoption-declarations/(withdrawals|sample-results)"} <= paths


def test_a_declaration_from_another_origin_is_refused_by_the_browser_surface(ws, tmp_path):
    events = _bulk(_client(ws))
    ui = tmp_path / "ui"
    (ui / "en").mkdir(parents=True)
    (ui / "en" / "index.html").write_text("<html></html>", encoding="utf-8")
    app = create_app(ws, token=DESKTOP, browser_session="s", launch_codes=browser.LaunchCodes("s"), ui_dir=ui,
                     workspaces_root=ws.parent)
    client = TestClient(app, base_url="http://127.0.0.1:8765")
    client.cookies.set(browser.SESSION_COOKIE, "s")
    body = {"event_ids": [next(iter(events.values()))["event_id"]], "confirm": True}
    foreign = client.post("/api/console" + ROUTE, json=body, headers={"Origin": "http://127.0.0.1:3000"})
    assert (foreign.status_code, foreign.json()["detail"]["code"]) == (403, "CONSOLE_ORIGIN_REFUSED")
    same = client.post("/api/console" + ROUTE, json=body, headers={"Origin": "http://127.0.0.1:8765"})
    assert same.status_code == 200, same.text


# --- the candidates are offered, never applied ------------------------------------------


def test_candidates_are_offered_by_their_note_and_nothing_is_declared_until_confirmed(ws):
    client = _client(ws)
    events = _bulk(client)
    view = client.get(ROUTE).json()
    assert (view["candidates"], view["undeclared_candidates"], view["declared"]) == (2, 2, 0)
    listed = {c["event_id"] for c in view["candidate_list"]}
    assert listed == {e["event_id"] for e in events.values() if e["note"] != "Read it; about weed mapping."}
    assert view["phrase"] == "stored from the agent's draft without being read one by one"
    assert not (ws / adoption.DECLARATIONS_FILE).exists()  # offered, not applied
    assert _check(client, "adopted_decisions_declared")["ok"] is False


def test_a_declaration_is_one_line_and_one_journal_row_and_the_events_are_unchanged(ws):
    client = _client(ws)
    events = _bulk(client)
    stored = {p: p.read_bytes() for p in (ws / ev.EVENTS_DIR).glob("*.jsonl")}
    bulk = [e for e in events.values() if e["note"] != "Read it; about weed mapping."]
    body = _declare(client, [e["event_id"] for e in bulk], note="The 2026-11-20 adoption").json()
    declaration = body["declaration"]
    assert declaration["counts"] == {"INCLUDE": 1, "EXCLUDE": 1, "MAYBE": 0}
    assert declaration["declared_by"] == "researcher:local" and declaration["declared_at"]
    assert {e["event_id"] for e in declaration["events"]} == {e["event_id"] for e in bulk}
    [line] = (ws / adoption.DECLARATIONS_FILE).read_text(encoding="utf-8").splitlines()
    assert json.loads(line)["declaration_id"] == declaration["declaration_id"]
    [row] = _journal(ws, "SCREENING_ADOPTION_DECLARED")
    assert row["parameters"]["line_id"] == declaration["declaration_id"]
    assert {p: p.read_bytes() for p in (ws / ev.EVENTS_DIR).glob("*.jsonl")} == stored  # never rewritten
    assert body["state"]["declared"] == 2 and body["state"]["undeclared_candidates"] == 0


def test_the_client_cannot_choose_who_or_when(ws):
    client = _client(ws)
    events = _bulk(client)
    response = _declare(client, [next(iter(events.values()))["event_id"]], declared_by="someone", declared_at="2020-01-01")
    assert (response.status_code, response.json()["detail"]["code"]) == (422, "BODY_INVALID")


# --- a line cannot be forged or removed unnoticed ----------------------------------------


def test_a_line_typed_into_the_file_is_not_applied_and_a_removed_line_is_reported(ws):
    client = _client(ws)
    events = _bulk(client)
    target = next(e for e in events.values() if e["note"] == BULK)
    forged = {"schema": adoption.SCHEMA, "kind": "declaration", "id": "ADD-" + "f" * 24, "declaration_id": "ADD-" + "f" * 24,
              "events": [{"event_id": target["event_id"], "study_id": target["study_id"], "outcome": "EXCLUDE"}],
              "counts": {"INCLUDE": 0, "EXCLUDE": 1, "MAYBE": 0}, "declared_by": "x", "declared_at": "x"}
    (ws / "audit").mkdir(exist_ok=True)
    (ws / adoption.DECLARATIONS_FILE).write_text(json.dumps(forged) + "\n", encoding="utf-8")
    view = client.get(ROUTE).json()
    assert view["declared"] == 0 and view["integrity"]["unconfirmed"] == ["ADD-" + "f" * 24]
    check = _check(client, "adopted_decisions_declared")
    assert check["ok"] is False and check["advisory"] is True

    (ws / adoption.DECLARATIONS_FILE).unlink()
    assert _declare(client, [target["event_id"]]).status_code == 200
    (ws / adoption.DECLARATIONS_FILE).write_text("", encoding="utf-8")  # the line is removed by hand
    view = client.get(ROUTE).json()
    assert view["declared"] == 0 and len(view["integrity"]["removed"]) == 1
    assert _check(client, "adopted_decisions_declared")["ok"] is False


def test_a_withdrawal_is_a_later_line_and_the_declaration_stays(ws):
    client = _client(ws)
    events = _bulk(client)
    target = next(e for e in events.values() if e["note"] == BULK)
    assert _declare(client, [target["event_id"]]).status_code == 200
    unconfirmed = client.post(f"{ROUTE}/withdrawals", json={"event_ids": [target["event_id"]]})
    assert unconfirmed.json()["detail"]["code"] == "ADOPTION_CONFIRM_REQUIRED"
    not_declared = client.post(f"{ROUTE}/withdrawals", json={"event_ids": [str(uuid.uuid4())], "confirm": True})
    assert (not_declared.status_code, not_declared.json()["detail"]["code"]) == (409, "ADOPTION_NOT_DECLARED")
    done = client.post(f"{ROUTE}/withdrawals", json={"event_ids": [target["event_id"]], "confirm": True})
    assert done.status_code == 200, done.text
    lines = (ws / adoption.DECLARATIONS_FILE).read_text(encoding="utf-8").splitlines()
    assert [json.loads(x)["kind"] for x in lines] == ["declaration", "withdrawal"]
    assert client.get(ROUTE).json()["declared"] == 0


# --- DoD 2: Agreement leaves the declared decisions out ----------------------------------


def test_agreement_excludes_declared_decisions_and_says_how_many(ws):
    client = _client(ws)
    for study in _studies(client):
        _propose(client, ws, study)
    events = _bulk(client)
    before = client.get(f"{BASE}/agreement").json()
    assert before["decided_with_proposal"] == 3
    bulk = [e["event_id"] for e in events.values() if e["note"] != "Read it; about weed mapping."]
    assert _declare(client, bulk).status_code == 200
    after = client.get(f"{BASE}/agreement").json()
    assert after["decided_with_proposal"] == 1  # fails on today's code: the adopted decisions were counted
    assert after["adoption"]["declared"] == 2
    assert after["adoption"]["sample_owed"] is True and after["adoption"]["no_sample_drawn"] is True


def test_a_sample_is_drawn_with_its_seed_and_owed_until_its_result_is_recorded(ws):
    client = _client(ws)
    events = _bulk(client)
    excluded = next(e for e in events.values() if e["outcome"] == "EXCLUDE")
    bulk = [e["event_id"] for e in events.values() if e["note"] != "Read it; about weed mapping."]
    too_big = _declare(client, bulk, sample={"size": 2, "seed": 20261120})
    assert (too_big.status_code, too_big.json()["detail"]["code"]) == (422, "ADOPTION_SAMPLE_INVALID")
    body = _declare(client, bulk, sample={"size": 1, "seed": 20261120}).json()
    sample = body["declaration"]["sample"]
    assert (sample["size"], sample["seed"], sample["study_ids"], sample["how"]) == (1, 20261120, [excluded["study_id"]], "drawn")
    agreement = client.get(f"{BASE}/agreement").json()["adoption"]
    assert (agreement["sample_owed"], agreement["sample_owed_size"]) == (True, 1)
    declaration_id = body["declaration"]["declaration_id"]
    # The reviewer reads the sampled record in Triage and changes it to Include.
    _post(client, [_event(client, excluded["study_id"], "INCLUDE", supersedes=excluded["event_id"],
                          decided_at="2026-11-05T10:00:00.000Z")])
    unconfirmed = client.post(f"{ROUTE}/sample-results", json={"declaration_id": declaration_id})
    assert unconfirmed.json()["detail"]["code"] == "ADOPTION_CONFIRM_REQUIRED"
    result = client.post(f"{ROUTE}/sample-results", json={"declaration_id": declaration_id, "confirm": True})
    assert result.status_code == 200, result.text
    assert result.json()["result"]["changed_study_ids"] == [excluded["study_id"]]
    again = client.post(f"{ROUTE}/sample-results", json={"declaration_id": declaration_id, "confirm": True})
    assert (again.status_code, again.json()["detail"]["code"]) == (409, "ADOPTION_SAMPLE_INVALID")
    state = client.get(f"{BASE}/agreement").json()["adoption"]
    assert state["sample_owed"] is False
    assert state["samples"][0]["read"] is True and state["samples"][0]["changed"] == 1
    assert state["declared"] == 1  # the changed record is the reviewer's reading now


def test_a_sample_given_by_its_study_ids_is_kept_as_given(ws):
    client = _client(ws)
    events = _bulk(client)
    excluded = next(e for e in events.values() if e["outcome"] == "EXCLUDE")
    body = _declare(client, [excluded["event_id"]],
                    sample={"size": 1, "seed": 20261121, "study_ids": [excluded["study_id"]]}).json()
    assert body["declaration"]["sample"]["how"] == "given"
    other = next(e for e in events.values() if e["outcome"] == "INCLUDE" and e["note"] != BULK)
    bad = _declare(client, [other["event_id"]], sample={"size": 1, "seed": 1, "study_ids": [other["study_id"]]})
    assert bad.json()["detail"]["code"] == "ADOPTION_SAMPLE_INVALID"


# --- DoD 3: Publish ---------------------------------------------------------------------


def test_the_publish_checks_are_renamed_and_the_declaration_check_does_not_block(ws):
    client = _client(ws)
    events = _bulk(client)
    provenance = _check(client, "human_provenance")
    assert provenance["ok"] is True and provenance["detail"] == "every decision is recorded as the reviewer's"
    check = _check(client, "adopted_decisions_declared")
    assert (check["ok"], check["advisory"]) == (False, True)
    assert "2" in check["detail"]
    bulk = [e["event_id"] for e in events.values() if e["note"] != "Read it; about weed mapping."]
    assert _declare(client, bulk).status_code == 200
    check = _check(client, "adopted_decisions_declared")
    assert check["ok"] is True
    preview = client.get(f"{BASE}/prisma/preview").json()
    assert preview["adoption"]["declared"] == 2 and preview["adoption"]["sample_owed"] is True
    # No other check is advisory: those still block as before.
    assert [c["name"] for c in preview["checks"] if c.get("advisory")] == ["adopted_decisions_declared"]


def test_with_no_candidate_the_declaration_check_passes(ws):
    client = _client(ws)
    studies = _studies(client)
    _post(client, [_event(client, s, "INCLUDE") for s in studies])
    assert _check(client, "adopted_decisions_declared")["ok"] is True


# --- the read store: a declaration is seen by the next display request --------------------


def test_the_next_display_request_sees_a_declaration(ws):
    read_store.clear()
    client = _client(ws)
    events = _bulk(client)
    assert _check(client, "adopted_decisions_declared")["ok"] is False  # kept by the display route
    assert client.get(f"{BASE}/summary").json()["adoption"]["declared"] == 0
    bulk = [e["event_id"] for e in events.values() if e["note"] != "Read it; about weed mapping."]
    assert _declare(client, bulk).status_code == 200
    assert _check(client, "adopted_decisions_declared")["ok"] is True
    assert client.get(f"{BASE}/summary").json()["adoption"]["declared"] == 2
    # A withdrawal is seen as well.
    assert client.post(f"{ROUTE}/withdrawals", json={"event_ids": bulk[:1], "confirm": True}).status_code == 200
    assert client.get(f"{BASE}/summary").json()["adoption"]["declared"] == 1
