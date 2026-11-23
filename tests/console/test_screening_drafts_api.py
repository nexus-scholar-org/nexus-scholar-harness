"""H-screening-drafts: changing the method on an existing review, and the drafts under it.

The acceptance run of 2026-11-20 (``docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md``):

- the protocol's method block, written at genesis, set ``blinding`` and the
  not-reported policy; Prepare offered "Show beside the record" and silently did
  nothing, because ``PUT /settings`` refuses a change the protocol sets;
- 85% of the agent's drafts were Unclear because the ``unclear`` policy returns
  MAYBE before it looks at a decisive answer.

A method amendment (decision PROPOSED in ``docs/decisions.md``, H-screening-drafts)
changes ``blinding`` or ``not_reported`` after the workspace was created, as an
append-only record beside the signed protocol: ``protocol.json``, its fingerprint,
the accepted corpus, the batches and every decision stay as they are. Stored drafts
keep their answers and the outcome first derived; the outcome shown and counted is
derived at read time under the policy in force.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import test_screening_api_v1 as api
from fastapi.testclient import TestClient
from test_agent_runs_api import CONSENT, FakeDriver
from test_screening_api_v1 import BASE, RUN, DESKTOP, PHONE, _event, _post, _studies

from scholar_harness.console import create_app
from scholar_harness.console.refusals import CONSOLE_REFUSALS
from scholar_harness.screening import events as ev
from scholar_harness.screening import proposals as pr

BLOCK = {
    "dedup": {"doi": True, "title_similarity": 0.97, "first_author": True, "year_tolerance": 1},
    "rules_version": "screening-rules-v1",
    "not_reported": "unclear",
    "blinding": "reveal_after_decision",
}


def _workspace_with_block(tmp_path: Path, monkeypatch, block: dict | None = BLOCK, prepare: bool | str = True) -> Path:
    """The API test workspace, its protocol carrying a method block from genesis."""
    protocol = json.loads(api.PROTOCOL.read_text(encoding="utf-8"))
    if block is not None:
        protocol["method"] = block
    path = tmp_path / "protocol_with_block.json"
    path.write_text(json.dumps(protocol), encoding="utf-8")
    monkeypatch.setattr(api, "PROTOCOL", path)
    root = tmp_path / "root"
    root.mkdir()
    return api._workspace(root, prepare=prepare)


def _client(ws: Path, driver=None, token: str = DESKTOP) -> TestClient:
    app = create_app(ws, token=DESKTOP, phone_tokens={PHONE})
    app.state.driver_factory = lambda provider, key: driver or FakeDriver()
    app.state.run_executor = lambda fn: fn()
    return TestClient(app, base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {token}"})


def _journal(ws: Path) -> list[dict]:
    return [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def _amend(client: TestClient, field: str, value: str, **extra):
    return client.post(f"{BASE}/method/amendments", json={"field": field, "value": value, "confirm": True, **extra})


# --- 2. the silent radio: a blinding change is applied as a recorded amendment -------


def test_a_blinding_change_on_a_protocol_set_workspace_is_applied_as_an_amendment(tmp_path, monkeypatch):
    ws = _workspace_with_block(tmp_path, monkeypatch)
    client = _client(ws)
    protocol_bytes = (ws / "protocol.json").read_bytes()
    fingerprint = ev.load_context(ws).protocol_fingerprint
    study = _studies(client)[0]
    _post(client, [_event(client, study)])  # a decision before the amendment
    # Today: the radio's only route refuses, so the screen did nothing.
    assert client.put(f"{BASE}/settings", json={"blinding": "show"}).json()["detail"]["code"] == "BLINDING_SET_BY_PROTOCOL"

    response = _amend(client, "blinding", "show")
    assert response.status_code == 200, response.text
    settings = client.get(f"{BASE}/settings").json()
    assert (settings["blinding"], settings["blinding_source"]) == ("show", "protocol")
    [amendment] = settings["method_amendments"]
    assert (amendment["field"], amendment["from"], amendment["to"]) == ("blinding", "reveal_after_decision", "show")
    assert amendment["amended_by"] == "researcher:local" and amendment["amended_at"]
    assert amendment["protocol_fingerprint"] == fingerprint

    # Who, when, from, to: one journal row.
    [row] = [r for r in _journal(ws) if r["action"] == "PROTOCOL_METHOD_AMENDED"]
    assert row["parameters"]["field"] == "blinding"
    assert row["parameters"]["before"] == {"blinding": "reveal_after_decision"}
    assert row["parameters"]["after"] == {"blinding": "show"}
    assert row["parameters"]["amended_by"] == "researcher:local"
    assert row["parameters"]["protocol_fingerprint"] == fingerprint

    # The signed protocol, its fingerprint and every binding are untouched.
    assert (ws / "protocol.json").read_bytes() == protocol_bytes
    assert ev.load_context(ws).protocol_fingerprint == fingerprint
    summary = client.get(f"{BASE}/summary").json()
    assert (summary["decided"], summary["protocol_changed"]) == (1, False)
    # Blinding is now off: an undecided record's draft is no longer hidden.
    undecided = _studies(client)[1]
    assert client.get(f"{BASE}/records/{undecided}/proposal").status_code == 200


def test_an_amendment_that_changes_nothing_or_names_an_unknown_value_is_refused(tmp_path, monkeypatch):
    ws = _workspace_with_block(tmp_path, monkeypatch)
    client = _client(ws)
    before = (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8")
    for field, value in (("blinding", "reveal_after_decision"), ("blinding", "hidden"), ("not_reported", "include"),
                         ("dedup", "loose"), ("rules_version", "screening-rules-v2")):
        response = _amend(client, field, value)
        assert response.status_code == 422, (field, value)
        assert response.json()["detail"]["code"] == "METHOD_AMENDMENT_INVALID"
    unconfirmed = client.post(f"{BASE}/method/amendments", json={"field": "blinding", "value": "show"})
    assert unconfirmed.status_code == 422 and unconfirmed.json()["detail"]["code"] == "METHOD_AMENDMENT_INVALID"
    assert (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8") == before
    assert "METHOD_AMENDMENT_INVALID" in CONSOLE_REFUSALS


def test_a_phone_token_cannot_amend_the_method(tmp_path, monkeypatch):
    ws = _workspace_with_block(tmp_path, monkeypatch)
    response = _amend(_client(ws, token=PHONE), "blinding", "show")
    assert response.status_code == 403 and response.json()["detail"]["code"] == "TOKEN_SCOPE_REFUSED"


def test_an_amendment_made_under_another_protocol_does_not_apply(tmp_path, monkeypatch):
    """Re-inception replaces the protocol: an amendment is bound to the fingerprint it was made under."""
    ws = _workspace_with_block(tmp_path, monkeypatch)
    client = _client(ws)
    assert _amend(client, "not_reported", "decisive_first").status_code == 200
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    protocol["metadata"] = {**protocol.get("metadata", {}), "title": "A replaced protocol"}
    (ws / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    settings = client.get(f"{BASE}/settings").json()
    assert settings["not_reported_policy"] == "unclear" and settings["method_amendments"] == []


def test_without_a_block_the_policy_can_still_be_amended_and_blinding_stays_a_setting(tmp_path, monkeypatch):
    ws = _workspace_with_block(tmp_path, monkeypatch, block=None)
    client = _client(ws)
    assert _amend(client, "not_reported", "decisive_first").status_code == 200
    settings = client.get(f"{BASE}/settings").json()
    assert (settings["not_reported_policy"], settings["not_reported_source"]) == ("decisive_first", "amendment")
    # Blinding without a block is the workspace setting, changed as before.
    assert settings["blinding_source"] == "settings"
    refused = _amend(client, "blinding", "show")
    assert refused.status_code == 422 and refused.json()["detail"]["code"] == "METHOD_AMENDMENT_INVALID"
    assert client.put(f"{BASE}/settings", json={"blinding": "show"}).status_code == 200


# --- 3. re-deriving existing drafts --------------------------------------------------


def _store_draft(ws: Path, client: TestClient, study: str, inc: str, exc: str) -> dict:
    """A draft stored through the engine's own path (submit_proposal), under the policy in force."""
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    context = ev.load_context(ws)
    paper = json.loads((ws / "literature" / "screening" / "batch_001.json").read_text(encoding="utf-8"))
    record = next(p for p in paper["papers"] if p["workspace_id"] == study)
    text = pr.record_text(record.get("title"), record.get("abstract"), record.get("year"))

    def answer(cid: str, value: str) -> dict:
        if value == "not_reported":
            return {"id": cid, "answer": value}
        quote = record["title"]
        start = text.index(quote)
        return {"id": cid, "answer": value, "evidence": {"text": quote, "start": start, "end": start + len(quote)}}

    batch = context.batches[context.study_batch[study]]
    return pr.submit_proposal(
        ws, study_id=study, title=record.get("title"), abstract=record.get("abstract"), published=record.get("year"),
        output={"criteria": [answer("INC-01", inc), answer("EXC-01", exc)], "cannot_decide": False},
        protocol=protocol, protocol_fingerprint=context.protocol_fingerprint,
        provenance={"task_version": "screen-v1", "model": "m", "prompt_sha256": "sha256:" + "0" * 64, "driver": "mcp",
                    "batch_binding": {"batch_id": batch.batch_id, "batch_sha256": batch.batch_sha256}},
        created_at="2026-11-20T10:00:00Z",
    )


def test_after_a_policy_amendment_a_stored_draft_keeps_its_first_outcome_and_shows_the_one_in_force(tmp_path, monkeypatch):
    ws = _workspace_with_block(tmp_path, monkeypatch, block={**BLOCK, "blinding": "show"})
    client = _client(ws)
    decisive, gaps = _studies(client)[:2]
    # EXC-01 answered yes beside an unreported inclusion: Unclear under `unclear`.
    first = _store_draft(ws, client, decisive, "not_reported", "yes")
    _store_draft(ws, client, gaps, "not_reported", "no")
    assert first["derived_outcome"] == "MAYBE"
    stored_before = (ws / pr.PROPOSALS_FILE).read_bytes()

    assert _amend(client, "not_reported", "decisive_first").status_code == 200

    shown = client.get(f"{BASE}/records/{decisive}/proposal").json()["proposal"]
    assert (shown["derived_outcome"], shown["reason_code"]) == ("EXCLUDE", "EXC-01")
    assert shown["not_reported_policy"] == "decisive_first"
    assert shown["recorded"] == {"derived_outcome": "MAYBE", "reason_code": None, "not_reported_policy": "unclear"}
    only_gaps = client.get(f"{BASE}/records/{gaps}/proposal").json()["proposal"]
    assert only_gaps["derived_outcome"] == "MAYBE"  # gaps alone stay Unclear
    # The store is append-only: the first outcome is never rewritten.
    assert (ws / pr.PROPOSALS_FILE).read_bytes() == stored_before
    # A draft stored after the amendment is derived under it, and says so.
    third = _studies(client)[2]
    later = _store_draft(ws, client, third, "not_reported", "yes")
    assert (later["derived_outcome"], later["not_reported_policy"]) == ("EXCLUDE", "decisive_first")


def test_the_queue_order_and_the_agreement_count_the_outcome_in_force(tmp_path, monkeypatch):
    ws = _workspace_with_block(tmp_path, monkeypatch)
    client = _client(ws)
    decisive, gaps = _studies(client)[:2]
    _store_draft(ws, client, decisive, "not_reported", "yes")
    _store_draft(ws, client, gaps, "not_reported", "no")
    # The researcher excludes the first record blind.
    _post(client, [_event(client, decisive, "EXCLUDE")])
    before = client.get(f"{BASE}/agreement").json()
    assert (before["unclear_either_side"], before["table_2x2"]["both_exclude"]) == (1, 0)
    assert client.put(f"{BASE}/settings", json={"queue_order": "agent_uncertainty"}).status_code == 200

    assert _amend(client, "not_reported", "decisive_first").status_code == 200
    after = client.get(f"{BASE}/agreement").json()
    assert (after["unclear_either_side"], after["table_2x2"]["both_exclude"]) == (0, 1)
    # Unclear drafts first: the gaps-only draft is still Unclear, so it leads.
    order = [i["study_id"] for i in client.get(f"{BASE}/queue", params={"view": "needs_you"}).json()["items"]]
    assert order[0] == gaps


def test_the_calibration_scores_the_outcome_in_force(tmp_path, monkeypatch):
    from scholar_harness.screening import agent_runs as runs

    ws = _workspace_with_block(tmp_path, monkeypatch)
    client = _client(ws)
    study = _studies(client)[0]
    _store_draft(ws, client, study, "no", "not_reported")
    _post(client, [_event(client, study, "EXCLUDE")])
    assert runs.calibration_result(ws, [study])["compared"] == 1
    assert _amend(client, "not_reported", "decisive_first").status_code == 200
    # Scored under the policy in force: the draft is now an exclusion that agrees.
    from scholar_agent import prompt_gate as pg

    seen = {}
    monkeypatch.setattr(pg, "score", lambda outcomes, labels: seen.update(outcomes) or {
        "include_recall": None, "include_recall_ci_low": None, "missed_includes": []})
    runs.calibration_result(ws, [study])
    assert seen == {study: "EXCLUDE"}


def test_an_agent_run_derives_under_the_amended_policy(tmp_path, monkeypatch):
    ws = _workspace_with_block(tmp_path, monkeypatch)
    client = _client(ws, FakeDriver())
    assert _amend(client, "not_reported", "decisive_first").status_code == 200
    started = client.post(f"{BASE}/proposals/runs", json={**RUN, "consent": CONSENT}).json()
    assert client.get(f"{BASE}/proposals/runs/{started['run_id']}").json()["state"] == "completed"
    assert {p["not_reported_policy"] for p in pr.read_proposals(ws)} == {"decisive_first"}


# --- 4. the run screen: the model remembered, the batch wait, the not-prepared message ---


def test_the_setup_names_the_last_model_used_and_a_run_says_whether_it_is_a_batch(tmp_path, monkeypatch):
    ws = _workspace_with_block(tmp_path, monkeypatch)
    client = _client(ws)
    setup = client.get(f"{BASE}/proposals/setup").json()
    assert setup["last_model"] is None
    started = client.post(f"{BASE}/proposals/runs", json={**RUN, "consent": CONSENT, "model": "claude-haiku-5-5"}).json()
    setup = client.get(f"{BASE}/proposals/setup").json()
    assert setup["last_model"] == {"provider": "anthropic", "model": "claude-haiku-5-5"}
    view = client.get(f"{BASE}/proposals/runs/{started['run_id']}").json()
    assert view["batch"] is False  # three records go direct; over 20 go to the batch service
    assert view["chunk_size"] == 200


def test_before_prepare_an_accepted_corpus_is_not_called_missing(tmp_path, monkeypatch):
    ws = _workspace_with_block(tmp_path, monkeypatch, prepare="accept_only")
    client = _client(ws)
    response = client.get(f"{BASE}/queue", params={"view": "decided"})
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "BATCHES_NOT_PREPARED"
    assert "BATCHES_NOT_PREPARED" in CONSOLE_REFUSALS


def test_without_an_accepted_corpus_the_refusal_is_unchanged(tmp_path, monkeypatch):
    ws = _workspace_with_block(tmp_path, monkeypatch, prepare=False)
    response = _client(ws).get(f"{BASE}/queue", params={"view": "decided"})
    assert response.status_code == 409 and response.json()["detail"]["code"] == "SNAPSHOT_NOT_ACCEPTED"


@pytest.mark.parametrize("field", ["blinding", "not_reported"])
def test_the_methods_paragraph_reports_a_method_amendment(tmp_path, field):
    """The amendment is reported in the screening export's methods text."""
    from test_export_api import BASE as EXPORT_BASE
    from test_export_api import client_for, decide, publish
    from test_screening_events import _build

    ws = _build(tmp_path, method=dict(BLOCK))
    value = {"blinding": "show", "not_reported": "decisive_first"}[field]
    client = client_for(ws)
    response = client.post(f"{EXPORT_BASE}/method/amendments", json={"field": field, "value": value, "confirm": True})
    assert response.status_code == 200, response.text
    decide(ws)
    publish(ws)
    body = client_for(ws).get(f"{EXPORT_BASE}/methods").json()
    text = body["paragraph"]
    label = {"blinding": "the reveal of the agent's drafts", "not_reported": "the not-reported rule"}[field]
    assert f"after the protocol was signed, the reviewer changed {label}" in text
    # Review F1: the source sentence says the values are amended; no drafts, no drafts sentence.
    sentences = [x.strip() for x in text.split(". ")]
    source_at = next(i for i, x in enumerate(sentences) if x.startswith("These values are set in the signed protocol"))
    assert sentences[source_at].rstrip(".") == "These values are set in the signed protocol except as amended below"
    assert sentences[source_at + 1].startswith("On ") and label in sentences[source_at + 1]
    assert "The agent's drafts are counted" not in text and "No AI model proposed decisions for this screening" in text
    assert "audit/method_amendments.jsonl" in [src["path"] for src in body["sources"]]  # review F6
    [figure] = body["figures"]["method_amendments"]
    assert (figure["field"], figure["to"]) == (field, value)
    from test_methods_api import _assert_no_forbidden, _assert_numbers_trace

    _assert_numbers_trace(body)  # the amendment's date traces to its figure
    _assert_no_forbidden(text)
    if field == "blinding":
        assert body["figures"]["blinding"]["at_publish"] == "show"
    if field == "not_reported":
        assert body["figures"]["method"]["not_reported"] == "decisive_first"
        assert (
            "An exclusion criterion met or an inclusion criterion not met in the title and abstract excluded the record; "
            "otherwise a criterion they did not report sent it to full-text assessment."
        ) in text


# --- review round 1 (F1, F4): boundary tests ---------------------------------------


def test_an_amendment_after_publication_is_not_in_that_publications_methods(tmp_path):
    from test_export_api import BASE as EXPORT_BASE
    from test_export_api import client_for, decide, publish
    from test_screening_events import _build

    ws = _build(tmp_path, method=dict(BLOCK))
    decide(ws)
    publish(ws)
    before = client_for(ws).get(f"{EXPORT_BASE}/methods").json()
    amended = client_for(ws).post(f"{EXPORT_BASE}/method/amendments", json={"field": "not_reported", "value": "decisive_first", "confirm": True})
    assert amended.status_code == 200
    after = client_for(ws).get(f"{EXPORT_BASE}/methods").json()
    assert after["paragraph"] == before["paragraph"] and after["figures"]["method_amendments"] == []
    assert after["figures"]["method"]["not_reported"] == "unclear"


def test_a_failed_journal_write_takes_the_amendment_line_back_out(tmp_path, monkeypatch):
    from scholar_harness.screening import method as m

    ws = _workspace_with_block(tmp_path, monkeypatch)
    path = ws / m.AMENDMENTS_FILE

    def refuse(*args, **kwargs):
        raise OSError("journal is read-only")

    monkeypatch.setattr("scholar_harness.workspace.audit.append_event", refuse)
    with pytest.raises(OSError):
        m.amend_method(ws, field="blinding", value="show", amended_by="researcher:local", amended_at="2026-11-20T10:00:00Z")
    assert path.read_text(encoding="utf-8") == ""
    assert m.effective_method(ws).config.blinding == "reveal_after_decision"


CRITERIA = pr.Criteria(inclusion=("INC-01",), exclusion=("EXC-01",))


def _stored(**over) -> dict:
    stored = {
        "protocol_fingerprint": "sha256:" + "1" * 64,
        "output": {"criteria": [{"id": "INC-01", "answer": "not_reported"}, {"id": "EXC-01", "answer": "yes"}], "cannot_decide": False},
        "validators": [{"name": "schema", "ok": True}],
        "derived_outcome": "MAYBE",
        "reason_code": None,
    }
    return {**stored, **over}


def test_outcome_in_force_keeps_a_draft_from_another_protocol_as_stored():
    draft = _stored()
    assert pr.outcome_in_force(draft, CRITERIA, not_reported="decisive_first", protocol_fingerprint="sha256:" + "1" * 64) == ("EXCLUDE", "EXC-01")
    assert pr.outcome_in_force(draft, CRITERIA, not_reported="decisive_first", protocol_fingerprint="sha256:" + "2" * 64) == ("MAYBE", None)


def test_outcome_in_force_keeps_a_failed_or_empty_draft_unclear():
    same = "sha256:" + "1" * 64
    failed = _stored(validators=[{"name": "schema", "ok": False}])
    assert pr.outcome_in_force(failed, CRITERIA, not_reported="decisive_first", protocol_fingerprint=same) == ("MAYBE", None)
    empty = _stored(output=None, validators=[{"name": "schema", "ok": False}])
    assert pr.outcome_in_force(empty, CRITERIA, not_reported="decisive_first", protocol_fingerprint=same) == ("MAYBE", None)
    no_checks = _stored(validators=[])
    assert pr.outcome_in_force(no_checks, CRITERIA, not_reported="decisive_first", protocol_fingerprint=same) == ("MAYBE", None)


def test_with_drafts_the_methods_paragraph_says_how_they_are_counted_once(tmp_path):
    """Review round 2: the positive case of the drafts sentence (drafts and a rule amendment)."""
    from test_export_api import BASE as EXPORT_BASE
    from test_export_api import client_for, decide, publish
    from test_screening_events import _build

    ws = _build(tmp_path, method=dict(BLOCK))
    client = client_for(ws)
    assert client.post(f"{EXPORT_BASE}/method/amendments",
                       json={"field": "not_reported", "value": "decisive_first", "confirm": True}).status_code == 200
    context = ev.load_context(ws)
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    study = sorted(context.study_batch)[0]
    pr.submit_proposal(
        ws, study_id=study, title="t", abstract="a", output={"criteria": [], "cannot_decide": True},
        protocol=protocol, protocol_fingerprint=context.protocol_fingerprint,
        provenance={"task_version": "screen-v1", "model": "m", "driver": "mcp", "prompt_sha256": "sha256:" + "0" * 64},
        created_at="2026-11-20T10:00:00Z",
    )
    decide(ws)
    publish(ws)
    text = client_for(ws).get(f"{EXPORT_BASE}/methods").json()["paragraph"]
    sentence = "The agent's drafts are counted under the not-reported rule in force at publication"
    assert text.count(sentence) == 1
    assert "No AI model proposed decisions for this screening" not in text
    assert text.index("after the protocol was signed") < text.index(sentence)
