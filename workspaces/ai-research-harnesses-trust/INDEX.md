# Project Index: AI-Assisted Academic Research Harnesses: Traceability, Trust, Audit and Reproducibility

- **Project Slug**: `ai-research-harnesses-trust`
- **Last Updated**: `2026-09-09 23:45:33 UTC`
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
| `project.json` | Project manifest, metadata, and research questions | 2026-09-09 23:45 | Active |
| `INDEX.md` | Master project directory and status catalog | 2026-09-09 23:28 | Synced |
| `audit/journal.jsonl` | Append-only provenance event ledger | 2026-09-09 23:45 | Active |
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
| `synthesis/literature_review.md` | Synthesis document & literature review | 2026-09-09 07:16 | In Progress |
| `reports/D3_ADVERSARIAL_AUDIT.md` | Formal methodology or audit report | 2026-09-09 23:29 | Audited |
| `reports/D3_FRAMING_DECISION.md` | Formal methodology or audit report | 2026-09-09 22:20 | Audited |
| `reports/D3_OSF_REGISTRATION_DRAFT.md` | Formal methodology or audit report | 2026-09-09 23:43 | Audited |
| `reports/literature_lessons_and_reading_list.md` | Formal methodology or audit report | 2026-09-09 09:29 | Audited |
| `reports/manuscript_d2.md` | Formal methodology or audit report | 2026-09-09 15:15 | Audited |
| `reports/manuscript_draft.md` | Formal methodology or audit report | 2026-09-09 23:29 | Audited |
| `reports/methodology_report.md` | Formal methodology or audit report | 2026-09-09 23:29 | Audited |
| `reports/PHD_DELIVERABLES_PLAN.md` | Formal methodology or audit report | 2026-09-09 23:29 | Audited |
| `reports/pipeline_engineering_report.md` | Formal methodology or audit report | 2026-09-09 23:44 | Audited |
| `reports/screening_consensus_report.md` | Formal methodology or audit report | 2026-09-08 22:25 | Audited |
| `reports/supplementary_references.md` | Formal methodology or audit report | 2026-09-09 23:20 | Audited |
| `pdfs/` | Downloaded Open Access full-text PDF documents (64 files) | Active | Downloaded |
| `extracted/` | Docling full-text structured Markdown extractions (64 files) | Active | Extracted |

---
*Note: This file is automatically maintained by the `workspace-manager` event logger.*
