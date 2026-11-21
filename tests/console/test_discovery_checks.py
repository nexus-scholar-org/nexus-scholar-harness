"""The discovery checks (M10b Part B, ``docs/ux/shared/final/02-checks.md`` "Discovery").

Offline, on the doubles of ``test_discovery_api.py``. The strict run of
2026-11-13 is the source of three rows: a harvest of 1,074 records against a
plan nobody had stated, 2.2% of records merged across four databases, and a
Hand-off that said nothing was ready while preparation had stopped.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from scholar_search.config import settings

from scholar_harness.console import discovery_checks as DC
from scholar_harness.console.api import discovery as D

_SPEC = importlib.util.spec_from_file_location(
    "_discovery_api_helpers_checks", Path(__file__).resolve().parent / "test_discovery_api.py"
)
h = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(h)
_PREP = importlib.util.spec_from_file_location(
    "_harvest_preparation_helpers_checks", Path(__file__).resolve().parent / "test_harvest_preparation_api.py"
)
prep = importlib.util.module_from_spec(_PREP)
_PREP.loader.exec_module(prep)

env = h.env
BASE = h.BASE
ACCEPT = "/api/v1/screening/corpus/accept"


def _checks(client, step: str | None = None, **params) -> dict:
    answer = client.get(f"{BASE}/checks", params={**({"step": step} if step else {}), **params})
    assert answer.status_code == 200, answer.text
    return answer.json()


def _ids(body: dict) -> list[str]:
    return [c["check_id"] for c in body["checks"]]


def _one(body: dict, check_id: str, subject: str = "") -> dict:
    return next(c for c in body["checks"] if c["check_id"] == check_id and c["subject"] == subject)


def _legs(fetched: dict[str, int], *, failed: tuple[str, ...] = (), capped: tuple[str, ...] = ()) -> list[dict]:
    return [
        {"provider": p, "query_id": "Q", "executed_query": "q", "reported_total": n, "fetched": n,
         "cap": 10000, "cap_source": "engine_ceiling", "cap_hit": p in capped, "status": "failed" if p in failed else "ok",
         "error": None, "error_code": "PROVIDER_TIMEOUT" if p in failed else None, "notes": [], "request": {},
         "started_at": "2026-11-13T08:00:00Z", "finished_at": "2026-11-13T08:00:00Z"}
        for p, n in fetched.items()
    ]


def _intent(ws: Path, pool_min, pool_max) -> None:
    (ws / "intent.json").write_text(json.dumps({"pool_min": pool_min, "pool_max": pool_max}), encoding="utf-8")


def test_harvest_above_target_1050_vs_300(env):
    client, ws, _ = env
    _intent(ws, 150, 300)
    h._write_run(ws, 1, started="2026-11-13T08:00:00Z", legs=_legs({"openalex": 600, "crossref": 450}))
    row = _one(_checks(client, "harvest"), "HARVEST_ABOVE_TARGET")
    assert row["level"] == "warning" and row["params"] == {"n": 1050, "min": 150, "max": 300}
    assert row["message"] == "The harvest fetched 1050 records; you planned 150 to 300."
    assert row["message_key"] == "checks.HARVEST_ABOVE_TARGET.sentence" and row["threshold"]["value"] == 300
    h._write_run(ws, 2, started="2026-11-14T08:00:00Z", legs=_legs({"openalex": 150, "crossref": 100}))
    assert "HARVEST_ABOVE_TARGET" not in _ids(_checks(client, "harvest"))


def test_harvest_above_general_limit_when_no_plan_stated(env):
    client, ws, _ = env
    _intent(ws, None, None)  # the protocol holds a preset; a preset is never the researcher's plan
    h._write_run(ws, 1, started="2026-11-13T08:00:00Z", legs=_legs({"openalex": 600, "crossref": 450}))
    row = _one(_checks(client, "harvest"), "HARVEST_ABOVE_TARGET")
    assert row["params"] == {"n": 1050, "limit": 1000} and row["threshold"]["value"] == 1000
    assert row["message"] == "The harvest fetched 1050 records, over the general limit of 1000."
    assert row["message_key"] == "checks.HARVEST_ABOVE_TARGET_general.sentence"
    h._write_run(ws, 2, started="2026-11-14T08:00:00Z", legs=_legs({"openalex": 500, "crossref": 400}))
    assert "HARVEST_ABOVE_TARGET" not in _ids(_checks(client, "harvest"))
    (ws / "intent.json").unlink()
    assert DC.planned(ws) is None


def test_harvest_legs_empty_failed_and_capped(env):
    client, ws, _ = env
    h._write_run(ws, 1, started="2026-11-13T08:00:00Z",
                 legs=_legs({"openalex": 300, "crossref": 0, "arxiv": 0, "pubmed": 50}, failed=("arxiv",), capped=("openalex",)))
    body = _checks(client, "harvest")
    assert [c["subject"] for c in body["checks"] if c["check_id"] == "HARVEST_DATABASE_EMPTY"] == ["crossref"]
    assert _one(body, "HARVEST_LEG_FAILED", "arxiv")["params"] == {"database": "arxiv", "code": "PROVIDER_TIMEOUT"}
    assert _one(body, "HARVEST_LOWER_BOUND", "openalex")["level"] == "note"


def _clusters(ws: Path, run: str, inputs: int, removed: int) -> None:
    unique = inputs - removed
    clusters = []
    for i in range(unique):
        members = [{"id": f"r{i}", "merged_by": None}]
        if i < removed:
            members.append({"id": f"r{i}b", "merged_by": "identifier"})
        clusters.append({"members": members})
    path = ws / "literature" / "dedup" / "clusters.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"run": run, "clusters": clusters, "method": {}}), encoding="utf-8")


def test_dedup_rate_low_across_four_databases(env):
    client, ws, _ = env
    h._write_run(ws, 1, started="2026-11-13T08:00:00Z",
                 legs=_legs({"openalex": 400, "semanticscholar": 300, "crossref": 250, "arxiv": 100}))
    _clusters(ws, "run_001", 1050, 23)
    row = _one(_checks(client, "dedup"), "DEDUP_RATE_LOW")
    assert row["params"] == {"share": "2.2%", "n": 1050, "k": 4}
    _clusters(ws, "run_001", 1050, 326)
    assert "DEDUP_RATE_LOW" not in _ids(_checks(client, "dedup"))


def test_dedup_rate_low_needs_three_databases(env):
    client, ws, _ = env
    h._write_run(ws, 1, started="2026-11-13T08:00:00Z", legs=_legs({"openalex": 600, "crossref": 450}))
    _clusters(ws, "run_001", 1050, 23)
    assert "DEDUP_RATE_LOW" not in _ids(_checks(client, "dedup"))


def test_handoff_preparation_unfinished_is_a_blocker_when_nothing_is_staged(env, monkeypatch):
    client, ws, _ = env
    assert "HANDOFF_PREPARATION_UNFINISHED" not in _ids(_checks(client, "handoff"))  # no run: the true empty state
    prep._fail_verification_once(client, monkeypatch)
    row = _one(_checks(client, "handoff"), "HANDOFF_PREPARATION_UNFINISHED")
    assert row["level"] == "blocker" and row["refusal"] == "PREPARATION_UNFINISHED" and not row["dismissible"]
    assert row["params"]["state"] == "failed" and row["params"]["stage"] == "verification"
    assert row["action"]["step"] == "harvest" and row["action"]["finish"] is True
    refused = client.post(ACCEPT)
    assert refused.status_code == 409 and h._code(refused) == "PREPARATION_UNFINISHED"
    # Finished: no row.
    prep._finish(client)
    assert "HANDOFF_PREPARATION_UNFINISHED" not in _ids(_checks(client, "handoff"))


def test_handoff_preparation_unfinished_is_a_note_with_staged_exports():
    handoff = {"run": "run_001", "preparation": {"state": "failed", "stage": "verification", "can_finish": True},
               "corpus": {"state": "STAGED", "sources": [{"label": "Scopus"}]}, "abstracts": {}, "provider_mix": []}
    (row,) = DC._handoff(handoff, None)
    assert row["level"] == "note" and row["refusal"] is None and row["dismissible"]


def test_running_preparation_gives_no_check():
    """The engine reads ``preparation`` through ``_preparation`` with the live job, so it says ``running``."""
    handoff = {"run": "run_001", "preparation": {"state": "running", "stage": "hydration"}, "corpus": {"state": "EMPTY"},
               "abstracts": {}, "provider_mix": []}
    assert DC._handoff(handoff, None) == []


def test_handoff_search_changed_blocker(env):
    client, ws, _ = env
    job, _ = h._run(client, {"providers": ["openalex"]})
    assert job["state"] == "succeeded", job
    h._edit_protocol(ws, lambda p: p["search_strategy"]["date_range"].update(start_year=2015))
    row = _one(_checks(client, "handoff"), "HANDOFF_SEARCH_CHANGED")
    assert row["level"] == "blocker" and row["refusal"] == "PROTOCOL_CHANGED_SINCE_RUN"
    assert h._code(client.post(ACCEPT)) == "PROTOCOL_CHANGED_SINCE_RUN"
    staged = {"run": "run_001", "search_changed": True, "preparation": {}, "corpus": {"sources": [{"label": "x"}]},
              "abstracts": {}, "provider_mix": []}
    assert DC._handoff(staged, None)[0]["level"] == "note"


def test_handoff_abstracts_and_one_database():
    handoff = {"run": "run_001", "preparation": {"state": "ready"}, "corpus": {"state": "STAGED"},
               "abstracts": {"with_abstract": 70, "title_only": 30, "share_with_abstract": 0.7},
               "provider_mix": [{"provider": "openalex", "share": 0.9}, {"provider": "crossref", "share": 0.2}]}
    ids = [c["check_id"] for c in DC._handoff(handoff, None)]
    assert ids == ["HANDOFF_ABSTRACTS_MISSING", "HANDOFF_ONE_DATABASE_DOMINATES"]


def test_discovery_checks_do_not_serve_the_estimate_check(env):
    client, ws, _ = env
    _intent(ws, None, None)
    h._write_run(ws, 1, started="2026-11-13T08:00:00Z", legs=_legs({"openalex": 5000}))
    assert "PLAN_ESTIMATE_ABOVE_TARGET" not in _ids(_checks(client))


def test_plan_mailto_blocker(env, monkeypatch):
    client, _ws, _ = env
    assert "PLAN_MAILTO_NOT_SET" not in _ids(_checks(client, "plan"))
    monkeypatch.setattr(settings, "mailto", "")
    row = _one(_checks(client, "plan"), "PLAN_MAILTO_NOT_SET")
    assert row["level"] == "blocker" and row["refusal"] == "MAILTO_NOT_SET"


def test_plan_openalex_key_blocker_only_when_selected(env, monkeypatch):
    client, ws, _ = env
    monkeypatch.setattr(settings, "openalex_key", None)
    assert _one(_checks(client, "plan"), "PLAN_OPENALEX_KEY_NOT_SET")["refusal"] == "OPENALEX_KEY_NOT_SET"
    h._edit_protocol(ws, lambda p: p["search_strategy"].update(target_databases=["crossref", "arxiv"]))
    assert "PLAN_OPENALEX_KEY_NOT_SET" not in _ids(_checks(client, "plan"))


def test_plan_query_term_missing_and_no_cap(env):
    client, ws, _ = env
    body = _checks(client, "plan")
    assert "PLAN_QUERY_TERM_MISSING" not in _ids(body)  # the golden protocol has UAV, weed and mapping
    assert _one(body, "PLAN_NO_CAP")["params"] == {"ceiling": 10000}
    h._edit_protocol(ws, lambda p: p["search_strategy"].update(core_concepts=[c for c in p["search_strategy"]["core_concepts"] if c["concept"] != "UAV"]))
    assert _one(_checks(client, "plan"), "PLAN_QUERY_TERM_MISSING", "UAV")["action"] == {
        "kind": "step", "step": "inception", "label_key": "checks.PLAN_QUERY_TERM_MISSING.action",
    }


def test_recall_missed_and_stale(env):
    client, ws, _ = env
    assert _one(_checks(client, "recall"), "RECALL_NOT_RUN")["level"] == "note"
    path = ws / "literature" / "recall_checks" / "check_001.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"shape": "discovery.recall-v1", "protocol_fingerprint": "sha256:old",
                                "missed_everywhere": ["10.1/missed"], "found": 1, "total": 2}), encoding="utf-8")
    body = _checks(client, "recall")
    missed = _one(body, "RECALL_SEED_MISSED", "10.1/missed")
    assert missed["level"] == "warning"
    # M11a part D (decision 2026-11-21 item 3, the spec's question 7): the query is changed on Plan now.
    assert {k: missed["action"][k] for k in ("kind", "step", "section")} == {"kind": "step", "step": "plan", "section": "change-search"}
    assert "RECALL_CHECK_STALE" in _ids(body) and "RECALL_NOT_RUN" not in _ids(body)


def test_dismiss_appends_check_dismissals_jsonl_and_journal_row(env):
    client, ws, _ = env
    h._write_run(ws, 1, started="2026-11-13T08:00:00Z", legs=_legs({"openalex": 300, "crossref": 0}))
    row = _one(_checks(client, "harvest"), "HARVEST_DATABASE_EMPTY", "crossref")
    refused = client.post(f"{BASE}/checks/HARVEST_DATABASE_EMPTY/dismiss", json={"subject": "crossref", "evidence_digest": row["evidence_digest"]})
    assert refused.status_code == 422 and h._code(refused) == "CHECK_REASON_REQUIRED"
    ok = client.post(f"{BASE}/checks/HARVEST_DATABASE_EMPTY/dismiss",
                     json={"subject": "crossref", "evidence_digest": row["evidence_digest"], "reason": "Crossref holds no abstracts here"})
    assert ok.status_code == 200, ok.text
    assert _one(ok.json(), "HARVEST_DATABASE_EMPTY", "crossref")["status"] == "dismissed"
    lines = [json.loads(x) for x in (ws / "audit" / "check_dismissals.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [(x["check_id"], x["action"], x["run"]) for x in lines] == [("HARVEST_DATABASE_EMPTY", "dismissed", "run_001")]
    journal = [e for e in h._journal(ws) if e["action"] == "CHECK_DISMISSED"]
    assert len(journal) == 1 and journal[0]["parameters"]["method"] == "HUMAN"
    assert journal[0]["parameters"]["reason"] == "Crossref holds no abstracts here"
    restored = client.post(f"{BASE}/checks/HARVEST_DATABASE_EMPTY/restore", json={"subject": "crossref"})
    assert restored.status_code == 200
    assert [e["action"] for e in h._journal(ws) if e["action"].startswith("CHECK_")] == ["CHECK_DISMISSED", "CHECK_RESTORED"]


def test_dismissal_reopens_on_a_new_run(env):
    client, ws, _ = env
    h._write_run(ws, 1, started="2026-11-13T08:00:00Z", legs=_legs({"openalex": 300, "crossref": 0}))
    row = _one(_checks(client, "harvest"), "HARVEST_DATABASE_EMPTY", "crossref")
    client.post(f"{BASE}/checks/HARVEST_DATABASE_EMPTY/dismiss",
                json={"subject": "crossref", "evidence_digest": row["evidence_digest"], "reason": "known"})
    h._write_run(ws, 2, started="2026-11-14T08:00:00Z", legs=_legs({"openalex": 300, "crossref": 0}))
    again = _one(_checks(client, "harvest"), "HARVEST_DATABASE_EMPTY", "crossref")
    assert again["status"] == "open" and again["previously_dismissed"]["reason"] == "known"


def test_unknown_step_and_run(env):
    client, _ws, _ = env
    assert h._code(client.get(f"{BASE}/checks", params={"step": "shape"})) == "STEP_UNKNOWN"
    assert h._code(client.get(f"{BASE}/checks", params={"run": "run_009"})) == "RUN_NOT_FOUND"


def test_a_workspace_without_a_protocol_refuses_the_list(env):
    client, ws, _ = env
    (ws / "protocol.json").unlink()
    assert h._code(client.get(f"{BASE}/checks")) == "PROTOCOL_MISSING"


@pytest.mark.parametrize("step", ["plan", "recall", "harvest", "dedup", "report", "handoff"])
def test_every_discovery_step_answers_a_list(env, step):
    client, _ws, _ = env
    body = _checks(client, step)
    assert body["shape"] == "checks-v1" and all(c["step"] == step for c in body["checks"])
    assert body["scope"]["kind"] == "workspace"
    assert "ready" not in body and D.ENGINE_CEILING == 10_000
