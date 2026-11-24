"""Settings and first-run setup (M13 Part B; ``docs/architecture/settings-api.md``).

The Settings screen reads and writes the user's own settings
(``scholar_search.user_settings``): the contact e-mail and the reviews folder
in the settings file, the keys in the system keychain (or, after the user
confirmed it, a file only they can read). Desktop only, same origin.

Rules kept here:

* a key's value is never in a response, a log line or a refusal; a response
  says only whether a key is set and where;
* the environment, then ``.env`` in the engine's folder, win over the screen
  (the researcher's answer 2, 2026-11-24): such a value is reported with its
  source and is not changed here (``SETTING_SET_ELSEWHERE``);
* a saved e-mail or key takes effect at the next request: the search settings
  are read again in place, with no restart; a new reviews folder restarts the
  server in place on it, as Open does on Workspaces.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from scholar_search import user_settings

from .. import refusals

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

KEY_NAMES = tuple(user_settings.KEY_ENV)
_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
_KEY = re.compile(r"[\x21-\x7e]{1,512}")  # printable ASCII, no spaces: every provider's key looks so


def _error(status: int, code: str, message: str, **details: Any) -> HTTPException:
    detail: dict[str, Any] = {"code": code, "message": message}
    if details:
        detail["details"] = details
    return HTTPException(status_code=status, detail=detail)


def _env_file() -> dict[str, str]:
    """``.env`` in the engine's current folder, as the search settings read it (names upper-cased)."""
    path = Path.cwd() / ".env"
    if not path.is_file():
        return {}
    try:
        from dotenv import dotenv_values

        values = dotenv_values(path)
    except Exception:  # noqa: BLE001 - an unreadable .env sets nothing
        return {}
    return {str(k).upper(): str(v) for k, v in values.items() if v is not None and str(v).strip()}


def _set_elsewhere(variable: str, *, env_file_applies: bool, env_file: dict[str, str]) -> str | None:
    """``environment`` or ``env_file`` when a value set there wins over the screen; else ``None``."""
    if os.environ.get(variable, "").strip():
        return "environment"
    if env_file_applies and env_file.get(variable.upper()):
        return "env_file"
    return None


def _reload_search_settings() -> None:
    from scholar_search.config import reload_settings

    reload_settings()


def snapshot(request: Request) -> dict[str, Any]:
    """What the screen shows; never a key's value."""
    env_file = _env_file()
    email_source = _set_elsewhere("SCHOLAR_MAILTO", env_file_applies=True, env_file=env_file)
    if email_source is not None:
        from scholar_search.config import settings

        email = settings.mailto
    else:
        email = user_settings.contact_email()
        email_source = "settings" if email else None
    keys: dict[str, dict[str, Any]] = {}
    for name, variable in user_settings.KEY_ENV.items():
        # The console reads `.env` for the search settings only; AI keys come from the environment or the store.
        source = _set_elsewhere(variable, env_file_applies=name in user_settings.SEARCH_KEYS, env_file=env_file)
        if source is None:
            _value, source = user_settings.stored_key(name)
        keys[name] = {"set": source is not None, "source": source, "variable": variable}
    usable = user_settings.keychain_usable()
    file = user_settings.keys_path()
    return {
        "shape": "settings-v1",
        "started_as": getattr(request.app.state, "started_as", None),
        "setup": user_settings.setup_state(),
        "settings_folder": str(user_settings.settings_dir()),
        "contact_email": {"value": email, "source": email_source},
        "keys": keys,
        "workspaces_root": {
            "path": str(request.app.state.workspaces_root),
            "source": request.app.state.workspaces_root_source,
        },
        "key_store": {"kind": "keychain" if usable else ("file" if file.is_file() else "none"), "file": str(file)},
    }


@router.get("")
def read_settings(request: Request) -> dict[str, Any]:
    return snapshot(request)


class EmailBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: str = Field(max_length=254)


@router.put("/contact-email")
def put_contact_email(body: EmailBody, request: Request) -> dict[str, Any]:
    where = _set_elsewhere("SCHOLAR_MAILTO", env_file_applies=True, env_file=_env_file())
    if where is not None:
        raise _error(409, refusals.SETTING_SET_ELSEWHERE, f"the contact e-mail is set in the {_words(where)}, which wins over Settings", source=where)
    value = body.value.strip()
    if value and not _EMAIL.fullmatch(value):
        raise _error(422, refusals.SETTING_INVALID, "this is not an e-mail address (nothing was sent to test it)", field="contact_email")
    user_settings.write_settings(contact_email=value or None)
    _reload_search_settings()
    return snapshot(request)


class KeyBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: str = Field(max_length=4096)
    use_file: bool = False


def _known(name: str) -> str:
    if name not in KEY_NAMES:
        raise _error(404, refusals.SETTING_INVALID, f"unknown key {name!r}", field="key")
    return name


@router.put("/keys/{name}")
def put_key(name: str, body: KeyBody, request: Request) -> dict[str, Any]:
    _known(name)
    variable = user_settings.KEY_ENV[name]
    where = _set_elsewhere(variable, env_file_applies=name in user_settings.SEARCH_KEYS, env_file=_env_file())
    if where is not None:
        raise _error(409, refusals.SETTING_SET_ELSEWHERE, f"this key is set in the {_words(where)} ({variable}), which wins over Settings", source=where)
    value = body.value.strip()
    if not _KEY.fullmatch(value):
        raise _error(422, refusals.SETTING_INVALID, "a key is one line of letters, digits and signs, with no spaces", field="key")
    try:
        user_settings.store_key(name, value, use_file=body.use_file)
    except user_settings.KeychainUnavailable as exc:
        raise _error(
            409,
            refusals.KEYCHAIN_UNAVAILABLE,
            "this computer has no keychain Nexus Scholar can use; the key can be kept in a file only you can read",
            file=str(exc),
        ) from None
    _reload_search_settings()
    return snapshot(request)


@router.post("/keys/{name}/remove")
def remove_key(name: str, request: Request) -> dict[str, Any]:
    _known(name)
    user_settings.remove_key(name)
    _reload_search_settings()
    return snapshot(request)


class SetupBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    choice: Literal["done", "later"]


@router.post("/setup")
def post_setup(body: SetupBody, request: Request) -> dict[str, Any]:
    user_settings.write_settings(setup=body.choice)
    return snapshot(request)


class ChooseBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


@router.post("/folder/choose")
def choose_folder(request: Request, background: BackgroundTasks, body: ChooseBody | None = None) -> JSONResponse:
    from scholar_harness.workspace import catalog

    from .. import folder_dialog

    source = request.app.state.workspaces_root_source
    if source in ("flag", "environment"):
        where = "--root option" if source == "flag" else "NEXUS_WORKSPACES_ROOT environment variable"
        raise _error(409, refusals.SETTING_SET_ELSEWHERE, f"the reviews folder is set by the {where}, which wins over Settings", source=source)
    on_root_change = getattr(request.app.state, "on_root_change", None)
    if on_root_change is None:
        raise _error(501, "RESTART_UNSUPPORTED", "this server was not started by `nexus-scholar ui`, so it cannot restart on another folder")
    current = request.app.state.workspace
    if current is not None:
        state = catalog.busy(Path(current))
        if state.get("run_active") or state.get("pairing_open"):
            raise _error(409, "WORKSPACE_BUSY", "an agent run or an approval is in progress; changing the folder would end it", **state)
    try:
        chosen = folder_dialog.choose(Path(request.app.state.workspaces_root))
    except folder_dialog.FolderDialogUnavailable:
        raise _error(409, refusals.FOLDER_DIALOG_UNAVAILABLE, "the folder dialog cannot open on this computer's desktop") from None
    if chosen is None:
        return JSONResponse({"chosen": None, "restarting": False})
    if current is not None:
        # Again after the dialog: a run or an approval may have started while it was open.
        state = catalog.busy(Path(current))
        if state.get("run_active") or state.get("pairing_open"):
            raise _error(409, "WORKSPACE_BUSY", "an agent run or an approval started while the folder window was open; nothing was changed", **state)
    chosen = chosen.expanduser().resolve()
    if not _writable(chosen):
        raise _error(409, "WORKSPACE_ROOT_UNAVAILABLE", f"Nexus Scholar cannot write to {chosen}", path=str(chosen))
    user_settings.write_settings(workspaces_root=str(chosen))
    background.add_task(on_root_change, chosen)
    return JSONResponse({"chosen": str(chosen), "restarting": True}, status_code=202)


def _writable(folder: Path) -> bool:
    try:
        folder.mkdir(parents=True, exist_ok=True)
        probe = folder / f".nexus-write-check-{os.getpid()}"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
    except OSError:
        return False
    return True


def _words(source: str) -> str:
    return {"environment": "environment", "env_file": ".env file"}.get(source, source)
