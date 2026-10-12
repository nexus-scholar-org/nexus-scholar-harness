# Documentation Index

Authoritative index of the Nexus Scholar Harness documentation. If you are new
here, read this page first; it tells you which of the two trees (`docs/` for
system and program documentation, [`specs/`](../specs/README.md) for formal
specifications) to look in, and which parts are **current** versus **historical**.

## 1. Start here

| Document | Description |
| :-- | :-- |
| [**Developer Compass**](./architecture/DEVELOPER_COMPASS.md) | **Developer entrypoint.** Current program status, packet routing, gates, and prohibited shortcuts. |
| [**User Guide**](./nexus_scholar_user_guide.md) | Installation (`uvx` / `pip`), workspace initialization, MCP setup, `doctor`, audit logging, troubleshooting. |
| [**Project Landing Page**](../README.md) | Ecosystem overview, four-command quickstart, architecture flow, release links. |

## 2. Current program — WP + three tracks

The active work. Each entry is an entrypoint, not a record.

| Track | Entrypoint | Status |
| :-- | :-- | :-- |
| **WP — Contract v1 adoption** | [Contract baseline](./architecture/contract_v1_baseline.md), [cross-kit contract](./architecture/cross_kit_contract_v1.md), [WP-01 archive](./architecture/wp01/README.md) | WP-01 delivered (qualified); remaining work packages open. The contract set is **contract-locked**. |
| **HCM — harness core modularity** | [`harness-core-modularity/README.md`](./architecture/harness-core-modularity/README.md) | Active; HCM-05 close-out, next = HCM-06 gating. |
| **AG — agent controls** | [`agent-controls/README.md`](./architecture/agent-controls/README.md) | Next packet AG-03A; **authority enforcement unproven**. |
| **UI — research-ui** | [`research_ui/README.md`](./architecture/research_ui/README.md) + [`apps/research-ui/`](../apps/research-ui/README.md) | UI-04 shipped; UI-05/06 and the `NOT_VERIFIED` items open. |

Delivery lanes, gate selection, and test policy: [test gate policy](./architecture/test_gate_policy.md).
Backlog and milestone history: [Roadmap](./UPCOMING_WORK.md).
Formal specifications for the program: [`specs/deep-audit-remediation-2026-09-17/`](../specs/deep-audit-remediation-2026-09-17/README.md).

## 3. System architecture

See [**`architecture/README.md`**](./architecture/README.md) for the master
lifecycle map (Phases 0–7), the governance set, and the per-track folders.

## 4. Reference

| Document | Description |
| :-- | :-- |
| [**Kit Surface Matrix**](./kits_surface_matrix.md) | Technical API · CLI · MCP reference across all eight scholar kits (tool signatures, flags, cross-kit contracts, env vars). Read before driving kit CLIs. |
| [**Commit Snapshots**](./internal/COMMIT_SNAPSHOTS.md) | Historical workspace snapshot markers for restoring previous workspace test data. |
| [User Guide](./nexus_scholar_user_guide.md) | Also linked under "Start here". |

## 5. Archive — historical, do not cite as current

| Location | Contents |
| :-- | :-- |
| [`internal/`](./internal/README.md) | The remaining internal record: `COMMIT_SNAPSHOTS.md`, the consolidation plan, one externally-cited analysis. |
| [`specs/exploratory-grounding-agent/`](../specs/exploratory-grounding-agent/README.md) | Complete/historical inception recon spec (M0.1–M0.7; tasks all closed). |

> Historical audits, ecosystem analyses, pre-build phase design sets (`phase_0`,
> `phase_5` blueprint, `phase_6`), the `v1_analysis` snapshot, and
> `specs/archive/` were removed in the 2026-10-12 consolidation; recoverable
> from git history.

## 6. Formal specifications

See [**`specs/README.md`**](../specs/README.md) for the specification hierarchy
and governing authority (Contract v1, kit specs, execution roadmap, domain series).
