"""Adapter core: the capability protocol and the enforced role session.

This module holds the shared, *enforced* machinery:

- :class:`RunRequest` / :class:`AuditEvent` / :class:`CapabilityAdapter` (spec 04 §1);
- :class:`RoleSession` — the only filesystem the role can touch. Its every
  operation is validated against the role record (``roles/<id>.json``) *and*
  the materialised run view; failures are typed refusals, never stack traces;
- :class:`InProcessAdapter` (``inprocess.py``) and :class:`OpencodeAdapter`
  (``opencode.py``) drive it for their respective surfaces.

Guarantee table (spec 04 §2):

| Guarantee        | Mechanism here                                        |
|------------------|--------------------------------------------------------|
| Write boundary   | stage → ``write_glob`` validation → promote; else refusal |
| Read boundary    | run view contains only ``read_glob`` matches            |
| Blinding         | per-arm view dirs; ``redacted-input`` strips fields     |
| Network          | socket-level guard; ``deny`` raises immediately         |
| Audit attribution| adapter writes the journal with hashes; roles never do  |
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import shutil
import socket
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

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
    (``audit/**`` included), and reads/listings outside the materialised run
    view. App mode turns this into an ``Envelope@1`` ``REFUSED`` with
    ``SCOPE_VIOLATION``.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.code = "SCOPE_VIOLATION"
        self.detail = detail


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
    """One role execution request. ``arm`` triggers isolation when set."""

    task_id: str
    role_id: str
    role_version: str
    inputs: tuple[str, ...]
    params: Mapping[str, str]  # {ws}, {batch}, {stu}, ...
    arm: str | None = None


@dataclass(frozen=True)
class AuditEvent:
    """Adapter-stamped provenance; the role never writes the journal itself."""

    action: str
    actor: str
    role_version: str
    description: str
    envelope_id: str
    inputs: tuple[tuple[str, str], ...] = ()  # (path, sha256)
    outputs: tuple[tuple[str, str], ...] = ()
    parameters: Mapping[str, Any] = field(default_factory=dict)
    status: str = "SUCCESS"
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class CapabilityAdapter(Protocol):
    """One interface, two implementations (spec 04 §1). Deliberately small."""

    def resolve_env(self, *, workspace: Path, config: Path) -> dict[str, str]:
        """Bind ``{CLI:*}``, ``{KIT_ROOT:*}``, ``{WORKSPACE}``, ``{CACHE}``,
        ``{CONFIG}`` for skill placeholder resolution."""

    def run(self, request: RunRequest, handler: Callable[[RoleSession], Any]) -> Any:
        """Execute one role against one request under enforced capability."""

    def emit(self, event: AuditEvent) -> None:
        """Append an attributed event to the workspace journal (adapter-only)."""


# ---------------------------------------------------------------------------
# Role record access
# ---------------------------------------------------------------------------


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

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "RolePolicy":
        independence = record.get("independence") or {}
        outputs = [
            o.get("write_glob")
            for o in record.get("outputs", [])
            if o.get("write_glob")
        ]
        if not outputs:
            raise ScopeViolation(
                f"role {record.get('id')!r} declares no output write_glob; "
                "the adapter refuses to run a role without a declared write boundary "
                "(spec 04 §6)"
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
            actor=str((record.get("audit") or {}).get("actor", "{role}@{version}")),
            redacted_fields=frozenset(independence.get("redacted_fields", [])),
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
        return RolePolicy(
            id=self.id,
            version=self.version,
            read_glob=tuple(self._substitute(g, params) for g in self.read_glob),
            write_glob=tuple(self._substitute(g, params) for g in self.write_glob),
            deny_glob=tuple(self._substitute(g, params) for g in self.deny_glob),
            network=self.network,
            isolation=self.isolation,
            blinded_from=self.blinded_from,
            actor=self.actor.replace("{role}", self.id).replace(
                "{version}", self.version
            ),
            redacted_fields=self.redacted_fields,
        )


def load_role_policy(roles_dir: Path, role_id: str) -> RolePolicy:
    record_path = roles_dir / f"{role_id}.json"
    if not record_path.is_file():
        raise ScopeViolation(
            f"unknown role {role_id!r}: no roles/{role_id}.json under {roles_dir}"
        )
    record = json.loads(record_path.read_text(encoding="utf-8"))
    return RolePolicy.from_record(record)


def run_request_policy(roles_dir: Path, request: RunRequest) -> RolePolicy:
    """Policy for a request, with the arm/isolation consistency gate.

    A role claiming ``isolation: none`` while an ``arm`` is set is a defect at
    the boundary, not inside the role (spec 04 §3; Phase-E negative case).
    """
    policy = load_role_policy(roles_dir, request.role_id).resolved(request.params)
    if request.arm is not None and policy.isolation == "none":
        raise ScopeViolation(
            f"role {request.role_id} claims isolation: none while arm="
            f"{request.arm} is set — dual-arm independence cannot hold"
        )
    return policy


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
# The enforced role session
# ---------------------------------------------------------------------------


class RoleSession:
    """The only filesystem the role can touch (spec 04 §2).

    Every operation is validated before the filesystem is opened: reads and
    listings against the materialised run view, writes against ``write_glob``
    minus ``deny_glob`` with staging into ``runs/{task_id}/out/`` and atomic
    promotion. Network egress is a socket-level guard.
    """

    # Default field redaction for ``isolation: redacted-input`` (identifying
    # bibliographic fields a blind arm must not see).
    DEFAULT_REDACTED_FIELDS = frozenset({"title", "authors", "abstract"})

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

    def read(self, path: Path | str) -> str:
        """Read a file inside the run view; everything else is out of scope."""
        resolved = (
            Path(path) if Path(path).is_absolute() else self._view_dir / Path(path)
        )
        target = resolved.resolve()
        if not target.is_relative_to(self._view_dir.resolve()):
            raise ScopeViolation(
                f"read {path!s}: outside the run view for {self._policy.id}"
                f" (arm {self._request.arm or 'solo'})"
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

    def _target_for(self, tag: str) -> str:
        """Resolve the promoted destination for output ``tag``.

        Run-level params are already bound in ``policy.write_glob``; remaining
        row-level placeholders (``{stu}``, ``{batch}``, …) bind to the output
        filename. A staged artifact name must be a plain filename — separators
        would let a caller carve the destination out of the boundary. Glob
        characters and unbindable placeholders disqualify a row.
        """
        if ".." in tag or not self._SAFE_TAG_RE.fullmatch(tag):
            raise ScopeViolation(
                f"write {tag!r}: staged artifact names must be plain filenames"
            )
        for row in self._policy.write_glob:
            # Bind row-level placeholders to the artifact's stem; the row's
            # own literal extension wins so ``{stu}.json`` + ``SCI-01.json``
            # yields ``SCI-01.json``, never ``SCI-01.json.json``.
            stem = Path(tag).stem
            candidate = self._ROW_PLACEHOLDER_RE.sub(stem, row)
            if re.search(r"\{[a-zA-Z_]", candidate):
                continue  # a row-level placeholder cannot bind to this tag
            if any(ch in candidate for ch in "*?[]"):
                continue  # a concrete destination cannot still be a glob row
            return candidate
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
        """
        relative = self._target_for(tag)
        if self._policy.deny_glob and glob_matches(relative, self._policy.deny_glob):
            raise ScopeViolation(
                f"write {relative!r}: inside deny_glob {list(self._policy.deny_glob)}"
                " — the adapter never promotes a denied destination"
            )
        payload = content.encode("utf-8") if isinstance(content, str) else content
        self._out_dir.mkdir(parents=True, exist_ok=True)
        staged = self._out_dir / Path(tag).name  # staging never escapes out/
        temp = staged.with_suffix(staged.suffix + ".partial")
        try:
            temp.write_bytes(payload)
            promoted = (self._root / relative).resolve()
            if not promoted.is_relative_to(self._root):
                raise ScopeViolation(f"write {relative!r}: escapes the run root")
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
        """Guarded egress context: sockets refuse instantly under ``network: deny``.

        This is the app-mode egress policy: a refused connection, not a
        timeout-and-retry (Phase-E acceptance criterion 3). Handlers must open
        sockets inside this guard; InProcessAdapter wraps the whole run in it.
        """
        deny = self._egress_deny
        if not deny:
            yield
            return
        original_socket = socket.socket
        original_create = socket.create_connection

        class _RefusingSocket(original_socket):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise EgressRefused(
                    self._session_role(),
                    "egress refused: network policy is deny for this role",
                )

        def _refusing_create(*args: Any, **kwargs: Any):
            raise EgressRefused(
                self._policy.id,
                "egress refused: network policy is deny for this role",
            )

        socket.socket = _RefusingSocket
        socket.create_connection = _refusing_create
        try:
            yield
        finally:
            socket.socket = original_socket
            socket.create_connection = original_create

    def _session_role(self) -> str:  # pragma: no cover — name helper only
        return self._policy.id

    @property
    def network_allowed(self) -> bool:
        return not self._egress_deny


# ---------------------------------------------------------------------------
# Adapter-shared helpers: view materialisation + promotion + journal
# ---------------------------------------------------------------------------


def sibling_write_globs(
    roles_dir: Path, policy: RolePolicy, params: Mapping[str, str]
) -> tuple[str, ...]:
    """Workspace output globs of the roles this one is blinded from.

    The *filesystem* mechanism behind "blinding is applied to the inputs"
    (spec 04 §3 rule 2): a blinded arm's run view never materialises files
    under a blinded sibling's declared ``write_glob``. The sibling role
    records (Phase A) are the authority — nothing is redeclared here.
    """
    globs: list[str] = []
    for sibling_id in policy.blinded_from:
        try:
            sibling = load_role_policy(roles_dir, sibling_id).resolved(params)
        except ScopeViolation:
            continue
        globs.extend(sibling.write_glob)
        # The sibling's in-progress staging, too, wherever it publishes.
        globs.append("runs/**/out/**")
    return tuple(globs)


def materialise_view(
    *,
    request: RunRequest,
    policy: RolePolicy,
    root: Path,
    workspace_run_dir: Path,
    isolation: str,
    redacted_fields: frozenset[str] | None = None,
    excluded_globs: Sequence[str] = (),
) -> Path:
    """Build the run view for ``{role}@{arm}`` (spec 04 §2 read boundary).

    - ``directory``/``redacted-input`` isolation: one per-arm directory under
      ``runs/{task_id}/view/``; ordering, mtimes, and anything outside the
      view are not exposed (spec 04 §3 rule 3).
    - Files import only from ``read_glob`` matches; ``deny_glob`` never
      subtracts from the read view (R4).
    - ``excluded_globs`` (root-relative, params already substituted) remove a
      blinded sibling's outputs from the view *before* materialisation —
      Phase-E acceptance criterion 2: arm B's run view does not contain arm
      A's outputs.
    """
    view_dir = workspace_run_dir / "view" / (request.arm or "solo")
    if view_dir.exists():
        shutil.rmtree(view_dir)
    view_dir.mkdir(parents=True)
    matched: list[Path] = []
    for pattern in policy.read_glob:
        for path in root.glob(pattern):
            if path.is_file():
                matched.append(path.resolve())
    seen: set[Path] = set()
    for path in sorted(matched):
        if path in seen:
            continue
        seen.add(path)
        rel = relative_posix(path, root)
        if glob_matches(rel, excluded_globs):
            # Blinded sibling output: never enters this arm's view.
            continue
        dest = view_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if isolation == "redacted-input" and rel.endswith(".json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                fields = redacted_fields or policy.redacted_fields
                if not fields:
                    fields = frozenset(RoleSession.DEFAULT_REDACTED_FIELDS)
                dest.write_text(
                    json.dumps(_redact(data, fields), indent=2), encoding="utf-8"
                )
                continue
            except json.JSONDecodeError:
                pass
        shutil.copyfile(path, dest)
    return view_dir


def append_journal(workspace: Path, event: AuditEvent) -> Path:
    """Adapter-written audit attribution (spec 04 §2, audit attribution row).

    Extends the workspace-manager event ledger schema
    (``.agents/skills/workspace-manager/references/audit_trace_spec.md`` §2)
    with the adapter-stamped provenance block; the adapter is the only writer.
    """
    journal = workspace / "audit" / "journal.jsonl"
    journal.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "event_id": f"EVT-{event.timestamp.replace('-', '').replace(':', '')[:17]}",
        "action": event.action,
        "agent_or_tool": event.actor,
        "description": event.description,
        "parameters": dict(event.parameters),
        "inputs": [path for path, _ in event.inputs],
        "outputs": [path for path, _ in event.outputs],
        "input_sha256": [sha for _, sha in event.inputs],
        "output_sha256": [sha for _, sha in event.outputs],
        "provenance": {
            "actor": event.actor,
            "role_version": event.role_version,
            "envelope_id": event.envelope_id,
            "writer": "InProcessAdapter@1",
        },
        "status": event.status,
        "timestamp": event.timestamp,
    }
    with journal.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
    return journal
