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

## Release posture

- **M0.1–M0.3**: usable via CLI wizard (Option A), default behavior preserved.
- **M0.4–M0.5**: agent-first enhancements; CLI remains a thin wrapper.
- `--resume` (resumable wizard) is **explicitly out of scope** for the M0.x line and listed as a future extension in `03_lifecycle.md`.