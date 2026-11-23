# H-charting-row-layout: the charting table's rows were about five lines tall, and the focused row looked cut in two
Branch: dev/h/charting-row-layout (from `origin/main` `6f31f92e`) · Lane: **STANDARD** · Status: **MERGED** as PR #305 on 2026-11-23 (merge commit `9af17212`); decision item 1 answered "Keep 44 px" (2026-11-23) · Started: 2026-11-23

**Lane.** STANDARD, from `docs/architecture/test_gate_policy.md` ("a bounded behavior … change owned by one repository"): UI only, one screen (the charting table) and one opt-in size of the shared `Button`. No contract, API, route, persisted file, copy, catalog or spec change. Gates: the charting vitest files, `tsc`, `lint:ui`, `npm run build`, then the selector's `pr` set (area research-ui) once on the final executable commit. The full suites are CI's (H-gate-and-ci).

## What the researcher saw
On 2026-11-23, on their real review (443 kept studies), the charting table (Full text view) had two layout faults:
1. Each row was about five lines tall: the row's actions ("Attach a PDF", "Paste a link", "Include", "Exclude") stood one per line, some broken across two lines.
2. The focused row's highlight covered only part of the row: the checkbox and title cells stayed white, without the frame.

## Causes
1. The actions are `Button variant="quiet"` with `className="px-1 text-xs"`. `Button` (`components/ui/base.tsx`) joins its base classes and the given ones in one class list, so `px-1` met `px-4` and `text-xs` met `text-[0.9375rem]`, and the stylesheet's order chose the base. Measured in the browser: 15 px text and 16 px padding, not 12 px and 4 px. The columns are narrow beside a long title, so `flex-wrap` put one action per line, and the words wrapped inside the buttons.
2. The two pinned cells (`sticky start-0` / `start-12`) carried `bg-leaf`. A selected row added `bg-brand-soft` beside it on the same cell, and `bg-leaf` won (the selected row's pinned cells stayed white). The row had no background of its own, so unselected rows were two-toned too (white pinned cells, grey `paper` elsewhere). The row's focus outline is painted under the pinned cells (they are positioned, `z-10`), so its start edge and the parts of the top and bottom edges under them did not show. While building the fix a third cause showed: with an opaque background on every row, the next row's background painted over the focused row's bottom edge.
3. Found while checking the scrolled table: the first pinned column was squeezed to its content (40 px) while the second is pinned at 48 px (`start-12`), so an 8 px slit showed the scrolled cells between the two pinned cells.

## Fix
- `Button` gains `size="small"` (opt-in; the regular size is unchanged): `min-h-11` kept (the brand rule: every variant at least 44 px tall), `px-1 text-xs leading-4 gap-1 whitespace-nowrap`. The size replaces the base's padding and text size instead of competing with them. It sets `data-size="small"`.
- The row's actions (file cell, decision cell) and the look-up pieces shown in the table (Confirm / Discard of a fetched file, "What was tried" and its Close) use `size="small"`. The two action pairs sit in `flex flex-nowrap` (`data-row-actions="file|decision"`): the column widens to hold both rather than stacking them; a long title wraps instead.
- The row owns one opaque background: `bg-leaf`, or `bg-brand-soft` when selected. The pinned cells take it (`bg-inherit`), so selected, not-kept (muted, `opacity-70` on the row) or any later row tint read as one band, and the pinned cells still hide what scrolls under them.
- The focused row's frame is drawn by its cells (inset shadows in `--color-focus`): top and bottom on every cell, the start edge on the first, the end edge on the last, mirrored in Arabic (`rtl:`). The row's own outline is removed in normal colours (`not-forced-colors:focus-visible:outline-none` on the row, so the browser's default ring does not come back); `data-focused` is unchanged. In forced colours (Windows High Contrast) the browser drops box shadows, so there the focused row keeps a 2 px outline of its own (`forced-colors:outline-2 …`); the pinned cells still cover its start, as before this change (review repair, `a6e9d59f`).
- The first pinned column is held at 48 px (`w-12 min-w-12`, header and body).

The same `small` size also reaches the one-study view, which renders the same `PendingFile` and `TriedDisclosure` (choice 3 below).

## Measured (browser, before and after)
The packaged app (`npm run build:export`, then `uv run nexus-scholar ui --workspace <temp ws> --port 8795 --no-browser`) on a temporary workspace built from the charting API test helpers (`tests/console/test_charting_api.py`: the published screening of `test_export_api.py`, two kept studies and one no longer kept; a 2 KB PDF attached to one kept study and a link on the other). Driven headless by Playwright (Chromium 1243, from the main checkout's `node_modules`), 2x pixels, the same script for both commits: the first row focused, the second selected. The fixture's titles are short ("Event record 2"), so for the long-title cases the script replaces each title cell's text in the page with a 165-character title (a measurement device; the study titles in the researcher's review are of that length). Heights are `getBoundingClientRect().height` of each `<tr>`, in CSS px.

| Case | Before (`6f31f92e`) | After (`8013d2bb`) | Action lines per cell, before → after |
| :-- | --: | --: | :-- |
| 1440 px wide, long titles, kept row with file or link | 157 | **109** | 2 → 1 |
| 1440 px, short titles | 109 | 109 | 1 → 1 |
| 1440 px, Arabic, long titles | 157 | 109 | 2 → 1 |
| 700 px (table scrolls sideways), long titles, row with a link / with the PDF | 157 / 181 | **141 / 141** | 2 → 1 |
| 700 px, Arabic | 179 / 203 | 141 / 141 | 2 → 1 |
| Not-kept row (no actions), 1440 px | 78.5 | 78.5 | — |
| **Measure only, not built:** the actions and links at 28 px instead of 44 px, 1440 px | — | **77** | 1 |

At 109 px a row is the file line (file name and Open, a 44 px link) plus one line of actions (44 px) plus the cell padding; the title takes two lines beside it. The rows in the researcher's screenshot (about 220 to 270 px) also had a "What was tried" line in the Full text column, which this fixture has not (no look-up was run; no network).

Screenshots, in `.cache/h-charting-row-layout/` of the worktree (gitignored), `before-*.png` and `after-*.png` for each case: `desktop-1440-light`, `desktop-1440-short-titles`, `desktop-1440-dark`, `desktop-1440-arabic`, `desktop-1440-arabic-dark`, `narrow-700-scrolled`, `narrow-700-scrolled-arabic`, `phone-375`, and `after-desktop-1440-dense-28px-measure-only.png`; the numbers in `before-measurements.json` and `after-measurements.json`. `pane-before-*.jpg` are the first look in the app's Browser pane (before the change, including a 1024 px one).

What the screenshots show after the change: one band per row in light and dark, the selected row's tint across the pinned cells, the muted row muted as a whole, the frame complete round the focused row (start edge on the right in Arabic), and, scrolled sideways at 700 px, the pinned cells hiding the scrolled cells with no slit between them. The phone (375 px) shows the read-only cards, not the table, before and after (unchanged).

## Tests
`apps/research-ui/tests/charting.row-layout.test.tsx`, 8 tests (jsdom does no layout, so they pin the classes and structure that give the look):
1. `Button` `small`: `min-h-11`, `px-1`, `text-xs`, `whitespace-nowrap`, none of `px-4`, `text-[0.9375rem]`, `gap-2`; `data-size`.
2. The row's two action pairs: `flex-nowrap`, no `flex-wrap`/`flex-col`; their accessible names and `data-*` hooks; each `data-size="small"` and `min-h-11`; the keyboard order attach, paste link, include, exclude.
3. Confirm, Discard and "What was tried" in the table are `small`.
4. The row owns one background (`bg-leaf`, `bg-brand-soft` when selected); both pinned cells have only `bg-inherit`.
5. A not-kept row is muted on the row; the pinned cells inherit.
6. The first pinned column (header and body) is `w-12 min-w-12`; the second is `start-12`.
7. Every cell of the focused row draws top and bottom; the first the start edge, the last the end edge, both directions; the unfocused row draws nothing.
8. In normal colours the row has no outline of its own (only `not-forced-colors:focus-visible:outline-none`); in forced colours the focused row keeps one and the other row has none (since the review repair).

All 8 **fail on `origin/main`** (the three component files swapped back; run on `8013d2bb`'s version of the test file, before test 8 was extended) and pass on the branch.

## Evidence
| Check | Commit | Command | Result |
| :-- | :-- | :-- | :-- |
| New tests on the old code | `6f31f92e` components + the new test file | `npx vitest run tests/charting.row-layout.test.tsx` | 8 failed of 8 |
| Charting vitest files | `8013d2bb` (tree, before commit) | `npx vitest run tests/charting --maxWorkers=4` | 40 files, 235 of 235 passed |
| Typecheck, UI lint | `8013d2bb` (tree) | `npx tsc --noEmit`; `npm run lint:ui` | pass; 76 of 76 |
| PR gate (`select_test_gate.py --changed origin/main --stage pr`: area research-ui) and build | `8013d2bb` | `git diff --check`; `npm run typecheck`; `npm run lint:ui`; `suite_lock.py -- npm test -- --maxWorkers=4`; `npm run build` | all pass: diff-check, typecheck; lint:ui 76 of 76; vitest **117 files, 1,347 of 1,347 passed** (303 s); build exit 0 |
| Browser look, before and after | `6f31f92e`, `8013d2bb` | export build + `nexus-scholar ui` on port 8795 + the Playwright script (above) | table above; screenshots in `.cache/` |
| Review repair: charting vitest files, typecheck, UI lint, diff-check | `a6e9d59f` (tree, before commit) | `npx vitest run tests/charting --maxWorkers=4`; `npx tsc --noEmit`; `npm run lint:ui`; `git diff --check` | 40 files, 235 of 235 passed; pass; 76 of 76; clean |
| Review repair: forced colours in the browser | `a6e9d59f` (tree) | export build; Playwright `emulateMedia({ forcedColors })`, the first row clicked then ArrowDown, ArrowUp (the row has DOM focus and `:focus-visible`) | normal: row outline `none`, the cells' inset frame drawn; forced: row outline `solid 2px`, cell shadows `none`. `after-forced-colors-none.png`, `after-forced-colors-active.png` |

The full vitest run and `npm run build` were not repeated after the review repair (one class list on the row and one test changed; the charting files ran, and the export build compiled the same CSS). The first export build of the repair printed `Error: Can't resolve './theme.css'` and still finished; a second build right after printed no error. Not looked into.

## Not verified
- Not looked at on the researcher's review (443 studies; their app and workspaces are not touched by build sessions). The heights are from a three-row fixture with a title replaced in the page.
- The "What was tried" line and a waiting fetched file (Confirm / Discard) were not seen in a browser: the fixture has no look-up (that needs the network). They are pinned by the vitest tests only. The same goes for the one-study view, where `PendingFile` and `TriedDisclosure` now render at the small size too.
- Hover: the table has no hover tint, before or after; none was added. The pinned cells would follow one (they inherit the row's background), not seen.
- Keyboard use in the browser: only ArrowDown and ArrowUp were pressed (the forced-colours check; the frame followed the focus). Space, Enter and Tab through the row's actions were not tried in a browser; the keymap vitest files pass and no key handling changed.
- Forced colours were emulated in Chromium, not seen on Windows High Contrast itself.
- The end edge of the frame is off-screen while the last column is scrolled out of view (a frame drawn by cells cannot avoid it); a not-kept row's frame is drawn at 70 % opacity, as its outline was before.
- French was not looked at; its action words are longer, so its columns are wider (they cannot wrap now).
- Other screens that pass `px-1 text-xs` to a `Button` through `className` (for example `query-workbench.tsx`, the term buttons) have the same lost classes; they are not changed here (follow-up).

## Review
`milestone-reviewer`, round 1 on `f97c00ad`: **APPROVE**. It compiled the branch's stylesheet and found every new class (both shadow directions, `bg-inherit`, `min-w-12`, `flex-nowrap`); found no state where a keyboard-focused row has no frame; confirmed `bg-inherit` under `opacity-70` (the row is one stacking context) and the RTL mirroring; found no other test asserting a changed class; and checked the record against the diff. It ran the new file with `charting.fetch-badge` (15 of 15), seven other charting files (38 of 38), `tsc` and `lint:ui` (76 of 76). One P3, taken: in forced colours the browser drops box shadows, and with the row's outline removed a focused row showed no frame there; repaired in `a6e9d59f` (above). Its other notes (the query workbench's lost classes, the end edge off-screen while scrolled, the muted row's frame at 70 %) are in "Not verified" and decision item 9. It noted that `origin/main` had moved to `460f23f3` (three documents-only commits) and that the branch merges into it cleanly; not merged here. The repair was not sent back to the reviewer.

## Decisions
In `docs/decisions.md`, "2026-11-23 — H-charting-row-layout".
