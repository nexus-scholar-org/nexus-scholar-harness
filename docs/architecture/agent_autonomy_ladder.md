# Agent autonomy ladder: proposal and design

Status: DECIDED 2026-11-10 (the researcher took the seven decisions in §9, all as recommended). Build order in §10; nothing starts before M3c-screens lands and the IEEE measurement exists.
Scope: screening autonomy modes (Phase 2), the calibration gate that unlocks
them, provenance of agent-made decisions, and a bounded discovery assistant
(Phase 1). Inception (Phase 0) is unchanged.

Companion decisions: `docs/decisions.md` 2026-11-03 "Agent system: proposals
only, least autonomy per job" (this proposal extends it; it does not reverse
it), 2026-11-04 screening decisions (§9 of
`docs/architecture/screening-api-contract.md`).

## 1. The idea in one paragraph

The agent earns autonomy on the researcher's own decisions. It starts as a
proposer. Once it has been measured against enough of the researcher's own
screening of this review and its recall of includes is high enough, the
researcher may let it screen the easy part and audit a sample. Only after a
larger measured set may they let it screen everything. Every record keeps a
decision event that says who decided it and under which mode, the PRISMA
methods paragraph states what the agent did, and a protocol change drops the
review back to the first rung. Nothing an agent decides is ever recorded as a
human decision.

## 2. What exists today

| Piece | State | Where |
|---|---|---|
| Decision events | Human only. `method != "HUMAN"` is refused with `INVALID_OUTPUT` ("agents submit proposals"). | `src/scholar_harness/screening/events.py:228` |
| Proposals | Append-only, with model, prompt hash, input hash, validators, derived outcome, `cannot_decide`. Outcome rule table: failed checks, `cannot_decide` or a not-reported criterion give `MAYBE` (Unclear), never Exclude. | `src/scholar_harness/screening/proposals.py:131-250` |
| Agent runs | In-app runs on the researcher's key with consent, estimate, cost ceiling, cancel; MCP driver writes proposals the same way. | `src/scholar_harness/screening/agent_runs.py` |
| Calibration | A run of kind `calibration` over records the researcher already decided; answers `include_recall`, `ci_low`, `missed_includes`, `compared`, marked advisory. | `agent_runs.py:590`, route `POST /screening/proposals/calibrations` |
| Agreement | The researcher's decisions beside the drafts, counting only decisions made before the reveal; the 2x2 table and the splits. | `GET /screening/agreement` |
| Modes | Settings hold `mode` = `human_sees_every_record` or `ai_agreed_exclusion` (needs a typed confirmation and `sample_audit_size`). **No code reads the mode**: it changes nothing in the queue or the intake. It is only reported in the methods paragraph (`export.py:846`). | `console/api/screening_v1.py:39-42, 411-422` |
| PRISMA checks | `human_provenance` (every winner is HUMAN), open conflicts, bound to current protocol, every record decided, projections current. | `screening_v1.py:678-706` |
| Methods paragraph | States one reviewer screened every record, the blinding, the queue order, and whether the AI-agreed-exclusion setting was on. | `src/scholar_harness/screening/export.py` |

So the second mode exists in name only. This proposal replaces it with modes
that do something, and gates them.

## 3. The ladder

| Rung | Name (setting value) | Who decides | What the researcher sees in the queue | Unlock |
|---|---|---|---|---|
| L0 | `human_every_record` | The researcher, every record. The agent proposes. | Everything. Today's behaviour. | Always available. |
| L1 | `agent_screens_you_audit` | The agent's EXCLUDE proposals stand as decisions. The researcher decides every agent INCLUDE, every Unclear, and a random audit sample of the agent's excludes. | Includes, Unclear, the audit sample. Agent excludes outside the sample are listed under a `decided` view labelled "agent". | A calibration on this review passes the L1 gate (§4). |
| L2 | `agent_autopilot` | The agent's proposals stand as decisions for every record it could decide. Unclear still goes to the researcher (an agent cannot make an Unclear record decided). | Unclear, plus an optional audit sample. | A calibration on this review passes the L2 gate, and the researcher types an acknowledgement at publish time (§7). |

Rules that hold on every rung:

- The agent never decides a record it marked `cannot_decide`, whose validators
  failed, or whose outcome is `MAYBE`. Those are the researcher's.
- The researcher may override any agent decision at any time; the override is
  a normal human event that supersedes the agent's.
- A protocol change (fingerprint) resets the review to L0 and invalidates the
  calibration, because the agent was measured against criteria that no
  longer exist.
- Changing the agent task version or model invalidates the calibration too.
- The mode is a journaled setting change, as every setting is today.

## 4. The calibration gate

A calibration compares the agent's latest proposals with the researcher's own
decisions on records decided **before** the draft was revealed (the agreement
route already knows which those are). The numbers below are proposed defaults;
each is a setting with a floor the engine refuses to go under.

| Gate | Records compared (min) | Include recall (point) | Include recall (95% CI low) | Missed includes allowed |
|---|---|---|---|---|
| L1 | 100, or the whole corpus when it has fewer than 200 records, never fewer than 50 | ≥ 0.95 | ≥ 0.90 | ≤ 2 |
| L2 | 200, never fewer than 100 | ≥ 0.98 | ≥ 0.95 | ≤ 1 |

Why recall of includes and not agreement: an agent that excludes a relevant
study costs the review a finding; an agent that includes an irrelevant one
costs the researcher one full-text read. The gate is one-sided on purpose.

The researcher reaches the gate by screening normally at L0 with blinding on
(the default) until enough records are decided, then running one calibration
over them. The agreement screen (spec 07) shows the gate as a bar: "73 of
100 compared; recall 0.96; the next rung needs 27 more records".

The audit sample at L1 is drawn at random from the agent's excludes at the
time the mode is set, sized by `sample_audit_size` (default 60: enough to see
at least one miss with 95% probability when the true miss rate is 5%). A
missed include found in the audit is reported on the Home card and in the
methods paragraph; the researcher chooses whether to drop to L0. The engine
does not drop the mode by itself, because a mode change mid-review is a
methods statement the researcher must own.

## 5. Provenance: how an agent decision is recorded

Two options were considered.

**A. Agent decision events.** The intake accepts a second method,
`AGENT_ADOPTED`, with `screener_id` = `agent:<model>`, a `proposal_id`, and an
`adopted_under` block naming the mode, the calibration run that unlocked it,
and the human who set the mode. Everything downstream (winners, conflicts,
PRISMA counts, export rows) keeps working because a record still has one
decision event.

**B. Adoption as one event.** The human's act "adopt the agent's proposals
for this scope" is a single journaled event, and the projection treats the
proposals it covers as decisions. Fewer events, but every consumer of
decisions must learn to look in two places, and the per-record export row
has no event to point at.

**Recommendation: A.** It is a contract change (the event schema gains a
method value and an optional block), so per the Contract v1 rules it needs an
architecture decision, regenerated schemas and golden fixtures, a negative
regression test (an `AGENT_ADOPTED` event without `adopted_under` is refused,
and one sent by a client is refused: only the engine mints them), and an
independent review. The engine mints these events in one place, when the mode
is set and when new proposals land under an active mode; a client can never
post one.

The PRISMA `human_provenance` check becomes `provenance_declared`: every
winner is `HUMAN`, or `AGENT_ADOPTED` under a mode the settings history shows
was active at that time. A new check `agent_decisions_disclosed` fails when
the methods paragraph does not state the agent's share.

## 6. API changes

Routes (all desktop-scoped; the phone keeps its read and decide scope):

- `GET /api/v1/screening/autonomy`: `{level, mode, gates: {L1: {...}, L2: {...}}, calibration: {run_id, compared, include_recall, ci_low, missed_includes, valid: bool, invalid_reason}, audit: {size, drawn, decided, missed_includes}}`.
- `PUT /api/v1/screening/settings` with `mode`: refuses `AUTONOMY_NOT_EARNED` (409, details = the failing gate numbers) unless the matching gate passes on a valid calibration; `agent_autopilot` also needs `confirm_autopilot: true`. Setting a lower mode is always allowed. The current `confirm_ai_agreed_exclusion` and the value `ai_agreed_exclusion` are retired (migration: an existing `ai_agreed_exclusion` setting reads as L0 with a journal note).
- `POST /api/v1/screening/proposals/adopt` is **not** exposed: adoption happens inside the engine when the mode is set and when a proposal run finishes under an active mode. This keeps "only the engine writes decisions for the agent" true.
- `GET /api/v1/screening/queue?view=audit_sample`: the sample at L1/L2.
- `GET /api/v1/screening/summary` gains `by_method: {HUMAN, AGENT_ADOPTED}` and `autonomy_level`.
- `GET /api/v1/screening/export` rows gain `method` and `adopted_under` (already in the event). `GET /methods` gains the sentences in §7.
- Refusal codes to register: `AUTONOMY_NOT_EARNED`, `CALIBRATION_INVALID`, `AUTOPILOT_NOT_ACKNOWLEDGED`, `AGENT_EVENT_FROM_CLIENT`.

Engine:

- `screening/autonomy.py` (new): gate evaluation, calibration validity (protocol fingerprint, task version, model), audit sampling with a recorded seed, adoption (minting `AGENT_ADOPTED` events from proposals).
- `screening/events.py`: accept the second method only when `adopted_under` is present and the call comes from the engine path (the HTTP intake keeps refusing it).
- `screening/export.py`: the methods sentences and the per-method counts.
- `console/api/screening_v1.py`: the routes above; the mode validation moves to `autonomy.py`.

## 7. What the researcher sees

- **Home** (spec 01): one card "Autonomy", showing the rung, the gate bar, and
  the next step in one sentence ("Screen 27 more records with the draft
  hidden, then run a calibration"). At L1/L2 it shows "Agent decided 412,
  you decided 58, audit: 60 drawn, 2 to go, 0 misses".
- **Agreement** (spec 07): the gate numbers and the "Unlock L1" button, which
  opens Settings with the mode preselected.
- **Settings**: the three modes as radio buttons with their gate state;
  locked ones say why.
- **Triage** (specs 03/04): unchanged. The queue simply contains fewer
  records. A record decided by the agent shows "Decided by the agent under
  L1 on 12 Nov; override" in the details disclosure (spec 12).
- **Publish** (spec 09): at L2 a typed acknowledgement, "This screening was
  done by an automated classifier; I take responsibility for reporting it",
  the same pattern as the replace-with-screening confirmation.
- **Methods paragraph** (spec 10), new sentences, in this order: "An automated
  classifier (model, task version) screened N records under mode X from
  date; it was calibrated on M records the reviewer had screened blind, with
  include recall R (95% CI low L). The reviewer screened every proposed
  include and unclear record and audited a random sample of S agent
  exclusions, finding K missed includes." At L0 nothing changes.

## 8. The discovery assistant (Phase 1)

Three bounded tasks, each a versioned task per the agent-system decision,
each producing proposals the researcher accepts verbatim, none deciding
anything:

1. **Synonyms**: from the protocol's concepts, propose synonyms, spelling
   variants and MeSH headings per concept; accepted ones are written into
   `search_strategy.core_concepts[].synonyms` by the engine (a protocol
   change, so the fingerprint moves and the plan dry run shows the new
   translations). Where: inception Criteria step pattern, reused on the
   discovery Plan screen.
2. **Translation explanations**: for each database row of the plan dry run,
   one plain sentence on what was sent and what could not be expressed
   (the `cannot_express` list already exists; the task only phrases it and
   proposes an alternative when a filter is missing, e.g. a language limit
   applied at screening instead).
3. **Recall repair**: when the recall check misses a golden seed, propose the
   smallest query change that would find it (a synonym, a dropped operator,
   a wider year), as a proposal the researcher applies through the plan.

MCP first (the researcher's Claude Desktop), in-app second, like screening.
No autonomy rung applies: these are protocol edits, and the protocol is the
researcher's.

## 9. Decisions taken (researcher, 2026-11-10)

1. **Provenance model**: A. One `AGENT_ADOPTED` event per record, minted by
   the engine only, carrying the proposal, the mode, the calibration run and
   the human who set the mode. A client can never post one. Contract change
   through the baseline gate and an independent review.
2. **L1 gate**: at least 100 blind decisions compared (the whole corpus
   under 200 records, never fewer than 50), include recall ≥ 0.95, 95% CI
   low ≥ 0.90, at most 2 missed includes.
3. **Autopilot (L2)**: designed and gated (200 compared, recall ≥ 0.98, CI
   low ≥ 0.95, ≤ 1 miss, typed acknowledgement at publish) but built only
   after the IEEE measurement. The first release ships L0 and L1.
4. **Audit sample**: 60 random agent excludes, fixed; the 10%-of-excludes
   figure is shown as advice.
5. **Protocol change**: drops the review to L0 and invalidates the
   calibration.
6. **Missed include in the audit**: the researcher decides; the Home card
   and the methods paragraph report it; the engine never changes the mode on
   its own.
7. **Names**: "Agent screens, you audit" (L1) and "Autopilot" (L2).

## 10. Milestones and order

| Milestone | Content | Lane | Needs |
|---|---|---|---|
| M9a-measure | Run the screening agent on the IEEE corpus against the researcher's decisions; record recall, cost, truncations; decide the thresholds from data. | STANDARD | Approved live spend, the researcher's key. |
| M9b-ladder-engine | §5 contract change, `autonomy.py`, gates, adoption, audit sample, methods sentences, export fields, refusal codes, fixtures. | RELEASE | Decisions 1–6. |
| M9c-ladder-ui | Home card, Agreement gate, Settings modes, publish acknowledgement, details disclosure line. Specs first (01, 07, 09, 10, 12 amended). | STANDARD | M9b. |
| M9d-discovery-assistant | The three tasks of §8 over MCP, then in-app. | STANDARD | M3c-screens merged. |

Nothing here starts before M3c-screens lands and the IEEE measurement exists.
