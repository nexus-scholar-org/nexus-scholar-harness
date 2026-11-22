"""M12a Part F (DoD F7): an arXiv id keeps its archive, and its version is read apart.

Found while sizing F7: the provider kept only the part of the entry's id after
the last ``/`` and cut it at the first ``v``, so ``hep-th/9901001v2`` became
``9901001`` (another paper, or none) and ``solv-int/9901001v1`` became ``sol``.
The fetch looks a record up by this id, so the parsing is fixed first.

Offline: the entries are read from a hand-made Atom answer
(``fixtures/arxiv_id_list_handmade.xml``; see its header), never a request.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from scholar_search.providers.arxiv import ArxivProvider, split_arxiv_id

FIXTURE = Path(__file__).parent / "fixtures" / "arxiv_id_list_handmade.xml"


def _entry(id_text: str) -> ET.Element:
    return ET.fromstring(
        '<entry xmlns="http://www.w3.org/2005/Atom">'
        f"<id>{id_text}</id><title>T</title><published>1999-01-04T00:00:00Z</published></entry>"
    )


@pytest.mark.parametrize(
    ("id_text", "expected"),
    [
        ("http://arxiv.org/abs/hep-th/9901001v2", "hep-th/9901001"),
        ("http://arxiv.org/abs/hep-th/9901001", "hep-th/9901001"),
        ("http://arxiv.org/abs/solv-int/9901001v1", "solv-int/9901001"),
        ("http://arxiv.org/abs/math.AG/0601001v1", "math.AG/0601001"),
        ("http://arxiv.org/abs/2101.01234v3", "2101.01234"),
        ("http://arxiv.org/abs/2101.01234", "2101.01234"),
        ("https://arxiv.org/abs/1501.00001v12", "1501.00001"),
    ],
)
def test_an_entry_id_keeps_its_archive_and_loses_only_its_version(id_text, expected):
    document = ArxivProvider()._parse_xml_entry(_entry(id_text))
    assert document.external_ids.arxiv_id == expected
    assert document.provider_id == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("hep-th/9901001v2", ("hep-th/9901001", "v2")),
        ("hep-th/9901001", ("hep-th/9901001", None)),
        ("solv-int/9901001v1", ("solv-int/9901001", "v1")),
        ("2101.01234v3", ("2101.01234", "v3")),
        ("arXiv:2101.01234", ("2101.01234", None)),
        ("http://arxiv.org/abs/hep-th/9901001v2", ("hep-th/9901001", "v2")),
        ("9901001", (None, None)),  # an old-style number without its archive names no paper
        ("not an id", (None, None)),
        ("", (None, None)),
    ],
)
def test_split_arxiv_id(text, expected):
    assert split_arxiv_id(text) == expected


def test_every_entry_of_the_hand_made_answer_keeps_its_archive():
    provider = ArxivProvider()
    root = ET.fromstring(FIXTURE.read_bytes())
    ids = [
        provider._parse_xml_entry(entry).external_ids.arxiv_id
        for entry in root.findall("atom:entry", provider.ns)
    ]
    assert ids[:3] == ["2101.01234", "hep-th/9901001", "solv-int/9901001"]


# ----------------------------------------------------------------- the look-up by id (DoD F7)


class _Response:
    def __init__(self, content: bytes):
        self.content = content
        self.text = content.decode("utf-8")


class _RecordingClient:
    """Stands for the lookup client: answers the hand-made feed, records each request."""

    def __init__(self, content: bytes):
        self.content = content
        self.calls: list[tuple[str, dict]] = []

    async def get(self, url, params=None, **kwargs):
        self.calls.append((url, dict(params or {})))
        return _Response(self.content)


def test_the_answer_gives_the_pdf_link_as_arxiv_gives_it_the_version_and_a_journal_doi():
    found = ArxivProvider().parse_id_list(FIXTURE.read_bytes())

    assert set(found) == {"2101.01234", "hep-th/9901001", "solv-int/9901001"}  # the error entry is left out
    new = found["2101.01234"]
    assert new.pdf_url == "http://arxiv.org/pdf/2101.01234v3"  # as given, not rebuilt
    assert new.version == "v3"
    assert new.doi == "10.1234/journal.2021.001"
    assert new.license is None  # the documented answer carries none
    old = found["hep-th/9901001"]
    assert (old.pdf_url, old.version, old.doi) == ("http://arxiv.org/pdf/hep-th/9901001v2", "v2", None)


@pytest.mark.asyncio
async def test_several_ids_go_in_one_request_with_max_results_and_without_versions():
    client = _RecordingClient(FIXTURE.read_bytes())
    provider = ArxivProvider()
    found = await provider.lookup_ids(
        ["2101.01234v1", "hep-th/9901001", "solv-int/9901001", "9901001", "2101.01234"], client=client
    )

    assert client.calls == [
        (
            "https://export.arxiv.org/api/query",
            {"id_list": "2101.01234,hep-th/9901001,solv-int/9901001", "max_results": 3},
        )
    ]
    assert set(found) == {"2101.01234", "hep-th/9901001", "solv-int/9901001"}


@pytest.mark.asyncio
async def test_more_ids_than_one_request_takes_are_asked_in_turn(monkeypatch):
    from scholar_search.providers import arxiv as module

    monkeypatch.setattr(module, "ID_LIST_CHUNK", 2)
    client = _RecordingClient(FIXTURE.read_bytes())
    await ArxivProvider().lookup_ids(["2101.01234", "hep-th/9901001", "solv-int/9901001"], client=client)
    assert [call[1]["id_list"] for call in client.calls] == ["2101.01234,hep-th/9901001", "solv-int/9901001"]


def test_the_api_host_is_paced_at_one_request_every_three_seconds():
    from scholar_search.http_client import ARXIV_RATE, host_budget, reset_host_budgets

    reset_host_budgets()
    try:
        assert ARXIV_RATE == pytest.approx(1 / 3)
        budget = host_budget(ArxivProvider().base_url)
        assert budget is not None and budget.rate == pytest.approx(ARXIV_RATE) and budget.capacity == 1.0
    finally:
        reset_host_budgets()
