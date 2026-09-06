"""Tests for the Phase-0 Interactive Inception wizard (scholar_harness.inception)."""

import hashlib
import json

import pytest
import typer
from typer.testing import CliRunner

from scholar_harness.cli import app
from scholar_harness.inception import (
    ConceptDraft,
    RQDraft,
    Survey,
    compile_protocol_files,
    detect_leanings,
    enforce_lexicon,
    make_intent,
    recommend_playbook,
    run_wizard,
    slugify,
)

runner = CliRunner()

GENESIS_TS = "2026-09-06T12:00:00+00:00"


def build_survey(**overrides) -> Survey:
    survey = Survey(
        topic="Can an on-device weed-detection pipeline run at real-time frame rates?",
        paradigm="Design Science",
        playbook="DESIGN_SCIENCE",
        secondary_paradigm=None,
        unit_of_analysis="embedded crop-field RGB cameras",
        proof="mIoU and FPS on a public benchmark suite with ablations",
        out_of_scope=["closed-source models"],
        languages=["en"],
        start_year=None,
        end_year=None,
        lead_researcher="Dr. X",
        title="On-Device Weed Detection for Embedded Agriculture",
        venue="arXiv",
        timeline_weeks=None,
        rqs=[
            RQDraft(
                text="Can an on-device weed-detection pipeline achieve real-time frame rates without sacrificing accuracy?",
                facet="artifact_performance",
                evidence="Benchmark suites, ablation studies",
            )
        ],
        concepts=[ConceptDraft(concept="weed detection", synonyms=["crop-weed segmentation"])],
        extra_inclusions=[],
        extra_exclusions=[],
        trust_score_threshold=6.0,
        matrix_dimensions=[],
    )
    for key, value in overrides.items():
        setattr(survey, key, value)
    return survey


# ---------------------------------------------------------------------------
# Stage 1: latent-intent mining
# ---------------------------------------------------------------------------


def test_detect_leanings_positivist():
    top = detect_leanings(
        "measure the statistically significant effect size of training data on model accuracy"
    )
    assert top[0][0] == "Positivist"
    assert top[0][1] >= 3


def test_detect_leanings_interpretivist():
    top = detect_leanings("how do farmers perceive and experience the adoption of uavs in daily practice")
    assert top[0][0] == "Interpretivist"


def test_detect_leanings_design_science():
    top = detect_leanings(
        "build an on-device pipeline architecture and benchmark frame-rate latency on embedded hardware"
    )
    assert top[0][0] == "Design Science"


def test_recommend_playbook_mapping():
    assert recommend_playbook("Positivist") == "PRISMA_SLR"
    assert recommend_playbook("Interpretivist") == "SCOPING_REVIEW"
    assert recommend_playbook("Design Science") == "DESIGN_SCIENCE"


def test_enforce_lexicon_flags_positivist_terms():
    warnings = enforce_lexicon("Interpretivist", "sample randomization improves internal validity")
    assert warnings
    assert any("internal validity" in w for w in warnings)


def test_enforce_lexicon_silent_outside_interpretivist():
    assert enforce_lexicon("Positivist", "sample randomization") == []


def test_slugify_cleans_title():
    assert slugify("  On-Device: Weed  Detection!  ") == "on-device-weed-detection"


# ---------------------------------------------------------------------------
# Stage 4: deterministic intent packet + compilation
# ---------------------------------------------------------------------------


def test_make_intent_golden_fields():
    intent = make_intent(build_survey(), "on-device-weed-detection", GENESIS_TS)

    assert intent["protocol_id"].startswith("proto-20260906-")
    assert intent["genesis_timestamp"] == GENESIS_TS
    assert intent["project_slug"] == "on-device-weed-detection"
    assert intent["playbook_type"] == "DESIGN_SCIENCE"
    assert intent["primary_paradigm"] == "Design Science"
    assert intent["unit_of_analysis"] == "embedded crop-field RGB cameras"
    assert intent["trustworthiness_framework"] == "Hevner DSR"
    assert intent["minimum_trust_score_threshold"] == 6.0
    assert intent["retraction_check_required"] is True
    assert intent["languages"] == ["en"]

    assert len(intent["research_questions"]) == 1
    assert intent["research_questions"][0]["text"].startswith("Can an on-device weed-detection")
    assert intent["research_questions"][0]["target_facet"] == "artifact_performance"

    assert intent["core_concepts"][0]["concept"] == "weed detection"
    assert intent["core_concepts"][0]["synonyms"] == ["crop-weed segmentation"]

    assert len(intent["inclusion_criteria"]) == 1
    assert "mIoU and FPS" in intent["inclusion_criteria"][0]["criterion"]
    assert intent["inclusion_criteria"][0]["maps_to_rqs"] == ["RQ1"]

    assert intent["exclusion_criteria"][0]["reason_category"] == "OUT_OF_SCOPE"
    assert "closed-source models" in intent["exclusion_criteria"][0]["criterion"]

    assert "Design Science" in intent["epistemological_rationale"]
    assert "embedded crop-field RGB cameras" in intent["epistemological_rationale"]


def test_intent_compiles_deterministically(tmp_path):
    intent = make_intent(build_survey(), "det-compile-workspace", GENESIS_TS)
    ws = tmp_path / "ws"
    ws.mkdir()

    first = compile_protocol_files(ws, intent)
    first_bytes = (ws / "protocol.json").read_bytes()
    second = compile_protocol_files(ws, intent)

    assert first["protocol_fingerprint"] == second["protocol_fingerprint"]
    assert (ws / "protocol.json").read_bytes() == first_bytes
    assert (ws / "intent.json").exists()
    assert (ws / "SCREENING_CRITERIA.md").exists()

    hex_digest = hashlib.sha256(first_bytes).hexdigest()
    assert first["protocol_fingerprint"] == f"sha256:{hex_digest}"

    criteria = (ws / "SCREENING_CRITERIA.md").read_text(encoding="utf-8")
    assert "On-Device Weed Detection" in criteria
    assert "EXC-01" in criteria
    assert "INC-01" in criteria
    assert "Minimum Trust Score: 6.0" in criteria


# ---------------------------------------------------------------------------
# Full wizard: scripted responder, offline end-to-end
# ---------------------------------------------------------------------------


class ScriptedResponder:
    """Pre-scripted answers to the wizard prompts (one per call, in order)."""

    sequenceless = True

    def __init__(self, answers):
        self.answers = list(answers)

    def _take(self):
        if not self.answers:
            raise AssertionError(f"ScriptedResponder exhausted; {len(self.answers)} answers left")
        return self.answers.pop(0)

    def text(self, message, default=""):
        return self._take()

    def confirm(self, message, default=True):
        return self._take()

    def choice(self, message, choices, default=""):
        return self._take()

    def multi(self, message, choices):
        return self._take()

    def num_if_valid(self, raw):
        return self._take()


E2E_ANSWERS = [
    "Can an on-device computer-vision weed-detection pipeline achieve real-time frame rates on embedded hardware without sacrificing classification accuracy?",
    "Design Science",          # paradigm choice
    "DESIGN_SCIENCE",          # playbook choice
    False,                     # add secondary paradigm?
    "embedded crop-field RGB cameras running weed-detection models",
    "mIoU and FPS measurements on a public benchmark suite with ablation studies",
    "closed-source models, pre-2022 studies",
    False,                     # set date window?
    "Can an on-device weed-detection pipeline achieve real-time frame rates on embedded hardware without sacrificing classification accuracy?",
    False,                     # add RQ2?
    "weed detection, on-device inference",
    "",                        # synonyms for 'weed detection'
    "",                        # synonyms for 'on-device inference'
    False,                     # manual inclusion?
    False,                     # manual exclusion?
    False,                     # configure matrix?
    True,                      # verification flags all-on?
    "On-Device Weed Detection for Embedded Agriculture",
    "Dr. Mouadh",              # lead researcher
    "",                        # venue
    "",                        # timeline
    None,                      # num_if_valid(timeline)
    True,                      # emit protocol + scaffold?]
]


def test_run_wizard_scripted_e2e(tmp_path):
    responder = ScriptedResponder(E2E_ANSWERS)
    result = run_wizard(responder, tmp_path, genesis_timestamp=GENESIS_TS)

    assert result["slug"] == "on-device-weed-detection-for-embedded-agriculture"
    assert result["playbook"] == "DESIGN_SCIENCE"
    assert result["paradigm"] == "Design Science"

    ws = tmp_path / "workspaces" / result["slug"]
    assert ws.is_dir()
    assert (ws / "project.json").exists()
    assert (ws / "intent.json").exists()
    assert (ws / "protocol.json").exists()
    assert (ws / "SCREENING_CRITERIA.md").exists()

    # Deterministic fingerprint matches the canonical bytes on disk
    expected = "sha256:" + hashlib.sha256((ws / "protocol.json").read_bytes()).hexdigest()
    assert result["protocol_fingerprint"] == expected

    # Let the deterministic compiler be the source of truth: re-compile intent
    intent = json.loads((ws / "intent.json").read_text(encoding="utf-8"))
    assert intent["genesis_timestamp"] == GENESIS_TS

    # Genesis audit event present in the append-only journal
    journal = (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(journal) >= 2
    genesis = next(evt for evt in map(json.loads, journal) if evt["action"] == "GENESIS")
    assert genesis["status"] == "SUCCESS"
    assert genesis["agent_or_tool"] == "scholar-harness/inception"
    assert any("protocol.json" in out for out in genesis["outputs"])

    # INDEX.md maintained by the workspace-manager logger
    assert (ws / "INDEX.md").exists()


def test_run_wizard_no_scaffold_aborts_without_writing(tmp_path):
    answers = E2E_ANSWERS[:-1] + [True]  # last confirm is the emit gate
    with pytest.raises(typer.Exit):
        run_wizard(ScriptedResponder(answers), tmp_path, genesis_timestamp=GENESIS_TS, no_scaffold=True)
    assert not (tmp_path / "workspaces").exists()


def test_inception_command_registered():
    result = runner.invoke(app, ["inception", "--help"])
    assert result.exit_code == 0
    assert "Socratic methodology interview" in result.stdout
    assert "--no-scaffold" in result.stdout
    assert "--root" in result.stdout