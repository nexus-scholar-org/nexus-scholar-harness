# H-protocol-signals Protocol-change signals and the discovery corpus view (F2, F3, F4)
Branch: dev/hardening/protocol-signals · Lane: **RELEASE** (the diff changes public HTTP responses: `/screening/summary`, `/screening/queue`, `/screening/prisma/preview`, `/discovery/runs`, `/discovery/handoff`, `/screening/corpus`, and widens the accept refusal `PROTOCOL_CHANGED_SINCE_RUN`; `test_gate_policy.md` §lanes, as for H-input-limits and M3h-providers. No Contract v1 schema, artifact identity or snapshot change: `generate_contract_baseline.py --check` passes) · Status: IN PROGRESS · Started: 2026-11-12

Scope is items 3 and 6 of the hardening plan in
[`three-phase-hardening-2026-11-10.md`](../../assessment/three-phase-hardening-2026-11-10.md) §4:
the protocol-change signals (F2, F3) and the corpus view of a discovery corpus
(F4). The two M3d reviewer follow-ups listed beside F4 are out of scope.
`corpus_accept.py` edits stay inside `corpus_status` and the run accept gate
(`refuse_if_run_protocol_changed`), because the concurrent branch
`dev/m3g/chase-accept-pending` touches the chase accept path in the same file.

## Definition of done
- [x] F2: `bound_to_current_protocol` is false after a semantic protocol edit (non-vacuous: no winners is not "bound"; a batch prepared under another protocol fails it); `/summary` and `/queue` carry `protocol_changed`; the choice is recorded in `docs/decisions.md` (`tests/console/test_screening_api_v1.py`).
- [x] F2: Screening Home says the protocol changed after screening started instead of an empty queue (en/fr/ar copy, vitest).
- [x] F2: only the current round's batches count (M3g rounds): an archived round prepared under an earlier protocol does not raise the flag (`tests/console/test_chase_api.py::test_f2_an_archived_round_never_raises_the_protocol_flag`).
- [x] F3: a run records `protocol_fingerprint` and the search it compiled (query, years, language, cap, databases) in `legs.json`; `GET /discovery/runs` items and `GET /discovery/handoff` carry `protocol_changed` before any accept (`tests/console/test_discovery_api.py`).
- [x] F3: the accept refusal `PROTOCOL_CHANGED_SINCE_RUN` also covers a changed database list, language or cap; a criteria-only edit is flagged but does not refuse (decision recorded).
- [x] F3: the Hand-off screen warns before the accept click (en/fr/ar copy, vitest).
- [x] F4: after a browser harvest `GET /screening/corpus` reports `databases` from the run's legs and `preview` from `deduped.json`, before and after the accept; a round-2 (chase) snapshot is checked (`tests/console/test_discovery_api.py`, `tests/console/test_chase_api.py`).
- [x] Each finding re-verified by `phase-auditor` before the fix; failing test written first.
- [ ] Closure gate on the final commit, `generate_contract_baseline.py --check`, `milestone-reviewer` APPROVE.

## Findings fixed
Each finding was re-verified open at `fd3cc329` by `phase-auditor` (F2 and F4 run in a scratch test: after three decisions and a protocol edit `/summary` gave `decided: 0` with no reason and `/prisma/preview` `bound_to_current_protocol: true`; a two-database browser run gave `databases: []` and a zero `preview` before and after the accept; F3 by reading: `legs.json` has no fingerprint, `/runs` and `/handoff` compare nothing).

| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| F2 | `tests/console/test_screening_api_v1.py::test_f2_a_protocol_edit_after_decisions_is_not_bound_and_is_flagged`, `::test_f2_no_decisions_is_not_vacuously_bound`, `::test_f2_nothing_prepared_reports_no_protocol_change` | yes at `fd3cc329`: 3 failed (`KeyError: 'protocol_changed'`; the check `True` with no decision) | yes |
| F2 (UI) | `apps/research-ui/tests/screening-home.test.tsx` "review F2: says the protocol changed after screening started instead of an empty queue" | yes with the `fd3cc329` components and copy (no such heading or card) | yes |
| F3 | `tests/console/test_discovery_api.py::test_f3_a_run_records_the_protocol_it_searched`, `::test_f3_a_search_edit_is_flagged_before_the_accept_and_refused_by_it` (databases, languages, cap), `::test_f3_a_criteria_edit_is_flagged_but_the_search_still_stands`, `::test_f3_a_run_from_before_the_fingerprint_reads_by_its_query` | yes at `fd3cc329`: 6 failed (`KeyError` on `protocol_fingerprint`, `protocol_changed`, `search_changed`) | yes |
| F3 (UI) | `apps/research-ui/tests/discovery-handoff.test.tsx` "review F3: warns before the click ...", "... says a change outside the search ...", "... says nothing when the protocol is the run's" | the first two fail with the `fd3cc329` components and copy | yes |
| F4 | `tests/console/test_discovery_api.py::test_f4_the_corpus_view_of_a_browser_harvest_shows_its_databases_and_counts`, `::test_f4_a_corpus_of_imports_keeps_its_own_view`; `tests/console/test_chase_api.py::test_f4_a_round_2_corpus_view_shows_the_chase` | yes at `fd3cc329`: 3 failed (`KeyError: 'origin'`; the auditor's run shows the zeros the first assertions after it check) | yes |

The F4 tests sit in `test_discovery_api.py` and `test_chase_api.py`, not `test_corpus_api.py` as the review proposed: that file tests the `/corpus` records page, and the two files named hold the browser-run and chase fixtures.

## Decisions
- [2026-11-12 — Protocol-change signals are flags; the hand-off accept refuses a changed search only](../../decisions.md) (proposed; the researcher confirms at the PR). F2 chose the flag `protocol_changed` over the refusal `PROTOCOL_CHANGED_SINCE_BATCH`; `PROTOCOL_CHANGED_SINCE_BATCH` is a UI state card only. F3 widened `PROTOCOL_CHANGED_SINCE_RUN` to the compiled search (query, years, language, cap, databases) and flags a criteria-only edit without refusing.
- Recovery after F2 is undoing the edit or replacing the protocol through Inception (M4d archive); Prepare cannot rebind, because it refuses a protocol that differs from the accepted corpus's.
- The screening API UI fixtures (`tests/fixtures/screening_api/`) were regenerated with `scripts/generate_screening_api_fixtures.py`: four files gain `protocol_changed: false`, nothing else changes.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| baseline | `fd3cc329` | `generate_contract_baseline.py --check` | current | <1 min |
| inner | working tree on `fd3cc329` (F2) | `pytest tests/console/test_screening_api_v1.py tests/console/test_chase_api.py tests/test_screening_events.py tests/e2e/test_golden_screening_api.py tests/console/test_methods_api.py` | all pass (121) | ~2 min |
| inner | working tree (F3) | `pytest tests/console/test_discovery_api.py tests/console/test_chase_api.py tests/pipeline -n 4` | all pass, 3 skipped | ~3 min |
| inner | `2e4dddf5` | `select_test_gate.py --changed main --stage inner`: `git diff --check`, screening tests, `tests/console -n auto`, `tests/pipeline tests/unit`, handoff; ruff bug classes on `src/` | all pass after regenerating the 4 screening API fixtures (`test_screening_api_contract.py` named them stale); ruff clean | ~6 min |
| inner | `fac1d4ed` | `tsc --noEmit`; full vitest | typecheck clean; vitest 519 passed (40 files) | ~2 min |
| review | `fac1d4ed` | `milestone-reviewer` | **CHANGES**: (1, P2) the archived-round test for the F2 DoD was uncommitted, Findings and Evidence empty; (2) F4 test path in the DoD; (3) a chase round after an imports round untested; (4) Home called a harvest "imported", and a chase round listed its legs as databases; (5) `protocol_search` compared by strict equality, coupled to the adapter's default database list (F15); (6) the decision overstated what the gate checks | |
| closure | `fac1d4ed` | closure gate | stopped before it finished (the repair below changes executable code) | |
| inner | repair | `pytest tests/console/test_discovery_api.py tests/console/test_chase_api.py tests/console/test_screening_api_v1.py tests/console/test_corpus_import_api.py -n 4`; `tsc --noEmit`; vitest screening-home, discovery-handoff | all pass; the new Home test fails with the line ungated | ~3 min |

Repairs: (1) committed `test_f2_an_archived_round_never_raises_the_protocol_flag`, tables filled; (2) DoD paths; (3) a chase round fills `origin` and `preview` only; `databases` stays the staged exports' rows (none after a harvest round 1) and `from_discovery` keeps its value (citation searching is not a database row), test `test_f4_a_round_2_after_imports_keeps_the_imports_as_its_databases`; (4) the Home "imported" line shows only for `origin: "imports"` (vitest "review F4: says what was imported only for imports ..."); (5) the database list is recorded only when the protocol names one and only the keys both records hold are compared (`test_f3_a_key_the_run_did_not_record_is_not_an_edit`, `test_f3_a_protocol_without_a_database_list_records_none`); (6) decision reworded. The stale hand-off comment is rewritten.

## Deferred
- The hand-off headline still carries no number for a harvest ("Accept this corpus for screening?"). F4 now sends `preview.unique_studies`, but that is the count after deduplication and before verification, while the snapshot is built from `verified.json`; showing it as "these N works" could disagree with the accepted count. Left as it was (M3c-screens deferred item).
- The M3d reviewer follow-ups listed beside F4 (`limits` used for two things, the `selected` status) are not in this milestone.
