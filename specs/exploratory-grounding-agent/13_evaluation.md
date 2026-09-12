# 13 — Evaluation Framework (ReconBench + measurable gates)

> **Status:** Proposed measurement contract. The cheap gates are M0.7 implementation candidates (see `08_milestones.md` M0.7 stub); ReconBench is a later benchmark effort.
> **Date:** 2026-09-13 · **Origin:** distilled from `temp_brainstorming.md` (retired) and aligned with `11_honest_review.md` (P1–P3).
> **Extends:** `11_honest_review.md`, `08_milestones.md` (M0.7), `12_semantic_grounding.md` (topics layer enables Topic Jaccard).

## 1. Why evaluation is unusual here

The grounding agent operates **before ground truth exists**. Phase-1 screening can be scored with precision/recall against labeled pools; the recon loop instead bridges *fuzzy curiosity → frozen protocol*. Evaluation therefore splits into **four measurable dimensions**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        EVALUATION TAXONOMY                             │
├──────────────────────────┬─────────────────────────────────────────────┤
│ 1. Epistemic Integrity   │ Provenance & zero-hallucination discipline  │
│ 2. Reconnaissance Signal │ Anti-echo, clustering precision, gap truth  │
│ 3. Downstream Yield      │ Phase-1 search hit rate & screening noise   │
│ 4. Autonomous Navigation │ Agent efficiency, Pareto tradeoff, escapes  │
└────────────────────────────────────────────────────────────────────────┘
```

## 2. Dimension 1 — Epistemic integrity & anchor discipline

| Metric | Formula | Target | Status |
| :--- | :--- | :--- | :--- |
| Anchor Provenance Rate (APR) | (concepts with ≥1 pool DOI) / total protocol concepts | **100%** (hard invariant) | ✅ **Already enforced** (M0.3 DoD-3; `test_inception_grounded`). Promote to a CI gate. |
| Phantom Entity Rate | invented datasets/metrics / total in protocol | **0%** | Partial — entities only emit from pool evidence (distiller anchor filter). Audit spot-Checks (PDF/abstract cross-check). |
| Citation Veracity (DOI liveness) | resolvable authentic DOIs / proposed anchors | **100%** | Not yet measured. `scholar-verify-kit` `/papers` resolution covers this at Phase-4; add a recon-time spot check (M0.7 optional). |

## 3. Dimension 2 — Reconnaissance & taxonomy quality

### 3.1 Query Echo Index (QEI)
Whether distilled vocabulary repeats the user's prompt instead of revealing the field:

$$\text{QEI} = \frac{|\text{Top-}K\text{ taxonomy terms} \cap \text{stemmed query tokens}|}{K} \qquad \text{target } \le 0.3$$

- **Cheapest high-value gate** (M0.7 T7.x): compute in `distiller.py` from pool `cache_key`-side query text + terms; assert in tests (≥50% of top-10 non-echo).
- Directly addresses `11_honest_review` §3.1 (`deep 20 / learning 19`).

### 3.2 Topic enrichment / Novelty recall
M0.6 topics layer vs human-authored review taxonomy on the same subject → **Topic Jaccard** over subfield/domain labels. Requires the ReconBench corpus (§6).

### 3.3 School cluster purity
Heuristic schools ("transformer" → power grids) measured by sampled audit (LLM-as-judge or manual), 50 papers/school: `Purity(S) = |correctly-matched ∩ S| / |S|`. Scripted sample + judge rubric; not continuous.

### 3.4 Gap reliability (true gaps vs pool artifacts)
`n ≤ 2` in the 25-doc pool may be query-phrasing artifact, not scarcity. Validation = **unconstrained corpus count** for the gap term (`OpenAlex meta.count`, S2 total) — a new seam (GAP B in `14_agent_loops.md`, M0.7). Reporting target: saturation label `scant | sparse | dense` per followup.

## 4. Dimension 3 — Downstream protocol viability (A/B)

| Metric | Definition | Hypothesis (grounded vs cold) |
| :--- | :--- | :--- |
| Zero-hit query rate | executions returning 0 Phase-1 hits | grounded → **0%** |
| Candidate signal-to-noise | included / total retrieved | grounded **significantly higher** |
| Screening agreement (κ) | Cohen's/Fleiss' at `agent_screen.py` | higher (anchored criteria = less ambiguity) |
| Protocol churn | revisions during Phases 1–4 | minimized |

Full A/B needs real workspace runs → ReconBench (L effort) or targeted 3-topic pilot (M effort).

## 5. Dimension 4 — Autonomous navigation

- **Pareto optimality of direction selection:** craft a pool with saturated (n>15, crowded), frontier (n∈[2,4], datasets+metrics present), and dead-end (n=0, unanchored) directions; measure frequency the agent picks the frontier.
- **Budget efficiency:** probes-to-convergence (≤3), tokens before genesis, and **escape handling** — impossible prompt (e.g. "quantum computing on blockchain for crop rotation") → clean zero-anchor abort, not hallucinated IntentPacket. Escape is partially enforced today (empty-pool hard abort, M0.3).

## 6. ReconBench (proposed benchmark harness)

1. **Corpus:** 30–50 published SLRs (Cochrane medical, ACM/IEEE SE, environmental science). Input = the review's original research question as the *vague seed prompt*; ground truth = published search strings, benchmark datasets, inclusion criteria, final bibliography.
2. **Runner** (repeated per SLR):
   ```
   recon_context = run_autonomous_grounding(seed_prompt)   # probe → distill → adaptive → protocol
   assert anchor discipline (APR == 100%)
   concept_recall  = |gold_search_terms ∩ (concepts ∪ synonyms)| / |gold|
   dataset_recall  = |gold_benchmarks ∩ terms.datasets.keys()| / |gold|
   qei, probe_count, steps_to_freeze
   ```
3. **Post-process:** aggregate recalls/APR/QEI across the corpus; flag systematic zero-hit and saturated directions.
4. **Status:** corpus assembly is the blocker (manual curation); runner is harness code (M0.7+ / post-PR).

## 7. Priority gates (implementable, cheapest first)

| # | Gate | Where | Effort | M0.7 task |
| :--- | :--- | :--- | :--- | :--- |
| P1 | APR CI gate (assert all protocol concepts anchored) | CI + `test_inception_grounded` | S | T7.1 |
| P1 | QEI in distiller + test gate (≥50% non-echo top-10) | `recon/distiller.py` | S | T7.2 |
| P1 | Gap-reliability saturation seam (uncapped count + label) | `recon/adaptive.py` + providers | S/M | T7.3 |
| P2 | Lexicon-bootstrap seam for Loop B | MCP `recon_distill` | M | T7.4 |
| P2 | School-purity sampled audit (script + judge rubric) | `scripts/` | M | T7.5 |
| P3 | ReconBench corpus + runner | `scripts/reconbench/` | L | T7.6 |
| P3 | Full A/B downstream comparison | pipeline integration | L | — |
| P1 | Canonical recon root (`NEXUS_RECON_ROOT`, kit-consistent) | MCP/CLI share one cache | S | T7.7 |
| P2 | Headless emission (`--auto-select`/`--direction-id`) + softened wizard exit | `inception.py` | S | T7.8 |

**Non-goal:** measuring "groundedness quality" of human reviewers — the agent's outputs are the object, not the researcher.