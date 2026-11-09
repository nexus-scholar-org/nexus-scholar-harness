"""M4c: the golden recon probe on the real M3a providers, replayed from a VCR cassette.

The cassette ``tests/fixtures/cassettes/golden_recon_probe.yaml`` is recorded
in ONE live run (the researcher's approval and contact address; decision
2026-11-09, "Recon over HTTP"): the golden UAV topic, 2020 to 2026, the four
recon providers (OpenAlex, Semantic Scholar, Crossref, arXiv) at the pool cap
of 25. The contact address, API keys and the User-Agent are filtered out, as
in M3a's golden search cassette.

Replay only by default (``record_mode="none"``): a request that is not in the
cassette fails the test. To re-record deliberately, delete the cassette and run
with ``NEXUS_RECORD_CASSETTES=1`` and a real ``SCHOLAR_MAILTO``.

The tests prove, offline:
- the probe runs through ``SearchEngine.run`` and keeps one leg per provider
  with its reported total and fetched count, and the pool is cached complete;
- distill and directions read it, and the gates score it;
- the console routes run the same probe as a job and bind its direction.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import pytest
import vcr
from fastapi.testclient import TestClient
from scholar_search.config import settings

from scholar_harness.console import create_app
from scholar_harness.recon.session import ReconSessions

ROOT = Path(__file__).resolve().parents[2]
CASSETTE = ROOT / "tests" / "fixtures" / "cassettes" / "golden_recon_probe.yaml"
TOPIC = "UAV crop weed mapping"
YEARS = (2020, 2026)
PROVIDERS = {"openalex", "semanticscholar", "crossref", "arxiv"}
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
        allow_playback_repeats=True,
    )


pytestmark = pytest.mark.skipif(
    not CASSETTE.exists() and not RECORD,
    reason="golden recon cassette not recorded yet (record with NEXUS_RECORD_CASSETTES=1)",
)


@pytest.fixture(autouse=True)
def _replay_settings(monkeypatch):
    monkeypatch.delenv("NEXUS_RECON_ROOT", raising=False)
    if not RECORD:
        monkeypatch.setattr(settings, "mailto", "replay@example.invalid")
    elif not settings.mailto:
        pytest.fail("recording needs SCHOLAR_MAILTO")
    monkeypatch.setattr(settings, "http_cache", False)
    monkeypatch.setattr(settings, "openalex_key", None)
    monkeypatch.setattr(settings, "s2_key", None)


def test_the_golden_probe_keeps_each_leg_and_feeds_directions(tmp_path):
    store = ReconSessions(root=tmp_path / "recon")
    with _vcr().use_cassette(str(CASSETTE)):
        out = asyncio.run(store.probe(TOPIC, topic=TOPIC, year_min=YEARS[0], year_max=YEARS[1]))
    assert {leg["provider"] for leg in out["legs"]} == PROVIDERS
    for leg in out["legs"]:
        assert leg["status"] == "ok", leg
        assert leg["fetched"] <= 25
        assert leg["reported_total"] is None or leg["reported_total"] >= leg["fetched"]
    assert out["status"] == "complete" and 12 <= out["n_docs"] <= 25
    assert out["served_from_cache"] is False

    again = asyncio.run(store.probe(TOPIC, session_id=out["session_id"], year_min=YEARS[0], year_max=YEARS[1]))
    assert again["served_from_cache"] is True and again["fingerprint"] == out["fingerprint"]

    explore = store.distill(out["session_id"])
    assert explore["gates"]["pool"]["sufficient"] is True
    found = store.directions(out["session_id"])
    assert found["directions"], "the golden pool proposes at least one direction"
    for d in found["directions"]:
        assert len(d["anchor_dois"]) >= 2


def test_the_golden_probe_runs_from_http_and_binds(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    app = create_app(None, token="t", workspaces_root=root)
    app.state.recon_root = tmp_path / "recon"
    draft = {"topic": TOPIC, "start_year": YEARS[0], "end_year": YEARS[1]}
    with _vcr().use_cassette(str(CASSETTE)), TestClient(
        app, base_url="http://127.0.0.1", headers={"Authorization": "Bearer t"}
    ) as client:
        sid = client.post("/api/v1/inception/drafts", json={"draft": draft}).json()["session_id"]
        recon = f"/api/v1/inception/drafts/{sid}/recon"
        job = client.post(f"{recon}/probe", json={}).json()["job"]
        with client.stream("GET", f"{recon}/jobs/{job['job_id']}/events") as stream:
            events = [line for line in stream.iter_lines() if line.startswith("event: ")]
        assert events[-1] == "event: done", events
        assert "event: leg" in events, "live paging reports progress per provider"
        done = client.get(f"{recon}/jobs/{job['job_id']}").json()["job"]
        assert {leg["provider"] for leg in done["result"]["legs"]} == PROVIDERS
        label = client.get(f"{recon}/directions").json()["directions"][0]["label"]
        bound = client.post(f"{recon}/bind", json={"direction": label}).json()
    assert bound["grounding"]["pool"]["fingerprint"] == done["result"]["fingerprint"]


def test_the_recon_cassette_holds_no_contact_address_or_key():
    text = CASSETTE.read_text(encoding="utf-8")
    assert "mailto=" not in text and "api_key=" not in text
    assert "@" not in "".join(line for line in text.splitlines() if "uri:" in line)
    if not RECORD:
        assert json.dumps(settings.mailto) not in text
