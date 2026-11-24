"""Provider API keys: the environment first, the OS keychain second (CORE-17, H-key-precedence).

A key is read from the provider's environment variable (the shell, or the
`.env` the process loaded), else from the OS keychain (`keyring`, extra `ai`)
under the service `nexus-scholar`. A variable that is set is the explicit,
per-run choice, so it beats the stored default; the MCP server already worked
this way (`_apply_keychain_keys`). Nothing here writes a key to a file, a
workspace, a config or the journal, and nothing returns a key except
`resolve_key`, which hands it to a driver in memory.

`key_status` says only where the key in use was found and whether the other
source also holds one, never a value. `refusal_note` says, after a provider
refused a key (401), which source it came from and how to replace it.
"""

from __future__ import annotations

import os
import re
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
    source: str  # the source in use: "environment" | "keychain" | "none"
    also_in_keychain: bool = False  # a keychain key exists too, and is not used (the environment wins)

    @property
    def present(self) -> bool:
        return self.source != "none"

    def describe(self) -> str:
        """One line for `keys status`: the source in use, the variable's name, the shadowed key; never a value."""
        if self.source == "environment":
            note = "; a keychain key also exists and is not used" if self.also_in_keychain else ""
            return f"environment ({ENV_VARS[self.provider]}{note})"
        return self.source


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


def _from_file(provider: str) -> str | None:
    """A key kept in the user's keys file, where the keychain failed (M13 Part B, after the user confirmed it)."""
    from scholar_search import user_settings

    value, where = user_settings.stored_key(provider)
    return value if where == "file" else None


def _from_environment(provider: str) -> str | None:
    return os.environ.get(ENV_VARS[provider], "").strip() or None


def keychain_available() -> bool:
    """Whether the keychain library is installed (extra `ai`); without it no keychain key can be read."""
    return _keyring() is not None


def resolve_key(provider: str) -> str | None:
    """The key to use: the environment variable if set, else the keychain entry, else the keys file, else None."""
    _check(provider)
    return _from_environment(provider) or _from_keychain(provider) or _from_file(provider)


def key_status(provider: str) -> KeyStatus:
    _check(provider)
    in_keychain = bool(_from_keychain(provider))
    if _from_environment(provider):
        return KeyStatus(provider, "environment", also_in_keychain=in_keychain)
    if in_keychain:
        return KeyStatus(provider, "keychain")
    return KeyStatus(provider, "file" if _from_file(provider) else "none")


_REFUSAL = re.compile(r"(?<!\d)401(?!\d)|AuthenticationError", re.IGNORECASE)


def is_refusal(error: object) -> bool:
    """True when a provider refused the key (HTTP 401).

    An exception counts by what it is (status 401, or the SDK's `AuthenticationError`), never by a "401" that
    happens to sit in its text (a URL, an id); a driver's per-record error string is text, so it is matched.
    """
    if isinstance(error, BaseException):
        return getattr(error, "status_code", None) == 401 or type(error).__name__ == "AuthenticationError"
    return bool(_REFUSAL.search(str(error)))


def refusal_note(provider: str) -> str:
    """After a 401: which source the refused key came from and how to replace it (no key value)."""
    status = key_status(provider)
    var = ENV_VARS[provider]
    if status.source == "environment":
        other = (
            f" A keychain key also exists and is not used; unset {var} to use it, or replace it with `nexus-scholar keys set {provider}`."
            if status.also_in_keychain
            else ""
        )
        return f"{provider} refused the key from the environment variable {var}. Put a valid key in {var} (the shell or the .env file).{other}"
    if status.source == "keychain":
        return (
            f"{provider} refused the key stored in the OS keychain. Replace it with `nexus-scholar keys set {provider}`, "
            f"or remove it with `nexus-scholar keys clear {provider}` and set {var} instead."
        )
    return f"{provider} refused the key it was given; no stored key or {var} is set now, so the key came from elsewhere in this process."


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
