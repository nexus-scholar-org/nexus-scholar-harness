# PhD Deliverables Plan

**Workspace:** `ai-research-harnesses-trust` (meta/SLR) · `uav-cv-precision-agriculture` (application domain)
**Decision (2026-09-09):** primary spine = **B — application domain (UAV/CV precision agriculture)** with the harness as the instrument; **co-track A** (trustworthy AI-for-research) is real and kept alive because it doubles as instrument validation. Both spines feed one thesis.

---

## 1. Thesis architecture (Spine B primary)

| Chapter | Content | Feeds |
|---|---|---|
| ch.1 | Background: UAV computer vision in precision agriculture; the methodological gap AI-assisted reviewing must fill | D1 |
| ch.2 | Method: the provenance-hardened evidence pipeline — discovery → screening (Fleiss' κ) → extraction → verbatim claim verification → consensus → Phase-4 trust streams | D2 (instrument chapter) |
| ch.3 | Empirics: the UAV segmentation / edge-inference benchmark review (corpus secured; write-up pending) | D1 (thesis core) |
| ch.4 | Validation: the meta-review of AI research harnesses — the instrument auditing itself + a review of reviews-class literature | D3 |
| ch.5 | Framework/implications: trustworthy autonomy in agri-AI evidence | synthesis |

The instrument is finished. **The measurement on the domain corpus is what is actually pending.** Steelman this in every planning conversation: the thesis is won or lost in ch.3, not in more tooling.

---

## 2. Deliverable cards

### D1 — UAV/CV systematic review & benchmark (thesis empirical core) · *DONE (write-up complete) — submission pending*

Verified state from `workspaces/uav-cv-precision-agriculture/project.json`:
- 1,837 identified → 1,488 deduped → 150 included → 138 fulltexts → **94-study audited-clean corpus** (44 audit-removed), 92% retrieval
- RQ1 segmentation performance (mIoU/F1) comparison; RQ2 edge-inference throughput under hardware constraints — metric datasets live: `synthesis_matrix.json` (94 studies), `synthesis_stats.json`, `synthesis/literature_review.md` (synthesis_verified: true)
- Phase-4 trust streams all DONE on all 94: retraction 0 flagged; RoB 2 low / 77 unclear / 15 high; COI 11 industry ties; open-science DAS 21 / CAS 18 public links; trust consensus 12 clusters → 8 ADEQUATE / 2 WEAK / 2 UNVERIFIED
- 6,707 vector chunks + 145-node citation graph for the methodology appendix

**Write-up COMPLETE (2026-09-09)** — the bundle is fully assembled and committed:
- `synthesis/d1_manuscript_draft.md` — complete manuscript (abstract, §1–§6, data availability, references; 354 claim-level checks, 3 quote-backed corrections disclosed)
- `synthesis/d1_tables.md` (Tables 1–3), `rq1_benchmark_tables.md`, `rq2_edge_tables.md` (15 true-edge cohort), `rq1_metric_reporting.md`, `rq1_anchor_audit.md`
- `synthesis/prisma_2020_flow.md` + `figures/fig1-6.*` (PRISMA flow, year/family/dataset-reuse/edge/RoB) — PNG+PDF
- `synthesis/provisional_resolution.md` — 39-caveat resolution ledger (4 CONFIRMED / 9 pending / 8−5−13 excluded)
- `synthesis/cover_letter.md` (date + OSF ID to fill), `synthesis/osf_registration_draft.md`, `submission_bundle_manifest.md`
- Regeneration scripts in `scripts/` → all artifacts deterministic/reproducible

Remaining (human): OSF reg submit + record ID; fill cover-letter date; render to Elsevier template (≥300 dpi figs).

Venue: domain flagship (e.g., *Computers and Electronics in Agriculture*, *Precision Agriculture*, or *Remote Sensing*). Target acceptance = thesis ch.3.

### D2 — The trust-provenance method paper (co-track A; instrument chapter)

Your most publishable artifact, ~80% material already in the repo:
- Result: auto-extraction (RAG baseline) certified only **43.3% of claims** as entailment-VERIFIED (25 studies, 11 non-corpus studies cited, verified in-scope claims for only 8/14 studies, zero claims for 44/58 included) vs the verbatim pipeline **510/510 at ≥90% threshold** — a measurable hallucination/verification result
- Method stack: `VerbatimClaimVerifier` (NFKC, 8-char window / 6-token n-gram dual-pass), multi-screener Fleiss' κ reconciliation (n≥3, deadlock isolation), Consensus Cartographer (Jaccard 0.30 / embedding θ 0.40), Phase-4 trust streams + trust-weighted grading (BLOCKED→STRONG)
- Evidence: `synthesis/method_comparison.md`, `docs/phase_6/README.md`, Phase-6 tests (98 pass / 3 skip), 50-event audit ledger
- **Status: write-up COMPLETE + final submission review DONE (2026-09-10).** `reports/manuscript_d2.md` v1.3 finalized (authors/affiliations/declarations, 14 references with resolved DOIs, RQ definitions, repair-loop transparency incl. first-pass 354/510, self-referential-criterion caveat, descriptive p-value framing). Every headline number recomputed and asserted by `scripts/reproduce_d2_stats.py` (37 assertions, all pass; Fisher p = 1.34e-49) against committed ledgers; figures 1–4 regenerate from `scripts/build_d2_figures.py` and are now embedded in the manuscript. Submission review pass applied: source-count wording corrected to five federated sources (bioRxiv-track via PubMed indexing), κ relabeled "fair" (not fair/moderate), threshold wording everywhere ("≥0.90 glyph-normalized coverage", not byte-exact), event count synced to 66. **Remaining: author human read-through + submission.**
- Venue: *Research Synthesis Methods*, *JAMIA*, or CS methods + arXiv. **Does not wait on D1.** Ready for author review → submission.

### D3 — Meta-review: "AI research harnesses and trust" (co-track A; ch.4 + instrument validation)

- Already drafted: `synthesis/literature_review.md` (4,198 words) + `reports/manuscript_draft.md` (4,048 words, 36 refs), 58 included / 181 excluded, 510 verified claims, 95 clusters
- **Framing prep DONE (2026-09-09, EVT-20260909223235)**: quantified corpus composition (32/58 = 55% preprint-track; 2026 alone = 30/58); wrote `reports/D3_FRAMING_DECISION.md` recommending **Option A: early-evidence / living scoping review** (title/methods must name it); resolved all 23 pending-author preprint refs via arXiv/OpenAlex (`scripts/resolve_d3_authors.py`, `scripts/regenerate_d3_references.py`) — reference list now fully author-attributed.
- **Option A ADOPTED (2026-09-09)**: `manuscript_draft.md` → v2 (early-evidence living scoping review, Review 1.0): living-review title/front-matter, early-evidence framing in abstract + §1, §3.8 living-review protocol (quarterly cadence, versioning, preprint policy incl. Crossref update-to supersession, diff discipline), §5.3 limitations rewritten, §7 declarations + protocol availability; all 36 refs author-attributed with arXiv/DOI IDs.
- **Adversarial audit v3 (2026-09-09, EVT-20260910-D3ADV)**: fixed wrong protocol fingerprint in §7 (was the other project's hash; now the recorded compile fingerprint `9646d5ec…`); COI partition 5+4+1+37=47 (added missing academic-or-public class); RAG coverage 43→44/58; κ relabeled fair (not fair/moderate); 47/58 Phase-4 coverage gap now explicit in §3.4+§5.3; ≥0.90 threshold wording (not byte-exact) in abstract/§1/§3.5/§5.2/§6; [5]/[6] OpenScholar preprint-of-published resolved; search strategy + supplement pointers added (§3.1/§3.8); protocol registration disclosed as "not external at v1.0"; authors/funding/CRediT block added; Appendix/search-log + preprint-version-table marked as supplementary deliverables still to be generated at journal-prep. Full findings: `reports/D3_ADVERSARIAL_AUDIT.md`.
- **Journal-prep packs built (2026-09-09)**: Vancouver-restyled 36 refs (first 6 authors + "et al.", venue-normalized, Workspace tokens moved to `reports/supplementary_references.md` with preprint→published supersession table); PRISMA-ScR flow report (`synthesis/prisma_scr_flow.md`) + vector figure (`synthesis/figures/fig_prisma_scr_flow.svg`); machine-readable search-log per version (`literature/search_log_v1.0.json`); OSF registration draft (`reports/D3_OSF_REGISTRATION_DRAFT.md`) — human step: submit to OSF. Corrected source-count wording to the verifiable five federated sources (bioRxiv-track via PubMed/Crossref indexing); re-synced `pipeline_engineering_report.md` and `methodology_report.md` event counts to 58; added `scripts/verify_journal_prep.py` (auto-reconciles refs↔supplement map↔ledger) and ran an independent preprint-identifier + OSF-criteria-verbatim QA pass (EVT-20260909234533-ed818a).
- **Remaining for submission (human)**: OSF registration submission (snippet + long-form draft ready, `reports/D3_OSF_REGISTRATION_SNIPPET.md`); final human read of the DOCX/HTML; per-version search-log updates each living cycle. Final v3 submission review DONE 2026-09-10 (commit `a34a415`).
- Role in thesis: meta-evidence that the class of tools this thesis builds is under-audited — motivates ch.2.
- Venue: *Systematic Reviews* (BMC) / *Research Synthesis Methods* / discipline journal.

### D4 — Software/artifact paper (back-pocket; ch.5-supporting)

- JOSS / *SoftwareX* / GigaScience(Software) on the harness: agent-agnostic CLI + MCP + workspace-files + append-only audit ledger + Phase-6 trust tools
- **Phase-7 distribution work (P7.1–P7.9) becomes content for this paper — not a pre-paper project.** This is the discipline mechanism: productization earns a publication or it doesn't happen.

---

## 3. Sequencing (what to do now)

1. **D1, D2, D3 write-ups ALL COMPLETE (2026-09-09/10).** D1 manuscript + bundle assembled; D2 v1.2 finalized; D3 v3 final submission review done. Nothing left but submissions (human) and assembly.
2. **Now→first submission in flight.** Remaining paper work (agent-side): D2 author review (the D3-style final pass not yet run on manuscript_d2.md). Human: OSF registration steps for D1 + D3, cover-letter fill, journal-template renders.
3. **After D1/D2 submitted:** D4 (software/artifact paper) + Phase-7 distribution work (P7.1–P7.9) — build only what unblocks that publication.
4. **Thesis assembly in parallel:** ch.1 background, ch.2 methods (from D2), ch.3 (D1), ch.4 (D3), ch.5 synthesis — open supervisor questions below gate final assembly.

## 4. Open questions for your supervisor

1. Is ch.3 (the application review) the intended core, and does the department accept an SR+benchmark as the doctoral empirical chapter, or does it demand novel algorithm/experiment work on top?
2. Is the meta-review (D3) a chapter or a stand-alone paper in your program's rules?
3. Endorsement of the early-evidence framing for a corpus that is 52% 2026 preprints.

## 5. Guardrails (anti-escape mechanism)

1. **Zero new engineering phases until D1 submitted.** Any change to kits/harness must reference a paper it unblocks.
2. Weekly check: "did today produce text/data a reviewer can read?" No = escape hatch, revert to D1 table-scaffolding.
3. Phase-7 work is gated behind D4 — earns a publication or is dropped.
4. Progress metric: not commits, not kit features — D1 word count + completed tables.