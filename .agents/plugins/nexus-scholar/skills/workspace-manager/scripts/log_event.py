"""Helper script and API to log events to a project's append-only audit journal and refresh INDEX.md."""

import argparse
import datetime
import json
import uuid
from pathlib import Path
from typing import Any


def refresh_index_md(project_dir: Path) -> Path:
    """Regenerates or updates the project's INDEX.md file based on current files and project.json."""
    manifest_path = project_dir / "project.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            pass

    title = manifest.get("title", project_dir.name)
    slug = manifest.get("project_id", project_dir.name)
    stats = manifest.get("stats", {})
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    catalog_entries = []
    
    # Check key files
    key_files = [
        ("project.json", "Project manifest, metadata, and research questions", "Active"),
        ("INDEX.md", "Master project directory and status catalog", "Synced"),
        ("audit/journal.jsonl", "Append-only provenance event ledger", "Active"),
        ("literature/criteria.md", "PRISMA Inclusion / Exclusion screening rules", "Configured"),
        ("literature/raw_search.json", "Raw federated literature search hits", "Discovered"),
        ("literature/deduped.json", "Deduplicated unique candidate papers", "Deduplicated"),
        ("literature/verified.json", "Hydrated bibliographic records with DOIs & abstracts", "Verified"),
        ("literature/included.json", "Screened eligible studies for full-text synthesis", "Included"),
        ("literature/excluded.json", "Excluded studies with logged decision reasons", "Excluded"),
        ("literature/screening/dual_screening_reliability_report.md", "Inter-rater reliability audit report", "Audited"),
        ("literature/screening/adjudicated_caveats.json", "Provisional caveat papers tracked for Stage 3 verification", "Provisioned"),
        ("literature/conflicts.json", "Complete ledger of inter-rater disputes & adjudications", "Adjudicated"),
        ("literature/conflict_adjudication_log.md", "Traceable adjudication narrative & dispute ledger", "Adjudicated"),
        ("literature/prisma_screening_report.md", "PRISMA flow diagram and systematic screening report", "Generated"),
        ("literature/prisma_report.json", "Structured JSON companion to PRISMA flow report", "Generated"),
        ("literature/screening/_clean_corpus_ids.json", "Post-audit clean corpus study ids", "Audited"),
        ("literature/screening/_audit_combined.json", "Full-text compliance audit verdicts", "Audited"),
        ("literature/extraction/SCHEMA.md", "Dual-route extraction schema contract", "Contracted"),
        ("literature/extraction/route_A/route_A_batch1.json", "Route A batch extractions", "Extracted"),
        ("literature/extraction/route_B/route_B_index.json", "Route B per-study extractions + index", "Extracted"),
        ("literature/extraction/compare/comparison_report.md", "Route A vs Route B comparison report", "Compared"),
        ("literature/extraction/adjudication/verdicts_all.json", "Adjudicated extraction conflicts", "Adjudicated"),
        ("literature/extraction/merged/records.json", "Canonical merged extraction dataset (per-value provenance quotes)", "Merged"),
        ("exports/search_summary.csv", "Tabular raw literature export", "Exported"),
        ("exports/verified_summary.csv", "Clean verified bibliography spreadsheet", "Exported"),
        ("exports/screening_decisions.csv", "Full title & abstract screening decisions spreadsheet", "Exported"),
        ("synthesis/synthesis_matrix.csv", "Verified one-row-per-study synthesis matrix", "Generated"),
        ("synthesis/synthesis_matrix.json", "Machine-readable synthesis matrix", "Generated"),
        ("synthesis/synthesis_stats.json", "Reproducible RQ1/RQ2 descriptive statistics", "Generated"),
        ("synthesis/build_synthesis.py", "Reproducible matrix + stats generator", "Generated"),
        ("synthesis/literature_review.md", "Synthesis document & literature review", "Final" if stats.get("synthesis_verified") else "In Progress"),
    ]

    for rel_path, desc, default_status in key_files:
        p = project_dir / rel_path
        if p.exists():
            mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime, tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
            catalog_entries.append(f"| `{rel_path}` | {desc} | {mtime} | {default_status} |")

    # Dynamic scan of reports/*.md
    reports_dir = project_dir / "reports"
    if reports_dir.exists():
        for r_file in sorted(reports_dir.glob("*.md")):
            rel_path = f"reports/{r_file.name}"
            mtime = datetime.datetime.fromtimestamp(r_file.stat().st_mtime, tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
            catalog_entries.append(f"| `{rel_path}` | Formal methodology or audit report | {mtime} | Audited |")

    # Check for PDFs and extracted files
    pdf_count = len(list((project_dir / "pdfs").glob("*.pdf"))) if (project_dir / "pdfs").exists() else 0
    extracted_count = len(list((project_dir / "extracted").glob("*.md"))) if (project_dir / "extracted").exists() else 0

    if pdf_count > 0:
        catalog_entries.append(f"| `pdfs/` | Downloaded Open Access full-text PDF documents ({pdf_count} files) | Active | Downloaded |")
    if extracted_count > 0:
        catalog_entries.append(f"| `extracted/` | Docling full-text structured Markdown extractions ({extracted_count} files) | Active | Extracted |")

    metrics_block = f"""- **Discovered Papers**: {stats.get("discovered_papers", 0)}
- **Verified Papers**: {stats.get("verified_papers", 0)}"""
    if "screened_papers" in stats:
        metrics_block += f"\n- **Screened Papers**: {stats.get('screened_papers', 0)}"
    if "included_papers" in stats:
        metrics_block += f"\n- **Full-Text Eligible Candidates**: {stats.get('included_papers', 0)}"
    if "confirmed_inclusions" in stats and "provisional_caveats" in stats:
        metrics_block += f" ({stats.get('confirmed_inclusions')} Confirmed + {stats.get('provisional_caveats')} Provisional Caveats)"
    if "excluded_papers" in stats:
        metrics_block += f"\n- **Confirmed Excluded Studies**: {stats.get('excluded_papers', 0)}"
    metrics_block += f"""
- **Downloaded PDFs**: {stats.get("downloaded_pdfs", pdf_count)}
- **Extracted Markdowns**: {stats.get("extracted_markdowns", extracted_count)}"""
    if "audited_clean_corpus" in stats or "merged_records" in stats:
        if "audited_clean_corpus" in stats:
            metrics_block += f"\n- **Post-Audit Clean Corpus**: {stats.get('audited_clean_corpus')} studies"
            if "audit_removed" in stats:
                metrics_block += f" ({stats.get('audit_removed')} scope violations removed)"
        if "merged_records" in stats:
            metrics_block += f"\n- **Merged Canonical Records**: {stats.get('merged_records')}"
            counts = []
            if "rq1_metric_studies" in stats:
                counts.append(f"{stats.get('rq1_metric_studies')} with \u22651 RQ1 segmentation metric")
            if "runtime_studies" in stats:
                counts.append(f"{stats.get('runtime_studies')} with on-device runtime")
            if "true_edge_studies" in stats:
                counts.append(f"{stats.get('true_edge_studies')} true embedded edge")
            if counts:
                metrics_block += " (" + "; ".join(counts) + ")"

    index_content = f"""# Project Index: {title}

- **Project Slug**: `{slug}`
- **Last Updated**: `{now_iso}`
- **Project Status**: `{manifest.get("status", "active").upper()}`

---

## 📊 Summary Metrics
{metrics_block}

---

## 🎯 Research Questions
"""
    for i, rq in enumerate(manifest.get("research_questions", []), 1):
        clean_rq = rq if not rq.startswith(f"RQ{i}:") else rq.split(":", 1)[1].strip()
        index_content += f"{i}. **RQ{i}**: {clean_rq}\n"

    index_content += f"""
---

## 📂 Project File Catalog

| File / Directory | Description | Last Modified | Status |
| :--- | :--- | :--- | :--- |
"""
    for entry in catalog_entries:
        index_content += f"{entry}\n"

    index_content += """
---
*Note: This file is automatically maintained by the `workspace-manager` event logger.*
"""

    index_path = project_dir / "INDEX.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content.strip() + "\n")

    return index_path


def log_project_event(
    project_path_or_slug: str | Path,
    action: str,
    agent_or_tool: str,
    description: str,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    parameters: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    status: str = "SUCCESS",
) -> dict[str, Any]:
    """Appends an event record to audit/journal.jsonl and refreshes INDEX.md."""
    path = Path(project_path_or_slug)
    if not path.is_dir() or not (path / "project.json").exists():
        # Try resolving inside workspaces/
        candidate = Path("workspaces") / str(project_path_or_slug)
        if candidate.is_dir():
            path = candidate

    audit_dir = path / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    journal_path = audit_dir / "journal.jsonl"

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    event_id = f"EVT-{now_utc.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

    event = {
        "timestamp": now_utc.isoformat(),
        "event_id": event_id,
        "action": action.upper(),
        "agent_or_tool": agent_or_tool,
        "description": description,
        "parameters": parameters or {},
        "inputs": inputs or [],
        "outputs": outputs or [],
        "metrics": metrics or {},
        "status": status.upper(),
    }

    # Append to journal
    with open(journal_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    # Update project.json updated_at
    manifest_path = path / "project.json"
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            manifest["updated_at"] = now_utc.isoformat()
            if metrics:
                for k, v in metrics.items():
                    if k in manifest.get("stats", {}):
                        manifest["stats"][k] = v
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
        except Exception:
            pass

    # Refresh INDEX.md
    refresh_index_md(path)

    print(f"Logged event [{action}] ({event_id}) -> {journal_path}")
    return event


def main():
    parser = argparse.ArgumentParser(description="Log an event to the project's append-only audit journal.")
    parser.add_argument("project", help="Project slug or directory path (e.g. avarel-fuse-multispectral)")
    parser.add_argument("--action", required=True, help="Action name (e.g. DISCOVERY_SEARCH, VERIFICATION)")
    parser.add_argument("--agent", default="agent", help="Agent or tool name (e.g. scholar-search-kit)")
    parser.add_argument("--description", default="", help="Human-readable event description")
    parser.add_argument("--inputs", nargs="*", default=[], help="Input files or identifiers")
    parser.add_argument("--outputs", nargs="*", default=[], help="Generated output files")
    parser.add_argument("--status", default="SUCCESS", help="Event status (SUCCESS/FAILED)")

    args = parser.parse_args()
    log_project_event(
        project_path_or_slug=args.project,
        action=args.action,
        agent_or_tool=args.agent,
        description=args.description,
        inputs=args.inputs,
        outputs=args.outputs,
        status=args.status,
    )


if __name__ == "__main__":
    main()
