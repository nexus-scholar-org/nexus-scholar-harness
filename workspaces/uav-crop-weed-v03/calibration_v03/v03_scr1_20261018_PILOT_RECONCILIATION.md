# SCR1 pilot — blinded two-agent Pass-1 test (UAV-SCREEN-SCR1-20261018)

Multi-agent screening machinery test authorized by the researcher. Two
independent screener-agents (A1/A2), same pilot slice (batches 0001–0006,
300 records), zero cross-visibility. All decisions are PASS-1 SUGGESTIONS
under Option C (100% human lead confirmation pending).

## Result matrix

| Metric | Value |
|---|---|
| Coverage per agent | **300/300** decision lines, batch-hash copied verbatim |
| Raw agreement | **99.33%** (INC 10/10, EXC 281/281, PENDING 7/7 mutual) |
| Cohen's κ (binary, 292 mutually decided) | **1.0** |
| Fleiss κ (kit `reconcile_multi_screener_decisions`) | **0.9506**; majority 292, ties 1 |
| Guardrail (abstract-null ⇒ never auto-exclude) | **upheld by both agents; 0 violations** |
| Reconciled include rate | 3.41% Wilson95 [1.86, 6.17] over 293 reconciled-decided |

**Projection (report-only, NOT a decision):** full-corpus includes ≈ **483 of
14,150** (interval 263–874); PENDING ≈ 2.7% → ~380 ambiguous records for human
triage. The "is this large corpus really included?" first estimate: the funnel
narrows ~29× by title/abstract triage alone, consistent with a harvest pool
dominated by relevance-search tails (the Crossref sweep tail, per design).

## The two boundary cases (exactly what PENDING exists for)

| ID | A1 | A2 | Signal |
|---|---|---|---|
| SCI-000637 | INCLUDE | PENDING | Zenodo drone weed-hotspot *sample data*, explicitly not a full training set |
| SCI-003230 | PENDING | EXCLUDE | Wheat/weed-cover **phenotyping**, platform unstated (EXC-02 territory but titled-only) |

Both route to the human lead's adjudication sheet, not to agent resolution.

## Machinery lessons recorded (for the harness dev backlog, ref. H1/H6)

1. **Agent blinding held**: both agents reported strict read-limits unaffected;
   outputs were schema-clean (12/12 files, every reason code present).
2. **Driver-side guardrail census is a detector, not the rule.** The reconcile
   driver's placeholder-aware census matched 0 ids while both agents flagged
   the true title-only guardrail cases — placeholder-text abstracts are
   non-null in the batch payload. Fix: census on *effective-signal emptiness*
   (stripped boilerplate), or carry the guards' own PENDING reasons as the
   compliance trace.
3. **Kit rating-fill semantics**: `reconcile_multi_screener_decisions` fills
   missing ratings with EXCLUDE — a one-sided PENDING-vs-EXCLUDE becomes a
   silent EXC majority (masked here by 99.3% agreement). For the full run,
   feed only mutual INCLUDE/EXCLUDE ratings or pass an explicit PENDING-aware
   adjudication_map.
4. **Wetware review of agent reports is cheap and caught real nuance**
   (SCI-000694 turfgrass self-flagged for possible PENDING upgrade by A2;
   batch-6 zero-includes sanity check requested by A2).

## State

Journal: `SCREENING_PREPARE` EVT-…230144, `SCREENING_RUN` EVT-…231348.
`PROVISIONAL_NOT_FROZEN`; nothing is included yet — every one of the 300
pilot records awaits the human lead's line-item confirmation via
`v03_scr1_human_confirmation_packet_pilot.md`. The Zertal/Djenba 10% blinded
sample + boundary-exclude verification is drawn AFTER full Pass-1.

Remaining gates to full Pass-1: researcher go for the 283-batch (≈14k record)
dispatch; then human lead confirmation; then the blinded human sample;
then reconciliation and the PRISMA screening report.
