# 14 — Autonomous Agent Loops (operating contract)

> **Status:** Proposed — the behavior contract for an unattended research agent (methodology-copilot) driving the recon lifecycle through MCP. Two required MCP seams (GAP A, GAP B) are still missing, so full autonomy is blocked until M0.7.
> **Date:** 2026-09-13 · **Origin:** distilled from `temp_brainstorming.md` (retired).
> **Owner:** methodology-copilot executes; the harness provides the seams. Researcher remains the final gate on direction selection (never auto-emitted protocol without human validation).

## 1. The five loops at a glance

| Loop | Action | Today? |
| :--- | :--- | :--- |
| A | Dual-mode discovery (keyword + semantic) → distill → delta on thin frontiers | ✅ M0.1–M0.6 |
| B | Dynamic lexicon bootstrap (agent derives domain patterns) | ⛔ GAP A (no agent-reachable lexicon seam) |
| C | Pareto direction scoring (`Novelty/Feasibility/Grounding`) | ⛔ agent-side only; terms layers ready |
| D | Anchor-guarded protocol compile | ✅ M0.3 (hard enforce) |
| E | Downstream transition (GENESIS → workspace → Phase-1+) | ✅ M0.3 + existing pipeline |

## 2. Loop A — Dual-mode discovery

1. `recon_probe(topic, semantic=False)` then `recon_probe(topic, semantic=True)` (same session; `/m/semantic/` keys keep pools distinct).
2. `recon_distill(session_id)` → layers: `micro_taxonomy`, `topics`, `schools`, `metrics`, `datasets`.
3. If any school/topic has `n ≤ 2`: `recon_delta(session_id, followups=3)` — bounded follow-ups, 25-pool DOI-union, `dropped_n`, per-followup `reason`.
4. Merge vocabulary; repeat ≤2 more rounds until no thin frontiers remain (convergence target in `13_evaluation.md` §5).

## 3. Loop B — Dynamic lexicon bootstrap — **GAP A**

**Reality:** `LEXICON_FIELDS` ships only `{"default"}`. `merge_lexicons(base, extra)` exists in harness but is not agent-reachable, so the "agent derives domain regexes" loop cannot run through MCP.

**Required seam (M0.7, T7.4):** `recon_distill` gains an optional `lexicon_json` parameter:
- Validate shape: `{metrics: {pattern: label}, datasets: {...}, schools: {...}}` — compile-able regex strings, non-empty.
- Semantics: `merge_lexicons(DEFAULT_LEXICON, parsed)` (extra wins), new frozen object; inputs unmutated.
- Provenance: lexicon hash recorded in the distilled artifact + terms file; determinism preserved (content-addressed name includes the hash).
- Rejection: malformed patterns or a non-object payload → clear error, no partial distill.

**Loop B sequence (post-seam):** read `pool_path` → inspect 10–25 abstracts → derive candidate patterns → verify each matches ≥1 pool doc (anchoring!) → submit `lexicon_json` → distill → metrics/datasets/schools now reflect the field.

## 4. Loop C — Pareto direction scoring

$$\text{Score}(D) = w_1 \cdot \text{Novelty}(D) + w_2 \cdot \text{Feasibility}(D) + w_3 \cdot \text{Grounding}(D)$$

| Component | Operationalization | Signal source |
| :--- | :--- | :--- |
| Novelty | thin frontiers favored (n∈[1,3]); n>15 penalized; n=0 rejected | `recon_delta` gaps / topics+schools `n` |
| Feasibility | benchmark datasets + standard metrics present in pool | `terms.datasets`, `terms.metrics` |
| Grounding | distinct anchor DOIs per candidate axis | `anchor_dois` arrays (all layers) |

- **Contract:** a candidate direction may only reference **anchored terms** (Loop D enforceable).
- **Governance:** weights are methodology-copilot-held configuration, NOT harness code; the harness exposes the signals, the agent resolves the tradeoff.

## 5. Loop D — Anchor-guarded protocol compile

For every `core_concept` / `synonym` entering the `IntentPacket`: cross-reference the terms anchor map. Anchored → keep; unanchored → **drop or one-shot probe** (a `recon_delta`-style follow-up targeting exactly that term). Matches the M0.3 hard-abort semantics when nothing is anchored (empty-pool exit).

## 6. E: Downstream transition

Post-compile: agent initializes the workspace (`workspace-manager`), runs Phase-1+ (`nexus_discover`, `nexus_screen`, `nexus_extract_pdf`, `nexus_rag_*`, `nexus_graph_build`), logging every step to `audit/journal.jsonl` with the `recon_context` session hash (GENESIS event, M0.3 already emits it).

## 7. Tool-matrix (today vs needed)

| Loop | Available today | Needed (M0.7) |
| :--- | :--- | :--- |
| A | `recon_probe` (semantic), `recon_distill`, `recon_delta` | — |
| B | `DomainLexicon`/`merge_lexicons` (harness-internal) | **GAP A:** `lexicon_json` param on `recon_distill` |
| C | terms layers (topics/schools/metrics/datasets + anchors) | agent-side scorer (copilot config) |
| D | `nexus_protocol_compile` + anchor rule | — |
| E | workspace-manager + `nexus_*` Phase-1+ | — |
| Eval (13) | `n ≤ 2` thin signal | **GAP B:** unconstrained corpus count → saturation |

## 8. GAP B — Gap-reliability / saturation seam

**Problem (`11_honest_review` §3.3):** `"1 direct hits, 20 adjacent"` pool-saturation reads like confidence the model lacks. Eval Dimension 2 (§3.4) requires an **uncapped corpus count** per gap term.

**Required seam (M0.7, T7.3):** providers expose a cheap count query (OpenAlex `meta.count` on a search/`filter` match; S2 match/totals) and `recon_delta` responses gain per-followup:
- `corpus_total` (uncapped works count for the term),
- `saturation_label` (`scant <50 | sparse 50–500 | dense >500` — thresholds configurable, documented).

This converts the naive adjacency reason into a real scarcity signal and feeds `13_evaluation.md` §3.4.

## 9. Non-goals / deferred

- Harness-side scoring/weights (copilot-held governance).
- Fully unattended protocol emission (researcher validation stays the final gate).
- New search providers; no LLM-based labeling in the harness path (determinism invariant).
- Resume/`--resume` wizard (external to M0.x, per `03_lifecycle.md`).