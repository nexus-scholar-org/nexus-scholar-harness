"""M11a Part B: known papers, comparison sets and the search development at genesis.

Spec `docs/roadmap/milestones/M11a-query-workbench.md` (c), (d), (e) and DoD 9 to 15, 19.
Hermetic: OpenAlex is a double (``scholar_search.estimate._provider`` is
replaced); the first search's pool is written through the console's search
seam; time is moved by replacing ``query_workbench.utcnow``.
"""

from __future__ import annotations

import base64
import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from scholar_search import estimate as est
from scholar_search.config import settings
from scholar_search.models import Document, ExternalIds

from scholar_harness import query_workbench as qw
from scholar_harness import query_workbench_sets as qs
from scholar_harness.console import browser, create_app, refusals
from scholar_harness.inception.drafts import DraftStore
from scholar_harness.workspace import catalog

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_PROTOCOL = ROOT / "workspaces" / "golden-uav-30" / "protocol.json"
PROXY = ROOT / "apps" / "research-ui" / "app" / "api" / "console" / "[...path]" / "route.ts"
TOKEN = "desk-token"
FOUR = [
    {"concept": "UAV", "synonyms": ["unmanned aerial vehicle"]},
    {"concept": "multispectral", "synonyms": ["multi-spectral"]},
    {"concept": "weed", "synonyms": []},
    {"concept": "segmentation", "synonyms": ["semantic segmentation"]},
]
THREE = [{"concept": "UAV", "synonyms": ["unmanned aerial vehicle", "multispectral", "multi-spectral"]}, FOUR[2], FOUR[3]]
SEEDS = ["10.1/s1", "10.1/s2", "10.1/s3", "10.1/s4"]
STRICT = "Weed segmentation from UAV multispectral imagery"


def _version(concepts=FOUR):
    return {"query_key": "main", "concepts": concepts, "start_year": 2015, "end_year": 2025, "languages": ["en"]}


def _doc(doi, title, abstract=""):
    return Document(title=title, abstract=abstract, external_ids=ExternalIds(doi=doi))


class OpenAlex:
    """An OpenAlex double for the seed lookup and the identifier check."""

    def __init__(self):
        self.works: dict[str, Document] = {}
        self.matching: set[str] = set()  # DOIs the query finds
        self.calls: list[tuple[str, int]] = []
        self.client = None

    async def works_by_doi(self, dois):
        self.calls.append(("lookup", len(dois)))
        return [self.works[d] for d in dois if d in self.works]

    async def find_dois(self, query, dois):
        self.calls.append(("find" if query is not None else "held", len(dois)))
        pool = self.matching if query is not None else set(self.works)
        return [d for d in dois if d in pool]

    async def count(self, query):
        self.calls.append(("count", 1))
        return 100


class Clock:
    def __init__(self):
        self.now = datetime(2026, 11, 21, 10, 15, tzinfo=UTC)

    def __call__(self):
        return self.now


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.delenv("NEXUS_RECON_ROOT", raising=False)
    monkeypatch.delenv("NEXUS_WORKBENCH_OPENALEX_IDS", raising=False)
    root = tmp_path / "root"
    catalog.create(root, "Review")
    ws = root / "review"
    shutil.copy2(GOLDEN_PROTOCOL, ws / "protocol.json")
    openalex, clock = OpenAlex(), Clock()
    monkeypatch.setattr(est, "_provider", lambda name: openalex)
    monkeypatch.setattr(qw, "utcnow", clock)
    monkeypatch.setattr(settings, "mailto", "console@example.invalid")
    monkeypatch.setattr(settings, "openalex_key", "console-test-key")  # a placeholder, never sent
    draft = DraftStore(root).create({"topic": "weeds", "concepts": FOUR, "golden_seeds": SEEDS})["session_id"]
    app = create_app(ws, token=TOKEN, workspaces_root=root)
    app.state.recon_root = tmp_path / "recon"
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        yield client, root, ws, draft, openalex, clock


def _url(draft, what):
    return f"/api/v1/inception/drafts/{draft}/workbench/{what}"


def _code(response):
    return response.json()["detail"]["code"]


def _seed_works(openalex, titles):
    for doi, title in zip(SEEDS, titles):
        openalex.works[doi] = _doc(doi, title)


# --------------------------------------------------------------------------- DoD 9, 10: the seed check by the words


def test_seeds_whose_words_hold_every_concept_cannot_test_the_query(env):
    client, root, ws, draft, openalex, _ = env
    _seed_works(openalex, [STRICT] * 4)
    body = {"version": _version(), "lookup": True, "dry_run": True}
    dry = client.post(_url(draft, "seeds"), json=body).json()
    assert dry["cost"] == {"lookup": 1, "openalex": 0} and openalex.calls == []
    answer = client.post(_url(draft, "seeds"), json=body | {"dry_run": False}).json()
    assert openalex.calls == [("lookup", 4)] and answer["requests"] == 1
    assert (answer["read"], answer["use_every_concept"], answer["missed"]) == (4, 4, 0)
    assert answer["warning"] == {"level": "all", "untested": ["UAV", "multispectral", "weed", "segmentation"]}
    assert answer["query_key"] == "main" and answer["measure"] == "words"
    # The texts are kept: a second check needs no request.
    openalex.calls.clear()
    again = client.post(_url(draft, "seeds"), json=body | {"dry_run": False}).json()
    assert openalex.calls == [] and again["cost"]["lookup"] == 0 and again["read"] == 4


def test_a_seed_that_lacks_a_concept_is_missed_by_the_words_with_its_own_terms_offered(env):
    client, root, ws, draft, openalex, _ = env
    _seed_works(openalex, [STRICT, STRICT, STRICT, "Weed segmentation from UAV RGB orthophotos"])
    answer = client.post(_url(draft, "seeds"), json={"version": _version(), "lookup": True}).json()
    missed = next(s for s in answer["seeds"] if s["doi"] == "10.1/s4")
    assert missed["missed"] is True and missed["lacks"] == ["multispectral"]
    assert "rgb orthophotos" in missed["suggestions"] and not any("weed" in t for t in missed["suggestions"])
    assert answer["warning"] == {"level": "concept", "untested": ["UAV", "weed", "segmentation"]}


def test_an_unread_seed_counts_neither_way_and_too_few_readable_seeds_say_so(env):
    client, root, ws, draft, openalex, _ = env
    _seed_works(openalex, [STRICT, STRICT])  # s3 and s4 are not in OpenAlex
    answer = client.post(_url(draft, "seeds"), json={"version": _version(), "lookup": True}).json()
    assert (answer["read"], answer["not_read"]) == (2, 2)
    assert [s["read"] for s in answer["seeds"]] == [True, True, False, False]
    assert answer["warning"]["level"] == "few"


def test_the_first_searchs_pool_gives_the_words_without_a_request(env, monkeypatch):
    client, root, ws, draft, openalex, _ = env
    from test_inception_checks import PoolSeam
    from test_recon_api import _probe

    seam = PoolSeam({"openalex": 4})
    client.app.state.recon_search_fn = seam
    _probe(client, draft, databases=["openalex"], refresh=True)
    seeds = [f"10.1/openalex.{i}" for i in range(4)]
    answer = client.post(_url(draft, "seeds"), json={"version": _version(), "seeds": seeds}).json()
    assert openalex.calls == [] and answer["read"] == 4
    # "Weed detection with UAV imagery": no multispectral, no segmentation.
    assert all(s["lacks"] == ["multispectral", "segmentation"] for s in answer["seeds"])


def test_no_seed_raises_no_warning(env):
    client, root, ws, draft, openalex, _ = env
    answer = client.post(_url(draft, "seeds"), json={"version": _version(), "seeds": []}).json()
    assert answer["warning"] is None and answer["total"] == 0


# --------------------------------------------------------------------------- DoD 11: OpenAlex per database, behind the switch


def test_the_openalex_seed_check_is_off_until_switched_on(env, monkeypatch):
    client, root, ws, draft, openalex, _ = env
    _seed_works(openalex, [STRICT] * 4)
    body = {"version": _version(), "lookup": True, "openalex": True}
    answer = client.post(_url(draft, "seeds"), json=body).json()
    assert answer["databases"] == [{"name": "openalex", "status": "switch_off", "found": [], "not_found": []}]
    assert ("find", 4) not in openalex.calls
    monkeypatch.setenv("NEXUS_WORKBENCH_OPENALEX_IDS", "1")
    openalex.matching = {"10.1/s1", "10.1/s2", "10.1/s3"}
    dry = client.post(_url(draft, "seeds"), json=body | {"dry_run": True}).json()
    assert dry["cost"] == {"lookup": 0, "openalex": 1}
    answer = client.post(_url(draft, "seeds"), json=body).json()
    oa = answer["databases"][0]
    assert (oa["status"], oa["found"], oa["not_found"]) == ("checked", ["10.1/s1", "10.1/s2", "10.1/s3"], ["10.1/s4"])


def test_the_seed_checks_are_kept_beside_the_draft(env):
    client, root, ws, draft, openalex, _ = env
    _seed_works(openalex, [STRICT] * 4)
    client.post(_url(draft, "seeds"), json={"version": _version(), "lookup": True})
    folder = DraftStore(root).dir / draft / "query_development"
    rows = [json.loads(line) for line in (folder / "seed_checks.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[-1]["query_key"] == "main" and rows[-1]["warning"]["level"] == "all"
    assert json.loads((folder / "seed_texts.json").read_text(encoding="utf-8"))["10.1/s1"]["title"] == STRICT


# --------------------------------------------------------------------------- DoD 12: comparison sets


def _ris(records):
    lines = []
    for r in records:
        lines += ["TY  - JOUR", f"TI  - {r['title']}"]
        if r.get("abstract"):
            lines.append(f"AB  - {r['abstract']}")
        if r.get("doi"):
            lines.append(f"DO  - {r['doi']}")
        lines.append("PY  - 2022")
        lines.append("ER  - ")
    return "\n".join(lines) + "\n"


SCOPUS = [
    {"title": "Weed segmentation from UAV multispectral imagery", "doi": "10.9/a"},
    {"title": "Weed mapping with UAV hyperspectral imagery and deep learning", "doi": "10.9/b",
     "abstract": "Hyperspectral bands improve weed segmentation."},
    {"title": "Hyperspectral weed segmentation from a UAV platform", "doi": "10.9/c",
     "abstract": "deep learning on hyperspectral imagery"},
    {"title": "Segmentation of weeds in RGB images", "doi": "10.9/d"},
]


def _stage_body(records=SCOPUS, *, name="scopus.ris", database="Scopus", string="TITLE-ABS-KEY(uav AND weed)"):
    return {"file_name": name, "content_base64": base64.b64encode(_ris(records).encode()).decode(),
            "database": database, "string": string, "exported_on": "2026-11-20"}


def _stage(client, draft, records=SCOPUS, **kw):
    return client.post(_url(draft, "comparison"), json=_stage_body(records, **kw))


def test_an_export_is_staged_as_a_comparison_set_apart_from_the_corpus(env):
    client, root, ws, draft, openalex, _ = env
    staged = _stage(client, draft)
    assert staged.status_code == 201, staged.text
    data = staged.json()
    assert (data["id"], data["database"], data["records_count"], data["exported_on"]) == ("cmp_001", "Scopus", 4, "2026-11-20")
    assert data["string"] == "TITLE-ABS-KEY(uav AND weed)" and data["no_abstract"] == 2
    folder = DraftStore(root).dir / draft / "query_development" / "comparison" / "cmp_001"
    assert (folder / "export.ris").read_bytes() == _ris(SCOPUS).encode()
    listed = client.get(_url(draft, "comparison")).json()
    assert [s["id"] for s in listed["sets"]] == ["cmp_001"] and "records" not in listed["sets"][0]
    assert not (ws / "literature" / "raw").exists()  # never the corpus staging


def test_a_set_is_removed_and_leaves_a_line_in_the_log(env):
    client, root, ws, draft, openalex, _ = env
    _stage(client, draft)
    assert client.post(_url(draft, "comparison/cmp_001/remove")).status_code == 200
    assert client.get(_url(draft, "comparison")).json()["sets"] == []
    log = qw.draft_log_path(DraftStore(root).dir, draft)
    kinds = [json.loads(line)["kind"] for line in log.read_text(encoding="utf-8").splitlines()]
    assert kinds == ["comparison_staged", "comparison_removed"]
    assert _code(client.post(_url(draft, "comparison/cmp_001/remove"))) == refusals.WORKBENCH_COMPARISON_NOT_FOUND


def test_a_file_that_is_not_an_export_too_large_or_one_set_too_many_is_refused(env, monkeypatch):
    client, root, ws, draft, openalex, _ = env
    bad = client.post(_url(draft, "comparison"), json={
        "file_name": "notes.ris", "content_base64": base64.b64encode(b"hello\nworld\n").decode(), "database": "Scopus"})
    assert bad.status_code == 422 and _code(bad) == refusals.WORKBENCH_COMPARISON_FORMAT
    monkeypatch.setattr(qs, "MAX_SET_RECORDS", 3)
    big = _stage(client, draft)
    assert big.status_code == 422 and _code(big) == refusals.WORKBENCH_COMPARISON_TOO_LARGE
    monkeypatch.setattr(qs, "MAX_SET_RECORDS", 5000)
    for _ in range(qs.MAX_SETS):
        assert _stage(client, draft).status_code == 201
    full = _stage(client, draft)
    assert full.status_code == 409 and _code(full) == refusals.WORKBENCH_COMPARISON_FULL
    folder = DraftStore(root).dir / draft / "query_development" / "comparison"
    assert sorted(p.name for p in folder.iterdir()) == [f"cmp_{i:03d}" for i in range(1, 6)]


# --------------------------------------------------------------------------- DoD 13, 14: the report


def test_the_report_by_the_words_lists_the_missing_records_and_their_shared_terms(env):
    client, root, ws, draft, openalex, _ = env
    _stage(client, draft)
    report = client.post(_url(draft, "comparison/cmp_001/report"), json={"version": _version(), "measure": "words"}).json()
    assert (report["missing_count"], report["total"], report["measure"]) == (3, 4, "words")
    assert report["set"]["database"] == "Scopus" and report["no_abstract"] == 2 and report["requests"] == 0
    lacks = {m["doi"]: m["lacks"] for m in report["missing"]}
    assert lacks == {"10.9/b": ["multispectral"], "10.9/c": ["multispectral"], "10.9/d": ["UAV", "multispectral"]}
    terms = {t["term"]: t["records"] for t in report["terms"]}
    assert terms.get("hyperspectral") == 2 and terms.get("deep learning") == 2
    assert not any("weed" in t or "segmentation" in t for t in terms)  # related to a query term
    assert all(t["of"] == 3 for t in report["terms"]) and len(report["terms"]) <= 15
    merged = client.post(_url(draft, "comparison/cmp_001/report"), json={"version": _version(THREE), "measure": "words"}).json()
    # Merged (UAV OR multispectral): only the RGB paper without UAV is still missing, as on 2026-11-20.
    assert merged["missing_count"] == 1 and merged["missing"][0]["doi"] == "10.9/d"


def test_the_report_pages_by_twenty(env):
    client, root, ws, draft, openalex, _ = env
    _stage(client, draft, [{"title": f"Weed study number {i}", "doi": f"10.8/{i}"} for i in range(45)])
    third = client.post(_url(draft, "comparison/cmp_001/report"),
                        json={"version": _version(), "measure": "words", "page": 3}).json()
    assert (third["page"], third["pages"], len(third["missing"]), third["missing_count"]) == (3, 3, 5, 45)


def test_on_plan_the_report_compares_with_the_harvest_by_doi_or_title(env):
    client, root, ws, draft, openalex, _ = env
    run = ws / "literature" / "search_runs" / "run_001"
    run.mkdir(parents=True)
    (run / "legs.json").write_text(json.dumps({"run": "run_001", "legs": []}), encoding="utf-8")
    (run / "raw.json").write_text(json.dumps([
        {"title": "anything", "external_ids": {"doi": "10.9/A"}},
        {"title": "Hyperspectral weed segmentation from a UAV platform."},
    ]), encoding="utf-8")
    assert client.post("/api/v1/discovery/workbench/comparison", json=_stage_body()).status_code == 201
    report = client.post("/api/v1/discovery/workbench/comparison/cmp_001/report",
                         json={"version": _version(), "measure": "harvest"}).json()
    assert report["against"] == {"label": "run_001", "records": 2} and report["missing_count"] == 2
    assert sorted(m["doi"] for m in report["missing"]) == ["10.9/b", "10.9/d"]
    assert (ws / "audit" / "query_development" / "comparison" / "cmp_001" / "set.json").is_file()
    assert not (ws / "literature" / "raw").exists()
    assert _stage(client, draft).status_code == 201
    refused = client.post(_url(draft, "comparison/cmp_001/report"), json={"version": _version(), "measure": "harvest"})
    assert refused.status_code == 409 and _code(refused) == refusals.WORKBENCH_COMPARISON_MEASURE


def test_the_openalex_measure_costs_two_requests_per_fifty_and_names_records_not_in_openalex(env, monkeypatch):
    client, root, ws, draft, openalex, _ = env
    monkeypatch.setenv("NEXUS_WORKBENCH_OPENALEX_IDS", "1")
    _stage(client, draft)
    openalex.works = {"10.9/a": _doc("10.9/a", "x"), "10.9/b": _doc("10.9/b", "x"), "10.9/d": _doc("10.9/d", "x")}
    openalex.matching = {"10.9/a"}
    body = {"version": _version(), "measure": "openalex"}
    dry = client.post(_url(draft, "comparison/cmp_001/report"), json=body | {"dry_run": True}).json()
    assert dry["cost"] == 2 and dry["status"] == "to_check" and openalex.calls == []
    report = client.post(_url(draft, "comparison/cmp_001/report"), json=body).json()
    assert report["requests"] == 2 and report["missing_count"] == 3 and report["not_in_database"] == 1


def test_the_openalex_measure_is_off_until_switched_on(env):
    client, root, ws, draft, openalex, _ = env
    _stage(client, draft)
    report = client.post(_url(draft, "comparison/cmp_001/report"), json={"version": _version(), "measure": "openalex"}).json()
    assert report["status"] == "switch_off" and openalex.calls == []


# --------------------------------------------------------------------------- DoD 15: genesis carries the development


def test_genesis_copies_the_development_and_the_preview_lists_it(env):
    client, root, ws, draft, openalex, _ = env
    from test_inception_proposals import uav_draft

    sid = client.post("/api/v1/inception/drafts", json={"draft": uav_draft()}).json()["session_id"]
    _seed_works(openalex, [STRICT] * 4)
    assert client.post(_url(sid, "seeds"), json={"version": _version(), "seeds": SEEDS, "lookup": True}).status_code == 200
    assert _stage(client, sid).status_code == 201
    record = DraftStore(root).load(sid)
    preview = client.post("/api/v1/inception/preview", json={"draft": record["draft"], "session_id": sid}).json()
    planned = [f for f in preview["files"] if "query_development" in f]
    assert planned == ["audit/query_development/counts.jsonl", "audit/query_development/seed_checks.jsonl",
                       "audit/query_development/seed_texts.json", "audit/query_development/comparison/"]
    created = client.post(f"/api/v1/inception/drafts/{sid}/genesis", json={})
    assert created.status_code == 201, created.text
    target = Path(created.json()["path"])
    dev = target / "audit" / "query_development"
    assert (dev / "counts.jsonl").read_text(encoding="utf-8") == \
        qw.draft_log_path(DraftStore(root).dir, sid).read_text(encoding="utf-8")
    assert (dev / "comparison" / "cmp_001" / "export.ris").is_file()
    events = [json.loads(line) for line in (target / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()]
    row = next(e for e in events if e.get("action") == "QUERY_DEVELOPMENT_RECORDED")
    assert row["metrics"]["comparison_sets"] == 1 and row["metrics"]["seed_checks"] == 1


def test_a_draft_with_no_development_lists_no_such_file(env):
    client, root, ws, draft, openalex, _ = env
    from test_inception_proposals import uav_draft

    sid = client.post("/api/v1/inception/drafts", json={"draft": uav_draft()}).json()["session_id"]
    record = DraftStore(root).load(sid)
    preview = client.post("/api/v1/inception/preview", json={"draft": record["draft"], "session_id": sid}).json()
    assert not [f for f in preview["files"] if "query_development" in f]


# --------------------------------------------------------------------------- the routes in both allow-lists


ROUTES = [
    "api/v1/inception/drafts/rec_0123abcd/workbench/seeds",
    "api/v1/inception/drafts/rec_0123abcd/workbench/comparison",
    "api/v1/inception/drafts/rec_0123abcd/workbench/comparison/cmp_001/remove",
    "api/v1/inception/drafts/rec_0123abcd/workbench/comparison/cmp_001/report",
    "api/v1/discovery/workbench/seeds",
    "api/v1/discovery/workbench/comparison",
    "api/v1/discovery/workbench/comparison/cmp_001/remove",
    "api/v1/discovery/workbench/comparison/cmp_001/report",
]


@pytest.mark.parametrize("path", ROUTES)
def test_each_route_is_in_the_browser_allow_list_and_the_proxy_and_not_a_phone_route(path):
    from scholar_harness.console import serve

    assert any(p.fullmatch(path) for p in browser.POST_PATHS)
    patterns = [re.compile(m.group(1).replace("\\/", "/"))
                for m in re.finditer(r"^\s*/(\^api.*\$)/,", PROXY.read_text(encoding="utf-8"), re.M)]
    assert any(p.fullmatch(path) for p in patterns)
    assert not serve._phone_may_reach("POST", "/" + path)


# --------------------------------------------------------------------------- DoD 19: the two fixed checks


def _checks(client, sid, step=None):
    answer = client.post(f"/api/v1/inception/drafts/{sid}/checks", json={"step": step} if step else {})
    assert answer.status_code == 200, answer.text
    return answer.json()


def _check(body, check_id):
    return [c for c in body["checks"] if c["check_id"] == check_id]


def _saved_version(root, sid):
    draft = DraftStore(root).load(sid)["draft"]
    return {"query_key": "main", "concepts": draft["concepts"], "start_year": draft.get("start_year"),
            "end_year": draft.get("end_year"), "languages": draft.get("languages") or ["en"]}


def test_query_not_counted_is_a_note_until_the_saved_version_is_counted(env):
    client, root, ws, draft, openalex, _ = env
    body = _checks(client, draft, "criteria")
    (note,) = _check(body, "QUERY_NOT_COUNTED")
    assert note["level"] == "note" and note["message"] == "This search has not been counted in any database yet."
    assert note["action"]["field"] == "concepts" and note["dismissible"] is True
    # Another version counted does not count for the saved one.
    client.post(_url(draft, "counts"), json={"version": _version(THREE), "providers": ["openalex"]})
    assert _check(_checks(client, draft, "criteria"), "QUERY_NOT_COUNTED")
    client.post(_url(draft, "counts"), json={"version": _saved_version(root, draft), "providers": ["openalex"]})
    assert not _check(_checks(client, draft, "criteria"), "QUERY_NOT_COUNTED")


def test_seeds_cannot_test_is_a_warning_with_the_panels_words_and_never_blocks(env):
    client, root, ws, draft, openalex, _ = env
    assert not _check(_checks(client, draft), "SEEDS_CANNOT_TEST")  # the seeds' words are not known yet
    _seed_works(openalex, [STRICT] * 4)
    client.post(_url(draft, "seeds"), json={"version": _version(), "lookup": True})
    body = _checks(client, draft)
    (warning,) = _check(body, "SEEDS_CANNOT_TEST")
    assert warning["level"] == "warning" and warning["step"] == "criteria" and warning["subject"] == "all"
    assert warning["message"] == ("Your 4 known papers each use a term of every concept, so they cannot show "
                                  "a paper this query misses.")
    assert warning["message_key"] == "checks.SEEDS_CANNOT_TEST_all.sentence"
    assert warning["action"]["kind"] == "step" and warning["action"]["step"] == "direction"
    assert not any(c["level"] == "blocker" for c in body["checks"] if c["check_id"] in ("SEEDS_CANNOT_TEST", "QUERY_NOT_COUNTED"))


def test_seeds_cannot_test_names_a_concept_no_seed_lacks(env):
    client, root, ws, draft, openalex, _ = env
    _seed_works(openalex, [STRICT, STRICT, STRICT, "Weed segmentation from UAV RGB orthophotos"])
    client.post(_url(draft, "seeds"), json={"version": _version(), "lookup": True})
    (warning,) = _check(_checks(client, draft), "SEEDS_CANNOT_TEST")
    assert warning["subject"] == "concept" and warning["params"]["concept"] == "UAV"
    assert warning["message"] == "No known paper lacks 'UAV'; the seeds cannot test it."
