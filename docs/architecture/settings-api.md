# Settings API (M13 Part B)

Status: **BUILT on `dev/m13/part-b-settings`** (2026-11-24; record [`docs/roadmap/milestones/M13-part-b.md`](../roadmap/milestones/M13-part-b.md)). Screen: [`docs/ux/shared/final/05-settings.md`](../ux/shared/final/05-settings.md). Same conventions as [`screening-api-contract.md`](screening-api-contract.md) and [`workspaces-api.md`](workspaces-api.md): JSON over the console's `/api/v1`, refusals as `{"detail": {"code", "message", "details"?}}`, desktop only (no route is in `_PHONE_ROUTES`), writes from the browser only from the app's own origin (`console/browser.py` allowlist).

## 1. What is stored, and where

| Value | Stored in | Read by |
| :-- | :-- | :-- |
| Contact e-mail | `settings.json` → `contact_email` | the search settings (`scholar_search/config.py`, field `mailto`), through them the PDF look-up (`scholar_pdf/config.py:contact_email`) and the MCP server |
| Reviews folder | `settings.json` → `workspaces_root` | `workspace/catalog.py:resolve_root` (source `settings`) |
| Setup choice | `settings.json` → `setup` (`done` or `later`; absent = `pending`) | the launcher's first page (`launcher.py:landing`) |
| OpenAlex and Semantic Scholar keys | the system keychain, service `nexus-scholar`, names `openalex` and `semanticscholar` | the search settings (fields `openalex_key`, `s2_key`) |
| AI keys (Anthropic, OpenAI-compatible, Gemini) | the system keychain, service `nexus-scholar`, names `anthropic`, `openai_compatible`, `gemini` (the names `nexus-scholar keys set` already uses) | `scholar_agent/keys.py:resolve_key`; the MCP server at start (`server.py:_apply_keychain_keys`) |
| Any key, where the keychain fails | `keys.json` beside `settings.json`, after the user confirmed it | the same readers, after the keychain |

The settings folder is `%APPDATA%\Nexus Scholar` on Windows, `~/Library/Application Support/Nexus Scholar` on macOS and `~/.config/nexus-scholar` on Linux (`scholar_search/user_settings.py:settings_dir`, shared with the installed app's `desktop.app_folders`). `NEXUS_SETTINGS_DIR` points it elsewhere; `NEXUS_APP_HOME` makes it `<home>/settings`. Both files are replaced atomically and created readable by this user only (`0600` on POSIX).

**Precedence** (the researcher's answer 2, 2026-11-24): an environment variable, then `.env` in the engine's current folder, then this store. The search settings get the store as pydantic's lowest-precedence source (`config.py:UserSettingsSource`). AI keys: the environment, then the keychain, then the file; the console does not read AI keys from `.env`. The reviews folder: `--root`, then `NEXUS_WORKSPACES_ROOT`, then the store, then the default: `<NEXUS_APP_HOME>/workspaces` when `NEXUS_APP_HOME` is set (item 21), else `~/Documents/Nexus Scholar/workspaces`.

**No restart for a value.** A saved e-mail or key is read again into the one shared search-settings instance (`config.py:reload_settings`), so the next request uses it. A new reviews folder restarts the server in place on it (`launcher.py:request_root`), as Open does.

## 2. Routes

| Route | Purpose | Request → response |
| :-- | :-- | :-- |
| `GET /api/v1/settings` | read | → `{shape: "settings-v1", started_as: "installed"\|"terminal"\|null, setup: "pending"\|"done"\|"later", settings_folder, contact_email: {value, source}, keys: {<name>: {set, source, variable}}, workspaces_root: {path, source}, key_store: {kind: "keychain"\|"file"\|"none", file}}`. `source` is `environment`, `env_file`, `settings`, `keychain`, `file`, `flag`, `default` or null. **A key's value is never in any response.** |
| `PUT /api/v1/settings/contact-email` | save the e-mail | `{value}` (empty removes it) → the settings. `SETTING_INVALID` 422 (not an e-mail address; nothing is sent to test it); `SETTING_SET_ELSEWHERE` 409 |
| `PUT /api/v1/settings/keys/{name}` | save a key | `{value, use_file?}` → the settings. `KEYCHAIN_UNAVAILABLE` 409 with `details.file` (resend with `use_file: true` after the user's yes); `SETTING_SET_ELSEWHERE` 409; `SETTING_INVALID` 422 (not one line of printable characters); an unknown name 404 |
| `POST /api/v1/settings/keys/{name}/remove` | remove a key | → the settings (from the keychain and the file) |
| `POST /api/v1/settings/setup` | finish or put off setup | `{choice: "done"\|"later"}` → the settings |
| `POST /api/v1/settings/folder/choose` | choose the reviews folder | `{}` → the engine opens the system's folder dialog on this computer's desktop (`console/folder_dialog.py`, a child process) and waits. `{chosen: null, restarting: false}` when cancelled; `202 {chosen, restarting: true}` when a folder was chosen: saved, then the server restarts on it. Refusals, all before the dialog opens and before anything is saved: `SETTING_SET_ELSEWHERE` 409 (`--root` or `NEXUS_WORKSPACES_ROOT`), `RESTART_UNSUPPORTED` 501 (`serve`), `WORKSPACE_BUSY` 409 (an agent run or an approval). After the dialog: `FOLDER_DIALOG_UNAVAILABLE` 409, `WORKSPACE_ROOT_UNAVAILABLE` 409 (the folder cannot be written) |

The routes answer with no workspace open (first run) and while a workspace's copy is being saved (`serve.py:_workspace_free`, `_format_blocked`). The refusal codes are in `console/refusals.py` and the screening API contract §7.
