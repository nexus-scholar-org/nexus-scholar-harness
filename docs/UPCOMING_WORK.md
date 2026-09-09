# Outstanding Tasks & Roadmap Analysis

This document aggregates all the outstanding, "undone" work across the Nexus Scholar repository. I have synthesized this from the `OPEN_SCIENCE_ROADMAP.md`, `ROADMAP_ASSESSMENT_AND_TASK_LIST.md`, and the architectural retrospective.

## 1. Immediate Architectural Debt (The "Fixes")
*Derived from the Phase 1-3 Retrospective. These are critical stability improvements.*

- ~~[P0] Windows CLI Stability~~ **DONE (commit `58283ac`).**
- ~~[P0] PDF Retrieval Resilience~~ **DONE:** `scholar-pdf-kit` gained institutional-proxy support and hardened PDF validation. Subdomain-prefix proxy style for SNL (`*.www.sndl1.arn.dz`), EZproxy (`login?url=`), and OpenAthens (`proxy.openathens.net`) via `rewrite_via_proxy(url, proxy_url, style="auto|subdomain|ezproxy|prefix")`, with `is_proxied_url()` guarding against double-proxying; the downloader's attempt-3 cascade re-runs the OA/direct-PDF candidates through the proxy when vanilla attempts hit Cloudflare/WAFs. New `--proxy`, `--proxy-style`, and `--strict-validate` flags on `scholar-pdf download|ingest`. Validation upgraded from a 5-byte check to a binary signature gate: `%PDF-<major>.<minor>` within the first 1024 bytes, `%%EOF` trailer within the last 8 KB, 10 KB size floor, plus optional pypdf structural validation (`validate_pdf_structure()`, encryption-tolerant). Existing failed-download dogfood behaviors (HTML block pages, "Checking your browser", truncated payloads) now reliably rejected.
- **[P1] State Syncing:** Add a `scholar-harness sync` command to atomically rebuild `project.json` and `INDEX.md` from filesystem state.
- **[P1] Screener Bias Calibration:** Add a 20-paper pre-flight calibration test and a boolean checklist to `scholar-agent-kit` to prevent wild variations in inclusion rates.
- **[P1] Discovery Integrity:** Enforce strict bidirectional title similarity when hydrating DOIs to prevent PubMed cross-contamination.

## 2. Unfinished Roadmap Tasks (The "Features")
*Derived from the `ROADMAP_ASSESSMENT_AND_TASK_LIST.md` and `OPEN_SCIENCE_ROADMAP.md`.*

### Phase 0: Intent Router
- [x] **Interactive Inception CLI**: A terminal wizard to conduct the Socratic interview — `uv run scholar-harness inception --root <repo>`. Implements the 4-stage Socratic protocol (`docs/phase_0/04_socratic_inception_protocol.md`): latent paradigm mining, 4-way refraction grid, Socratic boundary grill (unit of analysis, gold-standard proof, exclusions, lexicon enforcement), then emits `intent.json`, compiles the fingerprinted `protocol.json` and `SCREENING_CRITERIA.md`, scaffolds `workspaces/<slug>/`, and logs the `GENESIS` audit event. Responder-driven so tests are hermetic and scriptable.
- [x] **Protocol Generator**: The wizard compiles `protocol.json` directly through the deterministic `scholar-protocol-kit` compiler (no hand-authoring); intent → canonical bytes are reproducible (`sha256:` fingerprint verified by tests).
- [x] **Playbook Archetypes**: Preset templates selected at runtime from `scholar-protocol-kit`'s `PlaybookType` (`PRISMA_SLR`, `SCOPING_REVIEW`, `RAPID_EVIDENCE`, `DESIGN_SCIENCE`, `STUDENT_DISSERTATION`) with paradigm→playbook recommendations and per-playbook trustworthiness frameworks.

### Phase 1: Discovery & Harvesting
- [x] **Citation Snowballing**: Backward/forward reference traversal built into `scholar-search-kit` — single-hop `scholar-search snowball <id>` plus multi-hop BFS `scholar-search chain <seed...> --depth N` (deduped frontier, cycle protection, per-node/total caps, year bounds, edge manifest). Live-verified against OpenAlex in both directions.

### Phase 2: Synthesis & Graphs
- [x] **Consensus Cartographer**: A deterministic, hermetic claim-clustering tool in `scholar-rag-kit` (`uv run scholar-rag consensus claims.json [--rq-id] [--threshold] [--similarity lexical|sentence-transformers] [--output-json] [--output-md]`) that groups extracted synthesis claims into high-consensus vs. active-debate buckets. Jaccard greedy clustering (threshold 0.30) or optional embedding-cosine clustering (`embedder_claim_scorer`, threshold ~0.40; falls back to lexical on embedder errors), polarity-lexicon stance attribution (`POSITIVE`/`NEGATIVE`/`NEUTRAL`, auto-derived from claim text), per-study majority-stance dedup, and verdict rules (`HIGH_CONSENSUS`, `ACTIVE_DEBATE`, `UNRESOLVED`, `PROVISIONAL`). `scholar-rag synthesize --output-claims claims.json` now emits per-claim `study_id`/`stance` for downstream cartography. Semantic path added after dogfooding on `uav-cv-precision-agriculture` showed real-literature paraphrases (max pairwise Jaccard ~0.17) never merge at 0.30.

### Phase 3: Interactive Interfaces
- [ ] **Jupyter Notebook Suite**: Pre-built templates (`00_research_inception.ipynb`, etc.) that researchers can execute cell-by-cell.
- [ ] **Zotero Sync**: Two-way web API integration.
- [ ] **Overleaf / Typst Bridge**: Automated Git-backed export of the final manuscript.

### Phase 4: Trust Layers
- [x] **Abstracting Phase 4**: Retraction, Open Science, COI, and Risk-of-bias were proven as raw scripts inside the `uav` workspace, then abstracted into the `scholar-verify-kit` (in `tools/scholar-verify-kit/`, CLI `uv run scholar-verify ...`), runnable on *any* workspace. Verified by parity smoke test against the original `uav-cv-precision-agriculture/phase4/` outputs. Dogfooded live in 2026-09: all three offline streams reproduce the legacy 94-study summaries byte-identically, and the fresh online retraction run reports 0 retracted / 0 flagged / 0 errors. The dogfood also caught a real integration bug — `retraction`/`all` hard-coded `literature/screening/included.json` while every other kit uses `literature/included.json` — fixed in the CLI.
- [x] **Trust-weighted consensus** (`scholar-verify trust-context`): hermetic, deterministic annotator that joints a Consensus Cartographer `synthesis/consensus.json` against the four Phase-4 streams (per-study RoB/COI/retraction/open-science details + cluster aggregates) and grades each cluster `BLOCKED` → `UNVERIFIED` → `WEAK` → `ADEQUATE` → `STRONG` into `phase4/trust_consensus.{json,md}`. Core is the pure function `trust_context.annotate(consensus, phase4)`; only retraction introduces runtime variance. Dogfooded on `uav-cv-precision-agriculture`: 12 clusters → 8 ADEQUATE / 2 WEAK / 2 UNVERIFIED / 0 BLOCKED / 0 STRONG (corpus is mostly `?`-risk with sparse `public+link` open-science, so no STRONG is expected). Supports `--rq-id RQ<n>` scoping: per-RQ claim pools (`synthesis/claims_rq*.json`) attribute each cluster's claims to their originating RQ(s) by exact `(study_id, claim_text)` match, clusters carry `rq_ids` provenance, and scoped reports (`phase4/trust_consensus_RQ1.{json,md}`) include cross-RQ clusters as co-members; un-attributed clusters fall back to the report-level RQ codes. Dogfood verified full coverage (union of six per-RQ scopes = all 12 clusters).

### Phase 5: Collaboration & Empowerment (The UI Platform)
Phase 5 transitions the toolkit from a CLI engine into a collaborative, UI-driven platform. **Direction decided 2026-09-07:** the primary interface remains agent-agnostic (CLI + MCP + workspace files); Phase 5 adds a thin, local-first **Harness Console** that renders the same files and triggers the same `uv run` commands agents use — deliberately not a thick web app (no DB, no auth, no in-browser chat). Full design set: [`docs/phase_5/`](./phase_5/) (`README.md` decisions, `BLUEPRINT.md` architecture, `PLAN.md` milestones, `SPECS.md` API + PipelineSpec schema).
- [ ] **Shared Collaborative Workspaces**: Git + append-only audit ledger as the collaboration substrate; no realtime sync engine.
- [ ] **No-Code Workflow Builder**: `PipelineSpec` DAG editor that emits the same JSON `scholar-harness run --pipeline` consumes; dry-run on samples; exports `uv run` scripts.
- [ ] **Domain-Specific Playbooks**: 1-click instantiation of PRISMA SLR / scoping review / REA / meta-research `PipelineSpec` archetypes.

### Phase 6: Scientific Trust & External Harness Bridge (DeepSeek Harness / DSH)
Phase 6 establishes mathematical reliability and anchors the toolkit into modern external multi-agent platforms. Full specification: [`docs/phase_6/README.md`](./phase_6/README.md).
- [x] **Verbatim Evidence Verifier**: Promoted `VerbatimClaimVerifier` into `scholar-verify-kit` (`scholar_verify.verbatim` & `scholar-verify verbatim-claims` CLI) with dual-pass sliding character-windows (8-char, step 4) and token $n$-grams (6-token, step 3) + Unicode NFKC/hyphenation normalization to certify claims against source documents with $\ge 90\%$ verbatim threshold.
- [x] **Multi-Screener Adjudication & Fleiss' $\kappa$**: Built into `scholar-search-kit` (`reconcile_multi_screener_decisions`, `calculate_fleiss_kappa`) to handle $n$-rater consensus ($n \ge 3$), majority voting, and deadlock isolation.
- [x] **FastMCP Protocol Server Exposure**: Exposed `nexus_screen_reconcile` and `nexus_verify_claims` in `scholar-agent-kit` (`scholar_agent.server`), enabling seamless integration into DeepSeek Harness (`dsh`) and OpenCode over standard `stdio`.
- [x] **Phase 6 Specification**: Created [`docs/phase_6/README.md`](./phase_6/README.md) detailing the DSH Creator Mode preset, tool access lockdown, and verifiable provenance principles.

### Phase 7: Zero-Friction Distribution — Bench-Portable Nexus Scholar
Phase 7 makes Nexus Scholar installable anywhere: one `uvx` command, any empty folder, any harness (DeepSeek Harness, Claude Desktop, Cursor, OpenCode, VS Code, terminal), with verifiable provenance in a local `audit/journal.jsonl`. Full blueprint + technical review + deferred checklist: [`docs/phase_7_distribution/README.md`](./phase_7_distribution/README.md). **Declared 2026-09-09 after review; implementation deferred** (see the checklist and deferral note at the end of that spec).
- [ ] **P7.1 `--workspace` rootdir resolution**: `scholar_agent.server.main()` currently takes no args and resolves tool paths from process cwd (`workspace_dir="."`, `db_path="./chroma_db"`); must accept `--workspace <root>` and resolve all defaults against it. This is the portability enabler and blocks every `uvx` example below.
- [ ] **P7.2 Repo-root `nexus-scholar` tool-metapackage**: `[project]` + `[project.scripts]` entrypoints; dependency pins **generated from `.agents/plugins/nexus-scholar/plugins.json`** (single source of truth) by CI; ship as GitHub-Release wheel so `uvx --from <release> nexus-scholar` works.
- [ ] **P7.3 `nexus-scholar init <title>`**: reuse the existing `inception` Socratic wizard; scaffold canonical contract layout + `audit/journal.jsonl` + `.env.example` + `.mcp.json` + skill **symlinks** (never copies → version drift).
- [ ] **P7.4 `nexus-scholar setup-mcp`**: emit `.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json`, and print the Claude Desktop snippet with an **absolute** workspace path baked in (`${workspaceFolder}` doesn't expand there) + `env:` block for keys.
- [ ] **P7.5 `nexus-scholar doctor`**: validate kit versions vs `plugins.json`, API keys, skill resolvability, workspace layout.
- [ ] **P7.6 Ship `log_event`/`batch_log`/INDEX-sync as an importable CLI (`nexus-scholar log`)**: standalone workspaces can't reach repo-relative `scripts/` today.
- [ ] **P7.7 Lazy-import rag/graph** so `init`, `setup-mcp`, `search`, `doctor` never load torch/chromadb (keeps the 1-minute claim honest).
- [ ] **P7.8 CI verification** that the blueprinted `uvx` commands run end-to-end in a fresh temp folder.
- [ ] **P7.9 (deferred) PyPI publication** of the 8 kits + metapackage, only if external consumers appear; verify PyPI name availability first.