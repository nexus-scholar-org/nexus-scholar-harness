"""Verification and metadata hydration engine for academic literature."""

import copy
import logging
from collections.abc import Callable
from difflib import SequenceMatcher
from typing import Any

from .dedup import _title_key
from .exceptions import ProviderPausedError, QuotaExhaustedError
from .models import Document
from .providers.crossref import CrossrefProvider
from .providers.openalex import OpenAlexProvider

logger = logging.getLogger(__name__)

# Minimum normalized-title length (characters) for one-title-contained-in-other
# to be treated as a match. Guards against short titles trivially matching.
_BIDIRECTIONAL_CONTAINMENT_MIN = 12


def bidirectional_title_similarity(a: str, b: str) -> tuple[float, bool]:
    """
    Strict bidirectional title comparison used to guard DOI hydration.

    Returns (ratio, is_match). A match requires either:
      * SequenceMatcher ratio >= 0.90 over normalized title keys, or
      * one title fully contained in the other (subtitle/prefix forms), with the
        contained title at least `_BIDIRECTIONAL_CONTAINMENT_MIN` chars long.

    Bidirectional means we accept containment in *either* direction (order is
    not significant) and never hydrate on a one-sided statistic alone.
    """
    ka = _title_key(a)
    kb = _title_key(b)
    if not ka or not kb:
        return 0.0, False
    ratio = SequenceMatcher(None, ka, kb).ratio()
    if ratio >= 0.90:
        return ratio, True
    if len(ka) >= _BIDIRECTIONAL_CONTAINMENT_MIN and ka in kb:
        return ratio, True
    if len(kb) >= _BIDIRECTIONAL_CONTAINMENT_MIN and kb in ka:
        return ratio, True
    return ratio, False


#: Placeholder titles a record carries when it has none.
_NO_TITLE = ("", "Untitled", "Unknown Title")

#: Identifier fields a lookup may fill when the record has none.
_ID_FIELDS = ("doi", "arxiv_id", "pubmed_id", "openalex_id", "s2_id")


def confirmed(doc: Document, resolved: Document) -> Document:
    """``doc`` as verified by ``resolved``: a copy that keeps the record and its provenance.

    H-provenance-s2 (2026-11-20). A lookup that confirms a record (Crossref or
    OpenAlex by DOI, arXiv id or title) is not a database that found it. Until
    this fix the lookup's own record replaced the harvested one, so a work
    found by OpenAlex and Semantic Scholar reached ``verified.json`` as one
    ``crossref`` record. The copy keeps ``provider``, ``provider_id``,
    ``sources``, ``workspace_id`` and every field it already has; the lookup
    only fills what is missing (including a DOI resolved by title). A
    non-empty identifier is never replaced by a different one. ``doc`` itself
    is not changed.
    """
    out = copy.deepcopy(doc)
    if (out.title or "").strip() in _NO_TITLE and resolved.title not in _NO_TITLE:
        out.title = resolved.title
    for name in _ID_FIELDS:
        if not getattr(out.external_ids, name) and getattr(resolved.external_ids, name):
            setattr(out.external_ids, name, getattr(resolved.external_ids, name))
    for name in ("abstract", "venue", "url", "year", "tldr"):
        if not getattr(out, name) and getattr(resolved, name):
            setattr(out, name, getattr(resolved, name))
    if not out.authors and resolved.authors:
        out.authors = copy.deepcopy(resolved.authors)
    for name in ("citations_count", "references_count"):
        if getattr(out, name) is None and getattr(resolved, name) is not None:
            setattr(out, name, getattr(resolved, name))
    for oa in resolved.oa_locations:
        if oa not in out.oa_locations:
            out.oa_locations.append(copy.deepcopy(oa))
    return out



def _doi_kept(doc: Document, resolved: Document) -> str:
    """The note's tail when a title match carries another DOI than the record's own.

    ``confirmed`` keeps the record's DOI; the match's DOI is named here so the
    conflict stays visible in the verification audit.
    """
    own, other = doc.external_ids.doi, resolved.external_ids.doi
    if own and other and own.strip().lower() != other.strip().lower():
        return f"; the match's DOI {other} differs, the record keeps {own}"
    return ""


#: Why a record, or part of its check, was not done (H-quota-hang).
QUOTA_EXHAUSTED = "PROVIDER_QUOTA_EXHAUSTED"
PROVIDER_PAUSED = "PROVIDER_UNAVAILABLE_UNTIL"
STOPPED = "STOPPED_BY_RESEARCHER"


class _Skipped(Exception):
    """A lookup was not made: its provider is paused for the rest of the batch."""


class DocumentVerifier:
    """
    Verifies the existence of documents against Crossref & OpenAlex
    to detect hallucinations and hydates missing metadata.

    A verified record is the input record, filled where it lacks data; the
    lookup's record never replaces it (``confirmed``).

    H-quota-hang: when a provider answers with a wait beyond the HTTP
    client's cap (``ProviderPausedError``: a used-up quota, an announced
    outage), this verifier does not ask it again; ``paused`` lists those
    providers with their reset time. ``should_stop`` (an attribute, or the
    ``process_batch`` argument) is read before each record; ``stopped`` says
    whether it ended a batch early.
    """

    def __init__(
        self,
        crossref_provider: CrossrefProvider | None = None,
        openalex_provider: OpenAlexProvider | None = None,
    ):
        self.crossref = crossref_provider or CrossrefProvider()
        self.openalex = openalex_provider or OpenAlexProvider()
        self.should_stop: Callable[[], bool] | None = None
        self.stopped = False
        self._paused: dict[str, ProviderPausedError] = {}
        self._skipped: set[str] = set()

    @property
    def paused(self) -> list[dict[str, Any]]:
        """The providers not asked any more, each with its database name, HTTP status and reset time."""
        return [
            {
                "provider": key,
                "database": error.database,
                "status_code": error.status_code,
                "retry_after": error.retry_after,
                "resets_at": error.resets_at,
                "reason": QUOTA_EXHAUSTED if isinstance(error, QuotaExhaustedError) else PROVIDER_PAUSED,
            }
            for key, error in self._paused.items()
        ]

    def _pause(self, key: str, exc: ProviderPausedError) -> None:
        if key not in self._paused:
            logger.warning("%s is not asked again in this batch: %s", exc.database, exc)
            self._paused[key] = exc
        self._skipped.add(key)

    def _skip_if_paused(self, key: str) -> None:
        if key in self._paused:
            self._skipped.add(key)
            raise _Skipped(key)

    async def _get(self, key: str, provider: Any, url: str, **kwargs: Any) -> Any:
        """``provider.client.get``, unless ``key`` is paused; an answer that pauses it raises ``_Skipped``."""
        self._skip_if_paused(key)
        try:
            return await provider.client.get(url, **kwargs)
        except ProviderPausedError as exc:
            self._pause(key, exc)
            raise _Skipped(key) from exc

    @staticmethod
    def _title_mismatch(doc: Document, resolved: Document, via: str) -> str | None:
        """The DOI_TITLE_MISMATCH note when an identifier resolves to another title (SRCH-10).

        A record without a usable title cannot be compared and is not a mismatch.
        """
        if not doc.title or doc.title == "Untitled" or not resolved.title:
            return None
        ratio, ok = bidirectional_title_similarity(doc.title, resolved.title)
        if ok:
            return None
        return (
            f"DOI_TITLE_MISMATCH: {via} resolves to a different title "
            f"({ratio:.0%} similar): {resolved.title!r}"
        )

    async def verify_document(self, doc: Document) -> tuple[bool, Document, str]:
        """
        Verifies if a document is real.
        Returns (is_verified, hydrated_document, explanation).

        An identifier that resolves to a record with a different title is
        ``DOI_TITLE_MISMATCH``: not verified, and the input record is returned
        unchanged; it is never replaced by the resolved one (SRCH-10).

        A verified record is a copy of the input, filled where it lacks data
        (``confirmed``): its provider, sources and workspace id stay its own.
        """
        # 1. Verification by existing DOI (Crossref first, then OpenAlex fallback for arXiv/DataCite)
        if doc.external_ids.doi:
            clean_doi = doc.external_ids.doi.strip()
            # Try Crossref
            try:
                url = f"{self.crossref.base_url}/{clean_doi}"
                resp = await self._get("crossref", self.crossref, url)
                if resp.status_code == 200:
                    response = resp.json()
                    item = response.get("message", {})
                    if item:
                        verified_doc = self.crossref._normalize_document(item)
                        mismatch = self._title_mismatch(doc, verified_doc, f"DOI {clean_doi} (Crossref)")
                        if mismatch:
                            return False, doc, mismatch
                        return True, confirmed(doc, verified_doc), f"Verified via Crossref DOI ({clean_doi})"
            except Exception as e:
                logger.debug(f"Crossref DOI verification failed for {clean_doi}: {e}")

            # Try OpenAlex for non-Crossref / DataCite / arXiv DOIs
            try:
                url = f"{self.openalex.base_url}/https://doi.org/{clean_doi}"
                resp = await self._get("openalex", self.openalex, url)
                if resp.status_code == 200:
                    item = resp.json()
                    if item and item.get("id"):
                        verified_doc = self.openalex._normalize_document(item)
                        mismatch = self._title_mismatch(doc, verified_doc, f"DOI {clean_doi} (OpenAlex)")
                        if mismatch:
                            return False, doc, mismatch
                        return True, confirmed(doc, verified_doc), f"Verified via OpenAlex DOI ({clean_doi})"
            except Exception as e:
                logger.debug(f"OpenAlex DOI verification failed for {clean_doi}: {e}")

        # 2. Verification by arXiv ID
        if doc.external_ids.arxiv_id:
            clean_arxiv = doc.external_ids.arxiv_id.strip()
            try:
                url = f"{self.openalex.base_url}/https://arxiv.org/abs/{clean_arxiv}"
                resp = await self._get("openalex", self.openalex, url)
                if resp.status_code == 200:
                    item = resp.json()
                    if item and item.get("id"):
                        verified_doc = self.openalex._normalize_document(item)
                        mismatch = self._title_mismatch(doc, verified_doc, f"arXiv {clean_arxiv} (OpenAlex)")
                        if mismatch:
                            return False, doc, mismatch
                        return True, confirmed(doc, verified_doc), f"Verified via OpenAlex arXiv ({clean_arxiv})"
            except Exception as e:
                logger.debug(f"OpenAlex arXiv verification failed for {clean_arxiv}: {e}")

        # 3. Verification by Title in Crossref
        if doc.title and doc.title != "Untitled":
            try:
                self._skip_if_paused("crossref")
                try:
                    matched_doc = await self.crossref.validate_reference(doc.title)
                except ProviderPausedError as exc:
                    self._pause("crossref", exc)
                    raise _Skipped("crossref") from exc
                if matched_doc:
                    ratio = SequenceMatcher(
                        None, _title_key(doc.title), _title_key(matched_doc.title)
                    ).ratio()
                    if ratio >= 0.90:
                        return (
                            True,
                            confirmed(doc, matched_doc),
                            f"Verified via Crossref matching ({ratio:.0%} title match)" + _doi_kept(doc, matched_doc),
                        )
            except Exception as e:
                logger.debug(f"Crossref title search failed: {e}")

        # 4. Fallback to OpenAlex Title Search
        if doc.title and doc.title != "Untitled":
            try:
                url = f"{self.openalex.base_url}"
                params = {"search": doc.title, "per-page": 1}
                resp = await self._get("openalex", self.openalex, url, params=params)
                if resp.status_code == 200:
                    response = resp.json()
                    results = response.get("results", [])
                    if results:
                        candidate = self.openalex._normalize_document(results[0])
                        ratio = SequenceMatcher(
                            None, _title_key(doc.title), _title_key(candidate.title)
                        ).ratio()
                        if ratio >= 0.90:
                            return (
                                True,
                                confirmed(doc, candidate),
                                f"Verified via OpenAlex matching ({ratio:.0%} title match)" + _doi_kept(doc, candidate),
                            )
            except Exception as e:
                logger.debug(f"OpenAlex title search failed: {e}")

        return False, doc, "Unverified: Record not found in Crossref or OpenAlex"

    async def hydrate_metadata(self, doc: Document) -> Document:
        """Hydrates missing fields (abstract, OA URL, venue, citations) from OpenAlex."""
        doi = doc.external_ids.doi
        if not doi:
            return doc

        try:
            url = f"{self.openalex.base_url}/https://doi.org/{doi}"
            resp = await self._get("openalex", self.openalex, url)
            response = resp.json()
            if response:
                openalex_doc = self.openalex._normalize_document(response)

                # Period: strict bidirectional title guard. A contaminated DOI
                # (e.g. PubMed carrying another paper's DOI) must not silently
                # overwrite this record's metadata with a mismatched OpenAlex
                # record. When the source record has a real title, we verify it
                # against the OpenAlex title before enriching; on mismatch the
                # record is returned untouched.
                src_title = (doc.title or "").strip()
                if src_title not in ("", "Untitled", "Unknown Title"):
                    ratio, is_match = bidirectional_title_similarity(
                        src_title, openalex_doc.title
                    )
                    if not is_match:
                        logger.warning(
                            "Hydration skipped for DOI %s: title mismatch (%.2f) %r vs %r",
                            doi,
                            ratio,
                            src_title,
                            openalex_doc.title,
                        )
                        return doc

                # Enrich fields
                if not doc.abstract and openalex_doc.abstract:
                    doc.abstract = openalex_doc.abstract
                if not doc.venue and openalex_doc.venue:
                    doc.venue = openalex_doc.venue
                if not doc.url and openalex_doc.url:
                    doc.url = openalex_doc.url
                if not doc.year and openalex_doc.year:
                    doc.year = openalex_doc.year
                if not doc.authors and openalex_doc.authors:
                    doc.authors = openalex_doc.authors
                if doc.citations_count is None:
                    doc.citations_count = openalex_doc.citations_count
                if doc.references_count is None:
                    doc.references_count = openalex_doc.references_count
                if (
                    not doc.external_ids.openalex_id
                    and openalex_doc.external_ids.openalex_id
                ):
                    doc.external_ids.openalex_id = openalex_doc.external_ids.openalex_id
        except Exception as e:
            logger.debug(f"Hydration failed for DOI {doi}: {e}")

        return doc

    async def process_batch(
        self,
        documents: list[Document],
        verify: bool = True,
        enrich: bool = True,
        should_stop: Callable[[], bool] | None = None,
    ) -> tuple[list[Document], list[dict[str, Any]]]:
        """
        Processes a batch of documents with verification and hydration.
        Returns (processed_documents, audit_log): one record and one audit row
        per input document, in order; no record is ever dropped.

        H-quota-hang. Each audit row carries ``not_done`` (the parts of the
        check that were not made: ``verification``, ``enrichment``) and
        ``reason`` (``PROVIDER_QUOTA_EXHAUSTED``, ``PROVIDER_UNAVAILABLE_UNTIL``
        or ``STOPPED_BY_RESEARCHER``; ``None`` when everything was done). A
        record that no lookup confirmed while a paused provider was not asked
        is ``NOT_CHECKED``, never ``UNVERIFIED``: no database said it does not
        exist. A confirmation stays ``VERIFIED`` when only the enrichment was
        not done. ``should_stop`` (default: the ``should_stop`` attribute) is
        read before each record; after a stop the remaining records are kept
        as they are, ``NOT_CHECKED`` with ``STOPPED_BY_RESEARCHER``.
        """
        stop = should_stop if should_stop is not None else self.should_stop
        # A pause and a stop hold for one batch (decision H-quota-hang item 2).
        self._paused, self.stopped = {}, False
        processed_docs: list[Document] = []
        audit_log: list[dict[str, Any]] = []

        for doc in documents:
            if not self.stopped and stop is not None and stop():
                self.stopped = True
            if self.stopped:
                processed_docs.append(doc)
                audit_log.append(self._row(
                    doc, doc, False, "Not checked: stopped by the researcher", "NOT_CHECKED",
                    not_done=[part for part, asked in (("verification", verify), ("enrichment", enrich)) if asked],
                    reason=STOPPED,
                ))
                continue

            is_verified = True
            note = "Not checked"
            current_doc = doc
            not_done: list[str] = []
            skipped: set[str] = set()

            if verify:
                self._skipped = set()
                is_verified, current_doc, note = await self.verify_document(doc)
                if not is_verified and self._skipped and not note.startswith("DOI_TITLE_MISMATCH"):
                    skipped |= self._skipped
                    not_done.append("verification")
                    note = "Not checked: " + "; ".join(
                        f"{self._paused[key].database} was not asked ({self._paused[key]})"
                        for key in sorted(self._skipped)
                    )

            if is_verified and enrich and current_doc.external_ids.doi:
                self._skipped = set()
                current_doc = await self.hydrate_metadata(current_doc)
                if self._skipped:
                    skipped |= self._skipped
                    not_done.append("enrichment")

            code = (
                "NOT_CHECKED" if "verification" in not_done
                else "DOI_TITLE_MISMATCH" if note.startswith("DOI_TITLE_MISMATCH")
                else "VERIFIED" if is_verified and verify
                else "UNVERIFIED" if verify
                else "NOT_CHECKED"
            )
            reason = None
            if skipped:
                quota = any(isinstance(self._paused[key], QuotaExhaustedError) for key in skipped)
                reason = QUOTA_EXHAUSTED if quota else PROVIDER_PAUSED
            processed_docs.append(current_doc)
            audit_log.append(self._row(
                doc, current_doc, is_verified and code != "NOT_CHECKED", note, code,
                not_done=not_done, reason=reason,
            ))

        return processed_docs, audit_log

    @staticmethod
    def _row(
        doc: Document, current_doc: Document, verified: bool, note: str, code: str,
        *, not_done: list[str], reason: str | None,
    ) -> dict[str, Any]:
        return {
            "title": doc.title,
            "input_doi": doc.external_ids.doi,
            "verified": verified,
            "resolved_doi": current_doc.external_ids.doi,
            "status": note,
            "code": code,
            "not_done": not_done,
            "reason": reason,
        }
