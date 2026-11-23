"""One engine per user for the installed app (M13 Part A; spec §4.2 "A second click").

A second click on the icon must not start a second engine. The first engine
holds an exclusive lock on ``engine.lock`` in the settings folder for as long
as its process lives (the operating system drops the lock when the process
ends, also on a crash, so a stale lock cannot exist), and once its server
answers it writes ``engine.json`` beside it: its port and a secret made for
this launch. A second launcher that cannot take the lock reads that file and
asks the running engine, on loopback and with the secret, for a fresh
one-time launch link, opens the browser on it and exits.

Rules kept here:

* the instance routes answer only with the secret, and refuse any request
  that carries a browser's ``Origin`` or ``Sec-Fetch-Site`` header, so a web
  page can never reach them; they are not in the browser allowlist
  (``console/browser.py``) and the console token is not written to disk;
* the file is readable by this user only (the settings folder is per user;
  on POSIX the file is also ``0600``);
* the secret never reaches a log line or a command line.
"""

from __future__ import annotations

import hmac
import json
import os
import secrets
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import IO, Any

from fastapi import APIRouter, HTTPException, Request

LOCK_NAME = "engine.lock"
INFO_NAME = "engine.json"
PREFIX = "/instance"
SECRET_HEADER = "X-Nexus-Instance"
#: How long a second launcher waits for the running engine to answer (it may be restarting).
ANSWER_WAIT_SECONDS = 15.0


def _try_lock(handle: IO[bytes]) -> bool:
    try:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _unlock(handle: IO[bytes]) -> None:
    try:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass


class Instance:
    """This process's claim to be the user's one engine."""

    def __init__(self, folder: Path):
        self.folder = Path(folder)
        self.secret = secrets.token_urlsafe(32)
        self._handle: IO[bytes] | None = None

    @property
    def info_path(self) -> Path:
        return self.folder / INFO_NAME

    def acquire(self) -> bool:
        """``True`` when no other engine of this user is running (or starting)."""
        self.folder.mkdir(parents=True, exist_ok=True)
        handle = open(self.folder / LOCK_NAME, "a+b")  # noqa: SIM115 - held for the process's life
        if not _try_lock(handle):
            handle.close()
            return False
        self._handle = handle
        return True

    def publish(self, host: str, port: int) -> None:
        """Write ``engine.json`` once the server answers; replaced atomically."""
        payload = {"pid": os.getpid(), "host": host, "port": port, "secret": self.secret}
        temp = self.info_path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload), encoding="utf-8")
        if os.name != "nt":
            os.chmod(temp, 0o600)
        os.replace(temp, self.info_path)

    def release(self) -> None:
        """Remove the file when it is ours, then drop the lock."""
        if self._handle is None:
            return
        info = read_info(self.folder)
        if info is not None and hmac.compare_digest(str(info.get("secret", "")), self.secret):
            try:
                self.info_path.unlink()
            except OSError:
                pass
        _unlock(self._handle)
        self._handle.close()
        self._handle = None

    def router(self, *, launch_link: Callable[[], str], stop: Callable[[], None]) -> APIRouter:
        return router(self.secret, launch_link=launch_link, stop=stop)


def read_info(folder: Path) -> dict[str, Any] | None:
    try:
        info = json.loads((Path(folder) / INFO_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return info if isinstance(info, dict) and isinstance(info.get("port"), int) else None


def ask(folder: Path, action: str, *, wait: float = ANSWER_WAIT_SECONDS) -> dict[str, Any] | None:
    """Ask the running engine for ``launch-link`` or ``stop``; ``None`` when none answers in time."""
    deadline = time.monotonic() + wait
    while True:
        info = read_info(folder)
        if info is not None:
            request = urllib.request.Request(
                f"http://127.0.0.1:{info['port']}{PREFIX}/{action}",
                data=b"{}",
                headers={"Content-Type": "application/json", SECRET_HEADER: str(info.get("secret", ""))},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=3) as response:  # noqa: S310 - loopback only
                    return json.loads(response.read())
            except (urllib.error.URLError, OSError, ValueError):
                pass
        if time.monotonic() >= deadline:
            return None
        time.sleep(0.2)


def router(secret: str, *, launch_link: Callable[[], str], stop: Callable[[], None]) -> APIRouter:
    """The two routes a second launcher uses; never reachable from a browser page."""
    routes = APIRouter(prefix=PREFIX)

    def _check(request: Request) -> None:
        if request.headers.get("origin") is not None or request.headers.get("sec-fetch-site") is not None:
            raise HTTPException(403, {"code": "INSTANCE_BROWSER_REFUSED", "message": "this route is not served to a browser"})
        supplied = request.headers.get(SECRET_HEADER, "")
        if not hmac.compare_digest(supplied.encode(), secret.encode()):
            raise HTTPException(401, {"code": "INSTANCE_SECRET_REQUIRED", "message": "the instance secret is required"})

    @routes.post("/launch-link")
    def launch(request: Request) -> dict[str, str]:
        _check(request)
        return {"url": launch_link()}

    @routes.post("/stop")
    def stop_engine(request: Request) -> dict[str, bool]:
        _check(request)
        stop()
        return {"stopping": True}

    return routes
