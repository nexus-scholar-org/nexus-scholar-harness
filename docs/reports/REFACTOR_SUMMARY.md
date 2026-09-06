# Plugin Harness Refactor - Summary

## ✅ Work Completed

### 1. UTF-8 Encoding Fix for Windows
**File**: `scripts/install_plugins.py`

**Problem**: Windows console defaults to cp1252, causing `UnicodeEncodeError` when printing emojis.

**Solution**: Enhanced UTF-8 reconfiguration with dual-strategy approach:
- Strategy 1: Use `TextIOWrapper.reconfigure()` (Python 3.7+)
- Strategy 2: Wrap streams with `io.TextIOWrapper` if reconfigure unavailable

**Status**: ✅ Tested and verified - all emojis display correctly without errors

### 2. Plugin Installer Script
**File**: `scripts/install_plugins.py`

**Features**:
- Discovers plugins from `.agents/plugins/nexus-scholar/plugins.json`
- Searches for local checkouts (editable mode) with Git fallback
- Installs in dependency order
- Creates shared `.venv/` (no per-tool venvs)
- Verifies console scripts after installation
- Full emoji output with UTF-8 support

**Usage**:
```bash
# Automatic discovery (local-first, Git fallback)
uv run python scripts/install_plugins.py

# Git-only (no local checkouts)
uv run python scripts/install_plugins.py --git-only

# Clean legacy .venv directories
uv run python scripts/install_plugins.py --clean
```

### 3. Updated Project Configuration

#### `.gitignore`
- Added `tools/` to ignore external plugins

#### `README.md`
- Replaced `uv sync --project tools/X` with unified `uv run scripts/install_plugins.py`
- Updated all workflow examples to use `uv run scholar-search`, `uv run scholar-pdf`, etc.
- Updated repository structure documentation
- Clarified that plugins are NOT vendored

#### `pyproject.toml`
- Already slim (only harness orchestrator dependencies)
- No changes needed

### 4. Continuous Integration
**File**: `.github/workflows/ci.yml`

**Tests**:
- Lint with ruff
- Plugin installer smoke test (help + --git-only install)
- Plugin manifest JSON validation
- Workspace-manager CLI verification
- Multi-platform (Ubuntu, Windows, macOS)
- Multi-Python (3.11, 3.12)

### 5. Helper Scripts
- `scripts/validate_manifest.py`: Validates plugin manifest structure
- `scripts/pre_commit_check.py`: Pre-commit verification checklist

## 📊 Verification Results

All smoke tests pass:
- ✅ Plugin installer executes without encoding errors
- ✅ Emojis display correctly on Windows
- ✅ Plugin manifest is valid (6 plugins)
- ✅ Workspace-manager is functional
- ✅ .gitignore correctly ignores tools/
- ✅ README describes plugin installation
- ✅ CI workflow configured
- ✅ tools/ is tracked in git (will be removed)

## 🚀 Next Steps (Manual Git Operations)

```bash
# Stage all modified and new files
git add -A

# Remove tools/ from git tracking (keep local copies)
git rm -r --cached tools/

# Create commit
git commit -m "Refactor: Move tools to external plugins with unified installer

- Add scripts/install_plugins.py with UTF-8 encoding fix for Windows emojis
- Support local checkouts (editable installs) with automatic Git fallback
- Create shared .venv instead of per-tool virtual environments
- Update README with plugin installation instructions
- Add GitHub Actions CI workflow (lint + install + manifest validation)
- Update .gitignore to exclude external tools/ directory
- Add validation and pre-commit check utilities"

# Push to remote
git push origin main
```

## 📝 Architecture Overview

### Before (Vendored Tools)
```
harness/
├── tools/
│   ├── scholar-search-kit/  (full clone)
│   ├── scholar-pdf-kit/     (full clone)
│   └── ...                   (other kits)
├── scripts/
└── README (instructs: uv sync --project tools/X)
```

### After (External Plugins)
```
harness/
├── scripts/
│   ├── install_plugins.py   (unified installer)
│   ├── validate_manifest.py
│   └── pre_commit_check.py
├── .agents/plugins/
│   └── nexus-scholar/
│       └── plugins.json     (registry)
├── .github/
│   └── workflows/
│       └── ci.yml           (GitHub Actions)
├── .gitignore (ignores tools/)
└── README (instructs: python scripts/install_plugins.py)
```

### Plugin Discovery
1. **Local Editable Mode** (development): `tools/`, `../`, `../../`, custom `--dev-path`
2. **Git Fallback** (production): Clone from GitHub at specified branch/tag
3. **Single Shared .venv**: All plugins in one environment, reduces disk usage

## 🎯 Benefits

1. **Development-Friendly**: Keep local clones in `tools/` or `--dev-path` for editable installs
2. **Production-Ready**: Automatic Git fallback for deployment scenarios
3. **Cross-Platform**: UTF-8 encoding fix works on Windows/macOS/Linux
4. **CI/CD Integration**: GitHub Actions validates manifest and tests installation
5. **Reduced Disk Usage**: Shared environment instead of N per-tool venvs
6. **Single Source of Truth**: Each kit has one repo, no vendored copies

## ⚠️ Important Notes

- After `git rm -r --cached tools/`, the local `tools/` directory is still present but not tracked by git
- Developers with local clones can keep them for editable installs: `python scripts/install_plugins.py`
- Production deployments use Git fallback: `python scripts/install_plugins.py --git-only`
- Windows users benefit from UTF-8 encoding fix for emoji output in install logs
