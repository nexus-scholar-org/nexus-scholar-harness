# Decisions

One entry per decision that still shapes the code, newest first. The full
records were removed in the 2026-11-03 docs cut; each entry names the commit
history to read if you need the original reasoning (`git log --follow -- <path>`).

**How to read this log (2026-11-20).** An entry's heading states its status. Entries dated before 2026-11-08 that carry no status were decided before statuses were written into headings; they are in force unless a later entry or a "Superseded" note on them says otherwise. When a later decision replaces an earlier one, the earlier one carries a note.

**Open decisions (2026-11-20)**

| Entry | Item | What is open |
| :-- | :-- | :-- |
| 2026-11-21 — M11a Part B: known papers and comparison sets | 1 to 10 | Proposed with the build; the researcher's answer is pending. |
| 2026-11-21 — M11a Part A: the workbench's counts | 1 to 13 | Proposed with the build; the researcher's answer is pending. |
| 2026-11-19 — M9a: what the measurement says about the ladder gates | 2 | The minimum share of the researcher's excludes an agent must take before a rung unlocks: the principle is accepted; the researcher decided on 2026-11-20 to set the number when M9b is built. |

## 2026-11-21 — M11a Part B: known papers, comparison sets and the search development at genesis (items 1 to 10 PROPOSED)

Record: `docs/roadmap/milestones/M11a-query-workbench.md`, "Part B". Branch `dev/m11a/part-b-seeds-comparison`, built on Part A's branch. What the specification decided (OpenAlex only for the per-database checks, behind a switch; a comparison set never added to the corpus; the development saved under `audit/query_development/`; the two fixed checks never blockers) is built as decided. No Contract v1 model, schema, identity or fingerprint changes: the new files are side files outside the baseline; the preview's `files` list grows by the development files a draft has.

1. **Where a known paper's words come from, and the lookup.** In order: the first search's pool (records with a DOI), a harvest on Plan (the newest run's records, or the accepted corpus), the texts looked up earlier (`query_development/seed_texts.json`), and, only when the screen asks (`lookup: true`, cost stated first), one OpenAlex request per 50 unknown DOIs, counted in the budget. A seed with no title and no abstract is "not read". The lookup is an identifier filter without a search, which OpenAlex documents; it is not behind the switch.
2. **The switch for the per-database checks** (DoD 11, the comparison's "found by OpenAlex"): the environment variable `NEXUS_WORKBENCH_OPENALEX_IDS=1`, off by default; while off, the answer says `switch_off` and the screen "Not checked here". After the live run confirms OpenAlex combines `doi:` with `search.title_and_abstract` in one request, the default can be turned on (a one-line change).
3. **A comparison set's storage:** `query_development/comparison/cmp_NNN/` with the original file (`export.ris` or `export.nbib`) and `set.json` (database, the string stated, export date, and per record title, abstract, DOI, keywords, year). Beside the draft before genesis, under `audit/` after; never under `literature/`. A record without a title is dropped (counted nowhere). Limits as decided (5 sets, 5,000 records) plus 50 MB per file.
4. **Refusal codes** (named here, the screen spec's question 8): `WORKBENCH_COMPARISON_FORMAT` (422: not readable as RIS or NBIB, not base64, or no titled record), `WORKBENCH_COMPARISON_TOO_LARGE` (422), `WORKBENCH_COMPARISON_FULL` (409), `WORKBENCH_COMPARISON_NOT_FOUND` (404), `WORKBENCH_COMPARISON_MEASURE` (409: "harvest" with nothing to compare with; an unknown measure is `BODY_INVALID`).
5. **The measure is the screen's choice, never silently changed.** "Found in your harvest" reads the accepted corpus (`literature/verified.json`) when there is one, else a run's records (`?run`, newest by default; the screen spec's question 10), by DOI or the dedup's normalised title (`scholar_search.dedup.title_key`, made public; the private name stays an alias). At Inception it is refused, not replaced by another measure.
6. **Terms the missing records use:** the M4d candidate rule (`recon.distiller._term_candidates`, 1 to 3 words, its stop words), in at least two missing records, sharing no folded word with any term of the query; most records first, then the shorter term (a single word is the likelier synonym); at most 15. A known paper that lacks a concept offers up to 5 terms of its title by the same rule.
7. **The seed warning's levels:** `few` (1 or 2 readable), `all` (every readable seed uses a term of every concept), `concept` (some concepts no readable seed lacks; all are listed, the check names the first). No warning with no seed (`DIRECTION_SEEDS_FEW` covers it) or none readable (the panel says "not checked"). The fixed check `SEEDS_CANNOT_TEST` reads without any request.
8. **`QUERY_NOT_COUNTED` is cleared only by a Count of the saved version itself**: every count log row now carries the counted version's key (`version_key`). A version whose strings were all in the log (counted under an earlier version) sends nothing and writes no row, so the note stays until a Count sends at least the full query. *Alternative:* clear it from the cache keys (one translation per database at every checks read).
9. **Genesis copies the development and writes one journal row** (`QUERY_DEVELOPMENT_RECORDED`, outputs and counts) only when the draft has one. A replacement appends the logs, merges the looked-up texts and numbers the comparison sets after the existing ones (each keeps its draft id). The preview lists the files the draft has (`audit/query_development/counts.jsonl`, `seed_checks.jsonl`, `seed_texts.json`, `comparison/`).
10. **Comparison sets belong to the review, not to a query**: a set carries no `query_key`; each report carries the `query_key` and the version it measured (section (g)).

**Lane RELEASE** (`test_gate_policy.md`): new public routes and refusal codes, new genesis files in a public preview answer, two new check ids.

## 2026-11-21 — M11a Part A: the workbench's counts, the count log, the budget and the quota memory (items 1 to 13 PROPOSED)

Record: `docs/roadmap/milestones/M11a-query-workbench.md`, "Part A". Branch `dev/m11a/part-a-counts`. These are the choices the specification and the FINAL screen specifications leave open; what they decided (counts only on Count, the budgets, the 24-hour log, Crossref, the ×2 note) is built as decided. No Contract v1 model, schema, identity or fingerprint changes; the new files are side files outside the baseline.

1. **Where the shared budget and quota memory live: `<workspaces root>/.query_workbench/state.json`.** "Shared by every draft and workspace on this computer" is read as "under the workspaces root the console serves", the folder drafts (`.drafts/`) already live in; the catalog skips dot folders. *Alternative:* a per-user folder (outside every root), which two roots on one computer would share.
2. **OpenAlex without a key is its row (`key_missing`); the other databases are still counted.** The estimate refuses the whole call (`OPENALEX_KEY_NOT_SET`); the workbench does not, because a database's failure is its row (spec (a)). `MAILTO_NOT_SET` and `DISCOVERY_JOB_ACTIVE` refuse a real call only; the dry call answers `mailto_set` so the screen can show the setting before Count.
3. **A database's first failure stops its other requests in that Count.** After a refusal, a used-up quota, a throttle, a timeout or no answer, its remaining variants are not sent and not charged; each cell says the same status. Sending four more requests to a database that just said "slow down" would spend its quota for nothing.
4. **A whole Count lasts at most 100 seconds** (under the browser proxy's 120 s); each request at most 45 s (`COUNT_TIMEOUT`). Databases are asked in parallel, each database's requests one after another. A request not started in time is `timeout` and not sent.
5. **Databases counted when the screen names none:** at Inception the four of the preset (the screen sends the databases ticked on Explore, decision 2026-11-21 item 2); on Plan the protocol's list as written (Crossref is then drawn `not_comparable`, not hidden).
6. **The log's key is the database, the exact string sent, the years and the language;** a log answers for its own draft or workspace (the draft's log becomes the workspace's at genesis, part B). Not across drafts: two drafts counting the same string count it twice, which keeps each draft's development complete.
7. **The workbench's word match (whole words, English plurals), stated once in `scholar_search.workbench.fold_word`:** text is case-folded and every character outside `0-9a-z` separates words (as INC-21's `term_occurs`); a term matches as consecutive words; each word on both sides is folded: `-ies` to `-y` (over 4 letters), `-sses`, `-xes`, `-zes`, `-ches`, `-shes` lose `-es`, else a final `-s` goes unless the word ends in `ss`, `us` or `is` (over 3 letters). M8b-triage-highlights writes its browser matcher to this rule (note left in the shared notes); the two are separate code and must stay equal.
8. **The size estimate on Plan reads the workbench's log and writes nothing to it.** A string counted in the last 24 hours is a `counted` row with `from_count_log` (when it was counted); "Count again to refresh" (`refresh`) bypasses it. The estimate's own in-memory cache is unchanged.
9. **`estimate.count_one` rows gain `http_status`, `quota_exhausted` and `resets_at`** (additive; the code stays `PROVIDER_RATE_LIMITED`). The estimate answer carries them too.
10. **Only the query key `main` is taken** (`WORKBENCH_VERSION_INVALID` otherwise), and "Read what this concept removes" is OpenAlex only, one request of 25 records, charged to the budget and logged as a `removed` row that never answers a count.
11. **"What each synonym adds" asks the full query too** when it is not in the log: its cost is one request per term plus one for the full query (after a Count the full query is usually in the log, so it is one per term, as the specification says). The cost is stated before anything is sent.
12. **Counting after the corpus is accepted still writes the count log** under `audit/query_development/`: DoD 22's "records nothing" is read as "changes nothing in the protocol, the corpus or the journal". The log is the record of the search's development, which a methods section may want even after the accept. *Alternative:* count without logging after the accept.
13. **The budget is reserved before sending, and the shared file is never read as empty when it cannot be read** (review of Part A, round 1). A Count takes its whole planned cost from the budgets in one locked step and gives back what it did not send (a database stopped by its first failure); two Counts at once can no longer both pass. A state file that cannot be read after five tries refuses with `WORKBENCH_STATE_UNREADABLE` (503) and is not overwritten, so a moment's lock by another program cannot erase every pause and the day's spending. *Limit:* the lock is per console process; two consoles on one root are not serialised.

**Lane RELEASE** (`test_gate_policy.md`): six new public POST routes, three new refusal codes, a persisted file under `audit/`, additive fields on the estimate's rows.

## 2026-11-21 — The M11a screen questions closed; H-run-small-fixes Part C accepted (accepted by the researcher 2026-11-21)

The researcher answered these in the main session on 2026-11-21, each as proposed.

1. **H-run-small-fixes Part C, items 1 to 10, accepted as built** (entry below; PR #267): the proof answer writes no criterion beside a typed inclusion and stays the fallback of a draft with none; each out-of-scope item is its own exclusion criterion, undecided until accepted; weak proposed directions are filtered and a typed direction is grounded on its words; the smaller items as built.
2. **The query workbench at Inception** (`docs/ux/phase0-inception/final/10-query-workbench.md`, now FINAL): while a version has unused edits, "Use this version" is the brand button and Continue and Accept are secondary; merging two concepts opens a name field filled with the first concept's name; Count asks the databases ticked on Explore and the workbench has no list of its own; years and languages are shown and changed on Scope; a known paper can be added by DOI in the workbench (at most 25). Its other questions (route names, refusal codes, how an applied term is recorded, the proposed wording, the constants, the narrow layout) are closed as the spec proposes.
3. **"Change the search" on Plan** (`docs/ux/phase1-discovery/final/10-plan-amend-search.md`, now FINAL): it opens as a closed section on Plan; an amendment may be recorded for a version that was never counted, and the journal row says "not counted". Its other questions (the read that returns the concepts, who writes the consequences list, the reason's limit, the refusal when the protocol changed elsewhere, the neighbouring links, no pool on Plan, the two checks shown at Inception only, which run a report reads) are closed as the spec proposes.
4. **The wording stays open** until the researcher reads the built screens.

## 2026-11-20 — H-run-small-fixes Part C: the proof writes no criterion beside a typed inclusion, out-of-scope items accepted one by one, weak directions filtered, a cancel that says it is stopping (items 1 to 10 accepted by the researcher 2026-11-21, after the merge in PR #267)

Record: `docs/roadmap/milestones/H-run-small-fixes.md`, Part C. Found by the acceptance run of 2026-11-20 (findings 1 to 7, 23, 35, 39) and the Inception redesign's decision D15. Contract v1 baseline current before and after; no Contract v1 schema, protocol schema, identity or fingerprint algorithm changes. What a new protocol contains changes (items 1, 2): no existing protocol, corpus or decision is touched.

1. **Finding 1, narrowed: the proof answer writes "Reports the gold-standard proof — …" only as the fallback inclusion of a draft with no typed inclusion left.** Beside a typed inclusion (not dropped) the proof answer writes no criterion; it still feeds the rationale ("Convincing evidence: …") and the template question. Without a typed inclusion it stays the draft's only inclusion, undecided until accepted, as before (the M10b `proof_required` rule now also decides whether the criterion is written: `Survey.proof_criterion`). The CLI wizard keeps writing it (its prompt asks for each criterion with default "no"). An imported protocol whose first inclusion is that sentence keeps it as a typed inclusion when it has others, so an import round trip keeps every inclusion. **Alternative not built: never write it.** Measured: removing it broke more than 50 tests across the CLI wizard, genesis, the golden protocol and the import; a draft without a typed inclusion would then fail on "The protocol needs an accepted inclusion criterion" until the researcher types one, and the CLI wizard would need a new prompt. That is a larger change to how a protocol's inclusion side is formed; say if you want it (it fits M10f-3, Shape and Criteria).
2. **Finding 2: the out-of-scope answer gives one candidate per item, each undecided until accepted.** Items are separated by semicolons and line breaks (not commas: "satellite, aerial or ground imagery" is one item); blanks and repeats are dropped. In the browser draft every out-of-scope item is `undecided` until the researcher accepts or drops it (before: accepted by default), and counts in "{n} still need you"; the reason code per item (M10b) is unchanged. The CLI wizard keeps its prompt (default yes: answering is the decision there). Criterion ids of single items are unchanged; a line that held several items gives new ids (its old decision no longer applies, which is the point). Test drafts that relied on the default now accept their items.
3. **Findings 3 and 23: weak proposed directions are filtered.** A phrase made only of colour, band or general method words ("blue green red", "rgb nir"; a fixed list in `recon/directions.py`) or a cut of an acronym's expansion ("aerial vehicle uav", also "unmanned aerial vehicle uav": the words' initials end the acronym that follows them) is never proposed; an acronym is at most one letter longer than the words before it, so "tree height growth" or "small seeded grass" are kept (review P4). Consequence to know: "convolutional neural network cnn" is dropped too, while "convolutional neural network" is kept. The larger rethink is M11a.
4. **Finding 3: a typed direction is grounded when its content words occur together.** The exact phrase is asked first; when it anchors fewer than two papers and the phrase has two or more content words (stop words left out), a paper whose title or abstract holds every content word anchors it; the words rule answers only when it reaches the two papers a typed direction needs, so an ungrounded direction is always reported on its phrase (review round 2, A). The binding records the detail "its words occur together in {n} of {m} titles or abstracts", and `GET /recon/evidence` answers `match: "phrase"` or `"words"` (additive field). The two-paper threshold (`OWN_DIRECTION_MIN_ANCHORS`) is unchanged. The binding records the rule (`direction.match`, `words`), the own direction's `term_evidence` is the evidence that grounded it, and `audit/recon_context.json` records `direction_match`; the Direction screen says "grounded on its words" (review P1, P2). **Risk to accept:** the words may occur far apart in a title and abstract, so a topic pool grounds loose phrases too ("weed detection cost" is grounded by "Low-cost UAV for weed detection" and by an abstract that only mentions the cost of herbicides; review P5). *Alternatives:* title only, or a proximity rule (words within N of each other); not chosen without data.
5. **Finding 4: the start-year note waits for a search.** `SCOPE_START_YEAR_DEFAULTED` ("The first search used 2000") is raised only when the draft has a pool. The UI test fake keeps its own fixed rows ("never the engine's rules") and is not changed.
6. **Finding 5: times without the raw instant.** The F6 local-time fix (2026-11-19) was in the build the researcher used; the raw `2026-11-20T09:45:15.784778+00:00` came from the `<time>` element's `title`, which page readers and assistive technology announce. `Stamp` keeps the instant in `dateTime` only. "Notes ({n})" counts the note rows the disclosure shows, as text (the empty count could not be reproduced from the code; this removes both candidate causes: an engine count that differs from the rows, and a number inside a nested element a reader dropped).
7. **Finding 6: names for assistive technology.** The direction, Explore-mode and import radios carry a value (a radio without one is announced "on"); a DOI link without a title is named "DOI {doi}" (key `explore.papers.linkDoi`, en/fr/ar), not ", DOI {doi}".
8. **Findings 7 and 35: two silent refusals fixed; the exact requests of the run not proven.** Every request on both screens was traced (by a read-only subagent; the run's network log was not kept). *Finding 35:* `POST /proposals/runs/{id}/cancel` answered `state: "cancelled"` while the run was still running (a Batch run checks the cancel between chunks); the screen then offered Start and Calibrate, which the engine refused `RUN_ALREADY_ACTIVE` (409) with the card above the columns, out of view. The cancel answer and the run view now carry the run's own state and `cancel_requested`; the screen says "Stopping the run…" and offers no Start until a poll reports the run finished. A 404 `UNKNOWN_RUN` while polling is possible only when the console was restarted on another workspace. *Finding 7:* Review's "Ready to create?" list drew nothing when the all-steps checks read was refused (422 `DRAFT_INVALID`/`DRAFT_TOO_LARGE`); it now shows the refusal card. Whether these are the run's exact 422, 409 and 404 needs the request URLs from the browser's network tab next time.
9. **Finding 39: the quote check is not changed.** The prompt shows the model exactly the text the quotes are matched against (`record_message` wraps `record_text`), so a normalisation mismatch between the two is ruled out. On the frozen set (screen-v2 measurement, 283 of 1,644 failures) the failure rate does not differ by text feature: Unicode dashes 17.8% with vs 17.1% without, Unicode quotes 21.4% vs 16.5%, literal `\n` 0 of 2, title-only records 12.6% vs 17.9%, long abstracts 18.1% vs 16.7%; by label, 12.4% of the researcher's includes and 20.3% of the excludes. Nothing points at whitespace, Unicode punctuation or ligatures, so a normalisation would most likely not help and could only widen what counts as a quote. The measurement report keeps the failing record ids but not the quotes, and the real review's drafts (which hold them) were not opened. **Follow-up proposed:** keep the failing quote text in the measurement report (and count failures by kind: not found at all, found after whitespace normalisation, found after case folding) so the next measurement can say what the misquotes are.
10. **D15 quick fixes ("doing less first"): one already in the code, none built here.** "Never draw an empty checks panel" is already true (`ChecksPanel` returns nothing with no rows and nothing waiting). "Open the Explore sample by default and put it above the reading" was built and taken back: it contradicts the FINAL guidance audit (the papers are "folded and closed", I-E25) and its density tests, and the redesign record says M10f-0 needs its own go from the researcher. The other three (one check row per proposal, Out of scope asked once, one save on Direction) are more than a few lines.

**Lane RELEASE** (`test_gate_policy.md`): what a new protocol contains (items 1, 2), an additive public field (`match` on `/recon/evidence`, `cancel_requested` on the run view) and a changed public answer (the cancel route's `state`).

## 2026-11-20 — H-run-small-fixes Part B: Crossref left out of a joined query by default, no cap offered when one database is the size, the search command says when it was cut (items 1 to 8 accepted by the researcher 2026-11-20)

Record: `docs/roadmap/milestones/H-run-small-fixes.md`, Part B. Found by the acceptance run of 2026-11-20 (findings 9, 10, 13, 14, 17, 24, 29) and the decision of the same day ("Six open decisions settled", item 2). Contract v1 baseline current before and after; no protocol schema, no Contract v1 artifact, no identity changes. The run record (`legs.json`), the hand-off gate and the CLI `run` are unchanged.

1. **Finding 9: Crossref is not selected by default for a query that joins two or more concepts; how the default is decided.** Crossref's `query` parameter is a relevance search: it returns records that hold any of the words, so the AND between concepts is lost (6,221 matches against 166 in OpenAlex). The screens (Plan, Harvest, and Recall or the estimate sent no list) now start from a *default choice*: the protocol's list (as a run would search it), except that Crossref is left out when the query joins two or more concepts **and the protocol took the default list**: it names no list, an empty list, or exactly the four databases genesis writes (`openalex`, `semanticscholar`, `crossref`, `arxiv`, in any order and spelling), judged on the list as written: a list that adds a name the engine does not know (`scopus`) or names one twice is a written list and keeps Crossref (review P2). A concept whose own terms are joined with AND counts as one concept per term. **Why that rule:** every protocol made by genesis names those four (the preset is written into `protocol.json`, decision M10a item 2), so "a protocol that names Crossref keeps it" would keep it everywhere; a list that differs from the four is a choice the researcher (or an imported protocol) made, and it keeps every database it names (the golden protocol names five and keeps Crossref). The engine says it: `GET /discovery/plan` gains `concepts`, `default_providers`, `default_reason` (`CROSSREF_IGNORES_AND` or `null`), `warnings` (one per selected database that drops the AND) and `ignores_and` (the databases that would, chosen or not; empty for a one-concept query). Ticking Crossref again is allowed and shows the warning. *Not changed:* a harvest sent no `providers` (CLI `nexus-scholar run`, an older screen) still searches the protocol's list; the protocol itself is never edited (decision M10a item 2a). *Alternatives:* (b) change the preset so genesis stops writing Crossref for a joined query (changes every new protocol's content and fingerprint); (c) change the engine's own default for a run sent no list (changes the CLI and the hand-off's reading of a run). Neither built.
2. **Finding 9: the warning, on Plan and on Harvest.** "Crossref does not apply the AND between the {n} concepts of this query: it returns records that hold any of the words, so its count is far larger than the other databases' and most of its records are off-topic. Leave it out of this harvest, or keep it knowing that." When the default left it out: "Crossref is left out by default: this query joins {n} concepts and Crossref would not apply the AND. Tick it to search it anyway." The run report and the PRISMA-S text are unchanged; a harvest without Crossref lists it under `not_searched` as "not selected for this harvest" (M10a).
3. **Finding 10: no per-database cap is offered when one database is the size.** When one database reports more records than all the others together (judged on the reported totals, not on what a cap would fetch, so a cap in force does not bring the cap advice back; review P2), the estimate's recommendation is `kind: "one_database"` (`provider`, `provider_total`, `others_total`, no cap) instead of a cap: "Most of the records come from {name} ({n} of {total}). A cap per database keeps the first records each database returns, which are not the most relevant, so it cannot remove {name}'s off-topic records. Check whether {name}'s records match your question: if they do not, leave it out of this harvest; otherwise narrow the query." (The first wording said a cap would trim "only" that database; with two large databases it trims both: review P2.) with the link to inception. A cap is still offered when no single database dominates. *This changes the FINAL spec's own example* (5,000, 400 and 100 against 1,000 gave "500 per database"): it now names the 5,000 database. *Alternative:* offer the cap beside the advice; not chosen, the finding is that the cap is presented as a fix when it is not one.
4. **Decision 2026-11-20 item 2: arXiv's count is exact with a year window.** `UPPER_BOUND_WITH_YEARS` is empty; the arXiv row no longer says "upper limit" and its count enters the low end of the estimate. The field `fetch_is_upper_bound` stays (always false today) so an older screen still reads.
5. **Finding 14: a throttled host is paced.** A 429 that names no lower rate (no `x-rate-limit-*` header) and a short or no `Retry-After` now halves that host's shared budget (Crossref list or single-record, Semantic Scholar, arXiv) before the retry, never below one request per second (or the configured rate if lower). While that pace holds the host's bucket allows no burst (requests evenly spaced); 429s within one second of the last cut count once (concurrent requests); the pace holds 10 minutes, then the configured rate returns (review follow-ups: before, a burst of four 429s took Crossref to the floor for the life of the process). Measured offline only: against a fake Crossref that allows about 6.7 requests per second, 20 lookups at the configured 10 per second met at most a few 429s instead of about one per lookup. **Not checked against the real Crossref** (no live calls), so whether its 429s in the acceptance run were this kind is not known. *Alternative:* a lower configured single-record rate (5 per second); not chosen, it slows every user to fix what may be a per-network limit.
6. **Finding 29: `scholar-search search` says when it was cut and fails loudly.** After the table it prints, per database: "{name} stopped at the limit of {cap} records; it reports {total}. Raise --limit to fetch more." and "{name} failed ({code}): {error}". When a database failed and no record was found it prints "Nothing was saved: … failed and no record was found.", writes no file and exits 1; when some records were saved but a database failed it saves them and exits 2 (partial); otherwise 0. The `--limit` help says the default (the protocol's retrieval cap, else 100; 20 without a protocol). The skill and its references say the exit codes. *Alternative:* raise the default above 100; not chosen, the protocol's cap is the place for it and the message now says what was cut.
7. **Findings 17 and 24: the Recall card.** "Checked {date} UTC" printed the researcher's local time (the screen formats every engine time in the browser's zone since H-ui-findings F6): the "UTC" is removed (en/fr/ar). The "Crossref: 6221" in the second workspace came from the recall check itself, read from the code: without a list, the check searched every database the protocol names (the protocol names Crossref, the estimate had been asked without it), so 6,221 is very likely a real count for that query; the workspace's check file was not opened (the real review's folder was not touched). A recall check or an estimate sent no list now counts the default choice (item 1), the same databases Plan and Harvest start from, and Plan and Harvest always send the choice on screen to the estimate (review P1: Harvest's estimate counted Crossref while the harvest would leave it out; review N1: after "Reset to the protocol" an estimate sent no list would have left a ticked Crossref out).
8. **Finding 13: "retry only the database that failed" is not built; design left as a follow-up.** It is not cheap: a retried database's records must join the finished run's records before duplicates, abstracts and checks, so the newest published run is no longer "one search, one preparation" (`discovery.py::_run_summaries`, `pipeline/discovery.py`), and the corpus accept that combines a harvest with other sources is M3f-combined-corpus's area, in flight. *Design:* `POST /discovery/runs/{run}/retry {providers}` writes a supplement leg file under the same run (`legs_retry_NNN.json`), its records appended to that run's raw records with their leg; the run's preparation is marked `incomplete` and "Finish preparing" runs duplicates, abstracts and checks again over the union; the run keeps its number, so it is not stale; the report lists the retried leg with its own date. Open questions: whether a retry may use another query string than the run's (no: same protocol fingerprint, refused otherwise), and how PRISMA-S reports two dates for one database.

**Lane RELEASE** (`test_gate_policy.md`): a changed exit code of a public CLI command (`scholar-search search`) and additive public fields on `GET /discovery/plan` and the estimate; the rest (a changed default in the screens, a pacing rule in the HTTP client) would be STANDARD. No contract, identity, persistence or publication semantics change. The PR gate was run; the cross-platform closure gates were not (CI runs them).

## 2026-11-20 — M11a query workbench: the specification's choices (items 1 to 10 accepted by the researcher 2026-11-20, all as recommended; item 1 changes M10c item 16 of 2026-11-19; item 2 reads the 2026-11-20 order decision, item 2, narrowly)

**Accepted.** The researcher answered "yes to all" on 2026-11-20 in the main session, to the list "M11a specification: accept the 10 recommendations and approve it for building?" (relayed by the main session); the specification is approved for building, and the build has not started. M10c item 16 now carries a note.

Record: `docs/roadmap/milestones/M11a-query-workbench.md`; the researcher's page: `M11a-query-workbench-for-review.md` (same questions, same order). Found by the acceptance run of 2026-11-20 (findings 18 to 21): four concepts joined by AND returned 166 records in OpenAlex where three return 781; Scopus counts were 130 strict, 236 without UAV, 512 without multispectral; the recall check passed 4 of 4 because every seed used every concept; 31 of 130 Scopus records were missing from the harvest and the app could not say so. Nothing here changes a Contract v1 model, schema, identity or golden fixture: the new files are side files under `audit/query_development/` (the baseline names no file there), and a search amendment moves the protocol fingerprint through the existing M10c item 9(a) path.

1. **A researcher's amendment from Plan replaces the whole concept list** (remove, rename, merge, split, add), with a required one-sentence reason, through the 9(a) compile, guard (`PROTOCOL_AMENDMENT_REFUSED`, `outside_search`), backup and `PROTOCOL_AMENDED` code, called by a new route `POST /api/v1/discovery/workbench/amend` (not a proposal made and applied by the same person). The journal row carries `source: "researcher"`, the reason and the counts before and after. *Why:* the run's fix was a merge of two concepts, which today's add-only operations cannot express; a new workspace per change is what the researcher had to do on 2026-11-20. *Changes:* M10c item 16 (add only). *Consequences kept as they are* (M10c item 21): an earlier run can no longer become the corpus, checks and estimates of the old fingerprint stop applying, open proposals go stale; refused after acceptance. *Alternative:* keep item 16 and send larger changes through a new workspace (M10b Part A).
2. **M11a builds the workbench, not direction A's frame.** The workbench is drawn as A's concepts block and evidence column and placed inside today's step 5; the frame (M10f-1) and the relayout of Explore and Direction in A go with M11b or a row of their own. *Why:* the frame and both relayouts are each L; with them M11a would be twice M10b. *Reads* the order decision's item 2 ("its Explore and Direction part becomes the query workbench") as the purpose of that part (testing the search on real papers), not its layout. *Alternative:* build the frame first inside M11a.
3. **The search development goes into the workspace at genesis**: the count log rows, seed checks and comparison sets of the draft are copied to `audit/query_development/` and listed in the preview's `files`. *Why:* PRISMA-S reports strings, dates and counts; the researcher writes them down by hand today. *Cost:* the preview answer's file list changes (RELEASE).
4. **A daily request budget per database for the workbench**, per UTC day, shared by every draft and workspace on the computer: OpenAlex 200, Semantic Scholar 100, arXiv 100, PubMed 100, Crossref 20 (constants; to be checked against each provider's published limits at build and after the first real session). A count that would pass it is refused before any request (`WORKBENCH_BUDGET_SPENT`). A used-up quota (`QuotaExhaustedError`) is remembered until `resets_at` and reported as `quota_used_up`. *Why:* the OpenAlex quota ran out during the run's harvest.
5. **Counts are sent only on an explicit Count**, with the number of requests shown before; a persisted log keyed by database and exact string answers a repeat for 24 hours; a failed count is never reused. The estimate on Plan reads the same log.
6. **The concept note threshold is ×2**: a note when leaving a concept out at least doubles a count in a database that combines concepts. The note never says to drop the concept.
7. **Crossref in the workbench**: not counted by default for two or more concepts ("Count anyway" counts the full query, labelled "any of the words"); never in the drop test, the seed or comparison checks, or the works range. The harvest's own Crossref default belongs to H-run-small-fixes; the two read one constant if that milestone adds one.
8. **The workbench's word match folds English plurals** (weed, weeds), in its own matcher; INC-21's whole-word rule for directions and anchoring (M4c, M4d) is unchanged. The match covers title, abstract and keywords, and every report says it is a match by words, not by a database.
9. **OpenAlex is the only database for the per-database seed and comparison checks** (an identifier filter combined with the query, one request per 50 records), behind a switch until a live run shows OpenAlex answers it; the others read "not checked here" and the recall check on Plan is unchanged.
10. **The query translated for Scopus and Web of Science** (TITLE-ABS-KEY, TS=) is shown on the Inception screen to copy, marked "check it in the database", so a comparison export uses the same search. Not tested against those databases.

## 2026-11-20 — M3f-combined-corpus: a harvest and database exports make one corpus, deduplicated together at the accept (items 1 to 8 accepted by the researcher 2026-11-20, item 3 confirmed; M3f-combined-corpus)

Record and full design: `docs/roadmap/milestones/M3f-combined-corpus.md`. Found by the acceptance run of 2026-11-20 (findings 26, 27). No Contract v1 schema, identity algorithm, fingerprint rule or fixture changes: the snapshot builder receives other rows (Packet B inputs), hence the RELEASE lane.

1. **Until the accept a corpus has two parts, the harvest and the staged exports, each changed on its own and in any order.** Exports can be staged before or after a harvest and removed; a harvest can run (and be finished) while exports are staged; a second harvest replaces the first as the harvest part (the first stays `SUPERSEDED` and never enters). `VERIFIED_EXISTS` remains only for a `verified.json` that no search run and no import of this app made (records of unknown origin). `STAGED_IMPORT_PENDING` is no longer raised by "Run the search", "Finish preparing" or the end of a CLI `run`; the code stays registered for older clients. **Supersedes** the decision of 2026-11-10's "an import is allowed only before any harvest" and M3d-engine decision 12 ("Keep the rule for now, combine later"), as both announced, and the M3a review repair that refused a CLI run's snapshot beside staged exports. *Alternative:* allow only "exports first, then harvest"; not chosen, because the researcher's run needed both orders and nothing in the engine depends on the order.
2. **One deduplication at the accept, in a fixed order.** The rows handed to the existing builder are the harvest part's `verified.json` rows as they are, then every staged record in staging and file order, built as an import builds them today; the protocol's `Deduplicator` runs once over all of them inside the builder. The order does not depend on what the researcher did first, so the same inputs give the same `run_id` and artifact id. A harvest-only or import-only accept is byte-identical to before. The representative of a work is the deduplicator's existing choice (best metadata score; the others' identifiers, `sources` and longer abstract merged into it); screening shows the first member record with an abstract, as today. *Alternative:* deduplicate the raw harvest and the imports from scratch (one pass over everything fetched); not chosen, it would change every harvest's works and ids and repeat the verification of merged records.
3. **An unfinished harvest beside staged exports: the exports are accepted alone, and the Hand-off and CLI say so first.** This keeps M3i item 10 (accepted 2026-11-18) as it is; what is new is the sentence before the accept: "The harvest {run} is not prepared ({state}). If you accept now, the corpus holds your exports only and the harvest's records are left out for good. Finish preparing it first to include them." Without exports the accept still refuses `PREPARATION_UNFINISHED` (M3i item 7, H-quota-hang item 4). **To confirm:** *alternative (b):* refuse the accept while any published harvest is unfinished, so a harvest is never left out by a click; it changes M3i item 10, and a quota that stays out for days then blocks a researcher who has exports.
4. **Imported records stay unchecked and keep the abstracts they came with; the app says so** on the Hand-off and in the methods text. A check fills missing identifiers (H-provenance-s2 item 1), which enter the `REC-` id, so a check would make an import's id depend on what a database answered that day; it would also cost one OpenAlex request per imported record, the quota the run used up. M3c decision 9 (no abstract filling) stands. *Alternative:* check and fill imported records with H-quota-hang's `incomplete` behaviour; a milestone of its own if wanted.
5. **Where each record came from.** Each `verified.json` row keeps it (`provider` and `sources[]` for a harvest row, `source_database` for an imported one); the accept writes `literature/raw/provenance_manifest.json` with the schema `nexus.corpus-combined.v1` (the harvest part: run, records fetched per database, total; the import part: the import manifest's `sources` and `databases`; `total_raw_harvested` = fetched + imported). PRISMA identification for such a corpus: identified = fetched + imported, duplicates = identified − works, in the published report and the preview alike. Before the combined `verified.json` is written, the harvest's file is copied to `literature/search_runs/run_NNN/verified.json`, and put back with the manifest if the acceptance gate refuses. Both files are harness run records outside Contract v1.
6. **The Hand-off shows the corpus the accept would build.** Counts from the same in-memory deduplication; the provider mix has one row per source (each database searched, each export by its label) with `kind: "search" | "import"`, counting the works each found (amends spec 08's "no separate imports row"); "With an abstract" and "Title only" count works, a work having an abstract when any of its records has one (finding 27). `corpus.origin` gains `"combined"`; `corpus.harvest` is `{run, state, included}` or `null`. Both are additive.
7. **The report and methods text name how each source was obtained (PRISMA-S).** The corpus run's report lists each searched database with its recorded query (`kind: "search"`) and each export with the date, search string and limits the researcher stated (`kind: "import"`, "not stated" when absent); its `dedup` is the combined one. The methods text adds the exports sentence with those details, one sentence that the imported records were not checked, and "Deduplication across the N sources removed …". The screening export's "Records were identified from …" lists both parts.
8. **Out of scope:** retrying one failed database (finding 13: the harvest part would be several runs), several queries per review (finding 22, a contract decision), an export as a recall comparison set (finding 21), checking imported records (item 4), adding sources after the accept (M3g's round mechanism), a "discard this harvest" action, CSV import, near-twin review (M3e), the import-only report and Duplicates 404s (M3d-engine deferred), and a harvest-only corpus's PRISMA "records identified", which the code counts as works with 0 duplicates (read from the code, not run; changing it changes published numbers, so it is a follow-up with its own decision).


## 2026-11-20 — H-run-small-fixes Part A: approve every decided batch from one paste; the codes also shown in a desktop window (items 1 to 7 accepted by the researcher 2026-11-20; item 4 changes the wording of the 2026-11-04 decision "Approval: terminal-only code")

Record: `docs/roadmap/milestones/H-run-small-fixes.md`, Part A. Found by the acceptance run of 2026-11-20 (finding 38): approval was one batch at a time, each with a one-time code printed in the engine's terminal; the real review has 54 batches of 20, so 54 codes, and the terminal is not visible to a researcher for whom the app was started. Contract v1 baseline current before and after; no Contract v1 schema, model, identity or artifact changes.

1. **One fresh code per batch, shown and pasted together; not one code for many batches.** `POST /actions/pairing/begin-all` stages, for every ready batch, the same challenge `begin` stages (snapshot-bound, hash-only store, 5-minute life, 5 attempts), prints the codes as one block of `batch n: CODE` lines, and returns no code. `POST /actions/pairing/redeem-all` reads the pasted block and runs each pair through the unchanged single redeem. So the screening API contract §9.1 ("a fresh one-time code is issued for each batch generation", researcher 2026-11-04) and spec 09 decision 1 hold as written, and the stored record is unchanged: one approval file per batch, binding that batch's bytes (CON-03), the approver an unauthenticated local attestation (CON-02). **Alternatives not built:** (b) one short code that approves every ready batch: easier to type, but it changes §9.1 and the pairing store's one-batch record (a contract decision for the researcher); (c) an "Approve" button inside the engine's desktop window, with no code at all: what it proves is close to the code (only someone at this computer can press it), but it is a second authority scheme beside UI-07 and needs its own decision. The block is about 36 characters per batch (1,900 for 54), so it is copied and pasted, not typed.
2. **Which batches get a code.** Every candidate has a terminal decision (exact coverage, no unresolved row), the batch has no *current* approval (none, or one made before a decision changed: the staleness rule, unchanged), and it is not deferred (deferring is the researcher's own "not yet"; a single approval still lifts a deferral, as before). The others are listed with a reason: `ALREADY_APPROVED`, `DEFERRED`, `NOT_DECIDED`, or the refusal the batch gave (for example `WORKER_BATCH_MISSING` when its parent file is gone); one broken batch never stops the others (review P2). With no batch ready the answer is `APPROVAL_MISSING` (409), never an empty success. A code begun for one batch earlier is replaced by the new one, as a second `begin` replaces the first.
3. **Each line stands alone.** A pair that fails (a batch changed since its code was shown: `STALE_VIEW`; a wrong, used or expired code: `PAIRING_CODE_INVALID`) is listed under `refused` and the others are still approved: each approval binds only its own batch. With nothing approved the first refusal is the answer, under the request's own id (a paste with no code in it: `PAIRING_CODE_INVALID`, 403). **A journal failure is never a 200:** that batch is rolled back as a single redeem does, the pairs after it are not tried, and the answer is the 500 `ACTION_AUDIT_FAILED` with `details.approved` (the batches approved before it, which keep their approvals and journal rows) and `details.refused` (that batch, then every later one as `NOT_ATTEMPTED`) (review P2). The corpus-wide publication approval is staged only when every batch holds a current approval (CON-03, unchanged).
4. **The codes are also shown in a desktop window opened by the engine, when the app was started for the researcher (`nexus-scholar ui`).** The window runs in a child process of the engine (`python -I code_window.py`, the codes passed on its standard input, never its command line), so Tk never runs in the engine's process: on macOS a first load of Tk off the main thread aborts the whole process (review P1), and a Tk crash anywhere stays in the child. It is on top, titled "Nexus Scholar: approval" (never a code in the title: other programs can read titles), names the batches, says "If you did not just ask for codes on the Publish screen, close this window and copy nothing", shows the codes with a "Copy the codes" button, and closes when they expire. `begin` and `begin-all` answer `code_shown_on: "desktop"` when the child said the window is up, `"terminal"` otherwise; the terminal always has the codes. `nexus-scholar serve` opens no window (it is run from a terminal); `NEXUS_APPROVAL_WINDOW=0` turns it off. **Why this keeps the main thing the code proves.** The 2026-11-04 rule keeps the code off HTTP so that something that can call the console API (a page that got the token, another local process) cannot approve alone; the window is not reachable over HTTP and is shown by the engine on this computer's desktop, like its terminal. **What it changes:** the 2026-11-04 entry says the code is "printed only in the terminal"; under this item it is "shown only on this computer by the engine: its terminal, and a desktop window when the app was started for the researcher". **Two residual risks the researcher accepts by accepting this item (review P2):** (a) *An unrequested window.* A program that holds the console token (the same-user worker of UI-07 §2) can call `begin-all` itself; before this change that only printed codes in a terminal, now it also puts a window with codes on the desktop, on top, for whatever batches are ready. If the researcher copies them, that program can read the clipboard and approve them. The window's own words are the only guard ("if you did not just ask for codes … copy nothing"); the codes still approve only batches that are fully decided, each bound to its exact content. (b) *The clipboard is now the normal path.* UI-07 §3.1 has the researcher type the code, so the clipboard was optional; a block of about 1,900 characters for 54 batches is always copied, so any program of the same user can read it until it is replaced, and could redeem the codes first while they are valid. *Alternatives:* no Copy button (selecting and copying the text still goes through the clipboard, so it changes little); no window, terminal only (back to finding 38); a short single code for all batches (item 1, b), which could be typed instead of copied but changes §9.1.
5. **The journal keeps its per-batch shape.** One `SCREENING_PAIRING_REDEEMED` row per batch, as a single redeem writes, with `bulk: true` and the request id `<request>-b<n>`; no new journal action and no row for the begin (as for a single begin). The codes are never journaled.
6. **The paste is read leniently, the code strictly.** Pairs are `<1 to 6 digits>: <26 characters from the code alphabet>`, case-insensitive; a paste whose line breaks were dropped still reads, because a code has a fixed length. The batch number is bounded so a long run of digits cannot make the match slow (review P3: an unbounded one took 47 s on 40,000 digits). The first pair for a batch wins. A paste longer than 64,000 characters (about 1,800 batches) is read as holding no code. The screen sends the block once and empties the field on submit and when the codes expire (UI-07 §3.6).
7. **Speed.** Each code is still hashed with PBKDF2 at 210,000 rounds when staged and when checked (about 0.24 s each on the researcher's PC), and each approval is written as before. Measured on this PC with 54 batches of 20 decided records: the codes were ready after 34.9 s and the 54 approvals took 40.3 s (one run, while the test suite ran on the same PC, so an idle PC is likely faster). The screen says "Preparing the codes…" and "Approving the batches…", each "with many batches this takes up to a minute", while it works. *Not done:* hashing the codes in parallel.

**Lane RELEASE** (`test_gate_policy.md`): two new public routes on the approval path, an additive public value (`code_shown_on: "desktop"`), and a change to how an approval act is shown.


## 2026-11-20 — The order of work after the acceptance run (accepted by the researcher 2026-11-20)

Record: `docs/roadmap/production-plan.md` §6, "After the acceptance run"; motivation: `docs/roadmap/what-a-researcher-does.md`; evidence: `docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md` (37 findings).

1. **The order is: M3f-combined-corpus, the small fixes from the run, a query workbench (M11a), a criteria pilot (M11b), a minimal charting table (M12a), search updates with several queries (M3j), then release b7.** Sources, the query and the criteria come before agent autonomy and the in-app chat. *Why:* the run's serious findings were about what a researcher does first (develop the search, bring exports, revise criteria), and three of the six were born in Inception and found downstream.
2. **The Inception redesign is no longer a track of its own.** Its quick fixes join the small fixes; its Explore and Direction part becomes the query workbench; its Shape and Criteria part becomes the criteria pilot. Direction A and decisions D1 to D15 (2026-11-20) still say how those screens look.
3. **M9d-discovery-assistant is split:** synonyms and recall repair join the query workbench; the rest waits with M10e. **M3h-providers closes** with the small fixes, which take what is left of it.
4. **The query checks belong to Inception** (the researcher's view): the researcher must be able to test and iterate the query before the protocol freezes, and the same tool serves amendments on Discovery's Plan. **Several queries per review come back** (M3j); the researcher recalls that an earlier version had them.
5. **Specifications first for M11a and M11b:** neither has one; each is written and read by the researcher before anything is built, as for M10b.
6. **At most two milestones in flight,** because the researcher's decisions and reviews are the bottleneck. **One outside researcher uses the app without help before b7.**
7. **Waiting:** M9b and M9c (the M9a measurement is read again under `decisive_first` first), M10e, M3e (conditional), M2. The Matrix beyond the charting table, synthesis, the graph and the risk-of-bias trust score stay parked.


## 2026-11-20 — H-screening-drafts: a decisive answer first, the method amended after genesis, drafts derived under the rule in force (items 1 to 10 accepted by the researcher 2026-11-20, including the spend to measure `screen-v2` on Haiku 5.5; item 2 changes the 2026-11-08 decision "Method parameters move into the protocol")

Record: `docs/roadmap/milestones/H-screening-drafts.md`. Found by the acceptance run of 2026-11-20 (`docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md`): 85% (Haiku 5.5, 220 drafts) and 83% (Opus 5.5, 200 drafts) of the agent's drafts were Unclear, because the `unclear` rule returns Unclear as soon as one criterion is not reported, before it looks at a decisive answer. Re-derived outside the app with a decisive-answer-first rule the same drafts gave Haiku 96 Unclear, 107 Exclude, 17 Include and Opus 102, 85, 13. The rule, not the model, made the unclear pile (M9a item 3 asked for this rule to be settled first). On the same screen, "Show beside the record" silently did nothing because the protocol written at genesis sets blinding, and the run screen cost $7.59 where $0.22 was meant. Contract v1 baseline current before and after.

1. **A third not-reported rule, `decisive_first`.** A failed check or `cannot_decide` stays Unclear; then any exclusion criterion answered yes or any inclusion criterion answered no gives Exclude, with that criterion as the reason code (`EXC-n`, `FAILS-INC-n`); then any `not_reported` gives Unclear; otherwise Include. It differs from `unclear` only where a decisive answer sits beside a gap, and from `exclude` in that an unreported inclusion criterion alone never excludes. `unclear` stays the default and the value genesis writes, so no existing protocol changes. The value is added to `method.not_reported` in `scholar_protocol/models.py` (an additive enum value in the protocol schema, regenerated; `generate_protocol_schema.py --check` passes; a protocol without a block, or with today's block, keeps its fingerprint). Methods sentence: "An exclusion criterion met or an inclusion criterion not met in the title and abstract excluded the record; otherwise a criterion they did not report sent it to full-text assessment." With an amendment, the source sentence reads "These values are set in the signed protocol except as amended below.", each amendment follows, and "The agent's drafts are counted under the not-reported rule in force at publication; …" is written only when the publication has agent drafts (review F1). Name: plain words for what wins first; *alternatives:* `answers_first`, `exclude_on_answer`.
2. **The method is changed after genesis by a recorded amendment beside the signed protocol, not in it.** `POST /screening/method/amendments {field, value, confirm: true}` (desktop only) changes `blinding` or `not_reported`. It writes one line of `audit/method_amendments.jsonl` (amendment id, field, from, to, the screener id as "who", UTC time, the protocol fingerprint it was made under, an optional note) and one `PROTOCOL_METHOD_AMENDED` journal row (`before`/`after`, who, the fingerprint; the INDEX is refreshed). `protocol.json` is not touched, so its fingerprint, the accepted corpus snapshot, the batches and every decision event keep their binding. Every reader of the method (`method.effective_method`) applies the amendments made under the current protocol's fingerprint, oldest first; after a re-inception (a new protocol) they no longer apply. The methods paragraph reports each amendment made before publication, with its date, from and to (`figures.method_amendments`), and the blinding sentences treat a blinding amendment as a change like a settings row. **Why not the existing mechanisms:** M10c item 9(a) recompiles `protocol.json` and moves the fingerprint, and is refused once a corpus is accepted; re-inception archives the corpus. Either would leave every decision of a review in progress bound to a protocol that is no longer current (decision 2026-11-12, F2: they count nowhere). **What this changes in an accepted decision:** the 2026-11-08 entry says the signed protocol covers the method values; under this item the values in force are the signed ones plus the recorded amendments, and the fingerprint alone no longer says which rule derived a draft (so a draft now records `not_reported_policy`, item 3). **Contract v1:** no schema, model, identity, fingerprint algorithm or Contract v1 artifact changes; the proposal store and the journal are not Contract v1 artifacts; `generate_contract_baseline.py --check` passes. The rule never decides a record for the researcher: it shapes the agent's drafts and the reason the screen offers (under `exclude`, the checklist offers `FAILS-INC-n` for an unreported inclusion criterion), so no published inclusion or exclusion is derived from an amendment today. **This holds only until M9b:** under rung L1 an agent Exclude becomes an `AGENT_ADOPTED` decision, and an amendment from `unclear` to `decisive_first` turns many drafts into Excludes (107 of Haiku's 220 in the acceptance run) without moving the fingerprint, while the ladder's calibration is valid on "protocol fingerprint, task version, model" and only a fingerprint change drops the review to L0. **So M9b must also bind a calibration and the rung to the method in force** (the not-reported rule and blinding, amendments included), and an amendment must drop the review to L0 like a protocol change; a note says so in `docs/architecture/agent_autonomy_ladder.md`. **Alternatives not built:** (b) write the new value into `protocol.json` and re-prepare: a new fingerprint, every decision so far counts nowhere; (c) leave the method block out of the fingerprint the screening binds to, or re-bind existing events to a new fingerprint: both change Contract v1 identity rules and need a contract decision (Compass §3: never recompute a parent identity to make acceptance pass). If the researcher prefers (b) or (c), the overlay can be removed without a migration: nothing else reads the file.
3. **Stored drafts keep their first outcome; the outcome shown and counted is derived when read.** `proposals.jsonl` stays append-only: each draft keeps its answers, its checks, the outcome first derived and, from now on, the rule it was derived under (`not_reported_policy`; absent on older lines). `proposals.outcome_in_force` re-derives the outcome from the stored answers and checks under the rule in force, for drafts made under the current protocol; a draft made under another protocol keeps its stored outcome. It is used by the draft view (`GET /records/{id}/proposal` returns the outcome in force and `recorded: {derived_outcome, reason_code, not_reported_policy}`), the queue's agent-uncertainty order, the agreement table and the calibration check; triage says "First recorded as … under the earlier not-reported rule" when the two differ. *Alternative:* a recorded re-derivation (a new line per draft at each amendment); not chosen: it duplicates the store, and read-time derivation is deterministic from what is stored.
4. **Who may amend what.** Only `blinding` and `not_reported`; the dedup tiers and the rule-table version shape the corpus and the table and change only by re-inception. Blinding can be amended only when the protocol's method block sets it; without a block it stays the workspace setting changed on Prepare (`PUT /settings`, as before). A value already in force, an unknown field or value, or a missing `confirm` is refused `METHOD_AMENDMENT_INVALID` (HTTP 422, a new console refusal). `BLINDING_SET_BY_PROTOCOL` stays and now names the amendment route. "Who" is the workspace's screener id (`researcher:local` by default), the same identity the decisions carry; it is not a verified sign-in.
5. **Prepare offers the change and asks first.** Choosing the other blinding value, or another not-reported rule, opens a confirmation ("Amend the protocol's method?") naming the field, from and to, saying it is recorded in the journal and the methods paragraph and that the signed protocol, the corpus and the decisions are not changed (and, for the rule, that drafts are shown and counted under the new rule); nothing is sent before "Record the amendment". The amendments in force are listed under the controls. No radio silently does nothing any more. The rule table shows the decisive-first wording when that rule is in force. en/fr/ar.
6. **The run screen remembers the model and names the spend.** `GET /proposals/setup` returns `last_model` (provider and model of the newest run of any kind in the workspace); the screen starts from it, else from the cheapest listed model (`claude-haiku-5-5`, a UI constant a test pins to `prices.toml`). The confirmation reads "Send N records to Anthropic with <model>?" and "Estimated cost: $X (prices as of <date>)."; a dry run's dialog shows its own estimate (fetched when the dialog opens), and "Start the run" waits for it. *Alternative:* the engine chooses the default model; not chosen, the list of models is the screen's.
7. **A run says what it is waiting for.** The screen shows "Starting the run…" from the click until the engine answers (it took about 40 s in the acceptance run; the cause of that delay was not investigated). A run records `batch` and `chunk_size` (`GET /proposals/runs/{id}`; read from the estimate for older runs); while a Batch run is active the screen says "Sent to the batch service; results arrive in chunks of 200, usually within minutes." with the time waited, ticking.
8. **An accepted corpus without batches is not a missing corpus.** Screening reads (`/queue`, `/records`, `/agreement`, run scope) answered `SNAPSHOT_NOT_ACCEPTED` ("No accepted corpus") when the corpus was accepted but no batch was prepared; they now answer `BATCHES_NOT_PREPARED` (HTTP 409, a new console refusal, its own card "Batches not prepared yet" with a link to Prepare). `POST /prepare` and a workspace with no accepted corpus are unchanged.
9. **Inception does not ask.** Genesis still writes `blinding: reveal_after_decision` and `not_reported: unclear` without asking; no new Inception screen is built here. Recorded as a follow-up for the Inception redesign (M10f-3, Shape and Criteria) in the milestone record.
10. **A candidate prompt, `screen-v2`, built and not used.** Its only change from `screen-v1` is guidance to answer yes or no when the abstract gives reasonable grounds (another usual name, a narrower kind or a named instance of what the criterion asks about, with the UAV and multispectral examples) and to keep `not_reported` when there are none; the quote rule is word for word the same. It is listed under `[versions]` in `task.toml` with `measured = false`; `load_task()` returns `screen-v1`, a product run always loads the default and has no field to choose another (the run body refuses one), and only `prompt-gate measure --task-version screen-v2` loads it. `measure --not-reported decisive_first` re-derives the same answers under that rule offline; without the option the measurement derives under the measured workspace's rule in force (amendments included; review F5). **Waiting for the researcher's approval of the spend (nothing was run):** `uv run nexus-scholar prompt-gate measure --model claude-haiku-5-5 --task-version screen-v2 --not-reported decisive_first --yes` on the frozen 1,644-record set (dry run, prices as of 2026-11-11: expected $0.40, hard ceiling $1.83; with Opus 5.5 $11.42, ceiling $73.31). A comparison with `screen-v1` under the same rule needs a second run without `--task-version` (expected $0.38 on Haiku): the M9a reports of 2026-11-19 keep each record's outcome, not the agent's answers, so they cannot be re-derived. Making `screen-v2` the default is a separate decision after the measurement.

**Lane RELEASE** (`test_gate_policy.md`): a protocol schema value, new public routes and refusal codes, additive public fields (`settings`, the draft view, the run view, the setup) and a new persisted record (`audit/method_amendments.jsonl`).

## 2026-11-20 — Six open decisions settled by the researcher (accepted 2026-11-20)

The researcher answered these in the main session on 2026-11-20. Each one closes a row of the open-decisions table above, except item 4.

1. **Which provider key is used (H-key-precedence, PR #255):** items 1 to 5 accepted as built. A key set in the environment wins over one saved in the keychain.
2. **The size estimate counts arXiv as exact when years are set (M10b Part D, item 4).** Since M3h-c arXiv applies the year window itself, so its count is no longer an upper limit. The estimate and its note still say "upper limit" at `f6ddafac`: a small fix, not yet built.
3. **The M1b-2 prompt gate is met, on recall only.** The API route was measured on 2026-11-19 (M9a): include-recall lower bounds of 93.1% (Opus 5.5), 93.6% (Sonnet 5.5) and 96.8% (Haiku 5.5) against the bar of 0.90. The gate says nothing about the share of the researcher's excludes an agent takes; that is M9a item 2.
4. **M9a item 2: the minimum share of excludes is set when M9b is built.** Nothing uses the number before then. Measured shares: 6.4% (Opus), 1.7% (Sonnet), 1.9% (Haiku); no rung unlocks today.
5. **H-quota-hang item 3: "not checked" stays outside Contract v1.** The marks live in `literature/verification_checks.json`. A corpus whose checks did not finish cannot be handed off, so no accepted snapshot holds such a record. The contract question is closed; no contract change is planned.
6. **M3h-c item 1 accepted: the fixed bounds for an open-ended year range work.** Checked against arXiv on 2026-11-20 with three direct requests for `(all:weed AND all:multispectral)`: `submittedDate:[202401010000 TO 999912312359]` returned 11 results, `[199101010000 TO 202312312359]` returned 3, and the query without a date returned 14. The project's own check (`scripts/record_golden_recon_arxiv.py --check-open-ended`) was not used, because it needs the contact address from the environment.

The Inception redesign decisions (D1 to D15) were settled the same day and are recorded with the proposal on `dev/ux/inception-redesign` (not on `main`): direction A, quick fixes first, the Shape and Criteria part before Explore and Direction, and no larger build until the current review is screened.

## 2026-11-20 — H-quota-hang: a used-up quota ends the checks with a message; only the unchecked records are checked again (items 1 to 9 accepted by the researcher 2026-11-20, as built; the contract question in item 3 closed the same day: it stays outside the contract; H-quota-hang)

Record: `docs/roadmap/milestones/H-quota-hang.md`. Found by the acceptance run of 2026-11-20 (`docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md` on `dev/docs/acceptance-run-sensor-stress`, findings 12, 15, 16): OpenAlex answered 429 with `Retry-After: 50000` during "Checks", each record cost three 60 s waits, the screen said "Preparing", and the stop was read only between stages. Contract v1 baseline current before and after; no schema, model, identity algorithm or fixture changes.

1. **A `Retry-After` longer than the 60 s the client already capped its wait at is a closed door, not a throttle.** `AcademicHttpClient.get` and `.post` do not retry such an answer: a 429 raises `QuotaExhaustedError`, a 5xx `ProviderPausedError`, both carrying the database's name (from the request's host), the wait and the reset time (UTC). A shorter `Retry-After`, and an answer without one, keep today's behaviour; an HTTP-date `Retry-After` is now read too. Before, the POST loop slept the whole `Retry-After` with no cap. `QuotaExhaustedError` is still a `RateLimitExceededError`, so a search leg keeps the code `PROVIDER_RATE_LIMITED` (no new leg code); its message names the reset. *Alternatives:* a separate, longer threshold (5 minutes); not chosen, because the 60 s cap is the longest the client ever waited.
2. **The checks stop asking a database for the rest of the batch once it says its quota is used up; nothing is remembered beyond the batch.** Another batch, Explore, a search leg or a later run asks again and is refused once more (one request each). *Alternative:* a process-wide pause per host until the reset time; not chosen, because a long-running console would keep refusing after the researcher changes the key, and every other caller would change behaviour too.
3. **A record the checks could not finish is kept as it was found and marked, never dropped and never marked verified.** Per record: `NOT_CHECKED` when no lookup confirmed it and a paused database was not asked (never `UNVERIFIED`: no database said it does not exist); a record Crossref confirmed whose OpenAlex enrichment was not done stays `VERIFIED` with `not_done: ["enrichment"]`; `DOI_TITLE_MISMATCH` keeps its code. Reasons: `PROVIDER_QUOTA_EXHAUSTED`, `PROVIDER_UNAVAILABLE_UNTIL`, `STOPPED_BY_RESEARCHER`. The marks are written to a new run record, `literature/verification_checks.json` (one row per record: workspace id, code, `not_done`, reason), beside `verified.json`. **No Contract v1 field is added or changed**: the snapshot does not read this file. Fact found on the way: before this fix the verification stage discarded the verifier's per-record verdict, and `verified.json` already held every identified record, verified or not; the checks file is the first place the verdict is kept. *Open question, not decided here:* whether the corpus snapshot should carry a per-record check status (a contract decision).
4. **A preparation whose checks ended early is unfinished: the Hand-off and `accept-corpus` refuse it until it is finished.** `verified.json` is written with every record, the run's marker ends `INCOMPLETE` and the run view's `preparation.state` is `incomplete`, with `checks: {unchecked, unverified, unenriched, records, reason, paused[]}`; the two kinds are counted and said apart (`unverified`: no lookup could confirm the record; `unenriched`: confirmed, its missing abstract, venue or counts not filled in). The accept answers `PREPARATION_UNFINISHED` as for any unfinished preparation, on the Hand-off and now also in the CLI's `accept-corpus` (review F2: before, it never asked, so it would have frozen an `incomplete` run's records; it now refuses any unfinished search run, which also stops it freezing an earlier run's `verified.json` after a failed or stopped run). **Question for the researcher:** should a gap that is *only* enrichment (every record confirmed, `unverified` 0) block the Hand-off? As built it does, so a corpus Crossref fully confirmed waits for OpenAlex's reset only to fill in details, while the same gap in the abstracts stage blocks nothing. *Alternatives:* (a) block only on `unverified` (or a stop), and let an enrichment-only gap through with a note; (b) let the researcher accept any `incomplete` corpus after a warning. Neither chosen without the researcher's word.
5. **A stop during the checks also ends `incomplete`, keeping the records already checked** (before, a stop was read only before a stage, and a stop before verification kept nothing of it). The job ends `cancelled`, as a stop always did.
6. **"Finish preparing this corpus" after an `incomplete` end checks only the records left**, from `verified.json`, without running duplicates or abstracts again; the checked rows are kept as they are. When the checks file does not match `verified.json` row for row, or a row was refused into `verified_unresolved.json`, the preparation runs again from the saved records as before (no guess).
7. **How it is said.** The engine writes one English sentence (database, reset time in UTC, "N of M records were not checked", what to do), shown as the engine's message. The Harvest card and the Hand-off build the same facts from `preparation.checks` in en/fr/ar, with the reset time in the researcher's own clock (`localStamp`, decision H-ui-findings F6). The job of a quota stop ends `succeeded` with result status `INCOMPLETE`: the run's state, not the job, carries the message; no refusal code is added. The next-step bar keeps its four kinds: a used-up quota reads `failed` at "verifying" with reason `PROVIDER_QUOTA_EXHAUSTED` and the engine's sentence, a stop reads `stopped`. The CLI `run` panel gets an `INCOMPLETE` headline and the sentence. *Alternative:* a new bar kind `incomplete` and a refusal code; not chosen, it would touch the bar's table, the refusal registry and their copy.
8. **A pause and a stop hold for one batch** (`process_batch` resets them), and a used-up Crossref quota during the title search pauses Crossref too (`validate_reference` used to swallow it, so a record without a DOI read `UNVERIFIED`; review F4). A `Retry-After` beyond one year (or infinite) is read as one year; an unreadable one (`nan`) as absent (review F5).
9. **Lane RELEASE** (`test_gate_policy.md`): a new public state value (`incomplete`), an additive public field (`preparation.checks`) and a new persisted run record. The task was given as STANDARD "unless the policy says otherwise"; it does.

## 2026-11-20 — H-provenance-s2: a verifying lookup never replaces a record; the shorten advice per database (items 1 to 4 accepted by the researcher 2026-11-20, "accept decisions 1-4"; H-provenance-s2)

Record: `docs/roadmap/milestones/H-provenance-s2-2026-11-20.md`. Contract v1 baseline current before and after; no schema, identity algorithm or fixture changes.

1. **Verification confirms and fills; it never replaces.** A record confirmed by a Crossref or OpenAlex lookup (DOI, arXiv id or title) keeps its `provider`, `provider_id`, `sources`, `workspace_id` and every field it has; the lookup fills only what is missing. A non-empty identifier is never overwritten; a missing DOI is still filled from a title match. The lookup is not added to `sources` (it did not find the work in a search). *Alternative:* keep the lookup's metadata (Crossref's title, authors, venue) and carry over only the provenance fields; not chosen, because the record in `verified.json` would then not be what any searched database returned.
2. **Consequence accepted with item 1:** a corpus snapshot built from a run verified after this fix has other `REC-`/`STU-`/`COR-` ids than one built from the same harvest before it (the record identity hashes provider, provider id, title and year). Accepted snapshots in existing workspaces are not rewritten; a workspace accepted before the fix keeps the wrong attribution until it is harvested again.
3. **Each recon leg carries `shorten`**, decided by the engine with the existing word rule (keyword query, no `OR`, three or more words) for a leg that answered with nothing; Explore's list of the latest search shows the existing sentence on that leg. The failed-search card keeps giving it once. *Alternative:* a database-specific sentence for Semantic Scholar and arXiv only (whose searches need every word); not chosen, no new copy.
4. **A Semantic Scholar 200 answer with neither `total` nor `data` fails the leg** with its message; it is never "0 results".

## 2026-11-20 — Which provider key is used, and saying so (items 1 to 5 accepted by the researcher 2026-11-20, after the merge in PR #255; H-key-precedence-2026-11-20)

Record: `docs/roadmap/milestones/H-key-precedence-2026-11-20.md`. Found by the paid M9a run of 2026-11-19: a valid `ANTHROPIC_API_KEY` was set, `resolve_key` returned an old OS-keychain key first, the provider answered 401 three times, and `keys status` printed only "anthropic: keychain".

1. **An environment variable that is set beats the keychain; the keychain is the default when none is set.** `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` and `GEMINI_API_KEY` (blank counts as unset). Why: the explicit, per-run setting beats the stored default, and the MCP server already worked this way (`_apply_keychain_keys`: "a variable already set wins"; decision 2026-11-04, CORE-17). No earlier decision chose keychain-first: no entry here says it; only the module docstring of `scholar_agent/keys.py` and the title of one test did, citing that same CORE-17 entry, which says the opposite for the server. Not chosen: keeping the keychain first and only warning (the researcher's run shows the warning would have come after a refused paid call), and a `--key-source` option (a second way to say the same thing).
2. **`keys status` names the source in use, the variable, and the key it does not use.** `anthropic: environment (ANTHROPIC_API_KEY; a keychain key also exists and is not used)`, then one line on how to use the keychain key or remove it. When the keychain library is not installed it says that a keychain key cannot be read. It never prints any part of a key. The status object gains `also_in_keychain`; `source` keeps its three values, so the app's `GET /proposals/setup` is unchanged (it now says `environment` where it said `keychain` when both exist).
3. **A 401 is turned into one sentence naming the source of the refused key.** `prompt-gate run` and `prompt-gate measure`, for an exception that carries status 401 (a batch refused at `batches.create`) and for an all-failed run whose first error is a 401: "anthropic refused the key from the environment variable ANTHROPIC_API_KEY …" or "… stored in the OS keychain. Replace it with `nexus-scholar keys set anthropic`, or remove it with `nexus-scholar keys clear anthropic` …". Nothing is retried with the other key (that would spend on a second key the researcher did not choose). Other failures are raised as before. Not changed: the app's run API, which records the provider's per-record error text.
4. **A missing Anthropic SDK is said first.** `drivers.ensure_sdk` (Anthropic only; the other two drivers use httpx) raises one sentence that names `uv sync --extra ai` and the wheel's `uv tool install --force "nexus-scholar[ai]>=<installed version>"`. `prompt-gate run` and `measure` call it before any estimate, "add --yes to spend" line or key lookup; `--dry-run` and `estimate` spend nothing and need no SDK. `make_driver` calls it too, so any caller gets the sentence instead of `ModuleNotFoundError`.
5. **Agent-kit tests never touch the real keychain.** `tests/kits/agent/conftest.py` puts a fake `keyring` and no provider variable in every test there, and stubs `ensure_sdk` (the test environment has no `anthropic`). One console test that depended on the researcher's shell not setting `ANTHROPIC_API_KEY` now removes it.

## 2026-11-19 — M9a: what the measurement says about the ladder gates (proposed by the main session; accepted by the researcher 2026-11-20; the number in item 2 is set when M9b is built; M9a-measure D10)

Record: `docs/roadmap/milestones/M9a-measure.md`, "The measurement (run 2026-11-19)". The screening agent was run on the frozen 1,644-record sample with Opus 5.5, Sonnet 5.5 and Haiku 5.5 ($12.63). Recall lower bounds 93.1%, 93.6% and 96.8%; the agent excludes 6.4%, 1.7% and 1.9% of the researcher's excludes and leaves 67% to 77% of the records Unclear, mostly because the abstract does not report what a criterion asks.

1. **No rung is unlocked on these results.** L1 passes for all three models and L2 for Haiku, but the pass comes from staying undecided, not from deciding well.
2. **A gate needs a second condition besides recall:** a minimum share of the researcher's excludes that the agent takes off the pile, measured on the same calibration. The number is the researcher's to set; all three models are under 7% today.
3. **The "not reported in the abstract" rule is settled before M9b**: either the criteria are worded so an abstract can answer them, or the protocol says what an unreported criterion means at title-and-abstract stage (today it always means Unclear). Then the measurement is repeated.
4. **The draft thresholds (L1 0.90, L2 0.95) stay constants in `measure.py`** until items 2 and 3 are decided.

## 2026-11-19 — M10d: lighter screens, where the guidance spec is silent (items 1 to 12 accepted by the researcher 2026-11-19: 3, 4, 9 and 10 "as recommended", then the others; M10d-lighter-screens)

Record: `docs/roadmap/milestones/M10d-lighter-screens.md`. Spec: `docs/ux/shared/final/03-guidance.md` (FINAL; R8 and its questions 1 to 5 closed by the researcher 2026-11-15, decision 2026-11-15 item 8). The two brand-book exceptions of R8 are built as accepted (an icon-only hint named "About {label}", a neutral dashed "Recommended · {source}" badge) and now have their line in `docs/ux/brand/BRAND_BOOK.md` "Iconography". The items below are the build's choices where the spec is silent or could not be met as written; each took the smaller option. No route, engine, stored field, refusal code or Contract v1 artefact changes; each item is copy or layout and can be reversed in the UI alone.

1. **Split sentences get their own keys.** Where the audit hides one sentence of a two-sentence key, the hidden sentence becomes a key of its own in en, fr and ar (`direction.lede.order`, `handoff.lede.why`); a removed sentence is deleted from the three catalogs (`scope.lede`, `explore.lede`, `explore.tile.size.thinBody`, `direction.none.dir.body`, `shape.lede`, `criteria.lede`, `review.lede`, `done.lede`, `overview.lede`, `plan.lede`, `recall.lede`, `recall.ledeEmpty`, `harvest.lede.ready`, `dedup.lede`, `chase.lede`). A key removed whole stays in the catalogs, unused (`criteria.defaultNo`, `review.direction.skippedBody`, `plan.imports.afterRun`, `recall.legend`, `harvest.stage.corpusNotFrozen`, `handoff.failedNote`, `chase.empty.noSeedsBody`, `import.inReport`, `report.lede`), as M10b left `review.check.*`. *Alternative:* delete them (a catalog-only change).
2. **Keys added after the audit snapshot stay visible.** The audit test needs a row for every catalog key; the keys added by M10b and M10c and those of the screens outside the audit (08 Drafts, 09 Start from a protocol), about 240 in all, get rows marked STAYS, except `shape.planned.hint`, which `04-shape` already names a Hint. Nothing beyond the FINAL audit is hidden. The cost: a whole-namespace row (`sample.*`, `estimate.*`, `start.*`, `import.*`, `imported.*`, `criteria.reason.*`, `criteria.mine.*`) also covers keys added to that namespace later, so for those namespaces a new key no longer fails the audit test until someone audits it (narrowing them to per-key rows is the alternative). Candidates for a later pass are named in the rows (`sample.left.help`, `criteria.reason.hasPhrases`/`noPhrases`, `criteria.mine.descriptionHelp`, five `estimate.*` helps).
3. **Two screens over the hint budget (B4 = 6), as named exceptions in `density.budget.test.tsx`; this changes the researcher's question 5 answer, so it needs the researcher's word.** Explore with a pool shows 9 hint buttons (its search controls, mode, query and order, are repeated for a new search) and Plan shows 7 (one per key line under Limits). *Options:* (a) fold Explore's repeated search controls behind a "Search settings" section in the pool state (brings it to 6; a layout change the spec does not draw) and accept 7 on Plan; (b) raise B4 for these two screens in the spec and the test; (c) leave as built. *Recommended:* (a), after the researcher has tried Explore with real data (question 3). **Accepted by the researcher 2026-11-19 ("accept decisions 3, 4, 9 and 10 as recommended").** Option (a): Explore's repeated search controls are folded behind "Search settings" in the pool state after the researcher has tried Explore with real data (question 3); until then Explore keeps 9 hint buttons, and Plan keeps 7. The exceptions are written into `03-guidance` rule 5 and the test together (question 5).
4. **Shape's lede is 165 characters**, over B1's 130; it is the sentence the spec's per-screen table chose. The test allows 170 for Shape only; like item 3 this departs from question 5 and needs the researcher's word. *Alternative:* a shorter sentence ("Choose a lens and a playbook; the first research question stays a draft until you use it.", 89 characters), a copy change in three languages. **Accepted by the researcher 2026-11-19 ("accept decisions 3, 4, 9 and 10 as recommended").** As built: Shape's lede stays, B1 allows 170 characters for Shape, written into rule 5.
5. **Where a hint sits when the spec's anchor does not exist.** Recall has no "Not found" column heading: the miss meaning (`recall.mean.one` and `.all`, one panel) is one hint beside its title under the table. Recall's anchor note is a hint on the first anchor row's badge. Direction's order sentence is a hint at the end of the lede. Shape's leaning note is the lens legend's hint, never inside a label (a tap in a label would toggle the radio and the radio's name would include the hint). `harvest.saved`, `chase.gate.record` and `import.rejected.inReport` are hints at the end of their card, which has no heading. The draft hint (`nothingWritten`) is beside "Draft saved" on every step, as I-F2 says.
6. **Two sources the spec's list lacks.** `guidance.recommended.source.estimate` ("size estimate") for the suggested cap, and `guidance.recommended.source.lens` ("matches your lens") for the playbook that matches the lens; the lens itself carries "word scan of your topic", which replaces the old "Leaning · word scan of your topic" label (the mark is its provenance). The suggested cap is marked on Plan as well as Harvest, because both show the same estimate card.
7. **Explore's folds.** Topics and metrics are two folds inside the heuristic-reading card, so the draft label "Heuristic reading · not yet yours" stays above them. The key lines stay outside the "Databases asked" fold (a missing key is a V2 warning). The sample curation's refusal, the empty sample and the Undo toast sit outside the Papers fold. A check's action link opens the folds around its target before focusing it.
8. **One main action.** Plan's "Continue to Recall" and Duplicates' "Continue to the report" become the brand action (M10a's Plan test said neither Plan exit was brand; the 03-guidance per-screen table, written after it, names Continue to Recall). Recall's "Check these seeds" is brand until a check exists, then "Continue to Harvest"; Report's "I reviewed this text" until the text is reviewed, then "Continue to hand-off" (question 4). The discovery proposal card's Apply becomes secondary, as `01-proposals` says (it was built primary in M10c).
9. **The six existing suggestion mechanisms keep their own look** (decision 2026-11-15 item 31 names adopting the proposal card's look as M10d screen work). `03-guidance` does not specify it and it would change controls on four screens; it is deferred to a spec of its own. Decision item 31 (accepted) put it in M10d, so the deferral needs the researcher's word. **Accepted by the researcher 2026-11-19 ("accept decisions 3, 4, 9 and 10 as recommended").** Deferred to a spec of its own.
10. **The why of a Recommended mark (departs from FINAL rule 3; needs the researcher's word).** Rule 3 says the badge is followed by a hint holding the why. Built: Shape's lens has its why on the lens legend's hint (`shape.leaningNote`; a button may not sit inside the radio's label); Explore's semantic mark has no hint of its own, because its why (`explore.mode.help`, "Semantic search matches meaning, not only words.") is the Search mode hint just above it and a second copy would take Explore further over B4; the first fix in Review's "Ready to create?" and the size estimate's cap already carry their own "Why" disclosure on the same row; the playbook's mark sits inside its radio's label. *Alternative:* a hint after every badge (Explore then shows 10 hints). **Accepted by the researcher 2026-11-19 ("accept decisions 3, 4, 9 and 10 as recommended").** As built: no hint of its own after the marks; rule 3 notes it.
11. **Repairs after the independent review (round 1, CHANGES).** The Databases fold names the databases that found nothing in its summary as an unclear badge ("{n} found nothing", new key `guidance.section.zero` in en, fr and ar), as it names failures; the sample's no-reserve line and the offline line move above the Papers fold; Explore's query field has one hint (with no derived query its how-to sentence follows the field's own); the synonym suggestions of Criteria have one hint, on the first concept group drawn (round 2); the fieldsets whose legend holds a hint are named by the legend's words alone (`aria-labelledby`); Recall's hint sits beside "Not found"; a press inside an open hint's panel keeps it open.
12. **Test-only:** one sample-curation test that removes five papers in a row gets a 15 s timeout (1.5 s alone, past 5 s when the full suite runs in parallel), as M10b raised its sibling's wait.

## 2026-11-19 — H-hydration-418: React #418 on every page of the export (accepted by the researcher 2026-11-20; merged in PR #252 before acceptance; H-hydration-418)

Record: `docs/roadmap/milestones/H-hydration-418.md`. Supersedes item 8 of "H-ui-findings" below (the error is now reproduced and its cause found).

1. **A server module takes only components from a `"use client"` module; shared values live in a module with no directive.** The theme boot script moves to `lib/theme-boot.ts`. Imported from the client module, the string reached the page as a module reference, and `<head>` waited for it during hydration. Enforced by `tests/server-client-boundary.test.ts` over `app/`, `components/`, `lib/` and `i18n/` (PascalCase names and default exports count as components; constants in capitals do not). Not chosen: `suppressHydrationWarning` on `<body>` (hides every future mismatch and leaves the client re-render in place), or keeping the import and preloading the chunks (still a race).
2. **The browser suite fails any page that does not hydrate.** The shared `page` fixture in `tests-browser/helpers.ts` collects React #418, #423 and #425 (and the development wording) from page errors and the console and fails the test, as it already does for a non-localhost request.
3. **The race is tested by holding the shell's chunks back**, 800 ms, chosen from the payload's `AppShell` row (`tests-browser/hydration.spec.ts`), alongside a deterministic check that `<head>` in the payload has no reference. The race check is probabilistic in principle (before the fix it reported #418 on several of the six pages in every locale; on the console-served export, 6 of 10 loads); the payload check is not.

## 2026-11-19 — M10c: assistant and critic over MCP (items 1 to 14 accepted by the researcher 2026-11-19, item 9 as option (a); items 15 to 21 accepted 2026-11-19; M10c-assistant-mcp)

Record: `docs/roadmap/milestones/M10c-assistant-mcp.md`. Builds on the decisions of 2026-11-14 (what an assistant may execute) and the M10b specs `docs/ux/shared/final/01-proposals.md` (the `agent:<model>` source reserved for M10c; workspace proposal routes deferred to M10c) and `02-checks.md` ("The slot for M10c"). Each item below is a choice those specs leave open. None changes a Contract v1 model, schema or golden fixture (`generate_contract_baseline.py --check` current before and after D5). The researcher accepted items 1 to 14 on 2026-11-19 ("Go with your recommendations", relayed word for word by the main session with the recommendation: item 9 option (a), the others as written). Items 15 to 21 are the D5 build's choices where item 9(a) is silent; the researcher accepted them on 2026-11-19.

1. **The tools call the engine's code on the files, not the console over HTTP.** As the screening MCP tools do (`nexus_submit_proposal`): the console may not be running, and no launch token is handled by an MCP process. The drafts are found under the workspaces root the console uses (`resolve_root()`); a workspace by its folder.
2. **Who proposed it.** `source: "agent:<model>"`, the model name the client declares (required, `[A-Za-z0-9._:-]{1,64}`; it cannot be verified and is recorded as declared), and `agent: {model, task, task_version}` on the proposal. Tasks: `suggest`, `synonyms`, `translation`, `recall_repair` for proposals, `critic` for findings; `task_version` is `assistant-v1`.
3. **An assistant's proposal is a side write**, checked when it is made: the value is applied to a copy of the draft and run through `parse_draft(saving=True)`, so a suggestion the draft cannot take is refused at once (the existing `DRAFT_INVALID` / `DRAFT_TOO_LARGE` codes in the tool's answer) instead of failing on Apply. `updated_at` does not move.
4. **A finding's locator is a JSON pointer into the intent** (`IntentPacket`): the draft's `build_intent` before genesis, `intent.json` after. One shape for both stages and the critic test set's own. The engine maps it to the step that lists it and to the field the action links to. It must resolve, or name a missing element of a list or object that exists. Two prefixed forms, found while building: `draft:/<field>…` points into a draft's answers (a draft whose criteria are undecided has no intent yet), and `protocol:/…` into a workspace's `protocol.json` (criterion ids exist only there; two variants of the test set are protocol-only).
5. **Where a finding is kept.** On a draft: a side key `assistant_findings` of the draft record (beside `proposals`, `check_dismissals`). On a workspace: `audit/assistant_findings.jsonl`, append-only, with one `ASSISTANT_FINDING_REPORTED` journal row each. This is not a second proposal store: check rows have no store because the fixed checks are computed; an assistant's rows cannot be. Dismissals use the existing record.
6. **Findings are not carried at genesis.** They describe the draft as it was; the critic can be asked again on the workspace. Carrying them would add a file to genesis's `files` (a public preview answer). Revisit if the methods text needs to cite pre-genesis findings.
7. **Limits.** At most 30 open assistant proposals and 50 open findings per draft or workspace (`ASSISTANT_LIMIT_REACHED` in the tool's answer); a decided or dismissed one does not count. Still no "Apply all" (M10b R2, revisited here: the limit keeps the volume reviewable one card at a time).
8. **Severity to level.** `critical` and `major` are `warning`, `minor` is `note`; an assistant's row is never a `blocker` and never changes `ready` (02-checks: a blocker is an existing refusal).
9. **Proposals on a workspace (after genesis): the open choice.** M9d's recall repair, and synonyms once the protocol exists, are changes to the protocol after genesis; the app has no route that edits a workspace's protocol except a replacement genesis, which archives the corpus.
   - (a) **Chosen (accepted 2026-11-19), built in D5.** Workspace proposals are lines in the workspace's existing `audit/proposals.jsonl` (`target.kind: "workspace"`, the reserved value), listed as cards on Discovery Plan. Apply amends the search fields only (a concept's synonyms, a new concept, start and end year, languages) in `intent.json` and recompiles `protocol.json` with the compiler genesis uses; it journals `PROPOSAL_DECIDED` and `PROTOCOL_AMENDED`; the fingerprint moves and the existing protocol-change signals show it. Refused once a corpus is accepted (`_frozen`) or while a search runs. A proposal is stale when the protocol fingerprint is not the one it was made against (copy key `proposals.stale.protocol`, kept for this). New console routes, refusal codes and a Plan card list: the largest part of the milestone.
   - (b) No protocol edit after genesis: Apply of a workspace proposal starts a new draft from the workspace's protocol (M10b Part A) with the change applied, ending in a replacement genesis. No new protocol write; costs the researcher a re-inception per change.
   - (c) Defer: after genesis the assistant reports findings only (recall repair and translation alternatives as findings naming the change); synonyms are proposals only before genesis. Smallest; M9d's "as proposals" is then met before genesis only.
10. **One lock across processes.** `DraftStore` writes take an OS file lock on the draft (the `msvcrt` / `fcntl` pattern of `screening/events.py`) inside the thread lock, because the MCP server is a second process writing the same record.
11. **The existing recon tools.** `recon_probe` and `recon_delta` refuse a `session_id` that names a draft of the app (`RECON_SESSION_IS_A_DRAFT`): a new search for the app's draft changes its sample and can make its direction stale, and decision 2026-11-14 item 3 says a search starts only after the researcher confirms; the app's Explore is where they confirm. A recon session of the assistant's own (the `inception-agent` skill's) is unchanged. The parked tools are unchanged (`nexus_pipeline_run`, `nexus_screen*`): they act on files the researcher names, and their descriptions say they are not production.
12. **The read tools record nothing.** They compute the checks as the app does, without the checks POST's side effect (recording the proposals a check recommends), so a read by an assistant never writes.
13. **Scoring the critic set.** Rule 1(a) of the set's README (the locator) is computed; rule 1(b) ("the same problem") is a judgement left to a human or a separate judge, and the score says which defects were located, not caught. The README's bars stay suggestions for the researcher.
14. **Copy.** A proposal card: "Suggested by an assistant ({model})"; a check row: "Assistant · {model}", the sentence as the assistant wrote it (`dir="auto"`), and "The field changed after this was written." when `outdated`.
15. **(Accepted by the researcher 2026-11-19) The routes are `/api/v1/discovery/proposals…`**, not the `/api/v1/workspaces/{slug}/proposals…` that 01-proposals reserved. The console serves one open workspace (`app.state.workspace`); the `/api/v1/workspaces/` paths answer with none open and would let a request name another folder; the running discovery job that refuses an Apply lives in this console for this workspace. Alternative: the reserved path, refusing any slug but the open one.
16. **(Accepted by the researcher 2026-11-19) Targets are intent fields, and only these:** `core_concepts` (`add` a concept, a name or `{concept, synonyms}`), `core_concepts[<name>].synonyms` (`add`, `remove` one term), `start_year`, `end_year` (`replace`, a year or null), `languages` (`add`, `remove`, `replace`; a protocol left to the playbook's languages starts from the compiled list). No removal of a concept and no edit of the query's operators: the smallest set M9d's three tasks need. Intent names because the locator of a finding is the intent, and Apply writes `intent.json`. *Changed 2026-11-20 by the M11a entry, item 1: a researcher's amendment from Plan replaces the whole concept list (remove, rename, merge), with a required reason; an assistant's proposals keep these targets.*
17. **(Accepted by the researcher 2026-11-19) The guard compares compiled protocols.** Apply recompiles the amended intent and refuses (`PROTOCOL_AMENDMENT_REFUSED`, a new code, `reason: "outside_search"` with the paths) when the result differs from the current `protocol.json` anywhere but `search_strategy.core_concepts`, `.date_range` and `.languages`. So a workspace whose `protocol.json` was edited by hand, or written by an older version (no `method` block, M7-method), is never rewritten by an Apply. The same check runs when the assistant proposes, so such a suggestion is refused before a card shows it.
18. **(Accepted by the researcher 2026-11-19) Apply and Reject only.** No Edit (Plan has no editor for these fields) and no Restore. A stale card (the fingerprint moved) offers only Dismiss, as 01-proposals' stale state. Any Apply moves the fingerprint, so every other open workspace proposal goes stale at once (item 9(a) as accepted); the assistant is asked again on the new protocol. Reject is allowed when stale and after acceptance (it writes nothing but the record).
19. **(Accepted by the researcher 2026-11-19) A backup before each amendment.** `intent.json`, `protocol.json` and `SCREENING_CRITERIA.md` are copied to `audit/amended/<UTC stamp>/`; then the three are written (temp file and replace each), then the `applied` line, then `PROPOSAL_DECIDED` and `PROTOCOL_AMENDED` (old and new fingerprints, changed paths, the backup). A crash after the files and before the line leaves the proposal open and stale, never a half-written protocol. `project.json` and `INDEX.md` change only through the journal rows.
20. **(Accepted by the researcher 2026-11-19) Records and locking.** The assistant's proposal journals `ASSISTANT_PROPOSAL_RECORDED` (like `ASSISTANT_FINDING_REPORTED`); the decisions journal `PROPOSAL_DECIDED` with agent `nexus-scholar/ui`. The console and the MCP server take one lock, `.harness-console/proposals.lock` (git-ignored), through the drafts' lock (item 10, now `drafts.file_lock`).
21. **(Accepted by the researcher 2026-11-19) What a moved fingerprint does to what exists.** An accepted corpus never sees an amendment (Apply refuses `CORPUS_ALREADY_ACCEPTED`). If the protocol is changed by hand after acceptance anyway, the existing signals hold: screening reads `protocol_changed` and earlier decisions count nowhere (decision 2026-11-12, F2), and a resumed run refuses `PROTOCOL_CHANGED_SINCE_SNAPSHOT`. Before acceptance, every earlier search run reads `search_changed` (F3) and its hand-off accept is refused `PROTOCOL_CHANGED_SINCE_RUN`: the researcher searches again. Recall checks and size estimates are keyed by fingerprint, so the earlier ones stop applying. These are the existing behaviours; D5 adds none.

## 2026-11-19 — H-ui-findings: eight UI and build fixes (accepted by the researcher 2026-11-19; H-ui-findings-2026-11-19)

Record: `docs/roadmap/milestones/H-ui-findings-2026-11-19.md`.

1. **Shape's Continue needs a playbook the researcher chose** (finding 2). The spec says the matching playbook is marked, never selected, and gates Continue on a playbook; the build had gated only on the lens. Chosen: gate it (the spec's rule), no auto-selection. Not chosen: selecting the matching playbook when a lens is picked, which the spec rules out ("a machine proposal is a draft, not an answer"). The lede no longer promises that the lens "drafts the playbook".
2. **The criteria check uses the buttons' words, Accept or Reject** (finding 3). The spec's design text says Drop; the built buttons, tests and the "As built" note say Reject; renaming the buttons touches every screen and test. The sentence follows the buttons, and `02-checks` was amended.
3. **Count wording by a table keyed by copy key, with the form chosen by `Intl.PluralRules`** (finding 4). Not chosen: an ICU message library (a new dependency, and the catalog test forbids ICU blocks), or count-neutral wording ("Suggestions: 1"), which reads badly in French and Arabic. The table lists only the forms that differ; a key with no entry keeps its one catalog string. Eight keys are done; the others are in the record's Deferred list.
4. **Unsaved edits mark the old check rows instead of saving for the researcher** (finding 5). Accept on a criterion stays a local edit until the page is saved (`05-criteria`: "saved when you continue"); an auto-save on Accept would change what Undo means and write the draft on every click. Each old row says "Before your changes"; no route added. Apply on a stored suggestion already saves and re-reads the checks.
5. **Engine times print on the researcher's clock**, `YYYY-MM-DD HH:MM`, 24 hours, with the ISO instant in `dateTime` and `title` where the time is a header or a table cell (finding 6). The engine and its files stay UTC. The vitest run pins `TZ=UTC` so the suite does not depend on the machine's zone.
6. **A state card names its state once** (finding 7): the badge that repeated the heading is removed, and the role shows as the card's edge colour and `data-role`. Not chosen: a role word in the badge (a new string in three languages for every role), or hiding the heading (the heading is the card's name in the page outline).
7. **The prefetch 404s are fixed in the export, not in serving and not by turning prefetch off** (finding 9). The files are wrong on Windows builds only (Next writes nested folders); `build:export` flattens them. A serving-side fallback would paper over a bad export for the next consumer of it; turning prefetch off would give up the feature on every platform for a Windows-only fault. The released wheels are built on Linux in CI and were not affected; a wheel built on a Windows PC was.
8. **Finding 8 (hydration error #418 on Explore) is not reproduced and nothing was changed for it.** It needs the exact console line and the browser it appeared in. **Superseded (2026-11-20):** reproduced, explained and fixed by H-hydration-418 (2026-11-19, PR #252).

## 2026-11-18 — M10b Part D: the size estimate, where the spec is silent (17 items, accepted by the researcher 2026-11-18; M10b-proposals-checks Part D)

Record: `docs/roadmap/milestones/M10b-proposals-checks.md` "Part D (size estimate)". Spec: `docs/ux/phase1-discovery/final/01-plan.md` "Size estimate (M10b)" (questions closed by the researcher 2026-11-15: pace 30 s, the limit, the count on a button, nothing recorded). The items below are the building session's choices where the spec is silent or could not be met as written; each took the smaller option. None touches a Contract v1 model, schema or golden fixture (`generate_contract_baseline.py --check` stays current). Each can be reversed without migrating anything: the estimate is never stored.

1. **A recall check's totals are used on the button only.** The spec's Empty state says the card "is instead shown from" a recall check for this protocol, and its acceptance test says the card "sends no request" before a count. Built: nothing is read on load; when the researcher presses "Count what the databases hold", the engine takes each database's total from the newest recall check made for the current protocol fingerprint (`status: from_recall_check`, `recall_check: {check, checked_at}` in the answer) and asks only the databases the check could not answer. Showing the check's totals on load would add one read to every Plan load.
2. **`refresh` in the body.** `POST /discovery/estimate` takes `refresh: bool` (default false; not in the spec's body). "Count again" sends it only when the shown estimate came from a recall check ("Count again to refresh") and neither the cap nor the pace changed since; then the cache and the check are skipped. A what-if (another cap or pace) is answered from the cache, as the spec says. Otherwise "Count again" is answered from the 10-minute cache and asks again only the databases whose count failed (the spec's Partial state).
3. **The cache.** In the console process's memory, per (workspace, protocol fingerprint, the set of databases): the order never changes the estimate, so `[a, b]` and `[b, a]` share it. Only answered counts are kept (`counted`, `from_recall_check`, `not_countable`); a failed one is asked again on the next call, and the entry keeps its first `counted_at` and its first time for `ESTIMATE_TTL`, so a row counted earlier is never shown as counted at the retry and nothing is served more than 10 minutes after its count. `served_from_cache` is true only when no database was asked. A restart of the console empties it.
4. **arXiv is an upper bound only with a year window, and the works low end ignores it.** (Out of date since M3h-c, PR #251: arXiv now applies the year window itself; decided 2026-11-20: its count is exact, see "Six open decisions settled".) The spec makes arXiv's count an upper bound because the year window is applied after retrieval; without a window the count is exact, so `fetch_is_upper_bound` is true only when the query has a year. The works range's low end ("the largest single estimate") is the largest *exact* estimate, so it is never above `records.low`, which already leaves arXiv out.
5. **Four answer fields beyond the spec's shape.** `providers[].not_fetched` (what the cap leaves out, so the browser does no subtraction for "{rest} will not"), `recommendation.cuts` (the `{k}` of "It cuts {k} databases short"), `recall_check`, and `warn.limit {value, source}` (named in the spec's prose, not its shape). Additive.
6. **A changed choice of databases clears the shown estimate.** On Plan, changing the picker returns the card to its empty state ("Count what the databases hold") instead of a separate "out of date" sentence; no new copy key. A changed protocol fingerprint shows the spec's "The protocol changed since this was counted." with no figure.
7. **Offline.** The spec disables the button with "needs the engine on this computer". Built: the refusal card for an unreachable engine (`CONSOLE_UNREACHABLE` from the proxy client, with Try again) above the last estimate, which stays with "As of {time}". The button stays usable, so Try again and the button do the same thing.
8. **"Why this"** is a `<details>` disclosure under the recommendation that holds the warning's reason sentence (`estimate.warn.why.planned` or `.general`), not a separate listing of totals, caps and threshold (the rows above it already print them).
9. **Plan reads the corpus state on load** (`GET /screening/corpus`, one read, no database request) so the card is removed once the corpus is accepted, as the spec asks; before, Plan read only the plan and the runs.
10. **The contact email and the OpenAlex key are required for every estimate**, even one that would be answered from the cache or a recall check: one rule, as for Start (`MAILTO_NOT_SET`, `OPENALEX_KEY_NOT_SET` before any request).
11. **The size limit is read by one function**, `scholar_harness.size_limit.size_limit(workspace)`: `intent.json` `pool_max` as a positive whole number is "stated" (`source: planned`), anything else (null, absent file, unreadable) is the general limit `SIZE_WARN_WORKS` 1,000 (`scholar_search.estimate`). Part B's `HARVEST_ABOVE_TARGET` can call the same function.
12. **The duplicates reference line is not built.** The spec shows "Your last harvest removed {x} % as duplicates" when the workspace has an earlier deduplication, but it also removes the card once a run exists, and a deduplication exists only after a run; the line could never appear. Neither the read nor the copy key is built. If the researcher wants it, the card would need to stay after a run (a spec change).
13. **Copy added beyond the spec's list** (and `estimate.dup.last` dropped, item 12): `estimate.announce.atLeast` (the polite announcement when the upper end is unknown), `estimate.row.details` (the failed row's disclosure), `estimate.row.recall` ("From the recall check" on such a row); `estimate.pace.help` adds "Press Enter to apply it."
14. **A Semantic Scholar count refused with 401 or 403** raises the provider error with the same sentence a leg would carry (`refused_note`), since a count has no leg to put the note on; the row shows it under Details.
15. **"Use {cap} for this harvest" on Harvest** fills the field, marks it "Filled in from the estimate", and moves focus to the cap field; it sends nothing.
16. **A cap typed on Harvest after a count does not mark the estimate out of date.** The shown figures keep the cap they were counted with, and the card's cap line names it ("Cap for this harvest: {value} …" or the protocol's); "Count again" sends the field's number as the what-if and is answered from the cache. Marking the card out of date on every keystroke in the cap field was the larger option.
17. **One database's count is bounded at 45 seconds** (`COUNT_TIMEOUT`, `scholar_search.estimate`). The HTTP client retries a 429 or a 5xx and waits out `Retry-After` (up to 60 s, three times); past 45 s the row is `failed` with `PROVIDER_TIMEOUT`, so a slow database (most likely Semantic Scholar's shared keyless pool) is its own row and never times the whole call out at the proxy's 120 s.

## 2026-11-18 — M9a-measure: one command over the existing prompt gate (accepted 2026-11-18; M9a-measure)

Record: `docs/roadmap/milestones/M9a-measure.md`. Proposed by the build session; the researcher accepted all eight on 2026-11-18 and kept the lane STANDARD; none of it spends anything, and the measurement itself ran on 2026-11-19 after the researcher approved the spend (entry "M9a: what the measurement says about the ladder gates"). None touches a Contract v1 model, schema or golden fixture.

1. **`prompt-gate measure`, built on the gate.** A fifth command of the existing group and one module (`scholar_agent/measure.py`) that calls `prompt_gate` for the set, the text, the drivers, the outcome rule and the cost. No second driver or scorer. Changing it would mean a parallel scorer that can drift from the gate.
2. **Default scope is the gate's frozen sample** (1,644 records: all 644 includes and 1,000 seeded excludes). `--scope all` (14,150) costs about 8.5 times as much and adds only excludes; the ladder gate counts includes. Changing it: pass `--scope all`.
3. **A researcher's Unclear counts as an include** in the score, as the ladder says and `calibration_result` already did (fix to `prompt_gate.score`; the v03 labels have none, so no existing number moves).
4. **A stopped run is not scored.** Records a run never reached (the cost ceiling stopped it) are listed and left out of every figure; a failed call (truncated, refused, invalid, error) is Unclear as in the product and is also shown as a miss in a second, strict recall. The alternative, counting the unreached as Unclear, would inflate recall.
5. **The cost ceiling defaults to 1.5 x the no-caching estimate** ($22.80 for Opus on the frozen sample), checked between chunks of 200 as a product run does; `--cost-ceiling` overrides it. An explicit ceiling below the expected cost is refused before anything is sent, as a product run does. A model without a price is not run by `measure` (a ceiling is always set).
6. **The blind check refuses a figure in the task's own words, and an outcome word in the criteria.** The v03 criteria state a sampling plan ("~10% random sample"), which is review method, not an outcome, so a percentage in the criteria is allowed; a word such as "recall", "precision", "agreement" or "most of these" is not (conservative: a protocol about "precision agriculture" would be refused and the researcher would reword the criterion). Ladder decision of 2026-11-11 and lesson 54.
7. **A gate passes only on a run that measured something**, and it is reported twice: with a failed call as Unclear (the product's rule) and with every failed call as a miss. A run whose calls all failed passes nothing.
8. **The draft thresholds are constants** (`L1` 35 includes and 0.90, `L2` 75 and 0.95) in `measure.py`, evaluated review-wide; per-batch recall is descriptive. M9a decides the final numbers from the measurement and records them here.

## 2026-11-18 — Small fixes 2: gate wheel builds, lock follow-ups, F8 (item 4 accepted 2026-11-18; items 1 to 3 and 5 accepted by the researcher 2026-11-20, after their merge in PR #243; H-small-fixes-2-2026-11-18)

Record: `docs/roadmap/milestones/H-small-fixes-2-2026-11-18.md`. Nothing here changes a Contract v1 model, schema, fixture or baseline; each item can be reverted on its own.

1. **Manifest wheel builds.** The packaging checks (T-90 `pr`, T-110 `inner`) build a UI-less wheel through a shell-independent `uv run python -c` one-liner that sets `NEXUS_WHEEL_ALLOW_NO_UI=1`; the release-grade `closure` stages (T-120 and `area_defaults`) run `npm ci` and `build:export` first, as `ci.yml` does. Alternative: build the export in every case (slower, needs Node for an inner check), or add a wrapper script. The manifest is not covered by the baseline (`--check` current before and after).
2. **Commit-intent deletes wait like the lock's.** `finalize` and recovery delete the intent through `delete_waiting_out_readers` (the old `_delete_lock_file`, renamed, same bounded wait, `WinError 32` only), because `IndexRecovery.inspect` reads it without the lock. An exhausted wait still raises the OS error unchanged (the accepted decision of 2026-11-12 stands). A file already gone now counts as removed instead of raising in the race between the `exists()` check and the delete.
3. **`WorkspaceLock.release()` clears `held` after the delete.** After an exhausted wait the object still holds a lock whose file is there, so a second `release()` retries. The first call still raises; no caller catches it.
4. **(Accepted by the researcher on 2026-11-18.) F8-1 (publish retry journals once) and F8-3 (legacy event ids are distinct).** The publish handler reuses the journal row that already records the same `generation_id` and appends only when there is none, so a first publish whose row could not be written still gets it on retry. `append_legacy_event` now takes the id limb from `uuid4` (like `append_event`) and one clock reading instead of two. The old limb was `hash()` of the text, random per process, so it never matched a fixture and the "HCM-02 parity" it was kept for did not exist across processes; the id shape `EVT-<14 digits>-<6 hex>` is unchanged. Alternative: leave the id alone and document it.
5. **F8-2 (`ARTIFACT_ACCEPTED` once per batch) is not changed.** The rows are the Contract v1 acceptance gate's per-artifact provenance (`contracts/acceptance.py`), and `scripts/check_golden_workspace.py` requires one with `artifact_type == screening_batch`. Collapsing them would be a contract decision; a display-level grouping in the UI would not be.

## 2026-11-18 — M3h-c: the arXiv leg sends its year range (items 1 to 5 accepted by the researcher 2026-11-20; item 1 after a live check of the open-ended range the same day; merged in PR #251 before acceptance; M3h-c-arxiv-date)

Record: `docs/roadmap/milestones/M3h-c-arxiv-date.md`. Builds the half of F16 that decision 2026-11-18 item 2 (M3h-b) deferred; item 2 itself (the researcher re-records the arXiv answers) is accepted. Nothing here touches a Contract v1 artifact, the protocol schema or a protocol fingerprint. All five items below are proposed and wait for the researcher.

1. **The open end of a range takes a fixed bound.** arXiv's range needs both ends. A protocol or a recon call with one year gets `1991` (arXiv's first year) as the start or `9999` as the end: `submittedDate:[202001010000 TO 999912312359]`. Fixed, not "this year", so the request string, the leg record and any recording are the same on any day. The recon probe has no end year by default (`year_min=2000`, `year_max=None`), so this case is the common one in the browser. Unverified live: arXiv's documentation shows only closed ranges, and the golden cassettes are closed (2020 to 2026). Options: (a) **recommended and built:** send the open range, and the researcher checks it with the one extra request in the record's "For the researcher" (step 3; result recorded in the record). If arXiv refuses it, the fix is one constant. (b) Send no clause when a bound is missing and keep filtering after retrieval (the arXiv total then stays an upper bound for these calls). (c) Use the current year as the end: no extra request but the string changes every year.
2. **The local year check stays** as a guard, so a record that slips through is still dropped. Cost: none (the filter is a no-op when arXiv obeyed it). The leg note now reads "arXiv year range sent as a submittedDate filter (<first> to <last> ...); years are also checked after retrieval", and `cannot_express` lists no year line for arXiv any more (the plan shows what is sent in `executed_query`).
3. **Lane STANDARD**, not RELEASE. The diff changes the request one provider sends and what its leg notes say; it changes no Contract v1 semantics, no schema, no artifact identity code and no public API shape (the baseline `--check` is current before and after; no cassette is in the baseline). The pinned golden SCI/REC digests did not move after the re-record (the corpus after the local year guard is the same set), so the cassettes are the only data that changed. The full `pr` gate runs once on the final commit anyway. Overrule to RELEASE if you count a changed arXiv result set as a change to reproducibility.
4. **One recorder for both golden cassettes.** `scripts/record_golden_recon_arxiv.py` (written in M10a for the recon cassette) now records the arXiv leg of the recon probe and of the golden search, splices only the arXiv interactions into each cassette, and writes nothing unless every check passes for both (leg `ok`, a `submittedDate` clause sent, no arXiv error feed, no contact address in the recording, every other interaction byte for byte). Two live requests, both to `export.arxiv.org`.
5. **After the re-record, the pinned digests are checked in the same PR; they did not move.** `GOLDEN_SCI_DIGEST` and `GOLDEN_REC_DIGEST` (`test_golden_search_cassettes.py`) were expected to change because the arXiv answer changes; the replay shows they do not, because arXiv now returns only the in-range records that the local guard used to keep (arXiv entries 44 to 36 in the search cassette, 9 to 6 in the probe). No digest is edited.

## 2026-11-18 — M3h-b: one default database set, shared provider budgets, the leg's auth channel (accepted 2026-11-18; M3h-b-resilience)

Record: `docs/roadmap/milestones/M3h-b-resilience.md`. Findings F14 to F16 of `docs/assessment/three-phase-hardening-2026-11-10.md`. The researcher accepted all seven on 2026-11-18: item 1 as option (a), the four; item 2 as option (a), the researcher re-records the two arXiv interactions later and a follow-up sends the date range; items 3 to 7 as written. Nothing here touches a Contract v1 artifact, the protocol schema or a protocol fingerprint.

1. **F15: one default database set — needs the researcher's choice.** Until now a protocol without `search_strategy.target_databases`, the protocol model's default, the presets and recon used four databases (OpenAlex, Semantic Scholar, Crossref, arXiv), while `SearchEngine()`, a run whose list names no known database, the CLI search without a protocol and the console's "off by default" wording used five (the same plus PubMed).
   - (a) **Recommended and built: the four.** One constant, `scholar_search.models.DEFAULT_DATABASES`, read by the engine, the plan, the protocol adapter, the CLI, recon and the console (one import line and one assignment in `console/api/discovery.py`). The protocol model and the presets keep the same four as literals (the protocol kit does not import the search kit); a test keeps all eleven places equal (`test_provider_resilience.py::test_one_default_database_set`). Why: every protocol made by genesis already names these four (the model's default is written into `protocol.json`), recon uses them, and changing the model default changes protocol identity (see the cost of (b)). What changes: a run whose list names no known database (or `[]`), `SearchEngine()` and `scholar-search search` without a protocol no longer search PubMed; the Plan screen shows PubMed as "off by default", like bioRxiv, and so does the run report's list of databases not searched (it said "not selected in the protocol"); `tests/console/test_discovery_api.py` was updated to this. PubMed stays one tick away in Plan and Harvest (M10a). A protocol that names its databases searches exactly those, in its order (the golden protocol names five and still searches five).
   - (b) The five. Costs: the protocol model's default becomes five, so `src/scholar_protocol/schemas/v1/protocol.schema.json` is regenerated, and the fingerprint (`scholar_protocol.canonical`, which dumps defaults) of every existing `protocol.json` without `target_databases` changes: those workspaces then read "protocol changed" on their runs, hand-off and accept (F3), and a frozen corpus names the old fingerprint — a protocol identity change that needs a contract decision. Recon would ask PubMed in every probe (one more request each, `SCHOLAR_MAILTO` already required). New protocols from genesis would name five.
   - (c) Keep two sets and document them. Not recommended: the finding is that a researcher cannot tell which set runs.
   - Switching from (a) to (b) later costs exactly (b)'s list; from (a) to another list of four or fewer costs one constant and the two literals.
2. **F16: the arXiv date filter is not sent yet — needs the researcher's OK to record.** **Superseded (2026-11-20):** the filter is sent since M3h-c (PR #251). arXiv documents a `submittedDate:[YYYYMMDDTTTT TO YYYYMMDDTTTT]` range in `search_query`. Sending it changes the arXiv request in both golden cassettes (`golden_uav_search.yaml`, `golden_recon_probe.yaml`; both use 2020–2026), which replay only, matched on the query string. This milestone does not re-record (no live calls). Built now: the leg note and the plan's `cannot_express` no longer say arXiv "has no year filter"; they say the filter was not sent and years were filtered after retrieval. Options: (a) **recommended:** the researcher records the two arXiv interactions again with their own `SCHOLAR_MAILTO` (as for M10a item 3), and a follow-up sends the clause, keeps the local year filter as a guard, and re-pins the SCI/REC digests if the arXiv answer moves them; (b) leave arXiv unfiltered and keep the corrected note.
3. **Shared provider budgets.** Semantic Scholar counts a key's 1 request per second across all endpoints, and Crossref counts per contact address, so every client in one process that reaches `api.semanticscholar.org`, `api.crossref.org` or `export.arxiv.org` now waits on one budget per host (`http_client.host_budget`): the search leg, the abstract hydrator (which ran at 10 per second against Semantic Scholar), the harvest's verification stage (`scholar_search.verifier.DocumentVerifier`, whose `/works/{doi}` lookups use the Crossref provider's client) and citation chasing. The post-screening `scholar_verify` kit has its own HTTP client and is not counted (deferred). Rates: Semantic Scholar `SCHOLAR_RATE_LIMIT_S2` (0.9); Crossref two budgets, list requests (query, filter) `SCHOLAR_RATE_LIMIT_CROSSREF` (now 3.0, was 5.0) or 1.0 without a contact address, and single-record lookups `/works/{doi}` (the harvest's verification stage) `SCHOLAR_RATE_LIMIT_CROSSREF_SINGLE` (10.0) or 5.0 without one, so verification is not slowed to the list rate; arXiv one request every 3 seconds. Each client keeps its own limiter as well; the lower wins. A budget reads the configured rate on every request (a contact address set later is honoured). Two processes (the CLI and the console at once) still have a budget each.
4. **Rate-limit headers lower, never raise.** `x-rate-limit-limit` / `x-rate-limit-interval` (Crossref sends `3` / `1s` in its polite pool, recorded 2026-11-08) cap the budget the request used (Crossref list or single-record), or the client's own limiter for a host without one, for the rest of the process, but never below 1 request per second (or the configured rate when that is lower), so a one-off throttle header cannot stall a long-running console; a larger value is ignored, so a header can never push a client above the configured rate. `x-rate-limit-type` is logged. `x-concurrency-limit` is not used: a leg sends one request at a time.
5. **A 4xx answer to a POST is not retried.** `AcademicHttpClient.post` retried every 4xx up to three times; it now retries 429 (with `Retry-After`) and 5xx only, as `get` does. With the hydrator's keyless retry removed, a rejected Semantic Scholar key costs one request where it cost eight, and the hydrator logs that `SCHOLAR_S2_KEY` was rejected and is not retried keyless (as the search leg since M3h-providers).
6. **The leg record.** Each leg gains `endpoint` (the URL, no parameters), `auth` (`key`, `key_rejected`, `mailto`, `none`) and `page_size` (records asked per page; Semantic Scholar's bulk search takes no size and returns up to 1,000, so 1,000); `legs.json` gains `client: {package, version, user_agent}` (the User-Agent without the contact address). The fields are additive: older runs read without them, and no reader requires them. An OpenAlex 409 (spent budget) keeps `auth: key`; only a 401 or 403 with a key sent is `key_rejected`.
7. **The User-Agent** is `nexus-scholar/<installed version>` plus `(mailto:<address>)` when set, read from the installed distribution like the corpus producer's version; it was `scholar-search-kit/0.1.0`. The verify and PDF kits' own User-Agents (`scholar_verify/http_client.py`, `scholar_pdf/acquisition.py`) are outside this milestone (deferred).

## 2026-11-17 — M3i: the harvest stage marker, finishing a preparation, and stop between stages (accepted 2026-11-18; M3i-harvest-robustness)

Record: `docs/roadmap/milestones/M3i-harvest-robustness.md`. The fix itself was accepted on 2026-11-15 (M10b spec answer R5: a stage marker `pipeline.json` with `verified_run`, "Finish preparing this corpus" without a new search, Stop honoured between the stages). The choices below were made while building it; the researcher accepted all ten as written on 2026-11-18 ("accept the decisions"). Each is built as its recommended option, and each names what changing it would cost. None touches a Contract v1 model, schema or golden fixture; `generate_contract_baseline.py --check` stays current.

1. **What the marker holds.** `literature/search_runs/run_NNN/pipeline.json`: `{schema: "nexus.harvest-pipeline.v1", run, stages: {deduplication | hydration | verification: {status, at}}, ended: {status: DONE | FAILED | STOPPED, at, stage, message} | null, verified_run, resumed: [{at, from_stage}]}`. Added to the accepted text: `schema` and `run` (the file says what it is), `ended.stage` and `ended.message` (where it failed or stopped, and the error), `resumed` (each later attempt, so a finished marker does not hide that it was interrupted). The stage names are the engine's own (`deduplication`, `hydration`, `verification`), the same as the job's `stage` events; the M10b bar's words (`deduplicating`, `adding_abstracts`, `verifying`) are a mapping for M10b to make. It is written with the workspace's atomic writer, for every run, browser and CLI: first by the search stage, in the same step that publishes the run and before the run's `legs.json`, so no published run of this version is ever without one (review finding 1: a process that died in between would otherwise read as a run made before the marker, ready with an earlier run's works); then by the pipeline coordinator as each stage ends, before the stage is announced.
2. **`raw_published` keeps its meaning.** The run is still archived as published right after the search (M3a's meaning: its records are `raw_search.json`). The other option, publishing only when verification ends, was not taken: it changes a field older runs and the report already use, and a run that is not published could not be told apart from a stopped search, which is exactly the run that must be finishable. "Ready" is a new fact with its own name (`preparation.state`).
3. **Where finishing starts.** `POST /api/v1/discovery/runs/{run}/prepare` (job kind `prepare`). When the marker says deduplication ended for this run, `dedup/clusters.json` still names this run, and it was made with the deduplication tiers the protocol asks for now, hydration starts from `deduped.json`; otherwise deduplication starts from the run's own `raw.json` (review finding 11). `clusters.json` now names the newest run published as the corpus, which is always the run being deduplicated, not the newest run folder (review finding 2: a later search that was stopped is a newer folder). Hydration keeps no file of its own, so it runs again whenever verification did not end (it only asks for abstracts that are still missing). Not taken: a `hydrated.json` checkpoint per run (one more file to keep in step, for a stage that is safe to repeat). Only the newest published run can be finished (`superseded` otherwise), because `verified.json` has one place.
4. **Reading saved records back.** A new kit function, `scholar_search.models.document_from_record`, rebuilds a record field for field without the constructors' second clean-up, so the finished run writes the same `verified.json`, byte for byte, as an uninterrupted run on the same records (tested). Not taken: the JSON importer, which drops `sources`, `oa_locations` and `topics` and stamps a new retrieval time (the snapshot id depends on it).
5. **Runs made before the marker.** Not guessed. With a `verified.json` they read `ready`, as they always did; without one, `interrupted` at an unknown stage, and they can be finished from `raw.json` (this is the strict run's `run_001`). Consequence: for such a run an earlier run's `verified.json` cannot be detected; the guard in item 7 starts with the first run made after this change.
6. **Stop.** Read before each of the three stages; a stage that is running is never interrupted, so a stop during verification (the last stage) changes nothing and the run ends prepared. A stopped run ends `CANCELLED` (job `cancelled`), marker `STOPPED` at the stage that did not start, and can be finished later. Not done here: running deduplication off the event loop (for a large corpus the console may not answer while it runs; not measured), and interrupting verification between batches. Both are listed as follow-ups.
7. **An unfinished preparation is never accepted.** While the newest published run's marker is not `DONE` with `verified_run` equal to the run, `verified.json` is missing or an earlier run's. Then `corpus_status` reports `from_discovery: false` (so the state is `EMPTY` unless exports are staged), the hand-off counts none of that file's rows, and the hand-off accept refuses `409 PREPARATION_UNFINISHED` with the run, state and stage, both in the route (before `NOTHING_STAGED`) and in `accept_discovery_corpus`. Before this change the accept froze run 1's works under run 2's name. Not guarded: the CLI `nexus-scholar accept-corpus`, which accepts whatever `verified.json` holds by design (M0); guarding it is a separate decision. This is a new refusal on the accept, which is why the lane is RELEASE.
8. **Two refusal codes.** `PREPARATION_UNFINISHED` (the accept) and `PREPARATION_NOT_AVAILABLE` (the finish route; `details.reason`: `not_published`, `superseded`, `already_prepared`, `records_missing`). `AcceptCorpusRefused` gains an optional `details`. `preparation` also carries `cannot_finish` (`corpus_accepted` or `records_missing`) so the screen can say why a run cannot be finished (review finding 3), and `running` is given only to the run a live job is preparing (review finding 6). The M10b spec said "no new refusal code" of its next-step endpoint, not of this fix.
9. **Journal.** A stage that raises after the search now writes one `PIPELINE_RUN_ABORTED` row (status `FAILED`, naming the stage and the run) before the error propagates; before, such a run left no row. A stop writes the same action with status `PARTIAL` (never the search's `SUCCESS`; review finding 5). Each finish attempt writes `HARVEST_PREPARATION_RESUMED` (the run, the stage it starts from, the number of records) and no `DISCOVERY_SEARCH` row.
10. **Screens.** Stop stays on the Harvest screen in every stage, with a line saying it takes effect when the current step ends. "Finish preparing this corpus" is on the Harvest screen only; the Hand-off names the state and links there (the M10b spec's destination). The Import step is unchanged: its accept is disabled without staged exports, and with staged exports it accepts the exports (the unfinished harvest is then left as a record). No screen offers the accept of an unfinished harvest (the Hand-off shows "Not ready"), so the `PREPARATION_UNFINISHED` card is the engine's guard: it appears only if the state changed after the page was read, or for another client of the route. M10b replaces the Import accept with a link to the Hand-off.

## 2026-11-15 — M10b: proposals, checks, next step, start from a protocol (items 1 to 9, R1 to R9, accepted 2026-11-15; items 18, 21, 25 and 26 accepted 2026-11-18; items 27 to 45 accepted 2026-11-19; items 10 to 17, 19, 20, 22 and 23 accepted 2026-11-20; item 24 obsolete; M10b-proposals-checks)

Record: `docs/roadmap/milestones/M10b-proposals-checks.md`. Specs: `docs/ux/shared/final/01-proposals.md` to `04-next-step.md`; inception `02-explore` ("Sample curation (M10b)"), `04-shape`, `05-criteria`, `09-start-from-protocol`; discovery `01-plan` ("Size estimate (M10b)"), `03-harvest`; screening `11-import-corpus` ("Accepting on the Hand-off"). No language model is used in M10b. Items 1 to 9 are the researcher's answers of 2026-11-15 ("accept all"); items 10 and 11 are the writers' recommendations the main session adopted (the researcher may overrule); items 12 to 17 were settled in the spec pass of 2026-11-18, after M10a and M3i merged, and items 19 to 26 after the independent review of the specs the same day (CHANGES, 20 findings); they wait for the researcher, except items 21, 25 and 26, which the researcher accepted as written on 2026-11-18 (Part A is built on them). Item 18 is the researcher's. **Status on 2026-11-20:** the researcher accepted items 10 to 17, 19, 20, 22 and 23 (all built in Parts A to D); item 24 is obsolete (see the item); items 27 to 33 (Part B) and 34 to 45 (Part C) were accepted on 2026-11-19.

1. **Engine suggestions are recorded when accepted (R1).** The six mechanisms that exist today (wizard criteria, pool synonyms, suggested concepts, suggested matrix columns, directions, anchor papers as seeds) keep their fields and adopt the proposal card's look; they are not migrated to the proposal store. When the researcher accepts one, a write-only `engine:<mechanism>` record is kept, so the methods text can name its source.
2. **No "Apply all" in M10b (R2).** Revisit in M10c when the assistant adds volume.
3. **A planned number of records (R3).** Shape gains an optional "How many records do you plan to screen?" (`Draft.pool_min`, `pool_max`), compiled through the intent's existing fields into `target_candidate_pool_size`. The size checks and the estimate compare with it when stated (read from `intent.json`), else with a general limit of 1,000 works. A playbook preset is never treated as the researcher's plan. No protocol schema change.
4. **The proof answer may be empty (R4)** when the draft holds a typed or imported inclusion that is not dropped; then no proof criterion, no template question and no "Convincing evidence" sentence are written. One rule for every draft.
5. **Harvest robustness first (R5).** Built as M3i-harvest-robustness, merged 2026-11-18 (PR #235), before this build.
6. **One place to accept a corpus (R6).** The Hand-off accepts harvests and staged exports; the Import step keeps staging and its preview and links to the Hand-off.
7. **PRISMA exclusion counts stay per criterion id (R7).** The reason category is written into the criteria file and the screening instructions; the PRISMA "excluded, by reason" counts are not regrouped.
8. **Lighter screens (R8).** An icon-only help button and a neutral "Recommended" badge are allowed (two exceptions to the brand book); Explore and Review are folded first. M10d builds it.
9. **A dismissed warning needs one sentence of reason (R9);** a note can be dismissed without one. A dismissal belongs to the evidence it was made on and reopens when that changes; the old dismissal stays in the record.
10. **Proposals and checks (adopted from the writers).** A stale proposal cannot be applied or edited, only dismissed; only a rejected proposal can be restored; ids are content-derived (`prop_` and the check's `evidence_digest`); the new console refusal codes are registered in `console/refusals.py` and `screening-api-contract.md` §7 and documented in `docs/architecture/inception-api.md`, not in the closed `Envelope@1` registry (no contract change; wording made exact on 2026-11-18). Check thresholds are engine constants, calibrated on the golden UAV workspace before they are frozen; a warning never blocks. The inception checks route is a POST (it records the proposal a check recommends, idempotently); the discovery one is a GET. Genesis writes `audit/proposals.jsonl` and `audit/check_dismissals.jsonl`, and marks each applied proposal `in_protocol: true|false`.
11. **Criteria, columns, import, sample, estimate (adopted from the writers).** Reason codes follow `^[A-Z][A-Z0-9_]{2,39}$`; the paradigm default gets a settable reason (`Draft.default_exclusion_reason`), out-of-scope lines get `Draft.out_of_scope_reasons`. Own matrix columns store the whole dimension (seven fields) so an imported protocol's columns survive; the form offers name, description, type and required. Starting from a protocol prefills a new draft (no proposals), leaves the topic empty with "Use research question 1", marks each step "Imported, not yet checked" until visited, and lists what was not carried. Sample exclusions are kept on the draft record (not in the shared pool file), survive a scope change, refill only from records already fetched (`reserve`), and a paper without a DOI is keyed by its pool id. The size estimate counts only on a button, assumes 30 seconds per record (editable), and is not journaled. `project.json` gains `protocol_origin`.
12. **The reserve and the pool marker.** Storing the reserve changes the pool file; the pool's `sample` marker (`POOL_SAMPLE`, M10a decision item 6) becomes `relevance-2`, so a new search of the same question fetches again and stores a reserve. A pool already in a draft's session keeps working without refill and says so. Not taken: keeping `relevance-1` (cached pools would never gain a reserve until a refresh).
13. **The hand-off check follows M3i.** `HANDOFF_VERIFICATION_MISSING` becomes `HANDOFF_PREPARATION_UNFINISHED`, a blocker naming M3i's `PREPARATION_UNFINISHED` refusal, read from the same `preparation` view; its action is "Finish preparing this corpus" when the run can be finished. A running preparation is not a check (the next-step bar says it).
14. **The next-step bar reads M3i's `preparation`.** Rows B to D, G, I and J of the bar's table come from `preparation.state` and `stage` (so they survive a restart); "Finish preparing this corpus" is the button when `can_finish`, with "Search again" as the second link. The engine's stage names map to the bar's words in the builder.
15. **One criteria-reason check.** `05-criteria`'s two working names are the catalogue's `CRITERIA_REASONS_UNIFORM` (two or more accepted exclusions, one shared code). A single accepted exclusion on `OUT_OF_SCOPE` raises nothing.
16. **`protocol_origin` when absent.** A workspace made before M10b has no `protocol_origin`; it is read as `inception`, never guessed to be a placeholder.
17. **The Explore empty-search fixes.** (Refined by item 39.) On an empty first search the "Databases asked" list shows once (the failed-legs list of the refusal card, not a second copy of the latest probe); the "shorten the query" advice shows only when the engine says the empty result followed a keyword query of 3 or more words joined by AND, every leg answering with 0 results (`details.shorten`).
18. **Four PRs (accepted by the researcher, 2026-11-18).** The build ships as Part A (draft answers, start from a protocol), Part B (proposals and checks), Part C (next-step bar, Import link, Explore sample curation and empty-search fixes), Part D (size estimate), in that order; Part D after the search-provider resilience session merges.
19. **The engine-suggestion record rides on the draft save.** No separate record route: the draft `PUT` may carry `accepted_from: [{mechanism, field, value}]`; the engine checks each value against what the mechanism offered for the stored draft (before the save) and writes the `engine:<mechanism>` records in the same write. A value that was not offered, an edited one included, is not recorded and the save still succeeds (`not_recorded`); `PROPOSAL_NOT_OFFERED` is withdrawn. A direction's record is written by the bind.
20. **`SCOPE_TOPIC_LONG` is dropped.** Since M10a the probe sends a keyword query of the topic, or the researcher's edited query, never the topic as written. The catalogue has 50 checks.
21. **One lock and `updated_at` rule for the draft record.** `DraftStore` takes a per-draft lock. A side write (a proposal reject or restore, the checks POST recording proposals, a check dismissal or restore, a step mark) re-reads the record inside the lock, changes only its own key and keeps `updated_at`; an answer write (a draft save, proposal apply or apply-edited, a sample-exclusion change, a bind) checks `base_updated_at` inside the lock and sets a new `updated_at`.
22. **A state for an unfinished search.** (Refined by item 40.) The next-step table gains `SEARCH_UNFINISHED` (a harvest running with no run published yet, or a newest run that is not published: failed or stopped), always with a waiting variant (running, stopped or failed search).
23. **The next-step route is workspace-free and has no ETag.** `GET /api/v1/review/next-step` is added to the console's workspace-free paths and answers `NO_REVIEW` itself; the proxy forwards no `If-None-Match` or `ETag`, so the browser keeps the answer with the newest `computed_at`.
24. **Workspace proposal routes wait for M10c.** M10b creates no workspace proposal, so `/api/v1/workspaces/{slug}/proposals…` is built with M10c's first creator. **Obsolete (2026-11-20):** M10c item 15 (2026-11-19) built them at `/api/v1/discovery/proposals…` instead.
25. **Reason codes are checked on save only.** `parse_draft(saving=True)` on the draft `PUT` and `POST` refuses a code outside `^[A-Z][A-Z0-9_]{2,39}$`; reads, steps, preview and checks do not, so an older draft still opens and shows the code flagged (`reason_valid: false`) until its next save. An imported code outside the rule is normalised and listed, never refused.
26. **Review wording (strict-run findings 7 and 9).** The rationale reads "Convincing evidence: …" and the suggested Sample Size column says "How many were sampled or evaluated (unit of analysis: …)". The placeholder protocol's pinned fingerprint moves once, because its compiled text changes.
27. **The term checks look for acronyms only (Part B calibration, proposed 2026-11-18, accepted by the researcher 2026-11-19).** `CONCEPT_TERM_MISSING` and `PLAN_QUERY_TERM_MISSING` look for all-capitals acronyms of 2 to 6 letters (a plural `s` allowed) in the title, topic and research questions. The spec's second rule, a title word that also occurs in a research question, was run over the golden UAV protocols (`golden-uav-30`, `uav-crop-weed-v03`) before freezing: it flagged only "reliability" and "generalization", the review's outcomes rather than its search words, and no true miss. The acronym rule keeps the 2026-11-13 case (UAV). Revisit when a real miss of a spelled-out word is seen.
28. **Genesis writes the proposal and dismissal records before the GENESIS row (proposed 2026-11-18, accepted by the researcher 2026-11-19).** `audit/proposals.jsonl` and `audit/check_dismissals.jsonl`, with their `PROPOSALS_RECORDED` and `CHECK_DISMISSALS_RECORDED` rows, are written after the protocol files and before the GENESIS row, so GENESIS stays the last row genesis writes (code and tests read it as the last row). A replacement does not archive an empty record (it holds nothing), so a replacement of a workspace with no corpus still reports nothing archived.
29. **The bind's direction record (proposed 2026-11-18, accepted by the researcher 2026-11-19).** Choosing a proposed direction writes one `engine:direction` entry in the bind's own write, with `target.field: "grounding"` (a record key, not a `Draft` field), `op: "replace"` and the direction's label as the value; the researcher's own words and a skip write none (they are not engine suggestions). At genesis `in_protocol` is true when the bound direction still has that label.
30. **Two smaller rules of the proposal store (proposed 2026-11-18, accepted by the researcher 2026-11-19).** `remove` of an element that is no longer there is refused `PROPOSAL_NOT_OPEN` with `details.status: "absent"`, as `add` of one already there is (`"present"`). For `concepts` an element is the same when its name matches ignoring case; a synonym, ignoring case. A reject's optional reason is kept on the proposal as `reason` and on its `rejected` line in `audit/proposals.jsonl`.
31. **What Part B leaves to Part C (proposed 2026-11-18, accepted by the researcher 2026-11-19).** `EXPLORE_SAMPLE_MOSTLY_LEFT_OUT` reads the sample curation of `02-explore`, which Part C builds; until then it is not computed, and `EXPLORE_POOL_THIN` counts the pool's papers. The six existing suggestion mechanisms keep their own look in Part B (they send `accepted_from` with the save; adopting the proposal card's look is screen work for M10d, "lighter screens").
32. **One message key per sentence variant (proposed 2026-11-18, accepted by the researcher 2026-11-19).** A check whose sentence has two variants sends a separate key for the second (`checks.HARVEST_ABOVE_TARGET_general.sentence` and `.why`, the general-limit wording), so the browser picks the text by key and never decides which variant applies.
33. **A proposal card's Edit is an inline editor (Part B, proposed 2026-11-18, accepted by the researcher 2026-11-19).** `01-proposals` says Edit opens the field's normal editor on the screen. The build opens a small editor inside the card (a concept name or a synonym, the only values M10b's one creating check proposes), and "Apply my edit" sends `apply-edited`, which the engine validates as a save of the field. Moving the editor into each screen's own field component is screen work for M10d.
34. **The probe's own count stays on the recon state (Part C, proposed 2026-11-19, accepted by the researcher 2026-11-19).** `GET …/recon` keeps `session.latest.n_docs` as the number of papers the probe stored, so the Explore screen still knows a pool exists when every paper is left out (`02-explore` "Empty" (b)). The effective count is `sample.n_docs` and `distill`'s `pool.n_docs`; `02-explore` "Backend calls" said `n_docs` becomes effective there too.
35. **What "most of the sample" counts (Part C, proposed 2026-11-19, accepted by the researcher 2026-11-19).** `marked_share` is the left-out papers the pool still holds over those papers plus the effective sample: "the papers that were in the sample" read as every paper shown at some point, refills included. Both recommendations can hold at once; `recommend.reason` names the first (`BELOW_FLOOR`) and `recommend.reasons` lists both, and each is its own check row.
36. **Which keys a sample change accepts (Part C, proposed 2026-11-19, accepted by the researcher 2026-11-19).** A paper can be left out only when it is in the sample the screen shows (or is already left out: no change); a paper can be put back when it is left out or in the pool (putting back one that is not left out is no change). Any other key refuses the whole call with `PAPER_UNKNOWN` and changes nothing.
37. **The bind keeps the left-out keys beside their digest (Part C, proposed 2026-11-19, accepted by the researcher 2026-11-19).** `grounding` records `sample_exclusions_keys` with `sample_exclusions_digest`, so genesis reads the concept evidence on the pool as the bind read it (a later change is refused at genesis as `STALE_BINDING`). A grounding bound before Part C counts as bound with nothing left out: any paper left out after it makes it stale (`SAMPLE_CHANGED`).
38. **The gap check reads the pool as stored (Part C, proposed 2026-11-19, accepted by the researcher 2026-11-19).** The gap check (`recon/delta`) is not in `02-explore`'s table of what an excluded paper stops feeding; it still reads the raw pool, and the pool it merges keeps the first pool's reserve (the merge starts from the first pool; corrected after the review of Part C, finding 1). Left-out papers stay left out on the merged pool, since the key is the paper.
39. **When the empty search says "shorten" (Part C, proposed 2026-11-19, accepted by the researcher 2026-11-19).** A "keyword query" is any probe that is not semantic and whose query has no `OR` (with `OR` not every word must appear); words are counted without `AND`, `OR`, `NOT`, quotes and parentheses; a narrower search's label counts like the topic's query. Every database must have answered with no record and none failed.
40. **The next step before any search, and while a job runs (Part C, proposed 2026-11-19, accepted by the researcher 2026-11-19).** Rows 9 and 10 (`SETUP_NEEDED`, `READY_TO_SEARCH`) also need an empty corpus: a review that only imports exports never needs a contact email, and would otherwise read `SETUP_NEEDED` forever. A live harvest or preparation job answers before rows 12 and 13: `SEARCH_UNFINISHED` with variant A while it searches, `CORPUS_PENDING` with B to D while it prepares (the spec's purpose: "when something is running, say that instead").
41. **"Published, then changed" names no number (Part C, proposed 2026-11-19, accepted by the researcher 2026-11-19).** The engine does not count the studies that changed after publication (`GENERATION_STALE` counts changed outputs), so `PUBLISHED_STALE` carries no `{n}` and reads "The screening changed since you published." It answers for every publication status other than `CURRENT` (`STALE`, `MISMATCHED`, `LEGACY_UNVERIFIED`, `SUPERSEDED`), with the status's code in `params.code` for the Publish screen to explain; when the status cannot be read it also adds `publication` to `unknown` (review of Part C, finding 2).
42. **A later round's batches (Part C, proposed 2026-11-19, accepted by the researcher 2026-11-19).** For round 2 and later, an accepted round with no batches answers `ROUND_ACCEPTED` ("Round {round} is with screening. Prepare its batches."); row 16 (`NOT_PREPARED`) is round 1's. In table order row 16 would always match first and row 25 never. Rows 17 to 21 carry `params.round` when the round is above 1.
43. **Two waiting variants the builder does not compute (Part C, proposed 2026-11-19, accepted by the researcher 2026-11-19).** Variant K (`accepting_chase`) is a refusal of the chase accept (`WORKSPACE_JOB_ACTIVE`), shown by the Chase screen; no state leads to it. A running chase job is variant F on the state `PUBLISHED`, whatever the publication state.
44. **The draft's missing fields (Part C, proposed 2026-11-19, accepted by the researcher 2026-11-19).** `DRAFT_INCOMPLETE` sends `params.fields` as a list of field ids (or the check id of a blocker that names no field) and `params.step` as the first of their steps in the order Scope to Review; the browser labels them. When the checks cannot be computed, the answer is `DRAFT_INCOMPLETE` towards Review with `unknown: ["checks"]`, never `DRAFT_READY`.
45. **`PLAN_ESTIMATE_ABOVE_TARGET` stays on the estimate card's own words (Part C, proposed 2026-11-19, accepted by the researcher 2026-11-19).** Wiring the catalogue check to Part D's estimate would replace the card's accepted copy (`estimate.warn.*`, Part D decisions) with the catalogue sentence and change Part D's 24 card tests; the two wordings say the same thing. Which wording wins is a copy decision, left for M10d (lighter screens); until then the card's warning stays as built and the catalogue row stays unserved.

## 2026-11-14 — M10a: where the database choice lives, the probe query, the arXiv cassette (accepted 2026-11-14: 1a, 2a, 3a; items 4 and 6 accepted 2026-11-15)

The researcher chose 1(a), 2(a) and 3(a) in chat on 2026-11-14; for 3(a) the researcher runs the recording command with their own `SCHOLAR_MAILTO`. Record: `docs/roadmap/milestones/M10a-search-quality.md`. None of the options below touches a Contract v1 artifact, the protocol schema or the corpus fingerprint; the recommended ones do not change `protocol.json` at all.

1. **Explore: where the database choice and order live.**
   - (a) **Recommended: on the probe.** `POST .../recon/probe` gains an optional ordered `databases` list and an optional `query` (the researcher's edited keyword query). The probe record, the pool (which already keeps an ordered `providers` and is cached by it) and the grounding's pool summary keep both. The screen pre-fills from the latest probe, so a reload shows the last choice. A different choice is a new pool, so a bound direction becomes stale by the existing fingerprint check. No draft field.
   - (b) A new ordered `databases` field on the draft (`inception/steps.py::Draft`), saved before any probe and part of the scope that makes a binding stale.
   - Either way the Explore choice does **not** become the protocol's `search_strategy.target_databases` in M10a: recon can ask four databases, Discovery six, and the compiled protocol stays as the preset makes it. Carrying it over is a later choice (M10b "start from an existing protocol").
2. **Discovery: where the database choice and order live.**
   - (a) **Recommended: per harvest, the protocol stays the default.** Plan and Harvest offer the protocol's databases in its order, with the others unticked; the researcher may untick, tick and reorder. Plan previews the chosen list (`GET /discovery/plan?providers=…`, a new optional parameter) and hands it to Harvest in the page address; Harvest sends it as `providers` on `POST /discovery/runs`, which the engine already accepts and checks (`_check_providers`). The run's `legs.json` records the list asked for (`requested_providers`, a run record, not a v1 artifact). The report's `not_searched` already names a protocol database that was not searched; it gains the reason "not selected for this harvest". The executed query of each leg (PRISMA-S) keeps its shape. The hand-off gate is unchanged: it compares the protocol's list then and now, never a run's choice (decision 2026-11-12, item 2).
   - (b) Edit `protocol.search_strategy.target_databases`. No schema change, but it changes the protocol fingerprint (every later screen shows "protocol changed") and the browser has no protocol edit route except replace, which archives the corpus.
   - (c) A workspace settings file. Invisible to the drift and accept gates; not recommended.
   - In Discovery the order is the order the legs run and are listed in. It never changes the corpus: deduplication still sorts by `stable_order` (item 1 of the accepted entry below).
3. **The golden recon cassette.** Joining arXiv terms with `AND` changes the arXiv request recorded in `tests/fixtures/cassettes/golden_recon_probe.yaml` (matched on the query string), so its engine replay test fails on the arXiv leg until the arXiv answer is recorded again (the HTTP replay test still passes: it only checks that the pool is partial, which the recorded Semantic Scholar 429 already makes it). The recording command is `scripts/record_golden_recon_arxiv.py`. A pool cached before M10a is not reused: new pools carry a sample marker that a cache hit requires. Editing the recorded URL by hand would put OR results behind an AND request.
   - (a) **Recommended:** record the two arXiv interactions again, live, once, and replace only those in the cassette; the OpenAlex, Crossref and Semantic Scholar interactions stay byte-identical. arXiv is free and takes no key, but the engine refuses to run without `SCHOLAR_MAILTO`, which is sent to the databases: the researcher runs the one command, or approves it being run with their address.
   - (b) Record the whole cassette again (all four databases answer anew; the recorded Semantic Scholar 429 would probably change).
   - (c) Defer the arXiv change to a follow-up milestone.
   - *Outcome (2026-11-15).* The researcher ran the recording command with their own address. arXiv answered the AND query with one page (9 records reported, 6 kept for 2020–2026), so the cassette now holds one arXiv interaction in place of two; the other three interactions are byte-identical and the engine replay test passes.
4. **Decided in the build (accepted 2026-11-15).** "0 results" is derived from a leg that finished with nothing fetched while the database reported no results; no new leg status is added, so `legs.json` and `SearchLeg` keep their shape. The keyword query (`scholar_harness/recon/keywords.py`, the same at the browser, CLI wizard and MCP front doors, topic probe only): the topic is NFC-normalised; words are taken in the topic's order (combining marks belong to the word; internal hyphens, and a zero-width joiner or non-joiner between two letters, are kept); one-letter words, English stopwords and question and framing words are dropped, except upper-case acronyms such as `NO` or `IT`; duplicates are removed; at most six words are kept. A topic with a double quote or any upper-case `AND`/`OR`/`NOT` word (standing alone or next to punctuation, as in `weed (OR crop)`; not inside a hyphenated word such as `NOT-gate`) is already a query and is sent as written; parentheses alone are not. A keyworded query never holds an operator word. Known limits, accepted for this milestone and shown by tests: six words in topic order can cut the subject of a long question ("How does on-device inference of lightweight CNN models affect real-time weed detection accuracy …" keeps `on-device inference lightweight CNN models real-time`), and the stopwords are English, so a French topic keeps its function words. That is why the screen shows the query each database received, says "0 results", and lets the researcher edit the query and search again; better suggestions are M10c's assistant.
5. **Spec questions closed by the researcher (2026-11-14).** Explore pre-fills the query field with the engine's derived query and offers "Use the derived query" after an edit. The Plan picker's choice reaches Harvest in the page address; Harvest sends `providers` only when the researcher touched the picker or the address carried a choice. A choice that differs from the protocol, including by order alone, is named on the screen and never refused. The plan returns the protocol's own list; Chase also says "0 results".
6. **Decided in the review rounds (accepted 2026-11-15).** These follow from 1a and 2a and close gaps the adversarial reviews found.
   - *Which databases a narrower search and the gap check ask.* The databases of the pool they narrow or extend (its recorded `providers`); for a pool stored before M10a, the list of the latest probe that found records, else the four defaults (a probe that found nothing never became the pool, so it never counts). So the probe record, the merged pool and the grounding copy name the same list, and an empty probe with another list does not redirect them. A gap check on a pool stored before M10a writes that list onto the merged pool, so even one with no follow-up makes a new pool file and a direction bound to the old one reads `POOL_CHANGED`.
   - *A query that differs only in letter case, spacing or trailing punctuation* shares a recon cache key (the key normalises them) but is searched again, because Semantic Scholar and arXiv read `AND`/`OR`/`NOT` only in capitals; each probe's recorded query equals its pool's. The cache key is unchanged.
   - *Database names.* Recon takes exact ids (the screen sends ids); Discovery keeps its existing case- and alias-tolerant names. Both refuse with `PROVIDER_UNKNOWN`; recon also refuses a repeated id, while Discovery removes repeats and keeps the first order (on plan, run, recall and chase; a repeat used to run that database twice).
   - *`protocol_providers`* is exactly the list a run sent no `providers` searches: the adapter default when the protocol names none, the engine's default suite for an explicit empty list, never a name the run would drop, each name once. The OpenAlex key check and the recall check read the same list, so a protocol with an explicit empty list now has its OpenAlex leg checked for the key, and its recall check searches the engine's defaults instead of none.
   - *Explore's query field after the question changes* is filled with the new derived query, never the old topic's keywords; otherwise it shows the latest topic probe's query (a narrower probe's label is a direction, not a topic query).
   - *The pool's sample marker* is versioned (`relevance-1`); it changes whenever the sampling rule or a database's translation changes, so older cached pools are fetched again.
   - *PRISMA-S.* `search_report.md` and the methods paragraph name the protocol databases left out of a run that chose its databases.

## 2026-11-14 — Assisted inception: five milestones, database order, assistant limits (accepted 2026-11-14)

After the strict run of 2026-11-13, where Explore returned nothing useful and the researcher typed every inception answer by hand, the researcher approved the "Assisted inception" sequence (plan §6): M10a search quality and database choice, M10b proposals and checks, M10c assistant and critic over MCP, M10d lighter screens, M10e an in-app chat panel.

1. **The database order is sample priority only.** The researcher's database order decides which papers fill the Explore sample. It does not change which record represents a group of duplicates: that rule feeds the corpus fingerprint, and changing it would be a contract decision of its own.
2. **The in-app chat comes after the MCP version.** M10e follows M10c and waits for the researcher's approval of the AI spend.
3. **What an assistant may execute.** It reads and explains anything freely; it starts a search or a harvest only after the researcher confirms; its protocol edits arrive as proposals; it never accepts a corpus, makes a screening decision or publishes.
4. **The full sequence is built, in the order above.**

## 2026-11-12 — Releasing the index workspace lock waits out a file in use; an exhausted wait stays an OS error (accepted 2026-11-12; PR #230)

Found by a full-suite run on Windows: `test_two_runs_on_one_workspace_are_mutually_exclusive` failed once because `WorkspaceLock.release()` (`src/scholar_rag/replacement.py`) raised `PermissionError` (WinError 32). A refused second run reads the lock file to name its holder; Windows refuses to delete a file another handle has open, so the holder's delete failed after its replacement had completed and the lock file stayed behind.

1. **The delete is tried again, a bounded number of times.** Only `ERROR_SHARING_VIOLATION` is treated as transient: `LOCK_RELEASE_ATTEMPTS` (200) tries, `LOCK_RELEASE_RETRY_INTERVAL_SECONDS` (0.01 s) apart, about two seconds at most. No clock is read, in keeping with 7.4 ("never reads a timestamp"). A file that is already gone is a released lock. Any other failure is raised on the first try. The recovery store's release takes the same path.
2. **An exhausted wait is not a typed refusal.** By the time a run releases, it has published or refused. A typed `ReplacementError` from `release()` would travel back as a `REFUSED` result for a replacement that committed, which is a contract change (4.5 and 6.5 close the codes and the result model). So the operating system's error is raised unchanged, as before this change, and the file left behind is an orphan lock, which 7.4 already refuses like a live holder. The researcher accepted this as it is on 2026-11-12, so that case keeps no outcome of its own. What a caller sees today, unchanged by this fix: `IndexReplacement.run` raises the `PermissionError`; the index service (`src/scholar_rag/index_service.py`) reports the run as `FAILED`, naming only the error type, with no journal row; recovery is then refused `CONFLICT` by the orphan lock, so an operator has to delete the lock file by hand. The same single delete is now used when a lock's holder cannot be recorded (`acquire`'s failure path).
3. **Not covered here (follow-up).** The commit-intent deletes in `replacement.py` and `recovery.py` can meet the unlocked reader `IndexRecovery.inspect` the same way, and `release()` clears its held flag before the delete, so a second `release()` after an exhausted wait does nothing. Both predate this change.

No Contract v1 schema, code or baseline file changes. Tests: `tests/kits/rag/test_index_replacement.py` (a simulated file in use on every platform, a real open handle on Windows, the bounded wait, and no retry for another fault).

## 2026-11-12 — Protocol-change signals are flags; the hand-off accept refuses a changed search only (accepted 2026-11-12; H-protocol-signals, PR #228)

Fixes F2, F3 and F4 of the three-phase review (`docs/assessment/three-phase-hardening-2026-11-10.md`). Record: `docs/roadmap/milestones/H-protocol-signals.md`.

1. **Screening after a protocol edit is a flag, not a refusal (F2).** `GET /screening/summary` and `GET /screening/queue` carry `protocol_changed: true` when a batch of the current round was prepared under another protocol than `protocol.json` now (each batch envelope's `protocol_fingerprint` against the current canonical fingerprint); Screening Home shows the `PROTOCOL_CHANGED_SINCE_BATCH` card ("The protocol changed after screening started") with a link to Inception, and no triage button. The refusal option (`PROTOCOL_CHANGED_SINCE_BATCH` as a 409 on both reads) was not taken: the reads would stop answering while nothing was lost, the record view and conflicts still need them, and the existing behaviour that a decision bound to the current protocol is accepted stays as it was. The code is a UI state, so it is not added to `console/refusals.py`. `/prisma/preview`'s `bound_to_current_protocol` is no longer vacuous: false with no decision, and false when a current batch was prepared under another protocol. Recovery is undoing the edit, or replacing the protocol through Inception (M4d archives the screening and starts clean); Prepare cannot rebind batches because it refuses a protocol that differs from the accepted corpus's. Batches of an archived M3g round are not current, so they never raise the flag.
2. **The hand-off accept refuses a changed search, and flags any other edit (F3).** Every search run records `protocol_fingerprint` and `protocol_search` (query text, year window, language, retrieval cap, database list) in `legs.json`. `GET /discovery/runs` items and `GET /discovery/handoff` carry `protocol_changed` (the fingerprint differs) and `search_changed` (the compiled search differs). `PROTOCOL_CHANGED_SINCE_RUN` is widened from the query and years to the whole compiled search, because a change to the protocol's database list, language or cap since the run means the protocol now asks for a search the run did not do (the gate compares the protocol's list then and now, not the databases a browser run chose to search). The database list is recorded only when the protocol names one, and only the keys both records hold are compared, so a later change of the adapter's default list (F15) or a key added to the record never reads as an edit. An edit outside the search (criteria, title, research questions) is flagged but does not refuse: the records still answer the protocol's search, the accept binds them to the protocol as it is now, and no screening exists yet that the edit could invalidate; refusing would force a new harvest for a wording change. A run written before this change has no record, so its query and years decide as before. Not a Contract v1 change: `legs.json` is a run record, not a v1 artifact.
3. **The corpus view of a search corpus (F4).** `GET /screening/corpus` gains `origin`; for a browser harvest `databases` comes from the corpus run's legs and `preview` from the legs' fetched counts and `deduped.json`; in an M3g citation-searching round `origin` is `"citation_searching"` and `preview` is the chase's counts, while `databases` stays the staged exports' rows (none when round 1 was a browser harvest; the run's rows are not repeated there) and `from_discovery` keeps its value: citation searching is not a database search (PRISMA 2020 reports it under other methods) and the chase screen lists its legs. Screening Home's "imported" line shows only when `origin` is `imports`. The response keeps its keys and adds `origin` and three keys on a database row.

## 2026-11-12 — Input limits for drafts and decision events; one envelope for validation errors (accepted 2026-11-12; H-input-limits, PR #226)

Fixes F5, F6 and F7 of the three-phase review (`docs/assessment/three-phase-hardening-2026-11-10.md`). Record: `docs/roadmap/milestones/H-input-limits.md`.

1. **Every refusal carries a code (F5).** A body, query or path parameter pydantic refuses, on any console route, answers 422 `BODY_INVALID` in the refusal envelope with `details.errors[]` (`loc`, `msg`, `type`), never FastAPI's bare error list, and never the client's own value (`input`), which may be the oversized one. The UI shows one card for it with the engine's reason under it.
2. **Draft size limits (F6).** The limits live on the draft shape (`inception/steps.py`, `DRAFT_LIMITS`), not on the console body, so every route that parses a draft (create, save, steps, preview, genesis, recon) refuses the same way. They are generous for a real review and match the discovery note's 2 000 characters: 2 000 characters for each free-text answer (topic, unit of analysis, proof, title, each research question, each scope exclusion, each extra criterion); 200 for each name or label (researcher, venue, concept, synonym, matrix column, criterion id, lens, playbook, language tag); 20 research questions; 50 concepts with 50 synonyms each; 50 items in each of `out_of_scope`, `extra_inclusions`, `extra_exclusions`, `matrix_columns`; 500 criterion decisions; 20 languages; 25 seeds (the Recall limit, already in place). A draft over them is refused `DRAFT_TOO_LARGE` (422) and nothing is saved; a shape error in the same body is listed too. A draft saved before this change still loads; it is checked when it is next saved, stepped or previewed.
3. **Decision events (F7).** Intake refuses a `decided_at` more than 5 minutes ahead of the engine's own `received_at` as `PROVENANCE_MISSING` (a device clock may run a little fast, a year cannot; the event's own time is still what is stored and projected), a `device` that is not the token's scope as `INVALID_OUTPUT` (a desktop token sends `desktop`, a phone token `phone`; the alternative of overwriting `device` from the scope was not taken because the client's claim is kept as a claim, never rewritten), and a `note` that is not text or is over 2 000 characters as `INVALID_OUTPUT`. No new code was added for F7; the two existing codes cover it. The F7 limits apply to new events only: a retry of an event stored before them is still a `duplicate`. The researcher decided on 2026-11-12 that the note cap applies only to new client input: a note equal to the stored note of the event it supersedes is a copy and skips the cap, so resolving a conflict that keeps a note written before the cap succeeds and keeps the note whole (never truncated). Not a Contract v1 change: the decision event is not a v1 artifact.

## 2026-11-12 — Citation chasing: one level, capped forward legs, both directions, a second screening round (accepted; M3g-citation-chasing)

The researcher took the four recommended options on 2026-11-11 ("confirm all four as recommended"), relayed by the coordinating session; the stated defaults stand with them. Record: `docs/roadmap/milestones/M3g-citation-chasing.md`.

1. **One level per chase run.** The seeds are the published includes (`literature/included.json`, decision `INCLUDE`; `--seeds included+unclear` adds the `MAYBE` ones); what the chase finds is screened, never chased again in the same run. Chasing a later round's includes is the same command again, so saturation is reached deliberately and each round is reported. The kit's multi-hop `CitationChainer` stays a kit tool.
2. **Caps.** References (backward) are uncapped: a paper cites a bounded list. Citing papers (forward) are capped at 500 per seed and database; a leg that reaches the cap records `cap_hit` and is reported as a lower bound, as a harvest leg is. The run keeps at most 5,000 new records after deduplication; beyond that it is `PARTIAL` with a note naming how many were not kept. The protocol's year window is applied before screening and the removed count is reported (`outside_year_window`), because the frozen protocol makes the window an exclusion anyway (lesson 47). A record without a year is kept for screening.
3. **Both directions by default**, `--directions forward|backward` to restrict. OpenAlex is asked first, Semantic Scholar second, for every seed; the union is deduplicated. A seed is asked by its own id (OpenAlex work id, Semantic Scholar id, or `DOI:` on Semantic Scholar); a seed known only by DOI costs one OpenAlex lookup; a seed with no DOI and no database id is listed as not chaseable, never guessed (lesson 2).
4. **A chased batch is a second screening round, never an addition to the frozen snapshot.** Screening batches and every decision event are bound to the corpus fingerprint, and the contract makes a mismatch a closed gate, so no record can join the accepted snapshot without invalidating every decision. The accept therefore: takes the chase's new records (deduplicated against the whole corpus with the workspace's deduplicator, inside the year window) as `literature/verified.json` of round 2; freezes them as their own `corpus_snapshot` whose `inputs` name the parent snapshot (id and sha256), with the chase run named in the journal row and the rounds index; archives round 1's `literature/screening/` and its published `included.json`, `excluded.json`, `conflicts.json`, `prisma_report.json` and `prisma_screening_report.md` under `literature/screening_rounds/round_001/` (nothing is deleted, as a protocol replace archives a corpus); and records the rounds in `literature/screening_rounds/rounds.json`. Round 2 is prepared and screened in the usual place; its PRISMA report keeps round 1's published numbers in the databases arm and puts the chase in the "citation searching" arm (PRISMA 2020 item 7). Preconditions: round 1 published and current, the protocol unchanged since, the chase run from that publication. No Contract v1 schema, fixture or baseline file changes. Rejected: rebuilding one combined snapshot and carrying decisions forward (it would mint decision events the researcher never made, Compass §3); chasing only before the freeze from the protocol's golden seeds (not chasing from the includes; anchors are few; a possible cheap extra later).

## 2026-11-11 — Citation chasing comes after M4d, before the parked phases (accepted)

The researcher asked which of synthesis, the extraction matrix and the citation graph to build first. Answer taken: citation chasing (backward and forward snowballing from the includes) first, as a small discovery milestone `M3g-citation-chasing` after M4d, because it raises recall, the product's core promise, and the search kit already has the primitives. Then the extraction matrix, because synthesis without extracted data is a summary of abstracts. Synthesis after that, starting from matrix tables rather than generated prose. The graph visualisation last, if ever. The three stay parked until screening is solid with real users; only `M3g` enters the plan now (`docs/roadmap/production-plan.md` §6).

## 2026-11-11 — How M4d grounds browser inception: keys, languages, pool synonyms, anchor seeds (accepted 2026-11-11; M4d-inception-bridge)

Choices made while building M4d; the researcher accepted all six as written on 2026-11-11 ("confirm all the proposed decisions as they are"). Record: `docs/roadmap/milestones/M4d-inception-bridge.md`.

1. **The recon probe still asks OpenAlex without a key.** A probe fetches at most 25 records, which the keyless daily budget usually allows, so the probe is not refused the way a discovery run is (`OPENALEX_KEY_NOT_SET`). The leg says the key is missing (`key_set: false` and the provider's note), and a refusal (401, 403 or 409) fails the leg with `PROVIDER_REFUSED` and a note naming `SCHOLAR_OPENALEX_KEY`; the pool is then `partial` and never cached. A rejected Semantic Scholar key (403) and a throttle (429) fail their legs with `PROVIDER_REFUSED` and `PROVIDER_RATE_LIMITED`. Each leg keeps `error_code`, `notes` and `key_set`.
2. **Languages are recorded, not filtered.** The draft's languages go on the probe's query, into the pool and into its cache key, so a pool says which languages it was searched for. No database filters the probe by language today; every leg notes it. A real filter changes what the providers send for discovery too, so it waits for the provider package that owns them.
3. **A changed scope makes a bound direction stale.** A binding records the draft's question, years and languages. When any of them later differs, `check_binding` answers `SCOPE_CHANGED`, and preview and genesis refuse with `STALE_BINDING`, as for a changed pool.
4. **Pool synonyms are counts, not suggestions from a model.** For each concept, a term is offered when it occurs (1 to 3 words, stopwords dropped) in at least two of the pool records whose title or abstract contains the concept or one of its synonyms. It must not be a term of any concept, nor a piece or an extension of one. At most 10 are offered, the most frequent first. Nothing is added until the researcher ticks it.
5. **Seeds are DOIs from the pool's anchors.** The offered papers are pool records with a DOI that anchor a direction or a concept. The draft keeps at most 25 (the Recall limit), normalised and checked as DOIs. An intent without seeds compiles to the same protocol bytes as before.
6. **Replace keeps the review notes.** `synthesis/literature_review.md` is the researcher's own text and stays; everything else listed in the F1 decision moves.

## 2026-11-11 — Replacing a protocol archives its corpus; inception grounding answers (accepted; M4d-inception-bridge)

The researcher answered on 2026-11-11 in chat, taking every recommended option. Record: `docs/roadmap/milestones/M4d-inception-bridge.md`.

1. **Replace archives the corpus (F1).** When a protocol is replaced (`--replace`, or genesis with `replace: true` and the typed slug), everything that belongs to the old protocol's corpus moves into the same `audit/replaced/<stamp>/` folder as the old protocol: `literature/`, `artifacts/`, `audit/artifact_registry.json`, `.harness-console/`, and, when present, `rag/`, `extracted/`, `phase4/`, `synthesis/` and `pdfs/`. The new protocol starts with an empty corpus and can search. The `GENESIS` journal event names what was archived. The typed-slug confirmation stays as it is. Refusing replace with a `CORPUS_BOUND` code was the alternative; the researcher chose the archive, which is what "replace and back up" already promises.
2. **Continuing without a direction is recorded.** Binding "none" writes `grounding {choice: "none", grounded: false}`, so Review and `intent.json` say the protocol was not grounded (spec 03 Q1).
3. **The gap check is left out of the M4d screens.** The `delta` route stays for MCP. It merges follow-ups into a new pool, and the synonyms and seeds are drawn from that pool (spec 03 Q2).
4. **Defaults for the remaining spec questions:** no custom lexicon in the browser (02 Q1); the contact email is still set outside the app (02 Q2); the engine reports `scope_changed` when the draft's question, years or languages differ from the pool's, and a changed scope marks a bound direction out of date (02 Q3, 03 Q3); a read-only check says whether the researcher's own phrase occurs in the pool before binding (03 Q4); anchor seeds are kept in the draft, compiled into `search_strategy.golden_seeds` at genesis, and pre-filled on Recall with source "Anchor" (replaces 2026-11-10 discovery answer 3).

## 2026-11-11 — Autonomy ladder amended: the gate counts includes, and the agent is never shown outcome statistics (accepted)

The researcher approved two corrections to the 2026-11-10 ladder entry below, both from `docs/lessons/2026-10-17_uav_harvest_calibration_lessons.md`, which the first design did not use. (1) Lesson 35: the UAV corpus was about 98.7% excludes, so the gate's "100 records compared" held one or two includes and its recall interval meant nothing. The gate now counts the researcher's blind includes (an Unclear counts as an include): L1 needs at least 35 compared with a 95% Wilson lower bound on include recall of at least 0.90; L2 needs 75 and 0.95. Agreement and Cohen's κ are shown, never gated on. At a 2% include rate L1 needs about 1 750 records screened first; on a sparse corpus it may never unlock, by design. (2) Lesson 54: a disclosed exclusion prior flipped blind Unclear judgments to Exclude, so at every rung the agent's prompt carries no outcome statistics and no database of origin, any new prior passes a blinded A/B test measured on the Unclear-preservation rate, and the L1 audit reports the agent's Unclear rate beside its misses. Design: [`architecture/agent_autonomy_ladder.md`](architecture/agent_autonomy_ladder.md) §4.

## 2026-11-10 — A Semantic Scholar key that is rejected fails the leg; no silent keyless fallback (accepted 2026-11-12; M3h-providers)

Until now a 403 on `SCHOLAR_S2_KEY` retried the bulk search keyless with only a warning log, so a bad, quoted or pruned key was invisible and the report could not say which pool served the leg. Now a 401 or 403 fails the Semantic Scholar leg with `PROVIDER_REFUSED` and a note naming `SCHOLAR_S2_KEY` (the other databases still run, the run is `PARTIAL`); to search keyless the researcher unsets the key. `GET /discovery/plan` reports `s2_key_set` and the Plan screen says "Set, not yet verified", because the plan sends nothing. The key stays optional: the bulk endpoint runs keyless. The abstract hydrator's one keyless retry is unchanged (a follow-up; **superseded:** removed by M3h-b item 5, 2026-11-18). Evidence: `docs/kits/search/PROVIDERS_2026-11.md` §3a.

## 2026-11-10 — OpenAlex needs its API key: a browser run that selects OpenAlex refuses without it (accepted 2026-11-12; M3h-providers)

OpenAlex has required an API key since 2026-02-13 (keys only; the email parameter is gone; keyless calls share a small daily budget per IP, then 409; cursor paging past page one answers 401). The search kit stops sending `mailto` to OpenAlex. `POST /api/v1/discovery/runs` refuses with the new code `OPENALEX_KEY_NOT_SET` (409), after `MAILTO_NOT_SET` and before any request, when OpenAlex is among the run's databases (the body's `providers`, else the protocol's) and `SCHOLAR_OPENALEX_KEY` is unset; `GET /discovery/plan` reports `openalex_key_set`, and the Plan screen prints the line to set as it does for the contact email. The key stays an environment variable, like the email (decision 2026-11-08): the browser writes no settings file. Not gated: the engine and the CLI `run` (a keyless OpenAlex leg fails with `PROVIDER_REFUSED` and a note naming the key, and the other databases still run), and recall checks (a DOI lookup per seed fits the keyless budget). An OpenAlex 401, 403 or 409 keeps `error_code: PROVIDER_REFUSED` and adds that note. Record: `docs/roadmap/milestones/M3h-providers.md`; findings F12 in `docs/assessment/three-phase-hardening-2026-11-10.md`.

## 2026-11-10 — Agent autonomy ladder: the agent earns each rung on the researcher's own decisions (accepted; design, not yet built)

**Amended on 2026-11-11 (entry above): the gate numbers in this entry were replaced** (L1: 35 includes and a lower bound of 0.90; L2: 75 and 0.95). The screening agent stays a proposer by default (rung L0, today's behaviour). Two gated modes are added: "Agent screens, you audit" (L1: the agent's EXCLUDE proposals stand as decisions; the researcher decides every agent INCLUDE, every Unclear, and a random audit sample of 60 agent excludes) and "Autopilot" (L2: every record the agent could decide; Unclear stays with the researcher; typed acknowledgement at publish). A rung unlocks only through a calibration on the researcher's own blind decisions of this review: L1 needs at least 100 compared (the whole corpus under 200 records, never fewer than 50), include recall ≥ 0.95, 95% CI low ≥ 0.90, at most 2 missed includes; L2 needs 200, ≥ 0.98, ≥ 0.95, ≤ 1. L2 is designed but built only after the screening agent has been measured on the IEEE corpus. Provenance: one `AGENT_ADOPTED` decision event per record, minted by the engine only (never accepted from a client), carrying the proposal id, the mode, the calibration run and the human who set the mode; a Contract v1 change through the baseline gate and an independent review. A protocol change drops the review to L0 and invalidates the calibration. A missed include found in the audit is reported on Home and in the methods paragraph; the researcher, not the engine, decides whether to drop the mode. The methods paragraph states the classifier, the mode, the calibration numbers and the audit result. The existing `ai_agreed_exclusion` setting, which no code acts on, is retired. (Note 2026-11-20: the console still accepts the setting, `screening_v1.py`, until M9b builds this design.) A bounded discovery assistant (synonyms, translation explanations, recall repair) is proposals into the protocol, no autonomy. Milestones M9a-measure, M9b-ladder-engine (RELEASE), M9c-ladder-ui, M9d-discovery-assistant, none before M3c-screens lands. Design: [`architecture/agent_autonomy_ladder.md`](architecture/agent_autonomy_ladder.md).

## 2026-11-10 — Discovery API: what the packet left open (accepted 2026-11-12; M3b-api)

Twelve points the discovery API packet did not settle, decided while building M3b-api; each is listed with its packet section in `docs/roadmap/milestones/M3b-api.md` "Decisions". The ones that shape later work: a researcher's cancel (and a console shutdown) stops the harvest only, archives the run `PARTIAL` with its records in the run folder, and builds nothing from it; the methods draft is rendered on read and never stored, the reviewed text is stored per run; a run is `stale` once a later run's records became the corpus; `PROVIDER_UNKNOWN` (422) is a new code; a leg failure that is not a provider answer has no `error_code`; `run_pipeline` gains optional keyword hooks, the CLI and orchestrator calls are unchanged.

## 2026-11-10 — Discovery screens: ten answers that close specs 01–08 (accepted; M3c-screens)

The researcher took every recommended answer on 2026-11-10 ("all recommended"). The specs are `docs/ux/phase1-discovery/final/01-plan.md` to `08-handoff.md`; the record is `docs/roadmap/milestones/M3c-screens.md`.

1. `/discovery/` is a short status page (step bar, one line per step from the routes, "Continue at …"), not a redirect: a running harvest stays visible.
2. A protocol change from discovery is a sentence and a link to the inception drafts screen; no one-click amendment until the replace path is reachable from the browser (deferred). **Changed 2026-11-19:** M10c item 9(a) lets an assistant's suggestion for the search fields be applied on Plan.
3. Recall seeds are the researcher's own (DOI or arXiv id); inception's anchor papers wait for an engine item that records them in the workspace (deferred). **Superseded:** M4d item 4 (2026-11-11) pre-fills Recall with them.
4. Duplicates says that records the rules did not prove to be one work stay separate works.
5. The share removed is shown as a percentage; the written fraction is under Details.
6. A reviewed methods text can be edited; the save warns that it will no longer be marked reviewed.
7. The methods text of the latest run can be reviewed after the corpus is accepted (it is not part of the frozen corpus); older runs stay read-only.
8. "Hide the database of origin while screening" is cut: the existing blinding hides the agent's proposal, not the origin; a future screening setting with its own spec.
9. "Fill missing abstracts" is cut: the hand-off shows how many records have an abstract; a hydration field only if testers ask.
10. Failed databases are reached from the hand-off through the report in M3c; naming them in the hand-off answer is a small engine follow-up (deferred).

Also decided in the milestone, not asked: the primary navigation is Workspaces · Discovery · Screening (Inception is not a navigation entry today).

## 2026-11-10 — A browser harvest does not freeze the corpus; the hand-off screen does (accepted; M3b-api, engine change in M3d-engine)

**Superseded in part (2026-11-20, M3f-combined-corpus, accepted 2026-11-20):** "an import is allowed only before any harvest" is replaced by M3f item 1 (exports can be staged before or after a harvest; the accept combines both). The rest of this entry stands.

The researcher chose this on 2026-11-10 (option a of the M3b-api open question): "I press Accept on the hand-off screen". A search run started from the browser stops after deduplication and verification; it builds no corpus snapshot and prepares no screening batches. The corpus is frozen only by the hand-off screen's accept, the existing `POST /screening/corpus/accept`. Until then another harvest is allowed; an import is allowed only before any harvest (researcher, 2026-11-10, in M3d-engine: "Keep the rule for now, combine later"; `VERIFIED_EXISTS` keeps a harvest and imports apart, and one snapshot from both, deduplicated together, is M3f-combined-corpus, a RELEASE-lane milestone of its own because it changes the snapshot's inputs). The CLI `scholar-harness run` is unchanged (it still accepts the snapshot at the end of a run, as since M3a). The engine change (the browser run skipping `_accept_run_corpus` and the screening prepare) is M3d-engine, not M3b-api: in M3b-api a successful browser run still accepts the snapshot as M3a does. Built in M3d-engine: the browser run ends `PENDING_CORPUS_ACCEPT` with `corpus_snapshot` `NOT_ACCEPTED`, and the accept builds the artifact the CLI run's accept step builds from the same records (`docs/roadmap/milestones/M3d-engine.md`).

## 2026-11-10 — Discovery over HTTP: seven decisions for the Phase 1 screens (accepted; discovery API packet)

The researcher chose these on 2026-11-10, each explained in plain terms and taken one by one. The packet is `docs/architecture/research_ui/DISCOVERY_API_PACKET.md`.

1. **A harvest started from the browser runs inside the console process**, as recon does, so each database's progress is reported record by record. Closing the console stops the run; what was fetched is kept as a `PARTIAL` run. Not chosen: a subprocess job with a log poll (coarse progress).
2. **Near-twin pair review waits.** The first Duplicates screen shows counts per rule (identifier, exact title, fuzzy title). Whether pair-by-pair review is built is decided after the researcher's own corpora show how many near-twins survive. It would change the snapshot's inputs, so it is a RELEASE-lane milestone of its own.
3. **The recall check never rewrites the query.** It reports found or not found per database against the frozen protocol's query; a miss is recorded and never blocks the harvest; the fix is a protocol amendment through inception. (Since 2026-11-19, M10c item 9(a): a suggestion for the search fields can also be applied on Plan; the recall check itself still never rewrites the query.) The terminal tool's "heal" stays off the console.
4. **The plan shows the exact string each database will receive before the run.** Every provider exposes its translation without a request; a test pins the preview equal to the replayed golden legs.
5. **The contact email stays `SCHOLAR_MAILTO`.** On `MAILTO_NOT_SET` the screen prints the line to set and offers Retry; the browser writes no settings file. Revisit after testers.
6. **No CSV import** until a tester brings a CSV-only export. RIS and PubMed `.nbib` remain the formats.
7. **A per-run cap override is allowed from the browser**, recorded as `run_override` on every leg and in the report; the plan shows only the protocol's cap.

## 2026-11-09 — Recon over HTTP: one session store, pools that say what failed, anchors by occurrence (accepted 2026-11-12; M4c)

Proposed by the M4c session. The researcher accepted it as written on 2026-11-12.

- **One recon engine.**
  - The recon session store moves from `scholar_agent/server.py` to `scholar_harness/recon/session.py`.
  - The CLI wizard, the MCP `recon_*` tools and the console routes all probe through it, on the M3a `SearchEngine.run`. The MCP tools reach it through the adapter (`make_sessions`, adapter 1.1).
  - `MAILTO_NOT_SET` is a refusal at every door, before any request.
- **What a pool keeps, and what is cached (INC-09).**
  - A pool records one leg per provider and a status: `complete`, `partial` (a leg failed) or `empty`.
  - Only a complete pool is cached.
  - A partial pool is used and says which provider failed, but it is searched again next time.
  - An empty pool never becomes the session's pool.
  - `refresh` searches again.
  - `created_at` is shown in every probe answer, in the grounding and in the GENESIS summary.
- **Anchored means observed (INC-21).**
  - A paper anchors a term only when the term occurs as whole words in its title or abstract. Case, hyphens and punctuation are ignored, and there is no stemming.
  - "Hits returned" is kept apart from "observed in".
  - `compute_apr_observed` measures occurrence.
  - The topic is anchored only where it occurs.
- **Grounding lives beside the draft.**
  - `bind` writes `grounding` on the draft record, never inside `draft`. A client save cannot forge or drop it, and a draft without recon is unchanged, so no migration is needed.
  - `STALE_BINDING` means that the session's latest pool is not the bound pool.
  - Per-RQ evidence is computed at preview and genesis, because the RQs are written after the direction is chosen.
- **A pool under 12 papers binds only with consent.** `bind` refuses `POOL_TOO_SMALL` unless `accept_thin_pool` is set (INC-28 for the HTTP route). The CLI wizard still only prints a note.
- **No new search at genesis.** The CLI wizard searches each concept and synonym (budget 3). The HTTP flow does not search again at genesis. Preview shows each concept's occurrence in the bound pool and `apr_observed` instead.
- **The contact email** is the console process's `SCHOLAR_MAILTO`, from the environment or `.env`. There is no in-app setting yet, and the screens say how to set it.
- **Recon jobs** are kept in memory by the console process. A restart loses the job records, not the results: every probe is in the session store.
- **A direction needs its concept in two papers.** Over HTTP a direction is offered only when its concept occurs in at least two titles or abstracts, and its anchors are those papers. The wizard's "pool vocabulary" fallback (prior finding 9), which joins unrelated terms, is therefore not offered there. The CLI wizard keeps it.
- **The suite runs offline.**
  - `tests/conftest.py` refuses any non-loopback socket connect unless `NEXUS_RECORD_CASSETTES=1` or `NEXUS_ALLOW_NETWORK=1` is set.
  - It sets `HF_HUB_OFFLINE` for the RAG tests' cached embedding model. The guard found three RAG tests that reached the Hugging Face Hub on every run.
  - CI fetches `all-MiniLM-L6-v2` in a step before pytest.
- **The golden recon cassette** was recorded once, on 2026-11-09, with the researcher's approval and contact address. That address is filtered out and is not in the file. Semantic Scholar answered HTTP 429 (no API key). The cassette keeps that partial answer, so the replay proves INC-09 on real responses.
- **Lane.** RELEASE: the milestone changes public HTTP and MCP answers and what the recon cache persists.

**Not chosen:**
- Grounding inside the draft: a client could forge it.
- A TTL on cached pools: complete pools stay reusable, `created_at` shows their age, and `refresh` replaces them.
- Running the console's probes through the subprocess `JobRunner`: a recon probe runs in-process and has no CLI action.

## 2026-11-09 — The inception write gate names every file, and a draft keeps its backup (accepted; M4b)

The researcher chose this on 2026-11-09, closing the open questions of the inception specs 06, 07 and 08 before the screens were built.

- **The preview lists every file genesis writes.** `POST /inception/preview` answers `files` with the files of a new workspace (`NEW_WORKSPACE_FILES` in `inception/emit.py` plus `SUPPORT_FILES` in `inception/genesis.py`), or, when the target already holds a workspace, the files a replacement rewrites and its backup folder (`REPLACEMENT_FILES`). It used to name four files, so the write gate under-promised. `test_preview_names_every_file_genesis_writes` runs both geneses and compares.
- **A draft keeps the backup.** The draft's `emitted` record now also holds `backup_dir` and `previous_fingerprint` when genesis returns them, so the Done screen shows them after a reload.
- **Blank drafts and resume.** "Start a new review" always creates a draft; a draft with no title and no topic is listed as "Empty draft" (the browser cannot discard drafts: DELETE is not carried). Resume opens Scope.
- **Lane.** The two engine changes alter public HTTP answers, so M4b is RELEASE (`test_gate_policy.md` §lanes), not the STANDARD it started as.

**Not chosen:** showing the four-file list verbatim and deferring the engine change (the gate would keep under-promising); keeping the backup only in the browser tab (lost on reload); reusing an untouched draft (a frontend rule about what counts as untouched).

## 2026-11-09 — Triage is a focus screen on desktop: its own top bar, a counts rail, no filter chips (accepted; M8-triage)

The researcher chose this on 2026-11-09, after trying the first M8-triage build: "I want the triage the full viewport like the screenshots", and "I don't like those buttons" (the step bar and the queue's view chips).

**The decision.** From 1024 px the triage route is a focus screen, as in the redesign mockup:
- the site header and the screening step bar are not shown there; one slim triage bar takes their place, with the product name, "Triage" (the page's h1), the position line with a progress strip, and Queue (J/K), Help (?) and Leave triage (a link to screening Home);
- the queue column becomes a counts rail (need you, decided, skipped in this session) over the current and next titles; the whole queue opens from Queue or J/K, and its view is chosen from one dropdown instead of five chip buttons.

Below 1024 px nothing changes: the site header, the step bar and the stacked layout stay. On the desktop triage screen the language and theme menus are therefore one step away, on any other screen.

**Not chosen:** keeping the site header with a compact step bar (the first M8-triage build).

## 2026-11-09 — Triage: the checklist is a tool for the reason, not a gate for the decision (accepted; M8-triage)

The researcher chose this on 2026-11-09, after screening real IEEE records: the long checklist had to be answered for every record before Include was possible.

**The decision.** The checklist is collapsed by default. The screen shows the record and the three decision buttons.
- **Include** needs no answers. It is turned off only while an answer the researcher gave fails a criterion (an inclusion answered no, an exclusion answered yes, or an inclusion answered "not reported" under the protocol's `exclude` policy), so a decision never contradicts its own answers.
- **Exclude** is always available. It needs a reason. The reason is pre-selected from the first failed criterion when the answers give one; otherwise the reason chips are offered with none chosen.
- **The checklist opens** on E, to pick the reason, on a number key (1/2/3 answer the focused criterion), or on demand with its toggle.
- **Absent answers stay absent** in the event. They are never auto-filled and never sent as `not_reported`.

**Engine:** no change. `criteria` is optional in the decision-event contract, an EXCLUDE still carries `EXC-n` or `FAILS-INC-n`, and `REASON_CODE_INCONSISTENT` still refuses a reason that contradicts an answered criterion.

**Not chosen:** the inclusion criteria as one compact row of chips with Include still gated on every inclusion yes, and the two combined. Both keep the checklist as a gate.

## 2026-11-09 — The methods paragraph does not count decisions made without per-criterion answers (accepted; M8-triage)

The researcher chose this on 2026-11-09. The exported methods paragraph is unchanged by M8-triage. Each decision event still records which answers were given, so the count can be added later from the events.

**Not chosen:** a sentence such as "n decisions were recorded without per-criterion answers" in `screening/export.py`.

## 2026-11-09 — The triage screen fits 1440×900 and 1280×720 without page scroll (accepted; M8-triage)

The researcher chose this on 2026-11-09. At both viewport sizes the triage page never scrolls; a long abstract, the open checklist and the expanded queue scroll inside their own panes. Playwright checks `document.documentElement.scrollHeight <= innerHeight` at both sizes with a long abstract.

**Not chosen:** 1440×900 only, which would leave laptop screens scrolling.

## 2026-11-09 — An additive import format is a STANDARD-lane change (accepted; M5c-nbib)

The researcher chose this on 2026-11-09, asked at the review of M5c-nbib (PubMed MEDLINE `.nbib` import beside RIS).

**The question.** `test_gate_policy.md` §lanes lists public API and CLI semantics as RELEASE, and M5b (the RIS import, the same surface) was RELEASE. M5c-nbib widens `POST /corpus/sources` and `--ris` to a second file format and adds a `format` field to the source rows; the reviewer read that as RELEASE.

**The decision.** A new import format that leaves identity, the contract, the `verified.json` row shape and every existing input's behaviour unchanged is STANDARD: the pr gate once on the final executable commit, the contract check, and an independent review. The closure-stage extras (schema and two-study fixture checks, wheel build) were run and recorded for M5c-nbib anyway, so the evidence covers either lane.

**Not chosen:** relabelling the milestone RELEASE (no extra evidence would have been produced); treating every route widening as RELEASE by rule (the policy's RELEASE line is for changes to what existing inputs mean, which this is not).

## 2026-11-08 — Re-inception: refuse without `--replace`, back up, confirm a screening binding (accepted; M4a, INC-08)

The researcher chose this on 2026-11-08.

**One gated write path.** `scholar_harness.inception.emit.emit_workspace` is the only code that writes an inception protocol into a folder. The CLI wizard, `nexus-scholar init` (with and without `--scaffold-only`), the workspaces API, the inception HTTP route and the inception-agent helper `emit_protocol.py` all go through it. It compiles the intent before writing, so an invalid intent writes nothing.

**The guard:**
- **No `--replace`.** A folder that already holds a workspace (any `INIT_MARKERS` file) is refused with `WORKSPACE_EXISTS`, and nothing is written. The wizard checks as soon as the title gives the slug, then checks again at the write.
- **`--replace`.** It copies `protocol.json`, `intent.json` and `SCREENING_CRITERIA.md` to `audit/replaced/<UTC stamp>/` before writing. `project.json` is kept: `created_at`, `stats`, `registered_workspace_id` and `project_id` stay. Only the fields the new protocol states are refreshed: title, paradigm, research questions and `updated_at`. GENESIS names the old fingerprint and the backup path.
- **A screening binding needs a second, explicit confirmation.** Screening decisions are counted from the event log lines and the `batch_NNN_decisions.json` files, and a publication from `literature/screening/generation.json`. With any of these, `--replace` alone is refused with `SCREENING_BOUND`, and the refusal gives the counts.
  - **Mechanism:** on the CLI and in the skill helper, the extra flag `--discard-screening-binding`. Over HTTP, the body must also carry `confirm_discard_screening_binding` equal to the workspace slug, typed by the researcher.
  - GENESIS records that the binding was discarded, with the counts.

**What does not change:** the protocol compiler, the fingerprint rules and the screening data. The old decisions stay on disk, and they still refer to the old criteria, which are kept in the backup.

## 2026-11-08 — Inception criteria are shown verbatim and accepted one by one (accepted; M4a, INC-22)

The researcher chose this on 2026-11-08.

- **Every criterion is shown verbatim, with its source, and accepted one by one.** The source is one of: written by the wizard from the proof answer; the paradigm's default exclusion, written by the wizard; the researcher's out-of-scope answer; typed by the researcher.
- **A criterion the wizard wrote needs an explicit yes.** Its prompt defaults to no. A criterion the researcher typed defaults to yes.
- **A rejected criterion is not compiled.** The rationale's "Explicitly out of scope" sentence names only the accepted out-of-scope items.
- **An empty side is filled by asking.** If either side would be left empty, the wizard asks the researcher to write a criterion, because `IntentPacket` needs at least one inclusion and one exclusion criterion.
- **The pre-emit panel lists every accepted criterion in full**, not as counts.
- **The source is not stored in the protocol.** Storing it would be a contract change. It appears in the wizard and in the step API output.
- **The deterministic `--scaffold-only` placeholder protocol keeps every drafted criterion,** so its fingerprint does not move.
- **The agent path follows the same rule.** The inception-agent skill must show each criterion and get a per-criterion yes before it writes `intent.json`.

## 2026-11-08 — Inception drafts live under the workspaces root, with one session id (accepted; M4a, screens 00 and 08)

The researcher chose this on 2026-11-08.

- **Where drafts live.** A draft of the web wizard is saved at `<workspaces root>/.drafts/<session id>/draft.json`. A draft is the researcher's work, not a cache. The recon cache root defaults to `<repo>/.cache`, which does not fit a PyPI install.
- **The workspace list ignores drafts.** It skips folders whose name starts with a dot.
- **The session id** is `rec_` followed by 32 lowercase hex characters, the format the MCP recon sessions already use. The grounded CLI wizard uses it too (it used 12 hex characters). One id now names a draft and its recon session. The recon pools stay in the canonical recon cache.

## 2026-11-08 — The retrieval cap is a protocol method key (accepted; M3a-discovery, SRCH-31)

The researcher chose this on 2026-11-08.

**The key.** The protocol's `method` block gains an optional `retrieval_cap`: a positive integer, the most records fetched from one database for one query. When the key is absent, the protocol sets no cap: each database is paged until its reported total is reached.

**A safety ceiling still exists** in the engine, so a runaway query cannot fetch a million records. It is not a protocol value. When a leg stops at the protocol cap or at the ceiling, that leg reports `cap_hit: true`, the cap that applied and where it came from (`protocol` or `engine_ceiling`). The PRISMA-S report and the journal state it per database. A cap is never silent.

**`search_strategy.target_candidate_pool_size`** stops being a retrieval cap. Today its `max` (default 100) silently capped every provider (`protocol_adapter.py`). It stays in the protocol as an advisory planning figure and changes no retrieval.

**Fingerprint.** An absent `retrieval_cap` is left out of the canonical JSON, like an absent `reporting`, so no existing protocol's fingerprint changes. New workspaces do not write it (no cap is the default).

**Contract v1.** The protocol model is not in the contract baseline; `generate_contract_baseline.py --check` decides. The protocol JSON schema is regenerated by `scripts/generate_protocol_schema.py`.

**Not chosen:** reinterpreting `target_candidate_pool_size` as the cap (a misleading name); a run-time setting only (the signed protocol would not state the cap).

## 2026-11-08 — A live search needs a real contact email (accepted; M3a-discovery)

The researcher chose this on 2026-11-08.

Crossref, OpenAlex and NCBI ask for a contact address on each request (the "polite pool"). The default was a placeholder, `student@university.edu` (`scholar_search/config.py`), sent on every request on the user's behalf.

- The placeholder is removed. `SCHOLAR_MAILTO` (or `mailto` in the `.env`) has no default.
- A live search refuses before any request with the typed refusal `MAILTO_NOT_SET`, naming the setting to fill.
- What does not need it: `--help`, imports, dedup, the golden search replayed from cassettes (the test sets a placeholder, and the cassettes filter it out), and every offline path.
- Each search leg records whether a contact address was sent (`mailto_set: true`), never the address itself.

**Not chosen:** warn and run anonymously; leave the placeholder.

## 2026-11-08 — One live golden search, frozen to cassettes (accepted; M3a-discovery)

The researcher allowed one live search on the golden UAV protocol, against the free providers (OpenAlex, Crossref, PubMed, Semantic Scholar, arXiv), to record the VCR cassettes the golden search replays from. The cassettes are committed with the contact address and any API key filtered out. After that, every test replays offline; re-recording is a deliberate, separate step.

## 2026-11-08 — Reporting follows a guideline chosen in the protocol (accepted; plan step 11)

This accepts the 2026-11-06 consequence that screening is not specific to systematic reviews. The researcher chose the options below on 2026-11-08.

**The key.** The protocol's `method` block gains an optional `reporting` key, with three values: `prisma-2020`, `prisma-scr` or `none`. When the key is absent, or the protocol has no block at all, the guideline comes from `playbook_type`:

| Playbook type | Guideline |
| :-- | :-- |
| `PRISMA_SLR` | `prisma-2020` |
| `RAPID_EVIDENCE` | `prisma-2020` (rapid reviews usually report against PRISMA 2020) |
| `STUDENT_DISSERTATION` | `prisma-2020` |
| `SCOPING_REVIEW` | `prisma-scr` |
| `DESIGN_SCIENCE` | `none` (no systematic-search claim) |

A protocol may still set any of the three values to override this.

**Fingerprint.** An absent `reporting` is left out of the canonical JSON, the same way an absent block is. So no existing protocol's fingerprint changes, including protocols written with the M7-method block. New workspaces write the derived value into their block, so the signed protocol states it.

**What the guideline changes.** Only the labels and one sentence.
- **Screen labels name the guideline.**
  - Publish's preview reads "PRISMA 2020 screening preview", "PRISMA-ScR screening preview" or "Screening preview".
  - Export's counts heading reads "PRISMA 2020 counts", "PRISMA-ScR counts" or "Screening counts".
  - Export's language note names the matching flow diagram, or "your flow diagram".
- **The methods paragraph adds one sentence after the source sentence:**
  - `prisma-2020`: "The screening is reported following PRISMA 2020."
  - `prisma-scr`: "The screening is reported following PRISMA-ScR, the PRISMA extension for scoping reviews."
  - `none`: no sentence.
- **`figures.method.reporting` and `figures.method.reporting_source`** carry the value and where it came from: `protocol` or `playbook`, or `defaults` when there is no readable protocol (review, 2026-11-08). **`figures.method.reporting_label`** carries the name the sentence states ("PRISMA 2020", "PRISMA-ScR", or null for `none`), so the number in "PRISMA 2020" traces to a figure.

**What does not change:**
- The counts, their meaning and the counts sentence.
- The engine and the rule table.
- The published file `prisma_report.json`. It is a publication artifact that digests and currentness checks depend on, so it keeps its name under every guideline.

**Not chosen:**
- Always deriving from `playbook_type`, which would leave no way to override it.
- PRISMA-ScR's "sources of evidence" wording in the counts sentence and labels. It is deferred to the parked PRISMA-ScR checklist work.
- Renaming `prisma_report.json`.

## 2026-11-08 — Method parameters move into the protocol (accepted; plan step 10)

Accepts point 2 of "Three kinds of parameter" (2026-11-06) with the researcher's choices of 2026-11-08.

**Note 2026-11-20:** H-screening-drafts items 1 and 2 (PROPOSED, not accepted) add the `decisive_first` value and let `blinding` and `not_reported` be changed after genesis by a recorded amendment beside the signed protocol; if accepted, the values in force are the signed ones plus the amendments, and the `BLINDING_SET_BY_PROTOCOL` refusal below names the amendment route.

**The block.** `protocol.json` may carry an optional `method` block:

```json
"method": {
  "dedup": { "doi": true, "title_similarity": 0.97, "first_author": true, "year_tolerance": 1 },
  "rules_version": "screening-rules-v1",
  "not_reported": "unclear",
  "blinding": "reveal_after_decision"
}
```

**What goes in:** four values, the ones that can change what is included or how biased the screening is:
- the dedup tiers;
- the rule-table version;
- the not-reported policy;
- blinding.

Batch size stays a Prepare setting, because it only changes how the work is chunked.

**What a review may change, and the checked limits.** The protocol validator refuses anything outside these limits (`PROTOCOL_METHOD_INVALID`):
- `title_similarity`: 0.90–1.00.
- `year_tolerance`: 0–2.
- `doi`: always true.
- `first_author`: true or false.
- `rules_version`: a version the engine knows (today only `screening-rules-v1`).
- `not_reported`:
  - `unclear` (today's rule): any criterion not reported gives Unclear, which goes to full text.
  - `exclude`: an *inclusion* criterion not reported gives Exclude with `FAILS-INC-n`.
  - In both cases an *exclusion* criterion not reported never fails, as today.
  - The choice applies to the agent's drafts and to the reason the screen offers. A researcher's own decision is never overridden.
- `blinding`: `reveal_after_decision` or `show`. When the protocol sets it, the Prepare control shows the value and does not change it; the refusal is `BLINDING_SET_BY_PROTOCOL`.

**Fingerprint.** The block is optional, and when it is absent it is left out of the canonical JSON, so the fingerprint of every protocol without a block is unchanged. A protocol with the block hashes it, so the signed protocol covers these values. New workspaces are written with the block, filled with today's values.

**Existing workspaces** are left as they are. Without a block the defaults apply (today's values), decisions and fingerprints are untouched, and the methods paragraph names the defaults it used. There is no adopt command. Adopting the block means re-inception or a new workspace.

**Methods paragraph.** The paragraph reads the values in force (the block, or the defaults) and says which source it used.

**Contract v1.** Adding an optional field to the protocol schema is decided by `generate_contract_baseline.py --check`, not by convenience. If the check moves, this entry is the architecture decision the gate requires. The work then also needs:
- regenerated schemas and golden fixtures;
- a negative regression test (a protocol without the block keeps its exact fingerprint; an out-of-range value is refused);
- independent review.

**Not chosen:**
- An always-serialized default block. It would have changed every existing fingerprint.
- Environment variables. They are invisible to the hash.
- Batch size in the block. It does not change outcomes.
- An adopt command for existing workspaces.

## 2026-11-07 — Details on demand (M6-beta)

Each screening screen shows only what the researcher acts on. Identifiers and proofs sit
behind one "Details" disclosure per card. The disclosure is closed by default, reachable
from the keyboard, and has the same label on every screen. This is the brand book's "plain
words first, raw value underneath", read as: the raw value is one disclosure away, never
inline.

**Moved behind Details:**
- study ids and the raw form of DOIs;
- protocol and batch fingerprints;
- generation ids and fingerprints;
- event ids, run ids and prompt hashes;
- the "Recorded as you · HUMAN · time · protocol sha" line (the card keeps "Saved", with the time on hover);
- refusal codes (the plain sentence stays on the card);
- batch file names on Home and Publish.

Nothing leaves the DOM, so the provenance checks in Playwright still find every value. The
list for each screen is `docs/ux/phase2-screening/final/12-details-disclosure.md`.

## 2026-11-07 — Answer until decisive (M6-beta)

The desktop checklist no longer has to be filled in full before a decision.
- **Exclude** is enabled as soon as one criterion fails: an inclusion criterion answered
  no, or an exclusion criterion answered yes.
- **Include** needs every inclusion criterion answered yes and no exclusion criterion
  answered yes. **Superseded 2026-11-09** ("Triage is a focus screen on desktop"): Include needs no answers.
- **Unclear** is always enabled.

A criterion left unanswered is stored as absent from the event's `criteria`. It is never
recorded as `not_reported`, because that would claim the reviewer looked and found nothing.

The screening contract does not change: `criteria` is already optional, and the engine
validates only the reason code. On Exclude, the reason is pre-selected as the first failed
criterion in protocol order, so E then Enter excludes. An engine refusal,
`REASON_CODE_INCONSISTENT`, guards the case where an Exclude's reason code names a criterion
that the same event answers the other way.

## 2026-11-07 — Advance on decide, as a workspace setting (M6-beta)

After a decision, triage moves on in one of two ways, chosen per workspace on Prepare:
- **"show the draft, then N"** (the default): if the record has a draft, the revealed
  state shows and N advances. If it has no draft, the next record opens at once.
- **"move on at once"**: the next record always opens at once, and drafts stay in each
  record's details.

The setting is stored with the other screening settings (`GET/PUT /settings`) and journaled
as `SCREENING_SETTINGS_CHANGED`. The methods paragraph reports it only when it changed what
the reviewer saw, that is, when drafts were skipped.

## 2026-11-07 — Published means current (M6-beta)

A screening reads "Published" only while the published generation still matches the
decision files. The publication gate (`require_current_generation`, or one wrapper that
`/ui/publication-status`, `/summary`, export and methods all call) also checks
`stale_projections`. A decision recorded after publish makes every surface read
`GENERATION_STALE`, naming the stale batches or the number of changed studies.

Stored files and the Contract-v1 artifacts do not change; only the status that is read
changes. If the change turns out to alter stored semantics, it stops as
`BLOCKED_BASELINE_DRIFT` and the lane escalates to RELEASE. This closes the currentness gap
that M5-slim deferred (review T-P1-1).

## 2026-11-07 — The beta's parked list (M6-beta)

The researcher's plan of 2026-11-07 sets the order: every step before the first testers
shortens a tester's path to a good first hour, and every step after them is driven by what
they report.

**Parked until a tester asks:**
- the 1,644-record prompt gate (it measures agreement with earlier AI labels, review S-P0-2; run through the API on 2026-11-19 by M9a);
- the second-screener lane;
- the phone (M2);
- the live audit view;
- the PRISMA-ScR checklist rewrite;
- full text, extraction, synthesis, graph and verify.

**After the first testers:**
- the Windows pytest job, once the suite runs in under ten minutes or there is a second
  maintainer;
- the hardening pass (atomic writes, `os.replace` retry, `/healthz`, dead routes and client
  functions);
- the parameters decision, acted on between tester rounds because it changes the protocol
  fingerprint of new workspaces;
- reporting as a guideline switch keyed from `playbook_type`.

The beta is tagged `v1.1.0b1` only after the version fix, so the GitHub Release and its
wheel carry the same version, and nothing named 1.0.0 is published under a beta tag
(researcher, 2026-11-07).

## 2026-11-06 — Three kinds of parameter, and where each lives (accepted 2026-11-12; point 2 was accepted 2026-11-08, see "Method parameters move into the protocol")

The researcher raised it on 2026-11-06: values are encoded throughout the
project, screening may not be specific to systematic reviews, and the stages
may one day be composed by the researcher. A survey of the harness found
about 35 module-level numeric constants, five `NEXUS_*` environment
variables, and pydantic-settings classes in three kits. Most of the constants
are floors or contract limits; the problem is not their number but that three
kinds of value are mixed with no rule. The rule:

1. **Invariants stay in code.** Security floors and contract limits: pairing
   code length and lifetime, the launch code's two minutes, 200 events per
   request, the 50 MB import cap, the approver name length. They are not
   preferences; changing one is an architecture decision. They are listed
   once, with their floor and the reason, in
   `docs/architecture/DEVELOPER_COMPASS.md`, and nowhere else.
2. **Method parameters live in the protocol.** Anything a reviewer could ask
   "how did you …" about belongs in `protocol.json`, under a `method` block,
   versioned and covered by the protocol hash, so the researcher signs it and
   the methods paragraph reads it from the same place. Today these are in
   code: the deduplication tiers (exact DOI, then fuzzy title at 0.97 with
   first-author match and a year tolerance of ±1, `scholar_search/dedup.py`),
   the screening rule table and its version (`screening-rules-v1`,
   `screening/proposals.py`), the "any criterion not reported means Unclear"
   policy, the default batch size (20), and the blinding default
   (`reveal_after_decision`). The current values become the defaults a new
   protocol is written with, so nothing changes for a workspace that says
   nothing. A workspace that adopts the block gets a new protocol fingerprint,
   like any amendment; existing workspaces keep theirs until re-inception.
   Whether adding the block is a Contract v1 change is decided by
   `generate_contract_baseline.py --check`, not by convenience: if the check
   moves, stop and decide.
3. **Operator preferences live in the workspace settings and the keychain.**
   Provider, model, cost ceiling, queue order, advance-on-decide, theme,
   workspaces root. They are journaled when they affect provenance (as
   `SCREENING_SETTINGS_CHANGED` already is) and never hashed into the
   protocol.

Two consequences follow, both deferred until after M6-beta:

- **Screening is not specific to systematic reviews.** Criteria come from the
  protocol, decisions are events, the outcome is a rule table over
  per-criterion answers; that holds for scoping and mapping studies, umbrella
  and rapid reviews, dataset curation and abstract triage. What is specific is
  the reporting layer (PRISMA counts, the flow-diagram boxes, the methods
  paragraph), so reporting becomes a guideline chosen in the protocol
  (`prisma-2020`, `prisma-scr`, `none`), keyed from the existing
  `playbook_type`. The engine does not change.
- **Composition comes from artifact types, not a workflow engine.** Every stage
  is a step that declares the Contract v1 artifact types it consumes and
  produces and refuses with a typed code when an input is missing; the order
  falls out of the dependencies (import or discovery produce a corpus
  snapshot; prepare consumes it; collect consumes decisions). No workflow
  builder, no pipeline-spec runner, until a second workflow exists. The
  legacy nine-stage coordinator (`pipeline/coordinator.py`) and the
  pipeline-spec runner (`pipeline_executor.py`) are not that model and are
  not extended.

Not chosen: a settings framework for the harness (there are too few knobs to
justify one), environment variables for method parameters (invisible to the
protocol hash), and a per-screen configuration file (a preference that
changes the science must be in the protocol).

## 2026-11-06 — Several database exports in one corpus, deduplicated by the snapshot (M5b)

The researcher asked for several RIS files with cross-database deduplication and a way to
accept the corpus in the app. A PRISMA flow diagram needs the records identified per
database and the duplicates removed. Before this change, `accept-corpus --ris` took one
file and the counts read 0 duplicates.

- **Staging.** Each export is staged with a database label under `literature/raw/ris/`, kept
  byte for byte, and listed in `literature/raw/ris/sources.json`. A label may repeat (a
  database exported in parts); its files are summed into one database for PRISMA. Each
  file can carry a date searched and a search string, both optional. Staging and removal are journaled
  (`CORPUS_SOURCE_STAGED`, `CORPUS_SOURCE_REMOVED`).
- **Acceptance.** Acceptance writes one `verified.json` row per record, with
  `source_database`. It also writes `literature/raw/provenance_manifest.json`
  (`total_raw_harvested`, records per source), which the PRISMA counts already read.
- **Deduplication.** Nothing is collapsed at import. The snapshot builder's existing
  `Deduplicator` (DOI, then title, first author and year ±1) groups records into studies,
  so duplicates removed = records − studies, within and across files.
- **Contract.** The Contract-v1 snapshot schema is unchanged (`generate_contract_baseline.py
  --check` passes). Record ids now include the source and position, so two copies of one
  paper stay two records.
- **Freezing.** Once a corpus is accepted, its sources are frozen
  (`CORPUS_ALREADY_ACCEPTED`), and the app offers no way to replace it.
- **Routes.** `GET /corpus`, `POST /corpus/sources`, `POST /corpus/sources/{id}/remove`
  and `POST /corpus/accept` replace the planned M0 `POST /corpus/accept` row. They are
  desktop only and in both browser allowlists.
- **Methods paragraph.** It names each database with its count and date searched.

Approved by the researcher on 2026-11-06, with three changes to the Import screen (spec 11):
repeated labels are summed per database; the search details sit behind a "Search details"
disclosure with a "not stated" flag; and the Import step stays in the steps bar until the
corpus is accepted, after which Home shows one line of what was imported.

## 2026-11-06 — The approver's name is set on the Publish screen (M5-slim)

The researcher chose a field on the Publish screen over a command. Before,
nothing in the app wrote `literature/screening/operator_context.json`, so the
first approval of the golden run refused `OPERATOR_CONTEXT_MISSING` and the
researcher wrote the file by hand. Now `GET`/`PUT /api/v1/screening/approver`
read and write it (desktop only, in both browser allowlists), and every change
is journaled `SCREENING_APPROVER_SET` with the name before and after. The
Publish screen shows an Approver card above the batches; until a name is
saved, the code and approve buttons are disabled and the card says why.

What the name is, said plainly on the screen and in the contract: a name
typed on this computer, not a verified sign-in (CON-02/03 stay open; real
authentication is later work). Names the engine never trusts as a person
("unknown", …) refuse `APPROVAL_NOT_OPERATOR`. Changing the name later does
not rewrite approvals already made: each keeps the name it was made under.

## 2026-11-05 — The demonstration screens are removed; a new header and footer (M5-slim)

At the researcher's request the stale demonstration screens are gone: the
overview, the single-record `/screening` page, corpus, lineage and audit, with
their mock data (`lib/mock-*.ts`, `lib/contracts.ts`, `lib/project-state.ts`),
components and tests. Every remaining route reads a live workspace, so the
"Demonstration data" marker is gone too. `/<locale>` now forwards to
`/workspaces`, and `/<locale>/screening` forwards to `/screening/home`, so old
links still land somewhere real. The packaged app now opens on
`/en/screening/home/` (it opened the old demonstration page before).

This supersedes plan §8's "`corpus`, `lineage` and `audit` stay". Audit is
the loss that matters, since it carried provenance. The removed page showed
fixtures only, and a live audit view is follow-up work. The `ParkedNotice`
went with the screens it labelled; the parked CLI help and MCP descriptions
are unchanged.

The header is one 64px bar: the wordmark (no logo yet, per the brand book),
`Workspaces` and `Screening` with a brand underline on the current one, then a
language menu and a three-icon theme toolbar. Below `lg` these move into one
menu dialog. The footer is one line: the app runs on this computer, nothing is
sent unless agent proposals are started, and every decision is recorded in the
workspace's audit journal. The catalog shrank from 150 keys to 22 (the shell
chrome only); the screening screens keep their own per-locale copy.

## 2026-11-05 — The Claude Desktop Extension carries the wheel and launches it with uvx (M5-slim)

`scripts/build_mcpb.py` builds `nexus-scholar-<version>.mcpb` (MCPB `manifest_version` 0.4, the schema shipped with `@anthropic-ai/mcpb` 2.1.2). It bundles the `nexus-scholar` wheel and starts the server as `uvx --from ${__dirname}/<wheel> scholar-agent --workspace ${user_config.workspace}`, so it works before anything is on PyPI and needs only `uv` on the computer. Its one setting is the workspace folder. It holds no key and asks for none: provider keys stay in the OS keychain, which the server now reads at start (CORE-17 follow-up). The release workflow attaches it beside the wheel. Not chosen: the experimental `uv` server type (it would ship the source tree), and `sensitive` key fields in the extension (a second place for keys). Not verified here: installing it in Claude Desktop, and `npx @anthropic-ai/mcpb validate` (running the packer was not allowed in this session; the manifest is checked against the schema's required fields and types by `tests/test_build_mcpb.py`).

## 2026-11-05 — The packaged UI reaches the engine by a launch cookie and the proxy's allowlist (M5-slim)

The packaged app serves the UI as a static export from the console process
(plan §5.3), so the Next.js proxy, which held the token and allowed the
browser only reads and a list of writes, is not there. Its job moves into the
console (`src/scholar_harness/console/browser.py`), with the same rules:

- The UI keeps calling `/api/console/api/v1/...`; those requests are checked,
  then served as `/api/v1/...`. `/api/v1/...` itself still needs the bearer
  token, which never reaches the browser.
- The browser authenticates with an **HttpOnly, SameSite=Strict session
  cookie**. `nexus-scholar ui` opens `/launch?code=<code>`: a one-time code,
  valid 2 minutes, never the token. The session secret belongs to the launch,
  so it survives the restart onto another workspace.
- The **allowlist is the proxy's** (GET/HEAD on plain `/api/v1/...` paths; POST
  and PUT only on its lists, only from this origin; the draft read only from
  this app's pages); the workspaces routes join both lists. A test keeps the
  Python lists equal to `route.ts`.
- The static UI holds no workspace data and is served without a session.

New console codes: `CONSOLE_PATH_REFUSED`, `CONSOLE_ORIGIN_REFUSED`,
`CONSOLE_METHOD_REFUSED` (the proxy's), `LAUNCH_CODE_INVALID`.

## 2026-11-05 — The minimal workspace screen: root, open, create (M5-slim)

Spec `docs/ux/phase2-screening/final/00-workspaces.md` (FINAL). The
researcher's answers, 2026-11-05:

- **Root:** `--root`, then `NEXUS_WORKSPACES_ROOT`, then
  `~/Documents/Nexus Scholar/workspaces`; `--workspace <path>` still opens one
  folder and skips the screen. No settings screen or config file.
- **Open restarts** the engine and UI on the chosen folder (no in-place
  rebind, so no run state, pairing, phone token or cache crosses workspaces).
  It is refused `WORKSPACE_BUSY` while an agent run or an approval pairing is
  active, since a restart would kill it. Opening writes no journal event.
- **Create** asks for a title only; the folder is `{root}/{slug}`; an existing
  folder is refused `WORKSPACE_EXISTS`, never suffixed. It runs the same
  scaffold and support files as `nexus-scholar init --scaffold-only`, and its
  placeholder protocol is shown as a draft (no Contract v1 change).
- **Listing:** a folder counts as a workspace when it has `protocol.json`,
  `project.json` and `audit/journal.jsonl` (`.mcp.json` is not required);
  others are hidden behind "n folders skipped · Show them". `GET /workspaces`
  returns absolute paths (desktop-only, local).
- `docs/architecture/workspaces-api.md` is written and agreed before the
  engine work, with the codes `WORKSPACE_TITLE_INVALID`, `WORKSPACE_EXISTS`,
  `WORKSPACE_PATH_REFUSED`, `WORKSPACE_ROOT_UNAVAILABLE`, `WORKSPACE_NOT_VALID`,
  `WORKSPACE_BUSY`.

## 2026-11-05 — The prompt gate may be met on the MCP route

With no API credit, the researcher's own Claude (Claude Code subagents on the
subscription) answers the frozen v03 set through `nexus-scholar prompt-gate
export|import`: a blind export (prompt, schema and record text only; no label,
nothing ordered by label), one JSON answer per record, scored by the same
checks, rule table and bar as an API run. **A pass on this route is enough for
the M5-slim prompt-gate requirement for now** (researcher, 2026-11-05).

- The report names the route (`provider: "claude-code-mcp"`) and the model;
  its cost is null (the subscription is not metered per record).
- It measures the MCP route, not the API driver: the prompt runs inside
  Claude Code's own instructions, the output format is checked after the fact
  rather than enforced, and effort cannot be set. The API route stays
  unmeasured, and the agent-system §6 cost per 1,000 records stays an
  estimate, until an API run.
- Nothing may claim an API-route pass on the strength of an MCP-route one.

## 2026-11-05 — M1b-2 merges before its live prompt gate; the gate blocks M5-slim

The live prompt gate (Opus 5.5 on the frozen v03 set, Wilson lower bound of
include-recall >= 0.90; Sonnet 5.5 and Haiku 5.5 measured) needs API credit
the researcher does not have yet. Two smoke attempts measured nothing: a
placeholder key (401), then a real key on an account with no credit (400,
credit balance too low); neither was billed. M1b-2 therefore merges as
**code-complete with the prompt unmeasured** (researcher, 2026-11-05):

- the PR says plainly that the bar is not yet measured: Opus 5.5 is not shown
  to meet it, Sonnet and Haiku are unmeasured, and the agent-system §6 cost
  per 1,000 records is still an estimate;
- nothing in the product, its docs or its marketing may claim the agent passed
  the gate, or quote a measured recall or cost, until a gate report exists;
- the gate is a **blocking item for M5-slim**: no packaged release that runs
  agent proposals ships before it passes on the default provider and model,
  and its report and measured cost are recorded in the milestone file;
- the stand-ins were declined: a free Gemini key would not test the decided
  default and may let the provider use the records; a local model measures
  the pipeline, not the product.

**Later (note 2026-11-20):** the gate was relaxed to accept an MCP-route pass
(2026-11-05, entry above), parked for the beta (2026-11-07), and M5-slim shipped
with it open. The API route was measured on 2026-11-19 (M9a). Decided 2026-11-20: the gate is met, on recall only
(entry "Six open decisions settled").

**Superseded paragraph (kept for history, 2026-11-20 note):** the paragraph below describes a marker that
was removed on 2026-11-05 (entry "The demonstration screens are removed; a new header
and footer"). It belongs to no entry of its own.

The shell drew `Demonstration data` and "Read-only demonstrator" on every
route, including the six screening steps (`/screening/home`, `prepare`,
`proposals`, `triage`, `agreement`, `publish`) that only read the workspace's
engine and record decisions. There the labels were false. On those six routes
the shell now leaves the marker out and its footer says the data is live
(`isLiveOnlyPath`, `tests/shell.test.tsx`). Every other route keeps both,
including `/screening`, `/corpus`, `/lineage` and `/audit`, which still default
to fixtures; the rule "no mock data without the label" is unchanged
(researcher, 2026-11-05).

## 2026-11-05 — A minimal workspace screen joins M5-slim

The researcher asked why workspace management, Inception and Discovery came
after screening. The order stands (2026-11-03 entry below): screening is the
wedge, `accept-corpus` is its entry path, web Inception (M4) is past the
horizon and Discovery (M3) is stretch. One gap is pulled forward: a packaged
desktop app that can only open the single folder named on the command line is
not sellable. M5-slim therefore adds a **minimal workspace screen**: list the
workspaces under the workspaces root, open one, and create one (the same
scaffold as `nexus-scholar init`), with no Inception wizard. Its spec is written
before M5-slim starts; the M4 multi-workspace server and Inception spec 00 stay
in M4 (researcher, 2026-11-05).

## 2026-11-05 — The checked record text carries the publication year (M1b-2)

The text an agent sees and quotes, and that the engine checks quotes against
(`proposals.record_text`), is the title, a blank line and the abstract, then,
when the record has a year, a blank line and `Published: <year>`. Date
criteria (v03 INC-03, EXC-04) can then be answered with a verifiable quote;
before, the agent could only answer `not_reported`, so every record became
Unclear and the prompt gate measured nothing useful (researcher, 2026-11-05).

- Without a year the text and its `input_sha256` are unchanged, so earlier
  proposals keep their ids. With one, the hash and `proposal_id` change; no
  real proposals existed yet (only sandbox and test ones).
- Language still has no field; a language criterion is answered from the
  abstract or stays `not_reported`.
- The MCP record tool returns this `text` with the year, so an agent using
  MCP quotes the same string.
- **Usefulness is reported, not gated:** the prompt-gate report also gives
  the share of confirmed excludes the agent excludes and its Unclear rate;
  the pass bar stays include-recall.

## 2026-11-05 — The screening prompt gate: bar, sample and models (M1b-2)

The researcher set the prompt gate of agent-system §5 for the screening task:

- **Bar:** the 95% Wilson lower bound of include-recall is at least **0.90**.
  Include-recall counts an agent Unclear as not excluded, because Unclear goes
  on to full text. The bar applies per task version (provider, model, prompt,
  effort).
- **Sample:** every human-confirmed include of `uav-crop-weed-v03` (644) and
  1,000 of its confirmed excludes, drawn with a fixed, recorded seed. The set
  is frozen as a list of study ids with its SHA-256, so every model and prompt
  version is measured on the same records.
- **Models:** `claude-opus-5-5` (the default), `claude-sonnet-5-5` and
  `claude-haiku-5-5`. A cheaper model is adopted only if it meets the bar
  (agent-system §9 item 3).
- **The live run spends the researcher's key.** It runs only after the
  researcher sees the token-counted estimate and starts it; the key is stored
  in the OS keychain and never seen by the agent or written to a file.

**Caveat (carried from 2026-11-04):** the v03 labels are confirmations of agent
drafts. The gate measures recall against labels a person reviewed with a
draft in view, not against independent blind screening; the methods text says
so.

## 2026-11-05 — M1b is three PRs; three screening providers

M1b splits into **M1b-0** reveal tracking (RELEASE, backend only), **M1b-1**
desktop triage UI (STANDARD) and **M1b-2** drivers and the prompt-gate eval
(STANDARD). The researcher agreed the split on 2026-11-05. The reveal change is
isolated so the strict lane covers only the engine change to stored decision
events.

**Providers (researcher, 2026-11-05):** one driver interface with Anthropic
(the default), any **OpenAI-compatible** endpoint (a base URL and a key) and
Gemini. They share the prompt, the output schema, the plain-code outcome rule
and the rule that a refusal or a failed check becomes Unclear. Each provider
and model is its own task version and must pass the prompt gate on its own.
This settles agent-system §9 item 1: Gemini stays, behind the interface.

**Reveal semantics (contract §3.1, applied literally):** a reveal is the first
time the API returns a proposal for a study to a screener. It is recorded in
`literature/screening/reveals.jsonl` under the events lock and journaled as
`SCREENING_PROPOSAL_REVEALED` without the outcome. A superseding event received
after a reveal of that study's proposal, by that screener and in the current
generation, is stamped `changed_after_reveal: true`, whether or not the outcome
changes; the methods paragraph can compare outcomes from the event chain.
Events stored before M1b-0 keep `false`, which for them means "not tracked".

## 2026-11-04 — `accept-corpus` is the screening entry path until Packet B (M0)

`nexus-scholar accept-corpus` builds the Contract-v1 corpus snapshot with the
search kit's `build_corpus_snapshot_artifact` from `literature/verified.json`.
It publishes the snapshot through the existing acceptance gate, which
validates it against the frozen schema and journals the acceptance; `prepare`
then works on a fresh workspace.
- **RIS import:** `--ris <file>` imports a RIS export first. Each record gets
  a record-derived `SCI-` id (from title, year, DOI and author names), so a
  re-import yields the same ids. The import refuses to overwrite an existing
  `verified.json`.
- **Re-runs:** re-running on unchanged records publishes nothing.
- **No CSV importer:** none exists yet, so CSV is deferred.
- **Snapshot semantics unchanged:** the builder and acceptance are reused as
  they are, so the lane stays STANDARD.
- **Packet B:** full adoption, with discovery producing the snapshot itself,
  remains M3.

## 2026-11-04 — Approval: terminal-only code; event-decided batches need no worker step (CON-02/03)

**The code stays on the terminal.** The approval code is printed only in the
terminal running `nexus-scholar serve`, never returned over HTTP, and the
researcher types it into the publish screen. This keeps the existing pinned
rule: something that can call the console API (a malicious page that got the
token, another local process) still cannot approve on its own. The contract's
`qr_payload` for `pairing/begin` is dropped; spec 09 follows.

**Events replace the worker step.** A batch decided entirely by human decision
events is approved on its event projection. No worker recommendation is
required. The approval binds that batch's projected bytes only, never another
batch's (CON-03), and the approver is recorded as an unauthenticated local
attestation, not an identity (CON-02). The worker path stays for
agent-screened batches. Researcher's choices, 2026-11-04.

## 2026-11-04 — The v03 screening labels are human-confirmed: the M1b eval set

`uav-crop-weed-v03` has a signed screening confirmation:
`literature/screening/HUMAN_CONFIRMATION.json` (`HumanConfirmation@1`, PR
#172, 2026-10-31). Its lead reviewer, Mouadh BEKHOUCHE, confirmed all 14,150
agent decisions and changed none, and the record pins the 283 decision files
by SHA-256. The M0 note that v03 had no human labels was wrong: it read the
README and the `decision_status: FINAL_AGENT_UNCONFIRMED` fields and missed
this record.

**Consequences:**
- The v03 labels are the human-confirmed eval set for the M1b prompt gate
  (agent-system §5).
- The 200-record AI reference screening (`method: LLM`, 2026-11-04) is no
  longer needed as a stopgap. It stays available only as a model-versus-human
  comparison.
- The stale status fields are not rewritten: they sit in hashed decision
  files, a published report and the append-only journal. The README says so,
  and a `SCREENING_CONFIRMATION_RECOGNISED` journal row records that the
  confirmation supersedes them.

**Caveat for the methods text:** these are confirmations of agent drafts,
none changed. The eval measures recall against labels a human reviewed with
the draft in view, not against independent blind screening.

## 2026-11-04 — Unclear records go forward to full text (PRISMA)

A record the researcher marks Unclear (stored as `MAYBE`, labelled "Unclear →
full text") passes title and abstract screening. In the PRISMA flow it is
counted in "records sought for retrieval" with the includes, and shown on its
own line (`unclear_to_full_text`), never with the exclusions. The collector
stops refusing `MAYBE` at finalize (M1a), and `check_golden_workspace.py`
reconciles included + unclear + excluded + conflicts with records screened.
Researcher's choice, 2026-11-04.

## 2026-11-04 — CON-13 is guarded outside the Contract v1 lock

`contracts/acceptance.py` and `contracts/chain.py` check batch identity,
binding and membership only when a `screening_decisions` artifact has exactly
one `screening_batch` parent; zero or several parents skip those checks
(CON-13). Both files are locked by the Contract v1 baseline. Rather than a
contract change, the harness refuses to submit a decisions artifact without
exactly one batch parent, before it calls the frozen gate (M1a). A caller that
bypasses the harness and calls `accept_artifact` directly is not covered; that
gap is recorded for Contract v1.1. Researcher's choice, 2026-11-04.

## 2026-11-04 — Console guards and the `--lan` threat model (INC-01)

**Threats.** In stage 1 the console holds unpublished review data and can run
kit commands. Three kinds of caller can reach it:
- a web page in the researcher's browser: cross-site requests, and DNS
  rebinding through a name that resolves to 127.0.0.1;
- another process on the machine, including an AI agent's sandbox;
- from M2, a device on the same LAN.

**Guards, on every request** (`console/serve.py`):
- **Host.** The `Host` must be a loopback name (`HOST_REFUSED`).
- **Origin.** A browser `Origin` must be loopback (`ACTION_ORIGIN_REFUSED`,
  the code the screening actions already used).
- **Token.** Every route except `/healthz` needs `Authorization: Bearer
  <token>` (`TOKEN_REQUIRED`). `serve` takes the token from
  `NEXUS_CONSOLE_TOKEN`, or generates one and prints it once.
- **Loopback bind.** `serve` refuses a non-loopback `--host`.

**What a caller can run.**
- **Pipeline nodes** may run only the kit CLIs and the screening handoff
  script (`COMMAND_NOT_ALLOWED` in `validate_spec`). This applies in the
  console and in `scholar-harness run`; tests that run `python -c` stub nodes
  extend the list explicitly.
- **Jobs** run only in the served workspace (`WORKSPACE_MISMATCH`).

**The UI proxy** adds the token server-side, so the browser never holds it. It
answers only on a loopback host and forwards a POST only when its `Origin` is
the app's own.

**Residual risk, accepted for stage 1.** A process running as the same user
can forge `Origin` and POST through the proxy. It already has the user's
files, so this grants no new privilege. M5-slim serves the UI from the same
FastAPI process and replaces the proxy with a session cookie.

**`--lan` (M2).** It never exposes this app. `nexus-scholar ui --lan` mounts a
separate restricted sub-app on the LAN address:
- **Routes:** screening reads and decision-event POSTs only. The jobs,
  pipelines, streams and audit-writer routers are never mounted there; a test
  proves they are unreachable.
- **Pairing:** a phone pairs through a one-time token in the desktop QR code.
  The token lives 2 minutes and is exchanged for a session cookie scoped to
  the sub-app; no token appears in a URL after the first load.
- **Session end:** on stop, on process exit, or after 12 hours.
- **Transport:** plain HTTP on the LAN, so someone on the network can read
  abstracts and decisions in transit. That is accepted for stage 1, shown on
  the pairing screen, and fixed by opt-in HTTPS (`mkcert`) or the sync tier.
- **Desktop only:** approval stays on the desktop (contract §4, §9.1).

## 2026-11-04 — MCP tool paths are contained in the workspace (AGT-01)

Every path argument of a `scholar-agent` tool, for reading and for writing, must
resolve inside the MCP workspace (`--workspace`, else `NEXUS_MCP_WORKSPACE`, else
the repository root). Relative paths are joined onto it; absolute paths are
allowed only when they land inside it. Symlinks and `..` are resolved first. An
escaping path raises `PathOutsideWorkspace` (`PATH_OUTSIDE_WORKSPACE`) before
any I/O, which the MCP client sees as a tool error. Consequence: a researcher
who wants a tool to read a file elsewhere (a PDF in Downloads) copies it into
the workspace first. Reads are contained too, because an agent could otherwise
use a reader tool to pull any local file into its context. Path parameters never pass
anything through by its content (`'["/../x"]'` is valid JSON and, on POSIX, a
legal path). Only the four parameters that accept an inline payload
(`intent_json`, `protocol_json`, `screeners_json`, `adjudication_json`) keep a
value that parses as JSON, and never open it as a path (review findings, M0).

## 2026-11-04 — MCP keys stay in the env file, never in a config file (CORE-17)

`setup-mcp` used to copy provider keys from `.env` into an `env:` block of each
MCP config, including `<workspace>/.mcp.json` and `.cursor/mcp.json`, which git
tracked. Now it adds `--env-file <path>` to the server command, and
`scholar-agent` loads the approved keys (`SCHOLAR_*`, `NEXUS_*`, the three
provider keys) from that file at start. Variables already set in the
environment win. No config file holds a key value, VS Code works like the
other targets, and `.env`, `.mcp.json` and `.cursor/mcp.json` are gitignored.
Configs written by older versions keep their `env:` block until `setup-mcp` is
run again.

## 2026-11-04 — Screening API contract accepted

The researcher decided the contract's six open questions:
- a fresh approval code for each batch generation, refused while any phone has queued events;
- an OS file lock on each screener's event file;
- an Exclude on the phone needs a reason only, with no checklist;
- 200 events per request, with the UI sending larger backlogs in chunks;
- methods-paragraph wording and sample-audit size deferred to M5-slim;
- a dated price table, updated each release, behind the cost estimate.

All nine screening screen specs are now FINAL. Details:
[`architecture/screening-api-contract.md`](architecture/screening-api-contract.md) §9.

## 2026-11-03 — Plan revised after independent review: screening wedge at week 6

An independent review of the production plan found that screening could not be
reached before week 6: no code builds a corpus snapshot outside tests, and the
import path was not scheduled. It also found that M1 was too large for one
person. The researcher accepted three changes:

- **Order.** M0 (adding a minimal `accept-corpus` entry path) → M1a screening
  backend → M1b desktop UI and driver → M2 mobile → M5-slim package, where the
  wedge ships. Discovery (M3) is stretch. The web Inception wizard (M4) moves
  past the two-month horizon; inception stays CLI/MCP, labelled beta.
- **You see every record by default.** The agent orders the queue and
  proposes. Exclusion without a human look is an explicit opt-in with a sample
  audit, and the methods paragraph discloses it (PRISMA 2020 item 8).
- **Unclear is stored as the existing `ScreeningDecisionValue.MAYBE`.** It is
  labelled "Unclear → full text". There is no Contract v1 version change; only
  the collector's refusal of MAYBE at finalize changes, in M1a.

The review also moved the prompt-gate eval from the 30-record golden workspace
to the human-labelled `uav-crop-weed-v03` screening data (at least 200 records,
at least 30 includes). It restricted `--lan` to a sub-app without the
job-running routers, and keyed decision IDs on the client event ID so replays
cannot void approvals. Details: `roadmap/production-plan.md` §2, §4, §6;
`architecture/agent-system.md` §2–§6, §8.

## 2026-11-03 — Agent system: proposals only, least autonomy per job

The AI behind Phases 0–2 is built as versioned *tasks*: a prompt, an output
schema, a model and effort setting, and an eval set. Most tasks are plain code
or single structured calls. Only the inception conversation and the
researcher's own Claude Code or Claude Desktop (through MCP) run agent loops.
Model output is always a proposal in an append-only store with full provenance
(model, prompt hash, input hash, checks, usage). Plain-code validators check
each proposal, and anything that fails, refuses or is truncated goes to the
researcher as Unclear, never Exclude. Only the engine writes artifacts and the
journal, and only after a human decision. The in-app driver (the researcher's
own API key, with Message Batches and prompt caching) and the MCP driver share
the same tasks. Changing a prompt, model or effort setting needs a new task
version and an eval re-run, mirroring the contract-baseline gate. Default
model: `claude-opus-5-5`. Open then: whether to keep Gemini (decided since: it
stays), whether to build the in-app inception chat (decided since: milestone
M10e), and whether a cheaper screening model holds recall (measured 2026-11-19, M9a).
Design: [`architecture/agent-system.md`](architecture/agent-system.md).

## 2026-11-03 — Claude Code dev workflow and area-based test gates

The OpenCode four-agent loop is no longer the development workflow; the files
stay, baseline-locked, as history. Development runs in Claude Code with three
project slash commands (`/milestone`, `/gate`, `/ship` in `.claude/skills/`) and
four narrow subagents (`.claude/agents/`): a read-only finding auditor, a test
gatekeeper, an independent milestone reviewer, and a UX spec writer. The
researcher approves milestone starts, contract decisions and every push.

The test selector was keyed to E3 RAG tasks, so after the one-package merge a
screening edit selected an unrelated RAG test and a search, protocol or UI edit
fell back to the full ten-minute Python suite. Selection is now by source area
(`areas` in `docs/architecture/test_gate_manifest.json`, `--changed` from git).
Inner gates skip `@pytest.mark.slow`, and the PR gate runs the full suite once in
parallel (`pytest-xdist`, `-n auto`). The full suite still runs once per PR
candidate; that rule did not change. Details are in
[`architecture/test_gate_policy.md`](architecture/test_gate_policy.md) §Selector.

## 2026-11-03 — Deployment: local engine first, hybrid sync later (option C staged from A0)

Nexus Scholar ships first as a local engine. `uv tool install nexus-scholar`,
then `nexus-scholar ui`, serves the static-exported research UI and `/api/v1`
from the one FastAPI process on loopback, behind a per-launch token. `--lan`
plus a QR code lets a phone on the same network screen. Workspaces stay local
folders, with no hosted infrastructure. AI proposals come first from the
researcher's own Claude Code or Claude Desktop through the `scholar-agent` MCP
server, which writes proposals only. A bring-your-own Anthropic key is the
second path, for in-app runs. Whether Gemini stays as a third option was open (decided since: it stays)
(`architecture/agent-system.md` §9). The maintainer never pays for or resells
tokens. The engine, UI and MCP server stay MIT. Paid features (end-to-end
encrypted sync of decision and journal events, team dual screening with real
κ, institutional SSO) go in a separate proprietary service, built only after
10–20 real users. Stage 1 sells onboarding and support, not code-gated
features. A signed desktop app (Tauri with a Python sidecar) waits for user
demand. Hosted web-first (option B) was rejected: it contradicts the privacy
of unpublished reviews and adds operations work that one maintainer cannot
carry. The full option study is in
[`roadmap/production-plan.md`](roadmap/production-plan.md) §5.

## 2026-11-03 — Brand book replaces VISUAL_DIRECTION as the UI design system

`docs/ux/brand/tokens.json` and `BRAND_BOOK.md` become the design system of
record for `apps/research-ui`. This reverses VISUAL_DIRECTION decision D1 (no
web fonts, no radius, light only). Tokens generate the Tailwind 4 theme, with
light and dark modes. The fonts (Literata, Public Sans, IBM Plex Mono) are
self-hosted, not loaded from Google, so the tool works offline and makes no
third-party calls. VISUAL_DIRECTION rules that do not conflict are kept as
amendments. GATES and the browser colour tests are updated in the same PR.

## 2026-11-03 — Production scope: Inception, Discovery, Screening over two months

Only Phases 0–2 are brought to production, on the two-month sequence M0–M5 in
[`roadmap/production-plan.md`](roadmap/production-plan.md) §6. Screening comes
first. The quality gate is a real end-to-end run on the golden UAV workspace,
not the autonomous agent loop. Everything else is labelled "not production —
parked" in UI, docs, CLI and MCP.

## 2026-11-03 — One package instead of eight kit repositories

The harness and the eight `scholar-*-kit` packages ship as one distribution,
`nexus-scholar`, from the root `pyproject.toml`. Kit code lives in
`src/scholar_<kit>/`, kit tests in `tests/kits/<kit>/`. The per-kit repositories,
vendored snapshots, `plugins.json` pins, pin codegen, installer and separate
metapackage were removed: syncing eight repositories cost a single maintainer a
great deal and bought nothing while no one installs a kit on its own. If a kit
gains independent users it can be split out again with `git subtree split`.
Contract producer provenance keeps the component names and now reports the
package version and repository commit. See the
[assessment](assessment/README.md) for why this came first.

## 2026-11-03 — Fresh assessment replaces earlier audit material as the current view

[`assessment/`](assessment/README.md) is the current, evidence-backed view of
the harness and kits, with a ranked P0/P1/P2 list. Older dated reviews remain
as history only.

## 2026-10-26 — Human confirmation is a separate package outside the frozen baseline (Phase C)

`contracts/confirmation/` and its schema sit outside the non-recursive globs
that `generate_contract_baseline.py` hashes, so adding confirmation did not
change the frozen Contract v1 payload. The refusal registry is imported, never
extended. Behaviour: [`architecture/confirmation.md`](architecture/confirmation.md).
Spec: `specs/agent-layer-portability/06_human_confirmation.md`.
Original record: `docs/architecture/decision_phase_c_confirmation_2026-10-26.md`.

## 2026-10-26 — The agent envelope is a package, not a flat module (Phase B)

`scholar_harness.contracts.envelope` is a package for the same reason: a flat
module or a schema under `schemas/v1/` would have entered the frozen lock set.
Refusal codes: [`architecture/refusals.md`](architecture/refusals.md).
Spec: `specs/agent-layer-portability/02_envelope_and_refusals.md`.
Original record: `docs/architecture/decision_phase_b_envelope_2026-10-26.md`.

## 2026-10-25 — Agent roles are generated from `roles/*.json` (Phase A)

Role definitions (`roles/*.json` plus prompts) are the source; the OpenCode
agent files are generated by `scripts/generate_agent_roles.py`. Write
permissions are derived (a critic is denied what it judges; `deny_glob` is a
write denylist; `audit/journal.jsonl` is protected).
Spec: `specs/agent-layer-portability/01_role_model.md`.
Original record: `docs/architecture/decision_phase_a_role_generation_2026-10-25.md`.

## 2026-10-23 — T-SC1 accepted without a recorded independent review (accepted risk)

PR #144 (cross-kit canonical and identifier parity pin) entered `main` without
the independent reviewer and tester evidence the gates require. The researcher
accepted that risk explicitly; it is not a precedent for skipping review.
Original record: `docs/architecture/decision_t_sc1_acceptance_without_review_2026-10-23.md`.

## 2026-10-13 — Product direction: the individual researcher

The first user is an individual researcher running a review directly in Nexus:
a local research service with a browser review interface, with CLI and MCP as
advanced interfaces. First journey: provisional protocol → bounded retrieval →
review recommendations with preserved overrides → authorized screening
decisions → transparent screening record. Full-text charting and synthesis
follow as separately validated capabilities.
Original record: `docs/architecture/decisions/individual-researcher-product.md`.

## 2026-10-12 — TD-E3-CURRENTNESS: stale extracted bodies are refused (Option B)

When an extracted body is stale, the indexing stage writes one
`RAG_INDEX_REJECTED` event and returns the typed `STALE_EXTRACTED_BODY` refusal
before any backend call or index publication (it previously crashed on an
unsupported `parameters=` argument).
Original record: `docs/architecture/decisions/td_e3_currentness_decision.md`.

## 2026-10-12 — Agent instructions must reference files that exist

The baseline-locked agent definitions pointed at two spec files that never
existed; they were corrected to `10_cross_kit_contracts.md` and
`12_execution_roadmap.md`. Backticked paths are not caught by link checks, so
such references need review.
Original record: `docs/architecture/decisions/agent-instruction-reference-repair.md`.

## 2026-10-10/12 — Authorized screening: protected publisher, restricted worker (AG)

The researcher approved a protected local publisher with a restricted
scientific worker: agents may propose screening decisions, but publication of
final decisions requires the researcher's authorization. Approval of the
direction is not proof of isolation; the
[assessment](assessment/harness-contracts-screening.md) (CON-02/03) found the
authorization still bypassable.
Current state: [`architecture/agent-controls/README.md`](architecture/agent-controls/README.md).
Original record: `docs/architecture/agent-controls/agent_controls_decision.md`.
