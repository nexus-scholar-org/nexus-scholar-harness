"""E3 (M3d-engine; discovery API packet §4.4): the importers say which lines they could not use.

One fixture per format holds each rejection kind: a line outside any record
(``IMPORT_BAD_TAG``), a record without a title (``IMPORT_NO_TITLE``, the record
is still imported, as "Unknown Title", so no later record's position or id moves) and a year that is not a year (``IMPORT_BAD_YEAR``, the record
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
        "UAV weed maps in maize", "Unknown Title", "Drone imagery for weed detection", "A third kept record",
    ]
    assert [d.year for d in documents] == [2021, 2020, None, 2019]
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
    assert [d.provider_id for d in documents] == ["1001", "1002", "1003", "1004"]
    assert documents[1].title == "Unknown Title"
    assert [d.year for d in documents] == [2021, 2020, None, 2019]
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


def test_a_titleless_record_moves_no_later_records_position_or_id(tmp_path):
    """Review F1: a rejection is reported, never removed, so positions and SCI ids stay as before E3."""
    import shutil

    from scholar_harness.corpus_accept import _parse_export, _stable_sci_id

    stored = tmp_path / "scopus-00000000.ris"
    shutil.copy2(FIXTURES / "rejections.ris", stored)
    documents = _parse_export(stored, "scopus-00000000", "ris")
    assert [d.provider_id for d in documents] == [f"scopus-00000000#{i}" for i in range(1, 5)]
    third = documents[2]
    assert third.title == "Drone imagery for weed detection"
    assert third.workspace_id == _stable_sci_id(third, source="scopus-00000000", position=3)
