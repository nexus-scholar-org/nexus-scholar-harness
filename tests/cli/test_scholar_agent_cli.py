"""Hermetic unit tests for scholar-agent CLI entrypoint (Phase 7 Task P7.1)."""

from __future__ import annotations

import os
import subprocess
import sys
from unittest.mock import patch

import pytest
from scholar_agent import server
from scholar_agent.server import main


@pytest.fixture(autouse=True)
def clean_env():
    orig_ws = os.environ.get("NEXUS_MCP_WORKSPACE")
    orig_recon = os.environ.get("NEXUS_RECON_ROOT")
    yield
    if orig_ws is not None:
        os.environ["NEXUS_MCP_WORKSPACE"] = orig_ws
    else:
        os.environ.pop("NEXUS_MCP_WORKSPACE", None)
    if orig_recon is not None:
        os.environ["NEXUS_RECON_ROOT"] = orig_recon
    else:
        os.environ.pop("NEXUS_RECON_ROOT", None)


@pytest.mark.slow
def test_scholar_agent_cli_help_subprocess():
    """Verify scholar-agent --help succeeds and lists options and tools."""
    res = subprocess.run(
        [sys.executable, "-m", "scholar_agent.server", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "-w WORKSPACE" in res.stdout or "--workspace" in res.stdout
    assert "--transport" in res.stdout
    assert "nexus_screening_queue" in res.stdout
    # H-remove-rag-verify: the removed tools are not advertised.
    assert "nexus_verify_phase4" not in res.stdout
    assert "nexus_rag_query" not in res.stdout
    assert "recon_delta" in res.stdout


def test_scholar_agent_cli_workspace_flag(tmp_path):
    """Verify --workspace sets NEXUS_MCP_WORKSPACE and anchors relative paths."""
    ws = tmp_path / "custom_ws"

    with patch.object(server.mcp, "run") as mock_run:
        main(["--workspace", str(ws)])
        assert mock_run.called
        assert mock_run.call_args.kwargs.get("transport") == "stdio"

    assert os.environ["NEXUS_MCP_WORKSPACE"] == str(ws.resolve())
    assert os.environ["NEXUS_RECON_ROOT"] == str((ws / ".cache" / "inception_recon").resolve())

    # Relative paths should now anchor against ws
    resolved = server._resolve_path("literature/included.json")
    assert resolved == str((ws / "literature" / "included.json").resolve())


def test_scholar_agent_cli_short_workspace_flag(tmp_path):
    """Verify -w short alias works identically to --workspace."""
    ws = tmp_path / "short_ws"

    with patch.object(server.mcp, "run") as mock_run:
        main(["-w", str(ws), "--transport", "stdio"])
        assert mock_run.called

    assert os.environ["NEXUS_MCP_WORKSPACE"] == str(ws.resolve())



def test_scholar_agent_cli_transport_passthrough(tmp_path):
    """Verify --transport argument passes through to mcp.run()."""
    ws = tmp_path / "transport_ws"

    with patch.object(server.mcp, "run") as mock_run:
        main(["--workspace", str(ws), "--transport", "sse"])
        assert mock_run.called
        assert mock_run.call_args.kwargs.get("transport") == "sse"
