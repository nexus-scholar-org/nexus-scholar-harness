# scholar-search-kit assessment — 2026-11-03

Status: independent assessment, read-only. Commit 5deb3a1 (vendored `tools/scholar-search-kit`). Scope: `tools/scholar-search-kit/src/scholar_search/` (29 files, 6,243 physical lines; ~5.3k non-blank), `tools/scholar-search-kit/tests/` (21 files, 4,161 lines; 185 tests); consumers `src/scholar_harness/pipeline/{discovery,deduplication}.py`, `src/scholar_harness/screening/collector.py`, `tools/scholar-agent-kit/src/scholar_agent/server.py:339-450`. Method: read every source module in full; ran the kit suite (`uv run pytest tools/scholar-search-kit/tests -q` → 185 passed); wrote four offline reproduction scripts that stub the HTTP layer (`provider.client.get` replaced, or `httpx.MockTransport`) and executed them with the repo `.venv` Python. No network calls. Scripts and output are not committed; each Reproduced finding quotes the observed output.

Defects in kit source belong in the kit's own repo, `nexus-scholar-org/scholar-search-kit`. Per the repo rule they are not fixed in `tools/`.

## 1. Verdict

The kit is a set of working API adapters with good record-normalisation work: the DOI and PMID namespace fixes, the PubMed own-DOI fix, and the preprint-to-publisher identity rule are careful and well commented. The search layer has no notion of completeness, though. Three of six providers (Crossref, arXiv, PubMed) make a single request with a 100-record default cap. No provider reports the database's own hit count. The protocol adapter sets that cap to the protocol's *target candidate pool size*. The query string actually sent to each database is never recorded, and for arXiv it is silently rewritten into a much narrower query. The verifier, sold as a hallucination detector, marks a citation "verified" when its DOI resolves to a *different* paper, then replaces the record with that other paper. The screening helpers (heuristic screener, LLM parser, multi-screener reconciliation) turn uncertainty into EXCLUDE and carry hard-coded UAV-domain vocabulary. 185 green tests cover the happy paths and miss every defect below. Use the kit as a fetch-and-normalise library behind a harness that records, paginates and probes. It is not fit to run, unattended, any step a PRISMA report will rely on.

| Lens | Rating | Reason |
|---|---|---|
| Code quality & architecture | Weak | Thin provider abstraction (no pagination/total/capability contract), asymmetric retry policy, errors swallowed at three layers, domain vocabulary in a "generic" kit, a broken `__all__`, dead config. |
| Correctness & bugs | Failing | 16 reproduced defects. Several silently corrupt records or invert query logic: wrong-DOI "verification", bioRxiv `NOT` inversion, PubMed phrase mangling, PubMed title truncation. |
| Research-method fitness | Failing | Not PRISMA-S reportable: no executed per-database strings, no database hit counts, silent caps and rewrites. Dedup is order-dependent and records no merge reasons. Screening helpers are biased toward exclusion. |

## 2. Architecture and code quality

**SRCH-01 — The provider abstraction has no completeness contract (High, Static).** `BaseAPIProvider` (`providers/base.py:30-50`) defines only `search`, `get_citations` and `get_references` as async generators. It has no `count()`, no capability flags (boolean support, field support, max page size) and no way to return the executed query or the database's reported total. Each provider improvises its pagination, and the results are inconsistent:
- OpenAlex paginates with a cursor (`openalex.py:243-246`) and S2 with a token (`semanticscholar.py:114-148`). bioRxiv walks the date range (`biorxiv.py:94-126`).
- Crossref (`crossref.py:82-112`), arXiv (`arxiv.py:196-205`) and PubMed (`pubmed.py:140-157`) each make **one** request.

Totals the APIs do return are discarded: OpenAlex `meta.count` is used only in semantic mode, and Crossref `total-results` and PubMed esearch `count` are never read. The harvest lessons (lessons 12 and 14, backlog K2) record that the researcher had to bypass the kit and call the private `_normalize_document` to do partition sweeps. That is direct evidence the abstraction is missing this capability.

**SRCH-02 — Asymmetric retry policy; GET has none (High, Reproduced).** `AcademicHttpClient.get` (`http_client.py:86-126`) raises on the first 429 or any status of 400 or higher. Only `post` (`:128-220`) has backoff and honours `Retry-After`, and nearly all search traffic is GET. `httpx.AsyncHTTPTransport(retries=4)` (`:73`) retries only connection failures. Reproduced with a MockTransport that always answers 429:
`GET attempts: 1 -> [t] Rate limit exceeded on academic API (HTTP 429)`.
The S2 unauthenticated tier (1 req/s, shared pool) and keyless OpenAlex (401) therefore drop a whole provider leg on one bad response. Lessons 3, 4 and 18 record exactly this in the field: "0/500 HTTP 429", and "keyless → 200/1000 on HTTP 401".

**SRCH-03 — Errors are swallowed at three layers (High, Reproduced).** `SearchEngine.search_all` catches every exception per provider and only logs it (`engine.py:58-61`). Documents yielded before the failure stay in the result. Reproduced: the first OpenAlex page returns 200 records, the second raises a 401 ProviderError, and the output is `engine returned 200 docs, no exception raised; universe was 1344`. `CrossrefProvider.validate_reference` uses `except Exception: pass` (`crossref.py:139-140`). `DocumentVerifier` catches every lookup error and returns "Unverified: Record not found" (`verifier.py:77-146`), so a network outage reads as "possible hallucination". The harness compensates for discovery only, with `_ObservedProvider` in `src/scholar_harness/pipeline/discovery.py:140-250` (its docstring states the kit defect). The CLI (`cli.py:228`), MCP `nexus_discover` (`server.py:353`) and `validate-query` get no such compensation.

**SRCH-04 — Domain-specific vocabulary inside a "generic" kit (Medium, Static).** `screening.py:210-260` hard-codes exclusion phrase lists for UAV and remote-sensing reviews ("satellite imagery", "landsat", "sentinel-2", "rgb-only", ...). Those lists fire for any protocol whose exclusion criteria use the generic `reason_category` names `OUT_OF_SCOPE_RESOLUTION`, `OUT_OF_SCOPE_MODALITY` or `NO_EMPIRICAL_EVALUATION`. The arXiv provider was genericised (`arxiv.py:36-53`); screening was not.

**SRCH-05 — The package root's `__all__` exports names that do not exist (Low, Reproduced).** `__init__.py:33-64` lists `AcademicHttpClient`, `Author`, `Document`, `DocumentCluster`, `ExternalIds`, `JSONImporter`, `JSONLImporter`, `Query` and `RISImporter`, none of which are imported. `from scholar_search import *` gives `AttributeError module 'scholar_search' has no attribute 'AcademicHttpClient'`. `docs/kits_surface_matrix.md:175` already warns about the root import.

**SRCH-06 — Dead or misleading configuration and code (Low, Static).**
- `Settings.cache_expire_days` (`config.py:29`) is never read, and `cache_path` (`http_client.py:71`) is computed and discarded. Caching therefore uses hishel 0.0.32's default storage and controller, not the documented `SCHOLAR_CACHE_DIR`/30-day policy (`docs/providers.md:31-32`).
- Cache hits are only debug-logged (`http_client.py:111-113`), so an output cannot tell whether records came from today's API or from a cached response.
- `Query.language` is set by the protocol adapter (`protocol_adapter.py:70-86`) and read by no provider. The protocol's language restriction is silently ignored.
- Smaller dead code:
  - `escape_special_chars` is a no-op everywhere, because `special_chars=""` for every provider.
  - The "Not retracted" completeness point is a constant +1 (`completeness.py:75-77`).
  - The default `mailto` is `student@university.edu` (`config.py:13-15`). It is sent to OpenAlex and Crossref polite pools unless overridden.

**SRCH-07 — `Deduplicator` mutates its inputs in place (Medium, Static; confirms lesson 15).** `deduplicate` writes `workspace_id` and `cluster_id` onto every input document (`dedup.py:110-137`). `_merge_metadata` overwrites the representative's abstract, authors, IDs and counts (`dedup.py:313-377`). The members list keeps the same mutated objects. The docstring says "non-destructive metadata fusion" (`dedup.py:1`), which is false for the representative, and the source of each merged field is not retained.

## 3. Correctness and bugs

| ID | Sev. | Evidence | Location |
|---|---|---|---|
| SRCH-10 | Critical | Reproduced | `verifier.py:65-76` |
| SRCH-11 | Critical | Reproduced | `crossref.py:84-112`, `arxiv.py:196-225`, `pubmed.py:140-171` |
| SRCH-12 | High | Reproduced | `arxiv.py:146-194` |
| SRCH-13 | High | Reproduced | `biorxiv.py:94-121` |
| SRCH-14 | High | Reproduced | `pubmed.py:138` |
| SRCH-15 | High | Reproduced | `pubmed.py:100-109` |
| SRCH-16 | High | Reproduced | `screening.py:550-553` |
| SRCH-17 | High | Reproduced | `screening.py:822-844` |
| SRCH-18 | Medium | Reproduced | `verifier.py:218-236`, `cli.py:516-518` |
| SRCH-19 | Medium | Reproduced | `snowball.py:191-207`, `semanticscholar.py:150-181` |
| SRCH-20 | Medium | Reproduced | `providers/pubmed.py` (no `get_references`), `base.py:47-50` |
| SRCH-21 | Medium | Reproduced | `screen_comparator.py:42-52, 91-98` |
| SRCH-22 | Low | Reproduced | `openalex.py:178-195` |
| SRCH-23 | Low | Reproduced | `arxiv.py:101-104` |
| SRCH-24 | Medium | Static | `enrichment.py:67-73` |

**SRCH-10 — The "hallucination detector" verifies wrong-DOI citations and swaps in the other paper (Critical, Reproduced).** On the DOI path, any 200 response from Crossref returns `True` together with the Crossref record. No title comparison is made (`verifier.py:65-76`; the OpenAlex fallback at `:81-90` behaves the same). Title guards exist only on the title-search paths and in `hydrate_metadata`. A real DOI attached to the wrong title is the most common shape of an LLM-fabricated reference. Reproduced input: the title "Deep learning for UAV weed detection in sugar beet" with a DOI that resolves to "Soil moisture estimation in vineyards". Output:
`'verified': True, 'status': 'Verified via Crossref DOI (...)'` / `returned title: Soil moisture estimation in vineyards | workspace_id: None | sources: [{'provider': 'crossref', ...}]`.
The record is replaced wholesale. Its `workspace_id`, original provider provenance and `query_id` are lost, while the audit row still shows the *input* title. `scholar-search import --verify` and the harness verification stage (`src/scholar_harness/pipeline/verification.py:37`) inherit this behaviour. `test_verifier.py:9-41` tests only the case where the titles match.

**SRCH-11 — Silent truncation: three providers fetch one page, capped at 100 by default (Critical, Reproduced).**
- Crossref sends `rows=min(max_results or 100, 1000)` in a single request and never pages with a `cursor`. Reproduced with a stub advertising `total-results: 13096`: `requests: 1 params: {... 'rows': 100} docs: 100`.
- arXiv sends `max_results=min(max_results or 100, 1000)` with `start=0` once. It then applies the year window *locally* to that relevance-ranked page. Reproduced: `requests: 1 max_results param: 100 docs after local year filter: 12`, so a year-restricted arXiv search returns whichever of the top-100 relevance hits happen to fall in the window.
- PubMed sends `retmax=min(max_results or 100, 1000)` and ignores esearch `count`.

No warning, flag or total is emitted. Lesson 12 is the field confirmation: Crossref reported "1000 cap-bound" for three rounds against a true universe of about 13,096. The CLI default is worse: ad hoc `scholar-search search` uses `--limit 20` per provider (`cli.py:169`).

**SRCH-12 — arXiv silently rewrites long Boolean queries (High, Reproduced).** When the translated string exceeds 300 characters and contains `" AND "`, `arxiv.py:156-194` drops every multi-word phrase and keeps at most six single tokens per clause. It logs nothing. A typical three-concept protocol string ("unmanned aerial vehicle" OR UAV OR drone ... AND "weed detection" OR ... weeds ... AND "deep learning" OR ... CNN ...) was executed as:
`(all:UAV OR all:drone) AND (all:weeds) AND (all:CNN)`.
"weed", "deep learning" and "semantic segmentation" disappear, and because Lucene does not stem (per the code's own comment), "weed" does not match "weeds". The executed query is not returned to the caller (see SRCH-30).

**SRCH-13 — bioRxiv inverts `NOT`, turns `OR` into AND, and never matches phrases (High, Reproduced).** The translator maps all operators to `""` (`biorxiv.py:24-27`). The remaining tokens, including excluded terms and the literal quote characters, are then required as AND substrings (`:79-83, 116-118`). With stub records "...with satellite data", "...with drones" and "crop mapping for weed detection", the results were:
`'weed NOT satellite' -> ['weed detection with satellite data']`, `'drones OR satellite' -> []`, `'"weed detection"' -> []`.
The provider also downloads the *entire* bioRxiv date range (from 2013 by default) to filter locally. `SearchEngine()` includes bioRxiv by default (`engine.py:30-37`), and `validate-query` uses that default with no `max_results` (`cli.py:824`, `query_validator.py:49`). That makes it an hours-long full crawl that, even so, applies inverted logic.

**SRCH-14 — The PubMed field translation breaks quoted phrases (High, Reproduced).** `re.sub(r"(\w+):([^\s]+)", r"\2[\1]", ...)` (`pubmed.py:138`) tags only the text up to the first space. `ti:"weed detection" AND drone` becomes `"weed[ti] detection" AND drone`. This is the exact syntax the kit's own docs advertise (`docs/search-and-snowballing.md:34`). The same regex rewrites any `word:` inside a phrase, for example `"COVID-19: outcomes"`.

**SRCH-15 — PubMed titles and abstracts are truncated at the first inline tag (High, Reproduced).** `findtext("ArticleTitle")` and `AbstractText.text` (`pubmed.py:100-108`) return only the text before the first child element. PubMed uses `<i>`, `<sup>` and `<sub>` routinely for taxa, genes and chemical formulas. Reproduced: `title: 'Effect of' | abstract: 'We tested'`. Truncated titles weaken title-based dedup (SRCH-31) and corrupt T/A screening input.

**SRCH-16 — LLM "MAYBE"/"UNSURE" answers are coerced to EXCLUDE (High, Reproduced).** `"INCLUDE" if raw_decision == "INCLUDE" else "EXCLUDE"` (`screening.py:550-553`). A missing `decision` key defaults to INCLUDE, so the two failure modes point in opposite directions. Reproduced: `[('SCI-000001', 'EXCLUDE', 0.9), ('SCI-000002', 'EXCLUDE', 0.75)]`. The "MAYBE" record is excluded *with 0.9 confidence*, which keeps it out of the 0.40–0.70 conflict band (`:476`), so no human sees it. At T/A screening, uncertain records should go forward.

**SRCH-17 — Multi-screener reconciliation fabricates EXCLUDE votes (High, Reproduced).** A screener with no decision on a record is counted as an EXCLUDE vote (`screening.py:822-824`). Ties fall back to EXCLUDE pending adjudication (`:843-844`). Fleiss' κ is then computed over the fabricated ratings. Reproduced with record `y`, rated INCLUDE by screener A and unrated by B and C: `'reconciled': {'x': 'INCLUDE', 'y': 'EXCLUDE'}, 'ties': [], 'fleiss_kappa': -0.3333`. `y` is excluded and never listed as a tie. `calculate_fleiss_kappa` returns 1.0 (perfect agreement) for empty or single-rater input (`:742-751`). MCP `nexus_screen_reconcile` exposes this function (`server.py:1021`).

**SRCH-18 — Unverified records are reported as "confirmed real" (Medium, Reproduced).** `process_batch` initialises `is_verified = True` (`verifier.py:218`). With `verify=False` the audit row reads `'verified': True, 'status': 'Not checked'`, and `scholar-search import` without `--verify` prints "Verified: N/N documents confirmed real." (`cli.py:516-518`).

**SRCH-19 — Snowballing loses citation edges and truncates silently (Medium, Reproduced).**
- If a discovered document was already visited, the loop `continue`s before the edge is appended (`snowball.py:191-207`). Reproduced with two seeds that both cite W9: the edges were `[('W1','W9'), ('W1','RW1'), ('W2','RW2')]`, and W2→W9 was lost. The edge manifest therefore understates co-citation, which is the signal snowballing is used for.
- The caps (`max_per_node` 200, `max_total` 500, hard ceilings 500/2000 at `:22-26`) stop traversal without setting any truncation flag in `stats`.
- `SemanticScholarProvider.get_citations` and `get_references` make one request with `limit=1000` and ignore `next`. Reproduced: `requests: 1 docs: 1000 (response advertised next=1000)`.
- `scholar-search snowball` fetches everything, then slices to `--limit 25` by default (`cli.py:321`).
- A provider exception inside `chain` is not caught, so all documents collected so far are lost.

**SRCH-20 — PubMed backward chaining silently returns nothing (Medium, Reproduced).** `PubMedProvider` implements `get_citations` but not `get_references`. The base class yields nothing (`base.py:47-50`). Chaining defaults to `backward` (`snowball.py:147-148`), and the CLI help advertises pubmed (`cli.py:341`). Result: `pubmed backward: 0 docs, no error/warning`.

**SRCH-21 — The screening comparator silently drops records whose keys differ (Medium, Reproduced).** The key is the concatenation of whichever of `workspace_id`/`doi` are present (`screen_comparator.py:91-98`), so a record that has a DOI in run A but none in run B never matches. Reproduced: run A INCLUDE versus run B EXCLUDE on SCI-1, with the DOI missing in run B, gave `compared 1 agreement 1.0 discrepancies []`. The real disagreement vanishes, and unmatched records are not counted anywhere. The CLI help calls this "inter-rater reliability" (`cli.py:751`), but only raw percent agreement is computed, with no κ.

**SRCH-22 — OpenAlex routing depends on prose "and" inside phrases (Low, Reproduced).** Lowercase `and/or/not` anywhere, including inside quotes, is uppercased (`openalex.py:178-183`). Its presence then switches the search from full-text `search=` to the title_and_abstract filter (`:184-195`). `'"search and rescue" drone'` became `filter: title_and_abstract.search:"search AND rescue" drone`: both the field scope and the phrase changed. A comma anywhere in a Boolean string breaks the comma-joined `filter` parameter (acknowledged at `:190-192`, but not guarded).

**SRCH-23 — Old-style arXiv IDs lose their archive prefix (Low, Reproduced).** `split("/")[-1].split("v")[0]` (`arxiv.py:101-104`) turns `hep-th/9901001v2` into `9901001`. Unrelated papers from different archives can then share an `arxiv_id`, which is a Tier-1 dedup key.

**SRCH-24 — Abstract hydration has no title guard and over-applies (Medium, Static; confirms lesson 6).** `AbstractHydrator` assigns the abstract by DOI to every document sharing that DOI, including ones that already had an abstract (`enrichment.py:67-73`). Unlike `DocumentVerifier.hydrate_metadata`, it does no title check. A contaminated DOI, the failure mode documented at `pubmed.py:49-54`, therefore injects another paper's abstract straight into screening input. It is used by the harness hydration stage (`pipeline/hydration.py:31`).

## 4. Research-method fitness

**SRCH-30 — Not PRISMA-S reportable (Critical, Static plus SRCH-11/12).** PRISMA-S item 8 asks for the full strategy for each database *exactly as run*, and item 13 asks for the date each database was searched. Item 16 covers how duplicates were handled. The kit never emits per-provider executed query strings. The translated strings exist only as locals (`crossref.py:84`, `arxiv.py:140-194`, `pubmed.py:130-153`, `semanticscholar.py:89-92`). It never emits the database-reported hit count (SRCH-01), the cap applied, or whether the cap was hit. The only provenance a `Document` carries is a `query_id` and a `retrieved_at` timestamp (`models.py:106-107`). `retrieved_at` cannot distinguish a live response from a cached one (SRCH-06). The harness's `DISCOVERY_SEARCH` audit event records providers, `max_results` and an aggregate `raw_hits` (`discovery.py:490-512`), and nothing per database. As shipped, an SLR methods section cannot be written from kit output. The harvest lessons (11–14) document the researcher re-implementing all of this by hand.

**SRCH-31 — The search scope is defined by the desired pool size (High, Reproduced).** `compile_protocol_search` sets per-provider `max_results = search_strategy.target_candidate_pool_size.max` (default 100, `protocol_adapter.py:73-74`). A protocol with `{"min":200,"max":300}` produced `max_results=300`. A systematic search retrieves every record matching the strategy, and screening load is managed downstream. Capping retrieval to fit a target pool reverses that and is incompatible with any completeness claim. When the protocol has no concepts, the adapter silently searches the project title as a phrase (`:61-64`; reproduced as `"My review" 100`). It also has no exclusion (`NOT`) clause support and ignores `languages` (SRCH-06).

**SRCH-32 — Translation fidelity across providers is not real (High, Reproduced, see SRCH-12/13/14).** One `BooleanQueryTranslator` joins tokens with per-provider operator strings (`query_translator.py:193-219`). It has no notion of whether the target honours Boolean logic:
- Crossref's `query=` is relevance bag-of-words. The emitted `'( uav  drone ) + weed - satellite'` (reproduced) carries no enforceable Boolean semantics.
- S2 bulk gets `weed - satellite`, with a detached `-` (reproduced). S2's syntax applies `-` as a term prefix, so whether the negation takes effect is doubtful (Static; not checked against the live API).
- OpenAlex bypasses the translator entirely (`openalex.py:171-195`).
- arXiv, bioRxiv and PubMed are broken as shown above.

The parser silently degrades: unbalanced parentheses return the raw text untranslated (`query_translator.py:195-196`), and an unknown `field:` becomes `any` with only a log warning (`:105-107`). Lesson 1 states the same conclusion: "never submit literal boolean text to relevance endpoints".

**SRCH-33 — Query "validation" is circular (High, Static).** When golden seeds are missed, `_heal_query` ORs `doi:<seed>` clauses into the query (`query_validator.py:95-107`), re-runs it, and reports `validated: True` once recall reaches 1.0. Recall measured on a query that names the seeds says nothing about the strategy's sensitivity, and the "final_query" is not a defensible search string. Separately, `doi:` is not a field the translator maps (`query_translator.py:88-99` → `any`). Most providers would therefore search the literal DOI text, so "healing" may not even work as intended.

**SRCH-34 — Dedup is conservative on identifiers but order-dependent and unauditable (Medium, Reproduced).**
- *Strength.* Tier-1 PID matching with conflict blocking (`dedup.py:57-73, 223-278`) is well designed. Distinct publisher DOIs never merge. Only an exactly-one-preprint DOI pair is tolerated, and the PMID and DOI namespaces are normalised (`models.py:16-57`). The false-merge risk from identifiers is low.
- *Order dependence and transitive chaining.* With titles A, B and C, where the A–B and B–C ratios are 0.983 and A–C is 0.966 (below the 0.97 threshold), the input order A,B,C gave `1 clusters [['A','B','C']]` and A,C,B gave `2 clusters [['A','B'], ['C']]`. Input order comes from `asyncio.gather` arrival order (`engine.py:47-63`, network-timing dependent). So both cluster composition and the `SCI-%06d` IDs (`dedup.py:110-111`) can change between identical reruns.
- *Weak non-PID tier.* The title tier waives the author and year checks whenever either side lacks them (`dedup.py:295-309`). Two "Editorial" records from different journals with no authors or years merged (`1 cluster(s)`; Low frequency, but real for Crossref front-matter). The surname check is substring containment (`li` matches `williams`), and accents are not folded. The latter causes missed duplicates rather than false merges.
- *No audit trail.* `DocumentCluster` records no merge tier, ratio or reason (`models.py:158-174`). Representative election favours the provider weight (OpenAlex 5 over Crossref 4, `completeness.py:24-33`), so the preprint can become the representative over the version of record. The harness writes only representatives to `deduped.json` (`pipeline/deduplication.py:69-80`). A reviewer cannot answer "why were these two merged?", which is what PRISMA-S item 16 asks.

**SRCH-35 — The screening helpers are not valid screeners (High, Reproduced).**
- *The heuristic screener matches on single substrings.* An inclusion criterion counts as matched when any one of its words of 4 or more characters appears as a substring of title and abstract (`screening.py:319-329`). The criterion "Studies applying UAV multispectral imagery to weed detection in row crops" therefore INCLUDEd "Intrusion detection in computer networks" at 0.80 confidence (evidence `['detection']`). That is above the conflict band, so it is not flagged.
- *The exclusion lists ignore context.* A relevant UAV study whose abstract says "Unlike a previous systematic review, we flew 30 plots…" was EXCLUDEd, because `NO_EMPIRICAL_EVALUATION` matches the phrase anywhere.
- *Exposure.* This screener is the engine behind `scholar-search screen` (`cli.py:702`) and MCP `nexus_screen` (`server.py:398-450`). `nexus_screen` writes `included.json`/`excluded.json` to `./literature` by default, the same names the agent-in-the-loop `collect` step produces.
- *Fallback is unmarked.* `LLMBatchScreener` silently mixes heuristic fallback decisions into LLM output (`screening.py:579-586, 686-692`). `ScreeningDecision` has no `method`, model or prompt-hash field (`:17-27`), so the two cannot be told apart afterwards.
- *The PRISMA diagram is fabricated.* `to_mermaid`/`to_plantuml` print "Full-text assessed n = screened − excluded" and "Studies included" from T/A data alone (`screening.py:46-48, 80-82`; reproduced as `Full-text assessed n=1`, `Studies included n=1`). No full-text stage happened.

**SRCH-36 — Consumer defaults narrow the search silently (Medium, Static).** MCP `nexus_discover` defaults to `limit=10` per provider and `start_year=2020` (`server.py:340`). An agent calling it with only a query gets a date-restricted, 10-per-database result, labelled "Search completed: N unique papers". Provider failures are swallowed (SRCH-03) and nothing in its return string says so.

## 5. Doc drift

- `docs/kits_surface_matrix.md:189`, "429→ 5 exponential retries": false. GET makes one attempt (SRCH-02), and POST has `max_retries=3` (`http_client.py:60`).
- `README.md:17` and `docs/verification-and-dedup.md:9`, "Detect LLM hallucinations ... determine whether a given citation is authentic": refuted by SRCH-10.
- `docs/search-and-snowballing.md:34`, the PubMed example `title:"machine learning" AND healthcare` emits a malformed term (SRCH-14).
- `docs/providers.md:31-32`, `SCHOLAR_CACHE_DIR`/`SCHOLAR_CACHE_EXPIRE_DAYS` control a "SQLite HTTP cache": both settings are unused (SRCH-06).
- `dedup.py:1`, "non-destructive metadata fusion": the representative is mutated (SRCH-07).
- `docs/lessons/2026-10-17_uav_harvest_calibration_lessons.md` lesson 21, "kit code carries zero domain tokens": false at HEAD, because `screening.py:210-260` carries UAV vocabulary (the same lesson also lists it as an open item). Lessons 6, 12, 15 and 18 were *confirmed* by the code.

## 6. Prioritized recommendations

All kit fixes go to `nexus-scholar-org/scholar-search-kit` via fork and PR, then a `default_rev` bump.

| ID | Severity | Effort | Action |
|---|---|---|---|
| SRCH-10 | Critical | S | On the DOI path, require `bidirectional_title_similarity` before returning verified. On mismatch, return a distinct `DOI_TITLE_MISMATCH` status. Never replace the input record: return the candidate alongside it, and keep `workspace_id`/sources. |
| SRCH-11/31 | Critical | M | Paginate Crossref (cursor), arXiv (`start`) and PubMed (`retstart`/history). Make "no cap" the protocol default and drop the use of `target_candidate_pool_size` as a retrieval cap. Emit `cap_hit: bool` per provider. |
| SRCH-30/01 | Critical | M | Add a per-provider `SearchLeg` result: executed query string, request params, database-reported total, fetched count, cap, cache-hit flag, UTC timestamp, error. Return it from `search_all`, and have the harness journal it. |
| SRCH-12 | High | S | Remove the arXiv auto-compaction, or make it opt-in and return the executed string as a warning. |
| SRCH-13 | High | S | Drop bioRxiv from the `SearchEngine()` default, or implement correct Boolean evaluation and phrase matching. Never require NOT-terms. |
| SRCH-14/15 | High | S | Translate PubMed from the parsed tokens, not by regex (`"weed detection"[ti]`). Use `"".join(elem.itertext())` for titles and abstracts. |
| SRCH-02/03 | High | S | Give GET the same retry and `Retry-After` handling as POST. Have `search_all` return a per-provider error list instead of logging, and mark partial legs. |
| SRCH-16/17/35 | High | M | Map unknown LLM decisions to UNCERTAIN, routed to human review. Never count missing ratings as votes, and send ties forward rather than to EXCLUDE. Add `method`/`model`/`prompt_sha` to `ScreeningDecision`. Move the domain phrase lists out of the kit. Stop drawing a full-text box from T/A data. |
| SRCH-33 | High | S | Report seed recall of the unmodified query only. "Healed" queries must be labelled as non-validating. |
| SRCH-34 | Medium | M | Sort input deterministically (provider, provider_id) before clustering. Record `merge_tier`/`ratio`/`matched_on` per member. Require author or year evidence for the title tier. Persist cluster membership. |
| SRCH-19/20 | Medium | S | Always record edges, paginate S2 citations, set `truncated` in `stats`, and raise on unsupported directions. |
| SRCH-18/21/24 | Medium | S | Use `verified=None` when not checked. Use a single canonical key in the comparator, report unmatched records, and compute Cohen's κ. Add a title guard to the hydrator and skip records that already have an abstract. |
| SRCH-36 | Medium | S | Remove the `start_year=2020` and `limit=10` defaults from `nexus_discover` (agent-kit repo), and surface provider failures. |
| SRCH-05/06/22/23 | Low | S | Fix `__all__`, wire or delete the cache settings, guard OpenAlex phrase and comma handling, and keep the arXiv archive prefix. |

## 7. Limits of this assessment

- No live API calls were made. Provider behaviour was reproduced against stubbed responses shaped on each API's documented format. Real APIs may differ in details: S2 bulk's handling of a detached `-` (SRCH-32), and whether hishel actually caches these APIs' responses (SRCH-06), are unverified.
- Coverage limits:
  - I did not audit `identity.py` against the Contract-v1 schemas or golden fixtures (owned by the WP gates).
  - I ran the dedup algorithm only on small synthetic inputs. No precision or recall figures exist for a real corpus.
  - Harness consumers were read only at the call sites named in scope.
- The 185-test pass was observed once, on Windows with Python from `.venv`. I did not measure coverage.
- Severity reflects impact on an SLR when the kit is used as documented. Where the harness already compensates (SRCH-03 at discovery), the kit defect remains for the CLI and MCP surfaces, and the severity is kept for those.
