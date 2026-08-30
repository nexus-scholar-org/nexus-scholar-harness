---
name: workspace-manager
description: Central orchestration agent for research data routing and project state management. Supports concurrent event logging, batch operations, and real-time catalog synchronization across project workspaces.
---

# `workspace-manager` Skill Instructions

You are the central project orchestration agent for the Nexus Scholar Suite. Your job is to isolate literature, PDFs, extractions, and synthesis files into dedicated project directories under `workspaces/<project-slug>/` rather than polluting tool folders or the workspace root.

## Core Responsibilities
1. **Scaffold Projects**: Initialize standardized research project workspaces inside `workspaces/<project-slug>/`.
2. **Resolve Active Project**: Detect the active research project or prompt the user to choose or create one.
3. **Enforce Canonical Tool Paths**: Direct all toolkit commands (`scholar-search`, `scholar-pdf`, `scholar-rag`, etc.) to read from and write to the active project folder.
4. **Maintain State & Manifests**: Efficiently update `project.json` stats and `audit/journal.jsonl` as research progresses.
5. **Query Project State**: Retrieve project history, event logs, and current statistics programmatically.

---

## Quick CLI Workflow

### Initialize a Project
```bash
# Scaffold a new research project with automated INDEX.md
uv run python .agents/skills/workspace-manager/scripts/init_project.py \
  --title "Multispectral Weed Segmentation in Agriculture" \
  --slug multispectral-weeds \
  --paradigm "Design Science" \
  --rq "RQ1: What CNN architecture maximizes..." \
  --rq "RQ2: How does band selection affect..."
```

### Log Events (Single & Batch)
```bash
# Single event
uv run python .agents/skills/workspace-manager/scripts/log_event.py multispectral-weeds \
  --action DISCOVERY_SEARCH \
  --agent scholar-search-kit \
  --description "Federated search across 5 query clusters" \
  --outputs workspaces/multispectral-weeds/literature/raw_search.json

# Batch events (efficient append to journal)
uv run python .agents/skills/workspace-manager/scripts/batch_log.py multispectral-weeds --events-file events.jsonl
```

### Query Project State
```bash
# Get current project stats
uv run python .agents/skills/workspace-manager/scripts/query_project.py multispectral-weeds --stats

# Retrieve event history (last N events)
uv run python .agents/skills/workspace-manager/scripts/query_project.py multispectral-weeds --events --limit 10

# Export audit trail for compliance
uv run python .agents/skills/workspace-manager/scripts/query_project.py multispectral-weeds --audit-export audit_trail.json
```

---

## Canonical Project Structure

Every project in `workspaces/<project-slug>/` adheres to this layout:

```text
workspaces/<project-slug>/
├── INDEX.md                # Master human-readable index and status catalog
├── project.json            # Project manifest (title, RQs, keywords, stats)
├── audit/                  # Append-only journal.jsonl & verification audit logs
│   └── journal.jsonl       # Immutable event ledger of all executed actions
├── literature/             # Search results (raw_search.json, deduped.json, verified.json)
│   └── criteria.md         # PRISMA Inclusion / Exclusion rules
├── pdfs/                   # Downloaded PDFs & download_summary.json
├── extracted/              # Markdown (Docling) or TEI XML (Grobid)
├── synthesis/              # Literature review notes, comparative tables
└── exports/                # Reference exports (BibTeX, CSV, RIS)
```

---

## Event Logging (Append-Only Audit Trail)

### Single Events
After executing any major step (Search, Dedup, Verify, Screen, PDF Download, Extraction), log the action:

```bash
uv run python .agents/skills/workspace-manager/scripts/log_event.py <project-slug> \
  --action DISCOVERY_SEARCH \
  --agent scholar-search-kit \
  --description "Federated search across 5 query clusters" \
  --outputs workspaces/<PROJECT>/literature/raw_search.json \
  --metrics discovered_papers=127
```

### Batch Event Logging (High-Throughput)
For multiple sequential actions, batch them into one journal write:

```bash
# Create events.jsonl
cat > events.jsonl << EOF
{"action": "DISCOVERY_SEARCH", "agent": "scholar-search-kit", "description": "...", "outputs": ["raw_search.json"], "metrics": {"discovered_papers": 127}}
{"action": "DEDUPLICATION", "agent": "scholar-search-kit", "description": "...", "outputs": ["deduped.json"], "metrics": {"unique_papers": 89}}
{"action": "VERIFICATION", "agent": "scholar-search-kit", "description": "...", "outputs": ["verified.json"], "metrics": {"verified_papers": 87}}
EOF

# Batch log (single INDEX.md refresh)
uv run python .agents/skills/workspace-manager/scripts/batch_log.py <project-slug> --events-file events.jsonl
```

### Programmatic Event Logging (Async-Compatible)
```python
import asyncio
from workspace_manager import ProjectManager, EventBatch

async def main():
    pm = ProjectManager("multispectral-weeds")
    
    # Method 1: Single event
    await pm.log_event(
        action="DISCOVERY_SEARCH",
        agent_or_tool="scholar-search-kit",
        description="Multi-provider federated search",
        outputs=["literature/raw_search.json"],
        metrics={"discovered_papers": 127}
    )
    
    # Method 2: Batch events (efficient)
    batch = EventBatch()
    batch.add_event("DISCOVERY_SEARCH", "scholar-search-kit", "Search execution", ["literature/raw_search.json"], {"discovered_papers": 127})
    batch.add_event("DEDUPLICATION", "scholar-search-kit", "Dedup pass", ["literature/deduped.json"], {"unique_papers": 89})
    batch.add_event("VERIFICATION", "scholar-search-kit", "Verify & hydrate", ["literature/verified.json"], {"verified_papers": 87})
    
    # Write all events + refresh INDEX.md once
    await pm.batch_log_events(batch)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Querying Project State (Read-Only)

### CLI Queries
```bash
# Get summary stats
uv run python .agents/skills/workspace-manager/scripts/query_project.py multispectral-weeds --stats
# Output: Discovered: 127 | Verified: 87 | Downloaded: 42 | Extracted: 38

# Retrieve last N events
uv run python .agents/skills/workspace-manager/scripts/query_project.py multispectral-weeds --events --limit 20

# Export audit trail (for compliance/publication)
uv run python .agents/skills/workspace-manager/scripts/query_project.py multispectral-weeds --audit-export audit_report.json
```

### Programmatic Queries (Async)
```python
import asyncio
from workspace_manager import ProjectManager

async def main():
    pm = ProjectManager("multispectral-weeds")
    
    # Get stats
    stats = await pm.get_stats()
    print(f"Papers: {stats['discovered_papers']} discovered, {stats['verified_papers']} verified")
    
    # Get event history (with filtering)
    events = await pm.get_events(action="DISCOVERY_SEARCH", limit=10)
    for event in events:
        print(f"[{event['timestamp']}] {event['action']}: {event['description']}")
    
    # Query audit trail
    audit = await pm.get_audit_trail()
    print(f"Total actions logged: {len(audit)}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Agent Integration Guidelines & Best Practices

- **Project Resolution**: At the start of a multi-step workflow, detect or prompt for the active project:
  ```python
  pm = ProjectManager.resolve_active_project()  # Auto-detect from context or prompt
  ```

- **Batch Logging for Performance**: When running multi-step pipelines (search → dedup → verify → screen), use batch logging to write the journal once and refresh INDEX.md once (not N times).

- **Metric Aggregation**: Always update `stats` with quantitative outcomes (papers discovered, verified, downloaded, etc.). The INDEX.md uses these for the summary table.

- **Event Schema**: Follow the standard event schema:
  ```json
  {
    "timestamp": "2026-08-30T19:27:18.546691+00:00",
    "event_id": "EVT-20260830192718-f98507",
    "action": "DISCOVERY_SEARCH",
    "agent_or_tool": "scholar-search-kit",
    "description": "Multi-provider federated query",
    "parameters": {},
    "inputs": [],
    "outputs": ["literature/raw_search.json"],
    "metrics": {"discovered_papers": 127},
    "status": "SUCCESS"
  }
  ```

- **Error Handling**: If an event logs with `status: "FAILED"`, the workflow can retry. Use `--retry` in CLI or `retry=True` in Python API.

- **INDEX.md Refresh Strategy**: Single refresh after all batch events (not per-event) for performance. The `batch_log.py` script handles this automatically.

---

## Detailed References

- [Project Schema & State](references/project_schema.md): `project.json` specification, directory semantics, and state transitions.
- [Audit & Event Ledger Spec](references/audit_trace_spec.md): `audit/journal.jsonl` schema, event versioning, and `INDEX.md` generation algorithms.
- [Tool Routing Matrix](references/tool_routing_matrix.md): Comprehensive routing table for all suite tools, input/output specifications.
- [Performance & Concurrency](references/performance_concurrency.md): Batch event logging, concurrent project operations, caching strategies, and INDEX.md refresh optimization.
