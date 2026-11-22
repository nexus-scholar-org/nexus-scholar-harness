# M12a Charting table

Branch: `dev/m12a/charting-table-spec` (from `origin/main` at `1f218054`) · Lane: declared per part (K0, A, B, K, F and C, each **RELEASE**) · Status: **SPECIFICATION; questions 1 to 10 and the eight follow-up questions (1, F1 to F7) answered by the researcher on 2026-11-21** (question 6 changed: open-access copies are fetched, in a part of their own; question 9 changed: the agent-cells specification is written now, [`M12c-agent-cells.md`](M12c-agent-cells.md); F1 changed: the whole PDF kit is to become production, which adds Part K; F2 changed: B before F; F7 changed: records without a DOI are looked up by arXiv id). The five questions on what "the whole kit" covers (G1 to G5) were answered the same day, all as recommended: Part K covers downloading only. Decision item 21 (Part K's bar) was asked last: **"Production from now"** (not as recommended): the parked notice on `download` and `ingest` comes off before Part K's repairs, in a small PR of its own (K0), which carries the four smallest repairs with the words (question K0, "Label plus four repairs", as recommended). The screen specs' questions were closed the same day except two deferred items (screen 01 question 12, screen 02 question 5). **Nothing built; the start of the build is the researcher's to approve separately.** (Decision "2026-11-20 — The order of work after the acceptance run", item 5: a specification is written and read before anything is built.) · Fifth in the agreed order (plan §6, "After the acceptance run", row 5)

Short page for the researcher: [`M12a-charting-table-for-review.md`](M12a-charting-table-for-review.md). Screens (drafts; their own questions are still open): [`docs/ux/phase3-extraction/final/01-charting-table.md`](../../ux/phase3-extraction/final/01-charting-table.md) and [`docs/ux/phase3-extraction/final/02-one-study.md`](../../ux/phase3-extraction/final/02-one-study.md). Decisions: `docs/decisions.md`, "2026-11-21 — M12a charting table: the specification's choices" (answered 2026-11-21; Part F items PROPOSED).

Sources: `docs/roadmap/what-a-researcher-does.md` (steps 7 to 10), plan §6 row 5 and §8, `docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md`, the Phase 3 wireframes and findings X1 to X10 of 2026-11-02 (`docs/ux/phase3-extraction/README.md`, design history), and the code at `1f218054`, checked by the `phase-auditor` agent on 2026-11-21 (every "today" statement below carries its file reference).

## Goal

Take the researcher from the records kept at title and abstract to a filled charting table they can export and write from, in the app, without a spreadsheet kept on the side. Per kept record: get the full text (attached by the researcher, or fetched as an open-access copy that the researcher confirms) and record whether it was retrieved; decide at full text (include, or exclude with exactly one reason, counted for PRISMA 2020); chart one row per included study in the protocol's own columns, where "not reported" is a value and every change is saved, undoable and journaled. Export a CSV and a spreadsheet with the full-text counts and a methods text, and leave reading PDFs (M12b) and an agent proposing cells (M12c, specified now as a plan) for later milestones that this one makes possible.

## What a researcher does at this stage

From `what-a-researcher-does.md`: **7.** Get the full texts through the library, a request, or the authors; "not retrieved" has to be counted. **8.** Screen the full texts; each exclusion gets one reason, and the counts go into the flow diagram. **9.** Citation chasing; what is new is screened (built: M3g). **10.** Chart: one row per study in a spreadsheet; columns piloted on about five papers and revised; values from methods sections and tables; "not reported" is common and is a finding. "Most of the time goes to charting."

The first user is the researcher's own scoping review (sensor stress in UAV multispectral weed segmentation): 1,062 screened records, and, as the main session reported on 2026-11-21, about 74 included and several hundred "Unclear → full text" so far (not counted by this session: the workspace was not opened). Its protocol has two charting columns typed at Inception: "Sensor problems addressed" and "Cameras and evaluation design". They need the table within one to two weeks.

## What the app offers today (checked at `1f218054`)

**Screening ends at Publish and Export.** The header has three items, workspaces, discovery and screening (`apps/research-ui/components/site-header.tsx:34-38`); screening's pages end at publish and export; the next-step bar's last state reads "Export and methods are on Publish" (`apps/research-ui/lib/next-step-copy.ts:68`, `console/next_step.py:30-36`). Nothing follows.

**What publication writes.** `cmd_collect` (`src/scholar_harness/screening/collector.py`) writes, through `publish_generation` (`:1308`, `generation.json` last), `literature/included.json`, `excluded.json`, `conflicts.json`, `prisma_report.json`, `prisma_screening_report.md` (`screening/rounds.py:41`). An "Unclear → full text" decision is a record **inside `included.json`** with `screening.decision == "MAYBE"` (`src/scholar_search/screening.py:516-518`); there is no full-text list. Each record is the document (title, abstract, year, venue, authors, identifiers, url) plus a `screening` block (decision, reasoning, criteria, method, screener id). Publication needs every batch approved (`publication_approval.json`; without it `publish_generation` writes nothing, `collector.py:1194-1207`), and only fully decided batches can be approved; a review with undecided records cannot publish.

**The Publish screen says more than exists.** Its copy says Publish writes "the included, excluded and full-text lists" (`components/screening-publish.tsx:110-111`); there is no full-text list (`docs/ux/phase2-screening/final/09-publish.md:88` agrees with the code).

**Rounds.** When a citation-chasing round starts, the earlier round's published files are **moved** to `literature/screening_rounds/round_NNN/` (`screening/rounds.py:1-25, :111`); the current `included.json` holds only the current round; records carry no round field; no function reads the kept records of every round together. The exports read the current generation only (`screening/export.py:228`). Only counts are merged (`review_totals` in `prisma_report.json` from round 2 on).

**PRISMA and methods.** `PrismaFlowReport` (`scholar_search/screening.py:43-52`) counts identified, duplicates, screened, excluded (with reasons), included, unclear, conflicts. Nothing writes reports sought, reports not retrieved, reports assessed at full text, or full-text exclusions with reasons; the diagram's "Full-text assessed" box is computed as screened minus excluded (`screening.py:61, :94`). A legacy reader in `orchestrator.py:394-398` looks for `reports_sought_for_retrieval`, `reports_not_retrieved` and two others in `prisma_report.json`; nothing writes them. The methods paragraph is `build_methods` (`screening/export.py:514+`).

**The protocol promises a full-text tier it does not have.** `screening_criteria.two_tier_screening` defaults to true ("Tier 1 = Title/Abstract screen, Tier 2 = Full Text", `src/scholar_protocol/models.py:184-186`) and genesis writes `true` (`inception/intent.py:441`); no code runs a second tier.

**The charting columns.** `ResearchProtocol.matrix_dimensions` (`scholar_protocol/models.py:431`), each a `MatrixDimension` (`:190-230`): `id`, `name`, `description`, `target_section_category`, `data_type`, `required`, `fallback_value` (default "Not Reported"). Four types: `free_text`, `numeric`, `categorical`, `list` (`:62-74`). **No field holds the allowed values** of a categorical or list column. The researcher's own columns are written at Inception (`inception/steps.py:150, :413-439`; the form offers name, description, type and required, `components/inception-criteria.tsx:46`). The columns are part of the protocol fingerprint (`canonical.py:60`); `protocol.json` is not in the Contract v1 baseline lock (`scripts/generate_contract_baseline.py:12-51`), but changing a column moves the fingerprint, and the M10c amendment path cannot reach them (only the search fields, and refused after the corpus is accepted: `workspace_proposals.py:44-48`). Inception shows "Parked: the Matrix phase that fills these columns is not in production." (`lib/inception-copy.ts:205`, key `criteria.matrixParked`, asserted by `tests/inception-criteria.test.tsx:72`).

**What "parked" means, piece by piece.**

| Piece | What it does | How it can be reached | What "parked" means today |
| :-- | :-- | :-- | :-- |
| Stage 5 extraction (`pipeline/extraction.py`) | PyMuPDF over `pdfs/` found by slug or DOI name (`:79-95`); without a PDF, a metadata-only file with the abstract (`:160-189`), `extracted/{slug}.md` | `nexus-scholar run` (stages 5 to 9 run once `literature/included.json` exists, `pipeline/coordinator.py:1322-1346`) | **Nothing**: `run` and `extract` print no parked notice |
| Stage 6 indexing, 7 matrix, 9 synthesis | Chroma index (`rag` extra); `MatrixExtractor` writes `literature/synthesis_matrix.{csv,json,md}` with no audit event; `literature_review.md` | the same `run`; `extract index`; the kit CLI `scholar-rag matrix`; MCP `nexus_matrix_extract`; the console pipeline templates (`console/api/pipelines.py:220-302`) | Kit CLIs print "PARKED, not production" in help (`scholar_rag/cli.py:76`); MCP tool descriptions carry `PARKED_NOTICE` and still run (`scholar_agent/server.py:2414-2442`) |
| PDF kit (`scholar_pdf`) | Fetches open-access PDFs from OpenAlex and Unpaywall metadata, publisher patterns, an optional institutional proxy (`downloader.py:195-363`); names them `DOC-<sha256[:32]>.pdf` (`:111-114`); parses with PyMuPDF (`pdf` extra) or Docling/GROBID (`extract` extra); no OCR (a page without text is only classified `NEEDS_OCR`) | `scholar-pdf download|ingest|acquire|extract-run|extract`; MCP | Help prefix "PARKED" (`scholar_pdf/cli.py:38`); MCP `nexus_pdf_acquire` and `nexus_pdf_extraction` return a typed UNSUPPORTED refusal |
| `extract status|publish|index` (harness CLI, `cli.py:662-830`) | Reports extracted files; `publish` writes a Contract v1 `document_manifest` (`DocumentRecord.content_status` VALID / PARTIAL / FAILED / NEEDS_OCR); `index` runs stage 6 | CLI | No notice |
| UI | No matrix, full-text or charting route; no `ParkedNotice` component (removed 2026-11-05) | — | Plan §8: a parked surface added later must re-add the notice |

**Known broken.** PDF-07 (`docs/assessment/kit-pdf.md:58`): PDFs the kit downloads (`DOC-<sha>.pdf`) are never found by stage 5, which looks for slug or DOI names; still present at HEAD. PDF-08: the legacy parser writes "Extracted content from <name>" as a success when parsing fails (`scholar_pdf/extract.py`, around `:98-100`); still present. X3 (2026-11-02): without a model each matrix cell is the first sentence of a passage, cut at the first full stop ("97.3%" becomes "97"). `docs/kits_surface_matrix.md:119-135` calls stage 5 "RESOLVED", which PDF-07 contradicts (a stale doc, listed under follow-ups). **Consequence for this milestone:** nothing in the parked chain is reused for values; the table never reads `synthesis_matrix.*` or `extracted/`.

**Nothing attaches a PDF or a link to a screened record, or records a full-text status.** The one read route that lists `pdfs/*.pdf` and `extracted/*.md` is `GET /harvest/corpus` (`console/api/workspace.py:243-262`), which also reads a `literature/pdf_manifest.json` that nothing writes.

**Patterns that exist and can be reused.**
- Decision events (`screening/events.py`): append-only `literature/screening/events/<screener_id>.jsonl` under an OS lock; the client mints `event_id` (idempotency; same id, other content → `IDEMPOTENCY_CONFLICT`); a binding to protocol fingerprint and batch; undo is a later event with `supersedes` naming an earlier event of the same study and screener (`:599-612`), resolved by `heads()` and `winning_event()`; a batch of events and its one journal row commit together (`_commit`, `:693-737`).
- The journal writer `workspace/audit.py:146 append_event` (timestamp, event id, action, agent, description, parameters, inputs, outputs, metrics, status); a person is recorded inside `parameters` (e.g. `amended_by`).
- Method amendments (`screening/method.py:133-273`): `audit/method_amendments.jsonl` rows (amendment id, field, from, to, protocol fingerprint, amended by, at, note), journal `PROTOCOL_METHOD_AMENDED`, bound to the protocol fingerprint; the amendable fields are hard-coded to `blinding` and `not_reported`.
- The CSV writer `render_csv` (`screening/export.py:356-362`: UTF-8 with BOM, CRLF, opens in Excel) and the export route pattern (`build_export`, `:369`; `GET /export`).
- Console refusals live in `console/refusals.py` and the §7 table of `docs/architecture/screening-api-contract.md`, kept equal by `tests/console/test_console_refusals.py`; `SCREENING_NOT_PUBLISHED` already exists (M3g). New POST and PUT routes go in both allow-lists (`console/browser.py:40-66`, `apps/research-ui/app/api/console/[...path]/route.ts:48`).
- The screener id (`researcher:local` by default, `console/api/screening_v1.py:41`) is on every event; events are per screener, so a second reviewer is possible in the storage shape.
- The agent quote check: `screening/proposals.py:validate_output` (`:104`, `:124-135`): the quote must equal `text[start:end]` of the record text. A highlighted abstract exists only as an inner function of the triage page (`components/triage-page.tsx:106-120`); the API returns no highlights (`screening_v1.py:286`). M8b-triage-highlights (another session) builds the reusable component.
- No xlsx writer is a dependency in any extra (`pyproject.toml`).
- Contract v1 has no model for a retrieval record, a full-text decision or a charting cell (`contracts/models.py`); `ScreeningDecisionValue` has no full-text stage.

## Scope decisions (each argued both ways)

**Answered by the researcher on 2026-11-21** (questions of the researcher's page, quoted as chosen): 1 "Outside for now"; 2 "Beside the protocol"; 3 "Yes"; 4 "Only after publication"; 5 "Yes, smallest form"; 6 **"Fetch open-access PDFs"**, placed as **"Own part after A"** (not as recommended; see (d) and the new (d2)); 7 "Yes to both"; 8 "Add openpyxl"; 9 **"Plan it now"** (not as recommended; see (g)); 10 "A, B, C; CSV in B". Items (b), (f) and (i) were described on the page but not asked as questions; the researcher accepted all three on 2026-11-21 ("Accept all three").

**What "the whole kit" covers, answered 2026-11-21, all as recommended:** G1 "Reading waits for M12b-read"; G2 "Keep it parked"; G3 "Remove them"; G4 "Refuse with a message"; G5 "Yes, they stay parked".

**Follow-up answers, 2026-11-21** (the researcher's page, second table, quoted as chosen): 1 "Accept all three"; F1 **"Un-park the whole kit"** (not as recommended; the option read "The kit's downloader and commands become production too. Larger review and more risk; not sized"; see (d3) and Part K); F2 **"B before F"** (not as recommended; changes answer 10's order to A, B, F, C); F3 "Best open copy, labelled"; F4 "One at a time"; F5 "Leave it out" (asked after F1, knowing the kit has proxy code); F6 "Yes"; F7 **"Look up by arXiv id now"** (not as recommended; see (d2)).

### (a) Which records enter the table

**Decided 2026-11-21 (answer 4, as recommended): every record published as Include or as Unclear → full text, from every published round, read from the published files only.** In PRISMA 2020 both are "reports sought for retrieval": a title-and-abstract Include is not a final include. Each row shows its round (Databases, or Citation chasing) because PRISMA 2020 reports "other methods" in a separate column. A new engine reader joins the current `included.json` with each archived `round_NNN/included.json`.
- *For included only:* a smaller table (74 rows, not several hundred); the Unclear records could wait. *Against:* "Unclear → full text" means exactly "decide at full text"; leaving them out makes the full-text counts wrong and pushes several hundred decisions back into a spreadsheet.
- *For reading current, unpublished decisions:* the researcher could start before finishing screening. *Against:* publication is the only point where the kept set is approved and fingerprinted; rows would appear and vanish as decisions change, and the counts in the paper would not match the published screening. **Cost to the researcher:** the remaining title-and-abstract records must be decided and their batches approved before the table opens (accepted with answer 4).
- **Screening published again** (a decision changed after charting began): a row whose record left the kept set is not deleted; it is marked "No longer kept at title and abstract", keeps its values, and is left out of exports and counts. A new kept record appears marked "New since <date>".
- **A second, chased round:** its records join when that round is published; until then the table says a round is in progress. Records are keyed by `study_id`; one study in two rounds is impossible by construction (the chase screens only what is new; M3g).

### (b) Full-text status per record

**Accepted 2026-11-21 ("Accept all three"): four states.** Part F adds a fifth, `Fetched, to confirm`, which is not counted as retrieved ((d2)). `To get` (the default for every row), `Requested` (asked the library or the authors; optional date), `Retrieved`, `Not retrieved` with exactly one reason from a short fixed list (No access; Not found; Authors did not reply; Other, with words). "Sought" is not a state: every kept record is sought, as PRISMA counts it.
- **Many at once:** select rows (X; Shift+J/K extends; A selects every row shown), one key, an inline confirmation ("Mark 23 records as Retrieved? Enter to confirm"). One event per record, one journal row per action.
- *Against a richer model (request dates, reminders, library ticket numbers):* useful, but a tracker; a note per row covers it.

### (c) Full-text screening: here, or its own milestone

**Decided 2026-11-21 (answer 5, as recommended): here, in its smallest form.** Per row: `Include` or `Exclude` with exactly one reason: the protocol's exclusion criteria and failed inclusion criteria (the codes screening already uses, `EXC-n`, `FAILS-INC-n`, with their `reason_category` when set) plus "Other" with words. No per-criterion checklist, no agent, no batches, no approval code. **One record at a time** (no bulk full-text decision): PRISMA reports each as assessed. Undo as in triage.
- *For a milestone of its own:* full-text screening deserves the triage treatment (criterion answers, the agent, blinding, a publish step) and would keep M12a small. *Against:* without it the table holds every excluded-at-full-text record, the PRISMA full-text box stays empty, and the researcher keeps the decisions in a spreadsheet anyway; the protocol already promises a second tier (`two_tier_screening: true`). The smallest form is one field and one reason list on a row the table already has.
- *What it does not do (later):* link several reports of one study (PRISMA 2020's reports vs studies). M12a counts **reports** and says so in the export and the methods text; a note can say "same study as …".
- **No approval step** for full-text decisions: the researcher is the only reviewer, and the export carries the state and the bindings. A publish-like step can be added when a second reviewer exists (a later decision).

### (d) Attaching a PDF or a link (Part A)

**Decided 2026-11-21 (answer 6), not as recommended.** The recommendation was that the app fetches nothing. The researcher chose "Fetch open-access PDFs", in "Own part after A": **Part A ships with attach-your-own exactly as below and sends no request; Part F, specified in (d2), fetches.** The arguments below are kept as written; the "against" points are the conditions (d2) has to meet.

**Part A: the researcher attaches a local PDF or pastes a link, or neither; no Part A route sends a request.** An attached PDF is copied into the workspace's `pdfs/` (already gitignored) as `pdfs/<study_id>.pdf`, with its size and SHA-256 recorded; "Open" serves it from the local console in a new browser tab. A pasted link is stored as text. The record's DOI link is shown. Attaching a PDF to a row in `To get` sets it to `Retrieved` (undoable). Size limit 100 MB (a constant), PDF only (checked by its first bytes).
- *For fetching open-access copies:* most of this review's papers are open (MDPI, arXiv); a fetch would save clicks. *Against:* the fetcher is parked, PDF-07 is live, a wrong PDF silently attached is worse than none, Unpaywall needs the e-mail on every request, and no fetch has been measured on this review. The honest minimum is the researcher's own copy. *(Answered: fetching comes in Part F, after A, with each fetched PDF shown for confirmation.)*
- *Not in M12a:* reading the PDF (text, pages), a viewer inside the app, highlights in the full text (M8b's component on extracted text comes with M12b-read).

### (d2) Part F: fetching open-access copies (researcher's answer 6; F3, F4, F5, F6 accepted as recommended, F2 and F7 changed, 2026-11-21)

**What was asked.** A part of its own after A that fetches open-access copies, records each file in a manifest, and shows every fetched PDF as "to confirm" before it counts as Retrieved. Fetching stays out of Part A.

**What the researcher does.** In the Full text view they select rows, or choose "every row To get that has a DOI", and press `L` (look up; `F` already opens the form panel in screen 01). The status line asks: "Look up open-access copies of 214 records? The app asks Unpaywall and OpenAlex with your contact e-mail (shown) for the 177 with a DOI, and arXiv for the 31 with only an arXiv id, and downloads only the PDFs they list as open access. 6 selected records have neither and are skipped." Enter starts one run for the workspace; it can be cancelled and shows its progress. Each file found lands on its row as **Fetched, to confirm**, with its source, its version (published, accepted manuscript, preprint) and its licence as the provider gives them. That status is not Retrieved and is not counted as retrieved. The researcher opens the file (`O`) and either confirms it (`C`, "This is the full text of this record": the row becomes Retrieved) or discards it (`D`, with one reason: Wrong paper; Not the full text (abstract, supplement, landing page); Unreadable; Other, with words), and the row returns to its earlier status. Deciding the record at full text (`I` or `E`) on a row with a file to confirm asks first "Confirm this PDF as the full text? Enter", so the two take one step. There is no bulk confirmation: confirming means having looked.

**The manifest first (what PDF-07 requires).** PDF-07 is that the kit stores its files as `DOC-<sha256>.pdf` and keeps no record of which study a file belongs to (`downloader.py:111-114`; `docs/assessment/kit-pdf.md` §3), so nothing downstream can tell. With F1 ("Un-park the whole kit") the kit itself writes the manifest (Part K, the kit's half of PDF-07's fix), at the path its caller gives; Part F gives the one below. No file is stored without its manifest row:
- `charting/fetch_manifest.jsonl`, append-only, one row per record reached in a run: fetch run id; `study_id`; DOI; each provider asked and its answer (an open-access location, none, or an error with its HTTP status); the location used (URL as given, host type, version, licence); the final URL after redirects, each redirect, the HTTP status and content type; bytes and SHA-256; each check by name with its result; the stored path; the time; the app version.
- The file is stored by content as `pdfs/fetched/<sha256>.pdf` (under `pdfs/`, so gitignored; outside the non-recursive `pdfs/*.pdf` listing of `GET /harvest/corpus`). On confirmation, Part A's attachment event names the study, the manifest row and the hash, with `origin: fetched`, and the file is copied to `pdfs/<study_id>.pdf`, Part A's name. Confirm and discard are events in Part A's events file (`kind` `fetched_confirm`, `fetched_discard`), undoable like any other.
- Journal: `CHARTING_FETCH_STARTED` (records asked, providers, the e-mail used, whether the OpenAlex key is set but never its value) and `CHARTING_FETCH_FINISHED` (asked, found, downloaded, failed checks, errors, skipped without DOI, cancelled); confirmations ride in `CHARTING_EVENTS_RECEIVED`.
- PDF-07's harness half (stage 5 of the parked `run` looking for slug and DOI names, `pipeline/extraction.py:79-95`) stays open with reading, which waits for M12b-read (G1): Part F does not go through `run` or stage 5. It calls the kit's repaired downloader as a library (Part K), not the `scholar-pdf download` command. The manifest and the confirmed attachment are the mapping M12b-read will use. Part F does not write the legacy `literature/pdf_manifest.json` that `GET /harvest/corpus` reads and nothing writes (a follow-up).

**How a fetched file is checked before it is shown.** In this order; a failure stops the file and is written to the manifest:
1. The location came from Unpaywall or OpenAlex as an open-access PDF location, or from arXiv's own answer for the record's arXiv id; landing pages are not followed or scraped.
2. The answer is HTTP 200 after at most five redirects, each recorded.
3. The body is streamed to a staging file with a hard stop at 100 MB (Part A's limit).
4. The kit's `is_valid_pdf` (`scholar_pdf/validator.py:20-…`): a `%PDF-` header in the first 1,024 bytes, `%%EOF` in the last 8 KB, at least 10 KB. This catches an HTML page named `.pdf` and a `%PDF-`-prefixed HTML page.
5. The same SHA-256 as a file already fetched or attached for another record (a shared supplement, a publisher's error page) is shown as a warning on both rows.
6. With the `pdf` extra installed, the text of the first two pages is searched for the record's DOI and its title words ("Title found on page 1", or "Title not found: check it"); without the extra the row says "Not checked: open it". The base install does not parse PDFs.

None of these proves the file is the right paper, which is why only the researcher's confirmation makes it Retrieved (F4, "One at a time": no bulk confirmation). Version (F3, "Best open copy, labelled"): the published version first, then the accepted manuscript, then a preprint, each labelled on the row and in the export; the researcher decides at confirmation whether a preprint will do.

**What the providers need.**
- **Unpaywall:** one request per DOI with `email=` on every request. Part F uses `SCHOLAR_MAILTO`; without it the run is refused `MAILTO_NOT_SET`, the existing code and wording from discovery (`console/api/discovery.py:278-284`; decision 2026-11-08, "A live search needs a real contact email"). The kit's default `student@university.edu` (`scholar_pdf/config.py:8`) is never sent. Unpaywall's published guidance, as recalled and to be checked again when building: an e-mail on every call and at most about 100,000 calls a day; one review is a few hundred.
- **OpenAlex:** an API key is required since 2026-02-13; keyless calls share a small daily budget, then answer 409 (`scholar_search/providers/openalex.py:17-27`, decision 2026-11-10, "OpenAlex needs its API key"). The kit's lookup (`scholar_pdf/downloader.py:239-249`) sends only `mailto`, which OpenAlex no longer reads, so it is stale and not reused as it is. With `SCHOLAR_OPENALEX_KEY` set, Part F asks OpenAlex as well (its open-access locations); without it, Part F asks Unpaywall alone and says so before the run. OpenAlex calls draw on the same daily budget as a harvest.
- **The PDF hosts** named by those locations (publishers, repositories, arXiv). The app names itself (`nexus-scholar/<version> (mailto:<SCHOLAR_MAILTO>)`), not a browser (the kit sends a Chrome user agent, `downloader.py:200-201`). One request at a time per host, with a pause between requests to the same host; a 429 waits out `Retry-After` within the existing client's cap (`scholar_search/http_client.py:290-…`), otherwise the record is marked "Try later"; 403, 404 and 410 are written to the manifest and never retried (the kit retries them, `docs/assessment/kit-pdf.md` §2).
- **Records without a DOI: looked up by arXiv id** (F7, "Look up by arXiv id now", not as recommended). A record with no DOI but an arXiv id (`external_ids.arxiv_id`, set by the arXiv provider, `scholar_search/providers/arxiv.py:117-140`, and kept by deduplication, `dedup.py:107-130`) is asked of arXiv's own API (`export.arxiv.org/api/query?id_list=…`, several ids per call), which returns the entry's `pdf` link and its latest version; the PDF is that link, the one arXiv gives, not a URL the app makes up. If arXiv's answer carries a journal DOI, the record also goes to Unpaywall (and OpenAlex), and the best open copy wins (F3). Every arXiv copy is labelled "preprint (arXiv vN)". arXiv's limit, as recalled and to be checked when building: one request every three seconds on one connection, for the API and the PDFs; the code already paces arXiv at that rate (`ARXIV_RATE = 1 / 3`, `scholar_search/http_client.py:117`). The licence: the arXiv answer, as the provider reads it today, carries none, so the manifest records "arXiv; licence not given" unless the build finds a field in the answer (to check). Records with neither a DOI nor an arXiv id are skipped and counted.
- **What F7 costs.** No money and no key. Time: two requests per arXiv-only record at one every three seconds, so about four minutes for 40 such records. Build: about S on top of Part F (an id look-up beside the provider's search, one recorded cassette of the API, stub-server tests for the PDF, and the fix below). One defect found while sizing it: the provider keeps only the part of the id after the last `/` (`arxiv.py:121`), so an old-style id such as `hep-th/9901001` loses its archive and would fetch another paper or none; Part F fixes that parsing (with a test) before relying on the id.

**What is never done.** No paywall bypass of any kind: no shadow library, no login or cookies, no browser automation, no scraping of landing pages, no guessed publisher URLs (the kit's `enable_publisher_direct_patterns`, on by default in `scholar_pdf/config.py:30`, is not used, and the patterns are removed from the kit, G3 "Remove them"). No institutional proxy or gateway in Part F, neither used nor offered (F5, "Leave it out", answered knowing the kit has proxy code, `downloader.py:53-89, :365-379`; in the kit a proxy setting is refused with a message, G4 "Refuse with a message"). No fetch in the background or on a schedule: every run is started by the researcher, with its count and the services named. Fetched files stay in `pdfs/`, which is not in git, and are never exported.

**Reused and not reused.** Changed by F1 ("Un-park the whole kit"): Part F no longer builds a fetch module of its own beside a parked kit. It calls the kit's downloader as a library, after Part K has made it production (honest user agent, e-mail required, the OpenAlex key, no guessed URLs, no proxy, 4xx not retried, the manifest, the access route recorded). The app adds only what is the app's: the run (one per workspace, cancel, progress), the manifest path, the "Fetched, to confirm" status, confirm and discard, and the screen.

**Refusals.** Reused: `MAILTO_NOT_SET`, `SCREENING_NOT_PUBLISHED`, `RECORD_NOT_KEPT`, `BODY_INVALID`. New: `FETCH_ALREADY_ACTIVE` (one run per workspace), `FETCH_NOT_PENDING` (confirm or discard of a file not waiting), `DISCARD_REASON_REQUIRED`.

**Screen.** The Full text view gains the `L` action and its confirmation, the "Fetched, to confirm" status with source, version and licence, `C` and `D`, the fetch progress line, and a "To confirm" filter. Screen 01 points here; its fetch states are drafted in screen 01 before Part F is built.

**Lane and size.** **RELEASE**: outgoing provider calls, new routes and refusal codes, a new persisted manifest path. Size **M** (the kit's repairs moved to Part K; the arXiv look-up adds about S, so M at its upper end).

**Where it sits.** F2, "B before F" (not as recommended): **A, B, F, C**. F needs A (the rows and their statuses), B's finished table screen (they share it, so they are built one after the other) and Part K (the kit it calls). Re-checked for B before F:
- B must not assume the fifth status: its filters and status chips list A's four; F adds `Fetched, to confirm` and the "To confirm" filter.
- A row whose file waits for confirmation can be charted, as any row without a full text can (answer 7); confirming or discarding never touches its cells.
- The keys `L`, `C` and `D` are still free after B: screens 01 and 02 as drafted use `A`, `E`, `F`, `G`, `I`, `J`/`K`, `N`, `O`, `P`, `Q`, `R`, `X`, `Z`. B's build must keep them free (a note in screen 01).
- C still follows F, so the export carries each file's origin, version and licence. If F slips after C (risk 7), C ships with "attached" as the only origin and F adds its columns.

### (d3) Part K: the PDF kit's downloading becomes production (F1, "Un-park the whole kit", narrowed by G1 to G5, all answered 2026-11-21; item 21, "Production from now", not as recommended)

**What was asked.** The researcher chose "Un-park the whole kit" against the recommendation; the option read "The kit's downloader and commands become production too. Larger review and more risk; not sized." This section says what "production" requires for the kit, sizes it, and lists where the choice met decisions already taken; those five questions (G1 to G5) were answered as recommended, so **Part K covers downloading only**: the downloader and the `download` and `ingest` commands.

**What the kit is today** (`docs/assessment/kit-pdf.md`, 2026-11-03; the code at `1f218054` has not changed since, `git log -- src/scholar_pdf` shows only the merge and the parked notices). 13,528 lines in two unrelated stacks (PDF-01):
- **The legacy stack:** `downloader.py`, `validator.py`, `publisher_patterns.py`, `extract.py`, and the commands `download`, `ingest`, `extract` (`cli.py:301-617`). This is what the parked pipeline uses (`console/runtimes/actions.py:84,91`; `console/api/pipelines.py:221-352`; stage 5 imports `PyMuPDFEngine`, `pipeline/extraction.py:50`).
- **The contract-bound stack (WP01-E1 acquisition, E2 extraction):** `acquisition.py` (3,751 lines), `extraction.py` (3,108), their models, and the commands `acquire`, `extract-run`. Careful work (content-addressed storage, lineage checks, commit intents, typed outcomes), and called by nothing in the harness. E1 reads accepted Contract v1 parents (the corpus snapshot and the screening decisions) and refuses any study that is not `INCLUDE` (`STUDY_NOT_INCLUDED`, `acquisition.py:1154-1158`), so it cannot fetch the "Unclear → full text" rows M12a keeps (answer 4), which are outside the contract (answer 1). Its manifest is a kit sidecar, not a Contract v1 type (`docs/architecture/wp01/evidence-boundaries.md:57-59`).
- **MCP:** `nexus_pdf_acquire` and `nexus_pdf_extraction` are declared unsupported and return a typed refusal (`scholar_agent/server.py:805-863`); `nexus_extract_pdf` parses a PDF by path with PyMuPDF and is non-authoritative.
- **Tests today** (`tests/kits/pdf/`, counted, not run for this record): 170 test functions; the 2026-11-03 run collected 203, 195 passed, 8 skipped (7 need a Windows symlink privilege). By file: acquisition 19 and 51 (atomicity), extraction 48 and 6, publisher patterns 19 (they assert the guessed URLs), validator 12, downloader 9 (two cassettes, an OA lookup found and not found), CLI 5, legacy extract 1 (it asserts that a broken PDF "succeeds", PDF-08). No test drives the proxy, a real Docling or GROBID conversion, or a live fetch; no live run of `download` is recorded anywhere.

**What "production" requires before the acquisition side can be called that.** Each item is a change with a test; the reference is the finding or the line.
1. **A real contact e-mail, required.** The default `student@university.edu` (`config.py:8`) goes; the kit reads `SCHOLAR_MAILTO` and refuses without it (exit code non-zero; `MAILTO_NOT_SET` through the app).
2. **The app's own name, not a browser's.** The Chrome user agent (`downloader.py:200-201`) becomes `nexus-scholar/<version> (mailto:…)`; E1's transport already names itself, with a stale `scholar-pdf-kit/0.1` (`acquisition.py:175`).
3. **No guessed publisher URLs.** `publisher_patterns.py` was added "for Cloudflare/WAF bypass" (commit `39123d67`; module docstring), is on by default (`config.py:30`), and its IEEE rule addresses a different paper (PDF-11). **G3, "Remove them":** the direct-PDF patterns (`_PUBLISHER_PATTERNS`, `resolve_doi_to_publisher_pdf`), their setting `enable_publisher_direct_patterns` and their tests are deleted, arXiv's included (F7 reaches arXiv through its own API). `rewrite_via_proxy`, in the same module, is imported by the parked E1 (`acquisition.py:59, :1899`) and stays as parked proxy code (G4).
4. **OpenAlex with its key.** The kit's lookup sends only `mailto` (`downloader.py:239-249`), which OpenAlex no longer reads; it must send `SCHOLAR_OPENALEX_KEY`, skip OpenAlex without it, and treat 409 as "budget spent".
5. **No institutional proxy** in what becomes production (F5; **G4, "Refuse with a message"**: `download` and `ingest` refuse a set proxy, exit non-zero, and name the decision; the code stays, parked). The proxy is wired into the legacy downloader (`downloader.py:53-89, :365-379`) and E1 (`acquisition.py:1899`, `rewrite_via_proxy`).
6. **Definitive answers not retried** (PDF-06: a 404 costs about 6 s per candidate today).
7. **Open-access status from the evidence** (PDF-12): `is_oa: false` or `oa_status: closed` overrides a `pdf_url`, and the candidate that produced the bytes is recorded.
8. **The manifest** (PDF-07, the kit's half): study and DOI to file, SHA-256, source URL after redirects, version, licence, status, each check, at a path the caller gives; `download` writes one next to its output when none is given.
9. **The paper's identity looked for** (PDF-22): the DOI and title words on the first pages, recorded; "not checked" on the base install, which does not parse PDFs.
10. **Honest commands** (PDF-15: `ingest` and `download --input <missing>` exit 0 on failure); the size floor reported as a size floor (PDF-17); no `'None'` year, de-duplicated and atomic exports (PDF-18); the no-op `--smart-names`, `_safe_filename` and `models.py` removed (PDF-05).
11. **Portable writes** (PDF-03): a copy fallback where hard links fail (exFAT or FAT USB drives, some network shares), with a test.
12. **The notices and docs.** The "PARKED" help prefix (`cli.py:38`) comes off the production commands only; `docs/kits_surface_matrix.md`, the user guide, the kit skill (`.agents/skills/scholar-pdf-kit/SKILL.md`) and the kit README's drift (assessment §5) are corrected.
13. **Tests replaced, not only added:** the publisher-pattern tests go with the patterns; the downloader gains cassette and stub-server tests for items 1 to 11; the network guard covers them.

**What stays outside Part K (answered 2026-11-21).**
- **Reading PDFs** (`extract`, `extract-run`, `nexus_extract_pdf`, stage 5; PDF-08, -09, -10, -13, -14, -16, -19, -23) is "the whole kit" too, but it is what M12b-read is for, and it is large (L on its own). **G1, "Reading waits for M12b-read":** stays parked, with its notices; PDF-08 and the rest stay open until M12b-read.
- **E1 `acquire`** cannot serve M12a's rows (Include and Unclear, outside the contract). Making it production means wiring it to something or keeping it as a library, plus PDF-20, -21, -02, -04. **G2, "Keep it parked":** `acquire` keeps its parked help prefix and `nexus_pdf_acquire` its typed refusal.
- **The console's legacy pipeline templates** (`download`, then `extract`, then stages 5 to 9; `actions.py:84,91`, `pipelines.py:221-352`) feed the parked matrix and synthesis. **G5, "Yes, they stay parked".**

**How F1 and F5 fit together.** The kit becomes production; the proxy does not. Part F neither uses nor offers it (F5). In the kit, a proxy setting is refused by the production commands with a message that names the decision, rather than silently ignored, and its code stays as parked code until a decision of its own (G4, answered). Any later use would record the access route as "institutional", never as open access, and never export those files.

**Conflicts with what was already accepted, and how G1 to G5 settled them.**
- Answer 3 (accepted) keeps "fetching and reading PDFs (`scholar_pdf`)" parked; F1 un-parks the whole kit. The fetching side is settled by F1; the reading side stays parked (G1), so answer 3 holds for reading.
- Plan §8 lists full text (`scholar_pdf`, PDF-07/08) as parked in the docs, the CLI help and MCP; the main session changes §8 as listed under "What this un-parks".
- "No paywall bypass" (decision items 7 and 19): the kit's publisher patterns were written to get past bot protection (G3), and the proxy is institutional access (G4). Settled: the patterns are removed (G3) and the proxy is refused (G4), so the rule stands as written.

**Lane and size.** **RELEASE**: outgoing calls, a kit's public commands and behaviour change, a parked surface becomes production. Size **L, one PR** (final, after G1 to G5): items 1 to 13 for the downloader and `download`/`ingest`, at the upper end of L, about Part A's size. Reading (G1) and E1 (G2) are not in it.

**Item 21, Part K's bar: "Production from now"** (answered 2026-11-21, not as recommended; the option read "The parked notice comes off before the repairs. The known defects (placeholder e-mail, browser disguise) would then sit in a production command."). What it implies, plainly:

- **The words that change, and where.** The notice is one line for the whole `scholar-pdf` command group, `src/scholar_pdf/cli.py:36-41` ("PARKED, not production (Nexus Scholar 1.0 ships screening only). …"), so it covers all five commands today. It moves to the help of `extract`, `extract-run` and `acquire` only (G1, G2), and the group's help names `download` and `ingest` as production. `tests/test_parked_labels.py:16-24` lists `scholar_pdf.cli` among the parked kits and changes with it. The user guide's banner (`docs/nexus_scholar_user_guide.md:12-20`) and the surface matrix's banner and row (`docs/kits_surface_matrix.md:9-15, :32`) say "full text (`scholar_pdf`, findings PDF-07/08) still work, but are parked"; they become "downloading is production; reading PDFs is parked". The kit skill (`.agents/skills/scholar-pdf-kit/SKILL.md:12`, shipped in the wheel) still describes the publisher-pattern and proxy cascade and must say both are being removed or refused. Plan §8 "Docs" and "CLI" change as listed under "What this un-parks". The MCP tools are unchanged: `download` has no MCP tool, and `acquire`'s stays a typed refusal.
- **It is a code change, not approved to build by this answer.** The help text and its test are in `src/` and `tests/`. The answer decides what the label says; the PR that changes it needs the researcher's build approval like any other.
- **Where it naturally goes: a small PR of its own, Part K0, before Part A** (it touches only the kit's help text, its test and the docs, no file of A's), since "from now" cannot wait for Part K, which comes after A and beside B. **K0 answered "Label plus four repairs"** (2026-11-21, as recommended): the words come off together with the contact e-mail required (refused without it, reading the app's `SCHOLAR_MAILTO` as well as the kit's `MAILTO`), the app's own user agent, the publisher patterns off, and a set proxy refused with a message. **RELEASE** (a public command's network behaviour changes), size **S**. Of the five defects listed below, items 1 to 4 are then fixed in K0; item 5 waits for Part K.
- **What sits in a production command until Part K lands** (weeks: K comes after A and beside B). Run by the researcher, an agent, or the parked console pipeline buttons (G5, which call `scholar-pdf download`), `download` and `ingest` will:
  1. **send `student@university.edu` to Unpaywall and OpenAlex** on the researcher's behalf (`config.py:8`). The kit reads `MAILTO` from the environment or a `.env` in the folder it runs from; it does not read the app's `SCHOLAR_MAILTO`, so a researcher whose e-mail is set for the app still sends the placeholder;
  2. **pose as Chrome 124 on Windows** to every publisher and repository it contacts (`downloader.py:200-201`);
  3. **try the publisher patterns by default** (`config.py:30`), written "for Cloudflare/WAF bypass", which G3 decided to remove; the IEEE rule saves a different paper under the requested DOI (PDF-11), recorded as verified open access (PDF-12);
  4. **route through an institutional proxy if `PROXY_URL` is set** in the environment or a `.env` where it runs (`config.py:19`, pydantic settings), which G4 decided to refuse and F5 to leave out;
  5. call OpenAlex without the key (the keyless budget, shared with harvests, then 409); retry 404s about 6 s each (PDF-06); exit 0 on failure (PDF-15); and keep no record of which file is which study (PDF-07, files named `DOC-<sha>.pdf`).
  Items 1 and 2 reach real services under the researcher's name; items 3 and 4 contradict decisions accepted the same day; item 5 makes the output unreliable for a review. **The repairs that matter most while the commands are production and unrepaired are, in order: the e-mail (Part K item 1), the user agent (item 2), the patterns (item 3) and the proxy (item 5).** The app itself is not exposed: Part F, the only app path to the kit, comes after Part K.
- **Decision item 21 is replaced**: `download` and `ingest` are production from K0; Part K's thirteen repairs and its independent review remain the work, with DoD K1 to K7 unchanged and K8 reduced to the docs that K0 did not already change.
- **Found by the live check after K0 and fixed ahead of Part K** (2026-11-21, `H-pdf-resolver-locations`, record [`H-pdf-resolver-locations.md`](H-pdf-resolver-locations.md)): `download` read only the "best" location, so a paper whose direct PDF address is only in OpenAlex `locations` or Unpaywall `oa_locations` resolved nothing, and a failed lookup read the same as "no open copy".

**Where it sits.** K0 first, before A. Part K touches `src/scholar_pdf/`, its tests and its docs, not the table screen, so it can be built at the same time as B (different files) and must be merged before F. Order: **K0, then A, then B with K beside it, then F, then C.**

### (e) The charting itself

**Decided 2026-11-21 (answers 2 and 7, as recommended):** one row per record not excluded at full text; one column per `matrix_dimensions` item, in protocol order.
- **Types:** Text (`free_text`), Number (`numeric`), One of a list (`categorical`), Several of a list (`list`), and Yes/No (a One of with two fixed options). The **options** of a list column live in the charting form (below), because the protocol model has no field for them.
- **Every cell is one of:** empty (not charted yet), a value, **Not reported** (a value of its own, shown with words, never colour alone; it matches the protocol's `fallback_value`), or **Not applicable**.
- **Per cell, optional:** a note, and "Where from" (page, table or a short quote, free text, never checked by the app in this milestone).
- **Required columns** (`required: true`) are marked; the export counts their uncharted cells. Nothing blocks.
- **Charting without a retrieved full text is allowed** (scoping reviews sometimes chart from abstracts) and the row says "No full text" everywhere, including the export and the methods count (answer 7).
- *Against types:* free text everywhere is simpler and is what a spreadsheet gives. *For:* the researcher's first column is a list of three problems; typed options make the export countable (how many studies simulate a change of camera) without cleaning text later.

### (f) Piloting the columns, then changing them

**The form beside the protocol is decided (answer 2); the pilot and amendments were accepted on 2026-11-21 ("Accept all three"): a charting form beside the protocol, changed by recorded amendments, with a pilot switch.**
- The form (`charting/form.json`) is seeded once from `matrix_dimensions` (id, name, description, type, required) and adds what the protocol cannot hold: options, Yes/No, the order. **The protocol is never changed**, so its fingerprint, the corpus, the screening and every binding stay as they are.
- **Pilot:** a switch, on by default at first visit ("Try the form on about five studies, then revise it"); rows charted while it is on are marked Pilot. "End pilot" is one recorded click.
- **Amendments:** once any value exists, a change of a column (rename, definition, type, options added or removed, split into several, merged, added, removed) needs a one-sentence reason and writes one row of `charting/form_amendments.jsonl` (amendment id, what changed, from, to, reason, pilot or not, who, when, the protocol fingerprint and screening generation it was made under) and a `CHARTING_FORM_AMENDED` journal row. The methods text lists them ("The charting form was piloted on 5 studies and revised: …").
- **Cells a change touches** are never deleted: a renamed column keeps its values; a removed option, a changed type or a split marks the affected cells "Chart again", with the earlier value shown as history.
- *Against changing the protocol's `matrix_dimensions` instead:* a protocol schema change (options), a moved fingerprint for every protocol with columns, and an amendment path that today refuses anything after the corpus is accepted. *Against reusing `audit/method_amendments.jsonl`:* its fields are hard-coded to two and they mean the screening method; a column change is a charting matter. The shape of the row is reused, not the file.

### (g) An agent proposing cell values: later

**Decided 2026-11-21 (answer 9), not as recommended:** the researcher chose "Plan it now". The agent stays out of M12a's build, but its specification is written now, in parallel with the build: [`M12c-agent-cells.md`](M12c-agent-cells.md) and its page [`M12c-agent-cells-for-review.md`](M12c-agent-cells-for-review.md), a plan only, built on the list below. Nothing in it is approved to build, and any AI spend needs the researcher's approval.

**The recommendation, kept: not in M12a's build.** The storage leaves room for it: every event records who made it (`researcher:local` today; `agent:<model>` later) and the method (`HUMAN`).
What must exist first, in this order: (1) full text as text with page anchors (the PDF kit's parse, PDF-07 and PDF-08 fixed, a text-quality flag, X2); (2) a quote check over the full text, reusing screening's `quote_in_source` rule (the quote equals the text at its offsets), so a proposal without a checkable quote cannot be adopted; (3) the M8b highlighter on that text, to show the quote; (4) ~~a measurement on the researcher's own charted rows~~ dropped by the researcher on 2026-11-21 (M12c answer 7, "Count as I work": counts from their own adopt, edit and reject actions instead), and a spend approval; (5) the decision on Contract v1 types for cells (answer 1: a contract decision comes first; M12c question 1); (6) an adoption that records `AGENT_ADOPTED`-like provenance, never `HUMAN`. The parked `scholar_rag` matrix extractor is not a starting point (X3, X4).
- *For now:* the researcher's columns are judgement-heavy (what counts as "simulating" a camera change); an agent would save time only on cameras and splits. *Against now:* none of (1) to (4) exists, and a wrong cell in a scoping review's table is a wrong finding.

### (h) Export, PRISMA counts and the methods text

**Decided 2026-11-21 (answers 8 and 10, as recommended; the plain CSV of the Charting view comes with B):** With Part F the Full text sheet also carries each row's file origin (attached or fetched), the fetched version and licence, and the methods text adds "Open-access copies of F reports were located with Unpaywall [, OpenAlex] [and arXiv] and each was checked by the reviewer before use; D were discarded (reasons)."
- **CSV**: the charting table (one row per record not excluded at full text), with columns study id, first author, year, title, DOI, round, full-text status, then per charting column its value, note and where-from; UTF-8 with BOM, CRLF (reusing `render_csv`).
- **Spreadsheet (.xlsx)**, sheets: Charting (as the CSV), Full text (every kept record: round, status, reason, decision, reason), PRISMA counts, Charting form (columns, definitions, types, options, amendments), About (workspace, protocol fingerprint, corpus snapshot, screening generation and its publication date, export time, app version, "working export"), and, since spec 04's question 2 (answered 2026-11-22), a sixth sheet Methods (the paragraph, its notes and what it does not state). Written with `openpyxl` added to the base install (pure Python; open question 8).
- **PRISMA counts this stage adds**, per round (Databases / Citation chasing) and in total: reports sought for retrieval; reports not retrieved (with reasons); reports assessed for eligibility; reports excluded (with reasons, one each); reports included. Written to the export and to a new `charting/prisma_fulltext.json`; the screening's `prisma_report.json` is not rewritten.
- **The methods text** (its own block, beside screening's): "Of N reports sought, M were not retrieved (reasons). K reports were assessed at full text by one reviewer; E were excluded (reasons) and I were included. Data were charted by one reviewer using a form piloted on P studies and revised [list]. 'Not reported' was recorded when a study did not report an item. X studies were charted from the abstract only because the full text was not retrieved." Every number is computed; the sentence about reviewers states what the events show.
- **Exports never block.** They say how many cells are not charted yet and how many required cells are empty. Each export writes a `CHARTING_EXPORTED` journal row with the file's SHA-256, and the screen says "Exported <time>: 68 rows. Changes after this are not in that file."

### (i) Saving, undo, audit, and a second reviewer later

**Accepted 2026-11-21 ("Accept all three"):**
- **Every change is saved at once** as an append-only event in `charting/events/<screener_id>.jsonl`, the screening pattern: client `event_id`, `screener_id`, `at`, `method: "HUMAN"`, `study_id`, `kind` (`fulltext_status`, `fulltext_decision`, `attachment`, `link`, `cell`), the value, an optional note and where-from, and a binding (protocol fingerprint, screening generation id and fingerprint, form version). No Save button.
- **Undo** is a later event that `supersedes` the earlier one and restores the previous value (`Z`, as in triage). Nothing is overwritten.
- **Journal:** one row per save request (`CHARTING_EVENTS_RECEIVED`, counts by kind), committed with its events; plus `CHARTING_FORM_CREATED`, `CHARTING_FORM_AMENDED`, `CHARTING_PILOT_ENDED`, `CHARTING_ATTACHMENT_ADDED` (with the SHA-256), `CHARTING_EXPORTED`. A field is sent when it loses focus or on Enter (screen 02), never per keystroke; so a fully charted study of two columns costs a few journal rows. If that proves too noisy on 150 rows, the build may group a study's fields into one request; the event store is unchanged either way.
- **Who:** the screener id on every event and every amendment, the same identity screening uses (not a verified sign-in).
- **Re-inception** (a new protocol) archives the charting folder with the old protocol (the M4d archive rule); it is read-only there.
- **A second reviewer later needs:** their own events file (the shape already allows it); blinding of one reviewer's cells from the other until both have charted; a reconciliation view per cell; an agreed value as its own event naming both parents; agreement per column in the methods text; the second reviewer's full-text decisions counted as PRISMA asks (dual assessment). None of it is built here; nothing in M12a's storage would need migrating.

## Definition of done

Each item is checked by a test named in the build record, unless it says "live".

**Rows and full text (part A)**
- [ ] DoD 1. `GET /api/v1/charting` returns one row per record published as Include or MAYBE in the current generation and every archived round, with its round, the title-and-abstract decision and reason, and the row's state; with no current published generation it refuses `SCREENING_NOT_PUBLISHED`.
- [ ] DoD 2. A record that left the kept set after a new publication keeps its events, is marked `no_longer_kept`, and is left out of counts and exports; a new kept record is marked with the publication date.
- [ ] DoD 3. Full-text status events (`To get`, `Requested` with optional date, `Retrieved`, `Not retrieved` with exactly one reason from the fixed list, Other with words) are stored append-only per screener, idempotent on `event_id`; a reason missing or present when not allowed is refused (`FULLTEXT_REASON_REQUIRED`, new console refusal).
- [ ] DoD 4. A status set on many records is one request, one event per record and one journal row; a record not in the kept set is refused per item (`RECORD_NOT_KEPT`, new).
- [ ] DoD 5. A full-text decision (Include, or Exclude with exactly one reason from the protocol's exclusion and failed-inclusion codes or Other with words) is one record per request; a bulk decision is refused.
- [ ] DoD 6. Undo: an event with `supersedes` restores the previous value; the chain rule of screening applies (same study, same screener).
- [ ] DoD 7. A PDF upload (PDF signature, at most 100 MB) is stored as `pdfs/<study_id>.pdf` with its size and SHA-256 in the event and a `CHARTING_ATTACHMENT_ADDED` journal row; it is served back by `GET …/attachment`; anything else is refused (`ATTACHMENT_NOT_PDF`, `ATTACHMENT_TOO_LARGE`, new). A link is stored as text. No outgoing request is made by any Part A route (a test with the network guard).
- [ ] DoD 8. The table screen, Full text view, as in `01-charting-table.md`: every state has its words in en, fr and ar; keyboard as specified; axe passes in light and dark.
- [ ] DoD 9. A fourth header item and a next-step state after Publish lead to the table; Publish no longer says it writes a full-text list; Inception's "Parked: the Matrix phase…" line is replaced by "These columns are filled on the Charting step." (and its test).

**The charting form and cells (part B)**
- [ ] DoD 10. At first visit the form is seeded from `matrix_dimensions` (`charting/form.json`, version 1, `CHARTING_FORM_CREATED`); `protocol.json` and its fingerprint are unchanged (a test compares bytes).
- [ ] DoD 11. Cell events for the five types, Not reported and Not applicable, with optional note and where-from; a value that does not fit its type or options is refused (`CHARTING_VALUE_INVALID`, new).
- [ ] DoD 12. Form changes before any value exists are free (journaled); after, each needs a reason (`CHARTING_AMENDMENT_REASON_REQUIRED`, new) and writes `charting/form_amendments.jsonl` and `CHARTING_FORM_AMENDED`; affected cells become `chart_again` with their history kept.
- [ ] DoD 13. The Pilot switch marks rows; "End pilot" is recorded.
- [ ] DoD 14. The Charting view of the table and the one-study view (`02-one-study.md`), every state in words, keyboard as specified, axe light and dark; 150 rows by 5 columns stay responsive (a fixture test; budget stated in the build record).

**The PDF kit's acquisition (part K; details PROPOSED in (d3))**
- [ ] DoD K1. Without `SCHOLAR_MAILTO` the kit refuses to fetch and exits non-zero; the default e-mail is gone (a test greps the package).
- [ ] DoD K2. Every request carries `nexus-scholar/<version> (mailto:…)`; no browser user agent remains (a test on a stub server reads the header).
- [ ] DoD K3. No guessed publisher URL is requested and no proxy is used, even when the settings ask for them (the patterns are deleted, G3; a set proxy is refused with a message, G4; a test sets a proxy and sees the refusal, and the stub server sees no publisher-pattern request).
- [ ] DoD K4. OpenAlex is asked only with `SCHOLAR_OPENALEX_KEY`, sent as the key; a 409 is reported as the budget spent (cassettes).
- [ ] DoD K5. 403, 404 and 410 are not retried; a closed `is_oa` overrides a `pdf_url`; the candidate that produced the bytes is recorded (PDF-06, PDF-12).
- [ ] DoD K6. A manifest row per DOI asked, at the caller's path; no file without its row (PDF-07, the kit's half).
- [ ] DoD K7. The PDF-15, -17, -18, -05 and -03 fixes, each with its test; the publisher-pattern tests replaced; the kit suite passes.
- [ ] DoD K0 (Part K0, before A). `download` and `ingest` lose the parked prefix and the group's help names them as production; `extract`, `extract-run` and `acquire` keep it (a changed `tests/test_parked_labels.py`); the user guide, the surface matrix and the kit skill say downloading is production and reading is parked, and name the defects Part K still repairs; the four repairs of K0 ("Label plus four repairs") with their tests: DoD K1, K2 and K3 done early, with the kit reading `SCHOLAR_MAILTO` as well as `MAILTO`.
- [ ] DoD K8. The docs and the kit skill describe the repaired downloader; `extract`, `extract-run` and `acquire` keep their notice, and the MCP tools their typed refusal or parked description (G1, G2).

**Fetching open-access copies (part F, after B and K; details in (d2))**
- [ ] DoD F1. Without `SCHOLAR_MAILTO` a fetch is refused `MAILTO_NOT_SET` and no socket is opened; without `SCHOLAR_OPENALEX_KEY` OpenAlex is not asked and the run says so before it starts (tests on recorded cassettes, the suite's network guard).
- [ ] DoD F2. Every record a run reaches has a row in `charting/fetch_manifest.jsonl` (append-only; provider answers, location, version, licence, redirects, status, bytes, SHA-256, each check), including records skipped without a DOI or an arXiv id, failed, or reached before a cancel; no file is stored without its row.
- [ ] DoD F3. The checks of (d2), each on a local stub server: a real small PDF passes; an HTML page named `.pdf` and a `%PDF-`-prefixed HTML page fail; a body over the limit is cut and fails (limit lowered in the test); redirects are recorded and capped; 403, 404 and 410 are not retried; a 429 waits out `Retry-After` within the cap or ends as "Try later"; the same bytes for two records warn on both.
- [ ] DoD F4. Part F calls the kit's downloader as a library, never a copy of it; a run through the app sends no proxy and no guessed URL (K3, repeated at the app's level).
- [ ] DoD F5. A fetched file is `Fetched, to confirm` and counts as neither retrieved nor assessed; the PRISMA full-text counts do not move until it is confirmed (a test). Confirm writes the attachment with `origin: fetched` and the manifest row, and copies the file to `pdfs/<study_id>.pdf`; discard needs one reason (`DISCARD_REASON_REQUIRED`); both are undoable; confirm or discard of a file not waiting is refused `FETCH_NOT_PENDING`; a full-text decision on such a row asks for the confirmation first.
- [ ] DoD F6. One run per workspace (`FETCH_ALREADY_ACTIVE`); a cancel stops between records; a second run skips records that have a confirmed or waiting file; `CHARTING_FETCH_STARTED` and `CHARTING_FETCH_FINISHED` carry the counts and never the key.
- [ ] DoD F7. A record with no DOI and an arXiv id is asked of arXiv's API, its PDF is the link arXiv returns, paced at one request every three seconds, labelled "preprint (arXiv vN)"; a journal DOI in arXiv's answer sends it to Unpaywall too; an old-style id (`hep-th/9901001`) keeps its archive (a test on the provider's parsing); a record with neither id is skipped and counted (cassette and stub server).
- [ ] DoD F8. The Full text view's fetch states, as drafted in screen 01 before the build: words in en, fr and ar, keyboard, axe light and dark.
- [ ] DoD F9. Live, once, by the researcher on their review: a fetch run, with found, confirmed and discarded-as-wrong counted in the build record.

**Export and reporting (part C)**
- [ ] DoD 15. `GET /api/v1/charting/export?format=csv` and `format=xlsx` produce the files described in (h); a test reads the xlsx back with `openpyxl` and checks every sheet; the CSV opens with the BOM.
- [ ] DoD 16. The PRISMA full-text counts per round and in total; `charting/prisma_fulltext.json`; screening's own `prisma_report.json` unchanged.
- [ ] DoD 17. The methods block of (h), every number computed, the reviewer sentence derived from the events, amendments listed.
- [ ] DoD 18. Every export writes `CHARTING_EXPORTED` with the file's SHA-256; the screen shows the export time.
- [ ] DoD 19. Live, once, by the researcher: their own review, at least five studies charted in the pilot, one amendment, an export opened in their spreadsheet program. Recorded in the build record.

**Every part:** `generate_contract_baseline.py --check` passes (no Contract v1 file changes); the console refusal table and `console/refusals.py` stay equal; both POST allow-lists list the new routes.

## In and out

**In:** the table and the one-study view; the kept records of every published round; full-text status with reasons, set in bulk; a PDF attached or a link; the PDF kit's acquisition made production (Part K); open-access copies fetched with a manifest, by DOI or by arXiv id, and confirmed by the researcher (Part F); the full-text decision with one reason; the charting form seeded from the protocol, with types, options, Not reported, Not applicable, notes and where-from; pilot and amendments; undo; journal rows; CSV and xlsx export; PRISMA full-text counts; the methods block; the navigation step after Publish.

**Out (later, or another milestone):** fetching through an institutional proxy, guessed publisher URLs, records with neither a DOI nor an arXiv id; E1 `acquire` (G2); the console's legacy pipeline templates (G5); reading PDFs, extracted text, page anchors and the in-app viewer (M12b-read); highlights in the full text (M8b's component, applied in M12b-read); an agent proposing cells (M12c, specified now as a plan, built after (g)'s list); a second reviewer and reconciliation; linking reports of one study; per-criterion full-text answers; risk of bias or quality appraisal; synthesis, the graph, the trust score (parked); importing a spreadsheet charted elsewhere; changing the protocol's `matrix_dimensions` from the table; the phone.

## Parts, one PR each

| Part | Content | Lane | Size | Why this lane |
| :-- | :-- | :-- | :-- | :-- |
| **A. Rows and full text** | The cross-round reader, events store, status, decisions, attachments, links, undo, the table's Full text view, the nav step, the Publish and Inception wording, a CSV of the Full text view | **RELEASE** | M–L | New public routes and refusal codes, a new persisted record, a new reader of published artifacts |
| **B. Charting form and cells** | `form.json`, amendments, pilot, cell events, the Charting view, the one-study view, a plain CSV of the Charting view | **RELEASE** | L | New persisted records and routes |
| **K0. The notice comes off** (item 21, "Production from now") | `download` and `ingest` lose the parked prefix; the parked-label test; the user guide, the surface matrix and the kit skill; four small repairs (e-mail required, the app's user agent, patterns off, proxy refused; K0 "Label plus four repairs") | **RELEASE** | S | A public command's network behaviour changes |
| **K. The PDF kit's downloading to production** | (d3) items 1 to 13: e-mail required, the app's user agent, no guessed URLs, the OpenAlex key, no proxy, no 4xx retries, OA status from the evidence, the kit's manifest, the identity check, honest commands, portable writes, notices, docs and tests | **RELEASE** | L (one PR at the upper end; downloading only, G1 to G5) | A kit's public commands and network behaviour change; a parked surface becomes production |
| **F. Open-access fetching** | The fetch run through the kit, the manifest path, the arXiv-id look-up and the id fix, `Fetched, to confirm`, confirm and discard, the Full text view's fetch states, the fetch journal rows | **RELEASE** | M (upper end, with the arXiv look-up) | Outgoing provider calls, new routes and refusal codes, a new persisted manifest |
| **C. Export and reporting** | CSV and xlsx, PRISMA full-text counts, methods block, export journal | **RELEASE** | M | New public route, a new published file (`prisma_fulltext.json`), a new base dependency |

Order **K0, A, B, F, C**, with **K** built beside B (the researcher's answers 6, 10, F2 and item 21). After A the researcher can track retrieval, attach their own PDFs and decide at full text; after B they can chart; after F the open-access copies come in for confirmation; C makes the files for the paper. Six RELEASE PRs, K0 small (final). If the one-to-two-week need cannot wait for C, Part B can carry the plain CSV of the Charting view (small) and C the rest. A spreadsheet charted elsewhere cannot be brought back in (out of scope), so starting outside the app before B lands means typing twice. F and B share the table screen, so they are built one after the other (B first, F2); K shares no file with either and can be built beside B.

## Reused and new

| Need | Reused | New |
| :-- | :-- | :-- |
| Kept records | `included.json` (Include and MAYBE), `rounds.previous_rounds()` paths, `generation.json` | A reader across rounds |
| Events, undo, idempotency | The `screening/events.py` design (per-screener JSONL, lock, `supersedes`, commit with the journal row) | `charting/events/` with its own kinds |
| Journal | `workspace/audit.py:append_event` | Seven action names |
| Amendment record | The shape of `audit/method_amendments.jsonl` rows | `charting/form_amendments.jsonl` |
| Refusals | `SCREENING_NOT_PUBLISHED`, `GENERATION_STALE`, `PROTOCOL_CHANGED_SINCE_PUBLISH`, `BODY_INVALID`; the console refusal registry | The new codes listed in screen 01 (`RECORD_NOT_KEPT`, `FULLTEXT_REASON_REQUIRED`, `FULLTEXT_REASON_INVALID`, `CHARTING_VALUE_INVALID`, `CHARTING_COLUMN_UNKNOWN`, `CHARTING_AMENDMENT_REASON_REQUIRED`, `ATTACHMENT_NOT_PDF`, `ATTACHMENT_TOO_LARGE`, `LINK_INVALID`, `CHARTING_EXPORT_FORMAT_INVALID`, `CHARTING_PROTOCOL_REPLACED`) |
| CSV | `render_csv` | xlsx writer (`openpyxl`) |
| Reason codes | `EXC-n`, `FAILS-INC-n`, `reason_category` | The four not-retrieved reasons |
| Highlights | — (M8b builds the component; M12a shows the abstract as plain text) | — |
| Fetching (Parts K and F) | The kit's downloader, `is_valid_pdf`, staging and atomic promotion, its Unpaywall and OpenAlex readers, repaired in Part K; the arXiv provider and `ARXIV_RATE`; `MAILTO_NOT_SET`; the `Retry-After` cap of `scholar_search/http_client.py`; the agent-run lock pattern for one run per workspace | The kit's manifest writer; the arXiv-id look-up; `charting/fetch_manifest.jsonl`, `FETCH_ALREADY_ACTIVE`, `FETCH_NOT_PENDING`, `DISCARD_REASON_REQUIRED`, two journal actions |
| PDF reading, E1 `acquire`, matrix extractor | **Not used** by M12a (reading waits for M12b-read, G1; E1 stays parked, G2; matrix: X3, parked) | — |

## Risks

1. **The table waits for publication.** The researcher must decide every remaining title-and-abstract record and approve the batches first. If that takes longer than building, the table is ready before the data is (accepted with answer 4).
2. **Several hundred Unclear rows** make the Full text view long. Mitigation: the filter "To decide at full text", bulk status, and the one-study view moving with J/K. If the Unclear pile is mostly agent-adopted noise, the real fix is upstream (M11b).
3. **The bulk adoption of 2026-11-20** (439 exclusions and 69 inclusions recorded from drafts, each with a note) is invisible to the generated methods text; M12a's methods block does not fix that and must not repeat the pattern: full-text decisions are one at a time.
4. **`nexus-scholar run` runs the parked stages 5 to 9** once `included.json` exists, with no parked notice, writing `literature/synthesis_matrix.*` with truncated values (X3). A researcher could mistake that file for the charting table. Follow-up (outside M12a, small): print the parked notice in `run` and `extract`, or skip those stages unless asked.
5. **Two places for columns.** After an amendment, the form and the protocol's `matrix_dimensions` differ. The protocol shows what was planned, the form what was charted, and the methods text says how they differ. A re-inception starts a new form.
6. **Copyright.** Attached PDFs stay in `pdfs/`, which is gitignored; the export never includes them.
7. **Size.** Five RELEASE PRs (A, B, K, F, C) do not fit one to two weeks; A and B (the charting itself) can. Cut order if needed: F and K move after C (the researcher downloads by hand meanwhile; C ships with "attached" as the only origin), then the xlsx (CSV stays), then Not applicable, then the merge of columns (split stays).
8. **A wrong file confirmed.** A preprint or an accepted manuscript can differ from the published paper, and a fetched file can be the wrong paper. The version is shown and exported, the title check runs when the `pdf` extra is there, and only the researcher's confirmation counts; a wrong confirmation is undoable.
9. **Provider limits.** OpenAlex's keyless budget is small and shared with a harvest; Unpaywall's and arXiv's guidance is recalled, not checked. A run that meets a limit marks the affected records "Try later" rather than retrying.
10. **A kit made production in one pass.** Part K changes the network behaviour of commands that have never had a recorded live run, and replaces tests that lock in today's behaviour. Its review is an independent RELEASE review of its own; its live check is the fetch run of DoD F9.
11. **An old-style arXiv id** fetches another paper or none until the provider's parsing is fixed (in F, DoD F7).

## What cannot be verified without real PDFs and the real review

- Whether PDFs from this review's publishers upload, open from the local console in the researcher's browser on Windows, and pass the signature check (some sites serve HTML landing pages named `.pdf`).
- The time per row, and whether the keyboard flow holds over 50 to 150 rows (DoD 19, live).
- Whether the two columns as typed fit the form's types, or need splitting (that is what the pilot is for).
- How the xlsx opens in Excel and LibreOffice (the test reads it back with `openpyxl`, not with Excel).
- How many of the kept records end up "Not retrieved", and whether the four reasons are enough.
- How many of this review's records Unpaywall, OpenAlex and arXiv find an open-access PDF for, how many of those download as a valid PDF, and how many the researcher discards as wrong (DoD F9, live). No fetch was run for this specification.
- Whether the kit's repaired downloader behaves the same against real publishers and repositories as on the stub server (no live run of it exists today); and whether arXiv's answer carries a licence field.

## What this un-parks in plan §8, and what stays parked

Decision item 3 was accepted on 2026-11-21 (answer 3); answer 6 adds the fetch, F1 the kit, and G1 to G5 (answered the same day) narrow the kit to downloading. The plan itself is not edited by this specification. What the main session must change there:
- **§6, row 5 (M12a):** "A minimal charting table … export to a spreadsheet" becomes: the parked notice off `download` and `ingest` (K0, first), the charting table with full-text status and the full-text decision (A), the form and cells with a CSV (B), the PDF kit's downloading made production (K), open-access fetching by DOI or arXiv id with confirmation (F), the spreadsheet, the PRISMA full-text counts and the methods text (C); lane RELEASE per part, replacing "to be declared"; five PRs; order A, then B with K beside it, then F, then C.
- **§6, after row 5:** add M12b-read (reading PDFs page by page, PDF-08 and X2, RELEASE, L) and M12c (M12c-0 contract RELEASE M, M12c-2 app RELEASE L, M12c-3 MCP RELEASE M; no measurement part), after M12a and before M9b to M9d (M12c answer 9); the "Waiting" line that puts M9b and M9c first moves them after M12c.
- **§6, the line on M8b-triage-highlights** ("not yet placed in the order"): M12b-read and M12c need it merged; its place before M12b-read is for the main session to set.
- **§8, "Docs":** "full-text (`scholar_pdf`, PDF-07/08)" becomes: the PDF kit's downloading (`download`, `ingest`) is production from K0 (item 21, "Production from now"), with its known defects named until Part K repairs them; reading PDFs (`extract`, `extract-run`, stage 5, PDF-07's harness half, PDF-08), `acquire`, the institutional proxy and the console's legacy pipeline templates stay parked; the publisher direct-PDF patterns are removed.
- **§8, "CLI":** `download` and `ingest` lose the parked notice in K0, before Part K's repairs; `extract`, `extract-run` and `acquire` keep it; a set proxy is refused with a message.
- **§8, "MCP":** unchanged: `nexus_pdf_acquire` and `nexus_pdf_extraction` keep their typed refusal, `nexus_extract_pdf` its parked description.
- **§8, "UI":** unchanged; the charting screens are not a parked surface.
- **§8, the parked "matrix":** split: the hand-filled charting table is production (M12a); the automatic extractor stays parked; agent-proposed cells (M12c) are a new proposal task, not that extractor.
- **§8, "UI":** unchanged; the charting screens are not a parked surface.

| Plan §8 item | After M12a |
| :-- | :-- |
| "full-text" (UI) and full text in the parked docs list (`scholar_pdf`, PDF-07/08) | **Split (F1, G1 to G5).** Full-text *status* and the *full-text decision* become production, typed by the researcher. The kit's downloading (the downloader, `download`, `ingest`) becomes production after Part K's repairs, and Part F's fetch with a manifest and the researcher's confirmation is built on it. Stay parked: reading PDFs, until M12b-read (G1, PDF-08 open); E1 `acquire` and its MCP refusal (G2); the institutional proxy, refused with a message (G4); the console's legacy pipeline templates (G5). Removed: the publisher direct-PDF patterns (G3). |
| "matrix" (UI) | **Split.** The hand-filled charting table and its export become production. The automatic matrix (`scholar_rag` extractor, `nexus_matrix_extract`, stage 7 of `run`) stays parked. |
| `scholar_rag` (indexing, retrieval), synthesis | Parked. |
| `scholar_graph` | Parked. |
| `scholar_verify`, RoB / trust | Parked. |
| The rule "a parked surface shows a parked banner" | Unchanged; the charting screens are not a parked surface, so they carry none. Any link from them to a parked kit would need the notice. |

## Follow-ups found while writing this (not in M12a)

- `docs/kits_surface_matrix.md:119-135` says stage 5 is "RESOLVED"; PDF-07 is still live (`pipeline/extraction.py:79-95`).
- `src/scholar_protocol/models.py:193-195` says no pipeline reads `matrix_dimensions`; `scholar_rag/matrix.py:47` and `scholar_protocol/extraction.py:31` do.
- `src/scholar_search/screening.py:134` says included records are "advanced to PDF harvesting"; no such step follows.
- `nexus-scholar run` and `extract` carry no parked notice (risk 4).
- `GET /harvest/corpus` reads `literature/pdf_manifest.json`, which nothing writes (`console/api/workspace.py:256-262`).
- The parked `scholar_pdf` downloader sends a placeholder e-mail by default (`config.py:8`), a browser user agent (`downloader.py:200-201`), and an OpenAlex request without the key OpenAlex now requires (`downloader.py:239-249`). Now Part K's items 1, 2 and 4.
- `scholar_search/providers/arxiv.py:121` drops an old-style id's archive (`hep-th/9901001` becomes `9901001`), which also weakens deduplication on such ids (`dedup.py:107-130`); Part F fixes the parsing, the dedup consequence for existing corpora is not checked here.

## Open questions

Questions 1 to 10 and the follow-up questions 1 and F1 to F7 were answered on 2026-11-21 (top of the scope section). G1 to G5 were answered the same day, all as recommended. Item 21 was answered "Production from now" and K0 "Label plus four repairs". The screen specs' questions were closed on 2026-11-21 except screen 01 question 12 (Part F's fetch states, drafted before Part F) and screen 02 question 5 (the highlighter, left to the M8b amendment), so both specs stay DRAFT. Still open: those two items and the start of each build. The page: [`M12a-charting-table-for-review.md`](M12a-charting-table-for-review.md). The screens' closed questions are listed in each spec under "Questions closed (M12a, 2026-11-21)". The agent's questions are on [`M12c-agent-cells-for-review.md`](M12c-agent-cells-for-review.md).

## Build record

The build start was approved by the researcher on 2026-11-21 in the main session (building, not pushing). Each part is its own branch and its own PR, RELEASE lane, in the order K0, A, B (with K beside it), F, C.

### Part K0: `download` and `ingest` production, with four repairs

Branch `dev/m12a/k0-notice-off`, from `dev/m12a/charting-table-spec` (`2ea4a965`) with `origin/main` (`dacabd94`) merged in (`391fec9d`; the conflict at the top of `docs/decisions.md` kept both sides), so the specification documents travel with K0 · Lane **RELEASE** (a public command's network behaviour changes; item 27) · Decisions: `docs/decisions.md` "2026-11-21 — M12a K0" items 1 to 9 (accepted by the researcher 2026-11-21).

What was built:
- `src/scholar_pdf/config.py`: no default contact address; `contact_email()` reads the app's `SCHOLAR_MAILTO` first, then the kit's `MAILTO`; `require_contact_email()` raises `MailtoNotSetError` (`MAILTO_NOT_SET`); `user_agent()` is `nexus-scholar/<version> (mailto:<address>)`; `enable_publisher_direct_patterns` defaults to false.
- `src/scholar_pdf/downloader.py`: `process_doi` and `ingest_pdf` refuse a missing e-mail before any request; the PDF request and the OpenAlex and Unpaywall lookups send the app's user agent (the Chrome string and its `Accept-Language` are gone); the publisher-pattern candidates are no longer computed, whatever the setting says; the parked gateway code is used only when a caller passes a gateway (the `PROXY_URL` fallback is gone, review finding 2).
- `src/scholar_pdf/cli.py`: the group help names `download` and `ingest` as production and the others as parked; `extract`, `extract-run` and `acquire` carry "PARKED, not production" in their own help; `download` and `ingest` refuse, before any request and with exit code 1, a set proxy (`PROXY_REFUSED`, item 25), the pattern setting (`PUBLISHER_PATTERNS_REFUSED`, item 24) and a missing e-mail (`MAILTO_NOT_SET`).
- Docs: the banners of `docs/nexus_scholar_user_guide.md` (from the release after 1.1.0b6) and `docs/kits_surface_matrix.md` (and the matrix's pdf rows and environment table), the user guide's `SCHOLAR_MAILTO` row (now also sent to Unpaywall and OpenAlex by the kit), and the kit skill `.agents/skills/scholar-pdf-kit/SKILL.md` with its reference `references/resolution_and_download.md`, both with their bundle copies, say downloading is production and reading is parked, and name the defects Part K still repairs. Plan §8 is left to the main session (record, "What this un-parks"; the reviewer notes it should land with or right after this PR, since item 21 lists it).

| DoD | Test | State |
| :-- | :-- | :-- |
| K0 (label) | `tests/test_parked_labels.py`: `test_the_parked_pdf_commands_say_so_in_their_help` (extract, extract-run, acquire), `test_the_pdf_download_commands_are_production` (download, ingest), `test_the_pdf_kit_group_help_names_download_and_ingest_as_production`; the docs as listed above | done |
| K1 (early) | `tests/kits/pdf/test_k0_production_download.py`: `test_the_placeholder_contact_email_is_gone_from_the_kit` (greps the package), `test_download_refuses_without_a_contact_email`, `test_ingest_refuses_without_a_contact_email`, `test_the_library_refuses_before_any_request_without_a_contact_email`, `test_the_apps_scholar_mailto_is_what_the_providers_receive`, `test_scholar_mailto_wins_over_the_kits_own_mailto` | done |
| K2 (early) | `test_no_browser_user_agent_remains_in_the_kit`, `test_a_download_names_the_app_and_its_contact_on_a_stub_server` (aiohttp stub on 127.0.0.1 reads the header), `test_the_provider_lookups_name_the_app_and_its_contact` | done |
| K3 (early) | `test_the_publisher_patterns_are_off_by_default`, `test_no_guessed_publisher_url_is_requested_even_when_the_setting_asks`, `test_a_production_command_refuses_the_publisher_pattern_setting`, `test_a_production_command_refuses_a_set_proxy_with_a_message` (flag and setting, both commands), `test_the_library_does_not_read_proxy_url`; `test_a_download_with_contact_and_no_proxy_still_runs` | done (the library's parked gateway still runs when a caller passes one explicitly; Part K) |

Fails before: on the source at `391fec9d` the new file fails 17 of 18 (2026-11-21; the one that passes is the positive control `test_a_download_with_contact_and_no_proxy_still_runs`, as the reviewer confirmed by running the file against that source); four of `test_parked_labels.py`'s new tests fail there.

Replaced tests: `test_downloader.py::test_process_doi_publisher_pattern_fallback` (asserted the guessed IEEE URL; replaced by `test_no_guessed_publisher_url_is_requested_even_when_the_setting_asks`); `test_cli.py::test_cli_download_with_proxy_flags` (asserted a proxied download through the command; replaced by the refusal test, and by `test_cli_download_with_proxy_style_and_strict_validate` for the other options); `test_downloader.py::test_process_doi_proxy_subdomain_attempt` kept for the parked library proxy, without the guessed-URL step. `tests/kits/pdf/conftest.py` gives the kit's tests a test contact (decision item 8).

Not verified: no live request was sent (the brief forbids it). What a live check would settle: that Unpaywall and OpenAlex accept the app's user agent and the researcher's address as they did the browser string. Prepared (needs the researcher's approval; one Unpaywall request, one OpenAlex request, and one PDF download from the open-access location they name): `SCHOLAR_MAILTO=<the researcher's address> uv run scholar-pdf download --doi 10.7717/peerj.4375 --output <a scratch folder>`. The two orphan cassettes in `tests/kits/pdf/cassettes/` (no test reads them) still carry the old placeholder address in their recorded URLs; Part K replaces the downloader's tests.

Review round 1 (`milestone-reviewer`, on `05f065b3`, scope `391fec9d..HEAD`): **CHANGES**, 4 P3 and 5 P4 (decision items 1 to 9 judged reasonable, none contradicting an accepted item), all taken:

| # | Finding | Repair | Test |
| :-- | :-- | :-- | :-- |
| P3-1 | The skill's reference `references/resolution_and_download.md` (shipped in the wheel) still described the patterns ("default on"), the proxy rewrite and a Chrome user agent | both copies say: no guessed URL, no proxy, the app's user agent | `sync_skills_bundle.py --check` |
| P3-2 | The library still fell back to `PROXY_URL`, so K3's "no proxy even when the settings ask" was true of the commands only | the fallback is removed; decision item 5 says so | `test_the_library_does_not_read_proxy_url` |
| P3-3 | The surface matrix still said "Chrome UA" in the same bullet | "the app's user agent" | (none) |
| P3-4 | The user guide said the address is never sent to OpenAlex | the `SCHOLAR_MAILTO` row names Unpaywall and OpenAlex for the kit | (none) |
| P3-5 | No PR-stage evidence in the record | the Evidence table below | (none) |
| P4-6 | "the one passing test was a placeholder" was wrong | reworded: the positive control | (none) |
| P4-7 | The only CLI test of `--strict-validate` and `--proxy-style` went with the proxy test | a copy without `--proxy` | `test_cli_download_with_proxy_style_and_strict_validate` |
| P4-8 | `--proxy-style` read as a working option | its help: "Parked; a proxy is refused" | (none) |
| P4-9 | The banner did not say from which release | "from the release after 1.1.0b6" | (none) |

Evidence:

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| checkpoint | working tree before `7147488c` | `select_test_gate.py --changed origin/main --stage checkpoint` (pdf area): `pytest tests/kits/pdf tests/conformance/test_e1_acquired_document_boundary.py tests/conformance/test_e2_extraction_boundary.py tests/unit/test_extraction_stage.py tests/test_parked_labels.py tests/conformance/test_count_freshness.py tests/conformance/test_skill_portability.py tests/conformance/test_actions_cli_parity.py`; `sync_skills_bundle.py --check`; `git diff --check` | 444 tests, 1 failure (`extract-run`'s help had lost "authoritative"; repaired), then 54 of 54 on the repaired files; sync OK; clean | 49 s |
| pr | `7147488c` | `pytest -q -n auto` (junit); `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9`; `generate_contract_baseline.py --check`; `generate_protocol_schema.py --check`; `git diff --check origin/main...HEAD` | 6088 tests, 0 failures, 0 errors, 15 skipped; clean; clean; current; in sync; one blank line at the end of the new test file (repaired) | 1405 s |
| repairs (round 1) | `ba2201cf` | `pytest tests/kits/pdf tests/test_parked_labels.py tests/conformance/test_skill_portability.py tests/conformance/test_e2_extraction_boundary.py` (junit); real-bug ruff on `src/`; `sync_skills_bundle.py --check` | 382 tests, 0 failures, 7 skipped; clean; OK | 37 s |
| pr (final) | `9da51ac5` (`ba2201cf` with `origin/main` `86da80f4` merged in; run in a separate checkout of that commit) | `select_test_gate.py --changed origin/main --stage pr` (pdf area); `pytest -q -n 4` (junit; 4 workers, the main session's limit after the machine went down); `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9`; `generate_contract_baseline.py --check`; `generate_protocol_schema.py --check`; `git diff --check origin/main...HEAD` | 6091 tests, 4 failures, 0 errors, 15 skipped; clean; clean; current; in sync; clean | 1413 s |
| pr (final, short path) | `0b2f5cc5` (`9da51ac5` plus this record) | `pytest -q -n 4` (junit), from `.claude/worktrees/k0g`, a worktree of the branch with a short path, started only when no other pytest or Playwright run was going on the machine | 6091 tests, 0 failures, 0 errors, 15 skipped | 555 s |
| the 4 failures | `9da51ac5` code, short path | `pytest tests/console/test_methods_api.py` (junit) in the build worktree (`.claude/worktrees/…`, whose `HEAD` holds `9da51ac5` with Part A's commits, none touching screening, methods or the PDF kit) | 17 tests, 0 failures | 51 s |

The run on `9da51ac5` was not clean: its 4 failures are all in `tests/console/test_methods_api.py`, an area K0 does not touch, and come from the separate checkout's location: it lives under the session's temporary folder, and copying the golden workspace there makes a path of 264 characters, over Windows' 260 (`shutil.Error … [WinError 3] The system cannot find the path specified`, seen on the rerun of that file alone in that checkout: 4 of 17 fail). The same file passes 17 of 17 from the build worktree's shorter path. The earlier full run on `7147488c` (`-n auto`, from the build worktree) had no failure in it, and the rerun of the whole suite from the short-path worktree on `0b2f5cc5` has none (row "pr (final, short path)"), which confirms the cause. No UI file changed in K0, so typecheck, vitest, build and Playwright do not apply.

Review round 2 (on `ba2201cf`, scope `05f065b3..ba2201cf`): all nine round-1 findings confirmed repaired; one P3 left, evidence only: the PR-stage gate had to run on the final executable commit (the round-1 repairs changed code, so the earlier run could not be reused). The reviewer stated that once that run showed 0 failures and 0 errors the verdict is **APPROVE** without another review. It ran on `9da51ac5` with 4 failures from the gate checkout's path length, then on `0b2f5cc5` from a short path with none (Evidence above). Round 3 (`milestone-reviewer`, on `1df8ba22`, the evidence, the record and the merge `9da51ac5` only): **APPROVE**. In its words: "The evidence now shows a clean full PR-stage run on K0's final code, and the merge of main changed none of K0's own files." It checked that `git diff ba2201cf 9da51ac5` over K0's files is empty, that the junit files match the record (the short-path run holds the round-2 test and all 17 `test_methods_api` tests; the long-path failures are the `shutil.Error` the record gives), and that `1df8ba22` is documentation only. It did not rerun ruff, the baseline or the schema check on `9da51ac5` (recorded clean; the code is what it checked in round 2). Its P4 note on two blank lines in `docs/decisions.md` around the merged M11a Part C entry is repaired in the closing commit.

**Part K0: READY FOR PR** (not pushed). Branch `dev/m12a/k0-notice-off`. On 2026-11-21 the researcher accepted items 1 to 9 as built (asked in the main session: items 2 and 3 one by one, the other seven together), approved the push, and approved the prepared one-request live check, to be run after the merge. Plan §8 "Docs" and "CLI" should change with or right after this PR (decision item 21; record, "What this un-parks").

### Part A: rows, full-text status and decision, attachments, the Full text view

Branch `dev/m12a/part-a-rows-fulltext`, cut from K0's branch (`ba2201cf`), with K0's later commits merged in (`c6a90448`, `e50bbd53`; K0 at `2e9542f5`), so it carries K0 and `origin/main` `86da80f4`: **merge K0 first** · Lane **RELEASE** (new public routes and refusal codes, a new persisted record under `charting/`, a new reader of published artifacts, a change to the same-origin proxy) · Decisions: `docs/decisions.md` "2026-11-21 — M12a Part A" items 1 to 36 (accepted by the researcher 2026-11-21). The screen was built by a subagent from a brief written in the build session, which reviewed its report and its commits.

What was built:
- Engine `src/scholar_harness/charting/`: `kept.py` (the kept records of every published round: the current round's `included.json` when its generation is CURRENT or STALE, each archived round's copy; `chasing_pending`; `kept_history.jsonl`, from which `no_longer_kept` and `new_since` come; `protocol_replaced`), `events.py` (the append-only events store under an OS lock: kinds `fulltext_status`, `fulltext_decision`, `attachment`, `link`; validation and refusals; idempotency; undo by `supersedes` within study, screener and kind; one `CHARTING_EVENTS_RECEIVED` journal row committed with the events or neither), `attachments.py` (a streamed upload with a 100 MB stop and a `%PDF-` check, `pdfs/<study_id>.pdf`, earlier files kept under `pdfs/replaced/`, the file kept in step with undo), `table.py` (rows, counts, the reason options from the protocol, the writes, the Full text CSV), `lock.py`.
- Routes `src/scholar_harness/console/api/charting.py`: `GET /api/v1/charting`, `POST /api/v1/charting/events`, `POST` and `GET /api/v1/charting/records/{study_id}/attachment` (a raw PDF body, or a JSON link), `GET /api/v1/charting/export?format=csv&view=fulltext`; mounted in `serve.py`; the two POSTs in both allow-lists; no phone route.
- Refusals `RECORD_NOT_KEPT`, `FULLTEXT_REASON_REQUIRED`, `FULLTEXT_REASON_INVALID`, `ATTACHMENT_NOT_PDF`, `ATTACHMENT_TOO_LARGE`, `ATTACHMENT_MISSING`, `LINK_INVALID`, `CHARTING_EXPORT_FORMAT_INVALID`, `CHARTING_PROTOCOL_REPLACED` in `console/refusals.py` and `screening-api-contract.md` §7.
- `charting/` joins the re-inception archive list (`inception/emit.py`); the next step after Publish (`console/next_step.py`): DONE opens the table, PUBLISHED offers it.
- The proxy (`app/api/console/[...path]/route.ts`) forwards a PDF body as bytes and returns the attachment and the export as bytes; nothing else is widened.
- The screen `/[locale]/charting` (`components/charting-page.tsx`, `lib/charting-api.ts`, `lib/charting-logic.ts`, `lib/charting-copy.ts`): the Full text view of spec 01 with its states, banners, keyboard and inline confirmation line; a read-only list at phone width; en, fr and ar. The header's fourth item, the next-step copy, the Publish and Inception wording, and the links from Home and Export (decision items 14 to 32).

| DoD | Test (`tests/console/test_charting_api.py` unless named) | State |
| :-- | :-- | :-- |
| 1 | `test_the_table_lists_the_published_include_and_unclear_records_with_their_round`; `test_without_a_publication_the_table_refuses`; `test_an_archived_round_and_the_current_round_both_give_rows` (chasing pending) | done |
| 2 | `test_a_record_that_left_the_kept_set_keeps_its_events_and_leaves_counts_and_exports`; `test_a_record_that_joined_is_marked_with_the_publication_date`; `test_the_first_visit_marks_nothing_new`; UI `charting.stale-rows.test.tsx` | done (see "Not verified") |
| 3 | `test_status_events_are_stored_append_only_and_a_replay_is_a_silent_duplicate`; `test_a_status_reason_missing_or_not_allowed_is_refused` (7 cases); `test_other_with_words_is_a_reason` | done |
| 4 | `test_a_status_on_many_records_is_one_request_one_event_each_and_one_journal_row` (`RECORD_NOT_KEPT` per item); UI `charting.bulk-confirm.test.tsx`, `charting.keymap.test.tsx` (23 rows in 4 keypresses) | done |
| 5 | `test_a_decision_is_include_or_exclude_with_exactly_one_reason`; `test_a_bulk_decision_is_refused_whole`; UI `charting.states.test.tsx` ("decide one study at a time") | done |
| 6 | `test_undo_supersedes_and_restores_the_previous_value_for_the_same_study_and_kind`; `test_an_event_for_another_screener_is_refused`; UI `charting.keymap.test.tsx` (Z) | done |
| 7 | `test_a_pdf_is_stored_by_study_with_its_size_and_hash_and_a_to_get_row_becomes_retrieved`; `test_undo_of_an_attachment_takes_the_file_aside_and_never_deletes_it`; `test_a_second_file_keeps_the_first_aside_and_a_retried_upload_is_a_duplicate`; `test_anything_but_a_pdf_and_a_body_over_the_limit_are_refused`; `test_a_link_is_stored_as_text_and_a_bad_one_is_refused`; `test_no_part_a_route_opens_a_socket`; the browser path and the proxy as bytes (`test_the_packaged_browser_path_carries_the_pdf_and_the_csv_as_bytes`, `apps/research-ui/tests/console-proxy.test.ts`) | done |
| 8 | UI `charting.states.test.tsx`, `charting.keymap.test.tsx`, `charting.bulk-confirm.test.tsx`, `charting.not-by-colour.test.tsx`, `charting.mobile-readonly.test.tsx`, `charting.i18n.test.ts` (en, fr, ar; N9); Playwright `tests-browser/charting.spec.ts` (keyboard, axe in en and ar, light and dark, 390 px) | done |
| 9 | `tests/console/test_next_step_api.py::test_after_publish_the_next_step_opens_the_charting_table`; UI `shell`, `next-step-bar`, `screening-publish`, `inception-criteria` tests | done |
| Every part | `generate_contract_baseline.py --check`; `test_console_refusals.py`; `test_the_new_routes_are_in_both_post_allow_lists`; `test_the_protocol_file_is_never_written` | see Evidence |

Fails before: the new Python file stops at collection on `2e9542f5`'s source (`ModuleNotFoundError: scholar_harness.charting`), and the new UI files have no screen to test; the reproducing-test-first rule of the brief applies to K0 and K's repairs, not to new features.

Not verified:
- **A same-round re-publication.** The engine refuses a changed decision file in an accepted batch (`CONTENT_CHANGED`), so a fixture cannot publish round 1 again with other decisions; DoD 2 is tested with a seeded `kept_history.jsonl` row standing for the earlier publication. Whether and how a published round's kept set changes in practice (a reopen path) was not found in this build.
- **The browser run uses a fake console**, as every other `tests-browser` spec does (the config starts `next start` only); the PDF's bytes through the proxy are covered by the proxy's unit tests and the console's browser-path test, not by the browser run. The live configuration (`playwright.live.config.ts`) needs a fully decided golden workspace and was not run.
- No real PDF was opened in a browser tab; the researcher's own PDFs (upload, the signature check on publishers' files, opening from the local console on Windows) are DoD 19's live check (record, "What cannot be verified").
- The archived table's own read-only view after a re-inception is not built (decision item 11).

Evidence:

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner | working tree, `5553310b` | `pytest tests/console/test_charting_api.py tests/console/test_next_step_api.py tests/console/test_console_refusals.py` (junit) | 30, then 46, then 81 tests (after the K0 and main merge), 0 failures | |
| inner (UI) | `54a3bdaf` | typecheck; the touched vitest files; build; `playwright test tests-browser/charting.spec.ts` (the subagent's runs) | clean; 17 files, 290 tests, 0 failures; built; 8 passed (chromium, chromium-dark) | |
| pr | `f3304069` | `select_test_gate.py --changed origin/main --stage pr` (areas console, inception, harness-other, pdf, research-ui); `pytest -q -n 4` (junit; 4 workers, the main session's limit); `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9`; `generate_contract_baseline.py --check`; `generate_protocol_schema.py --check`; `sync_skills_bundle.py --check`; `git diff --check origin/main...HEAD`; `npm run typecheck`; `npx vitest run`; `npm run build`; `npx playwright test` (each heavy step started only when no other pytest, vitest or Playwright run was on the machine) | 6123 tests, 0 failures, 0 errors, 15 skipped; clean; clean; current; in sync; OK; clean; clean; 78 files, 1100 tests, 0 failures; built (the `/[locale]/charting` pages included); 652 passed, 12 skipped | 604 s; 6 s; 120 s; 20 s; 1040 s |

The Playwright run rewrote eight screenshots: the four of Home and Export (en, ar) changed with the new "Chart the included studies" link and are kept; the other four (workspaces at 1440 and 375, the empty import, the open mobile menu) were restored to the committed ones.

Review round 1 (`milestone-reviewer`, on `f4f430e9`, scope `2e9542f5..HEAD`): **CHANGES**, 1 P2, 3 P3, 5 P4; decision items judged reasonable except item 1 (finding 1) and item 33's stated reason (finding 3). All taken, in `d3b0613c` (after merging K0's PR-274 head `1a09daa8`, `16542db8`):

| # | Finding | Repair | Test (fails before: the reviewer's probe on `f4f430e9` for 1; reading for the rest) |
| :-- | :-- | :-- | :-- |
| P2-1 | The table read `literature/included.json` whenever the generation was CURRENT or STALE, but STALE also means "an output no longer matches its digest": a hand-edited file with a forged record gave a kept, writable row; archived rounds were not checked at all | each round's `included.json` must have the SHA-256 its own `generation.json` recorded, else `SCREENING_NOT_PUBLISHED`; a current round whose publication is neither current nor stale refuses the table instead of showing its rows as left (the reviewer's follow-up); decision item 1 narrowed | `test_a_hand_edited_included_file_is_never_read_as_published`, `test_an_archived_round_whose_file_was_edited_is_refused` |
| P3-2 | The read-only test accepted either code and checked `read_only` only on a 200 | exact assertions: 200, `read_only`, `CHARTING_PROTOCOL_REPLACED` on the events and the attachment routes, nothing written | `test_a_replaced_protocol_makes_the_table_read_only` |
| P3-3 | Item 33 said the undo reads each event's kind; the screen still read the ids by position | the screen reads `events` by kind; the test fake lists the kinds in the other order | `charting.keymap.test.tsx` (P and Z) with the reordered fake |
| P3-4 | `GET /charting/export` writes a journal row and had no cross-site guard | refused from another site in both guards, as the draft read is | `console-proxy.test.ts` ("refuses a cross-site charting export"), `test_the_charting_export_is_made_only_from_this_apps_pages` |
| P4-5 | The async attachment route ran the lock, the hashing and the file moves on the event loop | run in the thread pool | (existing attachment tests) |
| P4-6 | The export's journal description counted rows no longer kept | the kept count | (none) |
| P4-7 | A busy history lock on `GET /charting` was an untyped 500 | read the history instead | `test_a_busy_history_lock_still_answers_the_table` |
| P4-8 | `LINK_INVALID`'s contract row omitted the events route | added | `test_console_refusals.py` |
| P4-9 | An `OSError` while moving a PDF (a file open in a viewer) was an untyped 500, or left the file out of step after the events were stored | before the commit: `ATOMIC_COMMIT_FAILED` (503), nothing stored; after it: the events stand, the file is put in step on its next read and is served by its hash meanwhile (`serve_path` now checks the hash, not only the size) | `test_an_earlier_pdf_that_cannot_be_moved_aside_is_a_typed_refusal` |

Evidence after round 1:

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner | working tree before `d3b0613c` | `pytest tests/console/test_charting_api.py tests/console/test_browser_access.py tests/console/test_console_refusals.py -n 2` (junit); typecheck; `vitest run tests/charting.keymap.test.tsx tests/charting.states.test.tsx tests/console-proxy.test.ts` | 54 tests, 0 failures; clean; 98 tests, 0 failures | |
| pr | `d3b0613c` | the same PR gate as before, each heavy step alone on the machine: `pytest -q -n 4` (junit); `sync_skills_bundle.py --check`; typecheck; `vitest run`; build; `playwright test`; both ruff runs; baseline; protocol schema; `git diff --check origin/main...HEAD` | 6146 tests, 0 failures, 0 errors, 15 skipped; OK; clean; 79 files, 1117 tests, **2 failures** (`inception-explore.test.tsx` "opens on the first-search card…": a heading not found in time; `inception-sample.test.tsx` "names every row's button…": `Test timed out in 5000ms`); built; 664 passed, 12 skipped; clean; clean; current; in sync; clean | 674 s; 148 s; 49 s; 1186 s |
| the 2 vitest failures | `d3b0613c` | `vitest run tests/inception-explore.test.tsx tests/inception-sample.test.tsx`, three times, machine otherwise quiet | 79 of 79 each time | |

The two vitest failures are in Inception files that Part A does not touch (`git diff 1a09daa8 HEAD` over those tests and their components is empty); both are waits that ran out while the full vitest run started after six minutes of waiting for other sessions' runs to end, and both files pass alone (three runs; the reviewer's own run also 79 of 79). The Playwright run rewrote the same four screenshots as before (workspaces at 1440 and 375, the empty import, the open mobile menu); they were restored. `16542db8` merged K0's PR-274 head; `origin/main` `b36303b8` (PR 274's merge commit, the same tree as `1a09daa8`) is merged after the gate and changes no file.

Review round 2 (`milestone-reviewer`, on `15cd57eb`, the repair delta `d3b0613c` and the record): **APPROVE**. In its words: "All nine round-1 findings are fixed. I found no new P1 to P3." It reran 100 Python tests (charting, browser access, refusals, next step), the charting and proxy vitest files (111 tests), `tsc`, the real-bug ruff selection and the baseline check, all clean, and its round-1 probe is now refused. It asked that items 2 and 8 go back to the researcher with new items 34 to 36 (done: `docs/decisions.md`, Part A entry), and noted two P4 follow-ups: `GET /api/v1/charting` still appends to `kept_history.jsonl` without the cross-site guard (left as written, item 34), and a screenshot wording slip in this record (repaired).

**Part A: READY FOR PR** (not pushed). Branch `dev/m12a/part-a-rows-fulltext`; it carries K0 and `origin/main` `b36303b8`. The researcher accepted items 1 to 33 as built on 2026-11-21; items 2 and 8 (reworded) and 34 to 36 (new) were accepted as built the same day, and the push was approved.

**After merging `origin/main` `46371f45` (M11b part A), one repair by the main session, outside the review rounds above.** M11b part A's reader test (`tests/unit/test_criteria_readers.py`) failed on this branch: `charting/table.py` read the protocol's criteria itself to build the full-text exclusion reasons. `reason_options` now reads the criteria in force through `screening.criteria.criteria_in_force`, so a criterion revised before the first approval gives its wording in force and a retired one is not offered. Test: `tests/console/test_charting_api.py::test_the_full_text_reasons_are_the_criteria_in_force` (fails before, passes after). Evidence: the console, screening and PDF kit tests on the repaired tree, 1,422 tests, 0 failures, 8 skipped (`-n 4`); ruff clean; contract baseline and protocol schema current; typecheck clean. The full suite, vitest and Playwright were not repeated locally after this merge.

### Part K: the PDF kit's downloading made production

Branch `dev/m12a/part-k-kit-download`, cut from `origin/main` `55755bd7` (K0, Part A and the resolver fix, PR 278, merged), not from Part A's branch: it shares no file with Parts B and F · Lane **RELEASE** (a kit's public commands and network behaviour change) · Decisions: `docs/decisions.md` "2026-11-22 — M12a Part K" items 1 to 19 (PROPOSED). The work was built by a subagent from a brief written in the build session, which read its report and its commits and added item 18's repair.

What was built (section (d3); items 1, 2 and 5 were done by K0, the walk over every listed location by PR 278):
- Item 3: the publisher direct-PDF patterns and their tests deleted; the parked proxy code kept (`test_parked_proxy_routing.py`).
- Item 4: OpenAlex asked only with `SCHOLAR_OPENALEX_KEY` (sent as `api_key`), "not asked" said otherwise; a 409 named the budget spent.
- Item 6 (PDF-06): 400, 401, 403, 404, 410, 451 asked once; 429 within 60 s waited out; connection errors, timeouts and 5xx retried.
- Item 7 (PDF-12): closed evidence per service; the access status from the copy that produced the bytes; `INSTITUTIONAL_ACCESS` and `USER_PROVIDED`.
- Item 8 (PDF-07, the kit's half): `src/scholar_pdf/manifest.py`, a row for every DOI asked, no file without its row, `--manifest`.
- Item 9 (PDF-22): `src/scholar_pdf/identity.py`, the DOI and the title on the first two pages, "not checked" without PyMuPDF.
- Item 10: PDF-15 exit codes, PDF-17 the size floor named, PDF-18 years and exports, PDF-05 dead code removed (`models.py`, `--smart-names`, `_safe_filename`; the parked console template no longer passes `--smart-names`).
- Item 11 (PDF-03): a checked exclusive-create copy where hard links fail.
- Items 12 and 13: the guide, the surface matrix, `docs/kits/pdf/README.md` and `api_reference.md`, the kit skill and its bundle copy; the two unused cassettes with the old placeholder address deleted (nothing read them).
- After the live check of PR 278 (asked by the main session): every PDF request on the result, the row and the command's output (count, hosts, answers); PubMed Central's refusal recorded, not worked around (item 17).
- Found during the build: a DOI written as a link or with `doi:` is looked up as the bare DOI (item 18).

| DoD | Test (`tests/kits/pdf/` unless named) | Fails before | State |
| :-- | :-- | :-- | :-- |
| K1 | done by K0 (`test_k0_production_download.py`) | (K0) | done |
| K2 | done by K0; every request now listed with its host (`test_part_k_requests.py`) | 3 of 3 | done |
| K3 | `test_parked_proxy_routing.py` (the patterns gone, the proxy code parked), K0's refusals | 4 of 14 | done |
| K4 | `test_part_k_openalex_key.py` (mocked answers, no network) | 8 of 8 | done |
| K5 | `test_part_k_retries.py` (stub server on 127.0.0.1 counting requests), `test_part_k_access_status.py` | 10 of 12; 6 of 6 | done |
| K6 | `test_part_k_manifest.py` | 8 of 8 | done |
| K7 | `test_part_k_commands.py` (PDF-15, -18, -05), `test_part_k_size_floor.py` (PDF-17), `test_part_k_portable_writes.py` (PDF-03), `test_part_k_identity.py` (PDF-22), `test_part_k_doi_forms.py` (item 18); the kit suite | 12 of 14; collection error; 7 of 10; collection error; collection error | done |
| K8 | `tests/test_parked_labels.py` (notices unchanged on `extract`, `extract-run`, `acquire`), `tests/kits/agent/test_mcp_acquisition_capability.py` (MCP unchanged), `tests/conformance/test_skill_portability.py`, `sync_skills_bundle.py --check` | (docs) | done |

"Fails before" counts are the subagent's runs on the code before each fix (item 18's: mine). One test was changed after it was written: a "finished in under 2 s" check in `test_part_k_retries.py` failed under load (2.9 s) and now records whether the retry wait was used, which the old code also fails.

Not verified:
- No live request was sent. PubMed Central's answer, a FAT or exFAT drive (the copy fallback) and the base install without PyMuPDF were simulated with stubs and monkeypatches.
- Prepared checks, each needing the researcher's approval: (1) one request: with `SCHOLAR_OPENALEX_KEY` unset and `SCHOLAR_MAILTO` set, `uv run scholar-pdf ingest <a local PDF> --doi 10.7717/peerj.4375 --output <tmp>/pdfs` (one Unpaywall lookup; "OpenAlex is not asked"; one manifest row `USER_PROVIDED` with an `identity` value and no e-mail or key); (2) with the key set, `uv run scholar-pdf download --doi 10.7717/peerj.4375 --output <tmp>/pdfs` (two lookups and at most three PDF requests; the printed line and the row show PMC's answer, the repository's file, the request count and the hosts).
- A 100 MB stop and a five-redirect cap are Part F's (aiohttp's default of ten redirects applies to the command).

Evidence:

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner | `2251f398` and earlier | the kit's test files one at a time (load), and `test_e1_acquired_document_boundary`, `test_e2_extraction_boundary`, `test_actions_cli_parity`, `test_mcp_acquisition_capability`, `tests/unit/test_extraction_stage`, `test_parked_labels`, `test_skill_portability` alone (the subagent's runs); both ruff runs | kit 322 tests, 7 skipped, 0 failures (251 before Part K); the others 24, 43, 18 (2 skipped), 27, 18, 11, 113, 0 failures; clean | |
| inner | `171b40b7` | `pytest tests/kits/pdf/test_part_k_doi_forms.py tests/kits/pdf/test_part_k_commands.py tests/kits/pdf/test_part_k_manifest.py tests/kits/pdf/test_cli.py` (junit) | 33 tests, 0 failures | |
| pr | `a9f15b99` (code as `171b40b7`) | `select_test_gate.py --changed origin/main --stage pr` (areas console, pdf; no UI file); `pytest -q -n 4` (junit), started when no other pytest, vitest or Playwright run was on the machine; `sync_skills_bundle.py --check`; `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9`; `generate_contract_baseline.py --check`; `generate_protocol_schema.py --check`; `git diff --check origin/main...HEAD` | 6370 tests, 0 failures, 0 errors, 15 skipped; OK; clean; clean; current; in sync; clean | 711 s |

No file under `apps/` changed, so typecheck, vitest, build and Playwright do not apply. A first start of this gate with the UI steps included was stopped while it waited for the machine (its pytest workers ended); nothing from it is reported.

Review round 1 (`milestone-reviewer`, on `560f5dc6`, scope `55755bd7..HEAD`): **APPROVE**, with two P3s to repair before the researcher answers and six P4s. In its words: no P1 or P2 findings; none of items 1 to 19 contradicts an accepted item (item 1 narrows the resolver's accepted item 4 for the keyless case, which the researcher should see). Repairs:

| # | Finding | Repair | Test |
| :-- | :-- | :-- | :-- |
| P3-1 | The lookup client's on-disk cache stored each lookup address, OpenAlex key and e-mail included, in plain text under the folder the command ran from; item 2 understated it | the kit's three lookup clients keep no disk cache; item 2 reworded | `test_part_k_review.py::test_the_kits_lookup_clients_keep_no_disk_cache` |
| P3-2 | A library caller's forward proxy left files labelled open access (accepted item 25) | the downloader refuses a forward proxy (`PROXY_REFUSED`); new item 20 | `test_the_downloader_refuses_a_forward_proxy`; `test_downloader.py::test_gateway_and_forward_proxy_are_not_conflated` now expects the refusal |
| P4-3 | DoD K4 says "cassettes"; the tests mock the lookup client | not changed: the real client's 409 mapping (`http_client.py`) is the search kit's and is not exercised here; recorded as a deviation | (none) |
| P4-4 | No test read the user agent on the stub server (DoD K2) | asserted on every request the stub server saw | `test_part_k_requests.py::test_each_pdf_request_is_on_the_result_and_its_row` |
| P4-5 | Three storage-failure messages keep the error's text | item 4 says so (local paths only) | (none) |
| P4-6 | An invalid address or a certificate error was retried | not retried | `test_an_invalid_address_or_a_certificate_error_is_not_retried` |
| P4-7 | The copy's hash check and the exclusive-create race have no test | not added; a follow-up | (none) |
| P4-8 | One DOI written two ways in the input cost two lookups and two rows | de-duplicated on the bare DOI; item 18 | `test_the_input_file_is_deduplicated_on_the_bare_doi` |

The new tests fail on `560f5dc6`'s code by reading (no `cache_enabled` passed; a forward proxy only refused when equal to the gateway; `InvalidURL` and `ClientSSLError` are `ClientError`s; three calls for one DOI). Follow-ups the reviewer named, outside Part K: plan §8 still lists `scholar_pdf` downloading as parked (the main session's); the search kit's cache holds its key too; `download --input` does not count records without a DOI; a rare case where two DOIs share bytes and the first row fails.

Evidence after round 1:

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner | working tree before `a6a32eeb` | `pytest tests/kits/pdf -n 2` (junit); real-bug ruff on `src/` | 333 tests, 7 skipped, 0 failures; clean | 32 s |
| pr (final) | `a7b60db2` (code as `a6a32eeb`) | `pytest -q -n 4` (junit), started when no other pytest, vitest or Playwright run was on the machine; `sync_skills_bundle.py --check`; both ruff runs; baseline; protocol schema; `git diff --check origin/main...HEAD` | 6375 tests, 0 failures, 0 errors, 15 skipped; OK; clean; current; in sync; clean | 641 s |

A first start of this gate was cut off when the desktop app restarted; its leftover workers were ended and the gate was run again from the start.

Review round 2 (`milestone-reviewer`, on `70c58559`, the repair delta `560f5dc6..HEAD`): **APPROVE**. In its words: "All eight round 1 findings are resolved: six repaired, P4-3 recorded as a deviation and P4-7 listed as a follow-up. Nothing in the delta opens a new P1, P2 or P3." It reran the kit's tests (333, 0 failures, 7 skipped), the baseline check, the real-bug ruff run and `git diff --check`, all clean. One P4 follow-up: the no-cache test drives `download` only; `ingest` and `download_batch` are checked by reading.

**Part K: READY FOR PR.** Branch `dev/m12a/part-k-kit-download`, from `origin/main` `55755bd7`, with `origin/main` merged in by the main session, twice (`9e4be45f`, then `4962c9eb` after PR 282; document conflicts only, both sides kept; no code conflict). Decision items 1 to 20 were accepted by the researcher on 2026-11-22 as built (item 1 narrows the resolver's accepted item 4 for the keyless case; on item 17 they chose to plan PMC's own open-access route as a follow-up after Part F), the push was approved, and the two prepared live checks were approved for after the merge, the commands shown first.

**Part K: merged** on 2026-11-22 (PR 283, merge commit `258f9cc6`, 12 of 12 checks, head `76b47c15`).

Live checks after the merge (2026-11-22, the main session, on `main` `258f9cc6`; approved by the researcher, who also allowed the contact address and the OpenAlex key to be loaded from their `.env`; neither value was printed, and neither appears in the output or the manifest files, searched for both):

| Check | Command | Result |
| :-- | :-- | :-- |
| 2 (with the key) | `scholar-pdf download --doi 10.7717/peerj.4375 --output <scratch>` | exit 0; OpenAlex 200, Unpaywall 200; 2 PDF requests: `pmc.ncbi.nlm.nih.gov` "not a PDF (no %PDF- header in the first 1024 bytes)", `umontreal.scholaris.ca` stored (submittedVersion, cc-by, 2,433,346 bytes; "address 2 of 2 listed"); the printed line and the row name both hosts and the count; row `ACQUIRED`, `VERIFIED_OPEN_ACCESS`, route `open_location`, checks header, trailer and size floor pass, identity "doi found" |
| 1 (key unset) | `scholar-pdf ingest <that PDF> --doi 10.7717/peerj.4375 --output <scratch>` | exit 0; "OpenAlex is not asked: SCHOLAR_OPENALEX_KEY is not set. Only Unpaywall is asked."; lookups: openalex `NOT_ASKED`, unpaywall `ANSWERED` 200; row `ACQUIRED`, `USER_PROVIDED`, route `user_provided`, identity "doi found" |

Both as the build predicted, PMC's refusal included (decision item 17). Not covered by these two checks: a retry, a 429, a closed work, a forward proxy, the copy fallback, and a batch input file.

### Part B: the charting form, cells, pilot and amendments; the Charting view and the one-study view

Branch `dev/m12a/part-b-form-cells`, from Part A's `b4bdd6eb`, with Part A's PR-276 head `d110afe4` merged in (`1616d83b`; it brings `origin/main` `46371f45`, M11b part A, and the full-text reasons read through `criteria_in_force`): **merge Part A first** · Lane **RELEASE** (new persisted records `charting/form.json` and `charting/form_amendments.jsonl`, new routes and refusal codes) · Decisions: `docs/decisions.md` "2026-11-21 — M12a Part B" items 1 to 34 (accepted by the researcher 2026-11-22; items 30 and 31 change or read accepted Part A items 29 and 18). The screens were built by a subagent from a brief written in the build session, which read its report and its commits.

What was built:
- `src/scholar_harness/charting/form.py`: the form seeded once from `matrix_dimensions` (`CHARTING_FORM_CREATED`), versioned saves (free before any value, `CHARTING_FORM_CHANGED`; after, a one-sentence reason, one row per change in `form_amendments.jsonl`, `CHARTING_FORM_AMENDED`), the diff (added, removed, renamed, definition, type, options, required, order, split, merged, replaced), "End pilot" (`CHARTING_PILOT_ENDED`), the cell value check by type.
- `src/scholar_harness/charting/cells.py`: each study's cells as the form and its amendments make them read (value, Not reported, Not applicable, empty; note, where-from, pilot, "Chart again" with history), "charted", "has values".
- `events.py`: the `cell` kind (its undo chain per column), `where_from`, the pilot and the form version stamped by the engine. `table.py`: cells and counts (charted, not charted, pilot) on every row, the form in the table's answer, `GET`/`PUT /api/v1/charting/form`, `POST /api/v1/charting/form/pilot/end`, `GET /api/v1/charting/records/{study_id}`, the Charting CSV (`view=charting`).
- Refusals `CHARTING_VALUE_INVALID`, `CHARTING_COLUMN_UNKNOWN`, `CHARTING_AMENDMENT_REASON_REQUIRED`, `CHARTING_FORM_STALE` (console set and contract §7); the PUT and the pilot POST in both allow-lists.
- Screens (`apps/research-ui`): the Charting view of `/[locale]/charting` (`components/charting-cells.tsx`, in-cell editing, filters, "Chart the next study", the first-visit card, the no-columns state, the Export menu with two CSVs), the form panel (`components/charting-form-panel.tsx`), the one-study view `/[locale]/charting/study?id=…` (`components/charting-study.tsx`), copy in en, fr and ar.

| DoD | Test (`tests/console/test_charting_form_api.py` unless named; UI files under `apps/research-ui/tests/`) | State |
| :-- | :-- | :-- |
| 10 | `test_the_form_is_seeded_once_from_the_protocol_and_the_protocol_is_never_written` (bytes compared, one `CHARTING_FORM_CREATED`); `test_a_protocol_without_columns_seeds_an_empty_form` | done |
| 11 | `test_cells_of_every_type_with_not_reported_not_applicable_note_and_where_from`; `test_a_value_that_does_not_fit_its_column_is_refused` (10 cases); `test_where_from_goes_only_with_a_cell`; `test_undo_of_a_cell_follows_its_own_column`; UI `charting.cells-keymap.test.tsx` | done |
| 12 | `test_a_change_before_any_value_is_free_and_journaled`; `test_after_a_value_a_change_needs_a_reason_and_is_recorded` (and `CHARTING_FORM_STALE`); `test_a_changed_type_or_a_removed_option_marks_chart_again_and_keeps_the_history`; `test_a_split_marks_the_new_columns_with_the_earlier_value_as_history`; UI `charting.form-panel.test.tsx`, `charting-study.history.test.tsx` | done |
| 13 | `test_end_pilot_is_recorded_once_and_later_cells_are_not_pilot` (pilot values kept as final); UI `charting.charting-view.test.tsx`, `charting.form-panel.test.tsx` | done |
| 14 | UI `charting.charting-view.test.tsx`, `charting.cells-keymap.test.tsx`, `charting-study.keymap.test.tsx`, `charting-study.readonly.test.tsx`, `charting-study.no-fulltext.test.tsx`, `charting-study.mobile.test.tsx`, `charting-study.i18n.test.ts`; Playwright `tests-browser/charting-study.spec.ts` (five studies by keyboard, undo, an amendment in the panel, axe light and dark, no page scroll at 1440×900 and 1280×720, 390 px) and `charting.spec.ts`; budget below | done |
| Every part | `test_the_form_routes_are_in_both_allow_lists`; `test_console_refusals.py`; `generate_contract_baseline.py --check`; `tests/unit/test_criteria_readers.py` (no charting file reads the screening criteria itself) | see Evidence |

DoD 14's budget (150 kept rows × 5 columns, about half charted): `charting.budget.test.tsx` (jsdom, development React) holds the first draw under 4,000 ms, an arrow-key move under 150 ms on average over 120 moves, and one edit (Enter, type, Enter) under 600 ms; measured on its last run 615 ms, 35 ms and 119 ms (a busy machine; the numbers varied between runs). In Chromium on the production build (the last test of `charting-study.spec.ts`): page load to the drawn grid under 3,000 ms and under 50 ms per key over 60 keys, Playwright's round trip included; measured 431 and 521 ms, 6.6 and 8.1 ms per key (light, dark). Three changes got there: the phone list's cards are memoised (it re-rendered on every key: 175 to 225 ms a move), only the layout the window shows is drawn, and a focus landing where the screen already is no longer renders twice.

Fails before: on `b4bdd6eb`'s source the new Python tests fail (no `/form` route, no `cell` kind, no form in the table's answer); the screens are new.

Not verified:
- Merging columns in the panel is not built; the engine's merge and replacement are tested (`test_a_replaced_column_and_a_merge_are_recorded_and_mark_chart_again`), the panel offers a split only.
- The count of required cells not charted (scope (e): "the export counts their uncharted cells") is deferred to Part C's export and methods text; Part B marks required columns and counts rows not charted.
- Attach a PDF and Open it from the one-study view: the controls exist (Part A's actions) but no test drives them there.
- `npm run build:export` (the static export) was not run; the study route uses a query parameter so that it can be exported.
- Every UI test uses the fake console; the fake imitates the "Chart again" rules, which the Python tests check on the real engine.
- How the two columns as the researcher typed them fit the five types, and whether the keyboard flow holds over 50 to 150 rows with real text, are DoD 19's live check.

Evidence:

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner | `c9614db2`, `117c92f2` | `pytest tests/unit/test_criteria_readers.py tests/console/test_charting_api.py tests/console/test_charting_form_api.py tests/console/test_console_refusals.py tests/console/test_browser_access.py -n 2` (junit) | 78, then 70 tests after the merge of Part A's PR-276 head (`test_criteria_readers` included), 0 failures | |
| inner (UI) | `eaa6caad` | typecheck; 28 vitest files (the 17 charting files and their neighbours); build; `playwright test tests-browser/charting-study.spec.ts`, `charting.spec.ts` (the subagent's runs, one at a time) | clean; 361 tests, 0 failures; built; 16 and 8 passed | |
| pr | `117c92f2` | `pytest -q -n 4` (junit); `sync_skills_bundle.py --check`; typecheck; `vitest run`; build; `playwright test`; both ruff runs; baseline; protocol schema; `git diff --check origin/main...HEAD` (each heavy step alone on the machine) | 6231 tests, 0 failures, 0 errors, 15 skipped; OK; clean; 89 files, 1177 tests, **3 failures**; built; 680 passed, 12 skipped; clean; clean; current; in sync; one blank line at the end of `charting-study.tsx` | 641 s; 304 s; 60 s; 1213 s |
| the 3 vitest failures | `117c92f2` | read one by one | two real: the app's rule N12 (`i18n-direction-source.test.ts`: `charting-page.tsx` read `localStorage` to remember the first-visit card) and the guidance audit (`guidance.never-hidden.test.tsx`: the one-study view's two tips had no row in `docs/ux/shared/final/03-guidance.md`); one flake (`discovery-proposals.test.tsx`, files Part B does not touch; 5 of 5 alone, twice) | |
| repairs | `4f8139df` | the card closes for the page load (no browser storage; decision item 23 reworded); rows `X-ST1`, `X-ST2` and an `X-` prefix in the audit's reader (`tests/fixtures/guidance-audit.ts`); the blank line | | |
| pr (UI half, final) | `4f8139df` | the Python files that read the UI's files (`test_browser_access`, `test_lineage_api`, `test_screening_drafts_api`, `test_screening_read_api`, `test_wheel_build_hook`, `test_select_test_gate`; junit); typecheck; `vitest run`; build; `playwright test`; `git diff --check origin/main...HEAD` | 113 tests, 0 failures; clean; 89 files, 1177 tests, 0 failures; built; 680 passed, 12 skipped; clean | 76 s; 159 s; 26 s; 1050 s |

Since `117c92f2` only UI files and documents changed (`git diff --name-only 117c92f2 4f8139df`: `charting-page.tsx`, `charting-study.tsx`, `charting.charting-view.test.tsx`, `tests/fixtures/guidance-audit.ts`, `docs/decisions.md`, `docs/ux/shared/final/03-guidance.md`), so the full Python run on `117c92f2` stands for the Python side, and the Python tests that read files under `apps/research-ui/` ran again on `4f8139df`. Both Playwright runs rewrote the same four screenshots as Part A's (workspaces at 1440 and 375, the empty import, the open mobile menu); they were restored.

Review round 1 (`milestone-reviewer`, on `57a96c29`, scope `d110afe4..HEAD`): **CHANGES**, 1 P1, 2 P2, 6 P3 (and P4 follow-ups); decision items judged readings except item 13 (it changes spec 02's closed question 1) and item 12's claim. All taken:

| # | Finding | Repair | Test (fails before: the reviewer's probes on `57a96c29` for 1 to 3) |
| :-- | :-- | :-- | :-- |
| P1-1 | After a split, every later save from the panel was refused `BODY_INVALID` (the new columns keep naming the column that is gone) | `derived_from` is checked only for a column new in the save or whose sources change; the fake console applies the same rule | `test_after_a_split_the_form_still_saves_and_the_split_history_stays`, `test_a_free_split_before_any_value_also_keeps_saving` |
| P2-2 | A "several" value with a non-text item and a number beyond a float's range raised (500, the whole request lost) | strings checked first; `OverflowError` refused | `test_a_value_that_does_not_fit_its_column_is_refused` (three new cases) |
| P2-3 | "1,260" was stored as 1.26 | a comma before three digits, two commas or a hexadecimal is asked again; item 19 reworded | `charting.number-reading.test.ts` |
| P3-4 | Item 13 changes spec 02's closed question 1 without saying so | flagged for the researcher | (none) |
| P3-5 | No test of `replaced` or `merged`; item 12's speed claim rested on the UI's fake | engine tests added; the projection groups the events once per answer (0.35 s became about 0.01 s on the reviewer's probe); item 12 states the measure | `test_a_replaced_column_and_a_merge_are_recorded_and_mark_chart_again`; the probe (`scratchpad/probe_perf2.py`) |
| P3-6 | The CSV test did not assert an empty cell or a left-out row | both asserted | `test_the_charting_csv_writes_words_for_not_reported_and_leaves_uncharted_cells_empty` |
| P3-7 | A form save was three writes with no rollback; "has values" was read outside the events lock | rolled back on failure (`ATOMIC_COMMIT_FAILED`, 503); `put_form` holds the events lock (then the form's, always in that order); "End pilot" the same | `test_a_form_save_whose_journal_row_fails_changes_nothing` (the lock: by reading) |
| P3-8 | A `form.json` of another schema was silently re-seeded | refused `CHARTING_FORM_STALE` and kept | `test_a_form_file_this_version_cannot_read_is_refused_and_kept` |
| P3-9 | Required cells not charted were not counted and not listed as deferred | deferred to Part C, listed under "Not verified" above | (none) |

The repairs also changed the meaning of decision items 2 (a form save is all or nothing, `ATOMIC_COMMIT_FAILED`; "has values" is read while no cell can be stored) and 4 (the new columns keep naming their sources; an unreadable `form.json` is refused `CHARTING_FORM_STALE` and kept), besides 12, 13 and 19; all are PROPOSED, and the researcher sees them reworded.

P4 follow-ups left as they are: two protocol ids that become the same once made safe lose a column at seeding; a new column naming a column still in the form is recorded as "added" yet marked Chart again; a clear without `supersedes` keeps form changes as amendments; no test that nothing is seeded while the table is read-only; the `CHARTING_VALUE_INVALID` words say "not one of the options" for a text that is too long. ("0x10" is now asked again, with finding 3.)

Evidence after round 1:

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner | working tree before `72813eca` | `pytest tests/console/test_charting_form_api.py tests/console/test_charting_api.py tests/unit/test_criteria_readers.py -n 2` (junit); `vitest run tests/charting.number-reading.test.ts tests/charting.form-panel.test.tsx tests/charting.cells-keymap.test.tsx`; typecheck | 73 tests, 0 failures; 21 tests, 0 failures; clean | |
| pr (final) | `72813eca` | the full PR gate, each heavy step alone on the machine: `pytest -q -n 4` (junit); `sync_skills_bundle.py --check`; typecheck; `vitest run`; build; `playwright test`; both ruff runs; baseline; protocol schema; `git diff --check origin/main...HEAD` | 6239 tests, 0 failures, 0 errors, 15 skipped; OK; clean; 90 files, 1179 tests, 0 failures; built; 680 passed, 12 skipped; clean; clean; current; in sync; clean | 716 s; 151 s; 23 s; 1084 s |

The Playwright run rewrote the same four screenshots as before; they were restored.

Review round 2 (`milestone-reviewer`, on `edf2f482`, the repair delta `57a96c29..HEAD`): **APPROVE**. In its words: "All nine round-1 findings are repaired, and none of the repairs breaks anything I checked." It reran 92 Python tests and the three touched vitest files (21 tests), all clean, and its round-1 probes now behave as expected through the route. Two documentation points, repaired in the closing commit (no executable change, so the gate on `72813eca` stands): the contract row of `CHARTING_FORM_STALE` now names every route that loads the form and the unreadable-form meaning; the record and the open-decisions row say items 2 and 4 changed meaning too. P4 follow-ups, left as they are: the screen's words for `CHARTING_FORM_STALE` ("Reload the table") do not fit an unreadable form; "1.260" is read as 1.26 (right in English, ambiguous in French); a narrow two-tab race in which a free form change lands between `post_events` building its form context and taking the events lock; a change of `derived_from` alone is not stored (no difference found).

**Part B: READY FOR PR** (not pushed). Branch `dev/m12a/part-b-form-cells`; it carries Part A's PR-276 head `d110afe4` and must be merged after Part A. Decision items 1 to 34 were accepted by the researcher on 2026-11-22 as built (asked in the main session: items 13, 30, 31 and 19 one by one, the other thirty together), and the push was approved. Two things not built here become a follow-up PR after the merge, as the researcher chose: a control to merge two columns from the form panel, and a test for attaching and opening a PDF from the one-study view.

The static export (asked for by the main session before the PR; the app is shipped as the export):

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| export | `dc7064e2` | `npm run build:export` in `apps/research-ui`, alone on the machine | exit 0; the route list holds `/[locale]/charting` and `/[locale]/charting/study` for en, fr and ar; `.next-export/{en,fr,ar}/charting/index.html` and `.next-export/{en,fr,ar}/charting/study/index.html` written, `lang` and `dir` right (`ar` is `rtl`) | 63 s |
| export served | `dc7064e2` | the console built with `ui_dir=.next-export` (`create_app`, a TestClient, no network): `GET /{en,fr,ar}/charting`, `…/charting/`, `…/charting/study?id=STU-abc`, `…/charting/study/?id=STU-abc` | every one 200 with its locale's page (decision item 13: the one-study view's query-parameter address is served from the static export) | |

### Part B follow-up: merging columns from the form panel; attach and open in the one-study view, tested

Branch `dev/m12a/part-b-followup`, from `origin/main` `933be3fb` (Parts A and B merged) · Lane **STANDARD** (a bounded UI behaviour change in one repository: it writes form amendments through the existing API; the engine's merge exists since Part B) · Decisions: `docs/decisions.md` "2026-11-22 — M12a Part B follow-up" items 1 to 7 (accepted as built 2026-11-22). Asked for by the researcher on 2026-11-22, when accepting Part B: the two things Part B had not built ("Not verified" of Part B). The work was built by a subagent from a brief written in the build session.

What was built:
- `apps/research-ui/components/charting-form-panel.tsx`: "Merge with…" on each column card, its chooser and the merge (decision items 1 to 5); `lib/charting-copy.ts`: five keys in en, fr and ar.
- `apps/research-ui/tests/charting-helpers.tsx`: the fake engine applies the engine's split, merge and replacement rule and its history rule (a side effect fixed a history entry only the fake gave a column whose type changed).
- Tests: `tests/charting.form-panel.test.tsx` (five new: the chooser and its keys with a merge before any value; a merge after values through the amendment prompt with the history; a three-column merge step by step; and, from review round 1, a split of unsaved split parts and merges, and a chooser whose chosen column is removed), `tests-browser/charting-study.spec.ts` ("attach a PDF from the one-study view and open it in a new tab": the file chooser, the name and size, Retrieved, "Saved", the new tab's request for the attachment route; light and dark).

Not verified: the merge from the panel against the real engine (the engine's merge is `test_charting_form_api.py::test_a_replaced_column_and_a_merge_are_recorded_and_mark_chart_again`); no browser test drives the merge chooser, and the chooser was not looked at in either theme (axe runs with it closed); what the new tab shows (headless Chromium leaves a PDF tab's address empty, so the test checks the request).

Evidence:

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner | `1ece5716` | typecheck; `vitest run tests/charting.form-panel.test.tsx tests/charting.i18n.test.ts tests/charting-study.i18n.test.ts tests/charting-study.history.test.tsx tests/charting.charting-view.test.tsx`; `playwright test tests-browser/charting-study.spec.ts` (the subagent's runs, one at a time) | clean; 32 tests, 0 failures; 18 passed (light and dark) | |
| pr | `4647bf24` (code as `1ece5716`) | `select_test_gate.py --changed origin/main --stage pr` (area research-ui); the Python files that read the UI's files (`test_browser_access`, `test_lineage_api`, `test_screening_drafts_api`, `test_screening_read_api`, `test_wheel_build_hook`, `test_select_test_gate`; junit); `npm run typecheck`; `npx vitest run`; `npm run build`; `npx playwright test`; `git diff --check origin/main...HEAD` (each heavy step alone on the machine) | 113 tests, 0 failures; clean; 93 files, 1237 tests, 0 failures; built; 692 passed, 12 skipped; clean | 24 s; 143 s; 16 s; 848 s |

No Python source changed, so the full Python suite does not apply (the selector names only the research-ui area). Playwright rewrote the usual four screenshots; they were restored.

Review round 1 (`milestone-reviewer`, on `6b527d33`): **CHANGES**, 1 P2, 1 P3, 4 P4 (lane STANDARD confirmed, its stated reason corrected), all taken, with two follow-ups it named:

| # | Finding | Repair | Test |
| :-- | :-- | :-- | :-- |
| P2-1 | After a merge the engine sends one history entry per source, but both views showed only the last | every trailing history entry that names a source column is shown, one line each, in the table and the one-study view (`chartAgainHistory`) | `charting.form-panel.test.tsx` (both "Earlier value, in Images: 1260" and "in Data split: By field" on screen, in both views) |
| P3-2 | The names behind "Made from" were lost when the panel closed | kept by the page for the page load and passed to the panel | the before-any-value merge test closes and reopens the panel |
| P4-3 | The Open test counted exactly one request | at least one, the first checked | `charting-study.spec.ts` |
| P4-4 | The record's list of the three new tests was wrong | reworded | (none) |
| P4-5 | The lane's reason used the policy's FAST wording | "a bounded UI behaviour change in one repository" | (none) |
| P4-6 | Accepted Part B item 25 still says merging is not built | the follow-up entry says it amends that sentence | (none) |
| follow-up | Splitting an unsaved merge or split part was refused by the engine | split uses the same saved sources as merge (decision item 4) | `charting.form-panel.test.tsx` (fails with the fix taken out) |
| follow-up | A merge chooser whose chosen column was removed did nothing | the choice moves to a column that exists, or the chooser closes | `charting.form-panel.test.tsx` (fails with the fix taken out) |

Evidence after round 1, on `a910b2d3` (the repairs `7309bc27` to `3ebbe064`, the docs `c5a93219`, and `origin/main` `9e4be45f` merged in, no conflict): the Python files that read the UI's files 113 tests, 0 failures; typecheck clean; `vitest run` 94 files, 1257 tests, 0 failures (133 s); build ok; `playwright test` 706 passed, 14 skipped (858 s); `git diff --check origin/main...HEAD` clean; each heavy step alone on the machine. The usual four screenshots were restored.

Review round 2 (`milestone-reviewer`, on `7765cb09`): **APPROVE**. In its words: "All six round-1 findings and both follow-ups are repaired, and I found nothing new." It reran the form-panel and history vitest files (17 tests), all passing, and read the recorded gate. One P4, repaired in the closing commit: the list of new tests above now counts five.

**Part B follow-up: READY FOR PR.** Branch `dev/m12a/part-b-followup`; it carries `origin/main` `9e4be45f`. Decision items 1 to 7 were accepted by the researcher on 2026-11-22 as built (asked together in the main session; item 4 says how the engine records a split of an unsaved merge; the entry amends accepted Part B item 25's last sentence), and the push was approved.

**Part B follow-up: merged** on 2026-11-22 (PR 282, merge commit `4962c9eb`, 12 of 12 checks, head `db6962b9`).

### Part F: open-access fetching (the engine and the screens)

Branch `dev/m12a/part-f-fetch`, cut from Part K's branch (`d1f48bd9`) with `origin/main` `933be3fb` merged in; Part K's pushed head (PR 283, `76b47c15`) merged in on 2026-11-22 (`f108b97a`; the two conflicts were documents Part F had not touched, Part K's versions kept) · Lane **RELEASE** (new routes, a new persisted record and journal rows, refusal codes, outgoing requests, a change to the arXiv provider's parsing) · Spec: `docs/ux/phase3-extraction/final/03-fetch-states.md`, FINAL on 2026-11-22 (questions 1 to 10 answered by the researcher, each as recommended; the fifth refusal code `FETCH_FILE_WAITING` approved with question 6) · Decisions: `docs/decisions.md` "2026-11-22 — M12a Part F" items 1 to 68 (PROPOSED). The screens were built by a subagent from a brief written in the build session; the engine, its two later repairs and the documents in the build session.

What was built:
- The kit (`src/scholar_pdf/downloader.py`, `open_copies.py`, `manifest.py`): a body limit, a redirect cap, a pacer, the caller's copies and outcome rows, each with a default that leaves the commands unchanged (item 20); an arXiv copy labelled with its version (item 11).
- The arXiv provider (`src/scholar_search/providers/arxiv.py`): an old-style id keeps its archive (DoD F7; item 22, asked on its own), and a look-up by id list.
- The engine (`src/scholar_harness/charting/fetch.py`, new; `events.py`, `table.py`): the plan, the run (one per workspace, its lock, cancel, progress, the manifest `charting/fetch_manifest.jsonl`), "Fetched, to confirm" on the rows and in the counts, confirm and discard as events with their undo, the guard `FETCH_FILE_WAITING`, the journal rows `CHARTING_FETCH_STARTED` and `CHARTING_FETCH_FINISHED`; after the screens' build, the run names failed checks and failed look-ups, and the rows no longer kept keep their fetch state (items 23 and 24).
- The routes (`console/api/charting.py`), the refusals (`console/refusals.py`, the contract's §7 rows, `docs/architecture/screening-api-contract.md`), the browser allow-lists (`console/browser.py`, `app/api/console/[...path]/route.ts`, which also passes the waiting PDF through as bytes).
- The screens (`apps/research-ui/components/charting-fetch.tsx` and `lib/charting-fetch.ts`, new; `charting-page.tsx`, `charting-study.tsx`, `lib/charting-api.ts`, `charting-copy.ts` in en, fr and ar, `charting-logic.ts`); the hints X-F1 to X-F3 in `docs/ux/shared/final/03-guidance.md`; spec 01 FINAL and the Part F lines owed to specs 01 and 02.

| DoD | Test(s) |
| :-- | :-- |
| F1: no e-mail, no socket; no OpenAlex key, not asked and said | `test_charting_fetch_api.py::test_without_the_contact_email_the_plan_and_the_start_are_refused_before_any_request`, `::test_without_the_openalex_key_openalex_is_not_asked_and_the_plan_says_so`; `charting.fetch-plan.test.tsx` |
| F2: a manifest row for every record reached | `::test_every_record_reached_has_a_manifest_row_and_no_file_is_without_one`, `::test_a_failed_record_has_its_row_too`, `::test_a_cancel_stops_between_records_and_the_records_reached_keep_their_rows`; `test_part_f_kit.py::test_no_copy_from_the_caller_writes_a_row_and_sends_nothing` |
| F3: the checks on a local stub server | `::test_a_body_over_the_limit_is_cut_and_fails`, `::test_redirects_are_recorded_and_a_sixth_is_refused`, `::test_html_named_pdf_fails_its_checks`, `::test_a_429_that_asks_too_long_ends_as_try_later`, `::test_the_same_bytes_for_two_records_are_warned_on_both_rows`; `test_part_f_kit.py` (body limit declared and streamed, five redirects, the sixth, the pacer, a page that is not a PDF); 403, 404 and 410 asked once and a 429 within the cap waited out: Part K's `test_part_k_retries.py::test_a_definitive_answer_is_asked_once`, `::test_a_429_with_a_short_retry_after_is_waited_out_once` |
| F4: the kit as a library; no proxy, no guessed address | `::test_the_run_calls_the_kits_downloader_with_no_proxy_and_asks_only_listed_addresses`, `::test_the_default_session_trusts_no_proxy_from_the_environment` |
| F5: waiting, not counted; confirm, discard, undo, refusals | `::test_a_fetched_file_waits_and_the_prisma_counts_do_not_move`, `::test_confirm_attaches_the_file_with_origin_fetched_and_sets_retrieved_and_undo_takes_it_back`, `::test_discard_needs_one_reason_keeps_the_file_and_can_be_undone`, `::test_confirm_or_discard_with_nothing_waiting_is_fetch_not_pending`, `::test_a_decision_status_or_attachment_on_a_waiting_row_asks_for_the_confirmation_first`, `::test_a_record_no_longer_kept_keeps_its_waiting_file_on_the_row_and_cannot_be_confirmed`; `charting.fetch-confirm`, `-discard`, `-decide-guard`, `-badge` |
| F6: one run, cancel, skips, journal rows without the key | `::test_one_run_per_workspace`, `::test_a_second_run_skips_records_with_a_waiting_or_confirmed_file`, `::test_a_discarded_file_is_not_offered_again_and_the_record_is_left_out_unless_selected`, `::test_the_journal_rows_carry_the_counts_and_never_the_key`, `::test_a_run_this_console_did_not_finish_reads_as_interrupted_without_a_write`; `charting.fetch-run.test.tsx` |
| F7: arXiv by id, paced, labelled; a journal DOI goes to the services; old-style ids | `::test_an_arxiv_only_record_is_asked_of_arxiv_and_fetched_from_the_link_arxiv_gives`, `::test_a_journal_doi_in_arxivs_answer_goes_to_the_services_and_the_best_copy_wins`, `::test_arxiv_requests_share_one_budget_of_one_every_three_seconds`; `test_arxiv_ids.py` (seven test functions, 21 cases, a hand-made answer); `test_part_f_kit.py::test_a_published_version_listed_for_the_journal_doi_wins_over_the_arxiv_preprint`, `::test_the_arxiv_preprint_is_taken_when_the_services_list_no_copy` |
| F8: the screens, en/fr/ar, keyboard, axe light and dark | the fourteen `apps/research-ui/tests/charting.fetch-*` files; `tests-browser/charting-fetch.spec.ts` (seven tests, each in light and dark: plan and run with Cancel; filter, open, confirm and discard within four keypresses per row; a failed row and its tried panel; `I` on a waiting row; 390 px read-only; Arabic at 390 px; axe) |
| F9: a live run on the researcher's review | not done: the researcher's, after the merge |

Not verified:
- No live request was sent (no Unpaywall, OpenAlex, arXiv or publisher). Every run in the tests goes to fakes and a local stub server; the arXiv answer is hand-made, not recorded. DoD F9 is the first live run.
- The screens were not driven against a real console: vitest uses the fake engine in `tests/charting-helpers.tsx` and Playwright a fake at the network boundary; the fake imitates the engine's rules, which the Python tests check on the real engine.
- The French and Arabic words of the new keys were written in the build and not read by a speaker (item 51).
- PubMed Central's own route stays a follow-up after Part F (Part K item 17, the researcher's answer of 2026-11-22).
- The letter keys need the Latin keyboard layout (Part A's standing limit).

Review round 1 (`milestone-reviewer`, on `6bbe0c58`, the delta `76b47c15...HEAD`): **CHANGES**, no P1. In its words: "No paywall bypass, no proxy on the PDF session […], and no URL the app builds itself." Eleven findings; the gate that was running on `6bbe0c58` was stopped and is run again on the repairs.

| # | Finding | Repair | Test |
| :-- | :-- | :-- | :-- |
| P2-1 | The manifest named fetched files by absolute path (home path in a tracked file; a moved workspace could not serve or confirm them) | relative to the workspace (`manifest_file_root`); item 6 amended | `test_charting_fetch_api.py::test_the_manifest_names_files_relative_to_the_workspace_and_a_moved_workspace_still_serves_them` |
| P2-2 | A protocol replace did not stop or wait for a running look-up | genesis with `replace` refused `WORKSPACE_JOB_ACTIVE` while one runs; item 59 | `::test_a_protocol_replace_waits_for_a_running_look_up`; `test_inception_api.py::test_a_replacement_waits_for_a_running_look_up_of_open_access_copies` |
| P2-3 | A file could arrive on a row the researcher changed during the run (counts over the kept total, status keys refused) | the run skips such a row; a file that still arrives does not wait on it; item 60 | `::test_a_row_given_retrieved_during_the_run_is_not_asked_and_counts_add_up`, `::test_a_file_fetched_for_a_row_changed_while_it_downloaded_does_not_wait_on_it` |
| P2-4 | Item 22 left out that the arXiv id feeds the REC- and STU- ids, the verifier, the chasing keys and the retraction look-up | item 22 amended (documents only) | (none) |
| P3-5 | The Full text CSV said "To get" for a waiting row | "Fetched, to confirm"; item 61 | `::test_the_full_text_export_says_fetched_to_confirm_for_a_waiting_row` |
| P3-6 | The start's answer could read a short run as interrupted | not for the start's own answer; item 62 | `::test_the_start_answer_never_reads_a_short_run_as_interrupted` |
| P3-7 | Open was shown on a record no longer kept, whose file the route refused | the file is served; item 63 | `::test_a_record_no_longer_kept_keeps_its_waiting_file_on_the_row_and_cannot_be_confirmed` (extended) |
| P4-8 | "Try later" on a row whose file came from the other service | only for a record left without a file; item 64 | `::test_try_later_is_said_only_for_a_record_left_without_a_file` |
| P4-9 | The record's test count and the F3 row's missing retry tests | corrected above | (none) |
| P4-10 | A finish row could be written with no start row | not written then; item 65 | `::test_no_finish_row_when_the_start_row_could_not_be_written` |
| P4-11 | The UI tests' fake undid a confirm's attachment and status even after a later change | the fake follows the engine's rule (only while they still hold) | the charting vitest files (no test drives an undo after a later change) |

The new tests were written after the repairs and not run against the code before them; the findings were confirmed by reading (the reviewer ran `_file_entry` for finding 1). Follow-ups the reviewer named, not repaired here: two consoles on one workspace can both take over a stale lock (a read, remove and create race in `_acquire`); a dead console's process number reused by Windows keeps its lock "alive" (the pattern of `agent_runs`); the arXiv provider object made for the look-up opens an HTTP client it never uses or closes; the pacer reports "waiting" for an arXiv request the budget lets go at once.

Review round 2 (`milestone-reviewer`, on `2c0d021d`: the repairs `41c60093`, `a1be70c0` and `origin/main` `76c445ef` merged): **CHANGES**. In its words: "All eleven round-1 findings are repaired, and each new test would fail on the code at `6bbe0c58`." It found that the merge lost nothing from `origin/main`. The gate that was running on `2c0d021d` was stopped and is run again on the repairs.

| # | Finding | Repair | Test |
| :-- | :-- | :-- | :-- |
| P3-1 | Item 60 said a file fetched for a changed row never waits on it; the rule reads the row as it is now, so the file waits again once the row is To get, Requested or Not retrieved with no file | the behaviour kept and item 60 says it (the researcher's choice; hiding the file for good is the alternative) | `test_charting_fetch_api.py::test_a_file_fetched_for_a_row_changed_while_it_downloaded_does_not_wait_on_it` (extended: the file waits again, `FETCH_FILE_WAITING`) |
| P4-2 | The new per-record read of the events sat outside the record's `try`: a half-written line could fail the whole run | a failed read asks the record as planned; item 66 | `::test_a_bad_read_of_the_events_during_a_run_never_fails_it` |
| P4-3 | Rows changed during a run were counted only in the run file | the finish row's `changed_during_run` and a summary line; item 67 | `::test_the_finish_row_counts_the_rows_changed_during_the_run`; `charting.fetch-summary.test.tsx` ("says how many rows were left…") |
| P4-4 | The UI fake still showed the file after an undo of a confirm when the researcher's attachment held | the fake applies the engine's row rule | the charting vitest files |

Follow-ups the reviewer named, not repaired here: the moved-workspace test's first assertion proves nothing on Windows (JSON escapes the backslashes; the `pdfs/fetched/DOC-` assertion is the one that catches the old behaviour); `manifest_file_root` has no test in the kit's own tests; arXiv-only records go to arXiv's batch look-up at the start, so a row changed after it was already sent there; the replace's running-job check has the search jobs' check-then-act race.

Review round 3 (`milestone-reviewer`, on `f7136455`: the repairs `74a93333` and the docs `f7136455`): **APPROVE**. In its words: "All four round-2 findings are repaired… There are no new findings."

Evidence (the PR gate on `f7136455`, final code `74a93333`; each heavy step alone on the machine, the script waiting until no other test process ran):

| Check | Result |
| :-- | :-- |
| `pytest -q -n 4` (4 workers) with `--junitxml` | 6533 tests, 0 failures, 0 errors, 15 skipped (943 s) |
| `sync_skills_bundle.py --check`; `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9` | OK; clean; clean |
| `generate_contract_baseline.py --check`; protocol schema check | current; in sync |
| `npm run typecheck`; `npm run build` | clean; ok |
| `vitest run` | 108 files, 1342 tests: 2 failures in that run (`inception-explore`, `inception-workbench`, their first `findBy` past 1 s; item 68), 1 in a rerun alone; after `25d7956c` two full runs 1342 passed, 0 failures; typecheck clean |
| `playwright test` | 720 passed, 16 skipped (17.6 min) |
| `git diff --check origin/main...HEAD` | clean |

The four screenshots Playwright rewrites were restored. Later commits: `4b89c798` merges `origin/main` `46ebe639` (PRs 285 and 286, documents only; the conflict in this record resolved with both sides kept); `25d7956c` is the test repair of item 68 (two test files, no product code), checked by the two full vitest runs above; the rest are documents.

**Part F: READY FOR PR.** Branch `dev/m12a/part-f-fetch`; it carries Part K's PR-283 head `76b47c15` and `origin/main` `a34904dd` (merged in by the main session; one document conflict, both sides kept). Decision items 1 to 68 were accepted by the researcher on 2026-11-22 as built, and the push and the merge were approved; item 51 (the French and Arabic words) is still to be read by the researcher. DoD F9 (a live run on the researcher's review) is the researcher's, after the merge.

### Part C: export and reporting (the engine and the screens)

Branch `dev/m12a/part-c-export`, cut from Part F's head `baf9c26f` on the main session's word (2026-11-22, the researcher's answer "After Part F"); Part F's pushed head (PR 290, `3b11fd70`, with `origin/main` `a34904dd`) merged in (`51fc43f0`, no conflict) · Lane **RELEASE** (a new public route, new published files `charting/prisma_fulltext.json` and `charting/last_export.json`, a new base dependency) · Spec: `docs/ux/phase3-extraction/final/04-export-and-methods.md`, FINAL on 2026-11-22 (questions 1 to 4 answered by the researcher, each as recommended; spec 01 and record (h) now say six sheets) · Decisions: `docs/decisions.md` "2026-11-22 — M12a Part C" items 1 to 29 (PROPOSED). The engine and the spec's review were done in the build session; the spec was drafted by `ux-spec-writer` and the screens built by a subagent from a brief written in the build session.

What was built:
- The engine (`src/scholar_harness/charting/report.py`, new; `table.py`): the spreadsheet (six sheets, every text cell written as text), the PRISMA full-text counts per round, per arm and in total with the open counts apart, `charting/prisma_fulltext.json` and `charting/last_export.json` written at every export, the methods block with every number computed, the reviewer sentence from the events, the amendments in words and the files it is computed from; the open and required-open cell counts on the table; the Full text CSV's file origin, source, version and licence (with Part F).
- The routes (`console/api/charting.py`): `GET /charting/export?format=xlsx` beside the CSVs, `GET /charting/methods` (a pure read). No new refusal code, no new POST route, no proxy change (the export already passes as bytes).
- `openpyxl>=3.1.5` in the base install (answer 8; the lock already held 3.1.5 through Docling and changed by two lines, resolved offline).
- The screens (`apps/research-ui/app/[locale]/charting/report/page.tsx`, `components/charting-report.tsx` and `components/charting-export-lines.tsx`, new; `charting-page.tsx`, `screening-export.tsx`, `lib/charting-api.ts`, `lib/charting-copy.ts` in en, fr and ar): the "Export and methods" page (downloads, the help line of question 3, the last-export and open-cell lines, the counts table, "Still open", the methods paragraph with Copy, Notes, Not stated and Details), the spreadsheet in the table's Export menu with the persistent last-export lines, and the links from the table and from screening's export page.

| DoD | Test(s) |
| :-- | :-- |
| 15: CSV and xlsx of (h); the xlsx read back with `openpyxl`, every sheet checked; the CSV with its BOM | `tests/console/test_charting_export_api.py::test_the_spreadsheet_has_every_sheet_and_reads_back`, `::test_every_text_cell_is_text_never_a_formula`, `::test_the_full_text_csv_says_where_the_file_came_from`, `::test_a_format_other_than_csv_or_xlsx_is_refused_and_writes_nothing`; Part A's `test_charting_api.py::test_the_full_text_csv_has_a_bom_crlf_and_is_journaled_with_its_hash` |
| 16: PRISMA full-text counts per round and in total; `prisma_fulltext.json`; screening's `prisma_report.json` unchanged | `::test_the_prisma_full_text_counts_are_written_and_screenings_report_is_unchanged`, `::test_a_waiting_or_open_report_is_counted_apart_so_the_counts_add_up`; `charting.report.counts.test.tsx` |
| 17: the methods block, every number computed, the reviewer sentence from the events, amendments listed | `::test_the_methods_block_states_every_number_from_the_events` (exact sentences, notes, sources, a pure read), `::test_the_open_access_sentence_names_the_services_asked_and_the_discards`, `::test_amendments_are_listed_in_words`; `charting.report.methods.test.tsx` |
| 18: every export writes `CHARTING_EXPORTED` with the file's SHA-256; the screen shows the export time | `::test_every_export_is_journaled_with_its_hash_and_the_table_shows_the_last`, `::test_the_table_counts_open_and_required_cells`; `charting.report.export-line.test.tsx`, `charting.report.export-menu.test.tsx` |
| The page's states, words in en/fr/ar, the phone, axe light and dark | `charting.report.states.test.tsx`, `charting.report.i18n.test.tsx`, `charting.report.mobile.test.tsx`; `tests-browser/charting-report.spec.ts` |
| 19: live, once, by the researcher (five studies charted in the pilot, one amendment, an export opened in their spreadsheet program) | not done: the researcher's, after the merge |

Not verified:
- How the spreadsheet opens in Excel and LibreOffice: the tests read it back with `openpyxl` only (record, "What cannot be verified").
- The French and Arabic words of the new keys were written in the build and not read by a speaker.
- The screens ran against the fake engine of `tests/charting-helpers.tsx` and Playwright's fake at the network boundary, not a real console; the Python tests check the real engine.
- No live request (none is made by Part C).

Found while building, not repaired here (outside Part C):
- CI on PR 289 (documents only, on `main`) timed out on `inception-workbench.test.tsx` "a refused cost read says why…" (its `waitFor` near line 225, the default 1 s); Part F's item 68 gave 5 s to the first wait of that file only, so this wait is not covered. Same cause under load. Follow-up: that wait too, or item 68's alternative (a longer default in `tests/setup.ts`).
- CI failed twice on `tests-browser/charting-study.spec.ts:222` (the first field never focused after opening a study or moving). Read, not reproduced: in `components/charting-study.tsx` the focus effect clears its intent before it knows an enabled field exists, so one render with the fields disabled (`offline`) or not mounted spends it and nothing retries; and a focus deferred after a save is not tied to the study it was issued for, while the fields keep their elements across a move. A repair belongs to Part B's code: keep the intent until a field is focused, and drop a deferred focus when the study changed.

Review round 1 (`milestone-reviewer`, on `68731897`, the delta `3b11fd70...HEAD`): **CHANGES**, no P1; the contract baseline current. In its words, the spreadsheet writes text "as `s`, never as a formula", and no home path reaches any file. Six findings; repaired in `4212add6`:

| # | Finding | Repair | Test |
| :-- | :-- | :-- | :-- |
| P2-1 | A report not retrieved and decided was counted under both "not retrieved" and "assessed", so the boxes did not add up | each report in one box; the decision from the abstract counted apart, its own sentence and sheet lines; item 5 amended | `test_charting_export_api.py::test_a_waiting_or_open_report_is_counted_apart_so_the_counts_add_up` (extended: the identity with a decided Not retrieved row), `::test_the_prisma_full_text_counts_are_written_and_screenings_report_is_unchanged`, `::test_the_methods_block_states_every_number_from_the_events`, `::test_the_spreadsheet_has_every_sheet_and_reads_back` |
| P3-2 | `GET /charting/methods` seeded the form and the kept history on a table never opened | a pure read (`table(seed=False)`); item 27 | `::test_the_methods_block_on_a_table_never_opened_writes_nothing` |
| P3-3 | "Still open" said a waiting copy is awaiting retrieval; on a Not retrieved row it is not | the note's words, en, fr and ar; item 29 | `::test_a_waiting_or_open_report_is_counted_apart_so_the_counts_add_up` (a waiting copy on a Not retrieved row); `charting.report.counts.test.tsx` |
| P3-4 | No PR-stage gate evidence | the gate runs on the final executable commit (below) | (none) |
| P4-5 | "1 rows", "1 cells", "1 required cells" | the shared plural table; item 28 | `charting.report.export-line.test.tsx` ("says one row and one cell in the singular") |
| P4-6 | "checked by the reviewer" fixed; "0 were not retrieved"; the open-cell note | from the confirm events; "none is recorded as not retrieved"; "; 1 in a required column"; item 7 amended | `::test_the_methods_block_on_a_table_never_opened_writes_nothing`, `::test_the_methods_block_states_every_number_from_the_events` |

Follow-ups the reviewer named, not repaired here: Details shows no protocol fingerprint (item 26); spec 04's "Live-only" line names an `isLiveOnlyPath` that `app-shell.tsx` does not have; `methods()` reads the events files twice and the whole journal on every call.

Review round 2 (`milestone-reviewer`, on `9756fad7`: the repairs `4212add6` and `9756fad7`): **APPROVE**. In its words: "New problems from the repairs: none found." Two of its P4 follow-ups were done before the gate (`a1ff08b5`: the TypeScript type names the three decided-from-the-abstract counts; the "Still open" note's words are asserted); the others stay follow-ups: the "a reviewer" form of the open-access sentence has no test; the paragraph's abstract sentence gives no exclusion reasons; and those of round 1.

Evidence (the PR gate on `f9730e06`: `a1ff08b5`, the last product code, with `origin/main` `21a4e6a3` merged, documents only; each heavy step alone on the machine, the script waiting until no other test process ran):

| Check | Result |
| :-- | :-- |
| `pytest -q -n 4` (4 workers) with `--junitxml` | 6555 tests, 0 failures, 0 errors, 15 skipped (629 s) |
| `sync_skills_bundle.py --check`; `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9` | OK; clean; clean |
| `generate_contract_baseline.py --check`; protocol schema check | current; in sync |
| `npm run typecheck`; `npm run build` | clean; ok |
| `vitest run` on `f9730e06` | 115 files, 1402 tests, 2 failures: `plural.test.tsx` (Part C's: the plural table's new charting keys were not in the test's list of catalogs; repaired in `01a8e5df`) and `inception-workbench.test.tsx` "a rename keeps the row" (a `waitFor` past the default 1 s; it passed alone twice) |
| `vitest run` on `01a8e5df`, twice | first: 1 failure, `discovery-proposals.test.tsx` "names the assistant and its model…" (a first-render `findBy` past 1 s; 6 of 7 runs of the file alone passed); second: 115 files, 1402 tests, 0 failures |
| `playwright test` on `f9730e06` | 732 passed, 16 skipped (15.7 min) |
| `git diff --check origin/main...HEAD` | clean |

The failures outside Part C's files are the timing class of Part F's item 68: a wait with the default 1 s that runs out under load, in a different file each run (inception-workbench, discovery-proposals; PR 289's CI another wait of inception-workbench). Part C adds eight test files, so the suite is longer. A follow-up for the whole suite: item 68's alternative, a longer default for `findBy` and `waitFor` in `tests/setup.ts`. Playwright rewrote six screenshots: the two of screening's export page (en, ar) show the new "Export and methods" link and are kept (`01a8e5df`); the usual four were restored. Later commits are documents only.

**Part C: READY FOR PR** (not pushed). Branch `dev/m12a/part-c-export`; it carries `origin/main` `21a4e6a3` (Part F, PR 290, merged). Decision items 1 to 29 are PROPOSED; DoD 19 (the live run on the researcher's review) is the researcher's, after the merge.
