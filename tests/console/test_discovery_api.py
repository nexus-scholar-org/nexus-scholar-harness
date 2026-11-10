"""Discovery over HTTP (M3b-api, `docs/architecture/research_ui/DISCOVERY_API_PACKET.md` §4, §8).

Hermetic: the workspace is a scratch folder under ``tmp_path`` with a copy of
the golden protocol; the providers are in-memory doubles that the real
``SearchEngine`` runs (so legs, caps and progress are the engine's own), and
hydration and verification pass records through. Nothing reaches the network.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import time
from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from scholar_search.config import settings
from scholar_search.models import Document, ExternalIds

from scholar_harness.console import create_app
from scholar_harness.pipeline import discovery as disc
from scholar_harness.pipeline import hydration as hyd_mod
from scholar_harness.pipeline import verification as ver_mod
from scholar_harness.workspace import catalog

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_PROTOCOL = ROOT / "workspaces" / "golden-uav-30" / "protocol.json"
TOKEN = "desk-token"
BASE = "/api/v1/discovery"


def _doc(provider: str, i: int, *, year: int = 2023, abstract: str | None = "an abstract", doi: str | None = None,
         arxiv: str | None = None, title: str | None = None) -> Document:
    return Document(
        title=title or f"UAV weed mapping study {provider} {i}", year=year, provider=provider,
        provider_id=f"{provider}-{i}", abstract=abstract,
        external_ids=ExternalIds(doi=doi if doi is not None else f"10.1/{provider}.{i}", arxiv_id=arxiv),
    )


class FakeProvider:
    """A provider double the real engine runs: it fills the leg like a live provider does."""

    def __init__(self, name: str, docs: list[Document], *, total: int | None = None, delay: float = 0.0,
                 fail: Exception | None = None):
        self.name, self.docs, self.total, self.delay, self.fail = name, docs, total, delay, fail
        self.current_leg = None
        self.queries: list[str] = []

    async def search(self, query):
        self.queries.append(query.text)
        leg = self.current_leg
        if leg is not None:
            leg.executed_query = f"{self.name}: {query.text}"
            leg.reported_total = self.total if self.total is not None else len(self.docs)
        if self.fail is not None:
            raise self.fail
        for doc in self.docs:
            if self.delay:
                await asyncio.sleep(self.delay)
            yield deepcopy(doc)


class _PassthroughVerifier:
    async def process_batch(self, docs, verify=True, enrich=True):
        return list(docs), []


class _PassthroughHydrator:
    def __init__(self, client):
        pass

    async def hydrate_missing_abstracts(self, docs, batch_size=50):
        return list(docs), {"attempted": 0, "hydrated": 0, "failed": 0}


class _Client:
    def __init__(self, *a, **k):
        pass

    async def close(self):
        pass


class Providers:
    """What ``_resolve_providers`` hands the engine; a test changes it before a run."""

    def __init__(self):
        self.by_name: dict[str, FakeProvider] = {}
        self.default_docs = 4

    def set(self, name: str, provider: FakeProvider) -> None:
        self.by_name[name] = provider

    def __call__(self, names):
        out = []
        for name in names or []:
            if name not in self.by_name:
                self.by_name[name] = FakeProvider(name, [_doc(name, i) for i in range(self.default_docs)])
            out.append(self.by_name[name])
        return out or None


@pytest.fixture
def env(tmp_path, monkeypatch):
    root = tmp_path / "root"
    catalog.create(root, "Review")
    ws = root / "review"
    shutil.copy2(GOLDEN_PROTOCOL, ws / "protocol.json")
    providers = Providers()
    monkeypatch.setattr(disc, "_resolve_providers", providers)
    monkeypatch.setattr(hyd_mod, "AbstractHydrator", _PassthroughHydrator)
    monkeypatch.setattr(hyd_mod, "AcademicHttpClient", _Client)
    monkeypatch.setattr(ver_mod, "DocumentVerifier", _PassthroughVerifier)
    monkeypatch.setattr(settings, "mailto", "console@example.invalid")
    app = create_app(ws, token=TOKEN, workspaces_root=root)
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        yield client, ws, providers


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
    started = client.post(f"{BASE}/runs", json=body or {})
    assert started.status_code == 202, started.text
    job = started.json()["job"]
    events = _events(client, job["job_id"])
    return client.get(f"{BASE}/jobs/{job['job_id']}").json()["job"], events


def _journal(ws: Path) -> list[dict]:
    path = ws / "audit" / "journal.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_run(ws: Path, number: int, *, started: str, legs: list[dict] | None = None, published: bool = True) -> Path:
    run = ws / "literature" / "search_runs" / f"run_{number:03d}"
    run.mkdir(parents=True)
    legs = legs if legs is not None else [
        {"provider": "openalex", "query_id": "Q", "executed_query": "q", "reported_total": 10, "fetched": 10,
         "cap": 10000, "cap_source": "engine_ceiling", "cap_hit": False, "status": "ok", "error": None,
         "notes": [], "request": {}, "started_at": started, "finished_at": started},
    ]
    (run / "legs.json").write_text(json.dumps({
        "run": run.name, "status": "SUCCESS", "query_id": "Q", "query_text": "q", "year_min": 2020,
        "year_max": 2026, "raw_published": published, "legs": legs,
    }), encoding="utf-8")
    (run / "search_report.md").write_text(f"# Search report (PRISMA-S): {run.name}\n", encoding="utf-8")
    return run


# --------------------------------------------------------------------------- plan


def test_plan_refuses_without_a_protocol(env):
    client, ws, _ = env
    (ws / "protocol.json").unlink()
    response = client.get(f"{BASE}/plan")
    assert response.status_code == 409 and _code(response) == "PROTOCOL_MISSING"
    (ws / "protocol.json").write_text("{not json", encoding="utf-8")
    response = client.get(f"{BASE}/plan")
    assert response.status_code == 422 and _code(response) == "PROTOCOL_INVALID"


def test_plan_reports_the_protocol_cap_and_the_ceiling(env):
    client, ws, _ = env
    plan = client.get(f"{BASE}/plan").json()
    assert plan["shape"] == "discovery.plan-v1"
    assert plan["cap"] == {"value": 10000, "source": "engine_ceiling", "ceiling": 10000}
    assert plan["mailto_set"] is True
    assert plan["protocol_fingerprint"].startswith("sha256:")
    assert plan["query"]["year_min"] == 2020 and plan["query"]["text"]
    by_name = {p["name"]: p for p in plan["providers"]}
    # E1 (M3d-engine): each selected database's string and request, before any run, without a request sent.
    for name in ("openalex", "semanticscholar", "crossref", "arxiv", "pubmed"):
        row = by_name[name]
        assert row["selected"] is True and row["status"] == "translated", row
        assert row["executed_query"] and isinstance(row["request"], dict), row
        assert not {"mailto", "email", "tool", "api_key"} & set(row["request"]), row
        assert any(c.startswith("language (en)") for c in row["cannot_express"]), row
    assert "[pdat]" in by_name["pubmed"]["executed_query"]
    assert any("no year filter" in n for n in by_name["arxiv"]["notes"])
    assert by_name["biorxiv"] == {**by_name["biorxiv"], "selected": False, "status": "off_by_default",
                                  "executed_query": None, "request": None}
    assert plan["imports_hint"] == ["scopus", "wos"]

    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    protocol["method"] = {"retrieval_cap": 500}
    (ws / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    assert client.get(f"{BASE}/plan").json()["cap"] == {"value": 500, "source": "protocol", "ceiling": 10000}


# --------------------------------------------------------------------------- runs


def test_runs_lists_every_search_run_newest_first_and_marks_stale_ones(env):
    client, ws, _ = env
    assert client.get(f"{BASE}/runs").json() == {"shape": "discovery.runs-v1", "runs": [], "active_job": None}
    _write_run(ws, 1, started="2026-11-01T10:00:00+00:00")
    _write_run(ws, 2, started="2026-11-02T10:00:00+00:00")
    _write_run(ws, 3, started="2026-11-03T10:00:00+00:00", published=False)  # a failed harvest publishes nothing
    runs = client.get(f"{BASE}/runs").json()["runs"]
    assert [r["run"] for r in runs] == ["run_003", "run_002", "run_001"]
    assert {r["run"]: r["stale"] for r in runs} == {"run_003": False, "run_002": False, "run_001": True}
    assert runs[1]["legs_total"] == 1 and runs[1]["fetched_total"] == 10 and runs[1]["started_at"].startswith("2026-11-02")

    one = client.get(f"{BASE}/runs/run_002").json()
    assert one["run"] == "run_002" and one["legs"][0]["provider"] == "openalex"
    assert one["report_path"].endswith("search_runs/run_002/search_report.md")
    report = client.get(f"{BASE}/runs/run_002/report")
    assert report.status_code == 200 and report.headers["content-type"].startswith("text/markdown")
    assert "run_002" in report.text
    for missing in ("run_009", "run_00x", "run_1", "legs"):
        response = client.get(f"{BASE}/runs/{missing}")
        assert response.status_code == 404 and _code(response) == "RUN_NOT_FOUND", missing


def test_a_run_cannot_start_without_a_contact_email(env, monkeypatch):
    client, ws, providers = env
    monkeypatch.setattr(settings, "mailto", None)
    response = client.post(f"{BASE}/runs", json={})
    assert response.status_code == 409 and _code(response) == "MAILTO_NOT_SET"
    assert "SCHOLAR_MAILTO" in response.json()["detail"]["message"]
    assert not (ws / "literature" / "search_runs").exists()
    assert client.get(f"{BASE}/plan").json()["mailto_set"] is False
    recall = client.post(f"{BASE}/recall", json={"seeds": [{"id": "10.1/x", "kind": "doi", "source": "you"}]})
    assert recall.status_code == 409 and _code(recall) == "MAILTO_NOT_SET"
    assert not providers.by_name  # no provider was even built


def test_a_run_cannot_start_on_an_accepted_snapshot(env):
    client, ws, _ = env
    (ws / "audit").mkdir(exist_ok=True)
    (ws / "audit" / "artifact_registry.json").write_text(
        json.dumps({"artifacts": {"COR-1": {"artifact_type": "corpus_snapshot", "path": "x.json"}}}), encoding="utf-8"
    )
    response = client.post(f"{BASE}/runs", json={})
    assert response.status_code == 409 and _code(response) == "CORPUS_ALREADY_ACCEPTED"
    assert not (ws / "literature" / "search_runs").exists()


def test_a_run_cannot_start_over_staged_exports(env):
    """A run would end at the snapshot with STAGED_IMPORT_PENDING; it is refused before any request."""
    from scholar_harness.corpus_accept import stage_ris_source

    client, ws, providers = env
    ris = b"TY  - JOUR\nTI  - A staged record\nPY  - 2023\nDO  - 10.1/staged\nER  - \n"
    stage_ris_source(ws, "Scopus", ris, file_name="export.ris", searched_on="2026-11-01")
    response = client.post(f"{BASE}/runs", json={})
    assert response.status_code == 409 and _code(response) == "STAGED_IMPORT_PENDING"
    assert not (ws / "literature" / "search_runs").exists() and not providers.by_name


def test_a_run_refuses_a_cap_outside_the_ceiling_and_an_unknown_provider(env):
    client, _, _ = env
    for cap in (0, 10001, -3):
        response = client.post(f"{BASE}/runs", json={"cap_override": cap})
        assert response.status_code == 422 and _code(response) == "CAP_INVALID", cap
    response = client.post(f"{BASE}/runs", json={"providers": ["scopus"]})
    assert response.status_code == 422 and _code(response) == "PROVIDER_UNKNOWN"


def test_one_discovery_job_per_workspace(env):
    client, _, providers = env
    providers.set("openalex", FakeProvider("openalex", [_doc("openalex", i) for i in range(400)], delay=0.02))
    started = client.post(f"{BASE}/runs", json={"providers": ["openalex"]})
    assert started.status_code == 202
    job = started.json()["job"]
    assert job["kind"] == "run" and job["state"] == "running" and job["job_id"].startswith("djob_")
    again = client.post(f"{BASE}/runs", json={})
    assert again.status_code == 409 and _code(again) == "DISCOVERY_JOB_ACTIVE"
    assert again.json()["detail"]["details"]["job"]["job_id"] == job["job_id"]
    recall = client.post(f"{BASE}/recall", json={"seeds": [{"id": "10.1/x", "kind": "doi", "source": "you"}]})
    assert recall.status_code == 409 and _code(recall) == "DISCOVERY_JOB_ACTIVE"
    assert client.get(f"{BASE}/runs").json()["active_job"]["job_id"] == job["job_id"]
    assert client.post(f"{BASE}/jobs/{job['job_id']}/cancel").json()["job"]["state"] == "cancelled"
    missing = client.get(f"{BASE}/jobs/djob_0000000000000000")
    assert missing.status_code == 404 and _code(missing) == "DISCOVERY_JOB_NOT_FOUND"


def test_run_events_replay_snapshot_legs_stages_and_done(env):
    client, ws, _ = env
    job, events = _run(client, {"cap_override": 3, "note": "first harvest"})
    names = [name for name, _ in events]
    assert names[0] == "snapshot" and names[-1] == "done", names
    legs = [data for name, data in events if name == "leg"]
    assert {leg["provider"] for leg in legs} == {"openalex", "semanticscholar", "crossref", "arxiv", "pubmed"}
    assert set(legs[0]) >= {"job_id", "provider", "fetched", "reported_total", "cap", "cap_hit", "status"}
    stages = [data["stage"] for name, data in events if name == "stage"]
    # M3d-engine (decision 2026-11-10): a browser run stops before the snapshot.
    assert stages == ["discovery", "deduplication", "hydration", "verification", "corpus_snapshot"]
    assert job["state"] == "succeeded" and job["result"]["run"] == "run_001"
    assert job["result"]["stages"]["corpus_snapshot"]["status"] == "NOT_ACCEPTED"

    # A second connect replays the same stream in full.
    assert [name for name, _ in _events(client, job["job_id"])] == names

    manifest = json.loads((ws / "literature" / "search_runs" / "run_001" / "legs.json").read_text(encoding="utf-8"))
    assert manifest["cap_override"] == 3 and "first harvest" in manifest["notes"]
    assert {leg["cap_source"] for leg in manifest["legs"]} == {"run_override"}
    one = client.get(f"{BASE}/runs/run_001").json()
    assert one["cap_override"] == 3
    report = client.get(f"{BASE}/runs/run_001/report").text
    assert "Run override cap: 3" in report and "first harvest" in report
    # The plan still shows only the protocol cap (decision 7).
    assert client.get(f"{BASE}/plan").json()["cap"]["source"] == "engine_ceiling"


def test_cancel_keeps_fetched_records_and_archives_a_partial_run(env):
    client, ws, providers = env
    providers.set("openalex", FakeProvider("openalex", [_doc("openalex", i) for i in range(500)], delay=0.02))
    providers.set("crossref", FakeProvider("crossref", [_doc("crossref", i) for i in range(3)]))
    started = client.post(f"{BASE}/runs", json={"providers": ["openalex", "crossref"]})
    job_id = started.json()["job"]["job_id"]
    time.sleep(0.5)
    cancelled = client.post(f"{BASE}/jobs/{job_id}/cancel")
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["job"]["state"] == "cancelled"
    events = _events(client, job_id)
    assert events[-1][0] == "failed" and events[-1][1]["job"]["state"] == "cancelled"

    run = ws / "literature" / "search_runs" / "run_001"
    manifest = json.loads((run / "legs.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "PARTIAL"
    assert "cancelled by the researcher" in manifest["notes"]
    # Review finding 1: kept, not published as the corpus.
    assert manifest["raw_published"] is False and manifest["raw_kept"] is True
    assert client.get(f"{BASE}/runs").json()["runs"][0]["raw_published"] is False
    legs = {leg["provider"]: leg for leg in manifest["legs"]}
    assert legs["openalex"]["status"] == "stopped" and 0 < legs["openalex"]["fetched"] < 500
    assert legs["crossref"]["status"] == "ok" and legs["crossref"]["fetched"] == 3
    raw = json.loads((run / "raw.json").read_text(encoding="utf-8"))
    assert len(raw) == legs["openalex"]["fetched"] + 3  # the fetched records are kept
    # A cancelled harvest is not the corpus: nothing downstream, no snapshot.
    assert not (ws / "literature" / "raw_search.json").exists()
    assert not (ws / "audit" / "artifact_registry.json").exists()
    report = client.get(f"{BASE}/report").json()
    assert {r["database"]: r["completeness"] for r in report["identification"]}["openalex"] == "stopped"
    again = client.post(f"{BASE}/jobs/{job_id}/cancel")
    assert again.status_code == 200 and again.json()["job"]["state"] == "cancelled"


def test_closing_the_console_keeps_the_fetched_records_as_a_partial_run(tmp_path, monkeypatch):
    """Decision 1: a run held by the console stops with it, and what was fetched is kept."""
    root = tmp_path / "root"
    catalog.create(root, "Review")
    ws = root / "review"
    shutil.copy2(GOLDEN_PROTOCOL, ws / "protocol.json")
    providers = Providers()
    providers.set("openalex", FakeProvider("openalex", [_doc("openalex", i) for i in range(500)], delay=0.02))
    monkeypatch.setattr(disc, "_resolve_providers", providers)
    monkeypatch.setattr(settings, "mailto", "console@example.invalid")
    app = create_app(ws, token=TOKEN, workspaces_root=root)
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        assert client.post(f"{BASE}/runs", json={"providers": ["openalex"]}).status_code == 202
        time.sleep(0.3)
    manifest = json.loads((ws / "literature" / "search_runs" / "run_001" / "legs.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "PARTIAL" and "cancelled by the researcher" in manifest["notes"]
    assert 0 < manifest["legs"][0]["fetched"] < 500


# --------------------------------------------------------------------------- recall


class _Verifier:
    """DOI → the title the registry gives; one DOI resolves to another work."""

    titles = {
        "10.1/openalex.0": "UAV weed mapping study openalex 0",
        "10.1/swapped": "A different paper about soil moisture",
    }

    async def verify_document(self, doc):
        doi = (doc.external_ids.doi or "").lower()
        title = self.titles.get(doi)
        if title is None:
            return False, doc, "unresolved"
        from scholar_search.verifier import DocumentVerifier

        resolved = Document(title=title, provider="crossref", external_ids=ExternalIds(doi=doi))
        mismatch = DocumentVerifier._title_mismatch(doc, resolved, f"DOI {doi} (Crossref)")
        if mismatch:
            return False, doc, mismatch
        return True, resolved, "Verified"


@pytest.fixture
def recall_env(env, monkeypatch):
    import scholar_search.recall as recall_mod

    monkeypatch.setattr(recall_mod, "DocumentVerifier", _Verifier)
    client, ws, providers = env
    providers.set("openalex", FakeProvider("openalex", [
        _doc("openalex", 0), _doc("openalex", 1, doi="10.1/swapped", title="UAV weed mapping with drones"),
    ]))
    providers.set("arxiv", FakeProvider("arxiv", [_doc("arxiv", 0, doi="", arxiv="2301.00001")]))
    providers.set("pubmed", FakeProvider("pubmed", [], fail=RuntimeError("boom")))
    return env


SEEDS = [
    {"id": "10.1/openalex.0", "kind": "doi", "source": "anchor"},
    {"id": "10.1/swapped", "kind": "doi", "source": "you"},
    {"id": "arXiv:2301.00001v2", "kind": "arxiv", "source": "you"},
    {"id": "10.1/never", "kind": "doi", "source": "you"},
]


def _recall(client, seeds=SEEDS, providers=None):
    body = {"seeds": seeds} if providers is None else {"seeds": seeds, "providers": providers}
    started = client.post(f"{BASE}/recall", json=body)
    assert started.status_code == 202, started.text
    job = started.json()["job"]
    assert job["kind"] == "recall"
    events = _events(client, job["job_id"])
    assert events[-1][0] == "done", events[-1]
    return client.get(f"{BASE}/recall").json()


def test_recall_never_rewrites_the_query(recall_env):
    client, ws, providers = recall_env
    missing = client.get(f"{BASE}/recall")
    assert missing.status_code == 404 and _code(missing) == "RECALL_NOT_RUN"
    protocol_before = (ws / "protocol.json").read_bytes()
    plan_query = client.get(f"{BASE}/plan").json()["query"]["text"]

    check = _recall(client, providers=["openalex", "arxiv", "pubmed"])

    assert check["shape"] == "discovery.recall-v1" and check["query_text"] == plan_query
    for name in ("openalex", "arxiv", "pubmed"):
        assert providers.by_name[name].queries == [plan_query], name  # exactly the protocol's query, once
    assert (ws / "protocol.json").read_bytes() == protocol_before
    assert all("doi:" not in leg["executed_query"] for leg in check["legs"] if leg["executed_query"])
    seeds = {s["id"]: s for s in check["seeds"]}
    assert seeds["10.1/openalex.0"]["per_provider"] == {"openalex": "found", "arxiv": "n/a", "pubmed": "failed"}
    assert seeds["arXiv:2301.00001v2"]["per_provider"]["arxiv"] == "found"
    assert seeds["arXiv:2301.00001v2"]["per_provider"]["pubmed"] == "n/a"
    assert check["found"] == 3 and check["total"] == 4 and check["missed_everywhere"] == ["10.1/never"]
    stored = json.loads((ws / "literature" / "recall_checks" / "check_001.json").read_text(encoding="utf-8"))
    assert stored == check
    rows = [r for r in _journal(ws) if r.get("action") == "DISCOVERY_RECALL_CHECK"]
    assert len(rows) == 1 and rows[0]["parameters"]["missed_everywhere"] == ["10.1/never"]
    assert rows[0]["agent_or_tool"] == "scholar-harness-console"

    for bad in ([], [{"id": "", "kind": "doi", "source": "you"}], [{"id": "x", "kind": "isbn", "source": "you"}],
                [{"id": f"10.1/{i}", "kind": "doi", "source": "you"} for i in range(26)]):
        response = client.post(f"{BASE}/recall", json={"seeds": bad})
        assert response.status_code == 422 and _code(response) == "SEEDS_INVALID", bad


def test_recall_reports_a_doi_title_mismatch_and_keeps_the_seed(recall_env):
    client, ws, _ = recall_env
    check = _recall(client, providers=["openalex", "arxiv"])
    seeds = {s["id"]: s for s in check["seeds"]}
    swapped = seeds["10.1/swapped"]
    assert swapped["title_check"] == "DOI_TITLE_MISMATCH"
    assert swapped["title"] == "UAV weed mapping with drones"  # the found record, never the resolved one
    assert swapped["per_provider"]["openalex"] == "found"
    assert seeds["10.1/openalex.0"]["title_check"] == "ok"
    assert seeds["10.1/never"]["title_check"] == "unresolved"
    assert len(check["seeds"]) == 4
    second = _recall(client, providers=["openalex"])
    assert (ws / "literature" / "recall_checks" / "check_002.json").is_file()
    assert second["checked_at"] >= check["checked_at"]


# --------------------------------------------------------------------------- report


def test_report_marks_a_capped_leg_as_a_lower_bound(env):
    client, ws, providers = env
    assert _code(client.get(f"{BASE}/report")) == "RUN_NOT_FOUND"
    providers.set("openalex", FakeProvider("openalex", [_doc("openalex", i, abstract=None if i < 2 else "a")
                                                        for i in range(10)], total=40))
    providers.set("crossref", FakeProvider("crossref", [_doc("openalex", 0)] + [_doc("crossref", i) for i in range(2)]))
    job, _ = _run(client, {"cap_override": 5, "providers": ["openalex", "crossref"]})
    assert job["state"] == "succeeded", job

    report = client.get(f"{BASE}/report").json()
    assert report["shape"] == "discovery.report-v1" and report["run"] == "run_001"
    rows = {r["database"]: r for r in report["identification"]}
    assert rows["openalex"]["completeness"] == "lower_bound"
    assert rows["openalex"]["reported_total"] == 40 and rows["openalex"]["fetched"] == 5
    assert rows["openalex"]["no_abstract_rate"] == pytest.approx(2 / 5)
    assert rows["crossref"]["completeness"] == "full" and rows["crossref"]["kind"] == "search"
    assert {n["database"] for n in report["not_searched"]} == {"semanticscholar", "arxiv", "pubmed", "biorxiv"}
    assert report["dedup"]["removed"] == 1 and report["dedup"]["unique_works"] == 7
    # E4a (M3d-engine): the one duplicate shares a DOI.
    assert report["dedup"]["by_tier"] == {"identifier": 1, "exact_title": 0, "fuzzy_title": 0}
    assert report["outside_year_window"] == 0
    # M3d-engine: no screening is prepared before the hand-off accept, so there is no PRISMA preview yet.
    assert report["prisma"] is None
    assert [r["run"] for r in report["runs"]["runs"]] == ["run_001"]


def test_methods_text_is_a_draft_until_reviewed(env):
    client, ws, _ = env
    _run(client, {"cap_override": 3})
    methods = client.get(f"{BASE}/report").json()["methods_text"]
    assert methods["reviewed"] is False and methods["built_from"] == "run_001"
    assert "5 databases" in methods["text"] and "3" in methods["text"]

    # Review finding 2: a save that does not say whether it was reviewed is refused, and nothing is journaled.
    unsaid = client.put(f"{BASE}/report/methods", json={"text": "We searched five databases."})
    assert unsaid.status_code == 422
    assert not (ws / "literature" / "search_runs" / "run_001" / "methods.md").exists()
    assert not [r for r in _journal(ws) if r.get("action") == "METHODS_TEXT_REVIEWED"]
    saved = client.put(f"{BASE}/report/methods", json={"text": "We searched five databases.", "reviewed": True})
    assert saved.status_code == 200, saved.text
    stored = (ws / "literature" / "search_runs" / "run_001" / "methods.md").read_text(encoding="utf-8")
    assert stored.startswith("---\n") and "reviewed_at:" in stored and stored.rstrip().endswith("We searched five databases.")
    methods = client.get(f"{BASE}/report").json()["methods_text"]
    assert methods == {**methods, "text": "We searched five databases.", "reviewed": True, "built_from": "run_001"}
    rows = [r for r in _journal(ws) if r.get("action") == "METHODS_TEXT_REVIEWED"]
    assert len(rows) == 1 and rows[0]["parameters"]["run"] == "run_001"

    # A later run starts from its own draft; the reviewed text of run_001 stays and is shown beside it.
    _run(client, {"cap_override": 3})  # allowed: a browser run does not freeze the corpus (M3d-engine)
    methods = client.get(f"{BASE}/report").json()["methods_text"]
    assert methods["built_from"] == "run_002" and methods["reviewed"] is False
    assert methods["earlier_reviewed"]["run"] == "run_001"
    assert (ws / "literature" / "search_runs" / "run_001" / "methods.md").read_text(encoding="utf-8") == stored


# --------------------------------------------------------------------------- handoff


def test_handoff_counts_abstracts_and_the_year_window_from_verified_json(env):
    client, ws, _ = env
    rows = [
        {"title": "a", "year": 2021, "abstract": "x", "provider": "openalex",
         "sources": [{"provider": "openalex", "id": "1"}, {"provider": "crossref", "id": "c1"}]},
        {"title": "b", "year": 2010, "abstract": "x", "provider": "openalex", "sources": [{"provider": "openalex", "id": "2"}]},
        {"title": "c", "year": 2024, "abstract": "", "provider": "arxiv", "sources": [{"provider": "arxiv", "id": "3"}]},
        {"title": "d", "year": None, "abstract": None, "provider": "crossref", "sources": []},
    ]
    (ws / "literature").mkdir(exist_ok=True)
    (ws / "literature" / "verified.json").write_text(json.dumps(rows), encoding="utf-8")
    capped = {"provider": "openalex", "query_id": "Q", "reported_total": 900, "fetched": 500, "cap": 500,
              "cap_source": "protocol", "cap_hit": True, "status": "ok", "notes": [], "started_at": "2026-11-01"}
    _write_run(ws, 1, started="2026-11-01T00:00:00+00:00", legs=[capped])

    handoff = client.get(f"{BASE}/handoff").json()
    assert handoff["shape"] == "discovery.handoff-v1" and handoff["run"] == "run_001"
    assert handoff["abstracts"] == {"with_abstract": 2, "title_only": 2, "share_with_abstract": 0.5}
    assert handoff["outside_year_window"] == 1
    mix = {m["provider"]: m for m in handoff["provider_mix"]}
    assert mix["openalex"]["records"] == 2 and mix["crossref"]["records"] == 2 and mix["arxiv"]["records"] == 1
    assert mix["openalex"]["share"] == 0.5
    assert handoff["lower_bound_databases"] == ["openalex"]
    # Review finding 4: a later run that was not published does not replace the corpus run.
    _write_run(ws, 2, started="2026-11-02T00:00:00+00:00", published=False, legs=[{**capped, "provider": "crossref"}])
    later = client.get(f"{BASE}/handoff").json()
    assert later["run"] == "run_001" and later["lower_bound_databases"] == ["openalex"]
    assert handoff["near_twins_undecided"] is None
    assert handoff["protocol_fingerprint"].startswith("sha256:")
    assert handoff["corpus"]["shape"] == "screening.corpus-v1"


# --------------------------------------------------------------------------- hand-off accept (M3d-engine)


def test_a_browser_run_stops_before_the_snapshot_and_the_handoff_accepts_it(env):
    """Decision 2026-11-10: a browser harvest does not freeze the corpus; the hand-off screen does."""
    client, ws, _ = env
    job, _ = _run(client, {"providers": ["openalex", "crossref"]})
    assert job["state"] == "succeeded", job
    snapshot = job["result"]["stages"]["corpus_snapshot"]
    assert snapshot == {"status": "NOT_ACCEPTED", "reason": "awaiting the hand-off accept"}
    assert job["result"]["status"] == "PENDING_CORPUS_ACCEPT"
    registry = ws / "audit" / "artifact_registry.json"
    assert not registry.is_file() or "corpus_snapshot" not in registry.read_text(encoding="utf-8")
    assert not list((ws / "literature" / "screening").glob("batch_*.json")) if (ws / "literature" / "screening").is_dir() else True
    actions = [e["action"] for e in _journal(ws)]
    assert "CORPUS_SNAPSHOT_ACCEPTED" not in actions and "PIPELINE_RUN_PAUSED_FOR_CORPUS_ACCEPT" in actions

    before = client.get("/api/v1/screening/corpus").json()
    assert before["state"] == "STAGED" and before["from_discovery"] is True and before["accepted"] is None
    assert client.get(f"{BASE}/handoff").json()["corpus"]["state"] == "STAGED"

    # Another browser run is allowed before the accept, and is the corpus the accept freezes.
    second, _ = _run(client, {"providers": ["openalex"]})
    assert second["state"] == "succeeded" and second["result"]["run"] == "run_002"

    accepted = client.post("/api/v1/screening/corpus/accept")
    assert accepted.status_code == 200, accepted.text
    after = accepted.json()
    assert after["state"] == "ACCEPTED" and after["from_discovery"] is True
    assert after["accepted"]["studies"] == len(json.loads((ws / "literature" / "verified.json").read_text(encoding="utf-8")))
    assert client.get(f"{BASE}/handoff").json()["corpus"]["state"] == "ACCEPTED"
    events = [e for e in _journal(ws) if e["action"] == "CORPUS_SNAPSHOT_ACCEPTED"]
    assert len(events) == 1 and events[0]["parameters"]["artifact_id"] == after["accepted"]["artifact_id"]

    again = client.post(f"{BASE}/runs", json={})
    assert again.status_code == 409 and _code(again) == "CORPUS_ALREADY_ACCEPTED"
    twice = client.post("/api/v1/screening/corpus/accept")
    assert twice.status_code == 409 and _code(twice) == "CORPUS_ALREADY_ACCEPTED"


def test_the_handoff_accept_keeps_a_failed_database_as_a_snapshot_warning(env):
    """The accept reads the run's failed legs, as the pipeline passed them, so the outcome stays PARTIAL."""
    client, ws, providers = env
    providers.set("crossref", FakeProvider("crossref", [], fail=RuntimeError("boom")))
    job, _ = _run(client, {"providers": ["openalex", "crossref"]})
    assert job["state"] == "succeeded", job
    assert client.post("/api/v1/screening/corpus/accept").status_code == 200
    event = next(e for e in _journal(ws) if e["action"] == "CORPUS_SNAPSHOT_ACCEPTED")
    assert event["parameters"]["outcome_status"] == "PARTIAL"
    assert any(w.startswith("crossref: ") for w in event["parameters"]["provider_warnings"])


def test_report_lists_each_imports_limits_and_rejected_lines(env):
    """E3 (M3d-engine, packet §4.6): imports[].limits and imports[].rejected come from the staged rows."""
    from scholar_harness.corpus_accept import stage_ris_source

    client, ws, _ = env
    _write_run(ws, 1, started="2026-11-10T08:00:00Z")
    fixture = ROOT / "tests" / "kits" / "search" / "fixtures" / "imports" / "rejections.ris"
    stage_ris_source(ws, "Scopus", fixture.read_bytes(), file_name="scopus.ris", searched_on="2026-11-10",
                     query="uav AND weed", limits="English; 2018-2025")
    (imp,) = client.get(f"{BASE}/report").json()["imports"]
    assert imp["limits"] == "English; 2018-2025" and imp["records"] == 3
    assert [r["code"] for r in imp["rejected"]] == ["IMPORT_BAD_TAG", "IMPORT_NO_TITLE", "IMPORT_BAD_YEAR"]


# --------------------------------------------------------------------------- dedup (E4a)


def test_dedup_reports_the_counts_per_tier_of_the_newest_deduplication(env):
    """E4a (M3d-engine, packet §4.5 Stage 1): counts only, from literature/dedup/clusters.json."""
    client, ws, providers = env
    missing = client.get(f"{BASE}/dedup")
    assert missing.status_code == 404 and _code(missing) == "DEDUP_NOT_RUN"

    providers.set("openalex", FakeProvider("openalex", [
        _doc("openalex", 0), _doc("openalex", 1, title="Drone imagery for weed detection", doi=""),
        _doc("openalex", 2),
    ]))
    providers.set("crossref", FakeProvider("crossref", [
        _doc("openalex", 0),  # same DOI as openalex 0: identifier
        _doc("crossref", 1, title="Drone imagery for weed detection", doi=""),  # same title, no DOI: exact title
        _doc("crossref", 2),
    ]))
    job, _ = _run(client, {"providers": ["openalex", "crossref"]})
    assert job["state"] == "succeeded", job
    dedup = client.get(f"{BASE}/dedup").json()
    assert dedup == {
        "shape": "discovery.dedup-v1", "run": "run_001", "input_records": 6, "unique_works": 4, "removed": 2,
        "removed_rate": round(2 / 6, 4), "tiers": {"identifier": 1, "exact_title": 1, "fuzzy_title": 0},
        "method": {"title_similarity": 0.97, "year_tolerance": 1, "first_author": True, "source": "default"},
        "near_twins": None,
    }
    assert client.get(f"{BASE}/report").json()["dedup"]["by_tier"] == dedup["tiers"]


def test_after_a_browser_run_the_corpus_says_why_an_export_cannot_be_staged(env):
    """Researcher, 2026-11-10 ("keep the rule for now, combine later"): an export is staged only
    before any run; the corpus view names the refusal so the Import and hand-off screens can show it."""
    import base64

    client, ws, _ = env
    assert client.get("/api/v1/screening/corpus").json()["staging_refused"] is None
    job, _ = _run(client, {"providers": ["openalex"]})
    assert job["state"] == "succeeded", job
    corpus = client.get("/api/v1/screening/corpus").json()
    assert corpus["staging_refused"]["code"] == "VERIFIED_EXISTS"
    assert "search run" in corpus["staging_refused"]["message"]
    assert client.get(f"{BASE}/handoff").json()["corpus"]["staging_refused"] == corpus["staging_refused"]
    ris = b"TY  - JOUR\nTI  - A record\nPY  - 2023\nER  -\n"
    staged = client.post("/api/v1/screening/corpus/sources", json={
        "label": "Scopus", "file_name": "scopus.ris", "content_base64": base64.b64encode(ris).decode("ascii"),
    })
    assert staged.status_code == 409 and _code(staged) == "VERIFIED_EXISTS"
    assert staged.json()["detail"]["message"] == corpus["staging_refused"]["message"]

    assert client.post("/api/v1/screening/corpus/accept").status_code == 200
    assert client.get("/api/v1/screening/corpus").json()["staging_refused"]["code"] == "CORPUS_ALREADY_ACCEPTED"
