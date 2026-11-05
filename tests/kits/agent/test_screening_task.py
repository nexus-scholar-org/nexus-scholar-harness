"""The screening task (M1b-2): its prompt, schema and mapping to the engine's proposal shape."""

from __future__ import annotations

from scholar_agent.tasks import screening as task_mod
from scholar_harness.screening import proposals as pr

PROTOCOL = {
    "screening_criteria": {
        "inclusion": [{"id": "INC-01", "description": "Uses UAV imagery"}],
        "exclusion": [{"id": "EXC-01", "description": "Not an agricultural field"}],
    }
}
TITLE = "Drone mapping of weeds"
ABSTRACT = "We map weeds in maize fields from UAV imagery."


def test_task_loads_with_a_stable_prompt_hash():
    task = task_mod.load_task()
    assert task.task_version == "screen-v1" and task.defaults["model"] == "claude-opus-5-5"
    assert task.prompt_sha256.startswith("sha256:") and task.prompt_sha256 == task_mod.load_task().prompt_sha256
    prices = task_mod.load_prices()
    assert prices["as_of"] and prices["anthropic"]["claude-opus-5-5"]["input"] > 0


def test_system_prompt_lists_every_criterion_and_holds_no_record():
    task = task_mod.load_task()
    prompt = task_mod.system_prompt(task, task_mod.criteria_from_protocol(PROTOCOL))
    assert "`INC-01` (inclusion): Uses UAV imagery" in prompt and "`EXC-01` (exclusion)" in prompt
    assert "{criteria}" not in prompt and TITLE not in prompt
    assert task_mod.record_message(TITLE, ABSTRACT).startswith("<record>")


def test_schema_pins_ids_and_answers():
    schema = task_mod.output_schema(["INC-01", "EXC-01"])
    item = schema["properties"]["criteria"]["items"]["properties"]
    assert item["id"]["enum"] == ["INC-01", "EXC-01"] and item["answer"]["enum"] == ["yes", "no", "not_reported"]
    assert schema["additionalProperties"] is False


def _engine(output):
    criteria = pr.Criteria.from_protocol(PROTOCOL)
    checks = pr.validate_output(output, criteria, pr.record_text(TITLE, ABSTRACT))
    return pr.derive_outcome(output, criteria, checks), checks


def test_located_quotes_pass_the_engine_checks_and_the_rule_table_decides():
    raw = {
        "criteria": [
            {"id": "INC-01", "answer": "yes", "quote": "from UAV imagery"},
            {"id": "EXC-01", "answer": "no", "quote": "maize fields"},
        ],
        "cannot_decide": False,
        "reasoning": "UAV imagery of maize fields.",
    }
    out = task_mod.to_proposal_output(raw, TITLE, ABSTRACT)
    (outcome, reason), checks = _engine(out)
    assert all(c["ok"] for c in checks) and (outcome, reason) == ("INCLUDE", None)


def test_a_quote_not_in_the_record_makes_it_unclear_never_exclude():
    raw = {
        "criteria": [
            {"id": "INC-01", "answer": "no", "quote": "satellite data only"},  # not in the record
            {"id": "EXC-01", "answer": "no", "quote": "maize fields"},
        ],
        "cannot_decide": False,
        "reasoning": "x",
    }
    (outcome, _), checks = _engine(task_mod.to_proposal_output(raw, TITLE, ABSTRACT))
    assert outcome == "MAYBE"
    assert not next(c for c in checks if c["name"] == "quote_in_source")["ok"]


def test_a_non_object_answer_passes_through_and_fails_the_schema():
    for raw in (None, "not json", {"criteria": "x"}):
        (outcome, _), checks = _engine(task_mod.to_proposal_output(raw, TITLE, ABSTRACT))
        assert outcome == "MAYBE" and not all(c["ok"] for c in checks)


def test_without_a_year_the_record_text_and_its_hash_are_unchanged():
    """Decision 2026-11-05: the Published line is added only when a year is known."""
    assert pr.record_text(TITLE, ABSTRACT) == f"{TITLE}\n\n{ABSTRACT}"
    assert pr.input_sha256(TITLE, ABSTRACT) == pr.input_sha256(TITLE, ABSTRACT, None)
    assert pr.input_sha256(TITLE, ABSTRACT, "2024") != pr.input_sha256(TITLE, ABSTRACT)
    assert pr.record_text(TITLE, ABSTRACT, "2024").endswith("\n\nPublished: 2024")


def test_a_year_quoted_from_the_published_line_validates_a_date_criterion():
    protocol = {
        "screening_criteria": {
            "inclusion": [{"id": "INC-03", "criterion": "Published from 2020"}],
            "exclusion": [{"id": "EXC-04", "criterion": "Published before 2020"}],
        }
    }
    raw = {
        "criteria": [
            {"id": "INC-03", "answer": "yes", "quote": "Published: 2024"},
            {"id": "EXC-04", "answer": "no", "quote": "Published: 2024"},
        ],
        "cannot_decide": False,
        "reasoning": "2024 is inside the window.",
    }
    out = task_mod.to_proposal_output(raw, TITLE, ABSTRACT, "2024")
    criteria = pr.Criteria.from_protocol(protocol)
    checks = pr.validate_output(out, criteria, pr.record_text(TITLE, ABSTRACT, "2024"))
    assert all(c["ok"] for c in checks)
    assert pr.derive_outcome(out, criteria, checks) == ("INCLUDE", None)
    assert "Published: 2024" in task_mod.record_message(TITLE, ABSTRACT, "2024")
    # The protocol's `criterion` key is read for the prompt text.
    assert task_mod.criteria_from_protocol(protocol)[0].text == "Published from 2020"
