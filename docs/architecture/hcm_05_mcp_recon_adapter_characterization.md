# HCM-05 (unit 1) — MCP recon boundary characterization + harness adapter

**Status:** CHARACTERIZED -- HARNESS HALF IMPLEMENTED; KIT HALF BLOCKED.
**Lane:** STANDARD (structural transport-boundary work; owning full suite once).
**Owner:** harness (`nexus-scholar-org/nexus-scholar-harness`) for the adapter;
vendored `scholar-agent-kit` (canonical `nexus-scholar-org/scholar-agent-kit`)
read-only in this unit.
**Base:** `origin/main` `d07100f` (HCM-01..04 + TD-Option-B merged).
**Stop rule:** characterization + explicit adapter interface only. No MCP
server rewiring (it lives in `tools/`, forbidden), no behavior change.

## 1. Observed interface map (all confirmed by executed tests)

| # | Concern | Evidence | Test |
|---|---|---|---|
| B | Live tools + envelopes: `recon_probe(topic, session_id=None, start_year=2020, limit=10, semantic=False)` -> `{session_id, cache_key, status: probe_ok, n_docs, pool_path}` or `{status: error, message, cache_key: None}`; `recon_distill(session_id, lexicon_json=None)` -> terms/purity/qei reply or error; `recon_delta(session_id, followups=3)` -> merged lineage or error. All 3 registered on the MCP surface. | OBSERVED-KIT: drive all three with fakes | B01-B05 |
| B5 | `semantic=True` threads to `Query.semantic` and segments the cache key (`/m/semantic/`); keyword/semantic pools never collide. | OBSERVED-KIT | B05 |
| C | Dynamic discovery: `_harness_src()` (`NEXUS_HARNESS_SRC` -> `find_spec(scholar_harness.recon)` -> upward walk for `src/scholar_harness/recon/__init__.py` -> `""`) + gated `sys.path.insert`; never raises (lazy-guard contract). Installed layout returns `""`. | OBSERVED-KIT + SOURCE-TRACE | C01-C04 |
| D | Dead loader: `_ensure_harness_recon_loaded()` is NEVER called in any production path (`recon_probe`/`recon_distill`/`recon_delta`/`main`); `RECON_CACHE_ROOT=None` and all recon names are `None` until a caller runs it (only `tests/mcp/test_mcp_recon.py` does). Root snapshot happens only inside the loader. | SOURCE-TRACE | D01-D02 |
| E | Cache agreement: `NEXUS_RECON_ROOT` unifies the engine default and the MCP snapshot (both equal the override); without it both resolve repo-anchored CWD-independent `<root>/.cache/inception_recon`; `main() -w` pins `NEXUS_RECON_ROOT=<ws>/.cache/inception_recon`. | OBSERVED | E01-E03 |
| F | `RECON_SEARCH_FN=None` is a test-only seam: the only shipped write is the `None` default; production only *reads* it (`search_fn=RECON_SEARCH_FN`, probe + delta); injected fn => hermetic (`corpus_count` degrades to -1, no network). | SOURCE-TRACE + OBSERVED | F01-F02 |
| G | Inception parity: CLI wizard (`grounded.py`: `ReconEngine` + `distill_pool`), skill helper (`grounded_directions.py`: imports `scholar_harness.inception` directly, zero discovery), and MCP tools drive the same engine functions and share cache addresses (same query + explicit window => identical `cache_key`). OBSERVED default divergence: engine `year_min=2000` vs MCP `start_year=2020` -- parity requires an explicit shared window. | SOURCE-TRACE + OBSERVED | G01-G05 |
| H01/H02 | Missing harness interface (`ReconEngine=None` / `distill_pool=None`) raises **uncaught `TypeError` OUTSIDE** the documented `(RuntimeError, ValueError, OSError)` error envelope. | OBSERVED-KIT | H01-H02 |
| H03 | `RECON_CACHE_ROOT=None` does NOT fall back: `_session_root` divides the snapshot (`None / "sessions"`) => uncaught `TypeError` before the engine (which would fall back) is constructed. Only the engine half degrades; the session half does not. | OBSERVED-KIT (hypothesis corrected by execution) | H03 |
| H04 | `workspaces/`-anchored roots refuse *inside* the envelope with no writes. | OBSERVED-KIT | H04 |
| H05/H06 | `RuntimeError` from search maps into the envelope; `TypeError` from search escapes it (third escape path). | OBSERVED-KIT | H05-H06 |
| H07 | Malformed session/lexicon/followups/unknown-session stay inside the envelope. | OBSERVED-KIT | H07 |
| A | Adapter (`scholar_harness.recon.adapter`, `ADAPTER_VERSION="1.0"`) resolves the canonical root identically (env + no-env), raises typed `ReconAdapterInputError`/`ReconAdapterDependencyError` (both `RuntimeError`-compatible, input also `ValueError`) for bad inputs/missing symbols, preserves cache identity + idempotency (one search call for two identical probes), and delegates byte-identically (probe/distill/plan/merge/gates/followups). Adapter source has no kit/MCP/`sys.path`/digest/regex logic. | OBSERVED-ADAPTER (kit-free) | A01-A13 |

## 2. Adapter surface (harness-owned, versioned, delegation-only)

`src/scholar_harness/recon/adapter.py` (`ADAPTER_VERSION = "1.0"`):
`adapter_version`, `describe_interface`, `resolve_cache_root`,
`make_engine`, `build_cache_key`, `parse_key`, `normalize_text`,
`default_providers`, `default_lexicon`, `merge_lexicon`, `distill_terms`,
`plan_candidates`, `merge_pool_list`, `pool_gate`, `topic_gate`,
`saturation_for`, `probe_topic` (async), `run_followups` (async).
Errors: `ReconAdapterError(RuntimeError)` ->
`ReconAdapterDependencyError` (missing symbol / non-callable `search_fn`) and
`ReconAdapterInputError(RuntimeError, ValueError)` (malformed inputs,
`workspaces/` anchor). Both fit the kit's existing catch clause, so a future
adapter-backed tool maps into `{status: error}` instead of escaping as
`TypeError`. Imports cleanly standalone; no `sys.path`, no fallback roots,
no MCP imports, no algorithm duplication.

## 3. Kit-half verdict: BLOCKED_CANONICAL_REPO

The harness half is complete, but `tools/scholar-agent-kit/src/scholar_agent/
server.py` still uses the dynamic seam (`_harness_src` + `sys.path` insert +
`None`-until-loader globals + `RECON_SEARCH_FN`/`RECON_CACHE_ROOT` snapshot
globals). Consuming the adapter requires editing that file (e.g. replacing
the seam with `from scholar_harness.recon.adapter import ...` plus a declared
harness dependency for the wheel layout), which per the toolkit-sync rule
belongs to canonical `nexus-scholar-org/scholar-agent-kit` (vendored pin
`default_rev 79ffe42...`), NOT to a harness PR. Evidence: H01-H03 prove the
current seam's uncaught-`TypeError` class; D01 proves the loader is dead in
prod paths; C03 proves the `sys.path` insert is still the only import bridge.

**Ready bounded canonical-kit packet sketch (not executed here):**
goal -- server consumes `scholar_harness.recon.adapter v1.0` with no
`_harness_src`/`sys.path`/`_ensure_harness_recon_loaded`/`RECON_SEARCH_FN`
snapshot semantics change beyond typed errors; paths -- only
`src/scholar_agent/server.py` (+ kit tests); behavior -- identical envelopes
for B03-B05/H04/H05/H07, typed `{status: error}` (no `TypeError` escape) for
H01-H03/H06; tests -- re-run `tests/mcp/test_mcp_recon.py` (23) plus a
kit-side port of H01-H03 asserting envelopes; sync -- canonical-kit PR merge,
`plugins.json` `default_rev` bump to the resulting full SHA, vendored sync,
`nexus_scholar_pins.json` regen. Until that PR merges, the adapter is
*available but unwired*.

## 4. Validation evidence

- New: `tests/unit/test_recon_adapter_characterization.py` -- 41 passed.
- Neighbors: `tests/mcp/test_mcp_recon.py` (23) + `tests/recon/` + `tests/inception/` -- all passed (179 total in one run).
- Selectors: `select_test_gate.py --task HCM-05` unknown-task (no HCM-05 mapping) -- documented fallback to owning suites used.
- Generators `--check` (baseline/schemas/fixture/pins) + `ruff check scripts/` + `git diff --check`: all green (see return report for SHAs).
- Owning full suite (STANDARD lane): once on final candidate --
  `uv run pytest -q -p no:cacheprovider`: exit 0, 1162 collected,
  1156 passed + 6 skipped (pre-existing platform skips), 0 failed.

## 5. Debt / limits / next step

- H01-H03/H06 uncaught-`TypeError` paths remain live until the kit-half PR.
- Engine-vs-MCP year defaults diverge (2000 vs 2020); adapter keeps the engine default -- kit consumer must pass windows explicitly.
- No crash/concurrency claims for session writes; content-addressed artifacts only prove same-payload stability.
- **Next:** open the canonical-kit PR per the sketch above (HCM-05 unit 2); then delete the dead loader + discovery seam.
