"""Parked kits say so (production plan §8, M5-slim).

Synthesis, the matrix, the graph, risk-of-bias/trust and full text are parked:
their commands stay, and `--help` says in its first line that they are not
production, so nobody mistakes a working command for a supported one.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

NOTICE = "PARKED, not production"


@pytest.mark.parametrize("module", ["scholar_rag.cli", "scholar_graph.cli", "scholar_verify.cli", "scholar_pdf.cli"])
def test_a_parked_kit_says_so_in_help(module):
    import importlib

    app = importlib.import_module(module).app
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert NOTICE in " ".join(result.output.split())


def test_the_screening_commands_are_not_labelled_parked():
    from scholar_harness.cli import app

    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0 and NOTICE not in result.output


def test_parked_mcp_tools_say_so_first_and_screening_tools_do_not():
    from scholar_agent.server import PARKED_NOTICE, PARKED_TOOLS, mcp

    tools = {tool.name: tool for tool in mcp._tool_manager.list_tools()}
    assert set(PARKED_TOOLS) <= set(tools)
    for name in PARKED_TOOLS:
        assert tools[name].description.startswith(PARKED_NOTICE), name
    for name in ("nexus_screening_queue", "nexus_screening_record", "nexus_submit_proposal"):
        assert PARKED_NOTICE not in (tools[name].description or ""), name
