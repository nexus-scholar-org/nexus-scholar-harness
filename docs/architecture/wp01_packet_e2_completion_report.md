# WP01-E2 Completion Report

- **Packet:** WP01-E2 — extracted-text boundary
- **Final verdict:** `APPROVE`
- **Closed on canonical harness main:** `0fb665558e0808d66348476eda2c927439a96be1`
- **Next packet:** WP01-E3 — chunk and index boundary

## Closure statement

WP01-E2 is complete across its three owning repositories. The PDF kit verifies
the accepted E1 acquisition manifest and exact committed PDF bytes, publishes a
deterministic `pdf-extraction-manifest-v1` sidecar, and constructs a
non-authoritative frozen-Contract `DocumentManifestArtifact` candidate. The
agent kit declares authoritative extraction unsupported on MCP and rejects it
without I/O. The harness vendors both canonical implementations at immutable
full-SHA pins and is the sole owner of Contract acceptance and publication.

This closure does not claim that chunking, indexing, retrieval, evidence,
claims, verification, or synthesis is complete. Those boundaries begin with
WP01-E3. The kit-owned `pdf_extraction_manifest` remains outside the frozen
Contract v1 registry.

## Canonical publication ledger

| Stage | Canonical repository / PR | Merge commit | Harness evidence |
|---|---|---|---|
| E2 extraction domain | `nexus-scholar-org/scholar-pdf-kit` [PR #2](https://github.com/nexus-scholar-org/scholar-pdf-kit/pull/2) | `6ec6e3bb45612b40498772124de2ebc16717eb56` | Parent-bound extraction, `EXT-*` sidecar, deterministic non-authoritative candidate, atomicity and recovery tests. |
| PDF-kit CI follow-up | `nexus-scholar-org/scholar-pdf-kit` [PR #3](https://github.com/nexus-scholar-org/scholar-pdf-kit/pull/3) | `0430ee40c491edbb055af4ab068637275aada476` | Current vendored/pinned PDF-kit tree; dependency-only changes now trigger CI. |
| E2 MCP declaration/rejection | `nexus-scholar-org/scholar-agent-kit` [PR #2](https://github.com/nexus-scholar-org/scholar-agent-kit/pull/2) | `deebfad995ba88bbd748be9beddd1aa2b8a51264` | `pdf_extraction` declaration, zero-I/O rejection, truthful authoritative alternatives, legacy tool marked non-authoritative. |
| E2 harness adoption | `nexus-scholar-org/nexus-scholar-harness` [PR #50](https://github.com/nexus-scholar-org/nexus-scholar-harness/pull/50) | `0fb665558e0808d66348476eda2c927439a96be1` | Bounded acceptance adapter, exact vendoring/pins, E2 conformance, surface parity, distribution wheel gates. |

The frozen Contract v1 models, registries, generated schemas, golden fixture,
baseline, and locked WP01 adoption handoff remained unchanged.

## §14 completion record

### Extraction schema, identity, and placement

- Manifest schema/type: `pdf-extraction-manifest-v1` /
  `pdf_extraction_manifest`.
- Manifest identity: deterministic `EXT-*` ID.
- Placement: `literature/extraction/<run_id>/<EXT-…>.json`.
- Document identity: the accepted E1 `DOC-*` identity is reused and checked
  against the exact E1 source SHA-256.
- Extracted output: identity-addressed workspace-relative Markdown or TEI XML
  with bound frontmatter and recorded content checksum.

### Public surfaces and ownership

- Authoritative Python API:
  `scholar_pdf.extraction.PDFExtractionService`.
- Authoritative CLI: `uv run scholar-pdf extract-run <config.json>
  --audit-logger <path-to-log_event.py>`.
- Candidate builder: `scholar_pdf.contract_candidate`; every candidate records
  `contract_acceptance="not_performed_by_kit"`.
- Harness acceptance:
  `scholar_harness.extraction_adapter.accept_extraction_candidate`, which parses
  through the frozen `DocumentManifestArtifact` and delegates all publication,
  registry mutation, idempotency, audit, and rollback to `accept_artifact`.
- MCP capability: `pdf_extraction`, `mcp_supported=false`, operation
  `extract_pdf`, one non-retryable `UNSUPPORTED_CAPABILITY` error, and no I/O.
- Legacy `scholar-pdf extract`, `scholar_pdf.extract`, and
  `nexus_extract_pdf` remain non-authoritative conveniences and produce no E2
  sidecar, accepted reference, or Contract claim.

### Extraction truth and engine provenance

The sidecar records requested/effective engine, engine version, ordered
fallback attempts and reasons, page/character counts, usefulness-profile
version, content status, failure reason, source checksum, extracted checksum,
and acquisition-manifest binding. Required offline tests use deterministic
fakes for optional provider/daemon engines; live GROBID/Docling behavior is not
claimed by this report.

### Acceptance and negative coverage

All `E2-001` through `E2-016` criteria and the stable
`E2-NEG-001` through `E2-NEG-046` ledger are allocated to executable kit or
harness evidence. In particular:

- malformed/stale acquisition lineage and changed source bytes fail before an
  authoritative extraction commit;
- empty, stub, or unusable text cannot become `VALID`;
- failed/OCR-pending records cannot fabricate an extracted path;
- exact replay is deterministic and conflicting replay fails closed;
- changed/non-portable paths, cross-workspace parents, and mismatched
  fingerprints are rejected;
- `pdf_extraction_manifest` is rejected by the frozen Contract registry;
- a failure in the harness acceptance window restores the registry and leaves
  no published artifact;
- MCP extraction rejection is deterministic, non-retryable, and zero-I/O;
- documentation, capability registry, tool inventory, vendored trees, and pins
  are executable parity gates.

### Validation evidence

- PDF kit at Stage-1 head: `192 passed, 7 skipped` on Windows; canonical Linux
  CI ran the seven symlink limbs and reported `199 passed, 0 failed` on Python
  3.11 and 3.12. Ruff, wheel, compile, process-recovery, replay, containment,
  and mutation gates passed.
- Agent kit: E1+E2 focused boundary `60 passed`; full suite `88 passed` with
  one isolated pre-existing protocol-validation failure. Wheel contents and
  `--help` boundary text were verified; the rejection path performed no I/O.
- Harness PR #50: E2 gate `45 passed`; required cross-kit line `77 passed`;
  full suite `609 passed, 5 skipped, 0 failures`; all four generated-file
  checks and script Ruff passed. Nine CI jobs passed across Ubuntu, Windows,
  and macOS Python 3.11/3.12 plus schema and wheel E2E jobs.
- Independent post-merge-gate review refreshed the PDF-kit pin to PR #3 and
  reran `122` focused cross-kit/frozen-contract tests before the final green CI
  run.

### Distribution and synchronization

| Kit | `plugins.json` and generated metapackage pin |
|---|---|
| `scholar-pdf-kit` | `0430ee40c491edbb055af4ab068637275aada476` |
| `scholar-agent-kit` | `deebfad995ba88bbd748be9beddd1aa2b8a51264` |

The vendoring fixtures enumerate the exact Git mode/blob/path rows for both
canonical commits. `scripts/generate_nexus_scholar_pins.py --check` passes.
The metapackage declares the extraction-time YAML dependency, builds a wheel,
and both wheel-provided entrypoints answer `--help` through `uvx --from
<wheel>`, which is the clean-wheel gate used by CI.

### Residual risks and deferred maintenance

No E2 blocker remains. The following are explicitly non-blocking and do not
weaken the accepted E2 boundary:

- live optional extraction engines are not offline gates;
- usefulness thresholds are versioned policy and must not be changed
  retroactively;
- the legacy raw-path MCP extractor still has a risky default output directory
  and remains non-authoritative;
- agent-kit has pre-existing protocol-validation, Ruff-configuration,
  dependency-metadata, and tracked egg-info maintenance debt;
- the packet's `E2-NEG-018` prose should be reconciled with the implemented
  successor/replay detail when that row is next edited; the executable behavior
  follows the normative §7.4 identity definition.

## Reviewer verdict

`APPROVE` — WP01-E2 is safe for WP01-E3 to consume. Exact acquired bytes bind
to truthful extracted text; the kit cannot claim Contract acceptance; the
harness cannot publish without the frozen parent, fingerprint, idempotency, and
atomicity gates; and no unmerged toolkit revision is pinned.

## Audit disposition

No `workspaces/<slug>/` research project was modified, so no scientific
workspace journal event applies. The durable audit trail is the canonical
PR/merge ledger, immutable pins, vendoring fixtures, completion report, and
executable conformance suite.
