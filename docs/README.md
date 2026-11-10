# Documentation

Cut to what describes the system as it is, on 2026-11-03, and refreshed on
2026-11-10 against `main` after PR #216. Removed packet, triage, handoff and
plan documents remain in git history; the decisions they recorded are
summarized in [`decisions.md`](decisions.md).

## Start here

| Document | What it is |
| :-- | :-- |
| [Project README](../README.md) | What Nexus is, install, quickstart, developer setup. |
| [Getting started](getting-started.md) | The researcher's first review in the app: install, workspace, inception, discovery, import, screening, publish, export. |
| [Beta page](beta/README.md) | What the beta does and does not do, and how to report a problem. |
| [User guide](nexus_scholar_user_guide.md) | Install, workspace setup, the `ui` command, MCP, `doctor`, audit logging, environment, troubleshooting. |
| [What leaves your computer](data-flow.md) | Every external service, what it receives and when. |
| [Release notes](releases/) | [1.1.0b6](releases/1.1.0b6.md), [1.1.0b5](releases/1.1.0b5.md), [1.1.0b4](releases/1.1.0b4.md), [1.1.0b3](releases/1.1.0b3.md). |
| [Assessment](assessment/README.md) | **Current state and priorities.** The 2026-11-03 assessment of the harness and the kits with a ranked P0/P1/P2 list, the [full review of 2026-11-06](assessment/full-review-2026-11-06.md) and the [three-phase review of 2026-11-10](assessment/three-phase-hardening-2026-11-10.md). |
| [Decisions](decisions.md) | One entry per decision that still shapes the code. |
| [AGENTS.md](../AGENTS.md) | Rules for anyone (person or agent) changing the code. |

## Plan and progress

| Document | What it is |
| :-- | :-- |
| [Production plan](roadmap/production-plan.md) | Phases 0 to 2 to production. §6 lists the merged milestones with their PRs and the planned ones. |
| [Milestone records](roadmap/milestones/) | One file per milestone: definition of done, evidence, deferred items. |
| [Onboarding](roadmap/onboarding.md) | The production plan in one page and a reading order, for a developer joining the project. |
| [Agent autonomy ladder](architecture/agent_autonomy_ladder.md) | Decided 2026-11-10: screening autonomy modes, the calibration gate, agent decision provenance and the discovery assistant (M9a to M9d). |

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
| [Screening API contract](architecture/screening-api-contract.md) | The `/api/v1/screening` routes, decision events, proposals and the console refusal codes (§7). |
| [Discovery API packet](architecture/research_ui/DISCOVERY_API_PACKET.md) | The `/api/v1/discovery` routes behind the Phase 1 screens, the researcher's decisions and the milestone split. |
| [Inception API](architecture/inception-api.md) | Drafts, the step API, compile-preview, gated genesis and recon over HTTP. |
| [Workspaces API](architecture/workspaces-api.md) | Listing, creating and opening workspaces from the app. |
| [Agent system](architecture/agent-system.md) | Proposals only, least autonomy per job; drivers, tasks and the prompt gate. |
| [Refusals](architecture/refusals.md) | Typed refusal codes returned to agents (the envelope registry; the console codes are in the screening API contract §7). |
| [Human confirmation](architecture/confirmation.md) | How a person confirms agent output. |
| [Agent capability adapters](architecture/agent_capability_adapters.md) | In-process and OpenCode adapter bindings. |
| [Claim existence contract](architecture/claim_existence_contract.md) | Citation/claim existence checks. |
| [Canonical profile parity](architecture/canonical_profile_parity.md) | Cross-package canonical JSON parity. |
| [Workspace stats reconciliation](architecture/workspace_stats_reconciliation.md) | How `project.json` counts are reconciled. |
| [Console API spec](architecture/console/SPECS.md) | The local console API behind `apps/research-ui`: routes and browser allowlists. |
| [Research UI specs](architecture/research_ui/README.md) | The research UI's index: final screen specs, API packets, UI-07 action/presentation specs ([action](architecture/research_ui/UI-07_ACTION_SPEC.md), [presentation](architecture/research_ui/UI-07_PRESENTATION_SPEC.md)) and the [UI packet list](architecture/research_ui/AGENT_WORK_PACKETS.md). |
| [Agent controls record](architecture/agent-controls/README.md), [HCM record](architecture/harness-core-modularity/README.md) | Completion records of the AG and HCM tracks. |
| [Kit surface matrix](kits_surface_matrix.md) | API/CLI/MCP map of the packages. Partly re-checked on 2026-11-10 (search section); other claims date from 2026-09-13, and several are disproved in the assessment's §5 sections. Check before relying on it. |
| [Discovery providers (2026-11)](kits/search/PROVIDERS_2026-11.md) | What each search provider offers today, what the code sends, what changed at the providers, and the hardening candidates. |
| [Kit READMEs](kits/) | Per-package READMEs from the former kit repositories. Install instructions there may be obsolete (use `nexus-scholar`); check claims against the assessment. |

## Evidence and history

| Document | What it is |
| :-- | :-- |
| [UAV harvest calibration lessons](lessons/2026-10-17_uav_harvest_calibration_lessons.md) | Lessons from the UAV multi-provider harvest. |
| [UX reviews, final specs and brand](ux/) | The 2026-11-02/03 phase-by-phase UX reviews (inception, discovery, screening, extraction, verification) with wireframe canvases, kept as history; the final screen specs under `ux/<phase>/final/` (the build source; each Status line says what is built); the [final-spec template](ux/final-spec-template.md) and the *Nexus Scholar Provenance* design system ([brand book](ux/brand/BRAND_BOOK.md)). |
| [PRISMA-ScR readiness](assessment/prisma-scr-readiness.md) | 2026-11-06 checklist of each PRISMA-ScR reporting item against what the app does. |
| [Inception/recon scientific review](architecture/inception_recon_scientific_review.md) (2026-10-09), [test suite audit](architecture/test_suite_audit.md) (2026-10-13), [guideline conformance audit](architecture/guideline_conformance_and_review_audit_2026-10-21.md), [T-SC1 packet](architecture/packet_t_sc1_canonical_profile_parity_2026-10-21.md) | Dated records, kept as history. Links inside them may point at removed files. |
| [Commit snapshots](internal/COMMIT_SNAPSHOTS.md) | Where to restore earlier workspace data from. |
| [`specs/`](../specs/README.md) | Formal specifications that code and the frozen baseline still cite. |
