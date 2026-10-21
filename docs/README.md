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

The active work. Each entry is an entrypoint, not a record. Current packet status
and next priorities live in the [program tracker](UPCOMING_WORK.md); check live
main and PRs before presenting its snapshot as current. The selected product
direction is the [individual researcher application](architecture/decisions/individual-researcher-product.md).

| Track | Entrypoint |
| :-- | :-- |
| **WP — research correctness and contract adoption** | [Contract baseline](./architecture/contract_v1_baseline.md), [cross-kit contract](./architecture/cross_kit_contract_v1.md), [WP-01 completion](./architecture/wp01/README.md) |
| **HCM — harness core modularity** | [`harness-core-modularity/README.md`](./architecture/harness-core-modularity/README.md) |
| **AG — agent controls** | [`agent-controls/README.md`](./architecture/agent-controls/README.md) |
| **UI — research-ui** | [`research_ui/README.md`](./architecture/research_ui/README.md) + [`apps/research-ui/`](../apps/research-ui/README.md) |

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
| [**Harvest Calibration Lessons**](./lessons/2026-10-17_uav_harvest_calibration_lessons.md) | Lessons learned from the UAV multi-provider harvest (v0.2 pilot + v0.3), mapped to a proposed kit/harness development backlog (K1–K6, H1–H6). Evidence-anchored; proposals are not commitments. |
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
