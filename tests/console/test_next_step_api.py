"""The next-step bar's answer (M10b Part C, ``docs/ux/shared/final/04-next-step.md``).

``GET /api/v1/review/next-step`` and ``GET /api/v1/inception/drafts/{id}/next-step``,
built by ``console/next_step.py`` from the workspace folder and the job registries.
Offline, on the doubles of ``test_discovery_api.py``. Strict-run finding 11: after
a harvest nothing on Discovery pointed to the Hand-off, and the Hand-off itself
said there was nothing to hand off while the corpus was still being prepared.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from scholar_search.config import settings
from test_inception_proposals import uav_draft

from scholar_harness.console import create_app
from scholar_harness.console.api import discovery as D
from scholar_harness.console.api import screening_v1 as S
from scholar_harness.pipeline import harvest_marker

_SPEC = importlib.util.spec_from_file_location(
    "_discovery_api_helpers_next", Path(__file__).resolve().parent / "test_discovery_api.py"
)
h = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(h)
_PREP = importlib.util.spec_from_file_location(
    "_harvest_preparation_helpers_next", Path(__file__).resolve().parent / "test_harvest_preparation_api.py"
)
prep = importlib.util.module_from_spec(_PREP)
_PREP.loader.exec_module(prep)

env = h.env


@pytest.fixture(autouse=True)
def _protocol_from_inception(request):
    """The double scaffolds a placeholder workspace and copies the golden protocol in, which only a genesis does
    for real; ``protocol_origin`` says so, as genesis writes it."""
    if "env" in request.fixturenames:
        _client, ws, _ = request.getfixturevalue("env")
        manifest = json.loads((ws / "project.json").read_text(encoding="utf-8"))
        manifest["protocol_origin"] = "inception"
        (ws / "project.json").write_text(json.dumps(manifest), encoding="utf-8")


NEXT = "/api/v1/review/next-step"
ACCEPT = "/api/v1/screening/corpus/accept"
TOKEN = h.TOKEN


def _next(client) -> dict:
    answer = client.get(NEXT)
    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert body["shape"] == "review.next-step-v1" and body["computed_at"]
    return body


def _legs(fetched: dict[str, int]) -> list[dict]:
    return [
        {"provider": p, "query_id": "Q", "executed_query": "q", "reported_total": n, "fetched": n, "cap": 10000,
         "cap_source": "engine_ceiling", "cap_hit": False, "status": "ok", "error": None, "notes": [], "request": {},
         "started_at": "2026-11-13T08:00:00Z", "finished_at": "2026-11-13T09:40:00Z"}
        for p, n in fetched.items()
    ]


def _harvested(ws: Path, run: int = 1, *, done: tuple[str, ...] = ("deduplication", "hydration")) -> Path:
    """A harvest of 1,074 records whose search ended; 1,050 works after duplicates; preparation not ended."""
    from scholar_harness.pipeline.discovery import protocol_search_record

    path = h._write_run(ws, run, started="2026-11-13T08:00:00Z", legs=_legs({"openalex": 600, "crossref": 474}))
    manifest = json.loads((path / "legs.json").read_text(encoding="utf-8"))
    manifest["protocol_fingerprint"], manifest["protocol_search"] = protocol_search_record(ws / "protocol.json")
    (path / "legs.json").write_text(json.dumps(manifest), encoding="utf-8")  # the search of this protocol
    (path / "raw.json").write_text("[]", encoding="utf-8")
    (ws / "literature" / "deduped.json").write_text(json.dumps([{"title": f"w{i}"} for i in range(1050)]), encoding="utf-8")
    harvest_marker.start(path)
    for stage in done:
        harvest_marker.record_stage(path, stage, "DONE")
    return path


def _live_job(client, kind: str, preparing_run: str | None):
    job = D.DiscoveryJob(job_id="djob_ab12cd34ef56ab12", workspace=str(client.app.state.workspace), kind=kind,
                         preparing_run=preparing_run)
    client.app.state.discovery_jobs = jobs = getattr(client.app.state, "discovery_jobs", None) or D.DiscoveryJobs()
    jobs.jobs[job.job_id] = job
    return job


# --------------------------------------------------------------------------- the Hand-off case


@pytest.mark.parametrize(("done", "stage"), [
    (("deduplication", "hydration"), "verifying"),
    (("deduplication",), "adding_abstracts"),
    ((), "deduplicating"),
])
def test_harvest_finished_verification_running_is_corpus_pending_waiting(env, done, stage):
    """Reproducing (strict-run finding 11): the folder reads "Not ready" on the Hand-off, and no route said what was next."""
    client, ws, _ = env
    _harvested(ws, done=done)
    _live_job(client, "prepare", "run_001")
    handoff = client.get(f"{h.BASE}/handoff").json()
    assert handoff["preparation"]["state"] == "running"
    body = _next(client)
    assert (body["state"], body["phase"], body["scope"]) == ("CORPUS_PENDING", "discovery", "workspace")
    assert body["waiting"]["kind"] == "running" and body["waiting"]["stage"] == stage
    assert body["waiting"]["job"]["job_id"] == "djob_ab12cd34ef56ab12"
    assert body["params"]["works"] == 1050 and body["params"]["records"] == 1074 and body["params"]["run"] == "run_001"
    assert body["action"] == {"key": "followSearch", "to": {"screen": "discovery.harvest", "query": {"job": "djob_ab12cd34ef56ab12"}}}
    assert "accept" not in json.dumps(body).lower().replace("accepting_chase", "")


def test_marker_without_job_is_interrupted(env):
    client, ws, _ = env
    _harvested(ws)
    body = _next(client)
    assert body["state"] == "CORPUS_PENDING"
    assert body["waiting"]["kind"] == "interrupted" and body["waiting"]["stage"] == "verifying"
    assert body["waiting"]["reason"]["code"] == "INTERRUPTED"
    assert body["action"]["key"] == "finishPreparing" and body["action"]["to"] == {"screen": "discovery.harvest", "query": {"run": "run_001"}}
    assert [a["key"] for a in body["also"]] == ["searchAgain"]


def test_cannot_finish_offers_search_again_only(env):
    client, ws, _ = env
    path = _harvested(ws)
    (path / "raw.json").unlink()
    body = _next(client)
    assert body["waiting"]["kind"] == "interrupted" and body["action"]["key"] == "searchAgain" and body["also"] == []
    assert body["params"]["cannot_finish"] == "records_missing"


def test_failed_preparation_keeps_its_stage_and_message(env, monkeypatch):
    client, ws, _ = env
    prep._fail_verification_once(client, monkeypatch)
    body = _next(client)
    assert body["state"] == "CORPUS_PENDING"
    assert body["waiting"]["kind"] == "failed" and body["waiting"]["stage"] == "verifying"
    assert body["waiting"]["reason"]["code"] == "DISCOVERY_FAILED" and "verifier down" in body["waiting"]["reason"]["message"]
    assert body["action"]["key"] == "finishPreparing" and [a["key"] for a in body["also"]] == ["searchAgain"]


def test_stopped_preparation_offers_finish(env):
    client, ws, _ = env
    path = _harvested(ws)
    harvest_marker.end(path, "STOPPED", stage="verification")
    body = _next(client)
    assert body["waiting"]["kind"] == "stopped" and body["waiting"]["stage"] == "verifying"
    assert body["waiting"]["reason"]["code"] == "STOPPED_BY_RESEARCHER"
    assert body["action"]["key"] == "finishPreparing"


def test_failed_preparation_after_restart_offers_finish(env, tmp_path):
    """The marker survives a console restart: a new app reads the same folder."""
    client, ws, _ = env
    path = _harvested(ws)
    harvest_marker.end(path, "FAILED", stage="hydration", message="the abstracts service did not answer")
    app = create_app(ws, token=TOKEN, workspaces_root=ws.parent)
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as fresh:
        body = _next(fresh)
    assert body["waiting"]["kind"] == "failed" and body["waiting"]["stage"] == "adding_abstracts"
    assert body["waiting"]["reason"] == {"code": "DISCOVERY_FAILED", "message": "the abstracts service did not answer"}
    assert body["action"]["key"] == "finishPreparing"


def test_stale_verified_from_an_earlier_run_is_not_ready(env):
    client, ws, _ = env
    h._write_run(ws, 1, started="2026-11-10T08:00:00Z")
    (ws / "literature" / "verified.json").write_text(json.dumps([{"title": "A", "provider": "openalex"}]), encoding="utf-8")
    _harvested(ws, run=2)
    body = _next(client)
    assert body["state"] == "CORPUS_PENDING" and body["params"]["run"] == "run_002"


def test_staged_exports_win_over_an_unfinished_harvest(env):
    from scholar_harness.corpus_accept import stage_ris_source

    client, ws, _ = env
    _harvested(ws)
    ris = b"TY  - JOUR\nTI  - A staged record\nPY  - 2023\nDO  - 10.1/staged\nER  - \n"
    stage_ris_source(ws, "Scopus", ris, file_name="export.ris", searched_on="2026-11-01")
    body = _next(client)
    assert body["state"] == "STAGED_EXPORTS" and body["params"] == {"n": 1}
    assert body["action"]["key"] == "reviewExports" and body["action"]["to"]["screen"] == "discovery.handoff"


# --------------------------------------------------------------------------- the search


def test_first_harvest_searching_is_search_unfinished(env):
    client, _ws, _ = env
    job = _live_job(client, "run", None)
    job.emit("leg", {"provider": "openalex", "status": "ok", "fetched": 10})
    job.emit("leg", {"provider": "crossref", "status": "running", "fetched": 1})
    body = _next(client)
    assert body["state"] == "SEARCH_UNFINISHED"
    assert body["waiting"]["kind"] == "running" and body["waiting"]["stage"] == "searching"
    assert body["params"]["answered"] == 1 and body["params"]["databases"] >= 1
    assert body["action"]["key"] == "followSearch" and body["action"]["to"]["query"] == {"job": job.job_id}


def test_stopped_search_is_search_unfinished(env):
    client, ws, _ = env
    run = h._write_run(ws, 1, started="2026-11-13T08:00:00Z", published=False)
    manifest = json.loads((run / "legs.json").read_text(encoding="utf-8"))
    manifest["status"] = "PARTIAL"
    (run / "legs.json").write_text(json.dumps(manifest), encoding="utf-8")
    body = _next(client)
    assert body["state"] == "SEARCH_UNFINISHED" and body["waiting"]["kind"] == "stopped" and body["waiting"]["stage"] == "searching"
    assert body["waiting"]["reason"]["code"] == "STOPPED_BY_RESEARCHER" and body["action"]["key"] == "searchAgain"


def test_failed_search_is_search_unfinished(env):
    client, ws, _ = env
    run = h._write_run(ws, 1, started="2026-11-13T08:00:00Z", published=False)
    manifest = json.loads((run / "legs.json").read_text(encoding="utf-8"))
    manifest["status"] = "FAILED"
    (run / "legs.json").write_text(json.dumps(manifest), encoding="utf-8")
    body = _next(client)
    assert body["waiting"]["kind"] == "failed" and body["waiting"]["reason"]["code"] == "PROVIDERS_FAILED"
    assert body["action"]["key"] == "searchAgain"


# --------------------------------------------------------------------------- one test per row of table 1


def test_no_workspace_answers_no_review(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    app = create_app(None, token=TOKEN, workspaces_root=root)
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        body = _next(client)
        assert body["state"] == "NO_REVIEW" and body["action"]["to"]["screen"] == "inception.list"
        from scholar_harness.workspace import catalog

        catalog.create(root, "Another review")
        assert _next(client)["action"] == {"key": "chooseReview", "to": {"screen": "workspaces", "query": {}}}
        # The other workspace routes still refuse without a workspace.
        assert client.get("/api/v1/discovery/runs").status_code == 409


def test_no_protocol(env):
    client, ws, _ = env
    (ws / "protocol.json").unlink()
    body = _next(client)
    assert body["state"] == "NO_PROTOCOL" and body["action"]["to"]["screen"] == "inception.list"


def test_protocol_invalid(env):
    client, ws, _ = env
    (ws / "protocol.json").write_text("{not json", encoding="utf-8")
    assert _next(client)["state"] == "PROTOCOL_INVALID"


def test_protocol_placeholder(env):
    client, ws, _ = env
    manifest = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    manifest["protocol_origin"] = "placeholder"
    (ws / "project.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert _next(client)["state"] == "PROTOCOL_PLACEHOLDER"
    manifest.pop("protocol_origin")
    (ws / "project.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert _next(client)["state"] == "READY_TO_SEARCH", "a workspace without the field is never a placeholder"


@pytest.mark.parametrize(("mailto", "key", "what"), [
    (None, "k", "email"), ("a@b.invalid", None, "key"), (None, None, "both"),
])
def test_setup_needed(env, monkeypatch, mailto, key, what):
    client, _ws, _ = env
    monkeypatch.setattr(settings, "mailto", mailto)
    monkeypatch.setattr(settings, "openalex_key", key)
    body = _next(client)
    assert body["state"] == "SETUP_NEEDED" and body["params"] == {"what": what}
    assert body["action"] == {"key": "seeWhatToSet", "to": {"screen": "discovery.plan", "query": {}}}


def test_ready_to_search(env):
    client, _ws, _ = env
    body = _next(client)
    assert body["state"] == "READY_TO_SEARCH" and body["action"]["to"]["screen"] == "discovery.harvest"
    assert body["waiting"] is None and body["unknown"] == [] and body["protocol_fingerprint"]


def test_corpus_ready_then_accepted_then_not_prepared(env):
    client, ws, _ = env
    job, _ = h._run(client, {"providers": ["openalex", "crossref"]})
    assert job["state"] == "succeeded", job
    body = _next(client)
    assert body["state"] == "CORPUS_READY" and body["action"]["key"] == "reviewCorpus"
    assert body["action"]["to"]["screen"] == "discovery.handoff"
    assert body["params"]["records"] == 8 and body["params"]["works"] == 8
    assert client.post(ACCEPT).status_code == 200
    body = _next(client)
    assert body["state"] == "NOT_PREPARED" and body["action"]["to"]["screen"] == "screening.home"


def test_search_changed(env, monkeypatch):
    client, _ws, _ = env
    job, _ = h._run(client, {"providers": ["openalex"]})
    assert job["state"] == "succeeded"
    monkeypatch.setattr(D, "_drift", lambda ws, manifest: {"protocol_changed": True, "search_changed": True})
    body = _next(client)
    assert body["state"] == "SEARCH_CHANGED" and body["params"] == {"run": "run_001"}


def test_corpus_ready_names_a_protocol_change_outside_the_search(env, monkeypatch):
    client, _ws, _ = env
    h._run(client, {"providers": ["openalex"]})
    monkeypatch.setattr(D, "_drift", lambda ws, manifest: {"protocol_changed": True, "search_changed": False})
    body = _next(client)
    assert body["state"] == "CORPUS_READY" and body["params"]["protocol_changed"] is True


def _accepted(client) -> None:
    job, _ = h._run(client, {"providers": ["openalex"]})
    assert job["state"] == "succeeded"
    assert client.post(ACCEPT).status_code == 200


def _summary(monkeypatch, **kw) -> None:
    base = {"total": 10, "decided": 0, "needs_you": 0, "conflicts": 0, "protocol_changed": False}
    monkeypatch.setattr(S, "summary_of", lambda ws: {**base, **kw})


def test_preparing_batches_waits(env):
    client, _ws, _ = env
    _accepted(client)
    client.app.state.job_runner.jobs["j1"] = type("J", (), {
        "to_dict": lambda self: {"job_id": "j1", "action_id": "screen_prepare", "state": "running", "started_at": "t"},
    })()
    body = _next(client)
    assert body["state"] == "NOT_PREPARED" and body["waiting"]["stage"] == "preparing"
    assert body["action"]["key"] == "followPreparation"


@pytest.mark.parametrize(("summary", "state", "params", "screen"), [
    ({"protocol_changed": True, "needs_you": 3}, "PROTOCOL_CHANGED_AFTER_BATCHES", {}, "inception.list"),
    ({"conflicts": 2, "needs_you": 3}, "CONFLICTS", {"n": 2}, "screening.home"),
    ({"needs_you": 3}, "SCREENING", {"needs_you": 3, "total": 10}, "screening.triage"),
    ({}, "READY_TO_PUBLISH", {}, "screening.publish"),
])
def test_screening_rows_in_order(env, monkeypatch, summary, state, params, screen):
    client, _ws, _ = env
    _accepted(client)
    _summary(monkeypatch, **summary)
    body = _next(client)
    assert (body["state"], body["params"], body["action"]["to"]["screen"]) == (state, params, screen)
    assert body["phase"] == "screening"


def _published(ws: Path, monkeypatch, current: bool, chase: dict) -> None:
    from scholar_harness.authority.generations import GenerationStatus
    from scholar_harness.screening import currentness

    path = ws / "literature" / "screening" / "generation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")
    status = GenerationStatus.CURRENT if current else GenerationStatus.STALE
    result = type("R", (), {"status": status, "code": None if current else "GENERATION_STALE", "details": {}})()
    monkeypatch.setattr(currentness, "screening_currentness", lambda w: result)
    view = {"screening": {"published": True, "round": chase.get("round", 1)}, "seeds": {"chaseable": chase.get("chaseable", 3)},
            "runs": chase.get("runs", [])}
    monkeypatch.setattr(D, "_chase_view", lambda w: view)


@pytest.mark.parametrize(("current", "chase", "state", "params"), [
    (False, {}, "PUBLISHED_STALE", {"code": "GENERATION_STALE"}),
    (True, {}, "PUBLISHED", {}),
    (True, {"runs": [{"published": True, "accepted": None, "counts": {"new": 12}}]}, "CHASE_READY_TO_SEND", {"new": 12, "round": 2}),
    (True, {"runs": [{"published": True, "accepted": None, "counts": {"new": 0}}]}, "CHASE_NOTHING_NEW", {}),
    (True, {"chaseable": 0}, "DONE", {"chaseable": 0}),
    (True, {"runs": [{"published": True, "accepted": {"round": 2}, "counts": {"new": 4}}], "round": 2}, "DONE", {"chaseable": 3, "round": 2}),
])
def test_publication_and_chase_rows(env, monkeypatch, current, chase, state, params):
    client, ws, _ = env
    _accepted(client)
    _summary(monkeypatch)
    _published(ws, monkeypatch, current, chase)
    body = _next(client)
    assert (body["state"], body["params"]) == (state, params)


def test_a_chase_after_round_two_sends_round_three(env, monkeypatch):
    """Review of the bar (UI agent): the round suffix overwrote the chase's own round."""
    client, ws, _ = env
    _accepted(client)
    _summary(monkeypatch)
    _published(ws, monkeypatch, True, {"round": 2, "runs": [{"published": True, "accepted": None, "counts": {"new": 5}}]})
    body = _next(client)
    assert (body["state"], body["round"], body["params"]) == ("CHASE_READY_TO_SEND", 2, {"new": 5, "round": 3})


def test_round_two_not_prepared_is_round_accepted(env, monkeypatch):
    client, ws, _ = env
    _accepted(client)
    _summary(monkeypatch, total=0)
    monkeypatch.setattr(D, "_chase_view", lambda w: {"screening": {"published": True, "round": 2}, "seeds": {}, "runs": []})
    body = _next(client)
    assert (body["state"], body["round"], body["params"]) == ("ROUND_ACCEPTED", 2, {"round": 2})


def test_a_running_chase_waits(env, monkeypatch):
    client, ws, _ = env
    _accepted(client)
    _summary(monkeypatch)
    _published(ws, monkeypatch, True, {})
    job = _live_job(client, "chase", None)
    body = _next(client)
    assert body["waiting"]["stage"] == "chasing" and body["action"]["key"] == "followChase"
    assert body["action"]["to"]["query"] == {"job": job.job_id}


# --------------------------------------------------------------------------- the draft route


def _draft_client(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    app = create_app(None, token=TOKEN, workspaces_root=root)
    return TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"})


def test_draft_rows(tmp_path):
    with _draft_client(tmp_path) as client:
        sid = client.post("/api/v1/inception/drafts", json={"draft": {"topic": ""}}).json()["session_id"]
        body = client.get(f"/api/v1/inception/drafts/{sid}/next-step").json()
        assert body["scope"] == "draft" and body["state"] == "DRAFT_STARTED"
        assert body["action"] == {"key": "goToStep", "to": {"screen": "inception.scope", "query": {"draft": sid}}}

        sid = client.post("/api/v1/inception/drafts", json={"draft": {"topic": "Weed detection from drones"}}).json()["session_id"]
        body = client.get(f"/api/v1/inception/drafts/{sid}/next-step").json()
        assert body["state"] == "DRAFT_INCOMPLETE" and body["params"]["step"] == "shape"
        assert body["params"]["fields"][:2] == ["paradigm", "playbook"] and "title" in body["params"]["fields"]
        assert body["action"]["to"] == {"screen": "inception.shape", "query": {"draft": sid}}

        assert client.get("/api/v1/inception/drafts/rec_00000000000000000000000000000000/next-step").status_code == 404


def test_draft_ready_follows_the_checks_ready_flag(tmp_path):
    """All fields present and one undecided wizard criterion: not ready, as Review's "Must fix" row says."""
    with _draft_client(tmp_path) as client:
        draft = uav_draft(proof="field-validated accuracy", extra_inclusions=[])
        sid = client.post("/api/v1/inception/drafts", json={"draft": draft}).json()["session_id"]
        crit = client.post("/api/v1/inception/steps/criteria", json={"draft": draft}).json()["criteria"]
        wizard = [c["id"] for c in crit if c["generated"]]
        undecided = {**draft, "criteria_decisions": {w: True for w in wizard[1:]}}
        record = client.get(f"/api/v1/inception/drafts/{sid}").json()
        client.put(f"/api/v1/inception/drafts/{sid}", json={"draft": undecided, "base_updated_at": record["updated_at"]})
        body = client.get(f"/api/v1/inception/drafts/{sid}/next-step").json()
        assert body["state"] == "DRAFT_INCOMPLETE" and body["params"]["step"] == "criteria", body
        record = client.get(f"/api/v1/inception/drafts/{sid}").json()
        decided = {**draft, "criteria_decisions": {w: True for w in wizard}}
        client.put(f"/api/v1/inception/drafts/{sid}", json={"draft": decided, "base_updated_at": record["updated_at"]})
        checks = client.post(f"/api/v1/inception/drafts/{sid}/checks", json={}).json()
        body = client.get(f"/api/v1/inception/drafts/{sid}/next-step").json()
        assert checks["ready"] is True and body["state"] == "DRAFT_READY", body
        assert body["action"]["to"] == {"screen": "inception.review", "query": {"draft": sid}}
        made = client.post(f"/api/v1/inception/drafts/{sid}/genesis", json={})
        assert made.status_code == 201, made.text
        body = client.get(f"/api/v1/inception/drafts/{sid}/next-step").json()
        assert body["state"] == "DRAFT_CREATED" and body["params"]["title"] == draft["title"]
        assert body["action"]["key"] == "goToDone"


# --------------------------------------------------------------------------- the route


def test_an_unreadable_source_goes_to_unknown(env, monkeypatch):
    client, _ws, _ = env

    def broken(ws):
        raise OSError("disk")

    monkeypatch.setattr(S, "_corpus_view", broken)
    body = _next(client)
    assert body["state"] == "READY_TO_SEARCH" and body["unknown"] == ["corpus"]


def test_phone_token_refused(env, tmp_path):
    _client, ws, _ = env
    app = create_app(ws, token=TOKEN, phone_tokens={"phone-token"}, workspaces_root=ws.parent)
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": "Bearer phone-token"}) as phone:
        refused = phone.get(NEXT)
    assert refused.status_code == 403 and refused.json()["detail"]["code"] == "TOKEN_SCOPE_REFUSED"


def test_no_etag_header_and_nothing_written(env):
    client, ws, _ = env
    journal = ws / "audit" / "journal.jsonl"
    before = journal.read_bytes() if journal.exists() else b""
    answer = client.get(NEXT, headers={"If-None-Match": '"x"'})
    assert answer.status_code == 200 and "etag" not in {k.lower() for k in answer.headers}
    assert (journal.read_bytes() if journal.exists() else b"") == before


def test_every_state_and_stage_is_named_in_the_builder():
    from scholar_harness.console import next_step

    assert len(next_step.STATES) == 26 and len(set(next_step.STATES)) == 26
    assert set(next_step.STAGE_NAMES.values()) <= set(next_step.WAITING_STAGES)
    assert shutil.which  # keep the import used on every platform


def test_a_publication_status_that_cannot_be_read_asks_to_publish_again_and_says_so(env, monkeypatch):
    """Review of Part C, finding 2 (decision item 41): never a guess of CURRENT."""
    from scholar_harness.screening import currentness

    client, ws, _ = env
    _accepted(client)
    _summary(monkeypatch)
    path = ws / "literature" / "screening" / "generation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")

    def unreadable(w):
        raise OSError("disk")

    monkeypatch.setattr(currentness, "screening_currentness", unreadable)
    body = _next(client)
    assert body["state"] == "PUBLISHED_STALE" and "publication" in body["unknown"] and body["params"] == {"code": None}
