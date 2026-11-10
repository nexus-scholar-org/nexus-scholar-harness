# 07 States    Status: FINAL | Phase 1 Discovery | No route (behaviours inside each screen: 01 Plan, 02 Recall, 03 Harvest, 04 Import, 05 Dedup, 06 Report, 08 Hand-off) | Milestone M3c-screens

Boards: `States` (D7, `docs/ux/phase1-discovery/final/project/States.dc.html`), `MobileStates` (`.../MobileStates.dc.html`), the failure notes of `MobileStatus`. Packet: `docs/architecture/research_ui/DISCOVERY_API_PACKET.md` §4.7, §6 decision 5; records `docs/roadmap/milestones/M3b-api.md` decisions 1, 3, 7-9, 13 and `M3d-engine.md` decisions 7, 8, 12, 13 (they override the packet where they differ). Code: `src/scholar_harness/console/refusals.py` (registry; discovery codes added in M3b-api and M3d-engine), `console/api/discovery.py`, `console/api/screening_v1.py:603`, `src/scholar_harness/corpus_accept.py`, `serve.py:230`, `apps/research-ui/components/screening-state-card.tsx:90` (`StateCard`), `apps/research-ui/lib/screening-states.ts:137,263,667`. Model: `docs/ux/phase0-inception/final/08-states.md`. Shared rules (refusal card shape, ENGINE_UNREACHABLE, PROTOCOL_MISSING/INVALID, SSE rules): see 01-plan.md, Shared.

**Purpose.** For every discovery screen, name what happens when a step cannot go on as planned: one sentence, what it affects, one next step, and the typed code behind Details. This spec holds the table of codes and their copy.

**Changed from the canvas.** The board has nine cards; each state with no engine behind it is cut or reworded. Every cut:
- **"No records saved: Crossref timed out and Semantic Scholar was rate-limited" (Failed)** with "Retry the failed databases" and "Open run 2". The engine has no per-database retry (no per-leg stop or slice yield, M3b-api). The state stays, as `PROVIDERS_FAILED` (job error, every database failed) with the leg codes under each database; the action is "Search again" (a whole new run, allowed before the accept; Harvest). "Run 2's files are still there, marked stale" is cut: stale means a later run's records became the corpus, not "an older failed run"; the stale marker is its own state (below). The compound code line `PROVIDER_TIMEOUT · PROVIDER_RATE_LIMITED` becomes one code per database row, because leg codes are fields of a leg and never an HTTP refusal.
- **"Crossref stopped at the 2,000 cap" (Lower bound, `CAP_REACHED`).** Not a refusal and no code `CAP_REACHED` exists (the engine has `cap_hit` on a leg and `completeness: "lower_bound"` in the report). It is shown as a non-refusal state (below). "Split by year" and "Accept the lower bound" are cut: no route splits by year or records an acceptance; the honest action is "Search again with a higher cap" (decision 7, Harvest) while no corpus is accepted. The numbers (2,000, about 13,100) come from the leg, not from the copy.
- **"The protocol changed after run 2" (`PROTOCOL_CHANGED`, fingerprints, "Record the amendment", "See the change").** No route records an amendment and the run list carries no fingerprint. The engine's two protocol-changed refusals are `PROTOCOL_CHANGED_SINCE_RUN` (the accept, 409) and `PROTOCOL_CHANGED_SINCE_SNAPSHOT` (a run job error); both ask for a new search or the inception path, never an amendment from this screen.
- **"Set a contact email before searching" with an email field and "Save and continue" (`CONTACT_EMAIL_MISSING`).** Decision 5: the contact email stays the environment variable `SCHOLAR_MAILTO`; the browser writes no setting. The code is `MAILTO_NOT_SET`; the card prints the exact line to set and offers Retry. No input field.
- **"The local engine is not answering" with "A running harvest keeps going in the engine; nothing is lost" and "How to restart the engine".** The first sentence would be false when the console closed (closing the console cancels the run and keeps it `PARTIAL`, decision 1). The card says the page cannot reach the engine and that Harvest shows whether a search is still running once the engine answers. The restart link is the shared card's existing text.
- **"3 lines of the Scopus file could not be read" (`IMPORT_LINE_REJECTED`).** No such code: the row codes are `IMPORT_NO_TITLE`, `IMPORT_BAD_TAG`, `IMPORT_BAD_YEAR`, with the line number. Two of them (no title, bad year) still import the record (M3d-engine decision 7). Copy says which. Shown on 04 and the Report. "Scopus" is replaced by the staged label.
- **"The journal row could not be written" (`AUDIT_NOT_WRITTEN`) and "Move into the workspace".** No such code or route exists. Cut. The screens never claim a journal write beyond what the response says.
- **Phone states** (`MobileStates`: "Offline", "1 decision queued · will send when connected", "Scan the desktop QR again", "Connected"). Discovery is desktop-only; there is no decision to queue. Cut; a phone gets `TOKEN_SCOPE_REFUSED` (below).
- **Card order and the three-column grid** are not kept; the table below replaces them, and each screen renders its own `StateCard`.

## Entry / exit
- Entry: none of its own. A refusal reaches the researcher through the screen that called the route.
- Exit: the "action" column of the table: a link to a step (Plan, Recall, Harvest, Import, Report, Hand-off), "Try again", "Open the running job" or "Go to inception".
- Gate: none. Refusals are never retried silently, never turned into an override, and never shown as a success.

## Data in
| Field | Source |
| :-- | :-- |
| a refusal: `{detail: {code, message, details?}}` with the HTTP status | any discovery route; registry `console/refusals.py` ✓ |
| a job's `error {code, message, details?}` and a leg's `error_code` | `GET /api/v1/discovery/jobs/{id}` and the SSE `failed`/`done`/`leg` events ✓ M3b-api (`discovery.py:855`, `:864`) |
| a row's `rejected[{line, code, reason}]` | `GET /api/v1/screening/corpus` `sources[]` ✓ M3d-engine; `GET /api/v1/discovery/report` `imports[]` ✓ |
| proxy codes `CONSOLE_UNREACHABLE` (502) and `CONSOLE_TIMEOUT` (504) | the Next proxy `apps/research-ui/app/api/console/[...path]/route.ts`; shown as `ENGINE_UNREACHABLE` (`screening-states.ts:667`) ✓ |

An unregistered code renders as itself (the `stateCopy` fallback never guesses).

## Data out
None. This spec writes nothing.

## Backend calls
None of its own. Each code below is raised by the call in its "Raised by" cell, all ✓ (M3b-api `discovery.py`, M3d-engine `screening_v1.py:603` and `corpus_accept.py`). None is a new route; the registry entries and the contract §7 rows exist. The en/fr/ar copy and the StateCard entries are ✗ M3c (the implementer adds them to `screening-states.ts`). New StateCard actions needed ✗ M3c: `discovery-step` (a link to a step named in the entry), `job-open` (a link to Harvest with `?job=` from `details.job.job_id`), `env-line` (prints the line to set, with a copy button).

## The table of codes
Role is the brand status role (`docs/ux/brand/tokens.json`), shown as words in the badge, never colour alone. "Screens" is the screen(s) that can show it. Sentences are the en master (`discovery.states.<CODE>.title` and `.body`; `.affects` and `.action` as in the last two columns). The typed code is under Details, selectable, LTR.

### Protocol and workspace
| Code | HTTP | Role | Screens | Sentence (title: body) | Affects | Action |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| `PROTOCOL_MISSING` | 409 | blocked | 01, 02, 03, 06, 08 | There is no protocol to search with yet: Discovery reads its question, years and limits from a frozen protocol, and this workspace has none. | Every step of discovery | Go to inception (link `/inception/`). The board's "Import an export instead" is kept as a plain link to 04 only while no search ran |
| `PROTOCOL_INVALID` | 422 | blocked | 01, 02, 03, 06, 08 (accept) | The protocol cannot be read: Its file is damaged or no longer valid, so nothing can be searched or accepted. | Searching and the hand-off | Go to inception, or fix the file; shows the engine message under Details |
| `PROTOCOL_CHANGED_SINCE_RUN` | 409 | unclear | 08 (accept) | The protocol changed after this search: {run} searched a query or year window the protocol no longer has. Run the search again before accepting its corpus. | The hand-off | Search again (link to 03, only while no corpus is accepted) |
| `PROTOCOL_CHANGED_SINCE_SNAPSHOT` | job error | unclear | 03 | The protocol no longer matches the accepted corpus: The workspace already froze a corpus under another protocol, and the engine will not resume on it. Start a new workspace for a changed protocol. | That search | Go to inception (new workspace); no "amend" action exists. Rare in the browser: after an accept a run answers `CORPUS_ALREADY_ACCEPTED` first |
| `MAILTO_NOT_SET` | 409 | blocked | 02, 03 (and the Plan's `mailto_set: false`) | Set a contact email before searching: A search needs a contact email for the literature databases. Set `SCHOLAR_MAILTO` for the console (environment or .env) and start it again. | Recall and Harvest | The exact line in mono with a copy button: `SCHOLAR_MAILTO=<your email address>` (no placeholder address is filled in), then "Try again" (`onRetry`, re-sends nothing until clicked). The browser writes no setting |

### Jobs and runs
| Code | HTTP | Role | Screens | Sentence | Affects | Action |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| `DISCOVERY_JOB_ACTIVE` | 409 | unclear | 02, 03 | A search is already running: One discovery job runs at a time in a workspace. | Starting another | Open the running job (`details.job`, the job object; link to 03 with its `job_id`) |
| `DISCOVERY_JOB_NOT_FOUND` | 404 | unclear | 02, 03 | The console no longer knows this job: Jobs are kept in memory; the last ten finished are kept, and a restart clears them. | Live progress for this job | Open Harvest (it reads `active_job` and the run list) |
| `RUN_NOT_FOUND` | 404 | exclude (no run yet) or unclear (unknown run) | 03, 05 (link), 06 | There is no such run: No search run exists in this workspace yet, or `?run=` names none. | The report | Go to Harvest, or open the latest run |
| `RECALL_NOT_RUN` | 404 | exclude | 02 | No recall check has run yet: The page shows nothing until you run one. | The recall table | Run the check (02) |
| `DEDUP_NOT_RUN` | 404 | exclude | 05 | No deduplication has run yet: A search run deduplicates; a database export is deduplicated when you accept it. | The Duplicates counts | Go to Harvest. (An import-only workspace also answers this: known P3) |
| `SEEDS_INVALID` | 422 | blocked | 02 | A seed is not an identifier the check can use: {message} (the engine names the first bad seed). One to 25 seeds, each a DOI or an arXiv id. | The recall check | Fix the seed named |
| `CAP_INVALID` | 422 | blocked | 03 | That cap is not allowed: A per-run cap is a whole number from 1 to 10,000. | Starting a search | Change the cap |
| `PROVIDER_UNKNOWN` | 422 | blocked | 02, 03 | A database name is not one the engine knows: {unknown} is not in {known}. | Starting | Choose from the list |

### Corpus and hand-off
| Code | HTTP | Role | Screens | Sentence | Affects | Action |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| `CORPUS_ALREADY_ACCEPTED` | 409 | include on 08 (it is the finished state), blocked elsewhere | 03, 04, 08 | The corpus is already accepted: A frozen corpus is never searched or changed again. | Running, importing and accepting | Go to screening Home. On 08 the accepted card shows instead of a refusal. Never a "Run again" |
| `STAGED_IMPORT_PENDING` | 409 | unclear | 03 | Database exports are staged for import: Accept or remove them before a search run. | Starting a search | Go to 04 / 08 to accept (removal is not offered: no DELETE) |
| `VERIFIED_EXISTS` (via `staging_refused`, and the 409 on a source upload) | 409 | unclear | 04, 08 | An export cannot be added after a search: Exports are staged only before any search run. | Adding an export | Stay on the hand-off; the screen shows the message the engine gave. Combining both is a later milestone (M3f), not offered |
| `NOTHING_STAGED` | 409 | exclude | 08 | There is nothing to accept yet: No search records and no staged export. | Accepting | Go to Harvest or Import |
| `BATCHES_INCOMPLETE` | job error | unclear | 03 | Some studies are in no screening batch: {message} (the engine counts the studies of the accepted corpus that no batch holds). | That search | Go to screening Home and prepare again. Rare in the browser, as above |
| `ACCEPT_CORPUS_REFUSED` and other `AcceptCorpusRefused` codes (for example `PROTOCOL_METHOD_INVALID`) | 409 | blocked | 08 | The engine refused to freeze the corpus: its own message is shown under Details (the code is not guessed). | Accepting | None beyond the engine's message and "Try again" |
| `SOURCE_*` upload refusals (`SOURCE_LABEL_INVALID`, `SOURCE_DATE_INVALID`, `SOURCE_NOT_RIS`, `SOURCE_TOO_LARGE`, `SOURCE_DUPLICATE_FILE`) | 422 / 413 / 409 | blocked | 04 | Owned by spec 04 and the screening Import cards; listed so this table is complete | The upload | See 04 |

### Job outcomes and legs
| Code | HTTP | Role | Screens | Sentence | Affects | Action |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| `PROVIDERS_FAILED` | job error | blocked | 03, 06 | No database answered: Every database failed, so no records were kept. Each database's reason is below. | This search | Search again (03) |
| `DISCOVERY_FAILED` | job error | blocked | 03 | The search failed: Something other than a database refused it. The engine's text is under Details. | This search | Search again; if it repeats, copy the text for a bug report |
| `PROVIDER_RATE_LIMITED` | leg field | unclear | 03, 06 | {database} was rate-limited: It answered too many requests and stopped; its count is a lower bound or missing. | That database | Wait, then search again. Never an HTTP refusal; a failed leg makes a partial run |
| `PROVIDER_TIMEOUT` | leg field | unclear | 03, 06 | {database} timed out: It did not answer in time. | That database | Search again |
| `PROVIDER_UNAVAILABLE` | leg field | unclear | 03, 06 | {database} was unavailable: It returned a server error or no answer. | That database | Search again later |
| `PROVIDER_REFUSED` | leg field | blocked | 03, 06 | {database} refused the request: It answered with a client error. The engine's text is under Details. | That database | Check the plan's translation (01) |
| `IMPORT_NO_TITLE` | row field | unclear | 04, 06 | A record has no title: It was imported as "Unknown Title" (line {line}). | That record | Check the export |
| `IMPORT_BAD_TAG` | row field | unclear | 04, 06 | A line was not a tag: It was dropped (line {line}). | That line | Check the export |
| `IMPORT_BAD_YEAR` | row field | unclear | 04, 06 | A year was not four digits: The record was imported without a year (line {line}). | That record | Check the export |

### Transport and guards
| Code | HTTP | Role | Screens | Sentence | Affects | Action |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| `ENGINE_UNREACHABLE` (proxy `CONSOLE_UNREACHABLE` 502, `CONSOLE_TIMEOUT` 504) | 502 / 504 | blocked | all | The page cannot reach the engine on this computer: The last answer stays on screen with its time. If you closed the console, a running search stopped and was kept as a partial run. | Reads, saves and new searches until it answers | Try again; Harvest shows whether a search is still running |
| `TOKEN_SCOPE_REFUSED` | 403 | exclude | all (phone) | Discovery runs on your desktop: This page is not available to a phone. | The whole screen | Go to screening (`/screening`) |
| `ACTION_ORIGIN_REFUSED`, `HOST_REFUSED`, `TOKEN_REQUIRED`, `CONSOLE_ORIGIN_REFUSED`, `CONSOLE_METHOD_REFUSED`, `CONSOLE_PATH_REFUSED` | 403 / 4xx | blocked | all | The shared guard cards; unregistered ones render as their code | The action | As the existing cards |

### States that are not refusals
| State | Where | Source | What the screen shows |
| :-- | :-- | :-- | :-- |
| **Cancelled job** | 03 | job `state: "cancelled"`, SSE `failed`; status `CANCELLED`; legs `stopped` with the note "cancelled by the researcher" | "You stopped this search. What was fetched is kept as a partial run; nothing was deduplicated and no corpus was frozen." Role unclear. Action: "Search again". No code: a cancel is not a refusal |
| **Stream drop** | 03 | the SSE connection closed without `done`/`failed` | Per 01-plan.md, Shared: reconnect once, replay from the start, then keep the last state with "Retry". Copy: "Live progress stopped. The last state is shown." No typed code; Details says "event stream closed" |
| **Lower bound** | 03, 06, 08 | leg `cap_hit: true`, report `completeness: "lower_bound"`, handoff `lower_bound_databases` | "{database} stopped at its cap of {cap}, so its count is a lower bound: the database holds at least this many." Role unclear. Never shown as a complete count. Action: "Search again with a higher cap" while no corpus is accepted, else none |
| **Stale run** | all run-scoped screens | `runs[].stale` | "Stale: a later run's records became the corpus." The screen is read-only (see 01-plan.md, Shared) |
| **Partial run** | 03, 06 | status `PARTIAL`/`CANCELLED`, a leg `failed` or `stopped` | The status as written, with each database's own state |

## States
- **Default**: this spec has no screen; the default of each state is its `StateCard`: the badge in the role (title as text), an `h2` (or `h1` with `pageHeading` when the card stands for the screen), the body sentence, a `Details` disclosure holding "Affects: ..." and the typed code in the role colour (LTR, selectable), one action. The code is behind Details (rule page 12).
- **Empty**: `PROTOCOL_MISSING`, `RUN_NOT_FOUND` (no run), `RECALL_NOT_RUN`, `DEDUP_NOT_RUN`, `NOTHING_STAGED` are "nothing yet" states in the `exclude` role, not errors.
- **Loading**: each screen's skeleton (`aria-busy`); the card appears only when a read has failed or a job has ended with an error.
- **Error**: every row of the table. An unrecognised 5xx renders as its own code. A refusal on a write never alters the page's data.
- **Partial**: the "Partial run" row and the leg codes above; a refusal that concerns one database never hides the others.
- **Offline**: the engine is local; offline means `ENGINE_UNREACHABLE`; the page keeps its last read with "As of {time}", disables writes with "needs the engine on this computer", and never queues.
- **Protocol-changed**: the two rows in "Protocol and workspace". `PROTOCOL_CHANGED_SINCE_RUN` is the only one a button can trigger (the accept); `PROTOCOL_CHANGED_SINCE_SNAPSHOT` arrives as a job error.

## Desktop layout
No board layout is kept (the 3x3 grid of cards is a catalogue). Each screen renders `StateCard` where its content would be, full width of the main column, above the content it does not affect (a leg code sits inside that database's row; the screen-level codes stand for the screen with `pageHeading`). Components: the existing `StateCard`; three new StateCard actions (see Backend calls). Tokens from `docs/ux/brand/tokens.json`.

## Mobile layout (≤ 640 px)
Discovery is desktop-only on the engine (plan §4: write and job screens are desktop only); `MobileStates` is cut. A narrow desktop window stacks the card at full width with a 44 px action. A real phone gets `TOKEN_SCOPE_REFUSED` on the first read and shows `discovery.common.phone.desktopOnly` ("Discovery runs on your desktop. Open this page there.") with a 44 px link "Go to screening". The phone board's offline queue, QR re-scan and Connected badge are not built.

## Keyboard
Focus moves to the card heading when a refusal appears; the action is the next tab stop; Details is a native disclosure (`Enter` or `Space`). The copy button of the `MAILTO_NOT_SET` line is reachable and announces "Copied" politely. No single-key shortcuts.

## Copy
Keys in the discovery copy file named in 01-plan.md (en master, fr and ar by the implementer).
- `discovery.states.<CODE>.{title,body,affects,action}` for each code in the table, en text as written there. `body` placeholders: `{run}`, `{database}`, `{line}`, `{unknown}`, `{known}`, `{message}` (printed LTR in `bdi`).
- Non-refusal states: `discovery.states.cancelled.{title,body,action}`, `discovery.states.streamDropped.{title,body,action}` ("Live progress stopped. The last state is shown." / "Retry"), `discovery.states.lowerBound.{title,body,action}`, `discovery.states.partial.title`.
- Shared (01-plan.md, Shared): `discovery.common.stale`, `discovery.common.asOf`, `discovery.common.offline` "needs the engine on this computer", `discovery.common.phone.desktopOnly`, `discovery.common.retry` "Try again", `discovery.common.mailto.line` "SCHOLAR_MAILTO=<your email address>" (never a real or placeholder address filled in), `discovery.common.mailto.copy` "Copy the line", `discovery.common.mailto.copied` "Copied".

## Accessibility
- Role words in the badge ("Blocked", "Needs you", "Nothing yet") and never colour alone; `blocked` is text colour, not a fill behind text (tokens.json usage); contrast pairs `ink` on `surface`, `blocked` text on `ground`.
- Refusals `role="alert"`; the code is selectable text in mono, `dir="ltr"`; the copy button names what it copies.
- RTL (ar): the card mirrors; codes, run ids, line numbers and the env line stay LTR with Latin digits.
- Targets 44 px; light and dark tokens.

## Acceptance tests
Vitest `apps/research-ui/tests/discovery-states.test.tsx`: every code in the table maps to a copy key in en, fr and ar and shows its code under Details (a table-driven test over the list); an unknown code renders as itself; `MAILTO_NOT_SET` prints exactly `SCHOLAR_MAILTO=<your email address>`, has a copy button and a Retry that re-reads only when clicked, and has no input field; `DISCOVERY_JOB_ACTIVE` links to the job in `details.job`; `PROTOCOL_CHANGED_SINCE_RUN` links to Harvest only while the corpus is not accepted; `CORPUS_ALREADY_ACCEPTED` never offers a run; leg codes render per database and never as a page refusal; a cancelled job shows the cancelled card and no code; a closed stream shows the last state, reconnects once and then offers Retry; a capped leg shows "lower bound" and never a bare count; a stale run is read-only; `CONSOLE_UNREACHABLE` and `CONSOLE_TIMEOUT` render the `ENGINE_UNREACHABLE` card; `TOKEN_SCOPE_REFUSED` renders the desktop pointer; `discovery-states.i18n` (all keys in en; N9). Python: `tests/console/test_console_refusals.py` already keeps the registry in step with the contract §7 table; no engine code is added by this spec.
Playwright `discovery.spec.ts`: a stateful fake raises each refusal on its route; axe in light and dark; RTL (ar); no overflow at 375 and 1440 px.

## Questions closed by the researcher (2026-11-10: each recommended answer taken, "all recommended")
None.

## As built (M3c)
The codes are cards in `apps/research-ui/lib/screening-states.ts` (en, fr, ar), checked in every locale by `tests/discovery-copy.test.ts`. The printed contact line is `SCHOLAR_MAILTO=<your email>` (spec 01's form), with Check again. `CORPUS_ALREADY_ACCEPTED` keeps the screening card ("The corpus is already frozen"); on the discovery screens the accepted state replaces Start, Check and Accept, so the card is rarely reached.
