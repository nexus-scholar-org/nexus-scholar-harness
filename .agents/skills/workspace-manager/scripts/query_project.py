#!/usr/bin/env python3
"""Query project state and audit trail."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def get_project_stats(project_dir: Path) -> dict[str, Any]:
    """Retrieve current project statistics."""
    manifest_path = project_dir / "project.json"
    
    if not manifest_path.exists():
        return {}
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    return manifest.get("stats", {})


def get_research_questions(project_dir: Path) -> list[str]:
    """Retrieve research questions."""
    manifest_path = project_dir / "project.json"
    
    if not manifest_path.exists():
        return []
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    return manifest.get("research_questions", [])


def get_events(
    project_dir: Path,
    action: str | None = None,
    agent: str | None = None,
    limit: int | None = None,
    reverse: bool = True,
) -> list[dict[str, Any]]:
    """Query events from journal.jsonl with optional filtering."""
    journal_path = project_dir / "audit" / "journal.jsonl"
    
    if not journal_path.exists():
        return []
    
    events = []
    with open(journal_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                
                # Apply filters
                if action and event.get("action", "").upper() != action.upper():
                    continue
                if agent and event.get("agent_or_tool", "").lower() != agent.lower():
                    continue
                
                events.append(event)
            except json.JSONDecodeError:
                pass
    
    # Sort by timestamp (newest first by default)
    if reverse:
        events.reverse()
    
    # Limit results
    if limit:
        events = events[:limit]
    
    return events


def export_audit_trail(
    project_dir: Path,
    output_file: Path | None = None,
) -> dict[str, Any]:
    """Export full audit trail for compliance."""
    journal_path = project_dir / "audit" / "journal.jsonl"
    
    events = []
    if journal_path.exists():
        with open(journal_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    
    manifest_path = project_dir / "project.json"
    metadata = {}
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        metadata = {
            "project_id": manifest.get("project_id"),
            "title": manifest.get("title"),
            "created_at": manifest.get("created_at"),
            "updated_at": manifest.get("updated_at"),
        }
    
    audit_export = {
        "metadata": metadata,
        "audit_trail": events,
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_events": len(events),
    }
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(audit_export, f, indent=2)
        print(f"✅ Audit trail exported to {output_file}")
    
    return audit_export


def resolve_project_dir(project_path_or_slug: str | Path) -> Path:
    """Resolve project directory from slug or path."""
    path = Path(project_path_or_slug)
    
    if path.is_dir() and (path / "project.json").exists():
        return path
    
    # Try inside workspaces/
    candidate = Path("workspaces") / str(project_path_or_slug)
    if candidate.is_dir() and (candidate / "project.json").exists():
        return candidate
    
    raise FileNotFoundError(f"Project not found: {project_path_or_slug}")


def main():
    parser = argparse.ArgumentParser(description="Query project state and audit trail.")
    parser.add_argument("project", help="Project slug or directory path")
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show project statistics",
    )
    parser.add_argument(
        "--events",
        action="store_true",
        help="Show recent events from audit trail",
    )
    parser.add_argument(
        "--action",
        type=str,
        help="Filter events by action name (e.g., DISCOVERY_SEARCH)",
    )
    parser.add_argument(
        "--agent",
        type=str,
        help="Filter events by agent/tool name",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Limit number of events returned (default: 20)",
    )
    parser.add_argument(
        "--audit-export",
        type=Path,
        help="Export full audit trail to JSON file",
    )
    
    args = parser.parse_args()
    
    try:
        project_dir = resolve_project_dir(args.project)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1
    
    # Show stats
    if args.stats:
        stats = get_project_stats(project_dir)
        rqs = get_research_questions(project_dir)
        
        print(f"\n📊 Project Statistics")
        print(f"  Discovered Papers: {stats.get('discovered_papers', 0)}")
        print(f"  Verified Papers: {stats.get('verified_papers', 0)}")
        print(f"  Downloaded PDFs: {stats.get('downloaded_pdfs', 0)}")
        print(f"  Extracted Markdowns: {stats.get('extracted_markdowns', 0)}")
        
        if rqs:
            print(f"\n🎯 Research Questions:")
            for i, rq in enumerate(rqs, 1):
                print(f"  RQ{i}: {rq}")
    
    # Show events
    if args.events:
        events = get_events(
            project_dir,
            action=args.action,
            agent=args.agent,
            limit=args.limit,
        )
        
        if not events:
            print(f"\n⚠️  No events found")
        else:
            print(f"\n📝 Recent Events ({len(events)} shown)")
            for event in events:
                timestamp = event.get("timestamp", "N/A")
                action = event.get("action", "UNKNOWN")
                description = event.get("description", "")
                status = event.get("status", "UNKNOWN")
                
                status_icon = "✅" if status == "SUCCESS" else "❌"
                print(f"  {status_icon} [{timestamp[:10]}] {action}: {description}")
    
    # Export audit trail
    if args.audit_export:
        export_audit_trail(project_dir, args.audit_export)
    
    return 0


if __name__ == "__main__":
    exit(main())
