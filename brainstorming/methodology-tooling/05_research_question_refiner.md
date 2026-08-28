# Research Question Refiner (Agent Skill)

## Overview
A specialized prompt/skill that takes a vague, novice research question and structurally refracts it into four distinct, highly specific variants based on the four academic paradigms from Module 00.2.

## The Problem (The Argument)
A common mistake among students is arriving at their advisor's office with a broad, untestable question like, *"How does AI affect learning?"* 
Because the question lacks a paradigm, the researcher cannot determine what data to collect, what tools to use, or how to measure success. This tool demonstrates how the exact same core topic requires radically different methodological approaches depending on the researcher's epistemological stance.

## Detailed Specs

### The Workflow
**Trigger:** The user inputs a raw, messy research question into the `research-question-refiner` agent.
**Input Example:** *"I want to know if using large language models makes developers write better code."*

**Action:** The LLM applies the definitions from Module 00.2 to generate four rigid hypotheses/questions.

### The Refractions (Output Example)

1. **Positivist (Quantitative)**
   * **The Goal:** Measure objective, statistical effects.
   * **Refined Question:** *"What is the statistically significant impact of utilizing LLM-based assistants on the cyclomatic complexity and unit test coverage of code produced by mid-level Python developers?"*
   * **Required Data:** Numerical metrics (lines of code, test pass rates, time to completion).

2. **Interpretivist (Qualitative)**
   * **The Goal:** Understand subjective human experiences and meaning.
   * **Refined Question:** *"How do senior developers perceive the impact of LLM-generated code on their sense of authorial ownership and professional identity?"*
   * **Required Data:** Semi-structured interview transcripts, thematic coding.

3. **Pragmatist (Mixed Methods)**
   * **The Goal:** Solve a real-world problem by combining metrics with narratives.
   * **Refined Question:** *"To what extent do LLMs increase code commit frequency (Quant), and how does that accelerated pace affect developer burnout and code review fatigue (Qual)?"*
   * **Required Data:** Triangulation of Git commit logs and psychological survey data.

4. **Design Science (Computational/Engineering)**
   * **The Goal:** Build and evaluate a new artifact.
   * **Refined Question:** *"Can an IDE plugin utilizing a fine-tuned LLM with structural RAG reduce syntax errors in Python by 15% compared to standard autocomplete systems?"*
   * **Required Data:** Benchmark testing, ablation studies against a baseline model.

## Why this works
By forcing the student to see all four variants side-by-side, they immediately realize the necessity of committing to a single methodological paradigm before moving forward.
