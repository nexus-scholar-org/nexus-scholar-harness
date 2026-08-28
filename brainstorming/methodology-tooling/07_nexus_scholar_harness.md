# The Nexus Scholar Harness (Orchestrator)

## Overview
A "harness" in this context is a unified orchestrator (e.g., `nexus-scholar-cli` or a web-based `nexus-portal`) that ties the independent micro-kits together into a single, seamless, directed acyclic graph (DAG) workflow. 

Instead of the researcher manually invoking 10 different CLI kits, the harness guides them from a raw idea to a fully defended literature review and methodology design.

## The Harness Architecture (The Pipeline)

The harness is divided into **Three Major Phases**, matching the PhD lifecycle:

---

### Phase 1: Planning & Design (The "Idea" Stage)
*Input: A vague, unstructured research thought.*

1. **`research-question-refiner`**: The researcher inputs their thought. The harness generates 4 paradigm-specific variants. The researcher selects one.
2. **`methodology-copilot`**: The harness spins up the interactive Socratic agent to drill down into the selected question, forcing the user to commit to specific rigor metrics.
3. **`scholar-design-kit`**: The harness automatically runs statistical power calculations or data saturation estimates, and compiles a finalized `preregistration.md` file.

*Transition:* Now the researcher knows exactly what methodology they are using and what data they need.

---

### Phase 2: Discovery & Screening (The "Funnel" Stage)
*Input: The preregistered research question.*

4. **`scholar-search-kit`**: The harness queries OpenAlex/Crossref based on the refined keywords, downloading 2,000 raw metadata records (DOIs).
5. **`scholar-bib-kit`**: The harness automatically deduplicates the 2,000 DOIs, resolves messy citations, and standardizes the list.
6. **`scholar-screen-kit`**: The harness stops and asks the user for their `criteria.md` (Inclusion/Exclusion). It screens the 2,000 DOIs, generates a PRISMA flowchart, and outputs a final list of 150 "Approved" DOIs.
7. **`scholar-pdf-kit`**: The harness triggers the heavy Docling/Grobid engines to download and extract the 150 approved DOIs into pristine Markdown files.

*Transition:* The researcher now has 150 clean, highly relevant, full-text Markdown papers.

---

### Phase 3: Synthesis & Analysis (The "Insight" Stage)
*Input: 150 clean Markdown papers.*

8. **`scholar-rag-kit`**: The harness indexes all 150 Markdown files using **Structural Chunking** (breaking them down by IMRAD sections). It also applies the **`methodology-vector-space`** metadata tagging (classifying *how* each paper was done).
9. **`scholar-graph-kit`**: The harness builds the citation network of the 150 papers to identify the foundational "keystone" papers.
10. **`three-pass-triage`**: The harness presents a dashboard to the user. When the user queries the database, the harness uses graph-boosting (from the graph kit) and structural metadata (from the RAG kit) to fetch the precise evidentiary core of the papers. The agent then audits the methodologies.

## The Technical Implementation of the Harness

To implement this, we don't build a monolith. We build a **Makefile / Snakemake / Nextflow** pipeline, or a master Python Typer CLI (`nexus`) that calls the existing kits as plugins.

**Example User Experience:**
```bash
nexus init "How does AI affect learning?"
# (Triggers Phase 1: Copilot & Refiner)

nexus discover --limit 2000
# (Triggers Phase 2: Search -> Bib -> Screen)

nexus extract
# (Triggers Phase 2: PDF download & Docling)

nexus synthesize
# (Triggers Phase 3: RAG index & Graph build)
```

## Why the Harness Matters
It eliminates cognitive load. Students don't need to learn how to string 6 different Python tools together; they just follow the `nexus` command prompts. It mathematically prevents them from skipping steps (like downloading PDFs before screening them) and enforces extreme academic rigor.
