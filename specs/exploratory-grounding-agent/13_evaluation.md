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

### 3.5 Pool admission gates (P5 pool floor + P2 topical coherence) — implemented 2026-09-13
QEI (3.1) is a **lexical dispersion index that inverts on well-scoped semantic seeds** (multi-domain trial, `16_inception_improvements.md` §E). Admission therefore uses two further gates from `recon/gates.py`, both surfaced on the MCP `recon_distill` reply as `pool` and `purity`:

- **Pool sufficiency (`compute_pool_sufficiency`):** `n_docs ≥ POOL_THIN_FLOOR (12)` ⇒ `sufficient`, else `thin`. Thin pools degrade into fragmentary n-grams and typically lose the `topics` layer (trial: fintech n=8, materials n=6 produced directions like `11 kcal mol` and *no* topics). Thin ⇒ raise `limit` or run a delta before validating directions.
- **Topical coherence (`compute_topic_purity`):** over the distilled `topics` layer, `top3_share = Σ top-3 topic n / Σ all topic n`. `coherent` if `top3_share ≥ TOPIC_COHERENCE_TOP3_SHARE (0.50)`; `fragmented` if topics exist but spread; `indeterminate` when no topics are present (absence of signal, not zero — small/non-OpenAlex pools). Trial calibration: coherent oncology/climate/education pools scored 0.53–0.80.

Both thresholds are module constants (configurable, documented); the wizard prints an advisory `Pool assessment:` line (never aborts — the human stays the gate), and `qei` alone may no longer reject a pool whose purity is `coherent`.

### 3.6 Canonical recon root (P4) — implemented 2026-09-13
Recon state (sessions, content-addressed pools, distilled artifacts) lives under one **CWD-independent root** so the CLI wizard and the MCP server share a cache no matter where each is launched (`16_inception_improvements.md` §F.4):

- `NEXUS_RECON_ROOT` (absolute, resolved) wins when set — the operator escape hatch for pointing the whole pipeline at one root.
- Otherwise the root is `<project-root>/.cache/inception_recon`, where project-root is **walked up from the source tree** (`canonical_recon_root()` in `recon/engine.py`), not `Path.cwd()`. The MCP server imports the same helper from the harness, so launching it from `tools/scholar-agent-kit/` (its MCP `--directory`) no longer scatters sessions under a kit-local `.cache/`.
- `.cache/` is gitignored in every checkout, so no repo pollution regardless of the chosen root.

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
| P2 | Lexicon-bootstrap seam for Loop B | MCP `recon_distill` | M | implemented P3 (lenient `str\|dict`, E2E regression) |
| P2 | School-purity sampled audit (script + judge rubric) | `scripts/` | M | T7.5 |
| P2 | Topical-coherence gate (purity) + pool floor | `recon/gates.py` + MCP | S | implemented P5/P2 (`13_evaluation.md` 3.5) |
| P1 | Direction diversity (≥1/lexical family) + junk filter | `inception.py` | S | implemented P1 (`16_inception_improvements.md` F.2) |
| P6 | Default-lexicon cross-domain breadth (schools/metrics/datasets) | `recon/lexicon.py` | S | implemented P6 (`16_inception_improvements.md` F.6) |
| P3 | ReconBench corpus + runner | `scripts/reconbench/` | L | T7.6 |
| P3 | Full A/B downstream comparison | pipeline integration | L | — |
| P1 | Canonical recon root (`NEXUS_RECON_ROOT`, kit-consistent) | MCP/CLI share one cache | S | implemented P4 (`13_evaluation.md` 3.6) |
| P2 | Headless emission (`--auto-select`/`--direction-id`) + softened wizard exit | `inception.py` | S | T7.8 |

**Non-goal:** measuring "groundedness quality" of human reviewers — the agent's outputs are the object, not the researcher.