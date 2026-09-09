---
workspace_id: "SCI-000138"
doi: null
title: "AI Co-Scientist for Knowledge Synthesis in Medical Contexts: A Proof of Concept"
year: 2026
extraction_engine: "pymupdf"
---
# 2026 Rahgozar AI Co-Scientist for Knowledge Synthesis 

AI Co-Scientist for Knowledge Synthesis in Medical

Contexts: A Proof of Concept

Arya Rahgozara,b, Pouria Mortezaaghaa,b

aMethodological Implementation Research, Ottawa Hospital Research

Institute, Ottawa, ON, Canada bSchool of Engineering Design and Teaching Innovation, University of

arXiv:2601.11825v1  [cs.AI]  16 Jan 2026

Ottawa, Ottawa, ON, Canada


## Abstract

Background: Research waste in biomedical science is driven by redundant studies, incomplete reporting, and limited scalability of conventional evidence synthesis workflows. Objectives: To develop and evaluate an artificial intelligence (AI) co-scientist that enables scalable, transparent knowledge synthesis through explicit Pop- ulation, Intervention, Comparator, Outcome, and Study design (PICOS) for- malization. Methods: We designed a multi-representational platform integrating rela- tional databases, vector-based semantic retrieval, and a Neo4j knowledge graph, evaluated on dementia–sport (DS) and non-communicable disease (NCD) corpora. Automated PICOS compliance classification was performed on titles and abstracts using a Bidirectional Long Short-Term Memory (Bi- LSTM) baseline and a transformer-based multi-task classifier fine-tuned from PubMedBERT. Full-text synthesis employed retrieval-augmented generation (RAG) with hybrid vector and graph-based retrieval. Topic modeling us- ing BERTopic identified thematic structure, redundancy, and evidence gaps. Performance was assessed via classification metrics, expert review, and RAG versus non-retrieval comparison. Results: The transformer-based classifier achieved strong agreement with expert annotations, with study design classification accuracy of 95.7%, while the Bi-LSTM baseline reached 87% accuracy for PICOS compliance de- tection. RAG outperformed non-retrieval generation for queries requiring structured constraints, cross-study integration, and graph-based reasoning, whereas non-RAG approaches remained competitive for high-level summaries.

Topic modeling revealed substantial thematic redundancy and underexplored research areas. Conclusions: This AI co-scientist demonstrates that embedding PICOS- aware, explainable NLP into evidence synthesis workflows can improve scal- ability, transparency, and efficiency. The architecture is domain-agnostic and provides a practical framework for reducing research waste across biomedical disciplines.

Keywords: Knowledge Synthesis, Research Waste, PICOS Compliance, Artificial Intelligence, Natural Language Processing, Retrieval-Augmented Generation


## 1. Introduction

Reducing research waste in knowledge synthesis is increasingly recognized as essential for efficient and high-value scientific inquiry. Research waste arises from redundant, poorly targeted, or inadequately reported studies and substantially undermines downstream evidence synthesis. Scoping reviews play a key role in mitigating these inefficiencies by systematically mapping existing evidence, identifying conceptual and methodological gaps, clarifying outcome definitions, and promoting consistent terminology, thereby help- ing ensure that subsequent research is necessary and appropriately directed rather than duplicative [22]. Effective waste prevention further depends on robust monitoring and evaluation frameworks. Hybrid approaches that in- tegrate survey data, quantitative indicators, and program-level assessment outperform single-method strategies [1], yet significant gaps remain in un- derstanding which mechanisms most effectively incentivize waste reduction across research ecosystems [47]. Evidence suggests that durable reductions in research waste require coordinated packages of interventions rather than isolated measures, highlighting the need for stronger empirical validation [7].

Research waste persists across all stages of evidence generation and syn- thesis. Empirical studies indicate that more than 85% of surgical randomized controlled trials (RCTs) exhibit at least one form of waste, including incom- plete reporting and non-publication [6], with similar deficiencies observed across other biomedical domains [24]. These inefficiencies perpetuate delays in access to complete and reliable evidence, impairing informed decision- making by researchers, clinicians, and policymakers [11, 46].

Within evidence-based healthcare, the PICOS framework (Population,

2

Intervention, Comparator, Outcome, Study design) remains a cornerstone for structuring research questions and guiding systematic reviews. However, its contemporary application reveals both conceptual limitations and oppor- tunities for computational enhancement. Originally developed to support synthesis of intervention effects, PICOS has limited capacity to represent population heterogeneity, mechanistic pathways, or contextual modifiers in- fluencing outcome variability [9]. These limitations have motivated calls for synthesis approaches that integrate aggregative and configurative analyses beyond traditional meta-analytic paradigms. A further challenge is the fre- quent conflation of “PICO for the review” with “PICO for each synthesis,” a distinction that is insufficiently articulated in reporting guidelines and often inadequate for specifying synthesis-level eligibility and analytic criteria [8]. Recent tools such as InSynQ aim to operationalize synthesis questions more explicitly, improving transparency and review planning [8]. From a natu- ral language processing (NLP) perspective, PICOS also provides a useful ontological scaffold for machine-processable representations of clinical ques- tions, supporting automated evidence discovery, structured document pro- cessing, and downstream synthesis [27]. By imposing explicit definitions of Population, Intervention, Comparator, Outcomes, and Study design, PICOS supports efficient search strategies and eligibility criteria that directly guide downstream data extraction and synthesis, reduce retrieval of irrelevant or redundant studies, and improve comparability and reproducibility across het- erogeneous evidence bases.

Methodological frameworks grounded in PICOS have been shown to im- prove coherence and replicability in clinical trial design [25, 49, 48], yet adherence to reporting standards remains inconsistent. Guidelines such as CONSORT [30] and PRISMA [33] are not uniformly applied, limiting their effectiveness in reducing bias and facilitating evidence synthesis. Authors of systematic reviews continue to report substantial challenges in managing large-scale literature searches, screening, and data extraction [10], reinforcing the need for scalable methodological support.

These challenges have driven increasing interest in artificial intelligence (AI) methods for systematic reviews. A growing body of AI-driven NLP systems aims to accelerate literature search, screening, data extraction, and risk-of-bias assessment [31, 20]. While tools such as RobotReviewer and SciSpace demonstrate that AI can significantly reduce manual workload [26, 35, 15], many existing systems lack domain-specific adaptation, transparent uncertainty handling, and mechanisms for continuous updating [28].

3

NLP methods are now integral across the knowledge synthesis pipeline. In early stages, particularly title–abstract screening, automated classifiers can rapidly filter large corpora while maintaining high recall [19]. At later stages, semantic retrieval and similarity-based methods enable concept-level explo- ration of full texts, uncovering relationships not readily captured by keyword search [50]. Citation prioritization models further enhance efficiency and re- producibility by ranking studies by relevance [43]. Despite these advances, full-text processing remains a major bottleneck. Models trained primarily on titles and abstracts often degrade when applied to long-form articles due to increased linguistic complexity, heterogeneous reporting structures, and long- range dependencies [21]. Limited availability of annotated full-text corpora further constrains model development, underscoring the need for domain- adapted architectures and richer annotation resources.

The Brain–Heart Interconnectome (BHI) framework examines bidirec- tional interactions between cardiovascular and neurological systems, with im- portant implications for dementia–sport (DS) research and prevention strate- gies [12, 3, 37, 44]. Although the BHI literature is rapidly expanding, ineffi- ciencies in evidence synthesis and inconsistent adherence to quality standards hinder both clinical translation and research progress. These shortcomings directly contribute to research waste, defined as redundant or low-quality research that fails to generate substantive knowledge [4, 6, 51, 36].

In this study, we examine how NLP can be leveraged to mitigate research waste by strengthening the formalization and operationalization of PICOS across the evidence synthesis pipeline. We evaluate NLP methods for both title–abstract screening and full-text semantic analysis, focusing on how com- putational representations of PICOS elements can improve clarity, reduce re- dundancy, and enhance evidence discovery. We further assess conversational AI systems as tools to support scoping review workflows through interactive, evidence-grounded interrogation of large corpora. These methods are eval- uated across two medical contexts, dementia–sport and non-communicable diseases (NCD), to examine how domain characteristics shape system perfor- mance and the potential of NLP-enabled synthesis to reduce research waste.

Situated within the broader meta-research literature that frames research waste as a systemic problem encompassing redundancy, poor reporting, ir- reproducibility, and misalignment with societal needs [4], our work builds on calls for improved reproducibility [2] and comprehensive frameworks for adding value across the research lifecycle [45]. While these initiatives ar- ticulate foundational principles, they offer limited operational guidance for

4

large-scale evidence identification and synthesis, where waste often becomes entrenched.

Motivated by this gap, we developed an AI co-scientist to support knowl- edge synthesis through explicit PICOS formalization, combining large-scale title–abstract classification with an interactive conversational interface. Rather than addressing research waste abstractly, we ground our investigation in the DS and NCD domains, where evidence bases are rapidly expanding and highly heterogeneous. By enabling explainable PICOS-aware screening and downstream semantic interrogation of full texts, the proposed system sup- ports expert validation of inclusion decisions, exploration of fine-grained PI- COS properties, and targeted querying of large corpora that would otherwise be infeasible to analyze manually. Our objective is to assess whether such an AI co-scientist can meaningfully augment expert judgment, reveal latent pat- terns of non-compliance, and inform practical assessments of research waste in specific clinical domains. Accordingly, we treat PICOS not merely as a screening heuristic, but as a unifying structural framework that constrains search, screening, extraction, and synthesis across the evidence lifecycle, pro- viding a computational handle for identifying and mitigating research waste.

1.1. Aim and Scope of the Proposed System This paper introduces an AI-driven system designed to enhance evidence synthesis in the dementia–sport and NCD domains. The proposed framework integrates:

• Automated PICOS screening: Explainable classification to priori- tize studies aligned with methodological standards.

• Semantic and graph-based retrieval: Hybrid querying using Neo4j [40] and pgVector to expose relational structure among interventions, out- comes, and populations.

• Topic modeling with BERTopic: Identification of dominant themes, redundant clusters, and underexplored research areas [18].

• Conversational recommender system: Evidence-grounded responses to expert queries related to PICOS and research waste.

• Interactive dashboards: User-facing analytics integrating metadata and model-derived annotations to support exploration and policy-relevant insights.

5

1.2. Overall Workflow in Knowledge Synthesis Aligned with standard knowledge synthesis workflows, the system oper- ates across four primary phases (Figure 1):


## 1. Define and search: PICOS-guided query formulation supported by se-

mantic and graph-based retrieval.
2. Screen and assess: Automated PICOS compliance detection and hier-
archical classification.
3. Extract and synthesize: Topic modeling and clustering to identify themes,
redundancy, and emerging trends.
4. Interpret and update: Continuous ingestion of new literature and in-
teractive exploration via dashboards and conversational AI.

By prioritizing high-value evidence and minimizing redundancy, the frame- work aims to improve the efficiency and quality of dementia–sport and NCD evidence synthesis [23, 41, 17, 32, 42].


> **Figure 1: Workflow of the AI-driven system for knowledge synthesis in medical research.**

6

1.3. Medical Expert and Human Requirements Beyond technical considerations, system design was guided by iterative feedback from medical domain experts and stakeholders. Collaboration oc- curred primarily through asynchronous communication, enabling flexible en- gagement. Expert input informed three key areas. First, screening criteria were refined to avoid premature exclusion of studies lacking abstracts, ac- knowledging that incomplete records may still hold value in emerging do- mains. Second, eligibility criteria were aligned with evidence-based frame- works to ensure consistency in participant selection, intervention specifica- tion, comparator definition, and outcome evaluation. Third, evaluation met- rics and terminology were standardized, including explicit alignment of sen- sitivity with recall and clarification of binary labeling conventions for study design classification.

Experts further identified the importance of capturing contextual at- tributes such as study setting (e.g., community-based versus institutional), leading to extensions of the hierarchical classification scheme, including ex- plicit representation of systematic reviews as a distinct study design category. Integrating structured eligibility criteria with expert-driven feedback ensures methodological rigor while maintaining practical relevance. Continued col- laboration with domain experts remains essential for adapting the system to evolving DS and NCD research landscapes.


## 2. Methodology

We developed an end-to-end, modular evidence synthesis platform evalu- ated on two corpora drawn from the dementia–sport (DS) and non-communicable disease (NCD) literature. The system supports (i) structured knowledge ex- traction, (ii) hybrid retrieval and evidence-grounded generation across het- erogeneous data backends, and (iii) interactive, expert-facing exploration for screening, synthesis, and hypothesis generation (Figure 2). The architec- ture is intentionally multi-representational: each corpus is maintained con- currently as (a) a normalized relational database for metadata and model outputs, (b) a passage-level vector index for semantic retrieval, and (c) an explicit knowledge graph for multi-entity biomedical reasoning.

A tool-aware orchestration layer governs multi-step reasoning, routes sub- tasks to appropriate storage layers, and enforces conservative grounding policies, including retrieval-first generation, evidence sufficiency checks, and

7

mandatory citation attachment. These safeguards are designed to mini- mize unsupported claims and ensure traceable evidence use during synthesis. All core components are publicly available, including the agent framework, planning subsystem, graph-centric retrieval, and live database infrastructure: Agents, Planner, GraphRAG, and LiveDB.

The platform comprises two conceptually distinct but tightly integrated components. Kernel refers exclusively to the domain-adapted, multi-task transformer model responsible for automated PICOS and study design clas- sification during title–abstract screening. In contrast, the Conversational Recommender System (CRS) denotes the expert-facing, tool-augmented in- terface that supports natural language querying, retrieval-augmented gener- ation, and structured database interrogation. Kernel outputs are persisted as structured annotations and subsequently consumed by the CRS as filtering constraints and explanatory signals during evidence retrieval and synthesis.


> **Figure 2: Overall workflow for knowledge extraction, hybrid retrieval, and expert-facing**

> querying in the platform.

2.1. Corpus Preparation, Chunking, and Indexing Document ingestion and normalization. Scientific documents relevant to the Brain–Heart Interconnectome (BHI) context are ingested and normalized into a unified representation suitable for retrieval, analytics, and annotation. Bib- liographic metadata, including title, authorship, venue, and publication year, are extracted at ingestion. Each document is assigned a stable identifier prop-

8

agated across relational, vector, and graph layers to support reproducibility, provenance tracking, and cross-store joins.

Passage segmentation and chunk identifiers. To enable retrieval at clinically and methodologically meaningful granularity, documents are segmented into discrete textual passages before embedding and indexing. Chunking reduces context dilution in long-form articles, improves retrieval precision, and sup- ports fine-grained provenance during synthesis. Each chunk receives a unique identifier linked to its parent document, enabling passage-level citation and multi-hop graph relations (e.g., chunk-to-paper and chunk-to-author).

Metadata harmonization and derived annotation attachment. Metadata fields are harmonized across ingestion sources to enable deterministic filtering, ag- gregation, and reproducible cohort selection. Standardized bibliographic at- tributes are augmented with model-derived annotations, including PICOS compliance flags and topic assignments. Persisting these annotations at the record level decouples expensive inference from interactive querying and en- ables consistent application of structured constraints across retrieval, dash- boards, and evaluation workflows.

2.2. Data Representation and Storage Layers Relational layer. A structured relational schema stores bibliographic meta- data, chunk references, and model-derived annotations, including PICOS screening outputs and topic memberships. Treating these outputs as first- class fields supports deterministic filtering, auditability, and integration with business intelligence tools for monitoring screening outcomes and longitudi- nal trends. This design also enables stable reuse of screening labels during retrieval and evaluation without re-running inference.

Vector layer. Semantic retrieval is implemented using a PostgreSQL-backed vector store (pgVector), in which each document chunk is indexed as a dense embedding alongside rich metadata, including publication year, venue, au- thorship, PICOS flags, and topic assignments. This configuration supports similarity search under structured constraints and enables information needs poorly addressed by keyword search, such as cross-study comparisons of intervention–outcome relationships, subgroup-specific findings, and mecha- nistic descriptions expressed with heterogeneous terminology. Leveraging PostgreSQL also supports production requirements, including access control,

9

logging, backups, and monitoring, while enabling retrieval-first RAG work- flows.

Graph layer. Evidence synthesis in the Dementia–Sport (DS) and non-communicable disease (NCD) domains requires reasoning over interconnected entities span- ning populations, interventions, outcomes, phenotypes, study designs, venues, and authorship. We therefore represent extracted entities and relationships using a Neo4j knowledge graph, with nodes corresponding to papers, chunks, authors, topics, interventions, outcomes, and clinical descriptors. Typed edges encode relationships derived from extraction and linkage logic, en- abling multi-hop neighborhood queries and pattern discovery. Compared with purely vector-based retrieval, explicit graph representations support transparent relational exploration and provide interpretable relational paths underlying synthesized answers [34].

2.3. Retrieval-Augmented Generation for DS and NCD Question Answering We implement a corrective, evidence-centric retrieval-augmented genera- tion (RAG) framework for question answering over the BHI literature. Query routing, retrieval, relevance assessment, and synthesis follow an explicit con- trol flow that supports iterative refinement when initial evidence is insuffi- cient (Figure 3). Across modes, the system enforces a unified grounding re- quirement: all substantive claims in generated responses must be supported by retrieved passages with traceable provenance.

This requirement is operationalized through two complementary retrieval pathways: (i) graph-neighborhood retrieval using Neo4j GraphRAG for multi- entity and multi-hop reasoning, and (ii) metadata-aware semantic retrieval using a pgVector-backed store for efficient passage retrieval under structured constraints. Retrieved evidence is exposed to users and paired with sentence- level citations, supporting expert verification and reducing hallucinations.

2.3.1. Graph-neighborhood retrieval with Neo4j GraphRAG In the graph-centric pathway, retrieval is anchored on explicit relational structure and augmented with chunk-level text. Candidate evidence chunks are identified via hybrid retrieval over Neo4j indices using vector similarity and, when available, full-text search. Context is then expanded by travers- ing the local graph neighborhood (one to two hops) surrounding matched chunks. The resulting structured context preserves (i) inbound relations linking chunks to higher-level entities (e.g., papers, abstracts, authors), (ii)

10


> **Figure 3: Workflow for query routing, hybrid retrieval, relevance grading, and corrective**

> refinement when evidence is insufficient for grounded generation.

retrieved chunk texts, and (iii) outbound relations connecting chunks to re- lated biomedical concepts. Edge types and directionality are retained during serialization to support both model grounding and interactive inspection. In the expert interface, graph neighborhoods can be rendered and filtered by node or edge type to enable direct examination of the relational basis underlying each response.

2.3.2. Metadata-aware semantic retrieval with pgVector and contextual com- pression In the vector-first pathway, semantic similarity search is combined with structured constraints inferred from the natural language query. A self-query retriever maps query intent to metadata predicates, including publication year, venue, authorship, PICOS flags, and executes vector search within the constrained candidate set. To reduce redundancy, maximum marginal rele- vance diversification is applied to the top-k results. Retrieved passages are then compressed using a two-stage pipeline: an LLM-based extractor retains

11

query-relevant spans, followed by an embedding-based filter that removes low-similarity content below a configurable threshold. The final output com- prises a consolidated evidence context and a structured list of source descrip- tors (title, authors, venue, publication year, and screening flags), enabling auditable provenance while maintaining focused synthesis.

2.3.3. Agentic orchestration and grounded response policy Queries in the DS and NCD domains frequently require multi-step rea- soning, including enforcement of study design constraints, cross-intervention comparison, and synthesis of methodological limitations. We therefore em- ploy an agentic orchestration framework with explicit planning, execution, and replanning. The planner decomposes each query into a minimal se- quence of atomic steps, including tool invocations (retrieval, graph traversal, or database querying) and evidence-constrained synthesis operations. The executor enforces strict tool discipline: any step requiring factual content must invoke a retrieval or database tool, and unsupported external informa- tion is prohibited.

After each execution step, a replanner evaluates evidence sufficiency against fixed criteria: (i) coverage of all semantic constraints implied by the query, (ii) passage-level support for each substantive claim, and (iii) internal consistency across retrieved sources. The workflow terminates only when these conditions are satisfied; otherwise, targeted follow-up actions are triggered, such as ad- ditional retrieval hops or constraint refinement. This plan–execute–replan loop enforces conservative, evidence-first generation and mitigates prema- ture synthesis (Figure 4).

When retrieval is invoked, the response policy requires sentence-level at- tribution linked directly to supporting passages. Retrieved sources are ex- posed as structured artifacts in the user interface, enabling expert verification and transparent auditing of the synthesis process.

Modeling choices and baselines. We compare retrieval-augmented generation (RAG) with non-retrieval generation for BHI-specific queries. RAG is ex- pected to improve factual accuracy and cross-study integration for queries requiring reconciliation of heterogeneous outcomes or enforcement of struc- tured constraints, consistent with prior work [14]. To ensure stability and re- producibility, all generation is performed using deterministic decoding (tem- perature = 0).

12


> **Figure 4: LangGraph-based agentic control flow for planning, iterative tool use, evidence-**

> grounded synthesis, and replanning until sufficient evidence supports termination.

13

2.4. Automated PICOS Compliance and Explainable Classification To accelerate screening and enable structured retrieval constraints, we im- plement automated classification of PICOS compliance. Predictions are per- sisted in the relational layer, propagated to retrieval metadata, and exposed through user interfaces to support transparent screening and query refine- ment. In addition to supervised classifiers, the system supports description- based title–abstract screening, in which inclusion and exclusion decisions are derived directly from expert-defined textual eligibility criteria using large language models (Appendix Appendix A, Table A.2; Appendix Appendix B, Tables B.3 and B.4).

2.4.1. Kernel: multi-task transformer for PICOS screening Kernel is a multi-task transformer classifier fine-tuned from PubMed- BERT (microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract) to jointly predict Population, Intervention, Comparator, Outcome, and Study design. Each dimension is modeled as a ternary classification task (no, maybe, yes) to explicitly represent uncertainty and borderline cases common in ab- stract screening. Titles and abstracts are concatenated and encoded using a shared transformer backbone followed by parallel classification heads. Train- ing minimizes the mean cross-entropy loss across heads to promote balanced learning across dimensions.

Training, calibration, and conservative self-training. Kernel is trained using AdamW with linear warmup. Iterative expert review informs threshold cali- bration, label refinement, and identification of systematic failure modes, such as implicit population definitions or ambiguous intervention descriptions. To expand coverage while preserving precision, conservative self-training is ap- plied by assigning pseudo-labels only to unlabeled instances for which all PICOS heads exceed a confidence threshold of 0.90, followed by limited re- training iterations.

Interpretability and auditing. Kernel outputs per-dimension labels and con- fidence scores to support triage of borderline cases and targeted human re- view. Performance is evaluated against expert annotations using sensitivity, specificity, precision, recall, F1 score, and confusion matrices, computed per PICOS dimension and for aggregate qualification decisions used as retrieval constraints.

14

2.4.2. Baseline model and study design benchmarking For comparison under non-transformer settings, we implement a Bidirec- tional Long Short-Term Memory (Bi-LSTM) baseline trained on an extended PubMed-PICO dataset [20]. For benchmarking, Kernel outputs are aligned to a binary comparator by mapping yes and maybe to True and no to False. In deployment, richer study design labels are retained for filtering and ana- lytics, while the binary mapping supports comparison with legacy screening workflows.

Rationale for baseline selection. The Bi-LSTM baseline reflects legacy and resource-constrained screening systems that remain prevalent in production review pipelines and provides a computationally lightweight reference point. Its role is to isolate performance gains attributable to contextualized pre- training and domain adaptation in transformer-based models such as Kernel, rather than to compete with state-of-the-art architectures.

2.5. Live Database Connectivity and Agent-Mediated Querying Motivation. Evidence synthesis operates in settings where corpora and an- notations evolve continuously through new ingestions and revised screening decisions. To support operational use beyond static snapshots, the platform provides live connectivity to its databases, ensuring that expert queries reflect the current state of indexed evidence.

Live data plane. The database infrastructure supports iterative updates across DS and NCD contexts. Literature searches are re-executed to ingest newly published or revised records, which are deduplicated, versioned, and logged at the title–abstract level to preserve provenance. The champion screening classifier is applied to refreshed corpora, producing explainable outputs that guide expert validation and prioritize full-text acquisition.

Eligible full texts are parsed, segmented, and propagated to complemen- tary storage layers: relational databases for metadata, vector stores for se- mantic retrieval, and graph databases for modeling relationships across PI- COS elements and study attributes. Updates are propagated immediately to downstream applications, ensuring that conversational and dashboard inter- faces operate on the most current evidence base.

Agent–tool interface and safety constraints. Live querying is mediated by the same tool-aware agent used for RAG workflows. For structured analytics, schema-aware SQL queries are issued to compute real-time aggregates. To

15

reduce brittleness under schema evolution, SQL generation follows a schema- first protocol with identifier normalization and similarity-based resolution. All queries are validated before execution. Retrieval-based responses are constrained to retrieved evidence and require sentence-level attribution.

Session consistency and auditability. Each interaction session is associated with a unique identifier, logging all tool calls and intermediate outputs used to construct responses. Retrieval results may be cached within a session for responsiveness, with explicit refresh available when users require the latest database state. This design balances data freshness, reproducibility, and latency.

2.6. Topic Modeling, Visualization, and Expert Interfaces We apply BERTopic to cluster documents into coherent themes for the- matic navigation, redundancy detection, and identification of evidence gaps. Topic assignments are persisted in both PostgreSQL and Neo4j, enabling lon- gitudinal analysis and structured exploration of topic–intervention–outcome relationships. A Power BI dashboard summarizes publication trends, au- thorship patterns, topic evolution, and screening outcomes to support both high-level monitoring and detailed drill-down analysis (Figure 5).


> **Figure 5: Power BI dashboard summarizing publication trends and screening outcomes.**

2.7. Evaluation Protocol The platform is evaluated along three dimensions: retrieval quality, an- swer faithfulness, and screening accuracy.

16

RAG versus non-RAG generation. Domain experts assess generated responses for correctness, relevance, and completeness, with emphasis on queries re- quiring cross-study integration, outcome synthesis, or enforcement of study design constraints. Errors are categorized as unsupported claims, missed evidence, contradictory synthesis, or overgeneralization.

Retrieval performance and content fidelity. Retrieval quality is quantified us- ing ranking-based metrics, including Mean Reciprocal Rank (MRR). Gener- ation fidelity is assessed using ROUGE, complemented by expert evaluation of factual consistency with retrieved passages. Redundancy among retrieved chunks and evidence coverage for key claims are also tracked.

Screening and study design classification. For Kernel and baseline models, we report sensitivity, specificity, precision, recall, F1 score, and confusion ma- trices against expert-labeled references. Metrics are computed per PICOS dimension and for aggregate qualification decisions used operationally as re- trieval constraints. Study design performance is reported under the binary mapping for benchmarking, with richer labels retained for deployment-time analytics.


## 3. Results

We report results across four complementary components of the evalua- tion framework. First, we assess the performance of the explainable PICOS- based classification system applied to title–abstract screening. Second, we summarize topic modeling analyses that characterize the semantic structure of the corpora. Third, we evaluate a conversational recommender system (CRS) operating over full texts to answer expert queries related to research waste in the dementia–sport and non-communicable disease (NCD) domains. Finally, we describe an interactive dashboard that provides integrated access to curated medical databases and analytics for evidence exploration and de- cision support.

3.1. PICOS Compliance Detection Throughout this section, the Bi-LSTM model serves as a legacy base- line representative of traditional sequence-based screening approaches, while Kernel denotes the domain-adapted transformer model developed for scalable and high-fidelity PICOS classification.

17

In the NCD setting, Kernel was evaluated on a gold-standard set of 284 expert-labeled inclusion and exclusion decisions. Using its ternary output space (include, exclude, maybe), predictions were compared with both hu- man annotations and a larger instruction-tuned LLM prompted with iden- tical eligibility criteria. Kernel and the prompted LLM each achieved 95% agreement with expert judgments, and three-way concordance among Ker- nel, the LLM, and the human assessor reached 91%. Agreement beyond chance was moderate, with Cohen’s Kappa of 0.70 for Kernel versus human annotations and 0.65 for the LLM versus human annotations. Comparable or slightly higher agreement levels were observed in the Dementia–Sport cor- pus. Most disagreements were concentrated in abstracts with underspecified PICOS elements, where experts themselves expressed uncertainty, indicating that discordance primarily reflected borderline eligibility rather than system- atic model error.

On the Dementia–Sport dataset, the Bi-LSTM baseline achieved an accu- racy of 87% for identifying PICOS-compliant abstracts. While substantially less expressive than transformer-based models, this performance illustrates the utility of automated screening for reducing downstream review burden by filtering clearly non-compliant studies early in the pipeline.

Overall, machine–human discord was largely attributable to missing or weakly articulated PICOS elements rather than definitional conflicts. In such cases, both automated models and experts tended to express uncer- tainty, underscoring the intrinsic difficulty of screening poorly reported ab- stracts. These findings indicate that Kernel closely mirrors expert reason- ing in information-sparse scenarios while providing consistent, explainable screening decisions.

3.1.1. Study Design Classification in Dementia–Sport We further evaluated study design classification on the Dementia–Sport corpus by benchmarking Kernel against the Cochrane Study Design clas- sifier [39], an SVM-based model trained on a large biomedical corpus. To ensure a fair comparison, both systems operated exclusively on titles and abstracts. Expert annotations from a gold-standard set of 100 studies served as the reference standard.

3.1.2. Cochrane classifier performance Applied to the 100-study benchmark, the Cochrane classifier achieved perfect sensitivity (100%) for identifying randomized controlled trials (RCTs)

18

but low specificity (42%). This imbalance resulted from 26 false positives, indicating a tendency to overclassify studies as RCTs when experts judged them to be non-randomized.

3.1.3. Kernel performance Kernel was evaluated using title–abstract predictions across several domain- adapted training configurations. The deployed configuration achieved perfect sensitivity and specificity on the expert-annotated benchmark. While both Kernel and the Cochrane classifier rely on NLP-based screening, their train- ing strategies differ substantially: the Cochrane model reflects heterogeneous biomedical data, whereas Kernel is explicitly adapted to the Dementia–Sport domain. This domain adaptation appears critical for resolving ambiguous study design cues in abstracts and reducing false-positive RCT classifica- tions.

3.1.4. Error analysis and comparative insights Detailed error analysis showed that all 26 false positives produced by the Cochrane classifier corresponded to maybe judgments in both expert annota- tions and Kernel’s ternary output (true, false, maybe). In these borderline cases, Kernel’s explanations consistently highlighted textual cues suggestive of randomization, such as implied allocation or trial language, without ex- plicit confirmation. The Cochrane model tended to overgeneralize these sig- nals into binary positive predictions, whereas the Kernel preserved calibrated uncertainty. This contrast highlights the advantages of domain-specific fine- tuning and explainable ternary classification for screening nuanced clinical literature such as Dementia–Sport.

A separate validation on 164 references further assessed study design clas- sification performance. Table 1 summarizes both the confusion matrix counts and the derived evaluation metrics.

Together, these results demonstrate the system’s ability to rapidly prior- itize methodologically rigorous studies during screening, thereby improving the quality and efficiency of downstream synthesis. Although zero-shot and instruction-tuned large language models can be applied to PICOS screening, we do not adopt them as primary baselines due to higher computational cost, reduced determinism, and limited transparency at scale. In contrast, Kernel provides stable, explainable predictions with calibrated uncertainty, making it well-suited for integration into automated and auditable evidence-synthesis pipelines.

19


> **Table 1: Study design classification performance, including confusion matrix counts and**

> derived evaluation metrics.

Category TP FP TN FN

Confusion matrix 74 7 83 0

Metric Precision Recall Specificity Accuracy

Performance (%) 91.4 100.0 92.2 95.7

3.2. Topic Modeling Outcomes BERTopic clustering revealed coherent thematic structure across the cor- pora, enabling identification of high-density research areas, thematic overlap, and potential evidence gaps. Beyond summary statistics and top terms, mul- tiple visualizations were generated to examine topic prevalence and temporal evolution. An illustrative summary of all discovered topic labels and their high-frequency term representations is provided in Appendix Appendix C (Table C.5).


> **Figure 6 presents a heatmap of document counts by topic and publication**

> year (2010–2024), illustrating temporal variation in research intensity across
topics. Higher color intensity denotes greater publication volume, highlight-
ing periods of increased activity and topic-specific concentration over time.


> **Figure 6: Heatmap of document counts by topic (y-axis) and publication year (x-axis).**

> Higher intensity indicates greater publication density.


> **Figure 7 presents a representative word cloud highlighting high-frequency**

20

terms within a selected topic. Dominant terms such as pubmed, journals, and randomized point to methodological and reporting-oriented themes, provid- ing a concise visual summary of the cluster’s semantic focus.


> **Figure 7: Representative word cloud illustrating frequently occurring terms within a topic**

> cluster.

Key observations.

• Redundancy detection: Repeated short-term cardiovascular out- come studies were identified within specific clusters, prompting closer inspection of potential redundancy and highlighting underexplored long- term neurocardiological effects.

• Temporal dynamics: Publication volume peaked between 2018 and 2022 (Figure 6), consistent with shifts in funding priorities and in- creased emphasis on standardized reporting.

• Analytical granularity: Integrating BERTopic-derived themes with relational metadata enabled fine-grained analysis of dominant interven- tions and outcomes within each topic.

3.3. Performance of RAG versus Non-RAG Generation Domain experts compared retrieval-augmented generation (RAG) with a non-retrieval baseline across a set of medical queries. Both configurations used the same general-purpose large language models accessed via public APIs and identical decoding settings (temperature = 0), isolating the effect of retrieval augmentation.

Responses were evaluated along three criteria: (i) relevance of retrieved evidence, (ii) accuracy and contextual alignment of generated answers, and (iii) adequacy for informing clinical or research decision-making.

Overall, 75% of RAG-generated responses met or exceeded expert expec- tations. Outcome distributions were as follows:

21

• 30% of queries were satisfactorily addressed by both RAG and non- RAG approaches.

• 25% favored RAG, particularly for relationship-centric queries requiring integration of graph-structured evidence.

• 20% favored non-RAG generation, typically for high-level thematic summaries or narrative overviews.

• 25% exposed limitations requiring further optimization, primarily for queries demanding simultaneous integration of PICOS constraints, graph relationships, and topic-level context.

Topic-level representations derived from BERTopic contributed to im- proved query formulation and retrieval effectiveness. High-salience terms from dominant clusters were used to refine semantic constraints, enabling retrieval of more contextually relevant evidence and supporting more precise downstream synthesis.

3.3.1. Document relevance and hallucination prevention The LangGraph-based orchestration effectively reduced off-target refer- ences and unsupported content by enforcing retrieval-first generation with passage-level attribution. Mapping retrieved evidence directly to user queries substantially limited hallucinations commonly observed in standalone LLM outputs, thereby improving the reliability and utility of generated responses (Figure 3).

3.4. Business Intelligence Dashboard The dashboard provides interactive access to the curated medical databases through flexible querying and filtering. Users can filter records by biblio- graphic metadata, topic-model-derived semantic attributes, and PICOS com- pliance flags generated by Kernel. Topic-derived terms function as effective surrogates for controlled vocabularies, complementing traditional indexing. This integration of structured metadata and computational annotations en- ables efficient exploration of evidence landscapes, identification of gaps, and informed decision-making in scoping review workflows (Figure 5).

22


## 4. Discussion

Despite substantial advances in natural language processing and clinical informatics, research waste remains pervasive due to suboptimal data cura- tion, incomplete reporting, and manual review workflows that struggle to keep pace with rapidly expanding literatures [4, 51, 36]. The NLP pipeline and conversational recommender system (CRS) presented in this study aim to address these limitations by automating key components of knowledge syn- thesis while preserving expert oversight [31, 42, 15, 41]. Our results demon- strate a coherent alignment between core NLP tasks and the sequential stages of evidence synthesis, illustrating how automation can be integrated across the research lifecycle without compromising methodological rigor.

The workflow begins with a scalable title–abstract screening, where domain- adapted classifiers identify candidate studies from large corpora [19]. Only records meeting the inclusion criteria are propagated into structured down- stream representations, including relational databases, knowledge graphs, and chunked vector indexes. This design ensures that subsequent analyses operate exclusively on qualified evidence, reducing noise and downstream inefficiencies. Curated evidence is then made accessible through two comple- mentary interfaces: an interactive dashboard for structured exploration and analytics, and conversational recommender systems tailored to dementia– sport and non-communicable disease (NCD) use cases. Although optimized for these domains, the architecture is inherently generalizable and applicable to other specialties confronting large and heterogeneous evidence bases. Ac- cordingly, the empirical findings should be interpreted as a proof-of-concept demonstrating feasibility, interpretability, and workflow integration rather than as definitive estimates of research waste prevalence.

4.1. Automatic Classification and PICOS Compliance Reliable evidence synthesis depends on the selective inclusion of studies that meet PICOS criteria and adhere to robust methodological designs, such as randomized controlled trials and high-quality systematic reviews [9, 8]. In this context, the Bi-LSTM model provided a stable baseline for abstract-level PICOS screening, enabling early exclusion of low-quality or irrelevant stud- ies and reducing wasted effort in later review stages [20]. Building on this baseline, our hierarchical classification strategy further prioritized method- ologically rigorous designs within thematically relevant literature.

23

Title–abstract screening was implemented using an iterative human-in- the-loop framework in which expert judgment served as both supervisory signal and interpretive reference. Domain experts defined explicit inclusion and exclusion criteria for each PICOS dimension and provided approximately 250 gold-standard annotations. These annotations informed both fine-tuning of transformer-based models and prompt design for instruction-tuned LLMs, yielding ternary screening outputs (include, exclude, maybe) that explicitly represent uncertainty.

Disagreements between model predictions and expert annotations were treated not as model failures but as informative signals for refinement. It- erative cycles of feedback, re-annotation, and validation revealed previously implicit or underspecified contextual factors, leading to progressive clarifi- cation of PICOS definitions and eligibility criteria. This calibration process continued until screening performance exceeded 95% sensitivity and speci- ficity relative to expert judgments, at which point the model was deemed sufficiently reliable for large-scale screening. Throughout, confidence scores and local and global explanations accompanied each prediction, supporting transparency and expert trust.

Error analysis indicated that most disagreements stemmed from nuanced semantic ambiguities rather than systematic misclassification. Explanatory signals frequently highlighted incomplete reporting of PICOS elements or studies whose primary focus fell outside the intended scope, such as method- ological discussions of randomization, reporting standards, early trial termi- nation, recruitment strategies, or trial registration practices. Other cases involved partial PICOS fulfillment, including missing comparator definitions or outcome specifications, prompting refinement of exclusion criteria through expert deliberation. Simulation-based economic models and survey studies were ultimately excluded following consultation with NCD experts, illus- trating how human-machine collaboration not only improves classification accuracy but also sharpens conceptual boundaries in knowledge synthesis.

4.2. Topic Modeling and Global Explainability By applying BERTopic to cluster semantically related studies (Section 3.2), the system provides a mechanism for identifying redundancy and opportu- nities for methodological consolidation [18, 36]. High-frequency terms and dominant themes within clusters reveal repeated lines of investigation, en- abling editors, reviewers, and funding bodies to distinguish between incre- mental repetition and genuinely novel contributions. In the dementia–sport

24

and NCD domains, such signals can help redirect effort toward underex- plored questions, including biomarker discovery, therapeutic stratification, and improved patient screening strategies.

4.3. Dynamic Integration of a Live Database A fundamental limitation of conventional systematic reviews is the de- lay between publication and incorporation of new evidence. The proposed platform addresses this limitation through a continuously updated, living database architecture, ensuring that synthesis outputs reflect near real-time changes in the literature [23, 17, 42]. This capability is particularly relevant for time-sensitive clinical and policy decisions, such as those involving acute cardiovascular conditions or neuroprotective interventions, where reliance on outdated evidence can substantially compromise downstream impact.

4.4. Enhanced Accessibility via Conversational AI Conversational access to the evidence base substantially lowers barriers for non-technical stakeholders, including clinicians, allied health profession- als, and policymakers[29]. By allowing users to pose domain-specific ques- tions in natural language, the system reduces dependence on advanced data analytics expertise and narrows the gap between evidence production and ap- plication. The integration of retrieval-augmented generation (RAG) with an interactive dashboard further mitigates common limitations of standalone language models, including hallucination and weak attribution [14], while enabling organizations to monitor compliance trends and identify opportu- nities for targeted reporting guidance or policy intervention. Representative example questions illustrating the scope of PICOS-aligned queries supported by the CRS in the Dementia–Sport and NCD domains are provided in Ap- pendix Appendix D.

Within the AI co-scientist conversational recommender system (CRS), RAG is complemented by executable tools, including a schema-aware SQL query generator. The CRS dynamically selects tools based on inferred user intent, allowing seamless transitions between semantic retrieval and struc- tured database interrogation when appropriate.

4.4.1. SQL Generator Queries implying aggregation or enumeration, such as those beginning with phrases like “how many,” consistently trigger the SQL generator, whereas descriptive or exploratory questions are routed through semantic retrieval

25

over the document corpus. Early brittleness related to identifier case sensi- tivity was addressed by introducing schema-driven identifier normalization and fuzzy resolution before execution. Following these refinements, the CRS reliably answered quantitative queries, such as counts of abstracts containing specific terms, as well as analytical questions concerning topic prevalence. In each case, generated responses were directly verifiable against the underly- ing database, demonstrating the feasibility and reliability of tool-augmented conversational querying for structured evidence exploration.

Beyond structured queries, the CRS also supports open-ended seman- tic questioning over full texts, enabling clinically oriented information needs to be addressed through evidence-grounded synthesis. For example, queries regarding treatment options for advanced malignancies triggered multi-step reasoning workflows coordinated via LangGraph, integrating retrieval, syn- thesis, and attribution before response generation. Answers were accompa- nied by explicit source citations drawn from the corpus, allowing users to inspect supporting evidence and trace the reasoning process. This combina- tion of transparency, grounded generation, and intuitive interaction supports expert confidence and facilitates interactive exploration of both conclusions and the computational processes that produced them.

4.4.2. Waste and PICOS Because the conversational recommender system (CRS) has structured access to curated metadata, it can integrate bibliographic attributes such as authorship, publication date, and PICOS compliance flags with higher-level semantic reasoning over full-text content [20, 16, 13, 48]. This capability enables the CRS to answer queries that combine conceptual questions about PICOS with formal research standards. For example, when asked to con- trast PICO compliance with CONSORT and SPIRIT, the system correctly articulated their complementary roles: PICO structures research questions, SPIRIT governs trial protocol design and documentation, and CONSORT focuses on reporting completed trials [38, 5, 30]. In another multi-stage query, the CRS identified and summarized the population of a specific neuro- oncology RCT corpus as patients enrolled in non-surgical randomized trials conducted between 2005 and 2014, contextualizing this information within a PICOS framework and attributing it to the appropriate sources. Across such interactions, explicit source attributions accompanied evidence-grounded re- sponses, supporting transparency and expert verification.

The CRS also demonstrated robust performance on concept-level ques-

26

tions related to research waste. Queries addressing definitions, causes, ethical implications, and downstream harms of research waste yielded explanations consistent with established meta-research and research governance literature. Crucially, these responses were not generated in isolation; each was accom- panied by source citations drawn from the indexed corpus, allowing users to trace claims back to the primary literature. When asked how researchers can determine whether a question has already been answered, the CRS ar- ticulated evidence-based strategies such as consulting systematic and scop- ing reviews, examining trial registries, and assessing overlap in PICOS ele- ments [33, 22, 8, 9], again grounding recommendations in retrieved sources. Together, these results indicate that the CRS can function as a reliable AI co-scientist for reflective inquiry into research waste and responsible research practice.

4.4.3. Aggregated Semantics with Reasoning A key limitation identified in the current CRS arises when queries require both semantic interpretation and explicit quantitative reasoning over meta- data. In one instance, the CRS correctly addressed a conceptual question linking publication delay to null or unfavorable findings, consistent with prior meta-research. However, follow-up computational queries asking whether publication delays exceeded specific thresholds were less reliable, particularly when negative results were returned without consistent source attribution. This limitation highlights an incomplete integration between semantic rea- soning, temporal metadata extraction, and verifiable computation.

To mitigate this issue, we introduce an explicit Negative Grounding pro- tocol for null results. When no records satisfy a query’s constraints, the CRS returns a bounded negative response together with the exact search param- eters applied, including corpus scope, temporal window, study design filters, and metadata fields queried. Treating null results as first-class, auditable out- puts allows users to distinguish true absence of evidence from uncertainty, incomplete ingestion, or reasoning error.

Finally, the CRS is best understood as an assistive AI co-scientist rather than an autonomous research analyst. Its effectiveness depends on alignment between user expectations and the system’s optimized competency space. Light user orientation improves performance, particularly for aggregation queries that benefit from explicit metadata framing or multi-stage decompo- sition. Practical constraints were also observed: concise attribution lists are most effective for disease-specific queries, with iterative follow-up support-

27

ing deeper exploration. Some requests, such as analyses over intentionally un-ingested references or complex qualitative synthesis, fall outside the cur- rent scope. Nevertheless, when engaged through iterative dialogue, the CRS demonstrated strong performance on semantically complex inquiries related to PICOS formalization and research waste, reinforcing its role as a collab- orative, human-in-the-loop support tool for knowledge synthesis rather than a substitute for expert judgment.

4.5. Business Intelligence Insights Dashboard-enabled filtering by individual PICOS elements revealed sub- stantial structural gaps in the Dementia–Sport literature, providing an inter- pretable view of how research waste manifests at the levels of study design and reporting. By enabling isolation and quantification of compliance with each PICOS dimension, the system supports fine-grained analysis of where evidence production diverges from standards required for meaningful synthe- sis.

Population (P) compliance was observed in only 28% of publications. Model explanations and expert review consistently identified insufficient pop- ulation descriptions as the primary limitation, including omissions of demo- graphic characteristics, clinical profiles, and care settings. Population re- porting was frequently superficial, with limited adherence to CONSORT- or POPCORN-aligned expectations, substantially constraining interpretability and downstream aggregation.

Compliance was lowest for Intervention (I) and Comparator (C), at 15% and 9%, respectively. Error analysis and expert review identified these as the most semantically challenging PICOS elements to operationalize jointly in the NCD context, motivating adoption of the combined PIOS represen- tation for screening and downstream querying. Intervention non-compliance primarily reflected insufficient methodological specification, including miss- ing details on treatment type, dosage, duration, or delivery, while Compara- tor definitions were often implicit or absent, relying on conceptual discussion rather than explicit contrasts with placebo, standard care, or alternative interventions.

Outcome (O) compliance was comparatively higher at 47%, but remained limited by insufficient clarity. Although outcome-related concepts were of- ten mentioned, fewer studies specified primary or secondary outcomes or described assessment procedures. Non-compliance commonly reflected proxy

28


## discussions, such as measurement frameworks or bias considerations, rather

than explicit reporting of clinical endpoints.

Study Design (S) exhibited the highest compliance rate at 89%. Nonethe- less, deficiencies persisted, including references to randomized or controlled designs without explicit classification (e.g., RCT, cohort), and publications focused on reporting guidelines, statistical methods, or protocol development rather than original clinical investigations.

When considering joint PICOS compliance, only 4% of the Dementia– Sport corpus satisfied all five criteria simultaneously. The dashboard’s capac- ity to surface non-compliance at both granular and aggregate levels directly informed inclusion and exclusion decisions, demonstrating how PICOS-aware analytics expose structural inefficiencies in the evidence base. These findings indicate that research waste arises from cumulative omissions across multiple PICOS dimensions rather than isolated reporting failures, underscoring the value of explainable NLP for transparent, data-driven knowledge synthesis.

Temporal analysis further revealed a strong correlation between publi- cation volume and PICOS non-compliance since 2010. Although data from 2024–2025 likely underestimate true trends due to ongoing publication pipelines at the time of corpus extraction, sustained increases in both publication vol- ume and non-compliance were evident through 2023. A temporary reduction around 2019–2021 did not reflect improved reporting quality but rather paral- lel declines in output and non-compliance, plausibly associated with systemic disruptions during the COVID-19 pandemic (Fig. 8).

Topic trends stratified by PICOS compliance illustrate how dashboard filters can interrogate reporting practices longitudinally. Non-compliant pub- lications clustered around themes characterized by insufficient specificity in core descriptors, including population definitions, intervention details, com- parator descriptions, outcome specification, and explicit study design label- ing. Topic-level inspection further identified publications that appeared com- pliant at the abstract level but primarily addressed reporting guidelines or methodological frameworks upon closer semantic analysis, rather than re- porting original clinical evidence. Aligning topic semantics with PICOS- based filtering thus enables nuanced differentiation between substantive clin- ical studies and meta-level discourse, enhancing transparency in inclusion decisions and identification of research waste.

29


> **Figure 8: Trends in PICOS non-compliance and publication volume in the Dementia–**

> Sport corpus by publication year.


## 5. Limitations and Future Directions

Despite promising results, several limitations warrant consideration. First, model performance is sensitive to the quality and representativeness of train- ing data, and underrepresented subdomains within the Brain–Heart Intercon- nectome may experience reduced accuracy. Second, while continuous updates improve currency, verification of newly ingested evidence requires structured validation pipelines or sustained human oversight. Third, large-scale deploy- ment will require robust interoperability with institutional systems, raising challenges related to privacy, governance, and standardization. Finally, the platform’s effectiveness depends on user adoption; formal usability studies and iterative design refinement will be essential to maximize real-world im- pact.

Future work will focus on more advanced learning strategies, deeper inte- gration with clinical and hospital informatics infrastructures, and systematic user-centered evaluations to optimize operational deployment.

30


## 6. Ethics, Privacy, and Security

Ethical, privacy, and security considerations were integral to the system design. All analyses were restricted to openly accessible publications, and no large language models were retrained or fine-tuned on proprietary con- tent. Where required, generation was performed using secured local instances hosted within protected institutional computing environments, strictly for proof-of-concept evaluation. No document content was redistributed or ex- posed beyond controlled settings. The platform was developed solely to as- sess methodological feasibility, without compromising confidentiality, data governance obligations, or intellectual property rights.


## 7. Conclusion

We presented the design and evaluation of an AI co-scientist that oper- ates alongside human experts to mitigate research waste in multiple medical contexts, with a focus on Dementia–Sport, and non-communicable diseases. Grounded in scoping review methodology, the system supports an end-to- end evidence synthesis workflow spanning title–abstract screening, full-text processing, structured extraction, and evidence-grounded synthesis, guided by explicit PICOS formalization and retrieval-first generation.

In DS and NCD evidence synthesis, PICOS serves as a practical mech- anism for reducing research waste by imposing structure across the review lifecycle. Explicit definition of Population, Intervention, Comparator, Out- comes, and Study design enables efficient search strategies and eligibility criteria, reduces processing of irrelevant or redundant studies, and directly guides downstream extraction and synthesis. Consistent application of PI- COS further promotes transparency, reproducibility, and cross-study compa- rability in heterogeneous evidence bases.

The proposed platform integrates interoperable NLP components, includ- ing ingestion and chunking pipelines, relational and graph-based representa- tions, metadata-aware semantic retrieval, and expert-facing dashboards cou- pled with a conversational recommender system. Domain-adapted trans- former models provide explainable PICOS classification, while live database connectivity and hybrid retrieval support auditable full-text interrogation and synthesis.

Overall, the results indicate that combining explainable screening, struc- tured data curation, and tool-augmented conversational access can substan- tially reduce manual review burden while preserving expert oversight through

31

validation and iterative refinement. Although evaluated in the Dementia– Sport and NCD domains, the architecture is domain-agnostic and readily transferable to other clinical and research settings to support scalable, trans- parent, and continuously updatable evidence synthesis.

Declarations

Acknowledgement

We gratefully acknowledge the contributions of Prof. Doug Manuel and Prof. David Moher, whose scientific leadership and guidance were instrumen- tal throughout this work. We also thank their respective teams, including by not limited to Carol Smith, Alexandra Bodnaruc, Osmo Ramakko, and Mike Yeates, for expert annotation, rigorous testing, and constructive collabora- tion across all phases of the study. This research was supported by funding from the Brain-Heart Interconnectome and the Canadian Institute of Health Research.

CRediT authorship contribution statement

Arya Rahgozar and Pouria Mortezaagha designed the model, developed the computational framework, and implemented the pipeline. They both performed the experiments, statistical analyses, and wrote the manuscript. Both authors discussed the results and contributed to the final manuscript.

Data availability

The full-text articles analyzed were obtained from open-access sources. Derived datasets, intermediate outputs, and analysis scripts are available from the corresponding author upon reasonable request, subject to publisher licensing restrictions.

Declaration of competing interest

The authors declare that they have no known competing financial inter- ests or personal relationships that could have appeared to influence the work reported in this paper.

32


## References

[1] Bamberger, M., Rao, V., Woolcock, M., 2010. Using mixed methods

in monitoring and evaluation : Experiences from international develop- ment. World Bank.

[2] Begley, C.G., Ellis, L.M., 2012. Drug development: Raise standards for

preclinical cancer research. Nature 483, 531–533.

[3] Cai, Z., Gao, H., Wu, M., Li, J., Liu, C., 2024. Physiologic network-

based brain-heart interaction quantification during visual emotional elic- itation. IEEE Trans. Neural Syst. Rehabil. Eng. 32, 2482–2491.

[4] Chalmers, I., Glasziou, P., 2009. Avoidable waste in the production and

reporting of research evidence. The Lancet 374, 86–89.

[5] Chan, A.W., Tetzlaff, J.M., Altman, D.G., Laupacis, A., Gøtzsche, P.C.,

Krleža-Jerić, K., Hróbjartsson, A., Mann, H., Dickersin, K., Berlin, J.A., Doré, C.J., Parulekar, W.R., Summerskill, W.S.M., Groves, T., Schulz, K.F., Sox, H.C., Rockhold, F.W., Rennie, D., Moher, D., 2013. SPIRIT 2013 statement: defining standard protocol items for clinical trials. Ann. Intern. Med. 158, 200–207.

[6] Chapman, S.J., Shelton, B., Mahmood, H., Fitzgerald, J.E., Harrison,

E.M., Bhangu, A., 2019. Discontinuation and non-publication of sur- gical randomised controlled trials: Observational study. BMJ Open 9, e032019.

[7] Cox, J., Giorgi, S., Sharp, V., Strange, K., Wilson, D.C., Blakey, N.,

2010. Household waste prevention–a review of evidence. Waste Manag. Res. 28, 193–219.

[8] Cumpston, M.S., McKenzie, J.E., Ryan, R., Thomas, J., Brennan, S.E.,

2023. Critical elements of synthesis questions are incompletely reported: survey of systematic reviews of intervention effects. J. Clin. Epidemiol. 163, 79–91.

[9] Cumpston, M.S., McKenzie, J.E., Thomas, J., Brennan, S.E., 2020. The

use of ’PICO for synthesis’ and methods for synthesis without meta- analysis: protocol for a survey of current practice in systematic reviews of health interventions. F1000Res. 9, 678.

33

[10] Dal Santo, T., Rice, D.B., Amiri, L.S.N., Tasleem, A., Li, K., Boruff,

J.T., Geoffroy, M.C.B., Benedetti, A., Thombs, B., 2022a. Research waste from poor reporting of core methods and results and redundancy in studies of reporting guideline adherence: a meta-research review. Empty.

[11] Dal Santo, T.S., Rice, D.B., Amiri, L., Tasleem, A., Li, K., Boruff, J.,

Geoffroy, M., Benedetti, A., Thombs, B.D., 2022b. Research waste from poor reporting of core methods and results and redundancy in studies of reporting guideline adherence: A meta-research review. medRxiv doi:10.1101/2022.12.19.22283669.

[12] Deking, S., Liman, J., 2021. Interactions between the brain and heart.

Nervenarzt 92, 977–985.

[13] Dhrangadhariya, A., Manzo, G., Müller, H., 2024. Pico to picos: Weak

supervision to extend datasets with new labels, in: Studies in Health Technology and Informatics, pp. 166–177. doi:10.3233/shti240775.

[14] Fan, W., Ding, Y., Ning, L., Wang, S., Li, H., Yin, D., Chua, T.S., Li,

Q., 2024. A survey on rag meeting llms: Towards retrieval-augmented large language models. URL: https://arxiv.org/abs/2405.06211, arXiv:2405.06211.

[15] Ge, L., Agrawal, R., Singer, M., Kannapiran, P., De Castro Molina,

J.A., Teow, K.L., Yap, C.W., Abisheganaden, J.A., 2024. Leveraging artificial intelligence to enhance systematic reviews in health research: advanced tools and challenges. Syst. Rev. 13, 269.

[16] Ghosh, S., Thomas, R., Wang, Y., 2024. Alpapico: Advancing pico extraction for systematic reviews in low-resource settings. AI in Medicine 78, 203–212.

[17] Górska, A., Tacconelli, E., 2024. Towards autonomous living meta- analyses: A framework for automation of systematic review and meta- analyses. Stud. Health Technol. Inform. 316, 378–382.

[18] Grootendorst, M., 2022. Bertopic: Neural topic modeling with a class-

based tf-idf procedure. arXiv preprint arXiv:2203.05794 .

34

[19] Idnay, B., Dreisbach, C., Weng, C., Schnall, R., 2021. A systematic re-

view on natural language processing systems for eligibility prescreening in clinical research. J. Am. Med. Inform. Assoc. 29, 197–206.

[20] Jin, D., Szolovits, P., 2018. PICO element detection in medical text via

long short-term memory neural networks, in: Demner-Fushman, D., Co- hen, K.B., Ananiadou, S., Tsujii, J. (Eds.), Proceedings of the BioNLP 2018 workshop, Association for Computational Linguistics, Melbourne, Australia. pp. 67–75. URL: https://aclanthology.org/W18-2308/, doi:10.18653/v1/W18-2308.

[21] K. Rostam, Z.R., Kertész, G., 2025. Advances in pre-trained language

models for domain-specific text classification: A systematic review. ACM Transactions on Intelligent Systems and Technology 16, 1–41. URL: http://dx.doi.org/10.1145/3763002, doi:10.1145/3763002.

[22] Khalil, H., Jia, R., Moraes, E.B., Munn, Z., Alexander, L., Peters,

M.D.J., Asran, A., Godfrey, C.M., Tricco, A.C., Pollock, D., Evans, C., 2025. Scoping reviews and their role in identifying research priorities. J. Clin. Epidemiol. 181, 111712.

[23] Legate, A., Nimon, K., Noblin, A., 2024. (semi)automated approaches

to data extraction for systematic reviews and meta-analyses in social sciences: A living review. F1000Res. 13, 664.

[24] Lu, L., Sun, J., Ren, X., Ma, X., Guo, Q., Wang, X., 2021. Reporting

quality and research waste in gastric cancer randomized controlled trials. Annals of Surgical Oncology 28, 2991–3000.

[25] Ma, S., Pan, P., Xu, G., Yang, W., Li, D., Shen, T., Wang, Z., Cai,

Y., Yao, M., 2024. The application of the “PICO” teaching model in clinical research course for medical students. Global Medical Education 1, 63–71.

[26] Marshall, I.J., Kuiper, J., Wallace, B.C., 2016. RobotReviewer: evalu-

ation of a system for automatically assessing bias in clinical trials. J. Am. Med. Inform. Assoc. 23, 193–201.

[27] Mavergames, C., Oliver, S., Becker, L., 2013. Systematic reviews as

an interface to the web of (trial) data: using pico as an ontology for

35

knowledge synthesis in evidence-based healthcare research, in: SePub- lica, pp. 79–91. URL: https://api.semanticscholar.org/CorpusID: 8014463.

[28] Menezes, M.C.S., Hoffmann, A.F., Tan, A.L.M., Nalbandyan, M.,

Omenn, G.S., Mazzotti, D.R., Hernández-Arango, A., Visweswaran, S., Venkatesh, S., Mandl, K.D., Bourgeois, F.T., Lee, J.W.K., Makmur, A., Hanauer, D.A., Semanik, M.G., Kerivan, L.T., Hill, T., Forero, J., Restrepo, C., Vigna, M., Ceriana, P., Abu-El-Rub, N., Avillach, P., Bel- lazzi, R., Callaci, T., Gutiérrez-Sacristán, A., Malovini, A., Mathew, J.P., Morris, M., Murthy, V.L., Buonocore, T.M., Parimbelli, E., Patel, L.P., Sáez, C., Samayamuthu, M.J., Thompson, J.A., Tibollo, V., Xia, Z., Kohane, I.S., Consortium for Clinical Characterization of COVID- 19 by Electronic Health Records, 2025. The potential of generative pre- trained transformer 4 (GPT-4) to analyse medical notes in three different languages: a retrospective model-evaluation study. Lancet Digit. Health 7, e35–e43.

[29] Mikriukov, A., Senokosov, A., Succi, G., Tormasov, A., Plaksin, Y.,

Trofimova, E., Sitnikov, V., 2025. AI tools for automating systematic literature reviews, in: Proceedings of the 2025 International Conference on Software Engineering and Computer Applications, ACM, New York, NY, USA. pp. 25–30.

[30] Moher, D., F. Schulz, K., Altman, D., Almanza Muñoz, J.d.J.,

De Roux Reyes, S., 2024. La declaración CONSORT: Recomendaciones revisadas para mejorar la calidad de los informes de ensayos aleatoriza- dos de grupos paralelos. Rev. Sanid. Milit. 56.

[31] Ofori-Boateng, R., Aceves-Martins, M., Wiratunga, N., Moreno-Garcia,

C.F., 2024a. Towards the automation of systematic reviews using nat- ural language processing, machine learning, and deep learning: a com- prehensive review. Artif. Intell. Rev. 57.

[32] Ofori-Boateng, R., Aceves-Martins, M., Wiratunga, N., Moreno-Garcia,

C.F., 2024b. Towards the automation of systematic reviews using nat- ural language processing, machine learning, and deep learning: a com- prehensive review. Artif. Intell. Rev. 57.

36

[33] Page, M.J., McKenzie, J.E., Bossuyt, P.M., Boutron, I., Hoffmann,

T.C., Mulrow, C.D., Shamseer, L., Tetzlaff, J.M., Akl, E.A., Brennan, S.E., Chou, R., Glanville, J., Grimshaw, J.M., Hróbjartsson, A., Lalu, M.M., Li, T., Loder, E.W., Mayo-Wilson, E., McDonald, S., McGuin- ness, L.A., Stewart, L.A., Thomas, J., Tricco, A.C., Welch, V.A., Whit- ing, P., Moher, D., 2021. The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ 372, n71.

[34] Peng, B., Zhu, Y., Liu, Y., Bo, X., Shi, H., Hong, C., Zhang, Y., Tang,

S., 2024. Graph retrieval-augmented generation: A survey. URL: https: //arxiv.org/abs/2408.08921, arXiv:2408.08921.

[35] Petri, D., 2023. Evidence synthesis 2.0: how artificial intelligence is making systematic reviews more efficient. Recenti Prog. Med. 114, 359– 361.

[36] Rosengaard, L.O., Andersen, M.Z., Rosenberg, J., Fonnes, S., 2024.

Several methods for assessing research waste in reviews with a systematic search: a scoping review. PeerJ 12, e18466.

[37] Sabor, N., Mohammed, H., Li, Z., Wang, G., 2022. BHI-net: Brain-heart

interaction-based deep architectures for epileptic seizures and firing lo- cation detection. IEEE Trans. Neural Syst. Rehabil. Eng. 30, 1576–1588.

[38] Schulz, K.F., Altman, D.G., Moher, D., CONSORT Group, 2010. CON-

SORT 2010 statement: updated guidelines for reporting parallel group randomized trials. Ann. Intern. Med. 152, 726–732.

[39] Thomas, J., McDonald, S., Noel-Storr, A., Shemilt, I., Elliott, J.,

Mavergames, C., Marshall, I.J., 2021. Machine learning reduced work- load with minimal risk of missing studies: development and evaluation of a randomized controlled trial classifier for cochrane reviews. J. Clin. Epidemiol. 133, 140–151.

[40] Toledo, R.F., Atlee, J.M., Xiong, R.M., Liu, M., 2024. (neo4j) browser:

Visualizing variable-aware analysis results, in: Proceedings of the 2024 IEEE/ACM 46th International Conference on Software Engineering: Companion Proceedings, ACM, New York, NY, USA. pp. 69–73.

[41] Tomczyk, P., Brüggemann, P., Vrontis, D., 2024. AI meets academia:

transforming systematic literature reviews. EuroMed J. Bus. .

37

[42] Tóth, B., Berek, L., Gulácsi, L., Péntek, M., Zrubka, Z., 2024. Automa-

tion of systematic reviews of biomedical literature: a scoping review of studies indexed in PubMed. Syst. Rev. 13, 174.

[43] Tsou, A.Y., Treadwell, J.R., Erinoff, E., Schoelles, K., 2020. Machine

learning for screening prioritization in systematic reviews: comparative performance of abstrackr and EPPI-Reviewer. Syst. Rev. 9, 73.

[44] Vincenzo Catrambone, G.V., 2023. Complex brain-heart mapping in

mental and physical stress. IEEE J. Transl. Eng. Health Med. 11, 495– 504.

[45] Westmore, M., Bowdery, M., Cody, A., Dunham, K., Goble, D., van der

Linden, B., Whitlock, E., Williams, E., Lujan Barroso, C., 2023. How an international research funder’s forum developed guiding principles to ensure value and reduce waste in research. F1000Res. 12, 310.

[46] Yordanov, Y., Dechartres, A., Atal, I., Tran, V.T., Boutron, I., Crequit,

P., Ravaud, P., 2018. Avoidable waste of research related to outcome planning and reporting in clinical trials. BMC Med. 16, 87.

[47] Zacho, K.O., Mosgaard, M.A., 2016. Understanding the role of waste

prevention in local waste management: A literature review. Waste Manag. Res. 34, 980–994.

[48] Zhang, L., Tian, W., Zheng, Y., Jian, Y., 2024a. Enhancing PICOS

information extraction with UIE and ERNIE-health, in: Communica- tions in Computer and Information Science. Springer Nature Singapore, Singapore. Communications in Computer and Information Science, pp. 186–194.

[49] Zhang, Q., Qu, J., Zhao, Q., Xue, F., 2024b. Task-specific model allo-

cation medical papers PICOS information extraction, in: Communica- tions in Computer and Information Science. Springer Nature Singapore, Singapore. Communications in Computer and Information Science, pp. 166–177.

[50] Zhang, Y., Yang, R., Jiao, S., Kang, S., Han, J., 2025. Scientific paper re-

trieval with LLM-guided semantic-based ranking, in: Christodoulopou- los, C., Chakraborty, T., Rose, C., Peng, V. (Eds.), Findings of the

38

Association for Computational Linguistics: EMNLP 2025, Associa- tion for Computational Linguistics, Suzhou, China. pp. 2049–2060. URL: https://aclanthology.org/2025.findings-emnlp.108/, doi:10.18653/v1/2025.findings-emnlp.108.

[51] Zheutlin, A.R., Niforatos, J., Stulberg, E., Sussman, J., 2020. Research

waste in randomized clinical trials: A cross-sectional analysis. J. Gen. Intern. Med. 35, 3105–3107.

Appendix A. Eligibility criteria for Dementia–Sport studies


> **Table A.2 summarizes the a priori eligibility criteria used to identify and**

> screen Dementia–Sport studies, specifying inclusion requirements across par-
ticipants, interventions, comparators, outcomes, and study design in accor-
dance with the PICOS framework.

Appendix B. Eligibility criteria for Kernel-based study screening

Tables B.3 and B.4 summarize the inclusion and exclusion criteria ap- plied by the Kernel classifier for automated screening of simulation-based population health studies.

Appendix C. BERTopic Cluster Definitions and Representative Terms


> **Table C.5 provides an illustrative overview of the extracted topics, includ-**

> ing topic labels, high-frequency terms, and representative document group-
ings.

Appendix D. Example CRS Competency Questions Aligned with

PICOS

To preserve privacy and data governance constraints, we do not report verbatim system responses. Instead, we present representative competency questions illustrating the types of evidence-grounded, PICOS-aligned queries the Conversational Recommender System (CRS) is designed to support in the Dementia–Sport and non-communicable disease (NCD) domains.

Together, these example questions illustrate how explicit PICOS formal- ization enables structured querying, explanation, and identification of re- search waste signals without requiring access to protected system outputs.

39


> **Table A.2: Eligibility criteria for Dementia–Sport studies**

Domain Criteria

Type of participants Older adults aged 65 years and above. Participants must be diagnosed with dementia using accepted di- agnostic criteria, including DSM, ICD-10, National In- stitute of Neurological and Communicative Disorders and Stroke (NINCDS), Alzheimer’s Disease and Re- lated Disorders Association (ADRDA), or CERAD-K.

Type of interventions Exercise programs with clearly described characteris- tics, including type, frequency, intensity, duration, and setting. Eligible interventions included any combina- tion of aerobic exercise, strength training, or balance training. Frequency, intensity, and duration were unre- stricted. The intervention setting was not required to be explicitly described.

Types of comparators Controlled trials in which the only systematic difference between groups was the exercise intervention. Com- parator groups included usual care or social contact activities to ensure comparable levels of participant at- tention across groups.

Types of outcomes Primary outcomes: cognition; activities of daily liv- ing; neuropsychiatric symptoms (e.g., agitation, ag- gression); depression; mortality. Secondary outcomes: caregiver burden; quality of life; mortality; healthcare service costs.

Study design Individually randomized or cluster-randomized con- trolled trials (RCTs), including both parallel-group and cross-over designs. For cross-over trials, only data from the first intervention phase before crossover were con- sidered. Excluded designs: systematic reviews (with or with- out meta-analysis), observational studies (e.g., cohort or longitudinal designs), qualitative studies, and other non-randomized study designs.

40


> **Table B.3: Kernel eligibility criteria for simulation-based population health studies: study**

> characteristics and population

Domain Include Exclude

Study character- istics

Studies in which computational simulation modelling is the pri- mary analytical method used to address population health re- search objectives. Eligible ap- proaches include system dynam- ics models; agent-based models; microsimulation and macrosim- ulation; discrete event simula- tion; Markov models and Monte Carlo simulation; life table meth- ods for policy analysis; and com- putational attributable risk mod- els.

Observational or experimental studies without simulation mod- elling. Predictive modelling studies covered by TRIPOD or TRIPOD-AI, unless simu- lation modelling is explicitly used. Methodological or sta- tistical studies without substan- tive population health questions. Meta-analyses without scenario simulation.

Population Studies examining real or gen- eralizable human populations or subpopulations defined by geo- graphic, demographic, or social characteristics with relevance to population health or policy.

Individual-level clinical studies, trial-design simulations, ab- stract or theoretical populations, animal or laboratory studies, education-focused simulations, or individual risk prediction tools.

41


> **Table B.4: Kernel eligibility criteria for simulation-based population health studies: inter-**

> vention and outcomes
Domain
Include
Exclude

Intervention / exposure

Simulation studies evaluating the health impact of exposures, in- terventions, or policies on non- communicable disease outcomes through explicit or implicit sce- nario comparisons.

Methodological studies without applied health scenarios; behav- ioral simulations without NCD relevance; sensitivity or valida- tion exercises without scenario comparison; economic analyses focused primarily on costs.

Outcome Studies reporting outcomes related to WHO-defined non- communicable diseases, includ- ing mortality, life expectancy, YLL, QALYs, DALYs, disease burden, or major NCD risk factors.

Studies focused on non-NCD conditions, intermediate physio- logical outcomes only, or health- care system outcomes without explicit linkage to NCD health impacts.

42


> **Table C.5: Illustrative BERTopic output for all discovered topics, showing topic label**

> (Name) and high-frequency terms (Representation). Topic −1 corresponds to outlier doc-
uments not assigned to a coherent cluster.

Topic Name Representation

0 report_trial_studi_rct {report,trial,studi,rct,data,use,. . . } 1 outcom_trial_regist_regist r

{outcom,trial,regist,registr,primari, . . . } 2 blind_trial_bia_effect {blind,trial,bia,effect,outcom,. . . } 3 harm_report_trial_event {harm,report,trial,event,advers,. . . } 4 qualiti_rct_report_abstra ct

{qualiti,rct,report,abstract,method, . . . } 5 size_sampl_samplsize_calcul {size,sampl,samplsize,calcul,power, . . . } 6 trial_guidelin_item_report {trial,guidelin,item,report,develop, . . . } 7 journal_report_orthodont _rct

{journal,report,orthodont,rct,publis h,. . . } 8 subgroup_trial_analys_sub group

{subgroup,trial,analys,subgroupanal ys,. . . } 9 chines_tcm_report_rct {chines,tcm,report,rct,qualiti,. . . } 10 pro_rct_cancer_report {pro,rct,cancer,report,qualiti,. . . } 11 abstract_report_ci_trial {abstract,report,ci,trial,statist,. . . } 12 recruit_retent_particip_st rategi

{recruit,retent,particip,strategi,. . . } 13 trial_particip_patient_org an

{trial,particip,patient,organ,platfor m,. . . }

43


> **Table D.6: Example CRS competency questions aligned with Population (P)**

> Domain
Representative Questions

Dementia–Sport What populations are most frequently studied (e.g., age group, dementia stage, care setting)? How often are demographic characteristics explicitly re- ported? Which dementia subtypes are most represented in physi- cal activity interventions?

NCD Which NCD populations dominate the corpus (e.g., car- diovascular disease, diabetes, cancer)? How does population reporting vary by NCD subtype and publication year? Are vulnerable or underrepresented populations system- atically included or excluded?


> **Table D.7: Example CRS competency questions aligned with Intervention (I)**

> Domain
Representative Questions

Dementia–Sport What types of sport or physical activity interventions are most commonly evaluated? How often are intervention parameters (intensity, dura- tion, frequency) sufficiently reported? Which interventions are associated with cognitive versus functional outcomes?

NCD Which intervention classes dominate NCD research? Are intervention protocols consistently described across studies? How has intervention complexity evolved over time?

44


> **Table D.8: Representative CRS competency questions aligned with Comparator (C)**

> Domain
Example Questions

Dementia–Sport How frequently do studies include an explicit comparator group? What types of comparators are used (e.g., usual care, placebo, alternative activity)? In studies lacking comparators, what methodological jus- tifications are provided?

NCD How often are standard-of-care comparators used? Are head-to-head intervention comparisons common in specific NCD subdomains? Which NCD areas exhibit the highest rates of missing comparator information?


> **Table D.9: Representative CRS competency questions aligned with Outcome (O)**

> Domain
Example Questions

Dementia–Sport What primary outcomes are most frequently reported (e.g., cognition, mobility, quality of life)? How often are primary and secondary outcomes explicitly distinguished? Are outcome measures standardized across studies?

NCD What outcome categories dominate NCD research (e.g., mortality, biomarkers, functional outcomes)? How frequently are outcomes clearly operationalized and measurable? Which NCD domains show the greatest outcome-reporting heterogeneity?

45


> **Table D.10: Representative CRS competency questions aligned with Study Design (S)**

> Domain
Example Questions

Dementia–Sport What proportion of studies are randomized controlled tri- als? How often is study design explicitly stated versus inferred? Are reporting guidelines (e.g., CONSORT, SPIRIT) ref- erenced?

NCD Which study designs dominate by disease area? Has the proportion of RCTs versus observational studies changed over time? How frequently do studies describe protocols rather than report completed trials?


> **Table D.11: Cross-PICOS and research-waste–focused CRS competency questions**

> Domain
Representative Questions

Dementia–Sport What proportion of studies are fully PICOS compliant? Which PICOS elements most commonly drive exclusion decisions? Are there clusters of studies focused on reporting quality rather than clinical evidence?

NCD Which NCD subdomains exhibit the highest PICOS- related research waste? Are there recurring patterns of partial compliance (e.g., P and I reported, C missing)? How often do studies duplicate existing evidence without extending populations or outcomes?

46


> **Table D.12: High-level CRS reasoning modes used to address different query types**

Reasoning Mode Typical Question Characteristics

Structured querying Counts, proportions, trends, and rankings derived from metadata or PICOS flags. Semantic synthesis Explanatory, interpretive, or narrative questions re- quiring full-text evidence. Hybrid reasoning Queries combining cohort definition with explana- tory justification.

47
