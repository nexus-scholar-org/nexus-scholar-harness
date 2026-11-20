# H-provenance-s2 Provider attribution after verification; Semantic Scholar "0 results" in Explore
Branch: `dev/fix/provenance-s2` (from `origin/main` `88e3d6fb`) · Lane: **RELEASE** (see "Lane") · Status: **PR opened 2026-11-20 (review APPROVE); decisions 1 to 4 accepted by the researcher 2026-11-20** · Started: 2026-11-20

Two defects from the live run of 2026-11-19 (installed wheel from `origin/main` `2c4383e9`, the researcher's keys, a scratch workspace not available to this session). The researcher asked for both fixes on 2026-11-20. Choices: `docs/decisions.md`, top entry (2026-11-20, H-provenance-s2, items 1 to 4 accepted by the researcher 2026-11-20).

## Lane

**RELEASE.** `docs/architecture/test_gate_policy.md` puts "artifact identity or persistence" and "public API" changes in RELEASE.

- Defect 1 changes what `literature/verified.json` holds for a real run: each row keeps the harvested record (its `provider`, `provider_id`, `sources`, title, authors, venue) instead of the lookup's record. The corpus snapshot's `REC-` ids hash `provider`, `provider_id`, identifiers, title and year (`scholar_search/identity.py::_record_identity`), so a snapshot built from the same harvest gets different record, study and corpus ids than before this fix. The algorithm, the schemas and the golden fixtures do not change.
- The verification stage now preserves the dedup `workspace_id` on every verified row; before, every row the real verifier confirmed lost it and was restored through the DOI bridge, and a row confirmed by a title match whose input had no DOI was quarantined (`VERIFICATION_IDENTITY_BRIDGE_MISS`). Its audit metrics move from `bridge_restored` to `preserved`.
- Defect 2 adds `shorten` to each recon leg in the probe result and the session's probe record (an additive field of the inception API).
- **Contract v1 is not touched:** `uv run python scripts/generate_contract_baseline.py --check` answered "Contract baseline current" before the first edit (`88e3d6fb`) and after both fixes (`5ec74b8a`). No schema, model, identity algorithm or generated fixture is changed. Accepted snapshots in existing workspaces are not rewritten.

## Defect 1: provider attribution after a harvest

**Observed (2026-11-19).** Harvest `run_001`, protocol query `(UAV OR drone)` over OpenAlex, Semantic Scholar, Crossref and arXiv, cap 20 per database; each leg "Done, 20 of N". After duplicates, abstracts and verification: 64 works. The Hand-off "Provider mix" said Crossref 61 (95.31 %), arXiv 2, OpenAlex 1, no Semantic Scholar; `verified.json` agreed (61 `crossref`, 2 `arxiv`, 1 `openalex`, each row with one source).

**Cause.** `DocumentVerifier.verify_document` (`src/scholar_search/verifier.py`) returned the *lookup's* record as the verified record: the Crossref DOI lookup's `CrossrefProvider._normalize_document(...)` (provider `crossref`, one `crossref` source, no `workspace_id`), likewise for the OpenAlex DOI, arXiv-id and title lookups. Deduplication was correct: `Deduplicator._merge_metadata` merges every duplicate's `sources` into the representative, so `deduped.json` held each database that found a work. The stage `pipeline/verification.py` then restored the lost `workspace_id` through the DOI bridge, which hid the replacement: the rows kept their study ids but carried Crossref's provider, source and metadata. The 2 `arxiv` rows were records no lookup confirmed (returned unchanged); the 1 `openalex` row was one Crossref could not resolve and OpenAlex did. Every pipeline and console test passed verification through a pass-through fake, so no test ran the real verifier between deduplication and `verified.json`.

**Fix.** A verified record is a copy of the input record, filled where it lacks data (`confirmed(doc, resolved)` in `verifier.py`): `provider`, `provider_id`, `sources`, `workspace_id`, title, authors, venue and every other field it has stay its own; the lookup fills a missing title (only a placeholder such as `Untitled`), identifier, abstract, venue, URL, year, TLDR, authors, citation and reference counts and open-access locations. A non-empty identifier is never replaced by a different one; a DOI the record lacks is still filled from a title match, as before. The input record is not changed. A lookup is not a database that found the work, so it is not added to `sources`; the verification audit line already names it ("Verified via Crossref DOI ...").

**Readers checked.**
- Hand-off provider mix (`console/api/discovery.py::handoff`): counts each row once per database in its `sources`, so it now gives each database the works its leg fetched after duplicates; the shares can add up to more than 100 % when databases overlap (unchanged rule). The "one database dominates" check reads the same mix.
- PRISMA-S counts, the run report and the methods text (`scholar_search/search_report.py`, the methods route) read the legs (`legs.json`), not the rows: they were not wrong and do not change.
- RIS export `DB` tag (`scholar_search/export.py`, from `sources[0]`) and the CSV `provider` column (from `provider`): now the first database that found the work instead of `crossref`. RIS still writes one `DB` line although `sources` now lists every database (follow-up).
- Corpus snapshot: see "Lane".

## Defect 2: Semantic Scholar "0 results" on an Explore keyword search

**Observed (2026-11-19).** Explore, keyword mode, query `UAV imagery weed detection cereal crops`, years 2020 to present, language en. OpenAlex "25 of at least 1637"; Semantic Scholar "0 results, 0 of 0". The same key and the harvest leg (`(UAV OR drone)`) worked in the same session.

**Cause.** Not the endpoint, not a refusal, not the year or language filter. Explore and the harvest use the same `SearchEngine` and the same bulk endpoint (`/graph/v1/paper/search/bulk`); the request carries the words as typed and `year=2020-`, and no language filter is sent. Semantic Scholar's bulk search requires every (stemmed) term in the title or abstract. Three keyless live requests on 2026-11-20 (`fields=paperId,title`, no key, no contact address) gave: the six words with `year=2020-` → **200, `total: 0`**; without `year` → `total: 0`; four of the words (`UAV weed detection cereal`, `year=2020-`) → `total: 2`. OpenAlex's `search` matched the same words much more loosely. The screen showed that honestly ("0 results" is drawn only for an `ok` leg with nothing fetched and no reported total; a refused or failed leg shows "failed"). The defect: the existing advice "Every word of the query must appear, so a long query can find nothing. Shorten the query above." was given only when *every* database found nothing (`recon/session.py::says_shorten`, on a `POOL_EMPTY` refusal), so with OpenAlex answering it never appeared.

**Fix.**
- Each recon leg carries `shorten` (`recon/session.py::leg_says_shorten`, in `_legs_summary`): true when the leg answered (`status: ok`), fetched nothing and reported no total above zero, and the query is a keyword query (not semantic, no `OR`) of three or more words, the same word rule as `says_shorten`. The engine decides; the browser does not count words.
- Explore's "Databases asked" list of the latest search shows the existing sentence on that leg (`LegsList` `shorten` prop, `data-leg-shorten`); the failed-search card, which gives the advice once, passes no prop. No new copy.
- A Semantic Scholar 200 answer with neither `total` nor `data` (a message only) now fails the leg with that message instead of reading as "0 results" (`providers/semanticscholar.py::search`). A 401/403 (refused), an exhausted 429 and 5xx were already failures.

## Repairs after the review (round 1, CHANGES; code approved, P3s)
- Finding 2: a title match that carries another DOI than the record's own keeps the record's DOI and names the other in the verification note (`_doi_kept`); the `scholar-search verify` help no longer says it resolves canonical DOIs. Test `test_a_title_match_with_another_doi_names_it_in_the_note`.
- Finding 3: the gap check's record passes the original pool's query; a follow-up leg (a term the engine chose) never says shorten. Test `test_a_gap_check_follow_up_leg_never_says_shorten`.
- Finding 4: the RIS sentence above corrected.
- Finding 5: the per-leg advice shows only when another database found papers, so an all-empty search reloaded later does not repeat it per database. Test "is not repeated on every leg when no database found anything".

## Tests (each failed before the fix and passes after)
- `tests/kits/search/test_verifier.py`: `test_a_doi_lookup_does_not_replace_the_databases_that_found_the_work`, `test_process_batch_keeps_each_records_provider_and_leaves_the_input_untouched`, `test_a_title_match_fills_a_missing_doi_but_never_overwrites_a_different_one` (the real `CrossrefProvider` normalizer, the HTTP answer faked); `test_an_untitled_probe_takes_the_resolved_title` guards the recall seed check and passed before as well.
- `tests/unit/test_verified_provenance.py`: legs from four databases → real deduplicator → `run_verification` with the real verifier → `verified.json` lists every database per work, `preserved == 3`, and the Hand-off count per database equals each leg's distinct works. On `origin/main`: `preserved=0, bridge_restored=3`, every row `crossref`.
- `tests/console/test_recon_api.py`: `test_one_database_empty_on_a_long_keyword_query_says_shorten_on_its_leg` (in the job result and in the session's probe record), `test_a_leg_that_failed_or_a_short_query_never_says_shorten` (failed leg, two words, `OR`, semantic).
- `tests/kits/search/test_search_legs.py`: `test_semanticscholar_answer_without_a_result_list_fails_the_leg` (failed before: `ok`); `test_semanticscholar_zero_for_a_long_keyword_query_is_an_answer_with_its_total` pins the request and the honest zero (passed before; it characterizes the live answer).
- `apps/research-ui/tests/inception-legs.test.tsx`: "gives the shorten advice on the leg the engine flags" (failed before), "never on a leg the engine does not flag, nor where the screen gives it once".

## Evidence
| Stage | Commit | Command | Result |
| :-- | :-- | :-- | :-- |
| contract (before) | `88e3d6fb` | `uv run python scripts/generate_contract_baseline.py --check` | "Contract baseline current" |
| defect 1 before | `88e3d6fb` + tests | `uv run pytest tests/kits/search/test_verifier.py` | 3 failed (`'crossref' == 'openalex'`, ...) |
| defect 1 stage test on the old verifier | `origin/main` `verifier.py` | `uv run pytest tests/unit/test_verified_provenance.py` | 1 failed (`preserved=0, bridge_restored=3`) |
| defect 1 after | working tree | verifier, recall and verification-stage tests (6 files) | 72 passed |
| defect 2 before | `0710c38a` + tests | `pytest tests/console/test_recon_api.py -k shorten`; `vitest run tests/inception-legs.test.tsx`; `pytest tests/kits/search/test_search_legs.py -k semanticscholar` | 2 failed (`KeyError: 'shorten'`); 1 failed; 1 failed (`'ok' == 'failed'`) |
| defect 2 after | working tree | `tests/console/test_recon_api.py tests/recon tests/console/test_recon_sample_api.py -m "not slow"`; `tests/kits/search -m "not slow"`; vitest legs + explore; `npm run typecheck` | 265 passed; 426 passed; 64 passed; clean |
| contract (after) | `5ec74b8a` | `generate_contract_baseline.py --check` | "Contract baseline current" |
| checkpoint | `5ec74b8a` | the selector's checkpoint pytest lines plus `tests/console tests/unit tests/pipeline`, `-n auto`; `git diff --check` | 2392 passed, 4 skipped, 0 failed (9 m 18 s); clean |
| review round 1 | `72fd878e` | `milestone-reviewer` | **CHANGES**: code approved as it stands; P2 = evidence rows and closure; P3s 2 to 5 (repaired in `80fea855`, see "Repairs after the review") |
| repairs | `80fea855` | targeted: verifier, recon API, recon, provenance stage, recall tests; vitest legs + explore; typecheck | 265 passed; 65 passed; clean |
| pr + closure gate | `80fea855` (final executable commit) | `select_test_gate.py --changed origin/main --stage closure` (includes the pr stage): `uv run --extra dev --extra pdf --extra rag pytest -n auto` | **5720 passed, 15 skipped, 0 failed** (10 m 46 s) |
| | `80fea855` | `generate_contract_baseline.py`, `generate_contract_schemas.py`, `generate_two_study_contract_fixture.py`, `generate_protocol_schema.py` `--check` | all exit 0 ("current", "in sync") |
| | `80fea855` | `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9`; `git diff --check origin/main...HEAD` | all clean |
| | `80fea855` | `npm --prefix apps/research-ui run typecheck`; `test`; `build`; `test:browser`; `build:export` | exit 0; 937 passed (66 files); exit 0; **600 passed, 12 skipped** (13.2 m); exit 0 |
| | `80fea855` | `uv build --wheel`, installed in a fresh Python 3.12 venv; `nexus-scholar --help`, `scholar-agent --help` | built; both exit 0 |
| review round 2 | `c1d7fe63` | `milestone-reviewer`, limited to the round-1 findings and the delta `72fd878e..c1d7fe63` | **APPROVE**: F1 to F5 resolved; reran the targeted tests and the legs vitest; follow-up: three blank lines before `_doi_kept` in `verifier.py` (E303, outside CI's ruff selection) |
| merge of `origin/main` | `b3c158c3` (merges `618c6cf8`, PR #255 key precedence; only `docs/decisions.md` overlapped, both entries kept) | `uv run --extra dev --extra pdf --extra rag pytest -n auto`; contract baseline `--check`; both ruff; `git diff --check` | **5739 passed, 15 skipped, 0 failed** (9 m 1 s); current; clean; clean. The merged commits change no UI file, so the UI rows above stand |
| note | `5ec74b8a` | `npm test` run while the checkpoint loaded the machine | 8 files failed on 5 s waits in screens this change does not touch; 7 passed when rerun alone, the 8th (`discovery-proposals`) passed twice alone; the final run above is clean |
| note | `80fea855` | `test:browser` rewrites six tracked screenshots under `apps/research-ui/screenshots/` | restored with `git checkout`, not committed |

## Not verified
- No live harvest was re-run: the Hand-off numbers after the fix are shown by the stage test with faked lookups, not observed on the researcher's scratch workspace (not available here). A re-run of the same harvest should give each database about its 20 records after duplicates.
- No recorded verification interactions exist (the golden search cassette covers the search only; its tests pass verification through), so the real Crossref/OpenAlex answers in verification are not replayed.
- The Semantic Scholar check was keyless; the 2026-11-19 search was keyed. Both reach the same index; a keyed answer of `total: 0` was not reproduced.
- Whether OpenAlex's `search` also needs every word is not checked; the shared sentence ("Every word of the query must appear") is shown on any leg the rule flags, as it already was for an all-empty search.
- The Explore screen with a flagged leg was not looked at in a browser (the leg list sits in the "Databases asked" fold, which the researcher must open).
- CI matrix (Linux, macOS, Python 3.11) not run; the closure gate ran on Windows, Python 3.12, only.
