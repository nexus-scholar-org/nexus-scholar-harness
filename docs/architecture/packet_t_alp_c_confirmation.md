# Task packet — T-ALP-C: human confirmation (`HumanConfirmation@1`)

**Status:** delivered 2026-10-28; specification frozen 2026-10-26
**Owner surface:** harness
**Governing spec:** `specs/agent-layer-portability/06_human_confirmation.md` (new, orchestrator-owned) + the Phase C section of `05_migration_plan.md` §3
**Delivery lane:** `STANDARD`
**Phases shipped:** A (`#149`), B (`#150`, `3bf3bb4`)

## 0. Delivery record (2026-10-28)

- `scholar_harness.contracts.confirmation` (`model`, `api`, `schema`, `cli`)
  with `validate`, `verify_artifacts`, `enforce_coverage`, `export_gate` and
  `confirmation_fingerprint`; `HumanConfirmation@1` registered in the envelope
  payload map so Phase B D11 role/schema checks cover it.
- `scripts/confirm_screening.py` (`--interactive`, `--from-queue`,
  `--retrospective`), write-time hash re-verification, coverage-first refusals,
  audit event.
- `scholar-harness export --claim-confirmed` export gate only (no other CLI
  change).
- `roles/human-confirm.json` + prompt body, generated frontmatter/permissions.
- Docs: [`confirmation.md`](./confirmation.md),
  [`decision_phase_c_confirmation_2026-10-26.md`](./decision_phase_c_confirmation_2026-10-26.md).
- Gates: confirmation/envelope suites, role-generation suite, contract
  baseline `--check`, context-policy `--check`, scoped ruff.

## 1. Objective

Make "who decided this?" answerable with a person, a timestamp, and the exact artifact hashes they saw:

1. `HumanConfirmation@1` — a payload binding a named customer reviewer to the decision artifacts they reviewed, with honest override/deferral rows.
2. `scholar_harness.contracts.confirmation` — `validate(record, *, verify_artifacts=False)`, `verify_artifacts(record, root)` — named refusals throughout, envelope-package conventions.
3. `scripts/confirm_screening.py` — interactive or `--from-queue` producer; verifies every artifact hash at write time; refuses `BLOCKED_INPUT` naming the missing paths if coverage is incomplete.
4. **Export gate:** an export claiming "confirmed" refuses `REFUSED` unless a valid, verifying, non-retrospective `HUMAN_CONFIRMATION.json` exists at export time.

## 2. Scope

**Allowed paths**

- `src/scholar_harness/contracts/confirmation/**` (new module)
- `src/scholar_harness/contracts/schemas/confirmation/**` (JSON schema)
- `src/scholar_harness/cli.py` — export gate ONLY (scoped, named below; this is the first packet touching it since Phase B forbade it)
- `scripts/confirm_screening.py` (new)
- `tests/**` (confirmation tests, fixtures)
- `tests/conformance/fixtures/confirmation/**`
- `docs/architecture/packet_t_alp_c_confirmation.md` (this file)
- `docs/architecture/decision_phase_c_confirmation_2026-10-26.md` (new decision record)
- `docs/architecture/confirmation.md` (short generated-or-static doc; may be static)

**Forbidden paths**

- `tools/**`, `workspaces/**`, `roles/**` EXCEPT the one deliverable `roles/human-confirm.json` (see §1 of the plan: `tools: [read]`, `network: deny`, `bash: deny`) — if roles are touched, run `scripts/generate_agent_roles.py --check` and the Phase A test; that is the only roles change of this packet
- `specs/**` (normative input), `.opencode/**` generated files other than what the roles generator above legitimately regenerates for the new role
- `docs/architecture/contract_v1_baseline.md/.json` — frozen payloads stay byte-identical
- Envelope module (`src/scholar_harness/contracts/envelope/**`) — consumption via import only; the refusal registry enum stays frozen (confirmation reuses existing codes only)
- `src/scholar_harness/orchestrator.py`, `agent_screen.py` — no wiring

## 3. Acceptance criteria

1. A confirmation cannot silently bind to an artifact whose bytes changed after the reviewer saw it — verify-time + export-time refusal `PARENT_HASH_MISMATCH`, never a warning (spec §3.3).
2. `summary.considered == len(decisions)`, `confirmed+changed+deferred == considered` — validator-enforced.
3. Every `changed: true` verdict carries a non-empty `rationale`; validator refuses otherwise.
4. A workspace with no confirmation artifact cannot be exported as "confirmed" — the export CLI refuses `REFUSED` with machine-readable detail.
5. Retrospective records never satisfy the export gate; labelled explicitly.
6. Frozen Contract v1 schemas/goldens byte-identical (`generate_contract_baseline.py --check` green); refusal registry unchanged (tests prove enum parity with docs).
7. Every spec §3/§6 invariant is a test; envelope conformance (Phase B, 103 tests) untouched and green.
8. `pydantic` shapes so `Envelope@1` can wrap a confirmation as payload (validated only via the payload-schema mechanism; a schema-name near-miss must name-refuse as in D11).

## 4. Negative cases

Minimum matrix = spec §6 items 1–8 verbatim. Production notes:

- Producer probes: attempts to sign while a decision artifact is added *after* hashing but *before* write → write-time re-verify refuses.
- Export probe: export → mutate a decision file → export again → `PARENT_HASH_MISMATCH` (spec §6 item 8).
- Export probe: proof that CLI export with no confirmation artifact gives named refusal, exit 1, and does NOT alter the export bundle.

## 5. Validation commands

```
uv run python scripts/confirm_screening.py <fixture-workspace> --help
uv run pytest tests/conformance/test_confirmation.py -o addopts="" -q
uv run pytest tests/ -k "confirmation or envelope" -o addopts="" -q
uv run pytest tests/conformance/test_agent_role_permissions.py -o addopts="" -q  # only if a role record was touched
uv run python scripts/generate_contract_baseline.py --check
uv run python scripts/generate_agent_roles.py --check                             # only if roles touched
uv run python scripts/check_context_policy.py --check
uv run ruff check scripts/ src/scholar_harness/contracts/confirmation/ tests/conformance/test_confirmation.py
```

Note on `cli.py`: ruff findings exist there pre-packet (AGENTS-documented, out of CI scope); do not fix unrelated ones, and the packet's own lint gate is scoped to the files it touches.

## 6. Toolkit sync and workspace audit

- No `tools/<kit>/` change in scope; no pin change; canonical-repo obligation absent.
- The CLI export gate is the only runtime wiring; keep it small and mirror Phase B's CLI refusal-JSON/exit conventions.
- No research workspace is named or mutated, so no `audit/journal.jsonl` event owed from this packet. (The *tool* `confirm_screening.py` must itself write journal events — that functionality is part of its producer contract and tested on fixture workspaces.)

## 7. Review protocol

Independent reviewer + independent tester, same as B (packet §7 of `packet_t_alp_b_envelope.md`). The reviewer explicitly re-checks D11/Phase-B closure: the confirmation must not weaken or re-interpret the envelope contract, and the export gate must be fail-loud in any CWD (carry-forward from B cycle-3 F1).
