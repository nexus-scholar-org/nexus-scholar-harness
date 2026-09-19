# Nexus Scholar Deep-Audit Remediation Specifications

**Specification set:** `deep-audit-remediation-2026-09-17`  
**Version:** 1.0.0-draft  
**Status:** Draft for technical review  
**Evidence date:** 2026-09-17  
**Scope:** `src/scholar_harness` and all eight `tools/scholar-*-kit` packages

## Purpose

This directory converts the 2026-09-17 source and test audit into an
implementation-ready remediation program. It is intentionally stricter than a
review report: each confirmed defect is translated into normative requirements,
testable acceptance criteria, migration rules, and a dependency-ordered delivery
plan.

The governing objective is:

> A successful Nexus Scholar run must be operationally executable,
> provenance-preserving, and scientifically honest at every boundary. A green
> process exit, a populated artifact, or a passing unit test must never be used
> as a substitute for evidence identity, completeness, or validity.

## Document map

| Document | Owner boundary | Primary concerns |
|---|---|---|
| [00_system_scope_and_findings.md](00_system_scope_and_findings.md) | Entire system | Evidence baseline, severity model, invariants, exclusions |
| [01_harness_spec.md](01_harness_spec.md) | `src/scholar_harness` | Orchestration, screening gate, DAG execution, audit, console |
| [02_search_kit_spec.md](02_search_kit_spec.md) | `scholar-search-kit` | Discovery outcomes, lossless records, transitive dedup, retries |
| [03_pdf_kit_spec.md](03_pdf_kit_spec.md) | `scholar-pdf-kit` | Download validation, extraction truthfulness, metadata, atomicity |
| [04_bib_kit_spec.md](04_bib_kit_spec.md) | `scholar-bib-kit` | Conservative resolution, transitive dedup, safe writes |
| [05_rag_kit_spec.md](05_rag_kit_spec.md) | `scholar-rag-kit` | Study identity, evidence boundaries, indexing replacement, claims |
| [06_graph_kit_spec.md](06_graph_kit_spec.md) | `scholar-graph-kit` | Transformation correctness, graph identity, failure visibility |
| [07_protocol_kit_spec.md](07_protocol_kit_spec.md) | `scholar-protocol-kit` | Compile-time validity, intent fidelity, typed extraction schemas |
| [08_agent_kit_spec.md](08_agent_kit_spec.md) | `scholar-agent-kit` | MCP truthfulness, parity, path/recon anchoring, dependencies |
| [09_verify_kit_spec.md](09_verify_kit_spec.md) | `scholar-verify-kit` | Retraction blocking, open-science classification, stream parity |
| [10_cross_kit_contracts.md](10_cross_kit_contracts.md) | Shared contracts | IDs, envelopes, artifacts, provenance, errors, lifecycle |
| [11_validation_and_test_plan.md](11_validation_and_test_plan.md) | Repository QA | Contract, negative, packaging, concurrency, scientific tests |
| [12_execution_roadmap.md](12_execution_roadmap.md) | Delivery program | Work packages, dependencies, gates, repository ownership |
| [13_scientific_agent_loop_framework.md](13_scientific_agent_loop_framework.md) | Scientific orchestration | Reusable loop schema, states, safety and audit rules |
| [14_scientific_agent_loop_catalog.md](14_scientific_agent_loop_catalog.md) | Scientific workflows | Proposed task-oriented compositions of kits and agent capabilities |
| [15_deep_audit_report.md](15_deep_audit_report.md) | Audit evidence | Consolidated source review, validation evidence, and confirmed findings |
| [16_publication_strategy.md](16_publication_strategy.md) | Advisory (non-normative) | Scientific-contribution framing, evaluation/benchmark plan, venue strategy, fact-check appendix |

## Authority and interpretation

1. `10_cross_kit_contracts.md` governs shared data and behavioral contracts.
2. A kit specification governs behavior owned by that kit.
3. `01_harness_spec.md` governs orchestration and workspace state transitions.
4. `11_validation_and_test_plan.md` governs the minimum evidence required to
   claim a requirement complete.
5. `12_execution_roadmap.md` governs ordering, but never weakens a requirement.
6. Existing public contracts remain in force unless a specification explicitly
   defines their migration or deprecation.

Normative keywords **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY**
are interpreted as requirement levels. Each numbered requirement is intended to
be independently traceable to implementation and tests.

## Delivery boundary

These documents specify remediation; they do not themselves modify runtime
behavior. Toolkit-source changes must be made in each toolkit's canonical
repository, followed by:

1. tests in the owning repository;
2. a canonical toolkit commit;
3. the corresponding full-SHA `default_rev` update in
   `.agents/plugins/nexus-scholar/plugins.json`;
4. synchronization of the vendored `tools/<kit>` tree;
5. fork-and-PR delivery under the repository contribution gate.

## Global completion gates

The specification set is complete only when:

- every P0 and P1 requirement has an implementation and a named regression test;
- canonical paper identity survives protocol → search → screening → extraction →
  RAG → synthesis → verification;
- built-in pipelines pass executable CLI-contract validation, not only schema
  validation;
- no evidence artifact silently substitutes fabricated text or invented values;
- partial provider/network/LLM failures remain visible in structured outcomes;
- isolated package installation and `--help` smoke tests pass for every kit;
- all significant workspace mutations append a canonical audit event and update
  workspace state;
- the full harness suite and all toolkit suites pass without sharing a fixed
  temporary directory.
