from __future__ import annotations

import asyncio
import errno
import hashlib
import logging
import os
import shutil
import tempfile
from dataclasses import dataclass, replace
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

import aiohttp
from scholar_search.http_client import RETRY_AFTER_CAP, retry_after_seconds
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)
from yarl import URL

from .config import openalex_key, require_contact_email, settings, user_agent
from .identity import check_identity
from .manifest import MANIFEST_NOT_WRITTEN, append_row, manifest_row
from .open_copies import (
    ACQUIRED,
    ANSWERED,
    FAILED,
    MAX_OPEN_COPIES_TRIED,
    NOT_ASKED,
    NOT_FOUND,
    PDF_NOT_FETCHED,
    LookupOutcome,
    OpenCopy,
    lists_open,
    not_asked_note,
    open_copies,
    says_closed,
    unresolved,
)
from .publisher_patterns import (
    is_proxied_url,
    rewrite_via_proxy,
)
from .validator import check_failure, is_valid_pdf, pdf_checks, validate_pdf_structure

if TYPE_CHECKING:
    from scholar_search.http_client import AcademicHttpClient

logger = logging.getLogger(__name__)

#: The access status of a file fetched through the parked institutional gateway
#: (a caller passing one explicitly): never open access (M12a item 25, PDF-12).
INSTITUTIONAL_ACCESS = "INSTITUTIONAL_ACCESS"
#: The access status of a file the researcher gave (``ingest``), as E1 names it.
USER_PROVIDED = "USER_PROVIDED"
#: The outcome of an ``ingest`` that stored nothing.
NOT_STORED = "NOT_STORED"


# --------------------------------------------------------------- one request to a PDF address


def _public_url(value: object) -> str | None:
    """An address as text, without any ``user:password@`` part; ``None`` if it is not one."""
    if not isinstance(value, (str, URL)):
        return None
    url = value if isinstance(value, URL) else URL(value)
    if url.user is not None or url.password is not None:
        url = url.with_user(None)
    return str(url)


@dataclass
class FetchAttempt:
    """One request to a PDF address, as the manifest records it (Part K items 6 and 8).

    Never holds a lookup request: those carry the contact e-mail and the OpenAlex key.
    """

    #: The address asked.
    url: str
    #: ``open_location`` (an address a provider lists) or ``institutional_gateway`` (parked).
    route: str = "open_location"
    http_status: int | None = None
    #: The address that answered, after redirects.
    final_url: str | None = None
    #: Each address redirected from, in order.
    redirects: tuple[str, ...] = ()
    content_type: str | None = None
    #: Why the request gave no file, in words (never the error's own text).
    error: str | None = None
    #: The checks on the bytes, by name (``validator.PdfCheck``), when bytes came.
    checks: tuple = ()
    #: Whether this request repeated the one before it to the same address.
    retry: bool = False

    @property
    def host(self) -> str:
        """The host (and port, when given) the request went to."""
        return urlsplit(self.url).netloc.rsplit("@", 1)[-1]

    def answer(self, stored: bool = False) -> str:
        """What the address answered, in words: ``stored``, the error, or the status."""
        if stored:
            return "stored"
        if self.error:
            return self.error
        return f"HTTP {self.http_status}" if self.http_status is not None else "answered"

    def observe(self, response: object) -> None:
        """Keep the status, the final address, the redirects and the content type."""
        status = getattr(response, "status", None)
        self.http_status = status if isinstance(status, int) else None
        self.final_url = _public_url(getattr(response, "url", None))
        history = getattr(response, "history", ())
        if isinstance(history, (tuple, list)):
            self.redirects = tuple(
                url for url in (_public_url(getattr(hop, "url", None)) for hop in history) if url
            )
        headers = getattr(response, "headers", None)
        content_type = headers.get("Content-Type") if hasattr(headers, "get") else None
        self.content_type = content_type if isinstance(content_type, str) else None


def _retry_after(error: BaseException) -> float | None:
    headers = getattr(error, "headers", None)
    value = headers.get("Retry-After") if hasattr(headers, "get") else None
    return retry_after_seconds(value) if isinstance(value, str) else None


def _transient(error: BaseException) -> bool:
    """Whether asking the same address again can give a different answer (PDF-06).

    Retried: a connection error, a timeout, a 5xx, and a 429 whose ``Retry-After``
    is within ``RETRY_AFTER_CAP`` (the search kit's cap, M12a item 14). Not
    retried: every other answer, 400, 401, 403, 404, 410 and 451 among them, and
    a 429 that asks for a longer wait or gives none ("try later").
    """
    if isinstance(error, aiohttp.ClientResponseError):
        if error.status >= 500:
            return True
        if error.status == 429:
            wait = _retry_after(error)
            return wait is not None and wait <= RETRY_AFTER_CAP
        return False
    return isinstance(error, (aiohttp.ClientError, asyncio.TimeoutError))


_BACKOFF = wait_exponential(multiplier=1, min=2, max=10)


# ------------------------------------------------------------------ portable writes (PDF-03)

#: ``os.link`` errors that mean "no hard links here", where a copy is the fallback.
_NO_HARD_LINK_ERRNOS = frozenset(
    code
    for code in (
        errno.EPERM,
        errno.EXDEV,
        errno.EMLINK,
        errno.EOPNOTSUPP,
        getattr(errno, "ENOTSUP", errno.EOPNOTSUPP),
        getattr(errno, "ENOSYS", errno.EOPNOTSUPP),
    )
)
#: Their Windows equivalents: invalid function (FAT, exFAT), not the same device,
#: not supported, too many links.
_NO_HARD_LINK_WINERRORS = frozenset({1, 17, 50, 1142})


def _no_hard_links(error: OSError) -> bool:
    winerror = getattr(error, "winerror", None)
    if winerror is not None:
        return winerror in _NO_HARD_LINK_WINERRORS
    return error.errno in _NO_HARD_LINK_ERRNOS


def _copy_exclusive(source: Path, final: Path, digest: str) -> None:
    """Copy ``source`` to a new ``final`` (``O_EXCL``), fsync it, and check its hash.

    ``FileExistsError`` when ``final`` exists: nothing is overwritten. On any
    other failure the partly written ``final`` is removed.
    """
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    descriptor = os.open(final, flags, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as target, source.open("rb") as origin:
            shutil.copyfileobj(origin, target, 1024 * 1024)
            target.flush()
            os.fsync(target.fileno())
        if AsyncPDFDownloader._digest(final) != digest:
            raise OSError("the copied file does not match the validated bytes")
    except BaseException:
        final.unlink(missing_ok=True)
        raise


def _retry_wait(state: RetryCallState) -> float:
    """A 429's own ``Retry-After`` (within the cap), else 2 to 10 s of backoff."""
    error = state.outcome.exception() if state.outcome is not None else None
    if isinstance(error, aiohttp.ClientResponseError) and error.status == 429:
        wait = _retry_after(error)
        if wait is not None:
            return wait
    return _BACKOFF(state)


def _year(value: object) -> str:
    """A year as text, or ``""`` when the service gives none: never ``'None'`` (PDF-18)."""
    return "" if value is None or isinstance(value, bool) else str(value).strip()


def fetch_failure(error: BaseException) -> str:
    """Why a PDF address gave no file, in words; never the error's own text."""
    if isinstance(error, aiohttp.ClientResponseError):
        if error.status == 429:
            wait = _retry_after(error)
            asked = f", it asks for {wait:.0f} s" if wait is not None else ""
            return f"HTTP 429: the host asks to try later{asked}"
        return f"HTTP {error.status}"
    if isinstance(error, (asyncio.TimeoutError, aiohttp.ServerTimeoutError)):
        return "timed out"
    if isinstance(error, aiohttp.ClientError):
        return f"network error ({type(error).__name__})"
    return f"failed ({type(error).__name__})"


@dataclass
class DownloadResult:
    doi: str
    success: bool
    file_path: Path | None = None
    error_message: str | None = None
    # Deprecated compatibility projection.  Use access_status/status for new
    # callers; a successful HTTP response alone never sets this to True.
    was_oa: bool = False
    metadata: dict | None = None
    access_status: str | None = None
    status: str | None = None
    # H-pdf-resolver-locations. ``outcome`` says why: ACQUIRED, PDF_NOT_FETCHED
    # (addresses were listed, none gave a PDF), LOOKUP_FAILED, OPEN_NO_DIRECT_PDF
    # or NO_OPEN_COPY_LISTED. ``status`` keeps its three values.
    outcome: str | None = None
    # The copy the file came from: its version, licence, host, source and provider.
    open_copy: OpenCopy | None = None
    # What each service asked answered (never the request itself).
    lookups: tuple[LookupOutcome, ...] = ()
    copies_listed: int = 0
    copies_tried: int = 0
    # Part K: every request made to a PDF address for this DOI, retries included.
    attempts: tuple[FetchAttempt, ...] = ()
    # Part K item 7 (PDF-12): the candidate that produced the bytes, and its route
    # (``open_location`` or ``institutional_gateway``); ``None`` when no file came.
    source_url: str | None = None
    route: str | None = None
    # Part K item 9 (PDF-22): "doi found", "title found", "not found: check it"
    # or "not checked" (no PyMuPDF). Never blocks a file.
    identity: str | None = None
    # Part K item 8 (PDF-07): the caller's study id, the stored file's size and
    # SHA-256, the checks on it (``validator.PdfCheck``; on ``attempts`` for a
    # download), and whether this call created the file (``new_file``).
    study_id: str | None = None
    size: int | None = None
    sha256: str | None = None
    checks: tuple = ()
    new_file: bool = False

    @property
    def request_count(self) -> int:
        """How many requests went to PDF addresses for this DOI, retries included."""
        return len(self.attempts)

    def request_hosts(self) -> dict[str, int]:
        """How many of those requests went to each host."""
        return dict(Counter(attempt.host for attempt in self.attempts))

    def request_lines(self) -> list[str]:
        """Each PDF request in words, ``<host>: <answer>``, in the order sent."""
        lines = []
        for index, attempt in enumerate(self.attempts):
            stored = (
                self.success
                and index == len(self.attempts) - 1
                and attempt.url == self.source_url
            )
            retry = " (retry)" if attempt.retry else ""
            lines.append(f"{attempt.host}: {attempt.answer(stored)}{retry}")
        return lines


@dataclass(frozen=True)
class _Lookup:
    """One service's answer for one DOI: the outcome, and the payload when it answered."""

    outcome: LookupOutcome
    payload: dict | None = None


class AsyncPDFDownloader:
    """Asynchronous PDF Downloader using aiohttp."""

    def __init__(
        self,
        output_dir: Path | None = None,
        proxy_url: str | None = None,
        proxy_style: str = "auto",
        structural_validation: bool | None = None,
        institutional_gateway_url: str | None = None,
        forward_proxy_url: str | None = None,
        manifest_path: Path | None = None,
    ):
        self.output_dir = output_dir or settings.download_dir
        # Part K item 8: one JSON line per DOI asked, when the caller gives a path.
        self.manifest_path = Path(manifest_path) if manifest_path is not None else None
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_downloads)
        # ``proxy_url`` is retained as a deprecated alias for the historical
        # gateway configuration.  Parked code (M12a item 25): only a gateway the
        # caller passes is used; ``PROXY_URL`` is never read here (K0), and the
        # production commands refuse one.
        self.institutional_gateway_url = (
            institutional_gateway_url
            if institutional_gateway_url is not None
            else proxy_url
        ) or ""
        self.forward_proxy_url = forward_proxy_url or ""
        self.proxy_url = self.institutional_gateway_url
        self.proxy_style = proxy_style or settings.proxy_style or "auto"
        self.structural_validation = (
            settings.pdf_structural_validation
            if structural_validation is None
            else structural_validation
        )
        if (
            self.institutional_gateway_url
            and self.forward_proxy_url
            and self.institutional_gateway_url == self.forward_proxy_url
        ):
            raise ValueError(
                "institutional_gateway_url and forward_proxy_url must be distinct"
            )

    def _content_path(self, digest: str) -> Path:
        """Return the authoritative content/identity-addressed final path."""

        return self.output_dir / f"DOC-{digest[:32]}.pdf"

    @staticmethod
    def _digest(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _candidate_is_valid(self, path: Path) -> bool:
        if not is_valid_pdf(path):
            return False
        return not self.structural_validation or validate_pdf_structure(path)

    def _new_staging_path(self) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(
            prefix=".pdf-acquisition-", suffix=".tmp", dir=self.output_dir
        )
        os.close(descriptor)
        staging = Path(name)
        staging.unlink(missing_ok=True)
        return staging

    def _promote_staging(self, staging: Path, final: Path) -> bool:
        """Publish a validated file without replacing a concurrent writer."""

        digest = self._digest(staging)
        if final.is_symlink():
            raise OSError("content destination must not be a symlink")
        try:
            if staging.resolve(strict=True) == final.resolve(strict=True):
                return True
        except OSError:
            pass
        final.parent.mkdir(parents=True, exist_ok=True)
        if final.exists():
            if (
                final.stat().st_size != staging.stat().st_size
                or self._digest(final) != digest
                or not self._candidate_is_valid(final)
            ):
                raise OSError("content-addressed destination is occupied")
            staging.unlink(missing_ok=True)
            return False
        try:
            try:
                # A hard link publishes the already-validated inode atomically and
                # cannot overwrite a destination created by another process.
                os.link(staging, final)
            except FileExistsError:
                raise
            except OSError as error:
                # PDF-03: FAT or exFAT drives and some network shares have no hard
                # links. An exclusive-create copy with fsync still never overwrites.
                if not _no_hard_links(error):
                    raise
                _copy_exclusive(staging, final, digest)
        except FileExistsError:
            if (
                final.is_symlink()
                or final.stat().st_size != staging.stat().st_size
                or self._digest(final) != digest
                or not self._candidate_is_valid(final)
            ):
                raise OSError("content-addressed destination is occupied") from None
            staging.unlink(missing_ok=True)
            return False
        staging.unlink(missing_ok=True)
        return True

    def _promote_candidate(self, staging: Path) -> tuple[Path, bool]:
        """Promote validated bytes to their content identity path."""

        digest = self._digest(staging)
        final = self._content_path(digest)
        return final, self._promote_staging(staging, final)

    @retry(
        wait=_retry_wait,
        stop=stop_after_attempt(3),
        retry=retry_if_exception(_transient),
        reraise=True,
    )
    async def download_pdf(
        self,
        session: aiohttp.ClientSession,
        url: str,
        dest_path: Path,
        proxy_url: str = "",
        forward_proxy_url: str | None = None,
        attempts: list[FetchAttempt] | None = None,
        route: str = "open_location",
    ) -> bool:
        """Download, validate, and atomically publish to ``dest_path``.

        Only a transient failure is retried (``_transient``, PDF-06). Each
        request, retries included, is appended to ``attempts`` when given.
        """
        record = FetchAttempt(url=_public_url(url) or url, route=route)
        if attempts is not None:
            record.retry = bool(attempts) and attempts[-1].url == record.url
            attempts.append(record)
        # The app names itself and its contact (K0, M12a item 27), never a browser.
        headers = {
            "User-Agent": user_agent(),
            "Accept": "application/pdf,*/*;q=0.8",
        }
        timeout = aiohttp.ClientTimeout(total=settings.download_timeout)
        transport_proxy = (
            forward_proxy_url if forward_proxy_url is not None else proxy_url
        ).strip()
        staging = self._new_staging_path()
        if dest_path.is_symlink():
            staging.unlink(missing_ok=True)
            raise OSError("destination must not be a symlink")
        try:
            try:
                async with (
                    self.semaphore,
                    session.get(
                        url,
                        headers=headers,
                        timeout=timeout,
                        allow_redirects=True,
                        proxy=transport_proxy or None,
                    ) as response,
                ):
                    record.observe(response)
                    response.raise_for_status()
                    with staging.open("wb") as stream:
                        async for chunk in response.content.iter_chunked(8192):
                            stream.write(chunk)
                        stream.flush()
                        os.fsync(stream.fileno())
            except Exception as error:
                record.error = fetch_failure(error)
                raise

            # Each check by name (PDF-17): a short genuine PDF is "below the
            # size floor", not "invalid".
            record.checks = pdf_checks(staging, structural=self.structural_validation)
            failure = check_failure(record.checks)
            if failure is not None:
                record.error = failure
                return False
            self._promote_staging(staging, dest_path)
            return True
        finally:
            staging.unlink(missing_ok=True)

    async def _lookup(
        self, provider: str, http_client: AcademicHttpClient, doi: str
    ) -> _Lookup:
        """Ask one service about one DOI and keep what happened.

        One request, as before. A 404 is an answer (the service does not know
        the DOI); any other error or a body that is not a JSON object is a
        failed lookup, kept with its HTTP status or its error's class name and
        never with the error's text, which can hold the request address (with
        the contact e-mail or the OpenAlex key). Without ``SCHOLAR_OPENALEX_KEY``
        OpenAlex is not asked (``NOT_ASKED``, Part K item 4).
        """
        contact = require_contact_email()  # outside the try: a missing e-mail is refused, not a failed lookup
        if provider == "openalex":
            # Part K item 4: OpenAlex is asked only with its key, sent as its
            # ``api_key`` parameter (it no longer reads ``mailto``; the user
            # agent still names the contact). The key is never logged or kept.
            key = openalex_key()
            if not key:
                return _Lookup(LookupOutcome(provider, NOT_ASKED))
            url = f"https://api.openalex.org/works/https://doi.org/{doi}"
            params = {"api_key": key}
        else:
            url = f"https://api.unpaywall.org/v2/{doi}"
            params = {"email": contact}
        try:
            response = await http_client.get(
                url, params=params, headers={"User-Agent": user_agent()}
            )
            status = response.status_code
        except Exception as error:  # noqa: BLE001 - provider adapters vary
            status = getattr(error, "status_code", None)
            status = status if isinstance(status, int) else None
            kind = type(error).__name__
            logger.debug("%s lookup failed for %s: %s", provider, doi, kind)
            state = NOT_FOUND if status == 404 else FAILED
            return _Lookup(LookupOutcome(provider, state, status, kind))
        if status == 404:
            return _Lookup(LookupOutcome(provider, NOT_FOUND, status))
        payload = None
        if status == 200:
            try:
                payload = response.json()
            except ValueError:  # a body that is not JSON
                payload = None
        if not isinstance(payload, dict):
            kind = None if status != 200 else "NotAJsonObject"
            return _Lookup(LookupOutcome(provider, FAILED, status, kind))
        return _Lookup(LookupOutcome(provider, ANSWERED, status), payload)

    async def fetch_openalex_metadata(
        self, http_client: AcademicHttpClient, doi: str
    ) -> dict | None:
        """The OpenAlex answer, or ``None``. ``_lookup`` also says why there is none."""
        return (await self._lookup("openalex", http_client, doi)).payload

    async def fetch_unpaywall_metadata(
        self, http_client: AcademicHttpClient, doi: str
    ) -> dict | None:
        """The Unpaywall answer, or ``None``. ``_lookup`` also says why there is none."""
        return (await self._lookup("unpaywall", http_client, doi)).payload

    def extract_metadata(self, oa_data: dict, source: str) -> dict:
        metadata = {"title": "", "author": "", "year": ""}
        if source == "openalex":
            metadata["title"] = oa_data.get("title") or ""
            metadata["year"] = _year(oa_data.get("publication_year"))
            authorships = oa_data.get("authorships", [])
            if authorships:
                author_name = authorships[0].get("author", {}).get("display_name", "")
                # Get last name
                metadata["author"] = author_name.split(" ")[-1] if author_name else ""
        elif source == "unpaywall":
            metadata["title"] = oa_data.get("title") or ""
            metadata["year"] = _year(oa_data.get("year"))
            z_authors = oa_data.get("z_authors", [])
            if z_authors:
                metadata["author"] = (
                    z_authors[0].get("family")
                    or z_authors[0].get("name", "").split(" ")[-1]
                )
        return metadata

    @staticmethod
    def _provider_access_status(*payloads: dict | None) -> str:
        """Project only explicit provider OA evidence, never HTTP success.

        Explicit closed evidence (``is_oa: false``, ``oa_status: "closed"``)
        overrides a ``pdf_url`` in the same answer (Part K item 7, PDF-12), and
        a location its provider marks closed is never open evidence. This is
        the paper's status when no file came; a stored file takes the status of
        the location that produced its bytes (``process_doi``).
        """

        for payload in payloads:
            if not isinstance(payload, dict):
                continue
            if payload.get("restricted") is True and any(
                isinstance(payload.get(key), str) and payload[key].strip()
                for key in ("source", "publisher")
            ):
                return "RESTRICTED_CONFIRMED"
            if says_closed(payload):
                continue
            for location_key in ("best_oa_location", "primary_location"):
                location = payload.get(location_key)
                if (
                    isinstance(location, dict)
                    and location.get("is_oa") is not False
                    and (location.get("pdf_url") or location.get("url_for_pdf"))
                ):
                    return "VERIFIED_OPEN_ACCESS"
            if lists_open(payload) or payload.get("url_for_pdf"):
                return "VERIFIED_OPEN_ACCESS"
        return "UNRESOLVED"

    def _recorded(self, result: DownloadResult) -> DownloadResult:
        """Write the DOI's manifest row; no file is kept without it (Part K item 8).

        When the row cannot be written, a file this call created is removed and
        the DOI fails (``MANIFEST_NOT_WRITTEN``); a file stored by an earlier
        call (it has its own row) is kept.
        """
        if self.manifest_path is None:
            return result
        try:
            append_row(self.manifest_path, manifest_row(result, self.manifest_path))
            return result
        except OSError as error:
            note = ""
            if result.file_path is not None and result.new_file:
                result.file_path.unlink(missing_ok=True)
                note = "; the new file was removed"
            elif result.file_path is not None:
                note = "; the file stored by an earlier run is kept"
            message = f"The manifest row could not be written ({type(error).__name__}){note}."
            if result.error_message:
                message = f"{message} {result.error_message}"
            return replace(
                result,
                success=False,
                status="FAILED",
                outcome=MANIFEST_NOT_WRITTEN,
                file_path=None,
                new_file=False,
                error_message=message,
            )

    async def process_doi(
        self,
        session: aiohttp.ClientSession,
        http_client: AcademicHttpClient,
        doi: str,
        *,
        title: str | None = None,
        study_id: str | None = None,
    ) -> DownloadResult:
        """Resolve OA evidence and atomically acquire a PDF for one DOI.

        ``title`` (the caller's record) is looked for on the first pages, else
        the title the lookups give (Part K item 9). With a ``manifest_path``,
        one row is written for the DOI, with ``study_id`` (Part K item 8).
        """
        require_contact_email()  # refused before any request (MAILTO_NOT_SET)
        result = await self._process_doi(session, http_client, doi, title=title)
        return self._recorded(replace(result, study_id=study_id))

    async def _process_doi(
        self,
        session: aiohttp.ClientSession,
        http_client: AcademicHttpClient,
        doi: str,
        *,
        title: str | None = None,
    ) -> DownloadResult:
        try:
            # Both services are asked for every DOI, once each (decision
            # 2026-11-21, H-pdf-resolver-locations item 4, "Always ask both
            # services"), so the best copy is chosen across both lists.
            openalex = await self._lookup("openalex", http_client, doi)
            unpaywall = await self._lookup("unpaywall", http_client, doi)
            openalex_data, unpaywall_data = openalex.payload, unpaywall.payload
            lookups: tuple[LookupOutcome, ...] = (openalex.outcome, unpaywall.outcome)
            metadata: dict = {}
            if openalex_data:
                metadata = self.extract_metadata(openalex_data, "openalex")
            if unpaywall_data and not metadata.get("title"):
                metadata = self.extract_metadata(unpaywall_data, "unpaywall")

            # Every listed open location with a direct address, best version
            # first (M12a answer F3); a landing page is never an address.
            copies = open_copies(openalex_data, unpaywall_data)

            access_status = self._provider_access_status(openalex_data, unpaywall_data)
            if copies and access_status == "UNRESOLVED":
                # A location its provider marks open is that provider's evidence.
                access_status = "VERIFIED_OPEN_ACCESS"
            was_oa = access_status == "VERIFIED_OPEN_ACCESS"
            result = DownloadResult(
                doi=doi,
                success=False,
                was_oa=was_oa,
                access_status=access_status,
                metadata=metadata or None,
                lookups=lookups,
                copies_listed=len(copies),
            )
            if not copies:
                outcome, message = unresolved(
                    lookups, {"openalex": openalex_data, "unpaywall": unpaywall_data}
                )
                return replace(
                    result, status="UNRESOLVED", outcome=outcome, error_message=message
                )

            last_error: str | None = None
            tried = 0
            attempts: list[FetchAttempt] = []
            for copy in copies[:MAX_OPEN_COPIES_TRIED]:
                tried += 1
                # Only the provider's own open-access location: no guessed
                # publisher URL, whatever the setting says (K0, M12a items 24, 27).
                candidates: list[str] = [copy.url]
                if self.institutional_gateway_url and not is_proxied_url(
                    copy.url, self.institutional_gateway_url
                ):
                    # Parked gateway code (item 25): only when a caller passes one.
                    proxied = rewrite_via_proxy(
                        copy.url,
                        self.institutional_gateway_url,
                        style=self.proxy_style,
                    )
                    if proxied != copy.url:
                        candidates.append(proxied)

                for candidate in candidates:
                    candidate_path = self._new_staging_path()
                    route = "open_location" if candidate == copy.url else "institutional_gateway"
                    try:
                        try:
                            success = await self.download_pdf(
                                session,
                                candidate,
                                candidate_path,
                                forward_proxy_url=self.forward_proxy_url or None,
                                attempts=attempts,
                                route=route,
                            )
                        except Exception as error:  # noqa: BLE001 - any fetch failure
                            # Words, not the error's text (PDF-06; the address is on the attempt).
                            last_error = f"The listed address gave no PDF: {fetch_failure(error)}"
                            logger.debug("PDF candidate failed for %s: %s", doi, type(error).__name__)
                            continue
                        if not success:
                            last_error = (
                                "The listed address gave no PDF: "
                                f"{attempts[-1].error or 'not a valid PDF'}"
                            )
                            continue
                        identity = check_identity(
                            candidate_path, doi, title or metadata.get("title")
                        )
                        size = candidate_path.stat().st_size
                        digest = self._digest(candidate_path)
                        final_path, new_file = self._promote_candidate(candidate_path)
                        # The status follows the bytes (Part K item 7, PDF-12): an open
                        # location's own address is open access; the parked gateway is
                        # institutional access, never open access (M12a item 25).
                        opened = route == "open_location"
                        return replace(
                            result,
                            success=True,
                            file_path=final_path,
                            status="ACQUIRED",
                            outcome=ACQUIRED,
                            access_status=(
                                "VERIFIED_OPEN_ACCESS" if opened else INSTITUTIONAL_ACCESS
                            ),
                            was_oa=opened,
                            source_url=_public_url(candidate) or candidate,
                            route=route,
                            identity=identity,
                            size=size,
                            sha256=digest,
                            new_file=new_file,
                            # The label follows the bytes: a file fetched through
                            # the parked gateway is not that open location's copy.
                            open_copy=copy if candidate == copy.url else None,
                            copies_tried=tried,
                            attempts=tuple(attempts),
                        )
                    except Exception as error:  # noqa: BLE001 - storing the file failed
                        last_error = f"The PDF could not be stored: {type(error).__name__}: {error}"
                    finally:
                        candidate_path.unlink(missing_ok=True)

            message = last_error or "The listed address gave no PDF"
            if len(copies) > 1:
                message = f"{message} ({tried} of {len(copies)} listed addresses tried)"
            for lookup in lookups:
                if lookup.state == FAILED:
                    # The other service may list an address this run never saw.
                    message = (
                        f"{message}; {lookup.name} {lookup.failure()}, "
                        "so its list was not read"
                    )
                elif lookup.state == NOT_ASKED:
                    message = f"{message}; {not_asked_note(lookup)}"
            return replace(
                result,
                status="FAILED",
                outcome=PDF_NOT_FETCHED,
                copies_tried=tried,
                attempts=tuple(attempts),
                error_message=message,
            )
        except Exception as error:  # noqa: BLE001 - provider adapters vary
            return DownloadResult(
                doi=doi,
                success=False,
                was_oa=False,
                status="FAILED",
                access_status="UNRESOLVED",
                error_message=str(error),
            )

    async def download_batch(self, dois: list[str]) -> list[DownloadResult]:
        """Downloads a batch of DOIs concurrently and closes owned clients."""
        from scholar_search.http_client import AcademicHttpClient

        http_client = AcademicHttpClient(name="openalex-pdf", rate_limit=10)
        try:
            async with aiohttp.ClientSession() as session:
                tasks = [self.process_doi(session, http_client, doi) for doi in dois]
                return await asyncio.gather(*tasks)
        finally:
            await http_client.close()

    async def ingest_pdf(
        self,
        http_client: AcademicHttpClient,
        pdf_path: Path,
        doi: str,
        *,
        study_id: str | None = None,
    ) -> DownloadResult:
        """Atomically ingest a local PDF without overwriting existing bytes.

        The bytes are the researcher's own: the result's route is
        ``user_provided`` and its access status ``USER_PROVIDED`` (Part K item 7);
        with a ``manifest_path`` its row is written (item 8).
        """
        require_contact_email()  # the metadata lookups send it (MAILTO_NOT_SET)
        result = await self._ingest_pdf(http_client, pdf_path, doi)
        return self._recorded(replace(result, study_id=study_id))

    async def _ingest_pdf(
        self, http_client: AcademicHttpClient, pdf_path: Path, doi: str
    ) -> DownloadResult:
        if not pdf_path.exists():
            return DownloadResult(
                doi=doi,
                success=False,
                status="FAILED",
                outcome=NOT_STORED,
                access_status="UNRESOLVED",
                error_message="Provided PDF path does not exist.",
            )

        staging: Path | None = None
        try:
            openalex = await self._lookup("openalex", http_client, doi)
            openalex_data = openalex.payload
            lookups: tuple[LookupOutcome, ...] = (openalex.outcome,)
            unpaywall_data = None
            metadata: dict = {}
            if openalex_data:
                metadata = self.extract_metadata(openalex_data, "openalex")
            else:
                unpaywall = await self._lookup("unpaywall", http_client, doi)
                unpaywall_data = unpaywall.payload
                lookups = (*lookups, unpaywall.outcome)
                if unpaywall_data:
                    metadata = self.extract_metadata(unpaywall_data, "unpaywall")

            access_status = self._provider_access_status(openalex_data, unpaywall_data)
            staging = self._new_staging_path()
            shutil.copyfile(pdf_path, staging)
            checks = pdf_checks(staging, structural=self.structural_validation)
            failure = check_failure(checks)
            if failure is not None:
                return DownloadResult(
                    doi=doi,
                    success=False,
                    status="FAILED",
                    outcome=NOT_STORED,
                    access_status=access_status,
                    metadata=metadata or None,
                    error_message=f"The provided file was not stored: {failure}.",
                    lookups=lookups,
                    checks=checks,
                )
            identity = check_identity(staging, doi, metadata.get("title"))
            size = staging.stat().st_size
            digest = self._digest(staging)
            final_path, new_file = self._promote_candidate(staging)
            return DownloadResult(
                doi=doi,
                success=True,
                identity=identity,
                file_path=final_path,
                # The bytes are the researcher's, whatever the providers list (PDF-12).
                was_oa=False,
                status="ACQUIRED",
                outcome=ACQUIRED,
                access_status=USER_PROVIDED,
                route="user_provided",
                metadata=metadata or None,
                lookups=lookups,
                checks=checks,
                size=size,
                sha256=digest,
                new_file=new_file,
            )
        except Exception as error:  # noqa: BLE001 - provider adapters vary
            return DownloadResult(
                doi=doi,
                success=False,
                status="FAILED",
                outcome=NOT_STORED,
                access_status="UNRESOLVED",
                error_message=str(error),
            )
        finally:
            if staging is not None:
                staging.unlink(missing_ok=True)
