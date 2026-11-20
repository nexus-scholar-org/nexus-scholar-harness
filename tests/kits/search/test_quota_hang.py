"""H-quota-hang: a provider's used-up quota ends the request and the checks, never hours of retries.

The finding (acceptance run, 2026-11-20, findings 12, 15 and 16): OpenAlex
answered HTTP 429 with ``Retry-After: 50000`` (its daily quota) while the
harvest's "Checks" step (``DocumentVerifier.process_batch``) asked it once per
record. ``AcademicHttpClient.get`` retried each request three times, sleeping
``min(Retry-After, 60)`` each time, so 166 records cost about nine hours, and
the researcher's stop was read only between stages.

Offline: every request goes to an ``httpx.MockTransport`` double, and the
client's ``asyncio.sleep`` is replaced by a recorder, so a test measures the
time the client *would* have slept instead of sleeping it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from scholar_search import http_client as http_mod
from scholar_search.config import settings
from scholar_search.exceptions import (
    ProviderError,
    RateLimitExceededError,
)
from scholar_search.http_client import AcademicHttpClient
from scholar_search.models import Document, ExternalIds
from scholar_search.providers.crossref import CrossrefProvider
from scholar_search.providers.openalex import OpenAlexProvider
from scholar_search.verifier import DocumentVerifier

QUOTA_WAIT = "50000"  # what OpenAlex sent on 2026-11-20: about 14 hours


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setattr(settings, "mailto", "tester@example.org")
    monkeypatch.setattr(settings, "http_cache", False)
    monkeypatch.setattr(settings, "openalex_key", None)
    http_mod.reset_host_budgets()
    yield
    http_mod.reset_host_budgets()


@pytest.fixture
def slept(monkeypatch) -> list[float]:
    """Every sleep the HTTP client asks for, recorded and not slept.

    The shared per-host budgets are switched off here: their waits use the same
    ``asyncio.sleep`` and are not what these tests measure.
    """
    seen: list[float] = []
    monkeypatch.setattr(http_mod, "host_budget", lambda url: None)

    async def record(delay: float, *args, **kwargs) -> None:
        seen.append(float(delay))

    monkeypatch.setattr(http_mod.asyncio, "sleep", record)
    return seen


def _mock(client: AcademicHttpClient, handler) -> list[httpx.Request]:
    seen: list[httpx.Request] = []

    def record(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    client.client = httpx.AsyncClient(transport=httpx.MockTransport(record), headers=client.client.headers)
    return seen


def _quota(request: httpx.Request) -> httpx.Response:
    return httpx.Response(429, headers={"Retry-After": QUOTA_WAIT}, json={"error": "quota"})


def _quota_error():
    from scholar_search import exceptions

    return exceptions.QuotaExhaustedError


# --------------------------------------------------------------------------- the HTTP client


@pytest.mark.asyncio
async def test_a_429_with_a_retry_after_beyond_the_cap_is_not_retried_and_names_the_reset(slept):
    client = AcademicHttpClient(name="openalex", rate_limit=0, cache_enabled=False, base_delay=0)
    seen = _mock(client, _quota)
    before = datetime.now(UTC)
    with pytest.raises(RateLimitExceededError) as caught:
        await client.get("https://api.openalex.org/works/https://doi.org/10.1/x")
    error = caught.value
    assert isinstance(error, _quota_error())
    assert len(seen) == 1 and slept == []
    assert error.database == "OpenAlex" and error.provider == "openalex" and error.status_code == 429
    assert error.retry_after == 50000
    resets = datetime.fromisoformat(error.resets_at)
    assert before + timedelta(seconds=49990) <= resets <= datetime.now(UTC) + timedelta(seconds=50010)
    assert "quota" in str(error).lower() and error.resets_at in str(error)
    await client.close()


@pytest.mark.asyncio
async def test_a_retry_after_given_as_a_date_is_read_too(slept):
    later = datetime.now(UTC) + timedelta(hours=10)
    stamp = later.strftime("%a, %d %b %Y %H:%M:%S GMT")
    client = AcademicHttpClient(name="crossref", rate_limit=0, cache_enabled=False, base_delay=0)
    seen = _mock(client, lambda r: httpx.Response(429, headers={"Retry-After": stamp}))
    with pytest.raises(_quota_error()) as caught:
        await client.get("https://api.crossref.org/works/10.1/x")
    assert len(seen) == 1 and slept == []
    assert caught.value.database == "Crossref"
    assert abs(datetime.fromisoformat(caught.value.resets_at) - later) < timedelta(seconds=5)
    await client.close()


@pytest.mark.asyncio
async def test_a_short_retry_after_is_still_waited_and_retried(slept):
    client = AcademicHttpClient(name="openalex", rate_limit=0, cache_enabled=False, base_delay=0)
    answers = iter([httpx.Response(429, headers={"Retry-After": "2"}), httpx.Response(200, json={"id": "W1"})])
    seen = _mock(client, lambda r: next(answers))
    response = await client.get("https://api.openalex.org/works/W1")
    assert response.status_code == 200 and len(seen) == 2 and slept == [2.0]
    await client.close()


@pytest.mark.asyncio
async def test_a_429_without_retry_after_keeps_its_backoff_and_ends_as_a_rate_limit(slept):
    client = AcademicHttpClient(name="openalex", rate_limit=0, cache_enabled=False, base_delay=1)
    seen = _mock(client, lambda r: httpx.Response(429))
    with pytest.raises(RateLimitExceededError) as caught:
        await client.get("https://api.openalex.org/works/W1")
    assert not isinstance(caught.value, _quota_error())
    assert len(seen) == 4 and slept == [1.0, 2.0, 4.0]
    await client.close()


@pytest.mark.asyncio
async def test_a_5xx_with_a_long_retry_after_is_not_retried_either(slept):
    from scholar_search.exceptions import ProviderPausedError

    client = AcademicHttpClient(name="openalex", rate_limit=0, cache_enabled=False, base_delay=0)
    seen = _mock(client, lambda r: httpx.Response(503, headers={"Retry-After": "7200"}))
    with pytest.raises(ProviderPausedError) as caught:
        await client.get("https://api.openalex.org/works/W1")
    assert not isinstance(caught.value, RateLimitExceededError)
    assert caught.value.status_code == 503 and caught.value.retry_after == 7200
    assert len(seen) == 1 and slept == []
    await client.close()


@pytest.mark.asyncio
async def test_a_post_answered_429_with_a_long_retry_after_never_sleeps_it(slept):
    # Before this fix the POST loop slept the whole Retry-After, without the 60 s cap.
    client = AcademicHttpClient(name="hydration", rate_limit=0, cache_enabled=False, base_delay=0)
    seen = _mock(client, _quota)
    with pytest.raises(_quota_error()) as caught:
        await client.post("https://api.semanticscholar.org/graph/v1/paper/batch", json={"ids": []})
    assert len(seen) == 1 and slept == []
    assert caught.value.database == "Semantic Scholar"
    await client.close()


@pytest.mark.asyncio
async def test_a_post_with_a_short_retry_after_is_still_retried(slept):
    client = AcademicHttpClient(name="hydration", rate_limit=0, cache_enabled=False, base_delay=0)
    answers = iter([httpx.Response(429, headers={"Retry-After": "3"}), httpx.Response(200, json=[])])
    seen = _mock(client, lambda r: next(answers))
    response = await client.post("https://api.semanticscholar.org/graph/v1/paper/batch", json={"ids": []})
    assert response.status_code == 200 and len(seen) == 2 and slept == [3.0]
    await client.close()


# --------------------------------------------------------------------------- the checks


def _records(n: int) -> list[Document]:
    return [
        Document(
            title=f"Multispectral weed segmentation under sensor stress, part {i}",
            year=2024,
            external_ids=ExternalIds(doi=f"10.5555/weed.{i}"),
            provider="openalex",
            provider_id=f"W{i}",
            workspace_id=f"SCI-{i:06d}",
        )
        for i in range(n)
    ]


def _crossref_work(request: httpx.Request) -> httpx.Response:
    doi = request.url.path.split("/works/", 1)[1]
    i = doi.rsplit(".", 1)[1]
    return httpx.Response(200, json={"message": {
        "DOI": doi,
        "title": [f"Multispectral weed segmentation under sensor stress, part {i}"],
        "published-print": {"date-parts": [[2024]]},
    }})


def _verifier(crossref_handler, openalex_handler) -> tuple[DocumentVerifier, list, list]:
    crossref, openalex = CrossrefProvider(), OpenAlexProvider()
    for provider in (crossref, openalex):
        provider.client.base_delay = 0
        provider.client.rate_limiter.set_rate(0)
    crossref_seen = _mock(crossref.client, crossref_handler)
    openalex_seen = _mock(openalex.client, openalex_handler)
    return DocumentVerifier(crossref_provider=crossref, openalex_provider=openalex), crossref_seen, openalex_seen


@pytest.mark.asyncio
async def test_a_used_up_quota_ends_the_checks_in_bounded_time_and_keeps_every_record(slept):
    n = 12
    verifier, _, openalex_seen = _verifier(_crossref_work, _quota)
    records = _records(n)
    docs, audit = await verifier.process_batch(records, verify=True, enrich=True)

    # Bounded: OpenAlex is asked once, then never again in this batch, and nothing waits out the quota.
    assert len(openalex_seen) == 1
    assert sum(slept) <= 60
    # Every record is kept, in order, with its own identity.
    assert [d.workspace_id for d in docs] == [r.workspace_id for r in records]
    assert len(audit) == n
    # Crossref confirmed every record; the enrichment from OpenAlex was not done and says why.
    assert all(row["code"] == "VERIFIED" and row["verified"] is True for row in audit)
    assert all(row["not_done"] == ["enrichment"] for row in audit)
    assert all(row["reason"] == "PROVIDER_QUOTA_EXHAUSTED" for row in audit)
    paused = verifier.paused
    assert [p["database"] for p in paused] == ["OpenAlex"] and paused[0]["resets_at"]


@pytest.mark.asyncio
async def test_a_record_only_openalex_could_check_is_not_checked_never_unverified(slept):
    # Crossref does not know these DOIs and its title search finds nothing: only OpenAlex could say.
    def crossref_nothing(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/works/"):
            return httpx.Response(404, text="Resource not found.")
        return httpx.Response(200, json={"message": {"items": []}})

    verifier, _, openalex_seen = _verifier(crossref_nothing, _quota)
    records = _records(5)
    docs, audit = await verifier.process_batch(records, verify=True, enrich=True)

    assert len(openalex_seen) == 1 and sum(slept) <= 60
    assert len(docs) == 5
    for record, doc, row in zip(records, docs, audit, strict=True):
        assert doc.workspace_id == record.workspace_id and doc.title == record.title
        assert row["code"] == "NOT_CHECKED" and row["verified"] is False
        assert row["not_done"] == ["verification"] and row["reason"] == "PROVIDER_QUOTA_EXHAUSTED"
        assert "OpenAlex" in row["status"]


@pytest.mark.asyncio
async def test_a_stop_request_ends_the_checks_within_one_record(slept):

    def openalex_work(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    verifier, crossref_seen, _ = _verifier(_crossref_work, openalex_work)
    records = _records(10)
    asked: list[int] = []

    def should_stop() -> bool:
        asked.append(len(crossref_seen))
        return len(crossref_seen) >= 3  # the stop arrives while the third record is being checked

    docs, audit = await verifier.process_batch(records, verify=True, enrich=True, should_stop=should_stop)

    assert len(crossref_seen) == 3  # no fourth record was asked about
    assert [d.workspace_id for d in docs] == [r.workspace_id for r in records]
    assert [row["code"] for row in audit[:3]] == ["VERIFIED"] * 3
    assert all(row["code"] == "NOT_CHECKED" and row["reason"] == "STOPPED_BY_RESEARCHER" for row in audit[3:])
    assert all(row["not_done"] == ["verification", "enrichment"] for row in audit[3:])
    assert verifier.stopped is True


@pytest.mark.asyncio
async def test_without_a_quota_or_a_stop_the_audit_rows_say_everything_was_done(slept):
    verifier, _, openalex_seen = _verifier(_crossref_work, lambda r: httpx.Response(200, json={}))
    _, audit = await verifier.process_batch(_records(3), verify=True, enrich=True)
    assert len(openalex_seen) == 3 and slept == []
    assert all(row["code"] == "VERIFIED" and row["not_done"] == [] and row["reason"] is None for row in audit)
    assert verifier.paused == [] and verifier.stopped is False


def test_a_paused_provider_error_is_a_provider_error():
    from scholar_search.exceptions import ProviderPausedError, QuotaExhaustedError

    error = QuotaExhaustedError("openalex", database="OpenAlex", retry_after=50000.0, resets_at="2026-11-21T00:00:00+00:00")
    assert isinstance(error, ProviderPausedError) and isinstance(error, RateLimitExceededError)
    assert isinstance(error, ProviderError) and error.status_code == 429
