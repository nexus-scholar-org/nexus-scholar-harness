"""AGT-16/19 and the MCP proposal tools (agent-system §2, M1a).

MCP screening writes proposals only and journals inside a workspace; the
queue and record tools never reveal an agent outcome; `nexus_submit_proposal`
reaches the proposal store and never a decision file.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scholar_agent import server
from scholar_harness.contracts import AcceptanceContext, accept_artifact
from scholar_harness.screening.batcher import cmd_prepare
from scholar_protocol.canonical import canonical_fingerprint
from scholar_protocol.models import ResearchProtocol
from scholar_search.identity import build_corpus_snapshot_artifact
from scholar_search.models import Author, Document, ExternalIds

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "tests" / "kits" / "protocol" / "fixtures" / "canonical" / "identity_base.json"
WS_ID = "WSP-" + "e" * 32


@pytest.fixture
def ws(tmp_path, monkeypatch) -> Path:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    monkeypatch.setenv("NEXUS_MCP_WORKSPACE", str(workspace))
    (workspace / "project.json").write_text(
        json.dumps({"project_id": "mcp", "registered_workspace_id": WS_ID}), encoding="utf-8"
    )
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    (workspace / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    (workspace / "audit").mkdir()
    (workspace / "audit" / "journal.jsonl").touch()
    fingerprint = canonical_fingerprint(ResearchProtocol.model_validate(protocol))
    docs = [
        Document(
            title=f"MCP record {i}",
            year=2026,
            provider="crossref",
            provider_id=f"mcp-{i}",
            external_ids=ExternalIds(doi=f"10.1000/mcp-{i}"),
            abstract=f"UAV weed mapping study number {i}.",
            authors=[Author("Reviewer")],
            workspace_id=f"SCI-00000{i}",
        )
        for i in range(2)
    ]
    corpus = build_corpus_snapshot_artifact(
        docs,
        workspace_id=WS_ID,
        run_id="RUN-mcp",
        protocol_fingerprint=fingerprint,
        created_at=datetime(2026, 11, 4, tzinfo=UTC),
        commit="4" * 40,
    ).artifact
    assert accept_artifact(
        workspace,
        corpus,
        expected=AcceptanceContext(
            workspace_id=WS_ID, protocol_fingerprint=fingerprint, corpus_fingerprint=corpus["corpus_fingerprint"]
        ),
    ).accepted
    (workspace / "literature").mkdir()
    (workspace / "literature" / "verified.json").write_text(
        json.dumps([{"workspace_id": d.workspace_id, "title": d.title, "abstract": d.abstract} for d in docs]),
        encoding="utf-8",
    )
    cmd_prepare(workspace, batch_size=20)
    return workspace


def _journal(ws: Path) -> list[dict]:
    return [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def test_agt16_19_mcp_screening_writes_proposals_only_and_journals(ws):
    candidates = ws / "candidates.json"
    candidates.write_text(json.dumps([{"title": "A UAV weed paper", "abstract": "Drone weed mapping.", "workspace_id": "SCI-9"}]), encoding="utf-8")
    result = server.nexus_screen(str(candidates), str(ws / "protocol.json"), str(ws / "literature" / "mcp"))
    assert "Proposals only" in result
    out = ws / "literature" / "mcp"
    assert (out / "screening_proposals.json").is_file()
    assert not (out / "included.json").exists()
    assert not (ws / "literature" / "included.json").exists()
    rows = [r for r in _journal(ws) if r["action"] == "MCP_SCREENING_PROPOSED"]
    assert len(rows) == 1 and rows[0]["outputs"] == ["literature/mcp/screening_proposals.json"]


def test_queue_and_record_never_reveal_an_agent_outcome(ws):
    queue = json.loads(server.nexus_screening_queue())
    assert queue["status"] == "SUCCESS" and len(queue["items"]) == 2
    study = queue["items"][0]["study_id"]
    record = json.loads(server.nexus_screening_record(study))
    assert record["abstract"].startswith("UAV weed mapping")
    assert {c["kind"] for c in record["criteria"]} == {"inclusion", "exclusion"}
    assert "derived_outcome" not in json.dumps(queue) + json.dumps(record)


def test_submit_proposal_stores_a_draft_and_never_a_decision(ws):
    study = json.loads(server.nexus_screening_queue())["items"][0]["study_id"]
    record = json.loads(server.nexus_screening_record(study))
    text = f"{record['title']}\n\n{record['abstract']}"
    quote = "UAV weed mapping"
    start = text.index(quote)
    answers = [
        {"id": c["id"], "answer": "yes" if c["kind"] == "inclusion" else "no",
         "evidence": {"text": quote, "start": start, "end": start + len(quote)}}
        for c in record["criteria"]
    ]
    result = json.loads(server.nexus_submit_proposal(study, json.dumps({"criteria": answers, "cannot_decide": False}), model="claude-opus-5-5"))
    assert result["status"] == "SUCCESS"
    assert result["derived_outcome"] == "INCLUDE"
    assert all(v["ok"] for v in result["validators"])
    assert not list((ws / "literature" / "screening").glob("batch_*_decisions.json"))
    assert any(r["action"] == "SCREENING_PROPOSAL_SUBMITTED" for r in _journal(ws))
    queue = json.loads(server.nexus_screening_queue(view="no_proposal"))
    assert study not in {i["study_id"] for i in queue["items"]}


def test_a_malformed_proposal_is_recorded_as_unclear(ws):
    study = json.loads(server.nexus_screening_queue())["items"][0]["study_id"]
    result = json.loads(server.nexus_submit_proposal(study, "not json at all", model="claude-opus-5-5"))
    assert result["derived_outcome"] == "MAYBE"
    assert not all(v["ok"] for v in result["validators"])


def test_unknown_study_is_refused(ws):
    result = json.loads(server.nexus_submit_proposal("STU-" + "0" * 32, "{}", model="m"))
    assert result == {"status": "ERROR", "error": "UNKNOWN_STUDY"}


def test_agt19_a_writer_tool_journals_inside_a_workspace(ws):
    raw = ws / "raw.json"
    raw.write_text("[]", encoding="utf-8")
    assert "Successfully deduplicated" in server.nexus_dedup(str(raw), str(ws / "deduped.json"))
    rows = [r for r in _journal(ws) if r["action"] == "MCP_DEDUP"]
    assert len(rows) == 1 and rows[0]["parameters"]["tool"] == "nexus_dedup"


def test_agt19_a_failed_call_writes_no_journal_row(ws):
    assert server.nexus_dedup("missing.json", "out.json").startswith("Error")
    assert not [r for r in _journal(ws) if r["action"] == "MCP_DEDUP"]


def test_agt19_outside_a_research_workspace_nothing_is_journaled(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_MCP_WORKSPACE", str(tmp_path))
    raw = tmp_path / "raw.json"
    raw.write_text("[]", encoding="utf-8")
    assert "Successfully deduplicated" in server.nexus_dedup(str(raw), str(tmp_path / "out.json"))
    assert not (tmp_path / "audit").exists()
