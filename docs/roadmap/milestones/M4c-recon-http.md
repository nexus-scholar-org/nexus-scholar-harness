# M4c Recon over HTTP
Branch: `dev/m4c/recon-http` · Lane: **RELEASE**. The milestone changes public HTTP and MCP semantics: new `/api/v1/inception/drafts/{id}/recon/...` routes, new fields and a `refresh` parameter on the `recon_*` tools, and recon adapter 1.1. It also changes artifact persistence: what the recon cache keeps and what a draft record holds. `test_gate_policy.md` §lanes therefore puts it in RELEASE. · Status: IN PROGRESS · Started: 2026-11-09

Why: plan §6 row "M4 Inception web" lists "recon over HTTP" and INC-09/21. M4a (PR #206) held them until M3a (PR #204) rewrote the `scholar_search` providers. M4b (PR #209) left Explore and Direction as placeholders "coming with recon".

## Definition of done
- [x] **One recon engine on the M3a providers.**
  - `ReconEngine` runs `SearchEngine.run` and keeps one leg per provider in the pool.
  - `MAILTO_NOT_SET` refuses before any request: a refusal in the MCP tools and the CLI wizard, not a traceback.
  - The recon session store moves from `scholar_agent/server.py` to `scholar_harness/recon/session.py`. The MCP tools (through the adapter's `make_sessions`, adapter 1.1), the CLI wizard and the console call it.
  - Tests: `tests/recon/test_session.py` (both front doors), `tests/mcp/test_mcp_recon.py`, `tests/kits/agent/test_mcp_recon_adapter.py`, `tests/unit/test_recon_adapter_characterization.py`, `tests/inception/test_inception_grounded.py`.
- [x] **INC-09 and INC-21**, each with a failing-then-passing test (table below).
- [x] **Grounded evidence in the draft.**
  - `bind` writes `grounding` beside the draft: the pool fingerprint and `created_at`, the direction, the anchors, the anchored terms and the evidence.
  - Preview with `session_id` shows per-RQ and per-concept evidence. Genesis writes `audit/recon_context.json`.
  - Preview and genesis refuse `STALE_BINDING` when the session searched again.
  - A draft with no recon is unchanged.
  - Tests: `tests/console/test_recon_api.py`. M4b's `tests/console/test_inception_api.py` and `test_browser_access.py` pass unchanged.
- [x] **HTTP surface** `/api/v1/inception/drafts/{id}/recon/...`.
  - Probe and delta run as jobs with an SSE stream. Distill, directions and bind answer directly.
  - Refusals are codes with sentences, in `console/refusals.py` and contract §7.
  - Both proxy allowlists carry the four POST routes.
  - Tests: `tests/console/test_recon_api.py`, `tests/console/test_browser_access.py::test_recon_reaches_the_engine_from_the_browser`, `apps/research-ui/tests/console-proxy.test.ts`.
- [ ] **Offline tests.**
  - [x] Unit tests for the gates and the store.
  - [x] Route tests through the search seam.
  - [x] An offline guard in `tests/conftest.py`: a non-loopback connect fails the test (`tests/unit/test_offline_guard.py`).
  - [ ] The golden probe replayed from a VCR cassette (`tests/pipeline/test_golden_recon_cassette.py`). The test is written, but the cassette needs one live recording, approved by the researcher.
- [ ] **Specs.** `docs/ux/phase0-inception/final/02-explore.md` and `03-direction.md`, written from the canvases by `ux-spec-writer` and mapped to the new routes.
- [ ] **Gate.**
  - [x] `/gate inner` after edits.
  - [ ] `/gate pr` once on the final commit.
  - [x] Contract check.
  - [ ] `milestone-reviewer`.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| INC-09 | `tests/recon/test_recon_findings.py::test_inc09_an_empty_probe_is_not_cached` | yes (`b561b8e`): `(0, 0) != (0, 15)`, the empty pool was served from the cache | yes (`717bbfc`) |
| INC-09 | `::test_inc09_a_failed_leg_is_recorded_and_the_pool_is_not_cached` | yes: `TypeError: 'SearchRun' object is not iterable`, the legs were dropped | yes |
| INC-09 | `::test_inc09_refresh_probes_again` | yes: no `refresh` | yes |
| INC-09 | `::test_inc09_grounded_context_carries_each_pool_created_at` | yes: `KeyError: 'pool_created_at'` | yes |
| INC-21 | `::test_inc21_a_concept_is_not_anchored_on_a_record_that_does_not_contain_it` | yes: a bird-migration paper anchored "quantum error correction" (`DID NOT RAISE Exit`) | yes |
| INC-21 | `::test_inc21_a_synonym_with_hits_but_no_occurrence_is_dropped_and_hits_are_kept_apart` | yes: `['surface codes'] != []` | yes |
| INC-21 | `::test_inc21_the_topic_is_anchored_only_where_it_occurs` | yes: `KeyError: 'term_evidence'` | yes |
| INC-21 | `::test_inc21_apr_measures_occurrence_not_hits` | yes: no occurrence APR | yes |
| audit (phase-auditor) | `tests/recon/test_session.py::test_the_mcp_tool_answers_mailto_not_set_in_its_envelope`, `::test_the_cli_wizard_exits_with_mailto_not_set` | `MailtoNotSet` escaped the MCP envelope and the wizard (read in the audit) | yes |

## Decisions
- [2026-11-09, Recon over HTTP: one session store, pools that say what failed, anchors by occurrence](../../decisions.md) (proposed; the researcher decides at the PR).

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| start | `68a9c13` | branch from `origin/main` | clean | |
| audit | `68a9c13` | phase-auditor on INC-09, INC-21 | both reproduce. Also found: `MailtoNotSet` escapes the MCP envelope and the wizard | |
| red | `b561b8e` | `pytest tests/recon/test_recon_findings.py` | 8 failed, each for its finding | |
| inner | `717bbfc` | `pytest tests/recon tests/mcp tests/unit/test_recon_adapter_characterization.py tests/inception tests/cli -n auto` | all pass | |
| inner | working tree after `80ba36b` | `pytest tests/console tests/inception tests/recon tests/kits/agent tests/mcp tests/unit/test_recon_adapter_characterization.py tests/cli -m "not slow" -n auto` | **975 passed, 1 skipped** | 1 m 53 s |
| inner | `80ba36b` | `npm run typecheck`; `vitest run tests/console-proxy.test.ts` | clean; 56 passed | |
| check | working tree | `generate_contract_baseline.py --check`; `ruff check scripts/`; real-bug `ruff check src/` | current; clean; clean | |

## Deferred
- **A custom lexicon over HTTP.** The MCP `recon_distill` takes `lexicon_json`; there is no HTTP route.
- **An in-app contact email setting.** The console uses its process's `SCHOLAR_MAILTO`.
- **The CLI wizard's thin-pool gate** (INC-28) stays a printed note. The HTTP bind refuses `POOL_TOO_SMALL`.
- **Recon findings outside this milestone:**
  - INC-10: the pool is chosen by arrival order.
  - INC-24: directions are ranked by n-gram length.
  - Prior 7: the cache key omits the sample size.
  - Prior 8: the venue-token substring filter.
- **Release notes** (b5) for recon over HTTP and adapter 1.1.
