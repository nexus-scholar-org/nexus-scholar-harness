# 12 — Semantic Grounding (M0.6)

> **Status:** Scaffolded spec — design locked, implementation pending (coder/tester/reviewer loop).
> **Date:** 2026-09-13
> **Extends:** `04_memory_and_cache.md` (schema), `08_milestones.md` (M0.6), `10_task_list.md` (T6.x), `09_mcp_integration.md` (tool contracts), `05_tool_contracts.md` (kit seams).
> **Motivated by:** `11_honest_review.md` §3.1 (micro-taxonomy query-term noise), §3.2 (lexicon = configuration), §3.3 (naive adjacency).
> **API facts verified 2026-09-13:** OpenAlex `search.semantic` (embeddings-based, documented Aug 2026); OpenAlex **Concepts deprecated → replace with Topics** (~65k concepts/6 levels vs ~4.5k topics/4 levels, OpenAlex-native + CWTS); S2 `/paper/search*` runs S2's custom-trained ranker on keyword input (bulk = the resilient choice); S2 **Recommendations API is the SPECTER2/embedding surface** (not currently wired); OpenAlex polite-pool `mailto` now ignored, API keys required for sane rate limits.

---

## 1. Motivation

Two honest-review findings M0.6 kills with **classifier-grounded data** instead of more heuristics:

1. **Search is keyword-only.** The kits send `params["search"]=<text>` (stemmed + relevance-scored) to OpenAlex. OpenAlex now ships `search.semantic=` (embeddings over title+abstract): same-cost, meaning-matched discovery. A recon probe that runs BOTH modes gets keyword-struck docs *and* semantic neighbors.
2. **Taxonomy is keyword-frequency.** `micro_taxonomy` top terms are a restatement of the query (`deep 20 / learning 19 / detection 18` live). OpenAlex labels every work with **Topics** (classifier-produced, hierarchical, scored). Aggregating topics across a pool gives a *domain expert's vocabulary* with anchors by construction — not the query's words.

Goal: **semantic discovery + topic-grounded taxonomy**, additive and default-unchanged.

---

## 2. Verified provider facts (2026-09-13)

| Fact | Implication |
| :--- | :--- |
| `works?search.semantic=<q>` returns meaning-matched works (embeddings over title+abstract); regular `search=` is stemmed keyword; both relevance-sorted. | New optional **mode**; keep keyword as default. |
| Work records carry `topics` (active, 4-level: domain→field→subfield→topic, with `score` 0-1) and `primary_topic`; **`concepts` is deprecated** (still returned, not updated), 6-level. | Capture `topics`; fall back to `concepts` for legacy works. |
| New OpenAlex works are topic-first; older works may have empty `topics` but populated `concepts`. | Normalizer handles both; missing ⇒ empty list. |
| S2 `/paper/search/bulk` uses a custom-trained ranker on **keyword** input; the true embedding surface is **Recommendations API** (SPECTER2), addressed by paper/paper-set, not text. | S2 text search stays keyword; SPECTER2 snowball is a **stretch** item (T6.7). |
| `mailto=` polite pool ignored since ~Feb 2026; API-key rate limits. | `settings.openalex_key` must be set for reliable semantic runs; document it. |

---

## 3. Design (three seams, zero behavior change on default)

### Seam A — Search mode
- **Kit** (`scholar-search-kit`): `scholar_search.models.Query` gains `semantic: bool = False`. `OpenAlexProvider._build_params` selects `search.semantic` vs `search` from it. Year `filter` unchanged.
- **Harness** (`recon/engine.py`): `ReconEngine` and `probe(..., semantic=False)`; helpers construct `Query(..., semantic=semantic)`.
- **Cache-key mode segment** (`recon/cache_key.py`): keyword keys stay byte-identical (`v1/<providers>/y<range>/q/<sha256>`); semantic keys insert a mode segment:
  ```
  v1/<providers>/y<range>/m/semantic/q/<sha256>
  ```
  Same text+providers+window, different mode ⇒ different key ⇒ different pool (no cross-mode cache collision). Existing `parse_cache_key` extended to tolerate and expose the optional `mode`.

### Seam B — Work-topic capture
- **Kit**: `Document.topics: list[dict] | None`; `OpenAlexProvider._normalize_document` populates from `raw.get("topics")`, else `raw.get("concepts")`; each entry `{"source": "openalex_topics"|"openalex_concepts", "id", "display_name", "score"}` (`score: float | None`, None when absent).
- **Pool schema §5**: optional per-doc `topics: [...]` (present for OpenAlex docs; omitted otherwise). Pool writer (`recon/engine.py`) copies it through.

### Seam C — Topic taxonomy + adaptive integration
- **Distiller** (`recon/distiller.py`, `distill_pool(pool, lexicon=None)` — signature unchanged): emits a new top-level `topics` array in the terms dict:
  ```jsonc
  "topics": [
    {"label": "Computer vision & pattern recognition", "n": 7,
     "score": 0.87, "anchor_dois": ["10.xxxx/a", "10.xxxx/b"]}
  ]
  ```
  Aggregation: per pool doc, take its per-topic max score; `n` = distinct docs carrying the label; `score` = mean of per-doc max scores (documented, deterministic); `anchor_dois` sorted. Sort `(-n, label)`. **Anchored by construction** (label exists only if ≥1 pool doc carries it).
- **Adaptive** (`recon/adaptive.py`): `plan_followups` also treats **thin topics** (`n ≤ 2`, ≥1 anchor) as candidates (`{"term": <topic label>, "reason": "<n> direct hits, <m> adjacent", "school_n": n, "triggered": true}`). M0.4 merge/cap semantics unchanged.

---

## 4. Schema deltas (concrete)

| Doc | Change |
| :--- | :--- |
| `04_memory_and_cache.md` §3 | Add cache-key mode segment table row + example. |
| §4 session schema | Optional `"semantic": true` on probe entries (informational). |
| §5 pool schema | `docs[].topics` optional array (`source/id/display_name/score`). |
| §6 terms schema | New top-level `topics` layer (`label/n/score/anchor_dois`). |
| §7 invalidation | New row: search-mode change ⇒ key changes ⇒ new content-address. |
| `05_tool_contracts.md` | Document the kit seams: `Query.semantic`, `Document.topics`, `ReconEngine.semantic`, distiller `topics`. |

---

## 5. MCP surface (M0.6 changes)

- `recon_probe`: add `semantic: bool` (default `False`) → threaded to `Query`. Result JSON otherwise unchanged (session_id/cache_key/n_docs/pool_path).
- `recon_distill`: result gains `topics` (top-N list, `label/n/score/anchor_dois`).
- `recon_delta`: `followups` may contain thin-topic candidates (same `term/reason/confidence/school_n` contract); result unchanged otherwise.
- Lineage rule (T5.5) unchanged: every result carries `cache_key`; semantic probes' keys carry `/m/semantic/`.

---

## 6. Milestone DoD (M0.6 — all must hold)

1. `recon_probe(topic, semantic=True)` issues the OpenAlex `search.semantic` param (verified by payload-captured fake + a hermetic test); its cache key contains `/m/semantic/`; the keyword default key is byte-identical to M0.5.
2. Pool docs from the OpenAlex normalizer carry `topics` (with `concepts` fallback); §5 schema honored; docs without topics stay clean.
3. `distill_pool` emits a deterministic, anchored `topics` layer (`label/n/score/anchor_dois`); re-run is byte-identical.
4. `plan_followups` triggers for thin topics (`n ≤ 2`, anchored) with a non-empty reason; M0.4 merge/cap invariants hold.
5. Default behavior byte-identical and schema-backward-compatible: keyword probes still send `search=`; existing 173-suite stays green; no new deps (stdlib + existing kits).

**Non-goals (explicitly out of M0.6):** S2 Recommendations/SPECTER2 snowball (T6.7 stretch); wiring topics into the wizard's direction proposal; replacing `micro_taxonomy` or `schools` (they remain additive); any LLM-based labeling.

---

## 7. Task list (mirrors `10_task_list.md` M0.6)

- **[ ] T6.1** Kit: `Query.semantic` + OpenAlex `search.semantic`; harness: `ReconEngine/probe(..., semantic=)` + cache-key mode segment; tests (param selection, mode key, keyword default unchanged).
- **[ ] T6.2** Kit: `Document.topics` capture (topics→concepts fallback, normalized entries); pool §5 writer carries topics; tests (topics, concepts fallback, absent).
- **[ ] T6.3** Distiller `topics` layer (deterministic, anchored, scored); §6 schema; tests (aggregation math, sort, byte-determinism, empty-when-none).
- **[ ] T6.4** Adaptive thin-topic triggers; tests (thin topic → candidate + merge path intact; healthy topic no-op).
- **[ ] T6.5** MCP: `recon_probe(semantic=)`, `recon_distill`/`recon_delta` topics in results; `tests/test_mcp_recon.py` additions (semantic param passthrough, topics surfaced, lineage intact).
- **[ ] T6.6** QA: full suite + ruff + hermetic suites; **live smoke**: one keyword vs one semantic probe on the same topic — assert pools differ, topics layer present, no workspace writes.
- **[ ] (stretch, not in M0.6 DoD) T6.7** S2 Recommendations/SPECTER2 semantic snowball (thin-topic → embedding-similar papers), gated behind a follow-up milestone.

---

## 8. Acceptance / testing strategy

- Hermetic-first: fixture pools with hand-authored `topics`; fake `search_fn` capturing the outgoing `params` for the mode-selection test; existing deterministic fixtures must remain byte-identical for the no-topics path.
- Cross-mode assertion: same topic, `semantic=False` vs `True` → different cache keys and (in live smoke) different pools.
- Live smoke (post-restart, with `OPENALEX_API_KEY` set): `recon_probe("grape disease detection deep learning edge deployment", semantic=True)` direct comparison against the M0.5 keyword session `rec_c04ba5…`.

---

## 9. Risks & mitigations

| Risk | Mitigation |
| :--- | :--- |
| `topics` empty on many legacy works (concepts deprecated but populated) | concepts fallback; empty ⇒ no `topics` layer; taxonomy degrades gracefully to today's behavior. |
| Semantic search requires API key rate limits | Config note in `05_tool_contracts.md`; keyword mode unaffected; fail with a clear message if `openalex_key` unset for semantic mode. |
| New cache-key segment silently breaks lineage expectations | `parse_cache_key` + `mode` exposure; docs; tests assert M0.5 keys parse identically. |
| Topic scores not comparable across providers | Only OpenAlex contributes topics in M0.6; S2 FoS stays out of scope. |
| Scope creep into the wizard | Explicit non-goal; `inception.py`/`cli.py` untouched in M0.6. |