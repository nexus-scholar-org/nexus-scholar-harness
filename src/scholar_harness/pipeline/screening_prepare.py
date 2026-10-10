"""Screening preparation stage (HCM-04f neutral extraction).

Stage 4 preparation of the research pipeline: agent-in-the-loop batch
preparation, batch-file glob count, and the IN PROGRESS PRISMA report.
Extracted verbatim from ``ResearchOrchestrator.run_pipeline_async`` so the
orchestrator delegates without behavior change.

Split (coordinator handoff stays orchestrator-side): this stage owns ONLY
the automated preparation -- the call-time ``cmd_prepare`` batch build, the
``batch_*.json`` glob count (excluding ``_decisions``), and the
``prisma_screening_report.md`` IN PROGRESS write. Human/agent decisions,
adjudication, and the ``included.json`` collect gate (plus the
``PIPELINE_RUN_PAUSED_FOR_SCREENING`` audit and the ``SKIPPED`` mapping for
Stages 5-9) stay in the orchestrator: they are the coordinator's handoff
gate, not preparation.

Preservation notes:

- ``protocol_data`` (base orchestrator ``:622``) was vestigial -- read from
  ``protocol.json`` but never used downstream (only ``p_path`` reaches the
  PAUSE audit inputs). It is NOT carried into this stage; the batcher reads
  the protocol itself from the workspace directory.
- ``papers_to_screen`` (``len(verified_docs)``) is computed by the
  orchestrator from its own Stage 3 binding and is NOT recomputed here; the
  outcome carries no paper count.
- Fidelity seam: the base orchestrator resolved ``cmd_prepare`` with a
  FUNCTION-LEVEL ``from scholar_harness.agent_screen import cmd_prepare``
  so hermetic tests patching ``scholar_harness.agent_screen.cmd_prepare``
  take effect at call time. This stage preserves that mechanism with its own
  call-time resolution and NO module-top binding -- no broad
  ``orchestrator.__dict__`` fallback seam is added (none is needed).
- ``SystemExit`` from the batcher (``sys.exit(1)`` failure modes and the
  ``sys.exit(0)`` existing-batches path) propagates identically -- never
  swallowed, never mapped to an outcome.
- The stage emits NO decisions, NO collect output, and NO audit event of its
  own (no direct ``append_legacy_event`` call; the batch ``ARTIFACT_ACCEPTED``
  rows the batcher publishes via ``accept_artifact`` are inherited
  preparation state, not a stage audit). It never imports the collector,
  never reads ``included.json``, and never calls the audit publisher. The
  ``PIPELINE_RUN_PAUSED_FOR_SCREENING`` row stays orchestrator-side.

Neutrality: stdlib only plus the harness screening batcher entry point
(resolved at call time) -- no console transport, no Contract v1 acceptance
beyond what the batcher itself publishes, no workspace audit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ScreeningPreparationOutcome:
    """Typed outcome of the screening preparation stage.

    ``total_batches`` is the ``batch_*.json`` glob count (excluding
    ``_decisions`` files) -- the value the orchestrator maps to
    ``batch_files_prepared``. ``batch_files`` lists those batch files in
    sorted order (the count matches the base ``len([...])`` exactly; sorting
    only stabilizes the returned list). ``report_path`` is the IN PROGRESS
    PRISMA report written by this stage.
    """

    total_batches: int
    batch_files: list[Path] = field(default_factory=list)
    report_path: Path = field(
        default_factory=lambda: Path("prisma_screening_report.md")
    )

    @property
    def batch_paths(self) -> list[Path]:
        """Alias for ``batch_files`` (packet ``batch_files/paths`` wording)."""
        return self.batch_files


def run_screening_preparation(
    *,
    workspace_dir: Path | str,
    batch_size: int = 20,
    force: bool = True,
) -> ScreeningPreparationOutcome:
    """Prepare screening batches, count them, and write the IN PROGRESS report.

    Verbatim move of orchestrator Stage 4 preparation: call-time
    ``cmd_prepare(workspace_dir, batch_size=20, force=True)``, the
    ``screening_dir.glob("batch_*.json")`` count excluding ``_decisions``,
    and the identical ``prisma_screening_report.md`` IN PROGRESS write
    naming ``literature/screening/`` and the
    ``agent_screen.py collect <workspace_dir>`` next step.

    Only mechanical parameterization: ``workspace_dir`` / ``batch_size`` /
    ``force`` inputs. No logic edits, no renames of filenames/messages, no
    decisions/collect/audit side effects. ``SystemExit`` from ``cmd_prepare``
    escapes identically with nothing further written by this stage.
    """
    # Call-time resolution (NO module-top binding): hermetic tests patch
    # ``scholar_harness.agent_screen.cmd_prepare`` and it takes effect here
    # because the binding happens at call time, exactly as the base
    # orchestrator's function-level import did.
    from scholar_harness.agent_screen import cmd_prepare as _prepare_batches

    ws = Path(workspace_dir)
    lit_dir = ws / "literature"
    # Idempotent directory assurance (the orchestrator already creates this
    # before Stage 4; direct stage calls over a fresh tmp_path need it for
    # the zero-record report write). No behavior change when it exists.
    lit_dir.mkdir(parents=True, exist_ok=True)

    _prepare_batches(ws, batch_size=batch_size, force=force)

    screening_dir = lit_dir / "screening"
    batch_files = sorted(
        f for f in screening_dir.glob("batch_*.json") if "_decisions" not in f.name
    )
    total_batches = len(batch_files)

    report_path = lit_dir / "prisma_screening_report.md"
    report_path.write_text(
        f"# PRISMA Screening \u2014 IN PROGRESS\n\n"
        f"{total_batches} batch files prepared in `literature/screening/`.\n\n"
        f"**Next step**: Ask the agent to screen the batches, then run:\n"
        f"```\npython src/scholar_harness/agent_screen.py collect {ws}\n```\n",
        encoding="utf-8",
    )
    return ScreeningPreparationOutcome(
        total_batches=total_batches,
        batch_files=list(batch_files),
        report_path=report_path,
    )
