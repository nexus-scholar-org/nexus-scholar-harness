# M5-slim Package (ship)
Branch: dev/m5/package · Lane: **RELEASE** (closure; plan §6) · Status: IN PROGRESS · Started: 2026-11-05

Plan: [`production-plan.md`](../production-plan.md) §6 (M5-slim row), §5.3 stage 1 (A0 + MCP), §8 (parked labels). The branch also carries the workspace screen spec (`00-workspaces.md`, FINAL) and the MCP-route prompt-gate tool (`prompt-gate export|import`), both written after M1b-2 and merged in at the start.

## Definition of done
- [x] **Workspaces API contract** `docs/architecture/workspaces-api.md` agreed before engine work (researcher, 2026-11-05): `GET /workspaces`, `POST /workspaces`, `POST /workspaces/open`; six `WORKSPACE_*` codes plus `RESTART_UNSUPPORTED`. Routes built: `src/scholar_harness/workspace/catalog.py`, `console/api/workspaces.py`; tests `tests/console/test_workspaces_api.py` (the restart itself is the launcher item below).
- [x] **Static export served by FastAPI:** the UI is a static export served by the one FastAPI process, same origin, behind a per-launch token; the dev proxy and the `/` → `/en` redirect move into FastAPI; `next dev` stays for development only. Test: the exported app and `/api/v1` answer from one origin without the Next server. Done: `npm run build:static` (`NEXT_STATIC_EXPORT=1`, `.next-static/`); the console serves it and its browser surface (`console/browser.py`: launch cookie, the proxy's allowlist kept equal to `route.ts`); `tests/console/test_browser_access.py`; decision 2026-11-05 "launch cookie and the proxy's allowlist".
- [x] **`nexus-scholar ui [--workspace <path> | --root <folder>]`** starts the server and opens the browser; Open on the workspace screen restarts it on the chosen folder (spec 00). Test: launch, token required, restart on open, `WORKSPACE_BUSY`. Done: `console/launcher.py`, `tests/test_ui_launcher.py` (a real server restarts and the session survives); no workspace open → only the workspaces routes answer. The UI's "Opening {title}" handling is part of the screen item.
- [ ] **Minimal workspace screen** (spec `docs/ux/phase2-screening/final/00-workspaces.md`): list, open, create; its vitest and Playwright checks.
- [ ] **Decision export** (RIS/CSV) of the published screening; spec first (screen 09 or a new spec), FINAL before UI.
- [ ] **Methods paragraph** with PRISMA counts and the automation-use statement; spec first.
- [ ] **Data-flow statement**, one page: what leaves the machine, to which provider (API drivers, MCP route).
- [ ] **`.mcpb` Desktop Extension** for `scholar-agent`, and `nexus-scholar setup-mcp` writing no key to any file (CORE-17).
- [ ] **Honest "not production" labels** (§8): a shared `ParkedNotice` on parked routes/panels; parked kits marked in `docs/kits_surface_matrix.md` and the user guide; parked CLI `--help` notices; parked MCP tools return a typed refusal or warning.
- [ ] **Delete `scholar_bib`** and its consumers (`src/scholar_agent/server.py`, `tests/mcp/test_mcp_tools_graph.py`, `tests/kits/bib/`, the plugin manifest).
- [x] **Wheel smoke with the UI:** the wheel carries the static UI; a fresh install answers `nexus-scholar ui` and serves the app. Done: `hatch_build.py` bundles `.next-static/` as `scholar_harness_data/ui` (`NEXUS_WHEEL_REQUIRE_UI=1` in CI, release and publish); CI `wheel-e2e` starts `nexus-scholar ui` from the wheel and checks the launch, a page and the API; run locally from a clean venv (below). Release and publish now build the root package (they built the removed `packaging/nexus-scholar`).
- [ ] **The gate, part 1:** a fresh install from the wheel; accept-corpus → screening → publish on the golden UAV workspace **by the researcher**, audit trail intact.
- [ ] **The gate, part 2:** CI matrix green (ubuntu/windows/macos × 3.11/3.12).
- [ ] **The gate, part 3:** the prompt gate passes on the default model (MCP route allowed, decision 2026-11-05), its report and the route recorded here. Needs the researcher's go-ahead for the full 1,644-record run (subscription usage).

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |

## Decisions
- [2026-11-05 — The minimal workspace screen: root, open, create](../../decisions.md)
- [2026-11-05 — The prompt gate may be met on the MCP route](../../decisions.md)
- [2026-11-05 — M1b-2 merges before its live prompt gate; the gate blocks M5-slim](../../decisions.md)

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner + local wheel smoke | working tree on `13c3146` | console, inception, cli, launcher, agent tests (`-m 'not slow'`, `-n auto`) plus the slow launcher test; `tsc`; `console-proxy.test.ts`; `ruff check scripts/`; wheel with `NEXUS_WHEEL_REQUIRE_UI=1` installed in a clean venv: `nexus-scholar ui` → launch 303, create 201, page 200, open 202, restart onto the new workspace with the session kept | 619 passed, 1 skipped; 5 passed; clean; 35 passed; clean; all as expected | about 4 min |

## Deferred
- **Windows path length:** creating a workspace under a very deep root can pass the 260-character limit while the skills are copied (seen from a long temp folder). It is refused `WORKSPACE_ROOT_UNAVAILABLE` with the reason and nothing is left; the default root is short. `nexus-scholar init` has the same limit. A long-path-aware copy is not in M5-slim.
