#!/usr/bin/env python3
"""Nexus Scholar Plugin Installer.

Installs external Nexus Scholar toolkits into the unified harness environment.
Supports local dev checkouts (editable mode) with automatic fallback to remote Git repos.

Design notes:
- Uses `uv pip install` (PEP 508 / pip-style), NOT `uv sync`. `uv sync` reads each
  kit's `[tool.uv.sources]`, which contain relative paths that only work inside a
  monorepo checkout. `uv pip` ignores those and installs from the resolution we give it.
- Kits are installed in dependency order so that `scholar-search-kit` (the base) is
  present before dependent kits (`bib`, `graph`, `rag`, `agent`) resolve their deps.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _reconfigure_encoding_for_utf8() -> None:
    """Reconfigure stdout/stderr for UTF-8 to support emojis on Windows.
    
    Windows console defaults to cp1252/cp850, which doesn't support emojis.
    This function reconfigures streams to use UTF-8, with fallbacks for
    compatibility with different Python versions and environments.
    """
    if sys.platform != "win32":
        return

    # Strategy 1: Try reconfigure() method (Python 3.7+)
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError, RuntimeError):
                pass

    # Strategy 2: Wrap streams with UTF-8 codec if still needed
    if sys.stdout.encoding and "utf" not in sys.stdout.encoding.lower():
        try:
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding="utf-8",
                errors="replace",
                write_through=True,
            )
        except (AttributeError, ValueError):
            pass

    if sys.stderr.encoding and "utf" not in sys.stderr.encoding.lower():
        try:
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer,
                encoding="utf-8",
                errors="replace",
                write_through=True,
            )
        except (AttributeError, ValueError):
            pass


# Configure encoding early, before any output
_reconfigure_encoding_for_utf8()

# Default path to plugin manifest relative to repository root
DEFAULT_MANIFEST_PATH = Path(".agents/plugins/nexus-scholar/plugins.json")

# Install order: base kit first, then dependents. `scholar-agent-kit` depends on all others.
INSTALL_ORDER = [
    "scholar-search-kit",
    "scholar-pdf-kit",
    "scholar-bib-kit",
    "scholar-graph-kit",
    "scholar-rag-kit",
    "scholar-agent-kit",
]


def load_registry(manifest_path: Path) -> list[dict[str, Any]]:
    """Loads plugin list from JSON registry."""
    if not manifest_path.exists():
        print(f"❌ Error: Plugin registry manifest not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    plugins = data.get("plugins", [])
    if not plugins:
        print(f"⚠️ Warning: No plugins defined in {manifest_path}", file=sys.stderr)
    return plugins


def resolve_local_path(
    plugin_name: str,
    custom_dev_path: Path | None = None,
    repo_root: Path = Path("."),
) -> Path | None:
    """Searches for a local clone of the plugin to enable editable install."""
    candidate_paths: list[Path] = []

    if custom_dev_path:
        candidate_paths.append(custom_dev_path / plugin_name)

    env_dev_path = os.environ.get("NEXUS_PLUGIN_PATH")
    if env_dev_path:
        candidate_paths.append(Path(env_dev_path) / plugin_name)

    # Common conventions:
    # 1. tools/<plugin_name> inside harness
    # 2. ../<plugin_name> (side-by-side clone)
    # 3. ../../<plugin_name>
    candidate_paths.extend([
        repo_root / "tools" / plugin_name,
        repo_root.parent / plugin_name,
        repo_root.parent.parent / plugin_name,
    ])

    for path in candidate_paths:
        if path.exists() and (path / "pyproject.toml").exists():
            return path.resolve()

    return None


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Runs a shell command and streams output."""
    return subprocess.run(cmd, check=check)


def clean_legacy_venvs(repo_root: Path) -> None:
    """Cleans up isolated .venv directories in tools/ to avoid duplicate disk usage."""
    tools_dir = repo_root / "tools"
    if not tools_dir.exists():
        return

    print("🧹 Cleaning legacy per-tool virtual environments (.venv)...")
    cleaned = 0
    for venv_path in tools_dir.glob("*/.venv"):
        if venv_path.is_dir():
            print(f"  Removing: {venv_path}")
            shutil.rmtree(venv_path, ignore_errors=True)
            cleaned += 1

    if cleaned:
        print(f"✨ Removed {cleaned} duplicate virtual environment(s).")
    else:
        print("ℹ️ No duplicate .venv folders found.")


def install_plugin(
    plugin: dict[str, Any],
    dev_path: Path | None,
    git_only: bool,
    local_only: bool,
    upgrade: bool,
    repo_root: Path,
) -> bool:
    """Installs a single plugin using `uv pip`."""
    name = plugin["name"]
    repo_url = plugin["repo"]
    default_rev = plugin.get("default_rev", "main")
    extras = plugin.get("extras", [])
    extras_suffix = f"[{','.join(extras)}]" if extras else ""

    print(f"\n📦 Processing plugin: {name}")

    local_path = None
    if not git_only:
        local_path = resolve_local_path(name, custom_dev_path=dev_path, repo_root=repo_root)

    cmd = ["uv", "pip", "install"]
    if upgrade:
        cmd.append("--upgrade")

    if local_path:
        print(f"  📍 Found local checkout at: {local_path}")
        print(f"  🛠️  Installing in editable mode (-e)...")
        target = f"{local_path}{extras_suffix}"
        cmd.extend(["-e", target])
    else:
        if local_only:
            print(f"  ❌ Skipped: No local clone found and --local-only specified.")
            return False

        print(f"  🌐 Installing from Git repository: {repo_url} (branch/tag: {default_rev})")
        # Format: git+https://github.com/org/repo.git@rev#egg=name[extras]
        git_target = f"git+{repo_url}@{default_rev}"
        if extras:
            git_target = f"{git_target}#egg={name}{extras_suffix}"
        cmd.append(git_target)

    try:
        res = run_command(cmd, check=False)
        if res.returncode == 0:
            print(f"  ✅ Successfully installed {name}")
            return True
        else:
            print(f"  ❌ Installation failed for {name} (exit code: {res.returncode})", file=sys.stderr)
            return False
    except Exception as e:
        print(f"  ❌ Error during install: {e}", file=sys.stderr)
        return False


def verify_installation(plugins: list[dict[str, Any]]) -> dict[str, bool]:
    """Runs --help on each console_script to verify functionality."""
    print("\n🔍 Verifying installed plugin console scripts in shared environment...")
    results: dict[str, bool] = {}

    for plugin in plugins:
        name = plugin["name"]
        script = plugin.get("console_script")
        if not script:
            continue

        cmd = ["uv", "run", script, "--help"]
        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                print(f"  ✅ {script:<16} (from {name}) -> OK")
                results[name] = True
            else:
                print(f"  ❌ {script:<16} (from {name}) -> FAILED (exit {res.returncode})")
                results[name] = False
        except FileNotFoundError:
            print(f"  ❌ {script:<16} (from {name}) -> COMMAND NOT FOUND")
            results[name] = False

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Unified Plugin Installer for Nexus Scholar Harness."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help=f"Path to plugins.json (default: {DEFAULT_MANIFEST_PATH})",
    )
    parser.add_argument(
        "--plugin", "-p",
        type=str,
        help="Install only a specific plugin by name (e.g. scholar-search-kit)",
    )
    parser.add_argument(
        "--dev-path", "-d",
        type=Path,
        help="Directory where kit source repos are located locally",
    )
    parser.add_argument(
        "--git-only",
        action="store_true",
        help="Force installation from remote Git repositories, ignoring local checkouts",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Only install from local checkouts; do not fetch from Git",
    )
    parser.add_argument(
        "--upgrade", "-U",
        action="store_true",
        help="Upgrade installed packages",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove legacy per-tool .venv directories in tools/",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        default=True,
        help="Verify installed tools after installation (default: True)",
    )
    parser.add_argument(
        "--no-verify",
        action="store_false",
        dest="verify",
        help="Skip verification phase",
    )

    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parent.parent

    # Clean legacy per-tool venvs if requested
    if args.clean:
        clean_legacy_venvs(repo_root)

    manifest_path = (repo_root / args.manifest) if not args.manifest.is_absolute() else args.manifest
    plugins = load_registry(manifest_path)

    if args.plugin:
        plugins = [
            p for p in plugins
            if p["name"] == args.plugin or p.get("console_script") == args.plugin
        ]
        if not plugins:
            print(f"❌ Plugin '{args.plugin}' not found in registry {manifest_path}", file=sys.stderr)
            sys.exit(1)
    else:
        # Order plugins by dependency order for reliable resolution.
        plugins.sort(key=lambda p: INSTALL_ORDER.index(p["name"]) if p["name"] in INSTALL_ORDER else 999)

    print(f"🚀 Initializing installation of {len(plugins)} Nexus Scholar plugin(s)...")

    # Ensure root virtual environment is present
    venv_dir = repo_root / ".venv"
    if not venv_dir.exists():
        print("🔧 Creating shared root virtual environment (.venv)...")
        run_command(["uv", "venv", str(venv_dir)])

    success_count = 0
    for p in plugins:
        if install_plugin(
            plugin=p,
            dev_path=args.dev_path,
            git_only=args.git_only,
            local_only=args.local_only,
            upgrade=args.upgrade,
            repo_root=repo_root,
        ):
            success_count += 1

    print(f"\n📊 Summary: Installed {success_count}/{len(plugins)} plugin(s).")

    if args.verify and success_count > 0:
        verification = verify_installation(plugins)
        failed = [name for name, ok in verification.items() if not ok]
        if failed:
            print(f"\n⚠️ The following plugins failed verification: {', '.join(failed)}", file=sys.stderr)
            sys.exit(1)

    print("\n🎉 Harness environment ready! All plugins available via `uv run <command>`.")


if __name__ == "__main__":
    main()