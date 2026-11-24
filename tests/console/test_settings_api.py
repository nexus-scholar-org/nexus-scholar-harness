"""M13 Part B: settings and first-run setup (`docs/architecture/settings-api.md`).

Definition of done (specification §5.2 Part B), each by a test here:
- a search refused for a missing e-mail succeeds after the e-mail is saved on
  the screen, with no restart by the user;
- a key saved on the screen is never returned by any route;
- an environment variable (and `.env`, the researcher's answer 2) still wins.

Every test has its own settings folder and an empty in-memory keychain
(`tests/conftest.py`); made-up values only.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scholar_harness.console import browser, create_app, folder_dialog, launcher
from scholar_harness.workspace import catalog
from scholar_search import user_settings
from scholar_search.config import reload_settings, settings

TOKEN = "desktop-token"
FAKE_KEYS = {
    "openalex": "oa-MADE-UP-0001",
    "semanticscholar": "s2-MADE-UP-0002",
    "anthropic": "sk-ant-MADE-UP-0003",
    "openai_compatible": "sk-MADE-UP-0004",
    "gemini": "AIzaMADEUP0005xyz",
}
ALL_ENV = ("SCHOLAR_MAILTO", "SCHOLAR_OPENALEX_KEY", "SCHOLAR_S2_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", catalog.ROOT_ENV)


@pytest.fixture(autouse=True)
def clean(monkeypatch, tmp_path):
    for name in ALL_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)  # no `.env` unless a test writes one
    reload_settings()
    yield
    reload_settings()


def _client(ws: Path | None = None, *, root: Path, source: str = "default", **kwargs) -> TestClient:
    """The app as the launcher builds it: the folder it resolved, and where it came from."""
    app = create_app(ws, token=TOKEN, workspaces_root=root, workspaces_root_source=source, **kwargs)
    return TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"})


def test_the_screen_reads_nothing_set_on_a_first_run(tmp_path):
    body = _client(root=tmp_path / "reviews").get("/api/v1/settings").json()
    assert body["shape"] == "settings-v1" and body["setup"] == "pending"
    assert body["contact_email"] == {"value": None, "source": None}
    assert set(body["keys"]) == set(FAKE_KEYS)
    assert all(k["set"] is False and k["source"] is None for k in body["keys"].values())
    assert body["workspaces_root"]["source"] == "default"
    assert _client(root=tmp_path, source="flag").get("/api/v1/settings").json()["workspaces_root"]["source"] == "flag"
    assert body["key_store"]["kind"] == "keychain"


def test_a_search_refused_for_a_missing_email_goes_on_after_it_is_saved_with_no_restart(tmp_path, monkeypatch):
    """DoD 1. The run route checks the e-mail, then the OpenAlex key, then the accepted corpus, before any request."""
    from scholar_harness import corpus_accept

    monkeypatch.setattr(corpus_accept, "_accepted_snapshot", lambda ws: True)  # stops the run before any request
    catalog.create(tmp_path / "reviews", "Search Review")
    client = _client(tmp_path / "reviews" / "search-review", root=tmp_path / "reviews")
    run = {"providers": ["crossref"]}
    first = client.post("/api/v1/discovery/runs", json=run)
    assert first.status_code == 409 and first.json()["detail"]["code"] == "MAILTO_NOT_SET"

    saved = client.put("/api/v1/settings/contact-email", json={"value": "reviewer@example.org"})
    assert saved.status_code == 200 and saved.json()["contact_email"] == {"value": "reviewer@example.org", "source": "settings"}

    again = client.post("/api/v1/discovery/runs", json=run)  # same app, same process: no restart
    assert again.json()["detail"]["code"] == "CORPUS_ALREADY_ACCEPTED"
    assert settings.mailto == "reviewer@example.org"
    assert json.loads(user_settings.settings_path().read_text(encoding="utf-8"))["contact_email"] == "reviewer@example.org"


def test_a_saved_key_is_never_returned_by_any_route(tmp_path):
    """DoD 2: every settings answer and refusal, after every key is saved, holds no key's value."""
    client = _client(root=tmp_path / "reviews")
    answers = [client.put(f"/api/v1/settings/keys/{name}", json={"value": value}) for name, value in FAKE_KEYS.items()]
    answers.append(client.get("/api/v1/settings"))
    answers.append(client.put("/api/v1/settings/keys/openalex", json={"value": "has space"}))  # a refusal
    answers.append(client.put("/api/v1/settings/contact-email", json={"value": "not-an-email"}))
    answers.append(client.post("/api/v1/settings/setup", json={"choice": "done"}))
    for answer in answers:
        for value in FAKE_KEYS.values():
            assert value not in answer.text, answer.request.url
    body = client.get("/api/v1/settings").json()
    assert all(k == {"set": True, "source": "keychain", "variable": user_settings.KEY_ENV[n]} for n, k in body["keys"].items())
    # The engine uses them: the search settings and the AI key store read the keychain.
    assert settings.openalex_key == FAKE_KEYS["openalex"] and settings.s2_key == FAKE_KEYS["semanticscholar"]
    from scholar_agent import keys

    assert keys.resolve_key("anthropic") == FAKE_KEYS["anthropic"]
    # Remove takes it away again.
    removed = client.post("/api/v1/settings/keys/openalex/remove").json()
    assert removed["keys"]["openalex"] == {"set": False, "source": None, "variable": "SCHOLAR_OPENALEX_KEY"}
    assert settings.openalex_key is None


def test_the_environment_and_dotenv_still_win(tmp_path, monkeypatch):
    """DoD 3, and the researcher's answer 2: environment, then `.env`, then the screen."""
    client = _client(root=tmp_path / "reviews")
    assert client.put("/api/v1/settings/contact-email", json={"value": "screen@example.org"}).status_code == 200

    (tmp_path / ".env").write_text("SCHOLAR_MAILTO=dotenv@example.org\nSCHOLAR_OPENALEX_KEY=oa-DOTENV-MADE-UP\n", encoding="utf-8")
    reload_settings()
    body = client.get("/api/v1/settings").json()
    assert body["contact_email"] == {"value": "dotenv@example.org", "source": "env_file"}
    assert body["keys"]["openalex"]["source"] == "env_file" and "oa-DOTENV-MADE-UP" not in json.dumps(body)
    assert settings.mailto == "dotenv@example.org"
    refused = client.put("/api/v1/settings/contact-email", json={"value": "other@example.org"})
    assert refused.status_code == 409 and refused.json()["detail"]["code"] == "SETTING_SET_ELSEWHERE"
    assert refused.json()["detail"]["details"]["source"] == "env_file"
    assert client.put("/api/v1/settings/keys/openalex", json={"value": "oa-X"}).json()["detail"]["code"] == "SETTING_SET_ELSEWHERE"

    monkeypatch.setenv("SCHOLAR_MAILTO", "env@example.org")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-ENV-MADE-UP")
    reload_settings()
    body = client.get("/api/v1/settings").json()
    assert body["contact_email"] == {"value": "env@example.org", "source": "environment"}
    assert body["keys"]["anthropic"]["source"] == "environment" and "sk-ant-ENV-MADE-UP" not in json.dumps(body)
    assert settings.mailto == "env@example.org"
    # The screen's own value is kept, unused, for when the environment no longer sets one.
    assert user_settings.contact_email() == "screen@example.org"


def test_an_ai_key_in_dotenv_is_not_reported_as_set(tmp_path):
    """The engine reads `.env` for the search settings only; an AI key there is not one the engine uses."""
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=sk-ant-DOTENV\n", encoding="utf-8")
    body = _client(root=tmp_path / "reviews").get("/api/v1/settings").json()
    assert body["keys"]["anthropic"] == {"set": False, "source": None, "variable": "ANTHROPIC_API_KEY"}


def test_bad_values_are_refused_and_nothing_is_sent(tmp_path):
    client = _client(root=tmp_path / "reviews")
    for value in ("no-at-sign", "a@b", "two words@example.org"):
        answer = client.put("/api/v1/settings/contact-email", json={"value": value})
        assert answer.status_code == 422 and answer.json()["detail"]["code"] == "SETTING_INVALID"
    for value in ("", "   ", "has space", "line\nbreak", "x" * 513):
        answer = client.put("/api/v1/settings/keys/gemini", json={"value": value})
        assert answer.status_code == 422 and answer.json()["detail"]["code"] == "SETTING_INVALID", value
    assert client.put("/api/v1/settings/keys/unknown", json={"value": "x"}).status_code == 404
    assert client.put("/api/v1/settings/contact-email", json={"value": ""}).json()["contact_email"]["value"] is None


class _FailKeyring:
    """keyring's own stand-in on a computer with no keychain backend."""

    __module__ = "keyring.backends.fail"

    def get_password(self, *a):
        return None

    def set_password(self, *a):
        raise RuntimeError("No recommended backend was available")

    def delete_password(self, *a):
        raise RuntimeError("No recommended backend was available")


def test_no_keychain_asks_first_then_keeps_the_key_in_a_private_file(tmp_path, monkeypatch):
    """The researcher's answer 6: wherever the keychain fails, a file only this user can read, after a yes."""
    import sys
    import types

    fail = _FailKeyring()
    module = types.ModuleType("keyring")
    module.get_keyring = lambda: fail
    module.get_password, module.set_password, module.delete_password = fail.get_password, fail.set_password, fail.delete_password
    monkeypatch.setitem(sys.modules, "keyring", module)
    client = _client(root=tmp_path / "reviews")
    assert client.get("/api/v1/settings").json()["key_store"]["kind"] == "none"

    asked = client.put("/api/v1/settings/keys/anthropic", json={"value": FAKE_KEYS["anthropic"]})
    assert asked.status_code == 409 and asked.json()["detail"]["code"] == "KEYCHAIN_UNAVAILABLE"
    assert asked.json()["detail"]["details"]["file"] == str(user_settings.keys_path())
    assert not user_settings.keys_path().exists()  # nothing written before the yes

    kept = client.put("/api/v1/settings/keys/anthropic", json={"value": FAKE_KEYS["anthropic"], "use_file": True})
    assert kept.status_code == 200 and FAKE_KEYS["anthropic"] not in kept.text
    assert kept.json()["keys"]["anthropic"]["source"] == "file" and kept.json()["key_store"]["kind"] == "file"
    if os.name != "nt":
        assert (user_settings.keys_path().stat().st_mode & 0o777) == 0o600
    from scholar_agent import keys

    assert keys.resolve_key("anthropic") == FAKE_KEYS["anthropic"] and keys.key_status("anthropic").source == "file"
    client.post("/api/v1/settings/keys/anthropic/remove")
    assert keys.resolve_key("anthropic") is None


def test_setup_and_later_are_remembered_and_the_installed_first_run_opens_setup(tmp_path):
    """Answers 3 and 4: only the installed start opens setup, and only while no choice is saved."""
    ui = tmp_path / "ui"
    (ui / "en").mkdir(parents=True)
    (ui / "en" / "index.html").write_text("<html></html>", encoding="utf-8")
    quiet = {"root": tmp_path / "reviews", "workspace": None, "ui_dir": ui, "open_browser": False, "say": lambda _m: None}
    installed = launcher.Launcher(**quiet, started_as="installed")
    assert installed.landing() == "/en/settings/?setup=1"
    assert launcher.Launcher(**quiet).landing() == "/en/workspaces/"  # a terminal start lands as before
    client = _client(root=tmp_path / "reviews")
    assert client.post("/api/v1/settings/setup", json={"choice": "later"}).json()["setup"] == "later"
    assert installed.landing() == "/en/workspaces/"
    assert client.post("/api/v1/settings/setup", json={"choice": "never"}).status_code == 422


def test_the_routes_answer_with_no_review_open_and_only_to_the_desktop(tmp_path):
    client = _client(root=tmp_path / "reviews")
    assert client.get("/api/v1/settings").status_code == 200  # first run has no review
    phone = TestClient(create_app(None, token=TOKEN, phone_tokens={"phone"}, workspaces_root=tmp_path),
                       base_url="http://127.0.0.1", headers={"Authorization": "Bearer phone"})
    assert phone.get("/api/v1/settings").json()["detail"]["code"] == "TOKEN_SCOPE_REFUSED"


def test_the_browser_reaches_the_settings_writes_through_its_allowlist(tmp_path):
    session = "s"
    app = create_app(None, token=TOKEN, workspaces_root=tmp_path, browser_session=session,
                     launch_codes=browser.LaunchCodes(session))
    client = TestClient(app, base_url="http://127.0.0.1:8770")
    client.cookies.set(browser.SESSION_COOKIE, session)
    origin = {"Origin": "http://127.0.0.1:8770"}
    base = "/api/console/api/v1/settings"
    assert client.put(f"{base}/contact-email", json={"value": "r@example.org"}, headers=origin).status_code == 200
    assert client.put(f"{base}/keys/gemini", json={"value": "AIzaMADEUP"}, headers=origin).status_code == 200
    assert client.post(f"{base}/keys/gemini/remove", headers=origin).status_code == 200
    assert client.post(f"{base}/setup", json={"choice": "done"}, headers=origin).status_code == 200
    assert client.put(f"{base}/keys/other", json={"value": "x"}, headers=origin).json()["detail"]["code"] == "CONSOLE_METHOD_REFUSED"
    foreign = client.put(f"{base}/contact-email", json={"value": "r@example.org"}, headers={"Origin": "http://127.0.0.1:9999"})
    assert foreign.status_code == 403


def test_a_chosen_folder_is_saved_and_the_server_restarts_on_it(tmp_path, monkeypatch):
    chosen = tmp_path / "elsewhere"
    monkeypatch.setattr(folder_dialog, "choose", lambda start: chosen)
    restarted: list[Path] = []
    client = _client(root=tmp_path / "reviews", on_root_change=restarted.append)
    answer = client.post("/api/v1/settings/folder/choose", json={})
    assert answer.status_code == 202 and answer.json() == {"chosen": str(chosen.resolve()), "restarting": True}
    assert restarted == [chosen.resolve()] and user_settings.workspaces_root() == chosen.resolve()
    assert catalog.resolve_root(None) == (chosen.resolve(), "settings")
    monkeypatch.setattr(folder_dialog, "choose", lambda start: None)  # cancelled
    assert client.post("/api/v1/settings/folder/choose", json={}).json() == {"chosen": None, "restarting": False}


def test_a_folder_change_is_refused_before_anything_is_saved(tmp_path, monkeypatch):
    opened: list[object] = []
    monkeypatch.setattr(folder_dialog, "choose", lambda start: opened.append(start) or tmp_path / "x")
    serve_like = _client(root=tmp_path / "reviews")  # no restart hook: `serve`
    assert serve_like.post("/api/v1/settings/folder/choose", json={}).json()["detail"]["code"] == "RESTART_UNSUPPORTED"

    monkeypatch.setenv(catalog.ROOT_ENV, str(tmp_path / "env-root"))
    pinned = TestClient(create_app(None, token=TOKEN, on_root_change=lambda p: None), base_url="http://127.0.0.1",
                        headers={"Authorization": f"Bearer {TOKEN}"})
    assert pinned.post("/api/v1/settings/folder/choose", json={}).json()["detail"]["code"] == "SETTING_SET_ELSEWHERE"
    monkeypatch.delenv(catalog.ROOT_ENV)

    catalog.create(tmp_path / "reviews", "Busy Review")
    monkeypatch.setattr(catalog, "busy", lambda ws: {"run_active": True, "pairing_open": False})
    busy = _client(tmp_path / "reviews" / "busy-review", root=tmp_path / "reviews", on_root_change=lambda p: None)
    assert busy.post("/api/v1/settings/folder/choose", json={}).json()["detail"]["code"] == "WORKSPACE_BUSY"
    assert opened == [] and user_settings.workspaces_root() is None

    def unavailable(start):
        raise folder_dialog.FolderDialogUnavailable("no display")

    monkeypatch.setattr(catalog, "busy", lambda ws: {"run_active": False, "pairing_open": False})
    monkeypatch.setattr(folder_dialog, "choose", unavailable)
    assert busy.post("/api/v1/settings/folder/choose", json={}).json()["detail"]["code"] == "FOLDER_DIALOG_UNAVAILABLE"
    assert user_settings.workspaces_root() is None


def test_the_launcher_restarts_on_the_new_folder(tmp_path):
    ui = tmp_path / "ui"
    (ui / "en").mkdir(parents=True)
    (ui / "en" / "index.html").write_text("<html></html>", encoding="utf-8")
    catalog.create(tmp_path / "new-root", "Moved Review")
    seen = []

    class Server:
        def __init__(self, app, host, port):
            self.app, self.started, self.should_exit = app, True, False

        def run(self):
            seen.append(self.app.state.workspaces_root)
            if len(seen) == 1:
                self.app.state.on_root_change(tmp_path / "new-root")
            # the second run ends at once: the test stops after one restart

    la = launcher.Launcher(root=tmp_path / "old-root", workspace=None, ui_dir=ui, open_browser=False, say=lambda _m: None,
                           server_factory=Server)
    la.run()
    assert seen == [(tmp_path / "old-root").resolve(), (tmp_path / "new-root").resolve()]
    assert la.workspace == (tmp_path / "new-root" / "moved-review") and la.restarts == 1


def test_the_settings_folder_rules_are_shared_with_the_installed_app(tmp_path):
    from scholar_harness.console import desktop

    env = {"APPDATA": r"C:\U\R", "LOCALAPPDATA": r"C:\U\L"}
    assert desktop.app_folders(env, "win32").settings == user_settings.settings_dir(env, "win32")
    assert user_settings.settings_dir({"NEXUS_APP_HOME": "/h"}, "linux") == Path("/h/settings")
    assert user_settings.settings_dir({"NEXUS_SETTINGS_DIR": "/s", "NEXUS_APP_HOME": "/h"}, "linux") == Path("/s")
    user_settings.write_settings(contact_email="a@example.org")
    if os.name != "nt":
        assert (user_settings.settings_path().stat().st_mode & 0o777) == 0o600


def test_the_mcp_server_loads_a_key_kept_in_the_file(monkeypatch):
    """The MCP server copies stored AI keys into its environment at start; the file stands in for the keychain."""
    from scholar_agent import server

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    user_settings.store_key("gemini", FAKE_KEYS["gemini"], use_file=True)
    loaded = server._apply_keychain_keys()
    assert "GEMINI_API_KEY" in loaded and os.environ["GEMINI_API_KEY"] == FAKE_KEYS["gemini"]
    monkeypatch.delenv("GEMINI_API_KEY")
