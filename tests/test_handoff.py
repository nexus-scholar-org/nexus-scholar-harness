"""Tests for the agent handoff protocol (F3)."""

from __future__ import annotations

import json

import pytest

from scholar_harness.handoff import (
    HandoffPhase,
    HandoffState,
    PHASE_TRIGGERS,
    advance_phase,
    detect_completed_phases,
    load_handoff_state,
    next_actionable_phase,
    run_supervisor_once,
    save_handoff_state,
)


class TestHandoffPhase:
    def test_phase_order(self):
        from scholar_harness.handoff import PHASE_ORDER

        assert PHASE_ORDER[0] == HandoffPhase.INCEPTION
        assert PHASE_ORDER[-1] == HandoffPhase.COMPLETE
        assert len(PHASE_ORDER) == 7

    def test_phase_values(self):
        assert HandoffPhase.INCEPTION.value == "INCEPTION"
        assert HandoffPhase.SCREENING.value == "SCREENING"
        assert HandoffPhase.COMPLETE.value == "COMPLETE"


class TestStatePersistence:
    def test_load_default_when_no_file(self, tmp_path):
        state = load_handoff_state(tmp_path)
        assert state.current_phase == HandoffPhase.INCEPTION
        assert state.completed_phases == []
        assert state.workspace_dir == str(tmp_path.resolve())

    def test_save_and_load_roundtrip(self, tmp_path):
        state = HandoffState(
            current_phase=HandoffPhase.SCREENING,
            completed_phases=[HandoffPhase.INCEPTION],
            workspace_dir=str(tmp_path),
        )
        save_handoff_state(state, tmp_path)

        loaded = load_handoff_state(tmp_path)
        assert loaded.current_phase == HandoffPhase.SCREENING
        assert HandoffPhase.INCEPTION in loaded.completed_phases
        assert loaded.workspace_dir == str(tmp_path)

    def test_malformed_json_returns_default(self, tmp_path):
        sf = tmp_path / "handoff_state.json"
        sf.write_text("NOT VALID JSON {{{", encoding="utf-8")
        state = load_handoff_state(tmp_path)
        assert state.current_phase == HandoffPhase.INCEPTION


class TestPhaseDetection:
    def test_empty_workspace(self, tmp_path):
        completed = detect_completed_phases(tmp_path)
        assert completed == set()

    def test_inception_detected(self, tmp_path):
        (tmp_path / "intent.json").write_text("{}", encoding="utf-8")
        completed = detect_completed_phases(tmp_path)
        assert HandoffPhase.INCEPTION in completed

    def test_screening_detected(self, tmp_path):
        inc_dir = tmp_path / "literature"
        inc_dir.mkdir()
        (inc_dir / "included.json").write_text("[]", encoding="utf-8")
        completed = detect_completed_phases(tmp_path)
        assert HandoffPhase.SCREENING in completed

    def test_extraction_detected(self, tmp_path):
        rec_dir = tmp_path / "literature" / "extraction" / "merged"
        rec_dir.mkdir(parents=True)
        (rec_dir / "records.json").write_text("[]", encoding="utf-8")
        completed = detect_completed_phases(tmp_path)
        assert HandoffPhase.EXTRACTION in completed

    def test_graph_detected(self, tmp_path):
        lit_dir = tmp_path / "literature"
        lit_dir.mkdir()
        (lit_dir / "knowledge_graph.json").write_text("{}", encoding="utf-8")
        completed = detect_completed_phases(tmp_path)
        assert HandoffPhase.GRAPH in completed

    def test_synthesis_detected(self, tmp_path):
        synth_dir = tmp_path / "synthesis"
        synth_dir.mkdir()
        (synth_dir / "consensus.json").write_text("{}", encoding="utf-8")
        completed = detect_completed_phases(tmp_path)
        assert HandoffPhase.SYNTHESIS in completed

    def test_critique_detected(self, tmp_path):
        p4_dir = tmp_path / "phase4"
        p4_dir.mkdir()
        (p4_dir / "methodological_critique.md").write_text(
            "# Critique", encoding="utf-8"
        )
        completed = detect_completed_phases(tmp_path)
        assert HandoffPhase.CRITIQUE in completed


class TestAdvancePhase:
    def test_advance_moves_current_to_completed(self):
        state = HandoffState(current_phase=HandoffPhase.INCEPTION)
        state = advance_phase(state, HandoffPhase.SCREENING)
        assert state.current_phase == HandoffPhase.SCREENING
        assert HandoffPhase.INCEPTION in state.completed_phases

    def test_advance_does_not_duplicate(self):
        state = HandoffState(
            current_phase=HandoffPhase.INCEPTION,
            completed_phases=[HandoffPhase.INCEPTION],
        )
        state = advance_phase(state, HandoffPhase.SCREENING)
        assert state.completed_phases.count(HandoffPhase.INCEPTION) == 1


class TestNextActionable:
    def test_returns_next_after_detected_completed(self):
        """When INCEPTION triggers are detected, next is SCREENING."""
        state = HandoffState(
            current_phase=HandoffPhase.INCEPTION,
            completed_phases=[],
        )
        completed = {HandoffPhase.INCEPTION}
        nxt = next_actionable_phase(state, completed)
        assert nxt == HandoffPhase.SCREENING

    def test_returns_none_when_no_new_triggers(self):
        """When nothing new is detected beyond what's already advanced, NOOP."""
        state = HandoffState(
            current_phase=HandoffPhase.INCEPTION,
            completed_phases=[HandoffPhase.INCEPTION],
        )
        completed = {HandoffPhase.INCEPTION}  # already advanced past
        nxt = next_actionable_phase(state, completed)
        assert nxt is None

    def test_returns_none_when_empty(self):
        """Empty completed set → NOOP."""
        state = HandoffState(
            current_phase=HandoffPhase.INCEPTION,
            completed_phases=[],
        )
        completed: set[HandoffPhase] = set()
        nxt = next_actionable_phase(state, completed)
        assert nxt is None

    def test_skips_to_further_completed(self):
        """If INCEPTION is already advanced and SCREENING triggers exist, returns EXTRACTION."""
        state = HandoffState(
            current_phase=HandoffPhase.SCREENING,
            completed_phases=[HandoffPhase.INCEPTION],
        )
        completed = {HandoffPhase.INCEPTION, HandoffPhase.SCREENING}
        nxt = next_actionable_phase(state, completed)
        assert nxt == HandoffPhase.EXTRACTION


class TestSupervisorOnce:
    def test_noop_when_no_workspace(self, tmp_path):
        result = run_supervisor_once(tmp_path / "nonexistent")
        assert result["action"] == "NOOP"

    def test_advances_inception(self, tmp_path):
        (tmp_path / "intent.json").write_text("{}", encoding="utf-8")
        result = run_supervisor_once(tmp_path)
        assert result["action"] == "ADVANCED"
        assert result["from_phase"] == "INCEPTION"
        assert result["to_phase"] == "SCREENING"

    def test_noop_when_no_triggers(self, tmp_path):
        result = run_supervisor_once(tmp_path)
        assert result["action"] == "NOOP"

    def test_full_progression(self, tmp_path):
        # INCEPTION
        (tmp_path / "intent.json").write_text("{}", encoding="utf-8")
        r1 = run_supervisor_once(tmp_path)
        assert r1["to_phase"] == "SCREENING"

        # SCREENING
        lit = tmp_path / "literature"
        lit.mkdir()
        (lit / "included.json").write_text("[]", encoding="utf-8")
        r2 = run_supervisor_once(tmp_path)
        assert r2["to_phase"] == "EXTRACTION"

        # EXTRACTION
        rec_dir = lit / "extraction" / "merged"
        rec_dir.mkdir(parents=True)
        (rec_dir / "records.json").write_text("[]", encoding="utf-8")
        r3 = run_supervisor_once(tmp_path)
        assert r3["to_phase"] == "GRAPH"

        # GRAPH
        (lit / "knowledge_graph.json").write_text("{}", encoding="utf-8")
        r4 = run_supervisor_once(tmp_path)
        assert r4["to_phase"] == "SYNTHESIS"

        # SYNTHESIS
        synth = tmp_path / "synthesis"
        synth.mkdir()
        (synth / "consensus.json").write_text("{}", encoding="utf-8")
        r5 = run_supervisor_once(tmp_path)
        assert r5["to_phase"] == "CRITIQUE"

        # CRITIQUE
        p4 = tmp_path / "phase4"
        p4.mkdir()
        (p4 / "methodological_critique.md").write_text("# Critique", encoding="utf-8")
        r6 = run_supervisor_once(tmp_path)
        assert r6["to_phase"] == "COMPLETE"

        # All complete → NOOP
        r7 = run_supervisor_once(tmp_path)
        assert r7["action"] == "NOOP"
