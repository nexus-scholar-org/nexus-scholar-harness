"""Proposals on an inception draft (M10b Part B, ``docs/ux/shared/final/01-proposals.md``).

A proposal is a change the engine suggests; nothing is applied without the
researcher's click. In M10b the only creator of an open proposal is a fixed
check (``CONCEPT_TERM_MISSING``: the 2026-11-13 title and questions said "UAV"
and no concept did). A draft save may carry ``accepted_from`` records of the
engine suggestions that exist today. Genesis writes the record to
``audit/proposals.jsonl``. Hermetic: the recon search seam replaces the providers.
"""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from test_recon_api import Seam, _probe

from scholar_harness.console import create_app
from scholar_harness.console.browser import POST_PATHS
from scholar_harness.inception import proposals, steps
from scholar_harness.inception.drafts import DraftStore

TOKEN = "desk-token"
BASE = "/api/v1/inception"
REPO = Path(__file__).resolve().parents[2]
ROUTE_TS = REPO / "apps" / "research-ui" / "app" / "api" / "console" / "[...path]" / "route.ts"


def uav_draft(**changes) -> dict:
    """A draft that compiles, whose title and question say UAV while no concept does."""
    draft = {
        "topic": "Weed detection from UAV imagery",
        "paradigm": "Positivist",
        "playbook": "PRISMA_SLR",
        "unit_of_analysis": "field trials",
        "rqs": ["How accurate is UAV weed detection in row crops?"],
        "concepts": [{"concept": "weed detection", "synonyms": ["weed mapping"]}],
        "extra_inclusions": ["Field studies with aerial imagery"],
        "extra_exclusions": [{"criterion": "Simulation only", "reason_category": "WRONG_REPORT_TYPE"}],
        "title": "UAV weed detection",
        "lead_researcher": "A. Researcher",
    }
    draft.update(changes)
    return draft


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.delenv("NEXUS_RECON_ROOT", raising=False)
    root = tmp_path / "root"
    root.mkdir()
    app = create_app(None, token=TOKEN, workspaces_root=root)
    app.state.recon_root = tmp_path / "recon"
    app.state.recon_search_fn = Seam()
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        yield client, root


def _create(client, draft: dict | None = None) -> dict:
    created = client.post(f"{BASE}/drafts", json={"draft": draft or uav_draft()})
    assert created.status_code == 201, created.text
    return created.json()


def _checks(client, sid: str, step: str | None = None) -> dict:
    answer = client.post(f"{BASE}/drafts/{sid}/checks", json={"step": step} if step else {})
    assert answer.status_code == 200, answer.text
    return answer.json()


def _term_proposal(client, sid: str) -> dict:
    body = _checks(client, sid, "criteria")
    row = next(c for c in body["checks"] if c["check_id"] == "CONCEPT_TERM_MISSING")
    assert row["action"]["kind"] == "proposal"
    listed = client.get(f"{BASE}/drafts/{sid}/proposals").json()["proposals"]
    return next(p for p in listed if p["proposal_id"] == row["action"]["proposal_id"])


def _record(root: Path, sid: str) -> dict:
    return json.loads((root / ".drafts" / sid / "draft.json").read_text(encoding="utf-8"))


def test_a_check_proposes_uav_and_apply_writes_the_draft_and_the_decision_in_one_write(env):
    client, root = env
    record = _create(client)
    sid = record["session_id"]
    proposal = _term_proposal(client, sid)
    assert proposal["source"] == "check:CONCEPT_TERM_MISSING" and proposal["status"] == "open"
    assert proposal["target"] == {"kind": "draft", "id": sid, "field": "concepts"}
    assert proposal["op"] == "add" and proposal["value"] == {"concept": "UAV", "synonyms": []}
    assert proposal["step"] == "criteria" and proposal["decided_at"] is None
    # Recording the open proposal is a side write: the draft's updated_at is unchanged.
    assert _record(root, sid)["updated_at"] == record["updated_at"]

    applied = client.post(
        f"{BASE}/drafts/{sid}/proposals/{proposal['proposal_id']}/apply", json={"base_updated_at": record["updated_at"]},
    )
    assert applied.status_code == 200, applied.text
    body = applied.json()
    assert [c["concept"] for c in body["draft"]["concepts"]] == ["weed detection", "UAV"]
    assert body["updated_at"] != record["updated_at"]
    on_disk = _record(root, sid)
    assert on_disk["draft"] == body["draft"]
    stored = next(p for p in on_disk["proposals"] if p["proposal_id"] == proposal["proposal_id"])
    assert stored["status"] == "applied" and stored["decided_at"] and stored["decided_value"] == proposal["value"]
    # The check no longer fires once UAV is a concept, and re-running records nothing new.
    assert "CONCEPT_TERM_MISSING" not in [c["check_id"] for c in _checks(client, sid)["checks"]]


def test_rerunning_the_checks_records_the_same_proposal_once(env):
    client, root = env
    sid = _create(client)["session_id"]
    first = _term_proposal(client, sid)
    second = _term_proposal(client, sid)
    assert first["proposal_id"] == second["proposal_id"]
    assert len(_record(root, sid)["proposals"]) == 1


def test_the_id_is_content_derived_and_changes_with_the_base():
    draft = uav_draft()
    kw = {"source": "check:CONCEPT_TERM_MISSING", "field": "concepts", "op": "add", "value": {"concept": "UAV", "synonyms": []}, "why": "w"}
    a = proposals.make(draft_id="rec_" + "a" * 32, draft=draft, **kw)
    b = proposals.make(draft_id="rec_" + "a" * 32, draft=draft, **kw)
    c = proposals.make(draft_id="rec_" + "a" * 32, draft=uav_draft(concepts=[{"concept": "weeds", "synonyms": []}]), **kw)
    assert a["proposal_id"] == b["proposal_id"] != c["proposal_id"]
    assert re.fullmatch(r"prop_[0-9a-f]{12}", a["proposal_id"])


@pytest.mark.parametrize("source", ["agent:claude", "engine:pool_synonym", "chat:x", "check:", "nonsense"])
def test_only_a_check_or_an_import_creates_a_proposal(source):
    with pytest.raises(proposals.ProposalRefused) as exc:
        proposals.make(draft_id="rec_" + "a" * 32, draft=uav_draft(), source=source, field="topic", op="replace", value="x", why="")
    assert exc.value.code == "PROPOSAL_SOURCE_REFUSED" and exc.value.status == 422


@pytest.mark.parametrize(("field", "op"), [("nonsense", "add"), ("topic", "add"), ("title", "remove"), ("rqs", "merge")])
def test_a_target_the_draft_does_not_have_is_refused(field, op):
    with pytest.raises(proposals.ProposalRefused) as exc:
        proposals.make(draft_id="rec_" + "a" * 32, draft=uav_draft(), source="check:X", field=field, op=op, value="x", why="")
    assert exc.value.code == "PROPOSAL_TARGET_UNSUPPORTED"


def test_a_save_keeps_the_proposals_and_an_edited_target_makes_the_card_stale(env):
    client, root = env
    record = _create(client)
    sid = record["session_id"]
    proposal = _term_proposal(client, sid)
    edited = uav_draft(concepts=[{"concept": "weed detection", "synonyms": ["weed mapping"]}, {"concept": "drones", "synonyms": []}])
    saved = client.put(f"{BASE}/drafts/{sid}", json={"draft": edited, "base_updated_at": record["updated_at"]})
    assert saved.status_code == 200, saved.text
    assert [p["proposal_id"] for p in _record(root, sid)["proposals"]] == [proposal["proposal_id"]]
    listed = client.get(f"{BASE}/drafts/{sid}/proposals").json()
    stale = listed["proposals"][0]
    assert stale["status"] == "stale" and stale["current"] == "weed detection, drones"
    assert stale["base"]["shown"] == "weed detection"
    assert listed["by_step"]["criteria"] == {"open": 0, "stale": 1}
    refused = client.post(
        f"{BASE}/drafts/{sid}/proposals/{proposal['proposal_id']}/apply", json={"base_updated_at": saved.json()["updated_at"]},
    )
    assert refused.status_code == 409 and refused.json()["detail"]["code"] == "PROPOSAL_STALE"
    assert refused.json()["detail"]["details"] == {"base": "weed detection", "current": "weed detection, drones"}
    # A stale card can be dismissed (rejected), never applied.
    rejected = client.post(f"{BASE}/drafts/{sid}/proposals/{proposal['proposal_id']}/reject", json={})
    assert rejected.status_code == 200, rejected.text


def test_apply_and_apply_edited_refuse_a_stale_base_updated_at(env):
    client, _root = env
    record = _create(client)
    sid = record["session_id"]
    proposal = _term_proposal(client, sid)
    for path, extra in (("apply", {}), ("apply-edited", {"value": {"concept": "UAS", "synonyms": []}})):
        refused = client.post(
            f"{BASE}/drafts/{sid}/proposals/{proposal['proposal_id']}/{path}", json={"base_updated_at": "1999-01-01", **extra},
        )
        assert refused.status_code == 409 and refused.json()["detail"]["code"] == "DRAFT_CONFLICT"


def test_apply_edited_writes_the_researchers_value(env):
    client, root = env
    record = _create(client)
    sid = record["session_id"]
    proposal = _term_proposal(client, sid)
    mine = {"concept": "unmanned aerial vehicle", "synonyms": ["UAV", "drone"]}
    applied = client.post(
        f"{BASE}/drafts/{sid}/proposals/{proposal['proposal_id']}/apply-edited",
        json={"base_updated_at": record["updated_at"], "value": mine},
    )
    assert applied.status_code == 200, applied.text
    assert applied.json()["draft"]["concepts"][-1] == mine
    stored = _record(root, sid)["proposals"][0]
    assert stored["status"] == "applied_edited" and stored["decided_value"] == mine


def test_apply_goes_through_the_same_validation_as_a_save(env):
    client, root = env
    record = _create(client)
    sid = record["session_id"]
    proposal = _term_proposal(client, sid)
    too_long = client.post(
        f"{BASE}/drafts/{sid}/proposals/{proposal['proposal_id']}/apply-edited",
        json={"base_updated_at": record["updated_at"], "value": {"concept": "x" * (steps.MAX_NAME_CHARS + 1), "synonyms": []}},
    )
    assert too_long.status_code == 422 and too_long.json()["detail"]["code"] == "DRAFT_TOO_LARGE"
    bad = client.post(
        f"{BASE}/drafts/{sid}/proposals/{proposal['proposal_id']}/apply-edited",
        json={"base_updated_at": record["updated_at"], "value": {"name": "not a concept"}},
    )
    assert bad.status_code == 422 and bad.json()["detail"]["code"] == "DRAFT_INVALID"
    # Nothing was written by the refused applies.
    on_disk = _record(root, sid)
    assert on_disk["updated_at"] == record["updated_at"] and on_disk["proposals"][0]["status"] == "open"


def test_reject_changes_no_field_and_restore_returns_it_to_open(env):
    client, root = env
    record = _create(client)
    sid = record["session_id"]
    proposal = _term_proposal(client, sid)
    pid = proposal["proposal_id"]
    rejected = client.post(f"{BASE}/drafts/{sid}/proposals/{pid}/reject", json={"reason": "UAV is in the title only"})
    assert rejected.status_code == 200
    on_disk = _record(root, sid)
    assert on_disk["draft"] == record["draft"] and on_disk["updated_at"] == record["updated_at"]
    assert on_disk["proposals"][0]["status"] == "rejected" and on_disk["proposals"][0]["reason"] == "UAV is in the title only"
    again = client.post(f"{BASE}/drafts/{sid}/proposals/{pid}/reject", json={})
    assert again.status_code == 409 and again.json()["detail"] == {
        "code": "PROPOSAL_NOT_OPEN", "message": "this suggestion is rejected", "details": {"status": "rejected"},
    }
    restored = client.post(f"{BASE}/drafts/{sid}/proposals/{pid}/restore", json={})
    assert restored.status_code == 200 and _record(root, sid)["proposals"][0]["status"] == "open"
    assert _record(root, sid)["updated_at"] == record["updated_at"]
    # An applied proposal is not restored: the researcher edits the field instead.
    client.post(f"{BASE}/drafts/{sid}/proposals/{pid}/apply", json={"base_updated_at": record["updated_at"]})
    refused = client.post(f"{BASE}/drafts/{sid}/proposals/{pid}/restore", json={})
    assert refused.status_code == 409 and refused.json()["detail"]["code"] == "PROPOSAL_NOT_OPEN"
    missing = client.post(f"{BASE}/drafts/{sid}/proposals/prop_000000000000/reject", json={})
    assert missing.status_code == 404 and missing.json()["detail"]["code"] == "PROPOSAL_NOT_FOUND"


def test_a_side_write_between_another_tabs_read_and_save_keeps_both(env):
    """Reject, restore, a dismissal and a step mark leave ``updated_at`` alone (01-proposals, decided 2026-11-18)."""
    client, root = env
    tab_a = _create(client)
    sid = tab_a["session_id"]
    pid = _term_proposal(client, sid)["proposal_id"]
    client.post(f"{BASE}/drafts/{sid}/proposals/{pid}/reject", json={})
    seeds = _checks(client, sid, "direction")
    note = next(c for c in seeds["checks"] if c["check_id"] == "DIRECTION_SEEDS_FEW")
    dismissed = client.post(f"{BASE}/drafts/{sid}/checks/DIRECTION_SEEDS_FEW/dismiss", json={"evidence_digest": note["evidence_digest"]})
    assert dismissed.status_code == 200, dismissed.text
    # Tab A saves with the updated_at it read before both side writes.
    saved = client.put(f"{BASE}/drafts/{sid}", json={"draft": {**tab_a["draft"], "venue": "a journal"}, "base_updated_at": tab_a["updated_at"]})
    assert saved.status_code == 200, saved.text
    on_disk = _record(root, sid)
    assert on_disk["draft"]["venue"] == "a journal"
    assert on_disk["proposals"][0]["status"] == "rejected"
    assert [d["check_id"] for d in on_disk["check_dismissals"]] == ["DIRECTION_SEEDS_FEW"]


def test_side_writes_racing_saves_lose_nothing(tmp_path):
    """Under the draft lock, interleaved side writes and saves keep every change (threads, as FastAPI runs them)."""
    store = DraftStore(tmp_path)
    sid = store.create(uav_draft())["session_id"]

    def mark(i: int) -> None:
        store.transact(sid, lambda r: r.setdefault("check_dismissals", []).append({"i": i}), answer=False)

    def save(i: int) -> None:
        store.save(sid, uav_draft(venue=f"v{i}"))

    threads = [threading.Thread(target=f, args=(i,)) for i in range(20) for f in (mark, save)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    record = store.load(sid)
    assert sorted(d["i"] for d in record["check_dismissals"]) == list(range(20))
    assert record["draft"]["venue"].startswith("v")


def test_proposal_writes_are_refused_after_genesis(env):
    client, _root = env
    record = _create(client)
    sid = record["session_id"]
    pid = _term_proposal(client, sid)["proposal_id"]
    assert client.post(f"{BASE}/drafts/{sid}/genesis", json={}).status_code == 201
    refused = client.post(f"{BASE}/drafts/{sid}/proposals/{pid}/reject", json={})
    assert refused.status_code == 409 and refused.json()["detail"]["code"] == "DRAFT_EMITTED"


# --- accepted_from: the six mechanisms that exist today (R1) ------------------


def _pool_draft(client) -> tuple[str, dict, dict]:
    """A draft with a probed pool; answers the draft record and one pool synonym it offers."""
    record = _create(client, uav_draft(concepts=[{"concept": "weed detection", "synonyms": []}, {"concept": "on-device inference"}]))
    sid = record["session_id"]
    _probe(client, sid)
    record = client.get(f"{BASE}/drafts/{sid}").json()
    report = client.get(f"{BASE}/drafts/{sid}/recon/concepts").json()
    offered = next(s["term"] for c in report["concepts"] if c["concept"] == "weed detection" for s in c["suggestions"])
    return sid, record, {"mechanism": "pool_synonym", "field": "concepts[weed detection].synonyms", "value": offered}


def _with_synonym(draft: dict, term: str) -> dict:
    concepts = [dict(c) for c in draft["concepts"]]
    concepts[0] = {**concepts[0], "synonyms": [*concepts[0].get("synonyms", []), term]}
    return {**draft, "concepts": concepts}


def test_accepted_synonym_is_recorded_although_no_longer_offered_after_the_save(env):
    """The reproducing case: after the save ``concept_report`` no longer offers the term, so the
    engine must judge the entry on the stored draft, before the save."""
    client, root = env
    sid, record, entry = _pool_draft(client)
    draft = _with_synonym(record["draft"], entry["value"])
    saved = client.put(f"{BASE}/drafts/{sid}", json={"draft": draft, "base_updated_at": record["updated_at"], "accepted_from": [entry]})
    assert saved.status_code == 200, saved.text
    assert saved.json()["not_recorded"] == []
    after = client.get(f"{BASE}/drafts/{sid}/recon/concepts").json()
    assert entry["value"] not in [s["term"] for c in after["concepts"] for s in c["suggestions"]]
    kept = [p for p in _record(root, sid)["proposals"] if p["source"] == "engine:pool_synonym"]
    assert len(kept) == 1
    assert kept[0]["status"] == "applied" and kept[0]["value"] == entry["value"] and kept[0]["op"] == "add"
    # Records are listed as decided, never as open cards.
    listed = client.get(f"{BASE}/drafts/{sid}/proposals").json()
    assert listed["by_step"]["criteria"] == {"open": 0, "stale": 0}
    # A second save with the same entry is a no-op.
    again = client.put(f"{BASE}/drafts/{sid}", json={"draft": draft, "base_updated_at": saved.json()["updated_at"], "accepted_from": [entry]})
    assert again.status_code == 200
    assert len([p for p in _record(root, sid)["proposals"] if p["source"] == "engine:pool_synonym"]) == 1


def test_a_value_the_mechanism_did_not_offer_is_saved_but_not_recorded(env):
    client, root = env
    sid, record, entry = _pool_draft(client)
    edited = {**entry, "value": entry["value"] + "s"}  # the researcher changed the word before ticking
    draft = _with_synonym(record["draft"], edited["value"])
    saved = client.put(f"{BASE}/drafts/{sid}", json={"draft": draft, "base_updated_at": record["updated_at"], "accepted_from": [edited]})
    assert saved.status_code == 200, saved.text
    assert saved.json()["not_recorded"] == [edited]
    assert saved.json()["draft"] == draft
    assert not [p for p in _record(root, sid).get("proposals", []) if p["source"].startswith("engine:")]


def test_wizard_criterion_and_matrix_column_are_recorded_with_the_save(env):
    client, root = env
    record = _create(client, uav_draft(proof="field-validated accuracy"))
    sid = record["session_id"]
    criteria = client.post(f"{BASE}/steps/criteria", json={"draft": record["draft"]}).json()
    wizard = next(c for c in criteria["criteria"] if c["generated"])
    column = client.post(f"{BASE}/steps/matrix", json={"draft": record["draft"]}).json()["columns"][0]["name"]
    draft = {**record["draft"], "criteria_decisions": {wizard["id"]: True}, "matrix_columns": [column]}
    saved = client.put(f"{BASE}/drafts/{sid}", json={
        "draft": draft, "base_updated_at": record["updated_at"],
        "accepted_from": [
            {"mechanism": "wizard_criterion", "field": "criteria_decisions", "value": wizard["id"]},
            {"mechanism": "matrix_column", "field": "matrix_columns", "value": column},
            {"mechanism": "matrix_column", "field": "matrix_columns", "value": "A column nobody offered"},
        ],
    })
    assert saved.status_code == 200, saved.text
    assert saved.json()["not_recorded"] == [{"mechanism": "matrix_column", "field": "matrix_columns", "value": "A column nobody offered"}]
    assert sorted(p["source"] for p in _record(root, sid)["proposals"]) == ["engine:matrix_column", "engine:wizard_criterion"]


def test_an_unknown_mechanism_is_body_invalid(env):
    client, _root = env
    record = _create(client)
    refused = client.put(f"{BASE}/drafts/{record['session_id']}", json={
        "draft": record["draft"], "accepted_from": [{"mechanism": "agent", "field": "concepts", "value": "x"}],
    })
    assert refused.status_code == 422 and refused.json()["detail"]["code"] == "BODY_INVALID"


def test_a_chosen_direction_is_recorded_by_the_bind(env):
    client, root = env
    record = _create(client, uav_draft(concepts=[{"concept": "weed detection", "synonyms": []}]))
    sid = record["session_id"]
    _probe(client, sid)
    label = client.get(f"{BASE}/drafts/{sid}/recon/directions").json()["directions"][0]["label"]
    bound = client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"direction": label, "accept_thin_pool": True})
    assert bound.status_code == 200, bound.text
    kept = [p for p in _record(root, sid)["proposals"] if p["source"] == "engine:direction"]
    assert len(kept) == 1 and kept[0]["value"] == label and kept[0]["op"] == "replace" and kept[0]["step"] == "direction"


# --- genesis: audit/proposals.jsonl ------------------------------------------


def _lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _journal(ws: Path) -> list[dict]:
    return _lines(ws / "audit" / "journal.jsonl")


def test_genesis_writes_an_empty_record_for_a_draft_without_proposals(env):
    client, root = env
    sid = _create(client, uav_draft(title="Weed detection review", rqs=["How accurate is weed detection?"]))["session_id"]
    preview = client.post(f"{BASE}/preview", json={"draft": client.get(f"{BASE}/drafts/{sid}").json()["draft"]}).json()
    assert "audit/proposals.jsonl" in preview["files"] and "audit/check_dismissals.jsonl" in preview["files"]
    created = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert created.status_code == 201, created.text
    ws = Path(created.json()["path"])
    assert (ws / "audit" / "proposals.jsonl").read_text(encoding="utf-8") == ""
    row = next(e for e in _journal(ws) if e["action"] == "PROPOSALS_RECORDED")
    assert row["parameters"]["proposed"] == 0 and row["outputs"] == ["audit/proposals.jsonl"]


def test_genesis_records_each_decision_and_whether_it_is_in_the_protocol(env):
    client, root = env
    record = _create(client)
    sid = record["session_id"]
    pid = _term_proposal(client, sid)["proposal_id"]
    applied = client.post(f"{BASE}/drafts/{sid}/proposals/{pid}/apply", json={"base_updated_at": record["updated_at"]}).json()
    # The researcher later edits the applied concept away.
    edited = {**applied["draft"], "concepts": [{"concept": "weed detection", "synonyms": ["weed mapping", "UAV"]}]}
    client.put(f"{BASE}/drafts/{sid}", json={"draft": edited, "base_updated_at": applied["updated_at"]})
    created = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert created.status_code == 201, created.text
    ws = Path(created.json()["path"])
    lines = _lines(ws / "audit" / "proposals.jsonl")
    assert [line["event"] for line in lines] == ["proposed", "applied"]
    assert lines[0]["proposal_id"] == pid and lines[0]["source"] == "check:CONCEPT_TERM_MISSING"
    assert lines[1]["in_protocol"] is False  # applied, then edited away
    row = next(e for e in _journal(ws) if e["action"] == "PROPOSALS_RECORDED")
    assert row["parameters"]["by_status"]["applied"] == 1 and row["parameters"]["in_protocol"] == 0


def test_a_genesis_that_fails_after_the_record_leaves_no_workspace(env, monkeypatch):
    client, root = env
    sid = _create(client)["session_id"]

    def boom(target):
        assert (Path(target) / "audit" / "proposals.jsonl").exists()
        raise OSError("disk full")

    monkeypatch.setattr(steps, "install_workspace_support_files", boom)
    refused = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert refused.status_code == 409 and refused.json()["detail"]["code"] == "WORKSPACE_ROOT_UNAVAILABLE"
    assert not (root / "uav-weed-detection").exists()


def test_a_replacement_archives_the_old_record_and_writes_a_new_one(env):
    client, root = env
    first = _create(client)
    sid = first["session_id"]
    pid = _term_proposal(client, sid)["proposal_id"]
    client.post(f"{BASE}/drafts/{sid}/proposals/{pid}/reject", json={"reason": "in the title only"})
    ws = Path(client.post(f"{BASE}/drafts/{sid}/genesis", json={}).json()["path"])
    old = (ws / "audit" / "proposals.jsonl").read_text(encoding="utf-8")
    assert _lines(ws / "audit" / "proposals.jsonl")[-1] == {**_lines(ws / "audit" / "proposals.jsonl")[-1], "event": "rejected", "reason": "in the title only"}
    second = _create(client)["session_id"]
    replaced = client.post(f"{BASE}/drafts/{second}/genesis", json={"replace": True})
    assert replaced.status_code == 201, replaced.text
    backup = Path(replaced.json()["backup_dir"])
    assert (backup / "audit" / "proposals.jsonl").read_text(encoding="utf-8") == old
    assert (ws / "audit" / "proposals.jsonl").read_text(encoding="utf-8") == ""
    assert "audit/proposals.jsonl" in replaced.json()["archived"]


def test_the_four_decision_routes_are_in_both_allow_lists():
    ts = ROUTE_TS.read_text(encoding="utf-8")
    for action in ("apply", "apply-edited", "reject", "restore"):
        path = f"api/v1/inception/drafts/rec_{'a' * 32}/proposals/prop_0123456789ab/{action}"
        assert any(p.fullmatch(path) for p in POST_PATHS), path
    assert "proposals\\/prop_[0-9a-f]+\\/(apply|apply-edited|reject|restore)$/" in ts
