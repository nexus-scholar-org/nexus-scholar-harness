# Phase 5 — Collaboration & Empowerment: Design Docs

> **Status:** Planning (decision lock for Doc Set v1.0.0)
> **Date:** 2026-09-07
> **Consumes:** Phase 0–4 (harness CLI, 8 kits, workspace file contract, audit ledger, MCP)
> **Design north star:** *The agent is the primary interface; any GUI is a thin view + trigger over the same contract.*

This folder holds the Phase 5 design set. Read them in order:

| Doc | Answers |
| :-- | :-- |
| [`PLAN.md`](./PLAN.md) | What we build, in what order, what we deliberately do NOT build, success criteria. |
| [`BLUEPRINT.md`](./BLUEPRINT.md) | Architecture: the "harness console" pattern, system layers, agent parity, data & job flow. |
| [`SPECS.md`](./SPECS.md) | Concrete contracts: server API, `PipelineSpec` JSON schema, UI screens, acceptance matrix. |

---

## 1. What Phase 5 Is (and is not)

Phase 5 was envisioned (`docs/UPCOMING_WORK.md` §Phase 5 and the now-archived `OPEN_SCIENCE_ROADMAP_v1.md` deep-dive) as: **5a shared research workspaces**, **5b no-code workflow builder**, **5c domain-specific 1-click templates**. The repo contains two competing visions for "UI":

1. A now-archived web-app vision (`08_production_web_app.md` in `brainstorming/methodology-tooling/`) — a Next.js/React + FastAPI + Celery app ("Nexus Science") with a Claude-like chat copilot.
2. A now-archived agent-native vision (`09_agent_native_ecosystem.md` in `brainstorming/methodology-tooling/`) — the "headless advantage": package everything as MCP + skills, build zero UI code.

> Archival note: the `brainstorming/` deep-dives were removed from the tree on 2026-09-11. Restore from snapshot `72090e5` (see [`docs/COMMIT_SNAPSHOTS.md`](../COMMIT_SNAPSHOTS.md)) if the full text is needed.

**This design set resolves the tension: build a thin "harness console", not a thick web app, and keep the agent-native ecosystem as the backbone.** The console is a *second-class citizen by design*: it renders the same files agents read and triggers the same `uv run` CLI commands agents run. It never owns state.

---

## 2. Decision Log (why the console is thin)

| # | Decision | Rationale | Source conflict resolved |
| :--: | :-- | :-- | :-- |
| D1 | **Primary interface = agent-agnostic surface** (CLI + MCP + workspace files). The Phase 5 GUI is a **secondary observability + human-judgment surface**. | The product is already used agent-agnostically (opencode, Claude, GitHub Copilot, etc.). A UI that can't be driven in parallel by an agent breaks the workflow. | 08 vs 09 — 09 wins for interface primacy. |
| D2 | **Wrap, don't rewrite.** Console actions invoke kit CLIs via `uv run` and read workspace files directly. Zero logic duplication. | Keeps Phase-3 invariant #1 (zero state desync) and #2 (deterministic reproducibility) trivially true. | 08's "rewrap orchestrator as API" → kept minimal. |
| D3 | **Filesystem is the database.** No DB, no Celery/RabbitMQ, no realtime sync service in v1. | `project.json`, `INDEX.md`, `audit/journal.jsonl`, `literature/`, `synthesis/`, `phase4/` already ARE the canonical state. Adding a DB recreates the desync the repo has engineered away. | Roadmap "survives >50 concurrent edits" → meet via atomic-file discipline + reload, not a server. |
| D4 | **Chat stays in the agent.** The console offers no LLM chat panel. | The coding agents already do conversationally; a WebSocket copilot re-implements them poorly. Console focuses on *binding decisions* (screening, verification, export) where humans must sign off. | 08's "killer copilot" → deferred to agent layer. |
| D5 | **Auth/RBAC abandoned.** v1 is localhost-only, single user. Collaboration = git + audit ledger. | Building auth violates the thin-client principle. | 5a "cloud workspaces" → completely removed. |
| D6 | **Every console action has an explicit CLI/MCP equivalent** shown in the UI ("agent exchange"). | Guarantees anything a human does in the GUI, an agent can reproduce headlessly. | New invariant, added by this design. |

The single most important consequence of D1–D6: **the UI cannot become complicated without breaking its own contract.** Complexity budget is spent only where a GUI genuinely beats an agent — the **screening/verification human-judgment screens** and the **no-code pipeline builder** (itself just an editor for a JSON spec the CLI already consumes).

---

## 3. How the sections of the roadmap map onto this design

| Roadmap item | Phase 5 deliverable | Principle |
| :-- | :-- | :-- |
| **5a Shared workspaces** | Local-first console; collaboration via git + audit journal. | Filesystem-as-state; no sync engine. |
| **5b No-code workflow builder** | `PipelineSpec` (JSON) editor → dry-run on sample → export to `uv run` script or `scholar-harness run --pipeline` (M5.4) | Builder edits the same contract the CLI executes. |
| **5c Domain templates** | Library of preset `PipelineSpec` archetypes (PRISMA SLR, scoping review, REA, meta-research) | 1-click = instantiate a spec, not new logic. |

---

## 4. Key Q&A (addressed in detail)

### Q1. "Can we leverage a kind of harness UI?" — **Yes, and it is the recommended path.**

The most effective Phase 5 killer feature is not a dashboard — it is **proving that one mental model drives every surface**:

```
researcher ──► opencode / Claude / Copilot (agents)        ──┐
researcher ──► scholar-harness CLI (Terminal)               ├─► workspace files ──► kits
researcher ──► Phase 5 Harness Console (localhost web)  ─────┘    (canonical state)
```

The console's `status` screen is literally `orchestrator.get_status()` rendered in HTML; its "Run search" button shells out to `uv run scholar-search ...`; its audit timeline reads `journal.jsonl`. Everything the harness can do, the console can *show and trigger* with ~0 net-new capability code.

### Q2. "Should the UI be complicated?" — **No.**

- **Not complicated =** a static single-page HTML console served by one small FastAPI/uvicorn process, vendored JS (the repo already vendors `vis`/`tom-select` under `lib/`), reading files + spawning CLIs, no database.
- **Complicated =** its own state layer, DB, message broker, auth system, realtime collaborative cursors, an in-browser LLM chat. Every one of those adds a second source of truth that the agents (the real users) will fight with.
- Complication is **permitted in exactly two places** and both are small: the pipeline-spec editor and the screening/verification screens — because those are the moments a human, not an agent, must decide.

### Q3. Who is the console for?

Reviewers/PIs who must make and sign **binding decisions** (PRISMA inclusion, COI/verdict adjudication, export finalization), non-engineering collaborators, and teaching/landscape demos. Not a replacement for the agent interface.

### Q4. Where does the "collaborative shared workspace" go?

Into **git + the append-only audit journal**, not a realtime server. Two people reviewing the same workspace review the same files; the journal records who decided what when; conflict prevention is atomic-rename write discipline (already the repo's pattern) plus the built-in determinism that makes re-runs safe.

### Q5. Is the archived web app vision (`08_production_web_app.md`) abandoned?

**Yes. Abandoned entirely.** The console is the maximal UI that stays honest to the harness. We are committing exclusively to the thin, local-first, agent-agnostic architecture.

---

## 5. Repository Provenance (grounding)

- Harness CLI surface: `src/scholar_harness/cli.py` (`status`, `sync`, `run`, `export`, `inception`) and `orchestrator.py`.
- Agent handoff screening: `src/scholar_harness/agent_screen.py` (`prepare|status|collect`), batches `literature/screening/batch_NNN.json` → `batch_NNN_decisions.json`.
- MCP: `tools/scholar-agent-kit` (13 `nexus_*` tools: `nexus_protocol_compile|validate|render_criteria`, `nexus_discover`, `nexus_dedup`, `nexus_screen`, `nexus_extract_pdf`, `nexus_rag_index|query|synthesize`, `nexus_matrix_extract`, `nexus_graph_build`, `nexus_bib_clean`), `.agents/plugins/nexus-scholar/mcp_config.json`.
- Workspace contract: `workspaces/<slug>/` (`AGENTS.md` section "Where research output goes").
- Existing generated UIs to embed rather than rebuild: `scholar-graph-kit` `map.html` (PyVis), `scholar-rag-kit` renderings, `prisma_screening_report.md`, `phase4/trust_consensus*.md`.
- Prior design threads this supersedes/reconciles (archived in `brainstorming/`; restore from snapshot `72090e5` if needed): `PHASE_3_INTERACTIVE_INTERFACES_DEEP_DIVE.md`, `methodology-tooling/08_production_web_app.md`, `methodology-tooling/09_agent_native_ecosystem.md`, `OPEN_SCIENCE_ROADMAP_v1.md` §PHASE 5.