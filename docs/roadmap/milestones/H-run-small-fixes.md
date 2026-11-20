# H-run-small-fixes The small defects of the 2026-11-20 acceptance run

Item agreed by the researcher on 2026-11-20 (second in the order of work after the acceptance run, after M3f-combined-corpus; that order is in plan §6 on `dev/docs/acceptance-run-part-2`, PR #262, not yet on `main`). Source: `docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md` (findings 1 to 17 on `main`; 18 to 39 on `dev/docs/acceptance-run-part-2`). Delivered as three branches, one PR each, in this order:

| Part | Branch | Lane | Status |
| :-- | :-- | :-- | :-- |
| A, approve every decided batch with one paste (finding 38, the blocker) | `dev/h/run-fixes-approval` | RELEASE | READY FOR PR; its section is in this file on that branch |
| B, Discovery and the search command (findings 9, 10, 13, 14, 17, 24, 29; decision 2026-11-20 item 2) | `dev/h/run-fixes-discovery` | RELEASE | READY FOR PR (review round 3 APPROVE; PR gate green on `3b5642fd` + UI gates on `2762ca4b`); decisions 1 to 8 PROPOSED |
| C, Inception and screening small defects (findings 1 to 7, 23, 35, 39; redesign D15 quick fixes) | `dev/h/run-fixes-inception` | — | not started |

Each part branches from `origin/main` (`2436fe66`) and is complete on its own. This file and the top of `docs/decisions.md` exist on each branch with that part's section: the second and third PR to merge need a one-line conflict resolution (keep both sections, both entries).

Not in this item, already done the same day: the quota hang (H-quota-hang, PR #259); the agent-draft rule, method amendments and run screen (H-screening-drafts, PR #261). In another session, not touched here: M3f-combined-corpus (findings 26, 27; `corpus_accept.py`, the Import and Hand-off screens).

---

## Part B: Discovery and the search command

Branch `dev/h/run-fixes-discovery` from `origin/main` `2436fe66`. Choices: `docs/decisions.md`, entry "2026-11-20 — H-run-small-fixes Part B" (items 1 to 8, PROPOSED).

### Lane

**RELEASE** (`docs/architecture/test_gate_policy.md`): `scholar-search search` changes its exit code (a public CLI semantic), and `GET /discovery/plan` and the estimate gain public fields. No Contract v1 schema, identity, persistence or publication change; the protocol is never edited.

### Definition of done

- [x] Finding 9: Crossref is not ticked by default for a query that joins two or more concepts when the protocol took the default list; a protocol that names its own list keeps it; Plan and Harvest warn while Crossref is ticked for such a query; Harvest sends the default list. How the default is decided: decision item 1. Tests: `tests/console/test_discovery_api.py::test_finding_9_crossref_is_left_out_by_default_when_the_query_joins_concepts`, `test_a_protocol_that_names_its_own_list_keeps_crossref_with_the_warning`, `test_a_single_concept_query_keeps_crossref_without_a_warning[databases0|None]`, `test_a_protocol_without_a_list_also_leaves_crossref_out_for_a_joined_query`; UI `tests/discovery-plan.test.tsx` "discovery.plan Crossref and a joined query", `tests/discovery-harvest.test.tsx` "discovery.harvest Crossref and a joined query" (4).
- [x] Finding 10: no per-database cap is offered when one database fetches more than all the others together; the estimate names it. Tests: `tests/console/test_discovery_estimate_api.py::test_finding_10_a_cap_that_would_trim_one_database_is_not_offered`, `test_finding_10_the_acceptance_run_numbers`, `test_the_suggested_cap_is_the_largest_that_keeps_the_sum_at_the_limit` (now a non-dominant case); UI "names the one database that is the size and offers no cap".
- [x] Finding 13: not built (not cheap; touches the corpus combination M3f is building). Design and open questions in decision item 8; follow-up.
- [x] Finding 14: a 429 without a lower rate header paces the host's shared budget (halved, floor one per second). Tests: `tests/kits/search/test_crossref_pacing.py` (3). Not checked against the real Crossref.
- [x] Findings 17 and 24: "Checked {date}" without "UTC" (en/fr/ar); the Crossref count came from the check asking every protocol database (from the code); a check sent no list now asks the default choice. Test: `tests/console/test_discovery_api.py::test_finding_24_the_recall_check_asks_the_default_databases_not_crossref`; `test_m10a_a_recall_on_an_empty_protocol_list_asks_the_engines_default_suite` updated (a joined query leaves Crossref out of the default suite).
- [x] Decision 2026-11-20 item 2: arXiv's count with a year window is exact; no "upper limit" note. Test: `tests/console/test_discovery_estimate_api.py::test_decision_2026_11_20_item_2_arxiv_with_a_year_window_is_counted_exactly` (replaces the test that pinned the upper bound).
- [x] Finding 29: `scholar-search search` names each database stopped at the limit (with its reported total) and each failure; exit 1 and no file when a database failed and nothing was found; exit 2 when it saved a partial result. Tests: `tests/kits/search/test_cli_search_outcome.py` (4).
- [x] The UI test fake (`tests/fixtures/discovery-engine.ts`) follows the engine (plan fields, arXiv exact, the one-database rule).
- [x] Specs amended: `docs/ux/phase1-discovery/final/01-plan.md`, `02-recall.md`, `03-harvest.md`.
- [x] Reproducing tests written first and seen failing (Evidence).
- [x] PR gate green; `milestone-reviewer` APPROVE (Evidence).

### What changed

- `src/scholar_search/protocol_adapter.py`: `concept_count`.
- `src/scholar_search/plan.py`: `IGNORES_AND`, `default_choice`, `and_warnings`.
- `src/scholar_search/estimate.py`: `UPPER_BOUND_WITH_YEARS` empty; `_dominant` and the `one_database` recommendation.
- `src/scholar_search/http_client.py`: `slow_down(url)`, called on a 429 without a rate header in the GET retry path (the POST path is unchanged).
- `src/scholar_search/cli.py`: `_report_legs`, the exit codes, the `--limit` help.
- `src/scholar_search/plan.py` also: `took_default_list` (the protocol's list as written).
- `src/scholar_harness/console/api/discovery.py`: `_Protocol.concepts`, `.raw_databases`, `.default_choice()`; the plan's new fields; the recall and estimate default (no list = the default choice). Plan and Harvest always send their choice to the estimate (review N1).
- UI: `lib/discovery-api.ts` (types), `lib/discovery-copy.ts` (three keys, `recall.checkedAt`), `components/discovery-plan.tsx` (`defaultList`, `IgnoresAndNotes`, the first read), `components/discovery-harvest.tsx`, `components/discovery-estimate.tsx`.

### Review

Round 1 (`milestone-reviewer`, on `006eb7e9`): **CHANGES**, one P1, two P2, two P3. All repaired:

| # | Finding | Repair | Test |
| :-- | :-- | :-- | :-- |
| P1 | The Harvest estimate counted the protocol's list (Crossref included) while the harvest would search the default choice: finding 24 again | Harvest sends its choice to the estimate as it does to the run; the engine counts the default choice for an estimate sent no list | `tests/console/test_discovery_estimate_api.py::test_review_an_estimate_sent_no_list_counts_the_default_choice`; UI "starts without Crossref…" checks the estimate body |
| P2 | The one-database rule was judged on capped numbers (a cap of 1,000 brought the cap advice back for the run's numbers), and the copy said a cap trims "only" that database | Judged on reported totals; copy says a cap cannot remove that database's off-topic records (en/fr/ar) | `test_finding_10_the_acceptance_run_numbers[10000\|1000]`, `test_two_large_databases_where_one_is_slightly_larger_is_still_named` |
| P2 | "Took the default list" was judged after unknown names were dropped (an imported list with `scopus`, `wos` lost Crossref) | Judged on the list as written (`plan.took_default_list`) | `test_review_took_the_default_list_is_judged_on_the_list_as_written` (4 cases) |
| P3 | A refused second plan read left the Plan picker and preview out of step | The default read counts as done only once it succeeded | (code) |
| P3 | The skill line omitted the 20-record default without a protocol | Fixed | (docs) |

Round 2 (on `7bcd29c3`): **CHANGES**, every round-1 finding repaired; one new P1 (N1: after "Reset to the protocol" the estimate, sent no list, would leave a ticked Crossref out, since no list now means the default choice) and one P3 (N2, this record's "What changed"). Repaired in the next commit: both screens always send the choice to the estimate; the fake counts the default choice for an estimate sent no list; tests `tests/discovery-plan.test.tsx` and `tests/discovery-harvest.test.tsx` "after Reset to the protocol, the estimate counts Crossref (review N1)", engine `test_review_an_estimate_sent_the_protocol_list_counts_crossref`; six estimate tests that pinned an empty body updated. Its follow-up also done: a header rate is compared with the configured and announced rate, not a held 429 pace (`test_a_lower_header_rate_is_kept_while_a_429_pace_holds`).

Follow-ups also done: a 429 pace expires after 10 minutes, a burst of 429s halves once, and the bucket allows no burst while the pace holds (`test_a_burst_of_429s_halves_the_pace_once`, `test_the_pace_set_by_a_429_expires`); a concept whose terms are joined with AND counts per term (`tests/kits/search/test_protocol_adapter.py::test_concept_count_counts_each_term_of_an_and_concept`); exit codes in the search skill's reference. Not done: the unused `scholar_search.cli.search` import in `scholar_agent/server.py` (harmless, outside this item).

### Evidence

| Check | Result |
| :-- | :-- |
| Reproducing tests before the fix | 15 of the new or changed engine and CLI tests failed on the unfixed code (run 2026-11-20, `tests/kits/search/test_cli_search_outcome.py`, `test_crossref_pacing.py`, `tests/console/test_discovery_estimate_api.py`, `tests/console/test_discovery_api.py`); the one that passed was the "complete result" control |
| After the fix and the review repairs | `tests/kits/search` (all), `tests/console/test_discovery_estimate_api.py`, `test_discovery_api.py`: 576 passed; `test_crossref_pacing.py` run three times: 5 passed each |
| UI | `tests/discovery-plan.test.tsx`, `discovery-harvest.test.tsx`, `discovery-estimate.test.tsx`: 77 passed; all `tests/discovery*`: 209 passed; `tsc` clean |
| PR gate | On `3b5642fd` (`select_test_gate.py --changed origin/main --stage pr`): `git diff --check` clean; `uv run pytest -n auto`: 5844 passed, 15 skipped; ruff `scripts/` and the CI `src/` selection clean; skills bundle in sync; `tsc` clean; `build` ok. Vitest then failed one test (the guidance audit had no row for `plan.ignoresAnd`, `plan.defaultWithout`) and Playwright two (`discovery.spec.ts` "a database that fails its count" expected "at least 1008", now 1065 because arXiv counts exactly): fixed in `2762ca4b` (audit row D-P22, counts 101 / 35 / 15; the expectation). On `2762ca4b` (only a spec and a browser test changed, no Python): `tsc` clean, vitest 965 passed (66 files), `build` ok, Playwright 606 passed, 12 skipped (six tracked screenshots rewritten and restored) |
| Contract baseline | `generate_contract_baseline.py --check`: current (on `3b5642fd`) |
| Review | `milestone-reviewer`: round 1 CHANGES (1 P1, 2 P2, 2 P3) on `006eb7e9`; round 2 CHANGES (one new P1, N1, and one P3) on `7bcd29c3`; round 3 APPROVE on `3b5642fd` (no new finding) |

### Not verified

- Nothing was sent to a real database: whether Crossref's 429s in the run were the kind the pacing removes, and whether a real Crossref count for the acceptance run's query is still 6,221, were not checked.
- The finding 24 explanation is read from the code; the second workspace's recall check file was not opened.
- Not run through the installed wheel or on the researcher's workspaces; the screens were not looked at in a browser beyond the Playwright suite.
