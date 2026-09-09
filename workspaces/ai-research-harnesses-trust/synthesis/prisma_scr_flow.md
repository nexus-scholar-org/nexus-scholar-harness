# PRISMA-ScR Flow of Information — AI Research Harnesses & Trust Review (D3)

Prepared from pipeline artifacts: `literature/raw_search.json`, `literature/deduped.json`,
`literature/included.json`, `literature/excluded.json`, `literature/prisma_screening_report.md`,
`phase4/*.json`, and `audit/journal.jsonl`. Working draft for the D3 manuscript Methods
(PRISMA-ScR item flow; living review Version 1.0, corpus finalized 2026-09-09).

## 1. Flow counts (pipeline, 2026-09-09)

| Stage | Count | Source field |
|---|---|---|
| Records identified (5 providers: OpenAlex, Semantic Scholar, Crossref, PubMed, arXiv) | 250 | `raw_search.json` (50 per provider) |
| duplicate records removed (multi-tier dedup: DOI + normalized title) | 11 | 250 − 239 |
| Records screened (title + abstract, 4 independent AI screeners) | 239 | `deduped.json` |
| Records excluded at title/abstract (systematic exclusion rule) | 181 | `excluded.json` |
| Records included (review corpus) | 58 | `included.json` |
| Full-text PDFs downloaded and validated | 64 | `pdfs/` (OA harvest) |
| Included studies contributing verified claims | 57 | `synthesis/claims.json` (493 full-text + 17 abstract-only claims) |
| Included studies with empty abstract (claim-void) | 1 | SCI-000147 |
| Phase-4 certified (retraction 48 / open-science / COI 47 / risk-of-bias attestation) | 47 | `phase4/*` |

Notes:
- **bioRxiv-track** records are captured through PubMed/Crossref indexing (e.g., SCI-000082
  was returned by the pubmed endpoint), not a dedicated bioRxiv query.
- The older `prisma_screening_report.md` begins its count at 239 (post-dedup); the 250→11→239
  identification row above is the complete PRISMA-2020-compatible accounting.
- Records excluded at title/abstract = 239 − 58 = 181, all via the systematic exclusion rule.

## 2. Title/abstract screening reliability (validity disclosure)

| Metric | Value |
|---|---|
| Screeners | 4 independent AI screeners |
| Batches | 12 (agent-in-the-loop)
| Fleiss' κ | 0.408 (fair, Landis–Koch) |
| Majority-rule resolutions | 213 (≥3 of 4) |
| Two-vs-two deadlocks escalated | 26 (senior adjudicator) |
| Final | 58 included / 181 excluded |

## 3. Trust verification coverage (Phase-4, four streams)

| Stream | Coverage | Fields empty at v1.0 |
|---|---|---|
| Retraction status (OpenAlex/Crossref) | 48 studies checked; 0 flagged; `crossref_update_events: {}` | update-to supersession |
| Open-science artifact scan (DAS/CAS) | repo link present 16; both public link 7; any DAS/CAS statement 32; DAS explicitly unavailable 5 | — |
| Conflict-of-interest audit | 47 studies scanned: 5 industry-equipment ties, 4 declared-no-conflict, 1 academic-or-public, 37 no formal statement | — |
| Risk-of-bias attestation | PROBAST/QUADAS-2 deterministic scoring per `scholar-verify-kit` | — |

## 4. PRISMA-ScR item mapping (manuscript)

- **Title/abstract**: early-evidence living scoping review, Version 1.0
- **Background/rationale**: §1, §5.1
- **Objectives**: RQ1–RQ3 (`protocol.json` research_questions)
- **Protocol & registration**: `protocol.json` (hash-pinned, compiled fingerprint
  `sha256:9646d5ec6902c8f7687dfcb6568e473e1e01b78f666b20b74ec901f9703bf55c`); not externally
  registered at v1.0 (OSF planned) — disclosed in §7
- **Eligibility criteria**: protocol `screening_criteria` (INC/EXC); `SCREENING_CRITERIA.md`
- **Information sources**: §3.1, supplementary search-log (`literature/search_log_v1.0.json`)
- **Search**: concept-and-synonym Boolean strings (protocol `search_strategy`)
- **Selection, data extraction, quality appraisal**: §3.2–§3.5
- **Synthesis/results**: §4; consensus map `synthesis/consensus.json`
- **Risk of bias within studies**: PROBAST/QUADAS-2 (see §3.3, `phase4/`)
- **Living review**: §3.8 protocol

## 5. Flow diagram figure

Rendered vector figure: `synthesis/figures/fig_prisma_scr_flow.svg` (text-serializable).
IDENTIFICATION → SCREENING → ELIGIBILITY → INCLUDED per section 1; supersession and version
advance handled by the §3.8 living protocol rather than the static flow.