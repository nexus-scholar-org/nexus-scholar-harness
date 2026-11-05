"""Agent proposals: plain-code checks and the outcome rule table (agent-system §3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scholar_harness.screening import proposals as pr

PROTOCOL = {
    "screening_criteria": {
        "inclusion": [{"id": "INC-01"}, {"id": "INC-02"}],
        "exclusion": [{"id": "EXC-01"}],
    }
}
TITLE = "UAV weed mapping in maize"
ABSTRACT = "We map weeds from drone imagery in maize fields."
TEXT = pr.record_text(TITLE, ABSTRACT)
CRITERIA = pr.Criteria.from_protocol(PROTOCOL)


def _quote(fragment: str) -> dict:
    start = TEXT.index(fragment)
    return {"text": fragment, "start": start, "end": start + len(fragment)}


def _output(inc1="yes", inc2="yes", exc1="no", cannot=False, **evidence) -> dict:
    def answer(cid, value):
        item = {"id": cid, "answer": value}
        if value != "not_reported":
            item["evidence"] = evidence.get(cid, _quote("drone imagery"))
        return item

    return {
        "criteria": [answer("INC-01", inc1), answer("INC-02", inc2), answer("EXC-01", exc1)],
        "cannot_decide": cannot,
    }


def _derive(output):
    checks = pr.validate_output(output, CRITERIA, TEXT)
    return pr.derive_outcome(output, CRITERIA, checks), checks


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        (_output(), ("INCLUDE", None)),
        (_output(exc1="yes"), ("EXCLUDE", "EXC-01")),
        (_output(inc2="no"), ("EXCLUDE", "FAILS-INC-02")),
        (_output(inc1="not_reported"), ("MAYBE", None)),
        (_output(cannot=True), ("MAYBE", None)),
    ],
    ids=["include", "exclusion-yes", "inclusion-no", "not-reported", "cannot-decide"],
)
def test_the_rule_table_derives_the_outcome(output, expected):
    (outcome, checks) = _derive(output)
    assert outcome == expected
    assert all(c["ok"] for c in checks)


def test_a_quote_not_in_the_record_makes_it_unclear_never_exclude():
    output = _output(exc1="yes", **{"EXC-01": {"text": "invented passage", "start": 0, "end": 16}})
    (outcome, checks) = _derive(output)
    assert outcome == ("MAYBE", None)
    assert not next(c for c in checks if c["name"] == "quote_in_source")["ok"]


@pytest.mark.parametrize(
    "output",
    [
        {"criteria": [{"id": "INC-01", "answer": "yes"}]},
        {"criteria": [{"id": "INC-01", "answer": "maybe"}]},
        "not an object",
        {"criteria": "yes"},
    ],
    ids=["missing-criteria", "bad-answer", "not-object", "bad-shape"],
)
def test_malformed_output_is_unclear(output):
    checks = pr.validate_output(output, CRITERIA, TEXT)
    assert not all(c["ok"] for c in checks)
    assert pr.derive_outcome(output, CRITERIA, checks) == ("MAYBE", None)


def test_submit_stores_provenance_and_journals(tmp_path: Path):
    ws = tmp_path / "ws"
    (ws / "audit").mkdir(parents=True)
    (ws / "audit" / "journal.jsonl").touch()
    record = pr.submit_proposal(
        ws,
        study_id="STU-a",
        title=TITLE,
        abstract=ABSTRACT,
        output=_output(),
        protocol=PROTOCOL,
        protocol_fingerprint="sha256:" + "1" * 64,
        provenance={"task_id": "screen", "task_version": "screen-v1", "driver": "mcp", "model": "claude-opus-5-5"},
        created_at="2026-11-04T12:00:00Z",
    )
    assert record["derived_outcome"] == "INCLUDE"
    assert record["proposal_id"] == pr.proposal_id(
        "screen-v1", pr.input_sha256(TITLE, ABSTRACT), "sha256:" + "1" * 64, "claude-opus-5-5"
    )
    assert pr.latest_proposal(ws, "STU-a")["proposal_id"] == record["proposal_id"]
    rows = [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["action"] for r in rows] == ["SCREENING_PROPOSAL_SUBMITTED"]
    # A proposal never reaches a decision file.
    assert not list((ws).rglob("batch_*_decisions.json"))


def test_review_5_an_answer_without_an_id_is_unclear_not_a_crash():
    output = {"criteria": [{"answer": "yes"}, {"id": "INC-02", "answer": "yes"}], "cannot_decide": False}
    checks = pr.validate_output(output, CRITERIA, TEXT)
    assert pr.derive_outcome(output, CRITERIA, checks) == ("MAYBE", None)
