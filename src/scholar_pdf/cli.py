# ruff: noqa: B008 - Typer intentionally uses option/argument calls in defaults.
import asyncio
import json
import os
import sys
import tempfile
from contextlib import suppress
from pathlib import Path

import typer
from rich.console import Console
from rich.markup import escape
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table

# Force UTF-8 on Windows to prevent Rich console UnicodeEncodeError on OEM code pages
if sys.platform == "win32":
    with suppress(AttributeError, OSError, ValueError):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

from .acquisition import PDFAcquisitionService, WorkspaceManagerCliAuditSink
from .acquisition_models import AcquisitionRunConfig, OperationStatus
from .config import DECISION, MailtoNotSetError, contact_email, settings
from .downloader import AsyncPDFDownloader
from .extract import DoclingEngine, GrobidEngine
from .extraction import PDFExtractionService
from .extraction_models import ExtractionRunConfig
from .open_copies import FAILED as LOOKUP_STATE_FAILED
from .open_copies import (
    LOOKUP_FAILED,
    NO_OPEN_COPY_LISTED,
    OPEN_NO_DIRECT_PDF,
    PDF_NOT_FETCHED,
)
from .publisher_patterns import PROXY_STYLES

app = typer.Typer(
    help=(
        "Scholar PDF Kit. Production: 'download' (open-access PDFs by DOI) and "
        "'ingest' (a PDF you already have). Reading PDFs ('extract', "
        "'extract-run') and E1 'acquire' are parked; their help says so."
    )
)
console = Console()


def _refuse(code: str, message: str) -> None:
    """Print a refusal that names its decision and stop with exit code 1."""
    console.print(f"[bold red]{code}:[/bold red] {message}", soft_wrap=True)
    raise typer.Exit(1)


def _production_preflight(proxy: str | None) -> None:
    """What ``download`` and ``ingest`` refuse before any request (K0, M12a item 27)."""
    if (proxy or "").strip() or settings.proxy_url.strip():
        _refuse(
            "PROXY_REFUSED",
            "an institutional proxy is not used by the production download commands "
            f"({DECISION} item 25). Remove --proxy and PROXY_URL and run again.",
        )
    if settings.enable_publisher_direct_patterns:
        _refuse(
            "PUBLISHER_PATTERNS_REFUSED",
            "the publisher direct-PDF patterns (guessed publisher URLs) are removed "
            f"({DECISION} item 24). Remove ENABLE_PUBLISHER_DIRECT_PATTERNS and run again.",
        )
    if not contact_email():
        _refuse("MAILTO_NOT_SET", str(MailtoNotSetError()).split(": ", 1)[1])

_ACQUISITION_EXIT_CODES = {
    OperationStatus.SUCCESS: 0,
    OperationStatus.PARTIAL: 2,
    OperationStatus.FAILED: 1,
    OperationStatus.CANCELLED: 130,
}

# ``download`` (H-pdf-resolver-locations): the reason a DOI has no file, in the
# table and in the exit code. With several DOIs the exit code is the first of
# these that any DOI met, in this order; 1 stays "a listed address gave no PDF"
# and any other failure. 2 is left to Typer's usage errors.
_UNRESOLVED_LABELS = {
    LOOKUP_FAILED: "[red]Lookup failed[/red]",
    PDF_NOT_FETCHED: "[red]Failed[/red]",
    OPEN_NO_DIRECT_PDF: "[yellow]No direct PDF[/yellow]",
    NO_OPEN_COPY_LISTED: "[yellow]No open copy[/yellow]",
}
_DOWNLOAD_EXIT_CODES = {LOOKUP_FAILED: 3, OPEN_NO_DIRECT_PDF: 4, NO_OPEN_COPY_LISTED: 5}


def _download_exit_code(results: list) -> int:
    """0 when every DOI has its file; otherwise 3, 1, 4 or 5 (see the table above)."""
    failed = [res for res in results if not res.success]
    if not failed:
        return 0
    outcomes = {res.outcome for res in failed}
    if LOOKUP_FAILED in outcomes:
        return _DOWNLOAD_EXIT_CODES[LOOKUP_FAILED]
    if outcomes - set(_DOWNLOAD_EXIT_CODES):
        return 1
    if OPEN_NO_DIRECT_PDF in outcomes:
        return _DOWNLOAD_EXIT_CODES[OPEN_NO_DIRECT_PDF]
    return _DOWNLOAD_EXIT_CODES[NO_OPEN_COPY_LISTED]


def _write_json_atomic(path: Path, payload: str) -> None:
    """Write a CLI summary without exposing a partially written JSON file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _print_acquisition_human(outcome) -> None:
    """Render the canonical envelope without changing its status values."""

    table = Table(title="PDF Acquisition")
    table.add_column("Study", style="cyan")
    table.add_column("Acquisition", style="bold")
    table.add_column("Access")
    table.add_column("Document")
    table.add_column("Diagnostic")
    for item in outcome.data.item_outcomes:
        diagnostic = item.error.code if item.error is not None else ""
        if not diagnostic and item.warning is not None:
            diagnostic = item.warning.code
        table.add_row(
            item.study_id,
            item.acquisition_status.value,
            item.access_status.value,
            item.document_id or "-",
            diagnostic,
        )
    console.print(table)
    console.print(f"Operation status: {outcome.status.value}")
    reference = outcome.data.manifest_reference
    if reference is not None:
        console.print(
            f"Manifest: {reference.manifest_id} ({reference.workspace_relative_path})"
        )
    for error in outcome.errors:
        console.print(f"[red]{error.code}:[/red] {error.message}")


def _print_extraction_human(outcome) -> None:
    """Render the canonical E2 envelope without changing its status values."""

    table = Table(title="PDF Text Extraction (WP01-E2)")
    table.add_column("Study", style="cyan")
    table.add_column("Extraction")
    table.add_column("Content")
    table.add_column("Document")
    table.add_column("Engine")
    table.add_column("Diagnostic")
    for item in outcome.data.item_outcomes:
        diagnostic = item.error.code if item.error is not None else ""
        if not diagnostic and item.warning is not None:
            diagnostic = item.warning.code
        # The engine that actually produced the outcome: an item outcome exposes
        # `effective_engine` (the committed engine) and falls back to the
        # requested one when the chain never reached an effective engine.
        engine = item.effective_engine or item.requested_engine or "-"
        table.add_row(
            item.study_id,
            item.extraction_status.value,
            item.content_status.value if item.content_status is not None else "-",
            item.document_id or "-",
            engine,
            diagnostic,
        )
    console.print(table)
    console.print(f"Operation status: {outcome.status.value}")
    reference = outcome.data.manifest_reference
    if reference is not None:
        console.print(
            f"Sidecar: {reference.manifest_id} ({reference.workspace_relative_path})"
        )
    # `ExtractionOperationData` exposes the candidate as `candidate`; there is no
    # `document_manifest_candidate` attribute, so naming the wrong one would raise
    # an AttributeError on every real run.
    candidate = outcome.data.candidate
    if candidate is not None:
        # A candidate is an in-memory payload, not a file: it has no workspace
        # path, so only its identity and payload checksum are reported.  The
        # kit never publishes it and never claims Contract acceptance.
        console.print(
            "Contract candidate: "
            f"{candidate.artifact_id} "
            f"payload_sha256={candidate.payload_sha256} "
            f"(NON-AUTHORITATIVE; acceptance={candidate.contract_acceptance})"
        )
    for error in outcome.errors:
        console.print(f"[red]{error.code}:[/red] {error.message}")


@app.command("extract-run")
def extract_run(
    config: Path = typer.Argument(
        ..., exists=True, readable=True, help="ExtractionRunConfig JSON input."
    ),
    audit_logger: Path = typer.Option(
        ...,
        "--audit-logger",
        exists=True,
        readable=True,
        help="Canonical workspace-manager log_event.py path.",
    ),
    output: Path = typer.Option(
        None, "--output", "-o", help="Optional path for the JSON summary."
    ),
    human: bool = typer.Option(
        False, "--human", help="Render a human table in addition to JSON output."
    ),
) -> None:
    """PARKED, not production (reading PDFs waits for M12b-read). Extract screened PDF text through the E2 domain service (authoritative)."""

    try:
        run_config = ExtractionRunConfig.model_validate_json(
            config.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, ValueError) as error:
        raise typer.BadParameter(
            f"could not read a valid ExtractionRunConfig: {error}"
        ) from error

    if not run_config.requests:
        raise typer.BadParameter("ExtractionRunConfig.requests must not be empty")

    audit_sink = WorkspaceManagerCliAuditSink(
        workspace_root=run_config.requests[0].workspace_root,
        logger_path=audit_logger,
    )
    service = PDFExtractionService.from_config(run_config, audit_sink=audit_sink)
    outcome = asyncio.run(service.extract(run_config.requests))
    serialized = outcome.model_dump_json(indent=2)
    if output is not None:
        _write_json_atomic(output, serialized)
    typer.echo(serialized)
    if human:
        _print_extraction_human(outcome)
    raise typer.Exit(code=_ACQUISITION_EXIT_CODES[outcome.status])


@app.command("acquire")
def acquire(
    config: Path = typer.Argument(
        ..., exists=True, readable=True, help="AcquisitionRunConfig JSON input."
    ),
    audit_logger: Path = typer.Option(
        ...,
        "--audit-logger",
        exists=True,
        readable=True,
        help="Canonical workspace-manager log_event.py path.",
    ),
    output: Path = typer.Option(
        None, "--output", "-o", help="Optional path for the JSON summary."
    ),
    human: bool = typer.Option(
        False, "--human", help="Render a human table in addition to JSON output."
    ),
) -> None:
    """PARKED, not production (E1 acquisition stays parked, M12a item 23). Acquire parent-bound PDFs through the E1 domain service."""

    try:
        run_config = AcquisitionRunConfig.model_validate_json(
            config.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, ValueError) as error:
        raise typer.BadParameter(
            f"could not read a valid AcquisitionRunConfig: {error}"
        ) from error

    audit_sink = WorkspaceManagerCliAuditSink(
        workspace_root=run_config.requests[0].workspace_root,
        logger_path=audit_logger,
    )
    service = PDFAcquisitionService.from_config(run_config, audit_sink=audit_sink)
    outcome = asyncio.run(service.acquire(run_config.requests))
    serialized = outcome.model_dump_json(indent=2)
    if output is not None:
        _write_json_atomic(output, serialized)
    typer.echo(serialized)
    if human:
        _print_acquisition_human(outcome)
    raise typer.Exit(code=_ACQUISITION_EXIT_CODES[outcome.status])


def _export_results(export_format: str, output_dir: Path, successful_results: list):
    """Helper to export results, appending to existing files if they exist."""
    if not successful_results:
        return

    export_path = output_dir / f"download_summary.{export_format}"

    if export_format.lower() == "json":
        export_data = []
        if export_path.exists():
            with (
                suppress(OSError, json.JSONDecodeError),
                open(export_path, "r", encoding="utf-8") as f,
            ):
                export_data = json.load(f)

        # Append new successful results, avoiding duplicate DOIs
        existing_dois = {item["doi"] for item in export_data}
        for res in successful_results:
            if res.doi not in existing_dois and res.metadata:
                export_data.append(
                    {
                        "doi": res.doi,
                        "file_path": str(res.file_path),
                        "metadata": res.metadata,
                    }
                )

        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)
        console.print(f"[green]Exported metadata to {export_path}[/green]")

    elif export_format.lower() == "bibtex":
        bibtex_entries = []
        for res in successful_results:
            if not res.metadata:
                continue
            md = res.metadata
            author = md.get("author", "Unknown")
            year = md.get("year", "Unknown")
            title = md.get("title", "Unknown")
            key = f"{author}{year}".replace(" ", "")
            bibtex = f"@article{{{key},\n  title={{{title}}},\n  author={{{author}}},\n  year={{{year}}},\n  doi={{{res.doi}}}\n}}\n"
            bibtex_entries.append(bibtex)

        with open(export_path, "a", encoding="utf-8") as f:
            f.write("\n".join(bibtex_entries) + "\n")
        console.print(f"[green]Exported BibTeX to {export_path}[/green]")
    else:
        console.print(
            f"[yellow]Unknown export format: {export_format}. Use 'json' or 'bibtex'.[/yellow]"
        )


@app.command("download")
def download(
    dois: list[str] = typer.Option(
        None,
        "--doi",
        "-d",
        help="Specific DOI to download (can be specified multiple times)",
    ),
    input_file: Path = typer.Option(
        None,
        "--input",
        "-i",
        help="JSON file containing results from scholar-search-kit",
    ),
    output_dir: Path = typer.Option(
        Path("downloads"), "--output", "-o", help="Directory to save PDFs"
    ),
    max_concurrent: int = typer.Option(
        5, "--max-concurrent", "-c", help="Maximum concurrent downloads"
    ),
    smart_names: bool = typer.Option(
        False, "--smart-names", help="Rename downloaded PDFs using Author_Year_Title"
    ),
    export_format: str = typer.Option(
        None,
        "--export",
        help="Export successfully downloaded metadata (json or bibtex)",
    ),
    proxy: str = typer.Option(
        None,
        "--proxy",
        help="Refused: an institutional proxy is not used (decision 2026-11-21, M12a item 25).",
    ),
    proxy_style: str = typer.Option(
        "auto", "--proxy-style", help="Parked; a proxy is refused (M12a item 25)."
    ),
    strict_validate: bool = typer.Option(
        False,
        "--strict-validate",
        help="Require pypdf structural validation of downloads",
    ),
):
    """Download open-access PDFs by DOI (OpenAlex and Unpaywall locations). Needs SCHOLAR_MAILTO.

    The best open copy listed with a direct PDF address is taken: published
    version first, then accepted manuscript, then submitted version or preprint.
    Exit codes: 0 every DOI has its file; 3 a lookup failed (run again later);
    1 a listed address gave no PDF; 4 listed as open access but with no direct
    PDF address; 5 no open copy listed.
    """

    _production_preflight(proxy)
    if proxy_style not in PROXY_STYLES:
        raise typer.BadParameter(
            f"--proxy-style must be one of {', '.join(PROXY_STYLES)}"
        )
    settings.download_dir = output_dir
    settings.max_concurrent_downloads = max_concurrent

    doi_list = list(dois) if dois else []

    # Parse input file if provided
    if input_file and input_file.exists():
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    doi = None
                    if "external_ids" in item and item["external_ids"].get("doi"):
                        doi = item["external_ids"]["doi"]
                    elif "doi" in item:
                        doi = item["doi"]

                    if doi and doi not in doi_list:
                        doi_list.append(doi)
        except (
            AttributeError,
            KeyError,
            OSError,
            TypeError,
            UnicodeError,
            ValueError,
        ) as e:
            console.print(f"[bold red]Error parsing input file:[/bold red] {e}")
            raise typer.Exit(1)

    if not doi_list:
        console.print("[bold yellow]No DOIs provided to download.[/bold yellow]")
        raise typer.Exit(0)

    console.print(
        f"[bold blue]Starting download process for {len(doi_list)} DOIs...[/bold blue]"
    )

    downloader = AsyncPDFDownloader(
        output_dir=output_dir,
        use_smart_names=smart_names,
        proxy_url=proxy,
        proxy_style=proxy_style,
        structural_validation=strict_validate,
    )

    async def run_downloads():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Downloading PDFs...", total=len(doi_list))

            import aiohttp
            from scholar_search.http_client import AcademicHttpClient

            results = []
            http_client = AcademicHttpClient(name="openalex-pdf", rate_limit=10)
            try:
                async with aiohttp.ClientSession() as session:
                    # We process concurrently but update progress bar as each finishes
                    tasks = [
                        downloader.process_doi(session, http_client, doi)
                        for doi in doi_list
                    ]
                    for coro in asyncio.as_completed(tasks):
                        res = await coro
                        results.append(res)
                        progress.advance(task)
            finally:
                await http_client.close()

            return results

    # Run the event loop
    results = asyncio.run(run_downloads())

    # Display summary
    table = Table(title="Download Summary")
    table.add_column("DOI", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details")

    success_count = 0
    for res in results:
        if res.success:
            success_count += 1
            details = escape(str(res.file_path))
            if res.open_copy is not None:
                # The copy taken, labelled (M12a answer F3): version, licence, source.
                details += f" ({escape(res.open_copy.label())}"
                if res.copies_tried > 1:
                    details += f"; address {res.copies_tried} of {res.copies_listed} listed"
                details += ")"
            table.add_row(res.doi, "[green]Success[/green]", details)
        elif res.outcome in _UNRESOLVED_LABELS:
            table.add_row(
                res.doi,
                _UNRESOLVED_LABELS[res.outcome],
                escape(res.error_message or ""),
            )
        elif res.access_status == "VERIFIED_OPEN_ACCESS":
            table.add_row(
                res.doi,
                "[red]Failed[/red]",
                res.error_message or "Open-access source could not be acquired",
            )
        elif res.access_status == "RESTRICTED_CONFIRMED":
            table.add_row(
                res.doi,
                "[red]Restricted[/red]",
                res.error_message or "Access restricted",
            )
        else:
            table.add_row(
                res.doi,
                "[yellow]Unresolved[/yellow]",
                res.error_message or "No legal-copy determination was made",
            )

    console.print(table)
    console.print(
        f"[bold green]Successfully downloaded {success_count}/{len(doi_list)} PDFs.[/bold green]"
    )

    if export_format:
        successful_results = [res for res in results if res.success]
        _export_results(export_format, output_dir, successful_results)
    if success_count != len(doi_list):
        raise typer.Exit(_download_exit_code(results))


@app.command("ingest")
def ingest(
    pdf_path: Path = typer.Argument(
        ..., help="Path to the manually downloaded PDF file"
    ),
    doi: str = typer.Option(..., "--doi", "-d", help="The DOI associated with the PDF"),
    output_dir: Path = typer.Option(
        Path("downloads"), "--output", "-o", help="Directory to save PDFs"
    ),
    smart_names: bool = typer.Option(
        False, "--smart-names", help="Rename downloaded PDF using Author_Year_Title"
    ),
    export_format: str = typer.Option(
        None, "--export", help="Export successfully ingested metadata (json or bibtex)"
    ),
    proxy: str = typer.Option(
        None,
        "--proxy",
        help="Refused: an institutional proxy is not used (decision 2026-11-21, M12a item 25).",
    ),
    proxy_style: str = typer.Option(
        "auto", "--proxy-style", help="Parked; a proxy is refused (M12a item 25)."
    ),
    strict_validate: bool = typer.Option(
        False, "--strict-validate", help="Require pypdf structural validation on ingest"
    ),
):
    """Ingest a PDF you already have for a DOI (metadata looked up). Needs SCHOLAR_MAILTO."""
    _production_preflight(proxy)
    if proxy_style not in PROXY_STYLES:
        raise typer.BadParameter(
            f"--proxy-style must be one of {', '.join(PROXY_STYLES)}"
        )
    settings.download_dir = output_dir

    console.print(f"[bold blue]Ingesting {pdf_path} for DOI {doi}...[/bold blue]")
    downloader = AsyncPDFDownloader(
        output_dir=output_dir,
        use_smart_names=smart_names,
        proxy_url=proxy,
        proxy_style=proxy_style,
        structural_validation=strict_validate,
    )

    async def run_ingest():
        from scholar_search.http_client import AcademicHttpClient

        http_client = AcademicHttpClient(name="openalex-pdf", rate_limit=10)
        try:
            return await downloader.ingest_pdf(http_client, pdf_path, doi)
        finally:
            await http_client.close()

    res = asyncio.run(run_ingest())

    failed_lookups = [
        look for look in res.lookups if look.state == LOOKUP_STATE_FAILED
    ]
    if failed_lookups:
        # The file is the researcher's own; only its looked-up metadata is missing.
        said = "; ".join(f"{look.name} {look.failure()}" for look in failed_lookups)
        console.print(
            f"[yellow]Metadata lookup incomplete: {said}.[/yellow]", soft_wrap=True
        )
    if res.success:
        console.print(
            f"[bold green]Successfully ingested PDF to {res.file_path}[/bold green]"
        )
        if export_format:
            _export_results(export_format, output_dir, [res])
    else:
        console.print(f"[bold red]Failed to ingest PDF: {res.error_message}[/bold red]")


@app.command("extract")
def extract(
    pdf_path: Path = typer.Argument(
        ..., help="Path to the PDF file or directory of PDFs"
    ),
    output_dir: Path = typer.Option(
        Path("markdown"),
        "--output",
        "-o",
        help="Directory to save the extracted Markdown",
    ),
    engine: str = typer.Option("docling", help="Extraction engine: docling or grobid"),
    grobid_url: str = typer.Option(
        "http://localhost:8070", help="Grobid service URL if using grobid"
    ),
):
    """PARKED, not production (reading PDFs waits for M12b-read). LEGACY, NON-AUTHORITATIVE: extract raw Markdown from a PDF.

    This command writes to an arbitrary output directory and produces no
    acquisition/extraction lineage, no bound frontmatter, and no sidecar
    manifest. It can never write the authoritative `extracted/<document_id>.md`
    contract path. Use `extract-run` for the WP01-E2 deterministic pipeline.
    """

    console.print(
        "[bold yellow]Warning:[/bold yellow] 'extract' is non-authoritative. "
        "Outputs are unversioned and untraceable to a screened document. "
        "Use 'extract-run' for the WP01-E2 deterministic pipeline."
    )
    if not pdf_path.exists():
        console.print(f"[red]Path does not exist: {pdf_path}[/red]")
        raise typer.Exit(1)

    pdfs = []
    if pdf_path.is_file() and pdf_path.suffix.lower() == ".pdf":
        pdfs.append(pdf_path)
    elif pdf_path.is_dir():
        pdfs.extend(list(pdf_path.glob("*.pdf")))
    else:
        console.print(
            "[red]Input must be a PDF file or a directory containing PDFs.[/red]"
        )
        raise typer.Exit(1)

    if not pdfs:
        console.print("[yellow]No PDFs found.[/yellow]")
        raise typer.Exit(0)

    console.print(
        f"[bold blue]Extracting {len(pdfs)} PDFs using {engine}...[/bold blue]"
    )

    success = 0
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Extracting...", total=len(pdfs))

        for pdf in pdfs:
            progress.update(task, description=f"Extracting {pdf.name}...")
            try:
                if engine.lower() == "docling":
                    out = DoclingEngine.extract_markdown(pdf, output_dir)
                    console.print(f"[green]Extracted {pdf.name} -> {out}[/green]")
                elif engine.lower() == "grobid":
                    out = GrobidEngine.extract_markdown(pdf, output_dir, grobid_url)
                    console.print(f"[green]Extracted {pdf.name} -> {out}[/green]")
                else:
                    console.print(f"[red]Unknown engine: {engine}[/red]")
                    raise typer.Exit(1)
                success += 1
            except Exception as e:  # noqa: BLE001 - report each extractor failure
                console.print(f"[red]Failed to extract {pdf.name}: {e}[/red]")
            finally:
                progress.advance(task)

    console.print(
        f"[bold green]Successfully extracted {success}/{len(pdfs)} files to {output_dir}.[/bold green]"
    )


if __name__ == "__main__":
    app()
