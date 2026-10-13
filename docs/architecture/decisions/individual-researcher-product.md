# Product direction: individual researcher application

Date: 2026-10-13. Status: user-selected product direction; implementation sequence
below is proposed, not a new authorization to change runtime or deployment.

## Decision and first user

Prioritize an individual researcher conducting a literature review directly in
Nexus. The user explicitly selected this direction in discussion. Build a
local research service with a browser review interface as the initial delivery
target. CLI and MCP remain complementary advanced interfaces. The local-browser
implementation is a recommendation; choosing this user does not certify a
deployment architecture or approve every feature below.

The initial journey is: define a provisional protocol, retrieve a bounded
literature set, review recommendations, preserve overrides, authorize final
screening decisions, and export a transparent screening record. Full-text
charting and synthesis follow as separately validated capabilities.

## Shared foundations and delivery options

| Component | Product contribution |
|---|---|
| Kits | Scientific capabilities: protocol, search, PDF, RAG, graph, bibliography and verification |
| WP | Truthful outcomes, identity, lineage and correctness across capabilities; WP-01 is qualified closure, not validation of all later science |
| HCM | Shared workspace, audit and pipeline services behind CLI/MCP/UI; modular monolith, not a new package per service |
| AG | Scientific recommendations separated from review, authority and publication; current Windows evidence does not establish cloud/POSIX enforcement |
| UI | Understandable review, sources, uncertainty, progress and recovery; mock screens are not connected production workflows |
| Distribution | Installation and entrypoints; does not establish usable workflows or hosted operations |
| Research pilot | Tests codebook usefulness and scientific claims; agent critique is not independent human labeling |
| Test improvements | Reduce unnecessary validation and maintenance while retaining consequential regression protection |

Execution location, interaction surface, model supplier and approval/data owner
are separate choices. MCP is an interface, not a replacement research engine.
Local storage does not imply local inference: disclose configured provider data
flows. An external agent with unrestricted operator-level privileges is not
isolated merely because it calls MCP.

| Delivery option | Suitable user | Additional work beyond shared core |
|---|---|---|
| CLI / external agent + MCP | Technical researcher or integrator | Supported backend/host, tool boundaries, setup and separate trustworthy review |
| Local browser app | Individual researcher | Local startup, presentation API, separately reviewed action API, jobs and recovery |
| Desktop packaging | Researcher blocked by installation friction | Installer, updates, service lifecycle and platform validation |
| Institution-hosted web app | Lab/review team | Accounts, assignments, permissions, concurrent jobs, storage and backups |
| Managed SaaS | Team wanting managed operation | Tenant isolation, cloud authority model, costs/quotas, support and data lifecycle |
| Hybrid local/cloud | Collaboration with local processing needs | Synchronization, conflicts, connectivity and trust across locations |

Desktop, institution hosting, SaaS and hybrid are deferred options, not rejected
directions. There is no commitment to build them concurrently.

## Proposed priorities and decision gates

1. Finish AG-04's bounded review/approval/publication interaction. A deterministic
   scaffold demonstrates interaction, not an operational LLM or scientific accuracy.
2. Use that interaction with the researcher to identify friction. Select one
   supported worker backend and one representative pilot; keep formal accuracy
   evaluation gated on prospective design and actual reference labels.
3. Define the presentation boundary through UI-07 / HCM-06 after their prerequisites
   are reconciled. Read-only presentation is distinct from approval/mutation API.
4. Connect one real screening UI journey to harness services. Show drafts,
   unresolved items, source evidence, override history, failures and final state.
   Keep technical provenance inspectable rather than mandatory navigation.
5. Prove simple local startup and resumability. Choose desktop packaging only if
   installation is a demonstrated obstacle.
6. Promote the UAV two-paper preliminary pilot through valid provisional lineage
   where supported; expand extraction/synthesis only after source and role gates.

Select WP repairs by the supported user journey, rechecking dated findings.
Do not require completion of every historical WP/HCM packet before a bounded
release, and do not assume a bypass because a feature is convenient. Broader
collaboration/SaaS requires a separate architecture and operating decision.

## Status discipline

[UPCOMING_WORK.md](../../UPCOMING_WORK.md) is the cross-track tracker. Packet
documents retain detailed evidence. Status answers must check live main, open
PRs and active work before presenting a tracker snapshot as current. Distinguish
merged, active/reported, planned, deferred, qualified and unverified states.
Update affected tracker rows in delivery close-out; do not duplicate completion
tables across indexes. No automatic monitor or complete packet audit is implied.
