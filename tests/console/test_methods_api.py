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


SCOPUS_RIS = 'TY  - JOUR\nAU  - Rossi, M.\nTI  - UAV weed mapping in maize\nPY  - 2024\nDO  - 10.1000/m5b-1\nER  - \nTY  - JOUR\nAU  - Chen, L.\nTI  - Drone crop scouting with deep learning\nPY  - 2022\nDO  - 10.1000/m5b-2\nER  - \nTY  - JOUR\nAU  - Diaz, A.\nTI  - Hyperspectral weed discrimination\nPY  - 2021\nER  - \n'
WOS_RIS = 'TY  - JOUR\nAU  - Rossi, M.\nTI  - UAV Weed Mapping in Maize\nPY  - 2024\nDO  - https://doi.org/10.1000/M5B-1\nER  - \nTY  - JOUR\nAU  - Diaz, A.\nTI  - Hyperspectral weed discrimination.\nPY  - 2021\nER  - \nTY  - JOUR\nAU  - Okafor, N.\nTI  - Site-specific herbicide prescription maps\nPY  - 2023\nDO  - 10.1000/m5b-4\nER  - \n'


def _imported_workspace(tmp_path: Path) -> Path:
    """Two database exports (6 records, 2 duplicates) accepted and prepared, nothing decided."""
    from scholar_harness.corpus_accept import accept_corpus, stage_ris_source
    from scholar_harness.screening.batcher import cmd_prepare

    ws = tmp_path / "ws"
    (ws / "literature").mkdir(parents=True)
    (ws / "audit").mkdir()
    (ws / "audit" / "journal.jsonl").write_text("", encoding="utf-8")
    (ws / "project.json").write_text(json.dumps({"project_id": "m5b", "registered_workspace_id": se.WS_ID}), encoding="utf-8")
    (ws / "protocol.json").write_text(se.PROTOCOL.read_text(encoding="utf-8"), encoding="utf-8")
    stage_ris_source(ws, "Scopus", SCOPUS_RIS.encode(), file_name="scopus.ris", searched_on="2026-11-06")
    stage_ris_source(ws, "Web of Science", WOS_RIS.encode(), file_name="savedrecs.ris")
    accept_corpus(ws)
    cmd_prepare(ws, batch_size=20)
    return ws


def test_an_imported_corpus_publishes_the_snapshot_counts_and_names_its_databases(tmp_path):
    """S-P0-1 (full review 2026-11-06): with one verified row per record, collect and
    approval used to publish duplicates_removed = 0 for 6 records in 4 studies."""
    ws = _imported_workspace(tmp_path)
    studies = se._studies(ws)
    assert len(studies) == 4
    se._intake(ws, [se._event(ws, study, "INCLUDE") for study in studies])
    publish(ws)

    prisma = json.loads((ws / "literature" / "prisma_report.json").read_text(encoding="utf-8"))
    preview = client_for(ws).get(f"{BASE}/prisma/preview").json()
    assert (prisma["total_identified"], prisma["duplicates_removed"], prisma["records_screened"]) == (6, 2, 4)
    assert (preview["identified"], preview["duplicates_removed"], preview["screened"]) == (6, 2, 4)

    body = _methods(ws)
    _assert_numbers_trace(body)
    assert body["paragraph"].startswith(
        "Records were identified from Scopus (n = 3, searched 2026-11-06) and Web of Science (n = 3). "
        "6 records were identified; 2 duplicates were removed; 4 records were screened;"
    )
    assert [s["records"] for s in body["figures"]["identified_by_source"]] == [3, 3]
    assert "Date searched: not recorded for every database." in body["not_stated"]
    assert "provenance_manifest.json" in {s["name"] for s in body["sources"]}


# --- M6-beta: the paragraph reads as prose (review U-2, S-P1-1), on the 2026-11-06 evidence run ---

EVIDENCE = Path(__file__).resolve().parents[2] / "workspaces" / "golden-uav-30-run-2026-11-06"


def _evidence_methods(tmp_path: Path) -> dict:
    import shutil

    from scholar_harness.screening.export import build_methods

    ws = tmp_path / "evidence"
    shutil.copytree(EVIDENCE, ws)
    return build_methods(ws)


def test_no_op_settings_rows_are_not_repeated(tmp_path):
    paragraph = _evidence_methods(tmp_path)["paragraph"]
    assert paragraph.count("The AI-agreed-exclusion setting was") == 1
    assert "The AI-agreed-exclusion setting was off." in paragraph
    # Blinding really changed (hidden, shown, hidden, shown): each change once, no show-to-show row.
    assert paragraph.count("Drafts were shown before the decision from 2026-11-06.") == 1


def test_visible_drafts_report_no_blind_comparison(tmp_path):
    body = _evidence_methods(tmp_path)
    assert "After seeing a draft, the reviewer changed" not in body["paragraph"]
    assert "29 decisions were made with the draft visible; no blind comparison is reported." in body["paragraph"]
    assert body["figures"]["decided_with_draft_visible"] == 29
    _assert_numbers_trace(body)


def test_mcp_drafts_name_the_route(tmp_path):
    body = _evidence_methods(tmp_path)
    assert "provider not recorded" not in body["paragraph"]
    assert "via the researcher's Claude session (MCP)" in body["paragraph"]
    assert not any(s.startswith("Provider of the") for s in body["not_stated"])


def test_advance_setting_is_reported_only_when_drafts_were_skipped(tmp_path):
    """Spec 10 decision (researcher, 2026-11-07): said only when 'move on at once' skipped drafts."""
    ws = tmp_path / "evidence"
    import shutil

    from scholar_harness.screening.export import build_methods

    shutil.copytree(EVIDENCE, ws)
    assert "opened at once" not in build_methods(ws)["paragraph"]
    row = {
        "timestamp": "2026-11-05T00:00:00Z", "action": "SCREENING_SETTINGS_CHANGED", "agent": "test",
        "parameters": {"before": {"advance_on_decide": "show_draft_then_next"}, "after": {"advance_on_decide": "next_at_once"}},
    }
    with (ws / "audit" / "journal.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    body = build_methods(ws)
    assert (
        "For 29 records the next record opened at once after the decision, so the draft was not shown unless "
        "the reviewer opened it from the record's details."
    ) in body["paragraph"]
    assert body["figures"]["decided_draft_skipped"] == 29
    _assert_numbers_trace(body)


def test_blind_and_visible_decisions_each_get_their_sentence(tmp_path):
    """Spec 10 decision (researcher, 2026-11-07): both sentences when the two kinds mix."""
    ws = se._build(tmp_path)
    context = ev.load_context(ws)
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    studies = se._studies(ws)
    proposals = [
        pr.submit_proposal(
            ws, study_id=s, title="t", abstract="a", output={"criteria": [], "cannot_decide": True},
            protocol=protocol, protocol_fingerprint=context.protocol_fingerprint,
            provenance={"task_version": "screen-v1", "model": MODEL, "driver": "mcp", "prompt_sha256": PROMPT},
            created_at="2026-11-05T08:10:00Z",
        )
        for s in studies
    ]
    # Two decided blind (no draft in view), one with its draft visible.
    first = [se._event(ws, s, "INCLUDE", decided_at="2026-11-05T09:00:00.000Z") for s in studies[:2]]
    first.append(se._event(ws, studies[2], "INCLUDE", decided_at="2026-11-05T09:00:00.000Z",
                           proposal_shown={"proposal_id": proposals[2]["proposal_id"], "revealed_after_decision": False}))
    se._intake(ws, first, received_at="2026-11-05T09:00:05Z")
    ev.record_reveal(ws, study_id=studies[0], screener_id=se.SCREENER, proposal_id=proposals[0]["proposal_id"],
                     context=context, revealed_at="2026-11-05T09:30:00Z")
    se._intake(
        ws, [se._event(ws, studies[0], "EXCLUDE", supersedes=first[0]["event_id"], decided_at="2026-11-05T10:00:00.000Z")],
        received_at="2026-11-05T10:00:05Z",
    )
    publish(ws)
    body = _methods(ws)
    assert "After seeing a draft, the reviewer changed 1 of 1 decisions." in body["paragraph"]
    assert "1 decision was made with the draft visible; no blind comparison is reported." in body["paragraph"]
    _assert_numbers_trace(body)
