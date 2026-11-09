# 07 Done and hand-off    Status: FINAL | Phase 0 Inception | Route `/[locale]/inception/done?draft=rec_<32 hex>` (desktop only) | Milestone M4b

Boards: `Done` (D8, `docs/ux/phase0-inception/final/project/Done.dc.html`). Contract: `docs/architecture/inception-api.md` (genesis), `docs/architecture/workspaces-api.md` §3 and §4 (`POST /workspaces/open`, the restart). Code: `src/scholar_harness/console/api/inception.py:122` (genesis stores `emitted`), `src/scholar_harness/inception/drafts.py:95` (`mark_emitted`), `src/scholar_harness/console/api/workspaces.py:61` (open), `apps/research-ui/components/workspaces-screen.tsx:312-339` (the open-and-wait loop to reuse). The shared draft rules are in 01 "Shared by 01, 04, 05, 06 and 07".

**Purpose.** Confirm what was written, where, and under which protocol fingerprint, then open the new workspace so screening can start.

**Changed from the canvas.** Every cut or change:
- **No "Files written 7 of 7" table with Open links.** No HTTP route reads a workspace file list or opens a file, and the draft's `emitted` record has no file list. The screen states the folder and what the protocol files are in a sentence; it shows no per-file "Open".
- **No journal excerpt block.** The canvas prints the GENESIS event (`workspace WSP-…`, `by you · method HUMAN`). No route reads the journal for this screen, and the event's agent is `nexus-scholar/ui`, not "you". The screen says only that a GENESIS event was logged in the workspace's audit journal, which `emit_workspace` does (`emit.py:202`, `:229`).
- **No `WSP-` id, no recon cache sentence, no `recon_context.json`.** None is in the genesis answer; the draft folder note names the draft instead.
- **Next step is Screening, not Discovery.** The canvas's "Next · Phase 1 Discovery · Review the search plan" has no production screen before M3 reaches the UI, and the decided hand-off here is "Open the workspace", which lands on `/[locale]/screening/home/`. The canvas's terminal line `uv run scholar-harness discover plan` is marked `[proposed]` in the canvas and is cut.
- **A replacement is shown.** The canvas has no replacement state. When `replaced` is true the screen shows the backup folder and the previous fingerprint (see open question 1 for what survives a reload).
- **Draft styling does not apply.** The values here are written facts, not proposals: plain mono text, no draft badge.

## Entry / exit
- Entry: success of "Create the workspace" on 06; "Done" in the stepper once the draft is emitted; "Done" on a finished draft's row in 08; the "Go to the finished workspace" action of `DRAFT_EMITTED` on 01, 04, 05 and 06.
- Exit: "Open the workspace" goes to `/[locale]/screening/home/` after the app has restarted on the new folder; "All workspaces" goes to `/[locale]/workspaces`; "Start another review" goes to `/[locale]/inception/` (08).
- Gate: none. Nothing is written on this screen; "Open the workspace" restarts the engine and UI on the folder (workspaces-api §4), and is refused while an agent run is active or an approval pairing is open (`WORKSPACE_BUSY`).

## Data in
| Field | Source |
| :-- | :-- |
| `emitted{slug, path, protocol_fingerprint, replaced, at}` and the draft's `title` | `GET /api/v1/inception/drafts/{id}` ✓ M4a (`drafts.py:95`) |
| `previous_fingerprint`, `backup_dir` (only when `replaced`) | the `201` body of genesis, kept in `sessionStorage` under `inception:done:<id>` by 06; **not stored on the draft** (open question 1) |
| the workspace to open | `emitted.slug` |
| the workspace now serving (to detect the restart) | `GET /api/v1/workspace/meta` ✓ `src/scholar_harness/console/api/workspace.py:107` |

If the draft has no `emitted`, the screen is not applicable: it shows the client-side state `DRAFT_NOT_EMITTED` ("This draft has not created a workspace yet") with a link to 06. It is not an engine code.

## Data out
- Open: `POST /api/v1/workspaces/open` ✓ (`workspaces.py:61`), body `{slug}`. Answers `202 {slug, path, restarting: true}` and then the engine restarts on that folder, or `200 {…, restarting: false}` when that workspace is already the one serving (a replaced current workspace). The screen then polls `GET /api/v1/workspace/meta` every 500 ms, at most 120 times, until it names `path`, and navigates to `/[locale]/screening/home/` (with `?console=` when set). No journal event: opening changes nothing (workspaces-api decision 2). The UI writes nothing else.

## Backend calls
| Call | Status |
| :-- | :-- |
| `GET /api/v1/inception/drafts/{id}` | ✓ M4a `console/api/inception.py:80` |
| `POST /api/v1/workspaces/open` | ✓ `console/api/workspaces.py:61` (M5-slim) |
| `GET /api/v1/workspace/meta` | ✓ `console/api/workspace.py:107` |
| genesis `201` fields `previous_fingerprint` and `backup_dir` persisted on the draft | ✗ M4b (open question 1) |

Not in `_PHONE_ROUTES`; the open call sits under the loopback origin check.

## States
- **Default (new workspace)**: eyebrow "Inception · done · workspace written"; Literata h1 "The workspace {title} exists."; lede "The protocol files were written once, at the write gate, and the creation is logged as a GENESIS event in the workspace's audit journal." Main: the **Where it is** card (a table: Folder name = slug, Folder = path (LTR), Protocol fingerprint = mono DataCell, Replaced = "No, this is a new workspace"). Side: the **Next** card with the brand button "Open the workspace". Secondary: "All workspaces", "Start another review".
- **Replaced**: the same card with Replaced = "Yes", plus two rows: Previous fingerprint (mono) and Backup folder (`backup_dir`, LTR), and the sentence "The old protocol files are in the backup folder. project.json was kept, so the workspace's history and identity are unchanged." If `previous_fingerprint` and `backup_dir` are not available (the page was reloaded; open question 1) the two rows read "Recorded in the workspace's audit journal (GENESIS)". When the replaced workspace had screening, a note reads "Screening decisions made under the old protocol are still on disk. Screening home will show the protocol changed."
- **Empty**: no draft record is the case `DRAFT_NOT_FOUND`; a draft not yet emitted is `DRAFT_NOT_EMITTED` (above). Neither is a list, so there is no empty list.
- **Loading** (skeleton): a three-row card skeleton while the draft loads. Opening: the whole main area is replaced by `role="status"` text "Opening {title}", with no controls, until the new engine answers; this is the same wait as the Workspaces screen.
- **Error** (typed refusal, `StateCard`; texts in 08 or the existing set):
  - `DRAFT_NOT_FOUND`, `DRAFT_ID_INVALID`, `DRAFT_UNREADABLE`: whole-screen card, "Go to your drafts".
  - `WORKSPACE_BUSY` (409, `details.run_active` or `details.pairing_open`): the existing copy "Work in progress would be stopped" naming which is active, with "Go to screening home"; the Open button stays available for another try.
  - `WORKSPACE_NOT_VALID` (409): "Not a Nexus Scholar workspace" (the folder lost a marker file or was removed after it was created); next step "All workspaces".
  - `WORKSPACE_PATH_REFUSED` (422): existing copy; same next step.
  - `RESTART_UNSUPPORTED` (501): the existing copy, plus the exact command with this workspace filled in, `nexus-scholar ui --workspace {path}` (copyable, LTR). The new workspace exists; only the switch is unavailable.
  - Wait timeout (120 polls without the new path): `ENGINE_UNREACHABLE` (client-side), "Try again" repeats the poll without re-sending the open.
  - Guard codes `ACTION_ORIGIN_REFUSED`, `HOST_REFUSED`, `TOKEN_REQUIRED`, `TOKEN_SCOPE_REFUSED`: shared cards (08).
- **Partial**: the workspace was written but the open step failed (any error above). The "Where it is" card stays; the error card sits above the Next card; nothing is lost.
- **Offline**: the engine is local; offline means unreachable. The card from the last read stays with "As of {time}"; "Open the workspace" is disabled with "needs the engine on this computer".
- **Protocol-changed**: the workspace's protocol is the one just written. After a replacement, the screening home of that workspace reports `STALE_BINDING` ("Protocol changed", prepare again) when it has batches; this screen says so in the replaced note and does not read screening state.

## Desktop layout
Source: `Done` (D8), reduced as listed above; split main and side. Regions: shell and stepper (the "Done" step current); eyebrow, h1, lede; main **Where it is** card (and, for a replacement, the backup rows and note); a small **Draft** card ("Draft {id} is closed. It cannot be edited; start a new review with the same title to replace this protocol.", the id mono); side **Next · Screening** card: heading "Import your search results and start screening.", caption "Opening the workspace restarts the app on its folder.", the brand button "Open the workspace" (44 px), the secondary links "All workspaces" and "Start another review". No GatePanel (nothing is written here). New components: none.

## Mobile layout (≤ 640 px)
Desktop-only on the engine (see 01). A narrow desktop window shows one column: h1, lede, the Where it is card (rows stacked as label over value; long paths wrap, LTR), the Draft card, then the Next card with "Open the workspace" full width above the two links, all 44 px. A real phone gets the desktop pointer card (`TOKEN_SCOPE_REFUSED`).

## Keyboard
Focus order: skip link, shell, stepper, h1, the Where it is values (each copyable value has a Copy button), the Draft card, "Open the workspace", "All workspaces", "Start another review". On arriving from 06, focus is on the h1. While opening, focus moves to the status text. After an error, focus is on the card heading. No single-key shortcuts.

## Copy
Keys in `apps/research-ui/lib/inception-copy.ts`; shared keys are in 01.
- `inception.done.eyebrow` "Inception · done · workspace written"; `title` "The workspace {title} exists."; `lede` "The protocol files were written once, at the write gate, and the creation is logged as a GENESIS event in the workspace's audit journal."
- `where.title` "Where it is"; `where.slug` "Folder name"; `where.path` "Folder"; `where.fingerprint` "Protocol fingerprint"; `where.replaced` "Replaced"; `where.replaced.no` "No, this is a new workspace"; `where.replaced.yes` "Yes"; `where.previous` "Previous fingerprint"; `where.backup` "Backup folder"; `where.recorded` "Recorded in the workspace's audit journal (GENESIS)"; `where.copy` "Copy {value}"; `where.copied` "Copied".
- `replaced.note` "The old protocol files are in the backup folder. project.json was kept, so the workspace's history and identity are unchanged."; `replaced.screening` "Screening decisions made under the old protocol are still on disk. Screening home will show the protocol changed."
- `draft.title` "Draft"; `draft.body` "Draft {id} is closed. It cannot be edited. To change this protocol later, start a new review with the same title and replace it."
- `next.label` "Next · Screening"; `next.heading` "Import your search results and start screening."; `next.body` "Opening the workspace restarts the app on its folder."; `next.open` "Open the workspace"; `next.opening` "Opening {title}"; `next.workspaces` "All workspaces"; `next.another` "Start another review"; `next.command` "Start the app on this workspace"
- `notEmitted.title` "This draft has not created a workspace yet"; `notEmitted.body` "Create the workspace from the review step first."; `notEmitted.action` "Go to Review and create" (client-side code `DRAFT_NOT_EMITTED`).
- Refusals: existing `WORKSPACE_BUSY`, `WORKSPACE_NOT_VALID`, `WORKSPACE_PATH_REFUSED`, `RESTART_UNSUPPORTED` (`apps/research-ui/lib/screening-states.ts:409-426`) and `inception.refusal.<CODE>.*` (08).

## Accessibility
- The Where it is card is a table with row headers; values that are paths, slugs and fingerprints are `dir="ltr"` mono text, selectable, each with a labelled Copy button that announces "Copied".
- "Opening {title}" is `role="status"` with `aria-live="polite"`; refusals `role="alert"`, code selectable under Details.
- The single brand button names its effect. The Draft card and the replaced note are plain text, not colour-coded.
- Contrast pairs from tokens (`ink` on `surface`, `brand` on `ground` for the brand button with `on-brand` text). RTL (ar): layout mirrors; the table's label and value columns swap; paths, slug, fingerprint and `--workspace` command stay LTR; numerals Latin.

## Acceptance tests
Vitest `apps/research-ui/tests/inception-done.test.tsx`:
- renders the slug, path, fingerprint and `replaced` from `emitted`; for a replacement renders `previous_fingerprint` and `backup_dir` from the kept 201 body, and the journal pointer text when they are absent;
- "Open the workspace" posts `{slug}` to `/workspaces/open`, shows "Opening {title}", polls `GET /workspace/meta` until it names the path, then navigates to `/screening/home/`;
- a `200 restarting:false` answer navigates at once;
- `WORKSPACE_BUSY` names the active thing and links to screening home; `WORKSPACE_NOT_VALID` and `WORKSPACE_PATH_REFUSED` map to copy; `RESTART_UNSUPPORTED` shows the copyable `nexus-scholar ui --workspace <path>`; the poll timeout shows `ENGINE_UNREACHABLE` and retries the poll only;
- a draft without `emitted` shows `DRAFT_NOT_EMITTED` with a link to Review;
- exactly one brand button; no GatePanel; i18n and N9 guard.
Playwright `inception.spec.ts` (this screen's part, stateful fake): create from Review, land on Done, open, see the fake restart, land on screening home; a replaced workspace shows the backup; `RESTART_UNSUPPORTED` shows the hint; RTL pass; axe in light and dark; no horizontal overflow at 375 and 1440 px.

## Open questions
Answered by the researcher, 2026-11-09:
1. The draft's `emitted` record keeps `backup_dir` and `previous_fingerprint` when genesis returns them (engine change in M4b; `tests/console/test_inception_api.py::test_a_replacement_records_its_backup_on_the_draft`), so Done shows them after a reload. The tab's copy of the genesis answer is a convenience only.

None open.

## As built (M4b, 2026-11-09)
- No draft card and no copy buttons. The links are "Open the workspace" (brand), "All workspaces" and "Start another review".
- `RESTART_UNSUPPORTED` names `nexus-scholar ui --workspace "<path>"` with this workspace's path.
- Copy keys and their en, fr and ar texts are the code's: `apps/research-ui/lib/inception-copy.ts` (screen copy) and `apps/research-ui/lib/screening-states.ts` (refusal cards). The Copy section above gives the design intent and the English wording; where a key name or a sentence differs, the code is the record and `tests/inception-copy.test.ts` pins every key in every locale.
