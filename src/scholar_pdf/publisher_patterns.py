"""Institutional proxy routing: parked code (decision 2026-11-21, M12a item 25, G4).

The module's name is historical. The publisher direct-PDF patterns it held
(``_PUBLISHER_PATTERNS``, ``resolve_doi_to_publisher_pdf``,
``compute_direct_pdf_from_landing_url``) were added "for Cloudflare/WAF bypass"
and built addresses no provider listed; they were removed in Part K (item 24,
G3 "Remove them"). What stays is the proxy rewriting that the parked E1
``acquire`` and the downloader's parked gateway import. ``download`` and
``ingest`` refuse a proxy (``PROXY_REFUSED``).
"""

from __future__ import annotations

from urllib.parse import quote, urlparse, urlunparse

PROXY_STYLES = ("auto", "subdomain", "ezproxy", "prefix")

# Institutional/consortium proxy domains which serve remote access by
# prefixing a rewritten host as a subdomain of the proxy host, e.g.
#   https://ieeexplore.ieee.org/d/x            (direct)
#   https://ieeexplore-ieee-org.www.sndl1.arn.dz/d/x   (via consortium proxy)
# Covered families: Algeria SNL (*.arn.dz), EZproxy (*.ezproxy.*), OpenAthens.
_SUBDOMAIN_PROXY_SUFFIXES = (".arn.dz", ".openathens.net", ".ezproxy.")


def _proxy_netloc(proxy_url: str) -> str:
    url = proxy_url if "://" in proxy_url else f"https://{proxy_url}"
    return urlparse(url).netloc or proxy_url.strip()


def proxy_style(proxy_url: str) -> str:
    """Detect the proxy style from a proxy base URL.

    - ``ezproxy``    EZproxy base: ``https://proxy.uni.edu/login?url=``
    - ``subdomain``  host-prefix style: ``https://www.sndl1.arn.dz``
    - ``prefix``     generic origin-prefix: ``http://proxy:3128``
    """
    p = (proxy_url or "").lower()
    if "login?url=" in p:
        return "ezproxy"
    host = _proxy_netloc(p).lower()
    if host.endswith(_SUBDOMAIN_PROXY_SUFFIXES):
        return "subdomain"
    return "prefix"


def is_proxied_url(url: str, proxy_url: str) -> bool:
    """True if ``url`` already routes through the given proxy host."""
    if not url or not proxy_url:
        return False
    netloc = _proxy_netloc(proxy_url)
    return bool(netloc) and f".{netloc}".lower() in urlparse(url).netloc.lower()


def rewrite_via_subdomain(url: str, proxy_host: str) -> str:
    """Rewrite ``https://host.example.org/p/q`` to ``https://host-example-org.<proxy>/p/q``.

    Dots in the target host become dashes and the result is prefixed to the
    proxy host, exactly the scheme consortium gateways (SNL ``*.arn.dz``,
    EZproxy ``*.ezproxy.*``, OpenAthens) use.  Idempotent: an already-proxied
    URL is returned unchanged.
    """
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if not host:
        return url
    sub = host.replace(".", "-")
    new_host = f"{sub}.{proxy_host.strip().lstrip('.').rstrip('/')}"
    return urlunparse((parsed.scheme, new_host, parsed.path, parsed.params, parsed.query, parsed.fragment))


def rewrite_via_proxy(url: str, proxy_url: str, style: str = "auto") -> str:
    """
    Rewrite a URL to route through an institutional proxy.

    Supported styles (``style="auto"`` detects from the proxy base):

    - ``ezproxy``:   ``https://proxy.uni.edu/login?url=<original_url>``
    - ``subdomain``: ``https://<host-with-dashes>.<proxy.uni.edu>/<path>``
    - ``prefix``:    ``http://proxy:3128/<original_url>``
    """
    if not url or not proxy_url:
        return url

    resolved = proxy_style(proxy_url) if style == "auto" else style
    if resolved == "ezproxy":
        proxy_url = proxy_url.rstrip("/")
        sep = "&" if "?" in proxy_url else "?"
        return f"{proxy_url}{sep}{quote(url, safe=':/?=&#')}"

    proxy_host = _proxy_netloc(proxy_url)
    if not proxy_host:
        return url

    if resolved == "subdomain":
        return rewrite_via_subdomain(url, proxy_host)

    # Generic HTTP proxy: proxy_host/<original_url>
    return f"{proxy_url.rstrip('/')}/{url.lstrip('/')}"
