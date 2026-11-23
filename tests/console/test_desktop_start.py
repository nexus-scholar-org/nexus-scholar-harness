"""M13 Part A: the installed app's start with no terminal (spec §4.1, §4.2, §5.2 Part A).

Definition of done, each by a test here: a second start opens a new launch
link from the first engine and starts no second server; Stop ends the engine
and frees the port; a failure at start leaves a log naming the error and shows
the message; nothing is printed to a missing standard output. Also the
per-user folders, the log file's rules and the instance routes' refusals.
"""

from __future__ import annotations

import http.cookiejar
import os
import socket
import sys
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scholar_harness.console import browser, desktop, instance, launcher
from scholar_harness.workspace import catalog


@pytest.fixture
def ui(tmp_path):
    folder = tmp_path / "ui"
    for page in ("", "screening/home", "workspaces"):
        (folder / "en" / page).mkdir(parents=True, exist_ok=True)
        (folder / "en" / page / "index.html").write_text("<html>app</html>", encoding="utf-8")
    return folder


@pytest.fixture
def home(tmp_path, ui, monkeypatch):
    """Every per-user folder, the workspaces root and the screens under tmp_path."""
    monkeypatch.setenv(desktop.HOME_ENV, str(tmp_path / "home"))
    monkeypatch.setenv(desktop.DIALOGS_ENV, "0")
    monkeypatch.setenv(catalog.ROOT_ENV, str(tmp_path / "workspaces"))
    monkeypatch.setenv(launcher.UI_DIR_ENV, str(ui))
    monkeypatch.setenv("SCHOLAR_CACHE_DIR", str(tmp_path / "search-cache"))
    monkeypatch.setenv("NEXUS_RECON_ROOT", str(tmp_path / "recon"))
    monkeypatch.setattr(desktop.webbrowser, "open", lambda url: None)
    return desktop.app_folders()


def _logs(folders) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(folders.logs.glob("*.log")))


def test_the_user_folders_on_each_system():
    win = desktop.app_folders({"APPDATA": r"C:\U\R", "LOCALAPPDATA": r"C:\U\L"}, "win32")
    assert win == desktop.AppFolders(Path(r"C:\U\R") / "Nexus Scholar", Path(r"C:\U\L") / "Nexus Scholar" / "Logs",
                                     Path(r"C:\U\L") / "Nexus Scholar" / "Cache")
    mac = desktop.app_folders({"HOME": "/Users/r"}, "darwin")
    assert mac.settings == Path("/Users/r/Library/Application Support/Nexus Scholar")
    assert mac.logs == Path("/Users/r/Library/Logs/Nexus Scholar") and mac.cache == Path("/Users/r/Library/Caches/Nexus Scholar")
    linux = desktop.app_folders({"HOME": "/home/r"}, "linux")
    assert linux == desktop.AppFolders(Path("/home/r/.config/nexus-scholar"), Path("/home/r/.local/state/nexus-scholar/logs"),
                                       Path("/home/r/.cache/nexus-scholar"))
    assert desktop.app_folders({"HOME": "/home/r", "XDG_CONFIG_HOME": "/x"}, "linux").settings == Path("/x/nexus-scholar")
    assert desktop.app_folders({desktop.HOME_ENV: "/t"}, "win32").settings == Path("/t/settings")


def test_the_log_keeps_five_files_masks_and_stops_at_its_cap(tmp_path):
    for n in range(7):
        desktop.open_log(tmp_path, now=datetime(2026, 11, 24, 10, 0, n)).close()
    assert len(list(tmp_path.glob("*.log"))) == desktop.KEEP_LOGS
    log = desktop.open_log(tmp_path, cap=200)
    log.write("contact researcher@example.org, link /launch?code=abcDEF123_-x, key sk-ant-api03-abcdefghijk\n")
    log.write("x" * 500)
    log.write("after the cap\n")
    log.close()
    text = log.path.read_text(encoding="utf-8")
    assert "r***@example.org" in text and "researcher@" not in text
    assert "code=***" in text and "abcDEF123" not in text
    assert "sk-ant-***" in text and "abcdefghijk" not in text
    assert "size limit" in text and "after the cap" not in text and "x" * 500 not in text
    assert len(list(tmp_path.glob("*.log"))) == desktop.KEEP_LOGS


def test_one_lock_per_settings_folder(tmp_path):
    first, second = instance.Instance(tmp_path), instance.Instance(tmp_path)
    assert first.acquire() is True
    assert second.acquire() is False
    first.publish("127.0.0.1", 1234)
    assert instance.read_info(tmp_path)["port"] == 1234
    first.release()
    assert instance.read_info(tmp_path) is None  # its own file goes with it
    assert second.acquire() is True
    second.release()


def test_the_instance_routes_refuse_a_browser_and_a_wrong_secret(tmp_path, ui):
    claim = instance.Instance(tmp_path / "settings")
    app_launcher = launcher.Launcher(root=tmp_path / "root", workspace=None, ui_dir=ui, open_browser=False,
                                     say=lambda _: None, instance=claim)
    client = TestClient(app_launcher.build_app(None), base_url="http://127.0.0.1:8770")
    link = f"{instance.PREFIX}/launch-link"
    good = {instance.SECRET_HEADER: claim.secret}
    assert client.post(link).json()["detail"]["code"] == "INSTANCE_SECRET_REQUIRED"
    assert client.post(link, headers={instance.SECRET_HEADER: "wrong"}).status_code == 401
    browser_like = {**good, "Origin": "http://127.0.0.1:8770"}
    assert client.post(link, headers=browser_like).json()["detail"]["code"] == "INSTANCE_BROWSER_REFUSED"
    assert client.post(link, headers={**good, "Sec-Fetch-Site": "same-origin"}).status_code == 403
    assert client.post(link, headers={**good, "Origin": "http://evil.example"}).status_code == 403
    answer = client.post(link, headers=good)
    assert answer.status_code == 200 and "/launch?code=" in answer.json()["url"]
    # Not served under the browser prefix, and the console token is not the secret.
    assert client.post(f"/api/console{link}", headers=good).status_code in (400, 401, 404)
    assert client.post(link, headers={instance.SECRET_HEADER: app_launcher.token}).status_code == 401


def _engine(home_folders, root, ui):
    """A first engine as the installed app runs it: a real server holding the user's lock."""
    claim = instance.Instance(home_folders.settings)
    assert claim.acquire()
    app_launcher = launcher.Launcher(root=root, workspace=None, ui_dir=ui, port=launcher.free_port("127.0.0.1", 0),
                                     open_browser=False, say=lambda _: None, instance=claim)
    thread = threading.Thread(target=app_launcher.run, daemon=True)
    thread.start()
    deadline = time.time() + 15
    while instance.read_info(home_folders.settings) is None:
        assert time.time() < deadline, "the first engine never published its instance file"
        time.sleep(0.05)
    return claim, app_launcher, thread


def _port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


@pytest.mark.slow
def test_a_second_start_opens_a_link_from_the_first_engine_and_stop_frees_the_port(home, ui, tmp_path, monkeypatch):
    claim, first, thread = _engine(home, tmp_path / "workspaces", ui)
    opened: list[str] = []
    monkeypatch.setattr(desktop.webbrowser, "open", opened.append)
    built: list[object] = []
    monkeypatch.setattr(launcher.Launcher, "__init__", lambda *a, **k: built.append(a) or pytest.fail("a second engine was built"))
    try:
        assert desktop.main([]) == 0
        assert built == [] and first.restarts == 0 and len(opened) == 1
        assert opened[0].startswith(f"http://127.0.0.1:{first.port}/launch?code=")
        jar = http.cookiejar.CookieJar()
        browser_like = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        with browser_like.open(opened[0], timeout=5) as page:  # the link works once, on the first engine
            assert page.status == 200
        assert any(cookie.name == browser.SESSION_COOKIE for cookie in jar)
        assert "Another Nexus Scholar engine is running" in _logs(home)

        assert desktop.main(["--stop"]) == 0
        thread.join(timeout=15)
        assert not thread.is_alive()
        assert _port_free(first.port)
    finally:
        first.request_stop()
        thread.join(timeout=15)
        claim.release()
    assert instance.read_info(home.settings) is None


def test_a_held_lock_with_no_answer_says_so(home, monkeypatch):
    told: list[str] = []
    monkeypatch.setattr(instance, "ANSWER_WAIT_SECONDS", 0.3)
    holder = instance.Instance(home.settings)
    assert holder.acquire()
    try:
        assert desktop.main(["--no-browser"], tell=told.append) == 1
    finally:
        holder.release()
    assert told == [desktop.NOT_ANSWERING]


def test_a_failure_at_start_is_logged_and_shown_with_no_standard_output(home, monkeypatch):
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)

    def boom(self):
        print("the engine says something first")
        raise RuntimeError("could not bind the engine")

    monkeypatch.setattr(launcher.Launcher, "run", boom)
    told: list[str] = []
    assert desktop.main(["--no-browser"], tell=told.append) == 1
    assert sys.stdout is None and sys.stderr is None  # restored, and nothing was written to them
    log = _logs(home)
    assert "RuntimeError: could not bind the engine" in log and "the engine says something first" in log
    assert len(told) == 1 and told[0].startswith("Nexus Scholar could not start.")
    assert str(next(home.logs.glob("*.log"))) in told[0]
    assert instance.read_info(home.settings) is None and instance.Instance(home.settings).acquire()


def test_an_incomplete_install_is_named(home, monkeypatch):
    told: list[str] = []
    monkeypatch.setattr(launcher, "resolve_ui_dir", lambda: None)
    assert desktop.main(["--no-browser"], tell=told.append) == 1
    assert told == [desktop.INCOMPLETE]


def test_an_unwritable_workspaces_folder_is_named(home, monkeypatch):
    told: list[str] = []
    monkeypatch.setattr(desktop, "_writable", lambda folder: False)
    assert desktop.main(["--no-browser"], tell=told.append) == 1
    assert told[0].startswith("Nexus Scholar cannot write to ") and "workspaces" in told[0]


def test_the_engine_runs_in_the_settings_folder_with_the_user_cache(home, monkeypatch, tmp_path):
    for name in ("SCHOLAR_CACHE_DIR", "NEXUS_RECON_ROOT"):
        monkeypatch.delenv(name)
    seen: dict[str, str] = {}

    def record(self):
        seen.update(cwd=os.getcwd(), cache=os.environ["SCHOLAR_CACHE_DIR"], recon=os.environ["NEXUS_RECON_ROOT"],
                    landing=self.landing(), root=str(self.root))

    monkeypatch.setattr(launcher.Launcher, "run", record)
    before = os.getcwd()
    assert desktop.main(["--no-browser"]) == 0
    assert Path(seen["cwd"]) == home.settings.resolve() or Path(seen["cwd"]) == home.settings
    assert seen["cache"] == str(home.cache / "search") and seen["recon"] == str(home.cache / "inception_recon")
    assert seen["landing"] == "/en/workspaces/" and seen["root"] == str((tmp_path / "workspaces").resolve())
    assert os.getcwd() == before
    log = _logs(home)
    assert "Settings folder:" in log and "Workspaces folder:" in log and "Port:" in log


def test_an_environment_variable_still_wins_over_the_user_cache(home, monkeypatch):
    before = os.environ["SCHOLAR_CACHE_DIR"]
    monkeypatch.setattr(launcher.Launcher, "run", lambda self: None)
    assert desktop.main(["--no-browser"]) == 0
    assert os.environ["SCHOLAR_CACHE_DIR"] == before


def test_an_unknown_option_is_refused(home):
    assert desktop.main(["--frobnicate"]) == 2
    assert "Unknown options: --frobnicate" in _logs(home)
