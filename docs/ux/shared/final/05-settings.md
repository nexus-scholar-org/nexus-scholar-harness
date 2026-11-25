# 05 Settings and first-run setup    Status: FINAL (the two open questions were answered by the researcher on 2026-11-24, each as proposed; see "Open questions") | Shared (no phase; reached from Workspaces, the app shell and the control window) | Route `/[locale]/settings/` (first run: `/[locale]/settings/?setup=1`; desktop only) | Milestone M13 Part B (settings file, keychain, routes, screen)

Boards: none. No canvas board exists. The screen reuses the Workspaces screen's patterns (`apps/research-ui/components/workspaces-screen.tsx`: header block, cards, the wait for the engine after a restart, the desktop pointer) and the state card (`components/screening-state-card.tsx`); no new visual language and no new component. Records: `docs/roadmap/milestones/M13-installers.md` §4.3 (First-run setup, on a screen) and §5.2 "Part B"; `docs/roadmap/milestones/M13-part-b.md` ("Questions answered by the researcher (2026-11-24)", answers 1 to 6, quoted below as "answer n"). Neighbouring specs: `docs/ux/phase2-screening/final/00-workspaces.md` (the Settings link and the restart wait), `docs/ux/shared/final/04-next-step.md` (row `SETUP_NEEDED` names the e-mail and the OpenAlex key; its button goes to the discovery plan, not here). Brand: `docs/ux/brand/BRAND_BOOK.md` (one brand button per screen; machine output as a draft), `docs/ux/brand/tokens.json`.

**Purpose.** Give the contact e-mail, the optional keys and the folder of the reviews to Nexus Scholar once, on a screen, so the app searches without a terminal, a `.env` file or a restart by the researcher, and never shows a key again.

**Changed from the canvas.** No board exists, so each point is where this spec departs from an earlier text.
- **Three parts, not four** (answer 1). M13 §4.3 lists a fourth part, "Connect an AI assistant" and "Tell me when a new version is out". Neither is on this screen and neither has a placeholder; Part C and Part D add their own rows when they are built (and amend this spec then).
- **Five key rows, not "an AI provider key"** (answer 5). §4.3 names the OpenAlex key, the Semantic Scholar key and one AI key; the screen has those two plus three AI rows (Anthropic, OpenAI-compatible, Google Gemini). Every key row is write-only. There is no base-URL setting.
- **Who wins is shown, not hidden** (answer 2). The environment beats `.env` in the engine's current folder, which beats the screen (settings file and keychain). A row whose value comes from the environment or `.env` says so and has no edit.
- **"Later" is remembered** (answer 4), so the screen does not reopen at every start. A search still stops with `MAILTO_NOT_SET`; its card now links here.
- **No keychain** (answer 6): the screen asks before it keeps a key in a file, wherever the keychain fails (not only on Linux).
- **The Workspaces spec's "There is no settings screen and no config file for the root" (`00-workspaces.md`, "Backend calls") is superseded** for the folder: the screen saves it in the settings file. `--root` and `NEXUS_WORKSPACES_ROOT` still win (they show as "set elsewhere").
- **Not added:** a "test my key" button (nothing is sent to test an e-mail or a key), a reveal or copy button on a key, a base URL for an AI provider, an e-mail address shown anywhere but this screen and the sentence that names it.

## Entry / exit
- Entry:
  - **First run, installed start only** (answer 3): the app started from its icon, `started_as` is `installed`, `setup` is `pending` (no settings file yet). The launch link lands on `/[locale]/settings/?setup=1` instead of Workspaces. The decision is the engine's (`GET /settings`: `started_as`, `setup`); the browser sends the researcher there only when both say so.
  - **Terminal start** (`nexus-scholar ui`): lands where it does today (Workspaces, or a workspace). Setup never opens by itself.
  - A **Settings** link, on both starts: on Workspaces beside "New workspace" and "New review" (a secondary link, `workspaces-screen.tsx:388-394` is the pattern; the screen keeps exactly one brand button), and in the app shell's site header (`app-shell.tsx:59`, `SiteHeader`) on every route.
  - The control window's **Settings** button (`control_window.py:238-246`, where "Open the settings folder" stands today) opens `/[locale]/settings/` in the browser with a fresh launch link, the way Open in browser does. The window is English only, so the link carries the app's default locale.
  - The state cards' link action (see Dependencies).
- Exit: **Done** and **Later** (setup mode) go to Workspaces (`/[locale]/workspaces/`). In settings mode a "Back to Workspaces" link goes there; a refusal card's "choose another workspace" is unchanged. No other exit; the screen holds no draft that would be lost (each part saves on its own).
- Gate: **Done** is offered only once a contact e-mail is saved (`contact_email.value` not null, from the engine's last answer; the browser does not judge). **Later** is always offered. Neither writes anything but `setup` (see Data out). A phone token is refused (`TOKEN_SCOPE_REFUSED`).

## Data in
| Field | Source |
| :-- | :-- |
| `shape` (`settings-v1`), `started_as` (`installed`, `terminal` or null), `setup` (`pending`, `done`, `later`), `settings_folder` (path, LTR) | `GET /api/v1/settings` ✗ M13 Part B |
| `contact_email{value, source}` (the address is shown; it is not a secret) | same |
| `keys{openalex, semanticscholar, anthropic, openai_compatible, gemini}` each `{set, source}`; never a value | same |
| `workspaces_root{path, source}` | same |
| `key_store{kind: keychain\|file\|none, file}` (where a saved key is kept; names the file when `kind` is `file`) | same |
| `source` is one of `environment`, `env_file`, `settings`, `keychain`, `file`, `flag`, `default`, or null | same |
| the variable's name behind `environment` (for the sentence "Set in the environment (SCHOLAR_MAILTO)") | a fixed table in `lib/settings-copy.ts`: `SCHOLAR_MAILTO`, `SCHOLAR_OPENALEX_KEY` (`src/scholar_search/config.py:27`), `SCHOLAR_S2_KEY` (`:35`), `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY` (`src/scholar_agent/keys.py:23-27`), `NEXUS_WORKSPACES_ROOT`. Names only, never values |
| how the engine was started (to word the key store: Windows Credential Manager, the macOS Keychain, the desktop keyring) | the browser's platform is not used; the engine adds `key_store.label` ✗ M13 Part B if it wants a platform word, otherwise the generic "the system keychain" is printed |

The cookie `nexus_started_as` (`lib/engine-start.ts:16`, `useInstalled`, `:41`) only words the state cards. The screen reads `started_as` from `GET /settings`, not from the cookie.

No domain decision is made in the browser (`apps/research-ui/AGENTS.md`): the browser does not validate an e-mail (it only prints the engine's `SETTING_INVALID`), does not rank sources, does not decide that a keychain is missing.

## Data out
Every write is a button press on one row; nothing is saved while typing.

- **Save the e-mail**: `PUT /api/v1/settings/contact-email` `{value}` → 200 with the new `settings-v1`. An empty value removes it (the "Remove" button sends `{value: ""}`). The row re-renders from the answer.
- **Save or replace a key**: `PUT /api/v1/settings/keys/{name}` `{value, use_file?}` → 200 with `settings-v1` (no value inside). The input is emptied and its value dropped from component state at the moment the request is sent, so a refusal never leaves a key on screen; the researcher types it again. `use_file: true` is sent only by the answer "Keep the key in that file" (see the keychain-unavailable state), together with the same `value`, which the component keeps for that one resend (in memory, in the open confirmation, and drops on Cancel or on any answer).
- **Remove a key**: `POST /api/v1/settings/keys/{name}/remove` → 200 with `settings-v1`. No confirmation step: the row says "Not set" and the key can be typed again; the provider still holds the key it issued (the row's help says "Remove it at the provider if you no longer want it valid" only for the AI rows, `settings.key.removeNote`).
- **Change the folder**: `POST /api/v1/settings/folder/choose` (no body) → `{chosen: path|null}`. The engine opens the folder dialog on this computer's desktop and waits (the request stays open while the dialog is open). `null` is a cancel and changes nothing. A chosen folder is saved by the engine, which then restarts in place on it (as Open does, `00-workspaces.md` "Data out"); the page waits for it (see "Restarting").
- **Finish setup**: `POST /api/v1/settings/setup` `{choice: "done" | "later"}` → 200 with `settings-v1`, then the browser goes to Workspaces. "Later" is remembered in the settings file (answer 4).
- Journal: none. Settings are not review events and no workspace may be open; the workspace journal is never written. The engine's own log never holds a key (M13 §4.2 "The log file"); the e-mail is masked there.
- Keys and the e-mail take effect at once: the engine reloads its settings in place, with no restart and no lost tab, so a search that was refused for a missing e-mail succeeds on the next press (M13 §5.2 Part B definition of done). Only the folder restarts the engine.

## Backend calls
All new calls are desktop only (not in `_PHONE_ROUTES`, `src/scholar_harness/console/serve.py:64`: a phone token gets `TOKEN_SCOPE_REFUSED`), same origin, under the browser prefix `/api/console`, behind the same host and origin guards as the other writes (`HOST_REFUSED`, `TOKEN_REQUIRED`, `ACTION_ORIGIN_REFUSED`). The proxy `apps/research-ui/app/api/console/[...path]/route.ts` forwards GET; each PUT and POST path below is added to its allow-list ✗ M13 Part B. All six routes are **workspace-free** ✗ M13 Part B: the first run has no workspace open, and `serve.py:346` and `:367` answer `409 WORKSPACE_NOT_VALID` for any `/api/` route outside `_workspace_free` (`serve.py:104`), so `/api/v1/settings` and `/api/v1/settings/` are added there.

| Call | Status |
| :-- | :-- |
| `GET /api/v1/settings` | ✗ M13 Part B |
| `PUT /api/v1/settings/contact-email` | ✗ M13 Part B |
| `PUT /api/v1/settings/keys/{name}` (`name` one of `openalex`, `semanticscholar`, `anthropic`, `openai_compatible`, `gemini`) | ✗ M13 Part B |
| `POST /api/v1/settings/keys/{name}/remove` | ✗ M13 Part B |
| `POST /api/v1/settings/folder/choose` | ✗ M13 Part B |
| `POST /api/v1/settings/setup` | ✗ M13 Part B |
| the engine reading the settings file and the keychain after the environment and `.env` (search settings `src/scholar_search/config.py:9-38`, the PDF look-up, the MCP server) | ✗ M13 Part B (today they read the environment and `.env` only) |
| the key store: `SERVICE = "nexus-scholar"` (`src/scholar_agent/keys.py:22`), `store_key` (`:128`), `clear_key` (`:139`), `keychain_available` (`:76`); today only the three AI providers (`ENV_VARS`, `:23-27`) | ✓ for the three AI keys; ✗ M13 Part B to add `openalex` and `semanticscholar` and the file fallback |
| `GET /api/v1/workspaces` (the Workspaces screen's reads; the Settings link goes from it) | ✓ `src/scholar_harness/console/api/workspaces.py:33` (as cited in `00-workspaces.md`) |
| `GET /api/v1/workspace/meta` (the wait for the restarted engine, as `currentWorkspacePath`, `workspaces-screen.tsx:349`) | ✓ `src/scholar_harness/console/api/workspace.py:107` |
| the restart in place on a folder (`nexus-scholar ui` launcher; refuses `RESTART_UNSUPPORTED` when the engine was not started by it) | ✓ M5-slim (Workspaces Open); reused by ✗ M13 Part B |
| the control window's Settings button (`control_window.py:245` replaces "Open the settings folder" as the link, which stays a smaller link) | ✗ M13 Part B |

### Refusals
| Code | Where | HTTP | Status |
| :-- | :-- | :-- | :-- |
| `SETTING_INVALID` | e-mail (not an address; format checked, nothing sent) or key (empty or over-long) | 422 | ✗ M13 Part B |
| `SETTING_SET_ELSEWHERE` | e-mail, key or folder when the environment, `.env`, `--root` or `NEXUS_WORKSPACES_ROOT` sets it | 409 | ✗ M13 Part B |
| `KEYCHAIN_UNAVAILABLE` | key save; `details.file` is the file it would use | 409 | ✗ M13 Part B |
| `FOLDER_DIALOG_UNAVAILABLE` | folder choose; no desktop available | 409 | ✗ M13 Part B |
| `WORKSPACE_ROOT_UNAVAILABLE` | folder choose; the folder cannot be written | existing | ✓ `00-workspaces.md` "Proposed routes and refusal codes" |
| `RESTART_UNSUPPORTED` | folder choose; engine not started by `nexus-scholar ui`; nothing is saved | existing | ✓ (Workspaces Open) |
| `WORKSPACE_BUSY` | folder choose while an agent run or an approval is in progress; refused before the dialog opens, nothing is saved | existing | ✓ (Workspaces Open, `00-workspaces.md` Decision 2) |
| `TOKEN_SCOPE_REFUSED`, `HOST_REFUSED`, `TOKEN_REQUIRED`, `ACTION_ORIGIN_REFUSED` | every call | existing | ✓ shared guards |

The four new codes are added to `src/scholar_harness/console/refusals.py` and to the contract's refusal table in the same change (`tests/console/test_console_refusals.py` keeps them in step), as `00-workspaces.md` did for its codes. `docs/architecture/refusals.md` lists agent-role codes; these are console codes outside Contract v1.

## States
The screen reads the engine on load and after every write; each row re-renders from the `settings-v1` the engine returned.

- **Default** (settings mode, `?setup` absent): Literata h1 "Settings", a lede, three cards in this order: "Your e-mail address", "Keys", "Where your reviews are kept". Each row shows its state in text, never colour alone: the e-mail's value in a field with "Save"; each key "Set" (include role) with "Replace" and "Remove", or "Not set" (unclear role) with a password field and "Save key"; the folder's path (LTR) with "Change…". Under each row one source line (see Copy `settings.source.*`): "Saved in your settings", "Kept in the system keychain", "Kept in {path}". A link "Back to Workspaces". No brand button.
- **First run** (`?setup=1`, `setup` is `pending`): the same three cards with h1 "Set up Nexus Scholar" and the lede "Three things, each saved on its own. You can do them later." Below the cards: **Done** (the one brand button; disabled with the note `settings.setup.doneNeedsEmail` until the e-mail is saved, `aria-disabled` and the note linked by `aria-describedby`) and **Later** (secondary). The e-mail card says "Needed before any search" and holds the focus first (see Keyboard). `?setup=1` with `setup` already `done` or `later` renders settings mode (the engine's state wins; the query is only a hint) and the URL is replaced without it.
- **Empty** (nothing set): the e-mail field empty with its help sentence; every key row "Not set"; the folder row shows the default path with the source "Default location" (`default`). This is the first-run look. A first-run note: "Nothing here is needed to open a review. A search needs the e-mail address."
- **Loading** (skeleton): h1 and three card skeletons with `aria-busy="true"`; no value, no source line and no button until the first answer, so no wrong "Not set" flashes. A refresh after a write keeps the previous values on screen (no skeleton); the row being written shows its button as "Saving…", disabled. The folder row shows "A folder window is open on your computer. Choose the folder there." while the dialog is open (see below).
- **Error** (typed refusal → copy, inside the row that was written, `role="alert"`, with the code in a `font-mono` line as `stateCopy` prints it):
  - `SETTING_INVALID` (e-mail) → "That does not look like an e-mail address. Check it and save again. Nothing was sent." The field keeps its text and focus.
  - `SETTING_INVALID` (key) → "That key is empty or too long. Paste it again." The field is empty (the value was dropped on send) and has focus.
  - `SETTING_SET_ELSEWHERE` → the row's source line is shown ("Set in the environment (SCHOLAR_MAILTO)") and the edit is removed; copy "This value is set outside the screen, so it cannot be changed here. Change it where it is set, then reload." This is the result of a race (the listing said editable, the engine says otherwise); the row re-reads.
  - `KEYCHAIN_UNAVAILABLE` → not an error card: the confirmation state below.
  - `FOLDER_DIALOG_UNAVAILABLE` → "Nexus Scholar cannot open a folder window because this computer has no desktop for it. Start the app with --root <folder>, or set NEXUS_WORKSPACES_ROOT." (installed start: "Use the Nexus Scholar window's Open the settings folder, or ask for help." is not offered; the sentence stands as above, with `--root` shown only when `started_as` is `terminal`).
  - `WORKSPACE_ROOT_UNAVAILABLE` → "The reviews folder cannot be read or written: {path}." (the existing `workspaces.refusal.WORKSPACE_ROOT_UNAVAILABLE` text; the path is the one chosen). The folder is unchanged.
  - `RESTART_UNSUPPORTED` → "This copy of Nexus Scholar cannot restart itself. Stop it and start it again on the folder you want." (nothing is saved and the folder is unchanged; answered 2026-11-24.)
  - `WORKSPACE_BUSY` → the Workspaces screen's copy (`workspaces.busy.*`) with its "Go to screening home" link; refused before the dialog opens, nothing is saved (answered 2026-11-24).
  - `TOKEN_SCOPE_REFUSED` (a phone token) → the desktop pointer, as on Workspaces.
  - `HOST_REFUSED`, `TOKEN_REQUIRED`, `ACTION_ORIGIN_REFUSED` → the shared guard cards (`screening-state-card.tsx`); `ENGINE_UNREACHABLE` (client-side; proxy `CONSOLE_UNREACHABLE` 502, `CONSOLE_TIMEOUT` 504) → the existing engine-unreachable card, see Offline. An unregistered code prints itself under Details; the screen never guesses a meaning.
- **Partial** (some rows set elsewhere): the row shows its source and no edit control, only the text:
  - e-mail from the environment: "Set in the environment (SCHOLAR_MAILTO)", the address printed read-only; from `.env`: "Set in the .env file".
  - a key from the environment or `.env`: "Set" with the same source line and no Replace or Remove (the screen can neither read nor change it). If the keychain also holds a key that is not used, the engine's `source` is still `environment`; the screen says nothing about the other key (it cannot see it).
  - the folder from `--root` (`flag`) or `NEXUS_WORKSPACES_ROOT` (`environment`): the path read-only with "Set when the app was started (--root)" or "Set in the environment (NEXUS_WORKSPACES_ROOT)", and no Change… button.
  - Other rows stay editable. In setup mode **Done** counts an e-mail set elsewhere as saved (`contact_email.value` is not null), so setup can finish with nothing typed.
- **Keychain unavailable** (answer 6; the state after `KEYCHAIN_UNAVAILABLE` on a key save): an inline confirmation in that key's row, `role="alertdialog"`-free (it is a plain region, focus moves to its heading): "Your computer has no keychain Nexus Scholar can use. Keep the keys in a file only you can read? {file}" with two buttons, **Keep the key in that file** (sends the save again with `use_file: true`) and **Do not save** (drops the typed key; nothing was written). The file path is `details.file`, shown LTR. After yes, the row says "Kept in {file}" and every later key goes there without asking again (`key_store.kind` is `file`; the engine, not the browser, remembers). Where `key_store.kind` is `none` and no key has been saved, the Keys card says so up front in one sentence, `settings.store.none`, so the question is no surprise.
- **Restarting** (after a folder change): when `chosen` is a path the folder row is replaced by the status line "Moving to {path}…" (`role="status"`), the rest of the form is hidden, and the page polls `GET /api/v1/settings` every 500 ms for up to 120 tries (the loop of `workspaces-screen.tsx:346-358`) until `workspaces_root.path` equals the chosen path, then reloads the same URL (`?setup=1` kept in setup mode, so the researcher continues). The old engine stopping and the new one not yet up are not errors (errors during the wait are swallowed, `:353-355`). After the wait times out: the engine-unreachable card with "Check again". Nothing typed before the restart is lost, because each part was saved on its own.
- **Folder dialog open**: while `POST /folder/choose` is pending the row shows "A folder window is open on your computer. Choose the folder there." and Change… is disabled; the page is otherwise usable. Cancel in the dialog returns `{chosen: null}` and the row returns to its default with no message (a cancel is not a result).
- **Offline**: the engine is local, so offline means unreachable. The last answer stays on screen with "as of {time}" and every button is disabled (`aria-disabled`), so no write can be sent into the dark; the existing engine-unreachable card (`ENGINE_UNREACHABLE`) sits above the cards with "Check again". During the folder restart the same card appears only after the wait times out. Network loss on the machine changes nothing (loopback). A key typed before the engine went away stays in its field until the researcher sends it or leaves; it is never stored by the page.
- **Stale / protocol changed**: cannot occur. The screen reads no workspace, no protocol and no corpus: its routes are workspace-free and the settings are not bound to any protocol fingerprint. A settings answer older than the last write is discarded on arrival (the page applies the answer to the write it made, then refetches on window focus, as Workspaces does). A value changed outside the screen (the settings file edited by hand) shows on the next focus refetch, with no banner.
- **Live-only**: yes. The screen has no demonstration data, so the shell's `Demonstration data` marker is absent: `/settings` is added to the live-only list (`isLiveOnlyPath`, as `/workspaces` was in M5-slim) and a test pins it. Machine output: none; there is no model draft on this screen, so the draft styling is not used.

## Desktop layout
No board. Regions in order inside `main`: eyebrow ("Setup" in setup mode, otherwise none) and h1; lede; the three cards, each a `section` with its h2 and an `aria-labelledby`; in setup mode the action row (**Done**, **Later**) after the cards; in settings mode a "Back to Workspaces" link after them; a footer caption "This computer · engine running · {settings_folder}" (LTR path). Max width as the Workspaces screen (`max-w-2xl` lede, cards full width of the container); the cards use `bg-leaf` with `rule` borders, `ink` text, h1 `font-display`.

1. **Your e-mail address** card: the help sentence ("The literature databases ask who is sending requests. Nexus Scholar sends this address to the literature databases, to Unpaywall, and to the websites it downloads open-access PDFs from."), one field `type="email"` with its visible label, "Save" (secondary), "Remove" (a text button, only when a value is saved and editable), the source line.
2. **Keys** card: one sentence on where keys are kept ("Keys are kept in {where} and are never shown again."), then two groups with h3: "Literature databases" (OpenAlex, then Semantic Scholar) and "AI drafts (optional)" (Anthropic, OpenAI-compatible, Google Gemini, with the group sentence "Only for drafts the app asks an AI for; the provider charges you."). Each key is one row: label, help, then either the password field with "Save key", or the text "Set" with "Replace" and "Remove"; the source line under it. A key row in "Set" state shows no field. "Replace" swaps the row to the password field (focus moves to it) with "Save key" and "Cancel".
3. **Where your reviews are kept** card: the folder path (LTR, selectable text), "Change…" (secondary), the source line, and the sentence "Each review is one folder under this one. Changing it restarts Nexus Scholar on the new folder; this page reloads by itself."

The one brand button is **Done** in setup mode. Settings mode has none: every row saves on its own with a secondary button, so no row is "the" action (this spec's choice, within the brand book rule of one brand button per screen at most).

The app shell's `NextStepBar` is not rendered on this route (it renders on inception, discovery and screening routes only, `app-shell.tsx:63`; `04-next-step.md` "Which routes"), and `/settings` is added to its absent list so the settings page never shows a review's next step above a first-run setup.

## Mobile layout (≤ 640 px)
Per plan §4 the screen is a desktop screen: its routes are not on the phone allowlist. Two cases:
- **A narrow desktop window** (the same computer; a desktop token): the screen works. The cards stack in one column; fields, buttons and the "Settings" link are ≥ 44 px (`min-h-11`); **Done** and **Later** are full width, **Done** first. The folder row adds one caption "The folder window opens on the computer that runs Nexus Scholar." (`settings.folder.whereDialog`). Paths wrap with `overflow-wrap:anywhere` and stay `dir="ltr"`.
- **A phone** (a phone token, a different device): every route of this screen answers `TOKEN_SCOPE_REFUSED`, and the page renders a single card "Settings are changed on the computer that runs Nexus Scholar, because a key or a folder is chosen there." with a 44 px "Go to screening" link (`/[locale]/screening/`), as `workspaces.phone.desktopOnly` does on Workspaces. A phone cannot choose the folder (the dialog opens on the engine's desktop) and cannot be trusted with a key. No gestures.

## Keyboard
- Focus order: skip link, site header (its "Settings" link is a normal stop), h1 (not a stop), the e-mail field, "Save" (then "Remove" when shown), the key rows top to bottom (field or Replace, Remove, per row), "Change…", then in setup mode **Done** and **Later**; in settings mode "Back to Workspaces". Footer last.
- On load in setup mode the focus goes to the e-mail field (the first thing needed); in settings mode nothing steals focus (the skip link and `main` work as everywhere).
- `Enter` in a field saves that row only. `Escape` in a Replace field cancels and returns focus to the row's "Replace" button. "Replace" moves focus to the new field; "Save key" and Cancel return focus to the row's "Replace" button (key now "Set") or, after a refusal, stay on the field. "Remove" returns focus to the row's field (the key is now "Not set").
- The keychain confirmation takes focus on its heading when it opens; "Keep the key in that file" and "Do not save" are its two stops; after either, focus returns to the key's field (no) or its "Replace" button (yes).
- "Change…" opens the system dialog (the page cannot move focus into it); on return (a chosen folder or a cancel) focus goes to "Change…" again, or, after a chosen folder, to the status line "Moving to {path}…" (`tabIndex={-1}`) while the page waits.
- No single-key shortcut. The existing shell shortcuts (`g t`, `g p`, `?`) are untouched and ignored while a field has focus, as everywhere.

## Copy
Keys under `settings.` in a new copy file `apps/research-ui/lib/settings-copy.ts` ✗ M13 Part B (en master; fr and ar written by the implementer from the table below and reviewed; a missing string falls back to en, plan §7). Arabic is RTL: the page mirrors, and paths, e-mail addresses, variable names (`SCHOLAR_MAILTO`) and `--root` stay `dir="ltr"` in `bdi`. No literal `aria-label`, `title`, `alt` or `placeholder` (N9). `{...}` are parameters printed as given.

| Key | en | fr | ar |
| :-- | :-- | :-- | :-- |
| `settings.title.settings` | Settings | Réglages | الإعدادات |
| `settings.title.setup` | Set up Nexus Scholar | Configurer Nexus Scholar | إعداد Nexus Scholar |
| `settings.eyebrow.setup` | Setup | Première configuration | الإعداد الأول |
| `settings.lede.setup` | Three things, each saved on its own. You can do them later. | Trois choses, chacune enregistrée séparément. Vous pouvez les faire plus tard. | ثلاثة أمور، يُحفظ كلٌّ منها على حدة. يمكنك إتمامها لاحقًا. |
| `settings.lede.settings` | Your contact e-mail, your keys and where your reviews are kept. A change applies at once. | Votre adresse de contact, vos clés et l'emplacement de vos revues. Une modification s'applique tout de suite. | بريدك للتواصل ومفاتيحك ومكان حفظ مراجعاتك. يسري أي تغيير فورًا. |
| `settings.firstRunNote` | Nothing here is needed to open a review. A search needs the e-mail address. | Rien ici n'est nécessaire pour ouvrir une revue. Une recherche demande l'adresse e-mail. | لا شيء هنا لازم لفتح مراجعة. يحتاج البحث إلى عنوان البريد. |
| `settings.link` | Settings | Réglages | الإعدادات |
| `settings.back` | Back to Workspaces | Retour aux espaces de travail | العودة إلى مساحات العمل |
| `settings.email.heading` | Your e-mail address | Votre adresse e-mail | عنوان بريدك الإلكتروني |
| `settings.email.label` | E-mail address | Adresse e-mail | عنوان البريد الإلكتروني |
| `settings.email.help` | The literature databases ask who is sending requests. Nexus Scholar sends this address to the literature databases, to Unpaywall, and to the websites it downloads open-access PDFs from. | Les bases bibliographiques demandent qui envoie les requêtes. Nexus Scholar envoie cette adresse aux bases bibliographiques, à Unpaywall et aux sites web d'où il télécharge des PDF en libre accès. | تسأل قواعد البيانات العلمية عمّن يرسل الطلبات. يرسل Nexus Scholar هذا العنوان إلى قواعد البيانات العلمية وإلى Unpaywall وإلى المواقع التي ينزّل منها ملفات PDF مفتوحة الوصول. |
| `settings.email.required` | Needed before any search | Nécessaire avant toute recherche | لازم قبل أي بحث |
| `settings.email.save` | Save | Enregistrer | حفظ |
| `settings.email.remove` | Remove | Retirer | إزالة |
| `settings.email.saved` | E-mail address saved. | Adresse e-mail enregistrée. | حُفظ عنوان البريد. |
| `settings.email.removed` | E-mail address removed. | Adresse e-mail retirée. | أُزيل عنوان البريد. |
| `settings.keys.heading` | Keys | Clés | المفاتيح |
| `settings.keys.where` | Keys are kept in {where} and are never shown again. | Les clés sont conservées dans {where} et ne sont plus jamais affichées. | تُحفظ المفاتيح في {where} ولا تُعرض مرة أخرى أبدًا. |
| `settings.keys.group.databases` | Literature databases | Bases bibliographiques | قواعد البيانات العلمية |
| `settings.keys.group.ai` | AI drafts (optional) | Brouillons par IA (facultatif) | مسودات الذكاء الاصطناعي (اختياري) |
| `settings.keys.group.aiHelp` | Only for drafts the app asks an AI for; the provider charges you. | Uniquement pour les brouillons que l'application demande à une IA ; le fournisseur vous facture. | فقط للمسودات التي يطلبها التطبيق من الذكاء الاصطناعي؛ ويحاسبك المزوّد عليها. |
| `settings.key.openalex.label` | OpenAlex key | Clé OpenAlex | مفتاح OpenAlex |
| `settings.key.openalex.help` | Needed to search OpenAlex; free from openalex.org. | Nécessaire pour chercher dans OpenAlex ; gratuite sur openalex.org. | لازم للبحث في OpenAlex؛ مجاني من openalex.org. |
| `settings.key.semanticscholar.label` | Semantic Scholar key | Clé Semantic Scholar | مفتاح Semantic Scholar |
| `settings.key.semanticscholar.help` | Optional. Without it Semantic Scholar answers from a shared pool. | Facultative. Sans elle, Semantic Scholar répond depuis un lot partagé. | اختياري. من دونه يجيب Semantic Scholar من حصة مشتركة. |
| `settings.key.anthropic.label` | Anthropic key | Clé Anthropic | مفتاح Anthropic |
| `settings.key.openai_compatible.label` | OpenAI-compatible key | Clé compatible OpenAI | مفتاح متوافق مع OpenAI |
| `settings.key.gemini.label` | Google Gemini key | Clé Google Gemini | مفتاح Google Gemini |
| `settings.key.set` | Set | Définie | مضبوط |
| `settings.key.notSet` | Not set | Non définie | غير مضبوط |
| `settings.key.field` | Paste the key | Collez la clé | الصق المفتاح |
| `settings.key.save` | Save key | Enregistrer la clé | حفظ المفتاح |
| `settings.key.replace` | Replace | Remplacer | استبدال |
| `settings.key.remove` | Remove | Retirer | إزالة |
| `settings.key.cancel` | Cancel | Annuler | إلغاء |
| `settings.key.removeNote` | Remove it at the provider too if you no longer want it valid. | Retirez-la aussi chez le fournisseur si vous ne voulez plus qu'elle soit valide. | أزِله لدى المزوّد أيضًا إن لم تعد تريده صالحًا. |
| `settings.key.saved` | {label} saved. | {label} enregistrée. | حُفظ {label}. |
| `settings.key.removed` | {label} removed. | {label} retirée. | أُزيل {label}. |
| `settings.store.keychain` | the system keychain | le trousseau du système | سلسلة مفاتيح النظام |
| `settings.store.keychain.windows` | Windows Credential Manager | le Gestionnaire d'identification Windows | مدير بيانات اعتماد Windows |
| `settings.store.keychain.macos` | the macOS Keychain | le Trousseau d'accès macOS | سلسلة مفاتيح macOS |
| `settings.store.keychain.linux` | the desktop keyring | le trousseau de session | حافظة مفاتيح سطح المكتب |
| `settings.store.file` | a file only you can read ({path}) | un fichier que vous seul pouvez lire ({path}) | ملف لا يقرؤه غيرك ({path}) |
| `settings.store.none` | This computer has no keychain Nexus Scholar can use. When you save a key it will ask before keeping it in a file. | Cet ordinateur n'a pas de trousseau utilisable par Nexus Scholar. Quand vous enregistrerez une clé, il demandera avant de la garder dans un fichier. | لا تملك هذه الحاسبة سلسلة مفاتيح يستطيع Nexus Scholar استخدامها. عند حفظ مفتاح سيسألك قبل حفظه في ملف. |
| `settings.keychain.ask` | Your computer has no keychain Nexus Scholar can use. Keep the keys in a file only you can read? {path} | Votre ordinateur n'a pas de trousseau que Nexus Scholar puisse utiliser. Garder les clés dans un fichier que vous seul pouvez lire ? {path} | ليس في حاسوبك سلسلة مفاتيح يستطيع Nexus Scholar استخدامها. هل تُحفظ المفاتيح في ملف لا يقرؤه غيرك؟ {path} |
| `settings.keychain.yes` | Keep the key in that file | Garder la clé dans ce fichier | احفظ المفتاح في ذلك الملف |
| `settings.keychain.no` | Do not save | Ne pas enregistrer | لا تحفظ |
| `settings.source.environment` | Set in the environment ({name}) | Défini dans l'environnement ({name}) | مضبوط في بيئة التشغيل ({name}) |
| `settings.source.env_file` | Set in the .env file | Défini dans le fichier .env | مضبوط في ملف ‎.env‎ |
| `settings.source.settings` | Saved in your settings | Enregistré dans vos réglages | محفوظ في إعداداتك |
| `settings.source.keychain` | Kept in the system keychain | Conservée dans le trousseau du système | محفوظ في سلسلة مفاتيح النظام |
| `settings.source.file` | Kept in {path} | Conservée dans {path} | محفوظ في {path} |
| `settings.source.flag` | Set when the app was started (--root) | Défini au démarrage de l'application (--root) | مضبوط عند تشغيل التطبيق (‎--root‎) |
| `settings.source.default` | Default location | Emplacement par défaut | الموضع الافتراضي |
| `settings.elsewhere` | This value is set outside the screen, so it cannot be changed here. Change it where it is set, then reload. | Cette valeur est définie hors de l'écran ; elle ne peut pas être modifiée ici. Modifiez-la là où elle est définie, puis rechargez. | هذه القيمة مضبوطة خارج الشاشة فلا يمكن تغييرها هنا. غيّرها حيث ضُبطت ثم أعد التحميل. |
| `settings.folder.heading` | Where your reviews are kept | Où sont conservées vos revues | مكان حفظ مراجعاتك |
| `settings.folder.help` | Each review is one folder under this one. Changing it restarts Nexus Scholar on the new folder; this page reloads by itself. | Chaque revue est un dossier placé sous celui-ci. Le changer redémarre Nexus Scholar sur le nouveau dossier ; cette page se recharge toute seule. | كل مراجعة مجلد داخل هذا المجلد. تغييره يعيد تشغيل Nexus Scholar على المجلد الجديد، وتُعاد تحميل هذه الصفحة تلقائيًا. |
| `settings.folder.change` | Change… | Changer… | تغيير… |
| `settings.folder.dialogOpen` | A folder window is open on your computer. Choose the folder there. | Une fenêtre de dossier est ouverte sur votre ordinateur. Choisissez le dossier dedans. | نافذة اختيار مجلد مفتوحة على حاسوبك. اختر المجلد منها. |
| `settings.folder.whereDialog` | The folder window opens on the computer that runs Nexus Scholar. | La fenêtre de dossier s'ouvre sur l'ordinateur qui exécute Nexus Scholar. | تُفتح نافذة المجلد على الحاسوب الذي يشغّل Nexus Scholar. |
| `settings.folder.restarting` | Moving to {path}… | Passage au dossier {path}… | الانتقال إلى {path}… |
| `settings.setup.done` | Done | Terminé | تم |
| `settings.setup.later` | Later | Plus tard | لاحقًا |
| `settings.setup.doneNeedsEmail` | Done is available once your e-mail address is saved. | « Terminé » est disponible une fois votre adresse e-mail enregistrée. | يتوفر «تم» بعد حفظ عنوان بريدك. |
| `settings.saving` | Saving… | Enregistrement… | جارٍ الحفظ… |
| `settings.loading` | Loading your settings… | Chargement de vos réglages… | جارٍ تحميل إعداداتك… |
| `settings.liveAsOf` | As of {time} | État au {time} | حتى {time} |
| `settings.phone.desktopOnly` | Settings are changed on the computer that runs Nexus Scholar, because a key or a folder is chosen there. | Les réglages se changent sur l'ordinateur qui exécute Nexus Scholar, car la clé ou le dossier se choisit là. | تُغيَّر الإعدادات على الحاسوب الذي يشغّل Nexus Scholar، لأن المفتاح أو المجلد يُختار هناك. |
| `settings.refusal.SETTING_INVALID.email` | That does not look like an e-mail address. Check it and save again. Nothing was sent. | Cela ne ressemble pas à une adresse e-mail. Vérifiez-la et enregistrez de nouveau. Rien n'a été envoyé. | لا يبدو هذا عنوان بريد إلكتروني. تحقّق منه واحفظ من جديد. لم يُرسل شيء. |
| `settings.refusal.SETTING_INVALID.key` | That key is empty or too long. Paste it again. | Cette clé est vide ou trop longue. Collez-la de nouveau. | المفتاح فارغ أو طويل جدًا. الصقه من جديد. |
| `settings.refusal.SETTING_SET_ELSEWHERE` | = `settings.elsewhere` | = `settings.elsewhere` | = `settings.elsewhere` |
| `settings.refusal.FOLDER_DIALOG_UNAVAILABLE` | Nexus Scholar cannot open a folder window because this computer has no desktop for it. {hint} | Nexus Scholar ne peut pas ouvrir de fenêtre de dossier : cet ordinateur n'a pas de bureau pour cela. {hint} | لا يستطيع Nexus Scholar فتح نافذة مجلد لأن هذا الحاسوب لا يملك سطح مكتب لذلك. {hint} |
| `settings.refusal.FOLDER_DIALOG_UNAVAILABLE.hint` (terminal start only) | Start the app with --root <folder>, or set NEXUS_WORKSPACES_ROOT. | Lancez l'application avec --root <dossier>, ou définissez NEXUS_WORKSPACES_ROOT. | شغّل التطبيق بالخيار ‎--root <المجلد>‎ أو اضبط NEXUS_WORKSPACES_ROOT. |
| `settings.refusal.RESTART_UNSUPPORTED` | This copy of Nexus Scholar cannot restart itself. Stop it and start it again on the folder you want. | Cette copie de Nexus Scholar ne peut pas redémarrer seule. Arrêtez-la et relancez-la sur le dossier voulu. | لا تستطيع هذه النسخة من Nexus Scholar إعادة تشغيل نفسها. أوقفها وشغّلها من جديد على المجلد الذي تريده. |
| `settings.refusal.WORKSPACE_ROOT_UNAVAILABLE` | reuses `workspaces.refusal.WORKSPACE_ROOT_UNAVAILABLE` | (same key) | (same key) |

Strings that are not keys of this table and are reused: `workspaces.busy.*`, `workspaces.refusal.*`, the engine-unreachable card and the guard cards come from `lib/screening-states.ts`. The labels `{label}` in the announcements are the key rows' own labels.

The state cards that point here (see Dependencies) keep their codes and roles (`blocked`) and change their copy: the card for `MAILTO_NOT_SET`, `installed.MAILTO_NOT_SET` and `installed.inception.MAILTO_NOT_SET` now says "A search needs a contact e-mail address for the literature databases. Add it in Settings." with the action "Open Settings" (`state.settingsLink`); `OPENALEX_KEY_NOT_SET` says "OpenAlex needs a free API key. Add it in Settings, or leave OpenAlex out of the run."; `PROVIDER_KEY_MISSING` says "No key for this provider. Add one in Settings. Nothing was sent." (fr and ar by the implementer, with the same keys as the existing entries).

## Accessibility
- **Landmarks and headings.** One `main` (the shell's), one h1 (the title changes between setup and settings), each card an h2 in a `section` with `aria-labelledby`, key groups h3. The page `<title>` follows the h1.
- **A label for every field.** The e-mail field and each key field have a visible `<label>` and `aria-describedby` for the help sentence and the source line; the Set/Not set state is text in the row, read with the label ("OpenAlex key, Set").
- **Key fields**: `type="password"`, `autocomplete="off"`, `autocapitalize="off"`, `spellcheck="false"`, a distinct `name` that a password manager will not fill, and **no reveal button, no copy button**. The value is dropped from React state on send; the page never writes a key to the URL, to `localStorage`, to a log, or to the DOM after saving. The e-mail field is `type="email"` with `autocomplete="email"`.
- **Announce each save.** One visually hidden `role="status"` region (`aria-live="polite"`) is present from load; after each write it announces the result in words ("OpenAlex key saved.", "E-mail address removed.", "Moving to {path}…"). A refusal is `role="alert"` inside its row (the code printed in `font-mono`), so it is read at once. Announcements are not repeated by a refetch.
- **Status never rests on colour.** "Set" (include role) and "Not set" (unclear role) are text with an icon; the source line is text. "Set in the environment" is text, and the missing edit control is explained by that sentence, not by a greyed button alone. Buttons that cannot be pressed carry `aria-disabled` and the reason in a described-by note (Done needs the e-mail; offline).
- **Contrast pairs from the tokens** (`docs/ux/brand/tokens.json`), light and dark: `ink` on `leaf` and on `ground`; `ink-muted` on `leaf` for help text; `brand` on `leaf` for the secondary buttons and links; the **Done** brand fill with its on-brand text; role words on `leaf` (`include`, `unclear`, `blocked` as text colour only, `blocked` never as a fill behind text). The focus ring is the `focus` token and is never clipped; no sticky element covers a focused control (the page has none).
- **Touch and pointer.** Buttons and fields ≥ 44 px (`min-h-11`).
- **RTL (ar).** The layout, the buttons' order and the arrows mirror; the e-mail address, paths, `SCHOLAR_*` names, `--root`, the refusal codes and times are `dir="ltr"` inside `bdi` with Latin digits. Source lines that embed a path or a name keep the path LTR inside the Arabic sentence.
- **Motion.** No animation beyond the existing skeleton pulse, which respects `prefers-reduced-motion`.

## Acceptance tests
Browser suites were removed on 2026-11-23 (`docs/decisions.md`, H-test-diet), so there is no Playwright file here; M13's "browser test in both themes" is read as the vitest and in-process axe pass below plus a by-hand look (answered 2026-11-24, Open questions 1). Vitest under `apps/research-ui/tests/` (each against a stateful fake of `settings-v1` in `tests/fixtures/`):
- `settings.i18n.test.ts`: every `settings.*` key exists in en, fr and ar, the key rows cover exactly `openalex`, `semanticscholar`, `anthropic`, `openai_compatible`, `gemini`, and no literal `aria-label`, `title`, `alt` or `placeholder` is used (N9 guard).
- `settings.screen.test.tsx`: default settings mode (h1 "Settings", three cards in order, no brand button); first run (`?setup=1`, h1 "Set up Nexus Scholar", focus on the e-mail field, **Done** disabled with its note until an e-mail is saved, then enabled); `?setup=1` with `setup` `done` renders settings mode; the empty state prints "Not set" for every key and the default folder with "Default location".
- `settings.email.test.tsx`: Save sends `PUT /contact-email`; an empty value removes; `SETTING_INVALID` keeps the text and focus and prints the sentence with `role="alert"`; the success announces "E-mail address saved." in the status region.
- `settings.keys.test.tsx`: a saved key shows "Set" with Replace and Remove and **no** field and no value anywhere in the DOM, props or fetch bodies after the save; the password field has `type="password"`, `autocomplete="off"` and no reveal control; the typed value is gone from state when the request is sent; Replace moves focus to the field and Escape returns it; Remove sends the remove route; every response in the fake that contains a key's value fails the test (the screen-side half of "a key saved on the screen is never returned by any route").
- `settings.keychain.test.tsx`: `KEYCHAIN_UNAVAILABLE` (with `details.file`) shows the sentence of answer 6 with that path and two buttons; "Keep the key in that file" resends with `use_file: true` and the same value, then the row says "Kept in {file}"; "Do not save" drops the value and sends nothing; `key_store.kind` `none` prints `settings.store.none` before any save.
- `settings.elsewhere.test.tsx`: rows with `source` `environment` and `env_file` print "Set in the environment (SCHOLAR_MAILTO)" and "Set in the .env file", offer no field, Replace, Remove or Change…; `SETTING_SET_ELSEWHERE` after a race re-reads the row; a folder with `flag` or `environment` offers no Change…; **Done** is enabled when the e-mail is set elsewhere.
- `settings.folder.test.tsx`: Change… posts `/folder/choose`; `{chosen: null}` changes nothing and prints no message; a chosen path shows "Moving to {path}…", polls `GET /settings` until `workspaces_root.path` matches (the old engine failing in between is not an error), then reloads keeping `?setup=1`; the wait timing out shows `ENGINE_UNREACHABLE`; `FOLDER_DIALOG_UNAVAILABLE`, `WORKSPACE_ROOT_UNAVAILABLE` and `RESTART_UNSUPPORTED` print their sentences (the `--root` hint only when `started_as` is `terminal`).
- `settings.setup.test.tsx`: Done sends `{choice: "done"}` and Later `{choice: "later"}`, both go to Workspaces; the engine's `setup` decides, not the URL; `started_as` `terminal` never causes the entry redirect (the redirect lives in the launch link, and the test pins that the page itself does not redirect).
- `settings.states.test.tsx`: loading skeleton with `aria-busy` and no "Not set"; `ENGINE_UNREACHABLE` keeps the last values with "As of {time}" and disables every button; `TOKEN_SCOPE_REFUSED` renders only the desktop pointer; `HOST_REFUSED`, `TOKEN_REQUIRED` and `ACTION_ORIGIN_REFUSED` render the guard cards; the demonstration marker is absent (`isLiveOnlyPath("/settings")`); the NextStepBar is not rendered.
- `settings.a11y.test.tsx` (added to the in-process axe run, `accessibility-in-process.test.tsx`): no axe violation in default, first run, keychain confirmation and refusal states, in light and dark token sets, and in `ar` with `dir="rtl"`; the status region exists and announces once per write; the 44 px classes are present; paths and addresses carry `dir="ltr"`.
- Existing tests extended: `workspaces.list.test.tsx` (the Settings link is present with the right href, is secondary, and the screen still has exactly one brand button); the state-card tests for `MAILTO_NOT_SET`, `OPENALEX_KEY_NOT_SET`, `inception.MAILTO_NOT_SET` and `PROVIDER_KEY_MISSING` (installed and terminal scopes: the link to Settings, no `.env` step, no "Not available in this version").

Python under `tests/console/`:
- `test_settings_api.py`: `GET /settings` has the `settings-v1` shape and, across every response of every route in this file, never contains a key's value (the definition-of-done test); each `source` value is reported for the case that produces it; the environment beats `.env`, which beats the settings file and the keychain; a value set in the environment returns `SETTING_SET_ELSEWHERE` 409 on a write; `SETTING_INVALID` 422 for a malformed address and for an empty or over-long key, and nothing is sent to test an address; `KEYCHAIN_UNAVAILABLE` 409 carries `details.file` and writes nothing, and the resend with `use_file: true` writes a file only the user can read; the remove route clears the key; `setup` records `done` and `later` and `later` survives a restart; the routes are workspace-free (200 with no workspace open) and a phone token gets `TOKEN_SCOPE_REFUSED`; `FOLDER_DIALOG_UNAVAILABLE` with no desktop, `WORKSPACE_ROOT_UNAVAILABLE` for an unwritable folder, `SETTING_SET_ELSEWHERE` under `--root`, `RESTART_UNSUPPORTED` outside `nexus-scholar ui`; a cancelled dialog returns `{chosen: null}` and changes nothing.
- `test_settings_discovery.py`: a search refused with `MAILTO_NOT_SET` succeeds after `PUT /contact-email`, with no restart (the Part B definition of done); an environment variable still wins over a saved value.
- `tests/console/test_console_refusals.py` extended for `SETTING_INVALID`, `SETTING_SET_ELSEWHERE`, `KEYCHAIN_UNAVAILABLE`, `FOLDER_DIALOG_UNAVAILABLE`.
- `tests/console/test_control_window.py`: the Settings button opens `/settings/` with a fresh launch link (extends the Part A control-window tests).

## Dependencies (amendments made by the work that builds this screen)
- `apps/research-ui/lib/screening-states.ts` and `components/screening-state-card.tsx`: add the action `"settings"` to `StateAction` (`screening-states.ts:14-33`; a link to `/[locale]/settings/` carrying `?console=`), and change, in the installed scope (`INSTALLED_SCOPE`, `:1682`; `installedStateKey`, `:1685`) and in the terminal scope, the cards for `MAILTO_NOT_SET` (`:994`, `:1407`), `OPENALEX_KEY_NOT_SET` (`:1004`, `:1417`), `inception.MAILTO_NOT_SET` (`:1464`, installed `:1427`) and `PROVIDER_KEY_MISSING` (`:543`, installed `:1446`) from the `.env` step or "Not available in this version" to a link action "Open Settings". The commands `SCHOLAR_MAILTO=<your email>` and `SCHOLAR_OPENALEX_KEY=<your key>` stay as a second line on the terminal scope only (a terminal user can still use them). `installed.DRIVER_UNAVAILABLE` (`:1455`) mentions "Settings for providers come with the app's settings screen"; it is reworded to say a base URL is not a setting of this version (no base-URL setting, answer 5).
- `components/workspaces-screen.tsx`: a "Settings" secondary link beside "New review" (`:388-394`); `docs/ux/phase2-screening/final/00-workspaces.md` gets an addendum like its M4b one ("There is no settings screen" is superseded for the folder).
- `components/app-shell.tsx` / `SiteHeader`: a "Settings" link on every route. `04-next-step.md` is not edited (the bar is absent on `/settings`).
- `src/scholar_harness/console/control_window.py:238-246`: the "Settings" button (✗ M13 Part B).
- `src/scholar_harness/console/serve.py:64, :104`: the six routes are workspace-free and none is in `_PHONE_ROUTES`.
- `src/scholar_agent/keys.py:22-27, :128, :139` and `src/scholar_search/config.py:9-38`: read and write the settings file and the key store, after the environment and `.env`.
- The launch link of the installed start opens `/[locale]/settings/?setup=1` when `started_as` is `installed` and `setup` is `pending` (engine side, ✗ M13 Part B).
- Parts C (connect an AI assistant) and D (update choice) each amend this spec when they add a row.

## Open questions
None. Both were answered by the researcher on 2026-11-24 in the coordinator session, each as proposed:
1. **The screen check** ("Component tests + hand check"): vitest component tests against a fake engine, the in-process accessibility pass in light, dark and Arabic, and before the pull request a check by hand of the real installed start in both themes at phone and desktop width. No browser test comes back. *Not chosen:* one real-browser test for this screen.
2. **A folder change when a restart is not allowed** ("Refuse, save nothing"): the route refuses before the folder dialog opens, `WORKSPACE_BUSY` (409, the Workspaces screen's code and copy, with its "Go to screening home" link) while an agent run or an approval is in progress, `RESTART_UNSUPPORTED` when the engine was started by `serve`; nothing is saved. *Not chosen:* save the folder and apply it at the next start.
