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
