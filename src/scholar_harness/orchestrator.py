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
from scholar_rag.synthesis import GroundedSynthesisEngine

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


# HCM-04b: provider resolution and the discovery engine live in the neutral
# pipeline stage (scholar_harness.pipeline.discovery). These re-exports
# preserve the historical ``orchestrator._resolve_providers`` seam -- tests
# import it from here -- and the ``orchestrator.SearchEngine`` monkeypatch
# seam honored by the stage. Canonical definitions live in the stage module.
from .pipeline.discovery import (  # noqa: F401
    _PROVIDER_MAP,
    _resolve_providers,
    SearchEngine,
    run_discovery,
)

# HCM-04c: 2-tier deduplication lives in the neutral pipeline stage
# (scholar_harness.pipeline.deduplication). This re-export preserves the
# historical ``orchestrator.Deduplicator`` monkeypatch seam honored by the
# stage. Canonical definitions live in the stage module.
from .pipeline.deduplication import (  # noqa: F401
    DeduplicationOutcome,
    Deduplicator,
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
# (scholar_harness.pipeline.verification). This re-export preserves the
# historical ``orchestrator.DocumentVerifier`` monkeypatch seam honored by the
# stage. Canonical definitions live in the stage module.
from .pipeline.verification import (  # noqa: F401
    DocumentVerifier,
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
# (scholar_harness.pipeline.matrix). These re-exports preserve the
# historical ``orchestrator.ScholarRetriever`` / ``orchestrator.MatrixExtractor``
# monkeypatch seams -- fidelity and extraction-stage tests patch both from
# here. Canonical definitions live in the stage module.
from .pipeline.matrix import (  # noqa: F401
    MatrixExtractor,
    MatrixOutcome,
    ScholarRetriever,
    run_matrix,
)

# HCM-04j: citation knowledge graph lives in the neutral pipeline stage
# (scholar_harness.pipeline.graph). These re-exports preserve the
# historical ``orchestrator.CitationGraphBuilder`` /
# ``orchestrator.GraphVisualizer`` monkeypatch seams -- fidelity,
# extraction-stage, and matrix-stage tests patch both from here. Canonical
# definitions live in the stage module.
from .pipeline.graph import (  # noqa: F401
    CitationGraphBuilder,
    GraphOutcome,
    GraphVisualizer,
    run_graph,
)


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
        """Execute the end-to-end research workflow from protocol to grounded synthesis."""
        p_path = Path(protocol_path or (self.workspace_dir / "protocol.json")).resolve()
        if not p_path.exists():
            raise FileNotFoundError(f"Protocol file not found at {p_path}")

        protocol = ResearchProtocol.model_validate_json(
            p_path.read_text(encoding="utf-8")
        )
        results: dict[str, Any] = {"status": "SUCCESS", "stages": {}}

        # Setup workspace directories
        lit_dir = self.workspace_dir / "literature"
        pdf_dir = self.workspace_dir / "pdfs"
        ext_dir = self.workspace_dir / "extracted"
        synth_dir = self.workspace_dir / "synthesis"
        audit_dir = self.workspace_dir / "audit"
        chroma_dir = self.workspace_dir / "chroma_db"

        for d in (lit_dir, pdf_dir, ext_dir, synth_dir, audit_dir):
            d.mkdir(parents=True, exist_ok=True)

        # -------------------------------------------------------------
        # Stage 1: Protocol Query Compilation & Search
        # -------------------------------------------------------------
        # HCM-04b: delegated to the neutral pipeline stage. run_discovery owns
        # query compilation, provider resolution, federated search, and
        # raw-result publication; it emits no audit event and writes no
        # registry state.
        discovery_outcome = await run_discovery(
            protocol_path=p_path,
            literature_dir=lit_dir,
            max_search_results=max_search_results,
        )
        # Local binding retained: Stage 2 deduplicates these documents.
        discovered_docs = discovery_outcome.documents
        results["stages"]["discovery"] = discovery_outcome.count

        # -------------------------------------------------------------
        # Stage 2: 2-Tier Deduplication & PID Cluster Assignment
        # Bug fix: Dedup now runs on ALL discovered_docs combined (not a subset).
        # workspace_ids (SCI-XXXXXX) are assigned by the Deduplicator here.
        # -------------------------------------------------------------
        # HCM-04c: delegated to the neutral pipeline stage. run_deduplication
        # owns 2-tier dedup, PID cluster assignment, and deduped publication;
        # it emits no audit event and writes no registry state.
        dedup_outcome = run_deduplication(
            discovered_documents=discovered_docs,
            literature_dir=lit_dir,
        )
        # Local binding retained: Stage 2.5 hydrates these documents.
        unique_docs = dedup_outcome.representatives
        results["stages"]["deduplication"] = {
            "unique": dedup_outcome.unique,
            "duplicates_removed": dedup_outcome.duplicates_removed,
        }

        # -------------------------------------------------------------
        # Stage 2.5: Abstract Hydration (backfill missing abstracts)
        # -------------------------------------------------------------
        # HCM-04d: delegated to the neutral pipeline stage. run_hydration owns
        # client construction, missing-abstract backfill, the
        # ABSTRACT_HYDRATION audit event, and client close; the hydrated
        # documents flow to Stage 3 unchanged.
        hydration_outcome = await run_hydration(
            documents=unique_docs,
            workspace_dir=self.workspace_dir,
        )
        # Local binding retained: Stage 3 verifies these documents.
        docs_for_verify = hydration_outcome.documents

        # -------------------------------------------------------------
        # Stage 3: Verification (HCM-04e-1 Option B bridge-or-refuse)
        # -------------------------------------------------------------
        # HCM-04e: delegated to the neutral pipeline stage. run_verification
        # owns verifier construction, the DOI-bridge preserve/restore/refuse
        # loop (enumerate, no SCI- mint), verified/quarantine publication,
        # and the identity-resolved audit event; the identified documents
        # flow to Stage 4 unchanged.
        verification_outcome = await run_verification(
            documents=docs_for_verify,
            literature_dir=lit_dir,
            workspace_dir=self.workspace_dir,
        )
        # Local binding retained: Stage 4 counts these documents.
        verified_docs = verification_outcome.documents
        results["stages"]["verification"] = {
            "status": verification_outcome.status,
            "verified": verification_outcome.verified,
            "refused": verification_outcome.refused,
            "preserved": verification_outcome.preserved,
            "bridge_restored": verification_outcome.bridge_restored,
            "refusal_reasons": verification_outcome.refusal_reasons,
        }
        if verification_outcome.quarantine:
            results["stages"]["verification"]["quarantine"] = (
                verification_outcome.quarantine
            )

        # -------------------------------------------------------------
        # Stage 4: Systematic PRISMA 2020 Screening — Agent-in-the-loop
        #
        # The harness itself IS the LLM. No external API required.
        # The pipeline prepares batch files (20 papers each) in literature/screening/.
        # The harness agent reads each batch and writes a decisions file.
        # Run `agent_screen.py collect <workspace>` after agent finishes.
        # -------------------------------------------------------------
        # HCM-04f: delegated to the neutral pipeline stage.
        # run_screening_preparation owns the automated preparation (call-time
        # cmd_prepare, the batch_*.json glob count excluding _decisions, and
        # the IN PROGRESS prisma report); it emits no decisions/collect/audit.
        # The included.json collect-gate + PAUSE audit below stay here: they
        # are the coordinator's handoff gate, not preparation. protocol_data
        # (base :622) was vestigial -- read but never used downstream -- and
        # is not carried into the stage; papers_to_screen stays bound here
        # from the Stage 3 verified_docs.
        from scholar_harness.pipeline.screening_prepare import (
            run_screening_preparation,
        )

        preparation_outcome = run_screening_preparation(
            workspace_dir=self.workspace_dir, batch_size=20, force=True
        )
        # Local binding retained: Stage 4 reports this count; Stages 5-9 gate
        # on the collect handoff below.
        total_batches = preparation_outcome.total_batches

        results["stages"]["screening"] = {
            "status": "PENDING_AGENT_REVIEW",
            "batch_files_prepared": total_batches,
            "papers_to_screen": len(verified_docs),
        }
        # Stages 5-9 require the PRISMA collect handoff to have run. Without
        # literature/included.json the pipeline must stop, never fabricate output.
        inc_file = lit_dir / "included.json"
        if not inc_file.exists():
            for stage in ("extraction", "indexing", "matrix", "graph", "synthesis"):
                results["stages"][stage] = {
                    "status": "SKIPPED",
                    "reason": "PRISMA collect not run yet",
                }
            results["status"] = "PENDING_AGENT_REVIEW"
            self._log_audit_event(
                action="PIPELINE_RUN_PAUSED_FOR_SCREENING",
                agent="scholar-harness",
                description="Pipeline paused at PRISMA agent-in-the-loop handoff; "
                "screen literature/screening/batch_*.json then run agent_screen.py collect",
                inputs=[str(p_path)],
                outputs=[str(lit_dir / "screening")],
                metrics=results["stages"],
            )
            return results

        inc_docs = json.loads(inc_file.read_text(encoding="utf-8"))

        # -------------------------------------------------------------
        # Stage 5: Fulltext Extraction over included studies (no invented prose)
        # -------------------------------------------------------------
        # HCM-04g: delegated to the neutral pipeline stage. run_extraction
        # owns the existing-file skip, the metadata dict, the PDF locate +
        # PyMuPDF try/warning-fallthrough, and the verbatim
        # metadata-frontmatter write; it emits no audit event and writes no
        # registry state.
        extraction_outcome = run_extraction(
            included_documents=inc_docs,
            pdfs_dir=pdf_dir,
            extracted_dir=ext_dir,
        )
        # Local bindings retained: the results mapping below reads them.
        extracted_files = extraction_outcome.documents
        metadata_frontmatter_only = extraction_outcome.metadata_frontmatter_only
        results["stages"]["extraction"] = {
            "status": "DONE",
            "documents": len(extracted_files),
            "metadata_frontmatter_only": metadata_frontmatter_only,
        }

        # -------------------------------------------------------------
        # Stage 6: Vector & Semantic Indexing (ChromaDB)
        # -------------------------------------------------------------
        # E3-008 / T-90: the typed indexing surface refuses to mint chunk
        # identity it was not told, so identity is bound per document from the
        # pipeline's own recorded state (see _index_accepted_documents). The
        # workspace limb is the registered identity recorded in project.json at
        # inception -- never the project slug, never a value minted here. A
        # document with no accepted screening parent is REFUSED, never indexed
        # on an inferred workspace_id.
        index_res, indexer = self._run_indexing_stage(chroma_dir)
        results["stages"]["indexing"] = index_res

        # -------------------------------------------------------------
        # Stage 7: Dynamic Protocol Matrix Extraction
        # -------------------------------------------------------------
        # HCM-04i: delegated to the neutral pipeline stage. run_matrix owns
        # retriever construction, MatrixExtractor construction, and
        # extract_all publication; it emits no audit event and writes no
        # registry state. The retriever binding is carried for Stage 9.
        matrix_outcome = run_matrix(
            protocol=protocol,
            indexer_compat=indexer,
            chroma_dir=chroma_dir,
            literature_dir=lit_dir,
        )
        # Local bindings retained: the results mapping below reads them;
        # Stage 9 reuses the carried retriever.
        matrix_rows = matrix_outcome.rows
        retriever = matrix_outcome.retriever
        results["stages"]["matrix_rows"] = {"status": "DONE", "rows": len(matrix_rows)}

        # -------------------------------------------------------------
        # Stage 8: Citation Knowledge Graph & PageRank
        # -------------------------------------------------------------
        # HCM-04j: delegated to the neutral pipeline stage. run_graph owns
        # client construction, DOI collection, build_graph, PageRank, JSON
        # export, and HTML visualization; it emits no audit event and writes
        # no registry state. The client lifecycle is unchanged (per call, no
        # close -- the base never closed the graph client).
        graph_outcome = await run_graph(
            included_documents=inc_docs,
            literature_dir=lit_dir,
        )
        # Local bindings retained: the results mapping below reads them.
        results["stages"]["graph_nodes"] = {
            "status": "DONE",
            "nodes": graph_outcome.nodes,
            "edges": graph_outcome.edges,
        }

        # -------------------------------------------------------------
        # Stage 9: Grounded Evidence Synthesis & Entailment
        # -------------------------------------------------------------
        engine = GroundedSynthesisEngine(retriever=retriever)
        first_rq = (
            protocol.research_questions[0] if protocol.research_questions else None
        )
        rq_text = (
            first_rq.text if first_rq else "What are the primary empirical findings?"
        )
        rq_id = first_rq.id if first_rq else "RQ1"

        synthesis_result = engine.synthesize(
            query=rq_text,
            rq_id=rq_id,
            section_category="results_empirical",
        )

        synth_file = synth_dir / "literature_review.md"
        synth_file.write_text(synthesis_result.synthesis_markdown, encoding="utf-8")
        results["stages"]["synthesis"] = {
            "verified_claims": synthesis_result.verified_claims_count,
            "total_claims": len(synthesis_result.claims),
            "entailment_rate": synthesis_result.entailment_rate,
        }

        # -------------------------------------------------------------
        # Stage 10: Append-Only Audit Journal Logging
        # -------------------------------------------------------------
        self._log_audit_event(
            action="PIPELINE_RUN_COMPLETED",
            agent="scholar-harness",
            description=f"Completed end-to-end research pipeline for '{protocol.metadata.get('title', 'Unknown')}'",
            inputs=[str(p_path)],
            outputs=[
                str(synth_file),
                str(lit_dir / "synthesis_matrix.csv"),
                str(lit_dir / "knowledge_graph.html"),
            ],
            metrics=results["stages"],
        )

        return results

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
