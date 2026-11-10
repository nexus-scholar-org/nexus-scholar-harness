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

from scholar_harness.workspace.audit import append_event, append_legacy_event

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


def _existing_batch_count(lit_dir: Path) -> int:
    """Screening batch files already prepared (decision files excluded)."""
    screening = lit_dir / "screening"
    if not screening.is_dir():
        return 0
    return sum(1 for p in screening.iterdir() if p.name.startswith("batch_")
               and p.suffix == ".json" and "_decisions" not in p.name)


def _accept_run_corpus(ws: Path, provider_errors: dict[str, str]) -> dict[str, Any]:
    """Accept the run's verified records as the corpus snapshot (CORE-07).

    Returns the stage mapping: ``ACCEPTED`` (or ``ALREADY_ACCEPTED`` when the
    identical snapshot is registered), ``NOT_BUILT`` when the folder is not a
    workspace (no ``project.json``, so no workspace id to bind the snapshot
    to), or ``REFUSED`` with the typed code.
    """
    from scholar_harness.corpus_accept import AcceptCorpusRefused, accept_corpus

    try:
        manifest = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        manifest = None
    except (OSError, ValueError):
        manifest = {}  # unreadable: accept_corpus refuses it with its own code
    if manifest is None:
        return {
            "status": "NOT_BUILT",
            "reason": "no project.json: the folder is not a workspace, so no snapshot was built",
        }
    registered = manifest.get("registered_workspace_id") if isinstance(manifest, dict) else None
    if manifest and not (isinstance(registered, str) and registered.startswith("WSP-")):
        return {
            "status": "NOT_BUILT",
            "reason": (
                "project.json records no registered_workspace_id (a legacy workspace); "
                "no snapshot was built. Run `nexus-scholar accept-corpus` after registering it."
            ),
        }
    verified = ws / "literature" / "verified.json"
    try:
        rows = json.loads(verified.read_text(encoding="utf-8")) if verified.is_file() else []
    except (OSError, ValueError):
        rows = None  # unreadable: accept_corpus refuses it with its own code
    if rows == [] or (rows is not None and not isinstance(rows, list)):
        return {
            "status": "NOT_BUILT",
            "reason": "no verified records: there is nothing to snapshot",
        }
    from scholar_harness.corpus_accept import staged_sources

    if staged_sources(ws):
        # accept_corpus would materialise the staged database exports over the
        # verified.json this run just wrote, dropping the searched records
        # (M3a review finding 2). Two corpora are never merged silently.
        return {
            "status": "REFUSED",
            "code": "STAGED_IMPORT_PENDING",
            "reason": (
                "database exports are staged for import in this workspace; accept or "
                "remove them before building a corpus from a search run"
            ),
        }
    warnings = [f"{name}: {error}" for name, error in sorted(provider_errors.items())]
    try:
        accepted = accept_corpus(ws, provider_warnings=warnings)
    except AcceptCorpusRefused as exc:
        return {"status": "REFUSED", "code": exc.code, "reason": str(exc)}
    _journal_snapshot_accepted(ws, accepted, "from the search run", agent="scholar-harness")
    return {
        "status": "ALREADY_ACCEPTED" if accepted.already_accepted else "ACCEPTED",
        "artifact_id": accepted.artifact_id,
        "study_count": accepted.study_count,
        "record_count": accepted.record_count,
        "outcome_status": accepted.outcome_status,
        "provider_warnings": list(accepted.warnings),
    }


def _journal_snapshot_accepted(
    ws: Path, accepted: Any, origin: str, *, agent: str, run: str | None = None
) -> None:
    """Packet B: the producer's operation outcome (SUCCESS, or PARTIAL with the
    provider warnings) is journalled, not dropped (M3a review finding 5)."""
    parameters: dict[str, Any] = {
        "artifact_id": accepted.artifact_id,
        "already_accepted": accepted.already_accepted,
        "outcome_status": accepted.outcome_status,
        "provider_warnings": list(accepted.warnings),
    }
    if run is not None:
        parameters["run"] = run
    append_event(
        ws,
        "CORPUS_SNAPSHOT_ACCEPTED",
        f"Corpus snapshot {accepted.artifact_id} {origin}: "
        f"{accepted.study_count} studies from {accepted.record_count} records "
        f"({accepted.outcome_status})",
        agent=agent,
        inputs=[str(ws / "literature" / "verified.json")],
        outputs=[str(ws / "audit" / "artifact_registry.json")],
        parameters=parameters,
        metrics={"studies": accepted.study_count, "records": accepted.record_count},
        status=accepted.outcome_status,
    )


def discovery_corpus_run(ws: Path) -> Path | None:
    """The newest search run whose records became ``verified.json``, or ``None``."""
    runs_dir = Path(ws) / "literature" / "search_runs"
    if not runs_dir.is_dir():
        return None
    runs = sorted(
        (d for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("run_") and d.name[4:].isdigit()),
        key=lambda d: int(d.name[4:]),
        reverse=True,
    )
    for run_dir in runs:
        try:
            manifest = json.loads((run_dir / "legs.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        published = manifest.get("corpus_published", manifest.get("raw_published"))
        if published:
            return run_dir
    return None


def accept_discovery_corpus(workspace: Path | str, *, agent: str = "scholar-harness-console") -> Any:
    """Accept a browser run's ``verified.json`` as the corpus snapshot (M3d-engine).

    The hand-off screen's accept (decision 2026-11-10): the same producer call
    as the end of a CLI ``run`` (``accept_corpus`` with the run's failed
    databases as provider warnings, read back from its ``legs.json``), so the
    same records give the same artifact id and the same outcome status, and
    the same ``CORPUS_SNAPSHOT_ACCEPTED`` row. Refusals propagate as
    ``AcceptCorpusRefused``.
    """
    from scholar_harness.corpus_accept import accept_corpus

    ws = Path(workspace).resolve()
    run_dir = discovery_corpus_run(ws)
    errors: dict[str, str] = {}
    if run_dir is not None:
        manifest = json.loads((run_dir / "legs.json").read_text(encoding="utf-8"))
        errors = {
            str(leg.get("provider")): str(leg.get("error") or "failed")
            for leg in manifest.get("legs") or []
            if isinstance(leg, dict) and leg.get("status") == "failed"
        }
    warnings = [f"{name}: {error}" for name, error in sorted(errors.items())]
    accepted = accept_corpus(ws, provider_warnings=warnings)
    origin = f"from search run {run_dir.name}, accepted on the hand-off screen" if run_dir else "from discovery"
    _journal_snapshot_accepted(
        ws, accepted, origin, agent=agent, run=run_dir.name if run_dir else None
    )
    return accepted


#: Typed codes of the resume refusals (E5, M3b-api). The reason strings keep
#: them as prefixes, so journals and older readers still read them.
RESUME_REFUSAL_CODES = ("PROTOCOL_CHANGED_SINCE_SNAPSHOT", "BATCHES_INCOMPLETE")


def _refusal_code(reason: str) -> str | None:
    prefix = reason.split(":", 1)[0].strip()
    return prefix if prefix in RESUME_REFUSAL_CODES else None


def _resume_refusal(ws: Path) -> str | None:
    """Why the batches of an accepted snapshot cannot be resumed, or ``None``.

    The forced prepare used to refuse an edited protocol; resume keeps that
    check, and refuses a batch set that does not cover every study of the
    snapshot (a prepare that stopped part-way). M3a review finding 4.
    """
    from scholar_protocol.canonical import canonical_fingerprint

    registry = json.loads((ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8"))
    corpora = sorted(
        (e for e in registry.get("artifacts", {}).values() if e.get("artifact_type") == "corpus_snapshot"),
        key=lambda e: str(e.get("accepted_at") or ""),
    )
    snapshot = json.loads((ws / corpora[-1]["path"]).read_text(encoding="utf-8"))
    current = canonical_fingerprint(
        ResearchProtocol.model_validate_json((ws / "protocol.json").read_text(encoding="utf-8"))
    )
    if current != snapshot.get("protocol_fingerprint"):
        return (
            "PROTOCOL_CHANGED_SINCE_SNAPSHOT: protocol.json no longer matches the "
            "accepted corpus snapshot; start a new workspace for a changed protocol"
        )
    studies = {s["study_id"] for s in snapshot["data"]["studies"]}
    covered: set[str] = set()
    for path in sorted((ws / "literature" / "screening").glob("batch_*.json")):
        if "_decisions" in path.name:
            continue
        covered |= {p.get("workspace_id") for p in json.loads(path.read_text(encoding="utf-8")).get("papers", [])}
    missing = studies - covered
    if missing:
        return (
            f"BATCHES_INCOMPLETE: {len(missing)} of {len(studies)} studies of the "
            "accepted snapshot are in no screening batch; re-run prepare with --force"
        )
    return None


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
    providers: list[str] | None = None,
    progress_callback: Callable[[str, int], None] | None = None,
    leg_callback: Callable[[Any], None] | None = None,
    stage_callback: Callable[[str, str, Any], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
    notes: list[str] | None = None,
    freeze_corpus: bool = True,
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

    M3b-api (the console's discovery job): ``providers``, ``progress_callback``,
    ``leg_callback``, ``should_stop`` and ``notes`` pass through to
    ``run_discovery``; ``stage_callback(stage, status, detail)`` is called as
    each stage of a search run ends (``discovery``, ``deduplication``,
    ``hydration``, ``verification``, ``corpus_snapshot``,
    ``screening_prepare``). A harvest the researcher cancelled stops after
    discovery with status ``CANCELLED``: nothing is deduplicated or accepted.
    A resume refusal carries its typed ``code`` on the run and on the stages.

    M3d-engine (decision 2026-11-10): ``freeze_corpus=False`` is the browser
    run. It stops after verification with ``corpus_snapshot`` ``NOT_ACCEPTED``
    and status ``PENDING_CORPUS_ACCEPT``: no snapshot, no screening batches.
    The hand-off screen's accept (``accept_discovery_corpus``) freezes it. The
    CLI keeps the default, which accepts at the end of the run as since M3a.
    """

    def emit_stage(name: str, status: str, detail: Any = None) -> None:
        if stage_callback is not None:
            stage_callback(name, status, detail)

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

    # M3a-discovery CORE-06/07: once a corpus snapshot is accepted, the corpus
    # is frozen. A re-run (resume) does not search, deduplicate or verify
    # again, so ids, batches and decisions stay bound to that snapshot.
    from scholar_harness.corpus_accept import _accepted_snapshot

    corpus_frozen = _accepted_snapshot(ws)
    if corpus_frozen:
        verified_path = lit_dir / "verified.json"
        verified_docs = (
            json.loads(verified_path.read_text(encoding="utf-8"))
            if verified_path.is_file()
            else []
        )
        discovery_status = "SKIPPED"
        discovery_reason = (
            "CORPUS_ALREADY_ACCEPTED: the corpus snapshot is accepted; "
            "discovery, deduplication and verification were not re-run"
        )
        results["stages"]["discovery"] = 0
        results["discovery"] = {
            "count": 0,
            "status": discovery_status,
            "reason": discovery_reason,
            "corpus_published": False,
        }
        for stage in ("deduplication", "verification"):
            results["stages"][stage] = {
                **_ABORTED_STAGE_SHAPES[stage],
                "status": "SKIPPED",
                "reason": discovery_reason,
            }
        results["stages"]["corpus_snapshot"] = {
            "status": "ALREADY_ACCEPTED",
            "reason": discovery_reason,
        }
    else:
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
        discovery_options = {
            key: value
            for key, value in (
                ("providers", providers),
                ("progress_callback", progress_callback),
                ("leg_callback", leg_callback),
                ("should_stop", should_stop),
                ("notes", notes),
            )
            if value is not None
        }
        discovery_outcome = await run_discovery(
            protocol_path=p_path,
            literature_dir=lit_dir,
            max_search_results=max_search_results,
            **discovery_options,
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
            "search_run": getattr(discovery_outcome, "search_run", "") or "",
        }
        emit_stage("discovery", discovery_status, {"count": discovery_outcome.count, "reason": discovery_reason})

        if getattr(discovery_outcome, "cancelled", False) is True:
            # M3b-api: the researcher stopped the harvest. Its records stay in
            # the run's folder; nothing downstream is built from a stopped search.
            reason = f"discovery cancelled: {discovery_reason}"
            for name, shape in _ABORTED_STAGE_SHAPES.items():
                results["stages"][name] = {**shape, "status": "SKIPPED", "reason": reason}
            results["status"] = "CANCELLED"
            append_legacy_event(
                ws,
                "PIPELINE_RUN_ABORTED",
                "scholar-harness",
                f"Pipeline stopped: {discovery_reason}{_pipeline_note(results)}",
                [str(p_path)],
                [],
                results["stages"],
                status=_ledger_status(results),
            )
            return results

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
        emit_stage("deduplication", "DONE", results["stages"]["deduplication"])

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
        emit_stage("hydration", "DONE", None)

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
        emit_stage("verification", str(verification_outcome.status), {
            "verified": verification_outcome.verified, "refused": verification_outcome.refused,
        })

        if not freeze_corpus:
            # M3d-engine: a browser harvest does not freeze the corpus; the
            # hand-off screen does (decision 2026-11-10). Nothing past
            # verification is built, and another run or the accept may follow.
            reason = "awaiting the hand-off accept"
            results["stages"]["corpus_snapshot"] = {"status": "NOT_ACCEPTED", "reason": reason}
            emit_stage("corpus_snapshot", "NOT_ACCEPTED", results["stages"]["corpus_snapshot"])
            for stage in ("screening", "extraction", "indexing", "matrix_rows", "graph_nodes", "synthesis"):
                results["stages"][stage] = {
                    **_ABORTED_STAGE_SHAPES[stage],
                    "status": "SKIPPED",
                    "reason": reason,
                }
            results["status"] = "PENDING_CORPUS_ACCEPT"
            _apply_discovery_status(results, discovery_status, discovery_reason)
            append_legacy_event(
                ws,
                "PIPELINE_RUN_PAUSED_FOR_CORPUS_ACCEPT",
                "scholar-harness",
                "Pipeline paused before the corpus snapshot; the researcher accepts "
                f"literature/verified.json on the hand-off screen{_pipeline_note(results)}",
                [str(p_path)],
                [str(lit_dir / "verified.json")],
                results["stages"],
                status=_ledger_status(results),
            )
            return results

        # -------------------------------------------------------------
        # Stage 3.5: Corpus snapshot (WP-01 Packet B runtime adoption, CORE-07)
        # -------------------------------------------------------------
        # The verified records become the accepted Contract-v1 corpus
        # snapshot through the same producer path as `accept-corpus`
        # (build_corpus_snapshot_artifact + the acceptance gate), so
        # screening can be prepared from a fresh run. Provider failures are
        # carried as snapshot warnings (partial outcome, never hidden).
        snapshot = _accept_run_corpus(
            ws, getattr(discovery_outcome, "provider_errors", {}) or {}
        )
        results["stages"]["corpus_snapshot"] = snapshot
        emit_stage("corpus_snapshot", snapshot["status"], snapshot)
        if snapshot["status"] == "REFUSED":
            reason = f"corpus snapshot refused: {snapshot['reason']}"
            for stage in ("screening", "extraction", "indexing", "matrix_rows", "graph_nodes", "synthesis"):
                results["stages"][stage] = {
                    **_ABORTED_STAGE_SHAPES[stage],
                    "status": "SKIPPED",
                    "reason": reason,
                }
            results["status"] = "FAILED"
            append_legacy_event(
                ws,
                "PIPELINE_RUN_ABORTED",
                "scholar-harness",
                f"Pipeline aborted: the corpus snapshot was refused ({snapshot.get('code')}): "
                f"{snapshot['reason']}{_pipeline_note(results)}",
                [str(lit_dir / "verified.json")],
                [],
                results["stages"],
                status=_ledger_status(results),
            )
            return results

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

    existing_batches = _existing_batch_count(lit_dir)
    resume_refusal = (
        _resume_refusal(ws) if corpus_frozen and existing_batches else None
    )
    if corpus_frozen and existing_batches and resume_refusal is None:
        # Resume: the batches of the accepted snapshot are kept as they are
        # (a forced re-prepare would reshuffle them under existing decisions).
        total_batches = existing_batches
    else:
        try:
            if resume_refusal is not None:
                raise SystemExit(resume_refusal)
            preparation_outcome = run_screening_preparation(
                workspace_dir=ws, batch_size=20, force=True
            )
        except SystemExit as exc:
            # cmd_prepare exits on a refusal (no registry, protocol mismatch).
            # The run records the abort instead of dying (CORE-07).
            reason = (
                str(exc.code)
                if isinstance(exc.code, str)
                else "screening preparation refused (exit "
                f"{exc.code}); see the log for the reason"
            )
            code = _refusal_code(reason)
            for name in ("screening", "extraction", "indexing", "matrix_rows", "graph_nodes", "synthesis"):
                results["stages"][name] = {
                    **_ABORTED_STAGE_SHAPES[name],
                    "status": "SKIPPED",
                    "reason": reason,
                    **({"code": code} if code else {}),
                }
            results["status"] = "FAILED"
            if code:
                results["code"] = code
            emit_stage("screening_prepare", "FAILED", {"reason": reason, "code": code})
            append_legacy_event(
                ws,
                "PIPELINE_RUN_ABORTED",
                "scholar-harness",
                f"Pipeline aborted: {reason}{_pipeline_note(results)}",
                [str(p_path)],
                [],
                results["stages"],
                status=_ledger_status(results),
            )
            return results
        # Local binding retained: Stage 4 reports this count; Stages 5-9 gate
        # on the collect handoff below.
        total_batches = preparation_outcome.total_batches

    results["stages"]["screening"] = {
        "status": "PENDING_AGENT_REVIEW",
        "batch_files_prepared": total_batches,
        "papers_to_screen": len(verified_docs),
    }
    emit_stage("screening_prepare", "DONE", {"batch_files_prepared": total_batches})
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
