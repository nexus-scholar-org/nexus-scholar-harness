"""Actions-table <-> kit-CLI parity (SPECS.md §5 contract).

Every console action's rendered command must parse under the referenced kit
CLI: the invoked binary must exist, the subcommand must be registered, and
every flag in the template must be a declared option.  This is the standing
drift test promised (but previously missing) in ``actions.py`` and makes the
''actions-table'' prose contract executable in CI.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click
import pytest
from scholar_graph.cli import app as graph_app
from scholar_pdf.cli import app as pdf_app
from scholar_rag.cli import app as rag_app
from scholar_search.cli import app as search_app
from scholar_verify.cli import app as verify_app
from typer.core import TyperArgument, TyperOption
from typer.main import get_group

from scholar_harness.cli import app as harness_app
from scholar_harness.console.runtimes.actions import ACTIONS, render_command

CLI_APPS: dict[str, click.Group] = {
    "scholar-harness": get_group(harness_app),
    "scholar-search": get_group(search_app),
    "scholar-pdf": get_group(pdf_app),
    "scholar-rag": get_group(rag_app),
    "scholar-graph": get_group(graph_app),
    "scholar-verify": get_group(verify_app),
}

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_SCREEN_SCRIPT = REPO_ROOT / "src" / "scholar_harness" / "agent_screen.py"


def _command_surface(cmd: click.Command) -> tuple[set[str], int]:
    """Return (declared option flags, positional argument count) for a command."""
    flags: set[str] = set()
    arg_count = 0
    for param in cmd.params:
        if isinstance(param, TyperArgument):
            arg_count += 1
        elif isinstance(param, TyperOption):
            flags.update(param.opts)
    return flags, arg_count


def _usage_tokens(argv: list[str]) -> tuple[str, str, list[str]]:
    """Split a rendered action argv into (binary, subcommand, trailing tokens)."""
    assert argv[:2] == ["uv", "run"], f"action command must start with 'uv run': {argv}"
    return argv[2], argv[3], argv[4:]


def _flag_and_positional(rest: list[str]) -> tuple[list[str], int]:
    """Extract used flags and positional-argument usage from trailing tokens.

    Flag values (the token following a flag) are consumed and never counted as
    positional usage, mirroring how click/typer would parse the argv.
    """
    flags: list[str] = []
    positionals = 0
    i = 0
    while i < len(rest):
        tok = rest[i]
        if tok.startswith("-"):
            flags.append(tok)
            i += 1
            if i < len(rest) and not rest[i].startswith("-"):
                i += 1
        else:
            positionals += 1
            i += 1
    return flags, positionals


@pytest.mark.parametrize("action", ACTIONS, ids=lambda a: a.action_id)
def test_action_command_parses_against_cli(action):
    argv = render_command(action)
    binary, subcommand, rest = _usage_tokens(argv)

    if binary == "python":
        pytest.skip("agent_screen.py actions covered by test_agent_screen_subcommands_parse")

    assert binary in CLI_APPS, (
        f"action '{action.action_id}' references unknown CLI binary {binary!r}"
    )
    commands = CLI_APPS[binary].commands
    assert subcommand in commands, (
        f"action '{action.action_id}' references unknown subcommand "
        f"`{binary} {subcommand}` (known: {sorted(commands)})"
    )

    flags, arg_count = _command_surface(commands[subcommand])
    used_flags, positional_used = _flag_and_positional(rest)

    missing = [f for f in used_flags if f not in flags]
    assert not missing, (
        f"action '{action.action_id}' uses flags not declared by `{binary} {subcommand}`: {missing}"
    )

    assert positional_used <= arg_count, (
        f"action '{action.action_id}' passes {positional_used} positional arguments "
        f"but `{binary} {subcommand}` declares {arg_count}"
    )


@pytest.mark.parametrize("subcommand", ["prepare", "collect"])
def test_agent_screen_subcommands_parse(subcommand):
    """agent_screen.py prepare/collect (Agent-exchange actions) must parse."""
    result = subprocess.run(
        [sys.executable, str(AGENT_SCREEN_SCRIPT), subcommand, "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, (
        f"`agent_screen.py {subcommand} --help` failed:\n{result.stdout}\n{result.stderr}"
    )
    assert subcommand in result.stdout