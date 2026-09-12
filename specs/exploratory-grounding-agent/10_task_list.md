# Exploratory Grounding Agent — Implementation Task List

> **Status:** Live checklist for implementing `specs/exploratory-grounding-agent/`
> **Milestone spec:** [`08_milestones.md`](./08_milestones.md) (this list mirrors M0.1–M0.6; each task carries its DoD clauses)
> **Dev process:** Orchestrator roles — `coder` (writes code+tests), `tester` (runs verification), `reviewer` (reviews diff against the spec DoD). The orchestrator (opencode **build** agent) dispatches via the Task tool and checks boxes here when the DoD holds.
> **Git rule:** per the pull-request-gate skill — never push to `origin`; improvements ship via fork + PR. Do NOT commit during a work session unless asked.

---

## Legend

Each task's box is ticked only when:
1. the code + tests exist and are attributed to this task,
2. `uv run pytest` passes for the harness+kit tests that touch it,
3. `reviewer` confirmed the diff satisfies the M0.x DoD clause referenced.

---

## Task 0 — Recon package scaffold

- [x] **T0.1** `src/scholar_harness/recon/__init__.py` exports `ReconEngine`, `distill`, `cache_key`.
- [x] **T0.2** `src/scholar_harness/recon/cache_key.py` — hierarchical key builder (`v1/<providers>/y<year_min>-<year_max>/q/<sha256>`), query normalization, `parse_cache_key`.
- [x] **T0.3** `tests/recon/test_cache_key.py` — normalization (case/whitespace/punct), determinism, idempotent key for same query.
- [x] **T0.4** `tests/recon/__init__.py` (or conftest) so pytest collects the new `recon/` tests with the existing `pythonpath`.

---

## M0.1 — Empirical Surface Scan (ReconEngine.probe)

Spec: `08_milestones.md` M0.1 · architecture `02_architecture.md` §2 · lifecycle `03_lifecycle.md` Step 2 · cache `04_memory_and_cache.md` §2-3

- [x] **T1.1** `ReconEngine.probe(query, providers, year_min, year_max, max_results)` → builds `SearchEngine(providers=[...])`, calls `await search_all(q, dedup=True)` (10-25 cap), persists `pools/<sha>_pool.json` under `.cache/inception_recon/`.
- [x] **T1.2** Cap enforcement: pool size clamped to **10-25** regardless of provider returns (zero-padding not allowed; docs >25 trimmed).
- [x] **T1.3** Cache-hit path: same cache key re-runs **mutate nothing** and make **no network calls** (no provider list re-built).
- [x] **T1.4** No `workspaces/` writes: assert `CacheError`/guard if a target path ever resolves inside `workspaces/`.
- [x] **T1.5** No scikit-learn/keybert imports anywhere in the `recon/` module graph (DoD M0.1.3).
- [x] **T1.6** Tests: `tests/recon/test_engine.py` — probe returns `(pool_file, n)` with `10 ≤ n ≤ 25`; idempotency (second call: unchanged file bytes + no HTTP, mocked); no-workspaces guard.

**DoD M0.1:** all of `T1.1-T1.6` + no new deps.

---

## M0.2 — Distiller (pure-Python term-frequency baseline)

Spec: `08_milestones.md` M0.2 · lifecycle `03_lifecycle.md` Step 3 · terms schema `04_memory_and_cache.md` §6

- [x] **T2.1** `src/scholar_harness/recon/distiller.py` — term-frequency micro-taxonomy (`freq`, `anchor_dois`) from `pools/<sha>_pool.json`.
- [x] **T2.2** metrics/datasets keyword extraction (observed-in-pool only).
- [x] **T2.3** Hard anchor filter: a term with zero evidence in the pool **cannot** appear (`remove_unanchored`).
- [x] **T2.4** Determinism: same pool → byte-identical JSON output.
- [x] **T2.5** No scikit-learn/keybert import (pure stdlib + regex).
- [x] **T2.6** Tests: `tests/recon/test_distiller.py` — anchors enforced, empty-pool → empty terms, byte-identical re-run.

**DoD M0.2:** all of `T2.1-T2.6`.

---

## M0.3 — `--grounded` wizard flag (user-visible, optional)

Spec: `08_milestones.md` M0.3 · seam `cli.py:84-94` → `inception_command()` → `run_wizard()` · deployment `06_deployment_options.md` Option A

- [x] **T3.1** `typer.Option(--grounded)` added to `inception_command`; default behavior **byte-identical** without the flag.
- [x] **T3.2** `run_wizard(..., grounded=...)` inserts Step-2→Step-4 loop after Stage-1 topic capture, before Stage-2 refraction grid.
- [x] **T3.3** Direction proposal surfaces **≥ 1 grounded direction with ≥ 2 real citation anchors** (DOI) before any protocol compile.
- [x] **T3.4** Delta probe path wired (existing cache reuse + 1 targeted follow-up).
- [x] **T3.5** Validated intent flows through the **existing** `IntentPacket → compile_protocol` path (no parallel protocol emitter).
- [x] **T3.6** `GENESIS` audit event carries `recon_context` (session_id, cache_keys, pool_sizes, anchor_dois).
- [x] **T3.7** Tests: `tests/test_inception_grounded.py` — `--help` lists `--grounded`; without flag output identical to today; protocol.json terms all map to anchors; GENESIS event has `recon_context`.

**DoD M0.3:** all of `T3.1-T3.7`.

---

## M0.4 — Adaptive Probe Horizon

Spec: `08_milestones.md` M0.4 · lifecycle `03_lifecycle.md` Step 4 (gap confidence)

- [x] **T4.1** Thin sub-school detection: a school with `n ≤ 2` triggers an automatic follow-up probe before being proposed as a gap.
- [x] **T4.2** Gap directions carry explicit `confidence` reason string (e.g., "3 direct hits, 2 modernization-adjacent").
- [x] **T4.3** Merged follow-up docs keep cache keys + anchor DOIs; pool cap respected (no re-clutter).
- [x] **T4.4** Tests: `tests/recon/test_adaptive.py` — thin-school trigger + merge, confidence string non-empty.
- [x] **T4.5** **Cross-field lexicon**: externalize the hard-coded `_METRICS`/`_DATASETS`/`_SCHOOLS` pattern tables into a pluggable `DomainLexicon` (`src/scholar_harness/recon/lexicon.py`). Default keeps today's tables (backward compatible, existing distiller tests untouched); `merge_lexicons(base, extra)` hook so ANY field (oncology, education, robotics, chemistry…) registers its own metric/dataset/school patterns; `distill_pool(pool, lexicon=None)`. Micro-taxonomy stays purely empirical (already field-agnostic). Tests prove a non-CV domain with a custom lexicon detects its own metrics/datasets and does NOT emit unrelated defaults.

**DoD M0.4:** all of `T4.1-T4.5`.

---

## M0.5 — FAIR Memory + MCP Agent Interop

Spec: `08_milestones.md` M0.5 · MCP `09_mcp_integration.md` §2,§5

- [x] **T5.1** `recon_probe` MCP tool registered in `tools/scholar-agent-kit/src/scholar_agent/server.py` (returns JSON paths/keys, not prose).
- [x] **T5.2** `recon_distill` MCP tool registered (returns `terms/` file path + anchor DOIs).
- [x] **T5.3** `recon_delta` MCP tool registered (session-id aware, cache reuse).
- [x] **T5.4** Session state persists across copilot turns via `.cache/inception_recon/sessions/<session_id>.json`.
- [x] **T5.5** Tool schema: every result includes its `cache_key` (traceable lineage).
- [x] **T5.6** MCP test: `tests/test_mcp_recon.py` — tools listed, `recon_probe` returns machine-readable path + count.

**DoD M0.5:** all of `T5.1-T5.6`.

---

## M0.6 — Semantic Grounding (topics + semantic search modes)

Spec: `08_milestones.md` M0.6 · full design `12_semantic_grounding.md`

- [x] **T6.1** Kit: `Query.semantic` + OpenAlex `search.semantic` param; harness: `ReconEngine`/`probe(..., semantic=False)` + cache-key mode segment `/m/semantic/` (keyword default byte-identical). Tests: outgoing-param payload capture; mode key; keyword default unchanged. ✅ `test_providers.py` (23 tests incl. 2 live-caught API fixes: page-pagination, filter-omission); keyword key byte-identical to pre-M0.6 literal; parse handles 5-part (keyword) + 7-part (semantic) and rejects malformed modes.
- [x] **T6.2** Kit: `Document.topics` capture from `raw["topics"]` with deprecated-`concepts` fallback (`source/id/display_name/score`); pool §5 writer carries topics. Tests: topics, concepts fallback, absent. ✅ Normalizer/entry-shape tests + live pool carries real OpenAlex topics (5/5 openalex docs).
- [x] **T6.3** `distill_pool` emits a deterministic `topics` layer (`label/n/score/anchor_dois`, anchored by construction). Tests: aggregation math, sort, byte-determinism, empty-when-none. ✅ `_topic_layer` per-doc+label max score, mean→4dp/None, DOI-anchor-only; byte-identical re-run.
- [x] **T6.4** `plan_followups` thin-topic triggers (`n ≤ 2`, anchored). Tests: thin topic → follow-up + merge intact; healthy topic no-op. ✅ Shared `_thin_candidates`, dedup keeps school before topic; M0.4 merge/cap invariants untouched.
- [x] **T6.5** MCP: `recon_probe(semantic=False)` threaded through; `recon_distill`/`recon_delta` surface `topics`; `tests/test_mcp_recon.py` additions (param passthrough, topics surfaced, lineage intact). ✅ hermetic passthrough + topics surfaced; lineage (T5.5) intact.
- [x] **T6.6** QA: full suite + ruff + M0.6 hermetic suites; **live smoke** — one keyword vs one semantic `recon_probe` on the same topic (pools differ, topics layer present, zero workspace writes). ✅ full suite 193 passed/3 skipped/0 failed; ruff clean (scripts/ + M0.6 scope); live smoke below (QA.6).

**DoD M0.6:** all of `T6.1-T6.6` + default behavior byte-identical + no new deps.
**Stretch (not M0.6 DoD):** T6.7 — S2 Recommendations/SPECTER2 semantic snowball (thin-topic → embedding-similar papers), gated behind a follow-up milestone.

---

## M0.7 — Evaluation Gates + Autonomous Seams (PROPOSED — not gate-approved)

> Specs: `13_evaluation.md` (metrics/ReconBench) · `14_agent_loops.md` (loops + GAP A/B) · `08_milestones.md` M0.7 stub. Tasks **unticked** — gating not yet approved; effort/targets refined before dispatch.

- [ ] **T7.1** APR CI gate — assert every protocol `core_concept`/`synonym` has ≥1 anchor DOI (promote `test_inception_grounded` invariant to CI).
- [ ] **T7.2** QEI in `recon/distiller.py` + test gate on top-10 terms (≥50% non-echo; target QEI ≤ 0.3 per `13_evaluation.md` §3.1).
- [ ] **T7.3** GAP B: uncapped corpus-count seam (OpenAlex `meta.count` / S2 totals) → `corpus_total` + `saturation_label` (`scant|sparse|dense`) on `recon_delta` followups.
- [ ] **T7.4** GAP A: `recon_distill(lexicon_json=...)` MCP param — validate shape, `merge_lexicons(DEFAULT, extra)`, provenance hash in artifact name.
- [ ] **T7.5** School-purity sampled audit script + LLM-judge rubric (50 papers/school sample).
- [ ] **T7.6** ReconBench runner (`scripts/reconbench/`) — corpus is manual curation (30–50 published SLRs).
- [ ] **T7.7** Canonical recon root: `NEXUS_RECON_ROOT` env override enforced by both MCP server and CLI (fix 11 §3.5 CWD trap; no bare `Path.cwd()` resolution).
- [ ] **T7.8** Headless emission: `inception --auto-select` / `--direction-id <N>` + softened exit (11 §3.6); interactive-gate stays default.

**Proposed DoD M0.7:** stdlib/no-LLM in the harness path; default behavior byte-identical; full suite green; each seam hermetic-tested + live-smoked.

---

## QA Gate (run by `tester` before any task is ticked)

- [x] **QA.1** `uv run pytest` — full suite green (existing 25 + new `recon/` + inception tests). ✅ 173 passed / 3 skipped (post-M0.5, measured after code tidy); **rerun post-M0.6 (2026-09-13): 193 passed / 3 skipped / 0 failed** (+20 M0.6 tests over baseline, incl. 2 live-caught API-fix tests).
- [x] **QA.2** `uv run ruff check scripts/` — no NEW errors introduced (pre-existing ~15 tolerated; verify diff attribution not ours). ✅ "All checks passed!" (measured 2026-09-12).
- [x] **QA.3** `python scripts/install_plugins.py` still resolves kits (no kit re-vendoring regressions) — smoke. ✅ methodology unchanged; note: this host fails `install_plugins.py` at the file-copy step because the LIVE MCP server (`scholar-agent.exe`) locks its own exe — environmental (pre-existing), not a code regression. Kit resolution verified indirectly: MCP tool registry imports resolve (`SearchEngine`, `Deduplicator`, `Exporter`…) and the full suite is green.
- [x] **QA.4** `uv run scholar-harness inception --help` shows `--grounded` once M0.3 lands. ✅ `--grounded` listed (measured 2026-09-13).
- [x] **QA.5** Manual smoke on a real topic (e.g. `nexus_discover` probe) produces a real deduped pool + terms with anchor DOIs. ✅ **LIVE run completed post-restart (2026-09-13):** `recon_probe` "grape disease detection deep learning edge deployment" → 25-doc pool (session `rec_c04ba5…`, cache key `v1/openalex,semanticscholar,crossref,arxiv/y2019-2026/q/a1fb97e3…`); `recon_distill` → micro-taxonomy + metrics(F1/accuracy/mAP/precision/recall), datasets(PlantVillage/ImageNet), 5 anchored schools; `recon_delta` → 2 thin schools auto-probed (LLM n=1, multispectral n=1, reason "1 direct hits, 20 adjacent"), merged pool capped 25 (`dropped_n` 50), lineage cache keys merged (3). Nexus Scholar MCP dispatch (2026-09-13, 24.03 UTC) — same session, no re-probe.
- [x] **QA.6** M0.6 smoke: same topic probed **keyword vs `semantic=True`** → distinct cache keys (`/m/semantic/` present) and distinct pools; `recon_distill` shows a `topics` layer with anchors; zero `workspaces/` writes. ✅ **LIVE (engine-level, 2026-09-13, fresh cache root):** keyword pool `v1/…/q/a1fb97e3…` = 15 docs (openalex 5/5 with real topics); semantic pool `v1/…/m/semantic/q/a1fb97e3…` (same hash, distinct key) = 15 docs (openalex 5/5 with topics) — semantic hits visibly better-matched (grape/vine-specific); zero workspace writes. ⚠️ Live smoke **caught 2 real API constraints** fixed + hermetically pinned: cursor pagination rejected (→ page/per_page ≤ 50) and `filter` rejected (→ manual year filtering) for `search.semantic`. **MCP-level variant ✅ (2026-09-13, post-restart):** `recon_probe` topic "grape disease detection deep learning edge deployment" — keyword → `v1/…/q/a1fb97e3…` (5-seg, session `rec_f017f1…`); `semantic=True` → `v1/…/m/semantic/q/a1fb97e3…` (7-seg, session `rec_0d7c15…`); same query hash, distinct keys + pools (25 docs each), zero `workspaces/` writes. `recon_distill` on the semantic session returns a 6-topic anchored `topics` layer (top: "Smart Agriculture and AI" n=7 score=0.9359; thin frontiers UAV/drone n=1, multispectral n=1) + schools/metrics/datasets. Confirms the **CWD cache-root split live** (`tools\scholar-agent-kit\.cache\inception_recon\…`) → T7.7. Param passthrough, lineage (T5.5), isolation all verified at the MCP boundary.

---

## Release / PR (per pull-request-gate skill — only when user asks)

- [ ] **PR.0** Confirm gate: fork `nexus-scholar/nexus-scholar-harness`, target `nexus-scholar-org/nexus-scholar-harness`.
- [ ] **PR.1** Split commits logically (scaffold → M0.1 → M0.2 → M0.3 → M0.4 → M0.5 → docs).
- [ ] **PR.2** Update `docs/phase_0/README.md` + `specs/.../README.md` indexes if file names change.
- [ ] **PR.3** Open PR with the checklist above as the body; attach DoD evidence (test output).

---

*Completion rule: a milestone is "done" when its task boxes are checked AND its DoD block in `08_milestones.md` is satisfied.*