# UI-01c — visual direction, work packet + context capsule

**Status:** reviewed once (`CHANGES_REQUESTED`), repairs applied, awaiting delta re-review.
**Delivery lane:** FAST · **Unit:** one screen (`/` overview) including its chrome
**Bounded reading set:** this file + `apps/research-ui/AGENTS.md` +
`docs/architecture/research_ui/AGENT_WORK_PACKETS.md` §UI-01c +
`docs/architecture/research_ui/README.md`. No E3 handoff, kit internals, Contract v1 history.

---

## 0. Base branch — RESOLVED

**Human decision: branch off `main` (`ddcefe5`).** Implemented — branch
`feat/ui-01c-visual-direction` created from `main`.

Verified at branch creation:

- `merge-base main HEAD` = `ddcefe5ed3208c9b65a4d65616da8093b02110f5` — the PR targets
  `main` cleanly and carries no unrelated governance commits.
- `HEAD:apps/research-ui` = `e5dad9c:apps/research-ui` = `9ed53995…` — **the UI tree is
  byte-identical to the verified baseline**, so every recorded gate result in the capsule
  (53 vitest / 7 files, 23 browser, axe clean) carries over without re-derivation.
- This branch carries the **pre-context-protocol** `apps/research-ui/AGENTS.md`, and
  `docs/architecture/agent_context_protocol.md` does not exist in this tree. The capsule
  field contract is inlined below, so this does not block. The isolation rules in
  `AGENTS.md` and the mission instruction apply regardless of revision.
- `docs/architecture/research_ui/` is untracked in every tree, so the governing UI-01c
  packet has no immutable identity. See F8.

## 1. Unit and why it is one screen

The `/` overview, end to end — page composition, shell chrome, workflow treatment,
evidence lineage.

Deliberately not split. A body rebuilt as paper/ink beside a blue/slate pill nav is two
identities on one page: it fails the packet's own anti-template test and is not
reviewable. Coherence outranks a smaller diff.

## 2. Objective

Replace generic generated-SaaS character (blue/slate rounded cards, `shadow-sm`, equal
spacing, decorative pills) with a deliberate **research-instrument** language: calm,
precise, inspectable — closer to an evidence ledger or annotated scholarly document
than an analytics dashboard.

Signature motif: the visible path from a research claim back through evidence and
provenance.

Explicitly rejected: AI-dashboard cards, excessive pills, decorative gradients, and
"productivity" language.

## 3. Decisions taken for you (challenge them at review)

| # | Decision | Rationale |
|---|---|---|
| D1 | **No web fonts — CONFIRMED by human.** One display role from a local serif stack, one interface/data role from the system UI stack. | Confirmed. Packet requires ≤2 typeface roles and that the app stay usable if web fonts fail. A meetup demo must not depend on conference wifi. Known cost, accepted: no custom glyph identity. |
| D2 | **`components/status-badge.tsx` — scope extension.** It is 16 lines, the **sole** definition of state colour (a `Record<WorkflowState,string>` of raw `emerald/blue/slate/rose`, lines 3-8), `rounded-full` at line 12, and consumed only via `workflow-timeline.tsx:15`. Redesigning the workflow while leaving it untouched would leave raw palette as the last thing on the screen. | UI-01c packet requires a written reason **before** editing. |
| D3 | **`VISUAL_DIRECTION.md` at `./VISUAL_DIRECTION.md`** — scope relocation from the governing packet's `docs/architecture/research_ui/`. | Mission restricts work to `apps/research-ui/`, and `docs/architecture/research_ui/` is untracked pre-existing work. Cost recorded as F9. |
| D4 | **`tests-browser/helpers.ts` — scope extension.** F3's fix has no natural home otherwise: the asserted colour literal and its normalisation both live in `helpers.ts` / `focus-visibility.spec.ts`. | Same rule as D2. |

## 4. Allowed paths

Source:
- `app/globals.css`
- `app/page.tsx`
- `components/app-shell.tsx`, `components/primary-nav.tsx`, `components/mobile-nav.tsx`,
  `components/workflow-timeline.tsx`, `components/evidence-chain.tsx`
- `components/status-badge.tsx` — **extension, D2**
- `tests-browser/helpers.ts` — **extension, D4**

Artifacts:
- `tests/*.test.tsx` and `tests-browser/*.spec.ts` that directly cover the files above
- `screenshots/`
- `README.md`, `GATES.md`
- `VISUAL_DIRECTION.md` — **new, D3**
- `UI-01C_WORK_PACKET.md` — this file, orchestrator-owned

Any other path requires a written scope-extension reason **before** editing.

## 5. Immutable boundaries

The capsule lists these by path and points here rather than restating them.

- `lib/contracts.ts`, `lib/mock-project.ts` — **frozen.** Every mock claim, count, label,
  detail string and identifier stays byte-identical. Presentation only.
- State vocabulary `complete` / `active` / `waiting` / `refused` — unchanged.
- `AGENTS.md` — not editable in this packet.
- Shell guarantees: exactly one `<main>` owned by the shell; skip-link target
  `main#main-content[tabindex="-1"]`; named navigation; dialog behaviour; active-route
  semantics; visible `Demonstration data` marker **inside the shell `<header>`** (a test
  pins this location — see F6).
- No new routes. No `lib/api-client.ts` — that boundary does not exist yet.
- `package.json`, `package-lock.json` — no new dependency, no webfont, no font CDN.
- `playwright.config.ts`, `vitest.config.ts`, `tsconfig.json`, `next.config.ts`,
  `postcss.config.mjs`.
- Nothing outside `apps/research-ui/` changed.

## 6. Acceptance criteria

**Identity**
- A1. `@theme` declares semantic roles — paper, ink, rule, evidence, success, warning,
  refusal, focus (surface/raised as needed). The components consume roles; no new raw hex
  or raw `slate-*`/`blue-*`/`emerald-*`/`rose-*` utility without a written reason.
- A2. `VISUAL_DIRECTION.md` states product character, principles, palette roles, typography
  roles, spacing/radius rules, provenance treatment, and use/avoid patterns.
- A3. ≥3 motifs are **visible in the delivered screenshots**, each traceable to a named
  principle in `VISUAL_DIRECTION.md` and to a `file:line` in the implementation. Code-only
  motifs do not satisfy this.
- A4. Rounded containers only where they communicate grouping or interaction. Pills only
  for compact state or provenance labels. No decorative gradient, glass effect, hero copy,
  decorative chart, or copied template. **Functional-state exemption:** the skip link's
  focus affordance and the shared focus ring are exempt from any radius/shadow prohibition —
  they communicate interaction. See F10.
- A5. **No information removed.** Every element that exists today still exists: four
  workflow stage labels, descriptions and counts; all evidence node kinds, labels and
  details; the `Demonstration data` marker; the read-only authority statement. Removing or
  flattening content to satisfy A4/A11/A12 is a failure, not a compliance.

**Accessibility — regression gates, all measured**
- A6. axe on rendered CSS: **zero violations of any impact** at 375px, 1440px, and
  375px-with-dialog-open. `color-contrast` is a decided **pass** in all three.
  `incomplete` is asserted, not just printed: it must equal exactly
  `aria-hidden-focus` with 2 nodes **on the 375px dialog-open run**, and be empty on the
  other two. Any other incomplete, or any increase in count, fails. This assertion must be
  **added** to `tests-browser/rendered-axe.spec.ts` — it is not currently enforced anywhere.
- A7. All normal-size text ≥4.5:1. Re-measure the thin-margin sites in F1/F2.
- A8. Tab order unchanged: `[skip, trigger]` @375px, `[skip, Overview]` @1440px. Dialog
  traps focus; Escape restores focus to the trigger.
- A9. One visible 2px `focus-visible` ring on skip link, desktop nav link, mobile trigger,
  dialog close, and mobile nav link. If the ring colour changes, the global rule **and**
  `.skip-link:focus` must move to the same token — the suite cross-checks them (F3).
- A10. No horizontal overflow, no clipped content, no panel stretched into an oversized
  empty block, at either viewport.

**Content preserved**
- A11. The screen still shows: research question, four workflow stages with unchanged
  labels/states/counts, the claim-to-source trace with unchanged node kinds/labels/details,
  the read-only authority statement, and an unambiguous visible `Demonstration data` label.

**Responsive**
- A12. Evidence lineage stays legible at 375px as a document-like trail — marginal labels
  or equivalent — and does **not** collapse into a stack of cards.
- A13. Workflow reads as one record, not interchangeable cards.

## 7. Negative cases

- No new research facts, counts, identifiers, states, or backend capability. Presentation only.
- No workspace files, no kit CLI calls, no identifier/fingerprint/checksum computation.
- No edits to backend, harness, `contracts/`, `tools/`, or outside `apps/research-ui/`.
- **No i18n work.** No locale routing, catalogs, `dir="rtl"`, or bidirectional logic — that is
  UI-01d. Exception only if a shared primitive is impossible without a direction-agnostic
  hook, and then flagged, not silently added.
- No axe suppression, allow-list, `exclude`, disabled rule, or relaxed assertion.
- **Test changes — read this as a restriction, not a licence.** The governing packet
  (`AGENT_WORK_PACKETS.md:110-111`) states: *"Existing component tests remain green; visual
  changes add or update assertions **only when they protect meaningful semantics or
  accessibility**."* So:
  - The existing 53 tests **must stay green.** Deleting a test, loosening an assertion, or
    rewriting one to accommodate a presentation choice is not permitted.
  - You may **add** assertions where they protect semantics or accessibility (e.g. A6's
    `incomplete` check).
  - You may **update** an assertion only where the updated form still protects meaningful
    semantics or accessibility. F6 classifies all five couplings; **four are design
    constraints on the implementation, not tests to be rewritten.**

  F6 classification — treat these as rules for the *implementation*:

  | Coupling | Protects | Disposition |
  |---|---|---|
  | `home-page.test.tsx:40-43` — `Demonstration data` label inside shell `<header>` | **Meaningful semantics.** `AGENTS.md` lists "presenting mock data without the visible `Demonstration data` label" as **Forbidden**; §5 makes it a shell guarantee. | **NOT updatable.** Keep the label inside the shell `<header>`. This is an anti-fabrication guard, not presentation. |
  | `evidence-chain.test.tsx:22-25` — each `<li>`'s `firstElementChild.textContent` is the number | Presentation | Keep a **real DOM numeral** as the first element child. Do **not** implement the trail with CSS counters. A marginal numeral element satisfies this and is the better motif anyway. |
  | `home-page.test.tsx:51` — `page.tsx:13` is a single text node | Presentation | Keep one text node at that position; wrap neither in a `<span>` nor split it. |
  | `home-page.test.tsx:58` — total `<li>` count | Structural | Do not introduce extra nested lists on the overview; margins/labels are not lists. |
  | `home-page.test.tsx:65` — first N level-3 headings | Structural / semantics | Marginal labels must not be authored as `<h3>`; use `<p>`/`<span>`/`<dt>` or a different heading level. |
- **No claim of visually evaluating screenshots.** Agents may measure layout, geometry and
  accessibility. Visual judgement is the human's.

## 8. Active findings

| ID | Finding | Where / consequence |
|---|---|---|
| F1 | "Latest: …" `text-slate-500` on surface at **4.55:1** — 0.05 margin | `app/page.tsx:13` — in scope; also structurally coupled, see F6 |
| F2 | "Research integrity you can inspect" / "Read-only demonstrator…" at **4.76:1** | `app-shell.tsx:51`, `:77` — in scope |
| F3 | **Trap.** The literal `rgb(29, 78, 216)` appears **twice** in `focus-visibility.spec.ts` (`APP_FOCUS_OUTLINE` report-only ~:42, `APP_ACCENT_RGB` asserted ~:45/:81) and equals `--color-accent: #1d4ed8` (`globals.css:20`). The token is **hex**, so a naive token-read comparison fails on format. `:187-190` cross-checks the nav ring against the skip-link ring, so a separate `--color-focus` on the global rule while `.skip-link:focus` keeps `var(--color-accent)` **fails the suite even though A9 is met**. Normalise hex→rgb in `helpers.ts` (D4). | `focus-visibility.spec.ts`, `helpers.ts`, `globals.css` |
| F4 | `incomplete=aria-hidden-focus(2)` from 1×0px Headless UI focus guards, **on the 375px dialog-open run only**. Expected; report, never suppress. | now enforced by A6 |
| F5 | `summarise()` prints `color-contrast=pass` when a rule both passes and violates (reads `passes` before `violations`). Reporting only; the adjacent `violations=` field and `toEqual([])` carry the verdict. Fix while in the file. | `rendered-axe.spec.ts` |
| F6 | **Five structural couplings the redesign will break.** `home-page.test.tsx:51` pins the single-text-node layout of `page.tsx:13` (the F1 site); `:58` pins total `<li>` count — breaks on any nested list for A13; `:65` pins the first N level-3 headings — breaks on A12 marginal labels authored as `<h3>`; `evidence-chain.test.tsx:22-25` requires each `<li>`'s `firstElementChild.textContent` to be the number — **breaks on a CSS-counter trail, the most natural motif for A12**; `home-page.test.tsx:40-43` requires the `Demonstration data` label inside the shell `<header>` — **an anti-fabrication guard, not presentation; not updatable.** Per §7, treat these as constraints on the implementation, not tests to rewrite: full disposition table is in §7. | component tests |
| F7 | `status-badge.test.tsx:44` guards state-distinguishability by **class-string distinctness only**. Four visually identical class sets would pass. If the new palette makes two states hard to tell apart, this test will not catch it — verify by measurement. | `status-badge.test.tsx` |
| F8 | `docs/architecture/research_ui/` is **untracked**. The governing UI-01c packet has no immutable SHA and can drift or be falsified silently. | repo hygiene; not fixable in-pass |
| F9 | `AGENT_WORK_PACKETS.md:40` will point at a `docs/…/VISUAL_DIRECTION.md` that never exists (D3). That file is not editable in this packet. | follow-up task |
| F10 | `.skip-link:focus` carries `border-radius: 0.5rem` and a two-layer `box-shadow` (`globals.css:97`, `:104`) — apparently forbidden by A4, on the one element A9 names. Resolved by the A4 exemption. | `globals.css` |

## 9. Tests

Targeted, during implementation:
```
npm run typecheck
npx vitest run tests/home-page.test.tsx tests/workflow-timeline.test.tsx \
  tests/evidence-chain.test.tsx tests/status-badge.test.tsx \
  tests/accessibility-in-process.test.tsx tests/shell.test.tsx \
  tests/keyboard-traversal.test.tsx
npx playwright test tests-browser/rendered-axe.spec.ts tests-browser/overflow.spec.ts \
  tests-browser/tab-order.spec.ts tests-browser/focus-visibility.spec.ts \
  tests-browser/responsive-nav.spec.ts tests-browser/hygiene.spec.ts
```

`tests/shell.test.tsx` and `tests/keyboard-traversal.test.tsx` are included because they are
the **sole** importers of `app-shell`, `primary-nav`, and `mobile-nav`, and
`app-shell.tsx:51`/`:77` are F2's contrast sites.

Full gate, **once**, before the PR:
```
npm run typecheck && npm test && npm run build && npm run test:browser
```
Expected: **53 vitest / 7 files** — the count must hold, and per §7 the existing assertions
must stay green (A6 and the new work *add* assertions; nothing is rewritten). Any other count
needs a stated reason.

Browser: **23 → 24.** The increase is **exactly one new test**, in `screenshots.spec.ts`, for
the new `1440-evidence-trail.png` (§10). A6 is satisfied by adding `expect(...)` calls
**inside the three existing** `rendered-axe.spec.ts` tests and contributes **zero** new cases.
(Verified statically: 21 real `test()` sites + 2 loop expansions = 23 today. A naive grep for
`test(` returns 28 and is wrong — it counts 7 `test.describe` plus a `needle.test(html)`
false positive.)

The Python suite is **not** required for this lane and must not be run or "fixed"
(`research_ui/README.md` line 91). The dirty `tools/scholar-agent-kit/uv.lock` is out of scope.

## 10. Screenshots required

Regenerate all five existing, plus one new:

- `375-overview.png`, `1440-overview.png`, `375-mobile-nav-open.png`
- `375-skiplink-focused.png`, `1440-skiplink-focused.png`
- **`1440-evidence-trail.png`** (new — element-scoped capture of the signature motif so the
  human can judge it at usable size)

## 11. Review and repair policy

One broad review, **one** bounded repair pass, then a delta-only re-review. P0/P1 and
in-scope P2 are fixed. Unrelated P3 becomes a follow-up task and does not reopen the loop.
A repair packet carries only finding IDs, required outcome, allowed paths, and invalidated
evidence.

## 12. Human visual gate — procedure

This packet cannot self-certify: I and the subagents **cannot view images**.

1. Implementer reports the ≥3 motifs with principle name + `file:line` + which screenshot
   shows it.
2. Human opens the six screenshots and answers, per motif: *is this visible, and does it
   read as deliberate rather than incidental?*
3. Human also answers the governing anti-template question: **could this page be relabelled
   as a finance or CRM dashboard without changing its structure?**
4. Outcome is recorded here: `sign_off: <pending|approved|rejected>` plus notes.
   **Rejected ⇒ one more bounded repair pass, then stop.** Agents must not self-sign.

### Outcome

`sign_off: **approved**`

| | |
|---|---|
| **Decided by** | The **human packet owner**, reviewing the six delivered captures. Not an implementer, not a subagent, and not this record. |
| **Recorded** | `2026-10-02` — the date this decision was written down. As with the gate-19 ratification at §3.7.5, no in-repo artefact carries the decision's own timestamp; this row is the record, not a claim about when it was spoken. |
| **Scope** | Approves the **visual direction** of this packet's single screen (`/`, including its chrome). It does **not** extend to any later packet, does not authorise a second route, and does not waive any executable gate. |
| **Anti-template question** | **Answered no.** The human's finding: the page "no longer reads like a generic AI dashboard or a relabelled CRM", and reads instead as "a restrained research instrument". This discharges A3 and the §12 gate-3 question. |
| **Motifs** | All three requested motifs confirmed **clearly visible**: the numbered spine (workflow stages and claim-trace nodes), the ruled workflow ledger (horizontal record structure), and the square stamps (`COMPLETE`, `ACTIVE`, `WAITING`). |
| **375px degradation** | **Accepted.** The marginal node-kind labels stack above their content at 375. The human's reasoning: hierarchy remains readable and the vertical rule plus number retains the lineage motif, and forcing a desktop-style margin on mobile "would likely hurt legibility". This closes the residual the implementer flagged as `NOT_VERIFIED` and §3.7.6 disclosed. |

**What this sign-off does not certify.** It covers composition only. It does not
re-open, replace, or add to any executable gate — `typecheck`, `vitest 53/7`,
`build`, `playwright 25/7`, the axe runs and gate 21 all stand on their own recorded
evidence, independently of this decision. No agent in this lane can view an image, so
this row transcribes a human judgement and does not extend it.

---

## Follow-ups

### FU-2 — focused skip link overlaps the brand. **Non-blocking, raised by the human at sign-off.**

The human noted that in both skip-link captures the focused skip link **overlaps the
brand**. Their assessment: acceptable, because the state is transient and highly visible.
A later polish pass could give the affordance a dedicated top-layer placement so it never
sits over the brand mark.

Deliberately **not** fixed here. It is a visual polish item, it changes no acceptance
criterion, and the skip link is correctly focusable, visible, and correctly ordered at both
viewports (A8/A9, asserted). Fixing it inside this packet would have meant an unrequested
layout change to a composition the human had just approved. Recorded so the observation is
not lost — see `GATES.md` §3.7 for the open-item list.

### FU-1 (was F9) — broken cross-reference in the governing packet. **ORCHESTRATOR-OWNED. Not fixed by this packet.**

`docs/architecture/research_ui/AGENT_WORK_PACKETS.md:40` points at a
`VISUAL_DIRECTION.md` **under `docs/`**. Decision D3 relocated that document to
`./VISUAL_DIRECTION.md`, because the mission's write scope and the
design tokens both live there. **The reference is therefore broken and will stay
broken until an orchestrator acts on it.** Recorded here rather than silently
left, because a dangling pointer in a governing document is invisible to every
gate this lane owns.

**Why this packet did not fix it.** The file is untracked pre-existing work and
sits outside §4's allowed paths. Editing it would be a scope violation, and
editing an untracked file is also unverifiable — see FU-2.

**The decision required, which belongs to the orchestrator, not to this packet.**
Two options, and they are not equivalent:

| Option | Action | Also |
|---|---|---|
| **A** | Correct the reference in place, pointing at `./VISUAL_DIRECTION.md` | Fixes the broken pointer only. The file stays untracked and identity-less |
| **B** | Commit the whole `docs/architecture/research_ui/` tree so it is tracked, **then** correct the reference | Fixes the pointer **and** closes F8, because a tracked file has a SHA a capsule can pin |

**Option B is the better fix** and is the reason F8 and FU-1 are the same problem
wearing two hats: an untracked governing document can drift or be falsified
silently, and the broken pointer is a symptom of exactly that. Fixing only the
pointer leaves the more serious half open.

**Preconditions for either:** re-run the README ladder check (`§89` of
`research_ui/README.md`) against `known_baseline_failures`, and confirm
`docs/architecture/research_ui/` is intended to be tracked at all — it was
untracked at both `ddcefe5` and on this branch, so intent is genuinely unrecorded.

**Do not close FU-1 by editing `./VISUAL_DIRECTION.md` to suit the
broken pointer.** The document's location is correct; the pointer is wrong.

---

## Task context capsule

```yaml
task: UI-01c-visual-direction
delivery_lane: FAST
owner_repo: nexus-scholar-harness (apps/research-ui only)
base_sha: ddcefe5ed3208c9b65a4d65616da8093b02110f5   # main tip; see §0 open question
head_sha: ddcefe5ed3208c9b65a4d65616da8093b02110f5   # not yet branched
allowed_paths:
  - apps/research-ui/app/globals.css
  - apps/research-ui/app/page.tsx
  - apps/research-ui/components/app-shell.tsx
  - apps/research-ui/components/primary-nav.tsx
  - apps/research-ui/components/mobile-nav.tsx
  - apps/research-ui/components/workflow-timeline.tsx
  - apps/research-ui/components/evidence-chain.tsx
  - apps/research-ui/components/status-badge.tsx        # extension D2
  - apps/research-ui/tests-browser/helpers.ts            # extension D4
  - apps/research-ui/tests/*.test.tsx                   # only those covering the above
  - apps/research-ui/tests-browser/*.spec.ts            # only those covering the above
  - apps/research-ui/screenshots/
  - apps/research-ui/README.md
  - ./GATES.md
  - ./VISUAL_DIRECTION.md                # new, D3
  - ./UI-01C_WORK_PACKET.md              # orchestrator-owned
immutable_boundaries:                                    # by path; rules in §5, not restated
  - apps/research-ui/lib/contracts.ts
  - apps/research-ui/lib/mock-project.ts
  - apps/research-ui/AGENTS.md
  - apps/research-ui/package.json
  - apps/research-ui/package-lock.json
  - apps/research-ui/playwright.config.ts
  - apps/research-ui/vitest.config.ts
  - apps/research-ui/tsconfig.json
  - apps/research-ui/next.config.ts
  - apps/research-ui/postcss.config.mjs
acceptance_ids: [A1..A13]
open_findings: [F1, F2, F3, F4, F5, F6, F7, F8, F9, F10]
known_baseline_failures:
  - "pre-existing dirty paths unrelated to this packet: docs/README.md,
     docs/architecture/README.md, opencode.json, .opencode/agent/reviewer.md,
     tools/scholar-agent-kit/uv.lock, docs/orientation/,
     docs/architecture/wp02_public_benchmark_strategy.md (README ladder check §89
     must be read against this list, not treated as a scope violation)"
  - "harness conformance: vendored scholar-agent-kit uv.lock blob mismatch - OUT OF
     SCOPE for the UI lane, must not be fixed here"
evidence:
  - command: npm run test:browser
    commit: e5dad9c
    result: "pass - 23 passed; axe color-contrast=pass, violations=none,
             incomplete=aria-hidden-focus(2) on the 375px dialog-open run only.
             Note: e5dad9c is 2 docs-only commits behind base_sha ddcefe5; the
             apps/research-ui tree is identical at both."
  - command: npm test
    commit: e5dad9c
    result: "pass - 53 passed, 7 files"
  - command: npm run typecheck && npm run build
    commit: e5dad9c
    result: "pass - exit 0"
next_gate: inner
stable_sources:
  - apps/research-ui/AGENTS.md            # NOTE: pre-context-protocol revision at ddcefe5
  - ./UI-01C_WORK_PACKET.md#this-file
  - docs/architecture/research_ui/AGENT_WORK_PACKETS.md  # UNTRACKED - no @sha (F8)
  - docs/architecture/research_ui/README.md              # UNTRACKED - no @sha (F8)
```

**Capsule ends.** Update `head_sha`, `evidence`, and `open_findings` after every published
repair. Do not reload stable sources unless an escalation trigger fires (dependency/pin
change, merge-base change, gate reselection, public-surface change).
