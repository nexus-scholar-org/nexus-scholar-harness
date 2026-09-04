# PRISMA 2020 Literature Screening Flow Report

**Project Workspace:** `uav-cv-precision-agriculture`  
**Review Paradigm:** Empirical Benchmark Synthesis (Deep Learning UAV Segmentation & Edge Inference)  
**Standard:** PRISMA 2020 Statement & Guidelines with Dual-Independent Screening & Third-Party Adjudication  
**Date:** 2026-09-04

---

## 1. Identification Phase
- **Total Records Identified (Federated Search across 5 Providers)**: `1,837`
  - *OpenAlex*: 500
  - *Crossref*: 500
  - *Semantic Scholar*: 639 (Streams A + B)
  - *PubMed*: 122
  - *arXiv*: 76
- **Duplicate Records Removed (Multi-Tier Deduplication)**: `349`
- **Unique Records Retained for Screening**: `1,488`

---

## 2. Title & Abstract Screening Phase (Dual Independent + Adjudication)
- **Total Records Screened**: `1,488`
- **Independent Screener 1 Inclusions**: `786` (52.8% inclusion rate — over-inclusive due to template heuristics)
- **Independent Screener 2 Inclusions**: `112` (7.5% inclusion rate — strict criteria adherence)
- **Inter-Rater Reliability**:
  - Observed Agreement: `53.63%` (798 / 1,488 agreed)
  - Chance Expected Agreement: `47.60%`
  - **Cohen's Kappa ($\kappa$)**: `0.115` (*slight agreement*)
- **Disputes Flagged & Adjudicated**: `690` records (resolved by 6 third-party reviewing agent panels)
- **Reconciled Adjudication Outcome**:
  - Unanimously Agreed Inclusions: `104`
  - Adjudicated Inclusions: `7`
  - **Confirmed Inclusions**: `111`
  - **Provisional Inclusions for Stage 3 Full-Text Verification**: `39`
    - *22 missing-abstract papers* with relevant agricultural UAV titles
    - *17 contested EXC-06 papers* with in-scope segmentation/dataset abstracts lacking explicit numeric metrics
- **Total Records Eligible & Sought for Full-Text Retrieval**: `150` (10.08% overall retrieval rate)
- **Confirmed Records Excluded at Title/Abstract**: `1,338` (89.92%)

---

## 3. Exclusion Reasons Breakdown (Confirmed Excluded $N = 1,338$)

| Exclusion Code | Category / Rule Description | Count | % of Excluded |
| :--- | :--- | :---: | :---: |
| `EXC-03` | Out of Domain (Non-agricultural / satellite remote sensing / general CV) | 487 | 36.40% |
| `EXC-02` | Detection/Classification-Only (No pixel-level segmentation masks) | 292 | 21.82% |
| `EXC-05` | Secondary Literature (Reviews, surveys, perspective papers, non-peer-reviewed) | 281 | 21.00% |
| `EXC-01` | Non-UAV Platform (Satellite, ground-robot, tractor, or lab-bench only) | 156 | 11.66% |
| `EXC-06` | Incomplete / Non-Retrievable Benchmark Data (Confirmed metric-less / out-of-scope) | 92 | 6.88% |
| `EXC-04` | Non-Deep Learning (Conventional indices NDVI/ExG or classic ML without CNN/ViT) | 30 | 2.24% |
| **Total** | **All Confirmed Title/Abstract Exclusions** | **1,338** | **100.0%** |

---

## 4. Full-Text Retrieval & Eligibility Phase
- **Reports Sought for Retrieval**: `150`
- **Reports Successfully Retrieved & Validated**: `138` (**92.0% retrieval yield**)
  - *Full-Text PDF verified (`%PDF` magic bytes)*: 138 / 138
  - *Extracted Structured Markdown AST (`extracted/*.md`)*: 138 / 138
- **Reports Not Retrieved (Paywalls / Inaccessible Repositories)**: `12` (8.0%)
  - *Commercial Edited Book Chapters*: 5 (Springer LNNS/Smart Ag, Elsevier)
  - *Restricted Regional / Society Subscriptions*: 7 (SPIE, ASABE, Inderscience, regional journals)
- **Final Synthesized Review Corpus**: **`138` studies**

---

## 5. Methodological Summary & Final Corpus Lock
By implementing dual-independent screening with third-party adjudication, this systematic review averted a severe false-positive pollution risk (over 670 non-relevant papers eliminated). Through a comprehensive multi-channel retrieval protocol (combining institutional proxy resolution, Gold Open Access harvesting, and direct preprint recovery), the review achieved a **92.0% full-text retrieval yield** (138 out of 150 candidate studies).

The corpus is **formally locked at N = 138 studies**, fully converted into structured Markdown with complete YAML frontmatter, ready for automated vector database indexing, dynamic extraction matrix compilation, and grounded empirical synthesis.
