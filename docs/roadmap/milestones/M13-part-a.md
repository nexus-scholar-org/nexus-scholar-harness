# M13 Part A: the launcher for an installed app

Status: **BUILT on `dev/m13/part-a-launcher` (from `main` `cc0e8fa1`, `main` `0bcefdd3` merged in); items 1 to 4 accepted by the researcher on 2026-11-24, in a pull request; the engine start path only (see "Not in this branch"). Lane RELEASE.** The researcher gave the go on 2026-11-24 ("Start Part A and the workspace format version"), relayed by the coordinator session "Nexus Scholar parent work". Specification: `docs/roadmap/milestones/M13-installers.md` §4.1, §4.2, §5.2 Part A and §8 (trial build). Decisions: `docs/decisions.md`, entry "2026-11-24 — M13 Part A".

## What a start from an icon does now

`nexus-scholar-app` (the new `[project.gui-scripts]` entry point: `nexus-scholar-app.exe` on Windows, no console window), `pythonw -m scholar_harness.console.desktop`, and later the bundle's windowed program start the engine with no terminal (`src/scholar_harness/console/desktop.py`):

1. **Output goes to a log file before anything prints.** One file per launch in the user's log folder, the last five kept, none above 5 MB. It names the version, the system, the folders, the workspaces folder and the port; e-mail addresses, launch codes, `Bearer` values and key-like strings are masked. Standard output and error are the log, so nothing is written to a missing console.
2. **The user's own folders (spec §4.1).** Settings `%APPDATA%\Nexus Scholar` (Linux `~/.config/nexus-scholar`, macOS `~/Library/Application Support/Nexus Scholar`), logs `%LOCALAPPDATA%\Nexus Scholar\Logs`, cache `%LOCALAPPDATA%\Nexus Scholar\Cache`. `NEXUS_APP_HOME` puts all three under one folder (tests, CI). The engine runs in the settings folder, so the search settings' `.env` is read from there, never from the program folder or wherever the icon started; the search cache (`SCHOLAR_CACHE_DIR`) and the recon cache (`NEXUS_RECON_ROOT`) default to the cache folder. A variable already set still wins. No change to `scholar_search/config.py` was needed; reading the e-mail and keys from a settings file is Part B.
3. **One engine per user.** The engine holds a lock on `engine.lock` in the settings folder for its whole life (the system drops it when the process ends, also on a crash) and, once its server answers, writes `engine.json`: its port and a secret made for this launch (`console/instance.py`). A second start cannot take the lock, asks the running engine for a fresh one-time link (`POST /instance/launch-link` with the secret), opens the browser on it and exits; no second server starts. `--stop` asks the engine to stop (`POST /instance/stop`). The two routes check their own secret, never the console token, and refuse any request carrying a browser's `Origin` or `Sec-Fetch-Site` header; they are not in the browser allowlist.
4. **A failure says what to do.** A failure at start is written to the log with its traceback and shown in a small message window: "Nexus Scholar could not start. The details are in the log file: <path> …". Also named: an incomplete install (no screens), a workspaces folder that cannot be written, an engine that holds the lock but does not answer.

`nexus-scholar ui` in a terminal is unchanged: its folder, its `.env`, its output, and several engines side by side (tests, the release walk and the researcher's own engine rely on that).

## The three known faults

| # | Fault | Cause | Fix | Test that failed on `cc0e8fa1` |
| :-- | :-- | :-- | :-- | :-- |
| 1 | Release walk 1.1.0b7, fault 1: Workspaces → Open left the engine stopped in the Browser pane | uvicorn's graceful shutdown waits for every open response with no time limit; a page still receiving a response (an event stream, or a body the browser has not finished reading) kept the old server alive, so the new one never started | `timeout_graceful_shutdown=3` (`RESTART_GRACE_SECONDS`, `launcher.py`): after 3 s the open responses are cancelled and the restart goes on | `tests/test_ui_launcher.py::test_open_restarts_while_the_browser_holds_an_event_stream_open` (slow). On `cc0e8fa1` the same steps as a script: "no restart within 20 s"; after the fix 3.9 s |
| 2 | Trial build fault 3: the approval window could not start inside a bundle | `code_window._command()` started `sys.executable -I code_window.py`; in a bundle `sys.executable` is the app (`No such option: -I`) | frozen, the window starts as the app with `--approval-window`; `desktop.main` and `cli.main` hand that flag to `code_window.run_child()` before anything else loads | `tests/console/test_desktop_approval_window.py` (three tests) |
| 3 | Trial build fault 4: with no console the engine exited at start | `uvicorn.Config` configures logging on `sys.stderr`, which is `None` with no console: `ValueError: Unable to configure formatter 'default'` | with no standard output or error, uvicorn gets `log_config=None`; the installed start sends both streams to the log file first anyway | `tests/test_ui_launcher.py::test_the_server_starts_with_no_standard_output_or_error` (failed with that `ValueError`) |

**Seen in the Browser pane (2026-11-23, the desktop app's Chromium).** An engine started with `pythonw` from `C:\Windows` (no console), a temporary home, two test workspaces and the installed 1.1.0b7 screens. Open from Workspaces twice: first Trial Review A, then Trial Review B with an event stream held open by the page. Both came back on the new workspace's Screening Home. The log shows that the **first** Open, before any stream of mine was open, also hit the 3-second limit ("Cancel 1 running task(s), timeout graceful shutdown exceeded"). So the page itself held a response open, which is fault 1's cause. Before the fix, that Open would have waited forever.

## Definition of done (this branch)

| Item (spec §5.2 Part A) | Evidence |
| :-- | :-- |
| A second start opens a new launch link from the first engine and starts no second server | `test_a_second_start_opens_a_link_from_the_first_engine_and_stop_frees_the_port` (a real first engine; the link sets the session cookie on it; no `Launcher` built) |
| Stop ends the process and frees the port | the same test (`--stop`, thread ends, port binds); by hand with `pythonw … --stop`: exit 0, engine gone in 5.4 s, port 8770 free, `engine.json` removed |
| A failure at start leaves a log naming the error and shows the message | `test_a_failure_at_start_is_logged_and_shown_with_no_standard_output`; `test_an_incomplete_install_is_named`; `test_an_unwritable_workspaces_folder_is_named`; `test_a_held_lock_with_no_answer_says_so` |
| Nothing is printed to a missing standard output | the same failure test runs with `sys.stdout` and `sys.stderr` set to `None`; `test_the_server_starts_with_no_standard_output_or_error` |
| The per-user folders; the working folder is the settings folder | `test_the_user_folders_on_each_system`; `test_the_engine_runs_in_the_settings_folder_with_the_user_cache`; `test_an_environment_variable_still_wins_over_the_user_cache` |
| The log: one per launch, five kept, 5 MB cap, nothing sensitive | `test_the_log_keeps_five_files_masks_and_stops_at_its_cap` |
| The instance routes are not reachable from a page | `test_the_instance_routes_refuse_a_browser_and_a_wrong_secret` |
| The approval window works inside a bundle | the three tests above, and a windowed PyInstaller probe of `code_window.py` in a throw-away environment: frozen, no standard output in the parent, the child started as the app with the flag (no `-I`), "ready" received, the window closed itself when the test codes expired |
| No console window appears (by hand on Windows) | `nexus-scholar-app.exe --no-browser` from a `uv` install, started from `C:\Windows`: answers after 5.2 s, `/healthz` 200, the process has no visible window; `nexus-scholar-app.exe --stop` exit 0, engine gone, port free, `engine.json` removed. Also `pythonw -m scholar_harness.console.desktop --no-browser`: `engine.json` after 5.9 s, the log complete |
| With no settings, the first page is the setup screen | **not in this branch**: the setup screen is Part B |

## Independent review (milestone-reviewer), round 1: CHANGES, repaired

| # | Finding | Repair | Test |
| :-- | :-- | :-- | :-- |
| P1 | Approval codes went into the installed app's log file in plain text (the pairing routes `print()` them; standard output is the log). That breaks the pairing rule "never stored, never logged", and a process with file access could approve its own batch | the installed start builds the app with `codes_on_terminal=False`; the routes print nothing then, the codes go to the window only, and with no window both refuse `APPROVAL_WINDOW_UNAVAILABLE` (409, new console code: `refusals.py`, contract §7, app copy in three languages) | `tests/console/test_approve_all.py`: `test_installed_app_the_codes_never_reach_its_log_file`, `test_installed_app_without_a_window_refuses_instead_of_hiding_the_codes` (both routes), `test_the_installed_start_runs_its_engine_without_a_terminal_for_codes`; `test_the_engine_runs_in_the_settings_folder_with_the_user_cache` checks the flag |
| P2 | `engine.json` was published only if the server started within 10 s; a failed publish also stopped the browser from opening | no time limit while not stopping; a failed publish is logged and the browser still opens | `test_a_slow_first_start_is_still_published_and_a_failed_publish_still_opens_the_browser` |
| P3 | `engine.tmp` briefly readable by others on POSIX | created with `os.open(…, 0o600)` | (POSIX; not testable on Windows) |
| P3 | A second start opened any URL the answering port returned | only `http://127.0.0.1:<the port asked>/launch?…` | `test_a_link_to_another_port_is_not_opened` |
| P3 | A log folder that cannot be made escaped with no message | message `LOG_FAILED` | `test_a_log_folder_that_cannot_be_made_still_shows_a_message` |
| P3 | Failure messages were shown while the lock was held; a click just after Stop got "not answering" | lock released before the message; a waiting start takes the lock when it comes free | `test_an_incomplete_install_is_named_after_the_lock_is_freed`, `test_a_start_while_the_engine_is_stopping_goes_on_once_the_lock_is_free` |
| P3 | Decisions: stale "entry point" in the open row; the spec departure of item 5 not named | both corrected | — |
| follow-up | A test left a lock handle open; on POSIX a sixth click could prune the running engine's log | handle released; a log whose process runs is kept | `test_a_running_engines_log_is_not_pruned` (POSIX only, skipped on Windows) |

**Round 2: APPROVE** (f0f26985, code read; the gate was running). Two of its minor notes were repaired after it: the ready-wait thread now ends when the first server returns without starting (`test_the_ready_wait_ends_when_the_first_server_never_started`), and a write of `engine.json` that clashes is tried up to five times (`test_a_publish_that_clashes_once_is_tried_again`). Left as follow-ups: after an `APPROVAL_WINDOW_UNAVAILABLE` refusal the pairing status shows a pending challenge nobody can answer for up to 5 minutes, and the refused begin replaces a code an earlier window may still show (both harmless; voiding the staged records on refusal would be cleaner); one test replaces `time.sleep` for the whole process while it runs.

## Second pull request: the control window and the app's words (2026-11-24)

Status: **BUILT on `dev/m13/part-a-control-window` (from `main` `59f0dca1`), not pushed. Lane RELEASE.** Started on the researcher's go of 2026-11-24 ("Start it"), relayed by the coordinator session. Decisions entry: "2026-11-24 — M13 Part A, second pull request" (items 1 to 4 for the researcher).

### The control window (`src/scholar_harness/console/control_window.py`)

A start from an icon now opens a small window titled "Nexus Scholar" beside the browser:

- **Status line.** "Nexus Scholar is running on this computer. Your reviews are in <folder>." It also says:
  - "Opening your review…" while a small review's copy runs, before the server answers;
  - "Saving a copy of <title> before opening it: x MB of y MB" while a large review's copy runs;
  - the refusal's message when a review is refused;
  - after 60 s with no launch link used, that a security program or a proxy may block 127.0.0.1.
- **Buttons.**
  - **Open in browser**: a new tab with a fresh one-time link.
  - **Stop Nexus Scholar**.
  - "Show the log file" and "Open the settings folder".
  - "Copy the details", shown after an error.
- **Closing the window stops Nexus Scholar**, after the question "Stop Nexus Scholar? Open browser tabs will stop working." When something is in progress, the question names it and the default is to keep running: a copy of a review being saved, an agent run, approval codes waiting, a literature search.
- **A second click on the icon** opens a fresh link (as before) and brings the window to the front.
- **When the engine stops on an error**, the window says so and keeps the log and details buttons.
- **With no Tk or no display**, or with `NEXUS_APP_DIALOGS=0`, the start runs headless as in the first pull request.

The engine runs in a background thread and the window on the main thread. `desktop.run_with_window` stops the engine and waits for it however the window closes.

### The app's words for the installed app

The launch link sets a readable cookie, `nexus_started_as`: `installed` from an icon, `terminal` from `nexus-scholar ui`. The screens read it after mount (`useInstalled()`, so the first render matches the static export) and then use the installed wording.

| Where | Terminal start (unchanged) | Installed app |
| :-- | :-- | :-- |
| Contact e-mail and OpenAlex key cards (search, recall, harvest, inception, discovery plan) | put the line in the console's environment or `.env`, restart the console | put the line in `.env` in Nexus Scholar's settings folder (the window's "Open the settings folder"), stop it in its window and start it again |
| The look-up's e-mail refusal (charting) | same | same as above |
| No key for an AI provider | `nexus-scholar keys set <provider>` | "This version of the installed app cannot store a provider key yet" (no command) |
| Provider driver missing | `uv sync --extra ai` | names the missing setting; no command |
| Where the approval codes are (Publish) | the window and the engine's terminal | the window only |
| Approval-code refusals | — | "the code shown on this computer", for both starts |
| Using your own Claude (agent proposals) | `uv run scholar-agent` | "connecting Claude Desktop comes in a later version" |
| Workspaces: after creating a review; the empty list | the `accept-corpus` command; start the app on a folder from the terminal | import on the Import screen; move the folder into the workspaces folder |
| Screening home "Run from the terminal"; inception start's terminal hint | shown | hidden |

All in English, French and Arabic. Left with terminal words: the chase options' "from the terminal", `RESTART_UNSUPPORTED` (the installed app cannot hit it), and the "Not set — set SCHOLAR_OPENALEX_KEY" status labels (decision item 15).

### While a copy of an older review runs (the coordinator's question)

The workspace format check (PR 310) copies an older review before opening it.

- **A large review** (copied in the background) was checked with a real server in `test_while_a_copy_of_an_older_review_runs`:
  - the server answers and workspace routes say `WORKSPACE_PREPARING`;
  - the status line shows the copy and its progress, and the closing question names it;
  - a second start gets a fresh link from the running engine at once;
  - once the copy is done, the status line and the closing question are clear.
  - Stopping during the copy cancels it (the format module removes the partial zip and stamps nothing).
- **A small review** (under 64 MB, copied before the server answers) was reasoned about, not timed:
  - At the first start the window says "Opening your review…". `engine.json` is published only once the server answers, so a second click meanwhile waits, up to 15 s, and then says the engine does not answer.
  - On Open (a restart) the server is down for the length of the copy, and a second click waits the same way.
  - A copy under 64 MB takes seconds, but a slow disk could exceed 15 s. Raising the wait, or publishing before the copy, would be a follow-up if testers meet it.

### Definition of done (second pull request)

| Item | Evidence |
| :-- | :-- |
| The window: status, Open in browser, Stop, closing question with the busy check | `tests/console/test_control_window.py`: status line (copy, refusal, opening, failure), browser-blocked line, busy question, buttons, second start, threaded run and stop, engine error kept, start opens the window when it can; Tk smoke test (built and polled on Windows, skipped without a display) |
| Behaviour while a copy runs | `test_while_a_copy_of_an_older_review_runs` (slow, real server) |
| The app knows how the engine was started | `test_the_launch_link_tells_the_app_how_the_engine_was_started`; `apps/research-ui/tests/installed-copy.test.tsx` (cookie parsing, every installed card in three languages free of terminal words, the cards and the e-mail card after mount, the first render as the static export) |
| By hand on Windows | see Evidence below |

### Independent review (milestone-reviewer), round 1: CHANGES, repaired

| # | Finding | Repair | Test |
| :-- | :-- | :-- | :-- |
| P2 | The "No accepted corpus" card still showed `nexus-scholar accept-corpus …` in the installed app | `installed.SNAPSHOT_NOT_ACCEPTED`: the Import link, no command; the installed cards may carry no terminal command | `installed-copy.test.tsx` (the card list, and no command with terminal words) |
| P2 | The engine's own sentences for a missing session (`TOKEN_REQUIRED`) and a used link (`LAUNCH_CODE_INVALID`) said to start `nexus-scholar ui` | `serve._start_again`: in the installed app they say "click Open in browser in the Nexus Scholar window" | `test_the_launch_link_tells_the_app_how_the_engine_was_started` (both codes, both starts) |
| P2 | The workspaces screen and Publish had no test with the cookie set | cases with and without the cookie | `workspaces.test.tsx` and `screening-publish.test.tsx`, "in the installed app (M13 Part A)" |
| P3 | During a restart the status line could show the last review's copy or refusal | the review being opened wins: "Opening your review…" | `test_the_status_line_names_the_folder_the_copy_and_a_refusal` |
| P3 | The browser hint counted from the window, not from the server's answer | it counts from the first answer | `test_the_status_line_says_the_browser_may_be_blocked_only_after_a_minute_unused` |
| P3 | A stop (`--stop`) while the closing question is open left a call on a destroyed window | the window checks it still exists after the question | — (Tk only) |
| P3 | One test could open a message box on a developer's desktop | it passes a silent `tell` | — |

**Round 2: APPROVE** (d7582968, code read). Its note that the workspaces test looked for a button named "Copy" (the button is "Copy the command", so the check passed either way) is repaired: the test looks for any Copy button, and it fails when the button is shown. Its other note is left: if the engine stops on an error while the closing question is open and the answer is Yes, the window closes without showing the error (the log records it).

**Final gate on d7582968** (selector `pr`, areas console, search, research-ui): `tests/console tests/authority tests/test_ui_launcher.py` 1459 passed, 2 skipped; the search area 572 passed; typecheck pass; lint:ui 76 passed; vitest through the suite lock 119 files, 1369 passed; `git diff --check`, ruff, contract baseline, `select_test_gate --check` pass. The last commit changes one test line (`workspaces.test.tsx`, 17 passed).

Left as follow-ups, as the review listed them (P3):
- A stop during a restart's build can leave a large background copy, already started, to be killed at exit. That copy behaviour comes from PR 310.
- The closing question does not name a charting look-up or a pipeline job.
- The cookie belongs to the host, not the port: a `nexus_started_as=installed` from an earlier launch stays for a later `serve` on 127.0.0.1.
- More words that name a setting without a place: Explore's "OpenAlex refused the request; set SCHOLAR_OPENALEX_KEY", the look-up plan's labels, and the query workbench's "Add it in Settings" (there is no Settings screen yet).
- Tester notes should warn that Windows may save `.env` as `.env.txt` when extensions are hidden.

### A fault found in the browser check, fixed here

On the installed app's first discovery page, the request answered **500**. The search's HTTP cache (hishel) defaults to `.cache/hishel` in the folder the process started in, and it creates that folder without `exist_ok`. The installed engine runs in the settings folder, which has no `.cache` (`FileNotFoundError`, then `FileExistsError` when several search clients were built at once). `scholar_search/http_client.py` already computed `<SCHOLAR_CACHE_DIR>/scholar_cache` but never passed it. The fix creates that folder with `exist_ok` and gives it to hishel as its storage. The same fault reached a terminal start in a folder with no `.cache`. Test: `tests/kits/search/test_http_cache_location.py` (eight clients built at once in a fresh folder): it passes with the fix and fails on `59f0dca1` with the cache made in the starting folder. Effect on terminal users: the cache moves from `.cache/hishel` to `.cache/scholar_cache` (under `SCHOLAR_CACHE_DIR`), so it starts cold once.

### Evidence

| Check | Result |
| :-- | :-- |
| Selector `pr` gate on `e3084062` (areas console, research-ui) | `tests/console tests/authority tests/test_ui_launcher.py`: 1459 passed, 2 skipped; `npm run typecheck` pass; `npm run lint:ui` 76 passed; vitest through the suite lock: 119 files, 1365 passed |
| `git diff --check`, ruff (`scripts/`, `src/` bug rules), contract baseline `--check` | pass, current |
| The search area after the cache fix (selector `pr`, area search) | `tests/kits/search` + identity conformance + discovery, dedup and http-client units + migration + e2e search-screen: 572 passed |
| By hand on Windows: `nexus-scholar-app.exe --no-browser` from `C:\Windows`, temporary home, the UI export of this branch | engine answered in 7 s; a `pythonw` window titled "Nexus Scholar" appeared; `--stop` closed it in 3.9 s, freed port 8770 and removed `engine.json` |
| Browser pane (the desktop app's Chromium), same engine | readable cookie `nexus_started_as=installed` (the session cookie stays HttpOnly); Workspaces: the installed empty-list text; creating a review: the installed next step, no `accept-corpus` command and no Copy button; Discovery plan: the installed contact-email and OpenAlex key cards; no console error from the new code |
| The installed instruction works | a test address put in `.env` in the settings folder, `--stop`, start again: the contact-email card is gone (the OpenAlex card stays: no key) |
| The cache fault | before the fix the plan page answered a 500 (log: `FileNotFoundError` on `.cache\hishel`); after it, no failed request on the page, no `.cache` in the settings folder, the cache under `cache\search\scholar_cache` |

## Not in the first pull request (built in the second, above)

- **The control window** of §4.2: Open in browser, Settings, Stop, the status line and the closing question with the busy check. The instance routes it needs (a fresh link, stop) are here.
- **The app's text** (about 60 lines in three languages that send the user to a terminal, a variable or `.env`), and the engine telling the app how it was started.
- **The message "the browser could not reach Nexus Scholar"**: only the control window can show it.

## Evidence

| Check | Result |
| :-- | :-- |
| Targeted tests (`tests/test_ui_launcher.py`, `tests/console/test_desktop_*.py`) | 22 passed |
| Selector `pr` gate after the review repairs (f0f26985; areas console-screening, console, harness-cli, research-ui; task T-110) | `tests/console tests/authority tests/test_read_store.py tests/test_ui_launcher.py`: 1461 passed, 2 skipped; `tests/cli tests/unit tests/mcp` + parity: 832 passed, 2 skipped; `tests/kits/agent`: 284 passed. **Not run locally:** the research-ui typecheck, lint and vitest (this worktree has no `node_modules`); CI runs them on the one changed UI file (`lib/screening-states.ts`, one new refusal entry) |
| Selector `pr` gate after merging `main` `0bcefdd3` (areas console, harness-cli; task T-110) | `tests/console tests/authority tests/test_ui_launcher.py`: 1438 passed, 1 skipped; `tests/cli tests/unit tests/mcp` + parity + serve: 847 passed, 2 skipped; `tests/kits/agent`: 284 passed (all with `-n 4`) |
| `git diff --check`, `ruff check scripts/`, `ruff check src/ --select F821,…` | pass |
| Contract baseline `--check` | current |
| Wheel build | `uv build --wheel` (with `NEXUS_WHEEL_ALLOW_NO_UI=1`: this worktree holds no UI export): 1.5 MB; carries `console/desktop.py`, `console/instance.py` and `[gui_scripts] nexus-scholar-app`. Installed alone in a throw-away Python 3.12 environment with no extras: `nexus-scholar --help` and `scholar-agent --help` answer; `desktop.main(['--frobnicate'])` returns 2 and logs the line |
| Console-less start (`pythonw`) and `--stop` | as above |
| Browser pane, fault 1 | as above |
| Independent review (milestone-reviewer) | round 1 CHANGES (one P1, one P2, six P3), repaired in f0f26985; round 2 APPROVE |

## Notes

- After a restart with a response still open, the log holds uvicorn's "Cancel 1 running task(s)" and an "Exception in ASGI application" trace (a `CancelledError`). It is harmless, but a tester sending the log may ask about it. Ending the event streams when a stop starts would avoid it; not done here.
- `engine.lock` stays in the settings folder after a stop (an empty file; the lock, not the file, is what counts).
