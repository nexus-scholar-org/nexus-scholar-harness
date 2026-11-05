"""Serve a prepared copy of the golden workspace for live UI checks (M1b-1).

Copies ``workspaces/golden-uav-30`` to ``--dest`` (which must not be under
``workspaces/``), writes a local operator context, prepares the screening
batches, and runs the Harness Console on loopback. The golden workspace itself
is never modified. The console token comes from ``NEXUS_CONSOLE_TOKEN``, so the
research UI's proxy, started with the same variable, can reach it.

``--with-drafts N`` stores N sandbox agent drafts (driver ``sandbox``, model
``sandbox-fixture``: test data, never a real agent run) so the UI's reveal can
be exercised. ``--terminal-log`` copies the console's terminal output to a
file, which is where the approval code appears (it is never sent over HTTP).

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


def add_drafts(ws: Path, count: int) -> list[str]:
    """Store `count` sandbox drafts: every inclusion yes, every exclusion no."""
    from scholar_harness.screening import events as ev
    from scholar_harness.screening import proposals as pr

    context = ev.load_context(ws)
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    criteria = pr.Criteria.from_protocol(protocol)
    papers = {}
    for index in context.batches:
        batch = json.loads((ws / "literature" / "screening" / f"batch_{index:03d}.json").read_text(encoding="utf-8"))
        papers.update({p["workspace_id"]: p for p in batch["papers"]})
    studies = [s for index in sorted(context.batches) for s in context.batches[index].candidates][:count]
    for study in studies:
        paper = papers[study]
        quote = pr.record_text(paper.get("title"), paper.get("abstract"))[:40]
        output = {
            "criteria": [
                {"id": c, "answer": "yes" if c in criteria.inclusion else "no", "evidence": {"text": quote, "start": 0, "end": len(quote)}}
                for c in criteria.all
            ],
            "cannot_decide": False,
        }
        pr.submit_proposal(
            ws, study_id=study, title=paper.get("title"), abstract=paper.get("abstract"), output=output,
            protocol=protocol, protocol_fingerprint=context.protocol_fingerprint,
            provenance={"task_version": "sandbox", "model": "sandbox-fixture", "prompt_sha256": "sha256:" + "0" * 64, "driver": "sandbox"},
            created_at="2026-11-05T08:00:00Z",
        )
    return studies


class _Tee:
    """Write the console's terminal output to the terminal and a log file."""

    def __init__(self, stream, path: Path) -> None:
        self._stream = stream
        self._file = path.open("a", encoding="utf-8")

    def write(self, text: str) -> int:
        self._file.write(text)
        self._file.flush()
        return self._stream.write(text)

    def flush(self) -> None:
        self._file.flush()
        self._stream.flush()

    def __getattr__(self, name: str):
        return getattr(self._stream, name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dest", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--with-drafts", type=int, default=0)
    parser.add_argument("--terminal-log", type=Path)
    args = parser.parse_args(argv)

    token = os.environ.get("NEXUS_CONSOLE_TOKEN", "").strip()
    if not token and not args.build_only:
        print("NEXUS_CONSOLE_TOKEN must be set", file=sys.stderr)
        return 2
    ws = build(args.dest, batch_size=args.batch_size)
    if args.with_drafts:
        add_drafts(ws, args.with_drafts)
    if args.terminal_log:
        args.terminal_log.parent.mkdir(parents=True, exist_ok=True)
        args.terminal_log.write_text("", encoding="utf-8")
        sys.stdout = _Tee(sys.stdout, args.terminal_log)
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
