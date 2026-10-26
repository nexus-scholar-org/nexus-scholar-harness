"""CLI for ``python -m scholar_harness.contracts.envelope`` (spec 02 §8)."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .api import EnvelopeRefusalError, diff, find_roles_dir, validate
from .registry import RefusalCode, render_refusals_doc


def _prepare(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scholar_harness.contracts.envelope",
        description="Validate, verify, or diff Envelope@1 transport records.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    validate_parser = commands.add_parser("validate", help="validate one envelope")
    validate_parser.add_argument("path")
    validate_parser.add_argument(
        "--verify-parents",
        action="store_true",
        help="also verify parents/inputs content hashes against --root",
    )
    validate_parser.add_argument("--root", default=None)
    validate_parser.add_argument("--roles-dir", default=None)

    diff_parser = commands.add_parser("diff", help="diff two envelopes")
    diff_parser.add_argument("a")
    diff_parser.add_argument("b")
    diff_parser.add_argument("--roles-dir", default=None)

    commands.add_parser(
        "render-refusals", help="print the generated refusal-registry markdown"
    )

    args = parser.parse_args(argv)
    if args.command == "render-refusals":
        sys.stdout.write(render_refusals_doc())
        return 0
    try:
        if args.command == "validate":
            root = Path(args.root) if args.root else (Path.cwd())
            if not args.roles_dir and find_roles_dir(Path.cwd()) is None:
                # Reviewer repair (finding F1, cycle 2): the CLI must never
                # silently degenerate into the D11 library contract
                # (``roles_dir=None`` skips the role-record cross-checks,
                # including schema-name authority).
                raise EnvelopeRefusalError(
                    RefusalCode.BLOCKED_INPUT,
                    "no roles/ directory found from CWD: role-record "
                    "cross-checks (incl. schema-name authority, D11) would be "
                    "silently skipped — pass --roles-dir",
                )
            roles_dir = (
                Path(args.roles_dir) if args.roles_dir else find_roles_dir(Path.cwd())
            )
            envelope = validate(
                Path(args.path),
                verify_parents=args.verify_parents,
                root=root,
                roles_dir=roles_dir,
            )
            print(
                json.dumps(
                    {
                        "result": "accepted",
                        "envelope_id": envelope.envelope_id,
                        "status": str(envelope.status),
                        "role": f"{envelope.role}@{envelope.role_version}",
                    }
                )
            )
            return 0
        report = diff(Path(args.a), Path(args.b)).as_dict()
        print(_prepare(report))
        return 0
    except EnvelopeRefusalError as error:
        print(
            json.dumps(
                {
                    "result": "rejected",
                    "status": str(error.refusal_code),
                    "refusal_code": str(error.refusal_code),
                    "detail": error.detail,
                }
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
