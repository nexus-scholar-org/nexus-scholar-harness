"""The user's own Nexus Scholar settings: a settings file and the system keychain (M13 Part B).

Specification: ``docs/roadmap/milestones/M13-installers.md`` §4.3 and Q7;
the researcher's answers of 2026-11-24 in ``docs/roadmap/milestones/M13-part-b.md``.

* ``settings.json`` in the user's settings folder holds the contact e-mail,
  the reviews folder and whether first-run setup was done or put off. It is
  readable by this user only.
* Keys (OpenAlex, Semantic Scholar and the AI providers) go in the system
  keychain under the service ``nexus-scholar``, the name the app already uses
  for AI keys (``scholar_agent/keys.py``). Where the keychain fails, a file
  only this user can read is used instead, and only after the user confirmed
  it (answer 6): ``keys.json`` beside ``settings.json``.
* Precedence (answer 2): an environment variable first, then ``.env`` in the
  current folder (pydantic's own sources), then this store. A value set in
  the environment or ``.env`` is reported as set there and is not changed here.

Every package reads this module: the search settings (``config.py``), through
them the PDF look-up, and the MCP server. It holds no key in memory longer
than a call and never logs a value.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

#: Points the settings folder elsewhere (tests, CI, a portable copy).
SETTINGS_DIR_ENV = "NEXUS_SETTINGS_DIR"
#: The installed app's home override (``console/desktop.py``): its settings folder is ``<home>/settings``.
APP_HOME_ENV = "NEXUS_APP_HOME"
APP_NAME = "Nexus Scholar"
SETTINGS_FILE = "settings.json"
KEYS_FILE = "keys.json"
SCHEMA = "nexus.settings.v1"
SERVICE = "nexus-scholar"

#: The search keys and the field of the search settings each fills.
SEARCH_KEYS = {"openalex": "openalex_key", "semanticscholar": "s2_key"}
#: Every key the screen stores, with the environment variable that wins over it.
KEY_ENV = {
    "openalex": "SCHOLAR_OPENALEX_KEY",
    "semanticscholar": "SCHOLAR_S2_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai_compatible": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}
SETUP_STATES = ("done", "later")


class KeychainUnavailable(RuntimeError):
    """The system keychain cannot store a key here; the file needs the user's confirmation."""


def settings_dir(env: Mapping[str, str] | None = None, system: str | None = None) -> Path:
    """The user's settings folder (specification §4.1); the installed app and the engine share it."""
    env = os.environ if env is None else env
    system = system or sys.platform
    if env.get(SETTINGS_DIR_ENV):
        return Path(env[SETTINGS_DIR_ENV]).expanduser()
    if env.get(APP_HOME_ENV):
        return Path(env[APP_HOME_ENV]).expanduser() / "settings"
    user = Path(env.get("USERPROFILE") or env.get("HOME") or Path.home())
    if system == "win32":
        return Path(env.get("APPDATA") or user / "AppData" / "Roaming") / APP_NAME
    if system == "darwin":
        return user / "Library" / "Application Support" / APP_NAME
    return Path(env.get("XDG_CONFIG_HOME") or user / ".config") / "nexus-scholar"


def settings_path() -> Path:
    return settings_dir() / SETTINGS_FILE


def keys_path() -> Path:
    return settings_dir() / KEYS_FILE


# -- the settings file --------------------------------------------------------


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_private(path: Path, data: dict[str, Any]) -> None:
    """Replace ``path`` atomically with a file readable by this user only (0600 on POSIX)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        if os.name != "nt":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise


def read_settings() -> dict[str, Any]:
    """The settings file's values; ``{}`` when there is none (first run) or it cannot be read."""
    return _read_json(settings_path())


def exists() -> bool:
    return settings_path().is_file()


def write_settings(**changes: Any) -> dict[str, Any]:
    """Change some values; ``None`` removes one. Returns the new contents."""
    data = read_settings()
    data["schema"] = SCHEMA
    for name, value in changes.items():
        if value is None:
            data.pop(name, None)
        else:
            data[name] = value
    _write_private(settings_path(), data)
    return data


def setup_state() -> str:
    """``pending`` (no choice yet), ``done`` or ``later``."""
    value = read_settings().get("setup")
    return value if value in SETUP_STATES else "pending"


def contact_email() -> str | None:
    value = read_settings().get("contact_email")
    return value.strip() if isinstance(value, str) and value.strip() else None


def workspaces_root() -> Path | None:
    value = read_settings().get("workspaces_root")
    return Path(value) if isinstance(value, str) and value.strip() else None


# -- keys ---------------------------------------------------------------------


def keyring_module() -> Any | None:
    """The ``keyring`` library, imported on each call so a test's fake stands in for it; ``None`` without it."""
    try:
        import keyring  # extra `ai`
    except ImportError:
        return None
    return keyring


def keychain_usable() -> bool:
    """Whether a keychain backend exists here (not keyring's "fail" or "null" stand-in)."""
    kr = keyring_module()
    if kr is None:
        return False
    try:
        backend = kr.get_keyring()
    except Exception:  # noqa: BLE001 - no backend
        return False
    name = f"{type(backend).__module__}.{type(backend).__name__}".lower()
    return "fail" not in name and "null" not in name


def _check(name: str) -> None:
    if name not in KEY_ENV:
        raise ValueError(f"unknown key {name!r}; expected one of {tuple(KEY_ENV)}")


def _from_keychain(name: str) -> str | None:
    kr = keyring_module()
    if kr is None:
        return None
    try:
        value = kr.get_password(SERVICE, name)
    except Exception:  # noqa: BLE001 - a locked or absent keychain is "no key", never a crash
        return None
    return value.strip() if isinstance(value, str) and value.strip() else None


def _from_file(name: str) -> str | None:
    value = _read_json(keys_path()).get(name)
    return value.strip() if isinstance(value, str) and value.strip() else None


def stored_key(name: str) -> tuple[str | None, str | None]:
    """A key this store holds, and where: ``(value, "keychain" | "file")`` or ``(None, None)``.

    The environment and ``.env`` are not read here; callers that need the
    precedence read them first (the search settings do, through pydantic).
    """
    _check(name)
    value = _from_keychain(name)
    if value:
        return value, "keychain"
    value = _from_file(name)
    if value:
        return value, "file"
    return None, None


def store_key(name: str, value: str, *, use_file: bool = False) -> str:
    """Store a key; returns where (``keychain`` or ``file``).

    :class:`KeychainUnavailable` when the keychain cannot take it and the user
    has not confirmed the file yet (``use_file``).
    """
    _check(name)
    value = value.strip()
    if not value:
        raise ValueError("an empty key is not stored")
    if not use_file:
        kr = keyring_module()
        if kr is None or not keychain_usable():
            raise KeychainUnavailable(str(keys_path()))
        try:
            kr.set_password(SERVICE, name, value)
        except Exception as exc:  # noqa: BLE001 - a locked or broken keychain
            raise KeychainUnavailable(str(keys_path())) from exc
        _remove_from_file(name)  # one place per key
        return "keychain"
    # One place per key: an older keychain copy would be read first, so it goes before
    # the file is written; if it cannot be removed, nothing is written and the save is refused.
    kr = keyring_module()
    if kr is not None:
        try:
            if kr.get_password(SERVICE, name):
                kr.delete_password(SERVICE, name)
        except Exception:  # noqa: BLE001 - a keychain that cannot write may not delete either
            pass
    if _from_keychain(name):
        raise KeychainUnavailable(str(keys_path()))
    data = _read_json(keys_path())
    data[name] = value
    _write_private(keys_path(), data)
    return "file"


def _remove_from_file(name: str) -> bool:
    data = _read_json(keys_path())
    if name not in data:
        return False
    del data[name]
    _write_private(keys_path(), data)
    return True


def remove_key(name: str) -> bool:
    """Remove a key from the keychain and the file; ``True`` when one was there."""
    _check(name)
    removed = False
    kr = keyring_module()
    if kr is not None:
        try:
            if kr.get_password(SERVICE, name):
                kr.delete_password(SERVICE, name)
                removed = True
        except Exception:  # noqa: BLE001 - nothing stored, or no keychain
            pass
    return _remove_from_file(name) or removed


def search_values() -> dict[str, str]:
    """What this store gives the search settings (pydantic's lowest-precedence source)."""
    out: dict[str, str] = {}
    email = contact_email()
    if email:
        out["mailto"] = email
    for name, field in SEARCH_KEYS.items():
        value, _where = stored_key(name)
        if value:
            out[field] = value
    return out
