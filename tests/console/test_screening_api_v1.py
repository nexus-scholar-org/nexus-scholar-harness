"""Screening API, M1a routes (contract §4; required tests 4, 6, 7).

A synthetic workspace (accepted corpus, one prepared batch of three studies)
is driven only through HTTP: decisions enter as events, the projection
follows, and the reads, the proposal blinding, the PRISMA preview and the
phone token scope are checked against the contract.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scholar_harness.console import create_app
from scholar_harness.contracts import AcceptanceContext, accept_artifact
from scholar_harness.screening import proposals as pr
from scholar_harness.screening.batcher import cmd_prepare
from scholar_protocol.canonical import canonical_fingerprint
from scholar_protocol.models import ResearchProtocol
from scholar_search.identity import build_corpus_snapshot_artifact
from scholar_search.models import Author, Document, ExternalIds

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "tests" / "kits" / "protocol" / "fixtures" / "canonical" / "identity_base.json"
WS_ID = "WSP-" + "d" * 32
BASE = "/api/v1/screening"
DESKTOP, PHONE = "desktop-token", "phone-token"


def _workspace(root: Path, *, prepare: bool = True) -> Path:
    ws = root / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"project_id": "api", "registered_workspace_id": WS_ID}), encoding="utf-8"
    )
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    (ws / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    (ws / "audit").mkdir()
    (ws / "audit" / "journal.jsonl").touch()
    if not prepare:
        return ws
    fingerprint = canonical_fingerprint(ResearchProtocol.model_validate(protocol))
    docs = [
        Document(
            title=f"API record {i}",
            year=2026,
            provider="crossref",
            provider_id=f"api-{i}",
            external_ids=ExternalIds(doi=f"10.1000/api-{i}"),
            abstract=None if i == 2 else f"Abstract {i} about UAV weed mapping.",
            authors=[Author("Reviewer")],
            workspace_id=f"SCI-00000{i}",
        )
        for i in range(3)
    ]
    corpus = build_corpus_snapshot_artifact(
        docs,
        workspace_id=WS_ID,
        run_id="RUN-api",
        protocol_fingerprint=fingerprint,
        created_at=datetime(2026, 11, 4, tzinfo=UTC),
        commit="3" * 40,
    ).artifact
    assert accept_artifact(
        ws,
        corpus,
        expected=AcceptanceContext(
            workspace_id=WS_ID, protocol_fingerprint=fingerprint, corpus_fingerprint=corpus["corpus_fingerprint"]
        ),
    ).accepted
    (ws / "literature").mkdir()
    # prepare finds abstracts through each study's SCI- aliases.
    (ws / "literature" / "verified.json").write_text(
        json.dumps([{"workspace_id": d.workspace_id, "title": d.title, "abstract": d.abstract} for d in docs]),
        encoding="utf-8",
    )
    cmd_prepare(ws, batch_size=20)
    return ws


@pytest.fixture
def ws(tmp_path) -> Path:
    return _workspace(tmp_path)


@pytest.fixture
def client(ws) -> TestClient:
    return TestClient(
        create_app(ws, token=DESKTOP, phone_tokens={PHONE}),
        base_url="http://127.0.0.1",
        headers={"Authorization": f"Bearer {DESKTOP}"},
    )


def _studies(client: TestClient) -> list[str]:
    items = client.get(f"{BASE}/queue", params={"view": "needs_you", "limit": 50}).json()["items"]
    return [i["study_id"] for i in items]


def _event(client: TestClient, study: str, outcome: str = "INCLUDE", **overrides) -> dict:
    binding = client.get(f"{BASE}/records/{study}").json()["binding"]
    event = {
        "event_id": str(uuid.uuid4()),
        "study_id": study,
        "screener_id": "researcher:local",
        "method": "HUMAN",
        "outcome": outcome,
        "reason_code": "EXC-01" if outcome == "EXCLUDE" else None,
        "note": None,
        "criteria": [],
        "decided_at": "2026-11-04T10:00:00.000Z",
        "device": "desktop",
        "supersedes": None,
        "proposal_shown": None,
        "binding": binding,
    }
    event.update(overrides)
    return event


def _post(client: TestClient, events: list[dict], **kw) -> list[dict]:
    response = client.post(f"{BASE}/decisions/events", json={"events": events}, **kw)
    assert response.status_code == 200, response.text
    return response.json()["results"]


def test_summary_and_queue_views(client):
    summary = client.get(f"{BASE}/summary").json()
    assert summary["total"] == 3 and summary["decided"] == 0 and summary["needs_you"] == 3
    assert summary["lanes"]["second_screener"] == "PARKED"
    title_only = client.get(f"{BASE}/queue", params={"view": "title_only"}).json()["items"]
    assert len(title_only) == 1 and title_only[0]["flags"] == ["title_only"]
    studies = _studies(client)
    assert _post(client, [_event(client, studies[0])])[0]["result"] == "accepted"
    assert len(_studies(client)) == 2
    decided = client.get(f"{BASE}/queue", params={"view": "decided"}).json()["items"]
    assert [i["study_id"] for i in decided] == [studies[0]]


def test_queue_pages_with_a_cursor(client):
    first = client.get(f"{BASE}/queue", params={"limit": 2}).json()
    assert len(first["items"]) == 2 and first["next_cursor"] == 2
    rest = client.get(f"{BASE}/queue", params={"limit": 2, "cursor": 2}).json()
    assert len(rest["items"]) == 1 and rest["next_cursor"] is None


def test_record_detail_carries_binding_criteria_and_history(client):
    study = _studies(client)[0]
    detail = client.get(f"{BASE}/records/{study}").json()
    assert detail["binding"]["batch_id"].startswith("batch-")
    assert {c["kind"] for c in detail["criteria"]} == {"inclusion", "exclusion"}
    assert detail["my_decision"] is None and detail["history"] == []
    assert client.get(f"{BASE}/records/STU-{'0' * 32}").json()["detail"]["code"] == "UNKNOWN_STUDY"


def test_required_4_proposal_hidden_until_decided(client, ws):
    study = _studies(client)[0]
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    pr.submit_proposal(
        ws,
        study_id=study,
        title="t",
        abstract="a",
        output={"criteria": [], "cannot_decide": True},
        protocol=protocol,
        protocol_fingerprint=client.get(f"{BASE}/records/{study}").json()["binding"]["protocol_fingerprint"],
        provenance={"task_version": "screen-v1", "model": "claude-opus-5-5", "driver": "mcp"},
        created_at="2026-11-04T09:00:00Z",
    )
    assert client.get(f"{BASE}/queue", params={"view": "proposal_ready"}).json()["items"][0]["has_proposal"]
    hidden = client.get(f"{BASE}/records/{study}/proposal")
    assert hidden.status_code == 403 and hidden.json()["detail"]["code"] == "PROPOSAL_HIDDEN"
    _post(client, [_event(client, study)])
    shown = client.get(f"{BASE}/records/{study}/proposal").json()["proposal"]
    assert shown["derived_outcome"] == "MAYBE"


def test_events_project_to_the_batch_decisions_file(client, ws):
    studies = _studies(client)
    _post(client, [_event(client, studies[0]), _event(client, studies[1], "EXCLUDE")])
    path = ws / "literature" / "screening" / "batch_001_decisions.json"
    projected = json.loads(path.read_text(encoding="utf-8"))
    assert projected["source"] == "decision-events"
    assert {d["workspace_id"] for d in projected["decisions"]} == set(studies[:2])


def test_conflict_listed_and_resolved_with_a_superseding_event(client):
    study = _studies(client)[0]
    keep = _event(client, study, "INCLUDE")
    _post(client, [keep])
    assert _post(client, [_event(client, study, "EXCLUDE", device="phone")])[0]["result"] == "conflict"
    conflicts = client.get(f"{BASE}/decisions/conflicts").json()["items"]
    assert [c["study_id"] for c in conflicts] == [study]
    resolved = client.post(f"{BASE}/decisions/conflicts/{study}/resolve", json={"keep_event_id": keep["event_id"]})
    assert resolved.json()["results"][0]["result"] == "accepted"
    assert client.get(f"{BASE}/decisions/conflicts").json()["items"] == []
    assert client.get(f"{BASE}/records/{study}").json()["my_decision"]["outcome"] == "INCLUDE"


def test_more_than_200_events_are_refused(client):
    response = client.post(f"{BASE}/decisions/events", json={"events": [{}] * 201})
    assert response.status_code == 413


def test_required_6_unclear_counted_in_the_prisma_preview(client):
    studies = _studies(client)
    _post(
        client,
        [_event(client, studies[0]), _event(client, studies[1], "EXCLUDE"), _event(client, studies[2], "MAYBE")],
    )
    preview = client.get(f"{BASE}/prisma/preview").json()
    assert preview["included"] == 1
    assert preview["unclear_to_full_text"] == 1
    assert preview["excluded"] == {"total": 1, "by_reason": {"EXC-01": 1}}
    assert preview["not_yet_decided"] == 0
    assert all(check["ok"] for check in preview["checks"])


def test_settings_change_is_journaled_and_ai_exclusion_needs_confirmation(client, ws):
    assert client.get(f"{BASE}/settings").json()["blinding"] == "reveal_after_decision"
    refused = client.put(f"{BASE}/settings", json={"mode": "ai_agreed_exclusion"})
    assert refused.status_code == 422
    ok = client.put(
        f"{BASE}/settings",
        json={"mode": "ai_agreed_exclusion", "sample_audit_size": 40, "confirm_ai_agreed_exclusion": True},
    )
    assert ok.json()["mode"] == "ai_agreed_exclusion"
    rows = [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[-1]["action"] == "SCREENING_SETTINGS_CHANGED"


def test_prepare_refuses_without_an_accepted_snapshot(tmp_path):
    ws = _workspace(tmp_path, prepare=False)
    client = TestClient(create_app(ws), base_url="http://127.0.0.1")
    response = client.post(f"{BASE}/prepare", json={"batch_size": 20})
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "SNAPSHOT_NOT_ACCEPTED"


def test_pairing_begin_needs_an_operator_context(client):
    response = client.post(f"{BASE}/actions/pairing/begin", json={"batch": 1})
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "OPERATOR_CONTEXT_MISSING"


def test_pairing_begin_for_an_event_batch_keeps_the_code_on_the_terminal(client, ws, capsys):
    """Decision 2026-11-04: an event-decided batch needs no worker step, and the
    approval code is printed on the console's terminal, never returned."""
    (ws / "literature" / "screening" / "operator_context.json").write_text(
        json.dumps({"schema": "harness-operator-context-v1", "operator_identity": "researcher@example"}),
        encoding="utf-8",
    )
    studies = _studies(client)
    _post(client, [_event(client, s) for s in studies])
    response = client.post(f"{BASE}/actions/pairing/begin", json={"batch": 1})
    assert response.status_code == 200, response.text
    assert response.json()["code_shown_on"] == "terminal"
    printed = capsys.readouterr().out
    code = printed.split("approval code for batch 1: ")[1].split()[0]
    assert code and code not in response.text


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("POST", f"{BASE}/prepare", {"batch_size": 20}),
        ("POST", f"{BASE}/actions/publish", {"batch": 1}),
        ("POST", f"{BASE}/actions/pairing/redeem", {"batch": 1, "code": "x"}),
        ("POST", f"{BASE}/actions/pairing/begin", {"batch": 1}),
        ("PUT", f"{BASE}/settings", {"blinding": "show"}),
        ("POST", "/api/v1/jobs/start", {"action_id": "status"}),
        ("POST", "/api/v1/proposals/runs", {}),
    ],
)
def test_required_7_phone_token_refused_on_desktop_routes(client, method, path, payload):
    response = client.request(method, path, json=payload, headers={"Authorization": f"Bearer {PHONE}"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "TOKEN_SCOPE_REFUSED"


def test_phone_token_may_read_and_submit_events(client):
    phone = {"Authorization": f"Bearer {PHONE}"}
    assert client.get(f"{BASE}/summary", headers=phone).status_code == 200
    study = _studies(client)[0]
    results = _post(client, [_event(client, study, device="phone")], headers=phone)
    assert results[0]["result"] == "accepted"


def test_review_1_the_audit_feed_never_reveals_a_proposal_outcome(client, ws):
    """Review finding 1: journal rows must not carry the agent's call."""
    study = _studies(client)[0]
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    pr.submit_proposal(
        ws, study_id=study, title="t", abstract="a", output={"criteria": [], "cannot_decide": True},
        protocol=protocol,
        protocol_fingerprint=client.get(f"{BASE}/records/{study}").json()["binding"]["protocol_fingerprint"],
        provenance={"task_version": "screen-v1", "model": "claude-opus-5-5", "driver": "mcp"},
        created_at="2026-11-04T09:00:00Z",
    )
    journal = (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8")
    feed = client.get(f"{BASE}/ui/audit-feed").text
    for text in (journal, feed):
        assert "MAYBE" not in text and "derived" not in text


def test_review_10_agent_uncertainty_orders_unclear_drafts_first(client, ws):
    studies = _studies(client)
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    fingerprint = client.get(f"{BASE}/records/{studies[0]}").json()["binding"]["protocol_fingerprint"]
    # A clean INCLUDE draft for the first record, an Unclear draft for the last.
    record = client.get(f"{BASE}/records/{studies[0]}").json()
    text = pr.record_text(record["title"], record["abstract"])
    quote = text[:5]
    ok = {"criteria": [{"id": c["id"], "answer": "yes" if c["kind"] == "inclusion" else "no",
                        "evidence": {"text": quote, "start": 0, "end": 5}} for c in record["criteria"]],
          "cannot_decide": False}
    pr.submit_proposal(ws, study_id=studies[0], title=record["title"], abstract=record["abstract"], output=ok,
                       protocol=protocol, protocol_fingerprint=fingerprint,
                       provenance={"task_version": "v", "model": "m"}, created_at="2026-11-04T09:00:00Z")
    pr.submit_proposal(ws, study_id=studies[2], title="t", abstract="a", output={"criteria": [], "cannot_decide": True},
                       protocol=protocol, protocol_fingerprint=fingerprint,
                       provenance={"task_version": "v", "model": "m"}, created_at="2026-11-04T09:00:01Z")
    ordered = client.get(f"{BASE}/queue", params={"order": "agent_uncertainty"}).json()["items"]
    assert [i["study_id"] for i in ordered] == [studies[2], studies[0], studies[1]]
    assert "derived_outcome" not in json.dumps(ordered)


def _amend_protocol(ws: Path) -> None:
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    protocol.setdefault("metadata", {})["title"] = "Amended protocol title"
    (ws / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")


def test_review_a_decisions_of_an_earlier_protocol_count_nowhere(client, ws):
    studies = _studies(client)
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    fingerprint = client.get(f"{BASE}/records/{studies[0]}").json()["binding"]["protocol_fingerprint"]
    pr.submit_proposal(
        ws, study_id=studies[0], title="t", abstract="a", output={"criteria": [], "cannot_decide": True},
        protocol=protocol, protocol_fingerprint=fingerprint,
        provenance={"task_version": "v", "model": "m", "prompt_sha256": "sha256:" + "0" * 64},
        created_at="2026-11-04T09:00:00Z",
    )
    assert all(r["result"] == "accepted" for r in _post(client, [_event(client, s) for s in studies]))
    _amend_protocol(ws)
    summary = client.get(f"{BASE}/summary").json()
    assert (summary["decided"], summary["needs_you"]) == (0, 3)
    assert sorted(_studies(client)) == sorted(studies)
    hidden = client.get(f"{BASE}/records/{studies[0]}/proposal")
    assert hidden.status_code == 403 and hidden.json()["detail"]["code"] == "PROPOSAL_HIDDEN"
    # A new decision against the current protocol is accepted, not a conflict.
    assert _post(client, [_event(client, studies[0], "EXCLUDE")])[0]["result"] == "accepted"
    assert client.get(f"{BASE}/decisions/conflicts").json()["items"] == []


def test_review_b_a_projection_failure_after_commit_keeps_the_event_accepted(client, ws, monkeypatch):
    from scholar_harness.screening import events as ev

    study = _studies(client)[0]
    event = _event(client, study, "INCLUDE")
    real = ev.write_projection

    def busy(*args, **kwargs):
        raise PermissionError("decisions file open elsewhere")

    monkeypatch.setattr(ev, "write_projection", busy)
    assert _post(client, [event])[0]["result"] == "accepted"
    assert [e["event_id"] for e in ev.read_events(ws)] == [event["event_id"]]
    decisions = ws / "literature" / "screening" / "batch_001_decisions.json"
    assert not decisions.exists()
    # The retry is a duplicate, and it brings the projection up to date.
    monkeypatch.setattr(ev, "write_projection", real)
    assert _post(client, [event])[0]["result"] == "duplicate"
    assert json.loads(decisions.read_text(encoding="utf-8"))["decisions"][0]["workspace_id"] == study


def test_review_b_a_lock_timeout_is_atomic_commit_failed_and_stores_nothing(client, ws, monkeypatch):
    from scholar_harness.screening import events as ev

    def busy(_workspace):
        raise ev.LockBusy("lock held")

    monkeypatch.setattr(ev, "_locked", busy)
    result = _post(client, [_event(client, _studies(client)[0])])[0]
    assert (result["result"], result["refusal"]["code"]) == ("refused", "ATOMIC_COMMIT_FAILED")
    assert ev.read_events(ws) == []
