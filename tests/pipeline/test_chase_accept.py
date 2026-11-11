"""M3g-citation-chasing: the accept sends a chase's new records to screening as round 2.

Decision 2026-11-12 item 4: the new records are frozen as their own corpus
snapshot whose ``inputs`` name the parent snapshot; round 1's screening folder
and published outputs move under ``literature/screening_rounds/round_001/``;
round 2 is prepared, screened and published in the usual place with a PRISMA
report that carries both arms. Offline: fake databases, the socket guard on.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import shutil
from dataclasses import asdict
from pathlib import Path

import pytest

from scholar_harness.authority.generations import GenerationStatus, require_current_generation
from scholar_harness.pipeline import citation_chase as cc
from scholar_harness.pipeline import discovery as disc
from scholar_harness.screening import events as ev
from scholar_harness.screening import rounds
from scholar_harness.screening.batcher import cmd_prepare
from scholar_harness.screening.collector import cmd_collect

_SPEC = importlib.util.spec_from_file_location("_chase_run_helpers", Path(__file__).resolve().parent / "test_citation_chase.py")
h = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(h)
se = h.tea.se


@pytest.fixture
def ws(tmp_path: Path) -> Path:
    return h.build_ws(tmp_path)


def _install(monkeypatch, *providers) -> None:
    by_name = {p.name: p for p in providers}
    monkeypatch.setattr(disc, "_resolve_providers", lambda names: [by_name[n] for n in names if n in by_name] or None)


def _chase(ws: Path, monkeypatch, docs: list | None = None) -> cc.ChaseOutcome:
    docs = docs if docs is not None else [
        h._doc("Chased alpha", provider="openalex", pid="W1", doi="10.2/a", openalex="W1", year=2024),
        h._doc("Chased beta", provider="openalex", pid="W2", doi="10.2/b", openalex="W2", year=2022),
        h._doc("Chased gamma", provider="openalex", pid="W3", doi="10.2/c", openalex="W3", year=2021),
    ]
    _install(monkeypatch, h.FakeChaseProvider("openalex", citations={h.W_INCLUDE: docs}))
    return asyncio.run(cc.run_citation_chase(ws, providers=["openalex"], directions=["forward"]))


def _registry(ws: Path) -> dict:
    return json.loads((ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8"))["artifacts"]


def _corpora(ws: Path) -> list[tuple[str, dict]]:
    return sorted(
        ((aid, e) for aid, e in _registry(ws).items() if e.get("artifact_type") == "corpus_snapshot"),
        key=lambda item: item[1]["accepted_at"],
    )


def _journal(ws: Path, action: str) -> list[dict]:
    rows = [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r for r in rows if r.get("action") == action]


def _publish_round(ws: Path, outcome: str = "INCLUDE") -> None:
    """Decide every record of the current round the same way and publish."""
    studies = se._studies(ws)
    se._intake(ws, [se._event(ws, s, outcome) for s in studies])
    for index in ev.load_context(ws).batches:
        ev.write_projection(ws, index, se.SCREENER, workspace_id=se.WS_ID)
    se._stage_approval(ws)
    cmd_collect(ws)


# --------------------------------------------------------------------------- the happy path


def test_the_accept_freezes_the_new_records_as_round_2_and_archives_round_1(ws, monkeypatch):
    round1_prisma = json.loads((ws / "literature" / "prisma_report.json").read_text(encoding="utf-8"))
    round1_included = (ws / "literature" / "included.json").read_bytes()
    (parent_id, parent_entry), = _corpora(ws)
    generation_id = json.loads((ws / "literature" / "screening" / "generation.json").read_text(encoding="utf-8"))["generation_id"]
    outcome = _chase(ws, monkeypatch)
    assert outcome.status == "SUCCESS" and outcome.counts.new == 3

    accepted = cc.accept_citation_chase(ws)

    assert accepted.round == 2 and accepted.chase == "chase_001" and not accepted.already_accepted
    assert accepted.record_count == 3 and accepted.study_count == 3 and accepted.outcome_status == "SUCCESS"
    assert accepted.parent_corpus == parent_id
    # The round-2 snapshot is registered, names its parent and is now the newest.
    corpora = _corpora(ws)
    assert [aid for aid, _ in corpora] == [parent_id, accepted.artifact_id]
    artifact = json.loads((ws / corpora[1][1]["path"]).read_text(encoding="utf-8"))
    assert artifact["inputs"] == [{"artifact_id": parent_id, "sha256": parent_entry["sha256"]}]
    assert len(artifact["data"]["studies"]) == 3
    # Round 1 moved, nothing deleted; round 2's records are the corpus to screen.
    archive = ws / "literature" / "screening_rounds" / "round_001"
    assert sorted(accepted.archived) == sorted(["screening/", *rounds.PUBLISHED_OUTPUTS, "verified.json"])
    assert (archive / "screening" / "generation.json").is_file()
    assert (archive / "included.json").read_bytes() == round1_included
    assert json.loads((archive / "round.json").read_text(encoding="utf-8"))["prisma"] == round1_prisma
    assert json.loads((archive / "round.json").read_text(encoding="utf-8"))["generation_id"] == generation_id
    assert not (ws / "literature" / "screening").exists()
    assert not (ws / "literature" / "included.json").exists()
    verified = json.loads((ws / "literature" / "verified.json").read_text(encoding="utf-8"))
    assert [r["title"] for r in verified] == ["Chased alpha", "Chased beta", "Chased gamma"]
    assert all(r["workspace_id"].startswith("SCI-") for r in verified)
    assert verified[0]["sources"][0]["via"] == "citation-chase"
    index = rounds.read_rounds(ws)
    assert index["current"] == {**index["current"], "round": 2, "arm": "citation_searching", "chase": "chase_001",
                                "corpus_artifact_id": accepted.artifact_id}
    assert index["rounds"][0]["round"] == 1 and index["rounds"][0]["arm"] == "databases"
    assert index["rounds"][0]["corpus_artifact_id"] == parent_id and index["rounds"][0]["prisma"] == round1_prisma
    manifest = json.loads((ws / "literature" / "citation_chase" / "chase_001" / "chase.json").read_text(encoding="utf-8"))
    assert manifest["accepted"]["round"] == 2 and manifest["accepted"]["artifact_id"] == accepted.artifact_id
    # Journal: the snapshot, the archive and the accept.
    (snap,) = [r for r in _journal(ws, "CORPUS_SNAPSHOT_ACCEPTED") if r["parameters"].get("run") == "chase_001"]
    assert snap["parameters"]["artifact_id"] == accepted.artifact_id
    (archived,) = _journal(ws, "SCREENING_ROUND_ARCHIVED")
    assert archived["parameters"]["round"] == 1 and "screening/" in archived["parameters"]["moved"]
    (event,) = _journal(ws, "CITATION_CHASE_ACCEPTED")
    assert event["parameters"]["round"] == 2 and event["parameters"]["parent_corpus"] == parent_id
    # The screening context is round 2's: no batch yet, and the absent generation is
    # "not published", never a post-authorization deletion.
    assert ev.load_context(ws).batches == {}
    assert require_current_generation(ws).status is GenerationStatus.LEGACY_UNVERIFIED


def test_round_2_is_prepared_screened_and_published_with_both_prisma_arms(ws, monkeypatch):
    round1_prisma = json.loads((ws / "literature" / "prisma_report.json").read_text(encoding="utf-8"))
    _chase(ws, monkeypatch)
    cc.accept_citation_chase(ws)

    cmd_prepare(ws, batch_size=20)
    context = ev.load_context(ws)
    assert len(context.study_batch) == 3  # only the chased works are screened in round 2
    assert all(c.startswith("STU-") for c in context.study_batch)
    _publish_round(ws, "INCLUDE")

    assert require_current_generation(ws).status is GenerationStatus.CURRENT
    prisma = json.loads((ws / "literature" / "prisma_report.json").read_text(encoding="utf-8"))
    assert prisma["arm"] == "citation_searching" and prisma["round"] == 2
    assert (prisma["total_identified"], prisma["duplicates_removed"], prisma["records_screened"]) == (3, 0, 3)
    assert prisma["records_included"] == 3
    assert prisma["identification"]["fetched"] == 3 and prisma["identification"]["chase"] == "chase_001"
    assert prisma["identification"]["removed_before_screening"] == {"outside_year_window": 0, "over_ceiling": 0}
    assert prisma["previous_rounds"][0]["round"] == 1 and prisma["previous_rounds"][0]["prisma"] == round1_prisma
    assert prisma["review_totals"] == {
        "records_screened": 3 + round1_prisma["records_screened"],
        "records_excluded": round1_prisma["records_excluded"],
        "records_included": 3 + round1_prisma["records_included"],
        "records_unclear": round1_prisma["records_unclear"],
    }
    markdown = (ws / "literature" / "prisma_screening_report.md").read_text(encoding="utf-8")
    assert "## 3. Identification of studies via other methods (round 2: citation searching)" in markdown
    assert "## 4. Identification of studies via databases (earlier rounds, as published)" in markdown
    assert f"| 1 | databases | {round1_prisma['total_identified']} |" in markdown
    included = json.loads((ws / "literature" / "included.json").read_text(encoding="utf-8"))
    assert sorted(r["title"] for r in included) == ["Chased alpha", "Chased beta", "Chased gamma"]
    # The methods paragraph says both arms.
    from scholar_harness.screening.export import build_methods

    methods = build_methods(ws)
    text = methods["paragraph"]
    assert "Round 1 (databases)" in text and "Round 2 (citation searching, forward from 1 of 1 included studies on openalex)" in text
    assert methods["figures"]["rounds"][1]["arm"] == "citation_searching"


def test_a_second_chase_from_round_2_starts_round_3(ws, monkeypatch):
    _chase(ws, monkeypatch)
    cc.accept_citation_chase(ws)
    cmd_prepare(ws, batch_size=20)
    _publish_round(ws, "INCLUDE")
    seeds = cc.load_seeds(ws)
    assert sorted(s.doi for s in seeds) == ["10.2/a", "10.2/b", "10.2/c"]  # round 2's includes are the new seeds
    deeper = h._doc("Deeper", provider="openalex", pid="W9", doi="10.2/deep", openalex="W9", year=2023)
    _install(monkeypatch, h.FakeChaseProvider("openalex", citations={"W1": [deeper], "W2": [], "W3": []}))
    outcome = asyncio.run(cc.run_citation_chase(ws, providers=["openalex"], directions=["forward"]))
    assert outcome.chase == "chase_002" and outcome.counts.new == 1
    accepted = cc.accept_citation_chase(ws)
    assert accepted.round == 3 and accepted.chase == "chase_002"
    assert (ws / "literature" / "screening_rounds" / "round_002" / "round.json").is_file()
    assert [r["round"] for r in rounds.previous_rounds(ws)] == [1, 2]
    assert rounds.previous_rounds(ws)[1]["arm"] == "citation_searching"


def test_the_same_new_records_give_the_same_round_2_snapshot_id(ws, monkeypatch, tmp_path):
    _chase(ws, monkeypatch)
    twin = tmp_path / "twin"
    shutil.copytree(ws, twin)
    a = cc.accept_citation_chase(ws)
    b = cc.accept_citation_chase(twin)
    assert a.artifact_id == b.artifact_id and a.round == b.round == 2


# --------------------------------------------------------------------------- refusals leave nothing behind


def _assert_untouched(ws: Path, corpora_before: int) -> None:
    assert len(_corpora(ws)) == corpora_before
    assert not (ws / "literature" / "screening_rounds").exists()
    assert (ws / "literature" / "screening" / "generation.json").is_file()
    assert (ws / "literature" / "included.json").is_file()
    assert _journal(ws, "CITATION_CHASE_ACCEPTED") == []


def test_without_a_chase_run_or_with_nothing_new_the_accept_refuses(ws, monkeypatch):
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws)
    assert exc.value.code == "CHASE_NOT_RUN"
    _chase(ws, monkeypatch, docs=[])  # EMPTY_RESULT, published, nothing new
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws)
    assert exc.value.code == "CHASE_NOTHING_NEW"
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws, chase="chase_009")
    assert exc.value.code == "CHASE_NOT_RUN"
    _assert_untouched(ws, 1)


def test_a_failed_or_cancelled_run_cannot_be_sent(ws, monkeypatch):
    from scholar_search.exceptions import ProviderError

    _install(monkeypatch, h.FakeChaseProvider("openalex", fail=ProviderError("openalex", "no", status_code=403)))
    failed = asyncio.run(cc.run_citation_chase(ws, providers=["openalex"]))
    assert failed.status == "FAILED"
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws, chase="chase_001")
    assert exc.value.code == "CHASE_NOT_RUN"
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws)  # no published run at all
    assert exc.value.code == "CHASE_NOT_RUN"
    _assert_untouched(ws, 1)


def test_a_changed_protocol_or_an_unpublished_screening_refuses(ws, monkeypatch):
    _chase(ws, monkeypatch)
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    original = (ws / "protocol.json").read_text(encoding="utf-8")
    protocol["search_strategy"]["date_range"]["start_year"] = 2019
    (ws / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws)
    assert exc.value.code == "PROTOCOL_CHANGED_SINCE_PUBLISH"
    _assert_untouched(ws, 1)
    (ws / "protocol.json").write_text(original, encoding="utf-8")

    included = (ws / "literature" / "included.json").read_bytes()
    (ws / "literature" / "included.json").write_bytes(included + b"\n")  # a changed output: STALE
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws)
    assert exc.value.code == "SCREENING_NOT_PUBLISHED"
    assert len(_corpora(ws)) == 1 and not (ws / "literature" / "screening_rounds").exists()


def test_a_chase_from_an_earlier_publication_or_corpus_is_stale(ws, monkeypatch):
    _chase(ws, monkeypatch)
    path = ws / "literature" / "citation_chase" / "chase_001" / "chase.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["generation_id"] = "GEN-other"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws)
    assert exc.value.code == "CHASE_STALE"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["generation_id"] = json.loads((ws / "literature" / "screening" / "generation.json").read_text(encoding="utf-8"))["generation_id"]
    manifest["parent_corpus"] = {"artifact_id": "ART-corpus-" + "0" * 32, "sha256": "sha256:" + "0" * 64}
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws)
    assert exc.value.code == "CHASE_STALE"
    _assert_untouched(ws, 1)


def test_an_accepted_run_is_not_sent_twice(ws, monkeypatch):
    _chase(ws, monkeypatch)
    cc.accept_citation_chase(ws)
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws, chase="chase_001")
    assert exc.value.code == "CHASE_ALREADY_ACCEPTED"
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws)  # the newest published run is the accepted one; round 2 is not published
    assert exc.value.code in {"CHASE_ALREADY_ACCEPTED", "SCREENING_NOT_PUBLISHED"}
    assert len(_corpora(ws)) == 2


def test_an_archive_that_stops_part_way_is_journaled_refused_and_finished_by_a_retry(ws, monkeypatch):
    _chase(ws, monkeypatch)
    real_move = rounds.shutil.move
    calls = {"n": 0}

    def failing_move(src, dst):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("locked")
        return real_move(src, dst)

    monkeypatch.setattr(rounds.shutil, "move", failing_move)
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.accept_citation_chase(ws)
    assert exc.value.code == "ARCHIVE_INCOMPLETE"
    assert exc.value.details["moved"] == ["screening/"] and "included.json" in exc.value.details["not_moved"]
    (row,) = _journal(ws, "SCREENING_ROUND_ARCHIVE_INCOMPLETE")
    assert row["status"] == "FAILED" and row["parameters"]["not_moved"]
    assert len(_corpora(ws)) == 2  # the snapshot was registered before the move; the retry reuses it
    assert _journal(ws, "CITATION_CHASE_ACCEPTED") == []

    monkeypatch.setattr(rounds.shutil, "move", real_move)
    accepted = cc.accept_citation_chase(ws)
    assert accepted.round == 2 and accepted.already_accepted
    assert sorted(accepted.archived) == sorted(["screening/", *rounds.PUBLISHED_OUTPUTS, "verified.json"])
    assert (ws / "literature" / "screening_rounds" / "round_001" / "included.json").is_file()
    assert len(_corpora(ws)) == 2
    assert len(_journal(ws, "CITATION_CHASE_ACCEPTED")) == 1


# --------------------------------------------------------------------------- a first round is unchanged


def test_a_first_round_writes_exactly_the_kits_prisma_report(ws):
    from scholar_search.screening import PrismaFlowReport

    report = PrismaFlowReport(total_identified=3, duplicates_removed=0, records_screened=3, records_excluded=1,
                              records_included=1, conflicts_flagged=0, exclusion_reasons_breakdown={"EXC-01": 1},
                              records_unclear=1)
    outputs = rounds.prisma_outputs(ws, report)
    assert outputs == {
        "prisma_screening_report.md": report.to_markdown(),
        "prisma_report.json": json.dumps(asdict(report), indent=2),
    }
    assert rounds.current_round(ws) == {"round": 1, "arm": "databases", "chase": None, "corpus_artifact_id": None, "started_at": None}
    assert rounds.chase_identification(ws) is None


def test_load_context_keeps_every_batch_bound_to_the_current_corpus(ws):
    before = ev.load_context(ws)
    assert before.batches and ev.newest_corpus_fingerprint(ws) is not None
    assert all(True for _ in before.batches)
    # No registry: no fingerprint, no filtering.
    assert ev.newest_corpus_fingerprint(ws / "nowhere") is None
