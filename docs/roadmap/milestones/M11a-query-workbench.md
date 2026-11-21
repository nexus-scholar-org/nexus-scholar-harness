# M11a Query workbench

Branch: `dev/m11a/query-workbench-spec` (from `origin/main` at `2436fe66`) · Lane: to be declared per part (proposed below: A, B and D **RELEASE**, C **STANDARD**) · Status: **SPECIFICATION APPROVED 2026-11-20; the two screen specifications FINAL since 2026-11-21 (their questions closed as proposed); build not started** (the researcher accepted questions 1 to 10 as recommended, "yes to all", relayed by the main session; decision "2026-11-20 — The order of work after the acceptance run", item 5) · Third in the agreed order (plan §6, "After the acceptance run")

Short page for the researcher: [`M11a-query-workbench-for-review.md`](M11a-query-workbench-for-review.md). Screens: [`docs/ux/phase0-inception/final/10-query-workbench.md`](../../ux/phase0-inception/final/10-query-workbench.md) and [`docs/ux/phase1-discovery/final/10-plan-amend-search.md`](../../ux/phase1-discovery/final/10-plan-amend-search.md) (both `Status: DRAFT`). Decisions: `docs/decisions.md`, "2026-11-20 — M11a query workbench: the specification's choices" (accepted 2026-11-20).

Sources: `docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md` ("The search was too narrow", findings 3, 9, 18 to 21, 23, 24), `docs/roadmap/what-a-researcher-does.md` (step 2), plan §6 "After the acceptance run", `docs/decisions.md` "2026-11-20 — The order of work after the acceptance run" (those four are on PR #262, not yet on `main`), the Inception redesign proposal on the local branch `dev/ux/inception-redesign` (direction A, D1 to D15, decided 2026-11-20), and the code at `2436fe66`.

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
- [ ] DoD 1. For a version of the query (concepts, synonyms, years, languages) and a set of databases, the engine answers per database: the exact string sent (the E1 translation), the total, its status, when it was counted and whether it came from the cache. The draft's version is sent by the browser and need not be saved first.
- [ ] DoD 2. The same answer includes, for a query of two or more concepts, the count with each concept dropped, per database, and the gain against the full query.
- [ ] DoD 3. On request, for one concept and one database, the count with each synonym of that concept removed ("what each synonym adds"). The number of requests is stated before it is sent.
- [ ] DoD 4. Before any request, the answer to a dry call states how many requests a count would send per database, and refuses with `WORKBENCH_BUDGET_SPENT` when a database's daily budget would be passed. Nothing is sent on a keystroke.
- [ ] DoD 5. Counts are kept in a persisted count log keyed by database and exact string; a repeated string is answered from it for 24 hours without a request. A failed count is never kept.
- [ ] DoD 6. A database whose quota is used up (`QuotaExhaustedError`) gets the row status `quota_used_up` with `resets_at`; the engine sends nothing more to it from the workbench until that time, across drafts and workspaces. Throttling, refusal, timeout and unavailability keep their existing codes.
- [ ] DoD 7. For a query of two or more concepts Crossref is not counted by default; its row says it cannot combine concepts with AND. "Count anyway" counts it and the row is labelled "any of the words". Crossref is never part of the drop test, the seed check or the comparison.
- [ ] DoD 8. The size line of M10b Part D (records, works range, screening hours, the warning against the planned size) is computed by `estimate.summarize` for the version shown, before and after the freeze.

**Seeds and comparison sets (part B)**
- [ ] DoD 9. Seed check, without a database request: for each seed whose title and abstract are known, which concepts its words contain and which it lacks; a seed lacking a concept is "missed by the words of this query".
- [ ] DoD 10. The warning "seeds cannot test this query" when every seed that could be read uses a term of every concept, and per concept when no seed lacks it. A seed with no readable text is "not read" and does not count either way.
- [ ] DoD 11. Seed check per database where one request can answer it (OpenAlex, by an identifier filter combined with the search; to be confirmed live). Other databases say "not checked here; the recall check on Plan runs the full query".
- [ ] DoD 12. A RIS or NBIB export can be staged as a comparison set, with its database name, the string used there (optional) and the export date. It is stored apart from the corpus staging, is never accepted into a corpus, and can be removed.
- [ ] DoD 13. The comparison report: "{n} of {m} {database} records are missing from what your query finds", with the missing titles listed, for each the concepts it lacks, and the terms (1 to 3 words) found in at least two missing records and in no concept, with their record counts, offered as synonym suggestions that are never applied without a click.
- [ ] DoD 14. "What your query finds" is said in the report's own words and in this order of strength: found in the harvest (after a harvest, by DOI or normalised title, no request); found by OpenAlex (records with a DOI, one request per 50); matched by the query's words (title, abstract and keywords, no request).
- [ ] DoD 15. At genesis the draft's query development (count log rows of the versions tried, the seed checks, the comparison sets) is copied into the workspace under `audit/query_development/`, listed in the preview's `files`.

**Inception screen (part C)**
- [ ] DoD 16. The workbench is on Inception's step 5 as the concepts block and an evidence column, laid out as direction A's blocks (D10, D13); every state in the screen spec has its words in en, fr and ar; axe passes in light and dark.
- [ ] DoD 17. Concept edits in the workbench: add, rename, remove a concept; add or remove a synonym; merge two concepts into one (OR); split a term out into a new concept. Operators stay OR within a concept and AND between concepts.
- [ ] DoD 18. "Use this version" writes the draft's `concepts` through the normal save; counts shown for an earlier version say so until counted again.
- [ ] DoD 19. Two fixed checks, never blockers: `QUERY_NOT_COUNTED` (note) and `SEEDS_CANNOT_TEST` (warning), in the M10b catalogue, shown at the field and at Review.

**Amendment from Plan (part D)**
- [ ] DoD 20. On Plan, the workbench opens on the protocol's query. "Record this amendment" requires a one-sentence reason and writes through the M10c item 9(a) path (intent search fields, protocol recompiled with the genesis compiler, backup under `audit/amended/`, `PROTOCOL_AMENDED`), extended to replace the whole concept list; the journal row carries the reason, the source `researcher` and the counts before and after.
- [ ] DoD 21. Before the amendment is recorded, the screen lists what it changes: each earlier search run (it can no longer become the corpus), staged exports (left as they are, with their stated strings), recall checks and estimates (no longer apply), open workspace proposals (become stale).
- [ ] DoD 22. After a corpus is accepted the workbench still opens, counts and compares; it records nothing and says why.
- [ ] DoD 23. Every new record and answer carries `query_key` (today always `main`).

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
