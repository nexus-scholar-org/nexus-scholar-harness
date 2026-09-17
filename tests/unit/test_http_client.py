"""Tests for AcademicHttpClient.post() retry/backoff logic."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from scholar_search.exceptions import ProviderError, RateLimitExceededError
from scholar_search.http_client import AcademicHttpClient, RateLimiter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(status_code: int = 200, text: str = "", headers: dict | None = None) -> httpx.Response:
    """Build a minimal httpx.Response for testing."""
    return httpx.Response(
        status_code=status_code,
        text=text,
        headers=headers or {},
        request=httpx.Request("POST", "https://example.com"),
    )


@pytest.fixture
def client(tmp_path):
    """AcademicHttpClient with cache disabled and rate limiter patched."""
    with patch.object(RateLimiter, "wait", new_callable=AsyncMock):
        c = AcademicHttpClient(
            name="test",
            rate_limit=10.0,
            cache_enabled=False,
            max_retries=2,
            base_delay=0.01,
        )
    return c


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_post_success_200(client):
    """Successful POST returns 200 response."""
    ok_resp = _make_response(200, '{"ok":true}')
    client.client.post = AsyncMock(return_value=ok_resp)

    with patch.object(RateLimiter, "wait", new_callable=AsyncMock):
        result = await client.post("https://api.example.com", json={"q": "test"})

    assert result.status_code == 200
    assert result.json() == {"ok": True}


@pytest.mark.asyncio
async def test_post_429_retries_then_succeeds(client):
    """429 triggers retry then succeeds."""
    rate_resp = _make_response(429, "rate limited", {"retry-after": "0"})
    ok_resp = _make_response(200, '{"ok":true}')
    client.client.post = AsyncMock(side_effect=[rate_resp, ok_resp])

    with patch.object(RateLimiter, "wait", new_callable=AsyncMock):
        result = await client.post("https://api.example.com")

    assert result.status_code == 200
    assert client.client.post.call_count == 2


@pytest.mark.asyncio
async def test_post_429_exhausts_retries(client):
    """429 exhausts retries then raises RateLimitExceededError."""
    rate_resp = _make_response(429, "rate limited")
    client.client.post = AsyncMock(return_value=rate_resp)

    with patch.object(RateLimiter, "wait", new_callable=AsyncMock):
        with pytest.raises(RateLimitExceededError):
            await client.post("https://api.example.com")

    # max_retries=2 means 3 total attempts (0, 1, 2)
    assert client.client.post.call_count == 3


@pytest.mark.asyncio
async def test_post_5xx_exhausts_retries(client):
    """5xx exhausts retries then raises ProviderError."""
    err_resp = _make_response(503, "service unavailable")
    client.client.post = AsyncMock(return_value=err_resp)

    with patch.object(RateLimiter, "wait", new_callable=AsyncMock):
        with pytest.raises(ProviderError) as exc_info:
            await client.post("https://api.example.com")

    assert "503" in str(exc_info.value) or "HTTP request failed" in str(exc_info.value)
    assert client.client.post.call_count == 3


@pytest.mark.asyncio
async def test_post_request_error_triggers_backoff(client):
    """httpx.RequestError triggers exponential backoff then ProviderError."""
    client.client.post = AsyncMock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    with patch.object(RateLimiter, "wait", new_callable=AsyncMock):
        with pytest.raises(ProviderError) as exc_info:
            await client.post("https://api.example.com")

    assert "Network communication error" in str(exc_info.value)
    assert client.client.post.call_count == 3


@pytest.mark.asyncio
async def test_post_timeout_triggers_backoff(client):
    """httpx.TimeoutException triggers exponential backoff then ProviderError."""
    client.client.post = AsyncMock(
        side_effect=httpx.TimeoutException("timed out")
    )

    with patch.object(RateLimiter, "wait", new_callable=AsyncMock):
        with pytest.raises(ProviderError) as exc_info:
            await client.post("https://api.example.com", timeout=5.0)

    assert "timed out" in str(exc_info.value)
    assert client.client.post.call_count == 3


@pytest.mark.asyncio
async def test_post_merges_headers(client):
    """Caller-supplied headers merge with default Accept header."""
    ok_resp = _make_response(200)
    client.client.post = AsyncMock(return_value=ok_resp)

    with patch.object(RateLimiter, "wait", new_callable=AsyncMock):
        await client.post(
            "https://api.example.com",
            headers={"X-Custom": "value"},
        )

    call_kwargs = client.client.post.call_args
    sent_headers = call_kwargs.kwargs.get("headers", call_kwargs[1].get("headers", {}))
    assert sent_headers["Accept"] == "application/json"
    assert sent_headers["X-Custom"] == "value"


@pytest.mark.asyncio
async def test_post_retry_after_header_respected(client):
    """429 with retry-after header uses that delay."""
    rate_resp = _make_response(429, "", {"retry-after": "0"})
    ok_resp = _make_response(200, '{"ok":true}')
    client.client.post = AsyncMock(side_effect=[rate_resp, ok_resp])

    with patch.object(RateLimiter, "wait", new_callable=AsyncMock):
        with patch("scholar_search.http_client.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await client.post("https://api.example.com")

    assert result.status_code == 200
    # Should have slept with the retry-after value
    mock_sleep.assert_called_once()
    sleep_val = mock_sleep.call_args[0][0]
    assert sleep_val == 0.0  # retry-after: "0"
