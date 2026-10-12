# System Architecture & Design Blueprints

This directory holds the **live** architecture, governance, and per-track design
records for the Nexus Scholar ecosystem. Completed pre-build design sets and
superseded analysis were removed in the 2026-10-12 consolidation (recoverable from git history).

## Active work — WP program + three tracks

| Track | Entrypoint | What it is |
| :--- | :--- | :--- |
| **WP program** (Contract v1 adoption) | [`DEVELOPER_COMPASS.md`](./DEVELOPER_COMPASS.md), [`wp01/`](./wp01/README.md) | WP-01 delivered (qualified); remaining work packages open. `wp01/` is the WP-01 delivery archive. |
| **HCM** — harness core modularity | [`harness-core-modularity/README.md`](./harness-core-modularity/README.md) | Extracting neutral services (workspace, audit, pipeline, MCP) from `scholar_harness` without behaviour change. |
| **AG** — agent controls | [`agent-controls/README.md`](./agent-controls/README.md) | Authorization boundaries for agent-assisted screening/publication. **Enforcement is not yet proven.** |
| **UI** — research-ui | [`research_ui/README.md`](./research_ui/README.md) (spec), `apps/research-ui/` (app) | Researcher-facing view/controller over the harness; the harness stays authoritative. |

Each track folder carries its own `README.md` entrypoint and, where relevant, an
`archive/` for dated records.

## Governance (do not move — contract-locked or tool-read)

- [`DEVELOPER_COMPASS.md`](./DEVELOPER_COMPASS.md) — developer entrypoint and current program status.
- [`agent_context_protocol.md`](./agent_context_protocol.md) — agent task-context capsules.
- [`test_gate_policy.md`](./test_gate_policy.md) — delivery lanes; [`test_gate_manifest.json`](./test_gate_manifest.json) is read by `scripts/select_test_gate.py`.
- **Contract-locked set** (hashed by `scripts/generate_contract_baseline.py`; moving or editing any of these requires contract-baseline regeneration + a version decision): [`contract_v1_baseline.md`](./contract_v1_baseline.md) + [`contract_v1_baseline.json`](./contract_v1_baseline.json), [`cross_kit_contract_v1.md`](./cross_kit_contract_v1.md), [`wp01_contract_adoption_handoff.md`](./wp01_contract_adoption_handoff.md), [`wp01_packet_c_reference.md`](./wp01_packet_c_reference.md).

## Lifecycle architecture map (Phases 0–7)

| Phase | Subsystem | Location / Package | Status | Role & Contract |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 0** | Socratic Inception & Protocol Schema | `scholar_harness.inception` | **Implemented** | Interactive methodology interview, 4-way refraction grid, boundary grill, deterministic `protocol.json` compilation. |
| **Phase 1** | Federated Literature Discovery | `tools/scholar-search-kit` | **Implemented** | Multi-source academic search (OpenAlex, Crossref, Semantic Scholar, PubMed, arXiv, bioRxiv) and PID deduplication. |
| **Phase 2** | PRISMA Screening & OA Harvest | `tools/scholar-pdf-kit` | **Implemented** | Agent-in-the-loop screening decisions, open-access PDF harvesting, structured layout/text extraction. |
| **Phase 3** | Extraction, AST RAG & Knowledge Graphs | `tools/scholar-rag-kit` & `scholar-graph-kit` | **Implemented** | Structural AST chunking, PageRank-boosted hybrid retrieval, citation knowledge network construction. |
| **Phase 4** | Trust & Verification Layer | `tools/scholar-verify-kit` | **Implemented** | Retraction checking, open-science DAS/CAS scans, COI auditing, risk-of-bias scoring, verbatim claim verification. |
| **Phase 5** | Harness Console | [`./phase_5/SPECS.md`](./phase_5/SPECS.md) (live spec); blueprint archived | **Design Complete** | Local-first web UI for human-in-the-loop review, DAG execution, conflict adjudication. |
| **Phase 6** | Scientific Trust Bridge | shipped (spec removed) | **Implemented** | Cryptographic verification, Creator Mode presets, multi-agent harness bridges. |
| **Phase 7** | Bench-Portable Distribution | [`phase_7_distribution/`](./phase_7_distribution/README.md) | **Shipped v1.0.0** | Universal `nexus-scholar` metapackage, zero-friction `uvx` / `pip` installation, portable workspace CLI. |

> **Why are Phases 1–4 not separate documentation folders here?** They are the
> core computational pipeline, packaged as the eight modular kits under `tools/`
> and documented in the [Kit Surface Matrix](../kits_surface_matrix.md).

## Folders in this directory

| Folder | Contents |
| :--- | :--- |
| [`agent-controls/`](./agent-controls/README.md) | AG track (plan/decision + `archive/`). |
| [`harness-core-modularity/`](./harness-core-modularity/README.md) | HCM track (roadmap + current packet + `archive/`). |
| [`research_ui/`](./research_ui/README.md) | UI spec of record (`AGENT_WORK_PACKETS.md`). |
| [`wp01/`](./wp01/README.md) | WP-01 delivery archive (E1–E4 packets + closure). |
| [`decisions/`](./decisions/README.md) | Non-contract architecture decisions (ADRs). |
| [`phase_5/`](./phase_5/SPECS.md) | Live console `PipelineSpec` contract. |
| [`phase_7_distribution/`](./phase_7_distribution/README.md) | Shipped distribution blueprint and gap-analysis checklist. |

## Historical archive

Removed in the 2026-10-12 consolidation, recoverable from git history: the
pre-build design sets (`phase_0/`, `phase_5/` blueprint, `phase_6/`) and the
`v1_analysis/` snapshot.

---

> Public usage documentation: [User Guide](../nexus_scholar_user_guide.md),
> [Kit Surface Matrix](../kits_surface_matrix.md), [Roadmap](../UPCOMING_WORK.md),
> and the master [Documentation Index](../README.md).
