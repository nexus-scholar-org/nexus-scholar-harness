"""Central pytest configuration and shared fixtures for nexus-scholar-harness tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

GENESIS_TS = "2026-09-06T12:00:00+00:00"

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


@pytest.fixture
def sample_protocol() -> Dict[str, Any]:
    """A canonical minimal protocol dictionary conforming to IntentPacket/Protocol."""
    return {
        "protocol_id": "proto-test-sample",
        "genesis_timestamp": "2026-09-01T00:00:00+00:00",
        "project_slug": "test-sample-workspace",
        "playbook_type": "DESIGN_SCIENCE",
        "title": "Empirical Benchmark of Literature Harness",
        "lead_researcher": "Dr. Agent",
        "unit_of_analysis": "Research Pipelines",
        "epistemological_rationale": "Empirical validation of research workflows.",
        "research_questions": [
            {
                "text": "What is the throughput and fidelity of literature pipelines?",
                "target_facet": "evaluation_metrics",
                "required_evidence_type": "Quantitative Benchmark",
            }
        ],
        "core_concepts": [
            {"concept": "Research Interface", "synonyms": ["orchestrator", "harness", "agent"]}
        ],
        "inclusion_criteria": [
            {
                "criterion": "Evaluates systematic literature workflows and empirical benchmarks",
                "maps_to_rqs": ["RQ1"],
            }
        ],
        "exclusion_criteria": [
            {
                "criterion": "Informal opinion pieces or non-peer-reviewed blog posts",
                "maps_to_rqs": ["RQ1"],
            }
        ],
        "target_venues": ["ICSE", "FSE", "ASE", "ESEC/FSE"],
        "search_strings": ["systematic literature review AND automation"],
    }


@pytest.fixture
def sample_papers() -> List[Dict[str, Any]]:
    """List of sample paper dictionaries with workspace_id, title, authors, year, abstract."""
    return [
        {
            "workspace_id": "SCI-000001",
            "title": "Attention Is All You Need",
            "authors": ["Ashish Vaswani", "Noam Shazeer"],
            "year": 2017,
            "doi": "10.5555/3295222.3295349",
            "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
        },
        {
            "workspace_id": "SCI-000002",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "authors": ["Jacob Devlin", "Ming-Wei Chang"],
            "year": 2018,
            "doi": "10.18653/v1/N19-1423",
            "abstract": "We introduce a new language representation model called BERT.",
        },
        {
            "workspace_id": "SCI-000003",
            "title": "Language Models are Few-Shot Learners",
            "authors": ["Tom Brown", "Benjamin Mann"],
            "year": 2020,
            "doi": "10.48550/arXiv.2005.14165",
            "abstract": "Recent work has demonstrated substantial gains on many NLP tasks and benchmarks.",
        },
    ]


@pytest.fixture
def sample_verified(sample_papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """List of sample verified.json entries."""
    verified = []
    for paper in sample_papers:
        item = dict(paper)
        item["verification_status"] = "VERIFIED"
        item["screening_eligible"] = True
        verified.append(item)
    return verified


@pytest.fixture
def tmp_workspace(tmp_path: Path, sample_protocol: Dict[str, Any], sample_papers: List[Dict[str, Any]]) -> Path:
    """Scaffold a temporary workspace directory with canonical folders and basic metadata."""
    ws = tmp_path / "test-workspace"
    ws.mkdir(parents=True, exist_ok=True)
    for sub in ("literature", "literature/screening", "extracted", "synthesis", "audit", "pdfs"):
        (ws / sub).mkdir(parents=True, exist_ok=True)

    (ws / "protocol.json").write_text(json.dumps(sample_protocol, indent=2), encoding="utf-8")
    (ws / "literature" / "verified.json").write_text(json.dumps(sample_papers, indent=2), encoding="utf-8")
    (ws / "literature" / "included.json").write_text(json.dumps(sample_papers[:2], indent=2), encoding="utf-8")
    (ws / "project.json").write_text(
        json.dumps(
            {
                "project_slug": sample_protocol["project_slug"],
                "title": sample_protocol["title"],
                "phase": "initialized",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return ws
