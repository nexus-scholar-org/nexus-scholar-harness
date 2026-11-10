# M3h-providers Provider correctness (F11, F12, F13)
Branch: dev/m3h-providers/provider-correctness · Lane: **RELEASE** (escalated from the plan's STANDARD after the independent review: the diff changes public HTTP semantics, a new `OPENALEX_KEY_NOT_SET` refusal on `POST /discovery/runs` and new plan fields `openalex_key_set` and `s2_key_set`, and changes leg outcomes for a rejected Semantic Scholar key; `test_gate_policy.md` §lanes puts that in RELEASE, as it did for M4c. No Contract v1 schema, artifact identity or snapshot change: `generate_contract_baseline.py --check` passes at every commit) · Status: READY FOR PR · Started: 2026-11-10

Scope is the first package of the plan §6 row: F11, F12, F13 from
[`three-phase-hardening-2026-11-10.md`](../../assessment/three-phase-hardening-2026-11-10.md)
and two stale UI strings. F14 to F16 (Crossref rate limits and headers, arXiv
pacing and date filter, Semantic Scholar citation paging, the default database
set, the User-Agent version) are a later package.

Two additions from the researcher on 2026-11-10 (relayed by the planning
session): (A) reconcile Semantic Scholar with its current documentation and
stop a rejected key from silently falling back to the keyless pool; (B) a
proposal, not a build, for OpenAlex semantic search (see "Proposals").

## Definition of done
- [x] F11: PubMed sends `[tiab]` for abstract-scoped terms, never `[ab]`, and the leg says so; the executed string is pinned (`tests/kits/search/test_provider_correctness.py::test_pubmed_abstract_terms_are_sent_as_title_or_abstract`, `::test_pubmed_leg_records_the_tiab_string_it_sent`).
- [x] F11: a field tag PubMed did not apply becomes a leg note, read from the ESearch answer recorded on 2026-11-10 (`::test_a_field_tag_pubmed_did_not_apply_becomes_a_leg_note`, `::test_a_fieldsnotfound_entry_becomes_a_leg_note`, `::test_every_applied_tag_gives_no_note`; fixtures `tests/kits/search/fixtures/pubmed/`).
- [x] F12: OpenAlex is never sent `mailto` (`::test_openalex_never_sends_the_contact_email`); the key is documented as required (`config.py`, user guide §8, getting started).
- [x] F12: `GET /discovery/plan` reports `openalex_key_set`; `POST /discovery/runs` refuses `OPENALEX_KEY_NOT_SET` (409) when OpenAlex is selected without the key (`tests/console/test_discovery_api.py::test_a_run_that_selects_openalex_needs_its_key`, `::test_a_run_without_openalex_needs_no_openalex_key`, `::test_the_plan_reports_the_openalex_key`); registered in `console/refusals.py` and the screening API contract §7 (`tests/console/test_console_refusals.py`), listed in the discovery packet §4.7.
- [x] F12: an OpenAlex 401/403/409 is `PROVIDER_REFUSED` with a note naming the key (`::test_an_openalex_key_refusal_is_provider_refused_with_a_key_note`).
- [x] F12: the Plan screen prints the `SCHOLAR_OPENALEX_KEY` line as it does for the contact email; Harvest shows the refusal card (`apps/research-ui/tests/discovery-plan.test.tsx`, `discovery-harvest.test.tsx`, `discovery-copy.test.ts`; en, fr, ar).
- [x] F13: OpenAlex pages are at most 100, search and snowballing (`::test_openalex_page_size_never_exceeds_100`, `::test_openalex_snowball_pages_are_100`); boolean queries use `search.title_and_abstract` through `translate()` (`::test_openalex_boolean_query_uses_the_scoped_search_parameter`, `::test_openalex_boolean_query_with_a_comma_is_sent_unchanged`, `::test_openalex_search_sends_what_translate_says`).
- [x] UI strings: inception says Explore and Direction are not built yet; the contact email is required by Crossref and PubMed, OpenAlex needs its key (`inception-scope.test.tsx`, `discovery-copy.test.ts`).
- [x] S2 (addition A): a rejected `SCHOLAR_S2_KEY` (401/403) fails the leg with `PROVIDER_REFUSED` and a note naming the variable, with no keyless retry (`test_provider_correctness.py::test_a_rejected_s2_key_fails_the_leg_and_is_never_retried_keyless`, `::test_a_keyless_s2_refusal_says_it_was_keyless`, `::test_s2_uses_the_bulk_endpoint_and_sends_the_key_as_x_api_key`); the plan reports `s2_key_set` (`tests/console/test_discovery_api.py::test_the_plan_reports_whether_a_semantic_scholar_key_is_set`) and the Plan screen says "Set, not yet verified" (`discovery-plan.test.tsx`); findings in `docs/kits/search/PROVIDERS_2026-11.md` §3a.
- [x] OpenAlex semantic search (addition B): proposal below; nothing in the harvest changes.
- [x] Golden search cassette green with the new OpenAlex request (`tests/pipeline/test_golden_search_cassettes.py`): the OpenAlex interaction re-recorded with the researcher's OK and key (one live request, 2026-11-10); the other four databases' recordings are unchanged.
- [x] Review findings repaired (first review: CHANGES, 6 findings): PubMed tag check no longer infers an unapplied known tag from label counts (`::test_a_dropped_tiab_term_is_not_reported_as_an_unapplied_tag`, `::test_the_golden_quoted_phrase_is_reported_as_searched_word_by_word`, `::test_pubmed_stop_words_are_noted`; second review R1: a quoted phrase PubMed cannot find is reported as searched word by word, from the recorded golden answer); the OpenAlex abstract hydrator asks for 100 (`::test_the_openalex_abstract_hydrator_asks_for_at_most_100`); the recon count probe no longer sends `mailto` to OpenAlex; lane escalated to RELEASE; docs corrected.
- [x] Closure gate (`select_test_gate.py --changed main --stage closure`), contract baseline check, `milestone-reviewer` APPROVE on the repair.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| F11 | `tests/kits/search/test_provider_correctness.py` (5 PubMed tests) | yes, 5 failed at `3e353ea` | yes |
| F12 | `test_provider_correctness.py` (5 OpenAlex key tests); `tests/console/test_discovery_api.py` (2 key tests) | yes, 7 failed at `3e353ea` | yes |
| F13 | `test_provider_correctness.py` (8 page and parameter tests) | yes, 8 failed at `3e353ea` (one import error first; the test reads `MAX_PER_PAGE` through the module) | yes |
| S2 key (addition A) | `test_provider_correctness.py::test_a_rejected_s2_key_fails_the_leg_and_is_never_retried_keyless` | yes by reading: at `3e353ea` a 403 retried keyless (two calls, leg `ok`) | yes |

## Decisions
- [2026-11-10 — OpenAlex needs its API key](../../decisions.md) (proposed; the researcher confirms at the PR).
- [2026-11-10 — A rejected Semantic Scholar key fails the leg](../../decisions.md) (proposed; replaces the silent 403 downgrade of 2026-10-17).
- Golden cassette: the researcher chose on 2026-11-10 to re-record only the OpenAlex interaction with their key (in the worktree's gitignored `.env`). One live request; the key is filtered out of the cassette and asserted absent. The pinned SCI/REC digests move because OpenAlex now returns today's records for the scoped search parameter.
- A live check on 2026-11-10 (one keyless ESearch request to NCBI, no email, recorded as the fixtures) showed that the JSON answer's `errorlist.fieldsnotfound` is empty for `weed[ab]` while the XML answer says `<FieldNotFound>ab</FieldNotFound>`. The provider therefore also compares the tags it sent with the labels in `querytranslation`.
- The inception copy key `step.comingWithRecon` keeps its name (spec 02 names it for deletion when Explore ships); only its text changes.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner | working tree | `uv run pytest tests/kits/search/test_provider_correctness.py tests/kits/search/test_providers.py tests/kits/search/test_query_honesty.py tests/kits/search/test_plan_dry_run.py tests/kits/search/test_leg_error_codes.py tests/kits/search/test_search_legs.py tests/console/test_discovery_api.py tests/console/test_console_refusals.py` | 106 passed | ~40 s |
| inner | working tree | `npx vitest run` (plan, copy, inception copy, inception scope, harvest, recall) and `tsc --noEmit` | 40 passed; typecheck clean | ~20 s |
| inner | working tree | `uv run pytest tests/pipeline/test_golden_search_cassettes.py` | 3 failed: the OpenAlex request is not in the cassette (expected; re-record pending) | ~30 s |
| pr | `9cf8f50` | `uv run pytest -q -n auto`; vitest; build; Playwright | pytest: only the 3 expected golden failures; vitest 434 passed; build ok; Playwright 387 passed, 13 skipped | 616 s + 661 s |
| inner | `9840493` | `uv run pytest tests/pipeline/test_golden_search_cassettes.py tests/pipeline/test_golden_recon_cassette.py` | 9 passed (after the OpenAlex re-record) | 68 s |
| pr | `9a5ac4d8` | `uv run pytest -q -n auto`; `npm test`; `npm run typecheck` | pytest exit 0; vitest 434 passed; typecheck clean | 474 s + 71 s |
| review | `9a5ac4d8` | `milestone-reviewer` | CHANGES (6 findings, repaired in `99f071b8`) | |
| review | `99f071b8` | `milestone-reviewer` (repair delta) | CHANGES: R1 (quoted-phrase note wrong on the golden PubMed leg), R2 (two §1 rows unannotated); repaired in the next commit | |
| closure | `99f071b8` | `select_test_gate.py --changed main --stage closure`: contract baseline, schemas and two-study fixture `--check`, ruff `scripts/`, `git diff --check`, `pytest -n auto`, `uv build --wheel`, typecheck, vitest, build, Playwright | all exit 0; pytest 4743 passed, 15 skipped; vitest 434 passed; Playwright 387 passed, 13 skipped | 1135 s |
| review | `62cbab13` | `milestone-reviewer` (R1, R2 only) | **APPROVE** | |
| pr | `75ffcf95` | `pytest -n auto`, contract baseline `--check`, ruff bug classes on `src/`, `git diff --check`, no key in the branch diff | 4745 passed, 15 skipped; all clean (`64b18cc2` repaired a K0 domain-word failure in a comment; `75ffcf95` the S2 rate) | 491 s |

## Proposals

### OpenAlex semantic search (researcher's addition B; for decision, not built)

**What it is.** `search.semantic=<text>` on `/works` matches the meaning of up to 2,000 characters of text against an embedding of each work (the help page names Qwen3-Embedding-0.6B, 1,024 dimensions, page last updated 2026-11-03). It returns works like any list request, with an optional `relevance_score` (`select=id,title,relevance_score`); among close matches, cited works get "a small boost". Limits: 50 results per query, 1 request per second, one search parameter per request (`search`, `search.exact` or `search.semantic`), and 17 filters only (among them `publication_year`, `type`, `language`, `has_abstract`, `is_retracted`; any other filter answers 400). It costs what a keyword search costs ($1 per 1,000 calls; a free key gives $1 a day) and needs the key like every other OpenAlex request since 2026-02-13.

**How it differs from the harvest leg.** PRISMA-S asks for the exact search as run, so that it can be re-run. A keyword leg has that: a boolean string, a date filter and a reported total. A semantic query has no boolean string and no total in the same sense, and its ranking depends on a model and an index OpenAlex can change, so it is reproducible on the same day at best. It must never be merged silently into a keyword leg: it would be its own leg with its own report row ("OpenAlex semantic, top 50, meaning-matched, reproducible on the same day only") and its own `cap_source`.

**Where it fits.** (1) The recall check: when a golden seed is missed by every database, a semantic query built from the seed's title and abstract shows whether OpenAlex knows near neighbours the boolean query missed, which points at a missing synonym. This is diagnostic, adds no records to the corpus and needs no new report row. (2) The inception recon probe: a semantic query on the researcher's one-sentence question gives a sample of papers before any boolean string exists; recon is exploration, so same-day reproducibility is acceptable. (3) An optional extra harvest leg capped at 50: the weakest fit, since 50 records is a small and unrepeatable addition the methods paragraph would have to explain.

**What exists.** `openalex.py` already has a `semantic` path (`Query.semantic`, `per-page` capped at 50, no cursor, a `page` loop) that no harvest selects. Two of its assumptions are stale: it never sends a `filter` (the page now lists `publication_year` as supported), and it pages past 50 although the page says 50 per query.

**Offline tests that would prove it.** A recorded cassette of one semantic request (with the key filtered); a test that the semantic leg's `executed_query` is the text sent and its notes say "meaning-matched, not reproducible across days"; a test that the request carries `publication_year` and no other filter; a test that it never sends `cursor` or a second page; and, for the recall use, a test that a missed seed produces a semantic diagnostic row without adding any record to the run.

**What the 2026-10-17 harvest lessons add** ([`2026-10-17_uav_harvest_calibration_lessons.md`](../../lessons/2026-10-17_uav_harvest_calibration_lessons.md); added 2026-11-11 at the researcher's request).
- *How the query would be phrased (lessons 1 and 9).* Boolean text is never sent to a relevance endpoint (lesson 1), and `search.semantic` is one. A semantic leg would send a short natural-language statement written from the protocol's concepts (for example "unmanned aerial vehicle imagery for crop and weed mapping"), not the compiled boolean string; that sentence is its `executed_query`, and the plan shows it before any request. Relevance-ranked retrieval supports no completeness claim (lesson 9): the leg's report row would always say "top 50 by meaning, not a complete search", its `completeness` could never be `full`, and no PRISMA count or recall figure would be derived from it.
- *Where it would sit (lessons 44, 46, 49 to 51).* Provider precision differed about 70-fold in the pilot (OpenAlex 385.7 includes per 1,000 records, Crossref 5.4; lesson 44); yield is a property of the query's shape, not of the literature (lesson 46); one query produced most of the includes while nine produced none (lesson 49); and caps cut recall almost in proportion while query shape is the real lever (lesson 50). A 50-record semantic leg is therefore a precision probe, not a recall net. It belongs where a probe helps: the recall diagnostic for missed seeds and the recon probe, where its value is to show what the boolean query misses. As a harvest leg it would add a few high-precision records that the keyword legs mostly already hold. Its per-leg precision (includes per 1,000 records, once screening has run) belongs in the researcher's report beside the other legs' precision, and must never be shown to the screening agent: the agent sees no outcome statistics (lesson 54, [`agent_autonomy_ladder.md`](../../architecture/agent_autonomy_ladder.md) §4 "What the agent is never shown").
- *Keys and the auth channel (lessons 4 and 20).* Lesson 20 made keyless-first the standing discipline: a keyed run is an explicit researcher decision. OpenAlex has since made keys mandatory (2026-02-13), so for OpenAlex keyless-first is no longer possible, and this PR gates OpenAlex runs on the key instead; for Semantic Scholar the key stays optional and the Plan screen says whether one is set. Lesson 4 found that the auth state changes what a provider returns (OpenAlex keyed paged 1,000 of 1,000; keyless stopped at 200 on HTTP 401) and that the channel must be recorded per pass. `legs.json` still records no auth channel (finding F16); recording it per leg (keyless, keyed, key rejected) is a follow-up in the F14 to F16 package, not part of this PR.
- *Retries against a spent quota (lesson 18, backlog K4 and H6).* Retrying a spent per-IP quota buys no records (lesson 18: 2,659 retried, 64 recovered). The shared client still retries every 429 and 5xx up to three times with backoff (`http_client.py`, `max_retries=3`), per request, with no memory across requests. A quota-aware circuit breaker (stop a leg or the hydrator after N consecutive 429s and record the quota debt, K4) and a cheap probe before any quota-governed retry (H6) are follow-ups, not part of this PR.

**Recommendation.** Option 1, the recall check, first: it helps the researcher fix the boolean query, which is what PRISMA-S reports, and it never puts unreproducible records in the corpus. Option 2 can follow when the Explore screen is built. Option 3 is not recommended.

**Decision for the researcher.** Use OpenAlex semantic search as a recall diagnostic for missed seeds (recommended), as the recon probe in inception, as a capped extra harvest leg, or not at all; and whether its key cost (about one call per missed seed) is acceptable.

## Deferred
- F14, F15, F16 (plan §6 row, second package).
- Recall checks do not require the OpenAlex key (decision above).
- The abstract hydrator's one keyless retry after an S2 403 (same silent-fallback shape as the leg had); follow-up.
- A run whose protocol lists no database falls back to the engine default (with OpenAlex) without the key gate firing; check whether the protocol model allows an empty list (reviewer follow-up).
- A keyless `/paper/search` check (§3a "Still open"). The researcher's S2 key was checked live on 2026-11-10 with their OK: 403 `ForbiddenException` on the bulk endpoint (§3a). Their new key (2026-11-11): 429 `TooManyRequestsException`, then 200 on one retry; `rate_limit_s2` lowered to 0.9 (`::test_the_s2_rate_limit_stays_below_one_request_per_second`).
- One Semantic Scholar budget for the leg and the abstract hydrator (the key's 1 rps is cumulative across endpoints); with F14.
- Record the auth channel per leg (keyless, keyed, key rejected), lesson 4; finding F16.
- A quota-aware circuit breaker for 429s in the shared client and the hydrator, and a probe before quota-governed retries (lesson 18, backlog K4 and H6).
