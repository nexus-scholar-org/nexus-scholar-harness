"""Pipeline coordinator (HCM-04l neutral extraction).

Owns the ``run_pipeline_async`` orchestration glue moved verbatim from
``ResearchOrchestrator.run_pipeline_async`` (:510-780) so the orchestrator
delegates without behavior change. All 9 stages were already neutral
(HCM-04b..04k); this moves only the glue: protocol load/validate, directory
setup, Stage 1-9 delegation in order, the Stage-4 collect-gate + PAUSE audit,
the Stage-10 COMPLETED audit, status propagation, and no-fabrication
returns.

Preservation notes:

- Mechanical parameterization only: ``self.workspace_dir`` to
  ``workspace_dir``; ``self._run_indexing_stage`` to the explicit
  ``indexing_fn`` collaborator; ``self._log_audit_event`` to direct
  ``workspace.audit.append_legacy_event`` with identical args/order (same
  bytes as the adapter: same action, agent, description, inputs, outputs,
  metrics passthrough, and observed ``SUCCESS`` outcome).
- ``mock_mode`` stays accepted-but-unused (signature parity with the base;
  ``test_discovery_stage.py:358`` proves identical outcomes either way).
- Stage order and early-pause return preserved: discovery, deduplication,
  hydration, verification, screening preparation, then the
  ``included.json`` collect-gate (Stages 5-9 SKIPPED + ``PENDING`` +
  PAUSE audit + return before Stages 5-9), then extraction, indexing,
  matrix, graph, synthesis, then the COMPLETED audit.
- Results shape preserved: ``discovery`` count, ``deduplication``
  unique/dupes, ``verification`` status/counts (+ quarantine), ``screening``
  PENDING mapping with ``len(verified_docs)`` papers_to_screen, pause
  SKIPPED mappings (``extraction``/``indexing``/``matrix``/``graph``/
  ``synthesis``), success ``extraction`` DONE, ``indexing`` via the
  collaborator, ``matrix_rows`` DONE, ``graph_nodes`` DONE, ``synthesis``
  counts, plus the ``SUCCESS``/``PENDING_AGENT_REVIEW`` status propagation.
  The pause/success key asymmetry (``matrix`` vs ``matrix_rows``,
  ``graph`` vs ``graph_nodes``) is preserved verbatim.
- Bindings flow via coordinator locals: Stage-6 ``indexer`` to Stage 7,
  Stage-7 ``retriever`` to Stage 9, Stage-3 ``verified_docs`` length to
  Stage-4 ``papers_to_screen``. The in-memory ``ResearchProtocol`` is
  passed through to Stages 7/9 untouched (no re-parse).
- File/protocol DSL unchanged: missing protocol raises
  ``FileNotFoundError``; invalid protocol propagates the kit validation
  error; no fabrication on any path.
- Function-level import preserved: the base resolved
  ``run_screening_preparation`` with a function-level
  ``from scholar_harness.pipeline.screening_prepare import ...`` so the
  binding happens at call time. This coordinator keeps that call-time
  resolution at the same position (no module-top binding for that name).
  All other stages are module-top imports (as the base orchestrator did);
  that direction is safe: stages never import this coordinator at top
  (their orchestrator-namespace seams are lazy ``__dict__`` reads inside
  functions), and this coordinator never imports the orchestrator.
- Indexing DI decision (packet open question): the coordinator takes a
  REQUIRED keyword-only ``indexing_fn`` collaborator
  (``Callable[[Path], tuple[dict, Any]]``) and calls it as
  ``indexing_fn(chroma_dir)``. The orchestrator passes its bound
  ``self._run_indexing_stage`` (which stays untouched: E3/e2e call
  ``orch._run_indexing_stage`` directly, and its kit/data seams keep
  working through the orchestrator thin delegate). No default is offered:
  a ``None`` default would surprise (a missing collaborator must be a
  ``TypeError``, never a silent skip or an orchestrator import). This
  mirrors the HCM-04h stage-level explicit DI and keeps the coordinator
  neutral (no orchestrator import, no cycle).
- Audit neutrality: this coordinator calls ``append_legacy_event``
  directly (same bytes as the orchestrator adapter) and emits no other
  events; stage-owned audits (hydration, verification, indexing) stay in
  their stages. No new events, no rewording.
- Error propagation unchanged: a stage raise propagates with no
  fabricated mapping and no success claim; an audit raise propagates
  after the files the stage wrote.

Neutrality: stdlib plus ``scholar-protocol-kit`` only for the protocol
validation shape and harness stages only for delegation -- no console
transport, no Contract v1 acceptance beyond what the stages themselves
publish, no workspace audit beyond the two coordinator-owned legacy rows
(PAUSE + COMPLETED), no direct scholar-search/rag/pdf/graph kit imports.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from scholar_protocol.models import ResearchProtocol

from scholar_harness.workspace.audit import append_legacy_event

from .deduplication import run_deduplication
from .discovery import run_discovery
from .extraction import run_extraction
from .graph import run_graph
from .hydration import run_hydration
from .matrix import run_matrix
from .synthesis import run_synthesis
from .verification import run_verification

logger = logging.getLogger(__name__)


async def run_pipeline(
    *,
    workspace_dir: Path | str,
    protocol_path: Path | str | None = None,
    max_search_results: int | None = None,
    mock_mode: bool = False,
    indexing_fn: Callable[[Path], tuple[dict[str, Any], Any]],
) -> dict[str, Any]:
    """Execute the end-to-end research workflow from protocol to synthesis.

    Verbatim move of ``ResearchOrchestrator.run_pipeline_async`` (:517-780):
    protocol load/validate, directory setup, Stage 1-9 delegation in order,
    Stage-4 collect-gate + PAUSE audit, Stage-10 COMPLETED audit, status
    propagation, and no-fabrication returns.

    Only mechanical parameterization: ``workspace_dir`` / ``protocol_path`` /
    ``max_search_results`` inputs, ``indexing_fn`` for Stage 6, direct
    ``append_legacy_event`` for the two coordinator audits. ``mock_mode``
    is accepted-but-unused (signature parity). The screening-preparation
    import stays function-level at its base position. Kit/stage/audit
    failure propagates with no fabricated output and no success claim.
    """
    # mock_mode is accepted-but-unused: identical outcomes either way
    # (signature test test_discovery_stage.py:358). No reference here
    # preserves the base unused-parameter semantics.
    _ = mock_mode

    ws = Path(workspace_dir)
    p_path = Path(protocol_path or (ws / "protocol.json")).resolve()
    if not p_path.exists():
        raise FileNotFoundError(f"Protocol file not found at {p_path}")

    protocol = ResearchProtocol.model_validate_json(p_path.read_text(encoding="utf-8"))
    results: dict[str, Any] = {"status": "SUCCESS", "stages": {}}

    # Setup workspace directories
    lit_dir = ws / "literature"
    pdf_dir = ws / "pdfs"
    ext_dir = ws / "extracted"
    synth_dir = ws / "synthesis"
    audit_dir = ws / "audit"
    chroma_dir = ws / "chroma_db"

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
        workspace_dir=ws,
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
        workspace_dir=ws,
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
        workspace_dir=ws, batch_size=20, force=True
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
        append_legacy_event(
            ws,
            "PIPELINE_RUN_PAUSED_FOR_SCREENING",
            "scholar-harness",
            "Pipeline paused at PRISMA agent-in-the-loop handoff; "
            "screen literature/screening/batch_*.json then run agent_screen.py collect",
            [str(p_path)],
            [str(lit_dir / "screening")],
            results["stages"],
        )
        return results

    # AG-03C currentness gate: stages 5-9 run only on a CURRENT generation; a
    # stale/mismatched generation (including the MISMATCHED a deleted
    # generation reports when authorized material survives it) keeps them
    # SKIPPED/PENDING with an explicit reason naming the status (never a
    # silent pass, never consumption of a superseded run). A true-legacy
    # workspace (migration exception 2026-10-13, bounded — see the AG-03C
    # packet §2/§4: no authorized material ever) proceeds on the legacy file
    # path exactly as before, but REPORTS the typed LEGACY_UNVERIFIED code
    # explicitly — never a silent pass.
    from scholar_harness.authority.generations import (
        GenerationStatus,
        require_current_generation,
    )

    _generation = require_current_generation(ws)
    if _generation.status is GenerationStatus.LEGACY_UNVERIFIED:
        logger.warning(
            "PRISMA outputs are LEGACY_UNVERIFIED (%s); proceeding on the "
            "pre-authorization file path for compatibility: %s",
            _generation.code,
            _generation.message,
        )
    elif _generation.status is not GenerationStatus.CURRENT:
        _generation_reason = (
            "PRISMA outputs not current for authorized stages: "
            f"{_generation.status.value} ({_generation.code}); "
            f"{_generation.message}"
        )
        for stage in ("extraction", "indexing", "matrix", "graph", "synthesis"):
            results["stages"][stage] = {
                "status": "SKIPPED",
                "reason": _generation_reason,
            }
        results["status"] = "PENDING_AGENT_REVIEW"
        append_legacy_event(
            ws,
            "PIPELINE_RUN_PAUSED_FOR_SCREENING",
            "scholar-harness",
            "Pipeline paused: screening publication is not a current "
            f"authorized generation ({_generation_reason}); re-collect under "
            "an authorized generation before stages 5-9",
            [str(p_path)],
            [str(lit_dir / "screening")],
            results["stages"],
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
    # HCM-04l: the orchestrator keeps the thin _run_indexing_stage method
    # untouched (E3/e2e call it directly); the coordinator takes it as the
    # explicit indexing_fn collaborator (required, no default) and calls it
    # here with the same chroma_dir argument the base passed.
    index_res, indexer = indexing_fn(chroma_dir)
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
    # HCM-04k: delegated to the neutral pipeline stage. run_synthesis
    # owns engine construction, first-RQ selection with fallbacks, the
    # synchronous synthesize call, and literature_review.md publication;
    # it emits no audit event and writes no registry state.
    synthesis_outcome = run_synthesis(
        protocol=protocol,
        retriever=retriever,
        synthesis_dir=synth_dir,
    )
    # Local bindings retained: the results mapping below reads them;
    # Stage 10 reads the synth_file path.
    synth_file = synthesis_outcome.review_path
    results["stages"]["synthesis"] = {
        "verified_claims": synthesis_outcome.verified_claims,
        "total_claims": synthesis_outcome.total_claims,
        "entailment_rate": synthesis_outcome.entailment_rate,
    }

    # -------------------------------------------------------------
    # Stage 10: Append-Only Audit Journal Logging
    # -------------------------------------------------------------
    append_legacy_event(
        ws,
        "PIPELINE_RUN_COMPLETED",
        "scholar-harness",
        f"Completed end-to-end research pipeline for '{protocol.metadata.get('title', 'Unknown')}'",
        [str(p_path)],
        [
            str(synth_file),
            str(lit_dir / "synthesis_matrix.csv"),
            str(lit_dir / "knowledge_graph.html"),
        ],
        results["stages"],
    )

    return results
