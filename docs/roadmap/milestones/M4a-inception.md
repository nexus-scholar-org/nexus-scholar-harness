# M4a-inception: the inception engine pieces that do not collide with M3a
Branch: `dev/m4a/inception-engine` · Lane: **RELEASE** (confirmed by the researcher 2026-11-08: CLI semantics change, because re-inception refuses without `--replace`, and new HTTP routes; `test_gate_policy.md` §lanes; the plan's M4 row is RELEASE) · Status: MERGED (PR #206, 65e361d) · Started: 2026-11-08

Why: plan §6 row "M4 Inception web" is split. M4a covers the engine work that touches neither `src/scholar_search/` nor `src/scholar_harness/recon/`, which M3a Discovery owns, nor the `scholar_protocol` models and compiler. Plan §1 has INC-08 and INC-22. Plan §2 "Phase 0 Inception" lists screens 00, 06 and 08 with their backend.

## Definition of done
- [x] **INC-08. Re-inception refuses without `--replace`.** `run_wizard` refuses a folder that already holds a workspace (exit 1, nothing written). With `--replace`, it backs up `protocol.json`, `intent.json` and `SCREENING_CRITERIA.md` under `audit/replaced/<stamp>/`. It keeps `project.json` (`created_at`, `stats`, identity) and logs GENESIS with the old fingerprint and the backup. A workspace with screening decisions or a publication also needs `--discard-screening-binding`. Test: `tests/inception/test_inception_replace.py` (6 tests).
- [x] **INC-22. Every criterion is shown verbatim and accepted one by one.** Each criterion is printed with its source. A criterion the wizard wrote defaults to "no", and one the researcher typed defaults to "yes". A rejected criterion is not compiled. An empty side is filled by asking. The pre-emit panel lists every criterion. The inception-agent skill has the same rule. Test: `tests/inception/test_inception_criteria.py` (4 tests).
- [x] **Stateless step API** over the wizard's own functions (`inception/steps.py`: scope, shape, criteria, matrix). Test: `tests/inception/test_inception_steps.py`. Its parity test checks that the same answers give the same intent and fingerprint through the CLI wizard and through the preview.
- [x] **Compile-preview** (`steps.preview`, `genesis.compile_intent`) writes nothing. Tests: `test_preview_writes_nothing` in both `test_inception_steps.py` and `test_inception_api.py`.
- [x] **One gated genesis path** (`inception/emit.py::emit_workspace`). All of these use it: the CLI wizard, `nexus-scholar init` (both modes), the workspaces API create route, the inception HTTP genesis route, and the skill helper `emit_protocol.py`. Tests: `test_inception_replace.py`, `test_emit_helper.py`, `test_inception_steps.py`, `test_inception_api.py`. The existing `test_workspaces_api.py` and `test_cli_init.py` still pass.
- [x] **Draft sessions with one session id** (screens 00 and 08; UX finding #10). Drafts live at `<workspaces root>/.drafts/rec_<hex>/draft.json` and support create, save (with a conflict check), list, resume and discard. The grounded wizard now mints `rec_<hex>` too. Test: `tests/console/test_inception_api.py`.
- [x] **Create a workspace from a draft** over HTTP (`POST /api/v1/inception/drafts/{id}/genesis`) through the gate. Test: `test_inception_api.py`.
- [x] **Gate:** RELEASE closure on the final executable commit `e7f1e98` (see Evidence), with `generate_contract_baseline.py --check` included.
- [x] **Review:** the milestone-reviewer returned CHANGES at `150b46f` (1 P1, 2 P2, 3 P3). The repairs are in `e7f1e98`. It returned APPROVE at `e7f1e98`.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| INC-08 | `test_inception_replace.py::test_rerun_refuses_an_existing_workspace_and_writes_nothing`, `::test_rerun_into_a_raw_folder_refuses_too` | yes: "DID NOT RAISE Exit" (the second run overwrote the protocol); the `--replace` tests failed with an unknown argument | yes |
| INC-22 | `test_inception_criteria.py` (4 tests) | yes: the wizard asked no per-criterion question, so the scripted answers fell out of step (TypeError / AttributeError) | yes |
| review 1 P1 | `test_inception_api.py::test_genesis_refuses_a_folder_that_is_not_a_workspace_and_keeps_it`, `::test_a_failed_genesis_removes_only_the_folder_it_created` | yes: the reviewer reproduced it, and a foreign `my_notes.txt` was deleted | yes |
| UX #10 | `test_inception_grounded.py` (session id is `rec_` + 32 hex) | yes: it was 12 hex characters | yes |

The phase-auditor re-verified INC-08 and INC-22 at `a273fc6` before the fix, by reading the code; it did not run it. For INC-08, `nexus-scholar init` was already guarded, but `run_wizard` and `scholar-harness inception` were not. For INC-22, the MCP compile tool injects nothing, but the skill had no step that showed or confirmed the criteria.

## Decisions
- [2026-11-08, Re-inception: refuse without `--replace`, back up, confirm a screening binding](../../decisions.md) (researcher, accepted 2026-11-08). Mechanism: `--discard-screening-binding` on the CLI and in the skill helper; over HTTP, the typed workspace slug.
- [2026-11-08, Inception criteria are shown verbatim and accepted one by one](../../decisions.md) (researcher, accepted 2026-11-08).
- [2026-11-08, Inception drafts live under the workspaces root, with one session id](../../decisions.md) (researcher, accepted 2026-11-08).

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| start | `a273fc6` | `generate_contract_baseline.py --check` | Contract baseline current | |
| inner | `7ab4964` | `pytest tests/inception tests/cli/test_cli_init.py tests/console/test_workspaces_api.py` | all pass (125) | |
| inner | `dbc478e` | the inception, console inception, workspaces, console security and CLI init tests, `-n auto` | all pass | |
| closure (RELEASE) | `2c99330` | contract baseline, contract schemas and two-study fixture `--check`; `ruff check scripts/`; `git diff --check`; `sync_skills_bundle.py --check` | all pass | |
| pr | `150b46f` | `pytest -q -n auto` | **4525 passed, 15 skipped, 0 failed** | 15 m 34 s |
| review | `150b46f` | milestone-reviewer | CHANGES. P1: HTTP genesis could remove a folder that is not a workspace. P2: the skills still had ungated writers. P2: binding tests covered only the event log. P3: the previous fingerprint was a byte hash. P3: the refusal codes were not registered. P3: no placeholder golden. All six are fixed in `e7f1e98` | |
| closure (RELEASE) | `e7f1e98` | contract baseline, contract schemas and two-study fixture `--check`; `ruff check scripts/`; `git diff --check origin/main...HEAD`; `sync_skills_bundle.py --check`; `uv build --wheel` | all pass | |
| closure (RELEASE) | `e7f1e98` | `pytest -q -n auto` | exit 0, no FAILED or ERROR lines (the doubled `-q` hides the count line). The previous count was 4525 passed; the repairs add 8 tests | 9 m 00 s |
| re-review | `e7f1e98` | milestone-reviewer (repair delta) | **APPROVE**: all six findings resolved, no defect introduced by the repairs | |
| PR | `82bdc6e` | PR #206 CI | `python-test` failed: `test_cli_offers_replace_and_the_discard_confirmation` read Rich help that CI renders in colour, and the style codes split `--replace`. The test now strips ANSI codes | |
| merge | `d7a12f8` | merge of `origin/main` (M3a `e1039b1`, b4) | conflict in `docs/decisions.md` only, with both sides kept; contract baseline and schemas `--check` pass | |
| pr | `d7a12f8` | `pytest -q -n auto` | **4585 passed, 15 skipped, 0 failed** | 13 m 10 s |
| CI | `d7a12f8` | PR #206 checks | **12/12 pass**: python-test, lint-and-smoke on ubuntu, macOS and Windows, wheel-e2e on ubuntu and Windows, build-wheel, research-ui, research-ui-browser | |
| closure (RELEASE) | `2c99330` | `uv build --wheel` | `nexus_scholar-1.1.0b3-py3-none-any.whl`, which contains `inception/emit.py`, `inception/steps.py`, `console/api/inception.py` and the skill's `emit_protocol.py` | |

## Deferred
- **Held until M3a merges** (decided by the session that split M4): INC-09 and INC-21, recon over HTTP (`recon/engine.py` uses the `scholar_search` providers M3a changes), and PROT-02, PROT-03 and PROT-08 (`scholar_protocol` models and compiler; PROT-03 is a contract change). Drafts carry no grounded evidence until recon over HTTP exists.
- **The browser proxy allowlist** (`console/browser.py`) does not yet include `/api/v1/inception/*`. It opens with the inception screens, so the browser surface grows only when a screen uses it.
- **A multi-workspace server** stays in M4. Genesis creates the workspace; opening it is still `POST /workspaces/open`.
- **Method questions M1–M7** (`docs/ux/phase0-inception/README.md`) stay open, as plan §2 proposes. That includes INC-23 (English as the silent language default), which the draft keeps for parity with the wizard.
- **All UI** (`apps/research-ui`) is owned by the redesign session.
- **Re-review follow-up (P3):** if an OSError hits half-way through a `--replace`, it can leave a half-replaced workspace. The backup under `audit/replaced/` holds the old files, but the refusal message does not name the backup path.
- **Pre-existing lint in `wizard.py`** (unused imports, B008), outside the CI ruff scope, is left as it is.
