# Nexus Scholar Provenance

Every number has a source. That is the whole brand.

Nexus Scholar helps a researcher run a systematic literature review with agents doing the volume work and the researcher making every decision that matters. The interface has one job: show the evidence behind each number, each decision and each claim, so a PhD student can defend the review and a supervisor can check it in minutes.

This system is built fresh (no logo, no existing brand assets) from the Phase 0 to Phase 4 wireframes and their UX reviews in the harness repository, `docs/ux/`. It replaces the grey wireframe look with a finished one.

## Who it is for

- **PhD students** doing their first systematic review, often alone. They need to feel guided, never patronised, and to see where their own time goes.
- **Supervisors** who will not read the whole workspace. They need to trace any claim to its studies in a few clicks.
- **Experienced reviewers** who already know the method. They need the machine to stay out of the way and to never dress a guess up as a result.

## Principles

1. **Evidence before assertion.** A count shows its denominator. A claim shows its studies. A cell shows its quote and page. If the evidence cannot be shown, say so instead of showing the number alone.
2. **Say what is not known.** "Not reported", "unclear", "lower bound", "could not resolve" are values with their own colour, never blanks and never silently defaulted.
3. **Plain words first, raw value underneath.** "Mixed subfields (top-3 share 0.41)" not "purity 0.41". The metric stays for the methods section; the sentence is for the person.
4. **The human is the gate.** Nothing is written, published or called a result until the researcher confirms. Gates look like gates (`brand-soft` panel, dashed `brand` border) and there is one per screen at most.
5. **Machine output is a draft.** Agent-drafted cells, claims and ratings sit on plain `surface` until a person verifies them; only then do they take an `include` tint. A draft is never styled like a verified value.
6. **Quiet by default.** Exclusions are routine, so `exclude` is a grey. Colour is spent on what needs attention: `unclear` for "needs you", `blocked` for "stop".

## Voice

Write from the researcher's side of the screen, the way a careful colleague would talk.

| Do | Don't |
| --- | --- |
| "So far 227 records need you; 2,121 agreed exclusions do not." | "Triage queue: 227 items pending." |
| "Crossref stopped at the 2,000 cap, so this count is a lower bound." | "Cap reached." |
| "'uas' has no anchor in this pool; kept off the search string." | "Synonym dropped." |
| "Draft. Built from 41 passages in 27 studies. Not reviewed." | "AI-generated summary." |

- Headlines are the question the screen answers or the state in one sentence, in the `display` style.
- Buttons name the effect: "Write workspace", "Approve and publish", "Search again, narrower". Never "OK", "Submit", "Continue" alone.
- Errors say what happened, what it affects and the next step. No apologies, no exclamation marks.
- Keep the method's own words where the researcher will meet them in the literature: PRISMA, inclusion criterion, risk of bias, kappa. Explain the tool's own words instead of using them: say "prompt echo", not "QEI"; "how focused the pool is", not "purity".
- Never emoji, never "AI" as a selling word. The agents are "screeners", "lanes" or "the agent".

## Colour

Light is the primary theme; dark mirrors it with the same roles. Every colour has a role; nothing is decorative.

**Neutrals.** `ground` is a cool off-white so `surface` sheets read as paper laid on a desk. `ink` is a blue-black, `ink-muted` carries every secondary line, and `hairline` draws all structure. There are no drop shadows except `shadow-overlay` on dialogs.

**Brand.** `brand` is an archive blue used for exactly one thing per screen: the primary action, plus links, the current step and focus rings. `brand-soft` marks the current step and the gate panel. A screen with two brand buttons has one too many.

**Anchor.** `anchor` is a burnt ochre reserved for provenance: citation anchors, verbatim quotes (`anchor-soft` behind them), DOIs that link out, the highlighted span in an abstract. It is the colour that says "this is where the evidence is". Do not use it for warnings; that is `unclear`.

**Status, four roles.** The pipeline's states all map onto four semantic colours, so a researcher learns them once:

| Role | Means | Examples across phases |
| --- | --- | --- |
| `include` | yes, found, verified, strong | included record, seed found, verified cell, supported claim, Strong trust |
| `unclear` | needs a person, partial, limited | unclear at screening, partly-found quote, lower bound, some concerns, Weak trust, PARTIAL harvest |
| `blocked` | stop, missing, failed | retracted, FAILED harvest, no quote, high risk, Blocked trust |
| `exclude` | no, routine, not applicable | excluded record, not reported, n/a, skipped |

Each role has a `-soft` tint for badge and note backgrounds. Text on a tint is always the role's full colour, never ink. All four full colours pass 4.5:1 on `surface` and `ground` in both themes; `include` and `blocked` also differ in lightness, not only hue, so they survive colour-blindness and greyscale print.

**Rules.**
- A `-soft` tint never carries ink text; a full status colour never fills an area behind text.
- Charts use the same four roles plus `brand` and `ink-muted`; no other hues.
- Dark theme is not an inversion: tints are deep, full colours are lifted, and `on-brand` turns dark so brand buttons stay readable.

## Typography

Three families, each with one job.

- **Literata** (`display`, `title`): a reading serif with optical sizes. It carries the question each screen asks and nothing else. Set `display` at 40/44, weight 600, tracking -0.01em. Never below 28px; at small sizes use Public Sans.
- **Public Sans** (`heading`, `body`, `body-strong`, `caption`, `label`): the working face for everything a person reads or fills in. `label` is uppercase with 0.05em tracking and always `ink-muted`.
- **IBM Plex Mono** (`data`, `terminal`): identifiers only. A DOI, a `SCI-` id, a fingerprint, a path, a command. Prose is never set in mono, and mono is never used to look technical.

Numbers that line up in a column take `font-variant-numeric: tabular-nums`. Running text stays near 65 characters wide.

All three faces are hosted on Google Fonts; load `Literata:opsz,wght@7..72,400;7..72,600`, `Public+Sans:wght@400;500;600` and `IBM+Plex+Mono:wght@400;500`, each with its fallback stack from `type.families`.

## Spacing and shape

A 4px base. Cards and panels pad with `space-4`; sections inside a screen separate with `space-5`; major regions with `space-6`; a desktop screen pads with `space-7`.

Corners are small and consistent: `radius-sm` on badges and inputs, `radius-md` on cards and buttons, `radius-lg` only on dialogs and the one feature panel of a screen. `radius-pill` is for quick-reply and filter chips only. Nothing else is round.

Structure comes from `hairline` borders and `surface` steps. A card is a `surface` sheet with a hairline; a selected row is `surface-raised` or `brand-soft`; a gate is `brand-soft` with a dashed `brand` border. No shadows, no gradients, no left-border accent bars.

## Layout patterns

- **Step header.** `label` eyebrow ("STEP 4 OF 6 · TRIAGE · YOUR DECISIONS"), then the `display` question, then one `body` line in `ink-muted` saying what changed from today. Every screen opens this way.
- **Evidence beside the decision.** A decision control never sits more than one glance from its evidence: the quote, the two lanes' answers, the per-database count. On wide screens evidence is the left two-thirds and the decision the right third.
- **Queue, then detail.** Lists of things needing a person (triage, near-twins, quarantined files) are a narrow queue on the left and the current item on the right, with keyboard keys shown in `data` style on the buttons.
- **The gate panel.** One per screen at most, bottom right: `brand-soft` fill, dashed `brand` border, a `label` in `brand`, one sentence saying nothing is written until confirmed, the primary button, and a secondary "dry run" or "save draft".
- **"Today" footer.** In proposal screens, a `terminal`-style line under each state card recording today's behaviour, so the reader sees what the design changes.
- **Tables.** `label` column headers in `ink-muted`, hairline row rules, tabular numbers right-aligned, status as a badge in its own column. Wide tables scroll inside their card.

## Iconography

Inline stroke icons at 1.5px, 16px or 20px, drawn in the text colour of their context (`currentColor`). No filled icons, no emoji, no icon without a visible label except in a toolbar where the `aria-label` names it. Status is shown by a badge with words, never by an icon alone.

There is no logo yet. The name is set in `title` or `display` style, in `ink`, and that is the mark.

## Accessibility

- Text 4.5:1 on its background in both themes (3:1 at 24px and above). The tokens were chosen to pass; keep them.
- Every control is a real `button`, `a`, `input` or `select` with a label; keyboard focus shows a 2px `brand` ring offset by 2px.
- Touch targets are at least 44px tall.
- Status is never colour alone: a badge always carries a word.
- Reduced motion is respected; the interface has no decorative motion in any case.

## Components in this system

Static previews of the patterns the wireframes rely on, built from the tokens above: a status badge, a trust level, an evidence quote, a gate panel and a data cell in its four states. They are references for building the console (`apps/research-ui`) and the Design canvases; there is no component bundle yet.
