"""E2 (M3b-api): the check-only recall in ``scholar_search.recall``.

`docs/architecture/research_ui/DISCOVERY_API_PACKET.md` §4.2, decision 3: the
query is run as it is, never healed; a seed is found, not found, n/a or failed
per provider. The HTTP flow is in ``tests/console/test_discovery_api.py``.
"""

from __future__ import annotations

import asyncio

import pytest
from scholar_search.models import Document, ExternalIds, Query
from scholar_search.recall import SeedsInvalid, check_seeds, validate_seeds


class _Provider:
    def __init__(self, name, docs, fail=None):
        self.name, self.docs, self.fail, self.current_leg = name, docs, fail, None
        self.queries: list[Query] = []

    async def search(self, query):
        self.queries.append(query)
        if self.fail:
            raise self.fail
        for doc in self.docs:
            yield doc


class _NoVerifier:
    async def verify_document(self, doc):
        return False, doc, "unresolved"


def test_validate_seeds_bounds_and_shapes():
    assert validate_seeds([{"id": "10.1000/abc", "kind": "doi"}]) == [{"id": "10.1000/abc", "kind": "doi", "source": "you"}]
    assert validate_seeds([{"id": "arXiv:2301.00001v3", "kind": "arxiv", "source": "anchor"}])[0]["source"] == "anchor"
    for bad in ([], [{"id": "nope", "kind": "doi"}], [{"id": "10.1/x", "kind": "pmid"}],
                [{"id": "10.1/x", "kind": "doi", "source": "agent"}], [{"id": f"10.1/{i}", "kind": "doi"} for i in range(26)]):
        with pytest.raises(SeedsInvalid):
            validate_seeds(bad)


def test_the_query_is_run_as_it_is_with_the_cap():
    query = Query(text='"weed detection" AND uav', year_min=2020, max_results=None)
    openalex = _Provider("openalex", [Document(title="x", provider="openalex", external_ids=ExternalIds(doi="10.1/A"))])
    arxiv = _Provider("arxiv", [Document(title="y", provider="arxiv", external_ids=ExternalIds(arxiv_id="2301.00001"))])
    pubmed = _Provider("pubmed", [], fail=RuntimeError("down"))
    seeds = [
        {"id": "https://doi.org/10.1/a", "kind": "doi"},
        {"id": "10.48550/arXiv.2301.00001", "kind": "doi"},
        {"id": "2301.00001", "kind": "arxiv"},
    ]
    check = asyncio.run(check_seeds(query, seeds, [openalex, arxiv, pubmed], 50, verifier=_NoVerifier()))

    for provider in (openalex, arxiv, pubmed):
        assert [q.text for q in provider.queries] == [query.text]
        assert provider.queries[0].max_results == 50
    assert query.max_results is None  # the caller's query is not changed
    rows = {row["id"]: row["per_provider"] for row in check["seeds"]}
    assert rows["https://doi.org/10.1/a"] == {"openalex": "found", "arxiv": "n/a", "pubmed": "failed"}
    assert rows["10.48550/arXiv.2301.00001"] == {"openalex": "not_found", "arxiv": "found", "pubmed": "failed"}
    assert rows["2301.00001"] == {"openalex": "not_found", "arxiv": "found", "pubmed": "n/a"}
    assert check["found"] == 3 and check["missed_everywhere"] == []
    assert {leg["provider"]: leg["status"] for leg in check["legs"]}["pubmed"] == "failed"


class _MustNotCall:
    async def verify_document(self, doc):
        raise AssertionError("a stopped check sent a title lookup")


def test_a_stopped_check_sends_no_title_lookup():
    provider = _Provider("openalex", [Document(title="x", provider="openalex", external_ids=ExternalIds(doi="10.1/a"))])
    check = asyncio.run(check_seeds(Query(text="uav"), [{"id": "10.1/a", "kind": "doi"}], [provider], 10,
                                    verifier=_MustNotCall(), should_stop=lambda: True))
    assert check["seeds"][0]["title_check"] == "unresolved"
