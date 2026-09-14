# Documentation Index

Authoritative index of the Nexus Scholar Harness documentation, architectural design sets, and technical specifications.

## 1. User & Getting Started Guides

| Guide | Description |
| :-- | :-- |
| [**User Guide** (`nexus_scholar_user_guide.md`)](./nexus_scholar_user_guide.md) | Comprehensive usage guide: installation (`uvx` / `pip`), workspace initialization, MCP server setup, doctor health-checks, audit logging, and troubleshooting. |
| [**Project Landing Page** (`README.md`)](../README.md) | Ecosystem overview, four-command quickstart, architecture flow, and package release links. |

## 2. Technical References & Roadmap

| Document | State | Description |
| :-- | :-- | :-- |
| [**Roadmap & Backlog** (`UPCOMING_WORK.md`)](./UPCOMING_WORK.md) | **Live** | Consolidated outstanding work, milestone tracking, and prioritized feature backlog. |
| [**Kit Surface Matrix** (`kits_surface_matrix.md`)](./kits_surface_matrix.md) | **Active** | Technical API · CLI · MCP reference across all eight scholar kits: tool signatures, flags, behaviors, cross-kit contracts, and environment variables. |

## 3. Architecture & Phase Design Sets

See [**`architecture/README.md`**](./architecture/README.md) for the master lifecycle architecture map (Phases 0 through 7).

| Phase Design Set | Scope | Status |
| :-- | :-- | :-- |
| [**Phase 0: Socratic Inception** (`phase_0/`)](./architecture/phase_0/README.md) | Protocol schema specification, Socratic inception interview, and `protocol.json` contract. | **Implemented** |
| [**Phase 5: Harness Console** (`phase_5/`)](./architecture/phase_5/README.md) | Architecture for the thin, agent-agnostic local-first UI and `PipelineSpec` DAG executor. | **Design Complete** |
| [**Phase 6: Scientific Trust Bridge** (`phase_6/`)](./architecture/phase_6/README.md) | Verifiable provenance, claim verification, conflict adjudication, and external harness integrations. | **Active / Hardening** |
| [**Phase 7: Bench-Portable Distribution** (`phase_7_distribution/`)](./architecture/phase_7_distribution/README.md) | Zero-friction portable distribution via `nexus-scholar` umbrella package, universal MCP server, and CLI tools. | **Shipped v1.0.0** (PyPI & GitHub) |

## 4. Formal Specifications Series

| Specification | Scope |
| :-- | :-- |
| [**Grounded Exploratory Inception Agent** (`specs/exploratory-grounding-agent/`)](../specs/exploratory-grounding-agent/README.md) | Pre-protocol exploratory literature reconnaissance, empirical taxonomy distillation, and saturation scoring. |
| [**Inception Skill Ecosystem** (`specs/inception-ecosystem/`)](../specs/inception-ecosystem/README.md) | Inception skill stack boundaries, handoffs, and skill-tree/plugin-bundle distribution policy. |
| **Domain Agent Skills** (`.agents/skills/<kit>/SKILL.md`) | Verified agent skills (`scholar-search`, `scholar-pdf`, `scholar-rag`, `inception-agent`, `methodology-copilot`, `workspace-manager`, etc.). |

## 5. Internal Development & Archival Records

Historical adversarial audits, AI reviewer prompt templates, and ecosystem analyses are organized under [**`internal/`**](./internal/README.md):
- **[`internal/audits/`](./internal/audits/)**: Internal adversarial review reports and scorecards.
- **[`internal/review_prompts/`](./internal/review_prompts/)**: Internal reviewer agent prompt templates.
- **[`internal/ecosystem/`](./internal/ecosystem/)**: Deep-dive architectural analyses across related repositories.
- **[`internal/COMMIT_SNAPSHOTS.md`](./internal/COMMIT_SNAPSHOTS.md)**: Historical workspace snapshot markers for restoring previous workspace test data.