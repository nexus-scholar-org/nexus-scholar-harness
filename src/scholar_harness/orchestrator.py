"""Research Pipeline Orchestrator."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import networkx as nx
from scholar_graph.builder import CitationGraphBuilder
from scholar_graph.visualizer import GraphVisualizer
from scholar_pdf.extract import PyMuPDFEngine
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
from scholar_rag.matrix import MatrixExtractor
from scholar_rag.retriever import ScholarRetriever
from scholar_rag.synthesis import GroundedSynthesisEngine
from scholar_search.verifier import DocumentVerifier

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


logger = logging.getLogger(__name__)


def _study_doi(doc_item: dict[str, Any]) -> str:
    return (doc_item.get("external_ids") or {}).get("doi") or doc_item.get("doi") or ""


def _extraction_file_stem(doc_item: dict[str, Any]) -> str:
    """The on-disk filename stem for a document's extracted markdown.

    FILESYSTEM RESOLUTION ONLY. This value names a file under ``extracted/``;
    it is never an identity. Reading a ``document_id``, ``study_id``, or
    ``workspace_id`` out of this stem would be inference from a filename, which
    Contract v1 forbids: identity is stated in a typed request or inherited from
    an accepted artifact, never derived from a slug. Stage 6 therefore takes
    both limbs from the accepted ``document_manifest`` (``_accepted_document_records``)
    and takes its path from the record's own ``extracted_path``.

    The stem still prefers ``workspace_id`` over ``study_id`` because that is how
    Stage 5 has always named the file; the collision is a filename, not an
    identity, and it cannot reach a typed request.
    """
    idv = doc_item.get("workspace_id") or doc_item.get("study_id") or ""
    doi = _study_doi(doc_item)
    return (idv or doi or "doc").replace("/", "_").replace(":", "_")


def _study_pdf(pdf_dir: Path, doc_item: dict[str, Any]) -> Path | None:
    """Locate a harvested PDF for a study, preferring deterministic slugs."""
    doi = _study_doi(doc_item)
    slug = _extraction_file_stem(doc_item)
    candidates = [
        pdf_dir / f"{slug}.pdf",
        pdf_dir / f"{doi.replace('/', '_').replace(':', '_')}.pdf",
    ]
    for c in candidates:
        if c.exists():
            return c
    if doi:
        doi_slug = doi.replace("/", "_").replace(":", "_")
        for p in pdf_dir.glob("*.pdf"):
            if p.stem.startswith(doi_slug):
                return p
    return None


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
        # Stage 3: Verification
        # Bug fix: After verification, copy workspace_ids back from deduped docs
        # because verify_document() may return a freshly normalized Document that
        # loses the workspace_id set by the Deduplicator.
        # -------------------------------------------------------------
        verifier = DocumentVerifier()
        verified_docs, audit = await verifier.process_batch(
            docs_for_verify, verify=True, enrich=True
        )

        # Restore workspace_ids on verified docs using DOI as bridge
        wsid_by_doi: dict[str, str] = {
            d.external_ids.doi: d.workspace_id
            for d in docs_for_verify
            if d.external_ids.doi and d.workspace_id
        }
        for vd in verified_docs:
            if not vd.workspace_id and vd.external_ids.doi:
                vd.workspace_id = wsid_by_doi.get(vd.external_ids.doi)
            if not vd.workspace_id:
                # Last resort: assign a temporary sequential ID
                vd.workspace_id = f"SCI-{verified_docs.index(vd) + 1:06d}"

        (lit_dir / "verified.json").write_text(
            json.dumps(
                [
                    asdict(d) if hasattr(d, "__dataclass_fields__") else d
                    for d in verified_docs
                ],
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        results["stages"]["verification"] = len(verified_docs)

        # -------------------------------------------------------------
        # Stage 4: Systematic PRISMA 2020 Screening — Agent-in-the-loop
        #
        # The harness itself IS the LLM. No external API required.
        # The pipeline prepares batch files (20 papers each) in literature/screening/.
        # The harness agent reads each batch and writes a decisions file.
        # Run `agent_screen.py collect <workspace>` after agent finishes.
        # -------------------------------------------------------------
        from scholar_harness.agent_screen import cmd_prepare as _prepare_batches

        protocol_data = json.loads(p_path.read_text(encoding="utf-8"))
        _prepare_batches(self.workspace_dir, batch_size=20, force=True)

        screening_dir = lit_dir / "screening"
        total_batches = len(
            [
                f
                for f in screening_dir.glob("batch_*.json")
                if "_decisions" not in f.name
            ]
        )

        (lit_dir / "prisma_screening_report.md").write_text(
            f"# PRISMA Screening \u2014 IN PROGRESS\n\n"
            f"{total_batches} batch files prepared in `literature/screening/`.\n\n"
            f"**Next step**: Ask the agent to screen the batches, then run:\n"
            f"```\npython src/scholar_harness/agent_screen.py collect {self.workspace_dir}\n```\n",
            encoding="utf-8",
        )
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
        extracted_files: list[Path] = []
        metadata_frontmatter_only: list[str] = []
        pymupdf = PyMuPDFEngine()
        for doc_item in inc_docs:
            slug = _extraction_file_stem(doc_item)
            md_path = ext_dir / f"{slug}.md"
            if md_path.exists():
                extracted_files.append(md_path)
                continue

            doi = _study_doi(doc_item)
            metadata = {
                "workspace_id": doc_item.get("workspace_id", ""),
                "doi": doi,
                "title": doc_item.get("title") or "Untitled",
                "authors": doc_item.get("authors", []),
                "year": doc_item.get("year"),
            }

            pdf = _study_pdf(pdf_dir, doc_item)
            if pdf is not None:
                try:
                    extracted_files.append(
                        pymupdf.extract_markdown(pdf, ext_dir, metadata=metadata)
                    )
                    continue
                except Exception as exc:  # pragma: no cover - depends on PyMuPDF
                    logger.warning("PyMuPDF extraction failed for %s: %s", slug, exc)

            # Metadata-frontmatter-only document derived from real records; the
            # abstract is quoted verbatim and no Methodology/Results/Limitations
            # text is invented.
            abstract = doc_item.get("abstract") or "No abstract provided."
            frontmatter = (
                f"---\n"
                f'workspace_id: "{metadata["workspace_id"]}"\n'
                f'doi: "{metadata["doi"]}"\n'
                f"title: {json.dumps(metadata['title'], ensure_ascii=False)}\n"
                f"authors: {json.dumps(metadata['authors'], ensure_ascii=False)}\n"
                f"year: {metadata['year']}\n"
                f'extraction_engine: "metadata"\n'
                f"---\n\n"
            )
            md_path.write_text(
                frontmatter + f"## Abstract\n\n{abstract}\n", encoding="utf-8"
            )
            metadata_frontmatter_only.append(str(md_path))
            extracted_files.append(md_path)

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
        retriever = ScholarRetriever(
            db_path=str(chroma_dir),
            collection_name=indexer.collection_name,
            embedder_kwargs=indexer.embedder_kwargs,
        )
        matrix_extractor = MatrixExtractor(protocol=protocol, retriever=retriever)
        matrix_rows, csv_path, json_path = matrix_extractor.extract_all(
            output_dir=lit_dir
        )
        results["stages"]["matrix_rows"] = {"status": "DONE", "rows": len(matrix_rows)}

        # -------------------------------------------------------------
        # Stage 8: Citation Knowledge Graph & PageRank
        # -------------------------------------------------------------
        from scholar_search.http_client import AcademicHttpClient

        graph_builder = CitationGraphBuilder(
            AcademicHttpClient(name="openalex-graph", rate_limit=10)
        )
        dois = [d for d in (_study_doi(doc_item) for doc_item in inc_docs) if d]
        if dois:
            G = await graph_builder.build_graph(dois)
        else:
            # No DOIs to resolve: seed an empty graph so downstream reads stay valid.
            G = nx.DiGraph()
        CitationGraphBuilder.compute_pagerank(G)
        graph_builder.export_json(G, lit_dir / "knowledge_graph.json")

        vis = GraphVisualizer(str(lit_dir / "knowledge_graph.html"))
        vis.generate_html(G)
        results["stages"]["graph_nodes"] = {
            "status": "DONE",
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),
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
        """Parse the Contract v1 artifact registry through the frozen model.

        The registry is the recorded proof of what was accepted, so it is read with
        the frozen ``ArtifactRegistry`` / ``RegistryEntry`` models rather than
        hand-parsed: a missing or malformed ``sha256``, an unknown key, or a missing
        ``accepted_at`` / ``run_id`` / ``producer`` now makes the *registry*
        unusable instead of being silently coerced to ``""``.

        ``None`` means "nothing may be inherited from the registry": either no
        registry exists yet, or it does not validate. Callers treat that as an
        absence and refuse the affected documents, which is the fail-closed
        direction -- an unparseable registry must not widen what Stage 6 accepts.
        """
        registry_path = self.workspace_dir / "audit" / "artifact_registry.json"
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

    def _accepted_artifact_payload(self, entry: RegistryEntry) -> Any | None:
        """Read one accepted artifact's payload, with typed path containment.

        ``RegistryEntry.path`` is workspace-relative, so it is validated with the
        frozen ``ArtifactReference`` path rule and then re-checked against the
        resolved workspace root. A registry that points outside the workspace is
        refused, not followed.
        """
        try:
            ArtifactReference.portable_workspace_path(entry.path)
        except ValueError:
            logger.warning("registry entry %r has a non-portable path", entry.path)
            return None
        try:
            resolved = (self.workspace_dir / entry.path).resolve()
            resolved.relative_to(self.workspace_dir)
        except (OSError, ValueError):
            logger.warning("registry entry %r escapes the workspace", entry.path)
            return None
        try:
            return json.loads(resolved.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None

    def _accepted_screening_parents(self) -> dict[str, dict[str, str]]:
        """Map each included ``study_id`` to the accepted artifact that bound it.

        Read-only over the Contract v1 artifact registry that
        ``agent_screen.py collect`` publishes. An included study's scientific
        parent is the accepted ``screening_decisions`` artifact carrying its
        INCLUDE decision; the registry entry supplies that artifact's id and
        its accepted payload hash, and the artifact payload supplies the
        decision. Nothing is inferred here: a study with no accepted INCLUDE
        decision is simply absent from the result, and Stage 6 then refuses it
        rather than binding it to something that was never accepted.
        """
        registry = self._load_artifact_registry()
        if registry is None:
            return {}

        parents: dict[str, dict[str, str]] = {}
        for artifact_id, entry in sorted(registry.artifacts.items()):
            if entry.artifact_type != "screening_decisions":
                continue
            payload = self._accepted_artifact_payload(entry)
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

    def _accepted_document_records(self) -> dict[str, dict[str, str]]:
        """Map each accepted ``document_id`` to its recorded identity and path.

        This is where Stage 6's document and study identity are *inherited* rather
        than derived. Both limbs come from a ``DocumentRecord`` inside an accepted
        ``document_manifest`` -- the frozen artifact that records them
        (``contracts/schemas/v1/document-manifest.schema.json``, which requires
        ``document_id``, ``study_id``, ``source_hash``, ``content_status``, and
        ``extraction_method``, and requires an ``extracted_path`` for VALID/PARTIAL
        content). The registry entry supplies the manifest's artifact id and its
        accepted payload hash, so the parent binding is the accepted one.

        A document with no accepted manifest record is simply absent, and Stage 6
        refuses it. Nothing here derives a ``document_id`` from a filename, a
        title, or a DOI, and ``workspace_id`` is never offered as a study: under
        Contract v1 a workspace is not a study, and this method has no access to the
        workspace limb at all.
        """
        registry = self._load_artifact_registry()
        if registry is None:
            return {}

        records: dict[str, dict[str, str]] = {}
        for artifact_id, entry in sorted(registry.artifacts.items()):
            if entry.artifact_type != "document_manifest":
                continue
            payload = self._accepted_artifact_payload(entry)
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

    def recorded_workspace_id(self) -> str:
        """Return the workspace identity recorded in ``project.json``.

        Thin adapter over :func:`workspace.identity.require_recorded_identity`:
        records and re-reads only, never mints, never derives from the slug.
        Preserves the observed non-object ``AttributeError`` (HCM-01 defect (a)).
        """
        from .workspace.identity import require_recorded_identity

        return require_recorded_identity(self.workspace_dir)

    def _build_parent_view(self) -> dict[str, Any] | None:
        """Build the accepted-parent view required by IndexService.

        The parent view is the accepted ``document_manifest`` artifact, which carries
        the document records (document_id, study_id, extracted_path,
        extracted_content_sha256) and the parent screening decision reference.
        This is read from the Contract v1 artifact registry, not derived.
        """
        registry = self._load_artifact_registry()
        if registry is None:
            return None

        # Find the accepted document_manifest in this generation
        manifests = {}
        for artifact_id, entry in registry.artifacts.items():
            if entry.artifact_type != "document_manifest":
                continue
            payload = self._accepted_artifact_payload(entry)
            if payload is None:
                continue
            try:
                manifest = DocumentManifestArtifact.model_validate(payload)
            except ValueError:
                continue
            # Check generation match via workspace_id, protocol_fingerprint, corpus_fingerprint
            ws_id = self.recorded_workspace_id()
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
            md_path = (self.workspace_dir / extracted) if extracted else None
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
        """Construct the IndexServiceRequest from recorded workspace state.

        Every field is explicit; nothing is inferred or defaulted.
        """
        workspace_id = self.recorded_workspace_id()
        docs_path = self.workspace_dir / "extracted"

        # Gather accepted document records
        documents = self._accepted_document_records()
        parents = self._accepted_screening_parents()

        sources: list[IndexedSource] = []
        for document_id, record in sorted(documents.items()):
            study_id = record["study_id"].strip()
            if not study_id:
                continue
            extracted = record["extracted_path"]
            md_path = (self.workspace_dir / extracted) if extracted else None
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
        embedder = get_embedder(provider="sentence-transformers")
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

    def _run_indexing_stage(self, chroma_dir: Path) -> tuple[dict[str, Any], Any]:
        """Stage 6: index accepted documents via typed IndexService.

        This replaces the legacy ScholarIndexer.index_markdown upsert path with the
        typed E3 IndexService.index_workspace, enforcing the seven acceptance checks:
        parent_view gate, manifest exists, chunk identity matches, replacement intent
        valid, backend verified, audit event published, index record accepted.

        Fail-closed: no partial replacement, no success event if any check fails.
        """
        # Validate workspace identity BEFORE any store exists
        workspace_id = self.recorded_workspace_id()

        # Build parent_view from accepted document_manifest
        parent_view = self._build_parent_view()
        if parent_view is not None:
            from scholar_harness.extraction_producer import (
                PublicationRefused,
                validate_extraction_currentness,
            )

            try:
                validate_extraction_currentness(
                    self.workspace_dir, parent_view["artifact_id"]
                )
            except PublicationRefused as exc:
                self._log_audit_event(
                    action="RAG_INDEX_REJECTED",
                    agent="scholar-harness",
                    description="Stage 6 refused stale extraction provenance",
                    status="FAILED",
                    inputs=[str(parent_view["artifact_id"])],
                    outputs=[],
                    parameters={"code": exc.code},
                    metrics={"documents": 0},
                )
                return {"status": "FAILED", "code": exc.code, "documents": 0}, None
        if parent_view is None:
            # No accepted manifest -> refuse before touching any backend
            self._log_audit_event(
                action="RAG_INDEX_REJECTED",
                agent="scholar-harness",
                description="Stage 6 refused: no accepted document_manifest in this generation",
                status="FAILED",
                inputs=[str(self.workspace_dir / "audit" / "artifact_registry.json")],
                outputs=[],
                metrics={
                    "indexed_files": 0,
                    "total_chunks": 0,
                    "refused_documents": 0,
                    "rejection_code": "DOCUMENT_MANIFEST_NOT_ACCEPTED",
                },
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

            return {
                "status": "FAILED",
                "indexed_files": 0,
                "total_chunks": 0,
                "collection_count": None,
                "documents": [],
                "refused": [
                    {"document_id": "", "reason": "no accepted document_manifest"}
                ],
            }, MinimalIndexer()

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

        # Build the IndexServiceRequest
        request = self._build_index_service_request(
            chroma_dir=chroma_dir,
            parent_view=parent_view,
            run_id=run_id,
            created_at=created_at,
            producer_commit=producer_commit,
            producer_version=producer_version,
        )

        # Early refusal: no documents to index (all skipped during request building)
        if request is None:
            self._log_audit_event(
                action="RAG_INDEX_REJECTED",
                agent="scholar-harness",
                description="Stage 6 refused: no accepted documents have extractable content for indexing",
                status="FAILED",
                inputs=[str(self.workspace_dir / "audit" / "artifact_registry.json")],
                outputs=[],
                metrics={
                    "indexed_files": 0,
                    "total_chunks": 0,
                    "refused_documents": 0,
                    "rejection_code": "NO_DOCUMENTS_TO_INDEX",
                },
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

            return {
                "status": "FAILED",
                "indexed_files": 0,
                "total_chunks": 0,
                "collection_count": None,
                "documents": [],
                "refused": [{"document_id": "", "code": "NO_DOCUMENTS_TO_INDEX"}],
            }, MinimalIndexer()

        # Ensure journal directory exists
        journal_path = self.workspace_dir / "run-reports"
        journal_path.mkdir(parents=True, exist_ok=True)

        # Prepare backends and embedder
        embedder = get_embedder(provider="sentence-transformers")
        backend = ChromaReplacementView(
            db_path=str(chroma_dir), collection_name="scholar_docs", embedder=embedder
        )
        reader = ChromaVisibleSetReader(
            db_path=str(chroma_dir), collection_name="scholar_docs"
        )

        # Call IndexService
        result = index_workspace(
            request=request,
            backend=backend,
            reader=reader,
            embedder=embedder,
            workspace_root=self.workspace_dir,
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

        # Populate indexed documents from sources
        indexed_docs = []
        screening_parents = self._accepted_screening_parents()
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

                _sidecar_abs = self.workspace_dir / str(_sidecar_rel)
                if _sidecar_abs.is_file():
                    _candidate = json.loads(_sidecar_abs.read_text(encoding="utf-8"))
                    _decision = accept_index_candidate(
                        self.workspace_dir,
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

                        return _failed, MinimalIndexer()
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

                    return index_res, MinimalIndexer()
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

                return {
                    "status": "FAILED",
                    "indexed_files": 0,
                    "total_chunks": 0,
                    "collection_count": None,
                    "documents": [],
                    "refused": [{"document_id": "", "code": _fault_code}],
                }, MinimalIndexer()

        # Log audit event (the IndexService already journals its run report)
        # We also log the harness-level RAG_INDEX_BUILT for continuity
        self._log_audit_event(
            action="RAG_INDEX_BUILT",
            agent="scholar-harness",
            description=(
                f"Indexed {index_res['indexed_files']} accepted document(s) via IndexService; "
                f"{len(index_res['refused'])} refused"
            ),
            status=index_res["status"],
            inputs=[str(self.workspace_dir / "audit" / "artifact_registry.json")],
            outputs=[str(chroma_dir)],
            metrics={
                "indexed_files": index_res["indexed_files"],
                "total_chunks": index_res["total_chunks"],
                "refused_documents": len(index_res["refused"]),
            },
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

        return index_res, MinimalIndexer()

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
