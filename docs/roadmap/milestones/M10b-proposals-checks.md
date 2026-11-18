# M10b Proposals and checks
Branch: dev/m10b/build (from `dev/m10b/proposals-checks` at `2d07228d`, with `origin/main` at `e7644a6c` merged) · Lane: **RELEASE** (declared 2026-11-18: new public routes and answer fields, new refusal codes, new `Draft` fields that an older engine refuses, `audit/proposals.jsonl` and `audit/check_dismissals.jsonl` in the preview's `files`, and a changed accept path on the Import step; per `docs/architecture/test_gate_policy.md`) · Status: **Part A MERGED** (PR #240, merge commit `6e39b00a`, 2026-11-18; reviewer APPROVE on `dcb85d07`; decision items 21, 25 and 26 accepted 2026-11-18) · Part B started 2026-11-18 on a new branch from `main` · Parts C, D not started · Started: 2026-11-14

Second milestone of the "Assisted inception" sequence the researcher approved on
2026-11-14 (M10a search quality, **M10b proposals and checks**, M10c assistant and
critic over MCP, M10d lighter screens, M10e in-app chat). M10a
(`dev/m10a/search-quality`) runs in parallel and adds the plan §6 rows and the
`docs/decisions.md` entries; this branch does not edit `production-plan.md`,
`docs/decisions.md`, or the specs M10a amends (inception `01-scope`, `02-explore`,
`03-direction`; discovery `01-plan`, `03-harvest`).

**Split (researcher, 2026-11-18).** The build ships as four PRs, in this order:
Part A (draft answers and start from a protocol), Part B (proposals and checks),
Part C (next-step bar, Import link, Explore sample curation, Explore empty-search
fixes), Part D (size estimate). Part D starts after the search-provider resilience
session merges, because its count request touches `src/scholar_search/providers/*`.
Each PR names the Build items it closes.

Source of the scope: the strict UAV acceptance run of 2026-11-13 (the researcher
typed every question, concept, synonym and criterion by hand; every exclusion was
labelled `OUT_OF_SCOPE`; only three matrix columns could be chosen; 1,050 works
were harvested against a planned 150 to 300; nothing on Discovery pointed to the
Hand-off) and the researcher's requests of 2026-11-14 (a critic on every step,
less text on screen, an assistant that proposes).

## Design (proposed by the main session; the specs detail it)

### One proposal object
Everything that suggests a change to the researcher's draft or protocol is a
**proposal**. Sources in M10b: a fixed check (`check:<id>`), an imported protocol
(`import:<name>`). In M10c: an agent task (`agent:<model>`, task name and version).
In M10e: the chat. No language model is used in M10b.

| Field | Meaning |
| :-- | :-- |
| `proposal_id` | stable id |
| `target` | where it applies: an inception draft (`rec_…`) or a workspace, plus the field (`concepts`, `concepts[<concept>].synonyms`, `rqs`, `extra_inclusions`, `extra_exclusions`, `golden_seeds`, `matrix_columns`, `start_year`, …) |
| `op` | `add`, `replace` or `remove` |
| `value` | the exact value that would be written |
| `why` | one sentence, shown on the card |
| `evidence` | what supports it: DOIs, counts, the check id |
| `source` | who proposed it (see above) |
| `base` | what the target looked like when it was proposed; if the target has changed since, the proposal is `stale` |
| `status` | `open`, `applied`, `applied_edited`, `rejected`, `stale` |
| `decided_at` | when the researcher decided |

Rules:
- Nothing is applied without the researcher's click. A proposal is never pre-ticked.
- Apply goes through the same validation as a manual edit of that field. Edit opens
  the value in the field's normal editor and applies what the researcher saves.
- Every proposal and its decision is recorded: with the draft before genesis and in
  the workspace's audit trail from genesis on, so the methods text can say what was
  proposed by a check or an agent and accepted by the researcher.
- The engine-written suggestions that exist today (wizard criteria, synonym
  suggestions from the pool, suggested concepts, suggested matrix columns,
  direction proposals, anchor papers as seeds) keep their fields in M10b and adopt
  the same card. They are not migrated to the proposal store in this milestone;
  when the researcher accepts one, a write-only record with the source
  `engine:<mechanism>` is kept (R1, 2026-11-15).
- An assistant never accepts a corpus, makes a screening decision or publishes
  (accepted decision, 2026-11-14).

### Fixed checks (no AI)
Each step has a list of checks the engine computes from the draft, the pool and the
run. A check has an id, a level (`blocker` only where a refusal already exists
today, otherwise `warning` or `note`), one sentence, a "why" behind an icon, and one
recommended action: a link to the field, or a proposal. A warning can be dismissed
with a reason, which is recorded. The Review step lists every open check
("ready to create" or what is still open). M10c adds the agent critic as a second
source in the same list.

### Other items in this milestone
- **Start from an existing protocol**: begin an inception from a workspace's
  protocol or a protocol file, without AI.
- **A reason category for each exclusion**, including the out-of-scope lines.
- **The researcher's own matrix columns.**
- **A size estimate before a harvest**, with a suggested cap.
- **A "what's next" bar** on every screen of a review, computed by the engine.
- **Removing a paper from the Explore sample.**
- **The guidance rules for lighter screens** (M10d builds them): help behind an
  icon, one main action per step, the recommended choice marked, and a per-screen
  list of what stays visible.

## Definition of done
### Specs (this stage)
- [x] `docs/ux/shared/final/01-proposals.md`: the proposal object, card, list, storage, API and record.
- [x] `docs/ux/shared/final/02-checks.md`: the checks panel, the catalogue of checks per step (51 when written; 50 since `SCOPE_TOPIC_LONG` was dropped on 2026-11-18) with their thresholds, dismissal, readiness on Review.
- [x] `docs/ux/shared/final/03-guidance.md`: hint, recommended mark and density rules, with the per-screen audit for inception 01 to 07 and discovery 01 to 09.
- [x] `docs/ux/shared/final/04-next-step.md`: the "what's next" bar and its state table.
- [x] `docs/ux/phase0-inception/final/09-start-from-protocol.md`.
- [x] `docs/ux/phase0-inception/final/05-criteria.md` amended: exclusion reasons, own matrix columns.
- [x] `docs/ux/phase0-inception/final/04-shape.md` amended (added 2026-11-15 by R3 and R4): the planned number of records, the optional proof answer.
- [x] `docs/ux/phase0-inception/final/10-sample-curation.md`: removing a paper from the sample (folded into `02-explore` after M10a merges).
- [x] `docs/ux/phase1-discovery/final/10-size-estimate.md` (folded into `01-plan` after M10a merges).
- [x] The researcher has closed every open question (2026-11-15, "accept all"); each spec says `Status: FINAL`. The specs were written by seven writers and reconciled by the main session; no independent reviewer has read them.

### Spec pass after M10a and M3i (2026-11-18)
- [x] S1 `10-sample-curation` folded into `docs/ux/phase0-inception/final/02-explore.md` "Sample curation (M10b)" and `10-size-estimate` into `docs/ux/phase1-discovery/final/01-plan.md` "Size estimate (M10b)" (with a pointer section in `03-harvest.md`); both files deleted and every reference updated.
- [x] S2 The decisions written into `docs/decisions.md` (entry "2026-11-15 — M10b", items 1 to 17; 12 to 17 proposed, not yet accepted).
- [x] S3 `docs/ux/phase2-screening/final/11-import-corpus.md` amended: "Accepting on the Hand-off (M10b, R6)".
- [x] S4 `EXPLORE_SAMPLE_ONE_SOURCE`: its test text and "why" rewritten for M10a's spread sample (`02-checks`).
- [x] S5 Guidance audit recounted for Explore (I-E6, I-E37 to I-E43) and Harvest (D-H13, D-H17 to D-H23); totals inception 96 / 34 / 11 (141), discovery 90 / 32 / 15 (137), checked by counting the rows.
- [x] S6 Reconciled with M3i (merged): `04-next-step` reads `preparation` (rows 13, 14, B to D, G, I, J; "Finish preparing this corpus"; "What M3i settled"); the hand-off check is `HANDOFF_PREPARATION_UNFINISHED` with the refusal `PREPARATION_UNFINISHED`; the Hand-off stays the one place to accept.
- [x] S7 `05-criteria`'s two check working names reconciled to the catalogue's `CRITERIA_REASONS_UNIFORM`.
- [x] S8 `milestone-reviewer` run once on the specs (no independent reviewer had read them); its findings fixed. The review returned CHANGES with 20 findings on 2026-11-18; the main session decided each and the specs were amended the same day (draft-save `accepted_from` instead of a record route; `SCOPE_TOPIC_LONG` dropped, 50 checks; one refusal rule for the new codes; one lock and `updated_at` rule for the draft record; `SEARCH_UNFINISHED` and a workspace-free next-step route without ETag; workspace proposal routes deferred to M10c; reason codes checked on save only; the UAV rebuild carries the 13 own columns; the guidance audit recounted for Plan, Hand-off and Chase: inception 96 / 34 / 11 (141), discovery 95 / 34 / 15 (144)). Decisions items 18 to 26 in `docs/decisions.md` (18 accepted by the researcher; 19 to 26 proposed).

### Build (definition of done; each item names its tests; a strict-run finding gets its reproducing test first)
Rules for every item (2026-11-18):
- **A new POST route** is added to both POST allow-lists in the same change: `POST_PATHS` in `src/scholar_harness/console/browser.py` and the list in `apps/research-ui/app/api/console/[...path]/route.ts`; the browser allow-list test names it.
- **A new refusal code** is registered in `src/scholar_harness/console/refusals.py` and in `docs/architecture/screening-api-contract.md` §7 (kept equal by `tests/console/test_console_refusals.py`), and documented in `docs/architecture/inception-api.md` when an inception route answers it. Never in `docs/architecture/refusals.md` (the generated, closed `Envelope@1` registry).
- **A write to the draft record** follows the lock and `updated_at` rule of `01-proposals` "Where a proposal is kept".

Part A, the draft's answers (Shape, Criteria, Review) and starting from a protocol:
- [x] A1 Planned number of records (`04-shape` "How many records you plan to screen"): `Draft.pool_min`, `pool_max`; `steps/shape` answers `pool_preset`; compiled into `target_candidate_pool_size`; Review's "Planned records" line; `inception-api.md` (Draft fields, `steps/shape`). Tests: `tests/inception/test_steps_planned_size.py`; `apps/research-ui/tests/inception-shape.test.tsx`. Built (`c36d9680`); the UI tests are in `apps/research-ui/tests/inception-answers.test.tsx` ("inception.shape planned records").
- [x] A2 Optional proof (`04-shape` "The proof answer may be empty"): `proof_required(draft)`; `steps/shape` answers `proof_required`; `inception-api.md`. Tests: `tests/inception/test_steps_proof_optional.py`; `inception-shape.test.tsx`. Built (`c36d9680`); UI tests in `inception-answers.test.tsx` ("inception.shape optional proof").
- [x] A3 Exclusion reason categories (`05-criteria` "Exclusion reasons"): `Draft.out_of_scope_reasons`, `default_exclusion_reason`, the code rule checked on save and create only (`parse_draft(saving=True)`; an older code is read and flagged `reason_valid: false`), `reason_suggestions`, the Reason combobox; `inception-api.md`. Strict-run finding 5. Tests: `tests/inception/test_criteria_reasons.py`; `inception-criteria.test.tsx`. Built (`c36d9680`); UI tests in `inception-answers.test.tsx` ("inception.criteria reasons"). The combobox is a native `list` input (a combobox by role) with the engine's suggestions as options.
- [x] A4 Own matrix columns (`05-criteria` "Own matrix columns"): `Draft.custom_matrix_columns`, `build_intent`, `steps/matrix` `custom_columns`; `inception-api.md`. Strict-run finding 6. Tests: `tests/inception/test_custom_matrix_columns.py`; `inception-criteria.test.tsx`. Built (`c36d9680`); UI tests in `inception-answers.test.tsx` ("inception.criteria own matrix columns").
- [x] A5 Review wording (strict-run findings 7, 8, 9): the rationale reads "Convincing evidence: …" (not "Convincing evidence is A primary…"); the suggested Sample Size column says "How many were sampled or evaluated (unit of analysis: …)"; concepts listed with their synonyms; no stray dot before the folder path. The placeholder protocol's pinned fingerprint moves once (decision item 26). Reproducing tests first: `tests/inception/test_review_wording.py` (the rationale sentence, the Sample Size column description); `apps/research-ui/tests/inception-review.test.tsx` (concepts with synonyms, no stray dot before the folder path). Built (`c36d9680`); the UI tests are in `inception-answers.test.tsx` ("inception.review wording").
- [x] A6 Start from an existing protocol (`09-start-from-protocol`): `POST /inception/drafts/import` and `…/origin/checked` (both in the two POST allow-lists), the screen, banner and step marks, the GENESIS description (the default summary plus one sentence naming the source), `origin.label` in the draft listing; the `IMPORT_*` codes in the console refusal registry, §7 and `inception-api.md`. Built with A4. Tests: `tests/console/test_inception_import.py` (the UAV rebuild included: the 13 own columns carried, no proof typed); `tests/console/test_console_refusals.py`; `apps/research-ui/tests/inception-import.test.tsx`. Built (`fd9af0da`), with two pieces of B1 and C1 that it needs: the per-draft lock (`DraftStore`, `update_side`) and `protocol_origin` (`emit_workspace`, `_refresh_manifest`, the placeholder scaffold). Not built here: the Review note `REVIEW_IMPORT_STEP_NOT_OPENED` (a check, B2). Browser scenario in `tests-browser/inception.spec.ts` ("starts from an earlier review"), and the import screen added to that file's axe, overflow and hydration loops.

Part B, proposals and checks:
- [x] B1 Proposal store, API and card (`01-proposals`): the four POST routes (apply, apply-edited, reject, restore) in both allow-lists; the draft `PUT`'s `accepted_from` and its `engine:<mechanism>` records (R1); the per-draft lock; genesis's `audit/proposals.jsonl` with `in_protocol` and the journal rows, written inside `steps.genesis`'s try block and added to `ARCHIVED_ON_REPLACE`; `protocol_origin` written by both genesis paths and by `_refresh_manifest`; the `PROPOSAL_*` codes in the console refusal registry, §7 and `inception-api.md`. The workspace proposal routes are M10c's. Tests: `tests/console/test_inception_proposals.py`; `tests/console/test_console_refusals.py`; `apps/research-ui/tests/proposals.test.tsx`. Engine built (`8976091e`): `inception/proposals.py`, `DraftStore.transact` (one locked write; answer writes check `base_updated_at` and bump `updated_at`, side writes do neither), the five routes, `accepted_from` judged on the stored draft (the reproducing case `test_accepted_synonym_is_recorded_although_no_longer_offered_after_the_save`), the bind's `engine:direction` record, genesis's `audit/proposals.jsonl` written before the GENESIS row (decision item 28), 31 tests (30 when first built). `protocol_origin` was built in Part A. UI (`dc48926c`): the per-step suggestion list and card on inception 01 to 06 (`components/inception-assist.tsx`, `lib/proposals-copy.ts`), stepper badges, `accepted_from` sent by the screens that accept the five save-time mechanisms, the `not_recorded` line; `proposals.test.tsx` 15 tests. Edit uses an inline editor in the card, not the field's own editor (deferred list).
- [x] B2 Checks engine (`02-checks`, 50 checks): the inception and discovery catalogues, dismissal and restore with the record (`check_dismissals`, `audit/check_dismissals.jsonl`, also in `ARCHIVED_ON_REPLACE`); the inception checks POST and the dismiss and restore POSTs (inception and discovery) in both allow-lists; the `CHECK_*` codes in the console refusal registry, §7 and `inception-api.md`; thresholds marked ⚑ run over the golden UAV workspace and the 2026-11-13 evidence, the result recorded here before they are frozen. Tests: `tests/console/test_inception_checks.py` (the Shape checks included), `tests/console/test_discovery_checks.py`; `tests/console/test_console_refusals.py`. Engine built (`8976091e`): `inception/checks.py` (the inception catalogue, the check object, dismissal, the list response) and `console/discovery_checks.py` (the discovery catalogue, computed from the answers the discovery routes serve), 41 and 25 tests (37 when first built; 4 dismissal-reopening cases added after the review). `EXPLORE_SAMPLE_MOSTLY_LEFT_OUT` waits for Part C's sample curation (decision item 31). Calibration below.
- [x] B3 Checks panel on inception 01 to 06 and discovery 01 to 06 and 08; Review's "Ready to create?" list replaces its Checks card. Tests: `apps/research-ui/tests/checks-panel.test.tsx`. Built (`dc48926c`): `components/checks-panel.tsx` (panel and readiness list), `discovery-checks.tsx`, `lib/checks-copy.ts`, step-bar badges; mounted on inception scope to review and on discovery plan, recall, harvest, dedup, report and hand-off (Import has no check, as the spec says); 18 tests (the spec's 17 titles and a discovery Recall case). Browser scenario in `tests-browser/inception.spec.ts` (a check proposes UAV, Apply, reload; dismiss with a reason, reload, restore; Review "Not ready" then "Ready to create"). Not built: the narrow-window collapsible panel and toast, a discovery browser scenario, read-only checks of an older run (deferred list). Old Review tests that read the Checks card now read the readiness list.

Part C, the what's-next bar, the Import link and Explore:
- [ ] C1 Next-step builder `console/next_step.py`; `GET /review/next-step`, workspace-free (added to `_workspace_free` in `console/serve.py`; it answers `NO_REVIEW` itself), and `GET /inception/drafts/{id}/next-step`, both without ETag; the bar in `AppShell`; `protocol_origin` in `project.json` (`placeholder` from the placeholder scaffold of `nexus-scholar init`; `inception` or `import` from both genesis paths and from `_refresh_manifest` on a replacement); the `08-handoff` amendment "The next-step bar (M10b)" (`04-next-step`). No new refusal code. Strict-run finding 11. Tests: `tests/console/test_next_step_api.py`; `apps/research-ui/tests/next-step-bar.test.tsx`.
- [ ] C2 The Import step links to the Hand-off (`11-import-corpus` "Accepting on the Hand-off"). Strict-run finding 11. Tests: the `screening-import` vitest file.
- [ ] C3 Sample curation (`02-explore` "Sample curation"): `reserve` and `POOL_SAMPLE` `relevance-2`, `effective_pool`, `GET`/`POST …/recon/sample` (the POST in both allow-lists), `SAMPLE_CHANGED`, `recon_context` `sample_exclusions`, the Papers card controls; `PAPER_UNKNOWN` and `SAMPLE_EXCLUSIONS_FULL` in the console refusal registry, §7 and `inception-api.md`. Tests: `tests/recon/test_effective_pool.py`, `tests/console/test_recon_sample_api.py`; `tests/console/test_console_refusals.py`; `apps/research-ui/tests/inception-sample.test.tsx`.
- [ ] C4 Explore on an empty search (`02-explore` "Explore on an empty search (M10b)"): "Databases asked" shown once on a `POOL_EMPTY` or `PROVIDERS_FAILED` refusal; the shorten advice only when the job error carries `details.shorten: true` (decision item 17). Reproducing tests first: the `inception-explore.test.tsx` cases and the engine test named in that section.

Part D, the size estimate (after the search-provider resilience session merges):
- [x] D1 `POST /discovery/estimate` (in both allow-lists), a count per database, the Estimate card on Plan and Harvest (`01-plan` "Size estimate"); `PACE_INVALID` in the console refusal registry and §7. The count request per database touches `src/scholar_search/providers/*`. Tests: `tests/console/test_discovery_estimate_api.py`, `tests/kits/search/test_provider_count.py`; `tests/console/test_console_refusals.py`; `apps/research-ui/tests/discovery-estimate.test.tsx`. Built on `dev/m10b/part-d-size-estimate` (head `5000433f`); see "Part D (size estimate)" below. Open: the live check of the count forms (Part D deferred).

Every part:
- [ ] Copy in en, fr and ar for every new key (the N9 guard and the copy tests pass). **Part A: done** (FR and AR are typed `Record<InceptionCopyKey, string>`, so the type check fails on a missing key; `inception-copy.test.ts` and the N9 guard pass). **Part B: done** (`lib/proposals-copy.ts`, `lib/checks-copy.ts`, the 10 refusal cards in `lib/screening-states.ts`; FR and AR typed against the EN keys). Parts C, D: open.
- [ ] `/gate pr` once on the final executable commit of the part, `generate_contract_baseline.py --check`, `git diff --check`, `milestone-reviewer` APPROVE. **Part A: done** (pr gate on `a1ef6122`, the final executable commit; baseline current; diff check clean on `dcb85d07`; reviewer APPROVE on `dcb85d07`). Parts B, C, D: open.

### Calibration of the ⚑ thresholds (Part B, 2026-11-18)
Run over the data on this computer before freezing. The 2026-11-13 strict-run evidence is on the second computer and was **not** available, so the thresholds that only that run can test are kept at the spec's first values and marked unverified.
| Check | Data | Result | Kept |
| :-- | :-- | :-- | :-- |
| `CONCEPT_TERM_MISSING`, `PLAN_QUERY_TERM_MISSING` (term rule) | `golden-uav-30` and `uav-crop-weed-v03` protocols | the title-word half flagged only "reliability" and "generalization" (outcomes, not search words) on both; the acronym half flagged nothing (UAV is a concept there) and finds the 2026-11-13 case in tests | acronyms only (decision item 27, proposed) |
| `HANDOFF_ABSTRACTS_MISSING` (0.8) | `golden-uav-30` `verified.json` (30 works) | abstract share 1.0: no row | 0.8 |
| `HANDOFF_ONE_DATABASE_DOMINATES` (0.8) | same | largest share 0.567 (crossref): no row | 0.8 |
| every inception check | the UAV protocol imported as a draft (`uav-crop-weed-v03`, topic typed) | ready; 8 notes (no direction, no seeds, no planned number, 5 steps not opened since the import), no warning | as built |
| `EXPLORE_SAMPLE_ONE_SOURCE` (0.7), `DIRECTION_SEEDS_FEW` (3), `CRITERIA_REASONS_UNIFORM` (2), `HARVEST_ABOVE_TARGET` (plan or 1,000), `DEDUP_RATE_LOW` (0.05) | no recon pool, search run or deduplication on this computer | not calibrated; the tests use the 2026-11-13 figures the spec quotes (1,050 records, 2.2% merged across four databases) | spec values, unverified |

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| Strict run 5 (every exclusion `OUT_OF_SCOPE`, no reason could be set) | `tests/inception/test_criteria_reasons.py` (12 cases) | yes: 12 of 12 cases fail on `origin/main` (`extra_forbidden` on the new fields, no `reason_suggestions`, no rule) | yes |
| Strict run 6 (three suggested columns only; an own column was dropped) | `tests/inception/test_custom_matrix_columns.py` | yes: 8 of 8 fail | yes |
| Strict run 7 (the "Sample Size" sentence) | `test_review_wording.py::test_the_sample_size_column_quotes_the_unit_instead_of_pasting_it` | yes | yes |
| Strict run 8 (Review lists concepts without synonyms) | `inception-answers.test.tsx` "lists each concept with its synonyms" | not run against `origin/main` (the test was written with the fix) | yes |
| Strict run 9 (stray dot before the folder path; "Convincing evidence is A primary…") | `test_review_wording.py::test_the_rationale_quotes_each_answer_after_a_colon_without_a_double_full_stop`; `inception-answers.test.tsx` "puts the folder path inside the gate sentence" | yes for the rationale; the UI test was not run against `origin/main` | yes |
| Strict run (the title and questions said UAV, no concept did) | `test_inception_checks.py::test_concept_term_missing_uav`, `test_inception_proposals.py::test_a_check_proposes_uav_and_apply_writes_the_draft_and_the_decision_in_one_write` | yes: the checks route does not exist on `origin/main` (404) | yes |
| Strict run (two databases answered with no papers; the sample from one database) | `test_explore_database_empty_not_called_answered`, `test_explore_sample_one_source` | yes (no route) | yes |
| Strict run (every exclusion `OUT_OF_SCOPE`, draft side) | `test_criteria_reasons_uniform` | yes (no route) | yes |
| Strict run (1,050 harvested against an unstated plan; 2.2% merged; Hand-off said nothing while preparation stopped) | `test_discovery_checks.py::test_harvest_above_general_limit_when_no_plan_stated`, `test_dedup_rate_low_across_four_databases`, `test_handoff_preparation_unfinished_is_a_blocker_when_nothing_is_staged` | yes (no route) | yes |
| R1 (an accepted pool synonym is no longer offered after the save) | `test_accepted_synonym_is_recorded_although_no_longer_offered_after_the_save` | yes (`accepted_from` is `BODY_INVALID` on `origin/main`) | yes |
| Part A round 2, P3 (no full stop before "Started from" in a replacement's GENESIS row) | `test_inception_import.py::test_a_replacement_from_an_imported_draft_puts_a_full_stop_before_started_from` | yes: fails with the old line restored | yes |
| R3 / R4 (planned size, optional proof) | `test_steps_planned_size.py`, `test_steps_proof_optional.py` | yes: 7 of 14 fail (the 5 impossible-range cases already refuse on `origin/main`, as unknown fields under `extra="forbid"`; 2 proof cases describe what stays as it was) | yes |

## Review (Part B)
- Round 1 on `a07adaa5` (code at `dc48926c`): CHANGES, 7 findings (2 P2, 5 P3, no P1). Fixed: (1, P2) an `accepted_from` entry is recorded only when the saved draft holds it, judged by the engine (`test_an_entry_the_saved_draft_does_not_hold_is_not_recorded`); (2, P2) a dismissal reopens when the data the check judged changes: the scope, a concept's terms, an own direction's label and the pool's fingerprint are now in the evidence (four reopening tests); (3) a dismissal is judged inside the draft lock; (4) the two genesis journal rows are no longer swallowed on error; (5) the blocker test asserts each draft's one blocker equals the engine's refusal; (6) the test count in B2; (7) `02-checks`' term rule points to decision item 27. The five new tests fail on `dc48926c`'s engine and pass after. The reviewer's two follow-ups: the Hand-off's "open checks on earlier steps" line now counts blockers and warnings, as the step badge does; out-of-date cards building up for one term is in the deferred list. The inline Edit editor is decision item 33 (proposed). Decision items 29 and 31 must be accepted before merge (the reviewer's condition).
- Round 2 on `c582ebc5` (code at `7fd59aa3`, after `origin/main` 835b3d32 with Part D was merged): **APPROVE**. All 7 findings verified fixed; the merge keeps Part B and Part D (allow-lists, registry, §7, decisions); no new P0 to P2. Merge waits for the researcher's acceptance of decision items 29, 31 and 33 (and the other proposed items 27, 28, 30, 32). **Part B READY FOR PR** on `c582ebc5` and later documentation commits (code `7fd59aa3`). P3 follow-ups from round 2: `SHAPE_PLANNED_SIZE_EMPTY` hard-codes 1,000 instead of importing `SIZE_WARN_WORKS` (`inception/checks.py`); no direct test of a raising `append_event` at genesis; no vitest of its own for the Hand-off "earlier checks" count; no concurrency test for the dismissal under the lock. The contract row rendering and the B1 test count were fixed in the documentation commit after round 2.

## Review (Part A)
- Spec review (2026-11-18, before the build): CHANGES, 20 findings (4 P1, 15 P2, 1 P3); all fixed in `9924f5b2`.
- Part A, round 1 on `4784790c`: CHANGES, 11 findings (2 P2, 9 P3, no P1). Finding 1 (an imported column named like a suggestion lost its wording silently, or a case variant was refused later) and findings 3 to 11 fixed in `a1ef6122` and `dcb85d07`. Finding 2 is not code: decision items 21, 25 and 26 wait for the researcher.
- Part A, round 2 on `dcb85d07`: **APPROVE** (code), with the open condition above. One new P3, deferred (below).

## Decisions
Proposed here; they move to `docs/decisions.md` once M10a's entries are merged.
- 2026-11-14 (accepted by the researcher): database order drives the Explore sample only; the in-app chat follows the MCP version; what an assistant may execute; the full sequence.

### Spec drafts (2026-11-14)
All eight files are `Status: DRAFT` (seven writers, 2,145 lines). Verified by the
main session against the code: PRISMA "excluded by reason" counts are per criterion
id, not per `reason_category` (`screening/events.py::valid_reason`,
`screening/export.py:304-309`); a harvest job runs discovery, deduplication,
hydration and verification in that order (`pipeline/coordinator.py:595, 677, 696,
712`) and the Hand-off reads only `literature/verified.json`
(`corpus_accept.py:651-656`). Everything else in the drafts is the writers' reading.

### Put to the researcher (2026-11-14); all nine recommendations accepted on 2026-11-15 ("accept all")
| # | Question | Accepted answer |
| :-- | :-- | :-- |
| R1 | Record the engine's existing suggestions (pool synonyms, anchor papers, wizard criteria…) when the researcher accepts one, so the methods text can name their source? | Yes, as a write-only record in the same list |
| R2 | An "Apply all" button for a step's proposals? | No in M10b; revisit in M10c when the assistant adds volume |
| R3 | A field where the researcher states how many studies they plan to screen (today the protocol takes a preset range nobody chose)? | Yes; the size checks compare against it, and warn at 1,000 works when it is empty |
| R4 | After starting from a protocol, must the researcher type the "proof" answer and drop the criterion the wizard writes from it? | Make the proof answer optional when the draft already has an accepted typed inclusion |
| R5 | Harvest robustness (stage shown on every screen, resume preparation from the fetched records without a new search, Stop honoured in every stage): inside M10b or its own fix first? | Its own hardening fix, before the M10b build; it blocks the strict run |
| R6 | One place to accept a corpus: the Hand-off for both harvests and staged exports, with Import linking to it? | Yes |
| R7 | Group the PRISMA exclusion counts by reason category instead of by criterion? | No change |
| R8 | Lighter screens: allow an icon-only help button and a neutral "Recommended" badge (two exceptions to the brand book), and fold secondary cards on Explore and Review first? | Yes to both |
| R9 | Dismissing a warning needs one sentence of reason? | Yes for warnings; notes can be dismissed without one |

### Adopted from the writers' recommendations (main-session design; the researcher may overrule)
- Proposals: a stale proposal cannot be applied, only dismissed; only a rejected proposal can be restored; the new console refusal codes are registered in `console/refusals.py` and `screening-api-contract.md` §7 and documented in `docs/architecture/inception-api.md`, not in the closed `Envelope@1` registry (no contract change; wording made exact on 2026-11-18).
- Criteria: reason codes follow `^[A-Z][A-Z0-9_]{2,39}$`; the paradigm default gets a settable reason; the new `Draft` fields are additive, and `generate_contract_baseline.py --check` is run at build.
- Own matrix columns: the draft stores the whole dimension (so an imported protocol's columns survive); the screen offers name, description, type and required. This settles the difference between `05-criteria` and `09-start-from-protocol`.
- Start from a protocol: the topic stays empty with a "Use research question 1" button; an "imported, not yet checked" mark clears on visiting the step; per-question facets, the rationale and the database list are regenerated and listed as not carried.
- Next step: `protocol_origin` in `project.json`; the bar also serves the inception screens.
- Sample curation: exclusions survive a scope change; the reserve is only what was already fetched; a recommendation appears below 12 papers or when half are left out; a paper without a DOI can be left out.
- Size estimate: 30 seconds per record as an editable default; the count runs only on a button; the estimate is not journaled.
- Checks: thresholds are engine constants, calibrated on the golden UAV workspace before the build; a warning never blocks; a dismissal reopens when its data changes.

### Reconciled on 2026-11-15 (one pass by the main session after the answers)
- **Size warning (R3).** One limit for the estimate and for both size checks: the researcher's planned maximum when stated, else 1,000 works. The planned number is a new optional field on Shape (`Draft.pool_min`, `pool_max`), compiled through the intent's existing `pool_min` and `pool_max` into `target_candidate_pool_size`; "stated" is read from `intent.json`. No protocol schema or Contract v1 change by reading (`scholar_protocol/intent.py:209, :213`, `compiler.py:183-185`).
- **Proof (R4).** One rule for every draft, in `04-shape`: the proof may be empty when the draft holds a typed or imported inclusion that is not dropped. Checked in code: on the browser path the proof feeds only the wizard's inclusion, the template question and one rationale sentence.
- **Harvest (R5).** The stage marker, "Finish preparing this corpus" and Stop in every stage leave M10b for their own fix, proposed id **M3i-harvest-robustness**. It starts after M10a merges (both change `console/api/discovery.py` and the Harvest screen) and before the M10b build; it amends `03-harvest` and `08-handoff`. The researcher approves its start.
- **Check ids.** `10-sample-curation`'s two recommendations are the catalogue checks `EXPLORE_POOL_THIN` and `EXPLORE_SAMPLE_MOSTLY_LEFT_OUT` (new); the import's Review note is `REVIEW_IMPORT_STEP_NOT_OPENED` (new); the planned-size note is `SHAPE_PLANNED_SIZE_EMPTY` (new); the estimate's warning is `PLAN_ESTIMATE_ABOVE_TARGET`. The catalogue then had 51 checks; 50 since `SCOPE_TOPIC_LONG` was dropped on 2026-11-18.
- **A contradiction between two specs, found in this pass.** `01-proposals` said an imported protocol creates proposals; `09-start-from-protocol` prefills the draft directly. Settled as `09` says: the import creates no proposal in M10b, and the `import:<name>` source is kept for a later import into a draft that already has answers.
- **Own matrix columns.** The draft stores the whole dimension (seven fields); the form offers four.
- **What the methods text may count.** Added to `01-proposals`: genesis marks each applied proposal `in_protocol: true|false`, because an applied value can be edited away later. This is the main session's addition, not a writer's or the researcher's; overrule it if unwanted.
- Not changed: line numbers cited by older specs have drifted; the new specs cite the lines read on 2026-11-14.

### After M10a merges (done 2026-11-18, items S4 and S5)
- `EXPLORE_SAMPLE_ONE_SOURCE`'s "why" rewritten for the spread sample.
- Explore and Harvest recounted in `03-guidance`'s audit: 264 blocks at `a0191cc6`, 278 now.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| spec check | `3919a287` | `generate_contract_baseline.py --check`; `git diff --check` | current; clean (documentation only) | seconds |
| inner (A1–A5) | `c36d9680` | the 5 new `tests/inception/*` files; on `origin/main`'s four source files | 36 passed on the branch; 29 failed, 7 passed on `origin/main` (fails-before) | 23 s |
| inner (A6) | working tree before `fd9af0da` | `pytest tests/console tests/inception -m "not slow" -n auto`; `test_inception_import.py`, `test_console_refusals.py`, `test_browser_access.py`; vitest `inception-answers`, `inception-import`, `inception-copy`, `i18n-*` | 669 passed, 1 skipped; 39 passed; 15, 8, 39 passed | about 5 min |
| checkpoint | `fd9af0da` + test fixes in `b07bc6c7` | `select_test_gate.py --changed origin/main --stage checkpoint` (console, authority, inception, recon, cli init, protocol kit; typecheck; `npm test`) | first run: 3 failures, all from Part A (the init test pins `project.json` keys; a disclosure without the focus ring; an older Criteria test adding an exclusion with no reason); fixed in `b07bc6c7` and re-run green (19 and 10 tests) | 239 s Python, 93 s UI |
| browser (inception) | `b07bc6c7`, `e381f63b` | `playwright test tests-browser/inception.spec.ts tests-browser/hygiene.spec.ts` | first run 156 passed, 6 failed (the new import scenario's URL pattern; the file input's accessible name); fixed in `e381f63b`, the 16 affected tests then passed | 7.8 min, 46 s |
| **pr** | **`e381f63b`** | `git diff --check origin/main...HEAD`; `generate_contract_baseline.py --check`; `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9`; `pytest -q -n auto`; `typecheck`; `npm test`; `build`; `test:browser` | clean; current; clean; clean; **5,121 passed, 15 skipped, 0 failed**; clean; **658 passed (46 files)**; built; **507 passed, 13 skipped** (Playwright rewrote 10 tracked screenshots of screens Part A does not touch; restored) | 1,050 s in all (pytest 423 s, vitest 78 s, browser 529 s) |
| review round 1 fixes | `a1ef6122` | the 8 affected Python files (`test_inception_import.py`, the five new `tests/inception` files, `test_inception_criteria.py`, `tests/cli/test_cli_init.py`); vitest `inception-answers`, `inception-import`, `inception-copy`, `inception-shape`; typecheck | 89 passed; 32 passed; clean | 9 s, about 1 min |
| **pr (after review round 1)** | **`a1ef6122`** | as above | diff check: 3 files ended with a blank line (fixed in the next commit, whitespace only; nothing else changed, so the run below stands for it); baseline current; ruff clean twice; **pytest 5,129 passed, 15 skipped, 0 failed**; typecheck clean; **vitest 658 passed**; built; **browser 507 passed, 13 skipped** (10 screenshots rewritten and restored) | 980 s (pytest 356 s, vitest 72 s, browser 527 s) |
| inner (Part B engine) | working tree before `8976091e` | `pytest tests/console tests/inception -m "not slow" -n auto` | first run 5 failed (genesis tests reading GENESIS as the last journal row, and an archive list), fixed (decision item 28); then 768 passed; the new files 30 + 37 + 25 passed | 411 s |
| UI (subagent) | `dc48926c` | typecheck; vitest; `playwright test tests-browser/inception.spec.ts tests-browser/hygiene.spec.ts` | clean; 691 passed (48 files; `proposals` 15, `checks-panel` 18); 164 passed | about 1 h of building |
| **pr (Part B)** | **`dc48926c`** (with `origin/main` 088af7cf merged at `ac431f0a`) | `git diff --check origin/main...HEAD`; `generate_contract_baseline.py --check`; `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9`; `pytest -q -n auto -o addopts=""`; `typecheck`; `npm test`; `build`; `test:browser` (port 4391) | clean; current; clean; clean; **5,476 passed, 15 skipped, 0 failed** (the first run's summary was swallowed by `-q`, so it was run again with `-o addopts=""`); clean; **691 passed (48 files)**; built; **509 passed, 13 skipped** (10 screenshots of screening screens rewritten and restored) | pytest 464 s, vitest 75 s, browser 582 s |
| review round 1 fixes | `308549c6` | the 4 Part B Python files; vitest `checks-panel`, `discovery-handoff`, `proposals`; typecheck; the 5 new tests on `dc48926c`'s engine | 122 passed (one test-data fix, then all); 45 passed; clean; 5 failed before, 5 passed after | about 1 min |
| **pr (Part B, after review round 1 and `origin/main` 835b3d32 merged)** | **`7fd59aa3`** | as the row above | diff check clean; baseline current; ruff clean twice; **pytest 5,544 passed, 15 skipped, 0 failed**; typecheck clean; **vitest 717 passed (49 files)**; built; **browser 533 passed, 13 skipped** (13 screenshots of screens Part B does not touch rewritten and restored) | pytest 450 s, vitest 67 s, browser 584 s |

## Deferred
Part B (none is a DoD item; each is the spec's wording that the build did not reach):
- `EXPLORE_SAMPLE_MOSTLY_LEFT_OUT` is not computed until Part C builds sample curation; `EXPLORE_POOL_THIN` counts the pool's papers until then (decision item 31).
- The six existing suggestion mechanisms keep their own look; they record their acceptances through `accepted_from` (decision item 31; M10d).
- A proposal card's Edit opens an inline editor in the card, not the field's own editor on the screen.
- The narrow-window layout of the panel (collapsible header, 44 px rows) and the "Applied · {field}" toast; decisions are announced through a polite status line.
- No discovery browser scenario (its fake engine would need the runs, dedup and hand-off state); the discovery panel is covered by vitest and the engine tests.
- Checks of an older run (`?run=`) are not shown read-only on the screen; the route answers them.
- The `fields` and `steps` sentence slots arrive as one comma-joined string the browser splits to label each item; the evidence carries the list.
- The thresholds that only a search run, a deduplication or a recon pool can test (calibration table) are the spec's values, not run over the 2026-11-13 evidence, which is on the second computer.
- The `review.check.*` copy keys of the old Checks card are unused and still in the catalogue.
- Each save that changes the concepts while an acronym is still missing makes the next checks run record a new open proposal (the base changed), so out-of-date cards for the same term build up until dismissed (review of Part B, follow-up).

Part A (each listed by the Part A review of 2026-11-18, or found while building; none is a DoD item):
- The import screen's Offline state (`09` States: Create disabled with "needs the engine on this computer"). Not built; the screen shows the engine-unreachable card from the read instead. To build with Part C's bar, which owns the offline line.
- `inception-import.uav.test.tsx` (`09` names a vitest rebuild of the UAV draft against a fake that implements the mapping). The engine rebuild is the Python `test_import_rebuilds_uav_draft`, on the real UAV protocol; the UI is covered by `inception-import.test.tsx` and the browser scenario. Not written.
- Vitest cases for the Scope "needs" line and "Use research question 1" exist only in `inception-import.test.tsx` ("shows the banner and the marks ..."); Shape's proof "needs" line has no test of its own.
- The terminal wizard's "Rejection category" prompt still takes any text: the reason-code rule applies to browser saves (decision item 25). A separate decision.
- `pool_max: true` is read as 1 (pydantic's lax integers). Strict integers for the two fields are a follow-up.
- `REVIEW_IMPORT_STEP_NOT_OPENED` (the Review note for an unopened imported step) is a check: Part B.
- The GENESIS row of a *replacement* made from an imported draft reads "...(backup at audit/replaced/...) Started from ..." with no full stop between (`emit.py`, the replacement branch; Part A round 2, P3). A code change would need the full gate again; Part B rewrites this genesis code for `audit/proposals.jsonl`, so it is fixed there, with a test.

## Part D (size estimate)
Branch `dev/m10b/part-d-size-estimate`, from `origin/main` at `6e39b00a` (Part A merged, PR #240; provider resilience merged, PR #239). Lane RELEASE, as the milestone (a new public route in both allow-lists, a new refusal code, a new method on every provider). Built by a separate session while Part B was built on its own branch; Part D touches no inception screen, proposal, check object or inception API.

What D1 delivers:
- `BaseAPIProvider.count(query)` and its five overrides (`src/scholar_search/providers/*`): one request built from the plan's `translate()`, no record body (OpenAlex `per-page=1`, Crossref `rows=0`, PubMed `retmax=0`, arXiv `max_results=1`, Semantic Scholar the first bulk page with `fields=paperId`); bioRxiv raises `NotImplementedError` (`not_countable`).
- `scholar_search.estimate`: `count_providers` (in parallel; a failed database is its own row with the harvest's leg codes), `summarize` (fetch per database, records and works ranges, hours, the warning against the limit, the largest cap that keeps the sum at the limit, or narrowing), the constants `SIZE_WARN_WORKS` 1,000, `SUGGESTED_CAP_MIN` 100, `ESTIMATE_TTL` 600 s, pace 30 s (5 to 600).
- `scholar_harness.size_limit.size_limit(ws)`: `intent.json` `pool_max` stated, else 1,000 (R3).
- `POST /api/v1/discovery/estimate` (`console/api/discovery.py`), in both POST allow-lists; refuses `PROTOCOL_MISSING`/`PROTOCOL_INVALID`, `CAP_INVALID`, `PACE_INVALID` (new), `PROVIDER_UNKNOWN`, `MAILTO_NOT_SET`, `OPENALEX_KEY_NOT_SET`, `CORPUS_ALREADY_ACCEPTED`, `DISCOVERY_JOB_ACTIVE` before any request; uses a recall check for this protocol; caches counts 10 minutes; writes no file and no journal row. `PACE_INVALID` is in `console/refusals.py` and §7.
- The Estimate card (`components/discovery-estimate.tsx`) on Plan (side column, under Limits) and Harvest (ready state, above "What will be searched"); `?cap=` fills Harvest's cap field after hydration; copy in en, fr, ar (`lib/discovery-copy.ts`, `PACE_INVALID` in `lib/screening-states.ts`); the fake engine answers the route.

Decisions: `docs/decisions.md`, "2026-11-18 — M10b Part D: the size estimate, where the spec is silent" (17 items, accepted by the researcher 2026-11-18). Spec note: `01-plan.md` "As built (M10b Part D)".

### Part D tests
| Test | What it shows | Fails before |
| :-- | :-- | :-- |
| `tests/kits/search/test_provider_count.py` (9) | each count sends one request for the plan's string and filters with no record body; bioRxiv not countable; a missing total is `None`; a provider error is raised | yes: 9 of 9 fail on `origin/main` (no `count`) |
| `tests/console/test_discovery_estimate_api.py` (44) | the arithmetic (cap binds, works range, arXiv, unknown upper end, hours, warning boundaries, the spec's 5,000/400/100 → 500 example, narrowing); the route (protocol's and chosen databases, what-if cap, a failed row, bioRxiv, the cache and its expiry, a changed list or protocol, re-asking only failed rows, recall check used, skipped on refresh, ignored for another protocol, planned and general limits, ten refusals with no request, no file written, both allow-lists) | written with the route; on `origin/main` the route answers 404 (not run separately) |
| `apps/research-ui/tests/discovery-estimate.test.tsx` (24) | the spec's vitest list for Plan and Harvest | written with the card (not run against `origin/main`, where the card does not exist) |
| `tests-browser/discovery.spec.ts` "M10b: …" (2 journeys, axe in en and ar, overflow at 375 and 1440 px on Plan and Harvest) | count on Plan → capped database and warning → "Use 282" → Harvest field filled, nothing started → edit → Start sends `cap_override: 250`; a failed database leaves the rest readable | new |

### Part D evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner (engine) | `93154594` | `test_provider_count.py` on `origin/main`'s providers, then on the branch; `test_discovery_estimate_api.py`, `test_console_refusals.py`, `test_browser_access.py` | 9 failed before (no `count`), 9 passed after; 56 passed (one contract §7 failure on the first run, the `PACE_INVALID` row, added) | about 1 min |
| inner (UI) | `e7b39285` | vitest `discovery-estimate`, `discovery-copy`; then `discovery-plan`, `discovery-harvest`, `discovery-engine-fake`, `discovery-preparation`, `discovery-overview`, `i18n-direction-source`, `i18n-catalog`; typecheck | 29 passed; 123 passed; clean | about 45 s |
| browser (M10b subset) | `fb7a184c`, `38b36f38` | `playwright test tests-browser/discovery.spec.ts -g "M10b\|a choice made on Plan\|axe finds no violation"` | first run: 66 passed, 4 failed (axe `definition-list`: the figures' `<dl>` had no `dt`/`dd`); fixed in `38b36f38`, the 24 M10b tests then passed in both themes | 2.9 min, 47 s |
| inner (Python) | `38b36f38` | `pytest tests/console -m "not slow" -n auto`; `pytest tests/unit tests/test_handoff.py -m "not slow"`; `pytest tests/kits/search -m "not slow"` | 567 passed, 1 skipped; 710 passed; 412 passed | 4.5 min |
| review round 1 fixes | `c6507029` | the estimate and provider-count files (2 reproducing tests failed before the fix); vitest `discovery-estimate`, `discovery-copy`, N9 guard | 56 passed; 37 passed | about 30 s |
| **pr (Python)** | **`c6507029`** | `git diff --check origin/main...HEAD`; `generate_contract_baseline.py --check`; `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9`; `pytest -q -n auto` | clean; current; clean; clean; **5,417 passed, 15 skipped, 0 failed**. The commits after it change one vitest file, two class names and the records, so this run stands for the head | 606 s |
| pr (UI), first run | `bea44839` | typecheck; `npm test` | clean; 683 passed, **1 failed** (`details-rule`: the estimate's two `<summary>` had no focus ring); fixed in `5000433f`; the chain stopped before the build | 97 s |
| **pr (UI)** | **`5000433f`** | `git diff --check origin/main...HEAD`; typecheck; `npm test`; `build`; `test:browser` (on port 3127: 3117 was held by another process, and the config never reuses a server) | clean; clean; **684 passed (47 files)**; built; **531 passed, 13 skipped, 0 failed** (Playwright rewrote 13 tracked screenshots of screens Part D does not touch; restored) | 196 s vitest, 13.3 min browser |

### Part D review
- Round 1 on `fb7a184c` (`milestone-reviewer`): **CHANGES**, 10 findings (2 P2, 8 P3, no P1); boundaries held, arithmetic and the no-browser-count rule confirmed. Fixed in the next commit: 1 (each count bounded at 45 s, a slow database is a `PROVIDER_TIMEOUT` row; reproducing test), 3 (a retry keeps the first count time; reproducing test), 4 (`refresh` only when neither cap nor pace changed; vitest), 7 (a pace that is not a whole number says so inline; vitest), 9 (the S2 refused count has its test), 10 (`03-harvest` status). Recorded instead of built: 2 (the live check, deferred below), 5 (decision item 16), 6 (the duplicates line, decision item 12, a spec contradiction), 8 (focus order and `dir`, in `01-plan` "As built"). Separately, the browser run found the figures in a `<dl>` without `dt`/`dd` (axe `definition-list`), fixed in `38b36f38`.
- Round 2 on `c6507029`: **APPROVE**. All ten round-1 findings resolved (six fixed, four recorded). One new P3 (N1): the finding-4 vitest passed without the fix, because it pressed Enter rather than "Count again"; rewritten in the next commit to click "Count again" with another pace (no `refresh`) and again with nothing changed (`refresh: true`).

### Part D deferred
- **The live check of each provider's count form** (spec acceptance: "checked once against the golden UAV protocol by hand and the result recorded in the milestone's evidence"): OpenAlex `per-page=1`, Crossref `rows=0` (sent with `cursor=*`), PubMed `retmax=0`, arXiv `max_results=1`, Semantic Scholar's first bulk page with `fields=paperId`. Not done: this session makes no live provider call and handles no key. For the researcher, with the console's own keys: open the golden UAV workspace's Plan, press "Count what the databases hold", and compare each row's "found" with the `reported_total` of the same database in the workspace's last harvest legs; record the result here.
- **The catalogue check `PLAN_ESTIMATE_ABOVE_TARGET`** (`02-checks`): the card shows the engine's `warn` with the `01-plan` copy (`estimate.warn.*`), not the catalogue's id and sentence (`02-checks` line 280 words it differently). The check object is Part B's; reconciling the two wordings belongs to whichever of B and D merges second. `HARVEST_ABOVE_TARGET` is Part B's and can call `scholar_harness.size_limit.size_limit`.
- The skeleton rows while counting, `<bdi>` isolation and `dir="ltr"` on numbers inside translated sentences, and the spec's focus order inside the card (`01-plan` "As built (M10b Part D)").
- Follow-ups the review named, older than this branch: the search client's HTTP cache (`hishel`, `http_cache` on by default) could answer a count from cache; the estimate is not a job, so a harvest may start while a count is in flight (harmless).
