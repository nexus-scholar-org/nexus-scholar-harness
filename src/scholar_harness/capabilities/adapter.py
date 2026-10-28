"""Adapter core: the capability protocol and the enforced role session.

This module holds the shared, *enforced* machinery:

- :class:`RunRequest` / :class:`AuditEvent` / :class:`CapabilityAdapter` (spec 04 §1);
- :class:`RoleSession` — the only filesystem the role can touch. Its every
  operation is validated against the role record (``roles/<id>.json``) *and*
  the materialised run view; failures are typed refusals, never stack traces;
- :class:`InProcessAdapter` (``inprocess.py``) and :class:`OpencodeAdapter`
  (``opencode.py``) drive it for their respective surfaces.

Both adapters return a validated ``Envelope@1`` (spec 04 §1). ``Envelope@1``
carries **at most one output payload**: a run that promotes several artifacts is
represented by ``coverage`` plus the adapter-written journal, which remains the
authoritative per-artifact record. A promoted artifact that is not a JSON
object, a role that declares no/ambiguous output schema, or a payload that fails
its Contract v1 schema is reported as ``INVALID_OUTPUT`` — never coerced into
``OK`` and never given an invented schema name. Such a run **retains** the
failing payload for forensics (spec 02 §3; the frozen fixture
``tests/conformance/fixtures/envelope/invalid_output.json`` ships exactly that
shape) whenever the contract can name it: the artifact parsed as an object, the
role declares the schema, and the schema is registered in its payload registry.
Otherwise ``output`` is ``None`` and ``refusal.validation_findings`` names the
artifact path and the validator message.

The contract is the only authority: every returned envelope is validated with
``roles_dir`` (the same role-compatibility step the shipped
``python -m scholar_harness.contracts.envelope validate`` CLI applies). Request
inputs carry the schemas the **caller** declares (``RunRequest.input_schemas``,
positional to ``inputs``): the pre-handler check in :func:`run_request_policy`
refuses a count/name gap before any directory exists, so the adapter never
guesses a schema from position or file content and never attests one it cannot
know. Refusal states ship no inputs, and the audit row is written *after* the
envelope with the envelope's own status so the two can never disagree about a
``task_id``.

Two refusal classes, one hierarchy:

- :class:`ScopeViolation` — a **boundary** breach: the role left its declared
  capability (write/read/egress/arm) or the request crossed a boundary (unsafe
  label, undeclared or missing input schema, outside-root input).
- :class:`ContractViolation` — the **frozen contract** cannot represent the
  role record, request identity, or payload, so no ``Envelope@1`` exists even
  though nothing crossed a boundary (e.g. a role version the contract cannot
  parse). It subclasses :class:`ScopeViolation`, so ``except ScopeViolation``
  callers keep working.

Status coverage (F8/F9/F10):

- ``run()`` returns only ``OK``, ``PARTIAL`` or ``INVALID_OUTPUT``. ``REFUSED``
  is available through :meth:`ScopeViolation.envelope`, but the run path
  *raises* by design: a refused run must never be mistakable for a returned
  verdict. ``BLOCKED_INPUT``/``BLOCKED_*``, ``PROVIDER_TRANSIENT`` and
  ``GATE_FAILED`` are produced by the orchestrator/application layers, not by
  ``run()`` — so "run() returns an Envelope" is scoped to runs that pass the
  input preflight.
- ``coverage`` counts **artifacts** (``unit="artifact"``), never records: it
  never claims per-record PRISMA coverage.
- Among the eleven shipped roles only ``screener`` declares an output schema
  with a registered Contract v1 payload model (``ScreeningDecisions@1``), so it
  is the only role that can reach ``OK`` today. The other ten have no registered
  model for their declared output schemas and fail closed as ``INVALID_OUTPUT``
  (D11) once the payload is promoted and the contract refuses the unregistered
  name — their ``{task_id}``/``{stu}`` rows bind, so the refusal names the
  missing model rather than an unbound write row.

Guarantee table (spec 04 §2):

| Guarantee        | Mechanism here                                        |
|------------------|--------------------------------------------------------|
| Write boundary   | stage → ``write_glob`` validation → promote; else refusal |
| Read boundary    | run view contains only ``read_glob`` matches            |
| Blinding         | per-arm view dirs; ``redacted-input`` strips fields     |
| Network          | patched module-level socket/resolver entry points refuse |
| Audit attribution| adapter writes the canonical journal; roles never do    |
"""

from __future__ import annotations

import contextvars
import fnmatch
import hashlib
import importlib.util
import json
import os
import re
import shutil
import socket
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

from pydantic import ValidationError

from ..contracts.envelope.api import (
    EnvelopeRefusalError,
    envelope_id,
    validate,
)
from ..contracts.envelope.api import output_sha256 as contract_output_sha256
from ..contracts.envelope.model import (
    Envelope,
    EnvelopeCoverage,
    EnvelopeInputRef,
    EnvelopeOutput,
    EnvelopeProvenance,
    EnvelopeRefusal,
    EnvelopeStatus,
)
from ..contracts.envelope.registry import RefusalCode
from ..skills_portability.variables import (
    CLI_SHORTS,
    DEV_KIT_ROOT_TEMPLATE,
    KIT_SHORTS,
)
from ..workspace.audit import append_event
from ..workspace.loader import resolve_skills_root

NO_REDACT = "the run view never exposes files outside ``read_glob``"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


# ---------------------------------------------------------------------------
# Refusals — typed, renderable, never raw tracebacks (spec 04 §5.3)
# ---------------------------------------------------------------------------


class ScopeViolation(Exception):
    """A role-left operation crossed its capability boundary.

    Raised on writes outside ``write_glob``, writes into ``deny_glob``
    (``audit/**`` included), reads/listings outside the materialised run view,
    and inputs outside the run root. App mode turns this into an ``Envelope@1``
    ``REFUSED`` with ``SCOPE_VIOLATION`` via :meth:`envelope`; the run path
    itself deliberately keeps raising so a refused run can never be mistaken
    for a successful one.
    """

    #: Registry code carried by every refusal materialised from this exception.
    code = "SCOPE_VIOLATION"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.code = "SCOPE_VIOLATION"
        self.detail = detail

    def envelope(
        self,
        request: RunRequest,
        policy: RolePolicy,
        *,
        adapter: str,
        adapter_version: str,
        roles_dir: Path,
        duration_ms: int | None = None,
    ) -> Envelope:
        """Materialise this refusal as a validated ``REFUSED`` envelope.

        ``Envelope@1`` refusal states carry **no inputs** (api.py
        ``_check_role_compatibility``: a role's declared input schemas are the
        only names it may consume, and a refusal fired before or during reads
        cannot honestly claim a bound schema). It ships no payload and no
        ``output_sha256`` (spec 02 §3).

        ``roles_dir`` is **required and keyword-only**: it runs the same
        role-compatibility step as the shipped CLI, so a refusal envelope can
        never be returned unvalidated (a renderable state the CLI rejects is not
        a transport row).

        Robustness (R7): a blank detail is replaced with the exception's
        default text. An unregistered ``code`` is a defect, not something to
        coerce: ``Envelope@1.refusal.code`` is a closed registry, so this method
        raises a :class:`ScopeViolation` naming the code instead of silently
        relabelling the refusal as ``SCOPE_VIOLATION``. A request or role the
        frozen contract cannot represent at all (e.g. a role version with no
        parseable major) raises :class:`ContractViolation` naming the defect —
        this method raises by design. The run path still raises this exception
        by design; callers that need a renderable state call this method
        explicitly.
        """
        detail = (self.detail or "").strip() or "scope violation"
        registered = {member.value for member in RefusalCode}
        if self.code not in registered:
            raise ScopeViolation(
                f"refusal code {self.code!r} is not a registered RefusalCode; "
                "Envelope@1.refusal.code is closed (the adapter never coerces "
                "an unknown code to SCOPE_VIOLATION)"
            )
        try:
            return _build_envelope(
                request=request,
                policy=policy,
                status=EnvelopeStatus.REFUSED,
                inputs=(),
                adapter=adapter,
                adapter_version=adapter_version,
                duration_ms=duration_ms,
                refusal=EnvelopeRefusal(code=self.code, detail=detail),
                roles_dir=roles_dir,
            )
        except (ValidationError, EnvelopeRefusalError) as exc:
            raise ContractViolation(
                "cannot materialise a REFUSED envelope for this request "
                f"({request.role_id!r} task {request.task_id!r}): {exc}"
            ) from exc


class ContractViolation(ScopeViolation):
    """The frozen contract cannot represent this role, request, or payload.

    Distinct from a :class:`ScopeViolation`, which records a **boundary**
    breach (the role crossed a declared capability, or the request crossed a
    path/label/schema boundary). A contract violation means nothing crossed a
    boundary, yet no valid ``Envelope@1`` exists: e.g. a role record whose
    ``version`` has no parseable major, or a refusal code the registry scopes to
    other roles. Both are refusals the caller cannot proceed past, so this
    subclasses :class:`ScopeViolation` and existing ``except ScopeViolation``
    handlers keep working unchanged.

    Raised wherever an ``EnvelopeRefusalError`` escapes envelope construction
    (:func:`envelope_for_run` and :meth:`ScopeViolation.envelope`).
    """


def payload_digest(data: Mapping[str, Any]) -> str:
    """The one payload digest recipe: the contract's ``output_sha256``.

    Every payload digest the adapter emits **or verifies** goes through this
    helper (P3-6), so the hash an envelope carries and the hash a later scan
    compares are produced by the same contract code. The contract hashes
    ``output.data`` only (``api.py`` :func:`output_sha256`), which is why
    timing, provenance, and the schema name never enter the digest.

    Input refs deliberately do **not** use this helper: the contract defines an
    input's ``sha256`` as the hash of the materialised *file*
    (:func:`sha256_file`), not of a parsed payload.
    """
    digest = contract_output_sha256({"output": {"data": data}})
    if digest is None:  # pragma: no cover - ``data`` is always a JSON object
        # output_sha256 returns None only when ``output.data`` is absent; the
        # adapter never stages an unhashed payload, so this is a broken
        # invariant rather than a representable state.
        raise ContractViolation(
            "payload_digest requires a JSON object payload: the contract's "
            "output_sha256 returned None, and the adapter never emits an "
            "unhashed payload"
        )
    return digest


class EgressRefused(Exception):
    """Network egress refused by the role's egress policy.

    Raised *immediately* at the connect attempt — never a timeout-and-retry
    (Phase-E acceptance criterion 3).
    """

    def __init__(self, role: str, detail: str) -> None:
        super().__init__(f"{role}: {detail}")
        self.role = role
        self.detail = detail


# ---------------------------------------------------------------------------
# Data carriers (spec 04 §1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RunRequest:
    """One role execution request. ``arm`` triggers isolation when set.

    ``input_schemas`` is the **caller's** declaration of each input's schema,
    positional and in the same order as ``inputs``: ``input_schemas[i]`` names
    the schema of ``inputs[i]``. The adapter verifies every name against the
    role record's declared inputs before the handler runs
    (:func:`run_request_policy`) and writes the supplied names into
    ``Envelope@1.inputs[*].schema`` verbatim — it never infers a schema from
    position or file content, and never attests one the caller did not state.
    When the role declares no input schema at all, an empty tuple is allowed and
    the envelope uses the honest ``"untyped"`` placeholder, because the adapter
    has no schema-name authority to check against.
    """

    task_id: str
    role_id: str
    role_version: str
    inputs: tuple[str, ...]
    params: Mapping[str, str]  # {ws}, {batch}, {stu}, ...
    arm: str | None = None
    input_schemas: tuple[str, ...] = ()


@dataclass(frozen=True)
class AuditEvent:
    """Adapter-stamped provenance; the role never writes the journal itself.

    ``event_id``/``timestamp`` are minted by the canonical writer
    (:func:`scholar_harness.workspace.audit.append_event`), never here.
    ``adapter``/``adapter_version`` identify the surface that writes the row;
    each adapter stamps its own values in :meth:`emit` so a caller cannot
    mislabel an in-process event as ``opencode`` (or vice versa).
    """

    action: str
    actor: str
    role_version: str
    description: str
    #: Run id stamped into the journal ``parameters`` block; required and
    #: validated non-blank by :func:`append_journal`.
    task_id: str
    inputs: tuple[tuple[str, str], ...] = ()  # (path, sha256)
    outputs: tuple[tuple[str, str], ...] = ()
    parameters: Mapping[str, Any] = field(default_factory=dict)
    status: str = "SUCCESS"
    adapter: str = ""
    adapter_version: str = ""
    #: Adapter-observed wall time; ``None`` when the surface cannot measure it.
    duration_ms: int | None = None


# ---------------------------------------------------------------------------
# Skill environment bindings (spec 04 §1 + spec 03 §4): one key table
# ---------------------------------------------------------------------------

#: The single documented key table both adapters implement. ``resolve_env``
#: returns a flat ``dict[str, str]`` in this spelling and
#: :meth:`scholar_harness.skills_portability.Preamble.from_env` reads it back,
#: so the vocabulary's key names are the only convention.
ENV_BINDING_TABLE = """\
| Key                | InProcessAdapter (application)                     | OpencodeAdapter (dev loop)              |
|--------------------|----------------------------------------------------|-----------------------------------------|
| ``CLI:<short>``    | ``scholar-<short>`` console script                 | ``uv run scholar-<short>``              |
| ``KIT_ROOT:<short>``| the installed **package** directory (``…/src/scholar_<x>``), not a checkout root | ``<root>/tools/scholar-<short>-kit`` |
| ``SKILL_DIR:<skill>``| ``<workspace>/.agents/skills/<skill>`` if present,| ``<root>/.agents/skills/<skill>``       |
|                    | else the resolved skills root (wheel/repo)         |                                         |
| ``WORKSPACE``      | the ``workspace`` argument                         | the ``workspace`` argument              |
| ``CACHE``          | ``NEXUS_RECON_ROOT`` else ``<workspace parent>/.cache`` | ``NEXUS_RECON_ROOT`` else ``<root>/.cache`` |
| ``CONFIG``         | the ``config`` argument                            | the ``config`` argument                 |
| ``PY``             | ``sys.executable`` (the running interpreter)        | ``uv run python``                       |

The app ``KIT_ROOT:<short>`` is the installed *package* directory. Shipped
bodies that append ``/src/<module>/…`` or ``/pyproject.toml`` resolve only
against a vendored checkout, so those idioms do not resolve in an installed
wheel: reconciling the two meanings is an open contract decision, and the app
column is not fully resolved.

A binding that cannot be computed (a kit that is not importable, a skill
directory that does not exist) is **absent**, never invented: ``render`` then
raises its named ``ValueError``. A constructor ``env`` mapping overrides the
computed values, so a host application can pin any single key.
"""

#: ``<short>`` → console-script name. Derived from the skill vocabulary
#: (``skills_portability.variables.CLI_SHORTS``, itself derived from
#: ``KIT_COMMANDS``) so a kit a skill may name is always a CLI an adapter can
#: bind. Every surface follows ``scholar-<short>`` (``harness`` included:
#: ``{CLI:harness}`` is what ``rewrite_text`` emits for
#: ``uv run scholar-harness``).
CLI_SCRIPTS: dict[str, str] = {short: f"scholar-{short}" for short in CLI_SHORTS}

#: ``<short>`` → importable module name of the kit's package
#: (``rag`` → ``scholar_rag``). The harness is not a kit, so it is absent —
#: there is no ``{KIT_ROOT:harness}`` and no adapter pretends to bind one.
KIT_MODULES: dict[str, str] = {short: f"scholar_{short}" for short in KIT_SHORTS}


def cache_binding(default: Path) -> str:
    """``{CACHE}``: ``NEXUS_RECON_ROOT`` when set, else the surface default.

    The cache is deliberately allowed to live outside the workspace: the recon
    cache is shared across projects, so forcing it under ``<workspace>`` would
    silently move a user's state.
    """
    override = os.environ.get("NEXUS_RECON_ROOT")
    return override if override else str(default)


def installed_kit_root(short: str) -> Path | None:
    """The installed package directory for a kit, or ``None``.

    Resolved through the import system (never a hardcoded ``tools/`` path) so
    the application binds what it actually ships. A namespace package (the
    agent kit ships no ``__init__.py``) has no ``origin``; its
    ``submodule_search_locations`` is the package directory.

    **This is the package directory, not a checkout root.** Shipped skill
    bodies that compose ``{KIT_ROOT:<short>}/src/<module>/…`` or
    ``{KIT_ROOT:rag}/pyproject.toml`` resolve only against a vendored checkout;
    in an installed wheel ``<pkg>/src/<module>`` does not exist and the package
    directory has no ``pyproject.toml``. Reconciling the app binding with those
    idioms is an open contract decision (the dev column and the app column do
    not yet mean the same thing) — the app column is *not* fully resolved, and
    no adapter may pretend otherwise.
    """
    module = KIT_MODULES.get(short)
    if module is None:
        return None
    try:
        spec = importlib.util.find_spec(module)
    except (ImportError, ValueError):
        return None
    if spec is None:
        return None
    locations = list(spec.submodule_search_locations or ())
    if locations:
        candidate = Path(locations[0])
    elif spec.origin and spec.origin not in ("built-in", "frozen"):
        candidate = Path(spec.origin).parent
    else:
        return None
    resolved = candidate.resolve()
    return resolved if resolved.is_dir() else None


def dev_kit_root(root: Path, short: str) -> Path | None:
    """``{KIT_ROOT:<short>}`` in the dev loop: the vendored kit checkout.

    The path comes from
    :data:`~scholar_harness.skills_portability.variables.DEV_KIT_ROOT_TEMPLATE`,
    the same constant :meth:`Preamble.dev` uses, so the preamble and this
    adapter cannot drift.
    """
    if short not in KIT_MODULES:
        return None
    candidate = root / DEV_KIT_ROOT_TEMPLATE.replace("{{kit}}", short)
    return candidate if candidate.is_dir() else None


def skill_dirs_under(root: Path | None) -> dict[str, Path]:
    """``<root>/<skill>/SKILL.md`` directories, keyed by skill id."""
    if root is None or not root.is_dir():
        return {}
    return {
        entry.name: entry
        for entry in sorted(root.iterdir())
        if entry.is_dir() and (entry / "SKILL.md").is_file()
    }


def installed_skill_dirs(workspace: Path) -> dict[str, Path]:
    """``{SKILL_DIR:<skill>}`` for the app surface.

    Workspace-local skills win (an ``init``-scaffolded workspace installs them
    at ``<workspace>/.agents/skills``), then the project's one resolution order
    for everything else (``NEXUS_SKILLS_SRC`` → wheel bundle → repo
    ``.agents/skills``), so the adapter never hardcodes a checkout path.

    The fallback root decides what can appear: when it is a **checkout**, the
    app column can expose a repo-local ``SKILL_DIR:pull-request-gate`` (a
    dev-only skill the wheel excludes); in an **installed wheel** that id is
    never bound, because the wheel does not ship it.
    """
    resolved = skill_dirs_under(Path(workspace) / ".agents" / "skills")
    for name, path in skill_dirs_under(resolve_skills_root()).items():
        resolved.setdefault(name, path)
    return resolved


class CapabilityAdapter(Protocol):
    """One interface, two implementations (spec 04 §1). Deliberately small."""

    def resolve_env(self, *, workspace: Path, config: Path) -> dict[str, str]:
        """Bind the skill placeholder vocabulary for this surface.

        The key table is :data:`ENV_BINDING_TABLE` (one table, both adapters):
        ``CLI:<short>``, ``KIT_ROOT:<short>``, ``SKILL_DIR:<skill>``,
        ``WORKSPACE``, ``CACHE``, ``CONFIG`` and ``PY``. The mapping is
        consumed by
        :meth:`scholar_harness.skills_portability.Preamble.from_env`, so a
        skill body renders without a second naming convention.
        """

    def run(
        self, request: RunRequest, handler: Callable[[RoleSession], Any]
    ) -> Envelope:
        """Execute one role against one request and return a validated Envelope@1."""

    def emit(self, event: AuditEvent) -> None:
        """Append an attributed event to the workspace journal (adapter-only)."""


# ---------------------------------------------------------------------------
# Role record access
# ---------------------------------------------------------------------------


def _destination_key(path: str) -> str:
    """Filesystem-identity key for a (possibly unbound) output row.

    ``..`` segments collapse and case folds by host semantics — the same rules
    the eventual ``os.replace`` sees. Two rows with the same key would publish
    to one file, which no run may do (P2-4).
    """
    return os.path.normcase(os.path.normpath(path))


def _refuse_duplicate_destinations(role_id: str, rows: Sequence[str]) -> None:
    """Refuse a role whose output rows resolve to the same destination.

    Checked at policy load (raw rows) and again after run-level substitution
    (``RolePolicy.resolved``), because a ``{placeholder}`` param can make two
    distinct rows collapse onto one path. The message names the duplicated
    path and the role so the record can be repaired.
    """
    seen: dict[str, str] = {}
    for row in rows:
        key = _destination_key(row)
        if key in seen:
            raise ScopeViolation(
                f"role {role_id!r} declares output rows that resolve to the "
                f"same destination {row!r} (also {seen[key]!r}); a run must "
                "never publish two artifacts to one path"
            )
        seen[key] = row


@dataclass(frozen=True)
class RolePolicy:
    """The capability surface of one role, parsed from ``roles/<id>.json``."""

    id: str
    version: str
    read_glob: tuple[str, ...]
    write_glob: tuple[str, ...]
    deny_glob: tuple[str, ...]
    network: str  # "allow" | "deny"
    isolation: str  # "none" | "directory" | "redacted-input"
    blinded_from: tuple[str, ...]
    actor: str
    redacted_fields: frozenset[str]
    #: The role record's declared ``audit.emit`` actions, in record order.
    #: Convention: first = success verb, last = failure verb, intermediate
    #: actions are never selected; the adapter never invents a verb.
    emit_actions: tuple[str, ...]
    #: The role record's *unsubstituted* output rows. ``write_glob`` is the
    #: resolved form; this keeps the ``{arm}`` slot visible so the adapter can
    #: derive arm blinding from the role's own declaration instead of an
    #: arm vocabulary of its own (spec 04 §3 rule 2).
    write_template: tuple[str, ...] = ()
    #: ``schema`` declared on each output row, aligned with ``write_glob`` and
    #: ``write_template`` (``None`` when a row declares no schema). The adapter
    #: never invents a payload schema: an ``OK`` envelope may only name a
    #: schema the role record declares.
    write_schema: tuple[str | None, ...] = ()
    #: Every non-empty output schema the record declares, in record order.
    output_schemas: tuple[str, ...] = ()
    #: Every non-empty *input* schema the record declares, in record order.
    #: A request's ``input_schemas`` must be a subset of these names and carry
    #: one entry per input; the role record is the schema-name authority
    #: (api.py ``_check_role_compatibility``).
    input_schemas: tuple[str, ...] = ()
    #: The declared input schema names whose record row is ``required: true``,
    #: in record order. A request that omits one is refused before the handler
    #: (the run could not satisfy the role's declared input contract).
    required_input_schemas: tuple[str, ...] = ()
    #: Number of output rows the record marks ``required: true``. Coverage uses
    #: it as the floor a run must fill before it may report ``OK``.
    required_outputs: int = 0
    #: Refusal codes the record declares it may emit (spec 02 §6). The adapter
    #: checks this before attaching a code to a ``PARTIAL`` so the contract's
    #: role-compatibility step accepts the envelope.
    refusal_codes: tuple[str, ...] = ()

    @classmethod
    def from_record(
        cls, record: Mapping[str, Any], *, require_audit: bool = True
    ) -> "RolePolicy":
        independence = record.get("independence") or {}
        outputs = [
            o.get("write_glob")
            for o in record.get("outputs", [])
            if o.get("write_glob")
        ]
        # Same filtering rule as the contract's ``_declared_schemas``: only
        # rows carrying a string ``schema`` participate, in record order, so
        # the names the adapter verifies match the set the contract checks.
        declared_inputs = record.get("inputs")
        input_rows = [
            row
            for row in (declared_inputs if isinstance(declared_inputs, list) else [])
            if isinstance(row, Mapping)
            and isinstance(row.get("schema"), str)
            and row["schema"]
        ]
        input_schemas = tuple(str(row["schema"]) for row in input_rows)
        required_input_schemas = tuple(
            str(row["schema"]) for row in input_rows if row.get("required") is True
        )
        required_outputs = sum(
            1
            for row in record.get("outputs", [])
            if isinstance(row, Mapping)
            and row.get("write_glob")
            and row.get("required") is True
        )
        if not outputs:
            raise ScopeViolation(
                f"role {record.get('id')!r} declares no output write_glob; "
                "the adapter refuses to run a role without a declared write boundary "
                "(spec 04 §6)"
            )
        # P2-4: two output rows that already resolve to one destination can
        # never be published honestly, whatever the artifact names are. Refuse
        # the record at load; ``resolved`` repeats the check after substitution.
        _refuse_duplicate_destinations(str(record.get("id")), outputs)
        # Schema names travel with their row so a multi-output role can bind a
        # promoted artifact to the schema its own record declared.
        row_schemas: list[str | None] = []
        for output in record.get("outputs", []):
            if not output.get("write_glob"):
                continue
            declared = output.get("schema")
            row_schemas.append(
                str(declared) if isinstance(declared, str) and declared else None
            )
        audit = record.get("audit") or {}
        emit = tuple(audit.get("emit") or ())
        if require_audit and (
            not emit or any(not str(action).strip() for action in emit)
        ):
            raise ScopeViolation(
                f"role {record.get('id')!r} declares no audit actions; "
                "audit.emit must name at least one canonical event action "
                "(the adapter never invents a role verb)"
            )
        if require_audit and len(emit) < 2:
            # Only the one-action case is reachable: an empty/blank ``emit``
            # is refused just above. A role that can return a non-OK envelope
            # journals a *failure* verb, which it must declare itself — the
            # adapter will not invent one or reuse the completion verb.
            raise ScopeViolation(
                f"role {record.get('id')!r} declares 1 audit action; a role "
                "that can emit a non-OK envelope must declare a distinct "
                "failure action"
            )
        return cls(
            id=str(record["id"]),
            version=str(record.get("version", "0.0.0")),
            read_glob=tuple(record.get("read_glob", [])),
            write_glob=tuple(outputs),
            deny_glob=tuple(record.get("deny_glob", [])),
            network=str(record.get("network", "allow")),
            isolation=str(independence.get("isolation", "none")),
            blinded_from=tuple(independence.get("blinded_from", [])),
            actor=str(audit.get("actor", "{role}@{version}")),
            redacted_fields=frozenset(
                str(field).lower() for field in independence.get("redacted_fields", [])
            ),
            emit_actions=tuple(str(action) for action in emit),
            write_template=tuple(outputs),
            write_schema=tuple(row_schemas),
            output_schemas=tuple(s for s in row_schemas if s),
            input_schemas=input_schemas,
            required_input_schemas=required_input_schemas,
            required_outputs=required_outputs,
            refusal_codes=tuple(
                str(code)
                for code in record.get("refusal_codes", [])
                if isinstance(code, str)
            ),
        )

    _PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

    @classmethod
    def _substitute(cls, pattern: str, params: Mapping[str, str]) -> str:
        """Replace known placeholders; unknown row-level ones (e.g. ``{stu}``) stay.

        Phase-A globs may carry row-level placeholders the *caller* binds
        (e.g. ``{stu}`` per study); the adapter binds only the run-level
        params it was given and must not invent values.
        """

        def repl(match: re.Match[str]) -> str:
            key = match.group(1)
            return str(params[key]) if key in params else match.group(0)

        return cls._PLACEHOLDER_RE.sub(repl, pattern)

    def resolved(self, params: Mapping[str, str]) -> "RolePolicy":
        """Substitute run-level ``{placeholder}`` params into the glob rows."""
        write_glob = tuple(self._substitute(g, params) for g in self.write_glob)
        # P2-4: a param can collapse two distinct rows onto one destination
        # (``runs/{task}/{name}.json`` with name="verdict"), so the duplicate
        # check runs again on the resolved rows.
        _refuse_duplicate_destinations(self.id, write_glob)
        return RolePolicy(
            id=self.id,
            version=self.version,
            read_glob=tuple(self._substitute(g, params) for g in self.read_glob),
            write_glob=write_glob,
            deny_glob=tuple(self._substitute(g, params) for g in self.deny_glob),
            network=self.network,
            isolation=self.isolation,
            blinded_from=self.blinded_from,
            actor=self.actor.replace("{role}", self.id).replace(
                "{version}", self.version
            ),
            redacted_fields=self.redacted_fields,
            emit_actions=self.emit_actions,
            write_template=self.write_template,
            write_schema=self.write_schema,
            output_schemas=self.output_schemas,
            input_schemas=self.input_schemas,
            required_input_schemas=self.required_input_schemas,
            required_outputs=self.required_outputs,
            refusal_codes=self.refusal_codes,
        )


def load_role_policy(
    roles_dir: Path, role_id: str, *, require_audit: bool = True
) -> RolePolicy:
    """Load one role record; every failure is a typed ``ScopeViolation``.

    A torn record — unreadable file, invalid JSON, non-object document, or a
    missing required field — is a boundary defect, not a stack trace into the
    caller (R7). The message always names the record path so the operator can
    repair the record.
    """
    record_path = roles_dir / f"{role_id}.json"
    if not record_path.is_file():
        raise ScopeViolation(
            f"unknown role {role_id!r}: no roles/{role_id}.json under {roles_dir}"
        )
    try:
        text = record_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ScopeViolation(f"role record {record_path} is unreadable: {exc}") from exc
    try:
        record = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ScopeViolation(
            f"role record {record_path} is not valid JSON: {exc}"
        ) from exc
    if not isinstance(record, Mapping):
        raise ScopeViolation(
            f"role record {record_path} must be a JSON object, found "
            f"{type(record).__name__}"
        )
    try:
        return RolePolicy.from_record(record, require_audit=require_audit)
    except KeyError as exc:
        raise ScopeViolation(
            f"role record {record_path} is missing required field {exc}"
        ) from exc


def effective_arm(request: RunRequest) -> str | None:
    """The one definition of "this run has an arm" (spec 04 §3).

    ``RunRequest.arm`` is authoritative when present; ``params['arm']`` is the
    alternate spelling and must not create a second definition. The isolation
    gate, view directory, arm exclusions, promotion, and audit all consult this
    accessor, so a param-supplied arm cannot bypass any of them.

    Only ``None`` means "solo"; empty or whitespace-only values are refused by
    :func:`run_request_policy` and never reach the machinery.
    """
    if request.arm is not None:
        return request.arm
    return request.params.get("arm")


#: Run labels that become filesystem path segments (``runs/{task_id}``,
#: ``view/{arm}``). One plain segment only: no separators, drive letters,
#: stream suffixes, glob metacharacters, whitespace, or ``..``. Validated
#: *before* any directory is created or removed.
_LABEL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")


def _require_label(field: str, value: str) -> None:
    if _LABEL_RE.fullmatch(value) is None:
        raise ScopeViolation(
            f"{field} {value!r} is not a plain run label "
            "(expected [A-Za-z0-9][A-Za-z0-9._-]{0,63}); path separators, "
            "drive/stream syntax, glob characters, whitespace, and '..' are "
            "refused before any directory is touched"
        )
    if value.endswith("."):
        # P3-10: Windows strips trailing dots from a path segment, so
        # ``task_id="t-end."`` silently aliases the sibling ``runs/t-end`` and
        # ``"t-end.."`` resolves outside it (a raw FileNotFoundError from the
        # directory creation). Refuse before any directory exists. A bare
        # reserved device name (``CON``, ``NUL``, …) is *not* covered here and
        # remains deferred: it would need its own platform-dependent check.
        raise ScopeViolation(
            f"{field} {value!r} is not a plain run label: a label must not end "
            "with '.' — Windows strips trailing dots from a path segment, so "
            f"{value!r} would alias or escape the directory it names; refused "
            "before any directory is touched"
        )


def run_request_policy(roles_dir: Path, request: RunRequest) -> RolePolicy:
    """Policy for a request, with arm binding and the isolation gate.

    The effective arm is bound into the placeholder map before resolution so a
    role's ``{arm}`` slot never survives into :meth:`RoleSession._target_for`
    (where row-level placeholders bind from the artifact name — an arm must
    never be derived from a filename). When no arm is supplied the slot stays
    unbound and a write that needs it is refused at promotion time.

    ``{task_id}`` is bound from the validated ``RunRequest.task_id`` field,
    exactly like ``{arm}``: it is a *run* label, so it comes from one source of
    truth and never from ``params`` (a caller-supplied ``task_id`` key is
    refused here) and never from the artifact filename. Without this binding a
    role whose ``write_glob`` is ``runs/{task_id}/…`` (``reviewer``, ``coder``,
    ``tester``, ``orchestrator``) could not write its declared output at all.

    ``arm`` and ``task_id`` become path segments (``view/{arm}``,
    ``runs/{task_id}``) and are validated as plain labels here, before either
    adapter creates or removes a directory.

    A role claiming ``isolation: none`` while an arm is set is a defect at the
    boundary, not inside the role (spec 04 §3; Phase-E negative case).
    """
    if request.arm is not None and not request.arm.strip():
        raise ScopeViolation(
            "arm field RunRequest.arm is empty or whitespace-only; supply a "
            "concrete arm (or None for a solo run)"
        )
    param_arm = request.params.get("arm")
    if param_arm is not None and not param_arm.strip():
        raise ScopeViolation(
            "arm field params['arm'] is empty or whitespace-only; supply a "
            "concrete arm (or omit it for a solo run)"
        )
    # Validate both spellings independently: ``RunRequest.arm`` wins for the
    # run, but a malformed ``params['arm']`` must never be silently ignored.
    for label, value in (
        ("RunRequest.arm", request.arm),
        ("params['arm']", param_arm),
    ):
        if value is None:
            continue
        _require_label(label, value)
        if value not in ("A", "B"):
            raise ScopeViolation(
                f"{label} {value!r} is not a valid arm: Envelope@1 restricts "
                "arm to exactly 'A' or 'B' (case-sensitive) — aliasing such as "
                "'a' would collapse the two coding arms on a case-insensitive "
                "filesystem"
            )
    arm = effective_arm(request)
    if "task_id" in request.params:
        # One source of truth: the run label is the validated RunRequest field.
        # A params spelling could otherwise spoof another task's destination
        # (and would bypass ``_require_label`` below).
        raise ScopeViolation(
            "{task_id} is bound from RunRequest.task_id; do not pass it in params"
        )
    _require_label("RunRequest.task_id", request.task_id)
    params = dict(request.params)
    if request.arm is not None:
        params["arm"] = request.arm
    params["task_id"] = request.task_id
    policy = load_role_policy(roles_dir, request.role_id).resolved(params)
    if request.role_version != policy.version:
        raise ScopeViolation(
            f"request role_version {request.role_version!r} does not match role "
            f"record {request.role_id!r} version {policy.version!r}; the adapter "
            "refuses to stamp a journal row with a version the role record does "
            "not declare"
        )
    if arm is not None and policy.isolation == "none":
        raise ScopeViolation(
            f"role {request.role_id} claims isolation: none while arm="
            f"{arm} is set — dual-arm independence cannot hold"
        )
    if policy.isolation != "none" and arm is None:
        # Spec 02 §2 / api.py `_check_role_compatibility`: an envelope for an
        # isolated role must carry an arm. Refusing at policy load keeps the
        # adapter from ever building a solo envelope the contract rejects.
        slot = ""
        if any("{arm}" in row for row in policy.write_template):
            slot = " (its {arm} write slot cannot be bound)"
        raise ScopeViolation(
            f"role {request.role_id!r} declares isolation {policy.isolation!r}; "
            f"an arm is required{slot} — arm=None is only valid for "
            "isolation: none"
        )
    # Last, so the messages of the earlier gates stay the first failure (and
    # keep naming the label/version/arm defect the caller must fix first).
    _verify_input_schemas(request, policy)
    return policy


def _verify_input_schemas(request: RunRequest, policy: RolePolicy) -> None:
    """Refuse a request whose declared input schemas cannot be bound honestly.

    This is the only place input schemas are decided (F1): the caller states
    ``input_schemas`` positionally with ``inputs``, the role record supplies the
    set of names it accepts, and the adapter compares the two. Nothing is
    inferred from position, filename, or content, and nothing reaches
    ``Envelope@1`` that the caller did not declare.

    Runs *before* any ``runs/`` directory, ``rmtree``, read, or promotion: an
    unnameable input schema is a request defect, not an output defect, so it
    can never be reported as an ``INVALID_OUTPUT`` envelope over a run that
    already wrote files.
    """
    declared = policy.input_schemas
    supplied = tuple(request.input_schemas)
    if not declared:
        # The role claims no input schema, so the adapter has no authority to
        # judge names. It may still require one schema per input when the
        # caller declares any (a partial list cannot be bound positionally).
        if supplied and len(supplied) != len(request.inputs):
            raise ScopeViolation(
                f"request supplies {len(request.inputs)} inputs but declares "
                f"{len(supplied)} input_schemas; declare input_schemas in "
                "inputs order (or omit them entirely for a role that declares "
                f"no input schema, as {policy.id!r} does)"
            )
        return
    if len(supplied) != len(request.inputs):
        raise ScopeViolation(
            f"request supplies {len(request.inputs)} inputs but declares "
            f"{len(supplied)} input_schemas; declare input_schemas in inputs "
            f"order — role {policy.id!r} declares {list(declared)} and the "
            "adapter never guesses which schema belongs to which input"
        )
    undeclared = [name for name in supplied if name not in declared]
    if undeclared:
        raise ScopeViolation(
            f"request declares input schema(s) {undeclared!r} that role "
            f"{policy.id!r} does not declare; declared: {list(declared)}"
        )
    missing = [name for name in policy.required_input_schemas if name not in supplied]
    if missing:
        raise ScopeViolation(
            f"request omits required input schema(s) {missing!r} declared by "
            f"role {policy.id!r}; required inputs: "
            f"{list(policy.required_input_schemas)}"
        )


# ---------------------------------------------------------------------------
# Glob helpers (workspace-relative globs from Phase A records)
# ---------------------------------------------------------------------------


def glob_matches(relative_path: str, patterns: Sequence[str]) -> bool:
    """Match a workspace-relative POSIX path against Phase-A glob rows.

    Semantics follow fnmatch per segment, with ``**`` as a full segment
    matching zero or more segments. Each row translates to a regex —
    deterministic and testable.
    """
    target = relative_path.replace("\\", "/").strip("/")
    for pattern in patterns or ():
        segments = [
            seg for seg in pattern.replace("\\", "/").split("/") if seg not in ("", ".")
        ]
        pieces: list[str] = []
        for index, seg in enumerate(segments):
            piece = "^" if index == 0 else "/"
            if seg == "**":
                if index == len(segments) - 1:
                    # Trailing ``**``: everything below this point (or nothing).
                    pieces.append(r"(?:.*|/)?")
                    continue
                pieces.append(piece + r"(?:[^/]+/)*")
                continue
            token = re.escape(seg)
            token = token.replace(r"\*\*", r"(?:[^/]+/)*")  # embedded ** (rare)
            token = token.replace(r"\*", r"[^/]*")
            token = token.replace(r"\?", r"[^/]")
            pieces.append(piece + token)
        regex = "".join(pieces) + r"/?"
        # A globstar that is not the last segment absorbs the following
        # separator so it can also match zero intervening segments.
        regex = regex.replace(r"(?:[^/]+/)*/", r"(?:[^/]+/)*")
        if re.fullmatch(regex, target):
            return True
    return False


def relative_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def iter_read_files(root: Path, pattern: str) -> list[Path]:
    """Files under ``root`` matched by one root-relative Phase-A read glob.

    ``Path.glob`` changed semantics in 3.13: before it, a trailing ``**``
    component matched **directories only**, so ``**`` and
    ``workspaces/{ws}/literature/**`` silently matched *no files at all* on
    3.11/3.12 — both in the CI matrix. Appending ``/*`` enumerates the entries
    of every matched directory at any depth, which is exactly the documented
    3.13+ file set (verified against 3.12 and 3.14), and leaves every pattern
    without a trailing ``**`` segment untouched. Directories are filtered out
    by the caller-visible contract of this helper: it returns files only.
    """
    normalized = pattern.rstrip("/")
    if not normalized:
        return []
    if normalized == "**" or normalized.endswith("/**"):
        normalized += "/*"
    return [path for path in root.glob(normalized) if path.is_file()]


def hash_inputs(
    root: Path, inputs: Sequence[str], *, boundary: str = "run root"
) -> list[tuple[str, str]]:
    """Hash request inputs, refusing anything outside ``root`` first.

    ``RunRequest.inputs`` are caller-supplied strings. An absolute path or a
    path whose resolution leaves the root is a ``SCOPE_VIOLATION`` naming the
    input *before* any hash is computed — a raw ``ValueError`` from
    ``Path.relative_to`` would be a stack trace, not a refusal (Phase-E
    negative case). The relative POSIX path is what the envelope and journal
    record, so a path outside the root could never be represented honestly.
    """
    base = root.resolve()
    hashed: list[tuple[str, str]] = []
    for raw in inputs:
        candidate = Path(raw)
        if candidate.is_absolute():
            raise ScopeViolation(
                f"input {raw!s}: absolute paths are outside the {boundary} {base}"
            )
        resolved = (base / candidate).resolve()
        if not resolved.is_relative_to(base):
            raise ScopeViolation(
                f"input {raw!s}: resolves outside the {boundary} {base}"
            )
        if not resolved.is_file():
            raise ScopeViolation(f"input {raw!s} missing from the {boundary}")
        hashed.append((resolved.relative_to(base).as_posix(), sha256_file(resolved)))
    return hashed


# ---------------------------------------------------------------------------
# Redaction (spec 04 §3 rule 2): applied to the inputs, not requested from the agent
# ---------------------------------------------------------------------------


def _redact(data: Any, fields: frozenset[str]) -> Any:
    if isinstance(data, dict):
        return {
            k: ("[REDACTED]" if k.lower() in fields else _redact(v, fields))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_redact(v, fields) for v in data]
    return data


# ---------------------------------------------------------------------------
# Egress guard (spec 04 §2 network row: the patched entry points refuse)
# ---------------------------------------------------------------------------

#: The denying role for the *current* context, or ``None`` when egress is
#: allowed. A ContextVar (not a module boolean) keeps deny state per thread /
#: per asyncio task: the wrapped entry points are process-global because the
#: ``socket`` module is, so they consult this var before touching the network.
#: A concurrent ``network: allow`` run in another thread therefore sees
#: ``None`` and reaches the saved originals.
_EGRESS_DENY_ROLE: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "scholar_harness_egress_deny_role", default=None
)

#: Guards may nest (and different threads may guard concurrently); the module
#: attributes are installed once at depth 0 and restored at depth 0.
_EGRESS_INSTALL_LOCK = threading.RLock()
_EGRESS_GUARD_DEPTH = 0
_EGRESS_ORIGINALS: dict[str, Any] = {}

_EGRESS_PATCHED = (
    "socket",
    "SocketType",
    "create_connection",
    "getaddrinfo",
    "gethostbyname",
    "gethostbyname_ex",
    "gethostbyaddr",
    "getnameinfo",
)


def _refuse_egress_if_denied(call: str) -> None:
    role = _EGRESS_DENY_ROLE.get()
    if role is not None:
        raise EgressRefused(
            role,
            f"egress refused: network policy is deny for this role ({call})",
        )


def _install_egress_guard() -> dict[str, Any]:
    """Replace the resolver/socket entry points; return the saved originals."""
    originals = {name: getattr(socket, name) for name in _EGRESS_PATCHED}
    original_socket = originals["socket"]

    class _GuardedSocket(original_socket):  # type: ignore[misc, valid-type]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            _refuse_egress_if_denied("socket()")
            super().__init__(*args, **kwargs)

    def _guard(original: Any, call: str) -> Any:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _refuse_egress_if_denied(f"{call}()")
            return original(*args, **kwargs)

        return wrapper

    socket.socket = _GuardedSocket  # type: ignore[assignment]
    socket.SocketType = _GuardedSocket  # type: ignore[assignment]
    socket.create_connection = _guard(
        originals["create_connection"], "create_connection"
    )
    socket.getaddrinfo = _guard(originals["getaddrinfo"], "getaddrinfo")
    socket.gethostbyname = _guard(originals["gethostbyname"], "gethostbyname")
    socket.gethostbyname_ex = _guard(originals["gethostbyname_ex"], "gethostbyname_ex")
    socket.gethostbyaddr = _guard(originals["gethostbyaddr"], "gethostbyaddr")
    socket.getnameinfo = _guard(originals["getnameinfo"], "getnameinfo")
    return originals


def _restore_egress_guard(originals: Mapping[str, Any]) -> None:
    for name, original in originals.items():
        setattr(socket, name, original)


@contextmanager
def _deny_egress(role: str):
    """Install (once) the resolver/socket guard and deny this context only.

    Nested guards increment a depth counter and set the ContextVar to the
    innermost role; the outer guard's token restores the previous value on
    exit. Module attributes are restored exactly when the last guard (in any
    thread) exits, so a re-entrant guard never leaves a partially patched
    ``socket`` module behind.
    """
    global _EGRESS_GUARD_DEPTH
    with _EGRESS_INSTALL_LOCK:
        if _EGRESS_GUARD_DEPTH == 0:
            _EGRESS_ORIGINALS.clear()
            _EGRESS_ORIGINALS.update(_install_egress_guard())
        _EGRESS_GUARD_DEPTH += 1
    token = _EGRESS_DENY_ROLE.set(role)
    try:
        yield
    finally:
        _EGRESS_DENY_ROLE.reset(token)
        with _EGRESS_INSTALL_LOCK:
            _EGRESS_GUARD_DEPTH -= 1
            if _EGRESS_GUARD_DEPTH == 0:
                _restore_egress_guard(_EGRESS_ORIGINALS)
                _EGRESS_ORIGINALS.clear()


# ---------------------------------------------------------------------------
# The enforced role session
# ---------------------------------------------------------------------------


class RoleSession:
    """The only filesystem the role can touch (spec 04 §2).

    Every operation is validated before the filesystem is opened: reads and
    listings against the materialised run view, writes against ``write_glob``
    minus ``deny_glob`` with staging into ``runs/{task_id}/out/`` and atomic
    promotion. Network egress is a guard over the patched module-level socket
    and resolver entry points (see :meth:`egress_guard` for its scope limit).
    """

    # Default field redaction for ``isolation: redacted-input`` (identifying
    # bibliographic fields a blind arm must not see). ``doi``/``url``/``venue``
    # are identity-bearing too: leaving any of them visible re-identifies the
    # record by a single lookup, so the default covers the whole citation
    # fingerprint, not just title/authors/abstract.
    DEFAULT_REDACTED_FIELDS = frozenset(
        {
            "title",
            "authors",
            "abstract",
            "doi",
            "url",
            "venue",
            "journal",
            "year",
            "publication_date",
            "publisher",
            "affiliations",
        }
    )

    @classmethod
    def effective_redacted_fields(
        cls,
        role_fields: frozenset[str] = frozenset(),
        explicit_fields: frozenset[str] | None = None,
    ) -> frozenset[str]:
        """Union of defaults, role declaration, and the explicit adapter seam.

        Redaction is additive (spec 04 §3 rule 2): a role or caller can only
        add identifying fields, never drop the default citation fingerprint.
        Declared names are normalised to lowercase; matching is
        case-insensitive.
        """
        return frozenset(
            field.lower()
            for field in (
                set(cls.DEFAULT_REDACTED_FIELDS)
                | set(role_fields)
                | set(explicit_fields or ())
            )
        )

    def __init__(
        self,
        *,
        request: RunRequest,
        policy: RolePolicy,
        root: Path,
        view_dir: Path,
        out_dir: Path,
        egress_deny: bool,
    ) -> None:
        self._request = request
        self._policy = policy
        self._root = root.resolve()
        self._view_dir = view_dir
        self._out_dir = out_dir
        self._egress_deny = egress_deny
        self.staged: list[Path] = []  # promoted (absolute) output paths
        self.staged_sha256: list[str] = []

    # -- read boundary -----------------------------------------------------

    @property
    def view_dir(self) -> Path:
        return self._view_dir

    @property
    def promoted(self) -> tuple[Path, ...]:
        """Absolute paths this run promoted, in promotion order (read-only).

        The rollback path reads this to undo exactly what *this* run published
        when envelope construction fails after promotion. It is a snapshot, not
        a handle: a caller cannot mutate the session's state through it.
        """
        return tuple(self.staged)

    def read(self, path: Path | str) -> str:
        """Read a file inside the run view; everything else is out of scope."""
        resolved = (
            Path(path) if Path(path).is_absolute() else self._view_dir / Path(path)
        )
        target = resolved.resolve()
        if not target.is_relative_to(self._view_dir.resolve()):
            raise ScopeViolation(
                f"read {path!s}: outside the run view for {self._policy.id}"
                f" (arm {effective_arm(self._request) or 'solo'})"
            )
        if not target.is_file():
            raise ScopeViolation(f"read {path!s}: not materialised in the run view")
        return target.read_text(encoding="utf-8")

    def list(self, subdir: Path | str = ".") -> list[str]:
        """List files in the run view; the parent run directory is invisible."""
        target = (self._view_dir / Path(subdir)).resolve()
        if not target.is_relative_to(self._view_dir.resolve()):
            raise ScopeViolation(
                f"list {subdir!s}: outside the run view for {self._policy.id}"
            )
        if not target.exists():
            return []
        return [
            p.relative_to(self._view_dir).as_posix()
            for p in sorted(target.rglob("*"))
            if p.is_file()
        ]

    # -- write boundary ----------------------------------------------------

    _ROW_PLACEHOLDER_RE = re.compile(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}")
    _SAFE_TAG_RE = re.compile(r"[A-Za-z0-9._\-]{1,200}\Z")

    @staticmethod
    def _placeholder_matcher(
        basename: str, arm: str | None
    ) -> tuple[re.Pattern[str], list[tuple[str, str]]]:
        """Match a concrete artifact name against a row's *unbound* basename.

        The ``{arm}`` slot matches the run's arm **or nothing** — a handler may
        name the artifact with or without the arm segment, never with *another*
        arm's value. Every other row placeholder matches the text that binds
        it. Nothing is invented: the pattern comes from the role record.
        """
        pieces: list[str] = []
        groups: list[tuple[str, str]] = []
        pos = 0
        for index, match in enumerate(RolePolicy._PLACEHOLDER_RE.finditer(basename)):
            literal = basename[pos : match.start()]
            name = match.group(1)
            if name == "arm":
                # Omitting the arm omits the separator that introduced it, so
                # ``{batch}_decisions_{arm}.json`` accepts both
                # ``batch_001_decisions.json`` and ``batch_001_decisions_B.json``.
                body = literal.rstrip("_-.")
                separator = literal[len(body) :]
                pieces.append(re.escape(body))
                if arm:
                    pieces.append(f"(?:{re.escape(separator + arm)})?")
            else:
                pieces.append(re.escape(literal))
                group = f"p{index}"
                groups.append((name, group))
                pieces.append(f"(?P<{group}>.+?)")
            pos = match.end()
        pieces.append(re.escape(basename[pos:]))
        return re.compile("".join(pieces)), groups

    def _bind_row(
        self, row: str, template: str, tag: str, arm: str | None
    ) -> str | None:
        """Resolve ``row`` for ``tag``, or ``None`` when the row cannot bind it.

        The match pattern comes from the row's **template** with every
        run-level param bound except the arm (P2-4), so:

        * **Fixed basename** — a template whose basename carries no placeholder
          (``runs/{task_id}/packet.json``) matches the tag exactly: tag
          ``packet.json`` binds only that row, and ``verdict.json`` binds the
          sibling. A fixed row can never swallow another row's artifact (the
          old "no placeholders → bind anything" branch promoted every artifact
          to the first fixed row and overwrote it).
        * **``{arm}`` slot** — the one arm may be named or omitted, so a bare
          ``batch_001_decisions.json`` still binds
          ``…/batch_001_decisions_A.json`` for a single ``{arm}`` row.
        * **Tag placeholders** (``{batch}``, ``{stu}``, …) — they bind
          *structurally* to the artifact name. A placeholder that survived
          run-level resolution (e.g. an unbound ``{ws}``, or one in a directory
          segment) is never filled from the filename: the row stays
          un-bindable.
        """
        if any(ch in row for ch in "*?[]"):
            return None  # a concrete destination cannot still be a glob
        base = {k: v for k, v in self._request.params.items() if k != "arm"}
        # ``{task_id}`` is bound from the validated request field, exactly as
        # ``run_request_policy`` resolves it; the arm stays a slot so its
        # omitted form keeps binding.
        base.setdefault("task_id", self._request.task_id)
        agnostic = RolePolicy._substitute(template, base)
        basename = agnostic.rsplit("/", 1)[-1]
        matcher, groups = self._placeholder_matcher(basename, arm)
        match = matcher.fullmatch(tag)
        if match is None:
            return None
        bindings = {name: match.group(group) for name, group in groups}
        candidate = RolePolicy._PLACEHOLDER_RE.sub(
            lambda m: bindings.get(m.group(1), m.group(0)), row
        )
        if self._ROW_PLACEHOLDER_RE.search(candidate):
            return None  # a row-level placeholder has no value for this tag
        if any(ch in candidate for ch in "*?[]"):
            return None  # a concrete destination cannot still be a glob
        return candidate

    def _target_for(self, tag: str) -> str:
        """Resolve the promoted destination for output ``tag``.

        Run-level params are already bound in ``policy.write_glob`` — including
        ``{task_id}``, which :func:`run_request_policy` resolves from the
        validated ``RunRequest.task_id`` (never from ``params``, never from the
        artifact name).

        Binding truth table (P2-4) — ``row`` is the run-resolved row, and the
        *template* (params bound, arm kept as a slot) supplies the shape:

        ===============================  =========================  ==================
        template basename shape          tag                        result
        ===============================  =========================  ==================
        fixed filename                   equals the basename        that row
        fixed filename                   any other name             un-bindable
        ``{batch}``/``{stu}``/…          structural match           that row, bound
        ``{batch}``/``{stu}``/…          no structural match        un-bindable
        ``{arm}`` slot                   bare or the run's arm      that row
        ``{arm}`` slot                   the other arm's name       un-bindable
        unbound placeholder (any slot)   any                        un-bindable
        glob (``*``/``?``/``[]``)        any                        un-bindable
        ===============================  =========================  ==================

        Row-level placeholders (``{stu}``, ``{batch}``, …) bind *structurally*
        to the artifact name; the ``{arm}`` slot is never bound that way — it is
        bound only by ``RunRequest.arm`` (or ``params['arm']``) and otherwise
        refuses (spec 04 §3 rule 1: the arms never share a destination).

        More than one row binding the same tag is a :class:`ScopeViolation`
        naming the tag and the candidate rows: ambiguity is a refusal, never a
        first-match win (P2-4). A staged artifact name must be a plain filename
        — separators would let a caller carve the destination out of the
        boundary.
        """
        if ".." in tag or not self._SAFE_TAG_RE.fullmatch(tag):
            raise ScopeViolation(
                f"write {tag!r}: staged artifact names must be plain filenames"
            )
        arm = effective_arm(self._request)
        templates = self._policy.write_template or self._policy.write_glob
        unbound_arm: list[str] = []
        bound: list[tuple[str, str]] = []
        for row, template in zip(self._policy.write_glob, templates):
            if "{arm}" in row:
                # Defence in depth: an arm slot that survived resolution must
                # never receive a tag stem. Refuse rather than invent a name.
                unbound_arm.append(row)
                continue
            candidate = self._bind_row(row, template, tag, arm)
            if candidate is not None:
                bound.append((row, candidate))
        if len(bound) > 1:
            rows = ", ".join(repr(row) for row, _candidate in bound)
            raise ScopeViolation(
                f"write {tag!r}: {len(bound)} write_glob rows of "
                f"{self._policy.id} bind this artifact ({rows}); the adapter "
                "refuses an ambiguous binding instead of choosing a first "
                "match — the role record must declare distinct destinations"
            )
        if bound:
            return bound[0][1]
        if unbound_arm:
            raise ScopeViolation(
                f"write {tag!r}: role {self._policy.id!r} has an unbound {{arm}} "
                f"slot in write_glob {unbound_arm!r}; supply RunRequest.arm (or "
                "params['arm']) — the adapter never binds {arm} from an output "
                "filename"
            )
        raise ScopeViolation(
            f"write {tag!r}: no write_glob row of {self._policy.id} can bind "
            "this output filename"
        )

    def write(self, tag: str, content: bytes | str) -> Path:
        """Stage ``content`` as ``runs/{task_id}/out/{tag}``, validate, promote.

        The promoted destination is resolved from the role's ``write_glob``
        (row-level placeholders bind to the output filename) and validated
        against ``deny_glob`` *before* any byte is written outside staging;
        staging is removed on violation — a denied write leaves no file
        (Phase-E acceptance criterion 1).

        ``deny_glob`` is matched against the raw resolved path **and** its
        normalised form: a ``..`` segment anywhere in the chain (from a param or
        a record row) must not hide a denied destination from the denylist.

        A destination this run already promoted is refused too (P2-4): one run
        never publishes two artifacts to one path, so a second write with the
        same (or a case/normalisation-equivalent) destination cannot silently
        replace the first artifact before the journal describes it.
        """
        relative = self._target_for(tag)
        if self._policy.deny_glob:
            normalised = os.path.normpath(relative).replace(os.sep, "/")
            candidates = (
                [relative] if normalised == relative else [relative, normalised]
            )
            if any(
                glob_matches(candidate, self._policy.deny_glob)
                for candidate in candidates
            ):
                raise ScopeViolation(
                    f"write {relative!r}: inside deny_glob "
                    f"{list(self._policy.deny_glob)}"
                    " — the adapter never promotes a denied destination"
                )
        payload = content.encode("utf-8") if isinstance(content, str) else content
        promoted = (self._root / relative).resolve()
        if not promoted.is_relative_to(self._root):
            raise ScopeViolation(f"write {relative!r}: escapes the run root")
        key = os.path.normcase(str(promoted))
        if any(os.path.normcase(str(existing)) == key for existing in self.staged):
            raise ScopeViolation(
                f"write {relative!r}: this run already published an artifact to "
                f"{relative!r}; a run must never publish two artifacts to one "
                "path — the second would silently replace the first before the "
                "journal names it"
            )
        self._out_dir.mkdir(parents=True, exist_ok=True)
        staged = self._out_dir / Path(tag).name  # staging never escapes out/
        temp = staged.with_suffix(staged.suffix + ".partial")
        try:
            temp.write_bytes(payload)
            promoted.parent.mkdir(parents=True, exist_ok=True)
            os.replace(temp, promoted)
        finally:
            temp.unlink(missing_ok=True)
        self.staged.append(promoted)
        self.staged_sha256.append(sha256_bytes(payload))
        return promoted

    # -- network boundary --------------------------------------------------

    @contextmanager
    def egress_guard(self, _forced: bool | None = None):
        """Guarded egress context: the patched module-level entry points refuse before syscall.

        Under ``network: deny`` the module-level ``socket`` attributes named in
        ``_EGRESS_PATCHED`` (``socket``/``SocketType``, ``create_connection``,
        ``getaddrinfo``, ``gethostbyname``, ``gethostbyname_ex``,
        ``gethostbyaddr``, ``getnameinfo``) are replaced for the duration of the
        guard; each raises :class:`EgressRefused` before the original is
        called. The deny flag is a :class:`~contextvars.ContextVar`, so a
        concurrent ``network: allow`` thread still reaches the originals.

        Residual risk — **not** covered by this guard:

        1. Aliases and references captured *before* the guard
           (``from socket import socket, getaddrinfo``, a bound method, or any
           other module that already holds the original callable) bypass the
           module-level patch.
        2. Live socket objects created before the guard (or via an alias) can
           still ``connect``/``send``: only construction and the patched
           helpers are refused.
        3. Child threads and ``asyncio`` executor threads do not inherit the
           :class:`~contextvars.ContextVar`; a role that spawns one leaves the
           deny context.
        4. ``socket.socketpair`` and the private ``_socket`` module are not
           patched.
        5. Under ``isolation: redacted-input`` only ``.json`` files are
           redacted; any other file matched by ``read_glob`` is copied into the
           view unredacted.
        """
        if not self._egress_deny:
            yield
            return
        with _deny_egress(self._policy.id):
            yield

    @property
    def network_allowed(self) -> bool:
        return not self._egress_deny


# ---------------------------------------------------------------------------
# Adapter-shared helpers: view materialisation + promotion + journal
# ---------------------------------------------------------------------------


def _widen_row(template: str, arm: str | None = None) -> str:
    """Widen every ``{placeholder}`` in a record row to one segment wildcard.

    ``{arm}`` binds concretely when ``arm`` is supplied; every other row-level
    placeholder widens to ``*`` because it is bound per artifact at write time.
    Derived only from the role record — run-level ``params`` must not narrow a
    blinding/exclusion pattern (the caller may bind only some of them).
    """

    def repl(match: re.Match[str]) -> str:
        return arm if (arm is not None and match.group(1) == "arm") else "*"

    return RolePolicy._PLACEHOLDER_RE.sub(repl, template)


def sibling_write_globs(roles_dir: Path, policy: RolePolicy) -> tuple[str, ...]:
    """Workspace output globs of the roles this one is blinded from.

    The *filesystem* mechanism behind "blinding is applied to the inputs"
    (spec 04 §3 rule 2): a blinded arm's run view never materialises files
    under a blinded sibling's declared outputs. The sibling role records
    (Phase A) are the authority — nothing is redeclared here, and every row
    placeholder (including ``{arm}``/``{stu}``) widens to ``*`` so a caller's
    partial ``params`` cannot make the exclusion match nothing.

    Fail closed: a ``blinded_from`` name that does not resolve is a boundary
    defect. Silently skipping it would build an unblinded view while claiming
    isolation, so the ``ScopeViolation`` propagates.
    """
    globs: list[str] = []
    for sibling_id in policy.blinded_from:
        # A blinding sibling is only a *source* of output globs; it need not
        # be runnable (no declared audit actions) to protect the view.
        sibling = load_role_policy(roles_dir, sibling_id, require_audit=False)
        templates = sibling.write_template or sibling.write_glob
        globs.extend(_widen_row(template) for template in templates)
        # The sibling's in-progress staging, too, wherever it publishes.
        globs.append("runs/**/out/**")
    return tuple(globs)


def arm_exclusion_globs(
    policy: RolePolicy, request: RunRequest
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Derive the *same role's* other-arm outputs from its own record.

    Returns ``(other_arm_globs, this_arm_globs)``, both built from
    ``write_template`` alone. The arm vocabulary is never hard-coded,
    ``blinded_from`` is not consulted, and run-level ``params`` are ignored:
    ``other`` widens **every** placeholder (``…_decisions_{arm}.json`` →
    ``…_decisions_*.json``), while ``this`` binds the effective arm concretely
    and widens the rest. A candidate is another arm's artifact precisely when
    it matches ``other`` but not ``this`` (spec 04 §3 rules 1-2) — independent
    of how much the caller narrowed ``params``.

    Empty when the effective arm is ``None``: solo runs keep the whole view.

    Residual risk, stated rather than papered over: a role whose ``write_glob``
    has **no** ``{arm}`` slot declares no per-arm destination at all. The
    adapter then derives no exclusion and both arms target the same path — it
    does not invent an arm layout the Phase-A record did not declare.
    """
    arm = effective_arm(request)
    if arm is None:
        return (), ()
    templates = policy.write_template or policy.write_glob
    other = tuple(_widen_row(template) for template in templates)
    mine = tuple(_widen_row(template, arm) for template in templates)
    return other, mine


def view_exclusions(
    roles_dir: Path, policy: RolePolicy, request: RunRequest
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """All view exclusions for one run: ``(siblings, other arms, this arm)``.

    Shared by both adapters so the run view is built the same way on each
    surface (spec 04 §1; Phase-E acceptance criterion 2).
    """
    siblings: tuple[str, ...] = ()
    if effective_arm(request) is not None or policy.isolation != "none":
        siblings = sibling_write_globs(roles_dir, policy)
    other_arm, this_arm = arm_exclusion_globs(policy, request)
    return siblings, other_arm, this_arm


def materialise_view(
    *,
    request: RunRequest,
    policy: RolePolicy,
    root: Path,
    workspace_run_dir: Path,
    isolation: str,
    redacted_fields: frozenset[str] | None = None,
    excluded_globs: Sequence[str] = (),
    other_arm_globs: Sequence[str] = (),
    arm_globs: Sequence[str] = (),
) -> Path:
    """Build the run view for ``{role}@{arm}`` (spec 04 §2 read boundary).

    - ``directory``/``redacted-input`` isolation: one per-arm directory under
      ``runs/{task_id}/view/``; ordering, mtimes, and anything outside the
      view are not exposed (spec 04 §3 rule 3).
    - Files import only from ``read_glob`` matches; ``deny_glob`` never
      subtracts from the read view (R4).
    - ``excluded_globs`` (root-relative, params already substituted) remove a
      blinded sibling's outputs from the view *before* materialisation.
    - ``other_arm_globs``/``arm_globs`` remove this same role's outputs under
      a different arm: a path matching the widened row but not this arm's
      concrete row never enters the view. Phase-E acceptance criterion 2:
      arm B's run view does not contain arm A's outputs.
    """
    view_dir = workspace_run_dir / "view" / (effective_arm(request) or "solo")
    if view_dir.exists():
        shutil.rmtree(view_dir)
    view_dir.mkdir(parents=True)
    matched: list[Path] = []
    for pattern in policy.read_glob:
        matched.extend(path.resolve() for path in iter_read_files(root, pattern))
    seen: set[Path] = set()
    for path in sorted(matched):
        if path in seen:
            continue
        seen.add(path)
        rel = relative_posix(path, root)
        if glob_matches(rel, excluded_globs):
            # Blinded sibling output: never enters this arm's view.
            continue
        if (
            effective_arm(request) is not None
            and glob_matches(rel, other_arm_globs)
            and not glob_matches(rel, arm_globs)
        ):
            # This same role's output under a different arm.
            continue
        dest = view_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if isolation == "redacted-input" and rel.endswith(".json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                fields = RoleSession.effective_redacted_fields(
                    policy.redacted_fields, redacted_fields
                )
                dest.write_text(
                    json.dumps(_redact(data, fields), indent=2), encoding="utf-8"
                )
                continue
            except json.JSONDecodeError:
                pass
        shutil.copyfile(path, dest)
    return view_dir


def roll_back_promoted(session: RoleSession, run_dir: Path) -> None:
    """Undo exactly what **this** run promoted after a late failure (F3).

    Called by both adapters when envelope construction fails after the handler
    promoted artifacts: without it a ``ScopeViolation``/``ContractViolation``
    would leave published files behind with no journal row describing them.

    - Only ``session.promoted`` is deleted — the paths ``RoleSession.write``
      returned for *this* run. A pre-existing file this run overwrote cannot be
      restored (its bytes were replaced at promotion, before this call); the
      promoted path is removed so a failed run publishes nothing. Files this run
      never touched are never candidates.
    - Accepted fail-closed limit (P3-7): when this run overwrote a pre-existing
      artifact, rollback removes that path, so an **earlier** journal row naming
      it now points at a missing file. The alternative — leaving the failed
      run's bytes in place — would publish output the contract refused, which is
      worse. The removal is the documented outcome, not a silent repair, and the
      rollback leaves the original exception in charge (see below).
    - ``run_dir`` (``runs/{task_id}``, staging + view) is removed whole, and an
      empty ``runs/`` parent is removed with it — ``rmdir`` refuses a non-empty
      directory, so a sibling task's tree is never touched.
    - Best effort: every deletion error is swallowed so the *original*
      exception always reaches the caller. A failure here is not a new failure
      mode, and a rollback error must never mask a contract or scope refusal.
    """
    for path in reversed(session.promoted):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    shutil.rmtree(run_dir, ignore_errors=True)
    try:
        run_dir.parent.rmdir()
    except OSError:
        pass


def append_journal(workspace: Path, event: AuditEvent) -> Path:
    """Adapter-written audit attribution through the canonical writer.

    ``event_id``/``timestamp`` are minted once (``EVT-<ts>-<uuid6>``, no
    truncation collisions), ``action``/``status`` are normalised, and
    ``project.json``/``INDEX.md`` are reconciled. The adapter contributes the
    provenance it actually owns: the real actor, role version, adapter label,
    task/arm/isolation parameters, and input/output hashes under ``metrics``.
    It never forges an envelope id (the real one arrives with the envelope
    packet) and never writes a hardcoded writer label.

    A blank ``task_id`` is refused before the canonical writer is called: an
    audit row whose provenance cannot name its run is not evidence.
    """
    if not event.task_id.strip():
        raise ScopeViolation(
            f"audit event {event.action!r} has a blank task_id; the adapter "
            "never writes provenance that cannot name its run"
        )
    parameters = {
        **dict(event.parameters),
        "role_version": event.role_version,
        "adapter": event.adapter,
        "adapter_version": event.adapter_version,
        "task_id": event.task_id,
    }
    append_event(
        workspace,
        event.action,
        event.description,
        agent=event.actor,
        inputs=[path for path, _ in event.inputs],
        outputs=[path for path, _ in event.outputs],
        parameters=parameters,
        metrics={
            "input_sha256": [sha for _, sha in event.inputs],
            "output_sha256": [sha for _, sha in event.outputs],
            "duration_ms": event.duration_ms,
        },
        status=event.status,
    )
    return workspace / "audit" / "journal.jsonl"


# ---------------------------------------------------------------------------
# Envelope@1 construction (spec 04 §1; spec 02 §2-§4)
# ---------------------------------------------------------------------------

#: Placeholder used while the envelope is assembled; the real identity is
#: recomputed over the immutable fields once every field is final.
_ENVELOPE_ID_PLACEHOLDER = "ENV-" + "0" * 16

#: Journal ``status`` for each envelope state the adapter can produce (R6: the
#: adapter-written row and the returned envelope never disagree about the same
#: ``task_id``). ``OK`` is the canonical writer's ``SUCCESS``; the refusal
#: states keep their own closed names so a reader cannot mistake an invalid run
#: for a completed one.
_JOURNAL_STATUS = {
    EnvelopeStatus.OK: "SUCCESS",
    EnvelopeStatus.INVALID_OUTPUT: "INVALID_OUTPUT",
    EnvelopeStatus.PARTIAL: "PARTIAL",
}

#: The one registry code that speaks about unfilled coverage, and the only one
#: a ``PARTIAL`` envelope may attach to name its gap (spec 02 §3, §6).
_COVERAGE_GAP_CODE = RefusalCode.BATCH_INCOMPLETE.value


def journal_status_for(envelope: Envelope) -> str:
    """Journal ``status`` for one envelope: the envelope decides, not the caller.

    An envelope may only produce ``OK``/``PARTIAL``/``INVALID_OUTPUT`` from the
    run path; anything else maps to its own closed status name so an unexpected
    state is visible rather than silently reported as a success.
    """
    return _JOURNAL_STATUS.get(envelope.status, envelope.status.value)


def journal_action_for(policy: RolePolicy, envelope: Envelope) -> str:
    """The role's own declared verb for this envelope state.

    Record convention (holds for all eleven shipped records): the **first**
    declared action is the success verb, the **last** declared action is the
    failure verb, and intermediate actions are never selected by the adapter.
    ``OK`` therefore journals ``actions[0]`` and every non-OK state journals
    ``actions[-1]`` (``TASK_DISPATCHED``/``VERDICT_RECORDED``/``GATE_BLOCKED``
    → ``GATE_BLOCKED``; ``SCREENING_COMPLETED``/``SCREENING_BLOCKED`` →
    ``SCREENING_BLOCKED``). The adapter never invents a verb, and
    :func:`load_role_policy` refuses a runnable record with fewer than two
    actions so the two ends are always distinct.
    """
    actions = policy.emit_actions
    if envelope.status is EnvelopeStatus.OK:
        return actions[0]
    return actions[-1]


def _bind_inputs(
    request: RunRequest, policy: RolePolicy, inputs: Sequence[tuple[str, str]]
) -> list[EnvelopeInputRef]:
    """Bind hashed inputs to the schemas the caller declared (F1).

    The mapping is the caller's own declaration, position for position:
    ``Envelope@1.inputs[i].schema = request.input_schemas[i]``. No zip with
    ``policy.input_schemas`` and no positional guess — :func:`run_request_policy`
    has already refused a count mismatch, an undeclared name, or a missing
    required schema, so the two lists are the same length and every name is one
    the role declares.

    A caller-supplied name is attested **verbatim** whenever the caller supplied
    one, including for a role that declares no input schema at all: the adapter
    never replaces a stated name with a placeholder. Only when the caller
    supplied nothing (the role declares no inputs, or there are no inputs) does
    each ref carry the honest ``"untyped"`` placeholder — an ``Envelope@1``
    input schema must be a non-empty string and the adapter will not invent a
    name.
    """
    supplied = tuple(request.input_schemas)
    if supplied:
        schemas: tuple[str, ...] = supplied
    else:
        schemas = ("untyped",) * len(inputs)
    return [
        EnvelopeInputRef(schema=schema, path=path, sha256=sha)
        for schema, (path, sha) in zip(schemas, inputs)
    ]


def _finalise_envelope(envelope: Envelope, roles_dir: Path | None) -> Envelope:
    """Fill the deterministic id and let the contract authority judge it.

    ``roles_dir`` is always supplied by the adapters: :func:`validate` then runs
    the role-compatibility step (declared input/output schemas, refusal codes,
    arm-when-isolated, ``blinded_from``) exactly as the shipped
    ``python -m scholar_harness.contracts.envelope validate`` CLI does. An
    envelope the CLI would reject is never returned.
    """
    completed = envelope.model_copy(update={"envelope_id": envelope_id(envelope)})
    validate(completed.model_dump(by_alias=True), roles_dir=roles_dir)
    return completed


def _build_envelope(
    *,
    request: RunRequest,
    policy: RolePolicy,
    status: EnvelopeStatus,
    inputs: Sequence[EnvelopeInputRef],
    adapter: str,
    adapter_version: str,
    duration_ms: int | None,
    roles_dir: Path | None,
    refusal: EnvelopeRefusal | None = None,
    coverage: EnvelopeCoverage | None = None,
    output: EnvelopeOutput | None = None,
    output_sha256: str | None = None,
) -> Envelope:
    """Assemble one ``Envelope@1`` and validate it through the contract.

    The request's own ``task_id`` and ``arm`` are used verbatim: the adapter
    does not fabricate a placeholder identity (no ``"UNBOUND"`` task id, no
    coerced arm). A request whose identity cannot be represented is refused by
    :func:`run_request_policy` before a run starts; if it reaches this builder
    anyway, the contract's schema step rejects it and it surfaces as
    :class:`EnvelopeRefusalError`.
    """
    try:
        envelope = Envelope(
            envelope=1,
            envelope_id=_ENVELOPE_ID_PLACEHOLDER,
            role=request.role_id,
            role_version=policy.version,
            task_id=request.task_id,
            arm=effective_arm(request),
            created_at=datetime.now(UTC),
            status=status,
            retryable=False,
            human_action_required=False,
            refusal=refusal,
            coverage=coverage,
            inputs=list(inputs),
            parents=[],
            output=output,
            output_sha256=output_sha256,
            provenance=EnvelopeProvenance(
                adapter=adapter,
                adapter_version=adapter_version,
                isolation=policy.isolation,
                blinded_from=list(policy.blinded_from),
                duration_ms=duration_ms,
            ),
        )
    except ValidationError as exc:
        raise EnvelopeRefusalError(
            RefusalCode.INVALID_OUTPUT,
            "envelope schema validation failed: "
            + "; ".join(
                f"{'/'.join(str(part) for part in error['loc'])}: {error['msg']}"
                for error in exc.errors(include_url=False)
            ),
        ) from exc
    return _finalise_envelope(envelope, roles_dir)


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def payload_artifact_for(
    envelope: Envelope, promoted: Sequence[Path], root: Path
) -> str | None:
    """Root-relative POSIX path of the promoted artifact backing ``output``.

    ``Envelope@1`` carries at most one payload and ships only its canonical
    hash (``output_sha256``) — the envelope has no field naming the file. The
    journal does (F4): this helper identifies the backing artifact by the one
    rule that produced the hash — :func:`payload_digest`, the same contract
    ``output_sha256`` recipe the envelope builder used (P3-6) — scanning in
    promotion order so the *first* artifact (the one :func:`_envelope_for_run`
    chose as the payload) wins when two artifacts carry identical payloads.

    Restricted to ``OK``/``PARTIAL`` (F4). An ``INVALID_OUTPUT`` envelope may
    also carry a retained forensic payload (F2), and that artifact is already
    named in ``refusal.validation_findings``; the journal key stays scoped to
    the payload a caller may act on, so it is omitted for every refusal and
    invalid state.

    Returns ``None`` when the envelope carries no payload, is not a payload
    state, or when no promoted artifact reproduces the claimed hash; callers
    omit the journal key in that case rather than emitting a wrong path.
    """
    if (
        envelope.output is None
        or envelope.output_sha256 is None
        or envelope.status not in (EnvelopeStatus.OK, EnvelopeStatus.PARTIAL)
    ):
        return None
    for path in promoted:
        payload = _read_json_object(path)
        if payload is None:
            continue
        if payload_digest(payload) == envelope.output_sha256:
            return relative_posix(path, root)
    return None


def _resolve_output_schema(
    policy: RolePolicy, relative_path: str
) -> tuple[str | None, str | None]:
    """Bind a promoted artifact to one schema its own role record declares.

    Returns ``(schema, error)``. The adapter never invents a name and never
    falls back to ``"untyped"`` for ``output.schema``.
    """
    schemas = tuple(dict.fromkeys(policy.output_schemas))
    if not schemas:
        return None, (
            f"role {policy.id!r} declares no output schema; Envelope@1 cannot "
            "name a payload schema it was not given"
        )
    if len(schemas) == 1:
        return schemas[0], None
    matches: list[str] = []
    for row, schema in zip(policy.write_glob, policy.write_schema):
        if schema and glob_matches(relative_path, (_widen_row(row),)):
            matches.append(schema)
    candidates = tuple(dict.fromkeys(matches))
    if len(candidates) == 1:
        return candidates[0], None
    if not candidates:
        return None, (
            f"role {policy.id!r} declares {len(schemas)} output schemas and no "
            f"write_glob row binds promoted artifact {relative_path!r}"
        )
    return None, (
        f"role {policy.id!r} declares more than one output schema for promoted "
        f"artifact {relative_path!r}: ambiguous {list(candidates)}"
    )


def _invalid_output_envelope(
    *,
    request: RunRequest,
    policy: RolePolicy,
    adapter: str,
    adapter_version: str,
    duration_ms: int | None,
    roles_dir: Path | None,
    detail: str,
    finding: str,
    extra_findings: Sequence[str] = (),
    payload: tuple[str, dict[str, Any]] | None = None,
) -> Envelope:
    """A validated ``INVALID_OUTPUT`` envelope that retains the payload when allowed.

    R1: a refusal/invalid state ships ``inputs=()``. A run that failed output
    validation cannot honestly claim a bound input schema, and the contract
    checks every ``inputs[*].schema`` against the role's declaration.

    Retention (F2, spec 02 §3). ``INVALID_OUTPUT`` **retains** the payload for
    forensics — ``PayloadStatuses`` admits it and the frozen golden fixture
    ``tests/conformance/fixtures/envelope/invalid_output.json`` ships exactly
    such a payload (accepted by ``test_envelope.py``::
    ``test_invariant_invalid_output_retains_forensics``).

    Whether a given payload may be retained is decided by the **contract**, not
    by a local mirror of its rules (P3-6): the adapter builds the retained
    candidate and lets ``validate(..., roles_dir)`` judge it. The contract
    accepts the name only when the role declares that ``output.schema``
    (``contracts/envelope/api.py`` ``:273-278``) **and** a Contract v1 payload
    model is registered for it (``:279-286``); a refusal means the payload is
    unretainable, so the adapter retries with ``output=None`` and records the
    contract's own message in ``refusal.validation_findings``.

    ``output_sha256`` is computed with :func:`payload_digest`, which calls the
    contract's own :func:`~scholar_harness.contracts.envelope.api.output_sha256`
    — never a hand-rolled canonical hash: every payload digest the adapter
    emits or verifies goes through that one helper, and the contract's hash
    step agrees by construction (P3-6). ``coverage`` stays ``None``: an invalid
    run has no honest artifact count to report.

    The four unretainable cases, and why:

    - **zero artifacts** — there is no payload to retain;
    - **non-JSON-object artifact** — ``Envelope@1.output.data`` is a JSON
      object, and this class cannot invent a second encoding;
    - **undeclared schema** — ``api.py:273-278`` rejects any ``output.schema``
      the role does not declare, so the name has no honest home;
    - **declared but unregistered schema** — ``api.py:279-286`` rejects a
      declared schema absent from its payload registry (D11).

    In every unretainable case the envelope ships ``output=None`` /
    ``output_sha256=None`` and ``refusal.validation_findings`` names the
    artifact path plus the validator message.
    """

    def build(
        retained: EnvelopeOutput | None,
        digest: str | None,
        findings: list[str],
    ) -> Envelope:
        return _build_envelope(
            request=request,
            policy=policy,
            status=EnvelopeStatus.INVALID_OUTPUT,
            inputs=(),
            adapter=adapter,
            adapter_version=adapter_version,
            duration_ms=duration_ms,
            roles_dir=roles_dir,
            coverage=None,
            output=retained,
            output_sha256=digest,
            refusal=EnvelopeRefusal(
                code=EnvelopeStatus.INVALID_OUTPUT.value,
                detail=detail,
                validation_findings=findings,
            ),
        )

    findings = [finding, *extra_findings]
    if payload is None:
        return build(None, None, findings)
    schema, data = payload
    retained = EnvelopeOutput(schema=schema, data=data)
    # One digest recipe everywhere: ``payload_digest`` → contract helper.
    digest = payload_digest(data)
    try:
        return build(retained, digest, findings)
    except EnvelopeRefusalError as exc:
        # The contract is the only retention authority: no local mirror of its
        # declared/registered gates. It refused this name (undeclared schema or
        # no registered payload model), so the same envelope is representable
        # without a payload — ship that and keep the refusal as a finding.
        return build(None, None, [*findings, f"payload not retained: {exc}"])


def envelope_for_run(
    *,
    root: Path,
    request: RunRequest,
    policy: RolePolicy,
    inputs: Sequence[tuple[str, str]],
    adapter: str,
    adapter_version: str,
    duration_ms: int | None,
    staged: Sequence[Path],
    roles_dir: Path,
) -> Envelope:
    """Build the run's envelope from what the handler actually promoted.

    ``Envelope@1`` carries at most one output payload. With several artifacts
    the first artifact is the payload and ``coverage`` records the full count
    (``unit="artifact"``); the adapter-written journal remains the authoritative
    per-artifact record.

    Every promoted JSON artifact is validated through the contract authority
    before any of them is reported ``OK`` (R5): a run that promotes one valid
    and one invalid artifact is ``INVALID_OUTPUT`` naming the invalid artifact,
    never a silent success. That failing payload is **retained** under
    ``output`` for forensics when the role declares its schema and the contract
    registers it (F2); with two or more invalid artifacts the adapter retains
    none and says so in ``refusal.validation_findings``, because ``Envelope@1``
    carries at most one payload and picking one would be an invented rule.
    ``coverage.expected`` is the number of output rows
    the role marks ``required: true``, raised to ``produced`` because ``OK``
    requires ``produced == expected``: wildcard rows (``{batch}``, ``{stu}``)
    legitimately yield more artifacts than the record has rows. A run that
    fills fewer than the declared required rows is ``PARTIAL`` when the role
    declares a refusal code that can name the gap, else ``INVALID_OUTPUT``.

    ``roles_dir`` is required: every envelope returned here is validated with
    the same role-compatibility step the shipped CLI applies. A request whose
    envelope cannot be represented at all (rather than merely invalid output —
    e.g. a role record the contract rejects) leaves as a typed
    :class:`ContractViolation`, never a raw contract exception (R7); the
    adapters roll back this run's promoted artifacts when that happens (F3).

    An input count/name mismatch never reaches this builder: the pre-handler
    check in :func:`run_request_policy` refuses it, so there is no
    "cannot bind inputs to declared schemas" envelope (F1).
    """
    try:
        return _envelope_for_run(
            root=root,
            request=request,
            policy=policy,
            inputs=inputs,
            adapter=adapter,
            adapter_version=adapter_version,
            duration_ms=duration_ms,
            staged=staged,
            roles_dir=roles_dir,
        )
    except EnvelopeRefusalError as exc:
        raise ContractViolation(
            "cannot materialise a validated Envelope@1 for role "
            f"{request.role_id!r} task {request.task_id!r}: {exc}"
        ) from exc


@dataclass(frozen=True)
class _InvalidArtifact:
    """One promoted artifact that cannot produce an ``OK`` payload.

    ``payload`` is the retention candidate ``(schema, data)`` when the artifact
    parsed as a JSON object *and* a schema name was resolved; ``None`` when the
    artifact is unretainable for a structural reason. Whether the candidate is
    actually retained is decided by :func:`_invalid_output_envelope`, which lets
    the contract's role-compatibility step judge the schema name.
    """

    path: str
    message: str
    payload: tuple[str, dict[str, Any]] | None


def _envelope_for_run(
    *,
    root: Path,
    request: RunRequest,
    policy: RolePolicy,
    inputs: Sequence[tuple[str, str]],
    adapter: str,
    adapter_version: str,
    duration_ms: int | None,
    staged: Sequence[Path],
    roles_dir: Path,
) -> Envelope:
    """Body of :func:`envelope_for_run` (contract errors converted there)."""
    common = {
        "request": request,
        "policy": policy,
        "adapter": adapter,
        "adapter_version": adapter_version,
        "duration_ms": duration_ms,
        "roles_dir": roles_dir,
    }
    if not staged:
        return _invalid_output_envelope(
            **common,
            detail="handler produced no artifact",
            finding="no artifact promoted by the handler",
        )
    bound = _bind_inputs(request, policy, inputs)

    artifacts: list[tuple[str, str, dict[str, Any]]] = []
    invalid: list[_InvalidArtifact] = []
    for path in staged:
        relative = relative_posix(path, root)
        payload = _read_json_object(path)
        if payload is None:
            # Unretainable: Envelope@1.output.data is a JSON object and this
            # class has no second encoding for a bare blob.
            invalid.append(
                _InvalidArtifact(
                    path=relative,
                    message=(
                        f"promoted artifact {relative!r} is not a JSON object; "
                        "Envelope@1 can only carry an object payload"
                    ),
                    payload=None,
                )
            )
            continue
        schema, error = _resolve_output_schema(policy, relative)
        if schema is None:
            if error is None:
                # Invariant of _resolve_output_schema: exactly one of
                # (schema, error) is None. A silent fall-through here would
                # attach a payload to a schema name the adapter never resolved.
                raise ContractViolation(
                    "_resolve_output_schema returned neither a schema nor an "
                    f"error for promoted artifact {relative!r} of role "
                    f"{policy.id!r}; the adapter cannot name a payload schema "
                    "it did not resolve"
                )
            # Unretainable: no schema name to attach the payload to.
            invalid.append(_InvalidArtifact(path=relative, message=error, payload=None))
            continue
        # Probe this artifact with the contract itself: build the candidate
        # envelope the artifact would produce and let `validate` judge it. No
        # local re-implementation of the payload rules (R4).
        try:
            _build_envelope(
                **common,
                status=EnvelopeStatus.OK,
                inputs=bound,
                output=EnvelopeOutput(schema=schema, data=payload),
                output_sha256=payload_digest(payload),
                coverage=EnvelopeCoverage(expected=1, produced=1, unit="artifact"),
            )
        except EnvelopeRefusalError as exc:
            invalid.append(
                _InvalidArtifact(
                    path=relative,
                    message=f"promoted artifact {relative!r} failed validation: {exc}",
                    payload=(schema, payload),
                )
            )
            continue
        artifacts.append((relative, schema, payload))

    if invalid:
        # One bad artifact defeats OK, but retention is only honest for a
        # single failure: Envelope@1 carries at most one payload, so with two
        # or more the adapter retains none instead of inventing a precedence
        # rule (F2).
        if len(invalid) == 1:
            only = invalid[0]
            return _invalid_output_envelope(
                **common,
                detail=only.message,
                finding=only.message,
                payload=only.payload,
            )
        paths = ", ".join(repr(record.path) for record in invalid)
        note = (
            f"{len(invalid)} promoted artifacts are invalid ({paths}); no "
            "payload is retained because Envelope@1 carries at most one and "
            "the adapter will not guess which artifact is 'the' payload"
        )
        return _invalid_output_envelope(
            **common,
            detail=note,
            finding=invalid[0].message,
            extra_findings=[record.message for record in invalid[1:]] + [note],
            payload=None,
        )

    produced = len(artifacts)
    expected = max(policy.required_outputs, produced)
    first_schema = artifacts[0][1]
    first_payload = artifacts[0][2]
    output = EnvelopeOutput(schema=first_schema, data=first_payload)
    output_sha256 = payload_digest(first_payload)
    coverage = EnvelopeCoverage(expected=expected, produced=produced, unit="artifact")

    if produced < expected:
        detail = (
            f"coverage gap: {produced} of {expected} declared required output "
            "rows were produced"
        )
        gap = _COVERAGE_GAP_CODE if _COVERAGE_GAP_CODE in policy.refusal_codes else None
        if gap is None:
            detail += (
                f"; role {policy.id!r} declares no refusal code naming a "
                "coverage gap, so PARTIAL cannot be reported"
            )
            return _invalid_output_envelope(**common, detail=detail, finding=detail)
        try:
            return _build_envelope(
                **common,
                status=EnvelopeStatus.PARTIAL,
                # R1: only an OK envelope carries inputs.
                inputs=(),
                output=output,
                output_sha256=output_sha256,
                coverage=coverage,
                refusal=EnvelopeRefusal(
                    code=gap,
                    codes=[gap],
                    detail=detail,
                    validation_findings=[detail],
                ),
            )
        except EnvelopeRefusalError as exc:
            return _invalid_output_envelope(**common, detail=str(exc), finding=str(exc))

    try:
        return _build_envelope(
            **common,
            status=EnvelopeStatus.OK,
            inputs=bound,
            output=output,
            output_sha256=output_sha256,
            coverage=coverage,
        )
    except EnvelopeRefusalError as exc:
        # The contract validator is the authority; if it rejects an envelope we
        # built, the run is INVALID_OUTPUT with the validator's own finding.
        return _invalid_output_envelope(**common, detail=str(exc), finding=str(exc))
