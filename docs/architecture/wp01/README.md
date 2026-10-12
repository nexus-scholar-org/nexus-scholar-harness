# WP-01 — Contract v1 adoption: completion and residual debt

WP-01 (Contract v1 adoption) is **closed with residual debt**. The implemented
boundary rules are in [`evidence-boundaries.md`](./evidence-boundaries.md); the
normative contract is the frozen set at `docs/architecture/`. The per-packet
handoff and completion documents were removed in the 2026-10-12 cleanup and
remain in git history.

## Delivered packets

| Packet | Verdict | Canonical merge(s) | Headline |
|---|---|---|---|
| **A–D producers** (protocol / corpus / acceptance / screening) | adopted | harness PR #42 `ca6a77b` | Producers adopted; Compass records A/B/C/D adopted. |
| **E1** — acquired-document boundary | `APPROVE` | pdf-kit PR #1 `858911f`; agent-kit PR #1 `6050e0c`; harness PR #47 `baaeeb4` | Kit commits exact PDF bytes for an accepted study; agent kit declares acquisition unsupported on MCP and rejects without I/O; harness vendors both at full-SHA pins. |
| **E2** — extracted-text boundary | `APPROVE` | pdf-kit PR #2 `6ec6e3b`, PR #3 `0430e40`; agent-kit PR #2 `deebfad`; harness PR #50 `0fb6655`; runtime acceptance PR #63 `193209d` | Deterministic `pdf-extraction-manifest-v1` sidecar + non-authoritative Contract candidate; extraction published through the frozen acceptance gate. |
| **E3** — chunks / index-lineage boundary | `APPROVE` (blocked-with-cause; later all-live) | rag-kit PR #12 `f108fa8`, PR #13 `15a7a5a`; harness PR #64 `657b9d5`, #65 `3255333`, #69 `bb40f9d`, #70 `fb3629d`, #74 `38c89bc`, #75 `e09e909` | Index Manifest v1 sidecar with `CHK-` identity; `index-acceptance-v1` seven-step acceptance; accepted record `rag/index/accepted.json` + §6.6 audit event. |
| **E4** — adversarial evidence-currentness proof | `CLOSED_WITH_RESIDUAL_DEBT` | harness PR #77 `cc33c31` (tested repair `e07289e`) | Six mutation cases + rebuild case merged; unmodified replay succeeds without rewriting the record. |
| **E3 residual repair** | done | canonical main `8aea528` | Installer authority fixed; the three formerly-blocked ledger rows now execute (`PATH_OUTSIDE_WORKSPACE`, stale-hash `PARTIAL`); **29-row ledger has no MISSING entries**. |

## Validation evidence (as recorded at close)

- E3 adoption-status evidence post-merge `193209d`: targeted 72/1, full 730/6, conformance 131/2, count-freshness 5/5; negative coverage 153/153 (no manifest/registry/record/chroma_db on refusal).
- E4 mutation results: per-case codes in [`evidence-boundaries.md`](./evidence-boundaries.md) §E4.
- The E1/E2/E3 completion reports each recorded their conformance runs (E1-NEG-030/044/047; E2 parent-bound/`EXT-*`/atomicity/recovery; E3 seven-step acceptance).

## Residual debt (do not overclaim)

1. **Qualified closure.** WP-01 is closed with debt; it does not assert that all original E3/E4 obligations are proven, and it does not weaken the frozen Contract v1.
2. **No downstream scientific validation.** Retrieval, scoring, synthesis, consensus, claim verification, risk-of-bias, methodology-matrix, and agent-loop behaviour are **not** validated here — those are later work packages.
3. **E4 rebuild ≠ in-place migration.** The rebuild case creates a separate generation; in-place migration of an existing review generation is unproven.
4. **Kit sidecars are not Contract registry types.** `pdf_acquisition_manifest`, `pdf_extraction_manifest`, and `index_manifest` stay outside the frozen registry; the harness is the sole Contract acceptance/publication owner.
5. **Proof-bound vs declaration-only ledger rows** retain their original limits; they are not all end-to-end runtime proofs.

## Related consumers

`DEVELOPER_COMPASS.md` routes current work; the E2 boundary document is read at
runtime by `tests/conformance/test_e2_extraction_boundary.py` (now pointed at
[`evidence-boundaries.md`](./evidence-boundaries.md)); the E3 index-lineage
boundary is asserted by `tests/conformance/test_e3_index_lineage_boundary.py`.
