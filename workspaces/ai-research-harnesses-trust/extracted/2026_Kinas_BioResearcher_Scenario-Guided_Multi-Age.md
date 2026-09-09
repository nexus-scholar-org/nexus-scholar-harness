---
workspace_id: "SCI-000126"
doi: null
title: "BioResearcher: Scenario-Guided Multi-Agent for Translational Medicine"
year: 2026
extraction_engine: "pymupdf"
---
# 2026 Kinas BioResearcher Scenario-Guided Multi-Age

BIORESEARCHER: Scenario-Guided Multi-Agent for

Translational Medicine

Remigiusz Kinas Joanna Krawczyk Rafał Powalski Przemysław Pietrzak Agnieszka Kowalewska Krzysztof Kolmus Maciej Sypetkowski Łukasz Smoli´nski Tomasz Jetka ∗

arXiv:2605.05985v1  [cs.AI]  7 May 2026

Ingenix.AI, Warsaw, Poland


## Abstract

Translational medicine turns underspecified development goals into evidence syn- thesis that must combine literature, trials, patents, and quantitative multi-omics analysis while preserving identifiers, uncertainty, and retrievable provenance. General-purpose foundation models and off-the-shelf tool-augmented or multi- agent systems are not built for this: they tend to produce single-shot answers or run open-endedly, and fall short on the auditable, scenario-specific workflows that heterogeneous biomedical sources demand. This paper introduces BIORESEARCHER, a scenario-guided multi-agent system that maps queries to versioned research playbooks, delegates to specialized subagents over 30+ tools and machine-learning endpoints, mixes structured database access with sandboxed code for genome-scale analyses, and applies claim-level multi- model reconciliation before editorial assembly. We evaluate BIORESEARCHER across unit-level capabilities, open-ended biomedi- cal reasoning, and end-to-end clinical discovery. It leads evaluated baselines on 109 single-step tests (83.49% pass rate; 0.892 average score), achieves strong biomedical benchmark performance (89.33% on BixBench-Verified-50 and the top 0.758 mean score on BaisBench Scientific Discovery), and leads on a 30-query clinical end-to-end benchmark with the highest positive hit rate (74.7% ± 3.3%) and negative clear rate (96.8% ± 0.2%). These results show broad, competitive performance across unit-level, open-ended, and end-to-end clinical evaluations.

1 Introduction

Consider the following, exemplar question posed to a translational research team: “Given an antibody– drug conjugate (ADC) with a topoisomerase-I (TOP1) primary payload, what is the optimal second payload class for synergistic anti-tumor activity in non-small cell lung cancer (NSCLC)?”

This question, representative of real strategic decisions in pharmaceutical R&D, is operationally hard for several reasons. First, the query is entity-ambiguous: “Topo-I,” “topo1,” “topoiso- merase I,” and “TOP1” all denote the same protein target (ChEMBL ID CHEMBL1781, Ensembl ENSG00000198900), yet different databases index them under different names. At the same time, on- tology mismatches complicate cross-source integration: disease identifiers vary across EFO, DOID, MONDO, and TCGA conventions; compound identifiers differ between ChEMBL, and PubChem while accurate drug’s target mapping is noisy and depends on application.

∗Corresponding author: tomasz.jetka@ingenix.ai

Preprint.

Second, relevant evidence is scattered across heterogeneous sources: PubMed abstracts, Clini- calTrials.gov records, Google Patents filings, and DepMap multi-omics datasets, each with distinct identifiers, access patterns, and biological context. Additional sources such as research documents and ASCO, AACR, or ESMO abstracts could be integrated where licensing permits.

Third, reasoning spans interacting biological scales and high-dimensional measurements, requiring both qualitative synthesis and quantitative analysis. Fourth, outputs must be auditable dossiers: ranked hypotheses with mechanistic rationale and provenance. We present BIORESEARCHER, a scenario- guided multi-agent system that normalizes entities, routes questions to translational playbooks, delegates retrieval and CodeAct analyses, and reconciles evidence into provenance-preserving reports.

Our contributions are:

(a) A scenario-guided agent architecture for translational medicine that frames the problem as

scientific assistance for daily translational workflows: translating broad questions into explicit research plans, combining qualitative and quantitative evidence, and contextualizing outputs for clinical development (Section 2). (b) A layered evidence-synthesis stack with multi-model reconciliation that integrates ontology-

aware translation, qualitative knowledge synthesis, quantitative dataset analysis, and autonomous CodeAct-style computation under a single orchestrator, and reconciles outputs via structured claim-level debate—claim extraction, cross-model grouping, multi-round argumentation, and quantitative consensus detection—for auditable long-form biomedical report synthesis (Sec- tion 2). (c) A realistic multi-level evaluation protocol that separates component verification from hierar-

chical reasoning tests, autonomous custom-analysis tasks, and end-to-end expert assessment on realistic translational questions, together with ablations against direct LLM generation (Section 3).

2 System Architecture

BIORESEARCHER is a scenario-guided multi-agent system for translational evidence synthesis. Natural-language questions are often underspecified. Outputs are auditable dossiers with normalized entities, heterogeneous evidence, ranked hypotheses, mechanistic links, and retrievable provenance (e.g., PMIDs, NCT IDs, and patent numbers).

The architecture separates method selection, evidence acquisition, and reconciliation (Figure 1, Appendix A). A master orchestrator selects a versioned scenario playbook, decomposes the query, and delegates to specialized, state-isolated subagents that publish provenanced artifacts. A reconciliation agent drafts, compares, and resolves claims before a light editorial pass. Subagents use tool loops, iterative synthesis, cross-provider fan-out, and sandboxed code-mediated analysis; implementation details and tool coverage are provided in Appendices A and B.

3 Evaluation

To rigorously evaluate capability of BIORESEARCHER, we designed a benchmark suite at three complementary conceptual levels: single-step tests, clinical reasoning & autonomous analysis benchmark, and clinical end-to-end benchmark.

3.1 Single-Step Tests

We assembled a 109-question benchmark that verifies each system layer in isolation: L1 ontology and entity resolution, L2 qualitative retrieval, and L3 quantitative computation. That enables to verify how the system performs with accurately answering questions about data and facts across drug development aspects at every modality scale. The purpose of this benchmark is to see if the agent can perform simple factual checks and calculations. One may consider this a sanity check to see if the agent is able to perform basic tasks: crucial before evaluating the agent on more complex queries. The questions check e.g. the ability to resolve entity IDs, retrieve a PubMed publication, and process quantitative data. Each test question asks about a functionality of one sub-agent. Therefore, the tests do not only check the ability of the agent to perform single-step reasoning, but also the ability of the agent to route a simple question to the correct sub-agent. We use the single-step tests to compare

2

the performance of BIORESEARCHER, GPT-5.4-mini, GPT-5.5, and CellType Agent. The detailed benchmark design (subset definitions, test-case format) and evaluation protocol (LLM-as-a-judge configuration, rubric, scoring metric) are given in Appendix C.

3.2 Quantitative Reasoning & Autonomous Analysis Benchmark

We evaluate BIORESEARCHER’s ability to analyze custom datasets and propose dedicated au- tonomous analyses when the required computation is not fully specified in advance, using two com- plementary benchmarks: BixBench [1] and BaisBench (Scientific Discovery) [2]. See Appendix C for benchmark descriptions, task setup, and scoring details.

3.3 Clinical End-to-End Biomarkers Benchmark.

To evaluate end-to-end performance on translational-medicine reasoning, we constructed a benchmark of 30 expert-curated queries that pair a drug, mechanism of action (MOA), or indication with a clinically or preclinically validated biomarker. Items are stratified across seven tiers of evidential maturity, ranging from biomarkers approved alongside marketed therapies to prognostic biomarkers and synthetic-lethality hypotheses still under investigation.

Each query is paired with (i) an expert-authored positive answer drawn from regulatory labels, pivotal trials, or peer-reviewed literature, and (ii) a plausible negative control selected from adjacent biology to probe discrimination rather than mere recall. We report two metrics and then averaged across all benchmark items: the positive sample rate (PSR), i.e. the fraction of items whose positive answer pi appears in the system’s Top-10 list Li, and the negative sample rate (NSR), i.e. the fraction of items whose negative control ni is correctly excluded from Li (formal definitions in Appendix C). The whole benchmark is run three times per system, and the reported PSR and NSR are averaged.

4 Results

4.1 Single-Step Tests

Evaluation results for BIORESEARCHER, GPT-5.4-mini, GPT-5.5, and CellType Agent are shown in Table 1. As expected, GPT-5.4-mini has the lowest pass rates and average metric score across all layers and subsets. GPT-5.5 has signifficantly higher performance than GPT-5.4-mini, in all metrics. CellType Agent has the highest pass rate in layer L2 (Qualitative Synthesis). BIORESEARCHER with GPT-5.4 as core model achieved the highest average metric score in layers L1 (Ontology & Entity) and L3 (Quantitative Analysis), and the highest total pass rate and average metric score overall.


> **Table 1: Single-step test results, averaged over 3 runs. The first four columns report pass rates,**

> defined as the percentage of cases in the top rubric band (mean ± std over 3 runs) per layer and
overall. The last two columns report the judge’s average metric score and the average token usage
on the entire evaluation set (mean ± std over 3 runs). Model suffixes indicate reasoning effort, and
BIORESEARCHER variants indicate the core model used. BIORESEARCHER (mini) stands for BIORE-
SEARCHER with core model GPT-5.4-mini, BIORESEARCHER (low) stands for BIORESEARCHER
with core model GPT-5.4 with reasoning effort set to “low”.

System L1 (%) L2 (%) L3 (%) Total (%) Avg score Token usage

GPT-5.4-mini 26.26 ± 6.31 17.12 ± 4.13 11.11 ± 3.92 17.74 ± 2.80 0.316 ± 0.022 19167 ± 3948 GPT-5.4 (low) 40.85 ± 3.94 26.13 ± 3.12 20.51 ± 0.00 28.53 ± 1.84 0.448 ± 0.008 61824 ± 2341 GPT-5.5 (medium) 65.66 ± 1.75 37.84 ± 4.68 28.21 ± 5.13 42.81 ± 2.12 0.585 ± 0.009 221829 ± 7968 GPT-5.5 (high) 67.68 ± 1.75 40.04 ± 4.67 30.77 ± 2.56 45.09 ± 0.24 0.591 ± 0.005 447181 ± 20637 Gemini 3.1 Pro 47.38 ± 3.24 27.17 ± 1.21 12.82 ± 0.00 27.94 ± 1.10 0.481 ± 0.009 176974 ± 7500 CellType 81.82 ± 3.03 77.48 ± 1.56 46.60 ± 7.32 67.80 ± 1.70 0.731 ± 0.003 51953004 ± 931350 BIORESEARCHER (mini) 77.78 ± 1.75 74.77 ± 3.12 91.45 ± 1.48 81.65 ± 0.92 0.889 ± 0.015 2975729 ± 8001 BIORESEARCHER (low) 84.85 ± 3.03 68.47 ± 3.12 96.58 ± 1.48 83.49 ± 1.59 0.892 ± 0.004 2646126 ± 29309

3

4.2 Quantitative Reasoning & Autonomous Analysis Benchmark

BixBench. We report BixBench-style open-answer accuracy on phylobio/BixBench-Verified-50 [1] (Table 2) for the full 50-question set and a 22-question human subset of questions that concern human biology. For fairness, package-augmented Claude Code variants were provided the same data-analysis package list available to BIORESEARCHER, ensuring minimal execution context.

BaisBench. Mean SSD on the Scientific Discovery (BAIS-SD) track of BaisBench [2] is reported in Table 2. Task setup and scoring are specified in subsection 3.2.


> **Table 2: Quantitative reasoning and autonomous analysis benchmark results. BixBench-Verified-**

> 50 [1] reports open-answer accuracy (%, mean ± std over 3 runs) on the full set (50 questions) and a
22-question subset of questions about human biology. BaisBench Scientific Discovery (BAIS-SD) [2]
reports mean SSD on the 193-question SD track. BIORESEARCHER uses core model GPT-5.4 with
reasoning effort set to “medium”; No value is bolded since all results are statistically indistinguishable
from each other. CellType and Claude Code are powered by Claude Opus 4.7.

System BixBench acc. (%) BAIS-SD

Full Human Mean score

BIORESEARCHER 89.33 ± 1.15 81.82 ± 0.00 0.758 ± 0.005 CellType 89.33 ± 2.31 83.33 ± 6.94 0.641 ± 0.082 Claude Code 90.00 ± 2.00 83.33 ± 2.62 0.759 ± 0.012

4.3 Clinical End-to-End Benchmark

We constructed a benchmark centered on the translational medicine scenario family, where each query is paired with expert-authored ground truth. The benchmark tests system’s end-2-end performance, i.e. whether the system can reason, retrieve evidence, and generalize across a domain hierarchy. Table 3


> **Table 3: End-to-end benchmark results (30 queries): positive hit rate and negative clear rate (%).**

BIORESEARCHER, CellType, Medea, and OpenAI Deep Research: mean ± std over 3 runs. Medea is powered by GPT-5.4 with reasoning effort set to “low”.

System Positive rate Negative rate

BIORESEARCHER 74.7 ± 3.3 96.8 ± 0.2 CellType 61.7 ± 2.3 83.3 ± 0.0 Medea 33.7 ± 5.3 93.3 ± 3.3 OpenAI Deep Research 68.9 ± 7.7 81.1 ± 1.9

4.4 Case Study: Generation of Novel Biomarker Hypotheses

The ATR biomarker discovery case study illustrates our proposed regime in Appendix E. The system translated a broad synthetic-lethality question into a multi-stage omics analysis, separated pan-cancer from subtype-specific signals, and distinguished mechanistic pathway activation from candidate therapeutic sensitivity. Its final ranking did not simply maximize statistical signal: TP53 loss was treated as a robust marker of ATR pathway activation, ATM loss as the most mechanistically and clinically supported synthetic-lethal biomarker, APC loss as an exploratory colorectal-cancer-specific candidate, and ARID1A loss as biologically plausible but weaker in the available patient data. This behavior is aligned with the intended use case: producing a reviewable translational dossier that exposes evidence, caveats, and prioritization logic.

5 Analysis and Discussion

BIORESEARCHER obtains the best overall single-step pass rate (83.49%) and average judge score (0.892) on the 109-question suite (Table 1), surpassing the specialized CellType agent (67.80%,

4

0.731) and the strongest frontier baseline GPT-5.5 (high) (45.09%, 0.591). The largest margin is at L3 (Quantitative Analysis), where BIORESEARCHER reaches 91.45–96.58% against 46.60% for CellType and 28.21–30.77% for GPT-5.5, consistent with the architectural choice to expose genome-wide DepMap-style analyses through a CodeAct sandbox rather than a fixed set of pre- enumerated tool functions. At the same time, BIORESEARCHER is not uniformly dominant at every layer: CellType achieves a higher L2 pass rate (77.48% vs. 68.47–74.77%) on qualitative-synthesis questions, and frontier LLMs plateau near a 68% L1 ceiling regardless of reasoning effort. For narrow fact retrieval, specialized systems can therefore match or exceed a broader orchestrator.

The open-ended analysis benchmarks reinforce this interpretation. On BixBench, BIORESEARCHER reaches 89.33% accuracy on the full set and 81.82% on the human-biology subset, competitive with package-augmented coding agents (Table 2). On BaisBench Scientific Discovery, BIORESEARCHER achieves a mean score of 0.758 ± 0.005, exceeding CellType (0.641 ± 0.082) and matching Claude Code (0.759±0.012; Table 2). These results do not imply that orchestration alone solves autonomous biological discovery. Rather, they show that a translational agent can retain competitive data-analysis ability while adding the surrounding machinery that scientific users need: entity grounding, scenario- specific methodology, source separation, and final dossier construction.

On the end-to-end benchmark, BIORESEARCHER achieves the highest positive hit rate (74.7% ± 3.3%; Table 3) and the highest negative clear rate (96.8% ± 0.2%), exceeding CellType, Medea, and OpenAI Deep Research on both axes.

5


## References

[1] Ludovico Mitchener, Jon M. Laurent, Alex Andonian, Benjamin Tenmann, Siddharth Narayanan,

Geemi P. Wellawatte, Andrew White, Lorenzo Sani, and Samuel G. Rodriques. BixBench: a Comprehensive Benchmark for LLM-based Agents in Computational Biology, October 2025. arXiv:2503.00096 [q-bio].

[2] Erpai Luo, Jinmeng Jia, Yifan Xiong, Xiangyu Li, Xiaobo Guo, Baoqi Yu, Minsheng Hao,

Lei Wei, and Xuegong Zhang. Benchmarking AI scientists for omics data driven biological discovery, January 2026. arXiv:2505.08341 [cs].

[3] Emily Clough, Tanya Barrett, Stephen E Wilhite, Pierre Ledoux, Carlos Evangelista, Irene F

Kim, Maxim Tomashevsky, Kimberly A Marshall, Katherine H Phillippy, Patti M Sherman, et al. NCBI GEO: archive for gene expression and epigenomics data sets: 23-year update. Nucleic Acids Research, 52(D1):D138–D144, 2024.

[4] Confident AI. DeepEval: The open-source LLM evaluation framework. https://github.

com/confident-ai/deepeval, 2024. Accessed 2026.

[5] Daniil A. Boiko, Robert MacKnight, Ben Kline, and Gabe Gomes. Autonomous chemical

research with large language models. Nature, 624(7992):570–578, December 2023.

[6] Andres M. Bran, Sam Cox, Oliver Schilter, Carlo Baldassari, Andrew D. White, and Philippe

Schwaller. Augmenting large language models with chemistry tools. Nature Machine Intelli- gence, 6(5):525–535, May 2024.

[7] Chenglong Kang, Xiaoyi Liu, and Fei Guo. RetroInText: A Multimodal Large Language Model

Enhanced Framework for Retrosynthetic Planning via In-Context Representation Learning. October 2024.

[8] Reza Averly, Frazier N. Baker, Ian A Watson, and Xia Ning. LIDDIA: Language-based

Intelligent Drug Discovery Agent. In Christos Christodoulopoulos, Tanmoy Chakraborty, Carolyn Rose, and Violet Peng, editors, Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing, pages 12004–12028, Suzhou, China, November 2025. Association for Computational Linguistics.

[9] Martin Pacesa, Lennart Nickel, Christian Schellhaas, Joseph Schmidt, Ekaterina Pyatova, Lucas

Kissling, Patrick Barendse, Jagrity Choudhury, Srajan Kapoor, Ana Alcaraz-Serna, Yehlin Cho, Kourosh H. Ghamary, Laura Vinué, Brahm J. Yachnin, Andrew M. Wollacott, Stephen Buckley, Adrie H. Westphal, Simon Lindhoud, Sandrine Georgeon, Casper A. Goverde, Georgios N. Hatzopoulos, Pierre Gönczy, Yannick D. Muller, Gerald Schwank, Daan C. Swarts, Alex J. Vecchio, Bernard L. Schneider, Sergey Ovchinnikov, and Bruno E. Correia. One-shot design of functional protein binders with BindCraft. Nature, 646(8084):483–492, October 2025.

[10] Mingming Zhu, Jiahua Rao, Xiaoyu Chen, Qianmu Yuan, and Yuedong Yang. Advancing

Protein Design via Multi-Agent Reinforcement Learning with Pareto-Based Collaborative Optimization, January 2026. ISSN: 2692-8205 Pages: 2026.01.13.699365 Section: New Results.

[11] Manvitha Ponnapati, Sam Cox, Cade W. Gordon, Michael J. Hammerling, Siddharth Narayanan,

Jon M. Laurent, James D. Braza, Michaela M. Hinks, Michael D. Skarlinski, Samuel G. Rodriques, and Andrew White. ProteinCrow: A Language Model Agent That Can Design Proteins. July 2025.

[12] Yusuf H. Roohani, Andrew H. Lee, Qian Huang, Jian Vora, Zachary Steinhart, Kexin Huang,

Alexander Marson, Percy Liang, and Jure Leskovec. BioDiscoveryAgent: An AI Agent for Designing Genetic Perturbation Experiments. October 2024.

[13] Alireza Ghafarollahi and Markus Buehler. ProtAgents: Protein discovery via large language

model multi-agent collaborations combining physics and machine learning. March 2024.

6

[14] Zuojun Xu, Feng Ren, Ping Wang, Jie Cao, Chunting Tan, Dedong Ma, Li Zhao, Jinghong

Dai, Yipeng Ding, Haohui Fang, Huiping Li, Hong Liu, Fengming Luo, Ying Meng, Pinhua Pan, Pingchao Xiang, Zuke Xiao, Sujata Rao, Carol Satler, Sang Liu, Yuan Lv, Heng Zhao, Shan Chen, Hui Cui, Mikhail Korzinkin, David Gennert, and Alex Zhavoronkov. A generative AI-discovered TNIK inhibitor for idiopathic pulmonary fibrosis: a randomized phase 2a trial. Nature Medicine, 31(8):2602–2610, August 2025.

[15] Shanghua Gao, Richard Zhu, Zhenglun Kong, Ayush Noori, Xiaorui Su, Curtis Ginder,

Theodoros Tsiligkaridis, and Marinka Zitnik. TxAgent: An AI Agent for Therapeutic Reasoning Across a Universe of Tools, March 2025.

[16] Yubin Kim, Chanwoo Park, Hyewon Jeong, Yik Siu Chan, Xuhai Xu, Daniel McDuff, Hyeon-

hoon Lee, Marzyeh Ghassemi, Cynthia Breazeal, and Hae Won Park. MDAgents: An Adaptive Collaboration of LLMs for Medical Decision-Making. November 2024.

[17] Dyke Ferber, Omar S. M. El Nahhas, Georg Wölflein, Isabella C. Wiest, Jan Clusmann,

Marie-Elisabeth Leßmann, Sebastian Foersch, Jacqueline Lammert, Maximilian Tschochohei, Dirk Jäger, Manuel Salto-Tellez, Nikolaus Schultz, Daniel Truhn, and Jakob Nikolas Kather. Development and validation of an autonomous artificial intelligence agent for clinical decision- making in oncology. Nature Cancer, 6(8):1337–1349, August 2025.

[18] Qiao Jin, Zifeng Wang, Charalampos S. Floudas, Fangyuan Chen, Changlin Gong, Dara

Bracken-Clarke, Elisabetta Xue, Yifan Yang, Jimeng Sun, and Zhiyong Lu. Matching patients to clinical trials with large language models. Nature Communications, 15(1):9074, November 2024.

[19] Anurag Jayant Vaidya, Felix Meissen, Daniel C. Castro, Shruthi Bannur, Tristan Lazard,

Drew FK Williamson, Faisal Mahmood, Javier Alvarez-Valle, Stephanie Hyland, and Kenza Bouzid. NOVA: An Agentic Framework for Automated Histopathology Analysis and Discovery. November 2025.

[20] Kyle Swanson, Wesley Wu, Nash L. Bulaong, John E. Pak, and James Zou. The Virtual Lab of

AI agents designs new SARS-CoV-2 nanobodies. Nature, 646(8085):716–723, October 2025.

[21] Kexin Huang, Serena Zhang, Hanchen Wang, Yuanhao Qu, Yingzhou Lu, Yusuf Roohani, Ryan

Li, Lin Qiu, Gavin Li, Junze Zhang, Di Yin, Shruti Marwaha, Jennefer N. Carter, Xin Zhou, Matthew Wheeler, Jonathan A. Bernstein, Mengdi Wang, Peng He, Jingtian Zhou, Michael Snyder, Le Cong, Aviv Regev, and Jure Leskovec. Biomni: A General-Purpose Biomedical AI Agent. bioRxiv: The Preprint Server for Biology, page 2025.05.30.656746, June 2025.

[22] Ruofan Jin, Yucheng Guo, Yuanhao Qu, Ming Yang, Chun Shang, Qirong Yang, Linlin Chao,

Yi Zhou, Ruilai Xu, Ziyao Xu, Ruhong Zhou, Zaixi Zhang, Mengdi Wang, Xiaoming Zhang,

and Le Cong. BioLab: End-to-End Autonomous Life Sciences Research with Multi-Agents System Integrating Biological Foundation Models, September 2025. ISSN: 2692-8205 Pages: 2025.09.03.674085 Section: New Results.

[23] Zhongyue Zhang, Zijie Qiu, Yingcheng Wu, Shuya Li, Dingyan Wang, Zhuomin Zhou,

Duo An, Yuhan Chen, Yu Li, Yongbo Wang, Chubin Ou, Zichen Wang, Jack Xiaoyu Chen, Bo Zhang, Yusong Hu, Wenxin Zhang, Zhijian Wei, Runze Ma, Qingwu Liu, Bo Dong, Yuexi He, Qiantai Feng, Lei Bai, Qiang Gao, Siqi Sun, and Shuangjia Zheng. OriGene: A Self- Evolving Virtual Disease Biologist Automating Therapeutic Target Discovery, June 2025. Pages: 2025.06.03.657658 Section: New Results.

[24] Pengwei Sui, Michelle M. Li, Shanghua Gao, Wanxiang Shen, Valentina Giunchiglia, Andrew

Shen, Yepeng Huang, Zhenglun Kong, and Marinka Zitnik. Medea: An omics AI agent for therapeutic discovery. bioRxiv: The Preprint Server for Biology, page 2026.01.16.696667, January 2026.

[25] Houcheng Su, Weicai Long, and Yanlin Zhang. BioMaster: Multi-agent System for Automated

Bioinformatics Analysis Workflow, January 2025. Pages: 2025.01.23.634608 Section: New Results.

7

[26] Joshua Pickard, Ram Prakash, Marc Andrew Choi, Natalie Oliven, Cooper Stansbury, Jillian

Cwycyshyn, Alex Gorodetsky, Alvaro Velasquez, and Indika Rajapakse. Language Model Powered Digital Biology with BRAD, December 2024. arXiv:2409.02864 [cs].

[27] Zhizheng Wang, Qiao Jin, Chih-Hsuan Wei, Shubo Tian, Po-Ting Lai, Qingqing Zhu, Chi-Ping

Day, Christina Ross, Robert Leaman, and Zhiyong Lu. GeneAgent: self-verification language agent for gene-set analysis using domain databases. Nature Methods, 22(8):1677–1685, August 2025.

[28] Yuxing Lu, Wei Wu, Xukai Zhao, Rui Peng, and Jinzhuo Wang. KARMA: Leveraging Multi-

Agent LLMs for Automated Knowledge Graph Enrichment. October 2025.

[29] Timothy A. Yap, Elisa Fontana, Elizabeth K. Lee, David R. Spigel, Martin Højgaard, Stephanie

Lheureux, Niharika B. Mettu, Benedito A. Carneiro, Louise Carter, Ruth Plummer, Gregory M. Cote, Funda Meric-Bernstam, Joseph O’Connell, Joseph D. Schonhoft, Marisa Wainszelbaum, Adrian J. Fretland, Peter Manley, Yi Xu, Danielle Ulanet, Victoria Rimkunas, Mike Zinda, Maria Koehler, Ian M. Silverman, Jorge S. Reis-Filho, and Ezra Rosen. Camonsertib in DNA damage response-deficient advanced solid tumors: phase 1 trial results. Nature Medicine, 29(6):1400–1411, June 2023.

8


> **Figure 1: System architecture. The master orchestrator selects a scenario playbook and adaptively**

> delegates self-contained subtasks to specialized retrieval and analysis agents. Agents publish prove-
nanced source artifacts to a shared evidence bus; a reconciliation agent ingests the bus, drafts the
report with multiple models, and resolves disagreement at the claim level.

A Architecture Details

This appendix collects supporting artifacts referenced from Section 2: the high-level system diagram (Figure 1), the four reusable execution patterns underlying specialized subagents (Figure 2), and the claim-level reconciliation procedure (Algorithm 1).

B Domain-Specific Components and Tool Specifications

This appendix expands the domain-specific component stack summarized in Section 2 and provides parameter schemas for representative tools from each major category. All tools are implemented as Python functions with type annotations; a @tool decorator exposes them to agents as structured function-calling tools with auto-generated JSON schemas.

B.1 Entity Resolution and Biomedical Knowledge Grounding

The translation subagent is the foundation for all downstream research. It resolves entity ambiguity by mapping natural-language mentions to canonical identifiers using a ReAct agent with eight tools backed by local SQLite databases (ChEMBL 36, Open Targets) with API fallback:

• target_name_to_chembl_id: gene/protein name →ChEMBL target ID • molecule_name_to_chembl_id: drug name →ChEMBL molecule ID • target_to_drug_chembl_ids: target →associated drugs (Phase ≥2) • compound_smiles_to_name_and_chembl_id: SMILES →compound identity • get_drug_indications: drug →approved/investigated indications

9


> **Figure 2: Four reusable execution patterns. (a) Tool loops support structured database access: an**

> agent iterates with a fixed tool surface and emits a single artifact when finished. (b) Iterative synthesis
maps an agent’s research output through a deterministic plan, write, and summarize pipeline; the
iteration is internal to the agent. (c) Provider fan-out dispatches the same task to heterogeneous
models in parallel; each model produces a summary that the agent composes into a final summary,
exploiting cross-family diversity to reduce single-model bias. (d) Code-mediated analysis lets the
agent author code that is executed in a sandbox; sandbox output feeds back into the agent until it
emits final results. Solid arrows: deterministic transitions. Dashed arrows: feedback loops.

Algorithm 1 Claim-level section reconciliation.

Require: Candidate drafts D = {d1, . . . , dM} for section s, question q, agreement threshold τ, max

rounds R. Ensure: Reconciled section ys.

1: For each dm, extract atomic claims with source-support quote and confidence. 2: Cluster claims across drafts into topic groups labeled {full, partial, conflict}. 3: for r = 1, . . . , R do 4: In parallel, each model issues an updated stance per group with revised claim, explanation, and confidence, conditioned on other agents’ prior positions. 5: if no model disagrees on any group and mean confidence ≥τ then 6: break 7: end if 8: end for 9: Synthesize ys from drafts, claim groups, and final positions, restricted to the section’s allocated sources.

• disease_name_to_efo_id: disease name →EFO/MONDO ontology ID • molecule_smiles_to_molecule_synonyms: SMILES →all known synonyms (Pub- Chem) • get_gene_id_to_ensembl_id_mapping: gene symbol →Ensembl ID

Local SQLite is preferred over API access for latency and reproducibility; a swappable backend via translation_factory.py supports both modes. The output is a structured entity table with canonical IDs consumed by all downstream subagents, ensuring consistent entity resolution across all evidence streams.

Concrete Example. For the query “Topo-I inhibitor combinations in NSCLC,” the translation subagent resolves: (i) “Topo-I” →gene symbol TOP1 →ChEMBL target CHEMBL1781 →Ensembl ENSG00000198900; (ii) “NSCLC” →EFO_0003060 (cross-mapped to TCGA “LUAD”/“LUSC”

10

and DepMap disease contexts); (iii) associated compounds: Irinotecan (CHEMBL481), Topotecan (CHEMBL84), Trastuzumab Deruxtecan (CHEMBL4297564), among 24 Phase ≥2 drugs retrieved via target_to_drug_chembl_ids. This single grounding step prevents downstream subagents from searching for “topoisomerase I” in one database and “TOP1” in another without recognizing them as equivalent.

B.2 Tool Ecosystem

The system integrates 30+ tools spanning six ML endpoints and multiple external data sources (Table 4). Table 4 provides a categorized overview.


> **Table 4: Tool ecosystem organized by category, data source, and interaction pattern. The 30+ tools**

> span structured function-calling (Pattern 1–3 subagents) and CodeAct sandbox functions (Pattern 4).
ML model endpoints provide predictions for drug synergy.

Category Tools Data Source Pattern

Entity Resolution 8 translation tools ChEMBL 36, Open Targets, PubChem Local SQLite / REST Literature search_pubmed, fetch_abstracts, etc. (4) PubMed / NCBI E-utilities REST API Literature get_target_disease_evidence, etc. (4) Open Targets GraphQL API Text data RAG search_conference_abstracts (2) Licenced text data sources ChromaDB Clinical Trials search_clinical_trials (2) ClinicalTrials.gov v2 / AACT REST / SQLite Patents search_patents (2) Google Patents SerpAPI Target Profile get_basal_protein_info, etc. (4) DepMap, HPA Parquet + API Genome-Wide Dependency, expression, mutation tools (11) DepMap 24Q4 multi-omics CodeAct sandbox PPI/Pathways get_gene_pair_annotations, etc. (3) STRING/Reactome/GO CodeAct sandbox Drug Synergy predict_drug_combination (1) DrugComb v2 HF Gradio API

B.3 Conference Abstract and other licensed data sources - RAG

Conference abstracts and other licensed data sources contain the earliest reports of clinical results, often 6–12 months before peer-reviewed publication. This latency gap is critical for translational research.

The indexing pipeline processes conference PDFs via PyMuPDF with conference-specific chunking strategies. Metadata fields are extracted per chunk: conference name, year, page, abstract ID, section header (e.g., “Breast Cancer: Metastatic”), inferred disease type (mapped to 12 canonical categories including nsclc, colorectal_cancer, melanoma), gene symbols (regex-matched against 33 key oncology genes including KRAS, EGFR, BRAF, TOP1, BRCA1/2), drug mentions, trial phase (regex-extracted), NCT IDs (pattern NCT\d{8}), and abstract type (late-breaking, oral, poster). Embeddings are computed via SentenceTransformer (all-MiniLM-L6-v2) and stored in ChromaDB with metadata filtering, enabling queries such as “find late-breaking abstracts mentioning TOP1 in NSCLC.”

B.4 CodeAct Sandbox for Genome-Wide Analysis

The insights_and_signals subagent operates a sandboxed Python execution environment pre-loaded with nine DepMap 24Q4 Parquet datasets spanning ∼19K genes × ∼1,600 cell lines:

• Dependency screens: CRISPR gene effect (Chronos), CRISPR dependency probability, shRNA gene effect (DEMETER2), shRNA dependency probability • Omics: Gene expression (log2(TPM+1)), copy number (log2(CN ratio+1)), proteomics (normalized abundance), somatic mutations (binary), loss-of-function mutations (binary)

The namespace includes pre-loaded pandas, numpy, and scipy.stats, plus a THRESHOLDS dic- tionary encoding expert-curated biological cutoffs: CRISPR likely dependent (< −0.5), strongly dependent (< −1.0), dependency probability thresholds (dependent > 0.6, resistant < 0.4), copy- number gain (> 1.5), amplification (> 1.9), loss (< 0.6), FDR significance (< 0.1), and minimum sample size (≥3). These thresholds ground the LLM’s statistical analyses in accepted DepMap conventions, preventing arbitrary cutoff selection.

Security Model. Table 5 summarizes the sandbox security constraints.

11


> **Table 5: CodeAct sandbox security model.**

Constraint Details

Blocked builtins exec, eval, compile, __import__, open, input, breakpoint Execution timeout 600 s per code block Round cap Maximum 12 code blocks per session Output truncation 8,000 chars (stdout), 4,000 chars (stderr) Variable persistence Only msgpack-serializable primitives (str, int, float, bool, list, dict); DataFrames and numpy arrays ex- cluded Namespace isolation Filtered __builtins__ copy; no filesystem or network access

Edge-Case Handling. The sandbox addresses three failure modes: (1) resource exhaustion: code exceeding the 600 s timeout or 8,000-char output limit is killed mid-execution, and the LLM receives truncated output with a diagnostic message; (2) blocked operations: attempts to call restricted builtins raise NameError, which the LLM can observe and self-correct; (3) serialization failures: variables that cannot be msgpack-serialized (e.g., matplotlib figures) are silently dropped between code blocks, preventing state pollution.

Supported Analyses. 18 callable tool functions span genome-wide dependency correlations, expression–dependency associations, mutation stratification (Mann–Whitney U), synthetic lethality analysis (absolute thresholds + percentile ranking), PPI network analysis, GEO [3] expression outlier detection, and drug combination synergy prediction.

B.5 Parameter Schemas for Representative Tools

Patent Search (search_patents). The most complex tool schema, supporting both textual and chemical structure queries:

Parameter Type Description

text_terms List[TextTerm]? Structured query terms. Each TextTerm specifies value (phrase), where ∈{TITLE, ABSTRACT, CLAIM, FULL_DOCUMENT}, match ∈{PARTIAL, EXACT} chemical_terms List[ChemicalTerm]? Chemical structure queries. Each ChemicalTerm speci- fies value (SMILES or InChIKey), molecule_type ∈ {SMILES, INCHI_KEY}, chemical_search_type ∈ {EXACT, SIMILAR, SUBSTRUCTURE} text_connector QueryLogic AND/OR for combining text terms assignees List[str]? Patent assignee (company) names status StatusTypes GRANT / APPLICATION / ALL start_date, end_date str? Date range (YYYY/MM/DD format) limit int Results cap (10–100, default 10)

SMILES inputs are canonicalized via RDKit StandardizeSmiles; InChIKeys are validated by regex. Backend: SerpAPI google_patents engine with field-code query construction (e.g., TI= for title, SSS=(struct) for substructure).

Parameter Type Description

condition str? Disease/condition; supports AND/OR syntax, e.g., ((NSCLC) OR (lung cancer)) AND (EGFR) intervention str? Drug or treatment name; supports AND/OR term str? Free-text keyword search across all study fields status List[str]? Phase filter: RECRUITING, COMPLETED, AC- TIVE_NOT_RECRUITING, etc. (14 valid values) date_range str? Primary completion date range, e.g., 2020-01-01..2023-12-31 limit int Max results (default 50, max 1000)

Clinical Trial Search (search_clinical_trials). Default returned fields: NCTId, BriefTi- tle, OverallStatus, BriefSummary, Condition, Phase, InterventionName. Backend: ClinicalTri-

12

als.gov REST API v2. A local AACT SQLite variant with identical signature is available for offline/reproducible evaluation.

Parameter Type Description

query str PubMed query using native syntax: field tags ([Title/Abstract], [MeSH Terms], [Gene]), Boolean operators, quoted phrases max_results int Result limit (default 80) sort relevance | date Sort order min_date, max_date str? Publication date range (YYYY/MM/DD)

PubMed Search (search_pubmed). Returns PMID, title, journal, and year per result. On zero results, the tool returns PubMed’s querytranslation and lists unrecognized terms as diagnostic feedback, enabling the agent to reformulate queries. Backend: NCBI E-utilities (esearch → esummary) with exponential backoff on rate limiting.

C Benchmarks Construction

C.1 Single-Step Tests: Subsets


> **Table 6: Single-step test subsets, layer coverage, and a representative query per subset. Each subset**

> targets a specific system layer and is scored independently with its own rubric.

Subset Layer Tested N Representative Query

Ontology & Entity Entity resolution / grounding 33 “What is the Ensembl gene ID and ChEMBL target

ID for CD340?” Qualitative Synthesis Literature / trials / patents retrieval 37 “Provide the title of the publication with PMID

25439351.” Quantitative Analysis DepMap / omics computation 39 “What is the CRISPR gene-effect score for PARP1

in MCF7?”

Total 109

C.2 Single-Step Tests: Benchmark Design

The benchmark consists of 109 questions requiring single-step reasoning and is partitioned into three subsets (layers), summarized in Table 6. Ontology & Entity (L1) challenges entity normalization across biomedical ontologies. This layer focuses mostly on the ability of the agent to retrieve key entities (e.g. genes, diseases) from the free-text input and map them to their canonical IDs. Another example task is resolving a gene family name to a list of member genes with canonical IDs. Qualitative Synthesis (L2) evaluates retrieval of qualitative knowledge from biomedical databases. The questions check (among others) for facts about genes, compounds, protein functions and pathways, clinical trials, patents, and literature. Example tasks are retrieving clinical trial NCT IDs for a given context or assessing the success of a clinical trial given its NCT number. Quantitative Analysis (L3) assesses extraction and computation of key quantitative data points. An example task is checking the expression level of a given gene in a given cell line.

Test-case format. Each test case is a pair of a question (a natural-language query for the agent) and an expected output (example natural-language response that the agent is expected to return). For example, the expected output for the question “What is the Ensembl gene ID and ChEMBL target ID for CD340?” is as follows.

Ensembl ID: ENSG00000141736 ChEMBL target ID: CHEMBL1824

Each expected output was manually verified by an expert to be correct.

13

C.3 Single-Step Tests: Evaluation Protocol

Execution. Every question is submitted end-to-end to the full master graph: the top-level orchestra- tor dispatches it to the appropriate sub-agent, which invokes tools as needed. No sub-agent is tested in isolation, so the single-step tests also probe the orchestrator’s routing decisions. The agent’s actual output for scoring is the natural-language content of the final message emitted by the master graph.

Judge. We use DeepEval [4], an LLM-as-a-judge framework, to score open-ended natural-language outputs against the expected outputs. For each test case, the judge is shown the question, the actual output, and the expected output, and assigns a score between 0 and 1, together with a free-text justification. Each test case is paired with a custom DeepEval metric that instructs the judge how to score the output. A metric specification consists of (i) natural-language evaluation criteria, (ii) a rubric, i.e. a list of tier descriptions mapped to disjoint score bands on [0, 1], and (iii) a threshold score (the minimum score required for the test to pass). An example criteria block is:

Evaluation dimensions: 1. Canonical entity: When the expected output labels a canonical name (e.g. drug name, disease name), is it present and unambiguously identified in the actual output? 2. Identifier match: Do all identifiers labelled in the expected output appear in the actual output with matching values? 3. No fabrication: The actual output does not introduce alternative identifiers that contradict the expected ones, and does not confuse the entity with a same-string alias of a different gene/disease/drug.

A three-tier rubric yields the bands [0.0, 0.2], [0.4, 0.6], [0.8, 1.0]; the gaps make tier boundaries unambiguous and the judge commits to one tier per test case. In each custom metric, the threshold score is set so that a test passes if the judge assigns a score in the highest band (e.g. 0.8 for three-tier rubrics). An example three-tier rubric for entity-resolution questions (like the example for layer Ontology & Entity in Table 6) is shown in Table 7. We used DeepEval’s default LLM model, which is GPT 4.1, for all metrics.


> **Table 7: Example rubric: the judge assigns one tier, yielding a score in the corresponding band.**

Score band Expected outcome specification

[0.0, 0.2] Identifiers absent or contradicting the expected ones, or canonical entity (when labelled in the expected output) wrong or missing. [0.4, 0.6] Most identifiers correct but some missing or partially mismatched, or canonical entity (when labelled) partially off. Additional information contradicts the expected output. [0.8, 1.0] All expected identifiers present and matching, canonical entity (when labelled) correct, no fabricated alternatives. If additional information is present, it doesn’t contradict the expected output.

Metric. The primary per-subset metric is the pass rate: the fraction of test cases in that subset whose judge-assigned score satisfies score ≥threshold (i.e. such that were classified into the top tier of the rubric). Another metric is the average metric score: the average score of the test cases.

C.4 BixBench

We use a subset of BixBench restricted to Homo sapiens data, which probes open-ended biomedi- cal data analysis under partial specification. We report BixBench-style open-answer accuracy on phylobio/BixBench-Verified-50 [1] (Table 2) for the full 50-question set and a 22-question human subset of questions that concern human biology. For fairness, package-augmented Claude Code variants were provided the same data-analysis package list available to BIORESEARCHER, ensuring comparable minimal execution context.

C.5 BaisBench

We use the Scientific Discovery (BAIS-SD) track of BaisBench [2]: 193 data-driven questions on real single-cell RNA-seq datasets, grounded in biological conclusions from 41 published single-cell

14

studies, where agents analyze the provided data to select answers in single- and multi-answer formats as in the benchmark. Scoring is trichotomous (0, 0.5, or 1) per the SD task: single-answer items receive 0 or 1; multi-answer items receive 1 if all correct options are selected and no incorrect one, 0.5 if at least one correct option is selected and no incorrect one (but not the full set), and 0 otherwise. We report the mean SSD in Table 2.

Item construction. Candidate items were drafted by domain experts and cross-checked against at least one primary source per item (regulatory document, registered trial with reported biomarker analysis, or peer-reviewed publication). Items were retained only if (i) the positive answer was unambiguously supported by the primary source and (ii) the pairing was not trivially derivable from the query string itself (e.g., we excluded items where the biomarker name appeared verbatim in the drug’s INN or trial title). Tiers 2 and 3 were deliberately included to stress-test failure modes observed in pilot evaluations: target/biomarker conflation in Tier 2, and the gap between mechanistic plausibility and clinical translation in Tier 3.

C.6 End-2-End Clinical Biomarkers Benchmark Construction

Scope and design rationale. The benchmark targets a single, recurring translational scenario: given a therapy (approved or investigational), an MOA, or an indication, identify a biomarker with documented clinical or preclinical relevance. Items were stratified by evidential maturity so that ag- gregate scores can be decomposed into (a) recall of canonical, label-level facts and (b) generalization to settings where signal is distributed across heterogeneous sources (trial registries, mechanistic liter- ature, functional-genomics screens, observational prognostic studies). Tier-level expected accuracy was set a priori based on the breadth and consistency of available primary evidence.

Category specification. The 30 items are distributed across seven tiers as summarized in Table 8.


> **Table 8: Tier structure of the translational-medicine biomarker benchmark. Tier-level expected recall**

> reflects a priori difficulty estimates based on evidential maturity and source breadth.

Tier Construct tested Source archetype n

FDA/EMA label, NCCN guideline

1 Clinically-approved biomarker for an approved therapy (canonical pairing)

4

Label + pivotal trial 4

2 Clinically-approved biomarker – test- ing detailed description

3 Synthetic-lethality biomarker with clinical evidence, no full approval

Phase I/II trials, mechanis- tic papers

4

4 Biomarker reported in trials of non- approved therapies

ClinicalTrials.gov, trial publications

4

5 Biomarker with extensive preclinical validation (non-approved therapies)

Peer-reviewed preclinical studies

5

CRISPR/RNAi screens, DepMap-class evidence

6 Biomarker from synthetic-lethality dis- covery studies

5

Observational and meta- analytic literature

7 Prognostic biomarker for a specific in- dication

4

Negative controls. For each item, an expert-authored negative biomarker was selected from adjacent biology—same pathway, same indication class, or same therapeutic modality—such that surface-level retrieval (keyword overlap, co-occurrence in literature) would plausibly surface it. This design penalizes systems that retrieve by topical proximity rather than evidence-grounded reasoning.

Query template. Each benchmark item is submitted to the system using the fixed prompt below, with the placeholders [Target (MoA)] and [Indication] replaced by the corresponding fields from the item record:

Your task is:

15

Given a drug with its known molecular target(s): [Target (MoA)], and an indication [Indication], return a prioritized list of candidate molecular biomarkers that may predict treatment response, resistance, sensitivity, or patient enrichment. Definitions: • Target — the molecular entity or pathway directly modulated by the drug. • Biomarker — a molecular feature distinct from the direct drug target, such as mutation, amplification, deletion, fusion, expression change, pathway activation state, homologous recombination deficiency marker, co-mutation pattern, or other molecular alteration associated with response or resistance. • Indication — disease / tumor type / clinical context.

Scoring. For each item i with positive answer pi, negative control ni, and a system returning a Top-10 list Li, we report two metrics computed separately and then averaged across all N benchmark items: the positive sample rate

N X

PSR = 1 N

1[pi ∈Li], (1)

i=1

i.e. the fraction of items whose positive answer is recovered, and the negative sample rate

N X

NSR = 1 N

1[ni /∈Li], (2)

i=1

i.e. the fraction of items whose negative control is correctly excluded. The whole benchmark is run three times per system, and the reported PSR and NSR are averaged across the three runs. Tier-level subscores are reported alongside the aggregate to expose where systems trade off canonical recall against generalization to less mature evidence.

16


> **Table 9: Full specification of the 30-item translational-medicine biomarker benchmark (Tiers 1–**

> 4). Each item pairs a therapy/MOA/indication with an expert-validated positive biomarker and an
expert-authored negative control drawn from adjacent biology.

# Tier Drug (modality) Target (MOA)

Indication Biomarker (posi- tive)

Negative Reference

1 T1 Trametinib MEK (MAP2K1, MAP2K2)

Melanoma BRAF TP53 NCT01245062

2 T1 Trastuzumab deruxtecan (T- DXd)

ERBB2, TOP1

Breast, NSCLC, gastric

HER2 TACSTD2 NCT03734029; NCT01275677

3 T1 Vismodegib SMO Basal cell carci- noma; medulloblas- toma

PTCH1 CTNNB1 NCT00833417

4 T1 Palbociclib CDK4/CDK6 Advanced breast cancer

ER, HER2 CCND1 NCT00721461; NCT01740427

5 T2 Osimertinib EGFR Metastatic & adju- vant NSCLC

EGFR activating mutations (ex19del, L858R; T790M for 2L)

BRCA1 NCT02296125

6 T2 Erdafitinib FGFR1/2/3/4 Metastatic urothe- lial carcinoma

FGFR3 mutations (R248C, S249C, G370C, Y373C); FGFR3–TACC3 fusion

CD274 NCT03390504

Ovarian cancer FRα IHC ≥75% cells at ≥2+/3+

BRCA1/2 NCT02631876; NCT04296890 8 T2 Elacestrant ESR1 Advanced breast cancer

FOLR1, TUBB

7 T2 Mirvetuximab so- ravtansine

ESR1 LBD missense mutations (ctDNA)

ER NCT03778931

CDH1 RHOA NCT04551495; NCT03620643 10 T3 CPI-0209 EZH2 Advanced solid tumours & lym- phomas

9 T3 Entrectinib ROS1 Lobular breast, gas- tric, TNBC

ARID1A KMT2D NCT04104776

11 T3 RP-6306 PKMYT1 Advanced solid tu- mours

FBXW7 TP53 NCT04855656

12 T3 Onvansertib PLK1 Metastatic CRC KRAS APC NCT03829410

13 T4 Everolimus mTOR Thyroid cancer TSC1 ESR1 PMID:25295501 14 T4 Olaparib PARP1, PARP2

Prostate cancer BRIP1 PARG NCT02987543

15 T4 Vemurafenib BRAF Pancreatic cancer KRAS PTEN NCT01524978 16 T4 Palbociclib CDK4/6 Myeloma CDKN2A MDM2 NCT00555906


> **Table 10: Full specification of the 30-item translational-medicine biomarker benchmark (Tiers 5–7),**

> continued from Table 9.

# Tier Drug (modality) Target (MOA)

Indication Biomarker (posi- tive)

Negative Reference

17 T5 — BRAF Melanoma MAP2K1 BRCA1/2 NCT01006980 18 T5 — HSP90 Acute lymphoblas- tic leukemia

JAK1 CDKN2A PMID:22271575

19 T5 — AURKA NSCLC SMARCA4 TP53 PMID:28102363 20 T5 — CDK1/2/5/9 Osteosarcoma CCNE1 VEGFA PMID:30266815 21 T5 — FANCM Pan-cancer SMARCAL1 POLE2 PMID:39510066

22 T6 — PRKDC Pan-cancer ATM POLR2G PMID:23761041 23 T6 — PIK3CB Pan-cancer PTEN ARID1A PMID:18594509 24 T6 — ROCK2 Pan-cancer BRCA2 IDH1 PMID:37073955 25 T6 — LIG1 Pan-cancer BRCA2 POLD1 PMID:41070620 26 T6 — FEN1 Pan-cancer WDR48 RUVBL2 PMID:40205037

27 T7 — — Myelodysplastic syndromes

NRAS PTEN PMID:38319256

28 T7 — — Colorectal cancer POLD1 ESR1 PMID:38777726 29 T7 — — Invasive breast car- cinoma

CCND1 IDH1 PMID:18823530

30 T7 — — Medulloblastoma CTNNB1 ERBB2 NCT01878617

17

D Related Work

D.1 Agentic Systems in Biomedical Research

LLM-based agent systems in the life sciences span autonomous experimental design, clinical de- cision support, and broader biological investigation. In experimental design, Coscientist [5] and ChemCrow [6] demonstrated LLM-driven robotic synthesis and tool-grounded chemical reasoning, with later work extending to retrosynthesis [7], in-silico lead generation [8], protein binder design [9], multi-objective protein engineering [10, 11, 12, 13], and early clinical validation of an AI-designed kinase inhibitor [14]. These systems typically address well-scoped molecular or synthetic design tasks rather than multi-source evidence integration.

Clinical agents have been applied to therapeutic question answering over curated knowledge bases [15], adaptive multi-agent triage [16], multimodal precision oncology [17], patient-to-trial matching [18], and histopathology pipeline construction [19]. They operate within structured work- flows such as diagnosis, treatment selection, and eligibility screening, but are not primarily designed for open-ended translational evidence synthesis across heterogeneous sources.

Broader biological agent platforms include Virtual Lab [20], Biomni [21], BioLab [22], OriGene [23], and Medea [24], alongside systems for bioinformatics workflow automation [25, 26], self-verified gene-set analysis [27], and knowledge-graph construction [28]. Our system falls within this category but focuses on translational drug-discovery use cases, integrating evidence from literature, clinical trials, patents, and multi-omics datasets into structured research dossiers for preclinical and clinical development decisions.

18

E Case Study: Generation of Novel Biomarker Hypotheses using Synthetic Lethality Concept and Patient Data

We evaluated the TRESR trial [29] (NCT04497116), which is based on a synthetic-lethality (SL) hypothesis linking ATR inhibition to selected loss-of-function (LoF) alterations. While the study refers to “ATR inhibitor–sensitizing mutations,” these are not explicitly defined, though subsequent reports suggest a focus on DNA damage response genes identified via chemogenomic CRISPR screens [PMID: 37277454].

Thus, we tasked BIORESEARCHER with generating SL biomarker hypotheses for ATR inhibition based on clinical data (input specification in Figure 3). The agent autonomously selected TCGA and METAPRISM cohorts, identified LoF events associated with ATR expression, and evaluated candidates through survival analyses. Specifically, the system executed an end-to-end translational pipeline within the multi-agent orchestration framework (total runtime ≈1352 s; see Figure 8 for the full pipeline view). Scenario classification routed the query to the combination_discovery workflow, after which the translation subagent canonicalized ATR and the relevant clinical indications. Subsequently, the insights_and_signals (CodeAct) subagent conducted downstream multi-omic and survival analyses across multiple cohorts, leveraging iterative model invocations and tool-mediated operations to complete the analysis under the system-generated methodology summarized in Figure 4.

The BIORESEARCHER output combined patient-level data with literature and clinical context, evalu- ating two signal types: (i) LoF-associated ATR upregulation and (ii) survival patterns in low-ATR tumors as a proxy for drug-induced ATR inhibition. A condensed reasoning trace integrating these signals into a candidate ranking is shown in Figure 5.

Across both cohorts, increased ATR expression was most robustly associated with TP53 loss, suggest- ing a pan-cancer marker of ATR pathway activation, though likely reflecting general replication stress rather than specific therapeutic sensitivity. In contrast, the strongest evidence for a synthetic-lethal interaction emerged from ATM loss, which - despite lacking compensatory ATR upregulation - showed the clearest survival signal in low-ATR tumors, consistent with prior preclinical and clinical findings.

Subtype-specific signals further highlighted APC loss in colorectal cancer as the most prominent data- driven discovery, supported by both elevated ATR expression and favorable low-ATR survival patterns, although it lacks prior clinical validation. Finally, ARID1A loss demonstrated only modest support in patient datasets but remains biologically plausible given consistent evidence from external studies, warranting consideration as a secondary translational candidate. The agent-generated biological interpretation across these candidates is summarized in Figure 6.

Overall, the integrated evidence supports the following ranked hypotheses: TP53 LoF as the strongest pan-cancer marker of ATR pathway activation; ATM LoF as the most clinically and mechanistically supported synthetic-lethal biomarker; APC LoF in colorectal cancer as an unexpected data-driven candidate; and ARID1A LoF as a literature-supported but modestly recovered clinical candidate (clinically actionable prioritization in Figure 7). The framework’s key strength lies in combining autonomous multi-cohort analysis with calibrated restraint: where survival models were sparse or unstable, the agent avoided over-interpretation, preserving the reliability of the resulting translational dossier.

The remainder of this appendix shows the artifacts produced at each stage of the pipeline.

19


> **Figure 3: Research goals for automated ATR inhibitor biomarker discovery. Input specification**

> to the BIORESEARCHER system defining the biological context (ATR synthetic lethality), expected
signals (e.g., gene loss linked to high ATR expression, depletion in low-ATR tumors, survival
patterns), and analysis workflow. The pipeline comprises three tasks: (1) candidate biomarker
identification via pan-cancer and subtype-specific loss-of-function and ATR expression analyses; (2)
survival association conditioned on ATR levels; and (3) fixed-timepoint survival analysis in low-ATR
subgroups. A final validation step cross-references results with literature, databases, and clinical
trials to ensure biological and clinical relevance. The specification acts as a programmatic interface
linking user intent to agent execution, enabling reproducible and interpretable biomarker discovery
while constraining the search space.

20


> **Figure 4: System-generated methodology for automated ATR inhibitor biomarker discov-**

> ery. Methodological specification produced by BIORESEARCHER. Cohort composition (TCGA,
METAPRISM) and sample sizes for expression and LoF data is shown. Discovery is defined as
genome-wide testing of LoF vs. ATR expression using directional Mann–Whitney U tests, with
cohort-specific carrier thresholds and significance assessed via p-values and FDR (primary criterion).
Low-ATR subgroups are defined by expression quantiles (bottom 10%, 25%, 33%) for downstream
analyses. Survival analysis combines Cox interaction models with fixed-timepoint analyses (12, 24,
36 months), supplemented by Fisher’s exact tests in sparse settings. Results are contextualized using
canonical ATR and DNA damage response genes. The framework exposes all analytical choices,
ensuring reproducibility and interpretability.

21


> **Figure 5: Multi-signal biomarker prioritization from agent reasoning trace. Condensed execution**

> trace highlighting how BIORESEARCHER integrates heterogeneous evidence to prioritize ATR
biomarker candidates. TP53 loss emerges as the only reproducible pan-cancer signal associated
with increased ATR expression across cohorts. Subtype-specific analysis identifies APC loss as a
strong colorectal cancer signal. In contrast, survival-based analyses reveal ATM loss as the most
synthetic-lethality-like candidate, showing improved outcomes in low-ATR tumors despite lacking
expression association. The system explicitly downweights unstable Cox interaction models and
deprioritizes inconsistent signals (e.g., CDKN2A), illustrating calibrated uncertainty handling. This
figure demonstrates cross-task synthesis, where expression, stratified survival, and cohort-specific
analyses jointly inform hypothesis ranking.

22


> **Figure 6: Agent-generated biological interpretation and hypothesis prioritization. Post-analysis**

> interpretation of candidate ATR biomarkers, summarizing gene-specific evidence across expression
and survival signals. The system distinguishes between robust, data-supported signals (e.g. TP53,
ATM) and exploratory or context-specific candidates (e.g. APC, ARID1A), producing biologically
grounded, testable hypotheses.

23


> **Figure 7: Translation of hypotheses into clinically actionable prioritization. Agent-generated**

> ranking of ATR biomarker hypotheses based on clinical interpretability, integrating expression,
survival, and external plausibility signals. The system distinguishes between stratification markers
(e.g. TP53), synthetic-lethal candidates (e.g. ATM), and exploratory, subtype-specific hypotheses (e.g.
APC, ARID1A).

24


> **Figure 8: End-to-end execution and hypothesis synthesis in BIORESEARCHER. Multi-agent**

> pipeline for ATR biomarker discovery comprising four stages: (1) task decomposition, (2) specialized
biomarker and survival analyses, (3) validation with literature and clinical trials, and (4) reconciliation
and synthesis. The system integrates 37 intermediate artifacts into a single report (∼57k characters),
completing all steps autonomously. Final outputs are ranked, testable hypotheses, including TP53 loss
(pan-cancer ATR activation), ATM loss (top synthetic-lethal candidate), APC loss (colorectal-specific),
and ARID1A loss (weaker signal), while inconsistent findings (e.g., CDKN2A) are deprioritized.
The framework demonstrates end-to-end automation, large-scale result synthesis, and calibrated
uncertainty handling.

25

F Asset Provenance, Licenses, and Terms of Use

This appendix consolidates the third-party assets used by BIORESEARCHER and in our evaluation. For each asset we report the version (where applicable), the original creator or maintainer, a citation, a URL, the license under which the asset is made available, and a brief note on how we use it. Asset usage was verified against each license at the time of submission.

DepMap compliance note. The Broad Institute DepMap Terms of Use permit AI/ML model use with or on the data for internal research use, including non-profit sharing of methodologies, but restrict commercial use and explicitly restrict use of the data to “train, develop, or enhance machine learning or AI models other than for internal research use.” BIORESEARCHER’s sandbox loads DepMap 24Q4 Parquet files for on-the-fly statistical analysis (correlations, Mann–Whitney tests, percentile ranking, survival analysis). DepMap data are not used to fine-tune any model in this work, are not redistributed in our released artifacts, and are re-fetched by the user from the official DepMap portal when reproducing our results.

26

Asset Version Owner / Main- tainer

Citation & URL License / Terms Use in this work

(a) Biomedical databases and ontologies

Local SQLite; en- tity resolution and target/drug lookup. Open Targets Platform 26.03 Open Targets / EMBL-EBI

CC-BY; EBI Terms of Use

ChEMBL 36 EMBL-EBI https: //www.ebi. ac.uk/chembl/

Local SQLite + GraphQL API; target–disease evi- dence. PubChem 2026-04- 29 NCBI / NLM https: //pubchem.ncbi. nlm.nih.gov/

Terms of use for the Open Targets Plat- form - updated June 2021

https: //platform. opentargets. org/

NCBI/NLM public domain; NCBI Web- site and Data Usage Policies

Compound synonym resolution from SMILES.

Ensembl Release 115 EMBL-EBI https://www. ensembl.org/

Gene-symbol to Ensembl-ID map- ping. EFO EMBL-EBI https://www. ebi.ac.uk/efo/

Ensembl Privacy No- tice v 3.0.0

Disease-name to ontology-ID resolu- tion. MONDO v2026-04- 07 Monarch Initiative https://mondo. monarchinitiative. org/

Licensing of EMBL- EBI data resources

CC BY 4.0 Cross-mapped dis- ease IDs.

DOID Disease Ontology consortium

Cross-mapped dis- ease IDs.

https:// disease-ontology. org/

CC BY-SA 4.0 Basal protein char- acteristics and for Uniprot ID mapping. STRING 12.0 SIB / EMBL https:// string-db.org/

Human Protein Atlas 25.0 SciLifeLab / KTH https://www. proteinatlas. org/

CC BY 4.0 Protein–protein interaction graph. Reactome v96 Reactome consor- tium

CC BY 4.0 Pathway annota- tions. GEO (via ARCHS4 pipeline)

https:// reactome.org/

ARCHS4 pipeline Apache 2.0

GEO data: public domain; ARCHS4 pipeline: Apache 2.0

NCBI / NLM https: //www.ncbi.nlm. nih.gov/geo/

GEO expression out- lier detection

Gene Ontology 2026-03- 25 GO Consortium http: //geneontology. org/

CC BY 4.0 Functional annota- tions.

DrugComb 2 Changzhou Univer- sity and CSU

Drug-pair synergy prediction endpoint.

http: //drugcombdb. denglab.org/

ClinicalTrials.gov / AACT

AACT user agree- ment

Trial registration data.

NLM / CTTI https://aact. ctti-clinicaltrials. org/

NCBI/NLM Dis- claimer

PubMed live API NCBI / NLM https: //www.ncbi. nlm.nih.gov/

Literature retrieval.

Google Patents (Ser- pAPI)

live API SerpAPI (third- party)

SerpAPI Terms of Service (commercial API)

Patent search.

https: //serpapi.com/ google-patents-api


> **Table 11: Third-party assets used in BIORESEARCHER and in evaluation.**

27


> **Table 11 (continued).**

Asset Version Owner / Main- tainer

Citation & URL License / Terms Use in this work

(b) Functional-genomics and patient cohorts

Sandboxed Python analyses (depen- dency, expression, mutation stratifica- tion). TCGA 45.0 NCI / NHGRI https: //portal.gdc. cancer.gov/

DepMap (CRISPR, shRNA, omics, pro- teomics, mutations)

DepMap Terms of Use

25Q3 Broad Institute https://depmap. org/portal/

Survival analyses; ATR case study. We do not redistribute controlled-access data. MSK-CHORD 2024 MSK Cancer Data Science Initiative Group

NIH Genomic Data Sharing Policy

BY-NC-ND 4.0 Survival analyses; ATR case study.

https://www. cbioportal. org/study/ summary?id= msk_chord_2024

METAPRISM 30/10/2022 European Bioin- formatics Institute (EMBL-EBI)

Survival analyses; ATR case study.

https://www. ega-archive. org/


> **Table 11 (continued).**

Asset Version Owner / Main- tainer

Citation & URL License / Terms Use in this work

(d) Foundation models, agents, and APIs

GPT-5.4-mini, GPT- 5.4, GPT-5.5 API: 2.14.0 OpenAI https: //platform. openai.com/

Core models for BIORESEARCHER and baselines. GPT-4.1 API: 2.14.0 OpenAI https: //platform. openai.com/

OpenAI Business Terms; usage poli- cies

OpenAI Business Terms

LLM-as-a-judge for single-step tests.

OpenAI Business Terms

OpenAI Codex (CLI) 0.128.0 OpenAI https: //openai.com/

Baseline.

OpenAI Deep Re- search

API: 2.14.0 OpenAI https: //openai.com/

OpenAI Business Terms

Baseline.

Gemini 3.1 Pro API: 1.73.0 Google https://ai. google.dev/

Google APIs Terms of Service

Baseline.

Anthropic Commer- cial Terms of Service

Claude Code 2.1.128 Anthropic https://www. anthropic.com/

Baseline.

CellType Agent 28-03- 2026 Jiawen Chen, Jiang- hao Zhang, Huaxiu Yao, Yun Li

Baseline.

https: //github.com/ jianghao-zhang/ CellTypeAgent/

Medea 26-03- 2026 [24] https: //github.com/ mims-harvard/ MEDEA

Apache-2.0 Baseline.

Apache 2.0 Embedding model for the conference RAG index.

all-MiniLM-L6-v2 2.0 SentenceTransformers https:

//huggingface. co/ sentence-transformers/ all-MiniLM-L6-v2

28


> **Table 11 (continued).**

Asset Version Owner / Main- tainer

Citation & URL License / Terms Use in this work

(e) Software libraries and frameworks

DeepEval 3.9.7 Confident AI [4]; https: //github.com/ confident-ai/ deepeval

Apache 2.0 LLM-as-a-judge framework.

Apache 2.0 Vector store for the conference RAG in- dex.

ChromaDB 1.5.7 Chroma https: //github.com/ chroma-core/ chroma

BSD-3-Clause SMILES standardis- ation. pandas, numpy, scipy 2.3.3 / 2.1.3 / 1.17.1

RDKit 2026.3.1 RDKit consortium https://www. rdkit.org/

NumFOCUS https: //numpy.org/, etc.

BSD-3-Clause Sandbox numerics.

LangGraph / LangChain

1.1.6 / 1.2.15 LangChain Inc. https: //github.com/ langchain-ai/ langgraph

MIT Orchestration frame- work for the agent graphs.


> **Table 11 (continued).**

Asset Version Owner / Main- tainer

Citation & URL License / Terms Use in this work

(f) Benchmarks

BixBench-Verified-50 50- question subset

[1]; https: //huggingface. co/datasets/ phylobio/ BixBench-Verified-50

Apache 2.0 Quantitative- reasoning evalu- ation.

FutureHouse / Phylo- bio

193- question track

Luo et al. [2]; https: //github. com/EperLuo/ BaisBench

MIT Open-ended biological-discovery evaluation.

BaisBench (Scientific Discovery, BAIS-SD)

29
