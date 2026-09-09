# RQ1 claim briefing (n=166)

- [SCI-000007/abstract_only] (POSITIVE) DIVE is a multi-agent extraction framework that transforms figure-centric scientific content into structured, machine-actionable data, demonstrating that multi-agent workflows can convert heterogeneous literature into AI-ready formats.
  QUOTE: DIVE (Descriptive Interpretation of Visual Expression), a multi-agent extraction framework that transforms figure-centric scientific content into structured, machine-actionable data.
  TOK: [SCI-000007#abstract#FULLTEXT-001] | SEC: ABSTRACT
- [SCI-000056/fulltext] (POSITIVE) TrialScout uses an LLM to classify publications based on the text of abstracts rather than relying on NCT-ID searches or metadata matching, allowing it to use information not present in metadata alone and distinguish true result publications from protocols, secondary analyses, and reviews.
  QUOTE: Where existing automated methods rely on NCT-ID searches or metadata matching between trial registrations and publications, TrialScout uses an LLM to classify publications based on the text of the abstracts. This allows 
  TOK: [SCI-000056#discussion-comparison-to-previous-resear#FULLTEXT-002] | SEC: Discussion > Comparison to previous research
- [SCI-000066/abstract_only] (POSITIVE) A locally executed agentic AI framework for deduplication, screening, and structured data extraction in systematic reviews was developed and validated, reported following PRISMA-trAIce guidelines, indicating design emphasis on transparent reporting of AI use in evidence synthesis.
  QUOTE: We developed and validated a locally executed agentic artificial intelligence (AI) framework for deduplication, screening, and structured data extraction in systematic reviews, reported following Preferred Reporting Item
  TOK: [SCI-000066#abstract#FULLTEXT-009] | SEC: ABSTRACT
- [SCI-000066/abstract_only] (NEUTRAL) The framework consists of a multiagent pipeline of specialized agents for deduplication, title/abstract screening, structured data extraction, and verification, executed entirely locally.
  QUOTE: A multiagent pipeline of specialized agents for deduplication, title/abstract screening, structured data extraction, and verification was executed entirel
  TOK: [SCI-000066#abstract#FULLTEXT-010] | SEC: ABSTRACT
- [SCI-000071/abstract_only] (NEUTRAL) ENTGPT is a GPT-4o-based screening system that implements the novel STARR (screening of title and abstracts, reevaluation, and full-text review) protocol for systematic review screening.
  QUOTE: we investigate an LLM's performance in screening relevant articles for a SLR with the novel screening of title and abstracts, reevaluation, and full‐text review (STARR) protocol.
  TOK: [SCI-000071#abstract#FULLTEXT-012] | SEC: ABSTRACT
- [SCI-000082/fulltext] (POSITIVE) A microservices architecture using Docker containers ensures portability and reproducible performance across diverse computing environments.
  QUOTE: EcoXAI’s architecture is built upon modern software engineering principles, employing a microservices approach facilitated by Docker containers. This containerized architecture ensures high portability and enables consis
  TOK: [SCI-000082#body#FULLTEXT-014] | SEC: body
- [SCI-000082/fulltext] (POSITIVE) Discovery memory stores prior hypotheses and validation outcomes in semantic vector format, enabling RAG-based similarity search to avoid redundant hypothesis generation.
  QUOTE: EcoXAI stores prior hypotheses, validation outcomes, and supporting evidence. The hypotheses are stored in a semantic vector format, enabling the ability to perform Retrieval Augmented Generation (RAG) and similarity sea
  TOK: [SCI-000082#body#FULLTEXT-015] | SEC: body
- [SCI-000082/fulltext] (POSITIVE) Each pipeline step is auditable with its own logging of agent behavior, scripts, images, and reports.
  QUOTE: Each step is auditable with its own logging of agent behavior, scripts, images, and reports.
  TOK: [SCI-000082#body#FULLTEXT-016] | SEC: body
- [SCI-000082/fulltext] (POSITIVE) EcoXAI is organized around discrete, auditable pipelines rather than a single monolithic agent, spanning ingestion, EDA, normalization, predictive analysis, and hypothesis generation.
  QUOTE: EcoXAI is organized around discrete, auditable pipelines rather than a single monolithic agent.
  TOK: [SCI-000082#body#FULLTEXT-017] | SEC: body
- [SCI-000088/fulltext] (NEUTRAL) The majority of the included studies used off-the-shelf LLMs without task-specific fine-tuning and instead emphasized prompt engineering as the primary optimization strategy, meaning general-purpose LLMs achieved strong screening performance with minimal adaptation.
  QUOTE: Importantly, the majority of studies used off-the-shelf LLMs without task-specific fine-tuning, emphasizing prompt engineering as the primary optimization strategy.
  TOK: [SCI-000088#results-methodological-characteristics-o#FULLTEXT-024] | SEC: Results > Methodological characteristics of included studies
- [SCI-000088/fulltext] (NEUTRAL) This systematic review and meta-analysis of 18 studies (2023-2025) evaluates LLM-assisted medical literature screening as a workflow stage in evidence synthesis, following PRISMA-DTA guidance and searching PubMed, Web of Science, Embase, Cochrane Library, and Google Scholar from 1 January 2022 to 17 November 2025.
  QUOTE: This systematic review and meta-analysis was conducted according to PRISMA DTA guidance. PubMed, Web of Science, Embase, the Cochrane Library and Google Scholar were searched from 1 January 2022 to 17 November 2025.
  TOK: [SCI-000088#abstract-methods#FULLTEXT-025] | SEC: Abstract > Methods
- [SCI-000089/fulltext] (NEUTRAL) No task-specific training, fine-tuning, or few-shot examples were used, and the LLM is used only for summarizing articles not for making assessments or proposed action.
  QUOTE: No task-specific training, fine-tuning, or few-shot examples were used. The temperature parameter was not set because it was not supported by the o3 model in our implementation. Each paper was processed once before the t
  TOK: [SCI-000089#methods-procedure#FULLTEXT-035] | SEC: Methods > Procedure
- [SCI-000089/fulltext] (POSITIVE) The LLM-based system automatically extracted and summarized structured data from research paper PDFs using OpenAI's o3 model via API, with a strict JSON schema requiring filename, theme, category, time, place, person, and a 3-5 item Japanese plain-language bullet-point summary.
  QUOTE: The intervention group used an LLM-based system to automatically extract and summarize structured data from research paper PDFs using OpenAI's o3 model via OpenAI Application Programming Interface (API). Responses were c
  TOK: [SCI-000089#methods-intervention-and-control#FULLTEXT-036] | SEC: Methods > Intervention and Control
- [SCI-000090/fulltext] (supportive) Schema-constrained extraction uses fixed prompts and structured enumerations rather than free generation, with conservative missingness handling (returning 'NR') to minimize fabrication and ensure deterministic outputs.
  QUOTE: schema enforcement (constrained enumerations rather than free generation) and conservative missingness handling (returning 'NR') were designed to minimize fabrication and performed well in audited fields.
  TOK: [SCI-000090#discussion-limitations#FULLTEXT-042] | SEC: Discussion (Limitations)
- [SCI-000090/fulltext] (supportive) The pipeline couples screening with structured abstract-level extraction and high-level synthesis using fixed prompts and schemas, operationalizing a local-first workflow that does not depend on proprietary cloud models.
  QUOTE: the present work operationalizes a local-first workflow that couples screening with structured abstract-level extraction and high-level synthesis using fixed prompts and schemas.
  TOK: [SCI-000090#discussion#FULLTEXT-043] | SEC: Discussion
- [SCI-000090/fulltext] (supportive) The pipeline is fully local and zero-shot, running on consumer-grade hardware (Apple M1 Max) with the gpt-oss-20b model via Ollama, requiring no cloud APIs or proprietary models — enabling full reproducibility.
  QUOTE: This study benchmarked a fully local, zero-shot, schema-constrained LLM pipeline for title/abstract screening and abstract-based extraction and synthesis under reproducibility and privacy constraints on consumer-grade ha
  TOK: [SCI-000090#discussion#FULLTEXT-044] | SEC: Discussion
- [SCI-000096/fulltext] (supportive) LatteReview integrates Retrieval-Augmented Generation (RAG) workflows, allowing reviewers to dynamically fetch relevant information and incorporate retrieved data into the review process for grounding.
  QUOTE: LatteReview integrates seamlessly with retrieval-augmented generation workflows, enabling reviewers to: Leverage External Knowledge: Fetch relevant information dynamically to enhance review accuracy. Dynamic Context Addi
  TOK: [SCI-000096#section-3-6-retrieval-augmented-generati#FULLTEXT-051] | SEC: Section 3.6 (Retrieval-Augmented Generation Integration)
- [SCI-000096/fulltext] (supportive) LatteReview's ReviewWorkflow class orchestrates multi-stage review processes with sequential rounds, parallel reviews, conditional filtering, and output aggregation — providing structured provenance for each decision.
  QUOTE: The ReviewWorkflow class allows users to define multi-stage review processes with: Sequential Rounds: Execute reviews in predefined stages, where the output of one stage can feed into the next. Parallel Reviews: Assign m
  TOK: [SCI-000096#section-3-4-multi-reviewer-workflows#FULLTEXT-052] | SEC: Section 3.4 (Multi-Reviewer Workflows)
- [SCI-000096/fulltext] (supportive) Reasoning transparency is built into the TitleAbstractReviewer agent, which provides either brief or chain-of-thought (CoT) reasoning for its inclusion/exclusion decisions — reasoning cannot be None.
  QUOTE: The agent provides reasoning for its decisions, which could be "brief" or "cot", where the former means the agent should return a brief reasoning in 1 - 2 sentences, and the latter means a more detailed step-by-step reas
  TOK: [SCI-000096#lattereview-title-and-abstract-reviews-r#FULLTEXT-053] | SEC: LatteReview > Title and Abstract Reviews > Reasoning Transparency
- [SCI-000096/fulltext] (supportive) The framework is open-source and available on GitHub and PyPI, enabling reproducible installations and community contributions.
  QUOTE: LatteReview is designed to be straightforward to install ... The package is available on PyPI and can be installed using the following command: pip install lattereview ... For users requiring additional functionalities, 
  TOK: [SCI-000096#section-8-1-installation#FULLTEXT-054] | SEC: Section 8.1 (Installation)
- [SCI-000099/fulltext] (NEUTRAL) Every module in M-Reason logs token usage, runtime statistics, and inference metadata, which the authors describe as vital for monitoring computational costs with commercial APIs and for objectively comparing system performance against manual curation.
  QUOTE: Every module in M-Reason logs token usage, runtime statistics, and inference metadata. This is vital for monitoring computational costs, especially with commercial APIs, and allows for objective comparison of system perf
  TOK: [SCI-000099#3-4-design-principles-and-rationale#FULLTEXT-061] | SEC: 3.4 Design Principles and Rationale
- [SCI-000099/fulltext] (NEUTRAL) M-Reason organizes evidence analysis into three agent roles - Orchestrator, BioExpert, and Evaluator - where the Orchestrator sequences the workflow and returns status without touching an LLM, giving a clear separation of responsibilities that the authors state facilitates reproducibility.
  QUOTE: The Orchestrator does not interact with any large language model; instead, its role is to sequence the workflow and return workflow status. All substantive analysis and evaluation are handled by downstream agents.
  TOK: [SCI-000099#3-1-evidence-analysis#FULLTEXT-062] | SEC: 3.1 Evidence analysis
- [SCI-000099/fulltext] (NEUTRAL) M-Reason provides complete traceability and auditability from source evidence to final conclusions, exposing an interactive interface with seven agent terminals plus downloadable logs, prompts, and intermediate outputs from each iteration to support transparency and reproducibility.
  QUOTE: In addition, all logs, prompts, and intermediate outputs from each iteration are made available, supporting transparency and reproducibility. Execution metrics such as processing time, computational cost, token usage, th
  TOK: [SCI-000099#4-m-reason-interface#FULLTEXT-063] | SEC: 4 M-Reason Interface
- [SCI-000099/fulltext] (NEGATIVE) The authors position M-Reason as improving predictability and reproducibility but note it operates more as a deterministic workflow than a fully autonomous agent, which restricts adaptive decision-making.
  QUOTE: The system operates more as a deterministic workflow than a fully autonomous agent; while this improves predictability and reproducibility, it restricts adaptive decision-making capabilities.
  TOK: [SCI-000099#limitations#FULLTEXT-064] | SEC: Limitations
- [SCI-000100/fulltext] (POSITIVE) HySemRAG implements an eight-stage ETL pipeline integrated with a multi-agent RAG framework rather than a single monolithic generation system.
  QUOTE: HySemRAG implements an eight-stage ETL pipeline integrated with a multi-agent RAG framework.
  TOK: [SCI-000100#body#FULLTEXT-073] | SEC: body
- [SCI-000100/fulltext] (POSITIVE) The framework creates a chain of custody for every piece of information, combining semantic search (Qdrant), keyword search, and structured graph traversals (Neo4j) with Reciprocal Rank Fusion.
  QUOTE: The core of the framework creates a chain of custody for every piece of information. This begins with a hybrid retrieval engine that goes beyond simple vector search. It combines results from three distinct sources: sema
  TOK: [SCI-000100#body#FULLTEXT-074] | SEC: body
- [SCI-000100/fulltext] (POSITIVE) The system creates dual data products, a Neo4j knowledge graph and Qdrant vector collections, serving as structural infrastructure for verifiable information synthesis.
  QUOTE: The system creates dual data products - a Neo4j knowledge graph enabling complex relationship queries and Qdrant vector collections supporting semantic search - serving as foundational infrastructure for verifiable infor
  TOK: [SCI-000100#abstract#FULLTEXT-075] | SEC: abstract
- [SCI-000102/fulltext] (POSITIVE) A three-layer hierarchical agentic network (worker, manager, director) preserves traceability and transparency, with 13 worker-layer APIs accessing domain-specific resources including a medical knowledge graph, literature repositories, and clinical records.
  QUOTE: To preserve traceability and transparency, we implement a three-layer hierarchical agentic network: At the worker layer, DeepER-Med configures 13 APIs to access domain-specific resources, including a medical knowledge gr
  TOK: [SCI-000102#methods-agentic-collaboration-module#FULLTEXT-083] | SEC: Methods > Agentic collaboration module
- [SCI-000102/fulltext] (POSITIVE) All cited sources are listed in the reference section in order of appearance, enabling efficient review, verification, and downstream analysis by researchers.
  QUOTE: All cited sources are listed in the reference section in order of appearance, enabling efficient review, verification, and downstream analysis by researchers.
  TOK: [SCI-000102#methods-evidence-synthesis-module#FULLTEXT-084] | SEC: Methods > Evidence Synthesis module
- [SCI-000102/fulltext] (POSITIVE) DeepER-Med structures evidence-based medical research as an explicit and inspectable workflow comprising three stages—research intent investigation, evidence retrieval and interpretation, and structured knowledge synthesis—implemented through research planning, agentic collaboration, and evidence synthesis modules.
  QUOTE: DeepER-Med, an agentic AI system, structures evidence-based medical research as an explicit and inspectable workflow comprising three stages: research intent investigation, evidence retrieval and interpretation, and stru
  TOK: [SCI-000102#methods-framework-of-deeper-med#FULLTEXT-085] | SEC: Methods > Framework of DeepER-Med
- [SCI-000106/fulltext] (POSITIVE) The framework adapts recent advances in declarative prompt optimisation, developed for general-purpose LLM applications, and demonstrates their applicability to the domain of SLR automation, described as a novel application of such approaches to SLR pipelines.
  QUOTE: this work adapts recent advances in declarative prompt optimisation, developed for general-purpose LLM applications, and demonstrates their applicability to the domain of SLR automation ... This is a novel application of
  TOK: [SCI-000106#abstract#FULLTEXT-093] | SEC: ABSTRACT
- [SCI-000106/fulltext] (POSITIVE) The framework replaces manual, ad-hoc 'prompt alchemy' with a rigorous, four-step programmatic process: formally defining the research goal, codifying the quality standard with data, automatically compiling an optimal prompt, and packaging the result as a verifiable digital artefact.
  QUOTE: It replaces manual, ad-hoc "prompt alchemy" with a rigorous, four-step programmatic process: (1) formally defining the research goal, (2) codifying the quality standard with data, (3) automatically compiling an optimal p
  TOK: [SCI-000106#introduction#FULLTEXT-094] | SEC: INTRODUCTION
- [SCI-000106/fulltext] (NEGATIVE) The paper argues that current LLM-assisted SLR approaches rely on brittle, manually crafted prompts that compromise reliability and reproducibility, and that this prompt fragility undermines scientific confidence in LLM-assisted evidence synthesis.
  QUOTE: current approaches often rely on brittle, manually crafted prompts that compromise reliability and reproducibility. This fragility undermines scientific confidence in LLM-assisted evidence synthesis.
  TOK: [SCI-000106#abstract#FULLTEXT-095] | SEC: ABSTRACT
- [SCI-000106/fulltext] (NEGATIVE) The paper identifies that model updates can invalidate previously crafted prompts and break reliable pipelines, while cross-model behaviour and accuracy diverges significantly using identical prompts, eroding trust and widening the reproducibility gap in SLRs.
  QUOTE: Model updates can invalidate previously crafted prompts and break reliable pipelines, while cross-model behaviour and accuracy diverges significantly using identical prompts [4]. These LLM sensitivities and fragilities e
  TOK: [SCI-000106#introduction#FULLTEXT-096] | SEC: INTRODUCTION
- [SCI-000106/fulltext] (NEGATIVE) The paper notes that LLM performance is highly sensitive to the phrasing of input prompts, making LLM-assisted workflows unreliable, difficult to reproduce, and raising concerns about their scientific validity.
  QUOTE: LLMs show significant promise for automating SLR tasks, but their performance is highly sensitive to the phrasing of input prompts. This "prompt fragility" makes LLM-assisted workflows unreliable, difficult to reproduce,
  TOK: [SCI-000106#introduction#FULLTEXT-097] | SEC: INTRODUCTION
- [SCI-000106/fulltext] (POSITIVE) The proposed framework offers a path toward establishing new standards for transparency and auditability in AI-assisted reviews, allowing others to verify and replicate automated steps with precision.
  QUOTE: The proposed framework offers a path toward establishing new standards for transparency and auditability in AI-assisted reviews, allowing others to verify and replicate automated steps with precision.
  TOK: [SCI-000106#introduction#FULLTEXT-098] | SEC: INTRODUCTION
- [SCI-000106/fulltext] (POSITIVE) The work proposes a structured, domain-specific framework that embeds task declarations, test suites and automated prompt tuning into a reproducible SLR workflow, translated into a concrete blueprint with working code examples enabling researchers to construct verifiable LLM pipelines aligned with transparency and rigour principles.
  QUOTE: This research proposes a structured, domain-specific framework that embeds task declarations, test suites, and automated prompt tuning into a reproducible SLR workflow. These emerging methods are translated into a concre
  TOK: [SCI-000106#abstract#FULLTEXT-099] | SEC: ABSTRACT
- [SCI-000107/fulltext] (NEUTRAL) ADVISE embeds a fine-tuned BERT AI agent in the human title-and-abstract screening workflow with a screen-update-predict-sample active learning loop, where a priority score PS(p) = softmax(Pred(p))[1] ranks unscreened papers by predicted relevance probability and the human team screens prioritized papers in batches.
  QUOTE: Priority score is the probability that a paper is a relevant paper predicted by the AI agent, which is calculated by 𝑃𝑆(𝑝) = 𝑠𝑜𝑓𝑡𝑚𝑎𝑥(𝑃𝑟𝑒𝑑(𝑝))[1], where 𝑃𝑟𝑒𝑑(𝑝) is the predic- tion output from the classification model for
  TOK: [SCI-000107#methodology-active-learning-query-strate#FULLTEXT-102] | SEC: Methodology > Active Learning Query Strategy
- [SCI-000107/fulltext] (NEUTRAL) ADVISE preserves human verification of all relevant papers by design: because 'for evidence synthesis, all relevant papers need to be verified by a human agent', the highest-priority papers are sampled first, and the workflow stops screening when ranking similarity or the real-time inclusion rate crosses a threshold.
  QUOTE: This query strategy is adapted from the uncertainty sampling strategies [36]. For evidence synthesis, all relevant papers need to be verified by a human agent, so the papers most likely to be relevant are first sampled.
  TOK: [SCI-000107#methodology-active-learning-query-strate#FULLTEXT-103] | SEC: Methodology > Active Learning Query Strategy
- [SCI-000107/fulltext] (NEUTRAL) Reproducibility in ADVISE is handled by repeating every experiment five times and averaging predicted uncertainties and priority scores across the five runs to improve repeatability of the results.
  QUOTE: When the predicted uncertainties and PSs are needed to sample new papers with the LC and HP strategies, we use the mean values of the predictions from the five runs to improve the repeatability of the results.
  TOK: [SCI-000107#methodology-implementation-details#FULLTEXT-104] | SEC: Methodology > Implementation Details
- [SCI-000107/fulltext] (NEGATIVE) The practical interaction cost of the human-AI team is acknowledged as a concrete barrier: time needed to exchange information, label updates, dataset merging, and time lags between human labeling and model updates can mean one team operates with incomplete data.
  QUOTE: Finally, time lags between humans labeling documents, the AI agent receiving the documents and updating the model, and then the AI agent sending back newly ranked documents for human screening means that one team may be 
  TOK: [SCI-000107#discussion-the-cost-of-communication#FULLTEXT-105] | SEC: Discussion > The Cost of Communication
- [SCI-000108/fulltext] (NEUTRAL) This paper presents a template for future evaluations of LLMs in the context of data extraction for systematic review automation, and the authors advise caution when integrating models such as GPT-4 into tools, calling for further research on stability and reliability.
  QUOTE: This paper presents a template for future evaluations of LLMs in the context of data extraction for systematic review automation. Our results show that there might be value in using LLMs, for example as second or third r
  TOK: [SCI-000108#abstract#FULLTEXT-114] | SEC: ABSTRACT
- [SCI-000108/fulltext] (POSITIVE) To support repeatability, the study fixed conservative generation parameters for GPT-4 - temperature=0, frequency_penalty=0, presence_penalty=0, top_p=0.95 - aiming for maximum repeatability across repeated requests.
  QUOTE: The parameters selected for GPT-4 were designed to be as conservative as possible, aiming for maximum repeatability across repeated requests. They were: temperature=0, frequency_penalty=0, presence_penalty=0, top_p=0.95.
  TOK: [SCI-000108#methods#FULLTEXT-115] | SEC: METHODS
- [SCI-000109/fulltext] (POSITIVE) Result extraction uses a specialized three-step pipeline: identifying relevant content, extracting and logically processing numerical values, and converting values into a standardized tabular format.
  QUOTE: This enhanced pipeline consists of three crucial steps: (1) identifying the relevant content within the study (Prompt in Supplementary Fig. 11), (2) extracting and logically processing this content to obtain numerical va
  TOK: [SCI-000109#body#FULLTEXT-125] | SEC: body
- [SCI-000109/fulltext] (POSITIVE) TrialMind follows PRISMA for transparent screening, creating eligibility criteria based on the input PICO as the basis for study selection.
  QUOTE: TrialMind follows PRISMA to take a transparent approach to study screening. It creates a set of eligibility criteria based on the input PICOas the basis for study selection
  TOK: [SCI-000109#body#FULLTEXT-126] | SEC: body
- [SCI-000109/fulltext] (POSITIVE) TrialMind incorporates RAG to enrich context with knowledge sourced from PubMed and employs chain-of-thought processing to generate more exhaustive literature-search terms.
  QUOTE: TrialMind incorporates RAG to enrich the context with knowledge sourced from PubMed and employs CoT processing to facilitate a more exhaustive generation of relevant terms.
  TOK: [SCI-000109#body#FULLTEXT-127] | SEC: body
- [SCI-000110/fulltext] (POSITIVE) A continuously updated 'living' database structure lets the review reflect near real-time shifts in the evidence base, addressing the lag of conventional reviews.
  QUOTE: This system's living database structure updates continuously, ensuring that reviews reflect near real-time shifts in the evidence base.
  TOK: [SCI-000110#4-3-dynamic-integration-and-timely-evide#FULLTEXT-136] | SEC: 4.3 Dynamic Integration and Timely Evidence
- [SCI-000110/fulltext] (NEUTRAL) The framework follows a standard four-phase systematic-review pipeline — Define and Search, Screen and Assess, Extract and Synthesize, Interpret and Update — with each phase automated (PICOS guidance, study-design classification, BERTopic clustering, and living-database updates).
  QUOTE: 1. Define and Search: AI-guided query formulation based on PICOS, supported by semantic matching and graph-based retrieval. 2. Screen and Assess: Automated identification of PICOS-compliant articles and hierarchical clas
  TOK: [SCI-000110#1-2-overall-workflow-in-systematic-revie#FULLTEXT-137] | SEC: 1.2 Overall Workflow in Systematic Reviews
- [SCI-000110/fulltext] (NEUTRAL) The system orchestrates data flow across multiple backends: LangGraph routes multi-step queries to the appropriate data store, and the LiteralAI API logs all user interactions to promote transparency and accountability — a concrete audit-trail mechanism.
  QUOTE: LangGraph: Directs complex, multi-step queries to the appropriate data store (graph, relational, or vector) while minimizing hallucinations by verifying document relevance. LiteralAI API: Logs all user interactions, prom
  TOK: [SCI-000110#2-5-modular-integration-and-front-end-in#FULLTEXT-138] | SEC: 2.5 Modular Integration and Front-End Interface
- [SCI-000111/fulltext] (POSITIVE) Bio-SIEVE uses QLoRA fine-tuning on the LLaMA-7b and Guanaco-7B models trained on the Instruct Cochrane train split.
  QUOTE: We used QLoRA fine-tuning to train LLaMA7b and Guanaco7B on the Instruct Cochrane Train split.
  TOK: [SCI-000111#body#FULLTEXT-149] | SEC: body
- [SCI-000111/fulltext] (POSITIVE) The evaluation benchmark is safety-first, rewarding cautious models with high include recall and using professional systematic reviewers for annotation.
  QUOTE: This results in a benchmark that rewards cautious models with high include recall.
  TOK: [SCI-000111#body#FULLTEXT-150] | SEC: body
- [SCI-000111/fulltext] (NEGATIVE) The paper highlights reproducibility concerns arising from the opacity of closed-source models in systematic review automation.
  QUOTE: is in addition to reproducibility concerns arising from the opacity of closed-source models
  TOK: [SCI-000111#body#FULLTEXT-151] | SEC: body
- [SCI-000114/fulltext] (NEUTRAL) The corpus was augmented with a scraper to extract recent papers (2021–2023), yielding an augmented dataset of 66,692 papers searchable via three embedding models.
  QUOTE: VITAL- ITY 2 used this scraper to extract more recent papers between 2021- 2023, resulting in an augmented dataset of 66,692 papers.
  TOK: [SCI-000114#4-1-dataset-of-academic-articles#FULLTEXT-159] | SEC: 4.1 Dataset of Academic Articles
- [SCI-000114/fulltext] (NEUTRAL) The tool combines RAG with prompt chaining, implemented with the LangChain open-source library, breaking complex literature-review tasks into a series of smaller LLM steps.
  QUOTE: Prompt Chaining. Prompt chaining breaks down complex tasks to a series of smaller steps and provides specific prompts that are known to be effective for each of these steps [45]. VITALITY 2 bor- rows this idea and implem
  TOK: [SCI-000114#4-vitality-2#FULLTEXT-160] | SEC: 4 VITALITY 2
- [SCI-000114/fulltext] (NEUTRAL) vitaLITy 2 is released as open-source software alongside its paper corpus to support reproducible, re-usable literature review methods.
  QUOTE: We provide the system as an open-sourced code contribu- tion at https://vitality-vis.github.io, alongside the paper corpus, and hope to stimulate future work in optimizing literature review methods.
  TOK: [SCI-000114#7-conclusion#FULLTEXT-161] | SEC: 7 Conclusion
- [SCI-000114/fulltext] (NEUTRAL) vitaLITy 2 manages LLM context and conversation state through prompt chaining: a first API call produces a 'condensed conversation history' summary, which a second call concatenates with the user query and retrieved documents.
  QUOTE: we adopt a two-step approach in VITALITY 2: first, a summary of recent con- versations is generated by calling the LLM API once to obtain a “condensed conversation history.” Then, in the second API call, the user's query
  TOK: [SCI-000114#3-system-architecture#FULLTEXT-162] | SEC: 3 (System Architecture)
- [SCI-000115/fulltext] (POSITIVE) Human oversight in KSR is embedded at every review stage (not only final synthesis) to prevent error propagation, since screening and extraction inaccuracies can systematically distort downstream analysis and synthesis.
  QUOTE: Rather than reserving human evaluation for the final synthesis stage, oversight was embedded throughout to prevent error propagation, as inaccuracies in early stages such as screening and extraction can systematically di
  TOK: [SCI-000115#2-methods-2-2-1-human-in-the-loop-benchm#FULLTEXT-169] | SEC: 2 Methods > 2.2.1 Human-in-the-Loop Benchmark Design
- [SCI-000115/fulltext] (POSITIVE) KSR argues that oversight in LLM-assisted synthesis must be operationalized as auditable workflows with transparent prompt and model documentation, explicit evaluation criteria, and mechanisms for preserving disagreement across sources.
  QUOTE: oversight must be operationalized through auditable workflows, transparent prompt and model documentation, explicit evaluation criteria, and mechanisms for preserving disagreement across sources.
  TOK: [SCI-000115#4-discussion#FULLTEXT-170] | SEC: 4 Discussion
- [SCI-000115/fulltext] (NEUTRAL) KSR's Phase III is a model-agnostic orchestration layer that routes each task to the model with the strongest demonstrated performance for that task over shared retrieval infrastructure while maintaining expert validation throughout.
  QUOTE: Phase III operationalizes the benchmark results as a model-agnostic orchestration layer that routes each task to the system with the strongest demonstrated performance for that task, over shared retrieval infrastructure,
  TOK: [SCI-000115#1-introduction#FULLTEXT-171] | SEC: 1 Introduction
- [SCI-000115/fulltext] (NEUTRAL) The Knowledge Synthesis Review (KSR) framework decomposes evidence synthesis into four cognitive tasks (screening, extraction, analysis, synthesis), benchmarks LLM-based systems on each against expert reference standards, and routes each task to the best-performing system under continuous expert validation.
  QUOTE: We introduce the Knowledge Synthesis Review (KSR), a human-in-the-loop framework that decomposes evidence synthesis into screening, extraction, analysis, and synthesis, benchmarks LLM-based systems on each task against e
  TOK: [SCI-000115#abstract#FULLTEXT-172] | SEC: Abstract
- [SCI-000115/fulltext] (NEUTRAL) To limit evaluator bias, all LLM outputs in the KSR benchmark were anonymized and randomized before evaluation so that evaluators could not identify which system produced a given output.
  QUOTE: To limit bias toward any particular system, all model outputs were anonymized and randomized prior to evaluation, so that evaluators could not identify which system had produced a given output.
  TOK: [SCI-000115#2-methods-2-2-1-human-in-the-loop-benchm#FULLTEXT-173] | SEC: 2 Methods > 2.2.1 Human-in-the-Loop Benchmark Design
- [SCI-000117/fulltext] (POSITIVE) DeepWeaver generates final answers block-by-block from the refined TBC, a strategy that decomposes context pressure into claim-level generation and improves citation grounding by generating each section from a smaller, more relevant evidence subset.
  QUOTE: This block-wise generation strategy has two advantages: (1) it decomposes context pressure into claim-level generation, and (2) it improves citation grounding because each section is generated from a smaller and more rel
  TOK: [SCI-000117#3-method-3-3-evidence-grounded-answer-ge#FULLTEXT-183] | SEC: 3 Method > 3.3 Evidence-Grounded Answer Generation
- [SCI-000117/fulltext] (NEUTRAL) DeepWeaver maintains thought block chains (TBCs), an explicit data structure that decomposes open-ended answers into sequences of thought blocks bridging retrieved evidence and final generation.
  QUOTE: We define the Thought Block Chain (TBC) as an explicit data structure that bridges retrieved evidence and final answer generation. The TBC serves as the core information structure maintained by DeepWeaver, decomposing th
  TOK: [SCI-000117#3-method-3-1-thought-block-chain#FULLTEXT-184] | SEC: 3 Method > 3.1 Thought Block Chain
- [SCI-000117/fulltext] (NEUTRAL) The core evidence-weaving mechanism of DeepWeaver iterates over three ordered stages for refining its main TBC: Draft, Subordinate, and Commit.
  QUOTE: The core mechanism of DeepWeaver (Figure 2(B)) lies in the maintenance of a main TBC TM. It updates TM through multi-stage refinement. Overall, DeepWeaver consists of three ordered weaving stages: Draft, Subordinate, and
  TOK: [SCI-000117#3-method-3-2-evidence-weaving#FULLTEXT-185] | SEC: 3 Method > 3.2 Evidence Weaving
- [SCI-000117/fulltext] (NEUTRAL) To control context burden during TBC construction, the draft and subordinate stages randomly sample subsets of evidence fragments from the full evidence pool and the residual evidence set at each refinement turn.
  QUOTE: Furthermore, to reduce the context burden during TBC construction, the draft and subordinate stages randomly sample r (r < |E|) evidence fragments from E and Rt (the residual evidence set at refinement turn t), respectiv
  TOK: [SCI-000117#3-method-3-2-evidence-weaving#FULLTEXT-186] | SEC: 3 Method > 3.2 Evidence Weaving
- [SCI-000117/fulltext] (POSITIVE) Two refinement rounds over the initial TBC are sufficient to produce large answer-quality gains, and the paper sets n = 2 as default for a cost-performance trade-off.
  QUOTE: With only two rounds of refinement over the initial TBC, DeepWeaver brings large gains. This demonstrates the efficiency of the evidence weaving mechanism.
  TOK: [SCI-000117#4-experiments-4-6-cross-model-generaliza#FULLTEXT-187] | SEC: 4 Experiments > 4.6 Cross-Model Generalizability
- [SCI-000118/fulltext] (POSITIVE) Every API call is logged locally in structured JSON with model identity, token counts, latency, retry count, and initiating phase, enabling granular cost profiling.
  QUOTE: Every API call is logged locally in structured JSON: model identity, input/output token counts, call latency, retry count, and the initiating phase and agent. Cost is computed post hoc by multiplying token counts by per-
  TOK: [SCI-000118#body#FULLTEXT-196] | SEC: body
- [SCI-000118/fulltext] (POSITIVE) LUMEN automates six SR/MA phases end-to-end with automated RoB-2/ROBINS-I and GRADE assessment in addition to statistical synthesis and manuscript drafting.
  QUOTE: LUMEN automates six phases end-to-end—search strategy, title–abstract screening, full-text review, structured extraction, statistical synthesis, and manuscript drafting—with automated RoB-2/ROBINS-I and GRADE assessment.
  TOK: [SCI-000118#body#FULLTEXT-197] | SEC: body
- [SCI-000118/fulltext] (POSITIVE) LUMEN uses 11 specialized agents with deliberate model routing, assigning cheaper models to high-volume phases, Claude Sonnet to high-judgment phases, and GPT-5.4 to verification.
  QUOTE: The pipeline uses 11 specialized agents with deliberate model routing: high-volume phases use cheaper models (Gemini 3.1 Pro, GPT-4.1 Mini), while high-judgment phases use Claude Sonnet 4.6, and verification uses GPT-5.4
  TOK: [SCI-000118#abstract#FULLTEXT-198] | SEC: abstract
- [SCI-000118/fulltext] (POSITIVE) The full pipeline, including all code, cost logs, and prompts, is publicly released on GitHub.
  QUOTE: All code, cost logs, and prompts are publicly available at https://github.com/YHHuan/LUMEN.
  TOK: [SCI-000118#body#FULLTEXT-199] | SEC: body
- [SCI-000119/abstract_only] (POSITIVE) LLMs have the potential to assist researchers in generating Boolean queries for systematic reviews, with the paper reproducing and extending prior work on LLM-based query generation.
  QUOTE: The advent of generative AI and large language models (LLMs) promises to revolutionize this process by assisting researchers in several tedious tasks, one of them being the generation of effective Boolean queries that wi
  TOK: [SCI-000119#abstract#FULLTEXT-206] | SEC: ABSTRACT
- [SCI-000120/fulltext] (NEUTRAL) The evaluation corpus is a 586-document sample from the GAMI database (food sector focus group) of 1,682 peer-reviewed articles, where each original article was labeled by two human experts with conflicts resolved by a senior expert, providing the human reference standard.
  QUOTE: The curation of this dataset was rigorous wherein each peer-reviewed article was assigned to two human-labelers with climate change adaptation expertise and any con- flict between any of the features labelled by them was
  TOK: [SCI-000120#3-1-dataset#FULLTEXT-208] | SEC: 3.1 Dataset
- [SCI-000120/fulltext] (NEUTRAL) The study embeds GPT-4o in an evidence-extraction workflow that first converts PDF files to markdown with LlamaParse, includes an intermediate verification step (the model must first identify the adaptation response before listing stakeholders), and asks the model to supply excerpts justifying each extraction to analyze divergence from human annotations.
  QUOTE: We prompted GPT-4o1 for this task by first con- verting the PDF files to markdown format using LlamaParse2. To guide the model effectively, we included an intermediate verification step in the prompts. Specifically, the 
  TOK: [SCI-000120#3-3-experiments#FULLTEXT-209] | SEC: 3.3 Experiments
- [SCI-000122/fulltext] (NEUTRAL) All intermediate outputs — rule sets, function plans, parsed field values, and trial-level filtering outcomes — are logged, providing a complete audit trail from the original clinical query to the final selected studies.
  QUOTE: All intermediate outputs, including rule sets, function plans, parsed field values, and trial-level filtering outcomes, are logged to provide a complete audit trail from the original query to the final selected studies.
  TOK: [SCI-000122#2-1-trial-selection-and-structuring#FULLTEXT-218] | SEC: 2.1 Trial Selection and Structuring
- [SCI-000122/fulltext] (NEUTRAL) All steps of eligibility-aware weighting — penalty evaluation, score transformation, and weighted estimation — are executed deterministically and fully logged in the framework.
  QUOTE: All steps in this stage, including penalty evaluation, score transformation, and weighted estimation, are executed deterministically and fully logged.
  TOK: [SCI-000122#2-2-eligibility-aware-meta-analysis#FULLTEXT-219] | SEC: 2.2 Eligibility-Aware Meta-Analysis
- [SCI-000122/fulltext] (NEUTRAL) EligMeta separates LLM-based reasoning/orchestration from deterministic, version-controlled execution of numerically critical operations (trial selection, eligibility-weight computation, statistical estimation) to guarantee reproducibility and transparency.
  QUOTE: To ensure reproducibility and transparency, EligMeta employs a hybrid architecture: LLMs provide high-level reasoning and orchestration for natural language understanding and workflow planning, while numerically critical
  TOK: [SCI-000122#1-introduction#FULLTEXT-220] | SEC: 1 Introduction
- [SCI-000122/fulltext] (NEUTRAL) In the meta-analysis stage, LLM usage is restricted to penalty-rule specification and schema-constrained parsing, while penalty evaluation, score transformation, and statistical estimation are executed deterministically and auditable.
  QUOTE: LLM usage is restricted to penalty rule specification and schema-constrained parsing, while penalty evaluation, score transformation, and statistical estimation are deterministic and auditable.
  TOK: [SCI-000122#2-2-eligibility-aware-meta-analysis-figu#FULLTEXT-221] | SEC: 2.2 Eligibility-Aware Meta-Analysis (Figure 3 caption)
- [SCI-000122/fulltext] (NEUTRAL) The generated rule set is surfaced for expert review before execution, allowing conditions to be inspected and refined so the pipeline can be audited and corrected prior to running selection.
  QUOTE: The rule set is surfaced for expert review prior to execution, allowing conditions to be inspected and refined to ensure alignment with clinical intent.
  TOK: [SCI-000122#2-1-trial-selection-and-structuring#FULLTEXT-222] | SEC: 2.1 Trial Selection and Structuring
- [SCI-000124/fulltext] (POSITIVE) Four state-of-the-art LLMs as of September 2025 (GPT-4o, GPT-4o-mini, GPT-o3, GPT-5) were evaluated on 14 binary methodological criteria across 180 full-text articles.
  QUOTE: In this study, we evaluated four state-of-the-art language models’ (as of September 2025) ability to predict the binary labels across the 14 categories
  TOK: [SCI-000124#body#FULLTEXT-232] | SEC: body
- [SCI-000124/fulltext] (POSITIVE) Two complementary prompting strategies were used: BASIC prompts requesting direct binary responses, and DETAILED prompts including explanations and illustrative examples of each criterion.
  QUOTE: We implemented two complementary prompting strategies: BASIC prompts, which requested direct binary (Yes/No) responses without explanations, and DETAILED prompts, which included explanations and illustrative examples cla
  TOK: [SCI-000124#body#FULLTEXT-233] | SEC: body
- [SCI-000126/fulltext] (POSITIVE) BIORESEARCHER is a scenario-guided multi-agent system in which a master orchestrator selects a versioned scenario playbook, decomposes the query, and delegates to specialized, state-isolated subagents that publish provenanced artifacts, targeting auditable workflows for heterogeneous biomedical sources.
  QUOTE: A master orchestrator selects a versioned scenario playbook, decomposes the query, and delegates to specialized, state-isolated subagents that publish provenanced artifacts.
  TOK: [SCI-000126#system-architecture#FULLTEXT-254] | SEC: SYSTEM ARCHITECTURE
- [SCI-000126/fulltext] (POSITIVE) Outputs of BIORESEARCHER are auditable dossiers with normalized entities, heterogeneous evidence, ranked hypotheses, mechanistic links and retrievable provenance such as PMIDs, NCT IDs and patent numbers, preserving identifiers, uncertainty and retrievable provenance.
  QUOTE: Outputs are auditable dossiers with normalized entities, heterogeneous evidence, ranked hypotheses, mechanistic links, and retrievable provenance (e.g., PMIDs, NCT IDs, and patent numbers).
  TOK: [SCI-000126#system-architecture#FULLTEXT-255] | SEC: SYSTEM ARCHITECTURE
- [SCI-000126/fulltext] (NEGATIVE) The paper states that general-purpose foundation models and off-the-shelf tool-augmented or multi-agent systems fall short on the auditable, scenario-specific workflows that heterogeneous biomedical sources demand, motivating the architecture.
  QUOTE: General-purpose foundation models and off-the-shelf tool-augmented or multi-agent systems are not built for this: they tend to produce single-shot answers or run open-endedly, and fall short on the auditable, scenario-sp
  TOK: [SCI-000126#introduction#FULLTEXT-256] | SEC: INTRODUCTION
- [SCI-000126/fulltext] (POSITIVE) The system applies claim-level multi-model reconciliation before editorial assembly, using claim extraction, cross-model grouping, multi-round argumentation and quantitative consensus detection for auditable long-form biomedical report synthesis.
  QUOTE: reconciles outputs via structured claim-level debate-claim extraction, cross-model grouping, multi-round argumentation, and quantitative consensus detection-for auditable long-form biomedical report synthesis.
  TOK: [SCI-000126#introduction#FULLTEXT-257] | SEC: INTRODUCTION
- [SCI-000127/fulltext] (NEUTRAL) MedMeta's synthesis workflows are orchestrated with LangGraph, open-weights inference is optimized with vLLM, and closed-weights models are accessed via APIs — a concrete agentic pipeline architecture.
  QUOTE: Implementation. Workflow orchestration was implemented with LangGraph LangChain (2024), and inference of open-weights models was optimized using vLLM Kwon et al. (2023) (Appendix I). Closed-weights models were accessed v
  TOK: [SCI-000127#3-2-llm-workflows-for-conclusion-generat#FULLTEXT-263] | SEC: 3.2 LLM Workflows for Conclusion Generation
- [SCI-000127/fulltext] (NEUTRAL) Reproducibility is supported by releasing source code, step-by-step reproduction scripts, the preprocessed dataset, and the annotation platform code, plus a README with setup instructions.
  QUOTE: To facilitate reproducibility, we will release the source code and scripts in an anonymous repository during the review process. The repository will include: (i) a Data folder containing the preprocessed MedMeta dataset,
  TOK: [SCI-000127#reproducibility-statement#FULLTEXT-264] | SEC: Reproducibility Statement
- [SCI-000127/fulltext] (NEUTRAL) The benchmark defines six distinct synthesis workflows varying input type (parametric vs. retrieved), reasoning strategy (zero-shot vs. CoT), and retrieval fidelity (oracle, noisy, negated) to enable fine-grained evaluation of synthesis behavior.
  QUOTE: The benchmark includes six distinct synthesis workflows varying in input type (parametric vs. retrieved), reasoning strategy (zero-shot vs. chain-of-thought), and retrieval fidelity (oracle, noisy, or negated), enabling 
  TOK: [SCI-000127#3-1-figure-2-caption#FULLTEXT-265] | SEC: 3.1 (Figure 2 caption)
- [SCI-000128/fulltext] (POSITIVE) An independent Search Agent decouples evidence acquisition from downstream mechanistic reasoning, so the reasoning and visualization agents operate over shared evidence objects rather than reconstructing information from free-form text.
  QUOTE: an independent Search Agent that decouples evidence acquisition from downstream mechanistic reasoning, supporting both the citation-grounded report and an interactive evidence workspace, without independently regeneratin
  TOK: [SCI-000128#abstract#FULLTEXT-276] | SEC: Abstract
- [SCI-000128/fulltext] (POSITIVE) BioInsight uses typed artifact contracts between retrieval, reasoning, writing, and dashboard construction agents, exposing protein, pathway, publication, and citation links that are usually hidden in end-to-end biomedical agents.
  QUOTE: By enforcing artifact contracts between retrieval, reasoning, writing, and dashboard construction, BioInsight exposes protein, pathway, publication, and citation links that are usually hidden in end-to-end biomedical age
  TOK: [SCI-000128#conclusion#FULLTEXT-277] | SEC: Conclusion
- [SCI-000128/fulltext] (POSITIVE) The reasoning-note schema requires the Reasoning Agent to state what the pathway does, why it matters for the disease, which input proteins drive the interpretation, which interaction modules support the mechanism, and where evidence is weak or indirect.
  QUOTE: This schema gives the Reasoning Agent a narrow and inspectable output channel. It must state what the pathway does, why it may matter for the disease, which input proteins drive the interpretation, which interaction modu
  TOK: [SCI-000128#appendix-a-2-intermediate-artifacts-and-#FULLTEXT-278] | SEC: Appendix A.2 > Intermediate Artifacts and Reasoning Notes
- [SCI-000129/fulltext] (supportive) All prompts and LLM outputs are publicly available on Zenodo for reproducibility purposes.
  QUOTE: All prompts and LLM outputs used in this study are publicly available on Zenodo for reproducibility purposes at: https://doi.org/10.5281/zenodo.14177022.
  TOK: [SCI-000129#data-availability-statement#FULLTEXT-285] | SEC: Data Availability Statement
- [SCI-000129/fulltext] (supportive) Verification was applied through cross-checking among human reviewers (manual) and double-checking via comparison with manual results plus review of discrepancies (LLM-assisted).
  QUOTE: Verification Applied Cross-checking among human reviewers Double-checking: comparison with manual results + review of discrepancies
  TOK: [SCI-000129#barros-et-al-verification-and-risk-mitig#FULLTEXT-286] | SEC: Barros et al. > Verification and Risk Mitigation
- [SCI-000131/fulltext] (POSITIVE) A three-stage evidence-to-claim audit cascade (experiment-audit, result-to-claim, paper-claim-audit) provides code-level integrity checking, evidence-to-claim mapping, and independent manuscript-level verification against raw evidence files.
  QUOTE: Stage 1 audits evaluation integrity, Stage 2 maps results to explicit claims, and Stage 3 independently verifies manuscript claims against the source and raw evidence using a reviewer that the recommended configuration d
  TOK: [SCI-000131#methods-evidence-to-claim-audit-cascade#FULLTEXT-294] | SEC: Methods > Evidence-to-Claim Audit Cascade
- [SCI-000131/fulltext] (POSITIVE) ARIS decomposes the research workflow into five end-to-end workflows chained through plain-text artifact contracts, with a per-project research wiki providing persistent cross-session memory of papers, ideas, experiments, and tracked claims.
  QUOTE: Five workflows—idea discovery, experiment bridge, auto-review, paper writing, and rebuttal—chained through plain-text artifact contracts and grouped into four research phases (Discovery, Experimentation, Manuscript, Post
  TOK: [SCI-000131#methods-workflow-library-overview#FULLTEXT-295] | SEC: Methods > Workflow library overview
- [SCI-000131/fulltext] (POSITIVE) Each research capability is defined by a SKILL.md file containing YAML frontmatter followed by a natural-language workflow specification with inputs, outputs, step-by-step procedures, quality gates, and failure-handling instructions.
  QUOTE: Each research capability is defined primarily by a SKILL.md file, a plain-text Markdown specification that can be interpreted by multiple LLM-based coding agents, enabling independent development, domain-specific extensi
  TOK: [SCI-000131#methods-skills-layer#FULLTEXT-296] | SEC: Methods > Skills Layer
- [SCI-000135/fulltext] (POSITIVE) AutoSynthesis is an end-to-end multi-agent framework that automates the complete meta-analysis workflow from literature retrieval and study screening to quantitative data extraction, effect size computation, and statistical synthesis.
  QUOTE: In this work, we introduced AUTOSYNTHESIS, an end-to-end multi-agent framework that automates the complete meta-analysis workflow, from literature retrieval and study screening to quantitative data extraction, effect siz
  TOK: [SCI-000135#body#FULLTEXT-304] | SEC: body
- [SCI-000135/fulltext] (POSITIVE) AutoSynthesis records traceable audit logs and intermediate outputs, including screening decisions, eligibility judgments, extracted statistics, and effect size calculations.
  QUOTE: AUTOSYNTHESIS records traceable audit logs and intermediate outputs, including screening decisions, eligibility judgments, extracted statistics, and effect size calculations.
  TOK: [SCI-000135#body#FULLTEXT-305] | SEC: body
- [SCI-000135/fulltext] (POSITIVE) The modular, multi-agentic design allows users to start the workflow at later stages, for example when updating an existing meta-analysis, or to override specific design choices.
  QUOTE: The modular, multi-agentic design also allows users to start the workflow at later stages, for example, when updating an existing meta-analysis for which parts of the review process have already been completed, or to ove
  TOK: [SCI-000135#body#FULLTEXT-306] | SEC: body
- [SCI-000137/fulltext] (POSITIVE) LLM outputs were saved before being linked to human decisions or full-text outcomes, and manual post-processing was restricted to identifier-based merging with no LLM screening decision changed on substantive grounds.
  QUOTE: LLM outputs were saved before they were linked to human decisions or full-text outcomes. Manual post-processing was restricted to identifier-based merging and formatting standardisation; no LLM screening decision was cha
  TOK: [SCI-000137#methods-integrity-checks-and-safeguard-p#FULLTEXT-315] | SEC: Methods > Integrity checks and safeguard procedures
- [SCI-000137/fulltext] (POSITIVE) Safeguards against outcome leakage included disabling memory, processing file-batch inputs in separate conversations, retaining stable identifiers, and instructing models to assign Unclear rather than confident exclusion for ambiguous records.
  QUOTE: Memory was disabled; file-batch inputs were processed in separate conversations; stable identifiers were retained throughout; and the instructions explicitly required ambiguous or insufficiently described records to rece
  TOK: [SCI-000137#methods-integrity-checks-and-safeguard-p#FULLTEXT-316] | SEC: Methods > Integrity checks and safeguard procedures
- [SCI-000137/fulltext] (POSITIVE) Stable record identifiers were preserved throughout the entire input, model-output, merging, and analysis pipeline, enabling traceability of each screening decision back to its source record.
  QUOTE: Stable record identifiers were preserved throughout the input, model-output, merging, and analysis pipeline. During import and merging, outputs were inspected for apparent problems in record coverage, duplicate or missin
  TOK: [SCI-000137#methods-integrity-checks-and-safeguard-p#FULLTEXT-317] | SEC: Methods > Integrity checks and safeguard procedures
- [SCI-000137/fulltext] (POSITIVE) The analysis code, benchmark input data, LLM prompts, screening outputs, and comprehensive analytical results are archived in open supplementary materials, allowing reported comparisons to be reconstructed.
  QUOTE: The analysis code, benchmark input data, LLM prompts, screening outputs, detailed statistical definitions, and comprehensive analytical results are archived in the accompanying open materials, allowing the reported compa
  TOK: [SCI-000137#methods-software-and-computational-repro#FULLTEXT-318] | SEC: Methods > Software and computational reproducibility
- [SCI-000138/fulltext] (POSITIVE) Full-text synthesis employs retrieval-augmented generation (RAG) with hybrid vector and graph-based retrieval, and RAG outperformed non-retrieval generation for queries requiring structured constraints, cross-study integration, and graph-based reasoning, while non-RAG remained competitive for high-level summaries.
  QUOTE: RAG outperformed non-retrieval generation for queries requiring structured constraints, cross-study integration, and graph-based reasoning, whereas non-RAG approaches remained competitive for high-level summaries.
  TOK: [SCI-000138#abstract#FULLTEXT-327] | SEC: ABSTRACT
- [SCI-000138/fulltext] (POSITIVE) Kernel produces consistent, explainable screening decisions with a ternary output space (include, exclude, maybe), preserving calibrated uncertainty and closely mirroring expert reasoning in information-sparse scenarios.
  QUOTE: These findings indicate that Kernel closely mirrors expert reasoning in information-sparse scenarios while providing consistent, explainable screening decisions.
  TOK: [SCI-000138#results#FULLTEXT-328] | SEC: RESULTS
- [SCI-000138/fulltext] (POSITIVE) The AI co-scientist is designed as a multi-representational platform integrating relational databases, vector-based semantic retrieval, and a Neo4j knowledge graph, and is described as domain-agnostic with a practical framework for reducing research waste across biomedical disciplines.
  QUOTE: We designed a multi-representational platform integrating relational databases, vector-based semantic retrieval, and a Neo4j knowledge graph, evaluated on dementia-sport (DS) and non-communicable disease (NCD) corpora.
  TOK: [SCI-000138#abstract#FULLTEXT-329] | SEC: ABSTRACT
- [SCI-000138/fulltext] (POSITIVE) The platform embeds explicit PICOS formalization and explainable NLP into evidence synthesis workflows to improve scalability, transparency and efficiency, framing structured formalization as a route to auditable synthesis.
  QUOTE: This AI co-scientist demonstrates that embedding PICOS-aware, explainable NLP into evidence synthesis workflows can improve scalability, transparency, and efficiency.
  TOK: [SCI-000138#abstract#FULLTEXT-330] | SEC: ABSTRACT
- [SCI-000140/fulltext] (NEUTRAL) Brain Researcher anchors each auditable episode in a commitment card written before any analysis, sealed with a content hash so that any later change to the plan is detectable, and a claim card written afterward by the review layer recording the resulting claim, its assigned state, scope, and the checks it passed and failed.
  QUOTE: A commitment card, written before any analysis runs, fixes the question, the allowed alternatives, and the success and failure criteria, and is sealed with a content hash so that any later change to the plan is detectabl
  TOK: [SCI-000140#results-brain-researcher-converts-resear#FULLTEXT-338] | SEC: Results > Brain Researcher converts research questions into auditable claim records
- [SCI-000140/fulltext] (NEUTRAL) Brain Researcher defines six terminal claim states (accepted, qualified, revised, blocked, rejected, deferred) with explicit adjudication criteria, and routes unresolved decisions for human escalation rather than treating the verdict as a veto.
  QUOTE: S8 defines the six terminal claim states used for the reported collaborator and bounded-autonomous evaluations and routes unresolved decisions for human escalation.
  TOK: [SCI-000140#supplementary-methods-overview-of-the-su#FULLTEXT-339] | SEC: Supplementary Methods > Overview of the Supplement
- [SCI-000140/fulltext] (NEGATIVE) Brain Researcher exposes the limit of its formal audit layer in the NeuroMark episode: automated review failed to detect sign-blind scoring (after a server fault triggered fallback to a general-purpose agent that scored permutation p < 0.05 as favorable regardless of sign), and a human reviewer found the error, after which two checks were added to the skillset.
  QUOTE: NM-H2 also supplied the audit’s governance lesson: automated review missed an error that a human caught. After a server-side fault triggered fallback to a general-purpose coding agent, the agent scored any specification 
  TOK: [SCI-000140#results-brain-researcher-runs-multiverse#FULLTEXT-340] | SEC: Results > Brain Researcher runs multiverse analyses to expose claim sensitivity
- [SCI-000140/fulltext] (NEUTRAL) Brain Researcher returns an audit bundle linking the committed plan, tool calls, artifacts, evidence, and claim verdicts, mediated by a Model Context Protocol server that controls which actions a model may take.
  QUOTE: A tool registry and the Brain Researcher Knowledge Graph connect analysis routes to evidence and method conditions; a Model Context Protocol server mediates model actions; and execution and review layers return an audit 
  TOK: [SCI-000140#introduction#FULLTEXT-341] | SEC: Introduction
- [SCI-000140/fulltext] (NEUTRAL) In the NeuroMark collaborator case, Brain Researcher expanded a single pre-specified pipeline into a 480-specification multiverse covering connectivity, confound, dimensionality-reduction, classifier, and domain-granularity choices, recorded and reviewed all resulting runs, and automated review missed a sign-blind scoring error that a human reviewer caught by inspecting code and outputs.
  QUOTE: Brain Researcher expanded the analysis into a 480-specification multi- verse spanning connectivity, confound, dimensionality-reduction, classifier, and domain-granularity choices, and recorded and reviewed the resulting 
  TOK: [SCI-000140#results-brain-researcher-runs-multiverse#FULLTEXT-342] | SEC: Results > Brain Researcher runs multiverse analyses to expose claim sensitivity
- [SCI-000140/fulltext] (NEUTRAL) The run-bundle card records the event trace, trajectory document, observation record, analysis bundle, expected and produced artifacts, checksums, backend and software versions, preflight results, failures, retries, recovery events, and final execution status, and completed runs are hosted in an immutable provenance record.
  QUOTE: The run-bundle card records event trace, trajectory document, observation record, analysis bundle, run card, expected artifacts, produced artifacts, missing artifacts, checksums, backend versions, software versions, cont
  TOK: [SCI-000140#supplementary-methods-appendix-f-artifac#FULLTEXT-343] | SEC: Supplementary Methods > Appendix F: artifact-manifest records
- [SCI-000140/fulltext] (NEUTRAL) The scientific verification layer consumes the run bundle (rather than the model transcript alone), checking the selected plan, active constraints, execution trace, artifact manifest, logs, QC outputs, scorecards, candidate claims, and prior evidence, to prevent fluent explanations from substituting for observed artifacts.
  QUOTE: Scientific verification consumes the run bundle, not the model transcript alone. It checks the selected plan, active constraints, execution trace, artifact manifest, logs, QC outputs, scorecards, candidate claims, and pr
  TOK: [SCI-000140#supplementary-methods-s8-scientific-veri#FULLTEXT-344] | SEC: Supplementary Methods > S8. Scientific verification layer and claim calibration
- [SCI-000141/fulltext] (POSITIVE) An error-tolerant interface lets users see which data is provided as input when the LLM calls a tool, helping determine whether the tool was called as expected, and allows modification of all messages and generated data.
  QUOTE: the user should be able to see which data is provided as input when the LLM calls a tool. This helps determine whether the tool was called as expected.
  TOK: [SCI-000141#4-framework-for-ai-assisted-research-4-2#FULLTEXT-352] | SEC: 4 Framework for AI-Assisted Research > 4.2 Design Principles > Error-Tolerance
- [SCI-000141/fulltext] (NEUTRAL) External tools (Crossref, ORCID, Semantic Scholar, ORKG) are integrated into a Tool Library, called automatically by the LLM and made dynamically addable via the Model Context Protocol (MCP), including support for users to set up MCP servers for REST-endpoint tools.
  QUOTE: To ensure tools can be added dynamically, a Model Context Protocol (MCP) can be used. MCP provides a standardized approach to provide external access to LLMs. In this case, we are specifically interested in enabling call
  TOK: [SCI-000141#4-framework-for-ai-assisted-research-4-1#FULLTEXT-353] | SEC: 4 Framework for AI-Assisted Research > 4.1 Core System Modules > Tool Library
- [SCI-000141/fulltext] (POSITIVE) For transparency and reproducibility, the platform requires provenance data to be recorded for all generated artifacts (creators, model name and version, system and user prompts, invoked tools) and published as machine-readable research data, e.g., via RO-Crates.
  QUOTE: for all generated artifacts, provenance data has to be recorded, capturing the creators, model name, and model version, system and user prompts, invoked tools, etc. To provide complete transparency, this provenance data 
  TOK: [SCI-000141#4-framework-for-ai-assisted-research-4-2#FULLTEXT-354] | SEC: 4 Framework for AI-Assisted Research > 4.2 Design Principles > Transparency and Trustworthiness
- [SCI-000141/fulltext] (NEUTRAL) The Prompt Library is a collection of system prompts tailored to specific research-life-cycle tasks, each carrying metadata about the addressed task and available in multiple variants that users can see and modify.
  QUOTE: The Prompt Library is a collection of system prompts tailored toward specific tasks of the research life cycle. A list of prompts minimizes the need for researchers to create their own prompts, often relying on time-cons
  TOK: [SCI-000141#4-framework-for-ai-assisted-research-4-1#FULLTEXT-355] | SEC: 4 Framework for AI-Assisted Research > 4.1 Core System Modules > Prompt Library
- [SCI-000141/fulltext] (POSITIVE) The TIB AIssistant enables agent communication through a centralized data store, which the authors argue makes the context-window constraint less problematic and keeps agents self-contained and independently usable.
  QUOTE: The ability of different agents to communicate with each other can be accomplished via a centralized data store. Compared to keeping all generated content in the context of the LLM, this approach has several benefits: th
  TOK: [SCI-000141#4-framework-for-ai-assisted-research-4-1#FULLTEXT-356] | SEC: 4 Framework for AI-Assisted Research > 4.1 Core System Modules > Data Store
- [SCI-000141/fulltext] (NEUTRAL) The platform centers on human-machine collaboration in which the human researcher primarily orchestrates, directs, and reviews AI-supported processes and retains control at all times, rather than aiming for full automation.
  QUOTE: In such a hybrid approach, the human researcher primarily orchestrates, directs, and reviews AI-supported processes. In this model, researchers have control at all times and review and evaluate the output created by the 
  TOK: [SCI-000141#4-framework-for-ai-assisted-research-4-2#FULLTEXT-357] | SEC: 4 Framework for AI-Assisted Research > 4.2 Design Principles > Human-Machine Collaboration
- [SCI-000142/fulltext] (POSITIVE) Five mandatory human decision points enforce oversight at PICO definition, screening disagreement resolution, analysis type selection, GRADE quality assessment, and interpretation and clinical implications.
  QUOTE: Human decision points are embedded at five junctures: (1) PICO definition and eligibility criteria; (2) screening disagreement resolution; (3) analysis type selection (pairwise vs network meta-analysis); (4) GRADE qualit
  TOK: [SCI-000142#methods-pipeline-architecture#FULLTEXT-363] | SEC: Methods > Pipeline Architecture
- [SCI-000142/fulltext] (POSITIVE) Manuscript assembly reads effect estimates directly from R output files to prevent hallucination of statistical results, a capability unique among current SR automation tools.
  QUOTE: Manuscript assembly uses Quarto templates for each IMRaD section, reading effect estimates directly from R output files to prevent hallucination of statistical results. This capability is unique among current SR automati
  TOK: [SCI-000142#methods-manuscript-generation-and-qualit#FULLTEXT-364] | SEC: Methods > Manuscript Generation and Quality Assurance
- [SCI-000142/fulltext] (POSITIVE) meta-pipe comprises 10 sequential stages each implemented as a self-contained skill module with defined inputs, outputs, and quality thresholds, with inter-stage data contracts specifying file schemas at each boundary.
  QUOTE: meta-pipe comprises 10 sequential stages (Table 1), each implemented as a self-contained skill module with defined inputs, outputs, and quality thresholds. Each skill module is a structured prompt document containing wor
  TOK: [SCI-000142#methods-pipeline-architecture#FULLTEXT-365] | SEC: Methods > Pipeline Architecture
- [SCI-000144/fulltext] (NEUTRAL) All experimental conditions used deterministic decoding (temperature 0) with no retrieval augmentation, and the design produced 2,880 runs yielding 17,443 individual citations.
  QUOTE: All conditions use deterministic decoding (temperature 0) with no retrieval augmentation. The full design yields 144×5×4 = 2,880 runs producing 17,443 individual citations.
  TOK: [SCI-000144#3-experimental-design#FULLTEXT-371] | SEC: 3 Experimental Design
- [SCI-000144/fulltext] (NEUTRAL) The study uses a deterministic verification pipeline that parses each generated citation and checks it against Crossref and Semantic Scholar, running identically on every model and condition, with code publicly available.
  QUOTE: Our pipeline checks every generated citation against two scholarly databases—Crossref and Semantic Scholar—which together cover most of the indexed literature. The same pipeline runs identically on every model and condit
  TOK: [SCI-000144#4-verification-pipeline#FULLTEXT-372] | SEC: 4 Verification Pipeline
- [SCI-000148/abstract_only] (POSITIVE) An LLM-based ranking approach is proposed to select initial studies for literature review automation, addressing the bottleneck of manual data extraction from the scientific literature.
  QUOTE: This study examines the application of a lar
  TOK: [SCI-000148#abstract#FULLTEXT-386] | SEC: ABSTRACT
- [SCI-000151/fulltext] (NEUTRAL) LLAssist emits structured JSON and CSV outputs containing extracted semantics, relevance scores, and reasoning, deliberately requiring downstream analysis to enforce a human-in-the-loop workflow with process visibility.
  QUOTE: LLAssist provides two types of output: 1. a JSON file containing detailed information for each processed article, including extracted semantics, relevance scores, and reasoning, and 2. a CSV file presenting the same info
  TOK: [SCI-000151#2-1-5-output-generation#FULLTEXT-387] | SEC: 2.1.5 Output Generation
- [SCI-000151/fulltext] (NEUTRAL) LLAssist implements Chain-of-Thought as a two-step pipeline — key-semantics extraction followed by self-consistency-based filtering of the most consistent reasoning path.
  QUOTE: In LLAssist, CoT is simulated through two main steps: 1. Extract Key Semantics: The model helps to generate intermediate reasoning steps, expanding on key concepts in the prompt. 2. Filtering: From the expanded reasoning
  TOK: [SCI-000151#3-technical-implementation#FULLTEXT-388] | SEC: 3 Technical Implementation
- [SCI-000151/fulltext] (NEUTRAL) LLAssist supports both local models provisioned via Ollama (Llama 3, Gemma 2) and cloud models (GPT-3.5, GPT-4), letting researchers trade off processing speed, accuracy, and data-privacy concerns.
  QUOTE: This flexibility allows researchers to choose models based on their specific requirements, such as processing speed, accuracy, or data privacy concerns.
  TOK: [SCI-000151#3-technical-implementation#FULLTEXT-389] | SEC: 3 Technical Implementation
- [SCI-000152/fulltext] (NEUTRAL) A limitation noted is that timing the entire screening process for two raters would have provided more reliable results, as a well-planned parallel two-human-rater process might have taken almost the same time as one rater using LLMs, which was not reflected in the study.
  QUOTE: Our current study gives a close estimation of performance, but timing the entire process for two raters would have provided more reliable results. A well-planned screening process where two human raters are working in pa
  TOK: [SCI-000152#results#FULLTEXT-400] | SEC: RESULTS
- [SCI-000154/fulltext] (POSITIVE) OpenScholar can enhance off-the-shelf LMs: when GPT-4o is used as the underlying model, OpenScholar-GPT-4o achieves a 12% improvement in correctness compared with GPT-4o alone, demonstrating a pipeline-level boost independent of model weights.
  QUOTE: Furthermore, OpenScholar's use of smaller, efficient retrievers substantially reduced costs. The OpenScholar pipeline can also enhance off-the-shelf LMs. For example, when using GPT-4o as the underlying model, OpenSchola
  TOK: [SCI-000154#evaluation#FULLTEXT-410] | SEC: EVALUATION
- [SCI-000154/fulltext] (POSITIVE) OpenScholar introduces the OpenScholar DataStore (OSDS), a fully open, up-to-date corpus of 45 million scientific papers and 236 million passage embeddings, explicitly positioned as a reproducible foundation for training and inference in literature synthesis.
  QUOTE: OSDS is a fully open, up-to-date corpus of 45 million scientific papers and 236 million passage embeddings, offering a reproducible foundation for training and inference.
  TOK: [SCI-000154#introduction#FULLTEXT-411] | SEC: INTRODUCTION
- [SCI-000154/fulltext] (POSITIVE) OpenScholar is described as the first fully open, retrieval-augmented LM specifically designed for scientific research tasks, and all artefacts including code, models, data store, datasets and a public demo are open-sourced, supporting reproducibility.
  QUOTE: to our knowledge the first fully open, retrieval-augmented LM specifically designed for scientific research tasks. OpenScholar integrates a domain-specialized data store (OpenScholar DataStore, OSDS), adaptive retrieval 
  TOK: [SCI-000154#introduction#FULLTEXT-412] | SEC: INTRODUCTION
- [SCI-000154/fulltext] (POSITIVE) The self-feedback inference loop, reranking and retrieval are core components that evaluation demonstrates as important to OpenScholar's performance, indicating that the orchestrated pipeline itself, not just the base LM, drives literature synthesis quality.
  QUOTE: Our extensive evaluations demonstrate the importance of the core components of OpenScholar, including reranking, self-feedback and
  TOK: [SCI-000154#evaluation#FULLTEXT-413] | SEC: EVALUATION
- [SCI-000156/fulltext] (POSITIVE) The RAG approach builds a custom OpenAI Assistant with the SciTLDR dataset as the LLM knowledge base with retrieval enabled.
  QUOTE: The third procedure utilizes the RAG-based approach by using the Large Language Model: GPT-3.5-TURBO-0125. The first task is to create a custom OpenAI Assistant. Firstly, the SciTLDR dataset is collected, and then the GP
  TOK: [SCI-000156#body#FULLTEXT-421] | SEC: body
- [SCI-000156/fulltext] (POSITIVE) The primary objective is a system that automatically generates the literature review segment of a research paper using only the PDF files of related papers as input.
  QUOTE: The primary objective of this research is to develop a system that can automatically generate the literature review segment of a research paper by using only the PDF files of the related papers as input.
  TOK: [SCI-000156#body#FULLTEXT-422] | SEC: body
- [SCI-000156/fulltext] (POSITIVE) The system pipeline takes DOIs and PDFs of multiple papers as input, using PYPDF2 and Regular Expression libraries to collect each PDF's abstract, introduction, and conclusion before summarization.
  QUOTE: The system takes the DOI and PDF of multiple papers as input. It uses the Requests library to collect the paper titles and first author names from DOIs. Then it uses PYPDF2 and Regular Expression (RE) libraries to collec
  TOK: [SCI-000156#body#FULLTEXT-423] | SEC: body
- [SCI-000158/fulltext] (supportive) The multi-agent system operates through four sequential agents: (1) search string generation agent, (2) paper selection agent, (3) data extraction agent, and (4) data compilation agent — each with a defined role and handoff.
  QUOTE: Upon receiving the topic, the system systematically generates a pertinent set of research questions.
  TOK: [SCI-000158#sami-et-al-results-search-string-and-rqs#FULLTEXT-431] | SEC: Sami et al. > Results > Search String and RQs
- [SCI-000158/fulltext] (supportive) The paper selection agent applies inclusive and exclusive filtering criteria based on titles to refine search results, ensuring only the most pertinent literature is considered.
  QUOTE: the system is equipped with the capability to apply inclusive and exclusive criteria based on titles, which further refines the search results to ensure only the most pertinent literature is considered for review.
  TOK: [SCI-000158#section-4-1-llm-based-multi-agent-system#FULLTEXT-432] | SEC: Section 4.1 (LLM Based Multi-Agent System)
- [SCI-000159/fulltext] (supportive) High-quality training data is generated synthetically using the inference-time pipeline, with a two-step data filtering process (pairwise-filtering and rubric-filtering) to remove hallucinations and repetitive writing.
  QUOTE: Despite its effectiveness and scalability, synthetic data may also contain issues such as hallucinations, repetitive writing, or limited instruction-following ... we introduce a two-step data filtering process: pairwise-
  TOK: [SCI-000159#section-2-3-training-high-quality-synthe#FULLTEXT-437] | SEC: Section 2.3 (Training: High-Quality Synthetic Data Generation)
- [SCI-000159/fulltext] (supportive) OpenScholar includes a citation verification step where the generator LM ensures all citation-worthy statements are supported by references from retrieved passages, performing post hoc insertion for unsupported claims.
  QUOTE: the generator ensures that all citation-worthy statements—scientific claims requiring justification—are adequately supported by references from the retrieved passages. If any claims lack proper citations, the LM performs
  TOK: [SCI-000159#section-2-2-inference-iterative-generati#FULLTEXT-438] | SEC: Section 2.2 (Inference: Iterative Generation with Retrieval-Augmented Self-Feedback)
- [SCI-000159/fulltext] (supportive) OpenScholar's iterative self-feedback retrieval-augmented inference pipeline generates outputs with inline citations linked to specific passages from scientific literature, enabling researchers to trace output back to original literature and ensuring transparency and verifiability.
  QUOTE: These citations allow researchers to trace the output back to the original literature, ensuring transparency and verifiability.
  TOK: [SCI-000159#section-2-overview-of-openscholar#FULLTEXT-439] | SEC: Section 2 (Overview of OPENSCHOLAR)
- [SCI-000159/fulltext] (supportive) The OpenScholar-Datastore (OSDS) is built from 45 million papers using peS2o v3, producing 234 million passages — described as the largest open-sourced datastore for scientific literature.
  QUOTE: we use peS2o v3, which includes 45 million papers up until October 2024. ... Our datastore consists of 234 million passages. To our knowledge, this is the largest open-sourced datastore for scientific literature.
  TOK: [SCI-000159#section-2-1-openscholar-retrieval-pipeli#FULLTEXT-440] | SEC: Section 2.1 (OPENSCHOLAR Retrieval Pipeline)
- [SCI-000159/fulltext] (supportive) The authors open-source all components — code, data, model checkpoints, datastores, and the SCHOLARQABENCH benchmark — to support reproducibility and accelerate future research.
  QUOTE: We open-source the OPENSCHOLAR code, data, model checkpoints, datastores, and SCHOLARQABENCH, along with a public demo, to support and accelerate future research efforts.
  TOK: [SCI-000159#section-7-conclusion#FULLTEXT-441] | SEC: Section 7 (Conclusion)
- [SCI-000164/fulltext] (NEUTRAL) For fair comparison, the authors replicate the QA-based baseline with open-weights embeddings and a temperature of 0 instead of 0.2, deliberately increasing reproducibility over the original work.
  QUOTE: To in- crease reproducibility, we use a temperature of 0 instead of 0.2 as in the original work.
  TOK: [SCI-000164#5-3-baselines#FULLTEXT-449] | SEC: 5.3 Baselines
- [SCI-000164/fulltext] (NEUTRAL) LGAR's output parsing is engineered for determinism and reproducibility: temperature 0, regular-expression extraction of scale-verified scores, up to three retry attempts on malformed responses, and a fallback assignment of the average of generated relevance scores.
  QUOTE: Output Parsing. To make the responses as de- terministic and reproducible as possible, we use a temperature of 0. The scores are extracted using regular expression and we verify that they are in the desired relevance sca
  TOK: [SCI-000164#5-1-model-selection-and-experimental-set#FULLTEXT-450] | SEC: 5.1 Model Selection and Experimental Settings
- [SCI-000164/fulltext] (NEUTRAL) Model selection for LGAR is constrained to open-weights LLMs explicitly to enhance the reproducibility of the results.
  QUOTE: To enhance the reproducibility of our results, our model selection of instruction-following LLMs is constrained to open-weights alternatives.
  TOK: [SCI-000164#5-1-model-selection-and-experimental-set#FULLTEXT-451] | SEC: 5.1 Model Selection and Experimental Settings
- [SCI-000172/fulltext] (supportive) A progressive five-step testing methodology was implemented, scaling from 1 article with 10 manual questions (Experiment #1) to 30 articles with 10 AI-generated cross-document synthesis questions (Experiment #5).
  QUOTE: The implementation strategy has 5 incremental steps, meant to evaluate the solution progressively, from small functional tests to a large-scale volume testing.
  TOK: [SCI-000172#methodology#FULLTEXT-462] | SEC: Methodology
- [SCI-000172/fulltext] (supportive) The proposed RAG architecture integrates Azure Blob Storage (crawling/storage), Azure AI Search (embedding/indexing), and Azure OpenAI (LLM generation) with custom Python automation tools, forming an end-to-end pipeline from data acquisition to aggregated responses.
  QUOTE: The solution architecture used in this study aggregates: crawling, cloud storage, embedding, indexing, LLM, and automation services ... integrating mature software tools as Azure AI Search (for embeddings and vector spac
  TOK: [SCI-000172#methodology-figure-5#FULLTEXT-463] | SEC: Methodology / Figure 5
- [SCI-000177/abstract_only] (POSITIVE) The work demonstrates an AI system for synthesizing knowledge from scientific literature and curated databases to enable network-based drug repurposing, addressing challenges in evidence synthesis.
  QUOTE: Network-based drug repurposing requires the seamless synthesis of knowledge from both the scientific literature and curated databases, ensuring that researchers capture the best of human expertise alongside robust comput
  TOK: [SCI-000177#abstract#FULLTEXT-470] | SEC: ABSTRACT
- [SCI-000179/fulltext] (POSITIVE) Stage S1 (request intake) logs validated requests and assigns unique identifiers to guarantee idempotent behavior, preventing duplicate processing and establishing a secure, traceable entry point for the pipeline.
  QUOTE: Validated requests are logged and assigned unique identifiers to ensure idempotent behavior, thereby preventing duplicate processing. This stage establishes a secure and traceable entry point for the research automation 
  TOK: [SCI-000179#materials-and-methods-stage-s1-request-i#FULLTEXT-472] | SEC: Materials and Methods > Stage S1 - Request Intake and Validation
- [SCI-000179/fulltext] (POSITIVE) Stage S6 (persistence and status tracking) stores explicit processing-status indicators per record, enabling incremental execution and workflow resumption so previously processed records are not reanalyzed.
  QUOTE: This design enables incremental execution and workflow resumption, ensuring that previously processed records are not reanalyzed.
  TOK: [SCI-000179#materials-and-methods-stage-s6-persisten#FULLTEXT-473] | SEC: Materials and Methods > Stage S6 - Persistence and Status Tracking
- [SCI-000179/fulltext] (POSITIVE) The authors state the workflow supports transparent processing, enables traceability of analytical states, and facilitates efficient management of repeated executions.
  QUOTE: Overall, the workflow supports transparent processing, enables traceability of analytical states, and facilitates efficient management of repeated executions.
  TOK: [SCI-000179#results-and-discussion-incremental-proce#FULLTEXT-474] | SEC: Results and Discussion > Incremental Processing and Knowledge Persistence
- [SCI-000179/fulltext] (POSITIVE) The separation of the AI-assisted analysis stage (S5) from persistence and status management (S6) is described as reinforcing transparency, accountability, and responsible use of AI.
  QUOTE: The separation of AI-assisted analysis (S5) from persistence and status management (S6) reinforces transparency, accountability, and responsible use of AI.
  TOK: [SCI-000179#materials-and-methods-stage-s6-persisten#FULLTEXT-475] | SEC: Materials and Methods > Stage S6 - Persistence and Status Tracking
- [SCI-000179/fulltext] (NEUTRAL) The system's core is a workflow orchestration engine implemented using n8n that enables sequential and conditional execution across multiple heterogeneous data sources.
  QUOTE: At the core of the architecture is a workflow orchestration engine implemented using n8n, enabling sequential and conditional execution across multiple heterogeneous data sources.
  TOK: [SCI-000179#materials-and-methods-system-architectur#FULLTEXT-476] | SEC: Materials and Methods > System Architecture and Design
- [SCI-000179/fulltext] (NEUTRAL) The workflow supports multiple literature-review stages (paper retrieval, preliminary screening, review management) while maintaining human oversight and methodological control, with AI employed as a supportive component rather than a replacement for researcher judgment.
  QUOTE: The workflow supports multiple stages of the literature review process, including paper retrieval, preliminary screening, and review management, while maintaining human oversight and methodological control. Artificial in
  TOK: [SCI-000179#abstract#FULLTEXT-477] | SEC: Abstract
- [SCI-000181/fulltext] (POSITIVE) Domain-specific optimizations such as biomedical entity recognition, relationship extraction and specialized embeddings further enhance performance across diverse research scenarios.
  QUOTE: Domain-specific optimizations such as biomedical entity recognition, relationship extraction, and specialized embeddings further enhance performance across diverse research scenarios.
  TOK: [SCI-000181#abstract#FULLTEXT-486] | SEC: ABSTRACT
- [SCI-000181/fulltext] (POSITIVE) The proposed LLM+RAG architecture features specialized document processing for scientific papers, biomedical-specific vector embeddings, advanced retrieval strategies, and integrates with PubMed and other biomedical databases with natural language interfaces.
  QUOTE: The proposed LLM+RAG architecture offers a comprehensive solution featuring specialized document processing for scientific papers, biomedical-specific vector embeddings, advanced retrieval strategies, and sophisticated r
  TOK: [SCI-000181#abstract#FULLTEXT-487] | SEC: ABSTRACT
- [SCI-000181/fulltext] (POSITIVE) The system uses biomedical-specific vector embeddings trained on massive corpora of biomedical text, with comparative evaluations documenting that specialized biomedical embeddings improve retrieval performance compared to general-purpose embeddings on domain-specific information retrieval tasks.
  QUOTE: Generation of biomedical-specific embeddings involves training or fine-tuning embedding models on massive corpora of biomedical text, resulting in vector representations that more accurately capture the semantic relation
  TOK: [SCI-000181#vector-database#FULLTEXT-488] | SEC: VECTOR DATABASE
- [SCI-000181/fulltext] (NEGATIVE) Traditional keyword-based search tools like PubMed lack the semantic understanding to answer nuanced questions or summarize findings across multiple sources, with traditional search engines relying primarily on lexical matching and statistical term weighting achieving limited precision and recall on complex biomedical queries.
  QUOTE: Traditional keyword-based search tools like PubMed provide access to vast repositories but lack the semantic understanding to answer nuanced questions or summarize findings across multiple sources.
  TOK: [SCI-000181#introduction#FULLTEXT-489] | SEC: INTRODUCTION
- [SCI-000182/abstract_only] (POSITIVE) An AI-assisted, multi-phase framework leverages LLMs to automate major stages of the SLR workflow through an end-to-end modular approach supporting data processing, analysis, and visualization.
  QUOTE: This research presents an AI-assisted, multi-phase framework that leverages Large Language Models (LLMs) to automate and enhance the major stages of the SLR workflow. The proposed system integrates an end-to-end, modular
  TOK: [SCI-000182#abstract#FULLTEXT-496] | SEC: ABSTRACT
- [SCI-000182/abstract_only] (NEGATIVE) The conventional SLR process is characterized as time-consuming, labor-intensive, and susceptible to human bias, motivating the human-AI collaborative modular design.
  QUOTE: the conventional SLR process is time-consuming, labor-intensive, and susceptible to human bias.
  TOK: [SCI-000182#abstract#FULLTEXT-497] | SEC: ABSTRACT
- [SCI-000186/fulltext] (NEUTRAL) A dedicated Evolution Manager Agent (EMA) implements three self-evolution mechanisms — idea direction, idea validation, and experiment strategy evolution — that distill prior outcomes and failures into reusable strategies.
  QUOTE: The evolution manager agent (EMA) converts interaction histories into reusable strategies so that the system can learn from outcomes and failures and improve both idea generation and experiment execution across tasks. Ev
  TOK: [SCI-000186#3-5-evolution-manager-agent#FULLTEXT-498] | SEC: 3.5 Evolution Manager Agent
- [SCI-000186/fulltext] (NEUTRAL) EvoScientist formulates multi-agent evolution as a core requirement for end-to-end scientific discovery, explicitly treating accumulated interaction histories as a first-class resource for reuse rather than discarding them after execution.
  QUOTE: This motivates the formulation of multi-agent evolution as a core requirement for end-to-end scientific discovery, where interaction histories are treated as a first-class resource rather than discarded execution traces.
  TOK: [SCI-000186#1-introduction#FULLTEXT-499] | SEC: 1 Introduction
- [SCI-000186/fulltext] (NEUTRAL) EvoScientist's pipeline integrates external retrieval infrastructure via the Semantic Scholar API for the initial literature review phase, alongside Gemini-based idea generation and Claude-based code generation.
  QUOTE: For the initial literature review phase, we utilize the Semantic Scholar API to retrieve relevant papers. Scientific idea generation is performed using Gemini-2.5-Pro.
  TOK: [SCI-000186#4-5-implementation-details#FULLTEXT-500] | SEC: 4.5 Implementation Details
- [SCI-000186/fulltext] (NEUTRAL) The EvoScientist experiment-execution stage is designed to yield verifiable outputs (logs and metrics) and to produce a structured execution report for each proposal.
  QUOTE: Stage 2 (Experiment Execution) validates 𝑃by searching for and running executable code 𝐶to yield verifiable outputs (e.g., logs and metrics) and to produce an execution report 𝑊.
  TOK: [SCI-000186#3-methodology-problem-formulation#FULLTEXT-501] | SEC: 3 Methodology (Problem Formulation)
- [SCI-000186/fulltext] (NEUTRAL) The engineer agent's experiment tree search stores a structured execution record per attempt that includes run status, logs, and evaluation metrics, providing per-stage execution provenance.
  QUOTE: is a structured execution record that includes run status, logs, and evaluation metrics. The best-performing code at each stage is selected as:
  TOK: [SCI-000186#3-4-engineer-agent-for-experiment-tree-s#FULLTEXT-502] | SEC: 3.4 Engineer Agent for Experiment Tree Search
