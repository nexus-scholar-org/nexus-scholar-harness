"""M0: ``scripts/check_golden_workspace.py``, the verdict on the golden run.

A synthetic finished workspace passes; each test then breaks one property and
expects exactly that check to fail: a journal stage missing or out of order,
a decision without HUMAN provenance, a study without a decision, and PRISMA
counts that do not reconcile.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "check_golden_workspace", ROOT / "scripts" / "check_golden_workspace.py"
)
checker = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = checker  # dataclasses resolve their module through sys.modules
_SPEC.loader.exec_module(checker)

STUDIES = ["STU-a", "STU-b", "STU-c"]
RECORDS = {"REC-1": "STU-a", "REC-2": "STU-a", "REC-3": "STU-b", "REC-4": "STU-c"}


def _event(i: int, action: str, **parameters) -> dict:
    return {
        "timestamp": f"2026-11-04T10:00:{i:02d}+00:00",
        "event_id": f"EVT-{i}",
        "action": action,
        "description": action,
        "parameters": parameters,
        "status": "SUCCESS",
    }


def _artifact(ws: Path, artifact_id: str, artifact_type: str, data: dict, accepted_at: str) -> dict:
    path = f"artifacts/{artifact_type}/{artifact_id}.json"
    (ws / path).parent.mkdir(parents=True, exist_ok=True)
    (ws / path).write_text(json.dumps({"artifact_type": artifact_type, "data": data}), encoding="utf-8")
    return {"artifact_type": artifact_type, "path": path, "accepted_at": accepted_at}


def _decision(
    study: str,
    decision: str,
    method: str = "HUMAN",
    screener_id: str = "researcher",
    decided_at: str = "2026-11-04T10:00:03+00:00",
) -> dict:
    return {
        "study_id": study,
        "decision": decision,
        "method": method,
        "screener_id": screener_id,
        "decided_at": decided_at,
    }


def _finished(tmp_path: Path, decisions: list[dict] | None = None, journal: list[dict] | None = None) -> Path:
    ws = tmp_path / "ws"
    (ws / "audit").mkdir(parents=True)
    (ws / "literature").mkdir()
    decisions = decisions or [
        _decision("STU-a", "INCLUDE"),
        _decision("STU-b", "EXCLUDE"),
        _decision("STU-c", "EXCLUDE"),
    ]
    registry = {
        "ART-corpus": _artifact(
            ws,
            "ART-corpus",
            "corpus_snapshot",
            {"studies": [{"study_id": s} for s in STUDIES], "record_to_study": RECORDS},
            "2026-11-04T10:00:02Z",
        ),
        "ART-batch": _artifact(ws, "ART-batch", "screening_batch", {"batch_id": "BAT-1"}, "2026-11-04T10:00:03Z"),
        "ART-dec": _artifact(
            ws,
            "ART-dec",
            "screening_decisions",
            {"batch_id": "BAT-1", "decisions": decisions},
            "2026-11-04T10:00:04Z",
        ),
    }
    (ws / "audit" / "artifact_registry.json").write_text(json.dumps({"artifacts": registry}), encoding="utf-8")
    events = journal or [
        _event(0, "PROJECT_INITIALIZED"),
        _event(1, "PROTOCOL_ADOPTED"),
        _event(2, "ARTIFACT_ACCEPTED", artifact_type="corpus_snapshot"),
        _event(3, "ARTIFACT_ACCEPTED", artifact_type="screening_batch"),
        _event(4, "SCREENING_DECISIONS_RECORDED"),
        _event(5, "SCREENING_GENERATION_PUBLISHED"),
    ]
    (ws / "audit" / "journal.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    # As the collector publishes: Unclear (MAYBE) goes forward with the includes.
    included = [d for d in decisions if d["decision"] in ("INCLUDE", "MAYBE")]
    excluded = [d for d in decisions if d["decision"] == "EXCLUDE"]
    (ws / "literature" / "included.json").write_text(json.dumps(included), encoding="utf-8")
    (ws / "literature" / "excluded.json").write_text(json.dumps(excluded), encoding="utf-8")
    (ws / "literature" / "conflicts.json").write_text("[]", encoding="utf-8")
    prisma = {
        "total_identified": 4,
        "duplicates_removed": 1,
        "records_screened": 3,
        "records_excluded": len(excluded),
        "records_included": sum(1 for d in decisions if d["decision"] == "INCLUDE"),
        "records_unclear": sum(1 for d in decisions if d["decision"] == "MAYBE"),
        "conflicts_flagged": 0,
        "exclusion_reasons_breakdown": {"WRONG_TASK": len(excluded)},
    }
    (ws / "literature" / "prisma_report.json").write_text(json.dumps(prisma), encoding="utf-8")
    return ws


def _by_name(results) -> dict:
    return {r.name: r for r in results}


def test_a_finished_human_run_passes_every_check(tmp_path):
    results = checker.run_checks(_finished(tmp_path))
    assert all(r.ok for r in results), [(r.name, r.problems) for r in results]
    assert set(_by_name(results)) == {"journal", "provenance", "prisma"}


def test_main_exit_codes(tmp_path):
    assert checker.main([str(_finished(tmp_path))]) == 0
    empty = tmp_path / "empty"
    (empty / "audit").mkdir(parents=True)
    (empty / "audit" / "journal.jsonl").write_text("", encoding="utf-8")
    assert checker.main([str(empty)]) == 1


def test_missing_publication_stage_fails_the_journal_check(tmp_path):
    journal = [
        _event(0, "PROJECT_INITIALIZED"),
        _event(1, "PROTOCOL_ADOPTED"),
        _event(2, "ARTIFACT_ACCEPTED", artifact_type="corpus_snapshot"),
        _event(3, "ARTIFACT_ACCEPTED", artifact_type="screening_batch"),
        _event(4, "SCREENING_DECISIONS_RECORDED"),
    ]
    results = _by_name(checker.run_checks(_finished(tmp_path, journal=journal)))
    assert not results["journal"].ok
    assert any("screening published" in p for p in results["journal"].problems)
    assert results["provenance"].ok and results["prisma"].ok


def test_stages_out_of_order_fail_the_journal_check(tmp_path):
    journal = [
        _event(0, "PROJECT_INITIALIZED"),
        _event(1, "PROTOCOL_ADOPTED"),
        _event(2, "ARTIFACT_ACCEPTED", artifact_type="screening_batch"),
        _event(3, "ARTIFACT_ACCEPTED", artifact_type="corpus_snapshot"),
        _event(4, "SCREENING_DECISIONS_RECORDED"),
        _event(5, "SCREENING_GENERATION_PUBLISHED"),
    ]
    results = _by_name(checker.run_checks(_finished(tmp_path, journal=journal)))
    assert not results["journal"].ok
    assert any("batches prepared" in p for p in results["journal"].problems)


def test_a_malformed_journal_line_fails_the_journal_check(tmp_path):
    ws = _finished(tmp_path)
    with (ws / "audit" / "journal.jsonl").open("a", encoding="utf-8") as fh:
        fh.write("{not json\n")
    results = _by_name(checker.run_checks(ws))
    assert not results["journal"].ok
    assert any("line 7" in p for p in results["journal"].problems)


@pytest.mark.parametrize("method", ["LLM", "COMPOSED"])
def test_a_non_human_decision_fails_provenance(tmp_path, method):
    decisions = [
        _decision("STU-a", "INCLUDE"),
        _decision("STU-b", "EXCLUDE", method=method),
        _decision("STU-c", "EXCLUDE"),
    ]
    results = _by_name(checker.run_checks(_finished(tmp_path, decisions=decisions)))
    assert not results["provenance"].ok
    assert any("STU-b" in p and method in p for p in results["provenance"].problems)


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("screener_id", "researcher-draft", "placeholder screener"),
        ("screener_id", "", "placeholder screener"),
        ("decided_at", "1970-01-01T00:00:00+00:00", "placeholder decided_at"),
        ("decided_at", "", "placeholder decided_at"),
    ],
)
def test_placeholder_provenance_fails_even_when_human(tmp_path, field, value, reason):
    """DEVELOPER_COMPASS §6: HUMAN alone is not provenance (the CON-11 pattern)."""
    decisions = [
        _decision("STU-a", "INCLUDE"),
        _decision("STU-b", "EXCLUDE", **{field: value}),
        _decision("STU-c", "EXCLUDE"),
    ]
    results = _by_name(checker.run_checks(_finished(tmp_path, decisions=decisions)))
    assert not results["provenance"].ok
    assert any("STU-b" in p and reason in p for p in results["provenance"].problems)


def test_a_study_without_a_decision_fails_provenance(tmp_path):
    decisions = [_decision("STU-a", "INCLUDE"), _decision("STU-b", "EXCLUDE")]
    ws = _finished(tmp_path, decisions=decisions)
    results = _by_name(checker.run_checks(ws))
    assert not results["provenance"].ok
    assert any("STU-c" in p for p in results["provenance"].problems)


def test_prisma_counts_that_do_not_reconcile_fail(tmp_path):
    ws = _finished(tmp_path)
    path = ws / "literature" / "prisma_report.json"
    prisma = json.loads(path.read_text(encoding="utf-8"))
    prisma["records_included"] = 2
    path.write_text(json.dumps(prisma), encoding="utf-8")
    results = _by_name(checker.run_checks(ws))
    assert not results["prisma"].ok
    assert any("records_included" in p for p in results["prisma"].problems)


def test_prisma_identified_must_match_the_corpus(tmp_path):
    ws = _finished(tmp_path)
    path = ws / "literature" / "prisma_report.json"
    prisma = json.loads(path.read_text(encoding="utf-8"))
    prisma["total_identified"] = 99
    path.write_text(json.dumps(prisma), encoding="utf-8")
    results = _by_name(checker.run_checks(ws))
    assert not results["prisma"].ok
    assert any("total_identified" in p for p in results["prisma"].problems)


def test_the_unscreened_golden_workspace_reports_what_is_missing():
    results = _by_name(checker.run_checks(ROOT / "workspaces" / "golden-uav-30"))
    assert not results["journal"].ok
    assert any("batches prepared" in p for p in results["journal"].problems)
    assert not results["prisma"].ok


def test_unclear_is_forwarded_with_the_includes(tmp_path):
    """Decision 2026-11-04: MAYBE counts apart but is published in included.json."""
    decisions = [
        _decision("STU-a", "INCLUDE"),
        _decision("STU-b", "MAYBE"),
        _decision("STU-c", "EXCLUDE"),
    ]
    results = _by_name(checker.run_checks(_finished(tmp_path, decisions=decisions)))
    assert results["prisma"].ok, results["prisma"].problems


def test_conflicts_are_a_subset_not_an_extra_bucket(tmp_path):
    """The collector flags borderline rows as conflicts and still partitions them."""
    ws = _finished(tmp_path)
    literature = ws / "literature"
    flagged = json.loads((literature / "excluded.json").read_text(encoding="utf-8"))[:1]
    (literature / "conflicts.json").write_text(json.dumps(flagged), encoding="utf-8")
    prisma = json.loads((literature / "prisma_report.json").read_text(encoding="utf-8"))
    prisma["conflicts_flagged"] = 1
    (literature / "prisma_report.json").write_text(json.dumps(prisma), encoding="utf-8")
    results = _by_name(checker.run_checks(ws))
    assert results["prisma"].ok, results["prisma"].problems


def test_a_record_can_carry_several_exclusion_reasons(tmp_path):
    ws = _finished(tmp_path)
    path = ws / "literature" / "prisma_report.json"
    prisma = json.loads(path.read_text(encoding="utf-8"))
    prisma["exclusion_reasons_breakdown"] = {"WRONG_TASK": 2, "WRONG_PLATFORM": 1}
    path.write_text(json.dumps(prisma), encoding="utf-8")
    assert _by_name(checker.run_checks(ws))["prisma"].ok
    prisma["exclusion_reasons_breakdown"] = {"WRONG_TASK": 1}
    path.write_text(json.dumps(prisma), encoding="utf-8")
    results = _by_name(checker.run_checks(ws))
    assert not results["prisma"].ok
    assert any("exclusion reasons" in p for p in results["prisma"].problems)
