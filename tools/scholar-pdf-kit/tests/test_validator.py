from pathlib import Path

from scholar_pdf.validator import MIN_PDF_SIZE_BYTES, clean_invalid_pdf, is_valid_pdf


def test_is_valid_pdf_true(tmp_path: Path):
    pdf_path = tmp_path / "valid.pdf"
    # Create a file with a valid PDF header and realistic payload size
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4\n...")
        f.write(b"x" * max(0, MIN_PDF_SIZE_BYTES - 10))  # pad beyond size floor

    assert is_valid_pdf(pdf_path) == True
    assert clean_invalid_pdf(pdf_path) == True
    assert pdf_path.exists()

def test_is_valid_pdf_false_html(tmp_path: Path):
    html_path = tmp_path / "login.html"
    # Create a file with an HTML header instead of PDF
    with open(html_path, "wb") as f:
        f.write(b"<!DOCTYPE html><html>...")

    assert is_valid_pdf(html_path) == False
    assert clean_invalid_pdf(html_path) == False
    assert not html_path.exists() # Should be deleted

def test_is_valid_pdf_too_small(tmp_path: Path):
    small_path = tmp_path / "small.txt"
    # Create a file smaller than 5 bytes
    with open(small_path, "wb") as f:
        f.write(b"%PD")

    assert is_valid_pdf(small_path) == False
    assert clean_invalid_pdf(small_path) == False
    assert not small_path.exists()

def test_is_valid_pdf_size_floor_rejects_small_valid_header(tmp_path: Path):
    """A %PDF- header smaller than the size floor is a stub/block page, not a real PDF."""
    stub_path = tmp_path / "stub.pdf"
    with open(stub_path, "wb") as f:
        f.write(b"%PDF-1.4\n")
        f.write(b"small stub payload" * 10)  # well under MIN_PDF_SIZE_BYTES

    assert is_valid_pdf(stub_path) == False
    assert clean_invalid_pdf(stub_path) == False
    assert not stub_path.exists()