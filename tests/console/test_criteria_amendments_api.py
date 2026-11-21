"""M11b part A: the criteria in force and their amendments (DoD 1 to 10).

A criteria revision is an amendment beside the signed protocol (decision
2026-11-21, M11b items 1 to 4): ``protocol.json``, the corpus snapshot and the
batch files keep their bytes; the criteria in force are the signed list plus
the amendments under the current fingerprint; each amendment raises the
criteria version the engine stamps on every new decision event and draft; a
revision shows again the counted decisions it could change.

The workspace is the screening API test workspace (one batch of three records,
criteria INC-01 and EXC-01), driven through HTTP.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import test_screening_api_v1 as api
from fastapi.testclient import TestClient
from test_agent_runs_api import CONSENT, FakeDriver
from test_screening_api_v1 import BASE, DESKTOP, PHONE, _event, _post, _studies

from scholar_harness.console import create_app
from scholar_harness.console.refusals import CONSOLE_REFUSALS
from scholar_harness.screening import criteria as cr
from scholar_harness.screening import events as ev
from scholar_harness.screening import proposals as pr
from scholar_harness.screening.integrity import ScreeningIntegrityRefused, check_exact_coverage

INC_TEXT = "Formal research protocols declaring explicit research questions"
EXC_TEXT = "Non-canonical or malformed protocol documents"


def _client(ws: Path, driver=None) -> TestClient:
    app = create_app(ws, token=DESKTOP, phone_tokens={PHONE})
    app.state.driver_factory = lambda provider, key: driver or FakeDriver()
    app.state.run_executor = lambda fn: fn()
    return TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {DESKTOP}"})


@pytest.fixture
def ws(tmp_path) -> Path:
    workspace = api._workspace(tmp_path)
    (workspace / "SCREENING_CRITERIA.md").write_text("# Screening Criteria (signed)\n", encoding="utf-8")
    return workspace


@pytest.fixture
def client(ws) -> TestClient:
    return _client(ws)


def _amend(client: TestClient, op: str, side: str, ids=(), *, confirm=True, reason="Clearer after the pilot.", **extra):
    body = {"op": op, "side": side, "ids": list(ids), "confirm": confirm, **extra}
    if reason is not None:
        body["reason"] = reason
    return client.post(f"{BASE}/criteria/amendments", json=body)


def _ok(response) -> dict:
    assert response.status_code == 200, response.text
    return response.json()


def _code(response) -> str:
    return response.json()["detail"]["code"]


def _journal(ws: Path) -> list[dict]:
    return [json.loads(x) for x in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]


def _digests(ws: Path) -> dict[str, str]:
    """The bytes a revision must not touch: the protocol, the batch files, the registered artifacts."""
    paths = [ws / "protocol.json", *sorted((ws / "literature" / "screening").glob("batch_[0-9][0-9][0-9].json"))]
    registry = json.loads((ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8"))["artifacts"]
    paths += [ws / entry["path"] for entry in registry.values()]
    return {str(p.relative_to(ws)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def _stored(ws: Path) -> list[dict]:
    return ev.read_events(ws)


# --- DoD 1: one line, one journal row, protocol / snapshot / batches untouched ----


def test_dod1_a_revision_is_one_line_and_one_journal_row_and_touches_no_bound_artifact(ws, client):
    before = _digests(ws)
    fingerprint = ev.load_context(ws).protocol_fingerprint
    answer = _ok(_amend(client, "reword", "inclusion", ["INC-01"], text="Formal protocols with explicit research questions"))
    assert answer["recorded"] is True
    rows = [json.loads(x) for x in (ws / cr.AMENDMENTS_FILE).read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["amendment_id"].startswith("CRA-") and len(row["amendment_id"]) == 28
    assert (row["op"], row["side"], row["criteria_version_before"], row["criteria_version_after"]) == (
        "reword", "inclusion", 1, 2)
    assert row["from"][0]["text"] == INC_TEXT and row["to"][0]["text"].startswith("Formal protocols")
    assert row["protocol_fingerprint"] == fingerprint and row["reason"] == "Clearer after the pilot."
    assert row["amended_by"] == "researcher:local" and row["amended_at"] and row["pilot_id"] is None
    [journal] = [r for r in _journal(ws) if r["action"] == cr.AMENDED_ACTION]
    assert journal["parameters"]["amendment_id"] == row["amendment_id"]
    assert journal["parameters"]["from_ids"] == ["INC-01"] and journal["parameters"]["to_ids"] == ["INC-01"]
    assert journal["parameters"]["criteria_version_after"] == 2
    assert _digests(ws) == before  # protocol.json, the batch file, the snapshot keep their bytes
    assert ev.load_context(ws).protocol_fingerprint == fingerprint
    assert client.get(f"{BASE}/summary").json()["protocol_changed"] is False


def test_dod1_the_routes_are_desktop_only(client):
    for method, path, payload in (
        ("POST", f"{BASE}/criteria/amendments", {"op": "add", "side": "exclusion", "confirm": False, "text": "x"}),
        ("GET", f"{BASE}/criteria", None),
    ):
        response = client.request(method, path, json=payload, headers={"Authorization": f"Bearer {PHONE}"})
        assert response.status_code == 403 and _code(response) == "TOKEN_SCOPE_REFUSED"


# --- DoD 2: one reader, every reader moved (functional; the static list is in tests/unit) ---


def test_dod2_every_reader_takes_the_amended_wording(ws, client, monkeypatch):
    _ok(_amend(client, "reword", "inclusion", ["INC-01"], text="Reworded inclusion about UAV mapping"))
    _ok(_amend(client, "add", "exclusion", text="Simulation-only studies"))
    study = _studies(client)[0]
    # Triage's criteria and checklist (the record route).
    record = client.get(f"{BASE}/records/{study}").json()
    assert [(c["id"], c["text"]) for c in record["criteria"]] == [
        ("INC-01", "Reworded inclusion about UAV mapping"), ("EXC-01", EXC_TEXT), ("EXC-02", "Simulation-only studies")]
    assert record["criteria_version"] == 3
    assert [c["since_version"] for c in record["criteria"]] == [2, 1, 3]
    # The reason check at intake: the new exclusion is a valid reason.
    [result] = _post(client, [_event(client, study, "EXCLUDE", reason_code="EXC-02")])
    assert result["result"] == "accepted"
    # The agent run and its estimate build their prompt from the criteria in force.
    from scholar_agent import prompt_gate as pg

    seen: list[dict] = []
    real = pg.run_spec

    def spy(protocol, **kw):
        seen.append(protocol["screening_criteria"])
        return real(protocol, **kw)

    monkeypatch.setattr(pg, "run_spec", spy)
    estimate = client.post(f"{BASE}/proposals/runs", json={
        "provider": "anthropic", "model": "claude-haiku-5-5", "effort": "low", "estimate_only": True,
        "scope": {"study_ids": [study]}})
    assert estimate.status_code == 200, estimate.text
    assert [c["criterion"] for c in seen[-1]["inclusion"]] == ["Reworded inclusion about UAV mapping"]
    assert [c["id"] for c in seen[-1]["exclusion"]] == ["EXC-01", "EXC-02"]
    # The MCP record tool reads the criteria in force too.
    from scholar_agent import server

    monkeypatch.setenv("NEXUS_MCP_WORKSPACE", str(ws))
    mcp = json.loads(server.nexus_screening_record(study, workspace_dir=str(ws)))
    assert mcp["status"] == "SUCCESS", mcp
    assert [c["text"] for c in mcp["criteria"]][0] == "Reworded inclusion about UAV mapping"
    assert mcp["criteria_version"] == 3


def test_dod2_the_file_handoff_worker_refuses_once_the_criteria_are_amended(ws, client):
    from scholar_harness.screening.worker import WorkerRefused, run_recommend

    _ok(_amend(client, "reword", "exclusion", ["EXC-01"], text="Malformed protocol documents"))
    with pytest.raises(WorkerRefused) as refused:
        run_recommend(ws, 1)
    assert refused.value.code == cr.CRITERIA_AMENDED_USE_ENGINE


# --- DoD 3: ids --------------------------------------------------------------------


def test_dod3_reword_keeps_the_id_split_and_remove_retire_and_a_number_is_never_reused(ws, client):
    _ok(_amend(client, "add", "exclusion", text="Simulation-only studies"))  # EXC-02
    split = _ok(_amend(client, "split", "exclusion", ["EXC-01"], text=["Malformed documents", "Non-canonical documents"]))
    assert (split["new_ids"], split["retired_ids"]) == (["EXC-03", "EXC-04"], ["EXC-01"])
    reword = _ok(_amend(client, "reword", "exclusion", ["EXC-03"], text="Malformed protocol documents"))
    assert (reword["new_ids"], reword["retired_ids"]) == ([], [])
    removed = _ok(_amend(client, "remove", "exclusion", ["EXC-04"]))
    assert removed["retired_ids"] == ["EXC-04"]
    added = _ok(_amend(client, "add", "exclusion", text="Review articles"))
    assert added["new_ids"] == ["EXC-05"]  # after EXC-04, retired: never reused
    merged = _ok(_amend(client, "merge", "exclusion", ["EXC-02", "EXC-05"], text="Simulations or reviews"))
    assert (merged["new_ids"], merged["retired_ids"]) == (["EXC-06"], ["EXC-02", "EXC-05"])
    body = client.get(f"{BASE}/criteria").json()
    assert [c["id"] for c in body["criteria"]] == ["INC-01", "EXC-03", "EXC-06"]
    assert body["retired"] == ["EXC-01", "EXC-04", "EXC-02", "EXC-05"]
    assert body["criteria_version"] == 7


def test_dod3_a_retired_reason_is_refused_on_a_new_decision_and_stays_valid_on_earlier_ones(ws, client):
    studies = _studies(client)
    earlier = _event(client, studies[0], "EXCLUDE", reason_code="EXC-01")
    assert _post(client, [earlier])[0]["result"] == "accepted"
    _ok(_amend(client, "split", "exclusion", ["EXC-01"], text=["Malformed documents", "Non-canonical documents"]))
    [refused] = _post(client, [_event(client, studies[1], "EXCLUDE", reason_code="EXC-01")])
    assert refused["result"] == "refused" and refused["refusal"]["code"] == "REASON_CODE_RETIRED"
    assert "REASON_CODE_RETIRED" in CONSOLE_REFUSALS
    # The earlier event is a duplicate when replayed (the offline flush), never refused.
    assert _post(client, [earlier])[0]["result"] == "duplicate"
    # An unknown code is still REASON_CODE_INVALID.
    [unknown] = _post(client, [_event(client, studies[1], "EXCLUDE", reason_code="EXC-99")])
    assert unknown["refusal"]["code"] == "REASON_CODE_INVALID"
    # FAILS- a retired inclusion.
    _ok(_amend(client, "add", "inclusion", text="Peer-reviewed"))
    _ok(_amend(client, "remove", "inclusion", ["INC-01"]))
    [fails] = _post(client, [_event(client, studies[2], "EXCLUDE", reason_code="FAILS-INC-01")])
    assert fails["refusal"]["code"] == "REASON_CODE_RETIRED"
    assert _post(client, [_event(client, studies[2], "EXCLUDE", reason_code="FAILS-INC-02")])[0]["result"] == "accepted"


# --- DoD 4: the engine stamps the version --------------------------------------------


def test_dod4_events_and_drafts_carry_the_engine_stamped_version(ws, client):
    studies = _studies(client)
    _post(client, [_event(client, studies[0])])
    assert _stored(ws)[-1]["criteria_version"] == 1
    _ok(_amend(client, "reword", "exclusion", ["EXC-01"], text="Malformed protocol documents"))
    _post(client, [_event(client, studies[1], "EXCLUDE")])
    assert _stored(ws)[-1]["criteria_version"] == 2
    # A browser cannot send it.
    [refused] = _post(client, [_event(client, studies[2], criteria_version=5)])
    assert refused["result"] == "refused" and refused["refusal"]["code"] == "INVALID_OUTPUT"
    # An event stored without it reads as version 1.
    assert cr.event_version({"outcome": "INCLUDE"}) == 1
    # A draft is stamped too, and its id names the version from 2 on.
    context = ev.load_context(ws)
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    draft = pr.submit_proposal(
        ws, study_id=studies[2], title="t", abstract="a", output={"criteria": [], "cannot_decide": True},
        protocol=protocol, protocol_fingerprint=context.protocol_fingerprint,
        provenance={"task_version": "screen-v1", "model": "m", "prompt_sha256": api.PROMPT}, created_at="2026-11-21T10:00:00Z")
    assert draft["criteria_version"] == 2
    v1_id = pr.proposal_id("screen-v1", draft["input_sha256"], context.protocol_fingerprint, "m")
    assert draft["proposal_id"] != v1_id
    assert pr.proposal_id("screen-v1", draft["input_sha256"], context.protocol_fingerprint, "m", 1) == v1_id


def test_dod4_a_version_1_draft_id_is_unchanged_by_m11b():
    # The recipe of the screening API contract §2, for version 1: sha256 of the four fields.
    payload = json.dumps(["screen-v1", "sha256:abc", "sha256:fp", "model"], separators=(",", ":"))
    expected = "PRP-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]
    assert pr.proposal_id("screen-v1", "sha256:abc", "sha256:fp", "model") == expected


# --- DoD 5: shown again, the recheck view, the approval gate ---------------------------


def _decide_four_ways(client: TestClient) -> dict[str, str]:
    """INCLUDE, MAYBE, EXCLUDE citing EXC-01; the third record via FAILS-INC-01 is decided later."""
    studies = _studies(client)
    _post(client, [
        _event(client, studies[0], "INCLUDE"),
        _event(client, studies[1], "MAYBE"),
        _event(client, studies[2], "EXCLUDE", reason_code="EXC-01"),
    ])
    return {"include": studies[0], "maybe": studies[1], "exclude": studies[2]}


def test_dod5_a_reword_shows_again_include_unclear_and_excludes_citing_it_only(ws, client):
    ids = _decide_four_ways(client)
    # Rewording the inclusion: the Exclude cites EXC-01, untouched, so it still holds.
    dry = _ok(_amend(client, "reword", "inclusion", ["INC-01"], text="Explicit research questions", confirm=False))
    assert dry["recorded"] is False and dry["decided"] == 3
    assert dry["shown_again"] == {"INCLUDE": 1, "MAYBE": 1, "EXCLUDE": 0, "total": 2}
    assert not (ws / cr.AMENDMENTS_FILE).exists()  # the dry call writes nothing
    _ok(_amend(client, "reword", "inclusion", ["INC-01"], text="Explicit research questions"))
    recheck = client.get(f"{BASE}/queue", params={"view": "recheck"}).json()["items"]
    assert sorted(i["study_id"] for i in recheck) == sorted([ids["include"], ids["maybe"]])
    summary = client.get(f"{BASE}/summary").json()
    assert (summary["recheck"], summary["decided"], summary["needs_you"], summary["criteria_version"]) == (2, 1, 2, 2)
    # Rewording the exclusion now shows the Exclude again too.
    second = _ok(_amend(client, "reword", "exclusion", ["EXC-01"], text="Malformed protocol documents"))
    assert second["shown_again"] == {"INCLUDE": 0, "MAYBE": 0, "EXCLUDE": 1, "total": 1}
    assert second["waiting_after"] == 3


def test_dod5_an_added_criterion_shows_again_include_and_unclear_but_no_exclude(ws, client):
    _decide_four_ways(client)
    answer = _ok(_amend(client, "add", "exclusion", text="Simulation-only studies"))
    assert answer["shown_again"] == {"INCLUDE": 1, "MAYBE": 1, "EXCLUDE": 0, "total": 2}


def test_dod5_a_reason_category_change_shows_nothing_again(ws, client):
    _decide_four_ways(client)
    answer = _ok(_amend(client, "reason_category", "exclusion", ["EXC-01"], reason_category="WRONG_FORMAT"))
    assert answer["shown_again"]["total"] == 0
    assert client.get(f"{BASE}/criteria").json()["criteria"][1]["reason_category"] == "WRONG_FORMAT"


def test_dod5_a_batch_holding_a_record_shown_again_is_not_fully_decided(ws, client):
    ids = _decide_four_ways(client)
    projection = ws / "literature" / "screening" / "batch_001_decisions.json"
    assert len(json.loads(projection.read_text(encoding="utf-8"))["decisions"]) == 3
    _ok(_amend(client, "reword", "inclusion", ["INC-01"], text="Explicit research questions"))
    # The amendment rebuilt the decisions file: the two records shown again are out of it.
    entries = json.loads(projection.read_text(encoding="utf-8"))["decisions"]
    assert [e["workspace_id"] for e in entries] == [ids["exclude"]]
    assert ev.projection_is_current(ws, 1, projection)
    candidates = set(ev.load_context(ws).batches[1].candidates)
    with pytest.raises(ScreeningIntegrityRefused) as refused:
        check_exact_coverage(candidates, entries)
    assert refused.value.code == "COVERAGE_INCOMPLETE"


def test_dod5_a_record_shown_again_is_decided_again_by_a_superseding_event(ws, client):
    ids = _decide_four_ways(client)
    _ok(_amend(client, "reword", "inclusion", ["INC-01"], text="Explicit research questions"))
    record = client.get(f"{BASE}/records/{ids['include']}").json()
    earlier = record["shown_again"]["decision"]
    assert record["my_decision"] is None and record["shown_again"]["criteria_version"] == 1
    assert earlier["outcome"] == "INCLUDE"
    # A second head would leave the earlier decision in place: refused.
    [refused] = _post(client, [_event(client, ids["include"], "INCLUDE")])
    assert refused["result"] == "refused" and "supersede" in refused["refusal"]["message"]
    [accepted] = _post(client, [_event(client, ids["include"], "EXCLUDE", reason_code="FAILS-INC-01",
                                       supersedes=earlier["event_id"])])
    assert accepted["result"] == "accepted"
    recheck = client.get(f"{BASE}/queue", params={"view": "recheck"}).json()["items"]
    assert [i["study_id"] for i in recheck] == [ids["maybe"]]
    entries = json.loads((ws / "literature" / "screening" / "batch_001_decisions.json").read_text(encoding="utf-8"))
    decided = {e["workspace_id"]: e for e in entries["decisions"]}
    assert decided[ids["include"]]["decision"] == "EXCLUDE"
    assert decided[ids["include"]]["parent_decision_ids"]  # the earlier decision is its parent
    # Its earlier decision stays in the log.
    assert any(e["event_id"] == earlier["event_id"] for e in _stored(ws))


def test_dod5_a_published_screening_refuses_while_a_record_waits(tmp_path):
    from test_export_api import decide, publish, se

    workspace = se._build(tmp_path)
    decide(workspace)
    cr.amend_criteria(
        workspace, op="add", side="exclusion", ids=[], text="Simulation-only studies", reason_category=None,
        reason_category_given=False, reason="Found in the pilot.", confirm=True, amended_by="r", amended_at="2026-11-21T10:00:00Z",
    )
    # The two records shown again are out of the decisions file, so collect refuses it as incomplete
    # (review round 1, F8: the refusal names batch 1, and no projection is stale).
    assert ev.stale_projections(workspace) == []
    with pytest.raises(RuntimeError, match=r"missing, invalid, or rejected decision artifacts for batches \[1\]"):
        publish(workspace)
    assert not (workspace / "literature" / "screening" / "generation.json").exists()


# --- review round 1 -------------------------------------------------------------------------


def test_review_f1_a_batch_decided_through_the_file_handoff_blocks_a_revision(tmp_path):
    """F1: hand-off decisions are not in the event log; a revision could not show them again,
    and the batch would be approved under the old wording. The revision is refused instead."""
    import test_screening_actions as sa

    workspace, studies = sa._scaffold(tmp_path)
    sa._write_operator_context(workspace)
    sa.run_recommend(workspace, 1, produced_at=sa.NOW)
    sa._write_decisions(workspace, studies)  # decided through the hand-off, signed wording
    inc = cr.criteria_in_force(workspace).inclusion[0].id
    for confirm in (False, True):
        with pytest.raises(cr.AmendmentRefused) as refused:
            cr.amend_criteria(
                workspace, op="reword", side="inclusion", ids=[inc], text="A different test entirely",
                reason_category=None, reason_category_given=False, reason="probe", confirm=confirm,
                amended_by="r", amended_at="2026-11-21T10:00:00Z")
        assert (refused.value.code, refused.value.status) == ("CRITERIA_AMENDMENT_HANDOFF", 409)
    assert not (workspace / cr.AMENDMENTS_FILE).exists()
    assert cr.criteria_in_force(workspace).version == 1
    assert "CRITERIA_AMENDMENT_HANDOFF" in CONSOLE_REFUSALS


def test_review_f1_a_worker_recommendation_alone_blocks_a_revision(tmp_path):
    import test_screening_actions as sa

    workspace, _studies = sa._scaffold(tmp_path)
    sa.run_recommend(workspace, 1, produced_at=sa.NOW)
    assert cr.handoff_batches(workspace, ev.load_context(workspace)) == [1]


def test_review_f1_event_decided_batches_do_not_block_a_revision(ws, client):
    _decide_four_ways(client)
    assert cr.handoff_batches(ws, ev.load_context(ws)) == []
    _ok(_amend(client, "add", "exclusion", text="Simulation-only studies"))


def test_review_f2_a_reword_that_keeps_the_text_is_refused_and_points_to_reason_category(ws, client):
    _decide_four_ways(client)
    response = _amend(client, "reword", "exclusion", ["EXC-01"], text=EXC_TEXT, reason_category="WRONG_FORMAT")
    assert _code(response) == "CRITERIA_AMENDMENT_INVALID"
    assert "reason_category" in response.json()["detail"]["message"]
    assert not (ws / cr.AMENDMENTS_FILE).exists()


def test_review_f4_agreement_compares_a_decision_and_a_draft_of_the_same_version_only(ws, client):
    studies = _studies(client)
    _draft(ws, studies[0], "2026-11-21T09:00:00Z")
    first = _event(client, studies[0], "INCLUDE")
    _post(client, [first])  # decided under v1, before any reveal
    assert client.get(f"{BASE}/agreement").json()["decided_with_proposal"] == 1
    assert client.get(f"{BASE}/records/{studies[0]}/proposal").status_code == 200  # revealed
    _ok(_amend(client, "reword", "inclusion", ["INC-01"], text="Explicit research questions"))
    _post(client, [_event(client, studies[0], "INCLUDE", supersedes=first["event_id"])])  # decided again, v2
    _draft(ws, studies[0], "2026-11-21T11:00:00Z")  # a v2 draft
    # The only decision before the reveal is the v1 one: not compared with the v2 draft.
    body = client.get(f"{BASE}/agreement").json()
    assert body["decided_with_proposal"] == 0


def test_review_f5_a_split_takes_at_most_ten_texts(ws, client):
    response = _amend(client, "split", "exclusion", ["EXC-01"], text=[f"part {i}" for i in range(11)], confirm=False)
    assert _code(response) == "CRITERIA_AMENDMENT_INVALID"
    ten = _ok(_amend(client, "split", "exclusion", ["EXC-01"], text=[f"part {i}" for i in range(10)], confirm=False))
    assert len(ten["new_ids"]) == 10
    long_text = _ok(_amend(client, "reword", "exclusion", ["EXC-01"], text="x" * 40, confirm=False))
    assert long_text["recorded"] is False  # a single text is not capped at ten characters


def test_review_f7_validate_event_refuses_a_retired_reason(ws, client):
    _ok(_amend(client, "add", "exclusion", text="Simulation-only studies"))
    _ok(_amend(client, "remove", "exclusion", ["EXC-01"]))
    study = _studies(client)[0]
    refusal = ev.validate_event(_event(client, study, "EXCLUDE", reason_code="EXC-01"), ev.load_context(ws))
    assert refusal is not None and refusal["code"] == "REASON_CODE_RETIRED"
    assert ev.validate_event(_event(client, study, "EXCLUDE", reason_code="EXC-02"), ev.load_context(ws)) is None


# --- DoD 6 and 7: refusals and the dry call -----------------------------------------------


def test_dod6_refused_before_batches_exist(tmp_path):
    workspace = api._workspace(tmp_path, prepare="accept_only")
    response = _amend(_client(workspace), "add", "exclusion", text="x")
    assert (response.status_code, _code(response)) == (409, "CRITERIA_AMENDMENT_NO_BATCHES")


def test_dod6_refused_after_a_batch_is_approved(ws, client):
    approvals = ws / "literature" / "screening" / "approvals"
    approvals.mkdir(parents=True)
    (approvals / "batch_001_approval.json").write_text("{}", encoding="utf-8")
    response = _amend(client, "add", "exclusion", text="x")
    assert (response.status_code, _code(response)) == (409, "CRITERIA_AMENDMENT_AFTER_APPROVAL")
    assert client.get(f"{BASE}/criteria").json()["can_amend"] is False


def test_dod6_refused_in_a_later_screening_round(ws, client, monkeypatch):
    from scholar_harness.screening import rounds

    monkeypatch.setattr(rounds, "current_round", lambda _ws: {"round": 2})
    assert _code(_amend(client, "add", "exclusion", text="x")) == "CRITERIA_AMENDMENT_AFTER_APPROVAL"


@pytest.mark.parametrize(
    ("body", "why"),
    [
        ({"op": "reword", "side": "inclusion", "ids": ["INC-01"], "text": "x", "confirm": True}, "no reason"),
        ({"op": "reword", "side": "inclusion", "ids": ["INC-01"], "text": "x", "confirm": True, "reason": "  "}, "blank reason"),
        ({"op": "reword", "side": "inclusion", "ids": ["INC-01"], "text": "x", "reason": "r"}, "no confirm"),
        ({"op": "reword", "side": "inclusion", "ids": ["INC-09"], "text": "x", "reason": "r", "confirm": True}, "unknown id"),
        ({"op": "reword", "side": "exclusion", "ids": ["INC-01"], "text": "x", "reason": "r", "confirm": True}, "other side"),
        ({"op": "reword", "side": "inclusion", "ids": ["INC-01"], "text": INC_TEXT, "reason": "r", "confirm": True}, "no change"),
        ({"op": "rename", "side": "inclusion", "ids": ["INC-01"], "reason": "r", "confirm": True}, "unknown op"),
        ({"op": "split", "side": "inclusion", "ids": ["INC-01"], "text": "one", "reason": "r", "confirm": True}, "split one text"),
        ({"op": "merge", "side": "inclusion", "ids": ["INC-01"], "text": "m", "reason": "r", "confirm": True}, "merge one id"),
        ({"op": "add", "side": "exclusion", "text": EXC_TEXT, "reason": "r", "confirm": True}, "add a duplicate"),
        ({"op": "reword", "side": "inclusion", "ids": ["INC-01"], "text": "x", "reason": "r" * 501, "confirm": True}, "long reason"),
    ],
)
def test_dod6_invalid_revisions_are_refused_and_write_nothing(ws, client, body, why):
    before = (ws / "audit" / "journal.jsonl").read_bytes()
    response = client.post(f"{BASE}/criteria/amendments", json=body)
    assert response.status_code == 422, (why, response.text)
    assert _code(response) == "CRITERIA_AMENDMENT_INVALID", why
    assert not (ws / cr.AMENDMENTS_FILE).exists()
    assert (ws / "audit" / "journal.jsonl").read_bytes() == before


def test_dod6_a_retired_id_cannot_be_revised(ws, client):
    _ok(_amend(client, "add", "exclusion", text="Simulation-only studies"))
    _ok(_amend(client, "remove", "exclusion", ["EXC-01"]))
    response = _amend(client, "reword", "exclusion", ["EXC-01"], text="x")
    assert _code(response) == "CRITERIA_AMENDMENT_INVALID" and "retired" in response.json()["detail"]["message"]


def test_dod6_the_dry_call_answers_the_new_ids_and_writes_nothing(ws, client):
    before = {p: p.read_bytes() for p in (ws / "audit").rglob("*") if p.is_file()}
    dry = _ok(_amend(client, "split", "exclusion", ["EXC-01"], text=["A", "B"], confirm=False, reason=None))
    assert dry == {
        "recorded": False, "op": "split", "side": "exclusion", "new_ids": ["EXC-02", "EXC-03"], "retired_ids": ["EXC-01"],
        "criteria_version_before": 1, "criteria_version_after": 2, "decided": 0,
        "shown_again": {"INCLUDE": 0, "MAYBE": 0, "EXCLUDE": 0, "total": 0}, "waiting_after": 0,
    }
    assert {p: p.read_bytes() for p in (ws / "audit").rglob("*") if p.is_file()} == before
    assert (ws / "SCREENING_CRITERIA.md").read_text(encoding="utf-8") == "# Screening Criteria (signed)\n"


def test_dod7_a_revision_that_empties_a_side_is_refused(ws, client):
    for op, side, ids in (("remove", "exclusion", ["EXC-01"]), ("remove", "inclusion", ["INC-01"])):
        response = _amend(client, op, side, ids)
        assert (response.status_code, _code(response)) == (422, "CRITERIA_SIDE_EMPTY")
        assert _code(_amend(client, op, side, ids, confirm=False)) == "CRITERIA_SIDE_EMPTY"


# --- DoD 7b: the criteria route ------------------------------------------------------------


def test_dod7b_the_criteria_route_answers_the_criteria_in_force(ws, client):
    signed = client.get(f"{BASE}/criteria").json()
    assert signed["criteria_version"] == 1 and signed["retired"] == [] and signed["amendments"] == []
    assert signed["can_amend"] is True and signed["batches_prepared"] is True
    assert signed["criteria"] == [
        {"id": "INC-01", "side": "inclusion", "text": INC_TEXT, "reason_category": None, "since_version": 1},
        {"id": "EXC-01", "side": "exclusion", "text": EXC_TEXT, "reason_category": "INVALID_FORMAT", "since_version": 1},
    ]
    _ok(_amend(client, "reword", "exclusion", ["EXC-01"], text="Malformed protocol documents"))
    body = client.get(f"{BASE}/criteria").json()
    assert body["criteria_version"] == 2
    assert body["criteria"][1] == {"id": "EXC-01", "side": "exclusion", "text": "Malformed protocol documents",
                                   "reason_category": "INVALID_FORMAT", "since_version": 2}
    [amendment] = body["amendments"]
    assert amendment["op"] == "reword" and amendment["reason"] == "Clearer after the pilot."


# --- DoD 8: SCREENING_CRITERIA.md ------------------------------------------------------------


def test_dod8_the_criteria_file_is_rewritten_and_the_earlier_one_backed_up(ws, client):
    _ok(_amend(client, "reword", "exclusion", ["EXC-01"], text="Malformed protocol documents"))
    text = (ws / "SCREENING_CRITERIA.md").read_text(encoding="utf-8")
    assert "**Criterion**: Malformed protocol documents" in text and EXC_TEXT not in text.split("## Amendments")[0]
    assert "## Amendments" in text and "Clearer after the pilot." in text
    [backup] = list((ws / cr.AMENDED_DIR).iterdir())
    assert (backup / "SCREENING_CRITERIA.md").read_text(encoding="utf-8") == "# Screening Criteria (signed)\n"
    [row] = [r for r in _journal(ws) if r["action"] == cr.AMENDED_ACTION]
    assert backup.relative_to(ws).as_posix() + "/" in row["outputs"]


def test_dod8_a_journal_failure_takes_every_write_back(ws, client, monkeypatch):
    from scholar_harness.workspace import audit

    _decide_four_ways(client)
    projection = ws / "literature" / "screening" / "batch_001_decisions.json"
    before = (projection.read_bytes(), (ws / "SCREENING_CRITERIA.md").read_bytes())

    def broken(*_a, **_k):
        raise OSError("disk full")

    monkeypatch.setattr(audit, "append_event", broken)
    with pytest.raises(OSError):
        cr.amend_criteria(ws, op="reword", side="inclusion", ids=["INC-01"], text="Explicit research questions",
                          reason_category=None, reason_category_given=False, reason="r", confirm=True,
                          amended_by="r", amended_at="2026-11-21T10:00:00Z")
    assert (ws / cr.AMENDMENTS_FILE).read_bytes() == b""
    assert (projection.read_bytes(), (ws / "SCREENING_CRITERIA.md").read_bytes()) == before
    assert not (ws / cr.AMENDED_DIR).exists() or not any((ws / cr.AMENDED_DIR).iterdir())
    assert cr.criteria_in_force(ws).version == 1


# --- DoD 9: drafts under an earlier wording ----------------------------------------------------


def _draft(ws: Path, study: str, created_at: str) -> dict:
    context = ev.load_context(ws)
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    answers = [{"id": c.id, "answer": "no" if c.side == "exclusion" else "yes",
                "evidence": {"text": "", "start": 0, "end": 0}} for c in context.criteria.all]
    return pr.submit_proposal(
        ws, study_id=study, title="t", abstract="a", output={"criteria": answers, "cannot_decide": False},
        protocol=protocol, protocol_fingerprint=context.protocol_fingerprint,
        provenance={"task_version": "screen-v1", "model": "m", "prompt_sha256": api.PROMPT}, created_at=created_at)


def test_dod9_drafts_of_an_earlier_version_are_labelled_and_left_out(ws, client):
    studies = _studies(client)
    for study in studies:
        _draft(ws, study, "2026-11-21T09:00:00Z")
    _post(client, [_event(client, studies[2], "EXCLUDE", reason_code="EXC-01")])
    assert client.get(f"{BASE}/agreement").json()["decided_with_proposal"] == 1
    _ok(_amend(client, "reword", "exclusion", ["EXC-01"], text="Malformed protocol documents"))
    _post(client, [_event(client, studies[0], "INCLUDE")])
    # Labelled on the draft read.
    proposal = client.get(f"{BASE}/records/{studies[0]}/proposal").json()["proposal"]
    assert (proposal["criteria_version"], proposal["earlier_wording"]) == (1, True)
    # Left out of agreement (the study decided under v2 has only a v1 draft).
    assert client.get(f"{BASE}/agreement").json()["decided_with_proposal"] == 0
    # Counted on the run setup.
    setup = client.get(f"{BASE}/proposals/setup").json()["earlier_wording_drafts"]
    assert (setup["criteria_version"], setup["count"]) == (2, 3)
    # A new draft under v2 is current: no longer counted, and in agreement again.
    _draft(ws, studies[0], "2026-11-21T11:00:00Z")
    assert client.get(f"{BASE}/proposals/setup").json()["earlier_wording_drafts"]["count"] == 2
    assert client.get(f"{BASE}/agreement").json()["decided_with_proposal"] == 1
    fresh = client.get(f"{BASE}/records/{studies[0]}/proposal").json()["proposal"]
    assert (fresh["criteria_version"], fresh["earlier_wording"]) == (2, False)


def test_dod9_calibration_and_queue_order_leave_earlier_drafts_out(ws, client):
    from scholar_harness.screening import agent_runs as runs

    studies = _studies(client)
    _draft(ws, studies[0], "2026-11-21T09:00:00Z")
    _post(client, [_event(client, studies[0], "EXCLUDE", reason_code="EXC-01")])
    assert runs.calibration_result(ws, [studies[0]])["compared"] == 1
    _ok(_amend(client, "reword", "inclusion", ["INC-01"], text="Explicit research questions"))
    assert runs.calibration_result(ws, [studies[0]])["compared"] == 0
    # Queue order: an earlier draft orders like no draft.
    assert client.put(f"{BASE}/settings", json={"queue_order": "agent_uncertainty"}).status_code == 200
    items = client.get(f"{BASE}/queue", params={"view": "needs_you", "order": "agent_uncertainty"}).json()["items"]
    assert {i["study_id"] for i in items} == set(studies[1:])


def test_dod9_an_agent_run_stamps_its_drafts_with_the_version_in_force(ws, client):
    _ok(_amend(client, "add", "exclusion", text="Simulation-only studies"))
    study = _studies(client)[0]
    response = client.post(f"{BASE}/proposals/runs", json={
        "provider": "anthropic", "model": "claude-haiku-5-5", "effort": "low",
        "scope": {"study_ids": [study]}, "consent": CONSENT})
    assert response.status_code == 200, response.text
    [draft] = pr.read_proposals(ws)
    assert draft["criteria_version"] == 2
    assert {a["id"] for a in draft["output"]["criteria"]} == {"INC-01", "EXC-01", "EXC-02"}
    assert draft["validators"] and all(c["ok"] for c in draft["validators"] if c["name"] == "schema")


# --- DoD 10: the methods paragraph and the publish row -------------------------------------------


def test_dod10_the_methods_paragraph_reports_each_amendment_and_the_publish_row_its_digest(tmp_path):
    from test_export_api import decide, publish, se
    from test_methods_api import _assert_numbers_trace, _methods

    workspace = se._build(tmp_path)
    cr.amend_criteria(
        workspace, op="reword", side="exclusion", ids=["EXC-01"], text="Malformed protocol documents",
        reason_category=None, reason_category_given=False, reason="The pilot showed the word canonical confused.",
        confirm=True, amended_by="r", amended_at="2026-11-21T10:00:00Z",
    )
    decide(workspace)
    publish(workspace)
    body = _methods(workspace)
    paragraph = body["paragraph"]
    assert "On 2026-11-21, the screening criteria were amended: EXC-01 was reworded" in paragraph or (
        "the screening criteria were amended: EXC-01 was reworded" in paragraph)
    assert "“Malformed protocol documents”" in paragraph and "Reason: The pilot showed" in paragraph
    assert "No record had been decided under the earlier wording." in paragraph
    assert "not changed after the protocol was signed" not in paragraph
    [figure] = body["figures"]["criteria_amendments"]
    assert (figure["op"], figure["from_ids"], figure["decided"]) == ("reword", ["EXC-01"], 0)
    assert any(s["path"] == cr.AMENDMENTS_FILE.as_posix() for s in body["sources"])
    _assert_numbers_trace(body)


def test_dod10_with_no_amendment_the_paragraph_says_the_criteria_were_not_changed(tmp_path):
    from test_export_api import published_workspace
    from test_methods_api import _methods

    workspace, _ids = published_workspace(tmp_path)
    body = _methods(workspace)
    assert "The criteria were not changed after the protocol was signed." in body["paragraph"]
    assert body["figures"]["criteria_amendments"] == []


def test_dod10_the_publish_journal_row_carries_the_amendments_digest(tmp_path):
    from test_export_api import decide, se

    from scholar_harness.screening.collector import cmd_collect  # noqa: F401 - the publish path below

    workspace = se._build(tmp_path)
    cr.amend_criteria(
        workspace, op="add", side="exclusion", ids=[], text="Simulation-only studies", reason_category=None,
        reason_category_given=False, reason="r", confirm=True, amended_by="r", amended_at="2026-11-21T10:00:00Z",
    )
    decide(workspace)
    for index in ev.load_context(workspace).batches:
        ev.write_projection(workspace, index, se.SCREENER, workspace_id=se.WS_ID)
    se._stage_approval(workspace)
    client = TestClient(create_app(workspace, token=DESKTOP), base_url="http://127.0.0.1",
                        headers={"Authorization": f"Bearer {DESKTOP}"})
    response = client.post(f"{BASE}/actions/publish", json={})
    assert response.status_code in (200, 201), response.text
    [row] = [r for r in _journal(workspace) if r["action"] == "SCREENING_PUBLISH_COMPLETED"]
    digest = "sha256:" + hashlib.sha256((workspace / cr.AMENDMENTS_FILE).read_bytes()).hexdigest()
    assert row["parameters"]["criteria_amendments_sha256"] == digest


# --- decision item 5 as the researcher decided it (2026-11-21): bind the version ---------------------


def test_item5_the_record_binding_names_the_criteria_version(ws, client):
    study = _studies(client)[0]
    assert client.get(f"{BASE}/records/{study}").json()["binding"]["criteria_version"] == 1
    _ok(_amend(client, "add", "exclusion", text="Simulation-only studies"))
    assert client.get(f"{BASE}/records/{study}").json()["binding"]["criteria_version"] == 2


def test_item5_a_decision_bound_under_the_earlier_wording_is_refused_and_the_record_stays_queued(ws, client):
    studies = _studies(client)
    offline = _event(client, studies[0], "INCLUDE")  # bound under version 1, kept on a device offline
    _ok(_amend(client, "reword", "inclusion", ["INC-01"], text="Explicit research questions"))
    before = list(_stored(ws))
    [result] = _post(client, [offline])
    assert result["result"] == "refused" and result["refusal"]["code"] == "STALE_BINDING"
    assert "criteria" in result["refusal"]["message"]
    assert _stored(ws) == before  # nothing stored, so nothing is counted under the new wording
    queued = [i["study_id"] for i in client.get(f"{BASE}/queue", params={"view": "needs_you"}).json()["items"]]
    assert studies[0] in queued
    # Decided again under the binding the record now hands out: accepted, stamped version 2.
    [again] = _post(client, [_event(client, studies[0], "INCLUDE")])
    assert again["result"] == "accepted" and _stored(ws)[-1]["criteria_version"] == 2


def test_item5_a_binding_without_a_version_reads_as_version_1(ws, client):
    study = _studies(client)[0]
    event = _event(client, study)
    event["binding"] = {k: v for k, v in event["binding"].items() if k != "criteria_version"}
    assert _post(client, [event])[0]["result"] == "accepted"  # before any revision: version 1
    _ok(_amend(client, "add", "exclusion", text="Simulation-only studies"))
    other = _event(client, _studies(client)[0])
    other["binding"] = {k: v for k, v in other["binding"].items() if k != "criteria_version"}
    assert _post(client, [other])[0]["refusal"]["code"] == "STALE_BINDING"


def test_item5_a_stored_event_replays_as_a_duplicate_and_still_counts_after_a_revision(ws, client):
    studies = _studies(client)
    stored = _event(client, studies[2], "EXCLUDE", reason_code="EXC-01")
    assert _post(client, [stored])[0]["result"] == "accepted"
    _ok(_amend(client, "add", "inclusion", text="Peer-reviewed"))
    assert _post(client, [stored])[0]["result"] == "duplicate"
    # The binding check is at intake only: decisions made under version 1 still count.
    assert client.get(f"{BASE}/summary").json()["decided"] == 1
