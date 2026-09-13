"""scholar-verify CLI: post-screening trust verification for a workspace.

Commands mirror the Phase 4 analytical workstreams:
  ingress       merge included.json/excluded.json -> audit-clean corpus (unified)
  retraction    OpenAlex + Crossref retraction/status check
  open-science  DAS/CAS regex baseline over extracted fulltext
  coi           conflict-of-interest audit aggregator
  risk-of-bias  deterministic QUADAS-2/PROBAST scoring over records.json
  trust-context annotate consensus clusters with Phase-4 trust context
  all           run every verification stream sequentially
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

import typer

from . import coi, open_science, retraction, risk_of_bias, trust_context, verbatim

app = typer.Typer(help="Verify the trustworthiness of a screened corpus (retraction status, open-science artifacts, COI, risk of bias).")


def _resolve_workspace(workspace: Path) -> Path:
    ws = workspace.resolve()
    if not (ws / "protocol.json").exists() and not (ws / "INDEX.md").exists():
        raise typer.BadParameter(f"not a Nexus Scholar workspace (missing protocol.json/INDEX.md): {ws}")
    return ws


def _load(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise typer.Exit(f"missing required input: {path} ({label})")
    except json.JSONDecodeError as exc:
        raise typer.Exit(f"invalid JSON in {path}: {exc}")


def _write(ws: Path, name: str, data: dict[str, Any], md: str) -> None:
    out_dir = ws / "phase4"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / f"{name}.md").write_text(md, encoding="utf-8")
    typer.echo(f"wrote {out_dir / name}.json + .md")


def _slug(text: str) -> str:
    return "".join(ch for ch in text if ch.isalnum() or ch in "-_") or "scoped"


def _merged_records(ws: Path) -> list[dict[str, Any]]:
    return _load(ws / "literature" / "extraction" / "merged" / "records.json", "merged records")


def _manifest(ws: Path) -> list[dict[str, Any]]:
    return _load(ws / "phase4" / "_manifest.json", "phase4 manifest")


def _confirm_overwrite(ws: Path, name: str) -> None:
    target = ws / "phase4" / f"{name}.json"
    if target.exists() and not typer.confirm(f"Overwrite existing {target.name}?", default=True):
        raise typer.Exit(0)


@app.callback()
def _cb() -> None:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


@app.command("retraction")
def retraction_cmd(
    workspace: Path = typer.Option(..., "--workspace", "-w", help="Workspace directory", callback=_resolve_workspace),
    records: Path = typer.Option(None, "--records", help="Override canonical records.json path"),
    included: Path = typer.Option(None, "--included", help="Override included.json path"),
    sleep_s: float = typer.Option(0.2, "--sleep", help="Seconds between API calls"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Do not write output files"),
    yes: bool = typer.Option(False, "--yes", help="Skip overwrite confirmation"),
) -> None:
    """Check every canonical record for retraction / correction signals (OpenAlex + Crossref)."""
    rec_path = records or workspace / "literature" / "extraction" / "merged" / "records.json"
    inc_path = included or workspace / "literature" / "included.json"
    recs = _load(rec_path, "records")
    inc = _load(inc_path, "included")
    if not yes:
        _confirm_overwrite(workspace, "retraction_status_check")
    checker = retraction.RetractionChecker(sleep_s=sleep_s)
    out = checker.check(recs, inc)
    md = retraction.render_retraction_report(out)
    typer.echo(json.dumps(out["summary"], indent=2, ensure_ascii=False))
    if not dry_run:
        _write(workspace, "retraction_status_check", out, md)


@app.command("open-science")
def open_science_cmd(
    workspace: Path = typer.Option(..., "--workspace", "-w", help="Workspace directory", callback=_resolve_workspace),
) -> None:
    """Run the deterministic DAS/CAS regex baseline over extracted fulltext."""
    ws = workspace
    _confirm_overwrite(ws, "open_science_regex_baseline")
    recs = _merged_records(ws)
    extracted = ws / "extracted"
    out = open_science.run(recs, extracted)
    md = open_science.render_report(out)
    typer.echo(json.dumps(out["summary"], indent=2, ensure_ascii=False))
    _write(ws, "open_science_regex_baseline", out, md)


@app.command("coi")
def coi_cmd(
    workspace: Path = typer.Option(..., "--workspace", "-w", help="Workspace directory", callback=_resolve_workspace),
    chunks_dir: Path = typer.Option(None, "--chunks", help="Override _agent_results chunk directory"),
) -> None:
    """Aggregate analyst COI classifications into the canonical coi_audit output."""
    ws = workspace
    _confirm_overwrite(ws, "coi_audit")
    manifest = _manifest(ws)
    cdir = chunks_dir or (ws / "phase4" / "_agent_results")
    chunks = coi.load_chunks(cdir)
    out = coi.run(manifest, chunks)
    md = coi.render_report(out)
    typer.echo(json.dumps(out["summary"], indent=2, ensure_ascii=False))
    _write(ws, "coi_audit", out, md)


@app.command("risk-of-bias")
def risk_of_bias_cmd(
    workspace: Path = typer.Option(..., "--workspace", "-w", help="Workspace directory", callback=_resolve_workspace),
) -> None:
    """Score deterministic QUADAS-2/PROBAST risk-of-bias over canonical records."""
    ws = workspace
    _confirm_overwrite(ws, "risk_of_bias")
    recs = _merged_records(ws)
    manifest = _manifest(ws)
    out = risk_of_bias.run(recs, manifest)
    md = risk_of_bias.render_report(out)
    typer.echo(json.dumps(out["summary"], indent=2, ensure_ascii=False))
    _write(ws, "risk_of_bias", out, md)


@app.command("trust-context")
def trust_context_cmd(
    workspace: Path = typer.Option(..., "--workspace", "-w", help="Workspace directory", callback=_resolve_workspace),
    consensus: Path | None = typer.Option(None, "--consensus", help="Override consensus.json path"),
    risk_of_bias: Path | None = typer.Option(None, "--risk-of-bias", help="Override risk_of_bias.json path"),
    coi: Path | None = typer.Option(None, "--coi", help="Override coi_audit.json path"),
    retraction: Path | None = typer.Option(None, "--retraction", help="Override retraction_status_check.json path"),
    open_science: Path | None = typer.Option(None, "--open-science", help="Override open_science_regex_baseline.json path"),
    rq_id: str | None = typer.Option(None, "--rq-id", help="Scope report to clusters whose claims belong to this RQ (e.g. RQ1)"),
    claims_dir: Path | None = typer.Option(None, "--claims-dir", help="Override dir of claims_rq*.json used for RQ attribution"),
    output_json: Path | None = typer.Option(None, "--output-json", help="JSON output path (default <ws>/phase4/trust_consensus[_RQ].json)"),
    output_md: Path | None = typer.Option(None, "--output-md", help="Markdown output path (default <ws>/phase4/trust_consensus[_RQ].md)"),
) -> None:
    """Annotate Consensus Cartographer clusters with Phase-4 trust context (optionally per RQ)."""
    ws = _resolve_workspace(workspace)
    cons_path = consensus or (ws / trust_context.CONSENSUS_DEFAULT)
    cons = _load(cons_path, "consensus report")

    phase4_dir = ws / "phase4"
    overrides = {
        "risk_of_bias": risk_of_bias,
        "coi": coi,
        "retraction": retraction,
        "open_science": open_science,
    }
    phase4 = {}
    for key, default_fname in trust_context.PHASE4_INPUTS.items():
        p = overrides.get(key) or (phase4_dir / default_fname)
        if p.exists():
            phase4[key] = trust_context._rows(_load(p, f"phase4/{default_fname}"))

    cdir = claims_dir or (ws / "synthesis")
    claims_by_rq = trust_context.load_rq_claims(cdir) if cdir.exists() else {}

    annotated = trust_context.annotate(cons, phase4, rq_id=rq_id, claims_by_rq=claims_by_rq)
    md = trust_context.render_report(annotated)

    out_dir = ws / "phase4"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"trust_consensus_{_slug(rq_id)}" if rq_id else "trust_consensus"
    (output_json or (out_dir / f"{stem}.json")).write_text(
        json.dumps(annotated, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (output_md or (out_dir / f"{stem}.md")).write_text(md, encoding="utf-8")
    typer.echo(json.dumps(annotated.get("trust_level_counts", {}), indent=2, ensure_ascii=False))
    typer.echo(annotated.get("total_groups"))
    typer.echo(f"wrote {out_dir / stem}.json + .md")


@app.command("all")
def all_cmd(
    workspace: Path = typer.Option(..., "--workspace", "-w", help="Workspace directory", callback=_resolve_workspace),
    sleep_s: float = typer.Option(0.2, "--sleep", help="Seconds between API calls"),
    skip_retraction: bool = typer.Option(False, "--skip-retraction", help="Do not hit external APIs"),
) -> None:
    """Run the full Phase-4 verification sequence against the workspace."""
    ws = workspace
    recs = _merged_records(ws)
    manifest = _manifest(ws)

    if not skip_retraction:
        inc_path = ws / "literature" / "included.json"
        inc = _load(inc_path, "included")
        checker = retraction.RetractionChecker(sleep_s=sleep_s)
        out = checker.check(recs, inc)
        _write(ws, "retraction_status_check", out, retraction.render_retraction_report(out))

    out = open_science.run(recs, ws / "extracted")
    _write(ws, "open_science_regex_baseline", out, open_science.render_report(out))

    chunks = coi.load_chunks(ws / "phase4" / "_agent_results")
    out2 = coi.run(manifest, chunks)
    _write(ws, "coi_audit", out2, coi.render_report(out2))

    out3 = risk_of_bias.run(recs, manifest)
    _write(ws, "risk_of_bias", out3, risk_of_bias.render_report(out3))


@app.command("verbatim-claims")
def verbatim_claims_cmd(
    claims_file: Path = typer.Option(..., "--claims", "-c", help="Path to claims JSON file (e.g. synthesis/claims.json)"),
    extracted_dir: Path = typer.Option(..., "--extracted", "-e", help="Directory with extracted markdown files"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Path to write verification report JSON"),
    threshold: float = typer.Option(0.90, "--threshold", "-t", help="Coverage threshold for verbatim match"),
) -> None:
    """Verify synthesis claims against extracted full-text documents via verbatim window/ngram matching."""
    if not claims_file.exists():
        raise typer.BadParameter(f"Claims file not found: {claims_file}")
    if not extracted_dir.exists():
        raise typer.BadParameter(f"Extracted directory not found: {extracted_dir}")

    claims = json.loads(claims_file.read_text(encoding="utf-8"))
    if not isinstance(claims, list):
        raise typer.BadParameter("Claims file must contain a JSON list")

    source_texts: dict[str, str] = {}
    for md_file in extracted_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8", errors="replace")
        # Map by stem, full name, and potential SCI-xxxx in file or metadata
        source_texts[md_file.stem] = content
        m = re.search(r"workspace_id:\s*['\"]?(SCI-\d+)['\"]?", content)
        if m:
            source_texts[m.group(1)] = content
        # Also check study_id or filename patterns
        m_id = re.search(r"(SCI-\d+)", md_file.name)
        if m_id:
            source_texts[m_id.group(1)] = content

    verifier = verbatim.VerbatimClaimVerifier(threshold=threshold)
    results, metrics = verifier.verify_claims_ledger(claims, source_texts)

    typer.echo(f"Verified {metrics['verified_claims']}/{metrics['total_claims']} claims ({metrics['verification_rate']*100:.1f}%) at threshold {threshold}")

    if output:
        out_data = {
            "metrics": metrics,
            "results": [r.__dict__ for r in results]
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(out_data, indent=2, ensure_ascii=False), encoding="utf-8")
        typer.echo(f"Report written to {output}")


if __name__ == "__main__":
    app()

