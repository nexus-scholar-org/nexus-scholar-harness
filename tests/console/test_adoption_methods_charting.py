"""H-adopted-decisions-disclosure: the methods paragraph and the charting table with a declaration.

DoD 4: the methods text never says the reviewer screened every record when a
declaration exists; it states how many records were read one by one, how many
decisions were stored from the agent's drafts and with which outcome, and what
the sample found or that it was not read. Answer 5 (decision 2026-11-22): a
declaration on a published review makes only the methods paragraph out of date;
the published files and the decision export stay as published.

Item 6: a kept study whose inclusion was declared shows it beside the
title-and-abstract decision.

The workspace is published the way ``test_export_api.py`` does it.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from scholar_harness.console import create_app
from scholar_harness.screening import events as ev

_SPEC = importlib.util.spec_from_file_location(
    "_export_api_helpers_adoption", Path(__file__).resolve().parent / "test_export_api.py"
)
tea = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(tea)
se = tea.se

BULK = "Adopted in bulk from the agent's draft; not reviewed individually"
TOKEN = "desk-token"


def _client(ws: Path) -> TestClient:
    return TestClient(create_app(ws, token=TOKEN), base_url="http://127.0.0.1",
                      headers={"Authorization": f"Bearer {TOKEN}"})


def _workspace(tmp_path: Path) -> tuple[Path, dict[str, dict]]:
    """Record 0 excluded and record 2 included in bulk, record 1 read and sent to full text."""
    ws = se._build(tmp_path)
    settings = ws / "literature" / "screening" / "settings.json"
    settings.write_text(json.dumps({"screener_id": se.SCREENER}), encoding="utf-8")
    studies = se._studies(ws)
    inclusion = min(ev.load_context(ws).inclusion_ids)
    events = [
        se._event(ws, studies[0], "EXCLUDE", reason_code=f"FAILS-{inclusion}", note=BULK),
        se._event(ws, studies[1], "MAYBE", note="Read; the abstract does not say."),
        se._event(ws, studies[2], "INCLUDE", note=BULK),
    ]
    se._intake(ws, events)
    return ws, {e["study_id"]: e for e in events}


def _declare(client: TestClient, events: dict[str, dict], **extra) -> dict:
    ids = [e["event_id"] for e in events.values() if e["note"] == BULK]
    response = client.post("/api/v1/screening/adoption-declarations", json={"event_ids": ids, "confirm": True, **extra})
    assert response.status_code == 200, response.text
    return response.json()


def _methods(client: TestClient) -> dict:
    response = client.get("/api/v1/screening/methods")
    assert response.status_code == 200, response.text
    return response.json()


def _numbers_trace(body: dict) -> None:
    def leaves(value):
        if isinstance(value, dict):
            return [x for k, v in value.items() for x in (k, *leaves(v))]
        if isinstance(value, list):
            return [x for v in value for x in leaves(v)]
        return [value]

    found = leaves(body["figures"])
    numbers = {v for v in found if isinstance(v, (int, float)) and not isinstance(v, bool)}
    text = body["paragraph"].replace("SHA-256", "")
    for string in sorted({v for v in found if isinstance(v, str)}, key=len, reverse=True):
        text = text.replace(string, " ")
    digits = [float(n) if "." in n else int(n) for n in re.findall(r"\d+(?:\.\d+)?", text)]
    assert set(digits) <= numbers, (digits, numbers)


def test_without_a_declaration_the_paragraph_is_unchanged(tmp_path):
    ws, _ = _workspace(tmp_path)
    tea.publish(ws)
    body = _methods(_client(ws))
    assert "One reviewer screened every record." in body["paragraph"]
    assert body["figures"]["adoption"] is None


def test_a_declaration_before_publication_replaces_every_record_with_the_counts(tmp_path):
    ws, events = _workspace(tmp_path)
    client = _client(ws)
    _declare(client, events)
    tea.publish(ws)
    body = _methods(client)
    paragraph = body["paragraph"]
    assert "screened every record" not in paragraph
    assert "every decision in this screening was made by the reviewer" not in paragraph
    assert (
        "One reviewer read 1 record one by one; 2 decisions were stored from the agent's draft without being read "
        "one by one (1 excluded, 1 included and 0 unclear)."
    ) in paragraph
    assert "No sample of the 1 exclusion stored from the agent's draft was read." in paragraph
    adoption = body["figures"]["adoption"]
    assert (adoption["read_one_by_one"], adoption["stored_from_drafts"]) == (1, 2)
    assert adoption["by_outcome"] == {"EXCLUDE": 1, "INCLUDE": 1, "MAYBE": 0}
    assert adoption["declared_after_publication"] is False
    assert any(s["path"] == "audit/adoption_declarations.jsonl" for s in body["sources"])
    _numbers_trace(body)


def test_the_sample_is_stated_unread_then_with_what_it_found(tmp_path):
    ws, events = _workspace(tmp_path)
    client = _client(ws)
    declaration = _declare(client, events, sample={"size": 1, "seed": 20261120})["declaration"]
    tea.publish(ws)
    assert "A sample of 1 of these exclusions was drawn (seed 20261120) and has not been read." in _methods(client)["paragraph"]
    # The reviewer reads the sampled record and keeps it: the result is recorded, nothing changed.
    response = client.post("/api/v1/screening/adoption-declarations/sample-results",
                           json={"declaration_id": declaration["declaration_id"], "confirm": True})
    assert response.status_code == 200, response.text
    body = _methods(client)
    assert (
        "A sample of 1 of these exclusions was drawn (seed 20261120) and read; the reviewer changed 0 of the 1 decision."
    ) in body["paragraph"]
    _numbers_trace(body)


def test_a_declaration_on_a_published_review_makes_only_the_methods_out_of_date(tmp_path):
    ws, events = _workspace(tmp_path)
    tea.publish(ws)
    client = _client(ws)
    published = {n: (ws / "literature" / n).read_bytes() for n in ("included.json", "excluded.json", "prisma_report.json")}
    ris_before = client.get("/api/v1/screening/export", params={"format": "ris"})
    assert ris_before.status_code == 200
    before = _methods(client)
    _declare(client, events)
    after = _methods(client)
    assert after["paragraph"] != before["paragraph"] and "screened every record" not in after["paragraph"]
    assert after["figures"]["adoption"]["declared_after_publication"] is True
    assert any("after publication" in c for c in after["caveats"])
    assert after["generation_id"] == before["generation_id"]
    # The published files and the decision export are unchanged and still current.
    assert {n: (ws / "literature" / n).read_bytes() for n in published} == published
    ris_after = client.get("/api/v1/screening/export", params={"format": "ris"})
    assert (ris_after.status_code, ris_after.content) == (200, ris_before.content)


def test_a_kept_study_declared_as_adopted_shows_it_in_the_charting_table(tmp_path):
    ws, events = _workspace(tmp_path)
    tea.publish(ws)
    client = _client(ws)
    table = client.get("/api/v1/charting").json()
    assert all(r["ta_adopted"] is False for r in table["rows"])
    _declare(client, events)
    rows = {r["study_id"]: r for r in client.get("/api/v1/charting").json()["rows"]}
    included = next(s for s, e in events.items() if e["outcome"] == "INCLUDE")
    unclear = next(s for s, e in events.items() if e["outcome"] == "MAYBE")
    assert rows[included]["ta_adopted"] is True and rows[unclear]["ta_adopted"] is False
    study = client.get(f"/api/v1/charting/records/{included}").json()
    assert study["row"]["ta_adopted"] is True
