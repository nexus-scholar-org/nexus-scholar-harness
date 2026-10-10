"""Matrix stage (HCM-04i neutral extraction).

Stage 7 of the research pipeline: dynamic protocol matrix extraction over
the vector-indexed corpus. Extracted verbatim from
``ResearchOrchestrator.run_pipeline_async`` (:678-687) so the orchestrator
delegates without behavior change.

Preservation notes:

- Retriever construction is verbatim: ``ScholarRetriever`` with
  ``db_path=str(chroma_dir)`` plus ``collection_name`` /
  ``embedder_kwargs`` read off the Stage-6 ``indexer`` compat object
  (including the ``MinimalIndexer`` refusal shapes, which carry the same
  ``collection_name`` / ``embedder_kwargs`` / ``get_collection_count``
  surface). Only mechanical parameterization (``indexer`` to
  ``indexer_compat``, ``chroma_dir`` / ``literature_dir`` inputs) is
  applied.
- ``MatrixExtractor(protocol=protocol, retriever=retriever)`` is
  constructed exactly as the base Stage 7 did, with the in-memory
  ``ResearchProtocol`` passed through untouched (no re-parse, no
  re-compile, no dimension edits).
- ``extract_all(output_dir=lit_dir)`` is called with the same
  ``literature/`` directory the orchestrator passed; the
  ``(matrix_rows, csv_path, json_path)`` triple keeps its
  filename/location/serialization/ordering/shape (``synthesis_matrix.csv``
  / ``synthesis_matrix.json`` under ``literature/``; the kit also writes
  ``synthesis_matrix.md`` as an inherited side effect, unchanged). The
  ``pipelines.py`` template mention of ``synthesis_matrix.md`` is a
  read-only reference, not Stage-7 output, and is not touched here.
- The stage emits NO audit event and writes NO registry/acceptance state;
  the orchestrator maps the outcome to the identical
  ``results["stages"]["matrix_rows"]`` payload (``status DONE``,
  ``rows`` count). Stage 10 still logs the csv path later, unchanged.
- Downstream binding preserved: Stage 9 reuses the SAME ``retriever``
  object (``GroundedSynthesisEngine(retriever=retriever)``), so the outcome
  carries ``retriever`` alongside ``rows`` / ``csv_path`` / ``json_path``
  (mirroring ``IndexingOutcome`` carrying ``indexer`` for Stage 7).
- Error propagation unchanged: a kit raise (retriever construction,
  extractor construction, or ``extract_all``) propagates with no
  fabricated matrix, no ``DONE`` row, and no success claim.

Neutrality: stdlib plus ``scholar-rag-kit`` only for the
retriever/extractor shapes -- no console transport, no Contract v1
acceptance beyond what the kit itself publishes, no workspace audit.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scholar_rag.matrix import MatrixExtractor
from scholar_rag.retriever import ScholarRetriever

logger = logging.getLogger(__name__)


# Kit classes captured at import time so the legacy orchestrator-namespace
# seams below can tell a monkeypatched fake apart from the real kit class.
_REAL_RETRIEVER = ScholarRetriever
_REAL_MATRIX = MatrixExtractor


@dataclass
class MatrixOutcome:
    """Typed outcome of the matrix stage.

    ``rows`` are the extracted matrix rows (the ``matrix_rows`` binding the
    orchestrator maps to ``stages["matrix_rows"]["rows"]``);
    ``csv_path`` / ``json_path`` are the ``literature/synthesis_matrix.*``
    paths returned by ``extract_all``; ``retriever`` is the SAME retriever
    object passed to ``MatrixExtractor`` and reused by Stage 9
    (``GroundedSynthesisEngine(retriever=retriever)``).
    """

    rows: list[dict[str, Any]]
    csv_path: Path
    json_path: Path
    retriever: Any


def _retriever_class() -> type[ScholarRetriever]:
    """Return the ``ScholarRetriever`` class honoring the legacy test seam.

    Hermetic orchestrator tests monkeypatch
    ``scholar_harness.orchestrator.ScholarRetriever`` with a fake retriever
    (fidelity ``:193`` and extraction-stage ``:761``). The orchestrator no
    longer constructs the retriever itself, so the stage honors an
    orchestrator-namespace override when it differs from the kit class and
    otherwise uses this module's own global (which tests may also patch
    directly). Transitional HCM-04i seam: a later stub-migration packet
    should migrate the fidelity stubs to patch
    ``scholar_harness.pipeline.matrix.ScholarRetriever`` directly and drop
    the orchestrator fallback.
    """
    try:
        import scholar_harness.orchestrator as _orchestrator

        candidate = _orchestrator.__dict__.get("ScholarRetriever")
        if candidate is not None and candidate is not _REAL_RETRIEVER:
            return candidate
    except ImportError:  # pragma: no cover - orchestrator is always importable
        pass
    return ScholarRetriever


def _matrix_class() -> type[MatrixExtractor]:
    """Return the ``MatrixExtractor`` class honoring the legacy test seam.

    Hermetic orchestrator tests monkeypatch
    ``scholar_harness.orchestrator.MatrixExtractor`` with a fake extractor
    (fidelity ``:194`` and extraction-stage ``:762``). The orchestrator no
    longer constructs the extractor itself, so the stage honors an
    orchestrator-namespace override when it differs from the kit class and
    otherwise uses this module's own global (which tests may also patch
    directly). Transitional HCM-04i seam: a later stub-migration packet
    should migrate the fidelity stubs to patch
    ``scholar_harness.pipeline.matrix.MatrixExtractor`` directly and drop
    the orchestrator fallback.
    """
    try:
        import scholar_harness.orchestrator as _orchestrator

        candidate = _orchestrator.__dict__.get("MatrixExtractor")
        if candidate is not None and candidate is not _REAL_MATRIX:
            return candidate
    except ImportError:  # pragma: no cover - orchestrator is always importable
        pass
    return MatrixExtractor


def run_matrix(
    *,
    protocol: Any,
    indexer_compat: Any,
    chroma_dir: Path | str,
    literature_dir: Path | str,
) -> MatrixOutcome:
    """Build the retriever, extract the protocol matrix, publish files.

    Verbatim move of orchestrator Stage 7 (:678-687): ``ScholarRetriever``
    via ``_retriever_class()`` with ``db_path=str(chroma_dir)`` plus the
    ``indexer_compat`` collection/embedder limbs, ``MatrixExtractor`` via
    ``_matrix_class()`` with ``protocol`` + ``retriever``, then
    ``extract_all(output_dir=lit_dir)``.

    Only mechanical parameterization: ``protocol`` / ``indexer_compat`` /
    ``chroma_dir`` / ``literature_dir`` inputs. No logic edits, no renames
    of filenames/messages, no audit event, no registry writes. Kit failure
    propagates with no fabricated rows and no success mapping.
    """
    lit_dir = Path(literature_dir)
    retriever = _retriever_class()(
        db_path=str(chroma_dir),
        collection_name=indexer_compat.collection_name,
        embedder_kwargs=indexer_compat.embedder_kwargs,
    )
    matrix_extractor = _matrix_class()(protocol=protocol, retriever=retriever)
    matrix_rows, csv_path, json_path = matrix_extractor.extract_all(output_dir=lit_dir)
    return MatrixOutcome(
        rows=matrix_rows,
        csv_path=csv_path,
        json_path=json_path,
        retriever=retriever,
    )
