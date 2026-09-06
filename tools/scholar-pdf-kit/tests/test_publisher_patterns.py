from scholar_pdf.publisher_patterns import (
    compute_direct_pdf_from_landing_url,
    resolve_doi_to_publisher_pdf,
    rewrite_via_proxy,
)

# ---------------------------------------------------------------------------
# DOI → direct PDF
# ---------------------------------------------------------------------------

def test_ieee_doi_pattern():
    url = resolve_doi_to_publisher_pdf("10.1109/CVPR.2023.01432")
    assert url == "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=01432"


def test_springer_doi_pattern():
    url = resolve_doi_to_publisher_pdf("10.1007/s11263-023-01798-x")
    assert url == "https://link.springer.com/content/pdf/10.1007/s11263-023-01798-x.pdf"


def test_arxiv_doi_pattern():
    url = resolve_doi_to_publisher_pdf("10.48550/arXiv.2010.11929")
    assert url == "https://arxiv.org/pdf/arXiv.2010.11929.pdf"


def test_unknown_doi_returns_none():
    assert resolve_doi_to_publisher_pdf("10.1234/unknown.1234") is None
    assert resolve_doi_to_publisher_pdf("") is None
    assert resolve_doi_to_publisher_pdf(None) is None


# ---------------------------------------------------------------------------
# Landing page → direct PDF
# ---------------------------------------------------------------------------

def test_ieee_landing_pattern():
    url = compute_direct_pdf_from_landing_url("https://ieeexplore.ieee.org/document/01234567")
    assert url == "https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=01234567"


def test_elsevier_landing_pattern():
    url = compute_direct_pdf_from_landing_url(
        "https://www.sciencedirect.com/science/article/pii/S0168169918301234"
    )
    assert url == (
        "https://www.sciencedirect.com/science/article/pii/S0168169918301234/"
        "pdfft?isDTMRedir=true&download=true"
    )


def test_springer_landing_pattern():
    url = compute_direct_pdf_from_landing_url(
        "https://link.springer.com/article/10.1007/s11263-023-01798-x"
    )
    assert url == "https://link.springer.com/content/pdf/10.1007/s11263-023-01798-x.pdf"


def test_arxiv_landing_pattern():
    url = compute_direct_pdf_from_landing_url("https://arxiv.org/abs/2010.11929")
    assert url == "https://arxiv.org/pdf/2010.11929.pdf"


def test_unrecognized_landing_returns_none():
    assert compute_direct_pdf_from_landing_url("https://example.com/papers/foo") is None
    assert compute_direct_pdf_from_landing_url("") is None
    assert compute_direct_pdf_from_landing_url(None) is None


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