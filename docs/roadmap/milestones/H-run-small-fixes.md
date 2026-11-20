# H-run-small-fixes The small defects of the 2026-11-20 acceptance run

Item agreed by the researcher on 2026-11-20 (plan §6, "After the acceptance run": second, after M3f-combined-corpus). Source: `docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md` (findings 1 to 17 on `main`; 18 to 39 on `dev/docs/acceptance-run-part-2`, PR #262). Delivered as three branches, one PR each, in this order:

| Part | Branch | Lane | Status |
| :-- | :-- | :-- | :-- |
| A, approve every decided batch with one paste (finding 38, the blocker) | `dev/h/run-fixes-approval` | RELEASE | in review (see Part A) |
| B, Discovery and the search command (findings 9, 10, 13, 14, 17, 24, 29; decision 2026-11-20 item 2) | `dev/h/run-fixes-discovery` | not started | — |
| C, Inception and screening small defects (findings 1 to 7, 23, 35, 39; redesign D15 quick fixes) | `dev/h/run-fixes-inception` | not started | — |

Not in this item, already done the same day: the quota hang (H-quota-hang, PR #259); the agent-draft rule, method amendments and run screen (H-screening-drafts, PR #261). In another session, not touched here: M3f-combined-corpus (findings 26, 27; `corpus_accept.py`, the Import and Hand-off screens).

Each part branches from `origin/main` and is complete on its own; this file exists on each branch with the sections built so far.

---

## Part A: approve every decided batch with one paste (finding 38)

Branch `dev/h/run-fixes-approval` from `origin/main` `2436fe66`. Choices: `docs/decisions.md`, entry "2026-11-20 — H-run-small-fixes Part A" (items 1 to 7, PROPOSED).

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
- [ ] Contract baseline current; PR gate green; `milestone-reviewer` APPROVE (Evidence).

### What changed

- `src/scholar_harness/authority/pairing.py`: `begin_pairing_all` (calls `begin_pairing` per ready batch), `bulk_skip_reason`, `format_code_block`, `parse_code_block`. `begin_pairing` and `redeem_pairing` are unchanged.
- `src/scholar_harness/console/api/screening_v1.py`: `POST /actions/pairing/begin-all`; `begin` and `begin-all` also call the desktop window when the app has one (`_show_on_desktop`).
- `src/scholar_harness/console/api/screening.py`: the single redeem's body moved into `_redeem_one` (same rollback, same journal row); `POST /actions/pairing/redeem-all` loops over it.
- `src/scholar_harness/console/code_window.py` (new): the Tk window. `serve.py` takes `code_window`; `launcher.py` passes `code_window.reveal`.
- UI: `lib/screening-v1.ts` (`beginApprovalAll`, `PairingBegunAll`), `lib/screening-api.ts` (`postPairingRedeemAll`, `RedeemAllResult`), `components/screening-publish.tsx`, the dev proxy allowlist.

### Evidence

| Check | Result |
| :-- | :-- |
| Reproducing test before the fix | `test_finding_38_one_action_approves_54_decided_batches` and the other route tests failed (no `begin-all` route; `create_app` had no `code_window`); run 2026-11-20 on the unfixed tree |
| New engine tests | `tests/console/test_approve_all.py`: 17 passed |
| Neighbouring tests | `tests/console/test_approve_all.py tests/console/test_screening_api_v1.py tests/authority/test_pairing.py`: 104 passed |
| UI | `tests/screening-publish.test.tsx`: 20 passed; `tsc --noEmit` clean |
| Real window on this PC (Windows 11) | `code_window.reveal` returned `True`; its thread ended at the 3-second expiry |
| Timing, 54 batches of 20, real PBKDF2 rounds | Codes ready after 34.9 s, 54 approvals in 40.3 s (one run, `begin-all` then `redeem-all` over the test client, while the gate ran on the same PC) |
| Inner gate | {INNER} |
| PR gate | {PR} |
| Contract baseline | `generate_contract_baseline.py --check`: current |
| Review | {REVIEW} |

### Not verified

- The window was opened once on this PC by a script and closed itself at expiry; nobody looked at it, and the Copy button, the clipboard after the window closes, and how it looks on a high-DPI screen were not checked. On macOS and Linux it was not run at all (Tk needs a display; without one the codes stay on the terminal).
- Not run against the researcher's real workspace (`C:\Users\mouadh\Documents\Nexus Scholar\workspaces\` was not touched) nor through the installed wheel; not clicked in a browser (Playwright was not extended for this screen).
- Whether a program at Windows Low integrity can read the Tk window's text was not tested; the reasoning (UIPI blocks reading a higher-integrity window; the text is drawn by Tk, not held in a native edit control) is the same as for the terminal.
