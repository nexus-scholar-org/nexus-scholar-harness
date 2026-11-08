"""M7-method M5: the rule table follows the protocol's not-reported policy.

Decision 2026-11-08. ``unclear`` is today's table, cell for cell. ``exclude``
turns an *inclusion* criterion answered "not reported" into EXCLUDE with
``FAILS-INC-n``; an *exclusion* criterion that is not reported never fails.
Failed checks and ``cannot_decide`` stay Unclear under both policies: the
policy is about what the abstract does not say, not about a broken draft.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scholar_harness.screening import proposals as pr

CRITERIA = pr.Criteria(inclusion=("INC-01", "INC-02"), exclusion=("EXC-01",))
OK = [{"name": "schema", "ok": True}]


def _out(inc1: str, inc2: str, exc1: str, *, cannot_decide: bool = False) -> dict:
    return {
        "criteria": [
            {"id": "INC-01", "answer": inc1},
            {"id": "INC-02", "answer": inc2},
            {"id": "EXC-01", "answer": exc1},
        ],
        "cannot_decide": cannot_decide,
    }


# (INC-01, INC-02, EXC-01) -> (unclear-policy result, exclude-policy result)
CELLS = [
    (("yes", "yes", "no"), ("INCLUDE", None), ("INCLUDE", None)),
    (("yes", "yes", "yes"), ("EXCLUDE", "EXC-01"), ("EXCLUDE", "EXC-01")),
    (("no", "yes", "no"), ("EXCLUDE", "FAILS-INC-01"), ("EXCLUDE", "FAILS-INC-01")),
    (("yes", "no", "no"), ("EXCLUDE", "FAILS-INC-02"), ("EXCLUDE", "FAILS-INC-02")),
    # Not reported: the cells the policy changes.
    (("not_reported", "yes", "no"), ("MAYBE", None), ("EXCLUDE", "FAILS-INC-01")),
    (("yes", "not_reported", "no"), ("MAYBE", None), ("EXCLUDE", "FAILS-INC-02")),
    (("yes", "yes", "not_reported"), ("MAYBE", None), ("INCLUDE", None)),
    (("not_reported", "yes", "not_reported"), ("MAYBE", None), ("EXCLUDE", "FAILS-INC-01")),
    # A definite failure outranks a not-reported answer under both policies.
    (("not_reported", "yes", "yes"), ("MAYBE", None), ("EXCLUDE", "EXC-01")),
    (("not_reported", "no", "no"), ("MAYBE", None), ("EXCLUDE", "FAILS-INC-02")),
]


@pytest.mark.parametrize(("answers", "unclear", "exclude"), CELLS)
def test_every_cell_of_both_tables(answers, unclear, exclude) -> None:
    output = _out(*answers)
    assert pr.derive_outcome(output, CRITERIA, OK) == unclear  # default is today's table
    assert pr.derive_outcome(output, CRITERIA, OK, not_reported="unclear") == unclear
    assert pr.derive_outcome(output, CRITERIA, OK, not_reported="exclude") == exclude


@pytest.mark.parametrize("policy", ["unclear", "exclude"])
def test_a_broken_draft_stays_unclear_under_both_policies(policy) -> None:
    failed = [{"name": "schema", "ok": False}]
    assert pr.derive_outcome(_out("not_reported", "yes", "no"), CRITERIA, failed, not_reported=policy) == ("MAYBE", None)
    cannot = _out("not_reported", "yes", "no", cannot_decide=True)
    assert pr.derive_outcome(cannot, CRITERIA, OK, not_reported=policy) == ("MAYBE", None)


def test_an_unknown_policy_is_refused() -> None:
    with pytest.raises(ValueError):
        pr.derive_outcome(_out("yes", "yes", "no"), CRITERIA, OK, not_reported="include")


def test_submit_proposal_applies_the_protocols_policy(tmp_path: Path) -> None:
    """The stored draft's outcome follows the protocol it was screened under."""
    protocol = {
        "screening_criteria": {
            "inclusion": [{"id": "INC-01", "description": "UAV"}],
            "exclusion": [{"id": "EXC-01", "description": "review"}],
        },
        "method": {
            "dedup": {"doi": True, "title_similarity": 0.97, "first_author": True, "year_tolerance": 1},
            "rules_version": "screening-rules-v1",
            "not_reported": "exclude",
            "blinding": "reveal_after_decision",
        },
    }
    (tmp_path / "audit").mkdir()
    (tmp_path / "audit" / "journal.jsonl").touch()
    text = pr.record_text("A title", "An abstract.")
    quote = {"text": "An abstract", "start": text.index("An abstract"), "end": text.index("An abstract") + len("An abstract")}
    output = {
        "criteria": [{"id": "INC-01", "answer": "not_reported"}, {"id": "EXC-01", "answer": "no", "evidence": quote}],
        "cannot_decide": False,
    }
    record = pr.submit_proposal(
        tmp_path, study_id="SCI-000001", title="A title", abstract="An abstract.", output=output,
        protocol=protocol, protocol_fingerprint="sha256:" + "1" * 64,
        provenance={"task_version": "screen-v1", "model": "m", "prompt_sha256": "sha256:" + "0" * 64, "driver": "mcp"},
        created_at="2026-11-08T10:00:00Z",
    )
    assert (record["derived_outcome"], record["reason_code"]) == ("EXCLUDE", "FAILS-INC-01")
    assert record["rules_version"] == "screening-rules-v1"
    stored = [json.loads(line) for line in (tmp_path / pr.PROPOSALS_FILE).read_text(encoding="utf-8").splitlines()]
    assert stored[-1]["derived_outcome"] == "EXCLUDE"
