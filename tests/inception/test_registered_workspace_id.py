"""Registered workspace identity: mint once at inception, record, never re-derive.

The frozen Contract v1 identifier registry admits exactly one registered form for
a workspace (``WSP-<opaque>``). A human slug such as ``evidence-synthesis`` is a
label, not an identity, and the typed indexing surface refuses it. These tests pin
the three halves of that rule:

* inception mints a registered identity and records it in ``project.json``;
* the identity is stable across reads and re-scaffolds (minted ONCE);
* Stage 6 states the recorded identity and refuses cleanly when it is absent,
  never substituting the slug or minting at use time.
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
from scholar_harness.orchestrator import (
    RegisteredWorkspaceIdentityMissingError,
    ResearchOrchestrator,
)

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
# 3. Stage 6 records the identity, and refuses when it is absent
# ---------------------------------------------------------------------------


def test_stage6_request_states_the_recorded_identity(tmp_path, monkeypatch):
    """The built typed request carries the recorded WSP id, not the slug."""
    ws = scaffold_raw_project(
        tmp_path / "study",
        title="Evidence Synthesis",
        slug="evidence-synthesis",
        paradigm="",
        rqs=[],
    )
    recorded = _manifest(ws)["registered_workspace_id"]
    orch = ResearchOrchestrator(ws)

    captured: list[object] = []

    class _Indexer:
        collection_name = "scholar_docs"
        embedder_kwargs = {"provider": "mock", "model_name": None}

        def index_markdown(self, text, request=None):
            captured.append(request)
            return []

        def get_collection_count(self):
            return 0

    (ws / "audit").mkdir(exist_ok=True)
    (ws / "extracted").mkdir(exist_ok=True)
    (ws / "extracted" / "SCI-000001.md").write_text("# t\n\nbody\n", encoding="utf-8")
    (ws / "audit" / "artifact_registry.json").write_text(json.dumps({"artifacts": {}}))

    orch._index_accepted_documents(
        indexer=_Indexer(),
        workspace_id=orch.recorded_workspace_id(),
        inc_docs=[{"workspace_id": "SCI-000001"}],
        ext_dir=ws / "extracted",
    )
    # No accepted parent -> refused, so nothing was indexed; the identity still
    # had to be readable and registered for the request to be constructible.
    assert captured == []
    assert recorded != "evidence-synthesis"

    # With a recorded parent, the request states the recorded id verbatim.
    payload = {
        "data": {
            "decisions": [
                {
                    "study_id": "SCI-000001",
                    "decision": "INCLUDE",
                    "decision_id": "SCR-" + "1" * 32,
                }
            ]
        }
    }
    (ws / "audit" / "decisions.json").write_text(json.dumps(payload), encoding="utf-8")
    (ws / "audit" / "artifact_registry.json").write_text(
        json.dumps(
            {
                "artifacts": {
                    "ART-" + "1" * 32: {
                        "artifact_type": "screening_decisions",
                        "path": "audit/decisions.json",
                        "sha256": "sha256:" + "b" * 64,
                    }
                }
            }
        )
    )
    orch._index_accepted_documents(
        indexer=_Indexer(),
        workspace_id=orch.recorded_workspace_id(),
        inc_docs=[{"workspace_id": "SCI-000001"}],
        ext_dir=ws / "extracted",
    )
    assert len(captured) == 1
    assert captured[0].workspace_id == recorded


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
    (ws / "project.json").write_text(json.dumps({"project_id": "evidence-synthesis"}))
    with pytest.raises(RegisteredWorkspaceIdentityMissingError) as excinfo:
        ResearchOrchestrator(ws).recorded_workspace_id()
    assert "evidence-synthesis" in str(excinfo.value)


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
