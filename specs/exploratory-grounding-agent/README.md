# Grounded Exploratory Inception — current specification

> **Status:** Implemented and current. The recon subsystem lives in
> `src/scholar_harness/recon/`; the inception wizard in `src/scholar_harness/inception/`.
> The former milestone/proposal documents were removed in the 2026-10-12
> consolidation; the surviving detail files are listed below.

## What it is

A sandboxed literature-reconnaissance layer that runs **before** protocol
freezing. It probes the live literature, distills the empirically prevailing
taxonomy of a niche, and returns grounded, citation-backed research directions,
so a researcher arriving with fuzzy curiosity is not forced to invent search
synonyms, benchmarks, or gaps from parametric memory alone.

## Lifecycle (5 steps, all before any `workspaces/` scaffold exists)

1. **Intent clarification** (human-in-the-loop): narrow curiosity into probe-able
   axes and an ordered list of **semantic probe queries** (not boolean strings).
2. **Empirical surface scan** (deterministic + search-computed): fire the probes
   (OpenAlex-first provider order via the search kit); **cap the working pool at
   10–25 abstract records**; **abstract-only** — no full-text extraction (that is
   Phase 2); keep pool content within ~15k tokens per probe.
3. **Micro-extraction / distillation**: the harness distiller derives the
   prevailing terminology, benchmark datasets, metrics, sub-schools (`schools`),
   and topics from the pool.
4. **Direction proposal**: 2–3 grounded, structured directions, each anchored to
   real citations, validated by the researcher.
5. **Persistence**: exploratory state is written to the isolated recon cache
   (below) and never to `workspaces/`.

## Cache-root rules (CWD-independent, never in `workspaces/`)

- Recon state lives under the **canonical cache root**: `NEXUS_RECON_ROOT` if
  set, else `<repo>/.cache/inception_recon`. It is gitignored (`.gitignore`).
- The root is resolved CWD-independently so the interactive CLI wizard and the
  MCP server (launched `--directory tools/scholar-agent-kit`) share **one** cache.
- Cache is per-session scratch: pruned on success or by age. Detail and schema:
  [`04_memory_and_cache.md`](./04_memory_and_cache.md).

## Tool boundaries

| Step | Tool |
|---|---|
| 2 probe | `recon_probe` (`semantic=` opt-in); fallback `nexus_discover` + `nexus_dedup` |
| 3 distill | `recon_distill` (emits micro-taxonomy/metrics/datasets, plus topics/schools) |
| 4 directions | `recon_delta` (thin schools → thin topics) + researcher validation |

Tool replies return **paths and previews**, not prose bodies — the JSON artifacts
are on disk and machine-continuable. Recon does **not** extract full text.
Contracts: [`09_mcp_integration.md`](./09_mcp_integration.md),
[`14_agent_loops.md`](./14_agent_loops.md) (autonomous-loop operating contract
and the two required MCP seams: lexicon bootstrap, saturation).

## Evaluation gates

| Gate | Value | State |
|---|---|---|
| **Anchor Provenance Rate (APR)** | 100% — hard invariant | **Enforced** (M0.3); every protocol concept has ≥1 pool DOI |
| **QEI** (Query Echo Index) | target ≤ 0.3 — *advisory* | A lexical dispersion index; it **inverts on well-scoped semantic seeds**, so it never rejects a pool that the purity gate calls `coherent` |
| **Pool admission** (`recon/gates.py`) | surfaced as `pool` / `purity` on the `recon_distill` reply | Implemented; thresholds are module constants; the wizard prints an advisory line and never aborts — the human stays the gate |
| **Saturation label** | `scant` \| `sparse` \| `dense` per followup | Reporting target; validation seam is the unconstrained corpus count |

The full framework (dimensions, ReconBench, prioritised gates) is in
[`13_evaluation.md`](./13_evaluation.md).

## Surviving detail documents

| Spec | Scope |
| :--- | :--- |
| [`03_lifecycle.md`](./03_lifecycle.md) | The 5-step lifecycle in detail. |
| [`04_memory_and_cache.md`](./04_memory_and_cache.md) | Two-tier storage, cache keys, session schema, invalidation. |
| [`09_mcp_integration.md`](./09_mcp_integration.md) | The MCP surface an agent uses to drive grounded inception. |
| [`10_task_list.md`](./10_task_list.md) | The historical implementation checklist (closed; cited by the dev-loop agent definitions). |
| [`13_evaluation.md`](./13_evaluation.md) | Evaluation framework and gates. |
| [`14_agent_loops.md`](./14_agent_loops.md) | Autonomous agent operating contract (5 loops + 2 MCP seams). |
| [`16_inception_improvements.md`](./16_inception_improvements.md) | Post-evaluation improvement backlog and per-fix status. |

Removed in the 2026-10-12 consolidation (recoverable from git history): the
problem-definition, architecture, tool-contract, deployment-option, walkthrough,
milestone, honest-review, semantic-grounding and publication-plan documents, and
the calibration trial JSONs.
