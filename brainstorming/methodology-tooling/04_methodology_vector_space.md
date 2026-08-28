# Methodology Vector Space (RAG Integration)

## Overview
An extension to the `scholar-rag-kit` that transforms it from a traditional "factual search engine" into a "design search engine." It allows students to search literature specifically for methodological inspiration rather than just empirical findings.

## The Problem (The Argument)
Standard RAG pipelines (and academic search engines like Google Scholar) are optimized for factual retrieval (e.g., "What is the mortality rate of X?"). But researchers frequently need to query *how* something was done (e.g., "Find me examples of how computer vision papers structure their ablation studies for self-supervised learning models"). Because traditional embedding models flatten the structure of the document, finding methodological templates is extremely difficult.

## Detailed Specs

### 1. Enhanced Structural Chunking
The `scholar-rag-kit` already splits Markdown documents cleanly by their header tags (e.g., `## Methodology`). We will augment the `chunker.py` to recognize highly specific evidentiary structural patterns across paradigms:
* `## Problem Formulation`
* `## Experimental Setup`
* `## Ablation Study`
* `## Thematic Analysis`

### 2. LLM-Assisted Metadata Tagging
During the `index` phase in `scholar-rag-kit`, before a chunk is embedded into ChromaDB, it is passed through a lightweight, local LLM classifier.
The classifier tags the chunk with specific methodology metadata:
```json
{
  "paradigm": "design_science",
  "design": "ablation_study",
  "domain": "computer_vision"
}
```

### 3. The Methodology Search Interface
When a researcher is designing their protocol, they can query the RAG database using strict metadata filters to find methodological templates:
```bash
uv run scholar-rag query "How to evaluate robustness against adversarial noise" \
  --section Methodology \
  --paradigm design_science \
  --design ablation_study
```
**Output:** The system returns exactly the paragraphs where previous authors defended their adversarial robustness testing methodology. The student can now model their own `research_protocol.md` on these gold-standard templates.
