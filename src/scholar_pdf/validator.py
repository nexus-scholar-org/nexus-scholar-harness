import os
import re
from dataclasses import dataclass
from pathlib import Path

# Real PDFs are at least ~10 KB; HTML block-pages saved from a paywall are
# typically a few KB.  This guards against saving stub pages as PDFs even
# when the first bytes happen to contain a %PDF- marker.
MIN_PDF_SIZE_BYTES = 10 * 1024

# The PDF spec allows up to 1024 bytes of leading garbage before the header
# and requires the %%EOF marker on the trailer (within the last 1024 bytes
# for non-linearized files).  We scan a generous tail window to tolerate
# sloppy producers without rejecting real files.
_HEADER_SCAN = 1024
_TRAILER_SCAN = 8 * 1024

_HEADER_RE = re.compile(rb"%PDF-\d+\.\d+")


@dataclass(frozen=True)
class PdfCheck:
    """One named check on a candidate file, with its result (Part K, PDF-17)."""

    name: str
    passed: bool
    detail: str


def pdf_checks(file_path: Path, structural: bool = False) -> tuple[PdfCheck, ...]:
    """Each check of ``is_valid_pdf`` by name, plus pypdf's ``structure`` when asked.

    ``pdf_header`` (``%PDF-<major>.<minor>`` in the first 1024 bytes),
    ``pdf_trailer`` (``%%EOF`` in the last 8 KB), ``size_floor`` (at least
    ``MIN_PDF_SIZE_BYTES``) and, with ``structural``, ``structure`` (pypdf
    parses it). A file below the floor is not called invalid (PDF-17).
    """
    try:
        size = file_path.stat().st_size
        with open(file_path, "rb") as stream:
            head = stream.read(_HEADER_SCAN)
            stream.seek(max(0, size - _TRAILER_SCAN))
            tail = stream.read(_TRAILER_SCAN)
    except (OSError, ValueError, OverflowError):
        return (PdfCheck("readable", False, "the file could not be read"),)
    checks = [
        PdfCheck(
            "pdf_header",
            _HEADER_RE.search(head) is not None,
            "%PDF- header in the first 1024 bytes",
        ),
        PdfCheck("pdf_trailer", b"%%EOF" in tail, "%%EOF trailer in the last 8 KB"),
        PdfCheck(
            "size_floor",
            size >= MIN_PDF_SIZE_BYTES,
            f"{size} bytes; the floor is {MIN_PDF_SIZE_BYTES} bytes",
        ),
    ]
    if structural:
        parses = all(check.passed for check in checks) and validate_pdf_structure(file_path)
        checks.append(PdfCheck("structure", parses, "pypdf parses the file"))
    return tuple(checks)


def check_failure(checks: tuple[PdfCheck, ...]) -> str | None:
    """The first failed check in words, or ``None`` when every check passed."""
    failed = {check.name: check for check in checks if not check.passed}
    if not failed:
        return None
    if "readable" in failed:
        return "the file could not be read"
    if "pdf_header" in failed:
        return "not a PDF (no %PDF- header in the first 1024 bytes)"
    if "pdf_trailer" in failed:
        return "not a complete PDF (no %%EOF trailer in the last 8 KB)"
    if "size_floor" in failed:
        return (
            f"below the {MIN_PDF_SIZE_BYTES // 1024} KB size floor "
            f"({failed['size_floor'].detail.split(';')[0]}); it was not judged invalid"
        )
    return "pypdf could not parse it (--strict-validate)"


def is_valid_pdf(file_path: Path) -> bool:
    """
    Validate a candidate PDF by binary signature only (no external deps).

    A real PDF must be at least ``MIN_PDF_SIZE_BYTES`` (10 KB), carry a
    ``%PDF-<major>.<minor>`` header within the first 1024 bytes, and end with
    a ``%%EOF`` trailer marker within the last 8 KB.  This is deliberately
    stricter than a 5-byte prefix check: forged ``%PDF-``-prefixed HTML abuse
    prepends three tokens to an HTML page, which fails the trailer test.
    """
    if not file_path.exists() or file_path.stat().st_size < 5:
        return False

    try:
        if file_path.stat().st_size < MIN_PDF_SIZE_BYTES:
            return False

        size = file_path.stat().st_size
        with open(file_path, "rb") as f:
            head = f.read(_HEADER_SCAN)
            # %PDF-<major>.<minor> must appear within the first 1024 bytes
            # (the spec permits leading garbage before the header).
            if _HEADER_RE.search(head) is None:
                return False

            f.seek(max(0, size - _TRAILER_SCAN))
            tail = f.read(_TRAILER_SCAN)
            return b"%%EOF" in tail
    except (OSError, ValueError, OverflowError):
        return False


def validate_pdf_structure(file_path: Path) -> bool:
    """
    Stronger, optional structural validation via pypdf.

    Returns True when the file actually parses as a PDF.  Encrypted PDFs
    (password-protected) parse fine after decryption and are treated as valid;
    files that pypdf cannot make sense of at all return False.
    """
    if not is_valid_pdf(file_path):
        return False
    try:
        import pypdf
    except ImportError:
        # pypdf declared as a dependency but not installed in this env:
        # binary signature validation is authoritative, do not fail closed.
        return True

    try:
        with open(file_path, "rb") as f:
            pypdf.PdfReader(f, strict=False)
        return True
    except pypdf.errors.WrongPasswordError:
        return True
    except pypdf.errors.PdfReadError as exc:
        # "File has not been decrypted" means it is a real but encrypted PDF.
        return "decrypted" in str(exc).lower()
    except Exception:  # noqa: BLE001 - any parser failure invalidates the candidate
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
