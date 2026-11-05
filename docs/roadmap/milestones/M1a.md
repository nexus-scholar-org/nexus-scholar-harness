# M1a Screening backend
Branch: dev/m1a/screening-backend · Lane: **RELEASE** (plan §6: artifact
identity and acceptance semantics; it also changes public HTTP and MCP
behaviour) · Status: MERGED (PR #186, `0179157`, 2026-11-05) · Started: 2026-11-04

Plan: [`production-plan.md`](../production-plan.md) §6 row M1a, §1.2 findings,
§4 decision model. Contract: [`screening-api-contract.md`](../../architecture/screening-api-contract.md)
(ACCEPTED 2026-11-04). Agent design: [`agent-system.md`](../../architecture/agent-system.md) §2–§4.

## Definition of done

Carried over from M0
- [x] **M0 CI matrix result** recorded in `M0.md` (PR #185: 12/12 green after re-running two macOS jobs that never got a runner).

Assessment findings (phase-auditor first, reproducing test before the fix)
- [x] **CON-10**: dual mode starts on any `*_screener2.json`; unadjudicated disagreement refused.
- [x] **CON-11**: no missing decision becomes INCLUDE; no fabricated confidence, method or 1970 time; the console writer stamps `method: HUMAN`, `screener_id` and `decided_at` on every row.
- [x] **CON-13** (guarded outside the Contract v1 lock, researcher 2026-11-04): the harness refuses to submit a `screening_decisions` artifact that does not have exactly one `screening_batch` parent, before calling the frozen acceptance gate. The gap in `contracts/acceptance.py` and `chain.py` stays recorded for Contract v1.1.
- [x] **CON-14/15**: the dual path runs the unresolved, coverage and duplicate gates; its artifact id derives from decision ids.
- [x] **CON-02/03** (plan §1.2 fix): approval covers exactly one batch generation and never seals another batch's bytes; the approver is recorded as an unauthenticated local attestation, not an identity. Authentication waits for the sync tier.
- [x] **SRCH-16/17/35**: no imputed votes; uncertainty goes to the human; `ScreeningDecision` records method, model and prompt hash.
- [x] **AGT-16/18/19**: MCP screening writes proposals only; κ refuses fewer than two raters; state-changing MCP tools journal.

Decision events (contract §3)
- [x] **Event store**: append-only `literature/screening/events/<screener_id>.jsonl` behind an OS file lock (§9.2); intake results `accepted`, `duplicate`, `conflict`, `refused`.
- [x] **Projection** to `batch_NNN_decisions.json`: deterministic, excludes conflicted studies; the existing `decision_id` recipe is fed the winning event's immutable fields.
- [x] **Contract test 1**: replaying the same event set gives byte-identical decisions files and the approval stays valid (negative test).
- [x] **Contract tests 2, 3, 5, 8**: duplicate vs `IDEMPOTENCY_CONFLICT`; conflict excluded and collect refuses `BATCH_INCOMPLETE`; EXCLUDE without reason → `REASON_CODE_INVALID`; one journal row per accepted batch of events.

Unclear
- [x] **MAYBE passes finalize** as "Unclear → full text" and is counted as `unclear_to_full_text` (contract test 6); decision entry for the PRISMA rule (researcher, 2026-11-04: forwarded to full text, its own line); `check_golden_workspace.py` follows.

Proposals (agent-system §2–§4)
- [x] **Proposal store**: append-only, full provenance (model, prompt hash, input hash, checks, usage); plain-code validators; failures become Unclear, never Exclude; journal events.
- [x] **MCP**: read tools (queue, record) and `submit_proposal`; nothing over MCP writes decisions or published outputs.

Screening API (contract §4, M1a rows)
- [x] `GET /summary`, `GET /queue`, `GET /records/{id}`, `GET /records/{id}/proposal` (`PROPOSAL_HIDDEN`, contract test 4).
- [x] `POST /decisions/events` (≤ 200), `GET /decisions/conflicts`, `POST /decisions/conflicts/{id}/resolve`.
- [x] `GET`/`PUT /settings`, `POST /prepare` (`SNAPSHOT_NOT_ACCEPTED`), `GET /prisma/preview`.
- [x] `POST /actions/pairing/begin` reaches a staged challenge for an event-decided batch, with the code printed on the console terminal only (decision 2026-11-04).
- [x] **Token scopes**: a phone-scoped token is refused on prepare, proposal runs and publish (`TOKEN_SCOPE_REFUSED`, contract test 7).
- [x] **Refusal codes**: the proposed codes in contract §7 form the console refusal set (`console/refusals.py`), kept in step with the contract by `tests/console/test_console_refusals.py`. The agent-role registry (`Envelope@1`) is a different vocabulary and is unchanged.
- [x] **Shared fixtures** `tests/fixtures/screening_api/*.json` and `tests/console/test_screening_api_contract.py`.

End to end
- [x] **30-record fixture workspace screened end to end through the API** with HUMAN provenance on every decision; `scripts/check_golden_workspace.py` passes on it. Test: `tests/e2e/test_golden_screening_api.py` (a copy of `golden-uav-30`, 3 batches, 30 events, per-batch approval, collect; synthetic outcomes, labelled as such).
- [x] **Contract v1**: `generate_contract_baseline.py --check` passes throughout; any lock-set change stops as `BLOCKED_BASELINE_DRIFT`.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| CON-11 | `tests/test_screening_decision_integrity.py::test_missing_provenance_refuses_instead_of_defaulting` (no decision, no method, epoch time, no reason) | 4 failed: defaulted to INCLUDE/LLM/1970/"Agent screened." | pass |
| Unclear | `test_maybe_passes_finalize_as_unclear_to_full_text` | refused `UNRESOLVED_FINALIZE_REFUSED` | pass |
| CON-03 | `tests/test_screening_events.py::test_con03_one_batch_approval_never_seals_another_batch`, `::test_con03_a_changed_batch_needs_a_fresh_approval` | approving batch 1 staged a corpus-wide publication approval | publication staged only when every batch is currently approved |
| CON-02 | `::test_event_decided_batch_approves_without_a_worker_recommendation` | approver recorded as an identity | `identity_basis: unauthenticated-local-attestation` on every review and result |
| CON-10 | `tests/test_screening_decision_integrity.py::test_con10_a_second_screener_starts_dual_mode_without_an_adjudication_file`, `::test_con10_a_disagreement_without_adjudication_refuses` | screener 2 ignored without an adjudication file | dual mode; disagreement refused |
| CON-13 (guard) | `::test_con13_a_decisions_artifact_needs_exactly_one_batch_parent`, `::test_con13_every_decisions_submission_goes_through_the_guard` | no harness check | refused before the frozen gate |
| CON-14 | `::test_con14_a_dual_conflict_is_never_finalized`, `::test_con14_dual_duplicate_rows_refuse`, `::test_con14_both_unclear_is_an_agreement_forwarded_to_full_text` | dual path skipped the gates | coverage, duplicate and CONFLICT gates per screener |
| CON-15 | `::test_con15_dual_artifact_id_depends_on_the_decisions` | id from batch_id alone | id includes the decision ids |
| SRCH-16 | `tests/kits/search/test_screening_provenance.py::test_srch16_llm_uncertainty_goes_to_a_human`, `::test_srch16_no_invented_confidence_or_reason` | missing → INCLUDE, other → EXCLUDE, 0.75, "LLM screened." | MAYBE; no invented values |
| SRCH-17 | `::test_srch17_a_missing_vote_is_not_an_exclude`, `::test_srch17_an_unadjudicated_tie_is_a_conflict_not_an_exclude` | missing vote and open tie → EXCLUDE | CONFLICT, listed as incomplete |
| SRCH-35 | `::test_srch35_decision_carries_provenance_fields`, `::test_srch35_heuristic_decisions_are_labelled` | no method/model/prompt fields | `method`, `screener_id`, `model_id`, `prompt_version` |
| AGT-16 | `tests/mcp/test_mcp_screening_proposals.py::test_agt16_19_mcp_screening_writes_proposals_only_and_journals` | `nexus_screen*` wrote included/excluded/PRISMA | `screening_proposals.json` only |
| AGT-18 | `tests/kits/search/test_screening_provenance.py::test_agt18_kappa_is_undefined_below_two_raters` | κ = 1.0 with one rater | `None` |
| AGT-19 | `tests/mcp/test_mcp_screening_proposals.py::test_agt19_*` | no MCP tool journaled | writer tools journal inside a workspace, only on success |

## Decisions
- [Approval: terminal-only code; event-decided batches need no worker step](../../decisions.md) (2026-11-04)
- [The v03 screening labels are human-confirmed](../../decisions.md) (2026-11-04)
- [Unclear forwarded to full text](../../decisions.md) (2026-11-04)
- [CON-13 guarded outside the Contract v1 lock](../../decisions.md) (2026-11-04)

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| checkpoint | 5762c48 + events/API working tree | full suite once (`uv run pytest -n auto`); `ruff check scripts/`; contract `--check` | 4153 passed, 14 skipped; clean; baseline current | 280 s |
| checkpoint | SRCH/AGT working tree | full suite once (`uv run pytest -n auto`); `ruff check scripts/`; contract `--check` | 4186 passed, 14 skipped; clean; baseline current | 310 s |
| pr | be447ba | selector `--changed origin/main --stage pr` (areas screening, authority, console, search, agent-mcp): `git diff --check`; `ruff check scripts/`; `sync_skills_bundle.py --check`; contract `--check`; `generate_screening_api_fixtures.py --check`; `uv run pytest -n auto` (full suite once) | clean; clean; 13 OK; baseline current; 19 current; 4193 passed, 14 skipped | 323 s |
| pr (after review) | ae8795d | same selection and commands | clean; clean; 13 OK; baseline current; 19 current; 4203 passed, 14 skipped | 357 s |
| pr (after second review) | 63b3170 | same selection and commands | clean; clean; 13 OK; baseline current; 19 current; 4206 passed, 14 skipped | 338 s |
| pr (after third review) | 5f7c4f3 | same selection and commands | clean; clean; 13 OK; baseline current; 19 current; 4207 passed, 14 skipped | 332 s |

## Raised for the researcher
- ~~Approval code over HTTP~~ and ~~approval from events~~: decided 2026-11-04 (see Decisions).

## Parallel work
- **AI reference screening** of 200 `uav-crop-weed-v03` records, recorded as `method: LLM` (screener `claude-reference-v1`), blind to the v03 labels. It was meant as a stopgap eval set; it is no longer needed for that, because the v03 labels are human-confirmed (decision 2026-11-04). It is kept only as a model-versus-human comparison. Against the confirmed labels, it included 24 of the 60 sampled includes, marked 21 Unclear and excluded 15; it never included a confirmed exclusion.

## Review

`milestone-reviewer`, 2026-11-04, first pass: **CHANGES** (10 findings). All are fixed, each with a test that failed before:

| # | Finding | Fix | Test |
| :-- | :-- | :-- | :-- |
| 1 | The proposal journal row carried the derived outcome, readable in the audit feed before a decision (blinding bypass) | the journal records only that a proposal was stored | `test_review_1_the_audit_feed_never_reveals_a_proposal_outcome` |
| 2 | Any file claiming `source: decision-events` skipped the worker step | believed only when its bytes equal the event projection | `test_review_2_a_hand_written_event_claim_does_not_skip_the_worker_step` |
| 3 | The projection ignored event bindings; a new generation reused stale events | events must match the current protocol and batch; the projection carries its binding | `test_review_3_events_bound_to_an_earlier_generation_are_not_projected` |
| 4 | reconcile and κ treated MAYBE as a non-category | MAYBE is a category; a MAYBE majority is MAYBE | `test_review_4_unclear_is_a_category_in_reconcile_and_kappa` |
| 5 | An answer without an id crashed the checks | a failed check, so the proposal is Unclear | `test_review_5_an_answer_without_an_id_is_unclear_not_a_crash` |
| 6 | MCP proposals were stored without a model or prompt hash | refused, `PROVENANCE_MISSING` | `test_review_6_a_proposal_needs_its_model_and_prompt_hash` |
| 7 | Only `OSError` rolled back an intake; a lock timeout gave a 500 | any failure rolls back; a lock timeout is `ATOMIC_COMMIT_FAILED` | `test_review_7_a_non_os_journal_failure_also_rolls_back` |
| 8 | The projection was written outside the event lock | written under the lock (`after_commit`) | covered by the API tests |
| 9 | The CON-13 guard counted parents but did not check their type | the one parent must be a `screening_batch` | `test_con13_a_decisions_artifact_needs_exactly_one_batch_parent` |
| 10 | Evidence uncommitted; reveal tracking not listed; no queue-order test | this section; Deferred below; queue-order test | `test_review_10_agent_uncertainty_orders_unclear_drafts_first` |

Second pass: **CHANGES** (finding 3 fixed only in the projection; the finding 7 fix misreported a committed event). Fixed in the next commit:

| # | Finding | Fix | Test |
| :-- | :-- | :-- | :-- |
| A | Every reader except the projection still counted events from an earlier protocol or batch: the summary showed them decided, `needs_you` was empty, the proposal was revealed, and a new decision was reported as a conflict | one helper, `current_events`, used by `_state` (console and MCP), the conflict routes, the intake conflict check and the projection | `test_review_a_decisions_of_an_earlier_protocol_count_nowhere` |
| B | The lock-timeout `except OSError` also caught a projection failure after commit, so a stored event was reported refused and a retry left the projection stale | only `LockBusy` (the lock not taken) is `ATOMIC_COMMIT_FAILED`; a projection failure leaves the results as stored; duplicates re-project | `test_review_b_a_projection_failure_after_commit_keeps_the_event_accepted`, `test_review_b_a_lock_timeout_is_atomic_commit_failed_and_stores_nothing` |
| C | The reveal-tracking deferral lived only in M1a.md | added to the plan §6 M1b row (RELEASE for that change); `false` documented as "not tracked" | — |
| follow-up | `project.json` was read outside the try in `_reviewed_bytes` | read inside it, so a missing manifest falls back to the worker step | — |

Third pass: **CHANGES** (B2: the B fix swallowed a projection failure, so after an approval a stale decisions file could be published). Fixed in the next commit:

| # | Finding | Fix | Test |
| :-- | :-- | :-- | :-- |
| B2 | A projection failure after commit was silent; after a batch approval, collect published the older file because the staged review still matched its bytes | the failure is journaled (`SCREENING_PROJECTION_FAILED`); `collect` refuses `PROJECTION_STALE` while any `decision-events` file differs from `project_batch` (the event log is the authority); `projection_is_current` is the one comparison, shared with the approval path | `test_review_b2_a_failed_projection_after_approval_blocks_collect` |
| CI | a6716c8 (PR #186) | GitHub matrix: ubuntu/windows/macos × Python 3.11/3.12, lint, plugin, manifest | 12/12 green; merged as `0179157` | — |

Fourth pass (B2 only): **APPROVE**, 2026-11-05.

## Deferred
- **Reveal tracking** (`changed_after_reveal`, the `REVEAL` audit row; contract §3.1) moves to M1b. The reveal happens when the triage screen shows a proposal after a decision, which is M1b UI work; the engine field exists and is stamped `false` until then. **Before M1b, `changed_after_reveal: false` means "not tracked", not "not changed after a reveal".** The item is in the plan §6 M1b row, with that change escalated to RELEASE.
- **Library `submit_proposal` provenance:** only the MCP tool refuses a proposal without a model or prompt hash; the library call is guarded when the M1b driver becomes its first non-MCP caller.
- **`PROJECTION_STALE` as a typed console refusal**, and journaling a failure of the `SCREENING_PROJECTION_FAILED` row itself (collect still refuses): M1b, when the UI shows it.
- **Second-screener projection:** `write_projection` writes one `batch_NNN_decisions.json` whatever the screener; the second screener is parked (plan §6), and the per-screener file comes with it.
