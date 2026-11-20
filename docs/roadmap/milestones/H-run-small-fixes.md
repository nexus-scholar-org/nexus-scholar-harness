# H-run-small-fixes The small defects of the 2026-11-20 acceptance run

Item agreed by the researcher on 2026-11-20 (second in the order of work after the acceptance run, after M3f-combined-corpus; that order is in plan §6 on `dev/docs/acceptance-run-part-2`, PR #262, not yet on `main`). Source: `docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md` (findings 1 to 17 on `main`; 18 to 39 on `dev/docs/acceptance-run-part-2`, PR #262). Delivered as three branches, one PR each, in this order:

| Part | Branch | Lane | Status |
| :-- | :-- | :-- | :-- |
| A, approve every decided batch with one paste (finding 38, the blocker) | `dev/h/run-fixes-approval` | RELEASE | READY FOR PR (review round 2 repaired, PR gate green on `0a1f7d25`); decisions 1 to 7 accepted 2026-11-20 |
| B, Discovery and the search command (findings 9, 10, 13, 14, 17, 24, 29; decision 2026-11-20 item 2) | `dev/h/run-fixes-discovery` | not started | — |
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
