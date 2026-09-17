# Scholar Agent Kit Remediation Specification

**Status:** Proposed / implementation-ready  
**Owner:** scholar-agent-kit maintainers  
**Date:** 2026-09-17  
**Scope:** `tools/scholar-agent-kit`, its MCP surface, and adapter-only integration tests  
**Target release:** next breaking-safe minor release

## 1. Architecture and current state

`scholar-agent-kit` is the MCP front door for the Nexus Scholar suite. `server.py` imports protocol, search, PDF, RAG, graph, bibliography, and verification APIs and exposes synchronous and asynchronous `nexus_*` tools (`tools/scholar-agent-kit/src/scholar_agent/server.py:27-76`). Recon support reaches back into the harness through installed-package discovery, ancestor scanning, an environment override, and `sys.path` mutation (`server.py:79-115`). Paths are normalized through the MCP anchor before most tool execution (`server.py:159-170`).

The intended architecture is a thin adapter: validate inputs, invoke one canonical kit API, persist canonical artifacts atomically, emit audit events, and return a uniform structured outcome. It must not contain a second implementation of domain logic.

## 2. Confirmed findings

1. **P0 undeclared runtime dependency.** `server.py` imports five `scholar_verify` modules (`server.py:61-63`), but `scholar-verify-kit` is absent from dependencies and editable sources (`tools/scholar-agent-kit/pyproject.toml:6-22`). A clean installation can fail at import time.
2. **Mixed response contracts.** Protocol compilation returns JSON `{status,...}` (`server.py:178-205`), criteria rendering returns prose prefixed with `Error:` (`server.py:270-285`), discovery returns prose (`server.py:293-323`), and bibliography cleaning also returns prose (`server.py:815-837`). Callers cannot reliably distinguish data, validation failure, and infrastructure failure.
3. **Broad exception conversion loses failure type.** Many tools catch `Exception` and return strings or minimally structured JSON; examples are protocol compile/validate (`server.py:184-205,260-267`), screening (`server.py:443-509`), and reconciliation (`server.py:854-895`).
4. **Screening silently changes method.** LLM failure triggers heuristic screening (`server.py:458-475`) while the final success envelope does not report the fallback (`server.py:498-507`). That is a provenance and scientific-method defect.
5. **Screening writes five artifacts independently and non-atomically** (`server.py:481-496`), allowing a partially committed screening state.
6. **Protocol compilation does not persist its canonical protocol or audit event** (`server.py:178-203`); callers must interpret and write the returned payload.
7. **Recon loading mutates `sys.path` and assumes repository ancestry** (`server.py:79-115`). This is an explicit portability seam, not a stable package contract.
8. **Pipeline skip semantics are post-hoc result filtering.** The wrapper parses `skip_stages` after construction (`server.py:513-557`) rather than proving the orchestrator did not execute those stages.
9. **The MCP bibliography tool mutates the input by default** and returns prose (`server.py:815-837`).
10. **Claim verification accepts both a bare list and `{claims:[...]}`** (`server.py:899-940`), which is useful migration behavior but lacks an explicit schema-version negotiation contract.
11. **File-path protocol validation is broken.** The adapter reads a valid JSON file to text and passes that string directly to `ResearchProtocol.model_validate` (`server.py:230-248`), producing `INVALID`; the targeted agent-kit suite exposes this regression.
12. **Pipeline query is ignored.** `nexus_pipeline_run` accepts `query` but never forwards or uses it, while `skip_stages` removes result keys only after the full orchestrator has executed (`server.py:513-566`). The surface therefore accepts controls with materially false semantics.
13. **Workspace recon anchoring is initialized too early.** `RECON_CACHE_ROOT` is computed at module import (`server.py:125-135`), while CLI `--workspace` sets `NEXUS_RECON_ROOT` later (`server.py:1857-1863`); actual recon calls continue using the earlier root.
14. **Calibration does not gate screening.** Calibration utilities exist, but MCP screening uses only checklist construction and can proceed without a recorded readiness/calibration decision.

## 3. Goals and non-goals

### Goals

- Make every MCP tool machine-safe, deterministic at the adapter boundary, path-safe, and contract-versioned.
- Preserve domain-kit semantics and expose them without silent degradation.
- Guarantee CLI/API/MCP parity for equivalent operations.
- Make all material writes atomic and auditable.
- Make clean-wheel import and `--help` mandatory smoke gates.

### Non-goals

- Reimplement search, screening, PDF extraction, bibliography, RAG, graph, protocol, or verification algorithms.
- Make network providers deterministic.
- Preserve undocumented prose response parsing indefinitely.
- Let the agent kit own workspace business logic that belongs in the harness.

## 4. Normative requirements

### 4.1 Packaging and lifecycle

- **AG-001 MUST** declare every imported kit, including `scholar-verify-kit`, in both project dependencies and local editable sources.
- **AG-002 MUST** import successfully in a clean wheel environment containing only declared dependencies.
- **AG-003 MUST** close every client, provider, engine, or temporary resource on success, error, and cancellation. Async resources MUST use `async with` or `try/finally`.
- **AG-004 SHOULD** replace repository-ancestry `sys.path` injection with a declared harness adapter dependency or entry-point/plugin protocol. The environment override MAY remain for one deprecation cycle.

### 4.2 Tool protocol

- **AG-005 MUST** return the structured outcome envelope defined in `10_cross_kit_contracts.md`; no registered tool may return an `Error:` prose sentinel.
- **AG-006 MUST** assign stable error codes and distinguish validation, not-found, conflict, dependency, network, partial, and internal failures.
- **AG-007 MUST** include `contract_version`, `operation`, `run_id`, `status`, `artifacts`, `warnings`, and `provenance` in every response.
- **AG-008 MUST NOT** expose secrets, full exception traces, API keys, or arbitrary remote response bodies in public errors.
- **AG-009 SHOULD** accept a caller-supplied idempotency key for mutating operations and return the prior committed outcome on exact retry.

### 4.3 Paths, writes, and audit

- **AG-010 MUST** anchor relative paths to an explicit workspace or configured anchor; CWD MUST NOT determine artifact location.
- **AG-011 MUST** reject path traversal and, unless explicitly declared as an external input, paths outside the workspace.
- **AG-012 MUST** write multi-file artifact sets to a staging directory, validate them, atomically promote them, then append one audit event.
- **AG-013 MUST** leave the previous complete artifact set intact if any write, validation, or audit preparation fails.
- **AG-014 MUST** record input hashes, protocol fingerprint, method/configuration, kit versions, timestamps, output hashes, and fallback state.

### 4.4 Domain delegation and parity

- **AG-015 MUST** delegate domain behavior to public kit APIs; private imports such as `_check_cross_field` (`server.py:34-38`) MUST be replaced by public APIs.
- **AG-016 MUST** maintain a machine-readable tool registry mapping each MCP tool to API callable, CLI command, input schema, output schema, and capability differences.
- **AG-017 MUST** enforce parity tests for operations available through more than one surface.
- **AG-018 MUST** expose warnings even when an operation succeeds.
- **AG-019 MUST NOT** translate a failed LLM screening run into heuristic results without explicit caller opt-in. If opted in, status MUST be `PARTIAL`, `method_used` MUST identify the fallback, and artifacts MUST record both failure and fallback.
- **AG-020 MUST** verify the active protocol fingerprint before screening or downstream mutation and reject stale/missing fingerprints as `PROTOCOL_FINGERPRINT_MISMATCH`.
- **AG-021 MUST** make requested pipeline skips effective before execution; post-hoc output filtering is forbidden.
- **AG-022 MUST** either forward and honor `query` as documented or reject it as unsupported; accepted control parameters may never be ignored.
- **AG-023 MUST** parse file and inline protocol payloads into the same validated object path and prove parity with a golden valid/invalid fixture.
- **AG-024 MUST** resolve recon roots after CLI/workspace arguments and environment overrides are finalized; per-call operations MUST use that resolved root.
- **AG-025 MUST** require or explicitly waive the configured screening calibration gate, recording readiness status and rubric version in outputs.

## 5. API, data, and MCP behavior

Each tool SHALL have a typed request model and typed result payload. Paths in payloads SHALL be workspace-relative POSIX strings; absolute paths MAY appear only in local diagnostics. Tool-specific result data SHALL be nested under `data`.

- `nexus_protocol_compile`: return the canonical protocol, protocol ID, and fingerprint; persist only when `output_path` is explicitly supplied.
- `nexus_protocol_validate`: return all errors and warnings in both valid and invalid cases; never reconstruct a model through a second divergent path.
- `nexus_discover`: return artifact references and summary counts, not a human preview as the primary payload.
- `nexus_screen`: require corpus and protocol fingerprints; report `LLM`, `HEURISTIC`, or `HUMAN_BATCH` method; commit the screening artifact set atomically.
- `nexus_pipeline_run`: pass stage selection into the orchestrator before execution and return per-stage outcomes.
- `nexus_bib_clean`: default to a distinct output unless `in_place=true`; return counts, key changes, duplicate groups, and output hash.
- `nexus_verify_claims` / `nexus_verify_phase4`: consume the canonical claim and Phase-4 schemas from the cross-kit specification and retain per-item verdicts.

## 6. Migration and backward compatibility

1. Release N adds envelope responses and `legacy_text=true`; default remains legacy only if required by an identified consumer.
2. Release N+1 defaults to structured envelopes and emits a deprecation warning for legacy text.
3. Release N+2 removes legacy prose. Schema v1 readers remain supported through explicit adapters, never heuristic shape guessing.
4. Existing tool names remain stable. Renamed parameters require aliases for one minor release.
5. Existing artifacts are read through versioned migrations; outputs are always written at the current schema version.

## 7. Implementation plan

### P0

1. Declare `scholar-verify-kit`; add clean-install import and `scholar-agent --help` tests.
2. Introduce shared request/outcome/error models and convert all tools.
3. Make screening fallback opt-in and provenance-visible.
4. Add protocol/corpus fingerprint gates.
5. Make screening and Phase-4 multi-file writes transactional.
6. Fix file-path protocol validation, actual query forwarding, and true pre-execution stage skipping.

### P1

1. Add typed tool registry and parity tests.
2. Remove private protocol imports and post-hoc pipeline skipping.
3. Add idempotency, audit emission, and resource-lifecycle helpers.
4. Replace implicit in-place mutations with explicit flags.
5. Make recon anchoring dynamic and wire screening calibration/readiness provenance.

### P2

1. Replace the recon import seam with a packaged adapter protocol.
2. Add cancellation/progress events and bounded concurrency where domain APIs support them.
3. Generate MCP reference documentation from the registry.

## 8. Failure-focused test matrix

| Case | Expected result |
|---|---|
| Clean wheel lacks an imported dependency | Build/test fails before release; production import never fails |
| Relative path under hostile CWD | Artifact remains under configured workspace |
| `../` output traversal | `PATH_OUTSIDE_WORKSPACE`; no write |
| Invalid JSON / schema | `VALIDATION_ERROR` with field paths |
| Protocol changed after corpus preparation | `PROTOCOL_FINGERPRINT_MISMATCH`; no artifacts |
| LLM screening outage, fallback disabled | `DEPENDENCY_ERROR`; no heuristic artifacts |
| LLM outage, fallback enabled | `PARTIAL`; method and cause recorded |
| Third of five screening writes fails | no new artifact set or audit event |
| Network cancellation | all clients close; `CANCELLED` outcome |
| Duplicate idempotency key and identical inputs | same run/artifact result; no duplicate event |
| Duplicate key with different inputs | `IDEMPOTENCY_CONFLICT` |
| CLI/API/MCP same fixture | semantically identical canonical payload and hashes |

## 9. Definition of done

- All AG requirements have tests or an explicitly approved waiver.
- Clean source and wheel installs import and answer `--help` using only declared dependencies.
- No MCP tool uses prose error sentinels or untyped success strings.
- Screening cannot silently change methodology.
- Atomicity, fingerprint, path-boundary, cancellation, and parity tests pass on Windows and POSIX.
- Full harness suite and kit suite pass; vendored tree, canonical kit repository, and pinned revision agree.

## 10. Dependencies, risks, and documentation

Implementation depends on the common schemas in `10_cross_kit_contracts.md` and public protocol/harness adapter APIs. Principal risks are breaking consumers that parse prose, duplicate audit events during retries, and incorrectly classifying external paths. Mitigate with telemetry-free compatibility fixtures, idempotency tests, and explicit external-input declarations.

Update the kit README, MCP tool reference, `docs/kits_surface_matrix.md`, plugin manifest dependency notes, packaging documentation, and examples. Documentation MUST be generated or verified against the registry in CI.
