# M4b Inception screens over the step API
Branch: `dev/m4b/inception-ui` · Lane: **RELEASE**. The milestone started as STANDARD: a UI over routes that M4a shipped and reviewed under RELEASE. The researcher's answers on 2026-11-09 added two engine changes to public HTTP answers: preview `files` and the draft's `emitted` record (`test_gate_policy.md` §lanes; decision 2026-11-09). · Status: READY FOR PR (review APPROVE at `2489c46`; gates green on `c2022bc`) · Started: 2026-11-09

Why: plan §6 row "M4 Inception web" lists the UI for inception specs 00–08. M4a (PR #206) shipped the engine: drafts, the stateless step API, compile-preview and gated genesis (`docs/architecture/inception-api.md`). M4b builds the screens over it, so a researcher creates a workspace from the browser without the CLI wizard. Recon over HTTP (INC-09/21) is still not built, so Explore and Direction stay placeholders.

## Definition of done
- [x] **Specs.**
  - `docs/ux/phase0-inception/final/01-scope.md`, `04-shape.md`, `05-criteria.md`, `06-review.md`, `07-done.md` and `08-states.md` are `Status: FINAL`. Each maps its data to the exact `/api/v1/inception` routes and refusal codes. The `ux-spec-writer` agent wrote the drafts, and the researcher closed their four open questions on 2026-11-09.
  - Each spec ends with "As built (M4b)", which lists where the screens simplify it.
  - `02-explore.md` and `03-direction.md` are placeholders.
  - The Workspaces spec (00) has an addendum for the "New review" link.
- [x] **Browser surface.** `console/browser.py` and the Next proxy carry POST to drafts, steps, preview and genesis, and PUT on a draft. DELETE (discard) stays out. Tests: `tests/console/test_browser_access.py` (a full inception flow through the browser surface, plus refusals) and `apps/research-ui/tests/console-proxy.test.ts`.
- [x] **Screens.** The route group `/[locale]/inception/` has six screens: drafts (08), Scope (01), Shape (04), Concepts and criteria (05), Review and create (06), and Done (07).
  - Saves send `base_updated_at`. A save conflict shows `DRAFT_CONFLICT` as a sentence and overwrites nothing.
  - Each criterion is shown verbatim with its source, and a generated one waits for an explicit Accept.
  - Review previews with `POST /preview` and has one gate with one brand button in every state.
  - `WORKSPACE_EXISTS` with `markers` offers "Replace and back up". `SCREENING_BOUND` asks for the typed slug, and the engine compares it.
  - Done opens the workspace with `POST /workspaces/open` and lands on screening Home.
  - The flow starts from "New review" on the Workspaces screen.
  - Explore and Direction show as "coming with recon".
  - Copy is in en, fr and ar.
- [x] **Engine, decided by the researcher on 2026-11-09.**
  - The preview `files` lists every file genesis writes. Test: `test_preview_names_every_file_genesis_writes`.
  - The draft's `emitted` record keeps `backup_dir` and `previous_fingerprint`. Test: `test_a_replacement_records_its_backup_on_the_draft`.
- [x] **Tests.**
  - [x] Vitest: one file per screen (`tests/inception-*.test.tsx`), plus `inception-copy.test.ts` and `workspaces.test.tsx`.
  - [x] Playwright: `tests-browser/inception.spec.ts` runs the full flow and the bound flow against a stateful fake (`tests/fixtures/inception-engine.ts`), with axe on every screen in en and ar, light and dark, and overflow checks at 375 and 1440 px.
- [x] **Gate.** Inner gates after edits, then the pr and closure gates on the final executable commit `c2022bc` (see Evidence).
- [x] **Review.** The milestone-reviewer returned CHANGES at `59f0c4d` (2 P2, 3 P3), then APPROVE on the repair delta at `2489c46`.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| preview under-promises (spec 06 Q1) | `tests/console/test_inception_api.py::test_preview_names_every_file_genesis_writes` | yes: `.agents/skills/`, `.env.example`, `.mcp.json`, `INDEX.md`, `synthesis/literature_review.md` and others were written but not listed | yes |
| review #3: checks from "folder exists" | `tests/console/test_inception_api.py::test_preview_tells_a_workspace_from_a_folder_that_is_not_one` | yes: `KeyError: 'workspace'` | yes |
| backup lost on reload (spec 07 Q1) | `tests/console/test_inception_api.py::test_a_replacement_records_its_backup_on_the_draft` | yes: `KeyError: 'backup_dir'` | yes |

## Decisions
- [2026-11-09, The inception write gate names every file, and a draft keeps its backup](../../decisions.md) (researcher, accepted 2026-11-09). It also covers blank drafts, the Resume target and the lane.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| start | `8726fb9` | branch from `origin/main` | clean | |
| inner | `fafbddb` | `pytest tests/console/test_browser_access.py`; `vitest tests/console-proxy.test.ts` | 10 passed; 49 passed | |
| inner | `1f65f79` | `pytest tests/console/test_inception_api.py tests/inception tests/console/test_browser_access.py tests/cli/test_cli_init.py tests/console/test_workspaces_api.py -n auto` | 165 passed, 1 skipped | 26 s |
| inner | `1f65f79` | `npx tsc --noEmit`; `npx vitest run` (whole UI suite) | clean; 27 files, 326 passed | |
| pr | `59f0c4d` | `pytest -n auto` (whole suite) | **4609 passed, 15 skipped, 0 failed** | 8 m 37 s |
| closure | `59f0c4d` | `npx playwright test` (whole suite, light and dark) | **249 passed, 13 skipped, 0 failed** | 6 m 43 s |
| closure | `59f0c4d` | `uv build --wheel` | `nexus_scholar-1.1.0b4-py3-none-any.whl` | |
| review | `59f0c4d` | milestone-reviewer | CHANGES. P2: Review's fingerprint is re-stamped at genesis, so it is not "exactly" what is written. P2: the matrix and verification controls had no parked label, and the matrix help promised defaults that are not applied. P3: the Checks line used "folder exists", not the workspace markers genesis decides on. P3: the replacement list is fixed. P3: the replace text said project.json is "kept". Repairs below | |
| closure | `2489c46` | contract baseline, schemas, two-study fixture `--check`; `ruff check scripts/`; real-bug `ruff check src/`; `git diff --check origin/main...HEAD`; `uv build --wheel` | all pass | |
| closure | `2489c46` | `npx playwright test` (whole suite, light and dark) | **249 passed, 13 skipped, 0 failed** | 6 m 24 s |
| closure | `2489c46` | `npx vitest run` | 329 of 330 in a run that shared the CPU with the full pytest. The failing test was not identified. A rerun alone passed 330 of 330 | |
| pr | `2489c46` | `pytest -n auto` | 1 failed, 4609 passed. `test_preview_names_every_file_genesis_writes` is flaky: `INDEX.md` is rewritten stamped to the second, so it can be byte-identical; it failed 2 of 5 runs alone. The fix in `c2022bc` makes the test also detect writes by mtime; it then passed 8 of 8 alone | 8 m 18 s |
| re-review | `2489c46` | milestone-reviewer (repair delta) | **APPROVE**: all five findings resolved. P3 follow-up: a regular file at the target reads as a workspace in preview, and genesis refuses it correctly | |
| pr | `c2022bc` | `pytest -n auto` (whole suite; this commit changes only that Python test) | **4610 passed, 15 skipped, 0 failed**; `git diff --check` clean | 6 m 24 s |
| closure | working tree after `1f65f79` | contract baseline, schemas and two-study fixture `--check`; `ruff check scripts/`; real-bug `ruff check src/`; `sync_skills_bundle.py --check`; `git diff --check` | all pass | |

## Deferred
- **A regular file at the target** (re-review P3): `existing_markers` counts a file as a marker, so preview reads it as a workspace. Genesis then refuses `WORKSPACE_EXISTS` with no markers, and the card renders correctly.
- **Binding genesis to the previewed protocol** (review #1): genesis stamps its own time, so the written fingerprint differs from the preview. A save from another tab between preview and Create also goes through. The screen now labels the value a preview. Sending the expected fingerprint or the preview's timestamp with genesis is an engine decision for the researcher.
- **Release notes**: `docs/releases/` has no unreleased file. The next one (b5) names the browser inception flow, the inception routes on the browser surface, preview `files` and `target.workspace`, and the `emitted` backup fields. The user guide still describes only the CLI wizard, and plan §6 still says inception stays CLI/MCP.
- **Explore (02) and Direction (03)** wait for recon over HTTP (INC-09/21). Drafts carry no grounded evidence.
- **Discarding a draft** (`DELETE /inception/drafts/{id}`): the browser surface carries GET, HEAD, POST and PUT only. Blank drafts are labelled "Empty draft" (decision 2026-11-09).
- **Spec features simplified in the build.** They are listed under "As built (M4b)" in each spec:
  - no side proposal card on Scope;
  - no secondary paradigm;
  - no reason-code select for a typed exclusion;
  - no focus move after a criterion decision;
  - no Resume card;
  - no copy buttons;
  - no `beforeunload` guard;
  - offline is shown by the `ENGINE_UNREACHABLE` card, not by pre-disabled controls.
- **A real phone** cannot reach the inception routes (desktop only on the engine), so it gets the `TOKEN_SCOPE_REFUSED` card. The narrow layouts serve a narrow desktop window.
- **Workspaces Playwright check of the "New review" link** (spec 00 addendum): the vitest check covers the link and the single brand button. `inception.spec.ts` starts from `/inception/`.
