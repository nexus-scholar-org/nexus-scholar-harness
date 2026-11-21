"""M11a Part D: the researcher's amendment of the search from Plan (`POST /discovery/workbench/amend`).

Spec `docs/roadmap/milestones/M11a-query-workbench.md` (e), DoD 20 to 23, and
`docs/ux/phase1-discovery/final/10-plan-amend-search.md`. The workspace is made
by a real genesis (the M10c fixtures), so ``intent.json``, ``protocol.json``
and ``SCREENING_CRITERIA.md`` agree; nothing reaches the network.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from kits.agent.test_mcp_assistant import TOKEN, _create, _genesis, env  # noqa: F401 - env is a fixture
from scholar_harness import query_workbench as qw
from scholar_harness import workspace_proposals as WP
from scholar_harness.corpus_accept import AcceptCorpusRefused, refuse_if_run_protocol_changed
from scholar_search import workbench as wb
from scholar_search.plan import run_providers
from scholar_harness.console import browser, create_app, refusals
from scholar_harness.console.api.discovery import DiscoveryJob, DiscoveryJobs

ROOT = Path(__file__).resolve().parents[2]
PROXY = ROOT / "apps" / "research-ui" / "app" / "api" / "console" / "[...path]" / "route.ts"
PLAN = "/api/v1/discovery"
AMEND = f"{PLAN}/workbench/amend"


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


def _search(client) -> dict:
    return client.get(f"{PLAN}/plan").json()


def _body(read: dict, concepts: list[dict], **kw) -> dict:
    return {"query_key": "main", "concepts": concepts, "reason": "UAV and multispectral are one idea in this review.",
            "protocol_fingerprint": read["protocol_fingerprint"], **kw}


def _merged(read: dict) -> list[dict]:
    """The saved concepts with the first two merged into one OR group (the 2026-11-20 run's fix)."""
    concepts = read["search"]["concepts"]
    if len(concepts) < 2:
        return [{"concept": concepts[0]["concept"], "synonyms": [*concepts[0]["synonyms"], "unmanned aerial vehicle"]}]
    first, second, *rest = concepts
    merged = {"concept": first["concept"], "synonyms": [*first["synonyms"], second["concept"], *second["synonyms"]]}
    return [merged, *rest]


def test_plan_reads_the_protocols_concepts_years_languages_and_seeds(plan):
    client, ws, _app = plan
    read = _search(client)
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    strategy = protocol["search_strategy"]
    assert read["search"]["query_key"] == "main"
    assert [c["concept"] for c in read["search"]["concepts"]] == [c["concept"] for c in strategy["core_concepts"]]
    assert read["search"]["languages"] == strategy.get("languages", [])
    assert read["search"]["golden_seeds"] == strategy.get("golden_seeds", [])


def test_a_dry_run_lists_what_it_changes_and_writes_nothing(plan):
    client, ws, _app = plan
    read = _search(client)
    before = _bytes(ws)
    journal = len(_journal(ws))
    answer = client.post(AMEND, json=_body(read, _merged(read), dry_run=True, reason=""))
    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert body["dry_run"] is True and body["query_key"] == "main"
    assert body["previous_fingerprint"] == read["protocol_fingerprint"] != body["protocol_fingerprint"]
    assert body["changed"] and all(p.startswith("search_strategy.core_concepts") for p in body["changed"])
    assert set(body["consequences"]) == {"runs", "exports", "recall_checks", "estimate", "proposals"}
    assert _bytes(ws) == before and len(_journal(ws)) == journal
    assert not (ws / "audit" / "amended").exists()


def test_recording_replaces_the_concept_list_through_the_9a_path(plan):
    client, ws, _app = plan
    read = _search(client)
    concepts = _merged(read)
    answer = client.post(AMEND, json=_body(read, concepts))
    assert answer.status_code == 200, answer.text
    body = answer.json()
    intent = json.loads((ws / "intent.json").read_text(encoding="utf-8"))
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    assert [c["concept"] for c in intent["core_concepts"]] == [c["concept"] for c in concepts]
    assert [c["concept"] for c in protocol["search_strategy"]["core_concepts"]] == [c["concept"] for c in concepts]
    backup = ws / body["backup"]
    assert sorted(p.name for p in backup.iterdir()) == ["SCREENING_CRITERIA.md", "intent.json", "protocol.json"]
    row = [e for e in _journal(ws) if e["action"] == "PROTOCOL_AMENDED"][-1]
    params = row["parameters"]
    assert params["source"] == "researcher" and params["reason"] == "UAV and multispectral are one idea in this review."
    assert params["query_key"] == "main"
    assert params["previous_fingerprint"] == read["protocol_fingerprint"]
    assert params["protocol_fingerprint"] == body["protocol_fingerprint"] == _search(client)["protocol_fingerprint"]
    assert isinstance(params["counts"], dict)


def test_an_earlier_run_is_search_changed_after_the_amendment_and_a_staged_export_is_untouched(plan):
    client, ws, _app = plan
    read = _search(client)
    run = ws / "literature" / "search_runs" / "run_001"
    run.mkdir(parents=True)
    from scholar_harness.pipeline.discovery import protocol_search_record

    fingerprint, search = protocol_search_record(ws / "protocol.json")
    (run / "legs.json").write_text(json.dumps({"run": "run_001", "status": "COMPLETE", "legs": [
        {"provider": "openalex", "fetched": 781, "status": "ok"}], "protocol_fingerprint": fingerprint,
        "protocol_search": search}), encoding="utf-8")
    sources = ws / "literature" / "raw" / "ris" / "sources.json"
    sources.parent.mkdir(parents=True)
    sources.write_text(json.dumps({"sources": [{"id": "src_001", "label": "Scopus", "records": 618,
                                                "searched_on": "2026-11-20", "query": "TITLE-ABS-KEY(uav)"}]}), encoding="utf-8")
    staged = sources.read_bytes()
    manifest = json.loads((run / "legs.json").read_text(encoding="utf-8"))
    refuse_if_run_protocol_changed(ws, manifest)  # the run searched this protocol: no refusal yet
    dry = client.post(AMEND, json=_body(read, _merged(read), dry_run=True)).json()
    assert dry["consequences"]["runs"] == [{"run": "run_001", "records": 781, "status": "COMPLETE"}]
    assert dry["consequences"]["exports"][0] | {} == {"id": "src_001", "database": "Scopus", "records": 618,
                                                      "staged_on": "2026-11-20", "string": "TITLE-ABS-KEY(uav)"}
    assert client.post(AMEND, json=_body(read, _merged(read))).status_code == 200
    runs = client.get(f"{PLAN}/runs").json()["runs"]
    assert next(r for r in runs if r["run"] == "run_001")["search_changed"] is True
    assert sources.read_bytes() == staged
    # The earlier harvest can no longer become the corpus: the accept refuses it.
    with pytest.raises(AcceptCorpusRefused) as refused:
        refuse_if_run_protocol_changed(ws, manifest)
    assert refused.value.code == "PROTOCOL_CHANGED_SINCE_RUN"


def test_with_no_count_every_database_reads_not_counted_in_the_answer_and_the_journal(plan):
    client, ws, _app = plan
    read = _search(client)
    assert not qw.workspace_log_path(ws).exists()
    dry = client.post(AMEND, json=_body(read, _merged(read), dry_run=True)).json()
    assert dry["counts"] and all(pair == {"before": "not counted", "after": "not counted"} for pair in dry["counts"].values())
    assert client.post(AMEND, json=_body(read, _merged(read))).status_code == 200
    row = [e for e in _journal(ws) if e["action"] == "PROTOCOL_AMENDED"][-1]
    assert row["parameters"]["counts"] == dry["counts"]


def test_a_logged_count_of_the_protocols_string_is_the_before_number(plan):
    from scholar_search.protocol_adapter import compile_protocol_search

    client, ws, _app = plan
    read = _search(client)
    query, names = compile_protocol_search(ws / "protocol.json")
    name = run_providers(names)[0]
    _countable, (string,) = qw._translate(name, [(wb.Variant("full", wb.Version((wb.Concept("x", ("x",)),))), query)])
    qw.CountLog(qw.workspace_log_path(ws)).append([{
        "key": qw.cache_key(name, string, query), "kind": "full", "status": "counted", "total": 781,
        "counted_at": "2026-11-21T09:00:00Z",
    }])
    dry = client.post(AMEND, json=_body(read, _merged(read), dry_run=True)).json()
    assert dry["counts"][name] == {"before": 781, "after": "not counted"}


def test_an_unknown_database_in_the_protocol_is_left_out_not_a_server_error(plan):
    client, ws, _app = plan
    # A hand-written or imported protocol: the names in the intent and the protocol alike.
    names = ["openalex", "Scopus", "made-up"]
    for file, holder in (("intent.json", lambda d: d), ("protocol.json", lambda d: d["search_strategy"])):
        data = json.loads((ws / file).read_text(encoding="utf-8"))
        holder(data)["target_databases"] = names
        (ws / file).write_text(json.dumps(data), encoding="utf-8")
    read = _search(client)
    dry = client.post(AMEND, json=_body(read, _merged(read), dry_run=True))
    assert dry.status_code == 200, dry.text
    assert list(dry.json()["counts"]) == ["openalex"]
    assert client.post(AMEND, json=_body(read, _merged(read))).status_code == 200


def test_the_estimate_line_is_the_engines_and_only_when_one_was_counted_for_this_protocol(plan):
    client, ws, app = plan
    read = _search(client)
    assert client.post(AMEND, json=_body(read, _merged(read), dry_run=True)).json()["consequences"]["estimate"] is False
    app.state.estimate_cache = {(str(ws), "sha256:" + "0" * 64, ("openalex",)): {}}
    assert client.post(AMEND, json=_body(read, _merged(read), dry_run=True)).json()["consequences"]["estimate"] is False
    app.state.estimate_cache[(str(ws), read["protocol_fingerprint"], ("openalex",))] = {}
    assert client.post(AMEND, json=_body(read, _merged(read), dry_run=True)).json()["consequences"]["estimate"] is True


def test_open_assistant_proposals_are_counted_and_read_stale_after_the_amendment(plan):
    client, ws, _app = plan
    read = _search(client)
    made, created = WP.make(ws, source="assistant:test", field="languages", op="add", value="fr", why="French studies",
                            evidence=[])
    assert created and made["status"] == "open"
    dry = client.post(AMEND, json=_body(read, _merged(read), dry_run=True)).json()
    assert dry["consequences"]["proposals"] == 1
    assert client.post(AMEND, json=_body(read, _merged(read))).status_code == 200
    assert WP.listing(ws)["counts"]["stale"] == 1


def test_a_change_outside_the_search_is_refused_and_writes_nothing(plan, monkeypatch):
    from scholar_harness.inception import proposals as P

    client, ws, _app = plan
    read = _search(client)
    before = _bytes(ws)

    def outside(_protocol, _intent):
        raise P.ProposalRefused("PROTOCOL_AMENDMENT_REFUSED", "the change reaches eligibility", 422,
                                {"reason": "outside_search"})

    monkeypatch.setattr(WP, "compile_amendment", outside)
    response = client.post(AMEND, json=_body(read, _merged(read)))
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "PROTOCOL_AMENDMENT_REFUSED" and detail["details"]["reason"] == "outside_search"
    assert _bytes(ws) == before


def test_a_concept_kept_under_its_name_keeps_its_operator():
    intent = {"core_concepts": [{"concept": "uav", "synonyms": ["drone"], "boolean_operator": "AND"},
                                {"concept": "weed", "synonyms": []}]}
    new = WP._replace_concepts(intent, [{"concept": "uav", "synonyms": ["drone", "uas"]},
                                        {"concept": "crop", "synonyms": []}])
    assert new["core_concepts"][0]["boolean_operator"] == "AND"
    assert "boolean_operator" not in new["core_concepts"][1]


def test_the_reason_is_one_sentence_and_required(plan):
    client, ws, _app = plan
    read = _search(client)
    before = _bytes(ws)
    for reason in ("", "   ", "x" * 2_001, "x" * 5_000):
        response = client.post(AMEND, json=_body(read, _merged(read), reason=reason))
        assert response.status_code == 422 and response.json()["detail"]["code"] == refusals.WORKBENCH_REASON_INVALID
    assert _bytes(ws) == before


def test_a_protocol_changed_since_the_page_read_it_is_refused(plan):
    client, ws, _app = plan
    read = _search(client)
    stale = _body(read, _merged(read), protocol_fingerprint="sha256:" + "0" * 64)
    response = client.post(AMEND, json=stale)
    assert response.status_code == 409 and response.json()["detail"]["code"] == refusals.WORKBENCH_PROTOCOL_CHANGED


def test_the_protocols_own_search_is_nothing_to_record(plan):
    client, ws, _app = plan
    read = _search(client)
    response = client.post(AMEND, json=_body(read, read["search"]["concepts"]))
    assert response.status_code == 422 and response.json()["detail"]["code"] == refusals.WORKBENCH_VERSION_INVALID


def test_after_the_corpus_is_accepted_nothing_is_amended(plan, monkeypatch):
    client, ws, _app = plan
    read = _search(client)
    monkeypatch.setattr(WP, "frozen", lambda _ws: True)
    response = client.post(AMEND, json=_body(read, _merged(read)))
    assert response.status_code == 409 and response.json()["detail"]["code"] == "CORPUS_ALREADY_ACCEPTED"


def test_a_running_job_refuses_the_amendment(plan):
    client, ws, app = plan
    read = _search(client)
    jobs = DiscoveryJobs()
    jobs.jobs["djob_1"] = DiscoveryJob("djob_1", str(app.state.workspace), "run")
    app.state.discovery_jobs = jobs
    response = client.post(AMEND, json=_body(read, _merged(read)))
    assert response.status_code == 409 and response.json()["detail"]["code"] == "DISCOVERY_JOB_ACTIVE"
    assert client.post(AMEND, json=_body(read, _merged(read), dry_run=True)).status_code == 200


def test_the_route_is_in_both_allow_lists_and_not_a_phone_route():
    from scholar_harness.console import serve

    path = "api/v1/discovery/workbench/amend"
    assert any(p.fullmatch(path) for p in browser.POST_PATHS)
    patterns = [re.compile(m.group(1).replace("\\/", "/"))
                for m in re.finditer(r"^\s*/(\^api.*\$)/,", PROXY.read_text(encoding="utf-8"), re.M)]
    assert any(p.fullmatch(path) for p in patterns)
    assert not serve._phone_may_reach("POST", "/" + path)


def test_the_refusal_codes_are_registered():
    for code in ("WORKBENCH_REASON_INVALID", "WORKBENCH_PROTOCOL_CHANGED"):
        assert getattr(refusals, code) == code and code in refusals.CONTRACT_ADDED
