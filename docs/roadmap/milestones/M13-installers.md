# M13-installers

Status: **SPECIFICATION. Questions 1 to 12 answered by the researcher on 2026-11-23, each as recommended (§6). Nothing is built; the build of M13 needs the researcher's separate go. The trial build of question 12 comes first, after this specification is merged.** Written by a specification session at the researcher's request of 2026-11-23, started by the coordinator session "Nexus Scholar parent work". The start of any build, any trial build, any spend and any account is the researcher's to approve. Lane: per part (§5); the engine and app parts are **RELEASE**, the packaging-only parts **STANDARD**.

The request, in the researcher's words (2026-11-23): "I want like something installable for every platform, MSI for Windows, .deb or something like package manager for Linux, and why not macOS? It needs to be easy, next, for the user to install and configure the Nexus, and also install the MCP and it should create a desktop icon or start item menu. So when he clicks, it opens up the app directly. No need for terminal or code as shown in terminal only for people who don't know how to use terminal."

**How to read this.** §1 says what exists, from the code at `main` `6f31f92e`. §2 compares three ways to build installers; §3 explains signing. §4 is the behaviour a tester will see, and is the part to read most closely. §5 is the plan; §6 the questions; §7 what rests on documentation only. Words in *italics* are explained the first time they appear.

---

## 1. What exists today (at `main` `6f31f92e`)

### 1.1 What `nexus-scholar ui` does

- **One process, one address.** `nexus-scholar ui` (`src/scholar_harness/cli.py:1619-1665`) finds the app's screens (`console/launcher.py:33-44`: `NEXUS_UI_DIR`, else the copy inside the wheel, else a source build), picks the workspaces folder (`workspace/catalog.py:36-43`: `--root`, else `NEXUS_WORKSPACES_ROOT`, else `~/Documents/Nexus Scholar/workspaces`), and starts one server that serves both the screens and the engine's API on `127.0.0.1` only (`console/serve.py:49`).
- **The port.** 8770 if free, else one the system picks; fixed for the launch (`launcher.py:47-56`). A taken port is therefore not a failure today.
- **The browser session.** The launcher makes a secret token and a session secret per launch (`launcher.py:79-81`), then opens the default browser on a one-time *launch link* (`/launch?code=…`, `launcher.py:115-117`). The code is valid once, for 2 minutes (`console/browser.py:35`, `:123-142`); it sets a cookie that only this site can read and redirects into the app (`serve.py:300-306`). A used or expired link answers "start `nexus-scholar ui` again" (`serve.py:303`). **Consequence for an icon:** a second browser tab can be opened only by a new launch link, which only the running launcher can issue. Nothing outside the process can ask for one today.
- **Switching workspaces** restarts the server inside the same process, on the same port and session (`launcher.py:105-137`). A server not started by `ui` cannot switch (`console/api/workspaces.py:77`).
- **Stopping.** Only Ctrl+C in the terminal (`launcher.py:126`, `cli.py:1662-1665`). There is no Stop button.
- **Logs.** The server logs at "warning" level to the terminal (`launcher.py:147-150`). There is no log file.
- **Approval codes** (publishing a screening batch) are printed in the terminal, and also shown in a small desktop window (`console/code_window.py`). That window runs as a child process started as `[sys.executable, "-I", <the file>]` (`code_window.py:115-117`), with no console window on Windows (`:124`). It needs Tk (`:82`); without it the codes stay in the terminal only.
- **A second launch** starts a second, independent engine on another port, on the most recently used workspace (`launcher.py:47-56`, `catalog.py:139`). Nothing detects the first. The decision files have their own lock (`screening/events.py`), so two engines do not corrupt events, but two copies of the app on one workspace is still confusing.

### 1.2 What a first-time user must do with a terminal or a hand-edited file

| Step | Today | Screen or route? |
| :-- | :-- | :-- |
| Install | Python 3.11+ and `uv tool install "nexus-scholar>=1.1.0b6"` or `pip install` (`docs/nexus_scholar_user_guide.md:64-104`) | none |
| Start | `nexus-scholar ui` in a terminal, which must stay open (`user_guide.md:110-120`) | none |
| Contact e-mail (`SCHOLAR_MAILTO`) | an environment variable, or a `.env` file **in the folder the process starts from** (`src/scholar_search/config.py:90-92`; `user_guide.md:384-388`) | the app shows whether it is set (Discovery Plan, `apps/research-ui/components/discovery-plan.tsx:593-600`) and refuses a search without it (`console/api/discovery.py:280-285`, `MAILTO_NOT_SET`), with a message that names the variable and `.env` and says to restart; **no screen sets it** |
| OpenAlex key (`SCHOLAR_OPENALEX_KEY`, required for OpenAlex), Semantic Scholar key (`SCHOLAR_S2_KEY`, optional) | the same environment or `.env` (`config.py:27-38`) | shown as set or not on Plan; **no screen sets them** |
| AI provider keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`) | an environment variable, or `nexus-scholar keys set <provider>` into the system keychain (`cli.py:323-385`; `scholar_agent/keys.py:22`, `:128`); the keychain needs the `ai` extra (`keyring`) | **no screen** |
| Workspaces folder | `--root` or `NEXUS_WORKSPACES_ROOT`, else the default | the Workspaces screen lists, creates and opens; it cannot change the folder |
| Connect an AI client (MCP) | `nexus-scholar setup-mcp --workspace <folder> --harness claude` (`cli.py:169-195`, `mcp_setup.py:232`), or the `.mcpb` Claude Desktop extension attached to each release (`release.yml:68-70`, `scripts/build_mcpb.py`) | **no screen** |
| Read approval codes | terminal, or the desktop window | the window exists |
| Stop the app | Ctrl+C | none |
| Upgrade | `uv tool install --force "nexus-scholar>=<version>"` (`user_guide.md:472`) | none |
| Check the install | `nexus-scholar doctor` (`cli.py:198-231`) | none |

**About 60 lines of the app's own text, in its three languages, still send the user to a terminal, an environment variable or `.env`** (counted by a search for those words in `apps/research-ui/lib/*copy*.ts`, `screening-states.ts`, `screening-v1.ts` and `screening-api.ts`; an approximate count, not each line read). An installed app must change them.

Two facts matter for a launcher started from an icon, which starts in a folder the user did not choose:

- **The settings file and the cache depend on the starting folder.** The search settings read `.env` from the current folder (`config.py:90`) and the search cache defaults to `.cache` in the current folder (`config.py:48`). Started from a Start-menu icon, that folder is the program folder or the user's home.
- **The MCP entry needs `uv`.** `setup-mcp` writes `"command": "uvx"` with `--from nexus-scholar scholar-agent` (`mcp_setup.py:50-67`), and the `.mcpb` extension also starts the server with `uvx` (`build_mcpb.py:1-19`). A machine with only an installer has no `uv`. The Claude Desktop entry is written for one workspace (`--workspace <absolute path>`), in the user's Claude configuration (`mcp_setup.py:70-99`); the other targets (Cursor, VS Code, `.mcp.json`) write files inside the workspace.

### 1.3 The wheel and its release

- **One pure-Python wheel**, `nexus_scholar-<v>-py3-none-any.whl`, 3.5 MB for `1.1.0b6` (GitHub release asset, 3,514,925 bytes, published 2026-11-10). It holds the six packages, the skills and the app's screens (`pyproject.toml:100-127`).
- **Base dependencies** (`pyproject.toml:39-64`): fastapi, uvicorn, pydantic, pydantic-settings, httpx, aiohttp, mcp, openpyxl, pypdf, rich, typer, tenacity, requests, pyyaml, bibtexparser, hishel, and three that only the parked graph code uses: **scipy** (large: it brings numpy), networkx and pyvis (project review 2026-11-23, item 10). **Extras**: `pdf` (PyMuPDF, large), `extract` (Docling and lxml, very large: Docling brings machine-learning models), `ai` (anthropic, keyring).
- **Entry points** (`pyproject.toml:91-98`); extras at `:66-85`: `nexus-scholar`, `scholar-harness`, `scholar-agent` (the MCP server) and four kit commands. All are console programs; there is no windowed entry point.
- **Release** (`.github/workflows/release.yml`): on a `v*` tag, builds the app's screens with Node, the wheel with `uv build`, and the `.mcpb`; attaches both to a GitHub pre-release. **PyPI** (`publish.yml`): the same wheel, by trusted publishing. Both run on `ubuntu-latest` only.
- **CI** (`.github/workflows/ci.yml`): `lint-and-smoke` runs `--help` of both entry points from the wheel on Ubuntu, Windows and macOS; `wheel-e2e` (`ci.yml:156-252`) installs from the wheel on Ubuntu and Windows (not macOS), scaffolds a workspace, runs `setup-mcp --dry-run`, `doctor`, the journal, and starts `nexus-scholar ui --no-browser` and fetches the app (`ci.yml:241`).
- **The workspaces carry no format version** (project review 2026-11-23, finding 9 and item 8). Installed builds make silent upgrades more likely, because testers will install whatever the release page offers.

---

## 2. Three ways to build the installers

*Bundle* means a folder holding a private copy of Python, the app and every library, so nothing else needs to be installed. *Installer builder* means the tool that wraps that folder into the file a user double-clicks.

Facts below were read on 2026-11-23 on each tool's own pages, by a research agent of this session that opened each page named; anything it could not confirm is marked. Nothing was installed or built.

### 2.1 Route 1 — Briefcase (BeeWare)

Briefcase turns a Python project into a native app and its installer, with Python inside. Latest release 0.4.7, 2026-10-27 (briefcase.beeware.org, "Release history").

- **Formats.** Windows: an MSI made with the WiX Toolset (the default), or a zip ("Windows" platform page). macOS: a `.dmg` (default for windowed apps), a zip, or a `.pkg` ("macOS" page). Linux: `.deb`, `.rpm` and `.pkg.tar.zst` ("Linux system packages" page), Flatpak ("Flatpak" page) and AppImage, which the documentation itself "strongly discourage[s]" and says "is incompatible with the use of binary wheels" ("AppImage" page).
- **Per-user install on Windows.** With `system_installer = false` the MSI installs for the current user; per-machine installs "require admin permissions"; left unset, the installer asks ("Windows" page). A desktop shortcut can be offered (`create_desktop_shortcut`) and a "start the app" box on the last page.
- **Each platform on its own machine.** Each platform's page lists only its own system as a host; no page says Windows or macOS can be built elsewhere (implied, not stated). Linux packages for other distributions are built in Docker on a Linux host. The official CI how-to builds on `windows-latest`, `macos-latest` and `ubuntu-latest`, unsigned ("Building in CI").
- **Signing built in.** Windows `--identity`, `--timestamp-url`; on macOS, apps are "both signed and notarized when they are packaged" by default ("macOS" page).
- **No console window** is the default (`console_app` defaults to `False`, "Configuration").
- **The blocker for this project: no Tk.** On Windows, Briefcase uses Python's "embeddable" distribution, which "is missing some standard library modules", tkinter being the most notable ("Windows" page). On macOS its Python is built "with the IDLE, Tkinter and turtle packages removed" (BeeWare `Python-Apple-support` README). The approval-code window (`code_window.py:82`) and the control window of §4.2 use Tk.
- **Linux packages use the system's Python**, which must be 3.11 or later ("Linux system packages" page): one `.deb` per distribution release (Ubuntu 22.04's and 24.04's are different builds).
- **Updates**: `briefcase update` is a developer command ("update" command page); no end-user updater or single-instance feature was found (not confirmed either way).
- **Heavy libraries:** binary wheels must exist for each target ("FAQ"); PyMuPDF, lxml and keyring publish them on PyPI for the three systems (not checked per version). No Briefcase notes about them were found.

### 2.2 Route 2 — PyInstaller, plus one installer builder per platform (recommended)

PyInstaller collects a Python program, the Python it runs on and every library into one folder (pyinstaller.org, version 6.22.3).

- **One build per platform.** "It is not a cross-compiler"; "you must install PyInstaller on each platform and bundle your app separately on each" (manual home page; "Using PyInstaller").
- **One folder, not one file.** `--onedir` is the default; `--onefile` unpacks itself into a temporary folder at every start, is "a little slower to start", and leaves the folder behind after a crash ("How the one-file program works"). One folder is the right choice inside an installer.
- **No console window:** `--windowed` / `--noconsole`; on macOS this also makes a `.app` ("Using PyInstaller"). A bundle can hold two programs, one windowed (the app) and one console (the MCP server, which talks over its standard input and output).
- **Heavy libraries:** the community hook collection has hooks for `pymupdf`, `lxml`, `uvicorn`, `pydantic` and `webview`; PyInstaller itself has hooks for `keyring` and `_tkinter` (checked by the presence of the hook files on GitHub, not by a build). Docling has none.
- **Antivirus:** PyInstaller's own manual names "anti-virus false positives that result from the wide-spread use of pre-compiled bootloaders" as a reason to build its starter program from source ("Building the bootloader").
- **Licence:** GPL 2.0 with an exception: bundles "can be shipped with whatever license you want" ("License").
- **Updates and second launch:** none built in; this project builds both (§4.2, §4.5).

The installer builders:

| Platform | Builder | What it makes | Facts |
| :-- | :-- | :-- | :-- |
| Windows | **Inno Setup** (recommended, Q2) | one `setup.exe`, not an MSI | `PrivilegesRequired=lowest`: "will not request to be run with administrative privileges" (Inno Setup help, "PrivilegesRequired"); Windows 7 to 11 including Arm; free for any use with attribution, and "all commercial users … are requested to purchase a commercial license" (jrsoftware.org, "Inno Setup" and its licence text) |
| Windows | WiX Toolset (alternative) | an MSI | per-machine, per-user, or a choice (FireGiant docs, `Package` "Scope"); version 7.0.1 (2026-10-26); since v6, revenue-making users pay the "Open Source Maintenance Fee", with an exemption under US$10,000 a year of revenue, and v7 needs its licence accepted on the build machine (FireGiant "OSMF" page, from a search snippet, not opened) |
| Linux | **nFPM** | `.deb`, and `.rpm` from the same file | "a simple deb, rpm, apk, ipk, arch linux, msi, and msix packager", "just a single binary" (nfpm.goreleaser.com) |
| Linux | AppImage (only if asked, Q4) | one file to make executable and run | needs FUSE; on Ubuntu 22.04 and later the user must install `libfuse2` (`libfuse2t64` on 24.04) with a terminal command, or the app must be run with an extract flag (AppImage documentation, "FUSE") |
| macOS | `hdiutil` (part of macOS) or `create-dmg` | a `.dmg` | not opened by the research; standard tools |

### 2.3 Route 3 — a light installer that installs `uv` and then the wheel

A small installer that puts `uv` on the machine and runs `uv tool install "nexus-scholar[ai,pdf]==<version>"`, which downloads a private Python and the libraries, then makes the icons.

- `uv` installs per user with no administrator rights; tools go in `~/.local/bin` (`%USERPROFILE%\.local\bin` on Windows); tool environments in `%APPDATA%\uv\data\tools` on Windows; the private Python comes from Astral's python-build-standalone and is downloaded on demand (docs.astral.sh/uv: "Installation", "Storage", "Python versions"). `uv tool upgrade` keeps the version constraints given at install ("Tools").
- Tk in python-build-standalone: its distributions "contain tcl/tk support files" (its "Quirks" page, from a search snippet); partly confirmed.
- **For:** the smallest download; the exact wheel that CI already tests (`ci.yml:156-252`); updates are one command the app could run; `setup-mcp`'s `uvx` entry and the `.mcpb` would work unchanged.
- **Against:** the install needs the internet and downloads from PyPI and GitHub at install time (university proxies, slow lines, a PyPI outage on install day); what lands on the machine depends on what PyPI serves that day, not on what CI tested; more moving parts on the tester's machine, where failures are hardest to see; a console program (`uv`) runs during install; the installer still needs one builder per platform, so the packaging work is not much smaller.

### 2.4 Size, start time and comparison

**Size (estimates, not measured; Q12).** The wheel is 3.5 MB, but the bundle carries Python and every library: Python itself (roughly 30 to 40 MB), numpy and scipy (roughly 80 to 120 MB, used only by parked code), PyMuPDF (roughly 40 to 60 MB) and the rest (roughly 40 to 60 MB). **About 200 to 300 MB on disk and a 70 to 120 MB download** for routes 1 and 2; about 100 MB less once scipy, networkx and pyvis leave the base install (review item 10). Route 3 downloads a similar amount, at install time instead of from the release page. Start time is unknown until a trial build; a one-folder bundle starts about as fast as the same program from `uv`.

| | Briefcase | **PyInstaller + builders** | Light `uv` installer |
| :-- | :-- | :-- | :-- |
| Windows | MSI (per-user possible) | `setup.exe` (per-user), or MSI with WiX | `setup.exe` |
| Linux | `.deb`/`.rpm` per distribution release; Flatpak | one `.deb` (and `.rpm`) for several releases | `.deb` or a script |
| macOS | `.dmg`, `.pkg`, notarization built in | `.dmg`; signing and notarization by separate commands | `.pkg` or `.dmg` |
| Tk (approval window, control window) | **missing on Windows and macOS** | yes (a core hook) | yes (partly confirmed) |
| Works offline after download | yes | yes | no |
| What the tester runs = what CI tested | yes | yes | not exactly (PyPI on install day) |
| Builds on each own runner | yes | yes | yes |
| Moving parts to maintain | one tool, one config; per-distro Linux builds | three small configs over one recipe | an installer per platform plus `uv`'s behaviour |
| Known risk | Tk; Briefcase's own pace of change (0.3 to 0.4 in 2026) | antivirus false positives; bundle-only faults | network at install; support at a distance |

### 2.5 Recommendation

**Route 2: PyInstaller one-folder bundles, wrapped by Inno Setup on Windows, nFPM on Linux and a `.dmg` on macOS.** It keeps Tk, which the approval window needs today; it installs for one user without administrator rights on Windows; one Linux build serves several Ubuntu and Debian releases; and the tester runs the files CI tested. Its weak point is antivirus suspicion of unsigned PyInstaller programs, which is a signing question (§3) more than a tool question.

What would change it:
- **The researcher wants an MSI specifically** (for university IT, or because "MSI" is what testers expect): keep PyInstaller and use WiX instead of Inno Setup (Q2); the fee exemption applies while revenue is under US$10,000.
- **The approval and control windows move into the browser or an app window** (no Tk): Briefcase becomes attractive for its MSI, its per-distribution packages and its built-in notarization.
- **The trial build shows constant antivirus blocking on a clean Windows** that signing cannot fix soon: the light `uv` installer, whose downloaded files are Astral's and PyPI's, becomes the fallback.
- **Size matters more than offline install** (testers on very slow lines): the light installer.

---

## 3. Signing, in plain words

*Signing* means attaching a certificate to the program, so Windows or macOS can tell who published it and that it was not changed. Without it, both systems warn, and macOS hides the way past the warning. Costs checked on 2026-11-23.

### 3.1 Windows

**What an unsigned installer shows.** Microsoft Defender SmartScreen shows "Windows protected your PC". The user clicks **More info**, then **Run anyway**. Every new version starts again from zero reputation. A company policy can remove the button. (Microsoft Learn, "SmartScreen reputation for Windows app developers".) The browser may also warn that the file "is not commonly downloaded" (not checked).

**Smart App Control is the harder one.** On a recent Windows 11 installation, Smart App Control "in most cases … will automatically turn on" after an evaluation period, and an unsigned app it cannot judge "will consider it untrusted and block it", with no Run-anyway button (Microsoft Support, "What is Smart App Control?"). The user can turn it off in Windows Security › App & browser control; recent updates let it be turned on again without reinstalling Windows (same page). **So some testers will have to switch off a protection to run an unsigned build.** Whether it blocks the program files inside the bundle one by one, or only the installer, is not verified.

**Signing does not remove the warning at once.** Since 2024, even an expensive "EV" certificate "no longer bypass[es] SmartScreen"; a signed build still warns "until reputation accumulates", which "can take several weeks and hundreds of clean installs", but it shows the publisher's name and keeps reputation across versions (Microsoft Learn, "SmartScreen reputation" and "Code signing options").

| Remedy | Cost (2026-11-23) | For an individual in Algeria | Source |
| :-- | :-- | :-- | :-- |
| Nothing: unsigned, with an illustrated "More info › Run anyway" page | 0 | yes | — |
| **SignPath Foundation** (free signing for open-source projects) | 0 | the project must have an OSI licence with no proprietary parts (MIT qualifies), be maintained and already released, have a verifiable reputation, build its files from source in a verifiable way (CI), publish a code-signing policy, use two-factor sign-in for every team member, and approve each release by hand. The certificate names **SignPath Foundation** as publisher, not the researcher | signpath.org, "Terms" (a draft page) |
| **Certum "Open Source Code Signing"** (a smart card and reader) | **€69** for the set; the cloud variant about €359 (search snippet) | sold to natural persons as "Open Source Developer"; validity period not stated; identity checks by post or video | shop.certum.eu |
| A commercial certificate from another authority (OV) | **US$150 to 300 a year** typical (Microsoft's figure); Sectigo direct from US$536 a year | the key must sit on a hardware token or a cloud service since June 2023 | Microsoft Learn, "Code signing options"; sectigo.com |
| Microsoft's own **Artifact Signing** (was "Trusted Signing") | about **US$9.99 a month** | **not eligible**: "Individual developers must be located in the United States or Canada"; organisations in a listed set of countries, Algeria not among them | Microsoft Learn, Artifact Signing quickstart (updated 2026-11-20) and FAQ |
| The Microsoft Store (free listing; the Store re-signs MSIX packages) | 0 | possible, but an MSI or EXE submitted there must already be signed; a separate packaging track | Microsoft Learn, "Code signing options" |

### 3.2 macOS

**What an unsigned, un-notarized app shows.** A message that the app cannot be opened because Apple cannot check it. Since macOS 15 Sequoia the old Control-click › Open shortcut is gone (Apple Developer news, 2024-08-06). The user must open **System Settings › Privacy & Security**, scroll to the message about the app, click **Open Anyway**, confirm with their password, then click **Open** (Apple Support, "Safely open apps on your Mac"). Many people give up at that point. Apple silicon also refuses to run code with no signature at all; a free "ad hoc" signature, made on the build machine, satisfies that rule but not Gatekeeper (stated from PyInstaller and Apple practice; not verified on a build).

**The remedy.** The Apple Developer Program: **US$99 a year** ("prices may vary by region"); an individual enrols with a two-factor Apple Account and their legal name (developer.apple.com, "Enrollment"). It gives the Developer ID certificate and *notarization* (Apple scans the app and issues a ticket Gatekeeper accepts). The fee waiver is for non-profits, accredited schools and government bodies, and the applicant must "not be an individual" (Apple, "Membership fee waiver"). "Enrollment may not be supported in certain regions"; **whether an individual in Algeria can enrol was not confirmed**. A university could enrol as an institution, with the waiver; that is the university's decision.

### 3.3 Linux

A `.deb` opened from a file is installed by the Software app or `apt` after the computer's password; no signature is asked for (not confirmed by a source the research opened). Signing matters only for a package *repository* (apt's signed lists), which is out of this milestone.

### 3.4 What can be done at zero cost for the first testers

1. Ship Windows unsigned, with a one-page illustrated guide: More info › Run anyway; and, where Smart App Control blocks it, how to turn it off and that it can be turned on again afterwards.
2. Apply to the SignPath Foundation programme as soon as the first installer is on a release page (it asks for a released project and a CI build), and publish the code-signing policy it requires. If accepted, Windows builds are signed at no cost, under the Foundation's name.
3. Submit each release's installer to Microsoft's free false-positive review if Defender flags it (the Microsoft Security Intelligence submission portal; not opened by the research).
4. macOS: give the illustrated Open Anyway steps to a tester who agrees; otherwise keep macOS testers on the existing `uv` install until the US$99 is approved and enrolment from Algeria is confirmed.
5. Linux: nothing to pay.

The cheapest paid step, if SignPath refuses or its publisher name is unwelcome, is the Certum open-source set at €69 (validity and renewal price to check before buying).

---

## 4. What the tester sees (the product behaviour)

This section follows the answers of §6 (a bundle made with PyInstaller, the user's own browser, a small control window, Claude Desktop only, an update notice). Where an answer would change what the tester sees, the question is named.

### 4.1 Install

| | Windows 10 and 11 (64-bit) | Linux (Ubuntu 22.04 and 24.04, Debian 12; 64-bit Intel/AMD) | macOS 13 or later (Apple silicon) |
| :-- | :-- | :-- | :-- |
| What the user downloads | `NexusScholar-<version>-setup.exe` from the release page (Q2: or an `.msi`) | `nexus-scholar_<version>_amd64.deb` (Q4) | `NexusScholar-<version>.dmg` |
| What they click | double-click; the warning of §3 until it is signed; a short wizard: licence, "Create a desktop icon" (ticked), Install, "Start Nexus Scholar" (ticked), Finish | double-click; the Software app opens and asks for the computer's password (a `.deb` installs for every user; see Q4) | double-click; a window with the app and an Applications folder; drag one onto the other; the first open needs the step of §3 |
| Administrator rights | **not needed**: installs for this user only | needed (the password prompt) | not needed when dragged to the user's own Applications folder; the shared one asks for a password |
| Where the program goes | `%LOCALAPPDATA%\Programs\Nexus Scholar\` | `/opt/nexus-scholar/` | `Nexus Scholar.app` in Applications |
| Icons | Start menu entry "Nexus Scholar"; desktop icon if ticked; an entry in Settings › Apps for uninstalling | an entry in the applications menu (Activities); Ubuntu shows no desktop icons by default, so the user pins it to the dock | Launchpad and the Applications folder; the user may keep it in the Dock |
| Size on disk | to be measured (Q12); estimated 150 to 300 MB; see §2.4 | same | same |

What the installer writes outside the program folder: the menu entry and icon, and nothing else. Settings, logs and the cache are created by the app on first start, in the user's own folders:

| | Windows | Linux | macOS |
| :-- | :-- | :-- | :-- |
| Settings (`settings.json`) | `%APPDATA%\Nexus Scholar\` | `~/.config/nexus-scholar/` | `~/Library/Application Support/Nexus Scholar/` |
| Log files | `%LOCALAPPDATA%\Nexus Scholar\Logs\` | `~/.local/state/nexus-scholar/logs/` | `~/Library/Logs/Nexus Scholar/` |
| Cache (search and recon) | `%LOCALAPPDATA%\Nexus Scholar\Cache\` | `~/.cache/nexus-scholar/` | `~/Library/Caches/Nexus Scholar/` |
| Keys | Windows Credential Manager | the desktop's keyring (GNOME Keyring or KWallet) | the macOS Keychain |
| Workspaces | unchanged: `Documents\Nexus Scholar\workspaces` | unchanged: `~/Documents/Nexus Scholar/workspaces` | unchanged |

The launcher starts the engine in the settings folder, never in the program folder or wherever the icon happened to start it, so the `.env` and `.cache` rule of §1.2 cannot point at the wrong place.

### 4.2 Start

**The icon opens the user's own browser on the app (recommended, Q3), plus a small window titled "Nexus Scholar".** The window is the sign that the engine is running and the place to stop it. It holds:

- one sentence: "Nexus Scholar is running on this computer. Your reviews are in <folder>.";
- **Open in browser** (a new tab with a new one-time link; useful when the tab was closed);
- **Settings** (opens the settings screen of §4.3 in the browser);
- **Stop Nexus Scholar**;
- a line when a newer version exists (§4.5);
- a link "Show the log file".

The window can be minimised. Closing it asks "Stop Nexus Scholar? Open browser tabs will stop working." When a harvest, an agent run or an approval is in progress (the engine already knows: `catalog.py:147`), it says which and offers **Keep running**. A tray icon (the small icons by the clock) is left out: it needs another library per platform and the window does the same job.

*Browser or the app's own window (Q3).* An own window would wrap the same screens in a frame without an address bar (the usual library is pywebview, which uses the web engine the system already has: Edge WebView2 on Windows, WebKit on macOS, WebKitGTK on Linux). It looks more like an app. Against it: the screens are tested only in Chromium, Firefox and WebKit browsers today; WebKitGTK is not installed by default on every Linux desktop; it adds a dependency and a second code path for the session cookie, downloads (exports), links that should open in the real browser, and printing. The browser costs nothing new. The control window keeps the "is it running" question answered either way.

**A second click on the icon** does not start a second engine. The new launcher finds the first one (a small file in the settings folder holding its port and a secret only this user can read), asks it for a fresh one-time link, opens the browser on it, and exits. If the first engine is not answering (it crashed and left the file), the new launcher removes the file and starts normally. *Engine change:* one route, reachable from this computer only and only with that secret, that issues a launch link; it is never in the browser's allowlist.

**Approval codes** (to publish a screening batch) appear in their own window on top of the others, as today (`code_window.py`). With no terminal, that window becomes the only place they appear, so the build must make it work inside the bundle: today it starts `python -I <file>` through `sys.executable` (`code_window.py:115-117`), and in a bundle `sys.executable` is the app itself, not Python. *Engine change:* in a bundle the window is started as the app with a dedicated flag.

**When something goes wrong**, the control window shows a sentence the user can act on, with **Open the log folder** and **Copy the details**:

| What happened | What the window says |
| :-- | :-- |
| Port 8770 is taken | nothing: another free port is used, as today (`launcher.py:47-56`) |
| The engine failed to start | "Nexus Scholar could not start. The details are in the log file. Please send that file to the person who gave you Nexus Scholar." The log names the error. |
| The browser cannot reach the engine (some security programs block local addresses) | "Your browser could not reach Nexus Scholar on this computer. If you use a security program or a company proxy, allow 127.0.0.1." |
| The workspaces folder cannot be written (a cloud folder offline, a full disk) | "Nexus Scholar cannot write to <folder>. Choose another folder in Settings or free some space." |
| The app's files are damaged (the screens are missing) | "This installation is incomplete. Please reinstall Nexus Scholar." |

**The log file**: one per launch, the last five kept, none above 5 MB. It records the version, the system, the port, the workspaces folder and errors. It never holds a key; the e-mail address is masked. *Engine change:* today there is no log file (`launcher.py:147-150` logs to the terminal), and in a bundle with no console the standard output may not exist at all, so the launcher must send output to the file before anything prints.

### 4.3 First-run setup, on a screen

On the first start (no settings file yet) the browser opens **Set up Nexus Scholar** instead of Workspaces. One page, four parts, each saved on its own:

1. **Your e-mail address**, required before any search. "The literature databases ask who is sending requests. Nexus Scholar sends this address to Crossref, PubMed and Unpaywall, and nowhere else." The format is checked; nothing is sent to test it.
2. **Keys (optional)**. The OpenAlex key ("needed to search OpenAlex; free from openalex.org"), the Semantic Scholar key (optional), and an AI provider key ("only for drafts the app asks an AI for; the provider charges you"). Each field is write-only: once saved it shows **Set**, with **Replace** and **Remove**; the key is never shown again or sent to the browser.
3. **Where your reviews are kept**: the folder, with **Change…**. A browser cannot read a folder path from the computer, so **Change…** opens the system's folder dialog on the desktop, from the engine (the same kind of desktop surface as the approval window).
4. **Connect an AI assistant** (optional, §4.4), and **Tell me when a new version is out** (§4.5, Q9).

**Later** skips all of it: the app works, and a search still stops with the existing `MAILTO_NOT_SET` refusal, now pointing at Settings instead of `.env`. The same screen opens later from a **Settings** link on Workspaces and from the control window.

**Where it is stored (Q7).** The e-mail, the folder and the update choice go in `settings.json` in the settings folder (§4.1), readable by this user only. The keys go in the system's keychain, under the name the app already uses (`scholar_agent/keys.py:22`), which the app already reads for AI keys. An environment variable still wins over both, as today, so nothing changes for a user who works from a terminal. On a Linux desktop with no keyring the screen says so and offers to keep the keys in a file only this user can read, after a confirmation.

**Engine changes.** The search settings, the PDF look-up and the MCP server read the settings file and the keychain after the environment (today they read the environment and `.env` in the current folder: `config.py:90`, `scholar_pdf/config.py:65`). New routes: read the settings (which are set, never a key's value), write them, remove a key; desktop only, same origin, like the method amendments. A change takes effect by restarting the server in place, the way a workspace switch already does (`launcher.py:105-137`), so no open tab is lost.

### 4.4 Connect an AI assistant (MCP)

*MCP* is the standard way an AI app (Claude Desktop, Cursor and others) is given tools; Nexus Scholar's MCP server, `scholar-agent`, lets the researcher's own AI read the workspace and write proposals. Recommended for this milestone: **Claude Desktop only** (Q8), on Windows and macOS (Claude Desktop is not published for Linux; to check, §7).

- **Connect Claude Desktop**, on the Settings screen. It writes the `nexus-scholar` entry into Claude Desktop's configuration file, the file `setup-mcp` already writes (`mcp_setup.py:70-99`), merging only that entry and leaving the others alone, as today. Two differences from today: the command is **the MCP program inside the installed bundle** (an absolute path), not `uvx`, which an installer-only machine does not have (§1.2); and a copy of the file is kept beside it before every change. No key is written into the file (the CORE-17 rule): the server reads the keychain and the settings file when it starts.
- **Which workspace.** The entry names one workspace, as today. The button connects the workspace that is open; the screen says "Claude Desktop will work on <title>. To use another review, open it here and press Connect again."
- **What the user sees after.** "Done. Quit Claude Desktop completely and open it again to see Nexus Scholar's tools."
- **Claude Desktop not installed** (its configuration folder is missing): "Claude Desktop was not found on this computer. Install it, open it once, then press Connect again." Nothing is written.
- **Undo.** **Disconnect** removes only the `nexus-scholar` entry. The uninstaller does the same when the entry points at the program it removes (§4.6).
- **The `.mcpb` extension** stays on the release page for users who install with `uv`; the installers do not use it.

The MCP server already reads keys from the keychain and an env file when it starts (`src/scholar_agent/server.py:1883-1886`, `:1908`); Part B adds the settings file to what it reads.

*Engine and app change:* a route that reports the connection (none, connected and to which workspace, Claude not found), and the connect and disconnect writes; the CLI `setup-mcp` keeps working as it does.

### 4.5 Updates

**Recommended (Q9): a notice, and the user installs the new version themselves.** Once a day, if the user allowed it in setup, the engine asks GitHub's public release list which version is newest (beta versions included during the beta). Nothing about the user or their reviews is sent; GitHub sees the computer's address, as any page visit would. When a newer version exists, Workspaces and the control window show "Version <x> is available. What's new · Download". **Download** opens the release page; the user downloads the installer for their system and runs it. It replaces the program and keeps settings, keys and workspaces. The Windows installer asks to stop Nexus Scholar first if it is running. Installing an older version over a newer one warns first.

**Workspaces.** No install, update or uninstall ever opens, moves or deletes a workspace. But a newer version may write new files and fields into a review that an older version does not understand, and today a workspace has no format version (§1.3). This milestone **does not add one**: the project review's item 8 ("a format version on the workspace and a copy made before a newer build first opens it") is its own piece of work. The recommendation (Q11) is to build it **before installers go to outside testers**, because installers make updates easy and silent. Until then the update notice says "Before updating, make a copy of your reviews folder", which is weak.

### 4.6 Uninstall

| | How | Removed | Kept |
| :-- | :-- | :-- | :-- |
| Windows | Settings › Apps › Nexus Scholar › Uninstall | the program folder, the Start-menu entry, the desktop icon, the Claude Desktop entry if it points at this program | workspaces always; settings, keys and logs unless the user ticks "Also remove my settings and saved keys" (unticked by default) |
| Linux | the Software app, or `sudo apt remove nexus-scholar` | `/opt/nexus-scholar`, the menu entry | everything in the user's home folder: a system package never touches it |
| macOS | drag the app to the Bin | the app | everything else |

A **Remove my settings and keys** button on the Settings screen does the same clean-up on every system, for those who want it. Workspaces are never removed by anything in this milestone.

### 4.7 Left out of this milestone

- An app window of its own (unless Q3 is answered the other way), a tray icon, automatic or silent updates, delta updates.
- Store listings: Microsoft Store, winget, Mac App Store, Homebrew, Snap, Flathub.
- Windows on ARM, Linux on ARM, macOS on Intel (Apple stopped selling Intel Macs in 2023; added only if a tester needs it), Linux families other than Debian and Ubuntu (`.rpm` for Fedora: Q4).
- The `extract` extra (Docling, very large; Q10), the command line on the PATH (the `nexus-scholar` program is in the bundle for support, not on the PATH).
- Installs for every user of a shared computer, and deployment by a university IT department (an `.msi` matters there: Q2).
- The phone on the local network (M2), and AI clients other than Claude Desktop (Q8).
- The installer wizard in French and Arabic: English first; the app's screens keep their three languages.
- A workspace format version (Q11 decides whether it comes first, as its own item).

---

## 5. Plan

### 5.1 Order, and why it differs a little from the proposed one

The coordinator proposed: Windows unsigned, Linux, macOS, signing. **Confirmed for the platforms, with two changes.**

1. **The engine and app parts come first** (Parts A and B). An installer that starts the app but leaves the e-mail in a hand-edited file, or prints approval codes to a console nobody sees, fails the request. These parts also help everyone who installs with `uv` today, so they are worth building even if the packaging stalls.
2. **Signing is a track that starts on day one, not a last part.** The work in code is small (a CI step), but the waiting is long: an application to a free programme, or a purchase with identity checks, takes days to weeks. Starting the paperwork early costs nothing and is the only way to have signed Windows installers by the time testers multiply (Q6).

Windows before Linux before macOS stays right: the first testers most likely use Windows; Linux needs no signing; macOS is the hardest to give unsigned (§3.2) and needs a Mac to check on.

| Part | What | Kind | Lane | Effort (one person) | Needs |
| :-- | :-- | :-- | :-- | :-- | :-- |
| **A** | The launcher for an installed app | engine + app text | RELEASE | 4 to 6 days | — |
| **B** | Settings and first-run setup | engine + app (new screen, new routes) | RELEASE | 4 to 6 days | A |
| **W** | Windows installer | packaging + CI | STANDARD | 3 to 5 days | A, B; Q1, Q2 |
| **C** | Connect Claude Desktop | engine + app | RELEASE (writes another program's file) | 2 to 3 days | A, W (the bundled MCP program's path) |
| **D** | Update notice | engine + app | STANDARD | 1 to 2 days | A |
| **L** | Linux package | packaging + CI | STANDARD | 2 to 4 days | W (shares the bundle recipe); Q4 |
| **M** | macOS disk image | packaging + CI | STANDARD | 3 to 5 days | W; a tester with a Mac (the researcher has none, answer 5) |
| **S** | Signing | paperwork, then a CI step per platform | STANDARD | 1 day per platform of CI work; the paperwork waits | Q6 |

The first build that can go to a Windows tester is **A + B + W**; C and D follow before a release is announced to more testers. Total for A, B, W, C, D, L: about 16 to 26 working days; M adds 3 to 5. These are estimates for this codebase and its review practice, not measurements.

**CI costs nothing extra.** The repository is public, and GitHub's standard hosted runners are free for public repositories (GitHub Docs, "About billing for GitHub Actions"). The runners are `windows-latest` (Windows Server 2025), `ubuntu-latest` (Ubuntu 24.04; older images by name) and `macos-latest` (macOS 26 on Apple silicon); Intel macOS runners remain under other names (GitHub Docs, "GitHub-hosted runners"). The installer jobs run on release tags and on demand, not on every pull request, to keep the pull-request checks as they are.

Two pieces of work in other sessions change this milestone: the removal of the parked code from the package (the review's item 10, which would drop scipy, networkx and pyvis and so shrink every bundle) and the workspace format version (item 8, Q11). Neither is part of M13.

### 5.2 The parts

**Part A — the launcher for an installed app** (engine; RELEASE).
- A windowed entry point (`[project.gui-scripts]`), so the app starts with no console on Windows from an installer and also from `uv`.
- The per-user folders of §4.1; the working folder set to the settings folder; output sent to the log file before anything prints.
- The control window (§4.2): Open in browser, Settings, Stop, status, the closing question with the busy check.
- One engine per user: the instance file and the launch-link route of §4.2.
- The approval window started in a way that works inside a bundle.
- The app's text: the messages that send the user to a terminal, a variable or `.env` (§1.2, about 20 messages in three languages) say what to do in the installed app, and keep the command for a terminal user. The engine tells the app how it was started.
- *Definition of done*, each by a test: a second start of the launcher opens a new launch link from the first engine and starts no second server; Stop ends the process and frees the port; a failure at start leaves a log naming the error and shows the message; nothing is printed to a missing standard output; with no settings, the first page is the setup screen. Checked by hand on Windows from a `uv` install with the windowed entry point: no console window appears.

**Part B — settings and first-run setup** (engine + app; RELEASE).
- The screen of §4.3 in three languages; its routes in the browser allowlist (desktop only, same origin); keys write-only; the folder dialog on the desktop; restart in place to apply.
- The search settings, the PDF look-up and the MCP server read: environment first, then the settings file and the keychain. The `.env` in the current folder keeps working for the command line.
- *Definition of done*: a search refused for a missing e-mail succeeds after the e-mail is saved on the screen, with no restart by the user (a test on the discovery route); a key saved on the screen is never returned by any route (a test reads every settings response); an environment variable still wins (a test); the screen passes the accessibility checks and the browser test in both themes.

**Part W — the Windows installer** (packaging; STANDARD).
- The bundle recipe (Q1): two programs in one folder, the windowed app and the console MCP server; the app's screens and the skills included; `ai` and `pdf` extras included (Q10).
- The installer (Q2): per user, Start menu, desktop icon (ticked), the uninstaller of §4.6, the "stop it first" check, the downgrade warning.
- CI: a job on the Windows runner builds the bundle and the installer from the wheel, installs it silently for the current user, starts it in a test mode (no browser), fetches `/healthz` and the first page, stops it, uninstalls it, and checks that a workspace folder made during the test is still there. The release workflow attaches the installer to the GitHub release.
- *Definition of done*, on a clean Windows 11 (Windows Sandbox, which comes with Windows 11 Pro, is a clean machine at no cost): download from the release page, pass the warning of §3, install without an administrator password, start from the Start menu, see the app in the browser and the control window, complete setup, create a review, close, start from the desktop icon, uninstall; the review folder is still there. The size and the time to the first page are recorded.

**Part C — connect Claude Desktop** (engine + app; RELEASE). §4.4.
- *Definition of done*: tests on a fake configuration folder: connect merges only the entry and leaves a copy; disconnect removes only the entry; a missing Claude folder writes nothing; the entry names the bundled program and the open workspace and holds no key. By hand on Windows: Claude Desktop shows Nexus Scholar's tools after a restart (the MCP server answers from the bundle).

**Part D — the update notice** (engine + app; STANDARD). §4.5.
- *Definition of done*: tests with a recorded answer from GitHub: newer, same, older, no network (silent), the check turned off (no request is made); the notice in three languages.

**Part L — the Linux package** (packaging; STANDARD).
- The same recipe, built on the oldest supported Ubuntu runner so the bundle runs on newer systems too; the `.deb` with its menu entry and icon (Q4).
- CI: install in clean Ubuntu 22.04, 24.04 and Debian 12 containers, start in test mode with a virtual display, fetch the first page, remove the package.
- *Definition of done*: on a clean Ubuntu 24.04 desktop (a virtual machine or a tester), install by double-click, start from the menu, setup, a review, remove; the review stays.

**Part M — the macOS disk image** (packaging; STANDARD).
- The same recipe as an app bundle for Apple silicon, in a `.dmg`; marked "ad hoc" signed (a free, local signature Apple silicon requires to run any program; it does not satisfy Gatekeeper, §3.2).
- CI: on the macOS runner, mount, copy, start in test mode, fetch the first page.
- *Definition of done*: on a Mac that never had Nexus Scholar: download, pass §3.2, open, setup, a review, Bin; the review stays.
- **The researcher has no Mac (answer 5, 2026-11-23).** Part M can therefore only be built and smoke-tested in CI (the steps above, on the macOS runner); its definition of done waits for a tester with a Mac who is willing to try an unsigned app. Until then a macOS `.dmg` is not offered to testers as checked, and Mac users keep the `uv` install.

**Part S — signing** (STANDARD). §3 and Q6. Windows: apply to the free programme for open-source projects once one installer is released (answer 6); if accepted, a CI step signs the installer and the programs in it. macOS: only once a Mac tester exists and the yearly fee is approved; then signing and notarization in CI. Linux: nothing to sign for a `.deb` opened from a file.

### 5.3 Risks

| Risk | Effect | What reduces it |
| :-- | :-- | :-- |
| Antivirus programs flag unsigned bundles made with PyInstaller (a known pattern, §2) | the installer or the app is deleted or blocked on a tester's machine | signing (Part S); submitting each release to Microsoft's free false-positive review; building PyInstaller's starter program from source |
| Problems that exist only inside a bundle: no standard output, `sys.executable` is the app, data files and package version information not collected | the app starts on the CI runner but not for a user | Part A handles the first two; the CI install test of each part starts the real installed program, not the wheel |
| The Windows Documents folder is often synced by OneDrive | file locks while syncing; a review open on two computers | the existing Windows replace retry (M6-hardening); a sentence in setup when the folder is under OneDrive |
| University networks with proxies or blocked addresses | searches fail; the update check fails | the existing refusals name the database; the update check fails silently |
| The Linux keyring is missing on some desktops | keys cannot be stored safely | the file fallback of §4.3, after a confirmation |
| Bundle size (§2.4) | a slow download for testers on slow lines | measure first (Q12); drop the parked dependencies (review item 10) |
| Maintenance for one person | three installer jobs to keep green; each release takes longer in CI | one recipe shared by the three platforms; the installers built only on tags and on demand, not on every pull request |
| A newer build changes a real review | data loss or confusion for a tester | Q11 |

---

## 6. Questions closed (2026-11-23)

Asked in the coordinator session on 2026-11-23, one by one; each answered as recommended. Decision: `docs/decisions.md`, "2026-11-23 — M13-installers". The answers settle the design; they do not start the build, which needs the researcher's separate go.

1. **How the installers are built.** *Answer (as recommended):* **PyInstaller one-folder bundles with one installer builder per platform** (§2.2, §2.5). *Not chosen:* Briefcase (no Tk on Windows and macOS, so the approval window would have to be rewritten first; one Linux build per distribution release); the light installer that installs `uv` and then the wheel (needs the internet at install, and installs what PyPI serves that day). *Known cost:* three small configurations to keep; antivirus suspicion until signed; bundle-only faults that only an installed test catches (§5.3).

2. **Windows: a `setup.exe` or an MSI.** *Answer (as recommended):* **`setup.exe` made with Inno Setup**, per user, no administrator password. *Not chosen:* an MSI made with WiX (what IT departments deploy; per-user MSIs are possible but fussier; WiX asks a maintenance fee of revenue-making users above US$10,000 a year); both (twice the testing). *Known cost:* the request said "MSI"; a university that deploys only MSIs cannot use the `.exe`. The choice can be revisited later without changing the bundle.

3. **The user's browser, or the app's own window.** *Answer (as recommended):* **the user's default browser, plus the small control window** (§4.2). *Not chosen:* an own window with pywebview (looks more like an app; uses Edge WebView2 on Windows, present on Windows 11; WebKitGTK on Linux, not always installed; the screens are not tested in those engines; downloads, links and printing need work). *Known cost:* the app lives in a browser tab, which a user can close or lose among other tabs; **Open in browser** in the control window brings it back.

4. **Linux formats.** *Answer (as recommended):* **a `.deb` only** for Ubuntu and Debian, built once for several releases. *Not chosen:* also an `.rpm` (Fedora; nearly free with nFPM, but untested without a Fedora tester); an AppImage (no install, but Ubuntu 22.04 and later need a terminal command to add `libfuse2` first, §2.2); Flatpak (needs Flatpak set up, a runtime, and Flathub's review to be easy). *Known cost:* a `.deb` asks for the computer's password and installs for every user; Fedora users wait.

5. **The order of platforms.** *Answer (as recommended):* **Windows, then Linux, then macOS**, after the engine and app parts A and B (§5.1). *Not chosen:* macOS earlier (only if a first tester uses a Mac; it is the hardest to run unsigned); all three at once (three faults to chase at the same time). *Known cost:* Mac users keep the `uv` install longer. *Is there a Mac the researcher can use?* **"No Mac."** So Part M is built and smoke-tested in CI only, and its definition of done waits for a tester with a Mac (§5.2).

6. **Signing and spending.** *Answer (as recommended):* **zero spend now**: unsigned Windows builds with an illustrated guide; apply to the SignPath Foundation programme as soon as one installer is released; no macOS signing until a Mac tester exists (§3.4). *Not chosen:* the Certum open-source set at €69 now (signed under the researcher's own name; identity checks; renewal cost to check); a commercial certificate (US$150 to 300 a year and a hardware token); Microsoft's Artifact Signing (individuals outside the US and Canada are not eligible); the Apple Developer Program now (US$99 a year; enrolment from Algeria not confirmed). *Known cost:* first testers click through warnings, and some must switch off Smart App Control; SignPath may refuse or take weeks, and if it accepts, Windows names "SignPath Foundation" as publisher.

7. **Where settings and keys are kept.** *Answer (as recommended):* **e-mail, folder and update choice in a settings file in the user's settings folder; keys in the system keychain**, environment variables still first (§4.3). *Not chosen:* everything in one settings file (simpler, but keys in a file, against the spirit of the CORE-17 rule); a `.env` in a fixed folder (the current format, but a hand-edited file and keys in plain text). *Known cost:* a Linux desktop without a keyring needs the file fallback after a confirmation; three places to look when supporting a tester.

8. **Which AI clients the Connect button covers.** *Answer (as recommended):* **Claude Desktop only**, on Windows and macOS (§4.4). *Not chosen:* also Cursor and VS Code (their configuration files sit inside each workspace, and their users are comfortable with a terminal); Claude Code (a command-line tool); ChatGPT or others (not checked for local MCP support). *Known cost:* a researcher using another client follows the guide's `setup-mcp` section.

9. **How updates reach the tester.** *Answer (as recommended):* **a daily check of GitHub's public release list, on by default and switchable in setup and Settings; a notice with a Download link; the tester runs the new installer** (§4.5). *Not chosen:* no check at all (testers stay on old builds without knowing); the check off by default (most never turn it on); an automatic updater (signing becomes mandatory, since an unsigned self-updating program is what antivirus programs block first; much more code). *Known cost:* one request a day to GitHub from each tester's computer; the tester still downloads and installs by hand.

10. **What the bundle carries.** *Answer (as recommended):* **the base install plus the `ai` extra (keychain, Anthropic) and the `pdf` extra (PyMuPDF)**. *Not chosen:* the base only (no keychain, so keys could not be set on the screen; no PDF text); everything including `extract` (Docling brings machine-learning models of hundreds of megabytes, for the parked extraction). *Known cost:* PyMuPDF adds roughly 40 to 60 MB (estimate); the bundle carries scipy until the parked code leaves the package.

11. **The workspace format version: before or after the installers.** *Answer (as recommended):* **build the project review's item 8 (a format version on each workspace and a copy made before a newer build first opens it) before installers go to outside testers**, as its own piece of work. *Not chosen:* ship installers first and add it later (the risk lands on the first testers' real reviews); fold it into M13 (a contract-level change inside a packaging milestone). *Known cost:* the first tester build waits for that item (an estimate of S to M in the review).

12. **A trial build to measure size and start time.** *Answer (as recommended):* **yes, on this PC, before Part W starts**: PyInstaller in a throw-away environment (never in the project's), one Windows bundle from the current wheel with the `ai` and `pdf` extras, its size and time to the first page recorded, tried in Windows Sandbox; nothing committed except the numbers in this file. About two hours. *Not chosen:* measure only in CI once Part W is built (no early warning about size or antivirus); no measurement (the estimates of §2.4 stand). *Known cost:* one more tool downloaded to this PC, from PyPI, into a folder deleted afterwards.

---

## 7. Not verified

Nothing in this specification was built or tried. In particular:

- **No bundle was made.** Every size and start-time figure in §2.4 and §4.1 is an estimate from the libraries' usual sizes. Whether PyInstaller collects this project correctly (the app's screens under `scholar_harness_data`, the skills, package version information, uvicorn's and the MCP library's dynamic imports) is not checked.
- **Tk inside a bundle** on each platform, and in `uv`'s private Python, rests on the presence of PyInstaller's hook file and a search snippet, not on a run.
- **Smart App Control**: whether it blocks only the installer or each unsigned program and library inside the installed folder; whether the Python libraries that are already signed by their publishers help. Not tested.
- **Antivirus** behaviour on a PyInstaller bundle of this project: not tested.
- **Briefcase**: that Windows and macOS packages must be built on their own systems is implied by its pages, not stated; that no end-user updater or single-instance feature exists was not confirmed.
- **WiX's maintenance-fee terms** come from a search snippet, not the opened page.
- **Inno Setup per-user paths** (`%LOCALAPPDATA%\Programs\…` and the per-user Start menu with `PrivilegesRequired=lowest`) are its usual behaviour, not read on its pages.
- **The `.dmg` tools** (`hdiutil`, `create-dmg`) were not read.
- **The `uv` tool install of a windowed entry point** (that `[project.gui-scripts]` becomes a program with no console on Windows) was not checked in `uv`'s documentation.
- **Linux:** that a downloaded `.deb` needs no signature, and which desktops lack a keyring, were not confirmed by a source.
- **Claude Desktop**: its configuration path on Windows when installed from the Microsoft Store or as an MSIX package (it may differ from `%APPDATA%\Claude`); that there is no Linux version; that it picks up the MCP program from a bundle path with spaces in it. Not checked. `setup-mcp` writes the same `mcpServers` shape for the VS Code target as for the others (`mcp_setup.py:186-194`); whether VS Code reads that key was not checked (only relevant if Q8 widens the button).
- **Apple enrolment from Algeria** and **Certum's validity period and renewal price** were not confirmed.
- **SignPath Foundation's terms** were read on a page marked as a draft.
- **Microsoft's false-positive submission portal** was not opened.
- **The ~60 lines of app text** that mention a terminal, a variable or `.env` were counted by a word search, not read one by one.
- **Effort figures** in §5 are judgements, not measurements.
- **What a tester sees in the browser** (e.g. a "not commonly downloaded" warning in Edge or Chrome) was not checked.
- **Double-clicking a `.deb` on Ubuntu 24.04** opens the App Center, whose handling of local `.deb` files has varied between releases; not checked.
