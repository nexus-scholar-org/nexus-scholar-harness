"""Which open copies of a paper OpenAlex and Unpaywall list, and in what order.

H-pdf-resolver-locations (found live 2026-11-21): the "best" location of a
paper is often the publisher's landing page with no PDF address, while a
repository in the full list has one. Every listed location is read here.

Rules (decision 2026-11-21, M12a answer F3 and items 24 and 27):

- a location counts only if the provider marks it open (``is_oa`` true in an
  OpenAlex answer; listed in ``best_oa_location`` or ``oa_locations`` in an
  Unpaywall answer) and it carries a direct PDF address (``pdf_url`` or
  ``url_for_pdf``);
- explicit closed evidence from a service about the work (``is_oa: false`` or
  ``oa_status: "closed"``) overrides any ``pdf_url`` that service gives (Part K
  item 7, PDF-12): none of that service's addresses is listed;
- a landing page is never turned into a PDF address and no address is built;
- the published version comes first, then the accepted manuscript, then the
  submitted version or preprint, then a copy whose version is not given.

Nothing here makes a request.
"""

from __future__ import annotations

from dataclasses import dataclass

#: The providers' own version labels, best first (M12a answer F3).
VERSION_ORDER = ("publishedVersion", "acceptedVersion", "submittedVersion")
#: The label of a copy whose version the provider does not give, or gives in other words.
UNKNOWN_VERSION = "unknown"
#: How many listed addresses one DOI may cost (the best-ranked ones).
MAX_OPEN_COPIES_TRIED = 3

PROVIDER_NAMES = {"openalex": "OpenAlex", "unpaywall": "Unpaywall", "arxiv": "arXiv"}

#: Lookup states. ``NOT_FOUND`` (HTTP 404) is an answer: the service does not know the DOI.
ANSWERED, NOT_FOUND, FAILED = "ANSWERED", "NOT_FOUND", "FAILED"
#: OpenAlex is not asked without ``SCHOLAR_OPENALEX_KEY`` (Part K item 4). Neither an
#: answer nor a failure: running again without the key would not change it.
NOT_ASKED = "NOT_ASKED"

#: Why a DOI ended as it did (``DownloadResult.outcome``).
ACQUIRED = "ACQUIRED"
PDF_NOT_FETCHED = "PDF_NOT_FETCHED"
LOOKUP_FAILED = "LOOKUP_FAILED"
OPEN_NO_DIRECT_PDF = "OPEN_NO_DIRECT_PDF"
NO_OPEN_COPY_LISTED = "NO_OPEN_COPY_LISTED"

_NOT_A_PAYWALL_ANSWER = "This is not a paywall determination."


@dataclass(frozen=True)
class OpenCopy:
    """One open location with a direct PDF address, as its provider lists it."""

    url: str
    #: ``publishedVersion``, ``acceptedVersion``, ``submittedVersion`` or ``unknown``.
    version: str
    license: str | None
    #: ``publisher`` or ``repository``; ``None`` when the provider does not say.
    host_type: str | None
    source_name: str | None
    #: ``openalex``, ``unpaywall``, or ``arxiv`` (M12a Part F: the link arXiv's own answer gives).
    provider: str
    #: The version in the words a row shows when the provider says more than
    #: ``version`` (M12a Part F: "preprint (arXiv v3)"); ``None`` otherwise.
    version_label: str | None = None

    def label(self) -> str:
        """The copy in words, for a table row."""
        parts = [
            self.version_label or self.version,
            self.license or "licence not given",
            self.source_name or self.host_type or "host not given",
            f"listed by {PROVIDER_NAMES.get(self.provider, self.provider)}",
        ]
        return ", ".join(parts)


@dataclass(frozen=True)
class LookupOutcome:
    """What one service answered for one DOI. Never holds the request or its address."""

    provider: str
    state: str
    http_status: int | None = None
    #: The error's class name when the lookup failed; never its text.
    error_kind: str | None = None

    @property
    def name(self) -> str:
        return PROVIDER_NAMES.get(self.provider, self.provider)

    @property
    def budget_spent(self) -> bool:
        """OpenAlex answered 409: its daily budget is spent (Part K item 4)."""
        return self.provider == "openalex" and self.state == FAILED and self.http_status == 409

    def failure(self) -> str:
        """Why the lookup failed, in words: the HTTP status, or the kind of error.

        ``failed (HTTP 503)``, ``failed (HTTP 409: the daily budget is spent)``
        (OpenAlex only), ``failed (timed out)``, ``failed (network error)``
        (the lookup client's error with no status), ``failed (unreadable answer)``
        (a 200 whose body is not a JSON object), else the error's class name.
        """
        if self.budget_spent:
            return "failed (HTTP 409: the daily budget is spent)"
        if self.http_status is not None and self.http_status != 200:
            return f"failed (HTTP {self.http_status})"
        if self.error_kind and "Timeout" in self.error_kind:
            return "failed (timed out)"
        if self.error_kind == "ProviderError":
            return "failed (network error)"
        if self.http_status == 200:
            return "failed (unreadable answer)"
        return f"failed ({self.error_kind or 'no answer'})"


def _address(value: object) -> str | None:
    """A web address as given, or ``None``. Nothing is repaired or completed."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text if text.lower().startswith(("http://", "https://")) else None


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _version(value: object) -> str:
    return value if value in VERSION_ORDER else UNKNOWN_VERSION


def says_closed(payload: object) -> bool:
    """Whether one service's answer says the work is closed (Part K item 7, PDF-12).

    ``is_oa: false`` or ``oa_status: "closed"``, at the top (Unpaywall) or in
    ``open_access`` (OpenAlex). Such evidence overrides that service's ``pdf_url``.
    """
    if not isinstance(payload, dict):
        return False
    open_access = payload.get("open_access")
    if isinstance(open_access, dict) and (
        open_access.get("is_oa") is False or open_access.get("oa_status") == "closed"
    ):
        return True
    return payload.get("is_oa") is False or payload.get("oa_status") == "closed"


def _openalex_locations(payload: dict) -> list[dict]:
    listed = [payload.get("best_oa_location"), payload.get("primary_location")]
    more = payload.get("locations")
    if isinstance(more, list):
        listed.extend(more)
    return [location for location in listed if isinstance(location, dict)]


def _unpaywall_locations(payload: dict) -> list[dict]:
    listed = [payload.get("best_oa_location")]
    more = payload.get("oa_locations")
    if isinstance(more, list):
        listed.extend(more)
    # A location Unpaywall lists here is open; one that says otherwise is left out.
    return [
        location
        for location in listed
        if isinstance(location, dict) and location.get("is_oa") is not False
    ]


def _openalex_copies(payload: dict) -> list[OpenCopy]:
    copies = []
    for location in _openalex_locations(payload):
        url = _address(location.get("pdf_url"))
        if location.get("is_oa") is not True or url is None:
            continue
        source = location.get("source") if isinstance(location.get("source"), dict) else {}
        kind = _text(source.get("type"))
        copies.append(
            OpenCopy(
                url=url,
                version=_version(location.get("version")),
                license=_text(location.get("license")),
                host_type=None if kind is None else "repository" if kind == "repository" else "publisher",
                source_name=_text(source.get("display_name")),
                provider="openalex",
            )
        )
    return copies


def _unpaywall_copies(payload: dict) -> list[OpenCopy]:
    copies = []
    for location in _unpaywall_locations(payload):
        url = _address(location.get("url_for_pdf"))
        if url is None:
            continue
        host_type = _text(location.get("host_type"))
        if host_type == "publisher":
            source_name = _text(payload.get("journal_name")) or _text(payload.get("publisher"))
        else:
            source_name = _text(location.get("repository_institution"))
        copies.append(
            OpenCopy(
                url=url,
                version=_version(location.get("version")),
                license=_text(location.get("license")),
                host_type=host_type if host_type in ("publisher", "repository") else None,
                source_name=source_name,
                provider="unpaywall",
            )
        )
    return copies


def open_copies(openalex: dict | None, unpaywall: dict | None) -> list[OpenCopy]:
    """Every open copy with a direct PDF address, best first, each address once.

    Order: by version (``VERSION_ORDER``, then ``unknown``); within a version
    OpenAlex before Unpaywall, and within a provider its own order
    (``best_oa_location``, ``primary_location``, then the list as given).
    """
    listed: list[OpenCopy] = []
    if isinstance(openalex, dict) and not says_closed(openalex):
        listed.extend(_openalex_copies(openalex))
    if isinstance(unpaywall, dict) and not says_closed(unpaywall):
        listed.extend(_unpaywall_copies(unpaywall))
    return rank_copies(listed)


def rank_copies(listed: list[OpenCopy] | tuple[OpenCopy, ...]) -> list[OpenCopy]:
    """``listed`` best version first (``VERSION_ORDER``, then ``unknown``), each address once.

    Stable: copies of one version keep the order given. M12a Part F ranks the
    ``pdf`` link of arXiv's answer (a ``submittedVersion``) with the services'
    copies this way, so a published version listed for the journal DOI wins.
    """
    order = {version: rank for rank, version in enumerate((*VERSION_ORDER, UNKNOWN_VERSION))}
    seen: set[str] = set()
    copies = []
    for copy in sorted(listed, key=lambda item: order.get(item.version, len(order))):  # stable
        if copy.url not in seen:
            seen.add(copy.url)
            copies.append(copy)
    return copies


def open_landing_page(openalex: dict | None, unpaywall: dict | None) -> str | None:
    """The first open location's landing page, to name in a message. Never requested."""
    openalex = None if says_closed(openalex) else openalex
    unpaywall = None if says_closed(unpaywall) else unpaywall
    if isinstance(openalex, dict):
        for location in _openalex_locations(openalex):
            page = _address(location.get("landing_page_url"))
            if location.get("is_oa") is True and page:
                return page
    if isinstance(unpaywall, dict):
        for location in _unpaywall_locations(unpaywall):
            page = _address(location.get("url_for_landing_page"))
            if page:
                return page
    return None


def lists_open(payload: dict | None) -> bool:
    """Whether one service's answer marks the paper, or a location of it, as open."""
    if not isinstance(payload, dict) or says_closed(payload):
        return False
    open_access = payload.get("open_access")
    if isinstance(open_access, dict) and open_access.get("is_oa") is True:
        return True
    if payload.get("is_oa") is True:
        return True
    if payload.get("oa_status") in ("gold", "green", "hybrid", "bronze"):
        return True
    if any(location.get("is_oa") is True for location in _openalex_locations(payload)):
        return True
    more = payload.get("oa_locations")
    return isinstance(more, list) and any(isinstance(item, dict) for item in more)


def not_asked_note(lookup: LookupOutcome) -> str:
    """Why a service was not asked, in words (only OpenAlex without its key)."""
    return f"{lookup.name} was not asked (SCHOLAR_OPENALEX_KEY is not set)"


def _said(lookup: LookupOutcome, payload: dict | None) -> str:
    if lookup.state == NOT_ASKED:
        return not_asked_note(lookup)
    if lookup.state == FAILED:
        return f"{lookup.name} {lookup.failure()}"
    if lookup.state == NOT_FOUND:
        return f"{lookup.name} does not know this DOI"
    if lists_open(payload):
        return f"{lookup.name} lists it as open access without a direct PDF address"
    return f"{lookup.name} lists no open copy"


def unresolved(
    lookups: tuple[LookupOutcome, ...], payloads: dict[str, dict | None]
) -> tuple[str, str]:
    """The outcome and the message for a DOI with no direct PDF address.

    Three cases that read differently: a lookup failed (the answer is
    incomplete), the paper is listed as open but only with landing pages, and
    no open copy is listed.
    """
    said = "; ".join(_said(lookup, payloads.get(lookup.provider)) for lookup in lookups)
    if any(lookup.state == FAILED for lookup in lookups):
        message = (
            f"Lookup failed, so the answer is incomplete: {said}. "
            f"Run the command again later. {_NOT_A_PAYWALL_ANSWER}"
        )
        return LOOKUP_FAILED, message
    if any(lists_open(payloads.get(lookup.provider)) for lookup in lookups):
        page = open_landing_page(payloads.get("openalex"), payloads.get("unpaywall"))
        by_hand = (
            f"get the PDF from {page} yourself and use 'scholar-pdf ingest'"
            if page
            else "get the PDF yourself and use 'scholar-pdf ingest'"
        )
        message = (
            f"Open access, but no direct PDF address is listed: {said}. "
            f"No address is guessed; {by_hand}. {_NOT_A_PAYWALL_ANSWER}"
        )
        return OPEN_NO_DIRECT_PDF, message
    return NO_OPEN_COPY_LISTED, f"No open copy is listed: {said}. {_NOT_A_PAYWALL_ANSWER}"
