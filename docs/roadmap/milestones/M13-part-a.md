# M13 Part A: the launcher for an installed app

Status: **BUILT on `dev/m13/part-a-launcher` (from `main` `cc0e8fa1`), not pushed; the engine start path only (see "Not in this branch"). Lane RELEASE.** The researcher gave the go on 2026-11-24 ("Start Part A and the workspace format version"), relayed by the coordinator session "Nexus Scholar parent work". Specification: `docs/roadmap/milestones/M13-installers.md` §4.1, §4.2, §5.2 Part A and §8 (trial build). Decisions: `docs/decisions.md`, entry "2026-11-24 — M13 Part A".

## What a start from an icon does now

`pythonw -m scholar_harness.console.desktop` (and, once Part W builds it, the bundle's windowed program) starts the engine with no terminal (`src/scholar_harness/console/desktop.py`):

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
| No console window appears (by hand on Windows) | `pythonw -m scholar_harness.console.desktop --no-browser` from `C:\Windows`: `engine.json` after 5.9 s, `/healthz` 200, the log complete. The windowed entry point (`gui-scripts`) is not in this branch, see below |
| With no settings, the first page is the setup screen | **not in this branch**: the setup screen is Part B |

## Not in this branch (the rest of spec §5.2 Part A)

- **The `[project.gui-scripts]` entry point** (`nexus-scholar-app = "scholar_harness.console.desktop:run"`). It is one line in `pyproject.toml`, which the graph removal (`dev/h/remove-graph`) is changing; it waits for that merge.
- **The control window** of §4.2: Open in browser, Settings, Stop, the status line and the closing question with the busy check. The instance routes it needs (a fresh link, stop) are here.
- **The app's text** (about 60 lines in three languages that send the user to a terminal, a variable or `.env`), and the engine telling the app how it was started.
- **The message "the browser could not reach Nexus Scholar"**: only the control window can show it.

## Evidence

| Check | Result |
| :-- | :-- |
| Targeted tests (`tests/test_ui_launcher.py`, `tests/console/test_desktop_*.py`) | 22 passed |
| Selector `pr` gate (areas console, harness-cli) | see the commit and the report; filled below |
| `git diff --check`, `ruff check scripts/`, `ruff check src/ --select F821,…` | pass |
| Contract baseline `--check` | current |
| Wheel build | filled below |
| Console-less start (`pythonw`) and `--stop` | as above |
| Browser pane, fault 1 | as above |
| Independent review (milestone-reviewer) | filled below |

## Notes

- After a restart with a response still open, the log holds uvicorn's "Cancel 1 running task(s)" and an "Exception in ASGI application" trace (a `CancelledError`). It is harmless, but a tester sending the log may ask about it. Ending the event streams when a stop starts would avoid it; not done here.
- `engine.lock` stays in the settings folder after a stop (an empty file; the lock, not the file, is what counts).
