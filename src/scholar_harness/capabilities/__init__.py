"""``scholar_harness.capabilities`` — agent-layer Phase E.

Spec: ``specs/agent-layer-portability/04_capability_adapter_and_app_surface.md``
(§1-§3, §6) and the Phase-E deliverable rows of
``specs/agent-layer-portability/05_migration_plan.md``.

The adapter makes every independence guarantee a *filesystem fact* instead of a
sentence in a prompt:

* **CapabilityAdapter** — the one small interface (spec 04 §1).
* **InProcessAdapter** — the application: enforced run view, path validation,
  egress policy, adapter-written audit.
* **OpencodeAdapter** — the dev loop: best-effort, honestly documented.

Enforcement is shell, not science: roles receive a
:class:`~scholar_harness.capabilities.adapter.RoleSession` whose read/write/
list/network operations are constrained by the role record
(``roles/<id>.json``, Phase A). ``Envelope@1`` (Phase B) carries the result;
``HumanConfirmation@1`` (Phase C) and portability (Phase D) sit untouched.

:func:`run_role` is the dispatch entry point: a caller names
``"in-process"`` or ``"opencode"`` and receives a validated ``Envelope``
without importing either concrete class. **No CLI entrypoint calls it yet** —
wiring the application/CLI surface to it is a separate product decision, so
this module deliberately adds no command.

``Envelope@1`` carries at most one output payload. Multi-artifact runs are
represented by ``coverage`` plus the adapter-written journal; non-JSON or
schema-invalid artifacts are ``INVALID_OUTPUT``.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from ..contracts.envelope.model import Envelope
from .adapter import (
    AuditEvent,
    CapabilityAdapter,
    ContractViolation,
    EgressRefused,
    ENV_BINDING_TABLE,
    RoleSession,
    RunRequest,
    ScopeViolation,
)
from .inprocess import InProcessAdapter
from .opencode import OpencodeAdapter


def run_role(
    adapter_name: Literal["in-process", "opencode"],
    request: RunRequest,
    handler: Callable[[RoleSession], Any],
    *,
    workspace: Path,
    roles_dir: Path,
    root: Path | None,
    **adapter_options: Any,
) -> Envelope:
    """Run one role on the named surface and return its validated envelope.

    ``root`` is the **repository/enclosing tree** and is required — there is no
    default. ``workspace`` is the project directory *under* it
    (``<root>/workspaces/<slug>``). Defaulting ``root`` to ``workspace`` (the
    old behaviour) published into a nested ``ws/workspaces/<slug>/…`` tree that
    no other harness code reads, so a missing root, ``root=None``, a
    workspace that is not inside ``root``, or a workspace *equal* to ``root``
    is a :class:`ScopeViolation` **before** any adapter runs. The equality case
    would publish ``runs/`` and the audit journal at the repository root while
    the workspace tree stays where the other harness code reads it — one run
    split across two trees (P3-11).

    An unknown name is a :class:`ScopeViolation`, not an envelope:
    ``Envelope@1.provenance.adapter`` is the closed literal
    ``["opencode", "in-process"]`` and cannot carry an invented surface name.
    """
    if root is None:
        raise ScopeViolation(
            "run_role requires root=...: root is the repository/enclosing tree "
            "and workspace the project under it; defaulting root to the "
            "workspace would publish into a nested workspaces/<slug>/ tree no "
            "other harness code reads"
        )
    workspace_path = Path(workspace)
    root_path = Path(root)
    if workspace_path.resolve() == root_path.resolve():
        raise ScopeViolation(
            f"workspace {workspace_path} must be a project directory under "
            f"root {root_path}, not root itself: workspace == root publishes "
            "runs/ and the audit journal at the repository root, splitting one "
            "run across two trees (projects live at <root>/workspaces/<slug>)"
        )
    if not workspace_path.resolve().is_relative_to(root_path.resolve()):
        raise ScopeViolation(
            f"workspace {workspace_path} is not inside root {root_path}: root "
            "must be the repository/enclosing tree that contains the workspace "
            "(projects live at <root>/workspaces/<slug>)"
        )
    if adapter_name == "in-process":
        adapter = InProcessAdapter(
            root=root_path,
            workspace=workspace_path,
            roles_dir=roles_dir,
            **adapter_options,
        )
    elif adapter_name == "opencode":
        adapter = OpencodeAdapter(
            workspace=workspace_path,
            roles_dir=roles_dir,
            **adapter_options,
        )
    else:
        raise ScopeViolation(
            f"unknown adapter {adapter_name!r}: the harness knows 'in-process' "
            "and 'opencode' only; Envelope@1 provenance.adapter cannot carry "
            "another surface name"
        )
    return adapter.run(request, handler)


__all__ = [
    "AuditEvent",
    "CapabilityAdapter",
    "ContractViolation",
    "ENV_BINDING_TABLE",
    "EgressRefused",
    "Envelope",
    "InProcessAdapter",
    "OpencodeAdapter",
    "RoleSession",
    "RunRequest",
    "ScopeViolation",
    "run_role",
]
