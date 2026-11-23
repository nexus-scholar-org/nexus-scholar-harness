"""`nexus-scholar ui`: the packaged app's launcher (M5-slim; plan §5.3 stage 1).

One process serves the static UI and the console API on one loopback origin.
The launcher owns that server: it picks the port, makes the per-launch token
and session secret, opens the browser on a one-time launch link, and, when the
workspace screen asks to open another workspace, stops the server and starts a
new one on that folder with the same port, token and session
(`docs/architecture/workspaces-api.md` §4). Nothing else crosses a restart.

The installed app (M13 Part A, `console/desktop.py`) also gives the launcher
an `instance.Instance`: once the server answers, the launcher publishes its
port and secret, and serves the routes a second launcher uses to ask for a
fresh launch link or to stop this engine.

A restart or a stop must not wait for the browser: uvicorn's graceful
shutdown waits for every open connection with no time limit unless
`timeout_graceful_shutdown` is set, and a page holding an event stream kept
the old server alive (release walk 1.1.0b7, fault 1).
"""

from __future__ import annotations

import importlib.util
import os
import secrets
import socket
import sys
import threading
import time
import webbrowser
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from . import browser, code_window
from .instance import Instance

UI_DIR_ENV = "NEXUS_UI_DIR"
DEFAULT_PORT = 8770
#: Seconds a stopping server waits for open responses (event streams) before it cancels them.
RESTART_GRACE_SECONDS = 3
_BUNDLE_PACKAGE = "scholar_harness_data"
_REPO_EXPORT = Path(__file__).resolve().parents[3] / "apps" / "research-ui" / ".next-export"


def resolve_ui_dir() -> Path | None:
    """The static UI to serve: `NEXUS_UI_DIR`, the wheel's bundle, else a repo build."""
    candidates: list[Path] = []
    if os.environ.get(UI_DIR_ENV):
        candidates.append(Path(os.environ[UI_DIR_ENV]).expanduser())
    try:
        spec = importlib.util.find_spec(_BUNDLE_PACKAGE)
    except (ImportError, ValueError):
        spec = None
    candidates += [Path(loc) / "ui" for loc in (getattr(spec, "submodule_search_locations", None) or [])]
    candidates.append(_REPO_EXPORT)
    return next((c.resolve() for c in candidates if (c / "en" / "index.html").is_file()), None)


def free_port(host: str, preferred: int) -> int:
    """`preferred` when it is free, else one the OS picks; fixed for the whole launch."""
    for port in (preferred, 0):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind((host, port))
            except OSError:
                continue
            return probe.getsockname()[1]
    raise OSError(f"no free port on {host}")


class Launcher:
    """Serve one workspace at a time and restart on another when asked."""

    def __init__(
        self,
        *,
        root: Path,
        workspace: Path | None,
        ui_dir: Path,
        host: str = "127.0.0.1",
        port: int = DEFAULT_PORT,
        open_browser: bool = True,
        start_on_workspaces: bool = False,
        server_factory: Callable[[Any, str, int], Any] | None = None,
        say: Callable[[str], None] = print,
        instance: Instance | None = None,
    ):
        self.root, self.workspace, self.ui_dir = root, workspace, ui_dir
        self.host, self.port = host, port
        self.open_browser, self.say = open_browser, say
        self.start_on_workspaces = start_on_workspaces or workspace is None
        self.token = secrets.token_urlsafe(32)
        self.session = secrets.token_urlsafe(32)
        self.codes = browser.LaunchCodes(self.session)
        self.server_factory = server_factory or _uvicorn_server
        self.instance = instance
        self._next: Path | None = None
        self._stopping = False
        self._server: Any = None
        self.restarts = 0

    def build_app(self, workspace: Path | None) -> Any:
        from . import create_app
        from .serve import LOOPBACK_HOSTS

        return create_app(
            workspace,
            token=self.token,
            trusted_hosts=LOOPBACK_HOSTS,
            workspaces_root=self.root,
            on_open=self.request_open,
            browser_session=self.session,
            launch_codes=self.codes,
            ui_dir=self.ui_dir,
            # Finding 38: the app may have been started for the researcher, with
            # its terminal out of sight; the codes also show in a desktop window.
            code_window=code_window.reveal,
            local_routes=(
                self.instance.router(launch_link=self.launch_url, stop=self.request_stop)
                if self.instance is not None
                else None
            ),
        )

    def request_open(self, path: Path) -> None:
        """The workspaces route's restart hook: stop this server, start one on `path`."""
        if self._stopping:
            return
        self._next = Path(path)
        if self._server is not None:
            self._server.should_exit = True

    def request_stop(self) -> None:
        """Stop the engine: the running server ends and no other starts."""
        self._stopping = True
        self._next = None
        if self._server is not None:
            self._server.should_exit = True

    def landing(self) -> str:
        """Where the first page opens: the workspaces screen unless one was named."""
        return "/en/workspaces/" if self.start_on_workspaces else "/en/screening/home/"

    def launch_url(self) -> str:
        query = urlencode({"code": self.codes.issue(), "next": self.landing()})
        return f"http://{self.host}:{self.port}{browser.LAUNCH_PATH}?{query}"

    def run(self) -> None:
        first = True
        while not self._stopping:
            app = self.build_app(self.workspace)
            self._server = self.server_factory(app, self.host, self.port)
            if first:
                url = self.launch_url()
                self.say(f"Nexus Scholar is running at http://{self.host}:{self.port}/ (press Ctrl+C to stop)")
                if not self.open_browser:
                    self.say(f"Open this one-time link in your browser: {url}")
                if self.open_browser or self.instance is not None:
                    threading.Thread(
                        target=self._when_ready, args=(url if self.open_browser else None,), daemon=True
                    ).start()
                first = False
            if self._stopping:  # a stop asked while the next server was being built
                return
            self._server.run()
            if self._next is None or self._stopping:
                return
            self.workspace, self._next = self._next, None
            self.restarts += 1
            self.say(f"Opening the workspace at {self.workspace}")

    def _when_ready(self, url: str | None) -> None:
        """Once the first server answers: publish the instance, then open the browser."""
        started = False
        for _ in range(200):
            started = bool(getattr(self._server, "started", False))
            if started:
                break
            time.sleep(0.05)
        if started and self.instance is not None:
            self.instance.publish(self.host, self.port)
        if url is not None:
            webbrowser.open(url)


def _uvicorn_server(app: Any, host: str, port: int) -> Any:
    import uvicorn

    # With no console (pythonw, a windowed bundle) sys.stdout and sys.stderr are
    # None and uvicorn's own logging set-up raises (trial build fault 4); its
    # loggers then use whatever the process set up (the installed app's log file).
    no_console = sys.stdout is None or sys.stderr is None
    return uvicorn.Server(
        uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="warning",
            timeout_graceful_shutdown=RESTART_GRACE_SECONDS,
            **({"log_config": None} if no_console else {}),
        )
    )
