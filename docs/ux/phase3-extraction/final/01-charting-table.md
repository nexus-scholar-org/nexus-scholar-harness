# 01 Charting table    Status: DRAFT | Phase 3 Extraction (first slice of the parked Matrix phase) | Route `/charting` (desktop; read-only list on a phone) | Milestone M12a-charting-table (full-text status, decision, charting, export)

Boards (design history, not redrawn): `Retrieval` (counts and "not retrieved" reasons), `Eligibility` (reason list, counts into the PRISMA box), `Matrix` (study × column grid, "Not reported" as a value), `States` (no full text card), and the README of `docs/ux/phase3-extraction/` (2026-11-02). Contract: none yet; M12a adds its own events file (open question 9). Visual system: `docs/ux/brand/BRAND_BOOK.md`.

**Purpose.** After screening, get the full texts, decide at full text with one reason for each exclusion, and chart one row per study in the two columns the protocol names, saving as you go and exporting a spreadsheet.

**Changed from the canvas.**
- The boards draft cells with an agent and verify them. M12a has no agent, no parsing and no extraction model: every value is typed by the researcher. The "Verified / Edited / Machine draft" cell states are not used; a cell is a value, `Not reported`, `Not applicable` or empty. Nothing here is machine output, so no draft styling.
- Retrieval and eligibility are not separate steps (boards 2 and 3): one table with two views of the same rows. In Part A the app fetches nothing and finds no open-access copy; the researcher attaches a file or pastes a link. Part F (the researcher's answers of 2026-11-21) adds a look-up of open-access copies, by DOI or, without one, by arXiv id, each shown as "Fetched, to confirm" until the researcher confirms it; it comes after Part B (answer F2, "B before F"). Its states are listed in the milestone record, section (d2), and are drafted here before Part F is built (open question 12). Part B's build keeps the keys `L`, `C` and `D` free in this screen for Part F.
- Full-text eligibility has no per-criterion checklist and no quotes: one outcome and one reason, saved like a screening decision event.
- Matrix board's export block ("blocked while any cell is a machine draft") is dropped; export never blocks, it says how many cells are not charted yet.
- The "6 steps" strip of board 1 is not used. The table is one step reached from Publish and Home.

## Entry / exit
- Entry: Home (screening 01) and Export (screening 10), link "Chart the included studies" (`charting.table.link`), shown while screening is published; direct URL (the screen shows its own state); `g c`.
- Exit: the one-study view (02) with Enter; Publish (screening 09) from the not-published state; Export menu downloads. Gate: the table exists only for a published screening (`SCREENING_NOT_PUBLISHED`).

## Data in
| Field | Source |
| :-- | :-- |
| publication status `{status, code, generation_id, outputs}` (CURRENT, STALE, missing) | `GET /api/v1/ui/publication-status` ✓ `workspace.py:576` |
| kept records: `literature/included.json` holds Include and "Unclear → full text" (`screening.decision == "MAYBE"`); each has `study_id` (the row id), title, authors, year, venue, `external_ids.doi`, url, abstract and `screening` {decision, reason, note, screener_id, method}. The current round is `included.json`; each earlier citation-chasing round was moved to `literature/screening_rounds/round_NNN/`. The row list is the current published round plus each archived round; the round label comes from that | read server side by `GET /api/v1/charting` ✗ M12a (new engine code: there is no cross-round reader today; `GET /api/v1/ui/publication/outputs/{name}` ✓ `workspace.py:583` serves one file) |
| charting form `{columns[{column_id, name, definition, type, options[], required}], pilot_on, amendments[]}`. Seeded from `protocol.json` `matrix_dimensions[]` (`id`, `name`, `description`, `data_type`, `required`, `fallback_value`); mapping Text = `free_text`, Number = `numeric`, One of a list = `categorical`, Several of a list = `list`. The protocol holds no options, so options and the Yes/No type (a categorical with two fixed options) live only in the form; the protocol and its fingerprint are never changed. Required columns are shown as required, and the export notes required cells not charted | `GET /api/v1/charting/form` ✗ M12a |
| rows `{study_id, round, kept, new_since, fulltext{status, reason, requested_on, attachment{name, size, sha256}, link}, ft_decision{outcome, reason_code, note}, cells{column_id: {state, value, note, where_from, pilot, chart_again, history[]}}}` and the counts line | `GET /api/v1/charting` ✗ M12a |
| reason codes and short labels (`EXC-n`, `FAILS-INC-n`) | the same `reason_options` field of `GET /api/v1/charting` ✗ M12a, built from the protocol the way screening builds its chips |
| who (workspace screener id, default `researcher:local`) | `GET /api/v1/screening/settings` ✓ `screening_v1.py:436` |

## Data out
Every change is one append-only event, saved at once, no Save button. Payload: `event_id` (UUIDv7, client), `study_id`, `kind` (`fulltext_status`, `fulltext_decision`, `attachment`, `cell`, `form_amendment`, `pilot`), the new value, `screener_id`, `at`, `supersedes` for undo (the `event_id` of the earlier event on the same study and screener, as screening does; there is no undo event type). Per-event result: `accepted`, `duplicate` (silent), `refused` (with its code).
- Status for one or many rows, a full-text decision for one row: `POST /api/v1/charting/events` ✗ M12a, up to 200 events; a bulk status action sends one event per record; a request with `fulltext_decision` events for more than one study is refused (`BODY_INVALID`). Journal: one `CHARTING_EVENTS_RECEIVED` row per request.
- Attach: `POST /api/v1/charting/records/{study_id}/attachment` ✗ M12a (multipart PDF; copied to `pdfs/<study_id>.pdf`; the parked PDF kit and its `DOC-<sha>.pdf` names are not used; the server records name, size and SHA-256) or `{link}` JSON. Journal: `CHARTING_ATTACHMENT_ADDED`. Attaching to a `To get` row also writes a `Retrieved` status event; Z undoes both.
- Form: `PUT /api/v1/charting/form` ✗ M12a before any value exists; after one, `POST /api/v1/charting/form/amendments` ✗ M12a with `{change, from, to, reason, pilot, confirm: true}`. Journal: `CHARTING_FORM_AMENDED`, `CHARTING_PILOT_ENDED`.
- Export: `GET /api/v1/charting/export?format=csv|xlsx` ✗ M12a, read-only bytes; CSV reuses `render_csv` in `screening/export.py` (UTF-8 BOM, CRLF); no xlsx library is a dependency today, so the spreadsheet needs one added (open question 10). Journal: `CHARTING_EXPORTED` (rows, not-charted count, format).
- Undo is a new event that restores the previous value; nothing is deleted.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/ui/publication-status` | ✓ `workspace.py:576` |
| `GET /api/v1/screening/settings` (screener id) | ✓ `screening_v1.py:436` |
| `GET /api/v1/charting` | ✗ M12a |
| `POST /api/v1/charting/events` | ✗ M12a |
| `GET`, `POST /api/v1/charting/records/{study_id}/attachment` | ✗ M12a |
| `GET`, `PUT /api/v1/charting/form` | ✗ M12a |
| `POST /api/v1/charting/form/amendments` | ✗ M12a |
| `GET /api/v1/charting/export?format=csv\|xlsx` | ✗ M12a |

New routes join the host and token guards; the POSTs and the PUT also take the action-origin check (`ACTION_ORIGIN_REFUSED`) and go in both `POST_PATHS`/`PUT_PATHS` lists (`console/browser.py:40-66` and `apps/research-ui/app/api/console/[...path]/route.ts:48`) and are mounted in `console/serve.py`; none is on the phone allowlist.

**Navigation (✗ M12a).** The site header has three items (workspaces, discovery, screening; `components/site-header.tsx:34-38`); add a fourth, "Charting" (`nav.charting`), shown once screening is published. The next-step bar's state after publish, today "Export and methods are on Publish" (`lib/next-step-copy.ts:68`), gets a follow-on: "Next: get the full texts and chart the studies." with the link "Open charting" (`nextStep.charting.title`, `.link`).

**Refusal codes.** Codes for console routes live in `console/refusals.py` and the §7 table of `screening-api-contract.md` (a test keeps them equal); `docs/architecture/refusals.md` is the agent Envelope registry and is not touched. Existing, reused: `SCREENING_NOT_PUBLISHED` (✓ code, `refusals.py:229`, HTTP 409, today raised by the chase routes; the new charting routes raising it are ✗ M12a), `EXPORT_NOT_PUBLISHED` ✓ (not used here), `GENERATION_STALE` (`generations.py:114`), `PROTOCOL_CHANGED_SINCE_PUBLISH` (`refusals.py:238`), `TOKEN_SCOPE_REFUSED`, `HOST_REFUSED`, `TOKEN_REQUIRED`, `ACTION_ORIGIN_REFUSED`, `BODY_INVALID`. `ENGINE_UNREACHABLE` is client-side. New, ✗ M12a (to add to `refusals.py` and the contract table, with the refusals test):
| Code | When |
| :-- | :-- |
| `RECORD_NOT_KEPT` (409) | an event for a study that is not in the published kept set |
| `FULLTEXT_REASON_REQUIRED` (422) | Exclude or Not retrieved without a reason; "Other" without words |
| `FULLTEXT_REASON_INVALID` (422) | a reason code that is not in `reason_options` |
| `CHARTING_VALUE_INVALID` (422) | a value that does not fit the column type or its options |
| `CHARTING_COLUMN_UNKNOWN` (422) | a cell for a column not in the form |
| `CHARTING_AMENDMENT_REASON_REQUIRED` (422) | a form change after a value exists, sent without its one-sentence reason or `confirm` |
| `ATTACHMENT_NOT_PDF` (422) | the file is not a PDF |
| `ATTACHMENT_TOO_LARGE` (413) | over the limit (open question 5) |
| `LINK_INVALID` (422) | a link that is not http or https |
| `CHARTING_EXPORT_FORMAT_INVALID` (422) | a format other than csv or xlsx |
| `CHARTING_PROTOCOL_REPLACED` (409) | the protocol was replaced by a re-inception; the table is archived, read-only |

## States
- **Default**: h1 "Charting". Counts line: "74 kept · 40 retrieved · 3 not retrieved · 31 to get · 22 included at full text · 6 excluded · 12 charted". Toolbar: segmented control Full text / Charting (1, 2), "Show" select, Form, Pilot switch, Export. The table below. One brand button: "Chart the next study" (opens 02 on the first kept row not charted); once every row is charted it becomes "Export".
- **Empty, screening not published**: no table. "Screening is not published yet. The charting table lists the studies you kept, so publish first." Brand button "Go to Publish" (screening 09). Refusal `SCREENING_NOT_PUBLISHED` in Details.
- **Empty, nothing kept**: published with no Include and no Unclear. "Nothing was kept at title and abstract, so there is nothing to chart." Link to Triage.
- **First visit**: form seeded from the protocol, table of rows, one card: "Try the form on about five studies, then revise it." Brand button "Open the charting form"; "Not now" closes it. Pilot is on in the form panel.
- **No charting columns in the protocol**: the Charting view shows "Your protocol has no charting columns yet. Add the first one." Brand button opens the form panel with one empty column. The Full text view works normally.
- **Loading** (skeleton): counts line and 8 rows as skeletons; toolbar disabled; no count before the first answer.
- **Error** (typed refusal, words, code in Details, `role="alert"`): `RECORD_NOT_KEPT` "That study is not in the kept set any more. Reload the table." `FULLTEXT_REASON_REQUIRED` "Choose one reason first." `CHARTING_VALUE_INVALID` "That value is not one of the options." `CHARTING_AMENDMENT_REASON_REQUIRED` "Say in one sentence why the form changes." `ATTACHMENT_NOT_PDF` "Only a PDF can be attached. Paste a link instead." `ATTACHMENT_TOO_LARGE` "That file is too large to keep in the workspace." `GENERATION_STALE` see Stale. A refused change returns the cell or row to its last saved value and keeps the focus on it.
- **Partial**:
  - A row with no full text but charted: mark "No full text", counted as such in the export.
  - A cell `Not reported` ("Not reported", with an icon and words, never colour alone) or `Not applicable`; an empty cell reads "Not charted" in the cell's accessible name, visually a dash.
  - Cells after a form change: "Chart again" mark; the earlier value stays visible as history.
  - A row excluded at full text: hidden by default; "Show excluded" shows it greyed with its reason.
  - Citation-chasing round in progress, not published: a line "A citation-chasing round is being screened. Its studies appear here when it is published." The table shows the database round only.
  - Last export: "Exported 21 Nov 14:32: 68 rows. Changes after this are not in that file." and "{n} cells are not charted yet."
- **Offline** (console not answering): "The console is not answering. Nothing is lost; last change saved at 14:32." Changes already saved stay; new changes are refused locally with that sentence (no hidden queue in this milestone, open question 7). Export disabled.
- **Stale / protocol changed**:
  - Screening published again with changes: banner "Screening was published again on 21 Nov. 3 records were added, 2 are no longer kept." Added rows carry "New since 21 Nov"; a record that left the kept set stays with its values, marked "No longer kept at title and abstract", and is left out of exports. `GENERATION_STALE` (decisions changed, not yet published) shows "Decisions changed after publishing. This table follows the published screening." with a link to Publish.
  - Protocol replaced by a re-inception: "This table belongs to the old protocol. It is kept, read-only, with that protocol." `CHARTING_PROTOCOL_REPLACED`; all controls and Export of the archived table stay available, changes are off. `PROTOCOL_CHANGED_SINCE_PUBLISH` is shown by the existing card when the screening needs publishing again.

## Desktop layout
Compact table, brand-soft only for the one brand button. Regions top to bottom: app bar; h1 and counts line; toolbar; inline banners and the inline confirmation line; the table (`role="grid"`, sticky header and first column, scrolls inside itself); status line. Full text view columns: select, Study (title, year; DOI link when present), Round ("Databases" / "Citation chasing"), Full text (status badge), File (name and size, Open, Attach, or link), Decision (Include / Exclude and reason). Charting view: Study, then one column per charting column (cell value or Not reported / Not applicable / dash). Status roles: Include uses `include`, Exclude `exclude`, To decide and Requested `unclear`, Not retrieved `blocked`; each badge has words and an icon. The form panel (`charting.form.*`) opens beside the table (about 360 px), not a third screen:
- columns seeded from `matrix_dimensions` (name and definition), each with a type (Text, One of a list, Several of a list, Yes/No, Number) and its options; add, remove, reorder;
- the Pilot switch; "End pilot" (one click, recorded);
- Amendment prompt, inline: "Why does the form change? One sentence." with `Record the amendment` (like Prepare's amendment: field, from, to, goes into the journal and the export; earlier values and the protocol are not changed). The list "Amended on 21 Nov by <who>: <change>, from “…” to “…”" sits under the controls.
- The protocol is not edited; the form lives beside it.

## Mobile layout (≤ 640 px)
Read-only list, one card per study: title, round, status badge, charted values; rows are 44 px+ links that open 02 for that study. No bulk actions, no form panel, no attaching, no Export (one line: "Charting is on your desktop."). The Show select stays. Single-study editing is in 02.

## Keyboard
Shortcuts are off in text fields. Grid: arrow keys move between cells; `J`/`K` next and previous row; `Enter` opens the study (02) from a row, or edits a cell when a cell is focused (Enter saves and moves down, `Esc` cancels); `1` Full text view, `2` Charting view; `X` toggles the row's selection, `Shift+J`/`Shift+K` extends it, `A` selects all rows shown. Full text view, on the selection or the focused row: `G` To get, `Q` Requested, `R` Retrieved, `N` Not retrieved (then 1 to 4 chooses the reason, Enter confirms). On the focused row only, never on a selection (a full-text decision is made one study at a time; with several rows selected the status line says "Decide at full text one study at a time."): `I` Include, `E` Exclude (reason chips 1 to n, Enter confirms). `P` attach a file, `O` open file or link, `Z` undo your last change. Charting view: `Alt+N` Not reported, `Alt+A` Not applicable on the focused cell. Several rows: an inline line "Mark 23 records as Retrieved? Enter to confirm · Esc to cancel" (not a modal, `aria-live="polite"`). `F` opens the form panel, `Ctrl+E` Export menu, `?` help, `Esc` closes the panel, the menu, the confirmation line. Focus order: skip link, h1, toolbar, banners, grid, form panel. After a bulk action focus stays on the first changed row.

## Copy
Keys `charting.table.*` (en master, fr/ar fall back, plan §7). Literal `aria-label`, `title`, `alt` and `placeholder` attributes are not used (N9 guard).
- `charting.table.title` "Charting"; `.link` "Chart the included studies"; `.counts` "{kept} kept · {retrieved} retrieved · {notRetrieved} not retrieved · {toGet} to get · {included} included at full text · {excluded} excluded · {charted} charted"
- `charting.table.view.{fulltext,charting}` "Full text", "Charting"; `.show.label` "Show"; `.show.{all,toGet,requested,notRetrieved,toDecide,included,excluded,notCharted,pilot}` "All", "To get", "Requested", "Not retrieved", "To decide at full text", "Included at full text", "Excluded at full text", "Not charted", "Pilot"; `.showExcluded` "Show excluded"
- `charting.round.{databases,chasing}` "Databases", "Citation chasing"
- `charting.status.{toGet,requested,retrieved,notRetrieved}` "To get", "Requested", "Retrieved", "Not retrieved"; `charting.notRetrieved.{noAccess,notFound,noReply,other}` "No access or paywalled", "Not found", "Authors did not reply", "Other, with words"
- `charting.decision.{include,exclude,other}` "Include", "Exclude", "Other, with words"; `charting.decision.choose` "Choose one reason: press its number, then Enter"
- `charting.cell.{notReported,notApplicable,notCharted,noFullText,chartAgain,note,whereFrom,history}` "Not reported", "Not applicable", "Not charted", "No full text", "Chart again", "Note", "Where from (page or quote)", "Earlier value"
- `charting.bulk.confirm` "Mark {n} records as {status}? Enter to confirm · Esc to cancel"; `charting.announce.{saved,undone,bulkSaved}` "Saved", "Undone", "{n} records saved"
- `charting.pilot.{label,suggest,end,ended}` "Pilot", "Try the form on about five studies, then revise it.", "End pilot", "Pilot ended on {date}"
- `charting.form.{title,open,empty,reasonLabel,record,amended}` "Charting form", "Open the charting form", "Your protocol has no charting columns yet. Add the first one.", "Why does the form change? One sentence.", "Record the amendment", "Amended on {date} by {who}: {change}, from “{from}” to “{to}”."
- `charting.empty.{notPublished,nothingKept}` and `.goPublish` "Screening is not published yet. The charting table lists the studies you kept, so publish first.", "Nothing was kept at title and abstract, so there is nothing to chart.", "Go to Publish"
- `charting.next` "Chart the next study"; `charting.new` "New since {date}"; `charting.noLongerKept` "No longer kept at title and abstract"; `charting.chasingPending` "A citation-chasing round is being screened. Its studies appear here when it is published."
- `charting.offline` "The console is not answering. Nothing is lost; last change saved at {time}."; `charting.archived` "This table belongs to the old protocol. It is kept, read-only, with that protocol."; `charting.stale` "Decisions changed after publishing. This table follows the published screening."
- `charting.export.{menu,csv,xlsx,done,cellsOpen}` "Export", "CSV", "Spreadsheet (.xlsx)", "Exported {when}: {n} rows. Changes after this are not in that file.", "{n} cells are not charted yet."
- `charting.refusal.{RECORD_NOT_KEPT,FULLTEXT_REASON_REQUIRED,FULLTEXT_REASON_INVALID,CHARTING_VALUE_INVALID,CHARTING_COLUMN_UNKNOWN,CHARTING_AMENDMENT_REASON_REQUIRED,ATTACHMENT_NOT_PDF,ATTACHMENT_TOO_LARGE,LINK_INVALID,CHARTING_EXPORT_FORMAT_INVALID,CHARTING_PROTOCOL_REPLACED}`; `screening.details.*` for codes (12).
- Export content (fixed English, like screening export): CSV is the table, one row per record not excluded at full text, UTF-8 with BOM, CRLF. Spreadsheet sheets: Charting (a note and a where-from column beside each charting column), Full text (every kept record with status, reason, decision), PRISMA counts (reports sought, not retrieved with reasons, assessed for eligibility, excluded with reasons, included, each split Databases / Citation chasing), Charting form (columns, definitions, types, amendments), About (workspace, protocol fingerprint, corpus snapshot, screening publication date, export time, app version). Rows charted without a full text are labelled "No full text". The "Not charted" cell is empty in the file; "Not reported" and "Not applicable" are written as those words.

## Accessibility
Grid with `role="grid"`, row and column headers, `aria-rowcount`; selection with `aria-selected`; status is words plus an icon, never colour alone (Not reported, Chart again, No full text included). Live region (`aria-live="polite"`) says "Saved", "Undone", "23 records saved"; refusals `role="alert"` with the code in Details. The confirmation line is announced when it appears. Segmented control is a radiogroup. Targets 44 px on touch. Contrast per tokens: `include`, `unclear`, `blocked`, `exclude` as text and icon on their `-soft` fills only. RTL: the table mirrors, first column on the inline start; DOIs, hashes and file names `dir="ltr"`; numerals Latin. The panel is a labelled complementary region; `Esc` returns focus to the Form button.

## Acceptance tests
Vitest `charting.states.test.tsx` (each state renders with its words; every refusal code maps to a key); `charting.keymap.test.tsx` (X, Shift+J/K, A, one key sets status; budget: 23 rows to Retrieved in 4 keypresses); `charting.bulk-confirm.test.tsx` (inline line, Enter confirms, Esc cancels, one event per record); `charting.not-by-colour.test.tsx` (Not reported, Chart again, No full text carry text and icon); `charting.stale-rows.test.tsx` (left-the-kept-set row kept, marked, excluded from export; new rows marked); `charting.mobile-readonly.test.tsx`; `charting.i18n.test.ts` (keys in en; N9 guard). Python `tests/console/test_charting_api.py`: events append only, `duplicate` is silent, undo restores, `RECORD_NOT_KEPT`, reason refusals, amendment needs a reason, attachment copied with size and SHA-256, non-PDF and oversize refused, export CSV with BOM and the five sheets, a re-publish marks rows without deleting, a re-inception archives, the journal rows. Playwright `charting/charting.spec.ts` (publish golden-uav-30, chart 5 studies by keyboard, undo, export both formats, axe in light and dark, 390 px read-only).

## Open questions
1. Route: `/charting` and `/charting/study/{study_id}`, or under `/screening/`? It is Phase 3 and not a screening step, so I used `/charting`.
2. The "Not retrieved" reasons (No access or paywalled; Not found; Authors did not reply; Other with words) and the full-text exclusion reasons (the protocol's `EXC-n` and `FAILS-INC-n`, plus Other with words): is this the list you want? PRISMA 2020 asks for the reasons for exclusion at full text; should "Not retrieved" reasons also be counted under exclusion reasons? I kept them apart.
3. Key choices: `G Q R N` for status, `I E` for the decision, `P` attach, `O` open, `F` form, `Alt+N` and `Alt+A` for the two special cell values. `N` here means Not retrieved but `Alt+N` means Not reported; is that confusing?
4. Rows excluded at full text leave the charting view by default; should they also leave the counts line "charted"? I count only rows not excluded.
5. Largest PDF accepted: proposed 100 MB. Right?
6. Pilot rows: marked, and the "Pilot" filter shows them. Should pilot values be kept as the final values when the pilot ends (my default), or flagged for charting again?
7. Offline: new changes are refused with the saved-at line, not queued as in triage. Is that acceptable for 50 to 150 rows?
8. Narrow screens: a read-only list; no editing except in 02. Is reading the table on a phone useful at all, or should the route show "Charting is on your desktop" like export?
9. *(Answered by the researcher 2026-11-21, M12a question 1: outside the contract for now.)* The events file is a new, non-Contract-v1 record under `<ws>/`. It needs a decision on whether M12a stays outside the contract (a `CONSUMER_GATED` file) or gets a typed model.
10. *(Answered 2026-11-21, M12a question 8: add `openpyxl`.)* A spreadsheet (.xlsx) needs a new dependency (none exists today). Add one, or ship CSV only in M12a?
11. *(Answered 2026-11-21, M12a question 4: only after publication.)* Rows before publication: none (recommended, publishing needs every batch approved), or a read-only preview from current decisions?
12. Part F's fetch states are not drafted yet: the `L` look-up with its inline confirmation (services named, e-mail shown, records by DOI and by arXiv id counted, records with neither counted), the progress line and cancel, the "Fetched, to confirm" status with source, version and licence, `C` confirm and `D` discard with one reason, the "To confirm" filter, the confirmation asked before `I`/`E` on such a row, and the refusals `MAILTO_NOT_SET`, `FETCH_ALREADY_ACTIVE`, `FETCH_NOT_PENDING`, `DISCARD_REASON_REQUIRED`. Draft them here before Part F starts, which is after Part B (answer F2).
