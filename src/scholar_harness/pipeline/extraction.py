"""Extraction stage (HCM-04g neutral extraction).

Stage 5 of the research pipeline: fulltext extraction over included studies
with no invented prose. Extracted verbatim from
``ResearchOrchestrator.run_pipeline_async`` so the orchestrator delegates
without behavior change.

Preservation notes:

- Filename rule (``_extraction_file_stem``), DOI rule (``_study_doi``), and
  PDF locator (``_study_pdf``) are moved here verbatim; the orchestrator
  re-exports them (HCM-04b pattern) so the ``extraction_producer``,
  fidelity, conformance, and e2e import seams keep resolving from the
  orchestrator namespace with object identity (``orch.X is stage.X``).
- Engine path unchanged: ``scholar_pdf.extract.PyMuPDFEngine`` is
  constructed here exactly as the base Stage 5 did (``PyMuPDFEngine()``)
  and ``extract_markdown`` is called with the same ``(pdf, ext_dir,
  metadata=metadata)`` shape. Class-level
  ``PyMuPDFEngine.extract_markdown`` patches work regardless of import
  site, and no orchestrator-namespace engine patch was found, so NO
  broad ``orchestrator.__dict__`` fallback seam is added (none is needed).
- Byte-identical frontmatter template (exact f-string lines including
  ``json.dumps(..., ensure_ascii=False)``, raw ``year``, and
  ``extraction_engine: "metadata"``), filenames (``{slug}.md``), and
  skip/continue/fallthrough order: existing-file skip first, then
  PDF-try/continue, then engine-failure warning fallthrough, then
  metadata-frontmatter write. The failure warning text
  (``"PyMuPDF extraction failed for %s: %s"``) and the
  ``## Abstract`` body (verbatim abstract or ``"No abstract provided."``)
  are unchanged; no Methodology/Results/Limitations prose is invented.
- Rerun idempotence preserved: an existing ``{slug}.md`` is recorded and
  skipped without rewriting.
- The stage emits NO audit event and writes NO registry/acceptance state;
  the orchestrator maps the outcome to the identical
  ``results["stages"]["extraction"]`` payload (``status DONE``,
  ``documents`` count, ``metadata_frontmatter_only`` list).

Neutrality: stdlib plus ``scholar-pdf-kit`` only -- no console transport,
no Contract v1 acceptance, no workspace audit.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scholar_pdf.extract import PyMuPDFEngine

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


@dataclass
class ExtractionOutcome:
    """Typed outcome of the extraction stage.

    ``documents`` are the extracted markdown paths (the ``extracted_files``
    binding the orchestrator maps to ``stages["extraction"]["documents"]``);
    ``metadata_frontmatter_only`` lists the ``str`` paths written from
    metadata frontmatter without PDF text. ``count`` is ``len(documents)``.
    """

    documents: list[Path] = field(default_factory=list)
    metadata_frontmatter_only: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        """Number of extracted documents (``len(documents)``)."""
        return len(self.documents)


def run_extraction(
    *,
    included_documents: list[dict[str, Any]],
    pdfs_dir: Path | str,
    extracted_dir: Path | str,
) -> ExtractionOutcome:
    """Extract fulltext markdown for each included study document.

    Verbatim move of orchestrator Stage 5: existing-file skip, metadata dict
    (``workspace_id``/``doi``/``title``-or-``Untitled``/``authors``/``year``),
    PDF locate via ``_study_pdf``, ``PyMuPDFEngine().extract_markdown`` try
    with warning-and-fallthrough on failure, then metadata-frontmatter-only
    write (exact template + ``## Abstract`` verbatim body).

    Only mechanical parameterization: ``included_documents`` / ``pdfs_dir`` /
    ``extracted_dir`` inputs. No logic edits, no renames of filenames/
    messages/template, no audit event, no registry writes.
    """
    pdf_dir = Path(pdfs_dir)
    ext_dir = Path(extracted_dir)
    # Idempotent directory assurance (the orchestrator already creates this
    # before Stage 5; direct stage calls over a fresh tmp_path need it for
    # the frontmatter write). No behavior change when it exists.
    ext_dir.mkdir(parents=True, exist_ok=True)

    extracted_files: list[Path] = []
    metadata_frontmatter_only: list[str] = []
    pymupdf = PyMuPDFEngine()
    for doc_item in included_documents:
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

    return ExtractionOutcome(
        documents=extracted_files,
        metadata_frontmatter_only=metadata_frontmatter_only,
    )
