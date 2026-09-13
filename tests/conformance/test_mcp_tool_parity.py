"""MCP tool surface parity.

The actions table references MCP tools (``actions.mcp_tool``) that must be
exported by the scholar-agent-kit MCP server, and the server's own ``--help``
must enumerate every registered tool.  Both are standing drift checks: a tool
that silently disappears from the ``@mcp.tool()`` surface (or stays hidden
from ``--help``) breaks every consumer that relies on the documented surface.
"""

from __future__ import annotations

from scholar_agent.server import main, mcp

from scholar_harness.console.runtimes.actions import ACTIONS

REGISTERED_TOOLS: set[str] = {t.name for t in mcp._tool_manager.list_tools()}


def test_action_mcp_tools_are_registered():
    referenced = {a.mcp_tool for a in ACTIONS if a.mcp_tool}
    assert referenced, "actions table should reference at least one MCP tool"
    missing = sorted(referenced - REGISTERED_TOOLS)
    assert not missing, f"actions table references unregistered MCP tools: {missing}"


def test_help_lists_all_registered_tools(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["scholar-agent", "--help"])
    main()
    out = capsys.readouterr().out
    assert "Exposed MCP Tools" in out
    hidden = sorted(t for t in REGISTERED_TOOLS if t not in out)
    assert not hidden, (
        f"'scholar-agent --help' does not list registered tool(s): {hidden}"
    )