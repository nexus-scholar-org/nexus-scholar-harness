"""M11b part D, DoD 19: the five criteria wording checks of record (f).

Plain word rules on the accepted criteria, never blockers, each instance dismissed alone. An
honesty fixture pins what they cannot see: the 2026-11-20 review's mirror ("RGB only" against
"multispectral imagery from a UAV") shares no word, and "uses a learned model" beside "or a dataset
paper" is a contradiction of meaning.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "console"))
from test_inception_proposals import uav_draft  # noqa: E402

from scholar_harness.inception import checks, criteria_wording as cw, steps  # noqa: E402

WORDING = {"CRITERIA_DUPLICATE", "CRITERIA_CONTRADICT", "CRITERIA_MIRRORED", "CRITERIA_LUMPED",
           "CRITERIA_NEEDS_FULL_TEXT", "CRITERIA_WORDING_NOT_CHECKED"}


def _rows(inclusions=("Field trials in row crops",), exclusions=("Greenhouse experiments",), **changes) -> list[dict]:
    """The wording checks of a draft (a typed inclusion makes the proof answer optional)."""
    draft = uav_draft(
        extra_inclusions=list(inclusions),
        extra_exclusions=[{"criterion": e, "reason_category": "OUT_OF_SCOPE"} for e in exclusions],
        **changes,
    )
    return [c for c in checks._criteria_checks(steps.parse_draft(draft)) if c["check_id"] in WORDING]


def _kinds(rows) -> list[str]:
    return sorted(r["check_id"] for r in rows)


def test_two_criteria_of_one_side_with_equal_words_are_a_duplicate():
    rows = _rows(exclusions=["Simulation only", "simulation ONLY!"])
    [dup] = [r for r in rows if r["check_id"] == "CRITERIA_DUPLICATE"]
    assert dup["level"] == "warning" and dup["params"]["side"] == "exclusion" and "|" in dup["subject"]
    assert dup["dismissible"] is True and dup["refusal"] is None


def test_an_inclusion_and_an_exclusion_with_the_same_words_contradict():
    rows = _rows(inclusions=["Field studies with aerial imagery"], exclusions=["field studies, with aerial imagery"])
    [row] = [r for r in rows if r["check_id"] == "CRITERIA_CONTRADICT"]
    assert row["level"] == "warning" and row["action"]["field"] == "extra_exclusions"
    assert "CRITERIA_MIRRORED" not in _kinds(rows)  # equal texts are a contradiction, not a mirror


def test_an_exclusion_that_repeats_an_inclusion_with_a_negation_is_mirrored():
    rows = _rows(inclusions=["Multispectral imagery from a UAV"], exclusions=["Not multispectral UAV imagery"])
    [row] = [r for r in rows if r["check_id"] == "CRITERIA_MIRRORED"]
    assert row["level"] == "warning" and row["threshold"]["value"] == cw.MIRROR_SHARE
    assert sorted(next(e for e in row["evidence"] if e["name"] == "shared")["value"]) == ["imagery", "multispectral", "uav"]


@pytest.mark.parametrize(
    ("inclusion", "exclusion", "mirrored"),
    [
        # 3 of 5 content words of the inclusion: 0.6, at the constant.
        ("Hyperspectral canopy imaging drone surveys", "No hyperspectral canopy drone", True),
        # 2 shared of 5 and of 4: 0.5, below it.
        ("Hyperspectral canopy imaging drone surveys", "Without canopy drone flights indoors", False),
    ],
)
def test_the_mirror_share_is_the_constant(inclusion, exclusion, mirrored):
    assert ("CRITERIA_MIRRORED" in _kinds(_rows(inclusions=[inclusion], exclusions=[exclusion]))) is mirrored


@pytest.mark.parametrize(
    ("text", "lumped"),
    [
        ("UAV imagery; field trials", True),
        ("UAV, satellite or ground imagery", True),
        ("UAV, satellite, or ground imagery", True),
        ("UAV or satellite imagery", False),
        ("UAV, satellite imagery", False),
    ],
)
def test_a_criterion_holding_several_tests_is_a_lumped_note(text, lumped):
    rows = _rows(inclusions=[text])
    found = [r for r in rows if r["check_id"] == "CRITERIA_LUMPED"]
    assert bool(found) is lumped
    if found:
        assert found[0]["level"] == "note"


def test_a_criterion_naming_what_abstracts_rarely_report_needs_the_full_text():
    rows = _rows(inclusions=["Reports the sample size of each trial"])
    [row] = [r for r in rows if r["check_id"] == "CRITERIA_NEEDS_FULL_TEXT"]
    assert row["level"] == "note" and row["params"]["words"] == "sample size, reports the"
    assert row["action"]["field"] == "method_not_reported"
    assert not [r for r in _rows(inclusions=["Uses tabletop robots"]) if r["check_id"] == "CRITERIA_NEEDS_FULL_TEXT"]


def test_honesty_the_word_rules_do_not_see_a_mirror_or_a_contradiction_of_meaning():
    rows = _rows(inclusions=["Multispectral imagery from a UAV"], exclusions=["RGB only"])
    assert "CRITERIA_MIRRORED" not in _kinds(rows)
    rows = _rows(inclusions=["Uses a learned model"], exclusions=["Or a dataset paper"])
    assert not {"CRITERIA_MIRRORED", "CRITERIA_CONTRADICT", "CRITERIA_DUPLICATE"} & set(_kinds(rows))


def test_only_accepted_criteria_are_compared():
    plain = _rows(exclusions=["Simulation only", "simulation ONLY!"])
    [dup] = [r for r in plain if r["check_id"] == "CRITERIA_DUPLICATE"]
    second = dup["subject"].split("|")[1]
    rows = _rows(exclusions=["Simulation only", "simulation ONLY!"], criteria_decisions={second: False})
    assert "CRITERIA_DUPLICATE" not in _kinds(rows)


def test_none_of_the_wording_checks_is_a_blocker_and_each_instance_is_its_own_subject():
    rows = _rows(inclusions=["Field studies with aerial imagery", "UAV imagery; field trials", "Reports the sample size"],
                 exclusions=["field studies with aerial imagery", "Simulation only", "simulation only"])
    assert rows and all(r["level"] in ("warning", "note") and r["dismissible"] for r in rows)
    assert len({(r["check_id"], r["subject"]) for r in rows}) == len(rows)


def test_a_changed_text_is_a_new_subject_so_a_dismissal_does_not_carry_over():
    [before] = [r for r in _rows(exclusions=["Simulation only", "simulation only"]) if r["check_id"] == "CRITERIA_DUPLICATE"]
    [after] = [r for r in _rows(exclusions=["Simulation only", "simulation only."]) if r["check_id"] == "CRITERIA_DUPLICATE"]
    rows = _rows(exclusions=["Simulation studies only", "simulation studies only"])
    [changed] = [r for r in rows if r["check_id"] == "CRITERIA_DUPLICATE"]
    assert changed["subject"] != before["subject"]
    assert after["check_id"] == "CRITERIA_DUPLICATE"


def test_criteria_in_another_language_run_only_the_equality_checks_and_say_so():
    rows = _rows(inclusions=["Études de terrain sur imagerie aérienne"],
                 exclusions=["Pas d'imagerie aérienne de terrain", "Simulation seulement", "simulation seulement"])
    kinds = _kinds(rows)
    assert "CRITERIA_DUPLICATE" in kinds and "CRITERIA_MIRRORED" not in kinds
    [note] = [r for r in rows if r["check_id"] == "CRITERIA_WORDING_NOT_CHECKED"]
    assert note["level"] == "note" and "CRITERIA_MIRRORED" in note["params"]["checks"]
