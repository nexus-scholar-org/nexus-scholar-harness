# M4c Recon over HTTP
Branch: `dev/m4c/recon-http` · Lane: **RELEASE**. The milestone changes public HTTP and MCP semantics (new `/api/v1/inception/drafts/{id}/recon/...` routes, new fields in the `recon_*` tool answers) and artifact persistence (what the recon cache keeps, what a draft record holds), so `test_gate_policy.md` §lanes puts it in RELEASE. · Status: IN PROGRESS · Started: 2026-11-09

Why: plan §6 row "M4 Inception web" lists "recon over HTTP" and INC-09/21. M4a (PR #206) held them until M3a (PR #204) rewrote the `scholar_search` providers; M4b (PR #209) left Explore and Direction as placeholders "coming with recon".

## Definition of done
- [ ] **One recon engine on the M3a providers.** `ReconEngine` runs `SearchEngine.run` and keeps one leg per provider in the pool; `MAILTO_NOT_SET` refuses before any request. The recon session store moves from `scholar_agent/server.py` into `scholar_harness/recon/session.py`, and the MCP tools, the CLI wizard and the console call it. Tests: `tests/recon/test_session.py`, `tests/mcp/test_mcp_recon.py`, `tests/inception/test_inception_grounded.py`.
- [ ] **INC-09 and INC-21**, each with a failing-then-passing test (table below).
- [ ] **Grounded evidence in the draft.** A bound draft holds the pool fingerprint and `created_at`, the anchors, the chosen direction and per-RQ evidence; `STALE_BINDING` when the session's pool no longer matches. A draft with no recon is unchanged. Tests: `tests/inception/test_grounding.py`, M4b's `tests/console/test_inception_api.py` unchanged and passing.
- [ ] **HTTP surface** `/api/v1/inception/drafts/{id}/recon/...`: probe and delta as jobs with an SSE stream, distill, directions, bind; refusals as codes with sentences. Both proxy allowlists carry the routes. Tests: `tests/console/test_recon_api.py`, `tests/console/test_browser_access.py`, `apps/research-ui/tests/console-proxy.test.ts`.
- [ ] **Offline tests.** A golden probe replayed from a VCR cassette; unit tests for the gates; route tests on the cassette. The full suite makes no network call.
- [ ] **Specs.** `docs/ux/phase0-inception/final/02-explore.md` and `03-direction.md` written from the canvases by `ux-spec-writer`, mapped to the new routes.
- [ ] **Gate.** `/gate inner` after edits, `/gate pr` once on the final commit, contract check, `milestone-reviewer`.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |

## Decisions

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| start | `68a9c13` | branch from `origin/main` | clean | |

## Deferred
