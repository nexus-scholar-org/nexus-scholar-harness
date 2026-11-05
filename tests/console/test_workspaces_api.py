"""Workspaces routes (M5-slim; `docs/architecture/workspaces-api.md` §6).

Workspaces are created by the real scaffold under a temporary root; the
launcher's restart hook is a recorder, so no server is restarted here.
"""

from __future__ import annotations

import json
import os

import pytest
from fastapi.testclient import TestClient

from scholar_harness.console import create_app
from scholar_harness.screening import agent_runs as runs
from scholar_harness.workspace import catalog

DESKTOP, PHONE = "desk-token", "phone-token"
BASE = "/api/v1/workspaces"


def _journal(ws):
    return [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.fixture
def root(tmp_path):
    folder = tmp_path / "root"
    folder.mkdir()
    return folder


@pytest.fixture
def current(root):
    catalog.create(root, "Current Review")
    return root / "current-review"


def _client(current, root, opened=None):
    app = create_app(current, token=DESKTOP, phone_tokens={PHONE}, workspaces_root=root,
                     on_open=(opened.append if opened is not None else None))
    return TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {DESKTOP}"})


def test_list_shows_valid_workspaces_and_counts_the_skipped_ones(root, current):
    catalog.create(root, "Second Review")
    (root / "notes").mkdir()                       # not a workspace
    (root / ".hidden").mkdir()                     # never listed
    (root / "loose.txt").write_text("x", encoding="utf-8")
    (root / "second-review" / "nested").mkdir()    # no recursion
    body = _client(current, root).get(BASE).json()
    assert body["root"] == str(root.resolve()) and body["root_source"] == "flag" and body["writable"] is True
    assert [i["slug"] for i in body["items"]] == ["current-review", "second-review"]
    assert body["skipped_count"] == 1 and body["busy"] == {"run_active": False, "pairing_open": False}
    first = body["items"][0]
    assert first["is_current"] and first["title"] == "Current Review" and os.path.isabs(first["path"])
    assert (first["has_corpus"], first["screening_started"]) == (False, False)
    assert first["last_event"]["action"] == "GENESIS"
    shown = _client(current, root).get(BASE, params={"include_invalid": "true"}).json()
    notes = next(i for i in shown["items"] if i["slug"] == "notes")
    assert notes["valid"] is False and "protocol.json" in notes["invalid_reason"]


def test_a_workspace_without_support_files_still_lists(root, current):
    (current / ".mcp.json").unlink()
    assert [i["slug"] for i in _client(current, root).get(BASE).json()["items"]] == ["current-review"]


def test_a_symlink_out_of_the_root_is_not_listed(root, current, tmp_path):
    outside = tmp_path / "outside"
    catalog.create(tmp_path, "Outside")
    try:
        os.symlink(outside, root / "link", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available here")
    assert "link" not in [i["slug"] for i in _client(current, root).get(BASE, params={"include_invalid": "true"}).json()["items"]]


def test_create_writes_the_canonical_layout_and_journals_genesis(root, current):
    client = _client(current, root)
    created = client.post(BASE, json={"title": "Weed Mapping with UAVs"})
    assert created.status_code == 201
    body = created.json()
    ws = root / "weed-mapping-with-uavs"
    assert body["slug"] == "weed-mapping-with-uavs" and body["path"] == str(ws.resolve()) and body["protocol_fingerprint"].startswith("sha256:")
    for name in ("protocol.json", "project.json", "intent.json", "audit/journal.jsonl", ".mcp.json", ".env.example"):
        assert (ws / name).is_file(), name
    rows = _journal(ws)
    assert [r["action"] for r in rows] == ["PROJECT_INITIALIZED", "GENESIS"]
    # As for the CLI: PROJECT_INITIALIZED names the workspace manager, GENESIS the caller.
    assert [r["agent_or_tool"] for r in rows] == ["workspace-manager", catalog.UI_AGENT]

    again = client.post(BASE, json={"title": "Weed mapping with UAVs"})
    assert again.status_code == 409 and again.json()["detail"]["code"] == "WORKSPACE_EXISTS"
    (root / "plain-folder").mkdir()
    taken = client.post(BASE, json={"title": "Plain folder"})
    assert taken.status_code == 409 and taken.json()["detail"]["code"] == "WORKSPACE_EXISTS"
    assert list((root / "plain-folder").iterdir()) == []  # an existing folder is never touched
    empty = client.post(BASE, json={"title": "!!!"})
    assert empty.status_code == 422 and empty.json()["detail"]["code"] == "WORKSPACE_TITLE_INVALID"


def test_a_create_that_fails_part_way_leaves_nothing(root, current, monkeypatch):
    def broken(target, title, *, agent, timestamp=None):
        target.mkdir(parents=True)
        (target / "protocol.json").write_text("{}", encoding="utf-8")
        raise OSError("disk full")

    monkeypatch.setattr("scholar_harness.inception.genesis.scaffold_placeholder_workspace", broken)
    with pytest.raises(catalog.WorkspaceRefused) as refused:
        catalog.create(root, "Half Made")
    assert refused.value.code == "WORKSPACE_ROOT_UNAVAILABLE" and "disk full" in refused.value.message
    assert not (root / "half-made").exists()


def test_open_restarts_through_the_launcher_and_journals_nothing(root, current):
    catalog.create(root, "Next Review")
    before = _journal(root / "next-review")
    opened = []
    client = _client(current, root, opened)
    answer = client.post(f"{BASE}/open", json={"slug": "next-review"})
    assert answer.status_code == 202 and answer.json()["restarting"] is True
    assert opened == [(root / "next-review").resolve()]
    assert _journal(root / "next-review") == before
    same = client.post(f"{BASE}/open", json={"slug": "current-review"})
    assert same.status_code == 200 and same.json()["restarting"] is False and len(opened) == 1


def test_open_refuses_bad_targets_and_a_server_without_a_launcher(root, current):
    (root / "notes").mkdir()
    catalog.create(root, "Next Review")
    client = _client(current, root, [])
    for slug, code, status in (("notes", "WORKSPACE_NOT_VALID", 409), ("gone", "WORKSPACE_NOT_VALID", 409),
                               ("..", "WORKSPACE_PATH_REFUSED", 422), ("../x", "WORKSPACE_PATH_REFUSED", 422)):
        answer = client.post(f"{BASE}/open", json={"slug": slug})
        assert (answer.status_code, answer.json()["detail"]["code"]) == (status, code), slug
    unsupported = _client(current, root).post(f"{BASE}/open", json={"slug": "next-review"})
    assert unsupported.status_code == 501 and unsupported.json()["detail"]["code"] == "RESTART_UNSUPPORTED"


def test_open_is_refused_while_a_run_is_live_or_an_approval_is_open(root, current, monkeypatch):
    catalog.create(root, "Next Review")
    opened = []
    client = _client(current, root, opened)
    # A run live in this engine.
    run_id = "RUN-" + "a" * 24
    live = runs._Live(current, {"run_id": run_id, "state": "running"})
    with runs._START_GUARD:
        runs._acquire(current, run_id)
        with runs._LIVE_GUARD:
            runs._LIVE[runs._key(current, run_id)] = live
    try:
        busy = client.post(f"{BASE}/open", json={"slug": "next-review"})
        assert busy.status_code == 409 and busy.json()["detail"]["code"] == "WORKSPACE_BUSY"
        assert busy.json()["detail"]["details"] == {"run_active": True, "pairing_open": False}
        assert client.get(BASE).json()["busy"]["run_active"] is True
    finally:
        with runs._LIVE_GUARD:
            runs._LIVE.pop(runs._key(current, run_id), None)
        runs._release(current, run_id)
    # A staged approval pairing.
    (current / "literature" / "screening").mkdir(parents=True, exist_ok=True)
    (current / "literature" / "screening" / "batch_001.json").write_text("{}", encoding="utf-8")
    from scholar_harness.authority import pairing

    monkeypatch.setattr(pairing, "pairing_status", lambda ws, batch: {"state": pairing.PAIRING_STATE_STAGED})
    staged = client.post(f"{BASE}/open", json={"slug": "next-review"})
    assert staged.status_code == 409 and staged.json()["detail"]["details"] == {"run_active": False, "pairing_open": True}
    assert opened == []


def test_the_root_resolves_flag_then_environment_then_default(tmp_path):
    assert catalog.resolve_root(tmp_path, env={catalog.ROOT_ENV: "/elsewhere"}) == (tmp_path.resolve(), "flag")
    assert catalog.resolve_root(None, env={catalog.ROOT_ENV: str(tmp_path)}) == (tmp_path.resolve(), "environment")
    path, source = catalog.resolve_root(None, env={})
    assert source == "default" and path.parts[-3:] == ("Documents", "Nexus Scholar", "workspaces")


def test_a_phone_token_reaches_none_of_the_workspaces_routes(root, current):
    client = _client(current, root, [])
    phone = {"Authorization": f"Bearer {PHONE}"}
    for method, path, body in (("get", BASE, None), ("post", BASE, {"title": "x"}), ("post", f"{BASE}/open", {"slug": "current-review"})):
        answer = getattr(client, method)(path, headers=phone, **({"json": body} if body else {}))
        assert answer.status_code == 403 and answer.json()["detail"]["code"] == "TOKEN_SCOPE_REFUSED", path
