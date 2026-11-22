"""Part K item 11 (PDF-03): a copy where hard links fail.

The downloader published every file with ``os.link``. On a file system without
hard links (FAT or exFAT USB drives, some network shares) that raises, and every
download failed. Now a link that fails with EPERM, ENOTSUP/EOPNOTSUPP, EXDEV
(or their Windows equivalents) falls back to an exclusive-create copy with
fsync; a destination that already exists is still never overwritten.

The link call is made to fail here; no special file system is needed.
"""

from __future__ import annotations

import errno
import hashlib

import pytest

from scholar_pdf import downloader as downloader_module
from scholar_pdf.downloader import AsyncPDFDownloader

from .test_acquisition_contract import pdf_bytes
from .test_open_copy_resolver import FakeLookups, FakePdfHosts, closed_unpaywall

ADDRESS = "https://repository.example.org/a.pdf"


def no_hard_links(code: int, winerror: int | None = None):
    def link(source, destination, *args, **kwargs):
        error = OSError(code, "hard links are not supported here")
        if winerror is not None:
            error.winerror = winerror
        raise error

    return link


def one_open_copy() -> FakeLookups:
    openalex = {"open_access": {"is_oa": True}, "locations": [{"is_oa": True, "pdf_url": ADDRESS, "version": "publishedVersion"}]}
    return FakeLookups(openalex, closed_unpaywall())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("code", "winerror"),
    [
        (errno.EPERM, None),
        (errno.EXDEV, None),
        (getattr(errno, "ENOTSUP", errno.EOPNOTSUPP), None),
        (errno.EOPNOTSUPP, None),
        (errno.EINVAL, 1),  # Windows: ERROR_INVALID_FUNCTION (FAT, exFAT)
        (errno.EXDEV, 17),  # Windows: ERROR_NOT_SAME_DEVICE
    ],
    ids=["EPERM", "EXDEV", "ENOTSUP", "EOPNOTSUPP", "win-invalid-function", "win-not-same-device"],
)
async def test_a_download_is_stored_by_copy_where_hard_links_fail(code, winerror, monkeypatch, tmp_path):
    monkeypatch.setattr(downloader_module.os, "link", no_hard_links(code, winerror))
    body = pdf_bytes()
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out")

    result = await downloader.process_doi(FakePdfHosts({ADDRESS: body}), one_open_copy(), "10.1/fat")

    assert result.success is True, result.error_message
    assert result.file_path.read_bytes() == body
    assert result.file_path.name == f"DOC-{hashlib.sha256(body).hexdigest()[:32]}.pdf"
    assert sorted(path.name for path in (tmp_path / "out").iterdir()) == [result.file_path.name]


@pytest.mark.asyncio
async def test_ingest_is_stored_by_copy_where_hard_links_fail(monkeypatch, tmp_path):
    monkeypatch.setattr(downloader_module.os, "link", no_hard_links(errno.EPERM))
    source = tmp_path / "mine.pdf"
    source.write_bytes(pdf_bytes())
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out")

    result = await downloader.ingest_pdf(FakeLookups({"title": "T"}, closed_unpaywall()), source, "10.1/fat")

    assert result.success is True, result.error_message
    assert result.file_path.read_bytes() == source.read_bytes()


def test_the_copy_never_overwrites_a_different_file(monkeypatch, tmp_path):
    monkeypatch.setattr(downloader_module.os, "link", no_hard_links(errno.EPERM))
    downloader = AsyncPDFDownloader(output_dir=tmp_path)
    staging = tmp_path / "staging.tmp"
    staging.write_bytes(pdf_bytes("a"))
    final = tmp_path / "final.pdf"
    final.write_bytes(pdf_bytes("b"))

    with pytest.raises(OSError, match="occupied"):
        downloader._promote_staging(staging, final)
    assert final.read_bytes() == pdf_bytes("b")


def test_a_copy_that_fails_midway_leaves_no_partial_file(monkeypatch, tmp_path):
    monkeypatch.setattr(downloader_module.os, "link", no_hard_links(errno.EPERM))

    def broken_fsync(descriptor):
        raise OSError(errno.EIO, "the drive went away")

    monkeypatch.setattr(downloader_module.os, "fsync", broken_fsync)
    downloader = AsyncPDFDownloader(output_dir=tmp_path)
    staging = tmp_path / "staging.tmp"
    staging.write_bytes(pdf_bytes())
    final = tmp_path / "final.pdf"

    with pytest.raises(OSError):
        downloader._promote_staging(staging, final)
    assert not final.exists()


def test_another_link_error_is_not_hidden_by_a_copy(monkeypatch, tmp_path):
    monkeypatch.setattr(downloader_module.os, "link", no_hard_links(errno.ENOSPC))
    downloader = AsyncPDFDownloader(output_dir=tmp_path)
    staging = tmp_path / "staging.tmp"
    staging.write_bytes(pdf_bytes())

    with pytest.raises(OSError) as raised:
        downloader._promote_staging(staging, tmp_path / "final.pdf")
    assert raised.value.errno == errno.ENOSPC
    assert not (tmp_path / "final.pdf").exists()
