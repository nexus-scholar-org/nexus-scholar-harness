# Typed index (`scholar-rag index` / `index_workspace`)

The authoritative E3 publication path. CLI and Python API call the same T-90
shared service (`index_workspace`, `index_service.py:752`), so they cannot
answer the same request differently. Pinned kit `15a7a5a50a0394ed87b9b8b3c153081e10ec36ad`.

## CLI flags (`cli.py:83-122`)

One required positional plus ten required options — none minted, discovered,
or defaulted:

| Flag | Required? | Notes |
|---|---|---|
| `docs_path` (positional) | required | Directory of extracted Markdown (or a single file); scopes which files the run may read |
| `--parent-view` | required | JSON file holding the ACCEPTED parent view (adapter's output, never discovered) |
| `--journal` | required | Explicit path this run's own event is appended to; never searched for |
| `--workspace-root` | required | Workspace root; sidecar + commit intent are written beneath it; `journal_path`/`docs_path` are bound against it and refused if absolute/escaping |
| `--run-id` | required | Explicit `RUN-` identity; never minted here |
| `--created-at` | required | Explicit RFC3339 timestamp |
| `--producer-version` | required | Stated kit version, never read from the package |
| `--producer-commit` | required | Full 40-hex producer commit (`^[0-9a-f]{40}$`) |
| `--embedder-provider` | required | Embedding identity limb: provider, stated |
| `--embedder-model` | required | Embedding identity limb: model, stated |
| `--embedder-dimension` | required | Embedding identity limb: dimension, stated |
| `--db-path` | optional (default `./chroma_db`) | CWD-relative default — always pass an absolute `<ws>/chroma_db` in workspaces |
| `--collection` | optional (default `scholar_docs`) | Collection name |
| `--hnsw-space` | optional (default `cosine`) | Distance space recorded in the sidecar |
| `--embedder` | optional (default `sentence-transformers`) | Runtime provider selector (`sentence-transformers`, `openai`, `gemini`, or `mock`); the `--embedder-*` identity limbs above are still required |
| `--model-name` | optional | Runtime model override (e.g. `all-MiniLM-L6-v2`) |
| `--embedder-distance-metric` | optional (default `cosine`) | Identity limb with a default |
| `--embedder-model-revision` | optional | Identity limb for pinned revisions |
| `--recovery-probe-run-id` | optional | Report T-70's 7.5 row for this run id on the result |
| `--format` | optional (default `human`) | `human` or `json` (`json` prints `result.envelope()`, byte-identical to the API) |

`--workspace-id` was removed from `index` (it survives only on `query`).
There is **no** `--api-key` flag on `index` (that flag exists only on `extract`).

## Exits and refusal

`0` SUCCESS / `2` REFUSED / `3` PARTIAL / `4` FAILED
(`INDEX_SERVICE_EXIT_CODES`, `index_service.py:223`; `1` is deliberately
unused). Typed refusals (`IndexServiceValidationError` and kin) return a
`REFUSED` result with a closed-vocabulary code — never a traceback, never an
empty success. Unexpected exceptions become `FAILED`/`INTERNAL_ERROR`.

## What the run does and publishes

1. Binds every extracted file to the accepted-parent record that admitted it
   (`cli.py:224` assembly; eligibility = parent claim, reachability =
   `docs_path` containment). Disagreement is refused, not skipped.
2. Chunks under the explicit identity (`chunker.py:121`, closed option set
   `chunker.py:83`, `min_chunk_chars` merge `chunker.py:531`).
3. Publishes an `IndexManifest` v1 sidecar (`MANIFEST_SCHEMA_VERSION =
   "index-manifest-v1"`, `index_manifest.py:130`).
4. Commits through the R1–R7 replacement protocol (`IndexReplacement.run`,
   `replacement.py:1385`; recoverable commit intent, `replacement.py:638`)
   with live-set proof via `verify_backend` (`index_verifier.py:563`).
5. Appends its own run report (`RAG_INDEX_RUN_BUILT` /
   `RAG_INDEX_RUN_REJECTED`, `index_service.py:209`) to the **stated**
   journal destination only. Pointing `journal_path` at the canonical
   adapter ledger `audit/journal.jsonl` is refused (G-9) — the kit does not
   write the harness continuity event.

## Authoritative vs candidate (read carefully)

This run's sidecar + run report are the kit's own publication claim. The
§6.6 **accepted-record** event belongs to the harness `index-acceptance-v1`
adapter (`src/scholar_harness/index_acceptance.py` `accept_index_candidate`,
schema `index-acceptance-v1`), which publishes `rag/index/accepted.json` +
the canonical `RAG_INDEX_BUILT` §6.6 event — a `SUCCESS` here (sidecar +
`RAG_INDEX_RUN_BUILT` run report) is not an acceptance verdict. E3 status:
live harness rows including `E3-POS-005` golden parity are proven; ledger
completeness is `MISSING == ()`
(`tests/conformance/test_e3_index_lineage_boundary.py:2079,:2355`).

## Python API (same service)

```python
from scholar_rag.index_service import IndexServiceRequest, index_workspace
from scholar_rag.replacement import ChromaReplacementView
from scholar_rag.index_verifier import ChromaVisibleSetReader
from scholar_rag import get_embedder

embed = get_embedder(provider="sentence-transformers")  # "mock" hermetic; "openai"/"gemini" need keys
result = index_workspace(request, backend=..., reader=..., embedder=embed, workspace_root="<ws>")
result.envelope()  # the one machine-readable envelope; CLI --format json prints this
```

`IndexServiceRequest` (`index_service.py:400`) is closed, frozen, strict:
`sources` (six identity limbs per document + text + workspace-relative
path), `parent_view`, effective `chunker_configuration`, backend/collection,
six embedder-identity limbs, `created_at`/`producer_version`/`producer_commit`,
workspace-relative `journal_path` + `docs_path`. Anything inferred is a
refusal (`E3-NEG-025/026` family).
