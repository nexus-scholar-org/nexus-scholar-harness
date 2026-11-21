"""Fixed checks on an inception draft (M10b Part B, ``docs/ux/shared/final/02-checks.md``).

Each check is arithmetic or a string test on data the engine holds; no
language model. The background failures of the strict run of 2026-11-13 each
have a case here: two databases answered with no papers and the screen said
they answered; the sample came almost entirely from one database; the title
and the questions said "UAV" and no concept did; every exclusion carried
``OUT_OF_SCOPE``. Hermetic: pools are written straight into the recon cache
through the console's search seam.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from scholar_search.models import Document, ExternalIds, SearchLeg, SearchRun
from test_inception_proposals import uav_draft
from test_recon_api import _probe

from scholar_harness.console import create_app
from scholar_harness.console.browser import POST_PATHS
from scholar_harness.inception import checks, steps
from scholar_harness.inception.intent import CriterionDraft

TOKEN = "desk-token"
BASE = "/api/v1/inception"
REPO = Path(__file__).resolve().parents[2]


class PoolSeam:
    """A search seam answering a fixed set of records per database, with each leg's status."""

    def __init__(self, per_db: dict[str, int], failed: tuple[str, ...] = ()):
        self.per_db, self.failed = per_db, failed

    def __call__(self, query, providers):
        docs, legs = [], []
        for db in providers:
            n = 0 if db in self.failed else self.per_db.get(db, 0)
            for i in range(n):
                docs.append(Document(
                    title=f"Weed detection with UAV imagery {db} {i}", year=2023, provider=db,
                    provider_id=f"{db}-{i}", external_ids=ExternalIds(doi=f"10.1/{db}.{i}"),
                    abstract="weed detection from unmanned aerial imagery in crop rows",
                ))
            legs.append(SearchLeg(
                provider=db, query_id=query.id, status="failed" if db in self.failed else "ok", fetched=n,
                error="HTTPStatusError: 429" if db in self.failed else None,
            ))
        return SearchRun(documents=docs, legs=legs)


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.delenv("NEXUS_RECON_ROOT", raising=False)
    root = tmp_path / "root"
    root.mkdir()
    app = create_app(None, token=TOKEN, workspaces_root=root)
    app.state.recon_root = tmp_path / "recon"
    app.state.recon_search_fn = PoolSeam({"openalex": 25})
    with TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        yield client, app, root


def _create(client, draft: dict | None = None) -> dict:
    created = client.post(f"{BASE}/drafts", json={"draft": draft or uav_draft()})
    assert created.status_code == 201, created.text
    return created.json()


def _checks(client, sid: str, step: str | None = None) -> dict:
    answer = client.post(f"{BASE}/drafts/{sid}/checks", json={"step": step} if step else {})
    assert answer.status_code == 200, answer.text
    return answer.json()


def _ids(body: dict) -> list[str]:
    return [c["check_id"] for c in body["checks"]]


def _one(body: dict, check_id: str, subject: str = "") -> dict:
    return next(c for c in body["checks"] if c["check_id"] == check_id and c["subject"] == subject)


def _probed(client, app, per_db: dict[str, int], failed: tuple[str, ...] = (), draft: dict | None = None) -> str:
    app.state.recon_search_fn = PoolSeam(per_db, failed)
    sid = _create(client, draft)["session_id"]
    _probe(client, sid, databases=list(per_db), refresh=True)
    return sid


def test_no_check_reads_the_topic_length(env):
    client, _app, _root = env
    topic = " ".join(["word"] * 19)
    body = _checks(client, _create(client, uav_draft(topic=topic))["session_id"], "scope")
    assert [c for c in body["checks"] if c["level"] == "warning"] == []


def test_explore_database_empty_not_called_answered(env):
    client, app, _root = env
    sid = _probed(client, app, {"openalex": 25, "crossref": 0, "semanticscholar": 0})
    body = _checks(client, sid, "explore")
    empty = [c for c in body["checks"] if c["check_id"] == "EXPLORE_DATABASE_EMPTY"]
    assert sorted(c["subject"] for c in empty) == ["crossref", "semanticscholar"]
    assert all(c["level"] == "warning" and c["action"] == {"kind": "field", "step": "scope", "field": "topic",
                                                         "label_key": "checks.EXPLORE_DATABASE_EMPTY.action"} for c in empty)
    assert empty[0]["message"] == "crossref answered with no papers, while others found some."
    # Every database fetched something: no row.
    sid = _probed(client, app, {"openalex": 13, "crossref": 12})
    assert "EXPLORE_DATABASE_EMPTY" not in _ids(_checks(client, sid, "explore"))


def test_a_failed_database_is_a_warning_and_the_pool_is_marked_partial(env):
    client, app, _root = env
    sid = _probed(client, app, {"openalex": 25, "crossref": 5}, failed=("crossref",))
    body = _checks(client, sid, "explore")
    failed = _one(body, "EXPLORE_DATABASE_FAILED", "crossref")
    assert failed["level"] == "warning" and failed["params"]["database"] == "crossref"
    assert body["partial"] == [{"kind": "pool_partial", "databases": ["crossref"]}]


def test_explore_sample_one_source(env):
    client, app, _root = env
    sid = _probed(client, app, {"openalex": 24, "crossref": 1})
    row = _one(_checks(client, sid, "explore"), "EXPLORE_SAMPLE_ONE_SOURCE")
    assert row["params"] == {"share": "96%", "n": 25, "database": "openalex"}
    assert row["threshold"]["value"] == checks.ONE_SOURCE_SHARE
    sid = _probed(client, app, {"openalex": 13, "crossref": 12})
    assert "EXPLORE_SAMPLE_ONE_SOURCE" not in _ids(_checks(client, sid, "explore"))
    sid = _probed(client, app, {"openalex": 25})
    assert "EXPLORE_SAMPLE_ONE_SOURCE" not in _ids(_checks(client, sid, "explore"))


def test_a_thin_pool_and_a_changed_scope_are_warnings(env):
    client, app, _root = env
    sid = _probed(client, app, {"openalex": 5})
    body = _checks(client, sid, "explore")
    assert _one(body, "EXPLORE_POOL_THIN")["params"] == {"n": 5, "floor": 12}
    record = client.get(f"{BASE}/drafts/{sid}").json()
    client.put(f"{BASE}/drafts/{sid}", json={"draft": {**record["draft"], "start_year": 2015}})
    assert "EXPLORE_SCOPE_CHANGED" in _ids(_checks(client, sid, "explore"))


def test_explore_checks_wait_for_the_first_search(env):
    client, _app, _root = env
    body = _checks(client, _create(client)["session_id"], "explore")
    assert body["checks"] == []
    assert {w["check_id"] for w in body["waiting"]} >= {"EXPLORE_DATABASE_EMPTY", "EXPLORE_SAMPLE_ONE_SOURCE"}
    assert {w["needs"] for w in body["waiting"]} == {"pool"}


def test_concept_term_missing_uav(env):
    client, _app, _root = env
    body = _checks(client, _create(client)["session_id"], "criteria")
    row = _one(body, "CONCEPT_TERM_MISSING", "UAV")
    assert row["level"] == "warning" and row["action"]["kind"] == "proposal"
    # The first run already counts the suggestion it recorded.
    sid = _create(client)["session_id"]
    first = _checks(client, sid)
    assert _one(first, "REVIEW_PROPOSALS_OPEN")["params"] == {"n": 1}
    # With "unmanned aerial vehicle" the proposal is a synonym of it.
    draft = uav_draft(concepts=[{"concept": "weed detection"}, {"concept": "unmanned aerial vehicle"}])
    sid = _create(client, draft)["session_id"]
    pid = _one(_checks(client, sid, "criteria"), "CONCEPT_TERM_MISSING", "UAV")["action"]["proposal_id"]
    proposal = next(p for p in client.get(f"{BASE}/drafts/{sid}/proposals").json()["proposals"] if p["proposal_id"] == pid)
    assert proposal["target"]["field"] == "concepts[unmanned aerial vehicle].synonyms" and proposal["value"] == "UAV"
    # With UAV already a synonym: no row.
    draft = uav_draft(concepts=[{"concept": "weed detection"}, {"concept": "unmanned aerial vehicle", "synonyms": ["UAV"]}])
    assert "CONCEPT_TERM_MISSING" not in _ids(_checks(client, _create(client, draft)["session_id"], "criteria"))


def test_only_acronyms_are_salient_after_calibration():
    """Decision item 27 (proposed): on the golden UAV protocols the title-word rule flagged only the
    review's outcomes ("reliability", "generalization"); the acronym rule keeps the 2026-11-13 case."""
    draft = steps.parse_draft(uav_draft(
        topic="Spectral weed detection", title="Spectral indices for the detection of weeds with NDVI",
        rqs=["Which spectral indices detect weeds best?"], concepts=[{"concept": "weeds"}],
    ))
    assert [t["term"] for t in checks._term_missing(draft)] == ["NDVI"]
    golden = steps.parse_draft(uav_draft(
        title="Reliability and Generalization in UAV Crop-Weed Mapping: A Scoping Review",
        rqs=["How do UAV crop-weed mapping studies define and evaluate reliability?"],
        concepts=[{"concept": "UAV"}, {"concept": "weed"}, {"concept": "mapping"}],
    ))
    assert checks._term_missing(golden) == []


def test_criteria_reasons_uniform(env):
    client, _app, _root = env
    two_same = uav_draft(extra_exclusions=[
        {"criterion": "Simulation only", "reason_category": "OUT_OF_SCOPE"},
        {"criterion": "Greenhouse only", "reason_category": "OUT_OF_SCOPE"},
    ])
    row = _one(_checks(client, _create(client, two_same)["session_id"], "criteria"), "CRITERIA_REASONS_UNIFORM")
    assert row["params"] == {"n": 2, "code": "OUT_OF_SCOPE"}
    two_different = uav_draft(extra_exclusions=[
        {"criterion": "Simulation only", "reason_category": "WRONG_REPORT_TYPE"},
        {"criterion": "Greenhouse only", "reason_category": "OUT_OF_SCOPE"},
    ])
    for draft in (two_different, uav_draft()):
        assert "CRITERIA_REASONS_UNIFORM" not in _ids(_checks(client, _create(client, draft)["session_id"], "criteria"))


def _drop_wizard(draft: dict) -> dict:
    """Every wizard-written criterion dropped, so the draft's only blocker is the missing side."""
    items = steps.criteria_with_decisions(steps.parse_draft(draft))
    return {**draft, "criteria_decisions": {i["id"]: False for i in items if i["generated"]}}


BLOCKER_DRAFTS = {
    "SCOPE_TOPIC_MISSING": uav_draft(topic=""),
    "SHAPE_REQUIRED_MISSING": uav_draft(unit_of_analysis=""),
    "CONCEPTS_NONE": uav_draft(concepts=[]),
    # H-run-small-fixes: an out-of-scope item waiting for Accept (the proof beside a typed inclusion writes none).
    "CRITERIA_UNDECIDED": uav_draft(out_of_scope=["Satellite imagery"]),
    "CRITERIA_SIDE_MISSING": _drop_wizard(uav_draft(extra_exclusions=[])),
    "REVIEW_PROJECT_MISSING": uav_draft(lead_researcher=""),
    "REVIEW_TITLE_NOT_A_FOLDER": uav_draft(title="!!!"),
}


def test_the_compiler_blocker_names_intent_invalid(env, monkeypatch):
    """No draft that passes the draft rules makes the compiler refuse today, so the refusal is forced."""
    from pydantic import BaseModel

    class Strict(BaseModel):
        n: int

    def refuse(intent):
        Strict.model_validate({"n": "x"})

    client, _app, _root = env
    monkeypatch.setattr(steps, "compile_intent", refuse)
    body = _checks(client, _create(client)["session_id"], "review")
    row = _one(body, "REVIEW_COMPILER_REFUSED")
    assert row["level"] == "blocker" and row["refusal"] == "INTENT_INVALID" and body["ready"] is False
    with pytest.raises(steps.StepRefused) as exc:
        steps.preview(uav_draft())
    assert exc.value.code == "INTENT_INVALID"


@pytest.mark.parametrize("check_id", sorted(BLOCKER_DRAFTS))
def test_blockers_name_existing_refusals(env, check_id):
    client, _app, root = env
    draft = BLOCKER_DRAFTS[check_id]
    body = _checks(client, _create(client, draft)["session_id"])
    row = next(c for c in body["checks"] if c["check_id"] == check_id)
    assert row["level"] == "blocker" and not row["dismissible"] and body["ready"] is False
    with pytest.raises(steps.StepRefused) as exc:
        steps.preview(draft, workspaces_root=root)
    assert [c["check_id"] for c in body["checks"] if c["level"] == "blocker"] == [check_id]  # one blocker per draft
    assert row["refusal"] == exc.value.code


def test_the_target_checks_name_the_genesis_refusal_and_the_gate(env):
    client, _app, root = env
    (root / "uav-weed-detection").mkdir()
    (root / "uav-weed-detection" / "notes.txt").write_text("not a workspace", encoding="utf-8")
    body = _checks(client, _create(client)["session_id"], "review")
    row = _one(body, "REVIEW_TARGET_NOT_WORKSPACE")
    assert row["refusal"] == "WORKSPACE_EXISTS" and body["ready"] is False


def test_a_draft_the_engine_accepts_has_no_blocker_and_is_ready(env):
    client, _app, root = env
    sid = _create(client)["session_id"]
    body = _checks(client, sid)
    assert [c for c in body["checks"] if c["level"] == "blocker"] == []
    assert body["ready"] is True
    assert steps.preview(client.get(f"{BASE}/drafts/{sid}").json()["draft"], workspaces_root=root)
    assert set(body["by_step"]) == set(checks.INCEPTION_STEPS)
    assert body["shape"] == "checks-v1" and body["sources"] == ["check"]


def test_shape_planned_size_empty_is_a_note(env):
    client, _app, _root = env
    body = _checks(client, _create(client)["session_id"], "shape")
    row = _one(body, "SHAPE_PLANNED_SIZE_EMPTY")
    assert row["level"] == "note" and row["action"]["field"] == "pool_max" and row["dismissible"]
    stated = _checks(client, _create(client, uav_draft(pool_min=150, pool_max=300))["session_id"], "shape")
    assert "SHAPE_PLANNED_SIZE_EMPTY" not in _ids(stated)


def test_shape_proof_not_required_with_a_typed_inclusion(env):
    client, _app, _root = env
    assert "SHAPE_REQUIRED_MISSING" not in _ids(_checks(client, _create(client)["session_id"], "shape"))
    no_inclusion = uav_draft(extra_inclusions=[])
    row = _one(_checks(client, _create(client, no_inclusion)["session_id"], "shape"), "SHAPE_REQUIRED_MISSING")
    assert row["evidence"][0]["value"] == ["proof"] and row["action"]["field"] == "proof"


def test_the_wizard_draft_trips_the_undecided_blocker_with_the_first_row(env):
    client, _app, _root = env
    draft = uav_draft(proof="field-validated accuracy", extra_inclusions=[])
    proof_id = CriterionDraft("inclusion", "Reports the gold-standard proof — field-validated accuracy", "proof").id
    row = _one(_checks(client, _create(client, draft)["session_id"], "criteria"), "CRITERIA_UNDECIDED")
    assert row["params"] == {"n": 1} and row["action"]["criterion_id"] in (proof_id, row["action"]["criterion_id"])


def test_checks_describe_the_saved_draft(env):
    client, _app, _root = env
    record = _create(client, uav_draft(lead_researcher=""))
    body = _checks(client, record["session_id"], "review")
    assert body["scope"] == {"kind": "draft", "id": record["session_id"], "updated_at": record["updated_at"]}
    assert "REVIEW_PROJECT_MISSING" in _ids(body)


def test_checks_write_no_draft_field(env):
    client, _app, root = env
    record = _create(client)
    _checks(client, record["session_id"])
    on_disk = json.loads((root / ".drafts" / record["session_id"] / "draft.json").read_text(encoding="utf-8"))
    assert on_disk["draft"] == record["draft"] and on_disk["updated_at"] == record["updated_at"]


def test_one_broken_check_does_not_hide_the_others(env, monkeypatch):
    client, _app, _root = env

    def boom(draft):
        raise RuntimeError("broken")

    monkeypatch.setattr(checks, "_lexicon", boom)
    body = _checks(client, _create(client, uav_draft(lead_researcher=""))["session_id"])
    assert {"kind": "check_failed", "check_id": "SHAPE_LEXICON_WARNING", "error": "RuntimeError"} in body["partial"]
    assert "REVIEW_PROJECT_MISSING" in _ids(body)


def test_an_unknown_step_is_step_unknown(env):
    client, _app, _root = env
    sid = _create(client)["session_id"]
    refused = client.post(f"{BASE}/drafts/{sid}/checks", json={"step": "harvest"})
    assert refused.status_code == 404 and refused.json()["detail"]["code"] == "STEP_UNKNOWN"


# --- dismissal --------------------------------------------------------------


def _dismiss(client, sid: str, check_id: str, **body):
    return client.post(f"{BASE}/drafts/{sid}/checks/{check_id}/dismiss", json=body)


def test_dismiss_requires_reason_and_digest(env):
    client, _app, _root = env
    sid = _create(client)["session_id"]
    row = _one(_checks(client, sid, "criteria"), "CONCEPT_TERM_MISSING", "UAV")
    no_reason = _dismiss(client, sid, "CONCEPT_TERM_MISSING", subject="UAV", evidence_digest=row["evidence_digest"], reason="  ")
    assert no_reason.status_code == 422 and no_reason.json()["detail"]["code"] == "CHECK_REASON_REQUIRED"
    assert no_reason.json()["detail"]["details"] == {"limit": steps.MAX_TEXT_CHARS, "level": "warning"}
    too_long = _dismiss(client, sid, "CONCEPT_TERM_MISSING", subject="UAV", evidence_digest=row["evidence_digest"], reason="x" * 2001)
    assert too_long.json()["detail"]["code"] == "CHECK_REASON_REQUIRED"
    changed = _dismiss(client, sid, "CONCEPT_TERM_MISSING", subject="UAV", evidence_digest="sha256:old", reason="it is in the title only")
    assert changed.status_code == 409 and changed.json()["detail"]["code"] == "CHECK_CHANGED"
    assert changed.json()["detail"]["details"]["current"]["check_id"] == "CONCEPT_TERM_MISSING"
    missing = _dismiss(client, sid, "CONCEPT_TERM_MISSING", subject="LIDAR", evidence_digest="x", reason="r")
    assert missing.status_code == 404 and missing.json()["detail"]["code"] == "CHECK_NOT_FOUND"
    ok = _dismiss(client, sid, "CONCEPT_TERM_MISSING", subject="UAV", evidence_digest=row["evidence_digest"], reason="it is in the title only")
    assert ok.status_code == 200, ok.text
    after = _one(ok.json(), "CONCEPT_TERM_MISSING", "UAV")
    assert after["status"] == "dismissed" and after["dismissal"]["reason"] == "it is in the title only"
    assert ok.json()["counts"]["dismissed"] == 1


def test_note_dismissed_without_reason(env):
    client, _app, _root = env
    sid = _create(client)["session_id"]
    row = _one(_checks(client, sid, "shape"), "SHAPE_PLANNED_SIZE_EMPTY")
    ok = _dismiss(client, sid, "SHAPE_PLANNED_SIZE_EMPTY", evidence_digest=row["evidence_digest"])
    assert ok.status_code == 200 and _one(ok.json(), "SHAPE_PLANNED_SIZE_EMPTY")["dismissal"]["reason"] == ""


def test_blocker_not_dismissible(env):
    client, _app, root = env
    sid = _create(client, uav_draft(lead_researcher=""))["session_id"]
    row = _one(_checks(client, sid, "review"), "REVIEW_PROJECT_MISSING")
    refused = _dismiss(client, sid, "REVIEW_PROJECT_MISSING", evidence_digest=row["evidence_digest"], reason="later")
    assert refused.status_code == 409 and refused.json()["detail"] == {
        "code": "CHECK_NOT_DISMISSIBLE", "message": "this check cannot be dismissed",
        "details": {"level": "blocker", "refusal": "DRAFT_INCOMPLETE"},
    }
    # The gate warnings are answered by a confirmation, never dismissed.
    sid2 = _create(client)["session_id"]
    client.post(f"{BASE}/drafts/{sid2}/genesis", json={})
    sid3 = _create(client)["session_id"]
    row = _one(_checks(client, sid3, "review"), "REVIEW_TARGET_HAS_WORKSPACE")
    assert row["dismissible"] is False
    refused = _dismiss(client, sid3, "REVIEW_TARGET_HAS_WORKSPACE", evidence_digest=row["evidence_digest"], reason="I mean to")
    assert refused.json()["detail"]["code"] == "CHECK_NOT_DISMISSIBLE"


def test_dismissal_survives_put_and_does_not_bump_updated_at(env):
    client, _app, root = env
    record = _create(client)
    sid = record["session_id"]
    row = _one(_checks(client, sid, "shape"), "SHAPE_PLANNED_SIZE_EMPTY")
    _dismiss(client, sid, "SHAPE_PLANNED_SIZE_EMPTY", evidence_digest=row["evidence_digest"])
    on_disk = json.loads((root / ".drafts" / sid / "draft.json").read_text(encoding="utf-8"))
    assert on_disk["updated_at"] == record["updated_at"]
    saved = client.put(f"{BASE}/drafts/{sid}", json={"draft": {**record["draft"], "venue": "x"}, "base_updated_at": record["updated_at"]})
    assert saved.status_code == 200
    assert _one(_checks(client, sid, "shape"), "SHAPE_PLANNED_SIZE_EMPTY")["status"] == "dismissed"


def test_dismissal_reopens_when_evidence_changes(env):
    client, _app, _root = env
    record = _create(client, uav_draft(golden_seeds=["10.1/a"]))
    sid = record["session_id"]
    row = _one(_checks(client, sid, "direction"), "DIRECTION_SEEDS_FEW")
    _dismiss(client, sid, "DIRECTION_SEEDS_FEW", evidence_digest=row["evidence_digest"])
    client.put(f"{BASE}/drafts/{sid}", json={"draft": {**record["draft"], "golden_seeds": ["10.1/a", "10.1/b"]}})
    reopened = _one(_checks(client, sid, "direction"), "DIRECTION_SEEDS_FEW")
    assert reopened["status"] == "open" and reopened["dismissal"] is None
    assert reopened["previously_dismissed"]["at"]


def _dismiss_row(client, sid: str, row: dict) -> None:
    done = _dismiss(client, sid, row["check_id"], subject=row["subject"], evidence_digest=row["evidence_digest"], reason="seen")
    assert done.status_code == 200, done.text


def test_a_scope_dismissal_reopens_when_the_question_changes_again(env):
    """Review of Part B, finding 2: the digest holds the scope, not only the names of the changed parts."""
    client, app, _root = env
    sid = _probed(client, app, {"openalex": 25})
    record = client.get(f"{BASE}/drafts/{sid}").json()
    client.put(f"{BASE}/drafts/{sid}", json={"draft": {**record["draft"], "topic": "Weed detection from drones"}})
    _dismiss_row(client, sid, _one(_checks(client, sid, "explore"), "EXPLORE_SCOPE_CHANGED"))
    record = client.get(f"{BASE}/drafts/{sid}").json()
    client.put(f"{BASE}/drafts/{sid}", json={"draft": {**record["draft"], "topic": "Weed detection from satellites"}})
    row = _one(_checks(client, sid, "explore"), "EXPLORE_SCOPE_CHANGED")
    assert row["status"] == "open" and row["previously_dismissed"]


def test_a_concept_dismissal_reopens_when_its_terms_change(env):
    client, app, _root = env
    draft = uav_draft(concepts=[{"concept": "weed detection"}, {"concept": "hyperspectral"}])
    sid = _probed(client, app, {"openalex": 25}, draft=draft)
    _dismiss_row(client, sid, _one(_checks(client, sid, "criteria"), "CONCEPT_NOT_ANCHORED", "hyperspectral"))
    record = client.get(f"{BASE}/drafts/{sid}").json()
    concepts = [{"concept": "weed detection"}, {"concept": "hyperspectral", "synonyms": ["HSI"]}]
    client.put(f"{BASE}/drafts/{sid}", json={"draft": {**record["draft"], "concepts": concepts}})
    row = _one(_checks(client, sid, "criteria"), "CONCEPT_NOT_ANCHORED", "hyperspectral")
    assert row["status"] == "open" and row["previously_dismissed"]


def test_an_own_direction_dismissal_reopens_for_another_direction(env):
    client, app, _root = env
    sid = _probed(client, app, {"openalex": 25})
    bound = client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"own": "quantum sorting of seeds"})
    assert bound.status_code == 200, bound.text
    _dismiss_row(client, sid, _one(_checks(client, sid, "direction"), "DIRECTION_OWN_UNGROUNDED"))
    client.post(f"{BASE}/drafts/{sid}/recon/bind", json={"own": "robotic laser weeding"})
    row = _one(_checks(client, sid, "direction"), "DIRECTION_OWN_UNGROUNDED")
    assert row["status"] == "open" and row["previously_dismissed"]


def test_a_pool_dismissal_reopens_after_a_new_search(env):
    client, app, _root = env
    sid = _probed(client, app, {"openalex": 25, "crossref": 0})
    _dismiss_row(client, sid, _one(_checks(client, sid, "explore"), "EXPLORE_DATABASE_EMPTY", "crossref"))
    app.state.recon_search_fn = PoolSeam({"openalex": 20, "crossref": 0})
    _probe(client, sid, databases=["openalex", "crossref"], refresh=True)
    row = _one(_checks(client, sid, "explore"), "EXPLORE_DATABASE_EMPTY", "crossref")
    assert row["status"] == "open" and row["previously_dismissed"]


def test_restore(env):
    client, _app, root = env
    sid = _create(client)["session_id"]
    row = _one(_checks(client, sid, "shape"), "SHAPE_PLANNED_SIZE_EMPTY")
    not_dismissed = client.post(f"{BASE}/drafts/{sid}/checks/SHAPE_PLANNED_SIZE_EMPTY/restore", json={})
    assert not_dismissed.status_code == 409 and not_dismissed.json()["detail"]["code"] == "CHECK_NOT_DISMISSED"
    _dismiss(client, sid, "SHAPE_PLANNED_SIZE_EMPTY", evidence_digest=row["evidence_digest"])
    restored = client.post(f"{BASE}/drafts/{sid}/checks/SHAPE_PLANNED_SIZE_EMPTY/restore", json={})
    assert restored.status_code == 200 and _one(restored.json(), "SHAPE_PLANNED_SIZE_EMPTY")["status"] == "open"
    entries = json.loads((root / ".drafts" / sid / "draft.json").read_text(encoding="utf-8"))["check_dismissals"]
    assert [e["action"] for e in entries] == ["dismissed", "restored"]


def test_genesis_writes_check_dismissals_and_one_journal_row(env):
    client, _app, root = env
    sid = _create(client)["session_id"]
    row = _one(_checks(client, sid, "shape"), "SHAPE_PLANNED_SIZE_EMPTY")
    _dismiss(client, sid, "SHAPE_PLANNED_SIZE_EMPTY", evidence_digest=row["evidence_digest"])
    ws = Path(client.post(f"{BASE}/drafts/{sid}/genesis", json={}).json()["path"])
    lines = [json.loads(x) for x in (ws / "audit" / "check_dismissals.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [(x["check_id"], x["action"], x["carried_from"]) for x in lines] == [("SHAPE_PLANNED_SIZE_EMPTY", "dismissed", "draft")]
    journal = [json.loads(x) for x in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()]
    rows = [e for e in journal if e["action"] == "CHECK_DISMISSALS_RECORDED"]
    assert len(rows) == 1 and rows[0]["parameters"] == {"dismissed": 1, "restored": 0}
    # Empty for a draft with no dismissal.
    sid2 = _create(client, uav_draft(title="Weed detection review", rqs=["How accurate is weed detection?"]))["session_id"]
    ws2 = Path(client.post(f"{BASE}/drafts/{sid2}/genesis", json={}).json()["path"])
    assert (ws2 / "audit" / "check_dismissals.jsonl").read_text(encoding="utf-8") == ""


def test_preview_files_name_check_dismissals(env):
    client, _app, root = env
    files = client.post(f"{BASE}/preview", json={"draft": uav_draft()}).json()["files"]
    assert "audit/check_dismissals.jsonl" in files


def test_replacement_archives_check_dismissals(env):
    client, _app, root = env
    sid = _create(client)["session_id"]
    row = _one(_checks(client, sid, "shape"), "SHAPE_PLANNED_SIZE_EMPTY")
    _dismiss(client, sid, "SHAPE_PLANNED_SIZE_EMPTY", evidence_digest=row["evidence_digest"])
    ws = Path(client.post(f"{BASE}/drafts/{sid}/genesis", json={}).json()["path"])
    old = (ws / "audit" / "check_dismissals.jsonl").read_text(encoding="utf-8")
    replaced = client.post(f"{BASE}/drafts/{_create(client)['session_id']}/genesis", json={"replace": True}).json()
    assert (Path(replaced["backup_dir"]) / "audit" / "check_dismissals.jsonl").read_text(encoding="utf-8") == old
    assert (ws / "audit" / "check_dismissals.jsonl").read_text(encoding="utf-8") == ""


def test_an_imported_step_not_opened_is_a_note_on_review(env):
    client, _app, root = env
    record = _create(client)
    sid = record["session_id"]
    path = root / ".drafts" / sid / "draft.json"
    stored = json.loads(path.read_text(encoding="utf-8"))
    stored["origin"] = {"kind": "import", "checked": {"scope": True, "direction": True, "shape": False, "criteria": True, "review": True}}
    path.write_text(json.dumps(stored), encoding="utf-8")
    row = _one(_checks(client, sid, "review"), "REVIEW_IMPORT_STEP_NOT_OPENED", "shape")
    assert row["level"] == "note" and row["action"] == {"kind": "step", "step": "shape", "label_key": "checks.REVIEW_IMPORT_STEP_NOT_OPENED.action"}


def test_the_check_routes_are_in_both_allow_lists():
    ts = (REPO / "apps" / "research-ui" / "app" / "api" / "console" / "[...path]" / "route.ts").read_text(encoding="utf-8")
    sid = "rec_" + "a" * 32
    for path in (
        f"api/v1/inception/drafts/{sid}/checks",
        f"api/v1/inception/drafts/{sid}/checks/CONCEPT_TERM_MISSING/dismiss",
        f"api/v1/inception/drafts/{sid}/checks/CONCEPT_TERM_MISSING/restore",
        "api/v1/discovery/checks/DEDUP_RATE_LOW/dismiss",
        "api/v1/discovery/checks/DEDUP_RATE_LOW/restore",
    ):
        assert any(p.fullmatch(path) for p in POST_PATHS), path
    assert "checks\\/[A-Z][A-Z0-9_]+\\/(dismiss|restore)$/" in ts
    assert "discovery\\/checks\\/[A-Z][A-Z0-9_]+\\/(dismiss|restore)$/" in ts
