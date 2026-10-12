# WP01 Packet E4 — Adversarial Evidence-Currentness Proof

**Status:** `CLOSED_WITH_RESIDUAL_DEBT` (qualified scope; see completion report)
**Owner:** harness conformance boundary, with remediation routed to the owning
kit or harness component  
**Delivery lane:** `RELEASE`  
**Purpose:** prove from outside the completed E1–E3 chain that altered evidence
cannot be accepted or presented as the current evidence index.

## 1. Why E4 exists

Close-out addendum (2026-10-09): the operator authorized the bounded PR #77
repairs and qualified milestone closure. The completion report records which
original obligations remain unproven; the original requirements below are
preserved and must not be read as universally satisfied by this closure.

E1 establishes an acquired document, E2 establishes accepted extracted text,
and E3 establishes a lineage-bound index candidate and accepted index record.
Those components can each have unit tests while a cross-boundary mutation is
still silently absorbed. E4 is the independent negative proof that prevents
that gap.

E4 is not a new scientific workflow, index format, or Contract v1 version. It
is an adversarial conformance packet. It mutates one sealed input or observable
backend state at a time and proves that the existing boundaries detect the
change before a stale result can be called current.

## 2. Preconditions and start gate

E4 cannot start until all are true:

1. E3 has an approved completion report with every required E3 ledger item
   passing or an explicit architecture decision that supersedes it.
2. The canonical kit commits, vendored `tools/` snapshots, full-SHA plugin pins,
   and generated metapackage pins agree.
3. The E3 acceptance adapter publishes `rag/index/accepted.json` and the
   canonical audit event only after all seven E3 checks pass.
4. The normal, unmutated E1 → E2 → E3 golden workspace succeeds with the
   chosen real or hermetic backend and is independently reproducible.

Until then, this document is a definition, not authority to begin E4 or to
describe E3 as complete.

## 3. Immutable boundaries

- Contract v1 artifact types, identifier grammar, canonical JSON, parent-hash
  semantics, and acceptance semantics remain frozen.
- E4 never invents a replacement parent, identifier, checksum, or provenance
  record to make an altered input pass.
- E4 mutates copies of a sealed fixture workspace only. It never mutates a
  researcher workspace or canonical test fixture in place.
- A failed currentness check may preserve an older accepted index as historical
  state, but it must not report it as current for the altered inputs.
- E4 does not add retrieval, synthesis, scoring, consensus, UI, or agent-loop
  behavior.

## 4. The sealed baseline fixture

The harness owns one small fixture workspace containing:

- a registered protocol and corpus snapshot;
- accepted screening decisions;
- at least two accepted documents with distinct study/document identities;
- acquired PDF bytes and their recorded checksums;
- accepted E2 `document_manifest` records and extracted Markdown bytes;
- the E3 candidate sidecar, accepted index record, canonical audit event, and
  a queryable backend snapshot;
- a manifest of relative paths, canonical checksums, and expected normal-run
  outcomes.

The fixture is created or refreshed only by an explicit E4 fixture-generation
command. Individual tests copy it to `tmp_path`; no test edits the sealed
source tree. Fixture generation is deterministic and its seal is tested.

## 5. Mutation matrix

Each case changes exactly one declared boundary while retaining every other
sealed input byte-for-byte. The observable must be a refusal, a stale/currentness
failure, or a successful rebuild that produces a new lineage-bound result. A
mere exception without a structured outcome is not evidence.

| ID | External mutation | Required observation | Forbidden outcome |
|---|---|---|---|
| E4-NEG-001 | Flip one acquired PDF byte after E1 acceptance. | Acquisition/document checksum or downstream parent validation detects the changed source; no current E3 acceptance for the altered chain. | Reusing the earlier extraction/index as current without disclosure. |
| E4-NEG-002 | Change one accepted extracted Markdown byte after E2 acceptance. | Extraction-content binding or E3 input/hash verification rejects it or requires a new E2 acceptance. | Reusing chunk IDs, manifest, or accepted index as current. |
| E4-NEG-003 | Change one effective chunking configuration value. | Configuration/index fingerprint changes; old accepted index is not current for the new configuration. | Same accepted fingerprint under changed effective configuration. |
| E4-NEG-004 | Change embedding provider, model, revision, dimension, or distance identity. | Embedding-identity/currentness verification rejects the old index or requires a separately bound rebuild. | Querying or accepting the old backend as compatible. |
| E4-NEG-005 | Alter parent lineage: artifact ID, payload checksum, workspace, protocol fingerprint, or corpus fingerprint. | The relevant parent/lineage gate refuses before authoritative publication. | Coercion, identifier regeneration, or cross-workspace acceptance. |
| E4-NEG-006 | Remove, add, corrupt, or alter visible backend chunks/metadata. | Typed backend verification reports an inconsistent state; no current accepted index is published. | Count-only success, partial invisible repair, or success audit. |

The final implementation may split a row into narrower tests, but it may not
weaken the row's required observation. Any newly discovered mutation class is a
separate architecture addendum, not an unreviewed expansion of E4.

## 6. Required observables

For every mutation, the test records and asserts:

1. the sealed baseline checksum and the one changed path/value;
2. the attempted public entry point (harness CLI/API, not a private helper);
3. the structured result/error code and full parent/manifest identity context;
4. whether `rag/index/accepted.json` changed, remained historical, or was not
   created;
5. whether a `RAG_INDEX_BUILT` or `RAG_INDEX_REJECTED` event was emitted and
   whether its fields truthfully describe the outcome;
6. the backend's visible-set result before and after the attempt; and
7. that no partial authoritative state was published.

The E3 failure vocabulary remains authoritative. E4 must use the code selected
by the boundary that detected the mutation; it must not introduce generic
"stale" or "invalid" strings to conceal an unmapped condition.

## 7. Ownership and remediation

E4 tests belong in the harness because they compose the full evidence chain.
They do not authorize cross-repository fixes in one pull request.

| Finding location | Required response |
|---|---|
| Harness adapter, fixture builder, audit publication, or conformance harness | Harness repair PR, then rerun the affected E4 mutation and release gate. |
| PDF extraction/acquisition behavior | Canonical `scholar-pdf-kit` fork + PR, then separate harness vendor/pin synchronization PR. |
| Chunking, manifest, replacement, or backend verification | Canonical `scholar-rag-kit` fork + PR, then separate harness vendor/pin synchronization PR. |
| MCP declaration or agent transport | Canonical `scholar-agent-kit` fork + PR, then separate harness vendor/pin synchronization PR. |
| Frozen contract ambiguity | Stop; create an architecture/version decision before any implementation. |

## 8. Acceptance criteria

- **E4-001:** the sealed baseline fixture reproduces an accepted current index.
- **E4-002:** each mutation in §5 is isolated and independently detected.
- **E4-003:** no mutation can leave a new accepted record or success event that
  claims the altered evidence is current.
- **E4-004:** a normal rebuild after a legitimate input/configuration change is
  explicit, lineage-bound, and distinguishable from reuse of stale state.
- **E4-005:** the tests exercise public harness composition and the kit's typed
  verification surface, not duplicated kit internals.
- **E4-006:** every demonstrated defect is repaired by its owner before E4 is
  closed; no expected-failure or allow-list is called a pass.
- **E4-007:** replay of the unmodified sealed fixture remains deterministic.

## 9. Required gates

E4 is `RELEASE` work. The task capsule selects exact commands under
`docs/architecture/test_gate_policy.md`, but final evidence includes at least:

```powershell
uv run python scripts/select_test_gate.py --task T-140 --stage closure
uv run pytest
uv run ruff check scripts/
uv run python scripts/generate_contract_baseline.py --check
uv run python scripts/generate_contract_schemas.py --check
uv run python scripts/generate_two_study_contract_fixture.py --check
uv run python scripts/generate_nexus_scholar_pins.py --check
```

Run the focused E4 mutation case while editing. Run the full relevant suites
only at the final candidate or when a dependency/pin/public boundary changes.
CI supplies the cross-platform proof. Every repair uses the active task context
capsule plus a delta; it does not reload this handoff or E1–E3 history without
an escalation trigger.

## 10. Completion report

The E4 completion report must enumerate each mutation, its observed code and
publication state, the tested kit/harness SHAs, the fixture seal, and any
remediation PRs. It must state plainly whether the project has only proved the
E1–E3 evidence-currentness chain or has separately validated downstream
retrieval/synthesis behavior.

Only after E4 closes may the deferred harness core modularity roadmap begin.
