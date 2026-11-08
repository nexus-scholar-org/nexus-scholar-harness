from pathlib import Path

from scholar_search.export import Exporter
from scholar_search.importers import JSONImporter, JSONLImporter, RISImporter
from scholar_search.models import Author, Document, ExternalIds


def test_json_and_jsonl_export_import_roundtrip(tmp_path: Path):
    docs = [
        Document(
            title="Deep Learning Benchmark",
            year=2022,
            provider="test",
            external_ids=ExternalIds(doi="10.1000/182", arxiv_id="2201.00001"),
            abstract="A comprehensive study on neural networks.",
            authors=[Author(family_name="LeCun", given_name="Yann")],
            venue="ICLR",
            citations_count=450,
        )
    ]
    exporter = Exporter()

    # Test JSON
    json_path = tmp_path / "test.json"
    exporter.json(docs, json_path)
    imported_json = list(JSONImporter().parse(json_path))
    assert len(imported_json) == 1
    assert imported_json[0].title == docs[0].title
    assert imported_json[0].external_ids.doi == "10.1000/182"
    assert imported_json[0].citations_count == 450

    # Test JSONL
    jsonl_path = tmp_path / "test.jsonl"
    exporter.jsonl(docs, jsonl_path)
    imported_jsonl = list(JSONLImporter().parse(jsonl_path))
    assert len(imported_jsonl) == 1
    assert imported_jsonl[0].title == docs[0].title
    assert imported_jsonl[0].authors[0].family_name == "LeCun"

    # Test CSV
    csv_path = tmp_path / "test.csv"
    exporter.csv(docs, csv_path)
    assert csv_path.exists()
    assert "Deep Learning Benchmark" in csv_path.read_text(encoding="utf-8")


def test_ris_importer(tmp_path: Path):
    ris_content = """TY  - JOUR
TI  - The Mathematical Theory of Communication
AU  - Shannon, Claude E.
PY  - 1948
DO  - 10.1002/j.1538-7305.1948.tb01338.x
JO  - Bell System Technical Journal
AB  - Recent development of various methods of modulation...
ER  - 
"""
    ris_path = tmp_path / "shannon.ris"
    ris_path.write_text(ris_content, encoding="utf-8")

    imported = list(RISImporter().parse(ris_path))
    assert len(imported) == 1
    doc = imported[0]
    assert doc.title == "The Mathematical Theory of Communication"
    assert doc.year == 1948
    assert doc.external_ids.doi == "10.1002/j.1538-7305.1948.tb01338.x"
    assert len(doc.authors) == 1
    assert doc.authors[0].family_name == "Shannon"
    assert doc.authors[0].given_name == "Claude E."


# M6-hardening H6: exporters other than IEEE Xplore. The researcher's first
# real import (IEEE, 2026-11-08) worked; a tester's second database must too.
# Authors feed the cross-database dedup (first author), so a dropped A1 tag or
# a cut abstract would not fail loudly; it would weaken matching and screening.

WOS_STYLE = """TY  - JOUR
A1  - Lopez-Granados, Francisca
A1  - Torres-Sanchez, Jorge
T1  - Early season weed mapping in sunflower using UAV technology:
      variability of herbicide treatment maps against weed thresholds
JF  - Precision Agriculture
Y1  - 2016/02/01/
N2  - Site-specific weed management is defined as the application of
      customised control treatments only where weeds are located within the
      crop-field.
DO  - 10.1007/s11119-015-9415-8
ER  -
"""

LENS_STYLE = """TY  - JOUR
AU  - Huang, Huasheng
AU  - Deng, Jizhong
TI  - A fully convolutional network for weed mapping
  of unmanned aerial vehicle (UAV) imagery
T2  - PLOS ONE
PY  - 2018
DO  - 10.1371/journal.pone.0196302
AB  - Appropriate Site Specific Weed Management (SSWM) is crucial to ensure
  the crop yields.
ER  -

TY  - JOUR
AU  - Second, Record
TI  - A second record after a blank line
PY  - 2020
ER  -
"""


def test_ris_importer_reads_a1_authors_and_wrapped_values(tmp_path: Path):
    path = tmp_path / "wos.ris"
    path.write_text(WOS_STYLE, encoding="utf-8")
    (doc,) = list(RISImporter().parse(path))
    assert [(a.family_name, a.given_name) for a in doc.authors] == [
        ("Lopez-Granados", "Francisca"),
        ("Torres-Sanchez", "Jorge"),
    ]
    assert doc.title == (
        "Early season weed mapping in sunflower using UAV technology: "
        "variability of herbicide treatment maps against weed thresholds"
    )
    assert doc.abstract == (
        "Site-specific weed management is defined as the application of "
        "customised control treatments only where weeds are located within the "
        "crop-field."
    )
    assert doc.year == 2016
    assert doc.venue == "Precision Agriculture"
    assert doc.external_ids.doi == "10.1007/s11119-015-9415-8"


def test_ris_importer_reads_lens_style_records(tmp_path: Path):
    path = tmp_path / "lens.ris"
    path.write_text(LENS_STYLE, encoding="utf-8")
    first, second = list(RISImporter().parse(path))
    assert [a.family_name for a in first.authors] == ["Huang", "Deng"]
    assert first.title == (
        "A fully convolutional network for weed mapping of unmanned aerial vehicle (UAV) imagery"
    )
    assert first.abstract == (
        "Appropriate Site Specific Weed Management (SSWM) is crucial to ensure the crop yields."
    )
    assert first.venue == "PLOS ONE" and first.year == 2018
    assert second.title == "A second record after a blank line"
    assert [a.family_name for a in second.authors] == ["Second"]


def test_ris_importer_keeps_au_and_a1_together_in_order(tmp_path: Path):
    """A record carrying both tags keeps every author once, in file order."""
    path = tmp_path / "mixed.ris"
    path.write_text("TY  - JOUR\nAU  - First, A.\nA1  - Second, B.\nTI  - Mixed\nER  - \n", encoding="utf-8")
    (doc,) = list(RISImporter().parse(path))
    assert [a.family_name for a in doc.authors] == ["First", "Second"]


def test_ris_importer_reads_a_crlf_export(tmp_path: Path):
    """Windows exports end lines with CRLF (full review 2026-11-06, missing test)."""
    path = tmp_path / "crlf.ris"
    path.write_bytes(WOS_STYLE.replace("\n", "\r\n").encode("utf-8"))
    (doc,) = list(RISImporter().parse(path))
    assert len(doc.authors) == 2 and doc.abstract.endswith("crop-field.")
