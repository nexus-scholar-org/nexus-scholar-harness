"""Command Line Interface for Nexus Scholar Harness."""

from __future__ import annotations

import sys
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
):
    """Run the Phase-0 Socratic methodology interview and emit a compiled protocol."""
    inception_command(
        root,
        no_scaffold=no_scaffold,
        grounded=grounded,
        auto_select=auto_select,
        direction_id=direction_id,
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

    with console.status("[bold green]Executing multi-stage pipeline..."):
        res = orchestrator.run_pipeline(
            protocol_path=protocol_path, max_search_results=limit
        )

    console.print(
        Panel.fit(
            f"[bold green]✨ Research Pipeline Execution Completed Successfully![/bold green]\n\n"
            f"• Discovered: {res['stages'].get('discovery', 0)} papers\n"
            f"• Deduplicated: {res['stages'].get('deduplication', 0)} unique\n"
            f"• Included (PRISMA): {res['stages'].get('screening', {}).get('included', 0)}\n"
            f"• Markdown Extracts: {res['stages'].get('extraction', 0)}\n"
            f"• Matrix Rows: {res['stages'].get('matrix_rows', 0)}\n"
            f"• Graph Nodes: {res['stages'].get('graph_nodes', 0)}\n"
            f"• Grounded Claims: {res['stages'].get('synthesis', {}).get('verified_claims', 0)} / {res['stages'].get('synthesis', {}).get('total_claims', 0)} verified",
            title="Pipeline Execution Summary",
            border_style="green",
        )
    )


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
):
    """Export synthesized research findings and bibliographies to external tools."""
    workspace_path = workspace.resolve()
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
    """Run the Harness Console server (FastAPI + uvicorn) for a workspace."""
    import uvicorn

    from .console import create_app

    ws = workspace.resolve()
    if not ws.is_dir():
        console.print(f"[bold red]❌ Workspace directory not found: {ws}[/bold red]")
        raise typer.Exit(1)

    app = create_app(ws)
    console.print(
        f"[bold cyan]🌐 Harness Console listening on http://{host}:{port}[/bold cyan]\n"
        f"[dim]Workspace: {ws}[/dim]\n"
        f"[dim]CTRL+C to stop[/dim]"
    )
    uvicorn.run(app, host=host, port=port, reload=reload)


def main():
    app()


if __name__ == "__main__":
    main()
