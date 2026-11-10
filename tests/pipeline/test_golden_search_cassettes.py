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
        assert leg["cap_hit"] == (leg["fetched"] >= CAP and leg["reported_total"] > leg["fetched"]), name
        assert leg["mailto_set"] is True
        assert "mailto" not in leg["request"] and "email" not in leg["request"]
    assert outcome.status == "SUCCESS"
    assert outcome.providers_succeeded == tuple(sorted(DATABASES))  # review finding 3

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
    """The recorded requests carry no contact address, key or User-Agent.

    Response bodies are provider data and may contain placeholders such as
    Unpaywall's ``?email=<INSERT_YOUR_EMAIL>``; only the requests are checked.
    """
    import yaml

    cassette = yaml.safe_load(CASSETTE.read_text(encoding="utf-8"))
    assert cassette["interactions"]
    for interaction in cassette["interactions"]:
        request = interaction["request"]
        uri = request["uri"].lower()
        for name in _SECRET_QUERY:
            assert f"{name}=" not in uri, uri
        assert not {h.lower() for h in request.get("headers", {})} & set(_SECRET_HEADERS)
    if settings.mailto:
        assert settings.mailto not in CASSETTE.read_text(encoding="utf-8")


class _PassthroughVerifier:
    async def process_batch(self, docs, verify=True, enrich=True):
        return list(docs), []


class _PassthroughHydrator:
    def __init__(self, client):
        pass

    async def hydrate_missing_abstracts(self, docs, batch_size=50):
        return list(docs), {"attempted": 0, "hydrated": 0, "failed": 0}


class _Client:
    def __init__(self, *a, **k):
        pass

    async def close(self):
        pass


def test_the_handoff_accept_gives_the_snapshot_the_cli_run_gives(tmp_path, monkeypatch):
    """M3d-engine (decision 2026-11-10): the browser run stops before the snapshot,
    and the hand-off accept builds the artifact the CLI run's accept step builds.

    The artifact id is a function of the accepted records, and each record carries
    its ``retrieved_at``, so two harvests never share an id (true of two CLI runs
    too). The pin is therefore on the same records: the browser run's workspace
    is copied before the accept, the CLI run's accept step (``_accept_run_corpus``)
    freezes the copy, the hand-off accept freezes the original, and the ids match.
    A CLI run of the same search gives the same counts. Verification and hydration
    are passed through (they are not in the cassette).
    """
    from scholar_harness.pipeline import coordinator
    from scholar_harness.pipeline import hydration as hyd_mod
    from scholar_harness.pipeline import verification as ver_mod

    monkeypatch.setattr(hyd_mod, "AbstractHydrator", _PassthroughHydrator)
    monkeypatch.setattr(hyd_mod, "AcademicHttpClient", _Client)
    monkeypatch.setattr(ver_mod, "DocumentVerifier", _PassthroughVerifier)

    def run(ws: Path, **kwargs):
        with _vcr().use_cassette(str(CASSETTE)):
            return asyncio.run(coordinator.run_pipeline(
                workspace_dir=ws, max_search_results=CAP, indexing_fn=lambda _ws: ({}, None), **kwargs,
            ))

    cli = _workspace(tmp_path, "cli")
    cli_results = run(cli)
    cli_snapshot = cli_results["stages"]["corpus_snapshot"]
    assert cli_snapshot["status"] == "ACCEPTED", cli_snapshot  # the CLI still accepts at the end of a run

    browser = _workspace(tmp_path, "browser")
    browser_results = run(browser, freeze_corpus=False)
    assert browser_results["status"] == "PENDING_CORPUS_ACCEPT"
    assert browser_results["stages"]["corpus_snapshot"] == {
        "status": "NOT_ACCEPTED", "reason": "awaiting the hand-off accept",
    }
    registry = browser / "audit" / "artifact_registry.json"
    assert not registry.is_file() or "corpus_snapshot" not in registry.read_text(encoding="utf-8")
    assert not (browser / "literature" / "screening").is_dir() or not list(
        (browser / "literature" / "screening").glob("batch_*.json")
    )

    same_records = tmp_path / "same-records"
    shutil.copytree(browser, same_records)
    pipeline_step = coordinator._accept_run_corpus(same_records, {})
    accepted = coordinator.accept_discovery_corpus(browser)
    assert pipeline_step["status"] == "ACCEPTED"
    assert accepted.artifact_id == pipeline_step["artifact_id"]
    assert accepted.outcome_status == pipeline_step["outcome_status"] == cli_snapshot["outcome_status"]
    assert (accepted.study_count, accepted.record_count) == (cli_snapshot["study_count"], cli_snapshot["record_count"])


def test_the_plan_dry_run_equals_the_replayed_legs(tmp_path):
    """E1 (M3d-engine, packet §4.1, decision 4): each provider's translation, made
    without a request, is the string the replayed golden run sent, per database."""
    from scholar_search.plan import compile_plan

    ws = _workspace(tmp_path, "plan")
    outcome = _search(ws)
    sent = {leg["provider"]: leg for leg in outcome.legs}

    with _vcr().use_cassette(str(CASSETTE), allow_playback_repeats=False) as cassette:
        plan = compile_plan(ws / "protocol.json", ["openalex", "semanticscholar", "crossref", "arxiv", "pubmed", "biorxiv"])
        assert cassette.play_count == 0  # the dry run sends nothing
    preview = {p["name"]: p for p in plan["providers"]}
    assert set(preview) == DATABASES | {"biorxiv"}
    for name in DATABASES:
        assert preview[name]["status"] == "translated", name
        assert preview[name]["executed_query"] == sent[name]["executed_query"], name
        # The leg ran with the run override; the request differs only in what the cap sets.
        assert set(preview[name]["request"]) == set(sent[name]["request"]), name
        assert "mailto" not in preview[name]["request"] and "email" not in preview[name]["request"]
        assert preview[name]["notes"] == [n for n in sent[name]["notes"] if n in preview[name]["notes"]], name
    assert preview["biorxiv"]["status"] == "off_by_default"
    assert preview["biorxiv"]["executed_query"] is None and preview["biorxiv"]["request"] is None


#: The golden SCI-id map and REC->STU map before E4a (computed at 695bad4 on the
#: replayed cassette). E4a records the tier of each merge and must move neither.
GOLDEN_SCI_DIGEST = "b016a8025043df4ecd86c710fe11a44fd6c547238d97eb56e0c3ebf3f29415c7"
GOLDEN_REC_DIGEST = "87bc4f85c5b9270fef3b428a8bd13dab7e5869e836f0218a038b1fd2fc8b34bb"


def test_dedup_tiers_are_recorded_and_the_ids_do_not_move(tmp_path):
    """E4a (M3d-engine, packet §4.5 Stage 1): clusters.json beside deduped.json, ids unchanged."""
    import hashlib
    import json

    ws = _workspace(tmp_path, "tiers")
    outcome = _search(ws)
    sci, rec = _ids(ws, outcome.documents)
    assert hashlib.sha256(json.dumps(sorted(sci.items())).encode()).hexdigest() == GOLDEN_SCI_DIGEST
    assert hashlib.sha256(json.dumps(sorted(rec.items())).encode()).hexdigest() == GOLDEN_REC_DIGEST

    data = json.loads((ws / "literature" / "dedup" / "clusters.json").read_text(encoding="utf-8"))
    assert data["run"] == "run_001"
    assert data["method"] == {"title_similarity": 0.97, "year_tolerance": 1, "first_author": True, "source": "default"}
    clusters = data["clusters"]
    assert len(clusters) == len(sci)
    removed = sum(len(c["members"]) - 1 for c in clusters)
    assert removed == len(outcome.documents) - len(sci)
    assert {c["tier"] for c in clusters} <= {None, "identifier", "exact_title", "fuzzy_title"}
    assert all((c["tier"] is None) == (len(c["members"]) == 1) for c in clusters)
    merged_by = [m["merged_by"] for c in clusters for m in c["members"][1:]]
    assert len(merged_by) == removed and "identifier" in merged_by
    assert sorted(c["representative"]["workspace_id"] for c in clusters) == sorted(sci.values())
