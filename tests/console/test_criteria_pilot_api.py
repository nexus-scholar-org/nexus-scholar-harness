"""M11b part B: the criteria pilot (DoD 11 to 15; answers 5, 6, 9 and 11 of 2026-11-21).

A pilot is a random sample of the records with no main decision. Its decisions
are **not counted** (answer 5): they live in their own file and never reach the
event log, the projected batch decisions files, approval, collect or the
agreement read. While it is open, a main decision on one of its records is
refused; when it closes, its records are ordinary undecided records, screened
again blind to the pilot decision (answer 11). The result is counts only.

The workspace has 60 records in three batches (criteria INC-01 and EXC-01).
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
import test_screening_api_v1 as api
from fastapi.testclient import TestClient
from test_agent_runs_api import CONSENT, FakeDriver
from test_screening_api_v1 import BASE, DESKTOP, PHONE, WS_ID

from scholar_harness.console import create_app
from scholar_harness.console.refusals import CONSOLE_REFUSALS
from scholar_harness.contracts import AcceptanceContext, accept_artifact
from scholar_harness.screening import events as ev
from scholar_harness.screening import pilot as pl
from scholar_harness.screening import proposals as pr
from scholar_harness.screening.batcher import cmd_prepare
from scholar_protocol.canonical import canonical_fingerprint
from scholar_protocol.models import ResearchProtocol
from scholar_search.identity import build_corpus_snapshot_artifact
from scholar_search.models import Author, Document, ExternalIds

RECORDS = 60


def _workspace(root: Path, *, records: int = RECORDS, prepare: bool = True) -> Path:
    ws = root / "ws"
    ws.mkdir(parents=True)
    (ws / "project.json").write_text(json.dumps({"project_id": "pilot", "registered_workspace_id": WS_ID}), encoding="utf-8")
    protocol = json.loads(api.PROTOCOL.read_text(encoding="utf-8"))
    (ws / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    (ws / "audit").mkdir()
    (ws / "audit" / "journal.jsonl").touch()
    fingerprint = canonical_fingerprint(ResearchProtocol.model_validate(protocol))
    docs = [
        Document(title=f"Corpus record {i:02d}", year=2026, provider="crossref", provider_id=f"pl-{i}",
                 external_ids=ExternalIds(doi=f"10.1000/pl-{i}"), abstract=f"Abstract {i} about UAV weed mapping.",
                 authors=[Author("Reviewer")], workspace_id=f"SCI-{i:06d}")
        for i in range(records)
    ]
    corpus = build_corpus_snapshot_artifact(
        docs, workspace_id=WS_ID, run_id="RUN-pilot", protocol_fingerprint=fingerprint,
        created_at=datetime(2026, 11, 4, tzinfo=UTC), commit="3" * 40,
    ).artifact
    assert accept_artifact(ws, corpus, expected=AcceptanceContext(
        workspace_id=WS_ID, protocol_fingerprint=fingerprint, corpus_fingerprint=corpus["corpus_fingerprint"])).accepted
    (ws / "literature").mkdir()
    (ws / "literature" / "verified.json").write_text(
        json.dumps([{"workspace_id": d.workspace_id, "title": d.title, "abstract": d.abstract} for d in docs]),
        encoding="utf-8")
    if prepare:
        cmd_prepare(ws, batch_size=20)
    return ws


def _client(ws: Path, driver=None) -> TestClient:
    app = create_app(ws, token=DESKTOP, phone_tokens={PHONE})
    app.state.driver_factory = lambda provider, key: driver or FakeDriver()
    app.state.run_executor = lambda fn: fn()
    return TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {DESKTOP}"})


@pytest.fixture
def ws(tmp_path) -> Path:
    return _workspace(tmp_path)


@pytest.fixture
def client(ws) -> TestClient:
    return _client(ws)


def _ok(response) -> dict:
    assert response.status_code == 200, response.text
    return response.json()


def _code(response) -> str:
    return response.json()["detail"]["code"]


def _journal(ws: Path) -> list[dict]:
    return [json.loads(x) for x in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]


def _draw(client: TestClient, n: int = 20) -> dict:
    return _ok(client.post(f"{BASE}/pilot", json={"n": n, "confirm": True}))


def _pilot_records(client: TestClient) -> list[str]:
    return [i["study_id"] for i in _ok(client.get(f"{BASE}/queue", params={"view": "pilot", "limit": 200}))["items"]]


def _decision(study: str, outcome: str = "INCLUDE", **extra) -> dict:
    out = {
        "event_id": str(uuid.uuid4()), "study_id": study, "screener_id": "researcher:local", "method": "HUMAN",
        "outcome": outcome, "reason_code": "EXC-01" if outcome == "EXCLUDE" else None, "note": None,
        "criteria": [], "decided_at": "2026-11-21T10:00:00.000Z", "device": "desktop", "supersedes": None,
    }
    out.update(extra)
    return out


def _decide(client: TestClient, pilot_id: str, decisions: list[dict]) -> list[dict]:
    return _ok(client.post(f"{BASE}/pilot/{pilot_id}/decisions", json={"decisions": decisions}))["results"]


def _main_event(client: TestClient, study: str, outcome: str = "INCLUDE", **extra) -> dict:
    binding = client.get(f"{BASE}/records/{study}").json()["binding"]
    event = {**_decision(study, outcome, **extra), "proposal_shown": None, "binding": binding}
    return event


def _post_main(client: TestClient, events: list[dict]) -> list[dict]:
    return _ok(client.post(f"{BASE}/decisions/events", json={"events": events}))["results"]


def _draft(ws: Path, study: str, answers: dict[str, str], created_at: str = "2026-11-21T11:00:00Z") -> dict:
    context = ev.load_context(ws)
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    return pr.submit_proposal(
        ws, study_id=study, title="t", abstract="a",
        output={"criteria": [{"id": k, "answer": v, "evidence": {"text": "", "start": 0, "end": 0}} for k, v in answers.items()],
                "cannot_decide": False},
        protocol=protocol, protocol_fingerprint=context.protocol_fingerprint,
        provenance={"task_version": "screen-v1", "model": "m", "prompt_sha256": api.PROMPT}, created_at=created_at)


# --- DoD 11: the draw -----------------------------------------------------------------------


def test_dod11_the_dry_call_answers_n_the_pool_and_the_time_and_writes_nothing(ws, client):
    before = (ws / "audit" / "journal.jsonl").read_bytes()
    dry = _ok(client.post(f"{BASE}/pilot", json={"n": 50, "confirm": False}))
    assert dry == {"recorded": False, "n": 50, "available": RECORDS, "expected_minutes": 25}
    assert not (ws / pl.PILOT_DIR).exists()
    assert (ws / "audit" / "journal.jsonl").read_bytes() == before


def test_dod11_a_draw_writes_the_file_and_one_journal_row(ws, client):
    drawn = _draw(client, 30)
    assert (drawn["recorded"], drawn["pilot_id"], drawn["n"]) == (True, "pilot_001", 30)
    record = json.loads((ws / pl.PILOT_DIR / "pilot_001.json").read_text(encoding="utf-8"))
    assert record["seed"] == drawn["seed"] and record["n"] == 30 and len(record["records"]) == 30
    assert record["snapshot_id"] and record["protocol_fingerprint"] == ev.load_context(ws).protocol_fingerprint
    assert record["criteria_version"] == 1 and record["drawn_by"] == "researcher:local" and record["drawn_at"]
    assert all(set(r) == {"study_id", "batch_id"} for r in record["records"])
    [row] = [r for r in _journal(ws) if r["action"] == pl.DRAWN_ACTION]
    assert (row["parameters"]["pilot_id"], row["parameters"]["n"], row["parameters"]["seed"]) == ("pilot_001", 30, drawn["seed"])


def test_dod11_the_same_seed_on_the_same_snapshot_gives_the_same_list(tmp_path):
    first = _workspace(tmp_path / "a")
    second = _workspace(tmp_path / "b")
    a = pl.draw(first, n=20, confirm=True, drawn_by="r", seed=12345)
    b = pl.draw(second, n=20, confirm=True, drawn_by="r", seed=12345)
    list_a = [r["study_id"] for r in pl.read_draw(first, a["pilot_id"])["records"]]
    list_b = [r["study_id"] for r in pl.read_draw(second, b["pilot_id"])["records"]]
    assert list_a == list_b and len(set(list_a)) == 20
    third = _workspace(tmp_path / "c")
    other = pl.draw(third, n=20, confirm=True, drawn_by="r", seed=54321)
    assert [r["study_id"] for r in pl.read_draw(third, other["pilot_id"])["records"]] != list_a


def test_dod11_records_with_a_main_decision_or_in_an_earlier_pilot_are_not_drawn(ws, client):
    order = [i["study_id"] for i in _ok(client.get(f"{BASE}/queue", params={"view": "needs_you", "limit": 200}))["items"]]
    _post_main(client, [_main_event(client, s) for s in order[:5]])
    first = _draw(client, 20)
    in_first = set(_pilot_records(client))
    assert not in_first & set(order[:5])
    _ok(client.post(f"{BASE}/pilot/{first['pilot_id']}/close"))
    dry = _ok(client.post(f"{BASE}/pilot", json={"n": 20, "confirm": False}))
    assert dry["available"] == RECORDS - 5 - 20
    second = _draw(client, 20)
    in_second = {r["study_id"] for r in pl.read_draw(ws, second["pilot_id"])["records"]}
    assert not in_second & (in_first | set(order[:5]))


@pytest.mark.parametrize("n", [10, 25, 110, 0])
def test_dod11_a_size_outside_20_to_100_in_tens_is_refused(client, n):
    response = client.post(f"{BASE}/pilot", json={"n": n, "confirm": False})
    assert (response.status_code, _code(response)) == (422, "PILOT_SIZE_INVALID")


def test_dod11_more_than_the_records_left_is_refused(client):
    response = client.post(f"{BASE}/pilot", json={"n": 70, "confirm": True})
    assert (response.status_code, _code(response)) == (422, "PILOT_SIZE_INVALID")
    assert response.json()["detail"]["details"]["available"] == RECORDS


def test_dod11_refused_before_batches_after_approval_and_while_a_pilot_is_open(tmp_path, ws, client):
    unprepared = _client(_workspace(tmp_path / "u", prepare=False))
    response = unprepared.post(f"{BASE}/pilot", json={"n": 20, "confirm": True})
    assert (response.status_code, _code(response)) == (409, "BATCHES_NOT_PREPARED")
    _draw(client, 20)
    response = client.post(f"{BASE}/pilot", json={"n": 20, "confirm": False})
    assert (response.status_code, _code(response)) == (409, "PILOT_OPEN")
    assert response.json()["detail"]["details"] == {"pilot_id": "pilot_001", "undecided": 20}
    approvals = ws / "literature" / "screening" / "approvals"
    approvals.mkdir(parents=True)
    (approvals / "batch_001_approval.json").write_text("{}", encoding="utf-8")
    assert _code(client.post(f"{BASE}/pilot", json={"n": 20, "confirm": True})) == "CRITERIA_AMENDMENT_AFTER_APPROVAL"
    for code in ("PILOT_OPEN", "PILOT_RECORD_UNKNOWN", "PILOT_CLOSED", "PILOT_NOT_FOUND", "PILOT_SIZE_INVALID"):
        assert code in CONSOLE_REFUSALS


def test_dod11_the_pilot_routes_are_desktop_only(client):
    _draw(client, 20)
    for method, path, payload in (
        ("POST", f"{BASE}/pilot", {"n": 20, "confirm": False}),
        ("POST", f"{BASE}/pilot/pilot_001/decisions", {"decisions": []}),
        ("POST", f"{BASE}/pilot/pilot_001/close", None),
        ("GET", f"{BASE}/pilot/pilot_001/result", None),
    ):
        response = client.request(method, path, json=payload, headers={"Authorization": f"Bearer {PHONE}"})
        assert response.status_code == 403 and _code(response) == "TOKEN_SCOPE_REFUSED", path


# --- DoD 11b: the summary block ----------------------------------------------------------------


def test_dod11b_the_summary_names_the_open_or_last_pilot(client):
    assert _ok(client.get(f"{BASE}/summary"))["pilot"] is None
    drawn = _draw(client, 20)
    records = _pilot_records(client)
    _decide(client, drawn["pilot_id"], [_decision(records[0])])
    block = _ok(client.get(f"{BASE}/summary"))["pilot"]
    assert block == {"pilot_id": "pilot_001", "n": 20, "decided": 1, "open": True, "closed_at": None,
                     "closed_reason": None, "pilots": 1, "recheck": 0}
    _ok(client.post(f"{BASE}/pilot/pilot_001/close"))
    block = _ok(client.get(f"{BASE}/summary"))["pilot"]
    assert (block["open"], block["closed_reason"]) == (False, "ended") and block["closed_at"]


# --- DoD 11c: pilot decisions are kept apart and never counted ------------------------------------


def test_dod11c_a_pilot_decision_is_a_line_of_its_own_file_with_engine_fields(ws, client):
    drawn = _draw(client, 20)
    study = _pilot_records(client)[0]
    decision = _decision(study, "EXCLUDE", criteria=[{"id": "INC-01", "answer": "not_reported"}])
    [result] = _decide(client, drawn["pilot_id"], [decision])
    assert result["result"] == "accepted" and result["pilot_decision_id"].startswith("PLD-")
    assert len(result["pilot_decision_id"]) == 28
    [stored] = pl.read_decisions(ws, "pilot_001")
    assert stored["pilot_decision_id"] == result["pilot_decision_id"] and stored["pilot_id"] == "pilot_001"
    assert stored["criteria_version"] == 1 and stored["received_at"]
    assert stored["protocol_fingerprint"] == ev.load_context(ws).protocol_fingerprint
    assert "binding" not in stored
    # A replay is a duplicate; the same id with other content is refused.
    assert _decide(client, drawn["pilot_id"], [decision])[0]["result"] == "duplicate"
    changed = {**decision, "outcome": "INCLUDE", "reason_code": None}
    assert _decide(client, drawn["pilot_id"], [changed])[0]["refusal"]["code"] == "IDEMPOTENCY_CONFLICT"
    [row] = [r for r in _journal(ws) if r["action"] == pl.RECEIVED_ACTION]
    assert row["metrics"]["decisions"] == 1 and "outcome" not in json.dumps(row["parameters"])


@pytest.mark.parametrize(
    ("override", "code"),
    [
        ({"outcome": "EXCLUDE", "reason_code": "EXC-99"}, "REASON_CODE_INVALID"),
        ({"outcome": "EXCLUDE", "reason_code": "EXC-01", "criteria": [{"id": "EXC-01", "answer": "no"}]},
         "REASON_CODE_INCONSISTENT"),
        ({"criteria_version": 2}, "INVALID_OUTPUT"),
        ({"pilot_decision_id": "PLD-x"}, "INVALID_OUTPUT"),
        ({"binding": {}}, "INVALID_OUTPUT"),
        ({"event_id": "not-a-uuid"}, "INVALID_OUTPUT"),
        ({"decided_at": "2099-01-01T00:00:00Z"}, "PROVENANCE_MISSING"),
        ({"note": "x" * 2001}, "INVALID_OUTPUT"),
        ({"supersedes": "PLD-000000000000000000000000"}, "INVALID_OUTPUT"),
    ],
)
def test_dod11c_the_event_intakes_checks_apply(client, override, code):
    drawn = _draw(client, 20)
    study = _pilot_records(client)[0]
    [result] = _decide(client, drawn["pilot_id"], [{**_decision(study), **override}])
    assert result["result"] == "refused" and result["refusal"]["code"] == code


def test_dod11c_a_retired_reason_is_refused_in_the_pilot(ws, client):
    drawn = _draw(client, 20)
    _ok(client.post(f"{BASE}/criteria/amendments", json={
        "op": "add", "side": "exclusion", "text": "Simulation-only studies", "reason": "r", "confirm": True}))
    _ok(client.post(f"{BASE}/criteria/amendments", json={
        "op": "remove", "side": "exclusion", "ids": ["EXC-01"], "reason": "r", "confirm": True}))
    study = _pilot_records(client)[0]
    [result] = _decide(client, drawn["pilot_id"], [_decision(study, "EXCLUDE", reason_code="EXC-01")])
    assert result["refusal"]["code"] == "REASON_CODE_RETIRED"
    [ok] = _decide(client, drawn["pilot_id"], [_decision(study, "EXCLUDE", reason_code="EXC-02")])
    assert ok["result"] == "accepted"
    assert pl.read_decisions(ws, "pilot_001")[0]["criteria_version"] == 3


def test_dod11c_a_record_outside_the_pilot_and_an_unknown_pilot_are_refused(client):
    drawn = _draw(client, 20)
    pilot = set(_pilot_records(client))
    outside = next(i["study_id"] for i in _ok(client.get(f"{BASE}/queue", params={"view": "needs_you", "limit": 200}))["items"]
                   if i["study_id"] not in pilot)
    [result] = _decide(client, drawn["pilot_id"], [_decision(outside)])
    assert result["refusal"]["code"] == "PILOT_RECORD_UNKNOWN"
    response = client.post(f"{BASE}/pilot/pilot_009/decisions", json={"decisions": []})
    assert (response.status_code, _code(response)) == (404, "PILOT_NOT_FOUND")


def test_dod11c_pilot_decisions_reach_no_counted_reader(ws, client):
    """A workspace whose only decisions are pilot decisions: 0 decided, nothing approvable,
    nothing collected, an empty agreement, no batch decisions file."""
    from scholar_harness.screening.collector import cmd_collect

    drawn = _draw(client, 20)
    records = _pilot_records(client)
    _decide(client, drawn["pilot_id"], [_decision(s, "EXCLUDE" if i % 2 else "INCLUDE") for i, s in enumerate(records)])
    for s in records:
        _draft(ws, s, {"INC-01": "yes", "EXC-01": "no"})
    summary = _ok(client.get(f"{BASE}/summary"))
    assert (summary["decided"], summary["by_outcome"]) == (0, {"INCLUDE": 0, "EXCLUDE": 0, "MAYBE": 0})
    assert ev.read_events(ws) == []
    assert not list((ws / "literature" / "screening").glob("batch_*_decisions.json"))
    assert _ok(client.get(f"{BASE}/queue", params={"view": "decided"}))["items"] == []
    agreement = _ok(client.get(f"{BASE}/agreement"))
    assert (agreement["decided_with_proposal"], agreement["table_2x2"]["both_include"]) == (0, 0)
    preview = _ok(client.get(f"{BASE}/prisma/preview"))
    assert preview["excluded"]["total"] == 0 and preview["included"] == 0
    # Nothing approvable: no batch has a decisions file, so its coverage is empty (review F8).
    from scholar_harness.screening.integrity import ScreeningIntegrityRefused, check_exact_coverage

    for batch in ev.load_context(ws).batches.values():
        with pytest.raises(ScreeningIntegrityRefused) as refused:
            check_exact_coverage(set(batch.candidates), [])
        assert refused.value.code == "COVERAGE_INCOMPLETE"
    with pytest.raises(RuntimeError, match=r"missing, invalid, or rejected decision artifacts for batches \[1, 2, 3\]"):
        cmd_collect(ws)
    assert not (ws / "literature" / "screening" / "generation.json").exists()


# --- DoD 11d: the open pilot's records, closing, blind return ---------------------------------------


def test_dod11d_a_main_decision_on_an_open_pilot_record_is_refused(client):
    _draw(client, 20)
    study = _pilot_records(client)[0]
    [result] = _post_main(client, [_main_event(client, study)])
    assert result["result"] == "refused" and result["refusal"]["code"] == "PILOT_OPEN"
    # The open pilot's records are out of the main queue.
    main = {i["study_id"] for i in _ok(client.get(f"{BASE}/queue", params={"view": "needs_you", "limit": 200}))["items"]}
    assert study not in main and len(main) == RECORDS - 20


def test_dod11d_ending_the_pilot_returns_its_records_blind_to_the_pilot_decision(ws, client):
    drawn = _draw(client, 20)
    records = _pilot_records(client)
    _decide(client, drawn["pilot_id"], [_decision(records[0], "EXCLUDE"), _decision(records[1], "INCLUDE")])
    closed = _ok(client.post(f"{BASE}/pilot/{drawn['pilot_id']}/close"))
    assert (closed["open"], closed["closed_reason"], closed["decided"]) == (False, "ended", 2)
    [row] = [r for r in _journal(ws) if r["action"] == pl.CLOSED_ACTION]
    assert row["parameters"]["reason"] == "ended" and row["metrics"] == {"n": 20, "decided": 2}
    # Every pilot record is an ordinary undecided record of the main screening again.
    main = [i for i in _ok(client.get(f"{BASE}/queue", params={"view": "needs_you", "limit": 200}))["items"]]
    assert {i["study_id"] for i in main} >= set(records)
    item = next(i for i in main if i["study_id"] == records[0])
    assert item["decided"] is False and "pilot" not in json.dumps(item).lower()
    detail = _ok(client.get(f"{BASE}/records/{records[0]}"))
    assert detail["my_decision"] is None and detail["history"] == []
    assert "pilot" not in json.dumps(detail).lower() and "PLD-" not in json.dumps(detail)
    [accepted] = _post_main(client, [_main_event(client, records[0], "INCLUDE")])
    assert accepted["result"] == "accepted"  # no conflict with the pilot decision
    # A closed pilot takes no more decisions; a replay of a stored one is still a duplicate.
    [refused] = _decide(client, drawn["pilot_id"], [_decision(records[2])])
    assert refused["refusal"]["code"] == "PILOT_CLOSED"
    assert _code(client.post(f"{BASE}/pilot/{drawn['pilot_id']}/close")) == "PILOT_CLOSED"


def test_dod11d_a_pilot_closes_by_itself_when_its_last_record_is_decided(ws, client):
    drawn = _draw(client, 20)
    records = _pilot_records(client)
    _decide(client, drawn["pilot_id"], [_decision(s) for s in records])
    closure = json.loads((ws / pl.PILOT_DIR / "pilot_001_closed.json").read_text(encoding="utf-8"))
    assert closure["reason"] == "complete" and closure["decided"] == 20
    assert _ok(client.get(f"{BASE}/summary"))["pilot"]["open"] is False
    assert _ok(client.post(f"{BASE}/pilot", json={"n": 20, "confirm": False}))["available"] == RECORDS - 20


# --- DoD 12: the pilot queue ----------------------------------------------------------------------


def test_dod12_the_pilot_view_lists_the_drawn_records_in_drawn_order(ws, client):
    drawn = _draw(client, 20)
    order = [r["study_id"] for r in pl.read_draw(ws, drawn["pilot_id"])["records"]]
    body = _ok(client.get(f"{BASE}/queue", params={"view": "pilot", "limit": 200}))
    assert [i["study_id"] for i in body["items"]] == order
    assert body["pilot"] == {"pilot_id": "pilot_001", "open": True} and body["checklist_default"] == "collapsed"
    _decide(client, drawn["pilot_id"], [_decision(order[3])])
    items = _ok(client.get(f"{BASE}/queue", params={"view": "pilot", "limit": 200}))["items"]
    assert [i["decided"] for i in items][:5] == [False, False, False, True, False]


def test_dod12_the_pilot_view_is_empty_without_a_pilot(client):
    body = _ok(client.get(f"{BASE}/queue", params={"view": "pilot"}))
    assert (body["items"], body["pilot"]) == ([], None)


# --- DoD 13: the result --------------------------------------------------------------------------------


def test_dod13_from_the_decisions_alone_three_readings_and_the_four_it_could_not_compute(ws, client):
    drawn = _draw(client, 20)
    records = _pilot_records(client)
    # 12 Exclude on EXC-01, 6 Unclear, 2 Include: many Unclear (30%), EXC-01 does most of the work,
    # INC-01 never used (weaker form: no answers per criterion).
    decisions = [_decision(s, "EXCLUDE") for s in records[:12]] + [_decision(s, "MAYBE") for s in records[12:18]] + [
        _decision(s, "INCLUDE") for s in records[18:]]
    _decide(client, drawn["pilot_id"], decisions)
    result = _ok(client.get(f"{BASE}/pilot/pilot_001/result"))
    assert (result["decided"], result["n"], result["counted"]) == (20, 20, False)
    assert result["by_outcome"] == {"INCLUDE": 2, "MAYBE": 6, "EXCLUDE": 12}
    rows = {r["id"]: r for r in result["criteria"]}
    assert rows["EXC-01"]["exclusions"] == {"count": 12, "of": 12}
    assert rows["INC-01"]["exclusions"] == {"count": 0, "of": 12}
    assert rows["EXC-01"]["checklist_not_reported"] is None and rows["EXC-01"]["draft_not_reported"] is None
    kinds = {(o["kind"], tuple(o["criteria"])) for o in result["observations"]}
    assert kinds == {("many_unclear", ()), ("does_most_work", ("EXC-01",)), ("never_used", ("INC-01",))}
    assert next(o for o in result["observations"] if o["kind"] == "never_used")["form"] == "weaker"
    assert {n["kind"] for n in result["not_computed"]} == {"hard_to_judge", "fire_together", "mirrored_pair", "read_differently"}
    assert [r["study_id"] for r in result["records"]] == records and result["records"][0]["title"].startswith("Corpus record")


def test_dod13_with_the_agent_check_the_mirror_and_the_unreadable_criterion_show(ws, client):
    drawn = _draw(client, 20)
    records = _pilot_records(client)
    decisions = []
    for i, s in enumerate(records):
        if i < 10:  # the agent answers EXC-01 yes exactly when INC-01 no: a mirrored pair
            _draft(ws, s, {"INC-01": "no", "EXC-01": "yes"})
            decisions.append(_decision(s, "EXCLUDE"))
        else:  # INC-01 not reported in the abstract
            _draft(ws, s, {"INC-01": "not_reported", "EXC-01": "no"})
            decisions.append(_decision(s, "INCLUDE"))
    _decide(client, drawn["pilot_id"], decisions)
    result = _ok(client.get(f"{BASE}/pilot/pilot_001/result"))
    rows = {r["id"]: r for r in result["criteria"]}
    assert rows["INC-01"]["draft_not_reported"] == {"count": 10, "of": 20}
    # Include implies INC-01 met; the draft says not_reported there (not compared); on the ten
    # Excludes citing EXC-01, INC-01 is implied nothing, so INC-01 is never compared.
    assert rows["EXC-01"]["read_differently"] == {"count": 0, "of": 20, "source": "implied"}
    kinds = {(o["kind"], tuple(o["criteria"])) for o in result["observations"]}
    assert ("mirrored_pair", ("EXC-01", "INC-01")) in kinds
    assert ("hard_to_judge", ("INC-01",)) in kinds
    assert {n["kind"] for n in result["not_computed"]} == set()
    # Answer 11: counts only, never one record's draft.
    text = json.dumps(result)
    for key in ("derived_outcome", "proposal_id", "evidence", '"answers"'):
        assert key not in text, key
    assert set(result["records"][0]) == {"study_id", "outcome", "reason_code", "criteria_version", "title"}


def test_dod13_read_differently_against_checklist_answers(ws, client):
    drawn = _draw(client, 20)
    records = _pilot_records(client)
    decisions = []
    for i, s in enumerate(records):
        _draft(ws, s, {"INC-01": "yes", "EXC-01": "no"})
        answer = "no" if i < 6 else "yes"  # the researcher's checklist disagrees on INC-01 in 6 of 20
        decisions.append(_decision(s, "MAYBE", criteria=[{"id": "INC-01", "answer": answer}]))
    _decide(client, drawn["pilot_id"], decisions)
    rows = {r["id"]: r for r in _ok(client.get(f"{BASE}/pilot/pilot_001/result"))["criteria"]}
    assert rows["INC-01"]["read_differently"] == {"count": 6, "of": 20, "source": "answers"}
    assert rows["INC-01"]["checklist_not_reported"] == {"count": 0, "of": 20}
    result = _ok(client.get(f"{BASE}/pilot/pilot_001/result"))
    assert ("read_differently", ("INC-01",)) in {(o["kind"], tuple(o["criteria"])) for o in result["observations"]}


def test_dod13_a_second_pilot_has_the_first_beside_it(ws, client):
    first = _draw(client, 20)
    _decide(client, first["pilot_id"], [_decision(s, "EXCLUDE") for s in _pilot_records(client)])
    second = _draw(client, 20)
    _decide(client, second["pilot_id"], [_decision(s) for s in _pilot_records(client)[:5]])
    result = _ok(client.get(f"{BASE}/pilot/{second['pilot_id']}/result"))
    assert result["previous"]["pilot_id"] == "pilot_001" and result["previous"]["by_outcome"]["EXCLUDE"] == 20
    assert result["decided"] == 5 and result["open"] is True
    assert _ok(client.get(f"{BASE}/pilot/pilot_001/result"))["previous"] is None
    assert _code(client.get(f"{BASE}/pilot/pilot_007/result")) == "PILOT_NOT_FOUND"


def test_dod13_a_revision_during_the_pilot_labels_the_versions_and_shows_nothing_again(ws, client):
    drawn = _draw(client, 20)
    records = _pilot_records(client)
    _decide(client, drawn["pilot_id"], [_decision(s, "EXCLUDE") for s in records[:5]])
    answer = _ok(client.post(f"{BASE}/criteria/amendments", json={
        "op": "reword", "side": "exclusion", "ids": ["EXC-01"], "text": "Malformed documents", "reason": "r", "confirm": True}))
    assert answer["shown_again"]["total"] == 0 and answer["amendment"]["pilot_id"] == "pilot_001"
    _decide(client, drawn["pilot_id"], [_decision(s, "EXCLUDE") for s in records[5:8]])
    result = _ok(client.get(f"{BASE}/pilot/pilot_001/result"))
    assert result["criteria_versions_decided"] == [1, 2] and result["criteria_version"] == 2
    assert [r["criteria_version"] for r in result["records"][:8]] == [1] * 5 + [2] * 3
    assert _ok(client.get(f"{BASE}/queue", params={"view": "recheck"}))["items"] == []


# --- DoD 14: the agent check on the pilot ----------------------------------------------------------------


def test_dod14_the_agent_check_on_a_pilot_reads_its_labels_from_the_pilot_file(ws, client):
    drawn = _draw(client, 20)
    records = _pilot_records(client)
    _decide(client, drawn["pilot_id"], [_decision(s, "EXCLUDE" if i < 4 else "INCLUDE") for i, s in enumerate(records[:10])])
    body = {"pilot_id": drawn["pilot_id"], "provider": "anthropic", "model": "claude-haiku-5-5", "effort": "low"}
    # The consent comes from the run screen; record it once.
    from scholar_harness.screening import agent_runs as runs

    runs.record_consent(ws, "anthropic", model="claude-haiku-5-5", prompt_sha256=api.PROMPT, accepted_at=CONSENT["accepted_at"])
    started = _ok(client.post(f"{BASE}/proposals/calibrations", json=body))
    run = _ok(client.get(f"{BASE}/proposals/runs/{started['run_id']}"))
    assert run["kind"] == "calibration" and run["model"] == "claude-haiku-5-5" and run["records"] == 10
    assert run["calibration"]["compared"] == 10
    drafts = pr.read_proposals(ws)
    assert {p["study_id"] for p in drafts} == set(records[:10]) and {p["pilot_id"] for p in drafts} == {"pilot_001"}
    # The pilot result now has its agent columns (counts only).
    rows = {r["id"]: r for r in _ok(client.get(f"{BASE}/pilot/pilot_001/result"))["criteria"]}
    assert rows["INC-01"]["draft_not_reported"]["of"] == 10
    # Records outside the pilot's decided ones are refused; without pilot_id the route is unchanged.
    response = client.post(f"{BASE}/proposals/calibrations", json={**body, "study_ids": [records[15]]})
    assert (response.status_code, _code(response)) == (422, "INVALID_OUTPUT")
    response = client.post(f"{BASE}/proposals/calibrations", json={k: v for k, v in body.items() if k != "pilot_id"})
    assert _code(response) == "BODY_INVALID"  # review F9: without pilot_id, study_ids is required, as before
    assert _code(client.post(f"{BASE}/proposals/calibrations", json={**body, "pilot_id": "pilot_009"})) == "PILOT_NOT_FOUND"


# --- DoD 15: the agreement denominator ---------------------------------------------------------------------


def test_dod15_splits_by_criterion_carry_answered_by_both(ws, client):
    queue = [i["study_id"] for i in _ok(client.get(f"{BASE}/queue", params={"view": "needs_you", "limit": 200}))["items"]]
    for s in queue[:3]:
        _draft(ws, s, {"INC-01": "yes", "EXC-01": "no"}, created_at="2026-11-21T09:00:00Z")
    _post_main(client, [
        _main_event(client, queue[0], "INCLUDE", criteria=[{"id": "INC-01", "answer": "no"}]),
        _main_event(client, queue[1], "INCLUDE", criteria=[{"id": "INC-01", "answer": "yes"}, {"id": "EXC-01", "answer": "no"}]),
        _main_event(client, queue[2], "INCLUDE"),
    ])
    body = _ok(client.get(f"{BASE}/agreement"))
    # Real splits only, each with its denominator (old clients read `n` as before) ...
    assert body["splits_by_criterion"] == [{"criterion_id": "INC-01", "n": 1, "answered_by_both": 2}]
    # ... and every criterion answered by both, split or not, in its own field (review F3).
    assert body["answered_by_both"] == [{"criterion_id": "EXC-01", "n": 1}, {"criterion_id": "INC-01", "n": 2}]


# --- the methods paragraph --------------------------------------------------------------------------------------


def test_methods_state_the_pilot_and_that_its_decisions_were_not_counted(tmp_path):
    from test_export_api import decide, publish, se
    from test_methods_api import _assert_numbers_trace, _methods

    workspace = se._build(tmp_path)
    # The events-test workspace has three records; a pilot needs 20, so its draw file is written by hand.
    studies = se._studies(workspace)
    context = ev.load_context(workspace)
    pilot_dir = workspace / pl.PILOT_DIR
    pilot_dir.mkdir(parents=True)
    (pilot_dir / "pilot_001.json").write_text(json.dumps({
        "pilot_id": "pilot_001", "seed": 777, "n": 3, "drawn_at": "2026-11-04T09:00:00Z", "drawn_by": "r",
        "criteria_version": 1, "protocol_fingerprint": context.protocol_fingerprint,
        "records": [{"study_id": s, "batch_id": context.batches[1].batch_id} for s in studies]}), encoding="utf-8")
    pl.intake(workspace, "pilot_001", [
        {**_decision(s), "screener_id": se.SCREENER, "decided_at": "2026-11-04T09:30:00.000Z"} for s in studies[:2]
    ], token_scope="desktop", received_at="2026-11-04T09:30:05Z")
    from scholar_harness.screening import criteria as cr

    cr.amend_criteria(
        workspace, op="reword", side="exclusion", ids=["EXC-01"], text="Malformed protocol documents",
        reason_category=None, reason_category_given=False, reason="Unclear in the pilot.", confirm=True,
        amended_by="r", amended_at="2026-11-04T09:35:00Z", pilot_id="pilot_001",
    )
    pl.close(workspace, "pilot_001", closed_by="r", closed_at="2026-11-04T09:40:00Z")
    decide(workspace)
    publish(workspace)
    body = _methods(workspace)
    assert "The screening criteria were piloted on 2 records (seed 777), drawn at random from the 3 records" in body["paragraph"]
    assert "The pilot decisions were not counted" in body["paragraph"]
    assert "It was made during the pilot, before the main screening." in body["paragraph"]
    assert body["paragraph"].index("piloted on") < body["paragraph"].index("criteria were amended")
    assert body["figures"]["pilots"] == [{"pilot_id": "pilot_001", "drawn": 3, "decided": 2, "seed": 777, "date": "2026-11-04"}]
    _assert_numbers_trace(body)


# --- review round 1 of part B ---------------------------------------------------------------------------


def _pilot_check(ws: Path, client: TestClient, driver) -> dict:
    from scholar_harness.screening import agent_runs as runs

    runs.record_consent(ws, "anthropic", model="claude-haiku-5-5", prompt_sha256=api.PROMPT, accepted_at=CONSENT["accepted_at"])
    started = _ok(client.post(f"{BASE}/proposals/calibrations", json={
        "pilot_id": "pilot_001", "provider": "anthropic", "model": "claude-haiku-5-5", "effort": "low"}))
    return _ok(client.get(f"{BASE}/proposals/runs/{started['run_id']}"))


class _ExcludingDriver(FakeDriver):
    """Answers EXC-01 yes on every record: a draft Exclude against a pilot Include."""

    def run(self, requests, spec, *, on_result=None, cancelled=lambda: False):
        from scholar_agent.drivers import DriverResult

        out = []
        for request in requests:
            ids = spec.schema["properties"]["criteria"]["items"]["properties"]["id"]["enum"]
            # A verbatim quote from every abstract, so the draft passes its checks and is an Exclude.
            answers = [{"id": i, "answer": "yes", "quote": "UAV weed mapping"} for i in ids]
            result = DriverResult(request.custom_id, "ok", output={"criteria": answers, "cannot_decide": False, "reasoning": "r"},
                                  usage=self.usage, model=spec.model)
            out.append(result)
            if on_result:
                on_result(result)
        return out


def test_review_f1_the_agent_check_on_a_pilot_names_no_record(ws):
    client = _client(ws, driver=_ExcludingDriver())
    drawn = _draw(client, 20)
    records = _pilot_records(client)
    _decide(client, drawn["pilot_id"], [_decision(s, "INCLUDE") for s in records[:10]])
    run = _pilot_check(ws, client, _ExcludingDriver())
    assert run["calibration"]["missed_includes_count"] == 10
    assert run["calibration"]["missed_includes"] == []
    setup = _ok(client.get(f"{BASE}/proposals/setup"))
    text = json.dumps([run, setup])
    assert not any(s in text for s in records), "a pilot record's id is in the answer"


def test_review_f1_a_main_calibration_still_names_its_missed_records(ws):
    from scholar_harness.screening import agent_runs as runs

    client = _client(ws, driver=_ExcludingDriver())
    queue = [i["study_id"] for i in _ok(client.get(f"{BASE}/queue", params={"view": "needs_you", "limit": 5}))["items"]]
    _post_main(client, [_main_event(client, s, "INCLUDE") for s in queue[:3]])
    runs.record_consent(ws, "anthropic", model="claude-haiku-5-5", prompt_sha256=api.PROMPT, accepted_at=CONSENT["accepted_at"])
    started = _ok(client.post(f"{BASE}/proposals/calibrations", json={
        "study_ids": queue[:3], "provider": "anthropic", "model": "claude-haiku-5-5", "effort": "low"}))
    calibration = _ok(client.get(f"{BASE}/proposals/runs/{started['run_id']}"))["calibration"]
    assert sorted(calibration["missed_includes"]) == sorted(queue[:3]) and calibration["missed_includes_count"] == 3


def test_review_f2_a_pilot_with_no_decision_is_not_in_the_methods(tmp_path):
    from scholar_harness.screening.export import _pilot_sentences

    ws = _workspace(tmp_path)
    drawn = pl.draw(ws, n=20, confirm=True, drawn_by="r", seed=1)
    pl.close(ws, drawn["pilot_id"], closed_by="r")
    assert _pilot_sentences(ws, None, RECORDS) == ([], [], [])


def test_review_f11_the_pilot_sentence_reads_well_for_one_record_and_three_pilots(tmp_path):
    from scholar_harness.screening import criteria as cr
    from scholar_harness.screening.export import _pilot_sentences

    ws = _workspace(tmp_path)
    for i, seed in enumerate((11, 22, 33)):
        drawn = pl.draw(ws, n=20, confirm=True, drawn_by="r", seed=seed, drawn_at=f"2026-11-2{i + 1}T08:00:00Z")
        studies = [r["study_id"] for r in pl.read_draw(ws, drawn["pilot_id"])["records"]]
        pl.intake(ws, drawn["pilot_id"], [_decision(s, decided_at=f"2026-11-2{i + 1}T08:30:00Z")
                                          for s in studies[: (1 if i == 0 else 2)]],
                  token_scope="desktop", received_at=f"2026-11-2{i + 1}T09:00:00Z")
        pl.close(ws, drawn["pilot_id"], closed_by="r", closed_at=f"2026-11-2{i + 1}T10:00:00Z")
        if i == 1:
            cr.amend_criteria(ws, op="add", side="exclusion", ids=[], text="Simulation-only studies", reason_category=None,
                              reason_category_given=False, reason="r", confirm=True, amended_by="r",
                              amended_at="2026-11-22T12:00:00Z")
    sentences, figures, _paths = _pilot_sentences(ws, None, RECORDS)
    assert sentences[0] == (
        "The screening criteria were piloted on 1 record (seed 11), on 2 more (seed 22) and on 2 more (seed 33) "
        f"after a revision of the criteria, drawn at random from the {RECORDS} records of the corpus."
    )
    assert [f["decided"] for f in figures] == [1, 2, 2]


def test_review_f3_old_clients_see_no_zero_split(ws, client):
    queue = [i["study_id"] for i in _ok(client.get(f"{BASE}/queue", params={"view": "needs_you", "limit": 5}))["items"]]
    _draft(ws, queue[0], {"INC-01": "yes", "EXC-01": "no"}, created_at="2026-11-21T09:00:00Z")
    _post_main(client, [_main_event(client, queue[0], "INCLUDE",
                                    criteria=[{"id": "INC-01", "answer": "yes"}, {"id": "EXC-01", "answer": "no"}])])
    body = _ok(client.get(f"{BASE}/agreement"))
    assert body["splits_by_criterion"] == []  # agreeing answers are not splits, as before
    assert body["answered_by_both"] == [{"criterion_id": "EXC-01", "n": 1}, {"criterion_id": "INC-01", "n": 1}]


def test_review_f4_readings_below_their_minimum_are_named(ws, client):
    drawn = _draw(client, 20)
    records = _pilot_records(client)
    _decide(client, drawn["pilot_id"], [_decision(s, "MAYBE") for s in records[:5]])
    result = _ok(client.get(f"{BASE}/pilot/pilot_001/result"))
    assert result["observations"] == []
    short = {n["kind"]: n for n in result["not_computed"] if "min" in n}
    assert short["many_unclear"] == {"kind": "many_unclear", "needs": ["decisions"], "have": 5, "min": 10}
    assert short["never_used"]["min"] == 10 and short["does_most_work"] == {
        "kind": "does_most_work", "needs": ["exclusions"], "have": 0, "min": 5}


def test_review_f5_never_used_takes_its_full_form_only_for_an_answered_criterion(ws, client):
    drawn = _draw(client, 20)
    records = _pilot_records(client)
    decisions = [_decision(s, "INCLUDE") for s in records[:12]]
    decisions[0]["criteria"] = [{"id": "EXC-01", "answer": "no"}]  # one answer, on EXC-01 only
    _decide(client, drawn["pilot_id"], decisions)
    never = {o["criteria"][0]: o for o in _ok(client.get(f"{BASE}/pilot/pilot_001/result"))["observations"]
             if o["kind"] == "never_used"}
    assert never["EXC-01"]["form"] == "full" and never["EXC-01"]["counts"]["answered"] == 1
    assert never["INC-01"]["form"] == "weaker"


def test_review_f6_a_draw_is_refused_while_a_batch_was_decided_through_the_handoff(tmp_path):
    import test_screening_actions as sa

    workspace, _studies = sa._scaffold(tmp_path)
    sa.run_recommend(workspace, 1, produced_at=sa.NOW)
    with pytest.raises(pl.PilotRefused) as refused:
        pl.draw(workspace, n=20, confirm=False, drawn_by="r")
    assert refused.value.code == "CRITERIA_AMENDMENT_HANDOFF"


def test_review_f7_a_second_pilot_decision_must_supersede_the_first(ws, client):
    drawn = _draw(client, 20)
    study = _pilot_records(client)[0]
    [first] = _decide(client, drawn["pilot_id"], [_decision(study, "EXCLUDE")])
    [second] = _decide(client, drawn["pilot_id"], [_decision(study, "INCLUDE")])
    assert second["result"] == "refused" and second["refusal"]["code"] == "INVALID_OUTPUT"
    assert first["pilot_decision_id"] in second["refusal"]["message"]
    [change] = _decide(client, drawn["pilot_id"], [_decision(study, "INCLUDE", supersedes=first["pilot_decision_id"])])
    assert change["result"] == "accepted"
    rows = {r["study_id"]: r for r in _ok(client.get(f"{BASE}/pilot/pilot_001/result"))["records"]}
    assert rows[study]["outcome"] == "INCLUDE"


def test_review_f10_the_pilot_view_is_desktop_only(client):
    _draw(client, 20)
    response = client.get(f"{BASE}/queue", params={"view": "pilot"}, headers={"Authorization": f"Bearer {PHONE}"})
    assert response.status_code == 403 and _code(response) == "TOKEN_SCOPE_REFUSED"
    assert client.get(f"{BASE}/queue", params={"view": "needs_you"}, headers={"Authorization": f"Bearer {PHONE}"}).status_code == 200


def test_followup_a_pilot_number_is_never_reused_even_if_a_draw_file_is_unreadable(ws, client):
    _draw(client, 20)
    _ok(client.post(f"{BASE}/pilot/pilot_001/close"))
    (ws / pl.PILOT_DIR / "pilot_001.json").write_text("{not json", encoding="utf-8")
    assert _draw(client, 20)["pilot_id"] == "pilot_002"


def test_followup_a_revision_records_the_pilot_open_at_that_moment(ws, client):
    drawn = _draw(client, 20)
    answer = _ok(client.post(f"{BASE}/criteria/amendments", json={
        "op": "add", "side": "exclusion", "text": "Simulation-only studies", "reason": "r", "confirm": True}))
    assert answer["amendment"]["pilot_id"] == drawn["pilot_id"]
    _ok(client.post(f"{BASE}/pilot/{drawn['pilot_id']}/close"))
    later = _ok(client.post(f"{BASE}/criteria/amendments", json={
        "op": "add", "side": "exclusion", "text": "Review articles", "reason": "r", "confirm": True}))
    assert later["amendment"]["pilot_id"] is None


def test_part_c_the_pilot_view_carries_your_pilot_decision_and_the_main_views_do_not(ws, client):
    drawn = _draw(client, 20)
    records = _pilot_records(client)
    [first] = _decide(client, drawn["pilot_id"], [_decision(records[0], "EXCLUDE")])
    items = {i["study_id"]: i for i in _ok(client.get(f"{BASE}/queue", params={"view": "pilot", "limit": 200}))["items"]}
    head = items[records[0]]["pilot_decision"]
    assert (head["pilot_decision_id"], head["outcome"], head["reason_code"]) == (first["pilot_decision_id"], "EXCLUDE", "EXC-01")
    assert items[records[1]]["pilot_decision"] is None
    _ok(client.post(f"{BASE}/pilot/{drawn['pilot_id']}/close"))
    main = _ok(client.get(f"{BASE}/queue", params={"view": "needs_you", "limit": 200}))["items"]
    assert all("pilot_decision" not in i for i in main)

