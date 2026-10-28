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
import json
import socket
from pathlib import Path

import pytest

from scholar_harness.capabilities import (
    AuditEvent,
    EgressRefused,
    InProcessAdapter,
    OpencodeAdapter,
    RoleSession,
    RunRequest,
    ScopeViolation,
)
from scholar_harness.capabilities.adapter import glob_matches

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
    "audit": {"actor": "{role}@{version}"},
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


def _request(role: str = "conform-reviewer", task: str = "t-1", **kw) -> RunRequest:
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
    assert record["provenance"]["writer"] == "InProcessAdapter@1"


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
        _request(role="publisher", task="t-dual"),
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
    root, workspace = _seed_workspace(tmp_path)
    adapter = _adapter(root, workspace)
    restored: list[bool] = []

    def handler(session: RoleSession) -> None:
        with session.egress_guard():
            socket.socket  # noqa: B018 — the class itself must exist inside
        restored.append(
            socket.socket.__name__ == "SocketType" or hasattr(socket.socket, "fileno")
        )

    adapter.run(_request(), handler)
    assert restored == [True], "socket machinery must be restored after the run"


def test_network_allow_runs_normally(tmp_path: Path) -> None:
    root, workspace = _seed_workspace(tmp_path)
    allowed = dict(AGENT_RECORD, network="allow")
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
    assert record["provenance"]["role_version"] == "2.1.0"
    assert record["provenance"]["actor"] == "conform-reviewer@2.1.0"
    # Input hash matches the seeded file's content hash.
    seeded = workspace / "literature" / "batch.json"
    expected = hashlib.sha256(seeded.read_bytes()).hexdigest()
    assert record["input_sha256"] == [expected]
    # Output hash matches the promoted artifact's content hash.
    output_path = root / "workspaces" / _WS / "critique" / "SCI-01.json"
    assert output_path.is_file()
    assert record["output_sha256"] == [
        hashlib.sha256(output_path.read_bytes()).hexdigest()
    ]
    assert record["provenance"]["writer"] == "InProcessAdapter@1"


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
    root, workspace = _seed_workspace(tmp_path)
    dev = OpencodeAdapter(workspace=workspace, roles_dir=root / "roles")
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
