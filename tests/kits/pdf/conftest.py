"""The PDF kit's tests run with a known test contact address.

K0 (M12a item 27) makes the contact e-mail required; a developer's own
``SCHOLAR_MAILTO`` or ``MAILTO`` must not decide whether a test passes. Tests
of the refusal blank both again.

Part K item 4: OpenAlex is asked only with ``SCHOLAR_OPENALEX_KEY``. The tests
run with a made-up test key, so both services are asked as before; the tests of
the keyless case blank it. A developer's own key never reaches a test.
"""

from __future__ import annotations

import pytest

TEST_CONTACT = "kit-tests@example.org"
TEST_OPENALEX_KEY = "kit-test-openalex-key-not-real"


@pytest.fixture(autouse=True)
def _test_contact_address(monkeypatch):
    from scholar_search import config as search_config

    from scholar_pdf import config as pdf_config

    monkeypatch.setattr(search_config.settings, "mailto", None)
    monkeypatch.setattr(search_config.settings, "openalex_key", TEST_OPENALEX_KEY)
    monkeypatch.setattr(pdf_config.settings, "mailto", TEST_CONTACT)
    monkeypatch.setattr(pdf_config.settings, "proxy_url", "")
    monkeypatch.setattr(pdf_config.settings, "enable_publisher_direct_patterns", False)
