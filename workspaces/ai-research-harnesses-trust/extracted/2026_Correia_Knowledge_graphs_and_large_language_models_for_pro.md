---
workspace_id: "SCI-000167"
doi: "10.1016/j.ipm.2026.104882&quot"
title: "Knowledge graphs and large language models for prompt-based scientometric inquiry"
year: 2026
extraction_engine: "pymupdf"
---
# 2026 Correia Knowledge graphs and large language models for pro

This is a self-archived version of an original article. This version  may differ from the original in pagination and typographic details.

Correia, António; Saarela, Mirka; Kärkkäinen, Tommi

Author(s):

Knowledge graphs and large language models for prompt-based scientometric inquiry

Title:

Year:

2026

Version:

Published version

Copyright:

© 2026 The Author(s). Published by Elsevier Ltd.

Rights:

CC BY 4.0

Rights url:

https://creativecommons.org/licenses/by/4.0/

Please cite the original version:

Correia, A., Saarela, M., & Kärkkäinen, T. (2026). Knowledge graphs and large language models for prompt-based scientometric inquiry. Information Processing and Management, 63(7), Article 104882. https://doi.org/10.1016/j.ipm.2026.104882

Information Processing and Management 63 (2026) 104882

Contents lists available at ScienceDirect

Information Processing and Management

journal homepage: www.elsevier.com/locate/ipm

Knowledge graphs and large language models for prompt-based  scientometric inquiry$

António Correia ∗, Mirka Saarela , Tommi Kärkkäinen

Faculty of Information Technology, University of Jyväskylä, P.O. Box 35, FI-40014 Jyväskylä, Finland

A B S T R A C T

A R T I C L E  I N F O

Scientometrics is undergoing a methodological transformation driven by the increasing avail- ability of large-scale scientific data and advances in artificial intelligence (AI). Traditional  approaches centered on citation analysis and bibliographic coupling are now complemented by  methods that leverage semantic representations, structured knowledge, and natural language  understanding. However, current generative AI systems pose inherent challenges such as  hallucinations, lack of transparency in decision-making and explainability, and issues with  source reliability. In this article, we seek to mitigate these challenges by outlining a framework  that integrates knowledge graphs (KGs) and large language models (LLMs) for scientometric  inquiry. Taking a socio-technical perspective, the article sets out to explore the intersectional  space of computing and information science from a human-centered approach. The framework  is designed to support both established scientometric tasks, such as trend analysis, topic  detection, and collaboration mapping, and more exploratory, insight-generating applications,  including question answering, knowledge discovery, and contextual enrichment of scientific  content. Drawing on recent developments in the use of KGs and LLMs in scientific domains, we  provide a comparative overview of existing work, identify key design principles, and discuss the  advantages and limitations of such a framework. Our goal is to chart a pathway toward more  interactive, transparent, and generative approaches in information science and cross-disciplinary  research.

Keywords: Artificial intelligence Human-computer interaction Knowledge graphs Knowledge-based question answering Large language models Prompting Query-based search Scientometrics


## 1. Introduction

Scientometrics has long played a crucial role in understanding the structure, growth, and dynamics of science (Van Raan, 1997).  Traditional methods—such as citation analysis, co-authorship networks, and bibliometric indicators—remain central in information  science to evaluating research productivity, influence, collaboration patterns, and science-technology linkages (Abbasiantaeb et al.,  2025). An equally important dimension of scientometrics is the assessment of publication channels, including journal rankings,  impact metrics, and editorial practices, which inform decisions about where and how scientific work is disseminated (Pölönen  et al., 2021; Saarela & Kärkkäinen, 2020; Safón & Docampo, 2023). Yet, as scientific output continues to grow exponentially and  research becomes increasingly interdisciplinary and difficult to manually parse and analyze, the tools of scientometrics must evolve  accordingly (Mingers & Leydesdorff, 2015; Verma et al., 2023). This is exacerbated by the growing popularity of foundation and  large language models (LLMs), which have also brought new challenges to the information science community such as opaqueness  in decision-making/explainability, reliability of sources, and hallucinations (Formanek, 2025; Thelwall & Kurt, 2025).

$ This article is part of a Special issue entitled: ‘FLLM’ published in Information Processing and Management.

∗Corresponding author.

E-mail address: antonio.g.correia@jyu.fi (A. Correia).

https://doi.org/10.1016/j.ipm.2026.104882 Received 1 September 2025; Received in revised form 29 April 2026; Accepted 29 April 2026

Available online 8 May 2026  0306-4573/© 2026 The Author(s).  Published by Elsevier Ltd.  This is an open access article under the CC BY license  ( http://creativecommons.org/licenses/by/4.0/ ).

A. Correia et al.

Information Processing and Management 63 (2026) 104882

Fig. 1. A conceptual overview of research integrating traditional scientometric methods with emerging AI technologies. The framework combines  established scientometric tasks (e.g., citation analysis, trend detection) with the representational capabilities of KGs and the generative features  of LLMs. This integration supports new, discovery-oriented workflows while enhancing the scalability, interpretability, and interactivity of  information science and cross-disciplinary research.

Advances in artificial intelligence (AI), particularly in knowledge graphs (KGs) and LLMs, now offer the opportunity to expand  the analytic and exploratory power of scientometric applications. These technologies can not only enhance traditional tasks such as  trend detection and influence mapping, but also support new kinds of queries—for example, mining technology distributions and  evolution paths from scientific papers (Yun et al., 2022), generating structured summaries of highly cited works within specific  domains (Li et al., 2024), or identifying emerging research directions across multimodal scientific data (D’aquin, 2025). As a  result, information science scholars now have a wide range of opportunities to redefine search processes while facilitating reflective  information engagement (Mohammadi et al., 2026; Tibau et al., 2024).

In recent years, several studies have explored the use of KGs in scientometric analyses (e.g., Schäfer et al., 2024), while others  have investigated the application of LLMs for tasks such as supporting the execution of literature reviews (e.g., Schmitt, 2025),  citation context analysis (e.g., Nishikawa & Koshiba, 2024), topic modeling (e.g., Azher et al., 2024), and finding existing research  on relevant issues (e.g., Shen et al., 2023). At the same time, there is growing interest in the unification of KGs and LLMs for more  robust AI reasoning and knowledge discovery across domains (Jiang et al., 2024; Pan et al., 2024; Phan & Do, 2025). However, the  integration of traditional scientometric methods with KGs and LLMs to enhance literature search and analysis has yet to be fully  explored.

Drawing on the theoretical work of Marchionini (2008), which explores human interaction with digital information objects,  this article addresses this gap in research by presenting a conceptual and technical roadmap for combining KG- and LLM-based  technologies to enable deeper, more contextual, and interactive scientometric insights. To this end, we outline a human-centered  approach embedded in a socio-technical framework where structured knowledge representations and generative AI systems work  in tandem to provide more insightful scientometric analyses (see Fig. 1). Rather than replacing existing metrics, these tools extend  their reach by making such analyses more accessible, contextualized, and discovery-oriented.

Using the theoretical lenses described above, this study is guided by the following research questions (RQs): RQ1: How can KGs and LLMs be integrated into a unified framework to support more interactive and context-aware scientometric  inquiry?

RQ2: To what extent does a human-in-the-loop KG-LLM approach mitigate common errors in bibliometric analysis (e.g., hallu- cinations and semantic ambiguity) compared to using these technologies in isolation?

By answering these questions, we articulate a set of design considerations for mitigating the black-box and hallucination  limitations of standalone KGs and LLMs. We operationalize this framework through a human-in-the-loop (HITL) pipeline applied to  author name disambiguation, a core challenge in scientometrics. Moreover, we validate the proposed approach against traditional  crowdsourcing methods (human baseline), standalone KGs, and LLM-based approaches. The goal is to demonstrate workflow  feasibility and error-mitigation mechanisms through a proof-of-concept use case, rather than to claim performance superiority.

2

A. Correia et al.

Information Processing and Management 63 (2026) 104882


## 2. Related work

To identify the relevant literature for this study, a search was conducted using the Scopus, Web of Science, and Dimensions  databases. Scopus was selected due to its coverage for information science research, as previously noted by Thelwall and Maflahi  (2015). However, the exclusive reliance on Scopus would restrict the scope of the literature considered. Given the rapid pace and  interdisciplinarity of research on KGs and LLMs, we consulted Web of Science and Dimensions as additional sources (for a more  comprehensive view of the retrieval capabilities of the three sources selected for analysis see Singh et al. (2023)).

The search strategy employed a Boolean search query tailored to capture articles on KGs, LLMs, and their applications in  scientometrics and related fields. Specifically, the following search string was used on the title, abstract, and keywords:

‘‘(((‘‘knowledge graph*’’)) AND ((‘‘large language model*’’ OR ‘‘LLM*’’ OR ‘‘*GPT*’’ OR ‘‘*Gemini’’ OR ‘‘Llama*’’ OR ‘‘Grok*’’  OR ‘‘Claude*’’ OR ‘‘DeepSeek*’’) AND (‘‘quantitative studies’’ OR ‘‘scientometric*’’ OR ‘‘bibliometric*’’ OR ‘‘altmetric*’’ OR  ‘‘informetric*’’ OR ‘‘technometric*’’ OR ‘‘patentometric*’’)))’’

This search resulted in 19 records being returned on Scopus, 4 on Web of Science, and 14 on Dimensions. An interesting  observation already from this search is that all the documents identified through the three databases were published between 2024  and 2026, indicating the ongoing relevance and development of research in the intersection of KGs, LLMs, and scientometrics. We  excluded conference reviews, books, and book chapters, and retained journal articles and conference papers written in English. In  addition to the database search, a manual search was conducted using snowballing techniques (Wohlin et al., 2022), which involved  reviewing the reference lists of selected papers for further relevant studies.

The literature selected after this process (𝑛= 10) highlights key trends in the integration of KGs and LLMs, which are transforming  information science practices in two interrelated directions: enhancing traditional scientometric analyses and enabling discovery- oriented and generative applications. Table 1 summarizes key studies across these categories, highlighting the specific KGs used and  their contributions.

One important line of work focuses on improving the accuracy, scalability, and depth of traditional scientometric methods. For  instance, Tsaneva et al. (2025) examine workflows that combine LLMs with expert-in-the-loop validation to improve triple accuracy  in the Computer Science Knowledge Graph (CS-KG) (see Dessí et al. (2025) for details on the CS-KG 2.0 data descriptor). Li et al.  (2025) propose an AI-driven approach that maps convergence spaces among scientific and technological domains over time. Hou  et al. (2024) conduct a bibliometric analysis of the Geoscience Knowledge Graph (GeoKG), mapping the development of the field  and highlighting current hotspots such as geoscience knowledge representation and multi-source data integration. Their analysis  also identifies the integration of LLMs into GeoKG workflows as an emerging but underexplored direction.

To improve patent citation recommendations, Lu et al. (2024) introduce PK-BERT, a domain-specific KG that represents entities  within a Transformer architecture. Similarly to what was described in other related studies (e.g., Xiao et al., 2023), the use of KG- based semantic connections such as inventor relationships can outperform generic KG embeddings and improve examiners’ citation  recommendations. Weng et al. (2024) take a large-scale approach by using KG-based methods to trace the evolution of research on  LLMs themselves. Their work uncovers topical shifts and collaboration networks, reinforcing the idea that KGs are not only tools  for structuring knowledge but also for mapping the dynamics of scientific progress.

A parallel set of studies explores how combining KGs with LLMs can support more exploratory and generative research  workflows. Lopez et al. (2025) show that multimodal biomedical KGs can enrich foundation models in drug discovery, providing  both structured foundation and contextual depth. D’aquin (2025) argues for aligning LLMs with structured representations to  support scientific reasoning, proposing that KGs serve as cognitive scaffolds for navigating complex domains. Li et al. (2024) further  contribute to this category by using models trained on the Earth Science Data Corpus (ESDC) to demonstrate how extracted entity  knowledge can augment downstream applications such as topic discovery, scientometric mapping, and knowledge-enhanced question  answering. The resulting Earth Science Data KG supports scientometric analysis of Earth system science, enabling fine-grained  mapping of research trends in an increasingly data-rich domain.

Another example of generative scientometric applications is the work by Gu and Krenn (2024), who introduce SciMuse, a system  that combines a large-scale KG—constructed from more than 58 million scientific papers—with GPT-4 to generate personalized  research ideas. As in other areas where LLMs have become a focal point for iterative research idea ideation (e.g., Pu et al., 2025),  their large-scale evaluation involving 110 research group leaders illustrates how KGs and LLMs can augment early-stage scientific  creativity, predict the perceived ‘‘interestingness’’ of ideas, and foster cross-disciplinary collaboration.

Complementing these efforts, Cadeddu et al. (2024) investigate strategies for injecting structured knowledge into transformer- based models to enhance scientific text classification. They introduce the AIDA24k benchmark, a dataset derived from the  Academia/Industry DynAmics (AIDA) KG that links 24,000 articles to the Computer Science Ontology (CSO). Their comparative  analysis reveals that while sophisticated architectures like K-BERT perform well in low-resource settings, hybrid approaches  combining BERT with Multilayer Perceptrons (BERT-MLP) yield more stability and perform better on larger datasets.

Taken together, these studies illustrate a clear shift in scientometrics research—from retrospective measurement and mapping  toward proactive, AI-enhanced discovery and ideation. As Table 1 shows, KGs and LLMs now serve both as instruments of evaluation  and engines of scientific insight. Studies such as Li et al. (2024), while placed in the second category, can contribute to both  traditional and discovery-oriented workflows and therefore illustrate this convergence.

While the literature reviewed in this study demonstrates the growing intersection of KGs and LLMs, some critical limitations  remain. Most hybrid approaches are tightly coupled to specific domains, such as geoscience (Hou et al., 2024; Li et al., 2024) or

3

A. Correia et al.

Information Processing and Management 63 (2026) 104882


> **Table 1**

> Recent studies integrating KGs with LLMs in scientometrics and related domains. These methods have been applied to literature analysis, trend 
detection, and entity linking.
 Study
Focus
Knowledge graph used
 
 Category 1: Enhancing traditional scientometric analyses
 Tsaneva et al. (2025)
Hybrid workflows for triple validation and 
expert-in-the-loop KG refinement

Computer Science Knowledge Graph  (CS-KG)

Li et al. (2025) Generating fine-grained semantic feature  representations to capture scientific patterns and  technological interactions

Temporal Heterogeneous Graph Neural  Networks-based Technology Convergence  Prediction (THGNN-TCP)

Hou et al. (2024) Bibliometric mapping and trend analysis in  geoscience; emerging role of LLMs

Geoscience Knowledge Graph (GeoKG)

Lu et al. (2024) Combining patent KGs with the semantic  capabilities of the BERT language model to map  relationships between entities

Patent Knowledge graph embedded in  BERT (PK-BERT) model

Weng et al. (2024) Evolution of LLM research via large-scale  KG-based analysis

Custom KG of LLM publications

Category 2: Enabling discovery-oriented and generative applications  Lopez et al. (2025) Multimodal KGs as context for LLMs in  high-stakes domains (e.g., drug discovery)

Biomedical KG

D’aquin (2025) Aligning LLMs with structured KGs to support  scientific reasoning

General-purpose scientific KGs

Li et al. (2024) LLM-powered named entity recognition and  entity extraction; KG construction for  downstream tasks like question answering and  topic discovery

Earth Science Data KG (from ESDC  corpus)

Gu and Krenn (2024) Personalized idea generation and prediction of  research interest using LLMs and large-scale KGs

Custom KG from OpenAlex and preprint  servers (SciMuse)

Cadeddu et al. (2024) Graph-based knowledge injection strategies for  improving the effectiveness of transformer-based  models

Academia/Industry DynAmics Knowledge  Graph (AIDA KG)

biomedicine (Lopez et al., 2025). There is a lack of domain-agnostic frameworks capable of supporting generalized scientometric  inquiry both within information science and across disciplines. Moreover, state-of-the-art methods largely focus on KGs as static  repositories for fact-checking LLMs. They lack dynamic, HITL workflows in which user interaction actively shapes and refines  discovery while supporting sensemaking during the search process itself. Existing work typically isolates tasks by emphasizing  either KG construction (Schäfer et al., 2024) or topic modeling (Azher et al., 2024). Currently, integrated frameworks that unify  bibliometric-enhanced information retrieval (IR), entity disambiguation, and generative insight within a single pipeline remain  underexplored. Building on this trajectory, our work proposes a KG-LLM integrated framework that preserves the analytical rigor  of traditional scientometric approaches while embracing the generative, exploratory affordances of modern AI systems.

3. KG-LLM integrated framework with scientometric features for information science and cross-disciplinary research

We describe the overall socio-technical elements of our workflow-based methodological framework. This includes an innovative  human-AI interactive scientometric data processing pipeline focused on capturing intra- and inter-domain knowledge flows and  their impact (Correia, Kärkkäinen et al., 2023). Using a grounded theory approach (see Hicks (2018) for a detailed discussion  of how scholars in information science have advocated for the continued development and application of the grounded theory  method), theoretical assumptions underlying the proposed framework were validated through a qualitative study and participatory  appraisal (Correia, Grover et al., 2023). Conventional scientometric techniques have evolved, yet mapping evidence from large  bibliographic datasets remains challenging. Current methods often fail to satisfy the information seeking needs of diverse stake- holders. For instance, a healthcare practitioner may be interested in unveiling hidden patterns in grey literature on medical record  systems in a certain city or region, while a 3rd-year Ph.D. student in medical education may wish to analyze the impact of certain  AI implementation barriers in healthcare units based on specific characteristics (e.g., bed capacity of wards). In both cases, state- of-the-art LLM-based approaches involving prompt-based question answering could effectively support such search behaviors in an  interactive manner.

Despite recent remarkable achievement, transformer-based LLMs such as SciBERT and GPT-4 fail to capture contextual insights  into the structure, dynamics, and implications of scientometric data due to their limited capacity to interpret and contextualize  research outputs. Moreover, LLMs also depend on the availability and quality of the underlying pre-trained data, which may lead  to over-trust and over-reliance on the model, biased outputs, and incorrect answers (i.e., hallucination) (Mugaanyi et al., 2024;  Yang et al., 2026). This conveys the importance of an architecture that integrates KGs and LLMs as a structured, evidence-based

4

A. Correia et al.

Information Processing and Management 63 (2026) 104882

Fig. 2. General workflow diagram illustrating the KG-LLM interactive prompt-based system. User queries are processed by LLMs, which access  and interpret KG-based scientometric data to support insights on authors, publications, and entity-metric relationships.

interactive approach to enhancing domain-agnostic scientometric analyses in a dynamic way that disrupts the rigid frameworks  upon which current applications are built.

3.1. Description of the overall framework

Building on the architectural principles of the SciCrowd system (Correia et al., 2018), an experimental crowd-computing  prototype intended to support scientometric analysis, our framework is designed to identify patterns and associations in bibliometric  data that are computationally difficult for standalone models to verify. Data extraction is performed by a crawler that systematically  queries selected databases using a standardized XML-based application programming interface (API). The crawler executes a  predefined extraction algorithm to retrieve structured metadata and quantitative metrics, ensuring consistency and reproducibility  across data sources. This automated process minimizes manual intervention, supports scalable data collection, and enables efficient  aggregation of heterogeneous records for subsequent analysis. The extracted elements are structured into an evolutionary taxonomy  that captures their relationships and developmental trajectories over time. All bibliometric elements are modeled to support both  one-to-one and one-to-many relationships with other elements. This relational structure enables flexible linkage across entities,  facilitating the representation of interdependencies among publications, authors, venues, and metrics.

While SciCrowd traditionally relied on distributed volunteers, the integration of KGs and LLMs enables the system to explore  the breadth and depth of publication metadata while creating semantically meaningful linkages between entities. Fig. 2 shows our  prompt-based KG-LLM integrated solution. There are several components in the framework and each component corresponds to the  array of elements that constitute an interactive scientometric pipeline.

In a preprocessing phase, (1) we compute metadata collected from bibliometric data sources so that the raw data can be easily  structured within the KG. To this end, we use a bibliometric-enhanced IR module where the entities and metrics are extracted  and made accessible in the database for further exploration and analysis. After this step, (2) we use a human-AI scientometric  workflow (Correia et al., 2020) where the data automatically crawled from external sources is processed with humans in the loop to  correct possible errors/omissions. As stated by Donner (2024), there is a recurring problem related to the propagation of erroneous  data in research evaluation. These inaccuracies can bias the results of a research output analysis if not addressed properly, affecting  policies or decisions of funding, hiring, promotion, and tenure.

To address (2), we use an entity name disambiguation module where a custom interface can be generated to allow users to  correct errors or disambiguate entities. Correia, Guimarães et al. (2023) describes how such a module can be instantiated through  an author name disambiguation interface designed to merge publication entries with similar authorship-related features based on  multidocument similarity detection. The module was previously developed using PYBOSSA,1 a platform which comes with an API

5

A. Correia et al.

Information Processing and Management 63 (2026) 104882

that facilitates a built-in mechanism to transmit information to the task presenter. The usability of this interface was evaluated  by Correia et al. (2021) in a study with twenty-four participants who completed an adapted version of the validated questionnaire  for user interaction satisfaction (QUIS) (Chin et al., 1988). In line with other tools used to enhance transparency in literature  reviews (e.g., Van De Schoot et al., 2021), a balance strategy is used during the preprocessing of metadata to improve the quality  of the evidence-based inquiry.

Regarding the relationships that can coexist among linked entities in the KG, there is a need to integrate multiple data sources  and ensure interoperability for semantic linkages (Parinov & Kogalovsky, 2014; Shang et al., 2024). This includes textual content  (e.g., topics and taxonomic terms), temporal and geospatial information (e.g., publication year and author’s affiliation country), and  affiliation data (e.g., institution). The impact is measured through bibliometric indicators (e.g., citations) and alternative metrics such  as patent citations. Simultaneously, data-driven interactions contribute to the continuous improvement of the database by training  the algorithm on these interactions (e.g., deduplication for cases where there are similar entries in the database) and predicting  future actions based on similar occurrences. Since our research focuses on settings where human intervention provides correction  and additional oversight, these efforts are grounded in a HITL process (Natarajan et al., 2025) that is tailored to content and context  enrichment for both quantitative and qualitative modeling.

In such scenarios, the system is informed by the interactions with the environment and receives inputs to determine the most  appropriate course of action in a given situation with the intention of tuning its policy (Ramírez et al., 2022). In the context of  multidimensional scientometric data analysis, a HITL approach can be used to grasp elements of human-based decision-making and  generate insights that may not be immediately apparent, while keeping users in control by allowing them to review the algorithmic  actions and provide feedback on their accuracy. Within the scope of this work, HITL workflows offer the potential to assist in large- scale scientific KG construction by enhancing information quality and trustworthiness through an adaptive human-AI interactive  process. In practice, the system triggers a request for human intervention under specific conditions of uncertainty, e.g., when the  cosine similarity between a user’s query (e.g., ‘‘clinical surgery’’) and a retrieved author profile (e.g., ‘‘computer science’’) falls below  a predefined confidence threshold.

To quantify the semantic alignment between the user’s intent and the retrieved entities, a vector-based verification step is  employed. For example, consider 𝐕𝑞 to represent the vector embedding of the user’s natural language query and 𝐕𝑐 to represent  the vector embedding of the candidate’s research profile (derived from the aggregated titles of their publications). The semantic  proximity is determined by calculating the cosine similarity score, 𝜎, as defined in Eq. (1):

𝐕𝑞⋅𝐕𝑐 ‖𝐕𝑞‖ ‖𝐕𝑐‖ (1)

𝜎(𝐕𝑞, 𝐕𝑐) =

Based on this similarity score 𝜎, the system applies a tri-state classification logic to determine the final disambiguation status  𝐷(𝐕𝑞, 𝐕𝑐). As illustrated in Eq. (2), this decision-making process involves a specific uncertainty margin to trigger human intervention:

Accept (Match) if 𝜎> 0.95

⎧ ⎪ ⎨ ⎪⎩

Human Verification if 0.60 < 𝜎≤0.95

𝐷(𝐕𝑞, 𝐕𝑐) =

(2)

Reject (Homonym) if 𝜎≤0.60

Candidates with scores above the upper threshold (𝜎> 0.95) are linked to the entity, while those below the lower bound (𝜎≤0.60)  are disregarded. The interval between these thresholds represents an area of uncertainty, where the decision is delegated to the  human. In essence, the system automatically processes high-confidence matches while reserving human intervention for ambiguous  cases, a design choice that ensures efficiency while reducing errors in scientometric data analysis. This logic assures that the system  only makes definitive decisions when confidence is high, delegating questionable cases to human experts to resolve ambiguity and  maintain the integrity of the KG. This feedback loop complements the limitations reported in Correia, Guimarães et al. (2023) and  allows the user to correct errors in an interactive manner. These interventions not only refine the outputs but can also be temporarily  stored to enhance the session’s context, serving as a ‘‘memory aid’’ for the LLM in subsequent prompts.

3.2. Interaction elements in the prompt-based scientometric analysis pipeline

While the multidimensional KG is used to provide semantic enriched content (Tosi & Dos Reis, 2021), the mathematical capabili- ties of LLMs are leveraged to inspect patterns and relationships in the data through a multi-source, interactive scientometric analysis  pipeline. This refers to the process of using prompt-based methods to enable these foundation models to perform scientometric tasks  such as extracting connections between entities (e.g., authors, keywords, and institutions). As described by Correia, Grover et al.  (2023), the evolutionary taxonomy that supports the specification of different layers of knowledge representation in our system  lies in a faceted search approach (Armentano et al., 2014) which comprises concepts, methods, theories, sample characteristics,  technology attributes, interventions, effects, and findings that can be inspected and correlated with certain entities and metrics.

Such a KG- and LLM-enabled entity-relation extraction environment allows users to obtain a fine-grained, multi-level quantitative  depiction of the structure and evolution of a scientific or technology field. For instance, consider the task of measuring knowledge


## 1 https://pybossa.com/.

6

A. Correia et al.

Information Processing and Management 63 (2026) 104882

exchange between disciplines and subfields of science based on bibliometric indicators (Rinia et al., 2002). The KG-based human-LLM  interactive system can function as a ‘‘partner’’ supporting users in systematically mapping cross-disciplinary trajectories. By engaging  in human-AI progressive sensemaking (Kang et al., 2023), users can iteratively guide the question-and-answer system’s bibliometric  modeling and interpretation by ensuring that measures of knowledge transfer accurately reflect the complexity and dynamics of  a scientometric exercise of this nature. Following the same logic, the proposed KG-LLM integrated solution can be tested in other  scientometric tasks such as predicting technology convergence (Li et al., 2025), investigating scientific communication patterns on  social media (Ye et al., 2025), and measuring the effects of funding policies (Ou et al., 2024).

Using this AI-mediated human-information interaction approach, which is grounded in Marchionini (2008)’s theoretical ap- praisal, the system can act as a funding ‘‘advisor’’ for policymakers seeking to identify gaps in the literature and prioritize areas  requiring further investment. It can also function as an ‘‘assistant’’ able to provide answers about the novelty factor of a certain  technology based on the number of patent citations it has received over the years, or even as a ‘‘chain’’ where the LLM helps to  break down a complex problem into smaller subtasks (Wu et al., 2022). Regarding the latter, a chain-of-thought linked knowledge  approach enabling the systematic extraction and quantification of precise scientometric data from varied sources can be used to  adjust the depth of the KG and its networks dynamically. This chain of interactive linkage of entities and metrics also contributes  to improve the information traceability system.

From a human–computer interaction (HCI) viewpoint, the use of metaphors such as those illustrated above can impact pre-use  expectations and post-use evaluations of a human-AI system (Khadpe et al., 2020). Moving to the meta-level, they can shape the way  in which users create their mental models about the outcomes of the scientometric analysis process considering the model’s ability to  capture context and provide fine-grained insights. Although the field of information science has not extensively explored conceptual  metaphor theory (Lakoff & Johnson, 1980) and its implications for human-AI interaction, several lessons from HCI findings could  be drawn and incorporated into the design and implementation of applications that comprise these interactive features.


## 4. Illustrative use case supported by literature-based experimental evidence

This section describes the experimental setting used to benchmark the proposed KG-LLM integrated framework, including the  datasets and baseline methods used for comparison. To demonstrate the practical applicability of the framework, we present an  evidence-based illustrative use case in the context of author name disambiguation, a longstanding challenge in information science  that occurs when distinct authors share the same or similar names and/or when a single author is represented by multiple name  variants (Rodrigues & Ralha, 2026). From a scientometric point of view, what makes this apparently simple problem complex is  the rich interplay of metadata inconsistencies. Similar forms of ambiguity extend beyond author names to related entities such  as institutions, venues, funding agencies, and concepts. As a result, scientometric tasks such as estimating an author’s publication  output within a given time frame or answering more complex queries (e.g., the prompt illustrated in Fig. 2) are prone to error when  disambiguation is not adequately addressed.

Traditional author name disambiguation approaches rely on supervised learning or rule-based techniques over structured  metadata, whereas recent LLM-based methods leverage semantic modeling capabilities but are susceptible to hallucination, limited  reproducibility and reasoning depth, and lack of structural grounding (Yan et al., 2024). The proof-of-concept use case presented  here demonstrates how the proposed framework can be operationalized in a realistic information processing scenario. This validation  approach has been used in the field of information science to demonstrate, for example, the feasibility of multi-label learning  algorithms in text categorization (Al-Salemi et al., 2019).

4.1. Source data and experimental setup

To demonstrate the value of KG-LLM integration, results were compared across four categories of methods reported in the  literature: (i) crowdsourcing-based approaches (human baseline) (Correia, Guimarães et al., 2023; Correia et al., 2021), (ii) graph  neural network (GNN) models (Zhang et al., 2023), (iii) traditional heuristic-based machine learning (ML) methods (Kim &  Kim, 2024), and (iv) LLM-based approaches that either incorporate KGs or operate independently of them, with our framework  representing an integrated solution for scientometric inquiry validated using datasets from Sancheti et al. (2024) and Zhang et al.  (2024). Performance metrics are taken directly from the source publications, following a validation strategy adopted in prior  work (e.g., Xiong et al., 2025). Table 2 summarizes the datasets used as the experimental ground truth for our illustrative use  case. These datasets range from small-scale human-curated sets to million-scale KGs.

LLM Web Profile Corpus. A web-scraped collection of researcher profiles used to evaluate LLM-based attribute extraction.  It includes 500 distinct names and 14 multi-valued attributes (e.g., education, affiliation history, and research interests). Results  from Sancheti et al. (2024) demonstrate that hallucination rates increase with profile complexity and prompt depth when using  GPT-3.5.

OAG-Bench. A multi-faceted, fine-grained benchmark built on the Open Academic Graph (OAG) that integrates data from the  Microsoft Academic Graph (MAG) and AMiner. The benchmark serves as the primary dataset for testing LLM (ChatGLM-6B) vs.  GNN performance and comprises over one million publication records. It further includes PST-Bench (2141 labeled papers) and  CCKS2021-En (9221 scholar profiles) and employs the WhoIsWho dataset for supervised evaluation. Zhang et al. (2024) report that  ChatGLM-6B achieves a mean average precision (MAP) of 79.54% on incorrect assignment detection tasks, outperforming GNN-based  baselines (71.18%).

7

A. Correia et al.

Information Processing and Management 63 (2026) 104882


> **Table 2**

> Summary of datasets used for author name disambiguation and entity matching, including size, coverage, entity type, and the tasks for which 
each dataset was used.
 Dataset (Source)
Methodological 
aspects

Performance  indicators

Limitations

LLM Web Profile

GPT-3.5 with prefix tries (Web Profile  Corpus + Wikipedia); 500 distinct  names (common vs. uncommon)

8/10 similarity score (average) Prompt size limitations; LLM  hallucination in high-depth profiles

Corpus (Sancheti  et al., 2024)

OAG-Bench (Zhang

Zero-shot LLM (ChatGLM) vs. GNN  (Open Academic Graph) 1M+ papers,  70K+ authors, 300K+ concepts  (WhoIsWho)

77.92% AUC (ChatGML); 70.15%  AUC (GCCAD); 62.48% AUC  (GCN)

LLMs outperform KGs but struggle  with scholar profiling; hallucination;  prompt fatigue

et al., 2024)

ANDez (Kim & Kim,

2024) Random Forest; 6000 ambiguous  names

∼93% F1-score  (Classification)

Black-box classification; high  dependency on pre-labeled ‘‘gold  standard’’ data

LAGOS-AND (Zhang

TF-IDF + GNN  (ORCID + DOI + Microsoft Academic  Graph) 7.5M citations, 798K authors

97.56% F1-score  (Pairwise matching)

KG’s internal ID system achieved  ∼82% F1-score; clustering failures;  missing semantic links

et al., 2023)

NG-CrAI (Correia,

TF-IDF/BERT + Human  (Crowdsourcing); 48 documents,  pairwise comparisons

<50% accuracy for 2 out of 4  complex tasks

Crowdsourcing is too slow and costly  for large datasets; human (crowd)  fatigue

Guimarães et al.,  2023)

AuthCrowd (Correia

Human (Crowdsourcing); 24  participants, 8 disambiguation tasks

>75% mean accuracy on human  intelligence tasks (HITs)

Errors in article viewer interface  hindered human performance;  character noise; visual overlap; human  (crowd) fatigue

et al., 2021)

ANDez. A curated dataset designed to evaluate the transparency of traditional ML pipelines involving Random Forest algorithms.  It comprises 6000 ambiguous author names with associated bibliographic metadata (e.g., paper identifiers, publication year, venue,  author names, titles, instance IDs, and affiliations). The benchmark demonstrates that code sharing and standardized preprocessing  are critical for mitigating black-box effects in author name disambiguation.

LAGOS-AND. A ‘‘gold standard’’ dataset built by leveraging links between ORCID and DOI and validated against the MAG across  six facets: year, position, gender, ethnicity, name popularity, and domain. It supports both clustering (i.e., LAGOS-AND-BLOCK) and  pairwise classification (i.e., LAGOS-AND-PAIRWISE) and highlights recall limitations in KG-only approaches.

NG-CrAI. A controlled dataset of disambiguation tasks comprising publications from four renowned authors in the field of HCI.  It is divided into groups to evaluate cross-document similarity. The dataset provides ground truth for assessing the limitations of  BERT and TF-IDF in cases involving institutional changes and other sources of author ambiguity.

AuthCrowd. A dataset of publicly available peer-reviewed publications used to benchmark human performance as a baseline.  Experiments involving 24 participants highlighted limitations in performing HITs for author name disambiguation, including errors  arising from visual overlap and cognitive load.

These datasets provide the source data and baselines for our illustrative use case. The walkthrough focuses on the entity matching  components of the pipeline within the context of author name disambiguation, which are central for scientometric inquiry. It is  important to note that the datasets and metrics presented in Table 2 represent a synthesis of methodological approaches used in  previous research.

Because these studies employ heterogeneous metrics (e.g., QUIS for user satisfaction vs. AUC for classification), they are not  intended for direct comparison. Rather, we utilize these indicators as circumstantial evidence to map the performance plateaus  inherent in each isolated approach. Direct comparisons are strictly limited to cases where homologous metrics are available. While  the numerical values in Table 2 originate from diverse methodological systems, they collectively illustrate a three-way bottleneck:  algorithmic approaches are precise but rigid, generative systems are fluent but hallucinatory, and human-based approaches are  accurate but unscalable.

4.2. Evidence-based experimental results

The illustrative use case is grounded in limitations and errors reported in prior literature, including results from our own previous  experiments. We also consider the potential for generalization to other pipeline components and discuss broader implications of KG- LLM integration for complex scientometric tasks. The prompt illustrated in Fig. 2 serves as an example of how mitigating semantic  overlaps at the author level can improve the overall outcome. A pilot study was designed to test the following two hypotheses (H):

H1: A KG-LLM human-in-the-loop framework offers a more robust mechanism for identifying semantic anomalies in bibliographic  data than traditional approaches.

H2: Integrating KGs with LLMs may help mitigate current limitations at the author name disambiguation level compared with  crowdsourcing, KGs, and LLMs used in isolation.

8

A. Correia et al.

Information Processing and Management 63 (2026) 104882

To evaluate these hypotheses, we synthesize evidence across multiple performance dimensions. It is important to clarify that  these metrics serve as indicators of the limitations inherent to each approach rather than as a direct performance comparison, as  heterogeneous quantitative and qualitative data cannot be objectively ranked on a single scale.

While GNN-based methods achieve high structural recall, they lack the semantic nuance required to resolve complex disambigua- tion. While human experts provide a high-accuracy baseline, they are susceptible to cognitive fatigue (as evidenced by the QUIS  scores in AuthCrowd). The proposed hybrid framework is specifically designed to bridge these non-homologous gaps. Consequently,  the following analysis treats these disparate metrics as circumstantial evidence of paradigm-specific limitations rather than as direct  benchmark comparisons.

Bibliometric-enhanced IR. As a preprocessing step, we considered the 7.5 million citations from LAGOS-AND, normalized  through Unicode decoding and alphanumeric filtering as suggested by Kim and Kim (2024). Prior studies show that human accuracy  in author name disambiguation can be affected by interface complexity and task duration. For instance, Correia et al. (2021)  reported low satisfaction (QUIS score: 3.17/5.0) due to difficulties associated with reading text on the screen, with accuracy  dropping to 17%–25% for complex tasks in a specific subset. This finding is corroborated by Correia, Guimarães et al. (2023), who  observed fluctuations in task accuracy ranging from 16.67% to 70.83%. These experiments allowed to detect limitations related to  confusion over institutional change, time constraints, unpredictability of user actions, lack of flexibility, and costs incurred through  outsourcing HITs. Altogether, the reported findings indicate that crowdsourcing approaches (human baseline) do not scale to large  scientometric datasets (e.g., millions of records). A pipeline that uses LLMs to normalize author names (and other entities) into a  single canonical form prior to KG construction can mitigate semantic ambiguity and errors that reduced human accuracy by ∼15%  in earlier AuthCrowd experiments.

Faceted KG construction. Zhang et al. (2023) reported that the standard MAG author identification system achieved a precision  of 98.82% but a comparatively low recall of 70.16%. This result indicates that KG-only approaches are accurate when a match is  found, but they fail to recover ∼29.84% of an author’s publications because the KG lacks the flexibility to link heterogeneous  metadata nodes (e.g., name variants or changes in institutional affiliation). The authors further note that black-box systems do  not capture nuanced name variations, resulting in approximately 9%–12% of missed matches. Rather than relying solely on name  matching, KGs encode semantic relationships (e.g., Author A → affiliated with Institution B → publishes in Topic C). By leveraging  these relational links to bridge heterogeneous nodes, publications missing from the KG can be represented in a more structured  manner, thereby improving recall rates.

Advanced graph-based methods such as Graph Convolutional Networks (GCN) and Graph Contrastive Coding for Anomaly  Detection (GCCAD) leverage the topological structure of the KG. In the experiments conducted by Zhang et al. (2024), GCN achieved  an AUC of 62.48% whereas GCCAD achieved 70.15%. Although these models effectively capture structural proximity, they remain  limited in their ability to detect semantic anomalies in assignment detection. Consequently, their performance plateaus because  they rely exclusively on metadata (e.g., co-authorship networks and publication venues) rather than the semantic content of the  papers themselves. We argue that this limitation can be addressed by incorporating LLM-based processing. Integrating KGs and LLMs  enables enforcement of the structural constraints defined in LAGOS-AND while simultaneously leveraging the semantic processing  capabilities demonstrated in OAG-Bench without incurring the scalability costs associated with AuthCrowd and NG-CrAI.

LLM chains for disambiguation. Experiments conducted on the ANDez and LAGOS-AND datasets demonstrate that current ML  and heuristic-based approaches reach a ‘‘glass ceiling’’—defined as the model’s limited ability to move beyond pattern matching  toward genuine reasoning or the point at which additional data or computational resources no longer yields performance gains—of  approximately 70%–93% F1-score due to limited semantic understanding. In contrast, OAG-Bench shows that LLMs can outperform  KGs in capturing complex correlations, achieving a mean average precision of 79%. However, a 77.92% AUC appears to represent  the performance ceiling for black-box LLMs.

Despite the capability of LLMs to cross-reference attributes, the data presented in Sancheti et al. (2024) further demonstrate that  their performance declines as the size of the input prompt increases. LLM chains can mitigate the performance ceiling identified  by Zhang et al. (2024) and prevent the generation of ‘‘ghost references’’ (i.e., citations to non-existent publications (Orduña-Malea  & Cabezas-Clavijo, 2023)) and other hallucinated outputs by grounding data processing in a KG. This has also been proved for  other crowd-based workflows (e.g., Grunde-McLaughlin et al., 2025), where complex tasks can be decomposed into a sequence of  subtasks. At this level, a KG-LLM integrated framework uses the KG to address the recall problem of LAGOS-AND and the LLM to  address the correlation limitations of OAG-Bench.

Adaptive HITL Verification. Here, humans supervise the LLM’s decisions in the most ambiguous cases. Correia, Guimarães et al.  (2023) demonstrated that humans can achieve less than 50% accuracy on complex tasks due to being overwhelmed by side-by-side  PDF viewers. That is, under high cognitive load, performance declines. By presenting humans with KG-LLM generated evidence  (e.g., ‘‘These two papers both share the subtopic node ‘Gastro-surgical wearable assistants’ found in the KG’’), humans may provide  rewards or penalties (Yes/No) and contribute to improving task accuracy based on explainable AI techniques (for a more detailed  perspective on how explainability is framed within our interactive scientometrics framework see Saarela et al. (2025)). Consequently,  KG-LLM optimization can mitigate the cognitive overload and accuracy drop identified by Correia et al. (2021) at the level of  human-interpretable disambiguation decisions.

An integrated KG-LLM framework is experimentally grounded in this proof-of-concept use case as a convergence of these  methodologies. The literature-based experimental analysis supports the claim that a hybrid approach of this nature is not merely a  theoretical enhancement but a requirement to move scientometrics beyond the current performance plateaus found in the literature.  The cross-examination of data shed light on the hypotheses we investigate here. Humans alone are inefficient at processing data at  large scale and are prone to errors in complex scientometric tasks (Correia et al., 2021), while LLMs introduce hallucinations, recall

9

A. Correia et al.

Information Processing and Management 63 (2026) 104882

gaps, and lack of traceability regarding the sources used (Sancheti et al., 2024). In practice, LLM effectiveness diminishes as input  data grows, increasing the risk of hallucinations. They also lack contextual information and structural foundation for integrating  heterogeneous data (Zhang et al., 2024). While KGs provide the necessary structure to prevent hallucinations, they are too rigid  to capture entity nuances (e.g., author names), requiring the semantic processing capabilities of LLMs to achieve high accuracy in  tasks such as author name disambiguation. Therefore, an integrated framework combining KGs and LLMs can mitigate issues such  as those reported using OAG-Bench and ANDez.

4.3. Proof-of-concept walkthrough

To demonstrate the practical validity of the proposed framework, we conducted a walkthrough using the query presented  in Fig. 2. This proof-of-concept use case tests the ability of KG-LLM integration to handle author name disambiguation and  bibliometric-enhanced IR, two areas where standalone KGs and LLMs often fail.

LLM-based prompting. When querying GPT-4o via standard interface search, the LLM generated a coherent narrative but failed  in terms of precision. While it identified ‘‘Singapore General Hospital’’ and ‘‘National University Hospital’’ as key institutions, it  hallucinated citations to support the claim. For instance, the LLM cited a ghost reference titled ‘‘Smart Wearables in Minimally  Invasive Surgery’’ by Tan and Lim (2023). A cross-check on Scopus revealed that this paper does not exist and that the LLM had  conflated real authors (J. Tan is a surgeon in Singapore) with a title based on probabilistic word association.

KG inspection. For the purpose of this walkthrough, we utilized OpenAlex as the representative KG baseline, as it serves as an  active successor to the MAG/OAG structure used in prior benchmarks. We performed a simple search via the OpenAlex API using  the Boolean filtering logic implemented in the Python script below:


## 1 def get_real_openalex_data():

2 base_url = " https://api.openalex.org/works "

3

4 filters = (

5 " concepts.display_name:Wearable technology , "

6 " institutions.country_code:SG, "

7 " from_publication_date:2022-01-01 "

8 )

9

Unlike the LLM baseline, every record corresponded to a verifiable Digital Object Identifier (DOI), reducing the risks of  hallucination (i.e., ghost references). The search identified high-frequency authors with Singaporean affiliations but lacked the  semantic resolution to filter by specific clinical department. A critical instance of this ambiguity was the retrieval of ‘‘L. Wei’’,  an author in the wearables domain. The KG failed to differentiate between Lei Wei (a computer scientist at Nanyang Technological  University focusing on wearable sensors for construction safety) and L. Wei (a biomedical engineer at the National University of  Singapore working on surgical haptics). Lacking the semantic analysis capabilities of LLMs, the KG conflated these distinct identities  based on the shared ‘‘wearable’’ keyword and ‘‘Singapore’’ location. This confirms the high recall but low precision results reported  in previous studies when KGs are used in isolation, as they remain unable to filter authors based on the specific semantic nuances  of a clinical gastro-surgery context.

Hybrid KG-LLM approach. When using the LLM as a ‘‘parser’’ for prompt decomposition, the LLM can act as a ‘‘scientometric  agent’’ able to decompose the query into structured triples while linking terms to KG entities and semantic categories. Therefore,  the key differentiator of the proposed framework lies in how it sequences the complementary strengths of probabilistic reasoning  (LLMs) and deterministic retrieval (KGs). As demonstrated in the L. Wei test case, the logic operates hierarchically since the LLM  first functions as a semantic parser, decomposing the query into ontological structures (e.g., Context: Gastro-surgical vs. Concept:  Wearable Technology).

In the subsequent retrieval phase, the hybrid KG-LLM approach is designed to address the KG’s limitations at the semantic  level by applying an LLM-driven contextual verification. For instance, when the KG retrieves a false positive profile driven by  keyword overlap, the disambiguation module detects a semantic misalignment between the clinical context behind the query and  the candidate’s research profile. By automatically rejecting the false candidate, the framework aims to minimize the contamination  of the final output. Consequently, the generative module is constrained to synthesize the data based exclusively on a verified subset  of entities. This contributes to prevent possible ghost references observed in the standalone LLM baselines while achieving the  granular precision missed by the standalone KGs.

This approach was recently explored by Aggarwal et al. (2026) who claimed that LLMs can build ontologies of research topics  by leveraging distinct zero-shot prompting strategies. However, as noted in their study, zero-shot generated outputs often lack  the relational structure required for reliable retrieval-augmented generation (RAG). Our framework addresses this limitation by  sequencing the LLM’s probabilistic parsing with deterministic KG retrieval. This ensures that the ontological structures identified  are not merely plausible linguistic constructs but are verified against the relational constraints of the underlying KG and anchored  in metrics that provide additional context to the overall user experience. Our framework also addresses the gap identified  by Abbasiantaeb et al. (2025) regarding static science-technology linkages which do not allow the search process to become more  interactive and error-resistant for non-expert users. Our proposed framework bridges this gap by proposing the use of LLMs as  hierarchical semantic parsers that cross-reference the probabilistic reasoning of foundation models with the deterministic accuracy  of KGs.

10

A. Correia et al.

Information Processing and Management 63 (2026) 104882

4.4. Threats to validity

Although literature-based validation provides a useful benchmark source to assess the robustness of a KG-LLM integrated  framework, it remains limited by the scope of studies selected for comparison. The chosen papers focus primarily on author name  disambiguation, leaving other complex scientometric tasks underrepresented. While our comparative analysis of reported results  provides a lens through which to evaluate the benefits of KG-LLM integration, we recognize that the framework would benefit from  further validation on different scientific corpora and datasets such as SciSciCorpus (Shao et al., 2025) and SciSciNet (Lin et al.,  2023). We also acknowledge that direct comparisons with existing hybrid KG-LLM approaches would provide additional context for  evaluating the effectiveness of our framework. Rigorous empirical evaluation is necessary to assess the robustness of the tri-state  disambiguation logic when operating on non-curated bibliographic data streams with inconsistent metadata.

The framework’s reliance on KGs introduces another potential limitation. If the underlying KG contains erroneous or incomplete  information, the LLM may confidently generate inaccurate outputs, particularly for scientometric tasks requiring high precision such  as tracing paper sources and impact indicators. Moreover, the effectiveness of the generative component is highly sensitive to prompt  design. Minor variations in user queries can yield differing results, potentially affecting reproducibility and consistency.

Performance also depends on the quality and up-to-dateness of the pre-trained LLM. Biases in training corpora or gaps in domain  coverage can subtly influence contextual insights, echoing concerns about model opacity and inability to capture entanglements of  data transformations. Similarly, KG coverage varies by discipline and models trained on one domain may perform suboptimally  when applied to another, limiting cross-domain generalization.

Scalability introduces additional challenges. Although LLM chains can complement crowdsourcing techniques (human baseline),  computational demands for large bibliographic datasets remain substantial. Furthermore, standard metrics such as Precision, Recall,  and F1-score may not fully capture the qualitative value of contextual enrichment. This also applies to what Nunkoo and Thelwall  (2026) describe as the lack of a Global South strategy in research evaluation capable of addressing the limitations of traditional  citation-based indicators, which often overlook priorities in developing countries.

These considerations highlight that while the proposed KG-LLM framework demonstrates practical utility and scalable insight  generation, outcomes should be interpreted with caution since broader generalization across data-intensive tasks remains uncertain.  While full generalization is outside the scope of this study, the results support the claim that KG-LLM integration is both achievable  and useful in practice. Nonetheless, investigating alternative retrieval-augmented language models such as those examined by Asai  et al. (2026) represents an important direction for further empirical work. Future research could also explore enhanced KG  curation, more robust prompt strategies, and bibliometric-enhanced IR and assessment approaches that better reflect quantitative  and qualitative insights in complex scientometric tasks.


## 5. Discussion

From strategic innovation to funding proposals and department-based productivity assessments, contemporary public and private  decision-making increasingly depends on scientometric data to an unprecedented degree. As these indicators exert growing influence  over policy and funding priorities, the accuracy and robustness of evaluation instruments are of utmost importance. However, the  diversity of knowledge representations and views enabled by current digital libraries and scientometric applications are far from  meeting the information needs of science stakeholders. This requires a new set of AI-driven methods and approaches to improve  the process of meta-evaluating research outputs where algorithms are used not just as computational tools but as a means through  which users can discover new ideas and capture useful insights while finding connections and patterns.

In this section, we revisit the emerging generative capabilities of AI for information science and cross-disciplinary research to  contextualize the proposed solution in light of current human-centered AI developments. Drawing on both theoretical and practical  assumptions from the field of scientometrics, we interpret our findings in relation to our RQs and hypotheses as supported by the  AI and HCI literature.

5.1. Opportunities, risks, and threats of LLMs in information science

In scientometrics, the increasing use of AI is steadily automating key tasks traditionally managed by human experts, such as  citation analysis and publication channel classification. One prominent example is the automation of journal quality assessment,  which offers advantages like faster, scalable, and potentially more objective alternatives to conventional methods (Chatrinan et al.,  2025; Daud et al., 2015; Hassan et al., 2018). These AI-driven approaches address long-standing limitations of citation metrics, which  often reflect discipline-specific inequalities: fields like social sciences and humanities, for instance, struggle to compete with natural  sciences due to language barriers and differing publication practices (Hicks et al., 2015; Kulczycki et al., 2018; Sivertsen, 2016).  Expert-based rankings, while valuable, remain costly, subjective, and susceptible to biases or conflicts of interest, particularly when  evaluating niche or non-English language publications (Dondio et al., 2019; Haddawy et al., 2016; Saarela et al., 2016). However,  despite the promise of AI-based methods, challenges persist in capturing disciplinary differences effectively, and it remains unclear  how best to incorporate these variations into automated assessments (Saarela & Kärkkäinen, 2020).

Over time, scientometric analyses have evolved from simple, transparent statistics to more complex, opaque AI-driven systems.  Initially dominated by basic metrics, the field progressively adopted linear models, then non-linear ML techniques, which—despite  improving predictive performance—introduced challenges around interpretability. Now, with the rise of LLMs such as GPT-4 and  Llama 3, the situation has become even more complex. While these models offer powerful new opportunities for scientific knowledge

11

A. Correia et al.

Information Processing and Management 63 (2026) 104882

synthesis (Asai et al., 2026), literature review automation (Schmitt, 2025), trend analysis (D’aquin, 2025; Gu & Krenn, 2024; Tsaneva  et al., 2025), citation context analysis (Nishikawa & Koshiba, 2024), and taxonomy alignment (Cui et al., 2024), they also carry  significant risks (Annepaka & Pakray, 2025; Marchesin et al., 2025). Chief among these is their black-box nature, which makes it  difficult to trace or explain how specific conclusions are reached. For instance, when applying inclusion and exclusion criteria in  systematic reviews, LLMs may introduce biases due to ambiguous instructions, incomplete context, or the non-deterministic behavior  of the models themselves (Schmitt, 2025). While human raters are similarly subject to biases and inconsistencies (Brereton et al.,  2007; Južnič et al., 2010; Saarela & Kärkkäinen, 2020), the opacity of LLMs can amplify these issues, posing additional risks in  contexts requiring transparency, fairness, and accountability (Pan et al., 2024; Saarela, 2024).

5.2. How to optimize the research process in information science using KGs, LLMs, and scientometrics?

LLMs alone fall short for coping with the semantic relationships of scientometric inquiry. One potential solution to mitigate the  black-box nature of LLMs is the integration of KGs (Phan & Do, 2025), which can provide external knowledge for inference and  improve model transparency. By grounding LLMs in structured knowledge, KGs can offer a more interpretable and explainable basis  for their predictions, enhancing the interpretability of the results. This approach allows LLMs to access rich, structured data that can  guide their reasoning and provide additional context for their outputs, making the decision-making process more transparent (Pan  et al., 2024). The combination of KGs, LLMs, and scientometrics holds promise for advancing the field of information science by  not only improving the accuracy of analyses but also making the underlying processes more accessible and accountable.

Some studies have already documented the beneficial effects of using KGs in scientometric tasks such as patent information  analysis (Lu et al., 2024) and objective evaluation of venues (Lackner et al., 2021). A key question for any such system is which  scholarly KGs to use. The discontinuation of MAG in 2021 removed one of the most comprehensive open resources available to  the field (Chawla, 2021). As shown in Table 1, recent studies have explored domain-specific, custom-built, and emergent KGs  such as OpenAlex to fill this gap. However, no single KG offers a universally optimal solution. Each has its own strengths and  limitations, depending on the specific task at hand. Moreover, constructing and maintaining high-quality KGs remains inherently  difficult, as emphasized by Zhong et al. (2023), with effectiveness often hinging on the scope, granularity, and currency of the  knowledge captured. The decision of which KG to incorporate is therefore central to the accuracy, interpretability, and overall  utility of AI-driven systems for information science and cross-disciplinary research.

5.3. Making information science research more interactive: Four lessons from HCI research

The HCI community has long been demonstrating that we can use HITL-based techniques to combine AI and human inputs at a  large scale, allowing humans to fix inconsistencies and validate results while enhancing query answering and explainability (Y. Liu  et al., 2025). LLM prompt controllers and databases continue to evolve to support task decomposition and generation interfaces for  purposes ranging from evaluating AI-powered technologies as objects of study to using AI personas with different traits to act as  participants in human behavior experiments (Pang et al., 2025). The capacity of LLMs to work with data as search engines are diverse  and the interactive nature of the navigation experience in LLM-based environments highlights the potential uses of this technology in  information science. However, threats arise from the emergence of ghost references in citation function classification (Orduña-Malea  & Cabezas-Clavijo, 2023), as LLMs typically need domain-specific fine-tuning to accurately interpret citation contexts (Chatrinan  et al., 2025). From a human-centered AI perspective, there is a series of takeaways that can offer guidance to information science  scholars, practitioners, and/or end-users intended to explore the interactive capabilities of human-AI systems.

The growing complexity and multidimensionality of research outputs call for a more dynamic, content-driven faceted search  approach. By integrating interactivity into information science applications enabled by KG/LLM-knowledge query and visualization,  it becomes possible to move beyond simple consumption of metrics in a passive manner toward an active engagement with the data.  However, a lack of trust in AI-generated content can result in critical failures in terms of technology acceptance and adoption (Choung  et al., 2023). Researchers have made several attempts to understand the emotional effects of incorporating anthropomorphic features  into AI systems with perceived risks detected at the autonomy and privacy levels as an outcome of over-reliance (Akbulut et al.,  2024). Regarding the factors underlying sensitivity to prompt design, the lack of transparency in prompt engineering can be detrimental  to system operation and result in bottlenecks, hallucinations, and biases. Because minor variations in prompt syntax can yield  divergent results, a standardized structure for scientometric prompts may help address the challenge of stochastic reproducibility  which constitutes a significant barrier to the adoption of LLMs in scientometric inquiry. By versioning prompt templates alongside the  KG schema, the system can ensure that the semantic lens through which the scientometric data are processed and visualized remains  constant, even if the underlying model is updated. Moreover, interaction design approaches—such as error exposure, lightweight  factuality checks, explainability, source provenance display, and feedback mechanisms—can play a critical role in enhancing trust in  AI-generated suggestions and insights (Subramonyam et al., 2022). Such strategies may contribute to the detection of hallucinations  in LLM answers (Heo et al., 2025), improving reliability and completeness while maintaining appropriate governance and oversight.

HCI research underscores the value of designing for inclusivity, adaptability, and personalization (Torkamaan et al., 2024). In  line with this, human-centered AI interactive approaches can foster more nuanced interpretations by adapting the AI system to the  preferences and characteristics of each user. For instance, information science research can adopt a human-centered, participatory  design approach to better reflect the actual workflows, goals, and needs of different types of users. Research on progressive

12

A. Correia et al.

Information Processing and Management 63 (2026) 104882

sensemaking shows how interactivity facilitates iterative exploration (Kang et al., 2023; Suh et al., 2023), with implications for contexts  where scientometric data must support information science and cross-disciplinary research.

As we see advancements such as AI training itself to comprehend multimodal content through the use of auxiliary metadata  and labels, interaction-as-dialogue (Hornbæk & Oulasvirta, 2017) can be considered a key paradigm for the realization of effective  research-based knowledge evaluation in information science. Going back to conceptual metaphor theory (Lakoff & Johnson, 1980),  we recognize the value of emerging prompting techniques such as recursive metacognition, recently explored by Zhang et al. (2025).  This technique leverages inference-time scaling to enable LLMs to reason e.g. as a ‘‘team of experts’’ by decomposing prompts into  snippets that can be recursively inspected. The logic behind recursive language models is of practical value for scientometric inquiry,  as it leverages fine-grained faceted search. In light of this new enlarged agenda, the field can benefit from an innovative KG-LLM  integrated framework where both humans and AI contribute meaningfully and actively during the research process.

5.4. Critical challenges and barriers in implementing a human-centered KG-LLM integrated framework for scientometric inquiry

RQ1 sought to determine how KGs and LLMs can be integrated to support context-aware scientometric inquiry. Our multidi- mensional framework contributes to this effort by exploring the use of KGs as the deterministic ‘‘scaffold’’ for the probabilistic  processing chains of LLMs. The comparative benchmark analysis and experimental setting illustrate the potential of the proposed  framework, aligning with the conceptual premise of H1. As Huo et al. (2022) demonstrated with their bibliographic KG, the co- evolution of entities (e.g., authors, topics, and venues) holds predictive value beyond what conventional methods based solely on  static natural language processing can achieve. However, while KGs provide structure and fact-check sources, they lack semantic  flexibility. On the other hand, LLMs provide unique generative capabilities—as evidenced by mainstream LLMs such as GPT-4 and  Llama-2 (Liu et al., 2024)—but still struggle with generating precise structured outputs required for rigorous data analysis. Therefore,  our framework demonstrates the logic underlying H1 by integrating LLM-based semantic interpretation with KG-based affordances  to mitigate hallucination effects within this proof-of-concept context. By injecting the KG’s triples directly into the prompt context,  the model is instructed to return an output only using the provided triples. This mirrors the findings of Yan et al. (2024), where an  integrated approach combining LLM tuning with tree-based models significantly outperformed standalone methods in author name  disambiguation. Similarly, Shao et al. (2025) introduced SciSciGPT, a multi-agent system that validates our architectural proposal.  Complex scientometric workflows require specialized agents orchestrated to bridge the gap between unstructured user intent and  structured scholarly data.

RQ2 inquired whether a human-in-the-loop KG-LLM approach helps to handle common bibliometric errors. Although further  analyses are necessary to provide definitive answers to both RQs and to validate the hypotheses, the observations from this  walkthrough are consistent with the expectations of H2, suggesting that this integrated workflow shows promise in mitigating  hallucinations and semantic ambiguity compared to standalone methods in the evaluated scenarios. LLMs are prone to being  ‘‘stochastic parrots’’, generating plausible but incorrect citations. Formanek (2025) describes this phenomenon as a critical threat to  information science in the sense that LLMs can summarize text but may also generate fabricated DOIs or misinterpret user intent in  the absence of external validation. By grounding the generative component in the KG’s verified triples, the framework demonstrates  a viable pathway for restricting the LLM’s search space to existing entities, underscoring the need for an implementation mechanism  to mitigate the creation of ghost references and other forms of misleading information.

Thelwall et al. (2025) found that while ChatGPT correlates well with expert quality scores in many fields, it negatively correlates  in clinical medicine and systematically undervalues research in prestigious medical journals. This suggests that LLMs possess inherent  domain-specific biases that cannot be solved by prompting alone. Our HITL approach addresses this issue by enabling human  intervention when the system’s confidence is low (e.g., in high-stakes medical disambiguation), a necessity underscored by Thelwall  and Kurt (2025) who argue that LLMs should support rather than replace expert judgment due to their inherent opacity.

While the proposed framework is intended to mitigate specific shortcomings of standalone AI models, its implementation  introduces distinct challenges that must be acknowledged. A possible scenario of reduced effectiveness involves scientific domains  characterized by rapid semantic shifts and highly polysemous terminology. From a topic evolution view (see Chen et al. (2018)  for a detailed appraisal of topic- and context-level shifts), the framework may struggle to reconcile the static nature of a KG  with the evolving dynamics of scientific topics. Even with KG-based structuring, the generative component remains susceptible  to the inherent biases of the underlying LLM and its limited ability to process shifts that extend beyond simple lexical variation.  If disciplinary metadata are not explicitly encoded in the KG schema (i.e., sub-graphs), the LLM’s semantic interpretation may  hallucinate links between unrelated concepts. This limitation can force the framework to rely excessively on HITL oversight and  therefore increase the cognitive load when resolving deeper ontological conflicts that neither the KG nor the probabilistic model  can adjudicate independently.

Thelwall and Kurt (2025) note that LLM-based evaluations are biased by publication year (favoring newer articles), abstract  length, and first-author country. In line with this, Thelwall (2025) warns that the integration of LLMs into research evaluation  introduces an imbalanced incentive system where authors might eventually optimize abstracts to be ‘‘LLM-friendly’’ rather than  scientifically rigorous. The author goes even further by arguing that because LLM scores are opaque and ephemeral (changing with  model updates), they do not adhere to the transparency principles of the Leiden Manifesto unless strictly used as ‘‘assistants’’ in  decision-making.

ML techniques have been utilized to show that retraction features change over time (J. Liu et al., 2025). If the KG contains  erroneous nodes (e.g., retracted papers), the LLM may generate a narrative validating such findings. Unlike ‘‘stochastic’’ hallucina- tions which are random, these would be hallucination errors supported by the graph structure, making them significantly harder for

13

A. Correia et al.

Information Processing and Management 63 (2026) 104882

human users to detect. A static LLM operating within our framework might fail to capture these evolving temporal dynamics unless  continuously retrained or updated. A profound systemic risk is highlighted by Hao et al. (2026), who analyzed 41 million papers  to find that AI tools paradoxically lead to a ‘‘contraction’’ of collective scientific focus. AI-augmented research tends to converge  on popular, data-rich topics while ignoring foundational queries that lack training data. There is a risk that our framework, by  optimizing for retrievability and connectedness in the KG, might unintentionally reinforce this dynamic by guiding users toward  certain established research paths rather than disconnected areas. This reinforces the necessity of human oversight within the loop.  Without such oversight, the system risks automating a black-box evaluation standard that is both biased and potentially detrimental.  If a framework relies on LLM embeddings for retrieval, it risks inheriting these biases while potentially sidelining older foundational  work or non-Western research.


## 6. Theoretical contributions

This study advances scientometric research by proposing a human-centered framework that integrates KG and LLM to support  context-aware and interpretable research evaluation. In doing so, it contributes to a growing body of work that conceptualizes AI  systems not merely as computational tools, but as epistemic agents shaping knowledge discovery and evaluation.

First, we extend existing scientometric theory by introducing a hybrid paradigm that combines deterministic and probabilistic  representations of knowledge. Within this framework, KG acts as a structured and verifiable scaffold, while LLM provides semantic  flexibility and generative reasoning capabilities. This integration addresses the long-standing trade-off between interpretabil- ity and predictive performance in AI-driven scientometrics, supporting recent calls for combining symbolic and sub-symbolic  approaches (Pan et al., 2024; Yan et al., 2024).

Second, our findings contribute to human-centered AI by formalizing the role of HITL mechanisms in scientometric workflows.  Rather than treating human oversight as supplementary, we conceptualize it as integral to the knowledge production process,  particularly in contexts characterized by ambiguity and domain-specific variability. This aligns with prior work emphasizing  interactive sensemaking and collaborative intelligence in AI systems (Kang et al., 2023; Y. Liu et al., 2025; Suh et al., 2023).

Third, the study advances theoretical understanding of LLM limitations in scientific contexts. By systematically examining  hallucination risks, epistemic opacity, and domain-specific biases, we reinforce concerns that LLM outputs may lack reliability  without external grounding (Annepaka & Pakray, 2025; Formanek, 2025; Marchesin et al., 2025). Our results support the argument  that hybrid KG–LLM architectures can mitigate these issues by constraining the generative space through structured knowledge.

Finally, this work contributes to cross-disciplinary research by bridging scientometrics, HCI, and AI. The proposed framework  provides a conceptual foundation for future research on interactive, explainable, and adaptive systems that support complex  knowledge evaluation tasks, particularly in light of evolving AI capabilities for scientific synthesis and analysis (Asai et al., 2026;  Schmitt, 2025).


## 7. Practical implications

The proposed KG-LLM framework offers several practical implications for the design and deployment of AI-driven scientometric  systems.

First, grounding LLM outputs in KGs is essential for improving reliability and reducing hallucinations. Practitioners should  integrate curated and task-appropriate KG resources into AI pipelines, as the choice of KG directly affects system accuracy,  interpretability, and coverage (Chawla, 2021; Zhong et al., 2023). No single KG is universally optimal, making this selection a  critical design decision.

Second, the findings highlight the importance of transparent and standardized prompt engineering. Given the sensitivity of  LLM outputs to prompt variations, version-controlled prompt templates should be maintained alongside KG schemas to ensure  reproducibility and consistency. This is particularly relevant in scientometric contexts, where stochastic variability can undermine  trust and comparability (Schmitt, 2025).

Third, HITL mechanisms should be systematically embedded into AI workflows. Rather than fully automating evaluation  processes, systems should allow for human intervention in cases of ambiguity, low confidence, or domain-specific complexity. This  is especially important given documented biases and limitations in LLM-based evaluation (Formanek, 2025; Thelwall & Kurt, 2025).

Fourth, interface and interaction design are critical for user trust and adoption. Features such as explainability tools, provenance  tracking, and feedback mechanisms can improve transparency and help users critically assess AI-generated outputs (Heo et al.,  2025; Subramonyam et al., 2022). Designing for interactive exploration rather than passive metric consumption also supports more  effective sensemaking.

Fifth, practitioners must actively address known biases in LLM-based systems, including tendencies related to publication recency  and geographic factors (Thelwall, 2025; Thelwall et al., 2025). Without mitigation strategies, these biases may distort evaluation  outcomes and influence researcher behavior in undesirable ways.

Finally, continuous monitoring and updating of both KG and LLM components is necessary to reflect the evolving nature of  scientific knowledge. Issues such as retracted publications, shifting terminology, and emerging research areas require ongoing  maintenance to prevent the propagation of systematic errors (Hao et al., 2026; J. Liu et al., 2025).

Following previous research in information science that emphasizes the need for multidimensional mappings of evidence  extending beyond high-quality representations (Liang et al., 2026), this study operationalizes a unified framework that integrates  structured knowledge representations, probabilistic language modeling, and human oversight to reconcile reliability, adaptability,  and epistemic transparency in prompt-based, interactive scientometric assessments.

14

A. Correia et al.

Information Processing and Management 63 (2026) 104882


## 8. Conclusion

In a world of rapid technological changes leveraged by the emergence of AI-based products able to automate or even outperform  human-based processing, it is paramount to have an overview of the research being conducted within a given discipline or field  to make more informed decisions. Therefore, enhancing information science research has far-reaching consequences for shaping  not only the broader trajectory of scientific discovery from one domain to another domain but also the institutional and socio- technical arrangements that guide (and are guided by) scientific activities worldwide. However, current applications have not been  incorporating such advances in a way that they can offer on-demand insights accurately.

To mitigate this, this article discusses a paradigmatic shift in the way information science studies can be conducted by proposing  the integration of prompt-based LLM techniques with large-scale scientific KGs as a means to explore evolution patterns, historical  trajectories, and socio-epistemic contexts informed by scientometric indicators and fine-grained depictions at the semantic level. The  proposed KG-LLM integrated framework is embedded in a HITL-based interactive environment where both humans and algorithms  can expand their learning and decision-making capacity while contributing to the scientometric workflow. The insights discussed  here provide practical application guidance for future developments combining hybrid approaches and evidence-based progressive  sensemaking in human-AI information seeking.

CRediT authorship contribution statement

António Correia: Writing – original draft, Writing – review & editing, Investigation, Formal analysis, Conceptualization. Mirka  Saarela: Writing – original draft, Funding acquisition. Tommi Kärkkäinen: Validation, Supervision, Resources, Funding acquisition.

Funding

This work was supported by the Research Council of Finland (project no. 356314).

Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared  to influence the work reported in this paper.

Acknowledgments

This work was supported by the Research Council of Finland (project no. 356314).

Data availability

The data that support the findings of this paper is available upon request.


## References

Abbasiantaeb, Z., Verberne, S., & Wang, J. (2025). Tracing science-technology-linkages: A machine learning pipeline for extracting and matching patent in-text

references to scientific publications. Information Processing & Management, 62(6), Article 104264. Aggarwal, T., Salatino, A., Osborne, F., & Motta, E. (2026). Large language models for scholarly ontology generation: An extensive analysis in the engineering

field. Information Processing & Management, 63(1), Article 104262. Akbulut, C., Weidinger, L., Manzini, A., Gabriel, I., & Rieser, V. (2024). All too human? Mapping and mitigating the risk from anthropomorphic AI. vol. 7, In

Proceedings of the AAAI/ACM conference on AI, ethics, and society (pp. 13–26). Al-Salemi, B., Ayob, M., Kendall, G., & Noah, S. A. M. (2019). Multi-label Arabic text categorization: A benchmark and baseline comparison of multi-label

learning algorithms. Information Processing & Management, 56(1), 212–227. Annepaka, Y., & Pakray, P. (2025). Large language models: A survey of their development, capabilities, and applications. Knowledge and Information Systems,

67(3), 2967–3022. Armentano, M. G., Godoy, D., Campo, M., & Amandi, A. (2014). NLP-based faceted search: Experience in the development of a science and technology search

engine. Expert Systems with Applications, 41(6), 2886–2896. Asai, A., He, J., Shao, R., Shi, W., Singh, A., Chang, J. C., Lo, K., Soldaini, L., Feldman, S., D’Arcy, M., et al. (2026). Synthesizing scientific literature with

retrieval-augmented language models. Nature, 650, 857–863. Azher, I. A., Seethi, V. D. R., Akella, A. P., & Alhoori, H. (2024). LimTopic: LLM-based topic modeling and text summarization for analyzing scientific articles

limitations. In Proceedings of the 24th ACM/IEEE joint conference on digital libraries (pp. 1–12). Brereton, P., Kitchenham, B. A., Budgen, D., Turner, M., & Khalil, M. (2007). Lessons from applying the systematic literature review process within the software

engineering domain. Journal of Systems and Software, 80(4), 571–583. Cadeddu, A., Chessa, A., De Leo, V., Fenu, G., Motta, E., Osborne, F., Recupero, D. R., Salatino, A., & Secchi, L. (2024). A comparative analysis of knowledge

injection strategies for large language models in the scholarly domain. Engineering Applications of Artificial Intelligence, 133, Article 108166. Chatrinan, K., Noraset, T., & Tuarob, S. (2025). GAN-CITE: Leveraging semi-supervised generative adversarial networks for citation function classification with

limited data. Scientometrics, 130, 679–703. Chawla, D. S. (2021). Microsoft academic graph is being discontinued. What’s next? Nature News, 15, (Accessed 23 April 2025). Chen, B., Ding, Y., & Ma, F. (2018). Semantic word shifts in a scientific domain. Scientometrics, 117(1), 211–226.

15

A. Correia et al.

Information Processing and Management 63 (2026) 104882

Chin, J. P., Diehl, V. A., & Norman, K. L. (1988). Development of an instrument measuring user satisfaction of the human-computer interface. In Proceedings of

the SIGCHI conference on human factors in computing systems (pp. 213–218). Choung, H., David, P., & Ross, A. (2023). Trust in AI and its role in the acceptance of AI technologies. International Journal of Human–Computer Interaction, 39(9),

1727–1739. Correia, A., Grover, A., Jameel, S., Schneider, D., Antunes, P., & Fonseca, B. (2023). A hybrid human–AI tool for scientometric analysis. Artificial Intelligence

Review, 56, 983–1010. Correia, A., Guimarães, D., Paredes, H., Fonseca, B., Paulino, D., Trigo, L., Brazdil, P., Schneider, D., Grover, A., & Jameel, S. (2023). NLP-crowdsourcing hybrid

framework for inter-researcher similarity detection. IEEE Transactions on Human-Machine Systems, 53(6), 1017–1026. Correia, A., Guimarães, D., Paulino, D., Jameel, S., Schneider, D., Fonseca, B., & Paredes, H. (2021). AuthCrowd: Author name disambiguation and entity matching

using crowdsourcing. In 2021 IEEE 24th international conference on computer supported cooperative work in design (pp. 150–155). IEEE. Correia, A., Jameel, S., Schneider, D., Paredes, H., & Fonseca, B. (2020). A workflow-based methodological framework for hybrid human-AI enabled scientometrics.

In Proceedings of the 2020 IEEE international conference on big data (pp. 2876–2883). IEEE. Correia, A., Kärkkäinen, T., Jameel, S., Schneider, D., Antunes, P., Fonseca, B., & Grover, A. (2023). A pipeline for AI-based quantitative studies of science

enhanced by crowdsourced inferential modelling. In Proceedings of the 23rd international conference on hybrid intelligent systems (pp. 291–300). Springer. Correia, A., Schneider, D., Paredes, H., & Fonseca, B. (2018). SciCrowd: Towards a hybrid, crowd-computing system for supporting research groups in academic

settings. In Proceedings of the 24th international conference on collaboration and technology (pp. 34–41). Springer. Cui, W., Xiao, M., Wang, L., Wang, X., Du, Y., & Zhou, Y. (2024). Automated taxonomy alignment via large language models: Bridging the gap between knowledge

domains. Scientometrics, 129, 5287–5312. D’aquin, M. (2025). On the role of knowledge graphs in AI-based scientific discovery. Journal of Web Semantics, 84, Article 100854. Daud, A., Ahmad, M., Malik, M. S. I., & Che, D. (2015). Using machine learning techniques for rising star prediction in co-author network. Scientometrics, 102(2),

1687–1711. Dessí, D., Osborne, F., Buscaldi, D., Reforgiato Recupero, D., & Motta, E. (2025). CS-KG 2.0: A large-scale knowledge graph of computer science. Scientific Data,

12(1), 964. Dondio, P., Casnici, N., Grimaldo, F., Gilbert, N., & Squazzoni, F. (2019). The ‘‘invisible hand’’ of peer review: The implications of author-referee networks on

peer review in a scholarly journal. Journal of Informetrics, 13(2), 708–716. Donner, P. (2024). Data inaccuracy quantification and uncertainty propagation for bibliometric indicators. Research Evaluation, 33, rvae047. Formanek, M. (2025). Exploring the potential of large language models and generative artificial intelligence (GPT): Applications in Library and Information

Science. Journal of Librarianship and Information Science, 57(2), 568–590. Grunde-McLaughlin, M., Lam, M. S., Krishna, R., Weld, D. S., & Heer, J. (2025). Designing LLM chains by adapting techniques from crowdsourcing workflows.

ACM Transactions on Computer-Human Interaction, 32(3), 1–57. Gu, X., & Krenn, M. (2024). Interesting scientific idea generation using knowledge graphs and LLMs: Evaluations with 100 research group leaders. arXiv preprint

arXiv:2405.17044. Haddawy, P., Hassan, S.-U., Asghar, A., & Amin, S. (2016). A comprehensive examination of the relation of three citation-based journal metrics to expert judgment

of journal quality. Journal of Informetrics, 10(1), 162–173. Hao, Q., Xu, F., Li, Y., & Evans, J. (2026). Artificial intelligence tools expand scientists’ impact but contract science’s focus. Nature, 649, 1237–1243. Hassan, S.-U., Safder, I., Akram, A., & Kamiran, F. (2018). A novel machine-learning approach to measuring scientific knowledge flows using citation context

analysis. Scientometrics, 116(2), 973–996. Heo, S., Son, S., & Park, H. (2025). HaluCheck: Explainable and verifiable automation for detecting hallucinations in LLM responses. Expert Systems with

Applications, Article 126712. Hicks, A. (2018). Developing the methodological toolbox for information literacy research: Grounded theory and visual research methods. Library & Information

Science Research, 40(3–4), 194–200. Hicks, D., Wouters, P., Waltman, L., De Rijcke, S., & Rafols, I. (2015). Bibliometrics: The leiden manifesto for research metrics. Nature News, 520(7548), 429–431. Hornbæk, K., & Oulasvirta, A. (2017). What is interaction? In Proceedings of the 2017 CHI conference on human factors in computing systems (pp. 5040–5052). Hou, Z.-W., Liu, X., Zhou, S., Jing, W., & Yang, J. (2024). Bibliometric analysis on the research of geoscience knowledge graph (GeoKG) from 2012 to 2023.

ISPRS International Journal of Geo-Information, 13(7), 255. Huo, C., Ma, S., & Liu, X. (2022). Hotness prediction of scientific topics based on a bibliographic knowledge graph. Information Processing & Management, 59(4),

Article 102980. Jiang, Z., Zhong, L., Sun, M., Xu, J., Sun, R., Cai, H., Luo, S., & Zhang, Z. (2024). Efficient knowledge infusion via KG-LLM alignment. In L.-W. Ku, A. Martins,

& V. Srikumar (Eds.), Findings of the association for computational linguistics: ACL 2024 (pp. 2986–2999). Bangkok, Thailand: Association for Computational  Linguistics. Južnič, P., Pečlin, S., Žaucer, M., Mandelj, T., Pušnik, M., & Demšar, F. (2010). Scientometric indicators: Peer-review, bibliometric methods and conflict of

interests. Scientometrics, 85(2), 429–441. Kang, H. B., Wu, T., Chang, J. C., & Kittur, A. (2023). Synergi: A mixed-initiative system for scholarly synthesis and sensemaking. In Proceedings of the 36th

annual ACM symposium on user interface software and technology (pp. 1–19). Khadpe, P., Krishna, R., Fei-Fei, L., Hancock, J. T., & Bernstein, M. S. (2020). Conceptual metaphors impact perceptions of human-AI collaboration. Proceedings

of the ACM on Human-Computer Interaction, 4(CSCW2), 1–26. Kim, J., & Kim, J. (2024). ANDez: An open-source tool for author name disambiguation using machine learning. SoftwareX, 26, Article 101719. Kulczycki, E., Engels, T. C., Pölönen, J., Bruun, K., Dušková, M., Guns, R., Nowotniak, R., Petr, M., Sivertsen, G., Starčič, A. I., et al. (2018). Publication patterns

in the social sciences and humanities: Evidence from eight European countries. Scientometrics, 116, 463–486. Lackner, A., Fathalla, S., Nayyeri, M., Behrend, A., Manthey, R., Auer, S., Lehmann, J., & Vahdati, S. (2021). Analysing the evolution of computer science events

leveraging a scholarly knowledge graph: A scientometrics study of top-ranked events in the past decade. Scientometrics, 126, 8129–8151. Lakoff, G., & Johnson, M. (1980). Metaphors we live by. University of Chicago Press. Li, H., Liang, H., Hu, Y., & Liu, X. (2025). Technology convergence prediction based on temporal heterogeneous graph neural networks. Information Processing

& Management, 62(3), Article 104034. Li, H., Yue, P., Tapete, D., Cigna, F., Wu, Q., Xiang, L., & Lu, B. (2024). ESDC: An open earth science data corpus to support geoscientific literature information

extraction. Science China Earth Sciences, 67(12), 3840–3854. Liang, Z., van Eck, N. J., Wu, X., Mao, J., & Li, G. (2026). Citation importance-aware document representation learning for large-scale science mapping. Information

Processing & Management, 63(3), Article 104557. Lin, Z., Yin, Y., Liu, L., & Wang, D. (2023). SciSciNet: A large-scale open data lake for the science of science research. Scientific Data, 10(1), 315. Liu, Y., Li, D., Wang, K., Xiong, Z., Shi, F., Wang, J., Li, B., & Hang, B. (2024). Are LLMs good at structured outputs? A benchmark for evaluating structured

output capabilities in LLMs. Information Processing & Management, 61(5), Article 103809. Liu, J., Wang, X., & Liang, X. (2025). Bibliometric feature identification and analysis of retracted papers in biomedicine: An interpretable machine learning

perspective. Information Processing & Management, 62(5), Article 104176. Liu, Y., Wu, Z., Dong, X., Jiang, S., & Li, W. (2025). CorrectMe: An interactive framework for human-in-the-loop correction and explanation of object detection

models. Proceedings of the ACM on Human-Computer Interaction, 9(8), 170–186.

16

A. Correia et al.

Information Processing and Management 63 (2026) 104882

Lopez, V., Hoang, L., Martinez-Galindo, M., Fernández-Díaz, R., Sbodio, M. L., Ordonez-Hurtado, R., Zayats, M., Mulligan, N., & Bettencourt-Silva, J. (2025).

Enhancing foundation models for scientific discovery via multimodal knowledge graph representations. Journal of Web Semantics, 84, Article 100845. Lu, Y., Tong, X., Xiong, X., & Zhu, H. (2024). Knowledge graph enhanced citation recommendation model for patent examiners. Scientometrics, 129(4), 2181–2203. Marchesin, S., Silvello, G., & Alonso, O. (2025). Large language models and data quality for knowledge graphs. Marchionini, G. (2008). Human–information interaction research and development. Library & Information Science Research, 30(3), 165–174. Mingers, J., & Leydesdorff, L. (2015). A review of theory and practice in scientometrics. European Journal of Operational Research, 246(1), 1–19. Mohammadi, E., Thelwall, M., Cai, Y., Collier, T., Tahamtan, I., & Eftekhar, A. (2026). Is generative AI reshaping academic practices worldwide? A survey of

adoption, benefits, and concerns. Information Processing & Management, 63(1), Article 104350. Mugaanyi, J., Cai, L., Cheng, S., Lu, C., & Huang, J. (2024). Evaluation of large language model performance and reliability for citations and references in

scholarly writing: Cross-disciplinary study. Journal of Medical Internet Research, 26, Article e52935. Natarajan, S., Mathur, S., Sidheekh, S., Stammer, W., & Kersting, K. (2025). Human-in-the-loop or AI-in-the-loop? Automate or collaborate? vol. 39, In Proceedings

of the AAAI conference on artificial intelligence (pp. 28594–28600). Nishikawa, K., & Koshiba, H. (2024). Exploring the applicability of large language models to citation context analysis. Scientometrics, 129(11), 6751–6777. Nunkoo, R., & Thelwall, M. (2026). A Global South strategy for evaluating research value with ChatGPT. Quantitative Science Studies, 1–20. Orduña-Malea, E., & Cabezas-Clavijo, Á. (2023). ChatGPT and the potential growing of ghost bibliographic references. Scientometrics, 128(9), 5351–5355. Ou, G., Zhao, K., Zuo, R., & Wu, J. (2024). Effects of research funding on the academic impact and societal visibility of scientific research. Journal of Informetrics,

18(4), Article 101592. Pan, S., Luo, L., Wang, Y., Chen, C., Wang, J., & Wu, X. (2024). Unifying large language models and knowledge graphs: A roadmap. IEEE Transactions on

Knowledge and Data Engineering, 36(7), 3580–3599. Pang, R. Y., Schroeder, H., Smith, K. S., Barocas, S., Xiao, Z., Tseng, E., & Bragg, D. (2025). Understanding the LLM-ification of CHI: Unpacking the impact of

LLMs at CHI through a systematic literature review. In Proceedings of the 2025 CHI conference on human factors in computing systems (pp. 1–20). ACM. Parinov, S., & Kogalovsky, M. (2014). Semantic linkages in research information systems as a new data source for scientometric studies. Scientometrics, 98,

927–943. Phan, T. H., & Do, P. (2025). QUERY2TREE: A reasoning model for answering logical queries based on knowledge graph embedding and large language model.

Knowledge and Information Systems, 67(6), 5271–5300. Pölönen, J., Guns, R., Kulczycki, E., Sivertsen, G., & Engels, T. C. (2021). National lists of scholarly publication channels: An overview and recommendations

for their construction and maintenance. Journal of Data and Information Science, 6(1), 50–86. Pu, K., Feng, K. K., Grossman, T., Hope, T., Dalvi Mishra, B., Latzke, M., Bragg, J., Chang, J. C., & Siangliulue, P. (2025). IdeaSynth: Iterative research idea

development through evolving and composing idea facets with literature-grounded feedback. In Proceedings of the 2025 CHI conference on human factors in  computing systems (pp. 1–31). Ramírez, J., Yu, W., & Perrusquía, A. (2022). Model-free reinforcement learning from expert demonstrations: A survey. Artificial Intelligence Review, 55(4),

3213–3241. Rinia, E., van Leeuwen, T., Bruins, E., van Vuren, H., & van Raan, A. (2002). Measuring knowledge transfer between fields of science. Scientometrics, 54(3),

347–362. Rodrigues, N. S., & Ralha, C. G. (2026). A novel framework with ComMAND: A combined method for author name disambiguation. Information Processing &

Management, 63(1), Article 104304. Saarela, M. (2024). On the relation of causality-versus correlation-based feature selection on model fairness. In Proceedings of the 39th ACM/SIGAPP symposium

on applied computing (pp. 56–64). Saarela, M., Correia, A., & Kärkkäinen, T. (2025). Explainable and interactive scientometrics with large language models and knowledge graphs. In Proceedings

of the 2025 9th international symposium on multidisciplinary studies and innovative technologies (pp. 1–6). IEEE. Saarela, M., & Kärkkäinen, T. (2020). Can we automate expert-based journal rankings? Analysis of the Finnish publication indicator. Journal of Informetrics, 14(2),

Article 101008. Saarela, M., Kärkkäinen, T., Lahtonen, T., & Rossi, T. (2016). Expert-based versus citation-based ranking of scholarly and scientific publication channels. Journal

of Informetrics, 10(3), 693–718. Safón, V., & Docampo, D. (2023). What are you reading? From core journals to trendy journals in the Library and Information Science (LIS) field. Scientometrics,

128(5), 2777–2801. Sancheti, P., Karlapalem, K., & Vemuri, K. (2024). LLM driven web profile extraction for identical names. In Companion proceedings of the ACM web conference

2024 (pp. 1616–1625). Schäfer, H., Idrissi-Yaghir, A., Arzideh, K., Damm, H., Pakull, T. M., Schmidt, C. S., Bahn, M., Lodde, G., Livingstone, E., Schadendorf, D., et al. (2024).

BioKGrapher: Initial evaluation of automated knowledge graph construction from biomedical literature. Computational and Structural Biotechnology Journal,  24, 639–660. Schmitt, V. J. (2025). Disentangling patent quality: Using a large language model for a systematic literature review. Scientometrics, 130, 267–311. Shang, B., Zhao, Y., & Liu, J. (2024). Knowledge graph representation learning with relation-guided aggregation and interaction. Information Processing &

Management, 61(4), Article 103752. Shao, E., Wang, Y., Qian, Y., Pan, Z., Liu, H., & Wang, D. (2025). SciSciGPT: Advancing human–AI collaboration in the science of science. Nature Computational

Science, 6, 301–315. Shen, S., Liu, J., Lin, L., Huang, Y., Zhang, L., Liu, C., Feng, Y., & Wang, D. (2023). SsciBERT: A pre-trained language model for social science texts. Scientometrics,

128(2), 1241–1263. Singh, P., Singh, V. K., & Piryani, R. (2023). Scholarly article retrieval from Web of Science, Scopus and Dimensions: A comparative analysis of retrieval quality.

Journal of Information Science, Article 01655515231191351. Sivertsen, G. (2016). Patterns of internationalization and criteria for research assessment in the social sciences and humanities. Scientometrics, 107(2), 357–368. Subramonyam, H., Im, J., Seifert, C., & Adar, E. (2022). Solving separation-of-concerns problems in collaborative design of human-AI systems through leaky

abstractions. In Proceedings of the 2022 CHI conference on human factors in computing systems (pp. 1–21). Suh, S., Min, B., Palani, S., & Xia, H. (2023). Sensecape: Enabling multilevel exploration and sensemaking with large language models. In Proceedings of the 36th

annual ACM symposium on user interface software and technology (pp. 1–18). Thelwall, M. (2025). Responsible uses of large language models for research evaluation. In Proceedings of the 20th international conference on scientometrics &

informetrics (pp. 71–80). Thelwall, M., Jiang, X., & Bath, P. A. (2025). Estimating the quality of published medical research with ChatGPT. Information Processing & Management, 62(4),

Article 104123. Thelwall, M., & Kurt, Z. (2025). Research evaluation with ChatGPT: Is it age, country, length, or field biased? Scientometrics, 130, 5323–5343. Thelwall, M., & Maflahi, N. (2015). How important is computing technology for library and information science research? Library & Information Science Research,

37(1), 42–50. Tibau, M., Siqueira, S. W. M., & Nunes, B. P. (2024). ChatGPT for chatting and searching: Repurposing search behavior. Library & Information Science Research,

46(4), Article 101331.

17

A. Correia et al.

Information Processing and Management 63 (2026) 104882

Torkamaan, H., Tahaei, M., Buijsman, S., Xiao, Z., Wilkinson, D., & Knijnenburg, B. P. (2024). The role of human-centered AI in user modeling, adaptation,

and personalization – Models, frameworks, and paradigms. In A human-centered perspective of intelligent personalized environments and systems (pp. 43–84).  Springer. Tosi, M. D. L., & Dos Reis, J. C. (2021). SciKGraph: A knowledge graph approach to structure a scientific field. Journal of Informetrics, 15(1), Article 101109. Tsaneva, S., Dessì, D., Osborne, F., & Sabou, M. (2025). Knowledge graph validation by integrating LLMs and human-in-the-loop. Information Processing &

Management, 62(5), Article 104145. Van De Schoot, R., De Bruin, J., Schram, R., Zahedi, P., De Boer, J., Weijdema, F., Kramer, B., Huijts, M., Hoogerwerf, M., Ferdinands, G., et al. (2021). An

open source machine learning framework for efficient and transparent systematic reviews. Nature Machine Intelligence, 3(2), 125–133. Van Raan, A. (1997). Scientometrics: State-of-the-art. Scientometrics, 38(1), 205–218. Verma, M. K., Khan, D., & Yuvaraj, M. (2023). Scientometric assessment of funded scientometrics and bibliometrics research (2011–2021). Scientometrics, 128(8),

4305–4320. Weng, X., Wang, Y., Weng, S., Xiong, J., & Weng, L. (2024). Bibliometric analysis of large language model artificial intelligence based on knowledge graph. In

Proceedings of the 2024 IEEE 9th international conference on data science in cyberspace (pp. 428–434). Wohlin, C., Kalinowski, M., Felizardo, K. R., & Mendes, E. (2022). Successful combination of database search and snowballing for identification of primary studies

in systematic literature studies. Information and Software Technology, 147, Article 106908. Wu, T., Terry, M., & Cai, C. J. (2022). AI chains: Transparent and controllable human-AI interaction by chaining large language model prompts. In Proceedings

of the 2022 CHI conference on human factors in computing systems (pp. 1–22). Xiao, Y., Li, C., & Thürer, M. (2023). A patent recommendation method based on KG representation learning. Engineering Applications of Artificial Intelligence,

126, Article 106722. Xiong, C., Zheng, G., Ma, X., Li, C., & Zeng, J. (2025). DelphiAgent: A trustworthy multi-agent verification framework for automated fact verification. Information

Processing & Management, 62(6), Article 104241. Yan, Q., et al. (2024). Synergizing large language models and tree-based algorithms for author name disambiguation. In KDD 2024 OAG-challenge cup (pp. 1–6). Yang, C., Li, C., Hu, X., Yu, H., & Lu, J. (2026). Enhancing knowledge graph interactions: A comprehensive text-to-cypher pipeline with large language models.

Information Processing & Management, 63(1), Article 104280. Ye, Y. E., Na, J.-C., & Liu, M. (2025). Examining scholarly communication on x (Twitter): Insights from participants tweeting COVID-19 and ChatGPT publications.

Scientometrics, 130, 1045–1076. Yun, S., Cho, W., Kim, C., & Lee, S. (2022). Technological trend mining: Identifying new technology opportunities using patent semantic analysis. Information

Processing & Management, 59(4), Article 102993. Zhang, A. L., Kraska, T., & Khattab, O. (2025). Recursive language models. arXiv preprint arXiv:2512.24601. Zhang, L., Lu, W., & Yang, J. (2023). LAGOS-AND: A large gold standard dataset for scholarly author name disambiguation. Journal of the Association for

Information Science and Technology, 74(2), 168–185. Zhang, F., Shi, S., Zhu, Y., Chen, B., Cen, Y., Yu, J., Chen, Y., Wang, L., Zhao, Q., Cheng, Y., et al. (2024). OAG-Bench: A human-curated benchmark for academic

graph mining. In Proceedings of the 30th ACM SIGKDD conference on knowledge discovery and data mining (pp. 6214–6225). Zhong, L., Wu, J., Li, Q., Peng, H., & Wu, X. (2023). A comprehensive survey on automatic knowledge graph construction. ACM Computing Surveys, 56(4), 1–62.

18
