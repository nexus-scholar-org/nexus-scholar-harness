# 05 Concepts and criteria    Status: FINAL | Phase 0 Inception | Route `/[locale]/inception/criteria?draft=rec_<32 hex>` (desktop only) | Milestone M4b

Boards: `Criteria` (D6, `docs/ux/phase0-inception/final/project/Criteria.dc.html`), `MobileCriteria` (M3, `.../MobileCriteria.dc.html`). Contract: `docs/architecture/inception-api.md` (Steps: `criteria`, `matrix`, `scope`). Code: `src/scholar_harness/inception/steps.py` (`criteria_with_decisions` `:191`, `_criteria` `:210`, `_matrix` `:221`, `build_intent` `:241`), `src/scholar_harness/inception/intent.py` (`CRITERION_SOURCES` `:241`, `CriterionDraft` `:250`, `draft_criteria` `:285`, `draft_default_concepts` `:208`), `src/scholar_harness/inception/genesis.py:365` (`_default_matrix_dimensions`). Decisions: `docs/decisions.md`, 2026-11-08 "Inception criteria are shown verbatim and accepted one by one" (INC-22). The load/save protocol, stepper, proposal-card styling, conflict handling and the phone rule are in 01 "Shared by 01, 04, 05, 06 and 07".

**Purpose.** Name the concepts the search will use, then read every screening criterion word for word with where it came from, and accept or drop each one; also choose the extraction-matrix columns and the advisory verification setting.

**Changed from the canvas.** Every cut, with the reason:
- **No anchoring.** The canvas's concept table has "Anchor", "Occurs in 4 of 25 titles or abstracts", "anchored · checked", the "Checks left 2 of 3" counter, the "Check 'uas'" button and the 'uas' not-anchored row. They need a pool and recon (INC-09 and INC-21 are deferred, and `steps/*` has no grounded evidence). The concept table here has Concept and Synonyms only, and each synonym is the researcher's. The canvas sentence "A DOI in the pool is not enough: the term itself has to appear…" is dropped with them, and so is `audit/recon_context.json`.
- **Source labels.** The canvas names sources "You typed it · Scope", "Suggested from the pool", "Paradigm default". The engine has four sources (`CRITERION_SOURCES`), shown through the API's own `source_label`: "written by the wizard from your proof answer"; "the {paradigm} paradigm's default exclusion, written by the wizard"; "your out-of-scope answer"; "typed by you". "Suggested from the pool" does not exist. The label is shown verbatim as the engine sends it.
- **No criterion numbers (I1, E3).** Those are not identifiers the engine knows; the decision key is the content-derived `crit_` id. Rows are shown in the engine's order with the short id in `data` style (first 9 characters, full id in the row's Details), never an invented number.
- **Edit.** The canvas puts Accept, Edit and Drop on every draft. A generated criterion has no text field to edit: the proof criterion is built from the proof answer (04), and the paradigm default exists only while the draft has no exclusion at all (`draft_criteria`, `intent.py:296`). So a generated row has Accept and Drop only. Its caption says how to change it: for the proof criterion a link "Change your proof answer"; for the paradigm default "Add an exclusion of your own below; then this default is no longer proposed." A typed row (`manual`, `out_of_scope`) has Edit and Drop. Editing the text makes a new `crit_` id with no decision yet (it counts as typed, so it is accepted unless dropped).
- **Drop keeps the row.** Drop writes `criteria_decisions[id] = false`; the row stays, struck through, with "Restore" (removes the decision: a generated criterion returns to "Waiting for you", a typed one to accepted). The canvas's "Kept in the draft history" is not claimed; there is no history, only the decision.
- **No live SCREENING_CRITERIA.md preview here.** The canvas side card renders it as you decide. `POST /preview` needs a complete draft (title, lead), so the compiled text appears on 06. This screen shows no compiled text.
- **No custom matrix column.** The canvas has "+ Custom column". `build_intent` keeps only default columns whose name is in `matrix_columns` (`steps.py:259-261`), so a custom name would be dropped silently. Cut.
- **No trust threshold number.** The canvas prints "Trust threshold 6.0". The threshold is an engine constant; the number is shown on 06 from the compiled intent. Here only the on/off setting (`verification_checks`) is offered, with the badge "advisory · Phase 4 is parked".
- **Matrix columns start unticked.** The canvas pre-ticks defaults. A suggestion is a draft and is not applied until the researcher acts, so columns are proposed unticked with a secondary button "Tick all suggested columns".
- **Phone.** `MobileCriteria` is a one-criterion-at-a-time phone layout with an offline queue and "Accepted on the phone means accepted in the draft on your desktop". The inception routes are not phone routes (a phone token gets `TOKEN_SCOPE_REFUSED`), so the offline queue and the phone-accepts-for-desktop flow are cut. The layout is kept for a narrow desktop window (see Mobile layout). This conflicts with the canvas's "Decided" note that the phone reviews and accepts criteria; the production plan's desktop-only rule (plan §4) overrules it for M4b.

## Entry / exit
- Entry: "Continue to concepts and criteria" on 04; the stepper; "Back to concepts and criteria" from 06 (its `CRITERIA_UNDECIDED` and `CRITERIA_MISSING` cards link here).
- Exit: "Continue to Review and create" goes to 06 after saving; "Back to Shape" goes to 04; "Save draft and exit" goes to 08.
- Gate: Continue is disabled while any generated criterion is undecided, or while either side has no accepted criterion, or there is no concept. These mirror `CRITERIA_UNDECIDED`, `CRITERIA_MISSING` and the `concepts` presence check; the engine decides at 06. The disabled button lists the reasons beside it. A generated criterion is never pre-ticked and never counted as accepted until the researcher clicks Accept.

## Data in
| Field | Source |
| :-- | :-- |
| the draft record | `GET /api/v1/inception/drafts/{id}` ✓ M4a |
| `draft.concepts[{concept, synonyms[]}]`, `extra_inclusions[]`, `extra_exclusions[{criterion, reason_category}]`, `out_of_scope[]`, `criteria_decisions{id: bool}`, `matrix_columns[]`, `verification_checks` | same record |
| every criterion verbatim: `criteria[{id, kind, criterion, reason_category, source, source_label, generated, status}]`, `undecided[]`, `missing_sides[]` | `POST /api/v1/inception/steps/criteria` ✓ M4a (needs `paradigm` and `proof`), called with the in-memory draft after every change |
| suggested concept words `default_concepts[]` | `POST /api/v1/inception/steps/scope` ✓ M4a (needs `topic`) |
| suggested matrix columns `columns[{id, name, description, data_type, required, …}]`, `selected[]` | `POST /api/v1/inception/steps/matrix` ✓ M4a (needs `playbook`) |

`status` is `accepted`, `rejected` or `undecided`. A wizard-written criterion (`generated`) is `undecided` until it has a decision; a typed one is `accepted` unless rejected. The browser never derives `status`, `generated` or `id`; it reads them from the response and writes only `criteria_decisions[id]`.

## Data out
- Save: `PUT /api/v1/inception/drafts/{id}` ✓ M4a; writes `concepts`, `extra_inclusions`, `extra_exclusions`, `out_of_scope`, `criteria_decisions`, `matrix_columns`, `verification_checks`; every other field is carried through. Decisions for ids that no longer match any criterion (after an upstream answer changed) are **kept**, not pruned: the engine ignores them, and they apply again if the text is restored. No journal event.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/inception/drafts/{id}` | ✓ M4a `console/api/inception.py:80` |
| `PUT /api/v1/inception/drafts/{id}` | ✓ M4a `inception.py:88` |
| `POST /api/v1/inception/steps/criteria` | ✓ M4a `inception.py:106`, `steps.py:210` |
| `POST /api/v1/inception/steps/matrix` | ✓ M4a `inception.py:106`, `steps.py:221` |
| `POST /api/v1/inception/steps/scope` (suggested concepts) | ✓ M4a `inception.py:106`, `steps.py:165` |

Desktop only, loopback origin on writes, as 01.

## States
- **Default**: eyebrow "Step 5 of 6 · Concepts and criteria"; h1 "Which concepts and criteria will screen this review?" followed by the live count "3 still need you"; lede "Every criterion is shown word for word with where it came from. Nothing reaches the screening file until you accept it." Main: concepts card, inclusion card, exclusion card. Side: matrix card, verification card. One brand button: "Continue to Review and create" once nothing is undecided; while criteria are undecided it is a secondary button and the brand button is the current criterion's "Accept" (narrow layout, below). Never two at once.
- **Empty**: no concepts yet: the concepts card shows the suggested words from `default_concepts` as draft chips ("Add"), and the field to add one. Criteria with no `proof` or `paradigm`: the criteria cards are replaced by `DRAFT_INCOMPLETE` guidance ("Answer step 4 first", link to 04); not an error state of the engine, no alarm colour.
- **Loading** (skeleton): card skeletons for concepts, both criteria lists and the side cards; the criteria list keeps its previous rows with `aria-busy` while a re-read runs after a change, so rows do not jump.
- **Error** (typed refusal, `StateCard`; texts in 08):
  - `DRAFT_NOT_FOUND`, `DRAFT_ID_INVALID`, `DRAFT_UNREADABLE`: whole-screen card, "Go to your drafts".
  - `DRAFT_CONFLICT`, `DRAFT_EMITTED`: as in 01.
  - `DRAFT_INCOMPLETE` from `steps/criteria` (`missing` lists `paradigm` and/or `proof`), from `steps/matrix` (`playbook`) or from `steps/scope` (`topic`): each affected card shows a one-line sentence with a link to 04 or 01; the others keep working.
  - `DRAFT_INVALID` on save or step: `details.errors` under Details; the field named gets `aria-invalid`.
  - `CRITERIA_UNDECIDED` and `CRITERIA_MISSING` are refusals of `/preview` and genesis (06), not of these steps; here the same facts come from `undecided[]` and `missing_sides[]` and are shown as sentences, not as error cards ("3 criteria still need you", "The protocol needs an accepted exclusion criterion").
  - Guard codes and `ENGINE_UNREACHABLE`: shared cards (08).
- **Partial**: some criteria decided, some not (the common state). The per-side counter reads "3 of 4 accepted · 1 waiting". A side with no accepted criterion shows the sentence from `missing_sides` ("No accepted exclusion yet. The protocol needs at least one.").
- **Offline**: the engine is local; offline means unreachable. Decisions and edits stay in the tab and are marked unsaved; step re-reads stop and the last list stays with "As of {time}"; Continue and Save are disabled with "needs the engine on this computer".
- **Protocol-changed (answers changed upstream)**: a draft has no protocol, but its criteria depend on earlier answers. If 04's proof, 04's lens or the out-of-scope list changed, generated ids change and old decisions no longer match: the rows come back as "Waiting for you" and the card shows "You changed an answer these criteria were written from, so {n} need you again." (shown when the saved decisions contain ids that no criterion has and at least one criterion is undecided). Decisions are not deleted.

## Desktop layout
Source: `Criteria` (D6), split main and side.
- **Main, Concepts card**: a table of Concept, Synonyms and Remove; "Add a concept" field and "Add"; synonyms are comma-separated chips on each row with an inline field; suggested words from `default_concepts` in a draft card above the table ("Suggested from your question · not yet yours", each chip "Add {word}"). No anchor column.
- **Main, Inclusion and Exclusion cards**: one row per criterion, in the engine's order. Row: the criterion text (`body`, verbatim), the source badge (`source_label`), the status badge, for exclusions the reason code in `data` style, the short id in `data` style. Styling by status: **undecided generated** — draft styling (`surface`, dashed `ink-muted` border), badge "Waiting for you" (unclear), buttons Accept and Drop; **accepted** — `surface` with a solid `hairline` border, badge "Accepted" in the include role ("Accepted by you" if it was generated and clicked, "Typed by you" otherwise), buttons Edit (typed only) and Drop; **dropped** — struck-through text, badge "Dropped by you" in the exclude role, "Restore". The canvas tints accepted rows `include-soft` behind `ink` text; that breaks the brand rule that a soft tint never carries ink text, so the tint is kept on the badge only. Below each list: "Add an inclusion criterion" (text field, "Add") and, for exclusions, "Add an exclusion" with a reason-code select (OUT_OF_SCOPE default, LANGUAGE, INSUFFICIENT_DATA; the three the canvas and the CLI wizard name — the compiler remains the guard through `INTENT_INVALID` on 06) and the "Out of scope" chips (`out_of_scope[]`, each a text chip with remove, "Add an out-of-scope topic"); out-of-scope topics become exclusion criteria with code OUT_OF_SCOPE.
- **Side, Extraction matrix card**: "Columns the playbook suggests" with a checkbox per column (name, `description` as help), unticked at first; "Tick all suggested columns" (secondary); caption "Columns are saved in the protocol; the Matrix phase that fills them is parked."; ticking writes the column `name` into `matrix_columns`. None ticked is valid (no matrix columns).
- **Side, Verification card**: a toggle for `verification_checks` ("Retraction status, COI audit, open-science checks"), badge "advisory · Phase 4 is parked", the line "Recorded in protocol.json as advisory. Nothing enforces it while Phase 4 is not in production." (canvas, PROT-01).
- Button row at the end: the counter sentence, Back to Shape, Save draft and exit, Continue to Review and create.
Components: the existing card, badge, table and chips; the criterion row is a composition of them, no new component.

## Mobile layout (≤ 640 px)
Desktop-only on the engine (see 01); this is a narrow desktop window following `MobileCriteria`, stacked in one column. Order: back link and draft id; eyebrow and h1; a progress meter "5 of 7 decided" (`decided / total` from `criteria`, text and bar); the **current undecided criterion** as one card (id, source badge, text, reason code) with the next one previewed beneath it ("Next"); the concepts, the remaining criteria (collapsed lists with counts), the matrix and verification cards as collapsible sections (each header at least 44 px); a sticky bottom action bar. In the bar, while criteria are undecided: "Drop" (secondary) and "Accept" (**the brand button**; Continue is secondary and sits in the page flow); when none are undecided the bar is "Save draft and exit" and "Continue to Review and create" (brand). Edit appears on a typed criterion's card. A toast "{criterion} accepted · saved when you continue" with "Undo" (5 s, `role="status"`; Undo restores the previous local decision). No swipe gestures, no offline queue (cut). A real phone shows the desktop pointer card. All targets are at least 44 px.

## Keyboard
Focus order: skip link, shell, stepper, h1, concepts (suggested chips, table cells, add field), inclusion rows (each row: Accept, Edit or Drop in that order), add-inclusion field, exclusion rows, add-exclusion field and code select, out-of-scope chips, matrix checkboxes, "Tick all suggested columns", verification toggle, Back, Save draft and exit, Continue. After Accept or Drop, focus moves to the next undecided row's Accept (or to Continue when none is left); after Restore it stays on the row; after Edit it moves into the text field and `Escape` cancels, returning to the Edit button; after adding a concept or criterion, focus returns to the add field. Each decision is announced politely ("Accepted: {criterion}"). No single-key shortcuts.

## Copy
Keys in `apps/research-ui/lib/inception-copy.ts`; shared keys are in 01.
- `inception.criteria.title` "Which concepts and criteria will screen this review?"; `titleWaiting` "{n} still need you"; `lede` "Every criterion is shown word for word with where it came from. Nothing reaches the screening file until you accept it."
- Concepts: `concepts.title` "Concepts"; `concepts.count` "{n} concepts"; `concepts.col.{concept,synonyms,remove}` "Concept", "Synonyms", "Remove"; `concepts.add.label` "Add a concept"; `concepts.add.submit` "Add"; `concepts.synonym.label` "Synonyms for {concept}, separated by commas"; `concepts.suggested.title` "Suggested from your question · not yet yours"; `concepts.suggested.add` "Add {word}"; `concepts.none` "No concepts yet. Add at least one."
- Criteria: `incl.title` "Inclusion criteria"; `excl.title` "Exclusion criteria"; `side.counter` "{accepted} of {total} accepted · {waiting} waiting"; `side.counterDropped` "{n} dropped"; `side.missing.inclusion` "No accepted inclusion criterion yet. The protocol needs at least one."; `side.missing.exclusion` "No accepted exclusion criterion yet. The protocol needs at least one."
- Status: `status.undecided` "Waiting for you"; `status.accepted` "Accepted"; `status.acceptedByYou` "Accepted by you"; `status.typed` "Typed by you"; `status.rejected` "Dropped by you".
- Actions: `act.accept` "Accept"; `act.drop` "Drop"; `act.edit` "Edit"; `act.restore` "Restore"; `act.saveEdit` "Save the edit"; `act.cancelEdit` "Cancel"; `act.announceAccepted` "Accepted: {criterion}"; `act.announceDropped` "Dropped: {criterion}"; `act.toast` "{criterion} accepted · saved when you continue"; `act.undo` "Undo".
- Row captions: `row.reason` "Reason code {code}"; `row.id` "id {id}"; `row.changeProof` "Change your proof answer"; `row.defaultNote` "Add an exclusion of your own below; then this default is no longer proposed."; `row.generatedNote` "If you accept it, a record can be excluded or included on this basis at screening."
- Add: `addIncl.label` "Add an inclusion criterion"; `addIncl.help` "Type it exactly as screeners should read it."; `addExcl.label` "Add an exclusion"; `addExcl.code` "Reason code"; `addExcl.code.OUT_OF_SCOPE` "OUT_OF_SCOPE"; `addExcl.code.LANGUAGE` "LANGUAGE"; `addExcl.code.INSUFFICIENT_DATA` "INSUFFICIENT_DATA"; `oos.label` "Out of scope"; `oos.add` "Add an out-of-scope topic"; `oos.remove` "Remove {topic}"; `oos.help` "Each becomes an exclusion criterion with code OUT_OF_SCOPE."
- Upstream: `stale` "You changed an answer these criteria were written from, so {n} need you again."
- Matrix: `matrix.title` "Extraction matrix columns"; `matrix.help` "Columns the playbook suggests"; `matrix.tickAll` "Tick all suggested columns"; `matrix.note` "Columns are saved in the protocol; the Matrix phase that fills them is parked."; `matrix.needPlaybook` "Choose a playbook in step 4 to see the suggested columns."
- Verification: `verify.title` "Verification checks"; `verify.label` "Retraction status, COI audit, open-science checks"; `verify.badge` "advisory · Phase 4 is parked"; `verify.note` "Recorded in protocol.json as advisory. Nothing enforces it while Phase 4 is not in production."
- Progress and gate: `progress` "{decided} of {total} decided"; `gate.undecided` "{n} criteria still need Accept or Drop"; `gate.concepts` "Add at least one concept"; `gate.inclusion` "Accept at least one inclusion criterion"; `gate.exclusion` "Accept at least one exclusion criterion"; `needShape` "Answer step 4 first." ; `back` "Back to Shape"; `continue` "Continue to Review and create".
- Refusals: `inception.refusal.<CODE>.*` (08).

## Accessibility
- Each criterion row is a `li` in a list labelled by its card heading; the text is real text, never an image; the status badge carries words (Waiting for you, Accepted, Dropped by you), so colour is never the only cue. Text on `include-soft` or `unclear` badges is the role's full colour (BRAND_BOOK colour rules); `blocked` is text colour only.
- The row's buttons name their target ("Accept: {criterion}") through visible text plus `aria-describedby` to the criterion text. Strikethrough on dropped rows is paired with the "Dropped by you" badge.
- The progress meter is `role="progressbar"` with `aria-valuenow`, `-min`, `-max` and a text label. Decision changes and the toast use `aria-live="polite"`; refusals `role="alert"`.
- The reason-code select has a visible label; the matrix checkboxes have labels and descriptions; the verification toggle is a labelled checkbox with `aria-describedby` for the advisory note.
- RTL (ar): the layout mirrors; criterion text is `dir="auto"` (criteria are in the review's language); reason codes, ids and column names are `dir="ltr"`; numerals Latin; the progress bar fills from the inline start.
- Contrast pairs from tokens. The criterion text is always `ink` on `surface`; the `-soft` tints appear only behind the role badges, with the role's full colour as the badge text (BRAND_BOOK: a `-soft` tint never carries ink text). The draft/accepted difference is therefore the border (dashed `ink-muted` against solid `hairline`) plus the badge words, not a row fill.

## Acceptance tests
Vitest `apps/research-ui/tests/inception-criteria.test.tsx`:
- every criterion from `steps/criteria` renders verbatim with its `source_label`;
- a `generated` criterion is "Waiting for you", has no pre-ticked state, and counts as accepted only after Accept (which writes `criteria_decisions[id] = true`); Drop writes `false`; Restore removes the key;
- a typed criterion renders accepted without a click; Edit changes its text, so the new id has no decision and the old decision stays in the draft;
- Continue stays disabled while `undecided` is non-empty or `missing_sides` is non-empty or there is no concept, and lists the reasons; the saved PUT carries unrelated draft fields unchanged;
- the stale sentence appears when saved decisions hold unmatched ids and a criterion is undecided;
- matrix columns start unticked, "Tick all suggested columns" writes the engine's `name` values, and no custom column control exists;
- `DRAFT_INCOMPLETE` for `proof` or `playbook` shows a link to 04 on the affected card only;
- `DRAFT_CONFLICT` read-only and reload; `DRAFT_EMITTED` link to Done;
- the narrow layout shows one brand button at a time (Accept while undecided, Continue after) and a 44 px bar; i18n and N9 guard.
Playwright `inception.spec.ts` (this screen's part): decide every generated criterion, add an exclusion, tick matrix columns, Continue to 06; reload mid-way and see the decisions; the count line updates; keyboard-only completion; RTL pass; axe in light and dark; no horizontal overflow at 375 and 1440 px.

## Open questions
None.

## As built (M4b, 2026-11-09)
- The two actions are Accept and Reject (the spec's Drop). A typed criterion can also be removed. Focus does not move to the next waiting row after a decision.
- A typed exclusion always gets the reason code `OUT_OF_SCOPE`; there is no code select.
- When an upstream answer changes, the criteria the wizard wrote from it come back as "Waiting for you" because their ids change; no extra sentence names the cause.
- Concepts are rows of a concept field and a synonyms field; out-of-scope items are edited on Shape.
- The parked labels are shown: the matrix ("Parked: the Matrix phase that fills these columns is not in production.") and the verification checks (advisory, Phase 4 parked). With no column ticked the protocol has no matrix columns, and the help text says so (the engine applies no playbook default).
- A typed exclusion is sent without a reason code, so the engine's default (`OUT_OF_SCOPE`) applies.
- Copy keys and their en, fr and ar texts are the code's: `apps/research-ui/lib/inception-copy.ts` (screen copy) and `apps/research-ui/lib/screening-states.ts` (refusal cards). The Copy section above gives the design intent and the English wording; where a key name or a sentence differs, the code is the record and `tests/inception-copy.test.ts` pins every key in every locale.
