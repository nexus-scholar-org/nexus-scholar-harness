"""M6-hardening H1: the console's settings and approver writes are atomic.

Each write goes through ``scholar_harness.workspace.atomic``; a crash before
the replace (simulated by failing ``os.replace``) leaves the previous file
whole. Before the fix both routes wrote the target in place, so the simulated
crash never fired and the file changed.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from scholar_harness.console import create_app
from scholar_harness.workspace import atomic

from test_screening_api_v1 import BASE, DESKTOP, PHONE, _workspace


@pytest.fixture
def client_ws(tmp_path):
    ws = _workspace(tmp_path, prepare=False)
    client = TestClient(
        create_app(ws, token=DESKTOP, phone_tokens={PHONE}),
        base_url="http://127.0.0.1",
        headers={"Authorization": f"Bearer {DESKTOP}"},
    )
    return client, ws


def _crash(monkeypatch):
    def crash(src, dst):
        raise OSError("power cut before the replace")

    monkeypatch.setattr(atomic.os, "replace", crash)


def test_settings_survive_a_crash_mid_write(client_ws, monkeypatch):
    client, ws = client_ws
    assert client.put(f"{BASE}/settings", json={"blinding": "show"}).status_code == 200
    path = ws / "literature" / "screening" / "settings.json"
    before = path.read_bytes()

    _crash(monkeypatch)
    with pytest.raises(OSError, match="power cut"):
        client.put(f"{BASE}/settings", json={"blinding": "reveal_after_decision"})
    assert path.read_bytes() == before
    assert json.loads(before)["blinding"] == "show"
    assert sorted(p.name for p in path.parent.iterdir() if ".tmp" in p.name) == []


def test_the_operator_context_survives_a_crash_mid_write(client_ws, monkeypatch):
    client, ws = client_ws
    assert client.put(f"{BASE}/approver", json={"name": "First Name"}).status_code == 200
    path = ws / "literature" / "screening" / "operator_context.json"
    before = path.read_bytes()

    _crash(monkeypatch)
    with pytest.raises(OSError, match="power cut"):
        client.put(f"{BASE}/approver", json={"name": "Second Name"})
    assert path.read_bytes() == before
    assert json.loads(before)["operator_identity"] == "First Name"
    assert sorted(p.name for p in path.parent.iterdir() if ".tmp" in p.name) == []
