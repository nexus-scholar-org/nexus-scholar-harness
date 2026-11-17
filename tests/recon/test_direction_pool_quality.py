"""M10a OBS-4: a sample chosen by relevance gives directions anchored in on-topic records.

The records are the ones the golden recon cassette recorded for "UAV crop weed
mapping" (OpenAlex, Crossref, arXiv; Semantic Scholar answered 429), read
offline with each database's own normalizer, in recorded order, at most 25
per database. The old sample (``deduplicate(stable_order(...))[:25]``) is
compared with :func:`relevance_sample`, and the real distiller and direction
code run on both. On-topic means "weed" or "weeds" occurs in the title or
abstract.

Three checks: (a) at least 80 % of each new direction's anchors are on-topic, (b) the
new sample holds more on-topic DOI records, (c) the new directions are
observed in at least as many records. All three separate old from new in both
cases. The numbers were measured on 2026-11-15, after the researcher recorded
the arXiv answer to the AND query again (decision 3a, 2026-11-14).

Known limitation: generic labels such as "convolutional neural network" still
appear among the directions. They come from the direction scorer, which M10a
does not tune; this test only shows they are now anchored in on-topic records.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
import yaml
from scholar_search.dedup import Deduplicator, stable_order
from scholar_search.models import Document
from scholar_search.providers import ArxivProvider, CrossrefProvider, OpenAlexProvider

from scholar_harness.recon.distiller import distill_pool
from scholar_harness.recon.engine import POOL_MAX, _doc_to_pool_entry, relevance_sample
from scholar_harness.recon.session import directions_for, term_occurs

ROOT = Path(__file__).resolve().parents[2]
CASSETTE = ROOT / "tests" / "fixtures" / "cassettes" / "golden_recon_probe.yaml"
TOPIC = "UAV crop weed mapping"
YEARS = (2020, 2026)
ORDER = ["openalex", "semanticscholar", "crossref", "arxiv"]

pytestmark = pytest.mark.skipif(not CASSETTE.exists(), reason="golden recon cassette not recorded")


def _openalex_keeps(year: int | None) -> bool:
    """OpenAlex's client-side rule: a record without a year is kept."""
    return not year or YEARS[0] <= year <= YEARS[1]


def _arxiv_keeps(year: int | None) -> bool:
    """arXiv's client-side rule (``ArxivProvider.search``): a record without a year is dropped."""
    return (year or 0) >= YEARS[0] and (year or 9999) <= YEARS[1]


def _recorded(databases: list[str]) -> list[Document]:
    """The recorded records of ``databases``, fresh objects, each database in its own order.

    Each database's client-side year filter is applied as its provider applies
    it, and they differ: OpenAlex keeps a record without a year, arXiv drops
    it, and Crossref has none (its years are filtered by the server only).
    """
    interactions = yaml.safe_load(CASSETTE.read_text(encoding="utf-8"))["interactions"]
    openalex, crossref, arxiv = OpenAlexProvider(), CrossrefProvider(), ArxivProvider()
    found: dict[str, list[Document]] = {"openalex": [], "crossref": [], "arxiv": []}
    arxiv_pages: list[tuple[int, str]] = []
    for item in interactions:
        if item["response"]["status"]["code"] != 200:
            continue
        url = urlparse(item["request"]["uri"])
        body = item["response"]["body"]["string"]
        if url.netloc == "api.openalex.org":
            for raw in json.loads(body)["results"]:
                if _openalex_keeps(raw.get("publication_year")):
                    found["openalex"].append(openalex._normalize_document(raw))
        elif url.netloc == "api.crossref.org":
            found["crossref"] += [crossref._normalize_document(raw) for raw in json.loads(body)["message"]["items"]]
        elif url.netloc == "export.arxiv.org":
            arxiv_pages.append((int(parse_qs(url.query).get("start", ["0"])[0]), body))
    for _start, body in sorted(arxiv_pages):
        data = body.encode("utf-8") if isinstance(body, str) else body
        for entry in ET.fromstring(data).findall("atom:entry", arxiv.ns):
            doc = arxiv._parse_xml_entry(entry)
            if _arxiv_keeps(doc.year):
                found["arxiv"].append(doc)
    return [doc for name in ORDER if name in databases for doc in found.get(name, [])[:POOL_MAX]]


def _on_topic(entry: dict) -> bool:
    text = f"{entry.get('title') or ''} {entry.get('abstract') or ''}"
    return term_occurs("weed", text) or term_occurs("weeds", text)


def _measure(docs: list[Document]) -> dict:
    pool = {"docs": [_doc_to_pool_entry(d) for d in docs[:POOL_MAX]]}
    directions = directions_for(distill_pool(pool, query_text=TOPIC), pool)
    by_doi = {d["doi"]: d for d in pool["docs"] if d["doi"]}

    def share(direction: dict) -> float:
        anchors = direction["anchor_dois"]
        # A direction without anchors counts as off-topic, never as a division by zero.
        return sum(_on_topic(by_doi[doi]) for doi in anchors) / len(anchors) if anchors else 0.0

    return {
        "directions": directions,
        "on_topic_share": [share(d) for d in directions],
        "on_topic_doi_records": sum(1 for d in pool["docs"] if d["doi"] and _on_topic(d)),
    }


@pytest.mark.parametrize(
    "databases",
    [["openalex", "crossref", "arxiv"], ["openalex", "crossref"]],
    ids=["recorded", "without-arxiv"],
)
def test_relevance_sample_anchors_directions_in_on_topic_records(databases):
    old = _measure([c.representative for c in Deduplicator().deduplicate(stable_order(_recorded(databases)))])
    new = _measure(relevance_sample(_recorded(databases), ORDER, Deduplicator()))

    assert new["directions"], "the relevance sample proposes directions"
    assert old["directions"], "the old sample proposes directions, so (c) compares two real values"
    # (a) Measured 2026-11-15: every new anchor on-topic in both cases; old 1.0/0.4/0.4 with arXiv, 0.0 without.
    assert all(share >= 0.8 for share in new["on_topic_share"]), new["on_topic_share"]
    # (b) Measured: 2 -> 11 with arXiv, 0 -> 12 without. All DOI records: 21 -> 20 with arXiv and
    # 25 -> 24 without (the old rule fills with off-topic Crossref records), so on-topic ones are compared.
    assert new["on_topic_doi_records"] > old["on_topic_doi_records"]
    # (c) Measured: 2 -> 4 with arXiv, 2 -> 4 without.
    assert min(d["observed_in"] for d in new["directions"]) >= min(d["observed_in"] for d in old["directions"])
