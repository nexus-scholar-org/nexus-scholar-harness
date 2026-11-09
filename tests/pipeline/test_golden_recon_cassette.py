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

Recorded on 2026-11-09: OpenAlex, Crossref and arXiv answered; Semantic
Scholar answered HTTP 429 (no API key). The cassette keeps that, so the test
proves INC-09 on real responses.

The tests prove, offline:
- the probe runs through ``SearchEngine.run`` and keeps one leg per provider
  with its reported total and fetched count; the rate-limited leg is recorded
  as failed with its error, the pool is ``partial`` and is never reused;
- distill and directions read it, and the gates score it;
- the console routes run the same probe as a job and bind its direction.
"""

from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path

import pytest
import vcr
import yaml
from fastapi.testclient import TestClient
from scholar_search.config import settings

from scholar_harness.console import create_app
from scholar_harness.recon.session import ReconSessions

ROOT = Path(__file__).resolve().parents[2]
CASSETTE = ROOT / "tests" / "fixtures" / "cassettes" / "golden_recon_probe.yaml"
TOPIC = "UAV crop weed mapping"
YEARS = (2020, 2026)
PROVIDERS = {"openalex", "semanticscholar", "crossref", "arxiv"}
#: What the recorded run answered (2026-11-09).
RATE_LIMITED = "semanticscholar"
ANSWERED = PROVIDERS - {RATE_LIMITED}
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


def _cassette():
    # The HTTP test replays the same requests as the engine test.
    return _vcr().use_cassette(str(CASSETTE), allow_playback_repeats=True)


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
    with _cassette():
        out = asyncio.run(store.probe(TOPIC, topic=TOPIC, year_min=YEARS[0], year_max=YEARS[1]))
    legs = {leg["provider"]: leg for leg in out["legs"]}
    assert set(legs) == PROVIDERS
    for name in ANSWERED:
        leg = legs[name]
        assert leg["status"] == "ok", leg
        assert 0 < leg["fetched"] <= 25
        assert leg["reported_total"] is None or leg["reported_total"] >= leg["fetched"]
    limited = legs[RATE_LIMITED]
    assert limited["status"] == "failed" and limited["fetched"] == 0
    assert "429" in limited["error"]
    assert out["status"] == "partial" and 12 <= out["n_docs"] <= 25
    assert out["served_from_cache"] is False
    assert not list((tmp_path / "recon" / "pools").glob("*_pool.json")), "a partial pool is never cached"

    again = asyncio.run(store.probe(TOPIC, session_id=out["session_id"], year_min=YEARS[0], year_max=YEARS[1]))
    assert again["served_from_cache"] is False, "INC-09: the partial pool is searched again"

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
    with _cassette(), TestClient(
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
        assert done["result"]["status"] == "partial", "a partial pool is usable and says so"
        label = client.get(f"{recon}/directions").json()["directions"][0]["label"]
        bound = client.post(f"{recon}/bind", json={"direction": label}).json()
    assert bound["grounding"]["pool"]["fingerprint"] == done["result"]["fingerprint"]


#: The real address while recording; read before the autouse fixture patches settings.
_RECORDING_ADDRESS = os.environ.get("SCHOLAR_MAILTO") if RECORD else None
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}\b")
#: Addresses that may appear in provider help text or in our own replay setting.
_HARMLESS = re.compile(r"@(example\.(?:com|org|invalid)|openalex\.org|semanticscholar\.org|crossref\.org|arxiv\.org)$", re.I)


def addresses_in(text: str) -> list[str]:
    """Every e-mail address in ``text`` except documented harmless ones."""
    return sorted({m for m in _EMAIL.findall(text) if not _HARMLESS.search(m)})


def test_the_address_check_finds_a_planted_address():
    planted = "body: {string: 'contact researcher@univ-example.dz for access'}"
    assert addresses_in(planted) == ["researcher@univ-example.dz"]
    assert addresses_in("mailto: replay@example.invalid; see support@openalex.org") == []
    assert addresses_in("mAP@0.5 and mAP@0.5:0.95 on the benchmark") == []  # metrics, not addresses


def test_the_recon_cassette_holds_no_contact_address_or_key():
    """No request carries a contact address or key, and no address appears anywhere.

    Response bodies may mention ``api_key`` in provider help text (OpenAlex
    does), so the request URIs and headers are checked for parameters, and the
    whole file for addresses.
    """
    data = yaml.safe_load(CASSETTE.read_text(encoding="utf-8"))
    for interaction in data["interactions"]:
        request = interaction["request"]
        query = request["uri"].split("?", 1)[-1].lower()
        for secret in ("mailto=", "email=", "api_key=", "apikey=", "tool="):
            assert secret not in query, request["uri"]
        assert "@" not in request["uri"]
        headers = {k.lower() for k in (request.get("headers") or {})}
        assert not headers & {"user-agent", "x-api-key", "authorization", "cookie"}
    text = CASSETTE.read_text(encoding="utf-8")
    assert addresses_in(text) == []
    if _RECORDING_ADDRESS:
        assert _RECORDING_ADDRESS not in text
