# Thesis Assembly Skeleton

**Status:** v0.1 scaffold (2026-09-10) — chapter structure, source mapping, integration notes; no prose drafted yet.
**Primary spine:** B — application domain (UAV/CV precision agriculture) with the harness as instrument; co-track A (trustworthy AI-for-research) kept as instrument validation. Both feed one thesis.
**Owner of structure decisions:** `reports/PHD_DELIVERABLES_PLAN.md` (open supervisor questions §4 gate final assembly).

---

## Chapter → source map

| Chapter | Working title | Primary source | Figure inventory | Table inventory |
|---|---|---|---|---|
| ch.1 | Background: UAV computer vision in precision agriculture; the methodological gap AI-assisted reviewing must fill | D1 §1 (`workspaces/uav-cv-precision-agriculture/synthesis/d1_manuscript_draft.md` §1) + domain RAG reviews (`.../synthesis/rag_rq1..6_review.md`) | (from D1) year distribution, family distribution, dataset reuse | — |
| ch.2 | Method: the provenance-hardened evidence pipeline | D2 method paper (`reports/manuscript_d2.md` §2) + `reports/methodology_report.md` + `reports/pipeline_engineering_report.md` | D2 figures (verification coverage, per-RQ rates, repair loop, scope/debates) | D2 Table 1 (head-to-head), Table 2 (per-RQ rates) |
| ch.3 | Empirics: UAV segmentation / edge-inference benchmark review (thesis empirical core) | D1 manuscript complete (`.../synthesis/d1_manuscript_draft.md`) | D1 fig1–6 (PRISMA flow, year, family, dataset reuse, edge throughput, RoB heatmap) | D1 Tables 1–3 (metric reporting, embedded true-edge cohort, RoB) + `rq1_benchmark_tables.md` (A–C), `rq2_edge_tables.md` (B–D1) |
| ch.4 | Validation: the meta-review of AI research harnesses — the instrument auditing itself + review-of-reviews evidence | D3 manuscript (`reports/manuscript_draft.md`, Review 1.0 living scoping review) | D3 fig_prisma_scr_flow + D2 figures reused (head-to-head, scope/debates) | D3 Tables 1–7 (screening flow, reliability, methods, RAG/verbatim, consensus, RoB, characteristics) |
| ch.5 | Framework/implications: trustworthy autonomy in agri-AI evidence | NEW WRITING — synthesis of ch.2 instrument + ch.3 findings (15 true-edge, 83/88 single-use datasets, 77 unclear-RoB) + ch.4 meta-evidence (43.3% RAG vs 510/510 verbatim) | (to be designed) | (to be designed) |

## ch.3 integration constraints (the empirical chapter is the thesis core)

- Paired intra-study benchmark tables: `rq1_benchmark_tables.md` Tables A–B (per-dataset matrix, paired architecture comparisons).
- Embedded true-edge cohort table: D1 Table 2, n=15 — include energy/power where reported (only 3 studies; SCI-000440 4.8 W, SCI-000683 10.0 W, SCI-000810 13.2 W / 0.28 J-per-inference).
- 77 unclear-RoB sensitivity framing: RoB domains from `phase4/risk_of_bias.json`; overall low 2 / unclear 77 / high 15.
- 11 industry-tie COI context (4 funding, 7 affiliation/equipment) — must be explicit in the Discussion.
- Provisional resolution: `provisional_resolution.md` buckets 4 CONFIRMED / 9 PENDING / 8+5+13 excluded (39 total).
- Corpus lock statement: 138 retrieved → 94 audited-clean (44 removed), PRISMA flow `prisma_2020_flow.md`.

## ch.5 synthesis inputs (to be drafted)

- Trust verdict to carry: accurate-but-fragile evidence base. Top-per-dataset mIoU 0.875–0.983 yet 83/88 datasets used once ⇒ cross-study ranking invalid; only intra-study pairs trustworthy.
- Deployment envelope: Orin/RK3588 at FP16/INT8, ≤512 px sustain >20 FPS; Nano/TX2/CPU single-digit FPS; power reporting near-absent.
- Meta-evidence from ch.4 to carry: 43.3% RAG entailment-verified, 11 non-included studies cited, 510/510 verbatim at ≥0.90 ⇒ retrieval-associative gates are not verification; corpus-scope enforcement is the precondition for trustworthy automation.
- Thesis-forward implication: Q: what does trustworthy autonomy in agri-AI demand of the reviewers' toolkit? A: deterministic, corpus-scoped, quote-verified claim provenance + trust stream auditing (retraction/DAS/CAS/COI/RoB).

## Cross-cutting duties (every chapter)

1. Protocol fingerprints cited verbatim: D1 `sha256:e1bbcb79…`; D3 `sha256:9646d5ec…`.
2. Event-ledger counts frozen per chapter freeze-date (D3 currently 67 events at D3 close; D1 ledger independent at 94 events).
3. All chapter figures regenerable from committed scripts (`build_d2_figures.py`, `build_d1_figures.py`, `build_prisma_flow_png.py`).
4. No new prose may reuse a claim whose number is not pinned by `reproduce_d2_stats.py` / `verify_journal_prep.py` / D1 `project.json`.

## Open supervisor questions gating final assembly (§4 of the plan)

1. Is ch.3 the intended core, and does the department accept an SR+benchmark as the doctoral empirical chapter, or demand novel algorithm/experiment work on top?
2. Is the meta-review (D3) a chapter or a stand-alone paper in the program's rules?
3. Endorsement of the early-evidence framing for a corpus that is 52% 2026 preprints.

## Assembly sequence (agent-side, after supervisor answers)

- [ ] Decide ch.3 vs ch.4 as core per supervisor Q1/Q2.
- [ ] ch.3: merge D1 tables into thesis numbering; write ch.1 background from D1 §1 prose.
- [ ] ch.2: adapt `manuscript_d2.md` §2 methods prose to chapter voice; place Phase-4 trust streams in continuity with ch.3's RQ3.
- [ ] ch.5: draft framework from synthesis inputs above; design 1–2 chapter-specific figures/tables.
- [ ] Compose thesis front matter, bibliography (D1 APA + D3 Vancouver(36) + foundational refs), per-chapter event/ledger traceability.