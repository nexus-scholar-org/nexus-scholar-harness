# 11 Import the corpus    Status: FINAL, built (M5b) | Phase 2 Screening (before Prepare) | Route `/screening/import` (write actions desktop only) | Milestone M5b (corpus import; engine and UI)

Boards: none. The canvas has no import board; `Prepare` (D2, snapshot-missing state) only offers "Accept the Discovery corpus as a snapshot". This screen reuses the `Prepare` binding table, the `Publish` PRISMA card, the table, badge, EmptyState and state-card patterns and introduces no component. Contract: `docs/architecture/screening-api-contract.md` §4 (`POST /corpus/accept`), §7. PRISMA 2020 wording: the identification box ("Records identified from: Databases (n = …)"; "Records removed before screening: Duplicate records removed (n = …)"). Existing command being replaced as the only way in: `nexus-scholar accept-corpus --ris <one file>` (`src/scholar_harness/cli.py:1219`, `src/scholar_harness/corpus_accept.py:143`).

**Purpose.** Bring the database exports of a real review into the workspace without a terminal: one RIS file per database, each labelled, checked with counts before anything is frozen, then accepted as the corpus that screening starts from.

**Changed from the canvas.**
- **New screen, no board.** 02 shows a snapshot-missing state whose only action is a terminal command (`SNAPSHOT_NOT_ACCEPTED`, `apps/research-ui/lib/screening-states.ts:34`). This spec gives that card an in-app action. 02's button "Accept the Discovery corpus as a snapshot" (source `verified`) stays for workspaces that have a Discovery corpus (M3); this screen is the `import` source of `POST /corpus/accept`.
- **Several files, one per database.** Today `accept-corpus --ris` takes one file and refuses to replace an existing `verified.json` (`corpus_accept.py:117`). Here each file has a required, unique database label, an optional date searched and an optional search string, all kept with the records.
- **Duplicates are counted, not hidden.** The existing deduplicator (DOI first, then near-identical title + first author + year ±1) runs when the corpus snapshot is built, across and within files. The screen shows the numbers it needs for the PRISMA box: per database records, total identified, duplicates removed, unique studies to screen.
- **One-way.** After acceptance the screen is a read-only record of what was imported. Replacing an accepted corpus is not offered, because it would invalidate screening decisions; the screen says so and gives the reason.
- **Machine output as a draft.** The preview counts are computed by the engine from the files. They are shown with the draft styling and a "Preview · not frozen" badge until acceptance (BRAND_BOOK principle 5), and become plain facts after it.
- **Live-only.** No Demonstration marker; `/screening/import` is added to `isLiveOnlyPath` (`apps/research-ui/components/app-shell.tsx`) with a test, as in 00, 09 and 10.
- **Formats.** RIS only in this milestone (open question 3). The error for any other file is `SOURCE_NOT_RIS`. Since M5c-nbib (2026-11-08): PubMed MEDLINE `.nbib` is read too; the format is chosen per file by its extension, else by its first line, and the file picker accepts `.ris`, `.nbib` and `.txt`. The refusal code name is unchanged.

## Entry / exit
- Entry: Home (01) when no corpus is accepted, in place of the terminal hint ("Import your search results"); the action on the `SNAPSHOT_NOT_ACCEPTED` refusal card (08, 02): the card's action changes from the copyable terminal command to a link "Import the corpus" (the command stays as a secondary line for people who prefer the terminal); the steps bar if open question 4 is answered yes; the next-step card after a workspace is created (00); a direct URL. When the corpus is already accepted, Home and 02 link to this screen as "What was imported" (read-only).
- Exit: "Accept and freeze the corpus" success stays on this screen, switches to the accepted state, and shows the button "Continue to Prepare" (02). Back to 01 at any time; nothing staged is lost by leaving (staged files are on disk in the workspace).
- Gate: Accept is disabled until at least one source is staged and the preview has loaded (`NOTHING_STAGED` otherwise). A confirmation dialog explains the freeze. After acceptance every write control is removed, not disabled (`CORPUS_ALREADY_ACCEPTED` covers a stale tab).

## Data in
| Field | Source |
| :-- | :-- |
| `state` (`EMPTY` \| `STAGED` \| `ACCEPTED`) | `GET /api/v1/screening/corpus` ✓ M5b |
| staged sources `[{label, slug, file_name, records, searched_on, query}]` | `GET /api/v1/screening/corpus` ✓ M5b |
| preview counts `{identified, duplicates, unique_studies}` (dry run with the snapshot's deduplicator, nothing written) | `GET /api/v1/screening/corpus` ✓ M5b |
| accepted snapshot `{artifact_id, accepted_at, records, studies, duplicates}`; `sources` stay listed | `GET /api/v1/screening/corpus` ✓ M5b |
| `from_discovery` (the corpus came from discovery, not from database exports) and `limits {max_source_bytes, label_max_length}` | `GET /api/v1/screening/corpus` ✓ M5b |
| protocol and snapshot state for the Prepare link | `GET /summary` ✓ M1a (contract §4) |
| current workspace name | `GET /api/v1/workspace/meta` ✓ `src/scholar_harness/console/api/workspace.py:107` |

`unique_contributed` (how many studies exist only because of that database) is optional in the response; the screen shows the column only if the engine sends it (open question 6). The screen never computes a count in the browser.

## Data out
- Add a database: `POST /api/v1/screening/corpus/sources` ✓ M5b (`console/api/screening_v1.py`). JSON `{label, file_name, content_base64, searched_on?, query?}`; `content_base64` is the file's bytes (not decoded as text, so a BOM or a legacy encoding is kept and the sha256 is of the researcher's file); at most 50 MB per file (`limits.max_source_bytes` in `GET /corpus`). The engine parses it with the RIS importer, refuses a file with no records (`SOURCE_NOT_RIS`), copies it byte for byte to `literature/raw/ris/<slug>.ris` and returns 201 with the updated corpus state and preview. Because files travel as JSON text, a very large file is read in memory; the 50 MB limit is shown before upload.
- Remove a staged database: `POST /api/v1/screening/corpus/sources/{id}/remove` ✓ M5b (POST, because the browser allowlists serve no DELETE; `slug` comes from `GET /corpus`). Only before acceptance (`CORPUS_ALREADY_ACCEPTED` after). Returns the updated state. The engine deletes the copied file and the journal keeps its sha256 and record count (open question 7).
- Accept: `POST /api/v1/screening/corpus/accept` ✓ M5b (replaces the planned M0 row). No body. Writes `verified.json` (one row per record, with `source_database`) and `literature/raw/provenance_manifest.json`, builds the Contract-v1 corpus snapshot (its deduplicator groups the records into studies), publishes it through the acceptance gate, and returns the `GET /corpus` body with `state: "ACCEPTED"` and `accepted:{artifact_id, accepted_at, records, studies, duplicates}`.
- The UI never writes the workspace or the journal itself. Journal rows below are written by the engine.

## Journal (engine side, ✓ M5b)
| Event | When | Carries |
| :-- | :-- | :-- |
| `CORPUS_SOURCE_STAGED` | a file is added | label, file name, stored path, `searched_on`, `query`; metrics: records parsed, sha256 |
| `CORPUS_SOURCE_REMOVED` | a staged file is removed | label; metrics: records, sha256 |
| `CORPUS_IMPORTED` | accept, before the gate | inputs (the stored files), outputs (`verified.json`, the manifest), the source labels; metrics: records, records per source |
| the acceptance gate's own event | accept succeeds | the snapshot artifact, as for every accepted artifact |
| none | a refused call, a preview read | refusals write nothing |

The terminal path is the same engine: `nexus-scholar accept-corpus --ris Scopus=a.ris --ris "Web of Science=b.ris"` stages each file and accepts, so the terminal and this screen produce the same corpus from the same files.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/screening/corpus` | ✓ M5b |
| `POST /api/v1/screening/corpus/sources` | ✓ M5b |
| `POST /api/v1/screening/corpus/sources/{id}/remove` | ✓ M5b |
| `POST /api/v1/screening/corpus/accept` | ✓ M5b |
| `GET /api/v1/screening/summary` | ✓ M1a |
| `GET /api/v1/workspace/meta` | ✓ `workspace.py:107` |
| CLI `nexus-scholar accept-corpus --ris LABEL=PATH` (repeatable) | ✓ `cli.py` `accept-corpus`, `corpus_accept.py` |

None of the corpus routes is added to `_PHONE_ROUTES` (`src/scholar_harness/console/serve.py:50`); a phone token gets `TOKEN_SCOPE_REFUSED`. The three writes sit under the loopback origin check like the screening actions (`ACTION_ORIGIN_REFUSED`, `screening.py:1319`), plus `HOST_REFUSED` and `TOKEN_REQUIRED`. `GET /corpus` is a read with no origin check.

## States
- **Default (staged)**: Literata h1 "Import your search results". Lede "Add one file for each database you searched. Nothing is final until you accept." Stepper line "1 Add databases · 2 Check the counts · 3 Accept". Main: the "Add a database" card (collapsed to a button once at least one source is staged), the "Databases added" table, the "Counts for your PRISMA flow diagram" card. Side: "What happens next" (the freeze, copy of files to `literature/raw/ris/`, journal). One brand button on screen: "Accept and freeze the corpus" (after step 3 is reachable); "Add a database" is secondary until nothing is staged, when it becomes the brand button.
- **Empty (`EMPTY`)**: EmptyState "No databases added yet" with the add form open and the brand button "Add a database". Caption "Export your results from each database as an RIS file (.ris or .txt), then add them here." (Since M5c-nbib a PubMed `.nbib` file is accepted too; the file field and its help say so.) Accept is absent. Not an error; no code is shown.
- **Loading** (skeleton): table with three rows, counts card as skeleton; no count is shown until the server answers. **Uploading**: the row for the file appears at once with a progress state "Reading {file_name}" and a text status (not colour alone); the form is disabled; Accept is disabled; on success the row becomes a normal row and the counts refresh; no optimistic count. **Accepting**: button "Freezing the corpus", disabled; dialog closed; progress text in `aria-live`.
- **Error** (typed refusal, each as a state card with code, what it affects, one next step; codes shown as in `stateCopy`):
  - `SOURCE_LABEL_TAKEN` ✓ M5b (409): "A database called {label} is already added. Use another name, or remove the first one." Affects: this file only. Field error under the label, focus returns to it.
  - `SOURCE_NOT_RIS` ✓ M5b (422): "No records were found in {file_name}. Check that it is an RIS export from your database." Affects: this file only; nothing was added. Shows how many lines were read when the engine sends it. This is the parse-failure state; there is no partial parse, a file either yields records or is refused.
  - `SOURCE_TOO_LARGE` ✓ M5b (413): "{file_name} is larger than 50 MB. Export the results in smaller parts and add each part as its own database entry (for example Scopus 1, Scopus 2)." Checked in the browser first from `File.size` so the file is not read; the server refusal covers any other client.
  - `CORPUS_ALREADY_ACCEPTED` ✓ M5b (409): "The corpus is already frozen. You can no longer add or remove databases, because screening decisions depend on it." Next step: "See what was imported" (reload into the accepted state).
  - `NOTHING_STAGED` ✓ M5b (409): "Add at least one database before you accept." Normally prevented by the disabled button; this covers a stale tab.
  - `INVALID_OUTPUT` (✓ in the console set, `refusals.md`; used for a missing label or a `searched_on` that is not an ISO date): field error naming the field.
  - Acceptance gate failure (baseline drift or acceptance gate refusal, as `AcceptCorpusRefused` today, `corpus_accept.py:211`): shown with its engine code and message; nothing is published, the staged files stay.
  - `STALE_BINDING` (✓ `integrity.py:28`) if the protocol changed while staged: "The protocol changed. Rebind before you accept." link to 02/08.
  - `ACTION_ORIGIN_REFUSED`, `HOST_REFUSED`, `TOKEN_REQUIRED`, `TOKEN_SCOPE_REFUSED` (phone) → the shared guard cards (08); `ENGINE_UNREACHABLE` (client-side) → Engine-unreachable card.
- **Partial**: some files staged, others refused in the same session. Each refusal card is tied to the file that caused it and stays until dismissed; staged rows are unaffected. A staged file whose raw copy is missing from `literature/raw/ris/` when the workspace is read gets the row note "File missing from the workspace" (blocked text, not fill) and Accept is disabled until it is removed or re-added (engine reports `missing[]`).
- **Offline**: the engine is local, so offline means "engine unreachable". The last state stays readable with an "as of" caption; add, remove and accept are disabled. A file chosen before the loss is not queued (nothing is held in the tab; the form says "needs the engine on this computer").
- **Protocol-changed**: the preview does not depend on the protocol, but accepting does (the snapshot is bound to the protocol fingerprint). If it changed, the Protocol-changed card (08) shows and Accept is disabled; staging still works. After acceptance a later protocol change is shown on 02/08, not here.
- **Accepted (`ACCEPTED`)**: read-only. Badge "Corpus frozen" (include role) with the date and the snapshot fingerprint (LTR, short form with copy). The same table (no remove buttons), the same PRISMA counts card now stated as facts, and the line "This corpus is frozen. To change it you would have to start screening again, so the app does not offer it." Button "Continue to Prepare" (02) or, if batches exist, "Back to screening home". The add form, the remove buttons and the Accept button are absent. Raw files: "Copies of your files are in {path}" (LTR path).
- **Live-only**: yes; no Demonstration marker.

## Desktop layout
Split like `Prepare` (D2): main (about 2/3) and side.
- App bar (brand, workspace name link, locale switch); h1, lede, stepper line.
- **Add a database card** (raw-card style): a file picker (button "Choose an RIS file", drop zone with the same button; accepts `.ris`, `.txt`); **Database name** (required, text input with a datalist of suggestions Scopus, Web of Science, IEEE Xplore, PubMed, ACM Digital Library, Other; "Other" clears the field and asks the researcher to type the name; a chosen suggestion fills it; the name stays editable); **Date searched** (optional, native date input, ISO `YYYY-MM-DD`, help "The day you ran the search. PRISMA asks for it."); **Search string** (optional, multi-line text, `dir="ltr"`, monospace, help "Paste the exact search you ran in this database."); buttons "Add this database" (brand when nothing is staged, otherwise secondary) and "Cancel". The suggestion list is a hint, never a restriction; the label is free text, trimmed, 1 to 80 characters, unique case-insensitively (the server decides: `SOURCE_LABEL_TAKEN`).
- **Databases added** table: columns Database, File, Records, Date searched, Search string (first line, expandable "Show full search"), and Remove (before acceptance). Footer row "Total records identified". Row status text: "Added", "Reading…", "File missing" (role badge plus text).
- **Counts for your PRISMA flow diagram** card, badge "Preview · not frozen" (draft styling: dashed border on `brand-soft`) until accepted, then "Counted when frozen". Content is a table plus one sentence, in this order:
  - rows "Records identified from {database} (n = {records_parsed})" per source;
  - "Records identified, total (n = {records_identified})";
  - "Duplicate records removed (n = {duplicates_found})";
  - "Unique studies to screen (n = {unique_studies})".
  The sentence reads "Records identified from: Scopus (n = 1,204); Web of Science (n = 987); duplicate records removed (n = 611). Studies to screen: 1,580." It is the wording of the PRISMA 2020 identification box, so the researcher can copy it. The sentence is machine-written; it carries the draft treatment until acceptance. After acceptance these numbers are exactly the ones 09 shows under "identified" and "duplicates removed" (the PRISMA preview reads the accepted snapshot).
  A caption below explains duplicates in plain words: "A duplicate is the same article found in more than one database, or twice in the same file. The app matches them by DOI, then by near-identical title, first author and year (one year either way)." No count of "possible" duplicates is shown or offered for manual review here (open question 5).
- **Side card "What happens when you accept"**: three lines (the corpus is frozen as the starting point of screening; no database can be added, removed or replaced afterwards; copies of your files stay in `literature/raw/ris/` and every step is recorded in the audit journal) plus the brand button "Accept and freeze the corpus".
- **Accept confirmation dialog** (modal, focus trapped): title "Freeze this corpus?"; body "You are about to freeze {unique_studies} studies from {n} databases. After this you cannot add, remove or replace a database, because that would invalidate screening decisions. Check the counts first."; shows the per-database list and the three totals; actions "Freeze the corpus" (brand, not focused first) and "Go back" (focused first; `Esc` = Go back).
- Footer caption "This computer · engine running · {workspace path}" (LTR).

## Mobile layout (≤ 640 px)
Write actions are desktop-only (plan §4; the corpus routes are not on the phone allowlist). The phone shows a read-only status and a pointer, like the other write screens:
- State badge ("No corpus yet" in unclear role, "Databases added, not frozen" in unclear, or "Corpus frozen" in include role) from `GET /summary` (the one phone-allowed read); if `/corpus` itself is refused for the phone scope, the state comes from `/summary` alone and the table is not shown.
- One card "Importing is done on your desktop. Open this screen there to add your database files." with a 44 px "Go to screening" link (`/screening`). When frozen: the per-database counts card in read-only form if the phone scope allows `GET /corpus` (open question 9; the safe default is the badge and pointer only).
- No file picker, no form, no accept. The engine refuses any attempt with `TOKEN_SCOPE_REFUSED`.

## Keyboard
Tab order: skip link, app bar, steps bar, h1, file picker button, database name, date searched, search string, Add this database, Cancel, table rows (Show full search, Remove per row), counts card, Accept. `Enter` in the name field submits when a file is chosen; `Enter` on Accept opens the confirmation dialog; `Esc` closes the dialog and returns focus to Accept; the dialog's first focus is "Go back". `a` opens the add form from the page body (not while typing in a field). After a successful add, focus moves to the new row's file cell and "Added {label}" is announced politely; after a remove, to the next row or to the "Add a database" button; after a refusal, to the field it names or to the refusal card heading. After acceptance, focus moves to the "Corpus frozen" badge heading. The drop zone is also operable from the keyboard through the file picker button (no drag-only action).

## Copy
Keys, en master (fr and ar fall back to en where not yet translated, plan §7; locales en/fr/ar with RTL). Plain words, no jargon: the screen says "database", "file", "search results", "duplicate", "freeze", never "snapshot" or "ingest" in headings (the fingerprint is labelled "Corpus fingerprint").
`screening.import.title` ("Import your search results"), `screening.import.lede`, `screening.import.steps.{add,check,accept}`, `screening.import.add.{cta,title,file,fileHelp,drop,label,labelHelp,suggestions.{scopus,wos,ieee,pubmed,acm,other},searchedOn,searchedOnHelp,query,queryHelp,submit,cancel,uploading,reading}`, `screening.import.table.{database,file,records,searchedOn,query,showQuery,remove,total}`, `screening.import.row.{added,reading,fileMissing}`, `screening.import.counts.{title,draftBadge,frozenBadge,fromSource,identified,duplicates,unique,sentence,duplicatesHelp}`, `screening.import.accept.{cta,title,body,confirm,back,freezing}`, `screening.import.side.{title,freeze,files,journal}`, `screening.import.empty.{title,body}`, `screening.import.frozen.{badge,body,filesIn,continue}`, `screening.import.phone.{desktopOnly,state.empty,state.staged,state.frozen}`, `screening.import.entry.{home,refusalCard,viewOnly}`, `screening.import.liveStamp`, `screening.import.offline`; `screening.import.refusal.{SOURCE_LABEL_TAKEN,SOURCE_NOT_RIS,SOURCE_TOO_LARGE,CORPUS_ALREADY_ACCEPTED,NOTHING_STAGED}` (each with `.title`, `.body`, `.affects`, `.action`). The shared codes use `screening.state.<CODE>.*` from 08. Add `SNAPSHOT_NOT_ACCEPTED` action key `screening.state.SNAPSHOT_NOT_ACCEPTED.actionImport` ("Import the corpus") beside the existing terminal command (`screening-states.ts:34`; its `action` changes from `terminal` to a link action; the command stays as a secondary line). Input hints, button names, close, copy and dialog names are keys too: no literal `aria-label`, `title`, `alt` or `placeholder` attributes (N9 guard).

**Translation boundary.** Chrome, labels, help, refusals and counts wording are translated in en/fr/ar. The PRISMA sentence is built from a key with named slots so the number placement can differ by language; digits are Latin. User-entered text (database name, search string, file name) is shown verbatim and never translated. The suggestion names are product names and stay as written in every locale.

## Accessibility
- The form is a `fieldset` with `legend` "Add a database"; each field has a visible label and `aria-describedby` for its help; required label marked with text ("required"), not only a star. File picker is a real `<input type="file">` behind a labelled button; drop zone has the text "or drop the file here" and no information exists only in the drop zone.
- Table has real headers (`th scope`), a caption naming the screen, and a total row in `tfoot`. The counts card is a table with headers (`database`, `records`), not a paragraph of numbers. Long search strings are cut by CSS with a "Show full search" button (`aria-expanded`), never by truncating the text itself.
- Status badges pair text with role (include = frozen, unclear = staged or not frozen, blocked = refusals and missing file); colour is never the only cue; `blocked` is text/icon colour only, not a fill behind text. The draft badge is text.
- Uploading, "Added", "Removed" and "Freezing" are announced with `aria-live="polite"`; refusals use `role="alert"` and show the code as selectable text; field-level refusals set `aria-invalid` and point to the message with `aria-describedby`.
- The confirmation dialog uses `role="alertdialog"`, traps focus, and returns it to Accept. Contrast pairs from tokens (`ink` on `ground`, `brand` on `brand-soft`, role badges per BRAND_BOOK).
- RTL (ar): the layout mirrors; table columns reverse; the database name field is `dir="auto"`; file names, the search string, paths, fingerprints and the snapshot id are `dir="ltr"`; numerals Latin; the stepper arrows flip. Page content direction never reorders the PRISMA numbers inside a slot.
- Touch targets on the phone pointer are at least 44 px.

## Acceptance tests
Vitest: `import.states.test.tsx` (each of the seven states renders: empty, staged, uploading, refusal, partial, offline, accepted; every refusal code maps to a copy key and shows its code), `import.live-only.test.ts` (no Demonstration marker on `/screening/import`), `import.form.test.tsx` (label required and unique before submit hint; suggestions fill the label; `searched_on` sent as ISO date only; a file over 50 MB is stopped in the browser with `SOURCE_TOO_LARGE` copy and is not read), `import.counts-prisma.test.tsx` (the sentence and the table use the response numbers verbatim, draft badge before acceptance, none after), `import.accepted-readonly.test.tsx` (no add, remove or accept control in the DOM when `ACCEPTED`), `import.accept-dialog.test.tsx` (Go back focused first, `Esc` returns focus to Accept, the dialog states the freeze), `import.phone.test.tsx` (phone width shows the pointer and no form), `import.entry.test.tsx` (the `SNAPSHOT_NOT_ACCEPTED` card links here; Home shows the entry only while nothing is accepted), `import.i18n.test.ts` (keys exist in en; N9 guard).
Python (new): `tests/console/test_corpus_import_api.py` (state `EMPTY` then `STAGED` then `ACCEPTED`; two files with overlapping DOIs give the right per-source, total and duplicate counts; duplicates within one file are counted; `SOURCE_LABEL_TAKEN` on a repeated label including a case change; `SOURCE_NOT_RIS` on a text file and on an empty RIS, writing nothing; `SOURCE_TOO_LARGE` over 50 MB; `NOTHING_STAGED`; `CORPUS_ALREADY_ACCEPTED` on add, remove and a second accept with different files; accepting is idempotent for the same files; raw files are copied to `literature/raw/ris/` with matching sha256; the journal holds `CORPUS_SOURCE_STAGED`, `CORPUS_SOURCE_REMOVED` and `CORPUS_ACCEPTED` with the stated fields and a refused call journals nothing; the accepted snapshot passes the baseline drift check; every record keeps its source label; a phone token gets `TOKEN_SCOPE_REFUSED`; a non-loopback origin gets `ACTION_ORIGIN_REFUSED`), `tests/console/test_console_refusals.py` extended for the five new codes. Playwright: `screening/import.spec.ts` (import two RIS files of golden-uav-30 as two databases, check the counts, accept, land on 02 with Prepare enabled; refusal copy for each code; RTL pass), `screening/import.mobile.spec.ts` (WebKit mobile shows the badge and the desktop pointer only).

## Routes and refusal codes
Routes (✓ M5b, contract §4): `GET /api/v1/screening/corpus`, `POST /api/v1/screening/corpus/sources`, `POST /api/v1/screening/corpus/sources/{id}/remove`, `POST /api/v1/screening/corpus/accept`. Desktop only: a phone token gets `TOKEN_SCOPE_REFUSED` on all four.

Refusal codes (console set, outside Contract v1), from `AcceptCorpusRefused.code` in `corpus_accept.py`:
| Code | When |
| :-- | :-- |
| `SOURCE_LABEL_INVALID` | HTTP 422. The label is empty, over 40 characters, or uses characters other than letters, digits, spaces and `. & ( ) + / - _` |
| `SOURCE_DATE_INVALID` | HTTP 422. Date searched is not `YYYY-MM-DD` |
| `SOURCE_NOT_RIS` | HTTP 422. No records parsed from the file |
| `SOURCE_TOO_LARGE` | HTTP 413. The content is over 50 MB |
| `SOURCE_LABEL_TAKEN` | HTTP 409. A database with this label (case-insensitive, or the same file name slug) is already staged |
| `SOURCE_DUPLICATE_FILE` | HTTP 409. The same file (sha256) is already staged under another label |
| `SOURCE_NOT_FOUND` | HTTP 404. Remove names no staged source |
| `VERIFIED_EXISTS` | HTTP 409. `verified.json` came from discovery; database exports would replace it |
| `CORPUS_ALREADY_ACCEPTED` | HTTP 409. Add, remove or accept after the corpus is frozen |
| `NOTHING_STAGED` | HTTP 409. Accept with no staged source and no discovery corpus |

## Decisions (researcher, 2026-11-06)
Defaults accepted, with three changes. Where this list and the text above differ, this list wins.
1. **Search details are optional and hidden until needed.** Date searched and search string sit behind a closed "Search details" disclosure in the add form, not inline. A database whose files lack either shows a "not stated" flag in the table and on the counts card. The methods paragraph lists what is missing under "not stated". Nothing is required, and nothing is invented.
2. **Search string:** one free-text box per file, shown verbatim in monospace (`dir="ltr"`).
3. **RIS only** in M5b (`.ris`, `.txt`). Other formats are later. M5c-nbib (2026-11-08) added PubMed MEDLINE `.nbib`; CSV and BibTeX remain later.
4. **Steps bar:** an unnumbered "Import" step before "1 Prepare", shown until the corpus is accepted. After acceptance the step goes away and Home shows one line, for example "30 records from Scopus and Web of Science, 2 duplicates removed", with a link "What was imported" to this screen (read-only).
5. **Duplicates:** counts only. Reviewing duplicate groups by hand is a later screen.
6. **No per-database "unique contributed" column.**
7. **Removing a staged file** deletes its copy; the journal keeps its sha256 and record count.
8. **Terminal:** `--ris LABEL=PATH` repeats (done).
9. **Phone:** the "do this on your desktop" pointer only; the phone reads no corpus route.
10. **A label may repeat.** A database exported in parts is added twice under the same label ("Scopus", "Scopus"). Its files are summed into one database row, because PRISMA counts per database and the split is an export artefact. The first spelling of a label is kept ("scopus" joins "Scopus"). Each file has its own `id` for removal. `SOURCE_LABEL_TAKEN` is withdrawn; the same file twice is still refused (`SOURCE_DUPLICATE_FILE`).

**Superseded in the text above.** The table now has one row per database, summed, with its files listed under it, each with its own Remove control; "required, unique" labels are now "required, may repeat". `SOURCE_LABEL_TAKEN` is withdrawn. Remove uses `POST /corpus/sources/{id}/remove`, with the id from `GET /corpus` `sources[].id`. `GET /corpus` also returns `databases: [{label, records, files, searched_on: [dates], search_details_missing}]`, which is the row source for the table and the counts card. The "partial: file missing" state, the `a` shortcut and the drop zone are not in M5b: the file picker is the only way to add a file. The SOURCE_TOO_LARGE copy says to export in parts under the same database name.

## Open questions
None.
