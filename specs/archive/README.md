# Historical Specifications & Sprint Archive

This directory contains historical implementation plans, sprint execution checklists, and early draft specifications from earlier rapid development cycles (Phases 0 and A through F, September 2026).

## Archival Purpose and Context

During the rapid bootstrap phase of the Nexus Scholar Harness (PR #34), work was scoped into sequential implementation phases (A through F) accompanied by per-phase execution plans and an initial draft data contract (`INTER_PHASE_DATA_CONTRACT.md`).

Following the formal **Deep System Audit** of 2026-09-17 (`specs/deep-audit-remediation-2026-09-17/15_deep_audit_report.md`):
1. **Contract v1 Baseline**: The early draft contracts in this archive were formally audited, reconciled, and superseded by the normative Contract v1 specifications (`specs/deep-audit-remediation-2026-09-17/10_cross_kit_contracts.md` and `docs/architecture/cross_kit_contract_v1.md`), eliminating identity ambiguity and establishing strict provenance.
2. **Toolkit Source Migration**: The capabilities implemented during these sprints (scientometrics in `scholar-graph-kit`, RIS/CSL exporters in `scholar-search-kit`, AST backends in `scholar-rag-kit`, agent handoffs in `scholar_harness`) are maintained directly in their respective kit packages and active specifications.
3. **Preservation**: These documents are preserved in this archive for auditability, traceability, and historical record.

## Archived Sets

| Archive Set | Historical Scope | Status in Active Code |
| :--- | :--- | :--- |
| [`INTER_PHASE_DATA_CONTRACT.md`](./INTER_PHASE_DATA_CONTRACT.md) | Initial draft inter-phase contracts (2026-09-15) | **Superseded** by Contract v1 (`specs/deep-audit-remediation-2026-09-17/10_cross_kit_contracts.md`) |
| [`phase_0_refactoring.md`](./phase_0_refactoring.md), [`phase_0_refactoring/`](./phase_0_refactoring/) | Early refactoring checklist for inception and test layouts | **Complete** (`src/scholar_harness/inception/`, reorganized `tests/`) |
| [`phase_a_interoperability/`](./phase_a_interoperability/) | Phase A: RIS, CSL-JSON, GraphML export, metadata completeness | **Integrated** in `scholar-search-kit` & `scholar-graph-kit` |
| [`phase_b_scientometrics/`](./phase_b_scientometrics/) | Phase B: HITS, co-citation, coupling, Louvain clustering, query validation | **Integrated** in `scholar-graph-kit` & `scholar-search-kit` |
| [`phase_c_rag/`](./phase_c_rag/) | Phase C: VectorBackend, AST chunking, PII redaction, Gemini embeddings | **Integrated** in `scholar-rag-kit` |
| [`phase_d_agent/`](./phase_d_agent/) | Phase D: Screening and pipeline automation MCP tools | **Integrated** in `scholar-agent-kit` |
| [`phase_e_visualization/`](./phase_e_visualization/) | Phase E: Graph visualization, PRISMA flow diagrams | **Integrated** in `scholar-graph-kit` & `scholar-search-kit` |
| [`phase_f_specialized_agents/`](./phase_f_specialized_agents/) | Phase F: Critique, narrative, and handoff protocols | **Integrated**; handoff specification actively maintained at [`specs/handoff/`](../handoff/README.md) |

For the active, normative architecture and specifications, see [`specs/README.md`](../README.md).
