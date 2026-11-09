# M8-triage Triage on one screen, the checklist optional
Branch: dev/m8/triage-no-scroll · Lane: **STANDARD** (UI and spec only: no contract, engine, identity or publication change; the methods paragraph is unchanged by the researcher's choice) · Status: READY FOR PR (focus screen added after the researcher tried the app; its review CHANGES fixed; push and PR await the researcher) · Started: 2026-11-09

Why: the researcher's own run on real IEEE records (2026-11-09). The triage screen scrolls, and the long checklist has to be answered for every record before Include is possible. A redesign session's triage mockup (uncommitted, `.taste-skill/triage-inspect/desktop-fold.jpg` in the researcher's main checkout) is the one no-scroll screen: a top line with the position, the record in its own pane, the checklist in a right column, and a fixed decision bar. Only the triage screen is built; the other eight mockups wait for tester feedback. Base: `origin/main` at `8726fb9`.

The rule carried into the spec: **the checklist is a tool for the reason, not a gate for the decision.**

## Definition of done
- [x] **Decisions recorded** in `docs/decisions.md` (2026-11-09): checklist collapsed by default, Include needs no answers; methods paragraph unchanged; no page scroll at 1440×900 and 1280×720.
- [x] **Spec 03 FINAL with the M8-triage amendment** (`docs/ux/phase2-screening/final/03-triage-desktop.md`), through the `ux-spec-writer` agent (run 2026-11-09, commit `fa89368`); spec 12 touched only if a disclosure pattern changes; spec 05 aligned where it says the checklist is required.
- [x] **`decisiveFor`**: Include enabled unless an answer given fails a criterion; Exclude always available, its reason pre-selected from the first failed criterion when there is one, otherwise chosen from the chips; absent answers stay absent. Vitest `triage.decisive` (rewritten) and `triage.not-reported-policy` (kept).
- [x] **Collapsed checklist**: closed by default; opens on its toggle, on E, and on 1/2/3; Include with no answers sends an empty `criteria` list. Vitest `triage.collapsed-checklist`.
- [x] **Exclude without answers**: E opens the reason chips with none chosen; a chip number then Enter excludes; chips that contradict an answer are disabled. Vitest `triage.reason-from-checklist` (extended).
- [x] **Status line** says what the answers allow, and never asks for answers before a decision. Vitest.
- [x] **No page scroll**: Playwright asserts `document.documentElement.scrollHeight <= innerHeight` on `/screening/triage` at 1440×900 and 1280×720 with a long abstract; the abstract scrolls in its own pane.
- [x] **Budget kept**: `tests-browser/triage-desktop.spec.ts`, ten records by keyboard in at most 25 keypresses, focus on the next title.
- [x] **axe** on triage with no violation, light and dark.
- [x] **Focus screen on desktop** (researcher, 2026-11-09, after trying the app): from 1024 px the site header, step bar, footer and queue chips give way to one triage bar (wordmark, h1 "Triage", position and progress strip, Queue J K, Help ?, Leave triage), a counts rail, and a "Show" select. A failed load keeps Leave triage; Queue stays reachable when every record is decided. Vitest `triage.focus-bar`, `triage.boot-error`, `triage.all-decided`; Playwright: the site header is hidden at 1440 px and shown at 800 px.
- [ ] **Gates** (all done except the push: pr gate green on the focus-screen fix commit, with one comment-only rerun; baseline current; the focus-screen review CHANGES fixed): `/gate inner` after edits; `/gate pr` once on the final commit; `uv run python scripts/generate_contract_baseline.py --check` passes; `milestone-reviewer` APPROVE; the researcher is asked before push and PR.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |

## Decisions
- [Triage: the checklist is a tool for the reason, not a gate for the decision](../../decisions.md) (2026-11-09)
- [The methods paragraph does not count decisions made without per-criterion answers](../../decisions.md) (2026-11-09)
- [The triage screen fits 1440×900 and 1280×720 without page scroll](../../decisions.md) (2026-11-09)
- [Triage is a focus screen on desktop: its own top bar, a counts rail, no filter chips](../../decisions.md) (2026-11-09)

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner | `42d98f8` (working tree before commit) | `git diff --check`; `npm run typecheck`; `npm run test:related` (7 changed files) | pass; 13 files, 198 tests | about 1 min |
| pr | `42d98f8` | `git diff --check main`; `npm run typecheck`; `npm test`; `npm run build`; `npm run test:browser` (chromium light and dark) | pass: vitest 20 files, 290 tests; build compiled; Playwright 179 passed, 13 skipped (light-only screenshot tests in the dark project) | 290 s in all, Playwright 3.6 min |
| contract | `42d98f8` | `uv run python scripts/generate_contract_baseline.py --check` | "Contract baseline current" | seconds |
| review | `42d98f8` | `milestone-reviewer` | CHANGES: 2 P2, 4 P3, all documentation. Fixed in the next commit: API contract §3.1 `criteria` line, spec 03 and 05 stale sentences, the session key wording, this table. The pr gate is reused for that documentation-only commit (policy, evidence reuse) | — |
| review | `2319ce3` (focus screen) | `milestone-reviewer` on `29b19ee..2319ce3` | CHANGES: 3 P2, 2 P3. Fixed in `566425e`: Leave triage on a failed load; Queue always shown so Decided stays reachable; this file; a Playwright check of the hidden header; the Skipped wording in spec 03 | — |
| pr | `566425e` | `git diff --check main`; `npm run typecheck`; `npm test`; `npm run build`; `npm run test:browser` | vitest 20 files, 294 passed; typecheck and build pass; Playwright 181 passed, 13 skipped, 2 failed: the hygiene check found a `filter` utility compiled from a code comment ("five filter buttons") | 244 s |
| pr (rerun) | next commit (the comment reworded, no code change) | `npx playwright test tests-browser/hygiene.spec.ts tests-browser/triage-desktop.spec.ts` (light and dark) | 28 passed | 46 s |
| contract | `566425e` | `uv run python scripts/generate_contract_baseline.py --check` | "Contract baseline current" | seconds |

## Deferred
- The other eight redesign mockups (home, import, prepare, proposals, agreement, publish, export, workspaces): they wait for tester feedback (researcher, 2026-11-09).
- Review follow-ups (P3, not blocking; code left as reviewed so the pr gate stays valid):
  - no-scroll is not checked in the decided state (reveal table) or with a refusal or stale banner at 1280×720;
  - E opens the reason panel at the top of the right column, which may be scrolled out of view (`scrollIntoView`);
  - a chosen chip that a later answer contradicts stays pressed, and Confirm and Enter do nothing without saying why;
  - after Esc, E keeps a reason chosen earlier rather than pre-selecting a failure that appeared since;
  - while the reason panel is open, 1/2/3 pick chips rather than answer the checklist (M6-beta behaviour, more visible now that E opens the checklist);
  - axe runs with the checklist and reason panel open, not on the collapsed state.
- Live-run notes on a copy of the golden run (main session, 2026-11-09; P3, not blocking):
  - unfocused criteria still show their full text when the checklist opens;
  - the answer buttons carry no 1/2/3 key hints;
  - queue rows read "proposal hidden" while blinding is "show";
  - the venue reads "Not stored" without naming what is missing.
- Focus-screen follow-ups: the wordmark and Leave triage both go to screening Home, so the workspaces list is two steps away; the language and theme menus are not on desktop triage; the build prints a non-fatal "Can't resolve './theme.css'" message.
