# WP-01 Contract Adoption Handoff

**Status:** Ready for implementation agents
**Architecture owner:** Harness contract v1
**Reference implementation:** `src/scholar_harness/contracts/`
**Golden chain:** `tests/fixtures/contracts/v1/two_study_artifact_chain.json`

## Objective

Adopt the frozen contract in real protocol, search, and harness boundaries
without reopening identifier or envelope design. The golden chain is the
consumer contract: two different studies intentionally share a title and must
remain distinct through corpus, screening, document, and claim artifacts.

Implementation agents own adapters, not architecture. If a package cannot emit
the frozen shape without changing its domain model, it must report the mismatch
instead of weakening the schema or inventing compatibility behavior.

## Frozen decisions

Agents must not change these without a new architecture decision:

1. Workspace, study, source-record, document, chunk, claim, and evidence IDs are
   semantically distinct.
2. `SCI-*` remains a valid legacy study ID; new minting uses `STU-*`.
3. Title equality alone never establishes identity.
4. Provider identifiers remain under `external_ids` and do not replace
   `study_id`.
5. Every derived artifact names and hashes its direct parents.
6. Protocol and corpus fingerprints must match across one closed execution
   generation.
7. Screening decisions must match their exact parent batch binding.
8. Evidence must resolve to a usable document belonging to the same study.
9. Unknown major schema versions fail closed. Missing versions are legacy, not
   implicit v1.
10. A producer failure may be `PARTIAL` or hard failure, never empty success.

## Task packets

### Packet A — Protocol identity producer

**Repository:** canonical `scholar-protocol-kit` repository
**Purpose:** make protocol identity and fingerprints explicit inputs to every
downstream envelope.

Deliverables:

- expose the existing protocol fingerprint through one stable public adapter;
- mint or accept a `PRT-*` protocol ID without changing protocol fingerprint
  semantics;
- emit producer version/commit and schema version;
- preserve authored array order and the protocol kit's existing canonical
  serializer;
- add a fixture proving formatting-only changes preserve the fingerprint while
  semantic changes do not.

Do not replace protocol-kit's canonical serializer with the general artifact
serializer.

### Packet B — Search corpus snapshot producer

**Repository:** canonical `scholar-search-kit` repository
**Purpose:** emit `CorpusSnapshotArtifact` after verification/deduplication.

Deliverables:

- map each source record to one `REC-*` identifier;
- emit one stable `study_id` for each deduplicated component;
- retain provider IDs, legacy `SCI-*` aliases, and record-to-study lineage;
- emit a deterministic `COR-*` corpus ID and corpus fingerprint;
- expose partial provider outcomes through `OperationOutcome`;
- pass the same-title fixture and the transitive DOI/arXiv bridge fixture.

The search kit continues to own deduplication. Do not copy dedup algorithms into
the harness.

### Packet C — Harness artifact acceptance gate

**Repository:** this harness
**Purpose:** reject malformed, stale, or cross-workspace producer artifacts
before workspace state changes.

Deliverables:

- parse producer output through the typed v1 model selected by `artifact_type`;
- compare expected workspace/protocol/corpus context;
- verify every available direct-parent hash;
- return structured contract issues without publishing invalid artifacts;
- append audit/state updates only after acceptance and atomic publication;
- retain the rejected payload hash and bounded diagnostics for investigation.

Use `validate_artifact_chain` for closed handoff packages. A streaming/single
artifact acceptance path may allow unavailable parents only when it verifies
them against the workspace artifact registry.

### Packet D — Screening producer migration

**Repository:** harness, with search-kit screening compatibility as needed
**Purpose:** replace unbound batches/decisions with generation-bound artifacts.

Deliverables:

- prepare `ScreeningBatchArtifact` from an accepted corpus snapshot;
- write `ScreeningDecisionsArtifact` with the identical binding;
- reject decisions outside the parent batch;
- reject protocol/corpus/dedup/renderer mismatches;
- archive legacy decisions instead of silently reusing them;
- preserve screener identity, method, reason, and adjudication parents.

### Packet E — Downstream adapter stubs

**Repositories:** canonical PDF and RAG kit repositories
**Purpose:** prove the frozen consumer boundary before implementing their full
remediation work packages.

Deliverables:

- PDF adapter emits `DocumentManifestArtifact` with study/document identity and
  explicit content status;
- RAG adapter emits `ClaimEvidenceLedger` with citation tokens and independent
  verification axes;
- both adapters pass the golden chain without implementing unrelated PDF/RAG
  fixes early.

These are compatibility stubs for WP-01. Full PDF truthfulness remains WP-07;
full RAG identity/non-fabrication remains WP-02.

## Required validation for every packet

1. Owner-package unit tests.
2. Generated schema drift check.
3. The two-study golden chain.
4. One negative mutation relevant to the producer boundary.
5. Isolated wheel import and public-entrypoint smoke.
6. No network in required tests.
7. No toolkit change only in the harness vendored tree.

Harness commands:

```powershell
uv run python scripts/generate_contract_schemas.py --check
uv run python scripts/generate_two_study_contract_fixture.py --check
uv run pytest tests/test_cross_kit_contracts.py tests/test_contract_artifact_chain.py
```

## Agent completion report template

Each implementation agent returns:

```text
Packet:
Canonical repository:
Contract types adopted:
Legacy behavior retained/deprecated:
Files changed:
Negative fixtures added:
Targeted tests:
Isolated-wheel result:
Canonical commit/PR:
Harness vendored SHA/pin update:
Remaining mismatches or blocked decisions:
```

## Stop conditions

Stop and escalate rather than improvise when:

- an adapter would use workspace ID as study ID;
- title-only merging is required to pass an existing test;
- a producer cannot preserve source-record lineage;
- a legacy artifact lacks enough information to reconstruct fingerprints;
- an implementation would write before validation;
- two package adapters interpret the same contract field differently;
- a vendored toolkit change cannot be linked to its canonical repository commit.

## WP-01 completion gate

WP-01 is complete only when protocol → corpus → screening can execute using v1
artifacts, the harness rejects every golden negative mutation, two same-title
studies remain distinct, and canonical toolkit repositories, vendored snapshots,
and manifest pins agree. Passing model-only tests is necessary but not sufficient.
