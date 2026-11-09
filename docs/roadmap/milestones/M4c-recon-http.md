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
- [x] **Offline tests.**
  - [x] Unit tests for the gates and the store.
  - [x] Route tests through the search seam.
  - [x] An offline guard in `tests/conftest.py`: a non-loopback connect fails the test (`tests/unit/test_offline_guard.py`).
  - [x] The golden probe replayed from a VCR cassette.
    - The cassette `tests/fixtures/cassettes/golden_recon_probe.yaml` comes from one live run, approved by the researcher on 2026-11-09. Semantic Scholar answered 429, so the pool is partial.
    - `tests/pipeline/test_golden_recon_cassette.py` runs the engine and the HTTP flow.
    - The address is absent from the file, and no request carries a contact or key parameter.
  - [x] The guard found three RAG tests that called the Hugging Face Hub. They now load the cached model offline, and CI fetches the model before pytest.
- [x] **Specs (DRAFT).**
  - `docs/ux/phase0-inception/final/02-explore.md` and `03-direction.md` were written from the canvases by `ux-spec-writer` and map to the new routes.
  - Each lists the canvas features the engine does not serve, carries build notes (among them the M4b hydration fix), and ends with open questions for the researcher: 02 Q1–Q3, 03 Q1–Q4.
  - Two engine gaps the spec writer found are fixed here:
    - the recon events stream is in the proxy's `STREAM_PATHS`;
    - the fallback direction is no longer offered (03 Q5).
  - FINAL waits for the researcher's answers.
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
| prior 9 over HTTP (spec 03 Q5) | `tests/recon/test_session.py::test_a_direction_is_offered_only_when_its_term_occurs_in_two_records` | yes: the joined "pool vocabulary" direction was offered | yes |
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
| checkpoint | `8e44451` | `pytest -n auto` (whole suite, with the offline guard) | 3 failed: RAG tests reaching the Hugging Face Hub (`test_cli_matrix_command`, `test_nexus_rag_and_matrix_tools`, `test_cli_index_and_query_flow`). Fixed with `HF_HUB_OFFLINE` and a CI pre-fetch; the three then pass | |
| record | working tree | `NEXUS_RECORD_CASSETTES=1 SCHOLAR_MAILTO=<researcher> pytest tests/pipeline/test_golden_recon_cassette.py` (one live run, approved) | cassette written: OpenAlex, Crossref and arXiv 200; Semantic Scholar 429 | |
| inner | working tree | `pytest tests/recon tests/console/test_recon_api.py tests/pipeline/test_golden_recon_cassette.py tests/console/test_browser_access.py -n auto`; `vitest run tests/console-proxy.test.ts`; `tsc --noEmit` | 150 passed (replay, offline); 57 passed; clean | 1 m 17 s |

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
- **Engine gaps the specs work around.** Each is listed in the spec's "Changed from the canvas":
  - no cancel route for a recon job;
  - no read-only check of your own direction;
  - the gap check merges into the pool, so it can make a binding stale (03 Q2);
  - no `scope_changed` field (02 Q3);
  - the probe ignores `languages`.

## M4b follow-ups (for the next inception UI milestone; not fixed in M4c)
From a live review of the merged M4b screens (PR #209) on 2026-11-09, sent by the coordinating session. M4c stays backend plus specs.
1. **P2, every inception screen: React hydration mismatch.** `inceptionHref` in `apps/research-ui/components/inception-frame.tsx` builds the step-bar links from `window.location.search` (`?draft=`, `?console=`). The server renders them without the query and the client with it, so the console shows "Hydration failed" on each load and the tree is regenerated. Fix: take the draft id from `useSearchParams()` (or route params), or render the links after mount. The Explore and Direction specs carry this as a build note.
2. **P2, Shape: "Use this draft as RQn" can insert a stale sentence.** With unit and proof typed quickly and the button pressed before the step recomputed, RQ1 became "Can a novel … artifact achieve  for , compared to a defined baseline?", and that text compiled into the protocol. Disable the button while the step is in flight, or recompute on click.
3. **P3, Criteria: "Continue to review" is allowed with zero concepts.** Review then refuses with `DRAFT_INCOMPLETE` → Concepts. State the requirement on Criteria.
4. **P3, Review: a refusal card on first load.** Before the title is typed, "A few answers are still missing" (`DRAFT_INCOMPLETE`) shows for a form the researcher has not filled. Prefer a neutral "fill title and lead, then check" state until the first check.
5. **P3, Workspaces: two creation buttons.** "New workspace" (brand) and "New review" (quiet). Decide which is primary; the wizard is the product path.

The rest of that walk passed: the full create flow, `WORKSPACE_EXISTS` → replace with backup, `SCREENING_BOUND` with the typed slug and a sentence on a wrong name, the dark theme, and 375 px with no sideways scroll.
