"""End-to-End Integration Test for Phase 2 Pipeline.

Validates the full Phase 2 pipeline:
  Extracted Markdown (from Phase 1) -> Structural AST Chunking & Vector Indexing ->
  Citation & Concept Knowledge Graph -> Hybrid Graph-Boosted Retrieval ->
  Dynamic Protocol Extraction Matrix -> Grounded Synthesis & Claim Entailment -> Audit Ledger
"""

import json
from pathlib import Path
import networkx as nx
import pytest

from scholar_graph.builder import CitationGraphBuilder
from scholar_protocol.compiler import compile_protocol
from scholar_protocol.intent import (
    ConceptClusterIntent,
    CriterionIntent,
    IntentPacket,
    MatrixDimensionIntent,
    RQIntent,
)
from scholar_protocol.models import PlaybookType
from scholar_rag.chunker import MarkdownChunker, text_fingerprint
from scholar_rag.index_models import IndexDocumentRequest
from scholar_rag.indexer import ScholarIndexer
from scholar_rag.matrix import MatrixExtractor
from scholar_rag.retriever import ScholarRetriever
from scholar_rag.synthesis import GroundedSynthesisEngine


def test_phase2_full_pipeline_e2e(tmp_path: Path):
    # -------------------------------------------------------------
    # 1. Setup Workspace & Protocol
    # -------------------------------------------------------------
    workspace_dir = tmp_path / "workspace"
    audit_dir = workspace_dir / "audit"
    papers_dir = workspace_dir / "papers" / "extracted"
    lit_dir = workspace_dir / "literature"
    db_path = str(workspace_dir / "chroma_db")

    papers_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    lit_dir.mkdir(parents=True, exist_ok=True)

    intent = IntentPacket(
        protocol_id="proto-20260901-rag-synthesis",
        genesis_timestamp="2026-09-01T00:00:00+00:00",
        project_slug="code-gen-synthesis",
        playbook_type=PlaybookType.DESIGN_SCIENCE,
        title="Grounded Synthesis of AI Code Generation Benchmarks",
        lead_researcher="Alex Chen",
        unit_of_analysis="Code generation benchmark frameworks",
        epistemological_rationale="Empirical benchmark performance evaluation.",
        research_questions=[
            RQIntent(
                text="What are the primary pass@1 benchmark results across synthesized models?",
                target_facet="evaluation_metrics",
                required_evidence_type="Quantitative Benchmark",
            )
        ],
        core_concepts=[
            ConceptClusterIntent(
                concept="Code Synthesis",
                synonyms=["neural program synthesis"],
            )
        ],
        inclusion_criteria=[
            CriterionIntent(
                criterion="Empirical benchmark study",
                maps_to_rqs=["RQ1"],
            )
        ],
        exclusion_criteria=[
            CriterionIntent(
                criterion="Opinion or non-empirical editorial",
                reason_category="METHODOLOGY",
                maps_to_rqs=["RQ1"],
            )
        ],
        matrix_dimensions=[
            MatrixDimensionIntent(
                id="sample_size",
                name="Sample Size",
                description="Number of benchmark tasks or challenges evaluated",
                target_section_category="methodology",
            ),
            MatrixDimensionIntent(
                id="primary_results",
                name="Primary Results",
                description="Reported pass@k or accuracy metrics",
                target_section_category="results_empirical",
            ),
        ],
    )

    protocol = compile_protocol(intent)
    proto_path = workspace_dir / "protocol.json"
    proto_path.write_text(json.dumps(protocol.model_dump(), indent=2), encoding="utf-8")

    # -------------------------------------------------------------
    # 2. Phase 1 Extracted Markdown Files (with YAML Frontmatter)
    # -------------------------------------------------------------
    paper1_md = """---
workspace_id: SCI-000001
doi: 10.1038/s41586-024-0001
title: Neural Code Synthesis with Grounded LLMs
authors: Chen et al.
year: 2024
---
# Neural Code Synthesis with Grounded LLMs

## Abstract
We present an empirical study of neural code generation architectures.

## Methodology
We evaluate models on HumanEval-X containing 500 programming challenges.

## Empirical Results
Achieved 72.4% pass@1 on synthetic code generation benchmarks.

## Discussion and Limitations
Performance degrades on recursive dynamic programming tasks.
"""

    paper2_md = """---
workspace_id: SCI-000002
doi: 10.1038/s41586-024-0002
title: Multi-Language Benchmark Evaluation for Code Models
authors: Smith et al.
year: 2024
---
# Multi-Language Benchmark Evaluation for Code Models

## Abstract
Cross-language comparison of synthesis performance across 10 programming languages.

## Methodology
Evaluation was conducted on MultiPL-E across 1000 tasks per language.

## Empirical Results
Multi-turn reinforcement fine-tuning yields a 15% relative improvement in execution accuracy.

## Discussion and Limitations
Computational cost of beam search during inference remains significant.
"""

    # One directory per document: the six chunk-identity limbs describe a single
    # document, so a request is built per document and the run is scoped to that
    # document's own directory rather than sharing one request across the corpus.
    p1_doc_id = "2024_chen_neural_code_synthesis"
    p2_doc_id = "2024_smith_multilanguage_benchmark"
    for doc_id, body in ((p1_doc_id, paper1_md), (p2_doc_id, paper2_md)):
        doc_dir = papers_dir / doc_id
        doc_dir.mkdir(parents=True, exist_ok=True)
        (doc_dir / f"{doc_id}.md").write_text(body, encoding="utf-8")

    # -------------------------------------------------------------
    # 3. Phase 2 Cycle A & B: Structural Chunking & ChromaDB Indexing
    # -------------------------------------------------------------
    indexer = ScholarIndexer(
        db_path=db_path,
        collection_name="scholar_docs",
        embedder_kwargs={"provider": "mock"},
    )

    # Explicit identity per document, constructed exactly as the orchestrator
    # constructs it at Stage 6: every limb is stated, none is read back out of a
    # filename, a title, a DOI, or the working directory.
    accepted_parent_sha = "sha256:" + "1" * 64
    documents = (
        (p1_doc_id, "SCI-000001", paper1_md, "code-gen-synthesis"),
        (p2_doc_id, "SCI-000002", paper2_md, "code-gen-synthesis"),
    )

    indexed_files = 0
    total_chunks = 0
    for doc_id, study_id, body, workspace_id in documents:
        request = IndexDocumentRequest(
            workspace_id=workspace_id,
            study_id=study_id,
            document_id=doc_id,
            parent_artifact_id="ART-" + "1" * 32,
            parent_artifact_sha256=accepted_parent_sha,
            extracted_content_sha256=text_fingerprint(body),
            backend_provider=indexer.embedder_kwargs["provider"],
            collection=indexer.collection_name,
        )
        index_result = indexer.index_directory(
            docs_dir=papers_dir / doc_id,
            request=request,
            log_journal=True,
        )
        indexed_files += index_result["indexed_files"]
        total_chunks += index_result["total_chunks"]

    assert indexed_files == 2
    assert total_chunks >= 8
    assert indexer.get_collection_count() >= 8

    # Verify chunk structure and metadata fidelity. Only workspace_id is surfaced as
    # a metadata field; the other five limbs are bound into chunk_id, so they are
    # asserted there. Under E3 a workspace is not a study, so the workspace limb
    # now carries the project namespace and the study identity is no longer
    # smuggled in as a workspace id.
    chunker = MarkdownChunker()

    def _p1_request(**overrides) -> IndexDocumentRequest:
        fields = {
            "workspace_id": "code-gen-synthesis",
            "study_id": "SCI-000001",
            "document_id": p1_doc_id,
            "parent_artifact_id": "ART-" + "1" * 32,
            "parent_artifact_sha256": accepted_parent_sha,
            "extracted_content_sha256": text_fingerprint(paper1_md),
            "backend_provider": indexer.embedder_kwargs["provider"],
            "collection": indexer.collection_name,
        }
        fields.update(overrides)
        return IndexDocumentRequest(**fields)

    p1_identity = _p1_request()
    chunks_p1 = chunker.chunk_markdown(
        paper1_md, base_metadata=p1_identity.to_base_metadata()
    )
    assert any(c.metadata.section_category == "methodology" for c in chunks_p1)
    assert any(c.metadata.section_category == "results_empirical" for c in chunks_p1)
    assert any(c.metadata.workspace_id == "code-gen-synthesis" for c in chunks_p1)

    # The stated identity is load-bearing: reproducing it reproduces the chunk ids
    # exactly, and rebinding any one limb changes them.
    again = chunker.chunk_markdown(
        paper1_md, base_metadata=_p1_request().to_base_metadata()
    )
    assert [c.chunk_id for c in again] == [c.chunk_id for c in chunks_p1]
    for limb in ("study_id", "document_id", "parent_artifact_sha256"):
        rebound = chunker.chunk_markdown(
            paper1_md,
            base_metadata=_p1_request(**{limb: "0" * 32}).to_base_metadata(),
        )
        assert [c.chunk_id for c in rebound] != [c.chunk_id for c in chunks_p1], limb

    # -------------------------------------------------------------
    # 4. Phase 2 Cycle D: Citation & Concept Knowledge Graph
    # -------------------------------------------------------------
    G = nx.DiGraph()
    G.add_node(
        "10.1038/s41586-024-0001",
        title="Neural Code Synthesis with Grounded LLMs",
        year=2024,
        citations=45,
    )
    G.add_node(
        "10.1038/s41586-024-0002",
        title="Multi-Language Benchmark Evaluation for Code Models",
        year=2024,
        citations=30,
    )
    # Paper 1 cites Paper 2
    G.add_edge("10.1038/s41586-024-0001", "10.1038/s41586-024-0002")

    pr_scores = CitationGraphBuilder.compute_pagerank(G)
    assert "10.1038/s41586-024-0001" in pr_scores
    assert "10.1038/s41586-024-0002" in pr_scores
    # Cited node has equal or higher PageRank
    assert pr_scores["10.1038/s41586-024-0002"] >= pr_scores["10.1038/s41586-024-0001"]

    graph_json = lit_dir / "knowledge_graph.json"
    CitationGraphBuilder.export_json(G, graph_json)
    assert graph_json.exists()

    # -------------------------------------------------------------
    # 5. Phase 2 Cycle A & B: Hybrid Graph-Boosted Retrieval
    # -------------------------------------------------------------
    retriever = ScholarRetriever(
        db_path=db_path,
        collection_name="scholar_docs",
        embedder_kwargs={"provider": "mock"},
    )

    query_results = retriever.query(
        query_text="pass@1 benchmark performance",
        n_results=5,
        section_category="results_empirical",
        graph_source=graph_json,
        alpha=0.25,
    )

    assert len(query_results) >= 1
    top_result = query_results[0]
    assert top_result.citation_token.startswith("[")
    assert top_result.citation_token.endswith("]")
    assert top_result.hybrid_score > 0

    # -------------------------------------------------------------
    # 6. Phase 2 Cycle C: Dynamic Protocol Synthesis Matrix Extraction
    # -------------------------------------------------------------
    matrix_extractor = MatrixExtractor(
        protocol=proto_path,
        db_path=db_path,
        collection_name="scholar_docs",
        embedder_kwargs={"provider": "mock"},
    )

    rows, csv_path, json_path = matrix_extractor.extract_all(output_dir=lit_dir)
    assert len(rows) == 2
    assert csv_path.exists()
    assert json_path.exists()
    assert (lit_dir / "synthesis_matrix.md").exists()

    # Validate extracted dimension fields
    p1_row = next(r for r in rows if r["study_id"] == "SCI-000001")
    assert p1_row["study_id"] == "SCI-000001"
    assert "Neural Code Synthesis" in p1_row["title"]
    assert "sample_size" in p1_row
    assert "primary_results" in p1_row

    # -------------------------------------------------------------
    # 7. Phase 2 Cycle E: Grounded Synthesis & Entailment Verification
    # -------------------------------------------------------------
    synthesis_engine = GroundedSynthesisEngine(
        retriever=retriever,
        embedder_kwargs={"provider": "mock"},
    )

    synthesis_res = synthesis_engine.synthesize(
        query="What pass@1 rates and benchmark tasks are reported for synthetic code generation?",
        rq_id="RQ1",
        n_chunks=4,
    )

    assert synthesis_res.rq_id == "RQ1"
    assert synthesis_res.retrieved_chunks_count > 0
    assert len(synthesis_res.synthesis_markdown) > 50
    assert len(synthesis_res.claims) > 0
    assert synthesis_res.entailment_rate >= 0.0

    # Save synthesis document
    synth_file = lit_dir / "literature_review.md"
    synth_file.write_text(synthesis_res.synthesis_markdown, encoding="utf-8")
    assert synth_file.exists()

    # -------------------------------------------------------------
    # 8. Audit Ledger Verification
    # -------------------------------------------------------------
    journal_file = audit_dir / "journal.jsonl"
    assert journal_file.exists()
    journal_lines = [
        json.loads(line)
        for line in journal_file.read_text(encoding="utf-8").strip().split("\n")
    ]
    actions = [j.get("action") for j in journal_lines]

    assert "RAG_INDEX_BUILT" in actions
    assert "MATRIX_EXTRACTED" in actions
    assert "SYNTHESIS_GENERATED" in actions
