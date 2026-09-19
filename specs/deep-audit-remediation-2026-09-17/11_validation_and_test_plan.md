# Validation and Test Plan

**Version:** 1.0.0-draft  
**Status:** Required gate specification  
**Applies to:** Every requirement in this directory

## 1. Objective

The validation program must prove more than function-level correctness. It must
show that public surfaces agree, failures remain visible, artifacts retain their
identity and provenance, and an isolated installation behaves the same as the
shared development environment.

Passing the existing suite is necessary but not sufficient. Completion requires
new negative, metamorphic, migration, packaging, concurrency, and end-to-end
tests defined below.

## 2. Test principles

### VAL-001 — Traceability

Every normative MUST requirement must map to at least one automated test ID. A
test may cover multiple requirements, but a requirement cannot be closed by a
generic suite result alone.

### VAL-002 — Failure-first design

For every successful operation, tests must cover at least:

- malformed input;
- missing input;
- stale or mismatched input;
- dependency/import failure;
- network timeout/rate limit/provider outage where relevant;
- partial item failure;
- interrupted write;
- retry/idempotent replay;
- cancellation where supported.

### VAL-003 — No live network in required CI

Required CI tests must be hermetic. Network-backed contract tests may run in a
separate opt-in job and must never be the sole evidence for a requirement.

### VAL-004 — Contract fixtures

Cross-kit contracts must be tested through versioned golden fixtures. Producers
and consumers must run against the same fixture corpus.

### VAL-005 — Scientific negative controls

Tests must include negation, contradictory claims, missing fields, same-workspace
multi-paper corpora, retraction-only evidence, unresolved provider responses, and
non-entailing semantically similar text.

### VAL-006 — Platform coverage

The required matrix remains Windows, Linux, and macOS on supported Python
versions. Path, encoding, atomic-replace, and subprocess tests must run on every
platform rather than being Linux-only.

## 3. Test layers

### 3.1 Unit tests

Unit tests cover pure normalization, fingerprinting, union/merge behavior,
schema validation, error mapping, classification, and state transitions.

Requirements:

- deterministic inputs and outputs;
- no filesystem outside `tmp_path`;
- no network;
- exact reason/status assertions, not only truthiness;
- input objects checked for unintended mutation where relevant.

### 3.2 Component tests

Each kit must exercise its public Python service with fake transports/backends.
The test must verify structured outcomes and item-level diagnostics, not merely
that a file exists.

### 3.3 Surface parity tests

For operations available through more than one surface:

1. invoke the Python service;
2. invoke the CLI in JSON mode;
3. invoke the MCP wrapper;
4. normalize transport-only fields;
5. assert semantically equivalent outcomes, artifact hashes, warnings, and
   item-level statuses.

Intentional differences must be declared in the capability registry and tested
as explicit unsupported behavior.

### 3.4 Cross-kit contract tests

The following chains require producer/consumer tests:

| Producer | Consumer | Contract under test |
|---|---|---|
| Protocol | Search | strategy, golden seeds, protocol fingerprint |
| Search | Screening | canonical study IDs, source provenance, corpus fingerprint |
| Screening | PDF/Verify | included roster and screening-run lineage |
| PDF | RAG | document/study identity, extraction state, frontmatter/schema |
| Bib | RAG | DOI and bibliographic enrichment without identity replacement |
| Graph | RAG | node IDs and PageRank mapping |
| RAG | Verify | claim/evidence schema, per-study attribution, verification axes |
| All writers | Harness | outcome envelope, artifact commit, audit event |

### 3.5 End-to-end tests

Required hermetic scenarios:

1. **Two-paper happy path:** two papers in one workspace remain distinct through
   matrix, synthesis, consensus, and Phase 4.
2. **Human handoff:** pipeline pauses, rejects stale decisions, accepts matching
   decisions, and resumes without repeating valid completed work.
3. **Partial provider outage:** discovery returns `PARTIAL`, preserves successful
   provider results, and reports failed providers.
4. **No legal OA PDF:** result is unresolved/not-found, not “confirmed paywall,”
   with no invalid PDF artifact.
5. **Malformed extraction:** no successful full-text status and no indexable
   generic stub.
6. **Retraction-only evidence:** trust result is `BLOCKED`.
7. **Legacy workspace:** diagnosis identifies missing versions/fingerprints and
   applies an explicit migration or refuses safely.
8. **Cancelled job:** active command terminates or reaches a bounded safe point;
   final state and audit event agree.

## 4. Required kit-specific regressions

### 4.1 Search

- root import/export smoke for every declared symbol;
- three-record DOI/arXiv bridge unions to one cluster;
- all provider failures produce a non-success outcome;
- one provider failure plus results produces `PARTIAL` and diagnostics;
- GET 429/503 retry/backoff uses fake time and bounded attempts;
- JSON/JSONL round-trip retains provenance, topics, OA locations, raw-data policy,
  canonical IDs, and schema version;
- global versus per-provider limit semantics are enforced and documented;
- verification preserves canonical identity and lineage;
- clients close when search/verification raises.

### 4.2 PDF

- strict structural validation runs for new downloads and cache hits;
- failed strict validation removes/quarantines staged data before commit;
- real minimal valid PDF extracts non-stub content;
- malformed and encrypted fixtures produce explicit outcomes;
- successful PyMuPDF and Docling outputs share canonical metadata/frontmatter;
- Grobid's different output type is explicit and cannot masquerade as Markdown;
- gateway rewriting and forward proxy arguments are independently asserted;
- duplicate DOI batch input produces one atomic artifact;
- response size limit and interrupted write leave no canonical partial file.

### 4.3 Bib

- three-record DOI/title bridge unions transitively;
- deterministic survivor and field-merge policy;
- conservative Crossref threshold rejects unrelated first hit;
- protected local fields survive resolution under merge policy;
- same-key distinct records produce a reported conflict or deterministic rename;
- no-output/in-place behavior requires explicit authorization;
- resolver returns per-entry results for timeout, no match, ambiguous match, and
  success;
- client closes and concurrent tasks are bounded;
- malformed BibTeX does not overwrite source.

### 4.4 RAG

- two papers sharing one workspace produce distinct study IDs and tokens;
- absent methodology fields remain null/`NOT_REPORTED`, never plausible defaults;
- negated/numeric contradiction is not called entailed based on similarity;
- shortened-document reindex deletes obsolete chunks;
- identical reindex produces identical chunk set;
- audit journal path is explicit and consistent across index/query/matrix;
- `min_chunk_chars` behavior is either implemented and tested or removed;
- consensus does not mutate caller-owned claims;
- matrix fallback query is meaningfully different or removed;
- clean wheel import succeeds with declared dependencies only.

### 4.5 Graph

- every `build --mode` executes successfully with a common fixture;
- transforms preserve node roster and metadata, including isolates;
- actual Louvain honors seed or renamed greedy algorithm rejects seed;
- fetch failures produce item-level errors rather than isolated-success fiction;
- PageRank exception is distinguishable from a valid uniform graph;
- DOI URL/prefix/case normalization maps to one node;
- graph and PageRank key identities match RAG consumption;
- missing input is nonzero/structured failure;
- requested format controls emitted artifacts;
- minimal isolated installation includes all dependencies.

### 4.6 Protocol

- compiler rejects nonexistent RQ references and duplicate identifiers;
- inline/file/API/CLI/MCP validation parity;
- `golden_seeds` survives intent → protocol → canonical serialization;
- numeric, categorical, boolean, and list dimensions generate correct schemas;
- unknown/typo fields fail under strict input models;
- formatting changes preserve fingerprint; semantic array reorder follows declared
  ordering semantics;
- Windows CLI output is explicit UTF-8 without thread warnings;
- README commands/modules are executable through doctest-like smoke checks.

### 4.7 Agent

- valid file-path protocol validation returns `VALID`;
- query override materially reaches discovery or is rejected as unsupported;
- skipped stages do not execute, write, call network, or appear as successful;
- clean kit-local installation launches exactly the configured MCP command;
- `--workspace` redirects actual recon artifacts, not only an environment value;
- LLM failure returns `PARTIAL` with `HEURISTIC_FALLBACK` provenance;
- calibration gate prevents or explicitly flags an uncalibrated screening run;
- all tools return structured envelopes and genuine MCP errors;
- tool registry count, signatures, skill, and surface matrix stay generated/parity
  checked.

### 4.8 Verify

- retraction-only flagged study is `BLOCKED`;
- `No data available` is explicitly unavailable;
- unrelated URL cannot upgrade DAS/CAS;
- nearby typed data/code link upgrades only the matching signal;
- dry-run performs zero network calls if documented as plumbing-only;
- CLI and MCP `all` select the same documented stream set;
- explicit skipped retraction returns `SKIPPED`, not empty success;
- correction/addendum severity follows the approved policy;
- duplicate roster IDs fail rather than collapse silently;
- significant Phase-4 commits receive audit and workspace-state updates.

## 5. Property and metamorphic tests

Use property-based tests where they materially improve coverage:

- DOI normalization is idempotent;
- deduplication is order-independent after deterministic tie-breaking;
- merging is associative with respect to identity components;
- canonical JSON is stable under object-key/whitespace changes;
- atomic publication produces either old complete state or new complete state;
- retrying an identical committed operation adds neither duplicate artifact nor
  duplicate canonical audit event;
- claim/study identities remain unchanged when unrelated studies are added;
- changing corpus/workspace name does not merge studies.

## 6. Fault injection

Required injection points:

- before staging write;
- during staged write;
- after staged validation but before replace;
- after artifact replace but before audit append;
- rate-limit response with and without `Retry-After`;
- provider parse exception;
- database unavailable or collection mismatch;
- subprocess exit zero without output;
- subprocess nonzero after partial output;
- cancellation during active node;
- process restart with persisted running job.

Each test must state the expected recoverable state and next operator action.

## 7. Packaging and dependency tests

For the harness, metapackage, and every toolkit:

1. build wheel from a clean checkout;
2. install in a new isolated environment using declared dependencies only;
3. import package root and each documented public symbol;
4. run each console entrypoint `--help`;
5. for agent-kit, start MCP server and enumerate tools without invoking network;
6. compare installed metadata to `plugins.json`/generated pins where applicable;
7. fail on undeclared direct imports detected by static import/dependency analysis.

The shared editable `.venv` is not valid evidence for this gate.

## 8. Concurrency and temporary-directory requirements

**VAL-TMP-001 (MUST):** Tests must not configure one fixed `--basetemp` for
concurrent processes. CI and local parallel runs must use worker/process-unique
directories.

**VAL-TMP-002 (MUST):** Toolkit sub-suites launched in parallel must not delete or
reuse another suite's temporary root.

**VAL-CON-001 (MUST):** Audit appends, node manifests, and multi-file artifact
commits require concurrent-writer tests.

**VAL-CON-002 (MUST):** Downloader/indexer duplicate work tests must prove
deterministic one-artifact outcomes.

## 9. Performance guardrails

Performance is not a substitute for correctness, but regressions need bounds:

- dedup should remain near-linear outside fuzzy comparison buckets;
- graph pairwise transformations require benchmark fixtures and documented safe
  pool sizes;
- downloader/search concurrency must remain bounded;
- audit/state synchronization must not reread unbounded artifacts unnecessarily;
- RAG reindex replacement must scale by affected document, not full collection,
  where backend capabilities allow it.

Benchmark failures are advisory until baselines are approved, except unbounded
memory/task creation, which is a correctness failure.

## 10. CI gates

### Pull-request gate

- targeted owner-kit unit/component tests;
- shared cross-kit contract fixtures affected by the change;
- CLI/API/MCP parity tests for changed operations;
- dependency/entrypoint smoke for changed packages;
- harness conformance tests for changed pins/surfaces;
- CI-scoped `uv run ruff check scripts/`.

### Phase gate

- all tests across harness and affected kits;
- full schema/migration suite;
- hermetic end-to-end scenarios;
- Windows/Linux/macOS matrix;
- regenerated skills/surface matrix checked for drift;
- no fixed-temp collisions under supported parallel execution.

### Release gate

- clean wheels and minimal-dependency entrypoints;
- canonical toolkit repos, vendored trees, pins, and generated pins synchronized;
- release notes and migration guide;
- unresolved P0 count zero;
- unresolved P1 items explicitly waived by a recorded decision, never silently
  omitted.

## 11. Evidence record

Every completed requirement must add an entry to a traceability table containing:

| Field | Meaning |
|---|---|
| Requirement ID | e.g. `HAR-SCR-005` |
| Owning repository | Canonical implementation repository |
| Commit/PR | Immutable implementation reference |
| Test IDs | Exact automated evidence |
| Fixture/schema version | Contract evidence used |
| Result | Pass/fail plus date/platform |
| Migration impact | None or migration identifier |
| Notes | Remaining limits; no claim inflation |

## 12. Definition of done

- Every P0/P1 requirement is traceable to tests and an immutable change.
- All mandatory test layers pass.
- Negative scientific controls pass.
- Isolated package smokes pass.
- Parallel suite execution produces no temp-root collision.
- No skipped test hides an applicable supported-platform requirement.
- Known limitations are documented next to the surface they constrain.

