# Documentation

Cut to what describes the system as it is, on 2026-11-03. Removed packet,
triage, handoff and plan documents remain in git history; the decisions they
recorded are summarized in [`decisions.md`](decisions.md).

## Start here

| Document | What it is |
| :-- | :-- |
| [Project README](../README.md) | What Nexus is, install, quickstart, developer setup. |
| [User guide](nexus_scholar_user_guide.md) | Install, workspace setup, MCP, `doctor`, audit logging, troubleshooting. |
| [Assessment](assessment/README.md) | **Current state and priorities.** Independent assessment of the harness and all eight kits (2026-11-03) with a ranked P0/P1/P2 list. |
| [Decisions](decisions.md) | One entry per decision that still shapes the code. |
| [AGENTS.md](../AGENTS.md) | Rules for anyone (person or agent) changing the code. |

## Rules for the evidence chain

| Document | What it is |
| :-- | :-- |
| [Developer Compass](architecture/DEVELOPER_COMPASS.md) | Hard invariants (identity, parents, provenance, fail-closed publication), minimum screening provenance, required validation, prohibited shortcuts. |
| [Contract v1 baseline](architecture/contract_v1_baseline.md) + [JSON](architecture/contract_v1_baseline.json) | The frozen contract and its drift check. Baseline-locked. |
| [Cross-kit contract v1](architecture/cross_kit_contract_v1.md) | Identifiers, envelopes and parent binding across packages. Baseline-locked. |
| [WP-01 Packet C reference](architecture/wp01_packet_c_reference.md), [adoption handoff](architecture/wp01_contract_adoption_handoff.md) | Contract adoption reference. Baseline-locked. |
| [Evidence boundaries](architecture/wp01/evidence-boundaries.md), [WP-01 record](architecture/wp01/README.md) | PDF acquisition, extraction and indexing boundaries. |
| [Test gate policy](architecture/test_gate_policy.md) + [manifest](architecture/test_gate_manifest.json) | Which checks a change needs (`scripts/select_test_gate.py`). |
| [Git workflow](architecture/git_workflow.md) | Branches and the fork + PR rule. |

## How parts of the system work

| Document | What it is |
| :-- | :-- |
| [Refusals](architecture/refusals.md) | Typed refusal codes returned to agents. |
| [Human confirmation](architecture/confirmation.md) | How a person confirms agent output. |
| [Agent capability adapters](architecture/agent_capability_adapters.md) | In-process and OpenCode adapter bindings. |
| [Claim existence contract](architecture/claim_existence_contract.md) | Citation/claim existence checks. |
| [Canonical profile parity](architecture/canonical_profile_parity.md) | Cross-package canonical JSON parity. |
| [Workspace stats reconciliation](architecture/workspace_stats_reconciliation.md) | How `project.json` counts are reconciled. |
| [Console API spec](architecture/console/SPECS.md) | The local console API behind `apps/research-ui`. |
| [Research UI specs](architecture/research_ui/README.md) | UI-07 action/presentation specs and the UI packet list. |
| [Agent controls record](architecture/agent-controls/README.md), [HCM record](architecture/harness-core-modularity/README.md) | Completion records of the AG and HCM tracks. |
| [Kit surface matrix](kits_surface_matrix.md) | API/CLI/MCP map of the eight packages. **Stale** (2026-09-13): several claims are disproved in the assessment's §5 sections; regenerate before relying on it. |
| [Kit READMEs](kits/) | Per-package READMEs from the former kit repositories. Install instructions there are obsolete (use `nexus-scholar`); check claims against the assessment. |

## Evidence and history

| Document | What it is |
| :-- | :-- |
| [UAV harvest calibration lessons](lessons/2026-10-17_uav_harvest_calibration_lessons.md) | Lessons from the UAV multi-provider harvest. |
| [UX reviews and brand](ux/) | 2026-11-02/03 phase-by-phase UX reviews (inception, discovery, screening, extraction, verification) with wireframe canvases, and the *Nexus Scholar Provenance* design system. Proposals; not user-tested. |
| [Inception/recon scientific review](architecture/inception_recon_scientific_review.md) (2026-10-09), [test suite audit](architecture/test_suite_audit.md) (2026-10-13), [guideline conformance audit](architecture/guideline_conformance_and_review_audit_2026-10-21.md), [T-SC1 packet](architecture/packet_t_sc1_canonical_profile_parity_2026-10-21.md) | Dated records, kept as history. Links inside them may point at removed files. |
| [Commit snapshots](internal/COMMIT_SNAPSHOTS.md) | Where to restore earlier workspace data from. |
| [`specs/`](../specs/README.md) | Formal specifications that code and the frozen baseline still cite. |
