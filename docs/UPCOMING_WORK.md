# Backlog — current program

The single routing table for outstanding work. Each track's entrypoint carries
the detail; this file records only **what is open and what governs it**. The
former phase-by-phase roadmap (Phases 0–7) and its completed narratives are in
git history.

| Track | Current state | Next step | Blocker / dependency | Governing document |
| :-- | :-- | :-- | :-- | :-- |
| **WP** — Contract v1 adoption | WP-01 closed with residual debt; A–D producers adopted | Remaining work packages from the execution roadmap | Contract-gated; toolkit changes ship via each kit's canonical repo (fork + PR, pin + vendored sync) | [`wp01/README.md`](./architecture/wp01/README.md) · [`wp01/evidence-boundaries.md`](./architecture/wp01/evidence-boundaries.md) · [`12_execution_roadmap.md`](../specs/deep-audit-remediation-2026-09-17/12_execution_roadmap.md) · [`contract_v1_baseline.md`](./architecture/contract_v1_baseline.md) |
| **HCM** — harness core modularity | HCM-05 **adopted** (PR #107): harness adapter + canonical agent-kit integration | Record the HCM-06 decision and finish the close-out | HCM-02/03/06 have no packet documents — the roadmap is their only definition | [`harness-core-modularity/README.md`](./architecture/harness-core-modularity/README.md) |
| **AG** — agent controls | AG-04 delivered (pending PR merge): usable worker/review interaction on the protected publisher | **AG-05** — held-out scientific evaluation after calibration | POSIX unproven; model-accuracy/agent-reliability explicitly out of scope | [`agent-controls/README.md`](./architecture/agent-controls/README.md) · [`agent_controls_plan.md`](./architecture/agent-controls/agent_controls_plan.md) |
| **UI** — research-ui | UI-04 shipped; UI-04a maintenance merged (PR #109) | Open UI packets (UI-05 evidence lineage, UI-06) and the unresolved verification gates | Human visual review and the `fr`/`ar` fluent-language review remain `NOT_VERIFIED`; the browser suite has not been re-run since UI-04a | [`research_ui/README.md`](./architecture/research_ui/README.md) · [`apps/research-ui/docs/GATES.md`](../apps/research-ui/docs/GATES.md) |

Cross-track gates and delivery lanes: [`test_gate_policy.md`](./architecture/test_gate_policy.md);
current routing and prohibited shortcuts: the [Developer Compass](./architecture/DEVELOPER_COMPASS.md).

## Not scheduled

Phase-era feature ideas carried over for reference. None is scheduled, and each
needs a scoped packet before work starts: a Jupyter notebook suite, Zotero
two-way sync, and an Overleaf/Typst export bridge (Phase-3 era); shared
collaborative workspaces, a no-code `PipelineSpec` builder, and one-click domain
playbooks (Phase-5 console era). The live console contract is
[`console/SPECS.md`](./architecture/console/SPECS.md).
