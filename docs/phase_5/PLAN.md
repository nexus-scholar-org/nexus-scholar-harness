# Phase 5 — Plan: Milestones, Scope, Sequencing

> **Status:** Planning | Companion docs: [`README.md`](./README.md) · [`BLUEPRINT.md`](./BLUEPRINT.md) · [`SPECS.md`](./SPECS.md)

## 1. Guiding principles

1. **Agent-first, console-second.** Anything the console can do, an agent can already do; the console only adds *sight and sign-off*. (D1)
2. **Wrap, don't rewrite.** All execution is `uv run <kit-cli>`; all state is workspace files. (D2, D3)
3. **Complexity is rationed.** Spent only on the pipeline-spec editor and the human-judgment screens. (Q2 in README)
4. **MCP/CLI parity as a tested invariant.** The action↔command mapping table is data with CI coverage. (D6)

## 2. Milestones

### M5.0 — Contract & Decision Lock (weeks 1)
- Freeze the design docs in this folder (v1.0.0). Record decisions D1–D6 in the audit ledger.
- Define `PipelineSpec` schema `0.1.0` (**SPECS.md** §3) and the Action→Command mapping seed set (**SPECS.md** §5).
- **Exit:** anyone can read the docs and state the console's exact guarantees. No code yet.

### M5.1 — Harness Console Server (weeks 2–3) — `scholar-harness serve`
- Add `serve` subcommand to `src/scholar_harness/cli.py`: FastAPI + uvicorn, loopback bind, static file serving.
- Read endpoints over the workspace contract (meta, status, literature lists, screening batch listing, synthesis/phase-4/exports listing, audit timeline).
- Job Runner (asyncio subprocess, PID tracking, kill, timeout, SSE events, job log + journal events).
- **Exit:** dashboard JSON identical to `scholar-harness status`; a test job (`scholar-verify trust-context") runs and its completion lands in `audit/journal.jsonl`. Hermetic tests in `tests/` using a `tmp_path` workspace.

### M5.2 — Phase 5 Console: read-only observability (weeks 3–4)
- Static single-page app: Dashboard, Literature browser (included/excluded/included counts + per-item metadata), Synthesis & Trust renderer (styled Markdown for `prisma_screening_report.md`, `evidence_matrix.md`, `consensus_*.md`, `trust_consensus*.md`), Graph iframe (`knowledge_graph.html`), Audit timeline.
- Reload-on-focus + SSE tick so it keeps working while agents edit the same files.
- **Exit:** a reviewer can walk the full Phase 0→4 trail of an existing workspace from the browser without touching the terminal.

### M5.3 — Screening & Verification Console (weeks 5–6)
- The human-judgment surface: list `literature/screening/batch_NNN.json`, show title/abstract/criteria, record per-item decision → append to `batch_NNN_decisions.json` in the same JSONL-free schema the agent handoff expects, then run `collect`.
- Verification review: render Phase-4 verdicts (RoB/COI/retraction/open-science) per study with one-click "acknowledged"/"dispute" annotations that write to `phase4/` review files + journal events.
- **Exit:** a full screen/collect cycle for one batch round-trips identically whether driven by the GUI or by `agent_screen.py` (test proves parity).

### M5.4 — No-Code Pipeline Builder (weeks 7–9)
- PipelineSpec editor (drag/stack/param-form v1; canvas DAG optional), instantiate 5c domain templates, dry-run on N samples, then full run through `scholar-harness run --pipeline`.
- Export: rendered `uv run` shell script and/or committed `pipeline.json`.
- **Exit:** a non-programmer composes Search → Dedup → Screen → Harvest → Synthesize → Trust from templates and runs it end-to-end; dry-run produces no writes to canonical files.



## 3. Explicit non-goals for this cycle (from BLUEPRINT §7)

No chat copilot in the browser, no DB, no Celery/RabbitMQ, no realtime sync, no auth service, no re-implementation of ranking/graph/verification logic, no SaaS.

## 4. Deliverables & verification matrix

| # | Deliverable | Target artifact | Verification |
| :--: | :-- | :-- | :-- |
| 1 | Harness console server | `scholar-harness serve` command | Hermetic tests: all GET endpoints return contract-shaped JSON for a `tmp_path` workspace; job lifecycle `queued→success`; failure & kill paths. |
| 2 | Read-only console | static app surfaces | Manual walkthrough milestone review on `workspaces/uav-cv-precision-agriculture`; every rendered metric matches `status`/`INDEX.md`. |
| 3 | Screening console | decision-writer + collect path | Parity test: GUI-driven `batch_NNN_decisions.json` byte-equal to one produced by `agent_screen.py collect` for the same decisions. |
| 4 | Pipeline builder | `PipelineSpec` editor + runner | Non-programmer runtest; dry-run writes nothing under `workspaces/`; exported script executes equivalently. |
| 5 | Agent exchange | mapping table + UI "see CLI command" | CI test: every table row's command is runnable `--help`-safe; labels never drift from commands. |
| 6 | Audit parity | journal writes for all mutations | Test: every Job and Decision event round-trips the `journal.jsonl` schema validated by `workspace-manager`. |

## 5. Sequencing rationale + risks

- **M5.1 before M5.2/3:** the read APIs are the only dependency; UI is static after that.
- **M5.3 borrows the existing agent handoff** (`agent_screen.py prepare|collect`) so the GUI never invents a screening format.
- **M5.4 last (and skippable)**: pipeline automation is the highest-value but most optional surface; if time-boxed, the console is still shippable with M5.1–M5.3.
- **Risk register**
  | Risk | Mitigation |
  | :-- | :-- |
  | Scope creep toward a "real web app" | D1–D6 + anti-scope list enforced at review. |
  | Console drifts from CLI semantics | Action→Command mapping table is data + CI parity tests. |
  | Concurrent file edits (agent + console) | atomic-rename writes, mtime reload, no locks; deterministic re-runs make races benign. |
  | Long-running jobs block the loopback server | asyncio subprocess with streaming + SSE; never inline `run_sync`. |
  | Screenshot-grade Markdown rendering drift | styled Markdown viewer + iframes for generated HTML; no custom renderers of research data. |

## 6. Success criteria (Phase 5, from `ROADMAP_ASSESSMENT_AND_TASK_LIST.md` + this plan)

- [ ] A non-programmer builds and runs a search→screen→harvest→synthesize pipeline from the console (M5.4).
- [ ] Every console action displays its exact `uv run` command; the mapping table is CI-tested (M5.1/2).
- [ ] A screening/verification round-trip completed in the GUI is byte-identical to the agent-driven path (M5.3).

- [ ] Console is still only "wraps + renders + triggers": zero kit logic duplicated (review gate at each milestone).