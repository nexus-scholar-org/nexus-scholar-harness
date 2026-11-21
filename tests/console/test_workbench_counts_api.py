"""M11a Part A: the query workbench's counts (`POST …/workbench/counts`, `…/synonyms`, `…/removed`).

Spec `docs/roadmap/milestones/M11a-query-workbench.md` (a), (b), (f) and DoD 1 to 8, 23.
Hermetic: the databases that count are doubles (``scholar_search.estimate._provider``
is replaced); the exact strings come from each database's own translation,
which sends nothing. Time is moved by replacing ``query_workbench.utcnow``.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from scholar_search import estimate as est
from scholar_search.config import settings
from scholar_search.exceptions import ProviderError, QuotaExhaustedError, RateLimitExceededError
from scholar_search.models import Document, ExternalIds

from scholar_harness import query_workbench as qw
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


def _version(concepts=FOUR, **extra):
    return {"query_key": "main", "concepts": concepts, "start_year": 2015, "end_year": 2025, "languages": ["en"], **extra}


def _default_total(name: str, text: str) -> int:
    """A count that grows when a concept is left out, so drops have gains."""
    total = 166
    if "UAV" not in text:
        total = 236
    if "multispectral" not in text:
        total = 512 if "UAV" in text else 781
    if "weed" not in text:
        total = 900
    if "segmentation" not in text:
        total = 300
    return total + {"openalex": 0, "semanticscholar": -59, "arxiv": -159, "crossref": 6000, "pubmed": -100}.get(name, 0)


class Provider:
    def __init__(self, doubles: Doubles, name: str):
        self.doubles, self.name, self.client = doubles, name, None

    async def count(self, query):
        self.doubles.calls.append((self.name, query.text))
        fail = self.doubles.fail.get(self.name)
        if fail is not None:
            raise fail
        return self.doubles.total(self.name, query.text)

    async def search(self, query):
        self.doubles.calls.append((self.name, "search:" + query.text))
        for doc in self.doubles.docs:
            yield doc


class Doubles:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []
        self.fail: dict[str, Exception] = {}
        self.total = _default_total
        self.docs: list[Document] = []

    def __call__(self, name: str) -> Provider:
        return Provider(self, name)

    def asked(self, name: str | None = None) -> int:
        return sum(1 for n, _ in self.calls if name is None or n == name)


class Clock:
    def __init__(self):
        self.now = datetime(2026, 11, 21, 10, 15, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def env(tmp_path, monkeypatch):
    root = tmp_path / "root"
    catalog.create(root, "Review")
    ws = root / "review"
    shutil.copy2(GOLDEN_PROTOCOL, ws / "protocol.json")
    doubles, clock = Doubles(), Clock()
    monkeypatch.setattr(est, "_provider", doubles)
    monkeypatch.setattr(qw, "utcnow", clock)
    monkeypatch.setattr(settings, "mailto", "console@example.invalid")
    monkeypatch.setattr(settings, "openalex_key", "console-test-key")  # a placeholder, never sent
    draft = DraftStore(root).create({"topic": "weeds", "concepts": FOUR, "pool_max": 400})["session_id"]
    app = create_app(ws, token=TOKEN, workspaces_root=root)
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        yield client, root, ws, draft, doubles, clock


def _url(draft: str, what: str = "counts") -> str:
    return f"/api/v1/inception/drafts/{draft}/workbench/{what}"


def _count(client, draft, *, dry_run=False, concepts=FOUR, providers=("openalex", "semanticscholar", "arxiv"), **extra):
    body = {"version": _version(concepts), "providers": list(providers) if providers is not None else None,
            "dry_run": dry_run, **extra}
    return client.post(_url(draft), json=body)


def _row(answer, name):
    return next(r for r in answer["databases"] if r["name"] == name)


def _code(response) -> str:
    return response.json()["detail"]["code"]


def _log(root: Path, draft: str) -> list[dict]:
    path = qw.draft_log_path(DraftStore(root).dir, draft)
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# --------------------------------------------------------------------------- DoD 4: the dry call, the cost, nothing on a keystroke


def test_the_dry_call_states_the_cost_per_database_and_sends_nothing(env):
    client, root, ws, draft, doubles, _ = env
    answer = _count(client, draft, dry_run=True).json()
    assert doubles.calls == []
    assert answer["cost"] == {"total": 15, "by_database": {"openalex": 5, "semanticscholar": 5, "arxiv": 5}, "cached": False}
    assert answer["query_key"] == "main" and answer["dry_run"] is True and answer["requests"] == 0
    assert all(r["status"] == "to_count" for r in answer["databases"] if r["name"] in ("openalex", "arxiv"))
    assert not qw.draft_log_path(DraftStore(root).dir, draft).exists()


# --------------------------------------------------------------------------- DoD 1, 2: counts, exact strings, drops and gains


def test_a_count_answers_each_database_with_its_exact_string_and_each_concept_left_out(env):
    client, root, ws, draft, doubles, _ = env
    answer = _count(client, draft).json()
    assert doubles.asked() == 15 and answer["requests"] == 15
    oa = _row(answer, "openalex")
    assert (oa["status"], oa["total"], oa["from_cache"]) == ("counted", 166, False)
    assert oa["counted_at"] == "2026-11-21T10:15:00+00:00"
    from scholar_search.plan import _provider as real, translate_provider
    from scholar_search import workbench as wb

    expected = translate_provider(real("openalex"), wb.compile_version(wb.parse_version(_version())))["executed_query"]
    assert oa["string"] == expected and "multispectral" in expected
    drops = {d["concept"]: d for d in oa["drops"]}
    assert drops["UAV"]["total"] == 236 and (drops["UAV"]["gain"], drops["UAV"]["ratio"]) == (70, 1.4)
    assert drops["multispectral"]["total"] == 512 and drops["multispectral"]["ratio"] == 3.1
    assert drops["weed"]["largest"] is True and sum(d["largest"] for d in oa["drops"]) == 1
    assert drops["multispectral"]["string"] and "multispectral" not in drops["multispectral"]["string"]


def test_the_note_is_on_a_concept_whose_absence_at_least_doubles_a_count(env):
    client, root, ws, draft, doubles, _ = env
    answer = _count(client, draft, providers=["openalex"]).json()
    noted = {(n["concept"], n["database"]) for n in answer["notes"]}
    assert ("multispectral", "openalex") in noted and ("weed", "openalex") in noted
    assert ("UAV", "openalex") not in noted  # 236 is less than twice 166
    note = next(n for n in answer["notes"] if n["concept"] == "multispectral")
    assert (note["total"], note["without"]) == (166, 512)


def test_one_concept_has_no_drop_column(env):
    client, root, ws, draft, doubles, _ = env
    answer = _count(client, draft, concepts=[FOUR[2]], providers=["openalex"]).json()
    assert _row(answer, "openalex")["drops"] == [] and doubles.asked() == 1


# --------------------------------------------------------------------------- DoD 5: the count log and its 24 hours


def test_a_repeated_string_is_answered_from_the_log_for_24_hours(env):
    client, root, ws, draft, doubles, clock = env
    _count(client, draft)
    doubles.calls.clear()
    clock.now += timedelta(hours=23)
    dry = _count(client, draft, dry_run=True).json()
    assert dry["cost"]["total"] == 0 and dry["cost"]["cached"] is True
    answer = _count(client, draft).json()
    assert doubles.calls == [] and answer["requests"] == 0
    oa = _row(answer, "openalex")
    assert (oa["status"], oa["from_cache"], oa["counted_at"]) == ("cached", True, "2026-11-21T10:15:00+00:00")
    clock.now += timedelta(hours=2)
    assert _count(client, draft, dry_run=True).json()["cost"]["total"] == 15


def test_a_merge_asks_only_the_strings_not_yet_counted(env):
    client, root, ws, draft, doubles, _ = env
    _count(client, draft, providers=["openalex"])
    doubles.calls.clear()
    merged = _count(client, draft, concepts=THREE, providers=["openalex"], dry_run=True).json()
    # The merged full query and its three drops are strings never asked: four requests.
    assert merged["cost"]["by_database"] == {"openalex": 4}
    edited = [dict(c) for c in FOUR]
    edited[3] = {"concept": "segmentation", "synonyms": ["semantic segmentation", "instance segmentation"]}
    again = _count(client, draft, concepts=edited, providers=["openalex"], dry_run=True).json()
    # Changing one concept changes every string except the one that leaves that concept out.
    assert again["cost"]["by_database"] == {"openalex": 4}
    cell = next(d for d in _row(again, "openalex")["drops"] if d["concept"] == "segmentation")
    assert cell["status"] == "cached" and cell["total"] == 300


def test_every_request_is_a_log_row_and_a_failed_one_never_answers(env):
    client, root, ws, draft, doubles, _ = env
    doubles.fail["semanticscholar"] = ProviderError("semanticscholar", "unavailable", status_code=503)
    answer = _count(client, draft).json()
    ss = _row(answer, "semanticscholar")
    assert ss["status"] == "unavailable" and ss["total"] is None and ss["error_code"] == "PROVIDER_UNAVAILABLE"
    # The first failure stops that database; its other cells are not sent.
    assert doubles.asked("semanticscholar") == 1
    assert all(d["status"] == "unavailable" for d in ss["drops"])
    rows = _log(root, draft)
    assert len(rows) == 11 and {r["query_key"] for r in rows} == {"main"}
    assert [r["status"] for r in rows if r["provider"] == "semanticscholar"] == ["failed"]
    assert {r["draft"] for r in rows} == {draft} and all(r["requests"] == 1 and r["string"] for r in rows)
    del doubles.fail["semanticscholar"]
    assert _count(client, draft, dry_run=True).json()["cost"]["by_database"]["semanticscholar"] == 5


def test_the_log_writes_nothing_in_a_workspace_and_journals_nothing(env):
    client, root, ws, draft, doubles, _ = env
    before = {p: p.stat().st_mtime for p in ws.rglob("*") if p.is_file()}
    _count(client, draft)
    after = {p: p.stat().st_mtime for p in ws.rglob("*") if p.is_file()}
    assert before == after


# --------------------------------------------------------------------------- DoD 4: the budget


def test_a_count_that_would_pass_a_budget_is_refused_before_any_request(env, monkeypatch):
    client, root, ws, draft, doubles, _ = env
    monkeypatch.setitem(qw.BUDGETS, "arxiv", 4)
    _count(client, draft, concepts=[FOUR[2]])  # one request each
    doubles.calls.clear()
    dry = _count(client, draft, concepts=THREE, dry_run=True).json()
    arxiv = _row(dry, "arxiv")
    assert arxiv["status"] == "budget_spent" and "arxiv" not in dry["cost"]["by_database"]
    assert dry["budget"]["arxiv"] == {"limit": 4, "spent": 1, "left": 3, "renews_at": "2026-11-22T00:00:00+00:00", "low": False}
    refused = _count(client, draft, concepts=THREE)
    assert refused.status_code == 409 and _code(refused) == refusals.WORKBENCH_BUDGET_SPENT
    assert refused.json()["detail"]["details"]["databases"][0]["name"] == "arxiv"
    assert doubles.calls == []
    # The other databases can be counted.
    assert _count(client, draft, concepts=THREE, providers=["openalex"]).status_code == 200


def test_the_budget_is_shared_by_drafts_and_the_workspace_and_renews_each_utc_day(env, monkeypatch):
    client, root, ws, draft, doubles, clock = env
    monkeypatch.setitem(qw.BUDGETS, "openalex", 6)
    other = DraftStore(root).create({"concepts": FOUR})["session_id"]
    _count(client, draft, providers=["openalex"])  # 5
    dry = _count(client, other, concepts=THREE, providers=["openalex"], dry_run=True).json()
    assert _row(dry, "openalex")["status"] == "budget_spent"
    plan = client.post("/api/v1/discovery/workbench/counts",
                       json={"version": _version(THREE), "providers": ["openalex"], "dry_run": True}).json()
    assert _row(plan, "openalex")["status"] == "budget_spent" and plan["budget"]["openalex"]["low"] is True
    clock.now = datetime(2026, 11, 22, 0, 1, tzinfo=UTC)
    assert _row(_count(client, other, concepts=THREE, providers=["openalex"], dry_run=True).json(), "openalex")["status"] == "to_count"


# --------------------------------------------------------------------------- DoD 6: a used-up quota is remembered


def test_a_used_up_quota_is_remembered_across_drafts_until_it_resets(env):
    client, root, ws, draft, doubles, clock = env
    doubles.fail["openalex"] = QuotaExhaustedError("openalex", database="OpenAlex", retry_after=20_400,
                                                    resets_at="2026-11-22T00:00:00+00:00")
    answer = _count(client, draft).json()
    oa = _row(answer, "openalex")
    assert oa["status"] == "quota_used_up" and oa["resets_at"] == "2026-11-22T00:00:00+00:00"
    assert oa["resets_in"] == {"hours": 13, "minutes": 45} and oa["error_code"] == "PROVIDER_RATE_LIMITED"
    assert doubles.asked("openalex") == 1
    del doubles.fail["openalex"]
    doubles.calls.clear()
    other = DraftStore(root).create({"concepts": FOUR})["session_id"]
    again = _count(client, other, providers=["openalex"]).json()
    assert doubles.calls == [] and _row(again, "openalex")["status"] == "quota_used_up"
    clock.now = datetime(2026, 11, 22, 0, 0, 1, tzinfo=UTC)
    assert _row(_count(client, other, providers=["openalex"]).json(), "openalex")["status"] == "counted"


def test_the_last_count_is_shown_beside_a_used_up_quota(env):
    client, root, ws, draft, doubles, clock = env
    _count(client, draft, providers=["openalex"])
    clock.now += timedelta(hours=25)
    doubles.fail["openalex"] = QuotaExhaustedError("openalex", database="OpenAlex", retry_after=3600,
                                                    resets_at="2026-11-23T00:00:00+00:00")
    _count(client, draft, providers=["openalex"])
    oa = _row(_count(client, draft, providers=["openalex"], dry_run=True).json(), "openalex")
    assert oa["status"] == "quota_used_up"
    assert oa["last"] == {"total": 166, "counted_at": "2026-11-21T10:15:00+00:00"}


@pytest.mark.parametrize(("error", "status", "http"), [
    (RateLimitExceededError("semanticscholar", "busy"), "rate_limited", 429),
    (ProviderError("semanticscholar", "forbidden", status_code=403), "refused", 403),
    (ProviderError("semanticscholar", "down", status_code=None), "unavailable", None),
    (TimeoutError(), "timeout", None),
])
def test_throttling_refusal_unavailability_and_timeout_keep_their_codes(env, error, status, http):
    client, root, ws, draft, doubles, _ = env
    doubles.fail["semanticscholar"] = error
    ss = _row(_count(client, draft).json(), "semanticscholar")
    assert ss["status"] == status and ss["http_status"] == http and ss["total"] is None


def test_openalex_without_a_key_is_its_row_and_the_others_count(env, monkeypatch):
    client, root, ws, draft, doubles, _ = env
    monkeypatch.setattr(settings, "openalex_key", None)
    answer = _count(client, draft).json()
    assert _row(answer, "openalex")["status"] == "key_missing" and doubles.asked("openalex") == 0
    assert _row(answer, "arxiv")["status"] == "counted"


# --------------------------------------------------------------------------- DoD 7: Crossref


def test_crossref_is_not_counted_for_two_concepts_unless_asked_and_then_only_the_full_query(env):
    client, root, ws, draft, doubles, _ = env
    answer = _count(client, draft, providers=["openalex", "crossref"]).json()
    cr = _row(answer, "crossref")
    assert cr["status"] == "not_comparable" and cr["drops"] == [] and doubles.asked("crossref") == 0
    anyway = _count(client, draft, providers=["openalex", "crossref"], crossref_anyway=True).json()
    cr = _row(anyway, "crossref")
    assert (cr["status"], cr["total"], cr["any_words"]) == ("counted", 6166, True)
    assert cr["drops"] == [] and doubles.asked("crossref") == 1
    assert not any(n["database"] == "crossref" for n in anyway["notes"])
    # Never in the size line's range.
    assert anyway["size"]["estimate"]["records"] == {"low": 166, "high": 166}


def test_crossref_counts_like_any_database_for_one_concept(env):
    client, root, ws, draft, doubles, _ = env
    cr = _row(_count(client, draft, concepts=[FOUR[2]], providers=["crossref"]).json(), "crossref")
    assert cr["status"] == "counted" and cr["any_words"] is False


def test_a_database_not_asked_is_said_and_one_that_cannot_count_is_said(env):
    client, root, ws, draft, doubles, _ = env
    answer = _count(client, draft, providers=["openalex", "biorxiv"]).json()
    assert _row(answer, "biorxiv")["status"] == "not_countable" and doubles.asked("biorxiv") == 0
    assert _row(answer, "semanticscholar")["status"] == "not_asked"


# --------------------------------------------------------------------------- DoD 8: the size line


def test_the_size_line_is_the_estimates_arithmetic_for_the_version(env):
    client, root, ws, draft, doubles, _ = env
    answer = _count(client, draft).json()
    size = answer["size"]
    assert size["estimate"]["records"] == {"low": 280, "high": 280}  # 166 + 107 + 7
    assert size["estimate"]["works"] == {"low": 166, "high": 280}
    assert size["warn"]["limit"] == {"value": 400, "source": "planned"}  # the draft's pool_max
    assert size["effort"]["pace_seconds"] == est.DEFAULT_PACE_SECONDS


# --------------------------------------------------------------------------- DoD 3: what each synonym adds


def test_what_each_synonym_adds_states_its_requests_and_answers_gains(env):
    client, root, ws, draft, doubles, _ = env
    doubles.total = lambda name, text: 166 if "multi-spectral" in text else 150
    body = {"version": _version(), "concept_index": 1, "provider": "openalex", "dry_run": True}
    dry = client.post(_url(draft, "synonyms"), json=body).json()
    assert dry["cost"]["by_database"] == {"openalex": 3} and doubles.calls == []
    answer = client.post(_url(draft, "synonyms"), json=body | {"dry_run": False}).json()
    terms = {s["term"]: s for s in _row(answer, "openalex")["synonyms"]}
    assert (terms["multispectral"]["total"], terms["multispectral"]["gain"], terms["multispectral"]["adds_nothing"]) == (166, 0, True)
    assert (terms["multi-spectral"]["total"], terms["multi-spectral"]["gain"]) == (150, 16)
    assert answer["query_key"] == "main" and answer["concept_index"] == 1


# --------------------------------------------------------------------------- read what a concept removes


def test_reading_what_a_concept_removes_is_one_request_and_drops_what_the_full_query_matches(env):
    client, root, ws, draft, doubles, _ = env
    doubles.docs = [
        Document(title="Weed segmentation from UAV multispectral images", external_ids=ExternalIds(doi="10.1/a")),
        Document(title="Weeds segmentation in UAV RGB imagery", abstract="", external_ids=ExternalIds(doi="10.1/b")),
    ]
    body = {"version": _version(), "concept_index": 1, "dry_run": True}
    dry = client.post(_url(draft, "removed"), json=body).json()
    assert dry["cost"] == 1 and doubles.calls == []
    answer = client.post(_url(draft, "removed"), json=body | {"dry_run": False}).json()
    assert answer["requests"] == 1 and doubles.asked("openalex") == 1 and answer["read"] == 2
    assert [(r["doi"], r["lacks"]) for r in answer["records"]] == [("10.1/b", ["multispectral"])]
    assert _log(root, draft)[-1]["kind"] == "removed"


# --------------------------------------------------------------------------- refusals


def test_a_version_with_no_concept_is_refused(env):
    client, root, ws, draft, doubles, _ = env
    response = _count(client, draft, concepts=[{"concept": " ", "synonyms": []}])
    assert response.status_code == 422 and _code(response) == refusals.WORKBENCH_VERSION_INVALID
    assert doubles.calls == []


def test_a_real_count_needs_the_contact_email_and_no_running_job(env, monkeypatch):
    client, root, ws, draft, doubles, _ = env
    monkeypatch.setattr(settings, "mailto", None)
    assert _count(client, draft, dry_run=True).json()["mailto_set"] is False
    assert _code(_count(client, draft)) == refusals.MAILTO_NOT_SET
    monkeypatch.setattr(settings, "mailto", "console@example.invalid")
    from scholar_harness.console.api import discovery as disc_api

    jobs = disc_api.DiscoveryJobs()
    jobs.jobs["djob_1"] = disc_api.DiscoveryJob("djob_1", str(client.app.state.workspace), "run")
    client.app.state.discovery_jobs = jobs
    response = _count(client, draft)
    assert response.status_code == 409 and _code(response) == refusals.DISCOVERY_JOB_ACTIVE
    assert _count(client, draft, dry_run=True).status_code == 200
    assert doubles.calls == []


def test_an_emitted_or_unknown_draft_is_refused(env):
    client, root, ws, draft, doubles, _ = env
    assert _code(client.post(_url("rec_" + "0" * 32), json={"version": _version()})) == "DRAFT_NOT_FOUND"
    store = DraftStore(root)
    store.update_side(draft, "emitted", lambda _old: {"slug": "review"})
    assert _code(_count(client, draft)) == "DRAFT_EMITTED"


def test_the_refusal_codes_are_the_engines():
    assert qw.WORKBENCH_BUDGET_SPENT == refusals.WORKBENCH_BUDGET_SPENT
    assert qw.WORKBENCH_VERSION_INVALID == refusals.WORKBENCH_VERSION_INVALID
    assert {refusals.WORKBENCH_BUDGET_SPENT, refusals.WORKBENCH_VERSION_INVALID} <= refusals.CONTRACT_ADDED


# --------------------------------------------------------------------------- Plan: the workspace route, the estimate reads the log


def test_on_plan_the_log_is_under_audit_and_the_estimate_reuses_it(env):
    client, root, ws, draft, doubles, _ = env
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    strategy = protocol["search_strategy"]
    version = {"query_key": "main",
               "concepts": [{"concept": c["concept"], "synonyms": c.get("synonyms", [])} for c in strategy["core_concepts"]],
               "start_year": strategy["date_range"]["start_year"], "end_year": strategy["date_range"]["end_year"],
               "languages": strategy.get("languages") or ["en"]}
    answer = client.post("/api/v1/discovery/workbench/counts",
                         json={"version": version, "providers": ["openalex", "arxiv"]}).json()
    assert _row(answer, "openalex")["status"] == "counted"
    log = qw.workspace_log_path(ws)
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert rows and {r["workspace"] for r in rows} == {ws.name} and all(r["protocol_fingerprint"] for r in rows)
    doubles.calls.clear()
    estimate = client.post("/api/v1/discovery/estimate", json={"providers": ["openalex", "arxiv"]}).json()
    assert doubles.calls == []
    oa = next(r for r in estimate["providers"] if r["name"] == "openalex")
    assert oa["status"] == "counted" and oa["from_count_log"] == "2026-11-21T10:15:00+00:00"


def test_counting_on_plan_still_works_after_the_corpus_is_accepted(env, monkeypatch):
    client, root, ws, draft, doubles, _ = env
    from scholar_harness.console.api import discovery as disc_api

    monkeypatch.setattr(disc_api, "_frozen", lambda _ws: True)
    response = client.post("/api/v1/discovery/workbench/counts",
                           json={"version": _version(), "providers": ["openalex"]})
    assert response.status_code == 200 and _row(response.json(), "openalex")["status"] == "counted"


# --------------------------------------------------------------------------- the routes in both allow-lists


ROUTES = [
    "api/v1/inception/drafts/rec_0123abcd/workbench/counts",
    "api/v1/inception/drafts/rec_0123abcd/workbench/synonyms",
    "api/v1/inception/drafts/rec_0123abcd/workbench/removed",
    "api/v1/discovery/workbench/counts",
    "api/v1/discovery/workbench/synonyms",
    "api/v1/discovery/workbench/removed",
]


@pytest.mark.parametrize("path", ROUTES)
def test_each_route_is_in_the_browser_allow_list_and_the_proxy_and_not_a_phone_route(path):
    from scholar_harness.console import serve

    assert any(p.fullmatch(path) for p in browser.POST_PATHS)
    patterns = [re.compile(m.group(1).replace("\\/", "/")) for m in re.finditer(r"^\s*/(\^api.*\$)/,", PROXY.read_text(encoding="utf-8"), re.M)]
    assert any(p.fullmatch(path) for p in patterns)
    assert not serve._phone_may_reach("POST", "/" + path)
