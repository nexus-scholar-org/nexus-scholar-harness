# 12 Details disclosure (shared rule)    Status: FINAL | Phase 2 Screening | Applies to 01, 03, 05, 09, 10 (and to the shared state card) | Milestone M6-beta

Boards: none. This page restates a decision the researcher approved on 2026-11-07 ("Details on demand", `docs/decisions.md`). It introduces no visual language: the disclosure is the native `<details>` and `<summary>` pattern the screens already use (Home "Run from the terminal", Triage "Decision history", Publish "Defer", Export "What this statement is based on"), styled with the existing `brand` link colour. Rule source: BRAND_BOOK principle 3, "plain words first, raw value underneath", read as: **the raw value is one disclosure away, never inline.**

**Purpose.** Each screen shows what the researcher acts on. Identifiers, fingerprints and proofs are still there, one click away, for the researcher who audits and for the tests that check provenance.

## The rule
1. **One disclosure per card.** A card that holds identifiers or proofs gets exactly one "Details" disclosure, placed at the end of the card. A card with nothing to hide has none. No nesting.
2. **Closed by default.** No `open` attribute on first render. The browser may keep it open while the page stays mounted; a reload closes it.
3. **Keyboard-reachable.** Native `<summary>` is in the tab order; `Enter` and `Space` toggle it. Target at least 44 px high. Visible focus ring (`focus` token). It never traps focus and has no shortcut key.
4. **The same label everywhere.** The summary text is `screening.details.label` = "Details" (fr "Détails", ar "التفاصيل") on every screen, in every card. A card may add a short heading *inside* the opened panel (for example "What this statement is based on"), never in the summary.
5. **Nothing leaves the DOM.** Content stays in the document inside the closed `<details>` (it is hidden by the browser, not removed or lazy-loaded). Playwright provenance checks keep finding every value with the same locators, after opening the disclosure where they assert visibility. A test that asserts a value is *visible* must open the disclosure first.
6. **Values keep their form.** Inside the panel each value is a `DataCell` (mono, `dir="ltr"`, selectable) with its plain label beside it, never a bare hash. Numerals Latin. In Arabic the panel mirrors; the values stay LTR.
7. **Plain sentence stays outside.** A refusal card keeps its plain sentence, its role colour and its next step on the card; only the typed code moves inside Details. A decision card keeps one word, "Saved" (`screening.details.saved`), with the time as hover text (`title` from the key `screening.details.savedAt`, "Saved {time}"); the same time is also written inside Details, so the hover is not the only way to read it.
8. **Failing is not provenance.** A value the researcher must act on is never hidden: a failing check keeps its count on the line, a conflict keeps its card. Only values that prove or identify move.
9. **Locales.** Every string is a key, with en, fr and ar. No literal `aria-label`, `title`, `alt` or `placeholder` (N9 guard).

## Component
A thin wrapper `Details` in `apps/research-ui/components/ui/base.tsx` around native `<details>`; it takes the card's content as children and renders `screening.details.label`. It is not a new brand component: it is the pattern already used by hand in four screens, written once so the label cannot drift. Test: `details.rule.test.tsx` (closed by default; summary reachable by `Tab`; label equal in en, fr, ar; content present in the DOM while closed; no screen renders a second disclosure inside a card).

## Copy
`screening.details.label` (Details), `screening.details.saved` (Saved), `screening.details.savedAt` (Saved {time}, hover text), `screening.details.studyId` (Study id), `screening.details.doi` (DOI), `screening.details.protocol` (Protocol fingerprint), `screening.details.generation` (Generation), `screening.details.fingerprint` (Generation fingerprint), `screening.details.digest` (SHA-256), `screening.details.event` (Event id), `screening.details.recordedAs` (Recorded as you · HUMAN · {time} · protocol {fingerprint}), `screening.details.model` (Model), `screening.details.prompt` (Prompt hash), `screening.details.proposal` (Proposal id), `screening.details.batchFile` (Batch file), `screening.details.code` (Code). fr and ar fall back to en for the proof labels only until translated (plan §7); `screening.details.label` is translated from the start.

## What moves behind Details, per screen
Element names are those in `apps/research-ui/components/` as of 2026-11-07, so the change can be found.

### 01 Screening home (`screening-home.tsx`, `HomeReady`)
| Today | Moves to |
| :-- | :-- |
| Batches table, first column `<DataCell>{b.batch_file}</DataCell>` (raw file name) | The row reads "Batch {n}" (`screening.home.batch.n`); the file name goes into the Batches card's Details |
| Progress tiles "Records with an agent draft" (`agentProposed`, with its note) and "Conflicts to resolve" (`conflicts`) | The progress card's Details. A non-zero conflict count is not hidden: the `conflict` StateCard stays above (rule 8) |
| `StateCard` for `NOT_PREPARED` (and `STALE_BINDING`, `conflict`): the typed code line in the card | The code goes into the card's Details (see "Shared state card" below) |
| "Drafts: hidden until you decide · Mode: you see every record" line (`settings`) | Below the first screen, in the "Who screens" section; it is not an identifier and does not go in Details |

Not moved into Details: the "Run from the terminal" block is already a `<details>`. It is a how-to, not a proof, so its summary stays "Run from the terminal" (rule 4 applies to proof disclosures only). It goes below the first screen with the other secondary blocks (see 01).

### 03 Triage, desktop (`triage-page.tsx`)
| Today | Moves to |
| :-- | :-- |
| Record meta row: `<DataCell>{record.study_id}</DataCell>` and the DOI anchor text `record.doi` | Record card's Details: Study id, DOI (the raw form; still an `<a href="https://doi.org/…">`) |
| Decision card, `t("recordedAs")` line ("Recorded as you · HUMAN · time · protocol sha") | Decision card shows "Saved" (hover: the time); the full line, the event id of the decision and the protocol fingerprint go into the card's Details |
| `t("staleBanner")` with the inline `STALE_BINDING` span, and `t("refused", {code})` | Plain sentence stays; the code goes into the banner's Details |
| Aside (`data-testid="proposal-aside"`), revealed state: model, `prompt_sha256` and `proposal_id` `DataCell`s | The aside's Details: Model, Prompt hash, Proposal id |
| Event ids in the decision history (`record.history[].event_id`, used as keys; the list shows time, outcome, reason) | The history `<details>` stays as is (it is a feature, "Decision history"); event ids are added inside the decision card's Details, one per history row |

### 05 Record detail (`RecordDetail`, rendered inside the page above)
Same elements as 03 (05 is the record card, the checklist and the aside). Additionally the revealed comparison keeps criterion ids visible (they are the answer keys, not provenance); the "proposal hash revealed after decision" part of the provenance note goes into the aside's Details. On the phone (04, built in M2) the `STU-` id on the card label moves into the same disclosure.

### 09 Publish (`screening-publish.tsx`)
| Today | Moves to |
| :-- | :-- |
| Published banner `t("published", {id})` with the raw generation id | Banner reads "Published" (`screening.publish.published`); the generation id goes into the gate card's Details |
| Checks list: each line shows `c.detail` (mono text after the name) | One line per check: pass mark and name. The details of passing checks go into the Checks card's Details; a failing check keeps its count on the line (rule 8) |
| Batches card: `<DataCell>{label}</DataCell>` (batch file name without `.json`) and the same label inside the code-field and button names | Rows read "Batch {n}"; button and field names use "batch {n}"; the file name goes into the Batches card's Details |
| Gate panel (`GatePanel`, label `publishGate`): generation fingerprint, and the digests of the files to be written (spec 09 "Will be written", not rendered by the component today) | The gate card's Details: generation id, generation fingerprint, file digests |
| PRISMA preview card | Nothing moves: the numbers and the reasons table stay on the card |

### 10 Export and methods (`screening-export.tsx`)
| Today | Moves to |
| :-- | :-- |
| Header row: label "Generation" and `<DataCell>{shortId}</DataCell>` (first 16 characters, full id in `title`) | Header keeps only the badge "Published · current"; the generation id goes into the methods card's Details |
| Footer line `t("fingerprint")` with `<DataCell>{methods.generation_fingerprint}</DataCell>` | The methods card's Details |
| `<details>` "What this statement is based on" (sources table: `source.path`, `source.digest`) | Same disclosure, now labelled Details; the heading "What this statement is based on" moves inside the panel |
| Refusal cards | Code inside Details (shared state card) |
| Methods paragraph, counts table, reasons table, "Not stated", "Caveats", the export card | Nothing moves. The paragraph is now first in the card (see 10) |

### Shared state card (`screening-state-card.tsx`, `StateCard`)
The card shows the typed code as selectable text in the role colour (`data-state={code}`, `<code dir="ltr">`). Under this rule the title, the plain sentence and the next-step button stay; the code and the "affects" line go into a Details disclosure inside the card. `data-state` stays on the section, so tests keep finding the code by attribute. Spec 08 lists every refusal card and says each shows its code: that sentence is overridden by this rule; 08's states, wording and next steps are unchanged.

## Out of scope
Discovery screens (stretch), Workspaces list (00, which already shows the plain status), Import (11, its details are an import report), and phone screens 04 and 07.

## States
- **Default**: closed.
- **Empty**: a card with no proof to show renders no Details (not an empty one).
- **Loading**: no disclosure until the data it holds has loaded; the card's skeleton shows no summary.
- **Error**: a value that failed to load shows "Not stored" inside the panel, never a blank.
- **Partial**: the panel lists what is stored and says "Not stored" for the rest.
- **Offline**: unchanged; the panel shows the last loaded values with the screen's "as of" caption.
- **Protocol-changed**: the protocol fingerprint inside Details shows the old and the new value on 03 and 05.

## Backend calls
None. This is presentation only; every value comes from the call that the screen already makes (01, 03, 05, 09 and 10 specs list them). ✓ nothing new, ✗ nothing.

## Accessibility
Native disclosure semantics (`aria-expanded` is provided by the browser). Summary contrast `brand` on `ground`. The label is text, not an icon alone; a chevron may precede it and mirrors in RTL. Screen readers announce "Details, collapsed". Values inside are `dir="ltr"`.

## Acceptance tests
Vitest: `details.rule.test.tsx` (above), `home.compact.test.tsx`, `triage.details.test.tsx` (study id, DOI, recorded-as line and prompt hash are inside a closed `<details>`, and present in the DOM), `publish.details.test.tsx`, `export.details.test.tsx`. Playwright: the provenance checks keep passing unchanged with one added step, `await details.click()`; rendered axe on every amended screen in en and ar, light and dark (`tests-browser/rendered-axe.spec.ts`).

## Open questions
None.
