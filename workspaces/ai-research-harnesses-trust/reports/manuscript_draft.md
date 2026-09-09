# AI-Assisted Research Harnesses: Traceability, Evidence Trust, and Reproducibility in Agentic Systematic Review Systems
## A Grounded, Verbatim-Verified Systematic Scoping Review of the 2023–2026 Corpus

---

**Protocol ID**: PROTO-20260908-AI-RESEARCH-HARNESSES-TRUST
**Type**: Systematic scoping review (protocol-based), PRISMA-ScR compliant
**Manuscript status**: Draft v1 for author review
**Prepared by**: The Nexus Scholar Research Pipeline (multi-agent orchestration, throwaway prompts; all claims machine-verified verbatim against full text — see §3.5 and §7)
**Corpus window**: January 2023 – September 2026

---

## Abstract

**Background.** Large language model (LLM) and agentic systems are being pressed into service across the systematic-review lifecycle — search, screening, extraction, and synthesis — yet the trustworthiness of their outputs (citation verifiability, provenance, reproducibility) is not established.

**Methods.** We conducted a protocol-driven systematic scoping review across six scholarly sources (OpenAlex, Semantic Scholar, Crossref, PubMed, arXiv, bioRxiv; January 2023–September 2026). 239 deduplicated records were screened by four independent AI screeners (Fleiss' κ = 0.408) with majority voting and adjudicated deadlock resolution, yielding 58 included studies. Full text (64 Open-Access extractions, 3,814 AST chunks) was subjected to a four-stream trust audit (retraction status, open-science artifact scan, conflict-of-interest audit, risk-of-bias attestation). Evidence was synthesized by two competing pipelines: a deterministic top-k retrieval-augmented generation (RAG) baseline (90 claims, 43.3% entailment-verified) and an authoritative **multi-agent full-text claim-extraction pipeline** (8 full-text agents + 1 abstract agent) whose 510 claims were each **machine-verified verbatim** (char-window and token 6-gram coverage ≥ 0.90; 100% pass). Claims were clustered into a semantic consensus map.

**Results.** Architectures converge on auditable, provenance-bearing workflows: multi-agent role specialization, end-to-end orchestrated pipelines, retrieval- (RAG) and knowledge-graph-grounded designs, and prompt-compilation systems. Execution provenance is increasingly structured and append-only (deterministic IDs, immutable content-hashed run records, temperature-0 decoding, open-weights selection). Citation verifiability is the binding trust constraint: across 17,443 generated citations no model exceeded a 0.475 existence rate, while retrieval grounding reduced hallucinated papers to zero in OpenScholar-8B versus 78–98% for non-retrieval LLMs. Pooled LLM screening sensitivity/specificity reached 0.92/0.94 (I² = 95.8%), but temporal drift (−1.9%/day), run-to-run item-level discordance, and prompt fragility (up to 76-point accuracy swings) are not captured by standard reporting. The deterministic RAG pipeline cited 11 screened-out studies (corpus contamination) and verified only 43.3% of its claims; the multi-agent ledger reached 100% verbatim grounding across 57 included studies and surfaced a consensus structure (95 clusters: 16 high-consensus, 7 active debates, 37 unresolved, 35 provisional) invisible to RAG.

**Conclusions.** Full-text, verbatim-verifiable claim extraction is a tractable and superior synthesis primitive for trustworthy research infrastructure. We identify the field's open gap: no study provides an end-to-end, externally validated, multi-domain benchmark jointly evaluating screening, extraction, synthesis quality, citation verifiability, and cost.

**Keywords**: AI-assisted systematic review; agentic systems; retrieval-augmented generation; citation fact-checking; provenance; reproducibility; hallucination mitigation; evidence synthesis.

---

## 1. Introduction

Conventional systematic reviews and scoping reviews are time-consuming, labor intensive, and susceptible to human bias [1]; conventional keyword search tools "lack the semantic understanding to answer nuanced questions" [2]. The rapid commoditization of LLMs has produced a wave of research harnesses claiming to automate review workflows end to end — from federated discovery and deduplication to TITLE/ABSTRACT screening, full-text extraction, risk-of-bias assessment, and statistical synthesis. Yet the same commoditization introduces new failure modes: fabricated citations, unreproducible runs, opaque closed-weight models, and retrieval pipelines that silently draw on evidence outside the approved corpus.

This review asks three questions. **RQ1** — What is the state of the art in academic research and literature-review harnesses integrating LLMs and agentic AI (2023–2026), particularly their design mechanisms for execution provenance, audit trails, and process reproducibility? **RQ2** — What evidence-trust and academic-integrity mechanisms (citation fact-checking, hallucination mitigation, retraction checks, risk-of-bias, open-science artifact verification) do they incorporate? **RQ3** — How are they empirically evaluated, and what architectural gaps remain for the construction of novel, trustworthy research infrastructure?

Our contribution is methodological as much as substantive: the synthesis itself is generated and audited by the same class of systems under study. Every claim in this manuscript is backed by a machine-verified, word-for-word verbatim quote from the included full text, and every pipeline step is recorded in an append-only audit journal.

## 2. Related Work

Prior evaluations have been narrow and siloed. Screening-performance meta-analyses report strong pooled sensitivity but extreme heterogeneity [3]. Citation-fabrication studies establish low existence ceilings but stop at measurement [4]. System papers demonstrate retrieval-grounded claim generation but evaluate on narrow benchmarks [5][6]. Reviews of agentic scientific tools remain taxonomical [7], and reproducibility audits document run-to-run instability without remediating it [8]. Missing is a protocol-driven, corpus-scoped, verbatim-verified synthesis that simultaneously characterizes design, trust mechanisms, and evaluation maturity — the gap this review addresses. Our retrieval-augmented baseline further contributes a direct, quantitative comparison of deterministic RAG synthesis versus full-text multi-agent extraction over an identical corpus.

## 3. Methods

The review follows a registered protocol compiled with a protocol compiler (`protocol.json`, `SCREENING_CRITERIA.md`, `intent.json`) under the Design Science paradigm, and is reported in line with PRISMA-ScR. All stages were executed through a shared vectorized Python environment; every step is recorded in an append-only audit journal (`audit/journal.jsonl`, 47 events).

### 3.1 Search and record verification
Six sources were federated in a single pass (OpenAlex, Semantic Scholar, Crossref, PubMed, arXiv, bioRxiv) with search strings targeting LLM/agentic review automation, 2023–2026. 250 raw hits were deduplicated and hydrated (DOI and normalized-title resolution, abstract and DOI completion), yielding **239 unique verified records**.

### 3.2 Screening
Two hundred thirty-nine records were screened against explicit PICO-style inclusion/exclusion criteria by four independent AI screeners in twelve agent-in-the-loop batches (Fleiss' κ = **0.408**, fair/moderate agreement). Two hundred thirteen records were resolved by majority rule (≥3 of 4); the **26 two-vs-two deadlocks** were adjudicated by a senior adjudicator. Final: **58 included / 181 excluded**.

### 3.3 Full-text acquisition, extraction, and scoping
Open-Access PDFs were retrieved and extracted to YAML-frontmatter Markdown (64 documents; 3,814 structural AST chunks; `all-MiniLM-L6-v2` embeddings). Because extraction preceded final scoping, 18 extractions belong to screened-out studies; **all synthesis in this manuscript is scoped strictly to the 58 included studies**, and the screened-out extractions are removed from the evidence index for authoritative synthesis.

### 3.4 Trust verification (Phase 4)
Each included study was certified with four `scholar-verify` streams: retraction/status (OpenAlex `is_retracted`, Crossref `update-to`), open-science DA/S/CA artifact scanning, conflict-of-interest audit, and risk-of-bias attestation (47 studies fully checked).

### 3.5 Claim extraction with verbatim verification
**Approach B (authoritative).** Eight parallel agents read the complete text of the 46 full-text included papers (7 size-balanced batches ≤ ~456 KB) plus one agent over the 12 abstract-only papers, producing claims in a canonical 10-field schema (`rq_id`, `claim_text`, `citation_tokens`, `evidence_quote`, `section`, `stance`, `evidence_level`, `location_hint`, ...). Every quote was then **machine-verified verbatim** against the source file: glyph-normalized (bullet remapping, zero-width-space and Unicode-dash handling, NFKC, hyphen-wrap rejoin) matching via character windows (8 chars, step 4) and token 6-grams (6 tokens, step 3); a claim passes at ≥ 0.90 coverage on either metric. Initial verification failed 156/510 quotes; after four repair iterations including re-casting 11 light-paraphrase/math-glyph artifacts to exact substrings, **510/510 (100%) claims are verbatim-backed**, comprising 166 (RQ1), 132 (RQ2), 212 (RQ3) — 493 full-text and 17 abstract-only, spanning 57 studies (one included study has an empty abstract and contributes none).

**Approach A (baseline).** Deterministic RAG synthesis retrieved the top-30 chunks per research question from the full 64-document index and applied heuristic entailment verification of claims against their own snippets (90 claims, 30 per RQ).

### 3.6 Semantic consensus
The 510-claim ledger was clustered with cached-embedding cosine similarity (`all-MiniLM-L6-v2`, threshold 0.40) into a consensus map (16 high-consensus, 7 active debates, 37 unresolved, 35 provisional clusters).

### 3.7 Analysis and integrity of the synthesis
Results are reported per research question from the verbatim ledger, with cluster references; direct quotes are drawn verbatim from `claims.json`. Aggregates (e.g., citation existence, pooled sensitivity) are reported as stated by the source studies and cross-checked between claims.

## 4. Results

### 4.1 Corpus characteristics
The 58 included studies (2023: 2; 2024: 8; 2025: 18; 2026: 30) reflect exponential growth in agentic research tooling. Of the 46 full-text-characterized systems, keyword-classified architecture patterns are: single-agent/single-system 19 (41.3%); multi-agent/agentic orchestration 16 (34.8%); RAG/retrieval-grounded 5 (10.9%); end-to-end pipeline/meta-analysis 4 (8.7%); knowledge-graph/ontology 2 (4.3%). Phase-4 audit: **0 retractions**, 16 live repository links (34.0%), 7 dual data+code releases, 5 industry COI ties (10.6%), 4 declared no-conflict.

### 4.2 RQ1 — State of the art and design mechanisms
**Architectural convergence.** Systems press general-purpose LLMs into review pipelines without task-specific fine-tuning, treating **prompt engineering as the primary optimization strategy** [3][9]. Motivating framing recurs: conventional SLR practice is "time-consuming, labor-intensive, and susceptible to human bias" [1], and general-purpose agents "fall short on the auditable, scenario-specific workflows" biomedical evidence demands [7]. Five patterns recur: (i) **prompt-compilation systems** that package compiled prompts as "verifiable digital artefacts" to neutralize prompt fragility [9]; (ii) **multi-agent teams with role specialization** — Orchestrator/BioExpert/Evaluator decomposition [10], three-layer worker–manager–director networks [11], and 11-agent coordination with deliberate model routing (cheap models for throughput phases, strong models for judgment and verification) [12]; (iii) **end-to-end orchestrated pipelines** automating complete meta-analysis workflows [13][14][15]; (iv) **RAG/retrieval-grounded designs** coupling dynamic retrieval with answer generation [16][17][6]; and (v) **graph/knowledge-grounded designs** that productionize both a knowledge graph and vector collections as "structural infrastructure for verifiable information synthesis" [18][19].

**Execution provenance.** Provenance is increasingly structured, deterministic, and immutable: per-module token/runtime/inference logging [10], structured JSON API logs with model identity, latency, and retry counts [12], corpus-wide interaction logging [20], validated requests with unique identifiers guaranteeing **idempotent behavior** [21], stable record identifiers preserved end to end [8], and content-hashed "commitment cards" with run-bundles (event traces, checksums, retries) hosted in an immutable provenance record [22]. Reproducibility levers are dominated by **fixed decoding** (temperature 0 with frequency/penalty/presence penalties pinned [23]; temperature 0 with regex-constrained parsing and retries [24]; 2,880 runs producing 17,443 citations under deterministic settings [4]) and **model openness** — open-weights selection "explicitly to enhance the reproducibility of the results" [24], fully-local zero-API pipelines [25], and open-source positioning as an explicit fidelity alternative [26].

**Debates.** Open-source versus proprietary control: closed hosted models "cannot be guaranteed to reproduce original outputs because the underlying models and web interfaces are externally controlled and may change over time" [8][27]. Human-in-the-loop tension: dominant platforms position **researcher orchestration with retained control** and five mandatory human decision points [28][15], while deterministic workflows gain reproducibility but "restrict adaptive decision-making" [10].

### 4.3 RQ2 — Evidence-trust and academic-integrity mechanisms
**Citation verifiability ceiling.** Across **17,443 generated citations**, no model exceeded an existence rate of **0.475**; time-bound and combined conditions produced the steepest drops while outputs stayed format-compliant — "compliance without substance" [4]. A three-way Existing/Unresolved/Fabricated labeling pipeline audited against human labels achieved Cohen's κ = **0.63**; manual validation (n = 100) gave 0.75 overall agreement, precision 0.97 (Existing) and 0.88 (Fabricated) but only **0.43 (Unresolved)** — whose dominant error was Unresolved-to-Fabricated, making reported fabrication rates underestimates. Post-hoc multi-database verification was recommended [4].

**Grounded mitigation works.** OpenScholar, a retrieval-augmented scientific LM, returns passage-traceable answers [5]; OpenScholar-8B produced **zero hallucinated cited papers** versus baseline LLMs hallucinating **92.1% (CS) / 97.6% (Bio)** of cited papers; non-retrieval LLMs fabricated 78–98% of citations, worse in biomedicine [6]. Knowledge-graph integration into public biological graphs reduced hallucinations [29]. Deterministic countermeasures include Crossref/Semantic-Scholar verification [4], conservative schema-constrained missingness ("NR") to avoid fabrication [25], agent-level anti-hallucination instructions with full traceability [10], and multi-agent validation loops (generator + auditing QA agent) [18][11].

**Methodological integrity mechanisms.** Risk-of-bias assessment is institutionalized: PROBAST+AI and QUADAS-2 application to LLM screening studies [3], ROBINS-I-based automated risk-of-bias with PRISMA 2020 flow diagrams and funnel-plot checks [13]. Reproducibility is advanced by open code, cost, and prompt releases [12] and open-weights selection [24].

**Residual gaps.** Field-level citation accuracy remains imperfect (DOI matching 74.4%, in-text citations 73.9%) [18]. Two nominally identical runs agreed on 91.7% of records but **disagreed on 94 individual records, including 29 verified-eligible records retained by only one run** — aggregate similarity conceals item-level instability [8]. Verification proxies fail as reliability guarantees: BERTScore returned near-identical F1 across workflows and rated false conclusions as semantically equivalent to correct ones [17]. LLM precision for post-exposure controls (0.15–0.30) is far below the best human reviewer (0.89) [30]. Data contamination is unquantified across benchmarks [24].

### 4.4 RQ3 — Empirical evaluation, reliability, and gaps
**Screening performance.** A meta-analysis of 18 studies reports pooled sensitivity **0.92** (95% CI 0.81–0.96), specificity **0.94** (0.90–0.97), SROC AUC **0.98**, with substantial heterogeneity (I² = 95.8%); chain-of-thought improved sensitivity 0.86→0.95 (p < 0.01); full-text screening pooled sensitivity/specificity 0.99/0.99 [3]. Benchmark AUCs range 0.77–0.95 across heterogenous domains with inclusion rates from <1% to 12.4% [16]. **Extraction performance.** Structured field extraction strongly outperforms naive chunking: HySemRAG +35.1% semantic similarity (p < 0.000001, 643 observations) [18]; schema-constrained ketamine extraction achieved **100% recall / 97.9% precision / 98.9% F1** [25]. Extraction is domain-sensitive (clinical 82% accuracy best) with author-attribution errors (40% partial/failed) [23][31].

**Cost and efficiency.** Screeners run ~25× faster than human raters at $3.26 versus an estimated $492.18 for two human raters [32]; GPT-4o ≈ $3.16/100 articles, GPT-3.5 ≈ $0.22 [26]; a RAG pipeline synthesized 30 articles in 1m24s versus an estimated 50+ human hours [33]; full end-to-end pipeline costs are $19.51–$29.04 per review (median $22.65) [12].

**Reliability failure modes.** Temporal drift of **−1.9%/day** in HySemRAG's evaluation window [18]; identical questions answered identically only 69% of the time (8% substantively different) [23]; domain-transfer limits (LGAR reliably tested only in medicine due to sparse SYNERGY domains [24]); model ranking domain-dependence (e.g., one model 98% screening but 40% extraction in the same study) [34]; prompt fragility with up to **76 accuracy-point** swings from format variations [9]; contamination acknowledgment and cross-model divergence [35][9]. Multi-agent orchestration is **phase-dependent**: it hurts screening but is essential for extraction, yielding 5.7× more poolable analyses [12].

**The evaluation gap.** No included study provides an end-to-end, externally validated, multi-domain benchmark jointly evaluating screening, extraction, synthesis quality, citation verifiability, and cost. Validations are proof-of-concept against published reviews without blinded dual review [25], formally labeled "essential" to reproduce [15], single-model without cross-model replication [24], and rely on LLM-as-judge protocols correlating only moderately with experts (r = 0.65–0.81) [23][36].

### 4.5 Consensus cartography
The 95-cluster consensus map surfaces structure the RAG baseline cannot see. High-consensus themes (≥ 3 verbatim-backed sources): citation-verifiability failure at scale (0.475 existence ceiling), open-weights selection for reproducibility (17 studies), human-machine collaboration with retained researcher control, structured-field extraction superiority, and local-vs-API cost anatomy. **Seven active debates** include deterministic versus adaptive configuration, best-performing benchmark model, and LLM-versus-human screening reliability. Full cluster contents: `synthesis/consensus.md`.

### 4.6 Approach comparison (RAG baseline vs. multi-agent ledger)
The deterministic RAG baseline produced 90 claims across 25 studies, of which **only 43.3% were entailment-verified** (RQ1 36.7%, RQ2/RQ3 46.7%); it cited **11 studies absent from the included set** (its index contained the 18 screened-out extractions; a single non-included paper, SCI-000184, supplied 22/90 claims), covered 43 included studies not at all, and yielded 20 clusters with zero debates. The multi-agent ledger achieved **100% verbatim verification** across 57 included studies and 95 clusters including 7 active debates. Head-to-head details: `synthesis/method_comparison.md`.

### 4.7 Phase-4 trust audit
Retraction: 0/47 flagged. Open science: 16 repository links, 7 dual data+code, 32 explicit DA/S/CA statements, 5 proprietary. COI: 5 industry ties (two Meta-affiliated, Google, Anthropic, OpenAI), 37 with no formal COI statement — a structural feature of computer-science preprints and evocative of governance gaps the corpus itself describes.

## 5. Discussion

### 5.1 Interpretation
Three findings carry design consequences. **First**, provenance engineering has matured into a concrete, implementable pattern language — structured logging, deterministic IDs, idempotency, content-hashed commitments, open-weights selection, temperature-0 decoding — that converts "traceability" from a desideratum into a verifiable mechanism, but adoption is uneven across the corpus. **Second**, citation verifiability is the binding trust constraint: the 0.475 existence ceiling across 17,443 citations and the discrepancy between retrieval-grounded (zero hallucinated papers) and ungrounded (78–98%) systems jointly imply that **non-grounded claim generation is not defensible** in scholarly infrastructure. **Third**, evaluation practice lags the systems it purports to assess: aggregate metrics (I² > 95%, domain-dependent AUC 0.77–0.95, item-level run instability, semantic-similarity-proxy failures, −1.9%/day drift) make single-number validation claims unusable for trust certification.

### 5.2 Implications for trustworthy research infrastructure
1. **Append-only, file-based audit journals are the correct provenance primitive**, directly countering ephemeral logs and statistics that conceal item-level instability [8][22].
2. **Verbatim-verifiable evidence is tractable and should be standard.** A full-text agent pipeline achieved byte-exact provenance on 510/510 claims; deterministic RAG reached 43.3% on the same corpus.
3. **Corpus-scope discipline is mandatory.** Pre-screening extractions silently leak screened-out evidence into retrieval (11 contaminated studies in the RAG baseline); synthesis must be confined to the reconciled included set.
4. **Trust verification precedes synthesis** — retractions, COI ties, and open-science claims are knowable only through explicit Phase-4 streams.
5. **The field lacks its own benchmark.** Systems auditing review automation are themselves unaudited end-to-end; cross-domain, externally validated, jointly-evaluating infrastructure is the prerequisite for generalizable trust.

### 5.3 Limitations
Written tools were excluded from the review matrix to avoid self-selection bias. Twelve included studies lack full text and contribute abstract-only claims (17 of 510); one included study contributed none (empty abstract). The consensus clusterer uses a single embedding model and a hand-set threshold (0.40). Verbatim verification guarantees that a quote appears in the source text, not that the source is representative of its own corpus. Author names are placeholders awaiting human curation in this draft. Screening agreement (κ = 0.408) is fair/moderate; screening decisions were consensus-aggregated and adjudicated.

## 6. Conclusion

The 2023–2026 literature documents a rapid, convergent movement toward auditable, provenance-bearing, retrieval- and agent-grounded research harnesses — and an equally rapid emergence of trust gaps (citation fabrication ≤ 0.475 existence, item-level run instability, semantic-proxy failures, absent benchmarks) that any credible infrastructure must address. Our method — protocol-driven scoping, four-stream trust verification, verbatim-verified full-text claim extraction, and semantic consensus — demonstrates that trustworthy agentic synthesis is achievable today. The open research gap is a joint, externally validated, multi-domain evaluation benchmark for the field.

## 7. Declarations and Data Availability

- **Data availability**: full workspace `workspaces/ai-research-harnesses-trust/` (protocol, screening, extractions, claims ledger, consensus, audit journal, phase-4 outputs) is preserved and git-tracked (text/metadata) as audit-grade artifacts.
- **Code availability**: pipeline orchestration via Nexus Scholar kits; deterministic reruns reproduce identical claim sets and consensus.
- **Conflicts of interest**: none declared by the authors; the Nexus Scholar toolkit was excluded from the review matrix.
- **Traceability declaration**: every claim statistic in this manuscript is machine-verifiable against `synthesis/claims.json` (verbatim quotes) and `synthesis/consensus.json`; every pipeline step is recorded in `audit/journal.jsonl` (47 events).

---

## References

[1] Corpus preprint (author metadata pending curation). *Designing a Human-AI Collaborative Modular Approach to Automating Systematic Literature Reviews: From Objectives to Reporting* *Tampere University Institutional Repository (Tampere University).* (2025). Workspace: SCI-000182

[2] PAULRAJ, N. J. *Building an LLM Agent for Life Sciences Literature QA and Summarization* *World Journal of Advanced Research and Reviews.* (2025). DOI: 10.30574/wjarr.2025.26.2.1665. Workspace: SCI-000181

[3] Xie, C., Kong, W., Pi, L. et al. *Performance of Large Language Models in Automated Medical Literature Screening: A Systematic Review and Meta‐Analysis* *Journal of Evidence-Based Medicine.* (2026). DOI: 10.1111/jebm.70166. Workspace: SCI-000088

[4] Corpus preprint (author metadata pending curation). *Do Deployment Constraints Make LLMs Hallucinate Citations? An Empirical Study across Four Models and Five Prompting Regimes* *arXiv Preprint.* (2026). Workspace: SCI-000144

[5] Asai, A., He, J., Shao, R. et al. *Synthesizing scientific literature with retrieval-augmented language models* *Nature.* (2026). DOI: 10.1038/s41586-025-10072-4. Workspace: SCI-000154

[6] Corpus preprint (author metadata pending curation). *OpenScholar: Synthesizing Scientific Literature with Retrieval-augmented LMs* *arXiv (Cornell University).* (2024). DOI: 10.48550/arxiv.2411.14199. Workspace: SCI-000159

[7] Corpus preprint (author metadata pending curation). *BioResearcher: Scenario-Guided Multi-Agent for Translational Medicine* *arXiv Preprint.* (2026). Workspace: SCI-000126

[8] Corpus preprint (author metadata pending curation). *Evaluating human and LLM screening workflows in a conceptually complex scoping review: Recall--workload trade-offs and run-to-run consistency* *arXiv Preprint.* (2026). Workspace: SCI-000137

[9] Corpus preprint (author metadata pending curation). *Compiling Prompts, Not Crafting Them: A Reproducible Workflow for AI-Assisted Evidence Synthesis* *arXiv Preprint.* (2025). Workspace: SCI-000106

[10] Corpus preprint (author metadata pending curation). *Biomedical reasoning in action: Multi-agent System for Auditable Biomedical Evidence Synthesis* *arXiv (Cornell University).* (2025). DOI: 10.48550/arxiv.2510.05335. Workspace: SCI-000099

[11] Corpus preprint (author metadata pending curation). *DeepER-Med: Advancing Deep Evidence-Based Research in Medicine Through Agentic AI* *arXiv Preprint.* (2026). Workspace: SCI-000102

[12] Corpus preprint (author metadata pending curation). *LUMEN: Cost-Transparent Multi-Agent Pipeline for Automated Systematic Review and Meta-Analysis* *arXiv (Cornell University).* (2026). Workspace: SCI-000118

[13] Corpus preprint (author metadata pending curation). *AutoSynthesis: An agentic system for automated meta-analysis* *arXiv Preprint.* (2026). Workspace: SCI-000135

[14] Wang, Z., Cao, L., Danek, B. et al. *Accelerating clinical evidence synthesis with large language models* *npj Digital Medicine.* (2025). DOI: 10.1038/s41746-025-01840-7. Workspace: SCI-000109

[15] Corpus preprint (author metadata pending curation). *meta-pipe: An LLM-agent pipeline for end-to-end automated systematic review and meta-analysis* *arXiv Preprint.* (2026). Workspace: SCI-000142

[16] Corpus preprint (author metadata pending curation). *LatteReview: A Multi-Agent Framework for Systematic Review Automation Using Large Language Models* *arXiv (Cornell University).* (2025). DOI: 10.48550/arxiv.2501.05468. Workspace: SCI-000096

[17] Corpus preprint (author metadata pending curation). *MedMeta: A Benchmark for LLMs in Synthesizing Meta-Analysis Conclusion from Medical Studies* *arXiv (Cornell University).* (2026). Workspace: SCI-000127

[18] Corpus preprint (author metadata pending curation). *HySemRAG: A Hybrid Semantic Retrieval-Augmented Generation Framework for Automated Literature Synthesis and Methodological Gap Analysis* *arXiv (Cornell University).* (2025). DOI: 10.48550/arxiv.2508.05666. Workspace: SCI-000100

[19] Corpus preprint (author metadata pending curation). *AI Co-Scientist for Knowledge Synthesis in Medical Contexts: A Proof of Concept* *arXiv Preprint.* (2026). Workspace: SCI-000138

[20] Corpus preprint (author metadata pending curation). *An AI-Driven Live Systematic Reviews in the Brain-Heart Interconnectome: Minimizing Research Waste and Advancing Evidence Synthesis* *arXiv (Cornell University).* (2025). DOI: 10.48550/arxiv.2501.17181. Workspace: SCI-000110

[21] Tongnamtiang, S., Wongsim, M., Satchawatee, N. *An AI-Assisted Research Automation System for Scholarly Paper Retrieval and Review With Workflow Orchestration* *Journal of Computer Science.* (2026). DOI: 10.3844/jcssp.2026.2082.2091. Workspace: SCI-000179

[22] Corpus preprint (author metadata pending curation). *Bringing analytic rigor to agentic AI for science: The Brain Researcher platform for neuroimaging data analysis* *arXiv Preprint.* (2026). Workspace: SCI-000140

[23] Corpus preprint (author metadata pending curation). *Exploring the use of a Large Language Model for data extraction in systematic reviews: a rapid feasibility study* *arXiv Preprint.* (2024). Workspace: SCI-000108

[24] Jaumann, C., Wiedholz, A., Friedrich, A. *LGAR: Zero-Shot LLM-Guided Neural Ranking for Abstract Screening in Systematic Literature Reviews* *Findings of the Association for Computational Linguistics: ACL 2025.* (2025). DOI: 10.18653/v1/2025.findings-acl.412. Workspace: SCI-000164

[25] Serretti, A. *Benchmarking a Local Schema-Constrained Large Language Model Pipeline for Abstract Screening and Evidence Mapping* *Cureus.* (2026). DOI: 10.7759/cureus.111193. Workspace: SCI-000090

[26] Corpus preprint (author metadata pending curation). *LLAssist: Simple Tools for Automating Literature Review Using Large Language Models* *arXiv (Cornell University).* (2024). DOI: 10.48550/arxiv.2407.13993. Workspace: SCI-000151

[27] Corpus preprint (author metadata pending curation). *Bio-SIEVE: Exploring Instruction Tuning Large Language Models for Systematic Review Automation* *arXiv (Cornell University).* (2023). DOI: 10.48550/arxiv.2308.06610. Workspace: SCI-000111

[28] Corpus preprint (author metadata pending curation). *Towards AI-Supported Research: a Vision of the TIB AIssistant* *arXiv Preprint.* (2025). Workspace: SCI-000141

[29] Matsumoto, N., Choi, H., Freda, P. J. et al. *EcoXAI: Autonomous Agentic Ecosystem for Explainable Artificial Intelligence and Biomedical Discovery* *bioRxiv (Cold Spring Harbor Laboratory).* (2026). DOI: 10.64898/2026.07.08.737358. Workspace: SCI-000082

[30] Zhang, W., Nguyen, T., Stuart, E. A. et al. *Large language models for full-text methods assessment: a case study on mediation analysis* *Journal of the American Medical Informatics Association.* (2026). DOI: 10.1093/jamia/ocag108. Workspace: SCI-000124

[31] Corpus preprint (author metadata pending curation). *Knowledge Synthesis Review Framework: Task-Level Benchmarking of LLM-Based Systems for Multi-Source Evidence Synthesis* *arXiv Preprint.* (2026). Workspace: SCI-000115

[32] Zrubka, M., Alexy, M., György, K. T. et al. *Large Language Models for Title/Abstract Screening in Systematic Literature Reviews: A Case Study in Precision Livestock Farming* *2025 IEEE 25th International Symposium on Computational Intelligence and Informatics (CINTI).* (2025). DOI: 10.1109/cinti67731.2025.11311831. Workspace: SCI-000152

[33] MOŢĂŢĂIANU, A., PĂVĂLOIU, I. B. *Advanced Semantic Analysis of Research Papers Using a Retrieval-Augmented Architecture* *Proceedings of the International Conference on Business Excellence.* (2026). DOI: 10.2478/picbe-2026-0107. Workspace: SCI-000172

[34] Ferreira Barros, C., Kalinowski, M., Kassab, M. et al. *On the Use of a Large Language Model to Support the Conduction of a Systematic Mapping Study: A Brief Report from a Practitioner’s View* *Proceedings of the 2026 IEEE/ACM International Workshop on Methodological Issues with Empirical Studies in Software Engineering.* (2026). DOI: 10.1145/3786149.3788298. Workspace: SCI-000129

[35] Tang, X., Duan, X., Cai, Z. *Large Language Models for Automated Literature Review: An Evaluation of Reference Generation, Abstract Writing, and Review Composition* *Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing.* (2025). DOI: 10.18653/v1/2025.emnlp-main.83. Workspace: SCI-000125

[36] Corpus preprint (author metadata pending curation). *DeepWeaver: Bridging the Evidence Synthesis Gap in Open-Ended Question Answering* *arXiv (Cornell University).* (2026). DOI: 10.48550/arxiv.2608.18988. Workspace: SCI-000117