"""M7-method M9: the methods paragraph reports the method values in force.

Spec 10 amendment 2026-11-08 (wording verbatim). The dedup and not-reported
sentences are always written (they state values in force, not changed
settings); a source sentence says whether the values come from the signed
protocol or are the harness defaults. ``figures.method`` carries them all.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from test_export_api import BASE, client_for, decide, publish
from test_methods_api import _assert_no_forbidden, _assert_numbers_trace
from test_screening_events import _build

DEDUP_DEFAULT = (
    "Duplicates across databases were removed by exact DOI and by title similarity of at least 0.97 "
    "with the same first author and publication years at most 1 year apart."
)
UNCLEAR = "A criterion the title and abstract did not report sent the record to full-text assessment."
EXCLUDE = "An inclusion criterion the title and abstract did not report excluded the record."
FROM_DEFAULTS = "These are the harness defaults (screening-rules-v1); the protocol does not set them."
FROM_PROTOCOL = "These values are set in the signed protocol."


def _published(tmp_path: Path, method: dict | None) -> Path:
    ws = _build(tmp_path, method=method)
    decide(ws)
    publish(ws)
    return ws


def _methods(ws: Path) -> dict:
    response = client_for(ws).get(f"{BASE}/methods")
    assert response.status_code == 200, response.text
    return response.json()


def _block(**over) -> dict:
    block = {
        "dedup": {"doi": True, "title_similarity": 0.97, "first_author": True, "year_tolerance": 1},
        "rules_version": "screening-rules-v1",
        "not_reported": "unclear",
        "blinding": "reveal_after_decision",
    }
    for key, value in over.items():
        if key in block["dedup"]:
            block["dedup"][key] = value
        else:
            block[key] = value
    return block


def test_without_a_block_the_paragraph_names_the_defaults(tmp_path):
    body = _methods(_published(tmp_path, None))
    text = body["paragraph"]
    for sentence in (DEDUP_DEFAULT, UNCLEAR, FROM_DEFAULTS):
        assert sentence in text
    assert FROM_PROTOCOL not in text
    # Placement: dedup right after PRISMA; not-reported and source right after the screener.
    assert text.index("were included.") < text.index(DEDUP_DEFAULT)
    assert text.index("One reviewer screened every record.") < text.index(UNCLEAR) < text.index(FROM_DEFAULTS)
    method = dict(body["figures"]["method"])
    assert method.pop("reporting_source") == "playbook" and method.pop("reporting")  # M7b-guideline
    method.pop("reporting_label")
    assert method == {
        "dedup": {"doi": True, "title_similarity": 0.97, "first_author": True, "year_tolerance": 1},
        "rules_version": "screening-rules-v1",
        "not_reported": "unclear",
        "blinding": "reveal_after_decision",
        "source": "defaults",
    }


def test_with_a_block_the_paragraph_reports_its_values(tmp_path):
    block = _block(title_similarity=0.93, first_author=False, year_tolerance=0, not_reported="exclude", blinding="show")
    body = _methods(_published(tmp_path, block))
    text = body["paragraph"]
    assert (
        "Duplicates across databases were removed by exact DOI and by title similarity of at least 0.93 "
        "with the same publication year."
    ) in text
    assert EXCLUDE in text and UNCLEAR not in text
    assert FROM_PROTOCOL in text and FROM_DEFAULTS not in text
    assert body["figures"]["method"]["source"] == "protocol"
    assert body["figures"]["method"]["dedup"]["title_similarity"] == 0.93
    # Blinding from the protocol is the value in force (no agent ran here, so the
    # reveal sentence is not written; the figure carries it).
    assert body["figures"]["blinding"]["at_publish"] == "show"


@pytest.mark.parametrize(
    ("over", "clause"),
    [
        ({"year_tolerance": 2}, "with the same first author and publication years at most 2 years apart."),
        ({"year_tolerance": 0}, "with the same first author and the same publication year."),
        ({"first_author": False}, "with publication years at most 1 year apart."),
    ],
)
def test_the_dedup_sentence_follows_each_value(tmp_path, over, clause):
    text = _methods(_published(tmp_path, _block(**over)))["paragraph"]
    dedup = next(s for s in text.split(". ") if s.startswith("Duplicates across databases"))
    assert (dedup.rstrip(".") + ".").endswith(clause)


# M7b-guideline G5: the guideline sentence follows the source sentence.
GUIDELINE = {
    "prisma-2020": "The screening is reported following PRISMA 2020.",
    "prisma-scr": "The screening is reported following PRISMA-ScR, the PRISMA extension for scoping reviews.",
}


@pytest.mark.parametrize("reporting", ["prisma-2020", "prisma-scr", "none"])
def test_the_methods_paragraph_names_the_guideline(tmp_path, reporting):
    body = _methods(_published(tmp_path, _block(reporting=reporting)))
    text = body["paragraph"]
    for value, sentence in GUIDELINE.items():
        assert (sentence in text) == (value == reporting)
    if reporting != "none":
        assert text.index(FROM_PROTOCOL) < text.index(GUIDELINE[reporting])
    assert "reported following" not in text or reporting != "none"
    assert (body["figures"]["method"]["reporting"], body["figures"]["method"]["reporting_source"]) == (reporting, "protocol")
    # Review 1: "PRISMA 2020" carries a number; it must trace to a figure, and no banned word appears.
    assert body["figures"]["method"]["reporting_label"] == {"prisma-2020": "PRISMA 2020", "prisma-scr": "PRISMA-ScR"}.get(reporting)
    _assert_numbers_trace(body)
    _assert_no_forbidden(text)


def test_without_a_key_the_guideline_comes_from_the_playbook(tmp_path):
    body = _methods(_published(tmp_path, None))
    assert body["figures"]["method"]["reporting_source"] == "playbook"
    assert body["figures"]["method"]["reporting"] in ("prisma-2020", "prisma-scr", "none")
