"""E5 (M3b-api): a failed leg carries a typed ``error_code`` beside its ``error`` text.

`docs/architecture/research_ui/DISCOVERY_API_PACKET.md` §4.3, §4.7. The code is
a leg field, never an HTTP refusal: a failed leg makes a ``PARTIAL`` run.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest
from scholar_search.engine import SearchEngine, provider_error_code
from scholar_search.exceptions import ProviderError, ProviderTimeoutError, RateLimitExceededError
from scholar_search.http_client import AcademicHttpClient
from scholar_search.models import Document, Query


class _Failing:
    def __init__(self, name, exc):
        self.name, self.exc, self.current_leg = name, exc, None

    async def search(self, query):
        if False:
            yield None
        raise self.exc


class _Ok:
    name, current_leg = "ok", None

    async def search(self, query):
        yield Document(title="A record", provider="ok", provider_id="1")


CASES = [
    (RateLimitExceededError("openalex"), "PROVIDER_RATE_LIMITED"),
    (ProviderError("crossref", "slow", status_code=429), "PROVIDER_RATE_LIMITED"),
    (ProviderTimeoutError("arxiv", "Request timed out after 30s"), "PROVIDER_TIMEOUT"),
    (TimeoutError(), "PROVIDER_TIMEOUT"),
    (ProviderError("pubmed", "bad gateway", status_code=502), "PROVIDER_UNAVAILABLE"),
    (ProviderError("pubmed", "Network communication error: refused"), "PROVIDER_UNAVAILABLE"),
    (ProviderError("semanticscholar", "forbidden", status_code=403), "PROVIDER_REFUSED"),
    (ValueError("a parse bug"), None),
]


@pytest.mark.parametrize(("exc", "code"), CASES)
def test_each_failure_kind_has_its_code(exc, code):
    assert provider_error_code(exc) == code


def test_a_failed_leg_keeps_its_text_and_gains_its_code():
    engine = SearchEngine(providers=[_Failing("openalex", RateLimitExceededError("openalex")), _Ok()])
    run = asyncio.run(engine.run(Query(text="uav"), dedup=False))
    legs = {leg.provider: leg.to_dict() for leg in run.legs}
    assert legs["openalex"]["status"] == "failed"
    assert legs["openalex"]["error"].startswith("RateLimitExceededError")
    assert legs["openalex"]["error_code"] == "PROVIDER_RATE_LIMITED"
    assert legs["ok"]["status"] == "ok" and legs["ok"]["error_code"] is None


def test_the_http_client_raises_a_typed_timeout(monkeypatch):
    client = AcademicHttpClient(name="crossref", rate_limit=1000)
    client.max_retries = 0

    async def timeout(*a, **k):
        raise httpx.ReadTimeout("slow")

    monkeypatch.setattr(client.client, "get", timeout)
    with pytest.raises(ProviderTimeoutError) as caught:
        asyncio.run(client.get("https://api.crossref.org/works"))
    assert provider_error_code(caught.value) == "PROVIDER_TIMEOUT"
