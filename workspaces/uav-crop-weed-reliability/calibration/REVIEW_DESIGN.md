# Review design — revised after delegated decisions

Use [RESEARCHER_DECISIONS.md](RESEARCHER_DECISIONS.md) for selected scope and
workflow. Formative calibration uses operator-attended researcher confirmation;
no human labels or second reviewer are invented. Publication-quality independent
reference review remains conditional on actual people and assignment.

There are THREE distinct objects:
1. Query-development sentinels: known positive and negative scope probes already
   used to tune queries. They are not held out and do not force inclusion.
2. Fresh agent-evaluation records: separately sampled after criteria/skill tuning,
   with independently established reference labels before model exposure.
3. Primary-study held-out fields/dates/sensors: attributes charted from papers,
   unrelated to whether our literature records were held out from model tuning.

Reference disagreements: compare criterion-level evidence, obtain full text where
needed, preserve unresolved decisions, and use a named adjudicator when assigned.
The same researcher repeating screening does not constitute two independent
human reviewers; an LLM critic is likewise not the second human reference.

Remaining facts: actual final search date, institutional source access, human
reviewer/adjudicator availability, complete retrieval, and accepted source lineage.
Remaining design gate: held-out sampling/size and precision, timing allocation,
error denominators and proceed/revise/stop criteria fixed before evaluation.
Sentinels and the tiny development dry run supply no powered reliability result.

## Historical proposal (superseded)

# Reviewer & held-out design note — UAV crop/weed reliability pilot

> Historical calibration record. [Senior review](SENIOR_REVIEW.md) corrects sentinel/report-type and recall interpretations; [delegated decisions](RESEARCHER_DECISIONS.md) supersede the open choice list. No formal screening or independent human labels are claimed.

Date: 2026-10-12/13 (UTC). Status: **NO second reviewer is assigned. No
reviewer is assigned by this pilot.** PROTOCOL.md requires, before formal
screening, either two recorded independent human reviewers + adjudication
procedure or an explicit logged amendment to a single-reviewer procedure with
its limitation — and states "a model acting twice is not two human reviewers."
This file proposes options for the researcher to decide. Nothing here
constitutes assignment or protocol amendment.

## Reviewer arrangement options

- **Option A (protocol-default): two independent human reviewers + adjudicator.**
  Reviewers screen title/abstract independently in batches (agent-prepared
  handoff per AGENTS.md `agent_screen.py` flow), disagreements go to a named
  third adjudicator, criterion-specific reasons + PRISMA counts preserved.
  Highest credibility; slowest; needs two available domain readers.
- **Option B: single human reviewer + verification sample.** One reviewer
  screens all records; a second person (or the researcher) independently
  re-screens a random ≥10% sample + all excludes near the boundary; report
  agreement (e.g. Cohen's κ via `scholar-search screen-compare`) and resolve
  all disagreements by full-text check. Requires a logged protocol amendment
  (single-reviewer limitation stated).
- **Option C: single reviewer with agent pre-sort (human decides everything).**
  Agent applies SCREENING_CRITERIA.md as a triage suggestion only; the human
  reviewer confirms/rejects every record and all agent-suggested excludes get
  human review. Same amendment requirement as B, plus prompt/version logging
  for the agent pass. Fastest; weakest defensibility — venue-dependent.
- Adjudication procedure (for A, and disagreements in B/C): (1) criterion-level
  reason exchange; (2) full-text check for ambiguity (ambiguity advances, never
  infers exclusion); (3) named adjudicator decides; (4) decision + reason logged
  per record; (5) re-screen affected batches if eligibility is amended.

## Held-out evaluation design proposal

Two distinct held-out concepts must not be conflated:

1. **Held-out literature set (review-validity check):** reserve a small,
   pre-registered set of known-relevant records (the SENTINELS.md set is the
   natural seed, plus 2–5 additions at full-text stage) that the executed search +
   screening pipeline must retrieve and include; report recall against them in
   the PRISMA flow. Distinct from the `target_data_use` charting axis.
2. **Held-out *evaluation* charting (object of the review):** the review charts
   whether primary studies test on held-out fields/dates/sensors — this is
   data charted FROM papers (CHARTING_CODEBOOK.md `temporal_design`,
   `split_unit`, `shift_axes`), not a procedure the review itself runs.
   Proposal: pre-specify, before extraction, the decision rules for
   `heldout_date` vs `multiple_dates_no_heldout` disagreements (the D3 pilot
   case: multi-month acquisition ≠ held-out testing) and pilot them on 2–3 full
   texts with dual charting + adjudication.

## Open researcher decisions (checklist)

1. [ ] Confirm or revise the **English-only assumption** (bias statement for
   the report if retained; search implications if expanded).
2. [ ] Fix the **final search cutoff date** (decides S5-style edge records) and
   confirm the **2020 lower bound** (decides S2/WeedMap background-vs-include).
3. [ ] Confirm or deny **IEEE Xplore / Scopus / WoS access** (coverage limitation
   statement if unavailable).
4. [ ] Choose reviewer arrangement (**A / B / C**), name the humans, name the
   adjudicator; or direct a single-reviewer amendment.
5. [ ] Approve the **held-out literature set** (adopt/extend SENTINELS.md 5) and
   the **held-out-charting decision rules** pilot on full texts.
6. [ ] Confirm the **codebook revision path**: pilot on 2–3 full texts before
   freeze (CHARTING_PILOT.md finding 3), with logged reasons for changes.
7. [ ] Confirm whether the **AvaRel-Fuse draft** framing constrains any
   eligibility decision (protocol says it does not; confirm).
8. [ ] Decide disposition of background records (S2, D4-style reviews): cite as
   related work vs formal background appendix.

No freezing, no assignment, and no screening were performed in this pilot.
