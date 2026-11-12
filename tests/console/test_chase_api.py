"""M3g-citation-chasing: the chase routes under ``/api/v1/discovery/chase`` (offline, fake databases)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from scholar_search.config import settings

from scholar_harness.console import create_app
from scholar_harness.console.browser import POST_PATHS
from scholar_harness.pipeline import discovery as disc
from scholar_harness.screening import events as ev
from scholar_harness.screening.batcher import cmd_prepare

_SPEC = importlib.util.spec_from_file_location(
    "_chase_run_helpers", Path(__file__).resolve().parents[1] / "pipeline" / "test_citation_chase.py"
)
h = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(h)

TOKEN = "desk-token"
BASE = "/api/v1/discovery"


@pytest.fixture
def env(tmp_path, monkeypatch):
    ws = h.build_ws(tmp_path)
    monkeypatch.setattr(settings, "openalex_key", "console-test-key")  # a placeholder, never sent
    monkeypatch.setattr(settings, "s2_key", None)
    app = create_app(ws, token=TOKEN)
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        yield client, ws


def _install(monkeypatch, *providers) -> None:
    by_name = {p.name: p for p in providers}
    monkeypatch.setattr(disc, "_resolve_providers", lambda names: [by_name[n] for n in names if n in by_name] or None)


def _code(response) -> str:
    return response.json()["detail"]["code"]


def _events(client, job_id: str) -> list[tuple[str, dict]]:
    out, name = [], None
    with client.stream("GET", f"{BASE}/jobs/{job_id}/events") as stream:
        for line in stream.iter_lines():
            if line.startswith("event: "):
                name = line[len("event: "):]
            elif line.startswith("data: "):
                out.append((name, json.loads(line[len("data: "):])))
    return out


def _run(client, body: dict | None = None) -> tuple[dict, list[tuple[str, dict]]]:
    started = client.post(f"{BASE}/chase/runs", json=body or {})
    assert started.status_code == 202, started.text
    job = started.json()["job"]
    events = _events(client, job["job_id"])
    return client.get(f"{BASE}/jobs/{job['job_id']}").json()["job"], events


def test_the_chase_state_before_any_run(env):
    client, ws = env
    state = client.get(f"{BASE}/chase").json()
    assert state["shape"] == "discovery.chase-v1"
    assert state["screening"] == {**state["screening"], "published": True, "round": 1, "arm": "databases"}
    assert state["screening"]["generation_id"].startswith("GEN-")
    assert state["seeds"] == {"source": "included", "total": 1, "chaseable": 1, "not_chaseable": []}
    assert state["keys"] == {"openalex_key_set": True, "s2_key_set": False}
    assert state["defaults"] == {"directions": ["forward", "backward"], "providers": ["openalex", "semanticscholar"],
                                 "forward_cap": 500, "run_ceiling": 5000}
    assert state["runs"] == [] and state["latest"] is None and state["active_job"] is None


def test_a_chase_job_streams_its_legs_and_the_state_shows_the_run(env, monkeypatch):
    client, ws = env
    cited = h._doc("Cited work", provider="openalex", pid="W1", doi="10.2/a", openalex="W1")
    ref = h._doc("A reference", provider="openalex", pid="W2", doi="10.2/b", openalex="W2", year=2021)
    _install(monkeypatch, h.FakeChaseProvider("openalex", citations={h.W_INCLUDE: [cited]}, references={h.W_INCLUDE: [ref]}),
             h.FakeChaseProvider("semanticscholar", citations={f"DOI:{h.DOI_INCLUDE}": [cited]}))

    job, events = _run(client, {"note": "from the browser", "cap_per_seed": 50})
    assert job["state"] == "succeeded" and job["kind"] == "chase"
    assert job["result"]["chase"] == "chase_001" and job["result"]["status"] == "SUCCESS"
    assert job["result"]["counts"]["new"] == 2 and job["result"]["counts"]["duplicates_within_chase"] == 1
    legs = [data for name, data in events if name == "leg"]
    assert [(leg["provider"], leg["direction"], leg["fetched"], leg["status"]) for leg in legs] == [
        ("openalex", "forward", 1, "ok"), ("openalex", "backward", 1, "ok"),
        ("semanticscholar", "forward", 1, "ok"), ("semanticscholar", "backward", 0, "ok"),
    ]
    assert all(leg["seed"].startswith("STU-") and leg["cap"] in (50, None) for leg in legs)
    assert events[-1][0] == "done"
    summary = job["result"]["legs_summary"]
    assert summary[0] == {"provider": "openalex", "direction": "forward", "legs": 1, "ok": 1, "failed": 0, "skipped": 0,
                          "fetched": 1, "cap_hits": 0}

    state = client.get(f"{BASE}/chase").json()
    assert [r["chase"] for r in state["runs"]] == ["chase_001"]
    assert state["latest"]["chase"] == "chase_001" and state["latest"]["notes"] == ["from the browser"]
    assert state["latest"]["forward_cap"] == 50 and len(state["latest"]["legs_summary"]) == 4
    detail = client.get(f"{BASE}/chase/runs/chase_001")
    assert detail.status_code == 200 and detail.json()["counts"]["new"] == 2
    missing = client.get(f"{BASE}/chase/runs/chase_404")
    assert missing.status_code == 404 and _code(missing) == "CHASE_NOT_RUN"


def test_the_accept_starts_round_2_and_screening_home_offers_prepare(env, monkeypatch):
    client, ws = env
    docs = [h._doc(f"Chased {i}", provider="openalex", pid=f"W{i}", doi=f"10.2/{i}", openalex=f"W{i}") for i in range(3)]
    _install(monkeypatch, h.FakeChaseProvider("openalex", citations={h.W_INCLUDE: docs}))
    job, _ = _run(client, {"providers": ["openalex"], "directions": ["forward"]})
    assert job["state"] == "succeeded"

    response = client.post(f"{BASE}/chase/accept", json={})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["shape"] == "discovery.chase-accept-v1" and body["round"] == 2 and body["chase"] == "chase_001"
    assert body["corpus"]["records"] == 3 and body["corpus"]["artifact_id"].startswith("ART-corpus-")
    assert body["parent_corpus"].startswith("ART-corpus-") and body["archive_path"] == "literature/screening_rounds/round_001"
    assert "screening/" in body["archived"]

    # Screening Home: nothing prepared yet for round 2 (not round 1's counts).
    summary = client.get("/api/v1/screening/summary").json()
    assert summary["total"] == 0 and summary["decided"] == 0
    state = client.get(f"{BASE}/chase").json()
    assert state["screening"]["published"] is False and state["screening"]["round"] == 2
    assert state["runs"][0]["accepted"]["round"] == 2

    again = client.post(f"{BASE}/chase/accept", json={"chase": "chase_001"})
    assert again.status_code == 409 and _code(again) == "CHASE_ALREADY_ACCEPTED"
    rerun = client.post(f"{BASE}/chase/runs", json={})
    assert rerun.status_code == 409 and _code(rerun) == "SCREENING_NOT_PUBLISHED"

    # Prepare round 2 and read the PRISMA preview: the citation-searching arm.
    cmd_prepare(ws, batch_size=20)
    assert len(ev.load_context(ws).study_batch) == 3
    preview = client.get("/api/v1/screening/prisma/preview").json()
    assert preview["arm"] == "citation_searching" and preview["round"] == 2
    assert preview["identified"] == 3 and preview["duplicates_removed"] == 0 and preview["screened"] == 3
    assert preview["previous_rounds"][0]["round"] == 1 and preview["previous_rounds"][0]["prisma"]["records_screened"] == 3


def test_refusals_before_any_request(env, monkeypatch):
    client, ws = env
    _install(monkeypatch, h.FakeChaseProvider("openalex"))
    bad = client.post(f"{BASE}/chase/runs", json={"directions": ["sideways"]})
    assert bad.status_code == 422 and _code(bad) == "CHASE_DIRECTION_INVALID"
    seeds = client.post(f"{BASE}/chase/runs", json={"seeds": "everyone"})
    assert seeds.status_code == 422 and _code(seeds) == "CHASE_SEEDS_INVALID"
    unknown = client.post(f"{BASE}/chase/runs", json={"providers": ["nowhere"]})
    assert unknown.status_code == 422 and _code(unknown) == "PROVIDER_UNKNOWN"
    cap = client.post(f"{BASE}/chase/runs", json={"cap_per_seed": 0})
    assert cap.status_code == 422 and _code(cap) == "CAP_INVALID"
    extra = client.post(f"{BASE}/chase/runs", json={"depth": 2})
    assert extra.status_code == 422
    no_run = client.post(f"{BASE}/chase/accept", json={})
    assert no_run.status_code == 409 and _code(no_run) == "CHASE_NOT_RUN"

    monkeypatch.setattr(settings, "openalex_key", None)
    keyless = client.post(f"{BASE}/chase/runs", json={})
    assert keyless.status_code == 409 and _code(keyless) == "OPENALEX_KEY_NOT_SET"
    assert client.get(f"{BASE}/chase").json()["keys"]["openalex_key_set"] is False
    without_openalex = client.post(f"{BASE}/chase/runs", json={"providers": ["semanticscholar"]})
    assert without_openalex.status_code == 202  # the key is needed only when OpenAlex is asked
    _events(client, without_openalex.json()["job"]["job_id"])

    (ws / "literature" / "included.json").unlink()
    unpublished = client.post(f"{BASE}/chase/runs", json={"providers": ["semanticscholar"]})
    assert unpublished.status_code == 409 and _code(unpublished) == "SCREENING_NOT_PUBLISHED"
    assert client.get(f"{BASE}/chase").json()["screening"]["published"] is False


def test_a_failed_chase_is_a_failed_job_and_a_cancel_keeps_the_fetched_records(env, monkeypatch):
    from scholar_search.exceptions import ProviderError

    client, ws = env
    _install(monkeypatch, h.FakeChaseProvider("openalex", fail=ProviderError("openalex", "no", status_code=403)))
    job, events = _run(client, {"providers": ["openalex"]})
    assert job["state"] == "failed" and job["error"]["code"] == "PROVIDERS_FAILED"
    assert events[-1][0] == "failed"
    assert client.post(f"{BASE}/chase/accept", json={}).status_code == 409


def test_the_browser_may_post_the_chase_routes():
    assert any(p.fullmatch("api/v1/discovery/chase/runs") for p in POST_PATHS)
    assert any(p.fullmatch("api/v1/discovery/chase/accept") for p in POST_PATHS)
    assert not any(p.fullmatch("api/v1/discovery/chase/runs/chase_001") for p in POST_PATHS)



def test_f4_a_round_2_corpus_view_shows_the_chase(env, monkeypatch):
    """F4 with M3g: after the chase accept the corpus view is the citation-searching round's, not zeros."""
    client, ws = env
    docs = [h._doc(f"Chased {i}", provider="openalex", pid=f"W{i}", doi=f"10.2/{i}", openalex=f"W{i}") for i in range(3)]
    _install(monkeypatch, h.FakeChaseProvider("openalex", citations={h.W_INCLUDE: docs}))
    job, _ = _run(client, {"providers": ["openalex"], "directions": ["forward"]})
    assert job["state"] == "succeeded"
    assert client.post(f"{BASE}/chase/accept", json={}).status_code == 200

    corpus = client.get("/api/v1/screening/corpus").json()
    assert corpus["state"] == "ACCEPTED" and corpus["origin"] == "citation_searching"
    # Citation searching is not a database row: the chase's legs are not listed as databases.
    assert all(d.get("provider") != "openalex" or d.get("records") != 3 for d in corpus["databases"])
    assert corpus["preview"] == {"identified": 3, "duplicates": 0, "unique_studies": 3}
    assert corpus["accepted"]["records"] == 3


def test_f4_a_round_2_after_imports_keeps_the_imports_as_its_databases(env, monkeypatch):
    """Review finding 3: round 1 built from database exports; round 2 shows the chase counts, the exports' rows."""
    from scholar_harness import corpus_accept as ca

    client, ws = env
    docs = [h._doc(f"Chased {i}", provider="openalex", pid=f"W{i}", doi=f"10.2/{i}", openalex=f"W{i}") for i in range(3)]
    _install(monkeypatch, h.FakeChaseProvider("openalex", citations={h.W_INCLUDE: docs}))
    job, _ = _run(client, {"providers": ["openalex"], "directions": ["forward"]})
    assert job["state"] == "succeeded"
    assert client.post(f"{BASE}/chase/accept", json={}).status_code == 200
    # Round 1's staged exports stay on file after their accept, as an import leaves them.
    stored = ws / "literature" / "raw" / "ris" / "scopus.ris"
    stored.parent.mkdir(parents=True, exist_ok=True)
    stored.write_bytes(b"TY  - JOUR\nTI  - A record\nPY  - 2023\nER  -\n")
    ca._write_sources(ws, [{
        "id": "scopus-1", "label": "Scopus", "file_name": "scopus.ris", "records": 1, "searched_on": "2026-11-01",
        "query": "uav AND weed", "stored_as": "literature/raw/ris/scopus.ris", "format": "ris",
    }])

    corpus = client.get("/api/v1/screening/corpus").json()
    assert corpus["origin"] == "citation_searching" and corpus["from_discovery"] is False
    assert [d["label"] for d in corpus["databases"]] == ["Scopus"]
    assert [s["label"] for s in corpus["sources"]] == ["Scopus"]
    assert corpus["preview"] == {"identified": 3, "duplicates": 0, "unique_studies": 3}



def test_f2_an_archived_round_never_raises_the_protocol_flag(env, monkeypatch):
    """F2 with M3g: only the current round's batches are compared with the protocol."""
    client, ws = env
    docs = [h._doc(f"Chased {i}", provider="openalex", pid=f"W{i}", doi=f"10.2/{i}", openalex=f"W{i}") for i in range(3)]
    _install(monkeypatch, h.FakeChaseProvider("openalex", citations={h.W_INCLUDE: docs}))
    job, _ = _run(client, {"providers": ["openalex"], "directions": ["forward"]})
    assert job["state"] == "succeeded"
    assert client.post(f"{BASE}/chase/accept", json={}).status_code == 200
    cmd_prepare(ws, batch_size=20)
    registry = json.loads((ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8"))["artifacts"]
    current = {b.batch_id for b in ev.load_context(ws).batches.values()}
    archived = [
        ws / e["path"] for e in registry.values()
        if e.get("artifact_type") == "screening_batch"
        and json.loads((ws / e["path"]).read_text(encoding="utf-8"))["data"]["batch_id"] not in current
    ]
    assert archived, "round 1 left no batch artifact"
    for path in archived:  # as if round 1 had been prepared under another protocol
        envelope = json.loads(path.read_text(encoding="utf-8"))
        envelope["protocol_fingerprint"] = "sha256:" + "f" * 64
        path.write_text(json.dumps(envelope), encoding="utf-8")
    summary = client.get("/api/v1/screening/summary").json()
    assert summary["total"] == 3 and summary["protocol_changed"] is False

def test_a_new_chase_while_an_accept_is_pending_is_refused(env, monkeypatch):
    """Deferred M3g P3: the parent of a new chase is never an unscreened round snapshot."""
    from scholar_harness.screening import rounds

    client, ws = env
    docs = [h._doc(f"Chased {i}", provider="openalex", pid=f"W{i}", doi=f"10.2/{i}", openalex=f"W{i}") for i in range(2)]
    _install(monkeypatch, h.FakeChaseProvider("openalex", citations={h.W_INCLUDE: docs}))
    job, _ = _run(client, {"providers": ["openalex"], "directions": ["forward"]})
    assert job["state"] == "succeeded"

    real_move = rounds.shutil.move

    def failing(src, dst):
        raise OSError("locked")

    monkeypatch.setattr(rounds.shutil, "move", failing)
    failed = client.post(f"{BASE}/chase/accept", json={})
    assert failed.status_code == 409 and _code(failed) == "ARCHIVE_INCOMPLETE"
    monkeypatch.setattr(rounds.shutil, "move", real_move)

    refused = client.post(f"{BASE}/chase/runs", json={"providers": ["openalex"], "directions": ["forward"]})
    assert refused.status_code == 409 and _code(refused) == "CHASE_ACCEPT_PENDING"
    assert "chase_001" in refused.json()["detail"]["message"]
    assert client.get(f"{BASE}/chase").json()["active_job"] is None

    finished = client.post(f"{BASE}/chase/accept", json={})
    assert finished.status_code == 200 and finished.json()["round"] == 2
