"""M3h-c: the arXiv leg sends its year range as a ``submittedDate`` clause (F16).

arXiv's user manual documents ``submittedDate:[YYYYMMDDTTTT TO YYYYMMDDTTTT]``
(GMT, to the minute) inside ``search_query``. These tests are offline: they
read what ``ArxivProvider.translate`` builds and what the leg records. The
live syntax is confirmed by the researcher's re-record of the golden cassettes
(``docs/roadmap/milestones/M3h-c-arxiv-date.md``).
"""

from __future__ import annotations

import asyncio

import httpx
import pytest

from scholar_search.http_client import reset_host_budgets
from scholar_search.models import Query, SearchLeg
from scholar_search.providers.arxiv import ArxivProvider

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
  <opensearch:totalResults>2</opensearch:totalResults>
  <entry><id>http://arxiv.org/abs/2101.00001v1</id><title>In range</title>
    <published>2021-01-02T00:00:00Z</published></entry>
  <entry><id>http://arxiv.org/abs/1801.00001v1</id><title>Before the range</title>
    <published>2018-01-02T00:00:00Z</published></entry>
</feed>"""


@pytest.fixture(autouse=True)
def _budgets():
    reset_host_budgets()
    yield
    reset_host_budgets()


def test_a_year_range_is_sent_as_a_submitted_date_clause():
    sent, params, _ = ArxivProvider().translate(Query(text="drone AND weed", year_min=2020, year_max=2026))
    clause = "submittedDate:[202001010000 TO 202612312359]"
    assert sent.endswith(f" AND {clause}")
    assert params["search_query"] == sent
    assert sent.count("submittedDate") == 1
    # the topic part is the unchanged translation, grouped so AND binds to all of it
    bare, _, _ = ArxivProvider().translate(Query(text="drone AND weed"))
    assert sent == f"({bare}) AND {clause}"


def test_a_query_without_a_year_range_carries_no_clause():
    for query in (Query(text="drone AND weed"), Query(text="drone", year_min=None, year_max=None)):
        sent, params, notes = ArxivProvider().translate(query)
        assert "submittedDate" not in sent
        assert "submittedDate" not in params["search_query"]
        assert not any("submittedDate" in n for n in notes)
        assert not any("year" in r for r in ArxivProvider().cannot_express(query))


def test_an_open_ended_range_gets_a_fixed_bound():
    low, _, _ = ArxivProvider().translate(Query(text="drone", year_min=2020))
    high, _, _ = ArxivProvider().translate(Query(text="drone", year_max=2026))
    assert low.endswith("submittedDate:[202001010000 TO 999912312359]")
    assert high.endswith("submittedDate:[199101010000 TO 202612312359]")


def test_the_clause_is_added_after_compaction_and_once():
    long_text = " AND ".join(
        "(" + " OR ".join(f'"longterm{c}{i}"' for i in range(6)) + ")" for c in "abc"
    )
    plain, _, plain_notes = ArxivProvider().translate(Query(text=long_text))
    assert any("compacted" in n for n in plain_notes)  # the case does compact
    sent, _, notes = ArxivProvider().translate(Query(text=long_text, year_min=2020, year_max=2026))
    assert sent == f"({plain}) AND submittedDate:[202001010000 TO 202612312359]"
    assert any("compacted" in n for n in notes)


def test_the_leg_note_says_the_range_was_sent():
    _, _, notes = ArxivProvider().translate(Query(text="drone", year_min=2020, year_max=2026))
    note = next(n for n in notes if "submittedDate" in n)
    assert "was not sent" not in note
    assert "2020" in note and "2026" in note
    assert "sent" in note
    reasons = ArxivProvider().cannot_express(Query(text="drone", year_min=2020, year_max=2026))
    assert not any("year" in r for r in reasons)


def test_the_leg_records_the_clause_in_its_executed_query_and_request():
    provider = ArxivProvider()
    provider.client.client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, text=FEED))
    )
    provider.current_leg = SearchLeg(provider="arxiv", query_id="q")
    query = Query(text="drone", year_min=2020, year_max=2026)

    async def run():
        return [doc async for doc in provider.search(query)]

    docs = asyncio.run(run())
    leg = provider.current_leg
    assert "submittedDate:[202001010000 TO 202612312359]" in leg.executed_query
    assert "submittedDate:[202001010000 TO 202612312359]" in leg.request["search_query"]
    assert any("submittedDate" in n and "was not sent" not in n for n in leg.notes)
    # the local year check stays as a guard: the 2018 record is dropped even if arXiv returned it
    assert [d.title for d in docs] == ["In range"]
