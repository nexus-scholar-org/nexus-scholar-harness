"""Sample curation over HTTP (M10b Part C, ``02-explore`` "Sample curation (M10b)").

``GET``/``POST /api/v1/inception/drafts/{id}/recon/sample`` and every recon
read over the effective pool. Hermetic: the console's search seam replaces the
providers; the recon cache is ``tmp_path``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import E2E_ANSWERS
from fastapi.testclient import TestClient
from scholar_search.models import Document, ExternalIds, Query, SearchLeg, SearchRun

from scholar_harness.console import create_app
from scholar_harness.inception.drafts import DraftStore
from scholar_harness.inception.intent import CriterionDraft

TOKEN = "desk-token"
BASE = "/api/v1/inception"


def _doc(i: int, title: str, abstract: str, doi: bool = True) -> Document:
    return Document(
        title=title, year=2023, provider="openalex", provider_id=f"W{i:06d}",
        external_ids=ExternalIds(doi=f"10.1/w{i:03d}" if doi else None), abstract=abstract, url=f"https://example.org/{i}",
    )


def _docs(filler: int = 16, no_doi: bool = False) -> list[Document]:
    """8 on-topic papers, 2 that make a direction alone, and filler; 30 records give a reserve of 5."""
    docs = [_doc(i, f"Real-time weed detection on embedded hardware {i}", "an on-device inference pipeline for weed detection")
            for i in range(8)]
    docs += [_doc(200 + i, f"Hyperspectral canopy imaging study {i}", "hyperspectral canopy imaging of fields") for i in range(2)]
    words = ["apple", "river", "violin", "granite", "lantern", "harbor", "meadow", "pepper", "saddle", "tundra",
             "walnut", "zephyr", "anchor", "bramble", "cobalt", "dune", "ember", "fjord", "glacier", "hazel"]
    docs += [_doc(300 + i, f"Note {w}", f"{w} alone", doi=not (no_doi and i == 0)) for i, w in enumerate(words[:filler])]
    return docs


class Seam:
    def __init__(self, docs: list[Document]):
        self.docs = docs

    def __call__(self, query: Query, providers: list[str]) -> SearchRun:
        legs = [SearchLeg(provider=p, query_id=query.id, status="ok") for p in providers]
        return SearchRun(documents=list(self.docs), legs=legs)


def _accept_out_of_scope(answer: str) -> dict:
    """H-run-small-fixes (finding 2): each out-of-scope item waits for Accept; this draft accepts them."""
    return {
        CriterionDraft("exclusion", item.strip(), "out_of_scope", "OUT_OF_SCOPE").id: True
        for item in answer.split(",")
        if item.strip()
    }


def _draft() -> dict:
    a = E2E_ANSWERS
    proof_id = CriterionDraft("inclusion", f"Reports the gold-standard proof — {a[5]}", "proof").id
    return {
        "topic": a[0], "paradigm": a[1], "playbook": a[2], "unit_of_analysis": a[4], "proof": a[5],
        "method_not_reported": "unclear",  # M11b part D: the rule is chosen (no default)
        "out_of_scope": [s.strip() for s in a[6].split(",")], "rqs": [a[8]],
        "concepts": [{"concept": "weed detection"}, {"concept": "hyperspectral canopy"}],
        "criteria_decisions": {proof_id: True, **_accept_out_of_scope(a[6])},
        "title": "On-Device Weed Detection for Embedded Agriculture", "lead_researcher": "Dr. Example",
    }


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.delenv("NEXUS_RECON_ROOT", raising=False)
    root = tmp_path / "root"
    root.mkdir()
    app = create_app(None, token=TOKEN, workspaces_root=root)
    app.state.recon_root = tmp_path / "recon"
    app.state.recon_search_fn = Seam(_docs())
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        yield client, app, root


def _new(client) -> str:
    created = client.post(f"{BASE}/drafts", json={"draft": _draft()})
    assert created.status_code == 201, created.text
    return created.json()["session_id"]


def _probe(client, sid: str, **body) -> dict:
    started = client.post(f"{BASE}/drafts/{sid}/recon/probe", json=body)
    assert started.status_code == 202, started.text
    job = started.json()["job"]
    with client.stream("GET", f"{BASE}/drafts/{sid}/recon/jobs/{job['job_id']}/events") as stream:
        for _line in stream.iter_lines():
            pass
    done = client.get(f"{BASE}/drafts/{sid}/recon/jobs/{job['job_id']}").json()["job"]
    assert done["state"] == "succeeded", done
    return done["result"]


def _searched(client) -> str:
    sid = _new(client)
    _probe(client, sid, databases=["openalex"])
    return sid


def _mark(client, sid: str, **body):
    return client.post(f"{BASE}/drafts/{sid}/recon/sample", json=body)


def _keys(client, sid: str) -> list[str]:
    return [p["key"] for p in client.post(f"{BASE}/drafts/{sid}/recon/distill").json()["papers"]]


def _labels(client, sid: str) -> list[str]:
    return [d["label"] for d in client.get(f"{BASE}/drafts/{sid}/recon/directions").json()["directions"]]


def test_the_sample_starts_with_nothing_left_out_and_a_reserve(env):
    client, _app, _root = env
    sid = _searched(client)
    sample = client.get(f"{BASE}/drafts/{sid}/recon/sample")
    assert sample.status_code == 200, sample.text
    body = sample.json()
    assert (body["n_docs"], body["n_docs_raw"], body["max_docs"], body["reserve_n"], body["has_reserve"]) == (25, 25, 25, 1, True)
    assert body["excluded"] == [] and body["recommend"]["search"] is False
    assert len(_keys(client, sid)) == 25


def test_leaving_a_paper_out_removes_its_direction_and_a_reserve_paper_replaces_it(env):
    """Reproducing (strict run 2026-11-13): the directions kept counting off-topic papers; no route let the researcher say so."""
    client, _app, _root = env
    sid = _searched(client)
    assert "hyperspectral canopy imaging" in _labels(client, sid)
    before = client.get(f"{BASE}/drafts/{sid}").json()["updated_at"]
    marked = _mark(client, sid, add=["10.1/w200"], base_updated_at=before)
    assert marked.status_code == 200, marked.text
    body = marked.json()
    assert body["updated_at"] != before and body["n_docs"] == 25 and body["reserve_n"] == 0
    assert [(e["key"], e["in_pool"]) for e in body["excluded"]] == [("10.1/w200", True)]
    assert "hyperspectral canopy imaging" not in _labels(client, sid)
    papers = client.post(f"{BASE}/drafts/{sid}/recon/distill").json()["papers"]
    assert "10.1/w200" not in [p["key"] for p in papers]
    assert [p["added_for"] for p in papers if p["added_for"]] == ["10.1/w200"]


def test_leaving_out_and_putting_back_are_idempotent_and_never_touch_the_pool_file(env):
    client, _app, _root = env
    sid = _searched(client)
    pool_path = Path(client.post(f"{BASE}/drafts/{sid}/recon/distill").json()["pool"]["path"])
    original = pool_path.read_bytes()
    assert _mark(client, sid, add=["10.1/w000"]).status_code == 200
    again = _mark(client, sid, add=["10.1/w000"])
    assert again.status_code == 200 and [e["key"] for e in again.json()["excluded"]] == ["10.1/w000"]
    assert pool_path.read_bytes() == original
    back = _mark(client, sid, remove=["10.1/w000"])
    assert back.status_code == 200 and back.json()["excluded"] == []
    assert _mark(client, sid, remove=["10.1/w000"]).status_code == 200, "putting back a paper twice is not an error"
    assert pool_path.read_bytes() == original
    assert "10.1/w000" in _keys(client, sid)


def test_an_unknown_paper_is_refused_and_nothing_changes(env):
    client, _app, _root = env
    sid = _searched(client)
    before = client.get(f"{BASE}/drafts/{sid}").json()
    refused = _mark(client, sid, add=["10.1/w000", "10.9/nope"])
    assert refused.status_code == 422
    assert refused.json()["detail"]["code"] == "PAPER_UNKNOWN"
    assert refused.json()["detail"]["details"]["keys"] == ["10.9/nope"]
    after = client.get(f"{BASE}/drafts/{sid}").json()
    assert after["updated_at"] == before["updated_at"] and not after.get("sample_exclusions")


def test_a_paper_without_a_doi_is_left_out_by_its_pool_id(env):
    client, app, _root = env
    app.state.recon_search_fn = Seam(_docs(no_doi=True))
    sid = _searched(client)
    keys = _keys(client, sid)
    assert "openalex|W000300" in keys and "" not in keys
    assert _mark(client, sid, add=["openalex|W000300"]).status_code == 200
    assert "openalex|W000300" not in _keys(client, sid)


def test_past_200_papers_left_out_the_draft_is_full(env):
    client, app, _root = env
    sid = _searched(client)
    store = DraftStore(Path(app.state.workspaces_root))
    items = [{"key": f"10.8/old{i}", "reason": "NOT_RELEVANT"} for i in range(200)]
    store.transact(sid, lambda r: r.__setitem__("sample_exclusions", {"items": items}), answer=False)
    refused = _mark(client, sid, add=["10.1/w000"])
    assert refused.status_code == 422 and refused.json()["detail"]["code"] == "SAMPLE_EXCLUSIONS_FULL"
    assert refused.json()["detail"]["details"]["limit"] == 200
    assert len(client.get(f"{BASE}/drafts/{sid}").json()["sample_exclusions"]["items"]) == 200


def test_a_stale_base_is_a_conflict_and_an_emitted_draft_is_refused(env):
    client, app, _root = env
    sid = _searched(client)
    stale = _mark(client, sid, add=["10.1/w000"], base_updated_at="2000-01-01T00:00:00+00:00")
    assert stale.status_code == 409 and stale.json()["detail"]["code"] == "DRAFT_CONFLICT"
    DraftStore(Path(app.state.workspaces_root)).mark_emitted(sid, {"slug": "x", "path": "x"})
    emitted = _mark(client, sid, add=["10.1/w000"])
    assert emitted.status_code == 409 and emitted.json()["detail"]["code"] == "DRAFT_EMITTED"


def test_a_draft_save_keeps_the_papers_left_out(env):
    client, _app, _root = env
    sid = _searched(client)
    marked = _mark(client, sid, add=["10.1/w000"]).json()
    saved = client.put(f"{BASE}/drafts/{sid}", json={"draft": _draft(), "base_updated_at": marked["updated_at"]})
    assert saved.status_code == 200, saved.text
    assert [i["key"] for i in saved.json()["sample_exclusions"]["items"]] == ["10.1/w000"]
    item = saved.json()["sample_exclusions"]["items"][0]
    assert item["reason"] == "NOT_RELEVANT" and item["pool_fingerprint"].startswith("sha256:") and item["excluded_at"]


def test_two_drafts_sharing_a_cached_pool_keep_their_own_exclusions(env):
    client, _app, _root = env
    a, b = _searched(client), _searched(client)
    assert _mark(client, a, add=["10.1/w000"]).status_code == 200
    assert "10.1/w000" not in _keys(client, a) and "10.1/w000" in _keys(client, b)


def test_every_recon_read_skips_the_papers_left_out(env):
    client, _app, _root = env
    sid = _searched(client)
    _mark(client, sid, add=["10.1/w200"])
    concepts = client.get(f"{BASE}/drafts/{sid}/recon/concepts").json()
    row = next(c for c in concepts["concepts"] if c["concept"] == "hyperspectral canopy")
    assert row["anchored_in"] == 1 and concepts["n_docs"] == 25
    evidence = client.get(f"{BASE}/drafts/{sid}/recon/evidence", params={"term": "hyperspectral canopy imaging"}).json()
    assert evidence["observed_in"] == 1 and evidence["anchor_dois"] == ["10.1/w201"]
    seeds = client.get(f"{BASE}/drafts/{sid}/recon/seeds").json()["papers"]
    assert "10.1/w200" not in [s["doi"] for s in seeds], "a left-out paper is never offered as a seed"


def test_a_change_of_the_sample_after_the_bind_makes_the_direction_stale(env):
    client, _app, root = env
    sid = _searched(client)
    record = client.get(f"{BASE}/drafts/{sid}").json()
    bound = client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"direction": "real-time weed detection",
                                                                  "base_updated_at": record["updated_at"]})
    assert bound.status_code == 200, bound.text
    assert bound.json()["grounding"]["sample_exclusions_digest"].startswith("sha256:")
    assert client.get(f"{BASE}/drafts/{sid}/recon").json()["binding"]["stale"] is False
    _mark(client, sid, add=["10.1/w300"])
    binding = client.get(f"{BASE}/drafts/{sid}/recon").json()["binding"]
    assert binding["stale"] is True and binding["code"] == "SAMPLE_CHANGED"
    assert client.post(f"{BASE}/drafts/{sid}/genesis", json={}).json()["detail"]["code"] == "STALE_BINDING"
    _mark(client, sid, remove=["10.1/w300"])
    assert client.get(f"{BASE}/drafts/{sid}/recon").json()["binding"]["stale"] is False


def test_genesis_records_the_papers_left_out(env):
    client, _app, root = env
    sid = _searched(client)
    _mark(client, sid, add=["10.1/w200", "10.1/w300"])
    record = client.get(f"{BASE}/drafts/{sid}").json()
    bound = client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"direction": "real-time weed detection",
                                                                  "base_updated_at": record["updated_at"]})
    assert bound.status_code == 200, bound.text
    made = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert made.status_code == 201, made.text
    ws = root / made.json()["slug"]
    ctx = json.loads((ws / "audit" / "recon_context.json").read_text(encoding="utf-8"))
    block = ctx["sample_exclusions"]
    assert (block["n"], block["reason"], block["decided_by"]) == (2, "NOT_RELEVANT", "researcher")
    assert (block["pool_n_docs_raw"], block["effective_n_docs"], block["refilled_from_reserve"]) == (25, 24, 1)
    assert [i["key"] for i in block["items"]] == ["10.1/w200", "10.1/w300"]
    assert ctx["pool_sizes"] == [24]
    assert ctx["term_evidence"]["hyperspectral canopy"]["observed_in"] == 1
    rows = [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()]
    genesis = next(r for r in rows if r["action"] == "GENESIS")
    inline = json.loads(genesis["description"].split("recon_context=", 1)[1])
    assert inline["sample_exclusions_n"] == 2


def test_leaving_out_most_of_the_sample_opens_the_check(env):
    client, _app, _root = env
    sid = _searched(client)
    keys = _keys(client, sid)
    _mark(client, sid, add=keys[:13])
    checks = client.post(f"{BASE}/drafts/{sid}/checks", json={"step": "explore"}).json()["checks"]
    ids = {c["check_id"]: c for c in checks}
    assert "EXPLORE_SAMPLE_MOSTLY_LEFT_OUT" in ids, checks
    row = ids["EXPLORE_SAMPLE_MOSTLY_LEFT_OUT"]
    # 13 left out, one reserve paper refilled: 13 of the 26 papers that were in the sample.
    assert row["params"] == {"k": 13, "total": 26} and row["level"] == "warning"
    assert row["action"]["kind"] == "step" and row["action"]["step"] == "scope"
    assert "EXPLORE_POOL_THIN" not in ids


def test_a_sample_below_the_floor_after_leaving_papers_out_opens_the_thin_pool_check(env):
    client, app, _root = env
    app.state.recon_search_fn = Seam(_docs(filler=4))
    sid = _searched(client)
    assert "EXPLORE_POOL_THIN" not in {c["check_id"] for c in client.post(f"{BASE}/drafts/{sid}/checks", json={"step": "explore"}).json()["checks"]}
    _mark(client, sid, add=["10.1/w300", "10.1/w301"])
    sample = client.get(f"{BASE}/drafts/{sid}/recon/sample").json()
    assert sample["n_docs"] == 12 and sample["recommend"]["search"] is False
    _mark(client, sid, add=["10.1/w302"])
    sample = client.get(f"{BASE}/drafts/{sid}/recon/sample").json()
    assert sample["n_docs"] == 11 and sample["recommend"]["reason"] == "BELOW_FLOOR"
    ids = {c["check_id"] for c in client.post(f"{BASE}/drafts/{sid}/checks", json={"step": "explore"}).json()["checks"]}
    assert "EXPLORE_POOL_THIN" in ids


def test_the_sample_route_needs_a_pool(env):
    client, _app, _root = env
    sid = _new(client)
    assert client.get(f"{BASE}/drafts/{sid}/recon/sample").json()["detail"]["code"] == "RECON_SESSION_NOT_FOUND"
    assert _mark(client, sid, add=["10.1/w000"]).json()["detail"]["code"] == "RECON_SESSION_NOT_FOUND"


def test_the_sample_post_is_in_both_allow_lists():
    from scholar_harness.console.browser import POST_PATHS

    path = "api/v1/inception/drafts/rec_0123456789abcdef/recon/sample"
    assert any(p.fullmatch(path) for p in POST_PATHS)
    route = Path(__file__).resolve().parents[2] / "apps" / "research-ui" / "app" / "api" / "console" / "[...path]" / "route.ts"
    assert "probe|delta|distill|bind|sample" in route.read_text(encoding="utf-8")


def test_the_checks_name_the_pool_by_its_stored_fingerprint(env):
    """Review of Part C, finding 3: the evidence names the pool as stored, as every route does."""
    client, _app, _root = env
    sid = _searched(client)
    _mark(client, sid, add=["10.1/w200", "10.1/w201"])  # the concept "hyperspectral canopy" is then anchored nowhere
    stored = client.get(f"{BASE}/drafts/{sid}/recon/concepts").json()["fingerprint"]
    checks = client.post(f"{BASE}/drafts/{sid}/checks", json={}).json()["checks"]
    assert "CONCEPT_NOT_ANCHORED" in {c["check_id"] for c in checks}
    named = {e["value"] for c in checks for e in c["evidence"] if e.get("name") == "pool"}
    assert named == {stored}, (named, stored)


def test_an_assistant_reads_the_sample_without_the_papers_the_researcher_left_out(env, tmp_path):
    """M10c: the MCP assistant reads the same sample the screens show (M10b Part C curation)."""
    from scholar_harness import assistant
    from scholar_harness.recon.session import ReconSessions

    client, app, root = env
    sid = _searched(client)
    assert _mark(client, sid, add=["10.1/w200"]).status_code == 200
    pool = assistant.read_draft(root, sid, sessions=ReconSessions(root=app.state.recon_root))["pool"]
    assert "10.1/w200" not in [p["doi"] for p in pool["papers"]] and len(pool["papers"]) == 25
    assert [p["doi"] for p in pool["left_out_by_researcher"]] == ["10.1/w200"]
