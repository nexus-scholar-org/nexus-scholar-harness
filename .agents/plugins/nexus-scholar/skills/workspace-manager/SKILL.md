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
# Scaffold a new research project with automated INDEX.md.
# `title` is positional (init_project.py:184); --slug/--paradigm/--rq verified below.
uv run python .agents/skills/workspace-manager/scripts/init_project.py \
  "Multispectral Weed Segmentation in Agriculture" \
  --slug multispectral-weeds \
  --paradigm "Design Science" \
  --rq "RQ1: What CNN architecture maximizes..." \
  --rq "RQ2: How does band selection affect..."
```
Verified flags (`init_project.py --help`): `title` (positional), `--slug/-s`,
`--description/-d`, `--paradigm/-p`, `--rq` (repeatable), `--keyword/-k`
(repeatable), `--root` (default `.`). Scaffold creates `project.json`,
`synthesis/literature_review.md`, `audit/journal.jsonl` (`PROJECT_INITIALIZED`)
and `INDEX.md`; the remaining layout below appears via later pipeline stages.

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
  --inputs workspaces/<PROJECT>/protocol.json \
  --outputs workspaces/<PROJECT>/literature/raw_search.json \
  --status SUCCESS
```
`log_event.py` has no `--metrics` CLI flag (verified `log_event.py --help`:
positional `project`, required `--action`, `--agent`, `--description`,
`--inputs/--outputs` (`nargs *`), `--status`). To record quantitative outcomes,
put `"metrics"` in a `batch_log.py` events-file line or call
`log_project_event(..., metrics={...})` in Python (log_event.py:167); only keys
already present in `project.json` `stats` are merged (log_event.py:209-212).

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
- **Batch Logging for Performance**: When running multi-step pipelines (search → dedup → verify → screen), use `batch_log.py` with an `--events-file` to append N rows with one INDEX.md refresh. Verified flags (`batch_log.py --help`): positional `project`, required `--events-file`, `--refresh-index` (default True) / `--no-refresh-index`. Each line carries `action`, `agent`, `description`, `inputs`, `outputs`, `parameters`, `metrics`, `status` (see `references/audit_trace_spec.md` §2; loader: batch_log.py:82-108).
- **Query flags** (verified `query_project.py --help`): positional `project`, `--stats`, `--events` with `--action` / `--agent` / `--limit` (default 20), `--audit-export <file>`.
- **Genesis Provenance**: on protocol compile, log `GENESIS`; for grounded inception, write the full provenance sidecar `audit/recon_context.json` and a bounded inline summary (schema: `specs/inception-ecosystem/02_handoffs.md` §2.2; implementation: `src/scholar_harness/inception/genesis.py::log_genesis`).
- **Metric Aggregation**: record quantitative outcomes via the events-file `"metrics"` object or the Python `metrics=` kwarg — never via a `--metrics` CLI flag (it does not exist). The INDEX.md summary table reads `project.json` `stats`.
- **Event Schema**: follow `references/audit_trace_spec.md` §2 (field-for-field the `log_project_event` record: log_event.py:185-196). Do not duplicate the schema here.

## Boundaries (preserve)

- **Confirmation before emission.** Nothing is scaffolded or emitted without explicit user confirmation: the inception-agent Stage 6 human gate and the methodology-copilot pre-write check own that gate (`specs/inception-ecosystem/02_handoffs.md` §2.1 rule 1). Workspace-manager only runs the scaffold + audit writes the driver requests after confirmation, with scaffold values taken from the finalized `intent.json`.
- **Slug is a label, not an identity.** `project_id` is the human slug (directory name, `INDEX.md` label, `intent.json` `project_slug`). `registered_workspace_id` (`WSP-` + 32 lowercase hex, minted once at init from the OS CSPRNG and recorded in `project.json`) is the Contract v1 workspace identity stated by every artifact under the workspace. Never substitute one for the other; a workspace without a recorded id is pre-registration and fails closed (see `references/project_schema.md` §1.1; implementation: init_project.py:38-107).
- **Truthful append-only audit.** All writes go through `log_event.py` / `batch_log.py`; never hand-append to `journal.jsonl`. Every event carries timestamp, `event_id`, action, agent/tool, description, parameters, inputs, outputs, metrics, status.
- **Helpers vs candidates vs acceptance.** Helper scripts are conveniences, candidate outputs (raw search, deduped sets, unverified claims) are working state, and only the owning stage's acceptance step confers accepted status. Logging an event records provenance — it does not publish or accept a scientific claim or Contract v1 artifact.
- **Stack routing.** Interviews, paradigm choice, and `intent.json`/`protocol.json` emission belong to methodology-copilot conventions; grounded recon and direction selection belong to inception-agent; exact kit CLI flags belong to the `scholar-*-kit` skills. This skill routes there instead of duplicating volatile commands (see `references/tool_routing_matrix.md` for workspace-relative paths only).

## References

- `references/project_schema.md` — `project.json` identity + manifest.
- `references/audit_trace_spec.md` — journal schema, INDEX.md format.
- `references/tool_routing_matrix.md` — workspace-relative tool paths.
- `references/performance_concurrency.md` — batch-first throughput within committed flags.
- `specs/inception-ecosystem/01_skill_boundaries.md`, `02_handoffs.md` — stack ownership + emission chain.

> HCM-02/05 revisit note: human-capability-model refinements are out of scope for this refresh. This doc documents only the committed helper behavior above and does not anticipate HCM refactor behavior; revisit after the HCM packet lands.
