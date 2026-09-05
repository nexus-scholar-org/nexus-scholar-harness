# Project Index: UAV Computer Vision for Precision Agriculture: Deep Learning Segmentation & Edge Inference Benchmark Review

- **Project Slug**: `uav-cv-precision-agriculture`
- **Last Updated**: `2026-09-05 19:03:21 UTC`
- **Project Status**: `ACTIVE`

---

## 📊 Summary Metrics
- **Discovered Papers**: 1837
- **Verified Papers**: 1488
- **Screened Papers**: 1488
- **Full-Text Eligible Candidates**: 150 (111 Confirmed + 39 Provisional Caveats)
- **Confirmed Excluded Studies**: 1338
- **Downloaded PDFs**: 138
- **Extracted Markdowns**: 138
- **Post-Audit Clean Corpus**: 94 studies (44 scope violations removed)
- **Merged Canonical Records**: 94 (82 with ≥1 RQ1 segmentation metric; 40 with on-device runtime; 15 true embedded edge)

---

## 🎯 Research Questions
1. **RQ1**: What is the comparative segmentation performance (mIoU, F1-score) of CNNs, Transformers, and Hybrid architectures on agricultural UAV crop-weed imagery, specifically in paired intra-study benchmarks?
2. **RQ2**: How do edge hardware constraints (thermal design power, compute capacity in TOPS) and execution configurations (quantization precision, input resolution) impact real-time inference throughput (FPS, latency) for UAV segmentation models?

---

## 📂 Project File Catalog

| File / Directory | Description | Last Modified | Status |
| :--- | :--- | :--- | :--- |
| `project.json` | Project manifest, metadata, and research questions | 2026-09-05 19:03 | Active |
| `INDEX.md` | Master project directory and status catalog | 2026-09-05 19:03 | Synced |
| `audit/journal.jsonl` | Append-only provenance event ledger | 2026-09-05 19:03 | Active |
| `literature/raw_search.json` | Raw federated literature search hits | 2026-09-03 22:14 | Discovered |
| `literature/deduped.json` | Deduplicated unique candidate papers | 2026-09-03 22:16 | Deduplicated |
| `literature/verified.json` | Hydrated bibliographic records with DOIs & abstracts | 2026-09-04 01:48 | Verified |
| `literature/included.json` | Screened eligible studies for full-text synthesis | 2026-09-04 01:48 | Included |
| `literature/excluded.json` | Excluded studies with logged decision reasons | 2026-09-04 00:42 | Excluded |
| `literature/screening/dual_screening_reliability_report.md` | Inter-rater reliability audit report | 2026-09-04 00:42 | Audited |
| `literature/screening/adjudicated_caveats.json` | Provisional caveat papers tracked for Stage 3 verification | 2026-09-04 00:42 | Provisioned |
| `literature/conflicts.json` | Complete ledger of inter-rater disputes & adjudications | 2026-09-04 00:42 | Adjudicated |
| `literature/conflict_adjudication_log.md` | Traceable adjudication narrative & dispute ledger | 2026-09-04 00:42 | Adjudicated |
| `literature/prisma_screening_report.md` | PRISMA flow diagram and systematic screening report | 2026-09-04 10:52 | Generated |
| `literature/prisma_report.json` | Structured JSON companion to PRISMA flow report | 2026-09-04 10:51 | Generated |
| `literature/screening/_clean_corpus_ids.json` | Post-audit clean corpus study ids | 2026-09-04 17:33 | Audited |
| `literature/screening/_audit_combined.json` | Full-text compliance audit verdicts | 2026-09-04 17:33 | Audited |
| `literature/extraction/SCHEMA.md` | Dual-route extraction schema contract | 2026-09-04 17:37 | Contracted |
| `literature/extraction/route_A/route_A_batch1.json` | Route A batch extractions | 2026-09-04 18:02 | Extracted |
| `literature/extraction/route_B/route_B_index.json` | Route B per-study extractions + index | 2026-09-04 22:29 | Extracted |
| `literature/extraction/compare/comparison_report.md` | Route A vs Route B comparison report | 2026-09-04 22:46 | Compared |
| `literature/extraction/adjudication/verdicts_all.json` | Adjudicated extraction conflicts | 2026-09-04 22:51 | Adjudicated |
| `literature/extraction/merged/records.json` | Canonical merged extraction dataset (per-value provenance quotes) | 2026-09-04 22:52 | Merged |
| `synthesis/synthesis_matrix.csv` | Verified one-row-per-study synthesis matrix | 2026-09-05 12:39 | Generated |
| `synthesis/synthesis_matrix.json` | Machine-readable synthesis matrix | 2026-09-05 12:39 | Generated |
| `synthesis/synthesis_stats.json` | Reproducible RQ1/RQ2 descriptive statistics | 2026-09-05 12:39 | Generated |
| `synthesis/build_synthesis.py` | Reproducible matrix + stats generator | 2026-09-05 12:39 | Generated |
| `synthesis/literature_review.md` | Synthesis document & literature review | 2026-09-05 12:44 | Final |
| `reports/academic_methodology_review_and_phase2_directives.md` | Formal methodology or audit report | 2026-09-04 00:50 | Audited |
| `reports/discovery_remediation_report_20260903_231630.md` | Formal methodology or audit report | 2026-09-03 22:16 | Audited |
| `reports/discovery_report_20260903_230800.md` | Formal methodology or audit report | 2026-09-03 22:08 | Audited |
| `reports/dual_screening_synchronization_report_20260904_014500.md` | Formal methodology or audit report | 2026-09-04 00:42 | Audited |
| `reports/fulltext_acquisition_and_corpus_finalization_report.md` | Formal methodology or audit report | 2026-09-04 10:52 | Audited |
| `reports/harness_and_kits_architectural_retrospective_and_improvement_plan.md` | Formal methodology or audit report | 2026-09-04 10:56 | Audited |
| `reports/phase1_phase2_detailed_report.md` | Formal methodology or audit report | 2026-09-04 23:01 | Audited |
| `reports/screening_audit_report_20260903_233500.md` | Formal methodology or audit report | 2026-09-03 22:33 | Audited |
| `pdfs/` | Downloaded Open Access full-text PDF documents (138 files) | Active | Downloaded |
| `extracted/` | Docling full-text structured Markdown extractions (138 files) | Active | Extracted |

---
*Note: This file is automatically maintained by the `workspace-manager` event logger.*
