# M10b Proposals and checks
Branch: dev/m10b/proposals-checks · Lane: **to declare before engine work** (the spec stage is documentation only; RELEASE if the proposal record, the exclusion reasons or the next-step endpoint change a public HTTP response or touch Contract v1, per `docs/architecture/test_gate_policy.md`) · Status: SPECS FINAL (2026-11-15); the build has not started and waits for M10a and for the harvest fix M3i-harvest-robustness · Started: 2026-11-14

Second milestone of the "Assisted inception" sequence the researcher approved on
2026-11-14 (M10a search quality, **M10b proposals and checks**, M10c assistant and
critic over MCP, M10d lighter screens, M10e in-app chat). M10a
(`dev/m10a/search-quality`) runs in parallel and adds the plan §6 rows and the
`docs/decisions.md` entries; this branch does not edit `production-plan.md`,
`docs/decisions.md`, or the specs M10a amends (inception `01-scope`, `02-explore`,
`03-direction`; discovery `01-plan`, `03-harvest`).

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
- [x] `docs/ux/shared/final/02-checks.md`: the checks panel, the catalogue of 51 checks per step with their thresholds, dismissal, readiness on Review.
- [x] `docs/ux/shared/final/03-guidance.md`: hint, recommended mark and density rules, with the per-screen audit for inception 01 to 07 and discovery 01 to 09.
- [x] `docs/ux/shared/final/04-next-step.md`: the "what's next" bar and its state table.
- [x] `docs/ux/phase0-inception/final/09-start-from-protocol.md`.
- [x] `docs/ux/phase0-inception/final/05-criteria.md` amended: exclusion reasons, own matrix columns.
- [x] `docs/ux/phase0-inception/final/04-shape.md` amended (added 2026-11-15 by R3 and R4): the planned number of records, the optional proof answer.
- [x] `docs/ux/phase0-inception/final/10-sample-curation.md`: removing a paper from the sample (folded into `02-explore` after M10a merges).
- [x] `docs/ux/phase1-discovery/final/10-size-estimate.md` (folded into `01-plan` after M10a merges).
- [x] The researcher has closed every open question (2026-11-15, "accept all"); each spec says `Status: FINAL`. The specs were written by seven writers and reconciled by the main session; no independent reviewer has read them.

### Build (after the specs are FINAL; items and tests are named then)
- [ ] First: amend `docs/ux/phase2-screening/final/11-import-corpus.md` (the Import step links to the Hand-off; R6), fold `10-sample-curation` into `02-explore` and `10-size-estimate` into `01-plan`, and write the decisions below into `docs/decisions.md`.
- [ ] Proposal store, API and card, with the write-only record of accepted engine suggestions (R1).
- [ ] Checks engine and panel; thresholds calibrated on the golden UAV workspace before they are frozen.
- [ ] The planned number of records and the optional proof answer (`04-shape`).
- [ ] The six other items above. The import and the own matrix columns are built together.
- [ ] `/gate pr`, `generate_contract_baseline.py --check`, `milestone-reviewer` APPROVE.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |

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
- Proposals: a stale proposal cannot be applied, only dismissed; only a rejected proposal can be restored; the new console refusal codes are documented in `docs/architecture/inception-api.md`, not in the closed `Envelope@1` registry (no contract change).
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
- **Check ids.** `10-sample-curation`'s two recommendations are the catalogue checks `EXPLORE_POOL_THIN` and `EXPLORE_SAMPLE_MOSTLY_LEFT_OUT` (new); the import's Review note is `REVIEW_IMPORT_STEP_NOT_OPENED` (new); the planned-size note is `SHAPE_PLANNED_SIZE_EMPTY` (new); the estimate's warning is `PLAN_ESTIMATE_ABOVE_TARGET`. The catalogue now has 51 checks.
- **A contradiction between two specs, found in this pass.** `01-proposals` said an imported protocol creates proposals; `09-start-from-protocol` prefills the draft directly. Settled as `09` says: the import creates no proposal in M10b, and the `import:<name>` source is kept for a later import into a draft that already has answers.
- **Own matrix columns.** The draft stores the whole dimension (seven fields); the form offers four.
- **What the methods text may count.** Added to `01-proposals`: genesis marks each applied proposal `in_protocol: true|false`, because an applied value can be edited away later. This is the main session's addition, not a writer's or the researcher's; overrule it if unwanted.
- Not changed: line numbers cited by older specs have drifted; the new specs cite the lines read on 2026-11-14.

### After M10a merges
- `EXPLORE_SAMPLE_ONE_SOURCE` describes the sample as cut today; rewrite its "why" for the spread sample.
- The database picker and the "0 results" wording of M10a change text blocks that `03-guidance`'s audit counted (264 blocks at `a0191cc6`); recount Explore and Harvest before M10d.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |

## Deferred
