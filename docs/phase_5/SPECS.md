# Phase 5 — Specifications (Harness Console)

> **Status:** Planning | **Version:** 1.0.0 (PipelineSpec schema `0.1.0`) | Companion docs: [`README.md`](./README.md) · [`BLUEPRINT.md`](./BLUEPRINT.md) · [`PLAN.md`](./PLAN.md)

## 1. Console package layout (target)

```
src/scholar_harness/console/
├── __init__.py
├── serve.py                 # `scholar-harness serve` entry (FastAPI app factory)
├── api/
│   ├── workspace.py         # GET reads over canonical files
│   ├── jobs.py              # POST/GET jobs, SSE stream
│   ├── screening.py         # batch list + decisions writer
│   ├── pipelines.py         # PipelineSpec CRUD + dry-run
│   └── audit.py             # journal reads + event POST
├── runtimes/
│   ├── job_runner.py        # asyncio subprocess wrapper
│   └── actions.py           # Action → [command] mapping table (single source)
└── static/                  # no-build HTML + vendored JS (lib/)
    ├── index.html
    ├── app.js
    └── styles.css
```

Runtime dir (never committed): `<workspace>/.harness-console/{jobs,pid,log}`.

## 2. `scholar-harness serve` CLI contract

```
uv run scholar-harness serve --workspace <path> [--port 8765] [--host 127.0.0.1]
```

- Default bind is loopback. `--host 0.0.0.0` prints a prominent exposure warning.
- Reads `settings`/env exactly like the kits: API keys come from the environment, never via UI.
- Serves `/` → static console; `/api/v1/*` → JSON; `/api/v1/jobs/{id}/events` → SSE (`text/event-stream`).

## 3. HTTP API (seed surface, M5.1→M5.3)

All responses return the canonical file contents or 404 with the missing relative path. No cursor/pagination for v1 lists beyond `limit`/`offset`.

| Method | Path | Purpose | Backing file(s) |
| :-- | :-- | :-- | :-- |
| GET | `/api/v1/workspace/meta` | `project.json`, `INDEX.md` summary, playbook/fingerprint | `project.json`, `INDEX.md`, `protocol.json` |
| GET | `/api/v1/workspace/status` | Full `scholar-harness status` payload | `ResearchOrchestrator.get_status()` |
| GET | `/api/v1/literature/candidates` | Deduped, verified, hydrated counts + rows | `literature/*.json` |
| GET | `/api/v1/literature/included` · `/excluded` | PRISMA sets | `literature/included.json` · `excluded.json` |
| GET | `/api/v1/screening/batches` | batch list + decision/collect state | `literature/screening/*` |
| GET | `/api/v1/screening/batch/{n}` | batch items + existing decisions | `batch_NNN.json`, `batch_NNN_decisions.json` |
| POST | `/api/v1/screening/batch/{n}/decisions` | append decisions; run `collect` | `batch_NNN_decisions.json`; collect on `literature/` |
| GET | `/api/v1/synthesis/{file}` | `consensus*`, `evidence_matrix`, `synthesis_rq*`, `rag_rq*` | `synthesis/*` |
| GET | `/api/v1/phase4/{file}` | `trust_consensus*`, RoB/COI/retraction/open-science | `phase4/*` |
| GET | `/api/v1/assets/graph` | serve generated graph | `literature/knowledge_graph.html` |
| GET | `/api/v1/audit/events?action=&agent=` | journal timeline with filters | `audit/journal.jsonl` |
| POST | `/api/v1/audit/events` | append event (same schema as `workspace-manager/log_event.py`) | `audit/journal.jsonl` |
| POST | `/api/v1/jobs` | `{action or pipeline_id, params}` → `job_id` | job runner |
| GET | `/api/v1/jobs/{id}` | lifecycle + exit code + log tail | `.harness-console/jobs/<id>/` |
| POST | `/api/v1/jobs/{id}/cancel` | SIGTERM → SIGKILL after grace | job runner |
| GET | `/api/v1/jobs/{id}/events` | SSE: `state`, log lines, journal-event ticks | job runner |
| GET | `/api/v1/agents/actions` | the Action→Command table (section 5) | `runtimes/actions.py` |
| GET/POST | `/api/v1/pipelines` + `/api/v1/pipelines/{id}/dry-run` | PipelineSpec CRUD + sample dry-run | `.harness-console/pipelines/*.json` |

**Write discipline:** every POST that mutates canonical state writes atomically (temp file + `os.replace`) and then writes one `audit/journal.jsonl` event before responding.

## 4. PipelineSpec — JSON schema `0.1.0`

A pipeline is a DAG of kit invocations. It is pure data: the CLI (`scholar-harness run --pipeline`) and the console editor consume the identical file.

```jsonc
{
  "schema_version": "0.1.0",
  "id": "prisma_slr_default",
  "archetype": "PRISMA_SLR",            // playbook template origin
  "name": "PRISMA SLR (2020) — default",
  "workspace_slug": "my-review",
  "settings": {
    "rq_ids": ["RQ1", "RQ2"],
    "provider_priority": ["openalex", "semantic_scholar", "arxiv"]
  },
  "nodes": [
    {
      "id": "n1_discovery",
      "kit": "scholar-search-kit",
      "command": ["scholar-search", "run"],
      "args": {
        "query": "{{rq1_query}}",          // {{...}} references pipeline inputs
        "providers": "{{provider_priority}}",
        "year_min": 2019,
        "limit": 2000
      },
      "inputs": [],                        // file refs: workspace-relative
      "outputs": ["literature/candidates.json"],
      "on_fail": "abort"                   // abort | skip | continue
    },
    {
      "id": "n2_dedup",
      "kit": "scholar-search-kit",
      "command": ["scholar-search", "dedup"],
      "args": {"input": "literature/candidates.json"},
      "inputs": ["literature/candidates.json"],
      "outputs": ["literature/corpus.json"],
      "on_fail": "abort"
    },
    {
      "id": "n3_screen",                  // agent-in-the-loop: pauses for humans
      "kit": "harness-agent-screen",
      "command": ["python", "src/scholar_harness/agent_screen.py", "prepare"],
      "args": {"workspace": "{{workspace_slug}}"},
      "inputs": ["literature/corpus.json"],
      "outputs": ["literature/screening/batch_*.json"],
      "on_fail": "abort",
      "requires_decision": true           // blocks until batch decisions written
    }
  ],
  "edges": [["n1_discovery", "n2_dedup"], ["n2_dedup", "n3_screen"]],
  "dry_run": {"per_node_limit": 25},      // overridden at dry-run request time
  "created_by": "console|cli|agent",
  "fingerprint": "sha256:..."             // canonical bytes like protocol.json
}
```

Rules:
- `args` values are static or `{{settings_key}}`/`{{input_key}}` templates resolved against `settings` + node outputs; unresolved templates fail schema validation, not at runtime.
- Node commands are executed through the same `uv run` env as the kits (no custom interpreters).
- `requires_decision: true` nodes stop conditional on presence of decision files — this is what lets the console and the agent hand off screening cleanly.
- Fingerprint = SHA-256 of canonical JSON, mirroring `scholar-protocol-kit`'s approach; re-runs with same fingerprint + same inputs are guaranteed idempotent (railroaded by the roadmap determinism principle).

## 5. Action → Command mapping (single source of truth, seed set)

Location: `src/scholar_harness/console/runtimes/actions.py`. One table drives (a) the UI "Agent Exchange" panel, (b) the job runner's command construction, (c) CI drift tests.

| action_id | label | command template | mcp_tool | mutates |
| :-- | :-- | :-- | :-- | :-- |
| `status` | Show workspace status | `scholar-harness status -w {ws}` | — | no |
| `sync` | Resync project state | `scholar-harness sync -w {ws}` | — | yes |
| `discovery` | Federated discovery | `uv run --directory tools/scholar-search-kit scholar-search run --query {q}` | `nexus_discover` | yes |
| `screen_prepare` | Prepare screening batch | `python src/scholar_harness/agent_screen.py prepare {ws}` | `nexus_screen` | yes |
| `screen_collect` | Assemble screening decisions | `python src/scholar_harness/agent_screen.py collect {ws}` | `nexus_screen` | yes |
| `download` | Harvest OA PDFs | `uv run --directory tools/scholar-pdf-kit scholar-pdf download --input {ws}/literature/included.json --output {ws}/pdfs/` | `nexus_extract_pdf` | yes |
| `extract` | Extract fulltext | `uv run --directory tools/scholar-pdf-kit scholar-pdf extract --input {ws}/pdfs/ --output {ws}/extracted/` | `nexus_extract_pdf` | yes |
| `rag_index` | Index into vector store | `uv run --directory tools/scholar-rag-kit scholar-rag index --ws {ws}` | `nexus_rag_index` | yes |
| `trust_context` | Build trust consensus | `uv run --directory tools/scholar-verify-kit scholar-verify trust-context --workspace {ws}` | — | yes |
| `synthesize` | Grounded synthesis | `uv run --directory tools/scholar-rag-kit scholar-rag synthesize ...` | `nexus_rag_synthesize` | yes |
| `graph` | Build citation graph | `uv run --directory tools/scholar-graph-kit scholar-graph build ...` | `nexus_graph_build` | yes |
| `export` | Export artifact set | `scholar-harness export ...` | — | yes |

**CI drift test:** for every row, assert the command template's CLI exists (`--help` parses) and the `mcp_tool` name (if any) is registered in `.agents/plugins/nexus-scholar/mcp_config.json`.

## 6. Job Runner contract

```jsonc
{
  "job_id": "job_6f9c2a1",
  "action_id": "trust_context",
  "state": "queued|running|success|failed|cancelled",
  "pid": 8123,
  "exit_code": 0,
  "command": ["uv", "run", "--directory", "tools/scholar-verify-kit", "scholar-verify", "trust-context", "--workspace", "..."],
  "cwd": "<workspace>",
  "log_path": "<workspace>/.harness-console/jobs/job_6f9c2a1/stdout.log",
  "started_at": "2026-09-07T10:00:00Z",
  "finished_at": null,
  "journal_event_id": "EVT-20260907-..."
}
```

- Single-flight per action per workspace (409 on duplicate of an active `running` job); concurrency is achieved by the kits' own async internals, not by parallel CLI processes.
- Timeouts: per-action default 30 min (`download`/`extract` override to 12 h).
- On completion (any state), the runner writes `audit/journal.jsonl` via `log_event.py` semantics: `action`, `agent="scholar-harness-console"`, `inputs` = action params, `outputs` = job_id + exit code, `status` = SUCCESS/PARTIAL/FAILED.
- No secrets in command logs.

## 7. Screening decisions format (reuses the agent handoff verbatim)

`literature/screening/batch_NNN_decisions.json` stays the canonical shape produced today by the agent handoff in `src/scholar_harness/agent_screen.py`:

```jsonc
{
  "batch": 3,
  "decisions": [
    {"study_id": "SCI-000042", "decision": "included", "reason_code": "INC-01", "confidence": "high", "note": "plausible UAV weed mapping"},
    {"study_id": "SCI-000091", "decision": "excluded", "reason_code": "EXC-02", "confidence": "medium", "note": "no precision-agriculture domain"}
  ],
  "reviewed_by": "console|oc-<agent>|manual",
  "timestamp": "2026-09-07T10:00:00Z"
}
```

The GUI never introduces a new schema, and the parity test (PLAN matrix §4 row 3) asserts GUI-written files are byte-equivalent modulo `reviewed_by`/`timestamp` for identical decisions.

## 8. Concurrency & atomicity rules

- All console writes to canonical files: write to `<file>.tmp-<jobid>` in the same directory, then `os.replace`.
- Console reads never cache long-term: response functions stat + read on each request; SSE ticks push `ETag`-style reload signals on change (file mtime of `INDEX.md` is the cheap global heartbeat).
- Two console screens/agents writing the same decision batch: last-writer-wins per file per atomic replace, but per-event journal lines append — the journal is the reconciliation record (exactly the roadmap's "collaboration-safe" argument).

## 9. UI screens (static console, M5.2–M5.4)

| Screen | Purpose | Data source | Notes |
| :-- | :-- | :-- | :-- |
| Dashboard | Phase state, PRISMA counts, harvest/extract/index metrics, recent journal events | `/workspace/status`, `/audit/events` | mirrors `scholar-harness status` |
| Literature | candidates/deduped/included/excluded browsable + filterable | `/literature/*` | tom-select search (vendored) |
| Screening | batch picker, criteria panel, per-item decision radio + reason code, progress vs collect state | `/screening/*` | writes decision file + collect (M5.3) |
| Harvest & Extract | progress, proxy config hint, per-DOI result table | job events | read-only + trigger buttons |
| Synthesis & Trust | styled Markdown + trust badge legend, RQ scoped reports | `/synthesis/*`, `/phase4/*` | render, don't recompute |
| Pipeline Builder | template gallery → editor → dry-run → run/export | `/pipelines`, `jobs` | M5.4; emits `PipelineSpec` |
| Agent Exchange | per-screen "see CLI command / MCP tool" | `/agents/actions` | rendering of mapping table |
| Audit | journal timeline, filter by action/agent, expand event JSON | `/audit/events` | append-only view + (optional) annotate |

## 10. Acceptance matrix (hermetic tests)

| Test | Asserts |
| :-- | :-- |
| `test_status_endpoint_matches_cli` | `/workspace/status` JSON keys == `orchestrator.get_status()` keys on the same `tmp_path` workspace. |
| `test_job_lifecycle_success` | POST job → `queued→running→success`; journal event appended with matching `event_id`. |
| `test_job_failure_and_cancel` | failing command → `failed` + journal `FAILED`; cancel → SIGTERM path + `cancelled`. |
| `test_screening_parity` | GUI decisions file == agent `collect` output modulo review metadata. |
| `test_actions_table_drift` | every row's CLI parses `--help`; mcp_tool registered in `mcp_config.json`. |
| `test_pipeline_dry_run_writes_nothing` | dry-run of a PRISMA template leaves `workspaces/<slug>` canonical tree byte-identical. |
| `test_pipeline_fingerprint_stable` | same spec JSON → same `sha256` fingerprint; re-running is idempotent. |
| `test_atomic_write_no_partials` | kill a decision POST mid-write; no partial `batch_NNN_decisions.json` survives. |
| `test_loopback_default_bind` | server defaults to `127.0.0.1`; `--host 0.0.0.0` emits the exposure warning. |