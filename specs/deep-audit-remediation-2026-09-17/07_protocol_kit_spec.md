# Scholar Protocol Kit Remediation Specification

**Status:** Proposed  
**Date:** 2026-09-17  
**Owner:** scholar-protocol-kit maintainers  
**Priority:** P0 compile/validation integrity and intent fidelity  
**Scope:** `tools/scholar-protocol-kit/`, inception/compiler adapters, generated schemas/prompts, and validation contracts

## Scientific claim boundary

A compiled protocol is a declared research plan, not evidence that the plan is valid, complete, registered, PRISMA-compliant, or scientifically appropriate. Validation establishes schema and declared cross-field consistency only. Presets are suggestions with provenance, never empirical facts or silent researcher decisions. “Not reported” is an observation state and MUST NOT be invented as extracted evidence.

Identity rule: `workspace_id` scopes the corpus governed by a protocol; `study_id` identifies one included/candidate paper; `chunk_id` identifies a paper evidence unit. Protocol compilation MUST define these fields but MUST NOT interchange or fabricate them.

## Current architecture and data flow

An `IntentPacket` carries interview choices and optional overrides (`tools/scholar-protocol-kit/src/scholar_protocol/intent.py:126-244`). `compile_protocol` resolves missing intent fields against playbook presets (`compiler.py:11,126-220`; `presets.py:48-143`) and produces `ResearchProtocol`. Validation emits errors/warnings and supports strict mode (`validate.py:61-105,393-394`; `cli.py:98-133`). Canonicalization and fingerprinting serialize deterministic protocol bytes (`canonical.py:48-132`). Extraction code generates dynamic Pydantic models and prompts from matrix dimensions (`extraction.py:17-95`). CLI exposes validate, fingerprint, canon, compile, render, extraction-schema/prompt, and PRISMA checks (`cli.py:98-266`).

## Confirmed findings

1. `compile_protocol` presents compiled output as validated (`tools/scholar-protocol-kit/src/scholar_protocol/compiler.py:126-142`) but finishes with structural model validation only (`:240`). Cross-field rules live separately in `validate.py:122-277,419-420`. A criterion referencing nonexistent `RQ999` was confirmed to compile successfully.
2. `SearchStrategy` supports `golden_seeds` (`models.py:146-149`), but `IntentPacket` has no corresponding field (`intent.py:191-216`) and compiler construction omits it (`compiler.py:188-197`). Because extra fields are ignored, supplied seeds can disappear silently.
3. Dynamic extraction maps every non-list dimension—including numeric and categorical—to `str` (`extraction.py:31-37`). A numeric accuracy dimension was confirmed to generate JSON Schema type `string`.
4. Protocol and intent models use Pydantic's permissive extra-ignore behavior; a misspelled authoring field can disappear instead of failing. Several semantic fields such as Boolean operators, identifier shapes, and timestamps are also weakly constrained (`models.py:88,113,157,200,318-320`).
5. Valid protocol file paths return `INVALID` through the current MCP adapter because file text is passed directly to `ResearchProtocol.model_validate` rather than parsed JSON (`tools/scholar-agent-kit/src/scholar_agent/server.py:230-248`). Inline/file parity is broken outside the kit even though kit validation succeeds.
6. PRISMA scoring includes execution-dependent items that are necessarily false before a review has run (`validate.py:337-345`). The score is therefore a protocol-plus-execution readiness measure, not pure protocol compliance.
7. RAG imports protocol extraction/model code (`tools/scholar-rag-kit/src/scholar_rag/matrix.py:15-16`) while omitting protocol-kit from runtime dependencies; shared editable installation masks standalone packaging failure.
8. README module names such as `compile.py`/`playbook.py` do not match live `compiler.py`/`presets.py`, and CLI coverage such as PRISMA checks is incomplete.
9. Core scientific choices also have model/preset defaults (`models.py:116-147`; `compiler.py:190-220`; `presets.py:74-143`) without field-level provenance distinguishing researcher input from preset suggestion. This is a design risk confirmed by the materialized model behavior.
10. Extraction fallback values can insert strings such as “Not Reported” (`intent.py:102-118`; `extraction.py:38-52`) rather than representing typed missingness.

## Goals

- Require explicit ownership of scientifically material choices.
- Represent unset, preset-suggested, accepted, and observed-missing states distinctly.
- Preserve field-level decision provenance in canonical artifacts and fingerprints.
- Make validation levels and API/CLI/MCP behavior consistent.
- Generate extraction schemas that never fabricate evidence values.

## Non-goals

- Selecting methodology, databases, thresholds, or dates for the researcher.
- Certifying PRISMA registration/compliance or study quality.
- Treating a valid JSON schema as an adequate research design.
- Backfilling study/chunk identities during protocol compilation.

## Normative requirements

Requirement IDs: the numbered requirements below carry stable IDs `PR-001`…`PR-022`
(requirement *n* = `PR-0nn`). Regression tests and the traceability ledger required
by `11_validation_and_test_plan.md` (VAL-001, §11–§12) MUST reference these IDs.

1. Scientifically material fields MUST have no model-level value defaults: research questions, databases, date bounds, languages, inclusion/exclusion criteria, candidate-pool targets, screening mode, quality framework, verification thresholds, and extraction missingness policy.
2. Presets MAY produce suggestions, but compilation MUST require explicit acceptance and record `source=preset`, preset name/version, acceptance timestamp/actor, and overridden value history.
3. Compiled fields MUST distinguish `explicit`, `accepted_preset`, `derived`, and `unset`. Unset material fields MUST prevent an executable/final protocol.
4. `workspace_id` MUST be explicitly supplied or workspace-resolved and recorded. `study_id` and `chunk_id` MUST appear only as downstream identity requirements, never protocol/corpus substitutes.
5. Date ranges MUST be explicit and reproducible; no moving current-year default is permitted. Open-ended ranges require an explicit null bound and declared interpretation.
6. Extraction schemas MUST represent missing evidence as null plus a `missing_reason` enum (`not_reported`, `not_applicable`, `not_accessible`, `unclear`, `extraction_failed`). They MUST NOT insert “Not Reported” or any fallback as observed content.
7. Required extraction dimensions MUST fail validation when absent. Optional dimensions MUST remain null unless source evidence supplies a value.
8. Generated extraction prompts MUST demand evidence quote/span, source `study_id`, source `chunk_id`, extraction confidence/method, and missing reason. They MUST prohibit inference beyond source text.
9. Validation MUST expose named levels: schema, cross-field, methodological-readiness, and execution-readiness. “Valid” without a level is prohibited in machine output.
10. Warnings MUST be retained in every API/CLI/MCP result and artifact. Execution-readiness MUST fail on unresolved material warnings.
11. RQ references from criteria and dimensions MUST resolve; orphan RQs, duplicate IDs, contradictory criteria, invalid thresholds, empty languages/databases, and incoherent pool/date bounds MUST be errors at execution-readiness.
12. Canonical bytes and fingerprints MUST include schema version, compiler version, preset provenance, accepted suggestions, and material decision provenance; volatile timestamps MUST be excluded from the scientific-content fingerprint or separately fingerprinted.
13. Compilation MUST be deterministic for identical intent plus accepted-preset manifest. It MUST not consult wall-clock time or environment for scientific values.
14. API, CLI, and MCP MUST use one compiler/validator service and provide parity for strict/readiness validation, canonicalization, fingerprinting, extraction schema, and prompt generation.
15. Every generated artifact MUST state whether it is draft or execution-ready. Drafts MUST not be silently consumed by search/screen/RAG stages.
16. Errors MUST be stable coded findings with JSON locations, remediation text, and severity; unexpected exceptions MUST exit non-zero and never produce a final protocol.
17. `compile_protocol` MUST run the same structural and cross-field rules used by full validation before emitting an execution-ready protocol. Invalid RQ references, duplicate IDs, incoherent bounds, and other cross-field errors MUST fail compilation.
18. `golden_seeds` MUST be represented in intent, preserved through compilation/canonicalization, and validated according to declared cardinality/identifier rules. Unknown authoring fields MUST fail rather than disappear.
19. Extraction dimension kind MUST map to an appropriate typed schema: numeric to a documented numeric type/union, boolean to boolean, categorical to an enum or validated string vocabulary, list to typed arrays, and free text to string.
20. File-path and inline validation through API, CLI, and MCP MUST parse once and invoke the same public validator; a valid fixture MUST produce semantically identical results on every surface.
21. PRISMA protocol-readiness scoring MUST be separated from post-execution reporting/completeness checks and named accordingly.
22. Every direct consumer dependency, including RAG's protocol import, MUST be declared and validated in an isolated package installation.

## API, data, and CLI behavior

Introduce a versioned `ProtocolDraft` plus `DecisionProvenance` per material field and a `ProtocolValidationResult` with named levels. `compile_protocol` becomes two-phase: `suggest(intent)` returns unresolved choices and preset suggestions; `finalize(intent, acceptance_manifest)` emits an execution-ready protocol only when all material decisions are owned.

Extraction schema values use nullable typed fields plus companion evidence/missingness metadata. CLI adds `suggest`, `finalize`, `validate --level`, `canon`, `fingerprint --scope scientific|artifact`, and consistent `--json`. Existing `compile` defaults to draft-only during deprecation and exits non-zero if asked for final output with unresolved choices. MCP mirrors all operations and schemas.

## Migration and backward compatibility

- Add protocol schema v2; preserve a v1 reader but never infer that existing defaults were explicitly chosen.
- A migration command MUST mark values equal to old defaults as `provenance=legacy_unknown`, not `accepted_preset`; researcher confirmation is required for execution-ready status.
- Keep v1 canonical fingerprints verifiable. Generate separate v2 scientific/artifact fingerprints and a migration linkage record.
- Translate string fallback values to nullable fields plus a missingness policy; preserve original fallback only in migration notes.
- Retain CLI command aliases for one release with deprecation warnings and draft status.

## Work plan

### P0

1. Make compilation invoke shared full cross-field validation and add invalid-reference regressions.
2. Add `golden_seeds` to intent/compiler and reject unknown authoring fields.
3. Correct numeric/categorical/boolean/list extraction schema typing.
4. Fix and parity-test file-path/inline validation through agent MCP.
5. Separate protocol readiness from execution-completeness scoring.
6. Remove material model defaults or implement explicit field-level provenance/acceptance; block downstream execution on unresolved material choices.
7. Replace extraction fallback values with typed null/missing-reason/evidence provenance.

### P1

1. Version canonicalization/fingerprints and separate scientific from volatile artifact metadata.
2. Build v1 migration/confirmation workflow.
3. Unify API/CLI/MCP compiler, validation, canon, fingerprint, schema, and prompt surfaces.
4. Add stable finding codes and atomic artifact publication.
5. Declare protocol-kit in every direct consumer and add isolated-install tests.

### P2

1. Add contradiction analysis and domain-specific readiness plugins without silently changing core validity.
2. Add protocol diff tooling that highlights scientific decision changes separately from metadata changes.
3. Add registration/export mappings with explicit “not certified” boundaries.

## Failure-focused test matrix

| Area | Cases | Required assertion |
|---|---|---|
| Defaults | omitted DB/language/date/pool/threshold; direct model construction | remains unset/draft; no invented value |
| Presets | suggestion ignored/accepted/overridden; preset version changes | explicit acceptance and provenance; deterministic output |
| Identity | missing workspace; workspace used as study; study/chunk fields in extraction | correct scope; no substitution |
| Extraction | absent optional; absent required; not applicable; inaccessible; contradictory quote | null + coded reason; required fails; no fake text |
| Validation | duplicate IDs; bad RQ ref; empty DB/language; reversed dates/pool; warning at each level | stable codes and correct readiness outcome |
| Compile parity | bad RQ reference and duplicate ID through compile versus validate | compile refuses every cross-field-invalid protocol |
| Golden seeds | intent with 2-5 seeds; unknown field typo; invalid identifier | exact round-trip or validation failure; never silent drop |
| Extraction types | numeric, integer, boolean, categorical enum, list, text | correct JSON Schema/Pydantic types and validation |
| MCP modes | valid/invalid inline JSON and file path | identical validation level, findings, and status |
| PRISMA score | pre-execution protocol versus completed-review report | distinct named measures; no unavoidable false items in protocol readiness |
| Fingerprint | timestamp change; field-order change; scientific field change; preset provenance change | scientific hash stable only for non-scientific changes |
| Migration | v1 defaults; custom values; fallback strings; unknown extension fields | legacy_unknown; no fabricated acceptance; loss report |
| Surface parity | same draft through API/CLI/MCP | identical artifact, findings, exit/status semantics |
| Failure handling | malformed JSON; unknown schema; compiler exception; interrupted write | non-zero/structured error; no final artifact |
| Downstream gate | draft sent to search/screen/RAG | deterministic refusal with remediation |

## Definition of done

- No material scientific parameter appears without explicit provenance.
- Cross-field-invalid intent cannot compile to an execution-ready protocol.
- Golden seeds survive the complete intent-to-protocol path and authoring typos fail.
- Extraction schemas preserve declared data types rather than coercing scalars to strings.
- Omitted intent yields a draft with unresolved choices, not an executable protocol populated by defaults.
- Extraction output distinguishes observed value, null, and coded missing reason and always traces evidence to `study_id` and `chunk_id`.
- Scientific fingerprints ignore volatile artifact timestamps but change for any material decision/provenance change.
- v1 migration never claims old defaults were researcher-approved.
- API/CLI/MCP parity, schema fixtures, golden canonicalization, migration, and full harness tests pass.
- Downstream orchestration refuses non-execution-ready protocols.

## Dependencies and risks

Depends on inception/methodology UI supporting explicit acceptance, workspace manager supplying `workspace_id`, and search/screen/RAG honoring readiness gates and canonical identities. Risks include broad fixture/fingerprint churn, breaking v1 consumers, and increased user interaction. Versioned schemas, draft support, migration reports, and batched acceptance mitigate these risks.

## Documentation updates

Update protocol README/API/tutorial, schema docs, preset catalog, CLI/MCP help, inception workflow, surface matrix, migration guide, and extraction contract. Every example must mark suggested versus accepted values, validation level, draft/readiness status, identity semantics, missingness semantics, and the non-certification boundary.
