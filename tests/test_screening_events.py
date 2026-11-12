"""Screening decision events (contract §3, §8 required tests 1, 2, 3, 5, 8).

Each test builds a synthetic workspace (accepted corpus, prepared batch),
submits events through `intake`, and checks the stored log, the projection to
`batch_001_decisions.json`, and what `cmd_collect` makes of it.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scholar_harness.contracts import AcceptanceContext, accept_artifact
from scholar_harness.screening import events as ev
from scholar_harness.screening.batcher import cmd_prepare
from scholar_harness.screening.collector import cmd_collect
from scholar_protocol.canonical import canonical_fingerprint
from scholar_protocol.models import ResearchProtocol
from scholar_search.identity import build_corpus_snapshot_artifact
from scholar_search.models import Author, Document, ExternalIds

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "tests" / "kits" / "protocol" / "fixtures" / "canonical" / "identity_base.json"
WS_ID = "WSP-" + "c" * 32
SCREENER = "researcher:local-1"


@pytest.fixture
def ws(tmp_path) -> Path:
    return _build(tmp_path)


def _build(tmp_path: Path, *, batch_size: int = 20, method: dict | None = None) -> Path:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "project.json").write_text(
        json.dumps({"project_id": "events", "registered_workspace_id": WS_ID}), encoding="utf-8"
    )
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if method is not None:  # M7-method: screened under a protocol with a method block
        protocol["method"] = method
    (workspace / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    fingerprint = canonical_fingerprint(ResearchProtocol.model_validate(protocol))
    docs = [
        Document(
            title=f"Event record {i}",
            year=2026,
            provider="crossref",
            provider_id=f"ev-{i}",
            external_ids=ExternalIds(doi=f"10.1000/ev-{i}"),
            authors=[Author("Reviewer")],
        )
        for i in range(3)
    ]
    built = build_corpus_snapshot_artifact(
        docs,
        workspace_id=WS_ID,
        run_id="RUN-events",
        protocol_fingerprint=fingerprint,
        created_at=datetime(2026, 11, 4, tzinfo=UTC),
        commit="2" * 40,
    )
    corpus = built.artifact
    assert accept_artifact(
        workspace,
        corpus,
        expected=AcceptanceContext(
            workspace_id=WS_ID,
            protocol_fingerprint=fingerprint,
            corpus_fingerprint=corpus["corpus_fingerprint"],
        ),
    ).accepted
    (workspace / "literature").mkdir()
    (workspace / "literature" / "verified.json").write_text(
        json.dumps(
            [{"workspace_id": s["study_id"], "title": s["title"]} for s in corpus["data"]["studies"]]
        ),
        encoding="utf-8",
    )
    (workspace / "audit" / "journal.jsonl").touch()
    cmd_prepare(workspace, batch_size=batch_size)
    return workspace


def _studies(ws: Path) -> list[str]:
    return sorted(ev.load_context(ws).study_batch)


def _event(ws: Path, study: str, outcome: str = "INCLUDE", **overrides) -> dict:
    context = ev.load_context(ws)
    batch = context.batches[context.study_batch[study]]
    event = {
        "event_id": str(uuid.uuid4()),
        "study_id": study,
        "screener_id": SCREENER,
        "method": "HUMAN",
        "outcome": outcome,
        "reason_code": "EXC-01" if outcome == "EXCLUDE" else None,
        "note": None,
        "criteria": [],
        "decided_at": "2026-11-04T10:00:00.000Z",
        "device": "desktop",
        "supersedes": None,
        "proposal_shown": None,
        "binding": {
            "protocol_fingerprint": context.protocol_fingerprint,
            "batch_id": batch.batch_id,
            "batch_sha256": batch.batch_sha256,
        },
    }
    event.update(overrides)
    return event


def _received_after(events: list[dict]) -> str:
    """The engine's clock five seconds after the latest `decided_at` sent (F7: a
    decision ahead of the engine's clock is refused), `10:00:05Z` for the default event."""
    latest = datetime(2026, 11, 4, 10, 0, 0, tzinfo=UTC)
    for event in events:
        parsed = ev._parse_time(event.get("decided_at")) if isinstance(event, dict) else None
        if parsed is not None and parsed > latest:
            latest = parsed
    return (latest + timedelta(seconds=5)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _intake(ws: Path, events: list[dict], **kw) -> list[str]:
    kw.setdefault("token_scope", "desktop")
    kw.setdefault("received_at", _received_after(events))
    return [r.result for r in ev.intake(ws, events, **kw)]


def _journal(ws: Path) -> list[dict]:
    path = ws / "audit" / "journal.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_accepted_events_are_stored_with_engine_stamps(ws):
    studies = _studies(ws)
    assert _intake(ws, [_event(ws, studies[0])]) == ["accepted"]
    stored = ev.read_events(ws)
    assert len(stored) == 1
    assert stored[0]["received_at"] == "2026-11-04T10:00:05Z"
    assert stored[0]["token_scope"] == "desktop"
    assert stored[0]["changed_after_reveal"] is False


def test_required_2_duplicate_vs_idempotency_conflict(ws):
    studies = _studies(ws)
    event = _event(ws, studies[0])
    assert _intake(ws, [event]) == ["accepted"]
    assert _intake(ws, [event]) == ["duplicate"]
    changed = {**event, "outcome": "MAYBE"}
    results = ev.intake(ws, [changed], token_scope="desktop", received_at="2026-11-04T10:01:00Z")
    assert results[0].result == "refused"
    assert results[0].refusal["code"] == "IDEMPOTENCY_CONFLICT"
    assert len(ev.read_events(ws)) == 1


def test_engine_fields_cannot_be_set_by_the_client(ws):
    studies = _studies(ws)
    results = ev.intake(
        ws,
        [_event(ws, studies[0], changed_after_reveal=True)],
        token_scope="desktop",
        received_at="2026-11-04T10:00:05Z",
    )
    assert results[0].refusal["code"] == "INVALID_OUTPUT"


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"outcome": "EXCLUDE", "reason_code": None}, "REASON_CODE_INVALID"),
        ({"outcome": "EXCLUDE", "reason_code": "EXC-99"}, "REASON_CODE_INVALID"),
        ({"study_id": "STU-" + "0" * 32}, "UNKNOWN_STUDY"),
        ({"decided_at": "1970-01-01T00:00:00Z"}, "PROVENANCE_MISSING"),
        ({"screener_id": ""}, "PROVENANCE_MISSING"),
        ({"method": "LLM"}, "INVALID_OUTPUT"),
        ({"event_id": "not-a-uuid"}, "INVALID_OUTPUT"),
    ],
    ids=["exclude-no-reason", "exclude-bad-reason", "unknown-study", "epoch", "no-screener", "llm", "bad-id"],
)
def test_required_5_and_other_refusals(ws, overrides, code):
    studies = _studies(ws)
    results = ev.intake(
        ws, [_event(ws, studies[0], **overrides)], token_scope="desktop", received_at="2026-11-04T10:00:05Z"
    )
    assert results[0].result == "refused"
    assert results[0].refusal["code"] == code
    assert ev.read_events(ws) == []


def test_exclude_accepts_a_fails_inclusion_code(ws):
    studies = _studies(ws)
    inclusion = sorted(ev.load_context(ws).inclusion_ids)[0]
    assert _intake(ws, [_event(ws, studies[0], "EXCLUDE", reason_code=f"FAILS-{inclusion}")]) == ["accepted"]


def test_stale_binding_is_refused(ws):
    studies = _studies(ws)
    event = _event(ws, studies[0])
    event["binding"] = {**event["binding"], "batch_sha256": "sha256:" + "0" * 64}
    results = ev.intake(ws, [event], token_scope="desktop", received_at="2026-11-04T10:00:05Z")
    assert results[0].refusal["code"] == "STALE_BINDING"


def test_required_3_conflict_leaves_the_projection_and_collect_refuses(ws):
    studies = _studies(ws)
    decided = [_event(ws, s) for s in studies]
    assert _intake(ws, decided) == ["accepted"] * 3
    rival = _event(ws, studies[0], "EXCLUDE", device="phone")
    assert _intake(ws, [rival], token_scope="phone") == ["conflict"]
    assert [c["study_id"] for c in ev.conflicts(ev.read_events(ws))] == [studies[0]]
    path = ev.write_projection(ws, 1, SCREENER, workspace_id=WS_ID)
    projected = json.loads(path.read_text(encoding="utf-8"))
    assert studies[0] not in {d["workspace_id"] for d in projected["decisions"]}
    with pytest.raises(RuntimeError, match="collection blocked"):
        cmd_collect(ws)


def test_same_outcome_from_a_second_device_is_a_confirmation(ws):
    studies = _studies(ws)
    assert _intake(ws, [_event(ws, studies[0])]) == ["accepted"]
    assert _intake(ws, [_event(ws, studies[0], device="phone")], token_scope="phone") == ["accepted"]
    assert ev.conflicts(ev.read_events(ws)) == []


def test_superseding_event_wins_and_carries_its_parent_decision_id(ws):
    studies = _studies(ws)
    first = _event(ws, studies[0], "INCLUDE")
    assert _intake(ws, [first]) == ["accepted"]
    second = _event(ws, studies[0], "MAYBE", supersedes=first["event_id"], decided_at="2026-11-04T10:05:00.000Z")
    assert _intake(ws, [second]) == ["accepted"]
    projected = json.loads(ev.project_batch(ws, 1, SCREENER, workspace_id=WS_ID))
    entry = next(d for d in projected["decisions"] if d["workspace_id"] == studies[0])
    assert entry["decision"] == "MAYBE"
    assert entry["event_id"] == second["event_id"]
    assert entry["parent_decision_ids"] == [
        ev.decision_id_for(WS_ID, ev.load_context(ws).batches[1].batch_id, first, [])
    ]


def test_supersedes_must_name_an_earlier_event(ws):
    studies = _studies(ws)
    results = ev.intake(
        ws,
        [_event(ws, studies[0], supersedes=str(uuid.uuid4()))],
        token_scope="desktop",
        received_at="2026-11-04T10:00:05Z",
    )
    assert results[0].refusal["code"] == "INVALID_OUTPUT"


def test_required_8_one_journal_row_per_accepted_request(ws):
    studies = _studies(ws)
    before = len(_journal(ws))
    _intake(ws, [_event(ws, s) for s in studies], device="phone")
    rows = _journal(ws)[before:]
    assert [r["action"] for r in rows] == ["SCREENING_DECISIONS_RECEIVED"]
    assert rows[0]["metrics"]["events"] == 3
    _intake(ws, [ev.read_events(ws)[0] | {}])  # nothing new: no row
    assert len(_journal(ws)) == before + 1


def test_events_and_journal_row_are_written_together_or_not_at_all(ws, monkeypatch):
    studies = _studies(ws)

    def broken(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(ev, "append_event", broken)
    results = ev.intake(ws, [_event(ws, studies[0])], token_scope="desktop", received_at="2026-11-04T10:00:05Z")
    assert results[0].refusal["code"] == "ATOMIC_COMMIT_FAILED"
    assert ev.read_events(ws) == []


def test_required_1_replay_gives_byte_identical_projection_and_approval_stays_valid(ws):
    studies = _studies(ws)
    decided = [
        _event(ws, studies[0], "INCLUDE"),
        _event(ws, studies[1], "EXCLUDE"),
        _event(ws, studies[2], "MAYBE", note="Cannot tell from the abstract."),
    ]
    _intake(ws, decided)
    path = ev.write_projection(ws, 1, SCREENER, workspace_id=WS_ID)
    first = path.read_bytes()

    from scholar_harness.authority.generations import load_publication_approval

    _stage_approval(ws)
    cmd_collect(ws)
    approval = load_publication_approval(ws / "literature" / "screening")
    published = (ws / "literature" / "included.json").read_bytes()

    # The offline phone replays the same queue: all duplicates, same bytes.
    assert _intake(ws, decided, received_at="2026-11-05T08:00:00Z") == ["duplicate"] * 3
    path = ev.write_projection(ws, 1, SCREENER, workspace_id=WS_ID)
    assert path.read_bytes() == first
    cmd_collect(ws)  # the staged approval still matches: publish succeeds again
    assert load_publication_approval(ws / "literature" / "screening") == approval
    assert (ws / "literature" / "included.json").read_bytes() == published

    decisions = json.loads(first)["decisions"]
    assert {d["method"] for d in decisions} == {"HUMAN"}
    assert {d["decided_at"] for d in decisions} == {"2026-11-04T10:00:00.000Z"}


class _CapturePublish(Exception):
    """Test-only sentinel carrying the content a collect would publish."""


def _review_content(ws: Path) -> dict[str, str]:
    """The exact partition content the next collect would publish (no write)."""
    import scholar_harness.authority.generations as generations

    real = generations.publish_generation

    def capture(**kwargs):
        raise _CapturePublish(kwargs["content"])

    generations.publish_generation = capture
    try:
        try:
            cmd_collect(ws)
        except _CapturePublish as captured:
            return dict(captured.args[0])
    finally:
        generations.publish_generation = real
    raise AssertionError("collect returned without reaching the publication gate")


def _stage_approval(ws: Path) -> None:
    """Review the outputs, then mint an approval over exactly those bytes."""
    from scholar_harness.authority.binding import OperatorIdentity
    from scholar_harness.authority.generations import (
        build_publication_snapshot,
        content_sha256,
        mint_publication_approval,
        publication_binding,
        publication_file_bytes,
        resolve_publication_scope,
        write_publication_approval,
    )

    outputs = _review_content(ws)
    scope = resolve_publication_scope(ws)
    bindings = [dict(b) for b in scope.batch_bindings]
    snapshot = build_publication_snapshot(
        workspace_id=scope.workspace_id,
        run_id=scope.run_id,
        batch_bindings=bindings,
        protocol_fingerprint=scope.protocol_fingerprint,
        corpus_fingerprint=scope.corpus_fingerprint,
        output_digests={n: content_sha256(publication_file_bytes(t)) for n, t in outputs.items()},
    )
    binding = publication_binding(
        workspace_id=scope.workspace_id,
        run_id=scope.run_id,
        batch_bindings=bindings,
        protocol_fingerprint=scope.protocol_fingerprint,
        corpus_fingerprint=scope.corpus_fingerprint,
    )
    record = mint_publication_approval(
        operator=OperatorIdentity(identity="events-operator", source="publisher-operator-context"),
        binding=binding,
        snapshot_bytes=snapshot,
        approved_at="2026-11-04T11:00:00+00:00",
    )
    write_publication_approval(
        ws / "literature" / "screening", record, staged_at="2026-11-04T11:00:00+00:00"
    )


# --- approval (CON-02/03, decision 2026-11-04) --------------------------------


def _operator(ws: Path) -> None:
    (ws / "literature" / "screening" / "operator_context.json").write_text(
        json.dumps({"schema": "harness-operator-context-v1", "operator_identity": "researcher@example"}),
        encoding="utf-8",
    )


def _decide_all(ws: Path, outcome: str = "INCLUDE") -> None:
    _intake(ws, [_event(ws, s, outcome) for s in _studies(ws)])
    for index in ev.load_context(ws).batches:
        ev.write_projection(ws, index, SCREENER, workspace_id=WS_ID)


def test_event_decided_batch_approves_without_a_worker_recommendation(ws):
    from scholar_harness.authority.review import approve_command

    _operator(ws)
    _decide_all(ws)
    result = approve_command(ws, 1, approved_at="2026-11-04T12:00:00+00:00")
    assert result["superseded"] is False
    review = json.loads(Path(result["review_path"]).read_text(encoding="utf-8"))
    assert review["source"] == "decision-events"
    assert review["identity_basis"] == "unauthenticated-local-attestation"
    assert result["publication_staged"] is True
    cmd_collect(ws)  # the staged approval publishes
    assert (ws / "literature" / "included.json").is_file()


def test_con03_one_batch_approval_never_seals_another_batch(tmp_path):
    from scholar_harness.authority.review import approve_command

    ws = _two_batch_workspace(tmp_path)
    _operator(ws)
    _decide_all(ws)
    first = approve_command(ws, 1, approved_at="2026-11-04T12:00:00+00:00")
    assert first["publication_staged"] is False
    assert first["publication_pending_batches"] == [2]
    assert not (ws / "literature" / "screening" / "publication_approval.json").exists()
    with pytest.raises(RuntimeError):
        cmd_collect(ws)  # APPROVAL_MISSING: batch 2 was never approved
    second = approve_command(ws, 2, approved_at="2026-11-04T12:05:00+00:00")
    assert second["publication_staged"] is True
    cmd_collect(ws)
    assert (ws / "literature" / "included.json").is_file()


def test_con03_a_changed_batch_needs_a_fresh_approval(tmp_path):
    from scholar_harness.authority.review import approve_command

    ws = _two_batch_workspace(tmp_path)
    _operator(ws)
    _decide_all(ws)
    approve_command(ws, 1, approved_at="2026-11-04T12:00:00+00:00")
    # The researcher changes a batch-1 decision after approving it.
    study = ev.load_context(ws).batches[1].candidates[0]
    head = ev.winning_event(ev.read_events(ws), study, SCREENER)
    _intake(ws, [_event(ws, study, "MAYBE", supersedes=head["event_id"], decided_at="2026-11-04T12:01:00.000Z")])
    ev.write_projection(ws, 1, SCREENER, workspace_id=WS_ID)
    second = approve_command(ws, 2, approved_at="2026-11-04T12:05:00+00:00")
    assert second["publication_staged"] is False
    assert second["publication_pending_batches"] == [1]


def _two_batch_workspace(tmp_path: Path) -> Path:
    """Three studies prepared as two batches (2 + 1)."""
    workspace = _build(tmp_path, batch_size=2)
    assert sorted(ev.load_context(workspace).batches) == [1, 2]
    return workspace


def test_review_2_a_hand_written_event_claim_does_not_skip_the_worker_step(ws):
    """Review finding 2: `source: decision-events` must match the real projection."""
    from scholar_harness.authority.review import approve_command
    from scholar_harness.screening.worker import WorkerRefused

    _operator(ws)
    _decide_all(ws)
    path = ws / "literature" / "screening" / "batch_001_decisions.json"
    forged = json.loads(path.read_text(encoding="utf-8"))
    for entry in forged["decisions"]:
        entry["method"] = "LLM"
    path.write_text(json.dumps(forged), encoding="utf-8")
    with pytest.raises(WorkerRefused, match="WORKER_BATCH_MISSING"):
        approve_command(ws, 1, approved_at="2026-11-04T12:00:00+00:00")


def test_review_3_events_bound_to_an_earlier_generation_are_not_projected(tmp_path):
    """Review finding 3: a protocol change makes earlier events stale.

    Re-preparing the same corpus under the same protocol is idempotent (same
    batch generation), so the change that moves the generation is the
    protocol. Earlier events then leave the projection, the projected bytes
    change, and a previous approval no longer counts as current.
    """
    from scholar_harness.authority.review import _pending_batches

    ws = _build(tmp_path)
    _operator(ws)
    _decide_all(ws)
    path = ev.write_projection(ws, 1, SCREENER, workspace_id=WS_ID)
    before = path.read_bytes()
    assert json.loads(before)["decisions"]

    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    protocol.setdefault("metadata", {})["title"] = "Amended protocol title"
    (ws / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")

    after = ev.write_projection(ws, 1, SCREENER, workspace_id=WS_ID).read_bytes()
    assert json.loads(after)["decisions"] == []
    assert after != before
    assert _pending_batches(ws, 0, b"") == [1]


def test_review_7_a_non_os_journal_failure_also_rolls_back(ws, monkeypatch):
    def broken(*args, **kwargs):
        raise ValueError("bad journal row")

    monkeypatch.setattr(ev, "append_event", broken)
    results = ev.intake(ws, [_event(ws, _studies(ws)[0])], token_scope="desktop", received_at="2026-11-04T10:00:05Z")
    assert results[0].refusal["code"] == "ATOMIC_COMMIT_FAILED"
    assert ev.read_events(ws) == []


def test_review_b2_a_failed_projection_after_approval_blocks_collect(tmp_path):
    """A stored decision whose file rewrite failed is journaled, and collect
    refuses rather than publish the older, still-approved file."""
    import json as _json

    from scholar_harness.authority.review import approve_command
    from scholar_harness.screening.collector import cmd_collect

    ws = _build(tmp_path)
    _operator(ws)
    _decide_all(ws)
    approve_command(ws, 1, approved_at="2026-11-04T12:00:00+00:00")
    study = _studies(ws)[0]
    head = next(e for e in ev.read_events(ws) if e["study_id"] == study)
    change = _event(ws, study, "EXCLUDE", supersedes=head["event_id"], decided_at="2026-11-04T13:00:00.000Z")

    def held_open(_stored):
        raise PermissionError("decisions file held open")

    results = ev.intake(ws, [change], token_scope="desktop", received_at="2026-11-04T13:00:05Z", after_commit=held_open)
    assert results[0].result == "accepted"
    rows = [_json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[-1]["action"] == "SCREENING_PROJECTION_FAILED"
    assert ev.stale_projections(ws) == [1]
    with pytest.raises(RuntimeError, match="PROJECTION_STALE") as refused:
        cmd_collect(ws)
    assert not (ws / "literature" / "included.json").exists()
    # M1b-0: a typed refusal, which publish returns as 409 PROJECTION_STALE.
    from scholar_harness.console.refusals import CONSOLE_REFUSALS

    assert refused.value.code == "PROJECTION_STALE" and "PROJECTION_STALE" in CONSOLE_REFUSALS


# --- M1b-1: direct HTTP checks deferred from the M1b-0 review (P3-5, P3-6) ------


def _console(ws: Path):
    from fastapi.testclient import TestClient

    from scholar_harness.console import create_app

    return TestClient(create_app(ws, token="t"), base_url="http://127.0.0.1", headers={"Authorization": "Bearer t"})


def test_m1b1_publish_refuses_a_stale_decisions_file_with_a_typed_409(tmp_path):
    """P3-5: publish answers 409 PROJECTION_STALE, not a generic refusal."""
    from scholar_harness.authority.review import approve_command

    ws = _build(tmp_path)
    _operator(ws)
    _decide_all(ws)
    approve_command(ws, 1, approved_at="2026-11-04T12:00:00+00:00")
    study = _studies(ws)[0]
    head = next(e for e in ev.read_events(ws) if e["study_id"] == study)
    change = _event(ws, study, "EXCLUDE", supersedes=head["event_id"], decided_at="2026-11-04T13:00:00.000Z")

    def held_open(_stored):
        raise PermissionError("decisions file held open")

    assert ev.intake(ws, [change], token_scope="desktop", received_at="2026-11-04T13:00:05Z", after_commit=held_open)[0].result == "accepted"
    response = _console(ws).post(
        "/api/v1/screening/actions/publish", json={"request_id": None}, headers={"Origin": "http://127.0.0.1:3117"}
    )
    assert response.status_code == 409, response.text
    assert response.json()["detail"]["code"] == "PROJECTION_STALE"
    assert not (ws / "literature" / "included.json").exists()


def test_m1b1_replaying_the_approved_events_keeps_the_approval_and_publishes(tmp_path):
    """P3-6: re-posting every approved event is a duplicate, and the approval still publishes."""
    from scholar_harness.authority.review import approve_command

    ws = _build(tmp_path)
    _operator(ws)
    _decide_all(ws)
    approve_command(ws, 1, approved_at="2026-11-04T12:00:00+00:00")
    decisions = ws / "literature" / "screening" / "batch_001_decisions.json"
    before = decisions.read_bytes()
    stored = [{k: v for k, v in e.items() if k not in ev.ENGINE_FIELDS} for e in ev.read_events(ws)]

    results = _console(ws).post("/api/v1/screening/decisions/events", json={"events": stored}).json()["results"]
    assert {r["result"] for r in results} == {"duplicate"}
    assert decisions.read_bytes() == before
    response = _console(ws).post(
        "/api/v1/screening/actions/publish", json={"request_id": None}, headers={"Origin": "http://127.0.0.1:3117"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "CURRENT"
    assert (ws / "literature" / "included.json").is_file()


def test_m1b1_redeeming_one_batch_of_several_approves_it_without_staging_publication(tmp_path):
    """Found by the M1b-1 live gate: since CON-03, approving one batch of several
    stages no publication approval, and redeem_pairing read that key
    unconditionally, so every batch but the last failed with a KeyError (500)."""
    from scholar_harness.authority.pairing import begin_pairing, redeem_pairing

    ws = _two_batch_workspace(tmp_path)
    _operator(ws)
    _decide_all(ws)
    staged = begin_pairing(ws, 1)
    result = redeem_pairing(ws, 1, staged["code"], request_id="REQ-m1b1-a")
    assert result["batch_index"] == 1
    assert result["publication_approval_fingerprint"] is None  # batch 2 is not approved yet
    # The idempotent retry returns the same summary rather than failing.
    retry = redeem_pairing(ws, 1, staged["code"], request_id="REQ-m1b1-a")
    assert retry.pop("idempotent") is True and retry == result

    last = begin_pairing(ws, 2)
    final = redeem_pairing(ws, 2, last["code"], request_id="REQ-m1b1-b")
    assert final["publication_approval_fingerprint"]  # the last batch stages publication
    cmd_collect(ws)
    assert (ws / "literature" / "included.json").is_file()


def test_published_prisma_counts_a_fails_inclusion_exclusion_by_its_reason(ws):
    # M5-slim: an EXCLUDE whose reason is a failed inclusion criterion was
    # counted as UNSPECIFIED in the published prisma_report.json, while the
    # live PRISMA preview counted it by its code.
    studies = _studies(ws)
    inclusion = sorted(ev.load_context(ws).inclusion_ids)[0]
    _intake(ws, [
        _event(ws, studies[0], "EXCLUDE", reason_code=f"FAILS-{inclusion}"),
        _event(ws, studies[1], "EXCLUDE"),
        *[_event(ws, s, "INCLUDE") for s in studies[2:]],
    ])
    ev.write_projection(ws, 1, SCREENER, workspace_id=WS_ID)
    _stage_approval(ws)
    cmd_collect(ws)
    report = json.loads((ws / "literature" / "prisma_report.json").read_text(encoding="utf-8"))
    assert report["exclusion_reasons_breakdown"] == {f"FAILS-{inclusion}": 1, "EXC-01": 1}
    assert "UNSPECIFIED" not in (ws / "literature" / "prisma_screening_report.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("answer", ["yes", "no", "not_reported", None])
def test_an_exclude_reason_must_not_contradict_the_events_own_answer(ws, answer):
    """M6-beta (review S-P1-3): FAILS-INC-n with INC-n answered yes, or EXC-n with EXC-n
    answered no, is refused REASON_CODE_INCONSISTENT; an absent or not_reported answer is not."""
    context = ev.load_context(ws)
    inc, exc = min(context.inclusion_ids), min(context.exclusion_ids)
    studies = _studies(ws)
    for i, (code, criterion, contradiction) in enumerate([(f"FAILS-{inc}", inc, "yes"), (exc, exc, "no")]):
        criteria = [] if answer is None else [{"id": criterion, "answer": answer}]
        event = _event(ws, studies[i], "EXCLUDE", reason_code=code, criteria=criteria)
        result = ev.intake(ws, [event], token_scope="desktop", received_at="2026-11-07T10:00:00Z")[0]
        if answer == contradiction:
            assert result.refusal and result.refusal["code"] == "REASON_CODE_INCONSISTENT", result
        else:
            assert result.result == "accepted", result


# --- F7 (three-phase review): three client-supplied values are checked ------------


@pytest.mark.parametrize(
    ("overrides", "kw", "code"),
    [
        ({"decided_at": "2031-01-01T00:00:00Z"}, {}, "PROVENANCE_MISSING"),
        # received_at is 10:00:05; five minutes and one second later is refused
        ({"decided_at": "2026-11-04T10:05:06Z"}, {}, "PROVENANCE_MISSING"),
        ({"decided_at": "2026-11-04T12:05:06+02:00"}, {}, "PROVENANCE_MISSING"),  # the same instant, offset form
        ({"device": "phone"}, {}, "INVALID_OUTPUT"),
        ({"device": "desktop"}, {"token_scope": "phone"}, "INVALID_OUTPUT"),
        ({"note": "n" * (ev.MAX_NOTE_CHARS + 1)}, {}, "INVALID_OUTPUT"),
        ({"note": 7}, {}, "INVALID_OUTPUT"),
    ],
    ids=["decided-in-2031", "decided-5min-1s-ahead", "decided-ahead-with-offset", "phone-device-desktop-token",
         "desktop-device-phone-token", "note-too-long", "note-not-text"],
)
def test_f7_future_decisions_foreign_devices_and_long_notes_are_refused(ws, overrides, kw, code):
    studies = _studies(ws)
    kw = {"token_scope": "desktop", "received_at": "2026-11-04T10:00:05Z", **kw}
    results = ev.intake(ws, [_event(ws, studies[0], **overrides)], **kw)
    assert results[0].result == "refused"
    assert results[0].refusal["code"] == code
    assert ev.read_events(ws) == []


def test_f7_values_at_the_limits_are_accepted(ws):
    studies = _studies(ws)
    at_skew = _event(ws, studies[0], decided_at="2026-11-04T10:05:05Z", note="n" * ev.MAX_NOTE_CHARS)
    assert _intake(ws, [at_skew]) == ["accepted"]
    phone = _event(ws, studies[1], device="phone")
    assert _intake(ws, [phone], token_scope="phone") == ["accepted"]
    assert [e["device"] for e in ev.read_events(ws)] == ["desktop", "phone"]


def test_f7_a_stored_event_retried_after_the_limits_is_a_duplicate(ws):
    """Review finding 3: an event stored before the F7 limits (here a long note and a
    phone device under a desktop token, written straight to the log) is still a
    `duplicate` when retried, so the retry re-projects instead of being refused."""
    studies = _studies(ws)
    old = _event(ws, studies[0], device="phone", note="n" * (ev.MAX_NOTE_CHARS + 10))
    stored = {**old, "received_at": "2026-11-04T10:00:05Z", "token_scope": "desktop", "changed_after_reveal": False}
    log = ev.screener_file(ws, SCREENER)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(json.dumps(stored) + "\n", encoding="utf-8")
    assert [e["event_id"] for e in ev.read_events(ws)] == [old["event_id"]]
    assert _intake(ws, [old]) == ["duplicate"]
    # A new event with the same values is refused.
    assert _intake(ws, [{**old, "event_id": str(uuid.uuid4())}]) == ["refused"]
