# M8-triage Triage on one screen, the checklist optional
Branch: dev/m8/triage-no-scroll · Lane: **STANDARD** (UI and spec only: no contract, engine, identity or publication change; the methods paragraph is unchanged by the researcher's choice) · Status: IN PROGRESS · Started: 2026-11-09

Why: the researcher's own run on real IEEE records (2026-11-09). The triage screen scrolls, and the long checklist has to be answered for every record before Include is possible. A redesign session's triage mockup (uncommitted, `.taste-skill/triage-inspect/desktop-fold.jpg` in the researcher's main checkout) is the one no-scroll screen: a top line with the position, the record in its own pane, the checklist in a right column, and a fixed decision bar. Only the triage screen is built; the other eight mockups wait for tester feedback. Base: `origin/main` at `8726fb9`.

The rule carried into the spec: **the checklist is a tool for the reason, not a gate for the decision.**

## Definition of done
- [ ] **Decisions recorded** in `docs/decisions.md` (2026-11-09): checklist collapsed by default, Include needs no answers; methods paragraph unchanged; no page scroll at 1440×900 and 1280×720.
- [ ] **Spec 03 FINAL with the M8-triage amendment** (`docs/ux/phase2-screening/final/03-triage-desktop.md`), through the `ux-spec-writer` agent; spec 12 touched only if a disclosure pattern changes; spec 05 aligned where it says the checklist is required.
- [ ] **`decisiveFor`**: Include enabled unless an answer given fails a criterion; Exclude always available, its reason pre-selected from the first failed criterion when there is one, otherwise chosen from the chips; absent answers stay absent. Vitest `triage.decisive` (rewritten) and `triage.not-reported-policy` (kept).
- [ ] **Collapsed checklist**: closed by default; opens on its toggle, on E, and on 1/2/3; Include with no answers sends no `criteria`. Vitest `triage.collapsed-checklist`.
- [ ] **Exclude without answers**: E opens the reason chips with none chosen; a chip number then Enter excludes; chips that contradict an answer are disabled. Vitest `triage.reason-from-checklist` (extended).
- [ ] **Status line** says what the answers allow, and never asks for answers before a decision. Vitest.
- [ ] **No page scroll**: Playwright asserts `document.documentElement.scrollHeight <= innerHeight` on `/screening/triage` at 1440×900 and 1280×720 with a long abstract; the abstract scrolls in its own pane.
- [ ] **Budget kept**: `tests-browser/triage-desktop.spec.ts`, ten records by keyboard in at most 25 keypresses, focus on the next title.
- [ ] **axe** on triage with no violation, light and dark.
- [ ] **Gates**: `/gate inner` after edits; `/gate pr` once on the final commit; `uv run python scripts/generate_contract_baseline.py --check` passes; `milestone-reviewer` APPROVE; the researcher is asked before push and PR.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |

## Decisions
- [Triage: the checklist is a tool for the reason, not a gate for the decision](../../decisions.md) (2026-11-09)
- [The methods paragraph does not count decisions made without per-criterion answers](../../decisions.md) (2026-11-09)
- [The triage screen fits 1440×900 and 1280×720 without page scroll](../../decisions.md) (2026-11-09)

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |

## Deferred
- The other eight redesign mockups (home, import, prepare, proposals, agreement, publish, export, workspaces): they wait for tester feedback (researcher, 2026-11-09).
- The mockup's counts rail and progress strip: the position line already says where the researcher is.
