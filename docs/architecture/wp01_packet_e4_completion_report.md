# WP01 Packet E4 completion report

**Date:** 2026-10-09
**Status:** `CLOSED_WITH_RESIDUAL_DEBT` (bounded evidence-currentness proof)
**WP-01 milestone:** closed with the residual obligations listed below.
**Runtime merge:** PR #77, `cc33c318191635a3d0f4511d353b8534641fde98`.
**Tested repair:** `e07289e9e7ce2cc387477f136403dee491a91113`.

## Closure decision and boundaries

The operator requested direct narrow repairs, verification, and merge instead
of another agent review cycle, then authorized this qualified close-out.
This records a completed bounded milestone. It does not assert that all
original E3/E4 obligations are proven or weaken the frozen Contract v1.
The original handoff remains the source of the outstanding obligations.

A-D are adopted according to the Developer Compass. E1 and E2 have their own
completion reports. E3's approved completion report retains three blocked
harness execution rows. E4's six named mutation cases, control, replay, seal
checks, and renewed-generation case are merged. No downstream retrieval or
synthesis behavior or scientific quality has been separately validated here.

## Observed mutation results

| Case | Entry and observation | Publication state |
|---|---|---|
| E4-NEG-001 | Synthetic PDF byte change; E2 publication creates a different ART lineage. Stage 6 returns FAILED; kit run-report action is RAG_INDEX_RUN_REJECTED with no new manifest ID. The test does not pin a more specific error code. | Old E3 record remains historical; no new accepted index or success event. |
| E4-NEG-002 | Changed extracted text refuses E2 replay with STALE_EXTRACTED_BODY. Additional repair regression refuses Stage 6 with that code and adapter replay at check 4 with VALIDATION_ERROR. | Accepted index remains unchanged; stale-text Stage 6 preflight creates no backend. |
| E4-NEG-003 | Changed max_chunk_chars moves configuration/index fingerprints; stale declared digests are refused by accept_index_candidate at check 5. | No acceptance or success event; files unchanged. |
| E4-NEG-004 | Changed embedding model moves index fingerprint; stale declared digests are refused by the adapter at check 5. | No acceptance or success event; files unchanged. |
| E4-NEG-005 | Changed protocol fingerprint refuses at check 3 with PROTOCOL_FINGERPRINT_MISMATCH. | No authoritative publication. |
| E4-NEG-006 | Missing visible chunk is named by the typed verifier; adapter replay refuses with BACKEND_STATE_INCONSISTENT. | No acceptance or success event; historical record unchanged. |

Unmodified replay succeeds without rewriting the accepted record or emitting
a new success event. Reuse still verifies current evidence and backend state.
The rebuild case first refuses text changed under old E2 provenance, then
constructs a separate generation with changed source/text accepted through E2
before indexing; its E2 artifact, IDX manifest, and index fingerprint differ.
It does not prove an in-place migration of an existing review generation.

## Remediation and ownership

PR #77 includes harness-owned repairs in extraction_producer.py,
index_acceptance.py, and orchestrator.py. The early idempotency return no longer
bypasses fingerprint, backend, extraction-currentness, or final parent checks.
Stage 6 checks recorded E2 file hashes before indexing changed extracted text.
The existing replay test was corrected to require backend verification.
No kit source, pin, frozen schema, or UI change was required by these repairs.
The earlier report's "no defects" verdict is superseded by this evidence.

## Tested versions and fixture

The merged runtime tree is byte-identical to the tested repair tree. Relevant
canonical pins read from `.agents/plugins/nexus-scholar/plugins.json`:

- PDF: `3c024c37071b49265cfea6e713c1c9065e2a2cc0`.
- RAG: `15a7a5a50a0394ed87b9b8b3c153081e10ec36ad`.
- Agent: `79ffe421dfea2a2b6e4c02fdff651e6d23ce9b92`.
- Protocol: `4e10f25c25a1b150ce518348d211c7771683a9b7`.
- Search: `911d864fcb6a706d4c0339f80524a46f591e2cad`.

Fixture: `tests/e2e/fixtures/e4_golden/`. Its seal file is
`seal_manifest.json`, SHA-256
`67366db3183a9cb30a697d72b4d771166b1f82362317cb4d2c6d60dea1dfbf9e`.
The seal verifies checked-in fixture bytes; LF attributes stabilize checkout
bytes. Fixture regeneration contains timestamps/run identifiers and is not
claimed to produce identical bytes across runs.

## Validation

- Repair regression selection: 11 passed (E4 plus adapter replay test).
- Post-merge E4 selection: 10 passed; contract baseline current.
- PR #77 repair CI: 9/9 passed, run `37935418077`.
- Scripts lint and four generator checks passed.
- Local full suite: 769 passed, 9 skipped, 13 failed. The same 13 failing test
  IDs independently failed on original PR head `e6b8b45` in a pristine worktree;
  they are not claimed green. No new failing test ID remained.
- Earlier agent approval applies to the original candidate, not these direct
  repairs. The repair was directly verified and passed fresh CI under the
  operator's authorized shortcut; no new independent agent approval is claimed.

## Residual obligations and measured limits

| Obligation | Owner / next bounded action |
|---|---|
| E3-NEG-021, 022, 050 remain blocked in the E3 completion ledger. Canonical kit evidence does not replace missing harness execution evidence. | Harness installer: repair editable dependency overwrite, verify imports against the recorded pin, then execute these three rows without loosening expectations. |
| Local suite's 13 pre-existing failures remain. | Harness test maintenance: reconcile old replacement/backend mocks against the typed service; retain real refusal and no-publication coverage. |
| E4-NEG-001 uses synthetic PDF bytes and metadata extraction; no real E1 acquisition service or PDF parser runs in this fixture. Source mutation refusal on a genuine E1-accepted document is not established by this case. | PDF/harness integration proof: a separate genuine acquisition-to-extraction mutation case, with recorded parents and backend observations. |
| Mutation readers are injected typed readers derived from the manifest, rather than independently persisted live backend snapshots. Positive builds use Chroma, but six-case real-backend mutation coverage is not claimed. | Harness integration proof: independent backend observations if stronger physical-store guarantees are required. |
| Fixture regeneration is not byte-deterministic. | Fixture maintenance: separate stable content sealing from volatile run metadata if identical regeneration becomes required. |
| User-owned reviewer configuration was intentionally preserved. | Operator governance: recharter that role separately; do not label its elevated permissions an accidental edit. |

These are carried obligations, not silently passing checks. Qualified closure
permits planning the separate core modularity roadmap; it neither starts that
refactor nor asserts universal evidence-currentness, product readiness, or
validated retrieval/synthesis. A small real review is a useful next evaluation.
