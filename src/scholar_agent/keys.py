"""Provider API keys: the OS keychain first, the environment second (CORE-17).

A key is read from the OS keychain (`keyring`, extra `ai`) under the service
`nexus-scholar`, else from the provider's environment variable, which is how
`.env` users already work (decision 2026-11-04, CORE-17). Nothing here writes
a key to a file, a workspace, a config or the journal, and nothing returns a
key except `resolve_key`, which hands it to a driver in memory.

`key_status` says only where a key was found, never its value.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

SERVICE = "nexus-scholar"
ENV_VARS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai_compatible": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


@dataclass(frozen=True)
class KeyStatus:
    provider: str
    source: str  # "keychain" | "environment" | "none"

    @property
    def present(self) -> bool:
        return self.source != "none"


def _keyring():
    try:
        import keyring  # extra `ai`
    except ImportError:
        return None
    return keyring


def _check(provider: str) -> None:
    if provider not in ENV_VARS:
        raise ValueError(f"unknown provider {provider!r}; expected one of {tuple(ENV_VARS)}")


def _from_keychain(provider: str) -> str | None:
    kr = _keyring()
    if kr is None:
        return None
    try:
        value = kr.get_password(SERVICE, provider)
    except Exception:  # noqa: BLE001 - a locked or absent keychain is "no key", never a crash
        return None
    return value or None


def resolve_key(provider: str) -> str | None:
    _check(provider)
    return _from_keychain(provider) or (os.environ.get(ENV_VARS[provider], "").strip() or None)


def key_status(provider: str) -> KeyStatus:
    _check(provider)
    if _from_keychain(provider):
        return KeyStatus(provider, "keychain")
    if os.environ.get(ENV_VARS[provider], "").strip():
        return KeyStatus(provider, "environment")
    return KeyStatus(provider, "none")


def store_key(provider: str, value: str) -> None:
    """Store a key in the OS keychain. Refuses when no keychain backend exists."""
    _check(provider)
    if not value.strip():
        raise ValueError("an empty key is not stored")
    kr = _keyring()
    if kr is None:
        raise RuntimeError("no keychain support: install the 'ai' extra (uv sync --extra ai)")
    kr.set_password(SERVICE, provider, value.strip())


def clear_key(provider: str) -> bool:
    _check(provider)
    kr = _keyring()
    if kr is None:
        return False
    try:
        kr.delete_password(SERVICE, provider)
    except Exception:  # noqa: BLE001 - nothing stored
        return False
    return True
