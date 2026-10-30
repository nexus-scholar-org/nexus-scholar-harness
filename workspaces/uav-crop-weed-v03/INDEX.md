# Project Index: Reliability and Generalization in UAV Crop-Weed Mapping - Protocol v0.3 Amendment Workspace

- **Project Slug**: `uav-crop-weed-v03`
- **Last Updated**: `2026-10-30 20:19:12 UTC`
- **Project Status**: `ACTIVE`

---

## 📊 Summary Metrics
- **Discovered Papers**: 0 (pilot screening used the calibration corpus, not this manifest's `stats`)
- **Verified Papers**: 0
- **Downloaded PDFs**: 0
- **Extracted Markdowns**: 0

## 🔎 Screening Status (v0.3 pilot)
- **Status**: `FINAL_AGENT_UNCONFIRMED` — `HumanConfirmation@1` unsigned
- **Screened**: 14,150 (14,413 identified − 263 duplicates)
- **Included**: 644 · **Excluded**: 13,506 (of which 346 *not retrieved*, DEV-01)
- **Frozen instrument**: protocol `f81e6c58…f755`, criteria `9ae1f97d…b86f`
- **Console/UI view**: `literature/screening/MANIFEST.json` + 283 derived
  `batch_NNN.json` / `batch_NNN_decisions.json` (`DERIVED_EXPORT`, 2026-10-30).
  Read-only projection of the final decisions for the console and Research UI;
  not a new screening run and not a Contract-v1 generation
  (`accepted_parent_artifact: false`). See `AMENDMENTS.md` §v0.3 canonical
  screening export.

---

## 🎯 Research Questions
1. **RQ1**: How do UAV crop-weed mapping studies define and evaluate reliability under spectral degradation, sensor differences, and temporal shift?
2. **RQ2**: Which datasets, sensors, dates, fields, and split units support the reported generalization claims?
3. **RQ3**: How are uncertainty, calibration, missing evidence, and failed transfer reported?
4. **RQ4**: Which evidence gaps remain after separating dataset diversity, model mechanisms, and demonstrated external validation?

---

## 📂 Project File Catalog

| File / Directory | Description | Last Modified | Status |
| :--- | :--- | :--- | :--- |
| `project.json` | Project manifest, metadata, and research questions | 2026-10-29 12:30 | Active |
| `INDEX.md` | Master project directory and status catalog | 2026-10-29 12:30 | Synced |
| `audit/journal.jsonl` | Append-only provenance event ledger | 2026-10-29 12:30 | Active |
| `literature/included.json` | Screened eligible studies for full-text synthesis | 2026-10-29 12:29 | Included |
| `literature/excluded.json` | Excluded studies with logged decision reasons | 2026-10-29 12:29 | Excluded |
| `literature/prisma_screening_report.md` | PRISMA flow diagram and systematic screening report | 2026-10-29 12:29 | Generated |
| `literature/prisma_report.json` | Structured JSON companion to PRISMA flow report | 2026-10-29 12:29 | Generated |
| `literature/included.json` | 644 included records (document + screening) | 2026-10-29 12:29 | Final (agent, unconfirmed) |
| `literature/excluded.json` | 13,506 excluded records with per-row provenance | 2026-10-29 12:29 | Final (agent, unconfirmed) |
| `literature/screening/final_decisions.json` | All 14,150 final screening decisions | 2026-10-29 12:29 | Final (agent, unconfirmed) |
| `literature/screening/summary.json` | Counts, lanes, reasons, deviations | 2026-10-29 12:29 | Final (agent, unconfirmed) |
| `literature/screening/MANIFEST.json` | Derived 283-batch console/UI projection (`DERIVED_EXPORT`) | 2026-10-30 20:19 | Derived view |
| `literature/screening/batch_NNN.json` + `batch_NNN_decisions.json` | Per-batch papers and final decisions for the console/UI | 2026-10-30 20:19 | Derived view |
| `_drivers/v03_canonical_screening_export.py` | Deterministic driver that regenerates the derived batch layout | 2026-10-30 20:19 | Driver |
| `literature/prisma_report.json` | PRISMA counts including *not retrieved* | 2026-10-29 12:29 | Final (agent, unconfirmed) |
| `literature/prisma_screening_report.md` | PRISMA-ScR screening report + Mermaid flow | 2026-10-29 12:29 | Final (agent, unconfirmed) |
| `synthesis/literature_review.md` | Synthesis document & literature review | 2026-10-28 13:30 | In Progress |

---
*Note: This file is automatically maintained by the `workspace-manager` event logger.*
