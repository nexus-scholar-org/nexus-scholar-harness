# M6-beta Beta UX: fewer clicks, details on demand, four trust fixes
Branch: `dev/m6/beta-ux` (from `main` after M5b merges) · Lane: **STANDARD** (UI and small engine fixes; escalate to RELEASE only if the currentness item below changes `require_current_generation`'s contract) · Status: IN PROGRESS · Written: 2026-11-06 · Started: 2026-11-07 (M5b merged: PR #195, #196)

Why: the researcher's direction on 2026-11-06. The product goes to beta testers next; the workspaces are not expected to carry the PhD review. Testers will spend almost all their time in triage, and the researcher's own run found "a lot of clicks and scrolling" and provenance everywhere. The [full review](../../assessment/full-review-2026-11-06.md) (sections 2 and 3) lists the defects; this milestone takes the ones a tester meets and leaves the rest parked. Source of the rule applied throughout: the brand book, "plain words first, raw value underneath", read as **the raw value is one disclosure away, never inline**.

Plan: a new §6 row is added to [`production-plan.md`](../production-plan.md) at start (after M5b). Specs to amend to FINAL before the UI work: 01, 03, 05, 09, 10 in [`docs/ux/phase2-screening/final/`](../../ux/phase2-screening/final/), plus one shared rule page, `12-details-disclosure.md`.

## Scope

**In:** the triage loop, the details rule on every screening screen, the two trust breaks (Prepare batch size, workspace status), the methods paragraph's repetition, the all-decided and undo states, and four correctness gates that a tester would otherwise hit or that would make an upgrade impossible.

**Out, parked and said so in the plan row:** gate part 3 (the 1,644-record prompt gate; it measures agreement with earlier AI labels, review S-P0-2), the second-screener lane, the PRISMA-ScR checklist rewrite, the phone (M2), the Windows pytest job, the dead-code cut, the extras split, the live audit view. Discovery stays stretch.

## Definition of done

### A. Triage: the click tax (specs 03 and 05 amended)

- [ ] **Answer until decisive.** The checklist stops being all-or-nothing. An Exclude is enabled as soon as one criterion is failed (an inclusion answered no, or an exclusion answered yes); an Include needs every inclusion answered yes and no exclusion answered yes; Unclear is always enabled. Unanswered criteria are stored as absent, not as `not_reported`. Engine: no change (`events.py` validates the reason code only; `criteria` stays optional in the contract). UI: `lib/triage-logic.ts` `allAnswered` replaced by `decisiveFor(outcome)`; the "Answer every criterion before deciding" line replaced by "Exclude is ready: INC-01 answered no" / "Include needs INC-02 and INC-03". Vitest `triage.decisive.test.tsx`; the spec 05 §9.3 sentence rewritten.
- [ ] **The reason comes from the checklist.** On Exclude, the reason is pre-selected as the first failed criterion in protocol order and shown in words ("Fails INC-01 · Uses UAV-acquired imagery …", code in mono underneath); the other codes stay available as chips with their first clause as label (`lib/triage-copy.ts` reason labels from the protocol text, truncated at 60 characters). Enter confirms the pre-selected reason, so E then Enter excludes. Engine (optional, S-P1-3 of the review): `REASON_CODE_INCONSISTENT` refusal when an EXCLUDE's code names a criterion the event answers the other way; test in `tests/test_screening_events.py`. Vitest `triage.reason-from-checklist.test.tsx`.
- [ ] **Advance on decide.** After a decision with no draft to reveal, the next record opens at once; with a draft, the revealed state shows as today and N advances. A per-workspace setting "After I decide: show the draft, then N · move on at once (drafts stay in the record's details)" on Prepare, default the first. Setting stored with the others (`GET/PUT /settings`, journaled `SCREENING_SETTINGS_CHANGED`) and reported by the methods paragraph only when drafts were skipped. Vitest `triage.advance-on-decide.test.tsx`; Playwright: 10 records decided by keyboard in under 10 keypresses each.
- [ ] **Position and a collapsed queue.** "Record 12 of 30 · batch 1" above the record; the queue card collapsed to the chips plus the current and next titles, expanded by J/K or a toggle, remembered per session. Vitest `triage.position.test.tsx`; Playwright at 1440 and 1024.
- [ ] **Undo only when it can.** Z and the Undo button are absent until the record has a superseding target; the "cannot be undone" copy goes. Change my decision stays. Vitest `triage.undo-hidden.test.tsx`.
- [ ] **All decided is a hand-off, not a dead screen.** When the queue view is empty the centre shows "All 30 records are decided" with Publish as the one brand button and Agreement as a link; the draft aside is not rendered; the subtitle stops describing the blinding setting. Vitest `triage.all-decided.test.tsx`.

### B. Details on demand (new rule page 12, applied to 01, 03, 05, 09, 10)

- [ ] **The rule.** Each screen shows what the researcher acts on; identifiers and proofs sit behind one "Details" disclosure per card, closed by default, keyboard-reachable, with a consistent label. Moved behind it: study ids, DOIs' raw form, protocol and batch fingerprints, generation ids and fingerprints, event ids, the "Recorded as you · HUMAN · time · protocol sha" line (the card keeps one word, "Saved", with the time on hover), run ids, prompt hashes, refusal codes (the plain sentence stays, the code moves into the disclosure), the batch file names on Home and Publish. Nothing is removed from the DOM, so the Playwright provenance checks still find it. Written as `12-details-disclosure.md` (FINAL) with the list per screen.
- [ ] **Home (01).** The first screen is the next action and three numbers: need you, decided, included so far. Batches, "Who screens", the terminal block and the counts of drafts move below a fold or into Details. The raw `NOT_PREPARED` code leaves the card body. Vitest `home.compact.test.tsx`.
- [ ] **Publish (09).** Checks shown as one line each with a pass mark; the fingerprint and the digests behind Details; the PRISMA preview keeps the numbers and the reasons table. Vitest `publish.details.test.tsx`.
- [ ] **Export (10).** The generation fingerprint and the sources list behind Details; the paragraph first. Vitest `export.details.test.tsx`.
- [ ] **Rendered axe** passes on every amended screen in en and ar, light and dark (`tests-browser/rendered-axe.spec.ts` extended).

### C. The trust breaks

- [ ] **Prepare batch size is real.** `POST /prepare` passes `batch_size` to the job (`console/runtimes/actions.py` `screen_prepare` gains `--batch-size`, `job_runner.start` takes the argument list), bounded 5–100, refusal `BATCH_SIZE_INVALID` (422) outside it. Test `tests/console/test_screening_v1_prepare.py::test_prepare_honours_batch_size` (10 → 3 batches of 10, 10, 10 on the golden fixture). If passing the argument is not done in this milestone, the field is removed from the screen instead; the dialog may never promise what the engine ignores.
- [ ] **The workspace status is the publication status.** `workspace/catalog.py` derives the row's status in this order: published and current → "Published"; published with later decisions → "Published, decisions since"; batches with undecided records → "Screening in progress"; corpus accepted → "Corpus accepted"; else "New". The last journal action moves to the "Last activity" column only. Tests in `tests/console/test_workspaces_api.py`; vitest `workspaces.status.test.tsx`. The "Open now" badge becomes a status chip, not a wrapped button.
- [ ] **The methods paragraph reads as prose.** Settings rows whose value did not change are collapsed (`export.py` `_timeline`: drop no-op rows before sentences); "After seeing a draft, the reviewer changed k of n decisions" is emitted only when at least one decision was made before its reveal, otherwise "n decisions were made with the draft visible; no blind comparison is reported"; "provider not recorded" becomes "via the researcher's Claude session (MCP)" when every draft carries `driver: mcp`. Tests in `tests/console/test_methods_api.py` (`no_op_settings_rows_are_not_repeated`, `visible_drafts_report_no_blind_comparison`, `mcp_drafts_name_the_route`). Run against the 2026-11-06 evidence workspace as the fixture.

### D. Correctness gates before testers

- [ ] **Published means current.** `stale_projections` is checked inside `require_current_generation` (or one wrapper that `/ui/publication-status`, `/summary`, export and methods all call), returning `GENERATION_STALE` with `stale_batches`. Decision entry in `docs/decisions.md` first; if the check changes stored semantics, `BLOCKED_BASELINE_DRIFT` rules apply and the lane escalates. Test `tests/authority/test_publication_generations.py::test_a_decision_after_publish_makes_the_status_stale_everywhere`.
- [x] **`src/` is linted for real bugs in CI.** Done 2026-11-07: the step selects the real-bug classes (`F821,F811,F823,F632,F7,B023,B006,E9`), not the whole `F` family. `F` found 85 findings, of which 75 are style: 59 unused imports, 10 unused variables, 6 f-strings without placeholders. They stay out of the gate. The 11 bug-class findings are fixed. Three of them crashed reachable paths, each with a test that failed with `NameError` first: `tests/test_undefined_names_reachable.py` (calibrate without a gold file; `scholar-verify verbatim-claims`) and `tests/console/test_screening_read_api.py::test_ui_audit_feed_skips_an_unparseable_journal_line` (one bad journal line made the audit feed a 500). Originally planned as: `ci.yml` lint step adds `uv run ruff check src/ --select F,B023,B006,E9`; the eight findings fixed (`screening/report.py:51-52`, `scholar_verify/cli.py:247,251`, `console/api/screening.py:1206`, `inception/grounded.py:253`, `integrations/latex_typst.py:97`). Evidence: the CI run green.
- [ ] **Job spawns are contained.** `-P` added to the `-m` argv in `console/runtimes/actions.py`; `job_runner.py` passes an `env` without `NEXUS_CONSOLE_TOKEN`; `--` before `{q}` in the search action. Tests `tests/console/test_job_runner.py::test_jobs_do_not_import_from_the_workspace`, `::test_jobs_do_not_inherit_the_console_token`.
- [ ] **The version moves.** `pyproject.toml` version from the tag (`hatch-vcs`) or bumped to `1.1.0b1` with `release.yml` deriving the wheel and `.mcpb` names from it; `nexus-scholar --version` prints it; the UI footer shows it. Test `tests/test_build_mcpb.py` reads the version from the project, not a literal.

### E. Beta mechanics (docs only)

- [ ] **`docs/beta/README.md`:** who it is for, install in four commands, the one-page known limits (single reviewer, no full text, the terminal approval code, RIS only), how to report a problem (email plus the workspace's `audit/journal.jsonl` and `literature/screening/MANIFEST.json`; nothing else leaves the machine), and the version to quote.
- [ ] **Five testers named** by the researcher, each with their own RIS exports; the Workspaces screen's default root is confirmed on Windows and macOS by one tester each (recorded here, not in CI).
- [ ] **Gate:** `tsc`, vitest, `next build`, Playwright (both themes); the Python PR gate once on the final executable commit; `generate_contract_baseline.py --check`; a fresh wheel install run by the researcher through Import → Prepare → Triage (20 records by keyboard) → Publish → Export, timed, with the keypress count noted here.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| review U-1 (Prepare batch size ignored) | `test_prepare_honours_batch_size` | | |
| review U-3 (published workspace shown "in progress") | `workspaces.status.test.tsx` | | |
| review U-2 / S-P1-1 (methods paragraph repeats; reveal sentence under `show`) | `test_methods_api.py` three tests above | | |
| review U-4 / S-P1-3 (bare reason codes; reason not tied to checklist) | `triage.reason-from-checklist.test.tsx`, `REASON_CODE_INCONSISTENT` | | |
| review U-5 (seven answers per record) | `triage.decisive.test.tsx`, `triage.advance-on-decide.test.tsx` | | |
| review U-6, U-7 (undo refuses; dead all-decided screen) | `triage.undo-hidden.test.tsx`, `triage.all-decided.test.tsx` | | |
| review T-P1-1 (status ignores decisions after publish) | `test_a_decision_after_publish_makes_the_status_stale_everywhere` | | |
| review T-P1-3 (undefined names, unlinted `src/`) | CI lint step | | |
| review T-P1-4 (job spawn imports from the workspace; token inherited) | `test_job_runner.py` two tests | | |
| review T-P1-6 (version frozen at 1.0.0) | `test_build_mcpb.py` version read | | |

## Decisions (written at start, 2026-11-07, `docs/decisions.md`)
- 2026-11-07 — Details on demand
- 2026-11-07 — Answer until decisive
- 2026-11-07 — Advance on decide, as a workspace setting
- 2026-11-07 — Published means current
- 2026-11-07 — The beta's parked list (with the researcher's order and the tag-after-version rule)

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |

## Deferred
- Everything under "Out" above. Each has its review id; none is forgotten, none blocks a tester.
- Review T-P2 items (atomic writes for settings and operator context, `os.replace` retry, `/healthz` path, argument injection beyond `--`, coverage, dead routes): a follow-up hardening milestone after the first tester round.

## Start checklist (for `/milestone M6-beta`)
1. M5b merged to `main`; `git status --short` clean; `git fetch origin main`; `git switch -c dev/m6/beta-ux origin/main`.
2. Add the plan §6 row and move this file's Status to IN PROGRESS.
3. Decisions first (the five above), then spec amendments to FINAL (`ux-spec-writer`), then section C and D engine work with their failing tests, then A and B UI work, then E.
4. `/gate inner` after each executable edit; `/gate checkpoint` per DoD item; `/ship M6-beta`.
