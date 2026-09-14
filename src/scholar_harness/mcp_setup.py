"""``nexus-scholar setup-mcp``: wire the ``scholar-agent`` MCP server into
harness-specific config files (P7.4).

Replaces the documented copy-paste Tier-3 snippets with a single command that
merges **only** the ``nexus-scholar`` key into each target's ``mcpServers``
map (never clobbering foreign entries), bakes the **absolute** workspace path
into ``--workspace`` (``${workspaceFolder}`` doesn't expand in Claude Desktop
or a terminal-launched server), and optionally passes ``SCHOLAR_*`` /
``NEXUS_*`` / provider API keys through an ``env:`` block.  Config roots are
CWD-independent and hermetic via the ``NEXUS_MCP_CONFIG_HOME`` override (the
``NEXUS_RECON_ROOT`` pattern); env values are never echoed anywhere.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

console = Console()

HARNESSES = ("claude", "cursor", "vscode", "dsh", "mcp")
# ``all`` expands to every file-backed target plus the printed DSH manual.
ALL_TARGETS = ("claude", "cursor", "vscode", "mcp", "dsh")

# Targets whose config schema supports a per-server ``env:`` block.
ENV_SUPPORTING = ("claude", "cursor", "mcp")

# Keys picked out of the env file for passthrough; anything else is skipped.
MODEL_KEY_EXACTS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY")
ENV_PREFIXES = ("SCHOLAR_", "NEXUS_")
# Setup-time control only — the MCP server never reads these; don't forward them
# (NEXUS_MCP_WORKSPACE would otherwise be a no-op, since the server always
# derives its workspace from --workspace).
EXCLUDED_KEYS = ("NEXUS_MCP_CONFIG_HOME", "NEXUS_MCP_WORKSPACE")

DSH_SNIPPET = (
    "DSH Settings → MCP Servers → Add: command `uvx`, args "
    '`["--from", "nexus-scholar", "scholar-agent", "--workspace", "."]`'
)


def build_mcp_entry(workspace: Path) -> dict[str, Any]:
    """The ``nexus-scholar`` server entry shared by ``init`` and ``setup-mcp``.

    The absolute, baked-in workspace path is a P7.1 hard requirement:
    ``${workspaceFolder}`` only expands in Cursor/Windsurf/VS Code, not in
    Claude Desktop or a terminal-launched MCP server.
    """
    ws = workspace.resolve()
    return {
        "command": "uvx",
        "args": [
            "--from",
            "nexus-scholar",
            "scholar-agent",
            "--workspace",
            str(ws),
        ],
    }


def _config_dir(harness: str, workspace: Path) -> Path:
    """Base config directory for a harness target (P7.4).

    ``NEXUS_MCP_CONFIG_HOME`` overrides the platform config root **first**
    (the Claude Desktop case; mirrors the ``NEXUS_RECON_ROOT`` pattern) so the
    CLI wizard, the MCP server and tests stay CWD-independent and hermetic.
    Without the override the platform defaults apply (Windows ``%APPDATA%``,
    macOS ``~/Library/Application Support``, Linux ``~/.config``); the
    workspace-scoped editor targets resolve under the workspace directory
    itself.
    """
    if harness == "claude":
        override = os.environ.get("NEXUS_MCP_CONFIG_HOME")
        if override:
            return Path(override).expanduser().resolve()
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA") or Path.home())
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path.home() / ".config"
        return base
    return workspace.resolve()


def _target_path(harness: str, workspace: Path) -> Path:
    """On-disk config file for a harness target (``dsh`` has none)."""
    cfg = _config_dir(harness, workspace)
    if harness == "claude":
        return cfg / "Claude" / "claude_desktop_config.json"
    if harness == "cursor":
        return cfg / ".cursor" / "mcp.json"
    if harness == "vscode":
        return cfg / ".vscode" / "mcp.json"
    if harness == "mcp":
        return cfg / ".mcp.json"
    raise ValueError(f"no config file for target {harness!r}")


def _expand_targets(names: list[str]) -> list[str]:
    """Normalise ``--harness`` values (comma/space separated; ``all`` expands).

    Unknown targets are refused with a clean error.  Order follows
    :data:`ALL_TARGETS` when ``all`` appears; duplicates collapse.
    """
    targets: list[str] = []
    for raw in (["all"] if not names else names):
        for token in raw.replace(",", " ").split():
            name = token.strip().lower()
            if not name:
                continue
            if name == "all":
                targets.extend(ALL_TARGETS)
            elif name in HARNESSES:
                targets.append(name)
            else:
                console.print(
                    f"[bold red]\u274c Unknown harness target: {name} "
                    f"(choose from {', '.join(HARNESSES)} or 'all')[/bold red]"
                )
                raise typer.Exit(1)
    return list(dict.fromkeys(targets))


def _read_env_file(path: Path) -> dict[str, str]:
    """Parse a ``.env``-style file into ``{KEY: value}`` (no interpolation).

    ``utf-8-sig`` transparently drops a BOM (Windows Notepad/PowerShell
    ``Set-Content -Encoding utf8`` adds one; otherwise the first key carries a
    ``\\ufeff`` prefix and is skipped by :func:`_select_env_keys`).
    """
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"").strip()
        if key:
            values[key] = value
    return values


def _select_env_keys(values: dict[str, str]) -> dict[str, str]:
    """Keep only the passthrough-approved keys (unknown keys are skipped)."""
    return {
        key: value
        for key, value in values.items()
        if key not in EXCLUDED_KEYS
        and (key in MODEL_KEY_EXACTS or key.startswith(ENV_PREFIXES))
    }


def _load_config(path: Path) -> dict[str, Any]:
    """Best-effort read of an existing config (missing/corrupt → fresh map)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    if not isinstance(data.get("mcpServers"), dict):
        data["mcpServers"] = {}
    return data


def _merge_servers(
    config: dict[str, Any], key: str, entry: dict[str, Any]
) -> dict[str, Any]:
    """Merge ``key → entry`` into ``mcpServers``, preserving other entries."""
    servers = config.get("mcpServers")
    if not isinstance(servers, dict):
        servers = {}
    return {**config, "mcpServers": {**servers, key: entry}}


def _serialize(config: dict[str, Any]) -> bytes:
    return json.dumps(config, indent=2).encode("utf-8")


def _write_target(path: Path, payload: bytes) -> None:
    """Create any missing parent dirs and atomically replace the target."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_bytes(payload)
    os.replace(tmp, path)


def _masked_json(config: dict[str, Any]) -> str:
    """Human-safe dump: ``env`` values redacted as ``***``, keys preserved."""
    masked = json.loads(json.dumps(config))
    servers = masked.get("mcpServers")
    if isinstance(servers, dict):
        for entry in servers.values():
            if isinstance(entry, dict) and isinstance(entry.get("env"), dict):
                entry["env"] = {k: "***" for k in entry["env"]}
    return json.dumps(masked, indent=2)


def _one_liner(name: str, status: str, env_keys: dict[str, str]) -> str:
    """Human one-liner for the status table (env values never echoed)."""
    note = {
        "unchanged": "already wired — no change",
        "updated": "merged nexus-scholar entry (foreign mcpServers preserved)",
        "created": "wired",
    }[status]
    if env_keys:
        keys = ", ".join(sorted(env_keys))
        if name in ENV_SUPPORTING:
            note += f" \u00b7 env passthrough: {keys} (values masked)"
        else:
            note += (
                f" \u00b7 env NOT supported in this config \u2014 export "
                f"{keys} in your environment"
            )
    return note


def run_setup_mcp(
    workspace: Path,
    harness: list[str],
    *,
    dry_run: bool = False,
    env_file: Path | None = None,
) -> None:
    """Execute the P7.4 wiring plan: merge entries, then print the plan table.

    Refuses only a missing workspace (clean ``typer.Exit(1)``).  With
    ``--dry-run`` the exact write plan (path + status + config JSON for new
    files) is printed without touching the filesystem; env values never appear
    in any human output.
    """
    ws = workspace.resolve()
    if not ws.is_dir():
        console.print(f"[bold red]\u274c Workspace directory not found: {ws}[/bold red]")
        raise typer.Exit(1)

    targets = _expand_targets(harness)

    # ``--env-file`` explicit wins; else the workspace's own ``.env``.
    if env_file is None:
        candidate = ws / ".env"
        if candidate.is_file():
            env_file = candidate
    env: dict[str, str] = {}
    if env_file is not None:
        if not env_file.is_file():
            console.print(
                f"[yellow]\u26a0 env file not found ({env_file}); "
                "skipping env passthrough[/yellow]"
            )
        else:
            env = _select_env_keys(_read_env_file(env_file))

    table = Table(
        title="\u2699\ufe0f nexus-scholar MCP wiring",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Target", style="bold white", width=10)
    table.add_column("Path", style="dim")
    table.add_column("Status", style="green", width=11)
    table.add_column("Note", style="white")

    for name in targets:
        if name == "dsh":
            note = DSH_SNIPPET
            if env:
                note += " \u00b7 set SCHOLAR_*/NEXUS_*/provider keys in the DSH server env"
            table.add_row("dsh", "\u2014", "manual", note)
            continue

        path = _target_path(name, ws)
        if path.exists() and path.is_dir():
            console.print(
                f"[bold red]\u274c Target path is a directory, refusing to "
                f"overwrite: {path}[/bold red]"
            )
            raise typer.Exit(1)
        entry = build_mcp_entry(ws)
        if env and name in ENV_SUPPORTING:
            entry = {**entry, "env": dict(env)}
        merged = _merge_servers(_load_config(path), "nexus-scholar", entry)
        payload = _serialize(merged)

        if path.is_file():
            status = "unchanged" if path.read_bytes() == payload else "updated"
        else:
            status = "created"

        if dry_run:
            if status == "created":
                note = _masked_json(merged)
            elif status == "updated":
                note = "would re-merge into existing config"
            else:
                note = "already wired — no change"
        else:
            if status in ("created", "updated"):
                _write_target(path, payload)
            note = _one_liner(name, status, env)

        table.add_row(name, str(path), status, note)

    console.print(table)