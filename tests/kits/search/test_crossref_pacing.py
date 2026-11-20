"""H-run-small-fixes Part B, finding 14: a throttled host is paced, not hit again at full speed.

In the acceptance run of 2026-11-20 the per-record check was answered 429 by
Crossref on almost every record, each followed by one retry. The client
waited out each 429 and then went on at the configured single-record rate
(10 per second polite), so the next record met the same limit. A 429 that
carries no lower rate header now halves the host's shared budget (never below
one request per second), so the retries stop once the pace fits.

Offline: a fake Crossref answers 429 to any request that arrives less than
`GAP` seconds after the previous one it accepted. Whether this matches the
real Crossref limit was not checked (no live calls).
"""

from __future__ import annotations

import asyncio
import time

import httpx
import pytest

from scholar_search import http_client as http_mod
from scholar_search.config import settings
from scholar_search.http_client import AcademicHttpClient, crossref_rate

SINGLE = "https://api.crossref.org/works/10.1000/x"
GAP = 0.15  # the fake allows about 6.7 requests per second; the client starts at 10


@pytest.fixture(autouse=True)
def _fresh(monkeypatch):
    monkeypatch.setattr(settings, "mailto", "tester@example.org")
    monkeypatch.setattr(settings, "http_cache", False)
    http_mod.reset_host_budgets()
    yield
    http_mod.reset_host_budgets()


def _fake_crossref() -> tuple[httpx.MockTransport, dict[str, int]]:
    state = {"last": 0.0, "ok": 0, "throttled": 0}

    def handle(request: httpx.Request) -> httpx.Response:
        now = time.monotonic()
        if state["last"] and now - state["last"] < GAP:
            state["throttled"] += 1
            return httpx.Response(429)  # no Retry-After, no rate headers
        state["last"] = now
        state["ok"] += 1
        return httpx.Response(200, json={"message": {}})

    return httpx.MockTransport(handle), state


async def _lookups(n: int) -> dict[str, int]:
    client = AcademicHttpClient(name="crossref", rate_limit=crossref_rate(single=True), base_delay=0.2)
    transport, state = _fake_crossref()
    client.client = httpx.AsyncClient(transport=transport, headers=client.client.headers)
    for _ in range(n):
        response = await client.get(SINGLE)
        assert response.status_code == 200
    await client.client.aclose()
    return state


def test_finding_14_after_a_throttle_the_lookups_are_paced_and_stop_being_retried():
    state = asyncio.run(_lookups(20))
    assert state["ok"] == 20
    # Before: about one 429 per lookup (the pace went back to 10 per second after each wait).
    # After: the first throttles halve the budget, then the pace fits.
    assert state["throttled"] <= 3, state


def test_a_throttle_never_paces_a_host_below_one_request_per_second(monkeypatch):
    monkeypatch.setattr(http_mod, "THROTTLE_DEBOUNCE_S", 0.0)
    url = SINGLE
    budget = http_mod.host_budget(url)
    for _ in range(20):
        http_mod.slow_down(url)
    assert http_mod.host_budget(url).rate == pytest.approx(1.0)
    assert budget is http_mod.host_budget(url)


def test_a_host_without_a_shared_budget_is_not_paced():
    assert http_mod.slow_down("https://example.org/x") is False



def test_a_burst_of_429s_halves_the_pace_once():
    """Concurrent requests answered 429 together are one throttle (review follow-up)."""
    for _ in range(4):
        http_mod.slow_down(SINGLE)
    assert http_mod.host_budget(SINGLE).rate == pytest.approx(crossref_rate(single=True) / 2)


def test_the_pace_set_by_a_429_expires(monkeypatch):
    """A long-running console is not left slow after one throttled burst (review follow-up)."""
    http_mod.slow_down(SINGLE)
    assert http_mod.host_budget(SINGLE).rate < crossref_rate(single=True)
    monkeypatch.setattr(http_mod, "THROTTLE_HOLD_S", 0.0)
    assert http_mod.host_budget(SINGLE).rate == pytest.approx(crossref_rate(single=True))



def test_a_lower_header_rate_is_kept_while_a_429_pace_holds(monkeypatch):
    """Review follow-up: a header seen during a held pace is recorded, so it survives the pace's expiry."""
    client = AcademicHttpClient(name="crossref", rate_limit=crossref_rate(single=True))
    http_mod.slow_down(SINGLE)  # pace 5 per second, held
    client._read_rate_headers(SINGLE, httpx.Response(200, headers={"x-rate-limit-limit": "8", "x-rate-limit-interval": "1s"}))
    monkeypatch.setattr(http_mod, "THROTTLE_HOLD_S", 0.0)
    assert http_mod.host_budget(SINGLE).rate == pytest.approx(8.0)
