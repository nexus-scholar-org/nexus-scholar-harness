"""Serve a prepared copy of the golden workspace for live UI checks (M1b-1).

Copies ``workspaces/golden-uav-30`` to ``--dest`` (which must not be under
``workspaces/``), writes a local operator context, prepares the screening
batches, and runs the Harness Console on loopback. The golden workspace itself
is never modified. The console token comes from ``NEXUS_CONSOLE_TOKEN``, so the
research UI's proxy, started with the same variable, can reach it.

Usage::

    NEXUS_CONSOLE_TOKEN=dev uv run python scripts/golden_screening_sandbox.py --dest <dir> [--port 8765]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "workspaces" / "golden-uav-30"


def build(dest: Path, *, batch_size: int) -> Path:
    from scholar_harness.screening.batcher import cmd_prepare

    dest = dest.resolve()
    if (ROOT / "workspaces").resolve() in (dest, *dest.parents):
        raise SystemExit(f"refusing to build the sandbox inside workspaces/: {dest}")
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(GOLDEN, dest)
    context = dest / "literature" / "screening" / "operator_context.json"
    context.parent.mkdir(parents=True, exist_ok=True)
    context.write_text(
        json.dumps({"schema": "harness-operator-context-v1", "operator_identity": "sandbox-researcher"}),
        encoding="utf-8",
    )
    cmd_prepare(dest, batch_size=batch_size)
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dest", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args(argv)

    token = os.environ.get("NEXUS_CONSOLE_TOKEN", "").strip()
    if not token and not args.build_only:
        print("NEXUS_CONSOLE_TOKEN must be set", file=sys.stderr)
        return 2
    ws = build(args.dest, batch_size=args.batch_size)
    print(f"sandbox ready: {ws}", flush=True)
    if args.build_only:
        return 0

    import uvicorn

    from scholar_harness.console import create_app
    from scholar_harness.console.serve import LOOPBACK_HOSTS

    uvicorn.run(create_app(ws, token=token, trusted_hosts=LOOPBACK_HOSTS), host="127.0.0.1", port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
