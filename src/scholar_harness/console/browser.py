"""The packaged UI's access to the console (M5-slim; decision 2026-11-05).

In development the Research UI reaches the console through its Next.js proxy
(`apps/research-ui/app/api/console/[...path]/route.ts`), which holds the token
and lets the browser reach only the reads and an allowlist of writes. The
packaged app serves a static export from this process instead, so this module
does that job here, with the same rules:

- **The same paths.** The UI calls `/api/console/api/v1/...`; requests there are
  checked, then served as `/api/v1/...`. `/api/v1/...` itself still needs the
  bearer token (scripts, tests, the CLI).
- **A session cookie, not a token in the page.** The launcher opens
  `/launch?code=<one-time code>`; a valid code (single use, 2 minutes) sets an
  HttpOnly, SameSite=Strict cookie and redirects into the app. The bearer token
  never reaches the browser or a URL. The session secret belongs to the launch,
  so it survives a restart onto another workspace.
- **The same allowlist.** GET/HEAD on any `/api/v1/...` path of plain segments;
  POST and PUT only on `POST_PATHS` and `PUT_PATHS` (kept equal to the proxy's by
  `tests/console/test_browser_access.py`), each only from this origin; the draft
  read only from this app's own pages (it records a reveal).
"""

from __future__ import annotations

import hmac
import re
import secrets
import threading
import time
from urllib.parse import urlsplit

BROWSER_PREFIX = "/api/console"
SESSION_COOKIE = "nexus_session"
LAUNCH_PATH = "/launch"
LAUNCH_CODE_SECONDS = 120.0

_SEGMENT = re.compile(r"[A-Za-z0-9_-]+")

#: POST targets the browser may reach; the proxy's list plus the workspaces routes.
POST_PATHS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p)
    for p in (
        r"api/v1/screening/batch/\d+/decisions",
        r"api/v1/screening/actions/(pairing/(begin|redeem)|defer|publish)",
        r"api/v1/screening/decisions/events",
        r"api/v1/screening/decisions/conflicts/[A-Za-z0-9_-]+/resolve",
        r"api/v1/screening/prepare",
        r"api/v1/screening/proposals/(runs|calibrations)",
        r"api/v1/screening/proposals/runs/[A-Za-z0-9_-]+/cancel",
    )
)
#: Packaged-app only (the dev proxy has no workspace switching).
PACKAGED_POST_PATHS: tuple[re.Pattern[str], ...] = (re.compile(r"api/v1/workspaces(/open)?"),)
PUT_PATHS: tuple[re.Pattern[str], ...] = (re.compile(r"api/v1/screening/settings"),)
#: The one GET with an effect: reading a draft records a reveal.
READ_PROPOSAL = re.compile(r"api/v1/screening/records/[A-Za-z0-9_-]+/proposal")


class BrowserRefused(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


class LaunchCodes:
    """One-time launch codes for one session secret; thread-safe."""

    def __init__(self, session: str):
        self.session = session
        self._codes: dict[str, float] = {}
        self._lock = threading.Lock()

    def issue(self) -> str:
        code = secrets.token_urlsafe(24)
        with self._lock:
            self._codes[code] = time.monotonic() + LAUNCH_CODE_SECONDS
        return code

    def redeem(self, code: str | None) -> bool:
        if not code:
            return False
        with self._lock:
            expires = self._codes.pop(code, None)
        return expires is not None and time.monotonic() <= expires


def has_session(cookie: str | None, session: str) -> bool:
    return bool(cookie) and hmac.compare_digest(cookie.encode(), session.encode())


def same_origin(origin: str | None, host: str) -> bool:
    if not origin:
        return False
    parts = urlsplit(origin.strip())
    return parts.scheme in ("http", "https") and parts.netloc.lower() == host.lower()


def check(method: str, path: str, *, origin: str | None, host: str, fetch_site: str | None) -> str:
    """The `/api/v1/...` path to serve, or `BrowserRefused` with the proxy's codes."""
    inner = path[len(BROWSER_PREFIX) + 1 :] if path.startswith(BROWSER_PREFIX + "/") else ""
    segments = inner.split("/")
    if len(segments) < 2 or segments[:2] != ["api", "v1"] or not all(_SEGMENT.fullmatch(s) for s in segments):
        raise BrowserRefused(400, "CONSOLE_PATH_REFUSED", "only /api/v1/... paths are served to the browser")
    method = method.upper()
    writes = method in ("POST", "PUT")
    if writes and not same_origin(origin, host):
        raise BrowserRefused(403, "CONSOLE_ORIGIN_REFUSED", f"{method} is accepted only from this app's own origin")
    if method not in ("GET", "HEAD") and not writes:
        raise BrowserRefused(405, "CONSOLE_METHOD_REFUSED", "the browser may use GET, HEAD, POST and PUT")
    if method == "PUT" and not any(p.fullmatch(inner) for p in PUT_PATHS):
        raise BrowserRefused(405, "CONSOLE_METHOD_REFUSED", "PUT is served only for the screening settings")
    if method == "POST" and not any(p.fullmatch(inner) for p in POST_PATHS + PACKAGED_POST_PATHS):
        raise BrowserRefused(405, "CONSOLE_METHOD_REFUSED", "POST is served only for the screening actions and the workspaces")
    if READ_PROPOSAL.fullmatch(inner) and fetch_site not in (None, "same-origin", "none"):
        raise BrowserRefused(403, "CONSOLE_ORIGIN_REFUSED", "the agent's draft is read only from this app's own pages")
    return "/" + inner


def safe_next(target: str | None, default: str = "/en/") -> str:
    """A same-app path to land on after launch; anything else falls back."""
    if not target or not target.startswith("/") or target.startswith("//") or "\\" in target:
        return default
    parts = urlsplit(target)
    return default if parts.scheme or parts.netloc else target
