# H-test-diet

Status: **BUILT 2026-11-23 — see "Review" for the verdict** (branch `dev/h/test-diet`, cut from `origin/main` `8dd7904a`; not pushed). Lane: **RELEASE** (the coordinator's brief: it changes the gates every later milestone runs).

Source: the researcher's decisions of 2026-11-23 in the coordinator session, after `docs/assessment/test-suite-review-2026-11-23.md` (on local branch `dev/docs/project-review-2026-11-23`). Their words: "Delete all browser tests"; "I want to cut the browser tests and also the UI tests. Leave only component tests."; UI unit tests: "Cut scans and whole-page journeys". The coordinator had recommended keeping a small real-browser set; the researcher chose full deletion.

## Definition of done

- [x] The Playwright suites are gone: `tests-browser/` (25 specs, 2 helpers), `tests-live/` (the live gate), `tests-long-strings/` (the 30 % expansion gate), `playwright.config.ts`, `playwright.live.config.ts`, `playwright.long-strings.config.ts`, the committed `screenshots/` (12 PNG; the one the root README shows moved to `docs/images/screening-import-staged.png`), the `test:browser` script, the `@playwright/test` dependency and its lock entries (`npm install --offline`, 3 packages, no network), the CI job `research-ui-browser` with its Chromium download, the browser commands in `test_gate_manifest.json`, and the mentions in `test_gate_policy.md`, `/gate`, `phase-auditor`, the app's README, AGENTS.md, GATES.md, `tsconfig.json`, `.gitignore` files and two source comments.
- [x] Every vitest file is classified (table below), and only scans and multi-step journeys are removed; in mixed files only those tests.
- [x] The scans that guard a decided rule are in one lint file, `apps/research-ui/lint/ui-rules.lint.ts`, run by `npm run lint:ui`, by the local gate (all four stages of the `research-ui` area) and by CI (the `research-ui` job). The dropped ones are listed.
- [x] `vitest.config.ts` caps workers at four; the 150 ms loop in `tests/guidance-screens.tsx` is gone.
- [x] Gate: `tsc --noEmit`, the full vitest before and after, `npm run build`, `lint:ui`; the Python tests that name the gate commands.
- [x] An entry in `docs/decisions.md` with the two lists kept apart.
- [ ] Independent review (`milestone-reviewer`): see "Review".

## What is no longer checked anywhere (the cost of the researcher's choice)

Nothing replaces the browser suites. These were checked by them alone and are now checked by nobody until someone looks at the app:

1. **Hydration errors.** `hydration.spec.ts` loaded every page and failed on React #418, the error that broke every page in PR #252. The lint keeps the static rule that caused it (a server module takes only components from a client module, and the theme boot script comes from a module the server inlines), but a hydration error with another cause would pass every gate.
2. **Real-browser focus.** Focus rings as rendered (`--color-focus` on links and the skip link, cross-checked), focus after Ctrl+Down in the charting study view (the fault of H-charting-focus-fault, PR #293, which the browser suite reproduced; a jsdom regression test of the race is kept, `charting-study.focus-race`), focus order across the shell, and the keyboard budget "ten records in at most ten keypresses each" in Triage.
3. **Contrast.** `rendered-axe.spec.ts` ran axe on the rendered CSS in light and dark. jsdom reports `color-contrast` as incomplete, never as passed, so contrast is now unchecked in both themes.
4. **Layout overflow.** Horizontal overflow at 375 px and 1440 px on the real layout (`overflow.spec.ts` and the per-screen loops in `discovery`, `inception`, `charting`), the 30 % string-expansion gate (`tests-long-strings`), right-to-left placement as rendered, and the per-locale and per-viewport matrices. jsdom does no layout.
5. **The one run against the real engine.** `tests-live/triage-desktop.spec.ts` screened the 30 golden records in the real UI against a real console. Every remaining UI test talks to a fake engine; only the screening screens' fakes are checked against recordings of the engine (`tests/fixtures/page-engine.json`).
6. **Locale routing before JavaScript.** `lang` and `dir` on the server's raw HTML (`locale-routing.spec.ts`).
7. **Privacy hygiene of the served app.** No request to a non-localhost origin while a page runs (the browser fixture failed any test that made one), no absolute non-localhost URL in the served HTML, no analytics global, no credential-shaped literal in the configs (`hygiene.spec.ts`).
8. **The shipped CSS.** No dangling token, no raw palette utility and no retired palette in the CSS the browser receives (`hygiene.spec.ts`). The theme rules on `theme.css` stay in the lint; the built output is not checked. (Checked by hand once on this build: no `slate-` utility in `.next/static/css`.)
9. **Whole-flow behaviour in the production build:** downloads arriving as real files (Export, the charting exports), server-sent job events as a real `text/event-stream`, the restart wait of Open on Workspaces, polling and cancel of agent proposals, the real Next router and the same-origin proxy.
10. **The charting keyboard budget.** Under 50 ms a move in Chromium (`charting-study.spec.ts`), and its jsdom counterpart `charting.budget.test.tsx` (a timed 120-key walk, removed as a journey).
11. **Screenshots.** Nothing writes the reference captures any more; the README's one image is now a static file.
12. **One request body.** The approval-code step's `pairing/begin` request (`{batch: 1}` for a single batch) is no longer asserted; the code being sent trimmed and the field cleared are (choice 10).

The vitest cut adds, beyond the browser suites: 39 multi-step journeys (listed below; each crossed several submits or records), so a fault that appears only after a second or third write on the same page, or when moving between records, is less likely to be caught.

## Choices made in the build (for the reviewer)

1. **The rule applied to every vitest test.** *scan*: the assertions are about the text of source, CSS, config or catalogue files rather than rendered output. *journey*: three or more state-changing actions (writes, submits, moves to another step or record) with assertions between them, or a walk across steps or records doing work on more than one. Kept by three carve-outs: (a) keymap tests, whose purpose is one screen's key bindings, each key pressed and its effect asserted (for example `charting.keymap` "one status key on the focused row saves at once", `charting-study.keymap` "Alt+N and Alt+A ..."); (b) one decision made of several keys or clicks counts as one action, including a refused or cancelled first attempt (for example `triage` "picks reason chip 3 by keyboard ... confirms with Enter", `screening-pilot` "asks first, writes nothing on Not now ..."); (c) `charting-study.focus-race`, the only remaining guard of the fault of PR #293. Opening and dismissing a dialog with Esc or Cancel is not a state change.
2. **Classification by four read-only scouts, then one rule by the lead.** The scouts applied the brief with different strictness (one counted every key sequence as a journey, 40 in 43 files); the lead re-decided every journey against the rule above, per test. Borderline calls kept: `triage` 348, 391, 458, 523, 536, 627, 644, 712; `discovery-plan-amend` 70, 109, 144; `discovery-report` 103; `inception-sample` 197; `inception-workbench` 198; `screening-pilot` 221, 239; in group 1 `charting-study.keymap` 51, 94, 116, `charting.cells-keymap` 31, 63, 125, 153, `charting.charting-view` 111, `charting.states` 98, 155, `charting.fetch-decide-guard` 49, 92, `charting.fetch-discard` 40, 61, 89, `charting.fetch-plan` 133, `charting.fetch-run` 47, `charting.fetch-study` 65, 83, `charting.form-panel` 110, `charting.keymap` 39, 59, 108, 124, 144, `checks-panel` 258. Borderline calls removed: `triage` 255, 319, 659, 749; `discovery-plan-amend` 127. `inception-direction` 112 and 205 were removed in the first build and restored after review (finding 4): 205 has no write and one dialog dismissed with Esc, 112 two reads on one draft, both under the rule.
3. **The lint runs on vitest** (`vitest.lint.config.ts`, environment `node`, one worker), not on a hand-written Node script: the catalogues are TypeScript modules loaded through the `@/` alias, and keeping the scans' logic unchanged avoided rewriting 72 checks. It is one file outside `tests/`, not part of `npm test`, and it refuses to run from any folder but the app root. It took 4.7 s. A deliberate literal `aria-label` in `components/screening-export.tsx` made two N9 rules fail (then reverted), so it is not vacuous.
4. **`lint/` is excluded from Tailwind's source scan** (`@source not "../lint/**"` in `globals.css`), because the theme rule names retired variables on purpose; the same reason `tests/` is excluded.
5. **Two dropped boundary checks were restored by the lead**: "the document renders the theme boot script from a module the server inlines" and the guard on the boundary parser. With `hydration.spec.ts` gone they are the only trace of the #418 guard.
6. **The deterministic wait in `guidance-screens.tsx`.** `settle()` no longer waits 150 ms per read (up to 3 s per state); it flushes zero-delay turns inside `act` until three turns leave the word count unchanged. The two Criteria states now also wait for `[data-criteria-block]`, drawn only from the engine's answer, which the page asks 200 ms after the draft (the old real-time loop had covered that debounce by accident; without it "05 Criteria … one edit hint" failed once). The five dependent files pass (100 tests).
7. **Kept, though only the browser suites used them:** `scripts/golden_screening_sandbox.py` and its Python test (the live gate's console; a usable tool on its own, and Python is outside this part's scope), `next.config.ts`'s `NEXT_DIST_DIR` (the export build uses it), and the `.next-live/` and `.next-longstrings/` ignore lines (so a folder left on a developer machine stays out of `git status`).
8. **Comments that named a deleted spec** as the guard of something were rewritten to say no test checks it (`globals.css`, `lib/screening-api.ts`, the app README); historical work packets and milestone records were left as they are. GATES.md carries a dated note that every row citing a browser spec is history.
9. **Shared fixtures were not trimmed.** Branches of the fake engines in `tests/fixtures/` that only removed tests used may remain (the scouts removed per-file helpers only; one fake-engine branch for the pairing redeem in `screening-publish` was left as harmless).
10. **Seven one-decision tests added after review (finding 1).** Six removed journeys were the only UI test of a first write that matters; each now has a test that starts from a seeded engine state and makes one decision, so they fit the rule: `triage` "Change my decision after the reveal sends an event that supersedes the earlier one, with revealed_after_decision true" and "Undo on a changed decision restores the previous outcome, superseding the change"; `screening-publish` "sends a typed approval code once, trimmed, and clears the field" and "Publish the screening, with every batch approved, sends one publish request and says Published"; `inception-criteria` "Accept on the drafted criterion saves criteria_decisions[its engine id] = true"; `inception-review` "Replace, and discard the screening link sends the typed slug as confirm_discard_screening_binding"; `charting.form-panel` "before any value, Merge with… and confirm saves one column derived from both". Each was made to fail by changing its key expected value, then restored.
11. **Lint additions after review:** the `SCHOLAR_OPENALEX_KEY` line rule (finding 2) and the scan-root check of the N9 to N12 rules (finding 5). The app README, I18N.md, the three fake engines' headers and three lines of the production plan no longer present a browser spec as current (findings 3, 6, 7, 8).

## Evidence

All on the researcher's PC (Windows, 8 cores), `apps/research-ui`, with `node_modules` from `npm ci --offline`. No network was used.

| What | Commit | Command | Result |
| :-- | :-- | :-- | :-- |
| vitest before | `origin/main` `8dd7904a` (detached) | `npx vitest run` (default workers) | 119 files, **1,441 tests passed**, 0 failed; **203.7 s** (208 s wall) |
| vitest after (round 1) | `328c31d6` working tree | `npx vitest run` (`maxWorkers: 4`) | 115 files, **1,312 tests passed**, 0 failed; **225.5 s** (230 s wall) |
| vitest after repairs | `82c80973` | `npx vitest run` (`maxWorkers: 4`) | 115 files, **1,321 tests passed** (1,312 + 7 new + 2 restored), 0 failed; **206.3 s** (210 s wall) |
| new tests can fail | `82c80973` working tree | each of the 7 new tests with its key expected value changed, then restored | each failed; all restored |
| five files of the new tests | same | `npx vitest run` on triage, screening-publish, inception-criteria, inception-review, charting.form-panel | 5 files, 99 tests passed |
| lint | `82c80973` | `npm run lint:ui` | 1 file, 74 checks passed (72 written; one runs per locale); 4.7 s on `328c31d6` with 72 |
| lint can fail | same, one line added then removed | literal `aria-label` appended to `components/screening-export.tsx` | 2 failed (both N9 rules), 70 passed; file restored |
| guidance files after the wait change | same | `npx vitest run` on `guidance.screens`, `guidance.audit`, `guidance.never-hidden`, `guidance.words`, `density.budget` | 5 files, 100 tests passed, 26.7 s |
| type check | same | `npx tsc --noEmit` | clean, 21 s |
| type check after repairs | `82c80973` | `npx tsc --noEmit` | clean |
| production build | same | `npm run build` | passed, 51 s |
| gate selector | same | `uv run pytest tests/unit/test_select_test_gate.py -q`; `uv run python scripts/select_test_gate.py --check` | 40 passed; `OK: 24 tasks, 19 areas, 4 stages` |
| selector area `pr` | same | `uv run pytest tests/unit/test_select_test_gate.py tests/conformance -q`; `uv run ruff check scripts/` | 723 results, 2 failed: `test_e3_neg_050_pinned_stale_bytes_are_not_indexed[cli]` and `test_e3_diagnostic_real_chroma_index_workspace_reproducer`, both `No module named chromadb` (this worktree was synced with `--extra dev` only; the RAG code is being removed by the parallel cleanup); ruff clean |
| contract and whitespace | same | `generate_contract_baseline.py --check`; `git diff --check origin/main` | baseline current; clean |
| full Python suite | `82c80973` | `uv run pytest -q -n 4 --dist worksteal` (with `--extra dev --extra pdf --extra rag`, synced offline) | **6,590 results: 6,575 passed, 15 skipped, 0 failed**; 917 s (counted from the progress lines; this pytest prints no summary line) |
| lock file | same | `npm install --offline` after removing `@playwright/test` | removed 3 packages (`@playwright/test`, `playwright`, `playwright-core`), 46 lines |

**What the numbers say.** The cut removed 129 executed tests (9 %), 126 written ones. The full run did not get faster: 4 workers instead of vitest's default cost more than the cut saved. jsdom is created once per file and is 42 % of the tracked time in both runs, so the next saving is in the runner settings (one jsdom per worker), not in the number of tests; that is not part of this change. The worker cap is for stability under parallel sessions, which this run could not measure (the PC was otherwise idle).

## Classification of the vitest suite (before the cut)

Written tests: `it`/`test` as written, an `it.each` counted once (1,258 written = 1,441 executed). *Kind* is the file's kind after the lead's rule: *mixed* means at least one test was removed and one kept. Totals: 119 files; 13 component, 45 screen-state, 8 unit, 49 mixed, 3 all scans (deleted), 1 all journey (deleted). Removed: 85 scans (84 classified, plus the parser check of `server-client-boundary`, which moved to the lint with its file) and 39 journeys; kept 1,134 written tests; then 7 one-decision tests added after review (choice 10), so the suite has 1,141 written tests.

| File | Kind | Written | Scans out | Journeys out | Kept | Note |
| :-- | :-- | --: | --: | --: | --: | :-- |
| accessibility-in-process.test.tsx | component | 5 | 0 | 0 | 5 |  |
| charting-study.focus-race.test.tsx | screen-state | 4 | 0 | 0 | 4 |  |
| charting-study.history.test.tsx | screen-state | 3 | 0 | 0 | 3 |  |
| charting-study.i18n.test.ts | mixed | 3 | 2 | 0 | 1 |  |
| charting-study.keymap.test.tsx | screen-state | 9 | 0 | 0 | 9 |  |
| charting-study.mobile.test.tsx | screen-state | 2 | 0 | 0 | 2 |  |
| charting-study.no-fulltext.test.tsx | screen-state | 2 | 0 | 0 | 2 |  |
| charting-study.readonly.test.tsx | screen-state | 9 | 0 | 0 | 9 |  |
| charting.budget.test.tsx | journey | 1 | 0 | 1 | 0 | file deleted (timed 120-key walk) |
| charting.bulk-confirm.test.tsx | screen-state | 5 | 0 | 0 | 5 |  |
| charting.cells-keymap.test.tsx | screen-state | 10 | 0 | 0 | 10 |  |
| charting.charting-view.test.tsx | screen-state | 11 | 0 | 0 | 11 |  |
| charting.fetch-badge.test.tsx | screen-state | 7 | 0 | 0 | 7 |  |
| charting.fetch-confirm.test.tsx | mixed | 11 | 0 | 2 | 9 |  |
| charting.fetch-decide-guard.test.tsx | screen-state | 6 | 0 | 0 | 6 |  |
| charting.fetch-discard.test.tsx | screen-state | 6 | 0 | 0 | 6 |  |
| charting.fetch-filter.test.tsx | screen-state | 3 | 0 | 0 | 3 |  |
| charting.fetch-i18n.test.ts | mixed | 5 | 2 | 0 | 3 |  |
| charting.fetch-keymap.test.tsx | screen-state | 6 | 0 | 0 | 6 |  |
| charting.fetch-mobile.test.tsx | screen-state | 4 | 0 | 0 | 4 |  |
| charting.fetch-not-by-colour.test.tsx | screen-state | 1 | 0 | 0 | 1 |  |
| charting.fetch-plan.test.tsx | screen-state | 8 | 0 | 0 | 8 |  |
| charting.fetch-run.test.tsx | screen-state | 7 | 0 | 0 | 7 |  |
| charting.fetch-study.test.tsx | screen-state | 6 | 0 | 0 | 6 |  |
| charting.fetch-summary.test.tsx | screen-state | 8 | 0 | 0 | 8 |  |
| charting.fetch-tried.test.tsx | screen-state | 6 | 0 | 0 | 6 |  |
| charting.form-panel.test.tsx | mixed | 14 | 0 | 7 | 7 |  |
| charting.i18n.test.ts | mixed | 3 | 2 | 0 | 1 |  |
| charting.keymap.test.tsx | mixed | 8 | 0 | 1 | 7 |  |
| charting.mobile-readonly.test.tsx | screen-state | 3 | 0 | 0 | 3 |  |
| charting.not-by-colour.test.tsx | screen-state | 2 | 0 | 0 | 2 |  |
| charting.number-reading.test.ts | unit | 2 | 0 | 0 | 2 |  |
| charting.report.counts.test.tsx | screen-state | 9 | 0 | 0 | 9 |  |
| charting.report.export-line.test.tsx | screen-state | 11 | 0 | 0 | 11 |  |
| charting.report.export-menu.test.tsx | mixed | 5 | 0 | 1 | 4 |  |
| charting.report.i18n.test.tsx | mixed | 5 | 3 | 0 | 2 |  |
| charting.report.methods.test.tsx | screen-state | 10 | 0 | 0 | 10 |  |
| charting.report.mobile.test.tsx | screen-state | 2 | 0 | 0 | 2 |  |
| charting.report.states.test.tsx | mixed | 15 | 1 | 0 | 14 |  |
| charting.stale-rows.test.tsx | screen-state | 1 | 0 | 0 | 1 |  |
| charting.states.test.tsx | mixed | 14 | 1 | 0 | 13 |  |
| checks-panel.test.tsx | mixed | 23 | 1 | 1 | 21 |  |
| console-proxy.test.ts | unit | 41 | 0 | 0 | 41 |  |
| database-picker.test.tsx | component | 10 | 0 | 0 | 10 |  |
| density.budget.test.tsx | screen-state | 1 | 0 | 0 | 1 |  |
| details-rule.test.ts | scan | 2 | 2 | 0 | 0 | file deleted |
| discovery-chase.test.tsx | mixed | 15 | 1 | 0 | 14 |  |
| discovery-combined.test.tsx | mixed | 15 | 1 | 0 | 14 |  |
| discovery-copy.test.ts | mixed | 5 | 4 | 0 | 1 |  |
| discovery-dedup.test.tsx | screen-state | 7 | 0 | 0 | 7 |  |
| discovery-engine-fake.test.ts | unit | 15 | 0 | 0 | 15 |  |
| discovery-estimate.test.tsx | mixed | 26 | 0 | 1 | 25 |  |
| discovery-frame.test.tsx | component | 6 | 0 | 0 | 6 |  |
| discovery-handoff.test.tsx | screen-state | 12 | 0 | 0 | 12 |  |
| discovery-harvest.test.tsx | mixed | 26 | 0 | 1 | 25 |  |
| discovery-import.test.tsx | screen-state | 6 | 0 | 0 | 6 |  |
| discovery-overview.test.tsx | screen-state | 7 | 0 | 0 | 7 |  |
| discovery-plan-amend.test.tsx | mixed | 15 | 0 | 1 | 14 |  |
| discovery-plan.test.tsx | screen-state | 25 | 0 | 0 | 25 |  |
| discovery-preparation.test.tsx | mixed | 19 | 1 | 1 | 17 |  |
| discovery-proposals.test.tsx | component | 5 | 0 | 0 | 5 |  |
| discovery-recall.test.tsx | mixed | 13 | 0 | 1 | 12 |  |
| discovery-report.test.tsx | screen-state | 9 | 0 | 0 | 9 |  |
| doi-link-name.test.tsx | component | 2 | 0 | 0 | 2 |  |
| export-segment-files.test.ts | unit | 2 | 0 | 0 | 2 |  |
| guidance-copy.test.ts | mixed | 3 | 2 | 0 | 1 |  |
| guidance.audit.test.tsx | mixed | 4 | 3 | 0 | 1 |  |
| guidance.never-hidden.test.tsx | mixed | 2 | 1 | 0 | 1 |  |
| guidance.screens.test.tsx | screen-state | 14 | 0 | 0 | 14 |  |
| guidance.words.test.tsx | screen-state | 1 | 0 | 0 | 1 |  |
| highlighted-text.test.tsx | unit | 10 | 0 | 0 | 10 |  |
| hint.rtl.test.tsx | unit | 4 | 0 | 0 | 4 |  |
| hint.test.tsx | component | 10 | 0 | 0 | 10 |  |
| i18n-catalog.test.ts | mixed | 27 | 10 | 0 | 17 |  |
| i18n-direction-source.test.ts | scan | 6 | 6 | 0 | 0 | file deleted |
| i18n-render.test.tsx | component | 13 | 0 | 0 | 13 |  |
| inception-answers.test.tsx | mixed | 15 | 0 | 1 | 14 |  |
| inception-copy.test.ts | mixed | 6 | 5 | 0 | 1 |  |
| inception-criteria-block.test.tsx | mixed | 17 | 1 | 0 | 16 |  |
| inception-criteria.test.tsx | mixed | 9 | 0 | 2 | 7 |  |
| inception-direction.test.tsx | screen-state | 26 | 0 | 0 | 26 | 112 and 205 removed, then restored after review finding 4 |
| inception-done.test.tsx | screen-state | 5 | 0 | 0 | 5 |  |
| inception-explore.test.tsx | mixed | 55 | 0 | 3 | 52 |  |
| inception-import.test.tsx | mixed | 8 | 0 | 1 | 7 |  |
| inception-legs.test.tsx | component | 9 | 0 | 0 | 9 |  |
| inception-review.test.tsx | mixed | 17 | 0 | 1 | 16 |  |
| inception-sample.test.tsx | mixed | 21 | 2 | 3 | 16 |  |
| inception-scope.test.tsx | screen-state | 7 | 0 | 0 | 7 |  |
| inception-shape.test.tsx | mixed | 5 | 0 | 1 | 4 |  |
| inception-start.test.tsx | screen-state | 4 | 0 | 0 | 4 |  |
| inception-workbench.test.tsx | mixed | 28 | 1 | 4 | 23 |  |
| keyboard-traversal.test.tsx | component | 5 | 0 | 0 | 5 |  |
| loading-frame.test.tsx | screen-state | 3 | 0 | 0 | 3 |  |
| local-time.test.tsx | unit | 3 | 0 | 0 | 3 |  |
| next-step-bar.test.tsx | mixed | 27 | 2 | 0 | 25 |  |
| page-requests.test.tsx | screen-state | 3 | 0 | 0 | 3 |  |
| plural.test.tsx | mixed | 7 | 2 | 0 | 5 |  |
| proposals.test.tsx | mixed | 15 | 1 | 0 | 14 |  |
| read-sharing.test.ts | unit | 8 | 0 | 0 | 8 |  |
| recommended.test.tsx | component | 6 | 0 | 0 | 6 |  |
| screening-agreement.test.tsx | mixed | 6 | 1 | 0 | 5 |  |
| screening-export.test.tsx | mixed | 20 | 4 | 0 | 16 |  |
| screening-home.test.tsx | mixed | 20 | 3 | 0 | 17 |  |
| screening-import.test.tsx | mixed | 18 | 1 | 0 | 17 |  |
| screening-pilot-card.test.tsx | mixed | 11 | 1 | 0 | 10 |  |
| screening-pilot.test.tsx | mixed | 30 | 1 | 0 | 29 |  |
| screening-prepare.test.tsx | mixed | 22 | 1 | 0 | 21 |  |
| screening-proposals.test.tsx | mixed | 20 | 3 | 0 | 17 |  |
| screening-publish.test.tsx | mixed | 19 | 3 | 1 | 15 |  |
| screening-v1-client.test.ts | mixed | 7 | 1 | 0 | 6 |  |
| server-client-boundary.test.ts | scan | 3 | 3 | 0 | 0 | file deleted; its three checks are in lint:ui |
| shell.test.tsx | component | 18 | 0 | 0 | 18 |  |
| state-card.test.tsx | component | 2 | 0 | 0 | 2 |  |
| theme.test.tsx | mixed | 5 | 3 | 0 | 2 |  |
| triage-pilot.test.tsx | screen-state | 11 | 0 | 0 | 11 |  |
| triage.highlights.test.tsx | screen-state | 17 | 0 | 0 | 17 |  |
| triage.test.tsx | mixed | 51 | 2 | 4 | 45 |  |
| ui-base.test.tsx | component | 4 | 0 | 0 | 4 |  |
| workspaces.test.tsx | mixed | 12 | 1 | 0 | 11 |  |

### Journeys removed (39)

- `charting.budget.test.tsx`: 56 "draws ${ROWS} rows by 5 columns and walks them by keyboard within the stated budget"
- `charting.fetch-confirm.test.tsx`: 60 "asks first when the file was not found by the check, or the same bytes wait for another record"; 86 "with several rows selected C confirms nothing and says one at a time; a row with no file says so"
- `charting.form-panel.test.tsx`: 57 "before any value each change saves at once, from the version it was made on, with no reason"; 144 "a changed type marks the charted cells Chart again with the earlier value; Undo these changes drops a draft"; 197 "Merge with� makes one Text column from two, recorded as a merge; its cells show both earlier values to chart a"; 262 "before any value a merge saves at once; Esc and Cancel close the chooser, not the panel"; 301 "a third column merged into a merge not yet recorded names all three sources"; 332 "a split of a column not yet recorded names the saved sources, so the engine accepts it"; 365 "a column removed while the chooser is open: the choice moves to a column that exists, and Merge still works"
- `charting.keymap.test.tsx`: 87 "I includes the focused row; E then a number then Enter excludes it with that reason; OTHER asks for words"
- `charting.report.export-menu.test.tsx`: 58 "/charting/report: each download asks its own format and view and saves the engine's file"
- `checks-panel.test.tsx`: 90 "Dismiss of a warning needs a reason; sends one POST with subject, digest and reason; moves the row to Dismisse"
- `discovery-estimate.test.tsx`: 382 "answers a what-if after a recall-check estimate from the cache: no refresh with another pace"
- `discovery-harvest.test.tsx`: 47 "prints the SCHOLAR_MAILTO line; Check again re-reads and starts nothing"
- `discovery-plan-amend.test.tsx`: 127 "an edit while the confirmation is open closes it, so the version recorded is always the one on screen"
- `discovery-preparation.test.tsx`: 93 "keeps Stop after the search; a stop there ends the run as stopped before the next step"
- `discovery-recall.test.tsx`: 107 "prints the SCHOLAR_MAILTO line for MAILTO_NOT_SET and checks again"
- `inception-answers.test.tsx`: 84 "shows every exclusion's reason and lets the researcher change an out-of-scope line's"
- `inception-criteria.test.tsx`: 36 "records Accept by the engine's id, then saves and goes to Review"; 51 "adds and removes a typed criterion, names a missing side, and ticks every matrix column"
- `inception-explore.test.tsx`: 467 "offers the failed search's Search again only while a search could be sent: none without a database or with a q"; 592 "maps PROVIDER_UNKNOWN to the spec card with the code under Details; Reset the databases ticks every database i"; 617 "Reset the databases ticks every database in the engine's own order of databases_available"
- `inception-import.test.tsx`: 86 "offers Read it again when the source changed before the create"
- `inception-review.test.tsx`: 97 "needs the typed slug for a workspace with screening; the engine compares it"
- `inception-sample.test.tsx`: 120 "reports a direction that went away: before and after are the engine's directions"; 136 "Undo on the toast and Put back each send remove with the key"; 221 "warns before the first mark after a bind, sends nothing until confirmed, then shows the stale note"
- `inception-shape.test.tsx`: 13 "marks the engine's leaning, applies nothing, and drafts RQ1 only on request"
- `inception-workbench.test.tsx`: 152 "concept edits: rename, add and remove a term, split a term out, remove a concept; AND between, OR inside; an e"; 178 "merges two concepts under a name that starts as the first's, and shows the last counted and this version side "; 248 "after a real seed check, an edit shows the seed check of the new version (review C round 3)"; 269 "compares with a staged Scopus export: the report line, the measure, the missing records and their terms, appli"
- `screening-publish.test.tsx`: 139 "asks the engine to print a code, sends the typed code once, clears it, then publishes"
- `triage.test.tsx`: 255 "a change after the reveal supersedes the decision and shows the engine's stamp; undo restores the previous one"; 319 "sends proposal_shown with revealed_after_decision false, and true for a change after a reveal"; 659 "shows no Undo on a first decision, and Undo once there is something to undo"; 749 "with drafts and the default setting, N after the last record reaches the hand-off"

### Scans moved to `lint/ui-rules.lint.ts` (68, plus four added by the lead: the two boundary checks, the `SCHOLAR_OPENALEX_KEY` line and the scan-root check)

Per source file (each `describe` in the lint names it): locale parity of keys, placeholders and non-empty values for every catalogue (`messages/*`, charting, fetch, report, checks, discovery, inception, guidance, workbench, proposals, next-step, plural, triage, the screening copy objects); a refusal card or words for every refusal code in every locale; no literal `aria-label`/`title`/`alt`/`placeholder` in components (N9); logical, not physical, layout properties in components and the stylesheet (N10); no mirrored icon (N11); no browser storage or network at render time (N12); 44 px `<summary>` targets with a focus ring; the brand untranslated and no English sentence in a translation; `SCHOLAR_MAILTO`/`SCHOLAR_OPENALEX_KEY` untranslated; hints never carry a warning or refusal key; every catalogue key has a guidance-audit row; the default agent model is the cheapest listed in `prices.toml`; the theme is current with the brand tokens, every brand colour has a light and dark value and retired names stay out; the server/client module boundary (React #418); retired Publish wording; the workspaces copy and nav check.

- `charting-study.i18n.test.ts`: 2
- `charting.fetch-i18n.test.ts`: 2
- `charting.i18n.test.ts`: 2
- `charting.report.i18n.test.tsx`: 3
- `charting.report.states.test.tsx`: 1
- `charting.states.test.tsx`: 1
- `checks-panel.test.tsx`: 1
- `details-rule.test.ts`: 2
- `discovery-chase.test.tsx`: 1
- `discovery-copy.test.ts`: 3
- `discovery-preparation.test.tsx`: 1
- `guidance-copy.test.ts`: 2
- `guidance.audit.test.tsx`: 1
- `guidance.never-hidden.test.tsx`: 1
- `i18n-catalog.test.ts`: 7
- `i18n-direction-source.test.ts`: 5
- `inception-copy.test.ts`: 4
- `inception-criteria-block.test.tsx`: 1
- `inception-sample.test.tsx`: 2
- `inception-workbench.test.tsx`: 1
- `next-step-bar.test.tsx`: 2
- `plural.test.tsx`: 2
- `proposals.test.tsx`: 1
- `screening-agreement.test.tsx`: 1
- `screening-export.test.tsx`: 3
- `screening-home.test.tsx`: 2
- `screening-import.test.tsx`: 1
- `screening-pilot-card.test.tsx`: 1
- `screening-pilot.test.tsx`: 1
- `screening-prepare.test.tsx`: 1
- `screening-proposals.test.tsx`: 2
- `screening-publish.test.tsx`: 2
- `server-client-boundary.test.ts`: 1
- `theme.test.tsx`: 3
- `triage.test.tsx`: 1
- `workspaces.test.tsx`: 1

### Scans dropped (14)

- `discovery-combined.test.tsx`: no catalog string says an export cannot be added after a harvest, in any locale -- pins one decided sentence after finding 26; the rendered Harvest test (line 207) already checks the shown sentence
- `discovery-copy.test.ts`: the help-sentence half of "prints the SCHOLAR_OPENALEX_KEY line untranslated and never calls the email an OpenAlex requirement (F12)" (its wording only); the line half is in the lint (review finding 2)
- `guidance.audit.test.tsx`: reads every row of the spec's Audit, each id once, each key cell resolved -- tests the fixture parser, not the product
- `guidance.audit.test.tsx`: states the same counts per decision as the spec's table -- doc consistency only; ordinary review covers it
- `i18n-catalog.test.ts`: declares the key set once, in the catalog index -- tautology
- `i18n-catalog.test.ts`: maps every nav id to a key that exists in every catalog -- covered by the key-parity rule and by the MessageKey type
- `i18n-catalog.test.ts`: matches SHA-256 for ${path} -- breaks on every legitimate script or dependency change; dependency changes are reviewed in the diff
- `inception-copy.test.ts`: retires the not-built step tag and the recon note (M4d) -- one-off retirement check
- `screening-export.test.tsx`: has the three variants in every locale: small completeness check; general key-parity lint covers it
- `screening-home.test.tsx`: review F2: the summary fixture carries the flag the engine writes: pins a test fixture file's content, no user-visible rule
- `screening-proposals.test.tsx`: has the stopping sentence in every locale: only a non-empty check, covered by key parity
- `screening-publish.test.tsx`: names the approver in every locale: covered by parity lint
- `screening-v1-client.test.ts`: covers every fixture the engine writes: hand-maintained file-structure bookkeeping
- `triage.test.tsx`: names the list and the answers in every locale: subsumed by the parity and non-empty test

## Not verified

- **CI.** Nothing was pushed; the edited `ci.yml` (one job fewer, one lint step more) has not run. The number of required checks goes from 12 to 11 (`research-ui-browser` is gone); a branch protection rule that still requires it would wait forever. That is the coordinator's to adjust when merging.
- **Stability under load.** The worker cap and the deterministic wait were run on an otherwise idle PC; whether they remove the time-outs seen when sessions run suites together is not measured.
- **Fixture drift.** No remaining check compares the discovery, inception and charting fakes with the real engine (only the screening pages are answered from recordings).
- **The 1,312 after-count against a second run.** One full run after the cut; flakiness was not sampled.

## Review

**Round 1** (`milestone-reviewer`, on `328c31d6`): **CHANGES**, 3 P2 and 6 P3. All fixed in `82c80973`:

1. (P2) Six removed journeys were the only UI test of a first write: fixed by seven one-decision tests (choice 10); `pairing/begin`'s body stays unchecked (no-longer-checked item 12).
2. (P2) The `SCHOLAR_OPENALEX_KEY` line rule was claimed but not in the lint: added.
3. (P2) `I18N.md` still named browser specs and the deleted source test as current: rewritten with dates.
4. (P3) `inception-direction` 112 and 205 did not meet the rule: restored.
5. (P3) The scan-root check was dropped on a false premise: added to the lint.
6. (P3) README named a non-existent `scripts/lint-ui.mjs`: fixed.
7. (P3) The fake engines' headers named the Playwright spec: fixed.
8. (P3) The production plan still required Playwright in three places: dated notes, and decision item 1 names them.
9. (P3) The full Python suite asked by the selector at `pr` was not run: run once on `82c80973`, 6,575 passed, 15 skipped, 0 failed (Evidence).

Reviewer's follow-ups, not fixed here: the Explore guidance mounts swallow a missing table (`tests/guidance-screens.tsx`, the `.catch(() => undefined)` already on `main`); the dropped `screening-v1-client` fixture-coverage check (named in decision item 4).
