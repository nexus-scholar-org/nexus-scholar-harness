"""E1, the plan dry run (M3d-engine; discovery API packet §4.1)."""

from __future__ import annotations

import json

import pytest
from scholar_search.models import Query
from scholar_search.plan import compile_plan, leg_query


def _protocol(tmp_path, databases):
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps({
        "protocol_id": "P-1",
        "search_strategy": {
            "core_concepts": [
                {"concept": "unmanned aerial vehicle", "synonyms": ["drone"], "boolean_operator": "OR"},
                {"concept": "weed", "synonyms": ["weed mapping"], "boolean_operator": "OR"},
            ],
            "date_range": {"start_year": 2018, "end_year": 2025},
            "target_databases": databases,
        },
    }), encoding="utf-8")
    return path


def test_a_database_the_protocol_does_not_select_is_reported_not_translated(tmp_path):
    plan = compile_plan(_protocol(tmp_path, ["openalex", "Semantic Scholar"]))
    rows = {r["name"]: r for r in plan["providers"]}
    assert [r["name"] for r in plan["providers"]] == ["openalex", "semanticscholar", "crossref", "arxiv", "pubmed", "biorxiv"]
    assert rows["openalex"]["status"] == rows["semanticscholar"]["status"] == "translated"
    assert rows["crossref"]["status"] == "not_selected" and rows["crossref"]["executed_query"] is None
    assert rows["biorxiv"]["status"] == "off_by_default" and rows["biorxiv"]["request"] is None


@pytest.mark.parametrize("name", ["openalex", "semanticscholar", "crossref", "arxiv", "pubmed"])
def test_translate_sends_nothing_and_search_records_the_same_string(name, monkeypatch):
    from scholar_search.plan import _provider

    provider = _provider(name)
    sent = []

    async def refuse(*args, **kwargs):
        sent.append((args, kwargs))
        raise RuntimeError("stop after the first request")

    monkeypatch.setattr(provider.client, "get", refuse)
    query = leg_query(Query(text='("unmanned aerial vehicle" OR drone) AND weed', year_min=2018, year_max=2025))
    executed, request, notes = provider.translate(query)
    assert sent == [] and executed

    from scholar_search.models import SearchLeg

    provider.current_leg = SearchLeg(provider=name, query_id=query.id)
    import asyncio

    async def drain():
        async for _ in provider.search(query):
            pass

    with pytest.raises(RuntimeError):
        asyncio.run(drain())
    assert provider.current_leg.executed_query == executed
    assert provider.current_leg.notes[: len(notes)] == notes
