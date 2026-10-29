# Harness core modularity (HCM) track

Entrypoint for the HCM track: extracting neutral services from `scholar_harness`
without behaviour change.

## Current

| Document | Role |
|---|---|
| [`harness_core_modularity_roadmap.md`](./harness_core_modularity_roadmap.md) | **Plan/roadmap** for the track (packet order, deferrals, handoff). |
| [`hcm_05_mcp_recon_adapter_characterization.md`](./hcm_05_mcp_recon_adapter_characterization.md) | HCM-05 characterization (ADOPTED; PR #107). |
| [`hcm-02-disposition.md`](./hcm-02-disposition.md) | HCM-02 evidence disposition (IMPLEMENTED, qualified; see close-out below). |
| HCM-06 read presentation API | Merged (PR #133, `6575209`): 8 read-only GET routes with generation-currentness + loopback CORS; UI-04 live wiring. |

## Close-out record (2026-10-29)

HCM is **closed as a qualified track**: the neutral services and the two
presentation APIs are delivered, while HCM-03/04 remain partial and are not
claimed as whole-packet closure. No further HCM implementation is scheduled.

| Packet | Disposition | Evidence / limit |
|---|---|---|
| HCM-01 | Characterization recorded | 17 characterization tests; three defects recorded as observed behaviour, not policy |
| HCM-02 | **Implemented (qualified)** | `workspace/audit.py` is the neutral writer; direct callers migrated; the one genuine job-runner bypass was migrated in PR #134. OQ-H1 (failure contract) and OQ-H2 (test count) remain recorded in the disposition. |
| HCM-03 | **Partial** | `console/api/pipelines.py` delegates models/validation to `scholar_harness.pipeline`; the console transport module still exists, so "pipeline models fully out of transport" is not claimed. |
| HCM-04 | **Partial / subpacket** | Stage coordinators exist under `src/scholar_harness/pipeline/`; HCM-04e identity policy (bridge-or-refuse) is implemented. No packet-level closure of every stage extraction is claimed. |
| HCM-05 | **Adopted** | Harness adapter + canonical agent-kit integration (PR #107); pins and vendored snapshot synchronized at the time of delivery. |
| HCM-06 | **Merged** | PR #133 (`6575209`): 8 read-only GET routes, generation-currentness, loopback CORS; consumed by the UI-04 live wiring. |

Next-step statement for this track: **none scheduled**. Reopen only with a new
packet that names the transport removal (HCM-03) or an uncovered orchestration
stage (HCM-04); do not infer whole-packet completion from the partial rows.

## Completion record

Dated packet documents were removed in the 2026-10-12 consolidation; the
must-survive facts are here and the originals remain in git history.

| Packet | Outcome | Evidence |
|---|---|---|
| **HCM-01** — workspace/audit characterization | **Executed 2026-10-09** (isolated checkout): 17 new characterization tests passed; the HC1-1…HC1-7 result table recorded observed behaviour, unproven limits, and three defects recorded *not fixed* (non-object manifest raises untyped `AttributeError`/`TypeError`; corrupt-JSON `sync_state` silently rebuilds). HCM-02 must not adopt those as policy. | new `tests/unit/test_workspace_audit_characterization.py` |
| **HCM-04e** — verification identity policy | **IMPLEMENTED POLICY — Option B (bridge-or-refuse)**: a Stage-3 fallback `SCI-` identifier cannot reach Stage 6 without an accepted `document_manifest`; with no accepted manifest the stage refuses (`RAG_INDEX_REJECTED`) before any backend and never consults `verified.json` workspace ids. `SCI-` is a STUDY legacy alias only; `WST-`/`WSP-<32hex>` is the registered workspace form. | tests `test_vei_07_*`, `test_vei_07b_*`, `test_vei_08a_*`, `test_vei_08b_*` |

Any policy that mints, refuses, or quarantines identity needs its own packet
gate before it changes.

HCM-02/03 have no packet documents; the roadmap is their only definition. HCM-06 read API is merged (PR #133); UI-07 protected action API is merged (PR #134, `aa6e2f0`) including the job_runner journal migration.
Runtime work follows the test-gate policy (`docs/architecture/test_gate_policy.md`).

