# WP01-E1 Completion Report

- **Packet:** WP01-E1 — acquired-document boundary
- **Final verdict:** `APPROVE`
- **Closed on canonical harness main:** `baaeeb43977897924bd6ba9fda252e1bc9d464b8`
- **Next packet:** WP01-E2 — extracted-text boundary

## Closure statement

WP01-E1 is complete across its three owning repositories. The PDF kit now
acquires and commits exact PDF bytes for an accepted study; the agent kit
declares that acquisition is unsupported on MCP and rejects it without I/O; the
harness vendors both canonical implementations at immutable full-SHA pins and
enforces the cross-repository boundary through conformance tests.

This closure does not claim that text extraction, chunking, indexing, evidence,
or synthesis is complete. The kit-owned `pdf_acquisition_manifest` is not a
frozen Contract v1 registry type. WP01-E2 must verify this manifest and the
source bytes before it emits Contract v1 `DocumentManifestArtifact` records
with truthful extraction state.

## Canonical publication ledger

| Stage | Canonical repository / PR | Merge commit | Harness evidence |
|---|---|---|---|
| E1 acquisition domain | `nexus-scholar-org/scholar-pdf-kit` [PR #1](https://github.com/nexus-scholar-org/scholar-pdf-kit/pull/1) | `858911f6b7dd5738de94fa749ffc4c65b6d0b70e` | Vendored under `tools/scholar-pdf-kit/`; plugin and metapackage pins match. |
| E1 MCP declaration/rejection | `nexus-scholar-org/scholar-agent-kit` [PR #1](https://github.com/nexus-scholar-org/scholar-agent-kit/pull/1) | `6050e0c99cdddb0f2c1ce7e0c62458a58eab5ce7` | Vendored under `tools/scholar-agent-kit/`; plugin and metapackage pins match. |
| E1 harness synchronization | `nexus-scholar-org/nexus-scholar-harness` [PR #47](https://github.com/nexus-scholar-org/nexus-scholar-harness/pull/47) | `baaeeb43977897924bd6ba9fda252e1bc9d464b8` | E1-NEG-030/044/047, generated pins, surface matrix, skills, wheel dependency. |

The frozen Contract v1 baseline and
`docs/architecture/wp01_contract_adoption_handoff.md` remained unchanged.

## §14 completion record

### PDF-kit canonical repository, PR, and merge SHA

- Repository: `nexus-scholar-org/scholar-pdf-kit`
- PR: [#1](https://github.com/nexus-scholar-org/scholar-pdf-kit/pull/1)
- Merge SHA: `858911f6b7dd5738de94fa749ffc4c65b6d0b70e`
- Canonical implementation includes strict Contract v1 parent-shape checks,
  deterministic document identity, content validation, durable commit-intent
  recovery, cross-process publication locks, exact-manifest reuse, path
  containment, structured outcomes, and resource-cleanup diagnostics.

### Agent-kit canonical repository, PR, and merge SHA

- Repository: `nexus-scholar-org/scholar-agent-kit`
- PR: [#1](https://github.com/nexus-scholar-org/scholar-agent-kit/pull/1)
- Merge SHA: `6050e0c99cdddb0f2c1ce7e0c62458a58eab5ce7`
- Capability `pdf_acquisition` is declared with `mcp_supported=false`.
- `nexus_pdf_acquire` unconditionally returns `operation=acquire_pdf`,
  `status=FAILED`, `artifacts=[]`, and one non-retryable
  `UNSUPPORTED_CAPABILITY` error before provider, filesystem, manifest, or
  audit-success I/O.

### Acquisition schema and version

- Manifest schema: `pdf-acquisition-manifest-v1`
- Manifest type: `pdf_acquisition_manifest`
- Contract context version: `1.0.0`
- Manifest IDs: deterministic `ACQ-*` identities.
- Document IDs: deterministic `DOC-*` identities bound to workspace, study,
  exact source SHA-256, media type, and the documented identity algorithm.

### Public API/CLI surface and MCP capability declaration

- Python API: `scholar_pdf.acquisition` and
  `scholar_pdf.acquisition_models`.
- CLI: `uv run scholar-pdf acquire <config.json> --audit-logger
  <path-to-log_event.py>`.
- MCP: explicitly unsupported through the observable rejection boundary above.
- Surface ownership and commands are recorded in
  `docs/kits_surface_matrix.md` and the mirrored PDF/agent kit skills.

### Legacy projection retained/deprecated

`DownloadResult` remains as a compatibility projection for legacy
download/ingest callers. New authoritative E1 consumers use the typed
acquisition request, item outcome, batch outcome, and manifest models. Filename
existence, `was_oa`, and a successful HTTP response are not authoritative
document or legal-access evidence.

### Files changed

- Canonical PDF-kit PR: 18 paths, including the acquisition service/models,
  canonical identity helpers, strict parent gate, CLI integration, atomicity
  tests, and contract tests.
- Canonical agent-kit PR: capability registry, MCP server rejection adapter,
  and E1-NEG-047 tests.
- Harness PR #47: 35 paths covering the two vendored snapshots, two full-SHA
  pins, generated metapackage pins, E1 conformance fixtures/tests, surface
  documentation, skills, tool-count consumers, and wheel dependency metadata.

### Acceptance criteria covered

All `E1-001` through `E1-016` are covered. In particular:

- malformed, stale, excluded-study, cross-workspace, and mismatched parents
  fail before acquisition;
- document and manifest identities are deterministic and content-sensitive;
- access state is truthful and independent from gateway/proxy configuration;
- invalid content and conflicting persistent identity fail closed;
- process death, commit faults, replay, cancellation, and concurrency preserve
  authoritative state;
- workspace containment, packaging, canonical/vendored/pin synchronization,
  and the unsupported MCP boundary are executable conformance gates.

### Negative fixtures added

- PDF-kit implements the kit-owned `E1-NEG-001` through `E1-NEG-043`,
  `E1-NEG-045`, and `E1-NEG-046` cases, including real process-death and
  multi-process contention tests.
- Agent-kit implements `E1-NEG-047` with direct, registered-tool, mutation,
  static-reachability, and zero-I/O checks.
- Harness implements cross-repository `E1-NEG-030`, frozen-registry rejection
  `E1-NEG-044`, and the final `E1-NEG-047` documentation/surface parity limb.

### Targeted and full test results

Evidence recorded at the three canonical merge gates:

- PDF kit: focused `94 passed, 4 skipped`; full `140 passed, 4 skipped`; Ruff
  clean; process-death recovery and four-process contention probes passed.
- Agent kit: focused `27 passed`; one pre-existing protocol-validation baseline
  failure was isolated from the E1 delta; the MCP rejection path emitted zero
  audit events and all mutation probes were detected.
- Harness PR #47: full `564 passed, 5 skipped, 0 failed`; focused E1/MCP `67
  passed`; conformance `86 passed, 2 skipped`; Ruff and all four generated-file
  checks passed.
- PR #47 CI: nine jobs passed across Ubuntu, Windows, and macOS Python
  3.11/3.12, schema validation, and Windows/Ubuntu wheel E2E.

### Wheel and import smoke result

- PDF-kit wheel built and its public imports and `scholar-pdf --help` passed.
- Harness distribution wheel built with `pypdf>=4.0.0`; E1 imports resolved
  from the wheel bundle rather than an editable checkout.
- Both distribution entrypoints answered `--help`; offline init/setup-MCP/
  doctor/log E2E completed successfully.

### Harness vendored SHAs and pins

| Kit | `plugins.json` and generated metapackage pin |
|---|---|
| `scholar-pdf-kit` | `858911f6b7dd5738de94fa749ffc4c65b6d0b70e` |
| `scholar-agent-kit` | `6050e0c99cdddb0f2c1ce7e0c62458a58eab5ce7` |

The E1 vendoring fixtures enumerate the expected Git mode/blob/path rows. The
conformance gate compares the tracked snapshot exactly and verifies worktree
content through Git clean filters, so it is sensitive to real drift and
portable across LF and Windows `core.autocrlf` checkouts.

### Generated-pin check

`uv run python scripts/generate_nexus_scholar_pins.py --check` passes, and the
generated metapackage snapshot contains the same two full commit SHAs.

### Remaining mismatches or blocked decisions

No E1 blocker remains. Deferred work is outside E1:

- WP01-E2 owns extraction provenance and Contract v1
  `DocumentManifestArtifact` emission.
- E2 must revisit MCP semantic parity if extraction adds or changes MCP
  behavior; E1's unsupported acquisition declaration must not be silently
  broadened.
- Pre-existing agent-kit protocol-validation and non-hermetic RAG test behavior
  remain separate maintenance items and do not weaken E1 evidence.
- Agent-kit `.gitignore`, minor upstream docstring hygiene, and an optional
  import-time dependency guard remain non-blocking maintenance work.

## Reviewer verdict

`APPROVE` — WP01-E1 is safe for WP01-E2 to consume. No Contract v1 schema was
weakened, no unmerged toolkit revision was pinned, no vendored-only toolkit
implementation was introduced, and no scientific workspace was modified.

## Audit disposition

No `workspaces/<slug>/` research project was in scope, so no scientific
workspace journal event is applicable. The durable audit trail is the canonical
PR/merge ledger above, the immutable toolkit pins, the E1 vendoring fixtures,
and the executable conformance tests.
