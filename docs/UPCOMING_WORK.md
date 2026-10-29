# Program tracker and backlog

The single routing table for outstanding work. Each track's entrypoint carries
the detail; this file records only **what is open and what governs it**. The
former phase-by-phase roadmap (Phases 0–7) and its completed narratives are in
git history. Snapshot: 2026-10-29, committed baseline `d17710e`; AG-04, HCM-06,
UI-05 and UI-07 are merged. Check live main/PRs before answering current-status
questions.

Product direction: [individual researcher application](architecture/decisions/individual-researcher-product.md).
Priority: freeze and close the UAV pilot (human gates), then use its labels for
AG-05; keep WP-06/WP-13 parked until a harvest or migration asks for them.

| Track | Current state | Next step | Blocker / dependency | Governing document |
| :-- | :-- | :-- | :-- | :-- |
| **WP** — Contract v1 adoption | WP-01 closed with residual debt; 11 of the 13 other WP rows have bounded delivery recorded (evidence overlaps the packet scope, no fresh packet audit); genuinely open: **WP-06**, **WP-13** | WP-06 transitive dedup when the next harvest (B-D1) is planned; WP-13 when a legacy migration is requested | WP-06 needs the search-kit canonical repo (fork + PR, pin + vendored sync); WP-13 needs the one recorded legacy exception scoped | [`wp01/README.md`](./architecture/wp01/README.md) · [`wp01/evidence-boundaries.md`](./architecture/wp01/evidence-boundaries.md) · [`contract_v1_baseline.md`](./architecture/contract_v1_baseline.md) |
| **HCM** — harness core modularity | HCM-05 **adopted** (PR #107): harness adapter + canonical agent-kit integration; HCM-02 disposition **implemented** ([hcm-02-disposition.md](./architecture/harness-core-modularity/hcm-02-disposition.md), job-runner bypass migrated PR #134); HCM-03 **partial** (`console/api/pipelines.py` delegates models/validation to `scholar_harness.pipeline`); HCM-04e **implemented policy**; HCM-06 read API merged (PR #133, `6575209`); UI-07 action API merged (PR #134, `aa6e2f0`) | No new HCM implementation; the qualified close-out is recorded in the track README | HCM-02/03/04 have no packet documents — the roadmap is their only definition; HCM-03 transport removal and HCM-04 stage closure are not claimed | [`harness-core-modularity/README.md`](./architecture/harness-core-modularity/README.md) |
| **AG** — agent controls | AG-04 merged (PR #130, `28e5c42`): usable worker/review interaction on the protected publisher; AG-03A **Windows MIC proven, POSIX unproven**; AG-03B/C delivered | Provision and prove the POSIX authority arrangement, or run the attended pilot without claiming enforced authorization; AG-05 remains conditional | POSIX host boundary (two OS identities + modes) not implemented; AG-05 needs a real backend, fresh held-out set and independent labels | [`agent-controls/README.md`](./architecture/agent-controls/README.md) · [`agent_controls_plan.md`](./architecture/agent-controls/agent_controls_plan.md) |
| **UI** — research-ui | UI-04 shipped; UI-04a merged (PR #109); UI-05 evidence-lineage route shipped (PR #137); UI-07 read + action API merged (PRs #133/#134); UI test/build/browser gates run in CI | UI-06 audit activity (still open); visual-regression baselines; cross-browser run; human `fr`/`ar` review | Human visual and fluent-language review remain `NOT_VERIFIED`; Chromium-only; no visual-regression comparison | [`research_ui/README.md`](./architecture/research_ui/README.md) · [`apps/research-ui/docs/GATES.md`](../apps/research-ui/docs/GATES.md) |

Cross-track gates and delivery lanes: [`test_gate_policy.md`](./architecture/test_gate_policy.md);
current routing and prohibited shortcuts: the [Developer Compass](./architecture/DEVELOPER_COMPASS.md).

## Packet inventory and evidence limits

Merged/adopted means linked delivery evidence; active means reported in progress,
not delivered. Unreconciled means no full packet completion review was performed
for this tracker; it does not assert that the code is missing. Partial/subpacket
delivery never establishes an entire parent packet's completion.

**Bounded delivery** means the named evidence exists and overlaps the packet
scope; it is not a fresh packet audit and does not upgrade a subpacket into
whole-packet closure. Only WP-06 and WP-13 have no delivered scope.

| WP | Scope | Recorded status / evidence |
|---|---|---|
| WP-00 | Frozen decisions/schemas | Frozen baseline delivered; see baseline governance |
| WP-01 | Canonical identities/artifacts | Closed with residual debt; see WP-01 completion record |
| WP-02 | RAG identity/non-fabrication | Bounded delivery — WP-01 E3 index lineage/E4 currentness adopted with recorded debt; no separate WP-02 audit |
| WP-03 | Screening generation gate | Bounded delivery — AG-02 integrity + AG-03C shared gate/coherent generations + AG-04 review lifecycle |
| WP-04 | Typed PipelineSpec | Bounded delivery — `console/SPECS.md` is the live contract; models/validation live in `scholar_harness.pipeline` |
| WP-05 | Agent pipeline truthfulness | Bounded delivery — AG-02/03C/04 controls and the typed envelope/refusal registry |
| **WP-06** | Dedup/resolution | **Genuinely open** — `tools/scholar-search-kit/src/scholar_search/dedup.py` is still a greedy single pass; the roadmap wants union-find. Umbrella of B-D1. Requires canonical-kit PR + full-SHA pin + vendored sync |
| WP-07 | PDF/extraction truthfulness | Bounded delivery — WP-01 E1 acquisition + E2 extracted-text boundaries adopted |
| WP-08 | Graph correctness | Bounded delivery — `scholar-graph-kit` shipped (citation graph, normalized PageRank, HTML export) |
| WP-09 | Protocol integrity | Bounded delivery — deterministic compiler shipped; baseline drift gate green |
| WP-10 | Verification integrity | Bounded delivery — `scholar-verify-kit` shipped (retraction/DAS-CAS/COI/QUADAS-2-PROBAST) |
| WP-11 | Outcomes/audit/lifecycle | Bounded delivery — `OperationOutcome` v1; workspace/audit service (HCM-02) is the neutral writer |
| WP-12 | Packaging/surface parity | Bounded delivery — Phase 7 distribution shipped (source-bundling metapackage, wheel entrypoints) |
| **WP-13** | Legacy migration | **Genuinely open** — one recorded legacy exception remains; scope it only when a migration is requested |
| WP-14 | Docs/release | Delivered — 2026-10-12/2026-10-25 consolidations and routing documents |

WP definitions/dependencies: [execution roadmap](../specs/deep-audit-remediation-2026-09-17/12_execution_roadmap.md).
Its dated defect claims require live verification before task selection.

| Track / packet | Status | Evidence / next decision |
|---|---|---|
| HCM-01 | Characterization recorded | HCM README; measured defects are not approved policy |
| HCM-02 | Implemented (qualified) | Disposition in `hcm-02-disposition.md`; service + callers migrated, job-runner bypass migrated PR #134; OQ-H1/H2 remain recorded |
| HCM-03 | Partial | `console/api/pipelines.py` delegates models/validation to `scholar_harness.pipeline`; transport removal not claimed |
| HCM-04 | Partial / subpacket recorded | Stage coordinators exist under `pipeline/`; HCM-04e identity policy implemented; whole-packet closure not claimed |
| HCM-05 | Adopted | PR #107, harness + canonical-kit integration |
| HCM-06 | Merged (PR #133, `6575209`) | Read-only presentation API (8 GET routes with generation-currentness + loopback CORS); UI-04 live wiring |
| AG-00/01/02 | Historical assessment / delivered controls | AG completion record; AG-02 PR #106 |
| AG-03A/B/C | Delivered, bounded Windows evidence | AG plan; B PR #121, C PR #125/#126; **POSIX unproven** (15 isolation tests skip on non-Windows) |
| AG-04 | Merged | PR #130 `28e5c42`, close-out #131 `f4b5f60`; deterministic scaffold, not model accuracy |
| AG-05 | Conditional | Real screening backend, fresh held-out set, independent labels and authorized prospective design required |
| AG-06/07 | Deferred | Extraction/synthesis need separate evidence and authority decisions |
| UI-01–04 / 04a | Delivery recorded | UI-04a PR #109; mock-backed UI does not establish real backend integration |
| UI-05 | Shipped (PR #137, `95c5665`) | Evidence-lineage route and trace view |
| UI-06 | Open | Audit activity route/watch surface; not shipped |
| UI-07 | Read + action API merged (PR #134, `aa6e2f0`) | Read API + UI-04 live wiring (PR #133); protected action API: pairing-code approval, idempotent redemption, CLI begin, journal migration, browser-verified 6/6 |
| F1 | Merged | PR #127, `465c386`: documentation gate selection |
| F2–F5 | Deferred follow-ups | Audit; no broad test-deletion campaign |
| F6 | KEEP | Public-surface evidence insufficient for replacement |
| Kit ownership note | Recorded in this documentation candidate | Sample shows no demonstrated duplication; kit move deferred |
| UAV pilot | Preliminary delivered; **close-out open** | PR #123: two preliminary sources, zero accepted charting; protocol v0.3 is `PROVISIONAL_NOT_FROZEN`; researcher freeze + confirmations remain |

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
