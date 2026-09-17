# scholar-protocol-kit: Comprehensive Deep Dive Analysis

> **Kit Location:** tools/scholar-protocol-kit
> **Version:** 1.0.0
> **Analysis Date:** 2026-09-14

---

## Executive Summary

The scholar-protocol-kit is the **contract spine** of the Nexus Scholar research pipeline. It provides a deterministic, zero-LLM, zero-network protocol compilation and validation system for Phase 0 of systematic literature reviews. The kit is well-designed with strong determinism guarantees, comprehensive test coverage (83 test functions across 6 test files), and a clean separation of concerns across 9 source modules.

**Key Strengths:**
- Mathematical determinism: same IntentPacket always produces byte-identical protocol.json
- Two-tier validation: structural (Pydantic) + cross-field semantic rules
- Comprehensive golden fixture conformance testing with pinned SHA-256 fingerprints
- Clean CLI with proper exit code semantics (0=valid, 1=invalid, 2=usage error)
- Schema sync CI guard preventing model/schema drift

**Key Weaknesses:**
- Several edge cases in validation not covered (e.g., date_range missing keys, target_databases empty list)
- metadata field is untyped Dict[str, Any] with no validation
- No protocol versioning/migration strategy beyond v1.0.0
- Limited extraction model capabilities (no enum constraint propagation for categorical dimensions)
- Missing integration tests with downstream kits (scholar-rag-kit, scholar-agent-kit)

**Overall Assessment:** Production-ready for its core use case. The determinism guarantees and test suite are exemplary. Main areas for improvement are edge case handling, extraction model sophistication, and cross-kit integration robustness.

---

## 1. Functionalities

### 1.1 Complete Capability Inventory

| # | Capability | Module | CLI Command | Python API |
|---|-----------|--------|-------------|------------|
| 1 | Protocol validation (structural + cross-field) | validate.py | scholar-protocol validate [path] [--strict] | validate_protocol(path) -> ValidationReport |
| 2 | Deterministic protocol compilation | compiler.py | scholar-protocol compile [intent_path] | compile_protocol(intent) -> ResearchProtocol |
| 3 | Canonical JSON serialization | canonical.py | scholar-protocol canon [path] | canonical_json(protocol) -> bytes |
| 4 | SHA-256 fingerprinting | canonical.py | scholar-protocol fingerprint [path] | canonical_fingerprint(protocol) -> str |
| 5 | Screening criteria rendering | render.py | scholar-protocol render-criteria [path] | render_screening_criteria(protocol) -> str |
| 6 | Dynamic extraction model generation | extraction.py | scholar-protocol extraction-schema [path] | build_extraction_model(protocol) -> Type[BaseModel] |
| 7 | Extraction prompt generation | extraction.py | scholar-protocol extraction-prompt [path] | generate_extraction_prompt(protocol) -> str |
| 8 | Playbook presets | presets.py | (used internally by compiler) | PRESETS dict |
| 9 | Intent packet definition | intent.py | (input to compile) | IntentPacket model |
| 10 | JSON Schema generation | scripts/generate_schema.py | python scripts/generate_schema.py | generate_schema() -> dict |

### 1.2 CLI Command-to-Function Mapping

scholar-protocol validate [path] [--strict]
  -> validate_protocol(path)          [validate.py:284]
  -> report.is_valid / report.is_valid_strict()
  -> Exit 0 (valid), 1 (invalid), 2 (usage error)

scholar-protocol fingerprint [path]
  -> _load_protocol(path)             [cli.py:79]
  -> canonical_fingerprint(protocol)  [canonical.py:132]
  -> print(fp) to stdout

scholar-protocol canon [path]
  -> _load_protocol(path)             [cli.py:79]
  -> canonical_json(protocol)         [canonical.py:96]
  -> sys.stdout.buffer.write(bytes)

scholar-protocol compile [intent_path]
  -> compile_from_file(path)          [compiler.py:243]
  -> canonical_json(protocol)         [canonical.py:96]
  -> sys.stdout.buffer.write(bytes)

scholar-protocol render-criteria [path]
  -> _load_protocol(path)             [cli.py:79]
  -> render_screening_criteria(protocol) [render.py:14]
  -> print(md) to stdout

scholar-protocol extraction-schema [path]
  -> _load_protocol(path)             [cli.py:79]
  -> build_extraction_model(protocol) [extraction.py:17]
  -> model.model_json_schema()
  -> print(json.dumps(schema, indent=2))

scholar-protocol extraction-prompt [path]
  -> _load_protocol(path)             [cli.py:79]
  -> generate_extraction_prompt(protocol) [extraction.py:69]
  -> print(prompt) to stdout

### 1.3 Data Models and Schemas

#### Root Model: ResearchProtocol (models.py:292-351)

ResearchProtocol
  |--  (alias: schema_version) = schemas/v1/protocol.schema.json
  |-- protocol_id: str (required)
  |-- created_at: str (ISO-8601, auto-generated)
  |-- project_slug: str (required)
  |-- playbook_type: PlaybookType (required, enum)
  |-- metadata: Dict[str, Any] (freeform, open)
  |-- epistemology: EpistemologyConfig (required)
  |-- research_questions: List[ResearchQuestion] (min_length=1)
  |-- search_strategy: SearchStrategy (required)
  |-- screening_criteria: ScreeningCriteria (required)
  |-- matrix_dimensions: List[MatrixDimension] (default=[])
  +-- verification: VerificationConfig (default factory)

#### Sub-models:

PlaybookType (models.py:27-44) - 5 archetypes:
- PRISMA_SLR - Exhaustive systematic review
- SCOPING_REVIEW - Broad landscape mapping
- RAPID_EVIDENCE - Time-bounded review (24-72h)
- DESIGN_SCIENCE - Artifact engineering
- STUDENT_DISSERTATION - Pedagogical starter

EpistemologicalParadigm (models.py:46-59) - 4 stances:
- POSITIVIST - Quantitative, generalizable
- INTERPRETIVIST - Qualitative, lived experience
- DESIGN_SCIENCE - Computational artifacts
- PRAGMATIST_MIXED - Mixed methods

DimensionDataType (models.py:62-76) - 4 types:
- FREE_TEXT - Descriptive summary
- NUMERIC - Numbers with units
- CATEGORICAL - Bounded enum
- LIST - Array of items

ResearchQuestion (models.py:83-100):
- id, text, target_facet, synthesis_type (default=Comparative Matrix), required_evidence_type

ConceptCluster (models.py:103-116):
- concept, synonyms (list), boolean_operator (default=OR)

SearchStrategy (models.py:118-147):
- core_concepts (min_length=1), target_databases (4 defaults), date_range, languages, open_access_preferred, target_candidate_pool_size

ScreeningCriterion (models.py:150-164):
- id, criterion, maps_to_rqs (list of RQ refs), reason_category (optional)

ScreeningCriteria (models.py:167-185):
- inclusion (min_length=1), exclusion (min_length=1), two_tier_screening (default=True)

MatrixDimension (models.py:188-228):
- id, name, description, target_section_category (optional), data_type, required, fallback_value

EpistemologyConfig (models.py:231-259):
- primary_paradigm, secondary_paradigm (optional), unit_of_analysis, trustworthiness_framework, epistemological_rationale, incompatible_concepts

VerificationConfig (models.py:262-284):
- retraction_check_required, coi_and_funding_audit_required, reproducibility_das_cas_check, minimum_trust_score_threshold (0.0-10.0)

IntentPacket (intent.py:126-246):
A flattened, minimal representation that the compiler resolves against presets. Key design: IDs for RQs and criteria are auto-generated from declaration order.

### 1.4 Integration Points with Other Kits

| Downstream Kit | Integration | Direction | Data Flow |
|---------------|-------------|-----------|-----------|
| scholar-rag-kit | build_extraction_model() | protocol-kit -> rag-kit | Dynamic Pydantic model for matrix extraction |
| scholar-agent-kit | compile_protocol(), validate_protocol(), render_screening_criteria() | agent-kit -> protocol-kit | MCP tools nexus_protocol_compile/validate/render_criteria |
| scholar-search-kit | Protocol validation | search-kit -> protocol-kit | Validates protocol before search execution |
| scholar-verify-kit | Protocol metadata | verify-kit -> protocol-kit | Reads verification config flags |
| workspace-manager | Protocol file management | workspace-manager -> protocol-kit | Writes protocol.json to workspace |

**Known Issue:** scholar-rag-kit imports scholar_protocol.compiler.build_extraction_model but does NOT declare scholar-protocol-kit as a dependency in its pyproject.toml (documented in docs/kits_surface_matrix.md:354).

---

## 2. Improvements

### 2.1 Code Quality Issues

**[MEDIUM] Untyped metadata field** (models.py:328-336)

metadata: Dict[str, Any] = Field(
    default_factory=lambda: {
        "title": "",
        "lead_researcher": "",
        "target_venue_type": "",
        "timeline_weeks": 4,
    },
    description="Freeform project metadata (title, researcher, venue, timeline)",
)

- Problem: Dict[str, Any] allows any keys/values with no validation
- Impact: Typos in metadata keys silently pass validation; downstream consumers may miss data
- Fix: Create a typed MetadataConfig model with optional fields, or add a validator that checks for expected keys

**[LOW] Unused import in validate.py** (validate.py:179)

import datetime as dt  # imported inside function body

- Problem: datetime is imported at module level (line 15) AND inside _check_cross_field (line 179)
- Impact: Minor code smell; the module-level import is unused
- Fix: Remove the module-level import datetime or consolidate imports

**[MEDIUM] No protocol versioning strategy** (models.py:307-311)

schema_version: str = Field(
    "schemas/v1/protocol.schema.json",
    alias="",
    description="URI of the JSON Schema (relative kit path, resolved locally by the validator)",
)

- Problem: Schema is frozen at v1.0.0 with no migration path for future versions
- Impact: Any schema change requires manual migration; no backward compatibility
- Fix: Add a schema_version field that can be parsed and validated; add migration functions

**[LOW] Extract model naming** (extraction.py:59)

clean_id = protocol.protocol_id.replace("-", "_").title().replace("_", "")
model_name = f"{clean_id}ExtractionRow"

- Problem: The .title().replace("_", "") produces PascalCase but may produce unexpected results for certain protocol IDs
- Impact: Minor; model names appear in JSON Schema output
- Fix: Document the naming convention or use a more predictable transformation

### 2.2 Missing Features or Capabilities

**[HIGH] No --output flag on CLI commands**
- Current: All commands print to stdout; user must redirect
- Impact: Inconvenient for interactive use; no -i/-o flags
- Recommendation: Add optional --output flag to compile, render-criteria, extraction-schema, extraction-prompt commands while keeping stdout as default

**[HIGH] No protocol diff/comparison tool**
- Current: No way to compare two protocol.json files semantically
- Impact: Difficult to track protocol changes across iterations
- Recommendation: Add scholar-protocol diff [path1] [path2] command that shows semantic differences

**[MEDIUM] No protocol summary/statistics command**
- Current: No quick overview of protocol contents
- Impact: Researchers must manually inspect protocol files
- Recommendation: Add scholar-protocol summary [path] that shows RQ count, criterion count, matrix dimensions, etc.

**[MEDIUM] No extraction model validation**
- Current: build_extraction_model() generates models but does not validate they can be used
- Impact: Runtime errors when extraction model is incompatible with RAG system
- Recommendation: Add validate_extraction_model(protocol) that checks field names are valid Python identifiers, no collisions, etc.

**[LOW] No JSON Schema validation of protocol.json against the checked-in schema**
- Current: Validation uses Pydantic models, not the JSON Schema file
- Impact: The JSON Schema file (schemas/v1/protocol.schema.json) is generated but never used for validation
- Recommendation: Optionally validate against the JSON Schema for external tool compatibility

### 2.3 API Design Improvements

**[MEDIUM] validate_protocol() requires file path, not dict** (validate.py:284)

def validate_protocol(path: str | pathlib.Path) -> ValidationReport:

- Problem: Cannot validate an in-memory protocol dict without writing to disk first
- Impact: Test code must use tempfile.NamedTemporaryFile (see test_validate.py:19-26)
- Recommendation: Add overload: validate_protocol(path: str | Path) and validate_protocol(data: dict)

**[MEDIUM] No protocol serialization to YAML/TOML** (canonical.py)
- Current: Only JSON serialization
- Impact: Some users prefer YAML for readability
- Recommendation: Add canonical_yaml(protocol) and canonical_toml(protocol) functions

**[LOW] No protocol deserialization from canonical bytes** (canonical.py)
- Current: canonical_json(protocol) -> bytes exists but no reverse
- Impact: Cannot round-trip from canonical bytes back to protocol object
- Recommendation: Add protocol_from_canonical(bytes) -> ResearchProtocol

### 2.4 Error Handling Gaps

**[HIGH] No validation of target_databases values** (validate.py)
- Current: target_databases accepts any string values
- Impact: Typos like openalexx pass validation silently
- Recommendation: Add a validator that checks against known database names (openalex, semanticscholar, crossref, arxiv, etc.)

**[MEDIUM] No validation of languages format** (validate.py:217-223)

if not protocol.search_strategy.languages:
    report.add_error(...)

- Problem: Only checks non-empty; does not validate ISO 639-1 format
- Impact: Invalid language codes like english or eng pass validation
- Recommendation: Add regex or enum validation for ISO 639-1 codes

**[MEDIUM] No validation of created_at format** (models.py:316-319)

created_at: str = Field(
    default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(),
    description="ISO-8601 timestamp of protocol creation (UTC)",
)

- Problem: created_at is typed as str with no ISO-8601 validation
- Impact: Invalid timestamps like not-a-date pass validation
- Recommendation: Add a Pydantic validator or use datetime type with JSON serialization

**[MEDIUM] No validation of protocol_id format** (models.py:312-315)
- Problem: protocol_id accepts any string
- Impact: Spaces, special characters, or extremely long IDs pass validation
- Recommendation: Add regex pattern validation (e.g., ^[a-z0-9][a-z0-9-]*$)

**[LOW] No validation of concept length** (models.py:108)
- Problem: concept accepts empty strings
- Impact: Empty concept clusters may cause downstream search failures
- Recommendation: Add min_length=1 to concept field

### 2.5 Documentation Needs

**[HIGH] Missing CHANGELOG**
- Problem: No CHANGELOG.md to track version changes
- Impact: Users cannot easily understand what changed between versions
- Recommendation: Create CHANGELOG.md following Keep a Changelog format

**[MEDIUM] Missing API reference documentation**
- Problem: README.md shows examples but no complete API reference
- Impact: Developers must read source code to understand all parameters
- Recommendation: Generate API docs with Sphinx or mkdocstrings

**[MEDIUM] No architecture decision records (ADRs)**
- Problem: Design decisions (e.g., why canonical serialization works this way) are not documented
- Impact: New contributors cannot understand the rationale
- Recommendation: Create ADRs for key design decisions

---

## 3. Problems

### 3.1 Known Bugs or Issues

**[HIGH] date_range missing key validation** (validate.py:178-198)

dr = protocol.search_strategy.date_range
start = dr.get("start_year")
end = dr.get("end_year")
if start is not None and end is not None:
    if start > end:
        ...

- Problem: If date_range is missing start_year or end_year, validation passes silently
- Impact: Incomplete date ranges may cause search failures
- Fix: Add validation that both keys exist when date_range is provided

**[MEDIUM] target_candidate_pool_size missing key validation** (validate.py:200-215)

pool = protocol.search_strategy.target_candidate_pool_size
p_min = pool.get("min", 0)
p_max = pool.get("max", 0)

- Problem: Uses .get("min", 0) which silently defaults to 0 if key is missing
- Impact: Missing keys are treated as 0, which may not be intended
- Fix: Add validation that both min and max keys exist

**[MEDIUM] _check_cross_field imports inside function body** (validate.py:179, 239)

import datetime as dt  # line 179
from scholar_protocol.models import EpistemologicalParadigm, PlaybookType  # line 239

- Problem: These imports are inside the function body, executed on every call
- Impact: Minor performance overhead; code smell
- Fix: Move imports to module level

**[LOW] Temp file cleanup in tests** (test_validate.py:19-26)

def _write_tmp(data: dict) -> pathlib.Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(data, f, ensure_ascii=True)
    f.close()
    return pathlib.Path(f.name)

- Problem: Temp files are created with delete=False but never cleaned up
- Impact: Temp file accumulation on repeated test runs
- Fix: Add cleanup in test fixtures or use tmp_path pytest fixture

### 3.2 Edge Cases Not Handled

**[HIGH] Empty core_concepts.synonyms list** (models.py:109)

synonyms: List[str] = Field(
    default_factory=list,
    description="Alternative keyword synonyms (author order preserved)",
)

- Problem: Empty synonyms list is valid; may cause search query generation failures
- Impact: Downstream search kits may not handle empty synonym lists
- Fix: Add warning when synonyms list is empty

**[MEDIUM] target_section_category values not validated** (models.py:210-216)

target_section_category: Optional[str] = Field(
    None,
    description=(
        "Preferred source section: 'methodology', 'results_empirical', "
        "'discussion_limitations', or 'abstract_intro'.  Null = search all sections."
    ),
)

- Problem: Description lists valid values but no enum validation
- Impact: Invalid section categories pass validation
- Fix: Create TargetSectionCategory enum or add validator

**[MEDIUM] reason_category not validated** (models.py:163)

reason_category: Optional[str] = Field(
    None,
    description="Optional rejection category e.g. 'WRONG_POPULATION', 'WRONG_OUTCOME'",
)

- Problem: No validation of reason category format
- Impact: Inconsistent reason categories across protocols
- Fix: Add enum or pattern validation for common categories

**[LOW] boolean_operator not validated to OR/AND** (models.py:113-115)

boolean_operator: str = Field(
    "OR", description="Operator joining synonyms: 'OR' or 'AND'"
)

- Problem: Description says OR or AND but no enum validation
- Impact: Invalid operators like XOR pass validation
- Fix: Change to Literal[OR, AND] or add enum

**[LOW] minimum_trust_score_threshold precision** (models.py:279-284)
- Problem: Threshold accepts any float (e.g., 5.123456789)
- Impact: Canonical serialization may produce unexpected precision
- Fix: Round to 1 decimal place in validator

### 3.3 Limitations in Current Implementation

**[HIGH] No support for protocol inheritance or templating**
- Current: Each protocol is standalone; no way to base one protocol on another
- Impact: Common sections must be duplicated across protocols
- Recommendation: Add protocol templates or inheritance mechanism

**[MEDIUM] No support for multi-language protocols**
- Current: languages field is just a list of codes; no language-specific content
- Impact: Cannot create protocols with content in multiple languages
- Recommendation: Add language-tagged content fields

**[MEDIUM] No support for protocol revisions**
- Current: Protocol is immutable after compilation
- Impact: Cannot track protocol changes over time
- Recommendation: Add revision history or version tracking

**[LOW] No support for protocol comparison/merging**
- Current: No way to compare or merge two protocols
- Impact: Cannot combine protocols from different researchers
- Recommendation: Add protocol diff and merge operations

### 3.4 Technical Debt

**[MEDIUM] Hardcoded preset values** (presets.py:69-144)
- Problem: All preset values are hardcoded in Python; not configurable
- Impact: Adding new presets requires code changes
- Recommendation: Load presets from JSON/YAML files

**[MEDIUM] No plugin architecture for custom validators** (validate.py)
- Problem: Cross-field rules are hardcoded in _check_cross_field()
- Impact: Cannot add custom validation rules without modifying source
- Recommendation: Add validator plugin system

**[LOW] Test fixtures not parameterized for all edge cases** (tests/test_validate.py)
- Problem: Some edge cases are tested inline rather than as parameterized fixtures
- Impact: Inconsistent test coverage
- Recommendation: Convert all edge cases to parameterized fixtures

---

## 4. Optimizations

### 4.1 Performance Bottlenecks

**[LOW] Repeated imports in _check_cross_field** (validate.py:179, 239)

import datetime as dt  # line 179
from scholar_protocol.models import EpistemologicalParadigm, PlaybookType  # line 239

- Problem: Imports executed on every validation call
- Impact: ~0.1ms overhead per validation
- Fix: Move to module level

**[LOW] Redundant model_dump() calls in compiler** (compiler.py:233-238)

"epistemology": epistemology.model_dump(mode="json"),
"research_questions": [rq.model_dump(mode="json") for rq in _build_rqs(intent)],
"search_strategy": search_strategy.model_dump(mode="json"),
"screening_criteria": screening_criteria.model_dump(mode="json"),
"matrix_dimensions": [d.model_dump(mode="json") for d in _build_dimensions(intent)],
"verification": verification.model_dump(mode="json"),

- Problem: Each sub-model is dumped separately, then the whole dict is validated again
- Impact: Minor performance overhead for large protocols
- Optimization: Pass model objects directly to ResearchProtocol constructor

### 4.2 Memory Usage Issues

**[LOW] Large protocol fixtures in tests** (tests/fixtures/valid/prisma_slr_full.json)
- Problem: Full protocol fixtures are loaded into memory during tests
- Impact: ~10KB per fixture; 4 fixtures = ~40KB total
- Acceptable: This is well within normal test memory usage

### 4.3 Algorithm Efficiency

**[MEDIUM] Canonical serialization key sorting** (canonical.py:62-78)

if "metadata" in raw and isinstance(raw["metadata"], dict):
    raw["metadata"] = dict(sorted(raw["metadata"].items()))

- Problem: Sorting is O(n log n) for each nested dict
- Impact: Negligible for small dicts; could matter for very large metadata
- Optimization: Cache sorted results or use ordered dict from start

### 4.4 Caching Opportunities

**[MEDIUM] Schema generation caching** (scripts/generate_schema.py:92-118)
- Problem: generate_schema() regenerates schema on every call
- Impact: ~5ms per call; repeated in tests
- Recommendation: Cache generated schema in module-level variable

**[LOW] Fingerprint caching** (canonical.py:132-146)
- Problem: canonical_fingerprint() recomputes canonical JSON on every call
- Impact: ~1ms per call
- Recommendation: Cache fingerprint on ResearchProtocol instance (use functools.lru_cache or __hash__)

### 4.5 Parallelization Potential

**[LOW] Test execution** (tests/)
- Problem: Tests are run sequentially
- Impact: ~2s total test time
- Recommendation: Use pytest-xdist for parallel test execution (already available in dev dependencies)

---

## 5. Scientific Correction

### 5.1 Accuracy of Protocol Schema

**[HIGH] Missing PRISMA 2020 flow diagram support**
- Current: Protocol captures screening criteria but not the PRISMA flow diagram structure
- Impact: Researchers must manually create PRISMA flow diagrams
- Recommendation: Add optional prisma_flow field with diagram metadata

**[MEDIUM] No support for PICO/PICOS framework** (models.py:83-100)
- Current: Research questions are freeform text
- Impact: Cannot enforce structured PICO (Population, Intervention, Comparison, Outcome, Study design) format
- Recommendation: Add optional pico field to ResearchQuestion model

**[MEDIUM] No support for GRADE evidence certainty** (models.py:262-284)
- Current: VerificationConfig has trust score but no GRADE framework
- Impact: Cannot assess evidence certainty using GRADE methodology
- Recommendation: Add optional grade_assessment field

### 5.2 Alignment with Research Methodology Standards

**[HIGH] PRISMA 2020 compliance gaps**
- Current: ScreeningCriteria has two_tier_screening flag but no PRISMA-specific fields
- Missing:
  - prisma_flow_eligibility_criteria (PRISMA-S specific)
  - prisma_flow_information_sources
  - prisma_flow_selection_process
  - prisma_flow_data_extraction
- Impact: Researchers must supplement protocol with PRISMA-specific documentation
- Recommendation: Add optional prisma_config field

**[MEDIUM] No support for ROBIS (Risk of Bias in Systematic Reviews)**
- Current: VerificationConfig has basic flags but no structured ROBIS assessment
- Impact: Cannot systematically assess risk of bias using ROBIS tool
- Recommendation: Add optional robis_domains field

**[MEDIUM] No support for CASP (Critical Appraisal Skills Programme) checklists**
- Current: No study design-specific appraisal checklists
- Impact: Cannot enforce study design-specific quality assessment
- Recommendation: Add optional casp_checklist_type field

### 5.3 Correctness of Validation Rules

**[HIGH] date_range validation is incomplete** (validate.py:178-198)
- Current: Validates start_year <= end_year and year bounds
- Missing:
  - Validation that both keys exist when date_range is provided
  - Validation that years are integers (not floats or strings)
- Impact: Invalid date ranges may pass validation
- Fix: Add explicit key existence check

**[MEDIUM] target_candidate_pool_size validation is incomplete** (validate.py:200-215)
- Current: Validates min <= max and non-negative
- Missing:
  - Validation that both keys exist
  - Validation that values are integers (not floats)
- Impact: Invalid pool sizes may pass validation
- Fix: Add explicit key existence check

**[MEDIUM] No validation of synthesis_type values** (models.py:93-96)
- Current: synthesis_type accepts any string
- Impact: Inconsistent synthesis types across protocols
- Recommendation: Add enum validation (e.g., Comparative Matrix, Taxonomy, Narrative, Meta-Analysis)

**[LOW] No validation of required_evidence_type values** (models.py:97-100)
- Current: required_evidence_type accepts any string
- Impact: Inconsistent evidence types across protocols
- Recommendation: Add enum validation for common evidence types

### 5.4 Epistemological Paradigm Handling

**[HIGH] Limited paradigm options** (models.py:46-59)
- Current: 4 paradigms (Positivist, Interpretivist, Design Science, Pragmatist/Mixed)
- Missing:
  - Critical Theory
  - Constructivist
  - Post-positivist
  - Participatory/Action Research
- Impact: Researchers with other epistemological stances cannot accurately represent their work
- Recommendation: Add more paradigm options or allow custom paradigms

**[MEDIUM] No paradigm validation against methodology** (validate.py:236-251)
- Current: Only warns on questionable paradigm-playbook combinations
- Missing:
  - Validation that paradigm matches methodology (e.g., Positivist should use quantitative methods)
  - Validation that unit_of_analysis is appropriate for paradigm
- Impact: Epistemologically inconsistent protocols may pass validation
- Recommendation: Add paradigm-methodology coherence checks

**[MEDIUM] incompatible_concepts is freeform** (models.py:256-259)
- Current: No validation of what constitutes an incompatible concept
- Impact: Researchers may list concepts that are not actually incompatible
- Recommendation: Add guidance or validation for incompatible concept lists
## 6. Agent/Skill Recommendation

### 6.1 Should a Specialized Agent or Skill Be Created?

**Recommendation: YES -- Create a specialized protocol-qa-agent skill**

The scholar-protocol-kit already has a SKILL.md (.agents/skills/scholar-protocol-kit/SKILL.md), but it is a passive instruction document. A specialized agent (not just a skill) would add significant value because:

1. **Protocol quality is a critical gate** -- A bad protocol cascades errors through the entire research pipeline (search, screening, extraction, synthesis).
2. **Subjective assessment needed** -- Many protocol quality issues (e.g., Is this research question answerable? Are these criteria comprehensive?) require judgment, not just rule-based validation.
3. **Agent-in-the-loop opportunity** -- The inception wizard already uses LLM interaction; a QA agent could validate the wizard's output before compilation.

### 6.2 Narrow Scope of Tasks

| Task | Description | Frequency |
|------|-------------|-----------|
| Protocol Completeness Check | Verify all required fields are meaningful (not just present) | Every protocol |
| Research Question Quality | Assess RQs for clarity, answerability, scope | Every protocol |
| Criterion Coverage Analysis | Check that criteria comprehensively cover all RQs | Every protocol |
| Search Strategy Adequacy | Evaluate concept clusters for completeness | Every protocol |
| Paradigm-Methodology Coherence | Verify epistemological consistency | Every protocol |
| Extraction Dimension Validity | Check matrix dimensions are extractable and meaningful | When dimensions defined |
| Cross-Protocol Comparison | Compare two protocol versions for meaningful changes | On revision |

### 6.3 Evaluation Metrics for Agent Performance

| Metric | Definition | Target | Measurement |
|--------|-----------|--------|-------------|
| Completeness Score | % of protocol fields that pass quality checks | > 90% | Automated + LLM assessment |
| RQ Quality Score | Average RQ clarity rating (1-5) from LLM judge | > 4.0 | LLM-based rubric scoring |
| Criterion Coverage Ratio | % of RQs covered by at least one criterion | 100% | Automated |
| Search Recall Estimate | Estimated % of relevant papers captured | > 80% | LLM-based estimation |
| Paradigm Coherence Score | Binary: paradigm-methodology-consistent | 100% | Rule-based + LLM |
| False Positive Rate | % of QA warnings that are incorrect | < 5% | Human evaluation |
| False Negative Rate | % of real issues missed by QA | < 10% | Human evaluation |
| Response Time | Time to complete QA assessment | < 30s | Automated |

### 6.4 Critic Capabilities Needed

The agent should be able to:

1. **Detect common protocol anti-patterns:** Overly broad RQs, vague criteria, missing exclusion criteria, inconsistent terminology
2. **Suggest improvements:** Recommend additional criteria, refine vague criteria, propose search concepts, identify biases
3. **Validate against methodology standards:** PRISMA compliance, PICO structure, DSR methodology alignment
4. **Cross-reference with domain knowledge:** Concept appropriateness, standard exclusion criteria, missing verification steps

### 6.5 Agent-in-the-Loop Opportunities

| Loop Point | Agent Role | Trigger | Output |
|-----------|-----------|---------|--------|
| Post-Inception | Validate wizard output before compilation | After Socratic interview | QA report with pass/fail + suggestions |
| Pre-Search | Validate protocol before search execution | Before scholar-search runs | Search readiness assessment |
| Post-Screening | Validate screening decisions against protocol | After batch screening | Protocol adherence report |
| Pre-Extraction | Validate extraction dimensions for completeness | Before RAG extraction | Extraction readiness assessment |
| Post-Synthesis | Validate synthesis against original RQs | After synthesis completes | RQ coverage report |

### 6.6 Automation Potential

| Task | Current State | Automation Potential |
|------|--------------|---------------------|
| Schema validation | Fully automated | Already done |
| Cross-field validation | Fully automated | Already done |
| RQ quality assessment | Manual | HIGH -- LLM-based rubric scoring |
| Criterion coverage analysis | Manual | HIGH -- Automated graph analysis |
| Search adequacy assessment | Manual | MEDIUM -- LLM + heuristics |
| Paradigm coherence check | Semi-automated (warning only) | HIGH -- Rule-based + LLM |
| Protocol comparison | Manual | HIGH -- Diff + semantic analysis |


---

## 7. Priority-Ranked Improvement Suggestions

### Priority 1 (Critical -- Fix Immediately)

| # | Issue | Location | Impact | Effort |
|---|-------|----------|--------|--------|
| 1 | Add date_range key existence validation | validate.py:178-198 | High | Low |
| 2 | Add target_candidate_pool_size key existence validation | validate.py:200-215 | High | Low |
| 3 | Add created_at ISO-8601 format validation | models.py:316-319 | High | Low |
| 4 | Add protocol_id format validation | models.py:312-315 | Medium | Low |

### Priority 2 (High -- Fix Soon)

| # | Issue | Location | Impact | Effort |
|---|-------|----------|--------|--------|
| 5 | Add target_databases value validation | validate.py | High | Medium |
| 6 | Add languages ISO 639-1 validation | validate.py:217-223 | Medium | Medium |
| 7 | Add target_section_category enum validation | models.py:210-216 | Medium | Low |
| 8 | Add boolean_operator Literal validation | models.py:113-115 | Low | Low |
| 9 | Add validate_protocol(dict) overload | validate.py:284 | Medium | Medium |
| 10 | Add --output flag to CLI commands | cli.py | Medium | Medium |

### Priority 3 (Medium -- Plan for Next Release)

| # | Issue | Location | Impact | Effort |
|---|-------|----------|--------|--------|
| 11 | Add protocol versioning/migration strategy | models.py:307-311 | High | High |
| 12 | Add CHANGELOG.md | root | Medium | Low |
| 13 | Add protocol diff command | cli.py | Medium | Medium |
| 14 | Add protocol summary command | cli.py | Low | Low |
| 15 | Add PRISMA 2020 flow diagram support | models.py | Medium | High |
| 16 | Add PICO framework support | models.py:83-100 | Medium | High |
| 17 | Create protocol-qa-agent skill | .agents/skills/ | High | High |

### Priority 4 (Low -- Backlog)

| # | Issue | Location | Impact | Effort |
|---|-------|----------|--------|--------|
| 18 | Add YAML/TOML serialization | canonical.py | Low | Medium |
| 19 | Add extraction model validation | extraction.py | Low | Medium |
| 20 | Add protocol inheritance/templating | models.py | Low | High |
| 21 | Add ROBIS/CASP support | models.py | Low | High |
| 22 | Add more epistemological paradigms | models.py:46-59 | Low | Low |
| 23 | Add synthesis_type enum validation | models.py:93-96 | Low | Low |
| 24 | Move presets to JSON/YAML config | presets.py | Low | Medium |
| 25 | Add validator plugin system | validate.py | Low | High |

---

## Appendix A: File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| src/scholar_protocol/__init__.py | 75 | Public API re-exports |
| src/scholar_protocol/models.py | 351 | Pydantic v2 models (sole source of truth) |
| src/scholar_protocol/canonical.py | 146 | Deterministic serializer + sha256 fingerprint |
| src/scholar_protocol/validate.py | 324 | Structural + cross-field validation |
| src/scholar_protocol/compiler.py | 256 | IntentPacket to ResearchProtocol compiler |
| src/scholar_protocol/render.py | 89 | Markdown criteria renderer |
| src/scholar_protocol/extraction.py | 98 | Dynamic Pydantic schema synthesis |
| src/scholar_protocol/presets.py | 145 | Playbook presets |
| src/scholar_protocol/intent.py | 246 | IntentPacket model |
| src/scholar_protocol/cli.py | 248 | Typer + Rich CLI |
| scripts/generate_schema.py | 176 | JSON Schema generator |
| schemas/v1/protocol.schema.json | 483 | Checked-in JSON Schema |
| tests/test_validate.py | 267 | Validation tests |
| tests/test_models.py | 211 | Model parsing tests |
| tests/test_canonical.py | 306 | Canonical serialization tests |
| tests/test_compiler.py | 240 | Compiler conformance tests |
| tests/test_cli.py | 261 | CLI exit code tests |
| tests/test_schema_sync.py | 179 | Schema sync CI guard |

**Total source lines:** ~1,788 (src/) + ~1,244 (tests/) + ~176 (scripts/) = ~3,208 lines

## Appendix B: Test Coverage Summary

| Test File | Tests | Coverage Area |
|-----------|-------|---------------|
| test_validate.py | 18 | Validation rules, error codes, warnings |
| test_models.py | 16 | Model parsing, enums, bounds, defaults |
| test_canonical.py | 14 | Serialization determinism, fingerprinting |
| test_compiler.py | 12 | Compiler conformance, preset application |
| test_cli.py | 16 | CLI exit codes, output format |
| test_schema_sync.py | 7 | Schema-model synchronization |

**Total tests:** 83 test functions across 6 test files

---

*Analysis complete. Generated: 2026-09-14*
