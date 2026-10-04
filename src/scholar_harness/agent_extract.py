#!/usr/bin/env python3
"""agent_extract.py -- publish the Contract v1 document manifest and index it.

This is the runtime CLI half of the extraction acceptance link. Stage 5 wrote
``extracted/<stem>.md`` and Stage 6 indexes *accepted* documents, but between the
two nothing published the ``document_manifest`` Stage 6 inherits both of its
identity limbs from, so an extracted workspace reported ``FAILED`` at indexing.

The commands here do not implement acceptance. They call
:mod:`scholar_harness.extraction_producer`, which builds the candidate from
recorded workspace state and hands it to the frozen acceptance gate
(:mod:`scholar_harness.extraction_adapter` -> ``accept_artifact``).

Workflow::

    python src/scholar_harness/agent_extract.py status  <workspace>
    python src/scholar_harness/agent_extract.py publish <workspace> --index
    python src/scholar_harness/agent_extract.py index   <workspace>

Every command is read-mostly and fail-closed: a refusal publishes no manifest, no
registry entry, and no index, prints the typed refusal code, and exits non-zero.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Force UTF-8 on Windows to prevent Rich/print unicodes from crashing on OEM code pages
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError, OSError):  # non-reconfigurable stream
        pass

# Ensure src root is in sys.path for standalone script or dynamic module loads. The
# package-absolute import below therefore always resolves; there is no relative
# fallback to keep, because running this file as a script leaves no package context.
_SRC_ROOT = Path(__file__).resolve().parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from scholar_harness.extraction_producer import (
    PublicationRefused,
    index_accepted_documents,
    publication_status,
    publish_document_manifest,
)

EXIT_OK = 0
EXIT_REFUSED = 1


def _emit(payload: dict, as_json: bool) -> None:
    """Write one machine-readable JSON document to stdout, and nothing else.

    Plain ``print``, never a Rich renderer: the typer entry point shares a
    ``Console(force_terminal=True)`` for its human tables, which emits ANSI regardless of
    TTY, ``NO_COLOR`` or ``TERM=dumb`` and makes a refusal banner unparseable. The two
    entry points must produce byte-identical documents for the same payload, so this
    mirrors ``cli._emit_json`` exactly, ``sort_keys`` included.
    """

    if as_json:
        print(
            json.dumps(
                payload, indent=2, sort_keys=True, ensure_ascii=False, default=str
            )
        )
        return
    for key, value in payload.items():
        print(f"{key}: {value}")


def _cmd_status(workspace: Path, as_json: bool) -> int:
    report = publication_status(workspace)
    if as_json:
        _emit(report, as_json)
    else:
        recordings = report.get("recordings") or {}
        print(f"workspace:        {report['workspace']}")
        print(f"extracted files:  {len(report['extracted_files'])}")
        for path in report["extracted_files"]:
            print(f"  - {path}")
        refusal = recordings.get("refusal")
        if refusal:
            print(f"ready to publish: no ({refusal['code']})")
            print(f"  {refusal['message']}")
        else:
            print("ready to publish: yes")
            print(f"  workspace_id:           {recordings['workspace_id']}")
            print(f"  screening run:          {recordings['screening_run_id']}")
            print(
                f"  accepted manifests:     {recordings['document_manifests'] or 'none'}"
            )
    return EXIT_OK


def _cmd_publish(workspace: Path, as_json: bool, run_index: bool) -> int:
    outcome = publish_document_manifest(workspace)
    payload: dict = {"publication": outcome.as_dict()}
    if run_index:
        if outcome.accepted:
            try:
                payload["indexing"] = index_accepted_documents(workspace)
            except PublicationRefused as refusal:
                payload["indexing"] = {"refusal": refusal.as_dict()}
                payload["indexing_refused"] = True
        else:
            # Nothing was accepted, so there is nothing to index. Running Stage 6 here
            # would only record a refusal over an empty run.
            payload["indexing"] = {"skipped": "no accepted document manifest"}
    _emit(payload, as_json)
    if not outcome.accepted:
        return EXIT_REFUSED
    indexing = payload.get("indexing") or {}
    if indexing.get("status") not in {"SUCCESS", "PARTIAL", None}:
        return EXIT_REFUSED
    if indexing.get("refusal") or indexing.get("indexing_refused"):
        return EXIT_REFUSED
    return EXIT_OK


def _cmd_index(workspace: Path, as_json: bool) -> int:
    try:
        result = index_accepted_documents(workspace)
    except PublicationRefused as refusal:
        _emit({"indexing_refused": refusal.as_dict()}, as_json)
        return EXIT_REFUSED
    _emit(result, as_json)
    return EXIT_OK if result.get("status") in {"SUCCESS", "PARTIAL"} else EXIT_REFUSED


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Publish the Contract v1 document manifest for a workspace's real Stage 5 "
            "extraction output, then hand it to Stage 6.\n\n"
            "The candidate is built from recorded workspace state only "
            "(project.json identity, protocol.json fingerprint, the accepted corpus "
            "snapshot and its accepted screening decisions) and is accepted by the "
            "frozen acceptance gate. A refusal publishes nothing and exits 1."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def _add(name: str, help_text: str) -> argparse.ArgumentParser:
        item = sub.add_parser(name, help=help_text)
        item.add_argument("workspace", help="Path to workspace directory")
        item.add_argument(
            "--json", action="store_true", help="Emit machine-readable JSON"
        )
        return item

    _add("status", "Report recorded state without publishing or indexing.")
    p_publish = _add("publish", "Publish the accepted document manifest.")
    p_publish.add_argument(
        "--index",
        action="store_true",
        help="Run Stage 6 over the accepted manifest after publication",
    )
    _add("index", "Run Stage 6 over the already-accepted manifest.")

    args = parser.parse_args(argv)
    workspace_dir = Path(args.workspace).resolve()

    if args.command == "status":
        return _cmd_status(workspace_dir, args.json)
    if args.command == "publish":
        return _cmd_publish(workspace_dir, args.json, args.index)
    return _cmd_index(workspace_dir, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
