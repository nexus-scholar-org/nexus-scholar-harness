# H-input-limits Input hardening (F5, F6, F7)
Branch: dev/hardening/input-limits · Lane: **STANDARD** (`test_gate_policy.md` §lanes: a bounded behaviour change owned by this repository; the three fixes add refusal codes and limits on request bodies, change no Contract v1 schema, artifact identity or snapshot, and `generate_contract_baseline.py --check` must pass at every commit; escalate to RELEASE if the diff ever touches `src/scholar_harness/contracts/`) · Status: IN PROGRESS · Started: 2026-11-12

Scope is item 4 of the hardening plan in
[`three-phase-hardening-2026-11-10.md`](../../assessment/three-phase-hardening-2026-11-10.md) §4:
one validation handler (F5), draft limits (F6), event limits (F7). The plan §6
row "Three-phase review items" lists them without a milestone id; this record
gives them one. Out of scope: `src/scholar_harness/corpus_accept.py` and the
screening round/snapshot code (owned by the concurrent M3g-citation-chasing
session), F2–F4, F8–F10.

## Definition of done
- [x] F5: every console body that pydantic refuses answers 422 with `{"detail": {"code": "BODY_INVALID", "message", "details"}}`; one `RequestValidationError` handler in `console/serve.py`; the code is registered in `console/refusals.py` and the screening API contract §7 (`tests/console/test_console_refusals.py`, `tests/console/test_console_serve.py`).
- [x] F5: the Research UI shows a readable card for `BODY_INVALID` (`apps/research-ui/lib/screening-states.ts`, its test).
- [x] F6: the draft shape has size limits (text fields and list counts); a draft over them is refused `DRAFT_TOO_LARGE` (422), registered in the refusal set and the contract §7; the limits are recorded in `docs/decisions.md` (`tests/console/test_inception_api.py`).
- [x] F7: a decision event with `decided_at` more than 5 minutes after the engine's `received_at` is refused `PROVENANCE_MISSING`; a `device` that contradicts the token scope is refused; `note` is capped at 2 000 characters (`tests/test_screening_events.py`, `tests/console/test_screening_api_v1.py`).
- [x] Each finding re-verified by `phase-auditor` before the fix; failing test written first.
- [ ] `/gate pr` once on the final commit, `generate_contract_baseline.py --check`, `milestone-reviewer` APPROVE.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| F5 | `tests/console/test_console_refusals.py::test_a_body_pydantic_refuses_answers_the_refusal_envelope`, `::test_an_unknown_body_field_is_body_invalid` | yes at `6c66d24b`: `detail` is a list (`TypeError` on `["code"]`); the auditor saw `{"detail": [{"type": "dict_type", ..., "input": 5}]}` | yes |
| F6 | `tests/console/test_inception_api.py::test_an_oversized_draft_is_refused_and_not_saved` (12 cases), `::test_a_draft_at_its_limits_is_accepted`, `::test_a_too_large_and_malformed_draft_is_reported_as_too_large` | yes at `6c66d24b`: the auditor got 201 and a 26 244-byte `draft.json` for a 20 000-character topic with 500 questions; the new tests fail at collection (no limit constants) | yes |
| F7 | `tests/test_screening_events.py::test_f7_future_decisions_foreign_devices_and_long_notes_are_refused` (7 cases), `::test_f7_values_at_the_limits_are_accepted`; `tests/console/test_screening_api_v1.py::test_f7_a_phone_device_under_a_desktop_token_is_refused` | yes at `6c66d24b`: the auditor got `accepted` for a 2031 `decided_at`, a phone device on a desktop token and a 50 000-character note; the new tests fail at collection (no `MAX_NOTE_CHARS`) | yes |

## Decisions
- [2026-11-12 — Input limits for drafts and decision events; one envelope for validation errors](../../decisions.md) (proposed; the researcher confirms at the PR).
- The limits sit on the draft shape in `inception/steps.py` (every route parses it), not on `DraftBody` as the review suggested; `DraftBody` only wraps a dict.
- F7 adds no refusal code: a mismatched `device` and an oversized `note` are `INVALID_OUTPUT`, the code already used for a wrong `device` value; the future `decided_at` is `PROVENANCE_MISSING` as the review asked. The device is refused, not rewritten from the scope.
- Three existing tests sent a phone device under a desktop token to stage a second-device conflict; they now send it under the phone token. The events test helper's engine clock follows the latest `decided_at` it sends (it was fixed at 10:00:05, two hours before some fixtures' decisions).
- Old drafts are not checked on load (`GET /inception/drafts/{id}`), only when next saved, stepped or previewed, so a resume still works.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner | working tree on `6c66d24b` | `select_test_gate.py --changed main --stage inner`: `git diff --check`, screening tests, `tests/console -n auto`, `tests/inception`, typecheck, `vitest related`, the five owning files | all pass: 136, 407 (1 pre-existing skip), 112, 157 passed; vitest 28 files, 334 tests; typecheck clean | ~5 min |
| inner | working tree | `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9`; `ruff check scripts/`; `generate_contract_baseline.py --check` | all clean; baseline current | <1 min |

## Deferred
