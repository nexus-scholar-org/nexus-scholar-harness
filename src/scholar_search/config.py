"""Configuration management for scholar-search-kit."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main configuration settings loaded from environment or .env file."""

    # Contact address for the providers that read one (Crossref's polite pool,
    # NCBI E-utilities for PubMed). OpenAlex no longer reads it (F12).
    # No default: a live search refuses with MAILTO_NOT_SET until it is set
    # (decision 2026-11-08, "A live search needs a real contact email").
    mailto: str | None = Field(
        default=None,
        description="Contact email sent to Crossref and PubMed (SCHOLAR_MAILTO)",
    )

    # API Keys
    # OpenAlex requires a key since 2026-02-13 (announced 2026-01-14): keyless
    # calls share a small daily budget per IP, then answer 409, and cursor
    # paging past the first page answers 401. A browser run that selects
    # OpenAlex refuses with OPENALEX_KEY_NOT_SET until it is set
    # (decision 2026-11-10, "OpenAlex needs its API key").
    openalex_key: str | None = Field(
        default=None,
        description="OpenAlex API key, required for OpenAlex searches (SCHOLAR_OPENALEX_KEY)",
    )
    # Semantic Scholar: the bulk search runs keyless in a shared pool; a key
    # (sent as ``x-api-key``) gives 1 request per second of one's own. A key
    # S2 rejects (401/403; keys unused for about 60 days are pruned) fails the
    # leg with PROVIDER_REFUSED, never a silent keyless retry (M3h-providers).
    s2_key: str | None = Field(
        default=None,
        description="Semantic Scholar API key, optional (SCHOLAR_S2_KEY)",
    )

    # Cache settings
    http_cache: bool = Field(
        default=True,
        description=(
            "Cache provider responses (SCHOLAR_HTTP_CACHE). Off for recording or "
            "replaying VCR cassettes, where every request must reach the transport."
        ),
    )
    cache_dir: Path = Field(
        default=Path(".cache"), description="Directory to store SQLite cache"
    )
    cache_expire_days: int = Field(
        default=30, description="Number of days to keep API responses cached"
    )

    # Rate limits (Requests per second)
    rate_limit_openalex: float = Field(
        default=10.0, description="OpenAlex requests per second"
    )
    rate_limit_crossref: float = Field(
        default=5.0, description="Crossref requests per second (with mailto)"
    )
    # Semantic Scholar keys get "1 request per second, cumulative across all
    # endpoints", and S2 asks callers to set their limit "below this
    # threshold" (key e-mail, 2026-11-11); exactly 1.0 lets two requests land
    # in one second. The abstract hydrator has its own limiter (follow-up).
    rate_limit_s2: float = Field(
        default=0.9, description="Semantic Scholar requests per second (SCHOLAR_RATE_LIMIT_S2)"
    )
    rate_limit_pubmed: float = Field(
        default=3.0, description="PubMed requests per second (no key)"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SCHOLAR_",
        extra="ignore",
    )


# Global settings instance
settings = Settings()
