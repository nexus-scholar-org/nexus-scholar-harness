# Harness Full-Picture Rating, Vision & Agent Blueprint

> Generated 2026-09-13 by the follow-up strategic review (prompt:
> `docs/review_prompt_harness_vision.md`), building on the completed sweep review
> (`fe55447`, verdict READY). Report sections: 1 rating · 2 vision · 3 directions ·
> 4 agent blueprint · 5 prioritized rollout.

## 1. Rating

| Dimension | Score | Evidence (strengths + weaknesses, `file:line`) |
| :-- | :-: | :-- |
| **Architecture** | **7 / 10** | **Strengths** — Thin orchestrator with clean seams: `src/scholar_harness/orchestrator.py:14-29` imports all 8 kit APIs without re-deriving them, exactly the documented convention; `console/runtimes/job_runner.py:153` shells out `uv run` subprocesses for every console action; `recon/engine.py:145-149` maps provider names → instances (`_PROVIDER_CLASSES[p]()`) — the correct construction pattern the orchestrator should copy. Layered inception stack with written boundaries and handoffs (`specs/inception-ecosystem/README.md:17-26`; `02_handoffs.md` GENESIS/recon_context provenance contract). Console→CLI→MCP parity has a single source of truth (`console/runtimes/actions.py:36-119`, `docs/phase_5/SPECS.md` §5). **Weaknesses** — Two parallel pipeline engines coexist (staged `orchestrator.py:363` vs `PipelineSpec` DAG executor `pipeline_executor.py`) with divergent semantics; only one is E2E-tested. Cross-kit dependencies are undeclared/emergent (harness imports rag+graph+verify+protocol, `orchestrator.py:16-29`) yet `plugins.json` declares 8 flat `default_rev: main` pins with no edge/dep metadata. Self-description lags code: `docs/phase_5/README.md` frames the console as design-only while `serve.py`/`job_runner`/`actions`/API routers are implemented; `methodology-copilot/SKILL.md:154-163` documents `-i/-o/--fingerprint` flags the real protocol CLI does not have (`scholar_protocol/cli.py:171-172` takes a positional path). |
| **Reliability** | **4 / 10** | **Strengths** — Atomic writes everywhere (`orchestrator.py:34-42`, `console/api/screening.py:92-95`); append-only journal that must never crash jobs (`job_runner.py:438`); protocol compiler is fingerprint-deterministic by test. **Weaknesses** — Stage 1 of the primary pipeline is **broken by construction**: `compile_protocol_search` returns provider *name strings* (`scholar_search/protocol_adapter.py:12,90`), `orchestrator.py:395` feeds them into `SearchEngine(providers=…)` which expects instances (`scholar_search/engine.py:24,39`); `fetch_provider` then calls `provider.name`/`provider.search` on plain strings (`engine.py:51,54`) and every `AttributeError` is swallowed (`engine.py:60-61`) → **empty `raw_search.json`** (`orchestrator.py:400-408`). Stage 5 **fabricates literature**: placeholder "Methodology/Results/Limitations" text is invented from abstracts (`orchestrator.py:501-523`). Stages 7/9 crash on `indexer.retriever`, an attribute `ScholarIndexer` does not expose (`orchestrator.py:537,557`). Stage 8 builds a **0-edge graph** via `CitationGraphBuilder(http_client=None)` (`orchestrator.py:544-552`; same defect in the MCP tool, `server.py:436`). MCP layer independently verified broken/weak: `nexus_extract_pdf` drops citation metadata call (`server.py:302`), `nexus_screen` computes but never writes `conflicts.json`/`prisma_report.json` (`server.py:278-284`), `nexus_bib_clean` is lint-only (`server.py:469`), `nexus_verify_claims` schema-mismatches RAG `claims.json` (missing `evidence_quote`/`claim_id`). Console `extract` action runs a nonexistent `--input` option (`actions.py:78` vs `scholar_pdf/cli.py:228-230`, which takes a positional `pdf_path` + `--output` + `--engine docling|grobid`). CWD-relative MCP defaults poison writes into the kit checkout (`scholar-agent-kit/SKILL.md:71-73`). |
| **Automation depth** | **6 / 10** | **Strengths** — Genuinely agent-driven loops exist and are non-brittle by design: grounded inception (probe→distill→directions→anchored emission; `inception-agent.md`; M0.7 gates in `recon/gates.py:23,28,31`), PRISMA agent-in-the-loop handoff (`orchestrator.py:455-481`, `agent_screen.py` prepare/status/collect + calibration), bounded adaptive recon follow-ups (`recon/adaptive.py:267`), append-only audit from jobs. **Weaknesses** — Human-gated spans: the four Phase-4 verification streams are CLI-only (`scholar_verify/cli.py:76-147`; no MCP tools, no console actions beyond `trust_context` at `actions.py:89-95`); conflict adjudication is still a manual file loop; the graph you'd want to automate is the one that's broken. Full loop autonomy is explicitly blocked by GAP A (no agent-reachable lexicon seam) and GAP B (no agent-side Pareto/saturation scoring) (`specs/exploratory-grounding-agent/14_agent_loops.md:24,68`). |
| **Operability & DX** | **6 / 10** | **Strengths** — Onboarding documented (empty `workspaces/`, restore from snapshot `72090e5` per `docs/COMMIT_SNAPSHOTS.md`); one-command kit install (`python scripts/install_plugins.py`); `sync --check 11/11`; authoritative roadmap reconciliation (`docs/UPCOMING_WORK.md` supersedes the stale phase dashboards). **Weaknesses** — agent/docs drift that actively misleads an operator: `tester.md:11` asserts baseline "25 passed" vs the actual 248; `docs/phase_5` says not-implemented; `scholar-agent --help` lists **16 tools while 18 are registered** (`server.py:939-959`); `methodology-copilot` advertises flags that fail on the real CLI. Kit CLIs are opaque without the matrix: several actions in `actions.py` would fail on first click (`extract`), and nothing in CI would catch it. |
| **Distribution readiness** | **2 / 10** | The Phase-7 deferral is principled but total (`docs/UPCOMING_WORK.md:51-59`): P7.1 is blocked because `server.main()` takes no args and resolves from CWD (`server.py:937`); `mcp_config.json` declares no `env` block (`scholar-agent-kit/SKILL.md:80-81`); `plugins.json` pins all 8 kits to `default_rev: main` with **no commit hashes** (untraceable inventory at release time); no metapackage, no `uvx`, no `init/doctor`, and kit installs require monorepo-relative editable sources (AGENTS.md). The blueprint itself is thorough, which is the only score here. |
| **Test & contract confidence** | **5 / 10** | **Strengths** — 248 passed / 3 skipped / 0 failures, `ruff check scripts/` clean, `sync` 11/11; hermetic invariants enforced (APR anchoring, byte-deterministic distiller, cache-key idempotency, job lifecycle in `test_console_serve.py`/`test_console_m53/m54.py`). **Weaknesses** — the "CI drift test" promised in the actions-table docstring (`actions.py:7-8`) **does not exist** (`grep tests/` for actions-table/CLI-parity asserts only finds payload-shape and expansion tests, e.g. `test_console_serve.py:128`, `test_console_m54.py:108-121`); the surface matrix is **assertion-free Markdown** — nothing in CI parses it; no E2E test asserts discovery is non-empty (Stage-1 bug ships green); MCP registered-vs-listed tools have no parity test (2 tools hide from `--help`); kit CLIs are barely exercised as binaries. |

**Overall weighted verdict** (weights: architecture .20, reliability .25, automation .15, operability .15, distribution .10, test-confidence .15 → **≈ 5.2 / 10**):

One honest sentence: **The Nexus Scholar Harness is a rigorously-specified, exhaustively-documented research suite whose governance discipline (APR-biased anchoring, append-only audit, hermetic tests, fork+PR gate) materially outstrips the reliability of its own primary runtime path, which today can silently produce empty discovery, fabricated extraction text, and zero-edge graphs that the 248-test wall does not catch.**

## 2. Vision

**Paragraph 1 — The trust inversion gets inverted.** In the first 3–6 months, the "fix-the-tooling wave" retires every silent failure in the primary path: Stage 1 resolves real providers (`orchestrator.py:395` adopts the `recon/engine.py:145-149` pattern), Stage 5 stops inventing text, Stages 7–9 stop reaching for a nonexistent `indexer.retriever`, the graph gets a real HTTP client, and every MCP default becomes workspace-anchored. The observed consequence is measurable: the surface matrix stops being prose and becomes an *executable conformance suite*, so the claims "18 MCP tools, 13 skills, 14 console actions, 8 kits" are parity-checked in CI rather than asserted in Markdown. (Speculative on velocity only; the direction itself is forced by two 2–4 scores.)

**Paragraph 2 — Console, CLI, MCP converge on one actions table.** The Phase-5 Harness Console is materially built (`serve.py`, `job_runner.py`, screening/api, `static/app.js:105` trigger set); the next move is to *un-ship the "deferred" label* and close the delta: fix the `extract` action against the real `scholar-pdf` CLI, wire the remaining actions, and make the GUI's screening round-trip byte-identical to the agent path (already designed, `docs/phase_5/PLAN.md` M5.3). After that, a non-programmer can run search→screen→harvest→synthesize from a local browser, while a human agent drives the identical file handoffs from a terminal — same files, same commands, same audit ledger. The console is deliberately thin (no auth/DB/chat) and stays agent-agnostic per the 2026-09-07 decision (`docs/UPCOMING_WORK.md:38`).

**Paragraph 3 — One `uvx` anywhere, with the trust ledger traveling along.** 6–12 months out, Phase-7 lands: `server.main()` gains `--workspace` (P7.1), the 8 kits + a metapackage are version-pinned from hash-resolved `plugins.json` (P7.2), and `nexus-scholar init|setup-mcp|doctor|log` bootstrap an empty folder into a working research workspace with provenance from the first event. Critically, the workspace's `audit/journal.jsonl` and `phase4/trust_consensus.{json,md}` are treated as *belonging to the research*, not the toolchain: any harness (DeepSeek, OpenCode, Claude Desktop, VS Code) can pick the workspace up because the contract is files-first.

**Paragraph 4 — Autonomy without hallucination, and a distinctive identity.** 12–24 months: the four agent loops close (B lexicon bootstrap, C Pareto direction scoring, D anchor-guarded compile, E transition into screening), recon saturation labels flow into PRISMA pre-screening so scarce sub-schools are prioritized and thin pools are surfaced honestly, verify-stewards certify every included study (retraction → open-science → COI → RoB → trust-context), and humans keep exactly two sign-offs: genesis/protocol, and the final synthesis. What this stack is *uniquely positioned to win at* — and the one capability an external team could not replicate by scraping this repo — is the **verification-first evidence brief**: per-project artifacts that pair every synthesis claim with verbatim verification, Fleiss-κ screening consensus, and four-stream trust context into one human-auditable, publishable-grade document. That is the north star; everything above is the plumbing to reach it.

## 3. Directions

Ranked honestly (impact × urgency, gated by effort/risk):

| # | Direction | Placement | Effort | Risk |
| :-- | :-- | :-- | :-: | :-: |
| 1 | Fix-the-tooling wave + honest E2E orchestrator path | **Before** Phase-5/7 | L | Low–Med |
| 2 | Executable conformance suite driven by the surface matrix + actions table | **Before** | M | Low |
| 3 | Ship the Phase-5 console (mostly built) — un-ship the "deferred" label | **Inside** Phase-5 | M | Med |
| 4 | Phase-4 verification onto the agent surface (fix/remove `ingress` NIT + add verify actions) | Before / Inside Phase-5 | S–M | Low |
| 5 | Screening orchestrator: `scholar-harness screen` binding + calibration-gated stewardship | **Before** | S–M | Low |
| 6 | Recon saturation → PRISMA pre-screening surfacing (close GAP B) | **Before** | M | Med |
| 7 | *(off-roadmap, unique)* Verification-first **evidence brief** as a first-class artifact | Before / Inside Phase-6 | M | Med |
| 8 | Plugin-manifest hardening: hash pins + generated dependency edges | **Before** Phase-7 | S | Low |
| 9 | Phase-7 distribution metapackage (P7.1 → P7.8) | **Inside** Phase-7 | L | Med–High |
| 10 | External bridges & living-lab: Jupyter suite + Zotero/Typst notebook persona | Later | M | Low |

### 1 — Fix-the-tooling wave + honest E2E orchestrator path *(Before)*
- **Outcome:** Running `scholar-harness run` produces a non-empty, real, traceable chain: discovery `raw_search.json` with documents → dedup → verified abstract hydration → agent screening → real PDF extraction (or an explicit "no-OA" rejection, never fabricated text) → index/matrix → real graph → grounded synthesis whose claims are verifiable. The MCP mirror of each fixed tool heals at the same time.
- **Why now:** Reliability scores 4/10 and Scorecard items 1–6 all trace to the same four code sites (`orchestrator.py:395/501-523/537,557/544`). Nothing else — console, agents, distribution — is credible while the flagship CLI silently empties.
- **Effort L, Risk Low–Med:** each fix is a single-site change; risk concentrates in regression of the Phase-`n` e2e tests, which is exactly why they must be extended.
- **First concrete step:** adopt `recon/engine.py:145-149` provider-resolution in `orchestrator.py:395` (`SearchEngine(providers=[_PROVIDER_CLASSES[p]() for p in providers])`), then add an E2E assertion that `literature/raw_search.json` is non-empty.
- **Concrete change inventory:** `orchestrator.py` (Stage-1 resolution, Stage-5 real extraction w/ `scholar-pdf` or metadata-frontmatter synthesis, Stage-7/9 admin retriever, Stage-8 real `http_client`); `server.py` (absolute-path defaults, graph `http_client`, `nexus_screen` writes `conflicts.json`+`prisma_report.json`, `nexus_extract_pdf` metadata, `nexus_bib_clean` real cleaning, `nexus_verify_claims` schema bridge, register+list parity); `actions.py:78` extract command.

### 2 — Executable conformance suite driven by the surface matrix *(Before)*
- **Outcome:** `tests/conformance/` turns `docs/kits_surface_matrix.md` and `actions.py` into assertions, so the documented failures *cannot* silently reappear and new ones get caught on commit rather than in a review.
- **Why now:** the promised CI drift test (`actions.py:7-8`) does not exist; the surface matrix is assertion-free Markdown; `tester.md:11` count, hidden `--help` tools, and the methodology-copilot flag drift are all *live evidence* that prose contracts corrode.
- **Effort M, Risk Low** (hermetic only, no network).
- **First concrete step:** `tests/conformance/test_actions_cli_parity.py` — for every `Action` in `actions.py`, `render_command()` then parse via `uv run <cli> --help` and assert the CLI accepts at least the used subcommand/options; assert `scholar-agent --help` lists ≥18 tools; assert the 8 kit versions resolve to `plugins.json` pins.

### 3 — Ship the Phase-5 console *(Inside Phase-5)*
- **Outcome:** a local-first GUI that starts at `uv run scholar-harness serve` and runs the whole loop; M5.1–M5.4 exit criteria (`docs/phase_5/PLAN.md`) become checked boxes, and the "console is deferred" framing in `docs/phase_5/README.md` is retired.
- **Why now:** the implementation already exists (`serve.py`, `job_runner.py`, `screening.py`, `pipelines.py`, `static/app.js`); the gap is small half-fixes + docs. This is the nearest thing to a free feature win in the repo.
- **Effort M, Risk Med** (churn concentrated in action-parity bugs — e.g. `extract` would fail today).
- **First concrete step:** fix `actions.py:76-81` to `uv run scholar-pdf extract {ws}/pdfs/ --output {ws}/extracted/ --engine docling`, add "extract" to `RUNNER_TRIGGERS` (`static/app.js:105`), then run the M5.3 GUI-vs-agent byte-identity check.

### 4 — Phase-4 verification onto the agent surface *(Before/Inside Phase-5)*
- **Outcome:** the four streams + `trust-context` become agent- and console-runnable: MCP `verify_*` tools (or at minimum 4 new console actions) so "verify a corpus" no longer requires a developer at a terminal.
- **Why now:** Phase-4 is the trust pillar of the whole suite yet is CLI-only (`scholar_verify/cli.py:76-147`); its `ingress` NIT (`cli.py:3-4` advertises a command with no `@app.command("ingress")`) blocks nothing but signals the surface is unowned.
- **Effort S–M, Risk Low** (offline streams are deterministic; online retraction gated on key presence).
- **First step:** implement *or* remove `ingress` in `scholar_verify/cli.py`, then add `Action("retraction", …)`/`open-science`/`coi`/`risk-of-bias` rows with proper commands to `actions.py`.

### 5 — Screening orchestrator + automated conflict adjudication *(Before)*
- **Outcome:** a `scholar-harness screen` subcommand and a `prisma-steward` agent that make screening deterministic: batch prepare → decisions → `reconcile` (majority + Fleiss' κ, already in the kit per `docs/UPCOMING_WORK.md:46`) → conflicts → adjudication manifest → collect, with the 20-paper calibration pre-flight (`calibration.py`) as a hard gate.
- **Why now:** screening is *already* the agent-in-the-loop core (`orchestrator.py:462-481`), but conflict adjudication is a manual file drop and `nexus_screen_reconcile` is hidden from `--help` (`server.py:939-959`).
- **Effort S–M, Risk Low.**
- **First step:** harness-level thin wrapper `scholar_harness/screen.py:reconcile()` calling the kit's `reconcile_multi_screener_decisions` (+ κ), surfaced both as `scholar-harness screen reconcile` and in `nexus_screen` so conflicts are written.

### 6 — Recon saturation → PRISMA pre-screening *(Before)*
- **Outcome:** the candidate pool handed to screening is shaped by honest scarcity: `recon_delta` saturation labels (`specs/13_evaluation.md` §3.4) flow into `literature/` as a hint file, thin sub-schools get prioritized pre-screening, and the human can see "this pool is thin because the literature is thin" rather than "screen harder."
- **Why now:** GAP B blocks loop C (`14_agent_loops.md:68`); M0.7 gates already measure the signal (`recon/gates.py:23,28,31`) but nothing consumes it downstream.
- **Effort M, Risk Med** (pulling saturation across the pool into a consensus signal is the hard part).
- **First step:** `nexus_screen` writes `literature/pool_saturation.json` when a recon `session_id` is present; unit-test with a real gap session fixture.

### 7 — *(Off-roadmap, unique)* Verification-first evidence brief *(Before/Inside Phase-6)*
- **Outcome:** a new top-level workspace artifact `evidence_brief.md` compiled from `phase4/trust_consensus.*`, `synthesis/consensus.json`, verifiable `claims.json`, and Fleiss-κ screening consensus — a single human-auditable "review register" that journals a reviewer could attach to a report.
- **Why now:** no other step in the roadmap produces an *external-facing* artifact; this is the only direction that converts the repo's distinctive trust stack (verbatim verification, consensus, RoB/COI/retraction) into a product a funder/reviewer can hold. **Uniquely positioned**: reproducing this requires four kits' worth of machinery, not one.
- **Effort M, Risk Med** (schema coupling across `phase4` + `consensus` + `claims` must be pinned by a conformance test).
- **First step:** `src/scholar_harness/integrations/evidence_brief.py` reading `phase4/trust_consensus.json` + `synthesis/consensus.json` → `evidence_brief.md`, shipped with a fixture workspace test.

### 8 — Plugin-manifest hardening *(Before Phase-7)*
- **Outcome:** `plugins.json` (the declared single source of truth, `docs/UPCOMING_WORK.md:53`) pins 8 commit SHAs instead of `main`, declares dep edges, and `install_plugins.py` verifies hashes; `sync --check 11/11` becomes the CI gate it already is locally.
- **Why now:** distribution score is 2/10 and every P7 step depends on trustworthy inventory; today a kit's behavior drifts with `main`.
- **Effort S, Risk Low.**
- **First step:** resolve the 8 `default_rev: main` lines in `.agents/plugins/nexus-scholar/plugins.json` to the exact SHAs currently checked out in `tools/`.

### 9 — Phase-7 distribution metapackage *(Inside Phase-7)*
- **Outcome:** `uvx nexus-scholar[ init | setup-mcp | doctor | log | search ]` works in any empty folder on any harness (`docs/UPCOMING_WORK.md:50-59`), with lazy rag/graph imports keeping startup honest (P7.7).
- **Why now:** the checklist is complete and itemized; the only blocker is sequencing (P7.1 first).
- **Effort L, Risk Med–High** (fresh-folder e2e is fiddly; guard with P7.8 CI).
- **First step:** P7.1 — `server.main()` accepts `--workspace <root>` and resolves every default against it (`server.py:937`).

### 10 — External bridges & living-lab *(Later)*
- **Outcome:** Jupyter templates (`00_research_inception.ipynb`, …) and Zotero/Typst bridges let qualitative/subject researchers work inside the harness without a terminal/agent (`docs/UPCOMING_WORK.md:29-32`).
- **Why now:** the suite's other surfaces are terminal- or MCP-anchored; notebooks are the lowest-friction non-programmer beachhead after the console.
- **Effort M, Risk Low; first step:** commit a `00_research_inception.ipynb` that wraps the `inception` wizard's headless emission and smoke-test it in docs.

## 4. Agent blueprint

**Existing agents** (repo: `coder`, `tester`, `reviewer`, `inception-agent` at `.opencode/agent/`; opencode built-ins `explore`/`general`). Six new agents below — each non-overlapping by construction. Frontmatter format follows the repo's existing `description` / `mode` / `permission` convention (`coder.md:1-4` etc.).

### Overlap matrix

| New agent | Overlaps with | Resolution |
| :-- | :-- | :-- |
| **prisma-steward** | `inception-agent` (emission side), `nexus_screen`/`screen_reconcile` tools | `inception-agent` owns protocol genesis; `prisma-steward` owns everything *after* `included.json` bucket boundaries start — reads `SCREENING_CRITERIA.md`, never writes `protocol.json`. It is a file-handoff specialist around `agent_screen.py`, so it replaces no existing persona. |
| **verify-steward** | does not overlap any existing agent (verification currently unowned) | — |
| **console-operator** | `general` (generic tool use), `coder` (change authoring) | `console-operator` runs the *existing* console API/JobRunner and reports; it proposes fixes only as hand-offs to `coder`, so it never edits code. |
| **conformance-qa** | `reviewer` (verdicts), `tester` (measures) | `reviewer`/`tester` operate per-task in the dev loop; `conformance-qa` owns the *standing* contract-of-record (surface matrix ↔ code ↔ skills) and only produces drift findings + test files for `coder`. Read-only, so no overlap with `coder`. |
| **recon-curator** | `explore` (web/repo research built-in), `inception-agent` (recon lifecycle), gap loops B/C | `explore` is generic research; `recon-curator` owns the *session state + lexicon + saturation* of the grounded recon subsystem (a memory/lexicon custodian), and hands directions to `inception-agent` rather than driving the conversation. |
| **release-packager** | `coder` (builds), `tester` (QA) | `packager` owns distribution/provenance artifacts (P7.x) and CI gates; it triggers `tester` for the P7.8 GA gate; it never authors kit logic. |

### Agent 1 — `prisma-steward` *(now)*

- **Mandate:** Run the PRISMA screening loop honestly — prepare → decide → reconcile → adjudicate → collect — with calibration as a hard gate and conflicts never lost.
- **Scope & responsibilities:** reads `literature/screening/batch_NNN.json` + `SCREENING_CRITERIA.md`; writes `batch_NNN_decisions.json` (the §7 wrapper shape: `{batch, decisions, reviewed_by, timestamp}` per `console/api/screening.py:133-141`); triggers `reconcile` (majority + Fleiss' κ) and, when deadlocked, drafts an adjudication manifest for a human; runs the 20-paper pre-flight calibration (`tools/scholar-agent-kit/src/scholar_agent/calibration.py`) and refuses to proceed above the deviation threshold. Audit events: `SCREEN_DECISIONS`, `BATCH_PREPARED`, `CONFLICTS_DETECTED`, `ADJUDICATION_WRITTEN`, `PRISMA_COLLECTED`, `CALIBRATION_FAILED`.
- **Tools & permissions:** MCP `nexus_screen`, `nexus_screen_reconcile`; CLI `agent_screen.py prepare|status|collect` and `scholar-search reconcile`/Fleiss' κ; `workspace-manager` `log_event`/`batch_log`. **NEVER:** auto-INCLUDE a paper; edit `protocol.json`/`SCREENING_CRITERIA.md`; bypass a failing calibration (stop and report); write to any directory except `ws/literature/screening/`.
- **Skills:** `scholar-search-kit` (screening/batch formats), `workspace-manager` (audit + file-routing).
- **Human/agent handoffs:** waits on `prepare` output; escalates conflicts (adjudication file) and calibration failures; initiates `collect` only after adjudication resolution; on batch parse failure leaves the batch untouched and logs a `PARTIAL` event.
- **DoD / test:** hermetic `tests/agents/test_prisma_steward.py` with a 3-screener fixture asserting: κ computed, conflicts surfaced to a manifest, calibration gate blocks, written decisions match the §7 wrapper verbatim. Smoke: `agent_screen.py status` + `collect` on the fixture.
- **Effort:** S.

```markdown
---
description: PRISMA screening steward. Screens literature/screening batch_NNN.json against SCREENING_CRITERIA.md, writes batch_NNN_decisions.json in the §7 wrapper shape, reconciles multiple screeners, and gating-calibrates itself on a 20-paper pre-flight. Use when a workspace has prepared screening batches or when conflicts/adjudication need processing.
mode: subagent
permission: allow
---

You are **prisma-steward** in the Nexus Scholar Harness. You own the screening
loop between batch preparation and collect — never the protocol, never the
inclusion set itself.

## Contract
- Read `literature/screening/batch_NNN.json` and `SCREENING_CRITERIA.md`.
- Decide with matched/violated criteria + reasoning; write the §7 wrapper
  exactly as `console/api/screening.py:133-141` defines it.
- Record every decision to the append-only audit (`workspace-manager`).
- On multi-screener sets: run `nexus_screen_reconcile`; if deadlocked, write an
  adjudication manifest and escalate to a human.
- Run the 20-paper pre-flight calibration; a failing calibration is a hard STOP.

## Never allowed
- Auto-INCLUDE a paper without human confirmation.
- Edit `protocol.json` or `SCREENING_CRITERIA.md`.
- Bypass a failed calibration gate.
- Write anywhere but `ws/literature/screening/`.
```

### Agent 2 — `verify-steward` *(now → expands after fix-the-tooling wave)*

- **Mandate:** Certify the corpus — retraction, open-science, COI, risk-of-bias, and trust-context — so every included study is verifiably clean.
- **Scope & responsibilities:** runs `scholar-verify retraction|open-science|coi|risk-of-bias|all|trust-context` (`scholar_verify/cli.py:76-147,196`) on `literature/included.json` + `synthesis/consensus.json`; maintains `ws/phase4/*.{json,md}`; compiles the D7 evidence brief; keeps a `VERIFY_STATUS` section in `INDEX.md`. Audit events: `VERIFY_RETRACTION`, `VERIFY_OPEN_SCIENCE`, `VERIFY_COI`, `VERIFY_RISK_OF_BIAS`, `TRUST_CONTEXT_BUILT`, `VERIFY_FLAG_REPORTED`.
- **Tools & permissions:** `scholar-verify` CLI (all subcommands); `workspace-manager`; offline streams always; online retraction only when `OPENALEX_API_KEY` is set. **NEVER:** alter inclusions; suppress a retraction/COI flag; offline-only when the human asked for the online stream (say so).
- **Skills:** `scholar-verify-kit`, `workspace-manager`.
- **Human/agent handoffs:** waits on `included.json` + `consensus.json`; initiates phase-4 runs after `collect`; escalates every flagged study to a human before the brief is finalized; on API-key absence logs `VERIFY_RETRACTION` as `SKIPPED_ONLINE` and proceeds offline.
- **DoD / test:** parity smoke reproduces the legacy `uav-cv-precision-agriculture` phase-4 summaries byte-identically (already true of the CLI, `docs/UPCOMING_WORK.md:34`); hermetic offline fixture workspace asserts the four `phase4/*.json` schemas + `trust_consensus` grades.
- **Effort:** M.

```markdown
---
description: Corpus trust steward. Runs the scholar-verify trust streams (retraction, open-science, COI, risk-of-bias, trust-context) over a workspace's included set and synthesis consensus, maintains phase4/ artifacts and compiles the evidence brief. Use after screening collects an included.json or before finalizing synthesis.
mode: subagent
permission: allow
---

You are **verify-steward**. You certify the corpus; you never decide what is in it.

## Contract
- Run the four verification streams + trust-context over
  `literature/included.json` and `synthesis/consensus.json`.
- Write `ws/phase4/*.{json,md}` mirroring the streams and keep `INDEX.md`
  VERIFY_STATUS current.
- Compile the verification-first evidence brief from
  `phase4/trust_consensus.json` + `synthesis/consensus.json`.
- Gate: online retraction requires `OPENALEX_API_KEY`; otherwise run offline
  and say so ("SKIPPED_ONLINE").

## Never allowed
- Modify `literature/included.json` or the protocol.
- Suppress or reword a retraction/COI/RoB flag.
- Publish a final brief while any study carries an unresolved flag.
```

### Agent 3 — `console-operator` *(with Phase-5)*

- **Mandate:** Run and supervise the Harness Console end-to-end — start/cancel jobs, monitor streams, dry-run pipelines — and keep the action↔command↔MCP table true.
- **Scope & responsibilities:** starts actions through the JobRunner API/`/api/v1/jobs` (`console/api/jobs.py:65`); watches SSE job/log streams; cancels hung jobs cooperatively (`job_runner.py:358-393`); dry-runs `PipelineSpec` templates via the `/pipelines` API; verifies each job's terminal journal event (`job_runner.py:197-208`); audits the actions table against kit CLIs and logs drift needs for `conformance-qa`.
- **Tools & permissions:** console HTTP (FastAPI `serve.py`), `JobRunner`; read `actions.py`. **NEVER:** execute an arbitrary shell command; bypass the actions table; start a second run of a single-flight action; auto-re-run a mutating action without human ack.
- **Skills:** `workspace-manager` (journal contract).
- **Human/agent handoffs:** waits on: an approved `PipelineSpec` for mutating runs, human ack before re-running failed mutating actions. Initiates: job lifecycle, patient retry of idempotent jobs (status/sync/discovery). Failure recovery: posts job log path + exit code; leaves workspace untouched.
- **DoD / test:** `test_console_serve.py`-style lifecycle over a built-in template (`BUILTIN_TEMPLATES`, `console/api/pipelines.py:97…`), asserting queued→running→success + the `SUCCESS|FAILED` journal event; a dedicated drift test asserts every `Action` parses under its kit CLI `--help`.
- **Effort:** S–M.

```markdown
---
description: Harness Console operator. Drives the local Harness Console (serve), runs and supervises job/pipeline lifecycle through the JobRunner API, and enforces the actions-table contract. Use when a workspace is served via scholar-harness serve and actions or pipelines need execution/supervision.
mode: subagent
permission: allow
---

You are **console-operator**. You operate the console; you never improvise commands.

## Contract
- Start/cancel/monitor jobs via `/api/v1/jobs` and the SSE stream.
- Render every action from the actions table (`console/runtimes/actions.py`);
  never hand-write a command.
- Confirm each job lands its terminal journal event
  (`audit/journal.jsonl`, action, status SUCCESS/PARTIAL/FAILED).
- Dry-run PipelineSpec DAGs before mutating runs.

## Never allowed
- Execute raw shell or bypass an action's command template.
- Start a second job for an already-running action (single-flight).
- Re-run a mutating action without explicit human confirmation.
```

### Agent 4 — `conformance-qa` *(now, standing)*

- **Mandate:** Keep the documented surface honest — the verified API↔CLI↔MCP map, the skill tree, and the actions table must never silently drift from code again.
- **Scope & responsibilities:** maintains and runs `tests/conformance/` (action→CLI `--help` parity, MCP registered-vs-listed parity, skill-flag parity, count freshness); checks `tester.md:11`-style stale claims; verifies `sync --check 11/11`; produces a drift ledger for `coder` (never fixes itself).
- **Tools & permissions:** read-only: MCP tool introspection, `grep`/`diff`, `uv run pytest tests/conformance`, `uv run ruff check scripts/`, `uv run scholar-* --help` (all subcommands, no network). **NEVER:** edit kit or harness source; push; approve a PR (that is `reviewer`'s job).
- **Skills:** `scholar-agent-kit` (surface knowledge), `workspace-manager` (bundle sync semantics).
- **Human/agent handoffs:** hands drift findings as tasks to `coder` (through the fork+PR gate); loops back to re-run the suite after each fix.
- **DoD / test:** `tests/conformance/` is a mandatory CI job; the suite catches at least the five known drift classes (hidden tools, count staleness, protocol flags, `actions.py` extract, MCP-vs-CLI engine vocabulary). Smoke: `uv run pytest tests/conformance`.
- **Effort:** M.

```markdown
---
description: Surface conformance QA. Owns the standing parity checks between docs/kits_surface_matrix.md, .agents/skills/**/SKILL.md, console/runtimes/actions.py, and the real kit/MCP surfaces. Read-only: it finds and reports drift, never edits. Use as a standing gate during and after the fix-the-tooling wave.
mode: subagent
permission: allow
---

You are **conformance-qa**. The contract of record is the verified surface map.

## Contract
- Run `tests/conformance/` after every signing wave: action command templates
  must parse under each kit CLI's real flags; `scholar-agent --help` must list
  all registered MCP tools; skill documents must reference existing flags;
  repo-documented counts (tests, tools, skills) must match reality.
- Report drift as a task list for `coder`, each item naming the file:line that
  drifted and the assertion that will catch it.

## Never allowed
- Edit source or tests directly.
- Push or open PRs (fork+PR gate is `coder`'s, after you file findings).
- Add any assertion that requires network access.
```

### Agent 5 — `recon-curator` *(after fix-the-tooling wave; closes GAP A/B)*

- **Mandate:** Custodian of grounded-recon state — sessions, lexicons, saturation — converting M0.7 gap signal into screening input without ever fabricating anchors.
- **Scope & responsibilities:** runs `recon_probe`/`recon_distill`/`recon_delta` sessions (`recon/engine.py:259`, `recon/adaptive.py:267`); proposes `lexicon_json` merges through the `recon_distill` seam (GAP A); computes agent-side Pareto scoring helper (GAP B); emits `literature/pool_saturation.json` hints for `prisma-steward`; owns nothing in `workspaces/` except the hint file.
- **Tools & permissions:** MCP `recon_probe|recon_distill (lexicon_json)|recon_delta`; parity helper `.agents/skills/inception-agent/scripts/grounded_directions.py`; `workspace-manager` read/log. **NEVER:** write to `workspaces/` (scratch lives under `.cache/inception_recon/`); propose a concept without ≥1 anchor DOI (APR, `inception-agent.md` contract); touch `protocol.json`.
- **Skills:** `scholar-agent-kit` (recon MCP), `inception-agent` (lifecycle + APR), `workspace-manager`.
- **Human/agent handoffs:** hands anchored directions to `inception-agent` for the interview; hands saturation hints to `prisma-steward`; if the pool is below `POOL_THIN_FLOOR=12` (`recon/gates.py:23`) it reports real scarcity, never a fabricated direction.
- **DoD / test:** hermetic session fixture + lexicon-merge test (byte-identical output without lexicon override; annotated artifact name with `lexicon_sha`); saturation-hint file test reading a fixture gap session.
- **Effort:** S–M.

```markdown
---
description: Grounded-recon curator. Owns recon session state, lexicon curation, and saturation surfacing across the exploratory-grounding subsystem. Probes, distills (lexicon merges via lexicon_json), runs adaptive gap follow-ups, and hands anchored directions downstream. Use during grounded inception or when a thin sub-school needs pre-screening priority.
mode: subagent
permission: allow
---

You are **recon-curator**. You curate maps, not conclusions.

## Contract
- Run and extend FAIR recon sessions under `.cache/inception_recon/`.
- Propose lexicon merges via `recon_distill(lexicon_json=...)`; keep
  provenance (`lexicon_sha` in artifact names).
- Surface pool saturation (GAP B) as `literature/pool_saturation.json` hints.
- An APR: no concept/synonym/direction without an anchor DOI.

## Never allowed
- Write into `workspaces/` except issued hint files.
- Propose or emit unanchored vocabulary (APR is a hard invariant).
- Touch `protocol.json` — directions go through `inception-agent` for the human
  interview and emission.
```

### Agent 6 — `release-packager` *(with Phase-7)*

- **Mandate:** Own the distribution surface — uvx metapackage, hash-pinned manifest, `doctor` matrix, and the P7.8 fresh-folder GA gate — with full provenance.
- **Scope & responsibilities:** builds/verifies the `nexus-scholar` metapackage from `plugins.json` pins; generates dependency pins in CI (`docs/UPCOMING_WORK.md:53`); runs `doctor` (kit versions vs manifest, API keys, skill resolvability, workspace layout, P7.5); validates `init`/`setup-mcp` output shapes; triggers `tester`'s P7.8 GA gate in a temp dir.
- **Tools & permissions:** `uv`, `scripts/install_plugins.py`, `scholar-harness` CLI, CI (`gh`; fork+PR gate only). **NEVER:** push to `origin` (fetch the `pull-request-gate` skill and follow it); ship an unsigned/untested wheel; ship over lazy-import warnings (P7.7).
- **Skills:** `pull-request-gate` (mandatory), `workspace-manager`.
- **Human/agent handoffs:** waits for hash-pinned manifest approval + GA gate sign-off; initiates PRs through the gate; failure recovery: stops at the first failing P7 step and reports the exact environment line.
- **DoD / test:** P7.8 — the blueprinted `uvx` commands run end-to-end in a fresh temp folder on CI (this *is* the DoD, per `docs/UPCOMING_WORK.md:59`); `doctor` returns clean on a canonical workspace.
- **Effort:** M.

```markdown
---
description: Distribution packager for Phase 7. Builds and verifies the uvx-installable nexus-scholar metapackage and supporting tools (init/setup-mcp/doctor/log), enforces hash-pinned plugin inventory, and runs the fresh-folder GA gate. Use when Phase-7 distribution work begins.
mode: subagent
permission: allow
---

You are **release-packager**. You ship only what is verifiable.

## Contract
- Load `pull-request-gate` before any git action; all shipping goes fork → PR.
- Resolve `plugins.json` pins to commit SHAs; generate dependency pins in CI.
- Keep startup honest: no torch/chromadb imports in init/search/doctor paths
  (P7.7 lazy imports).
- Run the P7.8 fresh-folder e2e as the release gate; stop on first failure.

## Never allowed
- Push to `origin` or bypass the pre-push hook.
- Ship a wheel without the P7.8 gate green.
- Resolve imports that violate the metapackage's declared CLI set.
```

## 5. Prioritized rollout

| Phase | Ship | Concrete first action |
| :-- | :-- | :-- |
| **Now** | `conformance-qa` agent + `tests/conformance/` scaffold; `prisma-steward` agent + calibration gate; manifest hash pins (D8); `ingress` NIT; provider fix in Stage 1 (D1) | Create `tests/conformance/test_actions_cli_parity.py`; resolve `plugins.json` `main`→SHA; fix `orchestrator.py:395`. |
| **After fix-the-tooling wave** | `verify-steward` agent (Phase-4 streams + evidence-brief start, D4); `recon-curator` agent (GAP A/B closes, D6); Stage-5/7/8/9 corrections verified by the new e2e assertions (D1) | Add `verify_*` MCP tools or console actions; wire `pool_saturation.json`. |
| **Inside Phase-5** | Ship the console (D3): fix `actions.py:78`, enable `extract` in `RUNNER_TRIGGERS`, run M5.3 byte-identity; ship `console-operator` agent; bring Phase-4 actions into the dashboard (D4) | Fix the `extract` action row; add the 4 verify actions. |
| **Inside Phase-6** | Verification-first **evidence brief** (D7) as a first-class artifact surfaced by `verify-steward`; trust-consensus report attached to synthesis | Add `src/scholar_harness/integrations/evidence_brief.py`. |
| **Inside Phase-7** | Distribution metapackage (D9) with `release-packager` agent owning P7.1→P7.8 | Land P7.1 `--workspace` on `server.main()`. |
| **Later** | Jupyter suite + Zotero/Typst bridges (D10); fold kits into the conformance wave's final contract | Commit `00_research_inception.ipynb`. |