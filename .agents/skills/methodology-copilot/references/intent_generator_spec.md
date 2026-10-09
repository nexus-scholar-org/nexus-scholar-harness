# Intent Packet Specification (`intent.json`)

When transitioning from the methodology interview to the protocol generation phase, the Copilot produces an `intent.json` file inside `workspaces/<project-slug>/intent.json`.
This file is an `IntentPacket` which the deterministic compiler converts into the canonical `protocol.json`.

---

## 1. Structure of `intent.json`

The file must strictly follow the schema for `scholar_protocol.intent.IntentPacket`.

```json
{
  "protocol_id": "proto-20260901-benchmark",
  "genesis_timestamp": "2026-09-01T00:00:00+00:00",
  "project_slug": "benchmark-review",
  "playbook_type": "DESIGN_SCIENCE",
  "title": "Benchmark Evaluation for Code Synthesis",
  "lead_researcher": "Dr. Researcher",
  "unit_of_analysis": "Code generation models",
  "epistemological_rationale": "Empirical performance quantification",
  "research_questions": [
    {
      "text": "What pass@1 rates are achieved across benchmarks?",
      "target_facet": "evaluation_metrics",
      "required_evidence_type": "Quantitative Benchmark"
    }
  ],
  "core_concepts": [
    {
      "concept": "Code Generation",
      "synonyms": ["code synthesis", "program generation"]
    }
  ],
  "inclusion_criteria": [
    {
      "criterion": "Evaluates on public benchmarks",
      "maps_to_rqs": ["RQ1"]
    }
  ],
  "exclusion_criteria": [
    {
      "criterion": "Non-English editorial",
      "reason_category": "LANGUAGE",
      "maps_to_rqs": ["RQ1"]
    }
  ],
  "matrix_dimensions": [
    {
      "id": "sample_size",
      "name": "Sample Size",
      "description": "Number of benchmarks evaluated"
    }
  ]
}
```

## 2. Post-Generation Pipeline
After generating `workspaces/<project-slug>/intent.json`, compile and render
(both print to stdout, so redirect to persist — neither takes `-i`, `-o`, or
`--fingerprint`; fingerprint a compiled protocol with the separate
`fingerprint` command):
```bash
uv run scholar-protocol compile workspaces/<project-slug>/intent.json > workspaces/<project-slug>/protocol.json

uv run scholar-protocol fingerprint workspaces/<project-slug>/protocol.json

uv run scholar-protocol render-criteria workspaces/<project-slug>/protocol.json > workspaces/<project-slug>/SCREENING_CRITERIA.md
```
