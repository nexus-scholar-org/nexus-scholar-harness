"""M3a-discovery D3: the executed query is reported and never changed silently.

SRCH-12: arXiv compaction is reported on the leg, and never turns a NOT term
into a required one.
SRCH-14: PubMed field tags are built from parsed tokens, not a regex over the
translated string.
"""

from __future__ import annotations

import pytest
from scholar_search.config import settings
from scholar_search.engine import SearchEngine
from scholar_search.models import Query
from scholar_search.providers.arxiv import ArxivProvider
from scholar_search.providers.pubmed import PubMedProvider


@pytest.fixture(autouse=True)
def _mailto(monkeypatch):
    monkeypatch.setattr(settings, "mailto", "tester@example.org")


class _Capture:
    def __init__(self, response):
        self.calls: list[dict] = []
        self.response = response

    async def get(self, url, params=None, **kwargs):
        self.calls.append(dict(params or {}))
        return self.response


class _Empty:
    status_code = 200
    text = ""
    content = b""

    def json(self):
        return {"esearchresult": {"count": "0", "idlist": []}}


_LONG = (
    '("unmanned aerial vehicle" OR drone OR uav) AND ("weed detection" OR weed OR weeds)'
    ' AND ("deep learning" OR cnn OR "convolutional neural network" OR segmentation'
    ' OR "semantic segmentation" OR "object detection") AND (crop OR field OR agriculture'
    ' OR "precision agriculture" OR "site-specific weed management")'
)


async def _arxiv_leg(query_text: str):
    provider = ArxivProvider()
    provider.client = _Capture(_Empty())
    engine = SearchEngine(providers=[provider])
    run = await engine.run(Query(text=query_text, id="Q1"), dedup=False)
    return provider.client.calls[0]["search_query"], run.legs[0]


@pytest.mark.asyncio
async def test_arxiv_compaction_is_reported_on_the_leg():
    sent, leg = await _arxiv_leg(_LONG)
    assert leg.executed_query == sent
    assert any("compacted" in note for note in leg.notes), leg.notes
    # The note names what was dropped, e.g. the multi-word phrases.
    assert any("deep learning" in note for note in leg.notes), leg.notes


@pytest.mark.asyncio
async def test_arxiv_short_query_has_no_compaction_note():
    sent, leg = await _arxiv_leg("weed AND drone")
    assert leg.executed_query == sent
    assert not any("compacted" in note for note in leg.notes)


@pytest.mark.asyncio
async def test_arxiv_compaction_never_makes_a_not_term_required():
    text = _LONG + " AND NOT survey"
    sent, leg = await _arxiv_leg(text)
    # "survey" may only appear negated (ANDNOT), never as a required/OR'ed term.
    assert "all:survey" not in sent.replace("ANDNOT all:survey", "")
    assert leg.executed_query == sent


@pytest.mark.asyncio
async def test_pubmed_field_phrase_is_tagged_as_a_phrase():
    provider = PubMedProvider()
    provider.client = _Capture(_Empty())
    engine = SearchEngine(providers=[provider])
    run = await engine.run(Query(text='ti:"deep learning" AND weed', id="Q1"), dedup=False)
    term = provider.client.calls[0]["term"]
    assert term == '"deep learning"[ti] AND weed'
    assert run.legs[0].executed_query == term


@pytest.mark.asyncio
async def test_pubmed_leaves_colons_inside_phrases_alone():
    provider = PubMedProvider()
    provider.client = _Capture(_Empty())
    engine = SearchEngine(providers=[provider])
    await engine.run(Query(text='"weed: a review" OR herbicide', id="Q1"), dedup=False)
    term = provider.client.calls[0]["term"]
    assert term == '"weed: a review" OR herbicide'


@pytest.mark.asyncio
async def test_arxiv_and_not_becomes_andnot_but_or_not_is_left_alone():
    sent, _ = await _arxiv_leg("weed AND NOT survey")
    assert "ANDNOT all:survey" in sent and "AND ANDNOT" not in sent
    sent, _ = await _arxiv_leg("weed OR NOT survey")
    assert "OR ANDNOT" in sent
