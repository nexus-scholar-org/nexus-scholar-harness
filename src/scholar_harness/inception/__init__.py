from __future__ import annotations

import os
import sys
import types

from . import display, genesis, grounded, intent, wizard
from .display import console, show_refraction_grid
from .genesis import (
    INIT_MARKERS,
    REPO_ROOT,
    resolve_skills_root,
    resolve_workspace_manager_scripts,
    _load_log_module,
    _log_project_event,
    _bundled_skills_root,
    _log_module_ref,
    _log_module_tried,
    compile_protocol_files,
    scaffold_project,
    scaffold_raw_project,
    log_genesis,
    install_skills,
    write_mcp_json,
    write_env_example,
    require_uninitialized,
)
from .grounded import (
    _is_junk_term_label,
    _family_tokens,
    _grounded_directions_for_terms,
    _run_grounded_recon,
    _enforce_grounded_anchors,
    _grounded_default_concepts,
    _now_iso,
)
from .intent import (
    ALL_PLAYBOOKS,
    DESIGN_SCIENCE_KEYWORDS,
    INTERPRETIVIST_FORBIDDEN,
    INTERPRETIVIST_KEYWORDS,
    PARADIGM_KEYWORDS,
    PARADIGM_PROFILE,
    PLAYBOOK_RECOMMENDATION,
    POSITIVIST_KEYWORDS,
    PRAGMATIST_KEYWORDS,
    TRUSTWORTHINESS_FRAMEWORK,
    ConceptDraft,
    RQDraft,
    Survey,
    detect_leanings,
    draft_default_concepts,
    enforce_lexicon,
    make_intent,
    recommend_playbook,
    refraction_rows,
    slugify,
)
from .wizard import (
    ConsoleResponder,
    Responder,
    inception_command,
    init_command,
    run_wizard,
)

__all__ = [
    "ALL_PLAYBOOKS",
    "ConsoleResponder",
    "ConceptDraft",
    "DESIGN_SCIENCE_KEYWORDS",
    "INIT_MARKERS",
    "INTERPRETIVIST_FORBIDDEN",
    "INTERPRETIVIST_KEYWORDS",
    "PARADIGM_KEYWORDS",
    "PARADIGM_PROFILE",
    "PLAYBOOK_RECOMMENDATION",
    "POSITIVIST_KEYWORDS",
    "PRAGMATIST_KEYWORDS",
    "REPO_ROOT",
    "RQDraft",
    "Responder",
    "Survey",
    "TRUSTWORTHINESS_FRAMEWORK",
    "_enforce_grounded_anchors",
    "_family_tokens",
    "_grounded_directions_for_terms",
    "_is_junk_term_label",
    "_load_log_module",
    "_log_project_event",
    "_run_grounded_recon",
    "compile_protocol_files",
    "console",
    "detect_leanings",
    "draft_default_concepts",
    "enforce_lexicon",
    "inception_command",
    "init_command",
    "log_genesis",
    "make_intent",
    "recommend_playbook",
    "refraction_rows",
    "resolve_skills_root",
    "resolve_workspace_manager_scripts",
    "run_wizard",
    "scaffold_project",
    "scaffold_raw_project",
    "show_refraction_grid",
    "slugify",
    "_now_iso",
]


class _InceptionModule(types.ModuleType):
    def __getattribute__(self, name: str) -> object:
        if name in ("_log_module_ref", "_log_module_tried"):
            return getattr(genesis, name)
        return super().__getattribute__(name)

    def __setattr__(self, name: str, value: object) -> None:
        super().__setattr__(name, value)
        for submod in (genesis, grounded, intent, wizard, display):
            if hasattr(submod, name):
                setattr(submod, name, value)


sys.modules[__name__].__class__ = _InceptionModule


