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
- [ ] F2: `bound_to_current_protocol` is false after a semantic protocol edit (non-vacuous: no winners is not "bound"; a batch prepared under another protocol fails it); `/summary` and `/queue` carry `protocol_changed`; the choice is recorded in `docs/decisions.md` (`tests/console/test_screening_api_v1.py`).
- [ ] F2: Screening Home says the protocol changed after screening started instead of an empty queue (en/fr/ar copy, vitest).
- [ ] F2: only the current round's batches count (M3g rounds): an archived round prepared under an earlier protocol does not raise the flag.
- [ ] F3: a run records `protocol_fingerprint` and the search it compiled (query, years, language, cap, databases) in `legs.json`; `GET /discovery/runs` items and `GET /discovery/handoff` carry `protocol_changed` before any accept (`tests/console/test_discovery_api.py`).
- [ ] F3: the accept refusal `PROTOCOL_CHANGED_SINCE_RUN` also covers a changed database list, language or cap; a criteria-only edit is flagged but does not refuse (decision recorded).
- [ ] F3: the Hand-off screen warns before the accept click (en/fr/ar copy, vitest).
- [ ] F4: after a browser harvest `GET /screening/corpus` reports `databases` from the run's legs and `preview` from `deduped.json`, before and after the accept; a round-2 (chase) snapshot is checked (`tests/console/test_corpus_api.py`).
- [ ] Each finding re-verified by `phase-auditor` before the fix; failing test written first.
- [ ] Closure gate on the final commit, `generate_contract_baseline.py --check`, `milestone-reviewer` APPROVE.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |

## Decisions

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| baseline | `fd3cc329` | `generate_contract_baseline.py --check` | current | <1 min |

## Deferred
