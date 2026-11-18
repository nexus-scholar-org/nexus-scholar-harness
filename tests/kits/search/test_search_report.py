"""PRISMA-S transparency of a run's database choice (M10a, decision 2026-11-14 item 2a).

When a run was asked for its own list (``requested_providers``), the search
report and the methods paragraph name the protocol databases that list left
out; a run that used the protocol's list says nothing more than before.
"""

from __future__ import annotations

from scholar_search.search_report import (
    protocol_databases_left_out,
    render_methods_text,
    render_search_report,
)

FIVE = ["arxiv", "crossref", "openalex", "pubmed", "semanticscholar"]  # as protocol_search records them: sorted


def _leg(provider: str) -> dict:
    return {"provider": provider, "executed_query": "q", "reported_total": 3, "fetched": 3, "cap": 10000,
            "cap_source": "engine_ceiling", "cap_hit": False, "status": "ok", "started_at": "2026-11-14T10:00:00"}


def _manifest(requested, databases=FIVE) -> dict:
    return {"run": "run_001", "status": "SUCCESS", "query_text": "q", "requested_providers": requested,
            "protocol_search": {"databases": databases}, "legs": [_leg(n) for n in (requested or ["openalex"])]}


def test_the_databases_left_out_are_listed_in_the_known_order():
    manifest = _manifest(["pubmed", "openalex"])
    assert protocol_databases_left_out(manifest) == ["semanticscholar", "crossref", "arxiv"]


def test_a_protocol_without_a_list_leaves_out_from_the_adapter_default():
    assert protocol_databases_left_out(_manifest(["semanticscholar"], databases=None)) == ["openalex", "crossref", "arxiv"]


def test_an_explicit_empty_protocol_list_leaves_out_from_the_engine_default():
    left = protocol_databases_left_out(_manifest(["crossref"], databases=[]))
    assert left == ["openalex", "semanticscholar", "arxiv", "pubmed"]


def test_nothing_is_left_out_without_a_choice_or_a_record():
    assert protocol_databases_left_out(_manifest(None)) == []
    assert protocol_databases_left_out({"requested_providers": ["crossref"], "legs": []}) == []
    assert protocol_databases_left_out({"requested_providers": ["crossref"], "legs": []},
                                       fallback=["openalex", "crossref"]) == ["openalex"]


def test_the_search_report_names_the_databases_left_out_for_this_run():
    text = render_search_report(_manifest(["pubmed", "openalex"]))
    lines = [line for line in text.splitlines() if "not selected for this run" in line]
    assert lines == ["- Protocol databases not selected for this run: semanticscholar, crossref and arxiv"]


def test_the_search_report_is_unchanged_without_a_choice():
    assert "not selected for this run" not in render_search_report(_manifest(None))
    assert "not selected for this run" not in render_search_report(_manifest(["openalex", "crossref"] + FIVE))


def test_the_methods_text_names_the_databases_left_out_for_this_run():
    legs = [_leg("pubmed"), _leg("openalex")]
    text = render_methods_text(legs, not_selected_for_run=["semanticscholar", "crossref", "arxiv"])
    assert ("The protocol also names semanticscholar, crossref and arxiv, which were not selected for this run."
            in text)
    assert text.index("We searched 2 databases") < text.index("The protocol also names")


def test_the_methods_text_names_one_database_left_out_in_the_singular():
    legs = [_leg("pubmed"), _leg("openalex")]
    text = render_methods_text(legs, not_selected_for_run=["arxiv"])
    assert "The protocol also names arxiv, which was not selected for this run." in text
    assert "which were" not in text


def test_the_methods_text_is_unchanged_without_a_choice():
    legs = [_leg("pubmed"), _leg("openalex")]
    assert render_methods_text(legs) == render_methods_text(legs, not_selected_for_run=[])
    assert "not selected for this run" not in render_methods_text(legs)
