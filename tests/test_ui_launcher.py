"""`nexus-scholar ui`: the launcher and its restart onto another workspace (M5-slim).

`docs/architecture/workspaces-api.md` §4: Open answers, then the launcher stops
the server and starts one on the other folder with the same port, token and
session, so the open browser tab keeps working and nothing else carries over.
"""

from __future__ import annotations

import http.cookiejar
import json
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scholar_harness.console import browser, launcher
from scholar_harness.workspace import catalog


@pytest.fixture
def ui(tmp_path):
    folder = tmp_path / "ui"
    (folder / "en").mkdir(parents=True)
    (folder / "en" / "index.html").write_text("<html>app</html>", encoding="utf-8")
    for page in ("screening/home", "workspaces"):
        (folder / "en" / page).mkdir(parents=True)
        (folder / "en" / page / "index.html").write_text(f"<html>{page}</html>", encoding="utf-8")
    return folder


@pytest.fixture
def root(tmp_path):
    folder = tmp_path / "root"
    catalog.create(folder, "First Review")
    catalog.create(folder, "Second Review")
    return folder


class FakeServer:
    """Runs nothing; on its first run it asks to open another workspace, as the route would."""

    def __init__(self, app, host, port, script):
        self.app, self.started, self.should_exit = app, True, False
        self.script = script

    def run(self):
        self.script(self)


def test_open_restarts_on_the_other_folder_with_the_same_token_and_session(root, ui):
    seen = []

    def script(server):
        seen.append(server.app)
        if len(seen) == 1:
            server.app.state.on_open(root / "second-review")
            assert server.should_exit is True  # the hook stops the running server

    app_launcher = launcher.Launcher(root=root, workspace=root / "first-review", ui_dir=ui, open_browser=False,
                                     server_factory=lambda app, host, port: FakeServer(app, host, port, script), say=lambda _: None)
    app_launcher.run()
    assert [a.state.workspace for a in seen] == [(root / "first-review").resolve(), (root / "second-review").resolve()]
    assert app_launcher.restarts == 1
    for app in seen:
        client = TestClient(app, base_url="http://127.0.0.1:8770", headers={"Authorization": f"Bearer {app_launcher.token}"})
        assert client.get("/api/v1/workspace/meta").status_code == 200
        cookie = TestClient(app, base_url="http://127.0.0.1:8770")
        cookie.cookies.set(browser.SESSION_COOKIE, app_launcher.session)
        assert cookie.get("/api/console/api/v1/workspaces").status_code == 200


def test_the_landing_page_and_the_empty_root(tmp_path, ui):
    empty = tmp_path / "empty"
    quiet = {"ui_dir": ui, "open_browser": False, "say": lambda _: None}
    assert launcher.Launcher(root=empty, workspace=None, **quiet).landing() == "/en/workspaces/"
    named = launcher.Launcher(root=empty, workspace=tmp_path, **quiet)
    assert named.landing() == "/en/screening/home/"
    assert "code=" in named.launch_url() and "next=%2Fen%2Fscreening%2Fhome%2F" in named.launch_url()
    # No workspace open: only the workspaces routes answer.
    app = launcher.Launcher(root=empty, workspace=None, **quiet)
    client = TestClient(app.build_app(None), base_url="http://127.0.0.1:8770", headers={"Authorization": f"Bearer {app.token}"})
    assert client.get("/api/v1/workspaces").json()["current"] is None
    assert client.get("/healthz").json() == {"status": "ok"}  # names no path (M6-hardening H3)
    assert client.get("/api/v1/workspace/meta").json()["detail"]["code"] == "WORKSPACE_NOT_VALID"
    assert client.post("/api/v1/workspaces", json={"title": "Fresh"}).status_code == 201


def test_resolve_ui_dir_prefers_the_environment(tmp_path, ui, monkeypatch):
    monkeypatch.setenv(launcher.UI_DIR_ENV, str(ui))
    assert launcher.resolve_ui_dir() == ui.resolve()
    monkeypatch.setenv(launcher.UI_DIR_ENV, str(tmp_path / "nothing"))
    found = launcher.resolve_ui_dir()
    assert found is None or (found / "en" / "index.html").is_file()


def _wait(url, opener, timeout=15.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with opener.open(url, timeout=2) as response:
                return json.loads(response.read())
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.1)
    raise AssertionError(f"no answer from {url}")


@pytest.mark.slow
def test_a_real_server_restarts_and_the_browser_session_survives(root, ui):
    port = launcher.free_port("127.0.0.1", 0)
    app_launcher = launcher.Launcher(root=root, workspace=root / "first-review", ui_dir=ui, port=port,
                                     open_browser=False, say=lambda _: None)
    thread = threading.Thread(target=app_launcher.run, daemon=True)
    thread.start()
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    base = f"http://127.0.0.1:{port}"
    _wait(f"{base}/healthz", opener)
    opener.open(app_launcher.launch_url(), timeout=5).read()  # sets the session cookie
    meta = f"{base}/api/console/api/v1/workspace/meta"
    assert _wait(meta, opener)["workspace"] == str((root / "first-review").resolve())

    request = urllib.request.Request(f"{base}/api/console/api/v1/workspaces/open", data=json.dumps({"slug": "second-review"}).encode(),
                                     headers={"Content-Type": "application/json", "Origin": base}, method="POST")
    with opener.open(request, timeout=5) as response:
        assert response.status == 202
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            if _wait(meta, opener, timeout=2)["workspace"] == str((root / "second-review").resolve()):
                break
        except AssertionError:
            pass
        time.sleep(0.1)
    else:
        raise AssertionError("the server did not restart on the second workspace")
    assert app_launcher.restarts == 1
    app_launcher._server.should_exit = True
    thread.join(timeout=10)
    assert not thread.is_alive()


def test_the_cli_refuses_without_a_bundle_or_with_a_bad_workspace(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from scholar_harness.cli import app

    monkeypatch.setattr(launcher, "resolve_ui_dir", lambda: None)
    result = CliRunner().invoke(app, ["ui", "--root", str(tmp_path)])
    assert result.exit_code == 1 and "no app bundle" in result.output
    monkeypatch.setattr(launcher, "resolve_ui_dir", lambda: Path(tmp_path))
    bad = CliRunner().invoke(app, ["ui", "--workspace", str(tmp_path), "--root", str(tmp_path)])
    assert bad.exit_code == 1 and "Not a Nexus Scholar workspace" in bad.output
