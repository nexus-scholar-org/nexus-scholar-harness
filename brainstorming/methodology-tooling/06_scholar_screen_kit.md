# Scholar Screen Kit (The Missing Link)

## Overview
A dedicated CLI toolkit designed to bridge the gap between finding thousands of papers (`scholar-search-kit`) and downloading their full texts (`scholar-pdf-kit`). It functions as an AI-augmented, terminal-native alternative to Rayyan or Covidence.

## The Problem (The Argument)
Currently, our pipeline can find 2,000 DOIs via `scholar-search-kit` and deduplicate them via `scholar-bib-kit`. But if a student immediately passes those 2,000 DOIs to `scholar-pdf-kit`, they will waste hours downloading and running heavy Docling extraction on thousands of irrelevant papers. 

In Systematic Reviews (and rigorous literature reviews), there is a mandatory **Screening Phase**. Researchers must read the Title and Abstract of every paper and judge it against strict Inclusion/Exclusion Criteria. Doing this manually for 2,000 papers causes severe fatigue.

## Detailed Specs

### 1. The `criteria.md` File
The user writes a simple Markdown file defining their criteria:
```markdown
# Inclusion Criteria
- Studies involving human subjects.
- Published after 2018.
- Focuses on Large Language Models for coding.

# Exclusion Criteria
- Studies on animals.
- Review papers or meta-analyses (we only want primary empirical studies).
```

### 2. `scholar-screen abstract` (Phase 1)
**Action:** The tool ingests the 2,000 abstracts from `scholar-bib-kit` and the `criteria.md` file. It uses an LLM (with structured JSON outputs) to evaluate each abstract.
**Output:** It sorts the papers into `included.json`, `excluded.json`, and `conflicts.json` (where the LLM was unsure). For every exclusion, it records the exact *reason* (e.g., "Excluded: Animal study").

### 3. `scholar-screen prisma` (The Reporting Engine)
**Action:** Journals require a PRISMA flowchart showing exactly how many papers were filtered out and why.
**Output:** The kit automatically generates a PRISMA-compliant report:
* "Records identified: 2,000"
* "Records excluded at title/abstract phase: 1,850"
   * "Reason 1 (Animal Study): 800"
   * "Reason 2 (Review Paper): 1,050"
* "Records sought for full-text retrieval: 150"

### 4. The Handoff
The 150 DOIs in `included.json` are precisely what get handed off to `scholar-pdf-kit` for actual downloading and Docling extraction. 

## Why we need this
Without `scholar-screen-kit`, the pipeline is computationally wasteful and mathematically untraceable. This package enforces rigorous Systematic Review standards (PRISMA) while saving the researcher weeks of manual abstract reading.
