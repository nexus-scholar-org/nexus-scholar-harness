"""Neutral workspace service facade (HCM-02).

Thin re-exports only; no logic here. Dependency direction::

    contracts / screening / pipelines / console / CLI  ->  workspace.*

``workspace`` imports only contracts identifiers, stdlib, and its own
submodules -- never console transport, never kits.
"""

from __future__ import annotations

from .audit import (
    append_event,
    append_legacy_event,
    log_event,
    refresh_index,
    refresh_index_atomic,
    resolve_workspace,
)
from .errors import NotWorkspaceError, RegisteredWorkspaceIdentityMissingError
from .identity import (
    REGISTERED_WORKSPACE_ID,
    SHA_LEN,
    mint_registered_workspace_id,
    recorded_or_minted_workspace_id,
    require_recorded_identity,
    validate_registered_workspace_id,
)
from .loader import (
    bundled_skills_root,
    load_index_refresher_uncached,
    load_log_module_uncached,
    resolve_skills_root,
    resolve_workspace_manager_scripts,
)
from .manifest import read_manifest, update_manifest_for_event

__all__ = [
    "NotWorkspaceError",
    "REGISTERED_WORKSPACE_ID",
    "RegisteredWorkspaceIdentityMissingError",
    "SHA_LEN",
    "append_event",
    "append_legacy_event",
    "bundled_skills_root",
    "load_index_refresher_uncached",
    "load_log_module_uncached",
    "log_event",
    "mint_registered_workspace_id",
    "read_manifest",
    "recorded_or_minted_workspace_id",
    "refresh_index",
    "refresh_index_atomic",
    "require_recorded_identity",
    "resolve_skills_root",
    "resolve_workspace",
    "resolve_workspace_manager_scripts",
    "update_manifest_for_event",
    "validate_registered_workspace_id",
]
