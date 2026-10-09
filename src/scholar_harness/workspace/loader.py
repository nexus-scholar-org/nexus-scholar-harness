"""Neutral skills-loader service (HCM-02).

Centralizes the P7.3 wheel-portable skills resolution with the same precedence
everywhere, CWD-independent:

    NEXUS_SKILLS_SRC env override -> wheel-bundled ``scholar_harness_data/skills``
    -> repository ``.agents/skills``.

Pure resolution only (no import cache here). Callers that need caching keep
their own module-level cache variables for backward compatibility with existing
monkeypatch seams (genesis ``_log_module_ref/_tried``, console
``_INDEX_MD_REFRESH``); they delegate resolution to these pure functions so the
precedence cannot drift.

Filesystem injection for tests: pass an explicit ``skills_root`` or set
``NEXUS_SKILLS_SRC`` to a ``tmp_path`` bundle; never touch a real checkout.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any

SKILL_SOURCE_ENV = "NEXUS_SKILLS_SRC"
_BUNDLED_SKILLS_PACKAGE = "scholar_harness_data"
_BUNDLED_SKILLS_REL = "skills"

_LOGIMPORT_NAME = "workspace_manager_log_event"

# REPO_ROOT resolved from this file's location (CWD-independent):
# src/scholar_harness/workspace/loader.py -> parents[3] == repo root.
REPO_ROOT = Path(__file__).resolve().parents[3]


def bundled_skills_root() -> Path | None:
    """Locate the skills tree bundled inside the installed distribution wheel."""
    try:
        spec = importlib.util.find_spec(_BUNDLED_SKILLS_PACKAGE)
    except (ImportError, ValueError):
        return None
    for location in getattr(spec, "submodule_search_locations", None) or []:
        candidate = Path(location) / _BUNDLED_SKILLS_REL
        if candidate.is_dir():
            return candidate
    return None


def resolve_skills_root() -> Path | None:
    """Resolve the skills source root (a dir of ``<name>/SKILL.md`` children).

    Precedence (P7.3): ``NEXUS_SKILLS_SRC`` env override, then the skills
    bundled inside the installed wheel, then the repository checkout's
    ``.agents/skills``. CWD-independent.
    """
    env = os.environ.get(SKILL_SOURCE_ENV)
    if env:
        candidate = Path(env).expanduser().resolve()
        if candidate.is_dir():
            return candidate
    bundled = bundled_skills_root()
    if bundled is not None:
        return bundled
    repo = REPO_ROOT / ".agents" / "skills"
    return repo if repo.is_dir() else None


def resolve_workspace_manager_scripts(
    skills_root: Path | None = None,
) -> Path | None:
    """Locate the workspace-manager ``scripts/`` dir (wheel-portable)."""
    skills = skills_root if skills_root is not None else resolve_skills_root()
    if skills is None:
        return None
    candidate = skills / "workspace-manager" / "scripts"
    return candidate if candidate.is_dir() else None


def load_log_module_uncached(
    scripts_dir: Path | None = None,
    *,
    import_name: str = _LOGIMPORT_NAME,
) -> Any | None:
    """Load ``log_event.py`` in-process without caching.

    Mirrors ``genesis._load_log_module`` resolution but performs no global
    caching, so fault-injection tests stay hermetic: set ``NEXUS_SKILLS_SRC``
    to a ``tmp_path`` bundle or pass ``scripts_dir`` explicitly. Returns
    ``None`` when the script is unreachable or lacks ``log_project_event``.
    """
    scripts = (
        scripts_dir if scripts_dir is not None else resolve_workspace_manager_scripts()
    )
    if scripts is None:
        return None
    script = scripts / "log_event.py"
    if not script.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location(import_name, script)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        # Register under a distinct name so wheel and console copies coexist.
        # Use a unique key per import_name to avoid clobbering across callers.
        sys.modules[import_name] = module
        spec.loader.exec_module(module)
        if not hasattr(module, "log_project_event"):
            return None
        return module
    except (ImportError, OSError, TypeError, ValueError, SyntaxError, AttributeError):
        return None


def load_index_refresher_uncached(
    scripts_dir: Path | None = None,
) -> Any | None:
    """Load ``refresh_index_md`` from the workspace-manager skill (uncached)."""
    module = load_log_module_uncached(
        scripts_dir, import_name="workspace_manager_log_event_refresh"
    )
    if module is None:
        return None
    refresher = getattr(module, "refresh_index_md", None)
    return refresher if callable(refresher) else None
