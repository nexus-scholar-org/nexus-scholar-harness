# M13 Part W: the Windows installer

Status: **BUILT on `dev/m13/part-w-windows-installer` (cut from Part B's head `b5501e1a`), not pushed; the installer itself is built and tested only in CI, so its first run is the pull request's. Lane STANDARD.** The researcher chose Part W on 2026-11-24 ("Which M13 part should start next": "Part W: Windows installer"), directly in this session. Specification: `docs/roadmap/milestones/M13-installers.md` §2.2, §3.1, §4.1, §4.6, §5.2 Part W, Q1, Q2, Q10; the trial build of §8. Decisions: `docs/decisions.md`, entry "2026-11-24 — M13 Part W".

## Questions answered by the researcher (2026-11-24, before the build)

| # | Question | Answer | Not chosen |
| :-- | :-- | :-- | :-- |
| 1 | The app's icon (there is no logo yet) | **A simple monogram**: "NS" in the brand's archive blue, kept in the repository and turned into the `.ico` | Default icons; waiting for a logo |
| 2 | Where the installer is built and tested | **CI only**: GitHub's Windows runner builds, installs, starts, stops and uninstalls it, on tags and on demand. Nothing new is installed on this PC; locally only the bundle is built, in a throw-away environment | Also installing Inno Setup on this PC |
| 3 | The clean-machine check of the definition of done | **Decide later**, when the first installer exists | Turning on Windows Sandbox now; relying on CI and a tester |

## What was built

- **The bundle recipe** (`packaging/windows/nexus-scholar.spec`): one folder with two programs.
  - `Nexus Scholar.exe` is windowed. It runs the installed app, its approval-code window and its folder dialog.
  - `nexus-scholar-mcp.exe` is a console program: the MCP server, for Part C's Claude Desktop entry.
  - It collects `scholar_harness_data` (the screens, skills and docs), the packages' own data files and the plugin manifest. It records the package's version information.
  - It excludes `jedi`, IPython and `parso`, the trial build's path-length fault.
- **The build** (`packaging/windows/build.py`):
  - a throw-away Python 3.12 environment with the wheel, its `ai` and `pdf` extras and PyInstaller 6.22.3 (pinned);
  - with `--installer`, Inno Setup's compiler;
  - the version key (one integer that orders PEP 440 versions) for the downgrade check.
- **The installer** (`packaging/windows/nexus-scholar.iss`, Inno Setup):
  - per user, with no administrator password, installed in `%LOCALAPPDATA%\Programs\Nexus Scholar`;
  - a Start-menu entry, and a desktop icon (ticked);
  - "Start Nexus Scholar" at the end;
  - a running Nexus Scholar is stopped first, after asking, with the app's own `--stop`;
  - an older version over a newer one warns first (default No).
  - The uninstaller asks, default No, "Also remove your Nexus Scholar settings and saved keys?". On yes it runs the app's new `--forget` before the files go. A review is never removed.
- **`--forget`** (`console/desktop.py`):
  - removes every saved key (keychain and keys file), the settings folder, the logs and the cache;
  - a folder that holds the reviews folder is kept, and only the app's own files in it go.
- **The icon** (`packaging/icons/`): `nexus-scholar.svg` (the design), `make_icon.py` (Pillow, in a throw-away environment), and the generated `nexus-scholar.ico` and a 256 px PNG.
- **CI** (`.github/workflows/windows-installer.yml`, `packaging/windows/smoke_test.ps1`). It runs on v* tags (the installer is attached to that release), on demand, and on pull requests that change the packaging files. Steps:
  1. build the web export, the wheel, the bundle and the installer;
  2. install silently for the current user;
  3. check the Start-menu entry and `nexus-scholar-mcp.exe --help`;
  4. start with no browser, with the app's home and the reviews folder both temporary;
  5. fetch `/healthz` and the first page through a fresh launch link (first run: setup);
  6. stop it;
  7. uninstall silently;
  8. check that a review folder made before the install is still there.

  It records the sizes and the time to the first page in the run's summary.
- **A gate area** `windows-packaging` runs `tests/test_windows_packaging.py`.

## Not in this part

- **The Claude Desktop entry** (Part C). The uninstaller's "remove the Claude Desktop entry if it points at this program" (§4.6) comes with it.
- **The Settings screen's "Remove my settings and keys" button** (§4.6). `--forget` is the engine side of it.
- **Signing** (Part S). The installer is unsigned, so SmartScreen shows "More info, Run anyway" (§3.1).
- **The clean-machine check** (answer 3: later).

## Evidence

| Check | Result |
| :-- | :-- |
| `tests/test_windows_packaging.py` | 11 passed: the version order; the wheel name; the installer's promises (per user, `{userpf}`, desktop icon ticked, `--stop`, the downgrade default No, `--forget` unticked, reviews never removed, the AppId); the recipe's two programs and the trial's lessons; the CI test's temporary reviews folder; the workflow's triggers |
| `--forget` | `tests/console/test_desktop_start.py`: removes settings, keys (keychain and file), logs and cache and keeps a review; keeps a folder that holds the reviews folder |
| **The bundle built locally** (`build.py` without `--installer`, Python 3.12 in a throw-away environment, PyInstaller 6.22.3, from the wheel built with the web export of this branch) | built in 329 s in all (web export 39 s, wheel 15 s, bundle about 275 s); **226 MB in 1,988 files** (the trial: 285 MB in 7,594, before the graph code and `jedi` left) |
| **A frozen start of that bundle** (`Nexus Scholar.exe --no-browser` from `C:\Windows`; the app home and the reviews folder both temporary; keyring pointed at its null backend) | `nexus-scholar-mcp.exe --help` exit 0; the engine answered, `/healthz` ok; the first page through a fresh launch link **2.3 s** after the start, on `/en/settings/` (first run); `started_as: installed`; `--stop` stopped it and freed the port; the review folder untouched; the log says `bundled: True` and holds no error |
| The installer and its CI test | **not run yet**: the researcher chose CI only (answer 2), and the workflow runs on the pull request, which this session does not open |
| Contract baseline, `select_test_gate --check` (24 areas) | current; OK |

**Not verified:**
- the installer itself and its SmartScreen warning;
- the approval-code window and the folder dialog inside this bundle: the trial's probe covered the approval window's start, and both are started the same way;
- a clean machine (answer 3: later);
- the Inno Setup script compiling: first on CI.
