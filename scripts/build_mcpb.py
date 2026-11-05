"""Build the Claude Desktop Extension (`.mcpb`) for the scholar-agent MCP server.

M5-slim (production plan §5.3, stage 1): the agent experience is the
researcher's own Claude through MCP. The extension carries the `nexus-scholar`
wheel and launches `scholar-agent` from it with `uvx`, on the workspace folder
the researcher picks when installing. It holds no key: provider keys stay in
the OS keychain (`nexus-scholar keys set`), which the server reads at start.

Manifest format: MCPB `manifest_version` 0.4 (the schema shipped with
`@anthropic-ai/mcpb` 2.1.2, `schemas/mcpb-manifest-v0.4.schema.json`).

    uv build --wheel
    python scripts/build_mcpb.py --wheel dist/nexus_scholar-1.0.0-py3-none-any.whl

writes `dist/nexus-scholar-<version>.mcpb` (a zip with `manifest.json`, the
wheel and a short launcher note). `npx @anthropic-ai/mcpb validate
manifest.json` checks the manifest against the published schema.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_VERSION = "0.4"

LAUNCHER = '''"""Launch note for the nexus-scholar extension.

Claude Desktop starts the server from manifest.json's mcp_config:
`uvx --from <this folder>/<wheel> scholar-agent --workspace <your folder>`.
This file exists because the MCPB manifest requires an entry point; running it
does the same thing, for a client that runs the entry point directly.
"""

import os
import subprocess
import sys
from pathlib import Path

here = Path(__file__).resolve().parent.parent
wheel = next(here.glob("nexus_scholar-*.whl"))
sys.exit(subprocess.call(["uvx", "--from", str(wheel), "scholar-agent", *sys.argv[1:]], env=os.environ.copy()))
'''


def manifest(version: str, wheel_name: str) -> dict:
    """The extension manifest; it names no key and no environment secret."""
    return {
        "manifest_version": MANIFEST_VERSION,
        "name": "nexus-scholar",
        "display_name": "Nexus Scholar",
        "version": version,
        "description": "Screen a systematic review with your own Claude: read records and submit draft proposals; you decide in the Nexus Scholar app.",
        "long_description": (
            "Connects Claude to one Nexus Scholar workspace on this computer through the scholar-agent MCP server. "
            "Claude can list records to screen, read one with its criteria, and store a draft proposal; it never records a decision. "
            "Record text reaches Anthropic through your Claude app, under your account's terms. "
            "Retrieval, synthesis, graph, verification and full-text tools are present but parked, not production."
        ),
        "author": {"name": "Nexus Scholar Org", "url": "https://github.com/nexus-scholar-org/nexus-scholar-harness"},
        "homepage": "https://github.com/nexus-scholar-org/nexus-scholar-harness",
        "license": "MIT",
        "server": {
            "type": "python",
            "entry_point": "server/launch.py",
            "mcp_config": {
                "command": "uvx",
                "args": ["--from", f"${{__dirname}}/{wheel_name}", "scholar-agent", "--workspace", "${user_config.workspace}"],
            },
        },
        "user_config": {
            "workspace": {
                "type": "directory",
                "title": "Workspace folder",
                "description": "The Nexus Scholar workspace Claude works in (a folder holding protocol.json).",
                "required": True,
            }
        },
        "compatibility": {"platforms": ["darwin", "win32", "linux"], "runtimes": {"python": ">=3.11"}},
    }


def build(wheel: Path, out_dir: Path) -> Path:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    version = project["version"]
    if not wheel.is_file() or not wheel.name.startswith("nexus_scholar-"):
        raise SystemExit(f"not a nexus-scholar wheel: {wheel}")
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"nexus-scholar-{version}.mcpb"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("manifest.json", json.dumps(manifest(version, wheel.name), indent=2) + "\n")
        bundle.writestr("server/launch.py", LAUNCHER)
        bundle.write(wheel, wheel.name)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--wheel", type=Path, required=True, help="the nexus-scholar wheel to bundle")
    parser.add_argument("--out", type=Path, default=ROOT / "dist", help="output folder (default: dist/)")
    args = parser.parse_args(argv)
    print(build(args.wheel, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
