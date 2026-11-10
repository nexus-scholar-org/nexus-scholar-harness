# 00 Workspaces (minimal)    Status: FINAL, built (M5-slim) | Phase 2 Screening (entry; borrows Phase 0 spec 00) | Route `/workspaces` (desktop only) | Milestone M5-slim (list, create, open); the full picker stays in M4

Boards: `Main` (Inception D1 "Workspaces", `docs/ux/phase0-inception/final/project/Main.dc.html`), `MobileWorkspaces` (`.../MobileWorkspaces.dc.html`, not used here). Contract: `docs/architecture/workspaces-api.md`, not yet written; it is written before the engine work starts (Decision 6). Decision: `docs/decisions.md`, 2026-11-05, "A minimal workspace screen joins M5-slim" (merged with M1b-2, PR #189), and "The minimal workspace screen: root, open, create" (this spec's answers).

**Purpose.** Pick which review to work on, or start a new empty one, without a terminal, so a packaged desktop app is usable when it was not launched on one folder.

**Changed from the canvas.** This spec cuts the Inception workspace picker (`Main`) down to a list, an open action and a create action. Every cut:
- **No Inception wizard.** The "New review" button on the board starts six Inception steps; here "New workspace" runs only the scaffold of `nexus-scholar init --scaffold-only` (`src/scholar_harness/inception/wizard.py:411` `init_command`). The protocol it writes is the deterministic placeholder, shown as a draft (BRAND_BOOK principle 5) with the text "Placeholder protocol. Run the Inception wizard from the terminal to replace it." Inception stays CLI/MCP, beta (plan §6 M4).
- **No drafts.** The board's "Inception draft · step 5 of 6" row, the "Resume your draft" card, "Start over", "Discard draft" and the recon-cache line are removed. Drafts live in the recon cache and belong to M4.
- **No agent card, no phone card.** "Do this with your agent in Claude" and "Review on your phone / Show pairing code" are removed. Phone pairing lives on screening home (01).
- **No phase badge ladder.** The board shows Screening / Discovery / Inception done. Here the badge shows only what the engine can state from files: "No corpus yet" (unclear role), "Corpus accepted" (include role), "Screening in progress" (brand). Discovery has no production UI before M3.
- **Last-activity column** is the timestamp and event name of the last row of `audit/journal.jsonl`; the board's free sentence ("batch 002 decided") is not generated.
- **No `MobileWorkspaces` layout.** The route is desktop-only by default (plan §4); a phone gets a pointer to the desktop (see Mobile layout).
- **Pagination and search are absent.** The list is a plain table; a search field is added only if the root holds more than 25 folders (copy key reserved, not built in M5-slim).
- **Folder text.** The board prints `workspaces/<slug>/`; a packaged install prints the full path of the folder, LTR, because the root is not necessarily `workspaces/` (Decision 1).

## Entry / exit
- Entry: the packaged app opening with no workspace chosen (`nexus-scholar ui` without `--workspace`; the root is `--root <folder>`, else `NEXUS_WORKSPACES_ROOT`, else `~/Documents/Nexus Scholar/workspaces`); the app-bar workspace name (the current workspace's title, as a link); a refusal card whose next step is "choose another workspace". When `--workspace <path>` is given, the app opens straight on `/screening` and this screen is reached only from the app bar.
- Exit: "Open" on a row goes to `/screening` (01) of that workspace. "New workspace" stays on this screen, adds the row, and shows the next-step card (accept-corpus) with "Open" ready.
- Gate: Open restarts the engine and UI on the chosen folder, so it is refused with `WORKSPACE_BUSY` while an agent run is active or an approval pairing is open; a row that is not a valid workspace has no Open action.

## Data in
| Field | Source |
| :-- | :-- |
| workspaces root path, writable flag, root source (`flag`, `env`, `default`) | `GET /api/v1/workspaces` ✗ M5-slim |
| per row: `slug`, `title`, `path` (absolute; the route is local and desktop-only), `valid`, `invalid_reason?`, `has_corpus`, `screening_started`, `last_event{at, event}`, `is_current`; plus `skipped_count` (invalid folders) | `GET /api/v1/workspaces` ✗ M5-slim (read from `project.json`, `audit/journal.jsonl`, `literature/`). Valid means `protocol.json`, `project.json` and `audit/journal.jsonl` exist; `.mcp.json` is not checked, so older workspaces list. Invalid rows are returned only with `?include_invalid=true`. |
| current workspace (to mark the open row) | `GET /api/v1/workspace/meta` ✓ `src/scholar_harness/console/api/workspace.py:107` |
| engine busy: agent run active, approval pairing open (what a restart would kill) | `GET /api/v1/workspaces` field `busy{run_active, pairing_open}` ✗ M5-slim; sources: run registry (`RUN_ALREADY_ACTIVE` home) and `GET /actions/pairing/status` ✓ `screening.py:1407`. Lets the UI disable Open and explain before the click. |

## Data out
- Create: `POST /api/v1/workspaces` ✗ M5-slim, payload `{title}` only; the slug is derived and the folder is `{root}/{slug}`, shown live under the field. An existing folder is refused `WORKSPACE_EXISTS`, never suffixed (Decision 3). Server side it calls the same scaffold path as `init_command(scaffold_only=True)`: `slugify`, `require_uninitialized` (markers `INIT_MARKERS`, `genesis.py:64`), `scaffold_raw_project`, `compile_protocol_files`, `log_genesis`, then `install_workspace_support_files` (skills, `.mcp.json`, `.env.example`, as the CLI does; Decision 7). Per-item result: `{slug, path, protocol_fingerprint}` or a typed refusal. Journal: the `PROJECT_INITIALIZED` and `GENESIS` events that `log_genesis` already writes to `audit/journal.jsonl`, with agent `nexus-scholar/ui`; the UI never writes the journal itself. A create that fails part-way leaves no half workspace: the server removes a folder it created, and journals nothing.
- Open: `POST /api/v1/workspaces/open` ✗ M5-slim, payload `{slug}`; the server resolves it under the root. It checks the target is valid and that nothing is busy, answers `{slug, path, restarting: true}`, and then the engine and UI restart on that folder (no in-place rebind: no cache, job runner, pairing or phone token is carried over, and phone sessions end). The UI shows "Opening {title}" and reloads onto `/screening` when the new engine answers `GET /workspace/meta`. The restart is done by the `nexus-scholar ui` launcher, which owns the server process. Journal: no event; opening reads and changes nothing (Decision 2).
- No delete, rename, move or import action. Removing a workspace is a file-manager job; the app says so in the empty-folder help text.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/workspaces` | ✗ M5-slim |
| `POST /api/v1/workspaces` | ✗ M5-slim |
| `POST /api/v1/workspaces/open` | ✗ M5-slim |
| `GET /api/v1/workspace/meta` | ✓ `workspace.py:107` |
| `GET /api/v1/screening/actions/pairing/status` | ✓ `screening.py:1407` |
| `nexus-scholar ui` with `--root <folder>` (else `NEXUS_WORKSPACES_ROOT`, else `~/Documents/Nexus Scholar/workspaces`) and `--workspace <path>` (opens one folder directly, skips this screen); also restarts the engine on Open | ✗ M5-slim (plan §6 M5-slim row) |

There is no settings screen and no config file for the root (Decision 1).

None of the three new routes is added to `_PHONE_ROUTES` (`src/scholar_harness/console/serve.py:50`): a phone-scoped token gets `TOKEN_SCOPE_REFUSED`. They sit under the same host and origin guards as the other writes (`HOST_REFUSED`, `TOKEN_REQUIRED`, `ACTION_ORIGIN_REFUSED`); `POST` routes check the loopback origin like the screening actions.

## States
- **Default**: Literata h1 "Which review are you working on?", lede "Each review is one folder on this computer. The list shows the folders under {root}.", one brand button "New workspace", a table (Title and folder path, Status badge, Last activity, Open). The current workspace row carries a text "Open now" badge and no Open button. Machine-written placeholder protocol is shown with the draft styling on the next-step card only.
- **Empty**: root exists but holds no workspace → EmptyState "No workspaces yet" with "New workspace" and a caption "Your reviews will appear here. To use a folder you already have, start the app on it from the terminal." Root missing or not writable → the same card with refusal `WORKSPACE_ROOT_UNAVAILABLE` and its path.
- **Loading** (skeleton): table skeleton with three rows; no count is shown until the listing finishes. Create shows "Creating the workspace" on the button, disabled, until the server answers; no optimistic row.
- **Error** (typed refusal → copy; codes in the section below):
  - `WORKSPACE_TITLE_INVALID` → "That title has no letters or digits to make a folder name from. Use a longer title." (the check mirrors `init_command`: slug is empty).
  - `WORKSPACE_EXISTS` → "A workspace for this title already exists at {path}. Open it, or choose another title." with an "Open it" link. Maps `require_uninitialized` (`genesis.py:397`).
  - `WORKSPACE_PATH_REFUSED` → "That folder is outside the workspaces folder."
  - `WORKSPACE_ROOT_UNAVAILABLE` → "The workspaces folder cannot be read or written: {path}."
  - `WORKSPACE_NOT_VALID` → "This folder is not a Nexus Scholar workspace ({invalid_reason})."
  - `WORKSPACE_BUSY` (HTTP 409) → opening restarts the engine, which would end the work in progress. The card names which is active: "An agent run is active in this workspace. Opening another workspace restarts the app and would stop it." or "An approval is open. Opening another workspace restarts the app and would lose it." With a link "Go to screening home" (01), where the run can be cancelled. The Open buttons are disabled in advance from `busy{run_active, pairing_open}`; the refusal covers a state that changed after the listing.
  - `TOKEN_SCOPE_REFUSED` (phone) → the desktop pointer; `HOST_REFUSED`, `TOKEN_REQUIRED`, `ACTION_ORIGIN_REFUSED` → the shared guard cards (08); `ENGINE_UNREACHABLE` (client-side) → Engine-unreachable card. Every card shows its code, as in `stateCopy` (`apps/research-ui/lib/screening-states.ts`).
- **Partial**: some folders unreadable or invalid. Valid rows list normally; invalid folders are hidden by default behind the caption "n folders skipped · Show them". "Show them" expands rows that are greyed (`aria-disabled`), print the reason (`invalid_reason`), and have no Open action (Decision 4). Never hidden without a count.
- **Offline**: the engine is local, so offline means "engine unreachable". The last listing stays with an "as of" caption; New workspace and Open are disabled. Network loss itself changes nothing. During an Open restart the same card shows briefly as "Opening {title}", then the page reloads onto 01.
- **Stale / protocol changed**: a protocol change is a per-workspace state shown on 01 and 08 after opening; this screen does not read protocol bindings. A listing older than the last create/open is refetched on focus; a row whose folder vanished returns `WORKSPACE_NOT_VALID` on Open and the row is marked.
- **Next-step card after create** (state-card pattern, `action: "terminal"`, as the `SNAPSHOT_NOT_ACCEPTED` card in `screening-states.ts:36`): "Workspace created. Screening starts from an accepted corpus. Accept it from the terminal." with a copyable `nexus-scholar accept-corpus` command (with the `--workspace` argument filled in, LTR) and the placeholder-protocol note. A fresh workspace has no corpus, so screening home would show `SNAPSHOT_NOT_ACCEPTED` on 02; this card says it first.
- **Live-only**: yes. This screen has no demonstration data, so the shell's `Demonstration data` marker must be absent, as on the six screening steps (`apps/research-ui/components/app-shell.tsx`, `isLiveOnlyPath`); `/workspaces` is added to that list in M5-slim and a test pins it. (`isLiveOnlyPath` and its `LIVE_SCREENING_STEPS` list came with M1b-2, PR #189.)

## Desktop layout
Source: `Main` (Inception D1) reduced as listed above. Regions in order: app bar (brand, workspace name link when one is open, locale switch); h1, lede, brand button "New workspace"; the table card; the create panel (inline card under the button, opened by it: title field, derived-folder caption, "Create", "Cancel"); next-step card after a create; footer caption "This computer · engine running · {root}". Status badges use the roles include / unclear / blocked and carry text. The tokens come from `docs/ux/brand/tokens.json`; no new component is introduced (table, badge, EmptyState, state card already exist).

## Mobile layout (≤ 640 px)
Desktop-only (plan §4): the route is not on the phone allowlist. A phone that reaches `/workspaces` shows a single card "Choose the workspace on your desktop. The phone works on the one that is open." with a 44 px "Go to screening" link (`/screening`). No list, no create. `MobileWorkspaces` is not built.

## Keyboard
`n` opens the create panel; `Enter` in the title field submits, `Escape` closes the panel and returns focus to "New workspace"; `/` is reserved for a future search. Row: `Tab` reaches Open; `Enter` activates. Focus order: skip link, app bar, h1, New workspace, create panel (when open), table rows in order, next-step card, footer. After create, focus moves to the next-step card heading; after Open, to the h1 of 01.

## Copy
Keys, en master (fr/ar fall back to en, plan §7; locales en/fr/ar with RTL):
`workspaces.title` = "Which review are you working on?"; `workspaces.lede` = "Each review is one folder on this computer. The list shows the folders under {root}."; `workspaces.cta.new`; `workspaces.cta.open`; `workspaces.openNow` = "Open now"; `workspaces.table.{title,folder,status,lastActivity}`; `workspaces.status.{noCorpus,corpusAccepted,screening}`; `workspaces.create.{label,titleField,titleHelp,folderCaption,submit,cancel,submitting}`; `workspaces.create.placeholderProtocol`; `workspaces.next.{title,body,command,copy}`; `workspaces.empty.{title,body}`; `workspaces.opening` = "Opening {title}"; `workspaces.skipped.{count,show,hide}` = "{n} folders skipped · Show them"; `workspaces.invalid.reason.{noProject,noProtocol,noJournal,unreadable}`; `workspaces.busy.{run,pairing,goHome}`; `workspaces.phone.desktopOnly`; `workspaces.refusal.{WORKSPACE_TITLE_INVALID,WORKSPACE_EXISTS,WORKSPACE_PATH_REFUSED,WORKSPACE_ROOT_UNAVAILABLE,WORKSPACE_NOT_VALID,WORKSPACE_BUSY}`; `workspaces.liveStamp`. Input hint, close and copy-button names are keys too: no literal `aria-label`, `title`, `alt` or `placeholder` attributes (N9 guard).

## Accessibility
Table with real headers; the current row has `aria-current="true"` plus the text "Open now". Greyed (invalid) rows use `aria-disabled` and print the reason, never colour alone. Create field has a visible label and `aria-describedby` for the derived-slug caption, announced politely as it updates; refusals use `role="alert"`. Contrast pairs from tokens (`ink` on `ground`, `brand` on `brand-soft`, role badges per BRAND_BOOK). RTL: layout mirrors, table columns reverse, folder paths, the slug and the terminal command stay LTR (`dir="ltr"`), numerals Latin. The copy button announces "Copied".

## Acceptance tests
Vitest: `workspaces.list.test.tsx` (rows, current marker, invalid folders hidden behind "n folders skipped" and greyed without Open when shown), `workspaces.create.test.tsx` (slug caption, every refusal code maps to copy, next-step card shows the accept-corpus command), `workspaces.live-only.test.ts` (no demonstration marker on the path), `workspaces.i18n.test.ts` (keys exist in en; N9 guard). Python: `tests/console/test_workspaces_api.py` (list, create writes the canonical layout and `PROJECT_INITIALIZED` + `GENESIS`, `WORKSPACE_EXISTS` on a second create, `WORKSPACE_PATH_REFUSED` on a traversal, create also writes `.mcp.json` and `.env.example`, a workspace without `.mcp.json` still lists, `WORKSPACE_BUSY` 409 with a run active and with a pairing open, open sends no journal event, phone token refused with `TOKEN_SCOPE_REFUSED`), and `tests/console/test_console_refusals.py` extended for the new codes. Playwright: `workspaces/workspaces.spec.ts` (create in an empty root, open it, land on 01 with `SNAPSHOT_NOT_ACCEPTED` guidance; open refused with `WORKSPACE_BUSY` while a run is active, with the link to screening home; RTL pass), `workspaces/workspaces.mobile.spec.ts` (WebKit mobile shows the desktop pointer only).

## Proposed routes and refusal codes
New routes (all ✗ M5-slim): `GET /api/v1/workspaces`, `POST /api/v1/workspaces`, `POST /api/v1/workspaces/open`.

New refusal codes, to be added to `src/scholar_harness/console/refusals.py` and the contract's §7 table in the same change (`tests/console/test_console_refusals.py` keeps them in step). `docs/architecture/refusals.md` lists agent-role codes; these are console codes outside Contract v1, like the existing console set.
| Code | When |
| :-- | :-- |
| `WORKSPACE_TITLE_INVALID` | the title yields an empty slug (as `init_command` refuses) |
| `WORKSPACE_EXISTS` | the target folder already carries an `INIT_MARKERS` file |
| `WORKSPACE_PATH_REFUSED` | the resolved target is outside the workspaces root, or a path traversal |
| `WORKSPACE_ROOT_UNAVAILABLE` | the root is missing, unreadable or not writable |
| `WORKSPACE_NOT_VALID` | Open on a folder without the canonical markers, or one that vanished |
| `WORKSPACE_BUSY` | HTTP 409. Open while an agent run is active or an approval pairing is open: the restart would end it. The detail names which (`run_active`, `pairing_open`) |

`RUN_ALREADY_ACTIVE` keeps its own meaning (a second run) and is not reused.

## Decisions
All answered by the researcher, 2026-11-05.
1. Root: default `~/Documents/Nexus Scholar/workspaces`; `nexus-scholar ui --root <folder>` or `NEXUS_WORKSPACES_ROOT` overrides it; `--workspace <path>` still opens one folder directly and skips this screen. No settings screen, no config file. (researcher, 2026-11-05)
2. Open restarts the engine and UI on the chosen folder; there is no in-place rebind. Because a restart would kill an agent run or an open approval pairing, Open is refused while either is active: `WORKSPACE_BUSY` (409, names which is active, links to screening home where the run can be cancelled), with `busy{run_active, pairing_open}` in the listing. No `WORKSPACE_OPENED` journal event. (researcher, 2026-11-05)
3. Create asks for a title only; the slug is derived and the folder is `{root}/{slug}`; an existing folder is refused `WORKSPACE_EXISTS`, never suffixed. (researcher, 2026-11-05)
4. Invalid folders are hidden by default with "n folders skipped · Show them"; expanded rows are greyed with the reason and have no Open. (researcher, 2026-11-05)
5. The placeholder protocol is allowed, shown as a draft with the placeholder line; no Contract v1 change. (researcher, 2026-11-05)
6. `docs/architecture/workspaces-api.md` is written before the engine work; `GET /workspaces` may return absolute paths (desktop-only, local). (researcher, 2026-11-05)
7. Create also runs `install_workspace_support_files` (skills, `.mcp.json`, `.env.example`), like the CLI; validity checks only `protocol.json`, `project.json` and `audit/journal.jsonl`, so older workspaces without `.mcp.json` still list. (researcher, 2026-11-05)

## Addendum (M4b, 2026-11-09): the "New review" link
The Inception screens (`docs/ux/phase0-inception/final/01-scope.md` to `08-states.md`) now exist, so this screen gets one entry to them. Nothing else in this spec changes.
- **Link.** A secondary link-button "New review" (`workspaces.cta.newReview`, 44 px) beside the brand button "New workspace", going to `/[locale]/inception/` (08, the list of drafts with "Start a new review"). It is a link, not a second brand button; "New workspace" stays the screen's one brand button. It carries `?console=` when set. It is present in the Default and Empty states, absent when the root is unavailable, and absent on a phone (this screen shows the desktop pointer there).
- **What "New workspace" still is.** The empty scaffold with the placeholder protocol; it does not start the wizard. The "No Inception wizard" cut above stands for it.
- **Placeholder line.** `workspaces.create.placeholderProtocol` changes from "Placeholder protocol. Run the Inception wizard from the terminal to replace it." to "Placeholder protocol. Use New review with the same title to replace it." (A review with the same title reaches `WORKSPACE_EXISTS` at the write gate and asks before replacing; the old files are backed up.) fr and ar by the implementer.
- **Not added.** No count of drafts, no "Resume" link and no draft rows here; drafts have their own page (08). The empty-folder help text is unchanged.
- **Copy key.** `workspaces.cta.newReview` = "New review".
- **Tests.** Add to `workspaces.list.test.tsx`: the link is present with the right href, is secondary, and the screen still has exactly one brand button; to `workspaces/workspaces.spec.ts`: the link opens `/inception/`.
