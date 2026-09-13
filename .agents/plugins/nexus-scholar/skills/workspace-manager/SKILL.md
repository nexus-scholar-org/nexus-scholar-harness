---
name: workspace-manager
description: Central orchestration agent for research data routing and project state management. Supports concurrent event logging, batch operations, and real-time catalog synchronization across project workspaces.
---

# `workspace-manager` Skill Instructions

You are the central project orchestration agent for the Nexus Scholar Suite. Your job is to isolate literature, PDFs, extractions, and synthesis files into dedicated project directories under `workspaces/<project-slug>/` rather than polluting tool folders or the workspace root.

## Core Responsibilities
1. **Scaffold Projects**: Initialize standardized research project workspaces inside `workspaces/<project-slug>/`.
2. **Resolve Active Project**: Detect the active research project or prompt the user to choose or create one.
3. **Enforce Canonical Tool Paths**: Direct all toolkit commands (`scholar-protocol`, `scholar-search`, `scholar-pdf`, `scholar-graph`, `scholar-rag`, etc.) to read from and write to the active project folder.
4. **Maintain State & Manifests**: Efficiently update `project.json` stats, `protocol.json`, and `audit/journal.jsonl` as research progresses; record `GENESIS` (+ `recon_context` provenance sidecar for grounded inception) at protocol compile.
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
├── INDEX.md                   # Master human-readable index and status catalog
├── intent.json                # Socratic LLM intent packet
├── protocol.json              # Canonical deterministic research protocol contract
├── SCREENING_CRITERIA.md      # Rendered inclusion/exclusion criteria document
├── project.json               # Project manifest (title, RQs, keywords, stats)
├── audit/
│   ├── journal.jsonl          # Immutable event ledger of all executed actions
│   └── recon_context.json     # GENESIS provenance sidecar (grounded inception)
├── literature/                # Search results & screening artifacts
│   ├── raw_search.json        # Federated raw results
│   ├── deduped.json           # PID-clustered + title-similarity dedup
│   ├── verified.json          # Verified & hydrated records
│   ├── included.json          # Final screened include set
│   ├── excluded.json          # Screened-out records + reasons
│   ├── screening/             # batch_NNN.json + batch_NNN_decisions.json
│   ├── prisma_screening_report.md   # PRISMA 2020 flow
│   ├── graph.html             # PyVis interactive citation network visualization
│   └── graph.json             # Node-link graph topology & PageRank weights
├── pdfs/                      # Downloaded PDFs & download_summary.json
├── extracted/                 # Markdown with YAML frontmatter
├── synthesis/                 # Literature review, claims, dynamic synthesis matrices
├── exports/                   # CSV/JSON exports (search, verified, decisions)
└── phase4/                    # Verify-kit outputs (trust consensus, RoB/COI, retraction)
```

---

## Event Logging (Append-Only Audit Trail)

### Single Events
After executing any major step (Search, Dedup, Verify, Screen, PDF Download, Extraction, Graph, Matrix, Synthesis), log the action:

```bash
uv run python .agents/skills/workspace-manager/scripts/log_event.py <project-slug> \
  --action DISCOVERY_SEARCH \
  --agent scholar-search-kit \
  --description "Federated search across 5 query clusters" \
  --outputs workspaces/<PROJECT>/literature/raw_search.json \
  --metrics discovered_papers=127
```

### Batch & Programmatic Logging (CLI-first)

Logging is **CLI-first**: all writes go through the canonical scripts
(`log_event.py` for one event, `batch_log.py` for a batch). There is **no**
importable `workspace_manager` module — never hand-append to `journal.jsonl`.

```bash
# Batch events from a JSONL file (one process, one append, one INDEX.md refresh)
uv run python .agents/skills/workspace-manager/scripts/batch_log.py <project-slug> \
  --events-file events.jsonl
# events.jsonl = one event object per line (schema below); run <N> appends N rows
```

### The `GENESIS` event (hard convention)

Every project with a compiled protocol must record, besides `PROJECT_INITIALIZED`
(from `init_project.py`), a **`GENESIS`** audit event. For literature-grounded
inception it carries full provenance in the `audit/recon_context.json` sidecar
plus a bounded inline summary (direction, anchors, cache key, confidence). See
`specs/inception-ecosystem/02_handoffs.md` §2.2.

---

## Agent Integration Guidelines & Best Practices

- **Project Resolution**: At the start of a multi-step workflow, detect or prompt for the active project; inspect state before writing with `query_project.py --stats`.
- **Batch Logging for Performance**: When running multi-step pipelines (search → dedup → verify → screen), use `batch_log.py` with an `--events-file` to write the journal once and refresh INDEX.md once (not N times).
- **Genesis Provenance**: on protocol compile, log `GENESIS`; for grounded inception, write the full provenance sidecar `audit/recon_context.json` and a bounded inline summary (schema: `specs/inception-ecosystem/02_handoffs.md` §2.2; implementation: `src/scholar_harness/inception.py::log_genesis`).
- **Metric Aggregation**: Always update `stats` with quantitative outcomes (papers discovered, verified, downloaded, extracted, etc.). The INDEX.md uses these for the summary table.
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
