# UI-03 context capsule

Compact, re-readable context for packet **UI-03 — workflow timeline**. Read this
capsule plus a repair delta in later rounds instead of re-reading the stable
sources (GATES.md, VISUAL_DIRECTION.md, the work packets, the catalogs).

## Task

The workflow stage sequence must show each of the four states — `complete`,
`active`, `waiting`, `refused` — **with text and a distinct icon, never colour
alone**.

Governing packet: `docs/architecture/research_ui/AGENT_WORK_PACKETS.md` §UI-03
(lines 256–264). Scope: `components/workflow-timeline.tsx` and tests.
Negative cases: no claim that a future stage is complete; `refused` is distinct
from failed infrastructure. Gate: "State matrix test and narrow-width visual
check."

## Boundary (hard)

- Write only under `apps/research-ui/`, and only the packet's allowed paths:
  `components/workflow-timeline.tsx`, `tests/workflow-timeline.test.tsx` (± a new
  state-matrix test file), `tests/fixtures/presentation-fixture.ts`,
  `tests-browser/`, `docs/GATES.md`, `docs/UI-03_CONTEXT_CAPSULE.md`,
  `screenshots/`.
- Never touch: `components/status-badge.tsx`, `lib/contracts.ts`,
  `lib/mock-project.ts`, `lib/mock-project-states.ts`, `lib/project-state.ts`,
  `messages/`, `i18n/`, `package.json`, `package-lock.json`, `app/`,
  `docs/VISUAL_DIRECTION.md`, `docs/I18N.md`, `docs/UI-02_CONTEXT_CAPSULE.md`,
  `.opencode/`, and anything outside `apps/research-ui/`.
- No new i18n keys, no route change, no API, no new strings —
  `state.complete|active|waiting|refused` already exist in en/fr/ar.
- No invented identifiers, refusal codes, verdicts, DOIs or fingerprints
  (`apps/research-ui/AGENTS.md`). Presentation prose only.
- Logical/direction-aware layout only; role tokens only, no raw hex; no
  `left-*`/`right-*`/`ml-*`/`mr-*` (`tests/i18n-direction-source.test.ts`).
- No literal `aria-label`/`title`/`alt`/`placeholder` strings (same test, N9).
- Do not write Tailwind utility names into `.tsx` comments that the scanner
  would harvest (`tests-browser/hygiene.spec.ts` gate 21,
  "emitted from a comment only").

## Stable inputs (read once; reload only if a boundary moves)

| Source | What it fixes |
| --- | --- |
| `docs/architecture/research_ui/AGENT_WORK_PACKETS.md:256-264` | the packet's deliverable, negative cases, gate |
| `apps/research-ui/AGENTS.md` | semantic HTML, text labels in addition to colour, no domain decisions, `Demonstration data` untouched |
| `docs/VISUAL_DIRECTION.md` P3 (§3 rows, §5 line 276, §6, §9 M3) | a stamp's text is always the assertion; the dot anatomy; the icon **accompanies** the word |
| `components/status-badge.tsx` header (D2) | the application's only definition of state colour |
| `docs/UI-01D_WORK_PACKET.md` D-I18N-09 | no icon mirroring unless a per-icon decision is recorded |
| `docs/UI-01D_WORK_PACKET.md` D-I18N-10 + `tests-browser/helpers.ts` | locale-stable selectors, no English accessible names as handles |
| `lib/contracts.ts:1-9` | `WorkflowState` union and `WorkflowStage` shape (byte-frozen) |
| `messages/{en,fr,ar}.ts` | 74 keys × 3; `state.*`, `overview.recordError*` (byte-frozen) |
| `tests-browser/hygiene.spec.ts` | gate 21, raw-palette regex, `COLLATERAL_EMITTED` |
| `tests-browser/overflow-recipe.ts` | the one horizontal-overflow measurement both runners share |

**Doc gap (flagged, not repaired):** `apps/research-ui/AGENTS.md` rule 1 and the
packet's small-agent prompt both name `docs/architecture/research_ui/README.md`.
That file **does not exist** (the tree holds only `AGENT_WORK_PACKETS.md`,
`GATES.md`, `I18N.md`, `UI-01C_WORK_PACKET.md`, `UI-01D_WORK_PACKET.md`,
`UI-02_CONTEXT_CAPSULE.md`, `VISUAL_DIRECTION.md`). Creating it is outside this
packet's allowed paths, so it is recorded here and in `GATES.md` §7.4 as open
documentation debt.

**Gate-selection gap (flagged, not repaired):** `uv run python
scripts/select_test_gate.py --path apps/research-ui/components/workflow-timeline.tsx
--stage inner` exits 2 ("no task selected") — the E3 manifest maps no task to
UI paths. The governing gate for this packet is therefore the packet's own Gate
line plus the `VALIDATION_COMMANDS` listed below, recorded in `GATES.md` §7.

## Design decisions (UI-03)

1. **Icon set (D-I18N-09 record).** heroicons v2 outline, already a pinned
   dependency (`@heroicons/react: ^2.2.0`): `complete → CheckCircleIcon`,
   `active → ArrowPathIcon`, `waiting → ClockIcon`, `refused → NoSymbolIcon`.
   **All four are chosen as direction-neutral and are NOT mirrored** — no
   `rtl:scale-x-*`, no transform of any kind. `ArrowPathIcon` is arrow-like,
   which is D-I18N-09's named trigger: "If a future genuinely directional icon
   (chevron, arrow) appears, mirroring is an explicit per-icon decision recorded
   in the packet that adds it." That decision is made here, and it is *not* to
   mirror — the glyph draws a cycle, not a directional arrow. Because
   `AGENT_WORK_PACKETS.md` is not an allowed path, this
   per-icon decision is recorded here and in `GATES.md` §7.4, which is the
   "packet that adds it" available to this packet.
2. **Placement.** First child of the existing stamp cell in
   `workflow-timeline.tsx`, immediately before `<StatusBadge>`:
   `<Icon aria-hidden="true" data-stage-state-icon={stage.state} className="size-4 shrink-0 text-ink-muted" />`.
   The badge keeps its dot, hue and word; the icon adds the shape channel. No
   focusable element, no accessible-name change, no role change to `<ol>`/`<li>`.
3. **Neutral tone (D2).** One class string for all four states, carrying the
   `text-ink-muted` role. No `Record<WorkflowState, string>` of colour classes
   is introduced in the timeline; `status-badge.tsx` remains the only state→hue
   definition. State distinctness on the icon channel comes from *shape*
   (different path data + the `data-stage-state-icon` token), never from hue.
4. **The word stays the assertion (P3).** The icon accompanies the stamp; it
   never replaces it, never carries a `role`, `<title>` or `aria-label`, and the
   stamp's dot anatomy and hue map are untouched (`status-badge.tsx` is out of
   scope).
5. **Refused-fixture repair (A5).** `ALL_STATES_STAGES` claimed to exercise
   every `WorkflowState` "including `refused`" but listed none. A fifth stage
   (`fixture-e`) is appended so the doc-comment is true; the sequence stays
   monotone (no `complete` after a non-`complete` stage) and the file's
   disclaimer stays honest — the new row records no inclusion, exclusion,
   acceptance or refusal verdict, no identifier and no refusal code.

## Key files

| File | Role |
| --- | --- |
| `components/workflow-timeline.tsx` | the state icon, first child of the stamp cell (edited) |
| `tests/workflow-timeline-state-matrix.test.tsx` | A1–A4 state matrix + negative cases (new) |
| `tests/fixtures/presentation-fixture.ts` | `ALL_STATES_STAGES` gains the `refused` stage (A5) |
| `tests-browser/workflow-timeline-narrow.spec.ts` | A6: 375px `en`/`ar` narrow-width visual check (new) |
| `docs/GATES.md` §7 | the packet's measured gates and totals |
| `screenshots/*.png` | regenerated by `tests-browser/screenshots.spec.ts` |

Existing files deliberately left byte-identical:
`tests/workflow-timeline.test.tsx`, `tests/status-badge.test.tsx`,
`tests/i18n-catalog.test.ts`, `tests-browser/tab-order.spec.ts`,
`components/status-badge.tsx`, `messages/*`, `i18n/*`, `lib/*`, `app/*`,
`package*.json`.

## Validation

While editing (targeted): `npx vitest run tests/workflow-timeline.test.tsx
tests/workflow-timeline-state-matrix.test.tsx tests/status-badge.test.tsx
tests/home-page.test.tsx` plus `npm run typecheck`; targeted browser
`npx playwright test tests-browser/workflow-timeline-narrow.spec.ts
tests-browser/hygiene.spec.ts`.

Final gate, exactly once each, from `apps/research-ui/`:

```text
npm run typecheck
npm test
npm run build
npm run test:browser
npx playwright test --config playwright.long-strings.config.ts
```

From the repository root: `uv run ruff check scripts/` and `git status --short`
(scope check).

## Review protocol

Issue the packet to the reviewer with the acceptance map (A1–A9) and the exact
validation output. On `CHANGES_REQUESTED`, apply a **repair delta** against this
capsule — do not re-read GATES.md / VISUAL_DIRECTION.md / the packets unless a
defined boundary moved. Maximum three coder–reviewer cycles.

## Repair delta — cycle 1 (implementation deltas, written before any reviewer round)

Applied while implementing, each recorded before the code that followed it.
None of these weakened an acceptance criterion; two *narrowed a guard* to stop
it failing on something legitimate, and both were re-verified against the real
run.

| Finding | Repair |
| --- | --- |
| The D2 source guard as first drafted banned the bare hue words `success`/`evidence`/`warning`/`refusal` anywhere in `workflow-timeline.tsx` — and failed on `tests/evidence-chain.test.tsx`, which the file's own pre-existing header names | Guard narrowed to the *utility* spelling (`(?:text\|bg\|border\|ring\|fill\|stroke\|outline\|decoration\|divide)-<hue>(?![\w-])`, so it still catches a hue class in code **or** quoted in a comment) plus the `Record<WorkflowState, string>` pattern. A guard that fails on a file name is a guard people route around |
| A6's stamp-word check read `innerText`, which reports *rendered* text — the stamp is uppercase by design (P3), so `en` reported `COMPLETE` | Comparison made case-insensitive on both sides; the claim ("this locale's state word is on screen") is unchanged. `ar`, which has no case, passed either way |
| A4 needs "the rendered refused row contains no error/failure word" without hardcoding English regexes for `fr`/`ar` | Words are derived per locale from the error-ish *keys'* catalog values, tokenised on letters/diacritics, kept at ≥5 code points, and any token that **is** the refused stamp is excluded — `overview.recordError` itself says "not a refused decision" (en) and "non d'une décision refusée" (fr), so rejecting the stamp's own word would reject the very sentence that separates the two concepts |
| Fidelity order: `complete` sits after `refused` and `waiting` in N1's synthetic sequence | Kept deliberately. The component must render the input state it was given regardless of neighbours; a "sane-looking" order would let a position-inferring component pass |
| **Mutation check (re-executed for repair-cycle-1, F2):** deleting the explicit `aria-hidden="true"` prop from `<StateIcon>`. Against the current 16-test file: `Tests  1 failed \| 15 passed (16)`, exit 1, failing `pins the icon's props in our own JSX, not only in the library default (A1)` at `:256`. The earlier version of this row reported a green **16/16**, which came from the 15-test suite that existed *before* the pin below was written and was miscopied as 16 — replaced by the re-run above | Added a source pin: the `<StateIcon … />` block must contain `aria-hidden="true"`, `data-stage-state-icon={stage.state}` and the shared class string, so the prop is load-bearing in the suite rather than free-riding on `@heroicons/react` 2.2.0's own `"aria-hidden": "true"` svg default (a DOM-only assertion stays green with the prop deleted). The DOM assertion is kept as well, because the packet's claim is about what a screen reader receives |
| **Mutation check (re-executed for repair-cycle-1, F2):** `refused: NoSymbolIcon` → `refused: ClockIcon`. Against the current 16-test file: `Tests  1 failed \| 15 passed (16)`, exit 1, failing `renders four mutually distinct icon markups` (`AssertionError: expected 3 to be 4`, `:181`). The previously recorded `1 failed / 14 passed` was that same pre-pin 15-test suite | Failed as designed, so the stripped-markup distinctness claim is not vacuous — no code change. Both mutations were undone from a copy taken before the first: the component's SHA-256 is `12B42053D31A566BDD6493E4FDE2474BC1F8D2B6B6C5D696EC6E744B7D586498` before every mutation and after every restore (verified each time), and the full battery was re-run against the restored bytes. Verbatim summaries in `GATES.md` §7.2 |
| Cycle-2 review repairs (added after the fact — the rows above are the pre-review record the original heading referred to) | F1: the D-I18N-09 citation in `GATES.md` §7.4 and in Design decision 1 above was reworded to cite that packet's actual arrow/chevron rule instead of an invented convention; F2: all three mutation runs were re-executed against the current 16-test file and both mutation records rewritten from verbatim vitest output; F3: `GATES.md` §7.2's suite-composition sentence corrected — three of the ten `it(` blocks are locale-wrapped, giving 7 singletons + 3×3 = 16 (the earlier count was wrong) |

Design decisions 1–5 above were implemented **as specified**: same icon set,
same placement (first child of the stamp cell), same `size-4 shrink-0
text-ink-muted` class string, no icon swap, no placement or size change.

Validation after this delta: `npm run typecheck` (exit 0), `npm test`
(**195/195**, 12 files), `npm run test:browser` (61/61, 11 files — gate 21
reports `emitted from a comment only: []` and `emitted with no source anywhere:
[]`), `npm run build` (exit 0, 5 outputs),
`npx playwright test --config playwright.long-strings.config.ts` (10/10,
ratios `en 1.7167` / `fr 1.3884` / `ar 1.3409`), `uv run ruff check scripts/`
(clean).
