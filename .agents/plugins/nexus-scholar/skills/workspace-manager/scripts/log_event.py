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
        ("SCREENING_CRITERIA.md", "Rendered PRISMA Inclusion / Exclusion screening rules", "Configured"),
        ("literature/raw_search.json", "Raw federated literature search hits", "Discovered"),
        ("literature/deduped.json", "Deduplicated unique candidate papers", "Deduplicated"),
        ("literature/verified.json", "Hydrated bibliographic records with DOIs & abstracts", "Verified"),
        ("literature/included.json", "Screened eligible studies for full-text synthesis", "Included"),
        ("literature/excluded.json", "Excluded studies with logged decision reasons", "Excluded"),
        ("literature/prisma_screening_report.md", "PRISMA flow diagram and axis synthesis report", "Generated"),
        ("exports/search_summary.csv", "Tabular raw literature export", "Exported"),
        ("exports/verified_summary.csv", "Clean verified bibliography spreadsheet", "Exported"),
        ("exports/screening_decisions.csv", "Full title & abstract screening decisions spreadsheet", "Exported"),
        ("synthesis/literature_review.md", "Synthesis document & literature review draft", "In Progress"),
    ]

    for rel_path, desc, default_status in key_files:
        p = project_dir / rel_path
        if p.exists():
            mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime, tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
            catalog_entries.append(f"| `{rel_path}` | {desc} | {mtime} | {default_status} |")

    # Check for PDFs and extracted files
    pdf_count = len(list((project_dir / "pdfs").glob("*.pdf"))) if (project_dir / "pdfs").exists() else 0
    extracted_count = len(list((project_dir / "extracted").glob("*.md"))) if (project_dir / "extracted").exists() else 0

    if pdf_count > 0:
        catalog_entries.append(f"| `pdfs/` | Downloaded Open Access full-text PDF documents ({pdf_count} files) | Active | Downloaded |")
    if extracted_count > 0:
        catalog_entries.append(f"| `extracted/` | Docling full-text structured Markdown extractions ({extracted_count} files) | Active | Extracted |")

    index_content = f"""# Project Index: {title}

- **Project Slug**: `{slug}`
- **Last Updated**: `{now_iso}`
- **Project Status**: `{manifest.get("status", "active").upper()}`

---

## 📊 Summary Metrics
- **Discovered Papers**: {stats.get("discovered_papers", 0)}
- **Verified Papers**: {stats.get("verified_papers", 0)}
- **Downloaded PDFs**: {stats.get("downloaded_pdfs", pdf_count)}
- **Extracted Markdowns**: {stats.get("extracted_markdowns", extracted_count)}

---

## 🎯 Research Questions
"""
    for i, rq in enumerate(manifest.get("research_questions", []), 1):
        index_content += f"{i}. **RQ{i}**: {rq}\n"

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
