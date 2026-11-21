# M11a Query workbench

Branches: `dev/m11a/part-a-counts`, `dev/m11a/part-b-seeds-comparison`, `dev/m11a/part-c-screen`, `dev/m11a/part-d-plan-amend` (each from the then-current `origin/main`, or from the part before it while that part is not merged) · Lanes: A, B and D **RELEASE**, C **STANDARD** (as proposed; see each part's section) · Status: **BUILD IN PROGRESS** (build started 2026-11-21 on the researcher's "start the M11a build", from `origin/main` at `1f218054`; specification approved 2026-11-20, screens FINAL 2026-11-21) · Third in the agreed order (plan §6, "After the acceptance run")

Short page for the researcher: [`M11a-query-workbench-for-review.md`](M11a-query-workbench-for-review.md). Screens: [`docs/ux/phase0-inception/final/10-query-workbench.md`](../../ux/phase0-inception/final/10-query-workbench.md) and [`docs/ux/phase1-discovery/final/10-plan-amend-search.md`](../../ux/phase1-discovery/final/10-plan-amend-search.md) (both `Status: FINAL` since 2026-11-21). Decisions: `docs/decisions.md`, "2026-11-20 — M11a query workbench: the specification's choices" (accepted 2026-11-20).

Sources: `docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md` ("The search was too narrow", findings 3, 9, 18 to 21, 23, 24), `docs/roadmap/what-a-researcher-does.md` (step 2), plan §6 "After the acceptance run", `docs/decisions.md` "2026-11-20 — The order of work after the acceptance run" (those four are on PR #262, not yet on `main`), the Inception redesign proposal on the local branch `dev/ux/inception-redesign` (direction A, D1 to D15, decided 2026-11-20), and the code at `2436fe66`.

## What changed for the design since the specification (re-audit at `1f218054`, 2026-11-21)

The specification was written at `2436fe66`. Before part A the `phase-auditor` agent re-read every "reused" claim at `1f218054` (51 commits later: M3f-combined-corpus PR #263, H-run-small-fixes Parts B and C PRs #266 and #267, H-screening-drafts PR #261, H-quota-hang PR #259); read only, no network. What it changes for the build:

1. **Crossref is already left out of a joined query** for the harvest, Plan, Recall and the estimate (`scholar_search/plan.py`: `IGNORES_AND`, `default_choice`, `and_warnings`; `protocol_adapter.concept_count`). The workbench reads the same constant `IGNORES_AND` for its own counts (DoD 7) and adds no second rule. Nothing of the harvest side is redone.
2. **The default database choice has one function** (`plan.default_choice`). The workbench's Plan route starts from the protocol's list as written, so the Crossref row is drawn with its sentence (`not_comparable`) instead of disappearing; the screen sends the Plan picker's choice.
3. **arXiv's count is exact with a year window** (`estimate.UPPER_BOUND_WITH_YEARS` is empty since H-run-small-fixes Part B item 4). The row state `upper_bound` is kept as a field (`upper_bound`, always false today); no row says "at most" for arXiv any more. The comment the specification called stale was already corrected.
4. **A typed direction already matches on its words** (`recon.session.content_words`, `own_direction_evidence`, `match: "phrase" | "words"`). That is the direction rule (whole words, no plural folding) and stays as it is; the workbench's matcher is its own (`scholar_search.workbench.term_matches`, plurals folded), as decided (item 8).
5. **A used-up quota still becomes a failed row coded `PROVIDER_RATE_LIMITED`**, with the reset time only in the message: part A adds `quota_exhausted`, `resets_at` and `http_status` to `estimate.count_one`'s row (additive) and keeps the code.
6. **`GET /discovery/plan` now returns `concepts` as a number** (the concepts the query joins), not the list: part D still needs a read of the concept list for "Change the search".
7. **A staged export records the string the researcher stated** (`query` in `literature/raw/ris/sources.json`, M3f): part D's consequences list reads it; the screen specification's question 3 on Plan is answered by the code.
8. **M3f's staging is `literature/raw/ris/`**: comparison sets (part B) stay out of `literature/` entirely (`audit/query_development/comparison/` and beside the draft).
9. **`dedup._title_key` is still private**: part B makes it public, as planned.
10. The amendment path (`workspace_proposals.FIELD_OPS`, `decide`, `PROTOCOL_AMENDED`) and the method amendment (`screening/method.py`) are as the specification read them; line numbers moved.

Done items adjusted: DoD 7's harvest half is merged work (H-run-small-fixes Part B); DoD 7 here covers only the workbench's counts. DoD 1's row states: `upper_bound` cannot occur today (point 3). No other done item is already met by merged code.

## Goal

Let the researcher develop the search the way it is really done: edit concepts and synonyms, see what each database would return, and see what each concept costs, before the protocol freezes. Let them test the query against the papers they already know and against an export from a database the app cannot query, and be warned when those papers cannot test it. After the freeze, the same tool records a change of the search as an amendment from Discovery's Plan.

## What a researcher does today, and what goes wrong

On 2026-11-20 the researcher took a real scoping review through the installed wheel (sensor stress in multispectral UAV weed segmentation).

1. At Inception's step 5 they typed four concepts, each with synonyms: UAV, multispectral, weed, segmentation. The app joins concepts with AND. Nothing on that screen counts anything: the only numbers are "in n of 25" for each term in the first search's sample.
2. The protocol froze at "Create". The first counts for the real query appeared on Discovery's Plan: OpenAlex 166, Semantic Scholar 107, arXiv 7, Crossref 6,221. The Crossref number is for the words without the AND (finding 9); the screen gave no warning.
3. The recall check passed 4 of 4. All four seeds use a term of every concept, so the check could only pass (finding 20). The main session read it as "OpenAlex alone is enough".
4. Afterwards, by hand, outside the app: Scopus returned 130 records for the same query; 31 of them were not in the app's 166. Scopus counts with one concept dropped were 130 strict, 236 without UAV, 512 without multispectral. Relevant papers that use only one of "UAV" or "multispectral" were missed by every database. Nothing in the app could take the Scopus export as a comparison set (finding 21).
5. The fix was to merge UAV and multispectral into one concept. Because the concepts are frozen with the protocol, that meant a new workspace: OpenAlex 781, Semantic Scholar 539, arXiv 30, a final corpus of 1,062 works from five sources, and a fifth seed the strict query had missed.

What went wrong is that a decision with the largest effect on the review (four concepts or three) was made with no number in front of the researcher, and the one check that ran was unable to fail. Findings 18 (no screen shows what a concept costs, P1 for the review's quality) and 19 (the first counts come after the freeze, P1) are the core of this milestone; 20 and 21 complete it.

## Definition of done

Each item is checked by a test named in the build record, unless it says "live".

**Counts (part A)**
- [x] DoD 1. For a version of the query (concepts, synonyms, years, languages) and a set of databases, the engine answers per database: the exact string sent (the E1 translation), the total, its status, when it was counted and whether it came from the cache. The draft's version is sent by the browser and need not be saved first.
- [x] DoD 2. The same answer includes, for a query of two or more concepts, the count with each concept dropped, per database, and the gain against the full query.
- [x] DoD 3. On request, for one concept and one database, the count with each synonym of that concept removed ("what each synonym adds"). The number of requests is stated before it is sent.
- [x] DoD 4. Before any request, the answer to a dry call states how many requests a count would send per database, and refuses with `WORKBENCH_BUDGET_SPENT` when a database's daily budget would be passed. Nothing is sent on a keystroke.
- [x] DoD 5. Counts are kept in a persisted count log keyed by database and exact string; a repeated string is answered from it for 24 hours without a request. A failed count is kept as a record but never answers (wording aligned with (a), review of Part A).
- [x] DoD 6. A database whose quota is used up (`QuotaExhaustedError`) gets the row status `quota_used_up` with `resets_at`; the engine sends nothing more to it from the workbench until that time, across drafts and workspaces. Throttling, refusal, timeout and unavailability keep their existing codes.
- [x] DoD 7. For a query of two or more concepts Crossref is not counted by default; its row says it cannot combine concepts with AND. "Count anyway" counts it and the row is labelled "any of the words". Crossref is never part of the drop test, the seed check or the comparison.
- [x] DoD 8. The size line of M10b Part D (records, works range, screening hours, the warning against the planned size) is computed by `estimate.summarize` for the version shown, before and after the freeze.

**Seeds and comparison sets (part B)**
- [x] DoD 9. Seed check, without a database request: for each seed whose title and abstract are known, which concepts its words contain and which it lacks; a seed lacking a concept is "missed by the words of this query".
- [x] DoD 10. The warning "seeds cannot test this query" when every seed that could be read uses a term of every concept, and per concept when no seed lacks it. A seed with no readable text is "not read" and does not count either way.
- [ ] DoD 11. Seed check per database where one request can answer it (OpenAlex, by an identifier filter combined with the search; to be confirmed live). Other databases say "not checked here; the recall check on Plan runs the full query".
- [x] DoD 12. A RIS or NBIB export can be staged as a comparison set, with its database name, the string used there (optional) and the export date. It is stored apart from the corpus staging, is never accepted into a corpus, and can be removed.
- [x] DoD 13. The comparison report: "{n} of {m} {database} records are missing from what your query finds", with the missing titles listed, for each the concepts it lacks, and the terms (1 to 3 words) found in at least two missing records and in no concept, with their record counts, offered as synonym suggestions that are never applied without a click.
- [x] DoD 14. "What your query finds" is said in the report's own words and in this order of strength: found in the harvest (after a harvest, by DOI or normalised title, no request); found by OpenAlex (records with a DOI, one request per 50); matched by the query's words (title, abstract and keywords, no request).
- [x] DoD 15. At genesis the draft's query development (count log rows of the versions tried, the seed checks, the comparison sets) is copied into the workspace under `audit/query_development/`, listed in the preview's `files`.

**Inception screen (part C)**
- [x] DoD 16. The workbench is on Inception's step 5 as the concepts block and an evidence column, laid out as direction A's blocks (D10, D13); every state in the screen spec has its words in en, fr and ar; axe passes in light and dark.
- [x] DoD 17. Concept edits in the workbench: add, rename, remove a concept; add or remove a synonym; merge two concepts into one (OR); split a term out into a new concept. Operators stay OR within a concept and AND between concepts.
- [x] DoD 18. "Use this version" writes the draft's `concepts` through the normal save; counts shown for an earlier version say so until counted again.
- [x] DoD 19. Two fixed checks, never blockers: `QUERY_NOT_COUNTED` (note) and `SEEDS_CANNOT_TEST` (warning), in the M10b catalogue, shown at the field and at Review.

**Amendment from Plan (part D)**
- [x] DoD 20. On Plan, the workbench opens on the protocol's query. "Record this amendment" requires a one-sentence reason and writes through the M10c item 9(a) path (intent search fields, protocol recompiled with the genesis compiler, backup under `audit/amended/`, `PROTOCOL_AMENDED`), extended to replace the whole concept list; the journal row carries the reason, the source `researcher` and the counts before and after.
- [x] DoD 21. Before the amendment is recorded, the screen lists what it changes: each earlier search run (it can no longer become the corpus), staged exports (left as they are, with their stated strings), recall checks and estimates (no longer apply), open workspace proposals (become stale).
- [x] DoD 22. After a corpus is accepted the workbench still opens, counts and compares; it records nothing and says why.
- [x] DoD 23. Every new record and answer carries `query_key` (today always `main`).

**Closure**
- [ ] DoD 24. `generate_contract_baseline.py --check` current before and after each part.
- [ ] DoD 25 (live). The researcher develops one query in the app with real databases and a real Scopus export, and reports the result in this record.

## In and out

**In.** Counts per database for the query as edited; counts with each concept dropped; what each synonym adds (on request); a budget, a cache and honest words when a database refuses or its quota is used up; the seed check and its warning; comparison sets from RIS or NBIB; synonym suggestions from the pool, the seeds and the comparison set's missing records; the size line; the concepts block of Inception's step 5; the amendment from Plan; the two fixed checks; carrying the development into the workspace.

**Out, and where it goes.**
- Several named queries per review: M3j (contract decision). This design only keeps the door open (section (g)).
- Combining a harvest with exports into one corpus, and the Import and Hand-off screens: M3f-combined-corpus.
- Crossref off by default for the harvest, the retry of one failed database, weak direction phrases (findings 3 and 23), the Crossref value on Recall (finding 24): H-run-small-fixes. The workbench only follows the same Crossref rule for its own counts.
- CSV exports (IEEE Xplore's quick export, finding 25): not in M11a; the comparison set takes what Import takes.
- Any language model. The M9d tasks "synonyms" and "recall repair" are met here without a model: suggestions come from the pool, the seeds and the comparison set. Assistant proposals made over MCP (M10c) still appear at the field, as today. M10e (chat) waits.
- Direction A's frame (M10f-1), and the relayout of Explore and Direction in it (the rest of M10f-2): not in M11a (open question 2). The workbench is drawn as A's blocks and evidence column so it moves into the frame unchanged.
- Querying Scopus, Web of Science or any database behind an institutional sign-in. Never.
- Free boolean editing (NOT, nested groups, field tags). The query stays concepts joined by AND, terms joined by OR.
- The query translated for Scopus and Web of Science to copy: in part C only if open question 10 is accepted.

## The behaviour

### (a) Counts per database, the budget, the cache, refusals

**The version.** A version is `{query_key, concepts[{concept, synonyms[]}], start_year, end_year, languages}` plus the databases to ask. It is compiled by the compiler genesis uses (`scholar_search.protocol_adapter.compile_protocol_search` on a protocol-shaped dict), so the workbench never builds a query string of its own, and translated per database by `scholar_search.plan.translate_provider` (E1). Each row shows that exact string.

**When counts are sent.** Only when the researcher presses Count (or "What does each synonym add?"). An edit marks the shown counts "for the previous version" and changes nothing else. Before the button sends anything, the screen shows the cost: "Count: 15 requests (OpenAlex 5, Semantic Scholar 5, arXiv 5)". A version already in the cache costs nothing and the line says so.

**What one Count asks.** Per database: the full query, and, when there are two or more concepts, the query with each concept dropped. That is `concepts + 1` requests per database (5 for four concepts), except that a string already in the cache is not asked again; dropping concept B from two versions that differ only in B asks once.

**What each synonym adds** (on request, one concept, one database, default OpenAlex): the count with each synonym removed. Gain of a synonym = full count − count without it: the records reached only through that term. Requests: one per term of the concept. A term with gain 0 reads "adds nothing in OpenAlex today", never "remove it".

**The budget.** Each database has a daily budget of workbench requests (UTC day), shared by every draft and workspace on this computer, because a provider's quota belongs to the key, not to a review. Proposed defaults, constants in one place, to be set against each provider's published limits at build: OpenAlex 200, Semantic Scholar 100, arXiv 100, PubMed 100, Crossref 20. The budget exists to protect the harvest: on 2026-11-20 the OpenAlex quota ran out during a run. A Count that would pass a budget is refused before any request (`WORKBENCH_BUDGET_SPENT`, with the database and when it renews); counts in the cache still show. The screen shows what is left only when under a quarter remains.

**The cache, which is also the record.** A persisted, append-only count log: one row per request sent (`query_key`, database, exact string, years, language, status, total, `counted_at`, `requests`). Before genesis it lives beside the draft record; after genesis under the workspace (`audit/query_development/counts.jsonl`). A row younger than 24 hours answers the same string without a request; an older one is shown with its date and asked again only on Count. A failed row is kept as a record but never answers from the cache. The size estimate of Plan reads it too, so a version counted in the workbench is not counted again by the estimate. The log is not journaled row by row; the journal gets one row per recorded amendment and one at genesis.

**Rules kept from the estimate (M10b Part D).** Counts are refused while a harvest or a recall check runs in the workspace (`DISCOVERY_JOB_ACTIVE`: the rate limits are its), and need the contact email (`MAILTO_NOT_SET`) and, for OpenAlex, the key (`OPENALEX_KEY_NOT_SET`). A count never waits more than `COUNT_TIMEOUT` (45 s) per database. A database's failure is its row, never the answer's. arXiv with a year window is "at most n" (`UPPER_BOUND_WITH_YEARS`): since M3h-c its query carries the submission dates, so the count is already filtered, but a submission date is not the publication year (the comment at `estimate.py:42` still describes the older reason).

**New routes, not new fields on old ones.** The estimate (`EstimateBody`) and the recall check (`RecallBody`) take no query: they always use `protocol.json`, and a draft has none. So the workbench has its own routes, which build a `Query` from the version, and every new POST is added to the console's browser allow-list (`console/browser.py` `POST_PATHS`) and the proxy's list, kept equal.

**Row states and their words** (the screen spec has every string):

| Status | Example |
| :-- | :-- |
| `counting` | "Counting…" |
| `counted` | "781 · counted 14:02 UTC" |
| `cached` | "781 · counted today at 10:15 UTC" (or the date) |
| `upper_bound` | "at most 30 (arXiv filters years after the search)" |
| `stale_version` | "166 · for the previous version. Count again." |
| `quota_used_up` | "OpenAlex's daily quota is used up. It resets at 00:00 UTC, in 5 h 40 min. Last count: 166, today at 10:15 UTC." |
| `budget_spent` | "Today's counting budget for OpenAlex is used (200 requests). It renews at 00:00 UTC. The harvest's quota is kept for the harvest." |
| `rate_limited` | "Semantic Scholar is busy (it asked to slow down). Try again in a minute; the other counts stand." |
| `refused`, `unavailable`, `timeout` | "Semantic Scholar refused the request (HTTP 403)." / "…did not answer." / "…did not answer within 45 s." with the code under Details |
| `key_missing` | "OpenAlex needs your key. Add it in Settings." |
| `not_comparable` | Crossref, see (f) |
| `not_countable` | "This database cannot report a total." |
| `not_asked` | "Not in this search." |

**Quota memory.** When a count gets `QuotaExhaustedError`, the workbench stores `paused_until = resets_at` for that database and sends it nothing more until then (from any draft or workspace), answering `quota_used_up` from the stored time. A harvest is not blocked by this memory; it meets the quota itself (H-quota-hang).

### (b) What each concept costs

For each concept, per database: the count without it and the gain ("without UAV: 236, +106, ×1.8"). The table is the full query in the first column and one column per dropped concept; the largest gain is marked in words ("largest effect"), not colour alone.

**The note.** When dropping a concept at least doubles the count in at least one database that combines concepts, a note sits on that concept: "Without '{concept}', {database} finds {n} records instead of {m}. Read a few of them before deciding whether they belong." It never says to drop the concept: a concept that cuts 80 % of the results may be exactly right. Threshold ×2 is a constant (open question 6).

**Read what a concept removes** (on request, one concept, OpenAlex): the first 25 records of the query without that concept, minus those the full query's words also match, as titles with the concept's absence marked. One request. This is the researcher's "read the first two pages", without leaving the app.

**Merge.** The run's own fix (UAV OR multispectral in one concept) is one action: select two concepts, "Merge into one". The merged version is counted like any other; the screen then shows both versions side by side (the last counted and the current), so 166 → 781 is in front of the researcher.

### (c) The seed check

Seeds are the draft's `golden_seeds` (DOIs chosen at Direction from the pool, or typed, at most 25), and after genesis the protocol's `golden_seeds`.

**By the words (always, no request).** For each seed whose title and abstract are known (from the first search's pool; else one batched lookup by DOI, counted in the budget), the concepts its words contain, with the INC-21 whole-word match (`recon.session.term_occurs`). A seed that lacks a concept is shown "missed by the words of this query: no term of '{concept}' in its title or abstract", with the words it uses in that place offered as synonyms (recall repair without a model). This is a lower bound: databases also match keywords and stem words (open question 8).

**The warning.** When every seed that could be read uses a term of every concept: "Your {n} known papers each use a term of every concept, so they cannot show a paper this query misses. Add a known paper that does not say '{concept}', or compare with an export from another database." Per concept, when no seed lacks it: "No known paper lacks '{concept}'; the seeds cannot test it." A seed with no readable text is "not read" and counts neither way. With fewer than 3 readable seeds the warning reads "Too few known papers to test the query."

**Per database (where one request answers it).** OpenAlex: one request per 50 seeds combining an identifier filter with the query (to be confirmed live; if OpenAlex does not combine them, this row falls back to "not checked here"). Other databases: "Not checked here. The recall check on Plan runs the full query." The recall check itself is unchanged: it fetches the result up to the cap (a seed beyond the cap reads "not found") and looks up the titles of the seeds it found, so it is a harvest in miniature, not a count.

**Where a seed's words come from.** The first search's pool holds title and abstract for its records (`concept_report` reads them; only records with a DOI). The sample route (`GET …/recon/sample`) does not return abstracts, so the seed check reads the pool on the engine side. A seed typed by the researcher and not in the pool is looked up once by DOI (counted in the budget).

### (d) The comparison set

**Staging.** The researcher drops a RIS or NBIB file (the parsers Import uses), names the database (Scopus, Web of Science, IEEE Xplore, or their own words), may paste the string used there, and the export date (default today). It is stored as `cmp_NNN` beside the draft, or under the workspace in `audit/query_development/comparison/`, with the original file. It is never in the corpus staging, never accepted into a corpus, never deduplicated into anything; Remove deletes the set and leaves one line in the count log. Limits: 5 sets, 5,000 records each (constants).

**The report.** "{n} of {m} {database} records are missing from what your query finds." Then the missing titles (all of them, 20 per page), each with the concepts it lacks, and "Terms these records use that your query does not": terms of 1 to 3 words (the M4d candidate rule) in at least 2 missing records and related to no term of the query, at most 15, each "in 9 of 31 missing records". Each term can be added to a concept as a synonym with one click per term (the D5 suggestion look: "Suggested by the Scopus comparison · not yet yours"). No "add all".

**What "your query finds" means**, stated on the report, the strongest available:
1. After a harvest (Plan): in the harvest, by DOI or normalised title (the dedup identity). No request. This is how "31 of 130" was found by hand on 2026-11-20.
2. Found by OpenAlex: records with a DOI, one request per 50 (identifier filter and the query, as (c)); a second request per 50 without the query separates "not in OpenAlex" from "in OpenAlex, not found by your query". Opt-in, cost shown.
3. Matched by the query's words in the record's title, abstract and keywords. No request; always available. It finds a query that is too narrow; it cannot find a database's gaps (a missing abstract, a missing record).

Records without an abstract are counted apart ("12 have no abstract in the export; matched on title and keywords only").

### (e) Applying a change

**Before the freeze (Inception).** The workbench works on a version in the browser. "Use this version" puts it into the draft's `concepts` and saves through the normal `PUT` (D7: saving is unchanged). Nothing else in the draft moves: the criteria do not depend on concepts; the first search's sample and the direction stay; the per-term "in n of 25" counts are re-read after the save, as today. Every counted version stays in the count log, so the development is recorded. At genesis the log, the seed checks and the comparison sets are copied into `audit/query_development/`; a methods sentence can then say "the search was developed over {n} versions; the final counts were …" (the sentence itself is M12a's or the report's, not built here).

**After the freeze, before a corpus is accepted (Plan).** "Change the search" opens the workbench on the protocol's query. The researcher edits and counts as before. "Record this amendment" asks for one sentence (why) and shows the consequences, then writes through the M10c item 9(a) amendment path: `intent.json` search fields, `protocol.json` recompiled by the genesis compiler, the three files backed up to `audit/amended/<stamp>/`, `PROTOCOL_AMENDED` with `source: "researcher"`, the reason, the old and new fingerprints and the counts before and after. The guard `PROTOCOL_AMENDMENT_REFUSED` (`outside_search`) still applies. The path gains one operation, "replace the concept list", because removing, renaming and merging concepts are not among today's operations (M10c item 16 allows add only; open question 1). It also gains a caller: today only an assistant can create a workspace proposal (`assistant.propose_on_workspace`, reached over MCP); the console has only list, apply and reject. The researcher's amendment is therefore a new route (`POST /api/v1/discovery/workbench/amend`) that calls the same compile, guard, backup and journal code directly, not a proposal the researcher makes and applies to themselves. It rewrites `SCREENING_CRITERIA.md` as 9(a) does (the criteria text is unchanged; the file is recompiled).

What it does to what exists (the existing behaviours of M10c item 21, listed on the confirmation, nothing new added):
- an earlier search run reads `search_changed`; it can no longer become the corpus (`PROTOCOL_CHANGED_SINCE_RUN`); the researcher harvests again. The confirmation names the run and its size: "run_002 (781 records) was searched with the earlier query. After this amendment it cannot become the corpus; harvest again." (Adding only the difference is M3j.)
- recall checks and size estimates made under the old fingerprint stop applying; counts in the log stay, keyed by string, so the new version's counts are reused;
- open workspace proposals become stale;
- staged exports stay staged, untouched. They were searched in their own databases with the string the researcher typed there; the confirmation lists them with that string ("Scopus, 618 records, staged 20 Nov") and says "If you change that search too, export again and replace the file." Whether a staged export must be re-confirmed after an amendment is M3f's rule; this milestone only lists them.
- a refusal while a harvest or a check runs (`DISCOVERY_JOB_ACTIVE`).

**After a corpus is accepted.** The workbench opens, counts, compares with the corpus (case 1 of (d)) and checks seeds; "Record this amendment" is replaced by: "The corpus is accepted, so the search is not amended here. A new search added to this corpus comes with M3j; until then, start a new workspace from this protocol." (the M10b Part A start-from-protocol path). Screening is untouched.

### (f) Crossref

Crossref's API cannot express the AND between concepts (finding 9). The app's translation turns AND into `+` and OR into a blank (`providers/crossref.py`, `operator_map`) and sends it as the `query` parameter, which Crossref reads as a bag of words ranked by relevance; the string on Plan looks as if it kept the AND, and the count does not. For the run's query it reported 6,221 against OpenAlex's 166. For a query of one concept its count is comparable; for two or more it is not. So, for two or more concepts:
- not counted by default (no request spent); the row reads "Crossref cannot combine concepts with AND. Its count would be for any of your words, so it is not shown. Count anyway";
- "Count anyway" counts the full query only; the number reads "6,221 · any of the words, not your query";
- never in the drop test, the seed check per database, the comparison or the size line's works range.

The same rule for the harvest itself (Crossref off by default) is H-run-small-fixes'; the two must not disagree, so the workbench reads the same constant if that milestone adds one.

### (g) Several queries per review later (M3j)

Nothing in M11a assumes there will only ever be one query:
- every count row, seed check, comparison result and amendment record carries `query_key` (today always `main`, the only query a protocol holds);
- the workbench edits one query at a time; its header names it ("Search: main") where M3j will put a selector;
- comparison sets and seeds belong to the review, not to a query; their results are computed per `query_key` and, when M3j arrives, for the union (a seed found by any query is found);
- the drop test and the synonym gains are per query;
- the amendment record names the query it changed; M11a writes nothing that M3j's storage decision would have to migrate other than `protocol.json` itself, which M3j's contract decision owns.

## Parts, one PR each

| Part | Contents | Lane | Why that lane | Depends on |
| :-- | :-- | :-- | :-- | :-- |
| **A. Counts engine** | `scholar_search/workbench.py` (pure: compile a version, list the requests, drop and synonym variants, read the log); `scholar_harness/query_workbench.py` (count log, budget, quota memory); routes `POST /api/v1/inception/drafts/{id}/workbench/counts` and `POST /api/v1/discovery/workbench/counts` with a `dry_run` flag; refusal codes `WORKBENCH_BUDGET_SPENT`, `WORKBENCH_VERSION_INVALID`; the `quota_used_up` row status; the estimate reads the log | RELEASE | new public routes and refusal codes, a persisted file, a new row status in the estimate answer | none |
| **B. Seeds and comparison** | local seed check and warning; OpenAlex identifier check (behind a flag until confirmed live); comparison sets (stage, list, remove, report, missing terms); genesis copies `audit/query_development/` and lists it in the preview's `files`; checks `QUERY_NOT_COUNTED`, `SEEDS_CANNOT_TEST` | RELEASE | new routes, new genesis files in a public preview answer, new check ids | A |
| **C. Inception screen** | the concepts block and evidence column on step 5 (spec `10-query-workbench`), concept edits incl. merge and split, side-by-side versions, every state, en/fr/ar, axe light and dark | STANDARD (UI) | browser only, over A and B | A (B for its panels) |
| **D. Amendment from Plan** | "replace the concept list" on the 9(a) path, `source: "researcher"` and the reason; the consequences listing; the Plan screen (spec `10-plan-amend-search`); read-only after acceptance | RELEASE | a protocol write after genesis, an accepted decision changed (M10c item 16) | A, C |

Inner and checkpoint gates by `scripts/select_test_gate.py --changed main`; the full suite once per PR. All tests offline: provider answers through the existing cassettes and doubles; no live call in CI.

## Reused and new

Each reuse claim was checked against the code at `2436fe66` (the `phase-auditor` agent and by hand); the evidence is in "Reuse audit" below.

| Need | Reused | New |
| :-- | :-- | :-- |
| One count per database | `scholar_search.estimate.count_one` / `count_providers`, `BaseAPIProvider.count` on OpenAlex, Semantic Scholar, Crossref, arXiv, PubMed | variants (drop, synonym) are versions sent through the same function |
| Query string from concepts | `protocol_adapter.compile_protocol_search` (the genesis compiler) | a protocol-shaped dict built from a draft version |
| Exact string per database | `plan.translate_provider` (E1) | none |
| Size line | `estimate.summarize`, `size_limit.size_limit` (planned size) | at Inception, the planned size from the draft's `pool_max` |
| Typed provider errors | `engine.provider_error_code`; `QuotaExhaustedError` with `resets_at` (H-quota-hang) | row status `quota_used_up`; the quota memory across requests |
| Cache | the estimate's rules (failed rows never kept; no counting during a job) | persisted log keyed by exact string, 24 h, shared with the estimate |
| Term matching | `recon.session.term_occurs` (INC-21), `recon.distiller._term_candidates`, `recon.vocabulary.concept_report` | the boolean match of a whole version against one record |
| Seeds | `Draft.golden_seeds`, `recall.validate_seeds`, the recall check on Plan (unchanged) | local seed check, warning, OpenAlex identifier check |
| Export parsing | the RIS and NBIB importers of Import | the comparison store (apart from staging) and its report |
| Matching an export to a harvest | the dedup identity (DOI, normalised title) | the report |
| Suggestions | the M10b proposal look (D5), fixed checks catalogue (`02-checks`) | sources `comparison:<cmp id>`, `seed:<doi>`; two checks |
| Amendment after genesis | `workspace_proposals` apply path (compile, guard, backup, `PROTOCOL_AMENDED`) | "replace the concept list"; `source: "researcher"`; reason; counts in the journal row |
| Consequences | `search_changed`, `PROTOCOL_CHANGED_SINCE_RUN`, fingerprint-keyed checks (M10c item 21) | the listing before Record |

The method amendment of H-screening-drafts (`screening/method.py`) is **not** the path for the search: it amends `blinding` and `not_reported` beside the signed protocol and never moves the fingerprint. A search change must move it, because the harvest is bound to the query; 9(a) does that and is already accepted. The record format (who, when, from, to, why) is what M11a takes from it.

## Reuse audit

Run by the `phase-auditor` agent on 2026-11-20 at `2436fe66`, read only, no network; two of its locations re-checked by hand. Verdicts: T true, P partly (the correction is what this spec now says).

| # | Claim | Verdict | Evidence | What the spec takes from the correction |
| :-- | :-- | :-- | :-- | :-- |
| 1 | `count_one` / `count_providers`, one count per database, 45 s, statuses `counted` / `not_countable` / `failed` | T | `scholar_search/estimate.py:37,67-90`; `count` at `providers/openalex.py:255`, `semanticscholar.py:132`, `crossref.py:118`, `arxiv.py:335`, `pubmed.py:272`; base raises `NotImplementedError` (`base.py:120`) | One HTTP GET each (OpenAlex `per-page=1`, S2 bulk first page `fields=paperId`, Crossref `rows=0`, arXiv `max_results=1`, PubMed ESearch `retmax=0`), with the shared client's retries |
| 2 | Estimate route: protocol only, guards, in-memory cache 600 s, recall totals, no file | T | `console/api/discovery.py:1056-1178` (cache key `:1133`, recall reuse `:1138-1146`, failed rows dropped `:1157`) | The body takes no query: the workbench needs its own routes (a), not a field on this one |
| 3 | Quota becomes a `failed` row coded `PROVIDER_RATE_LIMITED`, reset time only in the message | T | `exceptions.py:58-72`, `estimate.py:79-80`, `engine.py:64-65` | No process-wide pause memory exists (`verifier.py:136` per verifier; `http_client` stores nothing): the quota memory is new |
| 4 | Recall check runs the whole query, `MAX_SEEDS` 25, job, file, journal | P | `recall.py:28,87-96,149-`; route `discovery.py:1013-1052` | Fetches up to the cap and looks up titles; not refused after acceptance; no OpenAlex-key guard (c) |
| 5 | No route compiles or counts a draft before genesis | T | `GET /discovery/plan` reads `protocol.json` only (`discovery.py:459-503`); `compile_protocol_search` and `compile_plan` accept a dict | New draft route builds its `Query` in memory |
| 6 | Crossref loses the AND | P | `providers/crossref.py` `operator_map` AND→`+`, OR→blank, sent as `query` | (f) says how, and that the string looks as if it kept the AND |
| 7 | `compile_protocol_search`: OR groups joined by AND, quoting, years, first language, `id` = protocol id | T | `scholar_search/protocol_adapter.py:34-85` | Falls back to the quoted title with no concepts: a version with no concept is refused (`WORKBENCH_VERSION_INVALID`) |
| 8 | Draft fields; no database list; databases from the playbook preset | T | `inception/steps.py:200-240`, `inception/intent.py:402`, `scholar_protocol/compiler.py:190` | Explore's probe uses the topic (`keyword_query(draft.topic)`) or a typed query, not the concepts, and the M10a picker's databases (`console/api/recon.py:312-359`); the sample route returns no abstracts (`recon/sample.py:102-139`). `golden_seeds` is validated as DOIs (`steps.py:186`, re-checked by hand) |
| 9 | `term_occurs` (whole words, no stemming), `concept_report`, ≥ 2 records, ≤ 10 suggestions | T | `recon/session.py:111` (re-checked by hand; the auditor placed it in `vocabulary.py`, which imports it), `recon/vocabulary.py:24-79`, route `recon.py:454-468` | Only pool records with a DOI; title and abstract |
| 10 | 9(a) apply path; `FIELD_OPS` add only for concepts | T | `workspace_proposals.py:52-63,266-271,418-453` | Only an assistant can create a workspace proposal (`assistant.py:477`, MCP `scholar_agent/server.py:2361`): the researcher's amendment is a new route over the same code (e) |
| 11 | Moved fingerprint: `search_changed`, `PROTOCOL_CHANGED_SINCE_RUN`, checks keyed by fingerprint | T | `pipeline/discovery.py:599-622`, `corpus_accept.py:279-298`, `console/discovery_checks.py:255-259`, `discovery.py:1039,1133` | Any protocol edit invalidates the estimate cache: the workbench log is keyed by exact string instead, so it survives |
| 12 | Method amendment: `blinding`, `not_reported` only, never touches `protocol.json` | T | `screening/method.py:133-141,207-273` | Not the path for the search (see above) |
| 13 | RIS and NBIB parsers; staging; binding | P | `scholar_search/importers.py` `RISImporter:31`, `NBIBImporter:157`; staging `POST /api/v1/screening/corpus/sources` (`console/api/screening_v1.py:662`), `corpus_accept.stage_ris_source:341-428`, files under `literature/raw/ris/` | Staged exports are not bound to the fingerprint until accept (`corpus_accept.py:785-854`); CSV is refused (`SOURCE_NOT_RIS`). A comparison set must not use this route or folder |
| 14 | Proposal object and fixed checks; sources | P | `inception/proposals.py:169-183`; checks in `inception/checks.py` | `CREATING_SOURCES` is `check`, `import`; others come through a wider tuple. Existing concept checks: `CONCEPTS_NONE`, `CONCEPT_TERM_MISSING`, `CONCEPT_NOT_ANCHORED`, `CONCEPTS_ONE_ONLY` (step `criteria`). M11a adds sources `comparison:`, `seed:` the same way |
| 15 | `size_limit` reads `pool_max` | T | `size_limit.py:20-29` | At Inception the draft's `pool_max` gives the same value |
| 16 | Refusal codes exist | T | `console/refusals.py:78-216`, `CONSOLE_REFUSALS:386` | None missing |
| 17 | OpenAlex parameter; arXiv upper bound | P | `providers/openalex.py:189-216` (boolean text goes to `search.title_and_abstract`); `estimate.py:42-43` | arXiv's reason changed with M3h-c (a) |
| 18 | UI components | T | `apps/research-ui/components/inception-criteria.tsx` (concept editor about `:353-368`), `discovery-estimate.tsx:101`, `discovery-proposals.tsx:30` | The screen specs name them |
| 19 | Side files outside the Contract v1 baseline | T | `docs/architecture/contract_v1_baseline.json` names none of `proposals.jsonl`, `recall_checks`, `core_concepts`, `golden_seeds`, drafts | `audit/query_development/` is outside it; a protocol schema change would not be (none here). Drift check not run (docs only) |
| 20 | A normalised-title function for matching | P | `scholar_search/dedup.py:10-12` `_title_key` (private), `Deduplicator._same_identifier:224`, `_normalize_doi:252` | Part B makes `_title_key` public or calls `Deduplicator`; no second definition |

Also found: the console's browser allow-list (`console/browser.py:39-75`) must name every new POST route; the estimate's `from_recall_check` totals came from a capped fetch and can differ from a count.

## Risks

1. **Quotas.** Every count is someone else's service. A researcher who counts thirty versions of a four-concept query against three databases sends 450 requests. The budget, the cache keyed by exact string and the explicit Count button are the defence; the budget defaults are guesses until checked against each provider's published limits.
2. **Words are not databases.** The local match (seeds, comparison) uses whole words in title, abstract and keywords; databases stem, search other fields and miss abstracts. "Matched by the words" can be wrong both ways; the report always says which measure it used.
3. **Counts move.** OpenAlex and Semantic Scholar grow daily; a count from yesterday may differ by a few records. The date is always shown.
4. **Semantic Scholar's count reads a first page** of up to 1,000 ids (no page size); it is the heaviest count and the most throttled (finding 11).
5. **The amendment discards a harvest.** Recording a change after a harvest makes the harvest unusable until M3j. The confirmation says so with the run's size.
6. **Two places, one tool.** Inception (draft) and Plan (workspace) have different stores and guards; parts A and D must share the engine code and differ only in where the log lives and what a write does.
7. **Scope.** A + B + C + D is about the size of M10b. Part C must not grow into A's frame (open question 2).
8. **M3f and H-run-small-fixes are being built at the same time** and own the corpus rules, Import, Hand-off and the harvest's Crossref default; the consequences listing and the Crossref rule must be re-read against them when D and A start.

## What will not be verified without a live run

- Whether OpenAlex answers an identifier filter combined with a search in one request (DoD 11 and (d) case 2), and how many DOIs one request takes.
- The real cost of the budget defaults against the providers' quotas; how many requests a real development session sends.
- Whether the drop counts in OpenAlex and Semantic Scholar show the run's effect as Scopus did (Scopus: 130, 236 without UAV, 512 without multispectral). The app's own databases were never counted with a concept dropped.
- Whether the local word match would have flagged the run's gap from the seeds or from a wider Scopus export (the 2026-11-20 Scopus export of 130 used the same strict query, so its words match the query by construction).
- Semantic Scholar's behaviour under repeated small counts.
- DoD 25: the researcher's own development session.

## Open questions

In [`M11a-query-workbench-for-review.md`](M11a-query-workbench-for-review.md), with recommendations and costs; the entry in `docs/decisions.md` holds the same items; all ten were accepted as recommended on 2026-11-20.

The two screen drafts (written by the `ux-spec-writer` agent) carry their own screen-level questions (11 on the Inception screen, 10 on Plan): which button is brand while a version is unsaved, how a merged concept is named, which databases Count asks at Inception, whether years and languages are editable in the workbench, route names beyond `counts` and `amend`, refusal codes for a refused comparison file and a missing reason, how Plan reads the protocol's concepts and seeds, what the engine refuses when the protocol changed under the page, and whether other screens' links now point to "Change the search". They are layout and build choices under the ten questions above; they are settled when each spec is made FINAL, at the start of its part. Their state sentences beyond the row-state table above are the agent's wording and need the researcher's read.

## Build record

### Part A: counts, the request budget and the cache

Branch `dev/m11a/part-a-counts` from `origin/main` at `1f218054` · Lane **RELEASE** (as proposed; `test_gate_policy.md`: new public routes, new refusal codes, a persisted file, additive fields on a public answer) · Decisions: `docs/decisions.md` "2026-11-21 — M11a Part A" items 1 to 10 (PROPOSED).

What was built:
- `src/scholar_search/workbench.py` (pure): `parse_version` (refuses `WORKBENCH_VERSION_INVALID` cases), `compile_version` through `compile_protocol_search`, `count_variants` (full plus each concept left out), `synonym_variants`, `gain`, `doubles` (×2), `largest`, and the word match `fold_word`/`term_matches`/`concepts_found`/`lacking`/`matches` (whole words, English plurals; decision item 7).
- `src/scholar_harness/query_workbench.py`: `CountLog` (append-only `counts.jsonl`, 24-hour answers, failed rows never answer), `SharedState` (daily budget per database, UTC day; quota memory until `resets_at`), `run` (counts and "what each synonym adds"), `read_removed` ("read what this concept removes", OpenAlex, 25 records, one request), `logged_rows` (the estimate reads the log).
- `src/scholar_harness/console/api/workbench.py`: `POST /api/v1/inception/drafts/{id}/workbench/{counts,synonyms,removed}` and `POST /api/v1/discovery/workbench/{counts,synonyms,removed}`, each with `dry_run`; in `console/browser.py` `POST_PATHS` and the proxy's list; no phone route.
- `estimate.count_one` rows gain `http_status`, `quota_exhausted`, `resets_at`; its timeout is read when called. `POST /discovery/estimate` reads the workbench log (`from_count_log`).
- Refusal codes `WORKBENCH_BUDGET_SPENT` (409), `WORKBENCH_VERSION_INVALID` (422) and `WORKBENCH_STATE_UNREADABLE` (503, review round 1) in `console/refusals.py` and `screening-api-contract.md` §7.
- A row whose database answered the full query and then failed carries `stopped` (`status`, `error_code`, `http_status`, `resets_at`, `resets_in`); Part C's screen will show it beside the number.

| DoD | Test (`tests/console/test_workbench_counts_api.py` unless named) | State |
| :-- | :-- | :-- |
| 1 | `test_a_count_answers_each_database_with_its_exact_string_and_each_concept_left_out` (string equals `translate_provider`'s), `test_a_repeated_string_is_answered_from_the_log_for_24_hours` (counted_at, from_cache); the version is the body's, the draft is not saved (`test_the_log_writes_nothing_in_a_workspace_and_journals_nothing`) | done |
| 2 | same first test (drops, gain, ratio, `largest`); `test_the_note_is_on_a_concept_whose_absence_at_least_doubles_a_count`; `test_one_concept_has_no_drop_column`; `tests/kits/search/test_workbench.py` (variants, gains) | done |
| 3 | `test_what_each_synonym_adds_states_its_requests_and_answers_gains` (cost before, `adds_nothing` at gain 0) | done |
| 4 | `test_the_dry_call_states_the_cost_per_database_and_sends_nothing`; `test_a_count_that_would_pass_a_budget_is_refused_before_any_request`; `test_the_budget_is_shared_by_drafts_and_the_workspace_and_renews_each_utc_day` ("nothing on a keystroke" is the screen's, part C) | done (engine) |
| 5 | `test_a_repeated_string_is_answered_from_the_log_for_24_hours`; `test_a_merge_asks_only_the_strings_not_yet_counted`; `test_every_request_is_a_log_row_and_a_failed_one_never_answers`; `test_on_plan_the_log_is_under_audit_and_the_estimate_reuses_it` | done |
| 6 | `test_a_used_up_quota_is_remembered_across_drafts_until_it_resets`; `test_the_last_count_is_shown_beside_a_used_up_quota`; `test_throttling_refusal_unavailability_and_timeout_keep_their_codes` | done |
| 7 | `test_crossref_is_not_counted_for_two_concepts_unless_asked_and_then_only_the_full_query`; `test_crossref_counts_like_any_database_for_one_concept` (seed and comparison exclusions are part B) | done (counts) |
| 8 | `test_the_size_line_is_the_estimates_arithmetic_for_the_version` (Inception, the draft's `pool_max`); on Plan the same function with `size_limit` | done |
| 23 | every answer and log row carries `query_key: "main"` (tests above); another key is refused (`tests/kits/search/test_workbench.py`) | done for part A |
| 24 | `generate_contract_baseline.py --check` before and after (Evidence) | see Evidence |

Fails before: on the source at `1f218054` the two new test files stop at collection (`ImportError: cannot import name 'workbench'`; 2 errors), seen 2026-11-21.

Review round 1 (`milestone-reviewer`, on `4ff5d37d`): **CHANGES**, 2 P2, 4 P3, 2 P4, all taken:

| # | Finding | Repair | Test (fails before: the reviewer's probes on `4ff5d37d`) |
| :-- | :-- | :-- | :-- |
| P2-1 | A real Count answered `cost: 0, cached: true` after sending 15 requests | the cost is fixed when the Count is planned (`Row.planned`) | `test_a_real_count_states_what_it_cost_not_what_is_left_to_count` |
| P2-2 | A cached number beside a used-up quota was in the table but not in the size line | the size line reads the full query's number, not the row's status | `test_the_size_line_counts_a_cached_number_beside_a_used_up_quota` |
| P3-3 | A failure after the full query was hidden at row level | `stopped` on the row | `test_a_database_stopped_after_the_full_query_says_so_on_its_row` |
| P3-4 | An unreadable state file was read as empty and written back (pauses and spending erased) | five tries, then `WORKBENCH_STATE_UNREADABLE`, never overwritten; a unique temporary file per writer | `test_an_unreadable_state_file_is_refused_and_never_overwritten` |
| P3-5 | Two Counts at once could both pass the budget; an error after sending lost its log rows | the whole cost is reserved in one locked step and the unsent part given back; each database's sending logs in `finally` | `test_two_reservations_cannot_both_pass_the_budget`, `test_what_was_sent_is_logged_when_a_database_fails_unexpectedly` |
| P3-6 | The routes' docstring said counting after the accept records nothing; it writes the log | docstring fixed; decision item 12 | (none) |
| P4-7 | DoD 5's wording ("never kept") against (a) ("kept as a record, never answers") | DoD 5 aligned with (a) | (none) |
| P4-8 | "What each synonym adds" costs the full query too | decision item 11 | (existing synonyms test) |

Review round 2 (on `5602e3b6`): **CHANGES**, 2 P3, 3 P4 (the round-1 repairs confirmed), all taken:

| # | Finding | Repair | Test |
| :-- | :-- | :-- | :-- |
| P3-1 | `stopped` ignored drops that were never sent because the Count's 100 s ran out | any drop that neither counted nor waits to be counted is a stop | `test_a_database_stopped_by_the_counts_deadline_says_so_on_its_row` |
| P3-2 | After requests were sent, a state file failing (refund, budget line, pause) answered 503 "nothing was sent" and lost the numbers | every shared-state call after sending is best effort (`_quietly`): the answer keeps its numbers, the budget line is `null` | `test_numbers_already_counted_survive_a_state_file_that_breaks_after_sending` |
| P4-3 | A pause that failed to store lost the sent request's log row | the log row is written first, then the pause | `test_a_quota_hit_is_logged_even_when_the_pause_cannot_be_stored` |
| P4-4 | "Read what this concept removes" kept its reservation when the provider could not be built | the reservation is given back on that path | (code path; no test) |
| P4-5 | The record said the screen shows `stopped`; the screen is Part C | wording | (none) |


Not verified (needs a live run, not run): the budget defaults against the providers' published limits; how many requests a real session sends; whether OpenAlex and Semantic Scholar show the dropped-concept pattern. Prepared command (researcher's approval needed; it sends 15 count requests, 5 each to OpenAlex, Semantic Scholar and arXiv, from the console of the real review's workspace or a draft):

```
POST /api/v1/discovery/workbench/counts  {"version": <the protocol's four concepts>, "providers": ["openalex","semanticscholar","arxiv"]}
```

then the same with UAV and multispectral merged (4 requests per database, 12 in all). The dry call (`"dry_run": true`) shows the count first and sends nothing.

Evidence:

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner | `526599b4` (working tree) | `select_test_gate.py --changed origin/main --stage inner`: `pytest tests/console -m "not slow" -n auto`; `pytest tests/unit tests/test_handoff.py tests/kits/search -m "not slow" -n auto`; ruff (real-bug classes); typecheck; `vitest related route.ts` | 859 passed, 1 skipped; 1204 passed; ruff clean; tsc clean; 69 passed | 261 s; 60 s |
| contract | `4ff5d37d`, `52399d67` | `generate_contract_baseline.py --check`; `generate_protocol_schema.py --check` | current; in sync | |
| pr (round 0) | `4ff5d37d` | `pytest -n auto`; `ruff check scripts/`; vitest; build; `test:browser` | 5977 passed, 15 skipped; clean; vitest 993 passed, 2 failed (both near the 5 s limit while Playwright ran; a rerun under the same load failed 5 other tests; on `52399d67` alone: 995 passed); build ok; Playwright 622 passed | 1142 s; 177 s; 52 s; 1229 s |
| pr (final) | `52399d67` | `pytest -n auto`; `ruff check scripts/`; typecheck; vitest (alone); baseline; protocol schema | 5985 passed, 15 skipped, 1 failed: `test_approve_all.py::test_a_decision_changed_after_approval_makes_the_batch_need_a_code_again` (H-run-small-fixes Part A's area, not touched here; passes 3 of 3 alone and its file 25 of 25: a timing flake under `-n auto`); clean; clean; 995 passed; current; in sync | 1055 s; 214 s |

Build and Playwright were not repeated on `52399d67`: the repairs after `4ff5d37d` changed Python only (`git diff 4ff5d37d 52399d67 -- apps` is empty apart from six screenshots the Playwright run regenerated, which are restored to `origin/main`).

Review: round 1 CHANGES (8), round 2 CHANGES (5), round 3 **APPROVE** on `52399d67` (the reviewer's lane line in round 3 said STANDARD; the part is RELEASE as declared above). Round 3 follow-ups, not repaired: no regression test for the provider-build failure of "read what this concept removes"; after a short state-file failure a pause may not be stored, so the next Count can send once to a database whose quota is used up; a drop answered `not_countable` is reported as `stopped` although sending goes on.

**Part A: READY FOR PR** (not pushed). Branch `dev/m11a/part-a-counts`.

### Part B: seeds and comparison sets

Branch `dev/m11a/part-b-seeds-comparison`, **from Part A's branch** (`dev/m11a/part-a-counts` at `0267d071`, not merged yet: merge Part A first) · Lane **RELEASE** (as proposed: new routes and refusal codes, new genesis files in the preview answer, new check ids) · Decisions: `docs/decisions.md` "2026-11-21 — M11a Part B" items 1 to 10 (PROPOSED).

What was built:
- `scholar_search.workbench`: `seed_check` (per seed the concepts found and lacking, "not read", the warning levels `all`, `concept`, `few`), `record_text`, `readable`, `related`. `scholar_search.dedup.title_key` is public. `OpenAlexProvider.find_dois` and `works_by_doi`: one request per 50 DOIs (`DOI_FILTER_MAX`), the identifier filter with or without the planned search.
- `scholar_harness/query_workbench_sets.py`: the seed check with its sources and the opt-in lookup (`seed_texts.json`, `seed_checks.jsonl`), the OpenAlex check behind `NEXUS_WORKBENCH_OPENALEX_IDS`, comparison sets (stage, list, remove), the report (three measures, missing records 20 per page with the concepts each lacks, terms), the genesis copy and the preview's file list. Budget: reserved before sending, unsent requests given back (Part A's rule).
- Routes: `POST …/workbench/seeds`, `GET`/`POST …/workbench/comparison`, `POST …/workbench/comparison/{cmp}/remove` and `…/report`, at Inception (`/api/v1/inception/drafts/{id}/…`) and on Plan (`/api/v1/discovery/…`); every POST in both allow-lists, none a phone route.
- Genesis: the draft's `query_development/` is copied to `audit/query_development/` with a `QUERY_DEVELOPMENT_RECORDED` journal row; the preview lists the files.
- Checks `QUERY_NOT_COUNTED` (note) and `SEEDS_CANNOT_TEST` (warning, three sentences), step `criteria`, in the catalogue, `02-checks.md` and `checks-copy.ts` (en, fr, ar; 52 ids). Count log rows carry `version_key`.

| DoD | Test (`tests/console/test_workbench_seeds_comparison_api.py` unless named) | State |
| :-- | :-- | :-- |
| 9 | `test_seeds_whose_words_hold_every_concept_cannot_test_the_query`, `test_a_seed_that_lacks_a_concept_is_missed_by_the_words_with_its_own_terms_offered`, `test_the_first_searchs_pool_gives_the_words_without_a_request`; `tests/kits/search/test_workbench.py` (seed check) | done |
| 10 | `test_an_unread_seed_counts_neither_way_and_too_few_readable_seeds_say_so`, `test_no_seed_raises_no_warning`; the pure tests | done |
| 11 | `test_the_openalex_seed_check_is_off_until_switched_on`; `test_the_openalex_identifier_request_combines_the_doi_filter_with_the_search_in_one_page` | done offline; **live confirmation pending** |
| 12 | `test_an_export_is_staged_as_a_comparison_set_apart_from_the_corpus`, `test_a_set_is_removed_and_leaves_a_line_in_the_log`, `test_a_file_that_is_not_an_export_too_large_or_one_set_too_many_is_refused` | done |
| 13 | `test_the_report_by_the_words_lists_the_missing_records_and_their_shared_terms`, `test_the_report_pages_by_twenty` | done |
| 14 | `test_on_plan_the_report_compares_with_the_harvest_by_doi_or_title`, `test_the_openalex_measure_costs_two_requests_per_fifty_and_names_records_not_in_openalex`, `test_the_openalex_measure_is_off_until_switched_on`, and the words measure above | done (OpenAlex measure offline only) |
| 15 | `test_genesis_copies_the_development_and_the_preview_lists_it`, `test_a_draft_with_no_development_lists_no_such_file` | done |
| 19 | `test_query_not_counted_is_a_note_until_the_saved_version_is_counted`, `test_seeds_cannot_test_is_a_warning_with_the_panels_words_and_never_blocks`, `test_seeds_cannot_test_names_a_concept_no_seed_lacks`; `apps/research-ui/tests/checks-panel.test.tsx` (copy) | done (engine and copy; shown at the field by part C) |
| 7 (rest) | Crossref is never part of the seed or comparison checks: they ask OpenAlex only | done |
| 23 | seed checks and reports carry `query_key` | done for part B |

Fails before: on Part A's head the new API file stops at collection (`ImportError: query_workbench_sets`) and 5 of the new pure tests fail (no `seed_check`, `related`), seen 2026-11-21.

Review round 1 (`milestone-reviewer`, on `559c3063`): **CHANGES**, 1 P2, 4 P3, 2 P4, all taken:

| # | Finding | Repair | Test (fails before: the reviewer's probe `rvB/test_probe_b.py` for B1; code reading for the others) |
| :-- | :-- | :-- | :-- |
| P2-B1 | The seed check still sent the OpenAlex check after the lookup met a used-up quota | a failed lookup stops OpenAlex for the call; the check's cost is given back and its row takes the lookup's status | `test_a_lookup_that_meets_a_used_up_quota_sends_nothing_more` |
| P3-B2 | A genesis copy failing half way (a replacement) left a re-protocoled workspace with a partial development; a retry appended twice | the development is built in a folder beside it (the existing one copied first) and moved in whole | `test_a_failed_genesis_copy_leaves_the_development_as_it_was`, `test_a_replacement_appends_the_logs_and_numbers_the_sets_after_the_existing_ones` |
| P3-B3 | The seed check warned "few" when no seed could be read | no warning when none is readable ("not checked") | `test_seeds_none_of_which_can_be_read_raise_no_warning`, `tests/kits/search/test_workbench.py::test_seeds_none_of_which_can_be_read_are_not_checked` |
| P3-B4 | Two uploads at once could take the same set number | the limit check, the number and the rename are one locked step per folder | (code path) |
| P3-B5 | The fixed check read the pool minus the left-out sample; the panel read the stored pool | both read the stored pool | (code path; the checks tests above) |
| P4-B6 | `WORKBENCH_COMPARISON_MEASURE` 422 could not happen (an unknown measure is `BODY_INVALID`) | contract table and decision item 4 corrected | (none) |
| P4-B7 | A call that sends nothing (switch off) was refused for the contact email | the guards run only when a request will be sent | `test_an_openalex_call_that_would_send_nothing_is_not_refused_for_the_contact_email` |

Review round 2 (on `fc6b5832`): **CHANGES**, 1 P2, 2 P3 (B1, B3 to B7 confirmed), all about the new genesis copy:

| # | Finding | Repair | Test |
| :-- | :-- | :-- | :-- |
| P2-R1 | The copy swapped folders in two renames; a failure between them left no `audit/query_development/` and a retry deleted the earlier record | no swap: nothing already there is moved or deleted; logs get only the lines they lack (under the count log's lock), texts are rewritten through a temporary file, each set is renamed into its number in one step and skipped if the same draft's set is there | `test_a_failed_genesis_copy_moves_nothing_and_a_retry_completes_it_once`, `test_a_replacement_numbers_another_drafts_sets_after_the_existing_ones` |
| P3-R2 | Rows the Plan workbench appended during the copy were lost | follows from R1: appends in place under the same lock as `CountLog.append` | (as above) |
| P3-R3 | A failed `copytree` left a hidden temporary folder | each set's temporary folder is removed on failure | (as above) |

Also: the staging and removal rows of the count log now carry the draft or workspace (`scope`), as every other row (two drafts' identical staging lines were merged by the dedupe).

Round-1 follow-ups, not repaired: with 1 or 2 seeds `SEEDS_CANNOT_TEST` (few) and `DIRECTION_SEEDS_FEW` both fire; `SEEDS_CANNOT_TEST`'s action goes to Direction although its sentence also offers an export comparison (part C puts that link in the panel); staging or removing a set on Plan writes under `audit/` without a journal row (as decision item 12 of Part A reads "records"); a DOI holding `,` or `|` would break its batch of 50 in the OpenAlex filter; an unreadable `artifact_registry.json` turns Plan's seed and report calls into a 500.

Not verified (needs a live run, not run): whether OpenAlex answers `filter=…,doi:a|b|…` combined with `search.title_and_abstract` in one request and returns exactly the matching works (DoD 11 and the comparison's OpenAlex measure); how many DOIs one request takes in practice. Prepared check, one request, for the researcher's approval: with `NEXUS_WORKBENCH_OPENALEX_IDS=1` set for the console, on Plan of the real review, `POST /api/v1/discovery/workbench/seeds {"version": <the protocol's query>, "openalex": true}` (its dry run states "openalex: 1"); then compare its `found` with the recall check's result for the same seeds. Whether the local word match would have flagged the run's gap is also unverified (the 2026-11-20 Scopus export used the strict query).

Review round 3 (on `dde504f3`): **APPROVE**. Follow-ups, not repaired: the merge of looked-up texts at genesis is not locked against a lookup running at the same moment (a cache: the cost is one repeated lookup); a replacement can leave more than 5 comparison sets (staging is then refused until some are removed); a draft set whose `set.json` cannot be read is skipped without a note; on a retry the journal row repeats the draft's full line counts, not the lines added.

Evidence (Part B):

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner | `0f052c04` | `pytest tests/console -m "not slow" -n auto`; `pytest tests/inception tests/unit tests/test_handoff.py tests/kits/search -m "not slow" -n auto`; vitest related (route, checks copy) | 896 passed, 1 skipped; 1381 passed; 709 passed | 164 s; 57 s |
| pr (round 0) | `559c3063` | `pytest -n auto`; ruff `scripts/`; typecheck; vitest; build; `test:browser` | 6020 passed, 15 skipped; clean; clean; 995 passed; ok; Playwright 622 passed, 12 skipped | 584 s; 120 s; 34 s; 851 s |
| pr (final) | `dde504f3` | `pytest -n auto`; ruff `scripts/`; `generate_contract_baseline.py --check`; `generate_protocol_schema.py --check` | 6026 passed, 15 skipped; clean; current; in sync | 550 s |

Vitest, build and Playwright were not repeated on `dde504f3`: the commits after `559c3063` change Python and docs only (no file under `apps/`). The six screenshots the Playwright run regenerated are restored to the branch's own.

**Part B: READY FOR PR** (not pushed). Branch `dev/m11a/part-b-seeds-comparison`, to be merged after Part A.

### Part C: the workbench on Inception's step 5

Branch `dev/m11a/part-c-screen`, **from Part B's branch** (`dev/m11a/part-b-seeds-comparison` at `23c57bc1`; merge A, then B, then C) · Lane **RELEASE**, not the STANDARD proposed: the screen needed the Scopus and Web of Science strings, which the engine now builds (an additive field `external` on the counts answer, decision C item 10) · Decisions: `docs/decisions.md` "2026-11-21 — M11a Part C" items 1 to 10 (PROPOSED).

What was built:
- `apps/research-ui/components/query-workbench.tsx`: the concepts block (concept rows with wrapping term chips, OR inside and AND between in words, rename, add and remove a term, Split, Remove concept, Merge into one with the name chosen among its terms, the topic's suggested concepts, the pool's suggestions in the D5 look, the cost line, Count, Use this version, Discard edits) and the evidence column (Counts: the table with each concept left out, the largest effect in words, the note on a concept, the exact string, every row state in words, Count anyway for Crossref, the budget line, the size line with the estimate's keys, the last counted version beside this one, "What does each synonym add?", "Read what this concept removes"; Known papers; Compare with an export; the strings for Scopus and Web of Science). One card per database on narrow windows.
- `apps/research-ui/lib/workbench-api.ts` (the routes of parts A and B), `lib/workbench-copy.ts` (every sentence in en, fr and ar, 199 keys).
- `components/inception-criteria.tsx`: the concepts card is replaced by the workbench; "Use this version" saves through the normal save with `accepted_from`; the leave question ("Use it" or "Leave it") before Continue or Save with unused edits; Continue is secondary while edits are unused.
- The guidance audit (`docs/ux/shared/final/03-guidance.md`): a "Query workbench" table, rows W-B1 to W-X1 (15 STAYS, 4 HINT), counted by `guidance.audit.test.tsx`, which now reads the workbench catalog too.
- Test fakes: `tests/fixtures/workbench-engine.ts`, plugged into the inception fake.

| DoD | Test | State |
| :-- | :-- | :-- |
| 16 | `apps/research-ui/tests/inception-workbench.test.tsx` (26 cases: every row state, Crossref, largest effect and note, exact string, sizes, seeds, comparison, D5 keys, refusals, copy en/fr/ar with equal placeholders and the N9 guard); `tests-browser/workbench.spec.ts` (axe with contrast in en and ar, light and dark; no sideways scroll at 375, 1024, 1280 and 1440 px); the existing axe and overflow loops over `criteria/` | done |
| 17 | `inception-workbench.test.tsx` "concept edits …", "merges two concepts …"; `workbench.spec.ts` "develop the search …" | done |
| 18 | "Use this version sends one PUT …", "asks once before leaving …"; the row reads "for the previous version" after any edit; `inception-criteria.test.tsx` (pool term applied, saved with its source) | done |
| 19 | `inception-workbench.test.tsx` "inception.workbench checks (DoD 19)": both checks at the concepts field with their words, Continue enabled; the existing Review checks list shows every open check | done |

Screenshots looked at (`workbench.spec.ts` with `M11A_SHOTS`), the filled region (counted, sections open, a Scopus export compared): `C:\Users\mouadh\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_51fc9825-32a2-4ed5-a19b-92c9aea969a5\m11a-screenshots\workbench-en-chromium.png`, `workbench-en-chromium-dark.png`, `workbench-ar-chromium.png`, `workbench-ar-chromium-dark.png`. What the first look found and the build changed: negative numbers from the fake's default counts, a squeezed concept name field, chips made large by the split sentence (now "Split" with the full sentence as its accessible name), the Crossref sentence wrapped in one column (now spanning the row), the counts table and the comparison form wider than a phone (cards, and a shrinkable form grid).

Not verified: the wording (decision 2026-11-21 item 4: it waits for the researcher's read); a real engine behind the screen (every UI test runs against the fake; the engine side is parts A and B's tests); the screen with a real review's 24 synonyms.

Review round 1 (`milestone-reviewer`, on `7f920872`): **CHANGES**, 1 P1, 4 P2, 6 P3, all taken:

| # | Finding | Repair | Test (fails before: the reviewer's probe `rvC/wb.probe.test.ts` for C1 to C3) |
| :-- | :-- | :-- | :-- |
| P1-C1 | "Use it" in the leave question saved twice; the second save carried the earlier time and was refused (`DRAFT_CONFLICT`), and nothing moved on | the version's own save stores the page; "Use it" then goes on without a second save | `"'Use it' in the leave question saves once …"` |
| P2-C2 | Merge after removing a selected concept crashed the region | an edit that changes the number of concepts clears the selection; Merge checks its indices | `"a removal clears the merge selection …"` |
| P2-C3 | "Count anyway" on counts of a previous version replaced the whole answer with Crossref's | not offered on a previous version | `"does not offer Count anyway on counts of a previous version"` |
| P2-C4 | The lookup's request count was worked out in the browser (and could promise requests it would not send) | the panel's dry call asks the lookup and the OpenAlex check; the buttons print the engine's `cost` | the seeds tests |
| P2-C5 | The cost line could be for the engine's default databases while the page counted Explore's | the dry call also follows the databases | (code path) |
| P3-C6 | Offline disabled only Count and Use, and could not be left | every engine action disabled; the last answer "As of {time} UTC"; "Check again" | (code path) |
| P3-C7 | Three printed figures were not engine fields (45 s, "1 request", 0 in the announcement) | `timeout_seconds` on each row; the removed read's cost from its dry call; no number when no cost was read | the row-state tests |
| P3-C8 | A known paper's term was put in the first lacking concept | the researcher chooses the concept, as for comparison terms | (code path) |
| P3-C9 | Split's accessible name did not hold its visible text; the spec's focus moves were missing | name "Split", the sentence as its description; focus after Merge, Split, removing a term, Apply and Reject | `"concept edits …"` (name and description) |
| P3-C10 | "Use it" was a second brand button | secondary | `"'Use it' …"` (at most one primary) |
| P3-C11 | Row state and rejected pool terms followed the index | rows keyed by position and name; rejections by the concept's name | (code path) |

Round-1 follow-ups, not repaired: the old card's per-term DOI lists and the concept-level "in n of m" line are not in the workbench (the chips carry each term's count); the browser's `languages ?? ["en"]` default; a term made only of quotes becomes an empty phrase in the Scopus string.

Review round 2 (on `71f14450`): **CHANGES**, 1 P2, 4 P3 (C1 to C11 confirmed repaired), all taken in `3d4d0062`:

| # | Finding | Repair | Test |
| :-- | :-- | :-- | :-- |
| P2-R1 | Keying rows by position and name (the C11 repair) remounted a row on every rename: focus and a click right after it were lost | each concept holds a stable id in the tab (never sent); rows are keyed by it | `"a rename keeps the row: the same checkbox node, focus where it went"` |
| P3-R2 | "Check again" after offline re-read only the counts' cost | the seed check and the removed read's cost follow it too | (code path) |
| P3-R3 | A failed cost read left "Read what this concept removes" disabled with no reason | the refusal is shown | (code path) |
| P3-R4 | After a real seed check the lookup and OpenAlex costs disappeared, so a failed lookup could not be tried again | the costs come from a dry call read again after each real check; the real answer stays shown | (code path) |
| P3-R5 | No engine test pinned `timeout_seconds` | asserted in `tests/console/test_workbench_counts_api.py` | `test_throttling_refusal_unavailability_and_timeout_keep_their_codes` |

Round-2 follow-ups, not repaired: a `timeout` row can also mean "not started in time" (decision A item 4), which "did not answer within 45 s" does not say; with the OpenAlex key missing the removed read's button says "(0 requests)".

Review round 3 (on `2cef66f7`): **CHANGES**, 1 P2, 1 P3 (R1, R2, R5 confirmed; R3 partly), both taken:

| # | Finding | Repair | Test |
| :-- | :-- | :-- | :-- |
| P2-R6 | After one real seed check, every later dry answer was ignored, even for an edited version: the panel showed the old version's seed check | a real check's answer stays only while the seeds and version are the ones it was for | `"after a real seed check, an edit shows the seed check of the new version"` |
| P3-R7 | "Check again" on a refused cost read only cleared the message; the button stayed disabled | the cost read has its own refusal, its "Check again" reads again, and a later success clears it | `"a refused cost read says why, and Check again reads it again"` |

Review round 4 (on `f72edec8`): **APPROVE** (the reviewer's lane line says STANDARD for that UI-only commit; the part is RELEASE as declared above). Follow-up, not repaired: when the concepts drop below two, an old cost refusal can stay on screen until the next read.

Evidence (Part C):

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| pr (round 0) | `7f920872` | `pytest -n auto`; ruff; baseline; protocol schema; typecheck; vitest; build; `test:browser` | 6027 passed, 15 skipped; clean; current; in sync; clean; 1022 passed; ok; Playwright 628 passed, 4 failed (two existing inception browser tests still typed into the old concepts card; updated in round 1), 12 skipped | 559 s; 99 s; 18 s; 958 s |
| pr (round 1) | `71f14450` | the same | 6027 passed; clean; current; in sync; 1025 passed; ok; Playwright 632 passed, 12 skipped | 519 s; 109 s; 21 s; 835 s |
| pr (final, Python) | `2cef66f7` | `pytest -n auto`; ruff `scripts/` and `src/` (real-bug classes); `generate_contract_baseline.py --check`; `generate_protocol_schema.py --check` | 6027 passed, 15 skipped; clean; current; in sync | 581 s |
| pr (final, UI) | `f72edec8` | typecheck; `npm test`; build; `test:browser` | clean; 1027 passed, 1 failed (`screening-proposals.test.tsx` "shows the run as starting above an earlier run's panel", H-screening-drafts' area, not touched here; passes 18 of 18 when its file runs alone, and the whole suite then 1028 passed: a timing flake under load); ok; Playwright 632 passed, 12 skipped | 101 s; 21 s; 784 s |

Python did not change after `2cef66f7` (`git diff 2cef66f7 f72edec8` touches the workbench component, its tests and this record). The six screenshots the Playwright runs regenerate are restored after each run.

**Part C: READY FOR PR** (not pushed). Branch `dev/m11a/part-c-screen`, to be merged after Parts A and B.

### Part D: "Change the search" on Plan

Branch `dev/m11a/part-d-plan-amend`, **from Part C's branch** (`dev/m11a/part-c-screen` at `11577013`; merge A, B, C, then D) · Lane **RELEASE** (a protocol write after genesis through a new route, two refusal codes, an additive field on the plan read) · Decisions: `docs/decisions.md` "2026-11-21 — M11a Part D" items 1 to 13 (PROPOSED).

What was built:
- Engine: `workspace_proposals.search_view` and `amend_search` (the 9(a) path extended to replace the whole concept list: the same lock, compile, `outside_search` guard, backup under `audit/amended/<stamp>/`, atomic writes, `PROTOCOL_AMENDED` with `source: "researcher"`, the reason, `query_key`, both fingerprints, the changed paths, the backup and the counts before and after); `GET /discovery/plan` gains `search`; `POST /api/v1/discovery/workbench/amend` with `dry_run` (the consequences: runs still on the protocol's search, staged exports with their stated strings, recall checks of the current fingerprint, the estimate, open proposals); a running job refuses the real call; `WORKBENCH_REASON_INVALID` and `WORKBENCH_PROTOCOL_CHANGED` registered (`refusals.py`, `screening-api-contract.md` §7); the route in both allow lists, not a phone route.
- Screen: `apps/research-ui/components/plan-change-search.tsx`: "Change the search" in the executed strings' header opens a region full width above Plan's columns; "In the protocol" read only; the Part C workbench on the protocol's query (nothing counted on open); "Record this amendment" waits for a change, then the confirmation: the reason (one sentence, required), what the amendment changes in the engine's words, the counts before and after, one brand button; refusals in words; the new fingerprint shown and Plan read again after the write; after the accept the workbench counts and compares, records nothing, says why and links to a new workspace from the protocol.
- Copy: 31 `plan.search.*` keys in en, fr and ar; guidance rows D-P23 to D-P30 (7 STAYS, 1 HINT); Plan's `plan.amend.help` hint removed, so Plan stays at 7 hints.
- Found on the way and repaired (decision D items 9 and 10): Part C's dimming of a previous version's counts failed contrast in light (one line in `query-workbench.tsx`); the Plan card and the workbench were two regions named "Search"; in Arabic the staged date was laid out right to left and the counts summary used a Latin comma; the export line did not print the string the researcher stated.

| DoD | Test | State |
| :-- | :-- | :-- |
| 20 | `tests/console/test_workbench_amend_api.py` "recording replaces the concept list through the 9a path" (intent, protocol, backup of three files, the journal row's fields), "the reason is one sentence and required", "the protocol's own search is nothing to record", "a protocol changed since the page read it is refused", "a running job refuses the amendment"; `apps/research-ui/tests/discovery-plan-amend.test.tsx` "Record this amendment waits for a change …" (the body sent: concepts, reason, fingerprint, `dry_run`, `query_key`) and "refuses with the engine's words …"; `tests-browser/plan-amend.spec.ts` "change the search on Plan …" | done |
| 21 | "a dry run lists what it changes and writes nothing", "an earlier run is search-changed after the amendment and a staged export is untouched" (engine); "names each earlier run, each staged export and the recall check …", "prints the string the researcher stated for an export …" (screen, en and ar) | done |
| 22 | "after the corpus is accepted nothing is amended" (engine, `CORPUS_ALREADY_ACCEPTED`); "after the corpus is accepted: the workbench still opens and counts, Record is absent …" (screen); `plan-amend.spec.ts` "after the corpus is accepted …" | done |
| 23 | the amend answer and the journal row carry `query_key: "main"` ("a dry run …", "recording …"); the plan read's `search.query_key` ("Plan reads the protocol's concepts …") | done |

Screenshots looked at (`plan-amend.spec.ts` with `M11A_SHOTS`; the open confirmation after a count and a merge, a Scopus export staged): `C:\Users\mouadh\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_51fc9825-32a2-4ed5-a19b-92c9aea969a5\m11a-screenshots\plan-amend-en-chromium.png`, `plan-amend-en-chromium-dark.png`, `plan-amend-ar-chromium.png`, `plan-amend-ar-chromium-dark.png`. What the look found is the last bullet above.

Not verified: an amendment on a real review's protocol (every test is on a genesis made by the M10c fixtures or on the fake); the wording (decision 2026-11-21 item 4).

Follow-ups, not repaired here: "1 concepts, 4 terms" (Part C's `workbench.written` and `workbench.versions.*` have no singular form; the workbench catalog has no plural table).

Review round 1 (`milestone-reviewer`, on `0a4e3d27`): **CHANGES**, no P1, 8 P2, 7 P3, all taken (decision D items 3 to 7 and 10 to 13 rewritten or added). The engine findings' tests were seen failing on `0a4e3d27`'s engine (`workbench.py` from that commit put back for one run: 4 failed); the screen tests on `0a4e3d27`'s components (13 of 14 failed).

| # | Finding | Repair | Test |
| :-- | :-- | :-- | :-- |
| P2-1 | With no count log the journal row held `counts: {}`, not "not counted" (decision 2026-11-21 item 3) | every database a run searches is named; no log or no count of the exact string reads "not counted" | `test_with_no_count_every_database_reads_not_counted_in_the_answer_and_the_journal`; `test_a_logged_count_of_the_protocols_string_is_the_before_number` |
| P2-2 | A protocol naming an unknown or non-canonical database ("Scopus") made the dry run and Record a 500, inside the lock | the counts use `run_providers` and a failed translation reads "not counted" | `test_an_unknown_database_in_the_protocol_is_left_out_not_a_server_error` |
| P2-3 | Record could send a version no longer on screen (edits and Discard stayed possible with the confirmation open) | the confirmation is for one version: any edit or Discard closes it | `"an edit while the confirmation is open closes it …"` |
| P2-4 | Enter in the reason field submitted the form and recorded | the confirmation is not a form; Enter is held in the field; only the button records | `"Escape and Cancel … Enter in the reason never records …"`; `plan-amend.spec.ts` "keyboard: …" (a real browser) |
| P2-5 | Escape and Cancel dropped focus to the page; no focus move after Record or a refusal | focus returns to "Record this amendment"; to the h1 after a recorded amendment; to the confirmation's heading (or the refusal) after a refusal | the same tests; "Record this amendment waits …" (h1); the two refusal tests |
| P2-6 | Two brand buttons on the screen ("Continue to Recall" with Count or Record) | while the region is open "Continue to Recall" is a plain link; the region's one primary action moves Count → Record → the confirmation's button (decision D item 6) | `brand()` at screen scope in the first two tests |
| P2-7 | The browser decided when the estimate no longer applies (backwards) | `estimate` is the engine's (an estimate counted for the current protocol); the browser prints it as it comes | `test_the_estimate_line_is_the_engines_…`; `"prints the estimate line when an estimate was counted …"` |
| P2-8 | Item 7 deferred links that decision 2026-11-21 item 3 had closed | the estimate's narrow and one-database advice and `RECALL_SEED_MISSED` go to `#change-search`; Recall gains the link and `plan.search.help`; `amend.help` REMOVED. `HANDOFF_SEARCH_CHANGED` kept on Harvest, for the researcher (decision D item 7) | `test_recall_missed_and_stale` (the action); `"the anchor other screens link to opens the section"`; `guidance.screens` (Recall's hint) |
| P3-9 | The region was in the main column; the spec draws it full width above both columns, opened from the strings card's header | as the spec: Plan's page header lifted above the columns | `"is a button in the executed strings' header; opened, a region above the columns …"` |
| P3-10 | "Start a new workspace" dropped the console origin | `inceptionHref(locale, "import", "", origin)` | the accepted-state test (with `?console=`) |
| P3-11 | Plan called the researcher's own amendment a change made elsewhere | Plan takes the answer's fingerprint before reading again | "Record this amendment waits …" (`[data-plan-changed]` absent) |
| P3-12 | A reason of 4,001 characters or more was the generic body refusal | the body's bound is 100,000; over 2,000 is always `WORKBENCH_REASON_INVALID` | `test_the_reason_is_one_sentence_and_required` (5,000) |
| P3-13 | No engine test for `outside_search`, the accept refusing an earlier run, or proposals reading stale | added | `test_a_change_outside_the_search_…`; the earlier-run test calls `refuse_if_run_protocol_changed` before and after; `test_open_assistant_proposals_are_counted_and_read_stale_…` |
| P3-14 | A vitest title claimed a job refusal it did not test; no offline or `PROTOCOL_AMENDMENT_REFUSED` case | added | `"a running job refuses Record …"`, `"a console that cannot be reached …"`, `"a refused dry run shows the engine's words …"` |
| P3-15 | The job refusal had no "Follow the running job"; `WORKBENCH_PROTOCOL_CHANGED` did not read the page again; a refused dry run read "Reading…" forever | all three as the spec | the three refusal tests |

Also taken from the reviewer's follow-ups: `search_view` lost its unused argument; a concept kept under its name keeps its `boolean_operator` (`test_a_concept_kept_under_its_name_keeps_its_operator`); run ids and database names are isolated in Arabic. The workbench is no longer remounted on a new fingerprint, so edits in the tab survive a change made elsewhere (decision D item 13).

Review round 2 (on `7019848b`): **CHANGES**, no P1, 1 P2, 3 P3; 13 of the 15 round-1 findings confirmed repaired, #6 (the brand-button variant) and #8's `HANDOFF_SEARCH_CHANGED` choice judged acceptable (the latter still needs the researcher's answer to decision D item 7 before a merge), #14's phone test accepted as a follow-up. Taken:

| # | Finding | Repair | Test |
| :-- | :-- | :-- | :-- |
| P2-R1 | Plan's own estimate card still linked to inception | Plan passes `searchHref`; on Plan the link opens the section directly | `discovery-estimate.test.tsx` "advises narrowing with Change the search, which opens the section on Plan itself …" and, on Harvest, "advises narrowing with a link to Plan's Change the search" |
| P3-R2 | Once `#change-search` was in the address, a second same-page link did nothing | closing the section clears the anchor | `plan-amend.spec.ts` "the #change-search anchor opens the section; closing clears it …" |
| P3-R3 | 02-checks still sent `RECALL_SEED_MISSED` to inception | the catalogue row names step `plan`, section `change-search` | (document) |
| unverified | Whether the compiler tidies the recorded concepts, so the tab would read as changed after Record | it does (probe: `"  Weed  detection "` with three cases of one synonym is recorded as `"Weed detection"` and one synonym); after the researcher's own amendment the workbench starts again from the protocol as recorded (decision D item 13) | `"after a recorded amendment the workbench shows the protocol as the engine recorded it …"` (fails without the remount) |
| gate | The round-1 gate's vitest failed `details-rule`: the new "Details" summary had no focus ring | the shared summary classes | `details-rule.test.ts` |

Round-2 follow-ups, not repaired: a concept whose `boolean_operator` is not OR is kept as such in the protocol but shown and counted as OR in the workbench (`search_view` does not carry the operator; genesis always writes OR, so only an imported or hand-written protocol has one); the `estimate` consequence reads the console's memory, so after a console restart it is false until the estimate is counted again (as the card itself).

Round-1 follow-ups, not repaired: `amend_search` and `decide` write intent, protocol and criteria, then the journal, with no rollback (a failure part-way leaves the files ahead of the journal); the backup and write block is now in two places and could be one helper that restores from the backup. The job check runs outside the proposals lock and the corpus accept does not take that lock (both as on the `decide` path; both fail closed through the drift and snapshot gates). The discovery screens have no desktop pointer for a phone-scoped token (every discovery screen; the amend route itself is refused to a phone token by the engine, `test_the_route_is_in_both_allow_lists_and_not_a_phone_route`).

Review round 3 (on `669856e0`): **APPROVE**. Before a merge it names the researcher's answer to decision D item 7 (`HANDOFF_SEARCH_CHANGED` kept on Harvest, against the letter of decision 2026-11-21 item 3) and the gate evidence below. Its two P3 notes are follow-ups, not repaired: closing the section with the header's "Change the search" toggle (not the region's Close) leaves `#change-search` in the address, so a reload opens it again; the vitest "after a recorded amendment …" also holds in the moment before Plan's re-read lands (the final state was traced by the reviewer and the test fails without the remount). Also unverified: if Plan's re-read fails after a successful Record, the workbench shows the earlier protocol until a reload (the success line and the new fingerprint are shown).

Evidence (Part D):

| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| pr (round 0) | `0a4e3d27` | `pytest -n auto`; ruff `scripts/` and `src/` (real-bug classes); baseline; protocol schema; typecheck; vitest; build; `test:browser` | pytest passed; clean; current; in sync; clean; vitest 1033 passed, 2 failed (`discovery-proposals` and `inception-workbench`, both passing when rerun alone while the round-1 repairs were being written in the same tree: the UI stages of this run are not counted); ok; Playwright 640 passed, 12 skipped (same caveat) | 785 s; 234 s; 56 s; 993 s |
| pr (Python, final) | `7019848b` | `pytest -n auto` (counted from a JUnit file); ruff `scripts/` and `src/` (real-bug classes); `generate_contract_baseline.py --check`; `generate_protocol_schema.py --check` | 6060 tests: 0 failures, 0 errors, 15 skipped; clean; current; in sync | 595 s |
| pr (UI, round 1) | `7019848b` | typecheck; vitest; build; `test:browser` | clean; 1041 passed, 1 failed (`details-rule`: the new Details summary had no focus ring; repaired in round 2); ok; Playwright 642 passed, 12 skipped | 116 s; 20 s; 831 s |
| pr (UI, final) | `669856e0` | baseline; protocol schema; typecheck; `npm test`; build; `test:browser` | current; in sync; clean; 1044 passed (70 files); ok; Playwright 644 passed, 12 skipped | 128 s; 25 s; 850 s |

Python did not change after `7019848b` (`git diff 7019848b 669856e0 -- src tests/console` is empty). The six screenshots the Playwright runs regenerate are restored after each run.

**Part D: READY FOR PR** (not pushed). Branch `dev/m11a/part-d-plan-amend`, to be merged after Parts A, B and C. Decision D item 7 was accepted by the researcher on 2026-11-21 (`HANDOFF_SEARCH_CHANGED` keeps "Search again"); items 1 to 6 and 8 to 13 stay PROPOSED.
