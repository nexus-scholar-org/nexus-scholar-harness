from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

#: Decision 2026-11-21, M12a items 21 and 27 (K0): ``download`` and ``ingest``
#: are production; the refusals below name the decision item they apply.
DECISION = "decision 2026-11-21, M12a"


class Settings(BaseSettings):
    """Global settings for scholar-pdf-kit."""

    # Contact address sent to Unpaywall and OpenAlex and in the User-Agent.
    # No default (K0, M12a item 27): the app's ``SCHOLAR_MAILTO`` is read
    # first, then the kit's own ``MAILTO``; without either the kit refuses
    # to fetch (``MAILTO_NOT_SET``).
    mailto: str = ""

    # Download configurations
    download_dir: Path = Path("downloads")
    max_concurrent_downloads: int = 5
    download_timeout: int = 30  # seconds

    # Institutional proxy support: parked code. ``download`` and ``ingest``
    # refuse a set proxy with a message (M12a item 25, G4).
    # EZproxy:   https://proxy.university.edu/login?url=
    # Subdomain: https://www.sndl1.arn.dz   (host-prefix style, auto-detected)
    # Prefix:    http://proxy:3128
    proxy_url: str = ""
    # auto | ezproxy | subdomain | prefix
    proxy_style: str = "auto"

    # Optional structural (pypdf) validation on ingest, beyond the binary
    # %PDF- header + %%EOF trailer signature check.
    pdf_structural_validation: bool = False

    # Publisher direct-PDF patterns: off (K0, M12a item 27) and no longer
    # read by the downloader; the patterns are removed in Part K (item 24,
    # G3). ``download`` and ``ingest`` refuse the setting when it is on.
    enable_publisher_direct_patterns: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


class MailtoNotSetError(RuntimeError):
    """The kit was asked to fetch without a contact address (``MAILTO_NOT_SET``)."""

    code = "MAILTO_NOT_SET"

    def __init__(self) -> None:
        super().__init__(
            "MAILTO_NOT_SET: fetching needs a contact email for Unpaywall and OpenAlex. "
            "Set SCHOLAR_MAILTO (or the kit's MAILTO) in the environment or in .env."
        )


def contact_email() -> str:
    """The contact address: the app's ``SCHOLAR_MAILTO`` first, then ``MAILTO``; ``""`` if neither."""
    from scholar_search.config import settings as search_settings

    for value in (search_settings.mailto, settings.mailto):
        if value and value.strip():
            return value.strip()
    return ""


def require_contact_email() -> str:
    """The contact address, or :class:`MailtoNotSetError` before any request is made."""
    address = contact_email()
    if not address:
        raise MailtoNotSetError()
    return address


def user_agent() -> str:
    """``nexus-scholar/<version> (mailto:<address>)``: the app names itself, never a browser."""
    from scholar_search.http_client import PACKAGE, package_version

    return f"{PACKAGE}/{package_version()} (mailto:{require_contact_email()})"
