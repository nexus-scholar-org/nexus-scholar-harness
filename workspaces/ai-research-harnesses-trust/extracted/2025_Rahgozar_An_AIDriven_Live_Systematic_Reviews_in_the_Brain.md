---
workspace_id: "SCI-000110"
doi: "10.48550/arxiv.2501.17181"
title: "An AI-Driven Live Systematic Reviews in the Brain-Heart Interconnectome: Minimizing Research Waste and Advancing Evidence Synthesis"
year: 2025
extraction_engine: "pymupdf"
---
# 2025 Rahgozar An AIDriven Live Systematic Reviews in the Brain

AN AI-DRIVEN LIVE SYSTEMATIC REVIEWS IN THE

BRAIN-HEART INTERCONNECTOME: MINIMIZING RESEARCH WASTE AND ADVANCING EVIDENCE

SYNTHESIS

arXiv:2501.17181v1  [cs.AI]  25 Jan 2025

A. Rahgozar1, P. Mortezaagha1, J. Edwards1, D. Manuel1, J. McGowen1, M. Zwarenstein1, D. Fergusson1,

A. Tricco1, K. Cobey1, M. Sampson1, M. King1, D. Richards1, A. Bodnaruc1, D. Moher1

1Ottawa Hospital Research Institute, Ottawa, Ontario, Canada


## ABSTRACT

Background: The rapidly evolving field of the Brain-Heart Interconnectome (BHI) merges neurology and cardiology. Despite its potential, inefficiencies in evidence synthesis and suboptimal adherence to quality standards often result in research waste. Systematic reviews are prone to redundancy, incomplete reporting, and lack of methodological rigor.

Objectives: We introduce an artificial intelligence (AI)-driven system designed to streamline sys- tematic reviews in the BHI domain. The system applies a multipronged approach that includes automated Population, Intervention, Comparator, Outcome, Study design (PICOS) detection, seman- tic search with vector embeddings, graph-based querying of complex relationships, topic modeling for redundancy assessment, and a continuously updated “living” database.

Methods: Key components of the system include a Bi-directional Long Short-Term Memory (Bi- LSTM) model to assess PICOS compliance, Retrieval-Augmented Generation (RAG) and large language models (LLMs) for enhanced semantic retrieval, and BERTopic for thematic clustering. Graph-structured data are stored using Neo4j to capture interactions among interventions, outcomes, and study designs. Performance was evaluated through comparative analyses of RAG with GPT- 3.5 versus plain GPT-4, with additional attention to the Bi-LSTM model’s accuracy for PICOS classification and a hierarchical study design classifier.

Results: RAG combined with GPT-3.5 outperformed GPT-4 for specialized BHI queries requiring graph-based and topic-driven insights. The Bi-LSTM model achieved an 87% accuracy in distinguish- ing PICOS-compliant articles, while the study design classifier attained a 95.7% overall accuracy. By detecting research redundancies, spotlighting underexplored topics, and offering real-time updates, this system systematically reduces waste. Its user-oriented interface provides interactive dashboards and conversational AI, supporting dynamic evidence synthesis.

Conclusion: This AI-enhanced platform addresses well-known challenges in systematic reviews and research waste. Although originally built for BHI, its architectural flexibility—incorporating advanced NLP, machine learning, and graph-based analytics—renders it broadly adaptable to various biomedical research fields. By enabling timely and rigorous evidence synthesis, our approach facilitates more efficient research allocations, fosters high-quality methodological standards, and supports informed clinical decision-making.

Keywords: Brain-Heart Interconnectome (BHI), Systematic Reviews, Research Waste, PICO Compliance, Artificial Intelligence (AI), Natural Language Processing (NLP), Topic Modeling, Retrieval-Augmented Generation (RAG), Study Design Classification, Conversational Systems

An AI-Driven Live Systematic Reviews in the Brain-Heart Interconnectome

1 Introduction

The Brain-Heart Interconnectome (BHI) explores the intricate bidirectional relationships between the cardiovascular and neurological systems [14, 30, 31, 32]. While BHI holds considerable promise for improving patient care, inefficiencies in synthesizing evidence, coupled with inconsistent adherence to quality standards, create obstacles for both clinical and research endeavors. These inefficiencies often give rise to research waste, defined as redundant or low-quality studies that fail to enhance collective knowledge [1, 4, 3, 9].

Research waste persists at virtually all stages of evidence synthesis. For instance, recent studies show that more than 85% of surgical randomized controlled trials (RCTs) exhibit at least one form of research waste—ranging from inadequate reporting to non-publication [4]—and comparable shortcomings persist in other areas of biomedical research [5]. Such inefficiencies generate a cycle in which researchers, clinicians, and policymakers often lack the most rigorous and current data necessary for optimal decisions [33, 34].

Methodological frameworks like PICOS (Population, Intervention, Comparator, Outcome, Study design) [27, 28, 29] promise improved coherence and replicability in clinical trial design [12, 15, 11]. However, evidence suggests that guidelines such as CONSORT (Consolidated Standards of Reporting Trials) [21] and PRISMA (Preferred Reporting Items for Systematic Reviews and Meta-Analyses) [24] remain inconsistently applied, undermining their full potential. In particular, many systematic review authors report substantial challenges in managing extensive literature searches and ensuring meticulous screening and data extraction [8].

The shortcomings in current processes have prompted increasing interest in artificial intelligence (AI) tools to enhance systematic reviews. Several initiatives integrate AI-driven natural language processing (NLP) methods to expedite literature search, screening, data extraction, and risk-of-bias evaluations [19, 10]. Although recent successes—such as RobotReviewer and SciSpace [16, 17, 18]—indicate that AI can lighten the manual workload, domain-specific customization and dynamic updating features remain underdeveloped in many of these systems [23].

1.1 Aim and Scope of the Proposed System

This paper introduces an AI-driven system designed to systematically enhance evidence synthesis in the BHI domain. Our solution incorporates:

• Automated PICOS Compliance Detection: Prioritizes studies aligned with rigorous methodological stan- dards.

• Semantic Search & Graph-Based Queries: Leverages Neo4j [26] and pgVector to reveal meaningful relational structures among diverse data elements (e.g., outcomes, interventions).

• Topic Modeling via BERTopic: Identifies core themes, flags redundant clusters, and highlights underexplored areas [25].

• Living Database Functionality: Dynamically integrates new publications into existing systematic reviews, ensuring near real-time updates.

• Interactive Dashboards and Conversational AI: Facilitates broad accessibility, enabling clinicians, re- searchers, and other stakeholders to engage with and interpret data more efficiently.

1.2 Overall Workflow in Systematic Reviews

Aligned with standard systematic review pipelines, the framework features four primary phases (Figure 1):

1. Define and Search: AI-guided query formulation based on PICOS, supported by semantic matching and graph-based retrieval.

2. Screen and Assess: Automated identification of PICOS-compliant articles and hierarchical classification of study designs (e.g., RCTs, cohort, case-control).

3. Extract and Synthesize: Dynamic clustering and topic modeling (using BERTopic) to highlight thematic areas, redundancy, and emerging trends.

4. Interpret and Update: Integration of new literature, real-time updates of the review database, and user interaction through dashboards and conversational AI.

By minimizing redundancies and emphasizing high-value studies, this system aims to reduce time wasted on low-impact or duplicative research, thus improving the quality and efficiency of BHI-related evidence synthesis [35, 36, 37, 38, 39].

2

An AI-Driven Live Systematic Reviews in the Brain-Heart Interconnectome


> **Figure 1: Workflow of the AI-Driven System for Systematic Reviews in BHI Research**

1.3 BHI Human Requirements

Beyond purely technical considerations, the system’s design and implementation were guided by iterative feedback from domain experts and key stakeholders in the Brain-Heart Interconnectome (BHI) community. Communication was primarily asynchronous (e.g., email exchanges), allowing for flexible collaboration across different time zones and schedules. These interactions served to:

• Clarify Screening Criteria: Experts emphasized that studies lacking abstracts should not be excluded prematurely, recognizing that incomplete records can still hold value in emerging BHI areas. Eligibility criteria were further aligned with evidence-based frameworks to ensure consistency in participant selection, intervention design, and outcome evaluation. These criteria included:

– Types of Participants: Studies must involve human participants diagnosed with conditions relevant to

the BHI domain, using accepted diagnostic criteria. – Types of Interventions: Interventions must be planned, structured, and replicable, targeting specific

outcomes related to neurological or cardiovascular health, with measurable fitness or health components. – Comparator Interventions: The design must include appropriate controls, such as no intervention, usual

care, or alternative validated interventions, to ensure the robustness of outcome assessments. – Outcome Measures: Both primary and secondary outcomes must be evaluated using validated tools to

capture key metrics such as cognitive function, activities of daily living, and health-related quality of life. – Timing of Assessments: Outcome evaluations must include immediate post-intervention assessments as

well as short-term and long-term follow-ups to provide a comprehensive view of intervention efficacy.

• Refine Evaluation Metrics and Terminology: Internal discussions reinforced the equivalence of “sensitivity” and “recall,” while highlighting additional metrics such as Positive Predictive Value (PPV) and Negative Predictive Value (NPV). These exchanges also confirmed that “YES/NO” labeling for study type predictions aligns with “TRUE/FALSE” classification conventions in clinical research.

• Expand Classification Dimensions: Stakeholders identified a “Setting” category (e.g., community, locked facility) necessary for systematically capturing the context of BHI investigations. This requirement led to

3

An AI-Driven Live Systematic Reviews in the Brain-Heart Interconnectome

enhancements in our hierarchical classification scheme, such as incorporating “systematic review” as a distinct study design node.

By incorporating structured eligibility criteria alongside expert-driven feedback, the system ensures consistency in evaluating studies while maintaining methodological rigor and practical relevance. As BHI research continues to evolve, ongoing collaboration with domain experts will remain integral to refining classification schemes, updating evaluation metrics, and aligning the system with real-world clinical and research needs.

2 Methodology

We developed a multifaceted architecture (Figure 2) that integrates cutting-edge AI and NLP components. The system coordinates retrieval, analysis, and exploration functions tailored specifically to the Brain-Heart Interconnectome (BHI) domain. Key components include:


> **Figure 2: Workflow for Knowledge Extraction and Querying**

2.1 Graph Database for Biomedical Insights

Recognizing the inherent complexity of BHI-related data, we utilize Neo4j to represent relationships among key entities such as interventions, outcomes, author affiliations, and publication venues. These graph structures enable sophisticated Cypher queries that uncover nuanced patterns (e.g., comorbidities, multiple interventions within a single study), ensuring a more comprehensive understanding of the domain (Figure 3) [41].


> **Figure 3: Neo4j Graph Visualization of Relationships**

2.2 Retrieval-Augmented Generation and Semantic Search

To optimize document retrieval and streamline knowledge generation:

• pgVector (PostgreSQL Extension): Stores document embeddings, enabling vector-based semantic searches that extend beyond simple keyword matching.

4

An AI-Driven Live Systematic Reviews in the Brain-Heart Interconnectome

• LangChain: Coordinates query processing and retrieval, ensuring that system responses are contextually and thematically aligned with user input.

We examined GPT-3.5 embedded within a RAG framework [40] and benchmarked it against standalone GPT-4. The RAG approach demonstrated superior performance in field-specific queries that require deeper data integration, such as comparing multiple interventions or focusing on specific outcome measures documented in the graph database.

2.3 Automated PICO Compliance Detection and Study Design Classification

1. PICO Compliance: A Bi-LSTM model, trained on an extended PubMed-PICO dataset [10], identifies whether a given abstract conforms to PICOS standards. The model consists of an embedding layer, followed by two bidirectional LSTM layers, two dense layers, and a dropout layer for regularization (Figure 4). 2. Study Design Classification: Large language models (LLMs) are employed to determine study design hierarchies. This process yields precise categorization (e.g., RCT, cohort, case-control, systematic review), which is crucial for the rapid identification of high-quality, methodologically sound research. Classification outcomes are stored in PostgreSQL for future query-based filtering.


> **Figure 4: Architecture of the Bi-LSTM Model for PICO Compliance Detection**

2.4 Topic Modeling with BERTopic

BERTopic supports thematic clustering and identification of underexplored or redundant lines of inquiry. By storing topic labels in both PostgreSQL and Neo4j, the system facilitates flexible exploration and real-time visualization. Researchers can track how key research themes evolve and cluster around pivotal interventions or outcomes. The BERTopic “terms” that define each cluster also serve to highlight the principal concepts driving the conversation in each theme.

2.4.1 Visualization and Dashboards

A Power BI dashboard furnishes interactive visualizations (e.g., word clouds, radial charts) to elucidate publication patterns, authorship dynamics, and shifting research themes (Figures 6, 5). In addition to supporting systematic reviewers, organizations such as the Canadian Institutes of Health Research (CIHR) can utilize this dashboard to monitor reporting guideline compliance (e.g., PICOS or CONSORT adherence) and to inform evidence-based policy and guidelines decisions. These functionalities allow for both granular and global views of BHI-related evidence, depending on user requirements.

2.5 Modular Integration and Front-End Interface

The system orchestrates data flow across multiple backends:

• LangGraph: Directs complex, multi-step queries to the appropriate data store (graph, relational, or vector) while minimizing hallucinations by verifying document relevance. • LiteralAI API: Logs all user interactions, promoting transparency and accountability. • Chainlit Frontend: Offers a user-friendly, conversational interface. Domain experts and clinicians can pose natural language questions and receive curated responses supplemented by relevant source documents.

5

An AI-Driven Live Systematic Reviews in the Brain-Heart Interconnectome


> **Figure 5: Power BI Dashboard Visualizing Research Trends**


> **Figure 6: Relational Database Schema for Metadata, Document Chunks, and Topic Clusters**

2.6 Evaluation Criteria

The system was assessed on:

1. Comparison: RAG vs. GPT-4. Human experts rated the relevance and accuracy of system-generated answers. RAG-based GPT-3.5 outperformed plain GPT-4 in inquiries involving layered domain knowledge (e.g., synergy between interventions). 2. Quantitative Metrics: Retrieval accuracy and content fidelity were measured using standard metrics (e.g., Mean Reciprocal Rank, ROUGE). 3. Hierarchical Study Design Classification: Expert evaluations confirmed that the automated classification process was robust and aligned well with gold-standard references.

3 Results

3.1 Performance of RAG vs. GPT-4

Expert reviewers evaluated RAG plus GPT-3.5 against GPT-4 across a series of domain-specific questions. Each query was scored on:

• Relevance of Retrieved Documents • Accuracy and Contextual Fit • Sufficiency for Guiding Clinical or Research Decisions

Overall, 75% of RAG-augmented responses met or exceeded expert expectations, with:

• 30% of queries adequately answered by both RAG-based GPT-3.5 and GPT-4.

6

An AI-Driven Live Systematic Reviews in the Brain-Heart Interconnectome

• 25% where RAG-based GPT-3.5 excelled, especially for relationship-centric queries leveraging Neo4j. • 20% where GPT-4’s broader generative capacity performed better (e.g., large-scale thematic overviews). • 25% where the system required further optimization, mainly due to complexity in synthesizing multiple data layers (e.g., PICOS compliance, graph-based relationships, and topic clusters).

Notably, the BERTopic “terms” that emerged within these topic clusters also helped refine certain queries. By focusing on the high-impact tokens identified in each cluster, RAG-based GPT-3.5 more effectively retrieved contextually relevant studies.

3.2 Topic Modeling Outcomes

BERTopic-derived clusters helped researchers pinpoint areas with high publication density and detect thematic overlaps. In addition to summary statistics and top terms, multiple visual representations were generated to capture the topic distribution and how it evolves over time.

In Figure 7, a line chart shows the number of documents assigned to each discovered topic. Peaks in this figure indicate clusters with a relatively higher number of publications. Table 1 provides an illustrative overview of the topics, including the topic label, high-frequency terms, and an example of representative documents.


> **Figure 7: Line chart showing the count of documents assigned to each discovered topic. Higher peaks indicate clusters**

with more publications.


> **Table 1: Illustrative BERTopic output for all discovered topics, showing label (Name), high-frequency terms**

(Representation), and count of documents.

Topic Count Name Representation

0 -1 -1_report_trial_studi_rct {report, trial, studi, rct, data, use, ...} 1 0 0_outcom_trial_regist_registr {outcom, trial, regist, registr, primari, ...} 2 1 1_blind_trial_bia_effect {blind, trial, bia, effect, outcom, ...} 3 2 2_harm_report_trial_event {harm, report, trial, event, advers, ...} 4 3 3_qualiti_rct_report_abstract {qualiti, rct, report, abstract, method, ...} 5 4 4_size_sampl_sampl size_calcul {size, sampl, sampl size, calcul, power, ...} 6 5 5_trial_guidelin_item_report {trial, guidelin, item, report, develop, ...} 7 6 6_journal_report_orthodont_rct {journal, report, orthodont, rct, publish, ...} 8 7 7_subgroup_trial_analys_subgroup {subgroup, trial, analys, subgroup analys, ...} 9 8 8_chines_tcm_report_rct {chines, tcm, report, rct, qualiti, ...} 10 9 9_pro_rct_cancer_report {pro, rct, cancer, report, qualiti, ...} 11 10 10_abstract_report_ci_trial {abstract, report, ci, trial, statist, ...} 12 11 11_recruit_retent_particip_strategi {recruit, retent, particip, strategi, ...} 13 12 12_trial_particip_patient_organ {trial, particip, patient, organ, platform, ...}


> **Figure 8 presents a stacked area chart depicting the temporal shifts in topic composition from 2010 to 2024. Each**

> color represents a different topic, and changing proportions show how research interests evolve over time. Figure 9 is a

7

An AI-Driven Live Systematic Reviews in the Brain-Heart Interconnectome

heatmap of document counts per topic (y-axis) by publication year (x-axis). Warmer (yellow) cells in this heatmap represent higher document frequencies.


> **Figure 8: Stacked area chart displaying how the topic composition shifts over time (2010–2024). Individual colors**

represent distinct topics.


> **Figure 9: Heatmap depicting the number of documents per topic (y-axis) per publication year (x-axis). Brighter**

(yellow) cells indicate higher document counts.


> **Figure 10 shows an example of a word cloud, highlighting frequently occurring terms that point to methodological**

> considerations such as “pubmed,” “journals,” and “randomized.” This provides a quick visual cue about the main ideas
defining the cluster.

Key Observations

• Redundancy Alerts were triggered by repeated short-term cardiovascular outcome studies, prompting a recommendation to investigate long-term neurocardiological impacts. • Temporal Trends can be visualized in Figures 8 and 9, showing peaks in publication volume from 2018 to 2022. This surge may be tied to shifting funding priorities or increased adoption of reporting guidelines. • Granularity in Analysis is enhanced by combining BERTopic cluster terms with relational data, offering deeper insights into the interventions and outcomes dominating each topic.

8

An AI-Driven Live Systematic Reviews in the Brain-Heart Interconnectome


> **Figure 10: Word cloud example**

3.3 Document Relevance and Hallucination Prevention

The LangGraph module proved successful at minimizing off-target references. By mapping retrieved texts back to original user queries, the system drastically reduced irrelevant or fabricated outputs commonly seen in standalone LLM- generated answers (Figure 11). This process enhances the clinical and research utility of AI-aggregated information.


> **Figure 11: Workflow for Query Processing, Retrieval, and Relevance Grading**

3.4 PICO Compliance Detection

The Bi-LSTM model recorded an accuracy of 87% in identifying PICOS-compliant abstracts. By spotlighting high- quality research early in the screening process, this feature helps curators avoid downstream inclusion of studies that fail to meet foundational evidence-based criteria.

9

An AI-Driven Live Systematic Reviews in the Brain-Heart Interconnectome

3.5 Study Design Classification

A validation study of 164 references measured the system’s classification performance for study design. Table 2 summarizes the confusion matrix.


> **Table 2: Confusion Matrix for Study Design Prediction**

True Positives False Positives True Negatives False Negatives

Counts 74 7 83 0


> **Table 3 shows derived performance metrics.**


> **Table 3: Performance Metrics for Study Design Classification**

Metric Precision Recall Specificity Accuracy

Value 91.4% 100% 92.2% 95.7%

These data underscore the system’s capability to rapidly identify and prioritize methodologically rigorous studies during the screening phase, augmenting the quality of subsequent analyses.

4 Discussion

The Brain-Heart Interconnectome (BHI) promises significant breakthroughs in clinical practice and research. However, persistent issues of suboptimal data curation, incomplete reporting, and manual workflows that often fail to keep pace with new findings contribute to research waste [3, 9]. Our proposed system seeks to alleviate these challenges by automating critical components of systematic reviews while providing decision support for researchers and clinicians.

4.1 Addressing Redundancy and Guiding Research Focus

By leveraging BERTopic to cluster related studies (see Section 3.2), the system exposes opportunities for methodological consolidation. The top terms extracted in each cluster help identify repetitive investigations. This feature aids editorial teams and funding bodies alike to redirect efforts toward genuinely novel or underexplored domains. In the BHI space, such direction could expedite the discovery of biomarkers, therapeutic targets, or improved patient screening methods.

4.2 Quality Assurance Through PICO Compliance and Study Design

Selective inclusion of PICOS-compliant and high-quality study designs (e.g., RCTs, systematic reviews for BHI) forms the foundation of dependable reviews. The Bi-LSTM model’s robust performance in screening abstracts for PICOS elements ensures that substandard studies are flagged early, thereby minimizing wasted effort in later review stages. Our hierarchical classification approach further refines selection by prioritizing the most robust methodologies within a given research theme.

4.3 Dynamic Integration and Timely Evidence

One major limitation of conventional reviews is the significant lag before newly published data are incorporated. This system’s living database structure updates continuously, ensuring that reviews reflect near real-time shifts in the evidence base. Such “live” systematic reviews can be of critical importance when time-sensitive decisions—such as those surrounding acute cardiovascular events or neuroprotective interventions—must be grounded in the latest evidence.

4.4 Enhanced Accessibility via Conversational AI and Dashboards

From an end-user perspective, the ability to pose domain-specific questions to a conversational AI dramatically lowers barriers to entry. Non-technical stakeholders—such as allied health professionals or policymakers—can navigate the evidence base without advanced data analytics expertise, thereby closing the gap between research production and application. The dynamic dashboard, enriched by BERTopic analyses, similarly empowers organizations to monitor compliance trends and uncover opportunities for targeted reporting guidelines and policy intervention.

10

An AI-Driven Live Systematic Reviews in the Brain-Heart Interconnectome

4.5 Potential for Broader Implementation

Although optimized for BHI, the architecture is generalizable. Other specialties or cross-disciplinary fields encountering large, heterogeneous bodies of literature can benefit from this structured, AI-driven system. By systematically highlighting both research gaps and emergent topics (through BERTopic’s cluster terms), this approach is poised to improve global research efficiency and reinforce evidence-based medicine principles in numerous clinical and translational arenas.

5 Limitations and Future Directions

Despite promising results, several constraints warrant further examination:

• Data Quality and Representativeness: The accuracy of classification models and topic clustering heavily depends on the quality and diversity of training data. Underrepresented subdomains in BHI may see diminished performance.

• Verification Overheads: While continuous updates ensure currency, verifying the trustworthiness of new studies demands structured pipelines or human oversight.

• Scalability and Interoperability: Large-scale real-world implementation may require robust interfaces with institutional databases, posing potential challenges around data privacy and standardization.

• User Adoption Studies: The system’s utility ultimately depends on acceptance by researchers and clinicians. Formal usability assessments and iterative improvements will be essential to refine the interface and outputs.

Future work will focus on more sophisticated machine learning workflows, stronger integration with hospital informatics systems, and user-centered design studies to optimize the platform’s real-world applicability.

6 Conclusion

Our AI-enhanced system reimagines systematic reviews in the Brain-Heart Interconnectome (BHI) by integrating advanced NLP methods, graph-based relationship modeling, and continuous database updates. Key functionali- ties—ranging from automated PICOS compliance detection for BHI to topic modeling—significantly reduce the burden of manual screening and refine research focus. By providing timely insights, democratized access via conversational AI, and robust data curation, the system delivers a transformative platform for evidence synthesis in BHI and potentially beyond. This technology-supported paradigm promises to uphold methodological rigor, mitigate research waste, and empower more decisive, up-to-date clinical and reporting guidelines’ policy-making actions.


## References


## References

[1] Chalmers, Iain and Glasziou, Paul. Avoidable waste in the production and reporting of research evidence. The

Lancet, 374(9683):86–89, 2009.

[2] Stephen, J. Chapman, M. Aldaffaa, Candice L. Downey, and David Jayne. Research waste in surgical randomized

controlled trials. British Journal of Surgery, 106(11):1464–1471, 2019. https://doi.org/10.1002/BJS. 11266.

[3] Alexander, R. Zheutlin, Joshua D. Niforatos, Eric Stulberg, and Jeremy B. Sussman. Research Waste in Random-

ized Clinical Trials: a Cross-Sectional Analysis. Journal of General Internal Medicine, 35(10):3105–3107, 2020. https://doi.org/10.1007/S11606-019-05523-4.

[4] Chapman, S.J., Shelton, B., Mahmood, H., Fitzgerald, J.E., Harrison, E.M., and Bhangu, A. Discontinuation and

non-publication of surgical randomised controlled trials: observational study. BMJ Open, 9(10):e032019, 2019.

[5] Lu, L., Sun, J., Ren, X., Ma, X., Guo, Q., Wang, X., and others. Reporting quality and research waste in gastric

cancer randomized controlled trials. Annals of Surgical Oncology, 28(6):2991–3000, 2021.

[6] Santo, S.D., Delgado-Rodriguez, M., and Bonfill, X. Meta-research studies of reporting guidelines and reporting

quality in trials: An overview. Systematic Reviews, 11:34, 2022.

11

An AI-Driven Live Systematic Reviews in the Brain-Heart Interconnectome

[7] Ghosh, S., Thomas, R., and Wang, Y. AlpaPICO: Advancing PICO extraction for systematic reviews in low-

resource settings. AI in Medicine, 78:203–212, 2024.

[8] Dal Santo, Teresa S., Rice, Danielle B., Amiri, Loabat, Tasleem, A., Li, K., Boruff, Jill, Geoffroy, Mcg,

Benedetti, Andrea, and Thombs, Brett D. Research waste from poor reporting of core methods and results and redundancy in studies of reporting guideline adherence: a meta-research review. medRxiv, 2022. https: //doi.org/10.1101/2022.12.19.22283669.

[9] Rosengaard, Louise Olsbro, Andersen, Mikkel Zola, Rosenberg, Jacob, and Fonnes, Siv. Several methods for

assessing research waste in reviews with a systematic search: a scoping review. PeerJ, 12:e18466–e18466, 2024. https://doi.org/10.7717/peerj.18466.

[10] Jin, Di, and Szolovits, Peter. PICO Element Detection in Medical Text via Long Short-Term Memory Neural

Networks. In Proceedings of the BioNLP 2018 Workshop, pages 67–75. Melbourne, Australia: Association for Computational Linguistics, 2018.

[11] Dhrangadhariya, Anjani, Manzo, Gaetano, and Müller, Henning. PICO to PICOS: Weak Supervision to Extend

Datasets with New Labels. Studies in Health Technology and Informatics, 2024. https://doi.org/10.3233/ shti240775.

[12] Zhang, Qi, Qu, Jing, Zhao, Qi, and Xue, Fuzhong. Task-Specific Model Allocation Medical Papers PICOS

Information Extraction. In Communications in Computer and Information Science, pages 166–177. Springer, 2023. https://doi.org/10.1007/978-981-97-1717-0_15.

[13] Panda, S., and Williams, G. Addressing global research inefficiencies through AI and interdisciplinary collabora-

tion. Nature Reviews Medicine, 19:345–358, 2022.

[14] Deking, Sarah, and Liman, Jan. Interactions between the brain and heart. Nervenarzt, 92(10):977–985, 2021.

https://doi.org/10.1007/S00115-021-01170-5.

[15] Feldner, Katie, and Dutka, Paula. Exploring the Evidence: Generating a Research Question: Using the PICOT

Framework for Clinical Inquiry. Nephrology Nursing Journal, 51(4):393–393, 2023. https://doi.org/10. 37526/1526-744x.2024.51.4.393.

[16] RobotReviewer and SciSpace automation tools for systematic reviews. Systematic Reviews Journal, 2024. Note:

Available at Systematic Reviews Journal. Accessed 2024.

[17] Petri, D. La sintesi delle evidenze 2.0: come l’intelligenza artificiale sta rendendo più efficienti le revisioni

sistematiche [Evidence synthesis 2.0: how artificial intelligence is making systematic reviews more efficient.]. Recenti progressi in medicina, 114(6):359–361, 2023. https://doi.org/10.1701/4042.40229.

[18] Ge, L., Agrawal, R., Singer, M., and others. Leveraging artificial intelligence to enhance systematic reviews

in health research: advanced tools and challenges. Systematic Reviews, 13:269, 2024. https://doi.org/10. 1186/s13643-024-02682-2.

[19] Ofori-Boateng, R., Aceves-Martins, M., Wiratunga, N., and others. Towards the automation of systematic reviews

using natural language processing, machine learning, and deep learning: a comprehensive review. Artificial Intelligence Review, 57:200, 2024. https://doi.org/10.1007/s10462-024-10844-w.

[20] Arvanitis, Costas D. Systematic literature review in five steps. Berkeley Program in Law & Economics, 155(3_Supplement):A103–A103, 2024. Publisher: Acoustical Society of America. https://doi.org/10. 1121/10.0026958.

[21] Moher, David, Schulz, Kenneth F., Altman, Douglas G., Almanza Muñoz, José de Jesús, and De Roux Reyes,

Santiago. La Declaración CONSORT: Recomendaciones revisadas para mejorar la calidad de los informes de ensayos aleatorizados de grupos paralelos. Revista de sanidad militar (México), 2024. https://doi.org/10. 56443/fbnznt22.

[22] Ke, YuHe, Jin, Liyuan, Elangovan, Kabilan, Abdullah, Hairil Rizal, Liu, Nan, Soh, Chai Rick, Tung, Joshua Yi

Min, Ong, Jasmine Chiat Ling, and Ting, Daniel Shu Wei. Development and Testing of Retrieval Augmented Generation in Large Language Models – A Case Study Report. arXiv preprint arXiv:2402.01733, 2024. https: //arxiv.org/abs/2402.01733.

[23] Menezes, Maria Clara Saad, and others. The potential of Generative Pre-trained Transformer 4 (GPT-4) to analyse

medical notes in three different languages: a retrospective model-evaluation study. The Lancet Digital Health, 7(1):e35–e43, 2023.

[24] Page, Matthew J., McKenzie, Joanne E., Bossuyt, Patrick M., Boutron, Isabelle, Hoffmann, Tammy C., Mulrow,

Cynthia D., Shamseer, Larissa, Tetzlaff, Jennifer M., Akl, Elie A., Brennan, Sue E., Chou, Roger, Glanville, Julie, Grimshaw, Jeremy M., Hróbjartsson, Asbjørn, Lalu, Manoj M., Li, Tianjing, Loder, Elizabeth W., Mayo-Wilson,

12

An AI-Driven Live Systematic Reviews in the Brain-Heart Interconnectome

Evan, McDonald, Steve, McGuinness, Luke A., Stewart, Lesley A., Thomas, James, Tricco, Andrea C., Welch, Vivian A., Whiting, Penny, and Moher, David. The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ, 372:n71, 2021. https://doi.org/10.1136/bmj.n71. [25] Grootendorst, Maarten. BERTopic: Neural topic modeling with a class-based TF-IDF procedure. arXiv preprint

arXiv:2203.05794, 2022. https://arxiv.org/abs/2203.05794. [26] Toledo, Rafael F., Atlee, Joanne M., Xiong, Rui Ming, and Liu, Mingyu. (Neo4j)ˆ Browser: Visualizing

Variable-Aware Analysis Results. Proceedings of the 16th ACM SIGSOFT International Conference on Software Engineering for Adaptive and Self-Managing Systems, pages 69–73, 2024. https://doi.org/10.1145/ 3639478.3640046. [27] Ma, Wei, Pan, Pei, Xu, Gang, Yang, Wenyi, Li, Dong, Tian, Shen, Wang, Zhichao, Cai, Yong, and Yao, Ming.

The application of the “PICO” teaching model in clinical research course for medical students. Global Medical Education, 2024. Publisher: Walter de Gruyter GmbH. https://doi.org/10.1515/gme-2024-0006. [28] Zhang, Qi, Qu, Jing, Zhao, Qi, and Xue, Fuzhong. Task-Specific Model Allocation Medical Papers PICOS

Information Extraction. Communications in Computer and Information Science, pages 166–177, 2023. Publisher: Springer Science+Business Media. https://doi.org/10.1007/978-981-97-1717-0_15. [29] Zhang, Lei, Wu, Tian, Zheng, Yuan, and Jian, Yue. Enhancing PICOS Information Extraction with UIE and

ERNIE-Health. Communications in Computer and Information Science, pages 186–194, 2023. Publisher: Springer Science+Business Media. https://doi.org/10.1007/978-981-97-1717-0_17. [30] Cai, Z., Gao, H., and Wu, M. Physiologic Network-based Brain-heart Interaction Quantification during Visual

Emotional Elicitation. IEEE Transactions on Neural Systems and Rehabilitation Engineering, 32:2482–2491, 2024. https://doi.org/10.1109/tnsre.2024.3424543. [31] Sabor, N., Mohammed, H., Li, Z., and Wang, G. BHI-Net: Brain-Heart Interaction-Based Deep Architectures

for Epileptic Seizures and Firing Location Detection. IEEE Transactions on Neural Systems and Rehabilitation Engineering, 30:1576–1588, 2022. https://doi.org/10.1109/TNSRE.2022.3181151. [32] Catrambone, V., and Valenza, G. Complex Brain-Heart Mapping in Mental and Physical Stress. IEEE Journal

of Translational Engineering in Health and Medicine, 1, 2023. https://doi.org/10.1109/jtehm.2023. 3280974. [33] Dal Santo, T.S., Rice, D.B., Amiri, L., Tasleem, A., Li, K., Boruff, J., Geoffroy, M., Benedetti, A., and Thombs,

B.D. Research waste from poor reporting of core methods and results and redundancy in studies of reporting guideline adherence: a meta-research review. medRxiv, 2022. https://doi.org/10.1101/2022.12.19. 22283669. [34] Yordanov, Y., Dechartres, A., Atal, I., Tran, V.-T., Boutron, I., Créquit, P., and Ravaud, P. Avoidable Waste

of Research Related to Outcome Planning and Reporting in Clinical Trials. BMC Medicine, 16(1):87, 2018. https://doi.org/10.1186/S12916-018-1083-X. [35] Legate, A., Nimon, K., and Noblin, A. (Semi)automated Approaches to Data Extraction for Systematic Reviews

and Meta-analyses in Social Sciences: A Living Review. F1000Research, 13:664, 2024. https://doi.org/10. 12688/f1000research.151493.2. [36] Tomczyk, P., Brüggemann, P., and Vrontis, D. AI Meets Academia: Transforming Systematic Literature Reviews.

Euromed Journal of Business, 2024. https://doi.org/10.1108/emjb-03-2024-0055. [37] Górska, A., and Tacconelli, E. Towards Autonomous Living Meta-Analyses: A Framework for Automation

of Systematic Review and Meta-Analyses. Studies in Health Technology and Informatics, 316:378–382, 2024. https://doi.org/10.3233/shti240427. [38] Ofori-Boateng, R., Aceves-Martins, M., Wiratunga, N., and Moreno-García, C.F. Towards the Automation of Sys-

tematic Reviews Using Natural Language Processing, Machine Learning, and Deep Learning: A Comprehensive Review. Artificial Intelligence Review, 57(8), 2024. https://doi.org/10.1007/s10462-024-10844-w. [39] Tóth, B., and Péntek, M. Automation of Systematic Reviews of Biomedical Literature: A Scoping Review of Stud-

ies Indexed in PubMed. Systematic Reviews, 13(1), 2024. https://doi.org/10.1186/s13643-024-02592-3. [40] Fan, Wenqi, Ding, Yujuan, Ning, Liangbo, Wang, Shijie, Li, Hengyun, Yin, Dawei, Chua, Tat-Seng, and Li,

Qing. A Survey on RAG Meeting LLMs: Towards Retrieval-Augmented Large Language Models. arXiv preprint arXiv:2405.06211, 2024. https://arxiv.org/abs/2405.06211. [41] Peng, Boci, Zhu, Yun, Liu, Yongchao, Bo, Xiaohe, Shi, Haizhou, Hong, Chuntao, Zhang, Yan, and Tang,

Siliang. Graph Retrieval-Augmented Generation: A Survey. arXiv preprint arXiv:2408.08921, 2024. https: //arxiv.org/abs/2408.08921.

13
