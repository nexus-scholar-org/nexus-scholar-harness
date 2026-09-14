# System Architecture & Design Blueprints

This directory contains the architectural blueprints and design specifications for the Nexus Scholar ecosystem.

## Lifecycle Architecture Map (Phases 0 through 7)

To ensure high modularity, the Nexus Scholar architecture separates the research methodology into sequential, verifiable phases:

| Phase | Subsystem | Location / Package | Status | Role & Contract |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 0** | **Socratic Inception & Protocol Schema** | [`phase_0/`](./phase_0/README.md) | **Implemented** | Interactive methodology interview, 4-way refraction grid, boundary grill, and deterministic `protocol.json` compilation. |
| **Phase 1** | **Federated Literature Discovery** | `tools/scholar-search-kit` | **Implemented** | Multi-source academic search (OpenAlex, Crossref, Semantic Scholar, PubMed, arXiv, bioRxiv) and PID deduplication. |
| **Phase 2** | **PRISMA Screening & OA Harvest** | `tools/scholar-pdf-kit` | **Implemented** | Agent-in-the-loop screening decisions, open-access PDF harvesting, and structured layout/text extraction. |
| **Phase 3** | **Extraction, AST RAG & Knowledge Graphs** | `tools/scholar-rag-kit` & `scholar-graph-kit` | **Implemented** | Structural AST chunking, PageRank-boosted hybrid vector retrieval, and citation knowledge network construction. |
| **Phase 4** | **Trust & Verification Layer** | `tools/scholar-verify-kit` | **Implemented** | Retraction checking, open-science DAS/CAS scans, COI auditing, risk-of-bias scoring, and verbatim claim verification. |
| **Phase 5** | **Harness Console** | [`phase_5/`](./phase_5/README.md) | **Design Complete** | Lightweight, local-first web UI for human-in-the-loop review, DAG execution, and conflict adjudication. |
| **Phase 6** | **Scientific Trust Bridge** | [`phase_6/`](./phase_6/README.md) | **Active** | Cryptographic verification, Creator Mode presets, and multi-agent harness bridges (DeepSeek Harness, Claude Desktop, Cursor). |
| **Phase 7** | **Bench-Portable Distribution** | [`phase_7_distribution/`](./phase_7_distribution/README.md) | **Shipped v1.0.0** | Universal `nexus-scholar` metapackage, zero-friction `uvx` / `pip` installation, and portable workspace CLI. |

> [!NOTE]
> **Why are Phases 1–4 not separate documentation folders here?**
> Phases 1 through 4 represent the core computational research pipeline. They are packaged as the eight modular Python kits checked out under `tools/` and documented in detail in the [Kit Surface Matrix](../kits_surface_matrix.md).

## Subdirectories

- **[`phase_0/`](./phase_0/)**: Socratic inception protocol, JSON Schema definitions, dynamic extraction matrix dimensions, and playbooks.
- **[`phase_5/`](./phase_5/)**: Harness Console blueprints, components, UI plans, and `PipelineSpec` execution schema.
- **[`phase_6/`](./phase_6/)**: Scientific trust specifications, external harness bridges, and multi-agent interaction policies.
- **[`phase_7_distribution/`](./phase_7_distribution/README.md)**: Bench-portable distribution blueprint, gap analysis checklist, and packaging architecture.

---

> For public usage documentation, see the [User Guide](../nexus_scholar_user_guide.md), the [Kit Surface Matrix](../kits_surface_matrix.md), the [Roadmap](../UPCOMING_WORK.md), and the master [Documentation Index](../README.md).
