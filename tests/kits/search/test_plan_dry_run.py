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


def test_without_a_choice_the_protocol_selects_as_before(tmp_path):
    plan = compile_plan(_protocol(tmp_path, ["crossref", "openalex"]), selected=None)
    assert [r["name"] for r in plan["providers"]] == ["openalex", "semanticscholar", "crossref", "arxiv", "pubmed", "biorxiv"]
    assert [r["name"] for r in plan["providers"] if r["selected"]] == ["openalex", "crossref"]


def test_a_chosen_list_is_listed_first_in_its_order_and_replaces_the_protocols(tmp_path):
    """M10a (decision 2026-11-14 item 2a): the run's choice, not the protocol's, is translated."""
    path = _protocol(tmp_path, ["openalex", "Semantic Scholar"])
    default = {r["name"]: r for r in compile_plan(path)["providers"]}
    plan = compile_plan(path, selected=["pubmed", "Semantic Scholar"])
    assert [r["name"] for r in plan["providers"]] == ["pubmed", "semanticscholar", "openalex", "crossref", "arxiv", "biorxiv"]
    rows = {r["name"]: r for r in plan["providers"]}
    assert rows["pubmed"]["selected"] is True and rows["pubmed"]["status"] == "translated"
    assert rows["semanticscholar"]["executed_query"] == default["semanticscholar"]["executed_query"]
    assert rows["openalex"]["selected"] is False and rows["openalex"]["status"] == "not_selected"
    assert rows["openalex"]["executed_query"] is None
    assert rows["biorxiv"]["status"] == "off_by_default"


def test_a_chosen_row_is_the_providers_own_translation_of_the_protocol_query(tmp_path):
    """The row is translate() of the protocol query; the API test compares it with a run's leg."""
    from scholar_search.plan import _provider, translate_provider
    from scholar_search.protocol_adapter import compile_protocol_search

    path = _protocol(tmp_path, ["openalex"])
    rows = {r["name"]: r for r in compile_plan(path, selected=["arxiv", "pubmed"])["providers"]}
    query, _ = compile_protocol_search(path)
    for name in ("arxiv", "pubmed"):
        expected = translate_provider(_provider(name), query)
        assert rows[name]["executed_query"] == expected["executed_query"]
        assert rows[name]["request"] == expected["request"]


def test_a_chosen_database_without_a_dry_run_says_so(tmp_path):
    rows = {r["name"]: r for r in compile_plan(_protocol(tmp_path, ["openalex"]), selected=["biorxiv"])["providers"]}
    assert rows["biorxiv"]["selected"] is True and rows["biorxiv"]["status"] == "selected"
    assert rows["biorxiv"]["executed_query"] is None and rows["biorxiv"]["notes"]


def test_an_explicit_empty_list_selects_what_the_engine_falls_back_to(tmp_path):
    """target_databases: [] runs the engine's default suite, so the plan selects and translates those."""
    from scholar_search.plan import DEFAULT_PROVIDERS

    plan = compile_plan(_protocol(tmp_path, []))
    assert [r["name"] for r in plan["providers"] if r["selected"]] == list(DEFAULT_PROVIDERS)
    assert all(r["status"] == "translated" for r in plan["providers"] if r["selected"])


def test_run_providers_is_the_list_a_run_searches():
    from scholar_search.plan import DEFAULT_PROVIDERS, run_providers

    assert run_providers(["Semantic Scholar", "scopus", "crossref", "semantic_scholar"]) == ["semanticscholar", "crossref"]
    assert run_providers([]) == run_providers(None) == run_providers(["scopus"]) == list(DEFAULT_PROVIDERS)


def test_the_engine_default_suite_is_the_plans_default_list():
    """run_providers' fallback names exactly what SearchEngine() builds when it is given no providers."""
    import asyncio

    from scholar_search.engine import SearchEngine
    from scholar_search.plan import DEFAULT_PROVIDERS

    engine = SearchEngine()
    try:
        assert tuple(p.name for p in engine.providers) == DEFAULT_PROVIDERS
    finally:
        asyncio.run(engine.close())  # each provider's HTTP client, never used


def test_the_protocol_default_is_the_adapters():
    from scholar_search.plan import protocol_default_providers
    from scholar_search.protocol_adapter import compile_protocol_search

    assert protocol_default_providers() == ["openalex", "semanticscholar", "crossref", "arxiv"]
    assert protocol_default_providers() == compile_protocol_search({"search_strategy": {}})[1]


def test_a_database_chosen_twice_is_listed_once(tmp_path):
    plan = compile_plan(_protocol(tmp_path, ["openalex"]), selected=["crossref", "crossref"])
    assert [r["name"] for r in plan["providers"]].count("crossref") == 1


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
