# Harness Full-Picture Rating, Vision & Agent Blueprint

## 1. Rating

### 1.1 Holistic Scorecard

| Dimension | Score (0–10) | Weight | Weighted | Primary Rationale Summary |
| :--- | :---: | :---: | :---: | :--- |
| **1. Architecture** | **7.5** | 20% | 1.50 | Clean thin-orchestrator separation and immutable file-contracts; undermined by undeclared cross-kit dependencies and orchestrator pipeline mock-leakage. |
| **2. Reliability** | **5.5** | 25% | 1.375 | Rigorous mathematical grounding in recon and verbatim verification; severely degraded by 6 known-broken MCP tools, CWD-relative path traps, and silent error swallowing. |
| **3. Automation Depth** | **6.5** | 20% | 1.30 | Autonomous Socratic recon and agent batch-screening handoffs; deadlocked on manual multi-screener ties and Phase-4 trust streams being CLI-only. |
| **4. Operability & DX** | **7.0** | 15% | 1.05 | Exemplary factual documentation (`kits_surface_matrix.md`) and 11/11 skill mirror hygiene; penalized by cold-onboarding friction and kit CLI test opacity. |
| **5. Distribution Readiness** | **3.5** | 10% | 0.35 | Sophisticated Phase-7 blueprint; entirely non-functional zero-install flow today with no root metapackage and missing MCP `--workspace` root resolution. |
| **6. Test & Contract Confidence** | **6.0** | 10% | 0.60 | 248 green hermetic unit/property tests; zero automated conformance tests against MCP/CLI surfaces and a CI workflow that completely skips `pytest`. |
| **Overall Score** | **6.2 / 10** | 100% | **6.18** | **Solid scientific and mathematical core wrapped in an unhardened, partially disconnected agent interface.** |

---

### 1.2 Evidence-Cited Dimension Evaluation

#### Dimension 1: Architecture (Score: 7.5 / 10)
- **Strengths:**
  1. *Thin Orchestrator Discipline*: The harness (`src/scholar_harness/orchestrator.py:369-588`) acts as an orchestrator rather than a monolithic framework, consuming the 8 kit packages (`tools/scholar-*-kit/`) as independent library leaves (`SearchEngine`, `Deduplicator`, `ScholarIndexer`, `ResearchProtocol`) without duplicating core algorithms (`AGENTS.md:1-12`).
  2. *Immutable File-First Contract*: All project state is anchored in canonical directories (`workspaces/<slug>/`) via standard files (`protocol.json`, `intent.json`, `audit/journal.jsonl`, `INDEX.md`, `project.json`), enforcing zero-sync-engine collaboration across heterogeneous agents and processes (`specs/inception-ecosystem/01_skill_boundaries.md:3-37`, `AGENTS.md:37-45`).
  3. *Clean Subsystem Decomposition*: The 8 specialized kits have mathematically distinct, orthogonal concerns (`docs/kits_surface_matrix.md:21-31`): discovery (`scholar-search`), extraction (`scholar-pdf`), bibliography (`scholar-bib`), semantic retrieval (`scholar-rag`), knowledge graphs (`scholar-graph`), protocol compilation (`scholar-protocol`), agent interface (`scholar-agent`), and scientific integrity (`scholar-verify`).
- **Weaknesses:**
  1. *Undeclared Cross-Kit Dependencies*: `scholar-rag-kit` imports `scholar_protocol.compiler.build_extraction_model` in `scholar_rag/matrix.py:27` but does not declare `scholar-protocol-kit` in `pyproject.toml` (`docs/kits_surface_matrix.md:290`). Similarly, `scholar-agent-kit` imports `scholar_verify.verbatim` (`tools/scholar-agent-kit/src/scholar_agent/server.py:38`) without declaring `scholar-verify-kit` (`docs/kits_surface_matrix.md:250-252, 294`). Only the monorepo shared `.venv` masks these missing declarations; a standalone `uv sync` breaks.
  2. *Orchestrator Pipeline Divergence & Mock Leakage*: In `src/scholar_harness/orchestrator.py:537, 557`, Stages 7 and 9 call `indexer.retriever`, which does not exist on `ScholarIndexer` (AttributeError); `orchestrator.py:501-507` fabricates synthetic placeholder text in Stage 5; `orchestrator.py:544` instantiates `CitationGraphBuilder(http_client=None)`, mirroring the 0-edge graph bug (`docs/kits_surface_matrix.md:80-86`).
  3. *Schema Impedance Mismatch*: `scholar-rag-kit` emits `SynthesisClaim` with `claim_text` and `citation_tokens` (`tools/scholar-rag-kit/src/scholar_rag/models.py:193-203`), but `scholar-verify-kit` `VerbatimClaimVerifier` requires `evidence_quote` (`tools/scholar-verify-kit/src/scholar_verify/verbatim.py:121-135`). Downstream synthesis ledgers fail verbatim verification with `MISSING_QUOTE` unless manually transformed (`docs/kits_surface_matrix.md:65-70`).

#### Dimension 2: Reliability (Score: 5.5 / 10)
- **Strengths:**
  1. *FAIR Memory & Deterministic Recon*: Grounded Inception and Recon (`src/scholar_harness/recon/`) guarantees CWD-independent cache resolution via `canonical_recon_root()` (`tools/scholar-agent-kit/src/scholar_agent/server.py:112`, `src/scholar_harness/recon/cache_key.py`), respecting `NEXUS_RECON_ROOT` or defaulting to `<repo>/.cache/inception_recon`, preventing scratch pollution (`specs/exploratory-grounding-agent/10_task_list.md:129`).
  2. *Strict Algorithmic Verification*: `VerbatimClaimVerifier` (`tools/scholar-verify-kit/src/scholar_verify/verbatim.py:36-79`) and `RetractionChecker` (`retraction.py:117-210`) use Unicode NFKC normalization, sliding character/token windows, and explicit Crossref/OpenAlex status evaluations without relying on stochastic LLM-as-a-judge heuristics (`docs/phase_6/README.md:10-14, 53-59`).
  3. *Fault-Tolerant Screening Protocol*: The batch screening handoff (`src/scholar_harness/agent_screen.py:9-31`) persists isolated JSON batches (`batch_NNN.json` -> `batch_NNN_decisions.json`), ensuring partial failures or process crashes never corrupt previously scored papers.
- **Weaknesses:**
  1. *Known-Broken MCP Tooling in Production*: Multiple tools on `scholar-agent` silently fail or drop data (`docs/kits_surface_matrix.md:36-79`): `nexus_graph_build` (`server.py:436`) constructs `CitationGraphBuilder(http_client=None)`, causing all OpenAlex requests to fail and returning 0 edges while reporting success; `nexus_extract_pdf` (`server.py:302`) drops all metadata keywords (`workspace_id`, `doi`, `year`, `authors`); `nexus_bib_clean` (`server.py:469`) calls `lint(generate_keys=False)` with zero cleaning or deduplication; `nexus_screen` (`server.py:278-284`) computes `conflicts.json` and `prisma_report.json` but never writes them to disk.
  2. *CWD-Relative Resolution Trap*: The MCP server starts with CWD inside `tools/scholar-agent-kit/` (`server.py`), causing default paths like `./chroma_db`, `./literature`, `./deduped.json` to write directly into the tool's git checkout rather than the researcher's workspace (`docs/kits_surface_matrix.md:39-44`).
  3. *Silent Error Swallowing & Phase-4 MCP Void*: In `scholar-search-kit`, per-provider exceptions are caught and swallowed in `search_all`, meaning network timeouts or rate limits return empty lists indistinguishable from zero candidate hits (`docs/kits_surface_matrix.md:126-127`). In `scholar-agent-kit`, all Phase-4 verification streams (retraction, open science, COI, risk-of-bias) have zero MCP wrappers (`docs/kits_surface_matrix.md:87-90`), leaving agents blind to trustworthiness checks without direct shell execution.

#### Dimension 3: Automation Depth (Score: 6.5 / 10)
- **Strengths:**
  1. *Autonomous Literature Reconnaissance*: Inception recon executes multi-round dual-mode queries (keyword and semantic), calculates Question Echo Index (QEI), triggers adaptive delta probes for thin frontiers (`n <= 2`), and computes anchor-provenance ratios without human intervention (`src/scholar_harness/recon/engine.py:30-150`, `distiller.py:40-120`, `specs/exploratory-grounding-agent/14_agent_loops.md:18-23`).
  2. *Asynchronous PRISMA Batch Screening*: `agent_screen.py` (`src/scholar_harness/agent_screen.py:60-75`) standardizes batch partitioning, prompt generation, decision parsing, and automated PRISMA 2020 report assembly.
  3. *Atomic State Synchronization*: `scholar-harness sync` (`src/scholar_harness/cli.py:118-155`, `orchestrator.py:270-325`) atomically re-computes discovery, deduplication, verification, inclusion, and extraction metrics, rebuilding `project.json` and `INDEX.md` directly from filesystem truth.
- **Weaknesses:**
  1. *Manual Deadlock Adjudication*: While `reconcile_multi_screener_decisions` in `scholar_search/screening.py` computes Fleiss' $\kappa$ and isolates 2-vs-2 tie deadlocks, resolution requires a human "Senior Adjudicator" to manually prepare an `adjudication_json` file (`docs/phase_6/README.md:49-52`, `tools/scholar-agent-kit/src/scholar_agent/server.py:510-521`); no agent loop exists to resolve screening deadlocks.
  2. *Phase-4 Trust Verification is Entirely CLI-Only*: An autonomous agent operating through MCP has no way to run retraction checks, scan DAS/CAS statements, audit COI chunks, or compute QUADAS-2/PROBAST risk of bias (`docs/kits_surface_matrix.md:87-90`); it requires human shell intervention (`uv run scholar-verify ...`).
  3. *Disconnected Synthesis and Trust Context*: The trust-context annotator (`scholar-verify trust-context`, `docs/UPCOMING_WORK.md:35`) joins Consensus Cartographer clusters with Phase-4 metrics, but cannot be called via MCP and has no autonomous pipeline trigger in `orchestrator.py`.

#### Dimension 4: Operability & DX (Score: 7.0 / 10)
- **Strengths:**
  1. *Factual Knowledge Base*: `docs/kits_surface_matrix.md:1-320` provides an exhaustive, verified technical reference documenting public APIs, CLI subcommands, MCP wrappers, and 11 critical cross-cutting failure modes across all 8 kits.
  2. *Skill Bundle Synchronization*: `scripts/sync_skills_bundle.py` maintains byte-identical mirroring between canonical `.agents/skills/` and `.agents/plugins/nexus-scholar/skills/` (verified 11/11 OK), preventing documentation drift across environments (`specs/inception-ecosystem/03_skill_tree_and_plugin_distribution.md:4-15`).
  3. *Predictable Layout & Audit Conventions*: `AGENTS.md:37-45` enforces canonical directory structure (`workspaces/<slug>/`) and append-only event logging (`audit/journal.jsonl`).
- **Weaknesses:**
  1. *Cold Onboarding Friction & Empty Workspaces*: All workspaces were purged on 2026-09-11 (`AGENTS.md:43-45`), requiring developers to check out git snapshot `72090e5` (`docs/COMMIT_SNAPSHOTS.md`) to see realistic research artifacts; running CLI commands on an empty workspace without running inception yields unhelpful errors.
  2. *Kit CLI Test Opacity*: The harness test suite in `tests/` focuses on harness internals (`recon/`, `test_console_*.py`, `test_inception*.py`); it does not smoke-test the kit CLI executables end-to-end, allowing CLI syntax mismatches (e.g. `scholar-pdf extract` requiring positional `pdf_path` instead of `--input`, or `scholar-verify` docstring referencing missing `ingress`) to remain hidden (`docs/kits_surface_matrix.md:84-86, 91-97`).
  3. *Setup "Gotcha" and Windows Process Locking*: `uv sync` alone fails to install the kit CLIs (`AGENTS.md:14-18`), requiring `python scripts/install_plugins.py`. On Windows, `install_plugins.py` crashes if the MCP server executable (`scholar-agent.exe`) is active in background processes, locking the binary file (`specs/exploratory-grounding-agent/10_task_list.md:142`).

#### Dimension 5: Distribution Readiness (Score: 3.5 / 10)
- **Strengths:**
  1. *Comprehensive Phase-7 Architectural Blueprint*: `docs/phase_7_distribution/README.md:1-170` details the 3-tier distribution strategy (`nexus-scholar` metapackage, portable CLI, universal MCP server) and an honest 9-point gap checklist (P7.1–P7.9).
  2. *Local Workspace Autonomy*: Workspaces require no external database, authentication service, or cloud backend; the directory with `protocol.json`, `audit/journal.jsonl`, and `INDEX.md` is fully portable and Git-collaborative (`docs/phase_5/README.md:35-41`).
- **Weaknesses:**
  1. *Zero-Friction Distribution is Completely Deferred*: The vision of `uvx nexus-scholar init` is non-functional today; there is no root metapackage `pyproject.toml` exposing `nexus-scholar` or `scholar-agent` scripts (`docs/UPCOMING_WORK.md:51-60`, `docs/phase_7_distribution/README.md:138-140`).
  2. *MCP Server Lacks `--workspace` Root Resolution*: `scholar_agent.server.main()` takes no CLI arguments (`tools/scholar-agent-kit/src/scholar_agent/server.py:960-965`, `docs/phase_7_distribution/README.md:137-139`), forcing tools to resolve relative to process CWD, which breaks in Claude Desktop, Cursor, or external harnesses.
  3. *Supply-Chain and Environment Unpinned*: `.agents/plugins/nexus-scholar/plugins.json:1-40` pins all kits to `default_rev: main` without commit hashes or wheel digests (`docs/kits_surface_matrix.md:313`). `.agents/plugins/nexus-scholar/mcp_config.json` defines no environment variable passthrough (`env: {}`) for required keys like `SCHOLAR_MAILTO`, `SCHOLAR_OPENALEX_KEY`, or `OPENAI_API_KEY`.

#### Dimension 6: Test & Contract Confidence (Score: 6.0 / 10)
- **Strengths:**
  1. *Hermetic Unit & Property Tests*: 248 passing tests in `uv run pytest` (0 failures, 3 skipped) covering canonical JSON serialization, APR anchor verification, QEI echo index math, hierarchical cache keys, and responder-driven Socratic inception wizards (`tests/recon/`, `tests/test_inception*.py`, `tests/test_rigor_upgrades.py`).
  2. *Deterministic Wizard Verification*: Socratic interview tests use deterministic responder sequences rather than live network calls or stochastic models.
- **Weaknesses:**
  1. *Surface Matrix is Assertion-Free Markdown*: `docs/kits_surface_matrix.md` contains 11 critical failure modes, but none of them are checked by an automated conformance suite; there is no test verifying that MCP tools actually conform to their documented contracts (e.g., verifying `nexus_graph_build` returns edges > 0 or that `nexus_extract_pdf` retains metadata).
  2. *CI Workflow Completely Skips Pytest*: `.github/workflows/ci.yml:33-52` runs ruff and manifest syntax checks, but skips `pytest` entirely because kit dependencies are external and plugin installation uses `continue-on-error: true` (`specs/exploratory-grounding-agent/10_task_list.md:123`). Breaking changes can be pushed to remote branches without triggering CI failure.
  3. *Untested API-to-Skill Contract Drift*: Skills document how agents should call tools, but no automated test checks that code examples in `SKILL.md` match real kit signatures (e.g. importing models from root instead of `scholar_search.models`, `docs/kits_surface_matrix.md:109-110`).

---

### 1.3 Overall Verdict

> **Verdict:** The Nexus Scholar Harness is an exceptionally rigorous, mathematically grounded research engine whose brilliant architectural foundations (deterministic protocols, byte-level verbatim claim verification, and append-only audit ledgers) are currently bottlenecked by an unhardened MCP front-door, manual screening/trust loops, and an entirely deferred distribution layer.

---

## 2. Vision

### Forward Vision (12–24 Months)

In 12 to 24 months, the Nexus Scholar Harness transitions from an internal developer monorepo into the **definitive, bench-portable operating system for verifiable academic research**. It establishes the computational gold standard for systematic literature reviews (SLRs), meta-analyses, and rapid evidence assessments (REAs). Rather than attempting to replace human intellectual judgment with black-box LLM hallucinations, the harness provides a mathematically audited substrate where autonomous AI agents and human principal investigators collaborate with cryptographic transparency.

Researchers interact with the system through a unified, agent-agnostic interface: a conversational Socratic interview conducts literature-grounded inception to probe live citation spaces, discover natural sub-schools of thought, and compile a fingerprinted `protocol.json`. Autonomous agents take over the mechanical heavy lifting—parallel discovery across six academic indices, deduplication, heuristic pre-screening, structural AST extraction, and consensus cartography. When ambiguity or conflicting evidence arises, the system pauses execution at strict human-judgment checkpoints, rendering intuitive side-by-side adjudication matrices in a lightweight, local-first console.

Every assertion synthesized by the harness is bound by immutable epistemic invariants: claims are certified through byte-level verbatim quote verification ($\ge 90\%$ coverage against source full-texts), screening decisions are audited via Fleiss' $\kappa$ inter-rater reliability, and every study undergoes four-stream risk-of-bias and retraction verification. All actions, metrics, and state mutations append to an immutable cryptographic ledger (`audit/journal.jsonl`).

Crucially, the harness achieves zero-friction distribution (`uvx nexus-scholar init`): any researcher, on any operating system, using any modern agent interface (DeepSeek Harness, Claude Desktop, Cursor, OpenCode, or terminal CLI), can instantiate a self-contained, Git-tracked research cell in seconds. The harness never absorbs kit internals, never demands a centralized database, and enforces academic integrity as an immutable computational law.

---

## 3. Directions

### 3.1 Ranked Strategic Directions

| Rank | Direction | Outcome | Why Now | Effort | Risk | First Concrete Step | Timing |
| :---: | :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **1** | **MCP Front-Door Hardening & Workspace Root Binding** | Fixes 6 broken MCP tools (graph, PDF metadata, bib clean, screen outputs, verbatim schema mismatch, rag boost) and adds `--workspace` argument. | Scorecard Reliability is 5.5. MCP is the primary agent surface; broken tools corrupt downstream agent trust. | **M** | Low | Add `--workspace` arg to `scholar_agent.server.main()` in `tools/scholar-agent-kit/src/scholar_agent/server.py:960` and resolve all defaults against it. | **Before** Phase 5 / 7 |
| **2** | **Surface Matrix Conformance Test Suite & CI Pytest Gate** | Automated test suite that executes all 18 MCP tools and kit CLIs against golden fixtures; activates `pytest` in GitHub Actions CI. | Test confidence is 6.0. The surface matrix is assertion-free markdown; CI currently skips pytest completely. | **M** | Low | Create `tests/test_surface_matrix_conformance.py` asserting non-zero edges on graph and frontmatter metadata on PDF extracts. | **Before** Phase 5 / 7 |
| **3** | **Phase-4 Trust Verification MCP Exposure & Ingress Fix** | Expose retraction, open-science, COI, risk-of-bias, and trust-context as MCP tools; clean up unregistered `ingress` docstring NIT. | Automation depth is stalled at Phase 3; Phase-4 trust verification is currently CLI-only. | **S** | Low | Register `@mcp.tool() def nexus_verify_stream(...)` and `nexus_verify_trust_context(...)` in `server.py:475`. | **Before** Phase 5 |
| **4** | **Autonomous Multi-Screener PRISMA Steward Agent** | Autonomous multi-agent screening loop with Fleiss' $\kappa$ computation, majority voting, deadlock isolation, and Socratic tie-breaking. | Screening is currently an awkward manual handoff (`agent_screen.py prepare` -> wait for agent -> `collect`). | **M** | Med | Draft `.opencode/agent/prisma-steward.md` orchestrating `agent_screen.py` and `nexus_screen_reconcile`. | **Now** |
| **5** | **Continuous Living Review & Retraction Sentinel (Unique Edge)** | Autonomous periodic surveillance: monitors for newly published papers, checks retractions of included studies, detects tainted synthesis clusters. | **Unique positioning**: Harness is the only platform with deterministic verbatim claims + trust-context + append-only audit. | **M** | Low | Create `src/scholar_harness/sentinel.py` to audit existing workspaces against fresh OpenAlex/Crossref queries. | **Before** Phase 5 |
| **6** | **Bench-Portable Distribution & Metapackage (Phase 7)** | `uvx nexus-scholar init` functional in any directory; universal MCP configs for Claude/Cursor/DSH; CI release wheels. | Distribution readiness is 3.5. Monorepo-relative paths prevent external adoption. | **L** | Med | Create repo-root `pyproject.toml` tool metapackage generated from `plugins.json` (P7.2). | **Inside** Phase 7 |
| **7** | **Thin Local-First Harness Console (Phase 5)** | Zero-DB, local-first FastAPI/HTML dashboard for human binding judgment (screening sign-off, consensus inspection, PipelineSpec DAGs). | Reviewers/PIs need visual inspection of PRISMA flow and consensus clusters without reading raw JSON files. | **L** | Low | Stand up minimal FastAPI server under `src/scholar_harness/console/` serving `status.html` (M5.1). | **Inside** Phase 5 |
| **8** | **Recon Saturation & QEI Ingestion into Search/Screening** | Feeds Inception recon signals (`topics`, `QEI`, `corpus_total`/`saturation_label`) into Phase-1 search expansion and screening thresholds. | Rich semantic topic bounds and saturation signals distilled during Phase 0 are currently discarded after protocol compile. | **M** | Low | Update `src/scholar_harness/orchestrator.py:391` (`compile_protocol_search`) to ingest `audit/recon_context.json`. | **Inside** Phase 5 |

---

### 3.2 Expanded Direction Details

#### Direction 1: MCP Front-Door Hardening & Workspace Root Binding
- **Outcome:** Resolves the 6 verified failure modes in `tools/scholar-agent-kit/src/scholar_agent/server.py`:
  1. `nexus_graph_build` (`server.py:436`): Passes a live `AcademicHttpClient` to `CitationGraphBuilder` instead of `None`, restoring citation edge discovery.
  2. `nexus_extract_pdf` (`server.py:302`): Passes `metadata` kwargs (`doi`, `workspace_id`, `authors`, `year`) to `PyMuPDFEngine.extract_markdown`.
  3. `nexus_bib_clean` (`server.py:469`): Calls `BibLinter.lint(generate_keys=True)` and `BibDeduplicator.dedup()` instead of lint-only in-place overwrite.
  4. `nexus_screen` (`server.py:278-284`): Writes `conflicts.json` and `prisma_report.json` to disk alongside `included.json` and `excluded.json`.
  5. `nexus_verify_claims` (`server.py:529-565`): Accepts `claims.json` with fallback mappings for `claim_text` -> `evidence_quote` and returns per-claim verdict lists in addition to aggregate metrics.
  6. Workspace root binding: `scholar_agent.server.main()` accepts `--workspace <path>`, eliminating process-CWD pollution (`docs/kits_surface_matrix.md:39-44`).
- **Why Now:** Reliability scorecard is 5.5. AI agents interacting via MCP cannot trust the tools today.
- **Effort:** M | **Risk:** Low | **Timing:** Before Phase 5 / Phase 7.
- **First Concrete Step:** Add `--workspace` CLI option to `scholar_agent.server.main()` and refactor default path arguments to resolve against it.

#### Direction 2: Surface Matrix Conformance Test Suite & CI Pytest Gate
- **Outcome:** Converts `docs/kits_surface_matrix.md` from static documentation into executable Python tests (`tests/test_surface_matrix_conformance.py`). Connects `uv run pytest` into `.github/workflows/ci.yml:33-52` so that PRs cannot merge if tool contracts regress.
- **Why Now:** Test confidence is 6.0. Pre-existing errors and tool regressions slip through because CI only checks `ruff check scripts/`.
- **Effort:** M | **Risk:** Low | **Timing:** Before Phase 5 / Phase 7.
- **First Concrete Step:** Create `tests/test_surface_matrix_conformance.py` asserting non-empty edge sets on graph building and metadata presence in markdown extraction.

#### Direction 3: Phase-4 Trust Verification MCP Exposure & Ingress Fix
- **Outcome:** Exposes `retraction`, `open-science`, `coi`, `risk-of-bias`, and `trust-context` on `scholar-agent` FastMCP server. Cleans up the unregistered `ingress` subcommand mentioned in `tools/scholar-verify-kit/src/scholar_verify/cli.py:4` by implementing `scholar-verify ingress` to cleanly merge and validate `included.json` before Phase 4 runs.
- **Why Now:** Automation depth is blocked because Phase-4 trust verification requires human shell access.
- **Effort:** S | **Risk:** Low | **Timing:** Before Phase 5.
- **First Concrete Step:** Add `@mcp.tool()` wrappers in `tools/scholar-agent-kit/src/scholar_agent/server.py` for each of the 4 Phase-4 verification streams.

#### Direction 4: Autonomous Multi-Screener PRISMA Steward Agent
- **Outcome:** Operationalizes multi-screener PRISMA 2020 workflows. An autonomous agent partitions batches, invokes dual screeners, computes Fleiss' $\kappa$ agreement via `scholar_search.screening.calculate_fleiss_kappa`, isolates deadlocks, and triggers a Socratic tie-breaker interview with the human PI.
- **Why Now:** Eliminates the awkward manual file handoff of `agent_screen.py`.
- **Effort:** M | **Risk:** Medium | **Timing:** Now.
- **First Concrete Step:** Create `.opencode/agent/prisma-steward.md` definition.

#### Direction 5: Continuous Living Review & Retraction Sentinel (Unique Positioning)
- **Outcome:** Transforms the harness from a one-shot review generator into an ongoing **Living Systematic Review Sentinel**. An autonomous loop wakes up periodically (or on demand), checks the corpus against fresh OpenAlex/Crossref publications, scans included DOIs for retractions or expressions of concern via `RetractionChecker`, evaluates affected consensus clusters via `trust_context.annotate`, downgrades tainted claims (`STRONG` -> `BLOCKED`), and logs signed alerts to `audit/journal.jsonl`.
- **Why Now:** **This is the repo's killer differentiator.** No other AI literature tool combines deterministic verbatim extraction, four-stream trust audits, consensus cartography, and append-only audit ledgers.
- **Effort:** M | **Risk:** Low | **Timing:** Before Phase 5.
- **First Concrete Step:** Implement `src/scholar_harness/sentinel.py` with `audit_workspace_drift(workspace_dir)`.

#### Direction 6: Bench-Portable Distribution & Metapackage (Phase 7)
- **Outcome:** Delivers `docs/phase_7_distribution/README.md`. Researchers install the entire suite via `uvx nexus-scholar init "Topic"`, which creates a self-contained research cell with symlinked skills, `.mcp.json`, and `.env.example`.
- **Why Now:** Overcomes the "monorepo-tied" barrier and makes Nexus Scholar usable across DeepSeek Harness, Claude Desktop, Cursor, and VS Code.
- **Effort:** L | **Risk:** Medium | **Timing:** Inside Phase 7 block.
- **First Concrete Step:** Create repo-root `pyproject.toml` tool metapackage declaring dependencies synchronized from `plugins.json` (P7.2).

#### Direction 7: Thin Local-First Harness Console (Phase 5)
- **Outcome:** Implements the local-first FastAPI console defined in `docs/phase_5/README.md`. Renders `status` in HTML, provides interactive screening and conflict adjudication screens for human PIs, and allows visual DAG editing of `PipelineSpec` JSON files.
- **Why Now:** Fulfills the Phase-5 promise of human empowerment without adding thick-database or auth complexity.
- **Effort:** L | **Risk:** Low | **Timing:** Inside Phase 5 block.
- **First Concrete Step:** Stand up `src/scholar_harness/console/` with `status.html` rendering `ResearchOrchestrator.get_status()`.

#### Direction 8: Recon Saturation & QEI Ingestion into Search/Screening
- **Outcome:** Connects the Grounded Inception outputs (`topics` taxonomy, `QEI` score, and `corpus_total`/`saturation_label`) directly into Phase-1 search queries and screening calibration, preventing PubMed/Crossref contamination.
- **Why Now:** Maximizes the return on investment of the recently completed M0.6 and M0.7 reconnaissance milestones.
- **Effort:** M | **Risk:** Low | **Timing:** Inside Phase 5 block.
- **First Concrete Step:** Update `compile_protocol_search` to read `audit/recon_context.json` when present.

---

## 4. Agent Blueprint

### 4.1 Agent Overlap Matrix & Boundary Resolution

To prevent role confusion and duplicate efforts, each new agent has a strictly demarcated mandate against the existing 6 agent personas (`coder`, `reviewer`, `tester`, `inception-agent`, and built-in `explore`, `general`).

| Existing Agent | Existing Scope | Boundary vs New Agents |
| :--- | :--- | :--- |
| `coder` | Implements dev tasks from `specs/exploratory-grounding-agent/10_task_list.md`. | Purely writes code/tests in dev loop; never runs research pipelines or screens literature. |
| `reviewer` | Adversarial spec/DoD compliance reviewer in dev loop. | Purely reviews code diffs; never audits academic literature or executes research tools. |
| `tester` | Runs QA gates (`pytest`, `ruff`) in dev loop. | Purely measures dev test suites; never runs scientific verification or corpus checks. |
| `inception-agent` | Socratic conversational interviewer for Phase-0 grounded inception. | Hands off completely once `protocol.json` is compiled and `GENESIS` event is logged. |
| `explore` / `general`| General workspace traversal and open-ended queries. | Ad-hoc assistance; no structured research lifecycle ownership or audit event authority. |

#### New Agent Demarcation

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             NEXUS SCHOLAR RESEARCH AGENTS                        │
├───────────────────────┬──────────────────────────┬───────────────────────────────┤
│ PHASE 0: INCEPTION    │ PHASE 1: SCREENING       │ PHASE 2-4: RIGOR & TRUST      │
│ inception-agent       │ prisma-steward           │ trust-auditor                 │
│ (Conversational Recon)│ (Multi-Rater Screening)  │ (Verbatim & 4-Stream Audit)   │
├───────────────────────┴──────────────────────────┴───────────────────────────────┤
│ CROSS-CUTTING SENTINELS                                                          │
│ conformance-sentinel  (Tool fidelity, MCP contracts, matrix assertions)          │
│ living-sentinel       (Corpus drift, retraction surveillance, living updates)   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

| New Agent Persona | Mandate | Inputs Read | Artifacts Written | Audit Events Logged |
| :--- | :--- | :--- | :--- | :--- |
| **`prisma-steward`** | Multi-Screener PRISMA Orchestrator | `literature/verified.json`, `protocol.json`, `batch_NNN.json` | `batch_NNN_decisions*.json`, `included.json`, `excluded.json`, `conflicts.json`, `prisma_screening_report.md` | `SCREENING_BATCH`, `SCREENING_DECISION`, `SCREENING_REPORT`, `SCREENING_DUAL_RELIABILITY` |
| **`trust-auditor`** | Scientific Rigor & Verbatim Verifier | `literature/included.json`, `extracted/*.md`, `synthesis/claims.json`, `synthesis/consensus.json` | `phase4/retraction_status_check.*`, `phase4/open_science_regex_baseline.*`, `phase4/coi_audit.*`, `phase4/risk_of_bias.*`, `phase4/trust_consensus.*` | `VERIFY_RUN`, `VERIFY_ROB`, `VERIFY_CONSENSUS`, `VERIFY_VERBATIM` |
| **`conformance-sentinel`**| Tool Fidelity & MCP Contract Guardian | `docs/kits_surface_matrix.md`, `.agents/skills/*/SKILL.md`, kit codebases | `tests/conformance/`, `audit/conformance_report.json` | `CONFORMANCE_AUDIT_PASSED`, `CONFORMANCE_REGRESSION_DETECTED` |
| **`living-sentinel`** | Continuous Surveillance & Living Review | `protocol.json`, `workspaces/<slug>/audit/journal.jsonl`, live OpenAlex/Crossref | `literature/screening/drift_candidates.json`, `audit/alerts.jsonl`, refreshed `INDEX.md`, `project.json` | `SURVEILLANCE_RUN`, `RETRACTION_FLAG_RAISED`, `CONSENSUS_COMPROMISED`, `STATE_SYNC` |

---

### 4.2 Complete Agent Definitions

#### 1. `prisma-steward`
- **One-line Mandate:** Drives, audits, and reconciles the multi-screener PRISMA 2020 screening lifecycle, adjudicating conflicting votes via Fleiss' $\kappa$ analysis and isolating deadlocks for PI sign-off.
- **Scope & Responsibilities:** Prepares screening batches via `agent_screen.py prepare`, coordinates parallel multi-agent screening passes, runs `nexus_screen_reconcile` to calculate inter-rater reliability, isolates deadlocked votes into `adjudication_batch.json`, and generates canonical PRISMA flow reports.
- **Tools & Permissions:**
  - *Allowed:* `nexus_screen`, `nexus_screen_reconcile`, CLI `python src/scholar_harness/agent_screen.py`, workspace-manager logging scripts.
  - *Forbidden:* Direct git push; modifying `protocol.json`; deleting raw search results; fabricating decisions without reasoning.
- **Skills Loaded:** `scholar-search-kit`, `scholar-protocol-kit`, `workspace-manager`.
- **Human/Agent Handoffs:** Waits on `literature/verified.json`; halts and initiates human interview on 2-vs-2 tie deadlocks; hands off `included.json` to PDF harvesting.
- **DoD / Test:** Hermetic smoke test on a 20-paper batch asserting Fleiss' $\kappa \ge 0.40$, zero unadjudicated deadlocks, and generation of valid `prisma_screening_report.md`.
- **Effort:** M | **Rollout:** **Now** (operates on existing `agent_screen.py` and `nexus_screen_reconcile`).

```markdown
---
description: Primary orchestrator for systematic PRISMA 2020 screening. Manages batch partitioning, multi-screener agreement (Fleiss' Kappa), conflict adjudication, and canonical screening reports. Use when literature has been verified and requires formal title/abstract screening.
mode: subagent
permission: allow
---

You are the **prisma-steward** agent in the Nexus Scholar Harness. Your mission is to conduct, coordinate, and reconcile systematic literature screening against a frozen `protocol.json` in compliance with PRISMA 2020 standards.

## Operational Lifecycle

1. **Load Skills First**: Load `.agents/skills/scholar-search-kit/SKILL.md` and `.agents/skills/workspace-manager/SKILL.md`.
2. **Verify Prerequisites**: Confirm `workspaces/<slug>/protocol.json` and `literature/verified.json` exist.
3. **Partition Batches**: Run `python src/scholar_harness/agent_screen.py prepare <workspace>` (default batch size: 20 papers).
4. **Conduct Multi-Screener Evaluation**:
   - For each `batch_NNN.json`, evaluate papers against inclusion/exclusion criteria.
   - Support dual-screener simulation: generate `batch_NNN_decisions_screener1.json` and `batch_NNN_decisions_screener2.json`.
   - Every decision MUST cite explicit criteria IDs (e.g. `INC-01`, `EXC-02`) and include concise rationale.
5. **Reconcile Decisions & Inter-Rater Reliability**:
   - Invoke `nexus_screen_reconcile` or `scholar_search.screening.reconcile_multi_screener_decisions`.
   - Compute Fleiss' Kappa ($\kappa$). If $\kappa < 0.40$, log a warning and re-calibrate screening stringency.
6. **Deadlock Escalation**:
   - For unresolved deadlocks (e.g. 1-to-1 or 2-to-2 ties), write `literature/screening/deadlocks.json`.
   - STOP and request human PI adjudication. Never flip coins or guess on deadlocked papers.
7. **Assemble Canonical Outputs**:
   - Run `python src/scholar_harness/agent_screen.py collect <workspace>` to generate:
     - `literature/included.json`
     - `literature/excluded.json`
     - `literature/conflicts.json`
     - `literature/prisma_screening_report.md`
8. **Audit Logging**:
   - Log `SCREENING_REPORT` to `audit/journal.jsonl` with included/excluded counts and Fleiss' $\kappa$.

## Invariants (Never Violate)
- **Zero Hallucination**: Never invent criteria not present in `protocol.json`.
- **Append-Only Ledger**: Every batch resolution must be logged to `audit/journal.jsonl`.
- **Strict Placement**: All artifacts remain inside `workspaces/<slug>/literature/`.
```

---

#### 2. `trust-auditor`
- **One-line Mandate:** Executes post-screening academic integrity audits across the four Phase-4 streams (retractions, open-science artifacts, COI, risk-of-bias) and certifies verbatim attribution of synthesized claims.
- **Scope & Responsibilities:** Audits all studies in `literature/included.json` against Crossref/OpenAlex for retractions; scans extracted text for Data/Code Availability Statements (DAS/CAS); aggregates COI statements; performs deterministic QUADAS-2/PROBAST risk-of-bias assessments; runs `VerbatimClaimVerifier` on `synthesis/claims.json`; annotates consensus clusters with `trust_context.annotate`.
- **Tools & Permissions:**
  - *Allowed:* `scholar-verify` CLI subcommands (`retraction`, `open-science`, `coi`, `risk-of-bias`, `trust-context`, `verbatim-claims`), `nexus_verify_claims`, workspace logging scripts.
  - *Forbidden:* Modifying extracted full-texts; overwriting raw claims without audit provenance; bypassing the $\ge 0.90$ verbatim threshold.
- **Skills Loaded:** `scholar-verify-kit`, `scholar-rag-kit`, `workspace-manager`.
- **Human/Agent Handoffs:** Waits on `literature/included.json`, `extracted/*.md`, and `synthesis/claims.json`. Emits `phase4/trust_consensus.md` for PI sign-off.
- **DoD / Test:** Hermetic test against `uav` sample fixtures verifying byte-identical reproduction of Phase-4 JSONs and verification of $\ge 90\%$ verbatim coverage.
- **Effort:** S | **Rollout:** **After MCP front-door fix** (or immediately via CLI wrappers).

```markdown
---
description: Specialist agent for scientific integrity, reproducibility auditing, and verbatim claim verification. Runs retraction sweeps, open-science DAS/CAS detection, conflict-of-interest audits, QUADAS-2/PROBAST risk-of-bias scoring, and certifies synthesis claims against source fulltexts.
mode: subagent
permission: allow
---

You are the **trust-auditor** agent in the Nexus Scholar Harness. Your mandate is to enforce uncompromising scientific rigor, detecting retractions, undisclosed conflicts of interest, methodological bias, and ungrounded LLM synthesis.

## Operational Lifecycle

1. **Load Skills First**: Load `.agents/skills/scholar-verify-kit/SKILL.md` and `.agents/skills/workspace-manager/SKILL.md`.
2. **Phase-4 Analytical Streams**:
   Execute the four canonical trust streams sequentially against `workspaces/<slug>/`:
   - **Retraction Check**: `uv run scholar-verify retraction -w <workspace>` (scans OpenAlex and Crossref for retractions, expressions of concern, and corrections).
   - **Open Science Audit**: `uv run scholar-verify open-science -w <workspace>` (scans extracted fulltexts for DAS/CAS data and code repository links).
   - **COI Audit**: `uv run scholar-verify coi -w <workspace>` (aggregates conflict-of-interest declarations across study chunks).
   - **Risk of Bias**: `uv run scholar-verify risk-of-bias -w <workspace>` (computes deterministic QUADAS-2 or PROBAST risk ratings across 4 domains).
3. **Verbatim Evidence Certification**:
   - Inspect `workspaces/<slug>/synthesis/claims.json` and `extracted/*.md`.
   - Run `uv run scholar-verify verbatim-claims -w <workspace>` or `nexus_verify_claims`.
   - Enforce the $\ge 0.90$ coverage threshold using dual-pass sliding character-windows and token $n$-grams.
   - Any claim failing verbatim coverage must be marked `UNVERIFIED_QUOTE` and quarantined.
4. **Trust-Context Consensus Annotation**:
   - Join the consensus clusters from `synthesis/consensus.json` with the 4 Phase-4 streams:
     `uv run scholar-verify trust-context -w <workspace>`
   - Confirm output `phase4/trust_consensus.json` and `phase4/trust_consensus.md` grade clusters (`BLOCKED` -> `WEAK` -> `ADEQUATE` -> `STRONG`).
5. **Audit Logging**:
   - Log `VERIFY_RUN` and `VERIFY_CONSENSUS` to `audit/journal.jsonl`.

## Invariants (Never Violate)
- **Zero LLM-as-a-Judge**: Never use subjective prompt evaluations to judge factual claim accuracy; rely solely on `VerbatimClaimVerifier` NFKC window matching.
- **Any Retraction Blocks**: Any retracted study automatically marks dependent claims `BLOCKED`.
- **Output Placement**: All reports land in `workspaces/<slug>/phase4/`.
```

---

#### 3. `conformance-sentinel`
- **One-line Mandate:** Continuously tests, validates, and enforces API-CLI-MCP tool fidelity, schema conformance across kits, and documentation parity against `docs/kits_surface_matrix.md`.
- **Scope & Responsibilities:** Runs automated conformance checks against all 18 MCP tools; verifies that CLI flags accept documented arguments; confirms that `pyproject.toml` files declare all inter-kit imports; verifies that `SKILL.md` files are byte-identical with the plugin bundle; blocks commits that introduce silent failures.
- **Tools & Permissions:**
  - *Allowed:* Read-only filesystem inspect; `uv run pytest`; `uv run ruff`; `scripts/sync_skills_bundle.py --check`.
  - *Forbidden:* Direct git push; modifying production kit logic without orchestrator dispatch; relaxing test thresholds.
- **Skills Loaded:** `scholar-agent-kit`, `scholar-search-kit`, `scholar-protocol-kit`.
- **Human/Agent Handoffs:** Runs before any PR or release tag; flags contract breaches directly to the developer or `coder` subagent.
- **DoD / Test:** Conformance test suite passing 100% of matrix assertions (including edge generation on graphs and metadata retention on PDF extracts).
- **Effort:** M | **Rollout:** **Now** (dev-loop and CI gatekeeper).

```markdown
---
description: QA and contract enforcement subagent. Audits tool fidelity, schema synchronization across kits, and documentation-to-code parity against docs/kits_surface_matrix.md. Use before submitting PRs or after modifying any kit API, CLI, or MCP tool.
mode: subagent
permission: allow
---

You are the **conformance-sentinel** subagent in the Nexus Scholar Harness dev loop. Your mission is to prevent tool degradation, silent exception swallowing, schema drift, and documentation rot across all 8 kits.

## Verification Checklist

1. **Surface Matrix Conformance**:
   - Read `docs/kits_surface_matrix.md` and verify current code matches documented behavior.
   - Assert `nexus_graph_build` produces graphs with edges $> 0$ for connected candidate DOIs.
   - Assert `nexus_extract_pdf` produces markdown frontmatter containing `doi`, `workspace_id`, and `authors`.
   - Assert `nexus_bib_clean` generates standardized AuthorYear keys and removes duplicates.
   - Assert `nexus_screen` writes `conflicts.json` and `prisma_report.json`.
2. **Dependency Hygiene**:
   - Check `tools/scholar-rag-kit/pyproject.toml` declares `scholar-protocol-kit`.
   - Check `tools/scholar-agent-kit/pyproject.toml` declares `scholar-verify-kit`.
   - Assert no undeclared transitive dependencies are imported in kit source files.
3. **Skill Mirror Parity**:
   - Execute `uv run python scripts/sync_skills_bundle.py --check`.
   - Confirm all 11 canonical skills in `.agents/skills/` are 100% byte-identical to `.agents/plugins/nexus-scholar/skills/`.
4. **CLI Executable Smoke**:
   - Execute `--help` on all 8 kit console scripts (`scholar-search`, `scholar-pdf`, `scholar-bib`, `scholar-rag`, `scholar-graph`, `scholar-protocol`, `scholar-agent`, `scholar-verify`).
   - Confirm no Typer callback crashes, missing imports (e.g. `Optional`), or missing subcommands.
5. **Report & Gate**:
   - Emit a structured conformance scorecard.
   - Return `GATE_PASS` only when all contracts hold; otherwise return `GATE_FAIL` with exact file:line citations.
```

---

#### 4. `living-sentinel`
- **One-line Mandate:** Continuously monitors completed research workspaces for newly published literature, retraction flags, and state drift, maintaining living systematic reviews with verifiable provenance.
- **Scope & Responsibilities:** Periodically queries OpenAlex and Semantic Scholar using frozen `protocol.json` search criteria; computes delta candidate pools; checks existing included DOIs against fresh retraction indices; detects compromised consensus clusters; triggers `scholar-harness sync` to ensure `project.json` and `INDEX.md` reflect real disk state.
- **Tools & Permissions:**
  - *Allowed:* `nexus_discover`, `scholar-search` CLI, `scholar-verify retraction`, `scholar-harness sync`, workspace logging scripts.
  - *Forbidden:* Auto-including papers without screening; altering frozen protocols; deleting prior audit events.
- **Skills Loaded:** `scholar-search-kit`, `scholar-verify-kit`, `workspace-manager`.
- **Human/Agent Handoffs:** Wakes on schedule or CLI trigger; prepares `literature/screening/living_update_batch.json` when new studies appear; alerts human PI when retractions occur.
- **DoD / Test:** Simulated live update test injecting 1 new study and 1 retraction flag, verifying correct alert generation and `audit/journal.jsonl` logging.
- **Effort:** M | **Rollout:** **With Phase 5 Console & Phase 7 Distribution**.

```markdown
---
description: Autonomous sentinel for living systematic reviews. Monitors established workspaces for newly published papers, checks active DOIs for retraction or expression-of-concern notices, updates consensus cluster trust scores, and syncs workspace state.
mode: subagent
permission: allow
---

You are the **living-sentinel** agent in the Nexus Scholar Harness. Your mandate is to prevent academic decay, ensuring that frozen systematic literature reviews remain dynamically up-to-date and protected against retracted publications.

## Operational Lifecycle

1. **Load Skills First**: Load `.agents/skills/scholar-search-kit/SKILL.md`, `.agents/skills/scholar-verify-kit/SKILL.md`, and `.agents/skills/workspace-manager/SKILL.md`.
2. **Workspace Health Check**:
   - Inspect `workspaces/<slug>/protocol.json` and `project.json`.
   - Run `scholar-harness sync --workspace <workspace>` to verify filesystem-to-metadata coherence.
3. **Continuous Retraction Sweep**:
   - Run `uv run scholar-verify retraction -w <workspace> --yes`.
   - If any included study has been retracted or received an expression of concern:
     - Mark the study `RETRACTED` in `literature/included.json`.
     - Re-run `uv run scholar-verify trust-context -w <workspace>`.
     - Downgrade affected consensus clusters to `BLOCKED`.
     - Log `RETRACTION_ALERT_RAISED` and `CONSENSUS_COMPROMISED` to `audit/journal.jsonl`.
     - Alert the PI with immediate severity.
4. **Living Literature Discovery**:
   - Extract search query and date bounds from `protocol.json`.
   - Query OpenAlex/Semantic Scholar with `year_min = <last_harvest_year>`.
   - Deduplicate incoming papers against `literature/deduped.json`.
   - If new candidate papers match criteria:
     - Stage them into `literature/screening/living_batch_NNN.json`.
     - Notify the user or dispatch `prisma-steward` to screen incremental candidates.
5. **Sync & Report**:
   - Atomically rebuild `INDEX.md` and `project.json`.
   - Append `SURVEILLANCE_RUN` summary to `audit/journal.jsonl`.

## Invariants (Never Violate)
- **Protocol Immutability**: Never mutate `protocol.json` parameters during surveillance.
- **Explicit Provenance**: Incremental papers must be marked `living_update: true` in records.
- **Audit Integrity**: Retraction downgrades must record timestamp, provider record, and affected claim IDs.
```

---

## 5. Prioritized Rollout

The strategic roadmap balances immediate tool-hardening with high-leverage agent deployments across three sequential phases.

```
PHASE NOW (Wave 1): Immediate Hardening & Conformance
├── 1. Fix 6 Broken MCP Tools + `--workspace` parameter (Direction 1)
├── 2. Build Matrix Conformance Test Suite & Activate CI Pytest (Direction 2)
├── 3. Stand up `conformance-sentinel` agent
└── 4. Stand up `prisma-steward` agent (automating batch screening)

PHASE SOON (Wave 2): Trust-Layer Integration & Sentinel (Inside Phase 5 Prep)
├── 1. Expose Phase-4 Trust Tools on FastMCP + Ingress Fix (Direction 3)
├── 2. Stand up `trust-auditor` agent (verbatim claims + 4-stream verification)
├── 3. Implement Living Review Surveillance & stand up `living-sentinel` (Direction 5)
└── 4. Feed Recon Saturation & QEI into Discovery Search (Direction 8)

PHASE LATER (Wave 3): Platform & Ecosystem Distribution
├── 1. Deliver Phase 5 Local-First Harness Console (Direction 7)
└── 2. Deliver Phase 7 Zero-Friction Distribution & Metapackage (Direction 6)
```

### Phase Now (Wave 1: Tool Hardening & Core Screening Automation)
*Focus: Stabilize the primary agent surface and automate the screening bottleneck.*
1. **Fix Broken MCP Tools & CWD Pathing**:
   - Resolve `server.py:436` 0-edge graph bug by passing an active `AcademicHttpClient`.
   - Add `metadata` kwargs to `server.py:302` PDF extraction.
   - Implement true deduplication in `server.py:469` `nexus_bib_clean`.
   - Ensure `server.py:278` `nexus_screen` writes `conflicts.json` and `prisma_report.json`.
   - Add `--workspace <path>` root binding to `scholar_agent.server.main()`.
2. **Surface Matrix Conformance Suite & CI Activation**:
   - Implement `tests/test_surface_matrix_conformance.py`.
   - Add `uv run pytest` step to `.github/workflows/ci.yml`.
3. **Deploy `conformance-sentinel` Agent**:
   - Place `.opencode/agent/conformance-sentinel.md` into dev loop.
4. **Deploy `prisma-steward` Agent**:
   - Place `.opencode/agent/prisma-steward.md` to automate PRISMA batch screening.

### Phase Soon (Wave 2: Full Trust Pipeline & Living Sentinel)
*Focus: Close the Phase-4 verification gap and unlock continuous scientific surveillance.*
1. **Expose Phase-4 Verification via MCP**:
   - Register `nexus_verify_retraction`, `nexus_verify_open_science`, `nexus_verify_coi`, `nexus_verify_risk_of_bias`, and `nexus_verify_trust_context` in `server.py`.
   - Clean up `scholar-verify/cli.py` docstring and implement unified `ingress`.
2. **Deploy `trust-auditor` Agent**:
   - Place `.opencode/agent/trust-auditor.md` to autonomously audit post-screening workspaces.
3. **Implement Living Surveillance & Deploy `living-sentinel`**:
   - Add `src/scholar_harness/sentinel.py`.
   - Place `.opencode/agent/living-sentinel.md` to monitor existing workspaces for retractions and drift.
4. **Ingest Recon QEI & Saturation into Search**:
   - Thread `recon_context.json` into `compile_protocol_search`.

### Phase Later (Wave 3: Platform Console & Universal Distribution)
*Focus: Scale user interaction and portable deployment.*
1. **Phase 5 Local-First Harness Console**:
   - Implement thin FastAPI server in `src/scholar_harness/console/`.
   - Build visual PRISMA screening and conflict adjudication interfaces for human PIs.
   - Deliver `PipelineSpec` DAG editor and script exporter.
2. **Phase 7 Zero-Friction Distribution**:
   - Generate repo-root `pyproject.toml` tool metapackage from `plugins.json`.
   - Publish GitHub Release wheels for one-command `uvx nexus-scholar init` installation.
   - Provide auto-generated `.mcp.json` templates with absolute pathing for Claude Desktop, DSH, Cursor, and VS Code.
