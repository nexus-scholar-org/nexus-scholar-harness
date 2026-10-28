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
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Mapping

from ..contracts.envelope.model import Envelope
from .adapter import (
    AuditEvent,
    CLI_SCRIPTS,
    KIT_MODULES,
    RolePolicy,
    RoleSession,
    RunRequest,
    ScopeViolation,
    append_journal,
    cache_binding,
    effective_arm,
    envelope_for_run,
    hash_inputs,
    installed_kit_root,
    installed_skill_dirs,
    journal_action_for,
    journal_status_for,
    materialise_view,
    payload_artifact_for,
    roll_back_promoted,
    run_request_policy,
    view_exclusions,
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
        # Explicit redaction additions; unioned with the role record and the
        # DEFAULT_REDACTED_FIELDS set on RoleSession — never a replacement.
        self._redacted_fields = redacted_fields
        self._env = dict(env or {})

    # -- CapabilityAdapter protocol ----------------------------------------

    def resolve_env(self, *, workspace: Path, config: Path) -> dict[str, str]:
        """Bind the skill placeholder vocabulary (``ENV_BINDING_TABLE``).

        The application column of the shared table in
        :data:`scholar_harness.capabilities.adapter.ENV_BINDING_TABLE`:

        - ``CLI:<short>`` → the ``scholar-<short>`` console-script name (the
          installed entry point; no ``uv`` in an application);
        - ``KIT_ROOT:<short>`` → the kit's **installed package directory**,
          resolved through the import system (a hardcoded ``tools/`` path is
          wrong the moment the app ships a wheel). Absent when the kit is not
          importable — the binding is never invented;
        - ``SKILL_DIR:<skill>`` → the workspace-local skill directory when it
          exists, else the project's resolved skills root (wheel bundle or
          repo ``.agents/skills``); absent when the skill ships nowhere;
        - ``PY`` → ``sys.executable``, the interpreter already running (never
          ``uv run``);
        - ``CACHE`` → ``NEXUS_RECON_ROOT`` when set, else
          ``<workspace parent>/.cache`` (never forced under the workspace);
        - ``WORKSPACE``/``CONFIG`` → the arguments.

        Pure: ``os.environ`` is only read, never written, and two consecutive
        calls return equal mappings. The constructor ``env`` mapping overrides
        any computed binding. A missing optional key is absent, not fatal:
        ``render`` raises the named ``ValueError`` for it.
        """
        env: dict[str, str] = {
            f"CLI:{short}": script for short, script in CLI_SCRIPTS.items()
        }
        for short in KIT_MODULES:
            kit_root = installed_kit_root(short)
            if kit_root is not None:
                env[f"KIT_ROOT:{short}"] = str(kit_root)
        for skill, skill_dir in installed_skill_dirs(workspace).items():
            env[f"SKILL_DIR:{skill}"] = str(skill_dir)
        env["WORKSPACE"] = str(workspace)
        env["CACHE"] = cache_binding(Path(workspace).parent / ".cache")
        env["CONFIG"] = str(config)
        env["PY"] = sys.executable
        env.update(self._env)
        return env

    def emit(self, event: AuditEvent) -> None:
        """Adapter-written audit; roles never touch the journal themselves.

        The writer label is stamped by *this* adapter, not supplied by the
        caller: an in-process event is always ``in-process@<version>``.
        """
        append_journal(
            self.workspace,
            replace(event, adapter=ADAPTER_NAME, adapter_version=ADAPTER_VERSION),
        )

    # -- execution ----------------------------------------------------------

    def run(
        self, request: RunRequest, handler: Callable[[RoleSession], Any]
    ) -> Envelope:
        """Execute one role under the enforced capability boundary.

        Order of guarantees: policy validation (including the input-schema
        preflight, F1) → input hashing (before any directory exists) →
        role-record consistency → run-view materialisation → guarded handler
        execution → staging promotion per write. Every boundary breach is a
        ``SCOPE_VIOLATION`` with **no file left behind**; the run path raises it
        by design and never returns a success envelope for a refused run.

        The handler's return value is **discarded**: ``Envelope@1`` has no field
        that can carry an arbitrary object (and a ``Path`` from
        ``session.write`` is not a payload). The envelope is built from what was
        actually promoted: at most one JSON-object payload, with ``coverage``
        (``unit="artifact"``) and the journal recording the full artifact
        count. Zero artifacts, a non-object artifact, or a schema-invalid
        payload is ``INVALID_OUTPUT``; a single failing payload is retained
        under ``output`` for forensics when the role declares its schema and the
        contract registers it (F2), otherwise the artifact path travels in
        ``refusal.validation_findings``.

        Failure handling after the handler (F3):

        - **Envelope construction fails.** ``envelope_for_run`` and everything
          up to (not including) the journal append runs inside one
          ``try/except Exception``. On failure this run's promoted artifacts
          (``session.promoted``, never a pre-existing file) and
          ``runs/{task_id}`` are deleted, then the *original* exception is
          re-raised: no published file can exist without a journal row
          describing it. Accepted fail-closed limit (P3-7): where this run
          overwrote a pre-existing artifact, rollback removes that path, so an
          earlier journal row naming it dangles — leaving the failed run's
          bytes would publish output the contract refused, which is worse.
        - **The journal append fails** (``OSError``). It is outside that block
          and deliberately **not** rolled back: the envelope is already valid
          and the output is published, so the append is authoritative (never
          partially written). Callers must not treat a raised append as an
          unpublish.

        Journal behaviour after a successful handler: the envelope is built
        **before** the row (R6), so the journal ``status`` is the envelope's own
        status (``OK`` → ``SUCCESS``, else the refusal state) and the row can
        never claim a success the returned envelope denies. ``Envelope@1``
        carries at most one payload, so ``parameters["payload_artifact"]``
        names the promoted file that backs ``output`` (``OK``/``PARTIAL``
        only); ``coverage`` counts every promoted artifact and the journal row
        is authoritative for the rest.
        """
        started = time.monotonic()
        policy = run_request_policy(self.roles_dir, request)
        # Hash before creating ``runs/{task_id}``: an outside-root input is a
        # refusal, not a half-created run directory.
        inputs = self._hash_inputs(request.inputs)
        isolation = policy.isolation
        run_dir = self.workspace / "runs" / request.task_id
        out_dir = run_dir / "out"
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            # Every boundary check happens before the handler: a refused
            # sibling/blinding check must not leave an empty staging dir
            # behind (the except block below removes ``out/``).
            excluded, other_arm, arm_glob = view_exclusions(
                self.roles_dir, policy, request
            )
            view_dir = materialise_view(
                request=request,
                policy=policy,
                root=self.root,
                workspace_run_dir=run_dir,
                isolation=isolation,
                redacted_fields=self._redacted_fields,
                excluded_globs=excluded,
                other_arm_globs=other_arm,
                arm_globs=arm_glob,
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
                handler(session)
        except ScopeViolation:
            # No file left behind: remove staged remnants of the failed run.
            shutil.rmtree(out_dir, ignore_errors=True)
            raise
        elapsed_ms = round((time.monotonic() - started) * 1000)
        # Build the envelope first: its status is the journal's status (R6).
        # F3: a construction failure (contract/schema) must not leave this
        # run's promoted artifacts published with no journal row. The rollback
        # deletes only what *this* run promoted plus its staging/view dir, and
        # re-raises the original exception.
        try:
            envelope = envelope_for_run(
                root=self.root,
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
        # F4: the journal names the artifact backing ``output`` (the envelope
        # carries one payload); omitted when the envelope carries none. The
        # journal append stays outside the rollback block (P9): an append
        # OSError surfaces with the output published.
        payload_artifact = payload_artifact_for(envelope, session.promoted, self.root)
        parameters: dict[str, Any] = {
            "arm": effective_arm(request) or "solo",
            "isolation": isolation,
        }
        if payload_artifact is not None:
            parameters["payload_artifact"] = payload_artifact
        self.emit(
            AuditEvent(
                # The role's own declared verb: its first action for OK, its
                # last declared action otherwise — never an intermediate
                # action and never an invented ``{ROLE}_RUN`` action.
                action=journal_action_for(policy, envelope),
                actor=policy.actor,
                role_version=policy.version,
                description=(
                    f"{request.role_id}@{policy.version} run {request.task_id}"
                    f" (arm {effective_arm(request) or 'solo'}; isolation {isolation};"
                    f" envelope {envelope.status.value}; {elapsed_ms} ms)"
                ),
                inputs=tuple(inputs),
                outputs=tuple(
                    (p.relative_to(self.root).as_posix(), sha)
                    for p, sha in zip(session.staged, session.staged_sha256)
                ),
                parameters=parameters,
                status=journal_status_for(envelope),
                task_id=request.task_id,
                duration_ms=elapsed_ms,
            )
        )
        return envelope

    # -- internals -----------------------------------------------------------

    def _hash_inputs(self, inputs: tuple[str, ...]) -> list[tuple[str, str]]:
        return hash_inputs(self.root, inputs)
