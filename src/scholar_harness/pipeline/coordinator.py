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
  events; stage-owned audits (discovery, hydration, verification, indexing)
  stay in their stages. No new events, no rewording -- except the
  ``PIPELINE_RUN_ABORTED`` row written when the discovery harvest FAILED
  (T-TRUTH-COUNTS-01 fail-closed publication: a failed harvest must not
  produce a "completed" pipeline row).
- Discovery status propagation (T-TRUTH-COUNTS-01, D-5): the pipeline
  status is the **workflow state** only (``SUCCESS`` | ``EMPTY_RESULT`` |
  ``PENDING_AGENT_REVIEW`` | ``FAILED``); the **discovery outcome** lives on
  ``results["discovery"]`` and in the ``DISCOVERY_SEARCH`` ledger row. The
  two axes are never collapsed: a ``FAILED`` harvest aborts the run before
  any downstream stage, an ``EMPTY_RESULT`` harvest is never reported as
  ``SUCCESS``, and a ``PARTIAL`` (degraded) harvest never overwrites the
  waiting state -- it is exposed explicitly through ``results["degraded"]``
  and ``results["degradation_reason"]``. The coordinator-owned ledger rows
  carry the harvest's success-ness (never a generic ``SUCCESS`` next to a
  degraded payload: the journal axis -- a row's status states that row's
  own outcome). The discovery stage's own ``DISCOVERY_SEARCH`` event is
  written by the stage itself (through ``workspace.audit``), never by this
  coordinator.
- Error propagation unchanged: a stage raise propagates with no
  fabricated mapping and no success claim; an audit raise propagates
  after the files the stage wrote.

Neutrality: stdlib plus ``scholar-protocol-kit`` only for the protocol
validation shape and harness stages only for delegation -- no console
transport, no Contract v1 acceptance beyond what the stages themselves
publish, no workspace audit beyond the three coordinator-owned legacy rows
(PAUSE + COMPLETED + ABORTED), no direct scholar-search/rag/pdf/graph kit
imports.
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


#: The stage-mapping shape each stage has on a *successful* path. The abort
#: path (a FAILED harvest) keeps the same keys -- with neutral zero values --
#: so a consumer that reads ``stages.deduplication["unique"]`` or
#: ``stages.matrix_rows["rows"]`` does not hit a ``KeyError`` on an aborted
#: run (T-TRUTH-COUNTS-01, F-9). The stage *names* are the successful-path
#: names too (``matrix_rows`` / ``graph_nodes``), never aliases.
_ABORTED_STAGE_SHAPES: dict[str, dict[str, Any]] = {
    "deduplication": {"unique": 0, "duplicates_removed": 0},
    "verification": {
        "verified": 0,
        "refused": 0,
        "preserved": 0,
        "bridge_restored": 0,
        "refusal_reasons": {},
    },
    "screening": {"batch_files_prepared": 0, "papers_to_screen": 0},
    "extraction": {"documents": 0, "metadata_frontmatter_only": []},
    # The indexing mapping is produced by the injected ``indexing_fn``; its
    # shape is not known here, so only the skip marker is published.
    "indexing": {},
    "matrix_rows": {"rows": 0},
    "graph_nodes": {"nodes": 0, "edges": 0},
    "synthesis": {
        "verified_claims": 0,
        "total_claims": 0,
        "entailment_rate": 0.0,
    },
}


def _apply_discovery_status(
    results: dict[str, Any], discovery_status: str, discovery_reason: str = ""
) -> None:
    """Let the harvest outcome colour the pipeline status (T-TRUTH-COUNTS-01).

    Two orthogonal axes, never collapsed (D-5):

    * ``results["status"]`` is the **workflow state** only: ``SUCCESS``,
      ``EMPTY_RESULT``, ``PENDING_AGENT_REVIEW`` or ``FAILED``;
    * the **discovery outcome** (``SUCCESS`` / ``PARTIAL`` /
      ``EMPTY_RESULT`` / ``FAILED``) lives in ``results["discovery"]`` and in
      the ``DISCOVERY_SEARCH`` ledger row.

    The consequences:

    * ``FAILED`` -- the pipeline status is ``FAILED`` (never ``SUCCESS``);
    * ``EMPTY_RESULT`` -- a pipeline that would otherwise report ``SUCCESS``
      reports ``EMPTY_RESULT`` instead: an empty harvest is never an
      unqualified success. A pipeline that is *waiting* for the PRISMA
      handoff keeps its waiting status (it never claimed ``SUCCESS``) and
      the empty harvest stays visible in ``results["discovery"]``;
    * ``PARTIAL`` -- a degraded harvest never overwrites the workflow state
      (doing so would destroy the waiting state). The degradation is exposed
      explicitly instead: ``results["degraded"]`` is ``True`` and
      ``results["degradation_reason"]`` names the failing providers.

    A stage double that does not report a status at all is treated as
    ``SUCCESS`` (the historical outcome contract of this seam).
    """
    if discovery_status == "FAILED":
        results["status"] = "FAILED"
    elif discovery_status == "PARTIAL":
        results["degraded"] = True
        results["degradation_reason"] = discovery_reason
    elif discovery_status == "EMPTY_RESULT" and results.get("status") == "SUCCESS":
        results["status"] = "EMPTY_RESULT"


def _ledger_status(results: dict[str, Any]) -> str:
    """The status a coordinator-owned journal row must carry.

    The journal axis: a row's status states the row's own outcome, never a
    generic ``SUCCESS`` sitting next to a degraded payload. The
    coordinator-owned rows are about the *run*, so their status states the
    harvest's success-ness:

    * ``FAILED`` -- the harvest failed (the row is the abort row);
    * ``PARTIAL`` -- the harvest was degraded: the row must not claim an
      unqualified success;
    * ``EMPTY_RESULT`` -- the harvest returned nothing: the row must not
      claim an unqualified success;
    * ``SUCCESS`` -- the harvest itself succeeded (the historical status of
      these rows; the pause itself is stated by the row's action and
      description, and the workflow state is in the returned mapping).

    ``append_legacy_event`` defaults to ``status="SUCCESS"``; relying on
    that default is exactly the defect this rule closes.
    """
    discovery = results.get("discovery") or {}
    harvest = str(discovery.get("status", "") or "")
    if harvest in ("PARTIAL", "EMPTY_RESULT", "FAILED"):
        return harvest
    return "SUCCESS"


def _pipeline_note(results: dict[str, Any]) -> str:
    """An explicit note about the harvest provenance and its degradation.

    Appended to the coordinator-owned row descriptions so a provenance gap
    (a ``DISCOVERY_SEARCH`` row that could not be written) or a degradation
    is visible in the ledger itself, never only in the returned mapping.
    """
    notes: list[str] = []
    discovery = results.get("discovery") or {}
    if discovery.get("audit_status") == "NOT_WRITTEN":
        notes.append(
            "discovery audit event NOT_WRITTEN: "
            f"{discovery.get('audit_reason', 'unknown reason')}"
        )
    if results.get("degraded"):
        notes.append(
            f"degraded discovery harvest: {results.get('degradation_reason', '')}"
        )
    if discovery.get("stale_artifacts_present"):
        notes.append(
            "stale corpus artifacts of an earlier run were left in place and "
            "are NOT this run's corpus: "
            + ", ".join(discovery.get("stale_artifacts") or [])
        )
    return ("; " + " | ".join(notes)) if notes else ""


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
    ``append_legacy_event`` for the three coordinator audits (PAUSE,
    COMPLETED, ABORTED). ``mock_mode`` is accepted-but-unused (signature
    parity). The screening-preparation import stays function-level at its
    base position. Kit/stage/audit failure propagates with no fabricated
    output and no success claim.
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
    results: dict[str, Any] = {
        "status": "SUCCESS",
        "stages": {},
        # D-5: the degradation signal is explicit and always present, so a
        # consumer never has to guess whether the key exists.
        "degraded": False,
        "degradation_reason": "",
    }

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
    # raw-result publication; it publishes exactly one canonical
    # DISCOVERY_SEARCH audit event (through workspace.audit) and writes no
    # registry state.
    #
    # T-TRUTH-COUNTS-01: the pipeline status must reflect the harvest
    # outcome without collapsing the two axes (D-5). A FAILED harvest
    # publishes no corpus artifact at all and stops the pipeline here
    # (fail-closed publication); an EMPTY_RESULT harvest is never reported
    # as SUCCESS; a PARTIAL (degraded) harvest never overwrites the
    # workflow state -- it is exposed through results["degraded"].
    discovery_outcome = await run_discovery(
        protocol_path=p_path,
        literature_dir=lit_dir,
        max_search_results=max_search_results,
    )
    # Local binding retained: Stage 2 deduplicates these documents.
    discovered_docs = discovery_outcome.documents
    results["stages"]["discovery"] = discovery_outcome.count
    discovery_status = getattr(discovery_outcome, "status", None) or "SUCCESS"
    discovery_reason = getattr(discovery_outcome, "reason", "") or ""
    results["discovery"] = {
        "count": discovery_outcome.count,
        "status": discovery_status,
        "reason": discovery_reason,
        "corpus_published": bool(getattr(discovery_outcome, "published", True)),
        "audit_status": getattr(discovery_outcome, "audit_status", "UNKNOWN"),
        "audit_reason": getattr(discovery_outcome, "audit_reason", ""),
        "audit_workspace": getattr(discovery_outcome, "audit_workspace", ""),
        "stale_artifacts_present": bool(
            getattr(discovery_outcome, "stale_artifacts_present", False)
        ),
        "stale_artifacts": list(
            getattr(discovery_outcome, "stale_artifacts", ()) or ()
        ),
    }

    if discovery_status == "FAILED":
        # Fail-closed publication: a failed harvest must not produce
        # authoritative downstream artifacts. The stage-mapping SHAPE is the
        # successful-path shape (same keys, neutral zero values), so a
        # consumer never hits a KeyError on an aborted run.
        reason = f"discovery failed: {discovery_reason}"
        for stage, shape in _ABORTED_STAGE_SHAPES.items():
            results["stages"][stage] = {
                **shape,
                "status": "SKIPPED",
                "reason": reason,
            }
        results["status"] = "FAILED"
        append_legacy_event(
            ws,
            "PIPELINE_RUN_ABORTED",
            "scholar-harness",
            "Pipeline aborted after a failed discovery harvest: "
            f"{discovery_reason}{_pipeline_note(results)}",
            [str(p_path)],
            [],
            results["stages"],
            status=_ledger_status(results),
        )
        return results

    # -------------------------------------------------------------
    # Stage 2: 2-Tier Deduplication & PID Cluster Assignment
    # Bug fix: Dedup now runs on ALL discovered_docs combined (not a subset).
    # workspace_ids (SCI-XXXXXX) are assigned by the Deduplicator here.
    # -------------------------------------------------------------
    # HCM-04c: delegated to the neutral pipeline stage. run_deduplication
    # owns 2-tier dedup, PID cluster assignment, and deduped publication;
    # it writes no registry state and emits no audit event of its own.
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
        _apply_discovery_status(results, discovery_status, discovery_reason)
        append_legacy_event(
            ws,
            "PIPELINE_RUN_PAUSED_FOR_SCREENING",
            "scholar-harness",
            "Pipeline paused at PRISMA agent-in-the-loop handoff; "
            "screen literature/screening/batch_*.json then run agent_screen.py collect"
            f"{_pipeline_note(results)}",
            [str(p_path)],
            [str(lit_dir / "screening")],
            results["stages"],
            status=_ledger_status(results),
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
        _apply_discovery_status(results, discovery_status, discovery_reason)
        append_legacy_event(
            ws,
            "PIPELINE_RUN_PAUSED_FOR_SCREENING",
            "scholar-harness",
            "Pipeline paused: screening publication is not a current "
            f"authorized generation ({_generation_reason}); re-collect under "
            "an authorized generation before stages 5-9"
            f"{_pipeline_note(results)}",
            [str(p_path)],
            [str(lit_dir / "screening")],
            results["stages"],
            status=_ledger_status(results),
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
    _apply_discovery_status(results, discovery_status, discovery_reason)
    append_legacy_event(
        ws,
        "PIPELINE_RUN_COMPLETED",
        "scholar-harness",
        f"Completed end-to-end research pipeline for '{protocol.metadata.get('title', 'Unknown')}'"
        f"{_pipeline_note(results)}",
        [str(p_path)],
        [
            str(synth_file),
            str(lit_dir / "synthesis_matrix.csv"),
            str(lit_dir / "knowledge_graph.html"),
        ],
        results["stages"],
        status=_ledger_status(results),
    )

    return results
