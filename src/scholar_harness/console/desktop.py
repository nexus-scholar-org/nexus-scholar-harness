"""The installed app's start: no terminal, one engine per user (M13 Part A).

`docs/roadmap/milestones/M13-installers.md` §4.1, §4.2 and §5.2 Part A. An
icon (a Start-menu entry, a desktop file, a macOS app) starts this, not
`nexus-scholar ui`: there is no console, the starting folder is whatever the
system chose, and nobody reads the output. So, before anything else:

1. standard output and error go to a log file in the user's log folder (one
   per launch, the last :data:`KEEP_LOGS` kept, none above :data:`LOG_CAP_BYTES`;
   e-mail addresses, launch codes and key-like strings are masked);
2. the working folder becomes the user's settings folder, so the search
   settings' `.env` and any relative cache path resolve there and never in the
   program folder; the search and recon caches default to the user's cache
   folder (an environment variable already set still wins);
3. a second start finds the running engine (`console/instance.py`), opens a
   fresh launch link from it and exits, starting no second server.

A failure the user can act on is shown in a small message window (Tk, as the
approval-code window), and the log names the error.

`nexus-scholar ui` in a terminal is unchanged: it keeps its own folder, its
output and its `.env`. Run this as `pythonw -m scholar_harness.console.desktop`
(or the bundle's windowed program); `--no-browser` starts the engine without
opening a browser (tests, CI), `--stop` stops the running engine.
"""

from __future__ import annotations

import faulthandler
import io
import os
import platform
import re
import sys
import threading
import time
import traceback
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import code_window
from .browser import LAUNCH_PATH

#: Points every per-user folder under one folder (tests, CI, a portable copy).
HOME_ENV = "NEXUS_APP_HOME"
#: Set to "0" to log failures without showing a message window (tests, CI).
DIALOGS_ENV = "NEXUS_APP_DIALOGS"
APP_NAME = "Nexus Scholar"
KEEP_LOGS = 5
LOG_CAP_BYTES = 5 * 1024 * 1024
LOG_PREFIX = "nexus-scholar-"

START_FAILED = (
    "Nexus Scholar could not start. The details are in the log file:\n{log}\n\n"
    "Please send that file to the person who gave you Nexus Scholar."
)
INCOMPLETE = "This installation is incomplete. Please reinstall Nexus Scholar."
CANNOT_WRITE = (
    "Nexus Scholar cannot write to {folder}. Free some space, or reconnect the folder if it is on "
    "a network or cloud drive, then start Nexus Scholar again."
)
LOG_FAILED = (
    "Nexus Scholar could not start: it cannot write its log folder {folder} ({error}). "
    "Free some space or check that folder, then start Nexus Scholar again."
)
NOT_ANSWERING = (
    "Nexus Scholar is already running on this computer but does not answer. Wait a minute and "
    "start it again; if this keeps happening, restart the computer."
)


@dataclass(frozen=True)
class AppFolders:
    settings: Path
    logs: Path
    cache: Path


def app_folders(env: dict[str, str] | None = None, system: str | None = None) -> AppFolders:
    """The user's own folders for settings, logs and cache (spec §4.1)."""
    env = dict(os.environ if env is None else env)
    system = system or sys.platform
    if env.get(HOME_ENV):
        home = Path(env[HOME_ENV]).expanduser()
        return AppFolders(home / "settings", home / "logs", home / "cache")
    user = Path(env.get("USERPROFILE") or env.get("HOME") or Path.home())
    if system == "win32":
        roaming = Path(env.get("APPDATA") or user / "AppData" / "Roaming")
        local = Path(env.get("LOCALAPPDATA") or user / "AppData" / "Local")
        return AppFolders(roaming / APP_NAME, local / APP_NAME / "Logs", local / APP_NAME / "Cache")
    if system == "darwin":
        library = user / "Library"
        return AppFolders(library / "Application Support" / APP_NAME, library / "Logs" / APP_NAME, library / "Caches" / APP_NAME)
    config = Path(env.get("XDG_CONFIG_HOME") or user / ".config")
    state = Path(env.get("XDG_STATE_HOME") or user / ".local" / "state")
    cache = Path(env.get("XDG_CACHE_HOME") or user / ".cache")
    return AppFolders(config / "nexus-scholar", state / "nexus-scholar" / "logs", cache / "nexus-scholar")


_MASKS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)"), r"\1***@\2"),
    (re.compile(r"(code=)[A-Za-z0-9_-]+"), r"\1***"),
    (re.compile(r"(Bearer\s+)[A-Za-z0-9._~+/=-]+"), r"\1***"),
    (re.compile(r"\b(sk-ant-|sk-|sk_|AIza)[A-Za-z0-9_-]{8,}"), r"\1***"),
)


def mask(text: str) -> str:
    """What a log line may hold: no e-mail address in full, no launch code, nothing key-like."""
    for pattern, replacement in _MASKS:
        text = pattern.sub(replacement, text)
    return text


class LogFile(io.TextIOBase):
    """A text stream into one launch's log file: masked, capped, safe across threads."""

    def __init__(self, path: Path, cap: int = LOG_CAP_BYTES):
        self.path = path
        self.raw = open(path, "a", encoding="utf-8", errors="replace", buffering=1)  # noqa: SIM115
        self._left = cap
        self._lock = threading.Lock()

    @property
    def encoding(self) -> str:  # type: ignore[override]
        return "utf-8"

    def writable(self) -> bool:
        return True

    def isatty(self) -> bool:
        return False

    def fileno(self) -> int:
        return self.raw.fileno()

    def write(self, text: str) -> int:
        size = len(text)
        clean = mask(str(text))
        data = len(clean.encode("utf-8", "replace"))
        with self._lock:
            if self.raw.closed or self._left <= 0:
                return size
            if data > self._left:
                clean = "\n[log file reached its size limit; nothing more is written]\n"
                self._left = 0
            else:
                self._left -= data
            self.raw.write(clean)
        return size

    def flush(self) -> None:
        with self._lock:
            if not self.raw.closed:
                self.raw.flush()

    def close(self) -> None:
        with self._lock:
            if not self.raw.closed:
                self.raw.close()
        super().close()


def _running(log: Path) -> bool:
    """Whether the process that writes ``log`` (its pid ends the name) still runs.

    Windows refuses to remove an open file anyway; POSIX would remove it.
    """
    if os.name == "nt":
        return False
    try:
        os.kill(int(log.stem.rsplit("-", 1)[1]), 0)
    except (ValueError, IndexError, ProcessLookupError):
        return False
    except OSError:  # it exists but belongs to someone else
        return True
    return True


def open_log(folder: Path, *, now: datetime | None = None, cap: int = LOG_CAP_BYTES) -> LogFile:
    """A new log file for this launch; the oldest ones beyond :data:`KEEP_LOGS` are removed.

    A log a running engine still writes is kept.
    """
    folder.mkdir(parents=True, exist_ok=True)
    old = sorted(folder.glob(f"{LOG_PREFIX}*.log"))
    for stale in old[: max(0, len(old) - (KEEP_LOGS - 1))]:
        if _running(stale):
            continue
        try:
            stale.unlink()
        except OSError:
            pass
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    return LogFile(folder / f"{LOG_PREFIX}{stamp}-{os.getpid()}.log", cap=cap)


def _dialogs_enabled() -> bool:
    return os.environ.get(DIALOGS_ENV, "1").strip() not in ("0", "false", "no", "off")


def tell_user(message: str) -> None:
    """A message window the user can read with no console; best-effort, never raises."""
    print(f"Shown to the user: {message}", flush=True)
    if not _dialogs_enabled():
        return
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showerror(APP_NAME, message, parent=root)
        root.destroy()
    except Exception:  # noqa: BLE001 - no Tk or no display: the log holds the message
        pass


def _writable(folder: Path) -> bool:
    try:
        folder.mkdir(parents=True, exist_ok=True)
        probe = folder / f".nexus-write-check-{os.getpid()}"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
    except OSError:
        return False
    return True


def _say(line: str) -> None:
    print(f"{datetime.now().isoformat(timespec='seconds')} {line}", flush=True)


def _header(folders: AppFolders) -> None:
    from scholar_harness import __version__

    _say(f"Nexus Scholar {__version__} starting")
    _say(f"System: {platform.platform()}; Python {platform.python_version()}; bundled: {bool(getattr(sys, 'frozen', False))}")
    _say(f"Settings folder: {folders.settings}")
    _say(f"Log folder: {folders.logs}")
    _say(f"Cache folder: {folders.cache}")


def _start(folders: AppFolders, *, stop: bool, open_browser: bool, tell: Callable[[str], None]) -> int:
    from . import instance as instance_module
    from .launcher import DEFAULT_PORT, Launcher, free_port, resolve_ui_dir
    from scholar_harness.workspace.catalog import most_recent, resolve_root

    _header(folders)
    for folder in (folders.settings, folders.cache):
        folder.mkdir(parents=True, exist_ok=True)
    os.chdir(folders.settings)
    os.environ.setdefault("SCHOLAR_CACHE_DIR", str(folders.cache / "search"))
    os.environ.setdefault("NEXUS_RECON_ROOT", str(folders.cache / "inception_recon"))

    if stop:
        answer = instance_module.ask(folders.settings, "stop", wait=2.0)
        _say("Asked the running engine to stop." if answer else "No running engine answered; nothing to stop.")
        return 0

    claim = instance_module.Instance(folders.settings)
    deadline = time.monotonic() + instance_module.ANSWER_WAIT_SECONDS
    while not claim.acquire():
        # Another engine holds the lock: ask it for a link. It may also be
        # stopping, in which case the lock comes free and this start goes on.
        answer = instance_module.ask(folders.settings, "launch-link", wait=1.0)
        if answer is not None:
            url = str(answer.get("url", ""))
            if not url.startswith(f"http://127.0.0.1:{answer.get('engine_port')}{LAUNCH_PATH}?"):
                _say("The running engine answered with an unexpected link; not opened.")
                tell(NOT_ANSWERING)
                return 1
            _say("Another Nexus Scholar engine is running; opening a new link from it.")
            if open_browser:
                webbrowser.open(url)
            return 0
        if time.monotonic() >= deadline:
            tell(NOT_ANSWERING)
            return 1
    problem: str | None = None
    try:
        ui_dir = resolve_ui_dir()
        root, source = resolve_root(None)
        if ui_dir is None:
            _say("No app bundle (the screens) was found.")
            problem = INCOMPLETE
        elif not _writable(root):
            _say(f"Workspaces folder: {root} (from the {source}) cannot be written.")
            problem = CANNOT_WRITE.format(folder=root)
        if problem is not None:
            return 1
        _say(f"Workspaces folder: {root} (from the {source})")
        launcher = Launcher(
            root=root,
            workspace=most_recent(root),
            ui_dir=ui_dir,
            port=free_port("127.0.0.1", DEFAULT_PORT),
            open_browser=open_browser,
            start_on_workspaces=True,
            say=_say,
            instance=claim,
            codes_on_terminal=False,  # standard output is the log: approval codes go to the window only
        )
        _say(f"Port: {launcher.port}")
        launcher.run()
        _say("Stopped.")
        return 0
    finally:
        claim.release()  # before any message, so a click meanwhile is not left waiting
        if problem is not None:
            tell(problem)


def main(argv: list[str] | None = None, *, tell: Callable[[str], None] = tell_user) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == [code_window.CHILD_FLAG]:
        return code_window.run_child()
    folders = app_folders()
    try:
        log = open_log(folders.logs)
    except OSError as exc:
        tell(LOG_FAILED.format(folder=folders.logs, error=exc))
        return 1
    saved_streams, saved_cwd = (sys.stdout, sys.stderr), os.getcwd()
    sys.stdout = sys.stderr = log
    own_faulthandler = not faulthandler.is_enabled()  # a test runner may have its own
    if own_faulthandler:
        faulthandler.enable(file=log.raw)
    try:
        unknown = [a for a in args if a not in ("--stop", "--no-browser")]
        if unknown:
            _say(f"Unknown options: {' '.join(unknown)}")
            return 2
        return _start(folders, stop="--stop" in args, open_browser="--no-browser" not in args, tell=tell)
    except KeyboardInterrupt:
        return 0
    except BaseException:  # noqa: BLE001 - also SystemExit from a server that could not bind
        traceback.print_exc(file=log)
        tell(START_FAILED.format(log=log.path))
        return 1
    finally:
        if own_faulthandler:
            faulthandler.disable()
        log.flush()
        sys.stdout, sys.stderr = saved_streams
        try:
            os.chdir(saved_cwd)
        except OSError:
            pass
        log.close()


def run() -> None:
    """The windowed program's entry point."""
    sys.exit(main())


if __name__ == "__main__":
    run()
