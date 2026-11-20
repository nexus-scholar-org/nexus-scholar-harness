"""Shared setup for the agent-kit tests.

- The MCP server is anchored at each test's ``tmp_path``: tool path arguments
  must resolve inside ``NEXUS_MCP_WORKSPACE`` (AGT-01). Tests that need another
  anchor set the variable themselves.
- No test reads the real OS keychain or a real provider key: a fake keychain
  stands in for `keyring` and the provider key variables are removed from the
  environment (H-key-precedence-2026-11-20). `keychain` is the fake's store.
- The provider SDK check (`drivers.ensure_sdk`) is a no-op, because the test
  environment has no `anthropic` and the CLI tests drive fake drivers. A test of
  the missing-SDK message restores the real function itself.
"""

from __future__ import annotations

import sys
import types

import pytest


@pytest.fixture(autouse=True)
def _mcp_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_MCP_WORKSPACE", str(tmp_path))


@pytest.fixture(autouse=True)
def keychain(monkeypatch):
    """A fake keychain (and no provider key in the environment): the dict is its contents."""
    from scholar_agent import keys

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


@pytest.fixture(autouse=True)
def _sdk_present(monkeypatch):
    from scholar_agent import drivers

    monkeypatch.setattr(drivers, "ensure_sdk", lambda provider: None, raising=False)
