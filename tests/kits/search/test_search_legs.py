"""M3a-discovery D1/D2/D7: per-provider search legs, pagination, caps, contact email.

SRCH-30 / CORE-21: each provider leg records the executed query, the reported
total, the fetched count, the cap and the date.
SRCH-11 / SRCH-31: providers page to the reported total or the cap and say
when the cap stopped them; there is no hidden cap of 100.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from scholar_search.config import settings
from scholar_search.engine import ENGINE_CEILING, MailtoNotSet, SearchEngine
from scholar_search.models import Document, Query, SearchLeg
from scholar_search.providers.arxiv import ArxivProvider
from scholar_search.providers.base import BaseAPIProvider
from scholar_search.providers.crossref import CrossrefProvider
from scholar_search.providers.openalex import OpenAlexProvider
from scholar_search.providers.pubmed import PubMedProvider
from scholar_search.providers.semanticscholar import SemanticScholarProvider


@pytest.fixture(autouse=True)
def _mailto(monkeypatch):
    monkeypatch.setattr(settings, "mailto", "tester@example.org")


def _json(payload):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = payload
    return resp


def _text(text: str):
    resp = MagicMock()
    resp.status_code = 200
    resp.text = text
    resp.content = text.encode("utf-8")
    return resp


class _Recorder:
    """Replaces ``provider.client.get``; answers from a callable, keeps the params."""

    def __init__(self, answer):
        self.answer = answer
        self.calls: list[tuple[str, dict]] = []

    async def __call__(self, url, params=None, **kwargs):
        snapshot = dict(params or {})
        self.calls.append((url, snapshot))
        return self.answer(url, snapshot)


async def _run(provider, query):
    engine = SearchEngine(providers=[provider])
    run = await engine.run(query, dedup=False)
    await engine.close()
    return run


# --------------------------------------------------------------- Crossref


def _crossref_item(i: int) -> dict:
    return {"DOI": f"10.1/cr{i}", "title": [f"Crossref paper {i}"], "issued": {"date-parts": [[2020]]}}


@pytest.mark.asyncio
async def test_crossref_pages_with_cursor_to_reported_total():
    provider = CrossrefProvider()

    def answer(url, params):
        if params["cursor"] == "*":
            return _json({"message": {"total-results": 5, "next-cursor": "c2",
                                      "items": [_crossref_item(i) for i in range(3)]}})
        return _json({"message": {"total-results": 5, "next-cursor": "c3",
                                  "items": [_crossref_item(i) for i in range(3, 5)]}})

    provider.client.get = _Recorder(answer)
    run = await _run(provider, Query(text="weed AND drone", max_results=None))

    assert len(run.documents) == 5
    assert len(provider.client.get.calls) == 2
    leg = run.legs[0]
    assert isinstance(leg, SearchLeg)
    assert leg.provider == "crossref"
    assert leg.executed_query == provider.client.get.calls[0][1]["query"]
    assert leg.reported_total == 5
    assert leg.fetched == 5
    assert leg.cap == ENGINE_CEILING
    assert leg.cap_source == "engine_ceiling"
    assert leg.cap_hit is False
    assert leg.pages == 2
    assert leg.status == "ok"
    assert leg.started_at and leg.finished_at


@pytest.mark.asyncio
async def test_crossref_cap_hit_when_total_exceeds_cap():
    provider = CrossrefProvider()

    def answer(url, params):
        return _json({"message": {"total-results": 50, "next-cursor": "more",
                                  "items": [_crossref_item(i) for i in range(int(params["rows"]))]}})

    provider.client.get = _Recorder(answer)
    run = await _run(provider, Query(text="weed", max_results=4, cap_source="protocol"))

    leg = run.legs[0]
    assert leg.fetched == 4
    assert leg.cap == 4
    assert leg.cap_source == "protocol"
    assert leg.cap_hit is True


# --------------------------------------------------------------- PubMed


_PUBMED_ARTICLE = """<PubmedArticle><MedlineCitation><PMID>{pmid}</PMID><Article>
<ArticleTitle>PubMed paper {pmid}</ArticleTitle></Article></MedlineCitation></PubmedArticle>"""


@pytest.mark.asyncio
async def test_pubmed_pages_esearch_with_retstart():
    provider = PubMedProvider()
    provider.ESEARCH_PAGE = 2  # small pages for the test

    def answer(url, params):
        if "esearch" in url:
            start = int(params.get("retstart", 0))
            ids = [str(100 + i) for i in range(start, min(start + 2, 3))]
            return _json({"esearchresult": {"count": "3", "idlist": ids}})
        pmids = params["id"].split(",")
        body = "".join(_PUBMED_ARTICLE.format(pmid=p) for p in pmids)
        return _text(f"<?xml version='1.0'?><PubmedArticleSet>{body}</PubmedArticleSet>")

    provider.client.get = _Recorder(answer)
    run = await _run(provider, Query(text="weed", max_results=None))

    esearch = [p for u, p in provider.client.get.calls if "esearch" in u]
    assert [int(p.get("retstart", 0)) for p in esearch] == [0, 2]
    leg = run.legs[0]
    assert leg.reported_total == 3
    assert leg.fetched == 3
    assert leg.executed_query == esearch[0]["term"]
    assert leg.cap_hit is False


# --------------------------------------------------------------- arXiv


def _arxiv_feed(total: int, ids: list[int]) -> str:
    entries = "".join(
        f"<entry><id>http://arxiv.org/abs/2101.{i:05d}v1</id><title>arXiv paper {i}</title>"
        f"<published>2021-01-01T00:00:00Z</published><summary>s</summary></entry>"
        for i in ids
    )
    return (
        '<feed xmlns="http://www.w3.org/2005/Atom" '
        'xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">'
        f"<opensearch:totalResults>{total}</opensearch:totalResults>{entries}</feed>"
    )


@pytest.mark.asyncio
async def test_arxiv_pages_with_start_and_reads_total():
    provider = ArxivProvider()
    provider.PAGE_SIZE = 2

    def answer(url, params):
        start = int(params["start"])
        return _text(_arxiv_feed(3, list(range(start, min(start + 2, 3)))))

    provider.client.get = _Recorder(answer)
    run = await _run(provider, Query(text="weed", max_results=None))

    assert [int(p["start"]) for _, p in provider.client.get.calls] == [0, 2]
    leg = run.legs[0]
    assert leg.reported_total == 3
    assert leg.fetched == 3
    assert leg.executed_query == provider.client.get.calls[0][1]["search_query"]


# --------------------------------------------------------------- OpenAlex / S2


@pytest.mark.asyncio
async def test_openalex_reports_meta_count():
    provider = OpenAlexProvider()

    def answer(url, params):
        return _json({"meta": {"count": 1, "next_cursor": None},
                      "results": [{"id": "https://openalex.org/W1", "title": "OA paper",
                                   "publication_year": 2021, "ids": {}}]})

    provider.client.get = _Recorder(answer)
    run = await _run(provider, Query(text="weed AND drone", max_results=None))
    leg = run.legs[0]
    assert leg.reported_total == 1
    assert leg.fetched == 1
    assert "weed AND drone" in leg.executed_query
    assert "mailto" not in leg.request
    assert leg.mailto_set is True


@pytest.mark.asyncio
async def test_semanticscholar_reports_total():
    provider = SemanticScholarProvider()

    def answer(url, params):
        return _json({"total": 2, "token": None,
                      "data": [{"paperId": f"p{i}", "title": f"S2 paper {i}", "year": 2021}
                               for i in range(2)]})

    provider.client.get = _Recorder(answer)
    run = await _run(provider, Query(text="weed", max_results=None))
    leg = run.legs[0]
    assert leg.reported_total == 2
    assert leg.fetched == 2
    assert leg.executed_query == provider.client.get.calls[0][1]["query"]


# --------------------------------------------------------------- engine


class _Failing(BaseAPIProvider):
    def __init__(self):
        super().__init__(name="failing", rate_limit=0)

    async def search(self, query):
        self._record_executed("x", {"q": "x"})
        raise RuntimeError("boom")
        yield  # pragma: no cover


@pytest.mark.asyncio
async def test_failed_leg_is_recorded_not_swallowed():
    run = await _run(_Failing(), Query(text="x"))
    leg = run.legs[0]
    assert leg.status == "failed"
    assert "boom" in leg.error
    assert leg.fetched == 0


@pytest.mark.asyncio
async def test_search_all_still_returns_documents_and_keeps_legs():
    class _One(BaseAPIProvider):
        def __init__(self):
            super().__init__(name="one", rate_limit=0)

        async def search(self, query):
            self._record_executed("q", {})
            self._record_total(1)
            yield Document(title="Only", provider="one")

    engine = SearchEngine(providers=[_One()])
    docs = await engine.search_all(Query(text="q"), dedup=False)
    assert [d.title for d in docs] == ["Only"]
    assert engine.last_legs[0].reported_total == 1


def test_default_engine_excludes_biorxiv():
    """SRCH-13: bioRxiv drops boolean operators, so it is never a default."""
    names = {p.name for p in SearchEngine().providers}
    assert "biorxiv" not in names
    assert {"openalex", "crossref", "pubmed", "semanticscholar", "arxiv"} <= names


# --------------------------------------------------------------- contact email (D7)


@pytest.mark.asyncio
async def test_live_search_refuses_without_mailto(monkeypatch):
    monkeypatch.setattr(settings, "mailto", None)
    provider = CrossrefProvider()
    provider.client.get = _Recorder(lambda u, p: pytest.fail("no request may be sent"))
    engine = SearchEngine(providers=[provider])
    with pytest.raises(MailtoNotSet) as err:
        await engine.run(Query(text="weed"))
    assert err.value.code == "MAILTO_NOT_SET"
    assert "SCHOLAR_MAILTO" in str(err.value)


def test_settings_have_no_placeholder_mailto():
    from scholar_search.config import Settings

    assert Settings.model_fields["mailto"].default is None
