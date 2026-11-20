# H-run-small-fixes The small defects of the 2026-11-20 acceptance run

Item agreed by the researcher on 2026-11-20 (second in the order of work after the acceptance run, after M3f-combined-corpus; that order is in plan §6 on `dev/docs/acceptance-run-part-2`, PR #262, not yet on `main`). Source: `docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md` (findings 1 to 17 on `main`; 18 to 39 on `dev/docs/acceptance-run-part-2`, PR #262). Delivered as three branches, one PR each, in this order:

| Part | Branch | Lane | Status |
| :-- | :-- | :-- | :-- |
| A, approve every decided batch with one paste (finding 38, the blocker) | `dev/h/run-fixes-approval` | RELEASE | MERGED 2026-11-20 (PR #264, merge commit `fdbc0c5f`); decisions 1 to 7 accepted by the researcher 2026-11-20 |
| B, Discovery and the search command (findings 9, 10, 13, 14, 17, 24, 29; decision 2026-11-20 item 2) | `dev/h/run-fixes-discovery` | RELEASE | READY FOR PR (review round 3 APPROVE; PR gate green on `3b5642fd` + UI gates on `2762ca4b`); decisions 1 to 8 PROPOSED |
| C, Inception and screening small defects (findings 1 to 7, 23, 35, 39; redesign D15 quick fixes) | `dev/h/run-fixes-inception` | not started | — |

Not in this item, already done the same day: the quota hang (H-quota-hang, PR #259); the agent-draft rule, method amendments and run screen (H-screening-drafts, PR #261). In another session, not touched here: M3f-combined-corpus (findings 26, 27; `corpus_accept.py`, the Import and Hand-off screens).

Each part branches from `origin/main` and is complete on its own; this file exists on each branch with the sections built so far.

---

## Part A: approve every decided batch with one paste (finding 38)

Branch `dev/h/run-fixes-approval` from `origin/main` `2436fe66`. Choices: `docs/decisions.md`, entry "2026-11-20 — H-run-small-fixes Part A" (items 1 to 7, accepted by the researcher 2026-11-20).

**The finding.** On Publish, approval was one batch at a time, each with a one-time code the engine printed in its terminal. The real review has 54 batches of 20: 54 requests, 54 codes of 26 characters typed by hand, and the terminal is not visible to a researcher for whom the app was started.

### Lane

**RELEASE** (`docs/architecture/test_gate_policy.md`): two new public routes on the approval path (`POST /actions/pairing/begin-all`, `POST /actions/pairing/redeem-all`), an additive public value (`code_shown_on: "desktop"`), and a change to where an approval code is shown. No Contract v1 schema, model, identity, fingerprint or artifact changes; the approval files, the publication approval, the journal row shape and the published files do not change.

### Contract question, answered without a contract change

The screening API contract §9.1 (researcher, 2026-11-04) says "a fresh one-time code is issued for each batch generation", and spec 09 decision 1 repeats it. A single code that approves many batches would change that decision, so it was **not built**. What was built keeps it: one fresh code per batch, staged, shown and pasted together, each redeemed by the unchanged single-batch path. The two other designs (one code for all; an Approve button in the engine's own desktop window) are written as alternatives in decision item 1 for the researcher to choose if the paste is not good enough.

### Definition of done

- [x] One action stages a fresh code for every fully decided, not currently approved, not deferred batch; the codes are printed on the terminal as one block of `batch n: CODE` lines and never returned over HTTP. Tests: `tests/console/test_approve_all.py::test_finding_38_one_action_approves_54_decided_batches`, `test_only_decided_not_yet_approved_batches_get_a_code`, `test_nothing_to_approve_is_a_refusal_not_an_empty_success`, `test_begin_all_needs_the_approver_name`.
- [x] One paste approves them all; each approval binds only its own batch's bytes (CON-03), one journal row per batch with the same shape (`bulk: true` added), each code used once. Tests: `test_finding_38_one_action_approves_54_decided_batches` (54 batches: approvals 1 to 54, each `final_decision_sha256` equal to its own decisions file, 54 journal rows, a second paste refused), `test_a_paste_that_lost_its_line_breaks_still_reads`.
- [x] The staleness rule is unchanged: a decision changed after approval makes the batch need a code again; a batch changed between the code and the paste is refused alone and the others are approved; the publication approval is staged only when every batch is approved. Tests: `test_a_decision_changed_after_approval_makes_the_batch_need_a_code_again`, `test_a_batch_changed_between_the_code_and_the_paste_is_refused_alone`.
- [x] A wrong paste approves nothing and answers the engine's refusal. Test: `test_a_wrong_paste_approves_nothing`.
- [x] The codes are shown where the researcher can get them without the terminal: `nexus-scholar ui` shows them in a window of the engine's own process on the desktop (never in the title, closes at expiry, Copy button); without it the codes stay on the terminal and the answer says so. Tests: `test_the_desktop_window_shows_the_codes_when_the_app_was_started_for_the_researcher`, `test_without_a_window_the_codes_stay_on_the_terminal`, `test_a_window_that_fails_leaves_the_codes_on_the_terminal`, `test_the_window_words_never_carry_a_code_and_the_title_is_fixed`, `test_the_window_can_be_turned_off`, `test_the_packaged_app_passes_the_desktop_window`.
- [x] Desktop only, loopback only: a phone token and a foreign origin are refused. Tests: `test_a_phone_token_cannot_reach_the_bulk_approval[begin-all|redeem-all]`, `test_a_foreign_origin_cannot_redeem`; the two allowlists (`console/browser.py`, `app/api/console/[...path]/route.ts`) carry the new paths.
- [x] Publish screen: "Show the codes for every decided batch", the paste field, "Approve the batches", the result per batch; the one-batch controls folded under "Approve one batch at a time"; en/fr/ar. Tests: `apps/research-ui/tests/screening-publish.test.tsx`, "publish.approve-all (finding 38)" (4 tests); the existing one-batch tests pass with the folded controls.
- [x] Specs amended: `docs/ux/phase2-screening/final/09-publish.md` (amendment 2026-11-20), `docs/architecture/screening-api-contract.md` (route rows, §9.1 note), `docs/architecture/research_ui/UI-07_ACTION_SPEC.md` (proposed amendment note above §3.1).
- [x] Reproducing test written first and seen failing (Evidence).
- [x] Contract baseline current; PR gate green on `0a1f7d25`; `milestone-reviewer` round 1 CHANGES (all repaired), round 2 CHANGES on one stray file only (removed in `0a1f7d25`; the reviewer said that removal makes it an APPROVE; not re-run after it).

### What changed

- `src/scholar_harness/authority/pairing.py`: `begin_pairing_all` (calls `begin_pairing` per ready batch), `bulk_skip_reason`, `format_code_block`, `parse_code_block`. `begin_pairing` and `redeem_pairing` are unchanged.
- `src/scholar_harness/console/api/screening_v1.py`: `POST /actions/pairing/begin-all`; `begin` and `begin-all` also call the desktop window when the app has one (`_show_on_desktop`).
- `src/scholar_harness/console/api/screening.py`: the single redeem's body moved into `_redeem_one` (same rollback, same journal row); `POST /actions/pairing/redeem-all` loops over it.
- `src/scholar_harness/console/code_window.py` (new): the Tk window, run as a child process (`python -I code_window.py`, codes on stdin; the file imports the standard library only, so the child starts in under a second). `serve.py` takes `code_window`; `launcher.py` passes `code_window.reveal`.
- UI: `lib/screening-v1.ts` (`beginApprovalAll`, `PairingBegunAll`), `lib/screening-api.ts` (`postPairingRedeemAll`, `RedeemAllResult`), `components/screening-publish.tsx`, the dev proxy allowlist.

### Review

Round 1 (`milestone-reviewer`, on `9286b175`): **CHANGES**, one P1, three P2, three P3. All repaired:

| # | Finding | Repair | Test |
| :-- | :-- | :-- | :-- |
| P1 | Tk was created in a thread of the engine; on macOS a first Tk load off the main thread aborts the whole process (not catchable) | The window runs in a child process (`python -I code_window.py`, codes on stdin, never argv); a crash stays in the child | `test_review_the_window_gets_the_codes_on_stdin_never_on_its_command_line`, `test_review_a_child_that_cannot_show_a_window_leaves_the_terminal`, `test_review_the_window_script_imports_the_standard_library_only` |
| P2 | One batch with a missing parent (`WorkerRefused` in `bulk_skip_reason`) stopped `begin-all` for all, after earlier codes were already replaced | The skip check moved inside the per-batch `try`; the batch is listed with its refusal | `test_review_one_broken_batch_does_not_block_the_others` |
| P2 | A journal failure mid-paste answered 200 and left the later batches unlisted | 500 `ACTION_AUDIT_FAILED` with `details.approved` and `details.refused` (later batches `NOT_ATTEMPTED`) | `test_review_a_journal_failure_mid_paste_is_a_500_that_names_every_batch` |
| P2 | Decision item 4 understated the residual: a token holder can make the window appear; the clipboard is now the normal path | Item 4 names both risks for the researcher to accept; the window names the batches and says to close it and copy nothing if the codes were not asked for | `test_review_the_window_says_which_batches_and_to_close_it_if_not_asked` |
| P3 | `(\d+)\s*:` backtracked quadratically (47 s on 40,000 digits); the paste cap was 200,000 characters | Batch number bounded to 6 digits; cap 64,000 characters | `test_review_a_long_run_of_digits_is_read_quickly` |
| P3 | No test that codes stay out of the redeem answer, the journal and the workspace files | Added | `test_review_the_codes_are_nowhere_but_the_terminal_after_a_bulk_run` |
| P3 | Decision and contract texts did not describe the 500 case and the per-batch begin refusals | Items 2, 3 and the contract rows updated | (docs) |

Follow-ups from the review also done: a batch refused a code for another reason is named with its code (not counted as "not fully decided"); the pasted block and a typed one-batch code are cleared on expiry (UI-07 §3.6); the re-raised refusal carries the request's own id; `_manifest_batches` skips an entry without a batch number; spec 09's key list. UI test: "names a batch the engine refused a code, and clears the pasted codes when they expire". Left as follow-ups: `bulkRefused` shows the engine's code untranslated (as the state cards do); the dev proxy's 120 s timeout would cut a paste of roughly 150 or more batches at the measured speed (the packaged app has no proxy).

### Evidence

| Check | Result |
| :-- | :-- |
| Reproducing test before the fix | `test_finding_38_one_action_approves_54_decided_batches` and the other route tests failed (no `begin-all` route; `create_app` had no `code_window`); run 2026-11-20 on the unfixed tree |
| New engine tests | `tests/console/test_approve_all.py`: 25 passed (17, then 8 from the review) |
| Neighbouring tests | `tests/console/test_approve_all.py tests/console/test_screening_api_v1.py tests/authority/test_pairing.py`: 104 passed |
| UI | `tests/screening-publish.test.tsx`: 21 passed; `tsc --noEmit` clean |
| Real window on this PC (Windows 11) | Before the repair (thread): `reveal` returned `True`, the thread ended at expiry. After it (child process): `reveal` returned `True` in 0.76 s; first attempt with `python -m` timed out at 5 s because importing the console package takes about 9 s, hence `python -I <file>` |
| Timing, 54 batches of 20, real PBKDF2 rounds | Codes ready after 34.9 s, 54 approvals in 40.3 s (one run, `begin-all` then `redeem-all` over the test client, while the gate ran on the same PC) |
| Inner gate (on the first commit) | authority, console and UI-related tests; one unrelated test (`tests/console/test_methods_method_block.py::test_without_a_block_the_paragraph_names_the_defaults`) failed once under parallel load and passed alone (9 of 9); it did not fail in the PR gate |
| PR gate on `0a1f7d25` (`select_test_gate.py --changed origin/main --stage pr`) | `git diff --check` clean; `uv run pytest -n auto`: 5842 passed, 15 skipped; ruff `scripts/` and the CI `src/` selection clean; `tsc` clean; vitest 962 passed (66 files); `build` ok; Playwright 606 passed, 12 skipped (it rewrites six tracked screenshots, restored with `git checkout`) |
| Contract baseline | `generate_contract_baseline.py --check`: current |
| Review | `milestone-reviewer`: round 1 CHANGES (1 P1, 3 P2, 3 P3) on `9286b175`, repaired in `9c39c4b4`; round 2 on the repair delta: every finding fixed, one new P3 (a vitest cache file committed under the root `node_modules/`), removed in `0a1f7d25`, root `node_modules/` now ignored |

### Not verified

- The window was opened on this PC by a script and closed itself at expiry; nobody looked at it, and the Copy button, the clipboard after the window closes, and how it looks on a high-DPI screen were not checked. On macOS and Linux it was not run at all (the child process is meant to make a Tk failure harmless there; without a display the codes stay on the terminal).
- Whether a window opened from a `pythonw` engine (no console) shows the same way was not tried; the child is started with `CREATE_NO_WINDOW` so no console window appears.
- Not run against the researcher's real workspace (`C:\Users\mouadh\Documents\Nexus Scholar\workspaces\` was not touched) nor through the installed wheel; not clicked in a browser (Playwright was not extended for this screen).
- Whether a program at Windows Low integrity can read the Tk window's text was not tested; the reasoning (UIPI blocks reading a higher-integrity window; the text is drawn by Tk, not held in a native edit control) is the same as for the terminal.

---

## Part B: Discovery and the search command

Branch `dev/h/run-fixes-discovery` from `origin/main` `2436fe66`. Choices: `docs/decisions.md`, entry "2026-11-20 — H-run-small-fixes Part B" (items 1 to 8, accepted by the researcher 2026-11-20).

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
