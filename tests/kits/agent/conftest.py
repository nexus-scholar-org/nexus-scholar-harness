"""Anchor the MCP server at each test's ``tmp_path``.

Tool path arguments must resolve inside ``NEXUS_MCP_WORKSPACE`` (AGT-01).
Tests that need another anchor set the variable themselves.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _mcp_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_MCP_WORKSPACE", str(tmp_path))
