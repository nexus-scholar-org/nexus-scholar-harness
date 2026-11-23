# H-faster-python-tests Cut the Python suite's fixed costs

Branch: `dev/h/faster-python-tests` · Lane: **STANDARD** (test code and one lazy import; no contract, product behaviour or public surface changes) · Status: **READY FOR PR** (review round 2 APPROVE; not pushed; stacked on Part 1)

**Stacked on Part 1.** Cut from `dev/h/remove-rag-verify` at `58468929` (H-remove-rag-verify, READY FOR PR, not merged), on the coordinator's instruction of 2026-11-23, so that nothing here measures or reworks tests Part 1 deletes, and the "before" numbers are the suite as it will be. It is to be rebased on `main` once Part 1 merges. A first start from `origin/main` (measurements only, no code) was dropped.

The researcher's decision of 2026-11-23 in the coordinator session, from the test-suite review of that day (`docs/assessment/test-suite-review-2026-11-23.md`, step 3, points 1 to 4).

## What changed

**(a) The orchestrator is imported when first used.** `src/scholar_harness/__init__.py` no longer imports `orchestrator` at the top: `scholar_harness.ResearchOrchestrator` resolves through a module `__getattr__`. The orchestrator pulls in the PDF and search kits, networkx, pypdf and aiohttp. `src/scholar_harness/cli.py` does the same (`_orchestrator_class()`; `cli.ResearchOrchestrator` still resolves and can be patched, as `tests/unit/test_cli_pipeline_summary.py` does), which also makes the product's own command start faster.

**(b) Workspace templates.** `tests/support/workspaces.py`: `copy_of(key, build, tmp_path)` runs a builder once per process (one pytest-xdist worker) under a private temporary root, checks that nothing in the result records that root's path (a builder that writes an absolute path fails there instead of handing tests paths into another folder), and copies the whole folder into each test's `tmp_path` (`shutil.copytree`, contents and modification times kept). Applied to the three builders the console tests call most, each keeping its signature, with the original renamed `*_fresh`:

| Builder | Key | Callers (files) |
| :-- | :-- | --: |
| `tests/test_screening_events.py::_build` (a prepared workspace) | batch size, method block, protocol file content | 25 call sites |
| `tests/console/test_screening_api_v1.py::_workspace` | `prepare`, protocol file content | 72 call sites |
| `tests/console/test_export_api.py::published_workspace` (a published screening) | protocol file content | 9 files |

The key holds every input the build reads: four fixtures or helpers patch `PROTOCOL` before building (`test_charting_export_api.py`, `test_charting_form_api.py`, `test_screening_drafts_api.py`, `test_screening_highlights.py`), so the protocol file's content is part of the key and such a test gets its own build (a scan of every test that patches something before calling a builder found no other input the builders read); `WS_ID` and `SCREENER`, module globals the builders also read, are in the keys too (review finding 4). The read store keys kept results by absolute workspace path, so copies never share one. **What a copy shares that fresh builds would not:** the "now" stamps of the build and its random ids (`uuid4` event ids, and the generation ids and file names that follow from them): a review rebuild found 14 of 23 files of a published workspace differ between two fresh builds. No test relies on two workspaces having different ids. A failed build leaves its own folder (`tempfile.mkdtemp`), so it cannot turn later calls into `FileExistsError`. `tests/console/_record_page_engine.py`, run directly rather than by pytest, now puts `tests/` on `sys.path` for `support`.

**(c) Command-line tests in process.** `tests/kits/protocol/test_cli.py` runs the 23 command tests through `typer`'s `CliRunner` with the same three fields a process gives (`returncode`, `stdout`, `stderr`), including the commands that write bytes to `sys.stdout.buffer` and the Rich diagnostics on stderr. An uncaught exception is re-raised with its traceback rather than reported as exit code 1, so a crash cannot pass as an expected refusal (stricter than the old subprocess, which exited 1). `test_fingerprint_stable` now compares two runs in one process, so it no longer spans two hash seeds; that case is covered by `tests/kits/protocol/test_canonical.py::test_pinned_golden_fingerprint` (a checked-in value) and by the real-start test (`canon` across processes). One new test starts the installed program for real and checks it answers like the in-process run (`test_the_installed_program_starts_and_answers`, marked slow).

**(d) Tests that start a process are marked slow.** Found by running the not-slow selection once with a recorder plugin on `subprocess.Popen` (which asyncio's subprocesses also use on Windows) and `multiprocessing`, noting the running test and the program: **49 test functions (57 cases)** start Python, `uv`, `icacls` or `cmd`; they are marked `@pytest.mark.slow` with a comment. Calls to `git` made by the product itself (1,178, to stamp a commit) are not counted: they are part of what is under test, and marking those tests would empty the inner gate of screening. Per file (cases): `authority/test_isolation_windows.py` 13 new (Windows-only; one more was already slow), `inception/test_inception_grounded.py` 9, `pipeline/test_pipeline_executor.py` 7, `inception/test_inception_replace.py` 6, `inception/test_inception_criteria.py` 4, `console/test_console_jobs.py` 3, two each in `kits/pdf/test_atomic_acquisition.py`, `inception/test_emit_helper.py`, `console/test_job_runner.py`, one each in nine more. `tests/conformance/test_contract_baseline.py::test_contract_baseline_is_current` also starts Python but is baseline-locked, so it is left unmarked.

No assertion was removed or loosened. Marking slow changes which stage runs a test (the inner gate skips it; checkpoint, PR and full runs keep it), not what it checks.

## Measurements

All on this PC, one process at a time, nothing else heavy running (checked before each run). Before = `58468929`, after = `0259e27e`, both on the same venv contents (Python 3.14.7, `--extra dev --extra pdf`). For the sample files and imports the two trees were run alternately, three rounds, from two worktrees; single runs varied by up to 40%, so ranges are given.

| What | Before | After |
| :-- | --: | --: |
| `import scholar_harness` (wall clock) | 4.15–4.38 s | 0.43–0.46 s |
| `import scholar_harness` (`-X importtime`, cumulative) | 3.93 s | 0.25 s |
| `import scholar_harness.cli` | 5.08–6.74 s | 2.37–2.53 s |
| `tests/console/test_charting_api.py` (37 tests) | 27.5–36.1 s | 14.7–16.4 s |
| `tests/console/test_screening_api_v1.py` (54) | 28.8–29.9 s | 19.2–19.3 s |
| `tests/console/test_export_api.py` | 15.4–15.9 s | 9.6–10.1 s |
| `tests/kits/protocol/test_cli.py` (23; after: 24) | 32.8–33.6 s | 6.8–7.4 s |
| Collection, `--collect-only`, warm | 28.8 s (5,351 tests) | 28.8 s (5,352 tests) |
| **Full suite, `-n 4`** | **516 s** (5,336 passed, 15 skipped) | **437 s** (5,337 passed, 15 skipped) |
| Not-slow selection (the inner gate's `-m "not slow"`), `-n 4` | 413 s (5,279 passed*) | 367 s (5,226 passed) |

\* The before run of the not-slow selection had 4 failures, all `shutil.Error` from a path over 260 characters: the comparison worktree sat in a deep scratchpad folder. The same 4 tests pass in the before full run, which ran from the normal worktree.

**What did not improve:** collection. It is the import of the test modules (the console's API and the kits), not the orchestrator alone; the lazy import does not reach it, because `scholar_harness.console` and the screening engine import the search kit themselves (`import scholar_harness.console.serve` is still 4 to 7 s). The test-suite review's step 4 (tiers) and a lazier console are where that time is.

## Definition of done

- [x] (a) The orchestrator import is lazy in `scholar_harness/__init__.py` (and in `cli.py`); `scholar_harness.ResearchOrchestrator` and `cli.ResearchOrchestrator` still resolve.
- [x] (b) A shared `tests/support/` module builds each kind of workspace once per worker and copies it per test, starting with `tests/console`; it refuses a template that records its own path.
- [x] (c) `tests/kits/protocol/test_cli.py` runs in process with one real start.
- [x] (d) The unmarked tests that start processes are marked slow (found by recording, not guessing); the locked baseline test is named and left.
- [x] Measured before and after: collection, the sample files the review timed, one full `-n 4` run.
- [x] No test weakened.

## Evidence

| Check | Head | Result |
| :-- | :-- | :-- |
| Full Python suite `-n 4` (junit), final head | `34af655e` | **5,337 passed, 15 skipped, 0 failed** (junit 5,352); 481 s, with the reviewer's targeted tests running alongside (the clean after-timing is the 437 s run on `0259e27e` above) |
| Full Python suite `-n 4` (junit) | `0259e27e` | 5,337 passed, 15 skipped, 0 failed (junit 5,352); 437 s |
| `tests/console/_record_page_engine.py` imported as a direct run does, and its `published_workspace` built (`main()` not run: it would rewrite the web app's fixture) | `34af655e` | works; failed before the round-1 fix (`ModuleNotFoundError: support`) |
| Template folders left in the temporary folder after the final run | `34af655e` | none |
| The files of the three builders' callers (24 files) | `aa0297a6` | 388 passed |
| The 57 newly slow cases, run with `-m slow` | `0259e27e` | 62 passed (with the files' existing slow tests); none left in `-m "not slow"` |
| `ruff check scripts/`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9`; `generate_contract_baseline.py --check`; `git diff --check` | `0259e27e` | pass; baseline current, no locked file changed |

## Review

- **Round 1** (`milestone-reviewer`, on `3eaf4bcc`): **CHANGES**. P2: the page-engine recorder script, run directly, could no longer import `support`. P3: the record called the builders deterministic though copies share random ids; a failed build could block later calls with `FileExistsError`; the keys lacked `WS_ID`/`SCREENER`; counts (57 cases, 13 new in the isolation tests); the crash check in the in-process helper could never fail; the lost two-hash-seed comparison. All fixed or recorded in `34af655e`. The reviewer found no weakened test (the protocol CLI checks hold under Click 8.5/Typer 0.27, stdout bytes and stderr included), no caller patching an input outside the key, and no reliance on the orchestrator's import side effects.
- **Round 2** (on `34af655e`): **APPROVE**. Targeted run 235 passed.

**Not verified.** CI and macOS/Linux (`_refuse_own_path` matches the path string as written; a resolved alias such as `/private/var` or an 8.3 name would not match, which matters only if a builder ever writes an absolute path, and none does today); the recorder script's `main()`; that each of the 49 marked tests starts a process on every OS (the list is one Windows recording run).
