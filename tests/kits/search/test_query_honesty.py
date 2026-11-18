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
async def test_arxiv_compaction_never_makes_a_lower_case_not_term_required():
    # The parser reads lower-case and/or/not as operators, so the compaction
    # gates must too: "and not survey" is a negation, never a required term.
    sent, leg = await _arxiv_leg(_LONG + " and not survey")
    assert sent.endswith("ANDNOT all:survey")
    assert "all:survey" not in sent.replace("ANDNOT all:survey", "")
    assert any("not compacted" in note for note in leg.notes), leg.notes
    assert leg.executed_query == sent


@pytest.mark.asyncio
async def test_arxiv_compaction_splits_clauses_on_a_lower_case_and():
    # A lower-case "and" joins clauses as the upper-case one does; an "and"
    # inside a phrase is part of the phrase, not a clause boundary.
    upper, _ = await _arxiv_leg(_LONG)
    lower, leg = await _arxiv_leg(_LONG.replace(" AND ", " and "))
    assert lower == upper
    assert any("compacted from" in note for note in leg.notes), leg.notes
    sent, _ = await _arxiv_leg(_LONG + ' AND ("research and development" OR rnd)')
    assert sent.endswith(" AND (all:rnd)")


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


@pytest.mark.asyncio
async def test_arxiv_joins_adjacent_terms_with_and():
    # OBS-3: arXiv reads adjacent terms as OR; the manual gives no default operator.
    sent, leg = await _arxiv_leg("UAV crop weed mapping")
    assert sent == "all:UAV AND all:crop AND all:weed AND all:mapping"
    assert leg.executed_query == sent


@pytest.mark.asyncio
async def test_arxiv_implicit_and_with_groups_phrases_and_not():
    sent, leg = await _arxiv_leg('(drone OR UAV) weed "crop row" NOT survey')
    assert sent == '( all:drone OR all:UAV ) AND all:weed AND all:"crop row" ANDNOT all:survey'
    assert leg.executed_query == sent


@pytest.mark.asyncio
async def test_arxiv_explicit_operators_are_unchanged():
    sent, _ = await _arxiv_leg("weed AND drone")
    assert sent == "all:weed AND all:drone"
    sent, _ = await _arxiv_leg("weed OR drone")
    assert sent == "all:weed OR all:drone"
    sent, _ = await _arxiv_leg("weed AND NOT survey")
    assert sent == "all:weed ANDNOT all:survey"
    sent, _ = await _arxiv_leg('ti:"row spacing" OR (weed AND drone)')
    assert sent == 'ti:"row spacing" OR ( all:weed AND all:drone )'


@pytest.mark.asyncio
async def test_arxiv_unparenthesised_or_mixed_with_adjacency_is_sent_flat():
    # No brackets are added: arXiv nests a flat chain to the right, so these
    # read as a AND (b OR c) and drone OR (UAV AND weed).
    sent, leg = await _arxiv_leg("a b OR c")
    assert sent == "all:a AND all:b OR all:c"
    assert leg.executed_query == sent
    sent, leg = await _arxiv_leg("drone OR UAV weed")
    assert sent == "all:drone OR all:UAV AND all:weed"
    assert leg.executed_query == sent


@pytest.mark.asyncio
async def test_arxiv_typed_andnot_is_its_negation_not_a_required_word():
    sent, leg = await _arxiv_leg("a ANDNOT b")
    assert sent == "all:a ANDNOT all:b"
    assert leg.executed_query == sent
    sent, _ = await _arxiv_leg("weed AND ANDNOT survey")
    assert sent == "all:weed ANDNOT all:survey"
    sent, _ = await _arxiv_leg("(drone OR UAV) andnot (survey OR review)")
    assert sent == "( all:drone OR all:UAV ) ANDNOT ( all:survey OR all:review )"
    # Inside a phrase, or as part of a longer word, it is left as written.
    sent, _ = await _arxiv_leg('"a ANDNOT b" weed-ANDNOT')
    assert sent == 'all:"a ANDNOT b" AND all:weed-ANDNOT'


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "typed, expected",
    [
        ("(a)ANDNOT(b)", "( all:a ) ANDNOT ( all:b )"),
        ("(a) ANDNOT (b)", "( all:a ) ANDNOT ( all:b )"),
        ("(a)ANDNOT (b)", "( all:a ) ANDNOT ( all:b )"),
        ("(a) ANDNOT(b)", "( all:a ) ANDNOT ( all:b )"),
        ("a ANDNOT(b)", "all:a ANDNOT ( all:b )"),
        ("(a)ANDNOT b", "( all:a ) ANDNOT all:b"),
        ("(a OR b)andnot(c)", "( all:a OR all:b ) ANDNOT ( all:c )"),
    ],
)
async def test_arxiv_typed_andnot_next_to_a_bracket_is_its_negation(typed, expected):
    sent, leg = await _arxiv_leg(typed)
    assert sent == expected
    assert leg.executed_query == sent


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "typed, expected",
    [
        ("weed ti:ANDNOT", "all:weed AND ti:ANDNOT"),
        ("ti:ANDNOT b", "ti:ANDNOT AND all:b"),
        ("ti: ANDNOT b", "ti:ANDNOT AND all:b"),
    ],
)
async def test_arxiv_andnot_after_a_field_is_a_term_of_that_field(typed, expected):
    # The parser reads the word after a field prefix as that field's term, so
    # ti:ANDNOT is a title term, not the operator: it is sent as written.
    sent, leg = await _arxiv_leg(typed)
    assert sent == expected
    assert leg.executed_query == sent


@pytest.mark.asyncio
async def test_arxiv_typed_andnot_after_an_unbalanced_quote_is_its_negation():
    # The parser reads an unclosed quote as part of a word, not as a phrase,
    # so the ANDNOT after it is the operator, never a required word.
    sent, leg = await _arxiv_leg('"b ANDNOT c')
    assert sent == 'all:"b ANDNOT all:c'
    assert leg.executed_query == sent
    # A quote inside a word does not open a phrase either.
    sent, _ = await _arxiv_leg('x"y ANDNOT z"')
    assert sent == 'all:x"y ANDNOT all:z"'


@pytest.mark.asyncio
async def test_arxiv_typed_andnot_keeps_a_long_query_from_compaction():
    sent, leg = await _arxiv_leg(_LONG + " ANDNOT survey")
    assert sent.endswith("ANDNOT all:survey")
    assert "all:survey" not in sent.replace("ANDNOT all:survey", "")
    assert any("not compacted" in note for note in leg.notes), leg.notes


def test_other_providers_still_read_andnot_as_a_word():
    pubmed = PubMedProvider()
    term, _, _ = pubmed.translate(Query(text="a ANDNOT b"))
    assert term == "a ANDNOT b"


_ADJACENT = (
    '(drone OR UAV OR UAS OR quadcopter OR multirotor OR "unmanned aircraft") AND unmanned'
    " aerial vehicle multispectral orthomosaic imagery weed crop row detection segmentation"
    " classification"
)


@pytest.mark.asyncio
async def test_arxiv_compaction_counts_the_implicit_ands():
    # 260 characters with spaces alone; the implicit ANDs bring it to 304,
    # which crosses the 300-character threshold. Compaction then ORs the
    # adjacent terms of a clause and keeps the first six.
    sent, leg = await _arxiv_leg(_ADJACENT)
    assert sent == (
        "(all:drone OR all:UAV OR all:UAS OR all:quadcopter OR all:multirotor) AND"
        " (all:unmanned OR all:aerial OR all:vehicle OR all:multispectral"
        " OR all:orthomosaic OR all:imagery)"
    )
    assert leg.executed_query == sent
    assert leg.notes == [
        "arXiv query compacted from 304 characters to 172: multi-word phrases dropped,"
        " at most 6 single tokens kept per clause and joined with OR;"
        ' dropped phrases: "unmanned aircraft"'
    ]
