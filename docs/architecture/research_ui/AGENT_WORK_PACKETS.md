# Research UI small-agent work packets

Dispatch one packet at a time. Agents must read `apps/research-ui/AGENTS.md` first. These packets deliberately avoid E3 runtime dependencies.

## UI-01 — Application shell

**Scope:** `apps/research-ui/app/layout.tsx`, navigation components, global styling.

**Deliverable:** Responsive shell with project identity, primary navigation, demonstration-data marker, skip link, and mobile navigation.

**Negative cases:** No toolkit calls, no authentication fiction, no hidden demo marker, no copied complete template.

**Gate:** Typecheck plus mobile/desktop screenshots and keyboard traversal.

## UI-01c — Nexus Scholar visual direction

**Why this packet exists:** UI-01 established a sound, accessible shell, but its
blue/slate cards, pills, shadows, and evenly spaced dashboard composition still
read as a generic generated SaaS interface. Freeze a recognisable Nexus Scholar
visual language before UI-02 through UI-06 multiply that language across more
routes. This packet changes presentation only; it does not add product behavior.

**Design intent:** Treat the application as a **research instrument**: calm,
precise, inspectable, and closer to an evidence ledger or annotated scholarly
document than an analytics dashboard. Its signature interaction is the visible
path from a research claim back through evidence and provenance.

**Allowed paths:**

- `apps/research-ui/app/globals.css`
- `apps/research-ui/app/page.tsx`
- `apps/research-ui/components/app-shell.tsx`
- `apps/research-ui/components/primary-nav.tsx`
- `apps/research-ui/components/mobile-nav.tsx`
- `apps/research-ui/components/workflow-timeline.tsx`
- `apps/research-ui/components/evidence-chain.tsx`
- UI tests and browser tests that directly cover those files
- `apps/research-ui/screenshots/`
- `apps/research-ui/README.md` and `apps/research-ui/GATES.md`
- `apps/research-ui/docs/VISUAL_DIRECTION.md` (new)

Any additional path requires a written scope-extension reason before editing.
Do not change `lib/contracts.ts` or `lib/mock-project.ts`.

**Deliverables:**

1. `VISUAL_DIRECTION.md` containing the product character, design principles,
   palette roles, typography roles, spacing/radius rules, provenance treatment,
   and examples of patterns to use and avoid.
2. A small semantic token layer for paper, ink, rule, evidence, success,
   warning, refusal, and focus colors. Component markup consumes roles rather
   than scattering arbitrary raw colors.
3. A redesigned overview composition that preserves the current information
   and visible `Demonstration data` marker while avoiding a card around every
   item.
4. A distinctive evidence-lineage primitive using an annotated vertical trail,
   marginal labels, or another document-like treatment that remains legible on
   narrow screens.
5. A restrained workflow treatment in which status, stage, and counts form one
   readable record rather than six interchangeable dashboard cards.
6. Updated 375px and 1440px screenshots, including the mobile navigation and a
   focused interactive control.

**Required design constraints:**

- Prefer warm paper, ink, hairline rules, marginal notes, and provenance stamps
  over cold dashboard gray, floating cards, and decorative shadows.
- Use at most one display typeface role and one interface/data typeface role;
  the application must remain usable if web fonts fail or are not introduced.
- Rounded containers are permitted only when they communicate grouping or
  interaction. Do not make every section a rounded card.
- Pills are reserved for compact state or provenance labels, not general
  decoration.
- Exact identifiers, actors, dates, refusal reasons, and lineage should look
  intentional rather than like metadata hidden beneath the interface.
- Keep the overview calm and dense enough to feel like a workbench, without
  reducing readability or touch-target size.
- Preserve the application shell's single `main`, skip link, named navigation,
  dialog behavior, active-route semantics, and visible demo-data marker.
- Keep all mock claims and counts unchanged. Visual redesign never authorizes
  new research facts, identifiers, states, or backend capability.

**Anti-template review:** Reject the result if it could plausibly be relabelled
as a generic finance, CRM, or analytics dashboard without changing its visual
structure. Reject unexplained gradients, glass effects, hero marketing copy,
oversized empty panels, excessive shadows, repeated rounded cards, decorative
charts, or a copied Tailwind Plus template. Tailwind Plus may supply individual
interaction patterns, but the final composition must be Nexus Scholar-specific.

**Accessibility repair included in this packet:** Resolve every UI-00b contrast
failure, provide a consistent application-level `focus-visible` treatment for
links and buttons, and prevent the desktop explanatory panel from stretching
into an oversized empty block. Do not suppress or allow-list accessibility
findings.

**Acceptance criteria:**

- All rendered normal-size text reaches WCAG 2.2 AA contrast (at least 4.5:1),
  including stage labels and unavailable navigation text/tags.
- Keyboard focus is clearly visible on the skip link, desktop navigation,
  mobile trigger, dialog close button, and mobile navigation link.
- Real tab order remains `[skip, trigger]` at 375px and `[skip, Overview]` at
  1440px; the dialog traps focus and restores it to its trigger on close.
- Neither viewport has horizontal overflow, clipped content, or an unexplained
  stretched/empty panel.
- The page retains a clear research question, workflow state, claim-to-source
  trace, read-only authority statement, and persistent demo-data label.
- A reviewer can identify at least three deliberate Nexus Scholar motifs in the
  screenshots and tie each one to `VISUAL_DIRECTION.md`.
- Existing component tests remain green; visual changes add or update assertions
  only when they protect meaningful semantics or accessibility.

**Gate:** Run `npm run typecheck`, `npm test`, `npm run build`, and
`npm run test:browser`. Inspect the resulting 375px and 1440px screenshots by a
human or image-capable reviewer; automated measurements alone do not approve
visual direction. Record exact contrast ratios for repaired sites. The packet
passes only with zero serious/critical axe violations, zero color-contrast
failures, a reviewer-approved visual composition, and no changes outside the
allowed paths.

**Stop condition:** Stop after the redesigned overview and its visual-direction
document pass review. Do not begin UI-02, add routes, introduce an API client,
or connect to a real workspace in this packet.

## UI-01d — Internationalization and bidirectional foundation

**Why this packet exists:** Locale architecture must be established before
UI-02 through UI-06 multiply user-facing strings and layout assumptions. This
packet internationalizes the existing shell and overview only. It does not
translate scientific source content, canonical artifacts, identifiers, audit
records, or controlled contract vocabulary.

**Initial proof locales:**

- `en` — source and fallback locale.
- `fr` — left-to-right translation proof.
- `ar` — right-to-left and Arabic-script proof.

These locales prove the architecture; they do not claim that translation has
been professionally reviewed. Until such review occurs, non-English catalogs
must be marked as demonstration translations in developer documentation.

**Allowed paths:**

- `apps/research-ui/app/` locale routing, layout, and metadata files
- `apps/research-ui/components/` components used by the shell and overview
- `apps/research-ui/i18n/` configuration and request helpers (new)
- `apps/research-ui/messages/` locale catalogs (new)
- `apps/research-ui/lib/` presentation-only locale helpers
- UI component and browser tests directly covering internationalization
- `apps/research-ui/package.json` and `package-lock.json` only if the selected
  internationalization library requires them
- `apps/research-ui/README.md`, `apps/research-ui/GATES.md`, and screenshots
- `apps/research-ui/docs/I18N.md` (new)

Any additional path requires a written scope-extension reason before editing.
Python, contracts, kits, pins, workspaces, audit files, and E3 documents remain
forbidden.

**Architecture deliverables:**

1. `I18N.md` records the locale strategy, URL convention, fallback behavior,
   message ownership, supported-direction map, formatting rules, and the
   boundary between interface translation and authoritative research content.
2. Locale-aware routing with one canonical URL strategy. Locale selection must
   be explicit and testable; it must not depend only on mutable browser state.
3. Server-compatible message loading. Do not force the entire application into
   client rendering merely to translate strings.
4. Separate, structurally equivalent message catalogs for `en`, `fr`, and `ar`.
   Catalog keys describe meaning or interface role rather than English wording.
5. A language selector usable by keyboard and assistive technology, showing
   each language in a recognisable form without flags.
6. Correct document `lang` and `dir` values for every locale, with `dir="rtl"`
   for Arabic and `dir="ltr"` for English and French.
7. Locale-aware number, date/time, and list formatting through `Intl` or the
   selected library. Do not localize canonical identifiers, hashes, exact audit
   timestamps, filenames, refusal codes, or quoted source text.
8. Bidirectional-safe shell, navigation, workflow, and evidence-lineage layouts
   using logical properties or direction-aware utilities instead of scattered
   left/right overrides.

**Translation boundary:**

- Translate application chrome, explanations, navigation, state descriptions,
  accessibility labels, empty/error text, and demonstration fixture prose.
- Preserve authoritative user-supplied research questions and source content in
  their original language unless the future API explicitly provides a distinct
  translation plus provenance.
- Preserve canonical artifact IDs, algorithm versions, checksums, exact audit
  timestamps, refusal codes, DOI values, file paths, and quoted evidence byte
  for byte. Apply direction isolation (`bdi`, `dir="auto"`, or an equivalent
  reviewed pattern) when embedding them inside RTL prose.
- Never silently substitute English for a missing safety-critical label. A
  missing required message fails development/test gates rather than rendering a
  raw key or an empty string.

**Negative cases:**

- No flag icons as language labels.
- No machine-translation API or network call at render time.
- No locale stored only in `localStorage`.
- No concatenated sentence fragments whose grammar assumes English word order.
- No manual date/number formatting and no locale-sensitive values used as
  canonical identifiers or persistence keys.
- No `text-left`, `ml-*`, `mr-*`, `left-*`, or `right-*` layout patch added
  where a logical/direction-aware alternative expresses the intent.
- No claim that French or Arabic wording is publication-quality without review
  by a fluent human.

**Acceptance criteria:**

- Direct navigation and refresh work for the same overview in all three
  locales; unsupported locales produce the documented refusal/not-found path.
- The `<html>` element exposes the correct `lang` and `dir` before hydration.
- All existing shell and overview interface strings come from catalogs; tests
  fail when a required key is removed from any locale.
- Catalog key sets are mechanically identical across `en`, `fr`, and `ar`.
- The language selector announces its purpose, current selection, and options;
  switching locale preserves the equivalent route rather than returning to an
  unrelated page.
- Arabic screenshots show a genuinely mirrored reading flow without reversed
  identifiers, numbers, icons whose meaning is directional, or broken focus
  order.
- Demo-data disclosure remains visible and correctly translated in every locale.
- English, French, and Arabic retain the UI-00b accessibility guarantees:
  visible focus, WCAG AA contrast, no horizontal overflow, functional skip
  link, dialog focus trap, and correct focus restoration.
- Long-string tests (at least 30 percent expansion) do not clip navigation,
  state labels, headings, or controls at 375px and 1440px.

**Gate:** Run `npm run typecheck`, `npm test`, `npm run build`, and
`npm run test:browser`. Browser coverage must exercise all three locales, both
directions, unsupported-locale behavior, selector keyboard use, refresh/deep
link behavior, catalog completeness, and 30-percent-expanded strings. Capture
375px screenshots for `en`, `fr`, and `ar`, plus 1440px screenshots for `en`
and `ar`. An image-capable or fluent reviewer must inspect Arabic direction and
French/Arabic wording; automated screenshots alone do not approve translation
quality.

**Stop condition:** Stop after the existing shell and overview are fully
locale-aware and the catalogs, routing, directionality, formatting, and gates
are documented. Do not internationalize screens that UI-02 through UI-06 have
not created, call translation services, add an API boundary, or translate
authoritative research artifacts.

## UI-02 — Project overview

**Scope:** overview route and presentation components.

**Deliverable:** Research question, current stage, corpus statistics, last significant event, and clear navigation to screening/evidence/audit.

**Negative cases:** Counts never inferred in the browser; absent counts render unknown rather than zero.

**Gate:** Populated, loading, empty, and error fixtures; component tests.

## UI-03 — Workflow timeline

**Scope:** `components/workflow-timeline.tsx` and tests.

**Deliverable:** Accessible stage sequence showing complete, active, waiting, and refused states with text and icons, not color alone.

**Negative cases:** No claim that a future stage is complete; refused is distinct from failed infrastructure.

**Gate:** State matrix test and narrow-width visual check.

## UI-04 — Screening workspace

**Scope:** fixture-backed screening page only.

**Deliverable:** Study citation, abstract, criteria panel, decision choices, reason field, and explicit disabled-submit explanation until the API exists.

**Negative cases:** No write to `workspaces/`; no decision persisted in local storage; no automatic inclusion presented as a human decision.

**Gate:** Keyboard-only flow, validation states, and disabled mutation test.

## UI-05 — Evidence lineage

**Scope:** evidence route and lineage components.

**Deliverable:** Claim -> chunk -> extracted document -> study -> screening decision trace, with source details progressively disclosed.

**Negative cases:** No invented quote, DOI, artifact ID, or acceptance status; missing lineage renders a refusal state.

**Gate:** Complete and broken-lineage fixtures plus accessibility check.

## UI-06 — Audit activity

**Scope:** audit route and event presentation components.

**Deliverable:** Human-readable chronological feed with actor, action, object, outcome, and expandable technical provenance.

**Negative cases:** UI does not rewrite, reorder, or append events; technical timestamps remain exact.

**Gate:** Empty, mixed-outcome, and malformed-event fixtures.

## UI-07 — Presentation API specification

**Blocked until requested.** This is the first cross-boundary packet.

**Scope:** documentation and typed API schemas before Python implementation.

**Deliverable:** Read-only endpoints for project summary, workflow status, evidence lineage, and audit feed; one separately reviewed screening-decision command.

**Negative cases:** API never exposes arbitrary workspace paths and never accepts caller-supplied canonical IDs as authority.

**Gate:** Contract review, threat review, fixture examples, then implementation in a separate packet.

## Prompt for a small UI agent

```text
Work only on packet UI-0N from docs/architecture/research_ui/AGENT_WORK_PACKETS.md.
Read apps/research-ui/AGENTS.md and docs/architecture/research_ui/README.md first.
Stay inside the packet's allowed paths. Use presentation-only mock data and keep
the Demonstration data label visible. Do not edit Python, contracts, tools, pins,
workspaces, audit files, or E3 documents. Do not invent identifiers or acceptance
results. Use the local tailwind-plus MCP to search for the smallest suitable
Application UI pattern, then adapt it into Nexus Scholar-specific components;
do not copy a complete template. Implement loading, empty, refused/error, and
populated states where applicable. Run targeted type/tests and inspect the route
at mobile and desktop widths. Report files changed, exact checks, screenshots,
and any API capability you need but did not invent.
```
