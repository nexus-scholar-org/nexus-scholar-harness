# Project Index: UAV Computer Vision for Precision Agriculture: Deep Learning Segmentation & Edge Inference Benchmark Review

- **Project Slug**: `uav-cv-precision-agriculture`
- **Last Updated**: `2026-09-04 10:51:56 UTC`
- **Project Status**: `COMPLETED (PHASE 3 COMPLETE - 100% SYNTHESIZED)`

---

## 📊 Summary Metrics
- **Discovered Papers**: 1837
- **Verified Papers**: 1488
- **Screened Papers**: 1488
- **Full-Text Eligible Candidates Sought**: 150 (111 Confirmed + 39 Provisional Caveats)
- **Confirmed Excluded Studies at Screening**: 1338
- **Reports Successfully Retrieved**: 138 (92.0% retrieval yield)
- **Reports Not Retrieved (Paywall/Restricted)**: 12 (8.0%)
- **Extracted Full-Text Markdowns**: 138 documents (in `extracted/`)
- **Final Locked Corpus Size**: 138 studies
- **Vector DB Semantic Chunks**: 6,707 AST chunks (`all-MiniLM-L6-v2`, in `chroma_db/`)
- **Citation Knowledge Network**: 145 nodes, 140 edges, normalized PageRank (`literature/knowledge_graph.json`)
- **Protocol Extraction Matrix**: 138 studies extracted across 7 dimensions (`literature/synthesis_matrix.json`)
- **Systematic Literature Review**: Completed publication-grade manuscript (`synthesis/literature_review.md`)

---

## 🎯 Research Questions
1. **RQ1**: What is the comparative segmentation performance (mIoU, F1-score) of CNNs, Transformers, and Hybrid architectures on agricultural UAV crop-weed imagery, specifically in paired intra-study benchmarks?
2. **RQ2**: How do edge hardware constraints (thermal design power, compute capacity in TOPS) and execution configurations (quantization precision, input resolution) impact real-time inference throughput (FPS, latency) for UAV segmentation models?

---

## 📂 Project File Catalog

| File / Directory | Description | Last Modified | Status |
| :--- | :--- | :--- | :--- |
| `project.json` | Project manifest, metadata, and research questions | 2026-09-04 12:31 | Active |
| `INDEX.md` | Master project directory and status catalog | 2026-09-04 12:31 | Synced |
| `audit/journal.jsonl` | Append-only provenance event ledger (30 events) | 2026-09-04 12:27 | Complete |
| `literature/raw_search.json` | Raw federated literature search hits | 2026-09-03 22:14 | Discovered |
| `literature/deduped.json` | Deduplicated unique candidate papers | 2026-09-03 22:16 | Deduplicated |
| `literature/verified.json` | Hydrated bibliographic records with DOIs & abstracts | 2026-09-04 01:48 | Verified |
| `literature/included.json` | Screened eligible studies for full-text synthesis (150 studies) | 2026-09-04 01:48 | Included |
| `literature/excluded.json` | Excluded studies with logged decision reasons (1338 studies) | 2026-09-04 00:42 | Excluded |
| `literature/references.bib` | Curated BibTeX database with standardized citation keys (150 entries) | 2026-09-04 12:14 | Curated |
| `literature/knowledge_graph.json` | Node-link citation network topology + normalized PageRank | 2026-09-04 12:21 | Generated |
| `literature/knowledge_graph.html` | Interactive PyVis force-directed network visualization | 2026-09-04 12:21 | Generated |
| `literature/synthesis_matrix.json` | 7-dimension dynamic extraction matrix (JSON, 138 studies) | 2026-09-04 12:23 | Extracted |
| `literature/synthesis_matrix.csv` | 7-dimension dynamic extraction matrix (CSV, 138 studies) | 2026-09-04 12:23 | Extracted |
| `literature/synthesis_matrix.md` | 7-dimension dynamic extraction matrix (Markdown, 138 studies) | 2026-09-04 12:23 | Extracted |
| `literature/screening/dual_screening_reliability_report.md` | Inter-rater reliability audit report | 2026-09-04 00:42 | Audited |
| `literature/screening/adjudicated_caveats.json` | Provisional caveat papers tracked for Stage 3 verification | 2026-09-04 00:42 | Provisioned |
| `literature/conflicts.json` | Complete ledger of inter-rater disputes & adjudications | 2026-09-04 00:42 | Adjudicated |
| `literature/conflict_adjudication_log.md` | Traceable adjudication narrative & dispute ledger | 2026-09-04 00:42 | Adjudicated |
| `literature/prisma_screening_report.md` | PRISMA flow diagram and systematic screening report | 2026-09-04 10:51 | Updated |
| `literature/prisma_report.json` | Structured JSON companion to PRISMA flow report | 2026-09-04 10:51 | Updated |
| `reports/fulltext_acquisition_and_corpus_finalization_report.md` | Phase 2 Full-Text Acquisition & Corpus Finalization Report | 2026-09-04 10:51 | Complete |
| `reports/harness_and_kits_architectural_retrospective_and_improvement_plan.md` | Architectural Retrospective & Roadmap Report | 2026-09-04 11:00 | Complete |
| `pdfs/` | Acquired Open Access & Institutional full-text PDF documents (138 files) | Active | Locked |
| `extracted/` | PyMuPDF structured full-text Markdown extractions with YAML frontmatter (138 files) | Active | Locked |
| `chroma_db/` | ChromaDB persistent dense vector store (6,707 AST chunks) | Active | Indexed |
| `synthesis/literature_review.md` | Systematic review manuscript with grounded claim-level citations | 2026-09-04 12:27 | Complete |
| `synthesis/synthesis_matrix.csv` | Comparative synthesis matrix (CSV mirror) | 2026-09-04 12:23 | Complete |
| `synthesis/synthesis_matrix.json` | Comparative synthesis matrix (JSON mirror) | 2026-09-04 12:23 | Complete |
| `synthesis/synthesis_matrix.md` | Comparative synthesis matrix (Markdown mirror) | 2026-09-04 12:23 | Complete |

---
*Note: This file is automatically maintained by the `workspace-manager` event logger.*
