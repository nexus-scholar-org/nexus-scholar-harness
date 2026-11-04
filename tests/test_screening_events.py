"""Screening decision events (contract §3, §8 required tests 1, 2, 3, 5, 8).

Each test builds a synthetic workspace (accepted corpus, prepared batch),
submits events through `intake`, and checks the stored log, the projection to
`batch_001_decisions.json`, and what `cmd_collect` makes of it.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
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
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "project.json").write_text(
        json.dumps({"project_id": "events", "registered_workspace_id": WS_ID}), encoding="utf-8"
    )
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
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
    cmd_prepare(workspace, batch_size=20)
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


def _intake(ws: Path, events: list[dict], **kw) -> list[str]:
    kw.setdefault("token_scope", "desktop")
    kw.setdefault("received_at", "2026-11-04T10:00:05Z")
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
    assert _intake(ws, [rival]) == ["conflict"]
    assert [c["study_id"] for c in ev.conflicts(ev.read_events(ws))] == [studies[0]]
    path = ev.write_projection(ws, 1, SCREENER, workspace_id=WS_ID)
    projected = json.loads(path.read_text(encoding="utf-8"))
    assert studies[0] not in {d["workspace_id"] for d in projected["decisions"]}
    with pytest.raises(RuntimeError, match="collection blocked"):
        cmd_collect(ws)


def test_same_outcome_from_a_second_device_is_a_confirmation(ws):
    studies = _studies(ws)
    assert _intake(ws, [_event(ws, studies[0])]) == ["accepted"]
    assert _intake(ws, [_event(ws, studies[0], device="phone")]) == ["accepted"]
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
