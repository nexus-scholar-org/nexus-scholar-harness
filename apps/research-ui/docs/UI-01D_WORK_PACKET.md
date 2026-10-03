# UI-01d — Internationalization and bidirectional foundation: work packet

**Status:** packet only. No UI-01d code has been written. This file is the
implementation contract for the next agent.

**Governing specification:**
`../architecture/research_ui/AGENT_WORK_PACKETS.md` § UI-01d (lines 125–244),
read together with `apps/research-ui/AGENTS.md` and the structural/rigour
precedent of `./UI-01C_WORK_PACKET.md`.

**Branch / base (verified):** `feat/ui-01d-i18n-rtl`, HEAD `8ba4fb6`
("Merge pull request #57 from nexus-scholar/feat/ui-01c-visual-direction").

**Verified baselines to preserve (recorded, not re-measured by this packet):**

| Gate | Baseline | Source |
| --- | --- | --- |
| `npm test` (Vitest) | 7 files / 53 tests | task instruction |
| `npm run test:browser` (Playwright) | 7 specs / 25 tests | task instruction |

No regression means: Vitest is `>= 7 files / >= 53 tests` with zero failures,
Playwright is `>= 7 specs / >= 25 tests` with zero failures, and no pre-existing
assertion is deleted or weakened without an individual justification recorded in
§12.

---

## 1. Objective

Make the existing shell + overview locale-aware across `en`, `fr`, `ar`:

1. Canonical locale routing where the URL is the only source of locale truth.
2. `<html lang>` and `<html dir>` correct **before hydration**, server-rendered.
3. Structurally identical typed message catalogs for all three locales, with the
   interface split into catalogued chrome vs byte-preserved authoritative/fixture
   content.
4. A keyboard/AT-usable, flagless language selector whose selection is URL
   persistent.
5. Logical-property direction handling, plus Arabic-script typography
   adaptation, with no physical-property patches.
6. `Intl`-based number formatting, with locale-sensitive values never used as
   canonical identifiers.
7. Machine-checkable gates, plus an explicit **human** sign-off that agents cannot
   self-certify.

## 2. Non-goals (hard stops)

- Do **not** implement or partially implement this packet's design while writing
  it. Read it, then implement.
- Do not touch Python, `src/`, `contracts/`, `tools/`, `.agents/`, `workspaces/`,
  `.agents/plugins/`, or any E3 document.
- Do not translate fixture or authoritative content (§4.3).
- Do not add an i18n dependency; `package.json` and `package-lock.json` stay
  byte-identical (§5.2).
- No machine-translation service, no render-time `fetch`, no `localStorage`
  locale, no `Accept-Language`/`navigator.language` negotiation in this packet.
- Do not internationalize screens UI-02…UI-06 have not created.
- Do not edit `../architecture/research_ui/AGENT_WORK_PACKETS.md` in this
  packet (see D-I18N-01c).

---

## 3. Numbered decisions

Each decision is normative. Where the governing packet is ambiguous, the decision
records the interpretation **and** raises a reviewer question (§16). Two decisions
(D-I18N-01, D-I18N-02) are **ratified rather than open** and carry their
ratification record in §3.1; only genuinely open interpretations raise a
question, and raising one for an already-settled decision is a defect, not
diligence.

### D-I18N-01 — Locale source of truth is the URL segment only — **RATIFIED**

`/en`, `/fr`, `/ar` are the only supported routes. `localStorage`, cookies,
`Accept-Language` and `navigator.language` are **not** consulted. `GET /` is a
temporary redirect to `/en`. Rationale: governing packet lines 165–166 ("must be
explicit and testable; it must not depend only on mutable browser state") and
negative case line 201.

### D-I18N-01a — Root layout is the locale layout

`app/layout.tsx` and `app/page.tsx` are **deleted**. Their content moves to
`app/[locale]/layout.tsx` and `components/overview-page.tsx`. The dynamic
segment layout is the topmost layout, which is the only position in the App
Router that can emit `<html lang dir>`. `components/locale-document.tsx` is a
**synchronous** server component that renders `<html>`/`<body>` and is composed
by `app/[locale]/layout.tsx`; the split exists because Next 16 `params` is a
`Promise`, so the layout must be `async`, while the vitest suites render the
document synchronously.

> **Hard gate.** If `next@16` refuses a root layout at a dynamic segment, or
> fails to render `<html lang dir>` server-side, stop and report
> `BLOCKED_UPSTREAM_ROUTING`. Do **not** fall back to a client-side
> `document.documentElement.lang = …` effect, and do not accept `lang="en"` as a
> constant. Acceptance criterion AC-2 is non-negotiable.

### D-I18N-01b — `/` redirect is `next.config.ts` `redirects()`, not middleware

`next.config.ts` gains `redirects()`: `{ source: "/", destination: "/en",
permanent: false }` (307). Rationale: static, framework-version-independent,
runs before filesystem routing, needs no `proxy.ts`/`middleware.ts` file, and is
assertable in a browser gate. `permanent: false` because 308 is user-agent
cached and the default locale must stay changeable. Existing `output:
"standalone"` is preserved.

### D-I18N-01c — `I18N.md` lands in `apps/research-ui/`, not `docs/`

D-I18N-01 (ratified): the deliverable is `./I18N.md`. The
governing packet's allowed-paths list (line 154) names
`../architecture/research_ui/I18N.md`, which sits in a currently **untracked**
tree (`git ls-files ../architecture/research_ui/` → 0 files; `git status`
reports `?? ../architecture/research_ui/`), so a file there would be invisible
to the PR. This is a deliberate, recorded divergence from line 154. A separate
**working-tree-only** correction to `../architecture/research_ui/AGENT_WORK_PACKETS.md`
(FU-1 plus the `I18N.md` path) is authorized to the human operator, but:

- it is **not** part of this packet's deliverable,
- it must **not** be staged, committed, or included in the PR,
- the untracked `../architecture/research_ui/` tree must be left exactly as
  found.

### D-I18N-02 — `lib/mock-project.ts` is byte-identical — **RATIFIED**

The fixture is authoritative-shaped content. It is **not translated**. Every
rendered fixture value is wrapped in `<bdi>` (an explicit `dir="auto"` is the
only acceptable equivalent, and only where a `textContent`-joined assertion
forces it). The Arabic screen therefore shows **translated chrome beside
English fixture content**. That is the required, visible consequence and must be
demonstrated in the `ar` screenshots and documented in `I18N.md` §"Translation
boundary". Enforced mechanically by §5.1's SHA-256 pin.

#### 3.1 Ratification record — D-I18N-01 and D-I18N-02

These two are **decided, not open**. The UI-01d review round 1 returned
`CHANGES_REQUESTED` and directed that they be recorded here as ratified rather
than re-opened, because both restate governing text verbatim and introduce no
new design; re-asking them would re-open a settled question and waste a review
round. H5 (§16) survives only as a *visual/product* judgement on how
already-ratified D-I18N-02 renders, not as the open question.

| Field | Value |
|---|---|
| **Decided by** | The **human packet owner** through the UI-01d governing packet itself (`../architecture/research_ui/AGENT_WORK_PACKETS.md` §UI-01d) and the standing architecture policy in `../architecture/research_ui/README.md` §"Internationalization policy" (lines 64–75). Not an implementer and not a subagent of this packet. |
| **Recorded** | **2026-10-03**, in §3.1 of this packet. Round 1 of the UI-01d review (`CHANGES_REQUESTED`) is the event that required the record; the ratification itself predates this packet and is not re-decided here. |
| **Review date** | The UI-01d governing packet carries no in-repo date, so this row records the date the decision was *written down*, following the `GATES.md` §3.7.5 convention. It does **not** claim a date for the decision. |
| **Scope** | D-I18N-01 ratifies **only** the URL-as-source-of-truth rule and the `GET /` → `/en` 307. D-I18N-02 ratifies **only** the non-translation of fixture/authoritative content and its visible consequence. Neither is a standing waiver of any negative case, and neither authorises editing `lib/mock-project.ts` (it stays byte-frozen by §5.1). |
| **Condition — D-I18N-01** | Ratified **only on condition that the locale is observable from the served bytes**. N1, N13 and AC-2's raw-response-body `fetch` check are that condition; without them the URL would be the *nominal* source of truth and nothing would prove it. |
| **Condition — D-I18N-02** | Ratified **only on condition that the demonstration-translation caveat is carried, not merely recorded** (§18 item 1b): `I18N.md` and the `fr`/`ar` screenshots must both show it, because `README.md` line 73 requires non-English catalogs to be marked as demonstration translations and a caveat that exists only in a decision table is not a mark. |
| **What is still open** | D-I18N-01c (`I18N.md` path divergence) is **not** ratified here — it is escalated through H8 with the same written scope-extension mechanism. |

### D-I18N-03 — Catalogues are typed and structurally identical, hand-rolled

`messages/en.ts` is the structural source of truth:

```ts
// messages/en.ts
export const en = {
  "app.meta.description": "Traceable systematic-review workflows for research teams.",
  // … 41 keys
} as const;
```

`messages/fr.ts` and `messages/ar.ts` are declared as
`const fr: Record<MessageKey, string> = { … }` where
`MessageKey = keyof typeof en`. A missing key **or an extra key** in `fr`/`ar` is
a `tsc` error. No third-party library (D-I18N-04).

### D-I18N-04 — No new dependency

`package.json` (SHA-256 `5687ea5b…f449`) and `package-lock.json`
(`bcdd05a0…36e7`) must not change. Governing packet lines 151–152 permit changes
"only if the selected internationalization library requires them"; none is
selected. Rationale: 41 keys × 3 locales and 3 `Intl` calls do not justify
`next-intl`, and the packet's own gates (build size, hygiene source scans) are
easier to hold on a dependency-free implementation.

### D-I18N-05 — Locale flows as a required prop; no React context

`translate(locale, key, values?)` is a **pure function** imported by **server**
components. Components that render chrome take a required `locale: Locale` prop.
No `LocaleProvider`, no context, no new `"use client"` boundary beyond
`components/locale-switcher.tsx`. Rationale: governing line 167–168 ("do not
force the entire application into client rendering merely to translate strings");
a required prop makes an unwired call site a `tsc` error instead of a silent
English fallback. **Do not** default the prop — a default would hide exactly the
bug the prop exists to catch. The four existing component tests pass
`locale="en"` explicitly (§12).

### D-I18N-06 — Locale names are locale metadata, not messages

Endonyms (`English`, `Français`, `العربية`), `dir`, and BCP-47 tags live in
`i18n/locales.ts` as a `LOCALE_METADATA` table, never in a catalog. Rationale: a
language's own name must not be translatable, and keeping it out of the catalogs
keeps the 41-key parity check meaningful. Each selector link carries
`lang={code}` and `hrefLang={code}`.

### D-I18N-07 — Controlled vocabularies: translate the display label, preserve the token

`WorkflowState` (`complete|active|waiting|refused`) and `EvidenceNode.kind`
(`claim|chunk|document|study|decision`) are **displayed** through catalogued
labels; the **English** catalog values are byte-identical to the tokens, so the
English DOM is unchanged and every existing state/kind assertion stays green
without edit. Interpretation recorded: governing line 130–131 excludes
"controlled contract vocabulary" from translation, while line 184 lists "state
descriptions" as translatable. Resolution: the canonical token is never
localized **as data** — `stage.state` and `node.kind` remain the contract values
and the React `key` is still derived from them; only the *rendered word* is
chrome. **Reviewer question RQ-1** (§16) asks the reviewer to ratify this.

### D-I18N-08 — Logical properties only; one documented typography exception

The six physical-property sites in §9 become Tailwind v4 logical utilities
(`border-s`, `border-e`, `ps-*`, `pe-*`, `start-*`, `end-*`, `text-start`,
`text-end`). Additionally, the eight sites that carry `text-[0.6875rem]` — seven
of which also carry `tracking-[…]`; §9.1 names the eighth exactly — gain
`rtl:tracking-normal rtl:text-[0.75rem]`. This is the **only**
permitted `rtl:` variant in the packet and it is typography, not layout:
positive letter-spacing and an 11px size are hostile to Arabic script
(`text-transform: uppercase` is a no-op in Arabic and is left in place).
Rationale for not scoping by `[dir="rtl"]`/`[lang="ar"]` in CSS: escaping
Tailwind's arbitrary-value class names into a stylesheet selector is more
fragile than one colocated, reviewable `rtl:` variant.

### D-I18N-09 — No icon mirroring in this packet

`mobile-nav.tsx:46` (`Bars3Icon`) and `:64` (`XMarkIcon`) are direction-neutral
and must **not** be mirrored. Blanket `rtl:scale-x-[-1]` is forbidden. If a
future genuinely directional icon (chevron, arrow) appears, mirroring is an
explicit per-icon decision recorded in the packet that adds it.

### D-I18N-10 — Locale selector is links, not a custom listbox

`components/locale-switcher.tsx` is a client component (it needs
`usePathname()` to keep the equivalent route on deeper future routes) that
renders:

```tsx
<nav aria-label={translate(locale, "locale.selectorLabel")} data-nav-region="locale">
  {SUPPORTED_LOCALES.map((code) => (
    <Link key={code} href={swapLocale(pathname, code)} lang={code} hrefLang={code}
          aria-current={code === locale ? "true" : undefined}>
      {LOCALE_METADATA[code].endonym}
    </Link>
  ))}
</nav>
```

Rationale: plain links are keyboard reachable, announce current selection via
`aria-current`, survive copy/right-click/middle-click, need no JS state, and
introduce no custom widget role. It is the **only** new client component, and it
imports no catalog (§5: `translate` runs in the layout, results are passed as a
prop array).

> `data-nav-region="locale"` — and `data-nav-region="primary"` /
> `data-nav-region="mobile"` on the two existing `<nav>`s, plus
> `data-nav-region="mobile-trigger"` on the `<DialogTrigger>` button — are the
> single non-a11y markup hooks this packet adds. They exist because
> `tests-browser/helpers.ts:79` identifies the primary nav through the
> **English** `aria-label`, which would silently stop matching in `fr`/`ar` and
> turn `tab-order.spec.ts:39` into a **vacuous pass**. The accessible names are
> unchanged in meaning and remain asserted in `shell.test.tsx`.

**Why the trigger needs a hook too, stated exactly.** `data-nav-region` on the
two `<nav>`s is not sufficient: the mobile disclosure is opened by a *button*,
and six existing locator sites identify that button by its **English** accessible
name — `rendered-axe.spec.ts:279` (via `helpers.ts:27`'s
`MOBILE_NAV_TRIGGER_LABEL`), `responsive-nav.spec.ts:31,41,52`,
`screenshots.spec.ts:135`, `tab-order.spec.ts:56`. Every one of those is a file
this packet schedules to run against `/fr` and `/ar` (§13.1, §15.1's
`375-mobile-ar.png`). An English accessible-name locator against a translated
document does not degrade quietly to a wildcard — it times out — but a
**time-out is a red run for the wrong reason**, and a reviewer triaging six
identical Playwright time-outs would not immediately know the cause was the
locator and not the application. `data-nav-region="mobile-trigger"` removes the
ambiguity. `MOBILE_NAV_TRIGGER_LABEL` stays in `helpers.ts` for the `en` cases
and for the `<bdi>`-free English assertion in `shell.test.tsx`; it is simply not
the locator for a `fr`/`ar` case.

### D-I18N-11 — Locale selector is the last header item in DOM order, visible at both viewports

`<LocaleSwitcher>` is rendered after `<MobileNav />` inside the header container.
Rationale (measured, not aesthetic): it keeps `responsive-nav.spec.ts:56-57`
(two Tabs → mobile trigger at 375px) and `focus-visibility.spec.ts:187-189`
(two Tabs → primary nav link at 1440px) correct without editing their press
counts, and confines the focus-ring growth to the 1440px union
(`tab-order.spec.ts:53`), which is explicitly updated. Moving the selector later
requires re-measuring those counts.

**The selector carries NO breakpoint.** It is visible at 375px and at 1440px, in
the same header row as `PrimaryNav`, and it is never `hidden lg:block` or
`lg:hidden`. This is a decision, not an omission, and it is load-bearing:

- Hiding it below `lg` would leave a mobile user **no locale affordance at all**.
  D-I18N-01 makes the URL the only source of locale truth, so with the selector
  hidden the only way to change locale on a 375px screen would be to hand-edit
  the path — which contradicts governing deliverable 5 (line 171–172: "a language
  selector usable by keyboard and assistive technology") more severely than a
  header that is one row taller.
- It also contradicts governing gate line 232–234, which requires the 375px
  screenshots for `en`, `fr` and `ar` *and* keyboard-usable switching.

Measured consequence, pinned by `tab-order.spec.ts` at **both** viewports (M3 —
this line was previously omitted from §13.1, which would have left the 375px
expectation silently un-measured):

| Viewport | Expected `order` (`describeStop` = `` `${tag}:${accessibleName}` ``) |
| --- | --- |
| 375px | `["a:Skip to main content", "button:Open main navigation", "a:English", "a:Français", "a:العربية"]` |
| 1440px | `["a:Skip to main content", "a:Overview", "a:English", "a:Français", "a:العربية"]` |

The three endonyms are `LOCALE_METADATA[code].endonym` (D-I18N-06) in
`SUPPORTED_LOCALES` order. The Arabic endonym is pinned as the **JS string
literal** `"a:العربية"` — a byte-identical label pin, the same discipline already
applied to `MOBILE_NAV_TRIGGER_LABEL` and the `375-overview.png` filename, and
deliberately **not** a regex or a `toContain`. `measureTabRing`'s 8 presses
(`helpers.ts:107`) cover five stops at both widths; if a future change made the
ring longer than eight, the assertion fails on the truncated array instead of
silently passing.

### D-I18N-12 — Locale selector stays in the shell, never in page content

`keyboard-traversal.test.tsx:176-189` asserts that `HomePage` contributes **zero**
tab stops. The selector therefore lives in `components/app-shell.tsx`, not in
`components/overview-page.tsx`. Violating this is legitimate breakage of a
deliberate tripwire and must not be "fixed" by editing that assertion.

### D-I18N-13 — Unsupported locale is a catalog-backed 404 in the default locale

`app/[locale]/layout.tsx` resolves `params.locale` through
`isSupportedLocale()`; on failure it resolves to `DEFAULT_LOCALE` (`en`) for the
`<html lang dir>` attributes only, so the document stays valid. The **page**
(`app/[locale]/page.tsx`) calls `notFound()`, which renders
`app/[locale]/not-found.tsx` with the four catalog-backed keys from §4.1.
`export const dynamicParams = true` is explicit and commented: `false` would make
Next serve its own English 404 and bypass the catalog-backed path.

Rationale: the page-level `notFound()` is the canonical documented Next case; a
`notFound()` thrown from the topmost layout is not.

### D-I18N-14 — `generateMetadata` is async and locale-aware

`generateMetadata({ params })` awaits `params` and returns
`metadataBase`-free relative metadata whose `title` is the pinned brand string
and whose `description` is `translate(locale, "app.meta.description")`.
`alternates.languages` and `metadataBase` are **deferred** (§15).

### D-I18N-15 — Long-string inflation is an env-gated, test-only transform

Governing acceptance line 228–229 requires a ≥30 % expansion gate. Inflation
lives in `i18n/long-strings.ts`, is applied inside `translate()`, and is gated by
`NEXT_PUBLIC_I18N_EXPANSION_PERCENT` (default `0`, i.e. off). Filler is
per-locale and script-correct (Latin for `en`/`fr`, Arabic for `ar`) so the
overflow measurement is meaningful. A new `playwright.long-strings.config.ts`
starts a second server on a different port **and performs its own `next build`
with the expansion env set, on its own `distDir`**; see §13.2 for the written
scope-extension request and for why the env-var-only formulation was vacuous
(B1).

### D-I18N-16 — No product surface is added for testing

No `?long=1` query parameter, no debug route, no `NODE_ENV` branches inside
components, no cookie. The only test hooks are `data-nav-region` (D-I18N-10 —
values `primary`, `mobile`, `mobile-trigger`, `locale`) and the env var
(D-I18N-15). No `data-testid` is introduced anywhere in this packet, precisely so
that "one hook vocabulary" stays true.

---

## 4. Exhaustive string inventory (`file:line`)

Every user-facing string in `app/` + `components/`, mechanically enumerated on
`8ba4fb6`. Counts: **41 catalogued** (40 `TRANSLATE` + 1 `BRAND`), **3 `FORMAT`**
sites, **25 rendered fixture values**, **1 declared-but-unrendered fixture
value**. Any string not listed here is not user-facing (class names, ids,
`aria-*` plumbing).

### 4.1 `TRANSLATE` — 40 catalog keys

| # | Site (verified line) | Key | English source (must stay exact) |
| --- | --- | --- | --- |
| T01 | `app/layout.tsx:10` → `app/[locale]/layout.tsx` | `app.meta.description` | `Traceable systematic-review workflows for research teams.` |
| T02 | `app/page.tsx:31` | `overview.eyebrow` | `Project overview` |
| T03 | `app/page.tsx:46` | `overview.lastEvent` | `Latest: {event}` |
| T04 | `app/page.tsx:55` | `overview.workflowHeading` | `Workflow` |
| T05 | `app/page.tsx:58` | `overview.workflowLede` | `Every stage exposes its decisions, evidence, and refusals.` |
| T06 | `app/page.tsx:71` | `overview.traceHeading` | `Claim-to-source trace` |
| T07 | `app/page.tsx:73` | `overview.traceLede` | `Follow a research claim back to its protocol-bound decision.` |
| T08 | `app/page.tsx:86` | `overview.asideEyebrow` | `Why this matters` |
| T09 | `app/page.tsx:89` | `overview.asideHeading` | `A synthesis is not trusted because it sounds convincing.` |
| T10 | `app/page.tsx:92` | `overview.asideBody` | `Nexus Scholar makes the evidence path inspectable and refuses artifacts that do not satisfy the declared lineage.` |
| T11 | `components/app-shell.tsx:48` | `a11y.skipToMain` | `Skip to main content` |
| T12 | `components/app-shell.tsx:61` | `shell.tagline` | `Research integrity you can inspect` |
| T13 | `components/app-shell.tsx:75` | `safety.demoDataLabel` | `Demonstration data` |
| T14 | `components/app-shell.tsx:97` | `shell.authorityStatement` | `Read-only demonstrator. The Python harness remains authoritative for contracts, identity, acceptance, toolkit execution and audit events.` |
| T15 | `components/primary-nav.tsx:27` | `nav.overview` | `Overview` |
| T16 | `components/primary-nav.tsx:28` | `nav.screening` | `Screening` |
| T17 | `components/primary-nav.tsx:29` | `nav.evidence` | `Evidence` |
| T18 | `components/primary-nav.tsx:30` | `nav.audit` | `Audit` |
| T19 | `components/primary-nav.tsx:38` | `nav.unavailable` | `Not yet available` |
| T20 | `components/primary-nav.tsx:104` | `nav.landmark.primary` | `Primary` |
| T21 | `components/mobile-nav.tsx:9` | `a11y.openMainNavigation` | `Open main navigation` |
| T22 | `components/mobile-nav.tsx:10` | `a11y.closeMainNavigation` | `Close main navigation` |
| T23 | `components/mobile-nav.tsx:56` | `nav.landmark.primaryMobile` | `Primary (mobile menu)` |
| T24 | `components/mobile-nav.tsx:58` | `nav.mobileDialogTitle` | `Main menu` |
| T25 | `components/workflow-timeline.tsx:28` | `workflow.listLabel` | `Research workflow` |
| T26 | `components/workflow-timeline.tsx:36` | `workflow.stageOrdinal` | `Stage {number}` |
| T27 | `status-badge.tsx:46` | `state.complete` | `complete` |
| T28 | `status-badge.tsx:46` | `state.active` | `active` |
| T29 | `status-badge.tsx:46` | `state.waiting` | `waiting` |
| T30 | `status-badge.tsx:46` | `state.refused` | `refused` |
| T31 | `components/evidence-chain.tsx:59` | `evidenceKind.claim` | `claim` |
| T32 | `components/evidence-chain.tsx:59` | `evidenceKind.chunk` | `chunk` |
| T33 | `components/evidence-chain.tsx:59` | `evidenceKind.document` | `document` |
| T34 | `components/evidence-chain.tsx:59` | `evidenceKind.study` | `study` |
| T35 | `components/evidence-chain.tsx:59` | `evidenceKind.decision` | `decision` |
| T36 | new `components/locale-switcher.tsx` | `locale.selectorLabel` | new — design as a concise noun phrase, e.g. `Language` |
| T37 | new `app/[locale]/not-found.tsx` | `notFound.heading` | new |
| T38 | new `app/[locale]/not-found.tsx` | `notFound.body` | new |
| T39 | new `app/[locale]/not-found.tsx` | `notFound.unsupportedLocale` | new, **single template** with `{requested}` and `{available}` placeholders |
| T40 | new `app/[locale]/not-found.tsx` | `notFound.backToDefault` | new |

Keys describe meaning/role, not English wording. T15–T19 must satisfy
`catalog.en[navKey(item.id)] === item.label` (and
`catalog.en["nav.unavailable"] === UNAVAILABLE_NAV_TEXT`) — asserted by test, so
`PRIMARY_NAV_ITEMS` and `UNAVAILABLE_NAV_TEXT` stay frozen.

**Precisely which fields are frozen** (M10 — "the constant stays frozen" is
ambiguous, and read literally it demands a render the frozen constant makes
impossible, because `components/primary-nav.tsx:27` pins
`PRIMARY_NAV_ITEMS[0] = { id: "overview", label: "Overview", href: "/" }` while
§12 requires a **locale-prefixed** `/en` href):

| Symbol | Frozen fields | Derived at render | Why |
| --- | --- | --- | --- |
| `PRIMARY_NAV_ITEMS` | `id`, `label`, and the **absence** of `href` on `screening`/`evidence`/`audit` | — | The set of surfaces, their ids, and the honesty rule (no dead-route link) are the UI-01c contract. `shell.test.tsx:220`'s `["Overview","Screening","Evidence","Audit"]` still holds. |
| `PRIMARY_NAV_ITEMS[0].href` | **frozen as the sentinel `"/"`** | `PrimaryNavList` computes the rendered href as `` `/${locale}` `` and **ignores `item.href` as a literal** | The constant keeps `/` so `shell.test.tsx:205`'s `item.href === undefined` filter (which selects the no-route entries) keeps its meaning, and so the "which route exists" fact stays declared in one place. The *rendered* href is locale-prefixed. |
| `UNAVAILABLE_NAV_TEXT` | frozen whole | — | `shell.test.tsx:213` asserts its exact text. |
| `currentItemId` | frozen default `"overview"` | — | `shell.test.tsx:190-193` asserts exactly one `aria-current="page"` whose text is `Overview`. |

The rendered-href computation is asserted **for all three locales** at
`tests/shell.test.tsx:201-202` (§12), so the sentinel can never quietly become a
bare `/` link again on `fr`/`ar`.

### 4.2 `BRAND` — 1 key, 2 sites

| # | Sites | Key | Value (identical in `en`/`fr`/`ar`) |
| --- | --- | --- | --- |
| B01 | `app/layout.tsx:9` (metadata title) + `components/app-shell.tsx:55` (wordmark) | `brand.productName` | `Nexus Scholar` |

One key, two roles, asserted identical across all three catalogs.

### 4.3 `FORMAT` — 3 sites, `Intl` only

| # | Site | Value | Rule |
| --- | --- | --- | --- |
| F01 | `workflow-timeline.tsx:36` | `{number}` inside `workflow.stageOrdinal` | `Intl.NumberFormat(locale)` |
| F02 | `workflow-timeline.tsx:47` | `stage.count` (`143`, `18`) | `Intl.NumberFormat(locale)`; **never** a key, id or persistence value |
| F03 | `evidence-chain.tsx:41` | trail ordinal `index + 1` | `Intl.NumberFormat(locale)`; stays a bare text node in `firstElementChild` |

`Intl.NumberFormat("en").format(143) === "143"`, so every existing count/ordinal
assertion keeps passing unchanged.

### 4.4 Byte-preserved fixture — 25 rendered values

Every one wrapped in `<bdi>` (D-I18N-02). Never translated, never `Intl`-formatted,
never used as a key.

| Fixture field | Site | Count |
| --- | --- | --- |
| `demoProject.title` | `page.tsx:35` (`<h1>`) | 1 |
| `demoProject.researchQuestion` | `page.tsx:38` | 1 |
| `demoProject.lastEvent` | `page.tsx:46`, interpolated into `overview.lastEvent` | 1 |
| `stages[].label` | `workflow-timeline.tsx:40` | 6 |
| `stages[].description` | `workflow-timeline.tsx:41` | 6 |
| `demoEvidence[].label` | `evidence-chain.tsx:62` | 5 |
| `demoEvidence[].detail` | `evidence-chain.tsx:63` | 5 |

**Declared but not rendered** (recorded for completeness, no change):
`mock-project.ts:4` `slug`, `mock-project.ts:9-14` `stages[].id` (React `key`
only, `workflow-timeline.tsx:31`), `mock-project.ts:19-23` `nodes[].status`.
These stay English/Latin **and** stay usable as machine identifiers in every
locale — that is the whole point of the isolation rule.

### 4.5 What is *not* in the inventory

No dates, times, timestamps, DOIs, checksums, refusal codes, file paths or
quoted evidence are rendered anywhere in the shell or overview, so this packet
introduces no formatting ambiguity for them. The rule is still recorded in
`I18N.md`: those categories are excluded from cataloguing and from `Intl`
formatting, and when a future packet renders one it must be emitted inside
`<bdi>` (or `dir="ltr"`) with `Intl`-independent formatting.

---

## 5. Frozen inputs

### 5.1 Byte pins (SHA-256, verified on `8ba4fb6`)

| File | Bytes | SHA-256 |
| --- | --- | --- |
| `lib/mock-project.ts` | 1710 | `af33ce0e6e9372ff4aa5c2d35689580ae8a78402edc521d40e7db0e314f72f2c` |
| `lib/contracts.ts` | 786 | `57b3d551a1ae0be4c0aa9cee7d05df47aef973c647f686699301dcbddaa624a2` |
| `package.json` | 1028 | `5687ea5bda1a92ab38d81d62263aff3f4f93082f7b4cc27ad8cebd847fb3f449` |
| `package-lock.json` | 122410 | `bcdd05a0a17254fd70f58e3ff45b7419373e9cd072968536c7374387826536e7` |

A vitest test asserts all four digests. This makes D-I18N-02 and D-I18N-04
mechanically enforceable instead of reviewer-trusted. `lib/` gets **no** other
edit.

### 5.2 Frozen file list

Unchanged: `lib/mock-project.ts`, `lib/contracts.ts`, `package.json`,
`package-lock.json`, `playwright.config.ts`, `vitest.config.ts`,
`tsconfig.json`, `next-env.d.ts`, `AGENTS.md`, `UI-01C_WORK_PACKET.md`,
`VISUAL_DIRECTION.md`, and every path outside `apps/research-ui/`.

**One exception, added by §13.2.4 request 2 part 3:** `.gitignore` moves from
this list to the modified list (it gains `.next-longstrings/`). That is the whole
of its change, it is inside `apps/research-ui/`, and it is escalated with the
other two scope-extension requests in H8.

Modified only where listed in §11–§13: `next.config.ts`, `.gitignore`,
`app/globals.css`,
the six existing components, the seven vitest files, the nine Playwright files,
`GATES.md`, and `README.md` if its commands change (they should not).

**The nine Playwright files, named so the manifest is auditable** (m18 — the
count 9 = 8 in `tests-browser/` + `playwright.config.ts` at the app root, which
is not obvious and was previously left as a bare number):

| # | Path | Role in UI-01d |
| --- | --- | --- |
| 1 | `tests-browser/focus-visibility.spec.ts` | §13.1 |
| 2 | `tests-browser/helpers.ts` | §13.1 (whole range 104–114 is MODIFIED — M4) |
| 3 | `tests-browser/hygiene.spec.ts` | §13.1 (M5: `sourceFiles()` must go recursive) |
| 4 | `tests-browser/overflow.spec.ts` | §13.1, and the recipe AC-9 reuses (M7) |
| 5 | `tests-browser/rendered-axe.spec.ts` | §13.1, and the **only** contrast coverage (M2) |
| 6 | `tests-browser/responsive-nav.spec.ts` | §13.1 |
| 7 | `tests-browser/screenshots.spec.ts` | §13.1, §15.1 |
| 8 | `tests-browser/tab-order.spec.ts` | §13.1 (line 35 newly covered — M3) |
| 9 | `playwright.config.ts` | **unchanged** (`npm run build` in `webServer.command`, line 62); listed so the count is complete |

There is no `tests-browser/evidence-contrast.spec.ts` and there never was; §13.1
and §18 previously named one, which was wrong. Contrast coverage is M2's
subject and is stated there.

---

## 6. Typed catalog design

```
apps/research-ui/i18n/
  locales.ts        SUPPORTED_LOCALES, Locale, DEFAULT_LOCALE,
                    LOCALE_METADATA (endonym/dir/tag), isSupportedLocale(),
                    resolveLocale(), swapLocale()
  translate.ts      MessageKey, MessageValues, translate(locale, key, values?)
  format.ts         formatNumber(locale, value) — Intl only
  long-strings.ts   D-I18N-15 inflation, default off
  index.ts          public surface
apps/research-ui/messages/
  en.ts fr.ts ar.ts index.ts
```

Required behaviour:

1. `Locale` is `"en" | "fr" | "ar"`. `resolveLocale(value: string): Locale`
   returns the exact match or `DEFAULT_LOCALE`; it is **case-sensitive** and
   performs **no** subtag negotiation (`/EN`, `/en-US`, `/fr-FR` → default).
2. `translate(locale, key, values?)`:
   - unknown key → `throw MissingMessageError(key)` (never renders the key);
   - value that `trim()`s to empty → `throw MissingMessageError` (never renders
     `""`);
   - unreplaced `{placeholder}` after interpolation → `throw` (catches
     placeholder drift);
   - returns a `string`, never `undefined`.
3. Interpolation is positional-free named substitution (`{event}`), one message
   per grammatical unit. **No concatenated fragments** (governing line 202).
4. `translate()` is pure, synchronous, and free of React, so it works in server
   components, `generateMetadata`, and vitest alike.
5. `swapLocale(pathname, target)`: replace/insert the first segment, preserve the
   rest and any trailing slash/query. `swapLocale("/fr/evidence?x=1","ar")` →
   `/ar/evidence?x=1`; `swapLocale("/","ar")` → `/ar`.
6. Catalogs contain no `Intl`-formatted output and no `lang`/`dir` values.

---

## 7. Routing and document direction

| Path | Status | `html lang` | `html dir` | Body |
| --- | --- | --- | --- | --- |
| `/` | 307 → `/en` | — | — | — |
| `/en` `/fr` `/ar` | 200 | `en` `fr` `ar` | `ltr` `ltr` `rtl` | catalogued overview |
| `/de` `/EN` `/en-US` `/fr-FR` `/ar-EG` | 404 | `en` | `ltr` | catalog-backed not-found naming `{requested}` and listing `{available}` |
| `/fr/…`, `/ar/…` (future) | 200 | segment locale | derived | locale-preserving (D-I18N-10) |

`app/[locale]/layout.tsx`:

```tsx
export const dynamicParams = true;               // D-I18N-13
export function generateStaticParams() { return SUPPORTED_LOCALES.map((locale) => ({ locale })); }
export async function generateMetadata({ params }): Promise<Metadata> { /* D-I18N-14 */ }
export default async function LocaleLayout({ children, params }: { children: React.ReactNode; params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  return <LocaleDocument locale={resolveLocale(raw)}>{children}</LocaleDocument>;
}
```

`components/locale-document.tsx` (synchronous, testable) renders
`<html lang={locale} dir={LOCALE_METADATA[locale].dir}>` + `<body>` +
`<AppShell locale={locale} currentPath={…}>`, and imports `./globals.css`
(moved with the layout import).

`app/[locale]/page.tsx`:

```tsx
export default async function LocalePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  if (!isSupportedLocale(raw)) notFound();
  return <OverviewPage locale={raw} />;
}
```

`app/[locale]/not-found.tsx` renders exactly **one** `<h1>`, the three catalog
strings and a `<Link href="/en">`. It must not import the catalogs directly if
that would duplicate keys — read them with `translate(DEFAULT_LOCALE, …)` since
the layout's fallback locale is `en` (D-I18N-13). It adds no landmark, no
focusable control other than the back link, and no second `<main>`.

---

## 8. Direction conversion: markup and CSS

`[dir="rtl"]` on `<html>` is the single source of direction. Do **not** add
`dir` to individual components; a component must work under whatever direction
its document declares. Do **not** introduce `rtl:` variants for *layout*
(governing line 205–206 forbids an `rtl:` layout patch where a logical utility
expresses the intent); the only `rtl:` variants permitted are D-I18N-08's
typography pair.

Verified current state: `grid-cols-[…]`, `gap-x-*`, `border-t/b`, `space-y`,
`inset-y-0` and `mx-auto` are already direction-safe (grid columns follow the
inline axis). No change needed for them.

---

## 9. Direction conversion table (complete, exhaustive)

| # | Site | Current | Replace with | Reason |
| --- | --- | --- | --- | --- |
| DC1 | `app/page.tsx:45` | `border-l border-rule-strong pl-4` | `border-s border-rule-strong ps-4` | Rule sits on the block's inline-start edge; in `ar` it must sit on the right. |
| DC2 | `app/page.tsx:84` | `border-l-2 border-evidence pl-5` | `border-s-2 border-evidence ps-5` | idem for the `Why this matters` aside. |
| DC3 | `app/globals.css:240` | `.skip-link:focus { left: 1rem; }` | `inset-inline-start: 1rem;` | The skip link must appear at the inline start (left in LTR, **right** in RTL). |
| DC4 | `components/evidence-chain.tsx:40` | `text-right` | `text-end` | The marginal ordinal aligns to the inline end of its narrow column. |
| DC5 | `components/evidence-chain.tsx:45-49` | prose in the doc comment naming `` `border-l` `` | update the comment to name `` `border-s` `` | Comment drift becomes a false record of the rule's side. |
| DC6 | `components/evidence-chain.tsx:50` | `border-l border-rule-strong pl-3 lg:pl-5` | `border-s border-rule-strong ps-3 lg:ps-5` | Lineage rail. |
| DC7 | `components/mobile-nav.tsx:54` | `right-0` | `end-0` | Panel anchors to the inline end so it opens from the correct edge. |
| DC8 | `components/mobile-nav.tsx:54` | `border-l` | `border-s` | Panel's edge rule is on its inline-start edge. |

The seven prose/doc comments in `app/page.tsx:13-20,80`, `app-shell.tsx:11-97`,
`mobile-nav.tsx:16-32`, `workflow-timeline.tsx:8-18`, `status-badge.tsx:8-45`
and `evidence-chain.tsx:15-45` describe invariants in English and about the
English DOM. They must be **updated where the invariant changes** (not
mechanically translated): `page.tsx:15` explicitly records that the
`Latest: …` line "stays a single text node (it is the F1 contrast site)", which
D-I18N-02 changes.

### 9.1 Arabic typography adaptation (D-I18N-08)

Add `rtl:tracking-normal rtl:text-[0.75rem]` to the class strings at:

`app/page.tsx:30`, `app/page.tsx:85`, `components/app-shell.tsx:74`,
`components/primary-nav.tsx:68`, `components/status-badge.tsx:27`,
`components/workflow-timeline.tsx:35`, `components/evidence-chain.tsx:40`,
`components/evidence-chain.tsx:58`.

**The characterisation in D-I18N-08 was off by one (m17); the site list is
correct and is not changed.** Seven of these eight sites pair
`text-[0.6875rem]` with a `tracking-[…]` value (`page.tsx:30` `:0.16em`,
`page.tsx:85` `:0.16em`, `app-shell.tsx:74` `:0.14em`, `primary-nav.tsx:68`
`:0.12em`, `status-badge.tsx:27` `:0.12em`, `workflow-timeline.tsx:35` `:0.16em`,
`evidence-chain.tsx:58` `:0.16em`). The **eighth**,
`components/evidence-chain.tsx:40`, is `pt-0.5 text-right text-[0.6875rem]
leading-4 text-ink-faint` — it carries the 11px size and the `text-right` (DC4)
but **no `tracking-` class at all** (verified on `8ba4fb6`). So for that one site
the size half of the pair is the whole adaptation and `rtl:tracking-normal` is a
harmless no-op. D-I18N-08's wording is corrected to "the eight sites that carry
`text-[0.6875rem]`, seven of which also carry `tracking-[…]`"; the sentence
"the eight sites that pair … with `tracking-[…]`" is withdrawn as inaccurate.

`status-badge.tsx:27` and `primary-nav.tsx:68` carry `uppercase`; in Arabic it is
a no-op, so the only adaptation needed is tracking + size. Colour and contrast are
unchanged (WCAG AA must still hold for the Arabic glyphs at the new size —
verify in the browser gate, do not assume).

---

## 10. Negative cases (must each have an executable check)

| # | Negative case | Executable check |
| --- | --- | --- |
| N1 | `/` must not render the overview | `locale-routing.spec.ts`: `GET /` → 3xx, `location` `/en`, final URL `/en` |
| N2 | Unsupported locales are case- and subtag-strict | `locale-routing.spec.ts` over `/de`, `/EN`, `/en-US`, `/fr-FR`, `/ar-EG`: status 404, body contains `notFound.unsupportedLocale` rendered in `en`, `html lang="en"`, `html dir="ltr"` |
| N3 | A missing required message fails loudly | `i18n-catalog.test.ts`: `translate("fr", <key removed from a cast>)` throws; a `""`/whitespace value throws; the thrown error never renders a key or empty string |
| N4 | Placeholder drift fails | `i18n-catalog.test.ts`: `{…}` placeholder sets identical in `en`/`fr`/`ar` for all 41 keys |
| N5 | Key-set drift fails at compile time and in test | `tsc` via `Record<MessageKey, string>`; `i18n-catalog.test.ts` asserts `Object.keys` equality and length `41` |
| N6 | The fixture file is byte-identical | `i18n-catalog.test.ts` asserts the §5.1 SHA-256 of `lib/mock-project.ts` and `lib/contracts.ts` |
| N7 | No dependency was added | `i18n-catalog.test.ts` asserts the §5.1 SHA-256 of `package.json` and `package-lock.json`; `git diff --stat` shows neither |
| N8 | No English survives translation | `i18n-render.test.tsx` iterates **every** `MessageKey` — not a word-count-filtered subset — and for each key asserts **both** directions in each of `en`/`fr`/`ar`. **(a) Presence:** the rendered node for key `k` under locale `L` contains `catalog[L][k]`, or, where `k` carries a `{placeholder}`, the exact `Intl`-/locale-formatted string built from that locale's catalog (F01–F03). **(b) Absence:** for every key, the rendered `fr` and `ar` document contains neither the raw English value **nor** a normalised form of it (whitespace-collapsed, case-folded, diacritic-stripped), unless the key is on the explicit allow-list below. The allow-list is a `const` in the test with **one-line reason per entry**: the three native endonyms `English` / `Français` / `العربية` (D-I18N-06 — a language's own name is not translatable and lives outside the catalogs), `brand.productName` = `Nexus Scholar` (D-I18N-02, §4.2 — identical in all three catalogs by design), `Research Nexus` if it is used, and any brand or product name. |
| N9 | No literal `aria-label`/`title`/`alt`/`placeholder` survives | `i18n-direction-source.test.ts`: zero matches of `/(aria-label\|title\|alt\|placeholder)="/` in `app/**` + `components/**` |
| N10 | No physical-property layout patch | `i18n-direction-source.test.ts`, over `app/**` + `components/**`, with the width suffixes made **optional** so a suffixed border utility cannot slip past (M15). Class regex — `border-l(?:-[0-9]+)?(?![\w-])`, `border-r(?:-[0-9]+)?(?![\w-])`, `rounded-l(?:-[0-9]+)?(?![\w-])`, `rounded-r(?:-[0-9]+)?(?![\w-])`, `text-left\|text-right(?![\w-])`, `ml-\d`, `mr-\d`, `pl-\d`, `pr-\d`, `left-\d`, `right-\d`, `space-x-reverse`, `divide-x-reverse`, `origin-left\|origin-right`, `float-left\|float-right` — zero matches. Plus, in `app/globals.css`, zero of `/(^\|[;\s])(left\|right\|margin-left\|margin-right\|padding-left\|padding-right\|border-left\|border-right)\s*:/`. **Why the suffix matters, verified on `8ba4fb6`:** the pre-M15 regex `border-l(?![\w-])` does **not** match `border-l-2`, so `app/page.tsx:84`'s `border-l-2` was caught only because the same element also carries `pl-5`. The moment the padding pair changes, the guard silently stops biting the width-suffixed site. The symmetric additions (`rounded-l-*`/`rounded-r-*` corners, `space-x-reverse`/`divide-x-reverse`, `origin-left|right`, `float-left|right`) are all verified absent from `app/` and `components/` today; they are listed so a future one is caught rather than argued about. |
| N11 | Direction-neutral icons are not mirrored | `i18n-direction-source.test.ts`: `mobile-nav.tsx` contains no `scale-x-[-1]` / `rtl:scale-x` |
| N12 | No render-time network or MT | `hygiene.spec.ts` (existing "no analytics globals" test) plus `i18n-direction-source.test.ts`: no `fetch(`, no `XMLHttpRequest`, no `localStorage`, no `navigator.language` in `app/**`, `components/**`, `i18n/**`, `messages/**` |
| N13 | Locale is never browser state | `locale-switch.spec.ts`: after switching to `fr`, a fresh context/`page.goto("/en")` returns `en`; no cookie/localStorage key is written |
| N14 | Switching preserves the equivalent route | `locale-switch.spec.ts` asserts `href` targets, `aria-current`, and that activating `ar` from `/fr` lands on `/ar` with `lang="ar" dir="rtl"` and no 404 |
| N15 | No hydration mismatch in any locale | `locale-routing.spec.ts` fails on any `console` error / `pageerror` matching `/hydrat\|did not match/i` for `/en`, `/fr`, `/ar` |
| N16 | No horizontal overflow in any locale, at 30 % expansion | `overflow.spec.ts` extended to `/fr`, `/ar`; the long-strings config (§13.2) runs the **same recipe** at 375 and 1440 against the inflated build. The recipe is M7's and is **not** a per-element `scrollWidth <= clientWidth`: `documentElement` **strict** `<=`, `body` and `<main>` `<= clientWidth + 1` (the 1px tolerance is the documented `overflow.spec.ts:49-53` rule — "sub-pixel rounding of fractional layout widths is not a scrollbar, and asserting a strict `<=` against it would be a flaky assertion dressed up as a strict one"), plus the existing unbreakable-token probe `[^\s]{24,}`. See §14 AC-9 for why per-element checking is out of scope and what replaces it. |
| N17 | Accessibility guarantees survive in all three locales | `rendered-axe.spec.ts` for `/fr` and `/ar` with zero serious/critical; `shell.test.tsx`'s existing rule list (`bypass`, `landmark-one-main`, `page-has-heading-one`, `region`, `landmark-unique`) unchanged |
| N18 | Focus is visible and ordered in `ar` | `focus-visibility.spec.ts` gains an `ar` case for the primary nav link, the mobile trigger and each locale link |
| N19 | Identifiers, numbers and codes are not reversed | `direction.spec.ts` asserts the ordinal column's `text-align` is `end`-resolved to `right` in `ar`, the count `143` renders as `143` (or `١٤٣` per locale) inside a `<bdi>`-isolated, non-reversed run, and the trail ordinals are 1…5 in ascending **logical** order |
| N20 | The 404 page is a valid page | `locale-routing.spec.ts`: exactly one `<h1>`, exactly one `main`, axe `page-has-heading-one` + `landmark-one-main` clean |

---

## 11. File manifest

### 11.1 New

```
UI-01D_WORK_PACKET.md                           orchestrator-owned (m20) — this
                                                file. Same designation as the
                                                UI-01c precedent (UI-01C_WORK_PACKET.md:76
                                                "this file, orchestrator-owned"): the
                                                implementer MUST NOT edit it. Any
                                                change to this packet after handoff is
                                                an orchestrator action, recorded as
                                                such, never a silent implementation
                                                edit.
I18N.md                                         (D-I18N-01c)
i18n/locales.ts  i18n/translate.ts  i18n/format.ts  i18n/long-strings.ts  i18n/index.ts
messages/en.ts    messages/fr.ts    messages/ar.ts    messages/index.ts
components/locale-document.tsx                   (sync; <html lang dir>)
components/locale-switcher.tsx                   (client; usePathname only)
components/overview-page.tsx                     (moved from app/page.tsx)
app/[locale]/layout.tsx  app/[locale]/page.tsx  app/[locale]/not-found.tsx
tests/i18n-catalog.test.ts
tests/i18n-render.test.tsx
tests/i18n-direction-source.test.ts
tests-browser/locale-routing.spec.ts
tests-browser/locale-switch.spec.ts
tests-browser/direction.spec.ts
playwright.long-strings.config.ts                (§13.2 scope extension, B1a, M8)
```

**Why `tests/`' three new files and `tests-browser/`'s three new specs are
inside the allowed paths without a scope extension**, since that is the point a
reviewer will check: governing line 150 allows "UI component and browser tests
directly covering internationalization", and these six files cover nothing else.
`playwright.long-strings.config.ts` is a **runner**, not a test, so line 150 does
not reach it — hence §13.2.

### 11.2 Deleted

```
app/layout.tsx          app/page.tsx
```

### 11.3 Modified

Per-file, per-range. Directory-level entries are not used: a directory in a
manifest cannot be reviewed, and `m21` requires the precision everywhere else in
§11 to hold here too.

| Path | Change |
| --- | --- |
| `next.config.ts` | `+ redirects()` (D-I18N-01b) **and** `+ distDir: process.env.NEXT_DIST_DIR ?? ".next"` so the long-strings build can write to its own directory (B1a). Both are outside the governing allowed-path list — see §13.2.4 request 2, and H8. |
| `.gitignore` | `+ .next-longstrings/` — the long-strings build's `distDir` (B1a). This file moves out of §5.2's frozen list for this one line; see §13.2.4 request 2 part 3 and H8. |
| `app/globals.css` | DC3 (`.skip-link:focus` → `inset-inline-start`) **and `+ @source not "../i18n/**"` plus `@source not "../messages/**"`** (M6 — see the rationale below). |
| `components/app-shell.tsx` | T11–T14, `+ <LocaleSwitcher>` last (D-I18N-11), `+ data-nav-region` |
| `components/primary-nav.tsx` | T15–T20, `+ rtl:` typography, `+ data-nav-region`, `+ locale` prop, `+` rendered-href computation `` `/${locale}` `` (§4.1's frozen-field table, M10) |
| `components/mobile-nav.tsx` | T21–T24, DC7, DC8, `+ locale` prop, `+ data-nav-region="mobile"` on the `<nav>` and `data-nav-region="mobile-trigger"` on the `<DialogTrigger>` (M13) |
| `components/workflow-timeline.tsx` | T25–T26, F01–F02, fixture `<bdi>`, `+ locale` prop, `+ rtl:` typography |
| `components/evidence-chain.tsx` | T31–T35, F03, DC4–DC6, DC5, fixture `<bdi>`, `+ locale` prop, `+ rtl:` typography |
| `components/status-badge.tsx` | T27–T30, `+ locale` prop, `+ rtl:` typography |
| `components/locale-document.tsx` | new file, §11.1 |
| `GATES.md` | new gate rows; human rows stay `NOT_VERIFIED`; **restate gate 21(a)/(b) coverage to name `app/` recursively** (M5); **add the contrast-coverage pointer** replacing the phantom `evidence-contrast.spec.ts` (M2); **add the `@source not` rationale line for `i18n/` + `messages/`** (M6); add the §3.1 ratification record (§16 rows H1–H6 and H8 stay `NOT_VERIFIED`) |
| `tests/home-page.test.tsx` | §12 rows |
| `tests/shell.test.tsx` | §12 rows — including **201–202 extended to all three locales** (M10) and **295–332 relabelled as a metadata-table assertion** (M14) |
| `tests/keyboard-traversal.test.tsx` | §12 rows |
| `tests/accessibility-in-process.test.tsx` | §12 row |
| `tests/workflow-timeline.test.tsx` | §12 row |
| `tests/evidence-chain.test.tsx` | §12 row |
| `tests/status-badge.test.tsx` | §12 row |
| `tests-browser/helpers.ts` | §13.1 rows — **104–114 modified as a whole range** (M4) |
| `tests-browser/tab-order.spec.ts` | §13.1 rows — **35 added**, 40, 44, 53, 56 (M3, M13) |
| `tests-browser/responsive-nav.spec.ts` | §13.1 rows — 30, 31, 40, 41, 52 (M13 adds the trigger locators) |
| `tests-browser/focus-visibility.spec.ts` | §13.1 rows |
| `tests-browser/screenshots.spec.ts` | §13.1 rows — 46–71, 135 |
| `tests-browser/rendered-axe.spec.ts` | §13.1 rows — **279 trigger locator** (M13); 224/276/316 gain `/fr`, `/ar`, `/de` |
| `tests-browser/overflow.spec.ts` | §13.1 rows — 29, 64; also the recipe AC-9 reuses |
| `tests-browser/hygiene.spec.ts` | §13.1 rows — **93–103 `sourceFiles()` made recursive** (M5), 293, 399 |

**M6 — why `app/globals.css` gains two `@source not` directives.** This
application has **no `tailwind.config.*`**; it is pure Tailwind v4 CSS-first auto
source detection, whose scanner reads *every* non-excluded file under the app
root as a candidate class-name source. The four existing directives at
`app/globals.css:57-59` exclude `../../**/*.md`, `../tests/**` and
`../tests-browser/**` (three directives, plus the fourth the file's own
arithmetic comment at lines 42–48 subsumes). What is **not** excluded is
`i18n/**/*.ts` and `messages/**/*.ts` — 14 new files whose entire content is
natural-language strings. A catalog word that collides with a utility name
(`table`, `inline`, `hidden`, `contents`, `sr-only`, `outline`, `truncate`, `grid`,
`flex`, …) is harvested into real CSS, and the consequence is measured and
specific: `hygiene.spec.ts:466-468` computes `unused = emitted - liveAll` and
excludes `COLLATERAL_EMITTED`; a harvested class that is **not** in that
grandfather set fails gate 21(c) with a defect nobody introduced, and a harvested
class that *is* grandfathered silently degrades gate 21(c) by widening the
allow-list. Both outcomes are bad, and the file's own comment at lines 36–40
records that an omission of exactly this kind once "produced no warning, and did
nothing". Adding the two directives is the cheapest correct answer; the
alternative — grandfathering whatever the catalogs happen to harvest — is
strictly worse. The new directives use the same `../`-relative-from-`app/`
spelling the file's arithmetic comment demands, and their prose must be added to
the same comment block so the arithmetic comment does not become false.

---

## 12. Vitest changes (each individually justified)

No assertion may be deleted or loosened. Every edit below names the invariant it
protects.

| File | Line | Change | Individual justification |
| --- | --- | --- | --- |
| `tests/home-page.test.tsx` | 4-5 | import `LocaleDocument` + `OverviewPage` | route moved to `app/[locale]/`; `RootLayout` is now async (D-I18N-01a) |
| `tests/home-page.test.tsx` | 51 | `getByText(\`Latest: ${lastEvent}\`)` → a function matcher on the `<p>`'s `textContent` **plus** an assertion that a `<bdi>` wraps the fixture value | D-I18N-02 requires the fixture value to be its own node; `getNodeText` joins only direct text children. The full sentence is still asserted exactly, and the isolation is now asserted too — strictly stronger |
| `tests/shell.test.tsx` | 7-8 | imports | as above |
| `tests/shell.test.tsx` | 201-202 | `expect(hrefs).toEqual(["#main-content","/"])` → a **per-locale** exhaustive array, asserted for **all three** locales by looping `SUPPORTED_LOCALES` and rendering with `currentPath={`/${locale}`}`: `` [`#${MAIN_CONTENT_ID}`, `/${locale}`, ...SUPPORTED_LOCALES.map((code) => `/${code}`)] `` — five entries: skip link, rendered Overview href, then the three selector hrefs in `SUPPORTED_LOCALES` order | D-I18N-01: the root route is now a redirect and nav hrefs are locale-prefixed. The assertion stays exhaustive (`toEqual`), so an unexpected href still fails. **M10:** this is only satisfiable because §4.1's frozen-field table derives the rendered Overview href from `` `/${locale}` `` at render while `PRIMARY_NAV_ITEMS[0].href` stays `"/"`. Asserting all three locales — not just `en` — is what stops the sentinel from being rendered bare on `fr`/`ar` later. If `LocaleSwitcher` calls `usePathname()` directly (D-I18N-10), the vitest file mocks `next/navigation`; the *expected hrefs* are the same either way, because `currentPath` and `usePathname()` agree under the mock. |
| `tests/shell.test.tsx` | 279 | `toEqual(["Primary","Primary (mobile menu)"])` → the **three** per-locale names (`catalog[locale]["nav.landmark.primary"]`, `…["nav.landmark.primaryMobile"]`, `…["locale.selectorLabel"]`), asserted **per locale**, **plus** `new Set(names).size === names.length` **per locale** | a third `navigation` landmark exists; `landmark-unique` requires distinct names. **M13:** a single-`en` assertion does not test the thing the rule is about — three *translated* names that stay mutually distinct. The old line 280 uniqueness check becomes per-locale, otherwise `fr` could ship `Primaire`/`Primaire (menu mobile)`/`Language` and go un-noticed only if two collided. |
| `tests/shell.test.tsx` | 295-332 | the metadata/`DOCUMENT_LANG` block → per-locale: `resolveLocale` table, `LOCALE_METADATA[locale].lang`/`dir` for all three, and `await generateMetadata({ params: Promise.resolve({ locale }) })` asserting the localized description. **M14 — relabelled honestly: this block asserts the per-locale METADATA TABLE, nothing more.** It does **not** assert that `<html lang dir>` reaches the document, and it cannot: React omits `<html>`/`<body>` when a root layout is mounted into a container `div`, and this file's own `runAxeOnRealDocument` helper transplants the children and *mirrors* `lang` from an exported constant — so the real document's `lang` is a value the test supplied, not one the render produced. The **only** assertion that `<html lang dir>` actually ships is AC-2's `fetch` of the **initial HTML response body** in `locale-routing.spec.ts` (§14). | `DOCUMENT_LANG` as a constant is exactly what D-I18N-01a removes; the block now pins `lang`+`dir` for all three locales in `LOCALE_METADATA`, and is labelled as the weaker of the two layers rather than being allowed to read as the stronger one (`GATES.md` §4.2 records the container-render limitation). |
| `tests/shell.test.tsx` | 118, 172-193, 210-213 | **no change** | English catalog values are byte-identical to `PRIMARY_NAV_ITEMS[].label` and `UNAVAILABLE_NAV_TEXT`; the pin is asserted in `i18n-catalog.test.ts`. **M13 scope limit, stated:** these rows stay `en`-only on purpose — they assert the English *wording* pin, not locale behaviour. The per-locale accessible-name and mutual-distinctness assertions for the three `navigation` landmarks are added at line 279, which is the row that can carry them without turning an English-byte-pin into a translation assertion. |
| `tests/keyboard-traversal.test.tsx` | 6-7 | imports | as above |
| `tests/keyboard-traversal.test.tsx` | 134-138 | union array gains the three locale links, in DOM order | D-I18N-11: new focusable controls. Deliberately *extended*, never narrowed — this is the UI-00 tripwire |
| `tests/keyboard-traversal.test.tsx` | 176-189 | **no change** | D-I18N-12 keeps the selector out of page content |
| `tests/accessibility-in-process.test.tsx` | 6 | import `OverviewPage` | route moved; add `locale="en"` |
| `tests/workflow-timeline.test.tsx` | 4/渲染 | add `locale="en"` | D-I18N-05 required prop |
| `tests/evidence-chain.test.tsx` | 4 | add `locale="en"` | as above |
| `tests/status-badge.test.tsx` | 4 | add `locale="en"` | as above |

Unchanged and expected to pass as-is (English values pinned):
`evidence-chain.test.tsx:15,23,33,34`, `workflow-timeline.test.tsx:19,33,34,41,50,63`,
`status-badge.test.tsx:21,24,39`, `home-page.test.tsx:29,39,49,50,64`,
`shell.test.tsx:51-124,132,169-266,349-423`.

---

## 13. Playwright changes (each individually justified)

### 13.1 Existing specs

| File | Line | Change | Justification |
| --- | --- | --- | --- |
| `helpers.ts` | **104–114 (whole range)** | `measureTabRing(page, presses = 8, locale = "en")`; `await page.goto("/")` → `` await page.goto(`/${locale}`) ``. The **whole range** is MODIFIED, not just line 105, because the signature itself changes (M4). | **M4.** The helper *navigates internally* and took no locale. With `redirects()` in place (D-I18N-01b) `goto("/")` lands on `/en` via a 307, so any future `fr`/`ar` ring test would measure **English** — and it would pass, because the English ring is the expected ring. That is a silent wrong-language measurement, not a failure, which is the worst failure mode available. A locale parameter makes the ring's language an explicit input. |
| `helpers.ts` | 104–114 | non-vacuity guard added inside the helper, immediately after the `goto`: read `document.documentElement.lang` and `throw` unless it equals `locale`. | The default `locale = "en"` is a convenience, not a safety net, and a default alone would leave the original defect reachable by omission. The guard makes "measured the wrong language" a **loud** error inside the helper rather than a green assertion downstream. `tab-order.spec.ts` gains the matching assertion that `html[dir]` is `rtl` for the `ar` ring. |
| `helpers.ts` | 79 | `closest('nav[aria-label="Primary"]')` → `closest('nav[data-nav-region="primary"]')` | D-I18N-10: an English-string selector silently stops matching in `fr`/`ar`, which would make `tab-order.spec.ts:39` a **vacuous pass** |
| `tab-order.spec.ts` | **35** | `expect(order).toEqual(["a:Skip to main content", "button:Open main navigation"])` → the five-stop array `["a:Skip to main content", "button:Open main navigation", "a:English", "a:Français", "a:العربية"]` | **M3 — this line was previously absent from §13.1 entirely.** It exists, it will change, and the change is caused by the switcher being visible at 375px (D-I18N-11). Pinned as **literal strings**, including the Arabic endonym `"a:العربية"` as a JS string literal, for the same reason `MOBILE_NAV_TRIGGER_LABEL` and the screenshot filenames are pinned byte-for-byte. |
| `tab-order.spec.ts` | 40 | same locale-stable hook (`nav[data-nav-region="primary"]`) | as above |
| `tab-order.spec.ts` | 44, 53 | expected 1440px ring grows from two stops to five: `["a:Skip to main content", "a:Overview", "a:English", "a:Français", "a:العربية"]` | D-I18N-11; assertion extended, not weakened. The `expect(ring.some((stop) => stop.inPrimaryNav)).toBe(false)` companion at line 39 is kept and now also covers the three locale links (`inLocaleNav` via `nav[data-nav-region="locale"]`), because a locale link must **not** be inside the primary nav. |
| `tab-order.spec.ts` | 56 | `page.getByRole("button", { name: "Open main navigation" })` → `page.locator('[data-nav-region="mobile-trigger"]')` | **M13.** This row will run against `/fr` and `/ar` in future; an English accessible-name locator there is a time-out, not a match. Listed rather than left implicit. |
| `tab-order.spec.ts` | 31, 49 | pass `measureTabRing(page, 8, "en")` explicitly | M4 — the call sites are MODIFIED even though the default would keep them green, so the ring's language is stated at every call site instead of relied upon. |
| `responsive-nav.spec.ts` | 30, 40 | locale-stable hook | as above |
| `responsive-nav.spec.ts` | 31, 41, 52 | `getByRole("button", { name: "Open main navigation" })` (and `helpers.ts:27`'s `MOBILE_NAV_TRIGGER_LABEL`) → `[data-nav-region="mobile-trigger"]` | **M13.** Same class of English accessible-name locator; `screenshots.spec.ts` and `rendered-axe.spec.ts` are enumerated separately below because they will run against non-English routes. |
| `responsive-nav.spec.ts` | 56-57 | **no change** (two Tabs → trigger at 375px) | D-I18N-11 chose the DOM position precisely so this measured count stays valid |
| `focus-visibility.spec.ts` | 26 | `PRIMARY_NAV_LINK = 'nav[aria-label="Primary"] a[href]'` → `'nav[data-nav-region="primary"] a[href]'` | as above |
| `focus-visibility.spec.ts` | 27 | **no change** — `MOBILE_TRIGGER = "[aria-controls='mobile-primary-nav']"` is already locale-stable, because `aria-controls` is an id, not a name | recorded so a reviewer does not "fix" a line that is already correct |
| `focus-visibility.spec.ts` | 110,158,186,216,236 | `goto("/")` → `goto("/en")` (line 186, 216 and 236 are inside tests that call `page.goto` **themselves** and never use `measureTabRing`, so M4's helper change does **not** rescue them) | as above |
| `focus-visibility.spec.ts` | 181-224 | add an `ar` case covering the nav link, the trigger and each locale link | N18 |
| `screenshots.spec.ts` | 48,62,88,105,122,134 | `goto("/")` → `goto("/en")` | as above |
| `screenshots.spec.ts` | 135 | `getByRole("button", { name: "Open main navigation" })` → `[data-nav-region="mobile-trigger"]` | **M13 — load-bearing, not cosmetic.** This is the capture behind §15.1's `375-mobile-ar.png`, i.e. an `ar` route. Left as-is it would time out on the English label and take the DC7/DC8 panel-edge evidence with it. |
| `screenshots.spec.ts` | 46-71 | keep `375-overview.png` / `1440-overview.png` filenames **byte-stable**; add the new locale captures under **new** names (`375-overview-fr.png`, `375-overview-ar.png`, `1440-overview-ar.png`) | the existing UI-01c artefacts are PR evidence; renaming them would destroy the comparison baseline (there is no `toHaveScreenshot` baseline — 0 usages — so no visual-diff break) |
| `rendered-axe.spec.ts` | 224,276,316 | `goto("/")` → `goto("/en")` + add `/fr`, `/ar` and `/de` (404) cases | N17, N20 |
| `rendered-axe.spec.ts` | **279** | `page.getByRole("button", { name: MOBILE_NAV_TRIGGER_LABEL })` → `page.locator('[data-nav-region="mobile-trigger"]')` | **M13.** The §13.1 addition of `/fr` and `/ar` axe cases (line 224) each need the dialog-open variant to run in the locale under test; with the English label they would time out on `fr`/`ar`. This line is the exact locator the review named and it was **unlisted**. |
| `overflow.spec.ts` | 29,64 | `goto("/")` → `goto("/en")` + add `/fr`, `/ar` cases | N16 |
| `hygiene.spec.ts` | 293,399 | `goto("/")` → `goto("/en")` | as above |
| `hygiene.spec.ts` | **93–103 `sourceFiles()`** | make the walk **RECURSIVE** (or, as the minimal equivalent, add `"app/[locale]"` to the `for (const dir of …)` list at line 95 and drop the `if (!entry.isFile()) continue;` early-`continue` for directories) | **M5.** `sourceFiles()` uses a **non-recursive** `readdir` with `if (!entry.isFile()) continue;`. Once §11.2 deletes `app/layout.tsx` and `app/page.tsx` and §11.1 creates `app/[locale]/{layout,page,not-found}.tsx`, the `app/` branch contributes **only** `globals.css` — so gate 21(a) (dangling `var(--token)`) and gate 21(b) (raw-palette utility in `.tsx`) would both go **vacuous for the new layout**, while gate 21(a)'s own assertion message at `hygiene.spec.ts:376` still claims "every `var(--token)` in `app/` or `components/`". A raw-palette utility in `app/[locale]/*.tsx` would then pass gate 21(b) silently. Recursion is preferred over listing the directory by hand because a *future* subdirectory would then be caught automatically rather than needing another packet. |
| `hygiene.spec.ts` | 96-99 scan roots | confirm the token/utility scans cover `app/` (**recursively, including `app/[locale]/`**) + `components/`, and that `i18n/` + `messages/` are outside them | new catalog files must not be scanned for class-name hygiene (they contain no classes). The recursion change above is what makes "`app/[locale]/` **is** scanned" true rather than aspirational. |
| `hygiene.spec.ts` | `COLLATERAL_EMITTED` set | **must not gain any `i18n/`- or `messages/`-derived class** | **M6.** `hygiene.spec.ts:466-468` computes `unused = emitted - liveAll` and excuses `COLLATERAL_EMITTED`. If the catalogs are left as Tailwind sources (§11.3's two new `@source not` directives are omitted or misspelled), a harvested class fails gate 21(c) as an unexplained defect; if it is *added* to the allow-list, the guard is silently degraded. The set is a UI-01c grandfather list and must stay one. |

### 13.1a Contrast coverage — corrected (M2)

**`tests-browser/evidence-contrast.spec.ts` does not exist and never did.**
`tests-browser/` contains exactly: `focus-visibility.spec.ts`, `helpers.ts`,
`hygiene.spec.ts`, `overflow.spec.ts`, `rendered-axe.spec.ts`,
`responsive-nav.spec.ts`, `screenshots.spec.ts`, `tab-order.spec.ts`. The old
§13.1 row and old §18 item 2 that named it are **deleted**, not repaired.

The real contrast coverage for this packet is:

| Coverage | Where | What it asserts |
| --- | --- | --- |
| Rendered-CSS contrast, all three locales | `tests-browser/rendered-axe.spec.ts` — the `AXE_CONTRAST_RULE_ID` (`color-contrast`) non-vacuity assertions at lines 267-270 (closed) and 308-311 (dialog open), extended to `/fr` and `/ar` by the §13.1 row at line 224 | `color-contrast` appears in axe's **`passes`** set, not merely absent from `violations`, for each locale. The `incomplete` ledger stays pinned to `[]` with the dialog closed (`EXPECTED_CLOSED_INCOMPLETE`) and to `["aria-hidden-focus(2)"]` with it open. An undecidable contrast node is therefore a red run, not a longer log line. |
| Recorded contrast evidence | `GATES.md` §3.2 (UI-00b: rendered colour contrast, and the two repairs it exposed) and §3.7.1 (UI-01c: contrast re-measured on the new palette, node-by-node with `fgColor`/`bgColor`/`contrastRatio`) | the measured ratios for the three pre-existing thin-margin sites (8.57:1, 9.19:1, 9.19:1 against a 4.5:1 requirement) |
| What this packet adds | `I18N.md` §"Translation boundary" + the `fr`/`ar` screenshots | the Arabic **12px label sites** after the §9.1 size/tracking adaptation, and the translated body copy. Colour and font-size are inherited and unchanged by `<bdi>` insertion, so the CSS-only reasoning holds — but WCAG AA must be **re-measured for the Arabic glyphs**, not assumed. That re-measurement is the `ar` half of `rendered-axe.spec.ts` plus human row **H4** (§16). |

### 13.2 New specs and the two written scope-extension requests

`tests-browser/locale-routing.spec.ts`, `locale-switch.spec.ts`,
`direction.spec.ts` are within the allowed path ("browser tests directly covering
internationalization", governing line 150).

#### 13.2.1 B1 — the expansion gate as previously formulated was vacuous

The previous version of this packet set `NEXT_PUBLIC_I18N_EXPANSION_PERCENT=30`
in a second `webServer` env and made that run the **only** executable check for
governing criterion lines 228–229. That gate measured nothing:

- Next.js **inlines every `NEXT_PUBLIC_*` reference at build time**. The
  reference is replaced with a literal during compilation, not at request time.
- `playwright.config.ts:62`'s `webServer.command` is `npm run build && npx next
  start -p 3117`, so `.next` already exists and already has `…EXPANSION_PERCENT`
  inlined as `0`.
- `next start` with the env var set therefore serves the **un-inflated**
  catalog. Every assertion passes identically to the normal run, and AC-9 reports
  green while measuring zero expansion.

The fix is both halves below, and both are required: (a) makes the inflation real,
(b) makes a *future* regression in (a) fail loudly instead of quietly.

#### 13.2.2 (a) The long-strings run builds its own, inflated, separate tree

`playwright.long-strings.config.ts` `webServer.command`, **verbatim**:

```ts
command:
  "npm run build && npx next start -p 3121",
```

with the environment block, **verbatim**:

```ts
env: {
  NEXT_PUBLIC_I18N_EXPANSION_PERCENT: "30",
  NEXT_DIST_DIR: ".next-longstrings",
},
```

and `url: "http://localhost:3121"`, `reuseExistingServer: false`,
`timeout: 300_000` (mirroring `playwright.config.ts:57-69`).

Three properties of that command are load-bearing and each is stated so a
reviewer can check it:

1. **It runs `npm run build` itself.** It does not assume `.next` exists and it
   does not attach to the already-built tree. `npm run build` is `next build`
   (`package.json:8`), unchanged — D-I18N-04 holds, `package.json` is byte-frozen.
2. **`NEXT_DIST_DIR=.next-longstrings` puts the output in a *different*
   directory**, so the long-strings build can neither read nor overwrite `.next`.
   A separate port plus a separate `distDir` is deliberate belt-and-braces: the
   port alone would already prevent serving, and the `distDir` alone would
   already prevent clobbering, and the failure this repairs was precisely a build
   shared between two configurations.
3. **`distDir` is therefore an env-read line in `next.config.ts`** — see
   §13.2.4. Without it, `next build` writes to `.next` and this gate is
   vacuous again for the same reason as before.

Because `NEXT_PUBLIC_I18N_EXPANSION_PERCENT` is inlined at build time, the
`env` block must be present for the **build** step. Playwright's `webServer.env`
applies to the whole `command`, so one block covers `npm run build && next
start`. This is stated explicitly because getting it wrong (env on `start` only)
reproduces B1 exactly.

`.next-longstrings` is build output. It must be added to the application
`.gitignore`; that file is currently frozen by §5.2, so it appears in the
§13.2.4 scope-extension request alongside `next.config.ts`.

#### 13.2.3 (b) MANDATORY precondition assertion inside the long-strings spec

Before **any** no-clipping assertion, the long-strings spec fetches the served
markup and asserts the expansion is **real**:

| Step | Assertion | Why it cannot be skipped |
| --- | --- | --- |
| 1 | `fetch` the initial HTML response body (not `page.evaluate`, not the DOM after hydration) for `/en` on the long-strings server | the response body is what `next start` serves; a client-rendered substitute would measure the wrong artifact |
| 2 | extract one catalogued sentence that inflation is guaranteed to lengthen — `overview.traceLede` (T07, `Follow a research claim back to its protocol-bound decision.`) | a **body-prose** sentence, not a short label, so the 30 % filler dominates any incidental whitespace normalisation |
| 3 | assert the served sentence's length is **strictly greater** than the length of `catalog.en["overview.traceLede"]` as compiled from source | "strictly greater", not "at least as long" — an equal length is a non-inflating build |
| 4 | assert the ratio is `>= 1.30` | `>= 30 %` is the governing threshold (lines 228–229); asserting only "longer" would let a 1 % inflation pass |
| 5 | assert the same for `/ar` with an Arabic-script sentence (`overview.asideBody`, T10) | Latin-only proof would not establish the Arabic filler path |
| 6 | `report()` all four numbers (un-inflated length, served length, ratio, locale) to stdout | the run's own output is the report's source — the `GATES.md` convention |

A non-inflating build fails **here**, loudly, with the numbers printed — before
any clipping assertion is evaluated, so a vacuous pass is impossible. This
precondition is recorded as its own acceptance row (**AC-9P**, §14) and its own
`pr` gate row (§15). It is **not** merged into AC-9's row: it is a precondition
of AC-9 being meaningful, and collapsing the two would let a future reviewer read
"AC-9 green" without noticing the gate measured the wrong build.

#### 13.2.4 Written scope-extension requests (governing line 156)

Both files below are outside the governing allowed-path list (lines 145–154).
Governing line 156 provides exactly one mechanism — "Any additional path
requires a written scope-extension reason before editing" — and both requests
use it. Both are escalated as **H8** (§16).

**Request 1 — `playwright.long-strings.config.ts` (new runner).**

*Reason.* Acceptance lines 228–229 mandate a ≥30 % expansion gate, and
`playwright.config.ts` declares a single `webServer` whose `command` is
`npm run build && npx next start -p 3117` against `.next`. The inflated build
needs a second server on a different port **and a separate `distDir`** (§13.2.2),
because `NEXT_PUBLIC_*` is inlined at build time and reusing `.next` makes the
gate vacuous (B1). Mutating the shared `playwright.config.ts` instead would put
every one of the 25 existing specs at risk and would make the shared config
locale- and build-variant-dependent, which is exactly the kind of implicit state
this application's runner design has been audited for. A separate config keeps
the normal run byte-identical. `package.json` is **not** touched (D-I18N-04); the
gate is invoked explicitly:

```
npx playwright test -c playwright.long-strings.config.ts
```

**Request 2 — `next.config.ts`.**

*Reason, part 1 — the redirect.* D-I18N-01b mandates `GET /` → `/en`. This
cannot be expressed inside the allowed `apps/research-ui/app/` or
`apps/research-ui/components/` paths. The three in-app alternatives were
evaluated and rejected:

| Alternative | Rejected because |
| --- | --- |
| `app/page.tsx` issuing `redirect()` | `app/page.tsx` is **deleted** by §11.2 (D-I18N-01a: the route moves to `app/[locale]/page.tsx`, and a static `/page.tsx` **cannot coexist** with `app/[locale]/page.tsx` — Next rejects two routes resolving to `/`). The redirect would have to live in `app/[locale]/page.tsx`, which would then 307 on *every* locale request. |
| A second root layout at `app/layout.tsx` | Requires a `<html>` at a static segment AND a `<html>` at `app/[locale]/`, i.e. two root layouts. Next permits one. D-I18N-01a's hard gate (`BLOCKED_UPSTREAM_ROUTING`) is already the riskiest assumption in the packet; doubling the root layouts raises it rather than lowering it. |
| `middleware.ts` / `proxy.ts` | Rejected on the merits by D-I18N-01b: it is framework-version-dependent, runs inside the request pipeline rather than statically, and this packet's own discipline forbids a new runtime layer for a static mapping. |

So the redirect needs `redirects()`, and `redirects()` is `next.config.ts`.

*Reason, part 2 — `distDir`.* §13.2.2(3): the long-strings build must write to
`.next-longstrings`, which requires `distDir: process.env.NEXT_DIST_DIR ??
".next"` in the same file. This is **not** a second, separate request; it is the
same line of reasoning as Request 1, and it is stated here so the reviewer sees
that `next.config.ts` is needed for *two* independent reasons, either of which
alone would justify it.

*Reason, part 3 — `.gitignore`.* `.next-longstrings/` is new build output in a
directory the existing `.gitignore` does not list (it lists `.next/`). Leaving it
untracked-but-visible would pollute `git status` and the ladder step 5 check
(`README.md:89`). `AGENTS.md`'s "Definition of done" requires "No protected path
outside `apps/research-ui/` changed" — this stays inside it.

**None of these three edits may be made before this packet's review records a
decision.** D-I18N-01b's reasoning is otherwise sound and its ruling —
`redirects()`, not middleware — is **CORRECT and preserved unchanged**.

---

## 14. Acceptance mapping

Every governing acceptance criterion (lines 212–229) mapped to code and an
executable check.

| # | Criterion (governing text) | Code | Executable check |
| --- | --- | --- | --- |
| AC-1 | Direct navigation and refresh work for the same overview in all three locales; unsupported locales produce the documented refusal/not-found path | D-I18N-01, 01a, 01b, 13 | `locale-routing.spec.ts`: `goto` + `reload()` on `/en`,`/fr`,`/ar` all 200 with the right chrome; `/de`,`/EN`,`/en-US`,`/fr-FR`,`/ar-EG` → 404 + catalog text |
| AC-2 | `<html>` exposes correct `lang` and `dir` **before hydration** | `LocaleDocument` (`app/[locale]/layout.tsx`) | `locale-routing.spec.ts` asserts `html[lang]`/`html[dir]` from the **initial HTML response body** (`fetch`, not `page.evaluate`), for `/en`, `/fr`, `/ar`, plus N15's no-hydration-error check. **This is the ONLY assertion in the packet that proves `<html lang dir>` actually ships.** The `shell.test.tsx` metadata block (§12) is explicitly *not* that assertion — see §12's M14 row and `GATES.md` §4.2. |
| AC-3 | All existing shell and overview interface strings come from catalogs; tests fail when a required key is removed from any locale | §4.1/§4.2 catalogs, N8, N9 | `i18n-catalog.test.ts` (key parity + N3 removal throw + N9) and `i18n-render.test.tsx` (N8) |
| AC-4 | Catalog key sets are mechanically identical across `en`, `fr`, `ar` | D-I18N-03 | `tsc` (`Record<MessageKey, string>`) **and** `i18n-catalog.test.ts` key-set equality |
| AC-5 | The selector announces purpose, current selection and options; switching preserves the equivalent route | D-I18N-06, 10, 11 | `locale-switch.spec.ts`: `nav` accessible name equals `locale.selectorLabel`, `aria-current="true"` only on the active link, each link's accessible name is its endonym, keyboard `Tab`/`Enter` reaches and activates each, target URL is the same route in the other locale |
| AC-6 | Arabic shows a genuinely mirrored reading flow without reversed identifiers, numbers, directional icons or broken focus order | D-I18N-02, 08, 09 + `direction.spec.ts` | `direction.spec.ts` (N19), N11 (no mirroring), and the `ar` focus case in `focus-visibility.spec.ts` (N18) |
| AC-7 | Demo-data disclosure visible and correctly translated in every locale | T13 `safety.demoDataLabel` | `i18n-render.test.tsx` asserts `translate(locale,"safety.demoDataLabel")` is rendered in `en`,`fr`,`ar`; `rendered-axe.spec.ts` all three locales |
| AC-8 | UI-00b guarantees retained: visible focus, AA contrast, no horizontal overflow, functional skip link, dialog focus trap, correct focus restoration | §9 + no change to `AppShell`/`MobileNav` structure | existing `shell.test.tsx` (unchanged assertions), `rendered-axe.spec.ts` (all locales, incl. the `color-contrast` non-vacuity assertion), `overflow.spec.ts` (all locales + expansion), `focus-visibility.spec.ts` (all locales), `responsive-nav.spec.ts` (unchanged press counts) |
| **AC-9P** | **Precondition for AC-9 (B1b, new row):** the 30 %-expanded build the AC-9 run measures **actually is** 30 % expanded. | D-I18N-15, §13.2.2, §13.2.3 | `playwright.long-strings.config.ts`'s own `webServer.command` (`npm run build` with `NEXT_PUBLIC_I18N_EXPANSION_PERCENT=30` and `NEXT_DIST_DIR=.next-longstrings`), **plus a mandatory first test** in the long-strings spec: `fetch` the initial HTML response body for `/en` and `/ar`, extract `overview.traceLede` (T07, Latin) and `overview.asideBody` (T10, Arabic script), assert each served sentence is **strictly longer** than its `catalog.en`/compiled source counterpart and at ratio `>= 1.30`, and `report()` all four numbers. Runs **before** any no-clipping assertion and fails loudly with the numbers printed. Without this row, AC-9 below is vacuous by construction, because `NEXT_PUBLIC_*` is inlined at build time and an un-inflated `.next` would satisfy every clipping assertion identically. §15's `pr` rows carry both halves. |
| AC-9 | 30 %-expanded strings do not clip navigation, state labels, headings or controls at 375 and 1440 | D-I18N-15, **gated by AC-9P** | `playwright.long-strings.config.ts` + a focused spec asserting **no clipping** for the nav, state stamps, headings and the locale selector at 375 and 1440, in `en` and `ar`. **The assertion is the `overflow.spec.ts` recipe, not a per-element `scrollWidth <= clientWidth`** (M7): `documentElement` **strict** `<=`, `body`/`<main>` `<= clientWidth + 1`, plus the existing unbreakable-token probe `[^\s]{24,}`. See the two exclusions below. |
| AC-10 (governing Gate) | `npm run typecheck`, `npm test`, `npm run build`, `npm run test:browser`; browser coverage of all three locales, both directions, unsupported-locale behavior, selector keyboard use, refresh/deep link, catalog completeness, 30 % expansion; 375px shots for `en`/`fr`/`ar` and 1440px for `en`/`ar`; human review | §15, §16 | §15 gate table + `GATES.md` ledger rows |

#### 14.1 AC-9 — what is asserted, and what is explicitly out of scope (M7)

The governing criterion says strings must not **clip navigation, state labels,
headings or controls**. The previous version of this packet specified
`element scrollWidth <= clientWidth`. That is wrong here for two independent
reasons, and both are recorded rather than quietly replaced:

1. **It contradicts this suite's own documented rule.** `overflow.spec.ts:10-14`
   states it outright: "sub-pixel rounding of fractional layout widths is not a
   scrollbar, and asserting a strict `<=` against it would be a flaky assertion
   dressed up as a strict one." That is why `body` and `<main>` carry a 1px
   tolerance at lines 52-53 while `documentElement` is strict at 49-51. AC-9 was
   specifying a stricter rule for the same measurement than the suite it
   reuses.
2. **On the named elements it measures nothing at all.** At 375px `PrimaryNav`
   is `hidden lg:block` (`components/primary-nav.tsx:104`); at 1440px
   `MobileNav`'s panel is `lg:hidden`. A `display: none` element has
   `clientWidth === 0` **and** `scrollWidth === 0`, so `0 <= 0` is true. An
   assertion over "the nav, the state stamps, the headings and the selector" at
   *both* widths necessarily includes a hidden element at each width, and a
   strict per-element check passes on the hidden one for free. This is the same
   vacuity the packet already guards against everywhere else
   (`rendered-axe.spec.ts`'s `panel.toBeVisible()` before an axe run,
   `hygiene.spec.ts` gate 21(c), `N8`'s presence direction).

**Decision — per-element clipping checking is OUT OF SCOPE for this packet**, and
the element-level requirement is met by two things that are both real:

- **viewport-level measurement at 30 % expansion in `en` and `ar`, at 375 and
  1440**, with `documentElement` strict. A clipped label cannot exist without the
  box growing, so a document that does not scroll sideways at 375px cannot be
  clipping anything. This is the same inference `overflow.spec.ts` already makes
  and records at line 7 ("nothing in the in-process suite can see a sideways
  scrollbar").
- **the H3 human screenshot gate** (§16), which sees the rendered glyphs, at
  `375-overview-long.png` / `1440-overview-long.png` (§15.1). Automated capture
  is not approval; a reviewer looking at an Arabic label at 375px is the check
  that actually distinguishes "wrapped acceptably" from "clipped".

If a later packet wants element-level measurement, the precondition is stated
here so it is not rediscovered: an element-level check is admissible **only**
when it is guarded on (a) the element being **visible** (`offsetParent !== null`,
not merely `clientWidth !== 0`, because a zero-width *visible* element is
possible) **and** (b) the element actually being a **clipping container**
(`overflow`/`overflow-x` in `hidden|clip|scroll|auto`). Absent (a) the check is
vacuous; absent (b) `scrollWidth` measures intrinsic content width rather than
clipping and will fail for reasons unrelated to clipping.

---

## 15. Gates (exact commands, run from `apps/research-ui/`)

### 15.0 Gate-convention provenance — why §15 is hand-written

**Recorded reason:** `docs/architecture/test_gate_manifest.json` has **no entry
for `apps/research-ui/**`** (verified on `8ba4fb6`: zero occurrences of
`research-ui` in that file), so the machine-readable selector cannot choose a
gate for any path in this application:

```
uv run python scripts/select_test_gate.py --path apps/research-ui/app/page.tsx --stage inner
ERROR: no task selected; pass --task or a path matching the manifest
```

The stage labels used below — `inner`, `checkpoint`, `pr` — are the **policy's
own vocabulary** (`docs/architecture/test_gate_policy.md`'s table: `inner`
"after an executable edit", `checkpoint` "a task … is complete", `pr` "the final
executable candidate is ready to publish"), and each row's content is correct
lane practice for this application. And
`../architecture/research_ui/README.md:91` explicitly exempts this application
from the Python full suite ("The UI does not require the Python full suite until
a Python API boundary is introduced"), so there is no Python gate to select
either.

The divergence is therefore **recorded, not hidden**: the commands below are
hand-written because the machine-readable selector has no manifest entry for this
application, not because the selector was bypassed. A reviewer re-running
`select_test_gate.py` will get the same error and should read this row as the
answer. **This packet does not modify `test_gate_manifest.json`** — that is a
harness-level conformance artifact outside `apps/research-ui/`, and adding to it
belongs to whoever owns the E3 manifest. Recorded here as a follow-up candidate
rather than silently divergent.

### 15.0.1 The gate table

| Stage | Command | Expectation |
| --- | --- | --- |
| inner (during edit) | `npm run typecheck` | 0 errors — the primary structural gate for catalog parity and required-prop wiring |
| inner | `npm test -- tests/i18n-catalog.test.ts tests/i18n-render.test.tsx tests/i18n-direction-source.test.ts` | new suites green |
| inner | `npm test -- tests/shell.test.tsx tests/home-page.test.tsx tests/keyboard-traversal.test.tsx tests/workflow-timeline.test.tsx tests/evidence-chain.test.tsx tests/status-badge.test.tsx tests/accessibility-in-process.test.tsx` | edited suites green |
| checkpoint | `npx playwright test tests-browser/locale-routing.spec.ts tests-browser/locale-switch.spec.ts tests-browser/direction.spec.ts` | new specs green |
| checkpoint | `npx playwright test tests-browser/tab-order.spec.ts tests-browser/responsive-nav.spec.ts tests-browser/focus-visibility.spec.ts tests-browser/overflow.spec.ts tests-browser/rendered-axe.spec.ts tests-browser/screenshots.spec.ts` | re-measured focus rings / axe / overflow; screenshot files written |
| pr | `npm run build` | production build succeeds; `/` → `/en` present in the build manifest |
| pr | `npm test` | `>= 7` files, `>= 53` tests, 0 failures — **and** the name-level diff below |
| pr | `npm run test:browser` | `>= 7` specs, `>= 25` tests, 0 failures — **and** the name-level diff below |
| pr | `npx playwright test -c playwright.long-strings.config.ts` | **AC-9P first**: the precondition test proves the served `/en` and `/ar` sentences are `>= 1.30×` their un-inflated source lengths, printing all four numbers. Then **AC-9**: no sideways overflow at 375/1440 in `en` and `ar` using the `overflow.spec.ts` recipe (§14.1). A green run in which the precondition did not execute is not a pass — the precondition is a separate `test()` so it cannot be skipped by a filter. |
| pr | `git diff --stat -- package.json package-lock.json lib/mock-project.ts lib/contracts.ts` | empty (D-I18N-02, D-I18N-04) |

Record each row in `GATES.md` with its real output. Rows that cannot be executed
in this environment stay `NOT_VERIFIED` with the reason — never a claim.

### 15.0.2 Anti-swap name-level diffs (m19)

The `>= 7 files / >= 53 tests` and `>= 7 specs / >= 25 tests` floors are correct
and non-shrinking — they match the recorded UI-01c baseline
(`GATES.md:245`, `:709`, `:711`). **A count floor cannot detect one test deleted
and one added**, and this packet adds many tests across many files, which is
exactly the change shape a count would hide. `GATES.md` already records the
per-spec-file arithmetic (`GATES.md:236-249`) and states the UI-01c no-swap
position explicitly; this packet inherits that and adds the mechanical check.

Run both, from `apps/research-ui/`:

```
npx vitest run --reporter=verbose 2>&1 | grep -E '^\s+[✓×]' | sort > /tmp/ui01d-vitest-names.txt
npx playwright test --list 2>&1 | grep -E '^\s+\[chromium\]' | sort > /tmp/ui01d-playwright-names.txt
```

| Check | Command | Expectation |
| --- | --- | --- |
| Vitest anti-swap | `comm -23 <UI-01c test-name list> /tmp/ui01d-vitest-names.txt` | **empty.** Every test name that existed on `8ba4fb6` still exists. A renamed test appears here as one removal plus one addition, so the diff is on **names**, not counts. |
| Playwright anti-swap | `comm -23 <UI-01c spec-name list> /tmp/ui01d-playwright-names.txt` | **empty.** Same property over `playwright test --list` output. |
| Deletion ledger | `GATES.md` | every name in either `comm -23` output that is *intended* to be removed is listed individually in §12 or §13.1 with its justification. §12's opening rule ("no assertion may be deleted or loosened") and the packet's baseline table ("no pre-existing assertion is deleted or weakened without an individual justification recorded in §12") remain the governing statement; these two commands make it checkable rather than asserted. |

The UI-01c baseline name lists are **regenerated from `8ba4fb6`**, not copied
from prose: `git stash`-free, use `git show 8ba4fb6:apps/research-ui/…` into a
temporary directory and run the two commands there, so the comparison is against
the committed tree and not against anyone's memory of it. Record both files'
contents in `GATES.md`.

**Shell note.** The two pipelines above are POSIX `grep`/`sort`/`comm`. The
repository's own agent shell is Windows PowerShell 5.1, so the equivalents are
`Select-String`, `Sort-Object`, and `Compare-Object -PassThru` /
`Compare-Object -IncludeEqual -ExcludeDifferent`. The **property being checked is
shell-independent**: a name present in the baseline and absent now is a deletion
or a rename, and it must appear in §12/§13.1's justification column. This packet
records the POSIX form because `GATES.md`'s existing evidence blocks are written
in it and the audience reviews diffs in both shells; the implementer uses whichever
their shell provides and must paste the **output** either way.

### 15.1 Screenshots

| Viewport | Locales | Files |
| --- | --- | --- |
| 375px | `en`, `fr`, `ar` | `375-overview.png` (existing name kept), `375-overview-fr.png`, `375-overview-ar.png` |
| 1440px | `en`, `ar` | `1440-overview.png` (existing name kept), `1440-overview-ar.png` |
| 375px | `fr`/`ar` mobile disclosure open | `375-mobile-ar.png` (direction of the panel edge, DC7/DC8) |
| 375px | 30 % expansion | long-strings run: `375-overview-long.png`, `1440-overview-long.png` |

Automated capture is **not** approval (§16).

The `30 % expansion` row's two captures come from the **long-strings config**, and
they therefore carry AC-9P's precondition with them: if the precondition failed,
these files do not exist and the row is `NOT_VERIFIED`, not "captured". The
`375-mobile-ar.png` row is the DC7/DC8 panel-edge evidence and depends on
`screenshots.spec.ts:135`'s locale-stable trigger locator (§13.1) to exist at
all.

---

## 16. Human sign-off (mandatory; agents cannot self-certify)

These rows stay `NOT_VERIFIED` in `GATES.md` until an image-capable/fluent
reviewer signs them. Agents may prepare the evidence and pose the questions; they
may **not** answer them.

| # | Question | Reviewer |
| --- | --- | --- |
| H1 | Is the French wording idiomatic and free of anglicisms? | fluent French reader |
| H2 | Is the Arabic wording idiomatic **and** correct in register for a research tool? | fluent Arabic reader |
| H3 | Do the Arabic screenshots show a genuinely mirrored reading flow, with the correct skip-link corner, panel edge, lineage rail side, and aligned ordinal column? **Do the 30 %-expanded captures (§15.1) clip anything?** — this is the human half of AC-9, since per-element automated clipping checking is out of scope (§14.1). | image-capable reviewer |
| H4 | Are the Arabic 12px label sites legible after the D-I18N-08 size/tracking adaptation? | image-capable reviewer |
| H5 | **Visual/product confirmation of the ALREADY-RATIFIED D-I18N-02** — *not* the open question whether translated chrome may sit beside English fixture content, which is settled (§3.1). The question is whether the result **renders acceptably**: is the `Demonstration data` label legible and correctly translated in Arabic, is the bilingual seam visually honest rather than confusing, and is the caveat visible to a viewer of the `fr`/`ar` screenshots? | product owner |
| H6 | **RQ-1** — ratify D-I18N-07: translating the *display label* of `WorkflowState`/`EvidenceNode.kind` while preserving the canonical tokens as data. | architect |
| H8 | **RQ-3** — ratify the **two** written scope-extension requests in §13.2.4: `playwright.long-strings.config.ts` (new runner) and `next.config.ts` (`redirects()` + `distDir`) plus the one-line `.gitignore` addition. | architect |

**H7 is DELETED (M11), not renumbered — do not renumber H8 to H7.** `H7` asked the
architect to "ratify D-I18N-01c: `I18N.md` in `apps/research-ui/`". That question
is superseded, and superseded *differently from how H5 was superseded*:

- **D-I18N-01c's ratification question is answered by §13.2.4**, not by a new
  human row. D-I18N-01c is a **path divergence** from governing line 154, and
  governing line 156 supplies exactly one mechanism for a path outside the
  allowed list: a written scope-extension reason. §13.2.4 is that reason, and it
  now sits in the same place as the other two path requests, so the architect's
  decision is about *three* paths in one place rather than one path in a
  question table and two paths in a prose paragraph.
- D-I18N-01c's *own* content — the working-tree-only correction to
  `../architecture/research_ui/AGENT_WORK_PACKETS.md` (FU-1 plus the `I18N.md`
  path) — remains explicitly **not** part of this packet's deliverable, still
  **not** staged, and still leaves the untracked `../architecture/research_ui/`
  tree exactly as found. That was never in question and is not escalated.
- **What H7 was mistaken for** is noted so the record is honest: §5 previously
  framed D-I18N-01c as open *and* carried a duplicate of the D-I18N-02 question in
  H5. Both were reviewer-question bookkeeping errors, not unresolved design. The
  gaps are H7's row and §5's framing, both corrected here; the **decisions
  themselves are unchanged and were not redesigned in response.**

A machine gate cannot produce H1–H5. `GATES.md` must show them as
`NOT_VERIFIED` until the signed review exists.

---

## 17. Follow-ups (explicitly out of scope)

1. `metadataBase` + `alternates.languages` (D-I18N-14) — needs a canonical origin.
2. Subtag negotiation (`/fr-FR` → `fr`) and `Accept-Language` — deliberately not
   in this packet; `/fr-FR` is a 404 by design.
3. Per-user remembered locale — must be a cookie or a URL default, never
   `localStorage` only.
4. UI-02…UI-06 localization: adopt `translate(locale, …)`, `Intl`, `<bdi>` and
   logical properties from day one.
5. Dates/timestamps/checksums/DOIs/refusal codes rendering — first appearance
   needs an explicit `Intl` policy for *display* versus byte-exact *display*.
6. `next/font`/font-stack review for Arabic coverage in `globals.css`.
7. Professional translation review and possible catalog version markers.

---

## 18. Could not determine from the allowed inputs

### 18.1 `../architecture/research_ui/README.md` — **WAS READ** (M9)

The previous item 1 here claimed the file "is outside the read set for this
packet" and that "its `known_baseline_failures` ladder check must be reconciled".
**Both statements were wrong**, and they are withdrawn:

| Claim | Fact |
| --- | --- |
| "outside the read set for this packet" | It is **tracked** (`git ls-files ../architecture/research_ui/README.md` returns the path), **present**, **readable**, and **mandatory**: `apps/research-ui/AGENTS.md` Implementation rule 1 is "Read `../architecture/research_ui/README.md` and the assigned work packet". A mandatory input was recorded as absent. It **was read**, and the two sections below are its conformance record. |
| "`known_baseline_failures` ladder check" | **No such field exists** in that file. It has no machine-readable status object at all; its ladder is the five-step prose list at lines 85–89, and its i18n policy is lines 64–75. Reconciling a field that is not there is not possible, and naming one implies the file has a structure it does not have. |

**The two reconciliations that the file's actual content requires:**

| # | Conformance row | README location | Status | Basis |
| --- | --- | --- | --- | --- |
| 18.1a | **Verification ladder step 5** — "Confirm `git diff --name-only` remains inside `apps/research-ui/` unless the packet explicitly includes this architecture folder" | lines 85–89 (step 5) | **SATISFIED — with one recorded exception** | Every UI-01d file is inside `apps/research-ui/` (§11.1–§11.3), so step 5 holds by construction. The single file outside it is `../architecture/research_ui/AGENT_WORK_PACKETS.md`, under D-I18N-01c's **working-tree-only** correction, which is **explicitly never staged, never committed, and never in the PR**, and which leaves the untracked `../architecture/research_ui/` tree exactly as found. The README's own escape hatch — "unless the packet explicitly includes this architecture folder" — is what that correction invokes, and the packet states the exclusion explicitly. **This row is satisfied by construction, not by inspection:** the only executable proof is `git diff --name-only` / `git status --short` showing no staged change under `docs/`, which is a `pr`-stage gate in `README.md:89` terms and belongs in the packet's report, not in its design. |
| 18.1b | **Internationalization policy** — "Non-English catalogs are demonstration translations until a fluent reviewer approves them" | lines 64–75 (the sentence is at line 73) | **PARTIALLY SATISFIED — a required change is added by this packet** | H1/H2 cover the *review* half. They do not cover the *marking* half. Recording the caveat in a decision table is not marking it: the requirement is that the non-English catalogs **be marked** as demonstration translations. So (i) `I18N.md` (§11.1) **carries** the caveat as a visible, named statement — not a footnote in a rationale block — including which keys it applies to and that `brand.productName` and the three endonyms are outside it; and (ii) the `fr` and `ar` screenshots in §15.1 are **presented with** that caveat in the report/PR description, so a viewer of the image sees that the French and Arabic strings have not had a fluent review. The governing packet's own lines 139–141 require the same thing ("they do not claim that translation has been professionally reviewed. Until such review occurs, non-English catalogs must be marked as demonstration translations in developer documentation"), and line 236–238 requires a fluent reviewer — which is H1/H2. Both halves are now separately assigned. |

A **third** item from the same file is already satisfied by existing structure and
is recorded for completeness: `README.md:91` ("The UI does not require the Python
full suite until a Python API boundary is introduced") is why §15 contains no
Python gate, and is the same fact §15.0 records as the gate-convention
provenance.

### 18.2 Remaining unknowns, each with its required executable check

| # | Unknown | Status | Required executable check |
| --- | --- | --- | --- |
| 18.2a | ~~`tests-browser/evidence-contrast.spec.ts` selectors were not enumerated~~ | **RESOLVED — M2. The file does not exist.** Both references (§13.1 and old §18 item 2) are deleted, not repaired. | The real contrast coverage is `rendered-axe.spec.ts`'s `color-contrast` non-vacuity assertion for all three locales, plus the recorded evidence in `GATES.md` §3.2 and §3.7.1. §13.1a is the replacement table. |
| 18.2b | `hygiene.spec.ts`'s exact scan-root list was only partially read | **RESOLVED — M5.** Lines 93–103 were read in full: `sourceFiles()` is a **non-recursive** `readdir` over `["app","components"]` with `if (!entry.isFile()) continue;`, and gate 21(a)'s assertion message at line 376 claims coverage of "`app/` or `components/`". | The recursion change in §13.1 is the check. After `app/layout.tsx`/`app/page.tsx` are deleted and `app/[locale]/*.tsx` created, the non-recursive scan would contribute only `globals.css` from `app/` — verifiable by asserting `sourceFiles()` returns a path containing `app/[locale]/`. `components/overview-page.tsx` **is** already scanned (it is a file directly in `components/`, matched by the existing loop), so route content that moves out of `app/` keeps its guard; the `GATES.md` restatement names `app/` recursively so the gate's own wording matches what it scans. |
| 18.2c | Next 16's tolerance for a root layout at a dynamic segment was reasoned from the framework's documented i18n pattern, not executed here | **HONEST CONCESSION, TIGHTENED (m16).** `app/[locale]/layout.tsx` as document owner **is** the documented Next pattern and `components/locale-document.tsx` is a synchronous composition of it, so the reasoning stands. What was missing is *the symptom to watch*. | **The one observable symptom D-I18N-01a's `BLOCKED_UPSTREAM_ROUTING` gate must catch — exactly two, and either is sufficient:** (1) `npm run build` fails with a prerender error naming `app/[locale]/layout.tsx` (missing `<html>`/`<body>` root, or "a route segment configuration option is not allowed here"), or (2) the build succeeds but the **served response bytes** contain no `<html` element with a `lang` attribute — i.e. AC-2's raw-response-body `fetch` check returns a document whose `documentElement.lang` is `""` or absent. Symptom (2) is the one that matters and it is **silent**: a build can succeed while React has hoisted nothing, so an implementation that only watches `npm run build` would report green. The gate therefore fires on either, and AC-2's `fetch` check is listed in §15's `pr` rows rather than left to the `checkpoint` stage. The forbidden fallbacks are unchanged: **not** a client-side `document.documentElement.lang = …` effect, and **not** accepting `lang="en"` as a constant. |
| 18.2d | The exact measured length ratios AC-9P will report | **UNKNOWN UNTIL IMPLEMENTED — and it must stay unknown until then.** The `>= 1.30` threshold is fixed by governing lines 228–229, so the assertion needs no pre-computed number; what is unknown is the achieved ratio, which depends on the filler implementation. | AC-9P's `report()` output in `GATES.md` is the record. A run whose achieved ratio is exactly at the threshold is a pass; a run whose precondition test was skipped is `NOT_VERIFIED` with that reason, never a claim. |