"""Command Line Interface for Nexus Scholar Harness."""

from __future__ import annotations

import json
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .orchestrator import ResearchOrchestrator
from .integrations.latex_typst import AcademicTypesettingExporter
from .integrations.obsidian import ObsidianVaultExporter
from .integrations.zotero import ZoteroBridge

app = typer.Typer(
    name="scholar-harness",
    help="Nexus Scholar Harness: Master CLI orchestrating systematic research workflows, MCP servers, and academic ecosystem integrations.",
    add_completion=False,
)
console = Console()


@app.command("status")
def status(
    workspace: Path = typer.Option(
        Path("."), "--workspace", "-w", help="Path to research workspace directory"
    ),
):
    """Display comprehensive status and pipeline metrics for a research workspace."""
    orchestrator = ResearchOrchestrator(workspace)
    stat = orchestrator.get_status()

    table = Table(title=f"🔬 Nexus Scholar Workspace: {stat['title']}", show_header=True, header_style="bold cyan")
    table.add_column("Pipeline Dimension", style="bold white", width=26)
    table.add_column("Status / Metric Value", style="green", width=40)

    table.add_row("Workspace Directory", stat["workspace"])
    table.add_row("Protocol Found", "✅ Yes" if stat["protocol_found"] else "❌ No (Run methodology-copilot)")
    table.add_row("Playbook Archetype", stat["playbook_type"])
    table.add_row("Current State", stat["phase"])
    table.add_section()
    table.add_row("Discovered Candidates", f"{stat['discovered_count']} papers")
    table.add_row("Deduplicated Corpus", f"{stat['deduped_count']} unique papers")
    table.add_row("Verified & Hydrated", f"{stat['verified_count']} verified")
    table.add_row("Included Studies (PRISMA)", f"{stat['included_count']} included ({stat['excluded_count']} excluded)")
    table.add_section()
    table.add_row("Harvested OA PDFs", f"{stat['pdfs_count']} PDFs")
    table.add_row("Extracted Markdown", f"{stat['extracted_count']} documents")
    table.add_row("Vector DB Chunks", f"{stat['vector_chunks']} chunks")
    table.add_row("Extraction Matrix Rows", f"{stat['matrix_rows']} rows")
    table.add_row("Citation Graph Nodes", f"{stat['graph_nodes']} nodes")
    table.add_row("Grounded Synthesis", "✅ Generated" if stat["synthesis_generated"] else "⏳ Pending")

    console.print(table)

    if stat["latest_events"]:
        event_table = Table(title="📜 Recent Audit Journal Events", show_header=True, header_style="bold yellow")
        event_table.add_column("Timestamp", style="dim", width=24)
        event_table.add_column("Action", style="bold cyan", width=22)
        event_table.add_column("Agent / Tool", style="magenta", width=18)
        event_table.add_column("Description", style="white")

        for evt in stat["latest_events"]:
            event_table.add_row(
                evt.get("timestamp", "")[:19].replace("T", " "),
                evt.get("action", ""),
                evt.get("agent_or_tool", ""),
                evt.get("description", "")[:60] + "..." if len(evt.get("description", "")) > 60 else evt.get("description", "")
            )
        console.print(event_table)


@app.command("run")
def run_pipeline(
    protocol: Path = typer.Option(
        Path("protocol.json"), "--protocol", "-p", help="Path to canonical protocol.json"
    ),
    workspace: Path = typer.Option(
        Path("."), "--workspace", "-w", help="Target research workspace directory"
    ),
    limit: int = typer.Option(
        None, "--limit", "-l", help="Max search candidates to fetch (for testing)"
    ),
):
    """Execute the full end-to-end systematic research pipeline."""
    orchestrator = ResearchOrchestrator(workspace)
    console.print(f"[bold cyan]🚀 Initializing Nexus Scholar Pipeline for {protocol}...[/bold cyan]")

    with console.status("[bold green]Executing multi-stage pipeline..."):
        res = orchestrator.run_pipeline(protocol_path=protocol, max_search_results=limit)

    console.print(Panel.fit(
        f"[bold green]✨ Research Pipeline Execution Completed Successfully![/bold green]\n\n"
        f"• Discovered: {res['stages'].get('discovery', 0)} papers\n"
        f"• Deduplicated: {res['stages'].get('deduplication', 0)} unique\n"
        f"• Included (PRISMA): {res['stages'].get('screening', {}).get('included', 0)}\n"
        f"• Markdown Extracts: {res['stages'].get('extraction', 0)}\n"
        f"• Matrix Rows: {res['stages'].get('matrix_rows', 0)}\n"
        f"• Graph Nodes: {res['stages'].get('graph_nodes', 0)}\n"
        f"• Grounded Claims: {res['stages'].get('synthesis', {}).get('verified_claims', 0)} / {res['stages'].get('synthesis', {}).get('total_claims', 0)} verified",
        title="Pipeline Execution Summary",
        border_style="green"
    ))


@app.command("export")
def export(
    format_type: str = typer.Argument(
        ..., help="Export target format: 'latex', 'typst', 'obsidian', 'zotero'"
    ),
    workspace: Path = typer.Option(
        Path("."), "--workspace", "-w", help="Path to research workspace directory"
    ),
    output: Path = typer.Option(
        None, "--output", "-o", help="Target output file or directory"
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
        console.print(f"[bold green]✅ Successfully exported LaTeX section to {out_target}[/bold green]")

    elif format_type.lower() == "typst":
        out_target = output or (workspace_path / "synthesis" / "literature_review.typ")
        AcademicTypesettingExporter.export_typst(synth_file, bib_file, out_target)
        console.print(f"[bold green]✅ Successfully exported Typst manuscript to {out_target}[/bold green]")

    elif format_type.lower() == "obsidian":
        out_target = output or (workspace_path / "literature" / "obsidian_vault")
        ObsidianVaultExporter.export_vault(workspace_path, out_target)
        console.print(f"[bold green]✅ Successfully exported Obsidian PKM Vault to {out_target}[/bold green]")

    elif format_type.lower() == "zotero":
        bridge = ZoteroBridge()
        inc_file = workspace_path / "literature" / "included.json"
        pdf_dir = workspace_path / "pdfs"
        manifest = bridge.sync_included_papers(inc_file, pdf_dir, project_slug=workspace_path.name)
        console.print(f"[bold green]✅ Synced {manifest.get('items_synced', 0)} items to Zotero collection '{workspace_path.name}'[/bold green]")

    else:
        console.print(f"[bold red]❌ Unsupported export format: {format_type}. Supported: latex, typst, obsidian, zotero[/bold red]")
        raise typer.Exit(1)


def main():
    app()


if __name__ == "__main__":
    main()
