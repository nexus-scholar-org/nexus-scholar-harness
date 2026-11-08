"""M3a-discovery D1 (harness half): SRCH-30 / CORE-21.

The discovery stage journals one leg per database (executed query, reported
total, fetched count, cap, cap_hit, dates) and keeps every run's raw records
and legs in a run-numbered folder that is never overwritten.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from scholar_search.config import settings
from scholar_search.engine import SearchEngine
from scholar_search.models import Document, ExternalIds
from scholar_search.providers.base import BaseAPIProvider

from scholar_harness.pipeline import discovery as disc

from test_discovery_stage import _write_protocol


@pytest.fixture(autouse=True)
def _mailto(monkeypatch):
    monkeypatch.setattr(settings, "mailto", "tester@example.org")


class _StubProvider(BaseAPIProvider):
    def __init__(self, name: str, titles: list[str], total: int):
        super().__init__(name=name, rate_limit=0)
        self.titles = titles
        self.total = total

    async def search(self, query):
        self._record_executed(f"{self.name}::{query.text}", {"q": query.text, "mailto": "x"})
        self._record_total(self.total)
        self._record_page()
        for i, title in enumerate(self.titles):
            yield Document(
                title=title,
                year=2024,
                provider=self.name,
                provider_id=f"{self.name}-{i}",
                external_ids=ExternalIds(doi=f"10.1/{self.name}{i}"),
            )


def _engine_factory(titles_by_provider: dict[str, list[str]], totals: dict[str, int]):
    def factory(providers=None):
        return SearchEngine(
            providers=[_StubProvider(n, t, totals[n]) for n, t in titles_by_provider.items()]
        )

    return factory


def _workspace(tmp_path: Path) -> tuple[Path, Path]:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"project_id": "ws", "title": "T", "stats": {}}), encoding="utf-8"
    )
    return ws, _write_protocol(ws)


def _events(ws: Path) -> list[dict]:
    lines = (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_the_journal_records_one_leg_per_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        disc,
        "SearchEngine",
        _engine_factory({"openalex": ["A", "B"], "crossref": ["C"]}, {"openalex": 2, "crossref": 40}),
    )
    ws, proto = _workspace(tmp_path)

    asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=ws / "literature",
                                   max_search_results=1))

    event = [e for e in _events(ws) if e["action"] == "DISCOVERY_SEARCH"][-1]
    legs = {leg["provider"]: leg for leg in event["parameters"]["legs"]}
    assert set(legs) == {"openalex", "crossref"}
    cr = legs["crossref"]
    assert cr["executed_query"].startswith("crossref::")
    assert cr["reported_total"] == 40
    assert cr["fetched"] == 1
    assert cr["cap"] == 1
    assert cr["cap_source"] == "run_override"
    assert cr["cap_hit"] is True
    assert cr["started_at"] and cr["finished_at"]
    assert "mailto" not in cr["request"]
    assert legs["openalex"]["reported_total"] == 2


def test_each_run_keeps_its_own_raw_files(tmp_path, monkeypatch):
    ws, proto = _workspace(tmp_path)
    lit = ws / "literature"

    monkeypatch.setattr(disc, "SearchEngine", _engine_factory({"openalex": ["First run"]}, {"openalex": 1}))
    asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=lit))
    monkeypatch.setattr(disc, "SearchEngine", _engine_factory({"openalex": ["Second run"]}, {"openalex": 1}))
    asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=lit))

    run1 = lit / "search_runs" / "run_001"
    run2 = lit / "search_runs" / "run_002"
    assert json.loads((run1 / "raw.json").read_text(encoding="utf-8"))[0]["title"] == "First run"
    assert json.loads((run2 / "raw.json").read_text(encoding="utf-8"))[0]["title"] == "Second run"
    legs1 = json.loads((run1 / "legs.json").read_text(encoding="utf-8"))
    assert legs1["legs"][0]["provider"] == "openalex"
    assert legs1["run"] == "run_001"

    events = [e for e in _events(ws) if e["action"] == "DISCOVERY_SEARCH"]
    assert [e["parameters"]["search_run"] for e in events] == ["run_001", "run_002"]
    assert str(run2 / "raw.json") in events[-1]["outputs"]
    assert str(run2 / "legs.json") in events[-1]["outputs"]


def test_a_failed_leg_is_journalled_with_its_error(tmp_path, monkeypatch):
    class _Boom(BaseAPIProvider):
        def __init__(self):
            super().__init__(name="pubmed", rate_limit=0)

        async def search(self, query):
            self._record_executed("weed[ti]", {})
            raise RuntimeError("HTTP 500")
            yield  # pragma: no cover

    def factory(providers=None):
        return SearchEngine(providers=[_StubProvider("openalex", ["A"], 1), _Boom()])

    monkeypatch.setattr(disc, "SearchEngine", factory)
    ws, proto = _workspace(tmp_path)
    outcome = asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=ws / "literature"))

    assert outcome.status == "PARTIAL"
    event = [e for e in _events(ws) if e["action"] == "DISCOVERY_SEARCH"][-1]
    pubmed = next(leg for leg in event["parameters"]["legs"] if leg["provider"] == "pubmed")
    assert pubmed["status"] == "failed"
    assert "HTTP 500" in pubmed["error"]
    assert pubmed["executed_query"] == "weed[ti]"


# ---------------------------------------------------------------------------
# M3a-discovery D5 / CORE-06: the dedup stage gives the same ids in any order.
# ---------------------------------------------------------------------------


def test_dedup_stage_ids_are_input_order_invariant(tmp_path):
    from scholar_harness.pipeline.deduplication import run_deduplication

    def docs():
        return [
            Document(title="Alpha study of widgets", year=2020, provider="openalex",
                     provider_id="W1", external_ids=ExternalIds(doi="10.1/a")),
            Document(title="Beta analysis of gadgets", year=2021, provider="crossref",
                     provider_id="10.1/b", external_ids=ExternalIds(doi="10.1/b")),
            Document(title="Gamma review of gizmos", year=2022, provider="pubmed",
                     provider_id="77", external_ids=ExternalIds(pubmed_id="77")),
        ]

    forward = run_deduplication(discovered_documents=docs(), literature_dir=tmp_path / "a" / "literature")
    backward = run_deduplication(discovered_documents=docs()[::-1], literature_dir=tmp_path / "b" / "literature")
    by_title = lambda out: {d.title: d.workspace_id for d in out.representatives}  # noqa: E731
    assert by_title(forward) == by_title(backward)
    assert (tmp_path / "a" / "literature" / "deduped.json").read_bytes() == (
        tmp_path / "b" / "literature" / "deduped.json"
    ).read_bytes()


# ---------------------------------------------------------------------------
# M3a-discovery D9: the PRISMA-S style search report, per database.
# ---------------------------------------------------------------------------


def test_each_run_writes_a_prisma_s_report_per_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        disc,
        "SearchEngine",
        _engine_factory({"openalex": ["A", "B"], "crossref": ["C"]}, {"openalex": 2, "crossref": 40}),
    )
    ws, proto = _workspace(tmp_path)
    asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=ws / "literature",
                                   max_search_results=1))

    report = (ws / "literature" / "search_runs" / "run_001" / "search_report.md").read_text(encoding="utf-8")
    assert "PRISMA-S" in report
    for name in ("openalex", "crossref"):
        assert f"crossref::" in report and f"openalex::" in report
        assert name in report
    # Per database: executed string, reported total, fetched, cap, cap hit, date.
    crossref_line = next(line for line in report.splitlines() if line.startswith("| crossref"))
    assert "40" in crossref_line and "| 1 |" in crossref_line
    assert "cap reached" in crossref_line
    assert "run override" in crossref_line
    assert "mailto" not in report
    event = [e for e in _events(ws) if e["action"] == "DISCOVERY_SEARCH"][-1]
    assert any(o.endswith("search_report.md") for o in event["outputs"])


def test_the_report_renders_a_failed_leg_and_its_notes():
    from scholar_search.search_report import render_search_report

    manifest = {
        "run": "run_007", "status": "PARTIAL", "query_id": "Q1", "query_text": "weed AND drone",
        "year_min": 2015, "year_max": 2025,
        "legs": [
            {"provider": "arxiv", "executed_query": "all:weed AND all:drone", "reported_total": 12,
             "fetched": 12, "cap": 10000, "cap_source": "engine_ceiling", "cap_hit": False,
             "status": "ok", "error": None, "notes": ["arXiv query compacted from 400 characters"],
             "started_at": "2026-11-08T10:00:00+00:00", "finished_at": "2026-11-08T10:00:05+00:00",
             "request": {}, "pages": 1, "mailto_set": True},
            {"provider": "pubmed", "executed_query": "weed[ti]", "reported_total": None, "fetched": 0,
             "cap": 10000, "cap_source": "engine_ceiling", "cap_hit": False, "status": "failed",
             "error": "ProviderError: HTTP 500", "notes": [], "started_at": "2026-11-08T10:00:00+00:00",
             "finished_at": "2026-11-08T10:00:01+00:00", "request": {}, "pages": 0, "mailto_set": True},
        ],
    }
    text = render_search_report(manifest)
    assert "run_007" in text and "2015" in text and "2025" in text
    assert "arXiv query compacted" in text
    assert "failed" in text and "HTTP 500" in text
    assert "not reported" in text  # pubmed total unknown


# ---------------------------------------------------------------------------
# M3a review finding 1: MAILTO_NOT_SET holds on the real run path, where the
# stage wraps every provider in an observation proxy.
# ---------------------------------------------------------------------------


def test_run_discovery_refuses_without_mailto_before_any_request(tmp_path, monkeypatch):
    from scholar_search.engine import MailtoNotSet
    from scholar_search.http_client import AcademicHttpClient

    async def _no_network(self, *a, **k):
        raise AssertionError("a request was sent without a contact address")

    monkeypatch.setattr(AcademicHttpClient, "get", _no_network)
    monkeypatch.setattr(settings, "mailto", None)
    ws, proto = _workspace(tmp_path)  # real engine, real providers from the protocol
    with pytest.raises(MailtoNotSet):
        asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=ws / "literature"))
    assert not (ws / "literature" / "search_runs").exists()


# ---------------------------------------------------------------------------
# M3a review finding 3: a leg stopped at the cap still counts as succeeded.
# ---------------------------------------------------------------------------


def test_capped_legs_count_as_succeeded_in_the_journal(tmp_path, monkeypatch):
    monkeypatch.setattr(
        disc,
        "SearchEngine",
        _engine_factory({"openalex": ["A", "B"], "crossref": ["C", "D"]}, {"openalex": 9, "crossref": 9}),
    )
    ws, proto = _workspace(tmp_path)
    outcome = asyncio.run(disc.run_discovery(protocol_path=proto, literature_dir=ws / "literature",
                                             max_search_results=1))
    assert outcome.providers_succeeded == ("crossref", "openalex")
    event = [e for e in _events(ws) if e["action"] == "DISCOVERY_SEARCH"][-1]
    assert event["metrics"]["providers_succeeded"] == 2
    assert "from 2 provider(s)" in event["parameters"]["reason"]


def test_the_report_does_not_claim_more_records_when_no_total_was_reported():
    from scholar_search.search_report import render_search_report

    leg = {"provider": "x", "executed_query": "q", "reported_total": None, "fetched": 5, "cap": 5,
           "cap_source": "protocol", "cap_hit": True, "status": "ok", "notes": [], "request": {}}
    text = render_search_report({"run": "run_001", "legs": [leg]})
    assert "more may exist" in text and "more records exist" not in text
