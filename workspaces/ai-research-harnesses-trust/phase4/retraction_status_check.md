# Retraction & Publication-Status Check

**Corpus**: 48 studies (post-audit); **run**: 2026-09-08T09:45:06.924631+01:00
**Sources**: OpenAlex `is_retracted`/`last_status_in_oa` + Crossref `update-to`

## Summary

| Metric | Value |
|---|---|
| Studies checked | 48 |
| Flagged (any retraction/correction/EoC signal) | 0 |
| Retracted (OpenAlex) | 0 |
| Crossref update-to events | none |
| OpenAlex provenance (`last_status_in_oa`) | not populated for this corpus |
| Unresolved lookups | 0 |

## Flagged studies

None.

## arXiv-only records (no formal retraction channel)

The following studies have no DOI and are arXiv-tracked; OpenAlex was consulted through a DOI-independent lookup (arXiv id → title/year match → OpenAlex id):

| ID | Title | OpenAlex retracted |
|---|---|---|
| SCI-000003 | 2023 Sušnjak PRISMADFLLM An Extension of PRISMA for Systemati | None |
| SCI-000005 | 2024 An vitaLITy 2 Reviewing Academic Literature Using La | None |
| SCI-000104 | Generative AI for Health Technology Assessment: Opportunities, Challenges, and Policy Considerations | None |
| SCI-000105 | A Review on Scientific Knowledge Extraction using Large Language Models in Biomedical Sciences | None |
| SCI-000009 | 2024 Haryanto LLAssist Simple Tools for Automating Literature R | None |
| SCI-000108 | Exploring the use of a Large Language Model for data extraction in systematic reviews: a rapid feasibility study | None |
| SCI-000013 | 2025 Auer Towards AI-Supported Research a Vision  | None |
| SCI-000014 | 2025 Godinez HySemRAG A Hybrid Semantic RetrievalAugmented Ge | None |
| SCI-000017 | 2025 Jaumann LGAR ZeroShot LLMGuided Neural Ranking for Abst | None |
| SCI-000020 | 2025 Rahgozar An AIDriven Live Systematic Reviews in the Brain | None |
| SCI-000106 | Compiling Prompts, Not Crafting Them: A Reproducible Workflow for AI-Assisted Evidence Synthesis | None |
| SCI-000025 | 2025 Zheng Agent4S The Transformation of Research Paradigms  | None |
| SCI-000027 | 2026 Bansal Beyond the Parameters A Technical Surve | None |
| SCI-000140 | Bringing analytic rigor to agentic AI for science: The Brain Researcher platform for neuroimaging data analysis | None |
| SCI-000032 | 2026 Kinas BioResearcher Scenario-Guided Multi-Age | None |
| SCI-000033 | 2026 Koch Beyond Task Success An Evidence-Synthes | None |
| SCI-000034 | 2026 Lin meta-pipe An LLM-agent pipeline for end | None |
| SCI-000138 | AI Co-Scientist for Knowledge Synthesis in Medical Contexts: A Proof of Concept | None |
| SCI-000038 | 2026 Rai From MultiAgent Reinforcement Learning to Agentic | None |
| SCI-000134 | How Software Engineering Students Use LLMs to Write Research Papers: An Experience Report | None |
| SCI-000115 | Knowledge Synthesis Review Framework: Task-Level Benchmarking of LLM-Based Systems for Multi-Source Evidence Synthesis | None |
| SCI-000041 | 2026 Taherinezhad AutoSynthesis An agentic system for aut | None |
| SCI-000042 | 2026 Tongnamtiang An AIAssisted Research Automation System for Scho | None |
| SCI-000044 | 2026 Wang DeepER-Med Advancing Deep Evidence-Base | None |
| SCI-000046 | 2026 Yang ARIS Autonomous Research via Adversaria | None |
| SCI-000136 | Investigating Novice Researchers' Perceptions of Research Privacy Within LLM-Assisted Workflows | None |
| SCI-000144 | Do Deployment Constraints Make LLMs Hallucinate Citations? An Empirical Study across Four Models and Five Prompting Regimes | None |

## API errors (lookups that did not resolve)

| ID | DOI | Detail |
|---|---|---|
| SCI-000003 | — | `{'_status': 404}` |
| SCI-000005 | — | `{'_status': 404}` |
| SCI-000104 | — | `{'_status': 404}` |
| SCI-000105 | — | `{'_status': 404}` |
| SCI-000009 | — | `{'_status': 404}` |
| SCI-000108 | — | `{'_status': 404}` |
| SCI-000013 | — | `{'_status': 404}` |
| SCI-000014 | — | `{'_status': 404}` |
| SCI-000017 | — | `{'_status': 404}` |
| SCI-000020 | — | `{'_status': 404}` |
| SCI-000106 | — | `{'_status': 404}` |
| SCI-000025 | — | `{'_status': 404}` |
| SCI-000027 | — | `{'_status': 404}` |
| SCI-000140 | — | `{'_status': 404}` |
| SCI-000167 | 10.1016/j.ipm.2026.104882&quot | `{'_status': 404}` |
| SCI-000032 | — | `{'_status': 404}` |
| SCI-000033 | — | `{'_status': 404}` |
| SCI-000034 | — | `{'_status': 404}` |
| SCI-000138 | — | `{'_status': 404}` |
| SCI-000038 | — | `{'_status': 404}` |
| SCI-000134 | — | `{'_status': 404}` |
| SCI-000115 | — | `{'_status': 404}` |
| SCI-000041 | — | `{'_status': 404}` |
| SCI-000042 | — | `{'_status': 404}` |
| SCI-000044 | — | `{'_status': 404}` |
| SCI-000046 | — | `{'_status': 404}` |
| SCI-000136 | — | `{'_status': 404}` |
| SCI-000144 | — | `{'_status': 404}` |

## Methodological note

- Correction markers from Crossref may be self-published errata; treat as low-severity unless `type == retraction` or `expression-of-concern`.
- OpenAlex `is_retracted` reflects the current metadata snapshot, not publisher live status.
- All per-study rows are in the JSON output; regenerate with `scholar-verify retraction --workspace <dir>`.
