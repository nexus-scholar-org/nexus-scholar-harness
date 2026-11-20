# H-run-small-fixes The small defects of the 2026-11-20 acceptance run

Item agreed by the researcher on 2026-11-20 (second in the order of work after the acceptance run, after M3f-combined-corpus; that order is in plan §6 on `dev/docs/acceptance-run-part-2`, PR #262, not yet on `main`). Source: `docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md` (findings 1 to 17 on `main`; 18 to 39 on `dev/docs/acceptance-run-part-2`). Delivered as three branches, one PR each, in this order:

| Part | Branch | Lane | Status |
| :-- | :-- | :-- | :-- |
| A, approve every decided batch with one paste (finding 38, the blocker) | `dev/h/run-fixes-approval` | RELEASE | READY FOR PR; its section is in this file on that branch |
| B, Discovery and the search command (findings 9, 10, 13, 14, 17, 24, 29; decision 2026-11-20 item 2) | `dev/h/run-fixes-discovery` | RELEASE | {STATUS} |
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
- [ ] PR gate green; `milestone-reviewer` APPROVE (Evidence).

### What changed

- `src/scholar_search/protocol_adapter.py`: `concept_count`.
- `src/scholar_search/plan.py`: `IGNORES_AND`, `default_choice`, `and_warnings`.
- `src/scholar_search/estimate.py`: `UPPER_BOUND_WITH_YEARS` empty; `_dominant` and the `one_database` recommendation.
- `src/scholar_search/http_client.py`: `slow_down(url)`, called on a 429 without a rate header in the GET retry path (the POST path is unchanged).
- `src/scholar_search/cli.py`: `_report_legs`, the exit codes, the `--limit` help.
- `src/scholar_harness/console/api/discovery.py`: `_Protocol.concepts`, `.named`, `.default_choice()`; the plan's new fields; the recall default.
- UI: `lib/discovery-api.ts` (types), `lib/discovery-copy.ts` (three keys, `recall.checkedAt`), `components/discovery-plan.tsx` (`defaultList`, `IgnoresAndNotes`, the first read), `components/discovery-harvest.tsx`, `components/discovery-estimate.tsx`.

### Evidence

| Check | Result |
| :-- | :-- |
| Reproducing tests before the fix | 15 of the new or changed engine and CLI tests failed on the unfixed code (run 2026-11-20, `tests/kits/search/test_cli_search_outcome.py`, `test_crossref_pacing.py`, `tests/console/test_discovery_estimate_api.py`, `tests/console/test_discovery_api.py`); the one that passed was the "complete result" control |
| After the fix | the same files plus `tests/kits/search/test_cli.py` and `test_provider_resilience.py`: 176 passed (after the M10a recall test was updated) |
| UI | `tests/discovery-plan.test.tsx`, `discovery-harvest.test.tsx`, `discovery-estimate.test.tsx`: 77 passed; all `tests/discovery*`: {UI_ALL}; `tsc` clean |
| PR gate | {PR} |
| Contract baseline | {BASELINE} |
| Review | {REVIEW} |

### Not verified

- Nothing was sent to a real database: whether Crossref's 429s in the run were the kind the pacing removes, and whether a real Crossref count for the acceptance run's query is still 6,221, were not checked.
- The finding 24 explanation is read from the code; the second workspace's recall check file was not opened.
- Not run through the installed wheel or on the researcher's workspaces; the screens were not looked at in a browser beyond the Playwright suite.
