---
name: scholar-protocol-kit
description: Instructions for using the scholar-protocol-kit Python API and CLI to compile, validate, fingerprint, render criteria, and build dynamic extraction models from research protocols.
---

# `scholar-protocol-kit` Skill Instructions

You are the research protocol and methodology compiler specialist of the Nexus Scholar Suite. Your role is to compile frozen researcher intent packets into canonical, deterministic `protocol.json` contracts, validate protocols against standard JSON schemas, calculate SHA-256 integrity fingerprints, render human-readable `SCREENING_CRITERIA.md`, and dynamically compile Pydantic models for downstream RAG matrix extraction.

## Core Capabilities

1. **Deterministic Protocol Compiler (`compile_protocol`)**:
   - Resolves `IntentPacket` specifications against archetype presets (`PRISMA_SLR`, `SCOPING_REVIEW`, `RAPID_EVIDENCE`, `DESIGN_SCIENCE`, `STUDENT_DISSERTATION`).
   - Assigns sequential deterministic identifiers (`RQ1`, `RQ2`, `INC-01`, `EXC-01`).
   - Zero LLM calls and zero network calls during compilation for reproducible builds.
2. **Canonical Serializer & Fingerprinting (`canonical_fingerprint`)**:
   - Canonicalizes JSON keys alphabetically with deterministic whitespace.
   - Computes reproducible SHA-256 checksums ensuring protocol immutability across phases.
3. **Criteria Document Renderer (`render_screening_criteria`)**:
   - Translates `protocol.json` into a clean, human-readable `SCREENING_CRITERIA.md` with explicit inclusion/exclusion reason categories.
4. **Dynamic Extraction Model Builder (`build_extraction_model`)**:
   - Generates dynamic Pydantic `BaseModel` classes from `protocol.matrix_dimensions` to enforce strict JSON schemas on downstream LLM extraction in `scholar-rag-kit`.

---

## CLI Usage

All commands are executed via `uv run`:

### 1. Compile Intent Packet to Protocol
```bash
# Compile intent.json into canonical protocol.json with SHA-256 fingerprinting
uv run scholar-protocol compile \
  -i workspaces/<project-slug>/intent.json \
  -o workspaces/<project-slug>/protocol.json \
  --fingerprint
```

### 2. Validate Protocol Schema & Fingerprint
```bash
# Validate conformance against protocol.schema.json
uv run scholar-protocol validate workspaces/<project-slug>/protocol.json

# Calculate and display SHA-256 canonical hash
uv run scholar-protocol fingerprint workspaces/<project-slug>/protocol.json
```

### 3. Render Human-Readable Screening Criteria
```bash
# Render markdown criteria
uv run scholar-protocol render-criteria \
  workspaces/<project-slug>/protocol.json \
  -o workspaces/<project-slug>/SCREENING_CRITERIA.md
```

### 4. Export Dynamic Extraction Schemas
```bash
# Export dynamic JSON schema for matrix extraction
uv run scholar-protocol extraction-schema workspaces/<project-slug>/protocol.json

# Export formatted LLM system extraction prompt fragment
uv run scholar-protocol extraction-prompt workspaces/<project-slug>/protocol.json
```

---

## Python API

```python
from pathlib import Path
from scholar_protocol.intent import IntentPacket, RQIntent, ConceptClusterIntent, CriterionIntent, MatrixDimensionIntent
from scholar_protocol.models import PlaybookType
from scholar_protocol.compiler import compile_protocol
from scholar_protocol.serializer import canonical_serialize, canonical_fingerprint
from scholar_protocol.render import render_screening_criteria
from scholar_protocol.extraction import build_extraction_model

# 1. Construct Intent Packet
intent = IntentPacket(
    protocol_id="proto-20260901-benchmark",
    genesis_timestamp="2026-09-01T00:00:00+00:00",
    project_slug="benchmark-review",
    playbook_type=PlaybookType.DESIGN_SCIENCE,
    title="Benchmark Evaluation for Code Synthesis",
    lead_researcher="Dr. Researcher",
    unit_of_analysis="Code generation models",
    epistemological_rationale="Empirical performance quantification",
    research_questions=[
        RQIntent(
            text="What pass@1 rates are achieved across benchmarks?",
            target_facet="evaluation_metrics",
            required_evidence_type="Quantitative Benchmark"
        )
    ],
    core_concepts=[
        ConceptClusterIntent(concept="Code Generation", synonyms=["code synthesis"])
    ],
    inclusion_criteria=[
        CriterionIntent(criterion="Evaluates on public benchmarks", maps_to_rqs=["RQ1"])
    ],
    exclusion_criteria=[
        CriterionIntent(criterion="Non-English editorial", reason_category="LANGUAGE", maps_to_rqs=["RQ1"])
    ],
    matrix_dimensions=[
        MatrixDimensionIntent(id="sample_size", name="Sample Size", description="Number of benchmarks evaluated")
    ]
)

# 2. Compile to validated ResearchProtocol
protocol = compile_protocol(intent)

# 3. Canonical Fingerprinting
raw_json = canonical_serialize(protocol)
sha256_hash = canonical_fingerprint(protocol)
print(f"Protocol Fingerprint: {sha256_hash}")

# 4. Render Markdown Criteria
markdown_criteria = render_screening_criteria(protocol)

# 5. Build Dynamic Extraction Model for RAG
ExtractionModel = build_extraction_model(protocol)
```
