# 02 One study    Status: DRAFT (every question for M12a closed by the researcher 2026-11-21; the one open item is question 5, what the highlighter marks here, left to the M8b-triage-highlights amendment; M12a shows the abstract as plain text; a spec is FINAL only when its open questions are empty) | Phase 3 Extraction | Route `/charting/study/{study_id}` (desktop; usable for a single study on a phone) | Milestone M12a-charting-table (one-study charting)

Boards (design history, not redrawn): `Matrix` (the source quote beside a cell), `Eligibility` (the study on the left, the decision on the right), `Retrieval` (full-text row), `States` (no full text). The README of `docs/ux/phase3-extraction/` (2026-11-02). Same events, form and refusals as 01; this page repeats none of them.

**Purpose.** Read one study and chart it, field by field, then move to the next study without leaving the keyboard.

**Changed from the canvas.**
- `Eligibility` drafts each criterion with an agent and quotes; here the researcher decides with one outcome and one reason, no checklist, no draft.
- `Matrix` shows a quote per cell machine-drafted; here "Where from" is free text the researcher types (page or quote).
- The abstract is plain text. The highlighter of M8b-triage-highlights (being built in another milestone) will mark it later; that is a later amendment of this spec, not designed here. Full-text reading is not in the page: the PDF opens in a new tab.
- One screen with two columns, not a wizard; no step bar, like the focus screens of triage.

## Entry / exit
- Entry: `Enter` on a row of 01; the next-study brand button on 01; a link `/charting/study/{study_id}`; a phone list row.
- Exit: `Esc` back to 01 on the same row, same view, same filter; `J`/`K` previous and next study in the table's current "Show" list. Gate: the study must be in the published kept set (`RECORD_NOT_KEPT`); the table's states (not published, archived) apply here too.

## Data in
| Field | Source |
| :-- | :-- |
| study `{title, authors, year, venue, doi, round, ta_decision, ta_reason, note}`, abstract (plain text), full-text block, decision, form columns, cells | `GET /api/v1/charting/records/{study_id}` ✗ M12a |
| neighbours (previous and next study ids in the current "Show" list) | `GET /api/v1/charting?show=` ✗ M12a (the table's list; the page keeps it from 01) |
| publication status | `GET /api/v1/ui/publication-status` ✓ `workspace.py:576` |
| attached PDF | `GET /api/v1/charting/records/{study_id}/attachment` ✗ M12a (served by the local console, opened in a new tab) |

## Data out
Same events as 01 (`POST /api/v1/charting/events` ✗ M12a, one event per change, saved when a field loses focus or on Enter, no Save button; `POST /api/v1/charting/records/{study_id}/attachment` ✗ M12a). Cell payload `{column_id, state: value | not_reported | not_applicable, value, note, where_from}`. Journal rows as in 01 (`CHARTING_EVENTS_RECEIVED`, `CHARTING_ATTACHMENT_ADDED`). Undo is a new event.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/charting/records/{study_id}` | ✗ M12a |
| `GET /api/v1/charting?show=` | ✗ M12a |
| `POST /api/v1/charting/events` | ✗ M12a |
| `GET`, `POST /api/v1/charting/records/{study_id}/attachment` | ✗ M12a |
| `GET /api/v1/ui/publication-status` | ✓ `workspace.py:576` |

Refusals as 01 (`RECORD_NOT_KEPT`, `FULLTEXT_REASON_REQUIRED`, `FULLTEXT_REASON_INVALID`, `CHARTING_VALUE_INVALID`, `CHARTING_COLUMN_UNKNOWN`, `ATTACHMENT_NOT_PDF`, `ATTACHMENT_TOO_LARGE`, `LINK_INVALID`, `CHARTING_PROTOCOL_REPLACED`, all ✗ M12a; `SCREENING_NOT_PUBLISHED` ✓ `refusals.py:229`).

## States
- **Default**: top bar: "Nexus Scholar" link, h1 = study title, position "Study 12 of 74", Leave ("Back to the table", Esc). Left column, the study: title, authors, year, venue, DOI link, round, "Title and abstract: Include" or "Unclear → full text" with the reason or note, then the full-text block (status select; File: name, size, Open, Attach; or a pasted link; the full-text decision Include / Exclude with its reason chips), then the abstract. Right column, the charting form for this study: one field per column, each with its definition under the name, `Not reported` and `Not applicable` buttons, Note, Where from. One brand button: "Next study" (J); on the last study "Back to the table".
- **Empty**: no charting columns in the protocol: the right column says "Your protocol has no charting columns yet." with the brand button "Add the first column" (opens the form panel on 01). A study with no abstract: "This record has no abstract."
- **Loading** (skeleton): title, two blocks and the field rows as skeletons; the J/K keys wait.
- **Error**: refusals of 01. A refused field returns to its last saved value with the card beside it; `RECORD_NOT_KEPT` "That study is not in the kept set any more. Back to the table." `ATTACHMENT_NOT_PDF` and `LINK_INVALID` appear under the File line.
- **Partial**:
  - No full text: the block says "No full text" with the mark that stays on the row; charting is allowed, the form shows the mark on top, "Charting from the abstract. This row is counted as having no full text."
  - Not reported: the field shows the word and an icon; the value input is disabled until it is cleared. Not applicable likewise.
  - Chart again after a form amendment: the field carries "Chart again" and the earlier value under "Earlier value" (read-only history).
  - Pilot on: a quiet "Pilot" mark beside the position; saved values are marked Pilot.
  - Excluded at full text: the form is read-only with "Excluded at full text: <reason>. Change the decision to chart it." and the decision control focused.
  - No longer kept at title and abstract: read-only, "No longer kept at title and abstract. Its values are kept and left out of exports."
  - Fetched, to confirm (Part F, built to `03-fetch-states.md`, section "One-study view (02)"): the full-text block shows the waiting file (badge, source, version, licence, size, identity result, warning), Open, Confirm and Discard with the reason chips inline, then "What was tried"; the status select is disabled with "A fetched file is waiting"; Attach and the link are hidden while it waits; the form keeps "Charting from the abstract" until the file is confirmed. `L` looks up this one record with the same plan block ("of 1 record"); `C`, `D`, `O`, `Z` and the question before `I`/`E` work as in the table.
- **Offline**: "The console is not answering. Nothing is lost; last change saved at 14:32." Fields stay readable; changes are refused locally.
- **Stale / protocol changed**: screening published again: "New since 21 Nov" on the study. Protocol replaced by a re-inception: the whole page is read-only with "This study's table belongs to the old protocol." (`CHARTING_PROTOCOL_REPLACED`); the PDF still opens.

## Desktop layout
Focus screen at ≥ 1024 px: no page scroll, a 48 px bar, two columns that scroll inside themselves (study about 55%, form about 45%), a status line at the bottom with "Saved" and the Z hint. Column widths like triage's record pane and right column. Status roles for the title-and-abstract decision and the full-text decision: `include`, `unclear`, `exclude`; all with words and an icon. Machine output: none. Below 1024 px the columns stack, study first.

## Mobile layout (≤ 640 px)
One study, stacked: study, full-text block, abstract, then the form. Fields are 44 px+, the two special-value buttons 44 px, Previous and Next at the bottom (study order of 01). Attach opens the phone's file picker; Open opens the PDF or link in a new tab. Bulk actions and the form panel do not exist here. Study-to-study moves stay, because a researcher can chart on a tablet; the list itself is read-only (01).

## Keyboard
Shortcuts are off in text fields. `J`/`K` or `Ctrl+↓`/`Ctrl+↑` next and previous study (the Ctrl keys also work inside a field and save it first); `Esc` back to the table on the same row; `Tab` moves through fields in column order; `Alt+N` Not reported and `Alt+A` Not applicable on the focused field; `Enter` in a single-line field saves and moves to the next field; `Shift+Enter` in Note adds a line; `I`, `E` full-text decision (reason chips 1 to n, Enter confirms), `G Q R N` status as in 01, `P` attach, `O` open, `Z` undo your last change. Focus order: bar, study, full-text block, abstract, form fields, Next. After J or K focus lands on the first field of the next study, and the live region says "Study 13 of 74. Saved."

## Copy
Keys `charting.study.*`; everything shared with 01 uses `charting.*`.
- `charting.study.position` "Study {k} of {total}"; `.back` "Back to the table"; `.next` "Next study"; `.previous` "Previous study"
- `charting.study.taDecision` "Title and abstract: {outcome}"; `.round` "Found by: {round}"; `.abstract` "Abstract"; `.noAbstract` "This record has no abstract."; `.doi` "Open the DOI link"
- `charting.study.file.{label,open,attach,link,none,size}` "Full text", "Open", "Attach a PDF", "Paste a link", "No full text", "{size}"
- `charting.study.fromAbstract` "Charting from the abstract. This row is counted as having no full text."
- `charting.study.excluded` "Excluded at full text: {reason}. Change the decision to chart it."; `.noLongerKept` "No longer kept at title and abstract. Its values are kept and left out of exports."; `.archived` "This study's table belongs to the old protocol."
- `charting.study.noColumns` "Your protocol has no charting columns yet."; `.addColumn` "Add the first column"
- `charting.study.announce.moved` "Study {k} of {total}. Saved."
- Field labels come from the protocol's column names; definitions from the column description; type hints `charting.type.{text,one,several,yesNo,number}` "Text", "One of a list", "Several of a list", "Yes or No", "Number"; `charting.cell.*` as 01.
- Tips sit behind an icon button (M10d), for example `charting.study.tip.whereFrom` "A page or a short quote, so you can find it again." and `charting.study.tip.notReported` "Use this when the study does not say. It is a finding, not a blank."

## Accessibility
Two labelled regions ("Study", "Charting form"), each scrollable with `tabindex="0"`. Every field has a visible label and its definition as description (`aria-describedby`). Not reported and Not applicable are toggle buttons with `aria-pressed`, words and an icon. "Saved" and the study position are `aria-live="polite"`; refusals `role="alert"` with the code in Details. The PDF link says it opens a new tab. Contrast pairs per tokens; status colours only as text and icon on `-soft`. RTL: columns mirror, DOI and file names `dir="ltr"`, numerals Latin. Targets 44 px on touch.

## Acceptance tests
Vitest `charting-study.keymap.test.tsx` (J/K and Ctrl+arrows save and move; Esc returns to the same row; Alt+N and Alt+A set the two special values); `charting-study.readonly.test.tsx` (excluded at full text, no longer kept and archived are read-only with their words); `charting-study.no-fulltext.test.tsx` (mark and count wording); `charting-study.history.test.tsx` (Chart again keeps the earlier value visible); `charting-study.mobile.test.tsx` (stacked, 44 px targets, no bulk actions); `charting-study.i18n.test.ts` (keys, N9). Playwright `charting/study.spec.ts` (chart 5 studies from the abstract by keyboard, attach a PDF and Open it in a new tab, undo, no page scroll at 1440x900 and 1280x720, axe in light and dark).

## Open questions
5. The abstract is plain text now. When the highlighter arrives, should it mark the title and abstract only, or also open the full text here? Left to the amendment of M8b-triage-highlights.

## Questions closed (M12a, 2026-11-21)
The researcher closed the questions below in the main session on 2026-11-21, all together and each as this spec proposed ("Close as proposed"). The wording and the layout stay open to change when the researcher sees the built screens, as for M11a.
1. Route: `/charting/study/{study_id}` (a path, so Back works) or a panel of 01 on the same URL? I chose its own page because Enter, J and K behave like triage. *(Closed 2026-11-21 as proposed.)*
2. `Ctrl+↓`/`Ctrl+↑` can clash with some screen readers; is `J`/`K` alone enough, with the Ctrl keys only inside fields? *(Closed 2026-11-21 as proposed: `J`/`K` and `Ctrl+↓`/`Ctrl+↑` both kept, the Ctrl keys also inside a field.)*
3. In the one-study view the full-text decision sits on the left under the file. Should it come after the abstract instead, since you read the abstract first? *(Closed 2026-11-21 as proposed.)*
4. When a study is excluded at full text and the form turns read-only, should its already typed values stay visible (my choice, read-only) or fold away? *(Closed 2026-11-21 as proposed.)*
6. On a phone, should Attach (the file picker) exist, or is attaching desktop only like the form panel? *(Closed 2026-11-21 as proposed.)*
