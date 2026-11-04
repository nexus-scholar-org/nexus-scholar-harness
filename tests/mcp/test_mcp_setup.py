"""P7.4 tests: ``nexus-scholar setup-mcp`` — harness-agnostic MCP wiring.

Hermetic: ``tmp_path`` workspaces + a monkeypatched ``NEXUS_MCP_CONFIG_HOME``
so nothing touches real ``%APPDATA%``/``~/.config`` (and claude's location is
CWD-independent on every platform).
"""

from __future__ import annotations

import json
import re

from typer.testing import CliRunner

from scholar_harness.cli import app

runner = CliRunner()

# Rich renders typer help through a Console; when the environment forces color
# (FORCE_COLOR, CI, a tty) ANSI style codes are interleaved inside the rendered
# flag text, so raw ``in result.stdout`` checks only hold in plain-render
# environments. Stripping the escapes asserts the real invariant -- the flag is
# registered and documented in ``--help`` -- under every rendering mode.
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _help_text(result) -> str:
    """The ``--help`` output with ANSI styling removed (render-mode independent)."""
    return _ANSI_RE.sub("", result.stdout)


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


def test_setup_mcp_command_registered():
    result = runner.invoke(app, ["setup-mcp", "--help"])
    assert result.exit_code == 0
    help_text = _help_text(result)
    assert "--workspace" in help_text
    assert "--harness" in help_text
    assert "--dry-run" in help_text
    assert "--env-file" in help_text
    assert "Wire the nexus-scholar MCP server into harness config files" in help_text


# ---------------------------------------------------------------------------
# default `all` plan + NEXUS_MCP_CONFIG_HOME override
# ---------------------------------------------------------------------------


def test_setup_mcp_default_all_targets(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_MCP_CONFIG_HOME", str(tmp_path / "cfg"))
    ws = tmp_path / "ws"
    ws.mkdir()

    # No --harness: default `all` → claude + cursor + vscode + mcp, dsh printed.
    result = runner.invoke(app, ["setup-mcp", "--workspace", str(ws)])
    assert result.exit_code == 0, result.stdout

    assert (ws / ".mcp.json").is_file()
    assert (ws / ".cursor" / "mcp.json").is_file()
    assert (ws / ".vscode" / "mcp.json").is_file()
    claude = tmp_path / "cfg" / "Claude" / "claude_desktop_config.json"
    assert claude.is_file()
    # DSH is instructions-only — printed, never written.
    assert "DSH Settings" in result.stdout
    assert "manual" in result.stdout


def test_setup_mcp_claude_config_home_override(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_MCP_CONFIG_HOME", str(tmp_path / "custom-config"))
    ws = tmp_path / "ws"
    ws.mkdir()
    result = runner.invoke(app, ["setup-mcp", "--workspace", str(ws), "--harness", "claude"])
    assert result.exit_code == 0, result.stdout
    claude = tmp_path / "custom-config" / "Claude" / "claude_desktop_config.json"
    assert claude.is_file()
    entry = json.loads(claude.read_text(encoding="utf-8"))["mcpServers"]["nexus-scholar"]
    assert entry["command"] == "uvx"
    assert entry["args"][:2] == ["--from", "nexus-scholar"]
    i = entry["args"].index("--workspace")
    assert entry["args"][i + 1] == str(ws.resolve())
    assert "${workspaceFolder}" not in claude.read_text(encoding="utf-8")


def test_setup_mcp_space_separated_harness_values(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_MCP_CONFIG_HOME", str(tmp_path / "cfg"))
    ws = tmp_path / "ws"
    ws.mkdir()
    result = runner.invoke(
        app, ["setup-mcp", "--workspace", str(ws), "--harness", "claude cursor mcp"]
    )
    assert result.exit_code == 0, result.stdout
    assert (tmp_path / "cfg" / "Claude" / "claude_desktop_config.json").is_file()
    assert (ws / ".cursor" / "mcp.json").is_file()
    assert (ws / ".mcp.json").is_file()
    assert not (ws / ".vscode" / "mcp.json").exists()


# ---------------------------------------------------------------------------
# merge / idempotency
# ---------------------------------------------------------------------------


def test_setup_mcp_merge_preserves_foreign_servers(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_MCP_CONFIG_HOME", str(tmp_path / "cfg"))
    ws = tmp_path / "ws"
    ws.mkdir()
    foreign = {
        "$schema": "https://example.invalid/schema.json",
        "mcpServers": {"other-tool": {"command": "npx", "args": ["serve", "--port", "9999"]}},
    }
    (ws / ".mcp.json").write_text(json.dumps(foreign), encoding="utf-8")

    result = runner.invoke(app, ["setup-mcp", "--workspace", str(ws), "--harness", "mcp"])
    assert result.exit_code == 0, result.stdout
    assert "updated" in result.stdout

    cfg = json.loads((ws / ".mcp.json").read_text(encoding="utf-8"))
    assert set(cfg["mcpServers"]) == {"other-tool", "nexus-scholar"}
    assert cfg["mcpServers"]["other-tool"] == {"command": "npx", "args": ["serve", "--port", "9999"]}
    assert cfg["$schema"] == "https://example.invalid/schema.json"  # top-level keys preserved


def test_setup_mcp_idempotent_and_byte_stable(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_MCP_CONFIG_HOME", str(tmp_path / "cfg"))
    ws = tmp_path / "ws"
    ws.mkdir()
    args = [
        "setup-mcp",
        "--workspace", str(ws),
        "--harness", "claude,cursor,vscode,mcp",
    ]

    first = runner.invoke(app, args)
    assert first.exit_code == 0, first.stdout
    assert "created" in first.stdout

    mcp_bytes = (ws / ".mcp.json").read_bytes()
    second = runner.invoke(app, args)
    assert second.exit_code == 0, second.stdout
    assert "unchanged" in second.stdout
    assert "created" not in second.stdout
    assert "updated" not in second.stdout
    # Idempotent: second identical run rewrites nothing — bytes are identical.
    assert (ws / ".mcp.json").read_bytes() == mcp_bytes


def test_setup_mcp_no_env_file_means_no_env_block(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_MCP_CONFIG_HOME", str(tmp_path / "cfg"))
    ws = tmp_path / "ws"
    ws.mkdir()
    result = runner.invoke(app, ["setup-mcp", "--workspace", str(ws), "--harness", "mcp"])
    assert result.exit_code == 0, result.stdout
    entry = json.loads((ws / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["nexus-scholar"]
    assert "env" not in entry


# ---------------------------------------------------------------------------
# --dry-run
# ---------------------------------------------------------------------------


def test_setup_mcp_dry_run_writes_nothing_deterministic(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_MCP_CONFIG_HOME", str(tmp_path / "cfg"))
    ws = tmp_path / "ws"
    ws.mkdir()
    args = ["setup-mcp", "--workspace", str(ws), "--harness", "all", "--dry-run"]

    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.stdout
    # Exact plan is shown (created file + its would-be config JSON)…
    assert "created" in result.stdout
    assert '"mcpServers"' in result.stdout
    # …but nothing lands on disk.
    assert not (ws / ".mcp.json").exists()
    assert not (ws / ".cursor" / "mcp.json").exists()
    assert not (ws / ".vscode" / "mcp.json").exists()
    assert not (tmp_path / "cfg").exists()

    again = runner.invoke(app, args)
    assert again.stdout == result.stdout


# ---------------------------------------------------------------------------
# env passthrough
# ---------------------------------------------------------------------------


def test_setup_mcp_never_writes_key_values(tmp_path, monkeypatch):
    """CORE-17: config files carry a pointer to the env file, never its values."""
    monkeypatch.setenv("NEXUS_MCP_CONFIG_HOME", str(tmp_path / "cfg"))
    ws = tmp_path / "ws"
    ws.mkdir()
    env = ws / ".env"
    env.write_text(
        "SCHOLAR_MAILTO=me@example.com\n"
        "OPENAI_API_KEY=sk-open-secret\n"
        "ANTHROPIC_API_KEY=sk-ant-secret\n",
        encoding="utf-8",
    )
    result = runner.invoke(
        app,
        ["setup-mcp", "--workspace", str(ws), "--harness", "claude,cursor,vscode,mcp",
         "--env-file", str(env)],
    )
    assert result.exit_code == 0, result.stdout

    targets = [
        tmp_path / "cfg" / "Claude" / "claude_desktop_config.json",
        ws / ".cursor" / "mcp.json",
        ws / ".vscode" / "mcp.json",
        ws / ".mcp.json",
    ]
    for path in targets:
        raw = path.read_text(encoding="utf-8")
        assert "sk-open-secret" not in raw and "sk-ant-secret" not in raw, path
        assert "me@example.com" not in raw, path
        entry = json.loads(raw)["mcpServers"]["nexus-scholar"]
        assert "env" not in entry, path
        args = entry["args"]
        assert args[args.index("--env-file") + 1] == str(env.resolve()), path


def test_server_env_file_selects_known_keys_without_overriding(tmp_path, monkeypatch):
    """The server loads approved keys from the env file; the real env wins."""
    from scholar_agent.server import _apply_env_file

    env = tmp_path / ".env"
    env.write_bytes(
        "﻿OPENAI_API_KEY=sk-bommed\n"
        "SCHOLAR_MAILTO=file@example.com\n"
        "NEXUS_MCP_CONFIG_HOME=/never\n"
        "SOME_FOREIGN_KEY=zzz\n".encode("utf-8")
    )
    for key in ("OPENAI_API_KEY", "NEXUS_MCP_CONFIG_HOME", "SOME_FOREIGN_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("SCHOLAR_MAILTO", "shell@example.com")

    loaded = _apply_env_file(env)

    assert sorted(loaded) == ["OPENAI_API_KEY"]
    import os

    assert os.environ["OPENAI_API_KEY"] == "sk-bommed"  # BOM does not swallow the key
    assert os.environ["SCHOLAR_MAILTO"] == "shell@example.com"
    assert "NEXUS_MCP_CONFIG_HOME" not in os.environ
    assert "SOME_FOREIGN_KEY" not in os.environ


def test_secret_bearing_files_are_gitignored():
    """CORE-17: .env and generated MCP configs never enter git."""
    import subprocess

    paths = [
        ".env",
        ".mcp.json",
        ".cursor/mcp.json",
        "workspaces/demo/.env",
        "workspaces/demo/.mcp.json",
        "workspaces/demo/.cursor/mcp.json",
    ]
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", *paths],
        capture_output=True,
        text=True,
        check=False,
    )
    ignored = set(result.stdout.split())
    assert ignored == set(paths), sorted(set(paths) - ignored)


def test_setup_mcp_never_prints_env_values(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_MCP_CONFIG_HOME", str(tmp_path / "cfg"))
    ws = tmp_path / "ws"
    ws.mkdir()
    secret = "sk-super-secret-value-xyz"
    env = ws / ".env"
    env.write_text(f"OPENAI_API_KEY={secret}\nSCHOLAR_MAILTO=private-me@example.com\n", encoding="utf-8")

    result = runner.invoke(
        app, ["setup-mcp", "--workspace", str(ws), "--harness", "mcp", "--env-file", str(env)]
    )
    assert result.exit_code == 0, result.stdout
    assert secret not in result.stdout
    assert "private-me@example.com" not in result.stdout

    # dry-run redacts values in the would-be config JSON (***, keys preserved)
    dry = runner.invoke(
        app,
        ["setup-mcp", "--workspace", str(ws), "--harness", "claude", "--env-file", str(env), "--dry-run"],
    )
    assert dry.exit_code == 0, dry.stdout
    assert secret not in dry.stdout

    # Redaction is structural: values → ***, key names preserved.
    from scholar_harness.mcp_setup import _masked_json

    masked = _masked_json(
        {
            "mcpServers": {
                "nexus-scholar": {
                    "command": "uvx",
                    "args": [],
                    "env": {"OPENAI_API_KEY": secret, "SCHOLAR_MAILTO": "private"}, 
                },
            },
        },
    )
    assert "OPENAI_API_KEY" in masked and "SCHOLAR_MAILTO" in masked
    assert secret not in masked and "private" not in masked
    assert masked.count("***") == 2


def test_setup_mcp_default_env_file_from_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_MCP_CONFIG_HOME", str(tmp_path / "cfg"))
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".env").write_text("SCHOLAR_MAILTO=a@b.c\n", encoding="utf-8")

    result = runner.invoke(app, ["setup-mcp", "--workspace", str(ws), "--harness", "mcp"])
    assert result.exit_code == 0, result.stdout
    entry = json.loads((ws / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["nexus-scholar"]
    assert "env" not in entry
    assert entry["args"][entry["args"].index("--env-file") + 1] == str((ws / ".env").resolve())


def test_setup_mcp_vscode_skips_env_but_notes(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_MCP_CONFIG_HOME", str(tmp_path / "cfg"))
    ws = tmp_path / "ws"
    ws.mkdir()
    env = ws / ".env"
    env.write_text("OPENAI_API_KEY=sk-vscode\n", encoding="utf-8")
    result = runner.invoke(
        app, ["setup-mcp", "--workspace", str(ws), "--harness", "vscode", "--env-file", str(env)]
    )
    assert result.exit_code == 0, result.stdout
    entry = json.loads((ws / ".vscode" / "mcp.json").read_text(encoding="utf-8"))["mcpServers"]["nexus-scholar"]
    # The server reads the env file itself, so VS Code works like every target.
    assert "env" not in entry
    assert "--env-file" in entry["args"]
    assert "sk-vscode" not in result.stdout


# ---------------------------------------------------------------------------
# refusal rules + dsh
# ---------------------------------------------------------------------------


def test_setup_mcp_missing_workspace_exits_1(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_MCP_CONFIG_HOME", str(tmp_path / "cfg"))
    result = runner.invoke(app, ["setup-mcp", "--workspace", str(tmp_path / "ghost")])
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower()
    assert not (tmp_path / "cfg").exists(), "nothing may be written on refusal"


def test_setup_mcp_unknown_harness_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_MCP_CONFIG_HOME", str(tmp_path / "cfg"))
    ws = tmp_path / "ws"
    ws.mkdir()
    result = runner.invoke(app, ["setup-mcp", "--workspace", str(ws), "--harness", "bogus"])
    assert result.exit_code == 1
    assert "bogus" in result.stdout
    assert not (ws / ".mcp.json").exists()


def test_setup_mcp_dsh_prints_instructions_only(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    result = runner.invoke(app, ["setup-mcp", "--workspace", str(ws), "--harness", "dsh"])
    assert result.exit_code == 0, result.stdout
    assert "DSH Settings" in result.stdout
    assert "--from" in result.stdout
    assert not (ws / ".mcp.json").exists()
    assert not (ws / ".cursor").exists()
    assert not (ws / ".vscode").exists()


# ---------------------------------------------------------------------------
# shared builder seam (write_mcp_json ↔ setup-mcp ≡ build_mcp_entry)
# ---------------------------------------------------------------------------


def test_build_mcp_entry_shared_with_init(tmp_path):
    from scholar_harness.inception import write_mcp_json
    from scholar_harness.mcp_setup import build_mcp_entry

    ws = tmp_path / "w"
    ws.mkdir()
    path = write_mcp_json(ws)
    cfg = json.loads(path.read_text(encoding="utf-8"))
    entry = cfg["mcpServers"]["nexus-scholar"]
    assert entry == build_mcp_entry(ws)
    # Absolute path in the cooked args, not a ${workspaceFolder} macro.
    assert entry["args"][entry["args"].index("--workspace") + 1] == str(ws.resolve())


# ---------------------------------------------------------------------------
# clamp regressions (reviewer): corrupt-JSON rebuild, init->setup-mcp byte
# stability on the same workspace, missing --env-file warning, dir-as-target
# ---------------------------------------------------------------------------


def test_setup_mcp_rebuilds_corrupt_config(tmp_path, monkeypatch):
    """A corrupt/missing config file is rebuilt cleanly (documented behavior)."""
    monkeypatch.setenv("NEXUS_MCP_CONFIG_HOME", str(tmp_path / "cfg"))
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".mcp.json").write_text("{invalid", encoding="utf-8")

    result = runner.invoke(app, ["setup-mcp", "--workspace", str(ws), "--harness", "mcp"])
    assert result.exit_code == 0, result.stdout
    assert "updated" in result.stdout

    cfg = json.loads((ws / ".mcp.json").read_text(encoding="utf-8"))
    assert set(cfg["mcpServers"]) == {"nexus-scholar"}
    assert cfg["mcpServers"]["nexus-scholar"]["command"] == "uvx"


def test_setup_mcp_unchanged_after_init(tmp_path, monkeypatch):
    """init->setup-mcp hand-off must report `unchanged`, not rewrite (CRLF clamp).

    The suite's setup-mcp->setup-mcp idempotency tests can't see a writer
    divergence between ``write_mcp_json`` (init) and ``setup-mcp``; this one
    crosses the seam with byte comparison.
    """
    from scholar_harness.inception import write_mcp_json

    monkeypatch.setenv("NEXUS_MCP_CONFIG_HOME", str(tmp_path / "cfg"))
    ws = tmp_path / "ws"
    ws.mkdir()

    write_mcp_json(ws)  # what `nexus-scholar init --scaffold-only` emits
    init_bytes = (ws / ".mcp.json").read_bytes()

    result = runner.invoke(app, ["setup-mcp", "--workspace", str(ws), "--harness", "mcp"])
    assert result.exit_code == 0, result.stdout
    assert "unchanged" in result.stdout
    assert (ws / ".mcp.json").read_bytes() == init_bytes


def test_setup_mcp_missing_env_file_warns_and_continues(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_MCP_CONFIG_HOME", str(tmp_path / "cfg"))
    ws = tmp_path / "ws"
    ws.mkdir()
    missing = tmp_path / "does-not-exist.env"
    result = runner.invoke(
        app, ["setup-mcp", "--workspace", str(ws), "--harness", "mcp", "--env-file", str(missing)]
    )
    assert result.exit_code == 0, result.stdout
    assert "env file not found" in result.stdout
    entry = json.loads((ws / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["nexus-scholar"]
    assert "env" not in entry


def test_setup_mcp_refuses_directory_as_target(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_MCP_CONFIG_HOME", str(tmp_path / "cfg"))
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".mcp.json").mkdir()
    result = runner.invoke(app, ["setup-mcp", "--workspace", str(ws), "--harness", "mcp"])
    assert result.exit_code == 1
    assert "directory" in result.stdout.lower()
    assert result.stdout.count("Traceback") == 0