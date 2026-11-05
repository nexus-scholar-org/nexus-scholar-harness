# M5-slim Package (ship)
Branch: dev/m5/package · Lane: **RELEASE** (closure; plan §6) · Status: IN PROGRESS · Started: 2026-11-05

Plan: [`production-plan.md`](../production-plan.md) §6 (M5-slim row), §5.3 stage 1 (A0 + MCP), §8 (parked labels). The branch also carries the workspace screen spec (`00-workspaces.md`, FINAL) and the MCP-route prompt-gate tool (`prompt-gate export|import`), both written after M1b-2 and merged in at the start.

## Definition of done
- [x] **Workspaces API contract** `docs/architecture/workspaces-api.md` agreed before engine work (researcher, 2026-11-05): `GET /workspaces`, `POST /workspaces`, `POST /workspaces/open`; six `WORKSPACE_*` codes plus `RESTART_UNSUPPORTED`. Routes built: `src/scholar_harness/workspace/catalog.py`, `console/api/workspaces.py`; tests `tests/console/test_workspaces_api.py` (the restart itself is the launcher item below).
- [ ] **Static export served by FastAPI:** the UI is a static export served by the one FastAPI process, same origin, behind a per-launch token; the dev proxy and the `/` → `/en` redirect move into FastAPI; `next dev` stays for development only. Test: the exported app and `/api/v1` answer from one origin without the Next server.
- [ ] **`nexus-scholar ui [--workspace <path> | --root <folder>]`** starts the server and opens the browser; Open on the workspace screen restarts it on the chosen folder (spec 00). Test: launch, token required, restart on open, `WORKSPACE_BUSY`.
- [ ] **Minimal workspace screen** (spec `docs/ux/phase2-screening/final/00-workspaces.md`): list, open, create; its vitest and Playwright checks.
- [ ] **Decision export** (RIS/CSV) of the published screening; spec first (screen 09 or a new spec), FINAL before UI.
- [ ] **Methods paragraph** with PRISMA counts and the automation-use statement; spec first.
- [ ] **Data-flow statement**, one page: what leaves the machine, to which provider (API drivers, MCP route).
- [ ] **`.mcpb` Desktop Extension** for `scholar-agent`, and `nexus-scholar setup-mcp` writing no key to any file (CORE-17).
- [ ] **Honest "not production" labels** (§8): a shared `ParkedNotice` on parked routes/panels; parked kits marked in `docs/kits_surface_matrix.md` and the user guide; parked CLI `--help` notices; parked MCP tools return a typed refusal or warning.
- [ ] **Delete `scholar_bib`** and its consumers (`src/scholar_agent/server.py`, `tests/mcp/test_mcp_tools_graph.py`, `tests/kits/bib/`, the plugin manifest).
- [ ] **Wheel smoke with the UI:** the wheel carries the static UI; a fresh install answers `nexus-scholar ui` and serves the app.
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

## Deferred
