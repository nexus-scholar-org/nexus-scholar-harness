"""Screening drivers behind one interface (decision 2026-11-05).

`make_driver` builds the driver for a provider; the provider SDKs and HTTP
clients are created lazily, so importing this package costs nothing on the
base install.
"""

from __future__ import annotations

from typing import Any

from .base import PROVIDERS, Driver, DriverResult, RunSpec, ScreeningRequest, Usage

__all__ = [
    "PROVIDERS",
    "Driver",
    "DriverResult",
    "ProviderSdkMissing",
    "RunSpec",
    "ScreeningRequest",
    "Usage",
    "ensure_sdk",
    "make_driver",
]


class ProviderSdkMissing(ImportError):
    """The provider's SDK is not installed; the message says what to install."""


def _install_hint() -> str:
    from importlib import metadata

    try:
        spec = f'"nexus-scholar[ai]>={metadata.version("nexus-scholar")}"'
    except metadata.PackageNotFoundError:
        spec = '"nexus-scholar[ai]"'
    return f"run `uv sync --extra ai` in a source checkout, or reinstall the package with its `ai` extra (`uv tool install --force {spec}`)"


def ensure_sdk(provider: str) -> None:
    """Raise `ProviderSdkMissing` (one sentence, no traceback needed) when the provider's SDK is absent.

    Only Anthropic uses an SDK (extra `ai`); the OpenAI-compatible and Gemini drivers use httpx.
    Commands call this before they print an estimate or a cost, so a missing extra is the first thing said.
    """
    if provider != "anthropic":
        return
    try:
        import anthropic  # noqa: F401  # extra `ai`
    except ImportError as exc:
        raise ProviderSdkMissing(f"The Anthropic SDK is not installed, so nothing can be sent to anthropic: {_install_hint()}.") from exc


def make_driver(provider: str, *, api_key: str | None, base_url: str | None = None, **options: Any) -> Driver:
    if provider == "anthropic":
        ensure_sdk(provider)
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
