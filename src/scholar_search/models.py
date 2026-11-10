"""Normalized models for the SLR and scholarly search workflow."""

from dataclasses import dataclass, field
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
