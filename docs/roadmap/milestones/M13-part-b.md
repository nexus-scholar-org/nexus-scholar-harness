# M13 Part B: settings and first-run setup

Status: **BUILT on `dev/m13/part-b-settings` (from `main` `f2a7407e`, `main` `5ffc53e2` merged in), not pushed; the check by hand of answer 7 was done by the coordinator session and its three faults are fixed. Lane RELEASE.** The researcher gave the go on 2026-11-24 ("Start Part B"), relayed by the coordinator session "Nexus Scholar parent work". Specification: `docs/roadmap/milestones/M13-installers.md` §4.3 and §5.2 Part B, and Q7 (settings in a file, keys in the system keychain). Decisions: `docs/decisions.md`, entry "2026-11-24 — M13 Part B". Screen specification: `docs/ux/shared/final/05-settings.md`.

## Questions answered by the researcher (2026-11-24)

Asked before the build and answered one by one in the coordinator session, each as recommended.

| # | Question | Answer | Not chosen |
| :-- | :-- | :-- | :-- |
| 1 | Scope of the screen | **E-mail, keys and the reviews folder**, plus a Settings link on Workspaces and a Settings button in the control window. Connect (Part C) and the update notice (Part D) come later, with no placeholder now | Connect Claude Desktop in this part |
| 2 | Which value wins when one is set in several places | **The environment, then `.env` in the current folder, then the screen** (the settings file and the keychain). When a value comes from the environment or `.env`, the screen says so and does not offer to change it | The screen's value beats `.env` |
| 3 | When setup opens by itself | **Only on the installed start with no settings file yet.** `nexus-scholar ui` from a terminal lands where it does today; both starts get the Settings link | Both starts open setup at first run |
| 4 | "Later" | **Remembered** in the settings file, so setup does not reopen at every start; a search still stops and asks for the contact e-mail, pointing to Settings | Setup reopens at each start until an e-mail is saved |
| 5 | AI provider keys | **Three optional rows**: Anthropic, OpenAI-compatible, Google Gemini; set, replace or remove only, never shown; no base-URL setting | Anthropic only |
| 6 | No system keychain | **A file only this user can read, after a confirmation, wherever the keychain fails**; the screen says where the file is | Linux only; elsewhere keys cannot be stored |

The screen specification (`docs/ux/shared/final/05-settings.md`) raised two more, also answered on 2026-11-24 as proposed:

| # | Question | Answer | Not chosen |
| :-- | :-- | :-- | :-- |
| 7 | What stands in for the "browser test in both themes" (the browser suites were removed on 2026-11-23) | **Component tests and a check by hand**: vitest against a fake engine, the in-process accessibility pass in light, dark and Arabic, and before the pull request a check by hand of the real installed start in both themes at phone and desktop width | One real-browser test for this screen |
| 8 | A folder change when a restart is not allowed | **Refuse, save nothing**: `WORKSPACE_BUSY` while an agent run or an approval is in progress, `RESTART_UNSUPPORTED` under `serve`, both before the folder dialog opens | Save the folder and apply it at the next start |

## What Part B replaces from Part A

- The installed app's words that send a tester to a `.env` file in the settings folder: the contact e-mail and OpenAlex key cards, the look-up's e-mail refusal (Part A second pull request, decision item 1).
- "Not available in this version" for provider keys in the installed app (item 2).
- "Open the settings folder" standing in for a Settings button in the control window (item 4).

## What was built

- **The store** (`src/scholar_search/user_settings.py`):
  - `settings.json` in the user's settings folder holds the contact e-mail, the reviews folder and the setup choice;
  - the keys go in the system keychain (service `nexus-scholar`), or in `keys.json` after a confirmation where the keychain fails (answer 6);
  - both files are readable by this user only.
- **The precedence** (answer 2): the search settings read the store as their lowest-precedence source, after the environment and `.env` (`src/scholar_search/config.py`), and reload in place. The AI key store (`scholar_agent/keys.py`) and the MCP server read the keys file after the keychain. The workspaces root reads the chosen folder after `--root` and `NEXUS_WORKSPACES_ROOT` (`workspace/catalog.py:resolve_root`).
- **The routes** (`src/scholar_harness/console/api/settings.py`; `docs/architecture/settings-api.md`):
  - read;
  - the e-mail;
  - a key;
  - remove a key;
  - setup;
  - the folder, through the system's folder dialog (`console/folder_dialog.py`) and a restart in place.

  They have four new refusal codes and never return a key's value.
- **First run** (answer 3): the installed start lands on `/en/settings/?setup=1` while no setup choice is saved. The control window's Settings button opens the screen with a fresh launch link.
- **The screen** (`apps/research-ui/components/settings-screen.tsx`, `/[locale]/settings/`), as its FINAL specification says: three cards, write-only keys, the source of each value, the keychain question, the folder change and its wait, Done and Later in setup mode, in English, French and Arabic.
- **Part A's stand-ins replaced**:
  - the cards for a missing e-mail, OpenAlex key or provider key link to Settings;
  - the discovery and look-up texts say to save the value on the Settings screen;
  - "Settings" is in the header on every route and on Workspaces.

## Definition of done (specification §5.2 Part B)

| Item | Evidence |
| :-- | :-- |
| A search refused for a missing e-mail succeeds after the e-mail is saved on the screen, with no restart by the user | `tests/console/test_settings_api.py::test_a_search_refused_for_a_missing_email_goes_on_after_it_is_saved_with_no_restart` (the same app: `MAILTO_NOT_SET`, then the run passes the e-mail check) |
| A key saved on the screen is never returned by any route | `test_a_saved_key_is_never_returned_by_any_route` (every answer and refusal after every key is saved); the screen's half: `apps/research-ui/tests/settings.screen.test.tsx` "a key leaves the page with its request and is never shown again" |
| An environment variable still wins | `test_the_environment_and_dotenv_still_win` (and `.env`, answer 2); the screen: "a value set in the environment or .env is printed with its source and cannot be edited" |
| The screen passes the accessibility checks and the check of answer 7 | `settings.screen.test.tsx` "settings.a11y" (in-process axe in light, dark and Arabic); the check by hand: see Evidence |

## Independent review (milestone-reviewer), round 1: CHANGES, repaired

| # | Finding | Repair | Test |
| :-- | :-- | :-- | :-- |
| P1 | The installed start built the search settings before moving into its settings folder, so the `.env` there was missed and the search cache went to the wrong folder | `desktop._start` reads the search settings again after the change of folder (`reload_settings()`) | `test_desktop_start.py::test_the_installed_start_reads_dotenv_and_the_cache_from_its_own_folders` |
| P1 | The check by hand of answer 7 and the Evidence were missing | Evidence below; the check by hand **was not done** (see there) | — |
| P2 | An empty variable (`SCHOLAR_MAILTO=`) hid the saved value, and the screen named the wrong source | `env_ignore_empty=True` in the search settings | `test_an_empty_variable_does_not_hide_the_saved_value` |
| P2 | A key kept in the file after the keychain refused it could be shadowed by an older keychain copy | storing in the file removes the keychain copy, and refuses again if it cannot | `test_a_key_kept_in_the_file_replaces_an_older_keychain_copy` |
| P2 | The busy check was not repeated after the folder dialog, which may stay open for minutes | checked again after the dialog; refused with `WORKSPACE_BUSY`, nothing saved | `test_a_run_started_while_the_folder_window_was_open_stops_the_change` |
| P2 | Child processes started by tests could read the real keychain | `tests/conftest.py` sets `PYTHON_KEYRING_BACKEND` to keyring's "null" backend for the session | — |
| P3 | `nexus-scholar keys clear` left a key kept in the file; the refusal note had no words for the file; the phone card's link said "Back to Workspaces"; `aria-describedby` named a missing source line | fixed | existing tests |

Left as follow-ups (P3, as the review listed them):
- **The keychain at start.** Every CLI and MCP start now reads the keychain at import when the `ai` extra is installed (a Linux keyring may prompt), so a lazy read is worth considering.
- **The folder dialog.**
  - Nothing stops two dialogs being open at once, from two tabs.
  - A dialog left open across a restart can still save the folder.
  - Firefox gives up on a request after 300 s, before the dialog's 10-minute wait ends.
- **The settings file.** It is written without a lock and without the Windows replace retry.
- **An unwritable reviews folder.** If the saved folder cannot be written, the installed start refuses to start, so the screen cannot be reached to change it.
- **The PDF kit's own `MAILTO`.** It now loses to the e-mail saved on the screen.
- **Missing from the screen specification.** The footer caption with the settings folder, and the reason disabled buttons give when the engine is unreachable.
- **Answer 3's wording.** Setup opens while no Done or Later choice is saved, which is wider than "no settings file yet".
- **Decision item 20.** It departs from the screen specification and needs the researcher's acceptance.

**Round 2: CHANGES on evidence only** (no code change required): every round-1 finding was verified repaired. Its three small notes were repaired in `2a939361`:
- a key is not written to the file while an old keychain copy cannot be removed;
- the shared search settings are restored after each test (`tests/conftest.py`);
- `keys clear` says "removed" or "no stored key".

What it still requires is the check by hand of answer 7, below.

## Evidence

| Check | Result |
| :-- | :-- |
| Full Python suite (suite lock, `-n 4`) on `435c296a` (the engine) | 5369 passed, 16 skipped |
| UI on `1bd71597`: typecheck, `lint:ui`, vitest (suite lock) | pass; 76 passed; 120 files, 1394 passed |
| Contract baseline, ruff (`scripts/`, `src/` bug rules), `select_test_gate --check`, `git diff --check` | current; pass |
| Final gate on the merged tree `113ac9c6` (this branch with `main` `5ffc53e2` merged in; after review rounds 1 and 2) | full Python suite (suite lock, `-n 4`): 5375 passed, 16 skipped; typecheck pass; `lint:ui` 76 passed; vitest (suite lock): 120 files, 1394 passed; `git diff --check`, ruff, contract baseline, `select_test_gate --check` pass |
| **Check by hand of the installed start (answer 7), done by the coordinator session** on `dc9db004` ("You check it here", the researcher, 2026-11-24) | Passed, with three small faults, fixed below. See "The coordinator's check by hand" |

## The coordinator's check by hand (2026-11-24, on `dc9db004`)

Done by the coordinator session at the researcher's request ("You check it here"). This session's own attempt was refused by its permission check. Setup:
- the web export built from `dc9db004` (`NEXUS_UI_DIR`);
- `nexus-scholar-app.exe --no-browser`;
- `NEXUS_APP_HOME` and `NEXUS_WORKSPACES_ROOT` both temporary folders;
- `NEXUS_APP_DIALOGS=0`;
- `PYTHON_KEYRING_BACKEND` set to keyring's "fail" backend;
- the provider and e-mail variables removed.

**Passed (English unless said):**
- **First run.** The installed start opened `/en/settings/?setup=1` by itself, with the cookie `nexus_started_as=installed`. Done was `aria-disabled` with its note until an e-mail was saved.
- **The e-mail.** An invalid address was refused in place (`SETTING_INVALID`, "Nothing was sent"). A made-up address saved: "Saved in your settings" and the announcement "E-mail address saved.". Done became available.
- **A key.** A made-up Anthropic key was refused with `KEYCHAIN_UNAVAILABLE` (409), then the question naming `keys.json` in the temporary settings folder appeared. After "Keep the key in that file" the row read Set, with Replace and Remove and "Kept in <file>". The value was in neither the page's HTML nor `GET /api/v1/settings`, whose source read `file`.
- **Done.** Done went to Workspaces, with the installed empty-list wording and a Settings link. `settings.json` held `contact_email`, `schema` and `setup: done`.
- **A new start.** The process was killed rather than stopped cleanly, so `engine.json` stayed. On the next start the app landed on Workspaces, not setup, and Settings showed the e-mail and the key as Set.
- **Remove.** The key read Not set at once, focus moved to that row's field, and `keys.json` became `{}`.
- **Themes and widths.** Light and dark at 1440 and 375 px, and `/ar/settings/` (RTL): no horizontal page scroll. The console held only the two expected refusals (422, 409).
- **The logs.** The two log files held no key, no e-mail address and no launch code.

**Faults found, fixed after the check** (tests in `apps/research-ui/tests/settings.screen.test.tsx`; web checks on `8c1ab476`: typecheck pass, `lint:ui` 76 passed, vitest through the suite lock 120 files and 1395 passed; no Python changed since the merged-tree run):
1. **A file path did not wrap at 375 px.** The keys file's path ran past the card's edge, in the Keys sentence and in the row's "Kept in …" line, in both themes. Both paragraphs now wrap like the folder path (`[overflow-wrap:anywhere]`). Test: the class on both lines.
2. **Focus was lost after "Keep the key in that file".** It fell to the page body. It now goes to the row's Replace button once the row has re-rendered. Escape, Cancel and "Do not save" use the same mechanism. Test: Replace has focus after the confirmation.
3. **Names were not told apart.** The five key fields were all named "Paste the key", and both Remove buttons were named "Remove". Each field, Replace and Remove now names its value: "Paste the key OpenAlex key", "Replace Google Gemini key", "Remove E-mail address". Test: "settings.names".

**The coordinator's observation on Done.** Before the e-mail is saved, Done kept the brand colour although it was `aria-disabled`. Pressing it does nothing (test "first run": no setup request is sent). It now also looks unavailable (`opacity-60`, `cursor-not-allowed`) until the e-mail is saved. The specification says only `aria-disabled` with the note, so the look is a choice of this build.

**Not covered by the check:**
- the folder row when it can be changed, and the folder dialog: `NEXUS_WORKSPACES_ROOT` pins the folder (see the note below);
- the cards' "Open Settings" link on Discovery or Screening: there was no review in the temporary folder;
- the control window's Settings button: windows were off;
- a real system keychain;
- French by eye.

## Note for anyone repeating the check by hand

**Set `NEXUS_WORKSPACES_ROOT` to a temporary folder, as well as `NEXUS_APP_HOME`.** `NEXUS_APP_HOME` moves the settings, log and cache folders only. Without the root variable, the workspaces root falls to the default, `~/Documents/Nexus Scholar/workspaces`, the researcher's real reviews folder. The installed start then opens the most recent review there, and the workspace format check would copy and stamp a real review. The start command this session first described for the check left that variable out; the permission check refused it. The consequence of setting the variable: the folder row shows "Set in the environment (NEXUS_WORKSPACES_ROOT)", so its changeable state and the folder dialog cannot be checked this way. Decision entry item 21 asks the researcher whether `NEXUS_APP_HOME` should also move the default reviews folder.
