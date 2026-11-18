"""M3h-b-resilience: provider resilience findings F14, F15, F16.

`docs/assessment/three-phase-hardening-2026-11-10.md` ("Provider side") and
`docs/kits/search/PROVIDERS_2026-11.md` §2, §3a, §5, §7. Offline: requests go
to ``httpx.MockTransport`` doubles or to a capturing fake client; the
Crossref rate-limit header values are the ones Crossref sent in the golden
recording of 2026-11-08 (``tests/fixtures/cassettes/golden_uav_search.yaml``).
"""

from __future__ import annotations

import importlib.metadata

import httpx
import pytest

from scholar_search import http_client as http_mod
from scholar_search.config import settings
from scholar_search.enrichment import AbstractHydrator
from scholar_search.exceptions import ProviderError
from scholar_search.http_client import AcademicHttpClient
from scholar_search.models import Query
from scholar_search.providers.arxiv import ArxivProvider
from scholar_search.providers.crossref import CrossrefProvider
from scholar_search.providers.semanticscholar import SemanticScholarProvider

CROSSREF = "https://api.crossref.org/works"
S2_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
S2_BATCH = "https://api.semanticscholar.org/graph/v1/paper/batch"
ARXIV = "https://export.arxiv.org/api/query"


@pytest.fixture(autouse=True)
def _fresh_budgets(monkeypatch):
    monkeypatch.setattr(settings, "mailto", "tester@example.org")
    monkeypatch.setattr(settings, "http_cache", False)
    monkeypatch.setattr(settings, "s2_key", None)
    reset = getattr(http_mod, "reset_host_budgets", lambda: None)
    reset()
    yield
    reset()


def _mock(client: AcademicHttpClient, handler) -> list[httpx.Request]:
    seen: list[httpx.Request] = []

    def record(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    client.client = httpx.AsyncClient(
        transport=httpx.MockTransport(record), headers=client.client.headers
    )
    return seen


# --------------------------------------------------------------------------- F14 User-Agent


def test_the_user_agent_names_nexus_scholar_and_its_installed_version():
    version = importlib.metadata.version("nexus-scholar")
    agent = AcademicHttpClient(name="t", rate_limit=0).client.headers["user-agent"]
    assert agent.startswith(f"nexus-scholar/{version}")
    assert "scholar-search-kit" not in agent and "0.1.0" not in agent
    assert "(mailto:tester@example.org)" in agent


def test_the_user_agent_carries_no_contact_address_when_none_is_set(monkeypatch):
    monkeypatch.setattr(settings, "mailto", None)
    agent = AcademicHttpClient(name="t", rate_limit=0).client.headers["user-agent"]
    assert agent == f"nexus-scholar/{importlib.metadata.version('nexus-scholar')}"


# --------------------------------------------------------------------------- F14 Crossref rate


def _effective(provider, url):
    budget = http_mod.host_budget(url)
    return min(provider.client.rate_limiter.rate, budget.rate)


def test_crossref_list_requests_stay_at_three_per_second_with_a_contact_address():
    provider = CrossrefProvider()
    assert _effective(provider, CROSSREF) <= 3.0
    assert _effective(provider, CROSSREF + "?query=x&filter=from-pub-date:2020") <= 3.0
    assert _effective(provider, CROSSREF + "/10.1000/xyz") <= 10.0


def test_crossref_list_requests_stay_at_one_per_second_without_a_contact_address(monkeypatch):
    monkeypatch.setattr(settings, "mailto", None)
    provider = CrossrefProvider()
    assert _effective(provider, CROSSREF) <= 1.0
    assert _effective(provider, CROSSREF + "/10.1000/xyz") <= 5.0


def test_crossref_list_and_single_record_requests_have_separate_budgets():
    assert http_mod.host_budget(CROSSREF) is not http_mod.host_budget(CROSSREF + "/10.1000/xyz")
    assert http_mod.host_budget(CROSSREF) is http_mod.host_budget(CROSSREF + "?rows=10")


def test_a_budget_follows_a_contact_address_set_later(monkeypatch):
    monkeypatch.setattr(settings, "mailto", None)
    assert http_mod.host_budget(CROSSREF).rate == pytest.approx(1.0)
    monkeypatch.setattr(settings, "mailto", "tester@example.org")
    assert http_mod.host_budget(CROSSREF).rate == pytest.approx(3.0)


@pytest.mark.asyncio
async def test_crossref_rate_limit_headers_lower_the_budget():
    client = AcademicHttpClient(name="crossref", rate_limit=3.0, cache_enabled=False)
    _mock(client, lambda r: httpx.Response(
        200, json={}, headers={"x-rate-limit-limit": "2", "x-rate-limit-interval": "1s"}
    ))
    await client.get(CROSSREF, params={"query": "x"})
    assert http_mod.host_budget(CROSSREF).rate == pytest.approx(2.0)
    await client.close()


@pytest.mark.asyncio
async def test_rate_limit_headers_never_raise_the_budget():
    client = AcademicHttpClient(name="crossref", rate_limit=3.0, cache_enabled=False)
    _mock(client, lambda r: httpx.Response(
        200, json={}, headers={"x-rate-limit-limit": "50", "x-rate-limit-interval": "1s"}
    ))
    await client.get(CROSSREF, params={"query": "x"})
    assert http_mod.host_budget(CROSSREF).rate <= 3.0
    await client.close()


@pytest.mark.asyncio
async def test_the_recorded_golden_crossref_headers_keep_three_per_second():
    # Crossref's own answer on 2026-11-08 (polite pool): limit 3, interval 1s.
    client = AcademicHttpClient(name="crossref", rate_limit=3.0, cache_enabled=False)
    _mock(client, lambda r: httpx.Response(
        200, json={}, headers={"x-rate-limit-limit": "3", "x-rate-limit-interval": "1s",
                               "x-api-pool": "polite-array", "x-concurrency-limit": "3"}
    ))
    await client.get(CROSSREF, params={"query": "x"})
    assert http_mod.host_budget(CROSSREF).rate == pytest.approx(3.0)
    await client.close()


@pytest.mark.parametrize(
    ("limit", "interval", "expected"),
    [("3", "1s", 3.0), ("60", "60s", 1.0), ("120", "1m", 2.0), ("5", "500ms", 10.0),
     ("x", "1s", None), ("3", "soon", None), ("0", "1s", None), (None, "1s", None)],
)
def test_rate_limit_header_values_are_read_or_ignored(limit, interval, expected):
    headers = {"x-rate-limit-interval": interval}
    if limit is not None:
        headers["x-rate-limit-limit"] = limit
    got = http_mod.header_rate(httpx.Headers(headers))
    assert got == (pytest.approx(expected) if expected is not None else None)


@pytest.mark.asyncio
async def test_a_header_from_a_host_without_a_budget_lowers_only_that_client():
    client = AcademicHttpClient(name="other", rate_limit=10.0, cache_enabled=False)
    _mock(client, lambda r: httpx.Response(
        200, json={}, headers={"x-rate-limit-limit": "4", "x-rate-limit-interval": "1s"}
    ))
    await client.get("https://example.org/api", params={})
    assert client.rate_limiter.rate == pytest.approx(4.0)
    assert http_mod.host_budget("https://example.org/api") is None
    await client.close()


# --------------------------------------------------------------------------- F16 arXiv rate


def test_arxiv_asks_at_most_one_request_every_three_seconds():
    provider = ArxivProvider()
    assert provider.client.rate_limiter.rate <= 1 / 3
    assert http_mod.host_budget(ARXIV).rate <= 1 / 3


# --------------------------------------------------------------------------- F16 arXiv date note


def test_the_arxiv_leg_note_no_longer_denies_a_date_filter():
    _, _, notes = ArxivProvider().translate(Query(text="drone AND weed", year_min=2020, year_max=2026))
    joined = " ".join(notes)
    assert "has no year filter" not in joined
    assert "submittedDate" in joined
    reasons = ArxivProvider().cannot_express(Query(text="drone", year_min=2020, year_max=2026))
    assert not any("has no year filter" in r for r in reasons)


# --------------------------------------------------------------------------- F16 S2 citations paging


class _Pages:
    """A fake client answering S2 citation pages of ``sizes`` records, with ``next``."""

    def __init__(self, sizes: list[int], key: str):
        self.sizes = sizes
        self.key = key
        self.calls: list[dict] = []

    async def get(self, url, params=None, **kwargs):
        params = dict(params or {})
        self.calls.append(params)
        offset = int(params.get("offset", 0))
        index = len(self.calls) - 1
        size = self.sizes[index] if index < len(self.sizes) else 0
        body = {
            "offset": offset,
            "data": [
                {self.key: {"paperId": f"P{offset + i}", "title": f"Paper {offset + i}"}}
                for i in range(size)
            ],
        }
        if index + 1 < len(self.sizes):
            body["next"] = offset + size
        return _Json(body)


class _Json:
    status_code = 200

    def __init__(self, body):
        self.body = body

    def json(self):
        return self.body


@pytest.mark.asyncio
@pytest.mark.parametrize(("method", "key"), [("get_citations", "citingPaper"), ("get_references", "citedPaper")])
async def test_s2_citations_and_references_are_paged_past_1000(method, key):
    provider = SemanticScholarProvider()
    fake = _Pages([1000, 10], key)
    provider.client = fake
    papers = [doc async for doc in getattr(provider, method)("PAPER")]
    assert len(papers) == 1010
    assert [c.get("offset", 0) for c in fake.calls] == [0, 1000]
    assert all(c["limit"] == 1000 for c in fake.calls)


@pytest.mark.asyncio
async def test_s2_citation_paging_stops_when_next_does_not_advance():
    provider = SemanticScholarProvider()

    class _Stuck(_Pages):
        async def get(self, url, params=None, **kwargs):
            self.calls.append(dict(params or {}))
            return _Json({"offset": 0, "next": 0, "data": [{"citingPaper": {"paperId": "P", "title": "T"}}]})

    fake = _Stuck([], "citingPaper")
    provider.client = fake
    papers = [doc async for doc in provider.get_citations("PAPER")]
    assert len(fake.calls) == 1 and len(papers) == 1


# --------------------------------------------------------------------------- M3h deferred: one S2 budget


def test_the_leg_and_the_abstract_hydrator_share_one_semantic_scholar_budget():
    SemanticScholarProvider()
    AcademicHttpClient(name="hydration", rate_limit=10)
    budget = http_mod.host_budget(S2_SEARCH)
    assert budget is not None
    assert budget is http_mod.host_budget(S2_BATCH)
    assert budget.rate <= settings.rate_limit_s2 < 1.0


@pytest.mark.asyncio
async def test_a_post_to_semantic_scholar_waits_on_the_shared_budget(monkeypatch):
    client = AcademicHttpClient(name="hydration", rate_limit=10, cache_enabled=False)
    _mock(client, lambda r: httpx.Response(200, json=[]))
    budget = http_mod.host_budget(S2_BATCH)
    waits = []
    original = budget.wait

    async def counted():
        waits.append(1)
        await original()

    monkeypatch.setattr(budget, "wait", counted)
    await client.post(S2_BATCH, json={"ids": []})
    await client.get(S2_SEARCH, params={})
    assert len(waits) == 2
    await client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [400, 403])
async def test_a_post_answered_4xx_is_sent_once(status):
    client = AcademicHttpClient(name="hydration", rate_limit=0, cache_enabled=False, base_delay=0)
    seen = _mock(client, lambda r: httpx.Response(status, text="Forbidden"))
    with pytest.raises(ProviderError) as caught:
        await client.post("https://example.org/batch", json={"ids": []})
    assert caught.value.status_code == status
    assert len(seen) == 1
    await client.close()


@pytest.mark.asyncio
async def test_a_post_answered_5xx_is_still_retried():
    client = AcademicHttpClient(name="hydration", rate_limit=0, cache_enabled=False, base_delay=0)
    answers = iter([httpx.Response(503), httpx.Response(200, json=[])])
    seen = _mock(client, lambda r: next(answers))
    response = await client.post("https://example.org/batch", json={"ids": []})
    assert response.status_code == 200 and len(seen) == 2
    await client.close()


@pytest.mark.asyncio
async def test_the_hydrator_never_retries_keyless_after_a_rejected_key(monkeypatch):
    monkeypatch.setattr(settings, "s2_key", "rejected-key")

    class _Refuses:
        def __init__(self):
            self.calls: list[dict] = []

        async def post(self, url, json=None, params=None, headers=None, **kwargs):
            self.calls.append(dict(headers or {}))
            raise ProviderError("hydration", "Forbidden", status_code=403)

    fake = _Refuses()
    hydrator = AbstractHydrator(fake)
    assert await hydrator._hydrate_from_s2(["10.1/x"]) == {}
    assert len(fake.calls) == 1
    assert fake.calls[0].get("x-api-key") == "rejected-key"


# --------------------------------------------------------------------------- F15 one default database set


def test_one_default_database_set():
    from scholar_harness.console.api import discovery as console_discovery
    from scholar_harness.recon import engine as recon_engine
    from scholar_protocol import presets
    from scholar_protocol.models import SearchStrategy
    from scholar_search import cli, engine, plan
    from scholar_search.models import DEFAULT_DATABASES
    from scholar_search.protocol_adapter import compile_protocol_search

    expected = list(DEFAULT_DATABASES)
    sets = {
        "engine": list(engine.DEFAULT_PROVIDER_NAMES),
        "engine suite": [p.name for p in engine.SearchEngine().providers],
        "plan": list(plan.DEFAULT_PROVIDERS),
        "run_providers(None)": plan.run_providers(None),
        "run_providers([])": plan.run_providers([]),
        "adapter, no list": list(compile_protocol_search({"search_strategy": {}})[1]),
        "protocol model": list(SearchStrategy.model_fields["target_databases"].default),
        "presets": list(presets._DEFAULT_DATABASES),
        "recon": list(recon_engine.DEFAULT_PROVIDERS),
        "console": list(console_discovery.DEFAULT_PROVIDERS),
        "cli, no protocol": [p.name for p in cli._default_providers()],
    }
    assert {name: s for name, s in sets.items() if s != expected} == {}


def test_a_protocol_that_names_its_databases_searches_exactly_those():
    import json
    from pathlib import Path

    from scholar_search.plan import run_providers
    from scholar_search.protocol_adapter import compile_protocol_search

    named = compile_protocol_search({"search_strategy": {"target_databases": ["pubmed", "crossref"]}})[1]
    assert run_providers(named) == ["pubmed", "crossref"]
    golden = Path(__file__).resolve().parents[3] / "workspaces" / "golden-uav-30" / "protocol.json"
    data = json.loads(golden.read_text(encoding="utf-8"))
    assert run_providers(compile_protocol_search(data)[1]) == [
        "openalex", "semanticscholar", "crossref", "arxiv", "pubmed",
    ]


# --------------------------------------------------------------------------- F16 leg record and auth channel


def _leg_after_translation(provider, query=None):
    from scholar_search.models import SearchLeg

    provider.current_leg = SearchLeg(provider=provider.name, query_id="Q")
    provider._record_translation(query or Query(text="drone AND weed", max_results=100))
    return provider.current_leg.to_dict()


@pytest.mark.parametrize(
    ("factory", "key", "endpoint", "auth", "page_size"),
    [
        ("crossref", None, "https://api.crossref.org/works", "mailto", 100),
        ("openalex", "oa-key", "https://api.openalex.org/works", "key", 100),
        ("openalex", None, "https://api.openalex.org/works", "none", 100),
        ("semanticscholar", "s2-key", S2_SEARCH, "key", 1000),
        ("semanticscholar", None, S2_SEARCH, "none", 1000),
        ("arxiv", None, ARXIV, "none", 100),
        ("pubmed", None, "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", "mailto", 100),
    ],
)
def test_each_leg_records_its_endpoint_auth_channel_and_page_size(
    monkeypatch, factory, key, endpoint, auth, page_size
):
    from scholar_search.providers.openalex import OpenAlexProvider
    from scholar_search.providers.pubmed import PubMedProvider

    monkeypatch.setattr(settings, "openalex_key", key if factory == "openalex" else None)
    monkeypatch.setattr(settings, "s2_key", key if factory == "semanticscholar" else None)
    classes = {
        "crossref": CrossrefProvider, "openalex": OpenAlexProvider,
        "semanticscholar": SemanticScholarProvider, "arxiv": ArxivProvider, "pubmed": PubMedProvider,
    }
    leg = _leg_after_translation(classes[factory]())
    assert (leg["endpoint"], leg["auth"], leg["page_size"]) == (endpoint, auth, page_size)
    if key:
        assert key not in str(leg)


def test_a_leg_without_a_contact_address_says_its_auth_channel_is_none(monkeypatch):
    monkeypatch.setattr(settings, "mailto", None)
    assert _leg_after_translation(CrossrefProvider())["auth"] == "none"


@pytest.mark.parametrize("status", [401, 403])
def test_a_rejected_s2_key_is_recorded_as_key_rejected(monkeypatch, status):
    import asyncio

    from scholar_search.engine import SearchEngine

    monkeypatch.setattr(settings, "s2_key", "s2-placeholder")
    provider = SemanticScholarProvider()

    async def refuse(url, params=None, headers=None, **kwargs):
        raise ProviderError("semanticscholar", "Forbidden", status_code=status)

    provider.client.get = refuse
    run = asyncio.run(SearchEngine(providers=[provider]).run(Query(text="drone AND weed"), dedup=False))
    assert run.legs[0].to_dict()["auth"] == "key_rejected"


@pytest.mark.parametrize(("status", "auth"), [(401, "key_rejected"), (403, "key_rejected"), (409, "key")])
def test_an_openalex_key_refusal_is_recorded_on_the_leg(monkeypatch, status, auth):
    import asyncio

    from scholar_search.engine import SearchEngine
    from scholar_search.providers.openalex import OpenAlexProvider

    monkeypatch.setattr(settings, "openalex_key", "oa-key")
    provider = OpenAlexProvider()

    async def refuse(url, params=None, headers=None, **kwargs):
        raise ProviderError("openalex", "refused", status_code=status)

    provider.client.get = refuse
    run = asyncio.run(SearchEngine(providers=[provider]).run(Query(text="drone AND weed"), dedup=False))
    assert run.legs[0].to_dict()["auth"] == auth


def test_the_mcp_discover_tool_searches_the_default_set(monkeypatch, tmp_path):
    import asyncio

    from scholar_agent import server
    from scholar_search.models import DEFAULT_DATABASES

    seen = {}

    class _Engine:
        def __init__(self, providers=None):
            from scholar_search.engine import SearchEngine

            self.providers = SearchEngine(providers=providers).providers if providers else None
            seen["names"] = (
                [p.name for p in providers] if providers else [p.name for p in SearchEngine().providers]
            )

        async def search_all(self, query, dedup=True):
            return []

        async def close(self):
            return None

    monkeypatch.setattr(server, "SearchEngine", _Engine)
    monkeypatch.setattr(server, "_resolve_path", lambda p: str(tmp_path / p))
    asyncio.run(server.nexus_discover("drone"))
    assert seen["names"] == list(DEFAULT_DATABASES)


# --------------------------------------------------------------------------- review repairs (M3h-b-resilience)


@pytest.mark.asyncio
async def test_the_harvest_verifier_waits_on_the_crossref_single_record_budget(monkeypatch):
    from scholar_search.models import Document, ExternalIds
    from scholar_search.providers.openalex import OpenAlexProvider
    from scholar_search.verifier import DocumentVerifier

    crossref, openalex = CrossrefProvider(), OpenAlexProvider()
    seen = _mock(crossref.client, lambda r: httpx.Response(404, text="Resource not found."))
    _mock(openalex.client, lambda r: httpx.Response(404, text="not found"))
    single = http_mod.host_budget(CROSSREF + "/10.1000/xyz")
    waits = []
    original = single.wait

    async def counted():
        waits.append(1)
        await original()

    monkeypatch.setattr(single, "wait", counted)
    doc = Document(title="T", provider="crossref", provider_id="x", external_ids=ExternalIds(doi="10.1000/xyz"))
    await DocumentVerifier(crossref_provider=crossref, openalex_provider=openalex).verify_document(doc)
    assert seen and seen[0].url.path == "/works/10.1000/xyz"
    assert waits == [1]
    await crossref.client.close()
    await openalex.client.close()


@pytest.mark.asyncio
async def test_a_throttle_header_never_sets_a_budget_below_one_per_second():
    client = AcademicHttpClient(name="crossref", rate_limit=3.0, cache_enabled=False)
    _mock(client, lambda r: httpx.Response(
        200, json={}, headers={"x-rate-limit-limit": "1", "x-rate-limit-interval": "100000h"}
    ))
    await client.get(CROSSREF, params={"query": "x"})
    assert http_mod.host_budget(CROSSREF).rate == pytest.approx(1.0)
    await client.close()


def test_a_limiter_with_no_rate_never_waits_or_divides():
    limiter = http_mod.RateLimiter(1.0)
    limiter.set_rate(0)
    limiter.tokens = 0.0  # an empty bucket: the old code divided by the rate here
    assert limiter._take() == 0.0


@pytest.mark.parametrize("field", ["rate_limit_crossref", "rate_limit_crossref_single", "rate_limit_s2"])
def test_a_zero_rate_setting_is_refused(field):
    from pydantic import ValidationError

    from scholar_search.config import Settings

    with pytest.raises(ValidationError):
        Settings(**{field: 0})
