"""H-pdf-resolver-locations: the open-access resolver walks every listed location.

Found live on 2026-11-21 (the check after K0, PR 274): ``scholar-pdf download
--doi 10.7717/peerj.4375`` got 200 from OpenAlex and from Unpaywall and still
answered "No legal open-access PDF URL was resolved". The resolver read only
the "best" location, which is the publisher's landing page with no PDF
address; the direct addresses sit in OpenAlex ``locations`` and Unpaywall
``oa_locations``. A failed lookup also read the same as "no open copy".

The two answers of that check are the fixtures ``openalex_peerj4375.json`` and
``unpaywall_peerj4375.json`` (saved as received; they hold no e-mail address).

Decisions: M12a answer F3 (published version first, then accepted manuscript,
then submitted version or preprint, each labelled), items 24 and 27 (no guessed
address), item 25 (no proxy). Record: ``docs/roadmap/milestones/
H-pdf-resolver-locations.md``.

Everything here is offline: the lookups and the PDF hosts are in-memory fakes
that record each request, and the suite's guard fails any real connection.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlsplit

import aiohttp
import pytest
from scholar_search.exceptions import ProviderError, ProviderTimeoutError
from tenacity import wait_none
from typer.testing import CliRunner

from scholar_pdf.cli import app
from scholar_pdf.downloader import AsyncPDFDownloader, DownloadResult

from .conftest import TEST_CONTACT
from .test_acquisition_contract import pdf_bytes

FIXTURES = Path(__file__).parent / "fixtures"
DOI = "10.7717/peerj.4375"
PMC_PDF = "https://pmc.ncbi.nlm.nih.gov/articles/PMC5815332/pdf/"
REPOSITORY_PDF = (
    "https://umontreal.scholaris.ca/bitstreams/"
    "87977f4b-036a-40f8-9c67-7827df63e419/download"
)
LOOKUP_HOSTS = {"api.openalex.org", "api.unpaywall.org"}
HTML = b"<html><body>Preparing to download ...</body></html>"

runner = CliRunner()


def openalex_answer() -> dict:
    return json.loads((FIXTURES / "openalex_peerj4375.json").read_text(encoding="utf-8"))


def unpaywall_answer() -> dict:
    return json.loads((FIXTURES / "unpaywall_peerj4375.json").read_text(encoding="utf-8"))


def without_address(payload: dict, address: str) -> dict:
    """The same answer with one direct PDF address removed everywhere."""
    changed = copy.deepcopy(payload)

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if value == address and key in ("pdf_url", "url_for_pdf"):
                    node[key] = None
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(changed)
    return changed


# ----------------------------------------------------------------- the fakes


class FakeLookups:
    """Stands for the lookup client. Answers the two services only."""

    def __init__(self, openalex, unpaywall):
        self.answers = {"api.openalex.org": openalex, "api.unpaywall.org": unpaywall}
        self.calls: list[str] = []

    @property
    def hosts(self) -> list[str]:
        return [urlsplit(url).hostname for url in self.calls]

    async def get(self, url, params=None, headers=None, **kwargs):
        self.calls.append(url)
        answer = self.answers[urlsplit(url).hostname]  # any other host is a KeyError
        if isinstance(answer, Exception):
            raise answer
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = answer
        return response

    async def close(self):
        return None


class _Body:
    def __init__(self, data: bytes):
        self._data = data

    async def iter_chunked(self, size):
        yield self._data


class _Response:
    def __init__(self, answer):
        self._error = answer if isinstance(answer, Exception) else None
        self.content = _Body(b"" if self._error else answer)

    def raise_for_status(self):
        if self._error:
            raise self._error

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class FakePdfHosts:
    """Stands for the PDF session. Records every address asked; unknown ones give HTML."""

    def __init__(self, answers: dict[str, bytes | Exception] | None = None):
        self.answers = answers or {}
        self.requested: list[str] = []

    def get(self, url, **kwargs):
        self.requested.append(url)
        return _Response(self.answers.get(url, HTML))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


def not_found(service: str) -> ProviderError:
    return ProviderError(service, "HTTP request failed: not found", status_code=404)


def closed_openalex() -> dict:
    return {
        "open_access": {"is_oa": False, "oa_status": "closed"},
        "best_oa_location": None,
        "primary_location": {
            "is_oa": False,
            "landing_page_url": "https://doi.org/10.1/closed",
            "pdf_url": None,
        },
        "locations": [
            {"is_oa": False, "landing_page_url": "https://doi.org/10.1/closed", "pdf_url": None}
        ],
    }


def closed_unpaywall() -> dict:
    return {"is_oa": False, "oa_status": "closed", "best_oa_location": None, "oa_locations": []}


@pytest.fixture
def downloader(tmp_path):
    return AsyncPDFDownloader(output_dir=tmp_path / "out")


# ----------------------------------------------- 1. every listed location is walked


def test_the_resolver_ranks_the_real_answers_pubmed_central_first():
    from scholar_pdf.open_copies import open_copies

    copies = open_copies(openalex_answer(), unpaywall_answer())

    best = copies[0]
    assert best.url == PMC_PDF
    assert best.version == "publishedVersion"
    assert best.license == "cc-by"
    assert best.host_type == "repository"
    assert best.source_name == "PubMed Central"
    assert best.provider == "openalex"
    # The same two addresses are listed by both services: each is kept once.
    assert [(c.url, c.version, c.provider) for c in copies] == [
        (PMC_PDF, "publishedVersion", "openalex"),
        (REPOSITORY_PDF, "submittedVersion", "openalex"),
    ]


def test_the_resolver_reads_unpaywalls_list_when_it_is_the_only_answer():
    from scholar_pdf.open_copies import open_copies

    copies = open_copies(None, unpaywall_answer())

    assert [(c.url, c.version, c.license, c.host_type, c.provider) for c in copies] == [
        (PMC_PDF, "publishedVersion", "cc-by", "repository", "unpaywall"),
        (REPOSITORY_PDF, "submittedVersion", "cc-by", "repository", "unpaywall"),
    ]
    assert copies[0].source_name == "National Institutes of Health"


@pytest.mark.asyncio
async def test_the_real_answers_download_the_pubmed_central_published_version(downloader):
    lookups = FakeLookups(openalex_answer(), unpaywall_answer())
    hosts = FakePdfHosts({PMC_PDF: pdf_bytes()})

    result = await downloader.process_doi(hosts, lookups, DOI)

    assert result.success is True, result.error_message
    assert result.status == "ACQUIRED" and result.outcome == "ACQUIRED"
    assert result.access_status == "VERIFIED_OPEN_ACCESS"
    assert result.file_path is not None and result.file_path.exists()
    chosen = result.open_copy
    assert (chosen.url, chosen.version, chosen.license) == (PMC_PDF, "publishedVersion", "cc-by")
    assert (chosen.host_type, chosen.source_name, chosen.provider) == (
        "repository",
        "PubMed Central",
        "openalex",
    )
    assert (result.copies_listed, result.copies_tried) == (2, 1)
    # Nothing but the services and the chosen address was asked.
    assert set(lookups.hosts) <= LOOKUP_HOSTS
    assert hosts.requested == [PMC_PDF]


@pytest.mark.asyncio
async def test_unpaywalls_list_is_used_when_openalex_fails(downloader):
    lookups = FakeLookups(
        ProviderError("openalex-pdf", "HTTP request failed", status_code=503),
        unpaywall_answer(),
    )
    hosts = FakePdfHosts({PMC_PDF: pdf_bytes()})

    result = await downloader.process_doi(hosts, lookups, DOI)

    assert result.success is True, result.error_message
    assert result.open_copy.provider == "unpaywall"
    assert result.open_copy.version == "publishedVersion"
    assert hosts.requested == [PMC_PDF]
    assert lookups.hosts == ["api.openalex.org", "api.unpaywall.org"]
    # The failed lookup stays on the result although the paper was found.
    assert [(look.provider, look.state, look.http_status) for look in result.lookups] == [
        ("openalex", "FAILED", 503),
        ("unpaywall", "ANSWERED", 200),
    ]


@pytest.mark.asyncio
async def test_only_a_submitted_version_with_an_address_is_taken_and_labelled(downloader):
    lookups = FakeLookups(
        without_address(openalex_answer(), PMC_PDF),
        without_address(unpaywall_answer(), PMC_PDF),
    )
    hosts = FakePdfHosts({REPOSITORY_PDF: pdf_bytes()})

    result = await downloader.process_doi(hosts, lookups, DOI)

    assert result.success is True, result.error_message
    assert result.open_copy.url == REPOSITORY_PDF
    assert result.open_copy.version == "submittedVersion"
    assert result.open_copy.license == "cc-by"
    assert result.open_copy.host_type == "repository"
    assert hosts.requested == [REPOSITORY_PDF]


# --------------------------------- 1. open locations with a direct address only


@pytest.mark.asyncio
async def test_a_closed_location_or_a_landing_page_is_never_requested(downloader):
    openalex = {
        "open_access": {"is_oa": True, "oa_status": "green"},
        "best_oa_location": {
            "is_oa": True,
            "landing_page_url": "https://repository.example.org/item/1",
            "pdf_url": None,
            "version": "acceptedVersion",
        },
        "primary_location": {
            "is_oa": False,
            "landing_page_url": "https://publisher.example.org/article/1",
            "pdf_url": "https://publisher.example.org/article/1.pdf",
            "version": "publishedVersion",
        },
        "locations": [
            {
                "is_oa": False,
                "landing_page_url": "https://publisher.example.org/article/1",
                "pdf_url": "https://publisher.example.org/article/1.pdf",
                "version": "publishedVersion",
            },
            {"is_oa": True, "landing_page_url": "https://repository.example.org/item/1", "pdf_url": None},
            # No is_oa at all: the provider did not mark it open.
            {"landing_page_url": "https://x.example.org/2", "pdf_url": "https://x.example.org/2.pdf"},
            # Not a web address.
            {"is_oa": True, "pdf_url": "ftp://files.example.org/1.pdf"},
        ],
    }
    unpaywall = {
        "is_oa": True,
        "oa_status": "green",
        "best_oa_location": {
            "url": "https://repository.example.org/item/1",
            "url_for_landing_page": "https://repository.example.org/item/1",
            "url_for_pdf": None,
            "version": "acceptedVersion",
        },
        "oa_locations": [
            {
                "url": "https://repository.example.org/item/1",
                "url_for_landing_page": "https://repository.example.org/item/1",
                "url_for_pdf": None,
            }
        ],
        # Not a list of open locations: never read.
        "oa_locations_embargoed": [{"url_for_pdf": "https://embargo.example.org/1.pdf"}],
        "first_oa_location": None,
    }
    lookups = FakeLookups(openalex, unpaywall)
    hosts = FakePdfHosts()

    result = await downloader.process_doi(hosts, lookups, "10.1/landing-only")

    assert hosts.requested == []
    assert set(lookups.hosts) <= LOOKUP_HOSTS
    assert result.success is False
    assert result.outcome == "OPEN_NO_DIRECT_PDF"
    assert result.open_copy is None


@pytest.mark.asyncio
async def test_the_real_answers_never_ask_a_landing_page_or_a_closed_location(downloader):
    """Twelve locations are listed; ten have no direct address or are closed."""
    lookups = FakeLookups(openalex_answer(), unpaywall_answer())
    hosts = FakePdfHosts()  # every address answers HTML, so every candidate is tried

    result = await downloader.process_doi(hosts, lookups, DOI)

    assert hosts.requested == [PMC_PDF, REPOSITORY_PDF]
    assert result.success is False
    assert result.outcome == "PDF_NOT_FETCHED"
    assert (result.copies_listed, result.copies_tried) == (2, 2)


# ------------------------------------------------------------- 2. the ranking


def test_copies_are_ranked_published_then_accepted_then_submitted_then_unlabelled():
    from scholar_pdf.open_copies import open_copies

    def location(name: str, version: str | None) -> dict:
        return {"is_oa": True, "pdf_url": f"https://{name}.example.org/a.pdf", "version": version}

    openalex = {
        "best_oa_location": location("oa-submitted", "submittedVersion"),
        "primary_location": location("oa-unlabelled", None),
        "locations": [
            location("oa-accepted", "acceptedVersion"),
            location("oa-published-1", "publishedVersion"),
            location("oa-published-2", "publishedVersion"),
        ],
    }
    unpaywall = {
        "best_oa_location": {"url_for_pdf": "https://up-published.example.org/a.pdf", "version": "publishedVersion"},
        "oa_locations": [
            {"url_for_pdf": "https://up-accepted.example.org/a.pdf", "version": "acceptedVersion"},
            {"url_for_pdf": "https://up-odd.example.org/a.pdf", "version": "somethingElse"},
        ],
    }

    copies = open_copies(openalex, unpaywall)

    assert [(urlsplit(c.url).hostname.split(".")[0], c.version) for c in copies] == [
        ("oa-published-1", "publishedVersion"),
        ("oa-published-2", "publishedVersion"),
        ("up-published", "publishedVersion"),
        ("oa-accepted", "acceptedVersion"),
        ("up-accepted", "acceptedVersion"),
        ("oa-submitted", "submittedVersion"),
        ("oa-unlabelled", "unknown"),
        ("up-odd", "unknown"),
    ]


@pytest.mark.asyncio
async def test_the_first_address_failing_leads_to_the_second(downloader):
    lookups = FakeLookups(openalex_answer(), unpaywall_answer())
    hosts = FakePdfHosts({PMC_PDF: HTML, REPOSITORY_PDF: pdf_bytes()})

    result = await downloader.process_doi(hosts, lookups, DOI)

    assert hosts.requested == [PMC_PDF, REPOSITORY_PDF]
    assert result.success is True, result.error_message
    assert result.open_copy.url == REPOSITORY_PDF
    assert result.open_copy.version == "submittedVersion"  # the label follows the copy taken
    assert (result.copies_listed, result.copies_tried) == (2, 2)


@pytest.mark.asyncio
async def test_a_refused_first_address_leads_to_the_second(downloader, monkeypatch):
    monkeypatch.setattr(AsyncPDFDownloader.download_pdf.retry, "wait", wait_none())
    refused = aiohttp.ClientResponseError(
        request_info=MagicMock(), history=(), status=403, message="Forbidden"
    )
    lookups = FakeLookups(openalex_answer(), unpaywall_answer())
    hosts = FakePdfHosts({PMC_PDF: refused, REPOSITORY_PDF: pdf_bytes()})

    result = await downloader.process_doi(hosts, lookups, DOI)

    assert list(dict.fromkeys(hosts.requested)) == [PMC_PDF, REPOSITORY_PDF]
    assert result.success is True, result.error_message
    assert result.open_copy.url == REPOSITORY_PDF


@pytest.mark.asyncio
async def test_at_most_three_listed_addresses_are_tried(downloader):
    from scholar_pdf.open_copies import MAX_OPEN_COPIES_TRIED

    addresses = [f"https://repo{n}.example.org/paper.pdf" for n in range(5)]
    openalex = {
        "open_access": {"is_oa": True},
        "locations": [
            {"is_oa": True, "pdf_url": address, "version": "acceptedVersion"} for address in addresses
        ],
    }
    lookups = FakeLookups(openalex, closed_unpaywall())
    hosts = FakePdfHosts()

    result = await downloader.process_doi(hosts, lookups, "10.1/many")

    assert MAX_OPEN_COPIES_TRIED == 3
    assert hosts.requested == addresses[:3]
    assert result.success is False
    assert result.outcome == "PDF_NOT_FETCHED" and result.status == "FAILED"
    assert (result.copies_listed, result.copies_tried) == (5, 3)
    assert "3 of 5" in result.error_message


# ------------------------------------------------------- 3. the three outcomes


@pytest.mark.asyncio
async def test_both_lookups_failing_is_a_failed_lookup_not_a_missing_copy(downloader):
    lookups = FakeLookups(
        ProviderError("openalex-pdf", "HTTP request failed", status_code=503),
        ProviderTimeoutError("openalex-pdf", "Request timed out after 30s"),
    )
    hosts = FakePdfHosts()

    result = await downloader.process_doi(hosts, lookups, DOI)

    assert result.success is False
    assert result.outcome == "LOOKUP_FAILED"
    assert result.status == "UNRESOLVED" and result.access_status == "UNRESOLVED"
    assert [(look.provider, look.state, look.http_status, look.error_kind) for look in result.lookups] == [
        ("openalex", "FAILED", 503, "ProviderError"),
        ("unpaywall", "FAILED", None, "ProviderTimeoutError"),
    ]
    assert "OpenAlex failed (HTTP 503)" in result.error_message
    assert "Unpaywall failed (timed out)" in result.error_message
    assert "again later" in result.error_message
    assert "not a paywall determination" in result.error_message
    assert hosts.requested == []


@pytest.mark.asyncio
async def test_one_lookup_failing_while_the_other_lists_nothing_is_a_failed_lookup(downloader):
    lookups = FakeLookups(
        ProviderError("openalex-pdf", "Rate limit exceeded", status_code=429),
        closed_unpaywall(),
    )
    hosts = FakePdfHosts()

    result = await downloader.process_doi(hosts, lookups, "10.1/closed")

    assert result.outcome == "LOOKUP_FAILED"
    assert "OpenAlex failed (HTTP 429)" in result.error_message
    assert "Unpaywall lists no open copy" in result.error_message
    assert "incomplete" in result.error_message
    assert hosts.requested == []


@pytest.mark.asyncio
async def test_open_without_a_direct_address_says_so_and_names_the_landing_page(downloader):
    openalex = without_address(without_address(openalex_answer(), PMC_PDF), REPOSITORY_PDF)
    unpaywall = without_address(without_address(unpaywall_answer(), PMC_PDF), REPOSITORY_PDF)
    lookups = FakeLookups(openalex, unpaywall)
    hosts = FakePdfHosts()

    result = await downloader.process_doi(hosts, lookups, DOI)

    assert result.success is False
    assert result.outcome == "OPEN_NO_DIRECT_PDF"
    assert result.status == "UNRESOLVED" and result.access_status == "VERIFIED_OPEN_ACCESS"
    assert "open access" in result.error_message
    assert "no direct PDF address" in result.error_message
    assert "https://doi.org/10.7717/peerj.4375" in result.error_message  # where to get it by hand
    assert "scholar-pdf ingest" in result.error_message
    assert hosts.requested == []  # the landing page is named, never requested


@pytest.mark.asyncio
async def test_no_open_copy_listed_says_so(downloader):
    lookups = FakeLookups(closed_openalex(), closed_unpaywall())
    hosts = FakePdfHosts()

    result = await downloader.process_doi(hosts, lookups, "10.1/closed")

    assert result.success is False
    assert result.outcome == "NO_OPEN_COPY_LISTED"
    assert result.status == "UNRESOLVED" and result.access_status == "UNRESOLVED"
    assert "OpenAlex lists no open copy" in result.error_message
    assert "Unpaywall lists no open copy" in result.error_message
    assert "not a paywall determination" in result.error_message
    assert hosts.requested == []


@pytest.mark.asyncio
async def test_a_doi_the_services_do_not_know_is_an_answer_not_a_failure(downloader):
    lookups = FakeLookups(not_found("openalex-pdf"), not_found("openalex-pdf"))
    hosts = FakePdfHosts()

    result = await downloader.process_doi(hosts, lookups, "10.1/unknown")

    assert result.outcome == "NO_OPEN_COPY_LISTED"
    assert [(look.provider, look.state, look.http_status) for look in result.lookups] == [
        ("openalex", "NOT_FOUND", 404),
        ("unpaywall", "NOT_FOUND", 404),
    ]
    assert "OpenAlex does not know this DOI" in result.error_message
    assert "Unpaywall does not know this DOI" in result.error_message


@pytest.mark.asyncio
async def test_the_three_outcomes_have_three_different_messages(downloader):
    async def message(openalex, unpaywall) -> str:
        result = await downloader.process_doi(FakePdfHosts(), FakeLookups(openalex, unpaywall), "10.1/x")
        return result.error_message

    failed = await message(
        ProviderError("openalex-pdf", "x", status_code=500),
        ProviderError("openalex-pdf", "x", status_code=500),
    )
    landing_only = await message(
        {"open_access": {"is_oa": True}, "best_oa_location": {"is_oa": True, "landing_page_url": "https://doi.org/10.1/x"}},
        {"is_oa": True, "oa_locations": [{"url_for_landing_page": "https://doi.org/10.1/x"}]},
    )
    none_listed = await message(closed_openalex(), closed_unpaywall())

    assert len({failed, landing_only, none_listed}) == 3
    assert failed.startswith("Lookup failed")
    assert landing_only.startswith("Open access, but no direct PDF address is listed")
    assert none_listed.startswith("No open copy is listed")


@pytest.mark.asyncio
async def test_a_failed_lookup_never_puts_the_contact_address_in_a_message(downloader):
    leaking = ProviderError(
        "openalex-pdf",
        f"Network communication error: https://api.openalex.org/works/x?mailto={TEST_CONTACT}",
    )
    lookups = FakeLookups(leaking, leaking)

    result = await downloader.process_doi(FakePdfHosts(), lookups, "10.1/x")

    assert result.outcome == "LOOKUP_FAILED"
    assert TEST_CONTACT not in result.error_message
    assert all(TEST_CONTACT not in str(look) for look in result.lookups)


@pytest.mark.asyncio
async def test_an_answer_that_is_not_a_json_object_is_a_failed_lookup(downloader):
    lookups = FakeLookups(["not", "an", "object"], closed_unpaywall())

    result = await downloader.process_doi(FakePdfHosts(), lookups, "10.1/x")

    assert result.outcome == "LOOKUP_FAILED"
    assert result.lookups[0].state == "FAILED"
    assert "OpenAlex failed" in result.error_message


# -------------------------------------------- 4. what the command sends is unchanged


@pytest.mark.asyncio
async def test_unpaywall_is_asked_only_when_openalex_lists_no_address(downloader):
    with_address = FakeLookups(openalex_answer(), unpaywall_answer())
    await downloader.process_doi(FakePdfHosts({PMC_PDF: pdf_bytes()}), with_address, DOI)
    assert with_address.hosts == ["api.openalex.org"]

    without = FakeLookups(closed_openalex(), closed_unpaywall())
    await downloader.process_doi(FakePdfHosts(), without, "10.1/closed")
    assert without.hosts == ["api.openalex.org", "api.unpaywall.org"]
    # One request per service and DOI, to these two addresses.
    assert without.calls == [
        "https://api.openalex.org/works/https://doi.org/10.1/closed",
        "https://api.unpaywall.org/v2/10.1/closed",
    ]


# ------------------------------------------------------------- the command


def _unresolved(outcome: str, status: str = "UNRESOLVED") -> DownloadResult:
    return DownloadResult(
        doi="10.1/x", success=False, status=status, outcome=outcome, error_message=f"message for {outcome}"
    )


@pytest.mark.parametrize(
    ("outcome", "status", "label", "exit_code"),
    [
        ("LOOKUP_FAILED", "UNRESOLVED", "Lookup failed", 3),
        ("PDF_NOT_FETCHED", "FAILED", "Failed", 1),
        ("OPEN_NO_DIRECT_PDF", "UNRESOLVED", "No direct PDF", 4),
        ("NO_OPEN_COPY_LISTED", "UNRESOLVED", "No open copy", 5),
    ],
)
def test_the_command_says_which_outcome_in_words_and_in_its_exit_code(
    outcome, status, label, exit_code, tmp_path
):
    with patch(
        "scholar_pdf.cli.AsyncPDFDownloader.process_doi", new_callable=AsyncMock
    ) as process_doi:
        process_doi.return_value = _unresolved(outcome, status)
        result = runner.invoke(app, ["download", "--doi", "10.1/x", "--output", str(tmp_path)])

    text = " ".join(result.output.split())
    assert result.exit_code == exit_code, text
    assert label in text


def test_the_commands_exit_code_for_several_dois_names_the_most_urgent_outcome(tmp_path):
    def run(*outcomes: str) -> int:
        results = [
            DownloadResult(doi=f"10.1/{n}", success=True, status="ACQUIRED", outcome="ACQUIRED", file_path=tmp_path / "a.pdf")
            if outcome == "ACQUIRED"
            else _unresolved(outcome)
            for n, outcome in enumerate(outcomes)
        ]
        with patch(
            "scholar_pdf.cli.AsyncPDFDownloader.process_doi", new_callable=AsyncMock
        ) as process_doi:
            process_doi.side_effect = results
            args = ["download", "--output", str(tmp_path)]
            for n in range(len(outcomes)):
                args += ["--doi", f"10.1/{n}"]
            return runner.invoke(app, args).exit_code

    assert run("ACQUIRED", "ACQUIRED") == 0
    assert run("ACQUIRED", "NO_OPEN_COPY_LISTED") == 5
    assert run("NO_OPEN_COPY_LISTED", "OPEN_NO_DIRECT_PDF") == 4
    assert run("OPEN_NO_DIRECT_PDF", "PDF_NOT_FETCHED", "NO_OPEN_COPY_LISTED") == 1
    assert run("PDF_NOT_FETCHED", "LOOKUP_FAILED", "ACQUIRED") == 3


def test_the_command_downloads_the_real_answers_offline_and_labels_the_copy(tmp_path, monkeypatch):
    lookups = FakeLookups(openalex_answer(), unpaywall_answer())
    hosts = FakePdfHosts({PMC_PDF: pdf_bytes()})
    monkeypatch.setattr("scholar_search.http_client.AcademicHttpClient", lambda **kwargs: lookups)
    monkeypatch.setattr(aiohttp, "ClientSession", lambda: hosts)

    result = runner.invoke(app, ["download", "--doi", DOI, "--output", str(tmp_path / "out")])

    text = " ".join(result.output.split())
    assert result.exit_code == 0, text
    assert len(list((tmp_path / "out").glob("DOC-*.pdf"))) == 1
    assert "publishedVersion" in text and "cc-by" in text
    assert hosts.requested == [PMC_PDF]
    assert set(lookups.hosts) <= LOOKUP_HOSTS


def test_the_command_reports_a_failed_lookup_offline_with_exit_code_3(tmp_path, monkeypatch):
    failing = ProviderError("openalex-pdf", "HTTP request failed", status_code=503)
    lookups = FakeLookups(failing, failing)
    hosts = FakePdfHosts()
    monkeypatch.setattr("scholar_search.http_client.AcademicHttpClient", lambda **kwargs: lookups)
    monkeypatch.setattr(aiohttp, "ClientSession", lambda: hosts)

    result = runner.invoke(app, ["download", "--doi", DOI, "--output", str(tmp_path / "out")])

    text = " ".join(result.output.split())
    assert result.exit_code == 3, text
    assert "Lookup failed" in text
    assert hosts.requested == []
    assert not list((tmp_path / "out").glob("*.pdf"))


# ------------------------------------------------------------------ ingest


@pytest.mark.asyncio
async def test_ingest_keeps_a_failed_lookup_on_its_result(downloader, tmp_path):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(pdf_bytes())
    failing = ProviderError("openalex-pdf", "HTTP request failed", status_code=503)
    lookups = FakeLookups(failing, failing)

    result = await downloader.ingest_pdf(lookups, pdf, DOI)

    assert result.success is True  # the file is the researcher's own; it is still stored
    assert [(look.provider, look.state, look.http_status) for look in result.lookups] == [
        ("openalex", "FAILED", 503),
        ("unpaywall", "FAILED", 503),
    ]


def test_the_ingest_command_says_when_the_lookup_failed(tmp_path, monkeypatch):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(pdf_bytes())
    failing = ProviderError("openalex-pdf", "HTTP request failed", status_code=503)
    lookups = FakeLookups(failing, failing)
    monkeypatch.setattr("scholar_search.http_client.AcademicHttpClient", lambda **kwargs: lookups)

    result = runner.invoke(app, ["ingest", str(pdf), "--doi", DOI, "--output", str(tmp_path / "out")])

    text = " ".join(result.output.split())
    assert result.exit_code == 0, text
    assert "Successfully ingested" in text
    assert "OpenAlex failed (HTTP 503)" in text
