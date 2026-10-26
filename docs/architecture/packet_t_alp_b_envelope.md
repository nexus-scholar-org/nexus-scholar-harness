# Task packet — T-ALP-B: envelope and refusal registry

**Status:** specification frozen 2026-10-26; implementation pending
**Owner surface:** harness
**Governing spec:** `specs/agent-layer-portability/02_envelope_and_refusals.md` (orchestrator-owned, including the `PROVIDER_TRANSIENT` amendment of 2026-10-26)
**Delivery lane:** `STANDARD`

## 1. Objective

Give every role boundary the same transport shape, so a consumer can verify what happened to a request without parsing prose or trusting a role's word:

1. `Envelope@1` — a pydantic model plus JSON schema, covering status, coverage, refusal, input/parent hashes, and adapter-stamped provenance.
2. `scholar_harness.contracts.envelope` with `validate`, `diff`, `verify_parents`.
3. A refusal registry as a frozen enum plus generated docs.
4. Golden fixtures for the produced statuses, with a negative-test matrix.

**The envelope is transport, not science.** It says what happened to a request. It never adds fields to, reinterprets, or downgrades a Contract v1 payload. A screening verdict of `EXCLUDE` is payload; `PENDING` is payload; envelope `status` describes whether the role did its job.

## 2. Scope

**Allowed paths**

- `src/scholar_harness/contracts/**` (envelope module, registry, canonical serialisation reuse)
- `src/scholar_harness/contracts/schemas/**` (envelope JSON schema only)
- `tests/**` (envelope conformance, invariant matrix, fixtures)
- `tests/conformance/fixtures/**` (envelope fixtures only)
- `docs/architecture/packet_t_alp_b_envelope.md` (this file)
- `docs/architecture/decision_phase_b_envelope_2026-10-26.md` (new decision record)
- `docs/architecture/refusals.md` (generated registry table)

**Forbidden paths**

- `tools/**` — no kit source, no pin change
- `workspaces/**`
- `docs/architecture/contract_v1_baseline.md` / `.json` — the frozen payloads must be byte-identical after this packet (criterion 6); regeneration is forbidden
- `specs/**` — normative input, orchestrator-owned
- `.agents/**`, `.opencode/**`, `roles/**` — Phase A artifacts; the registry cross-checks against them read-only
- `src/scholar_harness/cli.py`, `orchestrator.py`, `agent_screen.py` — no runtime wiring in this packet

**Explicitly deferred (recorded here so scope is not invented later):** "orchestrator emits envelopes for dispatched packets; roles return them" is wired by Phase E's `CapabilityAdapter` (`RunRequest`/`Envelope`). B delivers the library and CLI those adapters call. This follows the non-goal in the spec's README (§5, no orchestration primitives in any phase) — not an ordering shortcut.

## 3. Acceptance criteria

1. Every invariant in `02` §3 — including the `PROVIDER_TRANSIENT` invariant — is a test.
2. `envelope_id` is stable across runs with identical inputs and payload; changes when any immutable part changes.
3. Timing fields (`created_at`, `duration_ms`, `provenance.adapter*`) do not affect either hash.
4. A `BLOCKED_INPUT` carrying a payload is rejected.
5. An unknown status string is rejected with a named error.
6. Frozen Contract v1 schemas and goldens are byte-identical before and after.
7. The refusal registry is closed: every code known to the validator appears in the generated docs table, and no emitted code is absent from the enum.
8. `PROVIDER_TRANSIENT` semantics hold: retryable, no human action, no payload, retried by the adapter — never by the role; the docs state the policy in `02` §3.

## 4. Negative cases

Minimum matrix from `02` §8, plus:

- `status: OK` with `output: null` — reject.
- `status: BLOCKED_INPUT` with a payload — reject.
- `status: PARTIAL` with `coverage.produced == coverage.expected` — reject.
- `status: PARTIAL` without a refusal — reject.
- `status: PROVIDER_TRANSIENT` with a payload, or with `retryable: false`, or with `human_action_required: true` — reject each.
- `status: OK` without `coverage` — reject.
- `refusal` present with a non-refusal status — reject.
- Unknown refusal code — reject.
- Mutated parent hash at the consumer — `PARENT_HASH_MISMATCH`, not a silent re-bind.
- Envelope carrying a payload field that a Contract v1 schema does not define — the payload schema validation fails, and the envelope does not rescue it.

## 5. Validation commands

```
uv run python -m scholar_harness.contracts.envelope validate <fixture>
uv run python -m scholar_harness.contracts.envelope diff <a> <b>
uv run pytest tests/conformance/test_envelope.py -o addopts="" -q
uv run pytest tests/ -k envelope -q
uv run python scripts/generate_contract_baseline.py --check
uv run python scripts/check_context_policy.py --check
uv run ruff check scripts/ src/ tests/conformance/
```

## 6. Toolkit sync and workspace audit

- No `tools/<kit>/` change is in scope; a pin change or vendored re-sync would be out of packet. Canonical-repo obligation absent ⇒ none can be violated.
- No workspace is named or mutated, so no `audit/journal.jsonl` event is owed.

## 7. Review protocol

Two independent gates on the implementation: a read-only reviewer (invariants, hashing determinism, scope), and a tester running the gates plus adversarial probes (mutated-parent consumption, timing-field perturbation, envelope-with-contraband-payload). Review findings are narrowed into repair packets as in Phase A; the reviewer decides blocking vs `CARRY_TO_PHASE_B/C`.

## 8. Review history

| Cycle | Verdict | Principal finding | Resolution |
|---|---|---|---|
| 1 (implementation) | pending review | — | First submission: `Envelope@1` model + module API (`validate`/`verify_parents`/`diff`/`envelope_id`/`output_sha256`), closed refusal registry with generated docs, seven golden fixtures, §3-invariant tests, §8 negative matrix, role-record cross-checks. Judgement calls recorded in `decision_phase_b_envelope_2026-10-26.md` (D1–D10), notably: envelope module lives as a *package* because the frozen baseline locks `contracts/*.py` with a non-recursive glob (D1); the PARTIAL/refusal spec tension resolved in favour of §3 (D2); `envelope_id` is timestamp-free contrary to the cosmetic §2 example (D3); parent disk verification hashes raw file bytes (D4). |
| 2 (adversarial tester) | repaired | Near-miss `output.schema` names (`ScreeningDecisions@2`, `screeningdecisions@1`, …) silently bypassed all payload validation when they missed `PAYLOAD_MODELS` exactly — fail-open on a typo. | Role records are now the schema-name authority: `output.schema`/`inputs[*].schema` are cross-checked against the role record's declared schemas at §8 step 5, each mismatch a named `INVALID_OUTPUT` refusal naming claimed and declared names; declared-but-unregistered names refused too (D11). Tests 1–4 of the repair packet added; fixtures, Phase A artifacts, spec untouched. |
| 2 (reviewer, F1) | repaired | From an unrelated CWD, `validate` with no `--roles-dir` and no discoverable `roles/` silently skipped every role-record cross-check (incl. D11 schema-name authority) and printed `{"result":"accepted"}` exit 0 for a `ScreeningDecisions@2` envelope. | The CLI now fails loud: discovery-less validate refuses with `BLOCKED_INPUT` on stderr naming `--roles-dir`, exit 1; the library's `roles_dir=None` D11 contract itself is unchanged (D11a in the decision record); one CLI test added. |
