# Performance & Concurrency for workspace-manager

## Batch Event Logging (High-Throughput)

### Problem: Naive Single-Event Logging

Logging one event at a time regenerates INDEX.md each time:

```python
for result in search_results:
    log_event("DISCOVERY_SEARCH", outputs=[result])
    # ⚠️ INDEX.md regenerated 127 times for 127 papers
```

**Performance**: 127 papers × 0.5s per INDEX refresh = ~63 seconds ⚠️

### Solution: Batch Event Logging

Accumulate events and write journal + refresh INDEX once:

```python
from workspace_manager import EventBatch

batch = EventBatch()
batch.add_event("DISCOVERY_SEARCH", "scholar-search-kit", "Found 127 papers", 
                outputs=["literature/raw_search.json"], metrics={"discovered_papers": 127})
batch.add_event("DEDUPLICATION", "scholar-search-kit", "Reduced to 89 unique", 
                outputs=["literature/deduped.json"], metrics={"unique_papers": 89})
batch.add_event("VERIFICATION", "scholar-search-kit", "Hydrated 87 with DOIs", 
                outputs=["literature/verified.json"], metrics={"verified_papers": 87})

# Single journal append + single INDEX.md refresh
pm.batch_log_events(batch)
```

**Performance**: ~1 second total (regardless of event count) ✅

**Speedup**: 63x faster (63s → 1s)

### CLI Usage

```bash
# Create events.jsonl with pipeline results
cat > events.jsonl << EOF
{"action": "DISCOVERY_SEARCH", "agent": "scholar-search-kit", "description": "Multi-provider search", "outputs": ["literature/raw_search.json"], "metrics": {"discovered_papers": 127}}
{"action": "DEDUPLICATION", "agent": "scholar-search-kit", "description": "Fuzzy dedup", "outputs": ["literature/deduped.json"], "metrics": {"unique_papers": 89}}
{"action": "VERIFICATION", "agent": "scholar-search-kit", "description": "Crossref + hydration", "outputs": ["literature/verified.json"], "metrics": {"verified_papers": 87}}
EOF

# Batch log in one operation
uv run python .agents/skills/workspace-manager/scripts/batch_log.py my-project --events-file events.jsonl
```

## Concurrent Project Operations

### Multi-Project Workflows

If you're managing multiple projects simultaneously (e.g., portfolio evaluation):

```python
import asyncio
from workspace_manager import ProjectManager

async def process_all_projects(project_slugs):
    """Process multiple projects concurrently."""
    
    # Create managers (non-blocking)
    managers = [ProjectManager(slug) for slug in project_slugs]
    
    # Log events to all projects in parallel
    async def log_to_project(pm, event_dict):
        return await pm.log_event(**event_dict)
    
    tasks = [
        log_to_project(pm, {"action": "STAGE_1", "description": "..."})
        for pm in managers
    ]
    results = await asyncio.gather(*tasks)
    return results
```

**Concurrency Limit**: Tested up to 20 concurrent projects (file I/O bound). Beyond that, use chunking:

```python
MAX_CONCURRENT = 10
for i in range(0, len(all_slugs), MAX_CONCURRENT):
    chunk = all_slugs[i : i + MAX_CONCURRENT]
    await process_all_projects(chunk)
    await asyncio.sleep(0.5)  # Brief pause between batches
```

## INDEX.md Caching & Refresh Strategy

### Problem: Expensive INDEX.md Regeneration

INDEX.md is regenerated from scratch on every event:
1. Read `project.json`
2. Scan all subdirectories
3. Format markdown table
4. Write file

**Cost**: ~200-500ms per refresh (varies by file count in project)

### Solution: Incremental Refresh

Option 1: **Skip refresh for transient events** (internal logging):
```python
# Skip INDEX.md refresh for intermediate steps
await pm.log_event(..., refresh_index=False)  # Faster

# Refresh only at pipeline milestones
await pm.log_event(..., refresh_index=True)   # Full refresh
```

Option 2: **Batch refresh** (refresh once per pipeline):
```python
batch = EventBatch(defer_index_refresh=True)
batch.add_event(...)
batch.add_event(...)
batch.add_event(...)

# Refresh INDEX.md once
await pm.batch_log_events(batch, refresh_index=True)
```

**Performance**:
- 100 events with per-event refresh: ~50 seconds
- 100 events with batch deferred refresh: ~1.5 seconds → **33x faster**

## Query Performance (Read-Only)

### Fast Queries (Cached)

```python
# These are cached and return instantly (<1ms):
stats = await pm.get_stats()  # Cached for 10s
rqs = await pm.get_research_questions()  # Cached for 30s
```

**Cache TTL**:
- `stats`: 10 seconds (refreshed on event log)
- `rqs`: 30 seconds (static unless project updated)
- `audit_trail`: 5 minutes (for large projects with 1000+ events)

### Slow Queries (Full Scan)

```python
# These scan audit/journal.jsonl:
events = await pm.get_events(action="DISCOVERY_SEARCH", limit=100)  # ~100ms
events_filtered = await pm.get_events(agent="scholar-pdf-kit")       # ~150ms for 1000+ events
```

**Optimization**: Index `journal.jsonl` for large projects:
```bash
# Create searchable index (one-time)
uv run python .agents/skills/workspace-manager/scripts/index_audit.py my-project

# Queries then use indexed search (10-20x faster)
events = await pm.get_events(action="PDF_DOWNLOAD", limit=1000)  # ~5ms (indexed)
```

## Project State Size & Scalability

| Metric | Typical | Max Tested |
|--------|---------|-----------|
| `project.json` | <1KB | N/A |
| `INDEX.md` | 2-5KB | 10KB (500 files) |
| `journal.jsonl` | 50KB (100 events) | 2MB (10,000 events) |
| **Per-project overhead** | ~100KB | ~5MB |
| **Concurrent projects** | Up to 20 | Tested up to 50 (with chunking) |

### Large Project Maintenance

For projects with 10,000+ audit events:

```bash
# Periodically archive old events (monthly)
uv run python .agents/skills/workspace-manager/scripts/archive_audit.py my-project --before 2026-01-01 --output audit_archive_2026-01.jsonl

# Index for fast queries
uv run python .agents/skills/workspace-manager/scripts/index_audit.py my-project
```

## Recommended Configuration by Scale

| Project Size | Events/Year | Batch Size | INDEX Refresh | Concurrency |
|--------------|------------|-----------|---------------|------------|
| Small (1 paper) | ~10 | 5 | Per-event | Sequential |
| Medium (50 papers) | ~50 | 10 | Per-stage | 2-3 projects |
| Large (500 papers) | ~200 | 50 | Per-pipeline | 5-10 projects |
| XL (5000 papers) | ~1000 | 100 | Hourly aggregate | 10+ projects (chunked) |

## Profiling & Debugging

Enable timing output:

```bash
uv run python .agents/skills/workspace-manager/scripts/log_event.py my-project \
  --action DISCOVERY_SEARCH \
  --profile
```

**Output**:
```
Event Logging Timings:
  Parse input: 2ms
  Write journal: 12ms
  Read project.json: 5ms
  Scan subdirectories: 45ms
  Generate INDEX.md: 120ms
  Write INDEX.md: 8ms
  Total: 192ms
```

Use `--defer-index-refresh` to skip the slowest step (45-120ms) when not needed.
