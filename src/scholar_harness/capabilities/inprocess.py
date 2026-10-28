"""``InProcessAdapter`` — the application surface: **enforced** capability.

Spec 04 §2: materialised run view, path validation at every I/O, egress
control, adapter-written audit. "In-process" is **not** an exemption from
isolation (spec 04 §6): the run view is materialised before the handler runs,
and the handler receives only the role session's view.

DO NOT reuse this class to claim dev-grade enforcement sideways: the dev loop
runs under :class:`scholar_harness.capabilities.opencode.OpencodeAdapter`
(best-effort, documented residual risk).
"""

from __future__ import annotations

import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .adapter import (
    AuditEvent,
    RolePolicy,
    RoleSession,
    RunRequest,
    ScopeViolation,
    append_journal,
    materialise_view,
    run_request_policy,
    sha256_file,
)

ADAPTER_NAME = "in-process"
#: Bumped when enforcement semantics change; journals record it.
ADAPTER_VERSION = "1.0.0"


class InProcessAdapter:
    """Runs roles inside the hosting process under enforced capability."""

    def __init__(
        self,
        *,
        root: Path,
        workspace: Path,
        roles_dir: Path,
        redacted_fields: frozenset[str] | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self.root = root.resolve()
        self.workspace = workspace.resolve()
        self.roles_dir = roles_dir
        # Explicit redaction override; empty → role-record fields, else the
        # DEFAULT_REDACTED_FIELDS set on RoleSession.
        self._redacted_fields = redacted_fields
        self._env = dict(env or {})

    # -- CapabilityAdapter protocol ----------------------------------------

    def resolve_env(self, *, workspace: Path, config: Path) -> dict[str, str]:
        """Bind the skill placeholders (spec 03 §4 right-hand column)."""
        env = dict(self._env)
        env.setdefault("WORKSPACE", str(workspace))
        env.setdefault("CONFIG", str(config))
        env.setdefault("CACHE", str(workspace.parent / ".cache"))
        return env

    def emit(self, event: AuditEvent) -> None:
        """Adapter-written audit; roles never touch the journal themselves."""
        append_journal(self.workspace, event)

    # -- execution ----------------------------------------------------------

    def run(self, request: RunRequest, handler: Callable[[RoleSession], Any]) -> Any:
        """Execute one role under the enforced capability boundary.

        Order of guarantees: policy validation → role record consistency →
        run-view materialisation → guarded handler execution → staging
        promotion is per-write inside the session. The envelope is ``OK``
        only when the handler completed and staging has no leftovers; every
        boundary breach is a ``SCOPE_VIOLATION`` with **no file left behind**.
        """
        started = time.monotonic()
        policy = run_request_policy(self.roles_dir, request)
        isolation = policy.isolation
        run_dir = self.workspace / "runs" / request.task_id
        out_dir = run_dir / "out"
        out_dir.mkdir(parents=True, exist_ok=True)
        inputs = self._hash_inputs(request.inputs)
        excluded: tuple[str, ...] = ()
        if request.arm is not None or isolation != "none":
            from .adapter import sibling_write_globs  # noqa: PLC0415

            excluded = sibling_write_globs(self.roles_dir, policy, request.params)
        try:
            view_dir = materialise_view(
                request=request,
                policy=policy,
                root=self.root,
                workspace_run_dir=run_dir,
                isolation=isolation,
                redacted_fields=self._redacted_fields,
                excluded_globs=excluded,
            )
            session = RoleSession(
                request=request,
                policy=policy,
                root=self.root,
                view_dir=view_dir,
                out_dir=out_dir,
                egress_deny=policy.network == "deny",
            )
        except ScopeViolation:
            shutil.rmtree(out_dir, ignore_errors=True)
            raise
        try:
            with session.egress_guard():
                result = handler(session)
        except ScopeViolation:
            # No file left behind: remove staged remnants of the failed run.
            shutil.rmtree(out_dir, ignore_errors=True)
            raise
        elapsed_ms = round((time.monotonic() - started) * 1000)
        self.emit(
            AuditEvent(
                action=f"{request.role_id.upper().replace('-', '_')}_RUN",
                actor=policy.actor,
                role_version=request.role_version,
                description=(
                    f"{request.role_id}@{request.role_version} run {request.task_id}"
                    f" (arm {request.arm or 'solo'}; isolation {isolation};"
                    f" {elapsed_ms} ms)"
                ),
                envelope_id=request.task_id,
                inputs=tuple(inputs),
                outputs=tuple(
                    (p.relative_to(self.root).as_posix(), sha)
                    for p, sha in zip(session.staged, session.staged_sha256)
                ),
                parameters={"arm": request.arm or "solo", "isolation": isolation},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )
        return result

    # -- internals -----------------------------------------------------------

    def _hash_inputs(self, inputs: tuple[str, ...]) -> list[tuple[str, str]]:
        hashed = []
        for raw in inputs:
            path = (self.root / raw).resolve()
            if not path.is_file():
                raise ScopeViolation(f"input {raw!s} missing from the run root")
            hashed.append((path.relative_to(self.root).as_posix(), sha256_file(path)))
        return hashed
