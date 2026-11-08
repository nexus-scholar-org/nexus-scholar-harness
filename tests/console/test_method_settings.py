"""M7-method M6: blinding set by the protocol; the policy the screen needs.

Decision 2026-11-08: when the protocol's ``method`` block sets blinding, the
settings report it with ``blinding_source: "protocol"`` and a change is
refused (``BLINDING_SET_BY_PROTOCOL``). Without a block nothing changes. The
settings also carry ``not_reported_policy`` so triage can offer the right
reason (M7). Derived fields are never written into ``settings.json``.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from test_screening_api_v1 import BASE, DESKTOP, PHONE, _workspace

from scholar_harness.console import create_app

BLOCK = {
    "dedup": {"doi": True, "title_similarity": 0.97, "first_author": True, "year_tolerance": 1},
    "rules_version": "screening-rules-v1",
    "not_reported": "exclude",
    "blinding": "show",
}


def _client(tmp_path, method: dict | None):
    ws = _workspace(tmp_path, prepare=False)
    if method is not None:
        protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
        protocol["method"] = method
        (ws / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    client = TestClient(
        create_app(ws, token=DESKTOP, phone_tokens={PHONE}),
        base_url="http://127.0.0.1",
        headers={"Authorization": f"Bearer {DESKTOP}"},
    )
    return client, ws


def test_without_a_block_blinding_is_a_setting_as_before(tmp_path):
    client, ws = _client(tmp_path, None)
    settings = client.get(f"{BASE}/settings").json()
    assert (settings["blinding"], settings["blinding_source"], settings["not_reported_policy"]) == (
        "reveal_after_decision", "settings", "unclear",
    )
    changed = client.put(f"{BASE}/settings", json={"blinding": "show"})
    assert changed.status_code == 200 and changed.json()["blinding"] == "show"


def test_the_protocol_sets_blinding_and_a_change_is_refused(tmp_path):
    client, ws = _client(tmp_path, BLOCK)
    settings = client.get(f"{BASE}/settings").json()
    assert (settings["blinding"], settings["blinding_source"], settings["not_reported_policy"]) == (
        "show", "protocol", "exclude",
    )
    refused = client.put(f"{BASE}/settings", json={"blinding": "reveal_after_decision"})
    assert refused.status_code == 409
    assert refused.json()["detail"]["code"] == "BLINDING_SET_BY_PROTOCOL"
    # The same value is not a change; other settings still change.
    assert client.put(f"{BASE}/settings", json={"blinding": "show"}).status_code == 200
    ok = client.put(f"{BASE}/settings", json={"queue_order": "agent_uncertainty"})
    assert ok.status_code == 200 and ok.json()["blinding"] == "show"
    stored = json.loads((ws / "literature" / "screening" / "settings.json").read_text(encoding="utf-8"))
    assert "blinding_source" not in stored and "not_reported_policy" not in stored


def test_an_invalid_block_is_refused_not_ignored(tmp_path):
    client, _ = _client(tmp_path, {**BLOCK, "blinding": "hidden"})
    response = client.get(f"{BASE}/settings")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "PROTOCOL_METHOD_INVALID"


@pytest.mark.parametrize("code", ["BLINDING_SET_BY_PROTOCOL", "PROTOCOL_METHOD_INVALID"])
def test_the_new_codes_are_console_refusals(code):
    from scholar_harness.console import refusals

    assert code in refusals.CONTRACT_ADDED
