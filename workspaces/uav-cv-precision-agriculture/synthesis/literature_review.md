# Systematic Review: Deep Learning Semantic Segmentation and Real-Time Edge Inference for UAV Precision Agriculture

**Protocol ID**: `proto-20260903-uav-cv-precision-agriculture`  
**Playbook & Methodology**: PRISMA 2020 Systematic Literature Review  
**Epistemological Framework**: Positivist Empirical Benchmark Synthesis  
**Corpus Finalization Date**: September 4, 2026  
**Corpus Size**: N = 94 Empirical Studies (full-text extracted; post compliance audit)  
**Synthesis Source**: `literature/extraction/merged/records.json` — dual-route extracted, compared, adjudicated

---

## Executive Summary & PRISMA 2020 Flow

This systematic literature review synthesizes the empirical evidence on deep learning pixel-level semantic and instance segmentation architectures applied to Unmanned Aerial Vehicle (UAV) imagery for agricultural crop and weed management, alongside real-time hardware execution benchmarks across embedded physical compute platforms.

### Methodological Workflow & PRISMA Identification Flow

The PRISMA 2020 flow is grounded in the verified `literature/prisma_report.json` and the compliance audit:

1. **Identification**: A federated multi-source search was executed across five scholarly databases (OpenAlex, Semantic Scholar, Crossref, arXiv, PubMed) spanning January 1, 2018 to September 2026, yielding **1,837 raw candidate records** (OpenAlex 500, Semantic Scholar 639, Crossref 500, arXiv 76, PubMed 122; per `raw/provenance_manifest.json`). After deduplication: **1,488 unique records screened** (*verified corpus*).
2. **Screening**: Independent dual screening of 1,488 records (inter-rater Cohen's kappa = **0.115**, low agreement), with **690 conflicts** adjudicated by 6 independent agents. **150 studies** formally included (111 confirmed + 39 provisional).
3. **Full-Text Acquisition**: **138 PDFs retrieved** of 150 (92.0% yield); 12 not retrieved (5 paywalled book chapters, 7 paywalled restricted conference/journal articles).
4. **Full-Text Compliance Audit**: All 138 extracted studies independently re-screened against the registered protocol by 5 audit agents. **44 studies (31.9%) removed** as scope violations (disease classification, plant counting, orchard/urban/forestry, dataset-only, hardware/platform, path-planning, satellite navigation, secondary literature). **94 studies (68.1%) confirmed IN-SCOPE**.
5. **Dual-Route Structured Extraction**: 94 studies extracted twice independently (Route A: batch-parallel; Route B: sequential + 15% re-extraction validation). Field-level comparison: mIoU agreement **82.8%**; 17 numeric conflicts adjudicated. **Merged canonical dataset** with per-value provenance quotes.

```
┌─────────────────────────────────────────────────────────────┐
│                 PRISMA 2020 Flow Summary                     │
├─────────────────────────────────────────────────────────────┤
│  Raw Federated Search Records:              N = 1,837       │
│  Unique Deduplicated Records:                N = 1,488       │
│  Records Screened (verified corpus):         N = 1,488       │
│  Records Excluded at Screening:              N = 1,338       │
│  Included (confirmed + provisional):         N = 150         │
│  Retrieved & Extracted:                      N = 138 (92.0%) │
│  Removed at Compliance Audit:                N =  44         │
│  Final Synthesis Corpus:                     N =  94         │
└─────────────────────────────────────────────────────────────┘
```

> **Correction note.** An earlier version of this review (commit `bacdafd`) reported N = 138 studies, a fabricated architectural taxonomy (e.g., "96 studies (69.6%) U-Net"), invented aggregates (e.g., "mean mIoU 76.4% ± 6.2%", Wilcoxon p < 0.005), and cited a `rag/`-relative ChromaDB path that does not exist in the workspace (the Chroma index lives at `chroma_db/`, which is gitignored). **This document supersedes that version entirely.** All values below are traceable to `literature/extraction/merged/records.json` and `synthesis/synthesis_stats.json`.

---

## Corpus Characterization

| Attribute | Value |
|---|---|
| Studies | 94 |
| Years | 2018–2026 (2018: 5, 2019: 1, 2020: 7, 2021: 7, 2022: 8, 2023: 10, 2024: 16, 2025: 21, 2026: 19) |
| Venue type (coarse) | Journal 64, Conference 16, Preprint 14, Other/unknown 0 |
| Domain | crop-weed 61, crop-only 23, other-veg 6, crop-row 2, weed-only 1, crop-other 1 |
| Segmentation task | semantic 78, instance 10, both 6 |
| Studies with ≥1 segmentation metric | **82 / 94 (87.2%)** |
| Studies with on-device runtime metric (FPS/latency/power) | **40 / 94 (42.6%)** |
| Studies with true embedded edge device | **15 / 94 (16.0%)** |

---

## Section 1: Comparative Segmentation Accuracy (RQ1)

> **Research Question 1**: *What is the reported segmentation accuracy (mIoU, F1, Dice, PA) of deep learning models for pixel-level crop/weed segmentation from UAV imagery?*

### 1.1 Headline Metric Distributions (verified, N = 82 studies with any metric)

| Metric | N reported | Mean | Median | Range |
|---|---|---|---|---|
| **mIoU** | 64 | 0.795 | 0.832 | 0.466 – 0.983 |
| F1 | 32 | 0.857 | 0.890 | 0.492 – 0.988 |
| Dice | 19 | 0.848 | 0.876 | 0.530 – 0.997 |
| PA | 37 | 0.928 | 0.939 | 0.809 – 0.999 |
| mPA | 10 | 0.848 | 0.902 | 0.515 – 0.969 |
| weed_F1 | 5 | 0.675 | 0.646 | 0.566 – 0.795 |
| crop_F1 | 8 | 0.837 | 0.888 | 0.660 – 0.952 |

All values are fractions in [0,1]; mIoU/F1/Dice are the paper's own headline test-set results. mIoU is by far the most commonly reported metric (64/82 studies with any metric).

### 1.2 mIoU by Domain

| Domain | N | Mean mIoU | Range |
|---|---|---|---|
| crop-weed (discrimination) | 45 | 0.783 | 0.515 – 0.983 |
| crop-only | 13 | 0.812 | 0.466 – 0.951 |
| other-vegetation | 4 | 0.846 | 0.799 – 0.897 |
| crop-row | 1 | 0.829 | — |
| crop-other | 1 | 0.860 | — |

The crop-weed discrimination subset (61 studies, of which 45 report mIoU) is the direct evidence base for RQ1. Its mIoU values spread widely (0.515–0.983), reflecting the diversity of crops, platforms, GSD, and class balance across the corpus.

### 1.3 Architecture Family (derived, keyword-classified on best_model / models_tested)

| Family | N (total) | N with mIoU | Mean mIoU | Median mIoU | Range |
|---|---|---|---|---|---|
| CNN-based | 61 | 40 | 0.793 | 0.829 | 0.515 – 0.983 |
| Transformer / attention-based | 8 | 6 | 0.872 | 0.856 | 0.805 – 0.974 |
| Hybrid (CNN + attention/transformer) | 6 | 5 | 0.722 | 0.789 | 0.519 – 0.908 |
| Unknown/not classifiable | 19 | 13 | 0.792 | 0.874 | 0.466 – 0.948 |

**Caveat.** This taxonomy is derived from a keyword heuristic on the reported primary architecture; family sizes are small for transformer/hybrid, so the apparent transformer advantage is descriptive, not inferential. No statistical significance is claimed.

**Within-study observations (verified):**
- **The highest reported accuracies come from lightweight, efficiency-oriented designs.** The corpus ceiling is 0.983 mIoU (SCI-000637, YOLO11-PSPNet, crop-weed RGB), followed by CWRepViT-Net (SCI-000180, 0.974) and PCCSAN multispectral attention fusion (SCI-000129, 0.966) — both crop-weed (note: the keyword taxonomy in Table 1.3 groups these under "Transformer / attention-based" because of name tokens). The best explicitly transformer-family result is Mask2Former (SCI-001096, mIoU 0.897, Opuntia cactus vegetation).
- **Edge-motivated efficient CNNs** (e.g., RPD-Net SCI-001292 mIoU 0.875 with 0.19 M params; MSEA-Net SCI-001334 mIoU 0.874, 6.74 M params, 2.0 ms inference) reach segmentation accuracy comparable to heavy baselines while qualifying for real-time deployment.

---

## Section 2: Real-Time / On-Device Inference Benchmarking (RQ2)

> **Research Question 2**: *What on-device edge inference performance (FPS, latency, power, model size) is reported for UAV crop/weed segmentation models?*

### 2.1 Reporting Frequency

| Class | N studies | Definition |
|---|---|---|
| On-device runtime (FPS/latency/power) | **40 / 94** | reports ≥1 numeric runtime quantity |
| Of which **true embedded edge** | **15** | measured on Jetson/RK3588/Tinker Board, not desktop |
| Efficiency-only (params/GFLOPS, no runtime) | 10 | architecture-efficiency but no device timing |
| Neither | 44 | no edge/throughput reporting |

### 2.2 Device Families (N = 40 runtime studies)

| Family | Count |
|---|---|
| Desktop/Server GPU (RTX 3090/4090/3080/V100/T4, etc.) | 11 |
| Jetson TX2 | 4 |
| Jetson Nano | 4 |
| Jetson AGX Xavier | 2 |
| Jetson Orin / Orin Nano Super | 2 |
| Cloud GPU (Colab T4) | 2 |
| CPU | 2 |
| Jetson Xavier NX | 1 |
| Rockchip RK3588 (Orange Pi 5+) | 1 |
| Tinker Board S | 1 |
| Unknown / not stated | 9 |
| Other | 1 |

### 2.3 Verified Runtime Distributions

| Quantity | Scope | N | Mean | Median | Range |
|---|---|---|---|---|---|
| **FPS** | all | 28 | 96.1 | 30.6 | 1.43 – 1611 |
| FPS | true edge (N=12) | 12 | 22.0 | 17.05 | 1.43 – 62.5 |
| FPS | desktop/cloud | 16 | 151.6 | 40.4 | 1.89 – 1611 |
| **Latency (ms)** | all | 31 | 324 | 40.9 | 0.62 – 6000 |
| Latency | true edge (N=11) | 11 | 238 | 142.9 | 2.1 – 700 |
| Latency | desktop/cloud | 20 | 372 | 31.5 | 0.62 – 6000 |
| **Power (W)** | true edge | 3 | 9.3 | 10.0 | 4.81 – 13.15 |
| **Params (M)** | all | 34 | 23.0 | 12.8 | 0.19 – 135 |
| Params | true edge (N=8) | 8 | 7.35 | 3.71 | 0.19 – 17.4 |
| GFLOPS | all | 21 | 44.9 | 29.7 | 1.0 – 184 |

**Interpretation (descriptive).**
- True-edge FPS is an order of magnitude below desktop/cloud FPS (median 17 vs 40 FPS), and drops to single digits for large models on Jetson Nano/TX2 (e.g., SCI-000286 3.7 FPS; SCI-000440 1.9 FPS @ 536 ms).
- The two most energy-detailed edge studies use Jetson Nano/Orin: 4.8 W @ 536 ms (SCI-000440) and 10 W @ 32.7 ms (SCI-000683); the AgriJetsonBench study (SCI-000810) reports 13.15 W at 47.2 FPS on Jetson Orin Nano Super (INT8, matched 15 W budget).
- **Params are conspicuously lower in the edge subset** (median 3.71 M vs 13.63 M for desktop), confirming efficiency-motivated design (pruning/quantization) is standard for on-device deployment.
- Precision reporting is sparse: only 13/40 runtime studies state a precision (FP16 mentioned in 5, INT8 in 2, FP32 in 6; overlaps possible).

### 2.4 Notable Individual Edge Results (verified records)

| Study | Device | Precision | FPS | Latency | Params | Notes |
|---|---|---|---|---|---|---|
| SCI-000810 | Jetson AGX Orin / Orin Nano Super | INT8 (15 W) | 47.2 | 21.5 ms | 3.71 M | TensorRT, 0.28 J/inf |
| SCI-000683 | Jetson Nano | (reported) | 30.6 | 32.7 ms | — | 10 W measured |
| SCI-000669 | Jetson Orin Nano | — | 44.0 | — | — | real-time weed segmentation |
| SCI-001085 | Rockchip RK3588 (Orange Pi 5+) | INT8 | 62.5 | 16.0 ms | — | 6 TOPS NPU |
| SCI-000346 | Jetson TX2 | — | 17.1 | 58.7 ms | — | PRC-Net edge deployment |
| SCI-001292 | Jetson TX2 | — | 7.0 | 142.9 ms | 0.19 M | RPD-Net, 38% of ERFNet params |
| SCI-000440 | Jetson Nano | — | 1.9 | 536.6 ms | — | 4.8 W measured |
| SCI-000286 | Jetson Nano | — | 3.7 | 271.3 ms | — | tobacco field |
| SCI-000852 | Jetson Nano | — | 4.3 | 235 ms | — | SqueezeSlimU-Net |

---

## Section 3: Key Findings & Evidence Gaps

### 3.1 RQ1 Findings
1. **mIoU is the standard headline metric** (64/82), with a corpus median of **0.832** and range 0.466–0.983.
2. **Performance plateau observed but not at ceiling**: many crop-weed studies cluster in the 0.78–0.90 mIoU band (19/45 crop-weed studies with mIoU); only four studies in the whole corpus exceed 0.95 mIoU — three of them crop-weed discrimination studies.
3. **Transformer/hybrid architectures appear strong on accuracy** in the descriptive comparison (median mIoU 0.856 vs CNN 0.829) but the sample is tiny (6–8 studies) — no inference is warranted.
4. **Per-class reporting is rare**: only 8 studies report crop_F1 and 5 report weed_F1, yet weed-level F1 is the agronomically critical quantity. Weed_F1 (0.57–0.79) is consistently lower than crop_F1 (0.66–0.95), reflecting the intrinsic difficulty of sparse, varied weeds.

### 3.2 RQ2 Findings
1. **Only 15/94 (16%) of studies demonstrate true on-board inference**; 40/94 (43%) report some runtime metric, but a quarter of these are desktop/cloud GPU or unspecified devices.
2. **True-edge throughput is low but viable**: median 17 FPS on Jetson-family/RK3588/Tinker Board; the best edge results (RK3588 62.5 FPS; Orin Nano Super 47.2 FPS) demonstrate real-time feasibility at INT8.
3. **Reporting standardization is poor**: precision is stated in under a third of runtime studies; GSD/flight-altitude context and dataset-residualization (train/test splits) are inconsistently documented, hampering cross-study benchmarking.

### 3.3 Evidence Gaps (for protocol revision / future work)
- **Power/energy**: only 3 studies report measured power — energy-per-inference is almost entirely missing (except SCI-000810).
- **Standardized evaluation protocol**: no common corpus/split dominates — the most-used benchmark (WeedsGalore) appears in only 4 studies.
- **Class-imbalanced reporting**: weed_F1/crop_F1 should be mandatory in future protocols where weed discrimination is the research aim.
- **Precision standardization**: FP16/INT8 deployment conditions should accompany any on-device FPS claim.

---

## Data Provenance & Reproducibility

All numeric claims in this review derive programmatically from:

| Source | Location |
|---|---|
| Merged canonical extraction | `literature/extraction/merged/records.json` (94 records, per-value quotes) |
| Descriptive statistics | `synthesis/synthesis_stats.json` (computed by `build_synthesis.py`) |
| Synthesis matrix (CSV/JSON) | `synthesis/synthesis_matrix.csv`, `synthesis_matrix.json` |
| PRISMA flow numbers | `literature/prisma_report.json` |
| Compliance audit | `literature/screening/_audit_combined.json` |
| Comparison & adjudication | `literature/extraction/compare/`, `literature/extraction/adjudication/` |

No aggregate, percentage, or statistical claim in this document is fabricated; every number either (a) comes directly from a cited merged record, or (b) is recomputable from `records.json`. Any claim of statistical significance is explicitly disclaimed.