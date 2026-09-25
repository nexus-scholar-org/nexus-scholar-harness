# Packet E1 — Acquired-Document Boundary

**Status:** `READY_FOR_IMPLEMENTATION`  
**Architecture owner:** Harness Contract v1  
**Implementation owner:** canonical `nexus-scholar-org/scholar-pdf-kit`  
**Declared MCP boundary owner:** canonical `nexus-scholar-org/scholar-agent-kit` (thin rejection adapter only)  
**Current PDF-kit pin:** `9fa9e00361cd6d3bd7aec3c5a079db80f0287f58`  
**Direct scientific parent:** accepted `ScreeningDecisionsArtifact`  
**Required context:** its accepted `CorpusSnapshotArtifact` and protocol/corpus fingerprints

### 1.0 Supersession

This handoff supersedes and replaces the **“Packet E — Downstream adapter stubs”** section of `docs/architecture/wp01_contract_adoption_handoff.md` for PDF acquisition. The older handoff remains locked in the Contract v1 baseline and is intentionally **not** edited. This handoff—not the historical adapter-stub wording—is authoritative for E1 acquisition and E2 extraction responsibilities and their handoff boundary.

## 1. Decision and scope

E1 establishes a truthful, deterministic boundary between an included study and
the exact PDF bytes acquired for it. It covers discovery, download or user
ingest, validation, legal/access provenance, content hashing, reuse, atomic
publication, structured failure reporting, and recovery after an interrupted
commit.

E1 does **not** extract text, run an extraction engine, mint chunks, build an
index, or publish claims. Those activities belong to E2–E4. E1 is acquisition
only; it must not make an extraction result appear to exist before E2 has
produced one.

### 1.1 Frozen-contract boundary

The frozen Contract v1 `DocumentRecord` is an **extracted-content** record:
`VALID` and `PARTIAL` require `extracted_path`, and every record requires
`extraction_method`. An acquisition-only adapter therefore cannot truthfully
emit the existing `DocumentManifestArtifact` without claiming extraction that
has not happened.

E1 consequently publishes a PDF-kit-owned acquisition manifest and operation
outcome. E2 consumes that accepted acquisition manifest and emits the existing
Contract v1 `DocumentManifestArtifact` only after extraction. E1 does not change
the frozen schemas and does not, by itself, complete Packet E.

The acquisition manifest is **not** a registered Contract v1 artifact. The
harness registries in `contracts/acceptance.py` and `contracts/chain.py` remain
frozen and contain no acquired-document type. E1 must not add an
`acquired_document_manifest` type, call `accept_artifact` with this payload, or
present it as a Contract v1 parent. The E1 publisher has its own schema,
validation, fingerprint, and lineage checks.

If an implementation requires E1 itself to emit an authoritative Contract v1
artifact, stop with `BLOCKED_CONTRACT_VERSION_DECISION`. Adding a new Contract
artifact type requires the full contract-change procedure: an
architecture/version decision, regenerated schemas and golden fixtures, a
negative regression test, and independent review. Setting
`content_status=FAILED`, inventing an `extracted_path`, or labelling a PDF path
as extracted text is forbidden.

### 1.2 Normative PDF requirement allocation

The PDF requirements are allocated explicitly below. An E1 completion claim
covers only rows marked **E1**. Rows marked **E2/E3** are explicit handoffs, not
work silently omitted from the broader remediation program. In particular, E1
does not implement PDF-008 through PDF-012, and no E1 test or completion report
may claim those rows as delivered.

| Requirement | Owner in this plan | Binding text and deferral justification |
|---|---|---|
| **PDF-001** | **E1 acquisition** | Every network download and `USER_PATH` ingest writes a uniquely named temporary file in the **same directory as the final store**, validates it, and atomically replaces/promotes only after validation. |
| **PDF-002** | **E1 acquisition** | Reuse is an exact manifest binding, not a filename cache hit: normalized DOI (when present), source checksum, byte length, validation profile **and version**, media type, final workspace-relative path, and workspace binding all match. |
| **PDF-003** | **E1 acquisition** | Every operation returns a versioned structured outcome with stage, status, source class, OA/access state, attempts, validation result, checksum, and sanitized error. |
| **PDF-004** | **E1 acquisition** | `not_open_access`/unresolved, `not_found`, `network_failed`, `invalid_pdf`, `identity_mismatch`, `reused`, and `success` remain distinguishable. `extraction_failed` is an E2 status and is not fabricated by E1. |
| **PDF-005** | **E1 acquisition** | Structural validation applies equally to network downloads, `USER_PATH` ingest, and reused artifacts; a cache hit cannot bypass it. |
| **PDF-006** | **E1 acquisition** | Invalid or failed temporary files are removed, while a previously valid final file remains untouched. |
| **PDF-007** | **E1 acquisition** | Owned HTTP clients, streams, and file handles close on success, exception, and cancellation; externally supplied clients retain their caller-owned lifecycle. |
| **PDF-008** | **E2/E3 — deferred** | Extraction failure structure and usefulness thresholds are extraction concerns. E1 does not run an engine or emit an extraction success/stub; E2 must add the evidence and tests. |
| **PDF-009** | **E2/E3 — deferred** | Requested/effective extraction engines and fallback reasons belong to the extraction boundary. E1 only records acquisition attempts and access provenance. |
| **PDF-010** | **E2/E3 — deferred** | Study, DOI, bibliographic metadata, checksum, and engine/version flow into extracted frontmatter and the registered `DocumentManifestArtifact` during extraction. E2's `DocumentManifestArtifact` emitter is the integration point for PDF-010/011 lineage; E1 supplies source fields but is not that artifact. |
| **PDF-011** | **E2/E3 — deferred** | MCP engine selection, rejection of unsupported engines, and preservation of canonical metadata through the extracted artifact or inseparable sidecar are E2 integration work. E1 does not claim an MCP extraction result. |
| **PDF-012** | **E2/E3 — deferred** | `pyyaml` declaration and extraction-side packaging are handled with the E2 extraction implementation and its clean-wheel tests. E1 does not add extraction dependencies. |
| **PDF-013** | **E1 acquisition** | Smart names and duplicate metadata cannot overwrite another identity; authoritative storage is content/identity addressed and collision-safe, including concurrent runs. |
| **PDF-014** | **E1 acquisition** | Summary and acquisition-manifest writes are atomic and machine-readable. Success counts include only committed, validated byte records. |
| **PDF-015** | **E1 acquisition** | OA status and article identity are never fabricated from an HTTP response, filename, title similarity, or gateway/proxy configuration. |
| **PDF-016** | **E1 acquisition** | Institutional URL gateways and transport-level forward proxies are separately configured, validated, recorded, and tested; one value cannot implicitly serve both roles. |
| **PDF-017** | **E1 acquisition** | Failure to resolve a legal OA URL is `UNRESOLVED`/`unresolved_no_legal_oa_copy_found`, never confirmed paywall or confirmed restriction. |

The remainder of this handoff allocates implementation and test obligations for
the E1 rows. The deferred rows must be allocated and evidenced in the E2/E3
packets before Packet E can be called complete.

## 2. Governing invariants

1. `study_id` comes from the accepted screening/corpus lineage; the PDF kit does
   not mint or infer it from a DOI, title, filename, URL, or array position.
2. A path is a location, not document identity.
3. `source_sha256` is calculated from the bytes that were actually validated.
4. A reusable document is bound to the complete reuse tuple in §7.2, not to a
   filename or a path that happens to exist.
5. Failure to resolve a legal OA copy is `UNRESOLVED`, not proof of a paywall.
6. No invalid, partial, HTML, identity-mismatched, or uncommitted file becomes
   authoritative output.
7. Publication is fail-closed and preserves every previously committed valid
   artifact and manifest.
8. A failed batch is still a real, machine-readable outcome. Zero committed
   records means `FAILED`; it is never an empty `SUCCESS`.
9. Every committed path is relative to one caller-supplied canonical workspace
   root and is serialized as a workspace-relative POSIX path.
10. Required tests use local fixtures and fake transports; no network is needed.

## 3. Input contract

The acquisition command receives one immutable request per study. The request
is rejected before transport or filesystem I/O when its parent or path binding
is invalid.

| Field | Requirement |
|---|---|
| `workspace_id` | Must equal the accepted parent workspace and use the registered workspace identifier form. |
| `workspace_root` | Required absolute, caller-supplied canonical workspace root. It is resolved and bound to the accepted `workspace_id` before use; it is never inferred from process CWD, title, DOI, or a relative path. |
| `run_id` | The acquisition run ID; must be distinct from study/document IDs and must be stable for an exact replay. |
| `study_id` | Must be included by the accepted screening decisions and exist in the accepted corpus snapshot. |
| `protocol_fingerprint` | Must equal both accepted parents. |
| `corpus_fingerprint` | Must equal both accepted parents. |
| `inputs` | Exact artifact ID and SHA-256 of the direct screening parent; the corpus parent is also listed because it supplies study identity and metadata. Each hash is recomputed with the harness canonical fingerprint function. |
| `doi` | Optional normalized lookup hint copied from corpus metadata, never document identity. The original may be retained as non-authoritative provenance. |
| `source_mode` | `DISCOVERY` or `USER_PATH`; it determines whether `source_path` is a permitted read-only input. |
| `source_path` | Optional explicit user-provided local PDF. It may be an explicitly permitted external read-only input, but it is never an output destination. It is mutually exclusive with discovery-only mode. |
| `access_assertion` | Required for `USER_PATH`; records `supplied_by` and the asserted `permission_basis` without claiming independent legal verification. |
| `validation_profile` | Named validation configuration. |
| `validation_profile_version` | Exact version of that profile; it is part of identity/reuse binding and cannot be inferred from the profile name. |

`workspace_root` is not serialized as a committed record path. It is the
security anchor used to resolve paths. The caller must provide a root whose
workspace binding is known to match the accepted parent; a caller-supplied
string alone is not sufficient if the workspace registry or parent metadata
binds a different root. A missing or inconsistent binding fails with the
appropriate lineage/path error before I/O.

The E1 verifier must load the exact accepted `ScreeningDecisionsArtifact` and
`CorpusSnapshotArtifact` by ID, validate their types and workspace, recompute
their canonical fingerprints, and check both the protocol and corpus
fingerprints. A missing, stale, cross-workspace, hash-mismatched, excluded, or
unknown-study parent is not a reason to fall back to a loose PDF lookup.

## 4. PDF-kit acquisition model

The canonical PDF kit owns these serialized models. Names may follow repository
conventions, but field semantics and conditions are fixed.

### 4.1 `AcquisitionStatus`

`AcquisitionStatus` is a committed per-item domain status. It is not a
replacement for the Contract v1 `OperationStatus` used for the batch envelope.

- `ACQUIRED`: new bytes validated and committed.
- `REUSED`: an exact manifest-bound committed artifact was reused, including an
  exact replay after a prior commit.
- `UNRESOLVED`: no legal OA PDF was resolved; this does not assert paywall or
  confirmed restriction.
- `NOT_FOUND`: a selected source was authoritatively absent.
- `NETWORK_FAILED`: transport attempts ended without a response sufficient to
  validate content.
- `INVALID_CONTENT`: returned or ingested bytes were not a valid PDF under the
  named profile.
- `IDENTITY_MISMATCH`: supplied or discovered metadata conflicts with the
  requested study's non-empty persistent identifiers.
- `CANCELLED`: the caller cancelled before commit.
- `FAILED`: an internal, filesystem, or commit failure prevented commit.

Only `ACQUIRED` and `REUSED` can produce a committed `AcquiredDocumentRecord`.
Failed and unresolved items remain visible in `item_outcomes` and errors, but
are not represented as byte-bearing documents.

For compatibility with the PDF-kit status vocabulary, the structured
acquisition outcome may project the statuses as follows: `ACQUIRED` → `success`,
`REUSED` → `reused`, `UNRESOLVED` → the truthful
`unresolved_no_legal_oa_copy_found`/`not_open_access` unresolved projection,
`NOT_FOUND` → `not_found`, `NETWORK_FAILED` → `network_failed`,
`INVALID_CONTENT` → `invalid_pdf`, and `IDENTITY_MISMATCH` →
`identity_mismatch`. The projection must retain `AcquisitionStatus` and
`AccessStatus`; it must not turn unresolved into confirmed paywall. The
`extraction_failed` status is reserved for E2.

### 4.2 `AccessStatus`

- `VERIFIED_OPEN_ACCESS`: provider evidence identifies a legal OA location.
- `USER_PROVIDED`: bytes were explicitly supplied; the recorded assertion is
  provenance, not independent legal verification.
- `UNRESOLVED`: legal availability could not be established.
- `RESTRICTED_CONFIRMED`: use only when a named source provides explicit,
  preserved evidence. It must never be inferred from lookup failure.

A successful HTTP response proves only that bytes were received and validated.
It does not by itself prove OA status or article identity. Gateway/proxy use is
recorded independently of `AccessStatus`.

### 4.3 `AcquisitionAttempt`

Each attempted source records:

- ordinal and source kind (`OPENALEX`, `UNPAYWALL`, `PUBLISHER_PATTERN`,
  `USER_PATH`, or `OTHER`);
- requested URL or a workspace-safe redacted representation;
- resolved URL when available;
- `gateway_used` and `forward_proxy_used` as separate booleans/configuration
  references;
- observed media type and HTTP status when applicable;
- attempt result and bounded diagnostic code;
- provider OA/licence evidence as received, without fabrication.

Secrets, access tokens, cookies, and proxy credentials must not be serialized.
Attempt timestamps are provenance only and must not participate in logical IDs,
the source-payload hash, or the idempotency key. Attempt order may be preserved
for audit but cannot change document identity.

### 4.4 `AcquiredDocumentRecord`

A byte-bearing committed record has the following required fields. The
`acquisition_status` field is committed on every record and is `ACQUIRED` or
`REUSED`:

```text
document_id
study_id
source_kind                    # USER_PATH for local ingest
source_sha256                  # sha256:<64 lowercase hex of validated bytes>
byte_length
media_type                     # application/pdf
workspace_relative_path        # final path, workspace-relative POSIX
acquisition_status             # ACQUIRED | REUSED
access_status
access_assertion               # object or null; required for USER_PATH
selected_source_url            # string, or null/absent for USER_PATH
selected_source                # URL for network source; relative path for USER_PATH
validation_profile
validation_profile_version
acquisition_method              # MethodProvenance-compatible
attempts
```

The conditional `USER_PATH` rule is normative:

- `source_kind` MUST be `USER_PATH`;
- `selected_source_url` MUST be `null` or absent, never a fabricated URL;
- `selected_source` MUST be the supplied path represented as a
  workspace-relative POSIX path (or an explicitly redacted external-input
  reference), never an absolute path in the committed record;
- `access_status` MUST be `USER_PROVIDED`;
- `access_assertion` MUST be committed with `supplied_by` and the asserted
  `permission_basis`; it is provenance, not a legal determination.

For a network source, `selected_source_url` is required when a source was
selected, and `access_assertion` may be null/absent. `selected_source` is the
source selected for the attempt; it is never used as `document_id`.

`source_sha256` is calculated from the exact bytes that passed the enabled
validation profile. Paths are workspace-relative, portable POSIX paths. A
committed record must not contain an absolute path, a `..` component, a drive
prefix, or a symlink that resolves outside the canonical workspace root.

### 4.5 Per-item outcomes and batch outcome

The manifest has a committed `item_outcomes` list with one entry for every
requested study. Each entry contains at least `study_id`, `source_kind`,
`acquisition_status`, `attempts`, the selected source when one exists, and a
bounded error or warning when applicable. This preserves negative and
unresolved results instead of omitting them.

The `records` list contains only committed byte records. It therefore contains
one or more records for a successful or partial run, and **zero records for an
all-failure run only when the manifest still carries the failed item outcomes**.
The manifest itself is always published for an all-failure run:

```text
records = []
operation.status = FAILED
errors = [at least one structured error]
item_outcomes = [one or more non-success outcomes]
```

A missing manifest, an empty successful manifest, and a published
zero-record/failed outcome are three distinguishable states. The third is the
required fail-closed representation of “no success”; it is not omitted and is
not treated as success.

The batch envelope uses the harness `OperationStatus` semantics, not a custom
batch success spelling:

- every requested item committed and no degradation → `SUCCESS`;
- at least one committed item and at least one unresolved, failed, cancelled,
  or otherwise degraded item → `PARTIAL`, with a warning or error explaining
  the degradation;
- zero committed items because all items failed or were unresolved → `FAILED`,
  with structured errors, while still publishing the fail-closed manifest;
- caller cancellation before commit → `CANCELLED`, unless a committed subset
  already exists, in which case the result is `PARTIAL` plus the explicit
  cancellation item outcome.

`ERROR` and `FAILED` are the canonical hard-failure aliases permitted by the
Contract v1 envelope; E1 uses `FAILED` for its operation-level fail-closed
branch. API and CLI JSON modes MUST expose the same batch `OperationStatus`,
per-item `AcquisitionStatus`, errors, warnings, and manifest reference. Human
tables may add labels, but they may not change these values. Acquisition is
intentionally **unsupported on MCP in E1**; §4.7 defines the capability
declaration and fail-closed MCP outcome.

### 4.6 `AcquiredDocumentManifest` and E2 integration

The manifest is a kit-owned, self-describing object. It has its own
`schema_version` and a `manifest_type` (for example,
`pdf_acquisition_manifest`); that type is not a Contract v1 `artifact_type`.
The E1 publisher validates the object with the kit-owned schema and does not
send it through the frozen harness acceptance/chain registries.

The manifest contains:

- `schema_version`, `manifest_type`, and deterministic `manifest_id`;
- workspace, run, protocol, and corpus context;
- exact immutable references to the accepted `CorpusSnapshotArtifact` and
  `ScreeningDecisionsArtifact`, including recomputed SHA-256 values;
- `parent_lineage_sha256`, a fingerprint over those exact references;
- producer package, version, and commit;
- `records` and `item_outcomes`;
- a canonical stable payload fingerprint and a non-self-referential
  `artifact_checksum` over the canonical manifest with that field set to null;
- batch `OperationStatus`, errors, warnings, and the idempotency key.

#### Parent references and stale-lineage rejection

`parent_refs` MUST contain entries equivalent to:

```json
{
  "corpus_snapshot": {
    "artifact_id": "<accepted ART-...>",
    "artifact_type": "corpus_snapshot",
    "sha256": "sha256:<canonical fingerprint of accepted payload>",
    "workspace_id": "<accepted workspace_id>",
    "protocol_fingerprint": "sha256:...",
    "corpus_fingerprint": "sha256:..."
  },
  "screening_decisions": {
    "artifact_id": "<accepted ART-...>",
    "artifact_type": "screening_decisions",
    "sha256": "sha256:<canonical fingerprint of accepted payload>",
    "workspace_id": "<accepted workspace_id>",
    "protocol_fingerprint": "sha256:...",
    "corpus_fingerprint": "sha256:..."
  }
}
```

`parent_lineage_sha256` is computed with the harness helper:

```text
parent_lineage_sha256 = canonical_fingerprint(parent_refs)
```

The individual parent hashes and the aggregate parent-lineage field are checked
against the accepted workspace registry and freshly recomputed parent payloads
before any manifest publication. A missing parent, stale registry entry,
cross-workspace parent, fingerprint mismatch, parent-hash mismatch, or study
not present in the accepted screening/corpus lineage MUST fail before the
manifest is published. This is the E1 implementation of the parent and
fingerprint portions of XC-006..XC-011 and XC-016..XC-021; it does not add a
new Contract type.

#### Manifest identity

The kit-owned manifest ID is deterministic over the manifest schema version,
workspace, run, exact parent references, and the normalized acquisition-record
set. A concrete adapter MUST use canonical JSON bytes and record its algorithm
version:

```text
normalized_acquisition_records = sorted logical item records by study_id,
                                  then document_id when present
manifest_identity_payload = {
  "schema_version": <pdf-acquisition schema version>,
  "workspace_id": <accepted workspace_id>,
  "run_id": <run_id>,
  "parent_refs": <canonical parent_refs above>,
  "acquisition_records": <normalized_acquisition_records>
}
manifest_id = "ACQ-" + sha256(canonical_json_bytes(manifest_identity_payload)).hexdigest()[:32]
```

`acquisition_records` is a canonical set-like view containing every requested
item's stable study/status/source binding, including failed and unresolved
items. It excludes timestamps, retry counters, response headers, and attempt
ordinals; those remain in the full manifest provenance but cannot make an exact
replay look like a new logical operation. The committed `records` list and
`item_outcomes` are sorted deterministically for the manifest payload, while
attempt history may retain its observed order inside each item. The stable source
binding includes the canonical `requested_source` and `selected_source`; a
changed non-volatile network URL or `USER_PATH` source therefore changes the
manifest identity when the key is recomputed, or is an idempotency conflict if a
persisted key is reused. In contrast, acquisition input order and retry/attempt
order are normalized and do not change the manifest identity. A same-run retry
with equivalent semantic input therefore has the same `manifest_id`; a
different non-volatile binding with the same key is never a replacement.

`manifest_payload_fingerprint` is the canonical fingerprint of the normalized
stable manifest payload. `artifact_checksum` deliberately does **not** hash the
final bytes that contain the checksum value. Define it with this exact,
non-circular construction:

```text
artifact_checksum_payload = copy(validated_manifest)
artifact_checksum_payload["artifact_checksum"] = null
artifact_checksum =
  "sha256:" + sha256(canonical_json_bytes(artifact_checksum_payload)).hexdigest()
```

The publisher sets the manifest's `artifact_checksum` field to that digest and
then atomically publishes the resulting object. A verifier loads the published
object, replaces its `artifact_checksum` value with null, recomputes the same
canonical digest, and fails closed on mismatch. Thus every other manifest field
is covered while the checksum value itself is excluded. This is a canonical
content checksum, not a checksum of the exact byte formatting written at the
manifest path, not a document ID, and not a replacement for the parent
fingerprint.

#### What E2 consumes and emits

After its own extraction validation, E2 consumes these committed fields from
the accepted E1 manifest (and preserves the manifest reference):

```text
document_id
study_id
source_sha256
byte_length
media_type
workspace_relative_path
validation_profile
validation_profile_version
access_status
selected_source_url
attempts
acquisition_method
```

For `USER_PATH`, E2 preserves the null/absent `selected_source_url`,
workspace-relative `selected_source`, and `access_assertion`; it must not invent
a URL. E2 emits the registered Contract v1 `DocumentManifestArtifact` only
after extraction has produced the required extracted path and extraction
method. The frozen `_REQUIRED_PARENT_TYPE` in both `acceptance.py` and
`chain.py` requires `document_manifest`'s Contract v1 parent to be
`screening_decisions`; that chaining remains unchanged.

The kit-owned acquisition manifest is therefore **not** added to the E2
`DocumentManifestArtifact.inputs` list. Its presence in the workspace registry
as a Contract artifact would make the frozen parent check fail. Instead, every
E2 document record (or its inseparable, explicitly versioned provenance
sidecar) MUST embed the reference fields
`acquisition_manifest_id` and `acquisition_manifest_sha256`, and MUST preserve
the exact E1 `document_id` and source hash. Here
`acquisition_manifest_sha256` is the E1 `artifact_checksum` computed by the
null-excluded canonical construction above: E2 loads the manifest, sets a copy
of its `artifact_checksum` field to null, recomputes the digest with
`canonical_json_bytes`, and rejects a mismatch before embedding it. This is an
embedded lineage reference, not a Contract v1 parent edge. E2 verifies the E1
manifest checksum and its parent references before extraction and fails closed
if they are stale.

### 4.7 Declared MCP capability boundary

E1 chooses the explicit-unsupported option for MCP acquisition. The canonical
PDF kit remains the domain-service owner, but the shared capability registry
MUST declare `pdf_acquisition` with `mcp_supported=false`, the owning surface
as API/CLI, and the stable rejection code `UNSUPPORTED_CAPABILITY`. The
agent-kit owns only a thin capability declaration/rejection adapter; it MUST NOT
reimplement download, ingest, validation, storage, or manifest logic in the
harness or MCP layer.

Capability discovery and any acquisition-shaped MCP request MUST make the
boundary observable rather than silently omitting the operation. The rejection
is a standard JSON operation envelope with `operation="acquire_pdf"`,
`status="FAILED"`, no artifacts, and one non-retryable error whose code is
`UNSUPPORTED_CAPABILITY` and whose message states that E1 acquisition is not
available through MCP and names the API/CLI alternatives. The request MUST be
rejected before provider transport, temporary/final file creation, manifest
creation, or audit-success append. The API and CLI remain supported E1 surfaces
and route through the same public PDF-kit domain service. This is the explicit
unsupported difference declared and tested under VAL-003 and XC-031..XC-032,
not a semantic-parity claim. E1 makes no claim about E2 extraction on MCP; that
remains in the E2 packet.

## 5. Validation and identity checks

A candidate is eligible for commit only after all enabled checks pass:

1. non-empty stream and configured size bounds;
2. `%PDF-` magic-byte validation;
3. PDF EOF/truncation check;
4. structural parser validation under the named profile;
5. SHA-256 computed from the bytes actually validated;
6. requested study exists in the accepted corpus and screening parents;
7. non-empty persistent identifiers do not conflict;
8. final media type is `application/pdf` regardless of misleading URL suffix or
   response header.

The same structural checks apply to network downloads, `USER_PATH` ingest, and
reused artifacts. A reuse path cannot skip validation merely because a file
exists or its filename looks stable. A failed validation removes or quarantines
the staged data and cannot publish a byte record.

Title/author similarity may produce a warning. It cannot override a conflicting
DOI or establish identity on its own. A non-empty DOI conflict is
`IDENTITY_MISMATCH`; an unresolved DOI is not silently filled from a title or
filename. Missing OA/access evidence remains explicitly missing or unresolved.

## 6. Exact document identity

E1 MUST use the harness's actual identifier rule, not a private `DOC-` digest
formula. For a validated candidate:

```text
input = {
  "study_id": <accepted corpus study_id>,
  "source_sha256": "sha256:" + sha256_hex(validated_bytes),
  "media_type": "application/pdf"
}

document_id =
  primary_prefix(IdentifierKind.DOCUMENT)
  + sha256(canonical_json_bytes({
      "algorithm_version": <recorded algorithm version, default "v1">,
      "kind": "document",
      "workspace_namespace": <accepted parent workspace_id>,
      "input": input
    })).hexdigest()[:32]
```

The concrete prefix is `DOC-` because
`IdentifierKind.DOCUMENT.value == "document"` and
`primary_prefix(IdentifierKind.DOCUMENT) == "DOC-"`.

`workspace_namespace` has one exact meaning here: it is the string
`workspace_id` carried by both accepted parent artifacts after those parents
have been verified to agree. It is not the filesystem path, the project slug,
a title, a DOI, a run ID, or a separately invented namespace. The accepted
parent's `workspace_id` is the workspace namespace used by the contract
producers and by `deterministic_id` in `canonical.py`.

`input` is the canonical JSON object shown above. The implementation MUST use
`canonical_json_bytes` semantics: UTF-8, lexicographically sorted object keys,
no insignificant whitespace, normalized numbers, no NaN/Infinity, and preserved
array order unless an array is explicitly registered as set-like. The payload
field set is `algorithm_version`, `input`, `kind`, and `workspace_namespace`;
the nested `input` field set is `media_type`, `source_sha256`, and `study_id`.
Those lists describe fields, not a hand-written serialization order. Key order
is determined solely by the helper's recursive `sort_keys=True`: the actual
top-level order is `algorithm_version`, `input`, `kind`,
`workspace_namespace`, and the nested order is `media_type`, `source_sha256`,
`study_id`. Callers must not construct a different JSON representation, hash a
preformatted JSON string, or hash a URL/filename. `source_sha256` is the
lower-case `sha256:`-prefixed hexadecimal digest of the exact validated bytes.

The kit MUST either call the harness `deterministic_id` helper or provide an
adapter proven byte-for-byte equivalent to it. The equivalent adapter MUST
have tests covering cross-workspace separation and invariance to URL, filename,
retry count/order, and acquisition input order. It MUST also prove that a
one-byte source mutation changes the ID and that the resulting value passes
`validate_identifier(IdentifierKind.DOCUMENT, document_id)` when E2 embeds it
in Contract v1. The `DOCUMENT` kind is registered; that makes the document ID
registrable/usable by Contract v1, but it does not make the E1 acquisition
manifest a registered Contract artifact. IDs remain opaque: consumers MUST NOT
parse the digest or infer study/source identity from its suffix.

If the algorithm version changes, the new version is part of the payload and
must be recorded. Migration of an old ID requires an explicit versioned
migration and lineage; it is not an in-place relabel.

### 6.1 Worked JSON examples

The following examples use illustrative identifiers; the 64-character values
are validly shaped hashes.

#### Local `USER_PATH` ingest

```json
{
  "manifest_type": "pdf_acquisition_manifest",
  "manifest_id": "ACQ-0123456789abcdef0123456789abcdef",
  "schema_version": "pdf-acquisition-manifest-v1",
  "workspace_id": "WSP-0123456789abcdef0123456789abcdef",
  "run_id": "RUN-0123456789abcdef0123456789abcdef",
  "parent_lineage_sha256": "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
  "idempotency_key": "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
  "records": [
    {
      "document_id": "DOC-33333333333333333333333333333333",
      "study_id": "STU-44444444444444444444444444444444",
      "source_kind": "USER_PATH",
      "source_sha256": "sha256:5555555555555555555555555555555555555555555555555555555555555555",
      "byte_length": 12345,
      "media_type": "application/pdf",
      "workspace_relative_path": "pdfs/acquired/DOC-33333333333333333333333333333333.pdf",
      "acquisition_status": "ACQUIRED",
      "access_status": "USER_PROVIDED",
      "access_assertion": {
        "supplied_by": "researcher@example.org",
        "permission_basis": "Researcher supplied an authorized local copy."
      },
      "selected_source_url": null,
      "selected_source": "inbox/supplied/paper.pdf",
      "validation_profile": "strict-pdf",
      "validation_profile_version": "1.0.0",
      "acquisition_method": "HUMAN",
      "attempts": [
        {
          "ordinal": 1,
          "source_kind": "USER_PATH",
          "requested_source": "inbox/supplied/paper.pdf",
          "result": "ACQUIRED"
        }
      ]
    }
  ],
  "item_outcomes": [
    {
      "study_id": "STU-44444444444444444444444444444444",
      "source_kind": "USER_PATH",
      "acquisition_status": "ACQUIRED",
      "document_id": "DOC-33333333333333333333333333333333"
    }
  ],
  "operation": {"status": "SUCCESS", "errors": [], "warnings": []}
}
```

#### All-failure batch

```json
{
  "manifest_type": "pdf_acquisition_manifest",
  "manifest_id": "ACQ-66666666666666666666666666666666",
  "schema_version": "pdf-acquisition-manifest-v1",
  "workspace_id": "WSP-0123456789abcdef0123456789abcdef",
  "run_id": "RUN-77777777777777777777777777777777",
  "parent_lineage_sha256": "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
  "idempotency_key": "sha256:8888888888888888888888888888888888888888888888888888888888888888",
  "records": [],
  "item_outcomes": [
    {
      "study_id": "STU-99999999999999999999999999999999",
      "source_kind": "OPENALEX",
      "acquisition_status": "UNRESOLVED",
      "selected_source_url": null,
      "attempts": [],
      "error": {
        "code": "UNRESOLVED_NO_LEGAL_OA_COPY_FOUND",
        "message": "No legal OA source was resolved; this is not a paywall determination."
      }
    }
  ],
  "operation": {
    "status": "FAILED",
    "errors": [
      {
        "code": "UNRESOLVED_NO_LEGAL_OA_COPY_FOUND",
        "message": "No requested study produced a committed PDF."
      }
    ],
    "warnings": []
  }
}
```

## 7. Workspace safety, reuse, atomicity, and recovery

### 7.1 Canonical workspace-root anchoring

Every workspace output, temporary file, rename, manifest write, and committed
path operation is anchored to the caller-supplied canonical `workspace_root`,
not process CWD. The root is resolved once and checked against the accepted
workspace binding before I/O. A path is accepted as a committed path only if
it is a relative POSIX path, has no absolute/drive/`..` component, and its
resolved real path remains inside the resolved root after symlink resolution.
A symlinked parent or final path that escapes the root is rejected with
`PATH_OUTSIDE_WORKSPACE` before a read/write that could escape.

A user may provide an external read-only source only when the capability and
permission are explicit. It is never a destination, never copied in place, and
never serialized as an absolute committed path. All destination and manifest
paths remain inside the workspace root. This is the E1 implementation of
XC-026..XC-029.

### 7.2 Exact reuse binding

Reuse is permitted only when an existing committed acquisition manifest and its
byte record are all available and the complete binding matches:

1. normalized DOI, including a match of “both absent” or “both present with the
   same normalized value”;
2. source checksum (`source_sha256`);
3. byte length;
4. validation profile **name and version**;
5. media type (`application/pdf`);
6. final workspace-relative POSIX path;
7. workspace binding (`workspace_id` and the caller-supplied canonical root
   binding).

`document_id` and manifest ID must also be recomputed and match. A filename
match, a DOI-only match, a profile-name-only match, a path-only match, a
changed byte, a changed profile version, or a workspace mismatch is not reuse.
Any mismatch forces a fresh acquisition in a collision-safe new final path or
fails closed; it never overwrites the prior valid record or silently adopts a
different binding. A reused artifact is structurally validated again under the
requested profile.

### 7.3 Commit state machine

For a byte-bearing item, publication is the following state machine. The
temporary file is in the **same directory as its final content-addressed
store**, not merely on the same filesystem, and has a unique name. The manifest
temporary is likewise in the manifest destination directory.

1. **Preflight:** verify the accepted parent lineage, workspace-root binding,
   study inclusion, source mode, path containment, configuration, and
   idempotency key. No transport or filesystem output is created before this
   succeeds.
2. **Stage:** stream/copy into a uniquely named same-directory temporary file,
   compute the byte length and SHA-256, flush/close safely, and never expose the
   temporary as authoritative.
3. **Validate:** run magic-byte, EOF/truncation, structural-profile, media-type,
   study, DOI/identity, size, and final-path checks against the staged bytes.
   A failure removes this attempt's temporary file and preserves prior output.
4. **Promote content:** atomically rename/replace the validated temporary file
   into a unique content/identity-addressed final path. If that path already
   contains the same validated identity, coalesce deterministically; never
   overwrite a different identity.
5. **Publish manifest:** build and validate the kit-owned manifest, stage it in
   its destination directory, and atomically replace the manifest. **The
   successfully replaced manifest is the commit marker.** Bytes without a
   committed manifest are non-authoritative and may be quarantined or cleaned
   later.
6. **Post-commit journal/audit:** append exactly one canonical
   workspace-manager audit event for the successful manifest commit, using the
   real kit/agent identity, parent IDs/hashes, manifest ID/checksum, operation
   status, and idempotency key. The event must not claim a Contract v1
   `DocumentManifestArtifact` was accepted.

For an all-failure run, steps 2–4 are skipped, but the fail-closed manifest is
still staged, atomically published, and followed by the appropriate canonical
failure/outcome event. It contains zero `records`, explicit `item_outcomes`, and
`OperationStatus=FAILED`. A failed manifest replace is not a successful empty
batch.

All file handles and owned clients are closed on success, retry, exception, and
cancellation. Cleanup removes only this operation's temporary/orphan output and
never deletes a prior valid final or manifest.

### 7.4 Idempotency and recovery

The idempotency key is deterministic over the acquisition schema version,
workspace, run, study, and a canonical source-payload hash:

```text
source_payload = {
  "source_kind": <DISCOVERY or USER_PATH>,
  "normalized_doi": <normalized DOI or null>,
  "requested_source": <canonical requested source or null>,
  "selected_source": <canonical selected source or null>,
  "expected_media_type": "application/pdf",
  "validation_profile": <profile name>,
  "validation_profile_version": <profile version>,
  "workspace_relative_final_path": <final path or proposed path>
}
source_payload_hash = canonical_fingerprint(source_payload)
idempotency_key = canonical_fingerprint({
  "schema_version": <pdf-acquisition schema version>,
  "workspace_id": <accepted workspace_id>,
  "run_id": <run_id>,
  "study_id": <study_id>,
  "source_payload_hash": source_payload_hash
})
```

The source payload deliberately excludes timestamps, retry count, attempt
ordinal, response headers, and transient diagnostics. A changed non-volatile
payload under an existing key is `IDEMPOTENCY_CONFLICT`; it cannot overwrite
or relabel the earlier manifest.

The key and deterministic manifest ID are persisted before recovery actions.
An exact replay computes the same key and manifest ID, detects the existing
manifest, verifies its stable fingerprint and bound bytes, and reports the item
as `REUSED` without downloading, rewriting, or duplicating the manifest. If the
manifest exists but its bytes are missing/invalid, or the key points to a
different non-volatile payload, recovery fails closed.

If manifest replacement succeeds but the post-commit audit append fails, the
manifest remains the authoritative commit marker. The operation reports a
structured recovery/partial outcome and leaves the prior valid state intact.
A rerun with the same key finds the already-published manifest, checks whether
the canonical audit event for `(manifest_id, idempotency_key)` exists, and
either:

- returns `REUSED` and completes the missing audit append exactly once; or
- returns an already-idempotent `REUSED` result without appending a duplicate.

If the process dies before manifest replacement, no new manifest is
authoritative; staged files are cleaned or recovered under the same key. If it
dies after content promotion but before manifest replacement, the content is an
orphan until the deterministic key/manifest check either safely recovers it or
removes it; it is never treated as committed. If the audit response is lost
after a successful append, the same lookup makes the replay idempotent.

### 7.5 Collision, naming, and lifecycle requirements

Authoritative storage is addressed by document/content identity, not a smart
filename. Distinct study/document identities cannot overwrite one another.
Concurrent duplicate logical inputs—same workspace, run, accepted `study_id`,
complete source binding, and validated bytes—deterministically coalesce to
exactly one committed artifact carrying the one deterministic `DOC-*` identity;
concurrent distinct identities receive separate paths or a conflict-safe
explicit result. The test must cover both same-smart-name/different-identity
and duplicate-DOI/concurrent-input cases.

Owned aiohttp/session and `AcademicHttpClient` instances close on success,
retry, exception, and cancellation. Externally supplied clients are not closed
by E1. Streams and temporary files close/clean on the same paths. A valid
existing final file is never removed by a failed refresh.

## 8. Implementation task packet

```text
TASK_ID: WP01-E1
OBJECTIVE: Implement the deterministic acquired-document boundary in the
  canonical scholar-pdf-kit, add the declared thin MCP rejection in the
  canonical scholar-agent-kit, and synchronize both into the harness.
OWNER_SURFACE: nexus-scholar-org/scholar-pdf-kit
MCP_ADAPTER_OWNER_SURFACE: nexus-scholar-org/scholar-agent-kit
  (capability declaration/rejection only)
DEPENDENCIES_AND_EVIDENCE:
  - Contract v1 baseline and identifier registry
  - accepted ScreeningDecisionsArtifact and CorpusSnapshotArtifact
  - current PDF behavior characterized at pin
    9fa9e00361cd6d3bd7aec3c5a079db80f0287f58
GOVERNING_REQUIREMENTS:
  - the normative allocation table in §1.2: only its E1 rows are E1 scope
  - the deferred PDF-008..PDF-012 rows are handed to E2/E3 and are not E1 work
  - this document sections 2-7
  - toolkit synchronization rule in DEVELOPER_COMPASS.md
OUTPUTS:
  - typed acquisition request/outcome/attempt/record/manifest models
  - exact harness-compatible deterministic document identity
  - kit-owned acquisition manifest with parent lineage and embedded E2 reference
  - atomic same-directory staging, content promotion, manifest commit, and recovery
  - exact-manifest reuse and workspace-root containment
  - structured CLI/API output with the same statuses and backward-compatible
    projection as needed
  - an E1 capability-registry declaration and thin MCP rejection for
    acquisition, without implementing PDF domain logic in the adapter
  - local-fixture tests and public documentation
```

### Allowed canonical PDF-kit paths for the future implementation

- `src/scholar_pdf/` acquisition, models, downloader, validator, CLI, and public
  exports;
- `tests/` focused acquisition/atomicity/identity/path/recovery tests and local
  fixtures;
- `README.md` and package-owned documentation;
- `pyproject.toml` only for a demonstrated runtime/test dependency.

### Allowed canonical MCP-adapter path for the future implementation

- canonical `nexus-scholar-org/scholar-agent-kit` `src/scholar_agent/` capability
  declaration and thin acquisition-rejection wrapper only;
- focused canonical agent-kit tests for the capability registry, exact MCP
  rejection envelope, and zero-I/O boundary;
- canonical agent-kit documentation needed to keep its public surface truthful.

### Allowed harness paths after the canonical kit changes land

- `tools/scholar-pdf-kit/` synchronized snapshot;
- `tools/scholar-agent-kit/` synchronized snapshot when the E1 MCP boundary
  changes the adapter;
- `.agents/plugins/nexus-scholar/plugins.json` full-SHA pins for every changed
  canonical kit;
- generated `packaging/nexus-scholar/nexus_scholar_pins.json`;
- focused cross-kit/conformance tests and PDF-kit skill documentation;
- `docs/kits_surface_matrix.md`, limited to the E1-relevant PDF
  acquisition/API/CLI/MCP capability, status, and manifest rows;
- this handoff and the compass only when status evidence changes.

### Forbidden paths and scope

- Contract v1 models, generated schemas, identifier registry, or golden fixture;
- RAG/chunk/index/claim implementation;
- workspaces or scientific result files;
- unrelated toolkit cleanup;
- vendored-only PDF-kit or MCP-adapter changes;
- network-dependent required tests.

## 9. Acceptance criteria

- **E1-001 Parent binding and manifest boundary:** missing, stale, cross-
  workspace, fingerprint-mismatched, excluded, or unknown studies fail before
  publication; the E1 manifest is kit-owned rather than a frozen Contract type.
- **E1-002 Deterministic identity:** the same study plus identical bytes yields
  the same harness-compatible `DOC-*` ID across URL, filename, retry/attempt
  order, and acquisition input order. Retry/attempt-order and acquisition
  input-order normalization leave the manifest ID unchanged. A changed
  non-volatile requested/selected source changes the manifest ID or produces
  the specified idempotency conflict, and another workspace yields a distinct
  document ID.
- **E1-003 Byte sensitivity:** one-byte content mutation changes the hash and
  document ID.
- **E1-004 Study separation:** identical bytes associated with two study IDs
  remain two distinct document identities.
- **E1-005 Exact reuse:** reuse succeeds only through a complete matching
  committed manifest, including normalized DOI, checksum, length, profile and
  version, media type, final path, and workspace binding; filename-only,
  DOI-only, profile-version-only, and path-only reuse fail.
- **E1-006 Truthful access and configuration:** unresolved discovery is not
  reported as confirmed restricted/paywalled; gateway and forward-proxy use are
  independent, and no OA or identity fact is fabricated.
- **E1-007 Content validation:** HTML, truncated, magic-byte-invalid, and
  structurally invalid content never commits on download, ingest, or reuse.
- **E1-008 Identity conflict:** a conflicting non-empty DOI yields
  `IDENTITY_MISMATCH`; title similarity cannot bypass it.
- **E1-009 Atomicity and recovery:** failures injected at download,
  validation, content move, manifest replace, and post-commit audit append leave
  either the prior valid state or the explicitly recoverable committed state;
  post-manifest/pre-audit recovery is idempotent and does not duplicate an
  artifact or event.
- **E1-010 Structured outcomes:** success, reuse, unresolved, `NOT_FOUND`,
  network failure, invalid content, identity mismatch, cancellation, internal
  failure, all-failure, and partial outcomes remain distinguishable on the
  supported API and CLI surfaces and use the canonical `OperationStatus`
  envelope.
- **E1-011 Resource safety:** owned HTTP clients, streams, file handles, and
  temporary files close on success, retry, cancellation, and exception;
  caller-owned clients retain ownership.
- **E1-012 Collision safety:** smart names or duplicate metadata cannot
  overwrite another document; concurrent distinct identities are isolated and
  duplicate logical inputs coalesce to exactly one artifact with the
  deterministic document identity.
- **E1-013 Portability and containment:** committed paths are
  workspace-relative POSIX paths, traversal/symlink escapes are rejected, and
  manifests round-trip on Windows and POSIX without absolute paths.
- **E1-014 Packaging:** an isolated wheel can import the public acquisition
  models and run `scholar-pdf --help` without the repository checkout.
- **E1-015 Synchronization and lineage:** every changed canonical kit commit,
  vendored tree, full-SHA plugin pin, and generated metapackage pin agree; the
  manifest parent hashes, null-excluded `artifact_checksum`, and E2 embedded
  acquisition-manifest reference agree exactly; the frozen Contract v1 chain
  map is unchanged.
- **E1-016 Declared MCP boundary:** the capability registry and E1 surface docs
  mark PDF acquisition unsupported on MCP; an acquisition-shaped MCP request
  returns the declared `FAILED`/`UNSUPPORTED_CAPABILITY` envelope before any
  provider or filesystem I/O, while API/CLI acquisition remains supported.

## 10. Traceability and mandatory negative tests (VAL-001)

Every E1 acceptance criterion maps to at least one stable automated test ID.
The positive fixture IDs below are deliberately small; all required negative
and fault cases have explicit `E1-NEG-###` identifiers. Tests are hermetic,
scriptable, and use fake transports/local temporary workspaces.

Positive fixture IDs:

- `E1-POS-001`: accepted `USER_PATH` PDF commits, validates, and round-trips;
- `E1-POS-002`: an exact second run detects the committed manifest and returns
  `REUSED` with the same IDs and hashes;
- `E1-POS-003`: a valid fake-transport network download commits with complete
  source and access provenance;
- `E1-POS-004`: a clean isolated wheel imports the public models and runs the
  `scholar-pdf --help` entrypoint.

### 10.1 Acceptance-criterion traceability

| Criterion | Required test IDs |
|---|---|
| E1-001 | `E1-NEG-001`, `E1-NEG-002`, `E1-NEG-003`, `E1-NEG-004`, `E1-NEG-044` |
| E1-002 | `E1-POS-002`, `E1-NEG-005`, `E1-NEG-045` |
| E1-003 | `E1-NEG-006` |
| E1-004 | `E1-NEG-007` |
| E1-005 | `E1-NEG-008`, `E1-NEG-009`, `E1-NEG-010`, `E1-NEG-011`, `E1-NEG-038`, `E1-NEG-040` |
| E1-006 | `E1-NEG-012`, `E1-NEG-033`, `E1-NEG-046` |
| E1-007 | `E1-NEG-023`, `E1-NEG-038` |
| E1-008 | `E1-NEG-013` |
| E1-009 | `E1-NEG-021`, `E1-NEG-022`, `E1-NEG-024`, `E1-NEG-025`, `E1-NEG-026`, `E1-NEG-035` |
| E1-010 | `E1-NEG-014`, `E1-NEG-015`, `E1-NEG-031`, `E1-NEG-032`, `E1-NEG-041`, `E1-NEG-042` |
| E1-011 | `E1-NEG-016`, `E1-NEG-017`, `E1-NEG-018`, `E1-NEG-042` |
| E1-012 | `E1-NEG-019`, `E1-NEG-039` |
| E1-013 | `E1-NEG-027`, `E1-NEG-028`, `E1-NEG-029`, `E1-NEG-043` |
| E1-014 | `E1-POS-004`, `E1-NEG-030` |
| E1-015 | `E1-NEG-004`, `E1-NEG-026`, `E1-NEG-030`, `E1-NEG-040`, `E1-NEG-044`, `E1-NEG-047` |
| E1-016 | `E1-NEG-047` |

The E1 rows in §1.2 map to the same evidence: PDF-001 to
`E1-NEG-021/022/024/025`; PDF-002 to `E1-NEG-008..011/038/040`; PDF-003 and
PDF-004 to `E1-NEG-014/015/022/023/041`; PDF-005 to
`E1-NEG-023/038`; PDF-006 to `E1-NEG-021/023/024/025`; PDF-007 to
`E1-NEG-016/017/018/042`; PDF-013 to `E1-NEG-019/039`; PDF-014 to
`E1-NEG-024/025/032/035`; PDF-015 to `E1-NEG-013/033/046`; PDF-016 to
`E1-NEG-012`; and PDF-017 to `E1-NEG-014/033`. PDF-008 through PDF-012 have
no E1 test claim and must be traced in their E2/E3 packets.

### 10.2 Stable negative-test ledger

The following IDs are required test names (or stable parametrized case IDs), not
claims that the tests already pass in this documentation-only repair packet.
Each test asserts the stated status, no-publication condition, cleanup, and
lineage outcome.

| Test ID | Required case and assertion |
|---|---|
| `E1-NEG-001` | Missing parent, missing/unknown study, and excluded study: reject before transport or file write; no new manifest. |
| `E1-NEG-002` | Cross-workspace parent: reject before publication; do not mint a document ID in the wrong namespace. |
| `E1-NEG-003` | Protocol or corpus fingerprint mismatch: reject before I/O; prior valid output remains. |
| `E1-NEG-004` | Parent artifact ID/hash mismatch or stale registry entry: reject; no parent is silently replaced. |
| `E1-NEG-005` | With the same parents, workspace, run, study, and bytes: (a) URL, filename, retry/attempt-order, and acquisition input-order variations leave the `DOC-*` ID unchanged; (b) retry/attempt-order and acquisition input-order normalization leave the manifest ID unchanged; and (c) changing a non-volatile requested/selected source, including a network URL or `USER_PATH` source, changes the manifest ID, or an existing persisted key returns `IDEMPOTENCY_CONFLICT` without replacement. A golden payload also pins the exact `canonical_json_bytes` output and its sorted top-level/nested key order. |
| `E1-NEG-006` | One-byte mutation of otherwise identical bytes: source hash and document ID change. |
| `E1-NEG-007` | Identical bytes attached to two study IDs: two document IDs and records remain distinct. |
| `E1-NEG-008` | Filename-only reuse: an existing matching filename without the complete committed binding is not a cache hit. |
| `E1-NEG-009` | DOI-only reuse: matching normalized DOI while checksum/length/profile/path/workspace differs is rejected. |
| `E1-NEG-010` | Profile-version reuse mismatch: same profile name with a different version, or missing version, is rejected. |
| `E1-NEG-011` | Final-path or workspace-binding reuse mismatch: path-only/workspace-only matching is rejected. |
| `E1-NEG-012` | Gateway independence: institutional gateway rewriting and transport forward-proxy settings are configured, recorded, and tested separately; one value cannot serve both roles. |
| `E1-NEG-013` | Title-similarity bypass: a title/author match cannot override a conflicting non-empty DOI; return `IDENTITY_MISMATCH`. |
| `E1-NEG-014` | `NOT_FOUND`: an authoritatively absent selected source remains `NOT_FOUND`, distinct from unresolved and network failure. |
| `E1-NEG-015` | Internal/filesystem failure: return structured `FAILED`, preserve prior valid output, and never report success. |
| `E1-NEG-016` | Client cleanup on success: every owned HTTP client, stream, and handle closes after a committed result. |
| `E1-NEG-017` | Client cleanup on retry: bounded retry exhaustion closes owned clients and temporary state. |
| `E1-NEG-018` | Client cleanup on exception and cancellation: external clients remain caller-owned; owned resources close. |
| `E1-NEG-019` | Concurrent smart-name collision: distinct DOI/study identities receive distinct content/identity paths and no overwrite. |
| `E1-NEG-020` | Source equals destination: reject the unsafe ingest/copy without damaging the source or publishing a partial final. |
| `E1-NEG-021` | Interrupted/torn write: interruption before or during stage leaves no authoritative partial final; temp cleanup is safe. |
| `E1-NEG-022` | Download fault injection: timeout, cancellation, or exhausted transport produces a classified non-success and no committed bytes. |
| `E1-NEG-023` | Validation fault injection: HTML, truncated, magic-byte-invalid, malformed, and encrypted content is rejected under the profile. |

| `E1-NEG-024` | Content move/atomic rename fault: prior valid content and manifest remain readable; no partial final is exposed. |
| `E1-NEG-025` | Manifest replace fault: no newly authoritative manifest is published and staged manifest bytes are cleaned. |
| `E1-NEG-026` | Post-manifest/pre-audit recovery: manifest replace succeeds, audit append fails, rerun completes the one missing event or returns idempotent `REUSED` without duplication. |
| `E1-NEG-027` | Traversal containment: `..`, absolute, drive, and separator tricks in a workspace-relative path fail before read/write. |
| `E1-NEG-028` | Symlink containment: a symlinked parent or final path escaping the canonical root fails with `PATH_OUTSIDE_WORKSPACE`. |
| `E1-NEG-029` | Portability: the same manifest/records round-trip on Windows and POSIX with only workspace-relative POSIX paths. |
| `E1-NEG-030` | Sync/packaging drift: every changed canonical PDF/agent kit commit, vendored tree, full-SHA plugin pin, generated metapackage pin, and clean-wheel import are checked; any mismatch fails. |
| `E1-NEG-031` | API/CLI parity: JSON API and CLI report the same `OperationStatus`, per-item `AcquisitionStatus`, errors, warnings, and manifest reference. |
| `E1-NEG-032` | All-failure batch: publish a fail-closed manifest with `records=[]`, non-success `item_outcomes`, and `OperationStatus=FAILED`; distinguish it from a missing manifest. |
| `E1-NEG-033` | Unresolved legal OA lookup is `UNRESOLVED`/unresolved-not-found, never `RESTRICTED_CONFIRMED`, “paywalled”, or an empty success. |
| `E1-NEG-034` | Idempotency conflict: same key with a changed non-volatile source payload fails and never overwrites the earlier manifest. |
| `E1-NEG-035` | Exact replay: same key/manifest detects the published artifact and adds neither a duplicate byte artifact nor a duplicate canonical audit event. |
| `E1-NEG-036` | `USER_PATH` record validity: `source_kind=USER_PATH`, `selected_source_url=null`/absent, and `selected_source` is a relative path; no URL is fabricated. |
| `E1-NEG-037` | User-provided material without `access_assertion` (`supplied_by` and `permission_basis`) is rejected before commit. |
| `E1-NEG-038` | Reused bytes are structurally validated under the requested profile; a filename-only or cache-hit shortcut cannot bypass validation. |
| `E1-NEG-039` | Concurrent duplicate logical inputs (including duplicate DOI) with the same workspace, run, accepted study, complete source binding, and bytes produce exactly one committed byte artifact, one deterministic `DOC-*` identity, and one manifest/audit commit; every successful item outcome references that identity and nothing is overwritten. |
| `E1-NEG-040` | Manifest/file hash mutation: changing any manifest field other than `artifact_checksum` changes the null-excluded canonical digest, changing only the stored digest also fails verification, and reuse/recovery reject either mutation or changed byte payload rather than trusting a path. |
| `E1-NEG-041` | OperationStatus mapping: all-success is `SUCCESS`, mixed committed/degraded is `PARTIAL` with diagnostics, and all-failure is `FAILED`; `AcquisitionStatus` remains per-item. |
| `E1-NEG-042` | Cancellation before commit: status is `CANCELLED` (or `PARTIAL` only when a committed subset exists), and no cancelled item is authoritative. |
| `E1-NEG-043` | External read-only input and output containment: permitted input can be read, but every output resolves inside the canonical workspace root. |
| `E1-NEG-044` | Non-registry manifest: passing the kit-owned manifest to the frozen Contract acceptance/chain registries is rejected as an unsupported type; no registry entry is fabricated. |
| `E1-NEG-045` | Cross-workspace document ID: identical study/bytes in two accepted workspaces produce distinct `DOC-*` IDs. |
| `E1-NEG-046` | No fabrication: HTTP success, filename, title similarity, and proxy/gateway configuration cannot manufacture OA or article identity. |
| `E1-NEG-047` | MCP capability boundary: the registry, skill, and surface matrix declare acquisition unavailable on MCP; an acquisition-shaped MCP call returns the standard JSON envelope with `operation=acquire_pdf`, `status=FAILED`, no artifacts, and non-retryable `UNSUPPORTED_CAPABILITY`, with zero provider/filesystem/manifest/audit-success I/O; the same acquisition fixture remains supported through API and CLI. |

### 10.3 Required fault-injection points and recovery assertions

The required injection points are **download**, **validation**, **move**,
**manifest replace**, and **post-commit append**. The focused suite must inject a
failure at every point, not only at the end of a happy path:

| Point | Test IDs | Required state/action |
|---|---|---|
| Download/transport | `E1-NEG-022` | No authoritative final or manifest; classify `NETWORK_FAILED`, `CANCELLED`, or other exact item status. |
| Staged validation | `E1-NEG-023` | Remove/quarantine the same-directory temp; preserve the prior valid artifact. |
| Content move/rename | `E1-NEG-024` | No partial final; prior valid content/manifest remain readable. |
| Manifest replace | `E1-NEG-025` | No new committed manifest; staged manifest is cleaned. |
| Post-commit append | `E1-NEG-026` | Manifest is the commit marker; rerun finds it and appends/reconciles exactly one audit event. |

Additional exact-replay and all-failure checks are `E1-NEG-032` and
`E1-NEG-035`. This covers XC-017..XC-023 and the failure-focused requirements
in `11_validation_and_test_plan.md` without treating provider failure as an
empty successful result.

## 11. Validation commands

The implementation PR must report exact commands and counts. Adapt only the
canonical-kit command prefix to its checkout environment.

```powershell
# canonical scholar-pdf-kit checkout
uv run pytest tests/test_acquisition_contract.py tests/test_atomic_acquisition.py
uv run pytest
uv run ruff check src tests
uv build --wheel

# canonical scholar-agent-kit checkout (declared unsupported MCP boundary)
uv run pytest tests/test_mcp_acquisition_capability.py
uv run pytest
uv run ruff check src tests
uv build --wheel

# harness after canonical merges, vendoring, and pin updates
uv run python -c "import json; from scholar_harness.contracts.canonical import canonical_json_bytes; print(canonical_json_bytes({'algorithm_version':'v1','input':{'media_type':'application/pdf','source_sha256':'sha256:'+'0'*64,'study_id':'STU-x'},'kind':'document','workspace_namespace':'ws-x'}).decode())"
uv run pytest tests/test_cross_kit_contracts.py tests/test_contract_artifact_chain.py tests/conformance/test_mcp_tool_parity.py
uv run pytest
uv run ruff check scripts/
uv run python scripts/generate_contract_baseline.py --check
uv run python scripts/generate_contract_schemas.py --check
uv run python scripts/generate_two_study_contract_fixture.py --check
uv run python scripts/generate_nexus_scholar_pins.py --check

# documentation/review gate
git diff --check
git status --short
```

Required test names may differ, but the focused suite must cover every E1
acceptance criterion and the IDs in §10. All required tests are offline and
deterministic.

## 12. Repository and PR sequence

1. Create the implementation branch in the canonical PDF-kit repository fork.
2. Implement and validate E1 there; open a PR to
   `nexus-scholar-org/scholar-pdf-kit`.
3. Merge the canonical PDF-kit PR and record its full commit SHA.
4. In a separate agent-kit fork branch, implement only the declared MCP
   capability/rejection boundary and its conformance test; merge its PR to
   `nexus-scholar-org/scholar-agent-kit` and record that full commit SHA.
5. In a separate harness branch, synchronize every changed kit to its exact
   merged commit, update all affected `plugins.json` full-SHA pins, regenerate
   metapackage pins, update the E1 rows in `docs/kits_surface_matrix.md`, and
   add/run harness conformance tests.
6. Open a harness PR through the personal fork. Never push the feature branch to
   canonical `origin`.

Do not open the harness pin PR against an unmerged or floating kit revision.

## 13. Stop conditions and label semantics

The `BLOCKED_*` values below are planner/reviewer stop labels used to explain
why implementation cannot safely continue. They are **not** runtime
`OperationStatus` values, item `AcquisitionStatus` values, or substitutes for
the stable runtime error codes in the structured envelope.

Stop and report the named blocker when:

- Contract v1 must change: `BLOCKED_CONTRACT_VERSION_DECISION`;
- a parent artifact cannot be verified: `BLOCKED_PARENT_LINEAGE`;
- study identity requires title-only inference: `BLOCKED_STUDY_IDENTITY`;
- legal/OA status would have to be invented: `BLOCKED_ACCESS_PROVENANCE`;
- atomic publication cannot preserve a prior valid artifact:
  `BLOCKED_ATOMICITY_DESIGN`;
- a canonical PDF-kit or agent-kit repository required by E1 cannot be updated:
  `BLOCKED_CANONICAL_REPO`;
- the baseline check fails: `BLOCKED_BASELINE_DRIFT`.

A runtime provider, validation, filesystem, cancellation, or audit failure is
reported through `AcquisitionStatus`, `OperationStatus`, and bounded error codes;
it is not relabelled as a planner `BLOCKED_*` status.

## 14. Completion report

```text
Packet: WP01-E1
PDF-kit canonical repository, PR, and merge SHA:
Agent-kit canonical repository, PR, and merge SHA:
Acquisition schema/version:
Public API/CLI surface and MCP capability declaration:
Legacy projection retained/deprecated:
Files changed:
Acceptance criteria covered:
Negative fixtures added:
Targeted/full test results:
Wheel/import smoke result:
Harness vendored SHAs and pins:
Generated-pin check:
Remaining mismatches or blocked decisions:
Reviewer verdict: APPROVE | CHANGES_REQUESTED | BLOCKED
```

An `APPROVE` verdict means the acquisition boundary is safe for E2 to consume.
It does not claim that extracted text, chunks, indexing, or grounded evidence
are complete.
