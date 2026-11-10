# M3b-api Discovery API
Branch: `dev/m3b-api/discovery-api` · Lane: **STANDARD** (packet §7: no change to what the corpus snapshot is built from; `generate_contract_baseline.py --check` at every commit) · Status: IN PROGRESS · Started: 2026-11-10

Why: plan §6 M3 is split. M3a (PR #204) built the engine; the screens 01–08 need routes that read what it writes and start it from the browser. The routes, codes and tests are fixed in [`DISCOVERY_API_PACKET.md`](../../architecture/research_ui/DISCOVERY_API_PACKET.md) (§4 shapes, §4.7 codes, §5 allowlists, §6 the researcher's seven decisions of 2026-11-10, §8 test names). No UI work here.

## Definition of done
- [ ] **Layer R reads** (packet §4.1, §4.3, §4.6, §4.8): `GET /discovery/plan` (no E1: `executed_query: null`), `GET /discovery/runs`, `GET /discovery/runs/{run}`, `GET /discovery/runs/{run}/report`, `GET /discovery/report` (report-v1 without `by_tier`), `PUT /discovery/report/methods`, `GET /discovery/handoff`. Tests: `tests/console/test_discovery_api.py`.
- [ ] **Layer J jobs** (packet §4.2, §4.3): `POST /discovery/runs` in-process with `cap_override`, `providers`, `note`; `POST /discovery/recall` over a new check-only `check_seeds` (E2); `GET /discovery/recall`; `GET /discovery/jobs/{id}`, `.../events` (SSE replayed on connect), `POST .../cancel` (run archived `PARTIAL`, records kept). One discovery job per workspace; `MAILTO_NOT_SET` and `CORPUS_ALREADY_ACCEPTED` before anything starts. Tests: `tests/console/test_discovery_api.py`, `tests/kits/search/test_recall_check.py`.
- [ ] **E5 typed codes**: `leg.error_code` (`PROVIDER_RATE_LIMITED`, `PROVIDER_TIMEOUT`, `PROVIDER_UNAVAILABLE`, `PROVIDER_REFUSED`) beside `error`; `PROTOCOL_CHANGED_SINCE_SNAPSHOT` and `BATCHES_INCOMPLETE` as a typed `code` on the run's stages and on the job's `error`, with the reason strings kept. Tests: `tests/kits/search/test_leg_error_codes.py`, `tests/unit/test_run_builds_snapshot.py`.
- [ ] **Registration and transport**: every new code in `console/refusals.py` and the contract §7 table; POST `discovery/(runs|recall)`, `discovery/jobs/<id>/cancel` and PUT `discovery/report/methods` in both allowlists; `discovery/jobs/<id>/events` in the proxy's `STREAM_PATHS`; `/jobs/start` still `405`; no phone-token route. Tests: `tests/console/test_console_refusals.py`, `tests/console/test_browser_access.py`, `apps/research-ui/tests/console-proxy.test.ts`.
- [ ] **Gate**: `/gate inner` after edits, `/gate pr` once on the final executable commit, contract check, `milestone-reviewer` APPROVE.

## Tests written first
Each route's test was written from packet §8 before the route and run against `main` + the test: all 13 console tests failed (12 on 404, the two recall tests on the missing `scholar_search.recall`), the two E5 assertions in `test_run_builds_snapshot.py` failed with `KeyError: 'code'`. `tests/kits/search/test_recall_check.py` found one gap in the first `check_seeds` (an arXiv DOI seed did not match a record with only the arXiv id), fixed before commit.

| Test | Fails before | Passes after |
| :-- | :-- | :-- |
| `tests/console/test_discovery_api.py` (15 tests: packet §8 plus refusals, shutdown) | yes, 404 / missing module | yes |
| `tests/unit/test_run_builds_snapshot.py::test_resume_refuses_*` (typed `code`) | yes, `KeyError: 'code'` | yes |
| `tests/kits/search/test_leg_error_codes.py` | yes, no `provider_error_code` | yes |
| `tests/kits/search/test_recall_check.py` | yes, arXiv DOI seed `not_found` | yes |
| `tests/console/test_browser_access.py::test_discovery_reaches_the_engine_from_the_browser`, `::test_a_phone_token_reaches_no_discovery_route` | new paths 405 | yes |
| `apps/research-ui/tests/console-proxy.test.ts` (discovery POST/PUT/stream) | new paths 405 | yes |

## Decisions
Points the packet did not settle, decided in this milestone. Summary entry: [`docs/decisions.md`](../../decisions.md) "Discovery API: what the packet left open" (2026-11-10). Each point names the packet section it completes.

1. **Cancel stops the harvest, not the run after it** (§4.3). A stopped leg says `status: "stopped"` with the note `cancelled by the researcher`; the run is archived `PARTIAL` with its fetched records in `search_runs/run_NNN/raw.json` only. A stopped harvest is not published as `literature/raw_search.json`, and the pipeline stops after discovery (`status: "CANCELLED"`, `PIPELINE_RUN_ABORTED` journaled): no dedup, no snapshot. A cancel that arrives after discovery ended does not stop dedup, verification or the snapshot. The job's last SSE event is `failed` with `state: "cancelled"` (the packet names only `done` and `failed`).
2. **Closing the console is a cancel** (§6 decision 1). The console's lifespan cancels running discovery jobs on shutdown, so the run is archived `PARTIAL` as above. A killed process cannot do this; its harvest is lost (the M3a engine archives at the end of discovery).
3. **`stale`** (§4.3): a run is stale when a later run's records became the corpus (`corpus_published`, or `raw_published` for runs before M3b-api). A later failed or cancelled run does not make an earlier one stale.
4. **The methods draft is rendered on read and never stored** (§4.6). `PUT /report/methods` writes `run_NNN/methods.md` with front matter (`run`, `reviewed`, `reviewed_at`). A later run's report shows its own draft and the earlier run's reviewed text as `methods_text.earlier_reviewed`, instead of writing `methods.draft.md`: a draft that is never written cannot overwrite anything.
5. **Report dedup counts** (§4.6) come from `deduped.json` only when the report's run is the newest run published as the corpus (the file belongs to that run); otherwise they are `null`. Import rows come from the staged sources (`corpus-sources`), `limits` and `rejected` are `null` until E3.
6. **Plan provider status before E1** (§4.1): a selected database says `status: "selected"` with `executed_query: null`; `"translated"` is kept for E1.
7. **`PROVIDER_UNKNOWN` (422)** is a new code for a `providers` list naming a database the engine does not know (runs and recall); the packet had no code for it.
8. **E5 classification** (§4.3): a 429 is `PROVIDER_RATE_LIMITED`; a timeout (new `ProviderTimeoutError`, raised by the HTTP client) `PROVIDER_TIMEOUT`; a 5xx or a network error with no answer `PROVIDER_UNAVAILABLE`; another 4xx `PROVIDER_REFUSED`. An exception that is not a provider answer (a parse error, a bug) gets no code, only its text.
9. **The run job's `error.code`** (§4.7): the coordinator's typed resume refusal (`PROTOCOL_CHANGED_SINCE_SNAPSHOT`, `BATCHES_INCOMPLETE`, now also `results["code"]` and on each skipped stage), the snapshot's refusal code (`STAGED_IMPORT_PENDING`, …), `PROVIDERS_FAILED` for a harvest where every database failed, else `DISCOVERY_FAILED`. All are registered in `console/refusals.py` and the contract §7 table, with the four leg codes.
10. **Recall details** (§4.2): `n/a` is a journal DOI on arXiv (an arXiv DOI `10.48550/arXiv.*` is not n/a) and an arXiv id on PubMed; an arXiv DOI seed matches a record carrying only the arXiv id. `title_check` compares the returned record (else the bare identifier) through `DocumentVerifier`; on a mismatch the returned record's title is kept. The check uses the protocol cap, else the engine ceiling. A cancelled check stores nothing.
11. **Leg events are thinned** (§4.3): one at the first record, every 25 records and at each leg's end, so a 10,000-record leg does not put 10,000 events in the replayed stream.
12. **`run_pipeline` gains optional keyword hooks** (`providers`, `progress_callback`, `leg_callback`, `stage_callback`, `should_stop`, `notes`, all `None` by default). The characterization test `tests/unit/test_coordinator.py::test_signatures_identical_and_mock_mode_unused` pins the extended list. `legs.json` gains `corpus_published`, `cap_override` and `notes`; a leg gains `error_code`. `search_report.md` prints the run override and the notes. The contract baseline check is unchanged.

13. **Staged exports refuse a run before it starts** (review finding 3, optional fix taken): `POST /runs` answers `409 STAGED_IMPORT_PENDING` when database exports are staged, instead of harvesting and failing at the snapshot.

### Open question for the researcher (review finding 3; before M3c specs)
A browser run is `run_pipeline`, which since M3a builds **and accepts** the corpus snapshot at the end of a successful run. So after one good run: every later browser run answers `CORPUS_ALREADY_ACCEPTED`; "re-run with a higher cap" after a lower-bound leg is not possible from the browser; and the hand-off screen (packet §4.8, which assumes acceptance happens there through `POST /screening/corpus/accept`) opens on a corpus that is already accepted. This milestone keeps M3a's behaviour (STANDARD lane: what the snapshot is built from, and when, is unchanged). The choice for M3c: (a) a browser run stops before the snapshot (`NOT_BUILT`) and the hand-off accepts it, which changes the run's stages; or (b) the hand-off shows "already accepted" and a higher-cap re-run goes through inception's replace path.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |

## Deferred
- E1 dry run (`providers[].executed_query`), E3 import rejections and `limits`, E4a dedup tiers (`by_tier`): M3d-engine (packet §7).
- E4b near-twin pairs and decisions: M3e-neartwins (packet §4.5 Stage 2, §6 decision 2).
- The §8 golden-cassette test "the dry run's executed strings equal the replayed legs'" belongs to E1 and moves with it to M3d-engine.
- Per-leg stop ("Stop arXiv") and slice yield: not offered, the engine has no leg cancel (packet §4.3); cancel stops the whole harvest.
- A harvest lost to a killed console process (not a clean shutdown): the engine archives at the end of discovery; incremental archiving would be an engine item (packet §6 decision 1 assumes a clean close).
- Report `identification[].cache` is always `null` (no cache flag on a leg yet); plan status `no_connection` is never produced (no offline probe); hand-off `dedup_decided_at` is left out (E4b).
- A cancel does not interrupt a page request in flight or a retry back-off (up to 60 s in `http_client.py`); cancel waits 30 s and may answer `state: "running"`, the job then ends `cancelled`.
- Reviewer follow-ups (P3): a draft save (`reviewed: false`) is journaled under `METHODS_TEXT_REVIEWED` with `reviewed: false` in its parameters; a malformed artifact registry gives 500 on `POST /runs`; dedup and prepare run synchronously in the console's event loop (decision 1's accepted cost); `JobRunner` jobs are not counted as discovery jobs (not browser-reachable).
