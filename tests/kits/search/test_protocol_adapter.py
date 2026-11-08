from pathlib import Path
from typer.testing import CliRunner

from scholar_search.cli import app
from scholar_search.protocol_adapter import compile_protocol_search

runner = CliRunner()


def test_compile_protocol_search_minimal_dict():
    protocol_dict = {
        "protocol_id": "proto-test-01",
        "search_strategy": {
            "core_concepts": [
                {
                    "concept": "Code Generation",
                    "synonyms": ["code synthesis", "program synthesis"],
                    "boolean_operator": "OR",
                },
                {
                    "concept": "Evaluation",
                    "synonyms": ["benchmarks"],
                    "boolean_operator": "OR",
                },
            ],
            "date_range": {
                "start_year": 2021,
                "end_year": 2025,
            },
            "languages": ["en"],
            "target_candidate_pool_size": {
                "min": 50,
                "max": 300,
            },
            "target_databases": ["openalex", "arxiv"],
        },
    }

    query, providers = compile_protocol_search(protocol_dict)

    assert query.id == "proto-test-01"
    assert '("Code Generation" OR "code synthesis" OR "program synthesis")' in query.text
    assert "(Evaluation OR benchmarks)" in query.text
    assert " AND " in query.text
    assert query.year_min == 2021
    assert query.year_max == 2025
    assert query.max_results is None  # SRCH-31: the pool size is advisory
    assert providers == ["openalex", "arxiv"]


def test_compile_protocol_search_valid_fixture(tmp_path: Path):
    fixture_json = """{
      "protocol_id": "proto-ds-01",
      "metadata": {"title": "Test Title"},
      "search_strategy": {
        "core_concepts": [
          {
            "concept": "Quantum",
            "synonyms": []
          }
        ],
        "date_range": {"start_year": 2020, "end_year": 2024},
        "target_databases": ["crossref"]
      }
    }"""
    file_path = tmp_path / "protocol.json"
    file_path.write_text(fixture_json, encoding="utf-8")

    query, providers = compile_protocol_search(file_path)
    assert query.text == "Quantum"
    assert query.year_min == 2020
    assert query.year_max == 2024
    assert providers == ["crossref"]


def test_cli_search_with_protocol_option(tmp_path: Path):
    fixture_json = """{
      "protocol_id": "proto-ds-01",
      "metadata": {"title": "Test Title"},
      "search_strategy": {
        "core_concepts": [{"concept": "attention"}],
        "date_range": {"start_year": 2017, "end_year": 2020},
        "target_databases": []
      }
    }"""
    file_path = tmp_path / "protocol.json"
    file_path.write_text(fixture_json, encoding="utf-8")

    # If target_databases is empty, cli falls back to default suite
    # We pass an invalid provider so search returns quickly without network
    result = runner.invoke(app, ["search", "--protocol", str(file_path), "--provider", "nonexistent"])
    assert result.exit_code != 0
    assert "Unknown provider" in result.output


# M3a-discovery SRCH-31: target_candidate_pool_size is advisory, never a cap.
def test_target_pool_max_is_not_the_retrieval_cap():
    protocol = {
        "protocol_id": "p1",
        "search_strategy": {
            "core_concepts": [{"concept": "weed", "synonyms": []}],
            "target_candidate_pool_size": {"min": 50, "max": 300},
        },
    }
    query, _ = compile_protocol_search(protocol)
    assert query.max_results is None


def test_no_hidden_default_cap_of_100():
    protocol = {"protocol_id": "p1", "search_strategy": {"core_concepts": [{"concept": "weed", "synonyms": []}]}}
    query, _ = compile_protocol_search(protocol)
    assert query.max_results is None


def test_method_retrieval_cap_is_the_cap_and_names_the_protocol():
    protocol = {
        "protocol_id": "p1",
        "search_strategy": {"core_concepts": [{"concept": "weed", "synonyms": []}]},
        "method": {"retrieval_cap": 250},
    }
    query, _ = compile_protocol_search(protocol)
    assert query.max_results == 250
    assert query.cap_source == "protocol"


def test_protocol_default_databases_exclude_biorxiv():
    protocol = {"protocol_id": "p1", "search_strategy": {"core_concepts": [{"concept": "weed", "synonyms": []}]}}
    _, providers = compile_protocol_search(protocol)
    assert "biorxiv" not in providers
