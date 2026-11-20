"""M10b Part D: the size estimate before a harvest (`POST /discovery/estimate`).

Spec `docs/ux/phase1-discovery/final/01-plan.md` "Size estimate (M10b)". Hermetic:
the providers the estimate counts are doubles (``scholar_search.estimate._provider``
is replaced), so nothing reaches the network; the arithmetic is tested on its
own (``scholar_search.estimate.summarize``) and through the route.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from scholar_search import estimate as est
from scholar_search.config import settings
from scholar_search.exceptions import ProviderError

from scholar_harness.console import create_app
from scholar_harness.console import refusals
from scholar_harness.workspace import catalog

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_PROTOCOL = ROOT / "workspaces" / "golden-uav-30" / "protocol.json"
TOKEN = "desk-token"
URL = "/api/v1/discovery/estimate"
PROTOCOL_DBS = ["openalex", "semanticscholar", "crossref", "arxiv", "pubmed"]


class CountingProvider:
    """A provider double: ``count`` answers a fixed total, or raises, and records each call."""

    def __init__(self, name: str, total: int | None = 100, fail: Exception | None = None, countable: bool = True):
        self.name, self.total, self.fail, self.countable = name, total, fail, countable
        self.calls: list[str] = []
        self.client = None

    async def count(self, query):
        self.calls.append(query.text)
        if not self.countable:
            raise NotImplementedError(f"{self.name} does not report how many records match")
        if self.fail is not None:
            raise self.fail
        return self.total

    async def search(self, query):  # pragma: no cover - a count never searches
        raise AssertionError("a count must not fetch records")
        yield


class Doubles:
    def __init__(self):
        self.totals: dict[str, int | None] = {name: 100 for name in [*PROTOCOL_DBS, "biorxiv"]}
        self.fail: dict[str, Exception] = {}
        self.made: list[CountingProvider] = []

    def __call__(self, name: str) -> CountingProvider:
        provider = CountingProvider(name, self.totals.get(name), self.fail.get(name), countable=name != "biorxiv")
        self.made.append(provider)
        return provider

    def asked(self) -> list[str]:
        return [p.name for p in self.made if p.calls]


@pytest.fixture
def env(tmp_path, monkeypatch):
    root = tmp_path / "root"
    catalog.create(root, "Review")
    ws = root / "review"
    shutil.copy2(GOLDEN_PROTOCOL, ws / "protocol.json")
    doubles = Doubles()
    monkeypatch.setattr(est, "_provider", doubles)
    monkeypatch.setattr(settings, "mailto", "console@example.invalid")
    monkeypatch.setattr(settings, "openalex_key", "console-test-key")  # a placeholder, never sent
    app = create_app(ws, token=TOKEN, workspaces_root=root)
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        yield client, ws, doubles


def _code(response) -> str:
    return response.json()["detail"]["code"]


def _files(ws: Path) -> dict[str, float]:
    return {str(p.relative_to(ws)): p.stat().st_mtime for p in ws.rglob("*") if p.is_file()}


def _row(answer: dict, name: str) -> dict:
    return next(r for r in answer["providers"] if r["name"] == name)


# --------------------------------------------------------------------------- the arithmetic


def _rows(totals: dict[str, int | None], status: str = "counted") -> list[dict]:
    return [{"name": n, "status": status if t is not None else "failed", "reported_total": t} for n, t in totals.items()]


def test_each_database_fetches_at_most_the_cap_and_says_whether_the_cap_binds():
    answer = est.summarize(_rows({"openalex": 700, "crossref": 300}), cap=500, limit=1000, pace_seconds=30, year_window=True)
    oa, cr = answer["providers"]
    assert (oa["fetch_estimate"], oa["cap_binds"], oa["not_fetched"]) == (500, True, 200)
    assert (cr["fetch_estimate"], cr["cap_binds"], cr["not_fetched"]) == (300, False, 0)


def test_works_range_is_the_largest_database_to_the_sum():
    answer = est.summarize(_rows({"openalex": 400, "crossref": 300, "pubmed": 50}), cap=10_000, limit=1000, pace_seconds=30, year_window=True)
    assert answer["estimate"]["records"] == {"low": 750, "high": 750}
    assert answer["estimate"]["works"] == {"low": 400, "high": 750}
    assert answer["estimate"]["counted_all"] is True


def test_decision_2026_11_20_item_2_arxiv_with_a_year_window_is_counted_exactly():
    """Since M3h-c arXiv applies the year window itself, so its count is exact (no "upper limit")."""
    answer = est.summarize(_rows({"openalex": 300, "arxiv": 900}), cap=10_000, limit=1000, pace_seconds=30, year_window=True)
    assert _row(answer, "arxiv")["fetch_is_upper_bound"] is False
    assert _row(answer, "openalex")["fetch_is_upper_bound"] is False
    assert answer["estimate"]["records"] == {"low": 1200, "high": 1200}
    assert answer["estimate"]["works"] == {"low": 900, "high": 1200}


def test_arxiv_without_a_year_window_is_counted_exactly():
    answer = est.summarize(_rows({"openalex": 300, "arxiv": 900}), cap=10_000, limit=1000, pace_seconds=30, year_window=False)
    assert _row(answer, "arxiv")["fetch_is_upper_bound"] is False
    assert answer["estimate"]["works"] == {"low": 900, "high": 1200}


@pytest.mark.parametrize("status", ["failed", "not_countable"])
def test_a_database_not_counted_leaves_the_upper_end_unknown(status):
    rows = _rows({"openalex": 400}) + [{"name": "crossref", "status": status, "reported_total": None}]
    answer = est.summarize(rows, cap=10_000, limit=1000, pace_seconds=30, year_window=True)
    assert answer["estimate"]["counted_all"] is False
    assert answer["estimate"]["records"] == {"low": 400, "high": None}
    assert answer["estimate"]["works"] == {"low": 400, "high": None}
    assert answer["effort"]["hours"]["high"] is None
    assert _row(answer, "crossref")["fetch_estimate"] is None
    # The size cannot be bounded: a note, and narrowing, never a cap that cannot be promised.
    assert answer["warn"]["level"] == "note"
    assert answer["recommendation"]["kind"] == "narrow" and answer["recommendation"]["cap"] is None


def test_the_hours_are_works_times_the_pace_for_one_reviewer():
    answer = est.summarize(_rows({"openalex": 360, "crossref": 360}), cap=10_000, limit=1000, pace_seconds=60, year_window=True)
    assert answer["effort"] == {"pace_seconds": 60, "hours": {"low": 6.0, "high": 12.0}}


@pytest.mark.parametrize(
    ("totals", "level"),
    [
        ({"openalex": 1001, "crossref": 10}, "warning"),  # the low end is over
        ({"openalex": 1000, "crossref": 10}, "note"),  # only the high end is over
        ({"openalex": 600, "crossref": 400}, "none"),  # neither (the limit itself is not over)
    ],
)
def test_the_warning_level_at_its_boundaries(totals, level):
    answer = est.summarize(_rows(totals), cap=10_000, limit=1000, pace_seconds=30, year_window=True)
    assert answer["warn"]["level"] == level
    assert answer["warn"]["threshold_works"] == 1000
    if level == "none":
        assert answer["recommendation"] == {"kind": None, "cap": None, "expected_works": None, "cuts": None}


def test_the_suggested_cap_is_the_largest_that_keeps_the_sum_at_the_limit():
    """No database holds most of the records: 3,000, 3,000 and 100 against 1,000 give 450."""
    answer = est.summarize(_rows({"openalex": 3000, "crossref": 3000, "pubmed": 100}), cap=10_000, limit=1000, pace_seconds=30, year_window=True)
    rec = answer["recommendation"]
    assert rec["kind"] == "cap" and rec["cap"] == 450
    assert rec["expected_works"] == {"low": 450, "high": 1000}
    assert rec["cuts"] == 2


def test_finding_10_a_cap_that_would_trim_one_database_is_not_offered():
    """The spec's earlier example (5,000, 400, 100 against 1,000) offered "500 per
    database": it trims only the large database, keeps its first 500 records (not
    the most relevant) and every record of the others. When one database is the
    size, the estimate names it instead (finding 10: Crossref 6,221 beside 166)."""
    answer = est.summarize(_rows({"openalex": 5000, "crossref": 400, "pubmed": 100}), cap=10_000, limit=1000, pace_seconds=30, year_window=True)
    rec = answer["recommendation"]
    assert rec["kind"] == "one_database"
    assert rec["provider"] == "openalex" and rec["provider_total"] == 5000 and rec["others_total"] == 500
    assert rec["cap"] is None


@pytest.mark.parametrize("cap", [10_000, 1000])
def test_finding_10_the_acceptance_run_numbers(cap):
    """Judged on the reported totals, so a cap in force (1,000) does not bring the cap advice back (review P2)."""
    answer = est.summarize(_rows({"openalex": 781, "semanticscholar": 539, "crossref": 6221, "arxiv": 30}),
                           cap=cap, limit=2000, pace_seconds=30, year_window=True)
    rec = answer["recommendation"]
    assert rec["kind"] == "one_database" and rec["provider"] == "crossref" and rec["cap"] is None
    assert (rec["provider_total"], rec["others_total"]) == (6221, 1350)


def test_two_large_databases_where_one_is_slightly_larger_is_still_named():
    """1,500 against 1,400: the rule is "more than all the others together"; the copy no longer
    claims a cap would trim only that one (it would trim both here)."""
    answer = est.summarize(_rows({"openalex": 1500, "semanticscholar": 1400}), cap=10_000, limit=1000, pace_seconds=30, year_window=True)
    assert answer["recommendation"]["kind"] == "one_database"
    even = est.summarize(_rows({"openalex": 1400, "semanticscholar": 1400}), cap=10_000, limit=1000, pace_seconds=30, year_window=True)
    assert even["recommendation"]["kind"] == "cap"


def test_narrowing_is_advised_when_the_needed_cap_is_under_100():
    answer = est.summarize(_rows({"openalex": 5000, "crossref": 5000, "pubmed": 5000, "arxiv": 5000, "semanticscholar": 5000,
                                  }), cap=10_000, limit=300, pace_seconds=30, year_window=False)
    assert answer["recommendation"]["kind"] == "narrow"


# --------------------------------------------------------------------------- the route


def test_the_estimate_counts_the_protocols_databases_and_writes_nothing(env):
    client, ws, doubles = env
    doubles.totals.update({"openalex": 5000, "semanticscholar": 400, "crossref": 100, "arxiv": 50, "pubmed": 10})
    before = _files(ws)

    response = client.post(URL, json={})

    assert response.status_code == 200, response.text
    answer = response.json()
    assert answer["shape"] == "discovery.estimate-v1"
    assert answer["served_from_cache"] is False and answer["counted_at"]
    assert answer["protocol_fingerprint"] == client.get("/api/v1/discovery/plan").json()["protocol_fingerprint"]
    assert sorted(doubles.asked()) == sorted(PROTOCOL_DBS)
    assert [r["name"] for r in answer["providers"] if r["status"] == "counted"] == PROTOCOL_DBS
    assert _row(answer, "biorxiv")["status"] == "off_by_default"
    assert answer["cap"] == {"value": 10_000, "source": "engine_ceiling", "ceiling": 10_000}
    assert answer["effort"]["pace_seconds"] == 30
    # Nothing written, nothing journaled.
    assert _files(ws) == before


def test_the_count_uses_the_protocol_query_the_plan_shows(env):
    client, _ws, doubles = env
    client.post(URL, json={})
    text = client.get("/api/v1/discovery/plan").json()["query"]["text"]
    assert all(p.calls == [text] for p in doubles.made if p.calls)


def test_a_chosen_list_is_counted_in_place_of_the_protocols(env):
    client, _ws, doubles = env
    answer = client.post(URL, json={"providers": ["crossref", "pubmed"]}).json()
    assert sorted(doubles.asked()) == ["crossref", "pubmed"]
    assert [r["name"] for r in answer["providers"]][:2] == ["crossref", "pubmed"]
    assert _row(answer, "openalex")["status"] == "not_selected"


def test_a_what_if_cap_is_a_run_override(env):
    client, _ws, doubles = env
    doubles.totals["openalex"] = 700
    answer = client.post(URL, json={"cap": 500}).json()
    assert answer["cap"]["source"] == "run_override" and answer["cap"]["value"] == 500
    assert _row(answer, "openalex")["cap_binds"] is True and _row(answer, "openalex")["fetch_estimate"] == 500


def test_a_failed_database_is_its_row_not_the_call(env):
    client, _ws, doubles = env
    doubles.fail["semanticscholar"] = ProviderError("semanticscholar", "slow down", status_code=429)
    answer = client.post(URL, json={}).json()
    row = _row(answer, "semanticscholar")
    assert row["status"] == "failed" and row["error_code"] == "PROVIDER_RATE_LIMITED" and "slow down" in row["error"]
    assert row["reported_total"] is None and row["fetch_estimate"] is None
    assert answer["estimate"]["records"]["high"] is None


def test_biorxiv_selected_is_not_countable(env):
    client, _ws, _doubles = env
    answer = client.post(URL, json={"providers": ["crossref", "biorxiv"]}).json()
    assert _row(answer, "biorxiv")["status"] == "not_countable"
    assert answer["estimate"]["counted_all"] is False


def test_a_second_call_is_answered_from_the_cache_without_a_request(env):
    client, _ws, doubles = env
    client.post(URL, json={})
    asked = len(doubles.asked())
    again = client.post(URL, json={"cap": 50, "pace_seconds": 60}).json()
    assert again["served_from_cache"] is True
    assert len(doubles.asked()) == asked  # no new request
    assert again["effort"]["pace_seconds"] == 60 and again["cap"]["value"] == 50


def test_a_changed_provider_list_does_not_hit_the_cache(env):
    client, _ws, doubles = env
    client.post(URL, json={"providers": ["crossref", "pubmed"]})
    answer = client.post(URL, json={"providers": ["crossref"]}).json()
    assert answer["served_from_cache"] is False
    # The order has no effect on the estimate, so it shares the cache.
    client.post(URL, json={"providers": ["pubmed", "crossref"]})
    assert client.post(URL, json={"providers": ["crossref", "pubmed"]}).json()["served_from_cache"] is True


def test_a_changed_protocol_does_not_hit_the_cache(env):
    client, ws, _doubles = env
    first = client.post(URL, json={}).json()
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    protocol["search_strategy"]["date_range"]["start_year"] = 2019
    (ws / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    second = client.post(URL, json={}).json()
    assert second["served_from_cache"] is False
    assert second["protocol_fingerprint"] != first["protocol_fingerprint"]


def test_only_the_failed_databases_are_asked_again(env):
    client, _ws, doubles = env
    doubles.fail["crossref"] = ProviderError("crossref", "down", status_code=503)
    client.post(URL, json={})
    doubles.fail.clear()
    doubles.made.clear()
    answer = client.post(URL, json={}).json()
    assert doubles.asked() == ["crossref"]
    assert _row(answer, "crossref")["status"] == "counted"
    assert answer["served_from_cache"] is False


def test_the_cache_expires(env, monkeypatch):
    from scholar_harness.console.api import discovery as api

    client, _ws, doubles = env
    now = [1000.0]
    monkeypatch.setattr(api, "_monotonic", lambda: now[0])
    client.post(URL, json={})
    now[0] += est.ESTIMATE_TTL + 1
    assert client.post(URL, json={}).json()["served_from_cache"] is False


def _write_check(ws: Path, fingerprint: str, legs: list[dict], number: int = 1) -> None:
    root = ws / "literature" / "recall_checks"
    root.mkdir(parents=True, exist_ok=True)
    (root / f"check_{number:03d}.json").write_text(json.dumps({
        "shape": "discovery.recall-v1", "protocol_fingerprint": fingerprint, "checked_at": "2026-11-17T10:00:00+00:00",
        "legs": legs, "seeds": [], "found": 0, "total": 0, "missed_everywhere": [],
    }), encoding="utf-8")


def test_a_recall_check_for_this_protocol_gives_its_totals_without_a_request(env):
    client, ws, doubles = env
    fingerprint = client.get("/api/v1/discovery/plan").json()["protocol_fingerprint"]
    legs = [{"provider": n, "status": "complete", "reported_total": 222} for n in PROTOCOL_DBS if n != "pubmed"]
    legs.append({"provider": "pubmed", "status": "failed", "reported_total": None})
    _write_check(ws, fingerprint, legs)

    answer = client.post(URL, json={}).json()

    assert doubles.asked() == ["pubmed"]  # only what the check could not say
    assert _row(answer, "crossref")["status"] == "from_recall_check" and _row(answer, "crossref")["reported_total"] == 222
    assert _row(answer, "pubmed")["status"] == "counted"
    assert answer["recall_check"] == {"check": "check_001", "checked_at": "2026-11-17T10:00:00+00:00"}


def test_a_recall_check_is_skipped_on_refresh(env):
    client, ws, doubles = env
    fingerprint = client.get("/api/v1/discovery/plan").json()["protocol_fingerprint"]
    _write_check(ws, fingerprint, [{"provider": n, "status": "complete", "reported_total": 222} for n in PROTOCOL_DBS])
    assert client.post(URL, json={}).json()["recall_check"] is not None
    answer = client.post(URL, json={"refresh": True}).json()
    assert sorted(doubles.asked()) == sorted(PROTOCOL_DBS)
    assert answer["recall_check"] is None and answer["served_from_cache"] is False


def test_a_recall_check_for_another_protocol_is_ignored(env):
    client, ws, doubles = env
    _write_check(ws, "another-fingerprint", [{"provider": n, "status": "complete", "reported_total": 222} for n in PROTOCOL_DBS])
    answer = client.post(URL, json={}).json()
    assert sorted(doubles.asked()) == sorted(PROTOCOL_DBS)
    assert answer["recall_check"] is None


# --------------------------------------------------------------------------- the size limit


def _intent(ws: Path, pool_max: int | None) -> None:
    (ws / "intent.json").write_text(json.dumps({"pool_min": 150 if pool_max else None, "pool_max": pool_max}), encoding="utf-8")


def test_the_limit_is_the_planned_maximum_when_stated(env):
    client, ws, doubles = env
    _intent(ws, 300)
    doubles.totals.update(dict.fromkeys(PROTOCOL_DBS, 400))
    answer = client.post(URL, json={}).json()
    assert answer["warn"]["limit"] == {"value": 300, "source": "planned"}
    assert answer["warn"]["threshold_works"] == 300
    assert answer["warn"]["level"] == "warning"


@pytest.mark.parametrize("pool_max", [None, "absent"])
def test_the_limit_is_1000_when_no_plan_is_stated(env, pool_max):
    client, ws, _doubles = env
    if pool_max is None:
        _intent(ws, None)
    else:
        (ws / "intent.json").unlink(missing_ok=True)
    answer = client.post(URL, json={}).json()
    assert answer["warn"]["limit"] == {"value": 1000, "source": "general"}


# --------------------------------------------------------------------------- refusals before any request


def test_refusals_are_registered():
    assert refusals.PACE_INVALID in refusals.CONSOLE_REFUSALS


@pytest.mark.parametrize(
    ("body", "setup", "status", "code"),
    [
        ({}, "no_mailto", 409, "MAILTO_NOT_SET"),
        ({}, "no_openalex_key", 409, "OPENALEX_KEY_NOT_SET"),
        ({"providers": ["scopus"]}, None, 422, "PROVIDER_UNKNOWN"),
        ({"cap": 0}, None, 422, "CAP_INVALID"),
        ({"cap": 10_001}, None, 422, "CAP_INVALID"),
        ({"pace_seconds": 4}, None, 422, "PACE_INVALID"),
        ({"pace_seconds": 601}, None, 422, "PACE_INVALID"),
        ({}, "busy", 409, "DISCOVERY_JOB_ACTIVE"),
        ({}, "accepted", 409, "CORPUS_ALREADY_ACCEPTED"),
        ({}, "no_protocol", 409, "PROTOCOL_MISSING"),
    ],
)
def test_a_refused_estimate_sends_no_request(env, monkeypatch, body, setup, status, code):
    from scholar_harness import corpus_accept
    from scholar_harness.console.api import discovery as api

    client, ws, doubles = env
    if setup == "no_mailto":
        monkeypatch.setattr(settings, "mailto", None)
    elif setup == "no_openalex_key":
        monkeypatch.setattr(settings, "openalex_key", None)
    elif setup == "busy":
        class _Busy:
            def to_dict(self):
                return {"job_id": "j1", "kind": "run"}

        monkeypatch.setattr(api.DiscoveryJobs, "active", lambda self, _ws: _Busy())
    elif setup == "accepted":
        monkeypatch.setattr(corpus_accept, "_accepted_snapshot", lambda _ws: {"snapshot": "x"})
    elif setup == "no_protocol":
        (ws / "protocol.json").unlink()

    response = client.post(URL, json=body)

    assert response.status_code == status, response.text
    assert _code(response) == code
    assert doubles.asked() == []


def test_without_openalex_the_key_is_not_needed(env, monkeypatch):
    client, _ws, _doubles = env
    monkeypatch.setattr(settings, "openalex_key", None)
    assert client.post(URL, json={"providers": ["crossref"]}).status_code == 200


def test_an_unknown_field_is_refused(env):
    client, _ws, doubles = env
    response = client.post(URL, json={"cap_override": 5})
    assert response.status_code == 422
    assert doubles.asked() == []


def test_the_estimate_is_in_both_post_allow_lists():
    from scholar_harness.console.browser import POST_PATHS

    assert any(p.fullmatch("api/v1/discovery/estimate") for p in POST_PATHS)
    assert not any(p.fullmatch("api/v1/discovery/estimate/x") for p in POST_PATHS)
    # The proxy's list equals the console's (tests/console/test_browser_access.py).


def test_a_database_that_does_not_answer_in_time_is_its_row_not_the_call(env, monkeypatch):
    """Review finding 1: a count that retries a 429 for minutes must not time the whole call out at the proxy."""
    import asyncio

    client, _ws, doubles = env
    monkeypatch.setattr(est, "COUNT_TIMEOUT", 0.2)

    class _Hanging(CountingProvider):
        async def count(self, query):
            self.calls.append(query.text)
            await asyncio.sleep(30)

    make = doubles.__call__

    def provider(name):
        if name == "semanticscholar":
            hanging = _Hanging(name)
            doubles.made.append(hanging)
            return hanging
        return make(name)

    monkeypatch.setattr(est, "_provider", provider)
    answer = client.post(URL, json={}).json()
    row = _row(answer, "semanticscholar")
    assert row["status"] == "failed" and row["error_code"] == "PROVIDER_TIMEOUT"
    assert _row(answer, "crossref")["status"] == "counted"


def test_asking_a_failed_database_again_keeps_the_first_count_time(env):
    """Review finding 3: the rows counted first are not shown as counted at the retry."""
    client, _ws, doubles = env
    doubles.fail["crossref"] = ProviderError("crossref", "down", status_code=503)
    first = client.post(URL, json={}).json()
    doubles.fail.clear()
    second = client.post(URL, json={}).json()
    assert _row(second, "crossref")["status"] == "counted"
    assert second["counted_at"] == first["counted_at"]



def test_review_an_estimate_sent_no_list_counts_the_default_choice(env):
    """H-run-small-fixes review P1: the card must not count a database the harvest leaves out."""
    import json as _json

    client, ws, doubles = env
    data = _json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    data["search_strategy"]["target_databases"] = ["openalex", "semanticscholar", "crossref", "arxiv"]
    (ws / "protocol.json").write_text(_json.dumps(data), encoding="utf-8")
    answer = client.post(URL, json={}).json()
    assert "crossref" not in doubles.asked()
    assert next(r for r in answer["providers"] if r["name"] == "crossref")["status"] == "not_selected"
