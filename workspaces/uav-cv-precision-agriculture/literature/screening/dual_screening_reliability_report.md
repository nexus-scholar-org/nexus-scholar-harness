# Dual-Screening Reliability Report

**Project:** UAV Computer Vision for Precision Agriculture — Deep Learning Segmentation & Edge Inference Benchmark Review
**Workspace:** `workspaces/uav-cv-precision-agriculture`
**Procedure:** PRISMA 2020 title/abstract screening with an independent second screener and third-party adjudication of disagreements.
**Date:** 2026-09-04

---

## 1. Operating context

1,488 records (`literature/verified.json`) were screened in 60 batches of 25. Two independent screeners scored every paper; a third-party adjudicator then resolved every disagreement. Two prior screening passes had produced unreliable results, which is why this dual-review was commissioned. All batches were screened through the agent-in-the-loop file handoff (`.agents/.../agent_screen.py`) with one `batch_XXX.json` per batch, a `_decisions.json` file (screener 1), and a `_decisions_screener2.json` file (screener 2).

---

## 2. Inter-rater agreement (screener 1 vs. screener 2)

Decision labels: `INCLUDE` / `EXCLUDE` per paper.

### Confusion matrix (S1 rows × S2 columns), n = 1,488

| | S2 = INCLUDE | S2 = EXCLUDE | S1 row total |
|---|---|---|---|
| **S1 = INCLUDE** | 104 | 682 | 786 |
| **S1 = EXCLUDE** | 8 | 694 | 702 |
| **S2 col total** | 112 | 1376 | 1488 |

### Metrics
- Observed agreement: **0.5363** (798 / 1,488)
- Expected agreement (chance): **0.4760**
- **Cohen's kappa: 0.1150** — “slight” agreement (Landis & Koch), barely above chance.
- Marginal include rates: S1 = 52.8%, S2 = 7.5% (large classifier-offset bias).

The extraordinarily low agreement and the extreme imbalance (758 disagreeing papers vs. only 798 agreeing) indicate the two screeners are not measuring the same thing. Screening decisions of this magnitude require independent reconciliation, not trust in either set.

---

## 3. Discrepancy characterisation

Disagreement is **strongly asymmetric**:

- **682 records: S1 = INCLUDE, S2 = EXCLUDE.** Dominant S2 codes: EXC-03 (out of domain, 422), EXC-02 (detection/classification-only, 214), EXC-05 (secondary lit, 57), EXC-04 (non-DL, 44), EXC-06 (no results, 39), EXC-01 (non-UAV, 39).
- **8 records: S1 = EXCLUDE, S2 = INCLUDE.** S1 wrongly dropped in-scope studies under EXC-01/06. In adjudication, 5 benchmark studies were overturned to INCLUDE (SemiWeedNet SCI-000092, AgriJetsonBench SCI-000810, SCI-000084, SCI-000487, SCI-001088), while 3 dataset-release papers (cabbage dataset SCI-000902, CoFly-WeedDB SCI-000910, camelina SCI-000877) were classified under the contested EXC-06 dataset tail for Stage 3 full-text verification.

### Why the low kappa is not a code bug
Screener 1’s reasoning strings were near-identical boilerplate (“Empirical study evaluating UAV segmentation with RQ1 benchmark metrics”) regardless of actual paper content, and its decisions included in-scope outliers such as RL multi-UAV exploration (000011), forestry LiDAR (000019), and book chapters without benchmarks (000398, 000403). Screener 2 was consistently strict, producing individually-reasoned verdicts but occasionally over-excluding in-scope work on the wrong code (e.g., 000092, 000810).

---

## 4. Third-party adjudication

All **690 disputed records** were resolved by six independent reviewing agents (groups 1–6, files `_adjudication_resolved_group_1..6.json`), each adjudicating a disjoint subset strictly from the abstract, with both prior screeners’ reasoning supplied only as input (never as override). Output schema included adjudication-specific reasoning and final codes. Records not in the disputed set were left untouched (a scope over-run in group 5 was detected and corrected — 9 non-disputed records removed).

### Adjudication summary (n = 690)
- 683 EXCLUDE, 7 INCLUDE.
- Bulk exclusions are solid: EXC-03 out-of-domain (n = 433), EXC-02 detection/classification-only (n = 205).
- EXC-06 “no retrievable results” used on 39 exclusions: 22 truly have no abstract in the batch; **17 have an abstract but the adjudicator judged no solid segmentation metric** (see §6).

---

## 5. Final reconciled set (n = 1,488)

| Set | INCLUDE | EXCLUDE |
|---|---|---|
| Screener 1 | 786 | 702 |
| Screener 2 | 112 | 1376 |
| **Final reconciled** | **111** | **1377** |

Composition of final INCLUDE: **104** agreed-INCLUDE/INCLUDE by both screeners + **7** adjudicated-INCLUDE. Zero records left unresolved.

Decision rule: if both screeners agreed, that final verdict stands; if they disagreed, the third-party adjudicator’s verdict is final.

---

## 6. Caveats and suggested follow-up

1. **EXC-06 contested tail (n = 17):** papers with an abstract and an in-scope topic cue, excluded solely because the abstract lacks an explicit numeric segmentation metric. Examples include real-time ENet crop-row segmentation (SCI-000575), UAV adaptive path-planning semantic segmentation (SCI-000002), OverFOMO crop/weed + path planning (SCI-000666), and grass-weed detection in wheat (SCI-000650). If the review wishes to favour these method papers, a targeted re-adjudication under a more lenient standard could raise the include count slightly.
2. **Missing-abstract papers (n = 22):** excluded conservatively under EXC-06. These are candidates for full-text (PDF) verification rather than title/abstract screening.
3. **Generated artifacts** (kept in `literature/screening/` for audit): `_adjudication_review...` group files, `_final_reconciled_include.txt`, and analysis scripts `_agreement.py`, `_disagreement_analysis.py`, `_audit_adjudication.py`, `_quantify_exc06.py`, `_reconcile.py`.

---

## 7. Audit trail

- First screening (S1): pre-existing 60 `batch_*_decisions.json` files.
- Second screening (S2): 60 `batch_*_decisions_screener2.json` files created and validated (all 1,488 covered; zero parse/coverage problems).
- Adjudication: 6 `_adjudication_resolved_group_*.json` files (690 records).
- Reconciliation: `_reconcile.py` → final 111 / 1377.
- Events logged to `audit/journal.jsonl`: `EVT-20260904000014-8b2b9f` (Dual screening) and `EVT-20260904001202-c50766` (Adjudication).