"""M3a-discovery D8/D9/D5: the golden search, replayed from VCR cassettes.

The cassette ``tests/fixtures/cassettes/golden_uav_search.yaml`` was recorded
in ONE live run of the golden UAV protocol (decision 2026-11-08, "One live
golden search, frozen to cassettes") against OpenAlex, Semantic Scholar,
Crossref, arXiv and PubMed, with a run override of 100 records per database.
The contact address, API keys and the User-Agent are filtered out.

By default the test only replays (``record_mode="none"``): a request that is
not in the cassette fails the test, so it never reaches the network. To
re-record deliberately, delete the cassette and run with
``NEXUS_RECORD_CASSETTES=1`` and a real ``SCHOLAR_MAILTO``.

The test proves, offline:
- the golden search runs from the cassette and every database leg reports the
  executed string, the reported total, the fetched count and the cap (D8);
- the PRISMA-S report lists them per database (D9);
- a second run gives identical SCI ids and identical corpus snapshot ids (D5).
"""

from __future__ import annotations

import asyncio
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest
import vcr
from scholar_search.config import settings

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "workspaces" / "golden-uav-30"
CASSETTE = ROOT / "tests" / "fixtures" / "cassettes" / "golden_uav_search.yaml"
CAP = 100
DATABASES = {"openalex", "semanticscholar", "crossref", "arxiv", "pubmed"}
RECORD = os.environ.get("NEXUS_RECORD_CASSETTES") == "1"

_SECRET_QUERY = ["mailto", "email", "tool", "api_key", "apikey"]
_SECRET_HEADERS = ["user-agent", "x-api-key", "authorization", "cookie"]


def _scrub_response(response):
    headers = response.get("headers", {})
    for name in list(headers):
        if name.lower() in ("set-cookie", "cookie"):
            headers.pop(name)
    return response


def _vcr() -> vcr.VCR:
    return vcr.VCR(
        record_mode="once" if RECORD else "none",
        match_on=["method", "scheme", "host", "path", "query"],
        filter_query_parameters=_SECRET_QUERY,
        filter_headers=_SECRET_HEADERS,
        before_record_response=_scrub_response,
        decode_compressed_response=True,
    )


pytestmark = pytest.mark.skipif(
    not CASSETTE.exists() and not RECORD,
    reason="golden cassette not recorded yet (record with NEXUS_RECORD_CASSETTES=1)",
)


@pytest.fixture(autouse=True)
def _replay_settings(monkeypatch):
    if not RECORD:
        # Replay needs no real address; the cassette has none either.
        monkeypatch.setattr(settings, "mailto", "replay@example.invalid")
    elif not settings.mailto:
        pytest.fail("recording needs SCHOLAR_MAILTO")
    monkeypatch.setattr(settings, "http_cache", False)
    monkeypatch.setattr(settings, "openalex_key", None)
    monkeypatch.setattr(settings, "s2_key", None)


def _workspace(tmp_path: Path, name: str) -> Path:
    ws = tmp_path / name
    ws.mkdir()
    for item in ("protocol.json", "project.json"):
        shutil.copy2(GOLDEN / item, ws / item)
    return ws


def _search(ws: Path):
    from scholar_harness.pipeline.discovery import run_discovery

    with _vcr().use_cassette(str(CASSETTE)):
        return asyncio.run(
            run_discovery(
                protocol_path=ws / "protocol.json",
                literature_dir=ws / "literature",
                max_search_results=CAP,
            )
        )


def _ids(ws: Path, documents) -> tuple[dict[str, str], dict[str, str]]:
    """SCI ids from the dedup stage, then REC->STU from the Packet B builder."""
    from scholar_harness.corpus_accept import _deduplicator, _protocol_fingerprint, _workspace_id
    from scholar_harness.pipeline.deduplication import run_deduplication
    from scholar_search.identity import build_corpus_snapshot_artifact

    dedup = run_deduplication(discovered_documents=documents, literature_dir=ws / "literature")
    sci = {
        f"{d.provider}:{d.provider_id}": d.workspace_id for d in dedup.representatives
    }
    built = build_corpus_snapshot_artifact(
        dedup.representatives,
        workspace_id=_workspace_id(ws),
        run_id="RUN-golden-cassette",
        protocol_fingerprint=_protocol_fingerprint(ws),
        created_at=datetime(2026, 11, 8, tzinfo=UTC),
        deduplicator=_deduplicator(ws),
    )
    return sci, dict(built.artifact["data"]["record_to_study"])


def test_golden_search_replays_with_legs_report_and_stable_ids(tmp_path):
    first = _workspace(tmp_path, "first")
    outcome = _search(first)

    legs = {leg["provider"]: leg for leg in outcome.legs}
    assert set(legs) == DATABASES
    for name, leg in legs.items():
        assert leg["status"] == "ok", (name, leg.get("error"))
        assert leg["executed_query"], name
        assert leg["reported_total"] is not None, name
        assert 0 < leg["fetched"] <= CAP, (name, leg["fetched"])
        assert leg["cap"] == CAP and leg["cap_source"] == "run_override"
        assert leg["cap_hit"] == (leg["reported_total"] > leg["fetched"]), name
        assert leg["mailto_set"] is True
        assert "mailto" not in leg["request"] and "email" not in leg["request"]
    assert outcome.status == "SUCCESS"

    report = (first / "literature" / "search_runs" / "run_001" / "search_report.md").read_text(encoding="utf-8")
    for name, leg in legs.items():
        row = next(line for line in report.splitlines() if line.startswith(f"| {name} "))
        assert str(leg["fetched"]) in row and str(leg["reported_total"]) in row
        assert f"{CAP} (run override)" in row

    second = _workspace(tmp_path, "second")
    again = _search(second)
    assert [leg["executed_query"] for leg in again.legs] == [leg["executed_query"] for leg in outcome.legs]
    sci_1, rec_1 = _ids(first, outcome.documents)
    sci_2, rec_2 = _ids(second, again.documents)
    assert sci_1 == sci_2
    assert rec_1 == rec_2
    assert len(set(sci_1.values())) == len(sci_1)


def test_the_cassette_holds_no_contact_address_or_key():
    text = CASSETTE.read_text(encoding="utf-8")
    assert "mailto=" not in text and "email=" not in text
    assert "api_key" not in text and "x-api-key" not in text.lower()
    if settings.mailto:
        assert settings.mailto not in text
