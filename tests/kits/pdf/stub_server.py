"""A PDF host on 127.0.0.1 for the Part K tests, counting every request.

The suite's socket guard allows loopback only, so these tests exercise the real
``aiohttp`` client (redirects, status codes, headers) without any request
leaving the machine. Each route answers from a script: a list of answers, one
per request, the last one repeated.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from aiohttp import web


@dataclass
class Answer:
    status: int = 200
    body: bytes = b""
    content_type: str = "application/pdf"
    headers: dict[str, str] = field(default_factory=dict)
    #: A path on this server to redirect to (302), instead of a body.
    redirect_to: str | None = None


class StubPdfHost:
    """``async with StubPdfHost({"/a.pdf": [Answer(...)]}) as host: host.url("/a.pdf")``."""

    def __init__(self, routes: dict[str, list[Answer]]):
        self.routes = routes
        self.hits: Counter[str] = Counter()
        self.agents: list[str] = []
        self._runner: web.AppRunner | None = None
        self.port = 0

    def url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    async def _serve(self, request: web.Request) -> web.StreamResponse:
        path = request.path
        self.hits[path] += 1
        self.agents.append(request.headers.get("User-Agent", ""))
        script = self.routes.get(path)
        if not script:
            return web.Response(status=404, text="not here")
        answer = script[min(self.hits[path], len(script)) - 1]
        if answer.redirect_to is not None:
            return web.Response(
                status=302, headers={"Location": self.url(answer.redirect_to), **answer.headers}
            )
        return web.Response(
            status=answer.status,
            body=answer.body,
            content_type=answer.content_type,
            headers=answer.headers,
        )

    async def __aenter__(self) -> StubPdfHost:
        app = web.Application()
        app.router.add_route("GET", "/{tail:.*}", self._serve)
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, "127.0.0.1", 0)
        await site.start()
        self.port = site._server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *exc) -> None:
        if self._runner is not None:
            await self._runner.cleanup()
