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
- [ ] B1 Proposal store, API and card (`01-proposals`): the four POST routes (apply, apply-edited, reject, restore) in both allow-lists; the draft `PUT`'s `accepted_from` and its `engine:<mechanism>` records (R1); the per-draft lock; genesis's `audit/proposals.jsonl` with `in_protocol` and the journal rows, written inside `steps.genesis`'s try block and added to `ARCHIVED_ON_REPLACE`; `protocol_origin` written by both genesis paths and by `_refresh_manifest`; the `PROPOSAL_*` codes in the console refusal registry, §7 and `inception-api.md`. The workspace proposal routes are M10c's. Tests: `tests/console/test_inception_proposals.py`; `tests/console/test_console_refusals.py`; `apps/research-ui/tests/proposals.test.tsx`.
- [ ] B2 Checks engine (`02-checks`, 50 checks): the inception and discovery catalogues, dismissal and restore with the record (`check_dismissals`, `audit/check_dismissals.jsonl`, also in `ARCHIVED_ON_REPLACE`); the inception checks POST and the dismiss and restore POSTs (inception and discovery) in both allow-lists; the `CHECK_*` codes in the console refusal registry, §7 and `inception-api.md`; thresholds marked ⚑ run over the golden UAV workspace and the 2026-11-13 evidence, the result recorded here before they are frozen. Tests: `tests/console/test_inception_checks.py` (the Shape checks included), `tests/console/test_discovery_checks.py`; `tests/console/test_console_refusals.py`.
- [ ] B3 Checks panel on inception 01 to 06 and discovery 01 to 06 and 08; Review's "Ready to create?" list replaces its Checks card. Tests: `apps/research-ui/tests/checks-panel.test.tsx`.

Part C, the what's-next bar, the Import link and Explore:
- [ ] C1 Next-step builder `console/next_step.py`; `GET /review/next-step`, workspace-free (added to `_workspace_free` in `console/serve.py`; it answers `NO_REVIEW` itself), and `GET /inception/drafts/{id}/next-step`, both without ETag; the bar in `AppShell`; `protocol_origin` in `project.json` (`placeholder` from the placeholder scaffold of `nexus-scholar init`; `inception` or `import` from both genesis paths and from `_refresh_manifest` on a replacement); the `08-handoff` amendment "The next-step bar (M10b)" (`04-next-step`). No new refusal code. Strict-run finding 11. Tests: `tests/console/test_next_step_api.py`; `apps/research-ui/tests/next-step-bar.test.tsx`.
- [ ] C2 The Import step links to the Hand-off (`11-import-corpus` "Accepting on the Hand-off"). Strict-run finding 11. Tests: the `screening-import` vitest file.
- [ ] C3 Sample curation (`02-explore` "Sample curation"): `reserve` and `POOL_SAMPLE` `relevance-2`, `effective_pool`, `GET`/`POST …/recon/sample` (the POST in both allow-lists), `SAMPLE_CHANGED`, `recon_context` `sample_exclusions`, the Papers card controls; `PAPER_UNKNOWN` and `SAMPLE_EXCLUSIONS_FULL` in the console refusal registry, §7 and `inception-api.md`. Tests: `tests/recon/test_effective_pool.py`, `tests/console/test_recon_sample_api.py`; `tests/console/test_console_refusals.py`; `apps/research-ui/tests/inception-sample.test.tsx`.
- [ ] C4 Explore on an empty search (`02-explore` "Explore on an empty search (M10b)"): "Databases asked" shown once on a `POOL_EMPTY` or `PROVIDERS_FAILED` refusal; the shorten advice only when the job error carries `details.shorten: true` (decision item 17). Reproducing tests first: the `inception-explore.test.tsx` cases and the engine test named in that section.

Part D, the size estimate (after the search-provider resilience session merges):
- [ ] D1 `POST /discovery/estimate` (in both allow-lists), a count per database, the Estimate card on Plan and Harvest (`01-plan` "Size estimate"); `PACE_INVALID` in the console refusal registry and §7. The count request per database touches `src/scholar_search/providers/*`. Tests: `tests/console/test_discovery_estimate_api.py`, `tests/kits/search/test_provider_count.py`; `tests/console/test_console_refusals.py`; `apps/research-ui/tests/discovery-estimate.test.tsx`.

Every part:
- [ ] Copy in en, fr and ar for every new key (the N9 guard and the copy tests pass). **Part A: done** (FR and AR are typed `Record<InceptionCopyKey, string>`, so the type check fails on a missing key; `inception-copy.test.ts` and the N9 guard pass). Parts B, C, D: open.
- [ ] `/gate pr` once on the final executable commit of the part, `generate_contract_baseline.py --check`, `git diff --check`, `milestone-reviewer` APPROVE. **Part A: done** (pr gate on `a1ef6122`, the final executable commit; baseline current; diff check clean on `dcb85d07`; reviewer APPROVE on `dcb85d07`). Parts B, C, D: open.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| Strict run 5 (every exclusion `OUT_OF_SCOPE`, no reason could be set) | `tests/inception/test_criteria_reasons.py` (12 cases) | yes: 12 of 12 cases fail on `origin/main` (`extra_forbidden` on the new fields, no `reason_suggestions`, no rule) | yes |
| Strict run 6 (three suggested columns only; an own column was dropped) | `tests/inception/test_custom_matrix_columns.py` | yes: 8 of 8 fail | yes |
| Strict run 7 (the "Sample Size" sentence) | `test_review_wording.py::test_the_sample_size_column_quotes_the_unit_instead_of_pasting_it` | yes | yes |
| Strict run 8 (Review lists concepts without synonyms) | `inception-answers.test.tsx` "lists each concept with its synonyms" | not run against `origin/main` (the test was written with the fix) | yes |
| Strict run 9 (stray dot before the folder path; "Convincing evidence is A primary…") | `test_review_wording.py::test_the_rationale_quotes_each_answer_after_a_colon_without_a_double_full_stop`; `inception-answers.test.tsx` "puts the folder path inside the gate sentence" | yes for the rationale; the UI test was not run against `origin/main` | yes |
| R3 / R4 (planned size, optional proof) | `test_steps_planned_size.py`, `test_steps_proof_optional.py` | yes: 7 of 14 fail (the 5 impossible-range cases already refuse on `origin/main`, as unknown fields under `extra="forbid"`; 2 proof cases describe what stays as it was) | yes |

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

## Deferred
Part A (each listed by the Part A review of 2026-11-18, or found while building; none is a DoD item):
- The import screen's Offline state (`09` States: Create disabled with "needs the engine on this computer"). Not built; the screen shows the engine-unreachable card from the read instead. To build with Part C's bar, which owns the offline line.
- `inception-import.uav.test.tsx` (`09` names a vitest rebuild of the UAV draft against a fake that implements the mapping). The engine rebuild is the Python `test_import_rebuilds_uav_draft`, on the real UAV protocol; the UI is covered by `inception-import.test.tsx` and the browser scenario. Not written.
- Vitest cases for the Scope "needs" line and "Use research question 1" exist only in `inception-import.test.tsx` ("shows the banner and the marks ..."); Shape's proof "needs" line has no test of its own.
- The terminal wizard's "Rejection category" prompt still takes any text: the reason-code rule applies to browser saves (decision item 25). A separate decision.
- `pool_max: true` is read as 1 (pydantic's lax integers). Strict integers for the two fields are a follow-up.
- `REVIEW_IMPORT_STEP_NOT_OPENED` (the Review note for an unopened imported step) is a check: Part B.
- The GENESIS row of a *replacement* made from an imported draft reads "...(backup at audit/replaced/...) Started from ..." with no full stop between (`emit.py`, the replacement branch; Part A round 2, P3). A code change would need the full gate again; Part B rewrites this genesis code for `audit/proposals.jsonl`, so it is fixed there, with a test.
