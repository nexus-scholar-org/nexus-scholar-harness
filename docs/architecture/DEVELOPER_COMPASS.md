# Nexus Scholar Developer Compass

**Purpose:** the rules every change to the research evidence chain must keep.
Cut on 2026-11-03 to its rules; section numbers are unchanged so existing
citations ("Compass §3", "§7") still resolve. Packet status and ordering now
live in the [assessment priority list](../assessment/README.md); decisions in
[`docs/decisions.md`](../decisions.md).

## 2. The non-negotiable mental model

The harness does not merely pass files between tools. It accepts immutable,
typed scientific artifacts connected by verifiable lineage.

Every authoritative artifact must answer:

1. Which workspace produced it?
2. Which run produced it?
3. Which frozen protocol governed it?
4. Which corpus governed it?
5. Which exact parent artifacts were consumed?
6. Which package version and commit produced it?
7. Was the operation successful, partial, waiting, or failed?
8. Can the same logical input reproduce the same identities and fingerprints?

If an implementation cannot answer these questions, it is not ready to publish
an authoritative artifact.

## 3. Hard invariants

### Identity

- Keep workspace, protocol, run, corpus, source record, study, document, chunk,
  screening decision, claim, evidence, artifact, and audit-event IDs distinct.
- Never use a filename, array index, title, DOI, or provider-local ID as a
  substitute for the registered Contract v1 identity.
- Missing persistent identifiers may be compatible. Conflicting non-empty
  identifiers must not be silently merged.
- Identity generation must be deterministic and input-order independent where
  the contract declares order irrelevant.

### Fingerprints and parents

- Bind downstream artifacts to the exact protocol and corpus fingerprints.
- List every immutable parent under `inputs` with its artifact ID and checksum.
- Reject stale, missing, cross-workspace, or fingerprint-mismatched parents.
- Never recompute or silently replace a parent identity to make acceptance pass.

### Outcomes and provenance

- Empty output is not automatically success.
- Degraded work is `PARTIAL` and must explain the degradation.
- Hard failure must carry a structured error.
- Record the actual method: `HUMAN`, `DETERMINISTIC_RULE`, `HEURISTIC`, `LLM`,
  `EXTERNAL_PROVIDER`, or `COMPOSED`.
- A fallback must be explicit. Never label heuristic work as LLM work or an
  adjudicated result as a single screener decision.
- Do not invent timestamps, screeners, parent decisions, citations, or evidence.

### Fail-closed publication

- Validation or acceptance failure must stop authoritative publication.
- Missing screening decisions must not silently produce included/excluded sets.
- Dual screening requires two provenance-complete parent decisions.
- A disagreement requires an adjudication decision whose
  `parent_decision_ids` reference both screener decisions.
- Logging an acceptance failure and continuing is a contract violation.

## 6. Minimum valid screening provenance

A single decision handed to the Contract v1 collector needs, at minimum:

```json
{
  "decision_id": "SCR-example-001",
  "study_id": "STU-example-001",
  "screener_id": "reviewer-1",
  "method": "HUMAN",
  "decision": "INCLUDE",
  "reason": "Matches the frozen inclusion criteria.",
  "decided_at": "2026-09-24T12:00:00Z",
  "parent_decision_ids": []
}
```

For a dual-screening consensus, the final decision uses `COMPOSED` and lists
both source decision IDs. For a disagreement, the adjudication decision must
list both source decision IDs. Missing lineage blocks collection.

## 7. Required validation before declaring a task done

Every task must declare its `FAST`, `STANDARD`, or `RELEASE` delivery lane
using `docs/architecture/test_gate_policy.md` before implementation. The lane
sets the review cadence and minimum gate level; contract, identity,
publication, public-surface, and cross-kit work is always `RELEASE`.

During implementation, run focused tests. Select the final PR or closure
commands from the test-gate policy rather than rerunning the full harness suite
after every repair. In particular, a `STANDARD` task runs its owner suite once
for the final executable PR candidate; `RELEASE` work runs the full applicable
packet/closure gates. For contract-bound `RELEASE` work, the required checks
include:

```powershell
uv run pytest
uv run ruff check scripts/
uv run python scripts/generate_contract_baseline.py --check
uv run python scripts/generate_contract_schemas.py --check
uv run python scripts/generate_two_study_contract_fixture.py --check
uv run python scripts/generate_protocol_schema.py --check
```

Every boundary change also needs:

- one successful round-trip test;
- one negative mutation test;
- one stale or mismatched-parent test;
- one idempotence or determinism test;
- a test proving failure does not publish authoritative output.

## 9. Prohibited shortcuts

Do not:

- weaken a schema because an adapter is inconvenient;
- accept an unknown major schema version;
- publish after acceptance failure;
- convert missing decisions into silent heuristic success;
- merge records that carry conflicting persistent identifiers;
- invent provenance to migrate legacy data;
- treat a live log as the final scientific artifact;
- modify generated schemas or fixtures by hand;
- begin higher-level synthesis agents before their evidence boundaries exist;
- mix unrelated cleanup into a contract adoption PR.

## 12. Definition of done

A task is done only when:

- the producer emits a typed Contract v1 artifact or structured outcome;
- the artifact passes the acceptance gate;
- identity and parent lineage are explicit;
- reruns are deterministic or explicitly versioned;
- negative tests prove stale or malformed inputs fail closed;
- no authoritative output is left behind after failure;
- focused tests, full phase tests, baseline checks, and CI pass;
- documentation states measured behavior without claiming more than the tests
  demonstrate.

The guiding rule is simple: **make the evidence chain trustworthy before making
the agents more autonomous.**
