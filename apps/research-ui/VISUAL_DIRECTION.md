# Nexus Scholar visual direction

Packet **UI-01c**. This file is the design system of record for
`apps/research-ui/`. It states the character, the principles, and the concrete
token values the rest of the application must build on. UI-02 through UI-06
multiply this language across more routes; anything that contradicts this file
is a bug in the route, not a local variation.

`app/globals.css` is where these principles become values. This file is why
they have those values.

---

## 1. Product character

**A research instrument, not an analytics product.**

The application shows the state of a systematic literature review: a question
that was sealed, records that were found, decisions that were made, and the
path from each claim back to the text that supports it. The person reading it
is checking work, not scanning a dashboard. The nearest physical analogues are
an **evidence ledger**, a **protocol record**, and an **annotated scholarly
document** — not a CRM pipeline and not a finance product.

Three consequences that drive every later decision:

1. **Inspectability beats polish.** The reader's question is "where does this
   come from?" A design that hides lineage behind a hover state has answered a
   different question.
2. **Density is respect.** A workbench shows its work. Removing content to make
   a screen breathe is a defect, not polish.
3. **Restraint reads as authority.** A tool that trusts its own output does not
   decorate it.

### The anti-template test

The governing question from the packet: **could this page be relabelled as a
finance or CRM dashboard without changing its structure?**

Concretely, the things that make the answer **no**:

- Warm paper (`#f6f3ec`) and ink (`#1c1a17`) rather than white-on-slate-900.
- Hairline rules as the only separator. No floating cards, no `shadow-sm`.
- Marginal ordinals and marginal node kinds in the left margin, like a numbered
  document — not a vertical stack of equal panels.
- The workflow is **one ruled record** whose entries share baselines, not six
  interchangeable tiles.
- A display serif for the document voice and a system UI face for everything
  precise. Two roles, no web font, so the screen reads the same on conference
  wifi as on a laptop.
- State is a **stamp**, not a pill; the active route is an **underline**, not a
  filled chip.

If a future change makes the page relabellable as a CRM, the anti-template test
has failed even if every screenshot still looks tidy.

---

## 2. Principles

Each principle is named so a motif can cite it. The motifs in §9 are the
implementations a reviewer should look for in `screenshots/`.

### P1 — Rules, not containers

Structure is carried by hairlines and by whitespace, never by enclosing a thing
in a box. A section is not a card; it is a stretch of paper with a rule above
it.

*Rationale:* boxes imply objects. A review is a document, and its structure is
ruled, not boxed. This is also the single largest source of the old
generated-SaaS look, so it is the one worth being dogmatic about.

*Seen at:* `components/workflow-timeline.tsx:27` (`border-t border-rule-strong`
on the `<ol>` with no container), `components/evidence-chain.tsx:29`.

### P2 — Margins carry the reading order

Secondary information — ordinals, node kinds, stage numbers, the eyebrow — lives
in the **left margin**, not inline after the thing it labels. The margin is the
document's most load-bearing region, and a reader uses it to skim.

*Rationale:* inline annotations force the eye to re-parse each line. A margin
column is scanned once. This is what makes the evidence trail read as a trail.

*Seen at:* `components/evidence-chain.tsx:40` (the marginal ordinal, a real
`<span>` first child), `:52` (the marginal node kind at `lg:`, stacked above the
label at 375px), `components/workflow-timeline.tsx:34` (the `Stage N` ordinal).

### P3 — Provenance is stamped, and stamps are square

A fact that asserts where it came from — a workflow state, the
`Demonstration data` marker, a "Not yet available" annotation — is rendered as a
**square-cornered hairline stamp** with uppercase tracked text. Never a pill.
Never colour alone: the state word is always in the stamp.

*Rationale:* a pill is decorative vocabulary. A stamp is an assertion, and this
application's whole claim is that assertions are inspectable. Square corners also
survive at 11px, where a pill's curvature is sub-pixel noise.

*Seen at:* `components/status-badge.tsx:26-27`, `components/app-shell.tsx:74`
(`Demonstration data`), `components/primary-nav.tsx:67` (`Not yet available`).

### P4 — The document voice is opt-in

One serif, used for exactly three things: the product name, the route title, and
section headings. Everything that must be *read precisely* — body copy, labels,
ordinals, counts, stamps — is the system UI face. Numbers are
`font-variant-numeric: tabular-nums` so they sit in columns.

*Rationale:* the serif is what makes the page a document instead of a product.
Keeping it off the data is what keeps the data legible. Two roles, both local —
a meetup demo must not depend on conference wifi.

*Seen at:* `app/globals.css:80-83` (the two `--font-*` roles),
`app/globals.css:103` (`tabular-nums`), `app/page.tsx:34` (`font-display` on the
`<h1>` only).

### P5 — Colour means something, or it is a hairline

Every saturated colour on the page is a **role with a meaning**: `--color-
evidence` for provenance and the current route, `--color-success` / `-warning` /
`-refusal` for workflow state, `--color-focus` for the focus ring. The
`--color-rule-*` pair carries no meaning and is never used to signal. No
component invents a raw hex or a raw `slate-*`/`blue-*` utility.

*Rationale:* one accent colour used for "you are here" *and* "this is a link"
*and* "this state is active" is three meanings in one token, which is why
generic dashboards feel generic. Splitting the roles is what lets the palette be
warm without becoming decorative.

*Seen at:* `app/globals.css:52-70` (the rule and state blocks),
`components/status-badge.tsx:29-34` (the only definition of state colour),
`components/primary-nav.tsx:61` (`aria-[current]:decoration-evidence`).

### P6 — Restraint is enforced, not aspirational

No decorative gradient, no glass effect, no drop shadow for depth, no hero copy,
no decorative chart, no oversized empty panel. The **only** rounded, shadowed
element in the application is the skip link's focused reveal, which is exempt
because it communicates interaction: it is an overlay, and in a design whose
depth model is "no depth" an overlay needs something to say "I am on top".

*Rationale:* each of these is individually defensible and collectively
constitutes the generic look. The exemption is stated so the exception is
arguable rather than accidental.

*Seen at:* `app/globals.css:158-194` (the exemption, argued in place),
`components/mobile-nav.tsx:52-56` (the panel — separated by a hairline and the
backdrop, not by `shadow-xl`).

---

## 3. Palette roles

Declared once, in `app/globals.css`'s `@theme`. Components consume the role; a
raw hex in a component is a defect.

| Token | Value | Role | Meaning carried |
|---|---|---|---|
| `--color-paper` | `#f6f3ec` | Ground of the route | The substrate. Warm, so the ink reads as ink. |
| `--color-leaf` | `#fdfbf7` | Chrome, and the mobile dialog panel | The lighter sheet. Banner/footer/dialog sit *on* the paper. |
| `--color-ink` | `#1c1a17` | Primary text | The record's own voice. |
| `--color-ink-muted` | `#4a453d` | Body copy, descriptions | Secondary text, still full contrast. |
| `--color-ink-faint` | `#6b6357` | Marginal annotations, ordinals | The tightest role at 5.34:1. Use only at 11px+ and only for annotations. |
| `--color-rule` | `#ded5c3` | Hairline between records | Separation. Never meaning. |
| `--color-rule-strong` | `#bfb39b` | Heavy rule, chrome divider, stamp edge | Structure. Never meaning. |
| `--color-evidence` | `#1f3a5f` | Provenance: marginal kinds, eyebrows, the current route, the `active` state | "This is traceable / you are here / this is running." |
| `--color-success` | `#1f5c3a` | `complete` | — |
| `--color-warning` | `#7a5410` | `waiting`, and the `Demonstration data` marker | Caution, not alarm. |
| `--color-refusal` | `#8f2f28` | `refused` | — |
| `--color-focus` | `#1c1a17` | The one focus ring | Interaction. Its own token so a change to body ink cannot silently restate it. |

### Measured contrast

Ratios read out of axe-core's own `color-contrast` pass nodes on the rendered
page at 375px and 1440px (`GATES.md` §3.7). Every role clears WCAG 2.1 AA
normal-size 4.5:1 on **both** grounds:

| Role | on `--color-paper` | on `--color-leaf` | Required |
|---|---|---|---|
| `ink` | 15.66:1 | 16.79:1 | 4.5:1 |
| `ink-muted` | 8.57:1 | 9.19:1 | 4.5:1 |
| `ink-faint` | **5.34:1** | **5.72:1** | 4.5:1 |
| `evidence` | 10.36:1 | 11.11:1 | 4.5:1 |
| `success` | 7.15:1 | 7.67:1 | 4.5:1 |
| `warning` | 6.11:1 | 6.54:1 | 4.5:1 |
| `refusal` | 7.27:1 | 7.80:1 | 4.5:1 |

`ink-faint` is the tightest role and has 0.84 of headroom. A future edit that
darkens `--color-paper` must re-measure it rather than assume.

> **Reproducibility.** These ratios are **measured once**, in the UI-01c run, and
> are **not reproducible by the committed test suite**. The committed browser
> suite asserts that *every text node passes* 4.5:1 — which is what makes these
> numbers safe to design against — but it does not assert any individual ratio, so
> a future edit could invalidate a figure in this table without turning a gate red.
> `GATES.md` §3.7.1 is the record: which values are enforced, which are snapshots,
> and why. **Treat these as design inputs, not as gates.**

### State distinguishability

`tests/status-badge.test.tsx` only proves the four states carry distinct class
*strings*, which four visually identical palettes would also satisfy. Measured
instead, in CIE Lab:

| State | Token | on paper | Closest neighbour | ΔE |
|---|---|---|---|---|
| `complete` | `--color-success` | 7.15:1 | `waiting` | **47.8** |
| `active` | `--color-evidence` | 10.36:1 | `complete` | **51.1** |
| `waiting` | `--color-warning` | 6.11:1 | `refused` | **34.5** |
| `refused` | `--color-refusal` | 7.27:1 | `waiting` | **34.5** |

The tightest pair is `waiting`~`refused` at ΔE 34.5 (ochre against oxide), an
order of magnitude above a just-noticeable difference. Colour is in any case
never the only channel: each stamp renders the state word itself.

> **Reproducibility.** These ΔE values are **measured once**, computed from the
> token hexes in the UI-01c run, and are **not reproducible by the committed test
> suite** — no committed test measures colour distance, and
> `tests/status-badge.test.tsx` still asserts only that the four states carry
> distinct class *strings*. `GATES.md` §3.7.7 is the record. Two further limits
> travel with the table: `refused` is **never instantiated** by
> `lib/mock-project.ts`, so its row is derived from its token rather than
> measured off a rendered element; and the three other rows were read off the live
> DOM in a run that has since been deleted. **Do not cite these as enforced.**

---

## 4. Typography roles

Two roles. **No web font, no font CDN, no `@font-face`** — decision D1, and the
application must render correctly if a network fetch fails or never happens.

| Role | Stack | Used for | Never used for |
|---|---|---|---|
| `--font-display` | `georgia, "Iowan Old Style", "Palatino Linotype", palatino, "Book Antiqua", "Times New Roman", serif` | Product name, `<h1>`, section `<h2>`, dialog title | Data, labels, body |
| `--font-interface` | `ui-sans-serif, system-ui, -apple-system, "Segoe UI", roboto, "Helvetica Neue", arial, sans-serif` | Everything read precisely: body, descriptions, ordinals, counts, stamps, the whole navigation | Titles |

`--font-interface` is the inherited `body` default; `--font-display` is applied
per element, so adding a heading does not require remembering to switch back.

**Scale.** 36px/30px `<h1>` (viewport-dependent), 20px section `<h2>`, 18px
research question and counts, 16px stage and node labels, 14px body, 12px
chrome, 11px stamps and marginal annotations. Marginal annotations are
`uppercase` with `tracking-[0.16em]` and `text-[0.6875rem]` — the letterspacing
is what makes 11px read as an annotation rather than as small body text.

**Numerals.** `font-variant-numeric: tabular-nums` on `body`, so stage
ordinals, counts and trail numbers align vertically like a ledger column
instead of wobbling with proportional digits.

**No monospace role.** Exact identifiers are distinguished by case and
tracking, not by a third typeface. Adding one would breach the two-role rule.

---

## 5. Spacing and radius

**Spacing.** A 4px-derived scale via Tailwind utilities. Two structural
constants:

- Section rhythm: `mt-14` between the route's three sections (was `mt-10`/`mt-12`
  sized for cards). Generous, because the separators are hairlines and need air
  to read as intentional rather than as a border-bug.
- Record internals: `py-4` per row with `border-b border-rule` between entries,
  and a heavier `border-t border-rule-strong` above the whole sequence. The
  change of rule weight is what makes one record read as one record.

**Radius.**

| Where | Radius | Why |
|---|---|---|
| Skip link, focused | `0.25rem` | Exempt (A4): an overlay needs an edge. Argued at `app/globals.css:159`. |
| Mobile dialog panel | `0` | It is a sheet sliding over the page, bounded by the viewport, not a floating card. |
| The state-stamp dot | `rounded-full`, `size-1.5` | A dot. 6px diameter; the only curve in the composition, and it is a dot. |
| Everything else | `0` | — |

There is no `rounded-lg`, no `rounded-xl`, no `rounded-full` on a container.

---

## 6. Provenance treatment

The application's signature is the **visible path from a research claim back
through evidence to provenance**. It gets a dedicated primitive rather than a
generic list:

1. **A real DOM numeral** in the left margin of each `<li>`. Real text, not a
   CSS counter — a counter would render the same picture while failing
   `tests/evidence-chain.test.tsx`, and it would be unreadable to a screen
   reader and to anything reading the DOM.
2. **A continuous hairline spine.** `border-l` on each entry's content wrapper,
   contiguous across siblings with no vertical gap, so the five nodes read as
   one unbroken line rather than five separate rows.
3. **A marginal node kind** (`claim`, `chunk`, `document`, `study`, `decision`)
   in `--color-evidence`. At ≥1024px it stands in its own margin column beside
   the label; at 375px it sits directly above the label rather than disappearing
   behind a breakpoint.

Every state and provenance fact on the page is a square stamp with its own text
(P3): the workflow state, the `Demonstration data` marker, the `Not yet
available` navigation annotation. **A stamp's text is always the assertion** —
never an icon, never colour alone, never a tooltip.

The `Demonstration data` marker is a **safety** control, not chrome. It lives in
the shell's `<header>` at every viewport width, inside the disclosure never, and
`tests/home-page.test.tsx:32` pins that location. It may be restyled; it may not
be moved, demoted, or hidden.

---

## 7. Use / avoid

### Use

- A hairline above a record; a heavier hairline above the whole sequence.
- A marginal ordinal and a marginal label sharing one left band.
- A square stamp for any assertion about provenance or state.
- An underline for the active route; a transparent decoration for hover, so both
  states use one mechanism.
- Warm paper for the ground, `--color-leaf` for chrome that must read as a
  separate sheet.
- `text-ink` for anything the reader must act on; `text-ink-muted` for
  supporting prose; `text-ink-faint` for annotations only.

### Avoid

| Pattern | Why |
|---|---|
| A rounded card per section or per row | The core of the old look. Rules carry structure instead (P1). |
| `shadow-sm` / `shadow-xl` for depth | Depth is not the depth model. The one exempt case is argued in place (P6). |
| `rounded-full` pills on containers | Reserved for dots. A pill is decorative vocabulary (P3). |
| A gradient, glass, or blur | Decorative, and invisible to the reader's actual task. |
| Hero copy, a tagline block, a marketing headline | This is an instrument panel (P1). |
| A chart with no data behind it | No decorative chart, ever. |
| A dark callout card for an aside | Replaced by an editorial rule in `--color-evidence` (P1, P5). |
| State signalled by colour alone | Each stamp carries its word (P3). |
| A raw hex or raw `slate-*`/`blue-*` utility in a component | Roles only (P5). |
| Tabular numerals for running prose | `tabular-nums` is for columns (P4). |
| An oversized panel beside short content | `self-start` keeps the aside at its content's height (`GATES.md` §3.7). |

---

## 8. What is deliberately absent

- **Web fonts.** Accepted cost: no custom glyph identity. Recorded as decision D1.
- **Dark mode.** `color-scheme: light` is declared. A dark theme would need its
  own measured contrast table per role, and is not in this packet's scope.
- **A third typeface role.** See §4.
- **Motion.** No transitions on the record surfaces. The one dynamic element is
  the mobile disclosure, which is a Headless UI dialog and behaves as one.

---

## 9. The motifs a reviewer should look for

Each is visible in a committed screenshot, and each names its principle.

| # | Motif | Principle | Where | Screenshot |
|---|---|---|---|---|
| M1 | The evidence trail: five numbered entries on one unbroken hairline spine, each with its node kind in the left margin | **P2 Margins carry the reading order** | `components/evidence-chain.tsx:40`, `:50`, `:58` | `1440-evidence-trail.png`, `1440-overview.png` |
| M2 | The workflow as one ruled record: shared baselines, a heavy rule above the whole sequence, hairline between entries, `Stage N` in the margin | **P1 Rules, not containers** | `components/workflow-timeline.tsx:27`, `:31`, `:34` | `1440-overview.png`, `375-overview.png` |
| M3 | Square provenance stamps — the workflow states, `Demonstration data`, `Not yet available` — each carrying its own text | **P3 Provenance is stamped** | `components/status-badge.tsx:26-27`, `components/app-shell.tsx:74`, `components/primary-nav.tsx:67` | `375-overview.png`, `1440-overview.png` |
| M4 | The warm paper ground with the chrome on a lighter leaf sheet, divided by hairlines only | **P5 Colour means something** + P1 | `app/globals.css:46-47`, `components/app-shell.tsx:51`, `:91` | all six |
| M5 | The editorial aside: a heavy ink-blue rule down the left edge instead of a dark rounded callout card | **P1** + P5 | `app/page.tsx:84` | `1440-overview.png` |
| M6 | The masthead: a tracked `Project overview` eyebrow standing in the left margin of a two-column title block, over a serif `<h1>` | **P2** + **P4 The document voice is opt-in** | `app/page.tsx:30`, `:34` | `1440-overview.png` |

The governing anti-template question (§1) is answered by M1, M2 and M5 together:
a CRM relabelled with these components would have to replace the margin column
with a status chip column, replace the spine with card borders, and replace the
editorial rule with a callout.
