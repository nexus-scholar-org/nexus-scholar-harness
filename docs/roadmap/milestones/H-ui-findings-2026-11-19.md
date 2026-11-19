# H-ui-findings-2026-11-19: nine problems from a browser walk-through of the wheel
Branch: dev/fix/ui-findings-2026-11-19 · Lane: **STANDARD** · Status: READY FOR REVIEW (not pushed) · Started: 2026-11-19

Source: the main session ran the wheel built from `origin/main` at `7cd5fdca` in a browser on a scratch workspaces folder (no contact email, no keys, so no database request) and walked a test review from Inception into the Discovery plan. It reported nine problems; this record covers eight of them. Number 1 (after "Create the workspace", "Open the workspace" lands on Screening home) belongs to M10b Part C's next-step bar and is **not** touched here.

**Lane.** STANDARD, from `docs/architecture/test_gate_policy.md` ("a bounded behavior, packaging, or dependency change owned by one repository"): UI behaviour and copy in one app, plus one build-script step (`build:export`). No contract, API, route, persisted-file or MCP change; `src/scholar_agent` and `docs/roadmap/production-plan.md` are untouched. Gates: `inner` while editing, the `pr` set once on the final executable commit.

## Definition of done
- [x] Each finding is fixed with a test that fails before and passes after, shown not real, or deferred with a reason (table below).
- [x] One finding per commit (F4 and F5 each touch a spec line; F3 changes one spec line).
- [x] The fixed screens were checked in the browser against the real export served by the console (evidence below).
- [x] `/gate pr` once on the final executable commit, contract baseline check, `milestone-reviewer` verdict (recorded under Evidence).
- [x] Proposed decisions are in `docs/decisions.md`, for the researcher.
- [ ] Push and PR: waits for the researcher's own word.

## Findings
| # | Finding | Result | Commit | Reproducing test (fails before, passes after) |
| :-- | :-- | :-- | :-- | :-- |
| 1 | After "Create the workspace", "Open the workspace" lands on Screening home | **Not mine** (M10b Part C, next-step bar) | none | none |
| 2 | Shape: the matching playbook is marked, not selected, and Continue proceeds without one | **Real, fixed.** Spec `04-shape` says the playbook is marked but never selected and Continue needs a playbook the researcher chose; the build gated only on the lens. Continue now waits for a playbook and says "Choose a playbook first."; the lede no longer says the lens "drafts the playbook". The marked playbook is not auto-selected, so a playbook the researcher chose is never overridden | `780033a6` | `tests/inception-shape.test.tsx` "keeps Continue disabled until the researcher has chosen a playbook" |
| 3 | The check said "Accept or Drop"; the buttons say Accept and Reject | **Real, fixed.** The built buttons (and the spec's "As built" note in `05-criteria`) say Accept and Reject; the check sentence now uses the button words in en, fr, ar | `b6018c65` | `tests/inception-copy.test.ts` "names the two decisions with the words on the buttons" |
| 4 | "1 suggestions", "1 checks are waiting", "1 criteria" | **Real, fixed** for these three and five more sentences of the same pattern (count-first wording on the same panels). A small table by copy key holds the forms that differ; the form is picked by `Intl.PluralRules` (Arabic: one, two, few, many, other). Other count messages in the app are listed under Deferred | `2567f7b9` | `tests/plural.test.tsx` |
| 5 | After Accept or Apply the checks keep the old problems under "Save this page to update them" | **Partly real.** *Apply on a stored suggestion* already saves on the server and re-reads the checks (test added; it passes before and after, so that half is not a defect). *Accept on a criterion* is a local decision until the page is saved, which is the designed behaviour of `02-checks`; but the old rows under that line read like a failed action. The line now says there are unsaved changes and each old row is marked "Before your changes". No server route added | `8eccfacb` | `tests/checks-panel.test.tsx` "Accept on a criterion is not saved yet..." |
| 6 | "Draft saved 2026-11-19 06:17" is UTC with no label | **Real, fixed.** Engine instants print in the browser's zone (new `lib/local-time.ts`); the draft header, the drafts list and the workspaces table keep the ISO instant in `dateTime` and `title`; the as-of lines, the dismissal dates and the corpus freeze date use the same conversion. Hydration: every caller formats a value read after mount, so the prerendered markup is empty there. Vitest pins `TZ=UTC` | `a1a4a164` | `tests/local-time.test.tsx` |
| 7 | The refusal title appears twice | **Real, fixed.** Both copies were visible (a badge and the heading, same text): not a screen-reader-only heading. The badge is removed; the role shows as the card's edge colour and `data-role`; the heading names the state. Covers the Explore card, the Discovery estimate card and "Refused Refused" (the unknown-code card) | `d40b754c` | `tests/state-card.test.tsx` |
| 8 | One React hydration error (#418) on first load of the Explore step in the export | **Not reproduced at `7cd5fdca`+ (this branch).** Checked: Chromium (Playwright) on the real export served by the console, 4 profiles (default; dark, `fr-FR`, Europe/Paris, 1440 px; Arabic locale; 390 px) times 6 inception steps, plus 5 address variants of the Explore step (with `console=`, with a hash, in French, with no `draft`, with an unknown `draft`), console errors and page errors captured from load: none. The in-app browser, after a reload: none. A jsdom test server-rendered and hydrated the Scope, Explore, Direction, Shape, Criteria and Review screens (no location query at render, the query present at hydrate): 0 mismatches (scratch test, not kept). No code change. To diagnose it the main session's run needs the exact console line (the minified error carries a `HTML`/`TEXT` argument), the browser and any extension, and the draft's state | none | none |
| 9 | Three prefetch files 404 on every page | **Real, cause found, fixed in the build.** The console's static serving is fine (the nested path answers 200; the flat one 404 because the file is not there). Next's exporter builds each prefetch file name from the segment's file path by swapping `/` for `.`; on **Windows** the path has `\`, so it writes nested folders (`__next.$d$locale\workspaces\__PAGE__.txt`) where the client asks for `__next.$d$locale.workspaces.__PAGE__.txt`. Linux and macOS builds (CI, the released wheels) are flat. `build:export` now flattens them (a no-op elsewhere). Prefetch is left on | `71199571` (+ `e6ea19b2`, two comment words) | `tests/export-segment-files.test.ts` |

## Decisions
Proposed in `docs/decisions.md`, "2026-11-19 — H-ui-findings" (items 1 to 8), for the researcher.

## Evidence
Browser: the real export built on this machine (`npm run build:export`, which printed "Flattened 85 prefetch file(s)"), served by `nexus-scholar ui` on a scratch workspaces folder at 127.0.0.1:8791, driven in the built-in browser (a UTC+1 clock) and in Playwright Chromium. Observed:
- F2: after choosing a lens, 5 playbooks, 0 checked, Continue disabled, "Choose a playbook first." beside it.
- F6: header `Draft saved <time datetime="2026-11-19T06:44:27.817009+00:00" title="2026-11-19T06:44:27.817009+00:00">2026-11-19 07:44</time>` (the clock is UTC+1).
- F7: the Explore refusal card has one `h2` with its title (count 1), `data-role="blocked"`, a 4 px coloured edge.
- F4: the step bar read "· 1 suggestion" and "· 1 to check".
- F9: Playwright on the Explore, Workspaces and Discovery plan pages: no 404 on any `__next.$d$locale…` file (before the fix: three per page); `curl` of the flat name answers 200.

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner | each commit | `npm --prefix apps/research-ui run typecheck`; targeted `vitest run` of the changed screens | pass at each commit | seconds |
| pr | `71199571` (executable code; later commits are docs and two comment words) | `git diff --check origin/main` | clean | |
| pr | `71199571` | `npm --prefix apps/research-ui run typecheck` | pass | |
| pr | `71199571` | `npm --prefix apps/research-ui test` | 53 files, 735 tests passed | 140 s |
| pr | `71199571` | `npm --prefix apps/research-ui run build` (after clearing a stale `.next`; the first try failed resolving `./theme.css` from a leftover Turbopack cache, not from the code) | pass | |
| pr | `71199571` | `npm --prefix apps/research-ui run test:browser` | 531 passed, 13 skipped, 2 failed: the hygiene test found the word "static" in two new comments (comment words compile as utilities) | 13.4 min |
| pr (repair) | `e6ea19b2` | `npx playwright test tests-browser/hygiene.spec.ts` (both colour profiles) | 8 passed | 40 s |
| pr | `e6ea19b2` | `uv run python scripts/generate_contract_baseline.py --check` | "Contract baseline current" | |
| pr | `e6ea19b2` | `npm run build:export` then the real export served by `nexus-scholar ui` and driven in a browser (see above) | pass; "Flattened 85 prefetch file(s)"; no 404 | |
| review | `e6ea19b2` | `milestone-reviewer` | (verdict below) | |

## Deferred
- **A protocol with one one-word concept** produces a one-word query for every database and no check warns about it. Not built, as asked. Suggestion for the checks catalogue (`02-checks`): a warning `CONCEPTS_ONE_ONLY` already exists for one concept; extend its sentence or add a sibling check for "the whole query is one word", with the same non-blocking level.
- **Other count messages** that still read "1 …s": the many `{n}` strings outside the eight keys in `lib/plural.ts` (for example `checks.notes`, `checks.dismissed` and the screening and discovery screens' counts). The mechanism is general (`pluralTemplate`); each key needs its forms. A follow-up could sweep every `{n}`.
- **A "Save and update the checks" button** in the checks panel (F5): it would save the page from the panel, which owns no save. Not built; the rows now say why they are old.
- **F8** stays open until it can be reproduced (see the table).
- **Arabic digits.** The check sentences print Arabic-Indic digits in Arabic (the slot formatter), while `04-shape` says numerals Latin for RTL; not touched.
