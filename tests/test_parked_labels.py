"""Parked kits say so (production plan §8, M5-slim).

Reading PDFs is parked: its commands stay, and `--help` says in its first line
that they are not production, so nobody mistakes a working command for a
supported one. (Synthesis, the matrix and risk-of-bias/trust left with their
kits in H-remove-rag-verify; the citation graph in H-remove-graph, 2026-11-23.)

The PDF kit is split (decision 2026-11-21, M12a items 21 to 23 and 27, K0):
`download` and `ingest` are production; `extract`, `extract-run` and `acquire`
keep the notice in their own help.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

NOTICE = "PARKED, not production"


@pytest.mark.parametrize("command", ["extract", "extract-run", "acquire"])
def test_the_parked_pdf_commands_say_so_in_their_help(command):
    from scholar_pdf.cli import app

    result = CliRunner().invoke(app, [command, "--help"])
    assert result.exit_code == 0
    assert NOTICE in " ".join(result.output.split())


@pytest.mark.parametrize("command", ["download", "ingest"])
def test_the_pdf_download_commands_are_production(command):
    from scholar_pdf.cli import app

    result = CliRunner().invoke(app, [command, "--help"])
    assert result.exit_code == 0
    assert NOTICE not in " ".join(result.output.split())


def test_the_pdf_kit_group_help_names_download_and_ingest_as_production():
    from scholar_pdf.cli import app

    text = app.info.help
    assert NOTICE not in text
    assert "Production: 'download'" in text and "'ingest'" in text
    assert "parked" in text


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
