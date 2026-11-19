# H-hydration-418: React #418 on every full page load of the exported UI
Branch: dev/fix/hydration-418 · Lane: **STANDARD** · Status: MERGED (PR #252, merge commit `c54e99f2`, 2026-11-19; reviewer: code approved) · Started: 2026-11-19

**Lane.** STANDARD, from `docs/architecture/test_gate_policy.md` ("a bounded behavior, packaging, or dependency change owned by one repository"): one UI module split in two (`apps/research-ui`), a new unit guard, a new browser spec and a hydration guard in the browser suite's shared `page` fixture. No engine, contract, API, route, persisted-file or MCP change. Gates: `inner` while editing, the `pr` set once on the final executable commit.

## What was observed
The main session, 2026-11-19, ran the wheel built from `origin/main` at `2c4383e9` (`nexus-scholar ui`, opened through its `/launch` link on `localhost`) in the Claude desktop app's built-in browser (Chromium; dark scheme, `en-US`, `Africa/Lagos`, 1024 px). On every full page load (`/en/workspaces/`, the inception Scope, Explore and Shape steps, `/en/discovery/plan/`) the console showed twice: `Uncaught Error: Minified React error #418; visit https://react.dev/errors/418?args[]=HTML&args[]=`. The pages worked afterwards. Later the same day the main session reported it in the researcher's own Chrome too (same wheel, `127.0.0.1:8791`, light scheme, a UTC+1 zone): one #418 on a full load of `/en/inception/explore/?draft=…` after `/en/discovery/plan/`. So it is tied to neither the desktop app's pane nor the dark scheme, as a timing race would not be. The earlier build (`7cd5fdca`) showed it once, on Explore; H-ui-findings finding 8 could not reproduce it in Playwright.

`args[]=HTML` is React's word for an element mismatch (as opposed to `text`); it does not name the `<html>` element.

## Cause
`components/locale-document.tsx` is a server component. It imported `THEME_BOOT_SCRIPT` (a string) from `components/theme-toggle.tsx`, which is a `"use client"` module. Next does not inline a value imported across that boundary: it writes a **client reference**. The page's payload carried

```
["$","head",null,{"children":["$","script",null,{"dangerouslySetInnerHTML":{"__html":"$f"}}]}]
f:I[93539,[4 chunks],"THEME_BOOT_SCRIPT"]
```

The prerender resolved `$f` on the server, so the HTML was right. In the browser, `$f` resolves only once those four chunks have loaded (the same chunks `AppShell` needs). When hydration began before they had, `<head>`'s only child suspended and React rendered `<head>` a second time. React 19.3 saves the hydration cursor on entering `<head>` (its one hydration scope) and restores it on leaving; the second entry saved the cursor `<head>` had set, `head.firstChild`, so on leaving `<head>` the cursor stayed on `<meta charset="utf-8">`. The shell's first element in `<body>` (`div.flex min-h-screen flex-col`) then had nothing to match: #418 `HTML`, once on the concurrent pass and once on React's synchronous retry (hence "twice"), after which React rendered the whole document again on the client.

It is a race between the chunks and the start of hydration, so it depends on cache state, machine load and the browser: a warm cache or a fast load hides it. That is why Playwright on direct loads and a reload in the in-app browser did not show it. The chunks behind `AppShell` grew between `7cd5fdca` and `2c4383e9` (the next-step bar, the plural table, the review bus), which fits "once on Explore" before and "every page" after.

How it was found (all against the real export, `npm run build:export`, served by `nexus-scholar ui`):
1. Built-in browser, fresh origin: one #418 on the first Scope load after "Start a new review"; later loads were clean. Playwright direct loads (default; dark, `Africa/Lagos`, 1024 px; with CPU ×6 and with 150 ms latency): none. The dev server (in Playwright and in the built-in browser): none.
2. A scratch copy of the export with React's mismatch function patched to log the fiber path and the DOM node it was matching, served on a fresh origin in the built-in browser: two errors on one load, path `div.flex min-h-screen flex-col < AppShell < body < html`, next DOM node `<meta charset="utf-8">`, in `<head>`.
3. React 19.3's source (`react-dom-client`): the root starts the cursor at `document.body.firstChild`; `html` and `body` keep it; only `head` saves and restores it. A cursor on `head.firstChild` while hydrating a child of `<body>` means `<head>` was entered twice.
4. The decoded payload showed `__html: "$f"` and the client-reference row above.
5. Confirmed in Playwright by delaying requests for those four chunks: #418 on 6 of 10 loads across en, fr, ar (before the fix); 0 of 10 after.

Not the cause, checked: the clock and time zone (no instant reaches the prerendered markup; `lib/local-time.ts` callers format data read after mount); the theme attribute (`suppressHydrationWarning` on `<html>` covers the boot script's `data-theme`, and attributes do not raise #418); `localStorage`, `matchMedia` and `window` reads during render (none on these pages); the next-step bar's first render (equal on both sides); Headless UI's handoff flag (hydration-safe); the launch redirect; the response encoding (`text/html; charset=utf-8`, `<meta charSet>` first in `<head>`).

## Fix
`THEME_STORAGE_KEY` and `THEME_BOOT_SCRIPT` move to `lib/theme-boot.ts`, a module with no directive. `LocaleDocument` and `ThemeToggle` import them from there, and the server now writes the script text into the payload (`"__html":"(function(){try{var t=localStorage…"`), so `<head>` never waits for a module. This is the cause, not a silenced symptom: no `suppressHydrationWarning` was added (the existing one on `<html>` is for the boot script's deliberate `data-theme` attribute and is unchanged).

## Tests (fail before, pass after)
| Test | Before (fix reverted) | After |
| :-- | :-- | :-- |
| `tests/server-client-boundary.test.ts`: a server module takes only components from a `"use client"` module (whole `app/`, `components/`, `lib/`, `i18n/`); the document's boot script comes from a module without the directive | 2 failed: `components/locale-document.tsx imports THEME_BOOT_SCRIPT from client module components/theme-toggle.tsx` (the only violation in the app) | 3 passed |
| `tests-browser/hydration.spec.ts`, per locale en, fr, ar: (a) the payload's `<head>` carries no `"$…"` reference on six pages (Workspaces, Scope, Explore, Shape, Discovery plan, Screening home); (b) the same six pages loaded with the shell's chunks held back 800 ms report no hydration error | 6 of 6 failed (chromium): (a) `"$f"` in every locale; (b) #418 on several pages per locale, e.g. ar: Workspaces, Scope, Shape | 12 of 12 passed (chromium and chromium-dark) |
| `tests-browser/helpers.ts`: the shared `page` fixture now fails any test in the browser suite on a hydration error (`#418`, `#423`, `#425` or the development wording) | caught the same #418s in (b) | see the full suite under Evidence |

Updated for the move: `tests/theme.test.tsx` (imports), `tests/i18n-direction-source.test.ts` (the storage exemption names both theme files).

## Evidence
- Real export rebuilt with the fix: the payload's `<head>` holds the script text; no `THEME_BOOT_SCRIPT` row remains.
- Playwright on the fixed export, console-served, shell chunks held 800 ms, 10 loads (en, fr, ar): 0 errors (6 of 10 before).
- Built-in browser, fresh origin, fixed export, the reproduction sequence plus the Start → Scope click flow and loads in fr and ar (9 loads): no #418. Weak evidence on its own, since that browser reproduced it only sometimes before the fix.

Gate selection: `uv run python scripts/select_test_gate.py --changed origin/main --stage pr` → area `research-ui`: `git diff --check`, typecheck, vitest, build, `test:browser`. The executable code is `abc3a209`; the follow-up commit changes only a test pattern, a test comment and docs (the edited spec was rerun).

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| before fix | `abc3a209` with `locale-document.tsx` and `theme-toggle.tsx` reverted to `origin/main` | `npx playwright test tests-browser/hydration.spec.ts --project=chromium` | 6 failed of 6 (payload `"$f"`; #418 on several pages per locale) | about 2.5 min |
| before fix | same | `npx vitest run tests/server-client-boundary.test.ts` | 2 failed of 3 (the one violation named) | 3 s |
| inner | `abc3a209` | vitest on boundary, theme, i18n-direction-source, shell; `npm run typecheck` | 31 passed; clean | under 1 min |
| pr | `abc3a209` | `npm --prefix apps/research-ui run test:browser` (both projects, new hydration guard in every test) | **572 passed, 12 skipped, 0 failed** (the 12 are the light-only committed-screenshot tests, skipped in `chromium-dark` by design); rewritten screenshots restored, not committed | 15.9 min |
| pr | `abc3a209` | `npm --prefix apps/research-ui test` | 57 files, 806 passed | 2.5 min |
| pr | final tree | `npx playwright test tests-browser/hydration.spec.ts` (after narrowing its reference pattern) | 12 passed (chromium, chromium-dark) | 2.7 min |
| pr | final tree | `npm run typecheck`; `npm test`; `npm run build`; `git diff --check` | clean; 806 passed on the third run (see note); build OK; clean | 50 s; 2 min; 36 s |
| contract | final tree | `uv run python scripts/generate_contract_baseline.py --check` | baseline current | seconds |

Note on vitest: on the final tree two full runs failed one test, `tests/discovery-proposals.test.tsx` "names the assistant and its model…" (`findByRole` heading, default 1 s wait), and a third full run passed all 806. The file alone passed 3 of 3. Neither it nor the component it renders imports anything this change touches; it is a timing flake under the parallel full run, recorded here as a follow-up.

Review: `milestone-reviewer` on `abc3a209`: **CHANGES**, one item and evidence only ("The code at abc3a209 is approved as written"): record the PR gate and the full browser run, and update the status. Done in this record. Its P3 notes taken: the `<head>` payload check now counts only references that can make React wait (`"$<id>"`, `"$L…"`, `"$@…"`), not literal encodings such as `"$undefined"`; the storage-guard comment says `lib/` is outside its scope; the decisions wording matches this record. Its other P3 notes are under Follow-ups.

## Not verified
- The main session's exact setup (its wheel, its browser profile) was not rerun; the cause was reproduced with a build of the same commit on this machine.
- Linux and macOS builds: same code, so presumably the same race, but chunk names and timing differ; not run here.
- Other browsers (Firefox, Safari): not run.

## Follow-ups (not fixed here)
- The boundary check does not parse `export … from` re-exports or follow a module without a directive that re-exports from a client module, and treats any PascalCase name as a component. None of these exists in the code today (reviewer, P3).
- React gap: a replayed `<head>` does not get the hydration-cursor repair host components get (`replayBeginWork`), so any future wait inside `<head>` would bring #418 back. The payload check in `hydration.spec.ts` guards this app; reporting it upstream is optional.
- `tests/discovery-proposals.test.tsx` "names the assistant and its model…" can time out under the parallel full vitest run (see the vitest note).
- `components/triage-page.tsx:179` seeds `queueOpen` from `sessionStorage` in a `useState` initializer: a latent mismatch on Triage when the stored flag is `1`, if the first render shows it. Not observed; the new fixture guard would report it if a browser test reloads Triage with the flag set.

## Decisions
Proposed in `docs/decisions.md`, "2026-11-19 — H-hydration-418", for the researcher.
