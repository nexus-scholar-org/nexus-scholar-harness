"""M10b Part D: each database's count-only request (spec `docs/ux/phase1-discovery/final/01-plan.md` "Size estimate").

Offline: every provider's client is a capture double. A count sends one request,
built from the same ``translate`` the plan and the harvest use, with the page
size set so that no record body is asked for (OpenAlex ``per-page=1``,
Crossref ``rows=0``, PubMed ``retmax=0``, arXiv ``max_results=1``, Semantic
Scholar the first page with ``fields=paperId``). bioRxiv reports no total.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from scholar_search.config import settings
from scholar_search.models import Query
from scholar_search.plan import leg_query, translate_provider
from scholar_search.protocol_adapter import compile_protocol_search
from scholar_search.providers.arxiv import ArxivProvider
from scholar_search.providers.biorxiv import BiorxivProvider
from scholar_search.providers.crossref import CrossrefProvider
from scholar_search.providers.openalex import OpenAlexProvider
from scholar_search.providers.pubmed import PubMedProvider
from scholar_search.providers.semanticscholar import SemanticScholarProvider

ROOT = Path(__file__).resolve().parents[3]
GOLDEN_PROTOCOL = ROOT / "workspaces" / "golden-uav-30" / "protocol.json"


@pytest.fixture(autouse=True)
def _contact(monkeypatch):
    monkeypatch.setattr(settings, "mailto", "tester@example.org")
    monkeypatch.setattr(settings, "openalex_key", "count-test-key")  # a placeholder, never sent
    monkeypatch.setattr(settings, "s2_key", None)


class _Answer:
    status_code = 200

    def __init__(self, body=None, text: str = ""):
        self.body, self.text, self.content = body, text, text.encode("utf-8")

    def json(self):
        return self.body


class _Capture:
    def __init__(self, answer: _Answer):
        self.answer = answer
        self.calls: list[tuple[str, dict]] = []

    async def get(self, url, params=None, **kwargs):
        self.calls.append((url, dict(params or {})))
        return self.answer

    async def close(self):
        pass


ARXIV_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
  <opensearch:totalResults>312</opensearch:totalResults>
  <opensearch:startIndex>0</opensearch:startIndex>
  <opensearch:itemsPerPage>1</opensearch:itemsPerPage>
</feed>
"""

CASES = [
    # (provider class, answer, page-size parameter and value, the count read, the request field holding the string)
    (OpenAlexProvider, _Answer({"meta": {"count": 1234}, "results": [{}]}), ("per-page", 1), 1234, "search.title_and_abstract"),
    (CrossrefProvider, _Answer({"message": {"total-results": 987, "items": []}}), ("rows", 0), 987, "query"),
    (PubMedProvider, _Answer({"esearchresult": {"count": "456", "idlist": []}}), ("retmax", 0), 456, "term"),
    (ArxivProvider, _Answer(text=ARXIV_FEED), ("max_results", 1), 312, "search_query"),
    (SemanticScholarProvider, _Answer({"total": 2048, "data": [{"paperId": "x"}], "token": "next"}), ("fields", "paperId"), 2048, "query"),
]


def _golden_query() -> Query:
    return compile_protocol_search(GOLDEN_PROTOCOL)[0]


@pytest.mark.parametrize(("cls", "answer", "page", "total", "string_param"), CASES, ids=[c[0].__name__ for c in CASES])
def test_a_count_sends_one_request_for_the_plans_string_and_no_records(cls, answer, page, total, string_param):
    provider = cls()
    provider.client = _Capture(answer)
    query = leg_query(_golden_query())

    counted = asyncio.run(provider.count(query))

    assert counted == total
    assert len(provider.client.calls) == 1  # one request, no second page, no record fetch
    _url, params = provider.client.calls[0]
    name, value = page
    assert params[name] == value
    # The count is for exactly the executed string the researcher sees on Plan.
    assert params[string_param] == translate_provider(cls(), _golden_query())["executed_query"]
    assert "token" not in params  # never a second bulk page
    if cls is PubMedProvider:
        assert "efetch" not in _url


def test_a_count_keeps_the_plans_filters():
    """The year window and the other parameters of the plan go with the count (OpenAlex, Crossref, S2)."""
    query = leg_query(_golden_query())
    for cls, answer, _page, _total, _param in CASES:
        provider = cls()
        provider.client = _Capture(answer)
        asyncio.run(provider.count(query))
        sent = provider.client.calls[0][1]
        _executed, planned, _notes = cls().translate(query)
        for key, value in planned.items():
            if key in {"per-page", "rows", "retmax", "max_results", "fields", "cursor"}:
                continue
            assert sent[key] == value, (cls.__name__, key)


def test_biorxiv_cannot_be_counted():
    with pytest.raises(NotImplementedError):
        asyncio.run(BiorxivProvider().count(leg_query(_golden_query())))


def test_a_missing_total_is_none_not_zero():
    provider = CrossrefProvider()
    provider.client = _Capture(_Answer({"message": {"items": []}}))
    assert asyncio.run(provider.count(leg_query(_golden_query()))) is None


def test_a_failed_count_raises_the_providers_error():
    from scholar_search.exceptions import ProviderError

    class _Refusing(_Capture):
        async def get(self, url, params=None, **kwargs):
            raise ProviderError("crossref", "busy", status_code=429)

    provider = CrossrefProvider()
    provider.client = _Refusing(_Answer())
    with pytest.raises(ProviderError):
        asyncio.run(provider.count(leg_query(_golden_query())))


@pytest.mark.parametrize(("keyed", "status"), [(False, 403), (True, 401)])
def test_a_refused_semantic_scholar_count_names_the_refusal(monkeypatch, keyed, status):
    """Decision 14: a count has no leg, so the refusal sentence travels in the error."""
    from scholar_search.exceptions import ProviderError

    monkeypatch.setattr(settings, "s2_key", "s2-placeholder" if keyed else None)

    class _Refusing(_Capture):
        async def get(self, url, params=None, **kwargs):
            raise ProviderError("semanticscholar", "Forbidden", status_code=status)

    provider = SemanticScholarProvider()
    provider.client = _Refusing(_Answer())
    with pytest.raises(ProviderError) as raised:
        asyncio.run(provider.count(leg_query(_golden_query())))
    assert raised.value.status_code == status
    assert ("SCHOLAR_S2_KEY" if keyed else "keyless request") in str(raised.value)
