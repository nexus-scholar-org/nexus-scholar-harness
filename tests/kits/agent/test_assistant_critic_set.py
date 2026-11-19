"""The M10c critic test set, run through the assistant's MCP path with no AI.

``scripts/critic_set.py prepare`` makes one workspace per document of
``tests/fixtures/critic_protocols``; scripted clients then call the real
``nexus_assistant_read_workspace`` and ``nexus_assistant_report_finding``
tools, and ``score`` reads what was stored. This proves the path (every
finding is stored, journaled and listed as an agent row) and the scorer; it
says nothing about how well a real model criticises (not run here).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from scholar_agent import server
from scholar_harness import assistant

REPO = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location("critic_set", REPO / "scripts" / "critic_set.py")
critic_set = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(critic_set)

MODEL = "scripted-client"


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    out = tmp_path_factory.mktemp("critic_set")
    made = critic_set.prepare(out)
    return out, {m["id"]: m["files"] for m in made}


def _report(monkeypatch, out: Path, doc_id: str, **kw) -> dict:
    monkeypatch.setenv("NEXUS_MCP_WORKSPACE", str(out))
    answer = json.loads(server.nexus_assistant_report_finding(workspace_dir=str(out / doc_id), model=MODEL, **kw))
    assert answer["status"] == "SUCCESS", answer
    return answer


def _locator(doc: dict, pointer: str) -> str:
    return critic_set.PROTOCOL_PREFIX + pointer if doc["format"] == "protocol" else pointer


def test_prepare_makes_the_42_documents_as_genesis_would(prepared):
    _out, made = prepared
    assert len(made) == 42
    m = critic_set.manifest()
    formats = {v["id"]: v["format"] for v in m["variants"]}
    for doc_id, files in made.items():
        if formats.get(doc_id) == "protocol":
            assert files == ["protocol.json"]
        elif doc_id == "scoping-no-exclusion-criterion":  # the intent model refuses it (manifest)
            assert files == ["intent.json"]
        else:
            assert files == ["intent.json", "protocol.json"], doc_id


def test_every_document_can_be_read_through_the_tool(prepared, monkeypatch):
    out, made = prepared
    monkeypatch.setenv("NEXUS_MCP_WORKSPACE", str(out))
    for doc_id, files in made.items():
        if "protocol.json" not in files:
            continue
        answer = json.loads(server.nexus_assistant_read_workspace(workspace_dir=str(out / doc_id)))
        assert answer["status"] == "SUCCESS", (doc_id, answer)
        assert answer["protocol"]["search_strategy"]


def test_the_silent_client_locates_nothing(tmp_path):
    critic_set.prepare(tmp_path)
    result = critic_set.score(tmp_path)
    assert result["defects"] == {"located": 0, "defects": 43}
    assert result["base_false_alarms"] == [] and len(result["missed"]) == 43


def test_the_oracle_client_locates_every_defect_through_the_mcp_path(tmp_path, monkeypatch):
    """The manifest's own findings, sent one by one through the real tool, are all located."""
    critic_set.prepare(tmp_path)
    sent = 0
    for doc in critic_set.documents():
        for defect in doc["defects"]:
            answer = _report(monkeypatch, tmp_path, doc["id"], locator=_locator(doc, defect["fields"][0]),
                             severity=defect["severity"], finding=defect["finding"])
            row = answer["finding"]
            assert row["source"] == "agent" and row["check_id"] == assistant.FINDING_CHECK_ID
            assert row["level"] != "blocker" and row["step"] == "plan"
            sent += 1
    assert sent == 43
    result = critic_set.score(tmp_path)
    assert result["defects"] == {"located": 43, "defects": 43}
    assert result["critic_only"] == {"located": 31, "defects": 31}
    assert result["by_severity"] == {"critical": {"located": 4, "defects": 4}, "major": {"located": 30, "defects": 30},
                                     "minor": {"located": 9, "defects": 9}}
    assert result["base_false_alarms"] == [] and result["missed"] == []
    # Each finding is stored once and indexed in the journal.
    for doc in critic_set.documents():
        stored = critic_set.findings(tmp_path / doc["id"])
        assert len(stored) == len(doc["defects"])
        if stored:
            journal = (tmp_path / doc["id"] / "audit" / "journal.jsonl").read_text(encoding="utf-8")
            assert journal.count("ASSISTANT_FINDING_REPORTED") == len(stored)


def test_a_noisy_client_is_scored_with_false_alarms_on_the_bases(tmp_path, monkeypatch):
    critic_set.prepare(tmp_path)
    _report(monkeypatch, tmp_path, "scoping-base", locator="/research_questions/0/text", severity="major",
            finding="RQ1 is too broad.")
    _report(monkeypatch, tmp_path, "sr-base", locator="/core_concepts", severity="minor", finding="A note only.")
    result = critic_set.score(tmp_path)
    assert [a["document"] for a in result["base_false_alarms"]] == ["scoping-base"]
    assert result["base_minor_findings"] == 1


def test_a_finding_in_the_wrong_space_does_not_locate(tmp_path, monkeypatch):
    """A protocol-format variant is located only by a ``protocol:`` pointer, an intent one by a plain pointer."""
    critic_set.prepare(tmp_path)
    doc = next(d for d in critic_set.documents() if d["format"] == "protocol")
    pointer = doc["defects"][0]["fields"][0]
    assert critic_set._pointer(pointer, "protocol") is None
    assert critic_set._pointer(critic_set.PROTOCOL_PREFIX + pointer, "protocol") == pointer
    assert critic_set._pointer(critic_set.PROTOCOL_PREFIX + pointer, "intent") is None


@pytest.mark.parametrize(
    ("pointer", "targets", "expected"),
    [
        ("/inclusion_criteria/1/criterion", ["/inclusion_criteria/1/criterion"], True),
        ("/inclusion_criteria", ["/inclusion_criteria/1/criterion"], True),
        ("/inclusion_criteria/1", ["/inclusion_criteria/10/criterion"], False),
        ("/exclusion_criteria", ["/inclusion_criteria/1/criterion"], False),
        ("", ["/inclusion_criteria/1/criterion"], False),
    ],
)
def test_the_locator_rule(pointer, targets, expected):
    assert critic_set.locates(pointer, targets) is expected
