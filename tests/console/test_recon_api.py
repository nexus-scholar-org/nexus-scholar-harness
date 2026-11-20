"""Recon over HTTP (M4c): probe and delta as jobs with SSE, distill, directions, bind.

Hermetic: the console's search seam (``app.state.recon_search_fn``) replaces the
providers; ``tests/pipeline/test_golden_recon_cassette.py`` replays the real
providers from a cassette. The recon cache is ``tmp_path``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import E2E_ANSWERS
from fastapi.testclient import TestClient
from scholar_search.config import settings
from scholar_search.models import Document, ExternalIds, Query, SearchLeg, SearchRun

from scholar_harness.console import create_app
from scholar_harness.inception.intent import CriterionDraft

TOKEN = "desk-token"
BASE = "/api/v1/inception"


def _doc(i: int, title: str, abstract: str) -> Document:
    return Document(
        title=title, year=2023, provider="openalex", provider_id=f"W{i:06d}",
        external_ids=ExternalIds(doi=f"10.1/w{i:03d}"), abstract=abstract, url=f"https://example.org/{i}",
    )


def _pool(n_a: int = 8, n_b: int = 6) -> list[Document]:
    docs = [_doc(i, f"Real-time weed detection on embedded hardware {i}", "an on-device inference pipeline for weed detection") for i in range(n_a)]
    docs += [_doc(100 + i, f"Lightweight cnn weed segmentation {i}", "lightweight cnn models for crop rows") for i in range(n_b)]
    return docs


class Seam:
    """A search seam whose answer the test can change between probes."""

    def __init__(self, docs: list[Document] | None = None, failed: list[str] = ()):
        self.docs = _pool() if docs is None else docs
        self.failed = list(failed)
        self.calls: list[str] = []
        self.queries: list[Query] = []
        self.providers: list[list[str]] = []

    def __call__(self, query: Query, providers: list[str]) -> SearchRun:
        self.calls.append(query.text)
        self.queries.append(query)
        self.providers.append(list(providers))
        legs = [
            SearchLeg(provider=p, query_id=query.id, status="failed" if p in self.failed else "ok",
                      error="ConnectError: offline" if p in self.failed else None)
            for p in providers
        ]
        return SearchRun(documents=list(self.docs), legs=legs)


def _draft() -> dict:
    a = E2E_ANSWERS
    proof_id = CriterionDraft("inclusion", f"Reports the gold-standard proof — {a[5]}", "proof").id
    return {
        "topic": a[0], "paradigm": a[1], "playbook": a[2], "unit_of_analysis": a[4], "proof": a[5],
        "out_of_scope": [s.strip() for s in a[6].split(",")], "rqs": [a[8]],
        "concepts": [{"concept": "weed detection"}, {"concept": "on-device inference"}],
        "criteria_decisions": {proof_id: True},
        "title": "On-Device Weed Detection for Embedded Agriculture", "lead_researcher": "Dr. Example",
    }


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.delenv("NEXUS_RECON_ROOT", raising=False)
    root = tmp_path / "root"
    root.mkdir()
    app = create_app(None, token=TOKEN, workspaces_root=root)
    app.state.recon_root = tmp_path / "recon"
    app.state.recon_search_fn = Seam()
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        yield client, app, root, tmp_path / "recon"


def _new_draft(client) -> str:
    created = client.post(f"{BASE}/drafts", json={"draft": _draft()})
    assert created.status_code == 201, created.text
    return created.json()["session_id"]


def _events(client, sid: str, job_id: str) -> list[tuple[str, dict]]:
    out = []
    with client.stream("GET", f"{BASE}/drafts/{sid}/recon/jobs/{job_id}/events") as stream:
        event = None
        for line in stream.iter_lines():
            if line.startswith("event: "):
                event = line[len("event: "):]
            elif line.startswith("data: "):
                out.append((event, json.loads(line[len("data: "):])))
    return out


def _probe(client, sid: str, **body) -> dict:
    started = client.post(f"{BASE}/drafts/{sid}/recon/probe", json=body)
    assert started.status_code == 202, started.text
    job = started.json()["job"]
    events = _events(client, sid, job["job_id"])
    assert events[0][0] == "snapshot" and events[-1][0] in ("done", "failed")
    return client.get(f"{BASE}/drafts/{sid}/recon/jobs/{job['job_id']}").json()["job"]


def test_a_probe_runs_as_a_streamed_job_and_binds_into_the_draft_with_evidence(env):
    client, _app, root, recon = env
    sid = _new_draft(client)
    state = client.get(f"{BASE}/drafts/{sid}/recon").json()
    assert (state["session"], state["grounding"], state["mailto_set"]) == (None, None, True)

    job = _probe(client, sid)
    assert job["state"] == "succeeded", job
    result = job["result"]
    assert result["status"] == "complete" and result["n_docs"] == 14
    assert result["fingerprint"].startswith("sha256:") and result["created_at"]
    assert len(result["legs"]) == 4

    explore = client.post(f"{BASE}/drafts/{sid}/recon/distill")
    assert explore.status_code == 200, explore.text
    body = explore.json()
    assert body["pool"]["fingerprint"] == result["fingerprint"]
    assert body["gates"]["pool"]["sufficient"] is True
    assert {"label", "n", "anchor_dois"} <= set(body["schools"][0]) if body["schools"] else True
    assert body["papers"][0]["directions_anchored"] >= 1

    found = client.get(f"{BASE}/drafts/{sid}/recon/directions").json()
    labels = [d["label"] for d in found["directions"]]
    assert labels and found["narrower_left"] == 1
    for d in found["directions"]:
        assert len(d["anchor_dois"]) >= 2 and d["observed_in"] == len(d["anchor_dois"])

    record = client.get(f"{BASE}/drafts/{sid}").json()
    bound = client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"direction": labels[0], "base_updated_at": record["updated_at"]})
    assert bound.status_code == 200, bound.text
    grounding = bound.json()["grounding"]
    assert grounding["pool"]["fingerprint"] == result["fingerprint"]
    assert grounding["pool"]["created_at"] == result["created_at"]
    assert grounding["direction"]["label"] == labels[0] and grounding["anchors"]
    # A save of the draft keeps the grounding (only the bind route writes it).
    saved = client.put(f"{BASE}/drafts/{sid}", json={"draft": _draft(), "base_updated_at": bound.json()["updated_at"]})
    assert saved.json()["grounding"] == grounding

    preview = client.post(f"{BASE}/preview", json={"draft": _draft(), "session_id": sid})
    assert preview.status_code == 200, preview.text
    g = preview.json()["grounding"]
    assert g["pool"]["fingerprint"] == result["fingerprint"]
    assert g["rq_evidence"][0]["anchor_dois"], "the RQ names 'weed detection', observed in the pool"
    assert g["concept_evidence"]["weed detection"]["observed_in"] == 8
    assert "audit/recon_context.json" in preview.json()["files"]

    made = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert made.status_code == 201, made.text
    ctx = json.loads((root / made.json()["slug"] / "audit" / "recon_context.json").read_text(encoding="utf-8"))
    assert ctx["session_id"] == sid and ctx["pool_fingerprints"] == [result["fingerprint"]]
    assert ctx["pool_created_at"] == [result["created_at"]]
    assert ctx["direction"] == labels[0] and ctx["rq_evidence"][0]["anchor_dois"]
    journal = (root / made.json()["slug"] / "audit" / "journal.jsonl").read_text(encoding="utf-8")
    assert "pool_created_at" in journal


def test_a_draft_shaped_on_an_older_pool_is_refused_as_stale(env):
    client, app, _root, _recon = env
    sid = _new_draft(client)
    _probe(client, sid)
    label = client.get(f"{BASE}/drafts/{sid}/recon/directions").json()["directions"][0]["label"]
    assert client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"direction": label}).status_code == 200

    app.state.recon_search_fn.docs = _pool(n_a=9, n_b=7)  # the literature answers differently now
    refreshed = _probe(client, sid, refresh=True)
    assert refreshed["result"]["served_from_cache"] is False

    state = client.get(f"{BASE}/drafts/{sid}/recon").json()
    assert state["binding"]["stale"] is True
    for call in (
        lambda: client.post(f"{BASE}/preview", json={"draft": _draft(), "session_id": sid}),
        lambda: client.post(f"{BASE}/drafts/{sid}/genesis", json={}),
    ):
        refused = call()
        assert (refused.status_code, refused.json()["detail"]["code"]) == (409, "STALE_BINDING")
        assert "choose the direction again" in refused.json()["detail"]["message"].lower()
    # Binding again on the current pool clears it.
    label = client.get(f"{BASE}/drafts/{sid}/recon/directions").json()["directions"][0]["label"]
    client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"direction": label})
    assert client.post(f"{BASE}/drafts/{sid}/genesis", json={}).status_code == 201


def test_without_a_contact_address_a_probe_is_refused_before_any_request(env, monkeypatch):
    client, app, _root, recon = env
    app.state.recon_search_fn = None
    monkeypatch.setattr(settings, "mailto", None)
    sid = _new_draft(client)
    assert client.get(f"{BASE}/drafts/{sid}/recon").json()["mailto_set"] is False
    for route in ("probe", "delta"):
        refused = client.post(f"{BASE}/drafts/{sid}/recon/{route}", json={})
        assert (refused.status_code, refused.json()["detail"]["code"]) == (409, "MAILTO_NOT_SET"), route
        assert "SCHOLAR_MAILTO" in refused.json()["detail"]["message"]
    assert not recon.exists()


def test_failed_providers_fail_the_job_per_leg_and_nothing_is_cached(env):
    client, app, _root, recon = env
    app.state.recon_search_fn = Seam(docs=[], failed=["openalex", "semanticscholar", "crossref", "arxiv"])
    sid = _new_draft(client)
    job = _probe(client, sid)
    assert job["state"] == "failed"
    assert job["error"]["code"] == "PROVIDERS_FAILED"
    assert {leg["provider"] for leg in job["error"]["details"]["legs"]} == {"openalex", "semanticscholar", "crossref", "arxiv"}
    assert not list((recon / "pools").glob("*_pool.json")), "an empty pool is never cached"
    assert client.post(f"{BASE}/drafts/{sid}/recon/distill").json()["detail"]["code"] == "RECON_NO_POOL"


def test_a_partial_probe_succeeds_and_names_the_failed_leg(env):
    client, app, _root, recon = env
    app.state.recon_search_fn = Seam(failed=["crossref"])
    sid = _new_draft(client)
    job = _probe(client, sid)
    assert job["state"] == "succeeded" and job["result"]["status"] == "partial"
    assert [leg["provider"] for leg in job["result"]["legs"] if leg["status"] == "failed"] == ["crossref"]
    assert not list((recon / "pools").glob("*_pool.json"))


def test_a_thin_pool_needs_the_researchers_consent_to_bind(env):
    client, app, _root, _recon = env
    app.state.recon_search_fn = Seam(docs=_pool(n_a=4, n_b=3))
    sid = _new_draft(client)
    _probe(client, sid)
    label = client.get(f"{BASE}/drafts/{sid}/recon/directions").json()["directions"][0]["label"]
    refused = client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"direction": label})
    assert (refused.status_code, refused.json()["detail"]["code"]) == (409, "POOL_TOO_SMALL")
    assert refused.json()["detail"]["details"] == {"n_docs": 7, "floor": 12}
    ok = client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"direction": label, "accept_thin_pool": True})
    assert ok.status_code == 200


def test_one_narrower_search_on_a_known_direction(env):
    client, app, _root, _recon = env
    sid = _new_draft(client)
    _probe(client, sid)
    unknown = client.post(f"{BASE}/drafts/{sid}/recon/probe", json={"narrower": "not a direction"})
    assert (unknown.status_code, unknown.json()["detail"]["code"]) == (422, "DIRECTION_UNKNOWN")
    label = client.get(f"{BASE}/drafts/{sid}/recon/directions").json()["directions"][0]["label"]
    job = _probe(client, sid, narrower=label)
    assert job["state"] == "succeeded" and app.state.recon_search_fn.calls[-1] == label
    again = client.post(f"{BASE}/drafts/{sid}/recon/probe", json={"narrower": label})
    assert again.json()["detail"]["code"] == "NARROW_BUDGET_SPENT"


def test_the_gap_check_runs_as_a_job(env):
    client, _app, _root, _recon = env
    sid = _new_draft(client)
    _probe(client, sid)
    started = client.post(f"{BASE}/drafts/{sid}/recon/delta", json={"followups": 3})
    assert started.status_code == 202
    job_id = started.json()["job"]["job_id"]
    _events(client, sid, job_id)
    job = client.get(f"{BASE}/drafts/{sid}/recon/jobs/{job_id}").json()["job"]
    assert job["state"] == "succeeded", job
    assert job["result"]["pool_size_before"] == 14 and "followups" in job["result"]
    too_many = client.post(f"{BASE}/drafts/{sid}/recon/delta", json={"followups": 4})
    assert too_many.status_code == 422


def test_your_own_direction_is_recorded_as_ungrounded_until_it_occurs(env):
    client, _app, _root, _recon = env
    sid = _new_draft(client)
    _probe(client, sid)
    own = client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"own": "quantum error correction"}).json()["grounding"]
    assert own["direction"]["source"] == "researcher" and own["direction"]["grounded"] is False
    assert own["direction"]["observed_in"] == 0
    found = client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"own": "weed detection"}).json()["grounding"]
    assert found["direction"]["grounded"] is True and found["direction"]["observed_in"] == 8
    both = client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"own": "x", "direction": "y"})
    assert both.json()["detail"]["code"] == "NO_DIRECTION"


def test_recon_refusals_name_the_draft_and_the_job(env):
    client, _app, _root, _recon = env
    assert client.get(f"{BASE}/drafts/rec_0123456789abcdef/recon").json()["detail"]["code"] == "DRAFT_NOT_FOUND"
    sid = _new_draft(client)
    assert client.get(f"{BASE}/drafts/{sid}/recon/directions").json()["detail"]["code"] == "RECON_SESSION_NOT_FOUND"
    assert client.get(f"{BASE}/drafts/{sid}/recon/jobs/rjob_x").json()["detail"]["code"] == "RECON_JOB_NOT_FOUND"
    blank = client.post(f"{BASE}/drafts", json={"draft": {}}).json()["session_id"]
    assert client.post(f"{BASE}/drafts/{blank}/recon/probe", json={}).json()["detail"]["code"] == "DRAFT_INCOMPLETE"


def test_a_draft_without_recon_previews_and_emits_as_before(env):
    client, _app, root, _recon = env
    sid = _new_draft(client)
    preview = client.post(f"{BASE}/preview", json={"draft": _draft(), "session_id": sid}).json()
    assert "grounding" not in preview and "audit/recon_context.json" not in preview["files"]
    made = client.post(f"{BASE}/drafts/{sid}/genesis", json={}).json()
    assert not (Path(made["path"]) / "audit" / "recon_context.json").exists()


def test_a_client_cannot_forge_or_smuggle_grounding(env):
    """Review #7: only the bind route writes grounding; a save cannot add one."""
    client, _app, root, _recon = env
    sid = _new_draft(client)
    forged = {"session_id": sid, "pool": {"fingerprint": "sha256:forged"}, "direction": {"label": "x"}}
    top = client.put(f"{BASE}/drafts/{sid}", json={"draft": _draft(), "grounding": forged})
    assert top.status_code == 422
    inside = client.put(f"{BASE}/drafts/{sid}", json={"draft": {**_draft(), "grounding": forged}})
    assert (inside.status_code, inside.json()["detail"]["code"]) == (422, "DRAFT_INVALID")
    assert "grounding" not in client.get(f"{BASE}/drafts/{sid}").json()
    made = client.post(f"{BASE}/drafts/{sid}/genesis", json={}).json()
    assert not (Path(made["path"]) / "audit" / "recon_context.json").exists()


def test_finished_jobs_are_kept_only_up_to_a_limit(env):
    """Review #5: a long-running console does not keep every finished job."""
    from scholar_harness.console.api import recon as recon_api

    client, app, _root, _recon = env
    sid = _new_draft(client)
    ids = [_probe(client, sid, refresh=True)["job_id"] for _ in range(recon_api.KEEP_FINISHED + 2)]
    kept = [j for j in app.state.recon_jobs.jobs.values() if j.session_id == sid]
    assert len(kept) == recon_api.KEEP_FINISHED + 1  # the limit, plus the newest
    assert client.get(f"{BASE}/drafts/{sid}/recon/jobs/{ids[0]}").json()["detail"]["code"] == "RECON_JOB_NOT_FOUND"
    assert client.get(f"{BASE}/drafts/{sid}/recon/jobs/{ids[-1]}").status_code == 200


def test_a_question_changed_after_the_search_is_flagged(env):
    """Review #8: the session searched an older question."""
    client, _app, _root, _recon = env
    sid = _new_draft(client)
    _probe(client, sid)
    assert client.get(f"{BASE}/drafts/{sid}/recon").json()["topic_changed"] is False
    record = client.get(f"{BASE}/drafts/{sid}").json()
    client.put(f"{BASE}/drafts/{sid}", json={"draft": {**_draft(), "topic": "soil salinity"}, "base_updated_at": record["updated_at"]})
    assert client.get(f"{BASE}/drafts/{sid}/recon").json()["topic_changed"] is True


def test_the_recon_state_reports_the_database_keys_and_each_legs_code_and_notes(env, monkeypatch):
    """M4d DoD 1: Explore reads key state and leg codes from the engine, as the Plan screen does."""
    client, app, _root, _recon = env
    monkeypatch.setattr(settings, "openalex_key", None)
    monkeypatch.setattr(settings, "s2_key", "s2-placeholder")
    seam = Seam()

    def answer(query, providers):
        run = seam(query, providers)
        for leg in run.legs:
            if leg.provider == "semanticscholar":
                leg.status, leg.error_code = "failed", "PROVIDER_REFUSED"
                leg.notes.append("Semantic Scholar rejected SCHOLAR_S2_KEY (HTTP 403)")
        return run

    app.state.recon_search_fn = answer
    sid = _new_draft(client)
    _probe(client, sid)
    state = client.get(f"{BASE}/drafts/{sid}/recon").json()
    assert state["keys"] == {"openalex_key_set": False, "s2_key_set": True}
    legs = {leg["provider"]: leg for leg in state["session"]["latest"]["legs"]}
    assert legs["semanticscholar"]["error_code"] == "PROVIDER_REFUSED"
    assert legs["semanticscholar"]["notes"] == ["Semantic Scholar rejected SCHOLAR_S2_KEY (HTTP 403)"]
    assert (legs["openalex"]["key_set"], legs["semanticscholar"]["key_set"], legs["crossref"]["key_set"]) == (False, True, None)
    assert "s2-placeholder" not in json.dumps(state)


def _save(client, sid: str, **changes) -> None:
    record = client.get(f"{BASE}/drafts/{sid}").json()
    saved = client.put(f"{BASE}/drafts/{sid}", json={"draft": {**record["draft"], **changes}, "base_updated_at": record["updated_at"]})
    assert saved.status_code == 200, saved.text


def test_the_probe_sends_the_drafts_years_and_languages_and_the_pool_keeps_them(env):
    """M4d DoD 2: the pool is searched for the review's years and languages, and says so."""
    client, app, _root, _recon = env
    sid = _new_draft(client)
    _save(client, sid, start_year=2018, end_year=2024, languages=["en", "fr"])
    job = _probe(client, sid)
    query = app.state.recon_search_fn.queries[-1]
    assert (query.year_min, query.year_max, query.language) == (2018, 2024, "en,fr")
    assert job["result"]["languages"] == ["en", "fr"]
    assert (job["result"]["year_min"], job["result"]["year_max"]) == (2018, 2024)
    pool = client.post(f"{BASE}/drafts/{sid}/recon/distill").json()["pool"]
    assert pool["languages"] == ["en", "fr"]


def test_other_languages_are_a_different_pool(env):
    client, app, _root, _recon = env
    sid = _new_draft(client)
    first = _probe(client, sid)
    _save(client, sid, languages=["fr"])
    second = _probe(client, sid)
    assert second["result"]["served_from_cache"] is False
    assert first["result"]["cache_key"] != second["result"]["cache_key"]


def test_a_changed_scope_is_reported_and_makes_the_bound_direction_stale(env):
    """M4d (spec 02 Q3, 03 Q3): the engine compares the saved scope with the pool, not the browser."""
    client, _app, _root, _recon = env
    sid = _new_draft(client)
    _probe(client, sid)
    label = client.get(f"{BASE}/drafts/{sid}/recon/directions").json()["directions"][0]["label"]
    assert client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"direction": label}).status_code == 200
    state = client.get(f"{BASE}/drafts/{sid}/recon").json()
    assert (state["scope_changed"], state["scope_changes"], state["binding"]["stale"]) == (False, [], False)

    _save(client, sid, languages=["en", "ar"], end_year=2025)
    state = client.get(f"{BASE}/drafts/{sid}/recon").json()
    assert state["scope_changed"] is True
    assert state["scope_changes"] == ["years", "languages"]
    assert state["binding"]["stale"] is True and state["binding"]["code"] == "SCOPE_CHANGED"
    draft = client.get(f"{BASE}/drafts/{sid}").json()["draft"]
    preview = client.post(f"{BASE}/preview", json={"draft": draft, "session_id": sid})
    assert preview.json()["detail"]["code"] == "STALE_BINDING", preview.text
    assert client.post(f"{BASE}/drafts/{sid}/genesis", json={}).json()["detail"]["code"] == "STALE_BINDING"


# --------------------------------------------------------------------------- M4d DoD 3-5


def test_each_concept_says_how_many_pool_papers_anchor_it_and_offers_pool_terms(env):
    """M4d DoD 3 and 4: per-concept anchoring and co-occurring pool terms, no language model."""
    client, _app, _root, _recon = env
    sid = _new_draft(client)
    assert client.get(f"{BASE}/drafts/{sid}/recon/concepts").json()["detail"]["code"] == "RECON_SESSION_NOT_FOUND"
    _probe(client, sid)
    _save(client, sid, concepts=[{"concept": "weed detection", "synonyms": ["weed segmentation"]}, {"concept": "on-device inference"}])
    body = client.get(f"{BASE}/drafts/{sid}/recon/concepts").json()
    assert body["n_docs"] == 14 and body["fingerprint"].startswith("sha256:")
    weed, device = body["concepts"]
    assert (weed["concept"], weed["source"]) == ("weed detection", "draft")
    assert [(t["term"], t["observed_in"]) for t in weed["terms"]] == [("weed detection", 8), ("weed segmentation", 6)]
    assert weed["anchored_in"] == 14
    assert device["anchored_in"] == 8
    for concept in body["concepts"]:
        counts = [s["observed_in"] for s in concept["suggestions"]]
        assert counts == sorted(counts, reverse=True) and all(n >= 2 for n in counts)
        assert len(concept["suggestions"]) <= 10
        for s in concept["suggestions"]:
            # Never a term a concept already has, nor a piece or an extension of one.
            for t in ("weed detection", "weed segmentation", "on-device inference"):
                assert t.replace("-", " ") not in s["term"].replace("-", " ")
                assert s["term"].replace("-", " ") not in t.replace("-", " ")
    assert "embedded hardware" in [s["term"] for s in device["suggestions"]]


def test_a_draft_without_concepts_gets_the_scope_steps_suggested_concepts(env):
    client, _app, _root, _recon = env
    sid = _new_draft(client)
    _save(client, sid, concepts=[])
    _probe(client, sid)
    concepts = client.get(f"{BASE}/drafts/{sid}/recon/concepts").json()["concepts"]
    assert concepts and {c["source"] for c in concepts} == {"suggested"}


def test_your_own_phrase_can_be_checked_without_binding(env):
    """Spec 03 Q4 (M4d): a read-only check before an own direction is bound."""
    client, _app, _root, _recon = env
    sid = _new_draft(client)
    _probe(client, sid)
    before = client.get(f"{BASE}/drafts/{sid}").json()
    ev = client.get(f"{BASE}/drafts/{sid}/recon/evidence", params={"term": "Weed-Detection"}).json()
    assert (ev["term"], ev["observed_in"], ev["n_docs"], len(ev["anchor_dois"])) == ("Weed-Detection", 8, 14, 8)
    assert client.get(f"{BASE}/drafts/{sid}").json() == before
    blank = client.get(f"{BASE}/drafts/{sid}/recon/evidence", params={"term": "  "})
    assert blank.status_code == 422


def test_going_on_without_a_direction_is_recorded_as_not_grounded(env):
    """Spec 03 Q1 (M4d): the skip is an explicit choice that Review and intent.json can show."""
    client, _app, root, _recon = env
    sid = _new_draft(client)
    _probe(client, sid)
    both = client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"skip": True, "direction": "x"})
    assert both.status_code == 422 and both.json()["detail"]["code"] == "NO_DIRECTION"
    bound = client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"skip": True})
    assert bound.status_code == 200, bound.text
    g = bound.json()["grounding"]
    assert (g["direction"]["source"], g["direction"]["grounded"], g["choice"]) == ("none", False, "none")
    assert g["anchors"] == []
    made = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert made.status_code == 201, made.text
    ctx = json.loads((root / made.json()["slug"] / "audit" / "recon_context.json").read_text(encoding="utf-8"))
    assert (ctx["direction_source"], ctx["direction_grounded"]) == ("none", False)


def test_the_anchored_papers_are_offered_as_seeds_and_kept_ones_reach_the_protocol(env):
    """M4d DoD 5: seeds come from the pool's anchors and are written before genesis."""
    client, _app, root, _recon = env
    sid = _new_draft(client)
    _probe(client, sid)
    seeds = client.get(f"{BASE}/drafts/{sid}/recon/seeds").json()
    papers = seeds["papers"]
    assert papers and all(p["doi"] for p in papers)
    assert all(p["anchors"]["directions"] or p["anchors"]["concepts"] for p in papers)
    n = [len(p["anchors"]["directions"]) + len(p["anchors"]["concepts"]) for p in papers]
    assert n == sorted(n, reverse=True)

    kept = [papers[0]["doi"], papers[1]["doi"]]
    _save(client, sid, golden_seeds=kept)
    draft = client.get(f"{BASE}/drafts/{sid}").json()["draft"]
    preview = client.post(f"{BASE}/preview", json={"draft": draft})
    assert preview.json()["protocol"]["search_strategy"]["golden_seeds"] == kept
    made = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert made.status_code == 201, made.text
    protocol = json.loads((root / made.json()["slug"] / "protocol.json").read_text(encoding="utf-8"))
    assert protocol["search_strategy"]["golden_seeds"] == kept


def test_seeds_must_be_dois_and_at_most_25(env):
    client, _app, _root, _recon = env
    sid = _new_draft(client)
    record = client.get(f"{BASE}/drafts/{sid}").json()
    # A malformed seed is a shape error; 26 seeds is a size limit (H-input-limits, F6).
    for bad, code in ((["not a doi"], "DRAFT_INVALID"), ([f"10.1/x{i}" for i in range(26)], "DRAFT_TOO_LARGE")):
        draft = {**record["draft"], "golden_seeds": bad}
        refused = client.post(f"{BASE}/preview", json={"draft": draft})
        assert refused.status_code == 422 and refused.json()["detail"]["code"] == code, refused.text


def test_a_binding_made_before_m4d_is_not_stale_for_its_scope(env):
    """Review #7: a grounding without a recorded scope is compared on its pool only."""
    from scholar_harness.inception.drafts import DraftStore

    client, _app, root, _recon = env
    sid = _new_draft(client)
    _probe(client, sid)
    label = client.get(f"{BASE}/drafts/{sid}/recon/directions").json()["directions"][0]["label"]
    client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"direction": label})
    drafts = DraftStore(root)
    grounding = drafts.load(sid)["grounding"]
    grounding.pop("scope")  # as M4c wrote it
    drafts.bind_grounding(sid, grounding)
    _save(client, sid, languages=["fr"], start_year=2019)
    assert client.get(f"{BASE}/drafts/{sid}/recon").json()["binding"]["stale"] is False


def test_a_draft_with_no_from_year_matches_a_pool_searched_from_2000(env):
    """Review #7: the probe's default from-year is the scope's default, so nothing goes stale."""
    client, _app, _root, _recon = env
    sid = _new_draft(client)
    _save(client, sid, start_year=None)
    _probe(client, sid)
    label = client.get(f"{BASE}/drafts/{sid}/recon/directions").json()["directions"][0]["label"]
    client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"direction": label})
    state = client.get(f"{BASE}/drafts/{sid}/recon").json()
    assert (state["scope_changed"], state["binding"]["stale"]) == (False, False)


# --------------------------------------------------------------------------- M10a OBS-1

SENTENCE = (
    "How does on-device inference of lightweight CNN models affect real-time "
    "weed detection accuracy in crop rows under field conditions?"
)
KEYWORDS = "on-device inference lightweight CNN models real-time"


def test_a_sentence_topic_is_probed_as_keywords(env):
    """OBS-1: a topic sentence is probed as its keyword query; the draft keeps the sentence."""
    from scholar_search.providers.openalex import OpenAlexProvider
    from scholar_search.providers.semanticscholar import SemanticScholarProvider

    client, app, _root, _recon = env
    seam = Seam()

    def answer(query, providers):
        run = seam(query, providers)
        for leg in run.legs:
            leg.executed_query = query.text
        return run

    app.state.recon_search_fn = answer
    sid = _new_draft(client)
    _save(client, sid, topic=SENTENCE)
    job = _probe(client, sid)
    assert job["state"] == "succeeded", job
    assert seam.calls == [KEYWORDS]
    assert job["result"]["query"] == KEYWORDS

    # What the keyword query becomes at the two databases that require every word.
    _text, params, _notes = OpenAlexProvider().translate(Query(text=KEYWORDS))
    assert params["search"] == KEYWORDS and "search.title_and_abstract" not in params
    s2_text, _params, _notes = SemanticScholarProvider().translate(Query(text=KEYWORDS))
    assert s2_text.split() == KEYWORDS.split()
    assert not {"+", "|", "AND", "OR", "NOT"} & set(s2_text.split())

    state = client.get(f"{BASE}/drafts/{sid}/recon").json()
    assert state["session"]["topic"] == SENTENCE and state["topic_changed"] is False
    assert state["session"]["latest"]["query"] == KEYWORDS
    assert {leg["executed_query"] for leg in state["session"]["latest"]["legs"]} == {KEYWORDS}
    assert client.get(f"{BASE}/drafts/{sid}").json()["draft"]["topic"] == SENTENCE


def test_a_semantic_probe_sends_the_keyword_query_to_every_database(env):
    """Review item 5: OpenAlex search.semantic is one of four databases; all four get the keywords."""
    client, app, _root, _recon = env
    sid = _new_draft(client)
    _save(client, sid, topic=SENTENCE)
    job = _probe(client, sid, semantic=True)
    assert job["state"] == "succeeded", job
    seam = app.state.recon_search_fn
    query = seam.queries[-1]
    assert (query.text, query.semantic) == (KEYWORDS, True)
    assert seam.providers[-1] == ["openalex", "semanticscholar", "crossref", "arxiv"]
    assert job["result"]["query"] == KEYWORDS

    # Review round 2, item 6: what the recorded semantic Query becomes at OpenAlex and S2.
    from scholar_search.providers.openalex import OpenAlexProvider
    from scholar_search.providers.semanticscholar import SemanticScholarProvider

    _text, params, _notes = OpenAlexProvider().translate(query)
    assert params["search.semantic"] == KEYWORDS and "search" not in params
    s2_text, _params, _notes = SemanticScholarProvider().translate(query)
    assert s2_text.split() == KEYWORDS.split()


def test_a_narrower_search_is_never_keyworded(env, monkeypatch):
    """Review item 7: only the topic is turned into keywords; a direction label is sent as it is."""
    from scholar_harness.console.api import recon as recon_api

    converted: list[str] = []

    def spy(text: str) -> str:
        converted.append(text)
        return "kw " + text

    monkeypatch.setattr(recon_api, "keyword_query", spy)
    client, app, _root, _recon = env
    sid = _new_draft(client)
    _probe(client, sid)
    seam = app.state.recon_search_fn
    assert converted == [_draft()["topic"]] and seam.calls == ["kw " + _draft()["topic"]]

    label = "weed detection in the field using lightweight models"  # stopwords and framing words
    monkeypatch.setattr(
        recon_api.ReconSessions, "directions", lambda self, sid, **_kw: {"directions": [{"label": label}]}
    )
    job = _probe(client, sid, narrower=label)
    assert job["state"] == "succeeded", job
    assert seam.calls[-1] == label and job["result"]["query"] == label
    assert job["result"]["purpose"] == "narrower"
    assert converted == [_draft()["topic"]], "only the first search was keyworded"


def test_the_gap_check_sends_its_term_as_written_to_the_pools_databases(env, monkeypatch):
    """Review round 2, item 1: follow-ups ask the researcher's databases, and the record says so."""
    from scholar_harness.console.api import recon as recon_api
    from scholar_harness.recon import adaptive

    converted: list[str] = []
    monkeypatch.setattr(recon_api, "keyword_query", lambda text: converted.append(text) or text)
    term = "weed detection in the field"  # a stopword: keywording would drop "in the"
    monkeypatch.setattr(
        adaptive, "plan_followups",
        lambda distilled, pool: [{"term": term, "reason": "thin school", "school_n": 1}],
    )
    client, app, _root, _recon = env
    chosen = ["crossref", "openalex"]
    sid = _new_draft(client)
    probe = _probe(client, sid, databases=chosen)
    assert probe["state"] == "succeeded", probe
    seam = app.state.recon_search_fn
    before = len(seam.calls)
    converted.clear()

    started = client.post(f"{BASE}/drafts/{sid}/recon/delta", json={"followups": 3})
    assert started.status_code == 202, started.text
    job_id = started.json()["job"]["job_id"]
    _events(client, sid, job_id)
    job = client.get(f"{BASE}/drafts/{sid}/recon/jobs/{job_id}").json()["job"]
    assert job["state"] == "succeeded", job
    assert seam.calls[before:] == [term]
    assert seam.providers[before:] == [chosen]
    assert converted == []

    record = client.get(f"{BASE}/drafts/{sid}/recon").json()["session"]["latest"]
    assert record["purpose"] == "delta" and record["providers"] == chosen
    new_legs = record["legs"][len(probe["result"]["legs"]):]
    assert [leg["provider"] for leg in new_legs] == chosen
    pool = client.post(f"{BASE}/drafts/{sid}/recon/distill").json()["pool"]
    assert pool["providers"] == chosen


def test_a_probe_recorded_before_m10a_reads_back_with_null_query_and_providers(env):
    """Review item 9: the API never omits ``executed_query`` or ``providers`` for an older probe."""
    client, _app, _root, recon = env
    sid = _new_draft(client)
    _probe(client, sid)
    path = recon / "sessions" / sid / "session.json"
    session = json.loads(path.read_text(encoding="utf-8"))
    for probe in session["probes"]:
        probe.pop("providers", None)
        for leg in probe["legs"]:
            leg.pop("executed_query", None)
    path.write_text(json.dumps(session), encoding="utf-8")

    state = client.get(f"{BASE}/drafts/{sid}/recon").json()["session"]
    for probe in [state["latest"], *state["probes"]]:
        assert probe["providers"] is None
        assert probe["legs"] and all(leg["executed_query"] is None for leg in probe["legs"])


# --------------------------------------------------------------------------- M10a decision 1a

FOUR = ["openalex", "semanticscholar", "crossref", "arxiv"]


def test_the_recon_state_offers_the_derived_query_and_the_databases(env):
    client, _app, _root, _recon = env
    sid = _new_draft(client)
    _save(client, sid, topic=SENTENCE)
    state = client.get(f"{BASE}/drafts/{sid}/recon").json()
    assert state["derived_query"] == KEYWORDS
    assert state["databases_available"] == FOUR
    blank = client.post(f"{BASE}/drafts", json={"draft": {}}).json()["session_id"]
    assert client.get(f"{BASE}/drafts/{blank}/recon").json()["derived_query"] is None


def test_the_chosen_databases_and_the_edited_query_are_sent_as_given(env):
    """Decision 1a: the Seam gets the researcher's order and query; the topic sentence stays."""
    client, app, _root, _recon = env
    sid = _new_draft(client)
    _save(client, sid, topic=SENTENCE)
    chosen = ["arxiv", "openalex", "crossref"]
    edited = "lightweight CNN weed detection AND crop rows"
    job = _probe(client, sid, databases=chosen, query=f"  {edited}  ")
    assert job["state"] == "succeeded", job
    seam = app.state.recon_search_fn
    assert (seam.calls[-1], seam.providers[-1]) == (edited, chosen)
    assert (job["result"]["query"], job["result"]["providers"]) == (edited, chosen)
    assert [leg["provider"] for leg in job["result"]["legs"]] == chosen

    state = client.get(f"{BASE}/drafts/{sid}/recon").json()
    assert (state["session"]["latest"]["query"], state["session"]["latest"]["providers"]) == (edited, chosen)
    assert state["session"]["topic"] == SENTENCE and state["topic_changed"] is False
    assert state["derived_query"] == KEYWORDS
    assert client.get(f"{BASE}/drafts/{sid}").json()["draft"]["topic"] == SENTENCE
    pool = client.post(f"{BASE}/drafts/{sid}/recon/distill").json()["pool"]
    assert (pool["query"], pool["providers"]) == (edited, chosen)


def test_without_a_choice_the_four_databases_are_asked_in_default_order(env):
    client, app, _root, _recon = env
    sid = _new_draft(client)
    job = _probe(client, sid)
    assert app.state.recon_search_fn.providers[-1] == FOUR
    assert job["result"]["providers"] == FOUR


def test_a_narrower_search_asks_the_pools_databases(env):
    client, app, _root, _recon = env
    sid = _new_draft(client)
    _probe(client, sid, databases=["crossref", "openalex"])
    label = client.get(f"{BASE}/drafts/{sid}/recon/directions").json()["directions"][0]["label"]
    job = _probe(client, sid, narrower=label)
    assert job["state"] == "succeeded", job
    assert app.state.recon_search_fn.providers[-1] == ["crossref", "openalex"]
    assert job["result"]["providers"] == ["crossref", "openalex"]


def _usable_then_empty_arxiv(client, app) -> str:
    """A usable probe on [openalex, crossref], then an arXiv-only probe that finds nothing."""
    sid = _new_draft(client)
    assert _probe(client, sid, databases=["openalex", "crossref"])["state"] == "succeeded"
    seam = app.state.recon_search_fn
    kept = seam.docs
    seam.docs = []
    empty = _probe(client, sid, databases=["arxiv"], query="no such topic")
    assert empty["state"] == "failed" and empty["error"]["code"] == "POOL_EMPTY", empty
    seam.docs = kept
    state = client.get(f"{BASE}/drafts/{sid}/recon").json()["session"]
    assert state["latest"]["providers"] == ["arxiv"], "the empty probe is recorded"
    return sid


def test_the_gap_check_asks_the_databases_of_the_pool_it_extends(env, monkeypatch):
    """Orchestrator decision: not the databases of a later empty probe, which left the pool as it was."""
    from scholar_harness.recon import adaptive

    term = "weed detection in the field"
    monkeypatch.setattr(
        adaptive, "plan_followups",
        lambda distilled, pool: [{"term": term, "reason": "thin school", "school_n": 1}],
    )
    client, app, _root, _recon = env
    sid = _usable_then_empty_arxiv(client, app)
    seam = app.state.recon_search_fn
    before = len(seam.calls)

    started = client.post(f"{BASE}/drafts/{sid}/recon/delta", json={"followups": 3})
    assert started.status_code == 202, started.text
    job_id = started.json()["job"]["job_id"]
    _events(client, sid, job_id)
    job = client.get(f"{BASE}/drafts/{sid}/recon/jobs/{job_id}").json()["job"]
    assert job["state"] == "succeeded", job
    assert seam.calls[before:] == [term]
    assert seam.providers[before:] == [["openalex", "crossref"]]
    record = client.get(f"{BASE}/drafts/{sid}/recon").json()["session"]["latest"]
    assert record["purpose"] == "delta" and record["providers"] == ["openalex", "crossref"]
    pool = client.post(f"{BASE}/drafts/{sid}/recon/distill").json()["pool"]
    assert pool["providers"] == ["openalex", "crossref"]


def test_a_narrower_search_asks_the_databases_of_the_pool_it_narrows(env):
    client, app, _root, _recon = env
    sid = _usable_then_empty_arxiv(client, app)
    label = client.get(f"{BASE}/drafts/{sid}/recon/directions").json()["directions"][0]["label"]
    job = _probe(client, sid, narrower=label)
    assert job["state"] == "succeeded", job
    assert app.state.recon_search_fn.providers[-1] == ["openalex", "crossref"]
    assert job["result"]["providers"] == ["openalex", "crossref"]


@pytest.mark.parametrize(
    ("databases", "unknown", "repeated"),
    [
        ([], [], []),
        (["openalex", "pubmed"], ["pubmed"], []),
        (["openalex", "OpenAlex"], ["OpenAlex"], []),
        (["crossref", "openalex", "crossref"], [], ["crossref"]),
    ],
    ids=["empty", "unknown", "not-an-id", "duplicate"],
)
def test_a_wrong_database_list_is_refused_before_any_request(env, databases, unknown, repeated):
    client, app, _root, recon = env
    sid = _new_draft(client)
    refused = client.post(f"{BASE}/drafts/{sid}/recon/probe", json={"databases": databases})
    assert (refused.status_code, refused.json()["detail"]["code"]) == (422, "PROVIDER_UNKNOWN"), refused.text
    details = refused.json()["detail"]["details"]
    assert (details["known"], details["unknown"], details["repeated"]) == (FOUR, unknown, repeated)
    assert app.state.recon_search_fn.calls == [] and not recon.exists()


@pytest.mark.parametrize(
    "body",
    [
        {"query": ""},
        {"query": "   "},
        {"query": "x" * 2001},
        {"query": 7},
        {"databases": "openalex"},
        {"narrower": "weed detection", "query": "weed detection"},
        {"narrower": "weed detection", "databases": ["openalex"]},
    ],
    ids=["empty", "blank", "too-long", "not-text", "not-a-list", "narrower-and-query", "narrower-and-databases"],
)
def test_a_malformed_probe_body_is_body_invalid(env, body):
    client, app, _root, _recon = env
    sid = _new_draft(client)
    refused = client.post(f"{BASE}/drafts/{sid}/recon/probe", json=body)
    assert (refused.status_code, refused.json()["detail"]["code"]) == (422, "BODY_INVALID"), refused.text
    assert app.state.recon_search_fn.calls == []


def test_a_query_of_2000_characters_is_accepted(env):
    client, app, _root, _recon = env
    sid = _new_draft(client)
    job = _probe(client, sid, query="w" * 2000)
    assert job["state"] == "succeeded" and app.state.recon_search_fn.calls == ["w" * 2000]


def test_another_database_order_is_a_new_pool_and_makes_the_bound_direction_stale(env):
    client, _app, _root, _recon = env
    sid = _new_draft(client)
    first = _probe(client, sid, databases=["openalex", "crossref"])
    label = client.get(f"{BASE}/drafts/{sid}/recon/directions").json()["directions"][0]["label"]
    assert client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"direction": label}).status_code == 200
    grounding = client.get(f"{BASE}/drafts/{sid}").json()["grounding"]
    assert grounding["pool"]["providers"] == ["openalex", "crossref"]

    again = _probe(client, sid, databases=["openalex", "crossref"])
    assert again["result"]["served_from_cache"] is True
    assert client.get(f"{BASE}/drafts/{sid}/recon").json()["binding"]["stale"] is False

    second = _probe(client, sid, databases=["crossref", "openalex"])
    assert second["result"]["served_from_cache"] is False
    assert second["result"]["cache_key"] != first["result"]["cache_key"]
    state = client.get(f"{BASE}/drafts/{sid}/recon").json()
    assert state["binding"]["stale"] is True and state["binding"]["code"] == "POOL_CHANGED"
    refused = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert (refused.status_code, refused.json()["detail"]["code"]) == (409, "STALE_BINDING")


# --------------------------------------------------------------------------- M10b Part C, C4


def test_pool_empty_after_a_long_keyword_query_says_shorten(env):
    """Reproducing (2026-11-13, 02-explore "Explore on an empty search"): the advice showed on every empty search."""
    client, app, _root, _recon = env
    app.state.recon_search_fn = Seam(docs=[])
    sid = _new_draft(client)
    job = _probe(client, sid, query="weed detection drone imagery")
    assert job["state"] == "failed" and job["error"]["code"] == "POOL_EMPTY"
    assert job["error"]["details"]["shorten"] is True


def test_pool_empty_after_a_short_query_does_not_say_shorten(env):
    client, app, _root, _recon = env
    app.state.recon_search_fn = Seam(docs=[])
    sid = _new_draft(client)
    for query in ("weed detection", "weed OR drone OR imagery"):
        job = _probe(client, sid, query=query)
        assert job["error"]["code"] == "POOL_EMPTY"
        assert job["error"]["details"].get("shorten") is not True, query


def test_pool_empty_with_a_failed_database_does_not_say_shorten(env):
    client, app, _root, _recon = env
    app.state.recon_search_fn = Seam(docs=[], failed=["crossref"])
    sid = _new_draft(client)
    job = _probe(client, sid, query="weed detection drone imagery")
    assert job["error"]["code"] == "POOL_EMPTY"
    assert job["error"]["details"].get("shorten") is not True


def test_providers_failed_never_says_shorten(env):
    client, app, _root, _recon = env
    app.state.recon_search_fn = Seam(docs=[], failed=["openalex", "semanticscholar", "crossref", "arxiv"])
    sid = _new_draft(client)
    job = _probe(client, sid, query="weed detection drone imagery")
    assert job["error"]["code"] == "PROVIDERS_FAILED"
    assert "shorten" not in job["error"]["details"]


def test_a_semantic_search_that_finds_nothing_does_not_say_shorten(env):
    client, app, _root, _recon = env
    app.state.recon_search_fn = Seam(docs=[])
    sid = _new_draft(client)
    job = _probe(client, sid, query="weed detection drone imagery", semantic=True)
    assert job["error"]["code"] == "POOL_EMPTY"
    assert job["error"]["details"].get("shorten") is not True


# --------------------------------------------------------------------------- H-provenance-s2 (2026-11-20)


class _OneDatabaseEmpty:
    """OpenAlex answers; Semantic Scholar answers with no record (or fails), as on 2026-11-19."""

    def __init__(self, s2_failed: bool = False):
        self.s2_failed = s2_failed

    def __call__(self, query: Query, providers: list[str]) -> SearchRun:
        docs = _pool()
        legs = [
            SearchLeg(provider="openalex", query_id=query.id, status="ok", fetched=len(docs),
                      reported_total=1637, cap=25, cap_hit=True, executed_query=query.text),
            SearchLeg(provider="semanticscholar", query_id=query.id,
                      status="failed" if self.s2_failed else "ok",
                      error="HTTP 429" if self.s2_failed else None,
                      error_code="PROVIDER_RATE_LIMITED" if self.s2_failed else None,
                      fetched=0, reported_total=None if self.s2_failed else 0, executed_query=query.text),
        ]
        return SearchRun(documents=docs, legs=legs)


def _legs(job: dict) -> dict[str, dict]:
    return {leg["provider"]: leg for leg in job["result"]["legs"]}


def test_one_database_empty_on_a_long_keyword_query_says_shorten_on_its_leg(env):
    """Reproducing (live run 2026-11-19): Semantic Scholar "0 results" on a six-word query
    while OpenAlex answered. Its bulk search needs every word; the advice was only given
    when every database was empty, so it never showed here."""
    client, app, _root, _recon = env
    app.state.recon_search_fn = _OneDatabaseEmpty()
    sid = _new_draft(client)
    job = _probe(client, sid, query="UAV imagery weed detection cereal crops",
                 databases=["openalex", "semanticscholar"])
    assert job["state"] == "succeeded"
    legs = _legs(job)
    assert legs["semanticscholar"]["status"] == "ok" and legs["semanticscholar"]["reported_total"] == 0
    assert legs["semanticscholar"]["shorten"] is True
    assert legs["openalex"]["shorten"] is False
    # The session's record of the probe carries the same legs.
    probes = client.get(f"{BASE}/drafts/{sid}/recon").json()["session"]["probes"]
    assert {leg["provider"]: leg["shorten"] for leg in probes[-1]["legs"]} == {
        "openalex": False, "semanticscholar": True,
    }


def test_a_leg_that_failed_or_a_short_query_never_says_shorten(env):
    client, app, _root, _recon = env
    app.state.recon_search_fn = _OneDatabaseEmpty(s2_failed=True)
    sid = _new_draft(client)
    job = _probe(client, sid, query="UAV imagery weed detection cereal crops",
                 databases=["openalex", "semanticscholar"])
    assert _legs(job)["semanticscholar"]["status"] == "failed"
    assert _legs(job)["semanticscholar"]["shorten"] is False

    app.state.recon_search_fn = _OneDatabaseEmpty()
    for query in ("weed detection", "UAV OR drone OR imagery"):
        job = _probe(client, sid, query=query, databases=["openalex", "semanticscholar"])
        assert _legs(job)["semanticscholar"]["shorten"] is False, query
    job = _probe(client, sid, query="UAV imagery weed detection cereal crops", semantic=True,
                 databases=["openalex", "semanticscholar"])
    assert _legs(job)["semanticscholar"]["shorten"] is False
