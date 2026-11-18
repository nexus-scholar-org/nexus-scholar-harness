"""Normalized models for the SLR and scholarly search workflow."""

from dataclasses import dataclass, field, fields
from datetime import UTC, datetime
from typing import Any


@dataclass
class ExternalIds:
    doi: str | None = None
    arxiv_id: str | None = None
    pubmed_id: str | None = None
    openalex_id: str | None = None
    s2_id: str | None = None

    def __post_init__(self) -> None:
        if self.doi:
            value = self.doi.strip().lower()
            for prefix in (
                "https://doi.org/",
                "http://doi.org/",
                "https://dx.doi.org/",
                "http://dx.doi.org/",
                "doi:",
            ):
                value = value.removeprefix(prefix)
            value = value.strip()
            self.doi = value if value else None
        else:
            self.doi = None

        if self.arxiv_id:
            val = self.arxiv_id.strip()
            for prefix in ("arxiv:", "arXiv:"):
                val = val.removeprefix(prefix)
            val = val.strip()
            self.arxiv_id = val if val else None

        if self.pubmed_id:
            # Researcher-authorized r3b hardening: the PMID namespace must be
            # bare everywhere, for every importer/provider, not just the
            # OpenAlex search-leg parser (observed live 2026-10-17: URL-form
            # pubmed_id from any legacy provider or cached JSON collided with
            # the PubMed provider's bare PMID in _has_identifier_conflict,
            # annulling the DOI-tier merge of the same work).
            p_val = str(self.pubmed_id).strip().rstrip("/")
            for prefix in (
                "https://pubmed.ncbi.nlm.nih.gov/",
                "http://pubmed.ncbi.nlm.nih.gov/",
                "https://www.ncbi.nlm.nih.gov/pubmed/",
                "pmid:",
                "PMID:",
            ):
                p_val = p_val.removeprefix(prefix)
            self.pubmed_id = p_val.strip() or None
        else:
            self.pubmed_id = None


@dataclass
class Author:
    family_name: str
    given_name: str | None = None
    orcid: str | None = None

    @property
    def full_name(self) -> str:
        return (
            f"{self.given_name} {self.family_name}"
            if self.given_name
            else self.family_name
        )


@dataclass
class Document:
    title: str
    year: int | None = None
    provider: str = "unknown"
    provider_id: str = ""
    external_ids: ExternalIds = field(default_factory=ExternalIds)
    abstract: str | None = None
    authors: list[Author] = field(default_factory=list)
    venue: str | None = None
    url: str | None = None

    # Workspace & Provenance Identification
    workspace_id: str | None = None
    sources: list[dict[str, Any]] = field(default_factory=list)
    oa_locations: list[dict[str, Any]] = field(default_factory=list)

    # Snowballing & Enhanced Metadata
    citations_count: int | None = None
    references_count: int | None = None
    citation_intents: list[str] = field(
        default_factory=list
    )  # e.g. "methodology" from S2
    mesh_terms: list[str] = field(
        default_factory=list
    )  # Medical Subject Headings from PubMed
    tldr: str | None = None  # AI Summary from Semantic Scholar
    topics: list[dict] | None = (
        None  # classifier-grounded taxonomy ({source,id,display_name,score}, M0.6)
    )

    query_id: str | None = None
    retrieved_at: datetime | None = None
    cluster_id: int | None = None
    raw_data: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        import html
        import re

        if self.title:
            t = html.unescape(self.title)
            t = re.sub(r"<[^>]+>", "", t)
            self.title = re.sub(r"\s+", " ", t).strip()
        else:
            self.title = "Untitled"

        if self.venue:
            v = html.unescape(self.venue)
            v = re.sub(r"<[^>]+>", "", v)
            self.venue = re.sub(r"\s+", " ", v).strip()

        if self.abstract:
            a = html.unescape(self.abstract)
            # Strip JATS XML and general XML/HTML tags
            a = re.sub(r"<jats:[^>]+>", "", a)
            a = re.sub(r"</jats:[^>]+>", "", a)
            a = re.sub(r"<[^>]+>", "", a)
            self.abstract = re.sub(r"\s+", " ", a).strip()

        if not self.sources and self.provider and self.provider != "unknown":
            self.sources.append(
                {
                    "provider": self.provider,
                    "id": self.provider_id,
                }
            )

    def mark_retrieved(self) -> None:
        self.retrieved_at = datetime.now(UTC)


@dataclass
class Query:
    text: str
    id: str = "Q001"
    year_min: int | None = None
    year_max: int | None = None
    language: str = "en"
    max_results: int | None = None
    semantic: bool = False
    # Where ``max_results`` came from, reported on each search leg: "protocol"
    # (method.retrieval_cap), "run_override" (an explicit run option) or "query"
    # (a caller-set value). With no max_results the engine ceiling applies.
    cap_source: str = "query"


#: The databases searched when nothing names them (F15, M3h-b-resilience): a
#: protocol without ``search_strategy.target_databases``, a list with no known
#: name, ``SearchEngine()`` with no providers, a CLI search without a protocol
#: and the recon probe. The protocol model's default and the protocol presets
#: hold the same list (they cannot import this package);
#: ``tests/kits/search/test_provider_resilience.py::test_one_default_database_set``
#: keeps them equal. A protocol that names its databases searches exactly those.
#: The choice of this list is a proposed decision (``docs/decisions.md``,
#: 2026-11-18): PubMed and bioRxiv are searched when a protocol or a run names them.
DEFAULT_DATABASES: tuple[str, ...] = ("openalex", "semanticscholar", "crossref", "arxiv")

#: A leg's auth channel (F16, M3h-b-resilience): what identified the caller to
#: the provider. ``key`` an API key was sent; ``key_rejected`` the provider
#: refused the key (the leg was not retried keyless); ``mailto`` a contact
#: address only (Crossref's polite pool, NCBI's ``email``); ``none`` nothing.
AUTH_CHANNELS = ("key", "key_rejected", "mailto", "none")


@dataclass
class SearchLeg:
    """One provider's part of one search run (SRCH-30, CORE-21).

    Records what was actually sent and what came back, so the run can be
    reported per database (PRISMA-S): the executed query string, the total the
    provider reported, how many records were fetched, the cap that applied and
    whether it stopped the leg, and when. Never holds the contact address or
    an API key.
    """

    provider: str
    query_id: str
    executed_query: str | None = None
    request: dict[str, Any] = field(default_factory=dict)
    reported_total: int | None = None
    fetched: int = 0
    pages: int = 0
    cap: int | None = None
    cap_source: str | None = None
    cap_hit: bool = False
    status: str = "pending"
    error: str | None = None
    # E5 (M3b-api): the failure kind beside the text: PROVIDER_RATE_LIMITED,
    # PROVIDER_TIMEOUT, PROVIDER_UNAVAILABLE or PROVIDER_REFUSED; None when the
    # leg did not fail or failed on something that is not the provider's answer.
    error_code: str | None = None
    notes: list[str] = field(default_factory=list)
    mailto_set: bool = False
    started_at: str | None = None
    finished_at: str | None = None
    # F16 (M3h-b-resilience): where the leg's requests went (no parameters),
    # how the caller was identified (``AUTH_CHANNELS``) and the records asked
    # for per page. None for a provider that records no translation.
    endpoint: str | None = None
    auth: str | None = None
    page_size: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "query_id": self.query_id,
            "executed_query": self.executed_query,
            "request": dict(self.request),
            "reported_total": self.reported_total,
            "fetched": self.fetched,
            "pages": self.pages,
            "cap": self.cap,
            "cap_source": self.cap_source,
            "cap_hit": self.cap_hit,
            "status": self.status,
            "error": self.error,
            "error_code": self.error_code,
            "notes": list(self.notes),
            "mailto_set": self.mailto_set,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "endpoint": self.endpoint,
            "auth": self.auth,
            "page_size": self.page_size,
        }


@dataclass
class SearchRun:
    """The result of ``SearchEngine.run``: the documents and one leg per provider."""

    documents: list[Document]
    legs: list[SearchLeg]


@dataclass
class DocumentCluster:
    cluster_id: int
    representative: Document
    members: list[Document]
    #: E4a (M3d-engine): the tier that merged each member after the first
    #: (``identifier``, ``exact_title`` or ``fuzzy_title``), in member order.
    merges: list[str] = field(default_factory=list)

    @property
    def tier(self) -> str | None:
        """The tier of the cluster's first merge; ``None`` for a singleton."""
        return self.merges[0] if self.merges else None

    @property
    def size(self) -> int:
        return len(self.members)

    @property
    def confidence(self) -> float:
        has_identifier = any(
            member.external_ids.doi or member.external_ids.arxiv_id
            for member in self.members
        )
        return 1.0 if has_identifier else 0.95


def _saved_datetime(value: Any) -> Any:
    """A saved ``retrieved_at`` back as a ``datetime``; anything unreadable is kept as it is."""
    if not isinstance(value, str):
        return value
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return value


def document_from_record(record: dict[str, Any]) -> Document:
    """Rebuild a ``Document`` from its saved record (``asdict`` written as JSON).

    The inverse of how the search stages save records (``json.dumps(asdict(doc),
    default=str)``): every saved field is set as it was saved, with no second
    pass of the constructors' clean-up, so saving the result again gives the
    same record. A field the record does not carry keeps its default; a key the
    model does not know is ignored.
    """
    doc = Document(title="Untitled")
    names = {f.name for f in fields(Document)}
    for name, value in record.items():
        if name not in names:
            continue
        if name == "external_ids":
            ids = ExternalIds()
            for key, item in (value or {}).items():
                if key in ExternalIds.__dataclass_fields__:
                    setattr(ids, key, item)
            value = ids
        elif name == "authors":
            authors = []
            for item in value or []:
                author = Author(family_name="")
                for key, part in (item or {}).items():
                    if key in Author.__dataclass_fields__:
                        setattr(author, key, part)
                authors.append(author)
            value = authors
        elif name == "retrieved_at":
            value = _saved_datetime(value)
        setattr(doc, name, value)
    return doc
