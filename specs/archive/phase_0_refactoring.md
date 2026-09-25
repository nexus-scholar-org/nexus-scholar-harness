# Phase 0: Code and Test Health Refactoring

**Specification Version:** 1.0.0  
**Status:** READY FOR IMPLEMENTATION (Pre-requisite for Phases A-E)  
**Target System:** `scholar-harness`, `tests/`  

## 1. Executive Summary

Before implementing the new capabilities in Phases A through E, the codebase requires structural refactoring to address significant technical debt. The current state features a 1,846-line God Module (`inception.py`), an overloaded screening script (`agent_screen.py`), and a disorganized, flat test directory with milestone-numbered names. This phase resolves these issues to create a stable foundation for future development.

## 2. Source Code Refactoring

### 2.1 Refactor `inception.py`
The `src/scholar_harness/inception.py` file must be split into a dedicated `inception/` package.

- **Current State:** Single 1,846-line file handling Socratic interviews, grounded inception, intent generation, protocol compilation, and workspace scaffolding.
- **Proposed Structure:**
  - `src/scholar_harness/inception/__init__.py`
  - `src/scholar_harness/inception/wizard.py` (Interactive flow control)
  - `src/scholar_harness/inception/intent.py` (IntentPacket generation)
  - `src/scholar_harness/inception/grounded.py` (Grounded-mode specific logic)
  - `src/scholar_harness/inception/display.py` (Console formatting and output)
  - `src/scholar_harness/inception/genesis.py` (Workspace creation and audit events)

### 2.2 Refactor `agent_screen.py`
The `src/scholar_harness/agent_screen.py` file (850 lines) mixes file I/O, batching, and PRISMA reporting.

- **Proposed Structure:**
  - `src/scholar_harness/screening/__init__.py`
  - `src/scholar_harness/screening/batcher.py`
  - `src/scholar_harness/screening/collector.py`
  - `src/scholar_harness/screening/report.py`

## 3. Test Suite Reorganization

### 3.1 Directory Restructuring
The root `tests/` directory contains 23 flat files. These must be grouped by domain concern.

- **Proposed Structure:**
  - `tests/conftest.py` (Shared fixtures)
  - `tests/unit/` (e.g., `test_audit_log.py`, `test_doctor.py`)
  - `tests/cli/` (e.g., `test_harness_cli.py`, `test_cli_init.py`)
  - `tests/console/`
  - `tests/mcp/`
  - `tests/pipeline/`
  - `tests/inception/`
  - `tests/integrations/`
  - `tests/e2e/`
  - `tests/conformance/` (Keep as-is)
  - `tests/recon/` (Keep as-is)

### 3.2 Test Renaming
Milestone-named and phase-numbered tests must be renamed to reflect their feature scope.

- `test_console_m52.py` → `test_console_pipelines.py`
- `test_console_m53.py` → `test_console_screening.py`
- `test_console_m54.py` → `test_console_jobs.py`
- `test_phase1_e2e.py` → `test_e2e_search_screen.py`
- `test_phase2_e2e.py` → `test_e2e_extract_index.py`
- `test_phase3_e2e.py` → `test_e2e_synthesis.py`

### 3.3 Shared Fixtures (`conftest.py`)
Create a central `tests/conftest.py` to house shared fixtures, eliminating duplication across test files.
- `sample_protocol`
- `sample_papers`
- Mock objects and graphs
