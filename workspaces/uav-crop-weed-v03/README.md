# uav-crop-weed-v03 — protocol v0.3 amendment host workspace

Purpose: dedicated, isolated host for protocol revision v0.3 so the pilot workspace
(`../uav-crop-weed-reliability/`, v0.2, fingerprint `sha256:a1fd8d2a82e0a5fca77deabb
136ba84f73451full` — authoritative: `sha256:a1fd8d2a82e0a5fca77deabbad360a1d8190d2d
017d3ffa38342d8ac7ff73451`) and the demo clone stay byte-preserved.

## Provenance chain

- Parent: `../uav-crop-weed-reliability/` — protocol v0.2, `PROJECT_INITIALIZED`
  2026-10-12 → `GENESIS` → `PROTOCOL_AMENDED` (v0.1→v0.2) — full ledger in its
  `audit/journal.jsonl`.
- This workspace: intent v0.3 authored in conversation at the researcher's request
  (assistant-drafted); compiled here with the deterministic compiler. Compile event
  = `GENESIS` in this workspace's ledger. Authorship is a mechanical record, NOT
  authenticated scientific approval. **FROZEN 2026-10-29** (delegated researcher
  decision; see `AMENDMENTS.md` §v0.3 freeze). Protocol freeze is not screening
  confirmation: the 566 agent decision files remain unconfirmed by a human.

## Contents

- `intent.json` — v0.3 researcher-approved intent packet (transcribed verbatim).
- `protocol.json` — compiled product of the compiler (the only canonical protocol
  here; canonical fingerprint in `protocol.sha256`).
- `protocol.sha256` — canonical fingerprint: `sha256:f81e6c58aefb3159cb679ca87c4a
  83382dca199e0b02bb12ac409c15f8a4f755`.
- `SCREENING_CRITERIA.md` — rendered by the compiler.
- `charting.schema.json` + `CHARTING_CODEBOOK.md` — **v0.3.1 charting pair,
  frozen 2026-10-31 with F1 repaired**. The v0.3.0 bytes were frozen 2026-10-29
  with limitation F1 (no `evidence_state`↔content coupling); v0.3.1 imports the
  v0.2 cell logic as per-dimension conditional shapes and refuses every
  populated-under-absence case. SHA-256 `91dbe0c8f81034ccb5f7eea903a11d3d96e9a50bc42914eea6ec7d0fe7596b42`. Charting rows may now be produced
  under v0.3.1 (none accepted yet). Records: `validation_v031.json` and
  `audit/charting_validation_matrix_v031.json`; the superseded v0.3.0 bytes are
  kept as `audit/charting_schema_v030_superseded.json`.
- `validation.json` — attributed machine-gate record (engineer: orchestrator agent).
- `AMENDMENTS.md` — v0.2→v0.3 record.

## Hard boundaries (do not violate)

1. Never mutate `../uav-crop-weed-reliability/` frozen inputs or the demo clone
   (`../nexus-scholar-harness-demo/workspaces/uav-pilot-demo/`).
2. No screening, freezing, or search execution without the researcher gates
   (see `RESEARCHER_DECISIONS.md` in the pilot workspace). The **protocol freeze
   itself was recorded 2026-10-29** under delegated instruction; screening
   confirmation, PENDING resolution and protocol-text export remain gated.
3. Never hand-edit `protocol.json`; edit `intent.json`, recompile, re-fingerprint.
4. The 5-file search-kit patch applied in the demo clone is a separate park
   (canonical-repo stream blocked; see `../../operations` history and demo journal).
   It is NOT part of this workspace's provenance.
