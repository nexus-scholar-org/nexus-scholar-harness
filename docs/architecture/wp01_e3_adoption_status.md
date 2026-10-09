# WP01-E3 Adoption Status

- **Packet:** E3 — Stable Chunks and Index Lineage Boundary (in progress)
- **Base:** `fcc2467335a5f72f6b0dcfdca11579bd49f64478` (PR #60, harness E3 identity-limbs adoption)
- **Related closure:** E2 runtime-acceptance — PR #63 (merged `193209d`) publishing extraction through the frozen acceptance gate
- **Canonical kit pin:** `15a7a5a50a0394ed87b9b8b3c153081e10ec36ad` (scholar-rag-kit PR #13)

## Current state

E3’s identity-limbs boundary is operational. Stage 6 refuses indexing when no accepted `DocumentManifestArtifact` exists (pre-flight `DOCUMENT_MANIFEST_NOT_ACCEPTED`) leaving no `rag/chroma_db`; identity limbs (`workspace_id`, `protocol_fingerprint`, `corpus_snapshot_fingerprint`, `document_id`) are preserved end-to-end. `AcceptanceContext` is derived only from recorded workspace state and carried on the candidate. Screening/collector remains published via `accept_artifact`.

## What remains (specification-first)

Per `docs/architecture/wp01_packet_e3_implementation_handoff.md` (Status: `SPECIFICATION`) and `specs/deep-audit-remediation-2026-09-17/05_rag_kit_spec.md:54–74` (RAG-001–RAG-021), the full E3 definition of done requires:

- Index manifest v1 sidecar (deterministic, content-addressed chunk identities; limbs+chunk identity separation)
- Replacement/recovery semantics and currentness rules
- Declared API/CLI/MCP parity
- Legacy read-only handling and completeness guarantees
- Audit parameters/path completeness
- Harness adapter verification (proofs against live backend) per the seven-step acceptance
- Resolution of the 19 indexing defects enumerated in §1.4 of the handoff

## Evidence
- Post-merge (193209d): targeted 72/1, full 730/6, conformance 131/2, count freshness 5/5
- Negative coverage: 153/153 (no manifest/registry/publication record/chroma_db on refusal)
- Hermetic Stage 6 subprocess tests use rag-kits deterministic mock embedder with HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE

## Status
**E3: in progress.** Identity-limbs adoption is merged; full E3 implementation remains open.

## Next work
Complete the remaining E3 acceptance-adapter and ledger work as specified in
the E3 handoff. E4 now has an implementation-ready definition at
`docs/architecture/wp01_packet_e4_negative_proof_handoff.md`, but remains
blocked until E3 has an approved completion report.
