# H-adopted-decisions-disclosure

Status: **SPECIFICATION; questions 1 to 6 answered by the researcher on 2026-11-22, each as recommended; nothing built.** The build starts after M12a Part F is ready for its PR, in a session of its own (the researcher's answer, same day). Lane proposed: **RELEASE** (a new persisted record, a new route, a changed publication check and a changed methods text). Written by the main session on 2026-11-22 at the researcher's request, after the walk of the published sensor-stress review. The start of any build is the researcher's to approve separately.

Findings it answers: 43 and 44, with 40 and 41 behind them (`docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md`).

## The problem, in the app's own code

On the sensor-stress review, 996 of 1,062 decisions were stored in bulk from the agent's drafts, as `method: HUMAN` events with a free-text note. The app then states three things that are untrue for that review:

| Screen | What it says | Why (checked at `main` `db7f47a3`) |
| :-- | :-- | :-- |
| Publish | "Every decision is a human decision": Passes | `human_provenance` is `all(method == "HUMAN")` (`console/api/screening_v1.py:964-969`); the intake refuses any other method (`screening/events.py:436-439`), so it can never fail |
| Agreement | "You and the agent agreed on 99.9% of records" | a decision counts as blind when no reveal was recorded for the study (`screening_v1.py:1515-1519`); a script never triggers a reveal, so adopted decisions count as blind agreement: the agent agreeing with itself |
| Agreement | "You saw every record. No sample needed." | shown whenever the mode setting is not `ai_agreed_exclusion` (`screening-agreement.tsx:274-280`); no decision is consulted |
| Methods text | "One reviewer screened every record." | emitted when every entry is HUMAN with one `screener_id` (`screening/export.py:772-780`); nothing reads the note |

Nothing in a decision event says "this was adopted from a draft without being read": `note` is free text and `proposal_shown` is set by the client and says only that a draft was in view.

## What is already decided, and what this does not replace

The ladder decision of 2026-11-10 (`docs/decisions.md`, "Agent autonomy ladder"; `docs/architecture/agent_autonomy_ladder.md` §5) is the designed answer for decisions the agent makes under a gated mode: one `AGENT_ADOPTED` event per record, minted by the engine only, a Contract v1 change, with `human_provenance` replaced by `provenance_declared` and `agent_decisions_disclosed`. That is M9b, not started, and waits on the calibration gates.

This specification is narrower and comes first: **an honest disclosure for decisions that are already stored as HUMAN**, on this review and on any other where a researcher adopts drafts outside a gated mode. It adds no way to adopt in bulk from the app (findings 40 and 41 stay with M9b), and it does not touch the Contract v1 `ScreeningDecision` model or its schema.

## Proposal

**1. A declaration the researcher records.** A new append-only file `audit/adoption_declarations.jsonl` beside the journal. One line declares a set of decision events as "stored from the agent's draft without my reading each record": the event ids, the outcome counts, who declares it, when, an optional note, and the sample drawn from it if any (size, seed). A declaration cannot be removed; a later line may withdraw records from it by naming them ("I have since read these"). The existing events are not rewritten.

**2. How it is made.** `POST /screening/adoption-declarations` (desktop only, the same cross-site guard as the method amendments), with `confirm: true`. The screen offers the candidate set, it does not guess silently: the decisions whose note says they were adopted or stored in bulk, shown as a count with a way to list them; the researcher confirms or edits the set. On the sensor-stress review that is the 996.

**3. What the screens then say.**
- **Agreement:** declared decisions leave the agreement figure. The page says "{n} decisions were stored from the agent's draft without being read one by one; they are not counted here." "You saw every record. No sample needed." is shown only when there is no declaration and the mode is the default; with a declaration the box reads "A sample of {k} adopted exclusions is owed" until a sample result is recorded.
- **Publish:** the check is renamed "Every decision is recorded as the reviewer's" (it is all the engine can know), and a second check is added, "Decisions stored from drafts are declared": Passes with no candidates or with every candidate declared; "Look at this" when undeclared candidates exist.
- **Methods text:** "One reviewer screened every record" is replaced, when a declaration exists, by sentences with the counts: how many records the reviewer read, how many decisions were stored from the agent's drafts and by which outcome, and what the sample found or that it was not read.
- **Charting:** a kept study whose inclusion was declared as adopted shows it beside the title-and-abstract decision (finding 49).

**4. This review.** Nothing is migrated. After the build the researcher records the declaration on the sensor-stress workspace, which makes the published generation stale by the existing rule only if question 5 says so.

## Definition of done (proposed)

1. A declaration is refused without `confirm`, from a phone, for an event id that is not a current winning decision, and twice for the same record; each refusal has a code and a test.
2. With the two-study fixture plus a declared set, Agreement's figure excludes declared decisions; the test fails on today's code.
3. The Publish check for undeclared candidates is "Look at this" on a fixture holding bulk-noted decisions and Passes after the declaration.
4. The methods text never says "screened every record" when a declaration exists; a test pins the sentences in en, fr and ar.
5. The contract baseline check stays current with no regeneration.
6. A browser test of the declaration flow; copy in en, fr and ar.

## Questions closed (2026-11-22)

Asked in the main session, one by one; each answered as recommended. Decision: `docs/decisions.md`, "2026-11-22 — H-adopted-decisions-disclosure".

1. **A declaration now**, not a wait for M9b's `AGENT_ADOPTED`. Known cost: two mechanisms for a while; M9b must read declarations too.
2. **Candidates are found by the note's wording**, offered for confirmation, never applied silently. Known cost: a review whose bulk notes are worded differently offers nothing, and the researcher declares by filter (date range, batch). *Not chosen:* timing; both.
3. **An undeclared candidate does not block publication**: "Look at this" only. *Not chosen:* block until declared or dismissed with a reason.
4. **An owed sample does not block publication**; it is stated on Agreement, on Publish and in the methods text. Known cost: a review can be published with the sample unread. *Not chosen:* block.
5. **A declaration on a published review makes only the methods export out of date**; `included.json` and `excluded.json` stay as published. *Not chosen:* the whole generation stale.
6. **The phrase is "stored from the agent's draft without being read one by one"**, in all four places. *Not chosen:* "adopted from the agent's draft"; "accepted in bulk on the agent's recommendation".

## Not verified

Line references were gathered by a read-only search on 2026-11-22 and not each re-read by the main session. No design was tested against the engine. Whether the notes on the sensor-stress events are uniform enough for question 2 was not checked on the workspace.
