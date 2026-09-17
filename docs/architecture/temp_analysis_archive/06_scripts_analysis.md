# Scripts Directory Comprehensive Analysis

**Date:** 2026-09-14
**Directory:** `C:\Users\mouadh\Documents\nexus-scholar-harness\scripts\`

---

## 1. Complete Script Listing

| Script | Lines | Purpose | Category |
|--------|-------|---------|----------|
| `install_plugins.py` | 357 | Unified plugin installer for all 8 scholarly toolkits | Deployment |
| `generate_nexus_scholar_pins.py` | 116 | Code generation for metapackage pins | Code Generation |
| `validate_manifest.py` | 35 | Validates plugin manifest structure | Validation |
| `pre_commit_check.py` | 112 | Pre-commit checklist for plugin harness refactor | Validation |
| `push_tools.py` | 82 | Push toolkit changes to remote repositories | Deployment |
| `generate_latex.py` | 137 | Generate XeLaTeX manuscripts from markdown sources | Code Generation |
| `sync_skills_bundle.py` | 84 | Sync canonical skills to plugin bundle | Synchronization |
| `reconcile_dual_screening.py` | 416 | Reconcile dual-screening decisions for literature review | Data Processing |
| `hooks/pre-push` | 38 | Git pre-push hook enforcing contribution workflow | CI/CD |

---

## 2. Automation Workflows

### 2.1 Plugin Installation Pipeline (`install_plugins.py`)
**Location:** `scripts/install_plugins.py` (lines 1-357)

**Key Features:**
- **Dependency-ordered installation** (line 77-85): Kits installed in order: protocol -> search -> pdf -> bib -> graph -> rag -> agent
- **Dual installation modes**: Local editable (`-e`) vs. Git remote installation
- **Environment detection**: Checks `NEXUS_PLUGIN_PATH` env var and `tools/` directory
- **Legacy cleanup**: Removes per-tool `.venv` directories (line 140-157)
- **Post-install verification**: Runs `--help` on each console_script (line 215-246)

**CLI Options:**
- `--manifest`: Path to plugins.json (default: `.agents/plugins/nexus-scholar/plugins.json`)
- `--plugin/-p`: Install specific plugin only
- `--dev-path/-d`: Custom dev path for kit sources
- `--git-only`: Force remote Git installation
- `--local-only`: Only install from local checkouts
- `--upgrade/-U`: Upgrade installed packages
- `--clean`: Remove legacy per-tool .venv directories
- `--verify/--no-verify`: Post-install verification

**Windows Compatibility:** Lines 27-71 handle UTF-8 encoding for emojis on Windows console.

### 2.2 Toolkit Synchronization (`push_tools.py`)
**Location:** `scripts/push_tools.py` (lines 1-82)

**Workflow:**
1. Reads plugin manifest from `.agents/plugins/nexus-scholar/plugins.json`
2. For each toolkit in `tools/`:
   - Clones remote repository (shallow clone, `--depth 1`)
   - Copies local changes to cloned repo (excluding `.git`, `.venv`, `.pytest_cache`, etc.)
   - Commits with message: `feat(<name>): synchronize toolkit with nexus-scholar monorepo`
   - Pushes to `main` branch

**Error Handling:** Graceful fallback if clone fails (initializes fresh repo).

### 2.3 Skills Bundle Synchronization (`sync_skills_bundle.py`)
**Location:** `scripts/sync_skills_bundle.py` (lines 1-84)

**Purpose:** Mirror canonical `.agents/skills/<name>` trees into the plugin bundle.

**Key Logic:**
- Canonical source: `.agents/skills/` (always edited first)
- Target: `.agents/plugins/nexus-scholar/skills/`
- **Intentional exclusions** (line 27): `pull-request-gate` is excluded from mirroring
- **Drift detection**: `--check` mode reports differences without copying
- **File comparison**: Uses `filecmp.cmp` for byte-identical verification

---

## 3. Build and Deployment Processes

### 3.1 Metapackage Pins Generation (`generate_nexus_scholar_pins.py`)
**Location:** `scripts/generate_nexus_scholar_pins.py` (lines 1-116)

**Purpose:** Generate deterministic pins snapshot for `packaging/nexus-scholar/` metapackage.

**Data Flow:**
- **Input**: `.agents/plugins/nexus-scholar/plugins.json` (source of truth for kit versions)
- **Output**: `packaging/nexus-scholar/nexus_scholar_pins.json`

**Key Features:**
- **Deterministic output**: Kits sorted by name, fixed field order (line 34-39)
- **CI freshness check**: `--check` flag fails CI when pins drift (line 62-65)
- **Cross-platform support**: Normalizes CRLF to LF for Windows compatibility (line 52-59)
- **Diff output**: Shows exact changes needed when drift detected (line 68-75)

**Fields Captured per Kit:**
- `name`, `repo`, `default_rev` (commit SHA), `console_script`

### 3.2 LaTeX Manuscript Generation (`generate_latex.py`)
**Location:** `scripts/generate_latex.py` (lines 1-137)

**Purpose:** Generate XeLaTeX manuscripts from committed markdown sources.

**Deliverables Configured (lines 66-100):**
1. **d1**: UAV-CV precision agriculture manuscript
2. **d2**: AI research harnesses trust manuscript (d2)
3. **d3**: AI research harnesses trust main manuscript
4. **d4**: Software paper scope document
5. **thesis**: Thesis assembly document

**Build Process:**
- Uses `pandoc` for Markdown -> LaTeX conversion
- Applies custom XeLaTeX preamble with:
  - Times New Roman font
  - Math symbols (->)
  - Table formatting (booktabs, longtable)
  - Figure scaling (pandocbounded)
  - Hyperlinks and fancy headers

**Build Command:** `cd latex/<name> && xelatex -output-directory=build main.tex (x2)`

---

## 4. Code Generation Patterns

### 4.1 Deterministic Pin Generation Pattern
**File:** `generate_nexus_scholar_pins.py`

**Pattern:**
```python
# Input: plugins.json with full metadata
# Transform: Extract specific fields, sort alphabetically
# Output: Deterministic JSON with fixed key order
kits = [
    {field: plugin[field] for field in FIELDS}
    for plugin in manifest["plugins"]
]
kits.sort(key=lambda kit: kit["name"])
```

**Why Deterministic?**
- CI enforces freshness with `--check`
- Prevents accidental drift between source of truth and metapackage
- Byte-identical output enables strict equality checks

### 4.2 Skills Mirroring Pattern
**File:** `sync_skills_bundle.py`

**Pattern:**
```python
# Canonical source -> Bundle target
# Exclusion list for repo-policy skills
# File-level comparison for drift detection
src = CANONICAL / name
dst = BUNDLE / name
drifted = not (dst.is_dir() and _same_tree(src, dst))
```

---

## 5. Utility Functions

### 5.1 Plugin Registry Loader (`install_plugins.py`, lines 88-100)
```python
def load_registry(manifest_path: Path) -> list[dict[str, Any]]:
    """Loads plugin list from JSON registry."""
```
- Validates manifest exists
- Extracts `plugins` array
- Returns structured plugin data

### 5.2 Local Path Resolution (`install_plugins.py`, lines 103-132)
```python
def resolve_local_path(
    plugin_name: str,
    custom_dev_path: Path | None = None,
    repo_root: Path = Path("."),
) -> Path | None:
```
- Checks multiple candidate paths:
  - Custom dev path
  - `NEXUS_PLUGIN_PATH` environment variable
  - `tools/<plugin_name>` (local checkout)
  - Sibling directories (`../<plugin_name>`, `../../<plugin_name>`)

### 5.3 Legacy Venv Cleanup (`install_plugins.py`, lines 140-157)
```python
def clean_legacy_venvs(repo_root: Path) -> None:
```
- Removes `tools/*/.venv` directories
- Prevents duplicate disk usage from per-tool virtual environments

### 5.4 Installation Verification (`install_plugins.py`, lines 215-246)
```python
def verify_installation(plugins: list[dict[str, Any]]) -> dict[str, bool]:
```
- Runs `<console_script> --help` for each installed plugin
- Returns success/failure map
- Catches `FileNotFoundError` for missing commands

### 5.5 UTF-8 Encoding Handler (`install_plugins.py`, lines 27-71)
```python
def _reconfigure_encoding_for_utf8() -> None:
```
- Windows-specific: Reconfigures stdout/stderr for emoji support
- Strategy 1: `reconfigure()` method (Python 3.7+)
- Strategy 2: Wrap streams with `io.TextIOWrapper`

### 5.6 Tree Comparison (`sync_skills_bundle.py`, lines 38-42)
```python
def _same_tree(a: Path, b: Path) -> bool:
```
- Compares file lists (excluding `__pycache__`, `.pyc`)
- Byte-level file comparison with `filecmp.cmp(shallow=False)`

---

## 6. CI/CD Integration

### 6.1 Git Pre-Push Hook (`scripts/hooks/pre-push`)
**Location:** `scripts/hooks/pre-push` (lines 1-38)

**Purpose:** Enforce contribution workflow - all improvements must go through fork + PR.

**Logic:**
- Only gates pushes to `origin` (canonical repo)
- **Allowed refs:**
  - `refs/heads/main` (housekeeping baseline)
  - `refs/tags/*` (release tags)
- **Blocked refs:** All other branches with instructions to use fork + PR

**Installation:** `git config core.hooksPath scripts/hooks`

**Error Message (lines 28-32):**
```
BLOCKED: pushing '<ref>' directly to origin (canonical repo).
  Improve on the fork and submit a pull request instead:
    git push fork <ref>
    gh pr create -R nexus-scholar-org/nexus-scholar-harness --base main
  See .agents/skills/pull-request-gate/SKILL.md
```

### 6.2 Manifest Validation (`validate_manifest.py`)
**Purpose:** Validates plugin manifest structure for CI.

**Checks:**
- Manifest file exists at expected path
- `plugins` array is non-empty
- Each plugin has required fields: `name`, `repo`, `default_rev`, `console_script`

**Exit Codes:**
- 0: All validations passed
- 1: Validation failed

### 6.3 Pre-Commit Checklist (`pre_commit_check.py`)
**Purpose:** Comprehensive pre-commit validation for plugin harness refactor.

**Checks Performed (lines 19-88):**
1. Validate plugin manifest (JSON structure, non-empty)
2. Check `install_plugins.py` syntax (`py_compile`)
3. Verify `.gitignore` includes `tools/`
4. Check README describes plugin installer
5. Verify GitHub Actions CI workflow exists
6. Check `tools/` is tracked in git (expected state)

**Output:** Pass/fail summary with recommended git commands.

### 6.4 CI Integration Points
Based on AGENTS.md and script analysis:

**CI Workflow (referenced but not found in repo):**
- Lint: `uv run ruff check scripts/`
- Plugin installer help: `uv run python scripts/install_plugins.py --help`
- Manifest schema validation: `uv run python scripts/validate_manifest.py`
- Pins freshness: `uv run python scripts/generate_nexus_scholar_pins.py --check`
- Skills drift: `uv run python scripts/sync_skills_bundle.py --check`

---

## 7. Data Processing Scripts

### 7.1 Dual-Screening Reconciliation (`reconcile_dual_screening.py`)
**Location:** `scripts/reconcile_dual_screening.py` (lines 1-416)

**Purpose:** Synchronize dual-screening decisions, 3rd-party adjudication, and Option B (Provisional 150) into primary literature deliverables.

**Input Files:**
- `literature/verified.json` - 1488 verified documents
- `literature/screening/batch_*_decisions.json` - Screener 1 decisions
- `literature/screening/batch_*_decisions_screener2.json` - Screener 2 decisions
- `literature/screening/_adjudication_resolved_group_*.json` - Adjudication decisions
- `literature/screening/_final_reconciled_include.txt` - 111 confirmed include IDs

**Processing Logic (lines 26-238):**
1. Load all screening decisions
2. Identify 39 caveat papers:
   - 22 papers with missing abstracts
   - 17 contested EXC-06 papers with in-scope cues
3. Partition documents into:
   - Included (111 confirmed + 39 provisional)
   - Excluded (1338 confirmed)
   - Conflicts (690 disputed)
4. Build structured document records with screening metadata

**Output Files:**
- `literature/included.json` - 150 papers (111 + 39)
- `literature/excluded.json` - 1338 papers
- `literature/conflicts.json` - 690 disputed papers
- `literature/screening/adjudicated_caveats.json` - 39 caveat papers
- `literature/prisma_report.json` - PRISMA metrics
- `literature/prisma_screening_report.md` - Detailed markdown report
- `literature/conflict_adjudication_log.md` - Audit ledger

**Key Metrics (lines 263-274):**
- Total identified: 1837
- Duplicates removed: 349
- Records screened: 1488
- Cohen's Kappa: 0.115 (slight agreement)
- Conflicts adjudicated: 690

**Domain-Specific Logic:**
- Agricultural UAV CV terminology regex (line 72): `crop|weed|vegetation|segmentation|UAV|drone|wheat|maize|corn|rice|canola|soybean|field|row`
- EXC-06 exclusion code handling for incomplete benchmark data

---

## 8. Areas for Improvement

### 8.1 Robustness Issues

**1. Error Handling in `push_tools.py`**
- Lines 63-68: `commit_res.stdout.splitlines()[0]` may raise IndexError if stdout is empty
- Lines 71-80: Push failure is logged but not raised as error
- **Recommendation:** Add explicit error propagation for push failures

**2. Path Validation in `generate_latex.py`**
- Lines 66-100: Hardcoded workspace paths assume specific directory structure
- **Recommendation:** Add path existence checks before processing

**3. Regex Sensitivity in `reconcile_dual_screening.py`**
- Line 72: Agricultural terminology regex is project-specific
- **Recommendation:** Make regex configurable or parameterized

### 8.2 Security Concerns

**1. Shell Injection in `pre_commit_check.py`**
- Line 9: `shell=True` in `subprocess.run` with string command
- **Recommendation:** Use list form: `["uv", "run", "python", "-m", "py_compile", "scripts/install_plugins.py"]`

**2. Temporary Directory Usage in `push_tools.py`**
- Lines 29-82: Clones remote repos to temp directory
- **Recommendation:** Ensure temp directory cleanup on failure

### 8.3 Maintainability Issues

**1. Hardcoded Paths**
- `reconcile_dual_screening.py` line 22: `WORKSPACE = REPO_ROOT / "workspaces" / "uav-cv-precision-agriculture"`
- `generate_latex.py` lines 66-100: Multiple hardcoded workspace paths
- **Recommendation:** Accept workspace path as CLI argument

**2. Magic Numbers**
- `reconcile_dual_screening.py` line 85: `assert len(caveat_39_ids) == 39`
- **Recommendation:** Extract to named constants or config

**3. DRY Violations**
- `install_plugins.py` and `validate_manifest.py` both load and validate plugins.json
- **Recommendation:** Extract shared validation logic

### 8.4 Testing Gaps

**1. No Unit Tests**
- Scripts directory has no `test_*.py` files
- **Recommendation:** Add tests for:
  - Plugin registry loading
  - Path resolution logic
  - Pin generation determinism
  - Skills synchronization

**2. Integration Testing**
- CI runs `--help` checks but not full installation
- **Recommendation:** Add integration test that installs one kit in isolated env

### 8.5 Documentation

**1. Missing Docstrings**
- `push_tools.py`: No module-level docstring
- `validate_manifest.py`: Minimal function docstrings
- **Recommendation:** Add comprehensive docstrings

**2. Usage Examples**
- Scripts lack usage examples in docstrings
- **Recommendation:** Add examples in `"""..."""` blocks

### 8.6 Performance Considerations

**1. Sequential Processing in `push_tools.py`**
- Lines 18-82: Processes toolkits sequentially
- **Recommendation:** Consider parallel processing for multiple kits

**2. Full File Reads**
- `reconcile_dual_screening.py`: Reads entire JSON files into memory
- **Recommendation:** For large datasets, consider streaming parsing

### 8.7 Cross-Platform Compatibility

**1. Path Separators**
- All scripts use `pathlib.Path` (good)
- `.gitignore` check in `pre_commit_check.py` line 48: String matching may fail on different line endings
- **Recommendation:** Normalize line endings before comparison

**2. Encoding Handling**
- `install_plugins.py` handles Windows UTF-8 (good)
- Other scripts lack explicit encoding handling
- **Recommendation:** Add `encoding="utf-8"` to all `open()` calls

---

## 9. Script Dependencies

### External Tools Required
- `uv`: Package installer (used by install_plugins.py, generate_latex.py)
- `pandoc`: Document conversion (used by generate_latex.py)
- `xelatex`: LaTeX compilation (referenced in generate_latex.py docstring)
- `git`: Version control (used by push_tools.py, pre-push hook)

### Internal Dependencies
- `.agents/plugins/nexus-scholar/plugins.json`: Source of truth for kit versions
- `tools/<kit>/`: Local kit checkouts
- `workspaces/<project>/`: Research output directories

---

## 10. Summary

The `scripts/` directory contains **9 automation scripts** covering:

- **Deployment (2 scripts):** Plugin installation and toolkit synchronization
- **Code Generation (2 scripts):** Metapackage pins and LaTeX manuscripts
- **Validation (2 scripts):** Manifest validation and pre-commit checks
- **Data Processing (1 script):** Dual-screening reconciliation
- **Synchronization (1 script):** Skills bundle mirroring
- **CI/CD (1 script):** Git pre-push hook

**Strengths:**
- Well-structured plugin architecture with dependency ordering
- Deterministic code generation with CI freshness checks
- Comprehensive validation and verification
- Cross-platform compatibility (Windows UTF-8 handling)

**Weaknesses:**
- No unit tests for scripts
- Hardcoded paths reduce flexibility
- Some error handling gaps
- Documentation could be more comprehensive

**Overall Assessment:** The scripts provide a solid foundation for the Nexus Scholar Harness automation, with clear separation of concerns and good engineering practices. The main areas for improvement are testing coverage, parameterization, and error handling robustness.
