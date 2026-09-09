# D1 Submission Bundle Manifest

Version 2026-09-09. Bundle root: `workspaces/uav-cv-precision-agriculture/`. Upload order follows journal requirements; figures and tables are embedded in the draft AND included as standalone files.

## Core submission files
- [ ] `synthesis/d1_manuscript_draft.md` — manuscript (convert to journal template / DOCX-PDF at submission)
- [ ] `synthesis/figures/fig1_prisma_2020_flow.png` (+ .pdf) — PRISMA 2020 flow diagram
- [ ] `synthesis/figures/fig2_year_distribution.png` (+ .pdf) — publication year distribution
- [ ] `synthesis/figures/fig3_family_distribution.png` (+ .pdf) — architecture families
- [ ] `synthesis/figures/fig4_dataset_reuse.png` (+ .pdf) — dataset reuse
- [ ] `synthesis/figures/fig5_edge_throughput.png` (+ .pdf) — embedded true-edge throughput
- [ ] `synthesis/figures/fig6_ro_bias_heatmap.png` (+ .pdf) — risk-of-bias heatmap
- [ ] `synthesis/d1_tables.md` — Tables 1–3 (metric reporting, embedded cohort, RoB)
- [ ] `synthesis/d1_references.md` — 94-study audited bibliography (APA)
- [ ] `synthesis/cover_letter.md` — cover letter (target: Computers and Electronics in Agriculture; date to fill)
- [ ] `synthesis/osf_registration_draft.md` — preregistration (submit to OSF before submission)

## Supporting methods / transparency artifacts
- [ ] `protocol.json` + fingerprint `sha256:e1bbcb791d9108b2277fa468982f59cbdc611a66288556c5f4812fde34f1b077` in Data Availability
- [ ] `synthesis/prisma_2020_flow.md` — flow counts + kappa + resolution + reconciliation
- [ ] `synthesis/provisional_resolution.md` — 39-caveat resolution ledger
- [ ] `synthesis/fulltext_claim_audit.md` — 354 claim-level checks, corrections table
- [ ] `synthesis/rq1_anchor_audit.md` — anchor-row verification
- [ ] `synthesis/rq1_benchmark_tables.md`, `synthesis/rq2_edge_tables.md` — per-dataset and runtime tables
- [ ] `synthesis/rq1_metric_reporting.md` — metric/ambiguity reporting supplement
- [ ] `phase4/` JSON/MD trust artifacts (DAS/CAS, COI, RoB, trust_consensus.json)

## Data (journal Data Availability / OSF file store, optionally zipped)
- [ ] `literature/included.json` (150 records), `literature/references.bib` (150 entries)
- [ ] `literature/extraction/merged/records.json` + `extracted/*.md` full-text extractions
- [ ] `audit/journal.jsonl` — append-only event ledger

## Not for submission (internal/working)
- Scripts: `scripts/*.py` (figures, tables, read-through fixes, manifest builders)
- `literature/raw_search.json`, `literature/deduped.json`, `literature/verified.json` (raw pipeline)
- `synthesis/fulltext_audit/` per-study reports (kept for reviewer evidence if requested)
- `rag/chroma_db/`, `workspaces/**/pdfs/`, `lib/` (heavy/generated; gitignored)

## Target journal
- **Primary:** Computers and Electronics in Agriculture (Elsevier) — top agri-informatics venue, corpus's leading journal, accepts systematic reviews, values deployment + trust evidence.
- **Plan B (OA):** Smart Agricultural Technology (Elsevier) if open access / faster decisions preferred; fallback Remote Sensing (MDPI) for maximum in-corpus readership overlap.

## Required human actions before upload
- [ ] Fill date in `synthesis/cover_letter.md`
- [ ] Confirm department/lab brain optionality: affiliation currently "University of Oum El Bouaghi, Algeria"
- [ ] Submit OSF registration and record returned ID in manuscript Data Availability + cover letter
- [ ] Render manuscript to journal template; verify figure PNG resolution ≥ 300 dpi (PDF vectors provided)