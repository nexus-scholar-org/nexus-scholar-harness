# 02 · Handoff contracts

This file specifies **who writes what, when** across the inception stack. The
contracts are file-based — every handoff completes when a file appears on disk,
and must be logged to `audit/journal.jsonl`.

## 2.1 The emission chain (classic and grounded)

```text
[methodology-copilot interview | inception-agent Stage 6]
   │  intent.json  (IntentPacket — winner contract, intent_generator_spec.md)
   ▼
scholar-protocol compile --fingerprint                 → protocol.json
scholar-protocol render-criteria                       → SCREENING_CRITERIA.md
   ▼
workspace-manager scripts/init_project.py              → scaffold + INDEX.md
workspace-manager scripts/log_event.py PROJECT_INITIALIZED
workspace-manager scripts/log_event.py GENESIS         → provenance (incl. recon_context)
scholar-harness sync                                   → project.json / INDEX.md refresh
```

Rules:

1. **Emission is gated on explicit user confirmation** (`inception-agent` Stage 6
   human gate; methodology-copilot asks before writing workspaces).
2. The driver runs `init_project.py` **first** so `log_event.py` has a live
   workspace to write into. The scaffold `slug`, `title`, `paradigm`, and RQ set
   come from the finalized `intent.json` (never guessed).
3. All writes go through `workspace-manager` scripts or the `scholar-*` CLIs.
   Agents never hand-append to `journal.jsonl`.

## 2.2 The `GENESIS` event and `recon_context` provenance

`GENESIS` is the provenance record establishing *why* a project exists. It is a
hard convention for every project with a protocol:

- **`PROJECT_INITIALIZED`** — written by `init_project.py` at scaffold time.
- **`GENESIS`** — written after `intent.json` + `protocol.json` exist. It references
  the protocol fingerprint `protocol_json.sha256` and, for grounded inception,
  the recon provenance.

`GENESIS` writes provenance in **two forms** (this keeps the LEDGER readable while
preserving full context):

| Field | Content |
| :-- | :-- |
| `audit/recon_context.json` (sidecar) | **Full** provenance: original seed, cache keys, direction candidates, qualitative assessment, pool/purity gate snapshots, confidence, selected direction map, lexicon details. |
| `GENESIS` event inline | Bounded summary: direction, anchors, cache key, confidence, rationale. |

Compatibility: on Windows the engine/flow passes provenance **as a file path**
(argv-safe) rather than a huge JSON string (`inception.py::log_genesis`);
consumers honor both by merging sidecar facts over inline summary.

## 2.3 Grounded delegation (inception-agent → methodology-copilot)

At Stage 6 the inception-agent hands the driver back to the interview layer:

- **Input contract:** selected direction map (`{direction, anchors, cache_key,
  confidence}`) + the distilled `recon_context` and `intent.json` draft.
- **Expected output:** finalized `intent.json` (paradigm + RQ set aligned with the
  chosen direction), then the emission chain of §2.1.
- The interview conventions belong to methodology-copilot; inception-agent must
  not improvise a new emission schema.

## 2.4 Audit event conventions (top-level, by stage)

| Stage | Events expected in `journal.jsonl` |
| :-- | :-- |
| Scaffold | `PROJECT_INITIALIZED` |
| Protocol | `GENESIS` (+ recon sidecar for grounded) |
| Search | `SEARCH_RUN`, `SEARCH_DEDUP`, `SEARCH_VERIFY` |
| Screening | `SCREENING_BATCH`, `SCREENING_DECISION`, `SCREENING_REPORT`, `SCREENING_DUAL_RELIABILITY` |
| Extraction / RAG | `EXTRACTION_RUN`, `RAG_INDEX`, `RAG_QUERY` |
| Synthesis | `SYNTHESIS_RUN`, `MATRIX_EXTRACT` |
| Verify (phase4) | `VERIFY_RUN`, `VERIFY_CONSENSUS`, `VERIFY_ROB` |

Event `action` strings must match the `log_event.py` catalog, (including the
`reports` scan that auto-registers `prisma_screening_report.md` etc.) so
`query_project.py --events` and the `INDEX.md` sync stay consistent.

## 2.5 Failure handling

- Any handoff step writing to a workspace that does not exist **fails loudly** —
  run `init_project.py` first.
- `batch_log.py` is the preferred writer for multi-event sequences (one process,
  one append) over repeated `log_event.py` spawns.
- Parity guarantee: grounded-direction output may not silently diverge from the
  wizard; drift is caught by comparing against `scholar_harness.inception`
  functions (see the parity helper).