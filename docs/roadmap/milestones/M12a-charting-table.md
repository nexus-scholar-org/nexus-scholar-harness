# M12a Charting table

Branch: `dev/m12a/charting-table-spec` (from `origin/main` at `1f218054`) · Lane: declared per part (A, B, K, F and C, each **RELEASE**) · Status: **SPECIFICATION; questions 1 to 10 and the eight follow-up questions (1, F1 to F7) answered by the researcher on 2026-11-21** (question 6 changed: open-access copies are fetched, in a part of their own; question 9 changed: the agent-cells specification is written now, [`M12c-agent-cells.md`](M12c-agent-cells.md); F1 changed: the whole PDF kit is to become production, which adds Part K; F2 changed: B before F; F7 changed: records without a DOI are looked up by arXiv id). Five new questions on what "the whole kit" covers (G1 to G5) wait for the researcher (the page's last table). **Nothing built; the start of the build is the researcher's to approve separately.** (Decision "2026-11-20 — The order of work after the acceptance run", item 5: a specification is written and read before anything is built.) · Fifth in the agreed order (plan §6, "After the acceptance run", row 5)

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
- PDF-07's harness half (stage 5 of the parked `run` looking for slug and DOI names, `pipeline/extraction.py:79-95`) stays open until reading is decided (question G1): Part F does not go through `run` or stage 5. It calls the kit's repaired downloader as a library (Part K), not the `scholar-pdf download` command. The manifest and the confirmed attachment are the mapping M12b-read will use. Part F does not write the legacy `literature/pdf_manifest.json` that `GET /harvest/corpus` reads and nothing writes (a follow-up).

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

**What is never done.** No paywall bypass of any kind: no shadow library, no login or cookies, no browser automation, no scraping of landing pages, no guessed publisher URLs (the kit's `enable_publisher_direct_patterns`, on by default in `scholar_pdf/config.py:30`, is not used; what the production kit does with it is question G3). No institutional proxy or gateway in Part F, neither used nor offered (F5, "Leave it out", answered knowing the kit has proxy code, `downloader.py:53-89, :365-379`; what the production kit does with it is question G4). No fetch in the background or on a schedule: every run is started by the researcher, with its count and the services named. Fetched files stay in `pdfs/`, which is not in git, and are never exported.

**Reused and not reused.** Changed by F1 ("Un-park the whole kit"): Part F no longer builds a fetch module of its own beside a parked kit. It calls the kit's downloader as a library, after Part K has made it production (honest user agent, e-mail required, the OpenAlex key, no guessed URLs, no proxy, 4xx not retried, the manifest, the access route recorded). The app adds only what is the app's: the run (one per workspace, cancel, progress), the manifest path, the "Fetched, to confirm" status, confirm and discard, and the screen.

**Refusals.** Reused: `MAILTO_NOT_SET`, `SCREENING_NOT_PUBLISHED`, `RECORD_NOT_KEPT`, `BODY_INVALID`. New: `FETCH_ALREADY_ACTIVE` (one run per workspace), `FETCH_NOT_PENDING` (confirm or discard of a file not waiting), `DISCARD_REASON_REQUIRED`.

**Screen.** The Full text view gains the `L` action and its confirmation, the "Fetched, to confirm" status with source, version and licence, `C` and `D`, the fetch progress line, and a "To confirm" filter. Screen 01 points here; its fetch states are drafted in screen 01 before Part F is built.

**Lane and size.** **RELEASE**: outgoing provider calls, new routes and refusal codes, a new persisted manifest path. Size **M** (the kit's repairs moved to Part K; the arXiv look-up adds about S, so M at its upper end).

**Where it sits.** F2, "B before F" (not as recommended): **A, B, F, C**. F needs A (the rows and their statuses), B's finished table screen (they share it, so they are built one after the other) and Part K (the kit it calls). Re-checked for B before F:
- B must not assume the fifth status: its filters and status chips list A's four; F adds `Fetched, to confirm` and the "To confirm" filter.
- A row whose file waits for confirmation can be charted, as any row without a full text can (answer 7); confirming or discarding never touches its cells.
- The keys `L`, `C` and `D` are still free after B: screens 01 and 02 as drafted use `A`, `E`, `F`, `G`, `I`, `J`/`K`, `N`, `O`, `P`, `Q`, `R`, `X`, `Z`. B's build must keep them free (a note in screen 01).
- C still follows F, so the export carries each file's origin, version and licence. If F slips after C (risk 7), C ships with "attached" as the only origin and F adds its columns.

### (d3) Part K: the PDF kit's acquisition becomes production (F1, "Un-park the whole kit"; the details below are PROPOSED)

**What was asked.** The researcher chose "Un-park the whole kit" against the recommendation; the option read "The kit's downloader and commands become production too. Larger review and more risk; not sized." This section says what "production" requires for the kit, sizes it, and lists where the choice meets decisions already taken, as questions (G1 to G5), not resolved here.

**What the kit is today** (`docs/assessment/kit-pdf.md`, 2026-11-03; the code at `1f218054` has not changed since, `git log -- src/scholar_pdf` shows only the merge and the parked notices). 13,528 lines in two unrelated stacks (PDF-01):
- **The legacy stack:** `downloader.py`, `validator.py`, `publisher_patterns.py`, `extract.py`, and the commands `download`, `ingest`, `extract` (`cli.py:301-617`). This is what the parked pipeline uses (`console/runtimes/actions.py:84,91`; `console/api/pipelines.py:221-352`; stage 5 imports `PyMuPDFEngine`, `pipeline/extraction.py:50`).
- **The contract-bound stack (WP01-E1 acquisition, E2 extraction):** `acquisition.py` (3,751 lines), `extraction.py` (3,108), their models, and the commands `acquire`, `extract-run`. Careful work (content-addressed storage, lineage checks, commit intents, typed outcomes), and called by nothing in the harness. E1 reads accepted Contract v1 parents (the corpus snapshot and the screening decisions) and refuses any study that is not `INCLUDE` (`STUDY_NOT_INCLUDED`, `acquisition.py:1154-1158`), so it cannot fetch the "Unclear → full text" rows M12a keeps (answer 4), which are outside the contract (answer 1). Its manifest is a kit sidecar, not a Contract v1 type (`docs/architecture/wp01/evidence-boundaries.md:57-59`).
- **MCP:** `nexus_pdf_acquire` and `nexus_pdf_extraction` are declared unsupported and return a typed refusal (`scholar_agent/server.py:805-863`); `nexus_extract_pdf` parses a PDF by path with PyMuPDF and is non-authoritative.
- **Tests today** (`tests/kits/pdf/`, counted, not run for this record): 170 test functions; the 2026-11-03 run collected 203, 195 passed, 8 skipped (7 need a Windows symlink privilege). By file: acquisition 19 and 51 (atomicity), extraction 48 and 6, publisher patterns 19 (they assert the guessed URLs), validator 12, downloader 9 (two cassettes, an OA lookup found and not found), CLI 5, legacy extract 1 (it asserts that a broken PDF "succeeds", PDF-08). No test drives the proxy, a real Docling or GROBID conversion, or a live fetch; no live run of `download` is recorded anywhere.

**What "production" requires before the acquisition side can be called that.** Each item is a change with a test; the reference is the finding or the line.
1. **A real contact e-mail, required.** The default `student@university.edu` (`config.py:8`) goes; the kit reads `SCHOLAR_MAILTO` and refuses without it (exit code non-zero; `MAILTO_NOT_SET` through the app).
2. **The app's own name, not a browser's.** The Chrome user agent (`downloader.py:200-201`) becomes `nexus-scholar/<version> (mailto:…)`; E1's transport already names itself, with a stale `scholar-pdf-kit/0.1` (`acquisition.py:175`).
3. **No guessed publisher URLs.** `publisher_patterns.py` was added "for Cloudflare/WAF bypass" (commit `39123d67`; module docstring), is on by default (`config.py:30`), and its IEEE rule addresses a different paper (PDF-11). It cannot be production beside "no guessed URLs" (question G3).
4. **OpenAlex with its key.** The kit's lookup sends only `mailto` (`downloader.py:239-249`), which OpenAlex no longer reads; it must send `SCHOLAR_OPENALEX_KEY`, skip OpenAlex without it, and treat 409 as "budget spent".
5. **No institutional proxy** in what becomes production (F5; question G4). The proxy is wired into the legacy downloader (`downloader.py:53-89, :365-379`) and E1 (`acquisition.py:1899`, `rewrite_via_proxy`).
6. **Definitive answers not retried** (PDF-06: a 404 costs about 6 s per candidate today).
7. **Open-access status from the evidence** (PDF-12): `is_oa: false` or `oa_status: closed` overrides a `pdf_url`, and the candidate that produced the bytes is recorded.
8. **The manifest** (PDF-07, the kit's half): study and DOI to file, SHA-256, source URL after redirects, version, licence, status, each check, at a path the caller gives; `download` writes one next to its output when none is given.
9. **The paper's identity looked for** (PDF-22): the DOI and title words on the first pages, recorded; "not checked" on the base install, which does not parse PDFs.
10. **Honest commands** (PDF-15: `ingest` and `download --input <missing>` exit 0 on failure); the size floor reported as a size floor (PDF-17); no `'None'` year, de-duplicated and atomic exports (PDF-18); the no-op `--smart-names`, `_safe_filename` and `models.py` removed (PDF-05).
11. **Portable writes** (PDF-03): a copy fallback where hard links fail (exFAT or FAT USB drives, some network shares), with a test.
12. **The notices and docs.** The "PARKED" help prefix (`cli.py:38`) comes off the production commands only; `docs/kits_surface_matrix.md`, the user guide, the kit skill (`.agents/skills/scholar-pdf-kit/SKILL.md`) and the kit README's drift (assessment §5) are corrected.
13. **Tests replaced, not only added:** the publisher-pattern tests go with the patterns; the downloader gains cassette and stub-server tests for items 1 to 11; the network guard covers them.

**What stays outside Part K, as questions.**
- **Reading PDFs** (`extract`, `extract-run`, `nexus_extract_pdf`, stage 5; PDF-08, -09, -10, -13, -14, -16, -19, -23) is "the whole kit" too, but it is what M12b-read is for, and it is large (L on its own). Question G1.
- **E1 `acquire`** cannot serve M12a's rows (Include and Unclear, outside the contract). Making it production means wiring it to something or keeping it as a library, plus PDF-20, -21, -02, -04. Question G2.
- **The console's legacy pipeline templates** (`download`, then `extract`, then stages 5 to 9; `actions.py:84,91`, `pipelines.py:221-352`) feed the parked matrix and synthesis. Question G5.

**How F1 and F5 fit together.** The kit becomes production; the proxy does not. Part F neither uses nor offers it (F5). In the kit, a proxy setting is refused by the production commands with a message that names the decision, rather than silently ignored, and its code stays as parked code until a decision of its own (recommended in G4). Any later use would record the access route as "institutional", never as open access, and never export those files.

**Conflicts with what is already accepted (listed, not resolved).**
- Answer 3 (accepted) keeps "fetching and reading PDFs (`scholar_pdf`)" parked; F1 un-parks the whole kit. The fetching side is settled by F1; the reading side is question G1.
- Plan §8 lists full text (`scholar_pdf`, PDF-07/08) as parked in the docs, the CLI help and MCP; the main session changes §8 once G1 to G5 are answered.
- "No paywall bypass" (decision items 7 and 19): the kit's publisher patterns were written to get past bot protection (G3), and the proxy is institutional access (G4). Neither can be production under that rule as it stands.

**Lane and size.** **RELEASE**: outgoing calls, a kit's public commands and behaviour change, a parked surface becomes production. Size **L**: items 1 to 13 for the downloader and `download`/`ingest` are one RELEASE PR at the upper end of L, about Part A's size. It does not fit one PR if G1 or G2 brings in reading or E1: reading is another L (best kept as M12b-read), E1 another M.

**Where it sits.** Part K touches `src/scholar_pdf/`, its tests and its docs, not the table screen, so it can be built at the same time as B (different files) and must be merged before F. Order: **A, then B with K beside it, then F, then C.**

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
What must exist first, in this order: (1) full text as text with page anchors (the PDF kit's parse, PDF-07 and PDF-08 fixed, a text-quality flag, X2); (2) a quote check over the full text, reusing screening's `quote_in_source` rule (the quote equals the text at its offsets), so a proposal without a checkable quote cannot be adopted; (3) the M8b highlighter on that text, to show the quote; (4) a measurement on the researcher's own charted rows (agreement per column, as M9a did for screening) and a spend approval; (5) the decision on Contract v1 types for cells (answer 1: a contract decision comes first; M12c question 1); (6) an adoption that records `AGENT_ADOPTED`-like provenance, never `HUMAN`. The parked `scholar_rag` matrix extractor is not a starting point (X3, X4).
- *For now:* the researcher's columns are judgement-heavy (what counts as "simulating" a camera change); an agent would save time only on cameras and splits. *Against now:* none of (1) to (4) exists, and a wrong cell in a scoping review's table is a wrong finding.

### (h) Export, PRISMA counts and the methods text

**Decided 2026-11-21 (answers 8 and 10, as recommended; the plain CSV of the Charting view comes with B):** With Part F the Full text sheet also carries each row's file origin (attached or fetched), the fetched version and licence, and the methods text adds "Open-access copies of F reports were located with Unpaywall [, OpenAlex] [and arXiv] and each was checked by the reviewer before use; D were discarded (reasons)."
- **CSV**: the charting table (one row per record not excluded at full text), with columns study id, first author, year, title, DOI, round, full-text status, then per charting column its value, note and where-from; UTF-8 with BOM, CRLF (reusing `render_csv`).
- **Spreadsheet (.xlsx)**, sheets: Charting (as the CSV), Full text (every kept record: round, status, reason, decision, reason), PRISMA counts, Charting form (columns, definitions, types, options, amendments), About (workspace, protocol fingerprint, corpus snapshot, screening generation and its publication date, export time, app version, "working export"). Written with `openpyxl` added to the base install (pure Python; open question 8).
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
- [ ] DoD K3. No guessed publisher URL is requested and no proxy is used, even when the settings ask for them (as G3 and G4 decide; a test sets both and the stub server sees no such request).
- [ ] DoD K4. OpenAlex is asked only with `SCHOLAR_OPENALEX_KEY`, sent as the key; a 409 is reported as the budget spent (cassettes).
- [ ] DoD K5. 403, 404 and 410 are not retried; a closed `is_oa` overrides a `pdf_url`; the candidate that produced the bytes is recorded (PDF-06, PDF-12).
- [ ] DoD K6. A manifest row per DOI asked, at the caller's path; no file without its row (PDF-07, the kit's half).
- [ ] DoD K7. The PDF-15, -17, -18, -05 and -03 fixes, each with its test; the publisher-pattern tests replaced; the kit suite passes.
- [ ] DoD K8. The production commands lose the parked prefix; the docs and the kit skill say what is production and what stays parked; the `extract` commands keep their notice unless G1 says otherwise.

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

**Out (later, or another milestone):** fetching through an institutional proxy, guessed publisher URLs, records with neither a DOI nor an arXiv id; reading PDFs as production, unless G1 brings it in; reading PDFs, extracted text, page anchors and the in-app viewer (M12b-read); highlights in the full text (M8b's component, applied in M12b-read); an agent proposing cells (M12c, specified now as a plan, built after (g)'s list); a second reviewer and reconciliation; linking reports of one study; per-criterion full-text answers; risk of bias or quality appraisal; synthesis, the graph, the trust score (parked); importing a spreadsheet charted elsewhere; changing the protocol's `matrix_dimensions` from the table; the phone.

## Parts, one PR each

| Part | Content | Lane | Size | Why this lane |
| :-- | :-- | :-- | :-- | :-- |
| **A. Rows and full text** | The cross-round reader, events store, status, decisions, attachments, links, undo, the table's Full text view, the nav step, the Publish and Inception wording, a CSV of the Full text view | **RELEASE** | M–L | New public routes and refusal codes, a new persisted record, a new reader of published artifacts |
| **B. Charting form and cells** | `form.json`, amendments, pilot, cell events, the Charting view, the one-study view, a plain CSV of the Charting view | **RELEASE** | L | New persisted records and routes |
| **K. The PDF kit's acquisition to production** | (d3) items 1 to 13: e-mail required, the app's user agent, no guessed URLs, the OpenAlex key, no proxy, no 4xx retries, OA status from the evidence, the kit's manifest, the identity check, honest commands, portable writes, notices, docs and tests | **RELEASE** | L (one PR at the upper end); plus L if G1 adds reading, plus M if G2 adds E1 | A kit's public commands and network behaviour change; a parked surface becomes production |
| **F. Open-access fetching** | The fetch run through the kit, the manifest path, the arXiv-id look-up and the id fix, `Fetched, to confirm`, confirm and discard, the Full text view's fetch states, the fetch journal rows | **RELEASE** | M (upper end, with the arXiv look-up) | Outgoing provider calls, new routes and refusal codes, a new persisted manifest |
| **C. Export and reporting** | CSV and xlsx, PRISMA full-text counts, methods block, export journal | **RELEASE** | M | New public route, a new published file (`prisma_fulltext.json`), a new base dependency |

Order **A, B, F, C**, with **K** built beside B (the researcher's answers 6, 10 and F2). After A the researcher can track retrieval, attach their own PDFs and decide at full text; after B they can chart; after F the open-access copies come in for confirmation; C makes the files for the paper. Five RELEASE PRs instead of three (seven if G1 and G2 bring in reading and E1). If the one-to-two-week need cannot wait for C, Part B can carry the plain CSV of the Charting view (small) and C the rest. A spreadsheet charted elsewhere cannot be brought back in (out of scope), so starting outside the app before B lands means typing twice. F and B share the table screen, so they are built one after the other (B first, F2); K shares no file with either and can be built beside B.

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
| PDF reading, E1 `acquire`, matrix extractor | **Not used** by M12a (reading: G1; E1: G2; matrix: X3, parked) | — |

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

Decision item 3 was accepted on 2026-11-21 (answer 3); answer 6 adds the fetch and F1 the whole kit, with G1 to G5 open. The plan itself is not edited by this specification. What the main session must change there, once G1 to G5 are answered:
- **§6, row 5 (M12a):** the content now includes Part K and Part F; the lane is RELEASE per part; five PRs (A, B, K, F, C), seven if G1 and G2 bring in reading and E1; order A, then B with K beside it, then F, then C.
- **§6, the M12b-read and M12c rows** (if listed there): M12b-read takes reading PDFs unless G1 puts it in M12a.
- **§8, "Docs":** full text (`scholar_pdf`, PDF-07/08) is no longer simply parked: the acquisition side becomes production (Part K), reading stays parked unless G1 says otherwise.
- **§8, "CLI" and "MCP":** `download` and `ingest` lose the parked notice; `extract`, `extract-run`, `acquire` (G2) and the MCP tools keep theirs or their typed refusal as G1 and G2 decide.
- **§8, "UI":** unchanged; the charting screens are not a parked surface.

| Plan §8 item | After M12a |
| :-- | :-- |
| "full-text" (UI) and full text in the parked docs list (`scholar_pdf`, PDF-07/08) | **Split, as F1 and G1 to G5 decide.** Full-text *status* and the *full-text decision* become production, typed by the researcher. With F1, the kit's acquisition side (the downloader, `download`, `ingest`) becomes production after Part K's repairs, and Part F's fetch with a manifest and the researcher's confirmation is built on it. Recommended to stay parked, each a question: reading PDFs (G1, with PDF-08 open), E1 `acquire` and its MCP refusal (G2), the publisher patterns (G3), the institutional proxy (G4), the console's legacy pipeline templates (G5). |
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

Questions 1 to 10 and the follow-up questions 1 and F1 to F7 were answered on 2026-11-21 (top of the scope section). The open ones, G1 to G5 on what "the whole kit" covers, are on the researcher's page: [`M12a-charting-table-for-review.md`](M12a-charting-table-for-review.md). The screen-level questions are in each screen spec and are still open. The agent's questions are on [`M12c-agent-cells-for-review.md`](M12c-agent-cells-for-review.md).
