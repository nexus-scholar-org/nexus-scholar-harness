"""The methods paragraph of the published screening (spec 10, `GET /methods`).

Fixtures are published through the real path (events, projection, staged
approval, `cmd_collect`; helpers from `test_export_api.py`, which reuses
`tests/test_screening_events.py`). Settings changes go through `PUT /settings`
so the journal history is the real one.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from test_export_api import BASE, client_for, decide, publish, published_workspace, se

from scholar_harness.screening import agent_runs as runs
from scholar_harness.screening import events as ev
from scholar_harness.screening import proposals as pr
from scholar_harness.screening.export import FORBIDDEN_WORDS

PROMPT = "sha256:" + "ab12" * 16
MODEL = "claude-opus-5-5"


def _methods(ws: Path) -> dict:
    response = client_for(ws).get(f"{BASE}/methods")
    assert response.status_code == 200, response.text
    return response.json()


def _leaves(value) -> list:
    if isinstance(value, dict):
        return [x for k, v in value.items() for x in (k, *_leaves(v))]
    if isinstance(value, list):
        return [x for v in value for x in _leaves(v)]
    return [value]


def _assert_numbers_trace(body: dict) -> None:
    leaves = _leaves(body["figures"])
    numbers = {v for v in leaves if isinstance(v, int) and not isinstance(v, bool)}
    text = body["paragraph"].replace("SHA-256", "")
    for string in sorted({v for v in leaves if isinstance(v, str)}, key=len, reverse=True):
        text = text.replace(string, " ")
    found = [int(n) for n in re.findall(r"\d+", text)]
    assert found, "anti-vacuity: the paragraph states counts"
    assert set(found) <= numbers, (found, numbers)


def _assert_no_forbidden(paragraph: str) -> None:
    lowered = paragraph.lower()
    for word in ("validated", "accurate", "recall", "agreement", "concordance", "kappa", "cost", "gate"):
        assert word not in lowered, word
    assert set(FORBIDDEN_WORDS) == {"validated", "accurate", "recall", "agreement", "concordance", "kappa", "cost", "gate"}


def _agent_workspace(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    """Proposals from a recorded run, consent, a reveal, one tracked and one untracked change,
    and blinding and queue-order changes through PUT /settings."""
    ws = se._build(tmp_path)
    client = client_for(ws)
    assert client.put(f"{BASE}/settings", json={"blinding": "show"}).status_code == 200
    assert client.put(f"{BASE}/settings", json={"queue_order": "agent_uncertainty"}).status_code == 200
    context = ev.load_context(ws)
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    studies = se._studies(ws)
    run_dir = ws / runs.RUNS_DIR
    run_dir.mkdir(parents=True)
    (run_dir / "RUN-methods.json").write_text(
        json.dumps({"run_id": "RUN-methods", "provider": "anthropic", "model": MODEL, "state": "completed"}),
        encoding="utf-8",
    )
    runs.record_consent(ws, "anthropic", model=MODEL, prompt_sha256=PROMPT, accepted_at="2026-11-05T08:00:00Z")
    proposals = [
        pr.submit_proposal(
            ws, study_id=s, title="t", abstract="a", output={"criteria": [], "cannot_decide": True},
            protocol=protocol, protocol_fingerprint=context.protocol_fingerprint,
            provenance={"task_version": "screen-v1", "model": MODEL, "driver": "api", "prompt_sha256": PROMPT,
                        "run_id": "RUN-methods"},
            created_at="2026-11-05T08:10:00Z",
        )
        for s in studies[:2]
    ]
    first = [se._event(ws, s, "INCLUDE") for s in studies]
    se._intake(ws, first)  # received 2026-11-04: before reveal tracking began
    # Untracked: a change received before reveal tracking existed.
    se._intake(
        ws, [se._event(ws, studies[1], "MAYBE", supersedes=first[1]["event_id"], decided_at="2026-11-04T11:00:00.000Z")],
        received_at="2026-11-04T11:00:05Z",
    )
    # Tracked: the draft is revealed, then the decision changes.
    ev.record_reveal(ws, study_id=studies[0], screener_id=se.SCREENER, proposal_id=proposals[0]["proposal_id"],
                     context=context, revealed_at="2026-11-05T08:30:00Z")
    se._intake(
        ws, [se._event(ws, studies[0], "EXCLUDE", supersedes=first[0]["event_id"], decided_at="2026-11-05T09:00:00.000Z")],
        received_at="2026-11-05T09:00:05Z",
    )
    assert ev.read_events(ws)[-1]["changed_after_reveal"] is True
    publish(ws)
    return ws, {"changed": studies[0], "untracked": studies[1]}


def test_every_number_in_the_paragraph_is_a_figure_and_matches_prisma(tmp_path):
    ws, _ids = published_workspace(tmp_path)
    body = _methods(ws)
    _assert_numbers_trace(body)
    prisma = json.loads((ws / "literature" / "prisma_report.json").read_text(encoding="utf-8"))
    figures = body["figures"]
    assert (figures["identified"], figures["duplicates_removed"], figures["screened"], figures["excluded"],
            figures["unclear"], figures["included"]) == (
        prisma["total_identified"], prisma["duplicates_removed"], prisma["records_screened"],
        prisma["records_excluded"], prisma["records_unclear"], prisma["records_included"])
    assert figures["exclusion_reasons"] == prisma["exclusion_reasons_breakdown"]
    assert body["language"] == "en"
    generation = json.loads((ws / "literature" / "screening" / "generation.json").read_text(encoding="utf-8"))
    assert body["generation_id"] == generation["generation_id"]
    assert body["published_at"] == generation["published_at"]
    sources = {s["name"]: s for s in body["sources"]}
    assert sources["prisma_report.json"]["digest"] == generation["outputs"]["prisma_report.json"]
    assert sources["excluded.json"]["digest"] == generation["outputs"]["excluded.json"]


def test_no_proposals_states_that_no_ai_model_proposed(tmp_path):
    ws, _ids = published_workspace(tmp_path)
    body = _methods(ws)
    assert "No AI model proposed decisions for this screening." in body["paragraph"]
    assert "One reviewer screened every record." in body["paragraph"]
    assert body["figures"]["n_proposed"] == 0
    _assert_no_forbidden(body["paragraph"])


def test_queue_order_without_history_is_absent_and_listed_not_stated(tmp_path):
    ws, _ids = published_workspace(tmp_path)
    body = _methods(ws)
    assert "presented in" not in body["paragraph"]
    assert any(item.startswith("Queue order") for item in body["not_stated"])


def test_agent_use_consent_blinding_history_reveal_and_queue_order(tmp_path):
    ws, _ids = _agent_workspace(tmp_path)
    body = _methods(ws)
    paragraph = body["paragraph"]
    _assert_numbers_trace(body)
    _assert_no_forbidden(paragraph)
    setting_rows = [
        json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines()
        if '"SCREENING_SETTINGS_CHANGED"' in line
    ]
    blinding_date = setting_rows[0]["timestamp"][:10]
    order_date = setting_rows[1]["timestamp"][:10]
    assert (
        f"An AI model (anthropic, {MODEL}, task version screen-v1, prompt SHA-256 {'ab12' * 3}) proposed a draft "
        "decision with quoted evidence for 2 of 3 records." in paragraph
    )
    assert "Drafts were advisory; every decision in this screening was made by the reviewer." in paragraph
    assert "to anthropic on 2026-11-05." in paragraph
    # The blinding change mid-screening gives the dated sentence.
    assert "Drafts were hidden until the reviewer decided at the start of the screening." in paragraph
    assert f"Drafts were shown before the decision from {blinding_date}." in paragraph
    # One tracked change after a reveal; the earlier change is "not tracked", not zero.
    assert "After seeing a draft, the reviewer changed 1 of 1 decisions." in paragraph
    assert body["figures"]["changed_after_reveal"] == 1
    assert body["figures"]["changes_not_tracked"] == 1
    assert "whether the change followed a draft was not tracked" in paragraph
    assert any("not tracked" in item for item in body["not_stated"])
    # The queue order is reported with its date; before it, it was not recorded.
    assert f"Records were presented in agent-uncertainty order from {order_date}." in paragraph
    assert body["figures"]["queue_order"]["at_publish"] == "agent_uncertainty"
    assert f"Queue order: not recorded before {order_date}." in body["not_stated"]
    assert "The AI-agreed-exclusion setting was off." in paragraph


def test_ai_agreed_exclusion_setting_is_stated_with_its_date_and_sample(tmp_path):
    ws = se._build(tmp_path)
    client = client_for(ws)
    response = client.put(
        f"{BASE}/settings",
        json={"mode": "ai_agreed_exclusion", "sample_audit_size": 25, "confirm_ai_agreed_exclusion": True},
    )
    assert response.status_code == 200, response.text
    decide(ws)
    publish(ws)
    body = _methods(ws)
    _assert_numbers_trace(body)
    _assert_no_forbidden(body["paragraph"])
    assert re.search(
        r"The AI-agreed-exclusion setting was on from \d{4}-\d{2}-\d{2}, with a sample check of 25\.", body["paragraph"]
    )


def test_methods_source_missing_without_prisma_report(tmp_path):
    ws, _ids = published_workspace(tmp_path)
    (ws / "literature" / "prisma_report.json").unlink()
    response = client_for(ws).get(f"{BASE}/methods")
    assert response.status_code == 409, response.text
    assert response.json()["detail"]["code"] == "METHODS_SOURCE_MISSING"
    assert response.json()["detail"]["missing"] == "prisma_report.json"


def test_methods_is_generation_stale_after_a_decision_following_publish(tmp_path):
    ws, ids = published_workspace(tmp_path)
    from test_export_api import change_after_publish

    change_after_publish(ws, ids["included"])
    response = client_for(ws).get(f"{BASE}/methods")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "GENERATION_STALE"


def _tree(ws: Path) -> dict[str, bytes]:
    return {str(p.relative_to(ws)): p.read_bytes() for p in sorted(ws.rglob("*")) if p.is_file()}


@pytest.mark.parametrize("agent", [False, True], ids=["no-agent", "agent"])
def test_methods_writes_no_file_and_no_journal_row_and_is_repeatable(tmp_path, agent):
    ws = _agent_workspace(tmp_path)[0] if agent else published_workspace(tmp_path)[0]
    before = _tree(ws)
    first = _methods(ws)
    assert _methods(ws) == first
    assert _tree(ws) == before
