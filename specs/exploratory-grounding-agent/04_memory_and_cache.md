# 04 — Memory & Cache Architecture

## 1. Two-tier storage principle

| Tier | Location | Ownership | Git | Retention |
| :--- | :--- | :--- | :--- | :--- |
| **Exploratory scratchpad** | `.cache/inception_recon/` | recon sandbox only | **ignored** (`.gitignore:19`) | Per-session; pruned on success or age |
| **Canonical workspace** | `workspaces/<slug>/` | workspace-manager (+ all downstream kits) | tracked (metadata) | Project lifetime |

**Hard invariant:** the recon sandbox NEVER writes to `workspaces/`. Workspace scaffolding is created only at Step 5 emission, and only by `workspace-manager`.

## 2. Cache layout (under `.cache/inception_recon/`)

```
.cache/inception_recon/
├── sessions/
│   └── <session_id>.json          # session state (see schema below)
├── pools/
│   └── <sha>_pool.json            # deduped candidate pool for a probe (10-25 docs)
└── terms/
    └── <sha>_terms.json           # distilled terms + anchor docs
```

- `<sha>` = SHA-1 of the **cache key** (Section 3). Content-addressed → identical probes reuse identical files (idempotent re-runs, low disk cost).
- A probe is a pure function of its key: same key, same pool file, same terms file.

## 3. Hierarchical cache key

Structured as a URL-style path so it can be logged, grepped, and content-addressed:

```
v1/<providers>/y<year_min>-<year_max>/q/<sha256(text)>
```

| Segment | Meaning |
| :--- | :--- |
| `v1` | schema/format version bump gate (invalidate-all on bump) |
| `<providers>` | e.g. `openalex,semanticscholar,crossref,arxiv` (join-provenance) |
| `y<year_min>-<year_max>` | year window: `y2000-2026`, or `y2015` for a single year |
| `q/<sha256(text)>` | normalized query text (case-fold, collapse whitespace, strip trailing punct). Normalization is required so `"Drones & AI."` and `"drones & ai"` share a key. |

Example:

```
v1/openalex,semanticscholar,crossref,arxiv/y2000-2026/q/9f1c66e14a0f4c6b879d25e7c1bb6c8491e03c55d0c53b1c1d4a0e2d9b8a7f
```

## 4. Session schema (`sessions/<session_id>.json`)

```jsonc
{
  "schema_version": "v1",
  "session_id": "uuid-string",
  "created_at": "2026-09-12T10:15:00Z",
  "intent_hint": "drones & AI for crop disease detection",
  "clarified_axis": "edge UAV real-time pathology",
  "probes": [
    {
      "probe_id": "uuid-string",
      "query_text": "drone crop disease detection edge inference",
      "cache_key": "v1/openalex,semanticscholar,crossref,arxiv/y2015-2026/q/<sha256>",
      "pool_file": "pools/<sha>_pool.json",
      "terms_file": "terms/<sha>_terms.json",
      "pool_size": 18,
      "requested_urls": 3,
      "fetched_urls": 2
    }
  ],
  "validated_direction": {
    "direction_id": 2,
    "title": "YOLO-based edge UAV multispectral disease detection",
    "anchor_dois": ["10.xxxx/example-a", "10.xxxx/example-b"]
  },
  "delta_probes": [
    {
      "probe_id": "uuid-string",
      "query_text": "multispectral UAV plant disease detection",
      "cache_key": "…",
      "pool_file": "…",
      "terms_file": "…"
    }
  ]
}
```

## 5. Pool file schema (`pools/<sha>_pool.json`)

```jsonc
{
  "cache_key": "…",
  "created_at": "…",
  "docs": [
    {
      "id": "openalex|W2345678901",
      "provider": "openalex",
      "doi": "10.xxxx/....",
      "title": "…",
      "abstract": "…",
      "year": 2022,
      "citations": 43,
      "oa_url": "https://…"
    }
  ],
  "fulltexts": {
    "10.xxxx/example": {
      "source": "scholar-pdf-kit",
      "path_abs": "…",
      "chars": 48213
    }
  }
}
```

## 6. Terms file schema (`terms/<sha>_terms.json`)

```jsonc
{
  "cache_key": "…",
  "micro_taxonomy": [
    {"term": "disease detection", "freq": 14, "anchor_dois": ["…"]}
  ],
  "metrics": {"mAP": 12, "F1": 9, "FPS": 5},
  "datasets": {"PlantVillage": 6, "RoCoLe": 2},
  "schools": [
    {"label": "visible-light CNN", "n": 11, "anchor_dois": ["…"]}
  ]
}
```

## 7. Invalidation & hygiene

| Action | Rule |
| :--- | :--- |
| Content version bump | Bump `v1` → repo-wide invalidation |
| Provider list change | Key changes → new content-address (old files stay, orphaned, prunable) |
| Year-window change | Key changes → new content-address |
| Re-run same query | Cache hit — no network calls, no re-distill |
| Corrupt cache file | Treated as a miss; re-fetch & overwrite |
| Successful emission | Prune session file (optional); pools/terms may be retained short-term for delta probes |

## 8. Provenance hand-off to the audit ledger

At workspace genesis, `workspace-manager` logs a `GENESIS` event into `audit/journal.jsonl`. For grounded inception, the event **must** include a `recon_context` block:

```jsonc
{
  "event": "genesis",
  "recon_context": {
    "session_id": "…",
    "probe_count": 2,
    "cache_keys": ["v1/…", "v1/…"],
    "pool_sizes": [18, 9],
    "anchor_dois": ["10.xxxx/…"]
  }
}
```

This makes the lineage of every term in the final protocol auditable end-to-end: `GENESIS event → session → cache key → pool file → anchor DOI → Document`.