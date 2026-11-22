from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import shutil
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

import aiohttp
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import openalex_key, require_contact_email, settings, user_agent
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
    not_asked_note,
    open_copies,
    unresolved,
)
from .publisher_patterns import (
    is_proxied_url,
    rewrite_via_proxy,
)
from .validator import is_valid_pdf, validate_pdf_structure

if TYPE_CHECKING:
    from scholar_search.http_client import AcademicHttpClient

logger = logging.getLogger(__name__)


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
        use_smart_names: bool = False,
        proxy_url: str | None = None,
        proxy_style: str = "auto",
        structural_validation: bool | None = None,
        institutional_gateway_url: str | None = None,
        forward_proxy_url: str | None = None,
    ):
        self.output_dir = output_dir or settings.download_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_downloads)
        self.use_smart_names = use_smart_names
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

    def _safe_filename(self, doi: str, metadata: dict | None = None) -> str:
        """Converts a DOI to a safe filename, optionally using metadata."""
        if self.use_smart_names and metadata:
            title = metadata.get("title", "")
            author = metadata.get("author", "")
            year = metadata.get("year", "0000")

            if title and author:
                # Sanitize title and author
                safe_title = "".join(
                    c for c in title[:50] if c.isalnum() or c in (" ", "_")
                ).replace(" ", "_")
                safe_author = "".join(
                    c for c in author if c.isalnum() or c in (" ", "_")
                ).replace(" ", "_")
                return f"{year}_{safe_author}_{safe_title}.pdf"

        safe_doi = doi.replace("/", "_").replace("\\", "_").replace(":", "_")
        return f"{safe_doi}.pdf"

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
            # A hard link publishes the already-validated inode atomically and
            # cannot overwrite a destination created by another process.
            os.link(staging, final)
        except FileExistsError:
            if (
                final.is_symlink()
                or final.stat().st_size != staging.stat().st_size
                or self._digest(final) != digest
                or not self._candidate_is_valid(final)
            ):
                raise OSError("content-addressed destination is occupied")
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
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True,
    )
    async def download_pdf(
        self,
        session: aiohttp.ClientSession,
        url: str,
        dest_path: Path,
        proxy_url: str = "",
        forward_proxy_url: str | None = None,
    ) -> bool:
        """Download, validate, and atomically publish to ``dest_path``."""
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
                response.raise_for_status()
                with staging.open("wb") as stream:
                    async for chunk in response.content.iter_chunked(8192):
                        stream.write(chunk)
                    stream.flush()
                    os.fsync(stream.fileno())

            if not self._candidate_is_valid(staging):
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
            metadata["year"] = str(oa_data.get("publication_year", ""))
            authorships = oa_data.get("authorships", [])
            if authorships:
                author_name = authorships[0].get("author", {}).get("display_name", "")
                # Get last name
                metadata["author"] = author_name.split(" ")[-1] if author_name else ""
        elif source == "unpaywall":
            metadata["title"] = oa_data.get("title") or ""
            metadata["year"] = str(oa_data.get("year", ""))
            z_authors = oa_data.get("z_authors", [])
            if z_authors:
                metadata["author"] = (
                    z_authors[0].get("family")
                    or z_authors[0].get("name", "").split(" ")[-1]
                )
        return metadata

    @staticmethod
    def _provider_access_status(*payloads: dict | None) -> str:
        """Project only explicit provider OA evidence, never HTTP success."""

        for payload in payloads:
            if not isinstance(payload, dict):
                continue
            if payload.get("restricted") is True and any(
                isinstance(payload.get(key), str) and payload[key].strip()
                for key in ("source", "publisher")
            ):
                return "RESTRICTED_CONFIRMED"
            for location_key in ("best_oa_location", "primary_location"):
                location = payload.get(location_key)
                if isinstance(location, dict) and (
                    location.get("pdf_url") or location.get("url_for_pdf")
                ):
                    return "VERIFIED_OPEN_ACCESS"
            open_access = payload.get("open_access")
            if isinstance(open_access, dict) and open_access.get("is_oa") is True:
                return "VERIFIED_OPEN_ACCESS"
            if payload.get("is_oa") is True or payload.get("url_for_pdf"):
                return "VERIFIED_OPEN_ACCESS"
            if payload.get("oa_status") in {"gold", "green", "hybrid", "bronze"}:
                return "VERIFIED_OPEN_ACCESS"
        return "UNRESOLVED"

    async def process_doi(
        self, session: aiohttp.ClientSession, http_client: AcademicHttpClient, doi: str
    ) -> DownloadResult:
        """Resolve OA evidence and atomically acquire a PDF for one DOI."""
        require_contact_email()  # refused before any request (MAILTO_NOT_SET)
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
                    try:
                        success = await self.download_pdf(
                            session,
                            candidate,
                            candidate_path,
                            forward_proxy_url=self.forward_proxy_url or None,
                        )
                        if not success:
                            last_error = "Failed to download or invalid PDF"
                            continue
                        final_path, _ = self._promote_candidate(candidate_path)
                        return replace(
                            result,
                            success=True,
                            file_path=final_path,
                            status="ACQUIRED",
                            outcome=ACQUIRED,
                            # The label follows the bytes: a file fetched through
                            # the parked gateway is not that open location's copy.
                            open_copy=copy if candidate == copy.url else None,
                            copies_tried=tried,
                        )
                    except Exception as error:  # noqa: BLE001 - provider adapters vary
                        last_error = str(error)
                        logger.debug(
                            "PDF candidate failed for %s via a redacted provider URL: %s",
                            doi,
                            error,
                        )
                    finally:
                        candidate_path.unlink(missing_ok=True)

            message = last_error or "Failed to download or invalid PDF"
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
        self, http_client: AcademicHttpClient, pdf_path: Path, doi: str
    ) -> DownloadResult:
        """Atomically ingest a local PDF without overwriting existing bytes."""
        require_contact_email()  # the metadata lookups send it (MAILTO_NOT_SET)
        if not pdf_path.exists():
            return DownloadResult(
                doi=doi,
                success=False,
                status="FAILED",
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
            if not self._candidate_is_valid(staging):
                return DownloadResult(
                    doi=doi,
                    success=False,
                    status="FAILED",
                    access_status=access_status,
                    metadata=metadata or None,
                    error_message="The provided file is not a valid PDF.",
                    lookups=lookups,
                )
            final_path, _ = self._promote_candidate(staging)
            return DownloadResult(
                doi=doi,
                success=True,
                file_path=final_path,
                was_oa=access_status == "VERIFIED_OPEN_ACCESS",
                status="ACQUIRED",
                access_status=access_status,
                metadata=metadata or None,
                lookups=lookups,
            )
        except Exception as error:  # noqa: BLE001 - provider adapters vary
            return DownloadResult(
                doi=doi,
                success=False,
                status="FAILED",
                access_status="UNRESOLVED",
                error_message=str(error),
            )
        finally:
            if staging is not None:
                staging.unlink(missing_ok=True)
