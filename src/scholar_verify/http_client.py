"""Shared HTTP fetching with retry/backoff for the verification kit."""

from __future__ import annotations

import time
from typing import Any

import requests

DEFAULT_USER_AGENT = "nexus-scholar-verify-kit/0.1 (systematic review verification)"
DEFAULT_RETRY_LIMIT = 3
DEFAULT_SLEEP_S = 0.2


class VerifyHttpClient:
    """Small sync HTTP client matching the retry semantics used by Phase 4 checks."""

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        retry_limit: int = DEFAULT_RETRY_LIMIT,
        sleep_s: float = DEFAULT_SLEEP_S,
        timeout: float = 30.0,
    ) -> None:
        self.headers = {"User-Agent": user_agent}
        self.retry_limit = retry_limit
        self.sleep_s = sleep_s
        self.timeout = timeout

    def fetch_json(self, url: str) -> dict[str, Any]:
        """GET url and return parsed JSON; structured error/status sentinel on failure.

        Mirrors the Phase 4 fetch_json contract so callers can distinguish a clean
        404 (`{"_status": 404}`) from a transport error (`{"_error": "..."}`).
        """
        for attempt in range(self.retry_limit):
            try:
                r = requests.get(url, headers=self.headers, timeout=self.timeout)
                if r.status_code in (404, 400, 422):
                    return {"_status": r.status_code}
                r.raise_for_status()
                return r.json()
            except requests.RequestException as exc:
                if attempt == self.retry_limit - 1:
                    return {"_error": f"{type(exc).__name__}: {exc}"}
                time.sleep(self.sleep_s * (attempt + 1))
        return {"_error": "unreachable"}
