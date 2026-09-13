# Harness Full-Picture Rating, Vision & Agent Blueprint (Synthesized)

> **Context**: This document is a synthesized "third-eye" review merging the comprehensive evaluations from two prior vision reports (`harness_vision_report-11.md` and `harness_vision_report.md`). It provides a consolidated holistic scorecard, strategic vision, unified agent blueprint, and prioritized rollout plan.

---

## 1. Holistic Rating & Evidence Scorecard

| Dimension | Score (0–10) | Core Evidence & Rationale |
| :--- | :---: | :--- |
| **1. Architecture** | **7.5** | **Strengths**: Clean thin-orchestrator separation; immutable file-first contracts driving zero-sync-engine collaboration; clean subsystem decomposition across 8 orthogonal kits. <br>**Weaknesses**: Two parallel pipeline engines coexist with divergent semantics; undeclared cross-kit dependencies (e.g., `rag` importing `protocol`); mock-leakage in orchestrator pipelines. |
| **2. Reliability** | **5.0** | **Strengths**: Strict algorithmic verification (sliding-window verbatim checks, deterministic FAIR recon); atomic filesystem writes. <br>**Weaknesses**: Known-broken MCP tools in production (0-edge graph bugs, PDF metadata dropping, bib linting failures); primary Stage-1 pipeline silently swallows `AttributeError`s yielding empty searches; CWD-relative resolution traps for MCP servers. |
| **3. Automation Depth** | **6.5** | **Strengths**: Autonomous literature reconnaissance and PRISMA agent-screening handoffs; atomic state synchronization via `sync`. <br>**Weaknesses**: Manual deadlock adjudication (tie-breaking requires human intervention); Phase-4 trust verification streams are strictly CLI-only; disconnected synthesis and trust contexts. |
| **4. Operability & DX** | **6.5** | **Strengths**: Exhaustive factual documentation (`kits_surface_matrix.md`); authoritative 11/11 skill mirror synchronization hygiene. <br>**Weaknesses**: Documentation rot (hidden MCP tools, stale test counts); cold-onboarding friction (workspaces are empty out-of-the-box); opaque kit CLI testing. |
| **5. Distribution Readiness** | **3.0** | **Strengths**: Sophisticated Phase-7 architectural blueprint; standalone local-first autonomy (zero external DBs). <br>**Weaknesses**: Zero-friction distribution is completely deferred; MCP server lacks `--workspace` root resolution; plugin manifests unpinned (relying on `main` instead of commit hashes). |
| **6. Test Confidence** | **5.5** | **Strengths**: 248 green hermetic unit/property tests; deterministic wizard verification. <br>**Weaknesses**: Zero automated E2E conformance tests for MCP/CLI surfaces (the matrix is assertion-free markdown); CI workflow completely skips `pytest`. |
| **Overall Verdict** | **~5.7** | **The Nexus Scholar Harness is a rigorously-specified, mathematically grounded research engine whose brilliant architectural foundations are currently bottlenecked by an unhardened MCP front-door, manual automation loops, and an entirely deferred distribution layer.** |

---

## 2. Strategic Vision (12–24 Months)

In 12 to 24 months, the Nexus Scholar Harness will transition from an internal developer monorepo into the **definitive, bench-portable operating system for verifiable academic research**. It establishes the computational gold standard for systematic literature reviews (SLRs), meta-analyses, and rapid evidence assessments (REAs). 

- **The Trust Inversion & Tooling Healing**: In the first 3–6 months, the "fix-the-tooling wave" will retire every silent failure in the primary path. The surface matrix will stop being static markdown and evolve into an executable conformance suite that automatically polices regressions.
- **Console, CLI, and MCP Convergence**: The Phase-5 Harness Console will un-ship its "deferred" label, granting qualitative researchers a zero-DB, local-first GUI to run the entire search→screen→harvest→synthesize loop with byte-identical parity to terminal execution.
- **Autonomy Without Hallucination**: Autonomous loops will completely orchestrate PRISMA screening, Fleiss' $\kappa$ scoring, and saturation-driven recon feedback. Meanwhile, Phase-4 verification (retraction sweeps, open-science scanning, COI, RoB) will act as an immune system, continuously verifying corpus integrity.
- **The Verification-First Evidence Brief (The Killer Feature)**: The ultimate North Star is a distinctive, publishable artifact matching every synthesized claim with verbatim verification, consensus scoring, and four-stream trust audits—a capability impossible to replicate through simple LLM scraping.
- **One `uvx` Anywhere**: With Phase 7, the ecosystem becomes truly portable. `uvx nexus-scholar init` will allow any researcher on any interface (Claude Desktop, Cursor, Terminal) to instantiate a self-contained, Git-tracked research cell in seconds.

---

## 3. Ranked Strategic Directions

| Rank | Direction | Key Outcome | Effort | Phase Timing |
| :---: | :--- | :--- | :---: | :--- |
| **1** | **MCP Front-Door Hardening & E2E Fixes** | Fix the 6 broken tools (graph, PDF, bib), add `--workspace` binding, and repair the primary orchestrator pipeline to prevent silent empty searches. | **M** | **Before** Phase-5/7 |
| **2** | **Executable Conformance Suite** | Convert `kits_surface_matrix.md` and `actions.py` into executable tests; gate GitHub Actions CI on `pytest` success. | **M** | **Before** Phase-5/7 |
| **3** | **Multi-Screener PRISMA Steward** | Automate batch prep, calibration gating, multi-rater $\kappa$ scoring, and deadlock adjudication. | **S-M** | **Before** Phase-5 |
| **4** | **Phase-4 Verification onto Agent Surface** | Expose retraction, open-science, COI, and RoB as MCP tools and Console actions; remove the `ingress` NIT. | **S** | **Before** Phase-5 |
| **5** | **Recon Saturation → Pre-Screening** | Route Inception recon signals (QEI, saturation labels) into Phase-1 search expansion and screening thresholds. | **M** | **Before** Phase-5 |
| **6** | **Phase-5 Thin Local-First Console** | Launch the FastAPI/HTML dashboard for human-in-the-loop PI sign-offs and DAG execution visualization. | **M** | **Inside** Phase-5 |
| **7** | **Verification-First Evidence Brief** | Produce a first-class human-auditable artifact compiling trust consensus, verifiable claims, and screening provenance. | **M** | **Inside** Phase-6 |
| **8** | **Continuous Living Review Sentinel** | Periodic autonomous sweeps over completed workspaces to flag retractions, discover new literature, and update consensus. | **M** | **Inside** Phase-6 |
| **9** | **Plugin-Manifest Hardening** | Enforce hash pins (SHAs) and resolve explicit dependency edges in `plugins.json`. | **S** | **Before** Phase-7 |
| **10** | **Phase-7 Bench-Portable Distribution** | Ship the `nexus-scholar` metapackage, universal MCP configurations, and `uvx` zero-friction initialization. | **L** | **Inside** Phase-7 |

---

## 4. Unified Agent Blueprint

To prevent role confusion and duplicate efforts, each agent has a strictly demarcated mandate. The operational landscape consists of the foundational dev-loop agents (`coder`, `reviewer`, `tester`), the foundational `inception-agent`, and **seven new structured research/operations personas**.

### The 7 New Personas

1. **`prisma-steward`**: *PRISMA Screening Orchestrator*
   - **Mandate**: Drives the multi-screener PRISMA 2020 loop (prepare → decide → reconcile → collect), gating on 20-paper calibration passes.
   - **Responsibility**: Computes Fleiss' $\kappa$ agreement, surfaces deadlock manifests for human adjudication, and generates canonical reports. Never invents criteria.

2. **`verify-steward` (formerly `trust-auditor`)**: *Corpus Trust & Integrity*
   - **Mandate**: Certifies the corpus across the four Phase-4 streams (retraction, open-science, COI, risk-of-bias) and enforces verbatim extraction metrics.
   - **Responsibility**: Maintains the `phase4/` trust artifacts and compiles the D7 verification-first evidence brief. Never alters the underlying inclusion set.

3. **`console-operator`**: *Console Supervisor*
   - **Mandate**: Runs and supervises the Harness Console without improvising shell commands.
   - **Responsibility**: Starts/cancels jobs via `/api/v1/jobs`, dry-runs `PipelineSpec` DAGs, and guarantees successful terminal events in the audit ledger. 

4. **`conformance-sentinel` (formerly `conformance-qa`)**: *Contract Guardian*
   - **Mandate**: Polices API-CLI-MCP tool fidelity, documentation parity, and skill-tree synchronization.
   - **Responsibility**: Runs read-only automated conformance checks against the surface matrix and generates tasks for the `coder`. Never edits kit source directly.

5. **`recon-curator`**: *Reconnaissance Custodian*
   - **Mandate**: Manages grounded-recon state (sessions, lexicons, saturation) to convert gap signals into search criteria.
   - **Responsibility**: Proposes lexicon merges and emits saturation hints. Strictly adheres to Anchor Provenance Rules (APR); never hallucinates unanchored topics.

6. **`living-sentinel`**: *Living Review Surveillance*
   - **Mandate**: Continuously monitors frozen research workspaces for newly published literature and retraction flags.
   - **Responsibility**: Audits included DOIs against fresh open-science indices, updating consensus cluster trust scores and logging alerts for the PI.

7. **`release-packager`**: *Distribution Maintainer*
   - **Mandate**: Owns the Phase-7 distribution surface (`uvx` metapackage, hash-pinned manifest, `doctor` matrix).
   - **Responsibility**: Validates `init`/`setup-mcp` output shapes in a fresh temp folder gate, enforcing clean workspace layout generation. 

---

## 5. Prioritized Rollout Plan

| Phase | Core Deliverables | Immediate First Step |
| :--- | :--- | :--- |
| **NOW (Foundation)** | <ul><li>`conformance-sentinel` agent & `tests/conformance/`</li><li>`prisma-steward` agent & calibration gate</li><li>Manifest hash pinning</li><li>Provider execution fix in Orchestrator Stage 1</li></ul> | Fix `orchestrator.py:395` (AttributeError swallowing). Resolve `plugins.json` from `main` to explicit commit SHAs. |
| **Post-Tooling Wave** | <ul><li>`verify-steward` agent (Phase-4 streams)</li><li>`recon-curator` agent (saturation loops)</li><li>Validated E2E fixes (PDF metadata, Graph build)</li></ul> | Add `@mcp.tool()` wrappers for the 4 `verify` subcommands. Pipe `pool_saturation.json` into PRISMA. |
| **Inside Phase-5** | <ul><li>Launch Thin Local-First Console</li><li>`console-operator` agent</li><li>Integrate Phase-4 verification actions into dashboard</li></ul> | Fix `actions.py:78` `extract` command parity and run GUI byte-identity tests. |
| **Inside Phase-6** | <ul><li>`living-sentinel` continuous surveillance</li><li>Verification-First **Evidence Brief** (`evidence_brief.md`)</li></ul> | Create `evidence_brief.py` integration reading `trust_consensus.json` & `claims.json`. |
| **Inside Phase-7** | <ul><li>`nexus-scholar` distribution metapackage</li><li>`release-packager` agent</li></ul> | Add `--workspace` CLI argument to `scholar_agent.server.main()`. |
| **Later Horizons** | <ul><li>Jupyter Notebook suite (`00_research_inception.ipynb`)</li><li>Zotero/Typst bridges for external qualitative work</li></ul> | Commit `00_research_inception.ipynb` smoke tests. |
