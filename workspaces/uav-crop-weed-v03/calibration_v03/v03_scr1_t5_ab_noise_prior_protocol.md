# T5 pilot design — noise-prior A/B shard pair (queue item #15)

Persisted 2026-10-19 (orchestrator). Purpose: measure whether telling screening
shards what the pack composition looks like changes their decision distribution
— the protocol parameter flagged in lesson 48. This is the designed next-wave
pilot; **not yet executed** — dispatch waits for the researcher's word.

## Hypothesis

H0: informed (noise-prior) shards produce the same per-record decision
distribution as blind shards on identical packs (T4 baseline already exists).
H1: a noise-prior shifts decisions — most plausibly *more EXCLUDE* with
*higher stated confidence* on obviously-noisy records and *more PENDING* on
pack-typical records (anchoring bias), i.e., the prior changes both the mean
and the variance of judgments.

## Design (paired, fully controlled)

- **Unit**: per-record decision. Same packs, same model family, same frozen
  instrument (criteria SHA `9ae1f97d…b86f`, prompt template `0c7f129d…d16d`).
- **Blind arm (B)**: T4 round-2/3 decisions — already landed and strict-validated
  (1,235 records across 25 packs, 98.7% EXCLUDE agreement vs closed lane).
  No new run needed.
- **Informed arm (A)**: NEW shard sessions, TWO packs where the blind arm's
  behavior is known (recommend: `pack_0001` — 49 EXC / 1 PEND heavy-review
  composition — and `pack_0015` — 47 EXC / 3 PEND with guardrail cases). One
  shard per pack (2 sessions), to avoid intra-arm contagion.
- **Manipulation** (the ONLY prompt delta): one added paragraph in shard A's
  dispatch, verbatim-candidate:

  > PRIOR (may bias you — that is the experiment's point): historical
  > screening of similar packs returned ~95–100% EXCLUDE with a small guardrail
  > PEND residue; the corpus slice feeding this pack is dominated by
  > off-domain UAV engineering. Calibration note only — judge every record on
  > its own visible evidence; the pack-mention bias ("everyone else excluded
  > these") must not touch your per-record reasoning.

- **Cross-contamination guards**: A shards get the canonical FORBIDDEN list
  (decisions/, third_lane/, verification_lane/, moderation_views/, drivers,
  journal, code, web, other sessions) — they must NOT see the T4 baseline.
  Sessions are fresh; different packet text otherwise identical.

## Metrics (pre-registered)

1. **Per-record concordance** A vs B on the same packs (paired);
   decision-shift matrix (INCLUDE/EXCLUDE/PENDING × A→B).
2. **McNemar-style test** on discordant pairs (with n≈100, expect ≥2 committed
   direction if H1 has a meaningful effect; report exact binomial one-sided).
3. **Reason-code redistribution** (does WRONG_TASK get applied to MORE records
   in A?), per-record confidence deltas (mean, and on the PENDING subset).
4. **Guardrail compliance** (corrected rule) — must be ZERO violations in BOTH
   arms; a violation voids the run.
5. **Schema discipline**: same strict validation as T4 (IDs 1:1 order, SHAs,
   canonical fields) — a contract failure voids the record, not the finding.

## Success/interim criteria

- If A == B on ≥98% of pairs *and* confidence deltas ~0 → lesson 48's prior is
  inert; do NOT add pack-composition warnings to prompts (blinding cheaper).
- If A shifts EXCLUDE-heavy with confidence inflation but concordance on
  borderline records is stable → prior is safe for *noise* but must be
  suppressed for *pending-type* packs (split policy, not silence).
- If A shifts PENDING/countercurrent on borderline records → prior is harmful;
  blinding is mandatory for judgment lanes.

## Bookkeeping plan (at execution)

- New shard tag `T5-A1`, `T5-A2`; decisions under
  `scr1_screening/verification_lane/ab_study/decisions/pack_NNNN_decisions_T5A.json`
  (never overwrite T4 files).
- One SCREENING_RUN journal event at dispatch, one at close, plus the analysis
  artifact `v03_scr1_ab_noise_prior.json`.
- Option C unchanged: all outputs remain suggestions.
