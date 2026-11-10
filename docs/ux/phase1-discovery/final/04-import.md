# 04 Import    Status: FINAL, built (M3c-screens, PR #216) | Phase 1 Discovery | Route `/[locale]/screening/import?return=discovery` (the existing screen; write actions desktop only) | Milestone M3c-screens (an addendum to the built M5b screen, over the M3d-engine items)

**This spec is an addendum.** The screen is built and specified in `docs/ux/phase2-screening/final/11-import-corpus.md` (M5b, with M5c-nbib's PubMed `.nbib`), implemented in `apps/research-ui/components/screening-import.tsx`. Everything in 11 stands (states, layout, the accept dialog, keyboard, accessibility, refusals, decisions of 2026-11-06). This page lists **only what discovery adds**. Where this page and 11 differ, this page wins for the discovery visit.

Boards: `Import` (D2, `docs/ux/phase1-discovery/final/project/Import.dc.html`); no phone board. Contract: `docs/architecture/research_ui/DISCOVERY_API_PACKET.md` §4.4, §6 decision 6. Records: `docs/roadmap/milestones/M3d-engine.md` decisions 7, 8 and 12 (E3). Code: `src/scholar_harness/console/api/screening_v1.py` (`GET /screening/corpus` at `:563`, `POST /screening/corpus/accept` at `:603`), `src/scholar_harness/corpus_accept.py`, `src/scholar_search/importers.py`; the UI type to extend is `Corpus` in `apps/research-ui/lib/screening-v1.ts:333`. Decisions: `docs/decisions.md`, 2026-11-10 "Discovery over HTTP: seven decisions" (6, no CSV) and "A browser harvest does not freeze the corpus; the hand-off screen does". Shared rules: **01-plan.md "Shared by 01–08"**.

**Purpose.** Add the exports of databases the app has no connection to (Scopus, Web of Science, others) as part of the discovery flow: one file per database, with the date, the query and the limits the researcher used there, and see what the importer noted about each file.

**Changed from the canvas.** The canvas's Import board predates screen 11; most of it is already built differently. Every cut, with the board element:
- **CSV is out** (decision 6, packet §4.4). The board's "Drop an RIS or CSV file", `.csv` accept list and "any database that exports RIS or CSV" become "RIS or PubMed .nbib" (the built file field already says `.ris, .nbib or .txt`). No column-mapping step. The screen says "RIS or PubMed .nbib" and nothing about CSV.
- **The three-step single-file form** ("1 The file", "2 Where it came from", "3 Parse preview", gate "Add as a Scopus import" / "Discard this file"). Screen 11's flow stands: add a file (it is staged and parsed by the engine on the add), read the counts and the rejected lines on its row, remove it if wrong ("Remove {file}" is the board's "Discard"). There is no parse preview **before** the add, because the parse is the engine's, run on `POST /screening/corpus/sources`.
- **The database dropdown** (Scopus, Web of Science Core Collection, Other): 11's free-text name with suggestions stands.
- **"Records in file / Parsed / With a DOI / Rejected lines" four counts.** The route sends `records` (the parsed count) only. No "records in file", no "with a DOI", and no count of rejected lines: the rejected lines are listed, and the browser shows no number it counted itself.
- **What the codes mean.** The board says `IMPORT_NO_TITLE` "cannot be screened" and `IMPORT_BAD_YEAR` "kept out until you fix the file". The engine does otherwise (M3d decision 7): a record with no title **is imported**, as "Unknown Title", and reported; a bad year is imported **without a year**, and reported; only a stray line (`IMPORT_BAD_TAG`) is dropped. The copy below says that. The board's sentence "Rejected lines are listed in the report as not imported" becomes "The lines noted here are listed in the search report."
- **"Parsed records get stable record ids ... importing the same file again adds nothing twice"**: replaced by the engine's rule, `SOURCE_DUPLICATE_FILE` (the same file, by hash, is refused). Stable ids are not shown.
- **"The original file is kept unchanged in literature/imports/001/"**: the path is 11's, `literature/raw/ris/` (the built `filesIn` copy). The board's folder does not exist.
- **The board's "Gate · add to the corpus" panel**: not a gate. The accept stays on 11's side card ("What happens when you accept") and its confirmation dialog.
- **The board's eyebrow "Step 4 of 7 · Import an export · optional"** becomes "Step 4 of 7 · Import" when the visit comes from discovery; the screening step bar (Home, Import, 1 Prepare, ...) is replaced by the discovery step bar of 01 on that visit (see below).

## What discovery adds
1. **The discovery step bar and a return link.** When the address carries `?return=discovery` (the discovery step bar's "4 Import" link adds it), the screen shows the discovery step bar of 01 with "4 Import" as the current step (`aria-current="step"`) in place of the screening bar, the eyebrow "Step 4 of 7 · Import", and a link "Back to discovery" to `/[locale]/discovery/` at the top. `?console=` is carried on both. Without the parameter, or with any other value, the screen is exactly 11's (screening bar, "Screening · Import"). The parameter is only a presentation switch; no engine call reads it. Every link on the screen (Continue to Prepare, Back to screening home) keeps its own destination; with `return=discovery` the accepted state adds the link "Go to the hand-off" (`/discovery/handoff`) beside "Continue to Prepare".
2. **`limits`: "Limits you applied there".** A multi-line field inside the closed "Search details" disclosure, below the search string: label "Limits you applied there, if any", help "For example: document type, language, subject area. Stored exactly as you write it and printed in the search report." Sent as `limits` in `POST /screening/corpus/sources` (at most 2,000 characters; the field has `maxlength=2000` and a polite counter-free hint; a blank field sends nothing). The engine stores it verbatim (a blank string becomes `null`). It is shown on the file's row inside "Search details" ("Limits: ..." in monospace, `dir="ltr"`, the full text behind "Show full text", never cut by script), and a database whose files all lack it does **not** get a "not stated" flag: only the date and the search string keep 11's flag (decision 1 there), because the route has no `limits` flag in `databases[]`. A longer value than the engine accepts is a refusal the engine names; an unknown code is shown with its message under Details.
3. **`rejected[]` lines per file.** Each staged `sources[]` row carries `rejected: [{line, code, reason}]`. A row with at least one entry shows a "Lines the importer noted" disclosure (closed by default, `aria-expanded`), a table with columns **Line** (1-based physical line of the stored file), **Code** (selectable text: `IMPORT_NO_TITLE`, `IMPORT_BAD_TAG`, `IMPORT_BAD_YEAR`) and **What happened** (copy keyed by the code; the engine's `reason` follows under Details, `dir="ltr"`). The importer notes lines; the file still counts as added. A row with an empty list says nothing (no "0 rejected"). An unknown code is shown verbatim with the engine's `reason`.
   - `IMPORT_NO_TITLE`: "This record has no title. It was imported as 'Unknown Title' and will be merged with other untitled records by title."
   - `IMPORT_BAD_TAG`: "This line is not part of a record and was dropped. The rest of the file was read."
   - `IMPORT_BAD_YEAR`: "The year is not a four-digit year. The record was imported without a year."
   The "will be merged" half of the first sentence is the engine's stated behaviour (M3d decision 7: every "Unknown Title" record merges by exact title); if that behaviour changes the sentence changes with it.
4. **`staging_refused`: a sentence for a refusal the engine already knows.** `GET /screening/corpus` carries `staging_refused: {code, message} | null`. When it is non-null the add form is **not shown** (removed, not disabled) and a card says why in words, with the code under Details and the engine's `message` under Details:
   - `VERIFIED_EXISTS` (after a harvest wrote this workspace's records): "A search in this workspace already made the records, so a database export cannot be added to them. An export can be added only before the first harvest; combining the two is planned." Next step: a link to the hand-off ("Accept the harvest's corpus") when `state` is `STAGED` and `from_discovery` is true.
   - `CORPUS_ALREADY_ACCEPTED`: 11's frozen state ("The corpus is frozen...") already covers it; the card is not duplicated.
   The browser does not call `POST /screening/corpus/sources` to find this out. A stale tab that does call it and gets `VERIFIED_EXISTS` (409) or `CORPUS_ALREADY_ACCEPTED` (409) shows the same sentence.
5. **The rule, said once on the screen.** A side line on the empty and staged states: "For now a corpus is either a harvest or imported exports, not both. Add exports before the first harvest, or harvest and skip this step." (`discovery.import.rule`, from M3d decision 12; combining is the later milestone M3f-combined-corpus). The opposite order is the Harvest screen's `STAGED_IMPORT_PENDING` (03); the line also says "Staged exports must be accepted or removed before a harvest."
6. **RIS or PubMed `.nbib` only.** As built. The `.nbib` file is chosen by extension, else its first line; a RIS file read as MEDLINE gives `SOURCE_NOT_RIS`, not one rejection per line (M3d decision 7).
7. **After the accept** the report (06) shows each imported database under "imports" (`label`, `searched_on`, `query`, `limits`, `records`, `rejected`), so this screen's `limits` and rejected lines are not lost; a one-line pointer "These appear in the search report" links to `/discovery/report`.

## Entry / exit
- Entry: the discovery step bar ("4 Import", which adds `?return=discovery`); 11's entries stand (Home, the `SNAPSHOT_NOT_ACCEPTED` card, the Workspaces next-step card).
- Exit: 11's exits stand; with `return=discovery` also "Back to discovery" and "Go to the hand-off" (accepted state). The discovery step bar leaves to any step.
- Gate: 11's (Accept disabled until a source is staged and the preview loaded; confirmation dialog). The add form is removed while `staging_refused` is non-null.

## Data in
Everything in 11's table, plus (all from `GET /api/v1/screening/corpus` ✓ M3d-engine, `screening_v1.py:563`):
| Field | Use |
| :-- | :-- |
| `sources[].limits` (string or `null`) | shown in the file's "Search details", verbatim |
| `sources[].rejected[].{line, code, reason}` | the "Lines the importer noted" table (E3) |
| `staging_refused` (`{code: "VERIFIED_EXISTS" \| "CORPUS_ALREADY_ACCEPTED", message}` or `null`) | the sentence that replaces the add form |
| `from_discovery`, `state` (`STAGED` after a harvest waits for the accept) | the pointer to the hand-off |
| `sources[].{id, label, file_name, format, records, searched_on, query, sha256}` and `databases[]`, `preview`, `accepted`, `limits {max_source_bytes, label_max_length}` | as in 11 (the body's `limits` is the **upload** limits, not a source's `limits`; the screen keeps them apart) |
`lib/screening-v1.ts` `Corpus` and its source type gain `limits`, `rejected` and `staging_refused`.

## Data out
- `POST /api/v1/screening/corpus/sources` ✓ (`screening_v1.py`): body `{label, file_name, content_base64, searched_on?, query?, limits?}`; `limits` is new (E3 ✓ M3d-engine). Journal `CORPUS_SOURCE_STAGED` carries `parameters.limits` and `metrics.rejected` (engine side).
- Remove, Accept: unchanged from 11. The UI writes nothing itself.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/screening/corpus` (adds `sources[].limits`, `sources[].rejected`, `staging_refused`) | ✓ M5b; additions ✓ M3d-engine |
| `POST /api/v1/screening/corpus/sources` (adds body `limits`) | ✓ M5b; addition ✓ M3d-engine |
| `POST /api/v1/screening/corpus/sources/{id}/remove`, `POST /api/v1/screening/corpus/accept` (`screening_v1.py:603`) | ✓ M5b |
None is new. No phone route (a phone token gets `TOKEN_SCOPE_REFUSED`).

## States
11's seven states stand (default/staged, empty, loading, uploading, error, partial, offline, protocol-changed, accepted, live-only). Differences on a discovery visit:
- **Default**: as 11, with the discovery step bar, the `limits` field, the rejected-lines disclosure on rows that have entries, and the rule line.
- **Empty (`EMPTY`)**: as 11; the rule line sits under the add form. Not an error; no code.
- **Loading**: as 11; the step bar and the skeleton only.
- **Error** (typed): 11's codes (`SOURCE_LABEL_INVALID`, `SOURCE_DATE_INVALID`, `SOURCE_NOT_RIS`, `SOURCE_TOO_LARGE`, `SOURCE_DUPLICATE_FILE`, `CORPUS_ALREADY_ACCEPTED`, `NOTHING_STAGED`; `PROTOCOL_CHANGED_SINCE_RUN` belongs to the hand-off accept (08), not here) plus `VERIFIED_EXISTS` (409) as above; the code is under Details in every card. `PROTOCOL_MISSING` and `PROTOCOL_INVALID` are not raised by the corpus reads; the accept's `PROTOCOL_INVALID` is 11's.
- **Partial**: 11's, plus: some files have noted lines and some do not; a file with noted lines is still added and counted.
- **Offline**: 11's (last state readable "As of", add/remove/accept disabled).
- **Protocol-changed**: 11's (Accept disabled with the card).
- **`staging_refused` non-null** (new): the add form is absent; the explaining card stands where the form was; staged rows (if any) and counts stay readable.
- **Live-only**: yes (already in `isLiveOnlyPath`).

## Desktop layout
11's layout. Additions: the discovery step bar replaces the screening bar when `return=discovery`; inside the add form's "Search details" disclosure the `limits` field follows the search string; each source row's "Search details" shows `limits`, and a "Lines the importer noted" disclosure follows the row when `rejected` is non-empty; the `staging_refused` card replaces the "Add a database" card; the rule line is a caption in the side card. No new component beyond 01's step bar; the table uses 11's table pattern.

## Mobile layout (≤ 640 px)
As 11: write actions are desktop only; a phone shows the state badge from `GET /summary` and the desktop pointer, with no form and no table (`screening.import.phone.*`). On a narrow desktop window, the step bar wraps (44 px items) and the rejected-lines table scrolls inside its own card. No board exists at any width.

## Keyboard
11's. Added: the step bar comes after the skip link and shell (as in 01); the `limits` field follows the search string inside the disclosure; "Lines the importer noted" is a disclosure button after the row's "Show full search"; after a successful add, focus moves to the new row (11) and, if the row has noted lines, the polite announcement adds "{file} was added; some lines were noted."

## Copy
Keys `discovery.import.*` (en master; fr and ar by the implementer), beside 11's `screening.import.*` (unchanged): `eyebrow` "Step 4 of 7 · Import"; `back` "Back to discovery"; `handoff` "Go to the hand-off"; `limits.label` "Limits you applied there, if any"; `limits.help` "For example: document type, language, subject area. Stored exactly as you write it and printed in the search report."; `limits.row` "Limits"; `limits.showFull` "Show full text"; `rejected.title` "Lines the importer noted"; `rejected.line` "Line"; `rejected.code` "Code"; `rejected.what` "What happened"; `rejected.IMPORT_NO_TITLE`, `rejected.IMPORT_BAD_TAG`, `rejected.IMPORT_BAD_YEAR` (sentences above); `rejected.inReport` "The lines noted here are listed in the search report."; `added.noted` "{file} was added; some lines were noted."; `refused.VERIFIED_EXISTS.title` "Exports cannot be added after a harvest"; `refused.VERIFIED_EXISTS.body` as above; `refused.VERIFIED_EXISTS.affects` "No file can be added to this workspace."; `refused.VERIFIED_EXISTS.action` "Accept the harvest's corpus"; `rule` "For now a corpus is either a harvest or imported exports, not both. Add exports before the first harvest, or harvest and skip this step. Staged exports must be accepted or removed before a harvest."; `format` "RIS or PubMed .nbib"; `inReport` "These appear in the search report."; the existing `screening.import.refusal.*` and `screening.state.<CODE>.*` keys serve the other codes. No literal `aria-label`, `title`, `alt` or `placeholder` (N9 guard).

## Accessibility
11's, plus: the rejected-lines table has a caption ("Lines the importer noted in {file}"), `th scope`, the code as selectable text (role `unclear`, text, not colour alone); the disclosure uses `aria-expanded` and is operable by keyboard; `limits` has a visible label, `aria-describedby` for its help and `dir="ltr"`; the `staging_refused` card uses `role="alert"` with the code under Details; the step bar is the shared ordered list with `aria-current="step"`. RTL (ar): as 11, with line numbers, codes and the `limits` text `dir="ltr"`, the step bar order reversed.

## Acceptance tests
Vitest `apps/research-ui/tests/discovery-import.test.tsx` (new), beside 11's `import.*` tests: with `?return=discovery` the discovery step bar shows "4 Import" as current and a "Back to discovery" link, and without it the screening bar is shown; `?console=` is kept on both; `limits` is sent as typed (verbatim, not trimmed of inner text) and omitted when blank; a source with `rejected` entries shows the disclosure and one row per entry with its code, and a source with none shows no disclosure and no count; unknown codes render verbatim; `staging_refused: {code: "VERIFIED_EXISTS"}` removes the add form and shows the sentence with the code under Details, and no `POST /screening/corpus/sources` is made; `CORPUS_ALREADY_ACCEPTED` shows 11's frozen state; the file field names RIS and `.nbib` and offers no CSV; no browser-computed count is rendered (a mutated `rejected` length changes no number). `discovery-copy.test.ts` (keys; N9 guard). Python (existing, E3): `tests/console/test_discovery_api.py::test_after_a_browser_run_the_corpus_says_why_an_export_cannot_be_staged`, `tests/kits/search/test_import_rejections.py`.
Playwright `discovery.spec.ts` (this screen's part): from the discovery step bar import two RIS files (one with a title-less record and a bad year) as two databases with `limits`, see the noted lines per file, accept, see the hand-off link; after a fake harvest the add form is replaced by the `VERIFIED_EXISTS` sentence; RTL (ar); axe in light and dark.

## Questions closed by the researcher (2026-11-10: each recommended answer taken, "all recommended")
None.

## As built (M3c)
Built in `apps/research-ui/components/screening-import.tsx`. The `limits` field, the per-file limits and the "Lines the importer noted" table show on every visit (they are engine data), the step bar, "Back to discovery", the rule line and "Go to the hand-off" only with `?return=discovery` (read after mount). The `VERIFIED_EXISTS` card copy changed for every visit: since M3d-engine a harvest waits for the hand-off accept, so its next step is "Accept the harvest's corpus" (the hand-off), not Prepare. Not built: the "{file} was added; some lines were noted" announcement.
