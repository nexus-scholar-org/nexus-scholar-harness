"""Agent-layer Phase E conformance: capability adapter (spec 04, spec 05 §5).

Every test drives the *enforced* app surface (:class:`InProcessAdapter`) with
a synthetic workspace; the negative cases are the Phase-E packet's own list:

- role writes a denied path;
- role writes to ``audit/**``;
- blinded role attempts to list the parent run directory;
- role claims ``isolation: none`` when ``arm`` is set.

Acceptance criteria (spec 05 §5):

1. write outside ``write_glob`` → ``SCOPE_VIOLATION`` and no file left;
2. arm B's run view does not contain arm A's outputs (asserted by listing);
3. ``network: deny`` produces a refused connection, not timeout-and-retry;
4. journal entries carry adapter-stamped actor, role version, and input/output
   hashes;
5. dev mode documents residual risk in the adapter docstring and README.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import socket
import sys
import threading
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scholar_harness.capabilities import (
    AuditEvent,
    ContractViolation,
    EgressRefused,
    InProcessAdapter,
    OpencodeAdapter,
    RoleSession,
    RunRequest,
    ScopeViolation,
    run_role,
)
from scholar_harness.capabilities.adapter import (
    CLI_SHORTS,
    ENV_BINDING_TABLE,
    KIT_MODULES,
    KIT_SHORTS,
    glob_matches,
    iter_read_files,
    load_role_policy,
    run_request_policy,
)
from scholar_harness.skills_portability import (
    DEV_KIT_ROOT_TEMPLATE,
    Preamble,
    render,
)
from scholar_harness.contracts.canonical import canonical_json_bytes
from scholar_harness.contracts.envelope.api import (
    EnvelopeRefusalError,
    envelope_id,
    validate,
)
from scholar_harness.contracts.envelope.api import (
    output_sha256 as contract_output_sha256,
)
from scholar_harness.contracts.envelope.model import (
    Envelope,
    EnvelopeOutput,
    EnvelopeProvenance,
    EnvelopeRefusal,
    EnvelopeStatus,
)
from scholar_harness.workspace.loader import resolve_skills_root

ROOT = Path(__file__).resolve().parents[2]
ROLES_DIR = ROOT / "roles"

_WS = "demo-project"
#: Params every synthetic run uses.
PARAMS = {"ws": _WS}

AGENT_RECORD = {
    "id": "conform-reviewer",
    "kind": "role",
    "version": "2.1.0",
    "network": "deny",
    "independence": {
        "blinded_from": ["publisher"],
        "isolation": "redacted-input",
    },
    "audit": {
        "actor": "{role}@{version}",
        # F5: a role that can emit a non-OK envelope must declare a distinct
        # failure action (the adapter journals it for INVALID_OUTPUT/PARTIAL
        # and never reuses the completion verb).
        "emit": ["REVIEW_COMPLETED", "REVIEW_BLOCKED"],
    },
    "read_glob": ["workspaces/{ws}/literature/**"],
    "outputs": [
        {"schema": "Review@1", "write_glob": "workspaces/{ws}/critique/{stu}.json"}
    ],
    "refusal_codes": ["SCOPE_VIOLATION"],
}

#: Dual-arm pair for the independence test: both arms read the batch, write
#: disjoint outputs; the blinded arm lists ``publisher`` so arm B never
#: materialises arm A's output.
ARM_PAIR = {
    "publisher": {
        **AGENT_RECORD,
        "id": "publisher",
        "independence": {"blinded_from": [], "isolation": "none"},
        "outputs": [
            {
                "schema": "Review@1",
                "write_glob": "workspaces/{ws}/extracted/A/{stu}.json",
            }
        ],
    },
    "arm-reviewer": {
        **AGENT_RECORD,
        "id": "arm-reviewer",
        "independence": {
            "blinded_from": ["publisher"],
            "isolation": "redacted-input",
        },
        "read_glob": ["workspaces/{ws}/literature/**"],
        "outputs": [
            {
                "schema": "Review@1",
                "write_glob": "workspaces/{ws}/extracted/B/{stu}.json",
            }
        ],
    },
}

NONE_ISOLATION_RECORD = {
    **AGENT_RECORD,
    "id": "solo-agent",
    "independence": {"blinded_from": [], "isolation": "none"},
}

AUDIT_GREEDY_RECORD = {
    **AGENT_RECORD,
    "id": "greedy-agent",
    # Declares the forbidden destination as an output; deny_glob still wins
    # (deny_glob is a write denylist and always overrides write_glob).
    "outputs": [
        {"schema": "Review@1", "write_glob": "workspaces/{ws}/audit/**"},
    ],
}


def _seed_workspace(root: Path) -> tuple[Path, Path]:
    """Fake repo root with a ``workspaces/{ws}`` tree + synthetic role records."""
    roles = root / "roles"
    roles.mkdir(parents=True)
    for record in (
        AGENT_RECORD,
        NONE_ISOLATION_RECORD,
        AUDIT_GREEDY_RECORD,
        *ARM_PAIR.values(),
    ):
        (roles / f"{record['id']}.json").write_text(
            json.dumps(record), encoding="utf-8"
        )
    workspace = root / "workspaces" / _WS
    batch = workspace / "literature"
    batch.mkdir(parents=True)
    (batch / "batch.json").write_text(
        json.dumps(
            {
                "title": "Secret Title Nobody Under Arm B May See",
                "authors": ["Doe, J.", "Roe, A."],
                "records": ["SCI-000001", "SCI-000002"],
            }
        ),
        encoding="utf-8",
    )
    return root, workspace


def _adapter(root: Path, workspace: Path) -> InProcessAdapter:
    return InProcessAdapter(root=root, workspace=workspace, roles_dir=root / "roles")


SCREENER_ROLE_VERSION = "2.0.0"


def _seed_screener_workspace(root: Path) -> tuple[Path, Path]:
    """Real-role fixture: a workspace tree the actual ``roles/screener.json``
    can read. Roles stay the real records (``ROLES_DIR``), never synthetic."""
    workspace = root / "workspaces" / _WS
    screening = workspace / "literature" / "screening"
    screening.mkdir(parents=True)
    (workspace / "literature" / "batch_001.json").write_text(
        json.dumps(
            {
                "batch_id": "batch_001",
                "records": [
                    {"title": "Alpha", "authors": ["Doe, J."], "abstract": "…"}
                ],
            }
        ),
        encoding="utf-8",
    )
    (workspace / "protocol.json").write_text(
        json.dumps({"schema": "Protocol@1"}), encoding="utf-8"
    )
    (workspace / "project.json").write_text(json.dumps({"slug": _WS}), encoding="utf-8")
    (workspace / "SCREENING_CRITERIA.md").write_text("# Criteria\n", encoding="utf-8")
    (workspace / "INDEX.md").write_text("# Index\n", encoding="utf-8")
    return root, workspace


def _screener_adapter(root: Path, workspace: Path) -> InProcessAdapter:
    return InProcessAdapter(root=root, workspace=workspace, roles_dir=ROLES_DIR)


#: The three inputs ``roles/screener.json`` declares, in record order.
SCREENER_INPUTS = (
    f"workspaces/{_WS}/literature/batch_001.json",
    f"workspaces/{_WS}/protocol.json",
    f"workspaces/{_WS}/SCREENING_CRITERIA.md",
)
#: Their declared schemas, positionally. F1: the *caller* states these; the
#: adapter verifies them against the role record and never guesses.
SCREENER_INPUT_SCHEMAS = (
    "ScreeningBatch@1",
    "Protocol@1",
    "ScreeningCriteria@1",
)


def _screener_request(
    task: str,
    arm: str | None = "A",
    *,
    inputs: tuple[str, ...] = SCREENER_INPUTS,
    input_schemas: tuple[str, ...] = SCREENER_INPUT_SCHEMAS,
) -> RunRequest:
    return RunRequest(
        task_id=task,
        role_id="screener",
        role_version=SCREENER_ROLE_VERSION,
        # The three inputs ``roles/screener.json`` declares, in record order:
        # ScreeningBatch@1, Protocol@1, ScreeningCriteria@1. ``input_schemas``
        # must state the same names positionally (F1); the adapter refuses a
        # count/name gap *before* the handler rather than guessing a binding.
        inputs=inputs,
        params=PARAMS,
        arm=arm,
        input_schemas=input_schemas,
    )


def _decisions_blob(arm: str | None) -> str:
    return json.dumps({"arm": arm or "solo", "decisions": []})


def _request(role: str = "conform-reviewer", task: str = "t-1", **kw) -> RunRequest:
    # ``Envelope@1`` requires an arm for every role whose isolation is not
    # ``"none"`` (api.py role compatibility), so synthetic isolated roles run
    # with ``arm="A"`` by default. ``solo-agent`` / ``publisher`` callers pass
    # ``arm=None`` explicitly: a solo request is a deliberate choice, never a
    # default.
    kw.setdefault("arm", "A")
    return RunRequest(
        task_id=task,
        role_id=role,
        role_version="2.1.0",
        inputs=(f"workspaces/{_WS}/literature/batch.json",),
        params=PARAMS,
        **kw,
    )


# ---------------------------------------------------------------------------
# Criterion 1 + negative cases: denied writes leave no file
# ---------------------------------------------------------------------------


def test_write_outside_write_glob_refused_with_no_file(tmp_path: Path) -> None:
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    candidates = [
        (
            "../../literature/evil.json",
            root / "workspaces" / _WS / "literature" / "evil.json",
        ),
        (
            "runs/other-task/out/evil.json",
            root / "runs" / "other-task" / "out" / "evil.json",
        ),
    ]
    for tag, path in candidates:
        with pytest.raises(ScopeViolation) as excinfo:
            adapter.run(_request(), lambda s: s.write(tag, "{}"))
        assert excinfo.value.code == "SCOPE_VIOLATION"
        assert not path.exists(), f"SCOPE_VIOLATION left a file behind at {path}"


def test_write_to_audit_glob_is_denied(tmp_path: Path) -> None:
    """Negative: role writes to ``audit/**`` — deny_glob wins even when the
    output row itself declares the audit tree (deny always overrides)."""
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    journal = workspace / "audit" / "journal.jsonl"
    before = journal.read_text(encoding="utf-8") if journal.is_file() else ""
    with pytest.raises(ScopeViolation):
        adapter.run(
            _request(role="greedy-agent"),
            lambda s: s.write("../audit/journal.jsonl", '{"forged": true}'),
        )
    after = journal.read_text(encoding="utf-8") if journal.is_file() else ""
    assert before == after, "a denied write mutated the audit journal"


def test_role_cannot_write_journal_directly(tmp_path: Path) -> None:
    """The adapter writes the journal; roles never can (spec 04 §2)."""
    root, workspace = _seed_workspace(tmp_path)
    journal = workspace / "audit" / "journal.jsonl"
    assert not journal.is_file(), (
        "journal must not exist before the adapter runs (roles cannot create it)"
    )
    adapter = _adapter(root, workspace)

    def handler(session: RoleSession) -> None:
        session.write("SCI-01.json", '{"verdict": "include"}')

    adapter.run(_request(), handler)
    assert journal.is_file()
    record = json.loads(journal.read_text(encoding="utf-8").splitlines()[-1])
    # F5: the synthetic role's output schema (``Review@1``) is not registered,
    # so the run is INVALID_OUTPUT and journals the role's *failure* verb (its
    # second declared action) — never the completion verb.
    assert record["action"] == "REVIEW_BLOCKED"
    assert record["parameters"]["adapter"] == "in-process"
    assert "provenance" not in record


def test_blinded_role_cannot_list_parent_run_directory(tmp_path: Path) -> None:
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    checks = []

    def handler(session: RoleSession) -> None:
        try:
            session.list("..")
        except ScopeViolation as exc:
            checks.append(exc.code)
        try:
            session.list("../../..")
        except ScopeViolation as exc:
            checks.append(exc.code)

    adapter.run(_request(), handler)
    assert checks == ["SCOPE_VIOLATION", "SCOPE_VIOLATION"], (
        "the parent run directory must be invisible to a blinded role"
    )


def test_role_claims_isolation_none_with_arm_set(tmp_path: Path) -> None:
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    with pytest.raises(ScopeViolation) as excinfo:
        adapter.run(_request(role="solo-agent", arm="A"), lambda s: None)
    assert "isolation: none" in excinfo.value.detail
    assert "arm" in excinfo.value.detail


# ---------------------------------------------------------------------------
# Criterion 2: arm B's run view hides arm A's outputs
# ---------------------------------------------------------------------------


def test_arm_b_view_does_not_contain_arm_a_outputs(tmp_path: Path) -> None:
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    # Arm A runs first and publishes its output into the workspace tree.
    adapter.run(
        # ``publisher`` declares ``isolation: none``: a solo request is the
        # only shape its record permits.
        _request(role="publisher", task="t-dual", arm=None),
        lambda s: s.write("SCI-01.json", '{"verdict": "include", "arm": "A"}'),
    )
    assert (workspace / "extracted" / "A" / "SCI-01.json").is_file()

    # Arm B's view, materialised *after* A published, must not contain it.
    seen: list[str] = []
    adapter.run(
        _request(role="arm-reviewer", task="t-dual", arm="B"),
        lambda s: seen.extend(s.list()),
    )
    assert seen, "arm B's view should not be empty (it sees inputs)"
    # Asserted by listing the view: A's published path pattern absent, and no
    # raw staging from any arm leaks into a read view.
    assert not any("extracted/A" in entry for entry in seen)
    assert all(not entry.startswith("runs/") for entry in seen)
    # Isolation did not degenerate to an empty view: the input is present,
    # redacted.
    view = (
        adapter.workspace
        / "runs"
        / "t-dual"
        / "view"
        / "B"
        / "workspaces"
        / _WS
        / "literature"
        / "batch.json"
    )
    assert view.is_file()
    data = json.loads(view.read_text(encoding="utf-8"))
    assert "Secret Title Nobody Under Arm B May See" not in json.dumps(data), (
        "redacted-input isolation leaked an identifying field into the view"
    )


def test_directory_isolation_gives_disjoint_views(tmp_path: Path) -> None:
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    views: dict[str, str] = {}

    def make_handler(arm: str):
        def handler(session: RoleSession) -> None:
            views[arm] = str(session.view_dir)
            session.list()

        return handler

    adapter.run(_request(role="arm-reviewer", task="t-iso", arm="A"), make_handler("A"))
    adapter.run(_request(role="arm-reviewer", task="t-iso", arm="B"), make_handler("B"))
    assert views["A"] != views["B"], "per-arm view directories must be disjoint"


# ---------------------------------------------------------------------------
# Criterion 3: network deny is a refused connection, not timeout-and-retry
# ---------------------------------------------------------------------------


def test_network_deny_refuses_connection_immediately(tmp_path: Path) -> None:
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    outcomes: list[str] = []

    def handler(session: RoleSession) -> None:
        with session.egress_guard():
            try:
                # A closed local port: without the guard this would be an OS
                # round-trip (refused here only after real syscalls) or, on a
                # filtered host, a timeout-and-retry. Under the guard the
                # EgressRefused must be raised *before* any socket is created.
                socket.create_connection(("127.0.0.1", 59999), timeout=0.05)
                outcomes.append("CONNECTED")
            except EgressRefused:
                outcomes.append("REFUSED")
            except OSError:
                outcomes.append("SYSCALL_REACHED")

    adapter.run(_request(), handler)
    assert outcomes == ["REFUSED"], (
        "network: deny must refuse at the guard, never reach (or time out) syscalls"
    )


def test_egress_guard_is_reentrant_safe(tmp_path: Path) -> None:
    """P7: restoration is checked by identity, including the exception path."""
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    original_socket = socket.socket
    original_socket_type = socket.SocketType
    original_getaddrinfo = socket.getaddrinfo
    observed: dict[str, bool] = {}

    def handler(session: RoleSession) -> None:
        with session.egress_guard():
            observed["inner_socket"] = socket.socket is not original_socket
            observed["inner_gai"] = socket.getaddrinfo is not original_getaddrinfo
        # The adapter-level guard is still active after the nested one exits.
        observed["outer_patched"] = socket.socket is not original_socket
        try:
            with session.egress_guard():
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        observed["after_inner_exception_patched"] = socket.socket is not original_socket

    adapter.run(_request(), handler)
    assert observed == {
        "inner_socket": True,
        "inner_gai": True,
        "outer_patched": True,
        "after_inner_exception_patched": True,
    }
    assert socket.socket is original_socket
    assert socket.SocketType is original_socket_type
    assert socket.getaddrinfo is original_getaddrinfo

    # An exception escaping the run must also restore the module attributes.
    with pytest.raises(RuntimeError):
        adapter.run(
            _request(task="t-egress-raise"),
            lambda s: (_ for _ in ()).throw(RuntimeError("boom")),
        )
    assert socket.socket is original_socket
    assert socket.getaddrinfo is original_getaddrinfo


def test_network_allow_runs_normally(tmp_path: Path) -> None:
    root, workspace = _seed_workspace(tmp_path)
    allowed = dict(AGENT_RECORD, id="allow-agent", network="allow")
    roles = root / "roles"
    (roles / "allow-agent.json").write_text(json.dumps(allowed), encoding="utf-8")
    adapter = _adapter(root, workspace)
    flag: list[bool] = []
    adapter.run(_request(role="allow-agent"), lambda s: flag.append(s.network_allowed))
    assert flag == [True]


# ---------------------------------------------------------------------------
# Criterion 4: adapter-stamped audit attribution
# ---------------------------------------------------------------------------


def test_journal_carries_adapter_stamped_attribution(tmp_path: Path) -> None:
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)

    def handler(session: RoleSession) -> None:
        session.write("SCI-01.json", '{"verdict": "include"}')

    adapter.run(_request(), handler)
    journal = workspace / "audit" / "journal.jsonl"
    lines = [
        json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()
    ]
    record = lines[-1]
    # Actor is the adapter-stamped role@version from the Phase A record —
    # never a generic actor.
    assert record["agent_or_tool"] == "conform-reviewer@2.1.0"
    assert record["parameters"]["role_version"] == "2.1.0"
    assert record["parameters"]["adapter"] == "in-process"
    assert record["parameters"]["adapter_version"] == "1.0.0"
    assert record["parameters"]["task_id"] == "t-1"
    # Input hash matches the seeded file's content hash.
    seeded = workspace / "literature" / "batch.json"
    expected = hashlib.sha256(seeded.read_bytes()).hexdigest()
    assert record["metrics"]["input_sha256"] == [expected]
    # Output hash matches the promoted artifact's content hash.
    output_path = root / "workspaces" / _WS / "critique" / "SCI-01.json"
    assert output_path.is_file()
    assert record["metrics"]["output_sha256"] == [
        hashlib.sha256(output_path.read_bytes()).hexdigest()
    ]
    # The canonical writer mints identity; no hardcoded provenance block.
    assert "provenance" not in record


def test_promoted_output_matches_write_glob(tmp_path: Path) -> None:
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    promoted: list[Path] = []
    adapter.run(
        _request(),
        lambda s: promoted.append(s.write("SCI-02.json", '{"verdict": "defer"}')),
    )
    rel = promoted[0].resolve().relative_to(root).as_posix()
    assert rel == f"workspaces/{_WS}/critique/SCI-02.json"
    # The tag binds ``{stu}``; ``{ws}`` was already bound by the run params.
    assert glob_matches(rel, ("workspaces/demo-project/critique/SCI-02.json",))


# ---------------------------------------------------------------------------
# Criterion 5: dev mode documents residual risk honestly
# ---------------------------------------------------------------------------


def test_dev_adapter_documents_residual_risk() -> None:
    docstring = OpencodeAdapter.__doc__ or ""
    module_doc = (
        __import__(
            "scholar_harness.capabilities.opencode",
            fromlist=["__doc__"],
        ).__doc__
        or ""
    )
    text = docstring + module_doc
    assert "Residual risk" in text or "residual risk" in text
    assert "best-effort" in text.lower()
    assert "InProcessAdapter" in text, (
        "dev mode must name the enforced adapter it does not replace"
    )


def test_dev_adapter_does_not_claim_enforcement(tmp_path: Path) -> None:
    root, _workspace = _seed_workspace(tmp_path)
    dev = OpencodeAdapter(workspace=root, roles_dir=root / "roles")
    policy = dev.run  # exercising the honest path: view + session exist
    assert callable(policy)
    # Dev-mode enforcement is best-effort: the session is returned to the
    # handler, but its socket guard is never installed (residual risk #2).
    seen: list[bool] = []
    dev.run(
        _request(),
        lambda s: seen.append(s.network_allowed),  # dev: cooperative egress
    )
    assert seen == [True]


def test_empty_out_dir_left_after_scope_violation(tmp_path: Path) -> None:
    """Criterion 1's flip side: run staging leaves no output when refused."""
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    with pytest.raises(ScopeViolation):
        adapter.run(_request(), lambda s: s.write("../../audit/forged.jsonl", "x"))
    out_dir = workspace / "runs" / "t-1" / "out"
    assert not out_dir.exists() or not any(out_dir.iterdir())


# ---------------------------------------------------------------------------
# Read-glob semantics on every supported interpreter (py<3.13 trailing ``**``)
# ---------------------------------------------------------------------------


def test_iter_read_files_is_interpreter_independent(tmp_path: Path) -> None:
    """A root-relative read glob must match the same *files* on 3.11 and 3.13+.

    ``Path.glob`` changed in 3.13: before it, a trailing ``**`` component
    matched directories only, so ``**`` and ``workspaces/{ws}/literature/**``
    returned **no files at all** on 3.11/3.12 — the two versions in the CI
    matrix. The run view is built from these patterns, so the regression is
    silent: every role with a trailing-``**`` read glob gets an empty view.
    This test pins the helper's file set rather than the stdlib's, so it fails
    on any interpreter that reintroduces the divergence.
    """
    for rel in (
        "a/f.txt",
        "a/deep/x.json",
        "a/deep/er/y.json",
        "b.txt",
        "c/z.txt",
    ):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")

    def files(pattern: str) -> list[str]:
        return sorted(
            iter_read_files(tmp_path, pattern)
        )

    assert files("**") == [
        tmp_path / "a/deep/er/y.json",
        tmp_path / "a/deep/x.json",
        tmp_path / "a/f.txt",
        tmp_path / "b.txt",
        tmp_path / "c/z.txt",
    ]
    assert files("a/**") == [
        tmp_path / "a/deep/er/y.json",
        tmp_path / "a/deep/x.json",
        tmp_path / "a/f.txt",
    ]
    assert files("a/**/*") == files("a/**")
    assert files("c/*.txt") == [tmp_path / "c/z.txt"]
    # Directories are never part of a read view (``**`` matches them on 3.13+).
    assert all(path.is_file() for path in iter_read_files(tmp_path, "**"))
    # A missing base is empty, never an error: read globs are optional inputs.
    assert iter_read_files(tmp_path, "nope/**") == []


def test_screener_view_includes_deeply_nested_literature_files(
    tmp_path: Path,
) -> None:
    """Criterion 2 premise: the real screener's ``literature/**`` glob is live.

    On 3.11/3.12 the trailing ``**`` returned directories only, so the view was
    empty and *every* blinding assertion passed for the wrong reason. A file
    three directories deep must be listed and readable in the view.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    nested = workspace / "literature" / "screening" / "archive" / "2026"
    nested.mkdir(parents=True)
    (nested / "historic.json").write_text(
        json.dumps({"batch_id": "historic"}), encoding="utf-8"
    )
    adapter = _screener_adapter(root, workspace)
    seen: list[str] = []
    read_back: list[dict[str, object]] = []

    def handler(session: RoleSession) -> None:
        seen.extend(session.list())
        read_back.append(
            json.loads(
                session.read(
                    f"workspaces/{_WS}/literature/screening/archive/2026/historic.json"
                )
            )
        )

    adapter.run(_screener_request("t-scr-nested", arm="A"), handler)

    assert any(
        entry.endswith("literature/screening/archive/2026/historic.json")
        for entry in seen
    ), seen
    assert read_back == [{"batch_id": "historic"}]


# ---------------------------------------------------------------------------
# Same-role dual-arm blinding + arm binding (real roles/screener.json)
# ---------------------------------------------------------------------------


def test_real_screener_dual_arms_are_mutually_blind(tmp_path: Path) -> None:
    """Criterion 1: the *real* screener record, run as two arms.

    ``blinded_from`` is empty there, so sibling blinding cannot help: the arm
    exclusion must be derived from the role's own ``{arm}`` write slot.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)

    published_a: list[Path] = []

    def handler_a(session: RoleSession) -> None:
        published_a.append(
            session.write("batch_001_decisions.json", _decisions_blob("A"))
        )

    adapter.run(_screener_request("t-scr-ab", arm="A"), handler_a)
    assert published_a[0] == (
        workspace / "literature" / "screening" / "batch_001_decisions_A.json"
    )

    seen_b: list[str] = []
    b_reads: list[str] = []

    def handler_b(session: RoleSession) -> None:
        seen_b.extend(session.list())
        for path in (
            "literature/screening/batch_001_decisions_A.json",
            f"workspaces/{_WS}/literature/screening/batch_001_decisions_A.json",
        ):
            try:
                session.read(path)
                b_reads.append("READ")
            except ScopeViolation as exc:
                b_reads.append(exc.detail)

    adapter.run(_screener_request("t-scr-ab", arm="B"), handler_b)

    assert not any("batch_001_decisions_A.json" in entry for entry in seen_b), seen_b
    assert any(entry.endswith("literature/batch_001.json") for entry in seen_b)
    assert any(entry.endswith("protocol.json") for entry in seen_b)
    assert b_reads and all("not materialised" in detail for detail in b_reads), b_reads

    # Symmetric: arm B publishes, then arm A's view must hide it.
    adapter.run(
        _screener_request("t-scr-ba", arm="B"),
        lambda s: s.write("batch_001_decisions.json", _decisions_blob("B")),
    )
    seen_a: list[str] = []
    adapter.run(
        _screener_request("t-scr-ba", arm="A"),
        lambda s: seen_a.extend(s.list()),
    )
    assert not any("batch_001_decisions_B.json" in entry for entry in seen_a), seen_a
    assert any(entry.endswith("literature/batch_001.json") for entry in seen_a)
    assert any(entry.endswith("protocol.json") for entry in seen_a)


def test_solo_screener_view_still_sees_arm_tagged_artifacts(tmp_path: Path) -> None:
    """Criterion 2: ``arm=None`` gains no exclusions (blinding is dual-arm only).

    ``roles/screener.json`` declares ``isolation: redacted-input``, and
    ``Envelope@1`` requires an arm for any isolated role (api.py role
    compatibility: "arm is required when isolation is …"), so a *solo* run of
    that record is a typed refusal — asserted by
    :func:`test_solo_run_of_an_isolated_role_is_refused`. The criterion here is
    about the solo *view*, so the fixture runs a copy of the same record with
    ``isolation: none``: the only shape ``Envelope@1`` lets ``arm=None``
    describe.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    screening = workspace / "literature" / "screening"
    (screening / "batch_001_decisions_A.json").write_text(
        _decisions_blob("A"), encoding="utf-8"
    )
    roles = tmp_path / "roles"
    shutil.copytree(ROLES_DIR, roles)
    record = json.loads((roles / "screener.json").read_text(encoding="utf-8"))
    record["independence"]["isolation"] = "none"
    (roles / "screener.json").write_text(json.dumps(record), encoding="utf-8")
    adapter = InProcessAdapter(root=root, workspace=workspace, roles_dir=roles)
    seen: list[str] = []
    adapter.run(
        _screener_request("t-scr-solo", arm=None), lambda s: seen.extend(s.list())
    )
    assert any(entry.endswith("batch_001_decisions_A.json") for entry in seen), seen


def test_arm_request_binds_bare_tag_to_arm_destination(tmp_path: Path) -> None:
    """Criterion 3: arm B + a bare tag → ``…_decisions_B.json`` (no double name)."""
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    expected = workspace / "literature" / "screening" / "batch_001_decisions_B.json"

    promoted_bare: list[Path] = []
    adapter.run(
        _screener_request("t-bind-bare", arm="B"),
        lambda s: promoted_bare.append(
            s.write("batch_001_decisions.json", _decisions_blob("B"))
        ),
    )
    rel = promoted_bare[0].relative_to(root).as_posix()
    assert rel == f"workspaces/{_WS}/literature/screening/batch_001_decisions_B.json"
    assert "batch_001_decisions_batch_001_decisions" not in rel
    assert promoted_bare[0] == expected

    # The arm-tagged tag resolves to the same destination, not a second name.
    promoted_tagged: list[Path] = []
    adapter.run(
        _screener_request("t-bind-tagged", arm="B"),
        lambda s: promoted_tagged.append(
            s.write("batch_001_decisions_B.json", _decisions_blob("B"))
        ),
    )
    assert promoted_tagged[0] == expected

    # A different arm's tag is neither accepted nor promoted (no shared state).
    with pytest.raises(ScopeViolation):
        adapter.run(
            _screener_request("t-bind-cross", arm="B"),
            lambda s: s.write("batch_001_decisions_A.json", _decisions_blob("B")),
        )
    assert not (
        workspace / "literature" / "screening" / "batch_001_decisions_A.json"
    ).exists()


def test_unbound_arm_slot_refuses_and_writes_nothing(tmp_path: Path) -> None:
    """Criterion 4: no arm supplied → typed refusal naming ``{arm}``, no file."""
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    with pytest.raises(ScopeViolation) as excinfo:
        adapter.run(
            # No arm at all: the record's ``{arm}`` write slot cannot be bound,
            # and Envelope@1 requires an arm for an isolated role.
            _screener_request("t-no-arm", arm=None),
            lambda s: s.write("batch_001_decisions.json", _decisions_blob(None)),
        )
    detail = excinfo.value.detail
    assert "{arm}" in detail
    assert "screener" in detail
    assert not (
        workspace / "literature" / "screening" / "batch_001_decisions.json"
    ).exists()
    assert not list((workspace / "literature" / "screening").glob("*_decisions*"))


def test_opencode_arm_b_view_excludes_arm_a_artifact(tmp_path: Path) -> None:
    """Criterion 6: the dev adapter builds the same blinded view."""
    root, workspace = _seed_screener_workspace(tmp_path)
    app = _screener_adapter(root, workspace)
    app.run(
        _screener_request("t-dev-ab", arm="A"),
        lambda s: s.write("batch_001_decisions.json", _decisions_blob("A")),
    )
    dev = OpencodeAdapter(workspace=root, roles_dir=ROLES_DIR)
    seen: list[str] = []
    dev.run(_screener_request("t-dev-ab", arm="B"), lambda s: seen.extend(s.list()))
    assert not any("batch_001_decisions_A.json" in entry for entry in seen), seen
    assert any(entry.endswith("literature/batch_001.json") for entry in seen)
    hidden = (
        root
        / "runs"
        / "t-dev-ab"
        / "view"
        / "B"
        / "workspaces"
        / _WS
        / "literature"
        / "screening"
        / "batch_001_decisions_A.json"
    )
    assert not hidden.exists(), "arm A's artifact was materialised into arm B's view"


# ---------------------------------------------------------------------------
# Reviewer round 2: params-independent exclusion, one arm definition,
# sibling widening, and strict arm values.
# ---------------------------------------------------------------------------


def test_arm_exclusion_ignores_param_narrowing(tmp_path: Path) -> None:
    """Finding 1: a caller-bound ``{batch}`` must not narrow the exclusion."""
    root, workspace = _seed_screener_workspace(tmp_path)
    literature = workspace / "literature"
    (literature / "batch_002.json").write_text(
        json.dumps({"batch_id": "batch_002", "records": []}), encoding="utf-8"
    )
    adapter = _screener_adapter(root, workspace)
    for batch in ("batch_001", "batch_002"):
        adapter.run(
            RunRequest(
                task_id=f"t-narrow-{batch}",
                role_id="screener",
                role_version=SCREENER_ROLE_VERSION,
                inputs=SCREENER_INPUTS,
                params={"ws": _WS, "batch": batch},
                arm="A",
                input_schemas=SCREENER_INPUT_SCHEMAS,
            ),
            lambda s, name=batch: s.write(
                f"{name}_decisions.json", _decisions_blob("A")
            ),
        )
    screening = workspace / "literature" / "screening"
    assert (screening / "batch_001_decisions_A.json").is_file()
    assert (screening / "batch_002_decisions_A.json").is_file()

    seen: list[str] = []
    adapter.run(
        RunRequest(
            task_id="t-narrow-view",
            role_id="screener",
            role_version=SCREENER_ROLE_VERSION,
            inputs=SCREENER_INPUTS,
            # The caller narrowed ``{batch}`` to batch_001; the exclusion must
            # still cover batch_002's arm-A artifact.
            params={"ws": _WS, "batch": "batch_001"},
            arm="B",
            input_schemas=SCREENER_INPUT_SCHEMAS,
        ),
        lambda s: seen.extend(s.list()),
    )
    assert not any("batch_002_decisions_A.json" in entry for entry in seen), seen
    assert not any("batch_001_decisions_A.json" in entry for entry in seen), seen
    assert any(entry.endswith("literature/batch_001.json") for entry in seen)


def test_params_arm_is_the_same_arm_definition(tmp_path: Path) -> None:
    """Finding 3: ``params['arm']`` drives gate, view dir, exclusions, audit."""
    root, workspace = _seed_screener_workspace(tmp_path / "dual")
    adapter = _screener_adapter(root, workspace)

    promoted: list[Path] = []
    adapter.run(
        RunRequest(
            task_id="t-param-arm-a",
            role_id="screener",
            role_version=SCREENER_ROLE_VERSION,
            inputs=SCREENER_INPUTS,
            params={"ws": _WS, "arm": "A"},
            input_schemas=SCREENER_INPUT_SCHEMAS,
        ),
        lambda s: promoted.append(
            s.write("batch_001_decisions.json", _decisions_blob("A"))
        ),
    )
    assert promoted[0].name == "batch_001_decisions_A.json"
    assert (workspace / "runs" / "t-param-arm-a" / "view" / "A").is_dir(), (
        "a param-supplied arm must name the per-arm view directory"
    )
    journal = workspace / "audit" / "journal.jsonl"
    record = json.loads(journal.read_text(encoding="utf-8").splitlines()[-1])
    assert record["parameters"]["arm"] == "A"

    seen: list[str] = []
    adapter.run(
        RunRequest(
            task_id="t-param-arm-b",
            role_id="screener",
            role_version=SCREENER_ROLE_VERSION,
            inputs=SCREENER_INPUTS,
            params={"ws": _WS},
            arm="B",
            input_schemas=SCREENER_INPUT_SCHEMAS,
        ),
        lambda s: seen.extend(s.list()),
    )
    assert not any("decisions_A.json" in entry for entry in seen), seen

    # ``isolation: none`` cannot be bypassed through params['arm'] either.
    solo_root, solo_workspace = _seed_workspace(tmp_path / "solo")
    solo_adapter = _adapter(solo_root, solo_workspace)
    with pytest.raises(ScopeViolation) as excinfo:
        solo_adapter.run(
            RunRequest(
                task_id="t-param-arm-solo",
                role_id="solo-agent",
                role_version="2.1.0",
                inputs=(f"workspaces/{_WS}/literature/batch.json",),
                params={"ws": _WS, "arm": "A"},
            ),
            lambda s: None,
        )
    assert "isolation: none" in excinfo.value.detail
    assert "arm=A" in excinfo.value.detail


def test_blinded_from_screener_hides_arm_tagged_output(tmp_path: Path) -> None:
    """Finding 4: sibling blinding must widen a ``{arm}`` sibling row."""
    roles = tmp_path / "roles"
    shutil.copytree(ROLES_DIR, roles)
    blinded = {
        **AGENT_RECORD,
        "id": "screener-auditor",
        "independence": {
            "blinded_from": ["screener"],
            "isolation": "redacted-input",
        },
        "read_glob": ["workspaces/{ws}/literature/**"],
        "outputs": [
            {
                "schema": "Review@1",
                "write_glob": "workspaces/{ws}/critique/screening/{batch}.json",
            }
        ],
    }
    (roles / "screener-auditor.json").write_text(json.dumps(blinded), encoding="utf-8")
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = InProcessAdapter(root=root, workspace=workspace, roles_dir=roles)
    adapter.run(
        _screener_request("t-blind-source", arm="A"),
        lambda s: s.write("batch_001_decisions.json", _decisions_blob("A")),
    )
    screening = workspace / "literature" / "screening"
    assert (screening / "batch_001_decisions_A.json").is_file()

    seen: list[str] = []
    adapter.run(
        RunRequest(
            task_id="t-blind-viewer",
            role_id="screener-auditor",
            role_version="2.1.0",
            inputs=(f"workspaces/{_WS}/literature/batch_001.json",),
            params={"ws": _WS},
            arm="A",
        ),
        lambda s: seen.extend(s.list()),
    )
    assert not any("decisions_A.json" in entry for entry in seen), seen
    assert any(entry.endswith("literature/batch_001.json") for entry in seen)


def test_empty_or_blank_arm_is_refused(tmp_path: Path) -> None:
    """Finding 5: only ``None`` is solo; empty/blank arms are refused."""
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    inputs = (f"workspaces/{_WS}/literature/batch_001.json",)
    cases = [
        (
            RunRequest(
                "t-arm-empty",
                "screener",
                SCREENER_ROLE_VERSION,
                inputs,
                {"ws": _WS},
                arm="",
            ),
            "RunRequest.arm",
        ),
        (
            RunRequest(
                "t-arm-blank",
                "screener",
                SCREENER_ROLE_VERSION,
                inputs,
                {"ws": _WS},
                arm="   ",
            ),
            "RunRequest.arm",
        ),
        (
            RunRequest(
                "t-arm-empty-param",
                "screener",
                SCREENER_ROLE_VERSION,
                inputs,
                {"ws": _WS, "arm": ""},
            ),
            "params['arm']",
        ),
        (
            RunRequest(
                "t-arm-blank-param",
                "screener",
                SCREENER_ROLE_VERSION,
                inputs,
                {"ws": _WS, "arm": "  "},
            ),
            "params['arm']",
        ),
    ]
    for request, field in cases:
        with pytest.raises(ScopeViolation) as excinfo:
            adapter.run(
                request,
                lambda s: s.write("batch_001_decisions.json", _decisions_blob("A")),
            )
        assert field in excinfo.value.detail
    assert not (workspace / "runs").exists()
    assert not list((workspace / "literature" / "screening").glob("*_decisions*"))


# ---------------------------------------------------------------------------
# Reviewer round 3: run labels are path segments; blinding fails closed.
# ---------------------------------------------------------------------------


def test_unsafe_arm_labels_are_refused_before_removal(tmp_path: Path) -> None:
    """Arm values reach ``view/{arm}``; unsafe labels never reach rmtree."""
    root, workspace = _seed_screener_workspace(tmp_path)
    precious = workspace / "runs" / "victim" / "precious.txt"
    precious.parent.mkdir(parents=True)
    precious.write_text("keep me", encoding="utf-8")
    adapter = _screener_adapter(root, workspace)
    for arm in ("../../victim", "A|B", "A:stream"):
        with pytest.raises(ScopeViolation) as excinfo:
            adapter.run(
                RunRequest(
                    task_id="t-arm-label",
                    role_id="screener",
                    role_version=SCREENER_ROLE_VERSION,
                    inputs=(f"workspaces/{_WS}/literature/batch_001.json",),
                    params={"ws": _WS},
                    arm=arm,
                ),
                lambda s: None,
            )
        assert "RunRequest.arm" in excinfo.value.detail
        assert arm in excinfo.value.detail
        assert precious.is_file(), f"arm={arm!r} reached the view directory"
    assert not (workspace / "runs" / "t-arm-label").exists()


def test_unsafe_task_ids_are_refused_before_directory_creation(
    tmp_path: Path,
) -> None:
    """``task_id`` reaches ``runs/{task_id}``; unsafe labels create nothing."""
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    for task_id in ("../victim", "a/b", ".."):
        with pytest.raises(ScopeViolation) as excinfo:
            adapter.run(
                RunRequest(
                    task_id=task_id,
                    role_id="screener",
                    role_version=SCREENER_ROLE_VERSION,
                    inputs=(f"workspaces/{_WS}/literature/batch_001.json",),
                    params={"ws": _WS},
                ),
                lambda s: None,
            )
        assert "RunRequest.task_id" in excinfo.value.detail
        assert task_id in excinfo.value.detail
    assert not (workspace / "runs").exists()


def test_missing_blinded_sibling_fails_closed(tmp_path: Path) -> None:
    """A misspelled ``blinded_from`` name must not yield an unblinded view."""
    root, workspace = _seed_workspace(tmp_path)
    record = {
        **AGENT_RECORD,
        "id": "ghost-blinded",
        "independence": {
            "blinded_from": ["no-such-sibling"],
            "isolation": "redacted-input",
        },
    }
    (root / "roles" / "ghost-blinded.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    adapter = _adapter(root, workspace)
    with pytest.raises(ScopeViolation) as excinfo:
        adapter.run(
            RunRequest(
                task_id="t-ghost",
                role_id="ghost-blinded",
                role_version="2.1.0",
                inputs=(f"workspaces/{_WS}/literature/batch.json",),
                params=PARAMS,
                arm="A",
            ),
            lambda s: None,
        )
    assert "no-such-sibling" in excinfo.value.detail
    assert not (workspace / "runs" / "t-ghost" / "view").exists()
    # Reviewer residual: the refusal must not leave an empty staging dir.
    assert not (workspace / "runs" / "t-ghost" / "out").exists()


def test_valid_arm_and_task_labels_still_run(tmp_path: Path) -> None:
    """The label gate accepts ordinary run labels unchanged."""
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    promoted: list[Path] = []
    adapter.run(
        RunRequest(
            task_id="t-dual",
            role_id="screener",
            role_version=SCREENER_ROLE_VERSION,
            inputs=SCREENER_INPUTS,
            params={"ws": _WS},
            arm="B",
            input_schemas=SCREENER_INPUT_SCHEMAS,
        ),
        lambda s: promoted.append(
            s.write("batch_001_decisions.json", _decisions_blob("B"))
        ),
    )
    assert promoted[0].name == "batch_001_decisions_B.json"
    assert (workspace / "runs" / "t-dual" / "view" / "B").is_dir()


# ---------------------------------------------------------------------------
# T-ALP-E3E5: egress (E-3), canonical audit attribution (E-5), narrow
# redaction (F8), staging cleanup, and the Envelope@1 arm vocabulary.
# ---------------------------------------------------------------------------

_EVENT_ID_RE = re.compile(r"^EVT-\d{14}-[0-9a-f]{6}$")
_REDACTED_FIELDS = (
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
)


def _resolver_calls() -> list[tuple[str, object]]:
    """Every name-resolution/socket entry point the deny guard must cover."""
    return [
        ("getaddrinfo", lambda: socket.getaddrinfo("example.com", 80)),
        ("gethostbyname", lambda: socket.gethostbyname("example.com")),
        ("gethostbyname_ex", lambda: socket.gethostbyname_ex("example.com")),
        ("gethostbyaddr", lambda: socket.gethostbyaddr("127.0.0.1")),
        ("getnameinfo", lambda: socket.getnameinfo(("127.0.0.1", 80), 0)),
        ("create_connection", lambda: socket.create_connection(("127.0.0.1", 59999))),
        ("socket", lambda: socket.socket(socket.AF_INET, socket.SOCK_STREAM)),
        (
            "SocketType",
            lambda: socket.SocketType(socket.AF_INET, socket.SOCK_STREAM),
        ),
    ]


def test_deny_refuses_resolver_and_socket_entrypoints(tmp_path: Path) -> None:
    """Criterion 1 / E-3: ``deny`` means *no* sockets — DNS included.

    Pre-packet the guard patched only ``socket.socket``/``create_connection``,
    so every resolver call answered ``DNS-REACHED``.
    """
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    refused: dict[str, str] = {}

    def handler(session: RoleSession) -> None:
        with session.egress_guard():
            for name, call in _resolver_calls():
                try:
                    call()  # type: ignore[operator]
                except EgressRefused as exc:
                    refused[name] = exc.detail
                else:  # pragma: no cover — a reached syscall is the defect
                    refused[name] = "REACHED"

    adapter.run(_request(), handler)
    assert set(refused) == {name for name, _ in _resolver_calls()}
    for name, outcome in refused.items():
        assert outcome != "REACHED", f"{name} escaped the deny guard"
        assert "network policy is deny" in outcome

    # Under allow the same entry points reach the real implementation.
    allowed = dict(AGENT_RECORD, network="allow", id="allow-entrypoints")
    (root / "roles" / "allow-entrypoints.json").write_text(
        json.dumps(allowed), encoding="utf-8"
    )
    observed: dict[str, object] = {}

    def allow_handler(session: RoleSession) -> None:
        with session.egress_guard():
            observed["getaddrinfo"] = socket.getaddrinfo("localhost", 80)
            observed["gethostbyname"] = socket.gethostbyname("localhost")
            observed["gethostbyname_ex"] = socket.gethostbyname_ex("localhost")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.close()
            observed["socket"] = "OPENED"
            alias_sock = socket.SocketType(socket.AF_INET, socket.SOCK_STREAM)
            alias_sock.close()
            observed["SocketType"] = "OPENED"
            try:
                socket.getnameinfo(("127.0.0.1", 80), 0)
                observed["getnameinfo"] = "RESOLVED"
            except EgressRefused as exc:  # pragma: no cover — the defect
                observed["getnameinfo"] = f"EGRESS: {exc}"
            except OSError:
                observed["getnameinfo"] = "SYSCALL_REACHED"
            try:
                socket.create_connection(("127.0.0.1", 59999), timeout=0.05)
            except EgressRefused as exc:  # pragma: no cover — the defect
                observed["create_connection"] = f"EGRESS: {exc}"
            except OSError:
                observed["create_connection"] = "SYSCALL_REACHED"
            try:
                socket.gethostbyaddr("127.0.0.1")
                observed["gethostbyaddr"] = "RESOLVED"
            except OSError:  # reverse DNS may be unavailable; it must not be EGRESS
                observed["gethostbyaddr"] = "SYSCALL_REACHED"

    adapter.run(_request(role="allow-entrypoints"), allow_handler)
    assert observed["getaddrinfo"]
    assert observed["gethostbyname"]
    assert observed["gethostbyname_ex"]
    assert observed["socket"] == "OPENED"
    assert observed["SocketType"] == "OPENED"
    assert observed["getnameinfo"] in {"RESOLVED", "SYSCALL_REACHED"}
    assert observed["create_connection"] == "SYSCALL_REACHED"
    assert observed["gethostbyaddr"] in {"RESOLVED", "SYSCALL_REACHED"}


def test_deny_is_per_thread_not_process_global(tmp_path: Path) -> None:
    """Criterion 2: an ``allow`` thread resolves while another thread denies.

    Pre-packet the patch was a process-global ``socket.socket`` replacement,
    so the allow thread's socket construction was refused too.
    """
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    entered = threading.Event()
    release = threading.Event()
    failures: list[BaseException] = []

    def deny_handler(session: RoleSession) -> None:
        with session.egress_guard():
            entered.set()
            assert release.wait(timeout=10), "allow thread never released deny guard"
            with pytest.raises(EgressRefused):
                socket.getaddrinfo("example.com", 80)

    def deny_thread() -> None:
        try:
            adapter.run(_request(), deny_handler)
        except Exception as exc:  # noqa: BLE001 — surfaced below
            failures.append(exc)

    worker = threading.Thread(target=deny_thread)
    worker.start()
    try:
        assert entered.wait(timeout=10), "deny guard never installed"
        infos = socket.getaddrinfo("localhost", 80)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.close()
    finally:
        release.set()
        worker.join(timeout=10)
    assert not failures, failures
    assert infos, "the allow thread must resolve while the deny guard is active"
    assert worker.is_alive() is False


def test_nested_deny_guards_restore_and_allow_resolves(tmp_path: Path) -> None:
    """Criterion 3: nested guards keep deny, then restore to allow."""
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    outcomes: list[str] = []

    def handler(session: RoleSession) -> None:
        with session.egress_guard():
            with session.egress_guard():
                try:
                    socket.getaddrinfo("example.com", 80)
                except EgressRefused:
                    outcomes.append("INNER_REFUSED")
            try:
                socket.getaddrinfo("example.com", 80)
            except EgressRefused:
                outcomes.append("OUTER_REFUSED")

    adapter.run(_request(), handler)
    # The adapter's own outer guard is still active after the nested exits;
    # only leaving the run restores the process-wide entry points.
    assert outcomes == ["INNER_REFUSED", "OUTER_REFUSED"]
    assert socket.getaddrinfo("localhost", 80)


def test_real_screener_journal_uses_canonical_writer(tmp_path: Path) -> None:
    """Criterion 4 / E-5: the row is canonical, attributed, and hash-stamped."""
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)

    promoted: list[Path] = []
    adapter.run(
        _screener_request("t-journal", arm="A"),
        lambda s: promoted.append(
            s.write(
                "batch_001_decisions.json",
                json.dumps(_valid_decisions_payload("A")),
            )
        ),
    )
    journal = workspace / "audit" / "journal.jsonl"
    record = json.loads(journal.read_text(encoding="utf-8").splitlines()[-1])

    assert _EVENT_ID_RE.fullmatch(record["event_id"]), record["event_id"]
    assert record["action"] == "SCREENING_COMPLETED"
    assert record["action"] != "SCREENER_RUN"
    assert record["status"] == "SUCCESS"
    assert record["agent_or_tool"] == "screener@2.0.0"
    assert record["parameters"]["role_version"] == SCREENER_ROLE_VERSION
    assert record["parameters"]["task_id"] == "t-journal"
    assert record["parameters"]["arm"] == "A"
    assert record["parameters"]["isolation"] == "redacted-input"
    assert record["parameters"]["adapter"] == "in-process"
    assert record["parameters"]["adapter_version"] == "1.0.0"
    assert record["metrics"]["input_sha256"] == [
        hashlib.sha256(
            (workspace / "literature" / "batch_001.json").read_bytes()
        ).hexdigest(),
        hashlib.sha256((workspace / "protocol.json").read_bytes()).hexdigest(),
        hashlib.sha256((workspace / "SCREENING_CRITERIA.md").read_bytes()).hexdigest(),
    ]
    assert record["metrics"]["output_sha256"] == [
        hashlib.sha256(promoted[0].read_bytes()).hexdigest()
    ]
    assert isinstance(record["metrics"]["duration_ms"], int)
    assert "provenance" not in record


def test_opencode_emit_labels_its_own_writer(tmp_path: Path) -> None:
    """Criterion 5: ``OpencodeAdapter.emit`` is never labelled in-process."""
    root, workspace = _seed_workspace(tmp_path)
    dev = OpencodeAdapter(workspace=workspace, roles_dir=root / "roles")
    dev.emit(
        AuditEvent(
            action="REVIEW_COMPLETED",
            actor="conform-reviewer@2.1.0",
            role_version="2.1.0",
            description="dev-loop review",
            task_id="t-dev-emit",
            adapter="in-process",  # caller-supplied label must not win
            adapter_version="1.0.0",
        )
    )
    record = json.loads(
        (workspace / "audit" / "journal.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[-1]
    )
    assert record["parameters"]["adapter"] == "opencode"
    assert record["parameters"]["adapter_version"] == "1.0.0"
    assert record["agent_or_tool"] == "conform-reviewer@2.1.0"


def test_same_second_events_have_distinct_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Criterion 6: the canonical writer mints unique ids, not a truncated ts."""
    from scholar_harness.workspace import audit as audit_module

    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 1, 1, 1, 1, 1, tzinfo=UTC)

    monkeypatch.setattr(audit_module, "datetime", _FrozenDatetime)
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    for _ in range(2):
        adapter.emit(
            AuditEvent(
                action="REVIEW_COMPLETED",
                actor="conform-reviewer@2.1.0",
                role_version="2.1.0",
                description="same wall clock second",
                task_id="t-same-second",
            )
        )
    rows = [
        json.loads(line)
        for line in (workspace / "audit" / "journal.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert len(rows) == 2
    for row in rows:
        assert _EVENT_ID_RE.fullmatch(row["event_id"]), row["event_id"]
        assert row["event_id"].startswith("EVT-20260101010101-")
    assert rows[0]["event_id"] != rows[1]["event_id"]


def test_role_without_declared_audit_actions_is_refused(tmp_path: Path) -> None:
    """Criterion 7: no invented verb — policy load refuses an empty ``emit``."""
    root, workspace = _seed_screener_workspace(tmp_path)
    record = {
        **AGENT_RECORD,
        "id": "silent-role",
        "audit": {"actor": "{role}@{version}"},  # no "emit"
    }
    (root / "roles").mkdir(parents=True, exist_ok=True)
    (root / "roles" / "silent-role.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    adapter = InProcessAdapter(root=root, workspace=workspace, roles_dir=root / "roles")
    with pytest.raises(ScopeViolation) as excinfo:
        adapter.run(
            RunRequest(
                task_id="t-silent",
                role_id="silent-role",
                role_version="2.1.0",
                inputs=(f"workspaces/{_WS}/literature/batch_001.json",),
                params={"ws": _WS},
            ),
            lambda s: None,
        )
    assert "declares no audit actions" in excinfo.value.detail
    assert not (workspace / "runs").exists()


def test_redacted_input_hides_the_whole_citation_fingerprint(tmp_path: Path) -> None:
    """Criterion 8 / F8: DOI/URL/venue/year cannot re-identify a blind record."""
    root, workspace = _seed_screener_workspace(tmp_path)
    payload = {
        "screening_id": "SCR-000001",
        "decision": "include",
        "title": "Unmistakable Title",
        "authors": ["Doe, J."],
        "abstract": "Unmistakable abstract.",
        "doi": "10.1234/unmistakable",
        "url": "https://example.org/unmistakable",
        "venue": "Unmistakable Venue",
        "journal": "Unmistakable Journal",
        "year": 2024,
        "publication_date": "2024-01-01",
        "publisher": "Unmistakable Press",
        "affiliations": ["Unmistakable University"],
    }
    (workspace / "literature" / "batch_001.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    adapter = _screener_adapter(root, workspace)
    seen: list[dict[str, object]] = []

    def handler(session: RoleSession) -> None:
        seen.append(
            json.loads(session.read(f"workspaces/{_WS}/literature/batch_001.json"))
        )

    adapter.run(_screener_request("t-redact"), handler)
    redacted = seen[0]
    for field in _REDACTED_FIELDS:
        assert redacted[field] == "[REDACTED]", field
    assert redacted["screening_id"] == "SCR-000001"
    assert redacted["decision"] == "include"
    # The raw values never survive anywhere in the view payload.
    blob = json.dumps(redacted)
    assert "unmistakable" not in blob.lower()


def test_arm_vocabulary_is_exactly_a_or_b(tmp_path: Path) -> None:
    """Criterion 10: Envelope@1's ``arm`` literal rejects aliases."""
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    inputs = SCREENER_INPUTS
    cases = [
        (
            RunRequest(
                "t-arm-lower",
                "screener",
                SCREENER_ROLE_VERSION,
                inputs,
                {"ws": _WS},
                arm="a",
                input_schemas=SCREENER_INPUT_SCHEMAS,
            ),
            "RunRequest.arm",
        ),
        (
            RunRequest(
                "t-arm-c",
                "screener",
                SCREENER_ROLE_VERSION,
                inputs,
                {"ws": _WS},
                arm="C",
                input_schemas=SCREENER_INPUT_SCHEMAS,
            ),
            "RunRequest.arm",
        ),
        (
            RunRequest(
                "t-arm-param-lower",
                "screener",
                SCREENER_ROLE_VERSION,
                inputs,
                {"ws": _WS, "arm": "a"},
                input_schemas=SCREENER_INPUT_SCHEMAS,
            ),
            "params['arm']",
        ),
    ]
    for request, field in cases:
        with pytest.raises(ScopeViolation) as excinfo:
            adapter.run(request, lambda s: None)
        detail = excinfo.value.detail
        assert field in detail
        assert "Envelope@1" in detail
        refused_arm = request.arm if request.arm is not None else request.params["arm"]
        assert refused_arm in detail
    assert not (workspace / "runs").exists()

    # The declared vocabulary still runs, and names its own view dir.
    for arm in ("A", "B"):
        adapter.run(
            RunRequest(
                task_id=f"t-arm-ok-{arm}",
                role_id="screener",
                role_version=SCREENER_ROLE_VERSION,
                inputs=inputs,
                params={"ws": _WS},
                arm=arm,
                input_schemas=SCREENER_INPUT_SCHEMAS,
            ),
            lambda s: None,
        )
        assert (workspace / "runs" / f"t-arm-ok-{arm}" / "view" / arm).is_dir()


# ---------------------------------------------------------------------------
# T-ALP-E3E5 round 2: version pinning, task_id provenance, dev-loop audit,
# additive redaction, and sibling-only roles.
# ---------------------------------------------------------------------------


def test_role_version_mismatch_is_refused(tmp_path: Path) -> None:
    """P2: the request cannot stamp a version the role record does not declare."""
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    with pytest.raises(ScopeViolation) as excinfo:
        adapter.run(
            RunRequest(
                task_id="t-version-mismatch",
                role_id="screener",
                role_version="9.9.9",
                inputs=(f"workspaces/{_WS}/literature/batch_001.json",),
                params=PARAMS,
            ),
            lambda s: None,
        )
    detail = excinfo.value.detail
    assert "9.9.9" in detail
    assert SCREENER_ROLE_VERSION in detail
    assert not (workspace / "runs").exists()


def test_blank_task_id_is_refused_by_append_journal(tmp_path: Path) -> None:
    """P4: provenance that cannot name its run is not written."""
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    with pytest.raises(ScopeViolation) as excinfo:
        adapter.emit(
            AuditEvent(
                action="REVIEW_COMPLETED",
                actor="conform-reviewer@2.1.0",
                role_version="2.1.0",
                description="blank run id",
                task_id="   ",
            )
        )
    assert "blank task_id" in excinfo.value.detail
    assert not (workspace / "audit" / "journal.jsonl").exists()


def test_opencode_run_writes_canonical_journal_row(tmp_path: Path) -> None:
    """P5: the dev adapter writes one canonical row after a successful run."""
    root, workspace = _seed_screener_workspace(tmp_path)
    dev = OpencodeAdapter(workspace=root, roles_dir=ROLES_DIR)
    promoted: list[Path] = []
    dev.run(
        _screener_request("t-dev-run", arm="A"),
        lambda s: promoted.append(
            s.write(
                "batch_001_decisions.json",
                json.dumps(_valid_decisions_payload("A")),
            )
        ),
    )
    assert promoted[0] == (
        workspace / "literature" / "screening" / "batch_001_decisions_A.json"
    )
    record = json.loads(
        (root / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()[-1]
    )
    assert record["action"] == "SCREENING_COMPLETED"
    assert record["agent_or_tool"] == "screener@2.0.0"
    assert record["parameters"]["adapter"] == "opencode"
    assert record["parameters"]["role_version"] == SCREENER_ROLE_VERSION
    assert record["parameters"]["task_id"] == "t-dev-run"
    assert record["metrics"]["output_sha256"] == [
        hashlib.sha256(promoted[0].read_bytes()).hexdigest()
    ]
    assert record["metrics"]["input_sha256"] == [
        hashlib.sha256(
            (workspace / "literature" / "batch_001.json").read_bytes()
        ).hexdigest(),
        hashlib.sha256((workspace / "protocol.json").read_bytes()).hexdigest(),
        hashlib.sha256((workspace / "SCREENING_CRITERIA.md").read_bytes()).hexdigest(),
    ]


def test_redaction_is_additive_case_insensitive_and_recursive(
    tmp_path: Path,
) -> None:
    """P6: defaults | role fields | explicit seam; nested keys match lowercased."""
    roles = tmp_path / "roles"
    shutil.copytree(ROLES_DIR, roles)
    screener_path = roles / "screener.json"
    record = json.loads(screener_path.read_text(encoding="utf-8"))
    # A role may only *add*: mixed-case "Title" must not drop the DOI default.
    record["independence"]["redacted_fields"] = ["Title"]
    screener_path.write_text(json.dumps(record), encoding="utf-8")

    root, workspace = _seed_screener_workspace(tmp_path)
    payload = {
        "screening_id": "SCR-000002",
        "decision": "exclude",
        "title": "Identifiable",
        "doi": "10.1234/identifiable",
        "custom_secret": "seam-only",
        "nested": {"title": "Deep title", "keep": "visible"},
        "records": [{"doi": "10.1234/deep", "custom_secret": "deep-secret", "keep": 1}],
    }
    (workspace / "literature" / "batch_001.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    adapter = InProcessAdapter(
        root=root,
        workspace=workspace,
        roles_dir=roles,
        redacted_fields=frozenset({"CUSTOM_SECRET"}),
    )
    seen: list[dict[str, object]] = []

    def handler(session: RoleSession) -> None:
        seen.append(
            json.loads(session.read(f"workspaces/{_WS}/literature/batch_001.json"))
        )

    adapter.run(_screener_request("t-additive-redaction"), handler)
    data = seen[0]
    assert data["title"] == "[REDACTED]"
    assert data["doi"] == "[REDACTED]"  # default survives a role override
    assert data["custom_secret"] == "[REDACTED]"  # explicit seam adds
    assert data["nested"] == {"title": "[REDACTED]", "keep": "visible"}
    assert data["records"] == [
        {"doi": "[REDACTED]", "custom_secret": "[REDACTED]", "keep": 1}
    ]
    assert data["screening_id"] == "SCR-000002"
    assert data["decision"] == "exclude"


def test_blinding_sibling_need_not_declare_audit(tmp_path: Path) -> None:
    """P8: a role with no ``emit`` can blind a view but still cannot run."""
    root, workspace = _seed_workspace(tmp_path)
    roles = root / "roles"
    ghost = {
        **AGENT_RECORD,
        "id": "ghost-source",
        "audit": {"actor": "{role}@{version}"},  # no "emit"
        "outputs": [
            {
                "schema": "Review@1",
                "write_glob": "workspaces/{ws}/critique/ghost.json",
            }
        ],
    }
    viewer = {
        **AGENT_RECORD,
        "id": "ghost-viewer",
        "independence": {
            "blinded_from": ["ghost-source"],
            "isolation": "redacted-input",
        },
        "read_glob": [
            "workspaces/{ws}/literature/**",
            "workspaces/{ws}/critique/**",
        ],
    }
    (roles / "ghost-source.json").write_text(json.dumps(ghost), encoding="utf-8")
    (roles / "ghost-viewer.json").write_text(json.dumps(viewer), encoding="utf-8")
    critique = workspace / "critique"
    critique.mkdir()
    (critique / "ghost.json").write_text(
        json.dumps({"secret": "ghost output"}), encoding="utf-8"
    )
    adapter = _adapter(root, workspace)

    seen: list[str] = []
    adapter.run(
        _request(role="ghost-viewer", task="t-ghost-sibling"),
        lambda s: seen.extend(s.list()),
    )
    assert any(entry.endswith("literature/batch.json") for entry in seen), seen
    assert not any(entry.endswith("critique/ghost.json") for entry in seen), seen

    # Running the sibling itself is still refused at policy load.
    with pytest.raises(ScopeViolation) as excinfo:
        adapter.run(
            _request(role="ghost-source", task="t-ghost-direct"),
            lambda s: None,
        )
    assert "declares no audit actions" in excinfo.value.detail


# ---------------------------------------------------------------------------
# T-ALP-E4: Envelope@1 wiring, typed input refusals, and adapter dispatch.
# ---------------------------------------------------------------------------

_ENVELOPE_ID_RE = re.compile(r"^ENV-[0-9a-f]{16}$")
_SHA256_TEXT = "sha256:" + "a" * 64


def _valid_decisions_payload(arm: str = "A") -> dict[str, object]:
    """A contract-valid ``ScreeningDecisions@1`` payload (models.py read)."""
    return {
        "binding": {
            "screening_run_id": "RUN-000001",
            "protocol_fingerprint": _SHA256_TEXT,
            "corpus_fingerprint": "sha256:" + "b" * 64,
            "criteria_renderer_version": "1.0.0",
            "dedup_configuration_hash": "sha256:" + "c" * 64,
            "preparation_run_id": "RUN-000002",
        },
        "batch_id": "batch_001",
        "decisions": [
            {
                "decision_id": "SCR-000001",
                "study_id": "SCI-000001",
                "screener_id": f"screener-{arm}",
                "method": "LLM",
                "decision": "INCLUDE",
                "reason": "Meets the protocol criteria",
                "decided_at": "2026-10-28T00:00:00Z",
            }
        ],
    }


def _ok_envelope(
    tmp_path: Path, *, task: str = "t-env-ok", arm: str = "A"
) -> tuple[Envelope, Path, Path, InProcessAdapter]:
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    payload = json.dumps(_valid_decisions_payload(arm))
    envelope = adapter.run(
        _screener_request(task, arm=arm),
        lambda s: s.write("batch_001_decisions.json", payload),
    )
    return envelope, root, workspace, adapter


def test_run_returns_valid_ok_envelope_for_real_screener(tmp_path: Path) -> None:
    """Criterion 1: the real screener + a valid payload is a validated OK."""
    envelope, _root, _workspace, _adapter = _ok_envelope(tmp_path)

    assert isinstance(envelope, Envelope)
    assert envelope is not None, "run() must never return None on success"
    assert envelope.status is EnvelopeStatus.OK
    assert envelope.arm == "A"
    assert _ENVELOPE_ID_RE.fullmatch(envelope.envelope_id), envelope.envelope_id
    assert envelope.output is not None
    assert envelope.output.schema_ == "ScreeningDecisions@1"
    assert envelope.coverage is not None
    assert envelope.coverage.produced == envelope.coverage.expected == 1
    assert envelope.coverage.unit == "artifact"
    assert (
        envelope.output_sha256
        == hashlib.sha256(canonical_json_bytes(envelope.output.data)).hexdigest()
    )
    assert envelope.provenance.adapter == "in-process"
    assert envelope.provenance.isolation == "redacted-input"
    assert envelope.refusal is None
    assert validate(envelope.model_dump(by_alias=True), roles_dir=ROLES_DIR) == envelope


def test_schema_invalid_payload_is_invalid_output_with_findings(
    tmp_path: Path,
) -> None:
    """Criterion 2 + F2: a minimal blob is INVALID_OUTPUT, not a coerced OK.

    ``ScreeningDecisions@1`` is declared by ``roles/screener.json`` and
    registered in ``PAYLOAD_MODELS``, so the contract can name the failing
    payload and the adapter retains it — the same shape the frozen fixture
    ``tests/conformance/fixtures/envelope/invalid_output.json`` ships. The hash
    comes from the contract's own ``output_sha256`` helper, so the contract's
    hash step agrees by construction.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    blob = _decisions_blob("A")
    envelope = adapter.run(
        _screener_request("t-env-invalid", arm="A"),
        lambda s: s.write("batch_001_decisions.json", blob),
    )

    assert envelope.status is EnvelopeStatus.INVALID_OUTPUT
    assert envelope.refusal is not None
    assert envelope.refusal.code == "INVALID_OUTPUT"
    assert envelope.refusal.validation_findings
    assert any(
        "batch_001_decisions_A.json" in finding
        for finding in envelope.refusal.validation_findings
    ), envelope.refusal.validation_findings
    assert any(
        "Contract v1 schema" in finding
        for finding in envelope.refusal.validation_findings
    ), envelope.refusal.validation_findings
    # F2: the failing payload is retained for forensics (spec 02 §3).
    assert envelope.output is not None
    assert envelope.output.schema_ == "ScreeningDecisions@1"
    assert envelope.output.data == json.loads(blob)
    assert envelope.output_sha256 == contract_output_sha256(
        {"output": {"schema": "ScreeningDecisions@1", "data": envelope.output.data}}
    )
    assert envelope.coverage is None
    assert envelope.inputs == []
    assert validate(envelope.model_dump(by_alias=True), roles_dir=ROLES_DIR) == envelope

    # F3 re-check: this is a *returned* INVALID_OUTPUT, not a construction
    # failure, so the promoted artifact must survive (only a contract failure
    # rolls back a run).
    assert (
        workspace / "literature" / "screening" / "batch_001_decisions_A.json"
    ).is_file()

    # The retention encoding is not a private dialect: the shipped CLI agrees.
    from scholar_harness.contracts.envelope.cli import main as envelope_cli

    path = tmp_path / "invalid-envelope.json"
    path.write_text(
        json.dumps(envelope.model_dump(mode="json", by_alias=True), indent=2),
        encoding="utf-8",
    )
    assert envelope_cli(["validate", str(path), "--roles-dir", str(ROLES_DIR)]) == 0


def test_zero_artifact_run_is_invalid_output_not_ok(tmp_path: Path) -> None:
    """Negative: a handler that writes nothing cannot be an empty success."""
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    envelope = adapter.run(_screener_request("t-env-empty", arm="A"), lambda s: None)

    assert envelope.status is EnvelopeStatus.INVALID_OUTPUT
    assert envelope.refusal is not None
    assert envelope.refusal.code == "INVALID_OUTPUT"
    assert envelope.refusal.validation_findings == [
        "no artifact promoted by the handler"
    ]
    assert envelope.output is None
    assert validate(envelope.model_dump(by_alias=True), roles_dir=ROLES_DIR) == envelope


def test_opencode_run_returns_envelope_with_its_own_adapter_label(
    tmp_path: Path,
) -> None:
    """Criterion 3: the dev surface returns the same validated shape."""
    root, _workspace = _seed_screener_workspace(tmp_path)
    dev = OpencodeAdapter(workspace=root, roles_dir=ROLES_DIR)
    envelope = dev.run(
        _screener_request("t-oc-env", arm="A"),
        lambda s: s.write(
            "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
        ),
    )

    assert isinstance(envelope, Envelope)
    assert envelope.status is EnvelopeStatus.OK
    assert envelope.arm == "A"
    assert envelope.provenance.adapter == "opencode"
    assert envelope.output is not None
    assert envelope.output.schema_ == "ScreeningDecisions@1"
    assert validate(envelope.model_dump(by_alias=True), roles_dir=ROLES_DIR) == envelope


def test_envelope_id_is_deterministic_and_timing_free(tmp_path: Path) -> None:
    """Criterion 4: identity follows inputs/payload, never wall time."""
    first, _root, workspace, adapter = _ok_envelope(tmp_path, task="t-env-det")

    second = adapter.run(
        _screener_request("t-env-det", arm="A"),
        lambda s: s.write(
            "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
        ),
    )
    assert second.envelope_id == first.envelope_id

    input_path = workspace / "literature" / "batch_001.json"
    original = input_path.read_bytes()
    mutated = original.replace(b"Alpha", b"Alph4")
    assert mutated != original
    input_path.write_bytes(mutated)
    third = adapter.run(
        _screener_request("t-env-det", arm="A"),
        lambda s: s.write(
            "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
        ),
    )
    assert third.envelope_id != first.envelope_id

    timing_changed = first.model_copy(
        update={
            "created_at": datetime(2000, 1, 1, tzinfo=UTC),
            "provenance": first.provenance.model_copy(update={"duration_ms": 987654}),
        }
    )
    timing_changed = timing_changed.model_copy(
        update={"envelope_id": envelope_id(timing_changed)}
    )
    assert timing_changed.envelope_id == first.envelope_id
    assert validate(timing_changed.model_dump(by_alias=True), roles_dir=ROLES_DIR) == (
        timing_changed
    )


def test_scope_violation_materialises_a_validated_refused_envelope() -> None:
    """Criterion 5: the refusal state is renderable, not a stack trace."""
    request = _screener_request("t-refused-env", arm="A")
    policy = run_request_policy(ROLES_DIR, request)
    refusal = ScopeViolation("write 'evil.json': outside write_glob [deny]")
    envelope = refusal.envelope(
        request,
        policy,
        adapter="in-process",
        adapter_version="1.0.0",
        roles_dir=ROLES_DIR,
        duration_ms=7,
    )

    assert envelope.status is EnvelopeStatus.REFUSED
    assert envelope.refusal is not None
    assert envelope.refusal.code == "SCOPE_VIOLATION"
    assert envelope.refusal.detail == refusal.detail
    assert envelope.retryable is False
    assert envelope.output is None
    assert envelope.output_sha256 is None
    assert validate(envelope.model_dump(by_alias=True), roles_dir=ROLES_DIR) == envelope


def test_outside_root_inputs_are_typed_refusals_in_both_adapters(
    tmp_path: Path,
) -> None:
    """Criterion 6: absolute and ``..`` inputs refuse before any directory."""
    root, workspace = _seed_screener_workspace(tmp_path / "repo")
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")

    app = _screener_adapter(root, workspace)
    for task, raw in (
        ("t-out-absolute", str(outside)),
        ("t-out-dotdot", "../outside.json"),
    ):
        with pytest.raises(ScopeViolation) as excinfo:
            app.run(
                RunRequest(
                    task_id=task,
                    role_id="screener",
                    role_version=SCREENER_ROLE_VERSION,
                    # Three inputs, so the F1 input-schema preflight passes and
                    # the outside-root refusal is the one this test asserts.
                    inputs=(raw, *SCREENER_INPUTS[1:]),
                    params={"ws": _WS},
                    arm="A",
                    input_schemas=SCREENER_INPUT_SCHEMAS,
                ),
                lambda s: None,
            )
        assert "outside.json" in excinfo.value.detail
        assert "outside the run root" in excinfo.value.detail
        assert not (workspace / "runs").exists()
        assert not (workspace / "audit" / "journal.jsonl").exists()

    dev = OpencodeAdapter(workspace=root, roles_dir=ROLES_DIR)
    for task, raw in (
        ("t-dev-out-absolute", str(outside)),
        ("t-dev-out-dotdot", "../outside.json"),
    ):
        with pytest.raises(ScopeViolation) as excinfo:
            dev.run(
                RunRequest(
                    task_id=task,
                    role_id="screener",
                    role_version=SCREENER_ROLE_VERSION,
                    inputs=(raw, *SCREENER_INPUTS[1:]),
                    params={"ws": _WS},
                    arm="A",
                    input_schemas=SCREENER_INPUT_SCHEMAS,
                ),
                lambda s: None,
            )
        assert "outside.json" in excinfo.value.detail
        assert "outside the run root" in excinfo.value.detail
        assert not (root / "runs").exists()
        assert not (root / "audit" / "journal.jsonl").exists()


def test_run_role_dispatches_and_refuses_unknown_adapter(tmp_path: Path) -> None:
    """Criterion 7: one dispatch entry point; unknown names are typed refusals."""
    root, workspace = _seed_screener_workspace(tmp_path)
    envelope = run_role(
        "in-process",
        _screener_request("t-dispatch", arm="A"),
        lambda s: s.write(
            "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
        ),
        workspace=workspace,
        roles_dir=ROLES_DIR,
        root=root,
    )
    assert isinstance(envelope, Envelope)
    assert envelope.provenance.adapter == "in-process"
    assert validate(envelope.model_dump(by_alias=True), roles_dir=ROLES_DIR) == envelope

    with pytest.raises(ScopeViolation) as excinfo:
        run_role(
            "nope",  # type: ignore[arg-type]
            _screener_request("t-dispatch-unknown", arm="A"),
            lambda s: None,
            workspace=workspace,
            roles_dir=ROLES_DIR,
            root=root,
        )
    assert "nope" in excinfo.value.detail
    assert "unknown adapter" in excinfo.value.detail


def test_multi_artifact_run_carries_one_payload_and_full_coverage(
    tmp_path: Path,
) -> None:
    """Envelope@1 carries one payload; coverage + journal carry the rest."""
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    payload = json.dumps(_valid_decisions_payload("A"))

    def handler(session: RoleSession) -> None:
        session.write("batch_001_decisions.json", payload)
        session.write("batch_002_decisions.json", payload)

    envelope = adapter.run(_screener_request("t-multi", arm="A"), handler)
    assert envelope.status is EnvelopeStatus.OK
    assert envelope.coverage is not None
    assert envelope.coverage.expected == envelope.coverage.produced == 2
    assert envelope.coverage.unit == "artifact"
    assert envelope.output is not None
    assert validate(envelope.model_dump(by_alias=True), roles_dir=ROLES_DIR) == envelope
    journal = workspace / "audit" / "journal.jsonl"
    record = json.loads(journal.read_text(encoding="utf-8").splitlines()[-1])
    assert len(record["metrics"]["output_sha256"]) == 2, (
        "the journal remains the authoritative per-artifact record"
    )


def test_tampered_output_sha256_changes_identity_and_fails_validation(
    tmp_path: Path,
) -> None:
    """Negative: a claimed hash that was not recomputed is rejected."""
    envelope, _root, _workspace, _adapter = _ok_envelope(tmp_path, task="t-tamper")
    tampered = envelope.model_copy(update={"output_sha256": "0" * 64})

    with pytest.raises(EnvelopeRefusalError) as excinfo:
        validate(tampered.model_dump(by_alias=True), roles_dir=ROLES_DIR)
    assert "output_sha256" in excinfo.value.detail

    resigned = tampered.model_copy(update={"envelope_id": envelope_id(tampered)})
    assert resigned.envelope_id != envelope.envelope_id


# ---------------------------------------------------------------------------
# T-ALP-E4 round 2: the contract is the authority (roles_dir-aware validation),
# typed input binding, the arm gate, per-artifact validation, and journal
# agreement.
# ---------------------------------------------------------------------------


def test_ok_envelope_passes_the_shipped_cli(tmp_path: Path) -> None:
    """The artifact ``run()`` returns is accepted by the shipped CLI (exit 0).

    Newer contracts are validated by the harness library *and* by
    ``python -m scholar_harness.contracts.envelope validate``; an envelope only
    the library accepts is not a valid transport row. The test drives the CLI's
    own ``main`` (same code path as the module entrypoint) against the JSON
    document the adapter produced.
    """
    from scholar_harness.contracts.envelope.cli import main as envelope_cli

    envelope, _root, _workspace, _adapter = _ok_envelope(tmp_path, task="t-env-cli")
    assert envelope.status is EnvelopeStatus.OK

    path = tmp_path / "envelope.json"
    path.write_text(
        json.dumps(envelope.model_dump(mode="json", by_alias=True), indent=2),
        encoding="utf-8",
    )
    assert envelope_cli(["validate", str(path), "--roles-dir", str(ROLES_DIR)]) == 0


def test_solo_run_of_an_isolated_role_is_refused(tmp_path: Path) -> None:
    """R3: ``arm=None`` for ``isolation != "none"`` is a typed refusal.

    ``Envelope@1`` requires an arm for any isolated role (api.py role
    compatibility), so the adapter refuses before it creates a run directory or
    writes a journal row — it never builds a solo envelope the contract rejects.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    with pytest.raises(ScopeViolation) as excinfo:
        adapter.run(_screener_request("t-solo-isolated", arm=None), lambda s: None)

    detail = excinfo.value.detail
    assert "redacted-input" in detail
    assert "arm is required" in detail
    assert not (workspace / "runs").exists()
    assert not (workspace / "audit" / "journal.jsonl").exists()


def test_arm_a_run_of_an_isolated_role_succeeds(tmp_path: Path) -> None:
    """R3 counterexample: the same isolated role with ``arm="A"`` runs OK."""
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    envelope = adapter.run(
        _screener_request("t-arm-a-isolated", arm="A"),
        lambda s: s.write(
            "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
        ),
    )

    assert envelope.status is EnvelopeStatus.OK
    assert envelope.arm == "A"
    assert envelope.provenance.isolation == "redacted-input"
    assert [ref.schema_ for ref in envelope.inputs] == [
        "ScreeningBatch@1",
        "Protocol@1",
        "ScreeningCriteria@1",
    ]
    assert validate(envelope.model_dump(by_alias=True), roles_dir=ROLES_DIR) == envelope


def test_undeclared_input_schemas_are_refused_before_the_handler(
    tmp_path: Path,
) -> None:
    """F1: ``input_schemas=()`` for a role that declares inputs is a refusal.

    The pre-handler check names both counts and runs before ``runs/{task_id}``,
    any ``rmtree``, or any promotion: the caller cannot leave an ``OK``
    envelope attesting a schema binding the adapter invented. Replaces the old
    R2 behaviour, where a count mismatch became an ``INVALID_OUTPUT`` envelope
    *after* the handler had already published an artifact.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    request = _screener_request("t-input-mismatch", arm="A", input_schemas=())
    with pytest.raises(ScopeViolation) as excinfo:
        adapter.run(
            request,
            lambda s: s.write(
                "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
            ),
        )

    detail = excinfo.value.detail
    assert "3 inputs" in detail
    assert "0 input_schemas" in detail
    assert "inputs order" in detail
    assert not (workspace / "runs").exists()
    assert not (workspace / "audit" / "journal.jsonl").exists()
    assert not list((workspace / "literature" / "screening").glob("*_decisions*"))


def test_multi_artifact_with_one_invalid_artifact_is_invalid_output(
    tmp_path: Path,
) -> None:
    """R5 + F2: a second artifact is validated too; the invalid one is retained.

    With exactly one invalid artifact the adapter retains *that* payload (the
    findings name it), never the neighbouring success — the envelope must
    describe the failure the run is reporting.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    bad = _decisions_blob("A")

    def handler(session: RoleSession) -> None:
        session.write(
            "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
        )
        session.write("batch_002_decisions.json", bad)

    envelope = adapter.run(_screener_request("t-multi-bad", arm="A"), handler)

    assert envelope.status is EnvelopeStatus.INVALID_OUTPUT
    assert envelope.inputs == []
    assert envelope.refusal is not None
    assert envelope.refusal.validation_findings
    assert any(
        "batch_002_decisions_A.json" in finding
        for finding in envelope.refusal.validation_findings
    ), envelope.refusal.validation_findings
    # F2: the retained payload is the invalid artifact, not batch_001's success.
    assert envelope.output is not None
    assert envelope.output.schema_ == "ScreeningDecisions@1"
    assert envelope.output.data == json.loads(bad)
    assert envelope.output.data["decisions"] == []
    assert envelope.output_sha256 == contract_output_sha256(
        {"output": {"schema": "ScreeningDecisions@1", "data": envelope.output.data}}
    )
    assert envelope.coverage is None
    assert validate(envelope.model_dump(by_alias=True), roles_dir=ROLES_DIR) == envelope


def test_journal_status_matches_envelope_status(tmp_path: Path) -> None:
    """R6: the audit row and the returned envelope never disagree.

    ``OK`` journals the role's first declared action with ``SUCCESS``; an
    ``INVALID_OUTPUT`` run journals the role's second declared action with
    ``INVALID_OUTPUT`` — the row is written *after* the envelope exists, so it
    cannot claim a success the envelope denies.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)

    ok = adapter.run(
        _screener_request("t-status-ok", arm="A"),
        lambda s: s.write(
            "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
        ),
    )
    bad = adapter.run(
        _screener_request("t-status-bad", arm="A"),
        lambda s: s.write("batch_001_decisions.json", _decisions_blob("A")),
    )

    rows = [
        json.loads(line)
        for line in (workspace / "audit" / "journal.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    by_task = {row["parameters"]["task_id"]: row for row in rows}
    assert set(by_task) == {"t-status-ok", "t-status-bad"}

    assert ok.status is EnvelopeStatus.OK
    assert by_task["t-status-ok"]["status"] == "SUCCESS"
    assert by_task["t-status-ok"]["action"] == "SCREENING_COMPLETED"

    assert bad.status is EnvelopeStatus.INVALID_OUTPUT
    assert by_task["t-status-bad"]["status"] == "INVALID_OUTPUT"
    assert by_task["t-status-bad"]["action"] == "SCREENING_BLOCKED"


def test_declared_required_row_gap_is_partial(tmp_path: Path) -> None:
    """R5: fewer artifacts than declared required rows is ``PARTIAL``, not OK.

    The role below declares two ``required: true`` output rows but the run fills
    one. ``Envelope@1`` cannot report that as ``OK`` (produced == expected is an
    OK invariant), so the adapter reports ``PARTIAL`` with the role's own
    coverage-gap code and the journal records ``PARTIAL`` for the same task.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    roles = tmp_path / "roles"
    shutil.copytree(ROLES_DIR, roles)
    record = json.loads((roles / "screener.json").read_text(encoding="utf-8"))
    record["outputs"].append(
        {
            "required": True,
            "schema": "ScreeningDecisions@1",
            "write_glob": (
                "workspaces/{ws}/literature/screening/{batch}_review_{arm}.json"
            ),
        }
    )
    (roles / "screener.json").write_text(json.dumps(record), encoding="utf-8")
    adapter = InProcessAdapter(root=root, workspace=workspace, roles_dir=roles)

    envelope = adapter.run(
        _screener_request("t-partial", arm="A"),
        lambda s: s.write(
            "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
        ),
    )

    assert envelope.status is EnvelopeStatus.PARTIAL
    assert envelope.coverage is not None
    assert (envelope.coverage.produced, envelope.coverage.expected) == (1, 2)
    assert envelope.coverage.unit == "artifact"
    assert envelope.output is not None
    assert envelope.output.schema_ == "ScreeningDecisions@1"
    assert envelope.inputs == [], "only an OK envelope carries inputs"
    assert envelope.refusal is not None
    assert envelope.refusal.code == "BATCH_INCOMPLETE"
    assert validate(envelope.model_dump(by_alias=True), roles_dir=roles) == envelope

    record_row = json.loads(
        (workspace / "audit" / "journal.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[-1]
    )
    assert record_row["parameters"]["task_id"] == "t-partial"
    assert record_row["status"] == "PARTIAL"
    assert record_row["action"] == "SCREENING_BLOCKED"
    # F4: PARTIAL carries one payload too, so the journal names its file.
    assert record_row["parameters"]["payload_artifact"] == (
        f"workspaces/{_WS}/literature/screening/batch_001_decisions_A.json"
    )


def test_torn_role_record_is_a_typed_refusal(tmp_path: Path, monkeypatch) -> None:
    """R7: a torn record is a ``ScopeViolation`` naming the record path."""
    roles = tmp_path / "roles"
    shutil.copytree(ROLES_DIR, roles)
    (roles / "broken-json.json").write_text("{not json", encoding="utf-8")
    (roles / "not-an-object.json").write_text(json.dumps(["nope"]), encoding="utf-8")
    (roles / "missing-id.json").write_text(
        json.dumps(
            {
                "version": "2.0.0",
                "independence": {"isolation": "none", "blinded_from": []},
                "audit": {
                    "actor": "{role}@{version}",
                    # F5: a role that can emit a non-OK envelope must declare a distinct
                    # failure action (the adapter journals it for INVALID_OUTPUT/PARTIAL
                    # and never reuses the completion verb).
                    "emit": ["REVIEW_COMPLETED", "REVIEW_BLOCKED"],
                },
                "outputs": [
                    {"schema": "Review@1", "write_glob": "workspaces/{ws}/x.json"}
                ],
            }
        ),
        encoding="utf-8",
    )
    (roles / "unreadable.json").write_text("{}", encoding="utf-8")

    for role_id in ("broken-json", "not-an-object", "missing-id"):
        with pytest.raises(ScopeViolation) as excinfo:
            load_role_policy(roles, role_id)
        assert str(roles / f"{role_id}.json") in excinfo.value.detail

    real_read_text = Path.read_text

    def failing_read(self: Path, *args, **kwargs):
        if self.name == "unreadable.json":
            raise OSError("denied by test")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", failing_read)
    with pytest.raises(ScopeViolation) as excinfo:
        load_role_policy(roles, "unreadable")
    monkeypatch.undo()
    assert str(roles / "unreadable.json") in excinfo.value.detail
    assert "unreadable" in excinfo.value.detail


def test_unrepresentable_role_version_rolls_back_and_raises_contract_violation(
    tmp_path: Path,
) -> None:
    """R7 + F3 + F7: a role record the contract cannot bind leaves no debris.

    ``run_request_policy`` accepts the request (the versions match), the handler
    promotes a real artifact, and then the contract refuses the envelope:
    ``"v2"`` has no parseable major version. The adapter converts that into
    :class:`ContractViolation` (a ``ScopeViolation``) *and* removes exactly what
    this run promoted plus ``runs/{task_id}`` — a published artifact with no
    journal row is not allowed to survive a late contract failure.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    roles = tmp_path / "roles"
    shutil.copytree(ROLES_DIR, roles)
    record = json.loads((roles / "screener.json").read_text(encoding="utf-8"))
    record["version"] = "v2"
    (roles / "screener.json").write_text(json.dumps(record), encoding="utf-8")
    adapter = InProcessAdapter(root=root, workspace=workspace, roles_dir=roles)
    request = RunRequest(
        task_id="t-bad-version",
        role_id="screener",
        role_version="v2",
        inputs=SCREENER_INPUTS,
        params=PARAMS,
        arm="A",
        input_schemas=SCREENER_INPUT_SCHEMAS,
    )
    with pytest.raises(ScopeViolation) as excinfo:
        adapter.run(
            request,
            lambda s: s.write(
                "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
            ),
        )
    assert isinstance(excinfo.value, ContractViolation)
    assert "cannot materialise a validated Envelope@1" in excinfo.value.detail
    assert "v2" in excinfo.value.detail
    assert not (
        workspace / "literature" / "screening" / "batch_001_decisions_A.json"
    ).exists(), "F3: a contract failure must not leave a promoted artifact behind"
    assert not (workspace / "runs").exists(), "F3: the run directory must be removed"
    assert not (workspace / "audit" / "journal.jsonl").exists(), (
        "no journal row may claim a run whose envelope was never built"
    )


def test_journal_append_failure_is_not_rolled_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F3/P9: only envelope construction rolls back; the append is authoritative.

    The rollback block ends *before* the journal append on purpose: once the
    envelope is valid the output is published, so an append ``OSError`` must
    surface as-is and leave the promoted artifact in place. Rolling back there
    would destroy a valid, already-reported output because the ledger failed.
    """
    from scholar_harness.capabilities import inprocess as inprocess_module

    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)

    def failing_append(*_args: object, **_kwargs: object) -> Path:
        raise OSError("journal is read-only")

    monkeypatch.setattr(inprocess_module, "append_journal", failing_append)
    with pytest.raises(OSError) as excinfo:
        adapter.run(
            _screener_request("t-append-fails", arm="A"),
            lambda s: s.write(
                "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
            ),
        )
    monkeypatch.undo()

    assert "journal is read-only" in str(excinfo.value)
    assert (
        workspace / "literature" / "screening" / "batch_001_decisions_A.json"
    ).is_file(), "P9: a journal failure must not unpublish a valid output"
    assert (workspace / "runs" / "t-append-fails").is_dir(), (
        "P9: the append failure is outside the rollback block"
    )
    assert not (workspace / "audit" / "journal.jsonl").exists()


def test_refusal_envelope_normalises_a_blank_detail() -> None:
    """R7: a blank detail is replaced, never shipped as an empty refusal."""
    request = _screener_request("t-refused-normalise", arm="A")
    policy = run_request_policy(ROLES_DIR, request)
    refusal = ScopeViolation("   ")

    envelope = refusal.envelope(
        request,
        policy,
        adapter="in-process",
        adapter_version="1.0.0",
        roles_dir=ROLES_DIR,
    )

    assert envelope.status is EnvelopeStatus.REFUSED
    assert envelope.refusal is not None
    assert envelope.refusal.code == "SCOPE_VIOLATION"
    assert envelope.refusal.detail == "scope violation"
    assert envelope.inputs == []
    assert envelope.output is None
    assert envelope.output_sha256 is None
    assert validate(envelope.model_dump(by_alias=True), roles_dir=ROLES_DIR) == envelope


def test_refusal_envelope_refuses_an_unregistered_code() -> None:
    """F6: an unregistered ``code`` is a defect, never coerced to SCOPE_VIOLATION.

    ``Envelope@1.refusal.code`` is a closed registry. Silently relabelling the
    refusal would ship a transport row that misdescribes *why* the run was
    refused, so the accessor raises naming the code instead.
    """
    request = _screener_request("t-refused-unknown-code", arm="A")
    policy = run_request_policy(ROLES_DIR, request)
    refusal = ScopeViolation("unknown code must not be coerced")
    refusal.code = "NOT_A_REGISTERED_CODE"

    with pytest.raises(ScopeViolation) as excinfo:
        refusal.envelope(
            request,
            policy,
            adapter="in-process",
            adapter_version="1.0.0",
            roles_dir=ROLES_DIR,
        )
    assert "NOT_A_REGISTERED_CODE" in excinfo.value.detail
    assert "not a registered RefusalCode" in excinfo.value.detail


def test_refusal_envelope_never_raises_a_contract_error() -> None:
    """R7 + F7: a refusal the contract rejects surfaces as ``ContractViolation``.

    ``BATCH_INCOMPLETE`` is registry-scoped to the screening roles, so the
    contract's role-compatibility step rejects a ``tester`` refusal carrying it.
    ``ScopeViolation.envelope`` converts that into the typed contract exception
    (which is still a ``ScopeViolation`` for existing handlers) instead of
    leaking ``EnvelopeRefusalError``.
    """
    request = RunRequest(
        task_id="t-refused-tester",
        role_id="tester",
        role_version="2.0.0",
        # ``roles/tester.json`` declares both of these as required (F1).
        inputs=(
            f"workspaces/{_WS}/literature/batch.json",
            f"workspaces/{_WS}/INDEX.md",
        ),
        params=PARAMS,
        arm="A",
        input_schemas=("TaskPacket@1", "ValidationCommands@1"),
    )
    policy = run_request_policy(ROLES_DIR, request)
    refusal = ScopeViolation("tester cannot emit BATCH_INCOMPLETE")
    refusal.code = "BATCH_INCOMPLETE"
    with pytest.raises(ScopeViolation) as excinfo:
        refusal.envelope(
            request,
            policy,
            adapter="in-process",
            adapter_version="1.0.0",
            roles_dir=ROLES_DIR,
        )
    assert isinstance(excinfo.value, ContractViolation), (
        "a frozen-contract refusal must be reported as a contract violation"
    )
    assert "REFUSED envelope" in excinfo.value.detail


# ---------------------------------------------------------------------------
# T-ALP-E4 round 3: caller-declared input schemas (F1), late-failure rollback
# (F3), journal payload naming (F4), the audit-action floor (F5), the strict
# refusal accessor (F6), contract-vs-scope refusals (F7), and the frozen
# retention boundary (F2).
# ---------------------------------------------------------------------------


def test_input_schemas_are_attested_verbatim_in_caller_order(tmp_path: Path) -> None:
    """F1: the envelope repeats the caller's declaration, not the record order.

    The reviewer's probe swapped two inputs and still received ``OK`` under the
    adapter's own binding. Here the caller deliberately declares a different
    order (``Protocol@1`` first): the envelope must carry exactly that order and
    the contract must still accept the row — the caller's declaration is the
    attestation, and the adapter adds nothing to it.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    inputs = (SCREENER_INPUTS[1], SCREENER_INPUTS[0], SCREENER_INPUTS[2])
    schemas = ("Protocol@1", "ScreeningBatch@1", "ScreeningCriteria@1")

    envelope = adapter.run(
        _screener_request(
            "t-input-order", arm="A", inputs=inputs, input_schemas=schemas
        ),
        lambda s: s.write(
            "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
        ),
    )

    assert envelope.status is EnvelopeStatus.OK
    assert [ref.schema_ for ref in envelope.inputs] == list(schemas)
    assert [ref.path for ref in envelope.inputs] == list(inputs)
    assert validate(envelope.model_dump(by_alias=True), roles_dir=ROLES_DIR) == envelope


def test_input_schema_count_mismatch_is_refused_pre_handler(tmp_path: Path) -> None:
    """F1: two schemas for three inputs is a refusal, never a positional guess."""
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    with pytest.raises(ScopeViolation) as excinfo:
        adapter.run(
            _screener_request(
                "t-schema-count", arm="A", input_schemas=SCREENER_INPUT_SCHEMAS[:2]
            ),
            lambda s: s.write(
                "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
            ),
        )

    detail = excinfo.value.detail
    assert "3 inputs" in detail
    assert "2 input_schemas" in detail
    assert "inputs order" in detail
    assert not (workspace / "runs").exists()
    assert not (workspace / "audit" / "journal.jsonl").exists()
    assert not list((workspace / "literature" / "screening").glob("*_decisions*"))


def test_undeclared_input_schema_is_refused_naming_it_and_the_declared_set(
    tmp_path: Path,
) -> None:
    """F1: a schema the role does not declare is refused, not silently bound."""
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    with pytest.raises(ScopeViolation) as excinfo:
        adapter.run(
            _screener_request(
                "t-schema-undeclared",
                arm="A",
                input_schemas=("ScreeningBatch@1", "Protocol@1", "Review@1"),
            ),
            lambda s: None,
        )

    detail = excinfo.value.detail
    assert "Review@1" in detail
    assert "does not declare" in detail
    assert "ScreeningCriteria@1" in detail, "the refusal must list the declared set"
    assert not (workspace / "runs").exists()
    assert not (workspace / "audit" / "journal.jsonl").exists()


def test_missing_required_input_schema_is_refused(tmp_path: Path) -> None:
    """F1: a required declared input the request omits is a refusal.

    ``roles/inception-agent.json`` declares ``ChatIntent@1`` required and
    ``IntentPacket@1``/``ReconPool@1`` optional; a two-schema request that omits
    ``ChatIntent@1`` matches the input count yet cannot satisfy the role's own
    input contract.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    request = RunRequest(
        task_id="t-schema-missing",
        role_id="inception-agent",
        role_version="2.0.0",
        inputs=(
            f"workspaces/{_WS}/protocol.json",
            f"workspaces/{_WS}/INDEX.md",
        ),
        params=PARAMS,
        input_schemas=("IntentPacket@1", "ReconPool@1"),
    )
    with pytest.raises(ScopeViolation) as excinfo:
        adapter.run(request, lambda s: None)

    detail = excinfo.value.detail
    assert "ChatIntent@1" in detail
    assert "required input schema" in detail
    assert not (workspace / "runs").exists()
    assert not (workspace / "audit" / "journal.jsonl").exists()


def test_role_without_declared_inputs_attests_untyped(tmp_path: Path) -> None:
    """F1: no declared input schema → the honest ``"untyped"``, still valid.

    ``Envelope@1`` requires a non-empty input schema string. A role that
    declares no input rows gives the adapter no name to attest, so it emits
    ``"untyped"``; the contract's role-compatibility step accepts it because the
    record declares nothing to check against.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    roles = tmp_path / "roles"
    shutil.copytree(ROLES_DIR, roles)
    record = json.loads((roles / "screener.json").read_text(encoding="utf-8"))
    record.pop("inputs")
    (roles / "screener.json").write_text(json.dumps(record), encoding="utf-8")
    adapter = InProcessAdapter(root=root, workspace=workspace, roles_dir=roles)

    envelope = adapter.run(
        _screener_request("t-untyped", arm="A", input_schemas=()),
        lambda s: s.write(
            "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
        ),
    )

    assert envelope.status is EnvelopeStatus.OK
    assert [ref.schema_ for ref in envelope.inputs] == ["untyped"] * 3
    assert validate(envelope.model_dump(by_alias=True), roles_dir=roles) == envelope


def _retained_payload_envelope(schema: str, data: dict[str, object]) -> Envelope:
    """An ``INVALID_OUTPUT`` envelope that *retains* the failed payload (F2).

    Matches the frozen golden fixture
    (``tests/conformance/fixtures/envelope/invalid_output.json``): status,
    refusal with findings, one payload, and its canonical hash.
    """
    envelope = Envelope(
        envelope=1,
        envelope_id="ENV-" + "0" * 16,
        role="screener",
        role_version=SCREENER_ROLE_VERSION,
        task_id="t-retained",
        arm="A",
        created_at=datetime.now(UTC),
        status=EnvelopeStatus.INVALID_OUTPUT,
        retryable=False,
        human_action_required=False,
        refusal=EnvelopeRefusal(
            code="INVALID_OUTPUT",
            detail="promoted artifact failed validation",
            validation_findings=["decision: PERMANENT is not a valid enum value"],
        ),
        coverage=None,
        inputs=[],
        parents=[],
        output=EnvelopeOutput(schema=schema, data=data),
        output_sha256=hashlib.sha256(canonical_json_bytes(data)).hexdigest(),
        provenance=EnvelopeProvenance(
            adapter="in-process",
            adapter_version="1.0.0",
            isolation="redacted-input",
            blinded_from=[],
            duration_ms=1,
        ),
    )
    return envelope.model_copy(update={"envelope_id": envelope_id(envelope)})


def test_invalid_output_retention_is_refused_for_an_undeclared_schema() -> None:
    """F2: a retained payload under a schema the role does not declare fails.

    This is the frozen gate that *does* block retention
    (``contracts/envelope/api.py:273-278``, and ``:279-286`` for a declared
    schema with no registered model): the schema name may only be one the role
    declares, so an unvalidatable-role payload (D11) has no honest home.
    """
    envelope = _retained_payload_envelope("Extraction@1", {"x": 1})
    with pytest.raises(EnvelopeRefusalError) as excinfo:
        validate(envelope.model_dump(by_alias=True), roles_dir=ROLES_DIR)
    assert "Extraction@1" in excinfo.value.detail
    assert "is not one that role" in excinfo.value.detail


def test_invalid_output_retention_is_used_by_the_adapter(tmp_path: Path) -> None:
    """F2: retention is representable *and* the adapter actually uses it.

    The frozen fixture plus ``test_envelope.py``::
    ``test_invariant_invalid_output_retains_forensics`` establish that
    ``INVALID_OUTPUT`` retains its payload (payload re-validation runs only for
    ``OK``/``PARTIAL``: ``contracts/envelope/api.py:446``/``:474``). The adapter
    therefore retains a single failing payload under a role-declared, registered
    schema, and its hash is the contract's own — identical to the fixture's
    encoding.
    """
    payload = {"arm": "A", "decisions": []}  # not a valid ScreeningDecisions@1
    retained = _retained_payload_envelope("ScreeningDecisions@1", payload)
    validated = validate(retained.model_dump(by_alias=True), roles_dir=ROLES_DIR)
    assert validated.output is not None
    assert validated.output.schema_ == "ScreeningDecisions@1"

    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    envelope = adapter.run(
        _screener_request("t-retain-choice", arm="A"),
        lambda s: s.write("batch_001_decisions.json", json.dumps(payload)),
    )
    assert envelope.status is EnvelopeStatus.INVALID_OUTPUT
    assert envelope.output is not None
    assert envelope.output.data == payload
    assert envelope.output_sha256 == contract_output_sha256(
        {"output": {"schema": "ScreeningDecisions@1", "data": payload}}
    )
    assert envelope.output_sha256 == validated.output_sha256, (
        "the adapter and the frozen retention fixture agree on the encoding"
    )
    assert validate(envelope.model_dump(by_alias=True), roles_dir=ROLES_DIR) == envelope


def test_non_json_artifact_is_not_retained(tmp_path: Path) -> None:
    """F2 matrix: a non-object artifact is unretainable — no second encoding."""
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    envelope = adapter.run(
        _screener_request("t-retain-nonobj", arm="A"),
        lambda s: s.write("batch_001_decisions.json", "not json at all"),
    )
    assert envelope.status is EnvelopeStatus.INVALID_OUTPUT
    assert envelope.output is None
    assert envelope.output_sha256 is None
    assert envelope.coverage is None
    assert envelope.refusal is not None
    assert any(
        "batch_001_decisions_A.json" in finding and "not a JSON object" in finding
        for finding in envelope.refusal.validation_findings
    ), envelope.refusal.validation_findings
    assert validate(envelope.model_dump(by_alias=True), roles_dir=ROLES_DIR) == envelope


def test_declared_but_unregistered_schema_is_not_retained(tmp_path: Path) -> None:
    """F2 matrix: a declared schema with no Contract v1 model is unretainable.

    ``contracts/envelope/api.py:279-286`` rejects a retained payload whose
    declared schema is absent from ``PAYLOAD_MODELS`` (the D11 case). The
    synthetic role declares ``Review@1``, which no model registers, so the
    adapter ships ``output=None`` and names the artifact in the findings.
    """
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    envelope = adapter.run(
        _request(task="t-retain-unregistered"),
        lambda s: s.write("SCI-01.json", '{"verdict": "include"}'),
    )
    assert envelope.status is EnvelopeStatus.INVALID_OUTPUT
    assert envelope.output is None
    assert envelope.output_sha256 is None
    assert envelope.refusal is not None
    assert any(
        "SCI-01.json" in finding and "not registered" in finding
        for finding in envelope.refusal.validation_findings
    ), envelope.refusal.validation_findings
    # P3-6: the contract refused the name, so the fallback records *its*
    # message rather than a locally pre-judged gate.
    assert any(
        finding.startswith("payload not retained:")
        for finding in envelope.refusal.validation_findings
    ), envelope.refusal.validation_findings
    # The synthetic role is not a shipped record, so its own roles dir is the
    # only valid authority here (the real screener cases above use ROLES_DIR).
    roles = tmp_path / "roles"
    assert validate(envelope.model_dump(by_alias=True), roles_dir=roles) == envelope


def test_multiple_invalid_artifacts_retain_no_payload(tmp_path: Path) -> None:
    """F2: two invalid artifacts → no payload, and the findings say why.

    ``Envelope@1`` carries at most one payload. Retaining either failure would
    require inventing a precedence rule, so the adapter retains none and names
    every invalid artifact plus the reason.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)

    def handler(session: RoleSession) -> None:
        session.write("batch_001_decisions.json", _decisions_blob("A"))
        session.write("batch_002_decisions.json", json.dumps({"arm": "A"}))

    envelope = adapter.run(_screener_request("t-retain-two", arm="A"), handler)

    assert envelope.status is EnvelopeStatus.INVALID_OUTPUT
    assert envelope.output is None
    assert envelope.output_sha256 is None
    assert envelope.refusal is not None
    findings = envelope.refusal.validation_findings
    assert any("batch_001_decisions_A.json" in finding for finding in findings), (
        findings
    )
    assert any("batch_002_decisions_A.json" in finding for finding in findings), (
        findings
    )
    assert any("no payload is retained" in finding for finding in findings), findings
    assert validate(envelope.model_dump(by_alias=True), roles_dir=ROLES_DIR) == envelope


def test_journal_names_the_payload_artifact_for_ok(tmp_path: Path) -> None:
    """F4: the journal names the promoted file backing ``output``."""
    envelope, root, workspace, _adapter = _ok_envelope(tmp_path, task="t-payload-ok")
    assert envelope.output is not None
    record = json.loads(
        (workspace / "audit" / "journal.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[-1]
    )
    expected = f"workspaces/{_WS}/literature/screening/batch_001_decisions_A.json"
    assert record["parameters"]["payload_artifact"] == expected
    assert (root / record["parameters"]["payload_artifact"]).is_file()
    assert record["parameters"]["payload_artifact"] in record["outputs"]


def test_journal_omits_payload_artifact_for_invalid_output(tmp_path: Path) -> None:
    """F4 scope: the journal key tracks the payload a caller may act on.

    The run retains the failing payload for forensics (F2), but F4's
    ``payload_artifact`` stays scoped to ``OK``/``PARTIAL``; the artifact behind
    the retained payload is named in ``refusal.validation_findings`` instead.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    envelope = adapter.run(
        _screener_request("t-payload-bad", arm="A"),
        lambda s: s.write("batch_001_decisions.json", _decisions_blob("A")),
    )
    assert envelope.status is EnvelopeStatus.INVALID_OUTPUT
    assert envelope.output is not None, "the forensic payload is retained (F2)"
    record = json.loads(
        (workspace / "audit" / "journal.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[-1]
    )
    assert "payload_artifact" not in record["parameters"]


def test_single_action_role_is_refused_at_policy_load(tmp_path: Path) -> None:
    """F5: a role with one ``emit`` action cannot journal a failure verb.

    ``journal_action_for`` writes the role's second declared action for any
    non-OK envelope; a record with one action would journal its *completion*
    verb next to ``INVALID_OUTPUT``. Policy load refuses that shape instead.
    """
    roles = tmp_path / "roles"
    roles.mkdir()
    record = {
        **AGENT_RECORD,
        "id": "one-verb",
        "audit": {"actor": "{role}@{version}", "emit": ["WORK_COMPLETED"]},
    }
    (roles / "one-verb.json").write_text(json.dumps(record), encoding="utf-8")

    with pytest.raises(ScopeViolation) as excinfo:
        load_role_policy(roles, "one-verb")
    assert excinfo.value.detail == (
        "role 'one-verb' declares 1 audit action; a role that can emit a "
        "non-OK envelope must declare a distinct failure action"
    )

    # A sibling-only load (blinding source) is unaffected: it cannot run, so it
    # cannot journal, so it needs no failure verb.
    sibling = load_role_policy(roles, "one-verb", require_audit=False)
    assert sibling.emit_actions == ("WORK_COMPLETED",)


def test_two_action_role_journals_its_second_action_for_invalid_output(
    tmp_path: Path,
) -> None:
    """F5 re-assert: the declared failure verb is journaled, never action[0].

    The synthetic role's ``Review@1`` output schema has no registered Contract
    v1 model, so every run is ``INVALID_OUTPUT`` — the exact shape that must not
    journal ``REVIEW_COMPLETED``.
    """
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    envelope = adapter.run(
        _request(task="t-two-verbs"), lambda s: s.write("SCI-01.json", '{"v": 1}')
    )
    assert envelope.status is EnvelopeStatus.INVALID_OUTPUT
    record = json.loads(
        (workspace / "audit" / "journal.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[-1]
    )
    assert record["action"] == "REVIEW_BLOCKED"
    assert record["status"] == "INVALID_OUTPUT"


def test_refusal_envelope_requires_roles_dir() -> None:
    """F6: ``roles_dir`` is required keyword-only — no unvalidated envelope."""
    request = _screener_request("t-requires-roles-dir", arm="A")
    policy = run_request_policy(ROLES_DIR, request)
    refusal = ScopeViolation("boundary breach")
    with pytest.raises(TypeError):
        refusal.envelope(  # type: ignore[call-arg]
            request,
            policy,
            adapter="in-process",
            adapter_version="1.0.0",
        )


def test_contract_violation_is_exported_and_is_a_scope_violation() -> None:
    """F7: contract refusals keep the ``except ScopeViolation`` contract."""
    from scholar_harness.capabilities import adapter as adapter_module

    assert adapter_module.ContractViolation is ContractViolation
    assert issubclass(ContractViolation, ScopeViolation)
    violation = ContractViolation("role_version 'v2' is unrepresentable")
    assert isinstance(violation, ScopeViolation)
    assert violation.code == "SCOPE_VIOLATION"


# ---------------------------------------------------------------------------
# P2-1/P3-9: ``{task_id}`` is a run label bound from the request, never params
# ---------------------------------------------------------------------------


def test_task_id_placeholder_binds_the_validated_request_field(tmp_path: Path) -> None:
    """P2-1: ``{task_id}`` resolves from ``RunRequest.task_id``, not from params.

    ``roles/reviewer.json`` declares exactly one output,
    ``runs/{task_id}/review.json``. Without the binding the row kept the literal
    ``{task_id}`` and every write was refused as un-bindable, so ``reviewer``
    could not produce its declared output at all.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = InProcessAdapter(root=root, workspace=workspace, roles_dir=ROLES_DIR)
    request = RunRequest(
        task_id="t-alp-e4-42",
        role_id="reviewer",
        role_version="2.0.0",
        inputs=SCREENER_INPUTS,
        params=PARAMS,
        arm="A",
        input_schemas=("TaskPacket@1", "ChangeSet@1", "Diff@1"),
    )

    envelope = adapter.run(
        request, lambda s: s.write("review.json", '{"verdict": "approve"}')
    )

    destination = root / "runs" / "t-alp-e4-42" / "review.json"
    assert destination.is_file(), "the declared {task_id} output must be writable"
    assert destination.relative_to(root).as_posix() == "runs/t-alp-e4-42/review.json"
    assert "t-alp-e4-42" in destination.parts
    assert "{" not in str(destination), "no unbound placeholder may reach a path"
    assert envelope.task_id == "t-alp-e4-42"
    assert envelope.role == "reviewer"
    assert validate(envelope.model_dump(by_alias=True), roles_dir=ROLES_DIR) == envelope


def test_params_task_id_is_refused_in_favour_of_the_request_field(
    tmp_path: Path,
) -> None:
    """P2-1: ``params['task_id']`` is a refusal naming the one source of truth."""
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)
    request = RunRequest(
        task_id="t-real-task",
        role_id="screener",
        role_version=SCREENER_ROLE_VERSION,
        inputs=SCREENER_INPUTS,
        params={**PARAMS, "task_id": "t-other-task"},
        arm="A",
        input_schemas=SCREENER_INPUT_SCHEMAS,
    )

    with pytest.raises(ScopeViolation) as excinfo:
        adapter.run(
            request,
            lambda s: s.write(
                "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
            ),
        )

    assert excinfo.value.detail == (
        "{task_id} is bound from RunRequest.task_id; do not pass it in params"
    )
    # Refused before the handler: no run tree, no staging, no journal row.
    assert not (root / "runs").exists()
    assert not (workspace / "runs").exists()
    assert not (workspace / "audit" / "journal.jsonl").exists()


def test_dotdot_in_a_param_cannot_evade_deny_glob(tmp_path: Path) -> None:
    """P3-9: ``deny_glob`` is matched on the normalised destination too.

    ``{sub}`` is caller-supplied, so ``../../<ws>/audit`` walks the resolved
    row back into the denied ``audit/`` tree while the *raw* path string still
    reads as living under ``notes/``. Matching only the raw string would
    promote into the denylist; the normalised candidate catches it. The tag is
    the row's own basename (P2-4), so the ``..`` in the directory segment is
    what the refusals must see.
    """
    root, workspace = _seed_workspace(tmp_path)
    trap = {
        **AGENT_RECORD,
        "id": "deny-trap",
        "deny_glob": [f"workspaces/{_WS}/audit/**"],
        "outputs": [
            {
                "schema": "Review@1",
                "write_glob": "workspaces/{ws}/notes/{sub}/notes.json",
            }
        ],
    }
    (root / "roles" / "deny-trap.json").write_text(json.dumps(trap), encoding="utf-8")
    adapter = _adapter(root, workspace)
    request = RunRequest(
        task_id="t-deny-trap",
        role_id="deny-trap",
        role_version="2.1.0",
        inputs=(f"workspaces/{_WS}/literature/batch.json",),
        params={"ws": _WS, "sub": f"../../{_WS}/audit"},
        arm="A",
    )

    with pytest.raises(ScopeViolation) as excinfo:
        adapter.run(request, lambda s: s.write("notes.json", '{"forged": true}'))

    assert "deny_glob" in excinfo.value.detail
    assert not (workspace / "audit").exists()
    assert not (workspace / "notes").exists()


# ---------------------------------------------------------------------------
# P2-2: first declared action = success verb, last = failure verb
# ---------------------------------------------------------------------------


def test_three_action_role_journals_its_last_action_for_a_failed_run(
    tmp_path: Path,
) -> None:
    """P2-2: a non-OK run journals ``actions[-1]``, never an intermediate verb.

    ``roles/orchestrator.json`` declares
    ``['TASK_DISPATCHED', 'VERDICT_RECORDED', 'GATE_BLOCKED']``; the old
    ``actions[1]`` rule journaled ``VERDICT_RECORDED`` for an ``INVALID_OUTPUT``
    run. The record convention is first = success, last = failure.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    roles = tmp_path / "roles"
    shutil.copytree(ROLES_DIR, roles)
    record = json.loads((roles / "screener.json").read_text(encoding="utf-8"))
    record["audit"]["emit"] = [
        "SCREENING_COMPLETED",
        "SCREENING_WAIVED",
        "SCREENING_BLOCKED",
    ]
    (roles / "screener.json").write_text(json.dumps(record), encoding="utf-8")
    adapter = InProcessAdapter(root=root, workspace=workspace, roles_dir=roles)

    failed = adapter.run(_screener_request("t-three-fail", arm="A"), lambda s: None)
    assert failed.status is EnvelopeStatus.INVALID_OUTPUT
    row = json.loads(
        (workspace / "audit" / "journal.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[-1]
    )
    assert row["action"] == "SCREENING_BLOCKED"
    assert row["status"] == "INVALID_OUTPUT"

    ok = adapter.run(
        _screener_request("t-three-ok", arm="A"),
        lambda s: s.write(
            "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
        ),
    )
    assert ok.status is EnvelopeStatus.OK
    row = json.loads(
        (workspace / "audit" / "journal.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[-1]
    )
    assert row["action"] == "SCREENING_COMPLETED"
    assert row["status"] == "SUCCESS"


def test_shipped_roles_declare_distinct_first_and_last_emit_actions() -> None:
    """P2-2: the first/last convention holds for all twelve shipped records."""
    records = sorted(ROLES_DIR.glob("*.json"))
    assert len(records) == 12
    for path in records:
        record = json.loads(path.read_text(encoding="utf-8"))
        actions = record["audit"]["emit"]
        assert len(actions) >= 2, path.name
        assert actions[0] != actions[-1], path.name


# ---------------------------------------------------------------------------
# P2-3: ``run_role`` requires the enclosing root
# ---------------------------------------------------------------------------


def test_run_role_requires_a_root_containing_the_workspace(tmp_path: Path) -> None:
    """P2-3: no default root — it must be the tree the workspace lives under."""
    root, workspace = _seed_screener_workspace(tmp_path)

    def handler(session: RoleSession) -> None:
        session.write(
            "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
        )

    with pytest.raises(TypeError):
        run_role(  # type: ignore[call-arg]
            "in-process",
            _screener_request("t-no-root", arm="A"),
            handler,
            workspace=workspace,
            roles_dir=ROLES_DIR,
        )

    with pytest.raises(ScopeViolation) as excinfo:
        run_role(
            "in-process",
            _screener_request("t-none-root", arm="A"),
            handler,
            workspace=workspace,
            roles_dir=ROLES_DIR,
            root=None,
        )
    assert "root" in excinfo.value.detail
    assert "workspace" in excinfo.value.detail

    with pytest.raises(ScopeViolation) as excinfo:
        run_role(
            "in-process",
            _screener_request("t-outside-root", arm="A"),
            handler,
            workspace=workspace,
            roles_dir=ROLES_DIR,
            root=tmp_path / "elsewhere",
        )
    assert "not inside root" in excinfo.value.detail

    # Nothing was nested under the workspace and no run tree was created.
    assert not (workspace / "workspaces").exists()
    assert not (workspace / "runs").exists()
    assert not (root / "runs").exists()


# ---------------------------------------------------------------------------
# P3-4: caller-stated input schema names are attested verbatim
# ---------------------------------------------------------------------------


def test_no_input_role_attests_caller_supplied_names_verbatim(tmp_path: Path) -> None:
    """P3-4: a stated name is never replaced by ``"untyped"``.

    The role declares no input rows (so the adapter has no name authority), but
    the caller still states names positionally — position for position, they
    must reach the envelope unchanged. ``"untyped"`` is only for a caller that
    supplied no names at all.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    roles = tmp_path / "roles"
    shutil.copytree(ROLES_DIR, roles)
    record = json.loads((roles / "screener.json").read_text(encoding="utf-8"))
    record.pop("inputs")
    (roles / "screener.json").write_text(json.dumps(record), encoding="utf-8")
    adapter = InProcessAdapter(root=root, workspace=workspace, roles_dir=roles)
    stated = ("CallerStated@1", "CallerStated@2", "CallerStated@3")

    envelope = adapter.run(
        _screener_request("t-untyped-verbatim", arm="A", input_schemas=stated),
        lambda s: s.write(
            "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
        ),
    )

    assert envelope.status is EnvelopeStatus.OK
    assert [ref.schema_ for ref in envelope.inputs] == list(stated)
    assert "untyped" not in {ref.schema_ for ref in envelope.inputs}
    assert validate(envelope.model_dump(by_alias=True), roles_dir=roles) == envelope


# ---------------------------------------------------------------------------
# P3-5: no bare ``assert`` on the run path
# ---------------------------------------------------------------------------


def test_a_nameless_payload_is_a_typed_refusal_not_an_assertion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """P3-5: a broken ``_resolve_output_schema`` invariant refuses explicitly.

    ``python -O`` strips ``assert`` statements, which would let a ``(None,
    None)`` result fall through into ``_InvalidArtifact(message=None)``. The
    adapter must raise a typed :class:`ContractViolation` naming the invariant
    instead, and roll the run's promotion back (F3).
    """
    from scholar_harness.capabilities import adapter as adapter_module

    def nameless(policy: object, relative: str) -> tuple[None, None]:
        return None, None

    monkeypatch.setattr(adapter_module, "_resolve_output_schema", nameless)
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)

    with pytest.raises(ContractViolation) as excinfo:
        adapter.run(
            _screener_request("t-nameless", arm="A"),
            lambda s: s.write(
                "batch_001_decisions.json", json.dumps(_valid_decisions_payload("A"))
            ),
        )

    assert "_resolve_output_schema" in excinfo.value.detail
    assert not (
        workspace / "literature" / "screening" / "batch_001_decisions_A.json"
    ).exists(), "the failed construction must roll this run's promotion back"


# ---------------------------------------------------------------------------
# P2-4: a fully bound row binds only its own artifact (no first-match win)
# ---------------------------------------------------------------------------

#: Two *fixed* output rows (every placeholder is run-level) with distinct
#: filenames and the one payload schema the contract registers, so both rows can
#: cleanly produce an ``OK`` envelope with ``coverage {2,2}``.
TWO_FIXED_ROWS_RECORD = {
    **AGENT_RECORD,
    "id": "two-fixed-rows",
    "version": "2.1.0",
    "independence": {"blinded_from": [], "isolation": "none"},
    "read_glob": ["workspaces/{ws}/literature/**"],
    "outputs": [
        {
            "required": True,
            "schema": "ScreeningDecisions@1",
            "write_glob": "runs/{task_id}/packet.json",
        },
        {
            "required": True,
            "schema": "ScreeningDecisions@1",
            "write_glob": "runs/{task_id}/verdict.json",
        },
    ],
}


def _two_fixed_row_adapter(root: Path) -> InProcessAdapter:
    roles = root / "roles"
    roles.mkdir(parents=True)
    (roles / "two-fixed-rows.json").write_text(
        json.dumps(TWO_FIXED_ROWS_RECORD), encoding="utf-8"
    )
    (root / "workspaces" / _WS / "literature").mkdir(parents=True)
    return InProcessAdapter(
        root=root, workspace=root / "workspaces" / _WS, roles_dir=roles
    )


def _two_fixed_row_request(task: str = "t-two-rows") -> RunRequest:
    return RunRequest(
        task_id=task,
        role_id="two-fixed-rows",
        role_version="2.1.0",
        inputs=(),
        params=PARAMS,
        arm=None,
    )


def test_fixed_row_multi_output_role_promotes_each_row_to_its_own_file(
    tmp_path: Path,
) -> None:
    """P2-4: ``packet.json`` and ``verdict.json`` are two files, not one.

    The old "no remaining placeholders → bind anything" branch let the first
    fixed row swallow every artifact: writing ``verdict.json`` overwrote
    ``packet.json`` and the envelope still reported ``coverage {2,2}`` over a
    single file. Each fixed row must bind only its own basename.
    """
    root = tmp_path
    adapter = _two_fixed_row_adapter(root)
    first = _valid_decisions_payload("A")
    second = {**_valid_decisions_payload("A"), "batch_id": "batch_002"}

    def handler(session: RoleSession) -> None:
        session.write("packet.json", json.dumps(first))
        session.write("verdict.json", json.dumps(second))

    envelope = adapter.run(_two_fixed_row_request(), handler)

    packet = root / "runs" / "t-two-rows" / "packet.json"
    verdict = root / "runs" / "t-two-rows" / "verdict.json"
    assert packet.is_file(), "the packet row must reach its own destination"
    assert verdict.is_file(), "the verdict row must reach its own destination"
    assert packet != verdict
    assert packet.read_bytes() != verdict.read_bytes(), "two distinct payloads"
    assert json.loads(packet.read_text(encoding="utf-8"))["batch_id"] == "batch_001"
    assert json.loads(verdict.read_text(encoding="utf-8"))["batch_id"] == "batch_002"

    assert envelope.status is EnvelopeStatus.OK
    assert envelope.coverage is not None
    assert (envelope.coverage.expected, envelope.coverage.produced) == (2, 2)
    assert (
        validate(envelope.model_dump(by_alias=True), roles_dir=root / "roles")
        == envelope
    )


def test_the_same_destination_twice_in_one_run_is_refused(tmp_path: Path) -> None:
    """P2-4: one run never publishes two artifacts to one path."""
    root = tmp_path
    adapter = _two_fixed_row_adapter(root)
    first = json.dumps(_valid_decisions_payload("A"))
    second = json.dumps({**_valid_decisions_payload("A"), "batch_id": "batch_002"})

    def handler(session: RoleSession) -> None:
        session.write("packet.json", first)
        session.write("packet.json", second)

    with pytest.raises(ScopeViolation) as excinfo:
        adapter.run(_two_fixed_row_request("t-two-writes"), handler)

    detail = excinfo.value.detail
    assert "runs/t-two-writes/packet.json" in detail
    assert "already published" in detail
    assert "two artifacts to one path" in detail
    # The refusal lands before the second staging: the first artifact survives
    # with its own bytes rather than being silently replaced.
    packet = root / "runs" / "t-two-writes" / "packet.json"
    assert packet.is_file()
    assert packet.read_text(encoding="utf-8") == first
    assert not (root / "runs" / "t-two-writes" / "verdict.json").exists()


def test_an_artifact_tag_that_two_rows_bind_is_refused(tmp_path: Path) -> None:
    """P2-4: ambiguity is a refusal, never a first-match win.

    Two ``{stu}`` rows with different directories both bind
    ``SCI-01.json``: the destinations differ, so no load-time duplicate check
    catches it — the adapter must refuse and name the tag plus both candidate
    rows rather than silently choosing the first.
    """
    root, workspace = _seed_workspace(tmp_path)
    ambiguous = {
        **AGENT_RECORD,
        "id": "ambiguous-rows",
        "outputs": [
            {"schema": "Review@1", "write_glob": "workspaces/{ws}/a/{stu}.json"},
            {"schema": "Review@1", "write_glob": "workspaces/{ws}/b/{stu}.json"},
        ],
    }
    (root / "roles" / "ambiguous-rows.json").write_text(
        json.dumps(ambiguous), encoding="utf-8"
    )
    adapter = _adapter(root, workspace)
    request = RunRequest(
        task_id="t-ambiguous",
        role_id="ambiguous-rows",
        role_version="2.1.0",
        inputs=(f"workspaces/{_WS}/literature/batch.json",),
        params=PARAMS,
        arm="A",
    )

    with pytest.raises(ScopeViolation) as excinfo:
        adapter.run(request, lambda s: s.write("SCI-01.json", '{"v": 1}'))

    detail = excinfo.value.detail
    assert "SCI-01.json" in detail
    assert f"workspaces/{_WS}/a/{{stu}}.json" in detail
    assert f"workspaces/{_WS}/b/{{stu}}.json" in detail
    assert "ambiguous" in detail
    assert not (workspace / "a").exists()
    assert not (workspace / "b").exists()


def test_output_rows_that_resolve_to_one_destination_are_refused_at_load(
    tmp_path: Path,
) -> None:
    """P2-4: a record whose rows collapse onto one path is refused at load."""
    roles = tmp_path / "roles"
    roles.mkdir(parents=True)
    duplicate = {
        **AGENT_RECORD,
        "id": "duplicate-rows",
        "outputs": [
            {"schema": "Review@1", "write_glob": "runs/{task_id}/packet.json"},
            {"schema": "Review@1", "write_glob": "runs/{task_id}/packet.json"},
        ],
    }
    (roles / "duplicate-rows.json").write_text(json.dumps(duplicate), encoding="utf-8")
    with pytest.raises(ScopeViolation) as excinfo:
        load_role_policy(roles, "duplicate-rows")

    detail = excinfo.value.detail
    assert "duplicate-rows" in detail, "the refusal names the role"
    assert "runs/{task_id}/packet.json" in detail, "the refusal names the path"
    assert "same destination" in detail

    # Distinct raw rows can still collapse once a run-level param is bound.
    collapsing = {
        **AGENT_RECORD,
        "id": "collapsing-rows",
        "outputs": [
            {"schema": "Review@1", "write_glob": "runs/{task_id}/{name}.json"},
            {"schema": "Review@1", "write_glob": "runs/{task_id}/packet.json"},
        ],
    }
    (roles / "collapsing-rows.json").write_text(
        json.dumps(collapsing), encoding="utf-8"
    )
    policy = load_role_policy(roles, "collapsing-rows")
    with pytest.raises(ScopeViolation) as excinfo:
        policy.resolved({"task_id": "t-collapse", "name": "packet"})

    detail = excinfo.value.detail
    assert "collapsing-rows" in detail
    assert "runs/t-collapse/packet.json" in detail
    assert "same destination" in detail


def _orchestrator_request(task: str) -> RunRequest:
    """A request the shipped two-row ``roles/orchestrator.json`` accepts."""
    return RunRequest(
        task_id=task,
        role_id="orchestrator",
        role_version="2.0.0",
        inputs=(
            f"workspaces/{_WS}/protocol.json",
            f"workspaces/{_WS}/project.json",
        ),
        params=PARAMS,
        arm=None,
        input_schemas=("ExecutionPlan@1", "WorkspaceState@1"),
    )


def test_a_fixed_row_never_swallows_an_unknown_tag(tmp_path: Path) -> None:
    """P2-4: no first-match fallback for the shipped two-row orchestrator.

    ``roles/orchestrator.json`` declares ``runs/{task_id}/packet.json`` and
    ``runs/{task_id}/verdict.json``. Before the fix, ``notes.json`` bound the
    first fixed row and overwrote ``packet.json``; now it is un-bindable and
    ``verdict.json`` still reaches only its own row.
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = InProcessAdapter(root=root, workspace=workspace, roles_dir=ROLES_DIR)
    packet_payload = json.dumps({"row": "packet"})

    def handler(session: RoleSession) -> None:
        session.write("packet.json", packet_payload)
        session.write("notes.json", json.dumps({"row": "notes"}))

    with pytest.raises(ScopeViolation) as excinfo:
        adapter.run(_orchestrator_request("t-orch-fixed"), handler)

    detail = excinfo.value.detail
    assert "notes.json" in detail
    assert "no write_glob row" in detail, "no first-match fallback may bind it"
    assert "orchestrator" in detail
    packet = root / "runs" / "t-orch-fixed" / "packet.json"
    assert packet.read_text(encoding="utf-8") == packet_payload
    assert not (root / "runs" / "t-orch-fixed" / "notes.json").exists()
    assert not (root / "runs" / "t-orch-fixed" / "verdict.json").exists()

    # Positive control: the verdict row still binds its own basename.
    def both_rows(session: RoleSession) -> None:
        session.write("packet.json", packet_payload)
        session.write("verdict.json", json.dumps({"row": "verdict"}))

    adapter.run(_orchestrator_request("t-orch-both"), both_rows)
    packet = root / "runs" / "t-orch-both" / "packet.json"
    verdict = root / "runs" / "t-orch-both" / "verdict.json"
    assert json.loads(packet.read_text(encoding="utf-8"))["row"] == "packet"
    assert json.loads(verdict.read_text(encoding="utf-8"))["row"] == "verdict"


# ---------------------------------------------------------------------------
# P3-10: a label ending in '.' is refused before any directory exists
# ---------------------------------------------------------------------------


def test_task_label_with_trailing_dots_is_refused(tmp_path: Path) -> None:
    """P3-10: ``t-end.``/``t-end..`` alias or escape their own run directory.

    ``_LABEL_RE`` allows an interior/leading dot but Windows strips *trailing*
    dots from a path segment: ``t-end.`` silently aliases ``runs/t-end`` and
    ``t-end..`` walked out of it (a raw ``FileNotFoundError`` from the staging
    mkdir). Both must be typed refusals naming the field before ``runs/`` is
    created. (A bare reserved device name such as ``CON`` stays deferred.)
    """
    root, workspace = _seed_screener_workspace(tmp_path)
    adapter = _screener_adapter(root, workspace)

    for task in ("t-end.", "t-end.."):
        with pytest.raises(ScopeViolation) as excinfo:
            adapter.run(
                _screener_request(task, arm="A"),
                lambda s: s.write("batch_001_decisions.json", _decisions_blob("A")),
            )
        detail = excinfo.value.detail
        assert "RunRequest.task_id" in detail, detail
        assert task in detail
        assert "must not end with '.'" in detail

    assert not (workspace / "runs").exists()
    assert not (root / "runs").exists()
    assert not (workspace / "audit" / "journal.jsonl").exists()


# ---------------------------------------------------------------------------
# P3-11: ``workspace == root`` splits the journal from the artifacts
# ---------------------------------------------------------------------------


def test_run_role_refuses_a_workspace_equal_to_the_root(tmp_path: Path) -> None:
    """P3-11: equal paths pass ``is_relative_to`` but are not a project dir."""
    root, _workspace = _seed_screener_workspace(tmp_path)

    with pytest.raises(ScopeViolation) as excinfo:
        run_role(
            "in-process",
            _screener_request("t-root-eq", arm="A"),
            lambda s: None,
            workspace=root,
            roles_dir=ROLES_DIR,
            root=root,
        )

    detail = excinfo.value.detail
    assert "workspace" in detail
    assert "root" in detail
    assert str(root) in detail
    assert "not root itself" in detail
    assert not (root / "runs").exists()
    assert not (root / "audit" / "journal.jsonl").exists()


# ---------------------------------------------------------------------------
# T-ALP-D1: ``resolve_env`` binds the full skill vocabulary (spec 04 §1)
# ---------------------------------------------------------------------------

#: The nine ``{CLI:<short>}`` names a shipped skill uses. The registry
#: (``variables.CLI_SHORTS``) is the source of truth; this literal tuple is the
#: assertion, so extending the kit set is a deliberate edit here too.
CLI_SHORT_NAMES = (
    "agent",
    "bib",
    "graph",
    "harness",
    "pdf",
    "protocol",
    "rag",
    "search",
    "verify",
)

#: The eight kits that own a ``{KIT_ROOT:<short>}`` binding (the harness is a
#: CLI, not a kit: ``tools/scholar-harness`` does not exist).
KIT_SHORT_NAMES = (
    "agent",
    "bib",
    "graph",
    "pdf",
    "protocol",
    "rag",
    "search",
    "verify",
)


def _shipped_skill_names() -> tuple[str, ...]:
    return tuple(
        sorted(
            entry.name
            for entry in (ROOT / ".agents" / "skills").iterdir()
            if entry.is_dir() and (entry / "SKILL.md").is_file()
        )
    )


def _skill_names_for_surface(surface: str, workspace: Path) -> set[str]:
    """The ``SKILL_DIR`` vocabulary the documented surface owns.

    The two surfaces resolve skills differently (``ENV_BINDING_TABLE``):
    the application prefers a workspace-local copy and otherwise uses the
    project's one resolution order (``NEXUS_SKILLS_SRC`` → wheel bundle → repo
    checkout), so a wheel-only install legitimately omits the dev-only
    ``pull-request-gate`` skill; the dev-loop surface always reads the repo
    checkout. Deriving the expectation from the same documented roots — rather
    than from ``ROOT/.agents/skills`` alone — is what makes the assertion
    valid in both environments.
    """
    roots: list[Path] = []
    if surface == "opencode":
        roots.append(ROOT / ".agents" / "skills")
    else:
        roots.append(workspace / ".agents" / "skills")
        fallback = resolve_skills_root()
        if fallback is not None:
            roots.append(fallback)
    names: set[str] = set()
    for root in roots:
        if not root.is_dir():
            continue
        names |= {
            entry.name
            for entry in root.iterdir()
            if entry.is_dir() and (entry / "SKILL.md").is_file()
        }
    return names


def _expected_env_keys(surface: str, workspace: Path) -> set[str]:
    """The exact key set an adapter env must carry (never a subset check)."""
    keys = {f"CLI:{short}" for short in CLI_SHORT_NAMES}
    keys |= {f"KIT_ROOT:{short}" for short in KIT_SHORT_NAMES}
    keys |= {f"SKILL_DIR:{skill}" for skill in _skill_names_for_surface(surface, workspace)}
    return keys | {"WORKSPACE", "CACHE", "CONFIG", "PY"}


def _resolve_env(surface: str, workspace: Path, config: Path) -> dict[str, str]:
    if surface == "in-process":
        adapter = InProcessAdapter(root=ROOT, workspace=workspace, roles_dir=ROLES_DIR)
    else:
        adapter = OpencodeAdapter(workspace=workspace, roles_dir=ROLES_DIR)
    return adapter.resolve_env(workspace=workspace, config=config)


def _resolved_kit_package_dir(short: str) -> Path:
    """The package directory the import system reports for a kit.

    Normally ``Path(find_spec(...).origin).parent``; ``scholar_agent`` is a
    namespace package (it ships no ``__init__.py`` and has ``origin is None``),
    so ``submodule_search_locations`` is its package directory.
    """
    spec = importlib.util.find_spec(KIT_MODULES[short])
    assert spec is not None, f"{KIT_MODULES[short]} is not importable"
    if spec.origin is not None:
        return Path(spec.origin).parent.resolve()
    locations = list(spec.submodule_search_locations or ())
    assert locations, f"{KIT_MODULES[short]} has neither origin nor search locations"
    return Path(locations[0]).resolve()


def test_binding_vocabulary_matches_the_registry() -> None:
    """The literal assertions above cannot drift from the registry."""
    assert set(CLI_SHORT_NAMES) == set(CLI_SHORTS)
    assert set(KIT_SHORT_NAMES) == set(KIT_SHORTS)
    assert len(_shipped_skill_names()) == 14, (
        "the shipped skill set changed; update the expectation deliberately"
    )


@pytest.mark.parametrize("surface", ["in-process", "opencode"])
def test_resolve_env_binds_the_exact_key_set(surface: str, tmp_path: Path) -> None:
    """Criterion 1: every family, exact keys — no subset match."""
    missing = [
        short
        for short in KIT_SHORT_NAMES
        if importlib.util.find_spec(f"scholar_{short}") is None
    ]
    assert missing == [], (
        "kits not importable in this environment, so KIT_ROOT cannot be bound "
        f"(install them with scripts/install_plugins.py): {missing}"
    )
    workspace = tmp_path / "workspaces" / _WS
    workspace.mkdir(parents=True)
    config = tmp_path / "plugins.json"

    env = _resolve_env(surface, workspace, config)

    assert set(env) == _expected_env_keys(surface, workspace)
    assert all(isinstance(value, str) and value for value in env.values())
    assert env["WORKSPACE"] == str(workspace)
    assert env["CONFIG"] == str(config)
    for short in KIT_SHORT_NAMES:
        assert Path(env[f"KIT_ROOT:{short}"]).is_dir(), (surface, short)
    for skill in _skill_names_for_surface(surface, workspace):
        assert Path(env[f"SKILL_DIR:{skill}"]).is_dir(), (surface, skill)
    if surface == "in-process":
        assert env["CLI:harness"] == "scholar-harness"
        assert env["PY"] == sys.executable
        assert "uv" not in env["PY"]
    else:
        assert env["CLI:harness"] == "uv run scholar-harness"
        assert env["PY"] == "uv run python"


@pytest.mark.parametrize("surface", ["in-process", "opencode"])
def test_kit_root_binds_the_resolved_package_not_a_hardcoded_path(
    surface: str, tmp_path: Path
) -> None:
    """The app ``KIT_ROOT`` is the resolved package directory, not ``tools/``.

    Equality with the import system's answer (not merely ``is_dir``) is what
    fails a hardcoded ``tools/scholar-<short>`` implementation.
    """
    workspace = tmp_path / "workspaces" / _WS
    workspace.mkdir(parents=True)
    env = _resolve_env(surface, workspace, tmp_path / "plugins.json")

    for short in KIT_SHORT_NAMES:
        package_dir = _resolved_kit_package_dir(short)
        bound = Path(env[f"KIT_ROOT:{short}"])
        if surface == "in-process":
            assert bound == package_dir, (short, bound, package_dir)
        else:
            # Dev binds the vendored checkout, the single shared template.
            assert bound == ROOT / DEV_KIT_ROOT_TEMPLATE.replace("{{kit}}", short)
            # pytest's ``pythonpath`` imports editable kits from inside the
            # vendored checkout; a wheel/venv install (even the repo's own
            # ``.venv``) is not a checkout import and is not constrained by
            # this dev binding.
            if package_dir.is_relative_to(ROOT / "tools"):
                assert package_dir.is_relative_to(bound), (short, package_dir, bound)


def test_both_adapters_reference_the_shared_binding_table() -> None:
    """The key table lives once; each ``resolve_env`` docstring points at it."""
    for doc in (
        InProcessAdapter.resolve_env.__doc__,
        OpencodeAdapter.resolve_env.__doc__,
    ):
        assert doc is not None
        assert "ENV_BINDING_TABLE" in doc
    for family in (
        "CLI:<short>",
        "KIT_ROOT:<short>",
        "SKILL_DIR:<skill>",
        "WORKSPACE",
        "CACHE",
        "CONFIG",
        "PY",
    ):
        assert family in ENV_BINDING_TABLE
    # The app caveat is part of the contract text, not just a docstring aside.
    assert "package" in ENV_BINDING_TABLE
    assert "not fully resolved" in ENV_BINDING_TABLE


@pytest.mark.parametrize("surface", ["in-process", "opencode"])
def test_resolve_env_is_pure(
    surface: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Criterion 6: stable across calls, no ``os.environ`` mutation."""
    monkeypatch.delenv("NEXUS_RECON_ROOT", raising=False)
    workspace = tmp_path / "workspaces" / _WS
    workspace.mkdir(parents=True)
    config = tmp_path / "plugins.json"
    before = dict(os.environ)
    tree_before = sorted(
        str(path.relative_to(workspace)) for path in workspace.rglob("*")
    )

    first = _resolve_env(surface, workspace, config)
    second = _resolve_env(surface, workspace, config)

    assert first == second
    assert (
        sorted(str(path.relative_to(workspace)) for path in workspace.rglob("*"))
        == tree_before
    ), "resolve_env wrote into the workspace it only describes"
    assert dict(os.environ) == before
    assert not any(key.startswith("CLI:") for key in os.environ)
    for key in ("WORKSPACE", "CACHE", "CONFIG", "PY"):
        assert os.environ.get(key) == before.get(key)


@pytest.mark.parametrize("surface", ["in-process", "opencode"])
def test_cache_follows_nexus_recon_root_outside_the_workspace(
    surface: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Criterion 6: ``NEXUS_RECON_ROOT`` wins and is not forced under the ws."""
    workspace = tmp_path / "workspaces" / _WS
    workspace.mkdir(parents=True)
    outside = tmp_path / "shared-recon-cache"
    outside.mkdir()
    monkeypatch.setenv("NEXUS_RECON_ROOT", str(outside))

    env = _resolve_env(surface, workspace, tmp_path / "plugins.json")

    assert env["CACHE"] == str(outside)
    assert Path(env["CACHE"]) == outside
    assert not Path(env["CACHE"]).is_relative_to(workspace)

    # Default (no override) stays the surface's own cache root.
    monkeypatch.delenv("NEXUS_RECON_ROOT")
    default = _resolve_env(surface, workspace, tmp_path / "plugins.json")["CACHE"]
    if surface == "in-process":
        assert default == str(workspace.parent / ".cache")
    else:
        assert default == str(ROOT / ".cache")


def test_unimportable_kit_is_absent_and_render_names_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Negative: a kit that cannot be imported is absent, not invented."""
    from scholar_harness.capabilities import adapter as adapter_module

    monkeypatch.setitem(
        adapter_module.KIT_MODULES, "rag", "scholar_package_that_does_not_exist"
    )
    workspace = tmp_path / "workspaces" / _WS
    workspace.mkdir(parents=True)

    env = _resolve_env("in-process", workspace, tmp_path / "plugins.json")

    assert "KIT_ROOT:rag" not in env
    assert "CLI:rag" in env, "the CLI family is independent of the kit package"
    with pytest.raises(ValueError) as excinfo:
        render("Run {KIT_ROOT:rag}/apply.py", Preamble.from_env(env))
    assert "{KIT_ROOT:rag}" in str(excinfo.value)
    assert not isinstance(excinfo.value, KeyError)


def test_missing_skill_directory_is_absent_and_render_names_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Negative: a skill directory that does not exist is absent."""
    from scholar_harness.capabilities import adapter as adapter_module

    monkeypatch.setattr(adapter_module, "resolve_skills_root", lambda: None)
    workspace = tmp_path / "workspaces" / _WS
    workspace.mkdir(parents=True)

    env = _resolve_env("in-process", workspace, tmp_path / "plugins.json")

    assert not any(key.startswith("SKILL_DIR:") for key in env)
    with pytest.raises(ValueError) as excinfo:
        render(
            "{SKILL_DIR:workspace-manager}/scripts/log_event.py",
            Preamble.from_env(env),
        )
    assert "{SKILL_DIR:workspace-manager}" in str(excinfo.value)


def test_workspace_local_skill_dir_wins(tmp_path: Path) -> None:
    """The app surface prefers an ``init``-scaffolded workspace skill copy."""
    workspace = tmp_path / "workspaces" / _WS
    local = workspace / ".agents" / "skills" / "workspace-manager"
    local.mkdir(parents=True)
    (local / "SKILL.md").write_text("# workspace-manager\n", encoding="utf-8")

    env = _resolve_env("in-process", workspace, tmp_path / "plugins.json")

    assert env["SKILL_DIR:workspace-manager"] == str(local)
    assert set(env) == _expected_env_keys("in-process", workspace)


def test_resolve_env_constructor_overrides_win(tmp_path: Path) -> None:
    """A host application can pin any single binding (constructor ``env``)."""
    workspace = tmp_path / "workspaces" / _WS
    workspace.mkdir(parents=True)
    config = tmp_path / "plugins.json"
    adapter = InProcessAdapter(
        root=ROOT,
        workspace=workspace,
        roles_dir=ROLES_DIR,
        env={"CACHE": "/pinned/cache"},
    )

    env = adapter.resolve_env(workspace=workspace, config=config)

    assert env["CACHE"] == "/pinned/cache"
    assert set(env) == _expected_env_keys("in-process", workspace)


def test_opencode_resolve_env_constructor_overrides_win(tmp_path: Path) -> None:
    """The dev adapter honours the same constructor ``env`` seam."""
    workspace = tmp_path / "workspaces" / _WS
    workspace.mkdir(parents=True)
    adapter = OpencodeAdapter(
        workspace=workspace,
        roles_dir=ROLES_DIR,
        env={"WORKSPACE": "/pinned/ws", "CACHE": "/pinned/cache"},
    )

    env = adapter.resolve_env(workspace=workspace, config=tmp_path / "plugins.json")

    assert env["WORKSPACE"] == "/pinned/ws"
    assert env["CACHE"] == "/pinned/cache"
    assert set(env) == _expected_env_keys("opencode", workspace)
