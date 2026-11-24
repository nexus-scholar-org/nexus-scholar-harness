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
    for page in ("", "screening/home", "workspaces", "settings"):
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


def test_the_log_keeps_five_files_masks_and_stops_at_its_cap(tmp_path, monkeypatch):
    # One process makes every file here, so each name ends with this live pid;
    # on POSIX that would keep them all (see test_a_running_engines_log_is_not_pruned).
    monkeypatch.setattr(desktop, "_running", lambda log: False)
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
    """Whether a new engine could listen on ``port`` now.

    On POSIX the probe sets SO_REUSEADDR as uvicorn's own socket does: the
    stopped server's closed connections stay in TIME_WAIT for a while, and a
    plain bind is refused by them although nothing listens. A live listener
    still refuses the bind. On Windows the option would let the bind through
    beside a live listener, so it is not set there.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if os.name != "nt":
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
    probe = instance.Instance(home.settings)
    assert instance.read_info(home.settings) is None and probe.acquire()
    probe.release()


def test_an_incomplete_install_is_named_after_the_lock_is_freed(home, monkeypatch):
    told: list[tuple[str, bool]] = []

    def tell(message: str) -> None:
        # A second click while this message is open must not wait for a dead engine.
        probe = instance.Instance(home.settings)
        free = probe.acquire()
        probe.release()
        told.append((message, free))

    monkeypatch.setattr(launcher, "resolve_ui_dir", lambda: None)
    assert desktop.main(["--no-browser"], tell=tell) == 1
    assert told == [(desktop.INCOMPLETE, True)]


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
                    landing=self.landing(), root=str(self.root), terminal=self.codes_on_terminal)

    monkeypatch.setattr(launcher.Launcher, "run", record)
    before = os.getcwd()
    assert desktop.main(["--no-browser"]) == 0
    assert Path(seen["cwd"]) == home.settings.resolve() or Path(seen["cwd"]) == home.settings
    assert seen["cache"] == str(home.cache / "search") and seen["recon"] == str(home.cache / "inception_recon")
    # M13 Part B: the installed start's first run opens setup (answer 3); a saved choice lands on Workspaces.
    assert seen["landing"] == "/en/settings/?setup=1" and seen["root"] == str((tmp_path / "workspaces").resolve())
    assert seen["terminal"] is False  # its output is the log: approval codes go to the window only
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


def test_a_log_folder_that_cannot_be_made_still_shows_a_message(home, monkeypatch):
    def refuse(*_a, **_k):
        raise PermissionError("denied")

    monkeypatch.setattr(desktop, "open_log", refuse)
    told: list[str] = []
    assert desktop.main(["--no-browser"], tell=told.append) == 1
    assert len(told) == 1 and told[0].startswith("Nexus Scholar could not start: it cannot write its log folder")


def test_a_link_to_another_port_is_not_opened(home, monkeypatch):
    holder = instance.Instance(home.settings)
    assert holder.acquire()
    opened: list[str] = []
    monkeypatch.setattr(desktop.webbrowser, "open", opened.append)
    monkeypatch.setattr(instance, "ask", lambda *a, **k: {"url": "http://127.0.0.1:9/launch?code=x", "engine_port": 1234})
    told: list[str] = []
    try:
        assert desktop.main([], tell=told.append) == 1
    finally:
        holder.release()
    assert opened == [] and told == [desktop.NOT_ANSWERING]


def test_a_start_while_the_engine_is_stopping_goes_on_once_the_lock_is_free(home, monkeypatch):
    holder = instance.Instance(home.settings)
    assert holder.acquire()
    threading.Timer(0.5, holder.release).start()  # the old engine finishes stopping
    ran: list[bool] = []
    monkeypatch.setattr(launcher.Launcher, "run", lambda self: ran.append(True))
    assert desktop.main(["--no-browser"]) == 0
    assert ran == [True]


def test_a_slow_first_start_is_still_published_and_a_failed_publish_still_opens_the_browser(tmp_path, ui, monkeypatch):
    """Review P2: the old wait gave up after 200 polls (10 s) and never published."""
    polls = {"n": 0}

    class SlowServer:
        should_exit = False

        @property
        def started(self):
            return polls["n"] > 500

    monkeypatch.setattr(launcher.time, "sleep", lambda _s: polls.__setitem__("n", polls["n"] + 1))
    opened: list[str] = []
    monkeypatch.setattr(launcher.webbrowser, "open", opened.append)
    published: list[int] = []

    class Claim:
        def router(self, **_k):
            return instance.router("s", launch_link=lambda: "", stop=lambda: None)

        def publish(self, host, port):
            published.append(port)
            raise PermissionError("the file is held by another program")

    app_launcher = launcher.Launcher(root=tmp_path, workspace=None, ui_dir=ui, port=8799, open_browser=True,
                                     say=lambda _m: None, instance=Claim())  # type: ignore[arg-type]
    app_launcher._server = SlowServer()
    app_launcher._when_ready("http://127.0.0.1:8799/launch?code=x")
    assert polls["n"] > 500 and published == [8799] * launcher.PUBLISH_ATTEMPTS and opened == ["http://127.0.0.1:8799/launch?code=x"]


@pytest.mark.skipif(os.name == "nt", reason="Windows refuses to remove an open file; POSIX would remove it")
def test_a_running_engines_log_is_not_pruned(tmp_path):
    for n in range(desktop.KEEP_LOGS):
        (tmp_path / f"{desktop.LOG_PREFIX}20260101-00000{n}-999999999.log").write_text("old")
    live = tmp_path / f"{desktop.LOG_PREFIX}20250101-000000-{os.getpid()}.log"
    live.write_text("running")
    desktop.open_log(tmp_path).close()
    assert live.exists()


def test_the_ready_wait_ends_when_the_first_server_never_started(tmp_path, ui):
    """Review round 2: a server whose run() returns without starting left the wait thread spinning."""

    class NeverStarts:
        started, should_exit = False, False

        def __init__(self, *_a):
            pass

        def run(self):
            return None

    app_launcher = launcher.Launcher(root=tmp_path, workspace=None, ui_dir=ui, open_browser=False, say=lambda _m: None,
                                     server_factory=NeverStarts, instance=instance.Instance(tmp_path / "settings"))
    app_launcher.run()
    assert app_launcher._done is True
    waiter = threading.Thread(target=app_launcher._when_ready, args=(None,), daemon=True)
    waiter.start()
    waiter.join(timeout=2)
    assert not waiter.is_alive()


def test_a_publish_that_clashes_once_is_tried_again(tmp_path, ui, monkeypatch):
    monkeypatch.setattr(launcher.time, "sleep", lambda _s: None)
    attempts: list[int] = []
    said: list[str] = []

    class Claim:
        def router(self, **_k):
            return instance.router("s", launch_link=lambda: "", stop=lambda: None)

        def publish(self, host, port):
            attempts.append(port)
            if len(attempts) < 3:
                raise PermissionError("held by a reader")

    class Started:
        started, should_exit = True, False

    app_launcher = launcher.Launcher(root=tmp_path, workspace=None, ui_dir=ui, port=8798, open_browser=False,
                                     say=said.append, instance=Claim())  # type: ignore[arg-type]
    app_launcher._server = Started()
    app_launcher._when_ready(None)
    assert attempts == [8798, 8798, 8798] and said == []


def test_the_installed_start_reads_dotenv_and_the_cache_from_its_own_folders(home, monkeypatch):
    """Review of M13 Part B, P1: the search settings are read again after the start moves into its settings folder."""
    for name in ("SCHOLAR_CACHE_DIR", "NEXUS_RECON_ROOT", "SCHOLAR_MAILTO"):
        monkeypatch.setenv(name, "placeholder")  # recorded, so the test's end restores the original state
        monkeypatch.delenv(name)
    home.settings.mkdir(parents=True, exist_ok=True)
    (home.settings / ".env").write_text("SCHOLAR_MAILTO=dotenv@example.org\n", encoding="utf-8")
    seen: dict[str, str | None] = {}

    def record(self):
        from scholar_search.config import settings

        seen.update(mailto=settings.mailto, cache=str(settings.cache_dir))

    monkeypatch.setattr(launcher.Launcher, "run", record)
    assert desktop.main(["--no-browser"]) == 0  # tests/conftest.py puts the shared settings back afterwards
    assert seen == {"mailto": "dotenv@example.org", "cache": str(home.cache / "search")}


def test_forget_removes_settings_keys_logs_and_cache_but_never_a_review(home, tmp_path):
    """M13 Part W: the uninstaller's "Also remove my settings and saved keys" (specification §4.6)."""
    from scholar_search import user_settings

    reviews = tmp_path / "workspaces"
    catalog.create(reviews, "Kept Review")
    user_settings.write_settings(contact_email="r@example.org")
    user_settings.store_key("openalex", "oa-MADE-UP")
    user_settings.store_key("gemini", "AIza-MADE-UP", use_file=True)
    for folder in (home.logs, home.cache):
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "something").write_text("x", encoding="utf-8")
    (home.cache / desktop.KEPT_CACHE / "sessions").mkdir(parents=True)
    (home.cache / desktop.KEPT_CACHE / "sessions" / "probe.json").write_text("{}", encoding="utf-8")
    assert desktop.main([desktop.FORGET_FLAG]) == 0
    assert user_settings.stored_key("openalex") == (None, None) and user_settings.stored_key("gemini") == (None, None)
    for folder in (home.settings, home.logs):
        assert not folder.exists(), folder
    assert not (home.cache / "something").exists()
    # Review of Part W, P2: an unfinished draft's explorations in progress stay.
    assert (home.cache / desktop.KEPT_CACHE / "sessions" / "probe.json").is_file()
    assert (reviews / "kept-review" / "project.json").is_file()  # the review stays


def test_forget_keeps_a_folder_that_holds_the_reviews(home, tmp_path, monkeypatch):
    from scholar_search import user_settings

    inside = home.settings / "reviews"  # a reviews folder chosen inside the settings folder
    monkeypatch.setenv(catalog.ROOT_ENV, str(inside))
    catalog.create(inside, "Inside Review")
    user_settings.write_settings(contact_email="r@example.org")
    assert desktop.main([desktop.FORGET_FLAG]) == 0
    assert not user_settings.settings_path().exists()
    assert (inside / "inside-review" / "project.json").is_file()


def test_forget_stops_a_running_engine_first(home, monkeypatch):
    """Review of Part W, P3: a running engine holds its files and keys, so it is stopped and waited for."""
    from scholar_search import user_settings

    holder = instance.Instance(home.settings)
    assert holder.acquire()
    holder.publish("127.0.0.1", 9)
    asked: list[str] = []

    def stop(folder, action, wait=0):
        asked.append(action)
        holder.release()  # the engine stops and lets go of its lock
        return {"stopping": True}

    monkeypatch.setattr(instance, "ask", stop)
    user_settings.write_settings(contact_email="r@example.org")
    assert desktop.main([desktop.FORGET_FLAG]) == 0
    assert asked == ["stop"] and not user_settings.settings_path().exists()


def test_stop_removes_a_leftover_engine_file_and_keeps_a_live_one(home):
    """Review of Part W, round 2: a forced end leaves engine.json; --stop clears it only when no engine holds the lock."""
    home.settings.mkdir(parents=True, exist_ok=True)
    leftover = home.settings / instance.INFO_NAME
    leftover.write_text('{"pid": 1, "host": "127.0.0.1", "port": 9, "secret": "x"}', encoding="utf-8")
    assert desktop.main(["--stop"]) == 0
    assert not leftover.exists()  # no engine answered and none held the lock

    holder = instance.Instance(home.settings)
    assert holder.acquire()
    holder.publish("127.0.0.1", 9)  # a live engine that does not answer (port 9)
    try:
        assert desktop.main(["--stop"]) == 0
        assert holder.info_path.exists()  # a held lock: nothing removed
    finally:
        holder.release()
