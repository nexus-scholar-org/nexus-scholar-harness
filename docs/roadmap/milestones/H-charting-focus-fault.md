# H-charting-focus-fault: after Ctrl+Down the next study sometimes opened with the focus nowhere
Branch: dev/h/charting-focus-fault (from `origin/main` `21a4e6a3`) · Lane: **STANDARD** · Status: **MERGED 2026-11-23** (PR 293, `main` `ac6d29d8`; `milestone-reviewer` APPROVE, round 2) · Started: 2026-11-22

**Lane.** STANDARD, from `docs/architecture/test_gate_policy.md` ("a bounded behavior … change owned by one repository"): the keyboard focus of one screen (the charting one-study view) and one browser test. No contract, API, route, persisted file, copy or spec change. Gates: the repeat run of the failing browser test, `tsc`, the charting vitest files, then the `pr` set once on the final executable commit.

## What failed
`apps/research-ui/tests-browser/charting-study.spec.ts` "chart five studies from the abstract by keyboard, then undo the last change" failed twice in a row in CI on PR 289 (a documents-only PR), once per theme: `expect(page.locator('[data-field="sensor_problems"] input').first()).toBeFocused()` at line 222 received "inactive" for the full 10 s. For the researcher this means: after Ctrl+Down (or J, or Next) the next study opens with the focus nowhere, and the next key press does nothing until they click.

## Reproduced
On this machine, 40 repeats in each project of an instrumented copy of the test (it logged every `focus()` call with its stack, every focus change, every key and when the fields were replaced; not committed): **5 failed of 80** (4 in `chromium`, 1 in `chromium-dark`).
- 3 of them were this fault: at the move to study 2, to study 3, and to study 6 (the wait added by `e42bfb0c` before the undo step). None on the first study, when the view opens.
- 1 was a second cause in the same family (below, "Also repaired"): Alt+N's focus on Data split landed after the test had put the focus on the next field, so Alt+A went to the wrong field (`aria-pressed` stayed false).
- 1 was a test-only race at the end of the test (below).

## Cause
`apps/research-ui/components/charting-study.tsx` (line numbers as on `origin/main`): the focus after a move is a one-shot request in a ref, `focusAfterLoad` (191), set by `move()` (499) just after `setSwitching(true)`, and spent by the effect at 281–290, which is gated by the state `switching` and re-runs when `record` changes.

The log of a failing run shows the sequence:
1. Alt+A on the last field is saved; the answer's render (a new `record`) is committed and the saved Not applicable shows. React runs that render's effects in a later task (it yields to the browser to paint first).
2. Playwright sees the value and sends Ctrl+Down in that gap. `move()` sets `switching`, then `focusAfterLoad = "first"`.
3. Before rendering the move's update, React runs the effects still waiting, among them the focus effect of the render of step 1. Its closure still has `switching === false`; the ref now says "first". It spends the request and focuses the **previous** study's first field (logged as `focus() … sensor_problems pos=Study 1 of 7`, 2 ms after the key).
4. The move's render replaces the fields with the loading skeleton: the focused input is removed and the focus falls to `body`.
5. The next study arrives; the effect finds no request. The focus stays on `body`.

The same can happen to a researcher who presses Ctrl+Down, J or Next right after a save shows.

## Fix
The request names its study (`{ studyId, which }`), and the effect spends it only when the render it belongs to shows that study (`record.row.study_id === studyId`). A left-over run from the previous study's render now leaves the request for the next one.

**Also repaired, the same family.** Two focuses are asked for after a save's answer: Alt+N / Alt+A put the focus on the special button (`setTimeout` after the save), and Enter in a field moves to the next field (after the save). Both landed wherever the researcher was by then: on the next study after a quick Ctrl+Down (the special button of the same field there), or back on the old field after the researcher went to another one. Each now lands only if the researcher is still on that study and the focus is still in that field, or nowhere (the input was just switched off) (`stillAt`). Decision item 1.

**Test only.** At the end of the browser test, Esc opens the table at `row=STU-006`; the table reads the row and then drops it from the address (the address keeps only the view and filter, `charting-page.tsx` 538), so `toHaveURL(…row=STU-006)` raced with that rewrite (1 failure of 80). The test now waits for the navigation to that address; the row is still checked by the next lines (the counts and the focused STU-006 cell). Decision item 2.

## Tests
`apps/research-ui/tests/charting-study.focus-race.test.tsx`, four tests:
1. Ctrl+Down pressed the moment a saved value shows (React schedules its own work there, as in the browser; the next study's read answers a task later): the next study has the focus on its first field. Done four times, studies 1 to 5. **Fails on `origin/main`** and also with only the `stillAt` repair, so it tests the cause itself. One such move loses the focus in most jsdom runs, not all (the reviewer saw about 10 in 12 on `origin/main`); four moves in a row make a false pass unlikely.
2. Alt+A then Ctrl+Down before the save's answer: the focus is on the next study's first field. **Fails on `origin/main`** (it was on that study's Not applicable button).
3. Alt+N, then another field before the save's answer: the focus stays in the other field. **Fails on `origin/main`.**
4. Alt+N with the focus left in the field: the focus moves to the Not reported button (the behaviour kept). Passes before and after.

Test 1 (four moves): failed in 6 of 6 runs on `origin/main` and 6 of 6 with only `stillAt`, always on the focus at "Study 2 of 5". Tests 2 and 3 failed on `origin/main` in each of 3 runs here and 12 of 12 for the reviewer. After the fix: 4 passed, in each of 6 runs.

## Evidence
| Check | Commit | Command | Result |
| :-- | :-- | :-- | :-- |
| Repeat run before the fix | `21a4e6a3` + instrumentation | `RESEARCH_UI_PORT=3191 npx playwright test tests-browser/<instrumented copy>:209 --repeat-each 40` (both projects) | 5 failed, 75 passed (10.6 min) |
| Repeat run after the fix | `1acfa784` (the tree run, committed unchanged right after) | `RESEARCH_UI_PORT=3191 npx playwright test tests-browser/charting-study.spec.ts:209 --repeat-each 40` (both projects) | **80 passed, 0 failed** (7.0 min) |
| PR gate (`select_test_gate.py --changed origin/main --stage pr`: area research-ui) | `1acfa784` | `git diff --check`; `npm run typecheck`; `npm test`; `npm run build`; `npm run test:browser` | diff-check, typecheck, build: pass. Browser suite: **720 passed, 16 skipped, 0 failed** (20.1 min). Vitest: 1349 passed, 1 failed: `inception-workbench.test.tsx` "a rename keeps the row…" (1.2 s, under load; not touched by this change). That file alone afterwards: 33 of 33 passed |
| Charting one-study vitest files | `1acfa784` + the review repair | `npx vitest run tests/charting-study` | 7 files, 32 of 32 passed |
| Final executable commit | `bf3d6b91` (the review repair, a vitest file only) | `npm run typecheck`; `npm test` | typecheck pass; vitest **109 files, 1350 of 1350 passed** |
| Contract baseline | `5edf2c09` | `uv run python scripts/generate_contract_baseline.py --check` (run by the reviewer) | current |

## Not verified
- The CI failures were not shown to be at a given study: CI logs only the line. The local runs show studies 2, 3 and 6, never the first study on open; a failure on open was not excluded by any run, but no path to it was found by reading.
- Not tried in a real browser by hand; the fix was checked through the browser test and the jsdom tests.
- `apps/research-ui/tests/inception-workbench.test.tsx`: "a refused cost read says why…" (known to time out under load) was not looked into beyond a read of the test; no obvious cause was seen. In this branch's full vitest run another test of that file, "a rename keeps the row…", failed once the same way (about 1.2 s, under load) and passed when the file ran alone. Neither is touched here.
- The build and the browser suite were not run again after the review repair: it changed only the new vitest file, which neither of them reads.

## Review
`milestone-reviewer`, round 1: **CHANGES**, no code defect. Repaired: (1) the after-fix evidence and the gates are recorded above; (2) the test of the cause was timing-dependent, so it now makes the move four times, and the counts above say so; (3) the act flag is restored in `afterEach` and the wait for the saved value has its own time limit, so a failing run cannot leave the flag off; (4) decision item 2 now gives the table's steps in order.

Round 2, on the repair delta `5edf2c09..be977b2d`: **APPROVE**, all four findings repaired, nothing new. The reviewer ran the new test on a copy of the app with the old component swapped in: test 1 (four moves) failed in 6 of 6 runs on `origin/main` and 6 of 6 with only `stillAt`, and all four passed in 6 of 6 on the branch. The reviewer did not re-run the recorded gates.

## Follow-up (not in this change)
- Ctrl+Down and Ctrl+Up are handled before the screen's `switching` check (`charting-study.tsx`, the key handler and `move()`): two moves started before the move's first render (Ctrl+Down then Ctrl+Up quickly) can both run, and the screen can then show one study while the address and the focus request name the other. This was there before; with this change the focus does not land in that state. Found by the reviewer.

## Decisions
In `docs/decisions.md`, "2026-11-22 — H-charting-focus-fault": items 1 and 2 accepted by the researcher 2026-11-23, who approved the push and the PR.
