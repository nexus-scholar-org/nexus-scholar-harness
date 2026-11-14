# M10b Proposals and checks
Branch: dev/m10b/proposals-checks · Lane: **to declare before engine work** (the spec stage is documentation only; RELEASE if the proposal record, the exclusion reasons or the next-step endpoint change a public HTTP response or touch Contract v1, per `docs/architecture/test_gate_policy.md`) · Status: IN PROGRESS (specs) · Started: 2026-11-14

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
  the same card. They are not migrated to the proposal store in this milestone.
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
- [ ] `docs/ux/shared/final/01-proposals.md`: the proposal object, card, list, storage, API and record.
- [ ] `docs/ux/shared/final/02-checks.md`: the checks panel, the catalogue of checks per step with their thresholds, dismissal, readiness on Review.
- [ ] `docs/ux/shared/final/03-guidance.md`: hint, recommended mark and density rules, with the per-screen audit for inception 01 to 07 and discovery 01 to 09.
- [ ] `docs/ux/shared/final/04-next-step.md`: the "what's next" bar and its state table.
- [ ] `docs/ux/phase0-inception/final/09-start-from-protocol.md`.
- [ ] `docs/ux/phase0-inception/final/05-criteria.md` amended: exclusion reasons, own matrix columns.
- [ ] `docs/ux/phase0-inception/final/10-sample-curation.md`: removing a paper from the sample (folded into `02-explore` after M10a merges).
- [ ] `docs/ux/phase1-discovery/final/10-size-estimate.md` (folded into `01-plan` after M10a merges).
- [ ] The researcher has closed every open question; each spec says `Status: FINAL`.

### Build (after the specs are FINAL; items and tests are named then)
- [ ] Proposal store, API and card.
- [ ] Checks engine and panel.
- [ ] The six other items above.
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

### To reconcile after the answers (one pass over all eight files)
- The size warning: `10-size-estimate` uses an absolute 1,000; `02-checks` compares with the planned size (R3 decides).
- Check ids: `05-criteria` and `10-size-estimate` use working names; `02-checks` holds the catalogue.
- Line numbers cited by older specs have drifted; new specs cite current lines.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |

## Deferred
