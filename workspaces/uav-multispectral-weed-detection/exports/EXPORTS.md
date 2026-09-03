# Exported Deliverables — uav-multispectral-weed-detection

**Project:** Lightweight Multispectral UAV Vision Architecture for Real-Time Weed Detection and Precision Targeted Spraying
**Protocol:** `proto-20260902-uav-multispectral-weed-detection-v2`
**Paradigm:** Design Science
**Export date:** 2026-09-02 (post full pipeline completion)

This directory contains the final, portable research deliverables produced by the
Nexus Scholar Suite pipeline. Each file is a self-contained artifact intended for
downstream writing, submission, or external review.

| File | Source (canonical path) | Description |
|---|---|---|
| `references.bib` | `literature/references.bib` | 25-entry BibTeX database (keys = lowercased stems; UTF-8 author names verified) |
| `synthesis_matrix.csv` | `literature/synthesis_matrix.csv` | Cross-study matrix of 8 protocol dimensions across all 25 papers (68% populated with verified values) |
| `literature_review.md` | `synthesis/literature_review.md` | Grounded RQ1–RQ3 narrative with atomic citation tokens |
| `evidence_matrix.md` | `synthesis/evidence_matrix.md` | Manually-verified per-paper headline metrics (mIoU/params/FPS) |
| `knowledge_graph.html` | `literature/knowledge_graph.html` | Interactive PyVis citation-network map (20 nodes, 8 edges) |
| `knowledge_graph.json` | `literature/knowledge_graph.json` | Node-link topology + normalized PageRank scores |
| `data_quality_report.md` | `literature/data_quality_report.md` | Task-type classification, availability gaps, SSRN attribution, chunk reconciliation |
| `prisma_screening_report.md` | `literature/prisma_screening_report.md` | PRISMA screening summary (116 screened → 26 included) |
| `conflict_adjudication_log.md` | `literature/conflict_adjudication_log.md` | Per-paper keep/exclude rationale + κ=0.115 |
| `rq3_supplemental_register.md` | `literature/rq3_supplemental_register.md` | +3 RQ3 domain-shift sources (Gao ingested; Zuo, Weyler catalogued) |

## Key numbers reported in exports

- Corpus: 25 extracted full-text documents; RAG index `uav_msi_weeds` = 1185 chunks
- Evidence matrix: 24 curated rows (manually verified)
- Synthesis matrix: 25 studies × 8 dimensions
- Citation graph: 20 nodes / 8 edges (5 of 25 DOIs unresolvable in OpenAlex — AECE-2026, PrecAg-2017, ASNJ-Full+Text, RS-16-03538, M2GARSS-2022)
- Top PageRank hub: Gao (10.1016/j.eswa.2023.122980), then WeedsGalore (10.1109/wacv61041.2025.00467)

## Provenance

All exports are copies of files under the canonical workspace paths shown above.
The authoritative (git-tracked) versions live at those canonical locations; this
directory is a snapshot for external distribution.
