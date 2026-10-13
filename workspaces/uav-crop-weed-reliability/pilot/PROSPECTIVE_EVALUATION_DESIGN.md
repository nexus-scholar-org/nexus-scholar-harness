# Prospective agent-evaluation design — design-frozen BEFORE any model-outcome inspection (2026-10-13)

**Status:** DESIGN ONLY. No records sampled, no reference labels created, no
model exposed, no accuracy measured. Three objects are kept distinct per
`calibration/REVIEW_DESIGN.md` + `RESEARCHER_DECISIONS.md`.

## 0. Three objects (do not conflate)

1. **Query-development sentinels** (S1/S3/S4 positives + S2/S5 probes):
   already used for calibration (`calibration/QUERIES.md`,
   `verification.json`: Q2 3/3 eligible-positive hits on a 25-record page).
   They are NOT held out and NEVER count as held-out performance.
2. **Fresh literature records reserved for agent evaluation:** separately
   sampled AFTER criteria/skill tuning, with independently established
   reference labels BEFORE model exposure. This design specifies that set.
3. **Within-study held-out fields/dates/sensors:** attributes *charted from*
   papers (codebook `temporal_design`/`split_unit`/`shift_axes`), unrelated to
   whether *our literature records* were held out from model tuning.

## 1. Intended population and unit

- **Population:** candidate literature records for the scoping review’s
  title/abstract screening stage (eligibility reasoning under
  `SCREENING_CRITERIA.md` INC-01–03 / EXC-01–04, provisional v0.2), drawn
  from the formal corpus **after** the final search is executed and frozen
  (search date + source syntax + pagination + dedup recorded). boundary
  strata: clear-include / clear-exclude / platform-separability /
  report-type / date-language edge (cf. D1–D4 dry run).
- **Unit (primary):** literature *record* (deduplicated representative with
  persistent IDs + title/abstract; `workspace_id SCI-XXXXXX` is
  dedup-run-local, not cross-run identity). Criterion-level reasons are
  secondary units for error analysis. Full-text eligibility and charting
  accuracy are OUT of scope for this screening-evaluation (separate designs
  required).
- **Study-family vs report:** duplicate report versions are resolved BEFORE
  counting (protocol); the evaluation samples records post-dedup and tracks
  family linkage as metadata, not as the scoring unit.

## 2. Sampling and separation from development

- **Sampling frame:** the frozen post-dedup corpus (not yet existing —
  formal search unexecuted). Stratified random sample across the 5 strata
  above; development records (Q0–Q2 calibration pages, D1–D4, S1–S5) are
  **excluded by ID** from the frame (blocklist published with the freeze).
- **Separation:** sample AFTER criteria/skill freeze; reference labels
  established BEFORE any agent pass over the sampled records; agent prompts,
  model versions, and runs logged; no tuning on the held-out set
  (violations = protocol deviation, set discarded).
- **Enrichment disclosure:** if boundary strata are oversampled for power,
  sampling fractions are published and performance is reported stratum-wise +
  re-weighted to corpus prevalence — never as raw pooled accuracy alone.

## 3. Independent reference-label procedure

- **Default (protocol):** TWO independent human reviewers + named adjudicator
  (Option A, `REVIEW_DESIGN.md`). Reviewers screen title/abstract
  independently in batches (`agent_screen.py prepare` handoff), blind to each
  other and to model outputs; disagreements go through (i) criterion-level
  evidence exchange → (ii) full-text check where needed (ambiguity advances,
  never infers exclusion) → (iii) adjudicator decision → (iv) per-record
  logged decision + reason → (v) re-screen on eligibility amendment.
- **Fallbacks (B/C)** require a logged protocol amendment stating the
  single-reviewer limitation (B: second re-screens ≥10% + all near-boundary
  excludes, κ reported; C: agent triage only, human decides everything, all
  agent-suggested excludes human-reviewed + prompt/version logged).
- **Authorisation:** NO reviewers/adjudicator are assigned by this design.
  The factual gate is OPEN (see §8). A model acting twice, or an LLM critic,
  is NEVER a second human reviewer. Reference labels must precede model
  exposure; order is auditable via journal timestamps.

## 4. Missing text, unresolved decisions, disagreements

- Missing/incomplete abstract or unretrievable full text at screening stage:
 lean on title/metadata only per PROTOCOL.md; genuinely ambiguous records
  **advance** (include for full-text/pending), never inferred exclude.
  Provider gaps are retrieval states, not evidence.
- Unresolved post-adjudication decisions are retained as `UNRESOLVED` with
  reason; they are NOT counted as model error against an arbitrary label and
  are reported as their own denominator (see §5).
- Reviewer disagreements pre-adjudication are agreement data (κ, transition
  matrix via `screen-compare`), not model-error data.

## 5. Denominators (predeclared)

For the held-out set of size N (frozen):

- `N_eligible` (adjudicated INCLUDE), `N_ineligible` (adjudicated EXCLUDE by
  reason code), `N_unresolved` (no adjudicated label), `N_abstain_model`
  (model declines / no well-formed reason), `N_no_evidence` (model label
  right but criterion/anchor wrong or unsupported).
- **Eligibility errors:** false exclusions = adjudicated-eligible records the
  agent excluded ÷ `N_eligible` (primary safety metric); false inclusions =
  adjudicated-ineligible included ÷ `N_ineligible`. Report per-stratum + overall.
- **Abstentions:** reported separately (`N_abstain_model ÷ N`), never pooled
  as correct.
- **Reason/anchor errors:** incorrect criterion or unsupported quotation ÷
  (N − N_unresolved − N_abstain_model), separate from label accuracy.
- **Quotation accuracy:** verbatim match rate (cf. `scholar-verify`
  verbatim, threshold 0.90) over agent-cited spans; RAG cosine ≠ verification.
- Development sentinels NEVER enter any denominator.

## 6. Researcher effort and elapsed time

- **Correction effort:** per-record reviewer override rate, criterion
  correction rate, anchor correction rate, adjudication rate; time to correct
  (source-check + fix + resolution) measured from assignment to logged
  decision (not gross generation speed).
- **Elapsed review time:** total human time (screen + verify + adjudicate)
  vs agent-assisted counterfactual ONLY under separate/counterbalanced
  allocations (different reviewers or order-randomised disjoint record sets)
  to avoid memory effects; assignments + order preserved and published.
- **Suggestion bias:** fraction of agent-suggested excludes overturned on
  human review; all agent-suggested excludes get human review (Option C rule).
- Agreement alone (two agents agreeing) is NEVER reliability evidence.

## 7. Sample-size / precision approach (planning scenarios, no fabrication)

No error rates, reviewer time, or achieved precision are claimed or assumed.
Approach: **precision-gated** (Clopper–Pearson exact intervals) on the
primary metric (false-exclusion rate over `N_eligible`):

- Choose `N_eligible` so that 0 observed false exclusions rules out an
  unacceptable ceiling, and 1–2 observations still discriminate
  proceed/revise/stop (see §8). Illustrative widths (exact, two-sided 95%):
  0/20 → [0, 16.8%]; 0/30 → [0, 11.6%]; 0/50 → [0, 7.1%]; 1/30 → [0.08%,
  17.2%]; 2/50 → [0.5%, 13.7%]. These are arithmetic facts about the
  interval, not claims about the agent.
- Corpus prevalence of eligible records is unknown until the formal search;
  total N must oversample to bank enough `N_eligible` per stratum (e.g. if
  eligibility is ~20%, N≈150 yields ~30 eligible). The final N, stratum
  fractions, and target width are frozen WITH the corpus, before labels.
- No powered reliability/efficiency claim is made from calibration (n=4
  dry-run, 25-record pages). This design does not reverse-engineer thresholds
  from outcomes (none observed).

## 8. Predeclared proceed / revise / stop criteria (thresholds TBD with researcher)

Criteria are structural; numeric cutoffs require researcher authorisation
before the run (no thresholds invented here):

- **PROCEED** to review-scale assisted screening iff (i) false-exclusion
  upper bound below the researcher-set ceiling, (ii) anchor/reason error
  below its ceiling, (iii) unresolved + abstention within budget, AND
  (iv) time/correction effort shows a measured saving under the
  counterbalanced design.
- **REVISE** (criteria/skill/prompt + re-pilot on development records, new
  held-out set) iff errors concentrate in a fixable stratum (e.g.
  platform-separability) or anchors fail while labels pass.
- **STOP** (no agent-assisted screening; human-only review) iff false
  exclusions exceed ceiling, any eligible record is lost without human catch
  in the assisted arm, or separation/blinding is violated.
- All three decisions are recorded with denominators + intervals, not point
  estimates; software fixture pass counts are never pooled with these.

## 9. Authorisation and factual gates (explicit)

| Gate | Fact (2026-10-13) |
|---|---|
| Human reviewers / adjudicator assigned | **NONE assigned.** No names, no availability, no institutional source access (IEEE/Scopus/WoS unconfirmed). |
| Final formal search/refresh date | **NOT recorded.** No corpus, no sampling frame, no frozen blocklist. |
| Reference labels established | **NONE.** No held-out set sampled or frozen. |
| Model evaluation launched | **NOT launched and MUST NOT launch** until all above close + §8 thresholds authorised. |
| Who can authorise | Lead researcher (Mouadh) for scope/thresholds/amendments; protocol freeze additionally requires researcher review of assumptions + calibration outcomes per PROTOCOL.md. Delegated assistants record decisions; they do not constitute human reviewer assignment or freeze. |

**Do not use development sentinel coverage as held-out performance. Do not
fabricate assignments, time, error rates, or precision. The formal accuracy
evaluation remains gated — this document is the prospectively specified
design awaiting those facts.**
