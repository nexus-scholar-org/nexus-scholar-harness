# Phase 5 — Specifications (Harness Console)

> **Status:** Built and in use (checked against `main` on 2026-11-10) | **Version:** 1.0.0 (PipelineSpec schema `0.1.0`) | The companion design docs (README/BLUEPRINT/PLAN) were archived in the 2026-10-12 consolidation. §1, §2, §3.0 and §9 describe the console as it is; §3's seed table and §4 to §8 are the original Phase 5 design, kept for the parts that still hold. The routes the screens use are specified in [`screening-api-contract.md`](../screening-api-contract.md), [`workspaces-api.md`](../workspaces-api.md), [`inception-api.md`](../inception-api.md) and [`research_ui/DISCOVERY_API_PACKET.md`](../research_ui/DISCOVERY_API_PACKET.md).

## 1. Console package layout

```
src/scholar_harness/console/
├── __init__.py
├── serve.py                 # create_app: FastAPI factory, token, TrustedHost, origin checks
├── browser.py               # the packaged app's browser surface: launch code, cookie, allowlist
├── launcher.py              # `nexus-scholar ui`: static UI + engine, workspace switching
├── refusals.py              # the console refusal set (contract §7)
├── api/
│   ├── workspace.py         # GET reads over canonical files
│   ├── workspaces.py        # list, create, open (M5-slim)
│   ├── inception.py         # drafts, steps, preview, genesis (M4a)
│   ├── recon.py             # recon over HTTP (M4c)
│   ├── discovery.py         # plan, runs, recall, report, dedup, hand-off (M3b-api, M3d-engine)
│   ├── jobs.py              # POST/GET jobs, SSE stream
│   ├── screening.py         # batch list, decisions writer, pairing, defer, publish
│   ├── screening_v1.py      # the screening API (M1a onward)
│   ├── pipelines.py         # PipelineSpec CRUD + dry-run
│   ├── audit.py             # event POST
│   └── streams.py           # /api/v1/events/tick
└── runtimes/
    ├── job_runner.py        # asyncio subprocess wrapper
    └── actions.py           # Action → [command] mapping table (single source)
```

The console is **API-only**. The no-build SPA that lived under `static/` was
retired on 2026-10-31; the Research UI (`apps/research-ui/`) is the product
surface and reaches this API through its same-origin proxy.

Runtime dir (never committed): `<workspace>/.harness-console/{jobs,pid,log}`.

## 2. `scholar-harness serve` CLI contract

```
uv run scholar-harness serve --workspace <path> [--port 8765] [--host 127.0.0.1]
```

- Default bind is loopback. `--host 0.0.0.0` prints a prominent exposure warning. (Superseded by INC-01, M0: `serve` refuses any host outside `127.0.0.1`, `localhost`, `::1`; `cli.py` `serve`.)
- Every route except `/healthz` needs `Authorization: Bearer <token>`. The token is `NEXUS_CONSOLE_TOKEN` when set, else generated and printed once (`cli.py` `serve`, `serve.py` `create_app`). Hosts outside the loopback list answer `HOST_REFUSED`; a write from a foreign origin answers `ACTION_ORIGIN_REFUSED`.
- Reads `settings`/env exactly like the kits: API keys come from the environment (or the OS keychain for the screening drivers, `nexus-scholar keys`), never via UI.
- Serves `/api/v1/*` → JSON; SSE (`text/event-stream`) on `/api/v1/jobs/{id}/stream`, `/api/v1/events/tick`, `/api/v1/inception/drafts/{id}/recon/jobs/{job}/events` and `/api/v1/discovery/jobs/{job}/events`; `/healthz` → liveness. `serve` bundles no UI.
- **`nexus-scholar ui`** (M5-slim) is the researcher's entry point: one process on `127.0.0.1` (port 8770 by default) serves the static export of `apps/research-ui` and the same API, opens the browser through a one-time `/launch?code=` link that sets an HttpOnly session cookie, and can switch workspaces (`--workspace`, `--root`). The browser calls `/api/console/api/v1/...`, checked by `console/browser.py` (§9).

## 3. HTTP API

### 3.0 Routers mounted today (2026-11-10)

From `@router.` in `src/scholar_harness/console/api/*.py` and `include_router` in `serve.py`:

| Router (file) | Prefix | Routes | Specified in |
| :-- | :-- | :-- | :-- |
| `workspace.py` | `/api/v1` | GET `workspace/meta`, `workspace/status`, `literature/candidates`, `literature/included`, `literature/excluded`, `screening/batches`, `screening/batch/{n}`, `synthesis`, `synthesis/{filename}`, `phase4`, `phase4/{filename}`, `harvest/corpus`, `assets/graph`, `audit/events`, `agents/actions`, `ui/corpus/{kind}`, `ui/publication-status`, `ui/publication/outputs/{name}`, `ui/lineage` | this file §3, UI-07 specs |
| `workspaces.py` | `/api/v1` | GET `workspaces`; POST `workspaces`, `workspaces/open` | `workspaces-api.md` |
| `inception.py` | `/api/v1/inception` | GET/POST `drafts`; GET/PUT/DELETE `drafts/{id}`; POST `steps/{step}`, `preview`, `drafts/{id}/genesis` | `inception-api.md` |
| `recon.py` | `/api/v1/inception/drafts/{id}/recon` | GET `` (the state), `jobs/{job}`, `jobs/{job}/events`, `directions`; POST `probe`, `delta`, `distill`, `bind` | `inception-api.md` |
| `discovery.py` | `/api/v1/discovery` | GET `plan`, `runs`, `runs/{run}`, `runs/{run}/report`, `dedup`, `report`, `handoff`, `recall`, `jobs/{job}`, `jobs/{job}/events`; PUT `report/methods`; POST `runs`, `recall`, `jobs/{job}/cancel` | `DISCOVERY_API_PACKET.md` |
| `screening_v1.py` | `/api/v1/screening` | GET `summary`, `queue`, `records/{id}`, `records/{id}/proposal`, `decisions/conflicts`, `settings`, `approver`, `corpus`, `prisma/preview`, `export`, `methods`, `proposals/setup`, `proposals/runs/{id}`, `agreement`; PUT `settings`, `approver`; POST `decisions/events`, `decisions/conflicts/{id}/resolve`, `corpus/sources`, `corpus/sources/{id}/remove`, `corpus/accept`, `prepare`, `actions/pairing/begin`, `proposals/runs`, `proposals/runs/{id}/cancel`, `proposals/calibrations` | `screening-api-contract.md` §4 |
| `screening.py` | `/api/v1/screening` | POST `batch/{n}/decisions`, `actions/pairing/redeem`, `actions/defer`, `actions/publish`; GET `ui/batches`, `ui/batch/{n}/review`, `actions/pairing/status` | `screening-api-contract.md` §4, UI-07 |
| `jobs.py` | `/api/v1/jobs` | POST `start`, `{id}/cancel`; GET ``, `{id}`, `{id}/stream` | this file §6 |
| `pipelines.py` | `/api/v1/pipelines` | GET ``, `{id}`, `{id}/export`; POST ``, `{id}/dry-run` | this file §4 |
| `audit.py` | `/api/v1/audit` | POST `events` | this file §3 |
| `streams.py` | `/api/v1/events` | GET `tick` | this file §8 |

Four `/api/v1` routes that no caller used were removed in M6-hardening (PR #200; see `screening-api-contract.md` §4). The phone LAN routes (`/lan/pair`, `/lan/session/*`) are M2 and not built.

### 3.1 Seed surface (M5.1 to M5.3, the original design)

The table below is the original seed design. Where it differs from §3.0, §3.0 is what the code serves (for example jobs start at `POST /api/v1/jobs/start`, and a job's SSE is `/api/v1/jobs/{id}/stream`).

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
    "queries": { "rq1_query": "multispectral UAV weed segmentation" },
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
- `args` values are static or `{{settings_key}}`/`{{input_key}}` templates resolved against `settings` (e.g. `{{queries.rq1_query}}`) + node outputs; unresolved templates fail schema validation, not at runtime.
- Node commands are executed through the same `uv run` env as the kits (no custom interpreters).
- `requires_decision: true` nodes stop conditional on presence of decision files — this is what lets the console and the agent hand off screening cleanly.
- Fingerprint = SHA-256 of canonical JSON, mirroring `scholar-protocol-kit`'s approach; re-runs with same fingerprint + same inputs are guaranteed idempotent (railroaded by the roadmap determinism principle).

## 5. Action → Command mapping (single source of truth, seed set)

Location: `src/scholar_harness/console/runtimes/actions.py`. One table drives (a) the UI "Agent Exchange" panel, (b) the job runner's command construction, (c) CI drift tests.

| action_id | label | command template | mcp_tool | mutates |
| :-- | :-- | :-- | :-- | :-- |
| `status` | Show workspace status | `uv run scholar-harness status -w {ws}` | — | no |
| `sync` | Resync project state | `uv run scholar-harness sync -w {ws}` | — | yes |
| `discovery` | Federated discovery | `uv run scholar-search search --query "{q}"` | `nexus_discover` | yes |
| `dedup` | Deduplicate candidates | `uv run scholar-search dedup --input {ws}/literature/candidates.json --output {ws}/literature/corpus.json` | `nexus_dedup` | yes |
| `screen_prepare` | Prepare screening batch | `uv run python src/scholar_harness/agent_screen.py prepare {ws}` | `nexus_screen` | yes |
| `screen_collect` | Assemble screening decisions | `uv run python src/scholar_harness/agent_screen.py collect {ws}` | `nexus_screen` | yes |
| `download` | Harvest OA PDFs | `uv run scholar-pdf download --input {ws}/literature/included.json --output {ws}/pdfs/` | `nexus_extract_pdf` | yes |
| `extract` | Extract fulltext | `uv run scholar-pdf extract --input {ws}/pdfs/ --output {ws}/extracted/` | `nexus_extract_pdf` | yes |
| `rag_index` | Index into vector store | `uv run scholar-rag index {ws}/extracted/ --parent-view {ws}/parent-view.json --journal {ws}/audit/journal.jsonl --workspace-root {ws} --run-id <RUN-...> --created-at <rfc3339> --producer-version <version> --producer-commit <40-hex> --embedder-provider <provider> --embedder-model <model> --embedder-dimension <int>` | `nexus_rag_index` | yes |
| `trust_context` | Build trust consensus | `uv run scholar-verify trust-context --workspace {ws}` | — | yes |
| `synthesize` | Grounded synthesis | `uv run scholar-rag synthesize "{q}" --rq-id RQ1 --output-claims {ws}/synthesis/claims.json` | `nexus_rag_synthesize` | yes |
| `graph` | Build citation graph | `uv run scholar-graph build --input {ws}/literature/included.json --output {ws}/literature/knowledge_graph.html` | `nexus_graph_build` | yes |
| `export` | Export artifact set | `uv run scholar-harness export latex -w {ws}` | — | yes |

**CI drift test:** for every row, assert the command template's CLI exists (`--help` parses) and the `mcp_tool` name (if any) is an exported tool of `tools/scholar-agent-kit`'s MCP server (`tools/scholar-agent-kit/src/scholar_agent/server.py`).

## 6. Job Runner contract

```jsonc
{
  "job_id": "job_6f9c2a1",
  "action_id": "trust_context",
  "state": "queued|running|success|failed|cancelled",
  "pid": 8123,
  "exit_code": 0,
  "command": ["uv", "run", "scholar-verify", "trust-context", "--workspace", "..."],
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

## 9. UI screens (retired static console → Research UI)

The static console screens listed here in M5.2–M5.4 were retired on
2026-10-31. Their capabilities now live in `apps/research-ui/`, which consumes
this API through a same-origin proxy and keeps the demo/live distinction
visible:

| Former static screen | Research UI route | Packet |
| :-- | :-- | :-- |
| Dashboard | `/[locale]` overview | UI-02 |
| Workflow state | `/[locale]/workflow` | UI-03 |
| Screening | `/[locale]/screening` | UI-04, UI-07 |
| Corpus / PRISMA sets | `/[locale]/corpus` | UI-08 |
| Evidence lineage | `/[locale]/lineage` | UI-05 |
| Audit | `/[locale]/audit` | UI-06 |
| Job control / pipeline builder | **API only** (`/jobs`, `/pipelines`) — deliberately not browser-driven | — |

The routes in that table are history: the demonstration screens were removed on
2026-11-05 (`docs/decisions.md`). The Research UI routes on `main` (2026-11-10,
`apps/research-ui/app/[locale]/`) are:

| Phase | Routes | Built in |
| :-- | :-- | :-- |
| Workspaces | `/workspaces` (`/[locale]` forwards there) | M5-slim |
| 0 Inception | `/inception` (drafts), `/inception/scope`, `/inception/shape`, `/inception/criteria`, `/inception/review`, `/inception/done`. Explore and Direction have specs but no route | M4b |
| 1 Discovery | `/discovery`, `/discovery/plan`, `/discovery/recall`, `/discovery/harvest`, `/discovery/dedup`, `/discovery/report`, `/discovery/handoff`; Import is `/screening/import?return=discovery` | M3c-screens |
| 2 Screening | `/screening` (forwards to home), `/screening/home`, `/screening/import`, `/screening/prepare`, `/screening/triage`, `/screening/proposals`, `/screening/agreement`, `/screening/publish`, `/screening/export` | M1b-1 to M8-triage |

Job control and the pipeline builder stay API only.

**Browser allowlists.** Two lists carry the same rules and are kept equal by
tests: the development proxy (`apps/research-ui/app/api/console/[...path]/route.ts`,
pinned by `apps/research-ui/tests/console-proxy.test.ts`) and the packaged
app's browser surface (`src/scholar_harness/console/browser.py`, pinned by
`tests/console/test_browser_access.py`). GET and HEAD reach any `/api/v1/...`
path of plain segments. POST reaches only: screening `batch/{n}/decisions`,
`actions/pairing/(begin|redeem)`, `actions/defer`, `actions/publish`,
`decisions/events`, `decisions/conflicts/{id}/resolve`, `prepare`,
`corpus/(sources|accept)`, `corpus/sources/{id}/remove`,
`proposals/(runs|calibrations)`, `proposals/runs/{id}/cancel`; `workspaces` and
`workspaces/open`; inception `drafts`, `preview`, `steps/(scope|shape|criteria|matrix)`,
`drafts/{id}/genesis`, `drafts/{id}/recon/(probe|delta|distill|bind)`;
discovery `runs`, `recall`, `jobs/{id}/cancel`. PUT reaches only screening
`settings` and `approver`, `inception/drafts/{id}` and `discovery/report/methods`.
DELETE (for example discarding an inception draft), `/jobs/start`, `/pipelines`
POST and `/audit/events` POST are refused (`CONSOLE_METHOD_REFUSED`). Writes are
accepted only from the app's own origin, and the proposal read (which records a
reveal) only from the app's own pages.

No UI code remains in this package. Do not re-add a bundled SPA here: the UI's
transport rules (loopback-only upstream, path + method allowlist, streamed SSE,
GET-only CORS) are pinned in `apps/research-ui/tests/console-proxy.test.ts`.
In the packaged app, `create_app` is given the static export's folder
(`serve.py` `_UIFiles`) and `launcher.py` starts it; the export is built from
`apps/research-ui`, not kept here.

## 10. Acceptance matrix (hermetic tests)

| Test | Asserts |
| :-- | :-- |
| `test_status_endpoint_matches_cli` | `/workspace/status` JSON keys == `orchestrator.get_status()` keys on the same `tmp_path` workspace. |
| `test_job_lifecycle_success` | POST job → `queued→running→success`; journal event appended with matching `event_id`. |
| `test_job_failure_and_cancel` | failing command → `failed` + journal `FAILED`; cancel → SIGTERM path + `cancelled`. |
| `test_screening_parity` | GUI decisions file == agent `collect` output modulo review metadata. |
| `test_actions_table_drift` | every row's CLI parses `--help`; mcp_tool is an exported tool of `tools/scholar-agent-kit` (`server.py`). |
| `test_pipeline_dry_run_writes_nothing` | dry-run of a PRISMA template leaves `workspaces/<slug>` canonical tree byte-identical. |
| `test_pipeline_fingerprint_stable` | same spec JSON → same `sha256` fingerprint; re-running is idempotent. |
| `test_atomic_write_no_partials` | kill a decision POST mid-write; no partial `batch_NNN_decisions.json` survives. |
| `test_loopback_default_bind` | server defaults to `127.0.0.1`; `--host 0.0.0.0` emits the exposure warning. |