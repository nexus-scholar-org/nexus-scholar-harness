"""Research Pipeline Orchestrator."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scholar_protocol.models import ResearchProtocol
from scholar_rag.chunker import text_fingerprint
from scholar_rag.index_models import IndexDocumentRequest
from scholar_rag.index_service import (
    IndexServiceRequest,
    IndexedSource,
    Counts,
    index_workspace,
)
from scholar_rag.replacement import ChromaReplacementView
from scholar_rag.index_verifier import ChromaVisibleSetReader
from scholar_rag.embedder import get_embedder

from .contracts.acceptance import ArtifactRegistry, RegistryEntry
from .contracts.models import ArtifactReference, DocumentManifestArtifact
from .workspace.errors import RegisteredWorkspaceIdentityMissingError
from .workspace.identity import validate_registered_workspace_id


# Backward compatibility for tests that monkeypatch ScholarIndexer
# The legacy ScholarIndexer.index_markdown path has been replaced by IndexService.index_workspace
# This class exists only to allow existing tests to monkeypatch it; it is not used in production.
class ScholarIndexer:
    """Deprecated: Legacy indexer interface for test compatibility only.

    The real indexing path now uses scholar_rag.index_service.index_workspace.
    This stub allows tests to monkeypatch the old interface.
    """

    def __init__(self, db_path: str, **kwargs: Any) -> None:
        self.db_path = db_path
        self.collection_name = "scholar_docs"
        self.embedder_kwargs = {
            "provider": "sentence-transformers",
            "model_name": "all-MiniLM-L6-v2",
        }

    def index_markdown(self, text: str, request: Any = None) -> list[dict[str, str]]:
        raise NotImplementedError(
            "Legacy ScholarIndexer.index_markdown is not implemented. Use IndexService."
        )

    def get_collection_count(self) -> int:
        return 0


# HCM-04b: provider resolution lives in the neutral pipeline stage
# (scholar_harness.pipeline.discovery). These re-exports preserve the
# historical ``orchestrator._resolve_providers`` import path -- tests and
# callers import it from here. Canonical definitions live in the stage
# module. Tests patch ``pipeline.discovery.SearchEngine`` directly.
from .pipeline.discovery import (  # noqa: F401
    _PROVIDER_MAP,
    _resolve_providers,
    run_discovery,
)

# HCM-04c: 2-tier deduplication lives in the neutral pipeline stage
# (scholar_harness.pipeline.deduplication). Tests patch
# ``pipeline.deduplication.Deduplicator`` directly. Canonical definitions
# live in the stage module.
from .pipeline.deduplication import (  # noqa: F401
    DeduplicationOutcome,
    run_deduplication,
)

# HCM-04d: abstract hydration lives in the neutral pipeline stage
# (scholar_harness.pipeline.hydration). The orchestrator delegates Stage 2.5
# to ``run_hydration``; canonical definitions live in the stage module.
from .pipeline.hydration import (  # noqa: F401
    HydrationOutcome,
    run_hydration,
)

# HCM-04e: verification lives in the neutral pipeline stage
# (scholar_harness.pipeline.verification). Tests patch
# ``pipeline.verification.DocumentVerifier`` directly. Canonical definitions
# live in the stage module.
from .pipeline.verification import (  # noqa: F401
    VerificationOutcome,
    run_verification,
)


logger = logging.getLogger(__name__)


# HCM-04g: fulltext extraction lives in the neutral pipeline stage
# (scholar_harness.pipeline.extraction). These re-exports preserve the
# historical ``orchestrator._extraction_file_stem`` / ``_study_doi`` /
# ``_study_pdf`` seams -- extraction_producer, fidelity, conformance, and
# e2e import the helpers from here. Canonical definitions live in the
# stage module. No engine seam: the stage constructs
# ``scholar_pdf.extract.PyMuPDFEngine`` directly, exactly as Stage 5 did.
from .pipeline.extraction import (  # noqa: F401
    ExtractionOutcome,
    _extraction_file_stem,
    _study_doi,
    _study_pdf,
    run_extraction,
)

# HCM-04i: dynamic protocol matrix lives in the neutral pipeline stage
# (scholar_harness.pipeline.matrix). Tests patch
# ``pipeline.matrix.ScholarRetriever`` / ``pipeline.matrix.MatrixExtractor``
# directly. Canonical definitions live in the stage module.
from .pipeline.matrix import (  # noqa: F401
    MatrixOutcome,
    run_matrix,
)

# HCM-04j: citation knowledge graph lives in the neutral pipeline stage
# (scholar_harness.pipeline.graph). Tests patch
# ``pipeline.graph.CitationGraphBuilder`` / ``pipeline.graph.GraphVisualizer``
# directly. Canonical definitions live in the stage module.
from .pipeline.graph import (  # noqa: F401
    GraphOutcome,
    run_graph,
)

# HCM-04k: grounded synthesis lives in the neutral pipeline stage
# (scholar_harness.pipeline.synthesis). Tests patch
# ``pipeline.synthesis.GroundedSynthesisEngine`` directly. Canonical
# definitions live in the stage module.
from .pipeline.synthesis import (  # noqa: F401
    SynthesisOutcome,
    run_synthesis,
)

# HCM-04l: pipeline coordination glue lives in the neutral coordinator
# (scholar_harness.pipeline.coordinator). The orchestrator keeps only the
# thin run_pipeline_async/run_pipeline delegates with identical signatures;
# the coordinator calls stages, never the orchestrator (no cycle: stages
# read orch.__dict__ lazily inside functions only).
from .pipeline.coordinator import run_pipeline as _coordinator_run_pipeline  # noqa: F401


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON to disk with an atomic temp-file + os.replace dance."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


class ResearchOrchestrator:
    """Master research pipeline orchestrator integrating all Nexus Scholar toolkits."""

    def __init__(self, workspace_dir: Path | str = "."):
        self.workspace_dir = Path(workspace_dir).resolve()

    def get_status(self) -> dict[str, Any]:
        """Inspect workspace state and collect comprehensive progress statistics."""
        status: dict[str, Any] = {
            "workspace": str(self.workspace_dir),
            "protocol_found": False,
            "title": "Unknown",
            "playbook_type": "Unknown",
            "phase": "PHASE_0_PENDING",
            "discovered_count": 0,
            "deduped_count": 0,
            "verified_count": 0,
            "included_count": 0,
            "excluded_count": 0,
            "pdfs_count": 0,
            "extracted_count": 0,
            "vector_chunks": 0,
            "graph_nodes": 0,
            "matrix_rows": 0,
            "synthesis_generated": False,
            "latest_events": [],
        }

        # 1. Protocol Inspection
        proto_file = self.workspace_dir / "protocol.json"
        if proto_file.exists():
            try:
                protocol = ResearchProtocol.model_validate_json(
                    proto_file.read_text(encoding="utf-8")
                )
                status["protocol_found"] = True
                status["title"] = (
                    protocol.metadata.get("title", "Unknown")
                    if isinstance(protocol.metadata, dict)
                    else getattr(protocol.metadata, "title", "Unknown")
                )
                status["playbook_type"] = protocol.playbook_type.value
                status["phase"] = "PHASE_1_DISCOVERY"
            except Exception as e:
                logger.warning(f"Failed to parse protocol.json: {e}")

        # 2. Literature Files
        lit_dir = self.workspace_dir / "literature"
        if (lit_dir / "raw_search.json").exists():
            try:
                raw_docs = json.loads(
                    (lit_dir / "raw_search.json").read_text(encoding="utf-8")
                )
                status["discovered_count"] = len(raw_docs)
            except Exception:
                pass

        if (lit_dir / "deduped.json").exists():
            try:
                dedup_docs = json.loads(
                    (lit_dir / "deduped.json").read_text(encoding="utf-8")
                )
                status["deduped_count"] = len(dedup_docs)
            except Exception:
                pass

        if (lit_dir / "verified.json").exists():
            try:
                ver_docs = json.loads(
                    (lit_dir / "verified.json").read_text(encoding="utf-8")
                )
                status["verified_count"] = len(ver_docs)
            except Exception:
                pass

        if (lit_dir / "included.json").exists():
            try:
                inc_docs = json.loads(
                    (lit_dir / "included.json").read_text(encoding="utf-8")
                )
                status["included_count"] = len(inc_docs)
                status["phase"] = "PHASE_1_HARVESTING"
            except Exception:
                pass

        if (lit_dir / "excluded.json").exists():
            try:
                exc_docs = json.loads(
                    (lit_dir / "excluded.json").read_text(encoding="utf-8")
                )
                status["excluded_count"] = len(exc_docs)
            except Exception:
                pass

        if (lit_dir / "knowledge_graph.json").exists() or (
            lit_dir / "graph.json"
        ).exists():
            g_file = (
                lit_dir / "knowledge_graph.json"
                if (lit_dir / "knowledge_graph.json").exists()
                else lit_dir / "graph.json"
            )
            try:
                g_data = json.loads(g_file.read_text(encoding="utf-8"))
                status["graph_nodes"] = len(g_data.get("nodes", []))
            except Exception:
                pass

        if (lit_dir / "synthesis_matrix.json").exists():
            try:
                m_data = json.loads(
                    (lit_dir / "synthesis_matrix.json").read_text(encoding="utf-8")
                )
                status["matrix_rows"] = len(m_data) if isinstance(m_data, list) else 0
            except Exception:
                pass

        # 3. Harvested PDFs
        pdf_dir = self.workspace_dir / "pdfs"
        if pdf_dir.exists():
            status["pdfs_count"] = len(list(pdf_dir.glob("*.pdf")))

        # 4. Extracted Markdown
        ext_dir = self.workspace_dir / "extracted"
        if ext_dir.exists():
            status["extracted_count"] = len(list(ext_dir.glob("*.md")))
            if status["extracted_count"] > 0:
                status["phase"] = "PHASE_2_SYNTHESIS"

        # 4b. Vector Database Chunks
        chroma_dir = self.workspace_dir / "chroma_db"
        if not chroma_dir.exists():
            chroma_dir = self.workspace_dir / "rag" / "chroma_db"
        if chroma_dir.exists():
            try:
                import chromadb

                client = chromadb.PersistentClient(path=str(chroma_dir))
                collection = client.get_collection("scholar_docs")
                status["vector_chunks"] = collection.count()
            except Exception:
                pass

        # 5. Synthesis Review
        synth_file = self.workspace_dir / "synthesis" / "literature_review.md"
        if synth_file.exists():
            content = synth_file.read_text(encoding="utf-8").strip()
            if (
                len(content) > 50
                and "To be generated from extracted papers" not in content
            ):
                status["synthesis_generated"] = True
                if status["matrix_rows"] > 0 and status["vector_chunks"] > 0:
                    status["phase"] = "PHASE_3_COMPLETE"

        # 6. Audit Journal Events
        journal_file = self.workspace_dir / "audit" / "journal.jsonl"
        if journal_file.exists():
            try:
                events = []
                for line in (
                    journal_file.read_text(encoding="utf-8").strip().split("\n")
                ):
                    if line.strip():
                        events.append(json.loads(line))
                status["latest_events"] = events[-5:]
            except Exception:
                pass

        return status

    def sync_state(self, dry_run: bool = False) -> dict[str, Any]:
        """Atomically rebuild project.json stats and INDEX.md from filesystem state.

        Derives all countable metrics from the actual workspace layout (literature
        payloads, screening outputs, PDFs, extractions, synthesis artifacts) and
        merges them into the existing project.json manifest, preserving
        researcher-authored fields (title, research_questions, keywords, etc.).
        Uses an atomic temp-file + os.replace dance so a crash mid-write can never
        leave a truncated manifest or orphaned INDEX.md.
        """
        ws = self.workspace_dir
        ws.mkdir(parents=True, exist_ok=True)

        stats: dict[str, Any] = {}

        def _count(name: str, path: Path) -> None:
            if path.exists():
                try:
                    stats[name] = len(json.loads(path.read_text(encoding="utf-8")))
                except Exception:
                    stats[name] = 0

        lit = ws / "literature"
        _count("discovered_papers", lit / "raw_search.json")
        _count("deduped_papers", lit / "deduped.json")
        _count("verified_papers", lit / "verified.json")
        _count("included_papers", lit / "included.json")
        _count("excluded_papers", lit / "excluded.json")

        # PRISMA screening artifacts (batch decisions exclude batch-json supersets)
        prisma_path = lit / "prisma_report.json"
        if prisma_path.exists():
            try:
                prisma = json.loads(prisma_path.read_text(encoding="utf-8"))
                for key in (
                    "total_identified",
                    "records_screened",
                    "records_included",
                    "records_included_confirmed",
                    "records_included_provisional_caveats",
                    "records_excluded",
                    "conflicts_flagged",
                    "reports_sought_for_retrieval",
                    "reports_not_retrieved",
                    "reports_retrieved",
                    "retrieval_rate_pct",
                    "final_fulltext_corpus_assessed",
                ):
                    if key in prisma:
                        stats[key] = prisma[key]
            except Exception:
                pass

        # Harvested PDFs & extractions
        pdf_dir = ws / "pdfs"
        if pdf_dir.exists():
            stats["downloaded_pdfs"] = len(list(pdf_dir.glob("*.pdf")))
        ext_dir = ws / "extracted"
        if ext_dir.exists():
            stats["extracted_markdowns"] = len(list(ext_dir.glob("*.md")))

        # Graph / matrix / corpus artifacts
        graph_file = (
            lit / "knowledge_graph.json"
            if (lit / "knowledge_graph.json").exists()
            else lit / "graph.json"
        )
        if graph_file.exists():
            try:
                graph = json.loads(graph_file.read_text(encoding="utf-8"))
                stats["graph_nodes"] = len(graph.get("nodes", []))
                stats["graph_edges"] = len(graph.get("links", graph.get("edges", [])))
            except Exception:
                stats["graph_nodes"] = 0
        _count("merged_records", lit / "extraction" / "merged" / "records.json")
        clean_ids = lit / "screening" / "_clean_corpus_ids.json"
        if clean_ids.exists():
            try:
                stats["audited_clean_corpus"] = len(
                    json.loads(clean_ids.read_text(encoding="utf-8"))
                )
            except Exception:
                stats["audited_clean_corpus"] = 0
        matrix_path = lit / "synthesis_matrix.json"
        if not matrix_path.exists():
            matrix_path = ws / "synthesis" / "synthesis_matrix.json"
        _count("matrix_studies", matrix_path)

        # Vector DB chunk count
        chroma_dir = ws / "rag" / "chroma_db"
        if chroma_dir.exists():
            try:
                import chromadb

                client = chromadb.PersistentClient(path=str(chroma_dir))
                stats["vector_chunks"] = client.get_collection("scholar_docs").count()
            except Exception:
                pass

        # Merge into manifest
        manifest_path = ws / "project.json"
        manifest: dict[str, Any] = {}
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                manifest = {}
        if not manifest:
            manifest = {
                "project_id": ws.name,
                "title": ws.name,
                "created_at": datetime.now(UTC).isoformat(),
                "status": "active",
                "research_questions": [],
                "keywords": [],
            }
        manifest["updated_at"] = datetime.now(UTC).isoformat()
        merged_stats = dict(manifest.get("stats", {}))
        merged_stats.update(stats)
        # Recompute a defensible status flag if screen flow exists
        if merged_stats.get("final_fulltext_corpus_assessed", 0) > 0:
            merged_stats["phase"] = "PHASE_4_COMPLETE"
        elif merged_stats.get("extracted_markdowns", 0) > 0:
            merged_stats["phase"] = "PHASE_2_SYNTHESIS"
        elif merged_stats.get("included_papers", 0) > 0:
            merged_stats["phase"] = "PHASE_1_HARVESTING"
        else:
            merged_stats["phase"] = "PHASE_0_PENDING"
        manifest["stats"] = merged_stats

        if dry_run:
            return {
                "workspace": str(ws),
                "dry_run": True,
                "stats_updated": stats,
                "index_regenerated": False,
            }

        # Atomic write project.json
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(manifest_path, manifest)

        # Regenerate INDEX.md atomically via workspace-manager (reuse canonical renderer)
        index_regenerated = self._refresh_index_md_atomic()

        self._log_audit_event(
            action="STATE_SYNC",
            agent="scholar-harness",
            description=f"Rebuilt {ws.name} project.json + INDEX.md from filesystem state ({len(stats)} stats refreshed)",
            inputs=[
                str(p)
                for p in (lit / "raw_search.json", lit / "prisma_report.json")
                if p.exists()
            ],
            outputs=["project.json", "INDEX.md"],
            metrics=stats,
        )

        return {
            "workspace": str(ws),
            "dry_run": False,
            "stats": stats,
            "index_regenerated": index_regenerated,
        }

    def _refresh_index_md_atomic(self) -> bool:
        """Regenerate INDEX.md using the workspace-manager's canonical renderer.

        Thin adapter over :func:`workspace.audit.refresh_index_atomic`, which
        preserves the atomic backup/restore discipline (snapshot previous file,
        restore when the render raises or leaves an empty result). Appends no
        journal row.
        """
        from .workspace.audit import refresh_index_atomic

        return refresh_index_atomic(self.workspace_dir)

    async def run_pipeline_async(
        self,
        protocol_path: Path | str | None = None,
        max_search_results: int | None = None,
        mock_mode: bool = False,
    ) -> dict[str, Any]:
        """Execute the end-to-end research workflow from protocol to grounded synthesis.

        Thin delegate to ``pipeline.coordinator.run_pipeline`` (HCM-04l):
        identical signature; the coordinator owns the glue (protocol
        load/validate, dir setup, Stage 1-9 delegation, Stage-4 gate +
        PAUSE audit, Stage-10 COMPLETED audit, status propagation).
        """
        return await _coordinator_run_pipeline(
            workspace_dir=self.workspace_dir,
            protocol_path=protocol_path,
            max_search_results=max_search_results,
            mock_mode=mock_mode,
            indexing_fn=self._run_indexing_stage,
        )

    def run_pipeline(
        self,
        protocol_path: Path | str | None = None,
        max_search_results: int | None = None,
    ) -> dict[str, Any]:
        """Synchronous wrapper for run_pipeline_async."""
        return asyncio.run(
            self.run_pipeline_async(
                protocol_path=protocol_path, max_search_results=max_search_results
            )
        )

    def _load_artifact_registry(self) -> ArtifactRegistry | None:
        """Thin delegate to ``pipeline.indexing.load_artifact_registry`` (HCM-04h).

        Preserves the ``orch._load_artifact_registry()`` seam with an identical
        signature; the canonical implementation lives in the neutral stage.
        """
        from .pipeline.indexing import load_artifact_registry

        return load_artifact_registry(self.workspace_dir)

    def _accepted_artifact_payload(self, entry: RegistryEntry) -> Any | None:
        """Thin delegate to ``pipeline.indexing.accepted_artifact_payload`` (HCM-04h).

        Identical signature; canonical implementation lives in the stage.
        """
        from .pipeline.indexing import accepted_artifact_payload

        return accepted_artifact_payload(self.workspace_dir, entry)

    def _accepted_screening_parents(self) -> dict[str, dict[str, str]]:
        """Thin delegate to ``pipeline.indexing.accepted_screening_parents`` (HCM-04h).

        Identical signature; canonical implementation lives in the stage.
        """
        from .pipeline.indexing import accepted_screening_parents

        return accepted_screening_parents(self.workspace_dir)

    def _accepted_document_records(self) -> dict[str, dict[str, str]]:
        """Thin delegate to ``pipeline.indexing.accepted_document_records`` (HCM-04h).

        Identical signature; canonical implementation lives in the stage.
        """
        from .pipeline.indexing import accepted_document_records

        return accepted_document_records(self.workspace_dir)

    def recorded_workspace_id(self) -> str:
        """Return the workspace identity recorded in ``project.json``.

        Thin adapter over :func:`workspace.identity.require_recorded_identity`:
        records and re-reads only, never mints, never derives from the slug.
        Preserves the observed non-object ``AttributeError`` (HCM-01 defect (a)).
        """
        from .workspace.identity import require_recorded_identity

        return require_recorded_identity(self.workspace_dir)

    def _build_parent_view(self) -> dict[str, Any] | None:
        """Thin delegate to ``pipeline.indexing.build_parent_view`` (HCM-04h).

        Identical signature; canonical implementation lives in the stage.
        """
        from .pipeline.indexing import build_parent_view

        return build_parent_view(self.workspace_dir)

    def _build_index_service_request(
        self,
        *,
        chroma_dir: Path,
        parent_view: dict[str, Any],
        run_id: str,
        created_at: str,
        producer_commit: str,
        producer_version: str,
    ) -> IndexServiceRequest | None:
        """Thin delegate to ``pipeline.indexing.build_index_service_request`` (HCM-04h).

        Identical signature; forwards this module's (possibly patched)
        ``get_embedder`` global as the explicit kit collaborator and this
        instance's (possibly patched) ``_accepted_*`` readers as explicit
        data collaborators so the ``orch.get_embedder`` and
        ``orch._accepted_document_records`` monkeypatch seams keep working.
        Canonical implementation and kit defaults live in the stage.
        """
        from .pipeline.indexing import build_index_service_request

        return build_index_service_request(
            workspace_dir=self.workspace_dir,
            chroma_dir=chroma_dir,
            parent_view=parent_view,
            run_id=run_id,
            created_at=created_at,
            producer_commit=producer_commit,
            producer_version=producer_version,
            get_embedder_fn=get_embedder,
            documents=self._accepted_document_records(),
            screening_parents=self._accepted_screening_parents(),
        )

    def _run_indexing_stage(self, chroma_dir: Path) -> tuple[dict[str, Any], Any]:
        """Thin delegate to ``pipeline.indexing.run_indexing`` (HCM-04h).

        Identical signature; forwards this module's (possibly patched)
        ``get_embedder`` / ``ChromaReplacementView`` / ``ChromaVisibleSetReader``
        / ``index_workspace`` globals as explicit kit collaborators and this
        instance's (possibly patched) ``_build_parent_view`` / ``_accepted_*``
        readers as explicit data collaborators so all live Stage-6 seams keep
        working. Canonical implementation and kit defaults live in the stage.
        The outcome carries ``(result dict, indexer)`` for Stage 7.
        """
        from .pipeline.indexing import run_indexing

        outcome = run_indexing(
            workspace_dir=self.workspace_dir,
            chroma_dir=chroma_dir,
            get_embedder_fn=get_embedder,
            backend_cls=ChromaReplacementView,
            reader_cls=ChromaVisibleSetReader,
            index_workspace_fn=index_workspace,
            parent_view=self._build_parent_view(),
            documents=self._accepted_document_records(),
            screening_parents=self._accepted_screening_parents(),
        )
        return outcome.result, outcome.indexer

    def _log_audit_event(
        self,
        action: str,
        agent: str,
        description: str,
        inputs: list[str],
        outputs: list[str],
        metrics: dict[str, Any],
        status: str = "SUCCESS",
    ) -> None:
        """Appends an event to audit/journal.jsonl.

        Thin adapter over :func:`workspace.audit.append_legacy_event`, preserving
        the observed ``hex(hash(...))`` event-id scheme, no uppercasing, no
        manifest/INDEX update. ``status`` is the observed outcome, never a
        constant (a refused run must not log ``SUCCESS``).
        """
        from .workspace.audit import append_legacy_event

        append_legacy_event(
            self.workspace_dir,
            action,
            agent,
            description,
            inputs,
            outputs,
            metrics,
            status=status,
        )
