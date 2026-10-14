# Program tracker and backlog

The single routing table for outstanding work. Each track's entrypoint carries
the detail; this file records only **what is open and what governs it**. The
former phase-by-phase roadmap (Phases 0–7) and its completed narratives are in
git history. Snapshot: 2026-10-13, committed baseline `f4b5f60`; AG-04 is merged. Check live main/PRs before answering current-status questions.

Product direction: [individual researcher application](architecture/decisions/individual-researcher-product.md).
Priority: inspect AG-04 against UI-04, reconcile HCM prerequisites, define presentation/action
boundaries, connect one real screening UI journey, then simplify local startup.

| Track | Current state | Next step | Blocker / dependency | Governing document |
| :-- | :-- | :-- | :-- | :-- |
| **WP** — Contract v1 adoption | WP-01 closed with residual debt; A–D producers adopted | Remaining work packages from the execution roadmap | Contract-gated; toolkit changes ship via each kit's canonical repo (fork + PR, pin + vendored sync) | [`wp01/README.md`](./architecture/wp01/README.md) · [`wp01/evidence-boundaries.md`](./architecture/wp01/evidence-boundaries.md) · [`12_execution_roadmap.md`](../specs/deep-audit-remediation-2026-09-17/12_execution_roadmap.md) · [`contract_v1_baseline.md`](./architecture/contract_v1_baseline.md) |
| **HCM** — harness core modularity | HCM-05 **adopted** (PR #107): harness adapter + canonical agent-kit integration; HCM-02 disposition recorded ([hcm-02-disposition.md](./architecture/harness-core-modularity/hcm-02-disposition.md): service+callers delivered, job-runner bypass migrated (PR #134)); HCM-06 read API merged (PR #133, `6575209`); UI-07 action API merged (PR #134, `aa6e2f0`) with job_runner journal migration | Finish the close-out | HCM-02/03/06 have no packet documents — the roadmap is their only definition | [`harness-core-modularity/README.md`](./architecture/harness-core-modularity/README.md) |
| **AG** — agent controls | AG-04 merged (PR #130, `28e5c42`): usable worker/review interaction on the protected publisher | UI-07/HCM-06 boundary specification; AG-05 conditional | POSIX unproven; scaffold has no model judgments; AG-05 needs real backend and independent labels | [`agent-controls/README.md`](./architecture/agent-controls/README.md) · [`agent_controls_plan.md`](./architecture/agent-controls/agent_controls_plan.md) |
| **UI** — research-ui | UI-04 shipped; UI-04a maintenance merged (PR #109); UI-07 read API + UI-04 live wiring merged (PR #133); protected action API merged (PR #134, `aa6e2f0`): pairing-code approval, 5 action routes, UI dialog, browser-verified | UI-05/06 incremental | Human visual review and the `fr`/`ar` fluent-language review remain `NOT_VERIFIED`; the browser suite has not been re-run since UI-04a | [`research_ui/README.md`](./architecture/research_ui/README.md) · [`apps/research-ui/docs/GATES.md`](../apps/research-ui/docs/GATES.md) |

Cross-track gates and delivery lanes: [`test_gate_policy.md`](./architecture/test_gate_policy.md);
current routing and prohibited shortcuts: the [Developer Compass](./architecture/DEVELOPER_COMPASS.md).

## Packet inventory and evidence limits

Merged/adopted means linked delivery evidence; active means reported in progress,
not delivered. Unreconciled means no full packet completion review was performed
for this tracker; it does not assert that the code is missing. Partial/subpacket
delivery never establishes an entire parent packet's completion.

| WP | Scope | Recorded status / evidence |
|---|---|---|
| WP-00 | Frozen decisions/schemas | Frozen baseline delivered; see baseline governance |
| WP-01 | Canonical identities/artifacts | Closed with residual debt; see WP-01 completion record |
| WP-02 | RAG identity/non-fabrication | Full completion unreconciled; WP-01 E3/E4 is overlapping evidence, not full WP-02 closure |
| WP-03 | Screening generation gate | AG-02/03C delivered related controls; full WP-03 closure unreconciled |
| WP-04 | Typed PipelineSpec | Roadmap scope; completion unreconciled |
| WP-05 | Agent pipeline truthfulness | Roadmap scope; completion unreconciled |
| WP-06 | Dedup/resolution | Roadmap scope; completion unreconciled |
| WP-07 | PDF/extraction truthfulness | WP-01 E1/E2 adopted; full WP-07 closure unreconciled |
| WP-08 | Graph correctness | Roadmap scope; completion unreconciled |
| WP-09 | Protocol integrity | Compiler/identity evidence exists; full WP closure unreconciled |
| WP-10 | Verification integrity | Roadmap scope; completion unreconciled |
| WP-11 | Outcomes/audit/lifecycle | HCM/AG overlap; full WP closure unreconciled |
| WP-12 | Packaging/surface parity | Distribution shipped; full remediation WP closure unreconciled |
| WP-13 | Legacy migration | Legacy exception remains; full completion unreconciled |
| WP-14 | Docs/release | Consolidation delivered; full WP closure unreconciled |

WP definitions/dependencies: [execution roadmap](../specs/deep-audit-remediation-2026-09-17/12_execution_roadmap.md).
Its dated defect claims require live verification before task selection.

| Track / packet | Status | Evidence / next decision |
|---|---|---|
| HCM-01 | Characterization recorded | HCM README; measured defects are not approved policy |
| HCM-02/03 | Completion unreconciled | Neutral workspace/audit and pipeline-core roadmap; reconcile evidence before dependent scope |
| HCM-04 | Stage work/subpacket recorded | HCM-04e identity policy delivered; entire HCM-04 closure unreconciled |
| HCM-05 | Adopted | PR #107, harness + canonical-kit integration |
| HCM-06 | Merged (PR #133, `6575209`) | Read-only presentation API (8 GET routes with generation-currentness + loopback CORS); UI-04 live wiring |
| AG-00/01/02 | Historical assessment / delivered controls | AG completion record; AG-02 PR #106 |
| AG-03A/B/C | Delivered, bounded Windows evidence | AG plan; B PR #121, C PR #125/#126; POSIX unproven |
| AG-04 | Merged | PR #130 `28e5c42`, close-out #131 `f4b5f60`; deterministic scaffold, not model accuracy |
| AG-05 | Conditional | Real screening backend, fresh held-out set, independent labels and authorized prospective design required |
| AG-06/07 | Deferred | Extraction/synthesis need separate evidence and authority decisions |
| UI-01–04 / 04a | Delivery recorded | UI-04a PR #109; mock-backed UI does not establish real backend integration |
| UI-05/06 | Open/planned | Evidence lineage / audit activity; verify live packet/gate ledger |
| UI-07 | Read + action API merged (PR #134, `aa6e2f0`) | Read API + UI-04 live wiring (PR #133); protected action API: pairing-code approval, idempotent redemption, CLI begin, journal migration, browser-verified 6/6 |
| F1 | Merged | PR #127, `465c386`: documentation gate selection |
| F2–F5 | Deferred follow-ups | Audit; no broad test-deletion campaign |
| F6 | KEEP | Public-surface evidence insufficient for replacement |
| Kit ownership note | Recorded in this documentation candidate | Sample shows no demonstrated duplication; kit move deferred |
| UAV pilot | Preliminary delivered | PR #123: two preliminary sources, zero accepted charting; formal design/freezing gates remain |

This inventory is a routing aid, not a new packet audit. At close-out, update the
affected row with its merge/evidence and next action. An index links here rather
than maintaining a competing status table. Report stale or missing evidence as
unverified; do not infer percentages from packet counts.

## Not scheduled

Phase-era feature ideas carried over for reference. None is scheduled, and each
needs a scoped packet before work starts: a Jupyter notebook suite, Zotero
two-way sync, and an Overleaf/Typst export bridge (Phase-3 era); shared
collaborative workspaces, a no-code `PipelineSpec` builder, and one-click domain
playbooks (Phase-5 console era). The live console contract is
[`console/SPECS.md`](./architecture/console/SPECS.md).
