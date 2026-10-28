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
"""

from __future__ import annotations

from .adapter import (
    AuditEvent,
    CapabilityAdapter,
    EgressRefused,
    RoleSession,
    RunRequest,
    ScopeViolation,
)
from .inprocess import InProcessAdapter
from .opencode import OpencodeAdapter

__all__ = [
    "AuditEvent",
    "CapabilityAdapter",
    "EgressRefused",
    "InProcessAdapter",
    "OpencodeAdapter",
    "RoleSession",
    "RunRequest",
    "ScopeViolation",
]
