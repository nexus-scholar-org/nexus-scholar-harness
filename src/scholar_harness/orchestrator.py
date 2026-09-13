"""Research Pipeline Orchestrator."""

from __future__ import annotations

import asyncio
import importlib.util
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
from scholar_rag.indexer import ScholarIndexer
from scholar_rag.matrix import MatrixExtractor
from scholar_rag.retriever import ScholarRetriever
from scholar_rag.synthesis import GroundedSynthesisEngine
from scholar_search.dedup import Deduplicator
from scholar_search.engine import SearchEngine
from scholar_search.protocol_adapter import compile_protocol_search
from scholar_search.providers import (
    ArxivProvider,
    BaseAPIProvider,
    BiorxivProvider,
    CrossrefProvider,
    OpenAlexProvider,
    PubMedProvider,
    SearchProvider,
    SemanticScholarProvider,
)
from scholar_search.verifier import DocumentVerifier

_PROVIDER_MAP: dict[str, type[SearchProvider]] = {
    "openalex": OpenAlexProvider,
    "semanticscholar": SemanticScholarProvider,
    "semantic_scholar": SemanticScholarProvider,
    "crossref": CrossrefProvider,
    "arxiv": ArxivProvider,
    "pubmed": PubMedProvider,
    "biorxiv": BiorxivProvider,
}


def _resolve_providers(providers: list[Any] | None) -> list[SearchProvider] | None:
    """Resolve provider instances from names (strings) or existing instances."""
    if not providers:
        return None
    instances: list[SearchProvider] = []
    for p in providers:
        if isinstance(p, str):
            key = p.lower().strip().replace("-", "_").replace(" ", "_")
            cls = _PROVIDER_MAP.get(key)
            if cls:
                instances.append(cls())
            else:
                logger.warning("Unknown search provider: %s", p)
        elif isinstance(p, BaseAPIProvider) or hasattr(p, "search"):
            instances.append(p)
        else:
            logger.warning("Unexpected provider item: %r", p)
    return instances if instances else None

logger = logging.getLogger(__name__)


def _study_doi(doc_item: dict[str, Any]) -> str:
    return (doc_item.get("external_ids") or {}).get("doi") or doc_item.get("doi") or ""


def _study_slug(doc_item: dict[str, Any]) -> str:
    idv = doc_item.get("workspace_id") or doc_item.get("study_id") or ""
    doi = _study_doi(doc_item)
    return (idv or doi or "doc").replace("/", "_").replace(":", "_")


def _study_pdf(pdf_dir: Path, doc_item: dict[str, Any]) -> Path | None:
    """Locate a harvested PDF for a study, preferring deterministic slugs."""
    doi = _study_doi(doc_item)
    slug = _study_slug(doc_item)
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
                protocol = ResearchProtocol.model_validate_json(proto_file.read_text(encoding="utf-8"))
                status["protocol_found"] = True
                status["title"] = protocol.metadata.get("title", "Unknown") if isinstance(protocol.metadata, dict) else getattr(protocol.metadata, "title", "Unknown")
                status["playbook_type"] = protocol.playbook_type.value
                status["phase"] = "PHASE_1_DISCOVERY"
            except Exception as e:
                logger.warning(f"Failed to parse protocol.json: {e}")

        # 2. Literature Files
        lit_dir = self.workspace_dir / "literature"
        if (lit_dir / "raw_search.json").exists():
            try:
                raw_docs = json.loads((lit_dir / "raw_search.json").read_text(encoding="utf-8"))
                status["discovered_count"] = len(raw_docs)
            except Exception:
                pass

        if (lit_dir / "deduped.json").exists():
            try:
                dedup_docs = json.loads((lit_dir / "deduped.json").read_text(encoding="utf-8"))
                status["deduped_count"] = len(dedup_docs)
            except Exception:
                pass

        if (lit_dir / "verified.json").exists():
            try:
                ver_docs = json.loads((lit_dir / "verified.json").read_text(encoding="utf-8"))
                status["verified_count"] = len(ver_docs)
            except Exception:
                pass

        if (lit_dir / "included.json").exists():
            try:
                inc_docs = json.loads((lit_dir / "included.json").read_text(encoding="utf-8"))
                status["included_count"] = len(inc_docs)
                status["phase"] = "PHASE_1_HARVESTING"
            except Exception:
                pass

        if (lit_dir / "excluded.json").exists():
            try:
                exc_docs = json.loads((lit_dir / "excluded.json").read_text(encoding="utf-8"))
                status["excluded_count"] = len(exc_docs)
            except Exception:
                pass

        if (lit_dir / "knowledge_graph.json").exists() or (lit_dir / "graph.json").exists():
            g_file = lit_dir / "knowledge_graph.json" if (lit_dir / "knowledge_graph.json").exists() else lit_dir / "graph.json"
            try:
                g_data = json.loads(g_file.read_text(encoding="utf-8"))
                status["graph_nodes"] = len(g_data.get("nodes", []))
            except Exception:
                pass

        if (lit_dir / "synthesis_matrix.json").exists():
            try:
                m_data = json.loads((lit_dir / "synthesis_matrix.json").read_text(encoding="utf-8"))
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
            if len(content) > 50 and "To be generated from extracted papers" not in content:
                status["synthesis_generated"] = True
                if status["matrix_rows"] > 0 and status["vector_chunks"] > 0:
                    status["phase"] = "PHASE_3_COMPLETE"

        # 6. Audit Journal Events
        journal_file = self.workspace_dir / "audit" / "journal.jsonl"
        if journal_file.exists():
            try:
                events = []
                for line in journal_file.read_text(encoding="utf-8").strip().split("\n"):
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
                for key in ("total_identified", "records_screened", "records_included",
                            "records_included_confirmed", "records_included_provisional_caveats",
                            "records_excluded", "conflicts_flagged", "reports_sought_for_retrieval",
                            "reports_not_retrieved", "reports_retrieved", "retrieval_rate_pct",
                            "final_fulltext_corpus_assessed"):
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
        graph_file = lit / "knowledge_graph.json" if (lit / "knowledge_graph.json").exists() else lit / "graph.json"
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
                stats["audited_clean_corpus"] = len(json.loads(clean_ids.read_text(encoding="utf-8")))
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
            inputs=[str(p) for p in (lit / "raw_search.json", lit / "prisma_report.json") if p.exists()],
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

        project.json is written atomically (temp + os.replace) by sync_state; the
        INDEX.md renderer writes in place, so we snapshot the previous file first
        and restore it if the render raises or leaves an empty result. This keeps
        sync_state failure-safe without re-implementing the catalog renderer.
        """
        scripts_dir = (
            Path(__file__).resolve().parent.parent.parent
            / ".agents" / "skills" / "workspace-manager" / "scripts"
        )
        module_path = scripts_dir / "log_event.py"
        if not module_path.exists():
            return False
        try:
            spec = importlib.util.spec_from_file_location("_wm_log_event", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            index_path = self.workspace_dir / "INDEX.md"
            backup = None
            if index_path.exists():
                backup = index_path.read_text(encoding="utf-8")

            module.refresh_index_md(self.workspace_dir)

            rendered = index_path.read_text(encoding="utf-8")
            if not rendered.strip() or ("Project Index" not in rendered):
                if backup is not None:
                    index_path.write_text(backup, encoding="utf-8")
                return False
            return True
        except Exception:
            return False

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

        protocol = ResearchProtocol.model_validate_json(p_path.read_text(encoding="utf-8"))
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
        query, providers = compile_protocol_search(p_path)
        if max_search_results:
            query.max_results = max_search_results

        engine = SearchEngine(providers=_resolve_providers(providers))
        discovered_docs = await engine.search_all(query, dedup=False)
        await engine.close()

        # Save both combined raw and first-provider raw for reference
        (lit_dir / "all_raw_search.json").write_text(
            json.dumps([asdict(d) if hasattr(d, "__dataclass_fields__") else d for d in discovered_docs], indent=2, default=str),
            encoding="utf-8"
        )
        (lit_dir / "raw_search.json").write_text(
            json.dumps([asdict(d) if hasattr(d, "__dataclass_fields__") else d for d in discovered_docs], indent=2, default=str),
            encoding="utf-8"
        )
        results["stages"]["discovery"] = len(discovered_docs)

        # -------------------------------------------------------------
        # Stage 2: 2-Tier Deduplication & PID Cluster Assignment
        # Bug fix: Dedup now runs on ALL discovered_docs combined (not a subset).
        # workspace_ids (SCI-XXXXXX) are assigned by the Deduplicator here.
        # -------------------------------------------------------------
        deduplicator = Deduplicator()
        clusters = deduplicator.deduplicate(discovered_docs)
        unique_docs = [c.representative for c in clusters]
        dupes_removed = len(discovered_docs) - len(unique_docs)

        (lit_dir / "deduped.json").write_text(
            json.dumps([asdict(d) if hasattr(d, "__dataclass_fields__") else d for d in unique_docs], indent=2, default=str),
            encoding="utf-8"
        )
        results["stages"]["deduplication"] = {"unique": len(unique_docs), "duplicates_removed": dupes_removed}

        # -------------------------------------------------------------
        # Stage 3: Verification & Abstract Hydration
        # Bug fix: After verification, copy workspace_ids back from deduped docs
        # because verify_document() may return a freshly normalized Document that
        # loses the workspace_id set by the Deduplicator.
        # -------------------------------------------------------------
        verifier = DocumentVerifier()
        verified_docs, audit = await verifier.process_batch(unique_docs, verify=True, enrich=True)

        # Restore workspace_ids on verified docs using DOI as bridge
        wsid_by_doi: dict[str, str] = {
            d.external_ids.doi: d.workspace_id
            for d in unique_docs
            if d.external_ids.doi and d.workspace_id
        }
        for vd in verified_docs:
            if not vd.workspace_id and vd.external_ids.doi:
                vd.workspace_id = wsid_by_doi.get(vd.external_ids.doi)
            if not vd.workspace_id:
                # Last resort: assign a temporary sequential ID
                vd.workspace_id = f"SCI-{verified_docs.index(vd)+1:06d}"

        (lit_dir / "verified.json").write_text(
            json.dumps([asdict(d) if hasattr(d, "__dataclass_fields__") else d for d in verified_docs], indent=2, default=str),
            encoding="utf-8"
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
        total_batches = len([f for f in screening_dir.glob("batch_*.json") if "_decisions" not in f.name])

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
            slug = _study_slug(doc_item)
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
                    extracted_files.append(pymupdf.extract_markdown(pdf, ext_dir, metadata=metadata))
                    continue
                except Exception as exc:  # pragma: no cover - depends on PyMuPDF
                    logger.warning("PyMuPDF extraction failed for %s: %s", slug, exc)

            # Metadata-frontmatter-only document derived from real records; the
            # abstract is quoted verbatim and no Methodology/Results/Limitations
            # text is invented.
            abstract = doc_item.get("abstract") or "No abstract provided."
            frontmatter = (
                f"---\n"
                f"workspace_id: \"{metadata['workspace_id']}\"\n"
                f"doi: \"{metadata['doi']}\"\n"
                f"title: {json.dumps(metadata['title'], ensure_ascii=False)}\n"
                f"authors: {json.dumps(metadata['authors'], ensure_ascii=False)}\n"
                f"year: {metadata['year']}\n"
                f"extraction_engine: \"metadata\"\n"
                f"---\n\n"
            )
            md_path.write_text(frontmatter + f"## Abstract\n\n{abstract}\n", encoding="utf-8")
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
        indexer = ScholarIndexer(db_path=str(chroma_dir))
        index_res = indexer.index_directory(docs_dir=ext_dir, workspace_id=protocol.project_slug)
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
        matrix_rows, csv_path, json_path = matrix_extractor.extract_all(output_dir=lit_dir)
        results["stages"]["matrix_rows"] = {"status": "DONE", "rows": len(matrix_rows)}

        # -------------------------------------------------------------
        # Stage 8: Citation Knowledge Graph & PageRank
        # -------------------------------------------------------------
        from scholar_search.http_client import AcademicHttpClient

        graph_builder = CitationGraphBuilder(AcademicHttpClient(name="openalex-graph", rate_limit=10))
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
        results["stages"]["graph_nodes"] = {"status": "DONE", "nodes": G.number_of_nodes(), "edges": G.number_of_edges()}

        # -------------------------------------------------------------
        # Stage 9: Grounded Evidence Synthesis & Entailment
        # -------------------------------------------------------------
        engine = GroundedSynthesisEngine(retriever=retriever)
        first_rq = protocol.research_questions[0] if protocol.research_questions else None
        rq_text = first_rq.text if first_rq else "What are the primary empirical findings?"
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
            outputs=[str(synth_file), str(lit_dir / "synthesis_matrix.csv"), str(lit_dir / "knowledge_graph.html")],
            metrics=results["stages"]
        )

        return results

    def run_pipeline(self, protocol_path: Path | str | None = None, max_search_results: int | None = None) -> dict[str, Any]:
        """Synchronous wrapper for run_pipeline_async."""
        return asyncio.run(self.run_pipeline_async(protocol_path=protocol_path, max_search_results=max_search_results))

    def _log_audit_event(
        self,
        action: str,
        agent: str,
        description: str,
        inputs: list[str],
        outputs: list[str],
        metrics: dict[str, Any]
    ) -> None:
        """Appends an event to audit/journal.jsonl."""
        audit_file = self.workspace_dir / "audit" / "journal.jsonl"
        audit_file.parent.mkdir(parents=True, exist_ok=True)

        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_id": f"EVT-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{hex(hash(action + description))[-6:]}",
            "action": action,
            "agent_or_tool": agent,
            "description": description,
            "parameters": {},
            "inputs": inputs,
            "outputs": outputs,
            "metrics": metrics,
            "status": "SUCCESS"
        }

        with open(audit_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
