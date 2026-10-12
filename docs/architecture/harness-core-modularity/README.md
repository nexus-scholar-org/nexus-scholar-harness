# Harness core modularity (HCM) track

Entrypoint for the HCM track: extracting neutral services from `scholar_harness`
without behaviour change.

## Current

| Document | Role |
|---|---|
| [`harness_core_modularity_roadmap.md`](./harness_core_modularity_roadmap.md) | **Plan/roadmap** for the track (packet order, deferrals, handoff). |
| [`hcm_05_mcp_recon_adapter_characterization.md`](./hcm_05_mcp_recon_adapter_characterization.md) | Current close-out packet (ADOPTED; next is HCM-06 gating). |

## Completion record

Dated packet documents were removed in the 2026-10-12 consolidation; the
must-survive facts are here and the originals remain in git history.

| Packet | Outcome | Evidence |
|---|---|---|
| **HCM-01** — workspace/audit characterization | **Executed 2026-10-09** (isolated checkout): 17 new characterization tests passed; the HC1-1…HC1-7 result table recorded observed behaviour, unproven limits, and three defects recorded *not fixed* (non-object manifest raises untyped `AttributeError`/`TypeError`; corrupt-JSON `sync_state` silently rebuilds). HCM-02 must not adopt those as policy. | new `tests/unit/test_workspace_audit_characterization.py` |
| **HCM-04e** — verification identity policy | **IMPLEMENTED POLICY — Option B (bridge-or-refuse)**: a Stage-3 fallback `SCI-` identifier cannot reach Stage 6 without an accepted `document_manifest`; with no accepted manifest the stage refuses (`RAG_INDEX_REJECTED`) before any backend and never consults `verified.json` workspace ids. `SCI-` is a STUDY legacy alias only; `WST-`/`WSP-<32hex>` is the registered workspace form. | tests `test_vei_07_*`, `test_vei_07b_*`, `test_vei_08a_*`, `test_vei_08b_*` |

Any policy that mints, refuses, or quarantines identity needs its own packet
gate before it changes.

HCM-02/03/06 have no packet documents; the roadmap is their only definition.
Runtime work follows the test-gate policy (`docs/architecture/test_gate_policy.md`).

