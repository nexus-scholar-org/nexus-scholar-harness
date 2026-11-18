"""The planned number of records to screen (M10b, R3; ``04-shape``).

Before M10b no screen asked it, so the protocol always carried the playbook's
preset (strict run 2026-11-13: a harvest of 1,074 records against a preset
nobody chose). The draft's two numbers now reach ``target_candidate_pool_size``
through the intent's existing fields; empty keeps the preset.
"""

from __future__ import annotations

import pytest
from test_steps_proof_optional import ready_draft

from scholar_harness.inception import steps


def _compiled(draft: dict) -> tuple[dict, dict]:
    out = steps.preview(draft, genesis_timestamp="2026-11-18T09:00:00+00:00")
    return out["intent"], out["protocol"]["search_strategy"]["target_candidate_pool_size"]


def test_a_stated_range_reaches_the_protocol_and_the_intent():
    intent, pool = _compiled({**ready_draft(), "pool_min": 150, "pool_max": 300})
    assert (intent["pool_min"], intent["pool_max"]) == (150, 300)
    assert pool == {"min": 150, "max": 300}


def test_an_empty_pair_keeps_the_playbook_preset_and_records_null():
    intent, pool = _compiled(ready_draft())
    assert intent["pool_min"] is None and intent["pool_max"] is None
    assert pool == steps.pool_preset(ready_draft()["playbook"])


def test_up_to_alone_starts_from_zero_so_the_preset_minimum_cannot_exceed_it():
    # SCOPING_REVIEW's preset minimum is 200; "up to 150" alone must not compile to 200..150.
    intent, pool = _compiled({**ready_draft(), "playbook": "SCOPING_REVIEW", "pool_max": 150})
    assert intent["pool_min"] == 0
    assert pool == {"min": 0, "max": 150}


@pytest.mark.parametrize(
    "pair",
    [
        {"pool_min": 300, "pool_max": 150},
        {"pool_min": -1, "pool_max": 150},
        {"pool_max": 0},
        {"pool_max": 1_000_001},
        {"pool_min": 50},
    ],
)
def test_an_impossible_range_is_draft_invalid(pair):
    with pytest.raises(steps.StepRefused) as exc:
        steps.parse_draft({**ready_draft(), **pair})
    assert exc.value.code == "DRAFT_INVALID"


def test_shape_answers_the_chosen_playbooks_preset():
    out = steps.run_step("shape", {"topic": "weeds", "paradigm": "Positivist", "playbook": "SCOPING_REVIEW"})
    assert out["pool_preset"] == {"min": 200, "max": 1000}
    # No playbook chosen yet: the recommended one's preset.
    out = steps.run_step("shape", {"topic": "weeds", "paradigm": "Positivist"})
    assert out["pool_preset"] == steps.pool_preset(out["recommended_playbook"])
