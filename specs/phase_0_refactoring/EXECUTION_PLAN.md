# Phase 0 Execution Plan

**Source spec:** `specs/phase_0_refactoring.md`
**Generated:** 2026-09-17

---

## Task 1: Extract `inception.display` — console formatting helpers [INDEPENDENT]
**Description:** Move the `console` object, `show_refraction_grid`, and `_bounded` helper into `inception/display.py`. These have zero upward dependencies and are imported only by sibling inception functions.

**Files to Touch:**
- Create `src/scholar_harness/inception/display.py`
- Modify `src/scholar_harness/inception.py` (remove functions, add re-export)

### Execution Checklist
- [ ] Create `src/scholar_harness/inception/` directory
- [ ] Create `src/scholar_harness/inception/__init__.py` (empty initially)
- [ ] Create `src/scholar_harness/inception/display.py`
- [ ] Move `console = Console()` (line 44), `show_refraction_grid` (lines 354–365), `_bounded` (lines 723–727), and `_INLINE_LIST_CAP` (line 720) into `display.py`
- [ ] Add necessary imports to `display.py`: `from rich.console import Console`, `from rich.table import Table`, `from .intent import refraction_rows` (lazy or deferred to avoid circular)
- [ ] In `inception.py`, replace removed code with: `from .display import console, show_refraction_grid, _bounded, _INLINE_LIST_CAP`
- [ ] Verify `REPO_ROOT` constant stays in `inception.py` (used by wizard.py later)

### Testing Strategy
- Run `uv run pytest tests/test_inception.py -x` — all existing tests must pass unchanged (they import from `scholar_harness.inception` which re-exports).
- Grep for any other file importing `show_refraction_grid` or `_bounded` directly — none found in codebase.

### Definition of Done (DoD)
- `uv run pytest tests/test_inception.py -x` passes (0 failures).
- `from scholar_harness.inception.display import console` resolves.
- The original `inception.py` no longer defines `console`, `show_refraction_grid`, or `_bounded`.

---

## Task 2: Extract `inception.intent` — data models, constants, and intent generation [INDEPENDENT]
**Description:** Move all data models (`ConceptDraft`, `RQDraft`, `Survey`), paradigm constants, `slugify`, `make_intent`, `detect_leanings`, `recommend_playbook`, `enforce_lexicon`, `refraction_rows`, `draft_default_concepts`, and `_default_matrix_dimensions` into `inception/intent.py`. These are pure functions with no CLI/console dependencies.

**Files to Touch:**
- Create `src/scholar_harness/inception/intent.py`
- Modify `src/scholar_harness/inception.py`

### Execution Checklist
- [ ] Create `src/scholar_harness/inception/intent.py`
- [ ] Move constants: `PARADIGM_KEYWORDS`, `PARADIGM_PROFILE`, `ALL_PLAYBOOKS`, `PLAYBOOK_RECOMMENDATION`, `INTERPRETIVIST_FORBIDDEN` (lines ~250–303)
- [ ] Move dataclasses: `ConceptDraft`, `RQDraft`, `Survey` (lines 474–511)
- [ ] Move pure functions: `slugify` (514–519), `make_intent` (522–598), `detect_leanings` (305–315), `recommend_playbook` (318–320), `enforce_lexicon` (323–328), `refraction_rows` (336–351), `draft_default_concepts` (781–797), `_default_matrix_dimensions` (1518–1556)
- [ ] Add necessary imports to `intent.py`: `dataclasses`, `re`, `json`, `pathlib.Path`, `typing.Any`
- [ ] In `inception.py`, replace removed code with: `from .intent import (ConceptDraft, RQDraft, Survey, slugify, make_intent, ...)`
- [ ] Verify no circular dependency (intent.py must not import from display.py or wizard.py)

### Testing Strategy
- Run `uv run pytest tests/test_inception.py -x` — tests `test_detect_leanings_*`, `test_recommend_playbook_*`, `test_enforce_lexicon_*`, `test_slugify_*`, `test_make_intent_*` exercise moved functions.
- Run `uv run pytest tests/test_inception_grounded.py -x` — imports `_grounded_directions_for_terms` from inception (still re-exported).

### Definition of Done (DoD)
- `uv run pytest tests/test_inception.py tests/test_inception_grounded.py -x` passes.
- `from scholar_harness.inception.intent import Survey, make_intent` resolves.
- `inception.py` no longer defines any of the moved symbols directly.

---

## Task 3: Extract `inception.grounded` — grounded recon functions
**Description:** Move all grounded-recon functions (`_is_junk_term_label`, `_family_tokens`, `_same_direction_family`, `_select_diverse_directions`, `_grounded_directions_for_terms`, `_present_grounded_directions`, `_present_pool_assessment`, `_run_grounded_recon`, `_grounded_default_concepts`, `_pool_anchor_dois`, `_enforce_grounded_anchors`, `_now_iso`) into `inception/grounded.py`.

**Files to Touch:**
- Create `src/scholar_harness/inception/grounded.py`
- Modify `src/scholar_harness/inception.py`

### Execution Checklist
- [ ] Create `src/scholar_harness/inception/grounded.py`
- [ ] Move lines 799–1278 (all `_*` grounded functions plus `_now_iso`)
- [ ] Add imports to `grounded.py`: `from .intent import Survey, ConceptDraft, PARADIGM_PROFILE`, `from .display import console`, `from ..recon.engine import ReconEngine`
- [ ] In `inception.py`, replace with: `from .grounded import (_is_junk_term_label, _family_tokens, _grounded_directions_for_terms, _run_grounded_recon, _enforce_grounded_anchors, _now_iso, ...)`
- [ ] Ensure `_now_iso` is exported (used by `wizard.py` and `genesis.py` later)

### Testing Strategy
- Run `uv run pytest tests/test_inception_grounded.py -x` — the majority of these tests import `_grounded_directions_for_terms`, `_is_junk_term_label` directly.
- Run `uv run pytest tests/recon/test_gates.py -x` — imports `_run_grounded_recon`.
- Run `uv run pytest tests/test_inception.py -x` — uses `_now_iso` indirectly.

### Definition of Done (DoD)
- `uv run pytest tests/test_inception_grounded.py tests/recon/test_gates.py tests/test_inception.py -x` passes.
- `from scholar_harness.inception.grounded import _grounded_directions_for_terms` resolves.

---

## Task 4: Extract `inception.genesis` — workspace scaffolding and audit logging
**Description:** Move `scaffold_project`, `scaffold_raw_project`, `log_genesis`, `compile_protocol_files`, `require_uninitialized`, `install_skills`, `write_env_example`, `write_mcp_json`, `install_workspace_support_files`, `_scaffold_only_intent` into `inception/genesis.py`. These handle workspace creation and audit events.

**Files to Touch:**
- Create `src/scholar_harness/inception/genesis.py`
- Modify `src/scholar_harness/inception.py`

### Execution Checklist
- [ ] Create `src/scholar_harness/inception/genesis.py`
- [ ] Move: `scaffold_project` (625–646), `scaffold_raw_project` (649–717), `log_genesis` (730–780), `compile_protocol_files` (599–622), `require_uninitialized` (1579–1607), `install_skills` (1610–1644), `write_env_example` (1647–1675), `write_mcp_json` (1678–1691), `install_workspace_support_files` (1694–1727), `_scaffold_only_intent` (1730–1768)
- [ ] Move constants: `INIT_MARKERS` (65–71), `REPO_ROOT` (43), `SKILL_SOURCE_ENV`, `_BUNDLED_SKILLS_PACKAGE`, `_BUNDLED_SKILLS_REL` (59–61)
- [ ] Move `_log_project_event` (152–303 area), `_load_log_module` (119–150), `_bundled_skills_root` (78–88), `resolve_skills_root` (91–108), `resolve_workspace_manager_scripts` (110–117), `_logimport_name`/`_log_module_ref`/`_log_module_tried` (73–76)
- [ ] Add imports to `genesis.py`: `import json`, `import os`, `import shutil`, `import subprocess`, `import sys`, `import uuid`, `from pathlib import Path`, `from datetime import UTC, datetime`, `from ..mcp_setup import _serialize, build_mcp_entry`
- [ ] In `inception.py`, replace with re-exports: `from .genesis import (INIT_MARKERS, REPO_ROOT, resolve_skills_root, ...)`
- [ ] Update `cli.py`: change `from .inception import inception_command, init_command` (no change needed yet — wizard.py will own these after Task 5)
- [ ] Update `audit_log.py`: change `from .inception import _load_log_module` → `from .inception.genesis import _load_log_module`
- [ ] Update `doctor.py`: change `from .inception import resolve_skills_root` → `from .inception.genesis import resolve_skills_root`

### Testing Strategy
- Run `uv run pytest tests/test_audit_log.py -x` — imports `_load_log_module` and `init_command`.
- Run `uv run pytest tests/test_doctor.py -x` — imports `resolve_skills_root`.
- Run `uv run pytest tests/test_mcp_setup.py -x` — imports `write_mcp_json`.
- Run `uv run pytest tests/test_cli_init.py -x` — imports from `scholar_harness.inception` and calls `init_command`.

### Definition of Done (DoD)
- `uv run pytest tests/test_audit_log.py tests/test_doctor.py tests/test_mcp_setup.py tests/test_cli_init.py -x` passes.
- `from scholar_harness.inception.genesis import resolve_skills_root` resolves.
- `inception.py` no longer defines `scaffold_project`, `log_genesis`, `compile_protocol_files`, etc.

---

## Task 5: Extract `inception.wizard` — Responder protocol and main wizard flow
**Description:** Move `Responder`, `ConsoleResponder`, `run_wizard`, `inception_command`, and `init_command` into `inception/wizard.py`. This is the top-level orchestration layer that imports from all other inception submodules.

**Files to Touch:**
- Create `src/scholar_harness/inception/wizard.py`
- Modify `src/scholar_harness/inception.py` (now becomes the re-export shim)

### Execution Checklist
- [ ] Create `src/scholar_harness/inception/wizard.py`
- [ ] Move: `Responder` (373–378), `ConsoleResponder` (381–466), `run_wizard` (1280–1515), `inception_command` (1559–1571), `init_command` (1771–1846)
- [ ] Add imports to `wizard.py`: `from .display import console`, `from .intent import (Survey, ConceptDraft, RQDraft, slugify, make_intent, detect_leanings, ...)`, `from .grounded import (_run_grounded_recon, _enforce_grounded_anchors, ...)`, `from .genesis import (compile_protocol_files, scaffold_project, scaffold_raw_project, log_genesis, ...)`, `from ..recon.engine import ReconEngine`
- [ ] Rewrite `src/scholar_harness/inception.py` as a thin re-export module: import and re-export every public symbol from the four submodules plus `wizard.py` — this preserves all existing `from scholar_harness.inception import X` paths.

### Execution Checklist (continued)
- [ ] Verify `inception/__init__.py` re-exports: `from .wizard import inception_command, init_command, run_wizard, ConsoleResponder, Responder`
- [ ] Verify `inception/__init__.py` re-exports: all symbols from `.display`, `.intent`, `.grounded`, `.genesis`
- [ ] Confirm `cli.py` import (`from .inception import inception_command, init_command`) still works unchanged
- [ ] Confirm all 20+ test file imports still resolve

### Testing Strategy
- Run full test suite: `uv run pytest tests/ -x --timeout=60`
- Specifically target: `uv run pytest tests/test_inception.py tests/test_inception_grounded.py tests/test_cli_init.py tests/test_audit_log.py tests/test_doctor.py tests/test_mcp_setup.py -x`
- Spot-check: `uv run python -c "from scholar_harness.inception import inception_command, init_command, Survey, _grounded_directions_for_terms; print('OK')"`

### Definition of Done (DoD)
- `uv run pytest tests/ -x` passes (0 failures, same count as baseline).
- `inception.py` is ≤ 30 lines (re-exports only).
- `inception/wizard.py` defines `run_wizard`, `inception_command`, `init_command`.
- `from scholar_harness.inception import inception_command` still works.

---

## Task 6: Verify inception package — delete old file, update AGENTS.md [INDEPENDENT]
**Description:** Remove the original monolithic `inception.py` (now replaced by `inception/__init__.py` re-exports) and confirm the full test suite still passes. Update documentation references.

**Files to Touch:**
- Delete `src/scholar_harness/inception.py` (the original; `inception/__init__.py` replaces it)
- Modify `AGENTS.md` if it references `inception.py` directly

### Execution Checklist
- [ ] Confirm `inception/__init__.py` re-exports all symbols that were in the old `inception.py`
- [ ] Delete the old `src/scholar_harness/inception.py`
- [ ] Run `uv run pytest tests/ -x` — full suite must pass
- [ ] Run `uv run ruff check scripts/` — lint must pass
- [ ] Grep `AGENTS.md` for `inception.py` references and update if needed (line 20 references it)

### Testing Strategy
- Full suite: `uv run pytest tests/ -x`
- Lint: `uv run ruff check scripts/`
- Import smoke: `uv run python -c "from scholar_harness.inception import inception_command, init_command, Survey, console; print('OK')"`

### Definition of Done (DoD)
- `inception.py` no longer exists as a standalone file.
- `uv run pytest tests/ -x` passes with the same test count as baseline.
- `from scholar_harness.inception import inception_command` resolves.

---

## Task 7: Extract `screening.batcher` — batch preparation and doc rebuild [INDEPENDENT]
**Description:** Move `_rebuild_doc`, `_build_agent_instructions`, `_screening_dir`, `_load_decisions`, and `cmd_prepare` into `screening/batcher.py`.

**Files to Touch:**
- Create `src/scholar_harness/screening/` directory
- Create `src/scholar_harness/screening/__init__.py`
- Create `src/scholar_harness/screening/batcher.py`
- Modify `src/scholar_harness/agent_screen.py` (remove functions, add re-exports)

### Execution Checklist
- [ ] Create `src/scholar_harness/screening/` directory
- [ ] Create `src/scholar_harness/screening/__init__.py` (empty initially)
- [ ] Create `src/scholar_harness/screening/batcher.py`
- [ ] Move: `_rebuild_doc` (128–155), `_build_agent_instructions` (158–228), `_screening_dir` (231–234), `_load_decisions` (237–252), `cmd_prepare` (259–369)
- [ ] Add imports to `batcher.py`: `import json`, `import logging`, `import sys`, `from pathlib import Path`, `from scholar_search.models import Author, Document, ExternalIds`
- [ ] In `agent_screen.py`, replace with: `from .screening.batcher import _rebuild_doc, _build_agent_instructions, _screening_dir, _load_decisions, cmd_prepare`
- [ ] Verify `orchestrator.py` import (`from scholar_harness.agent_screen import cmd_prepare`) still works

### Testing Strategy
- Run `uv run pytest tests/test_console_m53.py -x` — exercises `cmd_collect` which calls `_rebuild_doc` and `_load_decisions`.
- Run `uv run pytest tests/test_orchestrator_fidelity.py -x` — monkeypatches `cmd_prepare`.
- Run `uv run pytest tests/test_pipeline_executor.py -x` — references `agent_screen.py` path.

### Definition of Done (DoD)
- `uv run pytest tests/test_console_m53.py tests/test_orchestrator_fidelity.py tests/test_pipeline_executor.py -x` passes.
- `from scholar_harness.screening.batcher import cmd_prepare` resolves.

---

## Task 8: Extract `screening.collector` — decision collection and assembly [INDEPENDENT]
**Description:** Move `cmd_collect` and `cmd_status` into `screening/collector.py`. These depend on `_screening_dir` and `_load_decisions` from batcher, and `_rebuild_doc` for document reconstruction.

**Files to Touch:**
- Create `src/scholar_harness/screening/collector.py`
- Modify `src/scholar_harness/agent_screen.py`

### Execution Checklist
- [ ] Create `src/scholar_harness/screening/collector.py`
- [ ] Move: `cmd_collect` (423–690+), `cmd_status` (376–417)
- [ ] Add imports to `collector.py`: `from .batcher import _screening_dir, _load_decisions, _rebuild_doc`
- [ ] In `agent_screen.py`, replace with: `from .screening.collector import cmd_collect, cmd_status`

### Testing Strategy
- Run `uv run pytest tests/test_console_m53.py -x` — directly calls `cmd_collect` (loaded via `importlib.util.spec_from_file_location`).
- Run `uv run pytest tests/test_console_m54.py -x` — may exercise screening status.

### Definition of Done (DoD)
- `uv run pytest tests/test_console_m53.py -x` passes.
- `from scholar_harness.screening.collector import cmd_collect` resolves.

---

## Task 9: Extract `screening.report` — calibration commands [INDEPENDENT]
**Description:** Move `cmd_calibration` and `cmd_calibrate_eval` into `screening/report.py`. These are self-contained calibration workflows.

**Files to Touch:**
- Create `src/scholar_harness/screening/report.py`
- Modify `src/scholar_harness/agent_screen.py`

### Execution Checklist
- [ ] Create `src/scholar_harness/screening/report.py`
- [ ] Move: `cmd_calibration` (693–757), `cmd_calibrate_eval` (759–793)
- [ ] Add imports to `report.py`: `import json`, `import logging`, `import sys`, `from pathlib import Path`, and the calibration imports (`_HAS_CALIBRATION`, `build_checklist_schema`, etc.)
- [ ] In `agent_screen.py`, replace with: `from .screening.report import cmd_calibration, cmd_calibrate_eval`

### Testing Strategy
- Run `uv run pytest tests/test_console_m53.py -x` — no direct calibration tests, but ensures no import breakage.
- Manual: `uv run python -c "from scholar_harness.screening.report import cmd_calibration; print('OK')"`

### Definition of Done (DoD)
- `uv run pytest tests/ -x` passes.
- `from scholar_harness.screening.report import cmd_calibration` resolves.

---

## Task 10: Finalize `screening` package — slim down `agent_screen.py` and verify [INDEPENDENT]
**Description:** After all submodules are extracted, `agent_screen.py` should be a thin re-export + CLI `main()` dispatcher. Verify all imports across the codebase resolve.

**Files to Touch:**
- Modify `src/scholar_harness/agent_screen.py` (reduce to re-exports + main)
- Modify `src/scholar_harness/screening/__init__.py` (public API exports)
- Modify `src/scholar_harness/rescreen_workspace.py` (update import path)

### Execution Checklist
- [ ] Rewrite `agent_screen.py` to: import and re-export `cmd_prepare`, `cmd_collect`, `cmd_status`, `cmd_calibration`, `cmd_calibrate_eval` from submodules; keep `main()` function with argparse dispatch
- [ ] Update `screening/__init__.py` to export public API: `cmd_prepare`, `cmd_collect`, `cmd_status`, `cmd_calibration`, `cmd_calibrate_eval`, `main`
- [ ] Update `rescreen_workspace.py`: change `from agent_screen import main` → `from scholar_harness.screening import main` (or keep `from agent_screen import main` if re-export works)
- [ ] Verify `orchestrator.py`: `from scholar_harness.agent_screen import cmd_prepare` still resolves
- [ ] Verify `console/api/pipelines.py` string references to `agent_screen.py` (these are command strings, not imports — no change needed)
- [ ] Verify `tests/conformance/test_actions_cli_parity.py`: references `AGENT_SCREEN_SCRIPT` path — confirm file still exists

### Testing Strategy
- Run full test suite: `uv run pytest tests/ -x`
- Specifically: `uv run pytest tests/test_console_m53.py tests/test_orchestrator_fidelity.py tests/test_pipeline_executor.py tests/conformance/test_actions_cli_parity.py -x`

### Definition of Done (DoD)
- `agent_screen.py` is ≤ 80 lines (re-exports + `main()`).
- `uv run pytest tests/ -x` passes with the same test count as baseline.
- `from scholar_harness.agent_screen import cmd_prepare` resolves.
- `from scholar_harness.screening import cmd_collect` resolves.

---

## Task 11: Create shared test fixtures in `tests/conftest.py` [INDEPENDENT]
**Description:** Create a central `tests/conftest.py` with shared fixtures (`sample_protocol`, `sample_papers`, mock objects) to eliminate duplication across test files. This must happen before directory restructuring.

**Files to Touch:**
- Create `tests/conftest.py`

### Execution Checklist
- [ ] Create `tests/conftest.py`
- [ ] Identify duplicated fixture patterns across test files:
  - `tests/test_phase3_e2e.py`: `@pytest.fixture` for `workspace` (line 34)
  - `tests/test_harness_cli.py`: `@pytest.fixture` for CLI runner (line 19)
  - `tests/test_console_serve.py`: `@pytest.fixture` for serve setup (line 209)
  - `tests/test_integrations.py`: `@pytest.fixture` (line 12)
- [ ] Extract commonly reused fixtures into `conftest.py`:
  - `sample_protocol`: minimal protocol.json dict
  - `sample_papers`: list of paper dicts with workspace_id, title, abstract, year
  - `sample_verified`: list of verified.json entries
  - `tmp_workspace`: temporary workspace directory with standard layout
- [ ] Ensure `conftest.py` fixtures use `@pytest.fixture` scope appropriately (session vs function)
- [ ] Remove duplicated fixture definitions from individual test files and rely on conftest

### Testing Strategy
- Run `uv run pytest tests/ -x` — all tests must still discover fixtures.
- Check that no fixture name collisions exist.

### Definition of Done (DoD)
- `tests/conftest.py` exists with ≥ 3 shared fixtures.
- `uv run pytest tests/ -x` passes.
- No test file defines a fixture with the same name as one in conftest.

---

## Task 12: Rename milestone-numbered test files [INDEPENDENT]
**Description:** Rename phase-numbered and milestone-named test files to reflect feature scope. These renames are purely cosmetic and affect only file names, not import paths.

**Files to Touch:**
- Rename `tests/test_console_m52.py` → `tests/test_console_pipelines.py`
- Rename `tests/test_console_m53.py` → `tests/test_console_screening.py`
- Rename `tests/test_console_m54.py` → `tests/test_console_jobs.py`
- Rename `tests/test_phase1_e2e.py` → `tests/test_e2e_search_screen.py`
- Rename `tests/test_phase2_e2e.py` → `tests/test_e2e_extract_index.py`
- Rename `tests/test_phase3_e2e.py` → `tests/test_e2e_synthesis.py`

### Execution Checklist
- [ ] Rename `tests/test_console_m52.py` → `tests/test_console_pipelines.py`
- [ ] Rename `tests/test_console_m53.py` → `tests/test_console_screening.py`
- [ ] Rename `tests/test_console_m54.py` → `tests/test_console_jobs.py`
- [ ] Rename `tests/test_phase1_e2e.py` → `tests/test_e2e_search_screen.py`
- [ ] Rename `tests/test_phase2_e2e.py` → `tests/test_e2e_extract_index.py`
- [ ] Rename `tests/test_phase3_e2e.py` → `tests/test_e2e_synthesis.py`
- [ ] Verify no cross-references between test files use the old filenames (grep for `test_console_m52`, `test_phase1_e2e`, etc.)
- [ ] Update any CI config or Makefile that references these filenames

### Testing Strategy
- Run `uv run pytest tests/ -x` — pytest discovers tests by file name, so renames are transparent.
- Grep for old filenames in CI config, Makefile, AGENTS.md.

### Definition of Done (DoD)
- `uv run pytest tests/ -x` passes with the same test count.
- No file named `test_console_m52.py`, `test_phase1_e2e.py`, etc. exists.
- Old filenames not referenced anywhere in the repo.

---

## Task 13: Create test directory structure and move tests [INDEPENDENT]
**Description:** Move the flat test files into domain-grouped subdirectories. Existing `tests/conformance/` and `tests/recon/` directories stay as-is.

**Files to Touch:**
- Create `tests/unit/`, `tests/cli/`, `tests/console/`, `tests/mcp/`, `tests/pipeline/`, `tests/inception/`, `tests/integrations/`, `tests/e2e/`
- Move files into their respective subdirectories

### Execution Checklist
- [ ] Create `tests/unit/` directory
- [ ] Move `tests/test_audit_log.py` → `tests/unit/test_audit_log.py`
- [ ] Move `tests/test_doctor.py` → `tests/unit/test_doctor.py`
- [ ] Create `tests/cli/` directory
- [ ] Move `tests/test_harness_cli.py` → `tests/cli/test_harness_cli.py`
- [ ] Move `tests/test_cli_init.py` → `tests/cli/test_cli_init.py`
- [ ] Move `tests/test_scholar_agent_cli.py` → `tests/cli/test_scholar_agent_cli.py`
- [ ] Create `tests/console/` directory
- [ ] Move `tests/test_console_pipelines.py` (renamed in Task 12) → `tests/console/test_console_pipelines.py`
- [ ] Move `tests/test_console_screening.py` → `tests/console/test_console_screening.py`
- [ ] Move `tests/test_console_jobs.py` → `tests/console/test_console_jobs.py`
- [ ] Move `tests/test_console_serve.py` → `tests/console/test_console_serve.py`
- [ ] Create `tests/mcp/` directory
- [ ] Move `tests/test_mcp_setup.py` → `tests/mcp/test_mcp_setup.py`
- [ ] Move `tests/test_mcp_recon.py` → `tests/mcp/test_mcp_recon.py`
- [ ] Move `tests/test_mcp_tools_graph.py` → `tests/mcp/test_mcp_tools_graph.py`
- [ ] Create `tests/pipeline/` directory
- [ ] Move `tests/test_pipeline_executor.py` → `tests/pipeline/test_pipeline_executor.py`
- [ ] Move `tests/test_pipeline_script.py` → `tests/pipeline/test_pipeline_script.py`
- [ ] Move `tests/test_orchestrator_fidelity.py` → `tests/pipeline/test_orchestrator_fidelity.py`
- [ ] Create `tests/inception/` directory
- [ ] Move `tests/test_inception.py` → `tests/inception/test_inception.py`
- [ ] Move `tests/test_inception_grounded.py` → `tests/inception/test_inception_grounded.py`
- [ ] Create `tests/integrations/` directory
- [ ] Move `tests/test_integrations.py` → `tests/integrations/test_integrations.py`
- [ ] Move `tests/test_nexus_scholar_metapackage.py` → `tests/integrations/test_nexus_scholar_metapackage.py`
- [ ] Move `tests/test_rigor_upgrades.py` → `tests/integrations/test_rigor_upgrades.py`
- [ ] Create `tests/e2e/` directory
- [ ] Move `tests/test_e2e_search_screen.py` (renamed in Task 12) → `tests/e2e/test_e2e_search_screen.py`
- [ ] Move `tests/test_e2e_extract_index.py` → `tests/e2e/test_e2e_extract_index.py`
- [ ] Move `tests/test_e2e_synthesis.py` → `tests/e2e/test_e2e_synthesis.py`
- [ ] Verify `tests/conformance/` and `tests/recon/` remain untouched
- [ ] Remove empty `tests/__pycache__/` directory if present

### Testing Strategy
- Run `uv run pytest tests/ -x` — pytest discovers tests recursively in subdirectories by default.
- Verify test count matches baseline: `uv run pytest tests/ --co -q | tail -1`
- Check that `conftest.py` is still discovered (it lives at `tests/conftest.py`, which pytest auto-imports).

### Definition of Done (DoD)
- `uv run pytest tests/ -x` passes with the same test count as baseline (391 passed).
- No `.py` test files remain in the `tests/` root (except `conftest.py`).
- `tests/conformance/` and `tests/recon/` are unchanged.

---

## Task 14: Update `test_cli_init.py` cross-module imports
**Description:** `test_cli_init.py` imports `E2E_ANSWERS`, `GENESIS_TS`, `ScriptedResponder` from `test_inception`. After moving both files to different subdirectories, these cross-imports must be updated.

**Files to Touch:**
- Modify `tests/cli/test_cli_init.py` (was `tests/test_cli_init.py`)
- Modify `tests/inception/test_inception.py` (was `tests/test_inception.py`)

### Execution Checklist
- [ ] In `tests/cli/test_cli_init.py`, line 12: `from test_inception import E2E_ANSWERS, GENESIS_TS, ScriptedResponder` — update to `from tests.inception.test_inception import ...` or move shared helpers to `conftest.py`
- [ ] Preferred approach: move `E2E_ANSWERS`, `GENESIS_TS`, `ScriptedResponder` into `tests/conftest.py` as shared fixtures/values
- [ ] Update `test_cli_init.py` to import from `conftest` (automatic via pytest fixtures) or from the new location
- [ ] Verify `test_inception.py` still exports these symbols if other tests depend on them

### Testing Strategy
- Run `uv run pytest tests/cli/test_cli_init.py tests/inception/test_inception.py -x`
- Run `uv run pytest tests/ -x` full suite.

### Definition of Done (DoD)
- `uv run pytest tests/cli/test_cli_init.py tests/inception/test_inception.py -x` passes.
- No `ImportError` or `ModuleNotFoundError` in any test file.

---

## Task 15: Final validation — full suite + lint + import smoke test
**Description:** Run the complete test suite, linter, and import smoke tests to confirm zero regressions from the entire Phase 0 refactoring.

**Files to Touch:**
- None (validation only)

### Execution Checklist
- [ ] Run `uv run pytest tests/ -x --tb=short` — 0 failures, same test count as baseline (391 passed)
- [ ] Run `uv run ruff check scripts/` — 0 lint errors
- [ ] Run import smoke tests:
  - `uv run python -c "from scholar_harness.inception import inception_command, init_command, Survey, console, _grounded_directions_for_terms; print('inception OK')"`
  - `uv run python -c "from scholar_harness.agent_screen import cmd_prepare, cmd_collect, cmd_status; print('agent_screen OK')"`
  - `uv run python -c "from scholar_harness.screening import cmd_prepare, cmd_collect; print('screening OK')"`
- [ ] Verify `inception.py` no longer exists as standalone file
- [ ] Verify `agent_screen.py` is ≤ 80 lines
- [ ] Verify no test file remains in `tests/` root (except `conftest.py`)
- [ ] Verify `tests/conformance/` and `tests/recon/` are untouched
- [ ] Count total test files: should be 23 (moved) + 2 existing subdirs = same coverage

### Testing Strategy
- Full suite regression: `uv run pytest tests/ -x`
- Lint gate: `uv run ruff check scripts/`
- Manual import verification (smoke commands above)

### Definition of Done (DoD)
- `uv run pytest tests/ -x` passes with ≥ 391 tests passed, 0 failures.
- `uv run ruff check scripts/` exits 0.
- All import smoke tests print "OK".
- The directory structure matches the spec's proposed layout.
