"""Command Line Interface for Nexus Scholar Harness."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .audit_log import run_log_batch, run_log_event, run_sync_index
from .doctor import render, run_doctor
from .inception import inception_command, init_command
from .integrations.latex_typst import AcademicTypesettingExporter
from .integrations.obsidian import ObsidianVaultExporter
from .integrations.zotero import ZoteroBridge
from .mcp_setup import run_setup_mcp
from .orchestrator import ResearchOrchestrator

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

app = typer.Typer(
    name="scholar-harness",
    help="Nexus Scholar Harness: Master CLI orchestrating systematic research workflows, MCP servers, and academic ecosystem integrations.",
    add_completion=False,
)
console = Console(force_terminal=True, legacy_windows=False)


def _print_version(value: bool) -> None:
    if value:
        from . import __version__

        typer.echo(f"nexus-scholar {__version__}")
        raise typer.Exit()


@app.callback()
def _main(
    version: bool = typer.Option(  # noqa: B008
        False, "--version", callback=_print_version, is_eager=True, help="Print the version and exit."
    ),
) -> None:
    """Nexus Scholar Harness."""


@app.command("status")
def status(
    workspace: Path = typer.Option(
        Path("."), "--workspace", "-w", help="Path to research workspace directory"
    ),
):
    """Display comprehensive status and pipeline metrics for a research workspace."""
    orchestrator = ResearchOrchestrator(workspace)
    stat = orchestrator.get_status()

    table = Table(
        title=f"🔬 Nexus Scholar Workspace: {stat['title']}",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Pipeline Dimension", style="bold white", width=26)
    table.add_column("Status / Metric Value", style="green", width=40)

    table.add_row("Workspace Directory", stat["workspace"])
    table.add_row(
        "Protocol Found",
        "✅ Yes" if stat["protocol_found"] else "❌ No (Run methodology-copilot)",
    )
    table.add_row("Playbook Archetype", stat["playbook_type"])
    table.add_row("Current State", stat["phase"])
    table.add_section()
    table.add_row("Discovered Candidates", f"{stat['discovered_count']} papers")
    table.add_row("Deduplicated Corpus", f"{stat['deduped_count']} unique papers")
    table.add_row("Verified & Hydrated", f"{stat['verified_count']} verified")
    table.add_row(
        "Included Studies (PRISMA)",
        f"{stat['included_count']} included ({stat['excluded_count']} excluded)",
    )
    table.add_section()
    table.add_row("Harvested OA PDFs", f"{stat['pdfs_count']} PDFs")
    table.add_row("Extracted Markdown", f"{stat['extracted_count']} documents")
    table.add_row("Vector DB Chunks", f"{stat['vector_chunks']} chunks")
    table.add_row("Extraction Matrix Rows", f"{stat['matrix_rows']} rows")
    table.add_row("Citation Graph Nodes", f"{stat['graph_nodes']} nodes")
    table.add_row(
        "Grounded Synthesis",
        "✅ Generated" if stat["synthesis_generated"] else "⏳ Pending",
    )

    console.print(table)

    if stat["latest_events"]:
        event_table = Table(
            title="📜 Recent Audit Journal Events",
            show_header=True,
            header_style="bold yellow",
        )
        event_table.add_column("Timestamp", style="dim", width=24)
        event_table.add_column("Action", style="bold cyan", width=22)
        event_table.add_column("Agent / Tool", style="magenta", width=18)
        event_table.add_column("Description", style="white")

        for evt in stat["latest_events"]:
            event_table.add_row(
                evt.get("timestamp", "")[:19].replace("T", " "),
                evt.get("action", ""),
                evt.get("agent_or_tool", ""),
                evt.get("description", "")[:60] + "..."
                if len(evt.get("description", "")) > 60
                else evt.get("description", ""),
            )
        console.print(event_table)


@app.command("init")
def init(
    project_title: str = typer.Argument(
        ..., help="Research project title (used to derive the workspace slug)"
    ),
    target_dir: Path = typer.Option(  # noqa: B008
        Path("."),
        "--dir",
        "-d",
        help="Target directory to scaffold into (default: current dir)",
    ),
    scaffold_only: bool = typer.Option(
        False,
        "--scaffold-only",
        help="Skip the Socratic wizard; scaffold the layout with a placeholder protocol",
    ),
):
    """Bootstrap a portable Nexus Scholar research workspace in any folder (P7.3)."""
    init_command(project_title, target_dir, scaffold_only=scaffold_only)


@app.command("setup-mcp")
def setup_mcp(
    workspace: Path = typer.Option(  # noqa: B008
        Path("."),
        "--workspace",
        "-w",
        help="Path to research workspace the MCP server operates on",
    ),
    harness: list[str] = typer.Option(  # noqa: B008
        None,
        "--harness",
        "-h",
        help="Harness target(s): claude, cursor, vscode, dsh, mcp, or all (comma/space separated)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print the exact write plan without touching the filesystem",
    ),
    env_file: Path | None = typer.Option(  # noqa: B008
        None,
        "--env-file",
        help=".env file with SCHOLAR_*/NEXUS_*/provider keys to pass through (default: <workspace>/.env if present)",
    ),
):
    """Wire the nexus-scholar MCP server into harness config files (P7.4)."""
    run_setup_mcp(workspace, harness, dry_run=dry_run, env_file=env_file)


@app.command("doctor")
def doctor(
    workspace: Path = typer.Option(  # noqa: B008
        Path("."),
        "--workspace",
        "-w",
        help="Path to a workspace to layout-validate (optional)",
    ),
    env_file: Path | None = typer.Option(  # noqa: B008
        None,
        "--env-file",
        help=".env file with SCHOLAR_*/NEXUS_*/provider keys (default: <workspace>/.env if present)",
    ),
    as_json: bool = typer.Option(
        False,
        "--json",
        help="Emit a machine-readable JSON report (values always masked)",
    ),
    exit_code: bool = typer.Option(
        False,
        "--exit-code",
        help="Exit non-zero if any check FAILs (doctor is advisory by default)",
    ),
):
    """Validate kits/versions, API keys, skills, and workspace layout (P7.5)."""
    ws = workspace.resolve()
    if env_file is None:
        candidate = ws / ".env"
        if candidate.is_file():
            env_file = candidate
    report = run_doctor(workspace=ws, env_file=env_file)
    render(report, as_json=as_json)
    if exit_code and report["overall"] == "FAIL":
        raise typer.Exit(1)


log_app = typer.Typer(
    name="log",
    help="Append audit events to a workspace journal and refresh INDEX.md (P7.6).",
    add_completion=False,
    no_args_is_help=True,
)


@log_app.command("event")
def log_event_command(
    workspace: str = typer.Argument(
        ...,
        help="Workspace directory path, or a project slug under a workspaces/ parent",
    ),
    action: str = typer.Option(
        ..., "--action", help="Action name (e.g. DISCOVERY_SEARCH); stored uppercased"
    ),
    agent: str = typer.Option(
        "agent", "--agent", help="Agent or tool responsible (e.g. scholar-search-kit)"
    ),
    description: str = typer.Option(
        "", "--description", help="Human-readable event description"
    ),
    inputs: list[str] = typer.Option(  # noqa: B008
        None,
        "--inputs",
        help="Input file(s) or identifier(s); repeatable and space-separated",
    ),
    outputs: list[str] = typer.Option(  # noqa: B008
        None, "--outputs", help="Output file(s); repeatable and space-separated"
    ),
    status: str = typer.Option(
        "SUCCESS", "--status", help="Event status (default SUCCESS); stored uppercased"
    ),
    param: list[str] = typer.Option(  # noqa: B008
        None, "--param", help="Parameter KEY=VALUE; repeatable"
    ),
    metric: list[str] = typer.Option(  # noqa: B008
        None, "--metric", help="Metric KEY=VALUE; repeatable"
    ),
):
    """Append one canonical audit event (audit/journal.jsonl) and refresh INDEX.md."""
    run_log_event(
        workspace,
        action=action,
        agent=agent,
        description=description,
        inputs=inputs,
        outputs=outputs,
        status=status,
        parameters=param,
        metrics=metric,
    )


@log_app.command("batch")
def log_batch_command(
    workspace: str = typer.Argument(
        ...,
        help="Workspace directory path, or a project slug under a workspaces/ parent",
    ),
    events_file: Path = typer.Argument(  # noqa: B008
        ..., help="JSONL file of event objects (one event per line)"
    ),
):
    """Append a JSONL batch of events and refresh INDEX.md.

    Lenient-skip policy: records that are malformed JSON or lack 'action' /
    'description' are skipped with an error line; validated records still
    append.  Exits 1 when any record was skipped or failed to write, but the
    journal always stays JSON-parse-clean.
    """
    run_log_batch(workspace, events_file)


@log_app.command("sync-index")
def log_sync_index_command(
    workspace: str = typer.Argument(
        ...,
        help="Workspace directory path, or a project slug under a workspaces/ parent",
    ),
):
    """Regenerate INDEX.md from workspace state (no journal append)."""
    run_sync_index(workspace)


app.add_typer(log_app, name="log")


keys_app = typer.Typer(
    name="keys",
    help="Store provider API keys in the OS keychain (never in a file).",
    add_completion=False,
    no_args_is_help=True,
)
_PROVIDER_HELP = "anthropic | openai_compatible | gemini"


@keys_app.command("set")
def keys_set(provider: str = typer.Argument(..., help=_PROVIDER_HELP)) -> None:
    """Store a key; it is typed at a hidden prompt and goes only to the keychain."""
    from scholar_agent.keys import store_key

    value = typer.prompt(f"{provider} API key", hide_input=True)
    try:
        store_key(provider, value)
    except (ValueError, RuntimeError) as exc:
        console.print(f"[bold red]❌ {exc}[/bold red]")
        raise typer.Exit(1) from exc
    console.print(f"[green]✓ {provider} key stored in the OS keychain[/green]")


@keys_app.command("status")
def keys_status() -> None:
    """Say where each provider's key is found (keychain, environment, none); never the key."""
    from scholar_agent.keys import ENV_VARS, key_status

    for provider in ENV_VARS:
        status = key_status(provider)
        console.print(f"{provider}: {status.source}")


@keys_app.command("clear")
def keys_clear(provider: str = typer.Argument(..., help=_PROVIDER_HELP)) -> None:
    """Remove a provider's key from the OS keychain."""
    from scholar_agent.keys import clear_key

    try:
        removed = clear_key(provider)
    except ValueError as exc:
        console.print(f"[bold red]❌ {exc}[/bold red]")
        raise typer.Exit(1) from exc
    console.print(f"{provider}: {'removed from the keychain' if removed else 'no keychain entry'}")


app.add_typer(keys_app, name="keys")


gate_app = typer.Typer(
    name="prompt-gate",
    help="The screening prompt gate on the frozen v03 set (agent-system §5).",
    add_completion=False,
    no_args_is_help=True,
)
_V03 = Path("workspaces") / "uav-crop-weed-v03"


def _gate_inputs(workspace: Path, limit: int | None, model: str, effort: str, max_tokens: int):
    import json as _json

    from scholar_agent import prompt_gate as pg

    frozen = _json.loads(pg.SET_FILE.read_text(encoding="utf-8"))
    records = pg.load_set(workspace, frozen)
    if limit:
        # A smoke run keeps both labels: the first includes and excludes in id order.
        inc = [r for r in records if r.label == "INCLUDE"][: (limit + 1) // 2]
        exc = [r for r in records if r.label == "EXCLUDE"][: limit // 2]
        records = inc + exc
    protocol = _json.loads((workspace / "protocol.json").read_text(encoding="utf-8"))
    return frozen, records, protocol, pg.run_spec(protocol, model=model, effort=effort, max_tokens=max_tokens)


@gate_app.command("estimate")
def gate_estimate(
    model: str = typer.Option("claude-opus-5-5", "--model"),
    provider: str = typer.Option("anthropic", "--provider"),
    effort: str = typer.Option("low", "--effort"),
    limit: int = typer.Option(0, "--limit", help="Only the first N records (a smoke run)"),
    workspace: Path = typer.Option(_V03, "--workspace"),
) -> None:
    """Estimate a gate run's tokens and cost from the dated price table; spends nothing."""
    from scholar_agent import prompt_gate as pg

    _frozen, records, _protocol, spec = _gate_inputs(workspace, limit or None, model, effort, 4096)
    batch = provider == "anthropic" and len(records) > pg.DIRECT_LIMIT
    result = pg.estimate(records, spec, provider=provider, batch=batch)
    cost = f"${result['cost_usd']:.2f}" if result["cost_usd"] is not None else "not priced"
    pricing = "Batches, half price" if batch else "direct calls, full price"
    console.print(
        f"{result['records']} records · {provider}/{model} at {effort} effort · estimate {cost} "
        f"({pricing}, prices as of {result['prices_as_of']}; an estimate, not a measurement)"
    )
    console.print(f"assumptions: {result['assumptions']}  tokens: {result['tokens']}")


@gate_app.command("run")
def gate_run(
    model: str = typer.Option("claude-opus-5-5", "--model"),
    provider: str = typer.Option("anthropic", "--provider"),
    effort: str = typer.Option("low", "--effort"),
    max_tokens: int = typer.Option(4096, "--max-tokens"),
    limit: int = typer.Option(0, "--limit", help="Only the first N records (a smoke run)"),
    base_url: str = typer.Option("", "--base-url", help="OpenAI-compatible endpoint"),
    yes: bool = typer.Option(False, "--yes", help="Confirm: this spends your provider key"),
    workspace: Path = typer.Option(_V03, "--workspace"),
) -> None:
    """Run the gate on the provider (spends your key) and write its report."""
    import json as _json
    from datetime import UTC, datetime

    from scholar_agent import prompt_gate as pg
    from scholar_agent.drivers import make_driver
    from scholar_agent.keys import resolve_key

    frozen, records, protocol, spec = _gate_inputs(workspace, limit or None, model, effort, max_tokens)
    batch = provider == "anthropic" and len(records) > pg.DIRECT_LIMIT
    estimate = pg.estimate(records, spec, provider=provider, batch=batch)
    if not yes:
        console.print(f"[yellow]Not run. Estimate: {estimate['cost_usd']} USD for {estimate['records']} records. Add --yes to spend your key.[/yellow]")
        raise typer.Exit(1)
    key = resolve_key(provider)
    if key is None and provider != "openai_compatible":
        console.print(f"[bold red]❌ No {provider} key. Run: nexus-scholar keys set {provider}[/bold red]")
        raise typer.Exit(1)
    options = {"direct_limit": pg.DIRECT_LIMIT} if provider == "anthropic" else {}
    driver = make_driver(provider, api_key=key, base_url=base_url or None, **options)
    console.print(f"Running {len(records)} records on {provider}/{model} …")
    results = driver.run(pg.requests_for(records), spec)
    out = pg.report(frozen=frozen, records=records, results=results, protocol=protocol, provider=provider, spec=spec, batch=batch)
    out["estimate"] = estimate
    out["smoke_run"] = bool(limit)
    out["finished_at"] = datetime.now(UTC).isoformat()
    pg.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = pg.RESULTS_DIR / f"{stamp}_{provider}_{model}_{effort}{'_smoke' if limit else ''}.json"
    path.write_text(_json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if not out["measured"]:
        first = next((r["driver_detail"] for r in out["records"] if r["driver_detail"]), "no result")
        console.print(f"[bold red]Not measured: none of the {len(records)} calls succeeded. First error: {first}. Report {path}[/bold red]")
        raise typer.Exit(1)
    s = out["score"]
    console.print(
        f"include-recall {s['include_recall']} (95% lower bound {s['include_recall_ci_low']}, bar {s['bar']}): "
        f"{'PASS' if s['passes'] else 'FAIL'} · excludes caught {s['exclusion_rate_on_confirmed_excludes']} · "
        f"unclear {s['unclear_rate']} · cost {out['cost_usd']} USD · report {path}"
    )



@gate_app.command("export")
def gate_export(
    out: Path = typer.Option(..., "--out", help="Folder for the blind export (prompt, schema, record batches)"),
    limit: int = typer.Option(0, "--limit", help="Only the first N records (a smoke run)"),
    workspace: Path = typer.Option(_V03, "--workspace"),
) -> None:
    """Export the set for agents to answer (the MCP route); no label leaves with it."""
    from scholar_agent import prompt_gate as pg

    frozen, records, _protocol, spec = _gate_inputs(workspace, limit or None, "claude-code", "n/a", 4096)
    manifest = pg.export_set(records, spec, out, set_sha256=frozen["set_sha256"])
    console.print(f"Exported {manifest['records']} records in {len(manifest['batches'])} batches to {out}; answers go in {out / 'answers'}")


@gate_app.command("import")
def gate_import(
    export: Path = typer.Option(..., "--export", help="The folder written by `prompt-gate export`, with its answers/"),
    model: str = typer.Option(..., "--model", help="The model the agents ran on"),
    workspace: Path = typer.Option(_V03, "--workspace"),
) -> None:
    """Score agents' answers to an export with the same checks, rule table and bar as a run."""
    import json as _json
    from datetime import UTC, datetime

    from scholar_agent import prompt_gate as pg

    manifest = _json.loads((export / "manifest.json").read_text(encoding="utf-8"))
    frozen, records, protocol, spec = _gate_inputs(workspace, None, model, "n/a", 4096)
    if manifest["set_sha256"] != frozen["set_sha256"] or manifest["prompt_sha256"] != pg.task_mod.load_task().prompt_sha256:
        console.print("[bold red]The export was made from another set or prompt; export again.[/bold red]")
        raise typer.Exit(1)
    wanted = set(manifest["study_ids"])
    records = [r for r in records if r.study_id in wanted]
    results = pg.import_answers(export, records, model=model)
    out = pg.report(frozen=frozen, records=records, results=results, protocol=protocol, provider=pg.MCP_PROVIDER, spec=spec, batch=False)
    out["smoke_run"] = len(records) < sum(frozen["counts"].values())
    out["finished_at"] = datetime.now(UTC).isoformat()
    pg.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = pg.RESULTS_DIR / f"{stamp}_{pg.MCP_PROVIDER}_{model}{'_smoke' if out['smoke_run'] else ''}.json"
    path.write_text(_json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if not out["measured"]:
        console.print(f"[bold red]Not measured: no answer of the {len(records)} was usable. Report {path}[/bold red]")
        raise typer.Exit(1)
    s = out["score"]
    console.print(
        f"include-recall {s['include_recall']} (95% lower bound {s['include_recall_ci_low']}, bar {s['bar']}): "
        f"{'PASS' if s['passes'] else 'FAIL'} · excludes caught {s['exclusion_rate_on_confirmed_excludes']} · "
        f"unclear {s['unclear_rate']} · statuses {out['driver_statuses']} · report {path}"
    )


app.add_typer(gate_app, name="prompt-gate")


extract_app = typer.Typer(
    name="extract",
    help=(
        "Publish the Contract v1 document manifest for a workspace's real Stage 5 "
        "extraction output and hand it to Stage 6 (runtime acceptance adoption)."
    ),
    add_completion=False,
    no_args_is_help=True,
)


def _extract_workspace(value: str) -> Path:
    return Path(value).resolve()


def _emit_json(payload: dict) -> None:
    """Write one machine-readable JSON document to stdout, and nothing else.

    ``--json`` is a wire format, so it must not be rendered through the shared
    ``console``: that one is built with ``force_terminal=True`` for the human tables,
    which makes Rich emit ANSI regardless of TTY, ``NO_COLOR`` or ``TERM=dumb`` and
    turns a human refusal banner into unparseable output. Plain ``print`` is what
    ``doctor.render`` already does for its own ``--json``, and the two surfaces now
    behave identically. ``sort_keys`` keeps the output diffable across runs.

    Callers must emit this *instead of* the human block, never alongside it.
    """

    print(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, default=str)
    )


@extract_app.command("status")
def extract_status(
    workspace: str = typer.Argument(..., help="Workspace directory path"),
    as_json: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
):
    """Report what is recorded for extraction publication; publish nothing."""
    from .extraction_producer import publication_status

    report = publication_status(_extract_workspace(workspace))
    if as_json:
        _emit_json(report)
        return
    recordings = report.get("recordings") or {}
    refusal = recordings.get("refusal")
    if refusal:
        console.print(
            f"[bold yellow]Not ready to publish: {refusal['code']}[/bold yellow]"
        )
        console.print(f"[dim]{refusal['message']}[/dim]")
    else:
        console.print(
            f"[bold green]Ready to publish[/bold green] "
            f"workspace={recordings['workspace_id']} "
            f"run={recordings['screening_run_id']} "
            f"accepted_manifests={recordings['document_manifests'] or 'none'}"
        )
    console.print(f"extracted files: {len(report['extracted_files'])}")


@extract_app.command("publish")
def extract_publish(
    workspace: str = typer.Argument(..., help="Workspace directory path"),
    index: bool = typer.Option(
        False, "--index", help="Run Stage 6 over the accepted manifest afterwards"
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
):
    """Publish the accepted document manifest through the frozen acceptance gate."""
    from .extraction_producer import publish_document_manifest

    outcome = publish_document_manifest(_extract_workspace(workspace))
    payload: dict = {"publication": outcome.as_dict()}
    exit_code = 0 if outcome.accepted else 1
    if index:
        if outcome.accepted:
            indexing, exit_code = _extract_index(workspace, exit_code)
            payload["indexing"] = indexing
        else:
            # Nothing was accepted, so there is nothing to index. Running Stage 6 here
            # would only record a refusal over an empty run.
            payload["indexing"] = {"skipped": "no accepted document manifest"}

    if as_json:
        # One document, and only that: a second JSON body on stdout would make the
        # whole stream unparseable just as surely as a human banner would.
        _emit_json(payload)
    else:
        if outcome.accepted:
            console.print(
                f"[bold green]Published {outcome.documents} document record(s)[/bold green] "
                f"{outcome.artifact_id} -> {outcome.published_path}"
                + (" (idempotent replay)" if outcome.idempotent else "")
            )
            if outcome.record_path:
                console.print(f"provenance record: {outcome.record_path}")
        else:
            refusal = outcome.refusal or {}
            console.print(
                f"[bold red]Refused ({outcome.status}): {refusal.get('code')}[/bold red]"
            )
            console.print(f"[dim]{refusal.get('message')}[/dim]")
        if index:
            _print_index(payload.get("indexing") or {})
    if exit_code:
        raise typer.Exit(exit_code)


@extract_app.command("index")
def extract_index(
    workspace: str = typer.Argument(..., help="Workspace directory path"),
    as_json: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
):
    """Run Stage 6 over the already-accepted document manifest."""
    result, exit_code = _extract_index(workspace, 0)
    if as_json:
        _emit_json(result)
    else:
        _print_index(result)
    if exit_code:
        raise typer.Exit(exit_code)


def _extract_index(workspace: str, exit_code: int) -> tuple[dict, int]:
    """Run Stage 6 and return its JSON result plus the process exit code.

    Both ``extract index`` and ``extract publish --index`` need this, and both must
    agree: the typed refusal is returned as data rather than raised past the caller, so
    a refusal is rendered (or serialized) by the one code path that owns the format.
    """

    from .extraction_producer import PublicationRefused, index_accepted_documents

    try:
        result = index_accepted_documents(_extract_workspace(workspace))
    except PublicationRefused as refusal:
        # ``stage6_refused`` rather than ``refused``: a *successful* Stage 6 result
        # already carries a ``refused`` list of rejected documents, and reusing that
        # name for the refusal case would make the two shapes indistinguishable.
        result = {"stage6_refused": True, "status": "FAILED", **refusal.as_dict()}
        exit_code = exit_code or 1
    else:
        if result.get("indexed_files", 0) == 0:
            exit_code = exit_code or 1
    return result, exit_code


def _print_index(result: dict) -> None:
    """Render one Stage 6 result as the human block, unchanged in wording and order."""

    if result.get("stage6_refused"):
        console.print(f"[bold red]Stage 6 refused: {result['code']}[/bold red]")
        console.print(f"[dim]{result['message']}[/dim]")
        return
    if result.get("skipped"):
        # ``publish --index`` on a refused publication: previously the command exited
        # before indexing, so the human block said nothing about Stage 6. It stays
        # silent here for that reason; the reason itself is still in the JSON payload.
        return
    console.print(
        f"[bold green]Stage 6 {result['status']}[/bold green]: indexed "
        f"{result['indexed_files']} document(s), {result['total_chunks']} chunk(s), "
        f"{len(result['refused'])} refused"
    )


app.add_typer(extract_app, name="extract")


@app.command("supervise")
def supervise(
    workspace: Path = typer.Option(
        Path("."), "--workspace", "-w", help="Path to research workspace directory"
    ),
    once: bool = typer.Option(
        True,
        "--once/--loop",
        help="Run one detection pass (default) or loop continuously",
    ),
    interval: int = typer.Option(
        60, "--interval", "-i", help="Seconds between detection passes in loop mode"
    ),
):
    """Run the agent handoff supervisor to detect and advance phases."""
    import time

    from .handoff import run_supervisor_once

    ws = workspace.resolve()

    if once:
        result = run_supervisor_once(ws)
        if result.get("action") == "ADVANCED":
            console.print(
                f"[bold green]Phase advanced: {result['from_phase']} → {result['to_phase']}[/bold green]"
            )
        else:
            console.print(
                f"[bold yellow]{result.get('reason', 'No action taken')}[/bold yellow]"
            )
        return

    console.print(
        f"[bold cyan]Supervisor loop started for {ws} (interval: {interval}s)[/bold cyan]"
    )
    try:
        while True:
            result = run_supervisor_once(ws)
            if result.get("action") == "ADVANCED":
                console.print(
                    f"[bold green]Phase advanced: {result['from_phase']} → {result['to_phase']}[/bold green]"
                )
            elif result.get("action") != "NOOP":
                console.print(f"[yellow]{result.get('action', 'unknown')}[/yellow]")
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("[bold yellow]Supervisor loop stopped.[/bold yellow]")


@app.command("inception")
def inception(
    root: Path = typer.Option(
        Path("."),
        "--root",
        "-r",
        help="Repository root containing workspaces/ (default: current dir)",
    ),
    no_scaffold: bool = typer.Option(
        False, "--no-scaffold", help="Run the interview only; emit nothing to disk"
    ),
    grounded: bool = typer.Option(
        False,
        "--grounded",
        help="Ground the inquiry in a real literature surface scan (probe + distill) before the refraction grid",
    ),
    auto_select: bool = typer.Option(
        False,
        "--auto-select",
        help="Headless: pick the best (first) grounded direction without an interactive prompt",
    ),
    direction_id: int | None = typer.Option(
        None,
        "--direction-id",
        help="Headless: pick the N-th grounded direction (1-based) without an interactive prompt",
    ),
    replace: bool = typer.Option(
        False,
        "--replace",
        help="Replace the protocol of an existing workspace with this title (the old protocol files are backed up under audit/replaced/)",
    ),
    discard_screening_binding: bool = typer.Option(
        False,
        "--discard-screening-binding",
        help="With --replace: replace even though screening decisions or a published screening exist under the current protocol",
    ),
):
    """Run the Phase-0 Socratic methodology interview and emit a compiled protocol."""
    inception_command(
        root,
        no_scaffold=no_scaffold,
        grounded=grounded,
        auto_select=auto_select,
        direction_id=direction_id,
        replace=replace,
        discard_screening_binding=discard_screening_binding,
    )


@app.command("sync")
def sync(
    workspace: Path = typer.Option(
        Path("."), "--workspace", "-w", help="Path to research workspace directory"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Compute stats without writing any files"
    ),
):
    """Atomically rebuild project.json stats and INDEX.md from filesystem state."""
    orchestrator = ResearchOrchestrator(workspace)
    result = orchestrator.sync_state(dry_run=dry_run)

    table = Table(
        title=f"🔄 State Sync: {result['workspace']}",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Key", style="bold white", width=30)
    table.add_column("Value", style="green", width=42)

    if result.get("dry_run"):
        table.add_row("Mode", "DRY RUN (no files written)")
        stats = result.get("stats_updated", {})
    else:
        table.add_row("Mode", "Committed")
        stats = result.get("stats", {})
        table.add_row(
            "INDEX.md Regenerated",
            "✅ Yes"
            if result.get("index_regenerated")
            else "⚠️  Not (workspace-manager unavailable)",
        )

    table.add_section()
    for key in (
        "discovered_papers",
        "verified_papers",
        "included_papers",
        "excluded_papers",
        "downloaded_pdfs",
        "extracted_markdowns",
    ):
        if key in stats:
            table.add_row(key, str(stats[key]))
    remaining = {
        k: v
        for k, v in stats.items()
        if k
        not in (
            "discovered_papers",
            "verified_papers",
            "included_papers",
            "excluded_papers",
            "downloaded_pdfs",
            "extracted_markdowns",
        )
    }
    for key, value in remaining.items():
        table.add_row(key, str(value))

    console.print(table)


#: The workflow statuses the pipeline publishes
#: (``SUCCESS`` | ``EMPTY_RESULT`` | ``PENDING_AGENT_REVIEW`` | ``FAILED``).
#: The CLI headline, panel styling and exit code are derived from these --
#: never from "the command returned without raising" (T-TRUTH-COUNTS-01,
#: CLI-CLOSURE). An empty harvest, a degraded harvest and a pipeline waiting
#: for the PRISMA handoff are NOT successes and must never be announced as
#: such.
_PIPELINE_STATUS_PRESENTATION: dict[str, tuple[str, str, str]] = {
    "SUCCESS": (
        "✨ Research Pipeline Execution Completed Successfully!",
        "green",
        "bold green",
    ),
    "EMPTY_RESULT": (
        "⚠️  Research Pipeline Completed with NO Results Discovered",
        "yellow",
        "bold yellow",
    ),
    "PENDING_AGENT_REVIEW": (
        "⏸ Research Pipeline Paused — awaiting PRISMA screening (agent-in-the-loop)",
        "cyan",
        "bold cyan",
    ),
    "FAILED": (
        "❌ Research Pipeline FAILED",
        "red",
        "bold red",
    ),
}

#: Headline used when the harvest was degraded (``results["degraded"]``) but
#: the workflow state is still ``SUCCESS``: a degraded harvest must never
#: carry an unqualified success claim.
_DEGRADED_HEADLINE = "⚠️  Research Pipeline Completed with a DEGRADED discovery harvest"

#: Headline used for a status the CLI does not know: unknown is not success.
_UNKNOWN_STATUS_HEADLINE = "⚠️  Research Pipeline Completed with an unrecognised status"


def _stage_count(stage: object, *keys: str) -> int:
    """Return an integer stage count from an int, a mapping or ``None``.

    The pipeline publishes a stage either as a plain integer (the discovery
    count) or as a mapping (``{"unique": 5, "duplicates_removed": 2}`` on the
    normal path, ``{"unique": 0, "status": "SKIPPED", "reason": ...}`` on the
    abort path). A mapping is read through ``keys`` in order; a mapping that
    carries none of them (a skipped stage) yields ``0``.

    The result is always an ``int``: the summary panel never renders a raw
    mapping or ``None`` to the user.
    """
    if isinstance(stage, bool):
        return 0
    if isinstance(stage, int):
        return stage
    if isinstance(stage, Mapping):
        for key in keys:
            raw = stage.get(key)
            if isinstance(raw, bool):
                continue
            if isinstance(raw, int):
                return raw
            if isinstance(raw, float):
                return int(raw)
            if isinstance(raw, str) and raw.strip().lstrip("-").isdigit():
                return int(raw.strip())
        return 0
    return 0


def _stage_note(stage: object) -> str:
    """Return a short annotation for a skipped stage (``""`` otherwise).

    A skipped stage reports ``0``; the reason is surfaced so the user can see
    *why* the stage did not run instead of reading a bare zero.
    """
    if (
        isinstance(stage, Mapping)
        and str(stage.get("status") or "").upper() == "SKIPPED"
    ):
        reason = str(stage.get("reason") or "").strip()
        return f" (SKIPPED: {reason})" if reason else " (SKIPPED)"
    return ""


def _pipeline_summary_panel(results: object) -> tuple[Panel, str]:
    """Build the pipeline summary panel and return it with the status.

    The second element is the workflow status (``SUCCESS`` |
    ``EMPTY_RESULT`` | ``PENDING_AGENT_REVIEW`` | ``FAILED``) the panel
    reports; the caller uses it to decide the exit code. The headline is
    derived from that status (and from the degradation flag), never from the
    absence of an exception.
    """
    data: Mapping[str, object] = results if isinstance(results, Mapping) else {}
    stages: Mapping[str, object] = (
        data.get("stages") if isinstance(data.get("stages"), Mapping) else {}
    )

    # A missing/empty status is NOT a success: it is an unknown outcome and
    # must render the unknown-status headline (never "Successfully").
    raw_status = str(data.get("status") or "UNKNOWN").strip().upper()
    degraded = bool(data.get("degraded"))
    degradation_reason = str(data.get("degradation_reason") or "").strip()

    headline, border_style, heading_style = _PIPELINE_STATUS_PRESENTATION.get(
        raw_status, (_UNKNOWN_STATUS_HEADLINE, "yellow", "bold yellow")
    )
    if raw_status == "SUCCESS" and degraded:
        # A degraded harvest is never an unqualified success.
        headline = _DEGRADED_HEADLINE
        border_style = "yellow"
        heading_style = "bold yellow"

    discovery_stage = stages.get("discovery")
    screening_stage = stages.get("screening")
    extraction_stage = stages.get("extraction")
    synthesis_stage = stages.get("synthesis")

    lines: list[str] = [
        f"[{heading_style}]{headline}[/{heading_style}]",
        "",
        f"[bold]Status: {raw_status}[/bold]",
    ]

    discovery = data.get("discovery")
    if isinstance(discovery, Mapping):
        harvest = str(discovery.get("status") or "").strip().upper()
        if harvest:
            harvest_reason = str(discovery.get("reason") or "").strip()
            suffix = f" ({harvest_reason})" if harvest_reason else ""
            lines.append(f"Discovery harvest: {harvest}{suffix}")

    if degraded:
        lines.append(
            "[bold yellow]⚠ Degraded harvest: "
            f"{degradation_reason or 'reason not reported'}[/bold yellow]"
        )

    pending = _stage_count(screening_stage, "papers_to_screen")
    lines.extend(
        [
            "",
            (
                f"• Discovered: {_stage_count(discovery_stage, 'count', 'discovered')}"
                f" papers{_stage_note(discovery_stage)}"
            ),
            (
                f"• Deduplicated: {_stage_count(stages.get('deduplication'), 'unique')}"
                f" unique{_stage_note(stages.get('deduplication'))}"
            ),
            (
                "• Included (PRISMA): "
                f"{_stage_count(screening_stage, 'included', 'included_count')}"
                f"{_stage_note(screening_stage)}"
            ),
            (
                "• Markdown Extracts: "
                f"{_stage_count(extraction_stage, 'documents', 'extracted')}"
                f"{_stage_note(extraction_stage)}"
            ),
            (
                f"• Matrix Rows: {_stage_count(stages.get('matrix_rows'), 'rows')}"
                f"{_stage_note(stages.get('matrix_rows'))}"
            ),
            (
                f"• Graph Nodes: {_stage_count(stages.get('graph_nodes'), 'nodes')}"
                f"{_stage_note(stages.get('graph_nodes'))}"
            ),
            (
                "• Grounded Claims: "
                f"{_stage_count(synthesis_stage, 'verified_claims')} / "
                f"{_stage_count(synthesis_stage, 'total_claims')} verified"
                f"{_stage_note(synthesis_stage)}"
            ),
        ]
    )
    if pending:
        lines.append(f"• Papers awaiting PRISMA screening: {pending}")

    panel = Panel.fit(
        "\n".join(lines),
        title="Pipeline Execution Summary",
        border_style=border_style,
    )
    return panel, raw_status


@app.command("run")
def run_pipeline(
    protocol: Path = typer.Option(
        None,
        "--protocol",
        "-p",
        help="Path to canonical protocol.json (classic orchestrator)",
    ),
    pipeline: Path = typer.Option(
        None, "--pipeline", help="Path to a PipelineSpec JSON file (M5.4 DAG executor)"
    ),
    workspace: Path = typer.Option(
        Path("."), "--workspace", "-w", help="Target research workspace directory"
    ),
    limit: int = typer.Option(
        None, "--limit", "-l", help="Max search candidates to fetch (for testing)"
    ),
    skip: str = typer.Option(
        None, "--skip", help="Comma-separated node ids to skip (DAG executor only)"
    ),
):
    """Execute a research pipeline: either the classic orchestrator (--protocol)
    or a PipelineSpec DAG (--pipeline, M5.4)."""
    if pipeline is not None:
        _run_pipeline_spec(pipeline, workspace, skip)
        return

    protocol_path = protocol or Path("protocol.json")
    orchestrator = ResearchOrchestrator(workspace)
    console.print(
        f"[bold cyan]🚀 Initializing Nexus Scholar Pipeline for {protocol_path}...[/bold cyan]"
    )

    from scholar_search.engine import MailtoNotSet

    try:
        with console.status("[bold green]Executing multi-stage pipeline..."):
            res = orchestrator.run_pipeline(
                protocol_path=protocol_path, max_search_results=limit
            )
    except MailtoNotSet as exc:
        # Decision 2026-11-08: no live search without a real contact email.
        console.print(f"[bold red]❌ {exc}[/bold red]")
        raise typer.Exit(code=1) from None

    panel, status = _pipeline_summary_panel(res)
    console.print(panel)

    if status == "FAILED":
        # A hard failure is the only non-zero exit: an empty harvest, a
        # degraded harvest and a pipeline waiting for the PRISMA handoff are
        # not failures -- but the panel states plainly what happened.
        raise typer.Exit(code=1)


def _run_pipeline_spec(pipeline: Path, workspace: Path, skip: str | None) -> None:
    """Execute a PipelineSpec DAG (M5.4)."""
    from .pipeline_executor import PipelineError, execute_file

    console.print(
        f"[bold cyan]🚀 Executing PipelineSpec {pipeline} in {workspace}...[/bold cyan]"
    )
    skip_ids = [s.strip() for s in skip.split(",")] if skip else []
    try:
        spec, results = execute_file(
            pipeline, workspace, output=console.print, skip=skip_ids
        )
    except PipelineError as exc:
        console.print(f"[bold red]❌ Pipeline halted: {exc}[/bold red]")
        raise typer.Exit(1)

    table = Table(
        title=f"➜ PipelineSpec {spec.id} · {spec.name or spec.archetype}",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Node", style="bold white", width=22)
    table.add_column("State", style="green", width=10)
    table.add_column("Exit", style="dim", width=6)
    table.add_column("Detail", style="white")
    for r in results:
        detail = (
            r.message or r.skipped_reason or (" ".join(r.command) if r.command else "—")
        )
        table.add_row(
            r.node_id, r.state, "-" if r.exit_code is None else str(r.exit_code), detail
        )
    console.print(table)

    states = {r.state for r in results}
    if "halted" in states:
        console.print(
            "[bold yellow]⏸ Pipeline paused: human review required before re-run.[/bold yellow]"
        )
        raise typer.Exit(1)
    console.print("[bold green]✨ PipelineSpec execution complete.[/bold green]")


@app.command("export")
def export(
    format_type: str = typer.Argument(
        ...,
        help="Export target format: 'latex', 'typst', 'obsidian', 'zotero', 'pipeline-sh'",
    ),
    workspace: Path = typer.Option(
        Path("."), "--workspace", "-w", help="Path to research workspace directory"
    ),
    output: Path = typer.Option(
        None, "--output", "-o", help="Target output file or directory"
    ),
    pipeline: str | None = typer.Option(
        None,
        "--pipeline",
        help="PipelineSpec id (in <ws>/.harness-console/pipelines) or path (format 'pipeline-sh')",
    ),
    claim_confirmed: bool = typer.Option(
        False,
        "--claim-confirmed",
        help=(
            "Narrate the export as 'confirmed by a person'. Refuses unless a "
            "valid, non-retrospective literature/screening/HUMAN_CONFIRMATION.json "
            "exists whose artifact hashes verify against the workspace now "
            "(agent-layer Phase C spec 06 §4)."
        ),
    ),
):
    """Export synthesized research findings and bibliographies to external tools."""
    workspace_path = workspace.resolve()

    if claim_confirmed:
        from .contracts.confirmation.api import ConfirmationRefusalError, export_gate

        try:
            confirmation_model = export_gate(workspace_path)
        except ConfirmationRefusalError as exc:
            from .contracts.envelope.registry import RefusalCode as _RC

            console.print(
                "[bold red]❌ Export refused "
                f"({str(_RC(exc.refusal_code))}): {exc.detail}[/bold red]"
            )
            raise typer.Exit(1) from exc
        console.print(
            f"[bold]Human confirmation:[/bold] signed by "
            f"{confirmation_model.reviewer.name} "
            f"({confirmation_model.reviewer.affiliation}, lead_reviewer)"
        )
    synth_file = workspace_path / "synthesis" / "literature_review.md"
    bib_file = workspace_path / "literature" / "references.bib"
    if not bib_file.exists():
        bib_file = workspace_path / "synthesis" / "references.bib"

    if format_type.lower() == "latex":
        out_target = output or (workspace_path / "synthesis" / "literature_review.tex")
        AcademicTypesettingExporter.export_latex(synth_file, bib_file, out_target)
        console.print(
            f"[bold green]✅ Successfully exported LaTeX section to {out_target}[/bold green]"
        )

    elif format_type.lower() == "typst":
        out_target = output or (workspace_path / "synthesis" / "literature_review.typ")
        AcademicTypesettingExporter.export_typst(synth_file, bib_file, out_target)
        console.print(
            f"[bold green]✅ Successfully exported Typst manuscript to {out_target}[/bold green]"
        )

    elif format_type.lower() == "obsidian":
        out_target = output or (workspace_path / "literature" / "obsidian_vault")
        ObsidianVaultExporter.export_vault(workspace_path, out_target)
        console.print(
            f"[bold green]✅ Successfully exported Obsidian PKM Vault to {out_target}[/bold green]"
        )

    elif format_type.lower() == "zotero":
        bridge = ZoteroBridge()
        inc_file = workspace_path / "literature" / "included.json"
        pdf_dir = workspace_path / "pdfs"
        manifest = bridge.sync_included_papers(
            inc_file, pdf_dir, project_slug=workspace_path.name
        )
        console.print(
            f"[bold green]✅ Synced {manifest.get('items_synced', 0)} items to Zotero collection '{workspace_path.name}'[/bold green]"
        )

    elif format_type.lower() in ("pipeline-sh", "pipeline"):
        import os
        import uuid as uuid_mod

        from .integrations.pipeline_script import render_pipeline_sh
        from .pipeline_executor import load_spec

        if not pipeline:
            console.print(
                "[bold red]❌ export pipeline-sh requires --pipeline <id|path>[/bold red]"
            )
            raise typer.Exit(1)
        store_dir = workspace_path / ".harness-console" / "pipelines"
        cand = Path(pipeline)
        spec_path = cand if cand.is_file() else store_dir / f"{pipeline}.json"
        if not spec_path.is_file():
            console.print(
                f"[bold red]❌ pipeline spec not found: {spec_path}[/bold red]"
            )
            raise typer.Exit(1)
        try:
            spec = load_spec(spec_path)
        except Exception as exc:
            console.print(f"[bold red]❌ cannot load pipeline: {exc}[/bold red]")
            raise typer.Exit(1)
        script = render_pipeline_sh(spec, workspace_path)
        out_target = output or (store_dir / f"{spec.id}.sh")
        store_dir.mkdir(parents=True, exist_ok=True)
        tmp = out_target.with_name(out_target.name + f".tmp-{uuid_mod.uuid4().hex[:8]}")
        tmp.write_text(script, encoding="utf-8")
        os.replace(tmp, out_target)
        console.print(
            f"[bold green]✅ Exported pipeline {spec.id} → {out_target}[/bold green]"
        )

    else:
        console.print(
            f"[bold red]❌ Unsupported export format: {format_type}. Supported: latex, typst, obsidian, zotero, pipeline-sh[/bold red]"
        )
        raise typer.Exit(1)


@app.command("accept-corpus")
def accept_corpus_command(
    workspace: Path = typer.Option(
        Path("."), "--workspace", "-w", help="Path to research workspace directory"
    ),
    ris: list[str] | None = typer.Option(  # noqa: B008
        None,
        "--ris",
        help=(
            "A RIS export to import first, as LABEL=PATH (e.g. Scopus=scopus.ris) or PATH "
            "(label = file name). Repeat once per database; duplicates across files are removed."
        ),
    ),
):
    """Accept the workspace's corpus snapshot so screening can start.

    Builds the Contract-v1 corpus snapshot from literature/verified.json, or from
    the database exports given with --ris (or staged in the app), and publishes it
    through the acceptance gate. Run `prepare` afterwards. Re-running on the same
    records is a no-op.
    """
    from .corpus_accept import AcceptCorpusRefused, accept_corpus, parse_ris_option

    try:
        result = accept_corpus(workspace, ris=[parse_ris_option(r) for r in ris or []])
    except AcceptCorpusRefused as exc:
        console.print(f"[bold red]❌ {exc}[/bold red]", markup=True, soft_wrap=True)
        raise typer.Exit(1) from exc
    state = "already accepted" if result.already_accepted else "accepted"
    console.print(
        f"[bold green]✅ Corpus snapshot {state}:[/bold green] "
        f"{result.study_count} studies from {result.record_count} records",
        soft_wrap=True,
    )
    console.print(f"[dim]{result.artifact_id}[/dim]")
    console.print("[dim]Next: prepare the screening batches.[/dim]")


@app.command("serve")
def serve(
    workspace: Path = typer.Option(
        Path("."), "--workspace", "-w", help="Path to research workspace directory"
    ),
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Bind host (loopback by default)"
    ),
    port: int = typer.Option(8765, "--port", "-p", help="Bind port"),
    reload: bool = typer.Option(
        False, "--reload", help="Enable uvicorn auto-reload (development only)"
    ),
):
    """Run the Harness Console server (FastAPI + uvicorn) for a workspace.

    INC-01: binds to loopback only and requires a per-launch bearer token on
    every API route. The token is ``NEXUS_CONSOLE_TOKEN`` when set (so the
    research UI's proxy, started with the same variable, can call the
    console); otherwise a fresh one is generated and printed once.
    """
    import os
    import secrets

    import uvicorn

    from .console import create_app
    from .console.serve import LOOPBACK_HOSTS

    ws = workspace.resolve()
    if not ws.is_dir():
        console.print(f"[bold red]❌ Workspace directory not found: {ws}[/bold red]")
        raise typer.Exit(1)
    if host.strip("[]") not in LOOPBACK_HOSTS:
        console.print(
            f"[bold red]❌ Refusing to bind {host}: the console serves loopback only "
            f"({', '.join(LOOPBACK_HOSTS)}). Phone access on the LAN comes with a "
            "restricted sub-app, not this server.[/bold red]"
        )
        raise typer.Exit(1)

    token = os.environ.get("NEXUS_CONSOLE_TOKEN", "").strip()
    generated = not token
    if generated:
        token = secrets.token_urlsafe(32)

    app = create_app(ws, token=token, trusted_hosts=LOOPBACK_HOSTS)
    console.print(
        f"[bold cyan]🌐 Harness Console listening on http://{host}:{port}[/bold cyan]\n"
        f"[dim]Workspace: {ws}[/dim]"
    )
    if generated:
        console.print("[dim]Start the research UI with this token in its environment:[/dim]")
        # Plain, unwrapped and unhighlighted so it copies as one token.
        console.print(
            f"  NEXUS_CONSOLE_TOKEN={token}", markup=False, highlight=False, soft_wrap=True
        )
    else:
        console.print("[dim]Token: from NEXUS_CONSOLE_TOKEN[/dim]")
    console.print("[dim]CTRL+C to stop[/dim]")
    uvicorn.run(app, host=host, port=port, reload=reload)


@app.command("ui")
def ui(
    workspace: Path | None = typer.Option(  # noqa: B008
        None, "--workspace", "-w", help="Open this workspace folder directly (skips the workspaces screen)"
    ),
    root: Path | None = typer.Option(  # noqa: B008
        None, "--root", help="Folder holding your workspaces (else NEXUS_WORKSPACES_ROOT, else ~/Documents/Nexus Scholar/workspaces)"
    ),
    port: int = typer.Option(8770, "--port", "-p", help="Port on 127.0.0.1 (another free one is used if taken)"),
    no_browser: bool = typer.Option(False, "--no-browser", help="Print the link instead of opening the browser"),
):
    """Open Nexus Scholar in your browser: the app and its engine, on this computer only."""
    from .console.launcher import Launcher, free_port, resolve_ui_dir
    from .workspace.catalog import most_recent, resolve_root, validity

    ui_dir = resolve_ui_dir()
    if ui_dir is None:
        console.print(
            "[bold red]❌ This install has no app bundle. From a source checkout, build it with "
            "`npm --prefix apps/research-ui run build:export`, or point NEXUS_UI_DIR at a static export.[/bold red]"
        )
        raise typer.Exit(1)
    folder, _source = resolve_root(root)
    target = workspace.resolve() if workspace is not None else None
    if target is not None and not validity(target)[0]:
        console.print(f"[bold red]❌ Not a Nexus Scholar workspace: {target} ({validity(target)[1]})[/bold red]")
        raise typer.Exit(1)
    launcher = Launcher(
        root=folder,
        workspace=target if target is not None else most_recent(folder),
        ui_dir=ui_dir,
        port=free_port("127.0.0.1", port),
        open_browser=not no_browser,
        start_on_workspaces=workspace is None,
        say=lambda line: console.print(line, markup=False, highlight=False, soft_wrap=True),
    )
    try:
        launcher.run()
    except KeyboardInterrupt:
        pass


def main():
    app()


if __name__ == "__main__":
    main()
