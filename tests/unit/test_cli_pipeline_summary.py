"""Truthfulness of the ``scholar-harness run`` summary panel.

T-TRUTH-COUNTS-01 / CLI-CLOSURE: the CLI panel used to announce
"Research Pipeline Execution Completed Successfully!" unconditionally and to
exit 0 for every pipeline outcome. The pipeline publishes a workflow status
(``SUCCESS`` | ``EMPTY_RESULT`` | ``PENDING_AGENT_REVIEW`` | ``FAILED``), a
separate degradation signal (``results["degraded"]`` /
``results["degradation_reason"]``) and a discovery outcome
(``SUCCESS`` | ``PARTIAL`` | ``EMPTY_RESULT`` | ``FAILED``). The panel must
state the real outcome, and the exit code must be non-zero only for a hard
``FAILED`` run.

These tests exercise the RENDERED output (via typer's ``CliRunner``), not
just the return value, and they cover the second rendering bug: a stage entry
is either a plain int or a mapping (``{"unique": 5, ...}`` on the normal
path, ``{"status": "SKIPPED", "reason": ...}`` on the abort path), so the
panel must never render a raw mapping.
"""

from __future__ import annotations

import io
import json
import re
from pathlib import Path
from typing import ClassVar

from rich.console import Console
from rich.panel import Panel
from typer.testing import CliRunner

from scholar_harness import cli as cli_mod
from scholar_harness.cli import app

runner = CliRunner()

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_BORDER_CHARS = "│─┌┐└┘╭╮╯╰━┃┏┓┗┛"


def _plain(text: str) -> str:
    """ANSI-free, border-free, whitespace-collapsed rendering of the output."""
    stripped = _ANSI_RE.sub("", text)
    for char in _BORDER_CHARS:
        stripped = stripped.replace(char, " ")
    return re.sub(r"\s+", " ", stripped).strip()


def _reference_border_codes(border_style: str) -> set[str]:
    """The ANSI codes the harness console emits for ``border_style``.

    Rendered with the *same* console settings as the CLI console so the
    comparison holds under any colour system (standard / 256 / truecolor).
    """
    buffer = io.StringIO()
    reference = Console(
        file=buffer,
        force_terminal=True,
        legacy_windows=False,
        width=200,
        color_system=cli_mod.console.color_system,
    )
    reference.print(Panel.fit("probe", border_style=border_style))
    return set(_ANSI_RE.findall(buffer.getvalue()))


def _assert_border_style(output: str, expected: str) -> None:
    """Assert the rendered panel border carries ``expected``'s colour."""
    codes = _reference_border_codes(expected)
    if not codes:
        # No colour system available: fall back to the declared style.
        assert expected
        return
    assert codes & set(_ANSI_RE.findall(output)), (
        f"expected the {expected!r} border colour {sorted(codes)} in the "
        f"rendered output"
    )


class _StubOrchestrator:
    """Orchestrator double that returns a canned pipeline result mapping."""

    results: ClassVar[dict] = {}

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace

    def run_pipeline(self, protocol_path=None, max_search_results=None):
        return dict(type(self).results)


def _invoke_run(monkeypatch, results: dict, tmp_path: Path):
    """Run the CLI ``run`` command against a stubbed pipeline result."""
    _StubOrchestrator.results = results
    monkeypatch.setattr(cli_mod, "ResearchOrchestrator", _StubOrchestrator)
    protocol = tmp_path / "protocol.json"
    protocol.write_text("{}", encoding="utf-8")
    workspace = tmp_path / "ws"
    workspace.mkdir(exist_ok=True)
    return runner.invoke(
        app,
        [
            "run",
            "--protocol",
            str(protocol),
            "--workspace",
            str(workspace),
        ],
    )


def _normal_stages() -> dict:
    """Stage mapping as published on the normal (non-aborted) path."""
    return {
        "discovery": 12,
        "deduplication": {"unique": 9, "duplicates_removed": 3},
        "verification": {"status": "DONE", "verified": 9},
        "screening": {
            "status": "PENDING_AGENT_REVIEW",
            "batch_files_prepared": 1,
            "papers_to_screen": 9,
        },
        "extraction": {"status": "DONE", "documents": 7},
        "matrix_rows": {"status": "DONE", "rows": 4},
        "graph_nodes": {"status": "DONE", "nodes": 7, "edges": 11},
        "synthesis": {"verified_claims": 3, "total_claims": 5},
    }


def _aborted_stages() -> dict:
    """Stage mapping as published on the abort path (every stage SKIPPED)."""
    reason = "discovery failed: no provider returned documents"
    return {
        "discovery": 0,
        "deduplication": {
            "unique": 0,
            "duplicates_removed": 0,
            "status": "SKIPPED",
            "reason": reason,
        },
        "verification": {
            "verified": 0,
            "refused": 0,
            "status": "SKIPPED",
            "reason": reason,
        },
        "screening": {
            "batch_files_prepared": 0,
            "papers_to_screen": 0,
            "status": "SKIPPED",
            "reason": reason,
        },
        "extraction": {"status": "SKIPPED", "reason": reason},
        "matrix_rows": {"rows": 0, "status": "SKIPPED", "reason": reason},
        "graph_nodes": {"nodes": 0, "edges": 0, "status": "SKIPPED", "reason": reason},
        "synthesis": {
            "verified_claims": 0,
            "total_claims": 0,
            "status": "SKIPPED",
            "reason": reason,
        },
    }


# --------------------------------------------------------------------------
# SUCCESS
# --------------------------------------------------------------------------


def test_success_status_renders_success_headline_and_success_border(
    monkeypatch, tmp_path
):
    """A genuinely successful run keeps the success wording and the green border."""
    result = _invoke_run(
        monkeypatch,
        {
            "status": "SUCCESS",
            "stages": _normal_stages(),
            "degraded": False,
            "degradation_reason": "",
        },
        tmp_path,
    )

    assert result.exit_code == 0
    plain = _plain(result.stdout)
    assert "Successfully" in plain
    assert "Status: SUCCESS" in plain
    assert "Deduplicated: 9 unique" in plain
    assert "Markdown Extracts: 7" in plain
    assert "Matrix Rows: 4" in plain
    assert "Graph Nodes: 7" in plain
    _assert_border_style(result.stdout, "green")


# --------------------------------------------------------------------------
# EMPTY_RESULT
# --------------------------------------------------------------------------


def test_empty_result_status_never_claims_success_and_exits_zero(monkeypatch, tmp_path):
    """An empty harvest is named plainly and is not a success (exit 0)."""
    result = _invoke_run(
        monkeypatch,
        {
            "status": "EMPTY_RESULT",
            "stages": {"discovery": 0},
            "degraded": False,
            "degradation_reason": "",
            "discovery": {
                "count": 0,
                "status": "EMPTY_RESULT",
                "reason": "no provider returned documents",
            },
        },
        tmp_path,
    )

    assert result.exit_code == 0
    plain = _plain(result.stdout)
    assert "Successfully" not in plain
    assert "NO Results Discovered" in plain
    assert "Status: EMPTY_RESULT" in plain
    assert "Discovery harvest: EMPTY_RESULT" in plain
    _assert_border_style(result.stdout, "yellow")


# --------------------------------------------------------------------------
# PENDING_AGENT_REVIEW
# --------------------------------------------------------------------------


def test_pending_agent_review_names_the_pause_and_exits_zero(monkeypatch, tmp_path):
    """A pipeline waiting for the PRISMA handoff is announced as paused."""
    result = _invoke_run(
        monkeypatch,
        {
            "status": "PENDING_AGENT_REVIEW",
            "stages": _normal_stages(),
            "degraded": False,
            "degradation_reason": "",
        },
        tmp_path,
    )

    assert result.exit_code == 0
    plain = _plain(result.stdout)
    assert "Successfully" not in plain
    assert "Paused" in plain
    assert "screening" in plain.lower()
    assert "Status: PENDING_AGENT_REVIEW" in plain
    _assert_border_style(result.stdout, "cyan")


# --------------------------------------------------------------------------
# FAILED
# --------------------------------------------------------------------------


def test_failed_status_never_claims_success_and_exits_non_zero(monkeypatch, tmp_path):
    """A hard failure is announced as a failure and exits non-zero."""
    result = _invoke_run(
        monkeypatch,
        {
            "status": "FAILED",
            "stages": _aborted_stages(),
            "degraded": False,
            "degradation_reason": "",
            "discovery": {
                "count": 0,
                "status": "FAILED",
                "reason": "no provider returned documents",
            },
        },
        tmp_path,
    )

    assert result.exit_code != 0
    assert result.exit_code == 1
    plain = _plain(result.stdout)
    assert "Successfully" not in plain
    assert "Research Pipeline FAILED" in plain
    assert "Status: FAILED" in plain
    _assert_border_style(result.stdout, "red")


# --------------------------------------------------------------------------
# Degradation
# --------------------------------------------------------------------------


def test_degraded_run_surfaces_the_degradation_reason(monkeypatch, tmp_path):
    """A degraded harvest is surfaced and never carries an unqualified success."""
    result = _invoke_run(
        monkeypatch,
        {
            "status": "SUCCESS",
            "stages": _normal_stages(),
            "degraded": True,
            "degradation_reason": "openalex provider failed: HTTP 503",
            "discovery": {
                "count": 12,
                "status": "PARTIAL",
                "reason": "openalex provider failed: HTTP 503",
            },
        },
        tmp_path,
    )

    assert result.exit_code == 0
    plain = _plain(result.stdout)
    assert "Degraded harvest: openalex provider failed: HTTP 503" in plain
    assert "Successfully" not in plain
    assert "Discovery harvest: PARTIAL" in plain
    _assert_border_style(result.stdout, "yellow")


# --------------------------------------------------------------------------
# A missing status is NOT a success
# --------------------------------------------------------------------------


def test_missing_status_never_renders_a_success_claim(monkeypatch, tmp_path):
    """F-3: an absent status is an unknown outcome, never a success.

    The panel used to default a missing status to ``SUCCESS``, so an empty
    result mapping rendered "Research Pipeline Execution Completed
    Successfully!" -- a false success claim about a run that never reported
    an outcome.
    """
    result = _invoke_run(monkeypatch, {}, tmp_path)

    plain = _plain(result.stdout)
    assert "Successfully" not in plain
    assert "unrecognised status" in plain
    assert "Status: UNKNOWN" in plain


# --------------------------------------------------------------------------
# Stage-shape rendering
# --------------------------------------------------------------------------


def test_abort_path_stage_mapping_renders_numbers_never_raw_mappings(
    monkeypatch, tmp_path
):
    """Skipped stages (mapping-shaped) render as integers, never as a dict."""
    result = _invoke_run(
        monkeypatch,
        {
            "status": "FAILED",
            "stages": _aborted_stages(),
            "degraded": False,
            "degradation_reason": "",
        },
        tmp_path,
    )

    plain = _plain(result.stdout)
    assert result.exit_code == 1
    assert "Deduplicated: 0 unique" in plain
    assert "Markdown Extracts: 0" in plain
    assert "Matrix Rows: 0" in plain
    assert "Graph Nodes: 0" in plain
    assert "Grounded Claims: 0 / 0 verified" in plain
    # No raw Python mapping / None ever reaches the user.
    assert "{" not in plain
    assert "}" not in plain
    assert "None" not in plain
    assert "'unique'" not in plain


def test_normal_path_mapping_stages_render_their_counts(monkeypatch, tmp_path):
    """A mapping-shaped stage on the normal path renders its count, not the mapping."""
    result = _invoke_run(
        monkeypatch,
        {
            "status": "SUCCESS",
            "stages": _normal_stages(),
            "degraded": False,
            "degradation_reason": "",
        },
        tmp_path,
    )

    plain = _plain(result.stdout)
    assert result.exit_code == 0
    assert "Discovered: 12 papers" in plain
    assert "Deduplicated: 9 unique" in plain
    assert "Grounded Claims: 3 / 5 verified" in plain
    assert "{" not in plain
    assert "}" not in plain


def test_missing_stage_entries_render_zero_never_none(monkeypatch, tmp_path):
    """A stage that was never reached renders as 0, never as None."""
    result = _invoke_run(
        monkeypatch,
        {
            "status": "SUCCESS",
            "stages": {},
            "degraded": False,
            "degradation_reason": "",
        },
        tmp_path,
    )

    plain = _plain(result.stdout)
    assert result.exit_code == 0
    assert "Discovered: 0 papers" in plain
    assert "Deduplicated: 0 unique" in plain
    assert "None" not in plain


# --------------------------------------------------------------------------
# The PipelineSpec DAG path is out of scope and must stay untouched
# --------------------------------------------------------------------------


def test_pipeline_spec_path_is_unaffected(monkeypatch, tmp_path):
    """The ``--pipeline`` DAG path keeps its own summary (not the new panel)."""
    spec = {
        "schema_version": "0.1.0",
        "id": "cli_closure_spec",
        "name": "CLI closure spec",
        "archetype": "PRISMA_SLR",
        "workspace_slug": "cli-closure",
        "settings": {},
        "nodes": [
            {
                "id": "n1",
                "kit": "test",
                "command": ["python", "-c", "print('ok')"],
                "args": {},
                "inputs": [],
                "outputs": [],
                "on_fail": "abort",
            }
        ],
        "edges": [],
        "dry_run": {},
        "created_by": "test",
    }
    spec_file = tmp_path / "pipeline.json"
    spec_file.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    workspace = tmp_path / "ws"
    workspace.mkdir()

    result = runner.invoke(
        app, ["run", "--pipeline", str(spec_file), "--workspace", str(workspace)]
    )

    assert result.exit_code == 0
    plain = _plain(result.stdout)
    assert "Pipeline Execution Summary" not in plain
    assert "PipelineSpec" in plain
