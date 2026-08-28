"""Helper script to initialize a standardized research project workspace."""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

def slugify(text: str) -> str:
    """Converts a title to a clean URL/filesystem friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")

def init_project(
    workspace_root: Path,
    title: str,
    slug: str | None = None,
    description: str = "",
    research_questions: list[str] | None = None,
    keywords: list[str] | None = None
) -> Path:
    project_slug = slug or slugify(title)
    project_dir = workspace_root / "workspaces" / project_slug

    # Subdirectories
    subdirs = ["audit", "literature", "pdfs", "extracted", "synthesis", "exports"]
    for sub in subdirs:
        (project_dir / sub).mkdir(parents=True, exist_ok=True)

    # Initial project.json manifest
    now = datetime.now(timezone.utc).isoformat()
    manifest = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "project_id": project_slug,
        "title": title,
        "description": description or f"Systematic literature review for {title}",
        "created_at": now,
        "updated_at": now,
        "status": "active",
        "research_questions": research_questions or [],
        "keywords": keywords or [],
        "stats": {
            "discovered_papers": 0,
            "verified_papers": 0,
            "downloaded_pdfs": 0,
            "extracted_markdowns": 0
        }
    }

    manifest_path = project_dir / "project.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Create an initial synthesis notes template
    notes_path = project_dir / "synthesis" / "literature_review.md"
    if not notes_path.exists():
        rq_section = "\n".join([f"- **{rq}**" for rq in (research_questions or ["RQ1: Primary research questions to be formulated."])])
        notes_content = f"# Literature Review: {title}\n\n## Objectives & Research Questions\n{rq_section}\n\n## Findings & Synthesis\n*To be generated from extracted papers.*\n"
        notes_path.write_text(notes_content, encoding="utf-8")

    # Import logger if available to log event and build INDEX.md
    try:
        from log_event import log_project_event
        log_project_event(
            project_path_or_slug=project_dir,
            action="PROJECT_INITIALIZED",
            agent_or_tool="workspace-manager",
            description=f"Initialized research project workspace for '{title}'",
            outputs=["project.json", "synthesis/literature_review.md"],
            parameters={"title": title, "slug": project_slug, "rqs": research_questions or []}
        )
    except Exception:
        pass

    print(f"Initialized research project: {project_dir}")
    return project_dir

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize a new research project workspace.")
    parser.add_argument("title", help="Human-readable project title")
    parser.add_argument("--slug", "-s", help="Optional custom project directory slug")
    parser.add_argument("--description", "-d", default="", help="Project description")
    parser.add_argument("--rq", action="append", help="Research question (can be repeated)")
    parser.add_argument("--keyword", "-k", action="append", help="Project keyword (can be repeated)")
    parser.add_argument("--root", default=".", help="Root repository directory (default: current directory)")

    args = parser.parse_args()
    init_project(
        workspace_root=Path(args.root),
        title=args.title,
        slug=args.slug,
        description=args.description,
        research_questions=args.rq,
        keywords=args.keyword
    )
