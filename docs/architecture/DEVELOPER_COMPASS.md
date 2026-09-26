# Nexus Scholar Developer Compass

**Baseline:** Contract v1 after canonical harness merge `ca6a77b` (PR #42)  
**Search-kit pin:** `911d864fcb6a706d4c0339f80524a46f591e2cad`  
**Purpose:** give development agents one short, authoritative starting point and
prevent downstream work from drifting around the scientific contract.

## 1. Current position

The trustworthy runtime chain is now:

```text
protocol artifact (Packet A)
        ↓ exact protocol fingerprint
corpus snapshot (Packet B)
        ↓ exact corpus fingerprint + record-to-study lineage
acceptance/publication gate (Packet C)
        ↓ accepted immutable parents
screening batch and decisions (Packet D)
        ↓ exact batch binding + decision lineage
acquired PDF + accepted extracted text (Packets E1-E2 — adopted)
        ↓ exact document/extraction lineage
stable chunks and index manifest (Packet E3 — next)
```

| Packet | Responsibility | Current state |
|---|---|---|
| A | Protocol identity producer | Adopted |
| B | Corpus snapshot and study identity producer | Adopted |
| C | Typed acceptance and atomic publication | Reference adopted |
| D | Bound screening batches and decisions | Adopted |
| E | PDF/document and RAG boundary adapters | E1-E2 adopted; E3 next |

Older documents may still describe A, B, or D as blocked. For implementation
status, this compass and canonical `main` at or after `ca6a77b` take precedence.
The frozen contract itself remains governed by
`docs/architecture/contract_v1_baseline.md`.

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

## 4. Source-of-truth map

| Need | Read this first |
|---|---|
| Frozen boundary and drift policy | `docs/architecture/contract_v1_baseline.md` |
| Typed models | `src/scholar_harness/contracts/models.py` |
| Identifier registry | `src/scholar_harness/contracts/identifiers.py` |
| Canonical hashing | `src/scholar_harness/contracts/canonical.py` |
| Acceptance and atomic publication | `src/scholar_harness/contracts/acceptance.py` |
| Packet C behavior | `docs/architecture/wp01_packet_c_reference.md` |
| Packet E1 implementation-ready handoff | `docs/architecture/wp01_packet_e1_acquired_document_handoff.md` |
| Packet E1 completion evidence | `docs/architecture/wp01_packet_e1_completion_report.md` |
| Historical Packet A–E definitions | `docs/architecture/wp01_contract_adoption_handoff.md` |
| Screening producer | `src/scholar_harness/screening/batcher.py` |
| Screening collector | `src/scholar_harness/screening/collector.py` |
| Search identity producer | `tools/scholar-search-kit/src/scholar_search/identity.py` |
| Deduplication behavior | `tools/scholar-search-kit/src/scholar_search/dedup.py` |
| Exact toolkit revisions | `.agents/plugins/nexus-scholar/plugins.json` |

## 5. Mandatory start procedure for every contract task

```powershell
git status -sb
git log -3 --oneline --decorate
uv run python scripts/generate_contract_baseline.py --check
uv run python scripts/generate_contract_schemas.py --check
uv run python scripts/generate_two_study_contract_fixture.py --check
uv run python scripts/generate_nexus_scholar_pins.py --check
```

If the baseline check fails, stop and report `BLOCKED_BASELINE_DRIFT`. Do not
regenerate files merely to make the check green.

Before changing a toolkit, read its `.agents/skills/<kit>/SKILL.md` and
`docs/kits_surface_matrix.md`.

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

During implementation, run focused tests. Before phase completion or PR:

```powershell
uv run pytest
uv run ruff check scripts/
uv run python scripts/generate_contract_baseline.py --check
uv run python scripts/generate_contract_schemas.py --check
uv run python scripts/generate_two_study_contract_fixture.py --check
uv run python scripts/generate_nexus_scholar_pins.py --check
```

Every boundary change also needs:

- one successful round-trip test;
- one negative mutation test;
- one stale or mismatched-parent test;
- one idempotence or determinism test;
- a test proving failure does not publish authoritative output.

## 8. Toolkit synchronization rule

Code under `tools/<kit>/` belongs to that toolkit's canonical repository.
Toolkit changes require all three steps:

1. Merge the change through the toolkit's fork and canonical PR.
2. Update that toolkit's full `default_rev` SHA in `plugins.json`.
3. Keep the vendored `tools/<kit>/` implementation synchronized with that SHA,
   then regenerate `packaging/nexus-scholar/nexus_scholar_pins.json`.

Never patch only the vendored copy. Never use a floating branch as a pin.

Harness improvements also go through the personal fork and a PR to
`nexus-scholar-org/nexus-scholar-harness`; never push a feature branch directly
to canonical `origin`.

## 9. Prohibited shortcuts

Do not:

- weaken a schema because an adapter is inconvenient;
- accept an unknown major schema version;
- publish after acceptance failure;
- convert missing decisions into silent heuristic success;
- merge records that carry conflicting persistent identifiers;
- invent provenance to migrate legacy data;
- treat a live log as the final scientific artifact;
- modify generated schemas, fixtures, or package pins by hand;
- begin higher-level synthesis agents before their evidence boundaries exist;
- mix unrelated cleanup into a contract adoption PR.

## 10. Next implementation order

### Packet E1 — acquired-document boundary

Define the accepted document artifact around `study_id`, acquisition outcome,
legal/OA status, source URL, checksum, media type, and exact corpus parent.
Do not treat a downloaded path as document identity.

The implementation-ready contract and task packet is
`docs/architecture/wp01_packet_e1_acquired_document_handoff.md`. It records the
important frozen-contract boundary: acquisition publishes a PDF-kit-owned
manifest; E2 emits Contract v1 `DocumentManifestArtifact` only after extraction.
The older Packet E definition is historical compatibility guidance and does not
replace this acquisition-specific packet.

**Status:** E1 complete and approved on harness merge
`baaeeb43977897924bd6ba9fda252e1bc9d464b8`: PDF kit
`858911f6b7dd5738de94fa749ffc4c65b6d0b70e`, agent kit
`6050e0c99cdddb0f2c1ce7e0c62458a58eab5ce7`, full-SHA pins, generated
metapackage pins, and E1-NEG-030/044/047 conformance agree. See
`docs/architecture/wp01_packet_e1_completion_report.md`. E2 subsequently
closed at `0fb665558e0808d66348476eda2c927439a96be1`; E3 is next.

### Packet E2 — extracted-text boundary

E2 consumes the accepted E1 acquisition manifest, verifies its parent lineage,
and binds extracted text to the accepted document ID and source checksum. Only
after extraction does the PDF kit construct a non-authoritative Contract v1
`DocumentManifestArtifact` candidate; the bounded harness adapter alone calls
the frozen acceptance gate and publishes the authoritative artifact. Requested
and effective extraction engines, fallback chain, page/character counts,
content status, and failure reason remain recorded in the kit-owned sidecar.

**Status:** E2 complete and approved on harness merge
`0fb665558e0808d66348476eda2c927439a96be1`: PDF kit
`0430ee40c491edbb055af4ab068637275aada476`, agent kit
`deebfad995ba88bbd748be9beddd1aa2b8a51264`, bounded harness acceptance
adapter, full-SHA pins, generated metapackage pins, and E2 conformance agree.
See `docs/architecture/wp01_packet_e2_completion_report.md`. E3 is next.

### Packet E3 — chunk and index boundary

Mint stable chunk IDs from the accepted document/extraction lineage. Publish an
index manifest containing the exact extraction parents, chunking configuration,
embedding model/version, and index fingerprint. Detect and reject stale chunks.
The frozen Contract v1 does not contain a chunk/index artifact type; E3 therefore
uses a kit-owned typed sidecar plus a harness acceptance record and must not
silently extend the frozen contract. The ratified readiness boundary and
implementation ordering are recorded in
`docs/architecture/wp01_packet_e3_readiness_baseline.md`.

### Packet E4 — negative end-to-end proof

Prove that changed PDF bytes, changed extraction output, changed chunking
configuration, and stale indexes cannot pass as current artifacts.

### Only after Packet E

Build extraction, verification, analysis, synthesis, reporting, and critic loops
on top of accepted document/chunk evidence. Agent sophistication must not outrun
evidence identity.

## 11. Small-agent task template

Give a development agent one bounded assignment in this form:

```text
Goal:
  Implement exactly one named packet or adapter boundary.

Immutable parents:
  List the accepted artifact types and fingerprints it must consume.

Output:
  Name the one Contract v1 artifact or outcome it must produce.

Must preserve:
  Identity, fingerprints, input checksums, method provenance, structured status.

Must reject:
  Missing parent, wrong workspace, stale fingerprint, unknown major version,
  invalid identifier, and idempotency conflict.

Tests:
  Happy path, negative mutation, stale parent, determinism, no-publication on
  failure.

Out of scope:
  Schema weakening, unrelated refactors, downstream features, generated-file
  hand edits.
```

## 12. Definition of done

A task is done only when:

- the producer emits a typed Contract v1 artifact or structured outcome;
- the artifact passes the acceptance gate;
- identity and parent lineage are explicit;
- reruns are deterministic or explicitly versioned;
- negative tests prove stale or malformed inputs fail closed;
- no authoritative output is left behind after failure;
- toolkit source, canonical repository commit, vendored copy, and pin agree;
- focused tests, full phase tests, baseline checks, and CI pass;
- documentation states measured behavior without claiming more than the tests
  demonstrate.

The guiding rule is simple: **make the evidence chain trustworthy before making
the agents more autonomous.**
