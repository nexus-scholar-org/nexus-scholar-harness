# Exploratory Grounding Agent — Specification

> **Status:** Proposal / Architecture Brainstorm
> **Date:** 2026-09-11 (folder created 2026-09-12)
> **Authors:** Nexus Scholar Architecture Team
> **Supersedes:** `docs/phase_0/06_exploratory_grounding_agent.md` (split into this folder)
> **Extends:** `docs/phase_0/04_socratic_inception_protocol.md`
> **Related decision:** Contribution gate enforced by `.agents/skills/pull-request-gate/SKILL.md` (fork + PR workflow).

---

## What this folder is

The single-file proposal `docs/phase_0/06_exploratory_grounding_agent.md` has been replaced by this folder of detailed, interdependent specs. The folder is the canonical home for the **Grounded Exploratory Inception Agent**: a sandboxed literature-reconnaissance layer that runs *before* protocol freezing, distills the empirically prevailing taxonomy of a research niche, and returns grounded, citation-backed research directions.

## Document map

| Spec | Scope |
| :--- | :--- |
| [`01_problem_definition.md`](./01_problem_definition.md) | The "cold inception" problem: why fuzzy curiosity cannot be fed straight into a frozen protocol, and the proposed reconnaissance-loop solution. |
| [`02_architecture.md`](./02_architecture.md) | System architecture: components, sequence diagram, and cache/workspace separation. |
| [`03_lifecycle.md`](./03_lifecycle.md) | The 5-step reconnaissance & grounding lifecycle in detail. |
| [`04_memory_and_cache.md`](./04_memory_and_cache.md) | Two-tier storage architecture, hierarchical cache keys, session schema, invalidation rules. |
| [`05_tool_contracts.md`](./05_tool_contracts.md) | Harness subsystem roles — **verified against the real kit APIs** (no invented methods). |
| [`06_deployment_options.md`](./06_deployment_options.md) | Implementation options: CLI wizard, autonomous agent/MCP, harness web console. |
| [`07_walkthrough.md`](./07_walkthrough.md) | Concrete end-to-end walkthrough (LLM unit-test generation for legacy COBOL/Fortran). |
| [`08_milestones.md`](./08_milestones.md) | The M0.x implementation milestones, each with a **Definition-of-Done (DoD)** gate. |
| [`09_mcp_integration.md`](./09_mcp_integration.md) | The Nexus MCP surface (`nexus_*` tools) that an agent uses to drive grounded inception. |
| [`10_task_list.md`](./10_task_list.md) | **Implementation checklist** (T0.x … T6.x + QA + PR gates) mirroring M0.1–M0.6 — the single source of truth the dev-loop agents tick off. |
| [`11_honest_review.md`](./11_honest_review.md) | Post-M0.1…M0.5 honest retrospective (& priorities P1–P3). |
| [`12_semantic_grounding.md`](./12_semantic_grounding.md) | **M0.6** — semantic search modes (OpenAlex `search.semantic`) + classifier-grounded Topics taxonomy (anchored `topics` layer, thin-topic adaptive triggers). |
| [`13_evaluation.md`](./13_evaluation.md) | Evaluation framework — 4 measurable dimensions (epistemic integrity, recon signal, downstream yield, autonomous navigation), ReconBench corpus/runner, prioritized gates (M0.7). |
| [`14_agent_loops.md`](./14_agent_loops.md) | Autonomous agent operating contract — 5 loops (dual-mode discovery, lexicon bootstrap, Pareto scoring, anchor-guarded compile, downstream transition) + the 2 required MCP seams (GAP A lexicon, GAP B saturation). |
| [`15_scientific_publication_plan.md`](./15_scientific_publication_plan.md) | **Scientific Publication Plan & Research Blueprint** — publication strategy, theoretical framing, ReconBench empirical evaluation, mathematical formulas (APR, QEI), target venues, and 6-week roadmap. |

## Executive summary — the cold inception problem

The current Phase-0 Socratic interview (`scholar_harness.inception` / `methodology-copilot`) transforms raw curiosity into a machine-readable protocol by asking: unit of analysis? gold-standard proof? search concepts & synonyms? out-of-scope?

A user arriving with a **messy, vague, or nascent curiosity** cannot answer these well:

1. **The user does not know what they do not know**: they cannot supply accurate search synonyms, baseline datasets, or gold-standard metrics before surveying the current landscape.
2. **Pure LLM hallucination risk**: relying only on parametric knowledge produces outdated or imaginary library names, benchmark datasets, and research gaps.
3. **Premature protocol freezing**: freezing `protocol.json` before verifying literature exists under those terms causes downstream failure (zero Phase-1 hits, or screening thousands of irrelevant papers).

### Proposed solution: empirical reconnaissance loop

Before freezing the protocol, deploy an **autonomous reconnaissance loop** that:

1. Conducts scratch semantic queries against OpenAlex and Semantic Scholar (plus Crossref/arXiv via the search-kit engine).
2. Rapidly pulls a micro-corpus (**10-25 candidate abstracts + 2-3 Open Access full texts**).
3. Distills the **empirically prevailing taxonomy**: actual terminology, dominant benchmark datasets, prevailing metrics, distinct sub-schools of thought.
4. Returns **2-3 grounded, structured research directions** backed by real citations.
5. Persists exploratory cache and memory in an isolated scratchpad (`.cache/inception_recon/`) without cluttering `workspaces/`.