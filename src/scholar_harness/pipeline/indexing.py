"""Indexing stage (HCM-04h neutral extraction).

Stage 6 of the research pipeline: typed vector and semantic indexing over
accepted documents with no invented identity. Extracted verbatim from
``ResearchOrchestrator._run_indexing_stage`` and its helpers so the
orchestrator delegates without behavior change.

Preservation notes:

- Registry readers (``load_artifact_registry`` / ``accepted_artifact_payload``
  / ``accepted_screening_parents`` / ``accepted_document_records``) are moved
  here verbatim; the orchestrator keeps thin delegating methods with identical
  signatures (HCM-04b pattern) so the E3 conformance, e2e acceptance, and
  registered-id suites that call ``orch._load_artifact_registry()`` /
  ``orch._accepted_*()`` / ``orch._build_parent_view()`` /
  ``orch._build_index_service_request(...exact kwargs...)`` /
  ``orch._run_indexing_stage(...)`` keep resolving from the orchestrator
  namespace with zero test edits.
- ``recorded_workspace_id`` is HCM-02-owned and stays in the orchestrator; it
  is a thin adapter over
  :func:`workspace.identity.require_recorded_identity` (identical messages,
  including the observed non-object ``AttributeError`` for a JSON-array
  manifest, HCM-01 defect (a), preserved). This stage calls
  ``require_recorded_identity(workspace_dir)`` directly -- the same function
  the orchestrator adapter calls -- so workspace-identity messages are
  byte-identical without importing the orchestrator.
- Parent view, request build (including the ``get_embedder`` dimension read
  and the hard-coded ``chromadb`` / ``sentence-transformers`` /
  ``all-MiniLM-L6-v2`` / ``384`` / ``cosine`` / chunker-config literals), and
  the full ``_run_indexing_stage`` body (identity-first, parent view, lazy
  ``validate_extraction_currentness`` from the same
  ``scholar_harness.extraction_producer`` module, three ``RAG_INDEX_REJECTED``
  paths, ``deterministic_id`` run identity with timestamp input, journal
  ``run-reports`` mkdir, embedder/backend/reader construction,
  ``index_workspace`` call, outcome mapping, documents populate via re-read
  screening parents, E3 adapter branch, legacy ``RAG_INDEX_BUILT`` audit, and
  the inline ``MinimalIndexer`` returns) are moved verbatim; only mechanical
  parameterization (``self.workspace_dir`` to ``workspace_dir``,
  ``self._method()`` to stage functions, kit globals to explicit collaborator
  args) is applied. No logic edits, no renames of codes/messages/filenames,
  no formatter churn.
- The stale-currentness ``RAG_INDEX_REJECTED`` audit call carries the base's
  latent ``parameters={"code": ...}`` keyword, which neither
  ``ResearchOrchestrator._log_audit_event`` nor
  ``workspace.audit.append_legacy_event`` accepts. Both raise ``TypeError``
  before any byte is written, with no publication. The stage preserves this
  exact call shape (and the resulting ``TypeError`` with no journal row)
  rather than repairing it: a repair would be a behavior change beyond this
  parity-only packet. See the focused test that proves the ``TypeError`` and
  the absence of journal bytes.
- Audit uses ``workspace.audit.append_legacy_event`` directly with the same
  arguments the orchestrator's thin ``_log_audit_event`` adapter passed
  through (same action, agent, description, inputs, outputs, metrics, and
  observed outcome status) so journal bytes are unchanged (same legacy
  ``hex(hash(...))`` event-id scheme, no uppercasing, no manifest/INDEX
  update). Chosen over a passed callable to keep the stage neutral (no
  orchestrator import) and to match the HCM-04d hydration precedent.
- Kit seams use small explicit DI (no lazy ``import orchestrator``, no
  ``__dict__`` snooping; the stage never imports the orchestrator). Kit
  defaults (``get_embedder``, ``ChromaReplacementView``,
  ``ChromaVisibleSetReader``, ``index_workspace``) live in this module; the
  orchestrator thin methods forward their own (possibly patched) globals as
  collaborator args. Tests that patch
  ``scholar_harness.orchestrator.ChromaReplacementView`` /
  ``ChromaVisibleSetReader`` / ``get_embedder`` / ``index_workspace`` keep
  working through that forwarding.
- ``ScholarIndexer`` is never constructed by Stage 6 (line evidence: the
  base ``_run_indexing_stage`` constructs only ``MinimalIndexer`` inline
  classes, ``ChromaReplacementView``, ``ChromaVisibleSetReader``, and the
  ``get_embedder`` result; ``grep ScholarIndexer`` in the orchestrator finds
  only the stub class definition). The legacy ``ScholarIndexer`` stub stays in
  the orchestrator solely as the historical patch point for tests that patch
  ``orch.ScholarIndexer``; those patches are vestigial (they never affect
  Stage 6) but removing the stub would break the patch sites, so it is kept.
- ``extraction_producer.index_accepted_documents`` (the CLI Stage-6 path)
  delegates to the orchestrator's Stage 6 and stays untouched; it benefits
  from the move through the orchestrator thin delegate with no change.

Neutrality: stdlib plus ``scholar-rag-kit`` only for the request/backend
shapes -- no console transport, no Contract v1 acceptance beyond calling the
frozen ``index_acceptance.accept_index_candidate`` adapter (called, not
touched), no workspace audit beyond the legacy ``RAG_INDEX_*`` rows this
stage owns.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scholar_rag.chunker import text_fingerprint
from scholar_rag.embedder import get_embedder
from scholar_rag.index_models import IndexDocumentRequest
from scholar_rag.index_service import (
    IndexedSource,
    IndexServiceRequest,
    index_workspace,
)
from scholar_rag.index_verifier import ChromaVisibleSetReader
from scholar_rag.replacement import ChromaReplacementView

from scholar_harness.contracts.acceptance import ArtifactRegistry, RegistryEntry
from scholar_harness.contracts.models import ArtifactReference, DocumentManifestArtifact
from scholar_harness.workspace.audit import append_legacy_event
from scholar_harness.workspace.identity import require_recorded_identity

logger = logging.getLogger(__name__)


def load_artifact_registry(workspace_dir: Path | str) -> ArtifactRegistry | None:
    """Parse the Contract v1 artifact registry through the frozen model.

    Verbatim move of ``ResearchOrchestrator._load_artifact_registry``: the
    registry is the recorded proof of what was accepted, so it is read with
    the frozen ``ArtifactRegistry`` / ``RegistryEntry`` models rather than
    hand-parsed. ``None`` means "nothing may be inherited from the
    registry": either no registry exists yet, or it does not validate.
    """
    ws = Path(workspace_dir)
    registry_path = ws / "audit" / "artifact_registry.json"
    if not registry_path.is_file():
        return None
    try:
        return ArtifactRegistry.model_validate_json(
            registry_path.read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as exc:
        logger.warning(
            "artifact registry %s is unusable (%s); refusing to inherit "
            "identity from it",
            registry_path,
            exc,
        )
        return None


def accepted_artifact_payload(
    workspace_dir: Path | str, entry: RegistryEntry
) -> Any | None:
    """Read one accepted artifact's payload, with typed path containment.

    Verbatim move of
    ``ResearchOrchestrator._accepted_artifact_payload``: ``RegistryEntry.path``
    is workspace-relative, validated with the frozen ``ArtifactReference``
    path rule and re-checked against the resolved workspace root. A registry
    that points outside the workspace is refused, not followed.
    """
    ws = Path(workspace_dir)
    try:
        ArtifactReference.portable_workspace_path(entry.path)
    except ValueError:
        logger.warning("registry entry %r has a non-portable path", entry.path)
        return None
    try:
        resolved = (ws / entry.path).resolve()
        resolved.relative_to(ws)
    except (OSError, ValueError):
        logger.warning("registry entry %r escapes the workspace", entry.path)
        return None
    try:
        return json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def accepted_screening_parents(
    workspace_dir: Path | str,
) -> dict[str, dict[str, str]]:
    """Map each included ``study_id`` to the accepted artifact that bound it.

    Verbatim move of ``ResearchOrchestrator._accepted_screening_parents``:
    read-only over the Contract v1 artifact registry. An included study's
    scientific parent is the accepted ``screening_decisions`` artifact
    carrying its INCLUDE decision; nothing is inferred.
    """
    registry = load_artifact_registry(workspace_dir)
    if registry is None:
        return {}

    parents: dict[str, dict[str, str]] = {}
    for artifact_id, entry in sorted(registry.artifacts.items()):
        if entry.artifact_type != "screening_decisions":
            continue
        payload = accepted_artifact_payload(workspace_dir, entry)
        if not isinstance(payload, dict):
            continue
        for decision in (payload.get("data") or {}).get("decisions") or []:
            if str(decision.get("decision") or "").upper() != "INCLUDE":
                continue
            study_id = str(decision.get("study_id") or "").strip()
            if not study_id:
                continue
            parents[study_id] = {
                "parent_artifact_id": artifact_id,
                "parent_artifact_sha256": entry.sha256,
                "decision_id": str(decision.get("decision_id") or ""),
            }
    return parents


def accepted_document_records(
    workspace_dir: Path | str,
) -> dict[str, dict[str, str]]:
    """Map each accepted ``document_id`` to its recorded identity and path.

    Verbatim move of ``ResearchOrchestrator._accepted_document_records``:
    both limbs come from a ``DocumentRecord`` inside an accepted
    ``document_manifest``. A document with no accepted manifest record is
    simply absent. Nothing derives a ``document_id`` from a filename, title,
    or DOI, and ``workspace_id`` is never offered as a study.
    """
    registry = load_artifact_registry(workspace_dir)
    if registry is None:
        return {}

    records: dict[str, dict[str, str]] = {}
    for artifact_id, entry in sorted(registry.artifacts.items()):
        if entry.artifact_type != "document_manifest":
            continue
        payload = accepted_artifact_payload(workspace_dir, entry)
        if payload is None:
            continue
        try:
            manifest = DocumentManifestArtifact.model_validate(payload)
        except ValueError as exc:
            logger.warning(
                "accepted document manifest %s is not a valid "
                "DocumentManifestArtifact: %s",
                artifact_id,
                exc,
            )
            continue
        for record in manifest.data.documents:
            records[record.document_id] = {
                "study_id": record.study_id,
                "extracted_path": record.extracted_path or "",
                "parent_artifact_id": artifact_id,
                "parent_artifact_sha256": entry.sha256,
            }
    return records


def build_parent_view(workspace_dir: Path | str) -> dict[str, Any] | None:
    """Build the accepted-parent view required by IndexService.

    Verbatim move of ``ResearchOrchestrator._build_parent_view``: the parent
    view is the accepted ``document_manifest`` artifact, read from the
    Contract v1 artifact registry, not derived. The workspace limb is the
    recorded identity (``require_recorded_identity`` -- the same function the
    orchestrator's ``recorded_workspace_id`` adapter calls, so messages are
    byte-identical).
    """
    ws = Path(workspace_dir)
    registry = load_artifact_registry(ws)
    if registry is None:
        return None

    # Find the accepted document_manifest in this generation
    manifests = {}
    for artifact_id, entry in registry.artifacts.items():
        if entry.artifact_type != "document_manifest":
            continue
        payload = accepted_artifact_payload(ws, entry)
        if payload is None:
            continue
        try:
            manifest = DocumentManifestArtifact.model_validate(payload)
        except ValueError:
            continue
        # Check generation match via workspace_id, protocol_fingerprint, corpus_fingerprint
        ws_id = require_recorded_identity(ws)
        if manifest.workspace_id != ws_id:
            continue
        # Protocol and corpus fingerprint should match the current generation
        # (they come from the accepted corpus snapshot)
        manifests[artifact_id] = manifest

    if not manifests:
        return None

    # Use the newest accepted manifest (by artifact_id ordering)
    manifest_id, manifest = sorted(manifests.items())[-1]
    entry = registry.artifacts[manifest_id]

    # Build parent_view.documents from the manifest's document records
    # Compute extracted_content_sha256 from the actual extracted file
    documents = []
    for record in manifest.data.documents:
        extracted = record.extracted_path
        md_path = (ws / extracted) if extracted else None
        extracted_content_sha256 = ""
        if md_path is not None and md_path.is_file():
            text = md_path.read_text(encoding="utf-8")
            extracted_content_sha256 = text_fingerprint(text)
        documents.append(
            {
                "document_id": record.document_id,
                "study_id": record.study_id,
                "extracted_path": record.extracted_path,
                "extracted_content_sha256": extracted_content_sha256,
            }
        )

    return {
        "artifact_id": manifest_id,
        "artifact_type": "document_manifest",
        "sha256": entry.sha256,
        "workspace_id": manifest.workspace_id,
        "protocol_fingerprint": manifest.protocol_fingerprint,
        "corpus_fingerprint": manifest.corpus_fingerprint,
        "documents": documents,
    }


def build_index_service_request(
    *,
    workspace_dir: Path | str,
    chroma_dir: Path,
    parent_view: dict[str, Any],
    run_id: str,
    created_at: str,
    producer_commit: str,
    producer_version: str,
    get_embedder_fn: Any = get_embedder,
    documents: dict[str, dict[str, str]] | None = None,
    screening_parents: dict[str, dict[str, str]] | None = None,
) -> IndexServiceRequest | None:
    """Construct the IndexServiceRequest from recorded workspace state.

    Verbatim move of ``ResearchOrchestrator._build_index_service_request``:
    every field is explicit; nothing is inferred or defaulted. The
    ``chroma_dir`` parameter is retained for signature parity (the base never
    reads it here). The embedder dimension is read from
    ``get_embedder(provider="sentence-transformers")`` (here
    ``get_embedder_fn`` -- the orchestrator forwards its own global so a
    patched ``orchestrator.get_embedder`` takes effect). Hard-coded literals
    (``chromadb`` / ``scholar_docs`` / chunker config / ``cosine`` /
    ``sentence-transformers`` / ``all-MiniLM-L6-v2`` / journal/docs paths)
    are unchanged.

    Explicit data DI: ``documents`` / ``screening_parents`` default to
    ``None`` meaning "read from the workspace" (the base behavior). The
    orchestrator thin delegate forwards its own (possibly patched)
    ``_accepted_document_records()`` / ``_accepted_screening_parents()``
    results here so live monkeypatch seams (E3-NEG-013 etc., which patch
    ``ResearchOrchestrator._accepted_document_records`` to simulate empty
    runs) keep working with zero test edits. Direct stage calls omit them
    and read from disk identically.
    """
    ws = Path(workspace_dir)
    workspace_id = require_recorded_identity(ws)
    docs_path = ws / "extracted"

    # Gather accepted document records (explicit DI or workspace read).
    if documents is None:
        documents = accepted_document_records(ws)
    if screening_parents is None:
        parents = accepted_screening_parents(ws)
    else:
        parents = screening_parents

    sources: list[IndexedSource] = []
    for document_id, record in sorted(documents.items()):
        study_id = record["study_id"].strip()
        if not study_id:
            continue
        extracted = record["extracted_path"]
        md_path = (ws / extracted) if extracted else None
        if md_path is None or not md_path.is_file():
            continue
        parent = parents.get(study_id)
        if parent is None:
            continue

        text = md_path.read_text(encoding="utf-8")
        # The parent_artifact_id and parent_artifact_sha256 in the IndexDocumentRequest
        # must match the parent_view (the accepted document_manifest), not the
        # screening decision. The IndexService validates this match.
        request = IndexDocumentRequest(
            workspace_id=workspace_id,
            study_id=study_id,
            document_id=document_id,
            parent_artifact_id=parent_view["artifact_id"],
            parent_artifact_sha256=parent_view["sha256"],
            extracted_content_sha256=text_fingerprint(text),
            backend_provider="chromadb",
            backend_model=None,
            collection="scholar_docs",
        )
        sources.append(
            IndexedSource(
                request=request,
                extracted_text=text,
                extracted_path=extracted,
                extraction_method="markdown",
            )
        )

    # The closed kit request requires at least one source. Return the
    # empty-run sentinel before constructing it or opening an embedder.
    if not sources:
        return None

    # Read embedder configuration from the indexer we'll use
    # We use the mock embedder for hermetic tests; real runs use sentence-transformers
    embedder = get_embedder_fn(provider="sentence-transformers")
    embedder_dim = getattr(embedder, "dimension", 384)

    return IndexServiceRequest(
        run_id=run_id,
        created_at=created_at,
        sources=tuple(sources),
        parent_view=parent_view,
        accepted_manifest=None,  # Not used for initial indexing
        chunker_configuration={
            "heading_levels": [1, 2, 3],
            "max_chunk_chars": 1200,
            "min_chunk_chars": 100,
            "overlap_chars": 150,
            "normalize_whitespace": True,
            "sentence_split_pattern": r"(?<=[.!?])\s+",
            "strip_frontmatter": True,
        },
        backend_type="chromadb",
        collection_name="scholar_docs",
        storage_schema_version="1.0.0",
        hnsw_space="cosine",
        embedder_provider="sentence-transformers",
        embedder_model="all-MiniLM-L6-v2",
        embedder_model_revision=None,
        embedder_dimension=embedder_dim,
        embedder_normalize_embeddings=True,
        embedder_distance_metric="cosine",
        producer_version=producer_version,
        producer_commit=producer_commit,
        journal_path="run-reports/rag-index.jsonl",
        docs_path="extracted",
        recovery_probe_run_id=None,
    )


@dataclass
class IndexingOutcome:
    """Typed outcome of the indexing stage.

    ``result`` is the stage result dict the orchestrator maps to
    ``results["stages"]["indexing"]`` (``status`` / ``indexed_files`` /
    ``total_chunks`` / ``collection_count`` / ``documents`` / ``refused`` plus
    optional ``acceptance`` / ``code``). ``indexer`` is the minimal
    indexer-like object Stage 7 binds its retriever to (``collection_name`` /
    ``embedder_kwargs`` / ``get_collection_count``). The outcome carries both
    so ``run_pipeline_async`` keeps its ``index_res, indexer`` binding.
    """

    result: dict[str, Any] = field(default_factory=dict)
    indexer: Any = None


_UNSET: Any = object()


def run_indexing(
    *,
    workspace_dir: Path | str,
    chroma_dir: Path | str,
    get_embedder_fn: Any = get_embedder,
    backend_cls: Any = ChromaReplacementView,
    reader_cls: Any = ChromaVisibleSetReader,
    index_workspace_fn: Any = index_workspace,
    parent_view: Any = _UNSET,
    documents: dict[str, dict[str, str]] | None = None,
    screening_parents: dict[str, dict[str, str]] | None = None,
) -> IndexingOutcome:
    """Index accepted documents via the typed E3 IndexService.

    Verbatim move of ``ResearchOrchestrator._run_indexing_stage``: the typed
    E3 ``IndexService.index_workspace`` path with its seven acceptance
    checks, fail-closed. Only mechanical parameterization: ``workspace_dir``
    / ``chroma_dir`` inputs plus explicit kit collaborators (whose defaults
    live in this module; the orchestrator forwards its own patched globals).

    Explicit data DI: ``parent_view`` defaults to the ``_UNSET`` sentinel
    meaning "build from the workspace" (the base behavior); an explicit
    ``None`` or dict is used as-is. ``documents`` / ``screening_parents``
    default to ``None`` meaning "read from the workspace"; an explicit dict
    (including ``{}``) is used as-is. The orchestrator thin delegate forwards
    its own (possibly patched) ``_build_parent_view()`` /
    ``_accepted_document_records()`` / ``_accepted_screening_parents()``
    results here so live monkeypatch seams (E3-NEG-013 etc., which patch
    ``ResearchOrchestrator._accepted_document_records`` to simulate empty
    runs) keep working with zero test edits. Direct stage calls omit them
    and read from disk identically.

    The lazy ``validate_extraction_currentness`` import stays lazy from the
    same ``scholar_harness.extraction_producer`` module; ``deterministic_id``
    / ``IdentifierKind`` stay lazy from the same contracts modules; the E3
    ``accept_index_candidate`` import stays lazy from the same
    ``scholar_harness.index_acceptance`` module. Audit rows go directly to
    ``append_legacy_event`` with the same bytes the orchestrator adapter
    passed through. ``MinimalIndexer`` inline definitions are moved verbatim.
    """
    ws = Path(workspace_dir)
    chroma_path = Path(chroma_dir)

    # Validate workspace identity BEFORE any store exists
    workspace_id = require_recorded_identity(ws)

    # Build parent_view from accepted document_manifest (or use the override).
    if parent_view is _UNSET:
        parent_view = build_parent_view(ws)
    if parent_view is not None:
        from scholar_harness.extraction_producer import (
            PublicationRefused,
            validate_extraction_currentness,
        )

        try:
            validate_extraction_currentness(ws, parent_view["artifact_id"])
        except PublicationRefused as exc:
            # PRESERVED LATENT DEFECT (parity-only, not repaired): the base
            # passes ``parameters={"code": ...}`` to an audit writer that
            # accepts no such keyword, so both the base
            # (``_log_audit_event``) and this stage (``append_legacy_event``)
            # raise ``TypeError`` before any byte is written, with no
            # publication. The call shape is kept verbatim.
            append_legacy_event(
                ws,
                action="RAG_INDEX_REJECTED",
                agent="scholar-harness",
                description="Stage 6 refused stale extraction provenance",
                inputs=[str(parent_view["artifact_id"])],
                outputs=[],
                metrics={"documents": 0},
                status="FAILED",
                parameters={"code": exc.code},  # type: ignore[call-arg]
            )
            return IndexingOutcome(
                result={"status": "FAILED", "code": exc.code, "documents": 0},
                indexer=None,
            )
    if parent_view is None:
        # No accepted manifest -> refuse before touching any backend
        append_legacy_event(
            ws,
            action="RAG_INDEX_REJECTED",
            agent="scholar-harness",
            description="Stage 6 refused: no accepted document_manifest in this generation",
            inputs=[str(ws / "audit" / "artifact_registry.json")],
            outputs=[],
            metrics={
                "indexed_files": 0,
                "total_chunks": 0,
                "refused_documents": 0,
                "rejection_code": "DOCUMENT_MANIFEST_NOT_ACCEPTED",
            },
            status="FAILED",
        )

        # Return a minimal indexer for Stage 7 compatibility even on refusal
        class MinimalIndexer:
            collection_name = "scholar_docs"
            embedder_kwargs = {
                "provider": "sentence-transformers",
                "model_name": "all-MiniLM-L6-v2",
            }

            def get_collection_count(self) -> int:
                return 0

        return IndexingOutcome(
            result={
                "status": "FAILED",
                "indexed_files": 0,
                "total_chunks": 0,
                "collection_count": None,
                "documents": [],
                "refused": [
                    {"document_id": "", "reason": "no accepted document_manifest"}
                ],
            },
            indexer=MinimalIndexer(),
        )

    # Generate run identity
    from scholar_harness.contracts.canonical import deterministic_id
    from scholar_harness.contracts.identifiers import IdentifierKind

    run_id = deterministic_id(
        IdentifierKind.RUN,
        workspace_id,
        {"stage": "indexing", "timestamp": datetime.now(UTC).isoformat()},
    )
    created_at = datetime.now(UTC).isoformat()
    producer_commit = "0" * 40  # Would come from harness commit in real usage
    producer_version = "1.0.0"

    # Build the IndexServiceRequest (forward data overrides so patched
    # orchestrator readers take effect; None means "read from workspace").
    request = build_index_service_request(
        workspace_dir=ws,
        chroma_dir=chroma_path,
        parent_view=parent_view,
        run_id=run_id,
        created_at=created_at,
        producer_commit=producer_commit,
        producer_version=producer_version,
        get_embedder_fn=get_embedder_fn,
        documents=documents,
        screening_parents=screening_parents,
    )

    # Early refusal: no documents to index (all skipped during request building)
    if request is None:
        append_legacy_event(
            ws,
            action="RAG_INDEX_REJECTED",
            agent="scholar-harness",
            description="Stage 6 refused: no accepted documents have extractable content for indexing",
            inputs=[str(ws / "audit" / "artifact_registry.json")],
            outputs=[],
            metrics={
                "indexed_files": 0,
                "total_chunks": 0,
                "refused_documents": 0,
                "rejection_code": "NO_DOCUMENTS_TO_INDEX",
            },
            status="FAILED",
        )

        # Return a minimal indexer for Stage 7 compatibility even on refusal
        class MinimalIndexer:
            collection_name = "scholar_docs"
            embedder_kwargs = {
                "provider": "sentence-transformers",
                "model_name": "all-MiniLM-L6-v2",
            }

            def get_collection_count(self) -> int:
                return 0

        return IndexingOutcome(
            result={
                "status": "FAILED",
                "indexed_files": 0,
                "total_chunks": 0,
                "collection_count": None,
                "documents": [],
                "refused": [{"document_id": "", "code": "NO_DOCUMENTS_TO_INDEX"}],
            },
            indexer=MinimalIndexer(),
        )

    # Ensure journal directory exists
    journal_path = ws / "run-reports"
    journal_path.mkdir(parents=True, exist_ok=True)

    # Prepare backends and embedder
    embedder = get_embedder_fn(provider="sentence-transformers")
    backend = backend_cls(
        db_path=str(chroma_path), collection_name="scholar_docs", embedder=embedder
    )
    reader = reader_cls(db_path=str(chroma_path), collection_name="scholar_docs")

    # Call IndexService
    result = index_workspace_fn(
        request=request,
        backend=backend,
        reader=reader,
        embedder=embedder,
        workspace_root=ws,
    )

    # Map IndexServiceResult to our stage result format
    if result.outcome == "SUCCESS":
        stage_status = "SUCCESS"
    elif result.outcome == "PARTIAL":
        stage_status = "PARTIAL"
    elif result.outcome == "REFUSED":
        stage_status = "FAILED"
    else:  # FAILED
        stage_status = "FAILED"

    # Build refused list from rejected_documents
    refused = [
        {"document_id": r.document_id, "code": r.code}
        for r in result.rejected_documents
    ]

    index_res = {
        "status": stage_status,
        "indexed_files": result.counts.accepted_documents,
        "total_chunks": result.counts.visible_chunks,
        "collection_count": result.counts.visible_chunks
        if result.counts.accepted_documents > 0
        else None,
        "documents": [
            {
                "document_id": r.document_id,
                "study_id": r.study_id,
                "parent_artifact_id": r.parent_artifact_id,
                "screening_decision_id": r.screening_decision_id,
                "chunks": str(r.chunks),
            }
            for r in result.rejected_documents  # Note: we need accepted documents, not rejected
        ]
        if False
        else [],  # We'll populate from sources
        "refused": refused,
    }

    # Populate indexed documents from sources (use the data override when the
    # orchestrator forwarded one so patched readers take effect; otherwise
    # re-read, exactly as the base does a second read here).
    indexed_docs = []
    if screening_parents is None:
        screening_parents = accepted_screening_parents(ws)
    for source in request.sources:
        indexed_docs.append(
            {
                "document_id": source.request.document_id,
                "study_id": source.request.study_id,
                "parent_artifact_id": source.request.parent_artifact_id,
                "screening_decision_id": screening_parents.get(
                    source.request.study_id, {}
                ).get("decision_id", ""),
                "chunks": "0",  # Would need to query the backend
            }
        )
    index_res["documents"] = indexed_docs

    # E3 acceptance boundary (T-131, handoff section 6): when the kit
    # produced a real candidate (a sidecar file plus a verified live set),
    # the harness adapter decides acceptance and owns the canonical
    # section 6.6 event. Stubbed IndexService results (conformance
    # mapping tests) carry no sidecar and keep the legacy event below.
    _sidecar_rel = getattr(result, "sidecar_path", None)
    _live_matches = bool(getattr(result, "live_set_matches", False))
    if _sidecar_rel and _live_matches and result.outcome in ("SUCCESS", "PARTIAL"):
        try:
            from scholar_harness.index_acceptance import accept_index_candidate

            _sidecar_abs = ws / str(_sidecar_rel)
            if _sidecar_abs.is_file():
                _candidate = json.loads(_sidecar_abs.read_text(encoding="utf-8"))
                _decision = accept_index_candidate(
                    ws,
                    _candidate,
                    run_id=request.run_id,
                    manifest_path=str(_sidecar_rel),
                    reader=reader,
                    intent_path=getattr(result, "intent_path", None),
                )
                if not _decision.accepted:
                    # Adapter refusal: zero publication beyond the kit's own
                    # run report (check 7 never ran). No legacy BUILT line.
                    _refused_docs = [
                        {
                            "document_id": "",
                            "code": str(_decision.code or "REFUSED"),
                        }
                    ]
                    _failed: dict[str, Any] = {
                        "status": "FAILED",
                        "indexed_files": 0,
                        "total_chunks": 0,
                        "collection_count": None,
                        "documents": [],
                        "refused": _refused_docs,
                        "acceptance": _decision.as_dict(),
                    }

                    class MinimalIndexer:
                        collection_name = "scholar_docs"
                        embedder_kwargs = {
                            "provider": "sentence-transformers",
                            "model_name": "all-MiniLM-L6-v2",
                        }

                        def get_collection_count(self) -> int:
                            return 0

                    return IndexingOutcome(result=_failed, indexer=MinimalIndexer())
                # Adapter accepted: it already appended the canonical
                # RAG_INDEX_BUILT event with the full section 6.6 field
                # set, so the legacy continuity line below is skipped to
                # avoid a second, incomplete event.
                index_res["acceptance"] = _decision.as_dict()

                class MinimalIndexer:
                    collection_name = "scholar_docs"
                    embedder_kwargs = {
                        "provider": "sentence-transformers",
                        "model_name": "all-MiniLM-L6-v2",
                    }

                    def get_collection_count(self) -> int:
                        return index_res["total_chunks"]

                return IndexingOutcome(result=index_res, indexer=MinimalIndexer())
        except Exception as exc:
            # Fail closed: an unexpected adapter fault is a FAILED run
            # with the adapter/refusal code, never a legacy BUILT line
            # (which would carry an absolute chroma_dir and incomplete
            # metrics). Stubs without sidecar_path/live_set_matches never
            # enter this branch and keep the legacy mapping below.
            logger.warning(
                "E3 acceptance adapter did not decide; failing closed",
                exc_info=True,
            )
            _fault_code = str(getattr(exc, "code", None) or "INTERNAL_ERROR")

            class MinimalIndexer:
                collection_name = "scholar_docs"
                embedder_kwargs = {
                    "provider": "sentence-transformers",
                    "model_name": "all-MiniLM-L6-v2",
                }

                def get_collection_count(self) -> int:
                    return 0

            return IndexingOutcome(
                result={
                    "status": "FAILED",
                    "indexed_files": 0,
                    "total_chunks": 0,
                    "collection_count": None,
                    "documents": [],
                    "refused": [{"document_id": "", "code": _fault_code}],
                },
                indexer=MinimalIndexer(),
            )

    # Log audit event (the IndexService already journals its run report)
    # We also log the harness-level RAG_INDEX_BUILT for continuity
    append_legacy_event(
        ws,
        action="RAG_INDEX_BUILT",
        agent="scholar-harness",
        description=(
            f"Indexed {index_res['indexed_files']} accepted document(s) via IndexService; "
            f"{len(index_res['refused'])} refused"
        ),
        inputs=[str(ws / "audit" / "artifact_registry.json")],
        outputs=[str(chroma_path)],
        metrics={
            "indexed_files": index_res["indexed_files"],
            "total_chunks": index_res["total_chunks"],
            "refused_documents": len(index_res["refused"]),
        },
        status=index_res["status"],
    )

    # Return a minimal indexer-like object for Stage 7 compatibility
    class MinimalIndexer:
        collection_name = "scholar_docs"
        embedder_kwargs = {
            "provider": "sentence-transformers",
            "model_name": "all-MiniLM-L6-v2",
        }

        def get_collection_count(self) -> int:
            return index_res["total_chunks"]

    return IndexingOutcome(result=index_res, indexer=MinimalIndexer())
