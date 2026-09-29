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
| 19 | The emitted CSS carries `--color-surface: #f8fafc` and `--color-ink: #172033`, the two pre-UI-01 raw-hex values **quoted in §1.2** so the comparison has a target in the tree, and no colour token was removed. Gate 19 makes **no** claim about the declarations UI-01 added, one of which (`color-scheme: light`) does change rendered behaviour | `npm run build` + inspection of the emitted CSS | EXECUTABLE (see §1.2) |

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

**23 tests: 23 pass.** UI-00b's first run reported 20 pass and 2 fail, both on
`color-contrast`; the contrast repair in §3.2 closed both, and the run now exits
0. Every number below is copied from a run's own `[measured]` output; nothing
here is inferred.

**The count is 23, and the arithmetic is auditable** — it is the sum of the
`playwright test --list` output, and only the axe spec changed:

| Spec file | Tests | Why |
|---|---:|---|
| `tests-browser/focus-visibility.spec.ts` | 3 | unchanged |
| `tests-browser/hygiene.spec.ts` | 3 | unchanged |
| `tests-browser/overflow.spec.ts` | 3 | 2 from the viewport loop + 1 standalone |
| `tests-browser/rendered-axe.spec.ts` | **4** | 2 from the viewport loop + the `image-alt` negative control + **the §3.6 dialog-open run** |
| `tests-browser/responsive-nav.spec.ts` | 3 | unchanged |
| `tests-browser/screenshots.spec.ts` | 5 | unchanged |
| `tests-browser/tab-order.spec.ts` | 2 | unchanged |
| **Total (7 files)** | **23** | was 22; +1, from `rendered-axe.spec.ts` alone |

No other spec file gained or lost a test, and no existing test was restructured
to make room: the new one is a fourth `test()` in the existing
`test.describe("axe-core on rendered CSS", …)`.

### 3.1 CLOSED by UI-00b

| # | Previously deferred item | Measured | Covered by |
|---|---|---|---|
| B1 | Real per-viewport tab order | 375px: `["a:Skip to main content","button:Open main navigation"]`. 1440px: `["a:Skip to main content","a:Overview"]` | `tests-browser/tab-order.spec.ts` |
| B2 | Tailwind's `lg:` breakpoint behaviour | 375px: `<nav aria-label="Primary">` hidden, trigger visible. 1440px: the exact reverse | `tests-browser/responsive-nav.spec.ts` |
| B3 | Rendered focus, skip link | `:focus-visible` true; `outline: 2px solid rgb(29, 78, 216)`, `outline-offset: 2px`, `position: fixed`; `clip-path` `inset(50%)` -> `none`; box 1x1 -> 169.69x40, inside the viewport. Same at both widths | `tests-browser/focus-visibility.spec.ts` |
| B4 | Rendered focus, primary-nav link and mobile trigger | Both `:focus-visible` true with the **application** ring `outline: 2px solid rgb(29, 78, 216)`, `outline-offset: 2px` — identical to the skip link's own ring. (At UI-00b's first run these two fell through to the user-agent `outline: 1px auto rgb(16, 16, 16)`, `outline-offset: 3px`; see §3.2 D1) | same |
| B5 | Screenshots of a route | 5 committed captures, 11,125-108,911 bytes each, PNG magic verified, `deviceScaleFactor: 1`, animations and caret off | `tests-browser/screenshots.spec.ts`, `screenshots/` |
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
`inert` (1 node) and `aria-hidden` (6 nodes); `tests/shell.test.tsx` asserts
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

#### 3.2.3 Residual, disclosed rather than closed

Three `text-slate-500` sites were already passing, were not in scope, and were
not changed — but they are the tightest margins left on the page and are
recorded so a future edit to them re-measures rather than assumes headroom:

| Site | Size | Foreground / background | Measured | Required |
|---|---|---|---|---|
| "Latest: …", `app/page.tsx:13` | 14px | `#62748e` on `#f8fafc` | **4.55:1** | 4.5:1 |
| "Research integrity you can inspect", `components/app-shell.tsx:51` | 12px | `#62748e` on `#ffffff` | **4.76:1** | 4.5:1 |
| "Read-only demonstrator…", `components/app-shell.tsx:77` | 12px | `#62748e` on `#ffffff` | **4.76:1** | 4.5:1 |

`4.55:1` is 0.05 above the threshold and `4.76:1` is 0.26 above it. They are
passes, not violations, and they are called out here precisely because they
would not survive an unnoticed edit to the `text-slate-500` token or to either
of the two backgrounds above.

Two corrections to this table, both found on review of the record rather than in
the code, since a gate record that miscounts its own residual-risk table is not
a trustworthy baseline. The `app-shell.tsx:51` row was missing entirely, so the
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

- [ ] **Automated visual-regression baselines.** Not started. `screenshots/`
      holds real captures and nothing compares two runs against each other, so
      a future visual regression would not be caught automatically.
- [ ] **A second route.** §4.3, unchanged by UI-00b. Still only `/`, so the
      layout-owned `main` is tested but not yet *exercised twice*.
- [ ] **Cross-browser rendering.** Chromium only. Firefox and WebKit are not
      installed and were not run, so no gate here may be read as
      engine-independent.
- [ ] **UI-03's narrow-width visual check**, in the sense the packet means it.
      UI-00b supplies narrow-width evidence for `/` only. The loading, empty and
      error states that clause is really about do not exist yet, so the item
      cannot be closed by this packet.

### 3.4 Runner note: `next start` under `output: "standalone"`

`next.config.ts` sets `output: "standalone"`, and `next start` prints:

```text
"next start" does not work with "output: standalone" configuration. Use "node .next/standalone/server.js" instead.
```

It then serves correctly anyway: all 23 tests ran against real rendered markup
at both viewports, and the measured values in §3.1 are consistent with the
source. The warning is recorded rather than silenced and the alternative was
not adopted, because switching the harness to `.next/standalone/server.js` would
change what is under test without a reason any gate requires. Next.js
**16.3.6**, Chromium build 1243.

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
