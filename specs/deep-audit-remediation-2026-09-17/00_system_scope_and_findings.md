# System Scope, Evidence Baseline, and Findings Register

**Status:** Draft for review  
**Applies to:** Harness plus eight toolkits  
**Source of truth:** Live checkout inspected on 2026-09-17

## 1. Why this specification set exists

The audited system has a coherent domain decomposition and broad happy-path test
coverage, but important defects cluster at package boundaries:

- identifiers change meaning between stages;
- CLI, API, and MCP surfaces advertise behavior they do not execute;
- failures are converted into empty or successful-looking outputs;
- old artifacts can satisfy new-run gates;
- extraction and synthesis can present missing evidence as populated evidence;
- package metadata does not always declare import-time dependencies.

The remediation therefore treats cross-boundary contracts as the primary design
unit. Fixing isolated functions without fixing their producers and consumers is
out of scope for completion.

## 2. Audited components

### 2.1 Harness

- CLI and distribution front doors
- monolithic `ResearchOrchestrator`
- configurable `PipelineSpec` DAG validation and execution
- agent-in-the-loop screening preparation and collection
- inception, recon, workspace scaffolding, doctor and MCP setup
- FastAPI console, job execution, streaming, and workspace inspection
- audit/state synchronization and artifact exporters

### 2.2 Toolkits

1. `scholar-protocol-kit`
2. `scholar-search-kit`
3. `scholar-pdf-kit`
4. `scholar-bib-kit`
5. `scholar-rag-kit`
6. `scholar-graph-kit`
7. `scholar-agent-kit`
8. `scholar-verify-kit`

## 3. Validation baseline

The audit produced the following observed results. These are evidence about the
current checkout, not future acceptance thresholds.

| Boundary | Observed result | Interpretation |
|---|---:|---|
| Harness full suite | 445 passed, 5 skipped, 1 setup error | Setup error was a shared fixed-temp collision; isolated rerun passed |
| Search kit | 151 passed | Boundary/failure contracts remain untested |
| PDF kit | 43 passed | Strict-download and successful-engine contracts remain untested |
| Bib kit | 2 passed | Coverage is insufficient for resolver and mutation behavior |
| RAG kit | 64 passed | Multi-paper identity and non-fabrication cases absent |
| Graph kit | 77 passed, 1 failed | Failure is stale CLI-output expectation; broken modes are otherwise uncovered |
| Protocol kit | 134 passed | Four Windows subprocess decode warnings; invalid cross-field compilation uncovered manually |
| Agent kit | 27 passed, 1 failed | Genuine file-path protocol-validation regression; a broader suite additionally reported 55 passed with two shared-temp setup collisions |
| Verify targeted set | Passed, 2 skipped | Trust/open-science boundary defects uncovered manually |

The repository-wide `--basetemp=tests_temp` configuration is unsafe for parallel
test processes. The isolated failing harness test passed when rerun with a unique
temporary root.

## 4. Severity model

| Level | Definition | Required response |
|---|---|---|
| P0 | Can silently corrupt evidence identity, execute materially different work than requested, fabricate evidence, or make canonical workflows unusable | Must be repaired before claiming end-to-end scientific reliability |
| P1 | Can misclassify evidence, hide important failures, violate a documented public contract, or lose provenance | Must be repaired before the next stable distribution release |
| P2 | Material reliability, packaging, parity, or documentation defect with a safe workaround | Schedule after P0/P1 contract stabilization |
| P3 | Maintainability, ergonomics, or low-probability robustness issue | Address opportunistically with relevant ownership work |

## 5. System findings register

| ID | Severity | Boundary | Confirmed finding | Owning spec |
|---|---|---|---|---|
| SYS-001 | P0 | Harness DAG | All built-in templates use nonexistent `scholar-search run`; structural validation reports them valid | 01 |
| SYS-002 | P0 | Screening | A stale `included.json` can satisfy a newly prepared screening run | 01, 10 |
| SYS-003 | P0 | RAG | Corpus `workspace_id` is used as per-paper identity, collapsing studies | 05, 10 |
| SYS-004 | P0 | RAG | Standard matrix fills absent evidence with invented domain values | 05 |
| SYS-005 | P0 | Agent | MCP pipeline ignores `query`; requested skipped stages still execute | 08 |
| SYS-006 | P0 | Protocol | Compiler emits cross-field-invalid protocols | 07 |
| SYS-007 | P1 | Search/Bib | Identifier-bridge dedup does not transitively union clusters | 02, 04 |
| SYS-008 | P1 | PDF | Strict structural validation is not applied to downloaded/cache-hit PDFs | 03 |
| SYS-009 | P0 | Graph | Coupling and hybrid CLI modes call incompatible API keyword names | 06 |
| SYS-010 | P1 | Verify | Retraction-only evidence can yield `UNVERIFIED` instead of `BLOCKED` | 09 |
| SYS-011 | P1 | Search | Provider failure is indistinguishable from zero results | 02, 10 |
| SYS-012 | P1 | PDF | Extraction failures can become successful-looking Markdown stubs | 03 |
| SYS-013 | P1 | Protocol/Agent | Valid file-path protocol validation returns `INVALID` over MCP | 07, 08 |
| SYS-014 | P1 | Graph | Graph transforms discard metadata and sometimes nodes | 06 |
| SYS-015 | P1 | Verify | Open-science negation and link association can inflate availability | 09 |
| SYS-016 | P1 | Cross-kit | Runtime dependencies are missing from multiple package manifests | 03, 05, 06, 08, 10 |
| SYS-017 | P1 | Harness | Audit event production is duplicated, weakly identified, and always-success in one path | 01, 10 |
| SYS-018 | P2 | Documentation | Skill, README, API, and surface-matrix content contradicts live behavior | All kit specs |
| SYS-019 | P1 | Harness DAG | `build_command` renders positional args as `--name value`, booleans as `--flag true`, lists as one flag plus extra tokens, and never passes declared outputs; built-ins are structurally valid but not executable even after SYS-001 | 01 |
| SYS-020 | P1 | Harness DAG | An unknown edge source is reported as an error yet `_toposort` still indexes `adj[src]`, raising `KeyError` instead of a structured validation error | 01 |
| SYS-021 | P1 | Harness | Search engine, verification clients, and graph client lack exception-safe cleanup in the fixed orchestrator path | 01 |
| SYS-022 | P0 | Verify | `scholar-verify verbatim-claims` crashes at runtime (`re` used but never imported) | 09 |

Register scope: this register lists system-level findings and their owning
specifications. Per-kit details, line-level evidence, and additional confirmed
defects (e.g. search exports/lineage, PDF Docling metadata loss, bib resolver
semantics, graph "Louvain" naming, protocol `golden_seeds`, agent recon anchoring)
are enumerated in `15_deep_audit_report.md` and the owning kit specifications.
Severities assigned here are authoritative over the informal ordering in the
audit report.

## 6. Global invariants

### INV-01 — Identity

`workspace_id` identifies one research workspace or corpus. `study_id` identifies
one paper/work. `chunk_id` identifies one evidence unit derived from one study.
No consumer may use the workspace identifier as a study identifier.

### INV-02 — Evidence honesty

Missing, inaccessible, unparsed, unreported, and failed are distinct states. They
must never be replaced by plausible domain values or generic extracted prose.

### INV-03 — Failure visibility

A partial provider, model, extraction, or verification failure must be represented
in a structured outcome. It must not be indistinguishable from a legitimate empty
result.

### INV-04 — Reproducible gates

A downstream artifact may satisfy a gate only when its recorded input fingerprint
matches the current upstream artifact set and protocol fingerprint.

### INV-05 — Surface parity

CLI, Python API, and MCP wrappers may intentionally expose different subsets, but
shared parameter names must have the same semantics. Unsupported parameters must
be rejected, not accepted and ignored.

### INV-06 — Safe persistence

Canonical JSON, Markdown, BibTeX, and state artifacts must be written using a
same-directory temporary file, validation where applicable, and atomic replace.

### INV-07 — Auditability

Every significant workspace mutation must produce one canonical event containing
stable identifiers, actual outcome, inputs, outputs, parameters, metrics, and
provenance. Audit failure must be observable.

### INV-08 — Package independence

Every import-time dependency must be declared. Each distributed package must pass
an isolated install/import/`--help` smoke without relying on the shared harness
environment.

## 7. Explicit non-goals

This remediation does not:

- claim that all scientific judgments can be automated;
- replace human title/abstract or full-text screening;
- bypass publisher access controls;
- guarantee recall merely because all providers returned successfully;
- define a new research methodology or risk-of-bias framework;
- authorize direct pushes to canonical repositories;
- require a wholesale rewrite of the harness or toolkits;
- require every toolkit capability to be exposed through MCP.

## 8. Decision record required before implementation

The following decisions must be recorded before dependent work lands:

1. Canonical `study_id` derivation and collision policy.
2. Versioned artifact envelope and migration policy.
3. Strict versus best-effort discovery mode defaults.
4. Whether semantic similarity remains a supported signal and what it is named.
5. Correction/addendum severity in Phase-4 trust calculation.
6. Whether pipeline commands remain generic arbitrary argv or move to a typed
   command registry.
7. Backward-compatibility window for existing unversioned workspaces.

