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
from scholar_harness import orchestrator as orch_module
from scholar_harness.contracts.identifiers import (
    IdentifierKind,
    validate_identifier,
)
from scholar_harness.orchestrator import (
    RegisteredWorkspaceIdentityMissingError,
    ResearchOrchestrator,
)
from scholar_rag.chunker import text_fingerprint

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


PROTOCOL_FP = "sha256:" + "1" * 64
PRODUCER = {"package": "nexus-scholar-harness", "version": "1.0.0", "commit": "4" * 40}
STUDY_ID = "STU-alpha"
DOCUMENT_ID = "DOC-alpha-pdf"
SCREENING_ARTIFACT_ID = "ART-screening-alpha"
EXTRACTED_REL = "extracted/STU-alpha.md"
EXTRACTED_TEXT = "# alpha\n\nReal extracted body text.\n"


def _accept_chain(ws: Path, *, with_manifest: bool = True) -> None:
    """Accept a REAL corpus -> batch -> decisions -> manifest chain in ``ws``.

    Every artifact goes through the frozen acceptance gate
    (``accept_artifact`` / ``accept_extraction_candidate``), so the registry entries,
    the published manifest, and the parent hashes are the ones the contract
    actually produced. Nothing here is hand-written into
    ``audit/artifact_registry.json``: a test that fabricated the registry would be
    asserting Stage 6 against an input the pipeline can never create.

    ``with_manifest=False`` stops after the accepted screening decisions, which is
    the workspace state a document with no accepted manifest record really looks
    like.
    """
    from scholar_harness.contracts.acceptance import (
        AcceptanceContext,
        accept_artifact,
    )
    from scholar_harness.contracts.canonical import corpus_snapshot_fingerprint
    from scholar_harness.extraction_adapter import accept_extraction_candidate

    workspace_id = _manifest(ws)["registered_workspace_id"]

    corpus_data = {
        "corpus_id": "COR-alpha",
        "identity_algorithm_version": "identity-v1",
        "record_to_study": {"REC-alpha-doi": STUDY_ID},
        "studies": [
            {
                "study_id": STUDY_ID,
                "title": "Alpha study",
                "publication_year": 2020,
                "source_record_ids": ["REC-alpha-doi"],
                "alias_ids": ["SCI-000001"],
                "external_ids": {"doi": ["10.1000/alpha"]},
            }
        ],
    }
    corpus_fp = corpus_snapshot_fingerprint(corpus_data)
    ctx = AcceptanceContext(
        workspace_id=workspace_id,
        protocol_fingerprint=PROTOCOL_FP,
        corpus_fingerprint=corpus_fp,
    )

    binding = {
        "corpus_fingerprint": corpus_fp,
        "protocol_fingerprint": PROTOCOL_FP,
        "criteria_renderer_version": "1.0.0",
        "dedup_configuration_hash": "sha256:" + "c" * 64,
        "preparation_run_id": "RUN-prep-alpha",
        "screening_run_id": "RUN-screening-alpha",
    }

    def _accept(payload: dict, parent=None) -> object:
        payload["corpus_fingerprint"] = corpus_fp
        if parent is not None:
            payload["inputs"] = [
                {"artifact_id": parent.artifact_id, "sha256": parent.payload_hash}
            ]
        result = accept_artifact(ws, payload, expected=ctx)
        assert result.accepted, [i.code for i in result.issues]
        return result

    batch = _accept(
        {
            "schema_version": "1.0.0",
            "artifact_id": "ART-screening-batch-alpha",
            "artifact_type": "screening_batch",
            "workspace_id": workspace_id,
            "protocol_fingerprint": PROTOCOL_FP,
            "run_id": "RUN-screening-alpha",
            "created_at": "2026-09-18T10:01:00Z",
            "producer": PRODUCER,
            "inputs": [],
            "data": {
                "batch_id": "batch-000",
                "batch_index": 0,
                "binding": binding,
                "candidates": [{"study_id": STUDY_ID, "title": "Alpha study"}],
            },
        },
        parent=_accept(
            {
                "schema_version": "1.0.0",
                "artifact_id": "ART-corpus-alpha",
                "artifact_type": "corpus_snapshot",
                "workspace_id": workspace_id,
                "protocol_fingerprint": PROTOCOL_FP,
                "corpus_fingerprint": corpus_fp,
                "run_id": "RUN-discovery-alpha",
                "created_at": "2026-09-18T10:00:00Z",
                "producer": {
                    "package": "scholar-search-kit",
                    "version": "1.0.0",
                    "commit": "4" * 40,
                },
                "inputs": [],
                "data": corpus_data,
            }
        ),
    )

    decisions = _accept(
        {
            "schema_version": "1.0.0",
            "artifact_id": SCREENING_ARTIFACT_ID,
            "artifact_type": "screening_decisions",
            "workspace_id": workspace_id,
            "protocol_fingerprint": PROTOCOL_FP,
            "run_id": "RUN-screening-alpha",
            "created_at": "2026-09-18T10:01:30Z",
            "producer": PRODUCER,
            "inputs": [],
            "data": {
                "batch_id": "batch-000",
                "binding": binding,
                "decisions": [
                    {
                        "study_id": STUDY_ID,
                        "decision": "INCLUDE",
                        "decision_id": "SCR-alpha-human",
                        "method": "HUMAN",
                        "reason": "Meets frozen criteria.",
                        "screener_id": "reviewer-1",
                        "decided_at": "2026-09-18T10:01:30Z",
                    }
                ],
            },
        },
        parent=batch,
    )

    if not with_manifest:
        return

    (ws / "extracted").mkdir(exist_ok=True)
    (ws / EXTRACTED_REL).write_text(EXTRACTED_TEXT, encoding="utf-8")

    manifest = {
        "schema_version": "1.0.0",
        "artifact_id": "ART-documents-alpha",
        "artifact_type": "document_manifest",
        "workspace_id": workspace_id,
        "protocol_fingerprint": PROTOCOL_FP,
        "corpus_fingerprint": corpus_fp,
        "run_id": "RUN-screening-alpha",
        "created_at": "2026-09-18T10:02:30Z",
        "producer": PRODUCER,
        "inputs": [
            {"artifact_id": decisions.artifact_id, "sha256": decisions.payload_hash}
        ],
        "data": {
            "documents": [
                {
                    "document_id": DOCUMENT_ID,
                    "study_id": STUDY_ID,
                    "source_hash": "sha256:" + "6" * 64,
                    "content_status": "VALID",
                    "extracted_path": EXTRACTED_REL,
                    "extraction_method": "DETERMINISTIC_RULE",
                }
            ]
        },
    }
    result = accept_extraction_candidate(ws, manifest, expected=ctx)
    assert result.accepted, [i.code for i in result.issues]
    assert result.published_path


class _CapturingIndexer:
    """Stands in for the bound kit indexer and records the typed requests."""

    collection_name = "scholar_docs"
    embedder_kwargs = {"provider": "mock", "model_name": None}

    def __init__(self) -> None:
        self.requests: list[object] = []
        self.texts: list[str] = []

    def index_markdown(self, text, request=None):
        self.requests.append(request)
        self.texts.append(text)
        return [{"chunk_id": "CH-1"}]

    def get_collection_count(self):
        return len(self.requests)


@pytest.fixture(autouse=True)
def typed_stage6_backend(monkeypatch, request):
    """Use the typed replacement backend and capture the real service inputs."""
    if not request.node.name.startswith("test_stage6"):
        return None
    path = (
        Path(__file__).resolve().parents[1]
        / "e2e/test_extraction_runtime_acceptance.py"
    )
    spec = importlib.util.spec_from_file_location("e3_mock_support", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    backend = module.CapturingReplacementView()
    backend.requests = []
    monkeypatch.setattr(orch_module, "ChromaReplacementView", lambda **_: backend)
    monkeypatch.setattr(
        orch_module, "ChromaVisibleSetReader", lambda **_: module.MockReader(backend)
    )
    monkeypatch.setattr(orch_module, "get_embedder", lambda **_: module.MockEmbedder())
    original = orch_module.index_workspace

    def captured(request, **kwargs):
        backend.requests.extend(source.request for source in request.sources)
        return original(request, **kwargs)

    monkeypatch.setattr(orch_module, "index_workspace", captured)
    return backend


def _workspace(tmp_path: Path) -> Path:
    return scaffold_raw_project(
        tmp_path / "study",
        title="Evidence Synthesis",
        slug="evidence-synthesis",
        paradigm="",
        rqs=[],
    )


def test_stage6_inherits_every_limb_from_the_accepted_manifest(
    tmp_path, monkeypatch, typed_stage6_backend
):
    """The real Stage 6 path binds the recorded limbs, not the slug or filename.

    Attribution controls make this non-tautological. The recorded ``document_id`` is
    ``DOC-alpha-pdf`` and the file on disk is ``extracted/STU-alpha.md``, the study
    is ``STU-alpha``, the workspace is a ``WSP-`` id, and the workspace's human slug
    is ``evidence-synthesis`` -- so every plausible wrong answer (the stem, the DOI,
    the alias, the slug, the workspace in the study limb) is a DIFFERENT string from
    what the request must carry. A Stage 6 that derived any limb from a filename
    would fail here.
    """
    ws = _workspace(tmp_path)
    _accept_chain(ws)
    orch = ResearchOrchestrator(ws)
    indexer = _CapturingIndexer()
    monkeypatch.setattr(orch_module, "ScholarIndexer", lambda **_: indexer)

    result, _indexer = orch._run_indexing_stage(tmp_path / "rag" / "chroma_db")

    assert result["indexed_files"] == 1, result
    assert result["refused"] == []
    assert len(typed_stage6_backend.requests) == 1
    request = typed_stage6_backend.requests[0]

    # Every limb is the recorded one.
    assert request.workspace_id == _manifest(ws)["registered_workspace_id"]
    assert request.study_id == STUDY_ID
    assert request.document_id == DOCUMENT_ID
    # Indexing binds the accepted document manifest; its upstream screening
    # lineage is separately validated by the extraction acceptance gate.
    parent_view = orch._build_parent_view()
    assert parent_view is not None
    assert request.parent_artifact_id == parent_view["artifact_id"]
    assert request.parent_artifact_sha256 == parent_view["sha256"]
    # And the hashed text is the text that was actually indexed.
    assert request.extracted_content_sha256 == text_fingerprint(EXTRACTED_TEXT)
    assert "Real extracted body text." in "\n".join(
        row.text for row in typed_stage6_backend.staged_records
    )

    # Attribution: the document limb must NOT be any string a filename-, slug-,
    # alias-, DOI- or title-derived implementation could have produced. Every one
    # of these is a different string from DOCUMENT_ID, so a derived limb fails.
    for derived in (
        "STU-alpha",  # the extracted filename stem
        "extracted/STU-alpha.md",
        "evidence-synthesis",  # the human workspace slug
        "SCI-000001",  # the corpus alias id
        "10.1000/alpha",  # the DOI
        "Alpha study",  # the title
    ):
        assert request.document_id != derived, derived
    # And the workspace limb is the registered id, not the slug or the stem.
    assert request.workspace_id not in ("evidence-synthesis", "STU-alpha")
    # A workspace is not a study: the two limbs must differ.
    assert request.study_id != request.workspace_id


def test_stage6_refuses_a_document_with_no_accepted_manifest(tmp_path, monkeypatch):
    """No accepted manifest record -> refused, even though a real file exists.

    The workspace has a real accepted screening parent and a real extracted
    markdown, so the only thing missing is the accepted artifact that states the
    document's identity. Indexing it would mean inventing both limbs from the file.
    """
    ws = _workspace(tmp_path)
    _accept_chain(ws, with_manifest=False)
    # A real extracted file, and even a real included.json mentioning the study.
    (ws / "extracted").mkdir(exist_ok=True)
    (ws / EXTRACTED_REL).write_text(EXTRACTED_TEXT, encoding="utf-8")
    lit = ws / "literature"
    lit.mkdir(exist_ok=True)
    (lit / "included.json").write_text(
        json.dumps([{"workspace_id": STUDY_ID, "study_id": STUDY_ID}]), encoding="utf-8"
    )
    orch = ResearchOrchestrator(ws)
    indexer = _CapturingIndexer()
    monkeypatch.setattr(orch_module, "ScholarIndexer", lambda **_: indexer)

    result, _indexer = orch._run_indexing_stage(tmp_path / "rag" / "chroma_db")

    assert result["indexed_files"] == 0
    assert indexer.requests == [], "nothing may be indexed without an accepted record"
    assert result["status"] == "FAILED"


def test_stage6_refuses_a_document_with_no_accepted_screening_parent(
    tmp_path, monkeypatch
):
    """A manifest record whose study was never screened in is refused.

    The manifest alone is not authority to index: the accepted screening decision
    is the study's scientific parent, and without it there is no accepted INCLUDE
    binding to inherit.
    """
    ws = _workspace(tmp_path)
    _accept_chain(ws, with_manifest=False)
    orch = ResearchOrchestrator(ws)
    # Publish a manifest record for a study that has no accepted decision, by
    # reusing the accepted chain's own manifest payload shape but pointing the
    # document at an unknown study. Built through the frozen model, and inserted as
    # a real accepted artifact whose screening parent is the accepted one.
    from scholar_harness.contracts.acceptance import AcceptanceContext, accept_artifact
    from scholar_harness.extraction_adapter import accept_extraction_candidate

    registry = json.loads(
        (ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
    )
    ctx_fp = registry["artifacts"][SCREENING_ARTIFACT_ID]
    del ctx_fp
    (ws / "extracted").mkdir(exist_ok=True)
    (ws / "extracted" / "ghost.md").write_text(EXTRACTED_TEXT, encoding="utf-8")

    # The document's study is not in the accepted decisions, so there is no parent.
    manifest_payload = None
    for entry in registry["artifacts"].values():
        if entry["artifact_type"] == "screening_decisions":
            payload = json.loads((ws / entry["path"]).read_text(encoding="utf-8"))
            manifest_payload = payload
    assert manifest_payload is not None

    corpus_fp = manifest_payload["corpus_fingerprint"]
    ctx = AcceptanceContext(
        workspace_id=manifest_payload["workspace_id"],
        protocol_fingerprint=manifest_payload["protocol_fingerprint"],
        corpus_fingerprint=corpus_fp,
    )
    result = accept_extraction_candidate(
        ws,
        {
            "schema_version": "1.0.0",
            "artifact_id": "ART-documents-ghost",
            "artifact_type": "document_manifest",
            "workspace_id": manifest_payload["workspace_id"],
            "protocol_fingerprint": manifest_payload["protocol_fingerprint"],
            "corpus_fingerprint": corpus_fp,
            "run_id": "RUN-screening-alpha",
            "created_at": "2026-09-18T10:03:00Z",
            "producer": PRODUCER,
            "inputs": [
                {
                    "artifact_id": SCREENING_ARTIFACT_ID,
                    "sha256": registry["artifacts"][SCREENING_ARTIFACT_ID]["sha256"],
                }
            ],
            "data": {
                "documents": [
                    {
                        "document_id": "DOC-ghost",
                        "study_id": "STU-unscreened",
                        "source_hash": "sha256:" + "7" * 64,
                        "content_status": "VALID",
                        "extracted_path": "extracted/ghost.md",
                        "extraction_method": "DETERMINISTIC_RULE",
                    }
                ]
            },
        },
        expected=ctx,
    )
    assert result.accepted, [i.code for i in result.issues]

    indexer = _CapturingIndexer()
    monkeypatch.setattr(orch_module, "ScholarIndexer", lambda **_: indexer)
    stage, _indexer = orch._run_indexing_stage(tmp_path / "rag" / "chroma_db")

    assert stage["indexed_files"] == 0
    assert indexer.requests == []
    assert stage["documents"] == []
    assert not (tmp_path / "rag" / "chroma_db").exists()
    assert stage["refused"][0]["code"] == "NO_DOCUMENTS_TO_INDEX"


def test_stage6_refuses_a_record_with_no_study_and_never_substitutes_the_workspace(
    tmp_path, monkeypatch
):
    """The study limb is never filled in from the workspace limb.

    Defence in depth: the frozen ``DocumentRecord`` validator requires a
    ``STU-``/``SCI-`` study id, so a published manifest always has one and this
    branch is unreachable through the acceptance gate today. It is pinned anyway,
    because the fallback this test exists to prevent -- ``study_id or workspace_id``
    -- is exactly the silent workspace-as-study substitution Contract v1 forbids,
    and it would otherwise be a one-token regression with no failing test.

    The record is injected at the projection boundary rather than published, so the
    assertion is about Stage 6's own behaviour and not about what the gate allows.
    """
    ws = _workspace(tmp_path)
    _accept_chain(ws)
    orch = ResearchOrchestrator(ws)
    indexer = _CapturingIndexer()
    monkeypatch.setattr(orch_module, "ScholarIndexer", lambda **_: indexer)
    workspace_id = orch.recorded_workspace_id()
    monkeypatch.setattr(
        orch,
        "_accepted_document_records",
        lambda: {
            "DOC-nostudy": {
                "study_id": "   ",
                "extracted_path": EXTRACTED_REL,
                "parent_artifact_id": "ART-documents-alpha",
                "parent_artifact_sha256": "sha256:" + "8" * 64,
            }
        },
    )

    result, _indexer = orch._run_indexing_stage(tmp_path / "rag" / "chroma_db")

    assert result["indexed_files"] == 0
    assert indexer.requests == [], "a request must not be built without a study limb"
    assert result["status"] == "FAILED"
    assert result["refused"][0]["code"] == "NO_DOCUMENTS_TO_INDEX"
    # And explicitly: the workspace limb was available and was NOT used as a study.
    assert workspace_id.startswith("WSP-")
    assert workspace_id not in result["refused"][0]["code"]


def test_stage6_identity_refusal_leaves_no_store_behind(tmp_path, monkeypatch):
    """Fix 4: the store must not exist when the identity cannot be stated.

    ``ScholarIndexer`` creates its Chroma directory on construction, so validating
    the workspace identity first is what keeps a refused run from leaving
    ``rag/chroma_db/`` on disk.
    """
    ws = tmp_path / "study"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"project_id": "evidence-synthesis"}), encoding="utf-8"
    )
    orch = ResearchOrchestrator(ws)
    chroma_dir = ws / "rag" / "chroma_db"

    constructed: list[str] = []

    def _boom(**kwargs):
        constructed.append(str(kwargs.get("db_path")))
        raise AssertionError("the store must not be constructed before validation")

    monkeypatch.setattr(orch_module, "ScholarIndexer", _boom)

    with pytest.raises(RegisteredWorkspaceIdentityMissingError):
        orch._run_indexing_stage(chroma_dir)

    assert constructed == [], "no indexer may be built without a recorded identity"
    assert not chroma_dir.exists(), "a refused run must leave no store behind"


def test_stage6_audit_event_reports_the_real_outcome(tmp_path, monkeypatch):
    """Fix 5: a run that indexed nothing must not log ``SUCCESS``."""
    ws = _workspace(tmp_path)
    _accept_chain(ws, with_manifest=False)
    orch = ResearchOrchestrator(ws)
    monkeypatch.setattr(orch_module, "ScholarIndexer", lambda **_: _CapturingIndexer())

    _res, _indexer = orch._run_indexing_stage(tmp_path / "rag" / "chroma_db")

    events = [
        json.loads(line)
        for line in (ws / "audit" / "journal.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    rag_events = [e for e in events if e.get("action") == "RAG_INDEX_REJECTED"]
    assert len(rag_events) == 1
    assert rag_events[0]["status"] != "SUCCESS"
    assert rag_events[0]["metrics"]["indexed_files"] == 0


def test_stage6_audit_event_records_a_real_run_as_success(tmp_path, monkeypatch):
    """The control for the test above: a genuine run does log SUCCESS.

    Stage 6 publishes through the E3 acceptance adapter (handoff §6.6), so the
    ledger line is the canonical accepted-record event -- not the legacy
    continuity line with ``metrics.indexed_files``. Emitting the legacy
    absolute-path line alongside would violate §6.6-never and §6.5.
    """
    ws = _workspace(tmp_path)
    _accept_chain(ws)
    orch = ResearchOrchestrator(ws)
    monkeypatch.setattr(orch_module, "ScholarIndexer", lambda **_: _CapturingIndexer())

    _res, _indexer = orch._run_indexing_stage(tmp_path / "rag" / "chroma_db")

    events = [
        json.loads(line)
        for line in (ws / "audit" / "journal.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    rag_events = [e for e in events if e.get("action") == "RAG_INDEX_BUILT"]
    assert len(rag_events) == 1
    event = rag_events[0]
    assert event["status"] == "SUCCESS"
    params = event["parameters"]
    # §6.6 field rows: identity, parent ref, manifest ref, fingerprints, counts.
    assert params["workspace_id"] == _manifest(ws)["registered_workspace_id"]
    assert isinstance(params["run_id"], str) and params["run_id"].startswith("RUN-")
    registry = json.loads(
        (ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
    )
    assert params["parent_artifact_id"] == "ART-documents-alpha"
    assert (
        params["parent_artifact_sha256"]
        == registry["artifacts"]["ART-documents-alpha"]["sha256"]
    )
    assert isinstance(params["manifest_id"], str) and params["manifest_id"].startswith(
        "IDX-"
    )
    assert params["manifest_path"].endswith(".json")
    assert params["artifact_checksum"].startswith("sha256:")
    for field in (
        "index_fingerprint",
        "chunk_set_fingerprint",
        "configuration_fingerprint",
        "production_fingerprint",
    ):
        assert params[field].startswith("sha256:"), field
    assert params["protocol_fingerprint"] == PROTOCOL_FP
    assert params["corpus_fingerprint"].startswith("sha256:")
    assert params["counts"]["accepted_documents"] >= 1
    assert isinstance(params["counts"]["rejected_documents"], int)
    assert isinstance(params["counts"]["visible_chunks"], int)
    assert params["rejected_documents"] == []
    assert params["embedding_identity"] == {
        "provider": "sentence-transformers",
        "model": "all-MiniLM-L6-v2",
        "dimension": 384,
        "distance_metric": "cosine",
    }
    assert params["configuration"]["max_chunk_chars"] == 1200
    assert "failing_step" not in params and "code" not in params
    # Canonical metrics travel with the accepted counts, not the legacy key.
    assert event["metrics"]["accepted_documents"] >= 1
    assert "indexed_files" not in event["metrics"]
    # §6.6-never: no absolute path, db_path, secret, or environment value.
    blob = json.dumps(event, sort_keys=True)
    lowered = blob.lower()
    assert "chroma_db" not in blob and "db_path" not in blob
    assert str(tmp_path) not in blob
    assert "/tmp/" not in blob and "C:\\" not in blob and "C:/" not in blob
    assert "sk-" not in blob and "ghp_" not in blob and "bearer" not in lowered
    assert "os.environ" not in blob and "getenv" not in lowered


def test_stage6_refuses_an_unusable_registry_rather_than_coercing_it(tmp_path):
    """A registry that does not validate is an absence, never a licence to infer.

    The registry is read through the frozen ``ArtifactRegistry``; a malformed entry
    must not be coerced into an empty ``sha256`` and used as a parent.
    """
    ws = _workspace(tmp_path)
    _accept_chain(ws)
    (ws / "audit").mkdir(exist_ok=True)
    (ws / "audit" / "artifact_registry.json").write_text(
        json.dumps(
            {
                "contract_version": "1.0.0",
                "artifacts": {
                    SCREENING_ARTIFACT_ID: {
                        "artifact_type": "screening_decisions",
                        "path": "../escape/decisions.json",
                        "sha256": "not-a-sha256",
                        "accepted_at": "2026-09-18T10:01:30Z",
                        "run_id": "RUN-screening-alpha",
                        "producer": PRODUCER,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    orch = ResearchOrchestrator(ws)
    assert orch._load_artifact_registry() is None
    assert orch._accepted_screening_parents() == {}
    assert orch._accepted_document_records() == {}


def test_stage6_refuses_a_registry_entry_that_escapes_the_workspace(tmp_path):
    """A workspace-relative path that climbs out is refused, not followed."""
    ws = _workspace(tmp_path)
    _accept_chain(ws)
    registry = json.loads(
        (ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
    )
    outside = ws.parent / "outside.json"
    outside.write_text(json.dumps({"data": {"decisions": []}}), encoding="utf-8")

    from scholar_harness.contracts.acceptance import ArtifactRegistry

    entry = registry["artifacts"][SCREENING_ARTIFACT_ID]
    registry["artifacts"]["ART-escape"] = {
        **entry,
        "path": "../outside.json",
    }
    (ws / "audit" / "artifact_registry.json").write_text(
        json.dumps(registry), encoding="utf-8"
    )
    assert ArtifactRegistry.model_validate(registry)  # the shape is legal

    orch = ResearchOrchestrator(ws)
    parents = orch._accepted_screening_parents()
    # The escaping entry yields nothing; the in-workspace one still resolves.
    assert parents, "the legitimate parent must still resolve"
    assert all(v["parent_artifact_id"] != "ART-escape" for v in parents.values())


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
