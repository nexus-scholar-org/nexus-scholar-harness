# Human confirmation (`HumanConfirmation@1`)

Normative input: `specs/agent-layer-portability/06_human_confirmation.md`.
Packet: [`packet_t_alp_c_confirmation.md`](./packet_t_alp_c_confirmation.md)
(Phase C). Judgement calls: [`decision_phase_c_confirmation_2026-10-26.md`](./decision_phase_c_confirmation_2026-10-26.md).

A confirmation answers one question: **which named person accepted exactly which
bytes?** The artifact is `literature/screening/HUMAN_CONFIRMATION.json` under a
workspace; its `artifacts[].sha256` values are raw file hashes of every
screening decision file the reviewer saw.

## Producer — `scripts/confirm_screening.py`

```
uv run python scripts/confirm_screening.py <workspace> [--interactive | --from-queue FILE] [--retrospective]
```

- **Discovery.** Every decision artifact under `literature/screening/` is
  collected (`batch_NNN_decisions.json`, `batch_NNN_decisions_screener2.json`,
  `_adjudication_resolved_group_*.json`). The reviewer cannot sign a subset: an
  uncovered artifact refuses `BLOCKED_INPUT` naming the file.
- **Staged bytes.** Each artifact is hashed at review start and its bytes are
  staged for the session. At write time the on-disk hash is re-verified; bytes
  mutated in between refuse `PARENT_HASH_MISMATCH` and the tool never silently
  re-binds to the new content.
- **Reviewer identity is supplied, never inferred.** `--interactive` prompts for
  name, affiliation, signing capacity and asks the reviewer to confirm; a
  decline writes nothing. `--from-queue` reads rows the reviewer prepared. No
  code path signs for someone who has not seen the decisions.
- **Row honesty.** `changed` rows require an amended verdict plus a non-empty
  `rationale`; `deferred` rows require a `defer_reason` and stay visible in the
  summary. Summary counts must agree with the rows. An override naming a study
  that is absent from the decision set is refused, never dropped.
- **Audit.** A successful write appends a `HUMAN_CONFIRMATION` event naming the
  real reviewer and the reviewed artifacts. The write lands before the append
  (residual risk, accepted in spec §4): a failed append warns rather than
  re-signing.
- **Retrospective records.** `--retrospective` only relabels a *fresh* signature
  as `retrospective: true`. No backfill of the pilot corpus happens: the absence
  of a confirmation is the honest state, and the export gate refuses it.

## Consumers — `scholar_harness.contracts.confirmation`

| Call | Meaning |
| :--- | :--- |
| `validate(record)` | Schema + invariants only (shape, counts, uniqueness, changed-row rationale, defer reasons). |
| `validate(record, verify_artifacts=True, root=<ws>)` | Coverage first, then every recorded hash against the current tree. |
| `verify_artifacts(record, root)` | Byte-level binding check alone. |
| `enforce_coverage(record, root)` | Every decision artifact on disk is covered by the record. |
| `confirmation_fingerprint(record)` | Canonical-JSON digest of the record minus `provenance.created_at` (the Phase B "timing never changes identity" rule). |
| `export_gate(root)` | The export-time gate below. |

The record is also a registered `Envelope@1` payload
(`PAYLOAD_MODELS["HumanConfirmation@1"]`), so a role boundary can carry it like
any other payload; a schema-name near-miss is refused as in Phase B D11.

## Export gate — `scholar-harness export --claim-confirmed`

The narrative "confirmed by a person" is only available when, at export time:

1. `literature/screening/HUMAN_CONFIRMATION.json` exists — otherwise
   `REFUSED_UNSUPPORTED` ("no human confirmation artifact");
2. the record validates and every artifact hash still matches the current
   workspace bytes — mutation since review is `PARENT_HASH_MISMATCH`, never a
   warning or re-hash;
3. `retrospective` is `false` — a retrospective record is
   `REFUSED_UNSUPPORTED` and may never back a "confirmed" export.

Without `--claim-confirmed` the export path is unchanged: the absence of a
confirmation is simply not narrated as confirmation.

## Refusals

| Condition | Code |
| :--- | :--- |
| Missing workspace/artifact, uncovered decision file, identity absent | `BLOCKED_INPUT` |
| Schema defect, count mismatch, duplicate study id, changed row without rationale, deferred row without reason, unknown override id | `INVALID_OUTPUT` |
| Artifact bytes changed after hashing | `PARENT_HASH_MISMATCH` |
| No confirmation artifact, retrospective record, export claiming confirmation it cannot prove | `REFUSED_UNSUPPORTED` |

All codes are frozen members of the Phase B registry; Phase C adds no enum
value and changes no Contract v1 schema.

## Role record — `roles/human-confirm.json`

The agent surface is read-only: `tools: [read]`, `network: deny`, `bash: deny`,
`isolation: none` (nothing is blinded from a confirmation), adapter-written
output at `workspaces/{ws}/literature/screening/HUMAN_CONFIRMATION.json`, and
audit events `HUMAN_CONFIRMATION` / `HUMAN_CONFIRMATION_REFUSED`. Generated
frontmatter and permissions come from the Phase A generator
(`scripts/generate_agent_roles.py --check`); the prompt body is
`roles/human-confirm.prompt.md`.
