# H-quota-hang A used-up provider quota during "Checks" ends the step with a message, not hours of retries
Branch: `dev/fix/quota-hang` (from `origin/main` `f05cd29a`) · Lane: **RELEASE** (see "Lane") · Status: **IN PROGRESS** · Started: 2026-11-20

The one blocker of the acceptance run of 2026-11-20 (a real scoping review through the wheel built from `f05cd29a`; record `docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md` on the local branch `dev/docs/acceptance-run-sensor-stress`, commit `ae41a35b`, not on `main`). Three findings of that run are one defect:

- **(12)** When OpenAlex's daily quota ran out during "Checks", the run neither failed nor paused with a message; the screen said "Preparing".
- **(15)** "Stop after the current step" was not read inside "Checks": `should_stop` was tested between stages only (`pipeline/coordinator.py::_prepare_corpus`).
- **(16)** `DocumentVerifier.process_batch` asks OpenAlex once per record (`hydrate_metadata`, and `verify_document`'s fallbacks), and `AcademicHttpClient.get` retried a 429 three times, sleeping `min(Retry-After, 60)` each time: with `Retry-After: 50000` that is about three minutes per record, nine hours for 166 records.

Choices: `docs/decisions.md`, entry "2026-11-20 — H-quota-hang" (items 1 to 8, all PROPOSED).

## Lane

**RELEASE.** The task was given as STANDARD "unless the test-gate policy says otherwise for the paths you touch". `docs/architecture/test_gate_policy.md` puts "public API" and "artifact persistence" changes in RELEASE, and this change adds:

- a public state value: a run's `preparation.state` can be `incomplete` (`GET /discovery/runs`, `/runs/{run}`, `/handoff`, the next-step bar, the Hand-off checks), and an additive field `preparation.checks` (`null` in every other state);
- a persisted run record: `literature/verification_checks.json`, written by every verification;
- a new marker end status `INCOMPLETE` in `search_runs/run_NNN/pipeline.json`.

**Contract v1 is not touched:** `uv run python scripts/generate_contract_baseline.py --check` answers "Contract baseline current" (see Evidence). No schema, model, identity algorithm or generated fixture changes; the corpus snapshot does not read the new file.

## Definition of done

- [x] A 429 (or 5xx) whose `Retry-After` exceeds the client's 60 s cap is not retried and raises a typed error naming the database and the reset time; short `Retry-After` values and answers without the header behave as before; both retry loops (`get`, `post`). Tests: `tests/kits/search/test_quota_hang.py` (HTTP client part).
- [x] In "Checks", once a database reports its quota used up, it is not asked again for the rest of the batch; every record is kept; the ones not checked are marked `NOT_CHECKED` (or `VERIFIED` with `not_done: ["enrichment"]`) with a reason code, never dropped and never marked verified. Tests: `test_a_used_up_quota_ends_the_checks_in_bounded_time_and_keeps_every_record`, `test_a_record_only_openalex_could_check_is_not_checked_never_unverified`.
- [x] The stop is read before each record of "Checks"; a stop ends the step within one record and keeps what was done. Tests: `test_a_stop_request_ends_the_checks_within_one_record` (kit), `test_a_stop_during_the_checks_ends_them_within_one_record` (API).
- [x] The run's state, the Harvest screen and the Hand-off screen say which database's quota is used up, when it resets, how many records were not checked, and what to do; en/fr/ar. Tests: `tests/console/test_quota_hang_api.py::test_a_used_up_quota_during_the_checks_ends_the_run_and_says_when_it_resets`; `apps/research-ui/tests/discovery-preparation.test.tsx`, describe "H-quota-hang".
- [x] "Finish preparing this corpus" after such a run checks only the records still not checked (it was cheap: the checks file names them). Test: `test_finish_preparing_after_the_reset_checks_only_the_records_not_checked`.
- [x] Reproducing tests written first and seen failing on the unfixed code (Evidence).
- [x] Contract baseline current; CI's two ruff runs clean.
- [ ] PR gate green on the final executable commit; closure gate (RELEASE).
- [ ] `milestone-reviewer` APPROVE.

## What changed

**HTTP client** (`src/scholar_search/http_client.py`, `exceptions.py`). `RETRY_AFTER_CAP = 60.0` (the wait the client already capped at). `retry_after_seconds` reads delta-seconds and HTTP dates. In `get` and `post`, a 429 or 5xx whose `Retry-After` exceeds the cap raises at once: `QuotaExhaustedError` (429; a `RateLimitExceededError`, so a search leg still records `PROVIDER_RATE_LIMITED`) or `ProviderPausedError` (5xx), with `database` (from the host: OpenAlex, Crossref, Semantic Scholar, arXiv, PubMed), `retry_after` and `resets_at` (UTC, ISO 8601). `post` used to sleep the whole `Retry-After`, uncapped.

**Verifier** (`src/scholar_search/verifier.py`). Lookups go through `_get`: a `ProviderPausedError` pauses that provider for the rest of the verifier's life (one stage run); a paused provider is not asked again. `process_batch(..., should_stop=None)` (default: the `should_stop` attribute) reads the stop before each record; after a stop the remaining records are kept as they are, `NOT_CHECKED` / `STOPPED_BY_RESEARCHER`. Each audit row gains `not_done` (`verification`, `enrichment`) and `reason`. `paused` lists the paused databases; `stopped` says whether a stop ended the batch.

**Verification stage** (`src/scholar_harness/pipeline/verification.py`). Sets the stop on the verifier (the stage doubles keep their historical `process_batch` signature); writes `literature/verification_checks.json` (`nexus.verification-checks.v1`: one row per published or refused row with its workspace id, code, `not_done`, reason; counts; paused databases; `stopped`); status `PARTIAL` when records were not checked (Compass §3: degraded work is `PARTIAL` and says why); `keep` publishes the named rows as they are and checks only the others. The audit event's description and metrics gain the unchecked counts only when there are any (the event is unchanged otherwise).

**Coordinator and marker** (`pipeline/coordinator.py`, `pipeline/harvest_marker.py`). A verification that left records unchecked ends the marker `INCOMPLETE` (with `unchecked`, `records`, `reason`, `paused` and the engine's sentence), writes one `HARVEST_PREPARATION_INCOMPLETE` journal row (`PARTIAL`), sets the run status `INCOMPLETE` (a stop: `CANCELLED`) and does not pause for the Hand-off. The run view's state is `incomplete`, an unfinished state: `can_finish`, and the accept refuses with `PREPARATION_UNFINISHED`. `finish_harvest_preparation` resumes an `INCOMPLETE` run from `verified.json` at verification, keeping the checked rows (`_partly_checked`), and falls back to the old full preparation when the checks file does not match `verified.json` or a row was quarantined. The coordinator still imports no kit module (`test_coordinator` pins it); the stop and `keep` are passed only when set, so stage doubles with the historical keywords still run.

**Console.** The next-step bar maps `incomplete` to its row 15 (`CORPUS_PENDING`): kind `failed` at "verifying" with reason `PROVIDER_QUOTA_EXHAUSTED` and the engine's sentence, or `stopped` for a stop; action "Finish preparing". The Hand-off check `HANDOFF_PREPARATION_UNFINISHED` fires for `incomplete`. The CLI `run` panel has an `INCOMPLETE` headline and prints the sentence.

**UI** (`apps/research-ui`). `PreparationState` gains `incomplete`, `Preparation.checks`; `preparationUnfinished` includes it. A shared `IncompleteChecks` component (Harvest's preparation card and the Hand-off's pending block) says the stop, each paused database with its reset time in the researcher's clock (`localStamp`), "N of M records were not checked ... none was dropped", and "After the reset, press “Finish preparing this corpus”: only those records are checked again" (or "Press ... to check them" after a stop). New copy in en/fr/ar: `harvest.title.prep.incomplete`, `harvest.prep.badge.incomplete`, `harvest.prep.incomplete.*`, `handoff.pending.incomplete`, `checks.state.incomplete`, `next.reason.PROVIDER_QUOTA_EXHAUSTED`, `next.reason.PROVIDER_UNAVAILABLE_UNTIL`. The fake engine (`tests/fixtures/discovery-engine.ts`) serves an `incomplete` preparation (quota or stop) and `checks: null` otherwise.

**Unchanged on purpose.** The abstracts stage (`AbstractHydrator`) is not changed: its OpenAlex and Semantic Scholar batch requests now fail at once on a quota answer (item 1) and it moves on, as it already did for any error, so it no longer waits either; the works it could not give an abstract are not marked (follow-up). Search legs and Explore get the same fast failure with the reset in the message; their codes do not change.

## Tests (each failed before the fix and passes after, unless noted)

- `tests/kits/search/test_quota_hang.py` (11): the 429 with `Retry-After: 50000` is sent once, never slept, and names OpenAlex and the reset; an HTTP-date `Retry-After`; a 5xx with a long wait; POST with a long wait (before: slept 50,000 s); 12 records end with OpenAlex asked once (before: 48 requests) and all records kept and marked; records only OpenAlex could check are `NOT_CHECKED`, not `UNVERIFIED`; a stop after the third record (before: `TypeError`, no stop argument); the audit rows of a full check. Characterization, passing before as well: `test_a_post_with_a_short_retry_after_is_still_retried`; `test_a_short_retry_after_is_still_waited_and_retried` and `test_a_429_without_retry_after_keeps_its_backoff_and_ends_as_a_rate_limit` failed before only on the import of the new error class.
- `tests/console/test_quota_hang_api.py` (3), the real verifier with the real Crossref and OpenAlex providers over `httpx.MockTransport`, the HTTP client's sleeps recorded: the quota run ends `INCOMPLETE` with OpenAlex asked once, all 8 works kept, the run view, the Hand-off, the accept refusal, the journal row, the next-step bar and the Hand-off check (before: OpenAlex asked 32 times, the run paused for the Hand-off as if prepared); finishing after the reset asks only the 4 records not checked (before: the run was already "prepared"); a stop at the third record checks no fourth (before: all 8 were checked).
- `apps/research-ui/tests/discovery-preparation.test.tsx`, describe "H-quota-hang" (5): the Harvest card (quota and stop) and the Hand-off in en, fr and ar (before, on the unfixed screens: 5 failed).
- `tests/unit/test_cli_pipeline_summary.py::test_incomplete_checks_name_the_quota_and_never_claim_success` (new; written with the fix).
- Changed: `tests/console/test_harvest_preparation_api.py::test_pipeline_marker_written_by_each_stage` pins the preparation view's keys; `checks` is added there (`None` for a ready run).

## Evidence
| Stage | Commit | Command | Result |
| :-- | :-- | :-- | :-- |
| kit before | `f05cd29a` + `tests/kits/search/test_quota_hang.py` | `uv run pytest tests/kits/search/test_quota_hang.py` | 10 failed, 1 passed (`48 == 1` OpenAlex requests for 12 records; `40 == 1`; `TypeError: ... unexpected keyword argument 'should_stop'`; `KeyError: 'not_done'`; missing `QuotaExhaustedError`) |
| kit after | `23564d48` | `uv run pytest tests/kits/search/test_quota_hang.py tests/kits/search/test_verifier.py` | 25 passed |
| stage tests | working tree before `32056971` | `pytest tests/unit/test_verification_stage.py tests/unit/test_verification_identity_policy.py tests/unit/test_verification_identity_characterization.py tests/unit/test_verification_bridge_conflict.py tests/unit/test_verified_provenance.py -n 4` | all passed (58) |
| harness before | `32056971` with `src/` from `origin/main` | `uv run pytest tests/console/test_quota_hang_api.py` | 3 failed (`32 == 1`; `'PENDING_CORPUS_ACCEPT' == 'INCOMPLETE'`; `8 == 3`) |
| harness after | `32056971`, then `98f74fd5` with the bar and check assertions | same | 3 passed |
| inner gate | `32056971` | `select_test_gate.py --changed origin/main --stage inner`: `git diff --check`; `pytest tests/pipeline tests/unit -m "not slow" -n auto`; `pytest tests/kits/search -m "not slow" -n auto`; the three named files | diff check exit 0; every run passed, no failure or error (the doubled `-q` hid the count lines) |
| UI before | `b44e57a5` with `discovery-harvest.tsx`, `discovery-handoff.tsx`, `discovery-api.ts` from `origin/main` | `npx vitest run tests/discovery-preparation.test.tsx -t "H-quota-hang"` | 5 failed |
| UI after | `b44e57a5` | `npx vitest run tests/discovery-preparation.test.tsx`; `npm run typecheck` | 25 passed; clean |
| contract | `e6904008` | `uv run python scripts/generate_contract_baseline.py --check` | "Contract baseline current" (run after the edits only; no contract file is in the diff) |
| lint | `a85fee82` | `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9` | both "All checks passed!" |

## Not verified

- **Nothing was run against live OpenAlex** (its quota for the researcher's key is used up today, and the task forbids live calls). The 429 answer with `Retry-After: 50000` is a test double built from the run's record; whether OpenAlex also sends `x-ratelimit-*` headers or a body the client should read was not checked.
- The researcher's real workspace (waiting on "Finish preparing this corpus") was not touched. Its run was prepared by the old code, which recorded no checks file: "Finish preparing" there runs the whole preparation again from the saved records (not the cheap re-check), and with this fix it ends quickly with a message if the quota is still used up.
- The screens were not looked at in a browser with an `incomplete` run (the fake engine and the component tests carry it); the closure gate's `test:browser` runs the existing browser tests, none of which shows this state.
- CI matrix (Linux, macOS, Python 3.11) not run.
