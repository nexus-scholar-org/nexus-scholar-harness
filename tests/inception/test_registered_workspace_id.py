"""Registered workspace identity: mint once at inception, record, never re-derive.

The frozen Contract v1 identifier registry admits exactly one registered form for
a workspace (``WSP-<opaque>``). A human slug such as ``evidence-synthesis`` is a
label, not an identity. These tests pin the three halves of that rule:

* inception mints a registered identity and records it in ``project.json``;
* the identity is stable across reads and re-scaffolds (minted ONCE);
* reading the recorded identity refuses cleanly when it is absent, never
  substituting the slug or minting at use time. (The Stage 6 indexing tests
  that also covered this left with ``scholar_rag``, H-remove-rag-verify.)
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from types import ModuleType

import pytest

from scholar_harness.inception.genesis import (
    mint_registered_workspace_id,
    recorded_or_minted_workspace_id,
    scaffold_raw_project,
)
from scholar_harness.contracts.identifiers import (
    IdentifierKind,
    validate_identifier,
)
from scholar_harness.orchestrator import ResearchOrchestrator
from scholar_harness.workspace.errors import RegisteredWorkspaceIdentityMissingError

REGISTERED_WORKSPACE_ID = re.compile(r"^WSP-[0-9a-f]{32}$")


def _manifest(ws: Path) -> dict:
    return json.loads((ws / "project.json").read_text(encoding="utf-8"))


def _load_init_project() -> ModuleType:
    """Load the workspace-manager scaffold script the way inception invokes it."""
    path = (
        Path(__file__).resolve().parents[2]
        / ".agents"
        / "skills"
        / "workspace-manager"
        / "scripts"
        / "init_project.py"
    )
    spec = importlib.util.spec_from_file_location("ws_init_project", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# 1. Inception mints and records
# ---------------------------------------------------------------------------


def test_mint_shape_is_a_registered_identifier():
    """The minted value satisfies the frozen registry, not just our regex."""
    value = mint_registered_workspace_id()
    assert REGISTERED_WORKSPACE_ID.fullmatch(value), value
    assert validate_identifier(IdentifierKind.WORKSPACE, value) == value


def test_mints_are_distinct():
    assert len({mint_registered_workspace_id() for _ in range(16)}) == 16


def test_raw_scaffold_records_registered_workspace_id(tmp_path):
    """P7.3 ``nexus-scholar init <folder>``: identity minted and recorded."""
    ws = scaffold_raw_project(
        tmp_path / "study",
        title="Evidence Synthesis",
        slug="evidence-synthesis",
        paradigm="",
        rqs=[],
    )
    manifest = _manifest(ws)
    recorded = manifest["registered_workspace_id"]
    assert REGISTERED_WORKSPACE_ID.fullmatch(recorded), recorded
    assert validate_identifier(IdentifierKind.WORKSPACE, recorded) == recorded
    # project_id stays the human label and is NOT the identity.
    assert manifest["project_id"] == "evidence-synthesis"
    assert recorded != manifest["project_id"]


def test_workspace_manager_writer_records_registered_workspace_id(tmp_path):
    """The other project.json writer must record the same shape."""
    module = _load_init_project()
    ws = module.init_project(
        workspace_root=tmp_path, title="Evidence Synthesis", slug="evidence-synthesis"
    )
    recorded = _manifest(ws)["registered_workspace_id"]
    assert REGISTERED_WORKSPACE_ID.fullmatch(recorded), recorded
    assert _manifest(ws)["project_id"] == "evidence-synthesis"


# ---------------------------------------------------------------------------
# 2. Minted ONCE: stable across reads and re-scaffolds
# ---------------------------------------------------------------------------


def test_identity_is_stable_across_repeated_reads(tmp_path):
    """Re-reading project.json must never regenerate the identity."""
    ws = scaffold_raw_project(
        tmp_path / "study",
        title="Evidence Synthesis",
        slug="evidence-synthesis",
        paradigm="",
        rqs=[],
    )
    first = _manifest(ws)["registered_workspace_id"]
    for _ in range(5):
        assert _manifest(ws)["registered_workspace_id"] == first
    # And a second read through the orchestrator's accessor agrees.
    assert ResearchOrchestrator(ws).recorded_workspace_id() == first


def test_rescaffolding_does_not_reidentify_a_workspace(tmp_path):
    """Re-scaffolding reuses the recorded id instead of minting a second one.

    Otherwise artifacts already accepted under the old id would stop sharing a
    workspace.
    """
    ws = tmp_path / "study"
    scaffold_raw_project(
        ws, title="Evidence Synthesis", slug="evidence-synthesis", paradigm="", rqs=[]
    )
    first = _manifest(ws)["registered_workspace_id"]

    scaffold_raw_project(
        ws, title="Evidence Synthesis", slug="evidence-synthesis", paradigm="", rqs=[]
    )
    assert _manifest(ws)["registered_workspace_id"] == first

    module = _load_init_project()
    module.init_project(
        workspace_root=tmp_path / "wm",
        title="Evidence Synthesis",
        slug="evidence-synthesis",
    )
    wm_ws = tmp_path / "wm" / "workspaces" / "evidence-synthesis"
    wm_first = _manifest(wm_ws)["registered_workspace_id"]
    module.init_project(
        workspace_root=tmp_path / "wm",
        title="Evidence Synthesis",
        slug="evidence-synthesis",
    )
    assert _manifest(wm_ws)["registered_workspace_id"] == wm_first


def test_recorded_or_minted_mints_only_when_absent(tmp_path):
    assert recorded_or_minted_workspace_id(tmp_path / "missing").startswith("WSP-")
    ws = tmp_path / "study"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"registered_workspace_id": "WSP-" + "a" * 32})
    )
    assert recorded_or_minted_workspace_id(ws) == "WSP-" + "a" * 32


def test_sync_state_preserves_the_recorded_identity(tmp_path):
    """`scholar-harness sync` must not drop the recorded identity."""
    ws = scaffold_raw_project(
        tmp_path / "study",
        title="Evidence Synthesis",
        slug="evidence-synthesis",
        paradigm="",
        rqs=[],
    )
    recorded = _manifest(ws)["registered_workspace_id"]
    ResearchOrchestrator(ws).sync_state()
    assert _manifest(ws)["registered_workspace_id"] == recorded


def test_audit_logging_preserves_the_recorded_identity(tmp_path):
    """The workspace-manager audit refresh is a read-modify-write, so it keeps
    the recorded id instead of rebuilding the manifest."""
    ws = scaffold_raw_project(
        tmp_path / "study",
        title="Evidence Synthesis",
        slug="evidence-synthesis",
        paradigm="",
        rqs=[],
    )
    recorded = _manifest(ws)["registered_workspace_id"]

    scripts = (
        Path(__file__).resolve().parents[2]
        / ".agents"
        / "skills"
        / "workspace-manager"
        / "scripts"
    )
    spec = importlib.util.spec_from_file_location(
        "ws_log_event", scripts / "log_event.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.log_project_event(
        project_path_or_slug=ws,
        action="PROJECT_INITIALIZED",
        agent_or_tool="test",
        description="probe",
    )
    assert _manifest(ws)["registered_workspace_id"] == recorded


# ---------------------------------------------------------------------------
# 3. The recorded identity is read, and refused when it is absent
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("field", "expect"),
    [
        (None, "records no 'registered_workspace_id'"),
        ("evidence-synthesis", "not a registered workspace identity"),
    ],
    ids=["absent", "unregistered-slug-in-workspace-limb"],
)
def test_stage6_refuses_without_a_recorded_identity(tmp_path, field, expect):
    """A pre-registration workspace fails closed, naming the missing field."""
    ws = tmp_path / "study"
    ws.mkdir()
    manifest = {"project_id": "evidence-synthesis"}
    if field is not None:
        manifest["registered_workspace_id"] = field
    (ws / "project.json").write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(RegisteredWorkspaceIdentityMissingError) as excinfo:
        ResearchOrchestrator(ws).recorded_workspace_id()

    message = str(excinfo.value)
    assert expect in message
    # The refusal must name the field and point at the fix, not crash generically.
    assert "registered_workspace_id" in message
    assert "project.json" in message
    # It must not have invented a substitute.
    assert (
        "WSP-"
        not in message.replace("WSP-<32 lowercase hex>", "").replace("WSP-<32 hex>", "")
        or "not a registered workspace identity" in message
    )


def test_refusal_names_the_slug_it_declined_to_use(tmp_path):
    """The message shows the slug that was available but is not an identity."""
    ws = tmp_path / "study"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"project_id": "evidence-synthesis"}), encoding="utf-8"
    )
    with pytest.raises(RegisteredWorkspaceIdentityMissingError) as excinfo:
        ResearchOrchestrator(ws).recorded_workspace_id()
    assert "evidence-synthesis" in str(excinfo.value)


# ---------------------------------------------------------------------------
# 4. ONE policy in BOTH project.json writers
# ---------------------------------------------------------------------------
#
# ``genesis.scaffold_raw_project`` and the workspace-manager ``init_project.py``
# both write ``project.json``, and a workspace can be created by either. If they
# disagree, the same workspace gets a different identity depending on which
# creator ran -- so these tests drive BOTH over the SAME cases and require the
# SAME outcome. Each module keeps its own typed error (the skill script must stay
# importable standalone), so the shared contract asserted here is the class NAME
# plus the policy outcome, not object identity.

_CREATORS = ("genesis", "init_project")


def _creator(tmp_path: Path, which: str):
    """Return ``(resolver, typed_error, expected_error_name)`` for one creator."""
    if which == "genesis":
        from scholar_harness.inception import genesis

        return (
            genesis.recorded_or_minted_workspace_id,
            genesis.RegisteredWorkspaceIdentityMissingError,
            "RegisteredWorkspaceIdentityMissingError",
        )
    module = _load_init_project()
    return (
        module.recorded_or_minted_workspace_id,
        module.RegisteredWorkspaceIdentityMissingError,
        "RegisteredWorkspaceIdentityMissingError",
    )


def _write_manifest_state(ws: Path, raw: str | None) -> None:
    ws.mkdir(exist_ok=True)
    if raw is not None:
        (ws / "project.json").write_text(raw, encoding="utf-8")


@pytest.mark.parametrize("which", _CREATORS)
def test_both_creators_reuse_a_valid_recorded_identity(tmp_path, which):
    """The one positive case: an already-recorded identity is reused verbatim."""
    resolver, _, _ = _creator(tmp_path, which)
    ws = tmp_path / "study"
    recorded = "WSP-" + "a" * 32
    _write_manifest_state(ws, json.dumps({"registered_workspace_id": recorded}))
    assert resolver(ws) == recorded


@pytest.mark.parametrize("which", _CREATORS)
def test_both_creators_mint_when_no_identity_was_ever_recorded(tmp_path, which):
    """Minting is allowed only where there is no recorded identity to lose."""
    resolver, _, _ = _creator(tmp_path, which)

    # No manifest at all.
    missing = tmp_path / "missing"
    assert REGISTERED_WORKSPACE_ID.fullmatch(resolver(missing))

    # A readable manifest that never recorded an identity.
    ws = tmp_path / "study"
    _write_manifest_state(ws, json.dumps({"project_id": "evidence-synthesis"}))
    minted = resolver(ws)
    assert REGISTERED_WORKSPACE_ID.fullmatch(minted)
    assert minted != "evidence-synthesis"

    # An explicit JSON null is "no value recorded", not a recorded value to
    # preserve: there is no identity to lose, so both writers mint here rather
    # than refusing a manifest that simply never held one.
    null_ws = tmp_path / "null-study"
    _write_manifest_state(null_ws, json.dumps({"registered_workspace_id": None}))
    assert REGISTERED_WORKSPACE_ID.fullmatch(resolver(null_ws))


@pytest.mark.parametrize(
    ("raw", "must_name"),
    [
        (
            json.dumps({"registered_workspace_id": "evidence-synthesis"}),
            "evidence-synthesis",
        ),
        (
            json.dumps({"registered_workspace_id": "WSP-legacy-workspace-1"}),
            "WSP-legacy-workspace-1",
        ),
        (json.dumps({"registered_workspace_id": "WSP-" + "Z" * 32}), "WSP-" + "Z" * 32),
        (json.dumps({"registered_workspace_id": "WSP-" + "a" * 31}), "WSP-" + "a" * 31),
        (json.dumps({"registered_workspace_id": 42}), "42"),
        ("{not json", "project.json"),
        (json.dumps([1, 2, 3]), "project.json"),
    ],
    ids=[
        "human-slug",
        "legacy-non-hex-wsp",
        "non-hex-32",
        "short-hex",
        "not-a-string",
        "corrupt-json",
        "not-an-object",
    ],
)
@pytest.mark.parametrize("which", _CREATORS)
def test_both_creators_refuse_rather_than_reidentify(tmp_path, which, raw, must_name):
    """Recorded-but-unusable identity -> typed refusal, in BOTH writers.

    Minting over recorded state is silent re-identification: artifacts already
    accepted under the old id would stop sharing a workspace. Each refusal names
    the offending value (or the file) so the operator can fix it instead of
    guessing why two runs disagree.
    """
    resolver, error, error_name = _creator(tmp_path, which)
    ws = tmp_path / "study"
    _write_manifest_state(ws, raw)

    assert (
        error.__name__ == error_name == ("RegisteredWorkspaceIdentityMissingError")
    ), "both creators must use the same typed refusal name"

    with pytest.raises(error) as excinfo:
        resolver(ws)

    message = str(excinfo.value)
    # The refusal names the offending value (or the file) so the operator can act,
    # and never hands back a fresh identity instead.
    assert must_name in message
    assert "WSP-" + "a" * 32 not in message


@pytest.mark.parametrize("which", _CREATORS)
def test_both_creators_reach_the_same_verdict_on_every_case(tmp_path, which):
    """One table, both writers, identical verdicts -- the anti-drift assertion.

    This is the test that would fail if either copy of the policy were edited
    without the other, which is exactly the drift the restated copy risks.
    """
    resolver, error, _ = _creator(tmp_path, which)
    verdict = []
    for raw in (
        json.dumps({"registered_workspace_id": "WSP-" + "a" * 32}),
        json.dumps({"project_id": "evidence-synthesis"}),
        json.dumps({"registered_workspace_id": "evidence-synthesis"}),
        json.dumps({"registered_workspace_id": "WSP-legacy-workspace-1"}),
        "{not json",
        None,
    ):
        ws = tmp_path / f"case-{len(verdict)}"
        _write_manifest_state(ws, raw) if raw is not None else ws.mkdir(parents=True)
        try:
            value = resolver(ws)
        except error as exc:
            verdict.append(("refuse", error.__name__ in type(exc).__name__))
        else:
            verdict.append(("mint" if value != "WSP-" + "a" * 32 else "reuse", True))
    assert verdict == [
        ("reuse", True),
        ("mint", True),
        ("refuse", True),
        ("refuse", True),
        ("refuse", True),
        ("mint", True),
    ]


def test_unreadable_manifest_refuses_rather_than_guessing(tmp_path):
    ws = tmp_path / "study"
    ws.mkdir()
    (ws / "project.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(RegisteredWorkspaceIdentityMissingError) as excinfo:
        ResearchOrchestrator(ws).recorded_workspace_id()
    assert "cannot read the recorded workspace identity" in str(excinfo.value)


def test_missing_project_json_refuses(tmp_path):
    ws = tmp_path / "study"
    ws.mkdir()
    with pytest.raises(RegisteredWorkspaceIdentityMissingError):
        ResearchOrchestrator(ws).recorded_workspace_id()
