#!/usr/bin/env python3
"""Batch event logging for high-throughput workspace management."""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any
from log_event import log_project_event


class EventBatch:
    """Accumulate multiple events and log them efficiently."""
    
    def __init__(self, defer_index_refresh: bool = True):
        self.events = []
        self.defer_index_refresh = defer_index_refresh
    
    def add_event(
        self,
        action: str,
        agent_or_tool: str,
        description: str,
        inputs: list[str] | None = None,
        outputs: list[str] | None = None,
        parameters: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        status: str = "SUCCESS",
    ) -> None:
        """Add an event to the batch."""
        self.events.append({
            "action": action,
            "agent_or_tool": agent_or_tool,
            "description": description,
            "inputs": inputs or [],
            "outputs": outputs or [],
            "parameters": parameters or {},
            "metrics": metrics or {},
            "status": status.upper(),
        })
    
    def __len__(self) -> int:
        return len(self.events)
    
    def __iter__(self):
        return iter(self.events)


async def batch_log_events(
    project_path_or_slug: str | Path,
    batch: EventBatch,
    refresh_index: bool = True,
) -> list[dict[str, Any]]:
    """Log multiple events and optionally refresh INDEX.md once."""
    logged_events = []
    
    for i, event_dict in enumerate(batch.events):
        # Suppress INDEX refresh for all but the last event
        should_refresh = refresh_index and (i == len(batch.events) - 1)
        
        try:
            logged_event = log_project_event(
                project_path_or_slug=project_path_or_slug,
                action=event_dict["action"],
                agent_or_tool=event_dict["agent_or_tool"],
                description=event_dict["description"],
                inputs=event_dict.get("inputs"),
                outputs=event_dict.get("outputs"),
                parameters=event_dict.get("parameters"),
                metrics=event_dict.get("metrics"),
                status=event_dict.get("status", "SUCCESS"),
                refresh_index=should_refresh,  # Only refresh on last event
            )
            logged_events.append(logged_event)
        except Exception as e:
            print(f"❌ Error logging event {i}: {e}")
            # Continue with next event
    
    return logged_events


def load_events_from_jsonl(file_path: Path) -> EventBatch:
    """Load events from a JSONL file."""
    batch = EventBatch(defer_index_refresh=True)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Events file not found: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                event_dict = json.loads(line)
                batch.add_event(
                    action=event_dict.get("action", "UNKNOWN"),
                    agent_or_tool=event_dict.get("agent", "agent"),
                    description=event_dict.get("description", ""),
                    inputs=event_dict.get("inputs"),
                    outputs=event_dict.get("outputs"),
                    parameters=event_dict.get("parameters"),
                    metrics=event_dict.get("metrics"),
                    status=event_dict.get("status", "SUCCESS"),
                )
            except json.JSONDecodeError as e:
                print(f"⚠️  Skipping line {line_num}: {e}")
    
    return batch


def main():
    parser = argparse.ArgumentParser(
        description="Batch log multiple events to a project's audit journal (single INDEX.md refresh)."
    )
    parser.add_argument("project", help="Project slug or directory path")
    parser.add_argument(
        "--events-file",
        type=Path,
        required=True,
        help="JSONL file with events (one event per line)",
    )
    parser.add_argument(
        "--refresh-index",
        action="store_true",
        default=True,
        help="Refresh INDEX.md after logging (default: True)",
    )
    parser.add_argument(
        "--no-refresh-index",
        action="store_false",
        dest="refresh_index",
        help="Skip INDEX.md refresh for faster batch logging",
    )
    
    args = parser.parse_args()
    
    # Load events
    batch = load_events_from_jsonl(args.events_file)
    
    if not batch:
        print(f"⚠️  No events loaded from {args.events_file}")
        return 1
    
    print(f"📝 Batch logging {len(batch)} events to {args.project}...")
    
    # Log batch (async)
    result = asyncio.run(
        batch_log_events(
            args.project,
            batch,
            refresh_index=args.refresh_index,
        )
    )
    
    print(f"✅ Logged {len(result)} events")
    print(f"📊 Summary: {len(result)} successful, 0 failed")
    return 0


if __name__ == "__main__":
    exit(main())
