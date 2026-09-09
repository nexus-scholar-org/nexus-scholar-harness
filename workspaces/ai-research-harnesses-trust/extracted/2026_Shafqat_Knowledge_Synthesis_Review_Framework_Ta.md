---
workspace_id: "SCI-000115"
doi: null
title: "Knowledge Synthesis Review Framework: Task-Level Benchmarking of LLM-Based Systems for Multi-Source Evidence Synthesis"
year: 2026
extraction_engine: "pymupdf"
---
# 2026 Shafqat Knowledge Synthesis Review Framework Ta

Knowledge Synthesis Review Framework: Task-Level Bench- marking of LLM-Based Systems for Multi-Source Evidence Synthesis

Wafa Shafqat1, Mark Patterson1,2 and Steven Liss1,2,3,4,5,6

1Magnet, Toronto Metropolitan University, Toronto, M5B2K3, Ontario, Canada. 2Future skill center, Toronto Metropolitan University, Toronto, M5B2K3, Ontario, Canada. 3Office of the Vice-President Research and Innovation, Toronto Metropolitan University, Toronto, M5B2K3, Ontario, Canada. 4Department of Chemistry and Biology, Toronto Metropolitan University, Toronto, M5B2K3, Ontario, Canada. 5Professor Emeritus, Environmental Studies, Queen’s University, Kingston, K7L3N6, Ontario, Canada. 6Professor Extraordinaire, Department of Microbiology, Stellenbosch University, South Africa. E-mail: steven.liss@torontomu.ca;ovpri@torontomu.ca.

Keywords: large language models (LLMs), evidence synthesis, future of work, human-in-the-loop, model benchmarking

arXiv:2608.12741v1  [cs.IR]  13 Aug 2026


## Abstract

Evidence in rapidly evolving fields is fragmented across academic studies, industry reports, policy documents,
and media sources that differ in quality, structure, and purpose, making timely synthesis difficult. Large language
models (LLMs) may accelerate this work, but their reliability across the distinct cognitive tasks of a review remains
uncertain. We introduce the Knowledge Synthesis Review (KSR), a human-in-the-loop framework that decomposes
evidence synthesis into screening, extraction, analysis, and synthesis, benchmarks LLM-based systems on each task
against expert reference standards, and routes each task to the best-performing system under continuous expert
validation. We evaluated GPT-5, Claude Sonnet 4, Gemini 2.5 Pro, and NotebookLM on a 244-document benchmark
subset drawn from a 1,893-document corpus on AI and work spanning four source types, against a gold standard
with high inter-rater reliability (92.2% agreement, 𝜅= 0.80). No system led on all tasks. Claude Sonnet 4 achieved
the highest screening accuracy (82.8%) and GPT-5 the highest recall (91.8%) at the expense of lower specificity.
Extraction exceeded 90% agreement for titles and sources but degraded in author and reference fields. Performance
declined most in interpretive analysis and cross-source synthesis, where expert judgment remained essential. A
contamination check on post-cutoff documents showed no evidence that prior exposure inflated results. Applied
to the full corpus, the routed workflow surfaced cross-source asymmetries and blind spots that single-source
synthesis would miss, including worker well-being, small firms, and the Global South. KSR offers a transparent,
auditable, model-agnostic framework for governing LLM assistance in research synthesis while preserving human
accountability.


## 1. Introduction

Evidence synthesis faces a growing structural problem in fast-moving research domains: the relevant evidence is dispersed across source types that differ fundamentally in quality, structure, incentives, and intended audience. Peer-reviewed research, industry reports, policy briefs, and media commentary each capture part of the picture, yet traditional systematic review methods were designed primarily for relatively homogeneous bodies of academic literature and can take anywhere from six months to over a year to complete [1]. In domains where technologies, organizational practices, and policy debates evolve quickly, this creates a widening lag between evidence generation and evidence synthesis, and it leaves

2

the public conversation to be shaped by whichever individual sources circulate most widely rather than by the balance of evidence.

The relationship between artificial intelligence (AI) and labor markets illustrates this problem sharply, and serves as the demonstration domain for this study. For example, in May 2024, the McKinsey Global Institute projected that generative AI could automate up to 30% of work hours by 2030 [2]. A subsequent 2025 study of AI chatbots in Denmark combined survey and administrative data on approximately 25,000 workers across 7,000 workplaces, spanning 11 occupations with high AI exposure [3]. It found no statistically significant changes in aggregate output, hours worked, or wages within the first year of adoption. These findings do not contradict McKinsey’s long-term automation scenario; they concern a shorter time horizon, a specific set of occupations, and a particular class of tools. However, their reception diverged sharply. The McKinsey projection received broad public and corporate visibility, while the Danish evidence appears to have reached primarily academic and policy audiences. Prior work indicates that media framing shapes public understanding of AI and can influence both adoption and governance [4]. This pattern of uneven reception, where projections tend to reach wider audiences than empirical findings, calls for a more systematic approach to synthesizing evidence across source types, at a pace traditional review methods cannot sustain.

Large language models (LLMs) offer a practical response. They are already embedded in how researchers, analysts, and policymakers process and produce knowledge [5, 6], and excluding them from a study of AI-assisted knowledge work would overlook a central feature of how knowledge production is currently evolving. However, using LLMs without a structured framework carries real risks. They can favor fluency over rigor [7, 8], and blur the boundaries between research and speculation [8, 9]. Recent evaluations conclude that LLMs are not yet reliable enough to conduct systematic reviews autonomously [10, 11]. Moreover, most existing evaluations of LLM assistance in reviews concentrate on individual stages, most often title and abstract screening, within relatively homogeneous and well- structured literatures such as clinical and biomedical research [11, 12, 13, 14]. Empirical tests of hybrid human-AI review workflows remain limited [11, 15], particularly evaluations that (a) span all core stages of a review, (b) compare multiple LLM-based systems on the same corpus against a common expert-annotated gold standard, and (c) do so over deliberately heterogeneous evidence that mixes peer- reviewed and grey literature. The key methodological challenge, then, is to develop LLM-assisted review processes that are systematic, transparent, comparative, and governed by expert judgment.


> **Figure 1. Overview of the three-phase KSR framework. Phase I constructs a multi-source corpus**

> of 1,893 documents and selects 244 for benchmarking. Phase II uses human-in-the-loop evaluation
to refine prompts, outputs, and evaluation protocols. Phase III applies model-agnostic, task-specific
routing across the corpus..

3

To address these gaps, we introduce the knowledge synthesis review (KSR) framework (Fig. 1), a structured workflow designed to make LLM-assisted evidence synthesis systematic, replicable, and expert-guided. KSR proceeds in three phases. Phase I constructs a multi-source evidence base of 1,893 documents spanning research papers (RPs), industry reports (IRs), policy briefs (PBs), and news, media, and blog sources (NMBs), directly responding to the source fragmentation described above. Phase II decomposes the review process into four cognitive tasks, namely screening, extraction, analysis, and synthesis, and benchmarks four widely used LLM-based systems (GPT-5, Claude Sonnet 4, Gemini 2.5 Pro, and NotebookLM) on each task against gold standards established by expert evaluators on a 244-document benchmark subset. Phase III operationalizes the benchmark results as a model-agnostic orchestration layer that routes each task to the system with the strongest demonstrated performance for that task, over shared retrieval infrastructure, while maintaining expert validation throughout.

The study addresses two research questions (RQs):

• RQ1: How do widely used LLM-based systems perform across the four core tasks of evidence synthesis (screening, extraction, analysis, and synthesis) and across heterogeneous source types, when evaluated against expert-annotated gold standards? • RQ2: How can task-level performance differences be translated into a transparent, human-guided orchestration workflow, and what does applying that workflow at scale reveal about the capabilities and limits of LLM-assisted synthesis in a fast-moving, multi-source evidence domain?

The paper’s primary contribution is methodological: a task-level benchmark of four contemporary LLM-based systems across the core cognitive tasks of evidence synthesis over heterogeneous sources, and, building on it, the KSR framework, a transparent and replicable workflow in which task-specific model routing is governed throughout by expert human validation. Because system capabilities evolve rapidly, KSR is designed to be model-agnostic: its task decomposition, evaluation rubrics, and routing logic can be reapplied as new models appear. As a secondary contribution, we apply KSR end-to-end to the full AI-and-work corpus. This demonstration shows the framework operating on real, uneven evidence and reveals how different source types emphasize different aspects of the same phenomenon, a pattern that synthesis from any single source type would miss. We therefore present the resulting labor- market observations as outputs of the evidence synthesis, useful for identifying patterns, asymmetries, and gaps across sources, rather than as direct empirical estimates of AI’s labor-market effects.


## 2. Methods

The proposed KSR framework was implemented in three sequential phases as illustrated in Fig. 1. Phase I focused on corpus construction, in which a multi-source evidence base was developed, cleaned, and organized into a curated document corpus, from which a benchmark subset was selected for expert review and model comparison. Phase II focused on task categorization and human-in-the-loop protocol development. In this phase, we first categorize the review process into four core knowledge synthesis tasks. Each task was conducted by expert evaluators and LLMs using structured prompts, standardized output formats, and iterative refinements based on model evaluations. Phase III addressed the model- agnostic task orchestration and scaling. The results of phase II informed the task-specific routing across the curated corpus. Rather than relying on a single model for all review stages, the framework assigned each task to the model that demonstrated the strongest empirical performance while preserving human oversight throughout1.

1The use of LLMs in this study was part of the research methodology and is described throughout this section. All LLM-assisted outputs were subject to human review, validation, and author accountability.

4

2.1. Phase I: Knowledge Base Creation

We constructed a multi-source corpus to capture diverse perspectives on the evolving relationship between AI and labor markets. Overall, the full corpus comprises 1,893 documents spanning RPs, IRs, PBs, and NMBs (2020–2025). Table 1 shows the composition of the entire corpus from which the benchmark subset was selected for human evaluation and model comparison. The distribution reflects the actual landscape of publicly available evidence on AI and labor markets, where news and media sources substantially outnumber academic and policy documents. We preserved this imbalance to represent the evidence environment as it exists. The smaller samples of IRs and PBs (n=30 each) reflect the limited volume of such documents publicly available on this topic rather than a sampling choice.

For academic research, we selected sources from leading databases, including Web of Science, ScienceDirect, Google Scholar, IEEE Xplore, Nature, Science, and Springer. We prioritized Q1–Q2 journals, to ensure high research quality, with the exception of a few Q3 articles, for their citation strength or topical novelty. Industry reports were chosen for their authority and relevance from organizations such as National Bureau of Economic Research2, McKinsey & Company3, Bureau of Labor Statis- tics4, World Economic Forum5, International Labour Organization (ILO)6, PricewaterhouseCoopers (PwC)7, LinkedIn8, Organization for Economic Co-operation and Development (OECD)9 , Deloitte10, The International Monetary Fund11. Policy briefs were collected from Economic Policy Institute12, Mas- sachusetts Institute of Technology (MIT)13, Stanford Human-Centered Artificial Intelligence (HAI)14, OECD, ILO. Media and commentary included publications from Forbes15, Brookings16, International Business Machines Corporation (IBM)17, Google News18, and Chicago Booth Review19.

2.2. Phase II: Task Categorization and Human-in-the-Loop Protocol Development

2.2.1. Human-in-the-Loop Benchmark Design For human-in-the-loop evaluation, we assembled a 244-document benchmark subset. It includes 103 research papers (RP), 30 industry reports (IR), 30 policy briefs (PB), and 81 news/media/blogs (NMB) articles, as shown in Table 1. Documents were identified via systematic keyword searches (AI and labor market, impacts of AI on work, societal impacts of AI, AI and the future of work). This curated dataset enables a balanced view across scholarly, industrial, policy, and public discourse. Because industry reports and policy briefs were scarce, all available documents of these two types were included; research papers and news/media sources were subsampled to keep expert review tractable while retaining sufficient documents per source type for meaningful cross-model comparison. The benchmark subset therefore deliberately over-represents the scarce, higher-credibility source types relative to the full corpus, in order to ensure each source type was adequately evaluated.

All tasks in the KSR workflow involve interaction between LLM-generated outputs and human review checkpoints. The framework was designed to incorporate structured human oversight, in which expert

2https://www.nber.org/ 3https://www.mckinsey.com 4https://www.bls.gov/ 5https://www.weforum.org/ 6https://www.ilo.org/ 7https://www.pwc.com/ca/en.html 8https://www.linkedin.com/ 9https://www.oecd.org/ 10https://www.deloitte.com/ 11https://www.imf.org/en/home 12https://www.epi.org/ 13https://web.mit.edu/ 14https://hai.stanford.edu/ 15https://www.forbes.com/ 16https://www.brookings.edu/ 17https://www.ibm.com/ 18https://news.google.com/ 19https://www.chicagobooth.edu/review

5


> **Table 1. Knowledge types, selection criteria, and document counts before and after processing.**

Source Type Predefined criteria Full Corpus

Benchmark

subset RP (Research papers) Peer-reviewed, methodological transparency, academic venue 324 103 IR (Industry reports) Firm-produced, forward-looking, profit-linked claims 30 30 PB (Policy briefs) Government or NGO-affiliated, policy-oriented, implementation-focused 30 30 NMB (News, media, and blogs)

(n)

Non-peer-reviewed, narrative-driven, public engagement goal 1509 81

Total 1893 244

reviewers assess model outputs at each stage of the workflow using predefined task-specific criteria. This human-in-the-loop design ensures that model performance is not evaluated only by whether an output is fluent or complete, but also by whether it is accurate, relevant, source-grounded, and useful for knowledge synthesis. Rather than reserving human evaluation for the final synthesis stage, oversight was embedded throughout to prevent error propagation, as inaccuracies in early stages such as screening and extraction can systematically distort downstream analysis and synthesis.

Primary benchmark evaluation was conducted by two field experts, one member of the author team and one evaluator external to, and independent of, the project with expertise in the AI field. To limit bias toward any particular system, all model outputs were anonymized and randomized prior to evaluation, so that evaluators could not identify which system had produced a given output. To assess the reliability of the screening gold standard, the two expert reviewers independently labeled each screened document as include or exclude prior to any reconciliation. Inter-rater reliability was measured using Cohen’s kappa, calculated for each source type and across all screened documents. We also report raw percent agreement, because kappa is sensitive to skewed label distributions. Across 244 screened documents, the two reviewers agreed on 92.2 percent of decisions (kappa = 0.804). Agreement was stable across source types, with kappa values of 0.718 for policy briefs, 0.831 for industry reports, 0.818 for research papers, and 0.812 for news and media sources, indicating that the screening criteria were applied consistently across heterogeneous evidence types. Documents on which the reviewers initially disagreed were resolved through consensus to produce the final screening decisions; 183 documents (RP=79, IR=21, PB=21, NMB=62) were retained for extraction, analysis, and synthesis after deduplication. For the extraction task, model outputs were scored against the source documents by comparing each extracted field to the verified record, with matches graded as exact, partial, or absent. For the analysis and synthesis tasks, outputs were assessed by the two reviewers against predefined rubrics, and scores were reconciled through the same consensus process. Each task was evaluated using structured prompts, standardized output formats, and predefined scoring rubrics. Depending on the task, outputs were assessed on dimensions such as accuracy, completeness, clarity, relevance, source fidelity, reasoning quality, and usefulness. Quantitative ratings, including one-to-five scores where appropriate, were combined with qualitative reviewer comments to identify task-level strengths, weaknesses, and recurring failure patterns across models. Each task in the KSR workflow (Fig. 2) has distinct evaluation criteria. Screening evaluates whether sources are correctly included or excluded according to predefined eligibility criteria and whether the rationale is appropriate.

Extraction assesses the accuracy and completeness of structured fields, including metadata, methods, findings, and links to supporting evidence. Analysis focuses on interpretive quality, thematic relevance, methodological insight, and the ability to identify limitations, gaps, and implications. Synthesis evaluates coherence, coverage, integration across sources, reduction of redundancy, and the quality of broader conclusions drawn from multiple evidence streams.

2.2.2. Task-Specific Review Protocols Task 1: Screening Screening was conducted to determine whether each document should be included in the KSR corpus for further extraction, analysis, and synthesis. Each document was assigned a binary

6

label of include or exclude. RPs were screened using titles, abstracts, and keywords, while PBs, IRs, and NMBs were screened using titles and executive summaries. To standardize model inputs, these fields were converted into JSON files and provided to each LLM using the same screening prompt structure.

The screening prompts reflected the manual inclusion and exclusion criteria used by the expert reviewers. Documents were required to be written in English and to demonstrate a clear theoretical, empirical, or policy connection between AI and labor market outcomes. Documents were included if they substantively addressed topics such as automation, employment, wages, skills, productivity, occupational change, organizational transformation, inequality, reskilling, or labor-market policy. Documents were excluded when the available title, abstract, keywords, or summary did not establish a substantive connection to AI-related labor-market outcomes.

The screening protocol was refined iteratively during the benchmark process. Early versions of the prompts included article links, but this approach was unreliable because most models could not consistently access or interpret external sources, with the exception of GPT-5 with web search enabled. In some cases, models generated judgments based only on titles rather than the full screening fields available in the JSON input (Appendix Fig. A1-A3). Additional issues included overlapping outputs, inconsistent rationales, and formatting errors. To address these limitations, the final protocol used simplified natural-language instructions, JSON-formatted inputs, and standardized .xlsx outputs. This stepwise protocol improved consistency across models and allowed screening decisions, rationales, and model outputs to be systematically compared (Appendix Fig. A4).

Task 2: Extraction The extraction task evaluated the ability of LLMs to convert unstructured or semi-structured source documents into standardized metadata records. Extraction prompts were tailored to each document type to reflect differences in source structure and available information (Appendix Fig. A5). For RPs, models extracted the document name, title, author(s), publication source, year, and the number of tables, figures, and references. For IRs and PBs, extraction focused on the document name, title, author(s), issuing organization, and year.

For NMBs, the schema captured the document name, title, issuing body or publisher, publication date, authorship, and links to relevant scholarly sources where available. The extracted fields were returned in structured formats, such as JSON or spreadsheet-compatible outputs, to support downstream analysis and comparison across models. Model outputs were evaluated against the source documents to assess field accuracy, completeness, consistency with the required schema, and source reliability. This task, therefore, tested not only whether models could identify relevant metadata but also whether they could produce standardized, machine-readable records suitable for integration into the broader KSR workflow.

Task 3: Analysis The analysis task evaluated the ability of LLMs to identify and summarize sub- stantive, interpretive content from each source type (Appendix Fig. A6). Unlike the extraction task, which focused on structured metadata, the analysis task required models to interpret document content and identify source-specific analytical elements relevant to AI and labor market impacts. For RPs, mod- els extracted three key dimensions: study limitations, future research directions, and a summary of the methodology. For IRs, the analysis focused on current limitations, key findings, and recommendations. For PBs, models identified gaps in existing policies, proposed interventions, and anticipated outcomes. For NMBs, analysis focused on reported limitations, core findings, and future implications. All outputs were returned as structured JSON objects to support comparison across models and integration into the synthesis stage. This task tested whether LLMs could move beyond factual extraction to produce structured analytical summaries that preserved the meaning and context of the original sources.

Task 4: Synthesis The synthesis task evaluated the ability of LLMs to produce integrative, cross- source narratives from the curated document corpus (Appendix Fig. A7). Unlike the analysis task, which focused on source-specific analytical elements, synthesis required models to integrate evidence across RPs, IRs, PBs, and NMBs. Synthesis prompts guided the models to address six core dimensions: overarching labor-market impacts of AI, stakeholder narratives, cross-source integration, temporal patterns, governance and ethics, and key challenges. Models were also asked to identify proposed

7

(a)

(b) Figure 2. The KSR framework: (a) Four LLMs perform screening, extraction, analysis, and synthesis on the same sources using standardized prompts, with expert refinement and evaluation producing task- level performance profiles. (b) These results guide task-specific model routing and generate harmonized outputs in formats such as XLSX and JSON.

future directions and blind spots in the evidence base. Outputs were returned as structured narratives to support comparison across models and integration into the final KSR findings. The synthesis task used the preprocessed and chunked corpus described in Section 2.1, allowing models to retrieve and integrate relevant evidence across the full document set. The synthesis outputs were evaluated for coherence, coverage, source integration, reduction of redundancy, source reliability, and usefulness for generating higher-level conclusions. This task tested whether LLMs could move beyond document-level analysis to produce integrated knowledge claims across heterogeneous evidence streams.

8

2.2.3. Model Selection and Comparative Evaluation We evaluated four widely used LLM-based systems including: GPT-5, Claude Sonnet 4, Gemini 2.5 Pro, and NotebookLM. These models were selected to represent the leading general-purpose LLMs available at the time of the study, based on their widespread use and distinct functional profiles. Each model was queried via API or web interface using standardized and identical prompts. To reduce evaluator bias, outputs were anonymized and randomized before assessment. This design provided a controlled basis for comparing model performance across the four KSR tasks.

2.2.4. Evaluation Metrics and Statistical Analysis Performance was assessed using task-specific evaluation metrics. Performance in the screening stage was evaluated using a confusion matrix based on the expert-labeled gold standard. A document was considered a True Positive (TP) when both the LLM and the expert classified it as Include. A False Positive (FP) occurred when the LLM classified a document as Include but the expert classified it as Exclude. A False Negative (FN) occurred when the LLM classified a document as Exclude but the expert classified it as Include. Finally, a True Negative (TN) occurred when both the LLM and the expert classified a document as Exclude. From these quantities, we computed the following evaluation metrics:

• Precision: To measure the proportion of documents predicted as relevant that were actually relevant. A higher precision indicates greater resistance to false positives.

Precision = 𝑇𝑃 𝑇𝑃+ 𝐹𝑃 (1)

• Recall: To measure the proportion of truly relevant documents that were successfully identified by the model. A higher recall indicates a lower risk of missing relevant evidence.

Recall = 𝑇𝑃 𝑇𝑃+ 𝐹𝑁 (2)

• Specificity: To evaluate the proportion of irrelevant documents that were correctly excluded.

Specificity = 𝑇𝑁 𝑇𝑁+ 𝐹𝑃 (3)

• Accuracy measures the overall proportion of correctly classified documents, considering both relevant and irrelevant studies.

Accuracy = 𝑇𝑃+ 𝑇𝑁 𝑇𝑃+ 𝑇𝑁+ 𝐹𝑃+ 𝐹𝑁 (4)

• F1-score is the harmonic mean of precision and recall, providing a balanced measure when both false positives and false negatives are important.

𝐹1 = 2 × Precision × Recall

Precision + Recall (5)

For extraction, we measured accuracy at the field level. For fixed metadata fields, such as author names, publication years, dates, and document titles, a correct extraction required an exact string match with the expert-verified record. For open-ended or variable text fields, matches were graded as PERFECT, SEMI, or NONE, reflecting full, partial, or absent correspondence with the target information.

For analysis, the model output was evaluated for each document, field, and LLM. The expert reviewers assessed the quality of the generated response to determine whether an output was relevant, sufficiently

9

detailed, well developed, credible, clearly written, and appropriate for the type of source and ana- lytical field being evaluated. Each output was assessed using six dimensions: relevance, specificity, completeness, evidence, clarity & structure, and a field-specific criterion.

Each dimension was scored on a five-point scale. A score of 1 indicated that the expected content was largely absent, incorrect, or off-topic. A score of 2 indicated a limited attempt with substantial weaknesses. A score of 3 represented an acceptable response that was relevant but remained generic, incomplete, or uneven. A score of 4 indicated a strong response that addressed most expectations but retained minor gaps. A score of 5 represented an excellent response that was highly relevant, specific, comprehensive, credible, clearly structured, and appropriate for the assigned source category and field. Responses containing no substantive content, or fewer than ten words, received a score of 1 across all dimensions because there was insufficient information for meaningful evaluation. The overall score was calculated as the mean of the six evaluation dimensions and rounded to the nearest whole number.

For synthesis, the outputs were evaluated according to their ability to integrate evidence across source types and generate coherent higher-level conclusions. The evaluation criteria included balance between critique and technical detail, quality of source integration, coverage of key themes, narrative coherence, reduction of redundancy, and usefulness to identify broader patterns, gaps, and future directions.

2.2.5. Validation and Bias Mitigation To strengthen methodological integrity, the KSR framework adopted a multi-stage validation and bias mitigation process. First, all outputs generated by LLMs were reviewed against predefined task-specific criteria. Screening decisions, extracted data, analytical summaries, and synthesis results were evaluated for accuracy, completeness, relevance, source reliability, and interpretive quality. Second, conflicting findings were flagged and retained rather than merged into a single narrative. For example, claims about productivity gains were considered alongside evidence on wage stagnation, job insecurity, occupational polarization, and unequal benefit distribution. This method allowed the synthesis to preserve tensions across different source types, stakeholder viewpoints, and time frames. Third, source credibility was assessed based on criteria like peer-review status, transparency of methods, institutional affiliation, and potential conflicts of interest. This was important because the corpus included diverse evidence from academic research, policy briefs, industry reports, and news/media/blog sources. The analytic rubric enabled consistent evaluation of interpretive quality. Synthesis prompts integrated evidence across different time frames while maintaining contradictions and gaps. Task-specific model routing further minimized reliance on any single model, reducing the impact of model-specific weaknesses on the overall review. The validated process was first tested on the 244-document benchmarking corpus and then applied to the full corpus. This provided a controlled basis for comparing model performance and for generating the main synthesis reported in the results.

A recognized risk when evaluating commercial LLMs on publicly available documents is training data contamination: because the corpus consists of public documents published between 2020 and 2025, some may have been part of the models’ training data, so measured extraction performance could reflect prior exposure rather than genuine processing of the supplied text. To assess this, we compared extraction accuracy on documents published after the models’ training cutoffs, which they could not have encountered during training, against accuracy on the full corpus. We took the most recent training cutoff among the evaluated systems (April 2025) as the threshold, classifying documents published after it as post-cutoff. The three systems with defined training cutoffs (GPT-5, Claude Sonnet 4, Gemini 2.5 Pro) were assessed; NotebookLM was excluded because it performs its own retrieval over uploaded documents and does not expose a comparable training cutoff. The check was conducted on news and media sources, which had enough post-cutoff documents to support a stable comparison; research papers, policy briefs and industry reports had too few documents published after the cutoff to assess separately. Post-cutoff documents were identified by verified original publication date. Extraction accuracy was

10

computed field by field on identical prompts and inputs, differing only in publication date, and pooled per system for comparison (see Table 2).


> **Table 2. Field-level extraction accuracy for NMB documents on the full corpus and pre- and post-cutoff**

> subsets, by model.

Model Field Full (%) Pre (%) Post (%) Post N

Title 98.4 97.1 100.0 27 Year 67.7 57.1 81.5 27 Source 96.8 94.3 100.0 27 Author 62.9 48.6 81.5 27 Links 74.2 77.1 70.4 27 Total 80.0 74.9 86.7 135

GPT-5

Title 95.2 91.4 100.0 27 Year 71.0 57.1 88.9 27 Source 91.9 85.7 100.0 27 Author 67.7 54.3 85.2 27 Links 75.8 80.0 70.4 27 Total 80.3 73.7 88.9 135

Claude

Title 96.8 94.3 100.0 27 Year 74.2 60.0 92.6 27 Source 95.2 94.3 96.3 27 Author 66.1 51.4 85.2 27 Links 40.3 31.4 51.9 27 Total 74.5 66.3 85.2 135

Gemini

2.3. Phase III: Model-Agnostic Task Orchestration and Scaling

Phase III applied the validated KSR workflow from the benchmark subset to the full corpus using a model-agnostic orchestration strategy. This phase used the finalized task-specific prompts, preprocessed document chunks, and model performance summaries generated during Phase II to guide task-specific model routing. A central component of this phase was a shared retrieval-augmented generation (RAG) infrastructure. The curated corpus was cleaned, semantically chunked, validated, de-duplicated, and stored in ChromaDB20. This retrieval layer was shared across models, meaning that GPT-5, Claude Sonnet 4, Gemini 2.5 Pro, and NotebookLM were provided access to the same underlying evidence base. The purpose of this shared retrieval layer was to keep model comparison and task execution grounded in a common corpus, reduce dependence on each model’s internal knowledge, and minimize variation caused by unequal access to evidence. The model performance summaries served as performance memory, capturing which models performed strongest for screening, extraction, analysis, and synthesis. Screening tasks were routed based on classification performance, including precision, recall, accuracy, and specificity. Extraction tasks were routed based on field-level accuracy and schema consistency. Analysis tasks were routed based on relevance, completeness, source reliability, interpretive quality, and clarity. Synthesis tasks were routed based on coherence, source integration, thematic coverage, and the ability to preserve contradictions and blind spots.

For each routed task, the orchestration layer combined three elements: the task-specific prompt template, the relevant retrieved context from the shared RAG layer, and the best-fit model identified through performance memory. Outputs were then returned in harmonized formats, including .xlsx screening results, structured JSON extraction and analysis outputs, and narrative synthesis files. Human

20https://www.trychroma.com/products/chromadb

11

oversight remained part of the workflow, with expert review used to validate routed outputs, monitor recurring failure modes, and ensure alignment with the task criteria established in Phase II.

The shared retrieval layer was used by the three systems queried via API or standard interface (GPT-5, Claude Sonnet 4, Gemini 2.5 Pro). NotebookLM, which performs its own internal retrieval over uploaded documents and exposes no interface to an external vector store, was instead given the same source documents and operated over its native retrieval. Rather than relying on one model across all review tasks, KSR uses shared retrieval infrastructure and task-specific routing to combine model strengths while preserving source grounding, comparability, and human review.


## 3. Results

This section presents the findings organized around the two research questions introduced above. We first address RQ1 by reporting model-level benchmark performance across the four KSR tasks. We then address RQ2 by presenting the human-guided synthesis of labor-market evidence across six analytical sub-questions.

3.1. Model Performance Varies Systematically by Task and Source Type

In screening, Claude Sonnet 4 achieved the most balanced performance, with an accuracy of 82.8% (Fig. 3) and the most balanced performance across metrics. It consistently constrained false positives, particularly in PB and NMB, where precision reached 70%, making it well-suited to final filtering stages where over-inclusion is costly. GPT-5, in contrast, demonstrated the strongest recall (91.8%) and excelled in RP and IR, but its specificity collapsed in PB (53.3%), where it misclassified all true exclusions as inclusions. Gemini 2.5 Pro and NotebookLM adopted more conservative strategies, reducing false positives at the cost of higher false negatives (Fig. 4). Together, these patterns confirm that screening behavior is context dependent.

In extraction, all models robustly identified titles and publishing sources, with match rates exceeding 90%. Author attribution and reference identification, however, remained error prone, with up to 40% of attempts yielding partial matches or failures, reflecting known challenges in parsing unstructured text [16]. Claude Sonnet 4 provided the most consistent performance overall (Fig. 5) and was particularly strong in linking NMB articles to underlying scholarly references (match rate of 76%). Gemini 2.5 Pro specialized in PB extraction, achieving near-perfect accuracy on titles and sources, whereas GPT- 5 underperformed sharply in this category (32%). NotebookLM maintained mid-range performance without leading in any field.

In analysis, methodological and key-finding summaries were the strongest outputs across models, with mean scores around 4.0 out of 5.0 (Fig. 6), reflecting the models’ ability to produce coherent narratives. Performance dropped markedly on forward-looking tasks, however: future directions averaged only 2.9–3.5, with NotebookLM scoring as low as 1.53 on PB, and limitations were similarly underdeveloped, suggesting the models struggle with critical appraisal. Claude Sonnet 4 ranked highest overall, leading in methodology summaries for RP (4.18) and achieving near-ceiling specificity in IR. Across source types, IRs yielded the richest analytical outputs, whereas PBs exposed persistent weaknesses in extrapolation and domain contextualization.

In synthesis, we evaluated LLMs on their ability to generate coherent, comprehensive, and policy- relevant narratives from heterogeneous evidence on AI’s labor-market impacts. Each model was prompted to address six analytical dimensions: overarching economic and social consequences; framing of stakeholder narratives; integration of academic, industry, policy, and media perspectives; temporal and sectoral trajectories; governance and ethical challenges; and identification of unresolved questions and future research directions.

12

(a) (b) Figure 3. Screening performance evaluation: (a) Accuracy of GPT-5, Claude, Gemini, and NotebookLM across four document categories: IR, NMB, PB, and RP. (b) Overall accuracy of LLMs averaged across all datasets. Claude achieved the highest overall accuracy (82.8%), followed by GPT-5 (ChatGPT) (Claude Sonnet 4.9%), Gemini (74.2%), and NotebookLM (73.8%).

GPT-5 and NotebookLM produced the most nuanced outputs, addressing all six dimensions in rich detail and surfacing underexplored issues such as risks to small enterprises and the invisibility of informal economies. Claude Sonnet 4 and Gemini 2.5 Pro provided more schematic summaries, effective for rapid orientation but less suited to deep integration. Notably, all models preserved pluralism, acknowledging contradictions across sources, yet they shared key limitations: visualizations were sparse, attention to cultural diversity was uneven, and human-centered concerns such as worker well-being were weakly integrated.

Across the four tasks, no system led consistently. Claude Sonnet 4 emerged as the most reliable all-rounder, combining high precision with consistent extraction and balanced analysis, while GPT-5 was best suited to initial broad screening given its high recall, though its low specificity necessitates downstream filtering. Gemini 2.5 Pro showed narrow specialization in structured domains such as PB, and NotebookLM offered moderate performance across tasks without leading in any. All systems scored lower on completeness and field-specific depth, indicating that although they often write clearly and specifically, they do not consistently capture domain-critical facets such as stakeholder impacts or methodological constraints. This pattern aligns with prior findings that model-generated summaries can appear fluent while remaining incomplete or unfaithful to source material [17], and that LLMs can struggle to use relevant information across long contexts [18].

3.1.1. Robustness to training data contamination To test whether prior exposure inflated extraction performance, we compared accuracy on documents published after the providers’ training cutoffs with accuracy on the full corpus. The check was conducted on news and media sources, where 27 of 60 documents fell after the cutoff, a large enough share to support a stable comparison; other source types contained too few post-cutoff documents to assess separately. Table 2 reports, for each model and extraction field, accuracy on the full corpus (Full), on documents published before the cutoff and therefore potentially seen during training (Pre), and on the 27 post-cutoff documents the models could not have encountered (Post N = 27), with Total giving each model’s accuracy aggregated across all five fields.

Post-cutoff accuracy showed no decline for any system. Total post-cutoff accuracy was 86.7 percent for GPT-5, 88.9 percent for Claude, and 85.2 percent for Gemini, against full-corpus values of 80.0,

13


> **Figure 4. Confusion matrices for screening performance by dataset and model. Each matrix displays**

> true vs. predicted inclusion (INCL) and exclusion (EXCL) decisions across four document categories.
Across datasets, all models show stronger recall for “INCL” decisions than for “EXCL” decisions.

80.3, and 74.5 percent. High-baseline fields such as title and source remained at or near ceiling on post- cutoff documents, while the only field to fall was links to scholarly articles, which was weak across all systems regardless of publication date.

The post-cutoff subset consists largely of uniformly structured articles from major outlets, which are easier to extract from than the more heterogeneous pre-cutoff material, so the higher post-cutoff scores likely reflect source composition rather than a genuine capability difference. The relevant finding is the absence of any systematic performance drop on unseen documents, indicating that prior exposure did not inflate the reported extraction results.

3.2. Demonstration: Applying KSR to AI and Work Corpus

The second half of RQ2 asks what applying the routed workflow at scale reveals about the capabilities and limits of LLM-assisted synthesis in a fast-moving, multi-source domain. This section summarizes the substantive output of that application, organized around three questions: what the synthesized evidence shows, how source types diverge in emphasis, and where the evidence base is systematically thin. We present these observations as outputs of the evidence synthesis, useful for identifying patterns,

14

(a) (b) (c)

(d) (e) (f)

(g) (h) (i)

(j) (k) (l)


> **Figure 5. Extraction performance across document categories. Panels (a–c) show extraction accuracy**

> for RP, including field-wise accuracy by model (a), overall model accuracy (b), and the field model
weighted accuracy heatmap (c). Panels (d–f) summarize performance for NMB. Panels (g–i) present
results for IR. Panels (j–l) depict performance for PB.

asymmetries, and gaps across sources, rather than as direct empirical estimates of AI’s labor-market effects.

3.2.1. What the Synthesized Evidence Shows A shared pattern emerges across source types: AI is more often framed as transforming work than elimi- nating jobs wholesale. Peer-reviewed studies emphasize occupational exposure, firm-level restructuring, and labor-market adjustment [19, 20], while related economic evidence points to distributional conse- quences such as shifts in labor share and regional inequality [21]. Policy and institutional reports frame these changes in terms of worker exposure, policy readiness, and risks of uneven transition [22, 23, 24].

15

(a) (b)

(c) (d)


> **Figure 6. Comparative analysis of mean overall scores across knowledge sources. Each panel shows**

> the average performance (1–5 scale) of LLMs (GPT-5/ChatGPT, Claude, Gemini, and NotebookLM)
across document categories: (a) RP, (b) NMB, (c) IR, and (d) PB. Bars represent mean scores for
task dimensions such as future directions, current limitations, and category-specific subfields (e.g., key
findings and policy interventions discussed).

Industry sources highlight changing skill demands and emerging forms of human–AI collaboration [25, 26]. Commentary sources foreground public-facing concerns about job disruption and the social choices shaping AI’s impact on work [27, 28].

The synthesis also surfaces convergence on two higher-order claims. First, AI’s labor-market impact is not determined by technology alone: outcomes depend on regulation, economic incentives, institutional power, workforce policy, and societal adaptation [21, 27, 28, 29, 30, 31, 32]. Second, exposure is uneven. Knowledge occupations in science, technology, legal, and creative fields face substantial task disruption but also greater potential for augmentation, whereas workers with weaker bargaining power or limited access to training, including low-wage service and care workers, are less positioned to benefit from AI- enabled transitions [24, 29, 33, 34, 35, 36]. Temporally, the evidence organizes into short-term firm-level experimentation with limited economy-wide employment effects (0 to 5 years) [25, 34, 37, 38, 39, 40], medium-term job churn and rising demand for hybrid human-AI skills (5 to 10 years) [33, 35, 36, 40], and more uncertain long-term institutional restructuring. Geographically, projected impacts diverge with digital infrastructure, institutional capacity, and sectoral composition, raising particular concerns for lower- and middle-income contexts including parts of the Global South [32, 34, 40].

3.2.2. Source Asymmetries and Cross-Source Convergence The methodologically significant result of the demonstration is how systematically the source types diverge in tone and emphasis while agreeing on core facts. Media and commentary sources often oscillate between alarmist and optimistic framings, while industry reports tend to emphasize productivity, wage growth, and business opportunity [41, 42]. Research and policy sources adopt more conditional or mixed framings, emphasizing exposure, uncertainty, policy readiness, and uneven transition risks [20, 28, 43, 44, 45]. Each type also carries characteristic omissions: industry reports underweight ethical concerns

16

such as algorithmic surveillance, hiring bias, and absent safety nets; media coverage amplifies immediate disruption over structural adjustment; academic findings remain fragmented across disciplines.

All four evidence types agree that AI simultaneously displaces and creates jobs, and that routine, lower-skill roles face the highest automation risk even as cognitive white-collar tasks encounter new exposure. Consensus is weaker on priorities: only one of the four source types treats reskilling as a strong current market priority, with the remainder rating it moderate, indicating a gap between what is widely acknowledged as necessary for the future and what present employment systems emphasize. A synthesis drawn from any single source type would inherit that type’s framing and omissions; the divergences documented here are visible only because the corpus was constructed across types, which is the design rationale established in Section 2.

Across source types, several recurring gaps emerge, although they are emphasized unevenly. Industry reports tend to foreground competitiveness and productivity [25, 37, 41], while policy briefs focus more on redistribution, risk mitigation, and institutional preparedness [22, 28, 45]. Considering these observations, the synthesis suggests that AI’s labor-market effects are not only technological but also structural: they reveal existing inequalities in skills, bargaining power, institutional capacity, and access to opportunity. Its long-term impact will therefore depend on how effectively societies design policies that ensure technological change advances inclusion rather than deepening division.

3.2.3. Governance and Policy Responses for Equitable AI Transitions The evidence points to a consistent message across sources that markets alone are unlikely to ensure equitable outcomes from AI adoption, because risks and benefits are shaped by institutions, labor-market power, regulation, and organizational choices [22, 27, 28, 44, 45, 46]. Recurring policy implications include embedding AI literacy, regulatory foresight, and equitable access to reskilling within labor and education systems [28, 44, 47, 48]. Several sources support an anticipatory governance approach that prioritizes early investment, long-term planning, and inclusive dialogue among governments, employers, workers, and educational institutions before disruptions become entrenched [27, 45, 46, 49]. Policy recommendations, therefore, center on large-scale reskilling, adaptive and socio-emotional skills, worker voice, and modernized regulation for AI-mediated and non-standard forms of employment. In workplace contexts, stronger monitoring and auditing mechanisms are also needed to address bias, transparency, and accountability in AI-enabled hiring and management systems [50, 51].

Despite the breadth of evidence, systematic blind spots still remain. Empirical analysis of small and medium enterprises is limited, leaving their exposure and adaptive capacity poorly understood relative to large corporations. Although emerging research shows that AI exposure can affect workers’ health, well-being, and everyday work experience [36, 47], worker well-being still receives insufficient attention, particularly the mental health consequences of AI adoption, including anxiety, surveillance stress, and diminished autonomy. Frameworks for worker empowerment remain underdeveloped, as sources frequently discuss technical skills and reskilling [25, 41], but rarely offer concrete strategies for strengthening worker agency, participatory governance, or meaningful AI literacy. Diverse perspectives are also insufficiently integrated in labor market analyses, including environmental implications, gender disparities, and cultural and regional contexts [22, 51].


## 4. Discussion

This study addresses two linked challenges: the fragmentation of evidence in fast-moving domains across source types that differ in methods, incentives, and evidentiary standards, and the difficulty of synthesizing such evidence at scale without sacrificing rigor. We proposed treating evidence synthesis as a set of distinct cognitive tasks, benchmarking system performance at each, and routing accordingly under continuous expert oversight.

17

The benchmark shows that no single system performed consistently well across screening, extrac- tion, analysis, and synthesis. Model strengths were complementary and task-specific, with some better suited to screening and structured extraction and others to long-context analysis. Performance declined on tasks requiring interpretive judgment, cross-source comparison, credibility assessment, or preserva- tion of conflicting claims. These findings align with and extend previous work on AI-assisted evidence synthesis. Existing studies show that LLMs can improve efficiency in screening and information extrac- tion, particularly in relatively homogeneous and well-structured domains such as clinical and biomedical evidence synthesis [11, 12, 13, 14, 52]. However, recent reviews also caution that LLMs are not yet reliable enough to conduct systematic reviews autonomously, especially where tasks require method- ological judgment, source appraisal, contextual interpretation, and transparent handling of uncertainty or disagreement [10, 53]. This makes structured human oversight essential for complex socio-economic evidence synthesis.

The study highlights why the design of AI-assisted synthesis workflows matters, with implications for both evidence-synthesis methodology and AI governance. First, LLM-assisted synthesis should not be treated as a single automated process, but as a sequence of tasks requiring different levels of model support and human validation. Second, because system behaviors shape which evidence is surfaced, how it is summarized, and which claims are emphasized, oversight must be operationalized through auditable workflows, transparent prompt and model documentation, explicit evaluation criteria, and mechanisms for preserving disagreement across sources. This aligns with broader AI governance work arguing that human oversight must be meaningful, institutionally supported, and embedded in system design rather than treated as a superficial or post-hoc safeguard [54, 55]. Prompt design also proved to be a critical methodological choice, with consistent outputs requiring multiple rounds of human-guided refinement across source types. Prior research has shown that LLMs can be sensitive to prompt phrasing and formatting [56], may align with user assumptions [57], may produce fluent but ungrounded content [58], and can underweight information positioned in the middle of long contexts [18]. In evidence synthesis, these limitations are not merely technical problems; they can shape the knowledge claims that inform policy and organizational decisions. This reinforces the need for transparent and auditable AI-assisted review workflows, including documentation of model choice, prompt design, retrieval procedures, evaluation criteria, and human review decisions. Because LLM capabilities evolve rapidly, KSR is designed so that its task decomposition, rubrics, and routing logic persist while the routing table is re-derived as new systems appear, reducing dependence on any single system’s blind spots.

Applying KSR end-to-end to the AI-and-work corpus illustrated the framework operating on real, uneven evidence and yielded substantive observations reported in Section 3.2. AI is reorganizing work unevenly: routine clerical and administrative tasks show greater exposure to automation, while many judgment-intensive roles are more often reshaped through augmentation and task redesign [2, 59, 60]. At the same time, projected productivity gains do not yet translate consistently into improved worker outcomes. Experimental and organizational studies show productivity improvements from AI adoption [2, 61, 62, 63], while short-term labor-market evidence suggests weaker or uneven effects on wages, hours worked, and output [3]. These patterns suggest that gains may be delayed, unevenly distributed, or captured more by firms and capital owners than by workers.

Several gaps remain visible across the corpus. Early-career workers, worker well-being, surveil- lance, autonomy, the Global South, informal economies, lower-resource firms, and the effectiveness of reskilling programs receive less systematic attention than productivity, skills, and competitiveness. For the methodological argument, the salient point is that these cross-source asymmetries and absences were detectable only because the corpus was constructed across source types and the workflow was designed to preserve disagreement. Which evidence becomes visible, and which circulates, is itself a determinant of public and policy understanding, and synthesis workflows either counteract or reproduce that unevenness.

18

The study has several limitations. First, the corpus is primarily English-language and text-based, leaving the performance of KSR on multilingual, visual, or non-textual evidence untested. Second, the evaluated models represent a 2025 baseline; as model capabilities evolve, their relative performance may change with new releases. Third, the routing strategy is motivated by task-level benchmark differences but was not validated end-to-end against a single-system baseline on held-out documents, and the efficiency claim is not yet quantified in time or cost; both are priorities for future work. Fourth, although screening reliability was high (𝜅= 0.80), reliability statistics were not computed for the analysis and synthesis rubric scores, which were reconciled through consensus and remain sensitive to the reviewers’ expertise, disciplinary backgrounds, and rubric design.

Future research should address these limitations by repeating the KSR benchmarking protocol with newer models, larger reviewer panels, multilingual corpora, and additional domains beyond AI and labor markets. It should also examine how shared retrieval infrastructures, audit trails, and transparent documentation of model choices and workflow decisions can improve the reliability of LLM-assisted evidence synthesis. Overall, the findings suggest that the value of LLMs in evidence synthesis lies not in automation but in augmentation, freeing human reviewers to focus their judgment where it matters most while maintaining accountability for the overall process. For fast-moving domains such as AI and labor markets, where evidence is large, heterogeneous, and unevenly visible, this balance between computational scale and critical human oversight is not a methodological preference but a practical necessity.


## 5. Conclusion

Evidence in fast-moving domains is scattered across academic research, industry reports, policy briefs, and media sources, each shaped by different methods, incentives, and audiences, and traditional review methods cannot synthesize it at the pace the domains evolve. This study introduced the Knowledge Syn- thesis Review (KSR) framework to address that challenge, combining multi-source corpus construction, task-level benchmarking of LLM-based systems against expert gold standards, performance-based task routing, and structured human oversight, demonstrated end-to-end on a 1,893-document corpus on AI and labor markets.

The paper makes two connected contributions. Methodologically, it provides a task-level, multi- system benchmark over deliberately heterogeneous sources, showing that system performance is task-specific and source-specific rather than universally reliable: no system led on all four tasks, and source type moderated performance throughout. These results imply that LLM-assisted synthesis is best decomposed into discrete cognitive tasks, each matched to the system best suited to it, with human judgment governing the whole through finalized task protocols, explicit rubrics, and auditable documen- tation. Validating routed against single-system and human-only baselines, with explicit time and cost accounting, is the immediate next step. As a demonstration, the application to the AI-and-work corpus showed the framework detecting cross-source asymmetries, preserved disagreements, and systematic blind spots, including worker well-being, small firms, informal economies, and the Global South, that synthesis from any single source type would have missed.

KSR’s central contribution is not tied to any particular generation of models or LLM-assisted systems but to a durable design: task decomposition, evaluation rubrics, and routing logic that persist while the routing table is re-derived as systems evolve. For research synthesis in fast-moving and socially consequential domains, the framework offers a replicable way to use LLMs for scale while keeping human judgment, transparency, and accountability as the governing layer of knowledge production.

Funding Statement. No funding information available.

Competing Interests. The authors declare no competing interests.

19

Use of Artificial Intelligence Tools. GPT-5, Claude Sonnet 4, Gemini 2.5 Pro, and NotebookLM were used as research instruments in the screening, extraction, analysis, and synthesis tasks evaluated in this study. Their versions, prompts, outputs, and human-validation procedures are described in the Methods. AI tools were also used during manuscript preparation to assist with language refinement.

Data Availability Statement. Data and code supporting the findings of this study are available from the authors upon request.

Ethical Standards. The research meets all ethical guidelines.


## References

[1] Rohit Borah, Andrew W Brown, Patrice L Capers, and Kathryn A Kaiser. Analysis of the time and workers needed to

conduct systematic reviews of medical interventions using data from the prospero registry. BMJ open, 7(2):e012545, 2017.

[2] McKinsey Global Institute. A new future of work: The race to deploy ai and raise skills in europe and beyond. https://ww

w.mckinsey.com/mgi/our-research/a-new-future-of-work-the-race-to-deploy-ai-and-raise-skills-in-europe-and-beyond?, 2024. Accessed 7 June 2026.

[3] Anders Humlum and Emilie Vestergaard. Large language models, small labor market effects, volume 33777. National

Bureau of Economic Research Cambridge, MA, 2025.

[4] Leila Ouchchy, Allen Coin, and Veljko Dubljević. Ai in the headlines: the portrayal of the ethical issues of artificial

intelligence in the media. AI & Society, 35(4):927–936, 2020.

[5] Qusai Khraisha, Sophie Put, Johanna Kappenberg, Azza Warraitch, and Kristin Hadfield. Can large language models replace

humans in systematic reviews? evaluating gpt-4’s efficacy in screening and extracting data from peer-reviewed and grey literature in multiple languages. Research Synthesis Methods, 15(4):616–626, 2024.

[6] Francisco Bolanos, Angelo Salatino, Francesco Osborne, and Enrico Motta. Artificial intelligence for literature reviews:

Opportunities and challenges. Artificial Intelligence Review, 57(10):259, 2024.

[7] Mikaël Chelli, Jules Descamps, Vincent Lavoué, Christophe Trojani, Michel Azar, Marcel Deckert, Jean-Luc Raynier, Gilles

Clowez, Pascal Boileau, Caroline Ruetsch-Chelli, et al. Hallucination rates and reference accuracy of chatgpt and bard for systematic reviews: comparative analysis. Journal of medical Internet research, 26(1):e53164, 2024.

[8] Ziwei Ji, Nayeon Lee, Rita Frieske, Tiezheng Yu, Dan Su, Yan Xu, Etsuko Ishii, Ye Jin Bang, Andrea Madotto, and Pascale

Fung. Survey of hallucination in natural language generation. ACM computing surveys, 55(12):1–38, 2023.

[9] Mike Perkins. Academic integrity considerations of ai large language models in the post-pandemic era: Chatgpt and beyond.

Journal of University Teaching and Learning Practice, 20(2):1–24, 2023.

[10] Judith-Lisa Lieberum, Markus Toews, Maria-Inti Metzendorf, Felix Heilmeyer, Waldemar Siemens, Christian Haverkamp,

Daniel Böhringer, Joerg J Meerpohl, and Angelika Eisele-Metzger. Large language models for conducting systematic reviews: on the rise, but not yet ready for use—a scoping review. Journal of Clinical Epidemiology, 181:111746, 2025.

[11] Justin Clark, Belinda Barton, Loai Albarqouni, Oyungerel Byambasuren, Tanisha Jowsey, Justin Keogh, Tian Liang, Christian

Moro, Hayley O’Neill, and Mark Jones. Generative artificial intelligence use in evidence synthesis: A systematic review. Research Synthesis Methods, pages 1–19, 2025.

[12] Fernando M Delgado-Chaves, Matthew J Jennings, Antonio Atalaia, Justus Wolff, Rita Horvath, Zeinab M Mamdouh,

Jan Baumbach, and Linda Baumbach. Transforming literature screening: The emerging role of large language models in systematic reviews. Proceedings of the National Academy of Sciences, 122(2):e2411962122, 2025.

[13] Ying Li, Surabhi Datta, Majid Rastegar-Mojarad, Kyeryoung Lee, Hunki Paek, Julie Glasgow, Chris Liston, Long He,

Xiaoyan Wang, and Yingxin Xu. Enhancing systematic literature reviews with generative artificial intelligence: development, applications, and performance evaluation. Journal of the American Medical Informatics Association, 32(4):616–625, 2025.

[14] Zifeng Wang, Lang Cao, Benjamin Danek, Qiao Jin, Zhiyong Lu, and Jimeng Sun. Accelerating clinical evidence synthesis

with large language models. npj Digital Medicine, 8(1):509, 2025.

[15] Faisal Saeed Malik and Orestis Terzidis. A hybrid framework for creating artificial intelligence-augmented systematic

literature reviews. Management Review Quarterly, pages 1–27, 2025.

20

[16] Dominika Tkaczyk, Paweł Szostek, Mateusz Fedoryszak, Piotr Jan Dendek, and Łukasz Bolikowski. Cermine: automatic

extraction of structured metadata from scientific literature. International Journal on Document Analysis and Recognition (IJDAR), 18(4):317–335, 2015.

[17] Joshua Maynez, Shashi Narayan, Bernd Bohnet, and Ryan McDonald. On faithfulness and factuality in abstractive sum-

marization. In Proceedings of the 58th annual meeting of the association for computational linguistics, pages 1906–1919, 2020.

[18] Nelson F Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy Liang. Lost in

the middle: How language models use long contexts. Transactions of the Association for Computational Linguistics, 12: 157–173, 2024.

[19] Dirk Nicolas Wagner. The nature of the artificially intelligent firm-an economic investigation into changes that ai brings to

the firm. Telecommunications Policy, 44(6):101954, 2020.

[20] Ali Zarifhonarvar. Economics of chatgpt: A labor market view on the occupational impact of artificial intelligence. Journal

of Electronic Business & Digital Economics, 3(2):100–116, 2024.

[21] Antonio Minniti, Klaus Prettner, and Francesco Venturini. Ai innovation and the labor share in european regions. European

Economic Review, page 105043, 2025.

[22] International Labour Organization. Work transformed: The promise and peril of artificial intelligence. https://www.ilo.or

g/sites/default/files/2025-07/ilo%20brief%20work%20transformed%20promise%20and%20peril%20of%20ai.pdf, 2025. Accessed 10 May 2026.

[23] International Economic Development Council. Artificial intelligence impact on labor markets. https://www.iedconline.org

/clientuploads/EDRP%20Logos/AI_Impact_on_Labor_Markets.pdf, 2025. Accessed 10 May 2026.

[24] Janine Berg, Mark Graham, Marek Havrda, Matthias Peissner, Saiph Savage, Basheerhamad Shadrach, Fernando Scha-

pachnik, Alexandre Shee, Lucía Velasco, and Kyoko Yoshinaga. Policy brief: Generative ai, jobs, and policy response. https://fair.work/wp-content/uploads/sites/17/2023/10/Policy-Brief-The-big-unknown.pdf, 2023. Accessed 10 May 2026.

[25] LinkedIn Economic Graph. Future of work report: Ai at work. https://economicgraph.linkedin.com/content/dam/me/econ

omicgraph/en-us/PDF/future-of-work-report-ai-november-2023.pdf, 2023. Accessed 10 May 2026.

[26] Amanda Downie and Molly Hayes. Ai in the workplace: Digital labor and the future of work. https://www.ibm.com/think/

topics/ai-in-the-workplace, 2026. Accessed 18 June 2026.

[27] Daron Acemoglu and Simon Johnson. Choosing ai’s impact on the future of work. https://ssir.org/articles/entry/ai-impac

t-on-jobs-and-work, 2023. Accessed 10 May 2026.

[28] Emily McGrath and Michelle Lavere. Labor market disruption and policy readiness in the ai era. https://tcf.org/content/co

mmentary/labor-market-disruption-and-policy-readiness-in-the-ai-era/, 2025. Accessed 10 May 2026.

[29] Josh Bivens and Ben Zipperer. Unbalanced labor market power is what makes technology—including ai—threatening to

workers: The best “ai policy” to protect workers is boosting their bargaining position. https://www.epi.org/publication/ai-u nbalanced-labor-markets/, 2024. Accessed 10 May 2026.

[30] Philippe Lorenz, Karine Perset, and Jamie Berryhill. Initial policy considerations for generative artificial intelligence.

https://www.oecd.org/content/dam/oecd/en/publications/reports/2023/09/initial-policy-considerations-for-generative-artif icial-intelligence_1a9ab450/fae2d1e6-en.pdf, 2023. Accessed 10 May 2026.

[31] Qiang Wang, Fuyu Zhang, and Rongrong Li. Artificial intelligence and sustainable development during urbanization:

Perspectives on ai r&d innovation, ai infrastructure, and ai market advantage. Sustainable Development, 33(1):1136–1156, 2025.

[32] Qin Chen, Jinfeng Ge, Huaqing Xie, Xingcheng Xu, and Yanqing Yang. Large language models at work in china’s labor

market. China Economic Review, page 102413, 2025.

[33] Sonia Chien-I Chen, Chuanming Zhang, and Chung-Ming Own. Artificial intelligence and employment: A delicate balance

between progress and quality in china. Applied Sciences, 15(9):4729, 2025.

21

[34] International Labour Organization. Generative ai and jobs: A 2025 update. https://www.ilo.org/publications/generative-a

i-and-jobs-2025-update, 2025. Accessed 10 May 2026.

[35] Noah Oder and Daniel Béland. Artificial intelligence, emotional labor, and the quest for sociological and political imagination

among low-skilled workers. Policy and Society, 44(1):116–128, 2025.

[36] Osea Giuntella, Johannes Konig, and Luca Stella. Artificial intelligence and the wellbeing of workers. Scientific Reports,

15(1):20087, 2025.

[37] LinkedIn Economic Graph. Work change report: Ai is coming to work. https://economicgraph.linkedin.com/research/work

-change-report, 2025. Accessed 10 May 2026.

[38] Chih-Hai Yang. How artificial intelligence technology affects productivity and employment: Firm-level evidence from

taiwan. Research Policy, 51(6):104536, 2022.

[39] Inga Fechner and Charlotte de Montpellier. Ai will fundamentally transform the job market but the risk of mass unemployment

is low. https://think.ing.com/articles/ai-will-fundamentally-transform-job-market-but-risk-of-mass-unemployment-is-l ow/, 2024. Accessed 10 May 2026.

[40] World Economic Forum. Future of jobs report 2025. https://reports.weforum.org/docs/WEF_Future_of_Jobs_Report_202

5.pdf, 2025. Accessed 10 May 2026.

[41] PwC. The fearless future: 2025 global ai jobs barometer. https://www.pwc.com/gx/en/issues/artificial-intelligence/job-bar

ometer/2025/report.pdf, 2025. Accessed 10 May 2026.

[42] Paola Cecchi-Dimeglio. How ai will transform the labor market: Essential insights for leaders. https://www.forbes.com

/sites/paolacecchi-dimeglio/2024/09/17/how-ai-will-transform-the-labor-market-essential-insights-for-leaders/, 2024. Accessed 10 May 2026.

[43] Samir Huseynov. Chatgpt and the labor market: Unraveling the effect of ai discussions on students’ earning expectations.

Journal of Economic Psychology, 108:102803, 2025.

[44] Sunny Jiang, Yesilernis Pena, Dell Gines, Todd Lang, and Melanie Hwang. Artificial intelligence impact on labor markets.

https://www.iedconline.org/clientuploads/EDRP%20Logos/AI_Impact_on_Labor_Markets.pdf, 2025. International economic development council, Accessed 10 May 2026.

[45] OECD. Assessing potential future artificial intelligence risks, benefits and policy imperatives. https://www.oecd.org/conte

nt/dam/oecd/en/publications/reports/2024/11/assessing-potential-future-artificial-intelligence-risks-benefits-and-policy-i mperatives_8a491447/3f4e3dfb-en.pdf, 2024. Accessed 10 May 2026.

[46] Nicky Dries, Joost Luyckx, Ute Stephan, and David G Collings. The future of work: A research agenda. Journal of

Management, 51(5):1689–1706, 2025.

[47] Romana Emilia Cramarenco, Monica Ioana Burcă-Voicu, and Dan Cristian Dabija. The impact of artificial intelligence (ai)

on employees’ skills and well-being in global labor markets: A systematic review. Oeconomia Copernicana, 14(3):731–767, 2023.

[48] Maria Rita Mancaniello and Francesco Lavanga. Adolescence in the italian labour market: In search of an equilibrium

among instability, uncertainty, and ai challenges. Social Sciences, 13(12):688, 2024.

[49] Andrius Grybauskas, Alessandro Stefanini, and Morteza Ghobakhloo. Social sustainability in the age of digitalization: A

systematic literature review on the social implications of industry 4.0. Technology in society, 70:101997, 2022.

[50] J Stewart Black and Patrick van Esch. Ai-enabled recruiting in the war for talent. Business Horizons, 64(4):513–524, 2021.

[51] Mahmut Özer, Matjaz Perc, and H. Eren Suna. Artificial intelligence bias and the amplification of inequalities in the labor

market. Journal of Economy Culture and Society, (69):159–168, 2024.

[52] Paul Loustalot, Boris Kopin, Sacha Levy, Basile Ferry, and Vincent Martenot. Msr72 development of an ai-powered tool

to accelerate and enhance systematic literature reviews for evidence-based decision making in clinical research. Value in Health, 28(12):S507, 2025.

22

[53] Lesley Uttley, Daniel S Quintana, Paul Montgomery, Christopher Carroll, Matthew J Page, Louise Falzon, Anthea Sutton,

and David Moher. The problems with systematic reviews: a living systematic review. Journal of Clinical Epidemiology, 156:30–41, 2023.

[54] Johann Laux. Institutionalised distrust and human oversight of artificial intelligence: towards a democratic design of ai

governance under the european union ai act. AI & Society, 39(6):2853–2866, 2024.

[55] Marcus Foth. Hostile interaction design: Ai, governance, and the quest for human oversight. AI & Society, pages 1–7, 2026.

[56] Melanie Sclar, Yejin Choi, Yulia Tsvetkov, and Alane Suhr. Quantifying language models’ sensitivity to spurious features

in prompt design or: How i learned to start worrying about prompt formatting. In International Conference on Learning Representations, volume 2024, pages 25055–25083, 2024.

[57] Mrinank Sharma, Meg Tong, Tomek Korbak, David Duvenaud, Amanda Askell, Sam Bowman, Esin Durmus, Zac Hatfield-

Dodds, Scott Johnston, Shauna Kravec, et al. Towards understanding sycophancy in language models. 2024:110–144, 2024.

[58] Lei Huang, Weijiang Yu, Weitao Ma, Weihong Zhong, Zhangyin Feng, Haotian Wang, Qianglong Chen, Weihua Peng,

Xiaocheng Feng, Bing Qin, et al. A survey on hallucination in large language models: Principles, taxonomy, challenges, and open questions. ACM Transactions on Information Systems, 43(2):1–55, 2025.

[59] Jonathan Hartley, Filip Jolevski, Vitor Melo, and Brendan Moore. The labor market effects of generative artificial intelligence.

Available at SSRN, 2024.

[60] Antti Kauhanen and Petri Rouvinen. Assessing early labour market effects of generative ai: evidence from population data.

Applied Economics Letters, pages 1–4, 2025.

[61] Shakked Noy and Whitney Zhang. Experimental evidence on the productivity effects of generative artificial intelligence.

Science, 381(6654):187–192, 2023.

[62] Erik Brynjolfsson, Danielle Li, and Lindsey Raymond. Generative ai at work. The Quarterly Journal of Economics, 140

(2):889–942, 2025.

[63] Jason Yu and Cheryl Qi. The impact of generative ai on employment and labor productivity. Review of Business, 44(1):

53–67, 2024.

23

Appendix A. Prompt Designs, Task Workflow and Evaluation

This section documents the prompt designs used across the knowledge synthesis review (KSR) workflow. Figures A1–A7 present the screening, extraction, analysis, and synthesis prompts, along with the key revisions that improved consistency and evaluability. Prompts were shaped with human in the loop review, then fixed prior to large scale orchestration.


> **Figure A1. URL access and full-text retrieval challenges in LLM screening. (a) Prompt 1: is a**

> structured screen that classifies AI and labor market documents as INCLUDE or EXCLUDE. (b) Gemini
could not open external links, so it screened only titles and snippets, increasing the risk of keyword-
driven misclassification. (c) NotebookLM likewise could not fetch full text from CSV URLs and was
limited to metadata. In contrast, ChatGPT occasionally opened links, yet its behavior was inconsistent,
suggesting instability. These behaviors motivate supplying full text in-context or prefetching documents
to support reliable screening..

24


> **Figure A2. Modified screening instructions and link retrieval across LLMs. (a) Prompt 2: An updated**

> screening prompt explicitly requiring models to visit the provided links and extract full information (title,
abstract, keywords, and content) before making an INCLUDE/EXCLUDE decision. (b) Gemini still did
not fetch full text despite explicit instructions, instead simulated the process using only metadata from
the CSV file, raising risks of incomplete or inaccurate classification. NotebookLM was given inputs
reformatted to JSON and saved as plain text, yet it could not follow links from the CSV and remained
constrained to metadata. These results show that stricter instructions alone did not overcome LLMs link-
access limits, so reliable screening benefits from supplying full text directly or prefetching documents..

25


> **Figure A3. Challenges in LLM-based screening under iterative prompts. (a) Prompt 3: A structured,**

> step-by-step prompt designed to guide the binary screening of AI and labor market papers into INCLUDE
or EXCLUDE categories, with explicit rules for inclusion, exclusion, and rationale. (b) Observed issues:
field leakage where the predicted label (pred_label) appeared inside the rationale column, misplaced
entries, repetition, and template-like rationales that were identical for most INCLUDE cases while
only EXCLUDE decisions received varied justifications. (c) Prompt 4: To address this, we explicitly
instructed the model to generate rationale tailored to each document ID..

26


> **Figure A4. Final category-specific screening prompts for systematic review. (a) Research papers:**

> Final binary screen for academic articles on AI and labor markets with explicit inclusion, exclusion,
and borderline rules, plus document-specific rationales. (b) News, media, and blogs: A parallel prompt
adapted for non-academic sources, with an additional exclusion rule to filter out documents not orig-
inating from news, media, or blogs. For industry reports, the structure remained identical except for
an added exclusion condition requiring sources to be from industry, small and medium-sized enter-
prises (SMEs), or organizations (excluding research papers, media, and blogs). For policy briefs, an
additional rule was introduced: exclude documents if unrelated to AI (all forms), policy, and labor (all
sectors/outcomes)..

27


> **Figure A5. Extraction prompts accross source types. (a) Research papers: extraction prompt designed**

> to capture bibliographic and structural metadata, including title, authors, journal/source name, publi-
cation year, and counts of tables, figures, and references. (b) News, media and blogs: schema records
outlet or issuing body, publication date, author(s), title, and links to cited research when available. (c)
Industry reports: schema emphasizes publishing organization, authorship, year, title, and report type,
reflecting organizational rather than academic provenance. (d) Policy briefs: schema adapted for policy
sources, extracting issuing body, publication date, authorship, and title. schema records issuing body,
publication date, author(s), and title. Across all categories, the output is a single JSON object per doc-
ument to ensure consistent, machine-readable metadata for downstream analysis..

28


> **Figure A6. Analysis prompts across source types (a) Research papers: extract and synthesize study**

> limitations, future research directions, and a concise methodology summary. (b) News, media, and
blogs: identify current limitations, key findings, and forward-looking implications or calls to action. (c)
Industry reports: capture current constraints (technological, market, regulatory), core market findings,
and projections or strategic recommendations. (d) Policy briefs: surface policy problems or gaps, pro-
posed interventions, and future directions for development and evaluation. All outputs are standardized
as well formed JSON objects to enable consistent comparison across sources in downstream analyses..

29


> **Figure A7. Synthesis prompt across source types. The synthesis prompt directs LLMs to integrate find-**

> ings from research papers (RPs), industry reports (IRs), policy briefs (BPs), and news, media, and blogs
(NMBs) by addressing six dimensions:(1) Overarching impacts: major ways AI affects labor markets,
noting areas of consensus, divergence, contradiction, and framing; (2) Source integration: comparison
of contributions and perspectives across RPs, IR, PBs, and NMBs; (3) Temporal and sectoral anal-
ysis: hort-, medium-, and long-term effects across sectors, occupations, and economic outcomes; (4)
Governance, ethics, and policy: analyzing regulatory challenges, stakeholder roles, and leadership pri-
orities; (5) Challenges, limitations, and uncertainties: evidence gaps, risks, and unresolved debates;
and (6) Future directions: proposed research, industry practices, workforce training, and policy prior-
ities. Outputs are captured as a structured summary to support consistent cross-source comparison..
