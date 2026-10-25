# Next investigations queue — SCR1 post-funnel follow-ups

Persisted 2026-10-19 (orchestrator, on researcher request). Items marked [RUNNING]
have drivers/output artifacts; items untouched are queued for later rounds.
Anchor: funnel 588 INC / 12,357 EXC / 391 PEND; provider findings in
`v03_scr1_provider_investigation.json` + `v03_scr1_provider_uniqueness.json`.

## Tier A — recommended first (cheap, decision-changing)

1. [DONE] **Include-rate per query_id** — which of the 40 query groups
   (Q-R3-openalex, Q-R3-crossref, R3C yearly, R3D quarterly, S2/arXiv/PubMed)
   actually produce include-lean mass; kill/rank dead queries. Output:
   `v03_scr1_yield_investigation.json`.
2. [ ] **Include-rate vs citations** — are the 69 Crossref-unique includes
   systematically low-citation (good recall) or is high-citation material
   missing from OpenAlex (coverage-gap warning)? Distribution comparison.
3. [DONE] **Moderation-redaction burden by provider** — redaction ledger
   (abstract-withheld counts + decision distribution) per provider.
4. [DONE] **Year coverage curves** — records-by-year and includes-by-year
   per provider (OpenAlex recency bias? Crossref classic-proceedings bias?).
5. [DONE] **Dedup near-twin probe** — only 263 duplicates merged at 1.8%; scan
   mutual-EXCLUDE pairs for near-identical normalized titles that did NOT
   merge (consistency/recall defect check).
6. [DONE] **T3/T4 entropy vs abstract length** — do disagreements concentrate in
   short-abstract records (evidence poverty routes to full-text, not recon)?

## Tier B — moderate effort

7. [DONE] Rationale-grounding flag rate **by provider** (from
   `v03_scr1_rationale_audit.json` cross-tab with provider labels).
8. [DONE] T4 agreement **stratified by pack provider-dominance** (is the 98.7%
   headline provider-dependent?).
9. [DONE] **Marginal value of S2/arXiv/PubMed** (21 unique records): did any reach
   include-lean? If all redundant, scope future lanes (PubMed only for health,
   arXiv only for preprints).
10. [DONE] Batch-position entropy in the 283-batch sweep (drift/pace check).

## Tier C — design probes (slowest, biggest payoff)

11. [DONE] **Cap ablation replay** — within-query file-order rank proxy;
    cap N ∈ {100,250,500,1000,∞} per query; report surviving records and
    surviving crossref-unique includes (cap operating curve). NOTE: retrieval
    rank is proxied by deduped file order, not original provider rank.
12. [DONE] Include-lean content pre-read — classify a) primary method / b)
    dataset / c) review / d) platform-ambiguous — feeds PRISMA.
13. [DONE] 2027-leak disqualification check (18 leaked rows vs other criteria).
14. [ ] **WRONG_TASK taxonomy clustering** over the 10,578 Crossref
    exclusions (severity ladder → which Crossref slices to type-filter).
15. [DONE] **T5 A/B: noise-prior vs blind shard** over identical packs (does
    informing shards of expected noise change decisions? curriculum for
    lesson 48 skill design). Verdict: policy 3 — prior harmful on judgment
    lanes (PENDING-preservation broken; guardrail violation fired); blinding
    mandatory. Artifacts: `v03_scr1_t5_ab_noise_prior_protocol.md` +
    `v03_scr1_ab_noise_prior.json`.

## Queue status: 15/15 DONE — investigations program closed 2026-10-19.
