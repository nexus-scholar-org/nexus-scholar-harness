# Performance & Concurrency for workspace-manager

**Blocked batch path (D1):** do not run the batch example below. At the current
source, `batch_log.py:72` supplies an unsupported `refresh_index` keyword to
`log_project_event` (`log_event.py:159-169`). Use serial single-event calls until
the separately owned runtime defect is repaired. Batch throughput and refresh
suppression are proposals, not verified behavior.

CLI-first throughput guidance. All commands below are verified flag-for-flag
via `--help` (inspection-only); nothing here writes a workspace, calls a
provider, or launches a server.

## Batch Event Logging (fewer processes, one refresh intent)

Logging one event per process regenerates `INDEX.md` on every event
(`log_project_event` always calls `refresh_index_md`: log_event.py:218-219).
A future repaired batch writer could reduce process overhead for multi-step
pipelines (search → dedup → verify → screen). Reference-only example:

```bash
# events.jsonl = one event object per line:
# {"action": "...", "agent": "...", "description": "...",
#  "inputs": [...], "outputs": [...], "parameters": {...},
#  "metrics": {...}, "status": "SUCCESS"}
uv run python .agents/skills/workspace-manager/scripts/batch_log.py my-project --events-file events.jsonl
```

Verified flags (`batch_log.py --help`): positional `project`, required
`--events-file`, `--refresh-index` (default True) / `--no-refresh-index`.
The events-file object keys map to `EventBatch.add_event` /
`load_events_from_jsonl` (batch_log.py:19-108): `action`, `agent`,
`description`, `inputs`, `outputs`, `parameters`, `metrics`, `status`.

Single events stay on `log_event.py` (verified `log_event.py --help`:
positional `project`, required `--action`, `--agent`, `--description`,
`--inputs/--outputs` (`nargs *`), `--status`). There is no `--metrics`,
`--profile`, or `--defer-index-refresh` CLI flag — do not use them.

## What not to use

- There is **no** importable `workspace_manager` module and **no**
  `ProjectManager` class. All writes go through the CLI scripts above; never
  hand-append to `journal.jsonl`.
- There are **no** `scripts/index_audit.py` or `scripts/archive_audit.py`
  helpers in the committed tree — do not document or invoke them.
- `log_project_event` takes no `refresh_index` parameter
  (log_event.py:159-169). Refresh control exists only as the `batch_log.py`
  CLI contract (`--refresh-index` / `--no-refresh-index`); programmatic
  refresh suppression is a deferred defect, not a documented feature (see the
  task return, not this doc).
- `query_project.py` helpers (`get_project_stats`, `get_research_questions`,
  `get_events`, `export_audit_trail`, `resolve_project_dir`) are plain
  uncached file reads (query_project.py:11-135). This doc makes no cache-TTL,
  timing, or speedup claim.

## Query Performance (read-only)

Reads never touch the journal for writing. Verified flags
(`query_project.py --help`): positional `project`, `--stats`, `--events` with
`--action` / `--agent` / `--limit` (default 20), `--audit-export <file>`.

```bash
uv run python .agents/skills/workspace-manager/scripts/query_project.py my-project --stats
uv run python .agents/skills/workspace-manager/scripts/query_project.py my-project --events --limit 10
uv run python .agents/skills/workspace-manager/scripts/query_project.py my-project --audit-export audit_trail.json
```

Filter semantics are literal substring comparisons in `get_events`
(query_project.py:58-62): `action` matches case-insensitively on the event
`action`, `agent` matches case-insensitively on `agent_or_tool`. Newest-first
is the default (`reverse=True`); `--limit` truncates after reversal.

## Project State Size & Scalability

Order-of-magnitude guidance only (not a measured guarantee):

| Artifact | Typical |
|----------|---------|
| `project.json` | <1KB |
| `INDEX.md` | 2-5KB (grows with the committed `key_files` catalog + `reports/*.md` scan) |
| `journal.jsonl` | ~0.5KB per event |

For large journals, prefer fewer, well-described batch events over one event
per paper, and use `--action` / `--agent` / `--limit` to bound reads. No
archive/index helper exists in the committed scripts; retention policy is out
of scope for this refresh (HCM revisit note in `SKILL.md` applies).
