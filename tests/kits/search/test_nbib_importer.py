"""M5c-nbib: the PubMed MEDLINE ``.nbib`` importer.

PubMed's *Send to → Citation manager* writes MEDLINE format: a four-character
tag padded with spaces, ``- ``, the value; a wrapped value continues on lines
that start with spaces; a blank line separates records; a tag may repeat
(``MH``, ``PT``, ``AU``/``FAU``, ``AID``). The fixture is a hand-written export
of five records with the shapes PubMed actually produces.
"""

from __future__ import annotations

from pathlib import Path

from scholar_search.importers import NBIBImporter

FIXTURE = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "pubmed" / "pubmed_uav_weeds.nbib"


def _parse(path: Path):
    return list(NBIBImporter().parse(path))


def test_the_fixture_yields_one_document_per_record():
    docs = _parse(FIXTURE)
    assert [d.external_ids.pubmed_id for d in docs] == ["30000001", "30000002", "30000003", "30000004", "30000005"]
    assert {d.provider for d in docs} == {"local_nbib"}
    assert [d.provider_id for d in docs] == [d.external_ids.pubmed_id for d in docs]
    assert all(d.retrieved_at is not None for d in docs)


def test_wrapped_title_and_abstract_are_joined_with_one_space():
    first = _parse(FIXTURE)[0]
    assert first.title == (
        "Deep learning-based weed detection in maize fields from multispectral UAV "
        "imagery: a comparison of convolutional architectures."
    )
    assert first.abstract is not None
    assert first.abstract.startswith("Site-specific weed management depends on accurate weed maps. We compared three")
    assert "three convolutional architectures" in first.abstract
    assert first.abstract.endswith("prescription maps.")
    assert "  " not in first.abstract and "\n" not in first.abstract


def test_fau_is_preferred_over_au_and_keeps_family_and_given_names():
    first = _parse(FIXTURE)[0]
    assert [(a.family_name, a.given_name) for a in first.authors] == [
        ("Rossi", "Marco"),
        ("Chen", "Li"),
        ("van der Berg", "Anna"),
    ]


def test_au_is_the_fallback_when_a_record_has_no_fau():
    second = _parse(FIXTURE)[1]
    assert [(a.family_name, a.given_name) for a in second.authors] == [("Okafor", "N"), ("Dubois", "P")]


def test_the_doi_comes_from_aid_then_lid_and_pii_is_ignored():
    docs = _parse(FIXTURE)
    assert docs[0].external_ids.doi == "10.1000/m5c-1"  # AID [doi], not the [pii]
    assert docs[1].external_ids.doi == "10.1000/m5c-2"
    assert docs[2].external_ids.doi == "10.1000/m5c-3"  # LID [doi] only
    assert docs[3].external_ids.doi is None  # a letter with no DOI at all
    assert docs[4].external_ids.doi == "10.1000/m5c-5"


def test_year_is_the_first_four_digits_of_dp():
    assert [d.year for d in _parse(FIXTURE)] == [2024, 2023, 2022, 2024, 2021]


def test_venue_prefers_the_full_journal_title_over_the_abbreviation():
    docs = _parse(FIXTURE)
    assert docs[0].venue == "Sensors (Basel, Switzerland)"  # JT over TA
    assert docs[3].venue == "Precis Agric"  # TA only
    assert docs[4].venue == "Computers and electronics in agriculture"  # JT only


def test_repeated_tags_are_collected_not_overwritten():
    first = _parse(FIXTURE)[0]
    assert first.mesh_terms == [
        "*Deep Learning",
        "Zea mays",
        "*Plant Weeds",
        "Remote Sensing Technology/*methods",
        "Agriculture/methods",
    ]
    assert first.raw_data is not None
    assert first.raw_data["publication_types"] == ["Journal Article", "Comparative Study"]
    assert first.raw_data["keywords"] == ["UAV", "precision agriculture", "weed mapping"]
    assert first.raw_data["language"] == ["eng"]
    third = _parse(FIXTURE)[2]
    assert third.raw_data["language"] == ["eng", "fre"]
    assert third.raw_data["publication_types"] == ["Journal Article", "Review"]


def test_a_bom_crlf_export_without_a_trailing_blank_line_is_read(tmp_path: Path):
    raw = (
        b"\xef\xbb\xbfPMID- 1\r\nTI  - Caf\xc3\xa9 weeds on one\r\n      line two\r\nDP  - 2020 Jan\r\n"
        b"FAU - Dupont, Jean\r\nAU  - Dupont J\r\n\r\n\r\n"
        b"PMID- 2\r\nTI  - Second\r\nDP  - 2019\r\nAU  - Lee K\r\n"
    )
    path = tmp_path / "pubmed.txt"
    path.write_bytes(raw)
    docs = _parse(path)
    assert [(d.external_ids.pubmed_id, d.title, d.year) for d in docs] == [
        ("1", "Café weeds on one line two", 2020),
        ("2", "Second", 2019),
    ]
    assert docs[0].authors[0].given_name == "Jean"
    assert (docs[1].authors[0].family_name, docs[1].authors[0].given_name) == ("Lee", "K")


def test_a_new_pmid_without_a_blank_line_starts_a_new_record(tmp_path: Path):
    path = tmp_path / "glued.nbib"
    path.write_text("PMID- 10\nTI  - One\nPMID- 11\nTI  - Two\n", encoding="utf-8")
    assert [(d.external_ids.pubmed_id, d.title) for d in _parse(path)] == [("10", "One"), ("11", "Two")]


def test_a_file_without_medline_tags_yields_nothing(tmp_path: Path):
    path = tmp_path / "not.nbib"
    path.write_text("TY  - JOUR\nTI  - A RIS record\nER  - \n", encoding="utf-8")
    assert _parse(path) == []
