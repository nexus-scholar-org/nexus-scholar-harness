"""INC-22: every screening criterion is shown verbatim and accepted one by one.

The wizard prints each inclusion and exclusion criterion with its source and
asks for each. A criterion the wizard wrote itself (from the proof answer, or
the paradigm's default exclusions) needs an explicit yes: its prompt defaults to
no. A criterion the researcher typed defaults to yes. A rejected criterion is
not compiled. If a side would be left empty, the wizard asks for one, because a
protocol needs at least one of each (decision 2026-11-08, criteria acceptance).
"""

from __future__ import annotations

import json

from conftest import GENESIS_TS
from rich.console import Console

from scholar_harness.inception import run_wizard
from scholar_harness.inception import wizard as wizard_mod

TOPIC = "Can an on-device computer-vision weed-detection pipeline achieve real-time frame rates on embedded hardware?"
PROOF = "mIoU and FPS measurements on a public benchmark suite"
PROOF_CRITERION = f"Reports the gold-standard proof — {PROOF}"
DS_DEFAULT_EXCLUSION = "Mere descriptive opinion without an evaluated computational artifact."


class RecordingResponder:
    """Scripted answers; records every confirm prompt with its default."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.confirms: list[tuple[str, bool]] = []

    def _take(self):
        assert self.answers, "RecordingResponder exhausted"
        return self.answers.pop(0)

    def text(self, message, default=""):
        return self._take()

    def confirm(self, message, default=True):
        self.confirms.append((message, default))
        return self._take()

    def choice(self, message, choices, default=""):
        return self._take()

    def multi(self, message, choices):
        return self._take()

    def num_if_valid(self, raw):
        return self._take()


def _answers(out_of_scope, criteria_answers, tail_extra=()):
    return [
        TOPIC,
        "Design Science",
        "DESIGN_SCIENCE",
        False,                      # secondary paradigm?
        "embedded crop-field RGB cameras",
        PROOF,
        out_of_scope,
        False,                      # date window?
        "Can an on-device weed detector run in real time?",
        False,                      # RQ2?
        "weed detection",
        "",                         # synonyms
        False,                      # manual inclusion?
        False,                      # manual exclusion?
        *criteria_answers,
        False,                      # matrix?
        True,                       # verification?
        "Weed Detection Criteria Test",
        "Dr. Mouadh",
        "",
        "",
        None,
        True,                       # emit
        *tail_extra,
    ]


def _run(tmp_path, monkeypatch, answers):
    recorder = Console(record=True, width=400)
    monkeypatch.setattr(wizard_mod, "console", recorder)
    responder = RecordingResponder(answers)
    result = run_wizard(responder, tmp_path, genesis_timestamp=GENESIS_TS)
    assert responder.answers == [], f"unused answers: {responder.answers}"
    return result, responder, recorder.export_text()


def _criterion_prompts(responder):
    return [(m, d) for m, d in responder.confirms if m.startswith("Accept")]


def test_every_criterion_is_shown_verbatim_with_its_source(tmp_path, monkeypatch):
    result, responder, text = _run(
        tmp_path, monkeypatch, _answers("closed-source models, pre-2022 studies", [True, True, True])
    )

    assert PROOF_CRITERION in text
    assert "closed-source models" in text and "pre-2022 studies" in text
    assert "written by the wizard from your proof answer" in text
    assert "your out-of-scope answer" in text

    prompts = _criterion_prompts(responder)
    assert len(prompts) == 3
    # The generated criterion needs an explicit yes; the typed ones accept on Enter.
    assert [d for _m, d in prompts] == [False, True, True]

    intent = result["intent"]
    assert [c["criterion"] for c in intent["inclusion_criteria"]] == [PROOF_CRITERION]
    assert [c["criterion"] for c in intent["exclusion_criteria"]] == ["closed-source models", "pre-2022 studies"]


def test_a_rejected_criterion_is_not_compiled(tmp_path, monkeypatch):
    result, _responder, _text = _run(
        tmp_path, monkeypatch, _answers("closed-source models, pre-2022 studies", [True, True, False])
    )

    ws = tmp_path / "workspaces" / result["slug"]
    intent = json.loads((ws / "intent.json").read_text(encoding="utf-8"))
    assert [c["criterion"] for c in intent["exclusion_criteria"]] == ["closed-source models"]
    assert "pre-2022 studies" not in (ws / "SCREENING_CRITERIA.md").read_text(encoding="utf-8")


def test_the_paradigm_default_exclusion_is_shown_and_can_be_refused(tmp_path, monkeypatch):
    # No out-of-scope answer: the wizard proposes the paradigm's default exclusion.
    # Refusing both generated criteria leaves each side empty, so the wizard asks for one.
    answers = _answers("", [False, False, "Evaluates on embedded hardware", "Simulation-only studies"])
    result, responder, text = _run(tmp_path, monkeypatch, answers)

    assert DS_DEFAULT_EXCLUSION in text
    assert "the Design Science paradigm's default" in text
    assert [d for _m, d in _criterion_prompts(responder)] == [False, False]

    intent = result["intent"]
    assert [c["criterion"] for c in intent["inclusion_criteria"]] == ["Evaluates on embedded hardware"]
    assert [c["criterion"] for c in intent["exclusion_criteria"]] == ["Simulation-only studies"]


def test_the_ready_panel_lists_every_accepted_criterion(tmp_path, monkeypatch):
    _result, _responder, text = _run(
        tmp_path, monkeypatch, _answers("closed-source models", [True, True])
    )
    # The pre-emit panel is printed last before the emit prompt; it names each
    # criterion in full, not as a count.
    panel = text[text.rindex("Weed Detection Criteria Test"):]
    assert PROOF_CRITERION in panel
    assert "closed-source models [OUT_OF_SCOPE]" in panel
    assert "inclusion: 1" not in panel


def test_the_scaffold_only_placeholder_fingerprint_does_not_move(tmp_path):
    """INC-22 changes the wizard, not the deterministic placeholder protocol.

    The golden value was computed at `a273fc6` (main before M4a) with the same
    title and timestamp.
    """
    from scholar_harness.inception.genesis import scaffold_placeholder_workspace

    result = scaffold_placeholder_workspace(
        tmp_path / "ws", "Placeholder Golden", agent="test", timestamp="2026-09-06T12:00:00+00:00"
    )
    assert result["protocol_fingerprint"] == "sha256:b7ea8b86a7fc4a2f69f325fca79953a8b9784e0cab02590722bd74dc4587f973"
