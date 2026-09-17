# Scholar Search Kit Remediation Specification

## Metadata

- Status: Draft for implementation
- Date: 2026-09-17
- Scope: `tools/scholar-search-kit`, its harness callers, and its agent/MCP adapters
- Priority: P0-P2
- Evidence policy: statements labelled **Confirmed** are grounded in the cited checkout; **Hypothesis** items require a reproducer before implementation.

## Problem and safety boundary

Search is the provenance boundary for the review corpus. A provider outage, lossy round trip, identity split, or unverifiable replacement record must never be represented as successful evidence discovery. Remediation must not fabricate documents, identifiers, verification status, abstracts, provider coverage, or screening decisions. Existing workspaces must remain readable.

All mutating commands MUST write through a same-directory temporary file, flush and close it, validate the complete artifact, and atomically replace the destination. Failure MUST preserve the previous destination and return a structured outcome. Every owned HTTP client MUST close on success, failure, and cancellation.

## Architecture and current data flow

`compile_protocol_search` maps protocol concepts and bounds to a `Query` plus provider names (`tools/scholar-search-kit/src/scholar_search/protocol_adapter.py:10-90`). `SearchEngine.search_all` concurrently streams provider results, optionally passing the combined list to `Deduplicator` (`tools/scholar-search-kit/src/scholar_search/engine.py:43-73`). Providers normalize remote records into the dataclasses in `models.py`; dedup assigns `SCI-*` identities; verification/hydration may replace or enrich records; import/export and screening persist downstream artifacts. The harness directly consumes these internal modules in `src/scholar_harness/orchestrator.py:514-623` and recon closes search engines in `src/scholar_harness/recon/engine.py:165-176`.

## Confirmed findings

1. Package exports are inconsistent. `__all__` names models, importers and `AcademicHttpClient` that are not imported (`tools/scholar-search-kit/src/scholar_search/__init__.py:3-52`); the README imports `Query` from the root (`tools/scholar-search-kit/README.md:97-108`). A live audit reproduced `AttributeError` from `from scholar_search import *`.
2. Identifier bridges do not union existing clusters. Matching stops at the first identifier (`tools/scholar-search-kit/src/scholar_search/dedup.py:57-67`) and subsequently re-registers all identifiers to one cluster (`tools/scholar-search-kit/src/scholar_search/dedup.py:127-129`). A DOI-only record, arXiv-only record, then a bridge record remained two clusters.
3. Provider exceptions are logged and swallowed (`tools/scholar-search-kit/src/scholar_search/engine.py:50-63`), so zero results and failed coverage are indistinguishable to callers.
4. GET has no application-level retry and raises immediately for 429/4xx (`tools/scholar-search-kit/src/scholar_search/http_client.py:86-126`), although the matrix claims exponential 429 handling (`docs/kits_surface_matrix.md:178-186`). `cache_path` is computed but unused (`tools/scholar-search-kit/src/scholar_search/http_client.py:69-79`), while cache expiry is configured separately (`tools/scholar-search-kit/src/scholar_search/config.py:25-31`).
5. Verification returns newly normalized records (`tools/scholar-search-kit/src/scholar_search/verifier.py:64-146`), losing lineage. The harness documents and partially repairs lost workspace IDs (`src/scholar_harness/orchestrator.py:601-623`).
6. `--limit` is described as a maximum (`tools/scholar-search-kit/src/scholar_search/cli.py:136-137`) but the same per-provider limit is dispatched to every provider (`tools/scholar-search-kit/src/scholar_search/engine.py:50-63`).
7. CLI cleanup occurs only after successful search/verification (`tools/scholar-search-kit/src/scholar_search/cli.py:228-232`, `tools/scholar-search-kit/src/scholar_search/cli.py:610-615`).
8. JSON exporters serialize the full dataclass (`tools/scholar-search-kit/src/scholar_search/export.py:14-32`), but importers omit `sources`, `oa_locations`, `topics`, and `raw_data` (`tools/scholar-search-kit/src/scholar_search/importers.py:104-144`, `tools/scholar-search-kit/src/scholar_search/importers.py:160-181`).
9. Unsupported citation methods silently yield nothing (`tools/scholar-search-kit/src/scholar_search/providers/base.py:42-50`).

Hypothesis to test: current sequential `SCI-*` assignment may be unstable when provider completion order changes; do not change the identity algorithm until a deterministic concurrency reproducer confirms this.

## Goals and non-goals

Goals: trustworthy provider coverage; deterministic identity union; lossless records; explicit verification lineage; consistent API/CLI/MCP outcomes; atomic artifacts; guaranteed cleanup. Non-goals: changing screening policy, adding proprietary databases, claiming complete literature recall, or silently rewriting existing workspace identifiers.

## Normative requirements

Requirement IDs: the numbered requirements below carry stable IDs `SE-001`…`SE-013`
(requirement *n* = `SE-0nn`). Regression tests and the traceability ledger required
by `11_validation_and_test_plan.md` (VAL-001, §11–§12) MUST reference these IDs.

1. The root package MUST either import every `__all__` symbol or remove it; documented imports MUST be executable.
2. Dedup MUST union every cluster connected by any canonical identifier and MUST preserve an auditable alias map when IDs collapse.
3. Search MUST return a structured batch outcome containing documents and one outcome per requested provider: `success|partial|failed|unsupported`, count, attempts, and sanitized error. These nested provider outcomes are lowercase and provider-scoped by design; the enclosing operation outcome MUST use the canonical uppercase status envelope of `10_cross_kit_contracts.md` (XC-011–XC-014) and MUST be `PARTIAL` whenever any requested provider failed, in addition to `SUCCESS` for full success.
4. Empty successful coverage MUST remain distinct from failed coverage. CLI exit status MUST be nonzero when all requested providers fail; partial success MUST be machine-detectable.
5. Retry behavior MUST be identical in documented API and implementation, honor bounded `Retry-After`, and never retry permanent 4xx responses except 408/429.
6. Cache directory and expiry MUST either be wired to explicit storage or removed from the public contract.
7. Verification MUST enrich the original logical record and preserve `workspace_id`, cluster ID, sources, query ID, retrieval time, and original identifiers. Conflicts MUST be recorded, not overwritten.
8. `--limit` and protocol pool size MUST have one documented meaning. A global cap is preferred; any per-provider option MUST be named explicitly.
9. JSON and JSONL round trips MUST preserve every normalized field and schema version. Unknown fields SHOULD be retained in an extension area.
10. Unsupported snowball operations MUST return `unsupported`, not an empty-success result.
11. SearchEngine, verifier, and HTTP clients MUST support async context management and idempotent close; callers MUST use `try/finally` or `async with`.
12. CLI and MCP writes MUST be atomic and MUST emit a structured summary artifact before reporting success.
13. No result, abstract, identifier, provider success, or verification status MAY be inferred merely to fill a missing field.

## API, data, and CLI behavior

Introduce versioned `ProviderOutcome` and `SearchBatchOutcome`; retain `search_all(...)->list[Document]` as a deprecated compatibility projection for one release. Add a strict option that raises a typed aggregate error after cleanup. Add `VerificationOutcome` with original identity, resolved candidate, confidence/reason, field-level changes, and failure class. Version serialized documents with `schema_version`; import legacy unversioned records as v0.

CLI JSON summaries MUST include requested/succeeded/failed providers, raw and unique counts, effective limit semantics, output path, and atomic commit status. Human tables MAY remain. Screening output MUST preserve existing filenames while writing them transactionally.

## Migration and backward compatibility

- Release 1: add outcome APIs and warnings; keep list-returning adapters and accept legacy JSON.
- Release 2: make structured outcomes primary; require explicit projection for documents only.
- Preserve existing `SCI-*` values when importing established workspaces. Emit aliases rather than renumbering bridge-unioned records.
- Coordinate root API changes with harness and agent-kit consumers and update pinned kit commit plus vendored snapshot together.

## Delivery plan

### P0

1. Repair/export-test the root API and docs.
2. Implement deterministic multi-cluster union and regression tests.
3. Add provider outcomes and eliminate ambiguous swallowed failures.
4. Preserve verification lineage and guarantee client cleanup.
5. Make JSON/JSONL persistence lossless and atomic.

### P1

1. Define/enforce global versus per-provider limits.
2. Unify GET/POST retry policy and implement or retire persistent cache settings.
3. Add explicit provider capability reporting.
4. Update harness/MCP adapters to carry structured outcomes into audit artifacts.

### P2

1. Add schema migration utilities and performance tests for union-find dedup.
2. Add optional strict provider quorum policies and cache observability.

## Failure-focused test matrix

| Area | Cases | Required assertion |
|---|---|---|
| Exports | every `__all__` name; README snippet | import succeeds and type is correct |
| Dedup | DOI/arXiv bridge; three-cluster bridge; conflicting IDs; input permutations | one deterministic cluster, alias ledger, no evidence loss |
| Providers | timeout, DNS, 429 with/without Retry-After, 404, malformed JSON, cancellation | classified outcome, bounded attempts, cleanup |
| Federation | zero hits, one failure, all failures, partial stream failure | empty success differs from failure; correct exit semantics |
| Limits | 1/5/6 providers, dedup on/off | documented cap is enforced |
| Verification | DOI match, title match, mismatch, outage, replacement candidate | lineage preserved; conflict visible |
| Round trip | all fields, unknown field, datetime, legacy v0 | semantic equality and schema version |
| Persistence | disk full, serialization error, interruption, existing destination | old artifact intact; no partial final file |
| Snowball | unsupported capability, cycles, cap, cancellation | explicit unsupported; deterministic bounded output |

## Definition of done

All P0 requirements and failure tests pass on supported platforms; current toolkit and harness suites pass; no leaked clients or partial final files occur under injected failures; docs and skills execute as written; audit artifacts distinguish coverage from evidence; vendored tree, canonical kit repository, and pinned SHA are synchronized.

## Dependencies and risks

Search is consumed by harness recon/orchestration, PDF HTTP access, and agent MCP tools. Outcome/API changes require coordinated adapters. Cluster union risks changing identity selection; mitigate with stable survivor rules and alias manifests. Retry changes risk API load; cap attempts and honor server guidance.

## Documentation updates

Update `tools/scholar-search-kit/README.md`, API/provider/verification docs, `.agents/skills/scholar-search-kit/SKILL.md`, and `docs/kits_surface_matrix.md` with exact imports, outcome schemas, limits, retry/cache truth, capability behavior, migration examples, and audit interpretation.
