"""Part K item 7 (PDF-12): the access status comes from the evidence and from the bytes.

- Explicit closed evidence (``is_oa: false``, ``oa_status: "closed"``) from a
  service overrides a ``pdf_url`` that service gives: the address is not
  requested and the paper does not read as open access.
- When a file is stored, its access status comes from the location that
  produced the bytes, and that candidate (address and route) is on the result.
- A file fetched through the parked institutional gateway (a caller passing one
  explicitly; the commands refuse a proxy) is never labelled open access: it
  reads ``INSTITUTIONAL_ACCESS`` (M12a item 25).

Offline: in-memory lookups and PDF hosts.
"""

from __future__ import annotations

import pytest

from scholar_pdf.downloader import AsyncPDFDownloader

from .test_acquisition_contract import pdf_bytes
from .test_open_copy_resolver import HTML, FakeLookups, FakePdfHosts, closed_unpaywall

CLOSED_PDF = "https://publisher.example.org/article/1.pdf"
OPEN_PDF = "https://repository.example.org/item/1.pdf"


def openalex_closed_with_pdf_url() -> dict:
    """The PDF-12 evidence: a closed work whose primary location carries a ``pdf_url``."""
    return {
        "open_access": {"is_oa": False, "oa_status": "closed"},
        "best_oa_location": None,
        "primary_location": {"landing_page_url": "https://doi.org/10.1/c", "pdf_url": CLOSED_PDF},
        "locations": [{"landing_page_url": "https://doi.org/10.1/c", "pdf_url": CLOSED_PDF}],
    }


def unpaywall_closed_with_pdf_url() -> dict:
    """Unpaywall says the work is closed, yet its best location carries an address."""
    return {
        "is_oa": False,
        "oa_status": "closed",
        "best_oa_location": {"url_for_pdf": CLOSED_PDF, "version": "publishedVersion"},
        "oa_locations": [{"url_for_pdf": CLOSED_PDF, "version": "publishedVersion"}],
    }


def unpaywall_open() -> dict:
    return {
        "is_oa": True,
        "oa_status": "green",
        "best_oa_location": {"url_for_pdf": OPEN_PDF, "version": "acceptedVersion", "host_type": "repository"},
        "oa_locations": [{"url_for_pdf": OPEN_PDF, "version": "acceptedVersion", "host_type": "repository"}],
    }


@pytest.fixture
def downloader(tmp_path):
    return AsyncPDFDownloader(output_dir=tmp_path / "out")


def test_closed_evidence_overrides_a_pdf_url_in_the_access_status():
    status = AsyncPDFDownloader._provider_access_status(openalex_closed_with_pdf_url())
    assert status == "UNRESOLVED"
    assert AsyncPDFDownloader._provider_access_status(unpaywall_closed_with_pdf_url()) == "UNRESOLVED"


@pytest.mark.asyncio
async def test_a_closed_paper_with_a_pdf_url_is_not_open_access(downloader):
    hosts = FakePdfHosts({CLOSED_PDF: pdf_bytes()})
    lookups = FakeLookups(openalex_closed_with_pdf_url(), closed_unpaywall())

    result = await downloader.process_doi(hosts, lookups, "10.1/c")

    assert hosts.requested == []
    assert result.success is False
    assert result.outcome == "NO_OPEN_COPY_LISTED"
    assert result.access_status == "UNRESOLVED"
    assert result.was_oa is False


@pytest.mark.asyncio
async def test_unpaywalls_closed_evidence_overrides_its_own_listed_address(downloader):
    hosts = FakePdfHosts({CLOSED_PDF: pdf_bytes()})
    lookups = FakeLookups(openalex_closed_with_pdf_url(), unpaywall_closed_with_pdf_url())

    result = await downloader.process_doi(hosts, lookups, "10.1/c")

    assert hosts.requested == []
    assert result.success is False and result.access_status == "UNRESOLVED"


@pytest.mark.asyncio
async def test_the_status_and_the_candidate_come_from_the_location_that_gave_the_bytes(downloader):
    hosts = FakePdfHosts({OPEN_PDF: pdf_bytes()})
    lookups = FakeLookups(openalex_closed_with_pdf_url(), unpaywall_open())

    result = await downloader.process_doi(hosts, lookups, "10.1/mixed")

    assert hosts.requested == [OPEN_PDF]
    assert result.success is True, result.error_message
    assert result.access_status == "VERIFIED_OPEN_ACCESS" and result.was_oa is True
    assert result.source_url == OPEN_PDF
    assert result.route == "open_location"
    assert (result.open_copy.url, result.open_copy.provider) == (OPEN_PDF, "unpaywall")


@pytest.mark.asyncio
async def test_a_file_through_the_parked_gateway_is_institutional_never_open_access(tmp_path):
    gateway = "https://www.sndl1.arn.dz"
    downloader = AsyncPDFDownloader(output_dir=tmp_path / "out", institutional_gateway_url=gateway)
    proxied = "https://repository-example-org.www.sndl1.arn.dz/item/1.pdf"
    hosts = FakePdfHosts({OPEN_PDF: HTML, proxied: pdf_bytes()})
    lookups = FakeLookups({"open_access": {"is_oa": False}}, unpaywall_open())

    result = await downloader.process_doi(hosts, lookups, "10.1/gateway")

    assert hosts.requested == [OPEN_PDF, proxied]
    assert result.success is True, result.error_message
    assert result.access_status == "INSTITUTIONAL_ACCESS"
    assert result.was_oa is False
    assert result.route == "institutional_gateway"
    assert result.source_url == proxied
    assert result.open_copy is None  # as merged (H-pdf-resolver-locations item 14b, PROPOSED)


@pytest.mark.asyncio
async def test_no_candidate_is_recorded_when_no_file_came(downloader):
    hosts = FakePdfHosts()  # HTML everywhere
    lookups = FakeLookups({"open_access": {"is_oa": False}}, unpaywall_open())

    result = await downloader.process_doi(hosts, lookups, "10.1/none")

    assert result.success is False
    assert result.source_url is None and result.route is None
    # The paper is still listed as open by its evidence; only no bytes came.
    assert result.access_status == "VERIFIED_OPEN_ACCESS"
