#!/usr/bin/env python3
"""
agent_screen.py — Agent-in-the-loop PRISMA screening for the scholar-harness.

Re-exports core screening functions from `scholar_harness.screening` and provides
the CLI entry point for agent-driven screening.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Force UTF-8 on Windows to prevent Rich/print unicodes from crashing on OEM code pages
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure src root is in sys.path for standalone script or dynamic module loads
_SRC_ROOT = Path(__file__).resolve().parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

try:
    from scholar_harness.screening.batcher import (
        _build_agent_instructions,
        _load_decisions,
        _rebuild_doc,
        _screening_dir,
        cmd_prepare,
    )
    from scholar_harness.screening.collector import cmd_collect, cmd_status
    from scholar_harness.screening.report import cmd_calibrate_eval, cmd_calibration
except ImportError:
    from .screening.batcher import (  # type: ignore
        _build_agent_instructions,
        _load_decisions,
        _rebuild_doc,
        _screening_dir,
        cmd_prepare,
    )
    from .screening.collector import cmd_collect, cmd_status  # type: ignore
    from .screening.report import cmd_calibrate_eval, cmd_calibration  # type: ignore

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Agent-in-the-loop PRISMA screening.\n"
            "The harness agent IS the LLM — no external API required.\n\n"
            "Workflow:\n"
            "  1. python agent_screen.py calibration <workspace>  (pre-flight bias check)\n"
            "  2. python agent_screen.py prepare <workspace>\n"
            "  3. Ask the agent: 'screen all batches in literature/screening/'\n"
            "  4. python agent_screen.py collect <workspace>"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # calibration
    p_cal = sub.add_parser("calibration", help="Generate a 20-paper pre-flight calibration batch.")
    p_cal.add_argument("workspace", help="Path to workspace directory")
    p_cal.add_argument("--sample-size", "-n", type=int, default=20)
    p_cal.add_argument("--gold-file", help="Path to gold-labeled JSON (optional; uses heuristic if absent)")

    # calibrate-eval
    p_ceval = sub.add_parser("calibrate-eval", help="Evaluate calibration decisions against gold standard.")
    p_ceval.add_argument("workspace", help="Path to workspace directory")

    # prepare
    p_prepare = sub.add_parser("prepare", help="Chunk verified.json into batch files.")
    p_prepare.add_argument("workspace", help="Path to workspace directory")
    p_prepare.add_argument("--batch-size", "-b", type=int, default=20)
    p_prepare.add_argument("--force", action="store_true", help="Overwrite existing batch files")

    # status
    p_status = sub.add_parser("status", help="Show screening progress.")
    p_status.add_argument("workspace", help="Path to workspace directory")

    # collect
    p_collect = sub.add_parser("collect", help="Assemble decision files into final outputs.")
    p_collect.add_argument("workspace", help="Path to workspace directory")

    args = parser.parse_args()
    workspace_dir = Path(args.workspace).resolve()

    if args.command == "calibration":
        cmd_calibration(workspace_dir, sample_size=args.sample_size, gold_file=args.gold_file)
    elif args.command == "calibrate-eval":
        cmd_calibrate_eval(workspace_dir)
    elif args.command == "prepare":
        cmd_prepare(workspace_dir, batch_size=args.batch_size, force=args.force)
    elif args.command == "status":
        cmd_status(workspace_dir)
    elif args.command == "collect":
        cmd_collect(workspace_dir)


if __name__ == "__main__":
    main()

