# WP-01 Packet C Reference: Harness Artifact Acceptance Gate

**Status:** `CONSUMER_GATED_REFERENCE`
**Owner:** `nexus-scholar-org/nexus-scholar-harness`
**Depends on:** frozen `contract-v1-wp00`
**Public API:** `scholar_harness.contracts.accept_artifact`

## Purpose

Packet C is the reference implementation for adopting Contract v1 without
weakening it. It accepts one producer artifact into an existing workspace only
after typed validation, generation-context validation, and direct-parent type,
hash, and payload validation succeed. Invalid inputs cannot enter the accepted
artifact registry.

This does not claim that protocol or search producers emit Contract v1. Packets
A and B remain open. It proves the harness consumer gate against the frozen
golden chain and negative mutations.

## Inputs and outputs

`accept_artifact(workspace, payload, expected=AcceptanceContext(...))` accepts a
mapping, JSON string, or JSON bytes. The caller supplies the expected workspace,
protocol fingerprint, and corpus fingerprint from trusted workspace state.

Accepted state:

- canonical payload: `artifacts/<artifact_type>/<artifact_id>.json`;
- typed registry: `audit/artifact_registry.json`;
- audit action: `ARTIFACT_ACCEPTED` after publication and registry replacement.

Rejected state:

- no accepted artifact or registry entry;
- bounded diagnostic record: `audit/rejections/<payload-sha256>.json`;
- audit action: `ARTIFACT_REJECTED` with `FAILED` status when audit storage is
  available;
- raw rejected payload is never retained by the gate.

## Gate sequence

1. Parse JSON object and compute its canonical payload hash.
2. Select the typed model from `artifact_type`; unknown types fail closed.
3. Validate schema, IDs, timestamps, fingerprints, and artifact-specific rules.
4. Compare workspace, protocol, and corpus context with trusted expectations.
5. Resolve every declared direct parent in the typed workspace registry,
   require its exact accepted hash and stored payload, and enforce the required
   parent type. Screening decisions must also match their parent batch binding,
   batch ID, and candidate set.
6. Detect same-ID/different-payload conflicts. Identical retries are idempotent
   only after the current context and lineage checks pass.
7. Reject an existing destination that has no matching registry entry.
8. Stage artifact and registry files, atomically replace both, then append the
   canonical audit event.
9. Roll back artifact and registry if staging, replacement, or audit append
   fails; return `ATOMIC_COMMIT_FAILED`.

The two-file artifact/registry update is implemented as staged atomic replaces
with restoration of the prior registry on failure. It is not a general database
transaction. No consumer should bypass this API and write the registry directly.

## Failure vocabulary

| Code | Meaning |
|---|---|
| `INVALID_JSON` | Input is not a JSON object. |
| `UNSUPPORTED_ARTIFACT_TYPE` | No frozen Contract v1 model owns the type. |
| `SCHEMA_VALIDATION_ERROR` | Typed model rejected the payload. |
| `WORKSPACE_ID_MISMATCH` | Artifact belongs to another workspace. |
| `PROTOCOL_FINGERPRINT_MISMATCH` | Artifact belongs to another protocol generation. |
| `CORPUS_FINGERPRINT_MISMATCH` | Artifact belongs to another corpus generation. |
| `REGISTRY_INVALID` | Accepted-artifact state is malformed and cannot be trusted. |
| `MISSING_PARENT_ARTIFACT` | A declared direct parent was not accepted. |
| `PARENT_HASH_MISMATCH` | Parent ID exists but its accepted hash differs. |
| `REGISTERED_PARENT_INVALID` | A registered parent payload cannot be loaded or typed. |
| `REGISTERED_PARENT_HASH_MISMATCH` | Stored parent content differs from its registry hash. |
| `REQUIRED_PARENT_TYPE_MISSING` | The artifact lacks its Contract v1 parent type. |
| `SCREENING_BATCH_ID_MISMATCH` | Decisions name a different batch than their parent. |
| `SCREENING_BINDING_MISMATCH` | Decisions and their parent batch have different bindings. |
| `DECISION_OUTSIDE_BATCH` | A decision references a study absent from its parent batch. |
| `IDEMPOTENCY_CONFLICT` | Existing artifact ID maps to different content. |
| `REGISTERED_ARTIFACT_MISSING` | Idempotent retry found no readable accepted payload. |
| `REGISTERED_ARTIFACT_INVALID` | Idempotent retry found invalid accepted content. |
| `REGISTERED_ARTIFACT_HASH_MISMATCH` | Accepted content differs from its registry hash. |
| `ORPHAN_ARTIFACT_PATH` | Destination exists without a matching registry entry. |
| `ATOMIC_COMMIT_FAILED` | Publication/audit failed and accepted state was rolled back. |

## Reference tests

`tests/test_contract_acceptance.py` proves:

- valid publication, registry, and audit ordering;
- rejection records retain hashes but not raw payloads;
- context mismatch fails before publication;
- missing and mismatched parents fail closed;
- identical retries remain context- and lineage-gated, while content conflicts
  are rejected;
- required parent types and screening parent bindings are enforced;
- orphan destinations are rejected without overwrite;
- audit and staging failures roll back accepted state.

## Pattern for smaller agents

Future packet implementations should copy the evidence structure, not the code
blindly:

1. state the exact completion level;
2. validate before mutation;
3. test a successful path and boundary-specific negative mutations;
4. make idempotency and partial failure explicit;
5. update the baseline state only after executable evidence exists;
6. never report adjacent packets as complete.

Packet D remains blocked until Packets A and B provide real protocol and corpus
producer artifacts. Packet C being implemented removes only the C dependency.
