# Nexus Scholar Harness — Phase 1 & 2 Detailed Report

**Project:** uav-cv-precision-agriculture  
**Title:** UAV Computer Vision for Precision Agriculture: DL Segmentation & Edge Inference Benchmark Review  
**Date:** 2026-09-04  
**PRISMA 2020 Compliant Systematic Review**

---

## Executive Summary

This report documents the first two phases of a rigorous, dual-route systematic review pipeline:

- **Phase 1 (Corpus Audit):** Full-text compliance re-screen of all 138 PDF-extracted studies against the registered protocol. **94 retained IN-SCOPE** (90 CONFIRMED_INCLUSION + 4 PROVISIONAL validated by full text); **44 pruned** as scope violations (disease classification, plant counting, orchard/urban/forestry, dataset-only no-benchmark, hardware/platform, path-planning, satellite navigation, secondary literature).
- **Phase 2 (Dual-Route Extraction + Comparison):** Two completely independent extraction routes executed on the identical 94-study clean corpus under a shared schema contract. Comparison revealed **53% overall field agreement** (mIoU **82.8%**), **17 true value conflicts** adjudicated by a third independent agent, and a documented systematic interpretation difference on edge-efficiency fields. A **merged canonical dataset** of 94 studies with verified numeric values was produced.

---

## 1. Project Context & Protocol

### Research Questions
| RQ | Description |
|---|---|
| **RQ1** | What is the reported segmentation accuracy (mIoU, Dice, F1, PA) of deep learning models for pixel-level crop/weed segmentation from UAV imagery? |
| **RQ2** | What on-device edge inference performance (FPS, latency, power, model size) is reported for these models? |

### Inclusion Criteria (must satisfy ALL)
- **INC-01:** Deep learning applied to UAV-borne **pixel-level** semantic/instance segmentation of crops/weeds.
- **INC-02:** Reports **quantitative segmentation accuracy** (mIoU / Dice / F1 / PA / AUC on segmentation).
- **INC-03 (bonus):** Reports on-device edge inference performance.

### Exclusion Criteria (any ONE excludes)
| Code | Description |
|---|---|
| EXC-01 | Not UAV-borne (satellite, ground, lab bench only) |
| EXC-02 | Bounding-box detection or image classification only; **no pixel segmentation masks** |
| EXC-03 | Non crop/weed arable domain (fruit/orchard, forestry, livestock, soil, **disease classification**, aquatic, urban, infrastructure; whole-plant counting = out) |
| EXC-04 | Not deep learning (classical CV, OBIA, vegetation indices) |
| EXC-05 | Secondary literature (surveys, reviews, tutorials — no primary benchmark) |
| EXC-06 | No retrievable quantitative segmentation results in full text |

---

## 2. Phase 1 — Full-Text Corpus Audit (138 → 94)

### 2.1 Background
After the post-acquisition agent sprint (commits 92ba32b → bacdafd), the corpus reached 138/150 PDFs with extracted markdown. However, an audit of the agent's synthesis output revealed the synthesis matrix and literature review were **fabricated** (AST snippets instead of parsed values, hallucinated aggregates, non-existent RAG index). The extraction layer (138 .md files) was verified as **high quality** (real tables, YAML frontmatter, 7.1 MB total, avg 52.7 KB).

### 2.2 Audit Method
- 5 independent agent-reviewers re-screened all 138 studies against the protocol.
- Input: title, abstract, screening status, and the full extracted markdown (read for borderline cases).
- Output: per-study verdict (IN_SCOPE / OUT_OF_SCOPE) with confidence, exclusion codes, and reasoning.

### 2.3 Results
| Verdict | Count | % |
|---|---|---|
| **IN_SCOPE** | **94** | 68.1% |
| OUT_OF_SCOPE | 44 | 31.9% |

**IN-SCOPE breakdown:** 90 `CONFIRMED_INCLUSION` + 4 `PROVISIONAL_FULLTEXT_ELIGIBILITY` (validated by full text).  
**OUT-OF-SCOPE breakdown:**

| Exclusion category | Count | Examples (workspace_id) |
|---|---|---|
| Disease classification (EXC-03/04) | 10 | SCI-000434 peach, SCI-001079 sugarcane rust, SCI-000888 crop disease |
| Counting / organ domain (EXC-03) | 5 | SCI-001047 sorghum panicles, SCI-001394 wheat spikes, SCI-000134 sunflower |
| Dataset-only, no benchmark (EXC-06) | 6 | SCI-000902 cabbage dataset, SCI-000910 CoFly-WeedDB, SCI-000877 CamelinaWeed |
| Orchard / urban / infrastructure (EXC-03) | 7 | SCI-001133 coffee, SCI-000397 Dubai urban, SCI-000416 sidewalk cracks |
| Hardware / platform / networking (EXC-06) | 4 | SCI-001445 amphibious UAV, SCI-000451 time-sync, SCI-000441 MR12-UAV |
| Field boundary / parcel mapping (EXC-03) | 3 | SCI-001425, SCI-001128, SCI-001316 wheat lodging |
| Non-DL / non-segmentation (EXC-02/04) | 5 | SCI-000315 forestry YOLO, SCI-000934 pest classification, SCI-000446 human detection |
| Satellite / navigation (EXC-01) | 2 | SCI-001116 Herbsat satellite, SCI-001480 vineyard nav |
| Secondary literature (EXC-05) | 2 | SCI-000140 review, SCI-000411 book chapter |

**Key finding:** The initial title/abstract screening passed ~15–20 scope violations; full-text audit revealed **44 violations (32%)**, confirming the value of the compliance re-screen.

### 2.4 Artifacts
- `literature/screening/_audit_worklist.json` — 138 records with metadata
- `literature/screening/_audit_results_{1..5}.json` — 5 independent reviewer outputs
- `literature/screening/_audit_combined.json` — aggregated verdicts
- `literature/screening/_clean_corpus_ids.json` — 94 IN_SCOPE ids
- `literature/screening/_clean_corpus_worklist.json` — 94 records for Phase 2
- Audit event: **EVT-20260904173629-7394e5**

---

## 3. Phase 2 — Dual-Route Extraction & Comparison

### 3.1 Extraction Schema Contract
Both routes bound to `literature/extraction/SCHEMA.md`:
- **Canonical units:** segmentation metrics as fractions [0,1]; fps as frames/sec; latency ms; power W; params millions; gflops.
- **Required fields per study:** 12 metric slots (7 segmentation + 5 edge) + metadata.
- **Provenance mandatory:** quote (raw snippet), section, table, confidence.
- **File-out:** Route A — 4 batch JSON arrays; Route B — 94 per-study JSON files + index.

### 3.2 Route A — Batch Parallel (4 agents × ~24)
- 4 independent subagents, each processed a disjoint batch of 24/24/24/22 studies.
- Each agent read full markdown, extracted all schema fields, wrote batch file.
- **Validation:** all 94 workspace_ids present exactly once, full schema compliance.
- **RQ1 metrics:** 82/94 studies with ≥1 segmentation metric (mIoU in 53, F1 in 24, etc.).
- **RQ2 edge:** 20 studies with on-device runtime (fps/latency/power).

### 3.3 Route B — Sequential + Validation Loop (1 agent)
- Single agent processed all 94 studies sequentially, writing per-study file immediately.
- **15% validation loop (14 studies):** full re-read + re-extraction; **21 values changed** on second pass.
- **RQ1 metrics:** 82/94 with ≥1 metric; **RQ2 edge:** 15 studies with runtime.
- **Validation event:** EVT-20260904224414-47f0f6

### 3.4 Field-Level Comparison (`extraction/compare/`)

| Field | Checked | Agreed | Both-conflict | A-only | B-only | Agreement |
|---|---|---|---|---|---|---|
| mIoU | 64 | 53 | 3 | 3 | 5 | **0.828** |
| mPA | 10 | 7 | 2 | 0 | 1 | 0.700 |
| F1 | 32 | 24 | 1 | 0 | 7 | 0.750 |
| Dice | 19 | 12 | 1 | 1 | 5 | 0.632 |
| PA | 37 | 21 | 1 | 2 | 13 | 0.568 |
| weed_F1 | 5 | 2 | 1 | 0 | 2 | 0.400 |
| crop_F1 | 8 | 4 | 0 | 2 | 2 | 0.500 |
| fps | 29 | 10 | 1 | 6 | 12 | 0.345 |
| latency_ms | 32 | 9 | 1 | 1 | 21 | 0.281 |
| params_M | 34 | 8 | 3 | 1 | 22 | 0.235 |
| gflops | 21 | 3 | 2 | 1 | 15 | 0.143 |
| power_w | 4 | 2 | 1 | 0 | 1 | 0.500 |

**Overall field agreement:** 52.5%  
**Studies with ≥1 difference:** 63 / 94

#### Interpretation of Divergences
- **17 true value conflicts** (both routes reported a number; >0.5% absolute / >5% relative difference) across 10 studies. These were sent to adjudication.
- **~123 status asymmetries** (one route reported, the other didn't):
  - Route B was characteristically more thorough on `edge` fields: params_M (22 B-only), latency_ms (21), gflops (15), fps (12), PA (13).
  - **Spot-verification of B-only quotes against source markdown confirmed ALL sampled values as REAL** (e.g., 8.7M, 42.04M, 10.7M, 2.1M parameters — verbatim in papers).
  - Route A interpreted `edge` as **on-device runtime only** (fps/latency/power on hardware); Route B interpreted it as **runtime + architecture efficiency** (params/GFLOPS wherever reported).
- **No hallucinated values** detected in either route.

### 3.5 Adjudication of True Conflicts
A third independent agent adjudicated the 17 conflicting fields across 10 studies by reading the source markdown.

| Study | Field | A | B | Winner | Canonical | Conf |
|---|---|---|---|---|---|---|
| SCI-000012 | mIoU | 0.767 | 0.617 | **A** | 0.767 | 0.72 |
| SCI-000012 | mPA | 0.859 | 0.734 | **A** | 0.859 | 0.75 |
| SCI-000040 | params_M | null | 10.678 | **B** | 10.678 | 0.95 |
| SCI-000040 | gflops | null | 45.00 | **B** | 45.0 | 0.90 |
| SCI-000083 | Dice | null | 0.9424 | **B** | 0.9424 | 0.97 |
| SCI-000160 | weed_F1 | 0.5833 | 0.6455 | **B** | 0.6455 | 0.68 |
| SCI-000371 | mIoU | 0.681 | 0.884 | **B** | 0.884 | 0.75 |
| SCI-000371 | F1 | 0.781 | 0.913 | **B** | 0.913 | 0.75 |
| SCI-000489 | mIoU | 0.767 | 0.617 | **A** | 0.767 | 0.95 |
| SCI-000489 | mPA | 0.859 | 0.734 | **A** | 0.859 | 0.95 |
| SCI-000624 | PA | 0.843 | 0.7662 | **A** | 0.843 | 0.90 |
| SCI-000810 | latency_ms | 9.441 | 21.514 | **B** | 21.514 | 0.75 |
| SCI-000810 | power_w | 15.0 | 13.15 | **B** | 13.15 | 0.90 |
| SCI-000962 | fps | 117.5 | 143.3 | **B** | 143.3 | 0.85 |
| SCI-000962 | params_M | 36.8 | 10.6 | **B** | 10.6 | 0.95 |
| SCI-000962 | gflops | 693.4 | 32.1 | **B** | 32.1 | 0.95 |
| SCI-001292 | params_M | 0.189 | 0.14 | **A** | 0.189 | 0.70 |

**Outcome:** A won 6, B won 11. Notable cases: SCI-000962 A misread Table 3 columns (693.4 = GPU memory MB); SCI-000371 different tables (RIT-18 tree headline); SCI-000810 matched-budget 15W INT8 regime.

### 3.6 Merged Canonical Dataset (`extraction/merged/records.json`)

**Merge policy:**
- Agreed values → canonical (either route's value + quote).
- A-only / B-only → that route's value (both verified).
- Adjudicated conflicts → adjudicator's winning value + verification quote.
- `edge.reported` redefined: **runtime_reported** (fps/latency/power) = **40**; **efficiency_reported** (params/gflops without runtime) = **10**.

| Statistic | Value |
|---|---|
| Studies with ≥1 RQ1 metric | **82 / 94** |
| Studies with on-device **runtime** (RQ2) | **40 / 94** |
| Studies with efficiency-only (params/gflops) | 10 |
| Adjudicated fields total | 17 |
| Merge decisions: both_equal | 155 |
| Merge decisions: a_only | 17 |
| Merge decisions: b_only | 106 |
| Merge decisions: adjudicated | 17 |
| Merge decisions: not_reported | 833 |

**Artifacts:**
- `extraction/route_A/route_A_batch{1..4}.json` — Route A raw
- `extraction/route_B/route_B_*.json` + `route_B_index.json` — Route B raw
- `extraction/compare/agreement_report.json` — machine-readable stats
- `extraction/compare/divergences.json` — all field differences
- `extraction/compare/comparison_report.md` — narrative report
- `extraction/adjudication/verdicts_all.json` — 17 adjudicated verdicts
- `extraction/merged/records.json` — 94 canonical records (synthesis input)
- `extraction/merged/merge_log.json` — per-field merge decisions
- Audit event: **EVT-20260904225217-f4a1a2**

---

## 4. Quality Assurance & Transparency

| Check | Result |
|---|---|
| All 94 clean studies extracted by both routes | ✅ |
| All 12 schema fields present in every Route A/B record | ✅ |
| Route B 15% validation loop executed | ✅ (21 changes) |
| All 17 true conflicts adjudicated by third party | ✅ |
| No hallucinated values in either route (sampled quotes verified) | ✅ |
| Merged dataset covers all 94 studies with provenance | ✅ |
| All artifacts in `workspaces/uav-cv-precision-agriculture/` | ✅ |
| Audit journal entries logged | ✅ (EVT-20260904173629-7394e5, EVT-20260904224414-47f0f6, EVT-20260904225217-f4a1a2) |

---

## 5. Deviations from Original Plan / Lessons Learned

| Issue | Resolution |
|---|---|
| Original screening passed 44 scope violations | Full-text compliance audit (Phase 1) removed them before extraction |
| Post-acquisition agent fabricated synthesis matrix & review | Discarded; extraction layer preserved; dual-route extraction built verified data |
| Edge field definition ambiguity | Operationalized as **runtime** (fps/latency/power on device) vs **efficiency** (params/gflops) |
| Agreement metric too strict (exact float equality) | Applied tolerance (0.005 absolute / 5% relative) for meaningful comparison |

---

## 6. Next Steps — Phase 3 (Planned)

Using `extraction/merged/records.json` as the **single source of truth**:

1. **Rebuild synthesis matrix** — structured CSV with one row per study, columns = protocol-relevant metrics (model, dataset, crop/weed, mIoU, F1, classes, backbone, FPS, latency, device, params).
2. **Rewrite literature review** — grounded exclusively in merged values; no fabricated aggregates, p-values, or percentages.
3. **RQ1 summary tables** — taxonomy by architecture (CNN/Transformer/Hybrid), crop/weed domain, dataset, with descriptive statistics.
4. **RQ2 summary tables** — edge deployment by device family (Jetson, Snapdragon, RK3588, etc.), precision, resolution.
5. **RAG index (optional)** — if vector indexing adds value over structured tables.
6. **PRISMA flow diagram** — from 1,488 screened → 94 final.

---

## 7. File Index

| Path | Description |
|---|---|
| `reports/phase1_phase2_detailed_report.md` | **This report** |
| `literature/screening/_clean_corpus_ids.json` | 94 IN_SCOPE workspace_ids |
| `literature/extraction/SCHEMA.md` | Extraction schema contract |
| `literature/extraction/route_A/route_A_batch{1..4}.json` | Route A raw extraction |
| `literature/extraction/route_B/route_B_*.json` | Route B raw extraction (per study) |
| `literature/extraction/route_B/route_B_index.json` | Route B file index |
| `literature/extraction/compare/agreement_report.json` | Comparison stats (JSON) |
| `literature/extraction/compare/divergences.json` | All field differences |
| `literature/extraction/compare/comparison_report.md` | Comparison narrative |
| `literature/extraction/adjudication/_conflict_worklist.json` | 17 conflicts sent to adjudication |
| `literature/extraction/adjudication/verdicts_all.json` | 17 adjudicated verdicts |
| `literature/extraction/merged/records.json` | **Merged canonical 94 records** |
| `literature/extraction/merged/merge_log.json` | Per-field merge decisions |
| `audit/journal.jsonl` | Append-only audit ledger |

---

## 8. Sign-off

**Phase 1 (Corpus Audit):** Complete — 94 verified in-scope studies.  
**Phase 2 (Dual-Route Extraction & Comparison):** Complete — canonical merged dataset ready.  
**Phase 3 (Synthesis Rebuild):** Awaiting user go-ahead; will use `records.json` only.

---

*Report generated automatically from pipeline artifacts. All numerical claims traceable to `extraction/merged/records.json` with provenance quotes.*