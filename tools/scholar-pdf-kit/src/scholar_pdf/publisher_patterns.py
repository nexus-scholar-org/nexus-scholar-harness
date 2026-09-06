"""Publisher direct-PDF endpoint patterns and proxy routing.

Bypasses Cloudflare/WAFs by computing direct PDF download URLs for known
publishers (IEEE, Elsevier/ScienceDirect, MDPI, Springer, arXiv) rather
than following the OA landing-page redirect chain.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import quote

logger = logging.getLogger(__name__)

# Minimum size in bytes to consider a downloaded file a real PDF rather than
# an HTML block-page or stub.  Caught by a genuine PDF header (%PDF-) *and*
# a size floor of ~10 KB.
MIN_PDF_SIZE_BYTES = 10 * 1024

# ---------------------------------------------------------------------------
# DOI-based publisher direct-PDF patterns
# ---------------------------------------------------------------------------
# Each entry: (doi_prefix_regex, landing_page_pattern, direct_pdf_template)
# The landing_page_pattern is used to detect *whether* a URL belongs to this
# publisher; the direct_pdf_template is the final resolved PDF URL.

_PUBLISHER_PATTERNS: list[dict[str, str | re.Pattern[str]]] = [
    {
        "name": "ieee",
        "doi_prefix": re.compile(r"^10\.1109/"),
        "direct_pdf": "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={doi_suffix}",
        "landing_pattern": re.compile(r"ieeexplore\.ieee\.org/document/(\d+)"),
    },
    {
        "name": "elsevier",
        "doi_prefix": re.compile(r"^10\.1016/"),
        "direct_pdf": "https://www.sciencedirect.com/science/article/pii/{pii}/pdfft?isDTMRedir=true&download=true",
        "landing_pattern": re.compile(r"sciencedirect\.com/science/article/pii/([A-Z0-9]+)", re.IGNORECASE),
    },
    {
        "name": "mdpi",
        "doi_prefix": re.compile(r"^10\.3390/"),
        "direct_pdf": "https://www.mdpi.com/{mdpi_path}/pdf",
        "landing_pattern": re.compile(r"mdpi\.com/(\d+[^/]*?)/(?:html|pdf)", re.IGNORECASE),
    },
    {
        "name": "springer",
        "doi_prefix": re.compile(r"^10\.(1007|1140)/"),
        "direct_pdf": "https://link.springer.com/content/pdf/{doi}.pdf",
        "landing_pattern": re.compile(r"link\.springer\.com/(?:article|chapter)/(\S+)"),
    },
    {
        "name": "arxiv",
        "doi_prefix": re.compile(r"^10\.48550/"),
        "direct_pdf": "https://arxiv.org/pdf/{arxiv_id}.pdf",
        "landing_pattern": re.compile(r"arxiv\.org/(?:abs|pdf)/(\d+\.\d+)"),
    },
]


def resolve_doi_to_publisher_pdf(doi: str) -> str | None:
    """
    Given a DOI, return a direct-PDF URL for known publishers, or None.

    For IEEE DOIs (10.1109/...), this computes the IEEE stamp URL directly
    from the DOI suffix, bypassing Cloudflare-protected landing pages.
    For Elsevier (10.1016/...), we derive the PII from the landing page URL
    when available, or attempt a direct ScienceDirect PDF construct.
    """
    if not doi:
        return None

    doi = doi.strip()

    # IEEE: 10.1109/<conference>.<year>.<id>  → direct stamp URL
    if doi.startswith("10.1109/"):
        arnumber = doi.split("/")[-1]
        # The IEEE suffix before the last dot is the arnumber
        parts = arnumber.split(".")
        if parts:
            num = parts[-1]
            url = f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={num}"
            logger.debug("IEEE direct PDF pattern: %s → %s", doi, url)
            return url

    # Springer: 10.1007/... or 10.1140/...  → Springer content PDF
    if doi.startswith(("10.1007/", "10.1140/")):
        url = f"https://link.springer.com/content/pdf/{doi}.pdf"
        logger.debug("Springer direct PDF pattern: %s → %s", doi, url)
        return url

    # arXiv DOI: 10.48550/<arxiv.id>  → arxiv.org/pdf/
    if doi.startswith("10.48550/"):
        arxiv_id = doi.removeprefix("10.48550/")
        url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        logger.debug("arXiv direct PDF pattern: %s → %s", doi, url)
        return url

    return None


def compute_direct_pdf_from_landing_url(landing_url: str) -> str | None:
    """
    Given a publisher landing page URL, return the direct-PDF endpoint URL
    for known publishers, or None if no pattern matches.
    """
    if not landing_url:
        return None

    # IEEE landing page → stamp PDF
    match = _PUBLISHER_PATTERNS[0]["landing_pattern"].search(landing_url)
    if match:
        arnumber = match.group(1)
        return f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arnumber}"

    # Elsevier / ScienceDirect → ScienceDirect PDF (need PII)
    match = _PUBLISHER_PATTERNS[1]["landing_pattern"].search(landing_url)
    if match:
        pii = match.group(1)
        return f"https://www.sciencedirect.com/science/article/pii/{pii}/pdfft?isDTMRedir=true&download=true"

    # MDPI → pdf endpoint
    match = _PUBLISHER_PATTERNS[2]["landing_pattern"].search(landing_url)
    if match:
        return landing_url.rstrip("/") + "/pdf" if not landing_url.endswith("/pdf") else None

    # Springer → /content/pdf/<doi>.pdf
    match = _PUBLISHER_PATTERNS[3]["landing_pattern"].search(landing_url)
    if match:
        doi_suffix = match.group(1)
        return f"https://link.springer.com/content/pdf/{doi_suffix}.pdf"

    # arXiv → /pdf/<id>.pdf
    match = _PUBLISHER_PATTERNS[4]["landing_pattern"].search(landing_url)
    if match:
        arxiv_id = match.group(1)
        return f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    return None


def rewrite_via_proxy(url: str, proxy_url: str) -> str:
    """
    Rewrite a URL to route through an institutional proxy.

    Supports EZproxy-style (prefix) and generic HTTP proxy patterns:

    EZproxy:  https://proxy.university.edu/login?url=<original_url>
    HTTP:     http://proxy:port/<original_url>

    The function detects the proxy style from the proxy_url value:
    - If proxy_url contains ``login?url=``, it is treated as an EZproxy base
      and the original URL is appended.
    - Otherwise, ``proxy_url/<original_url>`` is constructed.
    """
    if not url or not proxy_url:
        return url

    proxy_url = proxy_url.rstrip("/")
    if "login?url=" in proxy_url or "login?url=" in proxy_url.lower():
        # EZproxy: proxy base already contains the login-url pattern
        sep = "&" if "?" in proxy_url else "?"
        return f"{proxy_url}{sep}{quote(url, safe=':/?=&#')}"

    # Generic HTTP proxy
    return f"{proxy_url}/{url.lstrip('/')}"
