# UI-04 context capsule

Compact, re-readable context for packet **UI-04 — the screening workspace**.
Read this capsule plus a repair delta in later rounds instead of re-reading the
stable sources (GATES.md, I18N.md, the work packets, the catalogs).

## Task

A fixture-backed screening page: study citation, abstract, criteria panel,
decision choices, reason field, and an explicit disabled-submit explanation
"until the API exists".

Governing packet: `docs/architecture/research_ui/AGENT_WORK_PACKETS.md` §UI-04
(lines 266-274). Negative cases: "No write to `workspaces/`; no decision
persisted in local storage; no automatic inclusion presented as a human
decision." Gate: "Keyboard-only flow, validation states, and disabled mutation
test." Measured gates, totals, mutation battery and the acceptance map are in
`docs/GATES.md` §8.

## Boundary (hard)

UI-04 has **no explicit allowed-paths list** (Scope line 268: "fixture-backed
screening page only"), so the boundary was drawn as one new screen plus the
honesty extensions that screen forces. Every extension and its reason is listed
here — required because a packet without a path list cannot police itself
otherwise.

**Written:**

- New: `app/[locale]/screening/page.tsx`, `components/screening-page.tsx`,
  `components/screening-form.tsx`, `lib/mock-screening.ts`,
  `tests/screening-form.test.tsx`, `tests-browser/screening.spec.ts`,
  `docs/UI-04_CONTEXT_CAPSULE.md`.
- Catalogs: `messages/{en,fr,ar}.ts` — 19 `screening.*` keys appended as one
  labelled block (93 keys × 3 total).
- Tests in place: `tests/shell.test.tsx` (href list),
  `tests/keyboard-traversal.test.tsx` (7 stops),
  `tests/i18n-catalog.test.ts` (93),
  `tests/project-state-record.test.tsx` (continuation split + `phaseStampOf`),
  `tests-browser/{helpers,tab-order,screenshots,locale-routing,locale-switch,rendered-axe}.spec.ts`,
  `tests-long-strings/long-strings.spec.ts` (route dimension).
- Docs: `docs/GATES.md` §8, `docs/I18N.md` §3 rows.

**Scope extensions beyond "a new page", with reasons:**

| File | Extension | Reason |
| --- | --- | --- |
| `components/app-shell.tsx` | `"use client"` + `usePathname`, derives `currentItemId`, passes it to both navs; LocaleSwitcher comment corrected | `aria-current="page"` must come from the real pathname; a server shell cannot know it, and a stale comment claiming a module boundary would be a lie in the tree |
| `components/primary-nav.tsx` | `screening` gains `href: "/screening"`; exports `renderedHref`, `currentItemIdFromPathname` | the route exists, so presenting it as unavailable would be dishonest; `aria-current` needs a pathname-derived id |
| `components/mobile-nav.tsx` | `currentItemId: string \| undefined` (default removed) | a default would let a nav silently claim a surface |
| `components/project-state-record.tsx` | `NextDestination` links the destination word when `item.href !== undefined`, wrapped in `<bdi>` per `translateParts`' `isolated` contract | the overview's "next: screening" promise is now real; still no link without a route |
| `app/globals.css` | focus-ring selector extended to `input:focus-visible, textarea:focus-visible` | the workspace adds the first form controls; extending the **one shared rule** beats per-component ring utilities (which the hygiene gate would police and which would fork the focus treatment) |

**Never touched (and verified so in `git status`):** `lib/contracts.ts`,
`lib/mock-project*.ts`, `lib/project-state.ts`, `package.json`,
`package-lock.json`, `docs/VISUAL_DIRECTION.md`, `.opencode/` (its pre-existing
dirty `agent/reviewer.md` was preserved), everything outside
`apps/research-ui/`, and — as in every UI packet — `AGENT_WORK_PACKETS.md`
itself.

**Deliberate non-edit (legacy debt, do not "fix" casually):**
`lib/project-state.ts` is byte-frozen, so two of its comments are now stale:
"rendered as text, not a link" (the continuation *is* a link since this
packet) and `OverviewDestination`'s "None of them has a route yet — never as a
link". Recorded in GATES.md §8.4; repairing prose inside a frozen file is an
architecture decision.

## Stable inputs (read once; reload only if a boundary moves)

| Source | What it fixes |
| --- | --- |
| `AGENT_WORK_PACKETS.md:266-274` | deliverable, negative cases, gate |
| `apps/research-ui/AGENTS.md` | no domain decisions, `Demonstration data` label, no invented identifiers, report obligations |
| `docs/I18N.md` §3 (93-key row) | the catalog/fixture boundary: fixture prose untranslated and `<bdi>`-wrapped; ordinals bare |
| `docs/I18N.md` §5 | logical-only utilities; N9–N12 source scanner |
| `components/primary-nav.tsx` header | href = "which route exists" declaration; `renderedHref` never holds a locale |
| `lib/project-state.ts:237-270` (read-only) | the destination model the continuation must honour |
| `tests-browser/hygiene.spec.ts` | gate 21: emitted utilities need a *product-code* source, comments are harvested |
| `tests-browser/helpers.ts` (`measureTabRing`, `PRIMARY_NAV`) | locale-stable selectors; the `subpath` parameter added here |
| `messages/{en,fr,ar}.ts` | 93 keys × 3; `state.*`/`overview.*` untouched |

Known carry-over gaps (flagged, not repaired — outside allowed paths):
`docs/architecture/research_ui/README.md` does not exist, and
`scripts/select_test_gate.py` maps no task to UI paths (exits 2). The operative
gate is the packet's own Gate line plus the commands below.

## Design decisions (UI-04)

1. **Client boundary at the shell, not the page (D-UI04-01).** `app-shell.tsx`
   reads `usePathname()` once and derives `currentItemId =
   currentItemIdFromPathname(pathname, locale)`, typed `string | undefined`
   end-to-end. An unknown path yields `undefined`, never a guessed default —
   the nav may show *no* current surface, which is honest, rather than the
   wrong one.
2. **The form is a real client component; the page stays a server component.**
   Only decisions/reason state crosses the boundary; the record and criteria
   never do. `aria-label` on the form is computed with `translate()`, not a
   literal (direction-source test N9 forbids literal `aria-label="..."`).
3. **One tab stop for the radio group; the disabled button is not a stop.**
   Measured in Chromium (no radio preselected ⇒ entry at the first radio);
   an always-`disabled` button is skipped by the browser and correctly absent
   from the recorded ring (`tab-order.spec.ts` "screening workspace" screens).
4. **Validation is `aria-describedby`, not a live region.** The reader made
   the choice a moment ago; announcing the consequence would interrupt them.
   The browser test pins the element's attribute tuple
   (`aria-live`/`aria-atomic`/`role` all absent) so this cannot drift into an
   announcement later.
5. **The submit is disabled in *every* state and says why in visible text**
   (`screening.submitDisabledExplanation`, `screening.noPersistence`) — the
   absence of an API is a fact about the demonstration, not an error the
   reader must discover by pressing the button. Packet wording: "until the API
   exists."
6. **Fixture honesty by property, not by pin (D-UI04-06).**
   `lib/mock-screening.ts` carries a citation, an abstract, and three criteria
   — no verdict, no decision, no identifiers, no acceptance result (packet
   forbids inventing them). Unlike `lib/mock-project.ts` it is deliberately
   **not** byte-frozen; `tests/screening-form.test.tsx` property-tests the
   absence instead. All fixture text renders inside `<bdi>`; the marginal
   ordinal is bare `Intl` output (`I18N.md` §3).
7. **`fr` normalisation rule applied twice.** `screening.decisionLegend` fr is
   "Choix de décision" and `screening.citationLabel` fr is "Référence
   bibliographique" — each must not normalise to its English value. `ar` is
   all-Arabic, ASCII apostrophes, digits avoided.
8. **One focus treatment (D-UI04-08).** The textarea carries no focus
   utilities because `globals.css` declares the ring once for `a`, `button`,
   `input`, `textarea`. A comment in `screening-form.tsx` records this —
   worded without naming the bare utility, after gate 21 failed on
   `commentOnly: ["ring"]` when an earlier draft did name it (Tailwind does
   not strip comments from `.tsx`). That failure and repair are the live
   negative control for hygiene GATES.md §8.1 S9.
9. **Continuation link style** mirrors `not-found.tsx`
   (`text-sm font-medium text-evidence underline decoration-2 underline-offset-4`),
   destination word inside `<bdi>` because `translateParts` marks it
   `isolated`; unroutable destinations keep the text-plus-availability-tag
   form (`TAG_SHAPE`).

## Validation commands (from `apps/research-ui/` unless noted)

```
npm run typecheck                # exit 0
npm test                         # 216 passed / 216, 13 files
npm run build                    # exit 0; /en|fr|ar/screening prerendered
npm run test:browser             # 82 passed / 82 (build+server run by Playwright)
npx playwright test --config playwright.long-strings.config.ts   # 19 / 19
npx playwright test tests-browser/hygiene.spec.ts                # 4 / 4
uv run ruff check scripts/       # repo root; All checks passed!
git status --short               # scope check; only intended files move
```

Mutations a/b/c (button `enabled`, preselected decision, dropped nav href)
each failed the suite before they were believed; verbatim summaries and the
SHA-256 restore proofs are in `GATES.md` §8.2.

## Repair delta (things that failed first, kept for honesty)

- `rendered-axe.spec.ts`: route-dimension edit left a stray `}` — caught by
  `npm run typecheck` (exit 1, three TS syntax errors), fixed, exit 0.
- Hygiene gate 21 failed on `commentOnly: ["ring"]` after the first draft of
  the textarea comment; prose de-tokenised, gate green (see decision 8).
- `phaseStampOf`: `dot.closest("span")` returns the dot itself (it *is* a
  span) — the helper uses `dot.parentElement`; an earlier draft asserted
  against the wrong element.
- `getByText` ambiguity between the phase word and the destination link after
  the continuation became a link: assertions scoped via `phaseStampOf`.
- One cold-cache vitest run timed out in `keyboard-traversal.test.tsx`
  (15.7 s, environment 41 %); targeted re-run 8/8, full run 216/216 — a
  machine-load flake, not an assertion change.
- `GATES.md` §8 was appended with PowerShell `Add-Content`, which wrote seven
  cp1252 bytes (`6×§`, `1××`) into a UTF-8 file; byte-scan found them and they
  were spliced to their UTF-8 sequences, whole-file strict UTF-8 re-validated.
  Lesson recorded: append to these docs via UTF-8-safe tools, never
  `Add-Content`.

## Repair delta — cycle 1 (reviewer: CHANGES_REQUESTED, four findings)

Documentation/assertion-strength defects only; code, scope and design were
approved (the app-shell/globals/mobile-nav scope extensions judged
justified-and-minimal). Findings F1–F4 fixed in place, no other wording moved:

- **F1 — supersession markers for six falsified §1–§7 statements.** UI-04 made
  these present-tense claims false and left them unmarked; each now carries an
  in-place marker naming §8, in the document's own B3/B4 convention:
  `GATES.md:480` (open item "Still only `/`" → closed by UI-04), U2 (74 → 93
  keys), U5 (zero links → routable destinations link), U8 (ring unchanged →
  1440 ring gained the Screening stop), W10 (both claims), §7 A9 (both
  claims). Plus the recommended qualifiers on the §6.2/§7.2 totals headers
  ("at the close of UI-02/UI-03 — current totals are §8.2"). Run logs
  themselves untouched.
- **F2 — wrong arithmetic in §8.3 row 1.** The pre-UI-04 shell href array had
  **5** entries (verified against `git show HEAD:` — its comment read "The
  only five links"), now **6**; the row said 6 → 7 by conflating it with the
  7-entry jsdom tab-stop list (which also counts the mobile trigger). Row
  corrected, and the row now names the two metrics explicitly.
- **F3 — misattributed count in S5.** "The primary nav renders exactly seven
  elements" was false: the `Primary` landmark holds 4 entries (2 links +
  2 stamps), the locale landmark 3 links. S5 now claims the verified
  arithmetic (seven entries across both header nav landmarks; six document
  anchors), cites `tests/shell.test.tsx:241-284` for the exhaustive 6-anchor
   array and the never-a-link stamps assertion, and the 4+3 recount was run
   against the prerendered `en.html` (output pasted in Repair delta — cycle 2
   below).
- **F4 — "byte for byte" claim exceeded its assertion.**
  `getByText(fixture, { selector: "bdi" })` uses Testing Library's
  whitespace-normalising normalizer, so a whitespace-only rewrite passed while
  the prose claimed byte equality. The three locale tests now assert exact
  `textContent` equality (inventory length + citation + abstract + each
  criterion, no trim/normalize); no markup change was needed —
  `<bdi>{value}</bdi>` already renders one exact text node. Negative control:
  injecting a single leading space inside the citation `<bdi>` failed all three
  locales (`AssertionError: expected ' Amara R, …' to be 'Amara R, …'`,
  3 failed | 15 passed), then the file was restored byte-identical
  (SHA-256 `E9612095…46EE5` matched) and 18/18 went green again. Test count
  stays **216** — assertions were strengthened, none added.

## Repair delta — cycle 2 (reviewer: CHANGES_REQUESTED, F6)

- **F6 — both "pasted" provenance pointers had no paste.** The F3 row above and
  `GATES.md` S5 claimed the 4+3 recount output was pasted, but no block existed
  in either file. The recount was re-run for this cycle against the current
  prerendered `en.html` (50 929 bytes, mtime 10/09/2026 02:04:14) and its
  verbatim output is pasted below; the S5 pointer in `GATES.md` now names its
  own block (`**S5 recount**`, directly under the §8.1 table). Command: from the
  repo root in PowerShell, `[regex]::Matches` over the file —
  `<nav\b[^>]*>.*?</nav>` blocks with per-block `aria-label`/`<li`/`<a href`
  counts, plus document-wide `<a href`. Docs-only; no other wording moved.

```
=== S5 recount of prerendered en.html (re-run for repair-cycle-2) ===
file: C:\Users\mouadh\Documents\nexus-scholar-harness\apps\research-ui\.next\server\app\en.html
bytes: 50929  mtime: 10/09/2026 02:04:14
nav landmarks found: 2
  landmark [Primary]: entries(li)=4  anchors=2
  landmark [Language]: entries(li)=3  anchors=3
entries total: 7  =  links 5 + route-less stamps 2
document a[href] total: 6
hrefs: #main-content, /en, /en/screening, /en, /fr, /ar
mobile panel nav present: False
exit: 0
```
