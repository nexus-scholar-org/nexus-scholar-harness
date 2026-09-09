# PRISMA 2020 Flow of Information - UAV CV Precision Agriculture Review

Prepared from pipeline artifacts: `literature/prisma_report.json`, `literature/prisma_screening_report.md`,
`phase4/trust_consensus*.json`, `project.json`, and `synthesis/provisional_resolution.md`.
Working draft for the D1 manuscript Methods/Results (PRISMA 2020 item-flow).

## 1. Flow counts (pipeline, 2026-09-04)

| Stage | Count | Source field |
|---|---|---|
| Records identified (5 providers: OpenAlex, Crossref, Semantic Scholar, PubMed, arXiv) | 1,837 | total_identified |
| Duplicates removed (multi-tier dedup) | 349 | duplicates_removed |
| Records screened (title + abstract, dual independent) | 1,488 | records_screened |
| Records excluded at title/abstract | 1,338 | records_excluded |
| Records included at title/abstract (111 confirmed + 39 provisional) | 150 | records_included |
| Reports sought for retrieval (full-text) | 150 | reports_sought_for_retrieval |
| Reports not retrieved (paywalls: 5 book chapters, 7 restricted journals) | 12 | reports_not_retrieved |
| Full-text reports retrieved and validated (%PDF magic bytes) | 138 | reports_retrieved (92.0%) |
| Full-text corpus assessed | 138 | final_fulltext_corpus_assessed |

Corpus locked at N=138 converted to structured extraction Markdown (see `prisma_screening_report.md`).

## 2. Title/abstract screening reliability (validity disclosure)

| Metric | Value | Interpretation |
|---|---|---|
| Screener 1 inclusion rate | 786/1,488 (52.8%) | over-inclusive (template heuristics) |
| Screener 2 inclusion rate | 112/1,488 (7.5%) | strict criteria adherence |
| Observed agreement | 53.63% | |
| Cohen kappa | 0.115 | slight agreement |
| Disputes flagged + adjudicated | 690 (6 third-party panels) | |

This low inter-rater reliability is disclosed and mitigated by full third-party adjudication of every dispute;
it also motivated the EXC-06 caveat stream below. Report kappa in the manuscript with this framing.

## 3. Stage-3 eligibility resolution for the 39 provisional caveats (CAVEAT_EXC06)

Recorded in `synthesis/provisional_resolution.md` (2026-09-09, pipeline files untouched):

| Resolution | N | Implication for manuscript corpus |
|---|---|---|
| CONFIRMED (numeric metric in extracted fulltext) | 4 | include (SCI-000010, SCI-000129, SCI-000440, SCI-000650; two already anchor-verified) |
| CONFIRMED_PENDING_FULLTEXT (segmentation/benchmark paper, PDF not retrieved) | 9 | out of corpus until PDF retrieval |
| EXCLUDE_TOPIC (off-scope: sidewalk cracks, bombardment, urban traffic, human search, time-sync, amphibious, corn earworm, vineyard NMPC) | 8 | exclude - screening precision finding |
| EXCLUDE_EXC06 (adjudicator-confirmed no numeric segmentation metric) | 5 | exclude under EXC-06 |
| REVIEW_REQUIRED (no observable numeric metric; 10-minute human loop before any inclusion) | 13 | **excluded — confirmed unretrievable** (2026-09-09: no fulltext extraction, extracted MD, or PDF; paywalled/restricted venues) |

Effective fully-confirmed inclusion from the caveat stream = 4; effective corpus for quantitative synthesis
remains the 94 audited-clean extraction studies (phase-4) with the trust filter described in the ledger.

Discrepancy to reconcile: the 2026-09-04 report splits the 39 as 22 missing-abstract + 17 contested-EXC06;
the 2026-09-09 resolution found all 39 carrying the EXC06 caveat. Document the accounting difference.

**Reconciliation (2026-09-09):** both accounts cover the same 39 records. The 2026-09-04 split (22 missing-abstract + 17 contested-EXC06) is a *symptom-level* breakdown from the earlier screening batch; the CAVEAT_EXC06 flag was attached to all 39 during the stage-3 ledger for resolution bookkeeping. The canonical buckets (4 CONFIRMED / 9 PENDING / 8 EXCLUDE_TOPIC / 5 EXCLUDE_EXC06 / 13 EXCLUDED_UNRETRIEVED = 39) supersede the symptom split and are used in `synthesis/provisional_resolution.md` and manuscript §3.1.

## 4. PRISMA 2020 abstract checklist mapping

- RQ: stated (RQ1 accuracy / RQ2 edge inference / RQ3 consensus) - protocol.json research_questions
- Eligibility: INC-01..03 / EXC-01..06 (verbatim in SCREENING_CRITERIA.md + protocol.json)
- Information sources: 5 providers, 2018-01-01 .. 2026-12-31, English, OA preferred
- Risk of bias: verification block (retraction, COI, DAS/CAS, min trust score 6.0; QUADAS-2-adapted)
- Synthesis: comparative matrix (RQ1/RQ2) + trust consensus (RQ3); no meta-analysis of mixed datasets (88 distinct datasets)
- Registration: OSF draft - `synthesis/osf_registration_draft.md`; protocol fingerprint sha256:e1bbcb791d9108b2277fa468982f59cbdc611a66288556c5f4812fde34f1b077

## 5. PRISMA 2020 flow diagram structure (for the manuscript figure)

IDENTIFICATION -> SCREENING -> ELIGIBILITY -> INCLUDED, one row per count as in section 1, with
not-retrieved reasons on the eligibility edge and the definite-exclusion wedge (13 of the 39
caveats) shown as "excluded at full-text verification (retrieval/code/criteria)".