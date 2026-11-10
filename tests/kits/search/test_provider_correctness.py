"""M3h-providers: provider correctness findings F11, F12, F13.

`docs/assessment/three-phase-hardening-2026-11-10.md` §2 and
`docs/kits/search/PROVIDERS_2026-11.md`. Offline: the PubMed answers are the
ESearch responses recorded on 2026-11-10 under ``fixtures/pubmed/``.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from scholar_search.config import settings
from scholar_search.engine import SearchEngine
from scholar_search.exceptions import ProviderError
from scholar_search.models import Query, SearchLeg
from scholar_search.providers import openalex as openalex_mod
from scholar_search.providers.openalex import OpenAlexProvider
from scholar_search.providers.pubmed import PubMedProvider

FIXTURES = Path(__file__).parent / "fixtures" / "pubmed"


@pytest.fixture(autouse=True)
def _contact(monkeypatch):
    monkeypatch.setattr(settings, "mailto", "tester@example.org")
    monkeypatch.setattr(settings, "openalex_key", None)


class _Json:
    status_code = 200
    content = b""

    def __init__(self, body):
        self.body = body

    def json(self):
        return self.body


class _Capture:
    def __init__(self, body):
        self.calls: list[tuple[str, dict]] = []
        self.body = body

    async def get(self, url, params=None, **kwargs):
        self.calls.append((url, dict(params or {})))
        return _Json(self.body)


def _recorded(name: str) -> dict:
    body = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    body["esearchresult"]["idlist"] = []  # stop after the search page: no efetch
    return body


# --------------------------------------------------------------------------- F11 PubMed


def test_pubmed_abstract_terms_are_sent_as_title_or_abstract():
    provider = PubMedProvider()
    executed, request, notes = provider.translate(
        Query(text='abs:"weed mapping" AND title:drone', year_min=2020, year_max=2026)
    )
    assert executed == '"weed mapping"[tiab] AND drone[ti] AND 2020:2026[pdat]'
    assert request["term"] == executed
    assert "[ab]" not in executed
    assert notes == [PubMedProvider.ABSTRACT_NOTE]


def test_pubmed_query_without_abstract_terms_has_no_abstract_note():
    _, _, notes = PubMedProvider().translate(Query(text="weed AND drone"))
    assert notes == []


@pytest.mark.asyncio
async def test_pubmed_leg_records_the_tiab_string_it_sent():
    provider = PubMedProvider()
    provider.client = _Capture(_recorded("esearch_tiab_ok.json"))
    run = await SearchEngine(providers=[provider]).run(
        Query(text='abs:"weed mapping" AND title:drone', id="Q1"), dedup=False
    )
    sent = provider.client.calls[0][1]["term"]
    assert sent == '"weed mapping"[tiab] AND drone[ti]'
    leg = run.legs[0]
    assert leg.executed_query == sent
    assert PubMedProvider.ABSTRACT_NOTE in leg.notes
    assert not any("did not apply" in n for n in leg.notes), leg.notes


def _esearch_leg(body: dict, term: str) -> SearchLeg:
    provider = PubMedProvider()
    provider.current_leg = SearchLeg(provider="pubmed", query_id="Q1")
    provider._record_esearch_errors(body["esearchresult"], term)
    return provider.current_leg


def test_a_field_tag_pubmed_did_not_apply_becomes_a_leg_note():
    """The recorded answer to ``weed[ab] AND drone[ti]``: JSON says nothing, the translation widens."""
    body = _recorded("esearch_ab_field_not_found.json")
    assert body["esearchresult"]["errorlist"]["fieldsnotfound"] == []  # why the translation is read
    leg = _esearch_leg(body, "weed[ab] AND drone[ti]")
    notes = [n for n in leg.notes if "did not apply" in n]
    assert len(notes) == 1, leg.notes
    assert "[ab]" in notes[0] and "[ti]" not in notes[0]
    assert '"weed"[All Fields]' in notes[0]


def test_a_fieldsnotfound_entry_becomes_a_leg_note():
    leg = _esearch_leg(
        {"esearchresult": {"errorlist": {"fieldsnotfound": ["ab"], "phrasesnotfound": ["zz qq"]}}},
        "weed[ab]",
    )
    assert any("[ab]" in n for n in leg.notes), leg.notes
    assert any('"zz qq"' in n for n in leg.notes), leg.notes


def test_every_applied_tag_gives_no_note():
    body = _recorded("esearch_tiab_ok.json")
    leg = _esearch_leg(body, '"weed mapping"[tiab] AND drone[ti] AND smith[au] AND 2020:2026[pdat]')
    assert leg.notes == []


# --------------------------------------------------------------------------- F12 OpenAlex key


def test_openalex_never_sends_the_contact_email():
    executed, request, notes = OpenAlexProvider().translate(Query(text="weed AND drone"))
    assert "mailto" not in request and "email" not in request
    assert any("SCHOLAR_OPENALEX_KEY" in n for n in notes), notes


def test_openalex_sends_the_key_and_drops_the_note_when_set(monkeypatch):
    monkeypatch.setattr(settings, "openalex_key", "k-test")
    _, request, notes = OpenAlexProvider().translate(Query(text="weed AND drone"))
    assert request["api_key"] == "k-test" and "mailto" not in request
    assert notes == []


@pytest.mark.parametrize("status", [401, 403, 409])
def test_an_openalex_key_refusal_is_provider_refused_with_a_key_note(status):
    provider = OpenAlexProvider()

    async def refuse(*args, **kwargs):
        raise ProviderError("openalex", "HTTP request failed: key", status_code=status)

    provider.client.get = refuse
    run = asyncio.run(SearchEngine(providers=[provider]).run(Query(text="weed AND drone"), dedup=False))
    leg = run.legs[0].to_dict()
    assert leg["status"] == "failed" and leg["error_code"] == "PROVIDER_REFUSED"
    assert any(f"HTTP {status}" in n and "SCHOLAR_OPENALEX_KEY" in n for n in leg["notes"]), leg["notes"]


def test_an_openalex_server_error_gets_no_key_note():
    provider = OpenAlexProvider()

    async def fail(*args, **kwargs):
        raise ProviderError("openalex", "bad gateway", status_code=502)

    provider.client.get = fail
    run = asyncio.run(SearchEngine(providers=[provider]).run(Query(text="weed"), dedup=False))
    leg = run.legs[0].to_dict()
    assert leg["error_code"] == "PROVIDER_UNAVAILABLE"
    assert not any("refused the request" in n for n in leg["notes"])


# --------------------------------------------------------------------------- F13 OpenAlex page and search


@pytest.mark.parametrize("cap", [None, 50, 100, 200, 10_000])
def test_openalex_page_size_never_exceeds_100(cap):
    _, request, _ = OpenAlexProvider().translate(Query(text="weed", max_results=cap))
    assert request["per-page"] == min(cap or 100, 100)
    assert getattr(openalex_mod, "MAX_PER_PAGE", None) == 100


def test_openalex_boolean_query_uses_the_scoped_search_parameter():
    query = Query(text='("unmanned aerial vehicle" OR drone) AND weed', year_min=2020, year_max=2026)
    executed, request, _ = OpenAlexProvider().translate(query)
    assert request["search.title_and_abstract"] == executed == '("unmanned aerial vehicle" OR drone) AND weed'
    assert "search" not in request
    assert request["filter"] == "from_publication_date:2020-01-01,to_publication_date:2026-12-31"
    assert "title_and_abstract.search" not in json.dumps(request)


def test_openalex_boolean_query_with_a_comma_is_sent_unchanged():
    text = '"weed, crop" AND drone'
    executed, request, _ = OpenAlexProvider().translate(Query(text=text))
    assert executed == request["search.title_and_abstract"] == text
    assert "filter" not in request


@pytest.mark.asyncio
async def test_openalex_search_sends_what_translate_says():
    provider = OpenAlexProvider()
    provider.client = _Capture({"results": [], "meta": {"count": 0, "next_cursor": None}})
    query = Query(text="weed AND drone", max_results=500)
    _, expected, _ = provider.translate(query)
    _ = [d async for d in provider.search(query)]
    assert provider.client.calls[0][1] == expected


@pytest.mark.asyncio
async def test_openalex_snowball_pages_are_100():
    provider = OpenAlexProvider()
    provider.client = _Capture({"results": [], "meta": {"next_cursor": None}, "referenced_works": ["W1"]})
    _ = [d async for d in provider.get_citations("W9")]
    _ = [d async for d in provider.get_references("W9")]
    pages = [params.get("per-page") for _, params in provider.client.calls if "filter" in params]
    assert pages == [100, 100]


# --------------------------------------------------------------------------- Semantic Scholar key (researcher's addition A)


def _s2_leg(monkeypatch, key, status):
    from scholar_search.providers.semanticscholar import SemanticScholarProvider

    monkeypatch.setattr(settings, "s2_key", key)
    provider = SemanticScholarProvider()
    calls = []

    async def refuse(url, params=None, headers=None, **kwargs):
        calls.append(dict(headers or {}))
        raise ProviderError("semanticscholar", '{"message":"Forbidden"}', status_code=status)

    provider.client.get = refuse
    run = asyncio.run(SearchEngine(providers=[provider]).run(Query(text="weed AND drone"), dedup=False))
    return run.legs[0].to_dict(), calls


@pytest.mark.parametrize("status", [401, 403])
def test_a_rejected_s2_key_fails_the_leg_and_is_never_retried_keyless(monkeypatch, status):
    leg, calls = _s2_leg(monkeypatch, "s2-placeholder", status)
    assert calls == [{"x-api-key": "s2-placeholder"}]  # one keyed request, no keyless retry
    assert leg["status"] == "failed" and leg["error_code"] == "PROVIDER_REFUSED"
    assert any("rejected SCHOLAR_S2_KEY" in n and f"HTTP {status}" in n for n in leg["notes"]), leg["notes"]
    assert "s2-placeholder" not in json.dumps(leg)


def test_a_keyless_s2_refusal_says_it_was_keyless(monkeypatch):
    leg, calls = _s2_leg(monkeypatch, None, 403)
    assert calls == [{}]
    assert leg["error_code"] == "PROVIDER_REFUSED"
    assert any("keyless request" in n for n in leg["notes"]), leg["notes"]


def test_s2_uses_the_bulk_endpoint_and_sends_the_key_as_x_api_key(monkeypatch):
    from scholar_search.providers.semanticscholar import SemanticScholarProvider

    monkeypatch.setattr(settings, "s2_key", "s2-placeholder")
    provider = SemanticScholarProvider()
    assert provider.base_url.endswith("/graph/v1/paper/search/bulk")
    assert provider._get_headers() == {"x-api-key": "s2-placeholder"}
    _, request, _ = provider.translate(Query(text="weed AND drone"))
    assert "x-api-key" not in request and "api_key" not in request


# --------------------------------------------------------------------------- review findings (M3h-providers)


def test_a_dropped_tiab_term_is_not_reported_as_an_unapplied_tag():
    """A known tag whose term PubMed dropped (not found) is applied; only the drop is noted."""
    leg = _esearch_leg(
        {"esearchresult": {
            "querytranslation": '"drone"[Title/Abstract]',
            "errorlist": {"phrasesnotfound": ["zzqqxx"], "fieldsnotfound": []},
        }},
        "drone[tiab] OR zzqqxx[tiab]",
    )
    assert not any("did not apply" in n for n in leg.notes), leg.notes
    assert any('"zzqqxx"' in n and "left them out" in n for n in leg.notes), leg.notes


def test_the_golden_quoted_phrase_is_reported_as_searched_word_by_word():
    """Recorded golden answer (2026-11-08): PubMed split "herbicide prescription", it did not drop it."""
    body = json.loads((FIXTURES / "esearch_golden_uav_warnings.json").read_text(encoding="utf-8"))
    assert body["esearchresult"]["warninglist"]["quotedphrasesnotfound"] == ['"herbicide prescription"']
    term = (
        '(UAV OR drone) AND (weed OR "herbicide prescription") AND (mapping OR detection) AND 2020:2026[pdat]'
    )
    leg = _esearch_leg(body, term)
    assert leg.notes == [
        'PubMed found no exact match for the quoted phrase(s) "herbicide prescription"; '
        "it searched their words separately, all required (see PubMed's translation)"
    ]


def test_pubmed_stop_words_are_noted():
    leg = _esearch_leg(
        {"esearchresult": {
            "querytranslation": '"weed"[Title]',
            "warninglist": {"quotedphrasesnotfound": [], "phrasesignored": ["the"], "outputmessages": []},
        }},
        "weed[ti] AND the",
    )
    assert leg.notes == ['PubMed ignored the term(s) "the" (stop words); they were not searched']


@pytest.mark.asyncio
async def test_the_openalex_abstract_hydrator_asks_for_at_most_100():
    from unittest.mock import AsyncMock, MagicMock

    from scholar_search.enrichment import AbstractHydrator

    client = MagicMock()
    answer = MagicMock(status_code=200)
    answer.json.return_value = {"results": []}
    client.get = AsyncMock(return_value=answer)
    hydrator = AbstractHydrator(http_client=client)
    await hydrator._hydrate_from_openalex(["10.1/a", "10.1/b"])
    assert client.get.await_args.kwargs["params"]["per-page"] == 100


def test_the_s2_rate_limit_stays_below_one_request_per_second():
    """S2 keys allow 1 request per second across all endpoints; S2 asks for a limit below it."""
    from scholar_search.config import Settings
    from scholar_search.providers.semanticscholar import SemanticScholarProvider

    assert Settings.model_fields["rate_limit_s2"].default < 1.0
    assert SemanticScholarProvider().client.rate_limiter.rate < 1.0
