"""``nexus-scholar log``: append-only audit-contract operations as a CLI (P7.6).

Standalone workspaces (``nexus-scholar init``'d anywhere, no repo checkout)
keep the workspace-manager audit contract -- ``audit/journal.jsonl`` appends +
an ``INDEX.md`` refresh -- without reaching a repo-relative ``scripts/`` path.

The workspace-manager ``log_event.py`` script is located and loaded in-process
through P7.3's wheel-portable skills resolver (``NEXUS_SKILLS_SRC`` env
override -> wheel-bundled ``scholar_harness_data/skills`` -> repo
``.agents/skills``; see :func:`scholar_harness.inception.resolve_skills_root`),
and its canonical event schema / workspace-resolution preconditions are used
unchanged.  This module is only the CLI surface: ``event``/``batch``
orchestration + a ``sync-index`` shortcut.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from .inception import _load_log_module

console = Console()


class _NotWorkspaceError(Exception):
    """Raised when a target cannot be resolved to a Nexus Scholar workspace."""


# ---------------------------------------------------------------------------
# Resolver: in-process log_event.py + workspace-target resolution
# ---------------------------------------------------------------------------


def _resolve_log_module():
    """Load ``workspace-manager/scripts/log_event.py`` in-process.

    Thin wrapper over P7.3's cached :func:`scholar_harness.inception._load_log_module`,
    which already walks the wheel-portable source roots: ``NEXUS_SKILLS_SRC``
    env override, the wheel-bundled ``scholar_harness_data/skills`` tree
    (``uvx --from nexus-scholar`` with no repo checkout), then the repository
    ``.agents/skills``.  Returns ``None`` when the script is unreachable.
    """
    module = _load_log_module()
    if module is None or not (
        hasattr(module, "log_project_event") and hasattr(module, "refresh_index_md")
    ):
        return None
    return module


def _resolve_workspace(project_path_or_slug: str | Path) -> Path:
    """Resolve a workspace by path or slug -- mirror of ``log_event.py`` L171-179.

    The script uses the given path directly when it is a directory holding
    ``project.json``; otherwise it falls back to the CWD-relative
    ``workspaces/<slug>`` candidate (restricted, as in the script, to an
    existing directory).  Per the P7.6 contract the slug fallback applies only
    when the input is *not* an existing directory (a non-workspace dir path is
    refused rather than silently given an ``audit/`` ledger -- the single
    deliberate divergence from the script, which would otherwise create one
    inside any plain dir, and on Windows would re-resolve any absolute path
    through its naive ``workspaces/<abs>`` join).
    """
    path = Path(project_path_or_slug)
    if path.is_dir():
        if (path / "project.json").exists():
            return path
        raise _NotWorkspaceError(str(project_path_or_slug))
    candidate = Path("workspaces") / str(project_path_or_slug)
    if candidate.is_dir():
        return candidate
    raise _NotWorkspaceError(str(project_path_or_slug))


def _require_log_module():
    module = _resolve_log_module()
    if module is None:
        console.print(
            "[bold red]\u274c workspace-manager log_event.py unavailable; "
            "install the nexus-scholar wheel, set NEXUS_SKILLS_SRC, or run "
            "from the repo checkout.[/bold red]"
        )
        raise typer.Exit(1)
    return module


def _require_workspace(project_path_or_slug: str) -> Path:
    try:
        return _resolve_workspace(project_path_or_slug)
    except _NotWorkspaceError:
        console.print(
            f"[bold red]\u274c Not a Nexus Scholar workspace: "
            f"{project_path_or_slug!r} (need a directory holding project.json, "
            "or a slug under a workspaces/ parent).[/bold red]"
        )
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Event-command value shaping (parity with log_event.py's argparse `nargs="*"`)
# ---------------------------------------------------------------------------


def _expand_tokens(values: list[str] | None) -> list[str]:
    """Normalise ``--inputs``/``--outputs`` values (repeatable + space-separated)."""
    return [token for raw in values or [] for token in raw.split()]


def _parse_kv(pairs: list[str] | None, flag: str) -> dict[str, Any]:
    """Parse ``--param`` / ``--metric`` ``KEY=VALUE`` pairs into a dict."""
    out: dict[str, Any] = {}
    for raw in pairs or []:
        key, sep, value = raw.partition("=")
        key = key.strip()
        if not sep or not key:
            console.print(
                f"[bold red]\u274c {flag} must be KEY=VALUE (got {raw!r})[/bold red]"
            )
            raise typer.Exit(1)
        out[key] = value
    return out


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def run_log_event(
    workspace: str,
    *,
    action: str,
    agent: str = "agent",
    description: str = "",
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    status: str = "SUCCESS",
    parameters: list[str] | None = None,
    metrics: list[str] | None = None,
) -> None:
    """Append a single canonical audit event and refresh ``INDEX.md``.

    Defers to workspace-manager's ``log_project_event`` verbatim: record
    ``action`` uppercased, ``event_id`` ``EVT-<ts>-<hex6>``, ISO ``timestamp``,
    ``status`` uppercased; bumps ``project.json.updated_at`` (+ stats keys
    already present in ``manifest["stats"]``); refreshes ``INDEX.md``; and
    prints the standard ``Logged event [...] -> path`` line.
    """
    module = _require_log_module()
    target = _require_workspace(workspace)
    module.log_project_event(
        target,
        action,
        agent,
        description,
        inputs=_expand_tokens(inputs),
        outputs=_expand_tokens(outputs),
        parameters=_parse_kv(parameters, "--param"),
        metrics=_parse_kv(metrics, "--metric"),
        status=status,
    )


def _load_batch_records(events_file: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Parse a JSONL events file into validated records + per-line error strings.

    Lenient-skip semantics (documented in ``log batch --help``): a malformed
    JSON line or a record missing ``action``/``description`` is skipped with an
    error line and never written; the remaining valid records still append.
    Only fully validated records are returned, so the journal is never given
    partial/corrupt data.
    """
    if not events_file.is_file():
        raise FileNotFoundError(f"Events file not found: {events_file}")
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    with open(events_file, "r", encoding="utf-8") as fh:
        for line_num, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_num}: malformed JSON ({exc.msg})")
                continue
            action = record.get("action")
            description = record.get("description")
            if not isinstance(action, str) or not action.strip():
                errors.append(f"line {line_num}: missing required 'action'")
                continue
            if not isinstance(description, str):
                errors.append(f"line {line_num}: missing required 'description'")
                continue
            records.append(
                {
                    "action": action,
                    "agent_or_tool": record.get(
                        "agent_or_tool", record.get("agent", "agent")
                    ),
                    "description": description,
                    "inputs": record.get("inputs", []),
                    "outputs": record.get("outputs", []),
                    "parameters": record.get("parameters", {}),
                    "metrics": record.get("metrics", {}),
                    "status": record.get("status", "SUCCESS"),
                }
            )
    return records, errors


def run_log_batch(workspace: str, events_file: Path) -> None:
    """Append a validated JSONL batch to the journal and refresh ``INDEX.md``.

    Prints one ``Logged event [...]`` line per appended record plus a summary.
    Lenient-skip policy: records that are malformed JSON or lack ``action`` /
    ``description`` are skipped with an error line; validated records still
    append.  Exit code 1 (``typer.Exit``) when any record was skipped or failed
    to write; the journal itself always stays JSON-parse-clean.
    """
    module = _require_log_module()
    target = _require_workspace(workspace)
    try:
        records, errors = _load_batch_records(events_file)
    except FileNotFoundError as exc:
        console.print(f"[bold red]\u274c {exc}[/bold red]")
        raise typer.Exit(1)

    if not records and not errors:
        console.print(
            "[bold red]\u274c No events found in file (empty or all-blank lines): "
            f"{events_file}[/bold red]"
        )
        raise typer.Exit(1)

    for error in errors:
        print(f"\u26a0  Skipping {error}", file=sys.stderr)

    write_failures = 0
    for index, record in enumerate(records, 1):
        try:
            module.log_project_event(target, **record)
        except Exception as exc:  # noqa: BLE001 - one record must not kill the batch
            write_failures += 1
            print(f"\u274c Failed to write event {index}: {exc}", file=sys.stderr)

    logged = len(records) - write_failures
    summary = (
        f"Logged {logged} event(s) from {events_file.name}; "
        f"{len(errors)} record error(s), {write_failures} write failure(s); "
        "INDEX.md refreshed"
    )
    if errors or write_failures:
        console.print(f"[bold yellow]\u26a0  Partial completion -- {summary}[/bold yellow]")
        raise typer.Exit(1)
    console.print(f"[bold green]\u2705 {summary}[/bold green]")


def run_sync_index(workspace: str) -> None:
    """Regenerate ``INDEX.md`` from the workspace state; appends no journal event."""
    module = _require_log_module()
    target = _require_workspace(workspace)
    index_path = module.refresh_index_md(target)
    console.print(f"[bold green]\u2705 Refreshed INDEX.md -> {index_path}[/bold green]")