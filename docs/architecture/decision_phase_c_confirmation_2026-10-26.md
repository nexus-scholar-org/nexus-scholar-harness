# Decision record — Phase C human confirmation (2026-10-26)

Task packet: [`packet_t_alp_c_confirmation.md`](./packet_t_alp_c_confirmation.md).
Governing spec: `specs/agent-layer-portability/06_human_confirmation.md` and
`specs/agent-layer-portability/05_migration_plan.md` §3.

These are the calls a later reviewer cannot reconstruct from code. The
user-facing behaviour lives in [`confirmation.md`](./confirmation.md).

## D1 — the module is a *package* outside the frozen baseline glob

Same constraint as Phase B D1: `scripts/generate_contract_baseline.py` hashes
`src/scholar_harness/contracts/*.py` and `…/schemas/v1/*.json` non-recursively.
`contracts/confirmation/` and
`contracts/schemas/confirmation/confirmation.schema.json` sit outside those
globs, so no frozen payload changes and `--check` stays green. The refusal
registry enum is imported, never extended.

## D2 — payload registration and the alias-aware contraband check

`HumanConfirmation@1` is registered in `PAYLOAD_MODELS` so Phase B D11 holds for
this role too: its role record declares the output schema, so an envelope whose
payload nobody can validate is refused rather than travelling opaquely.

Registration exposed a real distinction in the contraband step. The five Phase B
payload models are *inner data* models wrapped by the envelope (`output.data`),
and none of them has a `schema` field. `HumanConfirmation` is the artifact
itself, so the record carries `"schema": "HumanConfirmation@1"` at the top of
`output.data`. The contraband check now compares the payload keys against
`model_fields` **plus declared aliases**; without that, every valid confirmation
would be refused for carrying its own `schema` key while still rejecting a
genuinely undefined field.

The strictness asymmetry is deliberate: the confirmation model is
`extra="forbid"` (closed vocabulary), whereas Contract v1 data models remain
`extra="allow"` for forward compatibility. The contraband step therefore keeps
rejecting unknown top-level keys for both, but only the confirmation model's own
validation rejects unknown nested keys.

## D3 — `validate()` runs payload validation; registration is not a role filter

`validate()` applies `_validate_payload_schema` whenever `output.schema` is a
registered name, *and* the D11 role-compatibility step refuses a
declared-but-unregistered role output. Both directions matter:

- a registered name with an invalid shape is `INVALID_OUTPUT` naming the schema
  and the field;
- a near-miss (`HumanConfirmation@2`) is `INVALID_OUTPUT` quoting the claimed
  name and the role record's declared name, exactly the D11 wording.

Phase C adds one role to the twelve-record catalogue: `roles/human-confirm.json`
declares `HumanConfirmation@1` as its only output, so the "declared but
unregistered" branch is live for the first time instead of theoretical.

## D4 — the export gate uses `REFUSED_UNSUPPORTED`, never a new code

Spec §4 calls the export-time refusal "`REFUSED`", but §7 of the registry makes
the enum frozen and `REFUSED` is not a member. The gate therefore refuses with
`REFUSED_UNSUPPORTED`, whose detail always begins with the literal phrase
`no human confirmation artifact` when the file is missing. Callers can match on
code *and* phrase; no downstream consumer needs a registry change.

The gate is ordered fail-closed: existence → `validate(verify_artifacts=True)`
(coverage before hashes) → `retrospective is False`. A retrospective record
therefore never reaches the success path even when its bytes are intact.

## D5 — retrospective is a label, not a backfill

`--retrospective` exists only so a freshly signed record can be *labelled* as
retrospective; it does not reconstruct the past and it prints that the export
gate will never accept it. The pilot corpus stays `agent-mutual`, and the
absence of a confirmation is reported honestly rather than manufactured. This
implements owner decision `05` §8 item 5 and criterion 5.

## D6 — the role is `tools: [read]` only

`05` §3 specifies `tools: [read]`, `network: deny`, `bash: deny`. The record
follows it literally: no `glob`, `grep` or `list`, no write capability, no
skills. The confirmation is produced by the adapter/script, not by the role
writing files; the role's job is to see the artifacts and the reviewer's rows.
`isolation: none` is correct because nothing is blinded *from* a signature, and
`written_by: adapter` keeps `edit` denied (Phase A R5 derivation).

`deny_glob` covers the audit journal and `.git/**` so the signing surface cannot
rewrite the ledger that records it. Emitted audit actions are
`HUMAN_CONFIRMATION` / `HUMAN_CONFIRMATION_REFUSED`, matching the producer's
event name.

## D7 — coverage is checked before hashes

A record that misses a screener2 or adjudication artifact is refused
`BLOCKED_INPUT` naming the file *before* any byte comparison. Otherwise a
partially-covering record could produce a hash mismatch first and send the
reviewer chasing a mutation that never happened. Ordering is part of the
contract, not an implementation detail.

## D8 — the producer writes the record before appending the journal

Spec §4 accepts the residual risk: if the journal append fails after a
successful write, the tool warns rather than deleting or re-signing, because
deleting a signed artifact would destroy the reviewer's act. Phase C tests cover
the warning path and the decline path (decline writes nothing, emits no event).

## D9 — identity excludes timing

`confirmation_fingerprint` drops `provenance.created_at` and canonicalises the
rest with the Phase B `canonical_json_bytes`, so re-running a reviewer's rows at
a later time yields the same identity while a changed verdict or artifact hash
changes it. No second canonicaliser was introduced.

## D10 — no retrospective test path on real workspaces

Tests exercise retrospective behaviour on fixture workspaces only. No packet
step generates a retrospective record under `workspaces/**`, and Phase C touches
no named research workspace, so no workspace audit event is owed by the packet
itself (the producer's event emission is tested on fixtures).
