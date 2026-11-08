"""Gated emit helper for the inception-agent skill (M4a; INC-08, INC-22).

The chat flow writes a workspace through the SAME gated genesis path as the
CLI wizard and the HTTP route (``scholar_harness.inception.emit.emit_workspace``):
scaffold, compile ``intent.json`` -> ``protocol.json`` + ``SCREENING_CRITERIA.md``,
and log GENESIS. A folder that already holds a workspace is refused unless
``--replace`` is given; a workspace with screening decisions or a published
screening also needs ``--discard-screening-binding``.

``--preview`` compiles in memory and prints the fingerprint and the exact
screening-criteria text; it writes nothing. Show that text to the researcher
before emitting.

Usage::

  uv run python .agents/skills/inception-agent/scripts/emit_protocol.py \\
      --intent <intent.json> (--root <repo root> | --dir <workspace folder>) \\
      [--recon-context <recon_context.json>] [--preview] \\
      [--replace] [--discard-screening-binding]

Prints one JSON object. Exit codes: 0 ok, 2 bad invocation or invalid intent,
3 refused by the overwrite guard (``code`` is WORKSPACE_EXISTS or SCREENING_BOUND).
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from pathlib import Path

from scholar_harness.inception.emit import GenesisRefused, emit_workspace
from scholar_harness.inception.genesis import compile_intent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--intent", required=True)
    where = parser.add_mutually_exclusive_group(required=True)
    where.add_argument("--root", help="repository root; the workspace is <root>/workspaces/<slug>")
    where.add_argument("--dir", help="write into this folder (nexus-scholar init layout)")
    parser.add_argument("--recon-context")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--discard-screening-binding", action="store_true")
    args = parser.parse_args(argv)

    try:
        intent = json.loads(Path(args.intent).read_text(encoding="utf-8"))
        recon = json.loads(Path(args.recon_context).read_text(encoding="utf-8")) if args.recon_context else None
        if args.preview:
            out = compile_intent(intent)
            print(json.dumps({
                "status": "PREVIEW",
                "protocol_fingerprint": out["protocol_fingerprint"],
                "screening_criteria": out["criteria_text"],
                "written": [],
            }, indent=2, ensure_ascii=False))
            return 0
        with contextlib.redirect_stdout(sys.stderr):  # stdout carries only the JSON result
            result = emit_workspace(
                intent,
                root=Path(args.root) if args.root else None,
                target_dir=Path(args.dir) if args.dir else None,
                replace=args.replace,
                discard_screening_binding=args.discard_screening_binding,
                recon_context=recon,
            )
    except GenesisRefused as exc:
        print(json.dumps({"status": "REFUSED", "code": exc.code, "message": exc.message, "details": exc.details}, indent=2))
        return 3
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        return 2
    print(json.dumps({"status": "SUCCESS", **result}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
