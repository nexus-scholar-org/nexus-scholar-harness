# Project Index: AI-Assisted Academic Research Harnesses: Traceability, Trust, Audit and Reproducibility

- **Project Slug**: `ai-research-harnesses-trust`
- **Last Updated**: `2026-09-09 07:28:52 UTC`
- **Project Status**: `ACTIVE`

---

## 📊 Summary Metrics
- **Discovered Papers**: 250
- **Verified Papers**: 239
- **Screened Papers**: 239
- **Full-Text Eligible Candidates**: 58
- **Confirmed Excluded Studies**: 181
- **Downloaded PDFs**: 64
- **Extracted Markdowns**: 64

---

## 🎯 Research Questions
1. **RQ1**: What is the state of the art in academic research and literature review harnesses that integrate LLMs and agentic AI (2023–2026), and what concrete design mechanisms do they implement for execution provenance, audit trails, and process reproducibility?
2. **RQ2**: What evidence-trust and academic-integrity mechanisms (e.g., citation fact-checking, hallucination mitigation, retraction checks, risk-of-bias, and open-science artifact verification) are incorporated into modern AI research harnesses?
3. **RQ3**: How are AI-assisted research harnesses empirically evaluated (benchmarks, ablations, inter-rater reliability, user studies), and what architectural gaps remain for the construction of a novel, trustworthy research infrastructure?

---

## 📂 Project File Catalog

| File / Directory | Description | Last Modified | Status |
| :--- | :--- | :--- | :--- |
| `project.json` | Project manifest, metadata, and research questions | 2026-09-09 07:28 | Active |
| `INDEX.md` | Master project directory and status catalog | 2026-09-09 07:18 | Synced |
| `audit/journal.jsonl` | Append-only provenance event ledger | 2026-09-09 07:28 | Active |
| `literature/raw_search.json` | Raw federated literature search hits | 2026-09-08 08:11 | Discovered |
| `literature/deduped.json` | Deduplicated unique candidate papers | 2026-09-08 08:12 | Deduplicated |
| `literature/verified.json` | Hydrated bibliographic records with DOIs & abstracts | 2026-09-08 08:17 | Verified |
| `literature/included.json` | Screened eligible studies for full-text synthesis | 2026-09-08 22:32 | Included |
| `literature/excluded.json` | Excluded studies with logged decision reasons | 2026-09-08 22:32 | Excluded |
| `literature/conflicts.json` | Complete ledger of inter-rater disputes & adjudications | 2026-09-08 22:32 | Adjudicated |
| `literature/prisma_screening_report.md` | PRISMA flow diagram and systematic screening report | 2026-09-08 22:32 | Generated |
| `literature/prisma_report.json` | Structured JSON companion to PRISMA flow report | 2026-09-08 22:32 | Generated |
| `literature/extraction/merged/records.json` | Canonical merged extraction dataset (per-value provenance quotes) | 2026-09-08 08:51 | Merged |
| `synthesis/synthesis_matrix.csv` | Verified one-row-per-study synthesis matrix | 2026-09-08 09:03 | Generated |
| `synthesis/synthesis_matrix.json` | Machine-readable synthesis matrix | 2026-09-09 01:29 | Generated |
| `synthesis/literature_review.md` | Finalized synthesis: 3 RQ chapters grounded in 510-claim ledger + 95 clusters | 2026-09-09 07:17 | Generated |
| `synthesis/claims.json` | Canonical 510-claim evidence ledger (verbatim-backed, RQ1 166 / RQ2 132 / RQ3 212) | 2026-09-08 23:37 | Generated |
| `synthesis/claims_rq1.json` | RQ1 claims subset (166 claims / 52 studies) | 2026-09-08 23:37 | Generated |
| `synthesis/claims_rq2.json` | RQ2 claims subset (132 claims / 48 studies) | 2026-09-08 23:37 | Generated |
| `synthesis/claims_rq3.json` | RQ3 claims subset (212 claims / 51 studies) | 2026-09-08 23:37 | Generated |
| `synthesis/consensus.json` | 95 semantic consensus clusters (16 high / 7 debates / 37 unresolved / 35 provisional) | 2026-09-08 23:54 | Generated |
| `synthesis/consensus.md` | Human-readable consensus cluster report & cluster descriptions | 2026-09-08 23:54 | Generated |
| `synthesis/method_comparison.md` | RAG vs multi-agent synthesis method comparison & verdict | 2026-09-09 06:35 | Documented |
| `synthesis/rag_baseline/` | Regenerated deterministic RAG baseline (90 claims, 43.3% verified) | 2026-09-09 06:20 | Documented |
| `synthesis/literature_review_draft_v1.md` | Preserved pre-ledger draft (superseded; cites screened-out studies) | 2026-09-09 07:16 | Archived |
| `synthesis/claims.json` | Canonical 510-claim evidence ledger (verbatim-backed, RQ1 166 / RQ2 132 / RQ3 212) | 2026-09-08 23:37 | Generated |
| `synthesis/consensus.json` | 95 semantic consensus clusters (16 high / 7 debates / 37 unresolved / 35 provisional) | 2026-09-08 23:54 | Generated |
| `synthesis/method_comparison.md` | RAG vs multi-agent synthesis method comparison & verdict | 2026-09-09 06:35 | Documented |
| `reports/manuscript_draft.md` | Publishable manuscript draft (abstract→conclusion, 36 corpus-built references) | 2026-09-09 07:28 | Drafted |
| `reports/methodology_report.md` | Formal methodology or audit report | 2026-09-09 07:03 | Audited |
| `reports/screening_consensus_report.md` | Formal methodology or audit report | 2026-09-08 22:25 | Audited |
| `pdfs/` | Downloaded Open Access full-text PDF documents (64 files) | Active | Downloaded |
| `extracted/` | Docling full-text structured Markdown extractions (64 files) | Active | Extracted |

---
*Note: This file is automatically maintained by the `workspace-manager` event logger.*
