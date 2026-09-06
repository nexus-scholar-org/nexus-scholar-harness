"""Scholar PDF Kit: Automated Open Access Discovery and PDF downloader."""

from .downloader import AsyncPDFDownloader, DownloadResult
from .extract import DoclingEngine, GrobidEngine, PyMuPDFEngine
from .publisher_patterns import (
    compute_direct_pdf_from_landing_url,
    resolve_doi_to_publisher_pdf,
    rewrite_via_proxy,
)
from .validator import MIN_PDF_SIZE_BYTES, clean_invalid_pdf, is_valid_pdf

__version__ = "0.1.0"
__all__ = [
    "MIN_PDF_SIZE_BYTES",
    "AsyncPDFDownloader",
    "DoclingEngine",
    "DownloadResult",
    "GrobidEngine",
    "PyMuPDFEngine",
    "clean_invalid_pdf",
    "compute_direct_pdf_from_landing_url",
    "is_valid_pdf",
    "resolve_doi_to_publisher_pdf",
    "rewrite_via_proxy",
]
