# H-charting-focus-fault: after Ctrl+Down the next study sometimes opened with the focus nowhere
Branch: dev/h/charting-focus-fault (from `origin/main` `21a4e6a3`) · Lane: **STANDARD** · Status: READY FOR PR, not pushed · Started: 2026-11-22

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
1. Ctrl+Down pressed the moment a saved value shows (React schedules its own work there, as in the browser; the next study's read answers a task later): the next study has the focus on its first field. **Fails on `origin/main`**, and also with only the `stillAt` repair, so it tests the cause itself.
2. Alt+A then Ctrl+Down before the save's answer: the focus is on the next study's first field. **Fails on `origin/main`** (it was on that study's Not applicable button).
3. Alt+N, then another field before the save's answer: the focus stays in the other field. **Fails on `origin/main`.**
4. Alt+N with the focus left in the field: the focus moves to the Not reported button (the behaviour kept). Passes before and after.

Before the fix: 3 failed of 4, in each of 3 runs. After: 4 passed, in each of 5 runs.

## Evidence
| Check | Commit | Command | Result |
| :-- | :-- | :-- | :-- |
| Repeat run before the fix | `21a4e6a3` + instrumentation | `RESEARCH_UI_PORT=3191 npx playwright test tests-browser/<instrumented copy>:209 --repeat-each 40` (both projects) | 5 failed, 75 passed (10.6 min) |
| Repeat run after the fix | (pending) | `RESEARCH_UI_PORT=3191 npx playwright test tests-browser/charting-study.spec.ts:209 --repeat-each 40` (both projects) | (pending) |

## Not verified
- The CI failures were not shown to be at a given study: CI logs only the line. The local runs show studies 2, 3 and 6, never the first study on open; a failure on open was not excluded by any run, but no path to it was found by reading.
- Not tried in a real browser by hand; the fix was checked through the browser test and the jsdom tests.
- `apps/research-ui/tests/inception-workbench.test.tsx` "a refused cost read says why…" (times out under load) was not looked into beyond a read of the test; no obvious cause was seen.

## Decisions
Proposed in `docs/decisions.md`, "2026-11-22 — H-charting-focus-fault" (items 1 and 2), for the researcher.
