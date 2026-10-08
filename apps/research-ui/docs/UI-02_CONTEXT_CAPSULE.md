# UI-02 context capsule

Compact, re-readable context for packet **UI-02 — project overview state model**.
Read this capsule plus a repair delta in later rounds instead of re-reading the
stable sources (GATES.md, I18N.md, the work packets, the catalogs).

## Task

Fixture-backed, read-only project-overview state model that makes the evidence
workflow understandable: `empty`, `setup`, `search`, `screening` (waiting for
human decisions), `extraction`, `indexing`, `refusal`, `degraded`, `ready` —
plus the record-arrival axis the UI-01 gate clause requires (populated, loading,
empty, error fixtures).

Governing packet: `docs/architecture/research_ui/AGENT_WORK_PACKETS.md` §UI-02.
Scope: "overview route and presentation components".
Negative cases: counts never inferred in the browser; absent counts render
**unknown**, never zero. Gate: "Populated, loading, empty, and error fixtures;
component tests."

## Boundary (hard)

- Write only under `apps/research-ui/`. No backend, `tools/`, pins, contracts,
  package files, workspace data, E3 handoffs, kit internals, Contract v1 history.
- Fixture-backed presentation only — no live API claim, no `lib/api-client.ts`.
- No invented Nexus Scholar identifiers, fingerprints, checksums, acceptance
  results, or refusal codes.
- Fixture content (`lib/mock-project.ts`, new fixture prose) renders byte for
  byte inside `<bdi>`; chrome comes from `messages/{en,fr,ar}.ts` as plain text;
  counts go through `formatNumber` bare (never `<bdi>`).
- Only logical layout utilities (`ps/pe/ms/me/border-s/border-e/text-start/
  text-end`); no physical ones — `tests/i18n-direction-source.test.ts` (N10).
- No raw palette utilities in `components/**`/`app/**` — `tests-browser/
  hygiene.spec.ts` gate 21. Declared tokens: paper, leaf, ink, ink-muted,
  ink-faint, rule, rule-strong, evidence, success, warning, refusal, focus.
- No literal `aria-label`/`title`/`alt`/`placeholder` strings (N9).
- Do not write Tailwind utility names into `.ts`/`.tsx` comments that the
  scanner would harvest (hygiene "emitted from a comment only").

## Byte pins (must not change — `tests/i18n-catalog.test.ts`)

`lib/mock-project.ts`, `lib/contracts.ts`, `package.json`,
`package-lock.json`. Therefore the new model lives in **new** files:
`lib/project-state.ts` (types), `lib/mock-project-states.ts` (fixtures).

## Facts that make the existing tests pass

- Catalog key count is asserted exactly: **42 → 74 after UI-02** (32 new keys).
  `en.ts` header comment and `I18N.md` §3 must be updated to the same number.
- `tests/home-page.test.tsx`: `getAllByRole("listitem")` must equal
  `stages(6) + evidence(5)` → the new section must render **no `<li>`**; the
  first six `level: 3` headings must stay the stage labels → the new section
  uses **`h2` only**, no `h3`, no `list` role.
- `tests/i18n-render.test.tsx` `englishChromeIn`: every sentence outside `<bdi>`
  in `fr`/`ar` must match a sentence of that locale's catalog → all new prose is
  catalogued; all new fixture prose is inside `<bdi>`.
- Keyboard/axe/shell suites: the new section adds **no focusable element** and
  no `main`; headings stay `h1 → h2`.
- Stamp precedent: `components/status-badge.tsx` (`STAMP_SHAPE`, token colours,
  `aria-hidden` dot, rtl size/tracking pair).

## Design decisions (UI-02)

- Two axes, deliberately separate:
  `record: "loading" | "error" | "ready"` (did the overview record arrive?)
  and, only when `ready`, `phase: ProjectOverviewPhase` (the nine workflow
  states). **A failed read (`error`) is not a refusal, and a refusal is not a
  failed read.**
- `ProjectOverviewState` is a discriminated union on `record`.
- Counts: `Partial<Record<OverviewCountField, number>>`; five fields always
  rendered; absent → `counts.unknown`.
- Fixture values reuse the frozen corpus numbers only (143 / 18 / 18); anything
  the fixture does not carry stays absent (unknown), never `0`.
- `next?: "screening" | "evidence" | "audit"` names the continuation surface as
  **text plus the `nav.unavailable` tag** — never a link (those routes do not
  exist; shell gate 16 forbids dead links).
- Vocabulary lookups `phaseKey` / `countKey` live in `i18n/translate.ts` as
  `Record<Token, MessageKey>` so a missing token label is a compile error.

## Key files

| File | Role |
| --- | --- |
| `lib/project-state.ts` | presentation types (new) |
| `lib/mock-project-states.ts` | 11 fixtures: loading, error, 9 phases (new) |
| `components/project-state-record.tsx` | the "Current stage" section (new) |
| `components/overview-page.tsx` | wires the section between masthead and workflow |
| `messages/{en,fr,ar}.ts` | +32 keys: `overview.state*`, `overview.record*`, `overview.nextDestination`, `phase.*` ×9 ×2, `counts.*` ×7 |
| `i18n/translate.ts`, `i18n/index.ts` | `phaseKey`, `countKey` exports |
| `tests/project-state-record.test.tsx` | state matrix (new) |
| `tests/i18n-catalog.test.ts` | key count + vocabulary additions |

## Validation

While editing (targeted): `npx vitest run tests/project-state-record.test.tsx
tests/i18n-catalog.test.ts tests/home-page.test.tsx tests/i18n-render.test.tsx`
plus `npm run typecheck`; targeted browser
`npx playwright test tests-browser/rendered-axe.spec.ts tests-browser/overflow.spec.ts`.
Final PR candidate, exactly once:
`npm run typecheck && npm test && npm run build && npm run test:browser`.

## Review protocol

Issue the packet to the reviewer with the acceptance map and exact validation
output. On `CHANGES_REQUESTED`, apply a **repair delta** against this capsule —
do not re-read GATES.md/I18N.md/packets unless a defined boundary moved.
Maximum three coder–reviewer cycles.

## Repair delta — cycle 1 (reviewer `CHANGES_REQUESTED`, findings F1–F5)

Reviewer verdict on UI-02-REVIEW-01: CHANGES_REQUESTED, no blockers, R1–R8/R10 and
N1–N10 all pass; the verdict rested on R9 (doc truthfulness). Applied:

| Finding | Repair |
| --- | --- |
| F1 (major): `GATES.md` §5.1 row I1 still claimed "41 keys / pinned digest / 140 tests" against §6's 74/144 | I1 reworded: no catalog digest exists (pins cover the four byte-frozen files), 41 was already stale against its own 42-key assertion, current count 74, status marked UI-01d snapshot superseded by §6 U2/§6.2; the §5.1 totals line annotated as a dated snapshot pointing at §6.2 |
| F2: `I18N.md` §4 step 6 claimed a "catalog digest" | Reworded: parity test asserts key count + identical key sets; SHA-256 pins cover the four byte-frozen files |
| F3: my §6.4 said the research_ui tree was "untracked" (tracked since `0fe5315`) | Reworded with the commit; tree verified clean there |
| F4: §6.2 said "5 static pages (`/en`,`/fr`,`/ar`, plus `_not-found`)" — four names | Enumerated all five outputs: `/_not-found`, `/[locale]`, `/en`, `/fr`, `/ar` |
| F5: read-failure stamp shares the refusal hue | Kept deliberately (oxide is the palette's failure tone; ochre would read as pending) and **recorded as a design note under §6.1** so the reuse is evidence, not accident |
| (reviewer residual risk: unknown-not-zero asserted only for `empty` + `search`) | Added one uniform test: all 9 fixtures × 3 locales × 5 fields — each row holds `formatNumber(value)` or `counts.unknown`, and absent rows never read zero |

Re-validate after the delta: `npm run typecheck` + `npm test` (test file changed);
browser/long-strings evidence unchanged because the delta touches only `docs/*.md`
(both excluded from the Tailwind scan by `@source not ../../**/*.md`) and
`tests/**` (excluded too) — `components/project-state-record.tsx` was **not** edited
(F5 was resolved in documentation).
