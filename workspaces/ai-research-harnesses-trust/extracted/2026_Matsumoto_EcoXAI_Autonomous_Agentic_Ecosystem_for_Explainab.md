---
workspace_id: "SCI-000082"
doi: "10.64898/2026.07.08.737358"
title: "EcoXAI: Autonomous Agentic Ecosystem for Explainable Artificial Intelligence and Biomedical Discovery"
year: 2026
extraction_engine: "pymupdf"
---
# 2026 Matsumoto EcoXAI Autonomous Agentic Ecosystem for Explainab

The copyright holder for this this version posted August 26, 2026.  ;  https://doi.org/10.64898/2026.07.08.737358 doi:  bioRxiv preprint

. CC-BY-NC-ND 4.0 International license perpetuity. It is made available under a  preprint (which was not certified by peer review) is the author/funder, who has granted bioRxiv a license to display the preprint in

Bioinformatics, 2026, pp. 1–4

doi: DOI Advance Access Publication Date: 01 January 2023

Applications Note

APPLICATIONS NOTE EcoXAI: Autonomous Agentic Ecosystem for Explainable Artificial Intelligence and Biomedical Discovery

Nicholas Matsumoto,1 Hyunjun Choi,1 Philip J. Freda,1 Miguel E. Hernandez,1

Zhiping Paul Wang1 and Jason H. Moore1,∗

1Department of Computational Biomedicine, Center for Artificial Intelligence Research and Education, Cedars Sinai Medical Center, 8700 N. San Vicente Blvd., Pacific Design Center, Suite G-541H, West Hollywood, 90069, CA, USA ∗Corresponding author. jason.moore@csmc.edu FOR PUBLISHER ONLY Received on Date Month Year; revised on Date Month Year; accepted on Date Month Year


## Abstract

Motivation: As biomedical datasets and knowledge graphs continue to grow in size, complexity, and heterogeneity, navigating and extracting actionable insights from them presents a major bottleneck for researchers. There is a clear need for autonomous analytical solutions that can utilize recent advancements in agentic AI such as agent harnessing and loop engineering without introducing hallucination or workflow fragmentation. Researchers, regardless of technical expertise, need tools that streamline complex data analysis and deliver meaningful, actionable insights grounded in both data and established biomedical knowledge. EcoXAI addresses this by introducing a modular, customizable, containerized multi-agent system that structures analysis into explicit pipeline execution stages, lowering the computational barrier for clinical and translational researchers. Result: EcoXAI replaces monolithic AI text interfaces with an autonomous execution-driven framework with specialized bioinformatics agents for delivering proactive, data-driven insights grounded in established biological knowledge. Unlike purely LLM-driven or less integrated AI solutions prone to hallucinations or biologically implausible outcomes, EcoXAI’s multi-agent framework, which leverages modern agentic management and explicit knowledge graph integration, provides greater transparency and verifiability in its reasoning. In our use case in drug repurposing for Alzheimer’s Disease, EcoXAI evaluated 103 drug candidates and identified 79 novel candidates whose predictive models exceeded a randomized baseline, including the CCR5 antagonist Maraviroc, whose generated hypothesis was subsequently supported by the literature. These results demonstrate the potential of knowledge graph-grounded AI agents to accelerate hypothesis-driven biomedical research. Availability and implementation: EcoXAI is available on GitHub at: https://github.com/EpistasisLab/EcoXAI. Contact: jason.moore@csmc.edu


## 1 Introduction

To address this challenge, we present an autonomous agentic Ecosystem for Explainable AI (EcoXAI), a knowledge graph-grounded multi-agent framework for iterative biomedical discovery. EcoXAI integrates structured biological knowledge with exploratory data analysis, hypothesis generation, and hypothesis-specific validation in a modular workflow. Rather than treating all analytical tasks as a single generic prediction problem, EcoXAI decomposes a user’s research objective into distinct stages: dataset normalization and profiling, domain knowledge retrieval from a user-provided comprehensive biomedical knowledge graph, generation of candidate hypotheses informed by both the dataset and the interaction with the knowledge graph, and validation using evaluation procedures appropriate to the hypothesis type. Supported hypotheses are retained in discovery memory,

The increasing scale and complexity of biomedical data have created a need for analysis frameworks that can combine statistical rigor, biological prior knowledge, and flexible workflow execution. In biomedical data science, important questions often span multiple modes of evidence, including association testing, predictive modeling, predictive analytics, pathway interpretation, and literature or knowledge- graph support. However, conventional analytical pipelines typically address these tasks separately, while general- purpose AI systems may generate plausible but biologically ungrounded outputs. This disconnect is especially limiting in complex disease domains such as Alzheimer’s disease, where meaningful discovery requires both dataset-specific evidence and mechanistic biological context.

© The Author 2026. Published by Oxford University Press. All rights reserved. For permissions, please e-mail: journals.permissions@oup.com

1

The copyright holder for this this version posted August 26, 2026.  ;  https://doi.org/10.64898/2026.07.08.737358 doi:  bioRxiv preprint

. CC-BY-NC-ND 4.0 International license perpetuity. It is made available under a  preprint (which was not certified by peer review) is the author/funder, who has granted bioRxiv a license to display the preprint in

2 Matsumoto et al.

Fig. 1. 1) EcoXAI’s agentic workflow diagram. 2) Screenshot of the hypotheses page, which contain a list of all the generated hypotheses as well as the per hypothesis view. The hypothesis view contains assets that were generated from the evaluation of the hypothesis and a comprehensive report.

rather rigorous validation, creativity, and grounding. Agents are infused with customizable agent skills such as data normalization, exploratory data analysis (EDA), hypotheses generation/testing, and knowledge graph interaction. EcoXAI supports flexible integration with LLMs through APIs or local models, and its modular design allows advanced users to customize or create new agents for specific tasks or proprietary data integration.

enabling subsequent rounds of analysis to build on prior results and avoid redundant hypothesis generation.


## 2 Implementation

In this section, we outline the key components and processes underlying EcoXAI’s architecture. EcoXAI is organized around discrete, auditable pipelines rather than a single monolithic agent. These pipelines include data ingestion, exploratory data analysis (EDA), data normalization, predictive analysis, knowledge-graph guided hypothesis generation, hypothesis execution, and memory management. The system interacts with large language models (LLM) through third party APIs or local deployments, and its modular design allows the orchestration layer to route tasks to specialized tools or agents as needed. Once the user uploads their dataset, EcoXAI’s EDA agent assesses and cleans the dataset and creates an explanatory analysis in a markdown file which will be included in every downstream agent’s memory. EcoXAI then performs the fully autonomous research loop: using the knowledge graph and prior experiments, if available, it provides a diverse set of hypotheses, then evaluate each hypothesis until the entire set is exhausted, and repeat this cycle until either token budget or number of hypotheses loops is reached.

A key feature is EcoXAI’s integration with public biological knowledge graphs, which grounds analyses in established biological knowledge within the graph, reducing the risk of hallucinations and implausible results, leading to enhanced interpretability by linking findings to known pathways and relationships as well as generating hypotheses with prior knowledge in context. This knowledge-aware approach is crucial for applications like genomic analysis or drug repurposing, where context is essential.


### 2.1 Key EcoXAI Features

1. Autonomous Workflow Orchestration: EcoXAI uses a planner-orchestrator layer that decomposes the entire biomedical analysis into ordered steps. The system ingests the data, performs EDA, and starts the autonomous hypothesis generation and evaluation loop. Each step is auditable with its own logging of agent behavior, scripts, images, and reports. A diagram is shown in Figure 1-1. 2. Flexible Data Ingestion and Profiling: EcoXAI supports multiple biomedical data formats and can ingest datasets containing structured variables such as demographic and clinical features, molecular features, and quantitative biomarkers, accommodating both classification and regression tasks. EcoXAI profiles the dataset to identify feature distributions, missingness, class imbalance, correlations, outliers, and other quality or structure-related properties. This exploratory stage establishes dataset- specific context that informs downstream reasoning. 3. Knowledge Graph Grounding: EcoXAI queries public biomedical knowledge graphs, such as the Alzheimer’s

EcoXAI’s architecture is built upon modern software engineering principles, employing a microservices approach facilitated by Docker containers. This containerized architecture ensures high portability and enables consistent, reproducible performance across diverse computing environments, providing a critical advantage in bioinformatics, where software deployment and dependencies often present challenges.

EcoXAI’s core intelligence relies on recent advances in AI harnessing frameworks, such as Claude Code, Codex, and OpenCode, which are software layers that equip an LLM with access to tools, specialized skills, and planning for complex workflows to perform real-world tasks reliably. These tools are particularly suited for biological data science problems requiring multi-step reasoning that need

The copyright holder for this this version posted August 26, 2026.  ;  https://doi.org/10.64898/2026.07.08.737358 doi:  bioRxiv preprint

. CC-BY-NC-ND 4.0 International license perpetuity. It is made available under a  preprint (which was not certified by peer review) is the author/funder, who has granted bioRxiv a license to display the preprint in

Short Article Title 3

KnowledgeBase (AlzKB) that uses the Cypher querying language, to retrieve pathways, gene-disease associations, drug-target relationships, and other relevant biological context. This information is used to inform hypothesis generation, interpret model outputs, and prioritize biologically plausible candidates. 4. Deployment and Modularity: EcoXAI packages the full analysis stack from the AI harnesses to dataset management in Docker containers, promoting reproducibility and simplifying deployment across local, cloud, and collaborative environments. The system can also operate with different LLMs and specialized tools or user-defined skills, enabling users to adapt the workflow to available compute resources, task complexity, and institutional constraints. 5. Hypothesis Generation: EcoXAI generates candidate hypotheses by combining the user’s research question with dataset-derived signals and knowledge-graph context. Existing hypotheses are retained in memory and used to prevent redundant proposals, encouraging diversity while preserving relevance to the main analysis objective. 6. Parallelized Hypothesis Evaluation: Candidate hypotheses are tested using methodologies specific to the hypothesis under evaluation. For example, predictive hypotheses are assessed using model performance metrics, while mechanistic or knowledge-graph-derived hypotheses are assessed using dataset-based corroboration and enrichment evidence. EcoXAI will deploy as many concurrent evaluation sessions as determined by the user settings until all pending hypotheses are evaluated and a new hypothesis generation cycle or budget alarm is triggered. 7. Discovery Memory: EcoXAI stores prior hypotheses, validation outcomes, and supporting evidence. The hypotheses are stored in a semantic vector format, enabling the ability to perform Retrieval Augmented Generation (RAG) and similarity search whenever the system needs to generate new hypotheses. This memory enables iterative refinement of the discovery process by ensuring that subsequent hypotheses build on previous findings rather than repeatedly covering the same analytic space.

biological mechanisms. EcoXAI will generate machine learning models and test whether the AUC of the drug’s model is more performant in AUC than the randomized baseline.

Gene scores

The genetic variants (single nucleotide polymorphisms) for this study were obtained from the ADSP. The analysis used the ADSP R4 v11 2023 release, originally comprising over 346 million variants and 36,361 samples. Quality control included removing low-quality, rare, or poorly genotyped variants and samples. Using the filtered data, gene-based scores were calculated to quantify the cumulative effect of common variants on AD risk. Summary statistics from a GWAS conducted on the eMERGE cohort were used to assign effect sizes (beta) to variants (Leung et al., 2025). Variants were mapped to genes based on genomic coordinates, and gene scores were computed using the following formula:

P(beta ∗genotype)

Gene score =

nvariants

This approach yielded quantitative gene-level scores for 20,935 genes across 11,280 individuals in the ADSP cohort.


## 4 Results

Using a local Qwen 3.6 27B model running continuously for two days, which would have otherwise cost over $300 using Anthropic’s Sonnet 4.6 token pricing, EcoXAI autonomously generated, executed, and evaluated 103 independent drug repurposing hypotheses. For each candidate drug, the framework interacted directly with the AlzKB knowledge graph to retrieve drug targets, identify biologically connected genes through multiple graph traversal strategies, construct competing feature sets, train XGBoost models with stratified 5-fold cross validation on the training set (80/20 split, random seed 25), and automatically generate a complete analytical report describing the resulting hypothesis.

Rather than optimizing a fixed feature set, EcoXAI iteratively explored multiple biological hypotheses for each drug. Through AlzKB and starting from experimentally validated drug targets, the framework autonomously generated alternative gene sets including direct targets, first- and second-order interactors, shared biological processes, pathway- restricted subnetworks, and other methods that the agent creatively decided to pursue without explicit human instruction. Each hypothesis was independently evaluated against a randomized baseline consisting of 1,000 XGBoost models trained on random gene sets containing up to 100 genes.


## 3 Drug Repurposing Use Case

EcoXAI’s versatile capabilities support a wide range of bioinformatics applications and we will showcase a complex biomedical use case that display the full agentic properties of EcoXAI. To demonstrate EcoXAI’s ability to interact with grounded and transparent knowledge, we applied it to a publicly available Alzheimer’s Disease (AD) knowledge graph, AlzKB (https://AlzKB.ai/). AlzKB is a Memgraph graph database containing detailed data on genes, diseases, drugs, and other relevant entities, along with the semantic relationships between them (Romano et al., 2023). We use the 1.21 version of AlzKB for our benchmarks. EcoXAI’s skill management allows the agents to be capable of automatically retrieving the schema of any connected knowledge graph database, querying the requisite knowledge, and executing its task with it.

Of the 103 candidate drugs evaluated, 79 produced models exceeding the randomized baseline AUC of 0.582, indicating that their corresponding knowledge graph derived gene networks contained predictive information beyond randomly selected genomic features. An interesting pattern emerged across successful hypotheses: direct drug targets alone frequently performed at or below the randomized baseline, whereas expanded biological interaction networks substantially improved predictive performance. This observation was reproduced across diverse drug classes including immune modulators, kinase inhibitors, metabolic drugs, calcium channel blockers, and GPCR-targeting compounds, suggesting that Alzheimer’s disease risk is better represented by wider networks than isolated molecular targets.

By interacting with AlzKB to analyze gene expression profiles or network contexts in AD, EcoXAI proposes and evaluates target candidates. In this case study, we tasked EcoXAI to not use drugs that are already associated with AD as well as to not use any genes that are connected to AD for its feature selection to force it to explore novel

The copyright holder for this this version posted August 26, 2026.  ;  https://doi.org/10.64898/2026.07.08.737358 doi:  bioRxiv preprint

. CC-BY-NC-ND 4.0 International license perpetuity. It is made available under a  preprint (which was not certified by peer review) is the author/funder, who has granted bioRxiv a license to display the preprint in

4 Matsumoto et al.

The final output of EcoXAI was a ranked list of 79 candidate drugs that exhibited improved predictive performance and biologically coherent mechanistic hypotheses derived entirely through autonomous reasoning over the biomedical knowledge graph. This demonstrates EcoXAI’s ability to move beyond automated model fitting by performing iterative scientific hypothesis generation, refinement, and biological interpretation with minimal human intervention.

As agentic AI systems continue to mature, ensuring transparency, reproducibility, and interpretability are key especially in the biomedical domain. Like other autonomous AI systems, EcoXAI is susceptible to planning errors and cascading failures. To mitigate this, the framework enforces strict isolation across its pipeline stages, persisting intermediate code execution scripts and experimental logic so human researchers can inspect, reproduce, or modify tasks mid-loop.

Although demonstrated here for drug repurposing, the framework is readily extensible to other biomedical discovery tasks, including multi-omics integration, biomarker discovery, pathway analysis, and precision medicine applications. By coupling autonomous scientific reasoning with grounded biomedical knowledge, EcoXAI provides a scalable platform for accelerating hypothesis-driven biological discovery while maintaining the transparency required for biomedical research.

Case Study: Autonomous Discovery of Maraviroc

Among the 103 evaluated candidates, EcoXAI identified the CCR5 antagonist Maraviroc as one of the strongest repurposing hypotheses. Maraviroc is commonly used as an antiviral medication in treatment of HIV. Starting from experimentally validated drug targets, EcoXAI queried AlzKB to construct a 77-gene interaction network while explicitly excluding all Alzheimer’s disease-associated genes. On the 20% test split, this initial hypothesis achieved a cross-validated XGBoost AUC of 0.6013, exceeding the randomized baseline.

Acknowledgments

This work is supported in part by funds from the Center for AI Research and Education at Cedars-Sinai Medical Center and grants from the National Institutes of Health USA (P30 AG094848, U01 AG066833, R01 LM014572, R01 LM010098, and K01 DA063751).

Without intervention and rather than stopping after obtaining a significant result, EcoXAI autonomously generated and evaluated refined hypotheses through additional knowledge graph expansion. Introducing second-order interaction ”bridge” genes increased performance to an AUC of 0.6143, one of the highest-performing models produced during the study and comparable in performance to the best human curated models in prior studies (Orlenko et al., 2025). Feature importance analysis revealed that the predictive signal was driven primarily by downstream network genes rather than the direct drug target, suggesting that distributed biological interactions better capture Alzheimer’s disease susceptibility.


## References

Yuk Yee Leung, Wan-Ping Lee, Amanda B Kuzma, Heather

Nicaretta, Otto Valladares, Prabhakaran Gangadharan, Liming Qu, Yi Zhao, Youli Ren, Po-Liang Cheng, et al. Alzheimer’s disease sequencing project release 4 whole genome sequencing dataset. Alzheimer’s & dementia, 21 (5):e70237, 2025. Man Li, De-Shu Shang, Wei-Dong Zhao, Li Tian, Bo Li, Wen-Gang Fang, Li Zhu, Shu-Mei Man, and Yu-Hua Chen. Amyloid β interaction with receptor for advanced glycation end products up-regulates brain endothelial ccr5 expression and promotes t cells crossing the blood-brain barrier. The Journal of Immunology, 182(9):5778–5788, 2009. Weijiang Ma, Aihua Liu, Xinya Wu, Li Gao, Jingjing Chen,

Although CCR5 was three hops removed from Alzheimer’s disease in the AlzKB graph and all AD-associated genes were explicitly excluded during hypothesis generation, subsequent literature review revealed substantial independent evidence supporting this connection. Previous studies have reported increased CCR5 expression in Alzheimer’s disease brains (Xia et al., 1998), implicated the CCL5/CCR5 axis in regulating amyloid-β and tau pathology through microglial signaling (Ma et al., 2023), and demonstrated that amyloid-β induces CCR5 expression in brain endothelial cells to promote immune cell trafficking across the blood-brain barrier (Li et al., 2009). These findings suggest that EcoXAI recovered a biologically meaningful disease mechanism through autonomous knowledge graph reasoning rather than simply rediscovering known Alzheimer’s disease annotations.

Hanxin Wu, Meixiao Liu, Yuxin Fan, Li Peng, Jiaru Yang, et al. The intricate role of ccl5/ccr5 axis in alzheimer disease. Journal of Neuropathology & Experimental Neurology, 82 (11):894–900, 2023. Alena Orlenko, Binglan Li, Neda Khanjani, Mythreye Venkatesan, Li Shen, Marylyn D Ritchie, Zhiping Paul Wang, Tayo Obafemi-Ajayi, and Jason H Moore. A random-walk- based learning framework to uncover novel gene candidates for alzheimer’s disease therapy. In Biocomputing 2026: Proceedings of the Pacific Symposium, pages 815–829. World Scientific, 2025. Joseph D Romano, Van Truong, Rachit Kumar, Mythreye


## 5 Conclusion

EcoXAI represents a step toward autonomous AI-assisted biomedical data science by combining modern paradigms in agent harnesses, loop engineering, and unbound interaction with structured biomedical knowledge graphs. Unlike frameworks that act as solely a conversational assistant, EcoXAI proactively performs end-to-end scientific workflows including exploratory data analysis, knowledge retrieval, hypothesis generation, predictive modeling, and biological interpretation. Its modular, containerized architecture with harnessed agents and easily editable agent pipelines, enables reproducible deployment across diverse computational environments while allowing researchers to incorporate custom analytical tools, knowledge graphs, and local LLMs.

Venkatesan, Britney E. Graham, Yun Hao, Nick Matsumoto, Xi Li, Zhiping Wang, Marylyn Ritchie, Li Shen, and Jason H. Moore. The alzheimer’s knowledge base – a knowledge graph for therapeutic discovery in alzheimer’s disease research. Journal of Medical Internet Research, 07(11):46777, 2023. doi: 10.2196/46777. MengQi Xia, ShiXin Qin, LiJun Wu, Charles R Mackay, and

Bradley T Hyman. Immunohistochemical study of the β- chemokine receptors ccr3 and ccr5 and their ligands in normal and alzheimer’s disease brains. The American journal of pathology, 153(1):31–37, 1998.
