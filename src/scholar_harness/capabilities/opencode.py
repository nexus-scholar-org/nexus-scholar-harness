"""``OpencodeAdapter`` — the dev-loop surface: **best-effort** capability.

Spec 04 §1 implementation table. The dev loop is *not* a sandbox; the
application is. One implementation must not claim both, so this adapter is
explicitly honest about what it cannot do (Phase-E acceptance criterion 5).

## Residual risk (documented, deliberately not resolved here)

The dev loop runs inside OpenCode's tool model, where the *operator is the
owner* (spec 04 §1). Enforcement is tri-state permissions plus adapter-side
path checks before and after each phase — e.g. ``scripts/select_test_gate.py``,
the generated permission fragments from Phase A, and the ``SCOPE_VIOLATION``
boundary checks of :class:`scholar_harness.capabilities.adapter.RoleSession`
staged runs. What it **cannot** guarantee, unlike InProcessAdapter:

1. **Filesystem writes outside the boundary are possible.** A misbehaving
   agent can direct ``bash`` at any path on the host; nothing here blocks the
   syscall. Mitigation: the pre/post path checks log violations loudly, and
   the push/PR gates catch diffs to published trees.
2. **Network egress is cooperative.** There is no socket-level guard in dev
   mode; ``network: deny`` is honoured by the agent's discipline plus tool
   policy, not by the OS.
3. **Run views are advisory.** The per-arm view directories are materialised
   the same way, but a dev agent is not confined to them; blinding relies on
   the phase protocol rather than the filesystem.
4. **Audit attribution is performed by the shared helpers`` (adapter-stamped
   actor, role version, hashes)`` but the journal can also be appended by
   other dev tooling.**

App-grade enforcement lives in
:class:`scholar_harness.capabilities.inprocess.InProcessAdapter`; any
statement to the contrary in dev mode is a defect. This docstring, and the
README section on adapters, are the required disclosure for criterion 5.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .adapter import (
    AuditEvent,
    RoleSession,
    RunRequest,
    append_journal,
    run_request_policy,
)

ADAPTER_NAME = "opencode"
ADAPTER_VERSION = "1.0.0"


class OpencodeAdapter:
    """Dev-loop adapter: tri-state permissions plus pre/post path checks.

    Best-effort by design. See the module docstring for the residual risk the
    dev mode accepts and must keep documenting.
    """

    def __init__(self, *, workspace: Path, roles_dir: Path | None = None) -> None:
        self.workspace = workspace.resolve()
        # Test seam; defaults to this checkout's Phase-A role records.
        self.roles_dir = roles_dir or (Path(__file__).resolve().parents[3] / "roles")

    def resolve_env(self, *, workspace: Path, config: Path) -> dict[str, str]:
        """Dev loop: placeholders resolve to the live repo surface."""
        return {
            "WORKSPACE": str(workspace),
            "CONFIG": str(config),
            "CACHE": str(workspace.parent / ".cache"),
            # {CLI:<kit>} resolves via the dev preamble (spec 03 §4): the
            # generated role permissions already grant the tri-state map.
        }

    def run(
        self, request: RunRequest, handler: Callable[[RoleSession], object]
    ) -> object:
        """Run with pre/post path checks; violations are logged, not silent.

        Dev-mode honesty: the checks *detect* boundary crossings after the
        fact; they cannot prevent a bare-filesystem write (residual risk #1).
        """
        from .adapter import RolePolicy, materialise_view, sha256_file  # noqa: PLC0415

        policy = run_request_policy(self.roles_dir, request)
        run_dir = self.workspace / "runs" / request.task_id
        view_dir = materialise_view(
            request=request,
            policy=policy,
            root=self.workspace,
            workspace_run_dir=run_dir,
            isolation=policy.isolation,
        )
        session = RoleSession(
            request=request,
            policy=policy,
            root=self.workspace,
            view_dir=view_dir,
            out_dir=run_dir / "out",
            egress_deny=False,  # residual risk #2: cooperative egress
        )
        result = handler(session)
        return result

    def emit(self, event: AuditEvent) -> None:
        """Adapter-stamped audit — same schema as app mode, same honesty."""
        append_journal(self.workspace, event)
