# Screening Criteria: AI-Assisted Academic Research Harnesses: Traceability, Trust, Audit and Reproducibility

**Protocol ID**: `proto-20260908-ai-research-harnesses-trust`
**Lead Researcher**: Mouadh & AI Agent
**Playbook**: SCOPING_REVIEW
**Paradigm**: Design Science

## Context & Rationale
**Unit of Analysis**: academic research and literature review harness systems

Design Science stance via the SCOPING_REVIEW playbook. Unit of analysis: academic research and literature review harness systems. Convincing evidence consists of concrete, published descriptions or evaluations of AI-assisted research harnesses reporting explicit mechanisms for execution provenance, audit trails, evidence verification, or reproducibility. Explicitly out of scope: generic writing assistants without research workflow orchestration, non-scholarly enterprise RAG, and purely narrative position papers without an artifact or evaluation.

## Research Questions

### RQ1
**Question**: What is the state of the art in academic research and literature review harnesses that integrate LLMs and agentic AI (2023–2026), and what concrete design mechanisms do they implement for execution provenance, audit trails, and process reproducibility?
- **Required Evidence**: Architectural specifications, workflow descriptions, provenance logging models
- **Synthesis Type**: Comparative Matrix

### RQ2
**Question**: What evidence-trust and academic-integrity mechanisms (e.g., citation fact-checking, hallucination mitigation, retraction checks, risk-of-bias, and open-science artifact verification) are incorporated into modern AI research harnesses?
- **Required Evidence**: Algorithmic descriptions of citation verification, hallucination mitigation, or integrity auditing layers
- **Synthesis Type**: Comparative Matrix

### RQ3
**Question**: How are AI-assisted research harnesses empirically evaluated (benchmarks, ablations, inter-rater reliability, user studies), and what architectural gaps remain for the construction of a novel, trustworthy research infrastructure?
- **Required Evidence**: Quantitative benchmark evaluations (accuracy, recall, precision, latency) and documented architectural limitations
- **Synthesis Type**: Narrative & Gap Analysis

## Inclusion Criteria

### INC-01
**Criterion**: Proposes, implements, or evaluates a computational tool, system, harness, or multi-agent pipeline specifically designed for academic literature discovery, screening, extraction, citation graph analysis, or evidence synthesis.
**Serves**: RQ1, RQ2, RQ3

### INC-02
**Criterion**: Incorporates Large Language Models (LLMs), agentic orchestration, or modern RAG mechanisms within the scientific literature workflow.
**Serves**: RQ1, RQ2, RQ3

### INC-03
**Criterion**: Explicitly describes or evaluates mechanisms for execution provenance (audit logs, DAG pipelines), citation verification / hallucination mitigation, or academic integrity (retraction, risk-of-bias, or open-science checks).
**Serves**: RQ1, RQ2

### INC-04
**Criterion**: Provides an accessible codebase, architecture specification, or quantitative empirical evaluation (e.g., precision, recall, citation accuracy, benchmark metrics, or user study).
**Serves**: RQ2, RQ3

## Exclusion Criteria

### EXC-01
**Criterion**: Pure academic writing, paraphrasing, grammar, or paper-authorship tools (e.g., Paperpal, generic ChatGPT writing prompts) lacking literature workflow orchestration or provenance.
**Rejection Reason Code**: `PURE_WRITING_TOOL`
**Serves**: RQ1, RQ2, RQ3

### EXC-02
**Criterion**: General-purpose conversational RAG or enterprise search systems not specifically targeted to academic research or scientific literature.
**Rejection Reason Code**: `NON_SCHOLARLY_DOMAIN`
**Serves**: RQ1, RQ2, RQ3

### EXC-03
**Criterion**: Narrative opinion pieces, commentaries, or high-level philosophical manifestos lacking a described system architecture or empirical evaluation.
**Rejection Reason Code**: `NO_COMPUTATIONAL_ARTIFACT`
**Serves**: RQ1, RQ2, RQ3

### EXC-04
**Criterion**: Published prior to 2023 (excluding pre-LLM historical literature).
**Rejection Reason Code**: `TEMPORAL_OUT_OF_BOUNDS`
**Serves**: RQ1, RQ2, RQ3

### EXC-05
**Criterion**: Full text not available in English.
**Rejection Reason Code**: `NON_ENGLISH`
**Serves**: RQ1, RQ2, RQ3

## Verification Constraints

- [x] Retraction check required
- [x] Conflict of Interest & Funding audit required
- [x] Reproducibility (Data/Code Availability) check required
- Minimum Trust Score: 6.0
