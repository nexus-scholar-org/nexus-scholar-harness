# Workspaces API (M5-slim)

Status: **AGREED** (researcher, 2026-11-05), before any engine work (decision 2026-11-05, "The minimal workspace screen: root, open, create"). Screen: [`docs/ux/phase2-screening/final/00-workspaces.md`](../ux/phase2-screening/final/00-workspaces.md) (FINAL). Same conventions as [`screening-api-contract.md`](screening-api-contract.md): JSON over the console's `/api/v1`, refusals as `{"detail": {"code", "message"}}`, desktop-only unless a route is listed in `_PHONE_ROUTES` (`src/scholar_harness/console/serve.py`).

## 1. What it is for

The packaged app (`nexus-scholar ui`) serves **one workspace at a time**, as the console always has (`create_app(workspace)`). These three routes let the researcher see the workspaces under a root, create one, and switch to another. Switching **restarts** the server on the other folder: no state crosses workspaces. The multi-workspace server stays in M4.

## 2. The root

The launcher resolves the workspaces root once, in this order, and passes it to `create_app(..., workspaces_root=...)`:

1. `nexus-scholar ui --root <folder>`;
2. the `NEXUS_WORKSPACES_ROOT` environment variable;
3. `~/Documents/Nexus Scholar/workspaces` (created on first use).

`nexus-scholar ui --workspace <path>` opens that folder directly and skips the screen. The root is still resolved, so the screen works from the app bar; the open workspace may sit outside the root, and is then shown as the current row with its own path. No config file and no settings route.

**No workspace open.** Started without `--workspace`, the launcher binds the server to the most recently active workspace under the root (by its last journal row) and opens the workspaces screen. When the root holds none, the server runs with no workspace: only the three workspaces routes, the static UI and `/healthz` answer, and every other API route is refused `409 WORKSPACE_NOT_VALID` ("no workspace is open"). `GET /workspaces` then returns `current: null`. (Added during M5-slim; the screen's empty state covers it.)

A folder under the root **is a workspace** when it contains `protocol.json`, `project.json` and `audit/journal.jsonl`. `.mcp.json`, skills and `.env.example` are not required. Only direct children of the root are listed; the scan does not recurse and follows no symlink out of the root.

## 3. Routes

| Route | Purpose | Request → response | Scope |
| :-- | :-- | :-- | :-- |
| `GET /api/v1/workspaces?include_invalid=` | list the root | → `{root, root_source: "flag"\|"environment"\|"default", writable, current: {slug?, path}, busy: {run_active, pairing_open}, skipped_count, items: [{slug, title, path, valid, invalid_reason?, has_corpus, screening_started, status, last_event: {at, action}?, is_current}]}`. `items` holds valid workspaces; invalid folders are returned only with `include_invalid=true`, each with `valid: false` and `invalid_reason` (which marker is missing, or "unreadable"). `path` is absolute. `title` comes from `project.json`; `has_corpus` from the accepted corpus snapshot; `screening_started` from any decision event; `status` (M6-beta) is where the screening stands, most advanced first: `PUBLISHED` (published and current), `PUBLISHED_CHANGED` (published, a decision since), `SCREENING` (batches prepared), `CORPUS_ACCEPTED`, `NEW`; `last_event` from the last line of `audit/journal.jsonl` | desktop |
| `POST /api/v1/workspaces` | create | `{title}` → `201 {slug, path, protocol_fingerprint}`. The slug is derived as `init_command` derives it; the folder is `{root}/{slug}`. The server runs the same steps as `nexus-scholar init --scaffold-only`, then `install_workspace_support_files`. The journal gets the same `PROJECT_INITIALIZED` (agent `workspace-manager`) and `GENESIS` (agent `nexus-scholar/ui`) rows as the CLI writes. A failure part-way removes the folder the request created and journals nothing | desktop, loopback origin |
| `POST /api/v1/workspaces/open` | switch workspace | `{slug}` → `202 {slug, path, restarting: true}`; then the server restarts on that folder (§4). Writes nothing and journals nothing | desktop, loopback origin |

The `POST` routes check the loopback `Origin` like the screening actions (`ACTION_ORIGIN_REFUSED`). No delete, rename, move or import route.

## 4. Open: the restart

`create_app` takes an optional `on_open: Callable[[Path], None]`, which the launcher supplies; without one (tests, `scholar-harness serve`), `POST /workspaces/open` answers `501 RESTART_UNSUPPORTED`. When `POST /workspaces/open` is accepted:

1. the server answers `202` first, then calls `on_open(path)` from a background task;
2. the launcher stops the current server and starts a new one, on **the same host, port and per-launch token**, bound to `path`. Same origin and token mean the open browser tab keeps working;
3. nothing is carried over: job runner, agent-run registry, pairing state and phone tokens belong to the old app instance and end with it;
4. the UI shows "Opening {title}", polls `GET /api/v1/workspace/meta` until it names the new path, then loads `/screening`.

**Busy:** before accepting, the server refuses `409 WORKSPACE_BUSY` when an agent run is active (`agent_runs.active_run(ws)` names a run live in this engine) or an approval pairing is open (`GET /screening/actions/pairing/status` state `STAGED`). `details` names which: `{run_active: bool, pairing_open: bool}`. The restart would end either.

Opening the workspace that is already current answers `200 {slug, path, restarting: false}` and restarts nothing.

## 5. Refusal codes

New console codes (not Contract v1). They go in `src/scholar_harness/console/refusals.py` and in the §7 table of `screening-api-contract.md` in the same change, so `tests/console/test_console_refusals.py` keeps them in step.

| Code | HTTP | Route | Meaning |
| :-- | :-- | :-- | :-- |
| `WORKSPACE_TITLE_INVALID` | 422 | create | the title yields an empty slug |
| `WORKSPACE_EXISTS` | 409 | create | `{root}/{slug}` already exists (a workspace or any other folder); never suffixed. `details.path` names it |
| `WORKSPACE_PATH_REFUSED` | 422 | create, open | the resolved folder is outside the root, a traversal, or a symlink out of it |
| `WORKSPACE_ROOT_UNAVAILABLE` | 409 | list, create | the root is missing and cannot be created, unreadable, or not writable; or the new workspace could not be written (the OS reason is in the message, e.g. a Windows path over 260 characters), and nothing is left behind |
| `WORKSPACE_NOT_VALID` | 409 | open | the folder lacks a canonical marker, or no longer exists |
| `WORKSPACE_BUSY` | 409 | open | an agent run is active or an approval pairing is open; `details` names which |
| `RESTART_UNSUPPORTED` | 501 | open | the server was not started by the `nexus-scholar ui` launcher |

`RUN_ALREADY_ACTIVE` keeps its meaning (a second agent run) and is not reused.

## 6. Tests (M5-slim)

`tests/console/test_workspaces_api.py`:
- list: valid only, invalid with `include_invalid`, `skipped_count`, no recursion, no symlink escape;
- create: the canonical layout plus `PROJECT_INITIALIZED` and `GENESIS` rows, `.mcp.json` and `.env.example`, `WORKSPACE_EXISTS` on a second create, `WORKSPACE_TITLE_INVALID`, `WORKSPACE_PATH_REFUSED`, cleanup after a failure part-way;
- open: `on_open` called with the resolved path after the `202`, `WORKSPACE_BUSY` for a live run and for a staged pairing, `WORKSPACE_NOT_VALID`, `RESTART_UNSUPPORTED` without a launcher, no journal row;
- a phone token is refused `TOKEN_SCOPE_REFUSED` on all three.

`tests/test_ui_launcher.py` covers the restart: same port and token, the new app bound to the new folder.
