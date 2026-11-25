# H-b8-small-faults The app's icon on its windows, two harmless log lines, the contact e-mail wording, documentation follow-ups
Branch: dev/h/b8-small-faults · Lane: **STANDARD** · Status: **MERGED** 2026-11-25 (PR #317, merge commit `d60f2ef3`; CI on head `05ea7316`: 12 checks passed, 1 skipped; independent review rounds 1 and 2 APPROVE, repairs made) · Started: 2026-11-25

Base: `origin/main` at `1985267b` (the released 1.1.0b8). Source: the coordinator's test of the installed 1.1.0b8 on this PC on 2026-11-25 (two faults named in the release note's known limits, `docs/releases/1.1.0b8.md`, which is not edited here), a wrong sentence on the Settings screen, and documentation found stale during the release. The researcher's words (2026-11-25): "Fix all remaining problems". No live request to a literature database, no AI spend, the app was not started on the real folders, the version is unchanged.

**Lane.** STANDARD, from `docs/architecture/test_gate_policy.md`: bounded behaviour changes in one package (`scholar_harness.console`, plus one refusal message in `scholar_harness.charting.fetch`), four UI strings in three languages and documentation. No public HTTP route, CLI flag, MCP tool, Contract v1 model, schema or fixture changes. The baseline-locked files are untouched (`generate_contract_baseline.py --check`: current).

## Definition of done
- [x] **1. The app's icon.** The control window, the approval-code window and the folder dialog set the app's icon in a wheel install and in the bundle; a refused or missing icon never stops a window.
- [x] **2. Log noise.** The two harmless lines leave the log and the terminal; everything else is still logged; the filters survive uvicorn's own logging set-up in both starts.
- [x] **3. The Settings e-mail sentence.** True in English, French and Arabic, traced to the code; `docs/data-flow.md` agrees with the code.
- [x] **4. Documentation follow-ups.** Each checked against the code at `1985267b`; changed only where wrong.
- [x] **5. Record and decisions.** This file; `docs/decisions.md` "2026-11-25 — H-b8-small-faults", every choice PROPOSED.

## What changed

### 1. The app's icon on its three Tk windows
- `src/scholar_harness/console/nexus-scholar.ico` (new): a byte-identical copy of `packaging/icons/nexus-scholar.ico`. It sits in the package, so hatch puts it in the wheel (the wheel ships every file under `src/scholar_harness`) and the PyInstaller recipe already collects it (`collect_data_files("scholar_harness")` in `packaging/windows/nexus-scholar.spec`; no `datas` entry is needed). It is read from beside the module (`Path(__file__)`), which works in both.
- `src/scholar_harness/console/window_icon.py` (new, standard library only): `ICON` and `set_icon(root)`. `root.iconbitmap(default=…)` on the window's root; a missing file or any Tk refusal (`tk.TclError` on Linux and macOS, where Tk takes no `.ico`) returns `False` and the window opens with Tk's own icon. Whether the native message boxes the control window opens show the icon was not checked.
- `src/scholar_harness/console/control_window.py`: imports `ICON` and `set_icon` from it and calls `set_icon` after the title.
- `src/scholar_harness/console/code_window.py` (approval codes) and `folder_dialog.py`: `_app_icon(root)` after the title or `withdraw()`. They run as `python -I <file>` outside the bundle (standard library only, and `-I` keeps their folder off `sys.path`), so there they load `window_icon.py` from beside them by its path; in the bundle (`--approval-window`, `--choose-folder`) they import it. Any failure returns `False`.
- `packaging/icons/make_icon.py`: writes the run-time copy too. `tests/test_windows_packaging.py::test_the_control_window_icon_is_the_same_file_as_the_installer_icon` fails if the two files differ.
- Tests: `tests/console/test_control_window.py` (the icon is package data and is handed to Tk; a `TclError` or a missing file returns `False`; a real Tk window whose `iconbitmap` raises still builds; real Tk takes the real `.ico` on Windows, `assert ... is True`); `tests/console/test_window_icon.py` (new, 14: each child window gets the icon in the bundle and as a script, a refusing Tk or a missing helper returns `False`, the helper a script loads imports no `scholar_*` package under `python -I`, the control window uses the same helper, real Tk takes the icon in each child on Windows, and both child files still import the standard library only). Real-Tk tests are skipped without Tk or a display.

### 2. Log noise
- `src/scholar_harness/console/log_noise.py` (new): two `logging.Filter`s and `install()`, which adds each once.
  - On the `asyncio` logger: a record is dropped only when its exception is a `ConnectionResetError` or `ConnectionAbortedError`, the innermost frame of its traceback is `_call_connection_lost` (the socket's `shutdown` there is a C call), and it carries no `__context__` and no `__cause__`. The message is not consulted, so a record without a traceback is kept.
  - On the `uvicorn.error` logger: a record is dropped only when its message is exactly "Cancel 0 running task(s), timeout graceful shutdown exceeded" (uvicorn 0.52.4, `server.py:294`, logged with `%s` and the count).
- `src/scholar_harness/console/launcher.py` `_uvicorn_server`: `log_noise.install()` after `uvicorn.Config(...)` (whose constructor runs uvicorn's logging set-up), for every server, restarts included. A logger's filters see the records created on it; `dictConfig` replaces a named logger's handlers but keeps its filters; the terminal start (uvicorn's default `log_config`) and the no-console start (`log_config=None`) both go through this function.
- Tests (`tests/console/test_log_noise.py`, 6): the noise records are dropped (from a real event loop's exception handler, with WinError 10054 and 10053, and through a transport-shaped `_call_connection_lost` whose `finally` resets; a hand-made record from a real raise; the exact uvicorn line). These pass: an unrelated `asyncio` error; a reset raised in another callback; a protocol `RuntimeError` followed by a reset in `finally` (kept, with the `RuntimeError` as its context); a reset raised inside the protocol's `connection_lost`; the callback's name in a message with no traceback; a non-reset exception in `_call_connection_lost`; "Cancel 2 …" and "Cancel 10 …"; a reset logged from another logger. `install()` is idempotent; every test that installs the filters removes them again (`kept` fixture); the filters are in place after `_uvicorn_server` with the default `log_config` and with `log_config=None`, and after `config.load()`.

### 3. The Settings e-mail sentence

Where the address goes, traced in the code at `1985267b`:

| Path | Hosts | Evidence |
| :-- | :-- | :-- |
| User-Agent of the shared search client `AcademicHttpClient` | every host it talks to: `api.openalex.org`, `api.semanticscholar.org`, `api.crossref.org`, `export.arxiv.org`, `eutils.ncbi.nlm.nih.gov`, `api.biorxiv.org` (search, recall, Explore, hydration, DOI verification, citation chasing; Charting's arXiv and lookup clients) | `src/scholar_search/http_client.py:103-104` (`user_agent`), `:382`, `:393`, `:399`; providers build it at `src/scholar_search/providers/base.py:50`; base URLs in `providers/*.py`; `src/scholar_search/enrichment.py:18-19`; `src/scholar_harness/charting/fetch.py:712-721` |
| PubMed `email` parameter | `eutils.ncbi.nlm.nih.gov` | `src/scholar_search/providers/pubmed.py:74-76`, `:184-186` |
| Unpaywall `email` parameter and User-Agent | `api.unpaywall.org` | `src/scholar_pdf/downloader.py:600-605` |
| OpenAlex lookup in the PDF path (only with its key) | `api.openalex.org` (User-Agent; no `mailto` parameter) | `src/scholar_pdf/downloader.py:591-605`; `src/scholar_search/providers/openalex.py:172-173` |
| **PDF download User-Agent** | **every site that holds a listed open-access PDF (publisher or repository, arXiv, PMC, …) and every site it redirects to** (at most five redirects from Charting; aiohttp keeps the header across redirects) | `src/scholar_pdf/config.py:94-98` (`user_agent`, always `(mailto:<address>)`), used at `src/scholar_pdf/downloader.py:500-502` in `download_pdf`; called for each listed copy at `:918`; Charting's look-up (`src/scholar_harness/charting/fetch.py`) and `scholar-pdf download`/`ingest` |
| Not sent | AI providers (`src/scholar_agent/drivers/`, `src/scholar_search/screening.py`); `src/scholar_pdf/acquisition.py` uses its own User-Agent without the address | grep of `mailto`/`user_agent` |

The behaviour is unchanged. The new sentence (key `settings.email.help`, `apps/research-ui/lib/settings-copy.ts`; the FINAL spec `docs/ux/shared/final/05-settings.md` follows):
- en: "The literature databases ask who is sending requests. Nexus Scholar sends this address to the literature databases, to Unpaywall, and to the websites it downloads open-access PDFs from."
- fr: "Les bases bibliographiques demandent qui envoie les requêtes. Nexus Scholar envoie cette adresse aux bases bibliographiques, à Unpaywall et aux sites web d'où il télécharge des PDF en libre accès."
- ar: "تسأل قواعد البيانات العلمية عمّن يرسل الطلبات. يرسل Nexus Scholar هذا العنوان إلى قواعد البيانات العلمية وإلى Unpaywall وإلى المواقع التي ينزّل منها ملفات PDF مفتوحة الوصول."

No test pinned the old sentence. `docs/data-flow.md` now says that Charting's look-up also writes the address into its run file and the journal's start event (`charting/fetch.py:803`, `:820` in this tree, `:802`, `:819` at the base; the plan at `:572` only returns it to the screen), lists citation chasing and the open-access look-up and download, names the PDF sites, and drops two wrong claims ("as `mailto` to OpenAlex"; "the Explore screen is not built"). The user guide's `SCHOLAR_MAILTO` row said a search sends OpenAlex no address; it is in the User-Agent, and the row now says so.

### 4. Documentation follow-ups
| Item | Verdict | Change |
| :-- | :-- | :-- |
| User guide: a review "last opened by a newer version is not opened by an older one" | **Wrong.** `workspace/format.py:174-178` refuses only a format above `CURRENT_FORMAT`; an older build with the same format opens it (`tests/unit/test_workspace_format.py:421`) | Reworded: only a newer format is refused; a review last opened by a newer version that stores reviews the same way opens as usual |
| `docs/data-flow.md`: Recall "(on `main`)" | **Wrong.** Recall shipped in 1.1.0b6 (`docs/releases/1.1.0b6.md`) | "(since 1.1.0b6)" |
| Troubleshooting text about the contact e-mail does not say Settings applies it with no restart | **Wrong** (`docs/getting-started.md` troubleshooting: "then start the app again"). `console/api/settings.py:124-133` saves and calls `reload_settings`, which updates the shared settings in place (`scholar_search/config.py:135-145`) | `MAILTO_NOT_SET` and `OPENALEX_KEY_NOT_SET` rows, and the Discovery paragraph of step 4, point to Settings ("applies at once, with no restart"); an environment or `.env` value still needs a restart and wins over Settings |
| `docs/beta/README.md`: "No full-text screening" | **Wrong.** Charting (since 1.1.0b7) holds a full-text decision per study, Attach a PDF, the open-access look-up, and the charting form filled by hand | The known-limit line now says what Charting does and what it does not (it extracts nothing from a PDF's text, apart from the look-up's identity check on the first two pages; no synthesis) |
| `docs/getting-started.md`: accepting under Import; Explore and Direction | **Wrong** on three counts: the corpus is accepted only on the Hand-off (`components/screening-import.tsx:22-24`); Explore and Direction have screens (`app/[locale]/inception/explore`, `…/direction`; step order `lib/inception-api.ts:398`); a harvest and exports are combined on the Hand-off (`lib/discovery-copy.ts:370`) | Inception steps 1-7 with Explore and Direction (with "Write my own direction" and "Continue without a direction"); Import step 3 is "Accept on the Hand-off"; Discovery step 4 says exports are combined with the harvest |

### 5. The restart wording (after the review)
- `apps/research-ui/lib/discovery-copy.ts` `mailto.where` and `openalexKey.where`, and `apps/research-ui/lib/charting-copy.ts` `charting.refusal.MAILTO_NOT_SET` (the terminal start's words; three languages each): Settings first ("applies at once"), then the environment line with its restart. Tests that pinned them: `tests/discovery-plan.test.tsx`, `tests/charting.fetch-i18n.test.ts`, `tests/charting.fetch-plan.test.tsx`. The FINAL specs that quote them follow (`docs/ux/phase1-discovery/final/01-plan.md`, `02-recall.md`, `03-harvest.md`, `09-chase.md`, `docs/ux/phase3-extraction/final/03-fetch-states.md`).
- `src/scholar_harness/charting/fetch.py` `require_mailto`: "... Save it on the Settings screen (it applies at once), or set SCHOLAR_MAILTO for the console (environment or .env) and start it again." No test pinned it.
- Not changed (decision item 11): the same "start it again" in `console/api/discovery.py:285`, `:299`, `console/api/recon.py:202`, `recon/session.py:372`, `:524`; and the FINAL specs `docs/ux/phase0-inception/final/02-explore.md:106` and `docs/ux/phase1-discovery/final/07-states.md:51`, whose words the screens no longer use (`lib/screening-states.ts` already says "Add it in Settings").

### 6. Stale OpenAlex `mailto` claims (after the review)
`docs/kits/search/README.md:42`, `docs/kits_surface_matrix.md:220` and `.agents/skills/scholar-search-kit/references/providers.md:28` said the code sends `mailto` to OpenAlex (or "Crossref, OpenAlex and NCBI"). None is baseline-locked (`contract_v1_baseline.json` names none of them). Corrected to the trace above. `uv run python scripts/sync_skills_bundle.py scholar-search-kit` copied the skill into the bundle: `.agents/plugins/nexus-scholar/skills/scholar-search-kit/references/providers.md` changed, nothing else.

## Independent review
Round 1 on the first working tree: **APPROVE with repairs before the commit.** All repairs made on the same tree:

| # | Finding | Done |
| :-- | :-- | :-- |
| 1 | P2: the asyncio filter was wider than claimed (a reset in `finally` after a protocol error, a reset inside the protocol's `connection_lost`, and the message alone were dropped) | Drop only when the innermost frame is `_call_connection_lost` and `__context__` and `__cause__` are both None; the message is not read. Both cases and a no-traceback record added to the pass-through test; the dropped hand-made record now comes from a real raise. Docstring and decision item 4 say exactly this |
| 2 | P2: no test asserted that real Tk accepts the real `.ico` | `test_real_tk_takes_the_real_icon`: on Windows `set_icon(root) is True`; likewise for each child window |
| 3 | P2: the beta page said the app does not read a PDF's text (the look-up's identity check reads the first two pages, `scholar_pdf/identity.py:69-88`) | Reworded: the app extracts nothing from a PDF's text; the look-up only checks that the DOI or the title's words are on a fetched file's first two pages; no synthesis |
| 4 | P3: guard `record.getMessage()` in the asyncio filter | The filter no longer calls it (finding 1); the uvicorn filter keeps its guard |
| 5 | P3: "default= also gives the icon to the closing question" is unverified | Dropped in the code, this record and decision item 2 (now named as not checked) |
| 6 | P3: Direction also offers "Write my own direction" and "Continue without a direction" | Added to Getting started, step 3 |
| 7 | P3: a test left a filter on the process-wide loggers | It uses the `kept` fixture |
| 8 | P3: `root.destroy()` not in `finally` | `try/finally` |
| 9 | (coordinator) the approval-code window and the folder dialog | Same icon through `window_icon.py`; decision item 3 updated |

The coordinator's further items 10 to 13 are sections 5 and 6 above and the data-flow sentence in section 3. The reviewer's list of what it did not verify (as relayed): the icon in a real bundle and on a real title bar, the filters against a real browser disconnect, the screens in a running app; none of these was done here either (below).

Round 2 on the repaired tree (only what changed since round 1): **APPROVE**, one P2 and three P3. All eight round 1 repairs confirmed; the reviewer ran both child-window files under `python -I` with a real Tk root (icon set, no `scholar_*` module loaded) and confirmed that an OpenAlex key saved on the Settings screen applies with no restart. Repaired by the coordinator on the same tree:

| # | Finding | Done |
| :-- | :-- | :-- |
| 1 | P2: `docs/ux/phase1-discovery/final/09-chase.md` quoted the contact e-mail sentence under the OpenAlex key (two places) | The key's own words, as in `apps/research-ui/lib/discovery-copy.ts` |
| 2 | P3: the "Contact email" prose of `docs/ux/phase1-discovery/final/01-plan.md` still quoted the old words | Brought in line with the copy table |
| 3 | P3: the standard-library import check did not cover `window_icon.py` | Added to the parametrised check in `tests/console/test_window_icon.py` |
| 4 | P3: `if __package__:` in the two child-window files relies on an attribute Python plans to retire | **Not changed.** If it goes, the error is caught, the windows open without the icon, and the Windows real-Tk tests fail and show it |

After these: `pytest tests/console/test_window_icon.py tests/console/test_approve_all.py -n 4`: 45 tests, 0 failures, 0 skipped (junit); `git diff --check` clean. The round 2 reviewer did not re-run `tsc`, `lint:ui`, the full web suite or the full Python suite; the gate table below is the builder's run before these three small repairs.

## Gates
All on the uncommitted working tree of `dev/h/b8-small-faults` (base `1985267b`), 2026-11-25, Windows 11, Python from the project venv. Counts read from `--junitxml` files. The final run is after the review's repairs.

| Stage | Command | Result |
| :-- | :-- | :-- |
| selector | `uv run python scripts/select_test_gate.py --changed origin/main --stage pr` | areas `console-charting,windows-packaging,console,research-ui`, task T-150; the commands below |
| inner | `uv run pytest tests/console/test_log_noise.py tests/console/test_window_icon.py tests/console/test_control_window.py tests/test_windows_packaging.py -m "not slow"` | 49 tests, 0 failures (one failure on the first try: the hand-made `_ProactorBasePipeTransport` message also matched the test's `Transport.` selector; the test now matches the message's start) |
| pr, first try | `uv run pytest tests/console tests/authority tests/test_ui_launcher.py tests/test_windows_packaging.py -q -n 4 --dist worksteal` | 1 526 tests, **1 failure**: `tests/console/test_approve_all.py::test_review_the_window_script_imports_the_standard_library_only`. The approval-code window's relative `from .window_icon import set_icon` is an import of the package in a file that must import the standard library only. Repaired: in the bundle the helper is imported by name (`importlib.import_module`), as a script it is loaded by path; a test for both child files was added (`test_window_icon.py`) |
| pr | the same command, after the repair | **1 528 tests, 0 failures, 0 errors, 2 skipped**, exit 0 |
| pr | `uv run pytest tests/conformance tests/unit/test_select_test_gate.py -q -n 4` (T-150; the bundled skill changed) | 671 tests, 0 failures, 3 skipped |
| pr | `uv run pytest tests/test_windows_packaging.py tests/console/test_desktop_start.py`, `tests/console tests/test_windows_packaging.py -q` | covered by the run above (both folders in it) |
| pr | `npm --prefix apps/research-ui run typecheck` | exit 0 |
| pr | `npm --prefix apps/research-ui run lint:ui` | 1 file, 76 tests passed |
| pr | `uv run python scripts/suite_lock.py -- npm --prefix apps/research-ui test` | 120 files, 1 395 tests passed |
| docs | `uv run pytest tests/conformance/test_count_freshness.py` | 4 tests, 0 failures |
| lint | `uv run ruff check scripts/`; `uv run ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9` | both clean (and the new files under the full rules) |
| contract | `uv run python scripts/generate_contract_baseline.py --check` | "Contract baseline current"; nothing regenerated |
| checks | `generate_protocol_schema.py --check`; `sync_skills_bundle.py --check` (after `sync_skills_bundle.py scholar-search-kit`); `select_test_gate.py --check`; `check_workflows.py`; `uv lock --check`; `git diff --check` | in sync; OK; OK (11 tasks, 24 areas, 4 stages); OK (4 workflows); exit 0; clean |
| wheel (first round) | `NEXUS_WHEEL_ALLOW_NO_UI=1 uv build --wheel --out-dir <scratch>` | the wheel holds `scholar_harness/console/nexus-scholar.ico` and `log_noise.py`; not rebuilt after the review (`window_icon.py` is a module beside them) |

The full Python suite was not run (CI runs it).

## Decisions
See `docs/decisions.md`, entry "2026-11-25 — H-b8-small-faults": items 1 to 7, 9 and 10 ACCEPTED 2026-11-25 ("Accept all nine"); item 8 ACCEPTED as built ("Keep, now disclosed"); items 11 ("Correct in a follow-up") and 12 ("Stop storing it") decided the same day and built in the follow-up below.

## Follow-up
`dev/h/b8-followups` (from `d60f2ef3`, record `docs/roadmap/milestones/H-b8-followups.md`) builds the researcher's answers to items 11 and 12 of 2026-11-25: the five engine messages named in section 5 and the two FINAL specs now name the Settings screen first; the look-up records `contact_email_set` instead of the address in its run file and the journal's start event, and `docs/data-flow.md` says so.

## Not verified
- **The icon in the real installed app.** Not built or installed here; the bundle's copy relies on `collect_data_files("scholar_harness")` collecting a non-Python file beside a module, which is that function's documented behaviour, not something run. On Windows the real-Tk test sets the real `.ico` on a withdrawn window; nobody looked at a title bar. The approval-code window and the folder dialog were not opened as real children (`python -I` or the bundle's flags); their loader was tested in-process and its standard-library-only load in a `python -I` subprocess. Whether the native message boxes and the native folder dialog show the icon was not checked.
- **The log filters against a real browser dropping a connection on Windows.** The `asyncio` record is produced by a real event loop's exception handler with a function of the same name, not by the proactor transport and a browser; the uvicorn line is logged by hand with the exact format string of uvicorn 0.52.4. A later uvicorn that rewords the line would make it reappear (harmless).
- **The changed words on screen.** The strings were changed and the UI checks ran; the Settings, Discovery and Charting screens were not looked at in a running app (light, dark, Arabic, phone width).
- **The full Python suite** was not run (CI runs it); the areas the selector named were.
