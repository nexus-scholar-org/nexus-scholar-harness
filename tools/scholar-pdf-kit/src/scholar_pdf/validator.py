import os
from pathlib import Path

# Real PDFs are at least ~10 KB; HTML block-pages saved from a paywall are
# typically a few KB.  This guards against saving stub pages as PDFs even
# when the first bytes happen to contain a %PDF- marker.
MIN_PDF_SIZE_BYTES = 10 * 1024


def is_valid_pdf(file_path: Path) -> bool:
    """
    Validates if a file is a valid PDF by checking its magic bytes and size.

    A valid PDF file should start with %PDF- and be at least
    ``MIN_PDF_SIZE_BYTES`` (10 KB) — a forged HTML block-page that happens to
    contain a ``%PDF-`` marker early on is therefore rejected.
    """
    if not file_path.exists() or file_path.stat().st_size < 5:
        return False

    try:
        if file_path.stat().st_size < MIN_PDF_SIZE_BYTES:
            return False
        with open(file_path, "rb") as f:
            header = f.read(5)
            return header == b"%PDF-"
    except Exception:
        return False


def clean_invalid_pdf(file_path: Path) -> bool:
    """
    Checks if a file is a valid PDF and deletes it if it is not.
    Returns True if the file was kept, False if it was deleted.
    """
    if is_valid_pdf(file_path):
        return True

    if file_path.exists():
        try:
            os.remove(file_path)
        except OSError:
            pass

    return False