"""Neutral workspace identity policy (HCM-02).

Owns mint/validate/require/recorded-or-minted with zero behavior change from
the two historical writers:

* ``require_recorded_identity`` replicates
  ``ResearchOrchestrator.recorded_workspace_id`` verbatim, including its
  observed defects: a valid-JSON non-object manifest raises untyped
  ``AttributeError`` (``manifest.get`` outside the ``try``), never a typed
  refusal. HCM-01 HC1-2 records this as OBSERVED-NOT-APPROVED; HCM-02 preserves
  it and regression-tests it. Do not "fix" it here without a separate
  behavior-decision packet.

* ``recorded_or_minted_workspace_id`` replicates
  ``genesis.recorded_or_minted_workspace_id`` verbatim (mint only when no
  manifest or no recorded field; typed refusal otherwise).

Consumers call ``require_recorded_identity`` and never mint. Initialization
calls ``recorded_or_minted_workspace_id`` only.
"""

from __future__ import annotations

import json
import re
import secrets
from pathlib import Path
from typing import Any

from ..contracts.identifiers import IdentifierKind, primary_prefix, validate_identifier
from .errors import RegisteredWorkspaceIdentityMissingError

#: Hex characters in the opaque part of a registered workspace identity.
SHA_LEN = 32

#: The registered workspace identity is exactly ``WSP-`` plus 32 lowercase hex.
#: Stricter than the registry's prefix check on purpose: the registry admits any
#: opaque ``WSP-`` limb, but a recorded identity that is not in canonical form is
#: legacy debt to be classified, not an identity to index under.
REGISTERED_WORKSPACE_ID = re.compile(rf"^WSP-[0-9a-f]{{{SHA_LEN}}}$")


def mint_registered_workspace_id() -> str:
    """Mint the registered workspace identity recorded in ``project.json``.

    The Contract v1 identifier registry admits exactly one registered form for a
    workspace, ``WSP-<opaque>`` (``IdentifierKind.WORKSPACE``), so a human slug
    such as ``evidence-synthesis`` is not a workspace identity and every typed
    surface refuses it. The registered identity is therefore minted here, once, at
    project initialization and recorded in ``project.json`` as
    ``registered_workspace_id``; ``project_id`` keeps the human slug.

    The suffix is 32 lowercase hex characters drawn from ``secrets`` (the OS
    CSPRNG), so two workspaces never collide and the value cannot be guessed from
    the title. The candidate is validated against the frozen registry before it is
    returned: a mint that would not validate is a bug, never a value to paper over.

    This is the only mint point for a workspace identity in the harness. Consumers
    must record and re-read it -- minting at use time would let one workspace
    present two identities, and deriving one from a slug would fabricate it.

    Mirrored in ``.agents/skills/workspace-manager/scripts/init_project.py``, the
    other ``project.json`` writer, which runs as a standalone script and so cannot
    import this package. Both writers are held to the same shape by
    ``tests/inception/test_registered_workspace_id.py``.
    """
    candidate = f"{primary_prefix(IdentifierKind.WORKSPACE)}{secrets.token_hex(16)}"
    return validate_identifier(IdentifierKind.WORKSPACE, candidate)


def validate_registered_workspace_id(value: str) -> str:
    """Return ``value`` if it is a registered workspace identity, else refuse.

    Enforces the canonical ``WSP-`` + 32 lowercase hex form *and* the frozen
    Contract v1 registry, so the harness never states an identity the typed
    surfaces would reject.
    """
    candidate = value.strip()
    if not REGISTERED_WORKSPACE_ID.fullmatch(candidate):
        raise RegisteredWorkspaceIdentityMissingError(
            f"{value!r} is not a registered workspace identity: the registered "
            f"form is WSP-<{SHA_LEN} lowercase hex>. Fix: replace the recorded "
            f"value with a registered identity, or re-create the workspace."
        )
    return validate_identifier(IdentifierKind.WORKSPACE, candidate)


def require_recorded_identity(workspace: Path | str) -> str:
    """Return the workspace identity recorded in ``project.json``.

    Consumer policy: records and re-reads only. Never mints, never derives the
    value from the project slug, never falls back. A workspace scaffolded before
    registered identities existed has no such field, and indexing under anything
    other than the recorded id would fabricate identity, so that case fails closed.

    Byte/message-compatible with ``ResearchOrchestrator.recorded_workspace_id``:
    the same typed messages for absent/corrupt/invalid, and the same observed
    untyped ``AttributeError`` for a valid-JSON non-object manifest (HCM-01 defect
    (a), preserved, not repaired).
    """
    ws = Path(workspace)
    manifest_path = ws / "project.json"
    manifest: dict[str, Any] = {}
    recorded: Any = None
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RegisteredWorkspaceIdentityMissingError(
                f"cannot read the recorded workspace identity from "
                f"{manifest_path}: {exc}. Repair or re-create project.json "
                f"(see: nexus-scholar init <title>, or add "
                f'"registered_workspace_id": "WSP-<32 hex>").'
            ) from exc
        # NOTE (HCM-01 defect (a), preserved): ``manifest.get`` is intentionally
        # outside the ``try`` so a JSON-array manifest raises ``AttributeError``,
        # exactly as the orchestrator does today. Do not coerce to a typed
        # refusal without a separate behavior-decision packet.
        recorded = manifest.get("registered_workspace_id")

    if not isinstance(recorded, str) or not recorded.strip():
        raise RegisteredWorkspaceIdentityMissingError(
            f"{manifest_path} records no 'registered_workspace_id'. Stage 6 "
            f"indexes under the workspace identity minted at inception and "
            f"will not substitute the project slug "
            f"({manifest.get('project_id')!r}) or mint a new one. "
            f"Fix: re-create the workspace so inception records a registered "
            f"identity (nexus-scholar init <title>), or add "
            f'"registered_workspace_id": "WSP-<32 hex>" to {manifest_path}.'
        )

    try:
        return validate_registered_workspace_id(recorded)
    except (TypeError, ValueError, RegisteredWorkspaceIdentityMissingError) as exc:
        raise RegisteredWorkspaceIdentityMissingError(
            f"{manifest_path} records 'registered_workspace_id' "
            f"({recorded!r}) which is not a registered workspace identity: "
            f"{exc}. Fix: replace it with a registered identity of the form "
            f"WSP-<32 lowercase hex>, or re-create the workspace."
        ) from exc


def recorded_or_minted_workspace_id(ws_dir: Path | str) -> str:
    """Resolve a workspace's identity under one fail-closed policy.

    Minting is permitted only when the workspace has no recorded identity to lose:
    a missing ``project.json``, or a readable manifest without the field. Every
    other case is a typed refusal rather than a fresh identity, because silently
    minting over recorded state is silent re-identification -- artifacts already
    accepted under the old id would no longer share a workspace.

    The policy, identical in both ``project.json`` creators:

    * no manifest / manifest without ``registered_workspace_id`` -> mint;
    * recorded value that is not ``WSP-<32 hex>`` -> refuse, naming the value;
    * unreadable, corrupt, or non-object ``project.json`` -> refuse, naming the
      path and the corruption.

    Byte/message-compatible with ``genesis.recorded_or_minted_workspace_id``.
    """
    ws = Path(ws_dir)
    manifest_path = ws / "project.json"
    if not manifest_path.is_file():
        return mint_registered_workspace_id()

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RegisteredWorkspaceIdentityMissingError(
            f"cannot read the recorded workspace identity from {manifest_path}: "
            f"{exc}. Repair or re-create project.json rather than minting over "
            f"recorded state (nexus-scholar init <title>)."
        ) from exc
    if not isinstance(manifest, dict):
        raise RegisteredWorkspaceIdentityMissingError(
            f"cannot read the recorded workspace identity from {manifest_path}: "
            f"it is not a JSON object. Repair or re-create project.json rather "
            f"than minting over recorded state."
        )

    recorded = manifest.get("registered_workspace_id")
    if recorded is None:
        # No identity has ever been recorded for this workspace, so there is no
        # lineage to destroy and minting creates rather than replaces one.
        return mint_registered_workspace_id()
    if not isinstance(recorded, str):
        raise RegisteredWorkspaceIdentityMissingError(
            f"{manifest_path} records 'registered_workspace_id' as "
            f"{type(recorded).__name__} ({recorded!r}) rather than a string. "
            f"Fix: replace it with a registered identity of the form "
            f"WSP-<{SHA_LEN} lowercase hex>."
        )
    return validate_registered_workspace_id(recorded)
