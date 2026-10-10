"""Synthesis stage (HCM-04k neutral extraction).

Stage 9 of the research pipeline: grounded evidence synthesis and
entailment over the vector-indexed corpus. Extracted verbatim from
``ResearchOrchestrator.run_pipeline_async`` (:733-757) so the
orchestrator delegates without behavior change.

Preservation notes:

- Engine construction is verbatim: ``GroundedSynthesisEngine`` with the
  exact ``retriever=retriever`` keyword, where ``retriever`` is the SAME
  object Stage 7 carried (``matrix_outcome.retriever``), never a fresh
  retriever, never ``indexer.retriever``.
- RQ selection is verbatim: ``protocol.research_questions[0]`` when the
  list is non-empty, else ``None``; ``rq_text`` falls back to
  ``"What are the primary empirical findings?"`` and ``rq_id`` falls
  back to ``"RQ1"``. The in-memory ``ResearchProtocol`` is passed
  through untouched (no re-parse, no re-compile, no dimension edits).
- ``synthesize`` is called synchronously (the base never awaited it)
  with the exact ``query=rq_text`` / ``rq_id=rq_id`` /
  ``section_category="results_empirical"`` keywords. No ``n_chunks``,
  ``paradigm``, ``boost_dois``, or ``llm_callable`` override is added;
  kit defaults apply exactly as the base did.
- Publication is verbatim: ``synthesis_dir / "literature_review.md"``
  written with ``synthesis_result.synthesis_markdown`` in ``utf-8``
  encoding, same path/name/encoding/content (byte-identical). The stage
  emits NO audit event and writes NO registry/acceptance state; the
  orchestrator maps the outcome to the identical
  ``results["stages"]["synthesis"]`` payload (``verified_claims`` /
  ``total_claims`` / ``entailment_rate``). Stage 10 still logs the
  review path later, unchanged.
- Generated prose stays system output, never human-approved: the stage
  adds no prompt, model, ranking, or claim logic and performs no
  scientific review; it only coordinates the kit engine and publishes
  its markdown bytes.
- Error propagation unchanged: an engine-construction or ``synthesize``
  raise propagates with no file, no fabricated mapping, and no success
  claim. A file-write failure likewise propagates with no outcome.
- The outcome carries counts plus the review path only; the markdown
  bytes live on disk as the base did. No ``synthesis_markdown`` field
  is added: the mapping needs only counts, Stage 10 needs only the
  path, and byte-parity probes read the file.

Neutrality: stdlib plus ``scholar-rag-kit`` only for the synthesis
engine shape -- no console transport, no Contract v1 acceptance beyond
what the kit itself publishes, no workspace audit.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scholar_rag.synthesis import GroundedSynthesisEngine

logger = logging.getLogger(__name__)


# Kit class captured at import time so the legacy orchestrator-namespace
# seam below can tell a monkeypatched fake apart from the real kit class.
_REAL_ENGINE = GroundedSynthesisEngine


@dataclass
class SynthesisOutcome:
    """Typed outcome of the synthesis stage.

    ``verified_claims`` is ``synthesis_result.verified_claims_count``
    (the value the orchestrator maps to ``stages["synthesis"]``);
    ``total_claims`` is ``len(synthesis_result.claims)``;
    ``entailment_rate`` is ``synthesis_result.entailment_rate``;
    ``review_path`` is the ``synthesis/literature_review.md`` path
    published by this stage (the ``synth_file`` binding Stage 10 logs).
    """

    verified_claims: int
    total_claims: int
    entailment_rate: float
    review_path: Path


def _engine_class() -> type[GroundedSynthesisEngine]:
    """Return the ``GroundedSynthesisEngine`` class honoring the legacy test seam.

    Hermetic orchestrator tests monkeypatch
    ``scholar_harness.orchestrator.GroundedSynthesisEngine`` with a fake
    engine (fidelity ``:195``, extraction-stage ``:763``,
    matrix-stage ``:548``, graph-stage ``:554``). The orchestrator no
    longer constructs the engine itself, so the stage honors an
    orchestrator-namespace override when it differs from the kit class
    and otherwise uses this module's own global (which tests may also
    patch directly). Transitional HCM-04k seam: a later stub-migration
    packet should migrate the fidelity stubs to patch
    ``scholar_harness.pipeline.synthesis.GroundedSynthesisEngine``
    directly and drop the orchestrator fallback.
    """
    try:
        import scholar_harness.orchestrator as _orchestrator

        candidate = _orchestrator.__dict__.get("GroundedSynthesisEngine")
        if candidate is not None and candidate is not _REAL_ENGINE:
            return candidate
    except ImportError:  # pragma: no cover - orchestrator is always importable
        pass
    return GroundedSynthesisEngine


def run_synthesis(
    *,
    protocol: Any,
    retriever: Any,
    synthesis_dir: Path | str,
) -> SynthesisOutcome:
    """Run grounded synthesis for the first research question, publish review.

    Verbatim move of orchestrator Stage 9 (:736-757): engine via
    ``_engine_class()`` with ``retriever=retriever``, first-RQ selection
    with the ``"What are the primary empirical findings?"`` / ``"RQ1"``
    fallbacks, synchronous ``synthesize(query=rq_text, rq_id=rq_id,
    section_category="results_empirical")``, then the identical
    ``literature_review.md`` ``utf-8`` write.

    Only mechanical parameterization: ``protocol`` / ``retriever`` /
    ``synthesis_dir`` inputs. No logic edits, no renames of
    filenames/fallbacks/call shapes, no prompt/model/ranking/claim
    changes, no audit event, no registry writes. Kit failure propagates
    with no fabricated review and no success mapping.
    """
    synth_dir = Path(synthesis_dir)
    # Idempotent directory assurance (the orchestrator already creates this
    # before Stage 9; direct stage calls over a fresh tmp_path need it for
    # the review write). No behavior change when it exists.
    synth_dir.mkdir(parents=True, exist_ok=True)

    engine = _engine_class()(retriever=retriever)
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
    return SynthesisOutcome(
        verified_claims=synthesis_result.verified_claims_count,
        total_claims=len(synthesis_result.claims),
        entailment_rate=synthesis_result.entailment_rate,
        review_path=synth_file,
    )
