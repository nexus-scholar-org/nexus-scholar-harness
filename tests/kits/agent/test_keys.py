"""Provider keys: keychain first, environment second, never a file (CORE-17, M1b-2).

A fake keyring stands in for the OS keychain, so no test touches the real one.
"""

from __future__ import annotations

import sys
import types

import pytest
from typer.testing import CliRunner

from scholar_agent import keys
from scholar_harness.cli import app

SECRET = "sk-ant-test-0123456789"


@pytest.fixture
def keychain(monkeypatch):
    store: dict[tuple[str, str], str] = {}
    fake = types.ModuleType("keyring")
    fake.get_password = lambda service, user: store.get((service, user))
    fake.set_password = lambda service, user, value: store.__setitem__((service, user), value)

    def delete(service, user):
        if (service, user) not in store:
            raise KeyError(user)
        del store[(service, user)]

    fake.delete_password = delete
    monkeypatch.setitem(sys.modules, "keyring", fake)
    for var in keys.ENV_VARS.values():
        monkeypatch.delenv(var, raising=False)
    return store


def test_keychain_wins_over_the_environment(keychain, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-env")
    assert keys.resolve_key("anthropic") == "from-env"
    assert keys.key_status("anthropic").source == "environment"
    keys.store_key("anthropic", SECRET)
    assert keychain[(keys.SERVICE, "anthropic")] == SECRET
    assert keys.resolve_key("anthropic") == SECRET and keys.key_status("anthropic").source == "keychain"
    assert keys.clear_key("anthropic") is True and keys.resolve_key("anthropic") == "from-env"


def test_no_key_anywhere_is_none_and_an_empty_key_is_refused(keychain):
    assert keys.resolve_key("gemini") is None and not keys.key_status("gemini").present
    with pytest.raises(ValueError):
        keys.store_key("gemini", "   ")
    with pytest.raises(ValueError, match="unknown provider"):
        keys.resolve_key("local")


def test_without_a_keychain_backend_storing_refuses_and_reading_falls_back(monkeypatch):
    monkeypatch.setitem(sys.modules, "keyring", None)  # import keyring -> ImportError
    monkeypatch.setenv("GEMINI_API_KEY", "g-env")
    assert keys.resolve_key("gemini") == "g-env"
    with pytest.raises(RuntimeError, match="ai"):
        keys.store_key("gemini", "x")


def test_cli_status_never_prints_a_key_and_set_reads_a_hidden_prompt(keychain):
    runner = CliRunner()
    result = runner.invoke(app, ["keys", "set", "anthropic"], input=SECRET + "\n")
    assert result.exit_code == 0, result.output
    assert SECRET not in result.output
    status = runner.invoke(app, ["keys", "status"])
    assert "anthropic: keychain" in status.output and "gemini: none" in status.output
    assert SECRET not in status.output
