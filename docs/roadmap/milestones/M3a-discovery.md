# M3a-discovery: the discovery engine (Python only)
Branch: `dev/m3a/discovery` · Lane: **RELEASE** (WP-01 Packet B runtime adoption, CORE-07; `test_gate_policy.md` §lanes) · Status: MERGED (PR #204, e1039b1) · Started: 2026-11-08

Why: plan §6 M3 Discovery, split in two. M3a is the engine half: search legs, pagination, query honesty, stable ids, Packet B adoption and the golden cassettes. M3b (discovery specs 01–08 and screens) waits for the `apps/research-ui` redesign to merge. M3a touches no file under `apps/research-ui`. The researcher has no Scopus or Web of Science access, so the free providers (OpenAlex, Crossref, PubMed, Semantic Scholar, arXiv) are how a corpus is built.

Every finding below was re-verified at `3b474cb` by the `phase-auditor` agent before its fix (all present; CORE-07 narrower than recorded: `accept_corpus` already called the builder since M0, but `run` never reached it).

## Definition of done
- [x] **D1. Search legs (SRCH-30, CORE-21).** `SearchEngine.run` returns one `SearchLeg` per provider: executed query, request (no contact address or keys), reported total, fetched, pages, cap, cap source, `cap_hit`, status, error, notes, dates. A failing provider is a `failed` leg, never silent. `DISCOVERY_SEARCH` carries `parameters.legs` and `parameters.search_run`; each run writes `literature/search_runs/run_NNN/` (`legs.json`, `raw.json` when published), and a folder is never reused. Tests: `tests/kits/search/test_search_legs.py`, `tests/unit/test_discovery_legs.py`.
- [x] **D2. Pagination and caps (SRCH-11, SRCH-31).** Crossref (cursor), PubMed (`retstart`), arXiv (`start`) page to the reported total; OpenAlex and Semantic Scholar report theirs. `target_candidate_pool_size` no longer caps; `method.retrieval_cap` does ([decision](../../decisions.md)); with no cap the engine ceiling (10,000) applies and is reported. GET retries 429/5xx with backoff. Tests: `test_search_legs.py`, `tests/kits/search/test_protocol_adapter.py`, `tests/kits/protocol/test_method_block.py`.
- [x] **D3. Query honesty (SRCH-12/13/14).** Executed string on every leg; arXiv compaction is noted with the dropped phrases and is skipped for NOT queries (it would make a NOT term required); `AND ANDNOT` is collapsed; bioRxiv is out of the engine default; PubMed terms are built from parsed tokens. Tests: `tests/kits/search/test_query_honesty.py`, `test_search_legs.py::test_default_engine_excludes_biorxiv`.
- [x] **D4. DOI title check (SRCH-10).** An identifier resolving to another title gives `DOI_TITLE_MISMATCH`: not verified, input record unchanged; audit rows carry a `code`. Tests: `tests/kits/search/test_verifier.py` (3 new).
- [x] **D5. Stable ids (CORE-06, CORE-10).** `stable_order()` sorts by content before dedup (harness stage and engine). The DOI bridge refuses an id already held in the batch, or different from the row's input id (`VERIFICATION_IDENTITY_BRIDGE_CONFLICT`). A re-run gives identical SCI and REC→STU ids (golden cassette test). Tests: `tests/kits/search/test_dedup.py::test_sci_ids_do_not_depend_on_input_order`, `tests/unit/test_discovery_legs.py::test_dedup_stage_ids_are_input_order_invariant`, `tests/unit/test_verification_bridge_conflict.py`.
- [x] **D6. Packet B adoption (CORE-07).** After verification `run` accepts the snapshot through `accept_corpus` → `build_corpus_snapshot_artifact` + the acceptance gate (provider failures as snapshot warnings), so screening batches are prepared in the same run. The producer outcome (SUCCESS, or PARTIAL with the provider warnings) is journalled as `CORPUS_SNAPSHOT_ACCEPTED`. A refused snapshot or a prepare exit is journalled `PIPELINE_RUN_ABORTED`. Staged database exports refuse the run's snapshot (`STAGED_IMPORT_PENDING`) instead of replacing its records. With an accepted snapshot a re-run skips discovery, dedup and verification (`CORPUS_ALREADY_ACCEPTED`) and keeps the batches, after checking the protocol still matches (`PROTOCOL_CHANGED_SINCE_SNAPSHOT`) and the batches cover every study (`BATCHES_INCOMPLETE`). Unregistered or empty workspaces report `NOT_BUILT`. Tests: `tests/unit/test_run_builds_snapshot.py` (10).
- [x] **D7. Contact email.** No placeholder default; a live search refuses `MAILTO_NOT_SET` before any request, including on the real `run` path where providers are wrapped (review finding 1), and `run` prints it without a traceback. Test for the wrapped path: `tests/unit/test_discovery_legs.py::test_run_discovery_refuses_without_mailto_before_any_request`. Tests: `test_search_legs.py::test_live_search_refuses_without_mailto`, `::test_settings_have_no_placeholder_mailto`, `tests/cli/test_harness_cli.py::test_run_without_a_contact_email_refuses_with_mailto_not_set`.
- [x] **D8. Golden cassettes.** One live run on 2026-11-08 (golden-uav-30 protocol, run override 100 per database) recorded `tests/fixtures/cassettes/golden_uav_search.yaml` (8.0 MB). Requests carry no contact address, key or User-Agent. Replay is offline (`record_mode="none"`). Test: `tests/pipeline/test_golden_search_cassettes.py`.
- [x] **D9. PRISMA-S report.** `search_runs/run_NNN/search_report.md` lists per database the executed string, reported total, fetched, cap and source, cap reached, status, date, notes and request parameters. Tests: `test_discovery_legs.py` (2), golden cassette test.
- [x] **D10. Contract check passes** at every commit (`Contract baseline current`).

Golden search as recorded (from the replayed report):

| Database | Reported total | Fetched | Cap |
| :-- | --: | --: | :-- |
| OpenAlex | 1,386 | 100 | 100 (run override), cap reached |
| Semantic Scholar | 836 | 100 | 100 (run override), cap reached |
| Crossref | 13,214 | 100 | 100 (run override), cap reached |
| arXiv | 44 | 36 | 100; years filtered after retrieval; query compacted (11 phrases dropped, listed) |
| PubMed | 83 | 83 | 100 |

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| SRCH-30, CORE-21 | `tests/kits/search/test_search_legs.py`; `tests/unit/test_discovery_legs.py::test_the_journal_records_one_leg_per_database`, `::test_each_run_keeps_its_own_raw_files`, `::test_a_failed_leg_is_journalled_with_its_error` | ImportError (no `ENGINE_CEILING`/`SearchLeg`); KeyError `legs`; FileNotFound `run_001/raw.json` | yes |
| SRCH-11 | `test_search_legs.py::test_crossref_pages_with_cursor_to_reported_total`, `::test_pubmed_pages_esearch_with_retstart`, `::test_arxiv_pages_with_start_and_reads_total` | ImportError (module) | yes |
| SRCH-31 | `tests/kits/search/test_protocol_adapter.py::test_target_pool_max_is_not_the_retrieval_cap`, `::test_no_hidden_default_cap_of_100`, `::test_method_retrieval_cap_is_the_cap_and_names_the_protocol`; `tests/kits/protocol/test_method_block.py` (2 retrieval_cap tests) | 300 / 100 returned; AttributeError `retrieval_cap` | yes |
| SRCH-12 | `tests/kits/search/test_query_honesty.py::test_arxiv_compaction_is_reported_on_the_leg`, `::test_arxiv_compaction_never_makes_a_not_term_required` | ImportError (no `engine.run`) | yes |
| SRCH-13 | `test_search_legs.py::test_default_engine_excludes_biorxiv` | ImportError (module) | yes |
| SRCH-14 | `test_query_honesty.py::test_pubmed_field_phrase_is_tagged_as_a_phrase`, `::test_pubmed_leaves_colons_inside_phrases_alone` | ImportError (no `engine.run`) | yes |
| SRCH-10 | `tests/kits/search/test_verifier.py::test_doi_resolving_to_a_different_title_is_a_mismatch_not_verified`, `::test_process_batch_never_swaps_a_mismatched_record` | `ok is True`; title swapped | yes |
| CORE-06 | `tests/kits/search/test_dedup.py::test_sci_ids_do_not_depend_on_input_order`; `tests/unit/test_discovery_legs.py::test_dedup_stage_ids_are_input_order_invariant` | ImportError `stable_order`; SCI-000001 vs SCI-000003 | yes |
| CORE-10 | `tests/unit/test_verification_bridge_conflict.py` (2) | `['SCI-000002', 'SCI-000002']` | yes |
| CORE-07 | `tests/unit/test_run_builds_snapshot.py` (3) | `SystemExit: 1` at `batcher.py:201` | yes |

**Milestone review (milestone-reviewer, verdict CHANGES at c6c1fed), fixed:**

| # | Finding | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- | :-- |
| R1 (P1) | `MAILTO_NOT_SET` never fired on `run`: the stage's proxies hid the providers | `test_discovery_legs.py::test_run_discovery_refuses_without_mailto_before_any_request` | DID NOT RAISE | yes |
| R2 (P1) | Staged RIS exports silently replaced the run's records in the snapshot | `test_run_builds_snapshot.py::test_staged_imports_are_never_silently_swapped_for_the_run` | ACCEPTED, 1 study | yes |
| R3 (P1) | Legs stopped at the cap were not counted as succeeded in the journal | `test_discovery_legs.py::test_capped_legs_count_as_succeeded_in_the_journal`; golden test asserts 5 | `()` succeeded | yes |
| R4 (P2) | Resume skipped the protocol and batch-coverage checks | `test_run_builds_snapshot.py::test_resume_refuses_an_edited_protocol`, `::test_resume_refuses_batches_that_do_not_cover_the_snapshot` | PENDING_AGENT_REVIEW | yes |
| R5 (P2) | The snapshot's PARTIAL outcome was built and dropped | `test_run_builds_snapshot.py::test_the_snapshot_outcome_is_journalled_with_provider_warnings` | KeyError `outcome_status` | yes |
| R6 (P2) | `NOT_BUILT` branches and the registered prepare-exit path untested | `test_run_builds_snapshot.py::test_no_project_json_reports_not_built`, `::test_unregistered_workspace_reports_not_built`, `::test_a_prepare_exit_in_a_registered_workspace_is_journalled` | (new coverage) | yes |
| P3 | Report said "more records exist" with no reported total; arXiv `OR ANDNOT` collapsed to `ANDNOT` | `test_discovery_legs.py::test_the_report_does_not_claim_more_records_when_no_total_was_reported`; `test_query_honesty.py::test_arxiv_and_not_becomes_andnot_but_or_not_is_left_alone` | wording; `ANDNOT` | yes |

## Decisions
- [2026-11-08 — The retrieval cap is a protocol method key](../../decisions.md)
- [2026-11-08 — A live search needs a real contact email](../../decisions.md)
- [2026-11-08 — One live golden search, frozen to cassettes](../../decisions.md)
- Contact address for the recording run: the researcher's university address, given for that run only (environment variable, not saved).

**Behaviour changes that update existing tests** (each pinned the old defect or old layout):
- `test_screening_prepare_stage.py::test_orchestrator_systemexit_propagates_without_mapping_or_pause`: a prepare exit is now journalled `PIPELINE_RUN_ABORTED` (plan §1.2 CORE-07 fix), still no report or pause row.
- `test_discovery_stage.py`: the literature folder also holds `search_runs/`; a failed harvest's outputs are its `legs.json` and `search_report.md` (no corpus file).
- `test_deduplication_stage.py`, `test_verification_stage.py`: content order, not arrival order (CORE-06).
- `test_protocol_adapter.py::test_compile_protocol_search_minimal_dict`: `max_results` is `None` (SRCH-31).
- `tests/inception/test_new_workspace_method.py`: new workspaces do not write `retrieval_cap`.
- The screening method view and methods figures leave `retrieval_cap` out (a discovery value).

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| baseline | 3b474cb | `uv run python scripts/generate_contract_baseline.py --check` | Contract baseline current | — |
| inner | 5655b24 | `uv run pytest tests/kits/search tests/kits/protocol -m "not slow"` | exit 0 | ~1 min |
| checkpoint | 62c7f3a | `uv run pytest tests/pipeline tests/unit tests/cli tests/console tests/inception -m "not slow" -n auto` | 0 failed (e2e needs `--extra rag`) | ~4 min |
| live record | 52646ee | `NEXUS_RECORD_CASSETTES=1 uv run pytest tests/pipeline/test_golden_search_cassettes.py` | cassette recorded, 6 requests | ~1 min |
| replay | 09aaf1d | `uv run pytest tests/pipeline/test_golden_search_cassettes.py` | 2 passed, offline | 17 s |
| contract | 81c7e53 | `generate_contract_baseline.py --check` | Contract baseline current | — |
| pr (1st) | c6c1fed | `uv run pytest -q -n auto` (dev+pdf+rag) | 1 failed (`test_pipeline_core` layering), fixed in c6c1fed | ~8 min |
| review | c6c1fed | milestone-reviewer | CHANGES: R1–R6 (+P3) | — |
| pr | 0b97ba1 | `uv run pytest -n auto` (dev+pdf+rag) | 4544 passed, 15 skipped, 0 failed | 16 min 27 s |
| lint | 0b97ba1 | `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9`; `git diff --check origin/main...HEAD` | clean | — |
| contract | 0b97ba1 | `generate_contract_baseline.py --check` | Contract baseline current | — |
| re-review | 0b97ba1 | milestone-reviewer | APPROVE (all six findings fixed, no new defect) | — |

## Deferred
- M3b: discovery specs 01–08 and the Discovery screens (plan §7 rule 1: M3 UI is the first cut); agent tasks (query critique, near-twin, methods text).
- `docs/architecture/contract_v1_baseline.md` still lists Packet B as not adopted. The file is hashed into the frozen baseline, so updating it needs the researcher's contract decision and a baseline regeneration; not done here.
- arXiv compaction itself stays (now reported, and skipped for NOT); replacing it with a full boolean translation is a later query-translation item.
- The engine ceiling (10,000) is a code constant, not a setting.
- Review P3, not done: no "stopped early" note when a leg ends below min(cap, total) without a reason; an empty harvest now ends FAILED (snapshot NOT_BUILT, then the prepare exit) rather than EMPTY_RESULT; `scholar_pdf` still has its own `student@university.edu` default (outside M3a, same issue).
- Verification and hydration of the golden search are not in the cassette (each is one request per record); the cassette covers the search legs, dedup and the Packet B snapshot ids.
