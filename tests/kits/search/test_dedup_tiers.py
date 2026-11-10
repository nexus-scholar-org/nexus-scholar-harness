"""E4a (M3d-engine): the deduplicator records which tier merged each record."""

from __future__ import annotations

from scholar_search.dedup import Deduplicator, stable_order
from scholar_search.models import Author, Document, ExternalIds


def _doc(pid, title, *, doi=None, year=2021, author="Lopez", provider="openalex"):
    return Document(title=title, year=year, provider=provider, provider_id=pid,
                    external_ids=ExternalIds(doi=doi), authors=[Author(family_name=author)])


def _docs():
    return [
        _doc("a1", "Weed maps from UAV imagery", doi="10.1/a"),
        _doc("a2", "Weed Maps from UAV Imagery!", doi="10.1/A", provider="crossref"),
        _doc("b1", "Deep learning for drone weed detection"),
        _doc("b2", "Deep learning for drone weed detection", provider="crossref"),
        _doc("c1", "Site specific herbicide prescription maps for maize fields in spring"),
        _doc("c2", "Site-specific herbicide prescription maps for maize field in spring", provider="crossref"),
        _doc("d1", "An unrelated singleton"),
    ]


def test_each_merge_names_its_tier_and_a_singleton_has_none():
    clusters = Deduplicator().deduplicate(stable_order(_docs()))
    by_first = {m.provider_id: c for c in clusters for m in c.members}
    assert by_first["a1"].tier == "identifier" and by_first["a1"].merges == ["identifier"]
    assert by_first["b1"].tier == "exact_title"
    assert by_first["c1"].tier == "fuzzy_title"
    assert by_first["d1"].tier is None and by_first["d1"].merges == []


def test_recording_tiers_changes_no_cluster_or_id():
    """Characterization taken before E4a (stable_order puts crossref first)."""
    plain = [(c.cluster_id, c.representative.workspace_id, [m.provider_id for m in c.members])
             for c in Deduplicator().deduplicate(stable_order(_docs()))]
    assert plain == [
        (1, "SCI-000001", ["a2", "a1"]),
        (2, "SCI-000002", ["b2", "b1"]),
        (3, "SCI-000003", ["c2", "c1"]),
        (4, "SCI-000004", ["d1"]),
    ]
