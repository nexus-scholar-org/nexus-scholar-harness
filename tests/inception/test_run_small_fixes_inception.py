"""H-run-small-fixes Part C: Inception defects found by the acceptance run of 2026-11-20.

Finding 1: the proof answer ("a table of ...") became an inclusion criterion
("Reports the gold-standard proof — ..."), which is not a screening rule.
Finding 2: the out-of-scope answer, typed as one line of items separated by
semicolons, became one lumped exclusion, accepted without a decision.
Findings 3 and 23: proposed directions such as "aerial vehicle uav" and "blue
green red"; a direction the researcher typed needed the exact phrase in two
papers, so a natural phrase scored 0 of 25.
Finding 4: "No start year is set. The first search used 2000" on a new draft
with no search.
"""

from __future__ import annotations

from scholar_harness.inception import checks, steps
from scholar_harness.inception.intent import CriterionDraft
from scholar_harness.recon import directions

TS = "2026-11-20T09:00:00+00:00"


def draft(**over) -> dict:
    base = {
        "topic": "Sensor stress in UAV multispectral weed segmentation",
        "paradigm": "Positivist",
        "playbook": "PRISMA_SLR",
        "unit_of_analysis": "segmentation models",
        "proof": "A table of mIoU per band combination on field data",
        "rqs": ["How robust is multispectral weed segmentation to sensor stress?"],
        "concepts": [{"concept": "weed segmentation", "synonyms": ["weed mapping"]}],
        "extra_inclusions": ["Evaluates weed segmentation on UAV multispectral imagery"],
        "title": "Sensor stress review",
        "lead_researcher": "A. Researcher",
    }
    base.update(over)
    return base


# --------------------------------------------------------------------------- finding 1


def test_finding_1_the_proof_answer_writes_no_criterion():
    criteria = steps.run_step("criteria", draft())["criteria"]
    assert "proof" not in {c["source"] for c in criteria}
    assert not any("gold-standard proof" in c["criterion"] for c in criteria)


def test_finding_1_the_proof_answer_still_reaches_the_rationale_and_the_rq_draft():
    d = draft(out_of_scope=["Satellite imagery"], criteria_decisions={})
    d["criteria_decisions"] = {c["id"]: True for c in steps.run_step("criteria", d)["criteria"]}
    out = steps.preview(d, genesis_timestamp=TS)
    assert "Convincing evidence: A table of mIoU per band combination on field data." in out["intent"]["epistemological_rationale"]
    assert steps.run_step("shape", d)["rq_draft"]


def test_without_a_typed_inclusion_the_proof_is_still_the_fallback_inclusion_and_waits_for_accept():
    """Narrowed fix (decision item 1): a draft with no typed inclusion keeps the proof
    criterion as its only inclusion, undecided until the researcher accepts it."""
    rows = [c for c in steps.run_step("criteria", draft(extra_inclusions=[]))["criteria"] if c["source"] == "proof"]
    assert len(rows) == 1 and rows[0]["status"] == "undecided"
    assert steps.run_step("shape", draft(extra_inclusions=[]))["proof_required"] is True


def test_dropping_every_typed_inclusion_brings_the_proof_criterion_back():
    d = draft()
    typed = CriterionDraft("inclusion", d["extra_inclusions"][0], "manual").id
    rows = steps.run_step("criteria", {**d, "criteria_decisions": {typed: False}})["criteria"]
    assert [c["source"] for c in rows if c["kind"] == "inclusion"] == ["proof", "manual"]


# --------------------------------------------------------------------------- finding 2


def test_finding_2_an_out_of_scope_line_of_items_becomes_one_candidate_each():
    answer = "Satellite imagery; Greenhouse-only studies;  Hyperspectral lab spectra ;"
    criteria = steps.run_step("criteria", draft(out_of_scope=[answer]))["criteria"]
    rows = [c for c in criteria if c["source"] == "out_of_scope"]
    assert [c["criterion"] for c in rows] == ["Satellite imagery", "Greenhouse-only studies", "Hyperspectral lab spectra"]


def test_finding_2_no_out_of_scope_candidate_is_accepted_before_the_researcher_accepts_it():
    d = draft(out_of_scope=["Satellite imagery; Greenhouse-only studies"])
    result = steps.run_step("criteria", d)
    rows = [c for c in result["criteria"] if c["source"] == "out_of_scope"]
    assert {c["status"] for c in rows} == {"undecided"}
    assert set(result["undecided"]) >= {c["id"] for c in rows}
    accepted = {**d, "criteria_decisions": {rows[0]["id"]: True}}
    statuses = {c["criterion"]: c["status"] for c in steps.run_step("criteria", accepted)["criteria"] if c["source"] == "out_of_scope"}
    assert statuses == {"Satellite imagery": "accepted", "Greenhouse-only studies": "undecided"}


def test_an_out_of_scope_item_without_semicolons_is_unchanged():
    row = CriterionDraft("exclusion", "Satellite imagery", "out_of_scope", "OUT_OF_SCOPE")
    criteria = steps.run_step("criteria", draft(out_of_scope=["Satellite imagery"]))["criteria"]
    assert [c["id"] for c in criteria if c["source"] == "out_of_scope"] == [row.id]


# --------------------------------------------------------------------------- findings 3 and 23


def test_finding_3_and_23_a_phrase_of_generic_or_colour_words_is_never_proposed():
    for junk in ("blue green red", "red green", "rgb nir", "aerial vehicle uav", "unmanned aerial vehicle uav"):
        assert directions._is_junk_term_label(junk), junk
    for kept in ("weed segmentation", "multispectral imagery", "sugar beet", "uav weed mapping", "red edge band"):
        assert not directions._is_junk_term_label(kept), kept


def _pool(*texts: str) -> dict:
    return {"docs": [{"doi": f"10.1/{i}", "title": t, "abstract": ""} for i, t in enumerate(texts)]}


def test_finding_3_a_typed_direction_is_grounded_when_its_words_occur_together():
    from scholar_harness.recon.session import own_direction_evidence

    pool = _pool(
        "Robustness of weed segmentation under sensor noise",
        "Sensor noise and multispectral weed segmentation",
        "Crop yield estimation",
    )
    phrase = "sensor noise robustness of weed segmentation"
    evidence = own_direction_evidence(pool, phrase)
    assert evidence["match"] == "words" and evidence["observed_in"] == 1
    natural = own_direction_evidence(pool, "weed segmentation under sensor noise")
    assert natural["match"] == "words" and natural["observed_in"] == 2
    exact = own_direction_evidence(pool, "weed segmentation")
    assert exact["match"] == "phrase" and exact["observed_in"] == 2


def test_a_one_word_direction_still_needs_the_word_itself():
    from scholar_harness.recon.session import own_direction_evidence

    pool = _pool("Weed mapping", "Weeds in maize")
    assert own_direction_evidence(pool, "weeds")["observed_in"] == 1


# --------------------------------------------------------------------------- finding 4


def _record(d: dict) -> dict:
    return {"draft": d, "grounding": None}


def test_finding_4_no_start_year_note_before_any_search():
    found, *_ = checks.inception_checks(_record(draft(start_year=None)), pool=None)
    assert "SCOPE_START_YEAR_DEFAULTED" not in {c["check_id"] for c in found}


def test_after_a_search_without_a_start_year_the_note_shows():
    found, *_ = checks.inception_checks(_record(draft(start_year=None)), pool={"docs": [], "providers": ["openalex"]})
    assert "SCOPE_START_YEAR_DEFAULTED" in {c["check_id"] for c in found}
