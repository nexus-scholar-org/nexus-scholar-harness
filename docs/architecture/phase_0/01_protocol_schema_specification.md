# Phase 0: `protocol.json` Schema Specification

> **Specification Version:** 1.0.0  
> **Status:** Standardized Architecture Specification  
> **Location in Workspace:** `workspaces/<project-slug>/protocol.json`

---

## 1. Overview & Role in the Harness

The `protocol.json` file is the **machine-readable contract** generated at the end of Phase 0. It encapsulates the full epistemological stance, refined research questions, boolean search strategy, screening rules, dynamic extraction dimensions, and trust verification parameters.

Every subsequent kit in the Nexus Scholar suite reads this file as its single source of truth.

---

## 2. Complete Pydantic v2 Implementation

```python
"""Data models for Phase 0 protocol.json specification."""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PlaybookType(str, Enum):
    """Canonical research playbook archetypes."""
    PRISMA_SLR = "PRISMA_SLR"                         # Exhaustive, systematic (PRISMA 2020)
    SCOPING_REVIEW = "SCOPING_REVIEW"                 # Broad landscape mapping (JBI / Arksey & O'Malley)
    RAPID_EVIDENCE_ASSESSMENT = "RAPID_EVIDENCE"     # Time-bounded high-precision (24-72h REA)
    DESIGN_SCIENCE_BENCHMARK = "DESIGN_SCIENCE"       # Artifact engineering & empirical benchmarking (Hevner)
    STUDENT_DISSERTATION = "STUDENT_DISSERTATION"     # Pedagogical starter / dissertation review


class EpistemologicalParadigm(str, Enum):
    """Core epistemological stances."""
    POSITIVIST = "Positivist"                         # Quantitative, generalizable, statistical
    INTERPRETIVIST = "Interpretivist"                 # Qualitative, human meaning, lived experience
    DESIGN_SCIENCE = "Design Science"                 # Computational artifacts, systems utility
    PRAGMATIST_MIXED = "Pragmatist / Mixed Methods"   # Metric triangulation & operational problem-solving


class DimensionDataType(str, Enum):
    """Supported data types for extracted matrix dimensions."""
    FREE_TEXT = "free_text"          # Descriptive summary (e.g. "Limitations", "Method summary")
    NUMERIC = "numeric"              # Numbers with units (e.g. "N = 450", "37ms latency", "pass@1 = 78.4%")
    CATEGORICAL = "categorical"      # Bounded enum (e.g. "RCT", "Observational", "A/B Benchmark")
    LIST = "list"                    # Array of items (e.g. ["Python", "C++", "Go"])


class ResearchQuestion(BaseModel):
    """A formal, refined research question."""
    id: str = Field(..., description="Unique identifier e.g. 'RQ1', 'RQ2'")
    text: str = Field(..., description="Formal refined research question")
    target_facet: str = Field(..., description="e.g. 'evaluation_metrics', 'effect_sizes', 'limitations'")
    synthesis_type: str = Field("Comparative Matrix", description="e.g. 'Comparative Matrix', 'Taxonomy', 'Narrative'")
    required_evidence_type: str = Field(..., description="e.g. 'Quantitative telemetry', 'Verbatim interviews'")


class ConceptCluster(BaseModel):
    """Conceptual keyword cluster with boolean operator for query expansion."""
    concept: str = Field(..., description="Primary conceptual term")
    synonyms: List[str] = Field(default_factory=list, description="Alternative keyword synonyms")
    boolean_operator: str = Field("OR", description="Operator between synonyms: 'OR' or 'AND'")


class SearchStrategy(BaseModel):
    """Federated multi-provider search strategy."""
    core_concepts: List[ConceptCluster] = Field(..., min_length=1)
    target_databases: List[str] = Field(
        default=["openalex", "semanticscholar", "crossref", "arxiv"],
        description="Target academic databases"
    )
    date_range: Dict[str, Optional[int]] = Field(
        default_factory=lambda: {"start_year": 2020, "end_year": 2026}
    )
    languages: List[str] = Field(default=["en"])
    open_access_preferred: bool = Field(True)
    target_candidate_pool_size: Dict[str, int] = Field(
        default_factory=lambda: {"min": 500, "max": 2000}
    )


class ScreeningCriterion(BaseModel):
    """Screening rule for inclusion or exclusion."""
    id: str = Field(..., description="e.g. 'INC-01', 'EXC-01'")
    criterion: str = Field(..., description="Explicit condition description")
    maps_to_rqs: List[str] = Field(default_factory=list, description="Associated RQs")
    reason_category: Optional[str] = Field(None, description="e.g. 'WRONG_POPULATION', 'WRONG_OUTCOME'")


class ScreeningCriteriaConfig(BaseModel):
    """Two-tier PRISMA screening configuration."""
    inclusion: List[ScreeningCriterion] = Field(..., min_length=1)
    exclusion: List[ScreeningCriterion] = Field(..., min_length=1)
    two_tier_screening: bool = Field(
        True, description="Tier 1 = Title/Abstract, Tier 2 = Full Text"
    )


class MatrixDimension(BaseModel):
    """Dynamic, domain-customizable matrix extraction dimension."""
    id: str = Field(..., description="Unique slug e.g. 'sample_size', 'benchmark_dataset'")
    name: str = Field(..., description="Human-readable column header e.g. 'Sample Size (N)'")
    description: str = Field(..., description="Guidance to LLM/RAG extractor on what specific text to extract")
    target_section_category: Optional[str] = Field(
        None,
        description="Target section: 'methodology', 'results_empirical', 'discussion_limitations', or 'abstract_intro'"
    )
    data_type: DimensionDataType = Field(DimensionDataType.FREE_TEXT)
    required: bool = Field(False, description="If True, flags studies that fail to report this dimension")
    fallback_value: str = Field("Not Reported", description="Default if paper does not state this metric")


class EpistemologyConfig(BaseModel):
    """Epistemological stance, rigor standard, and vocabulary boundaries."""
    primary_paradigm: EpistemologicalParadigm
    secondary_paradigm: Optional[EpistemologicalParadigm] = None
    unit_of_analysis: str = Field(..., description="e.g. 'Software developer commit diffs', 'Patient clinical cohort'")
    trustworthiness_framework: str = Field(..., description="e.g. 'PRISMA 2020', 'Lincoln & Guba', 'Hevner DSR'")
    epistemological_rationale: str = Field(..., description="Why this paradigm was chosen")
    incompatible_concepts: List[str] = Field(
        default_factory=list,
        description="Concepts or terms strictly invalid under this paradigm (suppressed from search/synthesis)"
    )


class VerificationConfig(BaseModel):
    """Phase 4 Trust and verification audit flags."""
    retraction_check_required: bool = Field(True)
    coi_and_funding_audit_required: bool = Field(True)
    reproducibility_das_cas_check: bool = Field(True)
    minimum_trust_score_threshold: float = Field(5.0, ge=0.0, le=10.0)


class ResearchProtocol(BaseModel):
    """The master Phase 0 research protocol specification."""
    schema_version: str = Field("1.0.0", alias="$schema")
    protocol_id: str = Field(..., description="Unique protocol identifier e.g. 'proto-20260901-ai-dev'")
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    project_slug: str = Field(..., description="Workspace slug e.g. 'ai-developer-productivity'")
    playbook_type: PlaybookType
    
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "title": "",
            "lead_researcher": "",
            "target_venue_type": "",
            "timeline_weeks": 4
        }
    )
    
    epistemology: EpistemologyConfig
    research_questions: List[ResearchQuestion] = Field(..., min_length=1)
    search_strategy: SearchStrategy
    screening_criteria: ScreeningCriteriaConfig
    matrix_dimensions: List[MatrixDimension] = Field(default_factory=list)
    verification: VerificationConfig = Field(default_factory=VerificationConfig)
```

---

## 3. Sample JSON Output

```json
{
  "$schema": "schemas/v1/protocol.schema.json",
  "protocol_id": "proto-20260901-llm-code-bench",
  "created_at": "2026-09-01T01:30:00Z",
  "project_slug": "llm-code-benchmarks",
  "playbook_type": "DESIGN_SCIENCE",
  "metadata": {
    "title": "Benchmarking Large Language Models in Code Generation: A Design Science Review",
    "lead_researcher": "Researcher",
    "target_venue_type": "ACM / IEEE Transactions",
    "timeline_weeks": 6
  },
  "epistemology": {
    "primary_paradigm": "Design Science",
    "unit_of_analysis": "Computational artifacts & automated test suite pass rates",
    "trustworthiness_framework": "Hevner Design Science Research Guidelines",
    "epistemological_rationale": "Evaluating computational utility and benchmark accuracy of code synthesis models.",
    "incompatible_concepts": ["Qualitative opinion surveys without code evaluation"]
  },
  "research_questions": [
    {
      "id": "RQ1",
      "text": "What automated benchmarks are utilized in empirical literature to measure LLM code generation pass rates?",
      "target_facet": "evaluation_metrics",
      "synthesis_type": "Comparative Matrix",
      "required_evidence_type": "Quantitative benchmark scores (pass@k, execution accuracy)"
    },
    {
      "id": "RQ2",
      "text": "What is the measured performance difference between dense retrieval and structural graph-boosted RAG for code synthesis?",
      "target_facet": "empirical_benchmark",
      "synthesis_type": "Comparative Matrix",
      "required_evidence_type": "Ablation delta tables and latency measurements"
    }
  ],
  "search_strategy": {
    "core_concepts": [
      {
        "concept": "Large Language Model Code Generation",
        "synonyms": ["neural code synthesis", "LLM code completion", "Copilot", "code LLMs"],
        "boolean_operator": "OR"
      },
      {
        "concept": "Benchmark Evaluation",
        "synonyms": ["HumanEval", "MBPP", "pass@1", "execution accuracy", "ablation study"],
        "boolean_operator": "OR"
      }
    ],
    "target_databases": ["arxiv", "semanticscholar", "crossref", "openalex"],
    "date_range": {
      "start_year": 2021,
      "end_year": 2026
    },
    "languages": ["en"],
    "open_access_preferred": true,
    "target_candidate_pool_size": {
      "min": 100,
      "max": 400
    }
  },
  "screening_criteria": {
    "two_tier_screening": true,
    "inclusion": [
      {
        "id": "INC-01",
        "criterion": "Presents a novel computational model, prompt architecture, or RAG pipeline for code generation",
        "maps_to_rqs": ["RQ1"]
      },
      {
        "id": "INC-02",
        "criterion": "Evaluates performance quantitatively against public standard benchmark datasets",
        "maps_to_rqs": ["RQ1", "RQ2"]
      }
    ],
    "exclusion": [
      {
        "id": "EXC-01",
        "criterion": "Position papers or non-peer-reviewed blog posts without empirical code evaluation",
        "reason_category": "NO_EVALUATION"
      },
      {
        "id": "EXC-02",
        "criterion": "Studies focusing purely on natural language translation without code execution",
        "reason_category": "WRONG_OUTCOME"
      }
    ]
  },
  "matrix_dimensions": [
    {
      "id": "model_arch",
      "name": "Model Architecture & Parameters",
      "description": "Extract foundation model name and parameter size (e.g. Llama-3-70B, GPT-4o, DeepSeek-Coder).",
      "target_section_category": "methodology",
      "data_type": "categorical",
      "required": true
    },
    {
      "id": "benchmark_datasets",
      "name": "Benchmark Dataset(s)",
      "description": "Extract specific test suites used (HumanEval, MBPP, SWE-bench, DS-1000).",
      "target_section_category": "methodology",
      "data_type": "list",
      "required": true
    },
    {
      "id": "pass_k_accuracy",
      "name": "pass@1 / Execution Accuracy",
      "description": "Extract numerical pass@1 or unit test pass percentages reported.",
      "target_section_category": "results_empirical",
      "data_type": "numeric",
      "required": true
    },
    {
      "id": "declared_limitations",
      "name": "Declared Limitations & Latency",
      "description": "Extract engineering constraints, compute requirements, or index latency.",
      "target_section_category": "discussion_limitations",
      "data_type": "free_text",
      "required": false
    }
  ],
  "verification": {
    "retraction_check_required": true,
    "coi_and_funding_audit_required": true,
    "reproducibility_das_cas_check": true,
    "minimum_trust_score_threshold": 6.0
  }
}
```
