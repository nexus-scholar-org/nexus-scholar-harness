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
4. **Audit attribution is performed by the shared helpers
   (adapter-stamped actor, role version, hashes), but the journal can also be
   appended by other dev tooling.**

App-grade enforcement lives in
:class:`scholar_harness.capabilities.inprocess.InProcessAdapter`; any
statement to the contrary in dev mode is a defect. This docstring, and the
README section on adapters, are the required disclosure for criterion 5.
"""

from __future__ import annotations

import time
from dataclasses import replace
from pathlib import Path
from typing import Callable, Mapping

from ..contracts.envelope.model import Envelope
from .adapter import (
    AuditEvent,
    CLI_SCRIPTS,
    KIT_MODULES,
    RoleSession,
    RunRequest,
    append_journal,
    cache_binding,
    dev_kit_root,
    effective_arm,
    envelope_for_run,
    hash_inputs,
    journal_action_for,
    journal_status_for,
    payload_artifact_for,
    roll_back_promoted,
    run_request_policy,
    skill_dirs_under,
)

ADAPTER_NAME = "opencode"
ADAPTER_VERSION = "1.0.0"


class OpencodeAdapter:
    """Dev-loop adapter: tri-state permissions plus pre/post path checks.

    Best-effort by design. See the module docstring for the residual risk the
    dev mode accepts and must keep documenting.
    """

    def __init__(
        self,
        *,
        workspace: Path,
        roles_dir: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self.workspace = workspace.resolve()
        # The adapter root is this checkout (the dev loop always runs from one).
        self.root = Path(__file__).resolve().parents[3]
        # Test seam; defaults to this checkout's Phase-A role records.
        self.roles_dir = roles_dir or (self.root / "roles")
        self._env = dict(env or {})

    def resolve_env(self, *, workspace: Path, config: Path) -> dict[str, str]:
        """Bind the skill placeholder vocabulary (``ENV_BINDING_TABLE``).

        The dev-loop column of the shared table in
        :data:`scholar_harness.capabilities.adapter.ENV_BINDING_TABLE`:

        - ``CLI:<short>`` → ``uv run scholar-<short>`` (the repo's live
          console scripts, exactly what :func:`rewrite_text` reverses);
        - ``KIT_ROOT:<short>`` → ``<root>/tools/scholar-<short>-kit`` (the
          shared ``DEV_KIT_ROOT_TEMPLATE``, the vendored checkout the kit is
          installed from); absent when that checkout is not present;
        - ``SKILL_DIR:<skill>`` → ``<root>/.agents/skills/<skill>``; absent
          when the skill does not exist;
        - ``PY`` → ``uv run python``;
        - ``CACHE`` → ``NEXUS_RECON_ROOT`` when set, else ``<root>/.cache``;
        - ``WORKSPACE``/``CONFIG`` → the arguments.

        Pure: ``os.environ`` is only read, never written, and two consecutive
        calls return equal mappings. The constructor ``env`` mapping overrides
        any computed binding.
        """
        env: dict[str, str] = {
            f"CLI:{short}": f"uv run {script}" for short, script in CLI_SCRIPTS.items()
        }
        for short in KIT_MODULES:
            kit_root = dev_kit_root(self.root, short)
            if kit_root is not None:
                env[f"KIT_ROOT:{short}"] = str(kit_root)
        for skill, skill_dir in skill_dirs_under(
            self.root / ".agents" / "skills"
        ).items():
            env[f"SKILL_DIR:{skill}"] = str(skill_dir)
        env["WORKSPACE"] = str(workspace)
        env["CACHE"] = cache_binding(self.root / ".cache")
        env["CONFIG"] = str(config)
        env["PY"] = "uv run python"
        env.update(self._env)
        return env

    def run(
        self, request: RunRequest, handler: Callable[[RoleSession], object]
    ) -> Envelope:
        """Run with pre/post path checks; violations are logged, not silent.

        Dev-mode honesty: the checks *detect* boundary crossings after the
        fact; they cannot prevent a bare-filesystem write (residual risk #1).
        After a successful handler the adapter still writes one canonical
        journal row (``opencode@<version>``, the role's declared action for the
        envelope state, promoted outputs and hashes) through the shared append
        path. The envelope is built **before** that row (R6), so the journal
        status is the envelope's own status and the two can never disagree
        about a ``task_id``.

        The handler's return value is discarded, exactly as in app mode:
        ``Envelope@1`` carries at most one JSON-object payload, built from the
        promoted artifacts; ``parameters["payload_artifact"]`` names the file
        that backs ``output`` (``OK``/``PARTIAL`` only), ``coverage`` counts
        every promoted artifact, and the journal remains authoritative for the
        rest. A failing payload is ``INVALID_OUTPUT`` and is retained under
        ``output`` for forensics when the role declares its schema and the
        contract registers it (F2); otherwise the artifact path travels in
        ``refusal.validation_findings``.

        Failure handling after the handler (F3), same rule as app mode: if
        envelope construction fails, this run's promoted artifacts and
        ``runs/{task_id}`` are removed and the original exception re-raised, so
        no published dev-loop artifact can exist without a journal row. A
        journal-append ``OSError`` is **not** rolled back: it surfaces with the
        output already published (P9). Accepted fail-closed limit (P3-7): where
        this run overwrote a pre-existing artifact, rollback removes that path,
        so an earlier journal row naming it dangles — leaving the failed run's
        bytes would publish output the contract refused, which is worse.
        """
        from .adapter import materialise_view, view_exclusions

        started = time.monotonic()
        policy = run_request_policy(self.roles_dir, request)
        # Hash before materialising any run directory: an outside-root input
        # is a typed refusal with no ``runs/`` debris.
        inputs = self._hash_inputs(request.inputs)
        run_dir = self.workspace / "runs" / request.task_id
        excluded, other_arm, arm_glob = view_exclusions(self.roles_dir, policy, request)
        view_dir = materialise_view(
            request=request,
            policy=policy,
            root=self.workspace,
            workspace_run_dir=run_dir,
            isolation=policy.isolation,
            excluded_globs=excluded,
            other_arm_globs=other_arm,
            arm_globs=arm_glob,
        )
        session = RoleSession(
            request=request,
            policy=policy,
            root=self.workspace,
            view_dir=view_dir,
            out_dir=run_dir / "out",
            egress_deny=False,  # residual risk #2: cooperative egress
        )
        handler(session)
        elapsed_ms = round((time.monotonic() - started) * 1000)
        # Build the envelope first: the journal records its status, never a
        # blanket success (R6). F3: a construction failure rolls back exactly
        # what this run promoted (plus its run dir) and re-raises; the journal
        # append below stays outside that block (P9).
        try:
            envelope = envelope_for_run(
                root=self.workspace,
                request=request,
                policy=policy,
                inputs=inputs,
                adapter=ADAPTER_NAME,
                adapter_version=ADAPTER_VERSION,
                duration_ms=elapsed_ms,
                staged=session.staged,
                roles_dir=self.roles_dir,
            )
        except Exception:
            roll_back_promoted(session, run_dir)
            raise
        # F4: name the artifact backing ``output`` (one payload per envelope).
        payload_artifact = payload_artifact_for(
            envelope, session.promoted, self.workspace
        )
        parameters: dict[str, object] = {
            "arm": effective_arm(request) or "solo",
            "isolation": policy.isolation,
        }
        if payload_artifact is not None:
            parameters["payload_artifact"] = payload_artifact
        self.emit(
            AuditEvent(
                action=journal_action_for(policy, envelope),
                actor=policy.actor,
                role_version=policy.version,
                description=(
                    f"{request.role_id}@{policy.version} run {request.task_id}"
                    f" (arm {effective_arm(request) or 'solo'}; isolation "
                    f"{policy.isolation}; envelope {envelope.status.value}; "
                    f"{elapsed_ms} ms)"
                ),
                task_id=request.task_id,
                inputs=tuple(inputs),
                outputs=tuple(
                    (p.relative_to(self.workspace).as_posix(), sha)
                    for p, sha in zip(session.staged, session.staged_sha256)
                ),
                parameters=parameters,
                status=journal_status_for(envelope),
                duration_ms=elapsed_ms,
            )
        )
        return envelope

    def _hash_inputs(self, inputs: tuple[str, ...]) -> list[tuple[str, str]]:
        return hash_inputs(self.workspace, inputs)

    def emit(self, event: AuditEvent) -> None:
        """Adapter-stamped audit — same schema as app mode, same honesty.

        The row is labelled ``opencode@<version>`` by this adapter; a caller
        cannot mislabel a dev-loop event as in-process.
        """
        append_journal(
            self.workspace,
            replace(event, adapter=ADAPTER_NAME, adapter_version=ADAPTER_VERSION),
        )
