# 08 — Implementation Milestones (M0.x) with DoD

> Each milestone is independently deliverable and gated by its **Definition-of-Done** acceptance criteria. Scope discipline: no milestone extends the `inception` CLI semantics that exist today (`--root/--no-scaffold` only) until M0.3 opts in via a new flag.

## M0.1 — Recomms / Empirical Surface Scan (sandboxed, deterministic)

**Scope:**
- `ReconEngine` (single probe): build `SearchEngine(providers=[...])` query, dedup via `Deduplicator`, cap pool at **10-25**, persist `pools/<sha>_pool.json` under `.cache/inception_recon/`.
- Hierarchical cache key (Section `04`), content-addressed.
- Probe → pool idempotent (same key ⇒ same pool file, no network).

**Real kit deps (verified):**
`scholar_search.engine.SearchEngine.search_all(q, dedup=True)`, `scholar_search.dedup.Deduplicator`, `Query`, `scholar_search.export.Exporter.json`.

**DoD — all must hold:**
1. `ReconEngine.probe("...")` returns `(pool_file, n)` where `10 ≤ n ≤ 25`.
2. `pools/` file carries the exact cache key; re-run with the same key mutates **nothing** on disk.
3. No dependency on `scikit-learn`/`keybert`/LLM at this stage (pure kit + stdlib JSON).
4. Zero writes into `workspaces/` (assert path prefix).

## M0.2 — Distiller (pure-Python term-frequency baseline)

**Scope:**
- `distiller.py`: term-frequency micro-taxonomy + metrics/datasets keyword extraction over the pool JSON.
- Terms emitted only when anchored to at least one pool doc.
- Baseline is deterministic; LLM augmentation is a **gated, later** extra, never default.

**DoD — all must hold:**
1. Given a pool of 8 abstracts, distiller emits `terms/` JSON with `freq ≥ 1` per term and `anchor_dois` lists.
2. A term with zero evidence anywhere in the pool **cannot** appear (filter is hard).
3. Re-running on the same pool produces byte-identical output.
4. No scikit-learn / keybert import anywhere in the module graph.

## M0.3 — `--grounded` wizard flag (user-visible, optional)

**Scope:**
- Seam: `cli.py:84-94` → `inception_command()` → `run_wizard()` — add `--grounded` opt-in.
- On `--grounded`: insert Step-2→Step-4 loop (probe → distill → propose directions) after Stage-1 topic capture, before the Stage-2 refraction grid.
- Researcher validates a direction or issues a delta probe; validated intent flows into the **existing** `IntentPacket` → `compile_protocol` path.

**DoD — all must hold:**
1. `uv run scholar-harness inception --help` lists `--grounded`; **without** the flag, behavior is byte-identical to today.
2. Wizard shows ≥1 grounded direction with ≥2 real citation anchors before protocol compile.
3. Every emitted `protocol.json` term maps to an `anchor_doi` recorded in the session.
4. `GENESIS` event contains `recon_context` (session_id, cache keys, pool sizes, anchor_dois).

## M0.4 — Adaptive Probe Horizon

**Scope:**
- Recursively refine probes: a thin sub-school triggers an automatic follow-up probe to confirm scarcity before it is proposed as a "gap".
- Gap-confidence scores surfaced to the researcher (e.g., "3 direct hits, 2 modernization-adjacent").

**DoD — all must hold:**
1. For a detected thin sub-school, ReconEngine issues ≥1 follow-up probe and merges results into the session without re-cluttering the pool cap.
2. Gap direction proposal includes explicit `confidence` reason string.
3. All merged docs still carry cache keys and anchor DOIs.

## M0.5 — Full FAIR-ified Memory + Agent Interop (MCP surface)

**Scope:**
- Expose `recon_probe` / `recon_distill` / `recon_delta` as `nexus_*` MCP tools (pattern: `tools/scholar-agent-kit/src/scholar_agent/server.py`).
- Methodology Copilot can drive the full lifecycle conversationally; session state survives across turns via `.cache/inception_recon/`.

**DoD — all must hold:**
1. Three new MCP tools registered, each returning machine-readable JSON (paths/keys), not prose.
2. A copilot turn "probe & distill drift" produces a session with ≥1 pool + ≥1 terms file + anchor DOIs.
3. No state lost between copilot turns for the same `session_id` (state on disk).
4. All tool results include the cache key (traceable lineage).

## M0.6 — Semantic Grounding (topics + semantic search modes)

> Full spec: `12_semantic_grounding.md`.

**Scope:**
- OpenAlex **semantic search mode** (`search.semantic=`, embeddings) as an opt-in mode; cache-key mode segment so keyword and semantic probes never collide.
- Capture OpenAlex **Topics** (with deprecated-Concepts fallback) into `Document`/pool schema.
- Distiller emits a classifier-grounded **`topics` layer** (`label/n/score/anchor_dois`) anchored by construction.
- Adaptive horizon extended: **thin topics** (`n ≤ 2`) trigger follow-up probes like thin schools.

**DoD — all must hold:**
1. `recon_probe(topic, semantic=True)` issues the OpenAlex `search.semantic` param (hermetic payload capture); its cache key contains `/m/semantic/`; keyword default key byte-identical to M0.5.
2. OpenAlex pool docs carry `topics` (concepts fallback); §5 schema honored; docs without topics stay clean.
3. `distill_pool` emits a deterministic, anchored `topics` layer; re-run byte-identical.
4. `plan_followups` triggers for thin topics; M0.4 merge/cap invariants hold.
5. Default behavior byte-identical + backward compatible; existing full suite stays green; no new deps.

**Non-goals (M0.6):** S2 Recommendations/SPECTER2 snowball (stretch T6.7), wizard/topics direction proposals, replacing `micro_taxonomy`/`schools`, LLM labeling.

## M0.7 — Evaluation Gates + Autonomous Loops (IMPLEMENTED — local; formal approval + release via PR)

> Specs: `13_evaluation.md` (metrics/ReconBench), `14_agent_loops.md` (loops + seams). Implemented end-to-end with a **human-in-the-loop approval**: gates + seams shipped as local commits with every seam hermetic-tested; the roadmapped items that were explicitly out of M0.7's stdlib/no-LLM scope (T7.5 school-purity audit, T7.6 ReconBench corpus) are **deferred with reasons** in `10_task_list.md`, not silently dropped. Default behavior is byte-identical across every added seam.

**Shipped scope:**
- **T7.1** APR gates (`recon/gates.py` `compute_apr`/`assert_apr`, ≥1 anchor DOI per concept/synonym) — hermetic tests; the "in CI" aspect is a **recorded deferral** (`PR.3`) because CI does not run pytest today (see decision log in `10_task_list.md`).
- **T7.2** QEI in `distiller.py` — `distill_pool(query_text=...)` computes the top-10 **echo index**; `assert_qei` gate (target ≤ 0.3); surfaced tool-/artifact-level for loop/agent consumers.
- **T7.3** GAP B seam — `ReconEngine.corpus_count` (OpenAlex `meta.count`, client released in `finally`, failure → -1) + `saturation_label` (`scant|sparse|dense|unknown`); `recon_delta` followups carry `corpus_total`/`saturation_label`.
- **T7.4** GAP A seam — `recon_distill(lexicon_json=...)` via `merge_lexicons` with provenance hashing in the artifact prefix (`distilled_lx<sha1[:12]>`).
- **T7.7** Canonical recon root — `NEXUS_RECON_ROOT` env override honored by both MCP server and CLI (fixes 11 §3.5 CWD trap).
- **T7.8** Headless emission — `inception --auto-select` / `--direction-id <N>` + softened non-interactive exit; interactive-gate stays default.

**DoD M0.7 — all hold:**
1. stdlib + regex only in the harness path (no new deps, no LLM/sklearn); kit APIs reused, none re-invented.
2. Default behavior byte-identical (each seam omits new keys/params under defaults, verified by byte-identical tests).
3. Full suite green — **223 passed / 3 skipped / 0 failed**; M0.7-affected files 106/106 pass (hermetic only).
4. Every seam hermetic-tested; review-fix round applied (corpus 0-fidelity, provider client close, qei production wiring).
5. T7.5/T7.6 explicitly deferred with reasons; release posture unchanged (M0.5–M0.6 documented).

**Non-goals (M0.7):** LLM-judge school-purity audit (T7.5), ReconBench curated corpus (T7.6), enforcing QEI as a hard wizard discard, CI pytest step (PR.3).

## Release posture

- **M0.1–M0.3**: usable via CLI wizard (Option A), default behavior preserved.
- **M0.4–M0.5**: agent-first enhancements; CLI remains a thin wrapper.
- `--resume` (resumable wizard) is **explicitly out of scope** for the M0.x line and listed as a future extension in `03_lifecycle.md`.