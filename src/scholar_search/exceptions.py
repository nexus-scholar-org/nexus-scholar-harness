"""Custom exceptions for scholar-search-kit."""


class ScholarSearchError(Exception):
    """Base exception for all scholar-search errors."""


class ProviderError(ScholarSearchError):
    """Raised when an external academic provider returns an error."""

    def __init__(self, provider: str, message: str, status_code: int | None = None):
        self.provider = provider
        self.status_code = status_code
        super().__init__(
            f"[{provider}] {message}"
            + (f" (HTTP {status_code})" if status_code else "")
        )


class RateLimitExceededError(ProviderError):
    """Raised when an API rate limit is exceeded."""

    def __init__(self, provider: str, message: str = "Rate limit exceeded"):
        super().__init__(provider=provider, message=message, status_code=429)


class ProviderPausedError(ProviderError):
    """A provider asked the client to wait longer than it ever waits (H-quota-hang).

    Raised instead of retrying when an HTTP 429 or 5xx answer carries a
    ``Retry-After`` beyond ``http_client.RETRY_AFTER_CAP``: retrying would only
    repeat the refusal. ``database`` is the provider's display name (from the
    request's host), ``retry_after`` the wait it asked for in seconds and
    ``resets_at`` the UTC time (ISO 8601) at which it said to come back.
    """

    def __init__(
        self,
        provider: str,
        message: str | None = None,
        *,
        status_code: int,
        database: str,
        retry_after: float,
        resets_at: str,
    ):
        self.database = database
        self.retry_after = retry_after
        self.resets_at = resets_at
        ProviderError.__init__(
            self,
            provider,
            message or f"{database} asks to wait {retry_after:.0f} s, until {resets_at}",
            status_code=status_code,
        )


class QuotaExhaustedError(ProviderPausedError, RateLimitExceededError):
    """HTTP 429 with a ``Retry-After`` beyond the cap: the provider's quota is used up until ``resets_at``.

    Still a ``RateLimitExceededError``, so a search leg records it as
    ``PROVIDER_RATE_LIMITED`` as before; the message names the reset time.
    """

    def __init__(self, provider: str, *, database: str, retry_after: float, resets_at: str):
        ProviderPausedError.__init__(
            self,
            provider,
            f"{database} quota used up; it resets at {resets_at} (Retry-After {retry_after:.0f} s)",
            status_code=429,
            database=database,
            retry_after=retry_after,
            resets_at=resets_at,
        )


class ProviderTimeoutError(ProviderError):
    """Raised when a provider request timed out (``PROVIDER_TIMEOUT`` on the leg)."""


class InvalidQueryError(ScholarSearchError):
    """Raised when a search query cannot be parsed or translated."""


class VerificationError(ScholarSearchError):
    """Raised when document verification or hydration fails."""
