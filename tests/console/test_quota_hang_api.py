"""H-quota-hang: a harvest whose checks meet a used-up quota ends, says so, and can be finished later.

The finding (acceptance run, 2026-11-20, findings 12, 15, 16): OpenAlex
answered ``429`` with ``Retry-After: 50000`` during the harvest's "Checks"
step; the run sat on "Preparing" for hours with no message, and "Stop after
the current step" was read only between stages.

Offline, as ``test_harvest_preparation_api.py`` (whose doubles this file
loads): the databases are in-memory doubles run by the real engine. The
checks run the real ``DocumentVerifier`` with the real Crossref and OpenAlex
providers, whose HTTP clients answer from ``httpx.MockTransport`` doubles;
the HTTP client's sleeps are recorded, never slept.
"""

from __future__ import annotations

import importlib.util
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from scholar_harness.pipeline import verification as ver_mod
from scholar_search import http_client as http_mod
from scholar_search.providers.crossref import CrossrefProvider
from scholar_search.providers.openalex import OpenAlexProvider
from scholar_search.verifier import DocumentVerifier

_SPEC = importlib.util.spec_from_file_location(
    "_harvest_preparation_helpers", Path(__file__).resolve().parent / "test_harvest_preparation_api.py"
)
p = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(p)
h = p.h

env = h.env
BASE = h.BASE
ACCEPT = p.ACCEPT
PROVIDERS = {"providers": ["openalex", "crossref"]}
WORKS = 8  # four records from each database double, all different works


class World:
    """What the two databases answer during the checks, and what they were asked."""

    def __init__(self) -> None:
        self.openalex_quota = True
        self.crossref: list[str] = []
        self.openalex: list[str] = []
        self.slept: list[float] = []
        self.after_crossref = None  # called with the number of Crossref requests so far

    def crossref_answer(self, request: httpx.Request) -> httpx.Response:
        self.crossref.append(str(request.url))
        if self.after_crossref is not None:
            self.after_crossref(len(self.crossref))
        match = re.fullmatch(r"/works/10\.1/(\w+)\.(\d+)", request.url.path)
        if not match:
            return httpx.Response(200, json={"message": {"items": []}})
        provider, i = match.groups()
        return httpx.Response(200, json={"message": {
            "DOI": f"10.1/{provider}.{i}", "title": [f"UAV weed mapping study {provider} {i}"],
            "published-print": {"date-parts": [[2023]]},
        }})

    def openalex_answer(self, request: httpx.Request) -> httpx.Response:
        self.openalex.append(str(request.url))
        if self.openalex_quota:
            return httpx.Response(429, headers={"Retry-After": "50000"}, json={"error": "daily quota"})
        return httpx.Response(200, json={})


@pytest.fixture
def world(env, monkeypatch) -> World:
    state = World()

    async def record(delay: float, *args, **kwargs) -> None:
        state.slept.append(float(delay))

    # Only the HTTP client's sleeps are replaced (its module's ``asyncio`` name), not the app's.
    monkeypatch.setattr(http_mod, "asyncio", SimpleNamespace(sleep=record))
    monkeypatch.setattr(http_mod, "host_budget", lambda url: None)

    class Verifier(DocumentVerifier):
        def __init__(self) -> None:
            crossref, openalex = CrossrefProvider(), OpenAlexProvider()
            for provider, answer in ((crossref, state.crossref_answer), (openalex, state.openalex_answer)):
                provider.client.base_delay = 0
                provider.client.rate_limiter.set_rate(0)
                provider.client.client = httpx.AsyncClient(
                    transport=httpx.MockTransport(answer), headers=provider.client.client.headers
                )
            super().__init__(crossref_provider=crossref, openalex_provider=openalex)

    monkeypatch.setattr(ver_mod, "DocumentVerifier", Verifier)
    return state


def _checks(ws: Path) -> dict:
    return json.loads((ws / "literature" / "verification_checks.json").read_text(encoding="utf-8"))


def _verified(ws: Path) -> list[dict]:
    return json.loads((ws / "literature" / "verified.json").read_text(encoding="utf-8"))


def test_a_used_up_quota_during_the_checks_ends_the_run_and_says_when_it_resets(env, world):
    client, ws, _ = env
    before = datetime.now(UTC)
    job, events = h._run(client, PROVIDERS)

    # Bounded: OpenAlex was asked once, nothing waited out its 14 hours, and the job ended.
    assert len(world.openalex) == 1 and sum(world.slept) <= 60
    assert job["state"] == "succeeded" and job["result"]["status"] == "INCOMPLETE", job

    # Every work is kept, none dropped and none verified by OpenAlex.
    verified = _verified(ws)
    assert len(verified) == WORKS and all(row["workspace_id"] for row in verified)
    checks = _checks(ws)
    assert checks["records"] == WORKS and checks["unchecked"] == WORKS
    assert checks["unchecked_reasons"] == {"PROVIDER_QUOTA_EXHAUSTED": WORKS}
    assert all(row["not_done"] == ["enrichment"] and row["code"] == "VERIFIED" for row in checks["rows"])
    assert [row["workspace_id"] for row in checks["rows"]] == [row["workspace_id"] for row in verified]

    # The run's state says it: which database, when it resets, how many records, what to do.
    preparation = client.get(f"{BASE}/runs/run_001").json()["preparation"]
    assert preparation["state"] == "incomplete" and preparation["stage"] == "verification"
    assert preparation["can_finish"] is True
    found = preparation["checks"]
    assert found["unchecked"] == WORKS and found["records"] == WORKS and found["reason"] == "PROVIDER_QUOTA_EXHAUSTED"
    assert [paused["database"] for paused in found["paused"]] == ["OpenAlex"]
    resets = datetime.fromisoformat(found["paused"][0]["resets_at"])
    assert before + timedelta(seconds=49_990) <= resets <= datetime.now(UTC) + timedelta(seconds=50_010)
    assert "OpenAlex quota is used up" in preparation["message"] and f"{WORKS} of {WORKS} records" in preparation["message"]
    assert "Finish preparing this corpus after the reset" in preparation["message"]

    # The job said it as it ended, and the journal has one row for it.
    stage = [d for name, d in events if name == "stage" and d["stage"] == "verification"]
    assert stage and stage[-1]["status"] == "INCOMPLETE" and stage[-1]["detail"]["unchecked"] == WORKS
    rows = [e for e in h._journal(ws) if e["action"] == "HARVEST_PREPARATION_INCOMPLETE"]
    assert len(rows) == 1 and rows[0]["status"] == "PARTIAL"
    assert "PIPELINE_RUN_PAUSED_FOR_CORPUS_ACCEPT" not in [e["action"] for e in h._journal(ws)]

    # The hand-off says it too, and refuses to freeze a corpus that is not fully checked.
    handoff = client.get(f"{BASE}/handoff").json()
    assert handoff["preparation"]["state"] == "incomplete" and handoff["preparation"]["checks"]["unchecked"] == WORKS
    refused = client.post(ACCEPT)
    assert refused.status_code == 409 and h._code(refused) == "PREPARATION_UNFINISHED", refused.text

    # The next-step bar and the hand-off checks read the same state. The double scaffolds a placeholder
    # workspace; genesis would record that the protocol came from inception (as test_next_step_api does).
    manifest = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    (ws / "project.json").write_text(json.dumps({**manifest, "protocol_origin": "inception"}), encoding="utf-8")
    bar = client.get("/api/v1/review/next-step").json()
    assert bar["state"] == "CORPUS_PENDING" and bar["action"]["key"] == "finishPreparing"
    assert bar["waiting"]["kind"] == "failed" and bar["waiting"]["stage"] == "verifying"
    assert bar["waiting"]["reason"] == {"code": "PROVIDER_QUOTA_EXHAUSTED", "message": preparation["message"]}
    checks = client.get(f"{BASE}/checks", params={"step": "handoff"}).json()
    row = next(c for c in checks["checks"] if c["check_id"] == "HANDOFF_PREPARATION_UNFINISHED")
    assert row["params"]["state"] == "incomplete" and row["action"]["finish"] is True


def test_finish_preparing_after_the_reset_checks_only_the_records_not_checked(env, world):
    client, ws, _ = env
    world.after_crossref = None
    # Half the works are checked before the quota runs out: OpenAlex answers the first four enrichments.
    answered = {"n": 0}
    real = world.openalex_answer

    def quota_after_four(request: httpx.Request) -> httpx.Response:
        answered["n"] += 1
        world.openalex_quota = answered["n"] > 4
        return real(request)

    world.openalex_answer = quota_after_four
    job, _ = h._run(client, PROVIDERS)
    assert job["result"]["status"] == "INCOMPLETE", job
    first = _checks(ws)
    assert first["unchecked"] == WORKS - 4
    done_ids = {row["workspace_id"] for row in first["rows"] if not row["not_done"]}
    assert len(done_ids) == 4

    # After the reset: OpenAlex answers again; only the four records not checked are asked about.
    world.openalex_answer = real
    world.openalex_quota = False
    world.crossref.clear()
    world.openalex.clear()
    job, events = p._finish(client)
    assert job["state"] == "succeeded" and job["result"]["resumed_from"] == "verification", job
    assert len(world.crossref) == WORKS - 4 and len(world.openalex) == WORKS - 4
    stages = [d["stage"] for name, d in events if name == "stage"]
    assert stages[:1] == ["verification"] and "deduplication" not in stages and "hydration" not in stages

    second = _checks(ws)
    assert second["unchecked"] == 0 and second["records"] == WORKS and second["checked_now"] == WORKS - 4
    assert len(_verified(ws)) == WORKS
    preparation = client.get(f"{BASE}/runs/run_001").json()["preparation"]
    assert preparation["state"] == "ready" and preparation["checks"] is None
    resumed = [e for e in h._journal(ws) if e["action"] == "HARVEST_PREPARATION_RESUMED"]
    assert resumed and "only the 4 records not checked are checked again" in resumed[-1]["description"]
    assert client.post(ACCEPT).status_code == 200


def test_a_stop_during_the_checks_ends_them_within_one_record(env, world):
    client, ws, _ = env
    world.openalex_quota = False

    def stop_at_the_third(count: int) -> None:
        if count == 3:
            for job in client.app.state.discovery_jobs.jobs.values():
                job.cancel_requested = True  # what "Stop after the current step" sets

    world.after_crossref = stop_at_the_third
    job, _ = h._run(client, PROVIDERS)

    assert len(world.crossref) == 3  # the record being checked ends; no fourth record is asked about
    assert job["state"] == "cancelled" and job["result"]["status"] == "CANCELLED", job
    checks = _checks(ws)
    assert checks["stopped"] is True and checks["unchecked"] == WORKS - 3
    assert checks["unchecked_reasons"] == {"STOPPED_BY_RESEARCHER": WORKS - 3}
    assert len(_verified(ws)) == WORKS
    preparation = client.get(f"{BASE}/runs/run_001").json()["preparation"]
    assert preparation["state"] == "incomplete" and preparation["checks"]["reason"] == "STOPPED_BY_RESEARCHER"
    assert preparation["message"].startswith("You stopped the checks between two records.")
    assert "after the reset" not in preparation["message"]
