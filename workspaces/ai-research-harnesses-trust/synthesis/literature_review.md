# AI-Assisted Academic Research Harnesses: A Systematic Scoping Review of Traceability, Evidence Trust, and Reproducibility

**Protocol ID**: `proto-20260908-ai-research-harnesses-trust`
**Playbook & Methodology**: JBI Scoping Review Framework (PRISMA-ScR)
**Epistemological Framework**: Design Science Paradigm with Empirical Evidence Synthesis
**Corpus Finalization Date**: September 9, 2026
**Corpus Size**: N = 58 Included Studies (239 Deduplicated Records Screened; 64 Full-Text Extractions)
**Evidence Ledger**: 510 Verbatim-Backed Claims (`synthesis/claims.json`) → 95 Consensus Clusters (`synthesis/consensus.json`)
**Synthesis Sources**: `synthesis/claims*.json`, `synthesis/consensus.json`, `synthesis/method_comparison.md`, `phase4/*.json`, `audit/journal.jsonl`

---

## Executive Summary & PRISMA-ScR Flow

This systematic scoping review characterizes the state of the art (2023–2026) in AI-assisted academic research harnesses — computational tools, agent architectures, and research infrastructure that automate or augment literature review and evidence synthesis. It focuses on execution provenance, audit trails, citation fact-checking, hallucination mitigation, academic-integrity mechanisms, and reproducibility, providing an evidence base for the engineering of trustworthy, publication-grade research infrastructure.

### PRISMA-ScR Identification and Selection Flow

All identification, screening, and retrieval numbers are immutably logged in `audit/journal.jsonl` and verified against `literature/included.json` / `literature/excluded.json`:

1. **Identification**: Federated discovery across five scholarly repositories (OpenAlex, Semantic Scholar, arXiv, Crossref, PubMed), 2023–2026 → **250 raw records**.
2. **Deduplication**: DOI- and normalized-title dedup resolved 11 duplicates (4.4%) → **239 unique records**.
3. **Verification & Hydration**: 239 records verified against OpenAlex/Crossref (86.6% abstract coverage, 86.2% DOI coverage).
4. **Screening**: 4 independent AI screeners over 12 batches (Fleiss' κ = 0.408); majority rule + senior-adjudicator resolution of 26 two-vs-two deadlocks → **58 INCLUDED / 181 EXCLUDED**.
5. **Full-Text Acquisition**: 64 Open Access PDFs downloaded and extracted to YAML-frontmatter Markdown (`extracted/`).
6. **Vector Index**: 64 documents → **3,814 AST chunks** in `chroma_db` (collection `scholar_docs`).
7. **Post-Screening Trust Certification (Phase 4)**: 47 studies checked — 0 retractions, 16 open-science repository links, 5 COI industry ties.
8. **Claim Extraction & Consensus**: **510 verbatim-backed claims** (RQ1 166 / RQ2 132 / RQ3 212) across 57 studies → **95 semantic consensus clusters** (16 high-consensus, 7 active debates, 37 unresolved, 35 provisional).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PRISMA-ScR 2020 Flow Diagram                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Federated Multi-Source Discovery:               N = 250                    │
│  Unique Deduplicated Records:                    N = 239 (11 duplicates)    │
│  Hydrated & Verified Records:                    N = 239                    │
│  Excluded at Screening:                          N = 181 (75.7%)            │
│  Included Full-Text Eligible Studies:            N =  58 (24.3%)            │
│  Open Access Full-Text Retrieved & Extracted:    N =  64                    │
│  Included Studies with Full-Text:                N =  46 (12 abstract-only) │
│  Structural AST Chunks Vector-Indexed:           N = 3,814 chunks           │
│  Phase 4 Retraction & Status Certified:          N =  47 (0 retracted)      │
│  Verbatim-Backed Evidence Claims:                N = 510 (100% verified)    │
│  Consensus Clusters (semantic, θ 0.40):          N =  95                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Corpus Taxonomy & Descriptive Characterization

The final corpus of **58 included studies** (2023–2026) reflects rapid year-on-year growth in agentic research tooling:

| Dimension | Distribution (n included) | Notes |
| :--- | :--- | :--- |
| **Temporal Window** | 2023: 2 (3.4%) · 2024: 8 (13.8%) · 2025: 18 (31.0%) · 2026: 30 (51.7%) | Exponential growth; 2026 alone is >half of the corpus |
| **Architectural Pattern** (keyword-classified, n=46 full-text) | Multi-agent / agentic orchestration 16 (34.8%) · single-agent / single-system 19 (41.3%) · RAG / retrieval-grounded 5 (10.9%) · end-to-end pipeline / meta-analysis 4 (8.7%) · knowledge-graph / ontology 2 (4.3%) | Multi-agent + retrieval architectures dominate the agentic cohort |
| **Evidence Availability** (Phase 4) | Public repository links: 16 · data+code dual open: 7 · explicit DAS/CAS statement: 32 · proprietary/no-release: 5 | 34.0% of checked corpus is open-source-verifiable |
| **Integrity Signals** (Phase 4) | Retracted: 0 · COI industry ties: 5 · declared-no-conflict: 4 · no formal COI statement: 37 | Preprints/CS venues rarely carry formal COI disclosures |

*The 12 included studies without available full text contribute abstract-only claims; SCI-000147 (empty abstract) contributes none.*

---

## Section 1 — RQ1: The State of the Art in AI-Assisted Research Harnesses

*Evidence: 166 RQ1 claims across 52 studies; 55 clusters touch RQ1.*

### 1.1 Topic: An Emerging, Convergent Architecture for Evidence Synthesis

Across the clusters that touch RQ1, the corpus documents a rapid transition from isolated LLM experiments to purpose-built **research harnesses** that integrate LLMs and agentic AI into systematic literature review (SLR) and evidence-synthesis workflows (2023–2026). The majority of included systems deploy off-the-shelf LLMs without task-specific fine-tuning, treating **prompt engineering as the primary optimization strategy**, with general-purpose models achieving strong screening performance through minimal adaptation (C9; SCI-000088). The motivating problem is concisely framed: conventional SLR practice is "time-consuming, labor-intensive, and susceptible to human bias" (C92; SCI-000182), and traditional keyword tools "lack the semantic understanding to answer nuanced questions" (C28; SCI-000181). Underpinning this convergence is an explicit orientation toward *auditability*: general-purpose agentic systems "fall short on the auditable, scenario-specific workflows" that heterogeneous biomedical sources demand (C1; SCI-000126).

### 1.2 Sub-theme A — Architectural Patterns and Design Mechanisms

The corpus evidences five recurring architectural patterns. **Prompt-compilation systems** replace manual "prompt alchemy" with a programmatic four-step process that compiles an optimal prompt and packages it as a "verifiable digital artefact," diagnosing prompt fragility as a threat to reproducibility (C15; SCI-000106). **Multi-agent teams with role specialization** are pervasive: M-Reason decomposes analysis into Orchestrator, BioExpert, and Evaluator roles, with an Orchestrator that sequences the workflow without touching an LLM (C18; SCI-000099); DeepER-Med builds a three-layer worker–manager–director network (C15; SCI-000102); LUMEN coordinates 11 specialized agents with deliberate model routing, assigning cheaper models to high-volume phases and more capable models to high-judgment and verification phases (C55; SCI-000118). **End-to-end orchestrated pipelines** assemble these components into full workflows: AutoSynthesis automates the complete meta-analysis workflow through statistical synthesis (C1; SCI-000135), TrialMind follows PRISMA with a three-step numerical-extraction pipeline (C38; SCI-000109), and meta-pipe chains ten sequential skill modules with inter-stage data contracts (C5; SCI-000142). **RAG- and retrieval-grounded designs** emphasize grounding and citation tracing: LatteReview integrates RAG so reviewers fetch information dynamically (C17; SCI-000096), G-RAG workflows are orchestrated with LangGraph (C26; SCI-000127), and OpenScholar's iterative self-feedback retrieval produces inline citations linked to specific passages (C53; SCI-000159). Finally, **graph/knowledge-grounded designs** integrate structured and vector representations — HySemRAG creates dual data products, a Neo4j knowledge graph and Qdrant vector collections, as "structural infrastructure for verifiable information synthesis" (C28; SCI-000100), and the AI co-scientist integrates relational databases, vector retrieval, and a knowledge graph (C28; SCI-000138).

### 1.3 Sub-theme B — Execution Provenance and Audit Mechanisms

Provenance and auditability emerge as a defining design commitment. **Structured vs. unstructured logging**: every module in M-Reason logs token usage, runtime statistics, and inference metadata (C24; SCI-000099); LUMEN logs every API call locally in structured JSON with model identity, token counts, latency, retry count, and initiating phase (C24; SCI-000118); the TIB AIssistant logs all user interactions via the LiteralAI API (C17; SCI-000110). **Deterministic IDs and idempotency**: one workflow's Stage S1 logs validated requests and "assigns unique identifiers to guarantee idempotent behavior" (C5; SCI-000179), while stable record identifiers are preserved throughout another pipeline (C5; SCI-000137). **Append-only and immutable journals**: Brain Researcher anchors each auditable episode in a commitment card "sealed with a content hash," records a run-bundle spanning event traces, checksums, retries, and recovery events, and hosts completed runs in an immutable provenance record (C74; SCI-000140). **Reproducibility mechanisms**: full release of code, cost logs, and prompts on GitHub (C5; SCI-000118); archival of code, prompts, and outputs in open supplementary materials (C9; SCI-000137); step-by-step reproduction scripts (C19; SCI-000127). **Fixed decoding parameters**: GPT-4 uses temperature=0, frequency_penalty=0, presence_penalty=0, top_p=0.95 to maximize repeatability (C10; SCI-000108); LGAR uses temperature 0 with regex-constrained parsing and retry logic (C39; SCI-000164); one deterministic design produced 2,880 runs yielding 17,443 citations (C33; SCI-000144). **Model-openness choices**: LGAR constrains selection to open-weights models "explicitly to enhance the reproducibility of the results" (C9; SCI-000164); a fully local, zero-shot pipeline runs on consumer-grade hardware with no cloud APIs (C5; SCI-000090).

### 1.4 Sub-theme C — Recurring Tensions and Debates

Two tensions recur. First, **open-source vs. proprietary**: LGAR's open-weights constraint and LLAssist's positioning as "a transparent, freely-modifiable open-source alternative" are motivated by the claim that reliance on closed, proprietary systems compromises reproducibility (C80; SCI-000151), echoed in concerns about the "opacity of closed-source models" (C17; SCI-000111). Second, **reproducibility of closed models**: re-executing proprietary hosted workflows "cannot be guaranteed to reproduce original outputs because the underlying models and web interfaces are externally controlled and may change over time" (C69; SCI-000137). A third, **human-in-the-loop** tension cuts across the corpus: the dominant platform positions human-machine collaboration as researcher orchestration with retained control rather than full automation (C34; SCI-000141), with five mandatory human decision points in meta-pipe (C38; SCI-000142). Yet M-Reason argues that its deterministic workflow improves reproducibility at the cost of restricting adaptive decision-making (C18; SCI-000099). Evaluation quality is bounded by concerns such as data contamination — many benchmark SLRs predate LLM exposure during pre-training (C51; SCI-000164) — alongside a recognized absence of validation data in some system-description papers (C32; SCI-000142).

### 1.5 RQ1 Consensus Findings

- **Architectures converge on orchestrating LLM reasoning over shared evidence toward auditable, provenance-bearing workflows**, rather than treating generation as a single monolithic step — single-agent, multi-agent, end-to-end, RAG-, and graph-grounded patterns all appear. (SCI-000099, SCI-000100, SCI-000106, SCI-000118, SCI-000126, SCI-000135, SCI-000159)
- **Execution provenance is increasingly structured, deterministic, and append-only**: JSON logging, deterministic IDs for idempotency, immutable run records, and content-hashed commitments support per-stage traceability. (SCI-000099, SCI-000118, SCI-000140, SCI-000179)
- **Fixed decoding parameters (especially temperature 0) and open-weights model selection are the dominant reproducibility levers**, paired with release of code, prompts, and outputs. (SCI-000108, SCI-000144, SCI-000164)
- **Human-in-the-loop retention, not full automation, is the stated design goal**, enforced by explicit decision checkpoints. (SCI-000141, SCI-000142)
- **The overriding tension is open vs. closed governance**: reproducibility is unattainable when models and interfaces are externally controlled and can change over time. (SCI-000111, SCI-000137, SCI-000151)

---

## Section 2 — RQ2: Evidence-Trust and Academic-Integrity Mechanisms

*Evidence: 132 RQ2 claims across 48 studies; 47 clusters touch RQ2.*

### 2.1 Topic: Evidence-Trust as a First-Class Concern

As LLM-based research harnesses move from proof-of-concept toward real practice, the accuracy and trustworthiness of their outputs have emerged as first-class design concerns. The corpus frames the problem as verifiability — whether a claim, citation, or synthesis can be traced to an inspectable source and independently confirmed. A central insight is that a model name alone insufficiently describes an LLM-based decision system: the workflow also comprises prompt instructions, uncertainty handling, integrity checks, and post-processing (SCI-000137).

### 2.2 Sub-theme A: Citation Verification and Hallucination Mitigation

Citation verification and hallucination mitigation are the best-evidenced integrity mechanisms. A landmark study across **17,443 generated citations** found that no model exceeded a citation-level existence rate of 0.475, with temporal and combined conditions producing the steepest drops even while outputs stayed format-compliant — "compliance without substance" (SCI-000144). The pipeline assigns a three-way label (*Existing*, *Unresolved*, *Fabricated*) to every citation, audited against human labels with a Cohen's kappa of 0.63; manual validation on 100 citations gave overall agreement of 75%, with precision 0.97 for *Existing* and 0.88 for *Fabricated* but only 0.43 for *Unresolved*, whose dominant error mode was Unresolved-to-Fabricated (SCI-000144). The authors recommend post-hoc verification against multiple databases and treating *Unresolved* citations as high risk (SCI-000144).

Retrieval grounding is the most common mitigation architecture. OpenScholar, a retrieval-augmented scientific LM, produces citation-backed, retrievable responses traceable from answer to source passage (SCI-000154); OpenScholar-8B achieves zero hallucinated papers in computer science and biomedicine versus baseline LLMs with 92.1% (CS) and 97.6% (Bio) hallucination ratios (SCI-000159). Non-retrieval LLMs fabricate 78–98% of cited papers, a problem exacerbated in biomedical domains (SCI-000159). Corroborating this, GPT-4o fabricated citations in 78–90% of cases when citing recent literature, while retrieval-grounded systems reached citation accuracy on par with human experts (SCI-000154). Knowledge-graph grounding adds another layer, with integration into public biological knowledge graphs reported to reduce hallucinations (SCI-000082). Pipeline defenses include deterministic verification against Crossref and Semantic Scholar (SCI-000144), schema-constrained extraction with conservative missingness handling ("NR") to minimize fabrication (SCI-000090), and LangGraph-based mapping of retrieved texts back to user queries (SCI-000110). M-Reason agent prompts carry explicit anti-hallucination instructions requiring agents to avoid introducing information not present in the supplied evidence, and its outputs are fully traceable to source with explicit citations (SCI-000099).

Deterministic decoding is a recurring enabler of auditability: experiments fix temperature at 0 with a fixed seed within verifiable digital artefacts (SCI-000106, SCI-000144), and one deployment lowers temperature to 0.1 while restricting the model to indexed information (SCI-000172). A multi-agent validation loop — a generator drafting cited answers and a QA agent auditing accuracy, consistency, and citation adherence — further hardens the pipeline (SCI-000100, SCI-000102).

### 2.3 Sub-theme B: Academic-Integrity Mechanisms

The corpus documents risk-of-bias and methodological-quality mechanisms. A high-consensus review applies PROBAST + AI and QUADAS-2 to rate the quality and risk of bias of included LLM screening studies, finding most at low risk of bias (SCI-000088). Automated risk-of-bias assessment following ROBINS-I has been implemented, alongside PRISMA 2020 flow diagrams and funnel plots for small-study effects and publication bias (SCI-000135). For reproducibility, open-weights model selection is positioned explicitly to enhance reproducibility (SCI-000164), and several harnesses publish full pipelines — code, cost logs, and prompts — on GitHub (SCI-000118). Provenance recording is motivated partly by integrity verification, helping users verify the accuracy and originality of AI-generated content (SCI-000141). FDA approval status, a dynamic filtering criterion, is validated through an agentic retrieval module querying a curated, versioned reference rather than trusting model or registry knowledge (SCI-000122).

### 2.4 Sub-theme C: Residual Trust Gaps

Despite these mechanisms, persistent trust gaps remain. Field-level citation accuracy is imperfect across all components, with DOI matching at 74.4% and in-text citations at 73.9% (SCI-000100). Re-execution of proprietary hosted LLM workflows cannot be guaranteed to reproduce original outputs because the models and web interfaces are externally controlled and may change (SCI-000137); two nominally identical runs agreed on 91.7% of records but disagreed on 94 individual records, including 29 verified eligible records retained by only one run — aggregate similarity conceals item-level instability (SCI-000137). Verification methods can themselves fail as reliability proxies: BERTScore gives nearly identical F1 scores across workflows and rates false conclusions as semantically equivalent to correct ones (SCI-000127), and models can act as "obedient synthesizers rather than critical reasoners," uncritically synthesizing factually inverted retrievals into coherent false conclusions (SCI-000127). LLMs struggle to identify post-exposure controls, with precision (0.15–0.30) far below the best human reviewer (0.89) (SCI-000124). The corpus cannot exclude data contamination since many benchmark reviews were published years ago and their data may already have been exposed to LLMs during pre-training (SCI-000164).

### 2.5 RQ2 Consensus Findings

- **Citation verifiability is the central trust problem.** Across 17,443 citations no model exceeds an existence rate of 0.475, yet outputs remain format-compliant. (SCI-000144, SCI-000154, SCI-000159)
- **Three-way labels are auditable but imperfect.** The Existing/Unresolved/Fabricated pipeline achieved Cohen's kappa 0.63 against human labels, but Unresolved precision is only 0.43, so reported fabrication rates are likely underestimates. (SCI-000144, SCI-000100)
- **Retrieval and knowledge-graph grounding materially reduce fabrication.** OpenScholar achieves zero hallucinated papers versus 78–98% fabrication for non-retrieval LLMs. (SCI-000154, SCI-000159, SCI-000082)
- **Risk-of-bias assessment is institutionalized.** PROBAST + AI, QUADAS-2, and ROBINS-I are applied to screen and score harness outputs. (SCI-000088, SCI-000135)
- **Reproducibility remains the deepest residual gap.** Closed, proprietary workflows cannot be guaranteed to re-execute identically, model names poorly describe decision systems, and automated proxies like BERTScore fail to detect compromised conclusions. (SCI-000137, SCI-000141, SCI-000127)

---

## Section 3 — RQ3: Empirical Evaluation, Reliability, and Architectural Gaps

*Evidence: 212 RQ3 claims across 51 studies; 70 clusters touch RQ3.*

### 3.1 Topic: The Evaluation Maturity Conundrum

AI-assisted research harnesses that automate literature screening, data extraction, and evidence synthesis have proliferated rapidly, yet standardized evaluation methodologies for assessing their trustworthiness remain underdeveloped. Drawing on 510 verbatim-backed claims across 95 semantic consensus clusters, this chapter examines (a) prevailing evaluation practices, (b) reliability and reproducibility characteristics, and (c) architectural gaps that must be addressed before a trustworthy research infrastructure can be constructed.

### 3.2 Evaluation Practices

Screening classification is the most mature evaluation domain. A meta-analysis of 18 studies reported pooled sensitivity 0.92 (95% CI 0.81–0.96), pooled specificity 0.94 (95% CI 0.90–0.97), and an SROC AUC of 0.98 for LLM-assisted title-and-abstract screening, though with substantial heterogeneity (I² = 95.82%) (SCI-000088). Chain-of-thought prompting improved sensitivity from 0.86 to 0.95 (p < 0.01) (SCI-000088). Full-text screening pooled sensitivity and specificity both reached 0.99 (SCI-000088). Yet aggregate figures obscure domain variability: SYNERGY benchmark AUCs ranged from 0.77 to 0.95, contingent on task heterogeneity, inclusion rates (from <1% to 12.36%), and threshold sensitivity (SCI-000096).

Structured field extraction outperforms naive document chunking. HySemRAG achieved 35.1% higher semantic similarity than PDF chunking (p < 0.000001) across 643 observations (SCI-000100); on the ketamine/neuroimaging benchmark, schema-constrained extraction reached 100% recall, 97.9% precision, and 98.9% F1 (SCI-000090). However, extraction accuracy is domain-sensitive — clinical studies achieved 82% accuracy, the highest across three domains, while author attribution and reference identification remained error-prone with up to 40% of attempts yielding partial matches or failures (SCI-000108, SCI-000115).

Cost and efficiency data are predominantly descriptive. GPT-4o costs approximately $3.16 per 100 articles, GPT-3.5 about $0.22, and locally run models incur no cloud cost (SCI-000151). Two LLMs screened nearly 25× faster than a human rater, costing $3.26 versus an estimated $492.18 for two human raters (SCI-000152). Manual synthesis of 30 articles was estimated at 50+ hours; a RAG architecture completed the same task in 1 minute 24 seconds (SCI-000172). LUMEN established the first empirical end-to-end pipeline cost characterization, ranging from $19.51 to $29.04 across five reviews (median $22.65) (SCI-000118). Inter-rater agreement anchors quality: the KSR screening gold standard achieved kappa 0.804 (SCI-000115), and a human audit of Brain Researcher's scoring agreed with 96% of automated judge verdicts (Cohen's κ = 0.94) (SCI-000140).

### 3.3 Reliability and Reproducibility Findings

Temporal instability is a concrete vulnerability: HySemRAG exhibited performance declining at −1.9% per day over its evaluation period (SCI-000100). Output variability is documented — LLM answers to "String" questions were identical only 69% of the time, with substantive differences in 8% of cases (SCI-000108). Two nominally identical runs agreed on 91.7% of records but disagreed on 94 items, including 29 verified eligible records retained by only one run, demonstrating that aggregate similarity concealed item-level instability (SCI-000137).

Domain-transfer limitations constrain reliability claims. LGAR, evaluated on 57 SLRs, was only reliably tested in the medical domain because other SYNERGY domains contained too few SLRs (SCI-000164). Model ranking is domain-dependent and not transferable across topics (SCI-000118); LLM effectiveness varies by task — Gemini PRO achieved 90% in both extraction and screening, while Manus scored 98% in screening but only 40% in extraction (SCI-000129).

Contamination risk and model-version dependence compound these threats. One study acknowledged possible test-training data overlap (SCI-000125); model updates can invalidate prompts, with cross-model behavior diverging under identical conditions (SCI-000106). Prompt fragility is quantified: subtle format variations produced differences up to 76 accuracy points (SCI-000106). Closed-model irreproducibility is flagged (SCI-000111), compounded by LLM-judged metrics (SCI-000117). One system reported no validation data, describing formal Cochrane-reproduction validation as essential before routine use (SCI-000142). BERTScore fails as a reliability proxy, rating false conclusions as semantically equivalent to correct ones (SCI-000127).

### 3.4 Architectural Gaps and Design Implications

These findings delineate critical gaps. Validation remains proof-of-concept — benchmarked against published reviews with single-author adjudication and no blinded dual review (SCI-000090). No screening output recovered all verified eligible records, and greater benchmark retention did not correspond to greater recovery (SCI-000137). Performance degrades on interpretive tasks: "future directions" averaged only 2.9–3.5/5.0 (SCI-000115). Multi-agent orchestration involves a phase-dependent trade-off — it hurts screening but is essential for extraction, producing 5.7× more poolable analyses (SCI-000118). Retrieval-reliant architectures remain vulnerable to noisy context: every tested model synthesized negated abstracts into coherent but false conclusions (SCI-000127). Future systems must embed deterministic verification, multi-database citation checking, and uncertainty quantification rather than relying on prompt engineering alone (SCI-000144).

### 3.5 RQ3 Consensus Findings and Gaps

- **Finding 1.** LLM-assisted screening achieves strong aggregate performance (pooled sensitivity 0.92, specificity 0.94, AUC 0.98), but heterogeneity (I² > 95%) and domain-dependent rankings (AUC 0.77–0.95) mean aggregate metrics alone are insufficient for trustworthy deployment. (SCI-000088, SCI-000096, SCI-000118)
- **Finding 2.** Temporal drift (−1.9%/day), run-to-run discordance (91.7% record agreement concealing 29 verified-eligible disagreements), and prompt fragility (up to 76-point accuracy swings) are reliability failure modes not captured by current reporting conventions. (SCI-000100, SCI-000137, SCI-000106)
- **Finding 3.** Cost and time reductions are substantial (25× speed-up, 98–99% time reduction) but predominantly descriptive observations without controlled counterfactuals, limiting causal inference about net workflow benefit. (SCI-000152, SCI-000129, SCI-000118)
- **Finding 4.** Validation coverage is critically narrow: proof-of-concept evaluations against published reviews, restricted to the medical domain, single-model without cross-model replication, and lacking blinded dual review. (SCI-000090, SCI-000142, SCI-000164, SCI-000135)
- **Finding 5.** Semantic similarity metrics (BERTScore, ROUGE) fail as reliability proxies, rating false and correct conclusions as equivalent, while LLM-as-a-Judge protocols correlate only moderately with experts (r = 0.65–0.81) — necessitating human-anchored validation. (SCI-000127, SCI-000108)
- **Gap.** No study provides an end-to-end, externally validated, multi-domain benchmark jointly evaluating screening, extraction, synthesis quality, citation verifiability, and cost-efficiency — the prerequisite for trustworthy, generalizable AI-assisted research infrastructure.

---

## Section 4 — Phase 4 Corpus Trust & Integrity Audit

The corpus feeding this synthesis was subjected to the four analytical streams of `scholar-verify-kit` (`phase4/*.json`):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 Phase 4 Trust Verification Audit Summary                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Retraction & Status Check:      47 checked, 0 retracted, 0 flagged         │
│  Open-Science DAS/CAS Scan:      47 scanned, 16 repos, 7 dual data+code     │
│  Conflict of Interest Audit:     47 audited, 5 industry ties, 4 declared no │
│  Risk of Bias Assessment:        47 assessed across reporting domains       │
└─────────────────────────────────────────────────────────────────────────────┘
```

- **Retraction status** (`phase4/retraction_status_check.json`): every included study queried against OpenAlex (`is_retracted`) and Crossref (`update-to`) — **0 retracted, 0 flagged (100% certified clean)**.
- **Open-science scan** (`phase4/open_science_regex_baseline.json`): **16 studies (34.0%)** carry live public repository links; **7 (14.9%)** provide both data and code; **32 (68.1%)** carry an explicit DAS/CAS statement; 5 declare data/code proprietary.
- **COI audit** (`phase4/coi_audit.json`): **5 studies (10.6%)** exhibit industry affiliations or equipment support (Meta ×2, Google, Anthropic, OpenAI); 4 declare no conflict; 37 carry no formal COI statement (common in CS preprints).
- **Risk-of-bias**: QUADAS-2/PROBAST-style reporting assessed across 47 studies; zero clusters are `BLOCKED` (no retraction exposure in the evidence base).

---

## Section 5 — Consensus Cartography and the RAG-vs-Multi-Agent Method Comparison

The 510-claim ledger was clustered with the `scholar-rag` Consensus Cartographer (semantic cosine, all-MiniLM-L6-v2, threshold 0.40) into **95 clusters**: **16 high-consensus, 7 active debates, 37 unresolved (mostly neutral direction), 35 provisional (single-source)**.

Illustrative high-consensus themes (verbatim-backed): *citation-verifiability failure at scale* (~0.475 existence ceiling; SCI-000144, SCI-000154, SCI-000159); *open-weights selection for reproducibility* (C9; 17 studies); *human-machine collaboration with retained researcher control* (C34; SCI-000107, SCI-000141); *structured field extraction > naive PDF chunking* (C13; SCI-000090, SCI-000100, SCI-000110, SCI-000128); *cost/efficiency of local vs API models* (C79; SCI-000151, SCI-000154). Active debates include *deterministic vs adaptive configuration* (C10), *best-performing benchmark model* (C14), and *automated screening reliability of LLM vs human reviewers* (C60, C90).

**Method decision (important for interpretation):** claims were produced by a **multi-agent full-text pipeline** (8 agents over 46 full texts + 12 abstracts), all 510 evidence quotes machine-verified verbatim (char-window + token 6-gram coverage ≥ 0.90). This supersedes the deterministic top-K RAG retrieval pipeline, which was regenerated separately as a comparison baseline (`synthesis/rag_baseline/`): 90 claims, only 43.3% entailment-verified, and grounded in 11 studies that are **not** in the final included corpus (the vector store indexes all 64 extractions, 18 of which were screened out). Full details and the head-to-head table: `synthesis/method_comparison.md`.

---

## Methodological Implications for Next-Generation Research Harnesses

1. **The append-only, file-based audit journal is the correct provenance primitive.** Structured, deterministic, immutable event ledgers (`audit/journal.jsonl`) directly answer the corpus's dominant failure mode — L0/L1 ephemeral logging and aggregate statistics that conceal item-level instability (SCI-000137, SCI-000140).
2. **Verbatim-verifiable evidence is achievable and should be standard.** 100% of the 510 claims carry machine-verified word-for-word source quotes. Any claim-generation pipeline that cannot produce byte-verifiable provenance (the RAG baseline's 43.3% entailment rate on retrieved snippets) is not publication-grade.
3. **Corpus-scope discipline is mandatory.** Indexing pre-screening extractions silently leaks screened-out evidence into retrieval-based synthesis (11 non-included studies cited by the RAG baseline). Synthesis must be scoped to the reconciled `included.json` set.
4. **Trust verification must precede synthesis.** Zero retractions, 5 COI ties, and 16 open-science repos were only knowable through explicit Phase-4 checks; the corpus demonstrates both the norm (citation existence ≤0.475) and the mitigation (retrieval grounding → zero hallucinated papers) (SCI-000144, SCI-000154, SCI-000159).
5. **Evaluation infrastructure for the field itself is the open gap.** No study provides an end-to-end, multi-domain, externally validated benchmark covering screening, extraction, synthesis quality, citation verifiability, and cost — the prerequisite for trustworthy infrastructure (RQ3 Gap; C32, C51).

---

## Declarations of Integrity & Data Availability

- **Traceability Declaration**: no claim, percentage, or aggregate in this document is fabricated. All 510 claims are verbatim-backed in `synthesis/claims.json`; every RQ chapter assertion is traceable to a claim or cluster in `synthesis/consensus.json`.
  - Screening flow: `literature/included.json`, `literature/excluded.json`, `literature/prisma_screening_report.md`
  - Taxonomy/matrix: `synthesis/synthesis_matrix.json`
  - Trust verification: `phase4/retraction_status_check.json`, `phase4/open_science_regex_baseline.json`, `phase4/coi_audit.json`
  - Claims & consensus: `synthesis/claims.json`, `synthesis/claims_rq1|2|3.json`, `synthesis/consensus.json|md`
  - Method comparison: `synthesis/method_comparison.md`, `synthesis/rag_baseline/`
  - Audit trail: `audit/journal.jsonl`
- **Data Availability**: the complete workspace, including extraction markdowns, vector index, claim ledger, and audit journal, is preserved in `workspaces/ai-research-harnesses-trust/`.
- **Conflicts of Interest**: the authors declare no competing financial interests. The Nexus Scholar toolkit itself was excluded from the review matrix to prevent self-citation or selection bias.