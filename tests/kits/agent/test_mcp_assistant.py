"""The assistant and the critic over MCP (M10c, ``docs/roadmap/milestones/M10c-assistant-mcp.md``).

The researcher's own MCP client may read a draft or a workspace and add a
suggestion: a proposal on the app's card or a finding in the app's checks
panel. Nothing it sends changes an answer, ``updated_at``, the protocol or
the corpus. These tests drive the real tool functions and the real console
routes in one process, with no model and no network.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scholar_agent import server
from scholar_harness.console import create_app

TOKEN = "desk-token"
BASE = "/api/v1/inception"
MODEL = "claude-opus-5-5"


def uav_draft(**changes) -> dict:
    """A draft that compiles; its title and question say UAV while no concept does."""
    draft = {
        "topic": "Weed detection from UAV imagery",
        "paradigm": "Positivist",
        "playbook": "PRISMA_SLR",
        "unit_of_analysis": "field trials",
        "rqs": ["How accurate is UAV weed detection in row crops?"],
        "concepts": [{"concept": "weed detection", "synonyms": ["weed mapping"]}],
        "extra_inclusions": ["Field studies with aerial imagery"],
        "extra_exclusions": [{"criterion": "Simulation only", "reason_category": "WRONG_REPORT_TYPE"}],
        "title": "UAV weed detection",
        "lead_researcher": "A. Researcher",
    }
    draft.update(changes)
    return draft


@pytest.fixture
def env(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    monkeypatch.setenv("NEXUS_WORKSPACES_ROOT", str(root))
    monkeypatch.setenv("NEXUS_RECON_ROOT", str(tmp_path / "recon"))
    app = create_app(None, token=TOKEN, workspaces_root=root)
    app.state.recon_root = tmp_path / "recon"
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        yield client, root


def _call(tool, **kwargs) -> dict:
    return json.loads(tool(**kwargs))


def _create(client, draft: dict | None = None) -> dict:
    created = client.post(f"{BASE}/drafts", json={"draft": draft or uav_draft()})
    assert created.status_code == 201, created.text
    return created.json()


def _tree(root: Path) -> dict[str, tuple[int, int]]:
    return {str(p.relative_to(root)): (p.stat().st_size, p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file()}


def _genesis(client, sid: str) -> Path:
    created = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert created.status_code == 201, created.text
    return Path(created.json()["path"])


# --------------------------------------------------------------------------- reads (D2)


def test_the_drafts_are_listed_with_their_open_suggestions(env):
    client, _root = env
    sid = _create(client)["session_id"]
    answer = _call(server.nexus_assistant_drafts)
    assert answer["status"] == "SUCCESS"
    item = next(d for d in answer["drafts"] if d["session_id"] == sid)
    assert item["open_proposals"] == 0 and item["findings"] == 0


def test_reading_a_draft_returns_answers_intent_checks_and_proposals_and_writes_nothing(env):
    client, root = env
    sid = _create(client)["session_id"]
    before = _tree(root)
    answer = _call(server.nexus_assistant_read_draft, session_id=sid)
    assert answer["status"] == "SUCCESS"
    assert answer["draft"]["topic"] == "Weed detection from UAV imagery"
    assert answer["intent"]["core_concepts"][0]["concept"] == "weed detection"
    assert answer["intent_refused"] is None
    ids = {c["check_id"] for c in answer["checks"]["checks"]}
    assert "CONCEPT_TERM_MISSING" in ids
    # A read records nothing: the check that recommends UAV links to its field, no proposal is made.
    term = next(c for c in answer["checks"]["checks"] if c["check_id"] == "CONCEPT_TERM_MISSING")
    assert term["action"]["kind"] == "field"
    assert answer["proposals"] == []
    assert _tree(root) == before


def test_an_incomplete_draft_is_read_with_the_reason_it_has_no_intent(env):
    client, _root = env
    sid = _create(client, {"topic": "Weed detection"})["session_id"]
    answer = _call(server.nexus_assistant_read_draft, session_id=sid)
    assert answer["intent"] is None and answer["intent_refused"]["code"]


def test_an_unknown_draft_is_a_typed_refusal(env):
    answer = _call(server.nexus_assistant_read_draft, session_id="rec_" + "0" * 32)
    assert answer == {"status": "ERROR", "code": "DRAFT_NOT_FOUND", "message": answer["message"]}


def test_reading_a_workspace_returns_protocol_plan_and_checks_and_writes_nothing(env):
    client, _root = env
    ws = _genesis(client, _create(client)["session_id"])
    before = _tree(ws)
    answer = _call(server.nexus_assistant_read_workspace, workspace_dir=ws.name)  # by its slug
    assert answer["status"] == "SUCCESS", answer
    assert answer["protocol"]["search_strategy"]["core_concepts"]
    assert answer["intent"]["title"] == "UAV weed detection"
    rows = answer["plan"]["providers"]
    assert rows and all("cannot_express" in r or "executed" in r or "query" in r for r in rows)
    assert answer["recall"]["refused"]["code"] == "RECALL_NOT_RUN"
    assert {c["check_id"] for c in answer["checks"]["checks"]} >= {"PLAN_QUERY_TERM_MISSING"}
    assert _tree(ws) == before


def test_a_workspace_path_outside_the_mcp_anchor_is_refused(env, tmp_path):
    outside = tmp_path.parent / "elsewhere"
    answer = _call(server.nexus_assistant_read_workspace, workspace_dir=str(outside))
    assert answer["code"] == "PATH_OUTSIDE_WORKSPACE"


# --------------------------------------------------------------------------- proposals (D3)


def _propose(sid: str, **kw) -> dict:
    args = {"session_id": sid, "field": "concepts[weed detection].synonyms", "op": "add", "value": "UAV",
            "why": "The title and the question say UAV; no concept does.", "model": MODEL, "task": "synonyms",
            "evidence": [{"kind": "words", "name": "term", "value": "UAV"}]}
    args.update(kw)
    return _call(server.nexus_assistant_propose, **args)


def test_a_proposal_lands_on_the_card_without_changing_the_draft_or_updated_at(env):
    client, _root = env
    record = _create(client)
    sid = record["session_id"]
    answer = _propose(sid)
    assert answer["status"] == "SUCCESS" and answer["created"] is True
    proposal = answer["proposal"]
    assert proposal["source"] == f"agent:{MODEL}"
    assert proposal["agent"] == {"model": MODEL, "task": "synonyms", "task_version": "assistant-v1"}
    assert proposal["status"] == "open" and proposal["step"] == "criteria"
    after = client.get(f"{BASE}/drafts/{sid}").json()
    assert after["draft"] == record["draft"] and after["updated_at"] == record["updated_at"]
    listed = client.get(f"{BASE}/drafts/{sid}/proposals?step=criteria").json()
    assert [p["proposal_id"] for p in listed["proposals"]] == [proposal["proposal_id"]]
    assert listed["by_step"]["criteria"]["open"] == 1
    # Sending it again records it once.
    again = _propose(sid)
    assert again["created"] is False and again["proposal"]["proposal_id"] == proposal["proposal_id"]
    assert len(client.get(f"{BASE}/drafts/{sid}/proposals").json()["proposals"]) == 1


def test_only_the_researcher_applies_it_and_genesis_counts_the_assistant(env):
    client, _root = env
    record = _create(client)
    sid = record["session_id"]
    pid = _propose(sid)["proposal"]["proposal_id"]
    applied = client.post(f"{BASE}/drafts/{sid}/proposals/{pid}/apply", json={"base_updated_at": record["updated_at"]})
    assert applied.status_code == 200, applied.text
    assert applied.json()["draft"]["concepts"][0]["synonyms"] == ["weed mapping", "UAV"]
    ws = _genesis(client, sid)
    lines = [json.loads(x) for x in (ws / "audit" / "proposals.jsonl").read_text(encoding="utf-8").splitlines()]
    proposed = next(x for x in lines if x["event"] == "proposed" and x["proposal_id"] == pid)
    assert proposed["source"] == f"agent:{MODEL}" and proposed["agent"]["task"] == "synonyms"
    assert next(x for x in lines if x["event"] == "applied" and x["proposal_id"] == pid)["in_protocol"] is True
    journal = [json.loads(x) for x in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()]
    counts = next(e for e in journal if e["action"] == "PROPOSALS_RECORDED")["parameters"]
    assert counts["by_source"]["agent"] == 1


def test_a_rejected_assistant_proposal_changes_nothing(env):
    client, _root = env
    record = _create(client)
    sid = record["session_id"]
    pid = _propose(sid)["proposal"]["proposal_id"]
    assert client.post(f"{BASE}/drafts/{sid}/proposals/{pid}/reject", json={"reason": "not a search word"}).status_code == 200
    after = client.get(f"{BASE}/drafts/{sid}").json()
    assert after["draft"] == record["draft"] and after["updated_at"] == record["updated_at"]


@pytest.mark.parametrize(
    ("kw", "code"),
    [
        ({"model": ""}, "PROVENANCE_MISSING"),
        ({"model": "bad model name"}, "PROVENANCE_MISSING"),
        ({"task": "decide"}, "TASK_UNKNOWN"),
        ({"why": "  "}, "BODY_INVALID"),
        ({"evidence": [{"kind": "opinion"}]}, "BODY_INVALID"),
        ({"field": "nonsense"}, "PROPOSAL_TARGET_UNSUPPORTED"),
        ({"field": "topic", "op": "add"}, "PROPOSAL_TARGET_UNSUPPORTED"),
        ({"field": "concepts[no such concept].synonyms"}, "PROPOSAL_TARGET_UNSUPPORTED"),
        ({"value": "weed mapping"}, "PROPOSAL_NOT_OPEN"),
        ({"field": "start_year", "op": "replace", "value": "not a year"}, "DRAFT_INVALID"),
        ({"field": "title", "op": "replace", "value": "x" * 5000}, "DRAFT_TOO_LARGE"),
    ],
)
def test_a_proposal_the_draft_could_not_take_is_refused_before_any_card(env, kw, code):
    client, root = env
    sid = _create(client)["session_id"]
    before = _tree(root)
    answer = _propose(sid, **kw)
    assert answer["status"] == "ERROR" and answer["code"] == code, answer
    assert _tree(root) == before


def test_proposals_are_refused_after_genesis(env):
    client, _root = env
    sid = _create(client)["session_id"]
    _genesis(client, sid)
    assert _propose(sid)["code"] == "DRAFT_EMITTED"


def test_open_assistant_proposals_are_limited(env, monkeypatch):
    from scholar_harness import assistant

    monkeypatch.setattr(assistant, "MAX_OPEN_PROPOSALS", 2)
    client, _root = env
    sid = _create(client)["session_id"]
    for word in ("UAV", "drone"):
        assert _propose(sid, value=word)["created"] is True
    answer = _propose(sid, value="UAS")
    assert answer["code"] == "ASSISTANT_LIMIT_REACHED" and answer["details"]["limit"] == 2
    # A decided one no longer counts.
    pid = next(p for p in _call(server.nexus_assistant_read_draft, session_id=sid)["proposals"] if p["value"] == "UAV")["proposal_id"]
    client.post(f"{BASE}/drafts/{sid}/proposals/{pid}/reject", json={})
    assert _propose(sid, value="UAS")["created"] is True


def test_the_browser_still_cannot_create_an_agent_proposal():
    from scholar_harness.inception import proposals

    with pytest.raises(proposals.ProposalRefused) as exc:
        proposals.make(draft_id="rec_" + "a" * 32, draft=uav_draft(), source="agent:x", field="topic", op="replace",
                       value="x", why="")
    assert exc.value.code == "PROPOSAL_SOURCE_REFUSED"


# --------------------------------------------------------------------------- findings (D4)


def _finding(**kw) -> dict:
    args = {"locator": "/inclusion_criteria/0/criterion", "severity": "major",
            "finding": "INC-01 asks for something the abstract cannot show.", "model": MODEL}
    args.update(kw)
    return _call(server.nexus_assistant_report_finding, **args)


def test_a_finding_on_a_draft_is_an_agent_row_in_the_checks_and_never_blocks(env):
    client, _root = env
    record = _create(client)
    sid = record["session_id"]
    answer = _finding(session_id=sid, severity="critical", why="Screening reads titles and abstracts.")
    assert answer["status"] == "SUCCESS" and answer["created"] is True
    after = client.get(f"{BASE}/drafts/{sid}").json()
    assert after["updated_at"] == record["updated_at"] and after["draft"] == record["draft"]
    body = client.post(f"{BASE}/drafts/{sid}/checks", json={}).json()
    assert body["sources"] == ["check", "agent"]
    row = next(c for c in body["checks"] if c["source"] == "agent")
    assert row["check_id"] == "ASSISTANT_FINDING" and row["subject"].startswith("find_")
    assert row["level"] == "warning" and row["severity"] == "critical" and row["step"] == "criteria"
    assert row["message"].startswith("INC-01") and row["agent"]["task"] == "critic"
    assert row["refusal"] is None and row["dismissible"] is True and row["outdated"] is False
    assert body["by_step"]["criteria"]["warning"] >= 1
    before_ready = body["ready"]
    assert _finding(session_id=sid, finding="A second problem.")["created"] is True
    assert client.post(f"{BASE}/drafts/{sid}/checks", json={}).json()["ready"] == before_ready
    # The same finding twice is recorded once.
    assert _finding(session_id=sid, finding="A second problem.")["created"] is False


def test_a_finding_is_dismissed_and_restored_by_the_existing_routes(env):
    client, _root = env
    sid = _create(client)["session_id"]
    row = _finding(session_id=sid)["finding"]
    url = f"{BASE}/drafts/{sid}/checks/ASSISTANT_FINDING"
    refused = client.post(f"{url}/dismiss", json={"subject": row["subject"], "evidence_digest": row["evidence_digest"]})
    assert refused.status_code == 422 and refused.json()["detail"]["code"] == "CHECK_REASON_REQUIRED"
    done = client.post(f"{url}/dismiss", json={"subject": row["subject"], "evidence_digest": row["evidence_digest"],
                                                "reason": "The abstract does report this."})
    assert done.status_code == 200, done.text
    got = next(c for c in done.json()["checks"] if c["subject"] == row["subject"])
    assert got["status"] == "dismissed"
    restored = client.post(f"{url}/restore", json={"subject": row["subject"]})
    assert next(c for c in restored.json()["checks"] if c["subject"] == row["subject"])["status"] == "open"


def test_a_finding_says_when_the_located_value_changed(env):
    client, _root = env
    record = _create(client)
    sid = record["session_id"]
    _finding(session_id=sid)
    changed = {**record["draft"], "extra_inclusions": ["Field studies that report detection accuracy"]}
    assert client.put(f"{BASE}/drafts/{sid}", json={"draft": changed}).status_code == 200
    row = next(c for c in client.post(f"{BASE}/drafts/{sid}/checks", json={}).json()["checks"] if c["source"] == "agent")
    assert row["outdated"] is True and row["status"] == "open"


@pytest.mark.parametrize(
    ("kw", "code"),
    [
        ({"locator": "inclusion_criteria"}, "LOCATOR_INVALID"),
        ({"locator": "/no_such_key/0"}, "LOCATOR_UNKNOWN"),
        ({"locator": "/inclusion_criteria/9/criterion"}, "LOCATOR_UNKNOWN"),
        ({"severity": "blocker"}, "BODY_INVALID"),
        ({"finding": ""}, "BODY_INVALID"),
        ({"model": ""}, "PROVENANCE_MISSING"),
    ],
)
def test_a_finding_that_cannot_be_placed_is_refused(env, kw, code):
    client, root = env
    sid = _create(client)["session_id"]
    before = _tree(root)
    answer = _finding(session_id=sid, **kw)
    assert answer["code"] == code, answer
    assert _tree(root) == before


def test_a_missing_element_may_be_named_by_its_list(env):
    client, _root = env
    sid = _create(client)["session_id"]
    assert _finding(session_id=sid, locator="/golden_seeds", severity="minor",
                    finding="No recall seed is named.")["finding"]["level"] == "note"
    assert _finding(session_id=sid, locator="/exclusion_criteria/-", finding="No exclusion for reviews.")["created"]


def test_an_incomplete_draft_takes_a_finding_on_its_answers(env):
    client, _root = env
    sid = _create(client, {"topic": "Weed detection"})["session_id"]
    assert _finding(session_id=sid)["code"] == "LOCATOR_INVALID"
    row = _finding(session_id=sid, locator="draft:/topic", finding="The question names no population.")["finding"]
    assert row["step"] == "scope" and row["action"] == {"kind": "field", "step": "scope", "field": "topic",
                                                         "label_key": "checks.ASSISTANT_FINDING.action"}


def test_a_finding_needs_exactly_one_target(env):
    assert _finding()["code"] == "TARGET_INVALID"
    assert _finding(session_id="rec_" + "0" * 32, workspace_dir="x")["code"] == "TARGET_INVALID"


def test_a_finding_on_a_workspace_is_recorded_journaled_and_listed_on_plan(env):
    client, root = env
    ws = _genesis(client, _create(client)["session_id"])
    answer = _finding(workspace_dir=ws.name, locator="/core_concepts/0/synonyms")
    assert answer["status"] == "SUCCESS", answer
    lines = (ws / "audit" / "assistant_findings.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(x)["event"] for x in lines] == ["reported"]
    journal = [json.loads(x) for x in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()]
    row = next(e for e in journal if e["action"] == "ASSISTANT_FINDING_REPORTED")
    assert row["parameters"]["model"] == MODEL and row["outputs"] == ["audit/assistant_findings.jsonl"]
    assert _finding(workspace_dir=ws.name, locator="draft:/topic")["code"] == "LOCATOR_INVALID"

    app = create_app(ws, token=TOKEN, workspaces_root=root)
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as c:
        body = c.get("/api/v1/discovery/checks?step=plan").json()
        assert "agent" in body["sources"]
        got = next(x for x in body["checks"] if x["source"] == "agent")
        assert got["step"] == "plan" and got["level"] == "warning"
        dismissed = c.post("/api/v1/discovery/checks/ASSISTANT_FINDING/dismiss", json={
            "subject": got["subject"], "evidence_digest": got["evidence_digest"], "reason": "Deliberate."})
        assert dismissed.status_code == 200, dismissed.text
        assert next(x for x in dismissed.json()["checks"] if x["subject"] == got["subject"])["status"] == "dismissed"


# --------------------------------------------------------------------------- limits (D6)

#: What decision 2026-11-14 item 3 forbids an assistant to do, and the code that does it.
FORBIDDEN_CODE = ("start_run", "accept_corpus", "screening.events", "screening_v1", "submit_proposal",
                  "publish(", "recon_probe(", ".probe(", ".delta(", "discovery_jobs", "genesis(")


def test_no_assistant_tool_searches_harvests_accepts_decides_or_publishes():
    import inspect

    from scholar_harness import assistant

    for name in server.ASSISTANT_TOOLS:
        source = inspect.getsource(getattr(server, name))
        assert not [w for w in FORBIDDEN_CODE if w in source], name
    module = inspect.getsource(assistant)
    assert not [w for w in FORBIDDEN_CODE if w in module]


def test_the_recon_tools_refuse_a_session_that_is_an_app_draft(env, monkeypatch):
    client, _root = env
    sid = _create(client)["session_id"]

    def no_search(*_a, **_k):  # pragma: no cover - reaching it is the failure
        raise AssertionError("a search was started for the app's draft")

    monkeypatch.setattr(server, "RECON_SEARCH_FN", no_search)
    for answer in (json.loads(server.recon_probe(topic="weeds", session_id=sid)),
                   json.loads(server.recon_delta(session_id=sid))):
        assert answer["code"] == "RECON_SESSION_IS_A_DRAFT"


def test_the_help_lists_every_assistant_tool(capsys):
    import contextlib

    with contextlib.suppress(SystemExit):
        server.main(["--help"])
    out = capsys.readouterr().out
    assert all(name in out for name in server.ASSISTANT_TOOLS)
