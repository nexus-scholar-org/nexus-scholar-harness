# Three-Pass Triage (Workflow & Skill)

## Overview
A semi-automated reading workflow that hardcodes Srinivasan Keshav's "Three-Pass Approach" (Module 00.1) into the core of the researcher's daily life, preventing them from falling into the trap of linear reading.

## The Problem (The Argument)
Novice researchers read academic papers like novels: from page 1 to the bibliography. This guarantees exhaustion, cognitive overload, and ultimately, reading far fewer papers than necessary to understand a field. The structural anatomy of a paper (IMRAD) exists precisely so scientists can skip around and pull exactly what they need.

## Detailed Specs

### Pass 1: Strategic Triage (Fully Automated)
**Trigger:** The user feeds a massive `.bib` file or a directory of 50 downloaded PDFs to the workflow.
**Action:** The system uses `scholar-pdf-kit` and a lightweight LLM prompt to extract *only* the specific anatomical parts needed for Pass 1:
1. Title
2. Abstract
3. The very last paragraph of the Introduction (where the core contribution/hypothesis always lives).
4. Section Headings (to map the structure).
5. The Conclusion.
**Output:** A Markdown spreadsheet (or interactive UI) allowing the user to click `[Approve]` or `[Discard]` on each paper within 5 minutes.

### Pass 2: The Evidence Core (Semi-Automated)
**Trigger:** Triggered for the papers the user "Approved" in Pass 1.
**Action:** The system applies `scholar-pdf-kit[extract]` to rip the raw Markdown from the PDF. It structurally chunks the document using the logic from `scholar-rag-kit`. 
It then isolates and presents *only* the Evidentiary Core:
* **Quantitative:** Extracts Figures, Tables, Captions, Results, and Ablation Studies.
* **Qualitative:** Extracts Thematic Tables, Conceptual Framework diagrams, and coding excerpts.
**Output:** The LLM summarizes *how* the research was executed (Methodology summary). The researcher can now evaluate the rigor without reading the filler text.

### Pass 3: Deep Re-Implementation / Critical Audit (Agentic)
**Trigger:** Reserved for the top 5% of papers that directly influence the researcher's own protocol.
**Action:** The agent adopts the persona of a highly critical "Reviewer 2". It cross-references the Methodology section against the Results section, hunting for:
* Methodological flaws or leaps in logic.
* Inadequate sample sizes or low statistical power.
* Lack of qualitative confirmability (e.g., missing audit trails).
**Output:** A deep, 2-page critical audit of the paper, pointing out exactly where the authors' claims are weak or unsupported by their own data.
