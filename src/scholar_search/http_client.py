"""HTTP client with caching, rate limiting, and retries for academic APIs."""

import asyncio
import importlib.metadata
import logging
import math
import re
import threading
import time
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlsplit

import hishel
import httpx

from .config import settings
from .exceptions import (
    ProviderError,
    ProviderPausedError,
    ProviderTimeoutError,
    QuotaExhaustedError,
    RateLimitExceededError,
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple token bucket rate limiter.

    Safe to share between clients, event loops and threads (M3h-b-resilience):
    the token arithmetic runs under a lock and nothing in it is bound to a loop.
    """

    def __init__(self, rate: float):
        self.rate = rate
        self.capacity = max(1.0, rate)
        self.tokens = self.capacity
        self.last_update = time.time()
        self._lock = threading.Lock()

    def set_rate(self, rate: float) -> None:
        """Change the rate; the burst follows it, and tokens never exceed the new burst."""
        with self._lock:
            self.rate = rate
            self.capacity = max(1.0, rate)
            self.tokens = min(self.tokens, self.capacity)

    def lower(self, rate: float) -> None:
        """Lower the rate (never raise it)."""
        if rate > 0 and (self.rate <= 0 or rate < self.rate):
            self.set_rate(rate)

    def _take(self) -> float:
        """Take a token and return 0, or return how long to sleep before trying again."""
        with self._lock:
            if self.rate <= 0:  # no limit (a client built with rate 0)
                return 0.0
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return 0.0
            return (1.0 - self.tokens) / self.rate

    async def wait(self) -> None:
        """Wait until a token is available."""
        if self.rate <= 0:
            return

        while True:
            sleep_time = self._take()
            if sleep_time <= 0:
                return
            await asyncio.sleep(max(0.01, sleep_time))


# --------------------------------------------------------------------------- client identity

PACKAGE = "nexus-scholar"


def package_version() -> str:
    """The installed ``nexus-scholar`` version, or ``0+unknown`` outside an install."""
    try:
        return importlib.metadata.version(PACKAGE)
    except importlib.metadata.PackageNotFoundError:
        return "0+unknown"


def user_agent() -> str:
    """``nexus-scholar/<version>``, plus ``(mailto:<address>)`` when a contact address is set.

    Crossref places a caller in its polite pool by the address in the
    User-Agent; arXiv and Crossref ask clients to name themselves accurately
    (F14: the agent said ``scholar-search-kit/0.1.0`` until M3h-b-resilience).
    """
    agent = f"{PACKAGE}/{package_version()}"
    if settings.mailto:
        agent += f" (mailto:{settings.mailto})"
    return agent


def client_identity() -> dict[str, str]:
    """What a run records about the client that sent its requests (never the contact address)."""
    version = package_version()
    return {"package": PACKAGE, "version": version, "user_agent": f"{PACKAGE}/{version}"}


# --------------------------------------------------------------------------- shared budgets

#: arXiv's terms of use: no more than one request every three seconds.
ARXIV_RATE = 1 / 3
#: Crossref without a contact address (public pool, since 2025-12-01): list
#: requests (query, filter) 1 per second, single-record requests 5.
CROSSREF_PUBLIC_RATE = 1.0
CROSSREF_PUBLIC_SINGLE_RATE = 5.0
#: A Crossref path that names one record (``/works/{doi}``); everything else is a list request.
_CROSSREF_SINGLE = re.compile(r"^/works/.+")


def crossref_rate(single: bool = False) -> float:
    """Crossref's rate: polite with a contact address, public without; list or single-record."""
    if single:
        rate = settings.rate_limit_crossref_single
        return rate if settings.mailto else min(rate, CROSSREF_PUBLIC_SINGLE_RATE)
    if settings.mailto:
        return settings.rate_limit_crossref
    return min(settings.rate_limit_crossref, CROSSREF_PUBLIC_RATE)


def _policy(url: str) -> tuple[str, float] | None:
    """``(budget key, rate)`` for a provider host with a process-wide limit, or None.

    A provider counts its limit per caller (Semantic Scholar: cumulative across
    all endpoints; Crossref: per contact address), so every client in the
    process that reaches the host shares one budget: the search leg, the
    abstract hydrator, the harvest's verification stage
    (``scholar_search.verifier.DocumentVerifier``, single-record lookups) and
    citation chasing. Crossref has two: list requests and single-record
    lookups have different limits. The post-screening ``scholar_verify`` kit
    has its own HTTP client and is not counted here.
    """
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if host == "api.semanticscholar.org":
        return host, settings.rate_limit_s2
    if host == "api.crossref.org":
        if _CROSSREF_SINGLE.match(parts.path or ""):
            return f"{host} single", crossref_rate(single=True)
        return f"{host} list", crossref_rate()
    if host == "export.arxiv.org":
        return host, ARXIV_RATE
    return None


_HOST_BUDGETS: dict[str, RateLimiter] = {}
#: The lowest rate a budget's provider has announced in its headers, per budget key.
_HEADER_CAPS: dict[str, float] = {}
_BUDGETS_LOCK = threading.Lock()


def host_budget(url: str) -> RateLimiter | None:
    """The shared budget for ``url``'s provider, created on first use; None for other hosts.

    Its rate is the configured one (read on every call, so a contact address
    set later is honoured), never above what the provider's headers said.
    """
    policy = _policy(url)
    if policy is None:
        return None
    key, rate = policy
    with _BUDGETS_LOCK:
        rate = min(rate, _HEADER_CAPS.get(key, rate))
        budget = _HOST_BUDGETS.get(key)
        if budget is None:
            budget = _HOST_BUDGETS[key] = RateLimiter(rate)
        elif budget.rate != rate:
            budget.set_rate(rate)
    return budget


#: The lowest rate a header can set (requests per second), unless the configured
#: rate is lower still: a one-off throttle header must not stall a long-running
#: console or MCP server until it restarts.
HEADER_FLOOR = 1.0


def _header_floor(configured: float) -> float:
    return min(configured, HEADER_FLOOR) if configured > 0 else HEADER_FLOOR


def _cap_from_headers(url: str, rate: float) -> bool:
    """Record a provider's announced rate for ``url``'s budget; False for a host without one."""
    policy = _policy(url)
    if policy is None:
        return False
    key = policy[0]
    rate = max(rate, _header_floor(policy[1]))
    with _BUDGETS_LOCK:
        _HEADER_CAPS[key] = min(rate, _HEADER_CAPS.get(key, rate))
    return True


def reset_host_budgets() -> None:
    """Forget every shared budget and announced rate (tests; a new process starts empty anyway)."""
    with _BUDGETS_LOCK:
        _HOST_BUDGETS.clear()
        _HEADER_CAPS.clear()


_INTERVAL = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(ms|s|m|h)?\s*$", re.IGNORECASE)
_UNIT_SECONDS = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0}


def header_rate(headers: httpx.Headers) -> float | None:
    """Requests per second from ``x-rate-limit-limit`` / ``x-rate-limit-interval``, or None.

    Crossref sends both (``3`` and ``1s`` in its polite pool on 2026-11-08);
    a missing, malformed or zero value gives None and changes nothing.
    """
    limit, interval = headers.get("x-rate-limit-limit"), headers.get("x-rate-limit-interval")
    if not limit or not interval:
        return None
    try:
        count = float(limit)
    except ValueError:
        return None
    match = _INTERVAL.match(interval)
    if not match or count <= 0:
        return None
    seconds = float(match.group(1)) * _UNIT_SECONDS[(match.group(2) or "s").lower()]
    if seconds <= 0:
        return None
    return count / seconds


# --------------------------------------------------------------------------- Retry-After

#: The longest ``Retry-After`` the client waits out (seconds). A longer one is
#: not a throttle but a closed door (a used-up daily quota, an announced
#: outage): the request ends at once with ``ProviderPausedError`` (H-quota-hang).
RETRY_AFTER_CAP = 60.0

#: The longest wait a reset time is computed from (one year): an absurd header
#: (``1e20``, ``inf``) must not overflow the date arithmetic (review F5).
RETRY_AFTER_MAX = 365 * 24 * 3600.0

#: Display names of the provider hosts, for the researcher's message.
_DATABASES = {
    "api.openalex.org": "OpenAlex",
    "api.crossref.org": "Crossref",
    "api.semanticscholar.org": "Semantic Scholar",
    "export.arxiv.org": "arXiv",
    "eutils.ncbi.nlm.nih.gov": "PubMed",
}


def database_name(url: str, fallback: str) -> str:
    """The display name of ``url``'s provider; ``fallback`` (the client's name) for another host."""
    host = (urlsplit(url).hostname or "").lower()
    return _DATABASES.get(host, fallback)


def retry_after_seconds(value: str | None, now: datetime | None = None) -> float | None:
    """Seconds from a ``Retry-After`` header (delta-seconds or an HTTP date); None when absent or unreadable."""
    if not value or not value.strip():
        return None
    text = value.strip()
    try:
        seconds = float(text)
    except ValueError:
        try:
            when = parsedate_to_datetime(text)
        except (TypeError, ValueError, IndexError, OverflowError):
            return None
        if when is None:
            return None
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
        seconds = (when - (now or datetime.now(UTC))).total_seconds()
    if math.isnan(seconds):
        return None
    # Clamped: a value beyond a year (or infinite) is read as a year.
    return min(max(0.0, seconds), RETRY_AFTER_MAX)


def _paused(name: str, url: str, status: int, wait: float) -> ProviderPausedError:
    """The typed error for an answer that asks to wait ``wait`` seconds, beyond the cap."""
    database = database_name(url, name)
    resets_at = (datetime.now(UTC) + timedelta(seconds=wait)).replace(microsecond=0).isoformat()
    if status == 429:
        return QuotaExhaustedError(name, database=database, retry_after=wait, resets_at=resets_at)
    return ProviderPausedError(
        name,
        f"{database} is unavailable (HTTP {status}); it asks to come back at {resets_at}",
        status_code=status,
        database=database,
        retry_after=wait,
        resets_at=resets_at,
    )


class AcademicHttpClient:
    """
    A robust HTTP client wrapped around hishel (httpx caching).
    Handles polite user agents, rate limiting, retries (429/503), timeouts, and caching.
    """

    DEFAULT_TIMEOUT: float = 30.0

    def __init__(
        self,
        name: str,
        rate_limit: float,
        cache_enabled: bool = True,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ):
        self.name = name
        self.rate_limiter = RateLimiter(rate_limit)
        self.cache_enabled = cache_enabled
        self.max_retries = max_retries
        self.base_delay = base_delay

        # Ensure cache directory exists
        settings.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = settings.cache_dir / "scholar_cache"

        transport = httpx.AsyncHTTPTransport(retries=4)
        agent = user_agent()

        if cache_enabled and settings.http_cache:
            self.client = hishel.AsyncCacheClient(
                transport=transport,
                headers={"User-Agent": agent},
            )
        else:
            self.client = httpx.AsyncClient(
                transport=transport,
                headers={"User-Agent": agent},
            )

    async def _wait(self, url: str) -> None:
        """This client's own limiter, then the host's shared budget when it has one."""
        await self.rate_limiter.wait()
        budget = host_budget(url)
        if budget is not None:
            await budget.wait()

    def _read_rate_headers(self, url: str, response: httpx.Response) -> None:
        """Lower the host's budget (or this client's limiter) to what the provider's headers allow."""
        rate = header_rate(response.headers)
        if rate is None:
            return
        budget = host_budget(url)
        current = (budget or self.rate_limiter).rate
        if current > 0 and rate >= current:
            return
        logger.info(
            f"[{self.name}] the provider allows {rate:g} requests per second "
            f"(x-rate-limit-type: {response.headers.get('x-rate-limit-type', 'not sent')})"
        )
        if _cap_from_headers(url, rate):
            host_budget(url)  # applies the new cap
        else:
            self.rate_limiter.lower(max(rate, _header_floor(current)))

    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> httpx.Response:
        """Execute a GET request with rate limiting, timeouts, error wrapping, and caching.

        HTTP 429 and 5xx answers are retried up to ``max_retries`` times with
        backoff (honouring ``Retry-After``), because a paginated leg makes many
        requests and one throttled page must not end it (M3a-discovery).

        H-quota-hang: an answer whose ``Retry-After`` exceeds ``RETRY_AFTER_CAP``
        is not retried: it raises ``QuotaExhaustedError`` (429) or
        ``ProviderPausedError`` (5xx) with the reset time. Before, a 14-hour
        ``Retry-After`` cost three sleeps of 60 s per request.
        """
        req_timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT

        for attempt in range(self.max_retries + 1):
            await self._wait(url)
            logger.debug(f"[{self.name}] GET {url}")
            try:
                response = await self.client.get(
                    url, params=params, timeout=req_timeout, headers=headers, **kwargs
                )
            except httpx.TimeoutException as e:
                raise ProviderTimeoutError(
                    self.name, f"Request timed out after {req_timeout}s: {e}"
                ) from e
            except httpx.RequestError as e:
                raise ProviderError(self.name, f"Network communication error: {e}") from e

            self._read_rate_headers(url, response)
            retryable = response.status_code == 429 or response.status_code >= 500
            if not retryable:
                break
            wait = retry_after_seconds(response.headers.get("retry-after"))
            if wait is not None and wait > RETRY_AFTER_CAP:
                raise _paused(self.name, url, response.status_code, wait)
            if attempt >= self.max_retries:
                break
            delay = wait if wait is not None else self.base_delay * (2**attempt)
            logger.warning(
                f"[{self.name}] HTTP {response.status_code} on attempt {attempt + 1}, retry after {delay}s"
            )
            await asyncio.sleep(min(delay, 60.0))

        # Check for cache hit in hishel
        if getattr(response.extensions, "from_cache", False):
            logger.debug(f"[{self.name}] Cache hit for {url}")

        if response.status_code == 429:
            raise RateLimitExceededError(
                self.name, "Rate limit exceeded on academic API"
            )
        elif response.status_code >= 400:
            raise ProviderError(
                self.name,
                f"HTTP request failed: {response.text[:200]}",
                status_code=response.status_code,
            )

        return response

    async def post(
        self,
        url: str,
        json: dict | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Execute a POST request with rate limiting, retries, and exponential backoff.

        Args:
            url: Target URL.
            json: JSON-serializable request body.
            params: Query parameters.
            headers: Extra headers merged with ``{"Accept": "application/json"}``.
            timeout: Per-request timeout in seconds (default: 30).

        Returns:
            Raw ``httpx.Response``; caller decides parsing.

        Raises:
            ProviderError: After all retries exhausted on network/HTTP errors.
            RateLimitExceededError: After all retries exhausted on HTTP 429.
        """
        req_timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        merged_headers = {"Accept": "application/json"}
        if headers:
            merged_headers.update(headers)

        last_exc: Exception | None = None

        for attempt in range(self.max_retries + 1):
            await self._wait(url)

            logger.debug(f"[{self.name}] POST {url} (attempt {attempt + 1})")
            try:
                response = await self.client.post(
                    url,
                    json=json,
                    params=params,
                    timeout=req_timeout,
                    headers=merged_headers,
                )
            except httpx.TimeoutException as exc:
                last_exc = exc
                logger.warning(
                    f"[{self.name}] Timeout on attempt {attempt + 1}: {exc}"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.base_delay * (2 ** attempt))
                    continue
                raise ProviderTimeoutError(
                    self.name, f"Request timed out after {req_timeout}s: {exc}"
                ) from exc
            except httpx.RequestError as exc:
                last_exc = exc
                logger.warning(
                    f"[{self.name}] Network error on attempt {attempt + 1}: {exc}"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.base_delay * (2 ** attempt))
                    continue
                raise ProviderError(
                    self.name, f"Network communication error: {exc}"
                ) from exc

            self._read_rate_headers(url, response)
            if response.status_code == 429 or response.status_code >= 500:
                # H-quota-hang: a wait beyond the cap ends the request (before,
                # this loop slept the whole Retry-After, without any cap).
                wait = retry_after_seconds(response.headers.get("retry-after"))
                if wait is not None and wait > RETRY_AFTER_CAP:
                    raise _paused(self.name, url, response.status_code, wait)
            # Handle HTTP error status codes
            if response.status_code == 429:
                delay = wait if wait is not None else self.base_delay * (2 ** attempt)
                logger.warning(
                    f"[{self.name}] 429 on attempt {attempt + 1}, retry after {delay}s"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(delay)
                    continue
                raise RateLimitExceededError(
                    self.name, "Rate limit exceeded on academic API"
                )
            elif response.status_code >= 400:
                # Only a server error is retried: a 4xx answer (a rejected key,
                # a bad request) says the same thing again (M3h-b-resilience;
                # before, a rejected Semantic Scholar key cost four requests).
                if response.status_code >= 500 and attempt < self.max_retries:
                    await asyncio.sleep(self.base_delay * (2 ** attempt))
                    continue
                raise ProviderError(
                    self.name,
                    f"HTTP request failed: {response.text[:200]}",
                    status_code=response.status_code,
                )

            return response

        # Unreachable but satisfies type checker
        raise ProviderError(self.name, "POST failed after all retries")

    async def close(self) -> None:
        """Close the underlying session."""
        await self.client.aclose()

