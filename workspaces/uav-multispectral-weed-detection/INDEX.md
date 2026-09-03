# INDEX: uav-multispectral-weed-detection

**Title**: Lightweight Multispectral UAV Vision Architecture for Real-Time Weed Detection and Precision Targeted Spraying
**Slug**: `uav-multispectral-weed-detection`
**Protocol**: `proto-20260902-uav-multispectral-weed-detection-v2`
**Paradigm**: Design Science
**Created**: 2026-09-01T17:17:00+00:00

---

## Research Questions

| ID | Question | Target Facet | Evidence Type |
|----|----------|--------------|---------------|
| RQ1 | Does a dual-branch spatial-spectral cross-attention architecture (SSFNet) outperform unimodal RGB and channel-stacked early-fusion multi-band baselines in weed-vs-crop segmentation accuracy (mIoU, weed IoU, weed F1) on open agricultural UAV datasets? | spectral_fusion_accuracy | Quantitative Benchmark |
| RQ2 | Can the multispectral fusion architecture sustain the real-time targeted-spraying threshold (>=30 FPS on NVIDIA Jetson-class edge) while keeping parameter count under 0.6M, and what is the measured latency (ms), FLOPs, and throughput trade-off against accuracy? | computational_efficiency_edge | Latency & Resource Profiling |
| RQ3 | How robust is the multispectral weed segmentation model to domain shifts from lighting variation, crop phenological stage, and sensor band calibration when evaluated across multiple agricultural benchmark datasets? | cross_dataset_robustness | Generalization Evaluation |

---

## Current Stats

| Metric | Count |
|--------|-------|
| Papers Discovered | 116 |
| Papers Deduplicated | 116 |
| Papers Verified | 116 |
| Papers Screened (LLM) | 116 |
| Papers Included | 26 |
| Papers Excluded | 90 |
| Papers Conflicts | 0 |
| PDFs Downloaded | 25 |
| Extracted Documents | 25 |
| RQ3 Supplemental Catalogued | 2 |
| Screening Conflicts Adjudicated | 49 |
| Inter-Annotator Kappa (keyword vs LLM) | 0.115 |
| Vector Chunks | 1185 |
| Paper Count (extracted) | 25 |
| Bibliography Entries | 25 |
| Matrix Rows (synthesis) | 25 |
| Citation-Graph Nodes | 20 |

---

## Directory Structure

```
workspaces/uav-multispectral-weed-detection/
├── INDEX.md                 # This file
├── project.json             # Project manifest
├── intent.json              # Socratic LLM intent packet
├── protocol.json            # Canonical research protocol
├── SCREENING_CRITERIA.md    # Inclusion/exclusion criteria
├── audit/
│   └── journal.jsonl        # Event ledger (append-only)
├── literature/
│   ├── raw_search.json      # 116 papers (federated search)
│   ├── deduped.json         # 116 unique papers
│   ├── verified.json        # 116 verified papers
│   ├── llm_included.json    # 26 papers (final/adjudicated)
│   ├── llm_excluded.json    # 90 papers (final/adjudicated)
│   ├── llm_conflicts.json   # 0 (resolved)
│   ├── conflicts.json       # 49 keyword conflicts (tentative 21 IN / 28 EX)
│   ├── conflict_adjudication_log.md  # per-paper keep/exclude rationale + kappa
│   ├── rq3_supplemental_register.md  # +3 RQ3 domain-shift sources (1 ingested, 2 catalogued)
│   ├── prisma_screening_report.md
│   ├── references.bib               # 25-entry BibTeX (keys = stem, UTF-8 verified)
│   ├── synthesis_matrix.csv/.json/.md # 25-study × 8-dim protocol matrix (68% filled)
│   ├── data_quality_report.md       # task-type classification, gaps, attribution checks
│   └── knowledge_graph.html/.json   # citation network + PageRank (25 nodes / 9 edges, 100% corpus parity)
├── pdfs/                    # 25 matched PDFs
├── extracted/               # 25 extracted documents
├── rag/
│   └── chroma_db/           # Vector index (1185 chunks, sentence-transformers)
├── synthesis/
│   ├── literature_review.md  # Grounded RQ1-RQ3 narrative w/ atomic citation tokens
│   ├── evidence_matrix.md   # Curated per-paper mIoU/params/FPS (RQ2 insights)
│   └── evidence_matrix_raw.json # raw regex extraction (unreliable, flagged)
└── exports/                 # Exported deliverables (EXPORTS.md manifest)
```

---

## Event Log (Recent)

| Timestamp | Action | Agent | Status |
|-----------|--------|-------|--------|
| 2026-09-02T12:33:00+00:00 | WORKSPACE_INITIALIZED | workspace-manager | SUCCESS |
| 2026-09-02T12:35:00+00:00 | DISCOVERY_SEARCH | scholar-search-kit | SUCCESS |
| 2026-09-02T12:35:30+00:00 | DEDUPLICATION | scholar-search-kit | SUCCESS |
| 2026-09-02T12:36:00+00:00 | VERIFICATION | scholar-search-kit | SUCCESS |
| 2026-09-02T12:36:30+00:00 | SCREENING (keyword) | scholar-search-kit | SUCCESS |
| 2026-09-02T12:40:00+00:00 | SCREENING (LLM batch) | sub-agents (x8) | SUCCESS |
| 2026-09-02T12:45:00+00:00 | CONFLICT_ADJUDICATION | human-in-the-loop | SUCCESS |
| 2026-09-02T13:40:00+00:00 | PDF_DOWNLOAD + EXTRACTION | scholar-pdf-kit / PyMuPDF | SUCCESS |
| 2026-09-02T14:15:00+00:00 | PDF_INGEST (univ. subscription) | human-in-the-loop | SUCCESS |
| 2026-09-02T14:30:00+00:00 | PDF+EXTRACT (ASVLB-Net from PMC HTML) | pymupdf / BeautifulSoup | SUCCESS |
| 2026-09-02T15:00:00+00:00 | CONTEXT-ONLY_REMOVAL (3 files) | agent | SUCCESS |
| 2026-09-02T15:05:00+00:00 | CONFLICT_ADJUDICATION_LOG + KAPPA (κ=0.115, N=116) | agent | SUCCESS |
| 2026-09-02T15:10:00+00:00 | BARRERO_FULLTEXT_UNAVAILABLE (closed access, documented) | agent | INFO |
| 2026-09-02T15:20:00+00:00 | RQ3_SEARCH (+Gao ingested; Zuo, Weyler catalogued) | agent | SUCCESS |
| 2026-09-02T15:30:00+00:00 | EVIDENCE_MATRIX_BUILT (24 curated rows, manual verify) | agent | SUCCESS |
| 2026-09-02T15:40:00+00:00 | RAG_INDEX_BUILT (25 docs, 2516 chunks) | scholar-rag-kit | SUCCESS |
| 2026-09-02T16:00:00+00:00 | SYNTHESIS_GENERATED (R1-R3 grounded, 16 claims) | agent + scholar-rag-kit | SUCCESS |
| 2026-09-02T17:00:00+00:00 | PROCEEDINGS_CLEANUP (contaminated dumps deleted + re-extracted) | agent | SUCCESS |
| 2026-09-02T17:30:00+00:00 | REFERENCES_BIB_BUILT (25 entries, stem keys) | scholar-bib-kit | SUCCESS |
| 2026-09-02T18:00:00+00:00 | RAG_REINDEX (25 docs → 1185 chunks) | scholar-rag-kit | SUCCESS |
| 2026-09-02T19:00:00+00:00 | MATRIX_BUILT (25-study × 8-dim synthesis matrix) | scholar-rag-kit + agent | SUCCESS |
| 2026-09-02T19:30:00+00:00 | SYNTHESIS_REGEN (tool entailment per RQ: 0/6, 1/5, 2/4) | scholar-rag-kit | SUCCESS |
| 2026-09-02T20:00:00+00:00 | DATA_QUALITY_PASS (non-seg re-classification, Barrero gap, SSRN attribution) | agent | SUCCESS |
| 2026-09-02T20:30:00+00:00 | CITATION_GRAPH_BUILT (20 nodes / 8 edges, PageRank) | scholar-graph-kit | SUCCESS |
| 2026-09-02T21:00:00+00:00 | EXPORTS (10 deliverables + manifest) | agent | SUCCESS |
| 2026-09-03T04:47:00+00:00 | CITATION_TOKENS_VERIFIED (16/16 atomic tokens resolve to ChromaDB chunks) | agent | SUCCESS |
| 2026-09-03T04:49:00+00:00 | CITATION_GRAPH_ENRICHED (25 nodes / 9 edges, 100% corpus parity) | scholar-graph-kit + agent | SUCCESS |

---

## Screening Criteria Summary

- **Inclusion**: 4 criteria (empirical segmentation results, multispectral imagery, UAV/edge context, open benchmark dataset)
- **Exclusion**: 5 criteria (wrong outcome, satellite-scale, RGB-only, non-empirical, non-English)
- **Verification**: Retraction check, COI/funding audit, reproducibility check required
- **Minimum Trust Score**: 5.0

---

*Last updated: 2026-09-02T21:00:00+00:00*
