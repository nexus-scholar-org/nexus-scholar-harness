"""M11b part D: the two method questions of Inception's step 5 (DoD 18, 18b, 18c; answers 8 and 12).

Draft visibility is pre-selected "after you decide" (a proposal); the not-reported rule has
**no default** (answer 8): ``METHOD_RULE_UNCHOSEN`` blocks step 5, Review and genesis until
one of the three is chosen. The choice travels in ``intent.json`` and the compiler copies it, so a
later search amendment does not see a method change (DoD 18b). The terminal wizard asks with no
default, and a scripted run needs ``--not-reported`` (answer 12).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest
import typer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "console"))
from test_inception_api import BASE, _client, _draft  # noqa: E402

from scholar_harness.inception import steps, wizard  # noqa: E402
from scholar_harness.inception.genesis import compile_intent  # noqa: E402


@pytest.fixture
def root(tmp_path):
    folder = tmp_path / "root"
    folder.mkdir()
    return folder


def _unchosen() -> dict:
    draft = _draft()
    draft.pop("method_not_reported", None)
    return draft


def _create(client, draft: dict) -> dict:
    created = client.post(f"{BASE}/drafts", json={"draft": draft})
    assert created.status_code == 201, created.text
    return created.json()


def _save(client, sid: str, draft: dict):
    record = client.get(f"{BASE}/drafts/{sid}").json()
    return client.put(f"{BASE}/drafts/{sid}", json={"draft": draft, "base_updated_at": record["updated_at"]})


# --- DoD 18: the fields, the blocker, genesis ------------------------------------------------


def test_a_new_draft_stores_the_rule_unchosen_and_visibility_after_you_decide(root):
    client = _client(root)
    record = _create(client, {"topic": "edge AI"})
    assert record["draft"]["method_not_reported"] is None
    assert record["draft"]["method_blinding"] == "reveal_after_decision"
    got = client.get(f"{BASE}/drafts/{record['session_id']}").json()["draft"]
    assert (got["method_not_reported"], got["method_blinding"]) == (None, "reveal_after_decision")


def test_the_two_fields_round_trip_and_a_value_outside_the_enums_is_refused(root):
    client = _client(root)
    sid = _create(client, _unchosen())["session_id"]
    saved = _save(client, sid, {**_unchosen(), "method_not_reported": "decisive_first", "method_blinding": "show"})
    assert saved.status_code == 200, saved.text
    assert (saved.json()["draft"]["method_not_reported"], saved.json()["draft"]["method_blinding"]) == ("decisive_first", "show")
    bad = _save(client, sid, {**_unchosen(), "method_not_reported": "include"})
    assert bad.status_code == 422 and bad.json()["detail"]["code"] == "DRAFT_INVALID"
    assert "method_not_reported" in json.dumps(bad.json()["detail"])


def test_a_chosen_rule_cannot_be_unset_and_a_save_without_the_field_keeps_it(root):
    client = _client(root)
    sid = _create(client, {**_unchosen(), "method_not_reported": "exclude"})["session_id"]
    unset = _save(client, sid, {**_unchosen(), "method_not_reported": None})
    assert unset.status_code == 422 and unset.json()["detail"]["code"] == "DRAFT_INVALID"
    # A screen from before part D sends no method fields: the stored choice is kept.
    kept = _save(client, sid, _unchosen())
    assert kept.status_code == 200 and kept.json()["draft"]["method_not_reported"] == "exclude"


def test_the_unchosen_rule_blocks_step_5_review_and_genesis_and_nothing_is_written(root):
    client = _client(root)
    sid = _create(client, _unchosen())["session_id"]
    checks = client.post(f"{BASE}/drafts/{sid}/checks", json={"step": "criteria"}).json()
    [row] = [c for c in checks["checks"] if c["check_id"] == "METHOD_RULE_UNCHOSEN"]
    assert (row["level"], row["refusal"], row["dismissible"]) == ("blocker", "METHOD_RULE_UNCHOSEN", False)
    assert row["action"]["field"] == "method_not_reported" and row["params"]["started_before_question"] is False
    review = client.post(f"{BASE}/drafts/{sid}/checks", json={}).json()
    assert any(c["check_id"] == "METHOD_RULE_UNCHOSEN" for c in review["checks"])
    preview = client.post(f"{BASE}/preview", json={"draft": _unchosen()})
    assert preview.status_code == 422 and preview.json()["detail"]["code"] == "METHOD_RULE_UNCHOSEN"
    genesis = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert genesis.status_code == 422 and genesis.json()["detail"]["code"] == "METHOD_RULE_UNCHOSEN"
    assert not any(p.name == "protocol.json" for p in root.rglob("protocol.json"))


def test_a_draft_from_before_the_question_says_so(root):
    # A draft stored before part D has no method fields at all.
    draft = steps.parse_draft(_unchosen())
    choice = steps.method_choice(draft)
    assert (choice["chosen"], choice["started_before_question"]) == (False, True)
    with pytest.raises(steps.StepRefused) as refused:
        steps.build_intent(draft, "2026-11-21T00:00:00+00:00")
    assert refused.value.code == "METHOD_RULE_UNCHOSEN" and refused.value.details["started_before_question"] is True


def test_genesis_writes_the_choice_into_the_method_block_and_the_preview_lists_it(root):
    client = _client(root)
    draft = {**_unchosen(), "method_not_reported": "decisive_first", "method_blinding": "show"}
    preview = client.post(f"{BASE}/preview", json={"draft": draft}).json()
    assert preview["intent"]["method"] == {"blinding": "show", "not_reported": "decisive_first"}
    method = preview["protocol"]["method"]
    # The guideline the playbook implies is still stated (M7b-guideline): DESIGN_SCIENCE implies none.
    assert (method["not_reported"], method["blinding"], method["reporting"]) == ("decisive_first", "show", "none")
    sid = _create(client, draft)["session_id"]
    made = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert made.status_code == 201, made.text
    [protocol_path] = list(root.rglob("protocol.json"))
    written = json.loads(protocol_path.read_text(encoding="utf-8"))
    assert written["method"]["not_reported"] == "decisive_first" and written["method"]["blinding"] == "show"
    intent = json.loads((protocol_path.parent / "intent.json").read_text(encoding="utf-8"))
    assert intent["method"] == {"blinding": "show", "not_reported": "decisive_first"}
    # The other method fields are today's.
    assert written["method"]["dedup"] == {"doi": True, "title_similarity": 0.97, "first_author": True, "year_tolerance": 1}


def test_the_criteria_step_answers_the_options_in_the_engines_order(root):
    body = steps.run_step("criteria", _unchosen())
    assert body["method_options"] == {"blinding": ["reveal_after_decision", "show"],
                                      "not_reported": ["unclear", "decisive_first", "exclude"]}
    assert body["method"] == {"blinding": "reveal_after_decision", "not_reported": None, "chosen": False,
                              "started_before_question": True, "source": None}


# --- DoD 18b: the choice travels in the intent ---------------------------------------------------


def _amend_synonym(protocol: dict, intent: dict) -> dict:
    from scholar_harness import workspace_proposals as wp

    concept = intent["core_concepts"][0]["concept"]
    new = wp.apply_op(intent, protocol, f"core_concepts[{concept}].synonyms", "add", "weed mapping")
    return wp.compile_amendment(protocol, new)


def test_a_search_amendment_of_a_review_that_chose_decisive_first_is_not_refused(root):
    draft = steps.parse_draft({**_unchosen(), "method_not_reported": "decisive_first"})
    intent = steps.build_intent(draft, "2026-11-21T00:00:00+00:00")
    protocol = json.loads(compile_intent(intent)["protocol_bytes"])
    assert protocol["method"]["not_reported"] == "decisive_first"
    answer = _amend_synonym(protocol, intent)
    assert answer["changed"] and all(p.startswith("search_strategy") for p in answer["changed"])


def test_without_the_method_in_the_intent_the_same_amendment_is_refused(root):
    """Why the choice must be in the intent: an intent without it recompiles to the default method."""
    from scholar_harness.inception.proposals import ProposalRefused

    draft = steps.parse_draft({**_unchosen(), "method_not_reported": "decisive_first"})
    intent = steps.build_intent(draft, "2026-11-21T00:00:00+00:00")
    protocol = json.loads(compile_intent(intent)["protocol_bytes"])
    without = {k: v for k, v in intent.items() if k != "method"}
    with pytest.raises(ProposalRefused) as refused:
        _amend_synonym(protocol, without)
    assert refused.value.details.get("reason") == "outside_search"


def test_a_protocol_without_the_choice_keeps_its_fingerprint(root):
    draft = steps.parse_draft({**_unchosen(), "method_not_reported": "unclear"})
    intent = steps.build_intent(draft, "2026-11-21T00:00:00+00:00")
    with_method = compile_intent(intent)["protocol_fingerprint"]
    without = compile_intent({k: v for k, v in intent.items() if k != "method"})["protocol_fingerprint"]
    # "unclear" and "after you decide" are the model defaults, so the block is byte-identical.
    assert with_method == without


# --- the import ---------------------------------------------------------------------------------


def _file(protocol: dict) -> dict:
    import base64

    return {"kind": "file", "file_name": "protocol.json",
            "content_base64": base64.b64encode(json.dumps(protocol).encode("utf-8")).decode("ascii")}


def test_an_imported_protocol_with_a_method_block_fills_the_two_questions(root):
    from scholar_harness.inception import importer

    draft = steps.parse_draft({**_unchosen(), "method_not_reported": "exclude", "method_blinding": "show"})
    protocol = json.loads(compile_intent(steps.build_intent(draft, "2026-11-21T00:00:00+00:00"))["protocol_bytes"])
    built = importer.map_source(importer.read_source(_file(protocol), root))
    assert (built["draft"]["method_not_reported"], built["draft"]["method_blinding"]) == ("exclude", "show")
    assert {"field": "method_not_reported", "from": "method", "class": "exact"} in built["carried"]
    assert {"what": "method"} not in built["lost"]
    protocol.pop("method")
    bare = importer.map_source(importer.read_source(_file(protocol), root))
    assert "method_not_reported" not in bare["draft"]  # unchosen: the blocker applies


# --- DoD 18c: the terminal wizard -----------------------------------------------------------------


def test_the_wizard_asks_the_rule_with_no_default_until_one_is_chosen():
    asked = []

    class Responder:
        answers = ["", "nonsense", "decisive_first"]

        def choice(self, message, choices, default=""):
            asked.append((message, [c[0] for c in choices], default))
            return self.answers.pop(0)

    assert wizard.ask_not_reported(Responder()) == "decisive_first"
    assert len(asked) == 3 and all(d == "" for _m, _c, d in asked)
    assert asked[0][1] == ["unclear", "decisive_first", "exclude"]


def test_a_scripted_run_without_the_rule_is_refused_before_anything_is_written(tmp_path):
    with pytest.raises(typer.Exit) as refused:
        wizard.require_not_reported(None, scripted=True)
    assert refused.value.exit_code == 2
    with pytest.raises(typer.Exit):
        wizard.require_not_reported("include", scripted=False)
    wizard.require_not_reported(None, scripted=False)  # a terminal: the question is asked
    wizard.require_not_reported("exclude", scripted=True)
    # The init command refuses before it touches the folder.
    target = tmp_path / "new"
    import unittest.mock as mock

    with mock.patch.object(wizard, "_scripted", return_value=True), pytest.raises(typer.Exit):
        wizard.init_command("A Title", target, not_reported=None)
    assert not target.exists()


def test_the_cli_names_the_option():
    from typer.testing import CliRunner

    from scholar_harness.cli import app

    out = CliRunner().invoke(app, ["inception", "--help"], terminal_width=200).output
    # Rich colours the help where colour is forced (CI), which splits the option's name.
    assert "--not-reported" in re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", out)


@pytest.mark.slow  # H-faster-python-tests: starts a process (recorded 2026-11-23).
def test_the_wizard_writes_the_rule_into_the_intent(tmp_path):
    from conftest import E2E_ANSWERS, ScriptedResponder

    result = wizard.run_wizard(ScriptedResponder(list(E2E_ANSWERS)), tmp_path, genesis_timestamp="2026-09-01T00:00:00+00:00",
                               not_reported="exclude")
    intent = json.loads((Path(result["workspace_dir"]) / "intent.json").read_text(encoding="utf-8"))
    assert intent["method"] == {"blinding": "reveal_after_decision", "not_reported": "exclude"}
    protocol = json.loads((Path(result["workspace_dir"]) / "protocol.json").read_text(encoding="utf-8"))
    assert protocol["method"]["not_reported"] == "exclude"


# --- the assistant over MCP proposes no rule --------------------------------------------------------


def test_the_assistant_has_no_proposal_kind_for_the_rule():
    from scholar_harness.inception import proposals

    # The fields a proposal may target: the method fields are not among them (the choice is the researcher's).
    assert not {"method_not_reported", "method_blinding"} & set(proposals.STEP_OF_FIELD)


@pytest.mark.parametrize(
    "skill",
    [".agents/skills/inception-agent/SKILL.md", ".agents/plugins/nexus-scholar/skills/inception-agent/SKILL.md"],
)
def test_the_inception_agent_skill_names_the_rule_wherever_it_scripts_the_wizard(skill):
    """Review D round 1, finding 3: a scripted run without ``--not-reported`` is refused, and the rule
    is the researcher's to choose, so the skill names the flag and says to ask."""
    text = (Path(__file__).resolve().parents[2] / skill).read_text(encoding="utf-8")
    for line in text.splitlines():
        if "--auto-select" in line:
            assert "--not-reported" in line, line
            assert "Ask the researcher" in line, line


# --- Item 5, as the researcher changed it (2026-11-22, "Shown, but I must confirm it") ----------


def _imported() -> dict:
    return {**_unchosen(), "method_not_reported": "exclude", "method_not_reported_source": "imported"}


def test_an_import_marks_its_rule_imported_and_carries_the_visibility_as_it_is(root):
    from scholar_harness.inception import importer

    draft = steps.parse_draft({**_unchosen(), "method_not_reported": "exclude", "method_blinding": "show"})
    protocol = json.loads(compile_intent(steps.build_intent(draft, "2026-11-22T00:00:00+00:00"))["protocol_bytes"])
    built = importer.map_source(importer.read_source(_file(protocol), root))
    assert (built["draft"]["method_not_reported"], built["draft"]["method_not_reported_source"]) == ("exclude", "imported")
    assert built["draft"]["method_blinding"] == "show"  # the visibility question is carried as it was
    protocol.pop("method")
    bare = importer.map_source(importer.read_source(_file(protocol), root))
    assert "method_not_reported_source" not in bare["draft"]


def test_an_imported_rule_is_shown_but_blocks_step_5_review_and_genesis_until_confirmed(root):
    client = _client(root)
    sid = _create(client, _imported())["session_id"]
    choice = steps.method_choice(steps.parse_draft(_imported()))
    assert (choice["not_reported"], choice["chosen"], choice["source"]) == ("exclude", False, "imported")
    step = client.post(f"{BASE}/steps/criteria", json={"draft": _imported()}).json()
    assert step["method"]["chosen"] is False and step["method"]["not_reported"] == "exclude"
    checks = client.post(f"{BASE}/drafts/{sid}/checks", json={"step": "criteria"}).json()
    [row] = [c for c in checks["checks"] if c["check_id"] == "METHOD_RULE_UNCHOSEN"]
    assert row["message_key"] == "checks.METHOD_RULE_UNCHOSEN_imported.sentence" and row["params"]["imported"] is True
    preview = client.post(f"{BASE}/preview", json={"draft": _imported()})
    assert preview.status_code == 422 and preview.json()["detail"]["code"] == "METHOD_RULE_UNCHOSEN"
    assert preview.json()["detail"]["details"]["imported"] is True
    genesis = client.post(f"{BASE}/drafts/{sid}/genesis", json={})
    assert genesis.status_code == 422 and genesis.json()["detail"]["code"] == "METHOD_RULE_UNCHOSEN"
    assert not any(root.rglob("protocol.json"))


def test_confirming_the_imported_rule_clears_the_blocker_and_records_the_confirmation(root):
    client = _client(root)
    sid = _create(client, _imported())["session_id"]
    saved = _save(client, sid, {**_imported(), "method_not_reported_source": "confirmed"})
    assert saved.status_code == 200, saved.text
    assert (saved.json()["draft"]["method_not_reported"], saved.json()["draft"]["method_not_reported_source"]) == ("exclude", "confirmed")
    checks = client.post(f"{BASE}/drafts/{sid}/checks", json={"step": "criteria"}).json()
    assert not any(c["check_id"] == "METHOD_RULE_UNCHOSEN" for c in checks["checks"])
    preview = client.post(f"{BASE}/preview", json={"draft": saved.json()["draft"]})
    assert preview.status_code == 200 and preview.json()["intent"]["method"]["not_reported"] == "exclude"


def test_choosing_another_rule_clears_the_blocker_and_drops_the_import_mark(root):
    client = _client(root)
    sid = _create(client, _imported())["session_id"]
    # A screen that changes the value but does not name the source: a different value is a choice.
    saved = _save(client, sid, {**_unchosen(), "method_not_reported": "unclear"})
    assert saved.status_code == 200, saved.text
    assert (saved.json()["draft"]["method_not_reported"], saved.json()["draft"]["method_not_reported_source"]) == ("unclear", "chosen")
    assert steps.method_choice(steps.parse_draft(saved.json()["draft"]))["chosen"] is True
    # A save that names nothing keeps the stored rule and its source.
    kept = _save(client, sid, {k: v for k, v in _unchosen().items() if not k.startswith("method_")})
    assert kept.json()["draft"]["method_not_reported_source"] == "chosen"


def test_a_confirmed_rule_cannot_be_marked_imported_again(root):
    client = _client(root)
    sid = _create(client, _imported())["session_id"]
    assert _save(client, sid, {**_imported(), "method_not_reported_source": "confirmed"}).status_code == 200
    back = _save(client, sid, _imported())
    assert back.status_code == 422 and back.json()["detail"]["code"] == "DRAFT_INVALID"
    assert "method_not_reported_source" in json.dumps(back.json()["detail"])
