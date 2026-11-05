"""Screening drivers behind one interface (decision 2026-11-05).

`make_driver` builds the driver for a provider; the provider SDKs and HTTP
clients are created lazily, so importing this package costs nothing on the
base install.
"""

from __future__ import annotations

from typing import Any

from .base import PROVIDERS, Driver, DriverResult, RunSpec, ScreeningRequest, Usage

__all__ = ["PROVIDERS", "Driver", "DriverResult", "RunSpec", "ScreeningRequest", "Usage", "make_driver"]


def make_driver(provider: str, *, api_key: str | None, base_url: str | None = None, **options: Any) -> Driver:
    if provider == "anthropic":
        from .anthropic_driver import AnthropicDriver

        return AnthropicDriver(api_key, **options)
    if provider == "openai_compatible":
        from .openai_compatible import OpenAICompatibleDriver

        if not base_url:
            raise ValueError("the OpenAI-compatible driver needs a base URL")
        return OpenAICompatibleDriver(base_url, api_key, **options)
    if provider == "gemini":
        from .gemini import GeminiDriver

        if not api_key:
            raise ValueError("the Gemini driver needs an API key")
        return GeminiDriver(api_key, **options)
    raise ValueError(f"unknown provider {provider!r}; expected one of {PROVIDERS}")
