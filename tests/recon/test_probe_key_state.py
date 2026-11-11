"""M4d DoD 1: the recon probe reports each database's key and leg state.

Before M4d the session's probe record kept only ``provider, status,
reported_total, fetched, cap, cap_hit, error``: the OpenAlex key note, the
refusal code of a rejected key and a throttle were dropped, so a thin pool
gave no reason. These tests run the real OpenAlex and Semantic Scholar
providers with their HTTP client replaced (no socket), next to a stub
database that returns the documents.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest
from scholar_search.config import settings
from scholar_search.engine import SearchEngine
from scholar_search.exceptions import ProviderError
from scholar_search.models import Document, ExternalIds, Query
from scholar_search.providers.openalex import OpenAlexProvider
from scholar_search.providers.semanticscholar import SemanticScholarProvider

from scholar_harness.recon.engine import ReconEngine
from scholar_harness.recon.session import ReconSessions


class _Json:
    status_code = 200
    content = b""

    def __init__(self, body):
        self.body = body

    def json(self):
        return self.body


class _StubDatabase:
    """A database that answers with fixed documents (stands in for Crossref)."""

    name = "crossref"

    def __init__(self, n: int = 14):
        self.docs = [
            Document(
                title=f"Weed detection on embedded hardware {i}", year=2023, provider="crossref",
                provider_id=f"C{i}", external_ids=ExternalIds(doi=f"10.9/c{i:03d}"),
                abstract="weed detection with on-device inference",
            )
            for i in range(n)
        ]

    async def search(self, query: Query) -> AsyncIterator[Document]:
        for doc in self.docs:
            yield doc


def _openalex(answer) -> OpenAlexProvider:
    provider = OpenAlexProvider()

    async def get(url, params=None, **kwargs):
        if isinstance(answer, int):
            raise ProviderError("openalex", "refused", status_code=answer)
        return _Json(answer)

    provider.client.get = get
    return provider


def _s2(status: int | None) -> SemanticScholarProvider:
    provider = SemanticScholarProvider()

    async def get(url, params=None, headers=None, **kwargs):
        if status is None:
            return _Json({"total": 0, "data": []})
        raise ProviderError("semanticscholar", '{"message":"Forbidden"}', status_code=status)

    provider.client.get = get
    return provider


@pytest.fixture(autouse=True)
def _contact(monkeypatch):
    monkeypatch.setattr(settings, "mailto", "tester@example.org")
    monkeypatch.setattr(settings, "openalex_key", None)
    monkeypatch.setattr(settings, "s2_key", None)


def _probe(tmp_path, monkeypatch, providers) -> dict:
    monkeypatch.delenv("NEXUS_RECON_ROOT", raising=False)
    engine = ReconEngine(cache_root=tmp_path)
    monkeypatch.setattr(engine, "_build_engine", lambda names: SearchEngine(providers=providers))
    sessions = ReconSessions(engine=engine)
    names = [p.name for p in providers]
    return asyncio.run(sessions.probe("weed detection", session_id="rec_" + "a" * 32, providers=names))


def _leg(record: dict, provider: str) -> dict:
    return next(leg for leg in record["legs"] if leg["provider"] == provider)


def test_without_an_openalex_key_the_leg_says_the_key_is_missing(tmp_path, monkeypatch):
    record = _probe(tmp_path, monkeypatch, [_openalex({"results": [], "meta": {"count": 0}}), _StubDatabase()])
    leg = _leg(record, "openalex")
    assert leg["status"] == "ok"
    assert leg["key_set"] is False
    assert any("SCHOLAR_OPENALEX_KEY" in note for note in leg["notes"]), leg


def test_an_openalex_key_refusal_fails_the_leg_and_names_the_key(tmp_path, monkeypatch):
    record = _probe(tmp_path, monkeypatch, [_openalex(409), _StubDatabase()])
    leg = _leg(record, "openalex")
    assert (leg["status"], leg["error_code"]) == ("failed", "PROVIDER_REFUSED")
    assert any("SCHOLAR_OPENALEX_KEY" in note and "409" in note for note in leg["notes"]), leg
    assert record["status"] == "partial"


def test_a_rejected_semantic_scholar_key_fails_the_leg_and_names_the_key(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "s2_key", "s2-placeholder")
    record = _probe(tmp_path, monkeypatch, [_s2(403), _StubDatabase()])
    leg = _leg(record, "semanticscholar")
    assert (leg["status"], leg["error_code"], leg["key_set"]) == ("failed", "PROVIDER_REFUSED", True)
    assert any("SCHOLAR_S2_KEY" in note for note in leg["notes"]), leg
    assert "s2-placeholder" not in repr(record)
    assert record["status"] == "partial"


def test_a_throttled_semantic_scholar_leg_says_it_was_rate_limited(tmp_path, monkeypatch):
    record = _probe(tmp_path, monkeypatch, [_s2(429), _StubDatabase()])
    leg = _leg(record, "semanticscholar")
    assert (leg["status"], leg["error_code"], leg["key_set"]) == ("failed", "PROVIDER_RATE_LIMITED", False)


def test_databases_without_a_key_report_no_key_state(tmp_path, monkeypatch):
    record = _probe(tmp_path, monkeypatch, [_StubDatabase()])
    assert _leg(record, "crossref")["key_set"] is None
