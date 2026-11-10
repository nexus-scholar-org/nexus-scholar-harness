"""E3 (M3d-engine; discovery API packet §4.4): the importers say which lines they could not use.

One fixture per format holds each rejection kind: a line outside any record
(``IMPORT_BAD_TAG``), a record without a title (``IMPORT_NO_TITLE``, the record
is not imported) and a year that is not a year (``IMPORT_BAD_YEAR``, the record
is imported without a year).
"""

from __future__ import annotations

from pathlib import Path

from scholar_search.importers import NBIBImporter, RISImporter

FIXTURES = Path(__file__).parent / "fixtures" / "imports"


def test_ris_rejections_name_the_line_and_the_code():
    importer = RISImporter()
    documents = list(importer.parse(FIXTURES / "rejections.ris"))
    assert [d.title for d in documents] == [
        "UAV weed maps in maize", "Drone imagery for weed detection", "A third kept record",
    ]
    assert [d.year for d in documents] == [2021, None, 2019]
    assert [(r["line"], r["code"]) for r in importer.rejected] == [
        (1, "IMPORT_BAD_TAG"),
        (9, "IMPORT_NO_TITLE"),
        (17, "IMPORT_BAD_YEAR"),
    ]
    assert all(r["reason"] for r in importer.rejected)
    assert "in press" in importer.rejected[2]["reason"]


def test_nbib_rejections_name_the_line_and_the_code():
    importer = NBIBImporter()
    documents = list(importer.parse(FIXTURES / "rejections.nbib"))
    assert [d.provider_id for d in documents] == ["1001", "1003", "1004"]
    assert [d.year for d in documents] == [2021, None, 2019]
    assert [(r["line"], r["code"]) for r in importer.rejected] == [
        (6, "IMPORT_NO_TITLE"),
        (12, "IMPORT_BAD_YEAR"),
        (14, "IMPORT_BAD_TAG"),
    ]


def test_a_clean_file_has_no_rejections_and_a_new_parse_starts_empty(tmp_path):
    importer = RISImporter()
    list(importer.parse(FIXTURES / "rejections.ris"))
    assert importer.rejected
    lines = (FIXTURES / "rejections.ris").read_text(encoding="utf-8").splitlines()[1:7]
    clean = tmp_path / "clean.ris"
    clean.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert len(list(importer.parse(clean))) == 1
    assert importer.rejected == []
