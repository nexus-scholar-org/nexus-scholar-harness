# HCM-05 — MCP recon boundary characterization + harness adapter adoption

**Status:** ADOPTED -- HARNESS HALF IMPLEMENTED AND KIT HALF MERGED + VENDORED.
**Lane:** RELEASE (cross-repo vendored-kit pin + MCP boundary; full harness
suite once + wheel build + minimal-env `--help` proofs).
**Owner:** harness (`nexus-scholar-org/nexus-scholar-harness`) for the adapter;
canonical kit `nexus-scholar-org/scholar-agent-kit` for the server rewiring
(merged as kit PR #5, commit `50c0b3fbf52fc1a9768b219bc2e894d713eb38af`).
**Base:** `origin/main` `86a9478` (PR #104+105 merged).
**Adoption pin:** `plugins.json` `scholar-agent-kit.default_rev` =
`50c0b3fbf52fc1a9768b219bc2e894d713eb38af` (40-char full SHA == canonical
`main` HEAD, verified via `git ls-remote` + temp-clone `git rev-parse HEAD`).
**Vendored tree proof:** `tools/scholar-agent-kit` staged blob SHAs equal the
canonical-commit blob SHAs for all 15 synced paths (21 canonical tracked files
minus 6 generated `src/scholar_agent_kit.egg-info/*`, an exclusion predating
this sync: old pin `79ffe42` tracked 20 files, vendored 14, same rule).
Staged delta vs base is exactly the merge diff: `pyproject.toml`,
`src/scholar_agent/server.py`, `tests/test_standalone_packaging.py` modified +
`tests/test_mcp_recon_adapter.py` added. `nexus_scholar_pins.json` regenerated
via `scripts/generate_nexus_scholar_pins.py` (`--check` green).
**Stop rule:** adoption only. No canonical kit re-edit, no adapter change
(`src/scholar_harness/recon/adapter.py` immutable), no behavior change beyond
the merged kit rewiring.

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

## 3. Kit-half verdict: ADOPTED (canonical PR #5 merged, vendored + pinned)

The former `BLOCKED_CANONICAL_REPO` is resolved. Canonical
`nexus-scholar-org/scholar-agent-kit` merged PR #5
(`50c0b3fbf52fc1a9768b219bc2e894d713eb38af`, parent `79ffe42`): the server now
consumes `scholar_harness.recon.adapter v1.0` with no `_harness_src`/`sys.path`/
`NEXUS_HARNESS_SRC` discovery. Harness adoption in this unit: `plugins.json`
pin bump, byte-identical vendored sync (15/15 blob-SHA equality, negative
controls: truncated-SHA pin fails `test_manifest_default_revs_are_pinned_commits`
+ 4 pins tests; one mutated blob fails the blob proof; both restored and green),
`nexus_scholar_pins.json` regen.

**Absent mechanisms (proven, not claimed):** no `_harness_src`/`_HARNESS_SRC`
attribute or reference, no `NEXUS_HARNESS_SRC` read, no `sys.path` mutation, no
`find_spec`/`importlib.util`/`import sys`, no per-symbol recon globals
(`ReconEngine`, `canonical_recon_root`, `distill_pool`, `execute_followups`
absent as module names AND as call sites in the recon tools). The loader binds
exactly `_recon_adapter` + `DomainLexicon` via a plain guarded import and
resolves `RECON_CACHE_ROOT` through `_recon_adapter.resolve_cache_root()`.

**Real-path evidence (live, hermetic, tmp roots + fake search_fn):**
`tests/mcp/test_mcp_recon.py` (27: 23 unchanged envelopes + U1-U4 adoption
proofs) and `tests/unit/test_recon_adapter_characterization.py` (41: Parts A/B
unchanged, C/D/F01/G03/H01-H02 rewritten to the adopted seam). Proven live:
all 3 tools registered with identical envelopes (B01-B05); bound adapter IS
`scholar_harness.recon.adapter` (U1/D01); loader called atop every tool
(D01); cache-identity reuse with a single fake call (existing reuse test);
same cache key engine-vs-MCP only with an explicit shared window (G04 + U4);
adapter-unavailable and malformed inputs map into `{status: error,
cache_key: None}` with no `TypeError` (H01/H02/U3/H07); `RECON_SEARCH_FN` stays
a read-only test seam (3 read sites, 1 write; F01); no `workspaces/` writes
(H04 + existing refusal tests).

**Year limitation (honest):** MCP `recon_probe` defaults `start_year=2020`
while `ReconEngine.probe`/adapter default `year_min=2000`; defaults
observably diverge (U4 asserts `default_key != explicit_key`). Parity requires
passing an explicit shared window -- never claimed otherwise.

**No over-claim:** H03 (test-only `RECON_CACHE_ROOT=None` post-load mutation
still raises `TypeError` outside the envelope) and H06 (`TypeError` raised *by*
an injected search_fn still escapes the documented
`(RuntimeError, ValueError, OSError)` catch) are unchanged by adoption and stay
characterized as designed-in escape paths, not regressions. No
crash/concurrency claims for session writes; content-addressed artifacts only
prove same-payload stability.

**Remaining follow-up:** none for HCM-05. The adapter is *wired*; H03/H06
escape paths are envelope-scope decisions for a future unit, not defects.
Next task: HCM-06 gating (per mission).

## 4. Validation evidence

- Adopted: `tests/unit/test_recon_adapter_characterization.py` -- 41 passed
  (Parts A/B/E/G04/G05/H03-H07 unchanged; C/D/F01/G03/H01-H02 rewritten to the
  adopted seam; 10 previously-seam-asserting tests failed pre-rewrite).
- Adopted: `tests/mcp/test_mcp_recon.py` -- 27 passed (23 pre-existing envelopes
  green unchanged on the new server + U1-U4 adoption proofs).
- Selectors: `select_test_gate.py --task HCM-05` unknown-task (no HCM-05 mapping)
  -- documented fallback to owning suites used (same as unit 1).
- Generators `--check` (baseline/schemas/fixture/pins) + `ruff check scripts/`
  + `git diff --check`: all green (see return report for SHAs).
- Owning full suite (RELEASE lane): once on final candidate --
  `uv run pytest -q -p no:cacheprovider` (see return report for counts).

## 5. Debt / limits / next step

- H01/H02 adapter-unavailable paths now map into the typed envelope (fixed by
  adoption). H03/H06 uncaught-`TypeError` paths remain BY DESIGN (test-only
  global mutation / foreign `TypeError` from an injected double) -- see §3.
- Engine-vs-MCP year defaults diverge (2000 vs 2020); adapter keeps the engine
  default -- callers must pass windows explicitly (U4 locks this in).
- No crash/concurrency claims for session writes; content-addressed artifacts
  only prove same-payload stability.
- **Next:** HCM-06 gating. No HCM-05 follow-up remains.
