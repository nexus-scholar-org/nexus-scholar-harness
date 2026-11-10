# 06 Search report    Status: FINAL | Phase 1 Discovery | Route `/[locale]/discovery/report` (`?run=run_NNN`, desktop only) | Milestone M3c-screens

Boards: `Report` (D6, `docs/ux/phase1-discovery/final/project/Report.dc.html`), `MobileReport` (`.../MobileReport.dc.html`). Packet: `docs/architecture/research_ui/DISCOVERY_API_PACKET.md` §4.6, §6 decision 7; records `docs/roadmap/milestones/M3b-api.md` decisions 3-5, `M3d-engine.md` decisions 8, 9. Code: `src/scholar_harness/console/api/discovery.py:524` (`report`), `:627` (`put_methods`), `:397` (`runs`), `:419` (markdown), `:402` (one run). Pattern for generated methods text: `docs/ux/phase2-screening/final/10-export-and-methods.md`. Brand: `docs/ux/brand/BRAND_BOOK.md` (principle 5, machine output as a draft), `docs/ux/brand/tokens.json`. Shared rules: see 01-plan.md, Shared.

**Purpose.** Read what each database was asked and returned, state which counts are lower bounds, and review the methods text before it goes into a manuscript.

**Changed from the canvas.** Every cut or change:
- **No total and no headline count.** The board's Total row (3,506), the h1 "Run 3: ... what you can claim", the phone headline "3,506 identified; 3,241 left after duplicates" and the badge "Partial · 1 of 4 failed" are sums or tallies the browser would compute. The answer has no total. Instead: per-database counts as written; the run's own `fetched_total` from the run list (an engine number); the run `status` printed verbatim as a badge (mapped to a label by a table, an unknown status prints as itself).
- **"Cache" column cut.** `identification[].cache` is `null` for every row (`discovery.py` report; packet marks it optional). A column of dashes is not shown.
- **"No abstract" column kept** from `no_abstract_rate` (a fraction or `null`); `null` reads "not counted".
- **Reported count "unknown"/"~13,100".** `reported_total` prints as written; `null` prints "not reported". The "~" is added only if the engine sends text; the screen does not invent it.
- **"Not searched" list.** The board's "Scopus and Web of Science (no connection; import an export)" and "bioRxiv (off: cannot evaluate NOT or Boolean operators)" have no source: `not_searched[]` carries only `database` and `reason` of `"off by default"` or `"not selected in the protocol"`. The screen prints those two reasons. `no_connection` is never produced.
- **"Imported exports 0 · none in run 3"** becomes the `imports[]` table (label, searched on, query, limits, records, and the `rejected` lines with their typed row codes). An empty `imports[]` says "No database export was staged for this run."
- **"Records identified, all sources", "Duplicates removed 265", "Records after duplicates 3,241"** come only from `dedup.removed`, `dedup.by_tier` and `dedup.unique_works`. When the report's run is not the newest corpus run these are `null` (M3b-api decision 5), and the screen says so in plain words (see Partial). "Near-twin pairs 14 / 2 decided" is cut (`near_twins: null`, M3e).
- **"Outside the year window: 18, kept and flagged for screening"** prints `outside_year_window` only; "flagged for screening" has no source and is cut.
- **PRISMA box** (not on the board; the packet adds it): `prisma` from the screening preview, `null` before screening starts.
- **Methods text.** "Edit text" and "Mark as reviewed" become: an editable text area and the one brand action "I reviewed this text" (`PUT /discovery/report/methods` with `reviewed: true`), plus "Save as draft" (`reviewed: false`, secondary). "Copy with the appendix of strings" becomes a copy button for the text plus the link to the markdown report, which carries the strings.
- **Run history** keeps run, date and status; the board's file paths (`literature/runs/003/raw.json`, `manifest.json`, `requests.json`) are cut (the folder is `search_runs/run_NNN`, no route lists these, and the browser must not name files it does not read). "Compare with run 2" is cut: no route compares runs.
- **Journal card** (`DISCOVERY_SEARCH`, `DEDUPLICATION`) is cut: no route returns journal rows, so the screen would be asserting what it cannot read.
- **"Fill the gaps": "Split Crossref by year" and "Retry Semantic Scholar" are cut.** There is no per-database retry and no year split (M3b-api: no per-leg stop, no slice yield). Honest replacement for a `lower_bound` or `failed` row: one line "To fetch more, search again from Harvest (a higher cap can be chosen there)" with a link, shown only while no corpus is accepted and the run is the latest (a frozen corpus is never re-run).
- **"Continue to hand-off"** was the brand button. The one brand action here is "I reviewed this text", so "Continue to hand-off" is a secondary link.
- **Phone.** `MobileReport` ("Open full report on desktop", the Status/Report/Near-twins tab bar) is cut; see Mobile layout.

## Entry / exit
- Entry: the step bar; "Continue to the report" from Dedup (05); a direct URL with `?run=`. Latest run by default; older runs are read-only and marked stale (see 01-plan.md, Shared).
- Exit: "Continue to hand-off" goes to 08 (carries `?console=`); "Back to Dedup" to 05; the run selector changes `?run=`. The markdown report opens in a new tab or downloads.
- Gate: none for navigation. The methods review is a record of the researcher's review, not a gate (a miss blocks nothing).

## Data in
| Field | Source |
| :-- | :-- |
| `run`, `status`, `cap_override` (printed when set: "Cap raised for this run to {cap_override}", `cap_source` `run_override`) | `GET /api/v1/discovery/report?run=` ✓ M3b-api `discovery.py:524` |
| `identification[]`: `database`, `kind` (`search`/`import`), `executed_query`, `reported_total`, `fetched`, `completeness` (`full`/`lower_bound`/`failed`/`stopped`), `no_abstract_rate`, `error_code`, `searched_at`, `notes` | same (`cache` is `null`: not shown) |
| `not_searched[]` `{database, reason}` | same |
| `imports[]` `{label, searched_on, query, limits, records, rejected[{line, code, reason}]}` | same (`limits` and `rejected` ✓ M3d-engine E3) |
| `dedup` `{removed, by_tier, near_twins, unique_works}` (`null` fields unless the run is the newest corpus run) | same |
| `outside_year_window` | same |
| `prisma` (`null` before screening) | same (`GET /screening/prisma/preview`) |
| `methods_text` `{text, built_from, reviewed, reviewed_at, earlier_reviewed}` | same |
| `runs` (the run selector and history: `run`, `status`, `started_at`, `finished_at`, `legs_total`, `fetched_total`, `raw_published`, `cap_override`, `stale`; `active_job`) | same, equal to `GET /api/v1/discovery/runs` ✓ M3b-api `discovery.py:397` |
| the markdown report | `GET /api/v1/discovery/runs/{run}/report` ✓ M3b-api `discovery.py:419` (`text/markdown`) |

`completeness` words: `full` "Complete" (include role), `lower_bound` "At least {fetched}" with a marker (unclear role), `failed` "Failed" with `error_code` under it (blocked role), `stopped` "Stopped by you" (unclear role). A `lower_bound` row prints "at least N" with N = `fetched` and the marker "Lower bound · stopped at the cap"; it never prints a bare number. `error_code` is one of `PROVIDER_RATE_LIMITED`, `PROVIDER_TIMEOUT`, `PROVIDER_UNAVAILABLE`, `PROVIDER_REFUSED` or `null` (a leg failure that is not a provider answer has no code, only its text in `notes`).

## Data out
- Review or save the methods text: `PUT /api/v1/discovery/report/methods` ✓ M3b-api `discovery.py:627`, body `{text (1 to 20,000 characters), reviewed (required boolean), run}`; answers `{text, built_from, reviewed, reviewed_at}`. Writes `search_runs/run_NNN/methods.md`; journals `METHODS_TEXT_REVIEWED` with `method: HUMAN`. A draft save (`reviewed: false`) is journaled under the same event name with `reviewed: false` (M3b-api reviewer follow-up); the screen says nothing about the journal beyond "Recorded".
- Nothing else.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/discovery/report?run=run_NNN` | ✓ M3b-api `console/api/discovery.py:524` |
| `PUT /api/v1/discovery/report/methods` | ✓ M3b-api `discovery.py:627` (browser allowlist: PUT) |
| `GET /api/v1/discovery/runs/{run}/report` | ✓ M3b-api `discovery.py:419` |
| `GET /api/v1/discovery/runs` | ✓ M3b-api `discovery.py:397` |

Not in `_PHONE_ROUTES` (`serve.py:55`): `TOKEN_SCOPE_REFUSED` (403) on a phone.

## States
- **Default**: eyebrow "Step 6 of 7 · Search report · PRISMA-S"; h1 "What each database was asked and what came back."; lede "Every row carries the exact string sent, the database's own total, the fetched count and the UTC date. A count stopped at a cap is a lower bound."; run badge (status); `cap_override` line when set; **Records identified per database** table (Database, Executed string with a copy button, Reported, Fetched, Completeness, No abstract, Searched UTC); **Not searched**; **Imports**; **Duplicates** (the three tier counts, removed and unique works as written); **Outside the year window**; **Screening so far** (PRISMA, when present); **Methods text** (draft card); side column **Run history** and the markdown link. The side link "Continue to hand-off".
- **Methods text states** (machine output stays a draft until the researcher says otherwise). `reviewed: false`: the card is `surface` with the dashed `ink-muted` border (the canvas `.draft`), badge "Methods text · draft · not reviewed", line "Built from {built_from} by the harness's template. Check every number against the table." The text area is editable; edits are local until a save. Buttons: "I reviewed this text" (the one brand action, `reviewed: true`), "Save as draft" (`reviewed: false`), "Copy text". `reviewed: true`: badge "Reviewed by you · {reviewed_at}" in the include role with the words; the text is shown as saved; if the researcher edits it, the badge turns "Edited, not saved" (unclear role) and the card never claims reviewed until the next `PUT` with `reviewed: true` returns. Saving an edited reviewed text as a draft says first: "This text will no longer be marked as reviewed." The screen never shows "reviewed" from local state: only from the response. `earlier_reviewed` present: a collapsed card "Reviewed text from {run}, {date}" with the text and "Copy text"; it is not applied to this run's draft.
- **Empty** (`RUN_NOT_FOUND`, 404: no run yet in this workspace): StateCard as page: "There is no search run yet." Affects: the report. Action: "Go to Harvest". Not an error in the researcher's work (role `exclude`).
- **Loading** (skeleton): table skeleton with five rows and a text-block skeleton, `aria-busy`; no number before the read finishes. During a save the brand button reads "Saving the review" and is disabled.
- **Error** (typed refusal, `StateCard`): `PROTOCOL_MISSING` (409) and `PROTOCOL_INVALID` (422) on load (the report reads the protocol): shared card, see 01-plan.md, Shared. `RUN_NOT_FOUND` (404) for an unknown `?run=` (message "{run} is not a run of this workspace.") with a link to the latest run. On save: `RUN_NOT_FOUND` as above; a text over 20,000 characters or empty is blocked in the form before sending (the engine's 422 is a validation error, shown as its own code if it arrives); `ENGINE_UNREACHABLE`; guard codes. A failed save keeps the text in the box.
- **Partial**: (a) `completeness` `failed`, `stopped` or `lower_bound` rows show their words and code; the status badge says Partial or Cancelled as the engine wrote it. (b) `dedup` fields `null`: "Duplicate counts are not this run's: a later run's records became the corpus." (`discovery.report.dedup.notThisRun`); the tier rows show "not this run's", never zero. (c) `prisma` `null`: "Screening has not started, so there is no PRISMA box yet." (d) `reported_total` `null`: "not reported". (e) A stale run (`runs[].stale`): the marker "Stale: a later run's records became the corpus" (shared) and the whole screen is read-only, including the methods text (no buttons that write; the text is selectable).
- **Offline**: the engine is local; offline means unreachable. The last report stays with "As of {time}"; the methods buttons are disabled with "needs the engine on this computer"; unsaved text stays in the box.
- **Protocol-changed**: the report carries no protocol fingerprint, so it cannot detect one. The hand-off does (08, `PROTOCOL_CHANGED_SINCE_RUN`). The report is the record of what was asked at that run; a note under the executed strings says "These are the strings sent in {run}; they may differ from today's plan."
- **Running job**: if `runs.active_job` is not `null`, a banner "A search is running" with a link to Harvest; the report shows the last finished run.

## Desktop layout
Source: `Report` (D6), reduced as listed. Regions: shell and step bar; eyebrow, h1, lede, run selector and status badge; main (about two thirds): identification table in a horizontal scroll container; Not searched; Imports; Duplicates; Outside the year window; PRISMA; methods text card. Side (one third): Run history, the markdown link ("Open the report as markdown"), "Continue to hand-off" (secondary link). Executed strings are mono, wrap anywhere, with a copy button per row (`discovery.report.copy`, announces "Copied" politely). Components: existing table, badge, card, `.draft` card, StateCard. The `lower_bound` marker is a text badge in the unclear role plus the word "At least".

## Mobile layout (≤ 640 px)
Discovery is desktop-only on the engine (see 05); `MobileReport` is cut as a phone layout and serves a **narrow desktop window**: one column: run selector, status badge, h1, then one card per database (name, completeness badge, "At least N" or the count, reported total, searched date, a "Executed string" disclosure with the copy button), Not searched, Imports, Duplicates, Outside the year window, the methods card, Run history, then "Continue to hand-off". The methods action "I reviewed this text" is full width, 44 px, above "Save as draft". A real phone shows `discovery.common.phone.desktopOnly` with a 44 px link "Go to screening" after the refused first read (`TOKEN_SCOPE_REFUSED`). The board's note "The executed strings, run history and methods draft are on the desktop report" is not shown: on a narrow desktop window they are all present.

## Keyboard
Focus order: skip link, shell, step bar, run selector, status, table rows (copy button per row), "Open the report as markdown", the methods text area, "Copy text", "Save as draft", "I reviewed this text", Run history links, "Continue to hand-off". `Escape` does nothing destructive. After a successful save, focus stays on the button and the badge change is announced (`aria-live="polite"`); after a refusal, focus moves to the card heading. No single-key shortcuts.

## Copy
Keys in the discovery copy file named in 01-plan.md (en master; fr and ar by the implementer). No literal `aria-label`, `title`, `alt`, `placeholder` (N9).
- `discovery.report.eyebrow` "Step 6 of 7 · Search report · PRISMA-S"; `title` "What each database was asked and what came back."; `lede` "Every row carries the exact string sent, the database's own total, the fetched count and the UTC date. A count stopped at a cap is a lower bound."; `capOverride` "Cap raised for this run to {cap}."
- Table: `col.database` "Database"; `col.query` "Executed string"; `col.reported` "Reported"; `col.fetched` "Fetched"; `col.completeness` "Completeness"; `col.noAbstract` "No abstract"; `col.searched` "Searched (UTC)"; `reportedNone` "not reported"; `noAbstractNone` "not counted"; `copy` "Copy the string"; `copied` "Copied"
- Completeness: `completeness.full` "Complete"; `completeness.lowerBound` "Lower bound"; `completeness.atLeast` "At least {n}"; `completeness.lowerBoundNote` "Stopped at the cap, so the database holds at least this many."; `completeness.failed` "Failed"; `completeness.stopped` "Stopped by you"
- `discovery.report.notSearched.title` "Not searched"; `notSearched.off` "off by default"; `notSearched.notSelected` "not selected in the protocol"
- `discovery.report.imports.title` "Database exports"; `imports.none` "No database export was staged for this run."; `imports.rejected` "{n} lines were not imported"; `imports.limits` "Limits: {limits}"
- `discovery.report.dedup.title` "Duplicates"; `dedup.removed` "Removed"; `dedup.unique` "Works left"; `dedup.notThisRun` "Duplicate counts are not this run's: a later run's records became the corpus."
- `discovery.report.window` "Records published outside the year window: {n}"; `prisma.title` "Screening so far"; `prisma.none` "Screening has not started, so there is no PRISMA box yet."
- Methods: `methods.title` "Methods text"; `methods.badgeDraft` "Methods text · draft · not reviewed"; `methods.badgeReviewed` "Reviewed by you · {date}"; `methods.badgeEdited` "Edited, not saved"; `methods.built` "Built from {run} by the harness's template. Check every number against the table."; `methods.review` "I reviewed this text"; `methods.saving` "Saving the review"; `methods.draft` "Save as draft"; `methods.unreview` "This text will no longer be marked as reviewed."; `methods.copy` "Copy text"; `methods.earlier` "Reviewed text from {run}, {date}"; `methods.tooLong` "The text is limited to 20,000 characters."
- `discovery.report.history.title` "Run history"; `history.note` "Each run keeps its own files; none is overwritten."; `markdown` "Open the report as markdown"; `again` "To fetch more, search again from Harvest."; `stringsNote` "These are the strings sent in {run}; they may differ from today's plan."; `next` "Continue to hand-off"; `back` "Back to Dedup"; `running` "A search is running"
- Empty: `discovery.report.empty.title` "There is no search run yet."
- Shared: `discovery.common.stale`, `discovery.common.phone.desktopOnly`, `discovery.common.asOf` (01-plan.md). Refusals: `discovery.states.<CODE>.*` (07).

## Accessibility
- Contrast pairs: `ink` on `surface` for rows, `ink-muted` captions; badges are words in their role (`include` Complete/Reviewed, `unclear` Lower bound/Stopped/Edited, `blocked` Failed); status never rests on colour alone. The `.draft` card is labelled by its badge; the brand `gate` dashed border is not used here (it belongs only to gates).
- The table has a caption, real headers and `scope`; a long executed string wraps (`overflow-wrap: anywhere`) and its copy button names the database ("Copy the string for OpenAlex"). The scroll container is focusable with a label.
- The methods text area has a visible label, a character counter in words ("{n} of 20,000"), and `aria-describedby` for the draft line; saves announce through `aria-live="polite"`; refusals use `role="alert"`.
- RTL (ar): layout mirrors; executed strings, run ids, dates, counts and codes are `dir="ltr"`, Latin digits; the methods text is `dir="auto"` (English by the harness template, editable in any language).
- Targets 44 px; light and dark tokens.

## Acceptance tests
Vitest `apps/research-ui/tests/discovery-report.test.tsx`: each `completeness` renders its words ("At least N" with the marker for `lower_bound`, never a bare number; `failed` with its `error_code`; `stopped`); no total and no sum is rendered (feed rows and look for none); `cache` is not shown; `not_searched` prints the two reasons; imports print `limits` and the `rejected` lines with their codes; `dedup` `null` fields print "not this run's" and never 0; `prisma: null` prints the line; `cap_override` prints when set and not otherwise; methods text with `reviewed: false` is a draft card and never says reviewed; "I reviewed this text" sends `PUT {text, reviewed: true, run}` once, disables itself while pending, and shows Reviewed only from the response; an edit after review shows "Edited, not saved"; "Save as draft" sends `reviewed: false` after the warning; a failed save keeps the text; `earlier_reviewed` renders collapsed and is not applied; a stale or older run is read-only (no write control); `RUN_NOT_FOUND` empty and unknown-run cards; the markdown link targets `/api/console/...runs/{run}/report`; offline disables the methods buttons; `discovery-report.i18n`; `discovery.live-only`.
Playwright `discovery.spec.ts` (this screen's part): a partial run (one failed, one capped, one stopped), edit and review the methods text and reload to see Reviewed; select an older run and see it read-only; RTL (ar); axe light and dark; no overflow at 375 and 1440 px.

## Questions closed by the researcher (2026-11-10: each recommended answer taken, "all recommended")
1. **Editing a reviewed text.** The engine lets you save a new text at any time and then marks it not reviewed unless you say reviewed again. The screen warns "This text will no longer be marked as reviewed" before saving an edit as a draft. Should the screen instead block edits to a reviewed text until you press "Edit"? Recommended: no block; the warning is enough and fewer steps.
2. **Reviewing after the corpus is accepted.** The engine accepts the review of the latest run's methods text before and after the hand-off accept. Recommended: allow it (the methods text is for the manuscript and is not part of the frozen corpus), and keep older runs read-only.

## As built (M3c)
