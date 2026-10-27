---
name: scholar-protocol-kit
description: Deterministic research-protocol compilation, validation, fingerprinting, and criteria rendering.
applies_to: [inception-agent, screener]
requires: [scholar-protocol]
variables: [CLI, CONFIG, KIT_ROOT, SKILL_DIR, WORKSPACE]
returns: json
layer: domain
---
# `scholar-protocol-kit` Skill Instructions

You are the research protocol and methodology compiler specialist of the Nexus Scholar Suite. Your role is to compile frozen researcher intent packets into canonical, deterministic `protocol.json` contracts, validate protocols against standard JSON schemas, calculate SHA-256 integrity fingerprints, render human-readable `SCREENING_CRITERIA.md`, and dynamically compile Pydantic models for downstream RAG matrix extraction.

## Core Capabilities

1. **Deterministic Protocol Compiler (`compile_protocol`)**:
   - Resolves `IntentPacket` specifications against archetype presets (`PRISMA_SLR`, `SCOPING_REVIEW`, `RAPID_EVIDENCE`, `DESIGN_SCIENCE`, `STUDENT_DISSERTATION`).
   - Assigns sequential deterministic identifiers (`RQ1`, `RQ2`, `INC-01`, `EXC-01`).
   - Zero LLM calls and zero network calls during compilation for reproducible builds.
2. **Canonical Serializer & Fingerprinting (`canonical_json` / `canonical_fingerprint`)**:
   - Serializes in Pydantic declaration order; only `metadata` / `date_range` /
     `target_candidate_pool_size` nested keys sorted, arrays preserved as authored.
   - Computes reproducible `sha256:<64hex>` over compact bytes (`separators=(",", ":")`,
     no trailing newline); formatting alone never changes the fingerprint.
3. **Criteria Document Renderer (`render_screening_criteria`)**:
   - Translates `protocol.json` into a clean, human-readable `SCREENING_CRITERIA.md` with explicit inclusion/exclusion reason categories.
4. **Dynamic Extraction Model Builder (`build_extraction_model`)**:
   - Generates dynamic Pydantic `BaseModel` classes from `protocol.matrix_dimensions` to enforce strict JSON schemas on downstream LLM extraction in `scholar-rag-kit`.

---

## CLI Usage

All commands are executed via `{CLI:protocol}`:

### 1. Compile Intent Packet to Protocol
```bash
# Compile intent.json into canonical protocol.json (always fingerprints; prints bytes to STDOUT)
{CLI:protocol} compile {WORKSPACE}/intent.json > {WORKSPACE}/protocol.json
```

### 2. Validate Protocol Schema & Fingerprint
```bash
# Validate conformance (structural + cross-field; --strict promotes warnings to errors)
{CLI:protocol} validate {WORKSPACE}/protocol.json
{CLI:protocol} validate {WORKSPACE}/protocol.json --strict

# Calculate and display SHA-256 canonical hash
{CLI:protocol} fingerprint {WORKSPACE}/protocol.json
```

### 3. Render Human-Readable Screening Criteria
```bash
# Render markdown criteria (prints to STDOUT; there is no -o flag)
{CLI:protocol} render-criteria \
  {WORKSPACE}/protocol.json > {WORKSPACE}/SCREENING_CRITERIA.md
```

### 4. Export Dynamic Extraction Schemas
```bash
# Export dynamic JSON schema for matrix extraction
{CLI:protocol} extraction-schema {WORKSPACE}/protocol.json

# Export formatted LLM system extraction prompt fragment
{CLI:protocol} extraction-prompt {WORKSPACE}/protocol.json
```

### 5. Golden Seeds for Search Validation

The `SearchStrategy` model supports `golden_seeds` — a list of 2-5 landmark paper DOIs that MUST appear in search results for recall validation.

```json
{
  "search_strategy": {
    "core_concepts": ["machine learning", "healthcare"],
    "golden_seeds": ["10.1000/test1", "10.1000/test2"],
    "target_candidate_pool_size": 100
  }
}
```

Golden seeds are used by the `validate-query` command in `scholar-search-kit` to verify search recall. Include them in your protocol to ensure your search strategy captures essential literature.

---

## Python API

```python
from pathlib import Path
from scholar_protocol.intent import IntentPacket, RQIntent, ConceptClusterIntent, CriterionIntent, MatrixDimensionIntent
from scholar_protocol.models import PlaybookType
from scholar_protocol.compiler import compile_protocol
from scholar_protocol.canonical import canonical_json, canonical_fingerprint
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
raw_json = canonical_json(protocol)
sha256_hash = canonical_fingerprint(protocol)
print(f"Protocol Fingerprint: {sha256_hash}")

# 4. Render Markdown Criteria
markdown_criteria = render_screening_criteria(protocol)

# 5. Build Dynamic Extraction Model for RAG
ExtractionModel = build_extraction_model(protocol)
```

---

## Verified surface, MCP mapping & knowledge

- pin: see `{CONFIG}` (`scholar-protocol-kit`
  vendored at `{KIT_ROOT:protocol}/`; canonical repo
  `nexus-scholar-org/scholar-protocol-kit` owns runtime). Matrix protocol rows are
  references only.
- **CLI never writes files** — `compile`, `validate` (+ `--strict`), `fingerprint`, `canon`,
  `render-criteria`, `extraction-schema`, `extraction-prompt` all print to STDOUT; redirect
  to persist. No `-i/-o` flags anywhere.
- **`validate_protocol` is two-tier**: Pydantic structural validation (always) **plus**
  cross-field rules (`_check_cross_field` in `validate.py:122`: duplicate RQ/criterion/
  dimension IDs, RQ refs, date/pool coherence, non-empty languages, plus non-fatal
  warnings). File mode (`validate_protocol(path)` / `validate <protocol.json>`) = full
  check; `--strict` promotes warnings to errors (`is_valid_strict`, `cli.py:99-138`).
- **Fingerprinting**: `canonical_json` emits declaration-order keys (nested `metadata` /
  `date_range` / `target_candidate_pool_size` keys sorted, arrays NOT sorted — reordering
  an array changes the fingerprint; `canonical.py:48-88`); fingerprint =
  `sha256:<64hex>` (`canonical.py:132-146`), content-based (formatting won't change it).
  Match across compile/validate.
- **MCP tools** (`server.py:272-379`): `nexus_protocol_compile` (path or JSON-string; returns
  `{status, protocol_id, fingerprint, protocol}` wrapper and does **not persist** — write
  `protocol.json` yourself), `nexus_protocol_validate` (file path **or** inline JSON —
  **both** run the full structural + cross-field rule set; `VALID` drops warnings,
  `INVALID`/`ERROR` return JSON strings, never MCP failures), `nexus_protocol_render_criteria`
  (path-only, raw markdown). `extraction-schema`/`extraction-prompt`/`canon`/`--strict` have
  **no MCP surface** — use the CLI.
- **Determinism trap**: `created_at` is pinned from `genesis_timestamp` in
  `compile_protocol` (`compiler.py:229`, `intent.py:140-146`); hand-edited protocols must
  carry an explicit valid `genesis_timestamp` or the fingerprint changes across runs.
  Compilation is pure — zero LLM/network (`compiler.py:1-7`).
- **Golden gates & derived schema**: golden `.sha256` fixtures gate serializer/preset/model
  changes (`compiler.py:16-24`; preset change = non-patch, `presets.py:7-9`); the checked-in
  `schemas/v1/protocol.schema.json` is derived from `models.py:1-10` and CI-checked
  (validator never edits it). `matrix-extract` validates only structurally.
- **Legacy**: a non-canonical or legacy/custom `protocol.json` (missing `$schema`,
  unparsable, or pre-v1 shape) must be detected and classified explicitly — never silently
  coerced into the canonical contract.
- **Routing**: search recall (`golden_seeds` + `scholar-search-kit validate-query`) →
  `scholar-search-kit` skill; matrix extraction (`build_extraction_model` → `scholar-rag-kit`) →
  `scholar-rag-kit` skill; MCP front-door (`nexus_*`) → `scholar-agent-kit` skill.
- **Integration**: `build_extraction_model` (dynamic Pydantic, `extraction.py:17-66`) feeds matrix extraction in
  `scholar-rag-kit`; `nexus_matrix_extract` imports it.

## Preflight

- `{CLI:protocol} --help` resolves on the target surface; if it does not, stop with `BLOCKED_INPUT`.
- `{WORKSPACE}` resolves to an existing canonical research workspace (contains `project.json` / `intent.json`).
- `{CONFIG}` (the kit pin manifest recording the pinned `scholar-protocol-kit` revision) resolves.

## Refusals

Codes this kit's existing content surfaces upstream:

- `BLOCKED_INPUT` — CLI fails to resolve or the required input files under `{WORKSPACE}` are missing.
- `INVALID` / `ERROR` — protocol validation outcomes (structural + cross-field rules fail); `--strict` additionally promotes warnings to errors.
- Legacy protocol detection: a non-canonical or legacy/custom `protocol.json` (missing `$schema`, unparsable, or pre-v1 shape) is detected and classified explicitly — never silently coerced into the canonical contract.
- Golden-fixture gates: golden `.sha256` fixtures gate serializer/preset/model changes (a preset change is a non-patch).

## Pointers

- Matrix extraction downstream: `scholar-rag-kit` skill (`build_extraction_model` → matrix extraction; `nexus_matrix_extract`).
- Search recall validation: `scholar-search-kit` skill (`golden_seeds` + `validate-query`).
- MCP front-door: `scholar-agent-kit` skill (`nexus_*`).
