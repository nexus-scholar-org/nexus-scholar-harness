# M1a Screening backend
Branch: dev/m1a/screening-backend · Lane: **RELEASE** (plan §6: artifact
identity and acceptance semantics; it also changes public HTTP and MCP
behaviour) · Status: IN PROGRESS · Started: 2026-11-04

Plan: [`production-plan.md`](../production-plan.md) §6 row M1a, §1.2 findings,
§4 decision model. Contract: [`screening-api-contract.md`](../../architecture/screening-api-contract.md)
(ACCEPTED 2026-11-04). Agent design: [`agent-system.md`](../../architecture/agent-system.md) §2–§4.

## Definition of done

Carried over from M0
- [x] **M0 CI matrix result** recorded in `M0.md` (PR #185: 12/12 green after re-running two macOS jobs that never got a runner).

Assessment findings (phase-auditor first, reproducing test before the fix)
- [ ] **CON-10**: dual mode starts on any `*_screener2.json`; unadjudicated disagreement refused.
- [ ] **CON-11**: no missing decision becomes INCLUDE; no fabricated confidence, method or 1970 time; the console writer stamps `method: HUMAN`, `screener_id` and `decided_at` on every row.
- [ ] **CON-13** (guarded outside the Contract v1 lock, researcher 2026-11-04): the harness refuses to submit a `screening_decisions` artifact that does not have exactly one `screening_batch` parent, before calling the frozen acceptance gate. The gap in `contracts/acceptance.py` and `chain.py` stays recorded for Contract v1.1.
- [ ] **CON-14/15**: the dual path runs the unresolved, coverage and duplicate gates; its artifact id derives from decision ids.
- [ ] **CON-02/03** (plan §1.2 fix): approval covers exactly one batch generation and never seals another batch's bytes; the approver is recorded as an unauthenticated local attestation, not an identity. Authentication waits for the sync tier.
- [ ] **SRCH-16/17/35**: no imputed votes; uncertainty goes to the human; `ScreeningDecision` records method, model and prompt hash.
- [ ] **AGT-16/18/19**: MCP screening writes proposals only; κ refuses fewer than two raters; state-changing MCP tools journal.

Decision events (contract §3)
- [ ] **Event store**: append-only `literature/screening/events/<screener_id>.jsonl` behind an OS file lock (§9.2); intake results `accepted`, `duplicate`, `conflict`, `refused`.
- [ ] **Projection** to `batch_NNN_decisions.json`: deterministic, excludes conflicted studies; the existing `decision_id` recipe is fed the winning event's immutable fields.
- [ ] **Contract test 1**: replaying the same event set gives byte-identical decisions files and the approval stays valid (negative test).
- [ ] **Contract tests 2, 3, 5, 8**: duplicate vs `IDEMPOTENCY_CONFLICT`; conflict excluded and collect refuses `BATCH_INCOMPLETE`; EXCLUDE without reason → `REASON_CODE_INVALID`; one journal row per accepted batch of events.

Unclear
- [ ] **MAYBE passes finalize** as "Unclear → full text" and is counted as `unclear_to_full_text` (contract test 6); decision entry for the PRISMA rule (researcher, 2026-11-04: forwarded to full text, its own line); `check_golden_workspace.py` follows.

Proposals (agent-system §2–§4)
- [ ] **Proposal store**: append-only, full provenance (model, prompt hash, input hash, checks, usage); plain-code validators; failures become Unclear, never Exclude; journal events.
- [ ] **MCP**: read tools (queue, record) and `submit_proposal`; nothing over MCP writes decisions or published outputs.

Screening API (contract §4, M1a rows)
- [ ] `GET /summary`, `GET /queue`, `GET /records/{id}`, `GET /records/{id}/proposal` (`PROPOSAL_HIDDEN`, contract test 4).
- [ ] `POST /decisions/events` (≤ 200), `GET /decisions/conflicts`, `POST /decisions/conflicts/{id}/resolve`.
- [ ] `GET`/`PUT /settings`, `POST /prepare` (`SNAPSHOT_NOT_ACCEPTED`), `GET /prisma/preview`, `POST /actions/pairing/begin`.
- [ ] **Token scopes**: a phone-scoped token is refused on prepare, proposal runs and publish (`TOKEN_SCOPE_REFUSED`, contract test 7).
- [ ] **Refusal codes**: the proposed codes in contract §7 are added to the registry.
- [ ] **Shared fixtures** `tests/fixtures/screening_api/*.json` and `tests/console/test_screening_api_contract.py`.

End to end
- [ ] **30-record fixture workspace screened end to end through the API** with HUMAN provenance on every decision; `scripts/check_golden_workspace.py` passes on it.
- [ ] **Contract v1**: `generate_contract_baseline.py --check` passes throughout; any lock-set change stops as `BLOCKED_BASELINE_DRIFT`.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |

## Decisions
- [Unclear forwarded to full text](../../decisions.md) (2026-11-04)
- [CON-13 guarded outside the Contract v1 lock](../../decisions.md) (2026-11-04)

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |

## Parallel work
- **AI reference screening** of 200 `uav-crop-weed-v03` records, recorded as `method: LLM` (screener `claude-reference-v1`), blind to the v03 agent labels. It is the provisional prompt-gate eval set for M1b, named "AI reference labels, not human-validated". The researcher asked for it on 2026-11-04 and declined to mark it as human.

## Deferred
None yet.
