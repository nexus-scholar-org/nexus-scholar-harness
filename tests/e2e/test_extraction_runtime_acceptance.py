"""Runtime acceptance adoption: Stage 5 output -> accepted manifest -> Stage 6.

Every test here drives the *real* surfaces. The workspace is built from a real
protocol fixture, a real ``scholar-search-kit`` corpus snapshot, the real
``scholar_harness.screening`` agent-in-the-loop handoff, and the real Stage 5
extraction writer; acceptance goes through the frozen gate
(:func:`scholar_harness.contracts.acceptance.accept_artifact` via the frozen
extraction adapter); indexing goes through the real Stage 6 with only the offline
embedder standing in. Nothing here fabricates a registry entry, a published
artifact, or a workspace identity.

The five acceptance criteria this packet must demonstrate:

* **A1** real extraction output publishes one accepted manifest and indexes it;
* **A2** an invalid candidate publishes no manifest, no registry entry, and no index,
  and returns an actionable typed refusal;
* **A3** audit statuses come from the canonical ``OperationStatus`` vocabulary and
  record the outcome that actually happened;
* **A4** the E3 identity refusals stay fail-closed -- the workspace slug is never
  used and no identity is minted at use time;
* **A5** a candidate-supplied fingerprint mutation is refused, because the trusted
  context limbs are derived from recorded state, not from the candidate.
"""

from __future__ import annotations

import copy
import dataclasses
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar

import pytest
from scholar_protocol.canonical import canonical_fingerprint
from scholar_protocol.models import ResearchProtocol
from scholar_search.identity import build_corpus_snapshot_artifact
from scholar_search.models import Author, Document, ExternalIds

from scholar_harness import orchestrator as orch_module
from scholar_harness.contracts.acceptance import AcceptanceContext, accept_artifact
from scholar_harness.contracts.models import (
    DocumentManifestArtifact,
    OperationStatus,
)
from scholar_harness.extraction_adapter import accept_extraction_candidate
from scholar_harness.extraction_producer import (
    PublicationRefused,
    build_acceptance_context,
    build_document_manifest_candidate,
    index_accepted_documents,
    publication_status,
    publish_document_manifest,
)
from scholar_harness.screening.batcher import cmd_prepare
from scholar_harness.screening.collector import cmd_collect

ROOT = Path(__file__).resolve().parents[2]
AGENT_EXTRACT = ROOT / "src" / "scholar_harness" / "agent_extract.py"
PROTOCOL_FIXTURE = (
    ROOT
    / "tools"
    / "scholar-protocol-kit"
    / "tests"
    / "fixtures"
    / "canonical"
    / "identity_base.json"
)

WORKSPACE_ID = "WSP-" + "0123456789abcdef" * 2
SLUG = "evidence-synthesis"
STUDY_TITLE = "Contract bound extraction"
DOI = "10.1000/runtime-acceptance"
RUN_ID = "RUN-search-runtime-acceptance"
SCREENING_REASON = "Meets the frozen inclusion criteria."

#: A body the PDF kit's own usability rule calls usable, written the way the frozen
#: Stage 5 writers write it (YAML frontmatter + prose).
_USABLE_BODY = (
    "## Abstract\n\n"
    + "This study reports a measured contract-bound extraction result. " * 12
    + "\n"
)


class CapturingIndexer:
    """Stands in for the bound kit indexer and records the typed requests.

    Only the embedding backend is replaced. Stage 6's identity binding, its refusal
    rules, and its request construction all run for real, so a Stage 6 that derived
    any limb from a filename or the slug would still be caught here.
    """

    collection_name = "scholar_docs"
    embedder_kwargs: ClassVar[dict[str, Any]] = {"provider": "mock", "model_name": None}

    def __init__(self) -> None:
        self.requests: list[Any] = []
        self.texts: list[str] = []

    def index_markdown(self, text, request=None):
        self.requests.append(request)
        self.texts.append(text)
        return [{"chunk_id": "CH-1"}]

    def get_collection_count(self) -> int:
        return len(self.requests)


class CapturingReplacementView:
    """Stands in for ChromaReplacementView and records the staged requests.

    The new IndexService uses the replacement protocol (R1-R7). This mock captures
    the IndexDocumentRequest objects that are built for each source document.
    """

    mode = "marker"
    collection_name = "scholar_docs"
    embedder_kwargs: ClassVar[dict[str, Any]] = {"provider": "mock", "model_name": None}

    def __init__(self) -> None:
        self.staged_records: list[Any] = []
        self.switched_chunk_ids: list[str] = []
        self.removed: list[str] = []
        self._last_run_id: str = ""

    def stage(self, run_id: str, records: list[Any]) -> None:
        self.staged_records.extend(records)

    def embed_staged(self, run_id: str, embedder: Any) -> None:
        pass

    def staged_rows(self, run_id: str) -> list[Any]:
        """R3 reads staged rows before R5 makes them visible."""
        from scholar_rag.replacement import StagedRow

        return [
            StagedRow(
                row_key=f"{run_id}#{record.chunk_id}",
                chunk_id=record.chunk_id,
                document_id=record.document_id,
                embedding_dimension=384,
            )
            for record in self.staged_records
        ]

    def switch_visibility(self, run_id: str, chunk_ids: list[str], mode: str) -> None:
        self.switched_chunk_ids = chunk_ids
        self._last_run_id = run_id

    def remove_obsolete(self, document_ids: list[str], keep_ids: list[str]) -> int:
        return 0

    def visible_ids(self) -> list[str]:
        return self.switched_chunk_ids

    def visible_count(self) -> int:
        return len(self.switched_chunk_ids)

    def visible_rows(self) -> list[Any]:
        """Return typed VisibleRows matching the switched chunks.

        The verification reads these rows and compares them against the manifest's
        visible_chunks. We build them from the staged CandidateChunk records.
        """
        # Build a map of chunk_id -> staged record
        staged_by_id = {r.chunk_id: r for r in self.staged_records}
        rows = []
        for chunk_id in self.switched_chunk_ids:
            record = staged_by_id.get(chunk_id)
            if record is None:
                continue
            from scholar_rag.index_verifier import VisibleRow

            rows.append(
                VisibleRow(
                    chunk_id=record.chunk_id,
                    document_id=record.document_id,
                    study_id=record.study_id,
                    row_key=f"{self._last_run_id}#{chunk_id}",
                    embedding_dimension=384,
                    stored_text=record.text,
                )
            )
        return rows


class MockReader:
    """Mock reader that returns the switched chunk IDs from the backend."""

    def __init__(self, backend: CapturingReplacementView) -> None:
        self.backend = backend

    def visible_ids(self) -> list[str]:
        return self.backend.visible_ids()

    def visible_count(self) -> int:
        return self.backend.visible_count()

    def visible_rows(self) -> list[Any]:
        return self.backend.visible_rows()

    def read_collection_metadata(self) -> dict[str, Any] | None:
        return {"hnsw:space": "cosine"}


class MockEmbedder:
    """Mock embedder that returns fixed vectors."""

    dimension = 384

    def __call__(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 384 for _ in texts]


@pytest.fixture
def indexer(monkeypatch) -> CapturingReplacementView:
    """Replace the replacement backend and embedder; the rest of Stage 6 is the real code."""

    captured = CapturingReplacementView()
    # Mock the replacement backend
    monkeypatch.setattr(
        "scholar_harness.orchestrator.ChromaReplacementView",
        lambda **_: captured,
    )
    # Mock the verifier reader to use the captured backend's switched IDs
    monkeypatch.setattr(
        "scholar_harness.orchestrator.ChromaVisibleSetReader",
        lambda **_: MockReader(captured),
    )
    # Mock the embedder to be hermetic
    monkeypatch.setattr(
        "scholar_harness.orchestrator.get_embedder",
        lambda **_: MockEmbedder(),
    )
    return captured


def _write_extracted(
    workspace: Path, record: dict[str, Any], *, body: str = _USABLE_BODY
) -> Path:
    """Write an extracted file exactly the way the frozen Stage 5 writers do.

    Stage 5 (``ResearchOrchestrator.run_pipeline`` metadata fallback) and the PDF kit's
    ``extract_markdown`` both emit a YAML frontmatter block keyed on the included
    record's own identity fields. Reproducing that writer here is what makes these
    tests exercise a real extraction output rather than a convenient stub.
    """

    from scholar_harness.orchestrator import _extraction_file_stem

    extracted = workspace / "extracted"
    extracted.mkdir(exist_ok=True)
    path = extracted / f"{_extraction_file_stem(record)}.md"
    path.write_text(
        "---\n"
        f'workspace_id: "{record.get("workspace_id", "")}"\n'
        f'doi: "{record.get("external_ids", {}).get("doi", "")}"\n'
        f"title: {json.dumps(record.get('title') or 'Untitled', ensure_ascii=False)}\n"
        'extraction_engine: "metadata"\n'
        "---\n\n"
        f"{body}",
        encoding="utf-8",
    )
    return path


def _build_workspace(tmp_path: Path, *, study_count: int = 1) -> dict[str, Any]:
    """Build a real workspace: protocol -> corpus -> screening handoff -> extraction.

    Returns the study records that Stage 5 would extract, taken from the real
    ``literature/included.json`` the handoff wrote.
    """

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "project.json").write_text(
        json.dumps(
            {
                "project_id": SLUG,
                "registered_workspace_id": WORKSPACE_ID,
                "stats": {},
            }
        ),
        encoding="utf-8",
    )
    protocol = json.loads(PROTOCOL_FIXTURE.read_text(encoding="utf-8"))
    (workspace / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    protocol_fp = canonical_fingerprint(ResearchProtocol.model_validate(protocol))

    sources = [
        Document(
            title=f"{STUDY_TITLE} {index}",
            year=2026,
            provider="crossref",
            provider_id=f"runtime-record-{index}",
            external_ids=ExternalIds(doi=f"10.1000/runtime-acceptance-{index}"),
            authors=[Author("Reviewer")],
            abstract="Abstract sentence. " * 5,
        )
        for index in range(1, study_count + 1)
    ]
    built = build_corpus_snapshot_artifact(
        sources,
        workspace_id=WORKSPACE_ID,
        run_id=RUN_ID,
        protocol_fingerprint=protocol_fp,
        created_at=datetime(2026, 9, 21, tzinfo=UTC),
        commit="3" * 40,
    )
    corpus = built.artifact
    result = accept_artifact(
        workspace,
        corpus,
        expected=AcceptanceContext(
            workspace_id=WORKSPACE_ID,
            protocol_fingerprint=protocol_fp,
            corpus_fingerprint=corpus["corpus_fingerprint"],
        ),
    )
    assert result.accepted is True, [issue.code for issue in result.issues]

    studies = corpus["data"]["studies"]
    literature = workspace / "literature"
    literature.mkdir()
    (literature / "verified.json").write_text(
        json.dumps(
            [
                {
                    "workspace_id": study["study_id"],
                    "title": study["title"],
                    "year": study["publication_year"],
                    "external_ids": {"doi": f"10.1000/runtime-acceptance-{index + 1}"},
                    "abstract": "Abstract sentence. " * 5,
                }
                for index, study in enumerate(studies)
            ]
        ),
        encoding="utf-8",
    )

    cmd_prepare(workspace, batch_size=20)
    screening = workspace / "literature" / "screening"
    (screening / "batch_001_decisions.json").write_text(
        json.dumps(
            {
                "batch": 1,
                "reviewed_by": "human-reviewer-1",
                "timestamp": "2026-09-21T12:00:00Z",
                "decisions": [
                    {
                        "workspace_id": study["study_id"],
                        "decision": "INCLUDE",
                        "method": "HUMAN",
                        "screening_reasoning": SCREENING_REASON,
                        "parent_decision_ids": [],
                    }
                    for study in studies
                ],
            }
        ),
        encoding="utf-8",
    )
    cmd_collect(workspace)

    included = json.loads((literature / "included.json").read_text(encoding="utf-8"))
    assert len(included) == study_count
    return {
        "workspace": workspace,
        "included": included,
        "study_ids": [s["study_id"] for s in studies],
    }


def _extracted_state(tmp_path: Path, *, study_count: int = 1) -> dict[str, Any]:
    """A workspace whose Stage 5 extraction output really exists on disk."""

    state = _build_workspace(tmp_path, study_count=study_count)
    for record in state["included"]:
        _write_extracted(state["workspace"], record)
    return state


def _registry(workspace: Path) -> dict[str, Any]:
    """The real registry, or an empty one when a case deleted it."""

    path = workspace / "audit" / "artifact_registry.json"
    if not path.is_file():
        return {"artifacts": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _registered_manifests(workspace: Path) -> dict[str, Any]:
    return {
        artifact_id: entry
        for artifact_id, entry in _registry(workspace)["artifacts"].items()
        if isinstance(entry, dict) and entry.get("artifact_type") == "document_manifest"
    }


def _journal(workspace: Path) -> list[dict[str, Any]]:
    journal = workspace / "audit" / "journal.jsonl"
    if not journal.is_file():
        return []
    return [
        json.loads(line)
        for line in journal.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _publication_record(workspace: Path, artifact_id: str) -> dict[str, Any]:
    return json.loads(
        (
            workspace / "literature" / "extraction_publications" / f"{artifact_id}.json"
        ).read_text(encoding="utf-8")
    )


# --------------------------------------------------------------------------- #
# A1 -- real extraction output publishes one accepted manifest and indexes it
# --------------------------------------------------------------------------- #


def test_a1_real_extraction_publishes_one_accepted_manifest_and_indexes_it(
    tmp_path: Path, indexer: CapturingReplacementView
) -> None:
    state = _extracted_state(tmp_path, study_count=2)
    workspace = state["workspace"]

    outcome = publish_document_manifest(workspace)

    assert outcome.accepted is True, outcome.refusal
    assert outcome.status == OperationStatus.SUCCESS.value
    assert outcome.idempotent is False
    assert outcome.documents == 2
    # Exactly one accepted document_manifest -- the runtime gap this packet closes.
    manifests = _registered_manifests(workspace)
    assert list(manifests) == [outcome.artifact_id]

    # The published payload re-validates through the frozen model and declares only
    # the accepted screening_decisions parents the registry recorded.
    payload = json.loads(
        (workspace / manifests[outcome.artifact_id]["path"]).read_text("utf-8")
    )
    manifest = DocumentManifestArtifact.model_validate(payload)
    assert {record.study_id for record in manifest.data.documents} == set(
        state["study_ids"]
    )
    registry = _registry(workspace)
    for parent in manifest.inputs:
        assert registry["artifacts"][parent.artifact_id]["sha256"] == parent.sha256

    # Stage 6 then indexes the accepted documents, unmodified.
    result = index_accepted_documents(workspace)
    assert result["status"] == OperationStatus.SUCCESS.value, result
    assert result["indexed_files"] == 2
    assert result["refused"] == []

    # Attribution: every indexed request carries the recorded limbs, and none of the
    # plausible wrong answers (a filename stem, the human slug, a DOI, a title).
    # The new IndexService builds IndexDocumentRequest objects in sources; verify via result.
    by_document = {doc["document_id"]: doc for doc in result["documents"]}
    parents = orch_module.ResearchOrchestrator(workspace)._accepted_screening_parents()
    for record in manifest.data.documents:
        doc = by_document[record.document_id]
        assert doc["study_id"] == record.study_id
        # A workspace is not a study.
        assert doc["study_id"] != WORKSPACE_ID
        assert doc["parent_artifact_id"] == outcome.artifact_id
        assert doc["screening_decision_id"] == parents[record.study_id]["decision_id"]
        for derived in (
            record.extracted_path,
            SLUG,
            str(record.extracted_path).split("/")[-1].removesuffix(".md"),
            STUDY_TITLE,
            "10.1000/runtime-acceptance-1",
        ):
            assert doc["document_id"] != derived, derived
        assert WORKSPACE_ID not in {SLUG, doc["study_id"]}


def test_a1_publish_is_idempotent_on_exact_replay(tmp_path: Path) -> None:
    state = _extracted_state(tmp_path)
    workspace = state["workspace"]

    first = publish_document_manifest(workspace)
    before = _registry(workspace)
    second = publish_document_manifest(workspace)
    after = _registry(workspace)

    assert first.accepted and second.accepted
    assert second.idempotent is True
    assert second.artifact_id == first.artifact_id
    assert after["artifacts"].keys() == before["artifacts"].keys()


_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def test_a1_publication_record_states_the_rule_that_produced_source_hash(
    tmp_path: Path,
) -> None:
    """``source_hash`` covers real bytes, and the record says which bytes."""

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    outcome = publish_document_manifest(workspace)
    assert outcome.accepted, outcome.refusal

    record = _publication_record(workspace, outcome.artifact_id)
    document = record["documents"][0]
    assert document["source_kind"] == "canonical_source_record"
    assert document["source_locator"] == "literature/included.json"
    # An exact digest form, not merely a prefix: "sha256:sha256:..." is not a digest.
    assert _DIGEST.match(document["source_hash"]), document["source_hash"]
    # The harness record is not, and does not claim to be, the kit's own sidecar.
    assert record["record_type"] == "harness_document_manifest_publication"
    assert "pdf-extraction-manifest-v1" not in record["record_type"]


def test_a1_source_hash_covers_the_workspace_pdf_when_one_exists(
    tmp_path: Path,
) -> None:
    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    record = state["included"][0]
    pdfs = workspace / "pdfs"
    pdfs.mkdir(exist_ok=True)
    from hashlib import sha256

    payload = b"%PDF-1.7 real harvested bytes\n"
    (pdfs / f"{record['workspace_id']}.pdf").write_bytes(payload)

    outcome = publish_document_manifest(workspace)
    assert outcome.accepted, outcome.refusal

    provenance = _publication_record(workspace, outcome.artifact_id)["documents"][0]
    assert provenance["source_kind"] == "workspace_pdf"
    assert provenance["source_hash"] == f"sha256:{sha256(payload).hexdigest()}"


def test_a1_crlf_extraction_output_is_readable_and_recorded_as_normalized(
    tmp_path: Path,
) -> None:
    """The kit's frontmatter grammar is LF-only; Stage 5 on Windows commits CRLF.

    The normalization is a byte-level step and is recorded, not hidden.
    """

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    path = workspace / "extracted" / f"{state['included'][0]['workspace_id']}.md"
    assert b"\r\n" in path.read_bytes()  # write_text on Windows

    outcome = publish_document_manifest(workspace)
    assert outcome.accepted, outcome.refusal
    provenance = _publication_record(workspace, outcome.artifact_id)["documents"][0]
    assert provenance["line_endings_normalized"] is True
    assert _DIGEST.match(provenance["extracted_sha256"]), provenance["extracted_sha256"]
    assert _DIGEST.match(provenance["extracted_file_sha256"]), provenance[
        "extracted_file_sha256"
    ]
    # The normalized body digest and the raw on-disk digest must be distinguishable:
    # collapsing them would hide the rewrite the producer performed.
    assert provenance["extracted_sha256"] != provenance["extracted_file_sha256"]


# --------------------------------------------------------------------------- #
# A2 -- invalid candidates publish nothing and refuse actionably
# --------------------------------------------------------------------------- #


def _assert_published_nothing(workspace: Path, outcome: Any) -> None:
    assert outcome.accepted is False
    assert outcome.status == OperationStatus.FAILED.value
    assert outcome.refusal is not None
    assert outcome.refusal["code"]
    assert outcome.refusal["message"]
    assert _registered_manifests(workspace) == {}
    assert not (workspace / "literature" / "extraction_publications").exists()
    assert not (workspace / "rag" / "chroma_db").exists()


@pytest.mark.parametrize(
    ("mutate", "expected_code"),
    [
        pytest.param(
            lambda ws: _delete_extracted_output(ws),
            "EXTRACTED_OUTPUT_MISSING",
            id="no-extraction-output",
        ),
        pytest.param(
            lambda ws: _overwrite_body(
                ws, "Extracted content from 10.1000/runtime-acceptance-1.pdf\n"
            ),
            "EXTRACTED_CONTENT_IS_STUB",
            id="legacy-stub-body",
        ),
        pytest.param(
            lambda ws: _overwrite_body(ws, "## Abstract\n\nToo short to be text.\n"),
            "EXTRACTED_CONTENT_NOT_USABLE",
            id="below-usability-threshold",
        ),
        pytest.param(
            lambda ws: _overwrite_frontmatter(ws, workspace_id="STU-someone-else"),
            "EXTRACTED_FRONTMATTER_MISMATCH",
            id="file-claims-another-study",
        ),
        pytest.param(
            lambda ws: _overwrite_frontmatter(ws, doi="10.1000/other"),
            "EXTRACTED_FRONTMATTER_MISMATCH",
            id="file-claims-another-doi",
        ),
        pytest.param(
            lambda ws: _strip_frontmatter(ws),
            "EXTRACTED_FRONTMATTER_UNREADABLE",
            id="not-a-committed-extraction",
        ),
        pytest.param(
            lambda ws: (ws / "literature" / "included.json").unlink(),
            "INCLUDED_RECORDS_MISSING",
            id="no-screening-output",
        ),
        pytest.param(
            lambda ws: (ws / "literature" / "included.json").write_text("[]", "utf-8"),
            "INCLUDED_RECORDS_EMPTY",
            id="empty-screening-output",
        ),
        pytest.param(
            lambda ws: (ws / "literature" / "included.json").write_text(
                json.dumps([{"title": "unresolvable", "workspace_id": "STU-ghost"}]),
                "utf-8",
            ),
            "STUDY_IDENTITY_UNRESOLVED",
            id="study-not-in-accepted-corpus",
        ),
        pytest.param(
            lambda ws: _append_duplicate_included(ws),
            "DUPLICATE_STUDY_RECORDS",
            id="same-study-twice",
        ),
        pytest.param(
            lambda ws: _unregister_screening_parent(ws),
            "SCREENING_GENERATION_ABSENT",
            id="no-accepted-screening-generation",
        ),
        pytest.param(
            lambda ws: _exclude_the_study_in_its_screening_parent(ws),
            "NO_ACCEPTED_SCREENING_PARENT",
            id="screening-decision-never-included-it",
        ),
        pytest.param(
            lambda ws: (ws / "audit" / "artifact_registry.json").unlink(),
            "ARTIFACT_REGISTRY_MISSING",
            id="no-registry",
        ),
        pytest.param(
            lambda ws: (ws / "audit" / "artifact_registry.json").write_text(
                json.dumps({"contract_version": "1.0.0", "artifacts": {"ART-x": {}}}),
                "utf-8",
            ),
            "ARTIFACT_REGISTRY_INVALID",
            id="unusable-registry",
        ),
        pytest.param(
            lambda ws: (ws / "protocol.json").unlink(),
            "PROTOCOL_ARTIFACT_MISSING",
            id="no-protocol",
        ),
        pytest.param(
            lambda ws: (ws / "protocol.json").write_text("{}", "utf-8"),
            "PROTOCOL_ARTIFACT_INVALID",
            id="unusable-protocol",
        ),
        pytest.param(
            lambda ws: _mutate_protocol(ws),
            "PROTOCOL_FINGERPRINT_MISMATCH",
            id="protocol-changed-after-corpus",
        ),
        pytest.param(
            lambda ws: _reidentify_project(ws, SLUG),
            "WORKSPACE_IDENTITY_NOT_REGISTERED",
            id="identity-replaced-by-the-slug",
        ),
        pytest.param(
            lambda ws: _unregister_identity(ws),
            "WORKSPACE_IDENTITY_NOT_RECORDED",
            id="identity-never-recorded",
        ),
        pytest.param(
            lambda ws: _escape_registry_path(ws),
            "PATH_NOT_WORKSPACE_RELATIVE",
            id="registered-parent-path-escapes",
        ),
    ],
)
def test_a2_invalid_workspace_state_refuses_and_publishes_nothing(
    tmp_path: Path, mutate, expected_code: str
) -> None:
    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    mutate(workspace)

    outcome = publish_document_manifest(workspace)

    _assert_published_nothing(workspace, outcome)
    assert outcome.refusal["code"] == expected_code, outcome.refusal


def test_a2_no_refusal_mentions_a_repair_a_caller_can_act_on(tmp_path: Path) -> None:
    """A refusal that names no repair leaves the operator stuck."""

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    _strip_frontmatter(workspace)

    outcome = publish_document_manifest(workspace)

    message = outcome.refusal["message"]
    assert outcome.refusal["details"]["study_id"]
    assert "extracted/" in message or "Stage 5" in message


def test_a2_gate_level_refusal_publishes_no_registry_entry(tmp_path: Path) -> None:
    """A candidate the frozen model accepts but the gate refuses still publishes nothing.

    The mutated payload here is handed to the *frozen adapter* directly, which is the
    only way to reach a gate-level refusal; the producer always builds a conforming
    candidate. The point of the test is that such a refusal is recorded, typed, and
    leaves the registry untouched.
    """

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    candidate = build_document_manifest_candidate(workspace)
    context = build_acceptance_context(workspace)

    mutated = copy.deepcopy(candidate.payload)
    mutated["inputs"] = [
        {"artifact_id": "ART-unregistered-parent", "sha256": "sha256:" + "9" * 64}
    ]
    result = accept_extraction_candidate(workspace, mutated, expected=context)

    assert result.accepted is False
    assert _registered_manifests(workspace) == {}
    assert result.rejection_path
    assert (workspace / result.rejection_path).is_file()


# --------------------------------------------------------------------------- #
# A3 -- canonical OperationStatus and honest audit events
# --------------------------------------------------------------------------- #


def test_a3_refusal_is_recorded_as_failed_not_success(tmp_path: Path) -> None:
    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    _strip_frontmatter(workspace)

    outcome = publish_document_manifest(workspace)
    assert outcome.accepted is False

    events = [
        e for e in _journal(workspace) if e["action"] == "DOCUMENT_MANIFEST_REFUSED"
    ]
    assert len(events) == 1
    assert events[0]["status"] == OperationStatus.FAILED.value
    assert events[0]["status"] in {member.value for member in OperationStatus}
    assert "EXTRACTED_FRONTMATTER_UNREADABLE" in events[0]["description"]
    assert not [
        e for e in _journal(workspace) if e["action"] == "DOCUMENT_MANIFEST_PUBLISHED"
    ]


def test_a3_success_event_reports_the_real_document_count(tmp_path: Path) -> None:
    state = _extracted_state(tmp_path, study_count=2)
    workspace = state["workspace"]

    outcome = publish_document_manifest(workspace)
    assert outcome.accepted

    events = [
        e for e in _journal(workspace) if e["action"] == "DOCUMENT_MANIFEST_PUBLISHED"
    ]
    assert len(events) == 1
    assert events[0]["status"] == OperationStatus.SUCCESS.value
    assert events[0]["metrics"]["documents"] == 2
    assert events[0]["agent_or_tool"] == "scholar-harness-extraction-producer"
    assert outcome.artifact_id in events[0]["outputs"][0]


def test_a3_producer_records_the_indexing_outcome_it_observed(
    tmp_path: Path, indexer: CapturingIndexer
) -> None:
    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    publish_document_manifest(workspace)

    result = index_accepted_documents(workspace)

    assert result["status"] == OperationStatus.SUCCESS.value
    events = [e for e in _journal(workspace) if e["action"] == "RAG_INDEX_BUILT"]
    assert len(events) == 1
    assert events[0]["status"] == OperationStatus.SUCCESS.value
    assert events[0]["metrics"]["accepted_documents"] == 1


def test_a3_indexing_nothing_is_failed_never_success(
    tmp_path: Path, indexer: CapturingIndexer
) -> None:
    """An accepted manifest with no usable document on disk is a real FAILED run."""

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    publish_document_manifest(workspace)
    _delete_extracted_output(workspace)

    result = index_accepted_documents(workspace)

    assert result["indexed_files"] == 0
    assert result["status"] == OperationStatus.FAILED.value
    assert not [e for e in _journal(workspace) if e["action"] == "RAG_INDEX_BUILT"]
    event = [e for e in _journal(workspace) if e["action"] == "RAG_INDEX_REJECTED"][-1]
    assert event["status"] == OperationStatus.FAILED.value


# --------------------------------------------------------------------------- #
# A4 -- E3 identity refusals stay fail-closed
# --------------------------------------------------------------------------- #


def test_a4_publication_refuses_without_a_recorded_identity(tmp_path: Path) -> None:
    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    _unregister_identity(workspace)

    outcome = publish_document_manifest(workspace)

    _assert_published_nothing(workspace, outcome)
    assert outcome.refusal["code"] == "WORKSPACE_IDENTITY_NOT_RECORDED"
    assert SLUG not in outcome.refusal["code"]


def test_a4_refusal_names_the_slug_it_declined_to_use(tmp_path: Path) -> None:
    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    (workspace / "project.json").write_text(
        json.dumps({"project_id": SLUG, "stats": {}}), encoding="utf-8"
    )

    outcome = publish_document_manifest(workspace)

    assert outcome.accepted is False
    assert outcome.refusal["code"] == "WORKSPACE_IDENTITY_NOT_RECORDED"
    assert SLUG in outcome.refusal["message"]


def test_a4_a_study_is_never_published_under_the_workspace_identity(
    tmp_path: Path,
) -> None:
    """``workspace_id`` on an included record carries a *study* id; that must not leak."""

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    outcome = publish_document_manifest(workspace)
    assert outcome.accepted, outcome.refusal

    payload = json.loads(
        (
            workspace / _registered_manifests(workspace)[outcome.artifact_id]["path"]
        ).read_text(encoding="utf-8")
    )
    manifest = DocumentManifestArtifact.model_validate(payload)
    for record in manifest.data.documents:
        assert record.study_id == state["included"][0]["workspace_id"]
        assert record.study_id != payload["workspace_id"]


# --------------------------------------------------------------------------- #
# A5 -- the trusted context never comes from the candidate
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "limb",
    ["workspace_id", "protocol_fingerprint", "corpus_fingerprint"],
)
def test_a5_candidate_supplied_fingerprint_mutation_is_refused(
    tmp_path: Path, limb: str
) -> None:
    """The gate refuses a mutated limb, and the producer never reads one back.

    The producer builds its candidate from the trusted context, so the mutation has
    to be applied by a caller to reach the gate -- which is precisely the attack the
    trusted context exists to stop.
    """

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    candidate = build_document_manifest_candidate(workspace)
    context = build_acceptance_context(workspace)

    mutated = copy.deepcopy(candidate.payload)
    mutated[limb] = "sha256:" + "9" * 64 if "fingerprint" in limb else "WSP-" + "9" * 32
    result = accept_extraction_candidate(workspace, mutated, expected=context)

    assert result.accepted is False
    assert any("MISMATCH" in issue.code for issue in result.issues)
    assert _registered_manifests(workspace) == {}


def test_a5_trusted_context_matches_recorded_state_not_a_candidate(
    tmp_path: Path,
) -> None:
    state = _extracted_state(tmp_path)
    workspace = state["workspace"]

    context = build_acceptance_context(workspace)
    candidate = build_document_manifest_candidate(workspace)

    project = json.loads((workspace / "project.json").read_text(encoding="utf-8"))
    corpus = json.loads(
        (
            workspace
            / next(
                entry["path"]
                for entry in _registry(workspace)["artifacts"].values()
                if entry["artifact_type"] == "corpus_snapshot"
            )
        ).read_text(encoding="utf-8")
    )
    assert context.workspace_id == project["registered_workspace_id"]
    assert context.protocol_fingerprint == corpus["protocol_fingerprint"]
    assert context.corpus_fingerprint == corpus["corpus_fingerprint"]
    # The candidate agrees with the context because the producer derives it from the
    # same recorded state -- never because the context was copied back out of it.
    assert candidate.payload["workspace_id"] == context.workspace_id
    assert candidate.payload["protocol_fingerprint"] == context.protocol_fingerprint
    assert candidate.payload["corpus_fingerprint"] == context.corpus_fingerprint


# --------------------------------------------------------------------------- #
# A5 -- the producer's own ``expected`` construction is under test here
# --------------------------------------------------------------------------- #
# The two tests above exercise the *frozen gate* with a context the test builds. That
# is a property of the gate, and it says nothing about what
# ``publish_document_manifest`` actually hands the gate. These two route the mutation
# through the producer instead, which is the only way to hold the producer's own
# ``expected=...`` construction to account.


class _ForeignIdentityProbe:
    """Make the candidate's payload claim a foreign identity; record ``expected``.

    The mutation is applied to the payload *before* the gate is reached, which is the
    only arrangement that can discriminate. Mutating a copy inside the gate wrapper
    leaves ``candidate.payload`` and recorded state in agreement, so the expectation
    would match either way and the test would prove nothing.

    With ``expected=candidate.context`` the gate sees recorded state and refuses. With
    ``expected=AcceptanceContext(**candidate.payload)`` -- the self-fulfilling pattern
    the reviewer rejected -- the mutated limb *is* the expectation, so the gate accepts
    and registers a manifest bound to a workspace that is not in ``project.json``.
    """

    def __init__(self, limb: str, monkeypatch) -> None:
        from scholar_harness import extraction_producer as producer

        self.producer = producer
        self.limb = limb
        self.expected: list[AcceptanceContext] = []
        self.payloads: list[dict[str, Any]] = []
        real_build = producer.build_document_manifest_candidate
        real_gate = producer.accept_extraction_candidate

        def build(workspace):
            candidate = real_build(workspace)
            payload = copy.deepcopy(candidate.payload)
            payload[self.limb] = (
                "sha256:" + "9" * 64
                if "fingerprint" in self.limb
                else "WSP-" + "9" * 32
            )
            return dataclasses.replace(candidate, payload=payload)

        def gate(workspace, payload, *, expected=None, actor=None):
            self.expected.append(expected)
            self.payloads.append(payload)
            return real_gate(workspace, payload, expected=expected, actor=actor)

        monkeypatch.setattr(producer, "build_document_manifest_candidate", build)
        monkeypatch.setattr(producer, "accept_extraction_candidate", gate)

    @property
    def received(self) -> AcceptanceContext:
        assert len(self.expected) == 1, self.expected
        return self.expected[0]

    @property
    def received_payload(self) -> dict[str, Any]:
        assert len(self.payloads) == 1, self.payloads
        return self.payloads[0]


@pytest.mark.parametrize(
    "limb",
    ["workspace_id", "protocol_fingerprint", "corpus_fingerprint"],
)
def test_a5_producer_hands_the_gate_a_context_from_recorded_state(
    tmp_path: Path, monkeypatch, limb: str
) -> None:
    """``expected`` must be the recorded-state context, not the payload's own limbs.

    The payload handed to the gate deliberately claims a foreign identity here, so the
    two implementations under comparison disagree. Asserting the recorded context, the
    refusal, *and* an untouched registry is what makes the self-fulfilling pattern
    impossible to reintroduce.
    """

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    recorded = build_acceptance_context(workspace)
    probe = _ForeignIdentityProbe(limb, monkeypatch)

    outcome = publish_document_manifest(workspace)

    assert probe.received == recorded, (
        "the producer handed the gate a context that is not the one derived from "
        f"recorded workspace state: {probe.received!r} != {recorded!r}"
    )
    assert getattr(probe.received, limb) == getattr(recorded, limb)
    # The payload really did claim something else, so the assertion above is not
    # vacuous: ``expected`` held the recorded limb while the payload held a foreign one.
    assert probe.received_payload[limb] != getattr(recorded, limb)
    _assert_published_nothing(workspace, outcome)
    assert outcome.refusal["code"] == "ACCEPTANCE_REFUSED"
    assert any(
        "MISMATCH" in code for code in outcome.refusal["details"]["issue_codes"]
    ), outcome.refusal["details"]["issue_codes"]


def test_a5_producer_refuses_a_foreign_identity_that_is_not_recorded(
    tmp_path: Path, monkeypatch
) -> None:
    """The reviewer's own demonstration, end to end: ``WSP-999...`` stays unregistered.

    The foreign workspace id is absent from ``project.json``, so a self-fulfilling
    expectation would return ``accepted=True``. The trusted context is what prevents
    that, and this test fails on the ``accepted is False`` line if it is removed.
    """

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    registered = json.loads((workspace / "project.json").read_text(encoding="utf-8"))[
        "registered_workspace_id"
    ]
    probe = _ForeignIdentityProbe("workspace_id", monkeypatch)

    outcome = publish_document_manifest(workspace)

    assert outcome.accepted is False
    assert outcome.status == OperationStatus.FAILED.value
    assert probe.received.workspace_id == registered
    assert _registered_manifests(workspace) == {}
    assert not (workspace / "literature" / "extraction_publications").exists()
    assert "WSP-" + "9" * 32 not in json.dumps(_registry(workspace), sort_keys=True)


def test_a5_candidate_carries_the_trusted_context_it_was_built_with(
    tmp_path: Path,
) -> None:
    """``Candidate.context`` is the single source of the expected limbs.

    It is what lets the producer pass the trusted context without re-deriving it (and
    without being tempted to read it back off the payload).
    """

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]

    candidate = build_document_manifest_candidate(workspace)

    assert candidate.context == build_acceptance_context(workspace)
    assert candidate.context.workspace_id == WORKSPACE_ID


def test_a5_status_reports_a_refusal_without_publishing(tmp_path: Path) -> None:
    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    _unregister_identity(workspace)

    report = publication_status(workspace)

    assert report["ready_to_publish"] is False
    assert report["recordings"]["refusal"]["code"] == "WORKSPACE_IDENTITY_NOT_RECORDED"
    assert _registered_manifests(workspace) == {}


# --------------------------------------------------------------------------- #
# Review repair 1 -- the four majors and the disclosure minor
# --------------------------------------------------------------------------- #


def test_index_without_an_accepted_manifest_refuses_before_touching_a_store(
    tmp_path: Path, monkeypatch
) -> None:
    """MAJOR 3: ``index`` must refuse *before* it creates a store or a network client.

    The workspace here is fully valid -- corpus, screening, registry, Stage 5 output --
    and has simply never published. Constructing Stage 6 first would create
    ``rag/chroma_db`` and download an embedding model before finding out there is
    nothing accepted to index, so the refusal has to come first and leave no trace.
    """

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]

    def explode(**_: Any) -> Any:
        raise AssertionError("Stage 6 was constructed for a workspace with no manifest")

    monkeypatch.setattr(orch_module, "ScholarIndexer", explode)
    monkeypatch.setattr(orch_module, "ResearchOrchestrator", explode)

    with pytest.raises(PublicationRefused) as caught:
        index_accepted_documents(workspace)

    assert caught.value.code == "DOCUMENT_MANIFEST_NOT_ACCEPTED"
    assert "publish" in caught.value.message
    assert not (workspace / "rag" / "chroma_db").exists()
    assert not (workspace / "rag").exists()
    assert [e for e in _journal(workspace) if e["action"] == "RAG_INDEX_BUILT"] == []


def test_index_never_indexes_an_unaccepted_manifest(
    tmp_path: Path, monkeypatch
) -> None:
    """MAJOR 3: a refused candidate is not an accepted manifest, so it is not indexable."""

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    _strip_frontmatter(workspace)

    refused = publish_document_manifest(workspace)
    assert refused.accepted is False

    monkeypatch.setattr(
        orch_module,
        "ScholarIndexer",
        lambda **_: pytest.fail("indexed a workspace with no accepted manifest"),
    )

    with pytest.raises(PublicationRefused) as caught:
        index_accepted_documents(workspace)

    assert caught.value.code == "DOCUMENT_MANIFEST_NOT_ACCEPTED"
    assert not (workspace / "rag" / "chroma_db").exists()


def test_publication_record_write_failure_is_typed_and_still_audited(
    tmp_path: Path, monkeypatch
) -> None:
    """MAJOR 4: the gate accepted, so the outcome must be recorded as accepted.

    The record file is provenance, not a gate input, so its failure cannot un-accept
    the artifact. It must surface as a typed refusal naming the real cause, the
    accepted artifact must stay registered and reachable by ``status``, the audit trail
    must say the acceptance really happened, and no temp file may be left behind.
    """

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    from scholar_harness import extraction_producer as producer

    def failing_write(ws: Path, candidate: Any, outcome: Any) -> str:
        raise OSError("simulated filesystem failure writing the publication record")

    monkeypatch.setattr(producer, "_write_publication_record", failing_write)

    with pytest.raises(PublicationRefused) as caught:
        publish_document_manifest(workspace)

    assert caught.value.code == "PUBLICATION_RECORD_UNWRITABLE"
    assert "simulated filesystem failure" in caught.value.message
    # The message names the artifact that really was accepted, so the operator knows
    # what is committed rather than guessing.
    assert caught.value.details["artifact_id"]
    assert caught.value.details["published_path"]
    manifests = _registered_manifests(workspace)
    assert list(manifests) == [caught.value.details["artifact_id"]]
    assert (
        workspace / manifests[caught.value.details["artifact_id"]]["path"]
    ).is_file()
    report = publication_status(workspace)
    assert report["ready_to_publish"] is True
    artifact_id = caught.value.details["artifact_id"]
    assert artifact_id in report["recordings"]["document_manifests"]

    # ...and the audit trail records what happened, including why the record is missing.
    published = [
        e for e in _journal(workspace) if e["action"] == "DOCUMENT_MANIFEST_PUBLISHED"
    ]
    assert len(published) == 1
    assert published[0]["status"] == OperationStatus.SUCCESS.value
    assert published[0]["metrics"]["documents"] == 1
    assert published[0]["parameters"]["publication_record_error"]
    # The accepted artifact is still an output; only the record path is absent.
    assert published[0]["outputs"] == [manifests[artifact_id]["path"]]
    assert _temp_leftovers(workspace) == []


def test_publication_record_is_written_atomically(tmp_path: Path, monkeypatch) -> None:
    """MAJOR 4: a partially written record never replaces a good one.

    The real writer is exercised here -- only the final ``os.replace`` is made to fail,
    which is the worst case: the temp file is fully written but the swap does not
    happen. The record must not appear, and the temp file must not be left behind for
    the next run to trip over.
    """

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    import os

    from scholar_harness import extraction_producer as producer

    class _NoSwap:
        """``os`` as the producer sees it, with only the atomic swap broken.

        Patching ``os.replace`` process-wide would also break the *frozen gate's* own
        atomic registry write, which runs first and is not what this test is about.
        """

        def __getattr__(self, name: str) -> Any:
            return getattr(os, name)

        @staticmethod
        def replace(src: Any, dst: Any) -> None:
            raise OSError("simulated crash at the atomic swap")

    monkeypatch.setattr(producer, "os", _NoSwap())

    with pytest.raises(PublicationRefused) as caught:
        publish_document_manifest(workspace)

    assert caught.value.code == "PUBLICATION_RECORD_UNWRITABLE"
    publications = workspace / "literature" / "extraction_publications"
    # Nothing claims to be a record -- not a truncated one, not a temp file.
    assert not list(publications.glob("*.json")) if publications.exists() else True
    assert _temp_leftovers(workspace) == []
    # The acceptance itself is still committed, because the gate already accepted it.
    assert len(_registered_manifests(workspace)) == 1


def test_republication_after_the_body_changes_is_refused_and_keeps_the_record(
    tmp_path: Path,
) -> None:
    """MAJOR 5: a mutated body is not the artifact that was already accepted.

    The artifact id is a fingerprint of the payload, so re-running over an edited body
    produces a *new* manifest that would sit beside the accepted one and overwrite its
    record. That is two artifacts claiming to be the accepted extraction of one study,
    so it must refuse with ``STALE_EXTRACTED_BODY`` and leave the original record and
    its provenance digests exactly as published.
    """

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    first = publish_document_manifest(workspace)
    assert first.accepted is True, first.refusal
    record_path = (
        workspace
        / "literature"
        / "extraction_publications"
        / f"{first.artifact_id}.json"
    )
    published_record = record_path.read_bytes()
    published_manifest = (
        workspace / _registered_manifests(workspace)[first.artifact_id]["path"]
    ).read_bytes()

    # A different, longer, still-usable body: valid extraction output, wrong content.
    _overwrite_body(
        workspace,
        "## Abstract\n\nA rewritten body.\n\n" + ("A substantive sentence. " * 200),
    )

    second = publish_document_manifest(workspace)

    # A typed refusal, not a silent replay: the artifact id is unchanged because the
    # frozen DocumentRecord carries no body field, so only the harness can see this.
    assert second.accepted is False
    assert second.status == OperationStatus.FAILED.value
    assert second.refusal["code"] == "STALE_EXTRACTED_BODY"
    details = second.refusal["details"]
    assert details["artifact_id"] == first.artifact_id
    assert details["publication_record"] == f"{first.artifact_id}.json"
    drifted = details["drifted"]
    recorded_document_ids = {
        item["document_id"] for item in json.loads(published_record)["documents"]
    }
    assert {entry["document_id"] for entry in drifted} == recorded_document_ids
    assert {entry["field"] for entry in drifted} == {
        "extracted_sha256",
        "extracted_file_sha256",
    }
    for entry in drifted:
        assert entry["published"] != entry["current"]

    # The accepted manifest is still the only one, and both the record and the
    # published payload are byte-identical to what was accepted.
    assert list(_registered_manifests(workspace)) == [first.artifact_id]
    assert record_path.read_bytes() == published_record
    assert (
        workspace / _registered_manifests(workspace)[first.artifact_id]["path"]
    ).read_bytes() == published_manifest
    # Exactly one publication event (the first run) and one refusal (this run).
    published_events = [
        e for e in _journal(workspace) if e["action"] == "DOCUMENT_MANIFEST_PUBLISHED"
    ]
    assert len(published_events) == 1
    refused_events = [
        e for e in _journal(workspace) if e["action"] == "DOCUMENT_MANIFEST_REFUSED"
    ]
    assert len(refused_events) == 1
    assert refused_events[0]["status"] == OperationStatus.FAILED.value
    assert _temp_leftovers(workspace) == []


def test_workspace_pdf_that_symlinks_out_of_the_workspace_is_refused(
    tmp_path: Path,
) -> None:
    """MINOR 7: a ``pdfs/`` entry that resolves outside the workspace is not evidence.

    Every other read in the producer goes through the containment rule. The study PDF
    lookup is the one that resolved its own hit, so a link planted inside ``pdfs/``
    could make a file from anywhere on the machine be hashed and cited as
    ``source_kind="workspace_pdf"`` -- i.e. as this workspace's evidence.
    """

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    study_id = state["study_ids"][0]
    outside = tmp_path / "outside" / "elsewhere.pdf"
    outside.parent.mkdir(parents=True)
    outside.write_bytes(b"%PDF-1.7\nnot this workspace's evidence\n")
    link = workspace / "pdfs" / f"{study_id}.pdf"
    link.parent.mkdir(exist_ok=True)
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError) as exc:  # pragma: no cover - platform
        pytest.skip(f"symlinks unavailable on this platform: {exc}")

    with pytest.raises(PublicationRefused) as caught:
        build_document_manifest_candidate(workspace)

    assert caught.value.code == "PATH_ESCAPES_WORKSPACE"
    assert str(outside) in caught.value.message or "outside" in caught.value.message
    assert _registered_manifests(workspace) == {}
    assert not (workspace / "literature" / "extraction_publications").exists()


def test_study_pdf_outside_the_workspace_is_refused(
    tmp_path: Path, monkeypatch
) -> None:
    """MINOR 7: a ``pdfs/`` hit that resolves outside the workspace is not evidence.

    Every other read in the producer goes through the containment rule; the study-PDF
    lookup is the one that resolved its own hit, so a file reached from outside the
    workspace could be hashed and cited as ``source_kind="workspace_pdf"`` -- i.e.
    presented as this workspace's evidence.

    The lookup is stubbed here so the guard is exercised on every platform; the
    symlinked case below covers the real resolution path where symlinks exist.
    """

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    outside = tmp_path / "outside" / "elsewhere.pdf"
    outside.parent.mkdir(parents=True)
    outside.write_bytes(b"%PDF-1.7\nnot this workspace's evidence\n")

    from scholar_harness import extraction_producer as producer

    monkeypatch.setattr(producer, "_study_pdf", lambda *_: outside)

    with pytest.raises(PublicationRefused) as caught:
        build_document_manifest_candidate(workspace)

    assert caught.value.code == "PATH_ESCAPES_WORKSPACE"
    assert "outside the workspace" in caught.value.message
    assert _registered_manifests(workspace) == {}
    assert not (workspace / "literature" / "extraction_publications").exists()


def test_republication_of_an_unchanged_body_is_idempotent(tmp_path: Path) -> None:
    """MAJOR 5's control: an unchanged body still replays idempotently.

    Without this, ``STALE_EXTRACTED_BODY`` could be "achieved" by refusing every replay,
    which would break the Stage 5 -> Stage 6 handoff on any retry.
    """

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    first = publish_document_manifest(workspace)

    second = publish_document_manifest(workspace)

    assert second.accepted is True
    assert second.idempotent is True
    assert second.artifact_id == first.artifact_id
    assert list(_registered_manifests(workspace)) == [first.artifact_id]


def test_skipped_registry_entries_are_disclosed_in_the_record_and_audit(
    tmp_path: Path,
) -> None:
    """MINOR 6: a registered artifact that is silently ignored is not disclosed.

    The workspace carries two real corpus generations, so one set of screening
    decisions belongs to a superseded generation. Passing it over is correct -- it is
    not evidence for this generation -- but a reader of the record has no other way to
    know it exists, so both the record and the audit event must name it and give the
    reason. Silence here is how a second generation looks like a single one.
    """

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    _register_prior_generation_screening(workspace)
    generations = _screening_artifact_ids(workspace)
    assert len(generations) == 2, generations

    outcome = publish_document_manifest(workspace)

    assert outcome.accepted is True, outcome.refusal
    assert outcome.skipped_registry_entries
    assert set(outcome.skipped_registry_entries.values()) == {"OTHER_GENERATION"}
    # The accepted manifest's own parents are never "skipped": a parent is used.
    assert not set(outcome.parent_artifact_ids) & set(outcome.skipped_registry_entries)
    assert set(outcome.skipped_registry_entries) == set(generations) - set(
        outcome.parent_artifact_ids
    )

    record = _publication_record(workspace, outcome.artifact_id)
    assert record["skipped_registry_entries"] == outcome.skipped_registry_entries

    event = next(
        e for e in _journal(workspace) if e["action"] == "DOCUMENT_MANIFEST_PUBLISHED"
    )
    assert (
        event["parameters"]["skipped_registry_entries"]
        == outcome.skipped_registry_entries
    )

    # The published manifest still declares only the current-generation parents.
    manifest = DocumentManifestArtifact.model_validate(
        json.loads((workspace / outcome.published_path).read_text("utf-8"))
    )
    published_parents = {parent.artifact_id for parent in manifest.inputs}
    assert published_parents == set(outcome.parent_artifact_ids)


def test_unreadable_registered_artifact_is_disclosed_when_it_is_skipped(
    tmp_path: Path,
) -> None:
    """MINOR 6: a registered artifact whose bytes are gone is disclosed, not dropped.

    The registry is the recorded proof of what was accepted, so a registered path with
    no file behind it is a real inconsistency. It cannot be used, and it must not be
    hidden either -- the skip has to name the artifact and the reason.
    """

    state = _extracted_state(tmp_path, study_count=2)
    workspace = state["workspace"]
    _register_prior_generation_screening(workspace)
    superseded, path = min(_screening_artifact_ids(workspace).items())
    (workspace / path).unlink()

    outcome = publish_document_manifest(workspace)

    assert outcome.accepted is True, outcome.refusal
    assert (
        outcome.skipped_registry_entries[superseded] == "ACCEPTED_ARTIFACT_UNREADABLE"
    )
    record = _publication_record(workspace, outcome.artifact_id)
    assert record["skipped_registry_entries"][superseded] == (
        "ACCEPTED_ARTIFACT_UNREADABLE"
    )
    assert _temp_leftovers(workspace) == []


def test_status_discloses_skipped_entries_without_publishing(tmp_path: Path) -> None:
    """MINOR 6: ``status`` must not report a clean workspace it had to skip past."""

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    _register_prior_generation_screening(workspace)

    report = publication_status(workspace)

    assert report["ready_to_publish"] is True
    skips = report["recordings"]["skipped_registry_entries"]
    assert set(skips.values()) == {"OTHER_GENERATION"}, skips
    assert _registered_manifests(workspace) == {}


# --------------------------------------------------------------------------- #
# Repair cycle 2 -- ``--json`` is a wire format
# --------------------------------------------------------------------------- #
# The three ``extract`` commands render through a ``Console(force_terminal=True)``, so
# Rich emits ANSI regardless of TTY, ``NO_COLOR`` or ``TERM=dumb``. A human banner
# printed alongside the JSON therefore made ``--json`` unparseable on the refusal path
# while ``status`` -- which returned early -- parsed fine. These tests drive the real
# typer app and the real standalone script and assert the *parsed* document, because
# the defect shipped green precisely by never parsing the output.


def _invoke(args: list[str]) -> Any:
    """Run the typer CLI with colour and terminal detection fully disabled."""

    from typer.testing import CliRunner

    from scholar_harness.cli import app

    runner = CliRunner()
    previous = {
        key: os.environ.get(key)
        for key in ("NO_COLOR", "TERM", "FORCE_COLOR", "COLUMNS")
    }
    os.environ["NO_COLOR"] = "1"
    os.environ["TERM"] = "dumb"
    os.environ.pop("FORCE_COLOR", None)
    os.environ["COLUMNS"] = "200"
    try:
        result = runner.invoke(app, ["extract", *args], color=False)
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    return result


def _assert_parses(result: Any) -> dict[str, Any]:
    """Assert stdout is *exactly* one JSON document, with no ANSI and no banner."""

    assert result.exit_code in (0, 1), (
        result.exit_code,
        result.stdout,
        result.exception,
    )
    assert "\x1b[" not in result.stdout, f"ANSI in --json output: {result.stdout!r}"
    assert "[" not in result.stdout.splitlines()[0][:1], result.stdout
    return json.loads(result.stdout)


def test_cli_status_json_parses_on_a_ready_workspace(tmp_path: Path) -> None:
    state = _extracted_state(tmp_path)
    report = _assert_parses(_invoke(["status", str(state["workspace"]), "--json"]))

    assert report["ready_to_publish"] is True
    assert report["recordings"]["workspace_id"] == WORKSPACE_ID
    assert report["extracted_files"]


def test_cli_status_json_parses_on_a_refusing_workspace(tmp_path: Path) -> None:
    state = _extracted_state(tmp_path)
    _unregister_identity(state["workspace"])
    report = _assert_parses(_invoke(["status", str(state["workspace"]), "--json"]))

    assert report["ready_to_publish"] is False
    assert report["recordings"]["refusal"]["code"] == "WORKSPACE_IDENTITY_NOT_RECORDED"
    assert report["recordings"]["refusal"]["message"]


def test_cli_publish_json_parses_on_success(tmp_path: Path) -> None:
    state = _extracted_state(tmp_path)
    result = _invoke(["publish", str(state["workspace"]), "--json"])
    payload = _assert_parses(result)

    assert result.exit_code == 0
    publication = payload["publication"]
    assert publication["accepted"] is True
    assert publication["status"] == OperationStatus.SUCCESS.value
    assert publication["artifact_id"]
    assert publication["published_path"]
    assert list(_registered_manifests(state["workspace"])) == [
        publication["artifact_id"]
    ]


def test_cli_publish_json_parses_on_refusal(tmp_path: Path) -> None:
    """The exact defect: a refusal banner used to precede the JSON on stdout."""

    state = _extracted_state(tmp_path)
    _strip_frontmatter(state["workspace"])
    result = _invoke(["publish", str(state["workspace"]), "--json"])
    payload = _assert_parses(result)

    assert result.exit_code == 1
    publication = payload["publication"]
    assert publication["accepted"] is False
    assert publication["status"] == OperationStatus.FAILED.value
    assert publication["refusal"]["code"] == "EXTRACTED_FRONTMATTER_UNREADABLE"
    assert publication["refusal"]["message"]
    assert _registered_manifests(state["workspace"]) == {}


def test_cli_index_json_parses_on_success(
    tmp_path: Path, indexer: CapturingIndexer
) -> None:
    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    _invoke(["publish", str(workspace)])

    payload = _assert_parses(_invoke(["index", str(workspace), "--json"]))

    assert payload["status"] == OperationStatus.SUCCESS.value
    assert payload["indexed_files"] == 1
    assert isinstance(payload["refused"], list)


def test_cli_index_json_parses_on_refusal(
    tmp_path: Path, indexer: CapturingIndexer
) -> None:
    state = _extracted_state(tmp_path)
    result = _invoke(["index", str(state["workspace"]), "--json"])
    payload = _assert_parses(result)

    assert result.exit_code == 1
    assert payload["stage6_refused"] is True
    assert payload["status"] == OperationStatus.FAILED.value
    assert payload["code"] == "DOCUMENT_MANIFEST_NOT_ACCEPTED"
    assert payload["message"]
    assert not (state["workspace"] / "rag" / "chroma_db").exists()


def test_cli_publish_index_json_is_one_document(
    tmp_path: Path, indexer: CapturingIndexer
) -> None:
    """``--index`` must not append a second JSON body and break the stream."""

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]

    result = _invoke(["publish", str(workspace), "--index", "--json"])
    payload = _assert_parses(result)

    assert result.exit_code == 0
    assert payload["publication"]["accepted"] is True
    assert payload["indexing"]["indexed_files"] == 1


def test_cli_publish_index_json_on_refusal_is_one_document(tmp_path: Path) -> None:
    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    _strip_frontmatter(workspace)

    result = _invoke(["publish", str(workspace), "--index", "--json"])
    payload = _assert_parses(result)

    assert result.exit_code == 1
    assert payload["publication"]["refusal"]["code"] == (
        "EXTRACTED_FRONTMATTER_UNREADABLE"
    )
    assert payload["indexing"] == {"skipped": "no accepted document manifest"}


@pytest.mark.parametrize(
    ("subcommand", "refused_exit_code"),
    [("status", 0), ("publish", 1), ("index", 1)],
)
def test_cli_human_output_is_unchanged_by_the_json_fix(
    tmp_path: Path, subcommand: str, refused_exit_code: int
) -> None:
    """Without ``--json`` the human block must still be there, and still be prose.

    ``status`` exits 0 on a refusal by design -- it reports, it does not gate -- so the
    expected exit code is per-subcommand and is asserted here rather than assumed.
    """

    state = _extracted_state(tmp_path)
    _strip_frontmatter(state["workspace"])

    result = _invoke([subcommand, str(state["workspace"])])

    assert result.exit_code == refused_exit_code, result.stdout
    assert result.stdout.strip()
    with pytest.raises(json.JSONDecodeError):
        json.loads(result.stdout)


def _workspace_dir(root: Path, name: str) -> Path:
    """Give each case its own parent; ``_build_workspace`` does ``mkdir`` on the dir."""

    target = root / name
    target.mkdir(parents=True, exist_ok=True)
    return target


def _script(args: list[str], *, env: dict[str, str] | None = None) -> tuple[int, str]:
    """Run the standalone script exactly as an operator would.

    The environment is inherited and only ``NO_COLOR``/``TERM`` are pinned, so the
    subprocess sees a real, working environment. An earlier hand-rolled allowlist of four
    variables looked hermetic but silently broke any case that reached Stage 6, which is
    the opposite of hermetic -- a stripped environment fails for unrelated reasons.
    ``env`` adds per-case overrides (the embedder shim) on top of that.
    """

    import subprocess

    child_env = {**os.environ, "NO_COLOR": "1", "TERM": "dumb", **(env or {})}
    child_env.pop("FORCE_COLOR", None)

    completed = subprocess.run(
        ["uv", "run", "python", str(AGENT_EXTRACT), *args],
        capture_output=True,
        text=True,
        check=False,
        env=child_env,
    )
    return completed.returncode, completed.stdout


def test_script_status_and_publish_json_parse_in_a_real_subprocess(
    tmp_path: Path,
) -> None:
    """Drive the real script entry point under ``NO_COLOR``/``TERM=dumb``.

    ``subprocess`` rather than ``main()`` so the assertion covers what an operator's
    shell actually receives, including any import-time stdout writes.
    """

    ready = _extracted_state(_workspace_dir(tmp_path, "ready"))

    code, stdout = _script(["status", str(ready["workspace"]), "--json"])
    report = json.loads(stdout)
    assert code == 0
    assert report["ready_to_publish"] is True
    assert "\x1b[" not in stdout, f"ANSI in --json output: {stdout!r}"

    code, stdout = _script(["publish", str(ready["workspace"]), "--json"])
    published = json.loads(stdout)
    assert code == 0
    assert published["publication"]["accepted"] is True
    assert published["publication"]["artifact_id"]
    assert "\x1b[" not in stdout, f"ANSI in --json output: {stdout!r}"

    refused = _extracted_state(_workspace_dir(tmp_path, "refused"))
    _strip_frontmatter(refused["workspace"])

    code, stdout = _script(["publish", str(refused["workspace"]), "--json"])
    payload = json.loads(stdout)
    assert code == 1
    assert payload["publication"]["accepted"] is False
    assert payload["publication"]["refusal"]["code"] == (
        "EXTRACTED_FRONTMATTER_UNREADABLE"
    )
    assert "\x1b[" not in stdout, f"ANSI in --json output: {stdout!r}"


def test_script_index_json_parses_on_success_and_refusal(
    tmp_path: Path, indexer: CapturingIndexer, capsys: pytest.CaptureFixture[str]
) -> None:
    """``main()`` in-process so the stubbed indexer keeps Stage 6 hermetic.

    The same two cases are also driven through a *real* subprocess further down, with the
    rag kit's deterministic ``mock`` embedder injected, so this in-process pair is the
    fast duplicate rather than the only evidence.
    """

    from scholar_harness import agent_extract
    from scholar_harness.agent_extract import EXIT_OK, EXIT_REFUSED

    workspace = _extracted_state(tmp_path)["workspace"]
    capsys.readouterr()  # discard the screening handoff's own chatter

    code = agent_extract.main(["index", str(workspace), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == EXIT_REFUSED
    assert payload["indexing_refused"]["code"] == "DOCUMENT_MANIFEST_NOT_ACCEPTED"

    assert agent_extract.main(["publish", str(workspace)]) == EXIT_OK
    capsys.readouterr()

    assert agent_extract.main(["index", str(workspace), "--json"]) == EXIT_OK
    indexed = json.loads(capsys.readouterr().out)
    assert indexed["status"] == OperationStatus.SUCCESS.value
    assert indexed["indexed_files"] == 1


def _mock_embedder_dir(root: Path) -> Path:
    """Force the rag kit's deterministic ``mock`` embedder inside a real subprocess.

    Stage 6's default provider is ``sentence-transformers``, which downloads
    ``all-MiniLM-L6-v2`` on a cold cache, so a subprocess success case would otherwise be
    a network test. ``scholar_rag.embedder.get_embedder`` documents ``mock`` as the
    provider "for unit tests / CI without GPU/downloads", and :class:`CapturingIndexer`
    already binds that provider for the in-process cases -- so this shim makes the
    subprocess cases hermetic in exactly the way the file already does.

    It works by patching the module attribute *before* ``scholar_rag.indexer`` is
    imported, because ``indexer.py`` binds ``get_embedder`` with a module-level
    ``from ... import``. A ``sitecustomize`` on ``PYTHONPATH`` is the only injection point
    that runs early enough without touching the kits or ``orchestrator.py``, and the venv
    ships no ``sitecustomize`` of its own to shadow.
    """

    shim = root / "mock_embedder_shim"
    shim.mkdir(parents=True, exist_ok=True)
    (shim / "sitecustomize.py").write_text(
        "import os\n"
        "\n"
        "if os.environ.get('SCHOLAR_RAG_EMBEDDER_PROVIDER') == 'mock':\n"
        "    import scholar_rag.embedder as _embedder\n"
        "\n"
        "    _real = _embedder.get_embedder\n"
        "\n"
        "    def _mocked(provider='mock', model_name=None, api_key=None):\n"
        "        return _real('mock')\n"
        "\n"
        "    _embedder.get_embedder = _mocked\n",
        encoding="utf-8",
    )
    return shim


def _offline_embedder_env(shim: Path) -> dict[str, str]:
    """``PYTHONPATH`` for the shim, with the HF hubs pinned offline to prove no download."""

    return {
        "SCHOLAR_RAG_EMBEDDER_PROVIDER": "mock",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "PYTHONPATH": os.pathsep.join(
            [
                str(shim),
                *([os.environ["PYTHONPATH"]] if os.environ.get("PYTHONPATH") else []),
            ]
        ),
    }


def _script_json(
    args: list[str], **env_overrides: str
) -> tuple[int, dict[str, Any], str]:
    """Run the script with ``--json`` and return (exit code, parsed document, stdout)."""

    code, stdout = _script([*args, "--json"], env=env_overrides)
    assert "\x1b[" not in stdout, f"ANSI in --json output: {stdout!r}"
    # A single document, asserted by parsing the whole stream: a banner before it, or a
    # second body after it, both fail here rather than degrading to a substring match.
    return code, json.loads(stdout), stdout


def test_script_index_json_refusal_in_a_real_subprocess(tmp_path: Path) -> None:
    """Standalone ``index --json`` with no accepted manifest: one document, exit 1.

    The preflight refuses before Stage 6 is constructed, so this case runs no embedder at
    all and needs no stub -- it is hermetic as written.
    """

    workspace = _extracted_state(tmp_path)["workspace"]

    code, payload, _ = _script_json(["index", str(workspace)])

    assert code == 1
    # The script's own envelope, not the cli.py ``stage6_refused`` shape: the two entry
    # points disagree here on purpose and that divergence is out of scope.
    assert payload["indexing_refused"]["code"] == "DOCUMENT_MANIFEST_NOT_ACCEPTED"
    assert payload["indexing_refused"]["message"]
    assert not (workspace / "rag" / "chroma_db").exists()


def test_script_index_json_success_in_a_real_subprocess(tmp_path: Path) -> None:
    """Standalone ``index --json`` after a real publish: one document, exit 0."""

    workspace = _extracted_state(tmp_path)["workspace"]
    offline = _offline_embedder_env(_mock_embedder_dir(tmp_path))

    code, published, _ = _script_json(["publish", str(workspace)], **offline)
    assert code == 0
    assert published["publication"]["accepted"] is True

    code, indexed, _ = _script_json(["index", str(workspace)], **offline)

    assert code == 0
    assert indexed["status"] == OperationStatus.SUCCESS.value
    assert indexed["indexed_files"] >= 1
    assert indexed["refused"] == []
    # Every identity limb Stage 6 bound is present and non-empty. Which artifact the
    # parent resolves to is scientific-lineage territory test_a1 already owns, so this
    # asserts the shape of the parsed document rather than restating that claim.
    document = indexed["documents"][0]
    assert all(
        isinstance(document[limb], str) and document[limb]
        for limb in (
            "document_id",
            "study_id",
            "parent_artifact_id",
            "screening_decision_id",
        )
    ), document
    assert (workspace / "rag" / "chroma_db").exists()


def test_script_index_json_zero_indexed_exits_one_in_a_real_subprocess(
    tmp_path: Path,
) -> None:
    """A run that indexed nothing must not exit 0, on the real script path too."""

    workspace = _extracted_state(tmp_path)["workspace"]
    offline = _offline_embedder_env(_mock_embedder_dir(tmp_path))

    assert _script_json(["publish", str(workspace)], **offline)[0] == 0
    _delete_extracted_output(workspace)

    code, payload, _ = _script_json(["index", str(workspace)], **offline)

    assert code == 1
    assert payload["status"] == OperationStatus.FAILED.value
    assert payload["indexed_files"] == 0


def test_script_status_json_identity_refusal_in_a_real_subprocess(
    tmp_path: Path,
) -> None:
    """``WORKSPACE_IDENTITY_NOT_RECORDED`` asserted through the script, not just the cli.

    Cheap and hermetic: ``status`` only reads recorded state, so it refuses without
    running the gate or touching an embedder.
    """

    workspace = _extracted_state(tmp_path)["workspace"]
    _unregister_identity(workspace)

    code, payload, _ = _script_json(["status", str(workspace)])

    assert code == 0  # status reports, it does not gate
    assert payload["ready_to_publish"] is False
    assert payload["recordings"]["refusal"]["code"] == (
        "WORKSPACE_IDENTITY_NOT_RECORDED"
    )
    assert payload["recordings"]["refusal"]["message"]


def test_cli_index_json_zero_indexed_exits_one(
    tmp_path: Path, indexer: CapturingIndexer
) -> None:
    """The cli half of the same rule: a FAILED run is reported as FAILED, and exits 1."""

    state = _extracted_state(tmp_path)
    workspace = state["workspace"]
    assert _invoke(["publish", str(workspace)]).exit_code == 0
    _delete_extracted_output(workspace)

    result = _invoke(["index", str(workspace), "--json"])
    payload = _assert_parses(result)

    assert result.exit_code == 1
    assert payload["status"] == OperationStatus.FAILED.value
    assert payload["indexed_files"] == 0
    # Not a typed refusal: this run reported an outcome, it did not decline to start.
    assert "stage6_refused" not in payload


def _temp_leftovers(workspace: Path) -> list[str]:
    """Any temp file the producer left behind, anywhere under the workspace."""

    return [
        path.relative_to(workspace).as_posix()
        for path in workspace.rglob("*")
        if path.is_file() and (path.name.startswith(".") or path.suffix == ".tmp")
    ]


def _register_prior_generation_screening(workspace: Path) -> str:
    """Register a real ``screening_decisions`` artifact from an *older* protocol.

    This is the state the reviewer asked to be disclosed: the registry holds two
    generations of screening decisions. The superseded one cannot be a parent of this
    generation's manifest, but it was genuinely accepted by the frozen gate, so the
    producer must pass it over *visibly*.

    Nothing is hand-written into the registry. The envelope is the real one the
    collector produced, re-stamped with a different protocol fingerprint and run id and
    re-identified the way ``agent_screen.collect`` identifies it, then put through the
    real frozen gate like any other artifact.
    """

    from scholar_harness.contracts.canonical import deterministic_id
    from scholar_harness.contracts.identifiers import IdentifierKind

    registry = _registry(workspace)
    current_id, current_entry = next(
        (artifact_id, entry)
        for artifact_id, entry in registry["artifacts"].items()
        if entry["artifact_type"] == "screening_decisions"
    )
    current = json.loads(
        (workspace / current_entry["path"]).read_text(encoding="utf-8")
    )
    batch_id = current["inputs"][0]["artifact_id"]
    current_batch = json.loads(
        (workspace / registry["artifacts"][batch_id]["path"]).read_text(
            encoding="utf-8"
        )
    )
    decisions = current["data"]["decisions"]
    prior_protocol_fingerprint = "sha256:" + "3" * 64
    prior_run_id = "RUN-search-prior-generation"
    assert prior_protocol_fingerprint != current["protocol_fingerprint"]

    prior = dict(current)
    prior["protocol_fingerprint"] = prior_protocol_fingerprint
    prior["run_id"] = "RUN-search-prior-generation"
    prior["created_at"] = "2026-09-14T09:00:00+00:00"
    # The gate checks the envelope against its own binding, so the binding is
    # re-stamped with the prior generation exactly as ``agent_screen.collect`` would.
    prior["data"] = dict(current["data"])
    prior["data"]["binding"] = {
        **current["data"]["binding"],
        "protocol_fingerprint": prior_protocol_fingerprint,
        "screening_run_id": prior_run_id,
    }
    prior["data"]["batch_id"] = "batch-prior-generation-001"

    # The decisions are bound to a screening *batch*, so the prior generation needs its
    # own batch too. It is the real batch re-stamped, re-identified, and accepted -- the
    # gate refuses a decision set whose binding disagrees with its parent batch, so this
    # is the only way a second generation can be genuinely accepted rather than forged.
    prior_batch = dict(current_batch)
    prior_batch["protocol_fingerprint"] = prior_protocol_fingerprint
    prior_batch["run_id"] = "RUN-search-prior-generation"
    prior_batch["created_at"] = "2026-09-14T08:00:00+00:00"
    prior_batch["data"] = dict(current_batch["data"])
    prior_batch["data"]["binding"] = dict(prior["data"]["binding"])
    prior_batch_id = prior["data"]["batch_id"]
    prior_batch["data"]["batch_id"] = prior["data"]["batch_id"]
    prior_batch["artifact_id"] = deterministic_id(
        IdentifierKind.ARTIFACT,
        current_batch["workspace_id"],
        {"kind": "screening-batch-artifact", "batch_id": prior_batch_id},
    )
    batch_result = accept_artifact(
        workspace,
        prior_batch,
        expected=AcceptanceContext(
            workspace_id=prior_batch["workspace_id"],
            protocol_fingerprint=prior_protocol_fingerprint,
            corpus_fingerprint=prior_batch["corpus_fingerprint"],
        ),
        actor="agent_screen.prepare",
    )
    assert batch_result.accepted is True, [
        (issue.code, issue.message) for issue in batch_result.issues
    ]
    prior["inputs"] = [
        {
            "artifact_id": prior_batch["artifact_id"],
            "sha256": _registry(workspace)["artifacts"][prior_batch["artifact_id"]][
                "sha256"
            ],
        }
    ]
    prior["artifact_id"] = deterministic_id(
        IdentifierKind.ARTIFACT,
        current["workspace_id"],
        {
            "kind": "screening-decisions",
            "batch_id": "prior-generation-batch",
            "decision_ids": [item["decision_id"] for item in decisions],
        },
    )
    result = accept_artifact(
        workspace,
        prior,
        expected=AcceptanceContext(
            workspace_id=prior["workspace_id"],
            protocol_fingerprint=prior_protocol_fingerprint,
            corpus_fingerprint=prior["corpus_fingerprint"],
        ),
        actor="agent_screen.collect",
    )
    assert result.accepted is True, [
        (issue.code, issue.message) for issue in result.issues
    ]
    assert prior["artifact_id"] != current_id
    assert prior["artifact_id"] in _screening_artifact_ids(workspace)
    return prior["artifact_id"]


def _screening_artifact_ids(workspace: Path) -> dict[str, str]:
    return {
        artifact_id: entry["path"]
        for artifact_id, entry in _registry(workspace)["artifacts"].items()
        if entry["artifact_type"] == "screening_decisions"
    }


# --------------------------------------------------------------------------- #
# Mutation helpers (each breaks one recorded truth; none fabricate state)
# --------------------------------------------------------------------------- #


def _extracted_path(workspace: Path) -> Path:
    """The one real extracted file, named the way Stage 5 named it."""

    from scholar_harness.orchestrator import _extraction_file_stem

    included = json.loads(
        (workspace / "literature" / "included.json").read_text(encoding="utf-8")
    )
    return workspace / "extracted" / f"{_extraction_file_stem(included[0])}.md"


def _overwrite_body(workspace: Path, body: str) -> None:
    """Replace the body, keeping the frontmatter block Stage 5 wrote."""

    path = _extracted_path(workspace)
    text = path.read_text(encoding="utf-8")
    head, marker, _rest = text.partition("\n---\n")
    assert marker, "the extracted file must have a frontmatter block"
    path.write_text(head + "\n---\n\n" + body, encoding="utf-8")


def _overwrite_frontmatter(workspace: Path, **values: str) -> None:
    """Rewrite the frontmatter block with *values* replaced, body untouched."""

    path = _extracted_path(workspace)
    lines = path.read_text(encoding="utf-8").splitlines()
    replaced: set[str] = set()
    for index, line in enumerate(lines):
        for key, value in values.items():
            if line.startswith(f"{key}: "):
                lines[index] = f'{key}: "{value}"'
                replaced.add(key)
    assert replaced == set(values), sorted(set(values) - replaced)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _strip_frontmatter(workspace: Path) -> None:
    path = _extracted_path(workspace)
    text = path.read_text(encoding="utf-8")
    _head, marker, rest = text.partition("\n---\n")
    assert marker, "the extracted file must have a frontmatter block"
    path.write_text(rest.lstrip("\n"), encoding="utf-8")


def _delete_extracted_output(workspace: Path) -> None:
    for path in (workspace / "extracted").glob("*.md"):
        path.unlink()


def _append_duplicate_included(workspace: Path) -> None:
    path = workspace / "literature" / "included.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps(records + [copy.deepcopy(records[0])]), encoding="utf-8")


def _unregister_screening_parent(workspace: Path) -> None:
    registry = _registry(workspace)
    registry["artifacts"] = {
        artifact_id: entry
        for artifact_id, entry in registry["artifacts"].items()
        if entry["artifact_type"] != "screening_decisions"
    }
    (workspace / "audit" / "artifact_registry.json").write_text(
        json.dumps(registry, indent=2), encoding="utf-8"
    )


def _mutate_protocol(workspace: Path) -> None:
    """Amend a *fingerprinted* research question after the corpus was accepted."""

    path = workspace / "protocol.json"
    protocol = json.loads(path.read_text(encoding="utf-8"))
    protocol["research_questions"][0]["text"] += " (amended after screening)"
    path.write_text(json.dumps(protocol), encoding="utf-8")


def _reidentify_project(workspace: Path, slug: str) -> None:
    (workspace / "project.json").write_text(
        json.dumps({"project_id": slug, "registered_workspace_id": slug, "stats": {}}),
        encoding="utf-8",
    )


def _unregister_identity(workspace: Path) -> None:
    manifest = json.loads((workspace / "project.json").read_text(encoding="utf-8"))
    manifest.pop("registered_workspace_id", None)
    (workspace / "project.json").write_text(json.dumps(manifest), encoding="utf-8")


def _escape_registry_path(workspace: Path) -> None:
    registry = _registry(workspace)
    for entry in registry["artifacts"].values():
        if entry["artifact_type"] == "screening_decisions":
            entry["path"] = "../outside/ART-screening-decisions.json"
    (workspace / "audit" / "artifact_registry.json").write_text(
        json.dumps(registry, indent=2), encoding="utf-8"
    )


def _exclude_the_study_in_its_screening_parent(workspace: Path) -> None:
    """Keep the accepted screening generation, drop its INCLUDE decision.

    The generation still exists and the registry still records the payload honestly,
    so the only defect left is that ``included.json`` claims a study the accepted
    screening decision never admitted.
    """

    from hashlib import sha256

    registry = _registry(workspace)
    entry = next(
        item
        for item in registry["artifacts"].values()
        if item["artifact_type"] == "screening_decisions"
    )
    payload_path = workspace / entry["path"]
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    for decision in payload["data"]["decisions"]:
        decision["decision"] = "EXCLUDE"
        decision["reason"] = "wrong population for this protocol"
    payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    entry["sha256"] = "sha256:" + sha256(payload_path.read_bytes()).hexdigest()
    (workspace / "audit" / "artifact_registry.json").write_text(
        json.dumps(registry, indent=2), encoding="utf-8"
    )


# --------------------------------------------------------------------------- #
# T-131 E3 acceptance adapter -- hermetic adapter assertions only
# --------------------------------------------------------------------------- #
# The kit produces a candidate; the harness adapter decides (handoff section 6).
# Every test below is hermetic: a deterministic mock embedder, offline flags,
# tmp dirs only, no network, no model download. The candidate is built through
# the real chunker/sidecar path (``_build_candidate_manifest``), and the live
# backend is a fake ``VerifiableBackend`` holding exactly the declared set, so
# the adapter's seven ordered checks, atomic publication, and idempotency are
# proven without opening a Chroma file.
#
# MISSING-ID disposition (T-140): this file claims only the adapter-owned
# ``E3-NEG-037`` / ``E3-POS-008`` acceptance boundary (via the adapter's
# ``index-acceptance-v1`` record and section 6.6 event). Kit-owned
# (009,011,017,021,022,030,031,035,050), publish-time frozen-gate (039),
# MCP (POS-009), and CI (POS-012) stay parked in
# ``tests/conformance/test_e3_index_lineage_boundary.py``.
# --------------------------------------------------------------------------- #

_ADAPTER_RUN_ID = "RUN-" + "a1" * 16
_ADAPTER_CREATED_AT = "2026-09-27T00:00:00Z"
_ADAPTER_COMMIT = "ab" * 20
_ADAPTER_VERSION = "0.2.0"
_ADAPTER_ACCEPTED_AT = "2026-09-28T00:00:00Z"
_ADAPTER_MANIFEST_RELPATH = "rag/index/RUN-a1/manifest.json"


def _adapter_mock_embedder(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Deterministic mock embedder for adapter candidate construction."""

    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    from scholar_rag.embedder import get_embedder as _kit_get_embedder

    mock = _kit_get_embedder("mock")
    mock.dimension = 384
    monkeypatch.setattr(orch_module, "get_embedder", lambda **_: mock)
    return mock


def _adapter_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, study_count: int = 1
) -> dict[str, Any]:
    """Build a real workspace plus a real kit candidate and its fake reader."""

    from scholar_harness.index_acceptance import ACCEPTED_RELPATH
    from scholar_harness.orchestrator import ResearchOrchestrator
    from scholar_rag.index_service import _build_candidate_manifest
    from scholar_rag.index_verifier import VisibleRow

    _adapter_mock_embedder(monkeypatch)
    state = _extracted_state(tmp_path, study_count=study_count)
    workspace = state["workspace"]
    outcome = publish_document_manifest(workspace)
    assert outcome.accepted is True, outcome.refusal
    orch = ResearchOrchestrator(workspace)
    parent_view = orch._build_parent_view()
    assert parent_view is not None
    request = orch._build_index_service_request(
        chroma_dir=tmp_path / "chroma-unused",
        parent_view=parent_view,
        run_id=_ADAPTER_RUN_ID,
        created_at=_ADAPTER_CREATED_AT,
        producer_commit=_ADAPTER_COMMIT,
        producer_version=_ADAPTER_VERSION,
    )
    assert len(request.sources) == study_count
    manifest = _build_candidate_manifest(
        request, docs_path=workspace / "extracted", workspace_root=workspace
    )
    payload = manifest.canonical_payload()
    rows = [
        VisibleRow(
            row_key=f"{_ADAPTER_RUN_ID}#{chunk.chunk_id}",
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            study_id=chunk.study_id,
            embedding_dimension=manifest.embedder.dimension,
            stored_text=None,
        )
        for chunk in manifest.visible_chunks
    ]

    class _FakeReader:
        def __init__(self, rows: Any, space: str) -> None:
            self._rows = list(rows)
            self._space = space
            self._ids = sorted(row.chunk_id for row in self._rows)

        def visible_ids(self) -> list[str]:
            return list(self._ids)

        def visible_count(self) -> int:
            return len(self._ids)

        def visible_rows(self) -> list[Any]:
            return list(self._rows)

        def read_collection_metadata(self) -> dict[str, Any]:
            return {"hnsw:space": self._space}

    reader = _FakeReader(rows, manifest.backend.hnsw_space)
    return {
        "workspace": workspace,
        "state": state,
        "request": request,
        "manifest": manifest,
        "payload": payload,
        "reader": reader,
        "rows": rows,
    }


def _adapter_journal(workspace: Path) -> list[dict[str, Any]]:
    return _journal(workspace)


def _adapter_accepted_bytes(workspace: Path) -> bytes | None:
    from scholar_harness.index_acceptance import ACCEPTED_RELPATH

    path = workspace / ACCEPTED_RELPATH
    return path.read_bytes() if path.is_file() else None


def test_adapter_accepted_parent_succeeds_with_record_and_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AD-1..AD-7 success: one accepted record plus one full section 6.6 event."""

    from scholar_harness.index_acceptance import (
        ACCEPTANCE_SCHEMA_VERSION,
        ACCEPTED_RELPATH,
        accept_index_candidate,
    )

    built = _adapter_candidate(tmp_path, monkeypatch)
    workspace = built["workspace"]
    before_registry = (workspace / "audit" / "artifact_registry.json").read_bytes()
    journal_before = _adapter_journal(workspace)

    result = accept_index_candidate(
        workspace,
        built["payload"],
        run_id=_ADAPTER_RUN_ID,
        manifest_path=_ADAPTER_MANIFEST_RELPATH,
        reader=built["reader"],
        accepted_at=_ADAPTER_ACCEPTED_AT,
    )

    assert result.accepted is True, (result.failing_step, result.code, result.detail)
    assert result.failing_step is None
    assert result.code is None
    assert result.complete is True
    assert result.reused is False
    assert result.manifest_id == built["manifest"].manifest_id
    # The accepted record exists, carries the adapter schema, and seals itself.
    accepted_path = workspace / ACCEPTED_RELPATH
    assert accepted_path.is_file()
    record = json.loads(accepted_path.read_text(encoding="utf-8"))
    assert record["schema_version"] == ACCEPTANCE_SCHEMA_VERSION
    assert record["schema_version"] == "index-acceptance-v1"
    assert record["manifest_id"] == built["manifest"].manifest_id
    assert record["manifest_path"] == _ADAPTER_MANIFEST_RELPATH
    assert record["status"] == built["manifest"].status
    assert record["counts"]["visible_chunks"] == built["manifest"].counts.visible_chunks
    # The transaction wrote exactly one new journal line: the canonical event.
    journal_after = _adapter_journal(workspace)
    assert len(journal_after) == len(journal_before) + 1
    event = journal_after[-1]
    assert event["action"] == "RAG_INDEX_BUILT"
    params = event["parameters"]
    for required in (
        "workspace_id",
        "run_id",
        "parent_artifact_id",
        "parent_artifact_sha256",
        "manifest_id",
        "manifest_path",
        "artifact_checksum",
        "index_fingerprint",
        "chunk_set_fingerprint",
        "configuration_fingerprint",
        "production_fingerprint",
        "protocol_fingerprint",
        "corpus_fingerprint",
        "counts",
        "rejected_documents",
        "embedding_identity",
        "configuration",
    ):
        assert required in params, required
    assert "failing_step" not in params
    assert "code" not in params
    blob = json.dumps(event, sort_keys=True)
    assert "chroma_db" not in blob and "db_path" not in blob
    assert "sk-" not in blob and "Bearer" not in blob
    # No registry mutation, no Contract publication of the sidecar.
    assert (
        workspace / "audit" / "artifact_registry.json"
    ).read_bytes() == before_registry
    assert "failing_step" not in params


def test_adapter_each_failed_check_yields_its_code_and_no_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AD-1..AD-6: every ordered check refuses with its canonical code."""

    import copy

    from scholar_harness.index_acceptance import (
        ACCEPTED_RELPATH,
        accept_index_candidate,
    )
    from scholar_rag.index_manifest import compute_fingerprints

    built = _adapter_candidate(tmp_path, monkeypatch)
    workspace = built["workspace"]
    payload = built["payload"]
    reader = built["reader"]

    def attempt(mutated: dict[str, Any], *, reader_override: Any = None) -> Any:
        return accept_index_candidate(
            workspace,
            mutated,
            run_id=_ADAPTER_RUN_ID,
            manifest_path=_ADAPTER_MANIFEST_RELPATH,
            reader=reader_override if reader_override is not None else reader,
            accepted_at=_ADAPTER_ACCEPTED_AT,
        )

    # Check 1: unknown parent is NOT_FOUND.
    bad1 = copy.deepcopy(payload)
    bad1["parent_artifact_ref"] = {
        "artifact_id": "ART-" + "0" * 32,
        "artifact_type": "document_manifest",
        "sha256": "sha256:" + "0" * 64,
    }
    refused1 = attempt(bad1)
    assert refused1.accepted is False
    assert (refused1.failing_step, refused1.code) == (1, "NOT_FOUND")

    # Check 2: stale parent hash is PARENT_HASH_MISMATCH.
    bad2 = copy.deepcopy(payload)
    bad2["parent_artifact_ref"]["sha256"] = "sha256:" + "f" * 64
    refused2 = attempt(bad2)
    assert (refused2.failing_step, refused2.code) == (2, "PARENT_HASH_MISMATCH")

    # Check 3: foreign workspace is WORKSPACE_NAMESPACE_MISMATCH.
    bad3 = copy.deepcopy(payload)
    bad3["workspace_id"] = "WSP-" + "9" * 32
    refused3 = attempt(bad3)
    assert (refused3.failing_step, refused3.code) == (3, "WORKSPACE_NAMESPACE_MISMATCH")

    # Check 4: ineligible document is VALIDATION_ERROR (adapter share).
    bad4 = copy.deepcopy(payload)
    bad4["documents"][0]["document_id"] = "DOC-" + "9" * 32
    refused4 = attempt(bad4)
    assert (refused4.failing_step, refused4.code) == (4, "VALIDATION_ERROR")

    # Check 5: tampered digest is VALIDATION_ERROR (no repair).
    bad5 = copy.deepcopy(payload)
    bad5["index_fingerprint"] = "sha256:" + "0" * 64
    refused5 = attempt(bad5)
    assert (refused5.failing_step, refused5.code) == (5, "VALIDATION_ERROR")

    # Check 5 collision limb: a listed id that cannot re-derive, with fresh
    # digests so the fingerprint comparison passes and the 5.1 rule fires.
    bad5b = copy.deepcopy(payload)
    bad5b["visible_chunks"][0] = dict(bad5b["visible_chunks"][0])
    bad5b["visible_chunks"][0]["chunk_id"] = "CHK-" + "0" * 32
    for doc in bad5b["documents"]:
        doc["chunk_ids"] = [
            ("CHK-" + "0" * 32)
            if cid == payload["visible_chunks"][0]["chunk_id"]
            else cid
            for cid in doc["chunk_ids"]
        ]
    for key, digest in compute_fingerprints(bad5b).items():
        if "." in key:
            head, tail = key.split(".", 1)
            bad5b[head][tail] = digest
        else:
            bad5b[key] = digest
    refused5b = attempt(bad5b)
    assert (refused5b.failing_step, refused5b.code) == (5, "CHUNK_IDENTITY_COLLISION")

    # Check 5 non-collision limb: a rederive VALIDATION_ERROR stays
    # VALIDATION_ERROR (never blanket-mapped to COLLISION).
    import scholar_harness.index_acceptance as _adapter_module5c
    from scholar_rag.index_manifest import ManifestValidationError

    _orig_rederive = _adapter_module5c.rederive_chunk_identities

    def _boom(_payload: Any) -> Any:
        raise ManifestValidationError(
            "inert test configuration", field="chunker.configuration"
        )

    monkeypatch.setattr(_adapter_module5c, "rederive_chunk_identities", _boom)
    try:
        refused5c = attempt(copy.deepcopy(payload))
    finally:
        monkeypatch.setattr(
            _adapter_module5c, "rederive_chunk_identities", _orig_rederive
        )
    assert (refused5c.failing_step, refused5c.code) == (5, "VALIDATION_ERROR")

    # Check 6: a dropped live chunk is BACKEND_STATE_INCONSISTENT.
    from scholar_rag.index_verifier import VisibleRow

    class _EmptyReader:
        def visible_ids(self) -> list[str]:
            return []

        def visible_count(self) -> int:
            return 0

        def visible_rows(self) -> list[Any]:
            return []

        def read_collection_metadata(self) -> dict[str, Any]:
            return {"hnsw:space": built["manifest"].backend.hnsw_space}

    refused6 = attempt(copy.deepcopy(payload), reader_override=_EmptyReader())
    assert (refused6.failing_step, refused6.code) == (6, "BACKEND_STATE_INCONSISTENT")

    # Every refusal published nothing: no record, no success event.
    assert not (workspace / ACCEPTED_RELPATH).exists()
    assert [
        e
        for e in _adapter_journal(workspace)
        if e["action"] == "RAG_INDEX_BUILT"
        and e["status"] == OperationStatus.SUCCESS.value
    ] == []


def test_adapter_backend_mismatch_refused_without_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AD-6 kit-query proof: the typed verification decides, nothing is written."""

    import scholar_harness.index_acceptance as adapter_module
    from scholar_harness.index_acceptance import (
        ACCEPTED_RELPATH,
        accept_index_candidate,
    )

    built = _adapter_candidate(tmp_path, monkeypatch)
    workspace = built["workspace"]
    before_registry = (workspace / "audit" / "artifact_registry.json").read_bytes()
    journal_before = _adapter_journal(workspace)

    calls: list[tuple[Any, Any]] = []
    real_verify = adapter_module.verify_backend

    def _spy(manifest: Any, view: Any) -> Any:
        calls.append((manifest, view))
        return real_verify(manifest, view)

    monkeypatch.setattr(adapter_module, "verify_backend", _spy)

    class _DroppedReader:
        def visible_ids(self) -> list[str]:
            return []

        def visible_count(self) -> int:
            return 0

        def visible_rows(self) -> list[Any]:
            return []

        def read_collection_metadata(self) -> dict[str, Any]:
            return {"hnsw:space": built["manifest"].backend.hnsw_space}

    refused = accept_index_candidate(
        workspace,
        copy.deepcopy(built["payload"]),
        run_id=_ADAPTER_RUN_ID,
        manifest_path=_ADAPTER_MANIFEST_RELPATH,
        reader=_DroppedReader(),
        accepted_at=_ADAPTER_ACCEPTED_AT,
    )

    assert refused.accepted is False
    assert refused.failing_step == 6
    assert refused.code == "BACKEND_STATE_INCONSISTENT"
    # The kit's typed query was the decider, exactly once.
    assert len(calls) == 1
    # Nothing was published: no record, no new journal line, no registry write.
    assert not (workspace / ACCEPTED_RELPATH).exists()
    assert _adapter_journal(workspace) == journal_before
    assert (
        workspace / "audit" / "artifact_registry.json"
    ).read_bytes() == before_registry


def test_adapter_atomic_commit_failure_preserves_state_and_intent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AD-ATOMIC: a journal failure rolls the record back and keeps the intent."""

    from scholar_harness.index_acceptance import (
        ACCEPTED_RELPATH,
        accept_index_candidate,
    )

    built = _adapter_candidate(tmp_path, monkeypatch)
    workspace = built["workspace"]
    # First acceptance establishes the last known complete index.
    first = accept_index_candidate(
        workspace,
        built["payload"],
        run_id=_ADAPTER_RUN_ID,
        manifest_path=_ADAPTER_MANIFEST_RELPATH,
        reader=built["reader"],
        accepted_at=_ADAPTER_ACCEPTED_AT,
    )
    assert first.accepted is True
    before_bytes = (workspace / ACCEPTED_RELPATH).read_bytes()
    journal_before = _adapter_journal(workspace)
    # A staged intent for the superseding run must survive the failed commit.
    intent_rel = "rag/index/RUN-b2/commit-intent.json"
    intent_path = workspace / intent_rel
    intent_path.parent.mkdir(parents=True, exist_ok=True)
    intent_path.write_text(json.dumps({"run_id": "RUN-b2"}), encoding="utf-8")

    def _failing_journal(*_: Any, **__: Any) -> Any:
        raise OSError("simulated unwritable ledger")

    # A superseding candidate (different chunker config, hence a different
    # manifest_id) reaches check 7 and then fails the atomic commit. Changing
    # the extracted text would break the parent's extracted_content_sha256
    # binding (kit-owned C-11), so the config -- which the parent never binds
    # -- is the hermetic way to force a new identity that still passes 1-6.
    from scholar_harness.orchestrator import ResearchOrchestrator
    from scholar_rag.index_service import IndexServiceRequest, _build_candidate_manifest
    from scholar_rag.index_verifier import VisibleRow

    orch = ResearchOrchestrator(workspace)
    parent_view = orch._build_parent_view()
    assert parent_view is not None
    base_request = orch._build_index_service_request(
        chroma_dir=tmp_path / "chroma-unused-2",
        parent_view=parent_view,
        run_id="RUN-" + "b2" * 16,
        created_at="2026-09-28T00:00:00Z",
        producer_commit=_ADAPTER_COMMIT,
        producer_version=_ADAPTER_VERSION,
    )
    altered_config = dict(base_request.chunker_configuration)
    altered_config["max_chunk_chars"] = 800
    request2 = IndexServiceRequest(
        **{
            **base_request.model_dump(mode="python"),
            "chunker_configuration": altered_config,
            "run_id": "RUN-" + "b2" * 16,
            "created_at": "2026-09-28T00:00:00Z",
        }
    )
    manifest2 = _build_candidate_manifest(
        request2, docs_path=workspace / "extracted", workspace_root=workspace
    )
    assert manifest2.manifest_id != built["manifest"].manifest_id
    rows2 = [
        VisibleRow(
            row_key=f"{request2.run_id}#{chunk.chunk_id}",
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            study_id=chunk.study_id,
            embedding_dimension=manifest2.embedder.dimension,
            stored_text=None,
        )
        for chunk in manifest2.visible_chunks
    ]

    class _Reader2:
        def __init__(self, rows: Any, space: str) -> None:
            self._rows = rows
            self._space = space

        def visible_ids(self) -> list[str]:
            return sorted(r.chunk_id for r in self._rows)

        def visible_count(self) -> int:
            return len(self._rows)

        def visible_rows(self) -> list[Any]:
            return list(self._rows)

        def read_collection_metadata(self) -> dict[str, Any]:
            return {"hnsw:space": self._space}

    refused = accept_index_candidate(
        workspace,
        manifest2.canonical_payload(),
        run_id=request2.run_id,
        manifest_path="rag/index/RUN-b2/manifest.json",
        reader=_Reader2(rows2, manifest2.backend.hnsw_space),
        intent_path=intent_rel,
        journal_append=_failing_journal,
        accepted_at="2026-09-29T00:00:00Z",
    )

    assert refused.accepted is False
    assert (refused.failing_step, refused.code) == (7, "ATOMIC_COMMIT_FAILED")
    # Old accepted state byte-identical, no new event, intent retained.
    assert (workspace / ACCEPTED_RELPATH).read_bytes() == before_bytes
    assert _adapter_journal(workspace) == journal_before
    assert intent_path.is_file()


def test_adapter_replay_is_noop_and_conflict_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AD-IDEMPOTENT: same fingerprint replays silently, same id diverges loudly."""

    import copy

    from scholar_harness.index_acceptance import (
        ACCEPTED_RELPATH,
        accept_index_candidate,
    )

    built = _adapter_candidate(tmp_path, monkeypatch)
    workspace = built["workspace"]
    first = accept_index_candidate(
        workspace,
        built["payload"],
        run_id=_ADAPTER_RUN_ID,
        manifest_path=_ADAPTER_MANIFEST_RELPATH,
        reader=built["reader"],
        accepted_at=_ADAPTER_ACCEPTED_AT,
    )
    assert first.accepted is True
    before_bytes = (workspace / ACCEPTED_RELPATH).read_bytes()
    journal_before = _adapter_journal(workspace)

    # Reuse still verifies the live backend; an unreadable backend refuses
    # without changing the historical record or emitting a success event.
    class _FailingReader:
        def visible_ids(self) -> Any:
            raise AssertionError("backend must not be touched on a no-op replay")

        def visible_count(self) -> Any:
            raise AssertionError("backend must not be touched on a no-op replay")

        def visible_rows(self) -> Any:
            raise AssertionError("backend must not be touched on a no-op replay")

        def read_collection_metadata(self) -> Any:
            raise AssertionError("backend must not be touched on a no-op replay")

    refused = accept_index_candidate(
        workspace,
        copy.deepcopy(built["payload"]),
        run_id="RUN-" + "f" * 32,
        manifest_path=_ADAPTER_MANIFEST_RELPATH,
        reader=_FailingReader(),
    )
    assert refused.accepted is False
    assert (workspace / ACCEPTED_RELPATH).read_bytes() == before_bytes
    assert _adapter_journal(workspace) == journal_before

    replayed = accept_index_candidate(
        workspace,
        copy.deepcopy(built["payload"]),
        run_id="RUN-" + "f" * 32,
        manifest_path=_ADAPTER_MANIFEST_RELPATH,
        reader=built["reader"],
        accepted_at="2026-10-01T00:00:00Z",
    )
    assert replayed.accepted is True
    assert replayed.reused is True
    assert (workspace / ACCEPTED_RELPATH).read_bytes() == before_bytes
    assert _adapter_journal(workspace) == journal_before

    # A different payload under the same manifest_id is never an overwrite.
    conflicted_payload = copy.deepcopy(built["payload"])
    conflicted_payload["index_fingerprint"] = "sha256:" + "1" * 64
    conflicted = accept_index_candidate(
        workspace,
        conflicted_payload,
        run_id="RUN-" + "e" * 32,
        manifest_path=_ADAPTER_MANIFEST_RELPATH,
        reader=built["reader"],
        accepted_at="2026-10-02T00:00:00Z",
    )
    assert conflicted.accepted is False
    assert (conflicted.failing_step, conflicted.code) == (7, "IDEMPOTENCY_CONFLICT")
    assert (workspace / ACCEPTED_RELPATH).read_bytes() == before_bytes
    assert _adapter_journal(workspace) == journal_before


def test_adapter_partial_is_recorded_never_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PARTIAL candidates are accepted as PARTIAL, never reported complete."""

    import copy

    from scholar_harness.index_acceptance import (
        ACCEPTED_RELPATH,
        accept_index_candidate,
    )
    from scholar_rag.index_manifest import IndexManifest, compute_fingerprints

    built = _adapter_candidate(tmp_path, monkeypatch, study_count=2)
    workspace = built["workspace"]
    manifest = built["manifest"]
    assert len(manifest.documents) == 2
    payload = copy.deepcopy(built["payload"])
    # Demote the second document to a rejected one, then re-seal the sidecar so
    # check 5 sees a genuinely valid PARTIAL candidate.
    demoted = payload["documents"].pop(1)
    payload["rejected_documents"].append(
        {
            "code": "EXTRACTED_TEXT_UNUSABLE",
            "detail": "demoted for the adapter PARTIAL proof",
            "document_id": demoted["document_id"],
            "extracted_path": demoted["extracted_path"],
            "study_id": demoted["study_id"],
        }
    )
    payload["visible_chunks"] = [
        chunk
        for chunk in payload["visible_chunks"]
        if chunk["document_id"] != demoted["document_id"]
    ]
    payload["counts"] = {
        "accepted_documents": len(payload["documents"]),
        "rejected_documents": len(payload["rejected_documents"]),
        "visible_chunks": len(payload["visible_chunks"]),
    }
    payload["status"] = "PARTIAL"
    for key, digest in compute_fingerprints(payload).items():
        if "." in key:
            head, tail = key.split(".", 1)
            payload[head][tail] = digest
        else:
            payload[key] = digest
    partial = IndexManifest.from_payload(payload)
    assert partial.status == "PARTIAL"
    # The fake reader holds exactly the demoted visible set.
    from scholar_rag.index_verifier import VisibleRow

    rows = [
        VisibleRow(
            row_key=f"{_ADAPTER_RUN_ID}#{chunk.chunk_id}",
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            study_id=chunk.study_id,
            embedding_dimension=partial.embedder.dimension,
            stored_text=None,
        )
        for chunk in partial.visible_chunks
    ]

    class _PartialReader:
        def __init__(self, rows: Any, space: str) -> None:
            self._rows = rows
            self._space = space

        def visible_ids(self) -> list[str]:
            return sorted(r.chunk_id for r in self._rows)

        def visible_count(self) -> int:
            return len(self._rows)

        def visible_rows(self) -> list[Any]:
            return list(self._rows)

        def read_collection_metadata(self) -> dict[str, Any]:
            return {"hnsw:space": self._space}

    result = accept_index_candidate(
        workspace,
        partial.canonical_payload(),
        run_id=_ADAPTER_RUN_ID,
        manifest_path=_ADAPTER_MANIFEST_RELPATH,
        reader=_PartialReader(rows, partial.backend.hnsw_space),
        accepted_at=_ADAPTER_ACCEPTED_AT,
    )
    assert result.accepted is True
    assert result.status == "PARTIAL"
    assert result.complete is False
    record = json.loads((workspace / ACCEPTED_RELPATH).read_text(encoding="utf-8"))
    assert record["status"] == "PARTIAL"
    event = _adapter_journal(workspace)[-1]
    assert event["action"] == "RAG_INDEX_BUILT"
    assert event["status"] == "PARTIAL"
    assert event["status"] != OperationStatus.SUCCESS.value


def test_adapter_record_write_failure_is_atomic_commit_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R1-F1a: a record-write OSError is step-7 ATOMIC_COMMIT_FAILED, old bytes intact."""

    import scholar_harness.index_acceptance as adapter_module
    from scholar_harness.index_acceptance import (
        ACCEPTED_RELPATH,
        accept_index_candidate,
    )

    built = _adapter_candidate(tmp_path, monkeypatch)
    workspace = built["workspace"]
    first = accept_index_candidate(
        workspace,
        built["payload"],
        run_id=_ADAPTER_RUN_ID,
        manifest_path=_ADAPTER_MANIFEST_RELPATH,
        reader=built["reader"],
        accepted_at=_ADAPTER_ACCEPTED_AT,
    )
    assert first.accepted is True
    before_bytes = (workspace / ACCEPTED_RELPATH).read_bytes()
    journal_before = _adapter_journal(workspace)
    intent_rel = "rag/index/RUN-b2/commit-intent.json"
    intent_path = workspace / intent_rel
    intent_path.parent.mkdir(parents=True, exist_ok=True)
    intent_path.write_text(json.dumps({"run_id": "RUN-b2"}), encoding="utf-8")

    real_atomic = adapter_module._atomic_write
    calls = {"count": 0}

    def _fail_once(path: Any, content: bytes) -> None:
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("simulated unwritable record")
        return real_atomic(path, content)

    monkeypatch.setattr(adapter_module, "_atomic_write", _fail_once)

    from scholar_harness.orchestrator import ResearchOrchestrator
    from scholar_rag.index_service import IndexServiceRequest, _build_candidate_manifest
    from scholar_rag.index_verifier import VisibleRow

    orch = ResearchOrchestrator(workspace)
    parent_view = orch._build_parent_view()
    assert parent_view is not None
    base_request = orch._build_index_service_request(
        chroma_dir=tmp_path / "chroma-unused-2",
        parent_view=parent_view,
        run_id="RUN-" + "b2" * 16,
        created_at="2026-09-28T00:00:00Z",
        producer_commit=_ADAPTER_COMMIT,
        producer_version=_ADAPTER_VERSION,
    )
    altered_config = dict(base_request.chunker_configuration)
    altered_config["max_chunk_chars"] = 800
    request2 = IndexServiceRequest(
        **{
            **base_request.model_dump(mode="python"),
            "chunker_configuration": altered_config,
            "run_id": "RUN-" + "b2" * 16,
            "created_at": "2026-09-28T00:00:00Z",
        }
    )
    manifest2 = _build_candidate_manifest(
        request2, docs_path=workspace / "extracted", workspace_root=workspace
    )
    assert manifest2.manifest_id != built["manifest"].manifest_id
    rows2 = [
        VisibleRow(
            row_key=f"{request2.run_id}#{chunk.chunk_id}",
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            study_id=chunk.study_id,
            embedding_dimension=manifest2.embedder.dimension,
            stored_text=None,
        )
        for chunk in manifest2.visible_chunks
    ]

    class _Reader2:
        def __init__(self, rows: Any, space: str) -> None:
            self._rows = rows
            self._space = space

        def visible_ids(self) -> list[str]:
            return sorted(r.chunk_id for r in self._rows)

        def visible_count(self) -> int:
            return len(self._rows)

        def visible_rows(self) -> list[Any]:
            return list(self._rows)

        def read_collection_metadata(self) -> dict[str, Any]:
            return {"hnsw:space": self._space}

    refused = accept_index_candidate(
        workspace,
        manifest2.canonical_payload(),
        run_id=request2.run_id,
        manifest_path="rag/index/RUN-b2/manifest.json",
        reader=_Reader2(rows2, manifest2.backend.hnsw_space),
        intent_path=intent_rel,
        accepted_at="2026-09-29T00:00:00Z",
    )

    assert refused.accepted is False
    assert (refused.failing_step, refused.code) == (7, "ATOMIC_COMMIT_FAILED")
    assert (workspace / ACCEPTED_RELPATH).read_bytes() == before_bytes
    assert _adapter_journal(workspace) == journal_before
    assert intent_path.is_file()


def test_adapter_refusal_coverage_steps_1_3_6_and_backend_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R1-F3: one code per step for the uncovered limbs; steps 1-5 never read."""

    import copy

    import scholar_harness.index_acceptance as adapter_module
    from scholar_harness.index_acceptance import (
        ACCEPTED_RELPATH,
        accept_index_candidate,
    )

    built = _adapter_candidate(tmp_path, monkeypatch)
    workspace = built["workspace"]
    payload = built["payload"]
    reader = built["reader"]

    calls: list[tuple[Any, Any]] = []
    real_verify = adapter_module.verify_backend

    def _spy(manifest: Any, view: Any) -> Any:
        calls.append((manifest, view))
        return real_verify(manifest, view)

    monkeypatch.setattr(adapter_module, "verify_backend", _spy)

    def attempt(mutated: dict[str, Any], *, reader_override: Any = None) -> Any:
        return accept_index_candidate(
            workspace,
            mutated,
            run_id=_ADAPTER_RUN_ID,
            manifest_path=_ADAPTER_MANIFEST_RELPATH,
            reader=(reader_override if reader_override is not None else reader),
            accepted_at=_ADAPTER_ACCEPTED_AT,
        )

    # Step 1 UNSUPPORTED_ARTIFACT_TYPE: registry entry is a known non-Contract type.
    registry_path = workspace / "audit" / "artifact_registry.json"
    registry_raw = json.loads(registry_path.read_text(encoding="utf-8"))
    parent_id = str(payload["parent_artifact_ref"]["artifact_id"])
    orig_type = registry_raw["artifacts"][parent_id]["artifact_type"]
    registry_raw["artifacts"][parent_id]["artifact_type"] = "index_manifest"
    registry_path.write_text(json.dumps(registry_raw, indent=2), encoding="utf-8")
    try:
        refused_unsupported = attempt(copy.deepcopy(payload))
    finally:
        registry_raw["artifacts"][parent_id]["artifact_type"] = orig_type
        registry_path.write_text(json.dumps(registry_raw, indent=2), encoding="utf-8")
    assert (refused_unsupported.failing_step, refused_unsupported.code) == (
        1,
        "UNSUPPORTED_ARTIFACT_TYPE",
    )

    # Step 1 VALIDATION_ERROR: no parent reference at all.
    bad1v = copy.deepcopy(payload)
    del bad1v["parent_artifact_ref"]
    refused1v = attempt(bad1v)
    assert (refused1v.failing_step, refused1v.code) == (1, "VALIDATION_ERROR")

    # Step 3 REQUIRED_PARENT_TYPE_MISSING: declared type is a known non-required one.
    bad3r = copy.deepcopy(payload)
    bad3r["parent_artifact_ref"] = dict(bad3r["parent_artifact_ref"])
    bad3r["parent_artifact_ref"]["artifact_type"] = "corpus_snapshot"
    refused3r = attempt(bad3r)
    assert (refused3r.failing_step, refused3r.code) == (
        3,
        "REQUIRED_PARENT_TYPE_MISSING",
    )

    # Step 3 PROTOCOL_FINGERPRINT_MISMATCH.
    bad3p = copy.deepcopy(payload)
    bad3p["protocol_fingerprint"] = "sha256:" + "1" * 64
    refused3p = attempt(bad3p)
    assert (refused3p.failing_step, refused3p.code) == (
        3,
        "PROTOCOL_FINGERPRINT_MISMATCH",
    )

    # Step 3 CORPUS_FINGERPRINT_MISMATCH.
    bad3c = copy.deepcopy(payload)
    bad3c["corpus_fingerprint"] = "sha256:" + "2" * 64
    refused3c = attempt(bad3c)
    assert (refused3c.failing_step, refused3c.code) == (
        3,
        "CORPUS_FINGERPRINT_MISMATCH",
    )

    # Steps 1-5 never touched the backend.
    assert calls == []

    # Step 6 EMBEDDING_IDENTITY_CHANGED: same ids, one row with a wrong dimension.
    from scholar_rag.index_verifier import VisibleRow

    manifest = built["manifest"]
    dim_rows = [
        VisibleRow(
            row_key=row.row_key,
            chunk_id=row.chunk_id,
            document_id=row.document_id,
            study_id=row.study_id,
            embedding_dimension=int(manifest.embedder.dimension) + 1,
            stored_text=None,
        )
        for row in built["rows"]
    ]

    class _DimReader:
        def __init__(self, rows: Any, space: str) -> None:
            self._rows = list(rows)
            self._space = space

        def visible_ids(self) -> list[str]:
            return sorted(r.chunk_id for r in self._rows)

        def visible_count(self) -> int:
            return len(self._rows)

        def visible_rows(self) -> list[Any]:
            return list(self._rows)

        def read_collection_metadata(self) -> dict[str, Any]:
            return {"hnsw:space": self._space}

    refused6e = attempt(
        copy.deepcopy(payload),
        reader_override=_DimReader(dim_rows, manifest.backend.hnsw_space),
    )
    assert (refused6e.failing_step, refused6e.code) == (
        6,
        "EMBEDDING_IDENTITY_CHANGED",
    )

    # Step 6 CONFIGURATION_INEFFECTIVE: the store records no distance space.
    class _NoSpaceReader:
        def __init__(self, rows: Any) -> None:
            self._rows = list(rows)

        def visible_ids(self) -> list[str]:
            return sorted(r.chunk_id for r in self._rows)

        def visible_count(self) -> int:
            return len(self._rows)

        def visible_rows(self) -> list[Any]:
            return list(self._rows)

        def read_collection_metadata(self) -> dict[str, Any]:
            return {}

    refused6c = attempt(
        copy.deepcopy(payload), reader_override=_NoSpaceReader(built["rows"])
    )
    assert (refused6c.failing_step, refused6c.code) == (
        6,
        "CONFIGURATION_INEFFECTIVE",
    )

    # The spy saw exactly the two step-6 reads, nothing for steps 1-5.
    assert len(calls) == 2
    # Nothing was published: no record, no success event.
    assert not (workspace / ACCEPTED_RELPATH).exists()
    assert [
        e
        for e in _adapter_journal(workspace)
        if e["action"] == "RAG_INDEX_BUILT"
        and e["status"] == OperationStatus.SUCCESS.value
    ] == []


def test_orchestrator_adapter_fault_fails_closed_without_legacy_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R1-F1b: an unexpected adapter raise is FAILED, never a legacy BUILT line."""

    from types import SimpleNamespace

    import scholar_harness.index_acceptance as adapter_module
    from scholar_harness.orchestrator import ResearchOrchestrator

    built = _adapter_candidate(tmp_path, monkeypatch)
    workspace = built["workspace"]
    payload = built["payload"]
    sidecar_rel = "rag/index/RUN-fault/manifest.json"
    sidecar_abs = workspace / sidecar_rel
    sidecar_abs.parent.mkdir(parents=True, exist_ok=True)
    sidecar_abs.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    journal_before = _adapter_journal(workspace)
    chroma_dir = tmp_path / "chroma-fault"

    stub = SimpleNamespace(
        outcome="SUCCESS",
        counts=SimpleNamespace(
            accepted_documents=1,
            rejected_documents=0,
            visible_chunks=len(payload["visible_chunks"]),
        ),
        rejected_documents=(),
        sidecar_path=sidecar_rel,
        live_set_matches=True,
        intent_path=None,
    )

    def _fake_index_workspace(request: Any, **kwargs: Any) -> Any:
        return stub

    monkeypatch.setattr(orch_module, "index_workspace", _fake_index_workspace)
    monkeypatch.setattr(
        orch_module, "ChromaReplacementView", lambda **_: SimpleNamespace()
    )
    monkeypatch.setattr(
        orch_module, "ChromaVisibleSetReader", lambda **_: SimpleNamespace()
    )

    def _boom(*_: Any, **__: Any) -> Any:
        raise RuntimeError("simulated adapter fault")

    monkeypatch.setattr(adapter_module, "accept_index_candidate", _boom)

    orch = ResearchOrchestrator(workspace)
    result, _indexer = orch._run_indexing_stage(chroma_dir)

    assert result["status"] == "FAILED"
    assert result["indexed_files"] == 0
    assert result["total_chunks"] == 0
    assert result["refused"] == [{"document_id": "", "code": "INTERNAL_ERROR"}]
    # No accepted record was written.
    assert not (workspace / "rag" / "index" / "accepted.json").exists()
    # No legacy BUILT line: the journal is byte-identical, so no absolute
    # chroma_dir output and no incomplete metrics were published.
    assert _adapter_journal(workspace) == journal_before
    assert [
        e for e in _adapter_journal(workspace) if e["action"] == "RAG_INDEX_BUILT"
    ] == [e for e in journal_before if e["action"] == "RAG_INDEX_BUILT"]
    blob = json.dumps(_adapter_journal(workspace), sort_keys=True)
    assert str(chroma_dir) not in blob
