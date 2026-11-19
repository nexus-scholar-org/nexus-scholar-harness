"""Workspace proposals after genesis (M10c D5; decision 2026-11-19, item 9 option (a)).

An assistant suggests a change to the protocol's search over MCP; the
suggestion is a line in ``audit/proposals.jsonl`` and a card on Discovery
Plan. Only the researcher's Apply, a console route, amends ``intent.json``
and recompiles ``protocol.json``; nothing outside the search fields is ever
changed, and nothing is changed once a corpus is accepted or while a search
runs. No model, no network.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from kits.agent.test_mcp_assistant import (  # noqa: F401 - env is a fixture
    MODEL,
    TOKEN,
    _call,
    _create,
    _genesis,
    env,
)
from scholar_agent import server
from scholar_harness import workspace_proposals as WP
from scholar_harness.console import browser, create_app
from scholar_harness.console.api.discovery import DiscoveryJob, DiscoveryJobs

PLAN = "/api/v1/discovery"
SYNONYMS = "core_concepts[weed detection].synonyms"


def _propose(ws: Path, **kw) -> dict:
    args = {"workspace_dir": ws.name, "field": SYNONYMS, "op": "add", "value": "UAV",
            "why": "Three of the recall seeds say UAV and none says weed detection.", "model": MODEL,
            "task": "recall_repair", "evidence": [{"kind": "doi", "value": "10.1/seed-a"}]}
    args.update(kw)
    return _call(server.nexus_assistant_propose, **args)


def _bytes(ws: Path) -> dict[str, bytes]:
    return {name: (ws / name).read_bytes() for name in ("intent.json", "protocol.json", "SCREENING_CRITERIA.md")}


def _journal(ws: Path) -> list[dict]:
    return [json.loads(x) for x in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()]


@pytest.fixture
def plan(env):  # noqa: F811
    client, root = env
    ws = _genesis(client, _create(client)["session_id"])
    app = create_app(ws, token=TOKEN, workspaces_root=root)
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as c:
        yield c, ws, app


def test_a_workspace_proposal_is_recorded_listed_on_plan_and_changes_nothing(plan):
    c, ws, _app = plan
    before = _bytes(ws)
    answer = _propose(ws)
    assert answer["status"] == "SUCCESS" and answer["created"] is True, answer
    proposal = answer["proposal"]
    assert proposal["target"] == {"kind": "workspace", "id": ws.name, "field": SYNONYMS}
    assert proposal["source"] == f"agent:{MODEL}" and proposal["agent"]["task"] == "recall_repair"
    assert proposal["status"] == "open" and proposal["step"] == "plan"
    assert _bytes(ws) == before  # nothing is applied by the assistant
    assert _propose(ws)["created"] is False  # the same suggestion is recorded once
    lines = [json.loads(x) for x in (ws / "audit" / "proposals.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [x["event"] for x in lines if x.get("target", {}).get("kind") == "workspace"] == ["proposed"]
    assert any(e["action"] == "ASSISTANT_PROPOSAL_RECORDED" for e in _journal(ws))

    listed = c.get(f"{PLAN}/proposals").json()
    assert listed["shape"] == "discovery.proposals-v1" and listed["counts"]["open"] == 1
    assert listed["proposals"][0]["current"] == "weed mapping" and listed["active_job"] is None
    assert _call(server.nexus_assistant_read_workspace, workspace_dir=ws.name)["proposals"]["counts"]["open"] == 1


def test_apply_amends_only_the_search_and_journals_it(plan):
    c, ws, _app = plan
    old_protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    old_fp = c.get(f"{PLAN}/plan").json()["protocol_fingerprint"]
    first = _propose(ws)["proposal"]
    second = _propose(ws, field="start_year", op="replace", value=2015, task="suggest")["proposal"]

    applied = c.post(f"{PLAN}/proposals/{first['proposal_id']}/apply")
    assert applied.status_code == 200, applied.text
    body = applied.json()
    assert body["amended"]["previous_fingerprint"] == old_fp
    assert body["amended"]["changed"] == ["search_strategy.core_concepts"]
    new_protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    assert new_protocol["search_strategy"]["core_concepts"][0]["synonyms"] == ["weed mapping", "UAV"]
    assert {k: v for k, v in new_protocol.items() if k != "search_strategy"} == {
        k: v for k, v in old_protocol.items() if k != "search_strategy"}
    intent = json.loads((ws / "intent.json").read_text(encoding="utf-8"))
    assert intent["core_concepts"][0]["synonyms"] == ["weed mapping", "UAV"]
    assert c.get(f"{PLAN}/plan").json()["protocol_fingerprint"] == body["amended"]["protocol_fingerprint"] != old_fp
    backup = ws / body["amended"]["backup"]
    assert json.loads((backup / "protocol.json").read_text(encoding="utf-8")) == old_protocol
    actions = [e["action"] for e in _journal(ws)]
    assert actions[-2:] == ["PROPOSAL_DECIDED", "PROTOCOL_AMENDED"]
    statuses = {p["proposal_id"]: p["status"] for p in body["proposals"]}
    # The fingerprint moved: the suggestion made against the old protocol is out of date (01-proposals).
    assert statuses == {first["proposal_id"]: "applied", second["proposal_id"]: "stale"}

    stale = c.post(f"{PLAN}/proposals/{second['proposal_id']}/apply")
    assert stale.status_code == 409 and stale.json()["detail"]["code"] == "PROPOSAL_STALE"
    again = c.post(f"{PLAN}/proposals/{first['proposal_id']}/apply")
    assert again.status_code == 409 and again.json()["detail"]["code"] == "PROPOSAL_NOT_OPEN"
    rejected = c.post(f"{PLAN}/proposals/{second['proposal_id']}/reject", json={"reason": "Too wide."})
    assert rejected.status_code == 200 and rejected.json()["counts"]["rejected"] == 1


def test_an_apply_that_would_change_a_field_outside_the_search_is_refused(plan):
    """The negative test: the intent's title was edited after the suggestion, so its Apply would retitle the protocol."""
    c, ws, _app = plan
    pid = _propose(ws)["proposal"]["proposal_id"]
    intent = json.loads((ws / "intent.json").read_text(encoding="utf-8"))
    intent["title"] = "Another title"
    (ws / "intent.json").write_text(json.dumps(intent, indent=2), encoding="utf-8")
    before, journal = _bytes(ws), len(_journal(ws))

    refused = c.post(f"{PLAN}/proposals/{pid}/apply")
    assert refused.status_code == 422, refused.text
    detail = refused.json()["detail"]
    assert detail["code"] == "PROTOCOL_AMENDMENT_REFUSED" and detail["details"]["reason"] == "outside_search"
    assert "metadata.title" in detail["details"]["paths"]
    assert _bytes(ws) == before and len(_journal(ws)) == journal
    assert not (ws / WP.AMENDED_DIR).exists()
    assert c.get(f"{PLAN}/proposals").json()["counts"]["open"] == 1


def test_compile_amendment_refuses_any_path_outside_the_search_fields(plan):
    _c, ws, _app = plan
    intent, protocol, _fp = WP.documents(ws)
    for key, value in (("title", "x"), ("unit_of_analysis", "farms"), ("target_databases", ["openalex"]),
                       ("pool_max", 5)):
        changed = {**intent, key: value}
        with pytest.raises(WP.P.ProposalRefused) as exc:
            WP.compile_amendment(protocol, changed)
        assert exc.value.code == "PROTOCOL_AMENDMENT_REFUSED" and exc.value.details["reason"] == "outside_search", key


@pytest.mark.parametrize(("kw", "code"), [
    ({"field": "title", "op": "replace", "value": "x"}, "PROPOSAL_TARGET_UNSUPPORTED"),
    ({"field": "core_concepts", "op": "remove", "value": "weed detection"}, "PROPOSAL_TARGET_UNSUPPORTED"),
    ({"field": "core_concepts[drones].synonyms"}, "PROPOSAL_TARGET_UNSUPPORTED"),
    ({"value": "weed mapping"}, "PROPOSAL_NOT_OPEN"),
    ({"field": "start_year", "op": "replace", "value": "not a year"}, "PROTOCOL_AMENDMENT_REFUSED"),
    ({"field": "core_concepts", "op": "add", "value": {"concept": "UAV", "synonyms": "drone"}}, "PROTOCOL_AMENDMENT_REFUSED"),
    ({"model": ""}, "PROVENANCE_MISSING"),
    ({"why": ""}, "BODY_INVALID"),
])
def test_a_workspace_proposal_the_protocol_could_not_take_is_refused(plan, kw, code):
    _c, ws, _app = plan
    before = (ws / "audit" / "proposals.jsonl").read_bytes()
    answer = _propose(ws, **kw)
    assert answer["status"] == "ERROR" and answer["code"] == code, answer
    assert (ws / "audit" / "proposals.jsonl").read_bytes() == before


def test_a_new_concept_and_languages_can_be_suggested_and_applied(plan):
    c, ws, _app = plan
    concept = _propose(ws, field="core_concepts", value={"concept": "UAV", "synonyms": ["drone"]})["proposal"]
    assert c.post(f"{PLAN}/proposals/{concept['proposal_id']}/apply").status_code == 200
    language = _propose(ws, field="languages", value="fr")["proposal"]
    body = c.post(f"{PLAN}/proposals/{language['proposal_id']}/apply").json()
    assert body["amended"]["changed"] == ["search_strategy.languages"]
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    assert [x["concept"] for x in protocol["search_strategy"]["core_concepts"]] == ["weed detection", "UAV"]
    assert protocol["search_strategy"]["languages"][-1] == "fr"


def test_nothing_is_suggested_or_applied_once_a_corpus_is_accepted(plan):
    c, ws, _app = plan
    pid = _propose(ws)["proposal"]["proposal_id"]
    (ws / "audit" / "artifact_registry.json").write_text(
        json.dumps({"artifacts": {"COR-1": {"artifact_type": "corpus_snapshot", "path": "x.json"}}}), encoding="utf-8")
    before = _bytes(ws)
    assert _propose(ws, value="drone")["code"] == "CORPUS_ALREADY_ACCEPTED"
    refused = c.post(f"{PLAN}/proposals/{pid}/apply")
    assert refused.status_code == 409 and refused.json()["detail"]["code"] == "CORPUS_ALREADY_ACCEPTED"
    assert _bytes(ws) == before
    assert c.get(f"{PLAN}/proposals").json()["frozen"] is True
    assert c.post(f"{PLAN}/proposals/{pid}/reject", json={}).status_code == 200  # rejecting changes nothing


def test_nothing_is_applied_while_a_search_runs(plan):
    c, ws, app = plan
    pid = _propose(ws)["proposal"]["proposal_id"]
    jobs = app.state.discovery_jobs = DiscoveryJobs()
    job = DiscoveryJob(job_id="djob_test", workspace=str(Path(app.state.workspace)), kind="run")
    jobs.jobs[job.job_id] = job
    before = _bytes(ws)
    refused = c.post(f"{PLAN}/proposals/{pid}/apply")
    assert refused.status_code == 409 and refused.json()["detail"]["code"] == "DISCOVERY_JOB_ACTIVE"
    assert _bytes(ws) == before
    assert c.get(f"{PLAN}/proposals").json()["active_job"]["job_id"] == "djob_test"


def test_open_workspace_proposals_are_limited(plan, monkeypatch):
    from scholar_harness import assistant

    _c, ws, _app = plan
    monkeypatch.setattr(assistant, "MAX_OPEN_PROPOSALS", 1)
    assert _propose(ws)["status"] == "SUCCESS"
    assert _propose(ws, value="drone")["code"] == "ASSISTANT_LIMIT_REACHED"


def test_genesis_history_is_not_listed_and_the_routes_are_allowed_for_the_browser(plan):
    c, ws, _app = plan
    with open(ws / "audit" / "proposals.jsonl", "a", encoding="utf-8") as handle:
        handle.write(json.dumps({"event": "proposed", "proposal_id": "prop_000000000000", "status": "open",
                                 "target": {"kind": "draft", "id": "rec_x", "field": "topic"}}) + "\n")
    assert c.get(f"{PLAN}/proposals").json()["proposals"] == []
    for action in ("apply", "reject"):
        assert any(p.fullmatch(f"api/v1/discovery/proposals/prop_0123456789ab/{action}") for p in browser.POST_PATHS)
    assert c.post(f"{PLAN}/proposals/prop_000000000000/apply").json()["detail"]["code"] == "PROPOSAL_NOT_FOUND"


def test_a_workspace_proposal_needs_exactly_one_target(plan):
    _c, ws, _app = plan
    assert _propose(ws, session_id="rec_" + "0" * 32)["code"] == "TARGET_INVALID"


@pytest.mark.parametrize("registry", ["{not json", "[]", '{"artifacts": []}'])
def test_an_unreadable_registry_counts_as_an_accepted_corpus(plan, registry):
    """Fail closed (review finding 2): Apply never amends a protocol whose acceptance it cannot read."""
    c, ws, _app = plan
    pid = _propose(ws)["proposal"]["proposal_id"]
    (ws / "audit" / "artifact_registry.json").write_text(registry, encoding="utf-8")
    before = _bytes(ws)
    refused = c.post(f"{PLAN}/proposals/{pid}/apply")
    assert refused.status_code == 409 and refused.json()["detail"]["code"] == "CORPUS_ALREADY_ACCEPTED"
    assert _bytes(ws) == before and not (ws / WP.AMENDED_DIR).exists()


def test_an_empty_workspace_name_is_refused_not_read_as_the_current_folder(plan):
    assert _call(server.nexus_assistant_read_workspace, workspace_dir="  ")["code"] == "TARGET_INVALID"
