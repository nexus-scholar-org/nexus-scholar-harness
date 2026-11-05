"""FastAPI application factory for the Harness Console server.

`scholar-harness serve --workspace <path>` runs this app over uvicorn
(loopback only by default). The app reads canonical workspace files and
dispatches mutations to kit CLIs via the job runner. All state is derived
from the workspace or the in-memory JobRunner — the API is stateless between
process restarts.

The console is API-only. The no-build SPA that used to be mounted at `/` and
`/static` was retired once the Research UI (`apps/research-ui`) became the
product surface; the browser reaches this API through that app's same-origin
proxy, never directly.
"""

from __future__ import annotations

import hmac
import re
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import browser

from .api import audit as audit_api
from .api import jobs as jobs_api
from .api import pipelines as pipelines_api
from .api import screening as screening_api
from .api import screening_v1 as screening_v1_api
from .api import streams as streams_api
from .api import workspace as workspace_api
from .api import workspaces as workspaces_api
from .runtimes.job_runner import JobRunner

#: Host names a loopback console answers to. ``serve`` passes exactly these.
LOOPBACK_HOSTS: tuple[str, ...] = ("127.0.0.1", "localhost", "::1")
#: Starlette's ``TestClient`` sends ``Host: testserver``; in-process callers of
#: ``create_app`` get it by default, ``serve`` never does.
_DEFAULT_HOSTS: tuple[str, ...] = (*LOOPBACK_HOSTS, "testserver")
# Same shape as the screening actions' own check (``_require_action_origin``).
_LOOPBACK_ORIGIN = re.compile(
    r"https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?", re.IGNORECASE
)
_OPEN_PATHS = frozenset({"/healthz"})

#: What a phone-scoped token may reach (contract §4 "Scope" column): screening
#: reads and decision events. Approval, publish, prepare, proposal runs, jobs,
#: pipelines and settings changes are desktop-only (`TOKEN_SCOPE_REFUSED`).
_PHONE_ROUTES: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (method, re.compile(pattern))
    for method, pattern in (
        ("GET", r"/api/v1/screening/(summary|queue|settings|prisma/preview|decisions/conflicts|actions/pairing/status)"),
        ("GET", r"/api/v1/screening/records/[A-Za-z0-9_-]+(/proposal)?"),
        ("POST", r"/api/v1/screening/decisions/events"),
        ("POST", r"/api/v1/screening/decisions/conflicts/[A-Za-z0-9_-]+/resolve"),
    )
)


def _phone_may_reach(method: str, path: str) -> bool:
    return any(m == method and p.fullmatch(path) for m, p in _PHONE_ROUTES)


def _refusal(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"detail": {"code": code, "message": message}}, status_code=status)


def _host_name(header: str) -> str:
    """``Host`` without its port; IPv6 brackets removed."""
    if header.startswith("["):
        return header[1:].split("]", 1)[0]
    return header.rsplit(":", 1)[0] if header.count(":") == 1 else header


def create_app(
    workspace: str | Path,
    *,
    token: str | None = None,
    trusted_hosts: Iterable[str] | None = None,
    phone_tokens: Iterable[str] | None = None,
    workspaces_root: str | Path | None = None,
    on_open: Callable[[Path], None] | None = None,
    browser_session: str | None = None,
    launch_codes: browser.LaunchCodes | None = None,
    ui_dir: str | Path | None = None,
) -> FastAPI:
    """Build the console app for one workspace.

    INC-01 guards run on every request: the ``Host`` must be a trusted loopback
    name (DNS rebinding), a browser ``Origin`` must be loopback, and when
    ``token`` is set every route except ``/healthz`` needs
    ``Authorization: Bearer <token>``. ``serve`` always passes a token and
    :data:`LOOPBACK_HOSTS`; ``token=None`` is for in-process tests only.

    ``workspaces_root`` is the folder the workspaces routes list (resolved
    like ``nexus-scholar ui`` resolves it when omitted); ``on_open`` is the
    launcher's restart hook, without which opening another workspace answers
    ``RESTART_UNSUPPORTED`` (workspaces API §4).

    The packaged app (``nexus-scholar ui``) also passes ``browser_session``,
    ``launch_codes`` and ``ui_dir``: the static UI is served from this process,
    and the browser reaches the API under ``/api/console`` with a session
    cookie and the proxy's allowlist (``console/browser.py``).
    """
    ws = Path(workspace).resolve()
    if not ws.is_dir():
        raise ValueError(f"workspace path does not exist: {ws}")

    app = FastAPI(
        title="scholar-harness console",
        version="0.1.0",
        description="Local observability and job-control surface for the Nexus Scholar harness.",
    )

    broadcast = jobs_api.JobStreamBroadcast()

    def on_job_event(event: dict[str, Any]) -> None:
        broadcast.put(event)

    runner = JobRunner(ws, on_event=on_job_event)

    app.state.workspace = ws
    app.state.job_runner = runner
    app.state.job_broadcast = broadcast
    from scholar_harness.workspace.catalog import resolve_root

    root, source = resolve_root(Path(workspaces_root) if workspaces_root is not None else None)
    app.state.workspaces_root = root
    app.state.workspaces_root_source = source
    app.state.on_open = on_open

    # Loopback-only CORS for GET from a loopback page (e.g. `next dev` on
    # :3000). CORS alone does not stop writes: a cross-origin "simple" POST
    # (text/plain) is sent without a preflight. The INC-01 guard below is what
    # refuses foreign origins, foreign hosts and calls without the token.
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    ui_root = Path(ui_dir).resolve() if ui_dir is not None else None
    if ui_root is not None and not (ui_root / "en").is_dir():
        raise ValueError(f"not a static UI export (no en/): {ui_root}")
    hosts = frozenset(trusted_hosts if trusted_hosts is not None else _DEFAULT_HOSTS)
    expected = f"Bearer {token}".encode() if token else None
    # Phone-scoped tokens (contract §4, §6). M2's `/lan/pair` adds to this set;
    # tests pass them in. A phone token reaches only `_PHONE_ROUTES`.
    app.state.phone_tokens = {t for t in (phone_tokens or ()) if t}

    # Registered after CORS, so it is the outer layer and runs first.
    @app.middleware("http")
    async def inc01_guard(request: Request, call_next):
        if _host_name(request.headers.get("host", "")) not in hosts:
            return _refusal(400, "HOST_REFUSED", "the console answers only on loopback")
        origin = request.headers.get("origin")
        if origin is not None and not _LOOPBACK_ORIGIN.fullmatch(origin.strip()):
            # The code the screening actions already use (contract §7).
            return _refusal(
                403, "ACTION_ORIGIN_REFUSED", "refusing a request from a non-loopback origin"
            )
        request.state.token_scope = "desktop"
        path = request.url.path
        if path.startswith(browser.BROWSER_PREFIX + "/") or path == browser.BROWSER_PREFIX:
            if browser_session is None:
                return _refusal(404, "CONSOLE_PATH_REFUSED", "the browser surface is served only by `nexus-scholar ui`")
            if not browser.has_session(request.cookies.get(browser.SESSION_COOKIE), browser_session):
                return _refusal(401, "TOKEN_REQUIRED", "open the app from `nexus-scholar ui` to start a session")
            try:
                inner = browser.check(
                    request.method, path, origin=origin, host=request.headers.get("host", ""),
                    fetch_site=request.headers.get("sec-fetch-site"),
                )
            except browser.BrowserRefused as exc:
                return _refusal(exc.status, exc.code, exc.message)
            # Served as the API route itself, with the desktop scope the proxy had.
            request.scope["path"] = inner
            request.scope["raw_path"] = inner.encode()
            return await call_next(request)
        if ui_root is not None and not path.startswith("/api/") and request.method in ("GET", "HEAD"):
            return await call_next(request)  # the static UI holds no workspace data
        if request.method != "OPTIONS" and path not in _OPEN_PATHS:
            supplied = request.headers.get("authorization", "").encode()
            phone = any(
                hmac.compare_digest(supplied, f"Bearer {t}".encode())
                for t in app.state.phone_tokens
            )
            if phone:
                request.state.token_scope = "phone"
                if not _phone_may_reach(request.method, request.url.path):
                    return _refusal(
                        403, "TOKEN_SCOPE_REFUSED", "this route is desktop-only"
                    )
            elif expected is not None and not hmac.compare_digest(supplied, expected):
                return _refusal(401, "TOKEN_REQUIRED", "a valid console token is required")
        return await call_next(request)

    app.include_router(workspace_api.router)
    app.include_router(workspaces_api.router)
    app.include_router(jobs_api.router)
    app.include_router(screening_api.router)
    app.include_router(screening_v1_api.router)
    app.include_router(pipelines_api.router)
    app.include_router(audit_api.router)
    app.include_router(streams_api.router)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "workspace": str(ws)}

    if launch_codes is not None and browser_session is not None:

        @app.get(browser.LAUNCH_PATH)
        def launch(code: str | None = None, next: str | None = None):  # noqa: A002 - the query name
            if not launch_codes.redeem(code):
                return _refusal(401, "LAUNCH_CODE_INVALID", "this launch link was used or has expired; start `nexus-scholar ui` again")
            response = RedirectResponse(browser.safe_next(next), status_code=303)
            response.set_cookie(browser.SESSION_COOKIE, browser_session, httponly=True, samesite="strict", path="/")
            return response

    if ui_root is not None:

        @app.get("/")
        def root_redirect() -> RedirectResponse:
            return RedirectResponse("/en/", status_code=307)

        not_found = ui_root / "404.html"
        app.mount("/", StaticFiles(directory=ui_root, html=True), name="ui")

        @app.exception_handler(404)
        async def ui_not_found(request: Request, exc):  # noqa: ANN001
            if not request.url.path.startswith("/api/") and not_found.is_file():
                return FileResponse(not_found, status_code=404)
            detail = getattr(exc, "detail", "Not Found")
            return JSONResponse({"detail": detail}, status_code=404)

    return app
