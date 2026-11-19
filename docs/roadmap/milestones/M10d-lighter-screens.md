# M10d-lighter-screens: tips behind icons, one main action, the recommended choice marked
Branch: `dev/m10d/lighter-screens` (from `origin/main` at `17d7310d`) · Lane: **STANDARD** (UI; plan §6) · Status: **IN PROGRESS** · Started: 2026-11-19 (the researcher: "start M10d")

Fourth milestone of "Assisted inception" (approved 2026-11-14). Plan §6 row **M10d-lighter-screens**: "Lighter screens: tips behind icons, one main action per step, the recommended choice marked. Specs written once, at the start of M10b."

**Spec.** `docs/ux/shared/final/03-guidance.md` (Status FINAL, questions closed by the researcher 2026-11-15) is the build contract: rules 1 to 5, the per-key Audit (rows `I-*` and `D-*`, decision STAYS / HINT / REMOVED), the per-screen header and action check, and its acceptance tests. The screen specs it amends are all FINAL: inception `01-scope` to `07-done` (02 and 03 built by M4d), discovery `01-plan` to `09-chase`; `docs/ux/phase2-screening/final/12-details-disclosure.md` (the details rule). The researcher's answers: R8 (M10b record and `docs/decisions.md` 2026-11-15 item 8: an icon-only hint and a neutral "Recommended" badge, two brand-book exceptions; Explore and Review folded first), and `03-guidance` "Open questions" 1 to 5 (closed).

**Lane.** STANDARD: UI only. No route, no engine change, no stored field, no refusal code, no Contract v1 artefact; `src/` is not touched.

**Not in this milestone.** Folding Criteria, Harvest, Report and Chase (rule 4, use 2): `03-guidance` question 3 keeps their layout until the researcher has looked at Explore and Review with real data. Replacing `overview.continue` and the second sentence of `done.lede` with the what's-next bar: question 5 keeps them. The look of the six existing suggestion mechanisms (decision 2026-11-15 item 31): see "Deferred".

## Measurement
The visible word count of each screen before and after, on the same fixture: `tests/guidance.words.test.tsx` renders each screen over the vitest fake engine in the state named in the table, waits for it to settle and counts the words a sighted reader sees (text outside `hidden`, closed `<details>` bodies, hint panels and `sr-only` text). "Before" is the same test run on `origin/main` (`17d7310d`) source.

Counted on 2026-11-19: before at `59e12a6a` (the screens of `origin/main` 17d7310d, only the test added), after at `844a4a87`. A word is what a sighted reader sees with every hint and fold closed; the papers of Explore's folded Papers section count before and not after, because that is what folding removes from the first view.

| Screen | Fixture state | Before | After | Removed or moved |
| :-- | :-- | --: | --: | --: |
| inception 01 Scope | a complete draft | 127 | 67 | 60 (47 %) |
| 02 Explore | a complete draft, never searched | 205 | 134 | 71 (35 %) |
| 02 Explore | after the first search, 14 papers | 623 | 230 | 393 (63 %) |
| 02 Explore | after a first search that found 7 papers | 645 | 247 | 398 (62 %) |
| 03 Direction | after the first search, three directions | 299 | 236 | 63 (21 %) |
| 04 Shape | a draft with a topic only | 256 | 165 | 91 (36 %) |
| 05 Criteria | a complete draft, nothing decided | 386 | 335 | 51 (13 %) |
| 06 Review | a complete draft, every criterion decided | 276 | 207 | 69 (25 %) |
| 07 Done | the workspace created | 66 | 52 | 14 (21 %) |
| discovery entry | one finished run | 118 | 92 | 26 (22 %) |
| 01 Plan | the protocol's plan | 416 | 280 | 136 (33 %) |
| 02 Recall | no recall check yet | 168 | 71 | 97 (58 %) |
| 03 Harvest | ready, no run yet | 243 | 170 | 73 (30 %) |
| 04 Import | the discovery visit, nothing staged | 185 | 150 | 35 (19 %) |
| 05 Duplicates | one finished run | 135 | 109 | 26 (19 %) |
| 06 Report | one finished run, a rate-limited database | 393 | 330 | 63 (16 %) |
| 08 Hand-off | one finished run, not accepted | 210 | 163 | 47 (22 %) |
| 09 Chase | screening published, no chase yet | 204 | 148 | 56 (27 %) |
| **all 18 states** | | **4,955** | **3,186** | **1,769 (36 %)** |

Nothing a refusal, a warning, a check or a gate says is hidden: `guidance.never-hidden.test.tsx` and the browser scenario "a warning is never inside a hint" hold it.

## Definition of done
Shared parts (`03-guidance` rules 1 to 5):
- [ ] G1 `Hint` and `Details` in `components/ui/base.tsx`; the hint is a `<button type="button">` with a 16 px glyph in a 44 px hit area, `aria-expanded`, `aria-controls`, the name "About {label}", a `role="note"` panel kept in the DOM (`data-hint-body`, the field's `aria-describedby`), Escape / outside click / Tab away close it, one open at a time, inline-end placement with logical flipping. New keys in `lib/guidance-copy.ts`, en, fr and ar. Tests: `tests/hint.test.tsx`, `tests/hint.rtl.test.tsx`, `tests/guidance-copy.test.ts`.
- [ ] G2 `RecommendedBadge` ("Recommended · {source}", dashed `ink-muted` border, `ink` on `surface-raised`, followed by its hint); never preselects. Test: `tests/recommended.test.tsx`.
- [ ] G3 The audit fixture (`tests/fixtures/guidance-audit.ts`, one row per `03-guidance` Audit row) and `tests/guidance.audit.test.tsx`: every rendered hint body's key is a HINT row; no HINT text in the visible flow; no REMOVED sentence in the DOM; every catalog key of `inception-copy` and `discovery-copy` matched by a row (keys added after the audit snapshot are added to the spec's Audit with their decision).
- [ ] G4 `tests/guidance.never-hidden.test.tsx`: no alert, StateCard, blocked/unclear badge, check, provenance or gate element inside a hint, on every screen fixture; no V1/V2/V3/V5/V6 key and no `screening-states.ts` key passed as a hint's `textKey` (static check).
- [ ] G5 `tests/density.budget.test.tsx`: per audited screen in its default state, one lede sentence of at most 130 characters, at most 6 hint buttons, zero inline help paragraphs, exactly one primary button, at most one gate; the card limit B2 only on Explore and Review (question 3).
- [ ] G6 Browser suite `tests-browser/guidance.spec.ts`: hint by click, tap and keyboard with focus kept on the button; placement mirrored in Arabic; a warning never inside a hint (Explore thin pool, Harvest capped database, Review existing workspace); moved text attached while closed; recommended never preselected; the Scope and Shape forms completed by keyboard. `rendered-axe.spec.ts` gains open hints and collapsed sections, en and ar, light and dark.
- [ ] G7 The brand book Iconography line for the two exceptions (`docs/ux/brand/BRAND_BOOK.md`); `03-guidance` status line "built"; the Measurement table above filled.

Screens. "Hint" lists the Audit rows moved behind a Hint; "Removed" the rows removed; each screen's test is `tests/guidance.screens.test.tsx` › `<screen>`, which asserts the hints, the removed sentences, the one primary button and the mark, plus the existing screen test kept green.

| Screen | Hint | Removed | One main action (the primary button) | Recommended | Fold (rule 4) |
| :-- | :-- | :-- | :-- | :-- | :-- |
| inception frame (every step) | I-F2 `nothingWritten` (beside "Draft saved") | none | (the step's own) | none | none |
| 01 Scope | I-S5, I-S6, I-S7 | I-S4 (lede sentence 2) | Continue to Explore | none | none |
| 02 Explore (first slice) | I-E8, E10, E19, E23, E26, E29, E30, E32, E35, E38, E39, E41 (at most 6 visible at once) | I-E3, I-E15 | Search the literature, then See {n} directions | "Search again with semantic search" on a thin pool, `Recommended · pool size check` | topics and metrics; papers; databases asked (summary "{n} failed") |
| 03 Direction | I-D4, D8, D17, D19, D24 | I-D5, I-D14 | Pursue {direction}, then Continue to Shape | nothing (the spec says the order is evidence) | none |
| 04 Shape | I-SH6, SH8, SH9, SH10, SH12, and the planned-records help (`04-shape` "The field") | I-SH2 | Continue to concepts and criteria | the leaning lens (`Recommended · word scan of your topic`) and the playbook that matches it | none |
| 05 Criteria | I-C7, C9, C10, C14 (one hint on the list heading), C17 | I-C3, I-C13 | Continue to review | only when an M10b check proposes one (the proposal card) | none (question 3) |
| 06 Review (first slice) | I-R5, R11, R13 | I-R3, I-R9 | Create the workspace (the gate) | the first open check's fix, `Recommended · check {id}` | files and fingerprint into Details |
| 07 Done | none | I-DN2 | Open the workspace | none | none |
| discovery entry | D-DS8, D-DS12, D-DS14 | D-DS11 | Continue at {step} | none (the bar) | none |
| 01 Plan | D-P7, P10, P13, P14, P15, P18 | D-P3, D-P8 | Continue to Recall | none | none |
| 02 Recall | D-R9 (one hint on "Not found"), R12, R13 | D-R3, D-R5, D-R8 | Check these seeds, then Continue to Harvest | none | none |
| 03 Harvest | D-H10, H11, H14, H15, H23 | D-H3, D-H7 | Start the harvest (Finish preparing this corpus in that state) | the size estimate's suggested cap, never pre-filled | none (question 3) |
| 04 Import (discovery visit) | D-I3, D-I5, D-I8 | D-I6 | the screen 11 accept | none | none |
| 05 Duplicates | D-DD8, D-DD9 | D-DD3 | Continue to the report | none | none |
| 06 Report | D-RP5 (one hint on "Completeness"), RP13, RP15 | D-RP2, D-RP3 | I reviewed this text while unreviewed, then Continue to hand-off | none | none (question 3) |
| 08 Hand-off | D-HO3, HO5, HO15 | D-HO10 | Accept this corpus (the gate) | none | none |
| 09 Chase | D-CH5, CH8, CH9, CH10, CH13, CH19 | D-CH3, D-CH17 | Chase citations, then Send these {new} works to screening | none | none (question 3) |

## Findings fixed
None (no assessment finding is in scope).

## Decisions
New choices are recorded in `docs/decisions.md` under "2026-11-19 — M10d" as PROPOSED.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |

## Deferred
- The six existing suggestion mechanisms (pool synonyms, anchor seeds, wizard criteria, the RQ draft, suggested concepts, the derived query) keep their own look. Decision 2026-11-15 item 31 names adopting the proposal card's look as M10d screen work, but `03-guidance` (the M10d contract) does not specify it and it would change controls on four screens; it needs its own spec (proposed below).
