# H-adopted-decisions-disclosure

Status: **BUILT 2026-11-23 on `dev/h/adopted-decisions-disclosure`, not pushed (see "Build 2026-11-23" below); the build's own choices are PROPOSED. Specification: questions 1 to 6 answered by the researcher on 2026-11-22, each as recommended.** The build starts after M12a Part F is ready for its PR, in a session of its own (the researcher's answer, same day). Lane proposed: **RELEASE** (a new persisted record, a new route, a changed publication check and a changed methods text). Written by the main session on 2026-11-22 at the researcher's request, after the walk of the published sensor-stress review. The start of any build is the researcher's to approve separately.

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
4. The methods text never says "screened every record" when a declaration exists; a test pins its sentences in English (the paragraph stays English, spec 10 decision 5), and a test pins the Export screen's declaration figures and their labels in en, fr and ar. *(Reworded 2026-11-23 on the researcher's answer "English paragraph (Recommended)"; decision item 22. As first written: "a test pins the sentences in en, fr and ar".)*
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

## Build 2026-11-23

Status: **BUILT on `dev/h/adopted-decisions-disclosure` (from `main` `9b2e0d5f`); not pushed. DoD 1 to 6 met (DoD 4 as reworded on the researcher's answer of 2026-11-23, decision item 22).** Lane: RELEASE (item 7). Built in a session of its own, started by the main session on the researcher's approval of 2026-11-23. The build's own choices are items 7 to 29 of the decisions entry "2026-11-23 — H-adopted-decisions-disclosure: the build's own choices": item 22 answered by the researcher, the others PROPOSED.

**What was built.**

- **Engine** (`src/scholar_harness/screening/adoption.py`, new). The append-only `audit/adoption_declarations.jsonl` with three kinds of line (declaration, withdrawal, sample result), each written with one journal row naming the line's id and SHA-256; a line the journal does not confirm is not applied, a recorded line missing from the file is reported (item 10). The reader, the state over the current winning decisions (declared, candidates by the note's wording, samples, what is owed), the three writes, and the lookup of declared events in a round's decision files (charting).
- **Routes** (`console/api/screening_v1.py`): `GET /screening/adoption-declarations` (a display route), `POST /screening/adoption-declarations`, `/withdrawals`, `/sample-results`, desktop only (the phone scope guard), in the browser allowlist and the development proxy's, `confirm: true`, under the events lock; six refusal codes (`console/refusals.py`, the contract's §7 and §4 tables).
- **Agreement** leaves declared decisions out of every figure and returns `adoption`; **Publish** renames the provenance detail, adds the advisory check `adopted_decisions_declared` and returns `adoption`; **summary** returns `adoption: {declared, undeclared_candidates}`.
- **Methods** (`screening/export.py`): the counts sentence instead of "One reviewer screened every record.", one sentence per sample or that none was read, "Drafts were advisory for the records the reviewer read one by one.", `figures.adoption`, the file among the sources, and the after-publication note (answer 5).
- **Charting** (`charting/table.py`): rows carry `ta_adopted`; the one-study view shows the phrase beside the title-and-abstract decision.
- **UI** (`apps/research-ui`): the declaration screen `/{locale}/screening/adopted` (`components/screening-adopted.tsx`), the shared copy `lib/adoption-copy.ts` (en, fr, ar), Agreement's sentence and sample box, Publish's "Look at this" (amber, outside the publish gate) with its sentence and link, Home's settings line, Export's declared figures and note, the charting badge, state cards for the six codes.

**Evidence.**

| DoD | Test | Result |
| :-- | :-- | :-- |
| 1 | `tests/console/test_adoption_declarations_api.py`: `…without_confirm…` (`ADOPTION_CONFIRM_REQUIRED`, nothing written), `…from_a_phone…` (`TOKEN_SCOPE_REFUSED`), `…not_a_current_winning_decision…` (superseded and unknown, `ADOPTION_EVENT_NOT_WINNING`), `…same_record_twice…` (one request and a second declaration, `ADOPTION_ALREADY_DECLARED`), `…another_origin…` (`CONSOLE_ORIGIN_REFUSED` on the browser surface), `…cannot_choose_who_or_when` | pass |
| 2 | `test_agreement_excludes_declared_decisions_and_says_how_many` (the three-record fixture: 3 compared before, 1 after declaring 2) | fails on `9b2e0d5f` (no route; the figure counted the adopted decisions), passes on the build |
| 3 | `test_the_publish_checks_are_renamed_and_the_declaration_check_does_not_block`, `test_with_no_candidate_the_declaration_check_passes` | pass |
| 4 | `tests/console/test_adoption_methods_charting.py`: the sentences pinned in English, no "screened every record", no "every decision … made by the reviewer", every number a figure, the sample unread then read, a declaration after publication (paragraph changed, note added, `included.json`, `excluded.json`, `prisma_report.json` and the RIS export byte for byte unchanged); `apps/research-ui/tests/screening-adopted.test.tsx` "adoption.export" pins the Export labels in en, fr and ar | pass (DoD 4 as reworded; the paragraph stays English, item 22 answered) |
| 5 | `uv run python scripts/generate_contract_baseline.py --check` | "Contract baseline current", no regeneration |
| 6 | `apps/research-ui/tests-browser/screening-adopted.spec.ts` (the flow in en: offered, nothing sent, focus in the dialog, axe clean, one POST with `confirm: true` and the sample, then Agreement; the screen in fr and ar with axe), both themes; `tests/screening-adopted.test.tsx` (18 tests) | pass |
| Item 6 | `test_a_kept_study_declared_as_adopted_shows_it_in_the_charting_table` (table and one-study read); UI badge copy in three locales | pass |
| Read store | `test_the_next_display_request_sees_a_declaration` (Publish's check and the summary, both kept by display routes, change on the next request after a declaration and after a withdrawal) | pass |
| Integrity | `test_a_line_typed_into_the_file_is_not_applied_and_a_removed_line_is_reported`, `test_a_withdrawal_is_a_later_line_and_the_declaration_stays`, the events files byte for byte unchanged after a declaration | pass |

Gates:

| Gate | Where | Result |
| :-- | :-- | :-- |
| Tests written first | the 22 API, methods and charting tests on `9b2e0d5f` with only `adoption.py` present | 21 failed, 1 passed (the phone refusal, already held by the scope guard) |
| Lint as CI | `uv run ruff check scripts/`; `uv run ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9` | clean, on `c9530ced` |
| Contract v1 | `uv run python scripts/generate_contract_baseline.py --check` | "Contract baseline current", on `c9530ced`; never regenerated |
| Screening API fixtures | `tests/console/test_screening_api_contract.py` after `generate_screening_api_fixtures.py` | 6 passed; three fixtures changed (item 27) |
| Full Python suite, once | `uv run pytest -q -n 4 -p no:cacheprovider` on `ea0b8a20` | exit 0: 6,597 passed, 15 skipped, none failed (counted from the progress lines only; pytest printed no summary line; first recorded as 6,605 and 31, a count that took in characters of the warnings text, corrected after review round 3) |
| Full Python suite on the final code | `uv run pytest -q -n 4 -p no:cacheprovider` on `71d81097` (review round 2, P2) | exit 0: 6,599 passed, 15 skipped, none failed; `pytest --collect-only` collects 6,614, the same total (checked by the reviewer) |
| After review round 1 | the affected files (`test_adoption_*`, `test_methods_api`, `test_methods_method_block`, `test_export_api`, `test_criteria_pilot_api`), `-n 4`, on `c9530ced` | 113 passed |
| Typecheck | `npx tsc --noEmit` | clean, on `c9530ced` |
| UI unit tests | `npx vitest run` | 1,459 passed on `ea0b8a20`; on `c9530ced` 1,459 passed and 1 failed in `tests/inception-workbench.test.tsx` ("a refused cost read…", "no refusal yet"), a file this build does not touch; it passed 3 times of 3 run alone (a wait under load) |
| Browser | `npx playwright test` of `screening-adopted`, `screening-export`, `screening-states`, `charting-study`, `hydration` (both themes) | 66 passed, 4 skipped, on `ea0b8a20`; `screening-adopted.spec.ts` again on `c9530ced` (after the Agreement change): 6 passed; no committed screenshot changed |


**Review.** `milestone-reviewer`, independent, two rounds.
- Round 1 (on `ea0b8a20`): CHANGES. P2: the methods draft sentences still counted declared decisions as blind or revealed; the contract rows of `/summary`, `/prisma/preview`, `/agreement` were not updated (a client gating on `all(ok)` would block on the advisory check); no gate evidence. P3: Home still said "you see every record" beside the declared count; Agreement said "You saw every record" beside undeclared candidates. All five fixed in `c9530ced` (items 19, 20 amended, item 29 added).
- Round 2 (on `c9530ced`): CHANGES on evidence only, "the code findings are resolved and nothing in the code needs to change"; the full suite had to run once on the final code commit, which it did on `71d81097` (above). Its P3 suggestion (a test of the "drawn outside the app" sentence) is in `71d81097`.
- Round 3 (on `eb2ff3c9`): **APPROVE**. One P3: the suite counts in this table were miscounted; corrected here.
- Follow-ups the reviewer left as P3, not changed: a crash between the line and its journal row leaves an unconfirmed line with no repair path (only an `OSError` from the journal append is rolled back); the sample seed is drawn in the browser (the pilot's is drawn by the engine); a sample stays owed after every decision of its declaration is withdrawn or decided again; Agreement builds a candidate list it discards; a citation-chasing round's charting match is untested beyond round 1; `read_ledger` reads the whole journal on each read that is not kept.

**Not verified.**

- On the sensor-stress review itself: the build did not read the researcher's workspaces (not allowed). Whether its 996 notes all match the candidate wording (item 8) is not checked; the notes quoted in the acceptance-run record match.
- The two samples drawn there (50 and 20) are to be recorded with their study ids (item 14); not tried.
- With 1,000 candidates: the declaration screen's list and the agreement and publish reads were not timed on a review of that size (the fixtures hold three records).
- The browser test answers the console with a fake of the engine's shapes; the engine's answers are covered by the Python tests, not by a browser run against the real engine.
- Screens looked at only through the tests (text, roles, axe); no screenshot was reviewed by a person.
