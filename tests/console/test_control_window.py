"""M13 Part A, second pull request: the installed app's control window (specification §4.2).

The decisions live in `ControlPanel`, which needs no display; the Tk view is
a thin layer, smoke-tested only where Tk and a display exist (CI's Linux
runner has neither, so that test is skipped there).
"""

from __future__ import annotations

import http.cookiejar
import json
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from scholar_harness.console import browser, control_window, desktop, instance, launcher
from scholar_harness.workspace import catalog
from scholar_harness.workspace import format as wsformat


@pytest.fixture
def ui(tmp_path):
    folder = tmp_path / "ui"
    for page in ("", "screening/home", "workspaces"):
        (folder / "en" / page).mkdir(parents=True, exist_ok=True)
        (folder / "en" / page / "index.html").write_text("<html>app</html>", encoding="utf-8")
    return folder


class Gate:
    def __init__(self, snap: dict[str, Any]):
        self.snap = snap

    def snapshot(self) -> dict[str, Any]:
        return self.snap


class State:
    pass


class FakeLauncher:
    """The attributes the panel reads, without a server."""

    def __init__(self, root: Path, workspace: Path | None = None):
        self.root, self.workspace = root, workspace
        self.app: Any = None
        self.opening: Path | None = None
        self._server: Any = None
        self.codes = browser.LaunchCodes("s")
        self.stopped = False

    def launch_url(self) -> str:
        return f"http://127.0.0.1:1/launch?code={self.codes.issue()}&next=%2Fen%2Fworkspaces%2F"

    def request_stop(self) -> None:
        self.stopped = True


def _with_gate(fake: FakeLauncher, snap: dict[str, Any]) -> None:
    fake.app = State()
    fake.app.state = State()
    fake.app.state.format_gate = Gate(snap)


def _panel(fake: FakeLauncher, tmp_path: Path, **kwargs: Any) -> control_window.ControlPanel:
    return control_window.ControlPanel(fake, settings_folder=tmp_path / "settings", log_file=tmp_path / "logs" / "x.log", **kwargs)


def test_the_status_line_names_the_folder_the_copy_and_a_refusal(tmp_path):
    fake = FakeLauncher(tmp_path / "reviews")
    panel = _panel(fake, tmp_path)
    assert panel.status() == f"Nexus Scholar is running on this computer. Your reviews are in {tmp_path / 'reviews'}."
    _with_gate(fake, {"state": "preparing", "title": "Sensor review", "done_bytes": 12_000_000, "total_bytes": 120_000_000})
    assert panel.status().endswith("Saving a copy of Sensor review before opening it: 12 MB of 120 MB.")
    _with_gate(fake, {"state": "refused", "title": "Sensor review", "refusal": {"message": "a newer version wrote it"}})
    assert panel.status().endswith("Sensor review was not opened: a newer version wrote it")
    _with_gate(fake, {"state": "ready", "title": "Sensor review"})
    assert "Saving" not in panel.status()
    _with_gate(fake, {"state": "refused", "title": "Old review", "refusal": {"message": "refused"}})
    fake.opening = tmp_path / "reviews" / "sensor"
    status = panel.status()  # a restart: the last app's refusal is not this review's
    assert status.endswith("Opening your review…") and "Old review" not in status
    fake.opening = None
    panel.engine_failed(RuntimeError("port gone"))
    assert panel.status() == control_window.FAILED and "RuntimeError: port gone" in panel.details()


def test_the_status_line_says_the_browser_may_be_blocked_only_after_a_minute_unused(tmp_path):
    now = [0.0]
    fake = FakeLauncher(tmp_path)
    panel = _panel(fake, tmp_path, clock=lambda: now[0])
    now[0] = 500.0  # a slow first start: the minute counts from the server's answer, not the window
    assert control_window.BROWSER_BLOCKED not in panel.status()
    fake._server = type("S", (), {"started": True})()
    assert control_window.BROWSER_BLOCKED not in panel.status()
    now[0] = 500.0 + control_window.BROWSER_HINT_SECONDS + 1
    assert control_window.BROWSER_BLOCKED in panel.status()
    assert fake.codes.redeem(fake.codes.issue())  # the browser used a link
    assert control_window.BROWSER_BLOCKED not in panel.status()
    quiet = _panel(FakeLauncher(tmp_path), tmp_path, clock=lambda: 10_000.0, open_browser_at_start=False)
    quiet.launcher._server = fake._server
    assert control_window.BROWSER_BLOCKED not in quiet.status()  # `--no-browser`: nothing was opened


def test_the_closing_question_names_what_is_in_progress(tmp_path, monkeypatch):
    ws = tmp_path / "review"
    ws.mkdir()
    fake = FakeLauncher(tmp_path, workspace=ws)
    panel = _panel(fake, tmp_path)
    assert panel.busy().question() == control_window.STOP_QUESTION

    monkeypatch.setattr(catalog, "busy", lambda _ws: {"run_active": True, "pairing_open": True})
    _with_gate(fake, {"state": "preparing", "title": "Review"})

    class Jobs:
        def active(self, workspace):
            return object() if workspace == ws.resolve() else None

    fake.app.state.discovery_jobs = Jobs()
    question = panel.busy().question()
    for words in ("A copy of your review is being saved", "An agent run is in progress.", "Approval codes are waiting",
                  "A search of the literature databases is in progress.", "Stopping Nexus Scholar now ends it.",
                  control_window.STOP_QUESTION):
        assert words in question


def test_the_buttons_open_a_new_link_stop_and_show_the_folders(tmp_path, monkeypatch):
    opened: list[str] = []
    shown: list[Path] = []
    monkeypatch.setattr(control_window.webbrowser, "open", opened.append)
    fake = FakeLauncher(tmp_path)
    panel = control_window.ControlPanel(fake, settings_folder=tmp_path / "settings", log_file=tmp_path / "logs" / "a.log",
                                        open_folder=shown.append)
    panel.open_in_browser()
    panel.open_in_browser()
    assert len(opened) == 2 and opened[0] != opened[1] and "/launch?code=" in opened[0]  # a fresh link each time
    panel.open_log_folder()
    panel.open_settings_folder()
    assert shown == [tmp_path / "logs", tmp_path / "settings"] and (tmp_path / "settings").is_dir()
    panel.stop()
    assert fake.stopped


def test_a_second_start_brings_the_window_forward(tmp_path, ui):
    panel_box: list[control_window.ControlPanel] = []
    claim = instance.Instance(tmp_path / "settings")
    app_launcher = launcher.Launcher(root=tmp_path / "root", workspace=None, ui_dir=ui, open_browser=False, say=lambda _m: None,
                                     instance=claim, on_second_start=lambda: panel_box[0].second_start())
    panel_box.append(_panel(app_launcher, tmp_path))  # type: ignore[arg-type]
    client = TestClient(app_launcher.build_app(None), base_url="http://127.0.0.1:8770")
    answer = client.post(f"{instance.PREFIX}/launch-link", headers={instance.SECRET_HEADER: claim.secret})
    assert answer.status_code == 200 and panel_box[0].raise_requested.is_set()


def test_the_launch_link_tells_the_app_how_the_engine_was_started(tmp_path, ui):
    quiet = {"root": tmp_path, "workspace": None, "ui_dir": ui, "open_browser": False, "say": lambda _m: None}
    for started_as in ("installed", "terminal"):
        app_launcher = launcher.Launcher(**quiet, started_as=started_as) if started_as == "installed" else launcher.Launcher(**quiet)
        client = TestClient(app_launcher.build_app(None), base_url="http://127.0.0.1:8770")
        answer = client.get(app_launcher.launch_url().split("8770", 1)[1], follow_redirects=False)
        assert answer.status_code == 303
        assert client.cookies.get(browser.STARTED_AS_COOKIE) == started_as
        used = client.get(app_launcher.launch_url().split("8770", 1)[1].replace("code=", "code=x"), follow_redirects=False)
        where = "Nexus Scholar window" if started_as == "installed" else "`nexus-scholar ui`"
        assert used.json()["detail"]["code"] == "LAUNCH_CODE_INVALID" and where in used.json()["detail"]["message"]
        no_session = TestClient(app_launcher.build_app(None), base_url="http://127.0.0.1:8770").get("/api/console/api/v1/workspaces")
        assert no_session.json()["detail"]["code"] == "TOKEN_REQUIRED" and where in no_session.json()["detail"]["message"]
        set_cookie = [h for h in answer.headers.get_list("set-cookie") if h.startswith(browser.STARTED_AS_COOKIE)]
        assert set_cookie and "httponly" not in set_cookie[0].lower()  # the page reads it; it is no secret


class FakeWindow:
    """Stands in for the Tk view: the user clicks Stop once the engine runs."""

    def __init__(self, panel, engine, root):
        self.panel, self.engine = panel, engine

    def run(self):
        deadline = time.time() + 10
        while self.engine.is_alive() and self.panel.launcher._server is None and time.time() < deadline:
            time.sleep(0.01)
        self.panel.stop()
        self.engine.join(timeout=10)


class LoopServer:
    def __init__(self, app, host, port):
        self.app, self.started, self.should_exit = app, True, False

    def run(self):
        while not self.should_exit:
            time.sleep(0.01)


def test_the_engine_runs_beside_the_window_and_stops_with_it(tmp_path, ui, monkeypatch):
    monkeypatch.setattr(control_window, "ControlWindow", FakeWindow)
    app_launcher = launcher.Launcher(root=tmp_path, workspace=None, ui_dir=ui, open_browser=False, say=lambda _m: None,
                                     server_factory=LoopServer)
    panel = _panel(app_launcher, tmp_path)  # type: ignore[arg-type]
    assert desktop.run_with_window(app_launcher, panel, root_window=object()) is False
    assert app_launcher._done is True


def test_an_engine_error_is_shown_in_the_window_not_lost(tmp_path, ui, monkeypatch):
    class Broken:
        def __init__(self, *_a):
            raise OSError("address in use")

    class WaitingWindow(FakeWindow):
        def run(self):
            self.engine.join(timeout=10)

    monkeypatch.setattr(control_window, "ControlWindow", WaitingWindow)
    app_launcher = launcher.Launcher(root=tmp_path, workspace=None, ui_dir=ui, open_browser=False, say=lambda _m: None,
                                     server_factory=Broken)
    panel = _panel(app_launcher, tmp_path)  # type: ignore[arg-type]
    assert desktop.run_with_window(app_launcher, panel, root_window=object()) is True
    assert panel.failure == "OSError: address in use" and panel.status() == control_window.FAILED


def test_the_installed_start_opens_the_window_when_it_can(tmp_path, ui, monkeypatch):
    monkeypatch.setenv(desktop.HOME_ENV, str(tmp_path / "home"))
    monkeypatch.setenv(catalog.ROOT_ENV, str(tmp_path / "workspaces"))
    monkeypatch.setenv(launcher.UI_DIR_ENV, str(ui))
    monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path / "c"))
    monkeypatch.setenv("NEXUS_RECON_ROOT", str(tmp_path / "r"))
    monkeypatch.setenv(desktop.DIALOGS_ENV, "1")
    used: list[tuple[Any, Any]] = []
    monkeypatch.setattr(control_window, "make_root", lambda: "a root")
    monkeypatch.setattr(desktop, "run_with_window", lambda la, panel, root: used.append((la.started_as, root)) or False)
    quiet = lambda _m: None  # noqa: E731 - no message box on a developer's desktop
    assert desktop.main(["--no-browser"], tell=quiet) == 0
    assert used == [("installed", "a root")]
    # No display or windows turned off: it runs headless, as before.
    monkeypatch.setattr(control_window, "make_root", lambda: None)
    monkeypatch.setattr(launcher.Launcher, "run", lambda self: None)
    assert desktop.main(["--no-browser"], tell=quiet) == 0 and len(used) == 1


def test_the_tk_window_builds_polls_and_closes(tmp_path):
    root = control_window.make_root()
    if root is None:
        pytest.skip("no Tk or no display here")
    root.withdraw()
    fake = FakeLauncher(tmp_path)
    panel = _panel(fake, tmp_path)
    engine = threading.Thread(target=lambda: time.sleep(0.5), daemon=True)
    engine.start()
    window = control_window.ControlWindow(panel, engine, root)
    assert window.status.cget("text").startswith("Nexus Scholar is running")
    panel.second_start()
    window.poll()
    assert not panel.raise_requested.is_set()  # the window came forward
    engine.join()
    window.poll()  # the engine ended without an error: the window closes
    with pytest.raises(Exception):
        root.winfo_exists()


def _wait_json(opener, url, timeout=20.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with opener.open(url, timeout=2) as response:
                return json.loads(response.read())
        except Exception:  # noqa: BLE001
            time.sleep(0.1)
    raise AssertionError(f"no answer from {url}")


@pytest.mark.slow
def test_while_a_copy_of_an_older_review_runs(tmp_path, ui, monkeypatch):
    """Coordinator's question: the status line and a second start while the copy runs.

    The copy runs in the background (a large review); the server answers
    meanwhile, workspace routes say WORKSPACE_PREPARING, the window says
    "Saving a copy…", the closing question names the copy, and a second start
    still gets a fresh link from the running engine.
    """
    root = tmp_path / "workspaces"
    catalog.create(root, "Older Review")
    ws = root / "older-review"
    (ws / wsformat.FORMAT_FILE).unlink(missing_ok=True)  # written before format versions: format 0
    release = threading.Event()
    real = wsformat.prepare_for_writing

    def slow(*args, **kwargs):
        release.wait(30)
        return real(*args, **kwargs)

    monkeypatch.setattr(wsformat, "prepare_for_writing", slow)
    monkeypatch.setattr(wsformat, "FOREGROUND_BYTES", 0)  # in the background, as for a large review
    claim = instance.Instance(tmp_path / "settings")
    assert claim.acquire()
    app_launcher = launcher.Launcher(root=root, workspace=ws, ui_dir=ui, port=launcher.free_port("127.0.0.1", 0),
                                     open_browser=False, say=lambda _m: None, instance=claim, started_as="installed")
    panel = _panel(app_launcher, tmp_path)  # type: ignore[arg-type]
    thread = threading.Thread(target=app_launcher.run, daemon=True)
    thread.start()
    try:
        deadline = time.time() + 20
        while instance.read_info(tmp_path / "settings") is None:
            assert time.time() < deadline
            time.sleep(0.05)
        assert "Saving a copy of Older Review before opening it" in panel.status()
        assert "A copy of your review is being saved" in panel.busy().question()
        answer = instance.ask(tmp_path / "settings", "launch-link", wait=5)  # a second click meanwhile
        assert answer is not None and "/launch?code=" in answer["url"]
        jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        opener.open(answer["url"], timeout=5).read()
        meta = f"http://127.0.0.1:{app_launcher.port}/api/console/api/v1/screening/summary"
        try:
            opener.open(meta, timeout=5)
            raise AssertionError("a workspace route answered while the copy ran")
        except urllib.error.HTTPError as exc:
            assert exc.code == 503 and json.loads(exc.read())["detail"]["code"] == "WORKSPACE_PREPARING"
        release.set()
        deadline = time.time() + 20
        while "Saving a copy" in panel.status():
            assert time.time() < deadline, "the status line kept saying the copy runs"
            time.sleep(0.05)
        assert panel.busy().reasons == ()
    finally:
        release.set()
        app_launcher.request_stop()
        thread.join(timeout=20)
        claim.release()
    assert not thread.is_alive()
