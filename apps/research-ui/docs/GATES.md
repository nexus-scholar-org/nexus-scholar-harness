# Research UI verification gates

This file records what packet UI-00 made executable, what packet UI-01 added on
top of it, what packet UI-00b measured in a real browser, the mobile-dialog-open
axe run added afterwards (§3.6), and — just as importantly — what remains
**unverified** or **failing**. Nothing below is claimed as covered unless a
command in this directory produced the evidence.

Commands referenced here all run in `apps/research-ui/`:

```text
npm run typecheck
npm run test
npm run test:browser
npm run build
```

`npm run test:browser` is packet UI-00b's suite. It starts and stops its own
server and needs a Chromium build (`npx playwright install chromium`).

## 1. Gates that are now executable

`npm run test` runs Vitest in-process against jsdom (`vitest.config.ts`), with
`@/*` resolved to the application root. It requires no server and no browser.

| # | Gate | Covered by | Status |
|---|------|-----------|--------|
| 1 | `StatusBadge` renders the full 4-state matrix (`complete`, `active`, `waiting`, `refused`), each by text | `tests/status-badge.test.tsx` | EXECUTABLE |
| 2 | `WorkflowTimeline` renders every stage label from a fixture, in order | `tests/workflow-timeline.test.tsx` | EXECUTABLE |
| 3 | `WorkflowTimeline` renders the count when defined and no number when `count` is `undefined` | `tests/workflow-timeline.test.tsx` | EXECUTABLE |
| 4 | `EvidenceChain` renders all nodes in the order supplied | `tests/evidence-chain.test.tsx` | EXECUTABLE |
| 5 | The `/` route shows the literal `Demonstration data` label (anti-fabrication guard) | `tests/home-page.test.tsx` | EXECUTABLE |
| 6 | The `/` route renders its project summary, timeline, and evidence chain | `tests/home-page.test.tsx` | EXECUTABLE |
| 7 | axe-core reports **zero `critical`** and **zero `serious`** violations on the rendered `/` page | `tests/accessibility-in-process.test.tsx` | EXECUTABLE, but see §2 and **§3.2** — this gate cannot fail on contrast, and when the rendered run first landed the same page **did** fail `color-contrast`; it passes now, on the evidence in §3.2, not on this gate |
| 8 | Tab moves `document.activeElement` to a different element each press; `Shift+Tab` walks back; focus is not trapped | `tests/keyboard-traversal.test.tsx` | EXECUTABLE (see §2, and §3.1 B1 for the rendered ring) |
| 9 | TypeScript compiles the app *and* the tests | `npm run typecheck` | EXECUTABLE |
| 10 | The application builds | `npm run build` | EXECUTABLE |
| 11 | The skip link is the **first** focusable element in the document, is focusable, and targets a `main` that exists and is programmatically focusable (`tabindex="-1"`) | `tests/shell.test.tsx`, `tests/keyboard-traversal.test.tsx` | EXECUTABLE (see 4.3) |
| 12 | The route's tab stops are exactly, and in DOM order, the **union across viewport widths**: skip link, `Overview` link, mobile-disclosure trigger. No single real viewport yields all three — at 375px the real order is [skip, trigger] (`primary-nav.tsx:88` is `hidden lg:block`), at >=1024px it is [skip, `Overview`] (`mobile-nav.tsx:30` is `lg:hidden`), because `display: none` removes an element from the focus order | `tests/keyboard-traversal.test.tsx` | EXECUTABLE, and **confirmed in a real browser** (§3.1 B1) — the union reasoning is now measured, not assumed |
| 13 | Tab and Shift+Tab walk the real route in both directions and leave the focusable set (no trap) | `tests/keyboard-traversal.test.tsx` | EXECUTABLE; the open-dialog trap is measured too (§3.1 B7) |
| 14 | The banner `<header>` is a top-level **sibling** of `<main>`, and there is exactly one `main` | `tests/shell.test.tsx` | EXECUTABLE (see 4.3) |
| 15 | The `Demonstration data` marker is rendered by the shell, sits in the banner, is outside the mobile disclosure, and has no hidden ancestor | `tests/shell.test.tsx`, `tests/home-page.test.tsx` | EXECUTABLE (see §2) |
| 16 | The primary navigation is a `<nav>` landmark with an accessible name; the active item carries `aria-current="page"`; no link points at a route that does not exist | `tests/shell.test.tsx` | EXECUTABLE |
| 17 | The mobile disclosure opens from the keyboard, closes via `Escape` and via its own close control, and returns focus to the trigger | `tests/shell.test.tsx` | EXECUTABLE (see §2) |
| 18 | axe-core reports **zero violations of any impact** on an assembled document, with `bypass`, `landmark-one-main`, `landmark-unique`, `page-has-heading-one` and `region` genuinely evaluated — and `region` / `landmark-unique` genuinely **pass** with the mobile disclosure open | `tests/shell.test.tsx` | EXECUTABLE (see §2) |
| 19 | **SUPERSEDED BY HUMAN-RATIFIED SUBSTITUTION — see §3.7.5, which carries the authority, the date, and the condition.** Originally: the emitted CSS carries `--color-surface: #f8fafc` and `--color-ink: #172033`, the two pre-UI-01 raw-hex values **quoted in §1.2**, and no colour token was removed. It passed on the evidence in §1.2. UI-01c deliberately changed the palette and **removed all three of those tokens**, so gate 19 as written **fails**; it was not silently deleted | `npm run build` + inspection of the emitted CSS | **FAILED as written**, then **substituted under ratified authority** — the substitution is conditional, and the condition is discharged by gate 21 |
| 20 | UI-01c: the emitted CSS carries all twelve UI-01c role tokens and both `--font-*` roles, and carries **no** UI-01 token (`--color-surface`, `--color-raised`, `--color-accent`) or UI-01 raw hex (`#f8fafc`, `#172033`, `#1d4ed8`) anywhere | `npm run build` + inspection of the emitted CSS | EXECUTABLE (see §3.7.5) |
| 21 | **Token discipline, general (UI-01c repair R1).** The property gate 19 used to carry, now enforced rather than traded away. (a) every `var(--token)` in `app/` and `components/` is **declared** in `app/globals.css` **and** reaches the browser; (b) **no raw palette utility** anywhere in `components/**/*.tsx` or `app/**/*.tsx` — **recursively**, since UI-01d moved the routes into `app/[locale]/` (M5) (this is A1, previously a convention with zero enforcement); (c) the **shipped stylesheet** contains no raw-palette utility, no raw-palette theme variable, and no retired UI-01 token or hex | `tests-browser/hygiene.spec.ts` | EXECUTABLE, with four live negative controls (§3.7.9) |

Gate 1 matters specifically because `lib/mock-project.ts` never uses `refused`;
the component is driven directly by prop to close that gap.

Gate 7 carries a **negative control** in the same file: a deliberately broken
`<img>` (no `alt`) is asserted to be reported by axe as a `critical`
`image-alt` violation. If that control ever reports zero critical violations,
the runner is broken and the green gate on `/` means nothing.

Gate 18 carries the same kind of control: it asserts not only "no blocking
violations" but that `bypass`, `landmark-one-main`, `landmark-unique`,
`page-has-heading-one` and `region` appear in the *evaluated* rule set at all.
A run that silently stopped reaching those rules would otherwise look identical
to a clean one.

### 1.1 What happened to the UI-00 focusable tripwire (measured, not as predicted)

UI-00 shipped a tripwire in `tests/keyboard-traversal.test.tsx` asserting that
the route rendered **zero** focusable elements, on the stated expectation that
"the moment a later packet adds navigation, this assertion fails". That
expectation **did not hold**, and the reason matters:

- The tripwire rendered `HomePage`, not the route. UI-01 moved the shell into
  `app/layout.tsx`, so `HomePage` on its own still renders no focusable
  elements and the tripwire stayed **green**.
- The tripwire's own comment claimed to watch "the route" while the code only
  ever watched a single component. That much is established by the file itself.
  The stronger reading — that UI-00's *reasoning* about the tripwire depended on
  the shell not existing yet, so it could not notice the day it stopped meaning
  what it said — is an **inference**, not something the tree shows.

UI-01 therefore converted it rather than deleting it. The converted assertion
renders the **assembled route** (`RootLayout` wrapping `HomePage`), keeps the
document-scoped query, and replaces "zero" with a positive, ordered statement:
exactly three tab stops, in order — skip link, `Overview` link, mobile-disclosure
trigger — plus a Tab/Shift+Tab walk of the real route in both directions. The
original observation ("the page component contributes no tab stops of its own")
is kept as its own test, and the portal control is kept verbatim.

### 1.2 Gate 19's comparison target, quoted into the tree

Gate 19 claims the `@theme` tokens compile to the colours the pre-UI-01 raw-hex
`:root` block produced. Those values exist nowhere in the tree: `apps/` is
untracked, so there is no VCS history to recover them from. Without a quoted
target the gate is not checkable by anyone, so the pre-UI-01 block is recorded
here:

```css
:root {
  --background: #f8fafc;
  --foreground: #172033;
}
```

It declared no `color-scheme`. Against those values the check is that the
emitted CSS contains `--color-surface: #f8fafc` and `--color-ink: #172033` (the
`#f8fafc` -> `--background` -> `--color-surface` rename, and likewise
`#172033` -> `--foreground` -> `--color-ink`), leaving `body`'s resolved
background and foreground unchanged. There are three additions with no pre-UI-01
counterpart, none of which is claimed to preserve anything:
`--color-raised: #ffffff` and `--color-accent: #1d4ed8`
(`app/globals.css:19-20`), and `color-scheme: light` (`app/globals.css:24`). The
last of these is the **only** addition that changes rendered behaviour: it sets
the document's preferred colour scheme, so it governs canvas/background
resolution, scrollbar rendering, and UA-rendered form controls and defaults. It
is present in the emitted CSS. A declared light scheme is defensible for a page
whose palette is fixed, but it is disclosed here because this section certifies
colour preservation, and an undisclosed rendering-affecting declaration is not
something this section may quietly carry.

The pre-UI-01 values recorded above were read by the implementer from
`app/globals.css` before its own edit, not recovered from history, because there
is none: `apps/` is untracked. Their only in-tree corroboration is the comment at
`app/globals.css:11-14` ("preserved verbatim"), which UI-01 itself authored, so
it corroborates rather than independently confirms; the reviewer of this repair
supplied no values, its F-5 finding saying only that the values "are not recorded
anywhere" and offering a choice between quoting them and restating gate 19.
Quoting them here (rather than restating
gate 19 as "the tokens match the hexes declared in `app/globals.css`", the other
option) is **chosen by the implementer, rationale: the second option would make
gate 19 a tautology — `app/globals.css` is the thing under test, so comparing it
to itself checks nothing, and the narrowed comparison the gate now makes —
the two pre-UI-01 values quoted above, plus the fact that no colour token was
removed — is the one worth keeping. The declarations UI-01 added are disclosed
above rather than folded into that comparison, because one of them,
`color-scheme: light`, does change rendered behaviour.**

**This section is now history, and its subject has been deliberately changed.**
§1.2 exists so that gate 19 had a comparison target, and it worked: gate 19
passed on the evidence recorded here. Packet UI-01c then **replaced**
`--color-surface` and `--color-ink` with `--color-paper` and `--color-ink` at new
values, and dropped `--color-raised` and `--color-accent` outright. Gate 19
therefore fails as written. It is left in the table in that state rather than
reworded into a pass, and §3.7.5 records the replacement gate. The reasoning
here — that a preservation claim is worth little without a target quoted into
the tree — is the reason the supersession is checkable at all.

## 2. Limits of the in-process checks (read before trusting gate 7 or 8)

Gate 7 is **jsdom + axe-core in a single Node process**. That means:

- It does **NOT** cover colour contrast. jsdom performs no layout and computes no
  real contrast ratios, so axe reports those rules as `incomplete`, never as
  passed. (`Not implemented: HTMLCanvasElement's getContext()` appears in the
  test output for exactly this reason.) A green gate 7 says nothing about
  text/background contrast — and §3.2 shows it, because when the rendered run
  first landed this very page **failed** `color-contrast`. It passes now, but
  only because a separate run in a real browser says so; gate 7 on its own
  still carries no contrast evidence either way.
- It does **NOT** cover focus order **as rendered**, nor visible focus rings.
  Gate 8 proves only that a simulated `Tab` moves `document.activeElement`
  between ordinary focusable elements and is not trapped. It says nothing about
  what a real browser's tab ring does, nor about focus indicators.
- It does **NOT** cover responsive rendering, layout, overflow, or anything that
  depends on a visual viewport.
- It evaluates a DOM subtree, not a full document, so **document-level rules are
  structurally out of scope of this run**. Measured, not assumed: comparing
  `axe.run(container)` against `axe.run(document.documentElement)` on the
  rendered `/` page, ten rules can do no useful work at container scope —
  - **Vacuous** (reported `inapplicable` under container scope, but genuinely
    evaluated at document scope, so they *can* fail there and *cannot* fail
    here): `aria-hidden-body`, `document-title`, `html-has-lang`,
    `html-lang-valid`, `landmark-one-main`, `page-has-heading-one`, `region`.
  - **Never evaluated at all** (axe drops the rule entirely when the context is
    not the document): `bypass`.
  - **`<head>`-scoped** (their target element can never be inside the RTL
    container; `inapplicable` under both scopes here because the jsdom document
    carries no viewport meta element): `meta-viewport`, `meta-viewport-large`.

  Four of these are not academic. `document-title` is supplied by
  `metadata.title` in `app/layout.tsx` (and `meta-viewport` by the Next default),
  so neither is covered by *this* gate. `region` requires all page content to
  sit inside landmarks — exactly the rule that UI-01's "primary navigation, skip
  link, and mobile navigation" has to satisfy — and `bypass` is the rule that
  requires a skip link or landmark to skip repeated blocks.

  **Status after UI-01.** Every limit above still applies to the
  container-scoped run in `tests/accessibility-in-process.test.tsx`, which was
  not modified. But the two load-bearing rules are no longer *unchecked*:
  `tests/shell.test.tsx` runs axe a second time at **document scope**, on a
  document assembled from the layout's own output, and asserts that
  `bypass`, `landmark-one-main`, `landmark-unique`, `page-has-heading-one` and
  `region` were all genuinely **evaluated**; that `bypass`, `region` and
  `landmark-one-main` were not **failed**; and that the run reports **zero
  violations of any impact** — not merely zero at `critical`/`serious`. That
  last one is enforced by `expect(results.violations.map(describeViolation))
  .toEqual([])` in the closed-state test itself, not asserted only in prose here.
  (`landmark-unique` and `page-has-heading-one` are asserted as *evaluated* in
  the closed state; the strict *pass* requirement is made of `region` and
  `landmark-unique` in the open-state run below.)

  The document-scope run is still jsdom, so the limits above apply to it too:
  it proves the *structure* is correct (one `main`, banner outside it, a
  resolvable skip-link target, all content in landmarks) and it proves nothing
  about how any of it looks once rendered.

  **The mobile disclosure open is also measured, not reasoned.** A second
  document-scope run opens the disclosure first, then asserts that
  `region` and `landmark-unique` are genuine **passes** (not merely
  `incomplete` "needs review" results) and that there are zero
  `critical`/`serious` violations. It also asserts its own premise — that
  Headless UI really did mark the rest of the page `aria-hidden` — so the run
  cannot quietly degrade into re-testing the closed state.

  `meta-viewport` and `meta-viewport-large` remain uncovered: they target
  `<head>`, which no in-process render supplies.

## 3. Browser verification (packet UI-00b)

`npm run test:browser` runs `playwright.config.ts` against a `next start`
server on port **3117**, with `reuseExistingServer: false` so it can never
attach to a process that was already listening, and with Playwright owning the
teardown — the server is gone after the run whether it passed or failed. The
suite is Chromium only (`npx playwright install chromium`), serial, one worker,
`deviceScaleFactor: 1`, at two viewports: **375x812** and **1440x900**.

**24 tests: 24 pass.** UI-00b's first run reported 20 pass and 2 fail, both on
`color-contrast`; the contrast repair in §3.2 closed both, and the run now exits
0. Every number below is copied from a run's own `[measured]` output; nothing
here is inferred. The count moved 23 → 24 in packet UI-01c, by exactly one new
test in `screenshots.spec.ts`; the arithmetic is in §3.7.2.

**The count is 25, and the arithmetic is auditable** — it is the sum of the
`playwright test --list` output. UI-00b added one test to `rendered-axe.spec.ts`;
UI-01c added one to `screenshots.spec.ts`; the UI-01c repair pass (R1) added one
to `hygiene.spec.ts`:

| Spec file | Tests | Why |
|---|---:|---|
| `tests-browser/focus-visibility.spec.ts` | 3 | unchanged; assertions added *inside* the 3 existing tests (§3.7.3) |
| `tests-browser/hygiene.spec.ts` | **4** | **+1 in the UI-01c repair pass (R1)**: the token-discipline guard, gate 21 (§3.7.9) |
| `tests-browser/overflow.spec.ts` | 3 | 2 from the viewport loop (`overflow.spec.ts:23`) + 1 standalone |
| `tests-browser/rendered-axe.spec.ts` | **4** | 2 from the viewport loop (`rendered-axe.spec.ts:218`) + the `image-alt` negative control + **the §3.6 dialog-open run**; assertions added *inside*, no new `test()` (§3.7.3) |
| `tests-browser/responsive-nav.spec.ts` | 3 | unchanged |
| `tests-browser/screenshots.spec.ts` | **6** | **+1 in UI-01c**: `1440-evidence-trail.png` (§3.7.2) |
| `tests-browser/tab-order.spec.ts` | 2 | unchanged |
| **Total (7 files)** | **25** | 23 → 24 in UI-01c, then 24 → **25** in the repair pass |

No existing test was restructured, deleted, or loosened to make room. **25 = 23
`test()` call sites + 2 loop expansions**, where the two expansions are the
viewport loops named in the table, each iterating two viewports.

**Why a naive `grep` for `test(` returns 25 and is nevertheless not the test
count** — every discrepancy named, so this needs no re-running to trust:

| Step | Value |
|---|---:|
| `grep -o 'test(' \| wc -l` across the 7 specs | **25** |
| less hits that are not a Playwright `test()` call | **−2** |
| = real `test()` call sites | **23** |
| plus one execution per loop iteration, two loops × 2 viewports | **+2** |
| **= tests Playwright actually runs** | **25** |

The two non-test hits, by file and line, both in `hygiene.spec.ts`:

- `:78` — `/\.(tsx|css)$/.test(entry.name)`, a real `RegExp.prototype.test` call
  in the R1 guard's file walk.
- `:133` — `needle.test(html)`, the pre-existing analytics-payload detector.

**A correction to the note this section used to carry.** It claimed a naive grep
"counts the 7 `test.describe` blocks plus a `needle.test(html)` false positive."
Both halves were wrong. `test.describe(` does **not** contain the substring
`test(` — there is no overlap, so those 7 blocks are never counted by that grep at
all — and the grep total was misstated. The line has been recomputed from the
files rather than argued from the old figure.

### 3.1 CLOSED by UI-00b

| # | Previously deferred item | Measured | Covered by |
|---|---|---|---|
| B1 | Real per-viewport tab order | 375px: `["a:Skip to main content","button:Open main navigation"]`. 1440px: `["a:Skip to main content","a:Overview"]` | `tests-browser/tab-order.spec.ts` |
| B2 | Tailwind's `lg:` breakpoint behaviour | 375px: `<nav aria-label="Primary">` hidden, trigger visible. 1440px: the exact reverse | `tests-browser/responsive-nav.spec.ts` |
| B3 | Rendered focus, skip link | `:focus-visible` true; `outline: 2px solid rgb(29, 78, 216)`, `outline-offset: 2px`, `position: fixed`; `clip-path` `inset(50%)` -> `none`; box 1x1 -> 169.69x40, inside the viewport. Same at both widths. **Superseded by UI-01c: the ring is now `rgb(28, 26, 23)` and the box is 166.23x42, because `.skip-link:focus` gained a 1px border and lost 1px of vertical padding (§3.7.4). Every other part of this row — `:focus-visible`, 2px solid, offset 2px, `position: fixed`, the clip reveal, within-viewport — is unchanged and re-measured** | `tests-browser/focus-visibility.spec.ts` |
| B4 | Rendered focus, primary-nav link and mobile trigger | Both `:focus-visible` true with the **application** ring `outline: 2px solid rgb(29, 78, 216)`, `outline-offset: 2px` — identical to the skip link's own ring. (At UI-00b's first run these two fell through to the user-agent `outline: 1px auto rgb(16, 16, 16)`, `outline-offset: 3px`; see §3.2 D1) **Superseded: the ring is now `rgb(28, 26, 23)` (§3.7.4)** | same |
| B5 | Screenshots of a route | **6** committed captures (UI-01c added `1440-evidence-trail.png`), PNG magic verified, `deviceScaleFactor: 1`, animations and caret off | `tests-browser/screenshots.spec.ts`, `screenshots/` |
| B6 | Horizontal overflow | 375px: `documentElement` 375/375, `body` 375/375, `<main>` 375/375. 1440px: 1440/1440 on all three. No sideways scroll at either width | `tests-browser/overflow.spec.ts` |
| B7 | Mobile disclosure focus trap (residual UI-01 item) | On open, focus moves to Headless UI's dialog root; 6 consecutive `Tab` presses cycle `button:Close main navigation` -> `a:Overview` -> back, never leaving the dialog subtree; `Escape` removes the panel and restores focus to `button:Open main navigation` | `tests-browser/responsive-nav.spec.ts` |
| B8 | axe non-vacuity, in a real browser | An `<img>` with no `alt`, injected into the live page, is reported as `critical` `image-alt`, 1 node | `tests-browser/rendered-axe.spec.ts` |
| B9 | No external origin, no analytics, no secrets | 0 non-localhost requests, 0 absolute non-localhost URLs in the served HTML, 0 analytics globals on `window`, 0 analytics payloads inlined, 0 credential-shaped literals in the Playwright config | `tests-browser/hygiene.spec.ts`, plus a non-localhost request guard on **every** test via the `page` fixture in `tests-browser/helpers.ts` |
| B10 | axe with the **mobile dialog open**, in a browser — the last unmeasured accessibility surface | 375px: `color-contrast=pass ; violations=none ; incomplete=aria-hidden-focus(2)`. Zero violations of any impact; `color-contrast` a decided pass, not an `incomplete`; the one `incomplete` rule is Headless UI's own focus guards, not a contrast node. See §3.6 | `tests-browser/rendered-axe.spec.ts` |

**B1 confirms §1 gate 12 rather than contradicting it.** The documented union
across viewport widths is what jsdom can see; the measured per-viewport rings
are its two strict subsets, exactly as `tests/keyboard-traversal.test.tsx`
predicts in its comment. No documentation needed correcting, and the assertions
were not bent.

**B3 vs B4, then and now.** At UI-00b's first run this was a split. The skip
link had an explicit application focus style (2px solid `--color-accent` =
`rgb(29, 78, 216)`). The primary-nav link and the mobile trigger had **no**
focus rule of their own; they inherited the browser default, which is visible
but is a `1px auto` ring and would change with the user's platform settings.
That was recorded rather than called a failure, so nobody would later read B4
as "the app styles focus on every control". It has since been repaired — one
shared rule in `app/globals.css`, §3.2 D1 — and all three elements now measure
identically.

**B7, measured rather than assumed.** Headless UI 2.2 roots the dialog at its
own `div#headlessui-dialog-*` carrying `role="dialog"` and `tabindex="-1"`, and
that element — an **ancestor** of `DialogPanel`, which itself carries no `role`
— is what receives focus on open. Focus containment is therefore asserted
against the dialog subtree (`[role="dialog"]`), not against
`#mobile-primary-nav`. In a real browser Headless UI marks the background
`inert` (1 node) and `aria-hidden` (6 nodes; **12 after UI-01c**, which added
elements to the page — the count is descriptive, not asserted);
`tests/shell.test.tsx` asserts
`aria-hidden` under jsdom. Same mechanism, different environment.

### 3.2 CLOSED — rendered colour contrast, and two repairs it exposed

**`npm run test:browser` now exits 0 with 23/23.** At UI-00b's first run two
tests were red on `color-contrast` because the application genuinely failed
WCAG 2.1 AA. That was not a runner problem and it was not suppressed,
allow-listed or downgraded: axe returned `incomplete: []` at both viewports
then, and returns `incomplete: []` now, so both verdicts are real verdicts
rather than "needs review".

**Before, at UI-00b's first run:**

| Viewport | Nodes | Where | Foreground / background | Measured | Required |
|---|---|---|---|---|---|
| 375px | 6 | `components/workflow-timeline.tsx:12`, the `text-slate-400` "Stage N" labels | `#90a1b9` on `#ffffff` | **2.63:1** | 4.5:1 |
| 1440px | 6 | the same six labels | `#90a1b9` on `#ffffff` | **2.63:1** | 4.5:1 |
| 1440px | 3 | `components/primary-nav.tsx:49`, `text-slate-400` unavailable nav entries, 14px | `#90a1b9` on `#ffffff` | **2.63:1** | 4.5:1 |
| 1440px | 3 | `components/primary-nav.tsx:52`, `text-slate-500` on `bg-slate-100` "Not yet available" tag, 11px | `#62748e` on `#f1f5f9` | **4.34:1** | 4.5:1 |

**After.** The two viewports' own `[measured]` lines, quoted from the passing
run:

```text
[measured] 375px axe: color-contrast=pass ; violations=none ; incomplete=none ;
[measured] 1440px axe: color-contrast=pass ; violations=none ; incomplete=none ;
```

Per-site ratios, read out of that same axe run's per-node data
(`fgColor` / `bgColor` / `contrastRatio` / `expectedContrastRatio`) rather than
recomputed or assumed:

| Site | Viewports | Foreground / background | Size | Before | **After** | Required |
|---|---|---|---|---|---|---|
| "Stage N" labels, `workflow-timeline.tsx:12` | 375px **and** 1440px, 6 nodes each | `#45556c` on `#ffffff` | 12px | 2.63:1 | **7.58:1** | 4.5:1 |
| Unavailable nav entries, `primary-nav.tsx:49` | 1440px, 3 nodes | `#45556c` on `#ffffff` | 14px | 2.63:1 | **7.58:1** | 4.5:1 |
| "Not yet available" tag, `primary-nav.tsx:52` | 1440px, 3 nodes | `#45556c` on `#f1f5f9` | 11px | 4.34:1 | **6.92:1** | 4.5:1 |

The three sites render only where their container does: the six "Stage N"
labels at both widths, the six nav nodes (3 entries + 3 tags) at 1440px only,
where the desktop `<nav>` is visible. The `4.34:1` near miss is now `6.92:1`,
and it is still held to normal-size: at 11px the threshold is 4.5:1, not 3:1.

**Nothing else was touched to get there.** The changes are two Tailwind
colour tokens — `text-slate-400` -> `text-slate-600` (`#90a1b9` ->
`#45556c`) on the two sites above, and `text-slate-500` -> `text-slate-600` on
the tag, whose `bg-slate-100` is unchanged. No rule was disabled, no
allow-list or excluded node was added, and `blockingViolations` is untouched:
`expect(outcome.violations).toEqual([])` and the `image-alt` negative control
are unchanged in substance and both still pass.

#### 3.2.1 The other two repairs this pass made

| # | Repair | Measured after |
|---|---|---|
| D1 | One shared focus ring in `app/globals.css` — `a:focus-visible, button:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }` — replacing the bare `button, a { outline-offset: 3px; }` it supersedes, rather than sitting beside it | skip link, primary-nav link and mobile trigger all report `2px solid rgb(29, 78, 216)`, `outline-offset: 2px` |
| D2 | `self-start` on the "Why this matters" `<aside>` in `app/page.tsx`, so the grid item hugs its content instead of stretching to the evidence chain's height | aside text unchanged and passing: `9.83:1` (`#8ec5ff` on `#0f172b`), `17.83:1`, `11.99:1` |

D1 uses `var(--color-accent)`, the same token and the same value the skip link
already used, so the skip link is not a special case: it is the first element
the shared rule reaches. Its own `:focus` treatment in `app/globals.css` is
untouched, and it still wins on specificity, so the skip link's behaviour is
unchanged — confirmed by the two skip-link tests still passing on
`outline=2px solid rgb(29, 78, 216) offset=2px` and the clip reveal still
`inset(50%)` -> `none`, box 1x1 -> 169.69x40.

(This paragraph is the record of the UI-00b run. UI-01c moved both rules onto
`--color-focus`, so the colour quoted above is superseded — see §3.7.4. The
*claim* it makes, that the shared rule reaches the skip link as its first
element, is unchanged and still measured.)

**D1 has a negative control, because the old assertion could not have caught
it.** `tests-browser/focus-visibility.spec.ts` asserted only
`outline-width > 0`, which the user-agent default satisfies — so the gap in B4
was invisible to it. It now pins width `2px`, style `solid`, colour
`rgb(29, 78, 216)` and offset `2px`, and cross-checks the nav link's ring
against the skip link's measured ring in the same run. Verified by deleting the
`app/globals.css` rule and re-running that spec: the nav link fell back to
`outline: 1px auto rgb(16, 16, 16)` and the test failed with
`primary nav link @1440 outline-width: expected 2px, got 1px`. The rule was
restored and the whole suite re-run green.

#### 3.2.2 A defect in the axe test itself, found by closing the contrast

`tests-browser/rendered-axe.spec.ts` compared the contrast rule id as
`colour-contrast`. axe-core emits `color-contrast` — the id was confirmed
against `node_modules/axe-core` before anything was changed — so the
non-vacuity guard could never match and could only ever fail. It stayed hidden
because `expect(outcome.violations).toEqual([])` fails first on any run where
contrast genuinely fails; it surfaced the moment contrast passed, as
`colour-contrast was not evaluated at all, so the empty violations array is
meaningless`. The guard is a real requirement, so it is repaired to compare
against axe's real id and is now live. This is a spelling fix to a comparison
string: no rule was disabled, no result filtered, no assertion relaxed.

The guard was then tightened a second time, on the same review. It originally
accepted `color-contrast` appearing in `outcome.passes` **or**
`outcome.incomplete`; this section's own header states that an `incomplete`
result is not a pass. A silent `passes` → `incomplete` regression — a gradient or
overlapping element that makes contrast undecidable — would therefore have left
the run green while the empty `violations` array became vacuous, which is the one
failure this guard exists to catch. It now requires `color-contrast` in
`outcome.passes` specifically. The assertion is
`expect(outcome.passes, …).toContain("color-contrast")`; no test was added by
that tightening, the suite was 22 immediately afterwards (it is 23 now — §3.6,
and the arithmetic is in §3), and a genuine failure continues to be caught by
the `violations` `toEqual([])` assertion above. The suite stayed green on the
first run after the tightening, so it was not over-tightened. Its failing path
has still not been exercised by a live negative control — see `NOT_VERIFIED` in
the repair report and §3.6.4 — so satisfiability is established by measurement,
bite by reasoning.

#### 3.2.3 Residual, disclosed rather than closed — **now CLOSED by UI-01c**

Three `text-slate-500` sites were already passing, were not in scope, and were
not changed — but they are the tightest margins left on the page and are
recorded so a future edit to them re-measures rather than assumes headroom:

| Site | Size | Foreground / background | Measured then | **Measured now** | Required |
|---|---|---|---|---|---|
| "Latest: …", `app/page.tsx:13` | 14px | `#62748e` on `#f8fafc` | **4.55:1** | **8.57:1** | 4.5:1 |
| "Research integrity you can inspect", `components/app-shell.tsx:51` | 12px | `#62748e` on `#ffffff` | **4.76:1** | **9.19:1** | 4.5:1 |
| "Read-only demonstrator…", `components/app-shell.tsx:77` | 12px | `#62748e` on `#ffffff` | **4.76:1** | **9.19:1** | 4.5:1 |

`4.55:1` is 0.05 above the threshold and `4.76:1` is 0.26 above it. They are
passes, not violations, and they are called out here precisely because they
would not survive an unnoticed edit to the `text-slate-500` token or to either
of the two backgrounds above.

**UI-01c closed all three**, which is what findings F1 and F2 were opened for.
The margins are now 4.02 and 4.43 above the threshold respectively, measured in a
browser (§3.7.1), and the tokens involved no longer exist. **This table is
retained rather than deleted**, for the reason the "Closed since" items above
were: it records what the tightest margins on this page used to be, which is the
part a future edit needs.

Two corrections to this table, both found on review of the record rather than in
the code, since a gate record that miscounts its own residual-risk table is not a
trustworthy baseline. The `app-shell.tsx:51` row was missing entirely, so the
table recorded two sites where the page has three. And the footer row cited
line 78, which is the text, not the class — the `text-slate-500` class is on
line 77. No ratio was recomputed: the two `#ffffff` rows carry the `4.76:1`
figure this section already records, and the new row's foreground/background
pair is the same `#62748e` on `#ffffff`.

### 3.3 Open items

**Closed since §3.1:** rendered colour contrast (§3.2, with new measured ratios
at both viewports, `incomplete: []`, no rule suppressed to get there). It is
named here rather than deleted so this section stays a complete ledger of
everything that was ever outstanding.

**Closed since §3.3:** axe with the mobile dialog open, in a browser (§3.6, now
B10). The jsdom half of this item was already closed by `tests/shell.test.tsx`;
§3.6 closes the rendered half, and closes it with a negative control, which
that jsdom run does not have. Named here rather than deleted for the same
reason as the item above.

Still open:

- [ ] **Automated visual-regression baselines.** Not started, and **made more
      valuable by UI-01c** rather than less. `screenshots/` now holds six
      captures of a deliberately composed screen, which is exactly the input a
      visual-regression gate needs; nothing still compares two runs against each
      other, so a future visual regression would not be caught automatically.
- [ ] **A second route.** §4.3, unchanged by UI-00b. Still only `/`, so the
      layout-owned `main` is tested but not yet *exercised twice*.
- [ ] **Cross-browser rendering.** Chromium only. Firefox and WebKit are not
      installed and were not run, so no gate here may be read as
      engine-independent.
- [ ] **UI-03's narrow-width visual check**, in the sense the packet means it.
      UI-00b supplies narrow-width evidence for `/` only. The loading, empty and
      error states that clause is really about do not exist yet, so the item
      cannot be closed by this packet.
- [ ] **The governing UI-01c packet has no immutable identity** (F8).
      `../architecture/research_ui/` is untracked in every tree, so
      `AGENT_WORK_PACKETS.md` can drift or be falsified silently. Not fixable in
      this packet; the repository, not the file, is the problem.
- [ ] **`AGENT_WORK_PACKETS.md:40` points at a `VISUAL_DIRECTION.md` that does
      not exist there** (F9). Decision D3 relocated that document into
      `apps/research-ui/`, where the mission's write scope and the design tokens
      both live. The governing packet is not editable in this packet, so the
      reference stays broken until a follow-up fixes it.

### 3.4 Runner note: `next start` under `output: "standalone"`

`next.config.ts` sets `output: "standalone"`, and `next start` prints:

```text
"next start" does not work with "output: standalone" configuration. Use "node .next/standalone/server.js" instead.
```

It then serves correctly anyway: **all 25 tests ran** against real rendered markup
at both viewports, and the measured values in §3.1 are consistent with the
source. The warning is recorded rather than silenced and the alternative was not
adopted, because switching the harness to `.next/standalone/server.js` would
change what is under test without a reason any gate requires. Next.js
**16.3.6**, Chromium build 1243.

*(This paragraph read "all 23 tests ran" and was missed when §3 and §3.1 were
updated during UI-01c. The figure is now 25 — 23 at UI-01c, 25 after the repair
pass's gate 21. Corrected rather than left to drift again.)*

### 3.5 Effect on the packet table

| Packet | `Gate:` clause (verbatim) | Residual browser-only element, after UI-00b |
|---|---|---|
| UI-01 (:13) | "Typecheck plus mobile/desktop screenshots and keyboard traversal." | **None.** Typecheck (gate 9), keyboard traversal (gates 12-13, now confirmed by B1), and the mobile/desktop screenshots (B2, B5) are all closed. |
| UI-02 (:23) | "Populated, loading, empty, and error fixtures; component tests." | None |
| UI-03 (:33) | "State matrix test and narrow-width visual check." | **Yes** — the narrow-width visual check. B2/B5/B6 cover `/` at 375px; the states that clause is about do not exist yet. See §3.3. |
| UI-04 (:43) | "Keyboard-only flow, validation states, and disabled mutation test." | None |
| UI-05 (:53) | "Complete and broken-lineage fixtures plus accessibility check." | None — but the in-process accessibility check was shown to miss a real, serious failure (§3.2). That failure is now fixed, and the lesson is not retired: the check could not see it, and only a rendered run could. Treat "satisfiable in jsdom" as weaker than it reads. |
| UI-06 (:63) | "Empty, mixed-outcome, and malformed-event fixtures." | None |

The UI-02, UI-04, UI-05 and UI-06 gates remain fully closable in jsdom with the
§1 runner. UI-01 is now wholly closable. UI-03 is not, and the reason is
missing application surfaces, not a missing browser.

### 3.6 The mobile dialog open, measured in a browser (B10)

**This state was previously unmeasured, and the §3.2 contrast repair was blind to
it.** The three "Not yet available" nav tags live in the desktop `<nav>`, which
is `hidden lg:block`, so below 1024px they render nowhere. On mobile they live
inside `MobileNav`'s Headless UI dialog, which **unmounts when closed** —
measured in-repo at `tests-browser/responsive-nav.spec.ts:122`, where the panel
goes to `toHaveCount(0)` after `Escape`. So the 375px axe run in §3.2 was
measuring a page with **no navigation in the DOM at all**, and it was green
over that absence. §3.2's per-site table says the `text-slate-500` → `text-slate-600`
repair was measured at "1440px, 3 nodes" — correct, and true of no other
viewport. Nothing in the file claimed mobile-dialog contrast had been checked,
because it never had.

`tests-browser/rendered-axe.spec.ts` now carries a fourth test,
`375px: zero real violations with the mobile dialog open`, which sets
`MOBILE_VIEWPORT`, opens the disclosure by role + accessible name
(`MOBILE_NAV_TRIGGER_LABEL`), asserts `#mobile-primary-nav` is **visible** before
measuring, then runs the same `runAxe` / `summarise` / `report` path as its
siblings and asserts the same two things: `outcome.violations` is `[]` at any
impact, and `color-contrast` is in `outcome.passes`. The visibility assertion is
load-bearing, not decoration — Headless UI unmounts the panel when closed, so
without it this test could pass while measuring the same navigation-free page
the closed-dialog run already covers.

#### 3.6.1 The measured result, quoted

```text
[measured] 375px: zero real violations on the rendered page
[measured] 375px axe: color-contrast=pass ; violations=none ; incomplete=none ;
[measured] 375px dialog-open axe: color-contrast=pass ; violations=none ; incomplete=aria-hidden-focus(2) ;
```

Zero violations of any impact. `color-contrast` is a **decided pass**, present in
`outcome.passes` — not an `incomplete` — so the §3.2.2 non-vacuity guard is
satisfied by a real verdict and the empty `violations` array is not vacuous.
**`incomplete` holds exactly one rule, `aria-hidden-focus`, on 2 nodes.**

#### 3.6.2 Why the translucent backdrop did not force `color-contrast` into `incomplete`

The risk was real and it was checked rather than assumed. `DialogBackdrop` is
`bg-slate-900/30`, computed as `oklab(0.207998 -0.00311178 -0.0418783 / 0.3)`,
and anything painted over it would have had an undecidable background. Nothing
is, at 375px, because the panel covers the viewport completely:

| Measurement | Value |
|---|---|
| `DialogPanel` rect at 375px | `x: 0`, `width: 375` (`w-full` beats `max-w-sm`, 384px) |
| `DialogBackdrop` rect at 375px | `x: 0`, `width: 375` — entirely behind the opaque panel |
| `DialogPanel` computed background | `rgb(255, 255, 255)` — opaque, so axe resolves every text node in it |
| `[role="dialog"]` computed background | `rgba(0, 0, 0, 0)` — transparent, but it paints no text |
| Leaf text nodes outside the panel | 71 — all of them in the `aria-hidden` background (6 `aria-hidden` nodes, 1 `inert`), which is consistent with the run producing **zero** `color-contrast` `incomplete` entries: none of them was left undecidable, because none of them was in the accessibility tree |

So the translucent backdrop is present and fully rendered, and it is still not a
contrast hazard, because the opaque panel sits on top of all of it. **No
allow-list, no `exclude`, no disabled rule and no relaxed assertion was needed
to reach that result** — it is what the markup already does. Had the panel been
narrower than the viewport, the backdrop question would have been live and
`color-contrast` could legitimately have gone to `incomplete`; that was the
finding to watch for, and it did not occur.

#### 3.6.3 The one `incomplete` node, named exactly

`aria-hidden-focus`, impact `serious`, 2 nodes, and it is **not** the application's
markup — it is Headless UI's own focus guards:

```text
button[data-headlessui-focus-guard="true"]:nth-child(1)
button[data-headlessui-focus-guard="true"]:nth-child(3)
```

Both are `<button>` elements measuring **1 × 0 px**, sitting inside
`aria-hidden="true"` and **not** inside the `[inert]` subtree. `aria-hidden-focus`
fires precisely because they are focusable elements inside an aria-hidden
subtree — which is their entire purpose: they are sentinels Headless UI injects
at the boundary of the hidden background so the browser's sequential focus
cannot land in it. The rule is correctly describing a real, library-generated
situation; it is not a defect in `MobileNav`, and it is not a contrast result.
It is reported, not suppressed.

Recorded precisely, because "the suite is green" is not the claim: the run's
`incomplete` is not empty, and that is why `summarise` prints
`incomplete=aria-hidden-focus(2)` rather than `incomplete=none`. The §3.2
header's "`incomplete: []` at both viewports" is still true **of the two
closed-dialog runs** and is not extended to this third state.

#### 3.6.4 Negative control: the new test does bite

The packet's point was that a negative control re-breaking
`components/primary-nav.tsx:52` to `text-slate-500` **passed at 375px** and
failed only at 1440px, so the closed-dialog mobile run protected nothing. With
the dialog-open test in place, re-breaking that one class makes the **375px
dialog-open** test fail. Reverting only `text-slate-600` → `text-slate-500` on
`UNAVAILABLE_TAG_CLASS` and re-running `npx playwright test
tests-browser/rendered-axe.spec.ts`:

```text
[measured] 375px axe: color-contrast=pass ; violations=none ; incomplete=none ;
  ✓  1 … 375px: zero real violations on the rendered page (3.9s)
[measured] 1440px axe: color-contrast=pass ; violations=color-contrast(serious, 3 nodes) ; incomplete=none ; …
  ✘  2 … 1440px: zero real violations on the rendered page (4.3s)
[measured] 375px dialog-open axe: color-contrast=pass ; violations=color-contrast(serious, 3 nodes) ; incomplete=aria-hidden-focus(2) ; color-contrast@4.34 .flex-col > li:nth-child(2) > .flex-wrap.gap-2.rounded-md > .py-0\.5.text-\[0\.6875rem\].bg-slate-100 | …
  ✘  3 … 375px: zero real violations with the mobile dialog open (4.1s)
  ✓  4 … negative control: axe really runs on the live page (2.0s)
  2 failed
```

All three broken-contrast nodes read
`Element has insufficient color contrast of 4.34 (foreground color: #62748e,
background color: #f1f5f9, font size: 8.3pt (11px), font weight: normal).
Expected contrast ratio of 4.5:1`, failing at `rendered-axe.spec.ts:213` on
`expect(outcome.violations).toEqual([])`. `components/primary-nav.tsx` was
restored and SHA-256-verified back to `52d02a9302ce5af90fa00ab431af4dec8fc440b1e163bf83105d75f94bb290fc`,
its pre-control hash, and the full suite was re-run green. Test 1 passing while
tests 2 and 3 fail is the measurement that matters: the closed-dialog mobile
run still cannot see navigation, and the open-dialog one can.

**One honest limit, which this control did *not* close.** The failure landed on
the `violations` assertion at line 213, so the non-vacuity guard at line 214
never executed. This control proves the new test detects a real contrast
failure; it does **not** exercise the §3.2.2 guard's own failing path, and that
item stays in `NOT_VERIFIED`. (A separate pre-existing wrinkle, visible in the
quoted line and left alone: when a rule passes for some nodes and violates for
others, `summarise`'s three-way precedence prints `color-contrast=pass` because
the id is present in `passes` at all. The adjacent `violations=` field and the
`toEqual([])` assertion carry the real verdict, which is why the run was still
correctly red. `summarise` was not restructured in this packet.)

**The `summarise` wrinkle above is FIXED by UI-01c** — finding F5 — by inverting
the precedence so a violation outranks a pass. See §3.7.3. It is left in this
section's text as written, because §3.6.4 is the record of that run and editing
it would falsify the quoted output.

### 3.7 Packet UI-01c — the visual-direction redesign

**This section is measurement, not judgement.** UI-01c changed how `/` looks:
warm paper for a cold dashboard, hairlines for cards, a document trail for a
stack of panels. `VISUAL_DIRECTION.md` is the design argument. What follows is
only what was measured, so that a reviewer can check the claims rather than take
them on trust.

**What is deliberately not in this section.** UI-01c cannot certify its own
visual direction. Nothing here claims a screenshot was looked at or judged. The
six captures in `screenshots/` exist for the human to open; §3.7.2 says which
motif each one should show, and that mapping is a claim to be checked, not a
result.

**Which of these numbers a reviewer can re-run, and which they cannot — stated
before any of them, so the tables are not read as more durable than they are.**

| Evidence | Reproducible from the committed suite? |
|---|---|
| Zero axe violations; `incomplete` exactly `[]` / `[]` / `aria-hidden-focus(2)` | **Yes.** `rendered-axe.spec.ts` asserts all of it, on every run |
| Focus ring `2px solid rgb(28, 26, 23) offset=2px`, both rules, both viewports | **Yes.** `focus-visibility.spec.ts` prints and asserts it |
| No horizontal overflow, 375/375 and 1440/1440 | **Yes.** `overflow.spec.ts` asserts it |
| Tab order, dialog focus trap, Escape restoration | **Yes.** `tab-order.spec.ts`, `responsive-nav.spec.ts` |
| Six PNGs with valid magic bytes and their byte sizes | **Yes.** `screenshots.spec.ts` asserts and prints each size |
| **Per-site contrast ratios** (§3.7.1) | **No.** The committed suite asserts *that every text node passed*, not *which ratio each one got*. The specific ratios came from a temporary measurement spec, now deleted |
| **Box geometry** (§3.7.6) | **No.** Same: the committed suite asserts overflow-free, not box dimensions |
| **Lab ΔE separations** (§3.7.7) | **No.** Computed from the token hexes; no committed test measures colour distance |

The second group is real measurement, taken in a real browser, and is reported
as such. But it is **not** enforced, and a future edit could invalidate a number
in §3.7.1, §3.7.6 or §3.7.7 without turning any gate red. That is the honest
boundary of this section: the *assertions* are permanent, the *tables* are
snapshots.

**The run that produced all of it**, recorded once, as the packet requires:

```
npm run typecheck && npm test && npm run build && npm run test:browser
```

| Stage | Result |
|---|---|
| `tsc --noEmit` | **exit 0** |
| `vitest run` | **53 passed / 7 files**, 11.57s |
| `next build` (Next 16.3.6, Turbopack) | **exit 0** — `/` and `/_not-found` static |
| `playwright test` | **24 passed**, 43.6s, 1 worker |

23 → 24 browser tests is **exactly one** added test, `1440-evidence-trail.png`.
No test was deleted, renamed, skipped, or loosened. All 53 unit tests still pass
against restyled markup with **zero** edits to any file in `tests/` — which is
the strongest single piece of evidence for F6 and A5 in this record: content was
preserved by construction rather than by rewriting the assertions that check it.

Three pre-existing runner warnings, unchanged and benign: jsdom cannot provide
`HTMLCanvasElement.getContext` (×3), `next start` ignores `output: standalone`
(the config's own `webServer` is used in practice), and npm's
`allow-scripts` notice from the WebServer subprocess.

#### 3.7.1 Contrast, re-measured on the new palette

Read out of axe's own `color-contrast` **pass** nodes — `fgColor`, `bgColor`,
`contrastRatio`, `expectedContrastRatio` — on the rendered page at both
viewports. Not recomputed from the hexes, not assumed.

The two findings UI-00b left open, both now closed with large margins:

| Site | Then | Now | Margin gained | Required |
|---|---|---|---|---|
| "Latest: …" (`app/page.tsx`, F1) | 4.55:1 | **8.57:1** | +4.02 | 4.5:1 |
| "Research integrity you can inspect" (`app-shell.tsx`, F2) | 4.76:1 | **9.19:1** | +4.43 | 4.5:1 |
| "Read-only demonstrator…" (`app-shell.tsx`, F2) | 4.76:1 | **9.19:1** | +4.43 | 4.5:1 |

Every text role on the page, against both grounds:

| Role | Ground | Ratio | Size | Required |
|---|---|---|---|---|
| `ink` `#1c1a17` | paper | 15.66:1 | 18-36px | 4.5:1 |
| `ink` `#1c1a17` | leaf | 16.79:1 | 12-18px | 4.5:1 |
| `ink-muted` `#4a453d` | paper | 8.57:1 | 14-18px | 4.5:1 |
| `ink-muted` `#4a453d` | leaf | 9.19:1 | 11-14px | 4.5:1 |
| **`ink-faint` `#6b6357`** | **paper** | **5.34:1** | **11px** | 4.5:1 |
| **`ink-faint` `#6b6357`** | **leaf** | **5.72:1** | **11px** | 4.5:1 |
| `evidence` `#1f3a5f` | paper / leaf | 10.36:1 / 11.11:1 | 11-14px | 4.5:1 |
| `success` `#1f5c3a` | paper / leaf | 7.15:1 / 7.67:1 | 11px | 4.5:1 |
| `warning` `#7a5410` | paper / leaf | 6.11:1 / 6.54:1 | 11px | 4.5:1 |
| `refusal` `#8f2f28` | paper / leaf | 7.27:1 / 7.80:1 | 11px | 4.5:1 |

**`ink-faint` is the tightest role on the page, at 5.34:1 with 0.84 of headroom.**
It carries the marginal `Stage N` ordinals, the trail's ordinals, and the
`Not yet available` stamp. If `--color-paper` is ever darkened, these are the
nodes that must be re-measured first. The hand-written table in
`app/globals.css` was corrected to these axe-reported figures; the values it
carried before were computed by hand and were up to 0.02 out.

#### 3.7.2 Screenshots: six, and which motif each should show

| File | Viewport | Motif a reviewer should find it in |
|---|---|---|
| `1440-evidence-trail.png` | 1440, element-scoped on `section[aria-labelledby="evidence-title"]` | **M1** the signature motif at readable size |
| `1440-overview.png` | 1440, full page | M1, M2, M4, M5, M6 |
| `375-overview.png` | 375, full page | M2, M3 — and M1's narrow-width form |
| `375-mobile-nav-open.png` | 375, dialog open | M4 on the panel; focus containment |
| `375-skiplink-focused.png` | 375, skip link focused | the A4/P6 exemption, visible |
| `1440-skiplink-focused.png` | 1440, skip link focused | the exemption at desktop size |

`1440-evidence-trail.png` is new in this packet and is the reason the browser
count moved 23 → 24. It is element-scoped, selected by the `aria-labelledby` the
section already carried, so it adds no attribute to the markup.

#### 3.7.3 What the suite now enforces that it did not before

**One new test** (`screenshots.spec.ts`, above). Everything else in this
subsection is assertions added *inside* existing tests. No test was deleted,
renamed, skipped, or loosened, and no axe rule was disabled, allow-listed or
excluded.

| Addition | Protects | Where |
|---|---|---|
| `incomplete` ledger asserted: exactly `["aria-hidden-focus(2)"]` on the dialog-open run, `[]` on the other two | **A6.** `incomplete` was previously *printed* by `summarise` and never checked, so a `color-contrast` that silently moved `passes` → `incomplete` — an undecidable background, a gradient, an overlap — would have stayed green on every assertion in the file. This is the assertion standing between the contrast gate and vacuity | `rendered-axe.spec.ts` |
| Skip-link `outlineColor` asserted against the live `--color-focus` token, at **both** viewports | A9 / **F3**. Previously the skip-link tests checked width, `clip-path` and box geometry but never the ring *colour*, so a skip link carrying a different colour from the shared rule would have passed | `focus-visibility.spec.ts` |
| `--color-focus` asserted `!== "rgb(16, 16, 16)"` | Non-vacuity for the above. Reading the token cannot catch a deleted CSS rule, but width/style/offset are pinned independently and would | `focus-visibility.spec.ts` |
| Nav ring cross-checked against the skip-link ring, both now on `--color-focus` | A9. **F3's real trap**: a separate `--color-focus` on the global rule while `.skip-link:focus` kept `--color-accent` would satisfy A9 perfectly and fail here, because the two render different colours | `focus-visibility.spec.ts` |
| `summarise` precedence inverted: violation → incomplete → pass → not-evaluated | **F5.** It read `passes` first, so a rule that both passed and violated printed `color-contrast=pass` — a log contradicting the red assertion beside it. Reporting only, but a log that says "pass" for a failing page is what later gets quoted in a report | `rendered-axe.spec.ts` |
| `toRgbString` / `readColourToken` in `helpers.ts` | **D4/F3.** A declared hex reads back as `#1c1a17`; a computed colour reads back as `rgb(28, 26, 23)`. Comparing them fails on format even though both are the same colour. `toRgbString` **throws** on anything it cannot normalise rather than returning a best-effort string | `helpers.ts` |

**The stale-literal removal is the one judgement call here**, so it is argued
rather than asserted. `focus-visibility.spec.ts` used to assert the literal
`rgb(29, 78, 216)` twice. That literal was a second, undeclared copy of
`--color-accent: #1d4ed8`, and the copy — not the stylesheet — was deciding the
test. Reading the token instead is what the test was always about: *the
application's own declared ring, not the browser's fallback*. It is not a
weakening, because three things are asserted independently of the colour: the
ring is `2px`, `solid`, offset `2px` (no user-agent default produces that
triple); the token is not the user-agent default colour; and the nav ring is
compared against the skip link's measured ring in the same run. **The failing
path of the colour assertion has not been exercised by a live negative control**
— see `NOT_VERIFIED`.

#### 3.7.4 The focus ring moved, and both rules moved together

`--color-accent` (`#1d4ed8`, `rgb(29, 78, 216)`) is **gone**. The ring is
`--color-focus` = `#1c1a17` = `rgb(28, 26, 23)`, declared as its own token so a
future change to body ink cannot silently restate the ring. Both rules read it,
which the emitted CSS confirms:

```css
a:focus-visible,button:focus-visible{outline:2px solid var(--color-focus);outline-offset:2px}
.skip-link:focus{...outline:2px solid var(--color-focus);outline-offset:2px;...}
```

Every §3.1/§3.2 line that quotes `rgb(29, 78, 216)` is marked superseded above.
The **geometry is unchanged** — 2px, solid, offset 2px, on the skip link, the
desktop nav link, the mobile trigger, the dialog close button and the mobile nav
link. Only the colour changed, and it changed to ink, which is the right choice
for a design whose only meaning-bearing boundary should be unmistakable against
a warm ground.

`.skip-link:focus` also changed shape, under the A4 functional-state exemption:
radius `0.5rem` → `0.25rem`, a **one**-layer box-shadow instead of two, and a
new 1px `--color-rule-strong` border so its edge is defined where the shadow is
faint. The argument for spending the exemption here, rather than leaving the
overlay with neither radius nor elevation, is written out at
`app/globals.css:158-171`.

#### 3.7.5 Gate 19 superseded under ratified authority; gate 20 substituted; gate 21 restores the traded property

##### The authority

Gate 19 required `--color-surface: #f8fafc` and `--color-ink: #172033` in the
emitted CSS and that **no colour token was removed**. UI-01c did all three things
it forbids, so gate 19 as written **fails**. It is recorded as **failed as
written** in the §1 table, not quietly reworded, and it is not deleted.

The substitution was **not** taken on an implementer's own authority. An earlier
revision of this section recorded the failure as "knowingly", which named no
decision-maker and so read as an implementer's private judgement. That was wrong
in substance, not just in tone: no agent may waive a gate. The record now reads:

| Field | Value |
|---|---|
| **Decided by** | The **human packet owner**, through the UI-01c review (`CHANGES_REQUESTED`), which **ratified** the gate 19 → gate 20 supersession. Not an implementer, not a subagent, and not this repair pass. |
| **Recorded** | **2026-10-02**, in this section and on gate 19's row in §1. |
| **Review date** | The review itself carries no in-repo date, so this row records the date the decision was *written down*, not a date claimed for the decision. |
| **Scope** | Authorises **this** palette change — the twelve UI-01c role tokens replacing the three UI-01 tokens. It is **not** a standing waiver, **not** a precedent for any future palette change, and **not** permission for any other gate to be superseded. |
| **Condition** | Ratified **only on condition that the general property gate 19 carried survives as a committed, enforced check.** That condition is discharged by **gate 21**, below. Without gate 21 the ratification is void and gate 19 stands as failing. |

##### Why a general property was traded for an enumeration

Because gate 19 was a **drift detector** and gate 20 is an **enumeration**, and
they detect different things:

| | Gate 19 (drift detector) | Gate 20 (enumeration) |
|---|---|---|
| Catches | The removal of **any** colour token, and drift in two named values | Only the **three named** UI-01 tokens and the three named UI-01 hexes |
| Stability | **Unsatisfiable by any deliberate palette change.** UI-01 preserved those values *on purpose*, so that a later packet would have to name a change. Naming it is the mechanism working | Stable indefinitely; a token added in UI-02 and later deleted is **not** caught |
| Verdict | Honest but unusable | Usable but narrow |

An enumeration is the right instrument for "did *this* change do what it said".
It is the wrong instrument for "could anything have leaked", and two real leaks
were found once the trade was examined — see §3.7.9. So the trade is legitimate
**only** because the general property was not discarded with it: gate 21 asserts
the property generally, over *every* token and *every* palette family, rather than
over the twelve names that happen to exist today. Had the enumeration been
substituted alone, the correct verdict would have been to refuse the
ratification.

Gate 20, against `.next/static/chunks/*.css`:

| Check | Result |
|---|---|
| `--color-paper`, `--color-leaf`, `--color-ink`, `--color-ink-muted`, `--color-ink-faint`, `--color-rule`, `--color-rule-strong`, `--color-evidence`, `--color-success`, `--color-warning`, `--color-refusal`, `--color-focus` present | **yes, all 12** |
| `--font-display`, `--font-interface` present | **yes, both** |
| `--color-surface`, `--color-raised`, `--color-accent` absent | **yes, 0 occurrences** |
| `#f8fafc`, `#172033`, `#1d4ed8` absent | **yes, 0 occurrences** |
| `#f6f3ec` (paper) and `#fdfbf7` (leaf) present | **yes** |
| **no other `--color-*` variable at all** — the shipped stylesheet carries exactly those 12 | **yes, 12 total** (Tailwind v4 tree-shakes its default theme) |

`color-scheme: light` is retained unchanged, and still governs canvas resolution
and UA-rendered controls exactly as §1.2 disclosed.

#### 3.7.6 Layout, measured at both viewports

| Measurement | 375px | 1440px |
|---|---|---|
| `documentElement` scrollWidth / clientWidth | **375 / 375** | **1440 / 1440** |
| Evidence trail `<ol>` box | 327 x 526 | 856 x 426 |
| Workflow `<ol>` box | 327 x 699 | 1216 x 535 |
| Editorial `<aside>` box | 327 x **171** | 320 x **171** |
| Each trail `<li>`'s `firstElementChild` | `<span>` holding `1`..`5` | same |
| Each trail `<li>`'s spine `border-left` | **1px** | **1px** |

Three things this settles, none of them by assertion:

- **A10.** No horizontal overflow at either viewport, and the aside measures
  **171px against the trail's 426px** at 1440px — it hugs its content instead of
  stretching into an oversized empty block. `self-start` from UI-00b's repair D2
  still does its job under the redesign.
- **A12.** The trail keeps its **document form at 375px**: the marginal ordinal is
  a real `<span>` with real text, and the hairline spine is still 1px. It did not
  collapse into cards at narrow width. The marginal node kind stacks above the
  label instead of hiding behind a breakpoint.
- **A13.** The workflow `<ol>` is one 699px (375px) / 535px (1440px) ruled
  sequence, not a grid of tiles.

#### 3.7.7 State distinguishability (F7)

`tests/status-badge.test.tsx:36` proves only that the four states carry distinct
class *strings*. Four visually identical palettes would pass it. Measured
instead, in CIE Lab, with the three instantiated states read off the live DOM and
`refused` read off its token (the fixture never declares it):

| State | Token | Rendered colour | on paper | Closest neighbour | ΔE |
|---|---|---|---|---|---|
| `complete` | `--color-success` | `rgb(31, 92, 58)` | 7.15:1 | `waiting` | **47.8** |
| `active` | `--color-evidence` | `rgb(31, 58, 95)` | 10.36:1 | `complete` | **51.1** |
| `waiting` | `--color-warning` | `rgb(122, 84, 16)` | 6.11:1 | `refused` | **34.5** |
| `refused` | `--color-refusal` | *(not instantiated)* | 7.27:1 | `waiting` | **34.5** |

The tightest pair is `waiting`~`refused` — ochre against oxide — at ΔE 34.5, an
order of magnitude above a just-noticeable difference. All six pairwise
separations exceed it by a wide margin. Colour is in any case never the only
channel: every stamp renders its state word inside the stamp, plus a filled dot,
and `tests/status-badge.test.tsx:18` pins the word.

**`refused` was not rendered anywhere on this screen.** Its numbers are
token-derived, which is weaker than rendered measurement, and that is stated
here rather than glossed.

#### 3.7.8 Findings closed, and what stays open

| ID | Outcome |
|---|---|
| **F1**, **F2** | **Closed.** Re-measured above with 4+ points of margin gained. |
| **F3** | **Closed.** The accent moved; the literal is gone; hex→rgb normalisation added; both rules on one token; the cross-check still bites. |
| **F4** | **Closed by enforcement.** `incomplete=aria-hidden-focus(2)` is now asserted exactly, on the one run that legitimately produces it, and `[]` on the other two. Still reported, never suppressed. |
| **F5** | **Closed.** Precedence inverted. |
| **F6** | **Satisfied as design constraints.** All five couplings hold with **zero** test edits. `home-page.test.tsx` and `evidence-chain.test.tsx` are byte-identical to the baseline. The `Demonstration data` label stayed in the shell `<header>` because it is an anti-fabrication guard, not presentation. |
| **F7** | **Closed by measurement** (§3.7.7). The class-string test is untouched. |
| **F8** | **Open, not fixable in this packet.** `../architecture/research_ui/` is untracked, so the governing UI-01c packet has no immutable SHA. `VISUAL_DIRECTION.md` was therefore relocated into `apps/research-ui/` (decision D3) so that the design direction *does* have an identity, but the governing packet still does not. |
| **F9** | **Open.** `AGENT_WORK_PACKETS.md:40` still points at a `docs/…/VISUAL_DIRECTION.md` that does not exist. That file is not editable in this packet. |
| **F10** | **Closed by the A4 functional-state exemption**, argued in place at `app/globals.css:158-171` and recorded in §3.7.4. |

**A5 — nothing removed.** The redesign is a composition change, and the component
tests that pin content held green throughout without being adjusted. Specifically
still present: all six stage labels with their descriptions, states and counts
(four complete, one active, one waiting — the packet's "four workflow stages" are
the four complete ones); all five evidence nodes with kind, label and detail; the
`Demonstration data` marker; and the read-only authority statement. **No badge,
description, count or node kind was dropped to satisfy A4, A11 or A12**, which
was the specific failure mode this packet had to avoid.

#### 3.7.9 Gate 21 — the root cause, and four live negative controls

The ratification's condition (above) is discharged here. Three things happened, in
this order: fix the root cause, then guard it, then prove the guard bites.

##### The root cause: documentation was compiling into the stylesheet

Gate 20 checks *names*. It cannot notice that those names were being **shipped**.
Tailwind v4 discovers utility candidates by scanning the tree, and its scanner does
not distinguish a class name in a component from the same characters inside a
sentence. So Markdown that *described* the retired palette — `GATES.md`, the
packet, `VISUAL_DIRECTION.md`, `../architecture/research_ui/` — was being
compiled into real rules:

| Present in emitted CSS before the fix | Source |
|---|---|
| `.text-slate-500`, `.text-slate-400`, `.text-slate-600`, `.bg-slate-100`, `.bg-slate-900/30` | findings prose in `GATES.md` and `UI-01C_WORK_PACKET.md:182` |
| `--color-slate-100/400/500/600/900` | same |
| `.rounded-lg`, `.rounded-xl`, `.blur`, `.mt-10`, `.mt-12`, `.py-0`, `.static` | `VISUAL_DIRECTION.md` A5/A8 and `GATES.md` prose |

The severity is in the last row. `VISUAL_DIRECTION.md` was **generating the exact
utilities it forbids** — `rounded-lg` and `blur` were in the "avoid" list and in
the shipped CSS. And a future author typing `text-slate-500` would silently
receive UI-00b's `#62748e`, which **passes axe at 4.55:1**, fails nothing, and is
wrong.

##### Two implementation findings, both recorded because both failed silently

**1. The test suite was a second source, and the guard was feeding itself.**
Fixing only Markdown left three selectors and three variables in the build. The
residue came from `tests-browser/hygiene.spec.ts` — **the new guard's own JSDoc**,
which names `text-slate-500`, `bg-slate-900/30` and `blue-700` to document what it
forbids. Being a `.ts` file it is read as a class-name source, and Tailwind does
not strip comments from `.ts`/`.tsx`. The guard was regenerating the exact defect
it exists to catch. This was not caught by reading the diff: it was caught by
gate 21 failing on a clean tree during the targeted run.

**2. `@source` paths resolve relative to the CSS file's directory, not the app
root.** `app/globals.css` lives in `app/`, so `./tests-browser/**` means
`app/research-ui/app/tests-browser/**`, which does not exist. It excludes nothing,
emits no warning, and still compiles the palette. The first two directives
appeared to work only because `../` incidentally reaches the app root. The
directives as shipped are:

```css
@source not "../../**/*.md";
@source not "../tests/**";
@source not "../tests-browser/**";
```

`../../**/*.md` replaces the original pair. Paths resolve from `app/`, so `..` is
`apps/research-ui/` and `../..` is `apps/`: the new pattern covers every Markdown
file under `apps/`, which strictly subsumes the `../**/*.md` it replaced (that one
reached `apps/research-ui/` alone). It does **not** reach `docs/`, which sits
outside `apps/`. An earlier revision of this section claimed it covered the
monorepo "including `docs/`"; that was wrong arithmetic in the one comment whose
job is to stop the next maintainer "correcting" the path, and it has been corrected
in `app/globals.css` too.

`docs/` is deliberately **not** excluded. Nothing under it has ever been scanned:
the only Tailwind-shaped token anywhere in `../architecture/research_ui/` is
`text-layer`, which is not emitted and is not a class this application could use.
Adding an exclusion for a directory that was never scanned would be a guess
presented as a fix. `app/` and `components/` stay scanned, so no real utility is
lost. This is written into the comment block above the directives in
`globals.css` as well, because the incorrect spelling is the one anyone would
naturally write.

##### Verified empirically on Tailwind 4.3.3, not assumed

`@source not` was confirmed to exist and take effect by rebuilding and diffing the
emitted CSS against the pre-fix baseline, with both measurements taken by the same
script and the same regexes:

| | Before | After |
|---|---|---|
| `.next/static/chunks/*.css` size | 21,170 bytes | **17,656 bytes** (−3,514) |
| raw-palette utility selectors | **5** | **0** |
| `--color-*` palette variables | **5** distinct | **0** |
| total class selectors in the file | 152 | 131 |
| selectors **removed** | — | **21, every one prose-only** |
| selectors **lost that any `.tsx` references** | — | **0** |
| selectors **gained** | — | **0** |

`--color-blue-700` is the diagnostic tell for finding 1: it occurs in exactly two
files, `GATES.md` (excluded) and `tests-browser/hygiene.spec.ts` (not excluded
until the paths were corrected), and it appeared in the intermediate build and in
neither of the endpoints.

The "0 legitimately lost" row is the load-bearing one, and it was checked per
selector by harvesting every `className` token from `app/*.tsx` and
`components/*.tsx` (112 tokens, variant prefixes stripped) and testing each
removed selector against that set. Two apparent hits were false positives of my
own earlier grep and are worth recording, because a laxer check would have
reported them as regressions:

* `.outline` matched `@heroicons/react/24/outline` in an import path, not a class.
* `.py-0` matched `py-0.5`.
* `.bg-paper` matched `hover:bg-paper` in `mobile-nav.tsx:44,62`. The *bare*
  utility was dead CSS harvested from prose; the used variant survives and
  resolves to the correct token:
  `.hover\:bg-paper:hover{background-color:var(--color-paper)}`.

So the bare `.bg-paper` rule was removed because nothing referenced it, not
because something lost it.

##### What `@source not` does not do, stated so nobody assumes it does

Tailwind still scans CSS *comments* it does not skip. `app/globals.css` names the
retired palette in prose, and that prose does **not** reach the stylesheet —
verified, the post-fix CSS contains zero `.text-slate-500` while the comment
remains in the source. `stripCssComments()` in the guard mirrors that behaviour
exactly, because a guard that reports the documentation as a defect is a guard
that gets disabled.

##### The guard: `tests-browser/hygiene.spec.ts`, one new test

Browser **24 → 25**, from **one** added `test()`, not three. One test, four
assertions, because all four share a single fixture — the served stylesheet — and
because each assertion carries a self-describing message naming the offending
**file and token**, so a failure is diagnosable without a re-run. If one of the
four breaks, the other three are masked until it is fixed; that trade was made
deliberately, and it is recorded here rather than hidden. Splitting into three
tests would mean fetching the stylesheet twice for no extra coverage.

| # | Assertion | Property restored |
|---|---|---|
| 1a | every `var(--token)` in `app/` + `components/` is **declared** in `app/globals.css` | **dangling reference.** CSS custom properties fail *silently*: a deleted token resolves to nothing, renders nothing, and `next build` exits 0 |
| 1b | …and actually **reaches the browser** (`token:` present in the served CSS) | a token can be declared in a file Tailwind does not scan — declared, never shipped, equally silent |
| 2 | **no raw palette utility** in `components/*.tsx` or `app/*.tsx` | **A1**, which was a source convention with **zero** enforcement. This is the enforcement |
| 3 | the **shipped stylesheet** has no raw-palette utility, no raw-palette variable, and none of the retired UI-01 tokens/hexes | the *actual* leak gate 20 could not express — it reads the bytes the server sends, not the build directory |

Assertion 3 is also what protects the `@source not` directives: they are a
four-line file edit, and this is the check that fails if they are deleted — or if
they are written in the plausible-but-wrong relative form described above.

##### Four live negative controls

A guard nobody has watched fail is an assumption. All four were run, and all four
were reverted.

| Control | Mutation | Result |
|---|---|---|
| **1a** | `var(--color-raised)` injected into a real rule in `app/globals.css` | **FAILS**, naming the file and the undeclared token. The message reads "every `var(--token)` in `app/` or `components/` must be declared in `app/globals.css`, or it resolves to nothing at runtime and no build error is raised" |
| **2** | `text-slate-500` added to a real `className` in `primary-nav.tsx`, no dangling token present | **FAILS** at assertion 2, naming `components\primary-nav.tsx: text-slate-500`, with the A1 message |
| **3** | **`@source not` directives deleted**, source tree otherwise **completely clean** | **FAILS** at assertion 3, reporting `--color-slate-100/400/500/600/900` and `--color-blue-700` in the shipped CSS |
| **4** | **no mutation at all** — run against an unmodified tree during the targeted browser pass | **FAILS**, reporting `.text-slate-500`, `.bg-slate-900`, `.bg-slate-900\/30` in the served CSS. It was **correct**: finding 1 was still live. Fixed at the root by excluding the test directories, not by relaxing the assertion |

Control 3 is the reviewer's own scenario: a clean tree, a small deletion, and the
gate goes red on the shipped bytes.

Control 4 is the one that earns the rest. It is the only control that was not
staged — it fired on the real repair, on a tree I believed was correct, and it
found a defect I had introduced two minutes earlier and would otherwise have
shipped. A guard that only ever catches mutations I planted would not have caught
this. Every mutation was reverted and the reverted state re-verified (0
directives removed, 0 residual `text-slate-500`, 0 residual `color-raised`).

Three defects were found **by running** rather than by reading the guard, and all
three are fixed:

- the failure path printed `pp\globals.css` because
  `file.slice(APP_ROOT.length + 1)` over-trimmed a path that already ends in a
  separator;
- assertion 2 initially scanned `.css` as well as `.tsx`, so it reported
  `app/globals.css`'s own prose — three false hits, one of which this section
  would otherwise have had to avoid writing;
- and the one from control 4: the guard's own JSDoc was a Tailwind source,
  because a `.ts` file is scanned and its comments are not stripped.

#### 3.7.10 The human visual gate, answered

UI-01c's §12 gate is the one no agent in this lane can close, because no agent
here can view an image. It was closed by the human packet owner on
`2026-10-02`, reviewing the six committed captures.

| | |
|---|---|
| **Decided by** | The **human packet owner**, opening the six captures in `screenshots/`. Not an implementer, not a subagent, and not this record. |
| **Recorded** | `2026-10-02` — the date written down. No in-repo artefact carries the decision's own timestamp, so this row is the record rather than a claim about when it was spoken. |
| **Scope** | The **visual direction** of this packet's single screen (`/`, including its chrome). It is **not** a waiver of any executable gate, **not** authority for a second route, and **not** precedent for a later packet. Every executable row above stands on its own recorded evidence, independently of this decision. |
| **Anti-template question** | **Answered no.** The page "no longer reads like a generic AI dashboard or a relabelled CRM", and reads as "a restrained research instrument". |
| **Motifs** | All three requested motifs confirmed **clearly visible**: the numbered spine (workflow stages and claim-trace nodes), the ruled workflow ledger, and the square stamps (`COMPLETE`, `ACTIVE`, `WAITING`). This discharges **A3** and §3.7.11 items 1 and 2. |
| **375px degradation** | **Accepted.** The marginal node-kind labels stack above their content at 375px; the hierarchy stays readable and the vertical rule plus numeral retains the lineage motif. Forcing a desktop-style margin on mobile "would likely hurt legibility". This closes the residual §3.7.6 disclosed. |

**One non-blocking observation, recorded not fixed (FU-2).** The human noted that
in both skip-link captures the focused skip link **overlaps the brand**. Accepted as
is, on the grounds that the state is transient and highly visible; a later polish
pass could give the affordance a dedicated top-layer placement. Left unfixed
deliberately: it changes no acceptance criterion, the skip link is correctly
focusable, visible and correctly ordered at both viewports (A8/A9, asserted), and
altering the layout inside this packet would have meant an unrequested change to a
composition the human had just approved.


#### 3.7.11 `NOT_VERIFIED` for UI-01c

1. **Visual direction was unverified here and is now answered by the human.**
   No agent in this lane can view an image, so nothing in this section certifies
   the composition. The human answered it on `2026-10-02`; see §3.7.10. §3.7.2
   is the mapping that was checked.
2. **The anti-template question was unanswered by measurement, and is now
   answered by the human.** "Could this page be relabelled as a finance or CRM
   dashboard without changing its structure?" is a judgement about structure.
   `VISUAL_DIRECTION.md` §1 answers it in prose; the human answered it in fact
   — **no** — and the record is §3.7.10.
3. **The failing path of the rewritten focus-colour assertion** has not been
   exercised by a live negative control. §3.2.2's identical limitation is
   inherited, not introduced: §3.7.3 argues the assertion is not vacuous, but
   satisfiability of the *colour* branch is established by measurement and bite
   by reasoning.
4. **No visual-regression baseline.** Six captures exist; nothing compares two
   runs. The §3.3 item stands, unchanged by this packet.
5. **Chromium only**, as always. No Firefox or WebKit evidence.
6. **`refused` was never rendered**, so §3.7.7's row for it is token-derived.
7. **The per-site ratios, box dimensions and ΔE values in §3.7 are not
   re-runnable.** The temporary spec that produced them was deleted, because it
   was scaffolding rather than a gate. The committed suite enforces the
   *conclusions* (every text node passes; nothing overflows) but not the specific
   numbers. Promoting these tables to enforced evidence would mean adding
   assertions on exact contrast ratios and box sizes, which is a maintenance
   liability for a screen that will keep changing — so this packet leaves it as a
   deliberate, recorded trade rather than pretending the gap is closed.

## 4. Known benign runner warnings

### 4.1 Vite CommonJS config loader

`npm run test` prints:

```text
(!) Your Vite config uses features that are unsupported by `configLoader: 'native'` ...
  - ESM syntax in a file loaded as CommonJS (vitest.config.ts:1:1).
```

`vitest.config.ts` is ESM source loaded through Vite's CommonJS path because
`package.json` has no `"type": "module"`. **The warning is benign and is
recorded here rather than silenced.**

For the record, the reason it is not fixed is a deliberate choice, not a
constraint. Renaming `vitest.config.ts` to `vitest.config.mts` would clear the
warning from inside this directory, touching neither `package.json` nor
application resolution — so that fix is available and in scope. It was not
performed in this repair for two reasons: the warning is harmless (the config
loads and the suite runs correctly), and the rename is a functional change with
real resolution risk that this repair did not ask for. Anyone closing it later
should expect to re-run the full suite after the rename.

### 4.2 React's `<html> cannot be a child of <div>` (introduced by UI-01)

Tests that render `RootLayout` from `app/layout.tsx` make React print:

```text
In HTML, <html> cannot be a child of <div>.
This will cause a hydration error.
```

This is **true and expected**, and it is a fact about the test harness, not
about the application. Next.js mounts a root layout into the *document*; a test
mounts it into a container `div`, which is not a legal parent for `<html>`. React
reports it and then omits `<html>` and `<body>` from the client render, so the
Testing Library container receives exactly the elements `<body>` would have
contained. `tests/shell.test.tsx` relies on that fact deliberately: to evaluate
document-level rules it transplants the container's children onto the real
`document.body`, and mirrors `lang` from the layout's exported `DOCUMENT_LANG`
and `document.title` from the layout's exported `metadata` — the app's own
values, never invented ones.

The warning is recorded rather than silenced. It is not suppressed because a
reviewer should be able to see why the tests mount a layout the way they do. It
is not fixed because the fix is to not render a root layout in a container
divider, which would mean giving up the composition test that proves the layout
actually wires the shell in.

Whether React 19's *hydration* of the real document is correct is **not** tested
here; it is covered by `npm run build` type/prerender checking only.

### 4.3 The shell owns the `main` landmark; a route must not

`components/app-shell.tsx` renders exactly one
`<main id={MAIN_CONTENT_ID} tabIndex={-1}>` and puts the route's content inside
it. `MAIN_CONTENT_ID` is exported from the shell, so the skip link's `href` and
the landmark's `id` are the same constant and cannot drift apart. `app/page.tsx`
therefore renders a plain `<div className="min-h-screen">` as its root: the route
supplies content, the shell supplies the landmark.

The obligation runs one way only. A route that forgets a `main` is already
correct, because the shell has one — and because the layout renders `{children}`,
there is no arrangement in which the shell's `main` and a route's `main` can both
be needed. The single remaining failure mode is a route that renders a `main` of
its own, which nests a second landmark inside the first: a `critical`
`landmark-one-main` violation, and a skip link that lands on the outer, near-empty
landmark instead of the content.

So the defect class is closed **by construction**, for every route including the
ones UI-02 through UI-06 have yet to add — not held by a convention that only the
one route currently in existence can exercise:

- `tests/shell.test.tsx` asserts the assembled route has exactly one `main`;
- …that the skip link's `href` resolves to it and that it carries
  `tabIndex="-1"`;
- …and, in the other direction, that `AppShell` **on its own** renders exactly
  one `main`, with the right `id` and `tabindex`, and the route's content inside
  it. That last assertion is deliberately written against the shell rather than
  against `/`: it is the one that survives the arrival of routes that do not yet
  exist, since it makes "a route that forgets its landmark" impossible rather
  than merely untested.

**What transfers to UI-02.** Not the landmark — the shell supplies that. A new
route must render **no** `main` of its own; it renders content only. No route
exists beyond `/` today, so the contract is *tested* but not yet *exercised
twice* (§3).

---

## 5. Packet UI-01d - i18n, RTL and the three-locale shell

This section records what packet UI-01d made executable, what it measured, and the
two items it **could not** close. The locale contract itself is
[`I18N.md`](./I18N.md); the governing packet is
[`UI-01D_WORK_PACKET.md`](./UI-01D_WORK_PACKET.md).

Everything below was produced by a command in this directory on this working tree.
Rows that could not be executed are marked, not omitted.

### 5.1 Executable gates added by UI-01d

| # | Gate | Covered by | Status |
|---|------|-----------|--------|
| I1 | Catalog parity: `fr` and `ar` carry **exactly** the same keys as `en`, no extras, no gaps — **74 keys since packet UI-02; the "41" this row originally stated was already stale against its own 42-key assertion** (there is no catalog digest; the SHA-256 pins in this test cover the four byte-frozen files only, see I2) | `tests/i18n-catalog.test.ts` | UI-01d snapshot - 10 files / 140 tests pass; **superseded for current totals by §6 U2 and §6.2** |
| I2 | Byte pins hold: `lib/mock-project.ts`, `lib/contracts.ts`, `package.json`, `package-lock.json` | `tests/i18n-catalog.test.ts` | EXECUTABLE - all four SHA-256 verified on the working tree |
| I3 | `translate()` refuses an unknown key and an empty interpolation result; no raw-key fallback | `tests/i18n-render.test.tsx` | EXECUTABLE |
| I4 | `<html lang dir>` is correct per locale **before hydration** | `tests-browser/locale-routing.spec.ts` (AC-2), `tests/shell.test.tsx` | EXECUTABLE - for supported locales; raw 404 lacks `lang`/`dir` (see §5.4) |
| I5 | The locale is the URL only: no cookie, no `localStorage`, no `sessionStorage`, verified from a **fresh browser context** | `tests-browser/locale-switch.spec.ts` (N13) | EXECUTABLE |
| I6 | Each selector link is the same path in another locale; activating `ar` from `/fr` lands on `/ar` | `tests-browser/locale-switch.spec.ts` (N14) | EXECUTABLE |
| I7 | The selector has no breakpoint: it is in the rendered ring at 375px and at 1440px | `tests-browser/tab-order.spec.ts` (D-I18N-11) | EXECUTABLE |
| I8 | No physical direction utility in `app/` or `components/`; `@source not` excludes Markdown, tests, `i18n/` and `messages/` | `tests/i18n-direction-source.test.ts` | EXECUTABLE - 6/6 |
| I9 | Arabic mirrors the trail's spine and ordinal column; ordinals stay 1...5 in document order; counts are locale-formatted and never digit-reversed; fixture runs are `<bdi>`-isolated and byte-identical; no icon is mirrored; focus order is unchanged | `tests-browser/direction.spec.ts` | EXECUTABLE |
| I10 | No hydration mismatch in any locale | `tests-browser/locale-routing.spec.ts` (N15) | EXECUTABLE |
| I11 | No horizontal overflow in `fr` and `ar` at 375px and 1440px, plus the original `en` runs | `tests-browser/overflow.spec.ts` (N16) | EXECUTABLE |
| I12 | No horizontally unbreakable token in the shipped fixture | `tests-browser/overflow.spec.ts` | EXECUTABLE |
| I13 | Rendered axe-core: zero real violations at 375px and 1440px, dialog open and closed, in all three locales | `tests-browser/rendered-axe.spec.ts` | EXECUTABLE - parameterized over `SUPPORTED_LOCALES` per P0-2 fix |
| I14 | **Contrast coverage** - the only contrast coverage is `rendered-axe.spec.ts` (M2). There is no `evidence-contrast.spec.ts`; the phantom file named in an earlier packet revision does not exist and nothing waits on it | `tests-browser/rendered-axe.spec.ts` | EXECUTABLE - the fr/ar runs are part of the evidence, because a longer string changes where a label wraps and therefore which tint it sits on |
| I15 | Skip link is keyboard reachable and its clip reveal really happens, in every locale | `tests-browser/focus-visibility.spec.ts` | EXECUTABLE |
| I16 | Token discipline (gate 21) after the new files landed | `tests-browser/hygiene.spec.ts` | EXECUTABLE - see 5.3 |
| I17 | **30 % expansion, and the precondition that makes it mean something** | `playwright.long-strings.config.ts` + `tests-long-strings/long-strings.spec.ts` | EXECUTABLE - 10/10, see 5.2 |
| I18 | Ten committed screenshots, `en`/`fr`/`ar` at 375px and `ar` at 1440px, plus the focus and dialog states | `tests-browser/screenshots.spec.ts` | EXECUTABLE - all ten regenerated in this run |

Browser suite: **53 passed / 53**, 10 files. Long-strings suite: **10 passed / 10**.
Vitest: **140 passed / 140**, 10 files. `npm run typecheck`: exit 0.
*(UI-01d snapshot, kept as this packet's dated evidence; the tree has since grown —
the current totals are §6.2. The stale numbers here are why §6 exists.)*

### 5.2 AC-9P - the 30 % expansion precondition, with the numbers

The previous formulation of this gate was **vacuous** (packet 13.2.1, finding B1): it
asked for 30 % inflation and then measured the already-built `.next` tree, which —
because `NEXT_PUBLIC_*` is inlined at build time — contained zero inflation. It passed
while proving nothing.

`playwright.long-strings.config.ts` now runs its own `next build` with
`NEXT_PUBLIC_I18N_EXPANSION_PERCENT=30` into `NEXT_DIST_DIR=.next-longstrings` on port
3121, and the spec's first assertion fetches the **served response body** and measures
one catalogued prose sentence inside it. Measured:

| Locale | Sentence | Un-inflated | Served | Ratio |
| --- | --- | --- | --- | --- |
| `en` | `overview.traceLede` | 60 | 103 | **1.7167** |
| `fr` | `overview.asideBody` | 121 | 168 | **1.3884** |
| `ar` | `overview.asideBody` | 88 | 118 | **1.3409** |

All three are `>= 1.30` and strictly greater than the source length, so the clipping
assertions that follow are measuring an inflated document. The `en` ratio exceeds
1.30 because `inflate()` appends whole filler phrases until the threshold is met, so
a short sentence overshoots; the guarantee is `>= 30 %`, not `== 30 %`.

At 30 % expansion, no locale scrolls sideways at either viewport
(`scrollWidth === clientWidth` for `documentElement`, `body` and `main` in all six
runs), and no element truncates instead of wrapping.

**Two runner notes, both measured rather than assumed:**

- React escapes `'` as `&#x27;` in text nodes, and French catalog entries contain
  apostrophes. Counting escaped bytes would inflate the *un-inflated* side of the
  ratio by however many apostrophes a sentence happens to have, which could
  manufacture a 1.30 ratio from a build that expanded nothing. The spec un-escapes
  before counting.
- A long-strings `next build` makes **Next.js itself** append
  `.next-longstrings/types/**/*.ts` and `.next-longstrings/dev/types/**/*.ts` to the
  `tsconfig.json` `include` array, printing *"We detected TypeScript in your project
  and reconfigured your tsconfig.json file for you."* Per **D-I18N-09** (ratified),
  these two include lines are now **committed** and the byte-freeze is amended to the
  new known-good SHA-256 `8e2f6721f36bb5e190accf7b210deb7b4f523d3f126e119611e41009fcbaf687`.
  `npm run typecheck` passes with or without those two lines (the existing `**/*.ts`
  include already covers the alternate tree), but they are now part of the committed
  freeze so the long-strings build no longer mutates the file. The previous reliance
  on an un-scripted `git checkout -- tsconfig.json` is removed.

### 5.3 Gate 21 after UI-01d - one real gap, closed

`sourceFiles()` in `tests-browser/hygiene.spec.ts` read only the **top level** of
`app/` and `components/`. That was complete while the routes lived directly in
`app/`; UI-01d moved them to `app/[locale]/`, and the walk was made recursive. The
failure mode was symmetric and worth stating, because both directions are a disabled
check:

- a raw palette utility in `app/[locale]/page.tsx` would have been reported as clean;
- a utility used **only** there (`leading-7`, in `not-found.tsx`) was reported as an
  emitted utility that no product source referenced.

After the fix, gate 21 passes with `emitted from a comment only: []`. Two comment
tokens had to be reworded rather than allow-listed, because the comment-naming rule
is stricter than the collateral list:

- `next.config.ts` said *"a static mapping does not need a request interceptor"* - now
  *"a redirect table declared here"*. `static` is a real Tailwind utility, so the
  prose was naming one.
- `components/workflow-timeline.tsx` said wrapping a numeral in `<bdi>` *"would blur
  the very distinction"* - now *"obscure"*.

Neither rewording weakened a rule; both were prose, and the packet's own remedy for a
utility named in a comment is to break the token in the prose. `COLLATERAL_EMITTED`
is unchanged at its seven original entries.

`app/globals.css` gained four `@source not` directives (`i18n/`, `messages/`,
`tests-browser/`, `tests-long-strings/`) on top of the existing `*.md` and `tests/`
exclusions (M6). This application has **no `tailwind.config.*`** - it is pure Tailwind
v4 CSS-first auto source detection, whose scanner reads every non-excluded file under
the app root as a candidate class-name source. Excluding the catalogs and the two
test trees is what keeps a translated string or an English assertion from compiling
into a real utility; the absence of those directives was what made `blur`, `ring` and
`static` emit in the first place.

### 5.4 OPEN: the unsupported-locale 404 cannot carry both correct raw `lang`/`dir` and name the refused segment

**This is escalated to the packet owner, not decided here.** Measured on Next 16.3.6
with temporary probes - not inferred:

| Requirement | What Next does |
| --- | --- |
| `app/[locale]/not-found.tsx` can read the refused segment | It receives **no props at all** - not an empty `params`, an absent one. Request headers carry no path either: only `host`, `user-agent`, `accept`, `x-forwarded-host`, `x-forwarded-port`, `x-forwarded-proto`, `x-forwarded-for` |
| HTTP status is `404` | `notFound()` does emit `404` |
| Raw pre-hydration `<html lang dir>` on the 404 | It emits `<html id="__next_error__">` with **no** `lang` and **no** `dir` |
| The refusal names `{requested}` | Rendered **instead of** `children` it gives full content and correct `lang`/`dir` - but the status becomes **`200`**. Rendered **alongside** `children` it keeps `404`, and the naming text is in the RSC payload but the served HTML is effectively only "Nexus Scholar" |

Three options exist and all three were rejected or deferred here, deliberately:

1. **`middleware.ts` rewrite** - rejected on the merits, same reasoning as the
   redirect: it adds a runtime layer and is framework-version-sensitive.
2. **A locale context/provider** - rejected: it reintroduces client locale state,
   which is exactly what D-I18N-01 forbids.
3. **Return `200` and label the page** - this *is* a soft 404. Rejected: it
   contradicts D-I18N-13's `404` requirement outright.

**D-I18N-13A ratification:** The refusal enumerates available locales but does **not**
echo the refused segment (D-I18N-13A). The raw 404 document's missing `lang`/`dir`
is a known Next.js 16.3.6 limitation that cannot be resolved without middleware
(rejected) or a custom server (out of scope). This limitation is honestly recorded
here rather than papered over. The `LocaleNotFound({ requested })` component
remains exported but unwired, with the naming UI implemented and commented.

**Test coverage is therefore split, on purpose:** N20 (`/de` is a valid page - one
`h1`, one `main`, the shell's landmarks) and the fallback-language half of N2 are
executable and pass after hydration; the raw pre-hydration `lang`/`dir` and the
naming sentence are recorded as **BLOCKED** above.

### 5.5 OPEN: case-insensitive static serving on Windows

Freshly measured on this machine, with a build from the current tree:

| Request | Status | Served |
| --- | --- | --- |
| `/EN` | **200** | `lang="en" dir="ltr"`, full English overview |
| `/Fr` | **200** | `lang="fr" dir="ltr"`, full French overview |
| `/DE` | 404 | `<html id="__next_error__">`; visible text only "Nexus Scholar"; the naming text is in the RSC payload |

Locale resolution in `i18n/locales.ts` is exact and case-sensitive, and
`generateStaticParams` returns only `en`, `fr`, `ar`. The case-folded request never
reaches either: Next has already matched `en.html`/`fr.html` on a case-insensitive
filesystem before the route function runs, so `notFound()` cannot see it. The
application therefore behaves as the contract requires *in the router* and cannot
behave as the contract requires *on this filesystem*.

This is a platform behaviour, not an application defect, and it is folded into the
same H8 escalation rather than worked around: every workaround (middleware, context,
normalisation) is one of the three mechanisms already rejected in 5.4.

### 5.6 Human review - NOT VERIFIED

These cannot be self-certified and are not claimed anywhere in this tree.

| # | Question | Reviewer | Status |
| --- | --- | --- | --- |
| H1 | Is the French wording idiomatic and free of anglicisms? | fluent French reader | **NOT VERIFIED** |
| H2 | Is the Arabic wording idiomatic **and** correct in register for a research tool? | fluent Arabic reader | **NOT VERIFIED** |
| H3 | Do the Arabic screenshots show a genuinely mirrored reading flow - correct skip-link corner, panel edge, lineage rail side, aligned ordinals? | image-capable reviewer | **NOT VERIFIED** |
| H4 | Are the Arabic 12px label sites legible after the D-I18N-08 size/tracking adaptation? | image-capable reviewer | **NOT VERIFIED** |
| H5 | Visual confirmation of the **already-ratified** D-I18N-02: translated chrome beside English fixture content | image-capable reviewer | **NOT VERIFIED** |
| H6 | **RQ-1** - ratify D-I18N-07: translating the *display label* while preserving canonical tokens as data | packet owner | **NOT VERIFIED** |
| H8 | **RQ-3** - ratify the two written scope-extension requests (`playwright.long-strings.config.ts`, `next.config.ts` + `.gitignore`), **and** rule on the two open items in 5.4 and 5.5 | packet owner | **NOT VERIFIED** |
| H9 | **Resolved** - the two include lines are committed and the byte-freeze amended to SHA-256 `8e2f6721f36bb5e190accf7b210deb7b4f523d3f126e119611e41009fcbaf687` per D-I18N-09 | packet owner | **VERIFIED** |

The mechanical half of D-I18N-02 *is* verified: the fixture is byte-identical
(SHA-256), every fixture run is `<bdi>`-isolated, and `375-overview-ar.png` and
`1440-overview-ar.png` demonstrate it. H5 is the visual/product confirmation of that
decision, which is a different question.

### 5.7 Test titles changed by this packet

Exactly two, both in `tests-browser/tab-order.spec.ts`, both **packet-sanctioned**
(13.1 lists rows 35, 40, 44, 53, 56 of that file as updated for M3/D-I18N-11), and
both because the measurement changed rather than because the assertion was relaxed:

| Was | Now |
| --- | --- |
| `375px: the desktop <nav> is display:none, so the ring is [skip, trigger]` | `... so the ring is [skip, trigger, three locales]` |
| `1440px: the mobile disclosure is display:none, so the ring is [skip, Overview]` | `... so the ring is [skip, Overview, three locales]` |

D-I18N-11 requires the selector at **both** viewports, which adds three stops at each
width. Both tests now assert the complete five-stop ring, in `en` and in `ar` - a
strictly stronger claim than the two stops they replaced. Every other original test
title in the seven pre-existing browser specs is byte-identical.

### 5.8 Scope notes

- `./I18N.md` is the deliverable path (D-I18N-01c). The untracked
  `../architecture/research_ui/` tree was **left exactly as found**: the FU-1 and
  index corrections named in D-I18N-01c are a working-tree-only correction **to the
  human operator**, explicitly not part of this packet's deliverable and explicitly not
  to be staged or committed.
- `.next-longstrings/` is the one `.gitignore` line this packet adds (H8). The
  long-strings runner's Playwright `outputDir` is nested inside the already-ignored
  `test-results/` rather than given a sibling `test-results-longstrings/`, precisely so
  that no second ignore rule is needed.

---

## 6. Packet UI-02 - the project-overview state model

This section records what packet UI-02 made executable. The packet's gate was
"populated, loading, empty, and error fixtures; component tests", and its negative
case was "counts are never inferred in the browser: an absent count renders unknown
rather than zero". Everything below was produced by a command in this directory on
this working tree.

### 6.1 Executable gates added by UI-02

| # | Gate | Covered by | Status |
|---|------|-----------|--------|
| U1 | The state model is a discriminated union: a phase is reachable only when `record === "ready"`, so no component can render a project state it never received | `lib/project-state.ts` + `npm run typecheck` | EXECUTABLE - `tsc --noEmit` exit 0 |
| U2 | Eleven fixtures (2 arrival + 9 phases); the nine phase words are pairwise distinct per locale and apart from the arrival words; the five statistic labels are distinct and apart from "unknown"; `phaseKey`/`countKey`/`phaseDescriptionKey` throw `UnmappedTokenError` for an undeclared token; catalog parity now at **74 keys × 3 locales** | `tests/project-state-record.test.tsx`, `tests/i18n-catalog.test.ts` | EXECUTABLE - 31 + 37 tests pass |
| U3 | Every fixture renders all five statistic rows; an absent field reads the translated `counts.unknown` and never `0`; every fixture count is one of the frozen corpus numbers (143/18) | `tests/project-state-record.test.tsx` | EXECUTABLE |
| U4 | A failed read renders neither a phase word nor the refusal word and no counts; a pending read the same; the refusal fixture renders the refusal word plus its `<bdi>`-isolated note, byte-identical in all three locales | `tests/project-state-record.test.tsx` | EXECUTABLE - per locale |
| U5 | The continuation surface renders translated text plus the "not yet available" tag, with **zero** links and zero focusable elements in the section; the section is one named region at heading level 2, adds no `listitem`, and the route's 6-stage + 5-evidence list counts and level-3 stage headings are unchanged | `tests/project-state-record.test.tsx`, `tests/home-page.test.tsx` | EXECUTABLE |
| U6 | Translation boundary: every rendered sentence outside `<bdi>` in `fr`/`ar` still comes from that locale's catalog (the substituted destination sentence is matched with its hole as a wildcard) | `tests/i18n-render.test.tsx` | EXECUTABLE - fr/ar scans return `[]` |
| U7 | Token discipline (gate 21) after the new files: no dangling token, no raw palette utility in source or shipped CSS, `emitted from a comment only: []` | `tests-browser/hygiene.spec.ts` | EXECUTABLE - part of the 59/59 run |
| U8 | Rendered axe zero real violations in `en`/`fr`/`ar` at 375px and 1440px, dialog open and closed; no horizontal overflow; no unbreakable token; tab ring unchanged at both widths | `tests-browser/rendered-axe.spec.ts`, `overflow.spec.ts`, `tab-order.spec.ts` | EXECUTABLE |
| U9 | The 30 % expansion gate still holds **with the 32 new strings inflated**: no sideways scroll in any locale at either width, no truncation instead of wrapping | `playwright.long-strings.config.ts` + `tests-long-strings/long-strings.spec.ts` | EXECUTABLE - 10/10, ratios `en 1.7167` / `fr 1.3884` / `ar 1.3409` |
| U10 | Committed screenshots regenerated against the new section (8 of 10 changed; the evidence-trail and mobile-dialog shots are unaffected) | `tests-browser/screenshots.spec.ts` | EXECUTABLE - all ten rewritten and verified as PNG |

**Design note (review finding F5):** the read-failure stamp deliberately shares the
refusal hue (`text-refusal`). The palette has four semantic hues and its oxide tone
is the palette's *negative/failure* role — reusing the ochre `warning` (the
waiting-state tone) for a failed read would mislabel it as pending, which is the
confusion the packet exists to prevent. The distinction the packet claims is carried
by the word and by the absence of any phase/count, both asserted per locale in
`tests/project-state-record.test.tsx`; the hue marks severity only, and this row is
what makes that choice evidence rather than accident.

### 6.2 Measured totals

- `npm run typecheck`: exit 0.
- `npm test`: **179 passed / 179**, 11 files (was 144/10 before UI-02: +35 tests,
  +1 file — 31 in `tests/project-state-record.test.tsx`, +4 vocabulary/distinctness
  tests in `tests/i18n-catalog.test.ts`).
- `npm run build`: 5 prerendered outputs — `/_not-found`, `/[locale]` (the route
  definition), and `/en`, `/fr`, `/ar`.
- `npm run test:browser`: **59 passed / 59**, 10 files.
- Long-strings suite: **10 passed / 10**.

### 6.3 Existing assertions this packet deliberately changed

Two, both because the measurement changed rather than because an assertion was
relaxed (the UI-01d §5.7 rule):

| Was | Now | Why |
| --- | --- | --- |
| `i18n-catalog.test.ts`: "exactly the 42 keys" → length 42 | length **74** | 32 keys added by this packet |
| `i18n-render.test.tsx`: `getByText(formatNumber("ar", 143))` | `getAllByText(...).length > 0` | 143 now renders twice on the route (timeline stage 1 and the record's "records discovered" row); the claim "Arabic-Indic digits are rendered" is unchanged |

`i18n-catalog.test.ts` also gained the `{destination}` interpolation value in its
fixed-values loop — the new `overview.nextDestination` hole would otherwise throw
`MissingMessageError` under test, which is the failure mode that hole exists to
prevent.

### 6.4 Not closed by this packet

- **H1–H5 carry over unchanged**: the 32 new `fr`/`ar` strings are demonstration
  translations like the rest of the catalog (`I18N.md` §9), not fluently reviewed.
- The `../architecture/research_ui/` tree is **tracked since `0fe5315`** (so the
  "untracked" adjective in §5.8's older scope note is itself stale) and was **left
  exactly as found**: this packet changed nothing under it, and the tree is clean
  there in `git status`.

## 7. Packet UI-03 - the workflow timeline's second channel

This section records what packet UI-03 made executable. The packet's deliverable
was the stage sequence showing `complete`, `active`, `waiting` and `refused`
"with text and icons, not color alone"; its negative cases were "no claim that a
future stage is complete" and "refused is distinct from failed infrastructure";
its gate was a "state matrix test and narrow-width visual check". Everything
below was produced by a command in this directory on this working tree. The
packet's design decisions, stable-input list and repair-delta table live in
`docs/UI-03_CONTEXT_CAPSULE.md`.

### 7.1 Executable gates added by UI-03

| # | Gate | Covered by | Status |
|---|------|-----------|--------|
| W1 | **State matrix — four states × three locales.** Inside each stage's own `<li>`: exactly one `svg[data-stage-state-icon]` naming that row's state, `aria-hidden="true"`, with no `role`, no `aria-label`, no `aria-labelledby`, no `<title>` and no text of its own; the stamp word equals `CATALOGS[locale]["state.<state>"]`, and no *other* state's word appears in that row. The declaration is also pinned **as bytes in the component's own JSX** (`<StateIcon ... />` must contain `aria-hidden="true"`) | `tests/workflow-timeline-state-matrix.test.tsx` | EXECUTABLE — 3 locale tests + 1 source pin |
| W2 | The four rendered icon markups are mutually distinct — asserted once as rendered and once **with the `data-stage-state-icon` token stripped**, so the distinctness is in the drawn shape and not in an attribute no reader can see (Set size 4 both times) | same file | EXECUTABLE |
| W3 | **Negative case 1 — no future stage claims complete.** Component fidelity: a hostile input order `waiting, refused, complete, active` renders each row's icon token and stamp word *exactly* as given, in all three locales, with no other state word in the row. The component never promotes, sorts or infers a state | same file | EXECUTABLE — 3 tests |
| W4 | Demo-fixture integrity: in `lib/mock-project.ts` no `complete` stage follows a non-`complete` stage, with non-vacuity guards on both sides so an all-complete or all-active fixture cannot pass it | same file | EXECUTABLE |
| W5 | **Negative case 2 — refused ≠ failed infrastructure.** The error-ish keys are *discovered* from `messages/en.ts` by key pattern (today `overview.recordError` and `overview.recordErrorLabel`), never enumerated; per locale the refused stamp is not spelled as any of their values, and the rendered refused row contains neither a full error value nor any ≥5-letter word from one. The words come from that locale's own catalog, so French and Arabic are checked in French and Arabic rather than against an English pattern that would match nothing there | same file | EXECUTABLE — 3 tests + 1 discovery non-vacuity |
| W6 | **No second state→colour definition (D2/N4).** The timeline source carries no `Record<WorkflowState, string>` and no state-hue colour utility (in code or quoted in prose); the four rendered icons share **one** class string whose only colour class is `text-ink-muted` | same file | EXECUTABLE |
| W7 | No new focusable element and no role/accessible-name change: the list keeps its accessible name and its `listitem` count, and the icon carries no `tabindex` | same file | EXECUTABLE |
| W8 | **Narrow-width visual check at 375px, `en` and `ar`.** The shared overflow recipe runs first (page must not scroll sideways), then for every demo stage row: one icon, a canonical state token, a stamp word from that locale's catalog, and — after `scrollIntoViewIfNeeded` — the icon, the stamp cell and the stamp each fully inside the viewport in **both** axes. Measured: `en` stamp cell `x 108.0..351.0`, `ar` stamp cell `x 24.0..267.0`, against a 375px viewport; icon `x 108.0..124.0` (en) / `251.0..267.0` (ar) | `tests-browser/workflow-timeline-narrow.spec.ts`, `tests-browser/overflow-recipe.ts` | EXECUTABLE — 2 tests |
| W9 | Gate 21 after the new comments and the second `@heroicons/react/24/outline` import: `emitted from a comment only: []`, `emitted with no source anywhere: []`, `raw-palette utilities: []`, `shipped CSS retired tokens/hexes: []` | `tests-browser/hygiene.spec.ts` | EXECUTABLE — part of the 61/61 run |
| W10 | Zero axe violations at 375px and 1440px in all three locales (dialog closed) and at 375px open; the tab ring is byte-for-byte the one UI-01d recorded; the catalog is still exactly **74 keys × 3 locales** | `tests-browser/rendered-axe.spec.ts`, `tests-browser/tab-order.spec.ts`, `tests/i18n-catalog.test.ts` | EXECUTABLE |
| W11 | The 30 % expansion gate still holds **with the icons in place**: no sideways scroll in any locale at either width and no truncation | `playwright.long-strings.config.ts` + `tests-long-strings/long-strings.spec.ts` | EXECUTABLE — 10/10, ratios `en 1.7167` / `fr 1.3884` / `ar 1.3409` |
| W12 | Committed screenshots regenerated against the icon change (**7 of 10 changed**; see 7.4) | `tests-browser/screenshots.spec.ts` | EXECUTABLE — all ten rewritten and verified as PNG |

Gate 1 in §1 still stands unchanged: `lib/mock-project.ts` never uses `refused`,
which is why W1/W3/W5 drive the component directly by prop, and why the `refused`
row on screen comes from the presentation fixture rather than from the demo
record.

### 7.2 Measured totals

- `npm run typecheck`: exit 0.
- `npm test`: **195 passed / 195**, 12 files (was 179/11 before UI-03: +16 tests,
  +1 file — the whole of `tests/workflow-timeline-state-matrix.test.tsx`).
- `npm run build`: exit 0, 5 prerendered outputs — `/_not-found`, `/[locale]`
  (the route definition), and `/en`, `/fr`, `/ar`.
- `npm run test:browser`: **61 passed / 61**, 11 files (was 59/10: +2 tests,
  +1 file — the two narrow-width checks in
  `tests-browser/workflow-timeline-narrow.spec.ts`).
- Long-strings suite: **10 passed / 10**.
- Gate 21 detail from the same run: `emitted class selectors: 150, used: 143`,
  the 7 unused being exactly the `COLLATERAL_EMITTED` prose allow-list
  (`collapse`, `contents`, `ordinal`, `rounded`, `shadow`, `table`, `visible`),
  `allow-listed but no longer emitted: []`,
  `emitted with no source anywhere: []`, `emitted from a comment only: []`.

**Mutation checks — the guards were made to fail before they were believed.**
Re-executed for repair-cycle-1 (F2) against the *current* bytes of
`tests/workflow-timeline-state-matrix.test.tsx`, SHA-256
`66C96A746476FA3E4DFF996015EB4093F81CB030CD04575BEA2F88DDD7FC57F3`, which holds
**16 executed tests** (10 source `it(` blocks, three of them inside a
three-locale loop; 7 singletons + 3×3 = 16). Command for every run, from
`apps/research-ui/`:
`npx vitest run tests/workflow-timeline-state-matrix.test.tsx`. Between runs the
component was mutated, then restored from a copy taken before the first
mutation.

| # | Mutation | Verbatim vitest summary | Exit | What it proved |
| --- | --- | --- | --- | --- |
| a | delete `aria-hidden="true"` from the `<StateIcon>` JSX | `❯ tests/workflow-timeline-state-matrix.test.tsx (16 tests \| 1 failed) 407ms` → `Test Files  1 failed (1)` → `Tests  1 failed \| 15 passed (16)` (`Start at  21:49:59`), failing test `pins the icon's props in our own JSX, not only in the library default (A1)` at `:256` | 1 | The prop is load-bearing in the suite: `@heroicons/react` 2.2.0 ships `"aria-hidden": "true"` as its own svg default, so a DOM-only assertion stays green with the prop deleted — hence the source pin |
| — | restore from the pre-mutation copy | `FINAL COMPONENT SHA-256 = 12B42053D31A566BDD6493E4FDE2474BC1F8D2B6B6C5D696EC6E744B7D586498` … `IDENTICAL: yes` | 0 | byte-identity with the pre-mutation file |
| c | `refused: NoSymbolIcon` → `refused: ClockIcon` in `stateIcon` | `❯ tests/workflow-timeline-state-matrix.test.tsx (16 tests \| 1 failed) 558ms` → `Test Files  1 failed (1)` → `Tests  1 failed \| 15 passed (16)` (`Start at  21:50:20`), failing test `renders four mutually distinct icon markups`, `AssertionError: expected 3 to be 4` at `:181` | 1 | The stripped-markup distinctness claim is real: two states would have been drawn identically, and only a `data-<token>` no reader can see would have separated them |
| — | restore from the pre-mutation copy | `FINAL COMPONENT SHA-256 = 12B42053D31A566BDD6493E4FDE2474BC1F8D2B6B6C5D696EC6E744B7D586498` … `IDENTICAL: yes` | 0 | byte-identity with the pre-mutation file |
| e | clean run, no mutation | `Test Files  1 passed (1)` → `Tests  16 passed (16)` (`Start at  21:50:44`) | 0 | the restored file is green |

Why the numbers changed at repair-cycle-1: this section previously recorded
`16 passed`, `1 failed / 15 passed` and `1 failed / 14 passed`, which implies
suite sizes of 16, 16 and 15 for one file. The first of those runs happened
**before** the source-pin test existed, when the file held 15 tests — it was
miscopied as 16, and the third run was against that same 15-test suite. All
three runs above were re-executed against the current 16-test file, so every
suite size here is 16 and each number is quoted from the run that produced it.

Component byte-identity: SHA-256 `12B42053D31A566BDD6493E4FDE2474BC1F8D2B6B6C5D696EC6E744B7D586498`
before the first mutation, after each of the two restores, and after the last;
the full battery was re-run against the restored file.

### 7.3 Existing assertions this packet deliberately changed

**None.** Every pre-existing test file is byte-identical after this packet —
`tests/workflow-timeline.test.tsx`, `tests/status-badge.test.tsx`,
`tests/i18n-catalog.test.ts`, `tests/home-page.test.tsx` and
`tests-browser/tab-order.spec.ts` were read, not edited. The measurement that
moved is recorded here rather than hidden inside a diff:

| Was | Now | Why |
| --- | --- | --- |
| `ALL_STATES_STAGES` held 4 stages; tests iterating it saw 4 | 5 stages; the same generic assertions see 5 | the fixture's own doc-comment claimed it exercised "every `WorkflowState`, including `refused`" while listing none — repaired (A5), so the assertion's *input* changed, not its claim |
| Route screenshots: 7 of 10 PNGs | same 10 files, 7 rewritten | the overview-bearing captures gain the icon column; regeneration is `screenshots.spec.ts`'s job, not a hand edit |

### 7.4 Design notes and scope

- **Icon set, and the D-I18N-09 record.** `complete → CheckCircleIcon`,
  `active → ArrowPathIcon`, `waiting → ClockIcon`, `refused → NoSymbolIcon`, all
  from `@heroicons/react/24/outline` (already a pinned dependency; `package.json`
  and `package-lock.json` untouched). **All four are chosen as direction-neutral
  and none is mirrored** — no `rtl:scale-x-*`, no transform of any kind.
  `ArrowPathIcon` is however arrow-like, and that is D-I18N-09's named trigger:
  "If a future genuinely directional icon (chevron, arrow) appears, mirroring is
  an explicit per-icon decision recorded in the packet that adds it." That
  decision is made here, and it is *not* to mirror — the glyph draws a cycle (a
  path traversed repeatedly), not a directional arrow. `AGENT_WORK_PACKETS.md` is
  not an editable path for this packet, so the record lives in
  `docs/UI-03_CONTEXT_CAPSULE.md` §"Design decisions" and in this row.
- **One neutral tone, not a second palette (D2).** All four icons render the
  identical class string, whose only colour class is `text-ink-muted`. The icon
  channel is shape; `components/status-badge.tsx` remains the application's
  **only** definition of state colour, and W6 asserts that from both ends (the
  source bytes and the rendered class list). The stamp keeps its dot, its hue
  and its word: the icon accompanies the assertion (P3), it never replaces it,
  and `VISUAL_DIRECTION.md` §5's dot anatomy and §9's M3 claim are untouched.
- **Refused-fixture repair (A5).** `ALL_STATES_STAGES` gained a fifth row
  (`fixture-e`, `refused`) so its doc-comment became true. The row is
  presentation prose only: no DOI, identifier, refusal code or verdict, the
  sequence's states only ever degrade along it, and the file's disclaimer stays
  honest (the stage's state is the step's own condition, not a decision about any
  record).
- **Scope notes.** (a) `uv run python scripts/select_test_gate.py --path
  apps/research-ui/components/workflow-timeline.tsx --stage inner` exits 2 with
  "no task selected" — the E3 manifest maps no task to UI paths, so the governing
  gate for this packet is its own Gate line plus the commands in
  `docs/UI-03_CONTEXT_CAPSULE.md` §Validation, not a `test_gate_manifest.json`
  row. (b) No new strings, no new i18n keys, no route change and no API: the four
  `state.*` words already exist in `en`/`fr`/`ar`. (c) `components/status-badge.tsx`
  and `lib/contracts.ts` were read only.
- **`refused` at 375px — an explicit limit of A6.** The route renders
  `lib/mock-project.ts`, which is byte-frozen and never uses `refused`, so the
  narrow-width gate measures the six demo rows (`complete`×4, `active`,
  `waiting`). The `refused` row travels the same grid cell and the same markup
  path, and its icon and stamp are asserted per locale in W1/W5; what is *not*
  claimed is a 375px pixel measurement of a refused row, because producing one
  would require editing a byte-pinned fixture.
- **Screenshots: 7 changed, 3 did not.** Rewritten: `375-overview.png`,
  `375-overview-fr.png`, `375-overview-ar.png`, `375-mobile-ar.png`,
  `1440-overview.png`, `1440-overview-ar.png`, `1440-skiplink-focused.png` —
  every capture whose frame contains the workflow section. Unchanged:
  `1440-evidence-trail.png` (scoped to the evidence section),
  `375-skiplink-focused.png` and `375-mobile-nav-open.png` (375px frames taken
  at the top of the page, where the workflow is below the fold).
- **Doc gap, flagged not repaired.** `apps/research-ui/AGENTS.md` rule 1 and the
  packet document's small-agent prompt both point at
  `docs/architecture/research_ui/README.md`, which **does not exist** (the tree
  holds `AGENT_WORK_PACKETS.md`, `GATES.md`, `I18N.md`, `UI-01C_WORK_PACKET.md`,
  `UI-01D_WORK_PACKET.md`, `UI-02_CONTEXT_CAPSULE.md`, `VISUAL_DIRECTION.md`).
  Creating it is outside this packet's allowed paths, so it is open documentation
  debt, recorded here and in the UI-03 capsule.

### 7.5 Not closed by this packet

- **Human visual review of the regenerated screenshots is NOT VERIFIED** — the
  same standing condition as `I18N.md` §9 / §5.6: automated assertions cover
  presence, position and non-clipping, not whether a shape reads well at 11px.
  The four icons should be eyeballed in `375-overview.png` and
  `375-overview-ar.png` by a reviewer with an image-capable pass.
- H1–H5 (unreviewed demonstration translations) carry over unchanged; this
  packet added no catalog text at all.
- The refused-row 375px measurement described in §7.4 stays open until a fixture
  that may carry `refused` on the route exists.

### 7.6 Acceptance map (A1–A9)

The packet's acceptance criteria, each with the code and the executable check
that carries it. Line numbers are from this working tree.

| A | Criterion | Verdict | Evidence (file:line) | Executable check |
| --- | --- | --- | --- | --- |
| A1 | Icon rendered per stage exactly as designed: `aria-hidden`, `data-stage-state-icon` = the state token, one neutral class token, no new focusable element; `StatusBadge` and the count logic unchanged | **PASS** | `components/workflow-timeline.tsx:67-72` (shape map), `:123-128` (icon as first child of the stamp cell); `tests/workflow-timeline-state-matrix.test.tsx:124`, `:227`, `:244`; `tests/workflow-timeline.test.tsx` and `tests/status-badge.test.tsx` byte-identical (absent from `git status`) | `npm test` → 195/195; mutation: deleting the prop now fails at `:244` |
| A2 | Stamp word = `CATALOGS[locale]["state.<state>"]` for every state × locale, present and unchanged; existing assertions still hold | **PASS** | `tests/workflow-timeline-state-matrix.test.tsx:124` (word + no-other-state-word, en/fr/ar), `:262`; catalogs untouched | `npm test` → 195/195 |
| A3 | Negative case 1: **no claim that a future stage is complete.** (a) the component renders the state it is given under a hostile order; (b) the demo fixture never marks a stage complete after one stopped being complete | **PASS** | (a) `:262` order `waiting, refused, complete, active` × 3 locales; (b) `:293` with non-vacuity guards on both sides | `npm test` |
| A4 | Negative case 2: **`refused` is distinct from failed infrastructure** — no error/failure wording in the rendered refused row, checked per locale from the locale's own catalog, with a non-vacuity guard on key discovery | **PASS** | `:312` (discovery, today `overview.recordError`/`overview.recordErrorLabel`), `:322` (×3 locales) | `npm test` |
| A5 | The presentation fixture actually carries a `refused` stage so A4 can render one (its doc-comment claimed to) | **PASS** | `tests/fixtures/presentation-fixture.ts:17`, `:32` (`fixture-e`); sequence still monotone | `npm test` |
| A6 | Narrow-width visual check: at 375px (`en`, `ar`) every rendered stage row shows its icon and stamp fully inside the viewport | **PASS** | `tests-browser/workflow-timeline-narrow.spec.ts:53`; measured boxes in §7.1 W8 (`en` stamp cell `108.0..351.0`, `ar` `24.0..267.0` vs 375px) | `npm run test:browser` → 61/61 |
| A7 | Only the PNGs that actually changed are modified | **PASS** | 7 of 10 in `git status`: `375-overview{,-fr,-ar}.png`, `375-mobile-ar.png`, `1440-overview{,-ar}.png`, `1440-skiplink-focused.png`; the other 3 byte-identical | `git status --short` |
| A8 | `docs/GATES.md` §7 and `docs/UI-03_CONTEXT_CAPSULE.md` record the measured gates, totals, changed assertions, design decisions (incl. the D-I18N-09 icon record) and open items | **PASS** | `docs/GATES.md:1561` ff.; `docs/UI-03_CONTEXT_CAPSULE.md` (Task, Boundary, Design decisions, Repair delta) | read-back above |
| A9 | Nothing else moves: catalog still 74 keys × 3 locales, tab ring unchanged, zero axe violations, no forbidden path touched | **PASS** | `tests/i18n-catalog.test.ts` (in 195/195), `tests-browser/tab-order.spec.ts` (in 61/61), axe specs (in 61/61), `git status --short` scope check in §7.4 | `npm test`, `npm run test:browser`, `git status --short` |

Packet-level negative cases map to A3 and A4; the packet's Gate line
("state matrix test and narrow-width visual check") maps to A1–A5 plus A6.
