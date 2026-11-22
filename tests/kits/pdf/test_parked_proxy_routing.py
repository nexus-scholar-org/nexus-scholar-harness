"""Part K item 3 (M12a item 24, G3 "Remove them"): the guessed publisher URLs are gone.

The direct-PDF patterns (``_PUBLISHER_PATTERNS``, ``resolve_doi_to_publisher_pdf``,
``compute_direct_pdf_from_landing_url``) were added "for Cloudflare/WAF bypass"
and their IEEE rule addressed another paper (PDF-11); they are deleted with
their tests. What stays in ``publisher_patterns`` is the institutional proxy
routing, parked code (item 25, G4) that the parked E1 ``acquire`` and the
parked gateway still import; the tests below keep it from rotting.
"""

import importlib

import pytest

import scholar_pdf
from scholar_pdf.publisher_patterns import (
    is_proxied_url,
    proxy_style,
    rewrite_via_proxy,
    rewrite_via_subdomain,
)

REMOVED = (
    "_PUBLISHER_PATTERNS",
    "resolve_doi_to_publisher_pdf",
    "compute_direct_pdf_from_landing_url",
)


@pytest.mark.parametrize("name", REMOVED)
def test_the_guessed_publisher_url_patterns_are_removed(name):
    module = importlib.import_module("scholar_pdf.publisher_patterns")
    assert not hasattr(module, name)
    assert not hasattr(scholar_pdf, name)
    assert name not in scholar_pdf.__all__


def test_the_kit_holds_no_guessed_publisher_address():
    """No module of the package builds an IEEE stamp or a ScienceDirect pdfft address."""
    from pathlib import Path

    package = Path(scholar_pdf.__file__).resolve().parent
    offenders = [
        path.name
        for path in package.rglob("*.py")
        if any(word in path.read_text(encoding="utf-8") for word in ("stampPDF", "pdfft?", "content/pdf/{"))
    ]
    assert offenders == []


# ---------------------------------------------------------------------------
# Proxying
# ---------------------------------------------------------------------------

def test_generic_http_proxy():
    rewritten = rewrite_via_proxy(
        "https://ieeexplore.ieee.org/document/123",
        "http://proxy.uni.edu:3128",
    )
    assert rewritten == "http://proxy.uni.edu:3128/https://ieeexplore.ieee.org/document/123"


def test_ezproxy_pattern():
    rewritten = rewrite_via_proxy(
        "https://www.sciencedirect.com/science/article/pii/S123",
        "https://proxy.uni.edu/login?url=",
    )
    assert rewritten.startswith("https://proxy.uni.edu/login?url=")
    assert "sciencedirect.com" in rewritten


def test_proxy_noop_on_empty():
    assert rewrite_via_proxy("https://x.org/a.pdf", "") == "https://x.org/a.pdf"
    assert rewrite_via_proxy("", "http://proxy.uni.edu") == ""


# ---------------------------------------------------------------------------
# Subdomain-prefix proxy (SNL *.arn.dz / EZproxy / OpenAthens)
# ---------------------------------------------------------------------------

def test_proxy_style_detection():
    assert proxy_style("https://www.sndl1.arn.dz") == "subdomain"
    assert proxy_style("https://ezproxy.library.uni.edu/login?url=") == "ezproxy"
    assert proxy_style("https://proxy.athens.ac.uk") == "prefix"
    assert proxy_style("http://proxy.uni.edu:3128") == "prefix"


def test_rewrite_via_subdomain_sndl():
    url = rewrite_via_proxy(
        "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=10209481",
        "https://www.sndl1.arn.dz",
    )
    assert url == (
        "https://ieeexplore-ieee-org.www.sndl1.arn.dz/"
        "stampPDF/getPDF.jsp?tp=&arnumber=10209481"
    )


def test_rewrite_via_subdomain_elsevier_sciencedirect():
    url = rewrite_via_proxy(
        "https://www.sciencedirect.com/science/article/pii/S0168169918301234",
        "https://www.sndl1.arn.dz",
    )
    assert url == (
        "https://www-sciencedirect-com.www.sndl1.arn.dz/"
        "science/article/pii/S0168169918301234"
    )


def test_rewrite_via_subdomain_openathens():
    url = rewrite_via_proxy(
        "https://link.springer.com/content/pdf/10.1007/s11263-023-01798-x.pdf",
        "https://proxy.openathens.net",
    )
    assert url.startswith("https://link-springer-com.proxy.openathens.net/")


def test_rewrite_via_subdomain_explicit_style():
    url = rewrite_via_proxy(
        "https://api.crossref.org/works",
        "https://gateway.proxy.university.edu",
        style="subdomain",
    )
    assert url == "https://api-crossref-org.gateway.proxy.university.edu/works"


def test_rewrite_via_subdomain_preserves_query():
    url = rewrite_via_subdomain(
        "https://europepmc.org/articles/PMC1234567?query=foo",
        "www.sndl1.arn.dz",
    )
    assert url == "https://europepmc-org.www.sndl1.arn.dz/articles/PMC1234567?query=foo"


def test_is_proxied_url():
    proxied = "https://ieeexplore-ieee-org.www.sndl1.arn.dz/stampPDF/getPDF.jsp"
    assert is_proxied_url(proxied, "https://www.sndl1.arn.dz") is True
    assert is_proxied_url("https://ieeexplore.ieee.org/stampPDF/getPDF.jsp", "https://www.sndl1.arn.dz") is False
    assert is_proxied_url(proxied, "") is False