"""M3g review repairs (milestone-reviewer CHANGES on 9c70a7bb), each test written to fail first.

R1 (P1): a chase deduplicates against every round's records, not only the current round's.
R2 (P2): a chase starts only from a published and current screening under the current protocol.
R3 (P2): the newest-snapshot filter applies only to a workspace with screening rounds.
R4 (P3): a round folder that cannot be made is a typed, journaled ARCHIVE_INCOMPLETE.
R5 (P3): an included row without a published decision is reported, never assumed a seed.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scholar_harness.pipeline import citation_chase as cc
from scholar_harness.screening import events as ev
from scholar_harness.screening import rounds
from scholar_harness.screening.batcher import cmd_prepare

_SPEC = importlib.util.spec_from_file_location("_chase_accept_helpers", Path(__file__).resolve().parent / "test_chase_accept.py")
ca = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ca)
h = ca.h
se = ca.se


@pytest.fixture
def ws(tmp_path: Path) -> Path:
    return h.build_ws(tmp_path)


def test_r1_a_round_3_chase_finds_round_1_records_already_in_the_corpus(ws, monkeypatch):
    round1 = json.loads((ws / "literature" / "verified.json").read_text(encoding="utf-8"))
    first = round1[0]
    ca._chase(ws, monkeypatch)
    cc.accept_citation_chase(ws)
    cmd_prepare(ws, batch_size=20)
    ca._publish_round(ws, "INCLUDE")

    back = h._doc(first["title"], provider="openalex", pid=first["external_ids"]["openalex_id"],
                  doi=first["external_ids"]["doi"], openalex=first["external_ids"]["openalex_id"], year=2026)
    ca._install(monkeypatch, h.FakeChaseProvider("openalex", references={"W1": [back], "W2": [], "W3": []}))
    outcome = asyncio.run(cc.run_citation_chase(ws, providers=["openalex"], directions=["backward"]))

    assert outcome.counts.already_in_corpus == 1 and outcome.counts.new == 0
    manifest = json.loads((ws / "literature" / "citation_chase" / outcome.chase / "chase.json").read_text(encoding="utf-8"))
    (row,) = manifest["already_in_corpus"]
    assert row["study_id"] == first["workspace_id"] and row["round"] == 1


def test_r2_a_stale_publication_or_a_changed_protocol_starts_no_chase(ws, monkeypatch):
    provider = h.FakeChaseProvider("openalex", citations={h.W_INCLUDE: []})
    ca._install(monkeypatch, provider)
    original = (ws / "protocol.json").read_text(encoding="utf-8")
    protocol = json.loads(original)
    protocol["search_strategy"]["date_range"]["start_year"] = 2019
    (ws / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    with pytest.raises(cc.ChaseRefused) as exc:
        asyncio.run(cc.run_citation_chase(ws, providers=["openalex"]))
    assert exc.value.code == "PROTOCOL_CHANGED_SINCE_PUBLISH"
    (ws / "protocol.json").write_text(original, encoding="utf-8")

    included = ws / "literature" / "included.json"
    included.write_bytes(included.read_bytes() + b"\n")  # a changed output: the generation is STALE
    with pytest.raises(cc.ChaseRefused) as exc:
        asyncio.run(cc.run_citation_chase(ws, providers=["openalex"]))
    assert exc.value.code == "SCREENING_NOT_PUBLISHED"
    assert provider.asked == []
    assert not (ws / "literature" / "citation_chase").exists()
    assert cc.publication_state(ws)["published"] is False


def test_r3_without_rounds_a_second_snapshot_drops_no_batch(tmp_path):
    from scholar_protocol.canonical import canonical_fingerprint
    from scholar_protocol.models import ResearchProtocol
    from scholar_search.identity import build_corpus_snapshot_artifact
    from scholar_search.models import Author, Document, ExternalIds

    from scholar_harness.contracts import AcceptanceContext, accept_artifact

    workspace = se._build(tmp_path)
    before = ev.load_context(workspace)
    assert before.batches
    protocol = json.loads((workspace / "protocol.json").read_text(encoding="utf-8"))
    fingerprint = canonical_fingerprint(ResearchProtocol.model_validate(protocol))
    other = build_corpus_snapshot_artifact(
        [Document(title="Another record", year=2026, provider="crossref", provider_id="x-1",
                  external_ids=ExternalIds(doi="10.1000/x-1"), authors=[Author("Other")])],
        workspace_id=se.WS_ID, run_id="RUN-other", protocol_fingerprint=fingerprint,
        created_at=datetime(2026, 11, 5, tzinfo=UTC), commit="3" * 40,
    ).artifact
    assert accept_artifact(workspace, other, expected=AcceptanceContext(
        workspace_id=se.WS_ID, protocol_fingerprint=fingerprint, corpus_fingerprint=other["corpus_fingerprint"],
    )).accepted

    assert ev.newest_corpus_fingerprint(workspace) is None  # no rounds index: no filter
    after = ev.load_context(workspace)
    assert after.batches.keys() == before.batches.keys() and after.study_batch == before.study_batch


def test_r4_a_round_folder_that_cannot_be_made_is_archive_incomplete(ws, monkeypatch):
    ca._chase(ws, monkeypatch)
    blocker = ws / "literature" / "screening_rounds" / "round_001"
    blocker.parent.mkdir(parents=True)
    blocker.write_text("in the way", encoding="utf-8")  # a file where the round folder goes
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws)
    assert exc.value.code == "ARCHIVE_INCOMPLETE"
    assert exc.value.details["moved"] == []
    (row,) = ca._journal(ws, "SCREENING_ROUND_ARCHIVE_INCOMPLETE")
    assert row["status"] == "FAILED"
    assert (ws / "literature" / "screening" / "generation.json").is_file()


def test_r5_an_included_row_without_a_decision_is_not_a_seed(ws):
    rows = json.loads((ws / "literature" / "included.json").read_text(encoding="utf-8"))
    rows[0]["screening"].pop("decision")
    (ws / "literature" / "included.json").write_text(json.dumps(rows), encoding="utf-8")
    seeds = cc.load_seeds(ws)
    missing = [s for s in seeds if s.decision == ""]
    assert len(missing) == 1 and not missing[0].chaseable and "no published decision" in missing[0].reason


# Re-review (a02883b4): a retry after ARCHIVE_INCOMPLETE must resume, whichever step failed.


def test_r4b_a_retry_after_a_round_folder_that_could_not_be_made_resumes(ws, monkeypatch):
    ca._chase(ws, monkeypatch)
    blocker = ws / "literature" / "screening_rounds" / "round_001"
    blocker.parent.mkdir(parents=True)
    blocker.write_text("in the way", encoding="utf-8")
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws)
    assert exc.value.code == "ARCHIVE_INCOMPLETE"
    blocker.unlink()
    accepted = cc.accept_citation_chase(ws)
    assert accepted.round == 2 and accepted.already_accepted
    assert len(ca._corpora(ws)) == 2  # one round-2 snapshot, not a second one
    assert (ws / "literature" / "screening_rounds" / "round_001" / "screening" / "generation.json").is_file()


def test_r4c_a_retry_after_a_failed_first_move_resumes(ws, monkeypatch):
    ca._chase(ws, monkeypatch)
    real_move = rounds.shutil.move

    def failing_first(src, dst):
        raise OSError("locked")

    monkeypatch.setattr(rounds.shutil, "move", failing_first)
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws)
    assert exc.value.code == "ARCHIVE_INCOMPLETE" and exc.value.details["moved"] == []
    monkeypatch.setattr(rounds.shutil, "move", real_move)
    accepted = cc.accept_citation_chase(ws)
    assert accepted.round == 2 and accepted.already_accepted
    assert len(ca._corpora(ws)) == 2
    assert rounds.current_round(ws)["corpus_artifact_id"] == accepted.artifact_id


# Deferred P3 (M3g review): a new chase while a round snapshot is pending must not take it as parent.


def test_r6_a_new_chase_while_an_accept_is_pending_is_refused(ws, monkeypatch):
    first = ca._chase(ws, monkeypatch)
    parent = json.loads((ws / "literature" / "citation_chase" / first.chase / "chase.json").read_text(encoding="utf-8"))
    real_move = rounds.shutil.move

    def failing_first(src, dst):
        raise OSError("locked")

    monkeypatch.setattr(rounds.shutil, "move", failing_first)
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws)
    assert exc.value.code == "ARCHIVE_INCOMPLETE"
    monkeypatch.setattr(rounds.shutil, "move", real_move)
    assert len(ca._corpora(ws)) == 2  # the round-2 snapshot is registered, not yet recorded as a round

    provider = h.FakeChaseProvider("openalex", citations={h.W_INCLUDE: []})
    ca._install(monkeypatch, provider)
    with pytest.raises(cc.ChaseRefused) as exc:
        asyncio.run(cc.run_citation_chase(ws, providers=["openalex"], directions=["forward"]))
    assert exc.value.code == "CHASE_ACCEPT_PENDING"
    assert first.chase in str(exc.value)
    assert provider.asked == []
    assert [p.name for p in (ws / "literature" / "citation_chase").iterdir() if p.is_dir()] == [first.chase]

    # Finishing the accept clears the refusal: the next chase's parent is the round-2 snapshot.
    accepted = cc.accept_citation_chase(ws)
    assert accepted.round == 2 and parent["parent_corpus"]["artifact_id"] != accepted.artifact_id
    cc.require_no_pending_accept(ws)


def _fail_moves(monkeypatch):
    def failing(src, dst):
        raise OSError("locked")

    monkeypatch.setattr(rounds.shutil, "move", failing)


def test_r6b_with_two_chases_on_one_parent_the_refusal_names_the_one_that_failed(ws, monkeypatch):
    """Review of fcc3557e (P1, P2): the pending snapshot belongs to the chase that built it."""
    a = ca._chase(ws, monkeypatch)
    b = ca._chase(ws, monkeypatch, docs=[h._doc("Other", provider="openalex", pid="W9", doi="10.2/z", openalex="W9", year=2023)])
    real_move = rounds.shutil.move
    _fail_moves(monkeypatch)
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws, chase=a.chase)
    assert exc.value.code == "ARCHIVE_INCOMPLETE"
    monkeypatch.setattr(rounds.shutil, "move", real_move)

    assert cc.pending_accept(ws) == a.chase
    with pytest.raises(cc.ChaseRefused) as exc:  # the other chase may not finish a's round
        cc.accept_citation_chase(ws, chase=b.chase)
    assert exc.value.code == "CHASE_ACCEPT_PENDING" and a.chase in str(exc.value)
    assert len(ca._corpora(ws)) == 2  # no third snapshot

    accepted = cc.accept_citation_chase(ws, chase=a.chase)
    assert accepted.round == 2 and cc.pending_accept(ws) is None
    manifest = json.loads((ws / "literature" / "citation_chase" / a.chase / "chase.json").read_text(encoding="utf-8"))
    assert "pending_round" not in manifest and manifest["accepted"]["artifact_id"] == accepted.artifact_id

    # b ran on round 1's corpus: after round 2 is published it is stale, and no lockout remains.
    cmd_prepare(ws, batch_size=20)
    ca._publish_round(ws, "INCLUDE")
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws, chase=b.chase)
    assert exc.value.code == "CHASE_STALE"
    cc.require_no_pending_accept(ws)


def test_r6c_the_owner_is_known_from_the_journal_without_the_marker(ws, monkeypatch):
    a = ca._chase(ws, monkeypatch)
    _fail_moves(monkeypatch)
    with pytest.raises(cc.ChaseRefused):
        cc.accept_citation_chase(ws, chase=a.chase)
    path = ws / "literature" / "citation_chase" / a.chase / "chase.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest.pop("pending_round")  # a run accepted before the marker existed
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert cc.pending_accept(ws) == a.chase


def test_r6d_malformed_manifests_are_skipped(ws, monkeypatch):
    ca._chase(ws, monkeypatch)
    bad = ws / "literature" / "citation_chase" / "chase_002"
    bad.mkdir()
    (bad / "chase.json").write_text("[1, 2]", encoding="utf-8")
    worse = ws / "literature" / "citation_chase" / "chase_003"
    worse.mkdir()
    (worse / "chase.json").write_text(json.dumps({"parent_corpus": "not an object"}), encoding="utf-8")
    assert cc.pending_accept(ws) is None


def test_r6e_a_pending_chase_whose_screening_was_published_again_does_not_lock_the_workspace(ws, monkeypatch):
    """Re-review of 034e4597 (P2): a retry refused CHASE_STALE and a new chase refused
    CHASE_ACCEPT_PENDING left no way out. The stale chase's snapshot stays registered but
    blocks nothing and is never a parent."""
    a = ca._chase(ws, monkeypatch)
    path = ws / "literature" / "citation_chase" / a.chase / "chase.json"
    round1_parent = json.loads(path.read_text(encoding="utf-8"))["parent_corpus"]["artifact_id"]
    real_move = rounds.shutil.move
    _fail_moves(monkeypatch)
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws, chase=a.chase)
    assert exc.value.code == "ARCHIVE_INCOMPLETE"
    monkeypatch.setattr(rounds.shutil, "move", real_move)
    (orphan,) = [aid for aid, _e in ca._corpora(ws) if aid != round1_parent]

    # Round 1 was published again after the chase ran (simulated on the chase's record).
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["generation_id"] = "GEN-an-earlier-publication"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws, chase=a.chase)
    assert exc.value.code == "CHASE_STALE"
    assert cc.pending_accept(ws) is None

    b = ca._chase(ws, monkeypatch, docs=[h._doc("Other", provider="openalex", pid="W9", doi="10.2/z", openalex="W9", year=2023)])
    b_manifest = json.loads((ws / "literature" / "citation_chase" / b.chase / "chase.json").read_text(encoding="utf-8"))
    assert b_manifest["parent_corpus"]["artifact_id"] == round1_parent  # never the orphaned snapshot
    accepted = cc.accept_citation_chase(ws, chase=b.chase)
    assert accepted.round == 2 and accepted.artifact_id != orphan
    assert rounds.current_round(ws)["corpus_artifact_id"] == accepted.artifact_id
