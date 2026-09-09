---
workspace_id: "SCI-000106"
doi: null
title: "Compiling Prompts, Not Crafting Them: A Reproducible Workflow for AI-Assisted Evidence Synthesis"
year: 2025
extraction_engine: "pymupdf"
---
# 2025 Susnjak Compiling Prompts, Not Crafting Them A 

Compiling Prompts, Not Crafting Them: A Reproducible

Workflow for AI-Assisted Evidence Synthesis

A Research in Brief Preprint

Teo Susnjak ∗ School of Mathematical and Computational Sciences

Massey University Albany, New Zealand

arXiv:2509.00038v1  [cs.CL]  22 Aug 2025

September 3, 2025


## Abstract

Large language models (LLMs) offer significant potential to accelerate systematic literature reviews (SLRs), yet current approaches often rely on brittle, manually crafted prompts that compromise reliability and reproducibility. This fragility undermines scientific confidence in LLM-assisted evidence synthesis. In response, this work adapts recent advances in declarative prompt optimisation, developed for general-purpose LLM applications, and demonstrates their applicability to the domain of SLR automation. This research proposes a structured, domain-specific framework that embeds task declarations, test suites, and automated prompt tuning into a reproducible SLR workflow. These emerging methods are translated into a concrete blueprint with working code examples, enabling researchers to construct verifiable LLM pipelines that align with established principles of transparency and rigour in evidence synthesis. This is a novel application of such approaches to SLR pipelines.

Keywords Systematic Literature Review Automation, Evidence Synthesis, Large Language Models, Reproducibility, Prompt Engineering, Context Engineering, Prompt Optimisation, Prompt Compilation, AI-driven Research Automation

What is already known

• Systematic literature reviews (SLRs) are foundational for evidence-based practice but are notoriously slow and resource-intensive. • Large language models (LLMs) show significant promise for automating SLR tasks, but their performance is highly sensitive to the phrasing of input prompts. • This "prompt fragility" makes LLM-assisted workflows unreliable, difficult to reproduce, and raises concerns about their scientific validity.

What is new

• This paper introduces a declarative framework that adapts state-of-the-art prompt optimisation techniques from the general AI field and applies them specifically to the domain of SLR automation. • It replaces manual, ad-hoc "prompt alchemy" with a rigorous, four-step programmatic process: (1) formally defining the research goal, (2) codifying the quality standard with data, (3) automatically compiling an optimal prompt, and (4) packaging the result as a verifiable digital artefact. • The study provides both a conceptual blueprint and a functional, code example, demonstrating a practical pathway to building robust and reproducible LLM pipelines for evidence synthesis.

∗Corresponding author: t.susnjak@massey.ac.nz

Compiling Prompts, Not Crafting Them A Preprint

Potential impact for research automation and synthesis researchers

• This work provides researchers and methodologists with a clear, actionable methodology to harness the speed of LLMs without sacrificing the scientific rigour and reproducibility that are cornerstones of evidence synthesis. • The proposed framework offers a path toward establishing new standards for transparency and auditability in AI-assisted reviews, allowing others to verify and replicate automated steps with precision. • It lays the groundwork for a future ecosystem of modular, verifiable, and reusable AI components for all stages of an SLR, empowering the community to build more trustworthy and efficient tools for research synthesis.

1 Introduction

Large language models (LLMs) now offer a promising path for automating systematic literature reviews (SLRs) [1]. Recent studies show that models have remarkable potential to automate all phases of an SLR process, from abstracts screening, data extraction, quality assessment, through to evidence syntheses with promising accuracy [1, 2]. Despite progress, serious concerns persist. LLM outputs can change significantly with small variations in LLM prompts [3]. Model updates can invalidate previously crafted prompts and break reliable pipelines, while cross-model behaviour and accuracy diverges significantly using identical prompts [4]. These LLM sensitivities and fragilities erode trust and widen the reproducibility gap in SLRs and scientific endeavours more broadly. Therefore, there is a need to explore more systematic approaches to the automation of SLRs that ensure reliability and repeatability when employing LLMs for evidence synthesis.

2 Prompt Engineering Crisis

The remarkable reasoning abilities of LLMs have resulted in natural language (NL) becoming framed as a new programming language[5], implying that NLs have become the primary interface for instructing AI systems, with generative models acting as compilers that translate these instructions into correct actions or executable code. However, this ignores the consequences of the ambiguity of NLs which do not have the rigidity and precision of highly syntactic programming languages. Humans rely on context to resolve meaning while programming removes ambiguity and assumptions through precise instructions. Treating LLM prompts as code collapses this difference. Since LLMs do not have the ability to produce same outputs for identical inputs, this results in the current state where prompt engineering has transformed into prompt alchemy. LLM outputs are highly non-deterministic, influenced by ad hoc prompt design choices, sequencing of instructions and slight rephrasings, as well as luck [6]. Subtle variations in prompt formats can result in differences as large as 76 accuracy points [3] on tasks from the Super-NaturalInstructions benchmark. The evidence of this brittleness is also growing in the SLR automation field [7, 1]. While studies identify LLM fragilities, none propose a reproducible, programmatic remedy offering deterministic and more accurate outputs. Table 1 summarises recent works using LLMs to automate different SLR phases, revealing their variability.

3 A Declarative Framework for Reliable and Reproducible SLR Automation

The brittleness of prompt engineering requires a paradigm shift from ad hoc design approaches to programmatic rigour. This work proposes the use of declarative prompt tuning approaches for future SLR automation research, inspired by recent advances in prompt optimisation such as the DSPy[19], GRPO[20] and GEPA[21] frameworks. This study presents a return to a programmatic, and a declarative paradigm specifically, aiming to restore reproducibility in LLM-driven SLR research by decoupling the researcher’s scientific intent (the “what”), from the model’s specific implementation (the “how”). Instead of relying on fragile, hand-crafted prompts, this approach treats LLM workflows for SLR tasks as language model (LM) programs that can be compiled. This compilation entails an automated process that systematically searches for a high-performing LLM-agnostic prompt configuration that satisfies a predefined quality standard or accuracy requirement. This methodology is operationalised through four key components depicted and described in Figure 1 and applicable to all stages of an SLR process. For a concrete illustration, the framework is translated to an example for the abstract screening process below:

2

Compiling Prompts, Not Crafting Them A Preprint

SLR Phase & Study Prompt Engineering Fragility Example

Screening

Shah et al. [8] Accuracy fluctuated by up to 28.3% across prompts Dennstädt et al. [9] Sensitivity/specificity swung from 94.5%/31.8% (Flan-T5) to 81.9%/75.2% (Mixtral) across LLM families and prompts. Cao et al. [10] Reordering or omitting few-shot exemplars altered include/exclude deci- sions for 15% of abstracts. Trad et al. [11] Tightening exclusion thresholds in prompts dropped abstract-error-rate (AER) from 72.1% to 50.7%. Cao et al. [12] Zero-shot prompting achieved sensitivity 16.7–87.5%, vs. optimised prompt 86.7–100.0%.

Data Extraction

Cao et al. [13] Accuracy swung by 15 percentage points across different prompts. Lai et al. [14] LLM-assisted extraction rose from 95.1% to 97.9%, driven by optimised prompts Li et al. [4] Recall for extracting study details varied between 64% and 92% across different LLMs and prompting strategies. Khraisha et al. [15] Accuracy spanned 60% to near-perfect levels (>95%) depending on prompts

Risk of Bias / Quality Assessment

Wang et al. [16] Agreement with clinical guidelines acutely ranged from kappa = –0.002 to 0.984 under different prompting styles, compromising compliance judgments. Lai et al. [17] RoB 1 accuracy shifted from 84.5% to 89.5% across different LLMs and prompt configurations; domain accuracies swung 56.7–98.3%. Lai et al. [14] LLM-only RoB 1 accuracy was 95.7–96.9%; domain scores varied from 87.9% to 100%. Eisele-Metzger et al. [18] Overall RoB2 LLM agreement was 41% (kappa=0.22; domain kappa range 0.10–0.31), varying with prompt phrasing and domain focus. Table 1: Examples of LLM prompt-induced performance swings in SLR tasks

Box 1: Blueprint for a Verifiable Screening Module via Declarative LM-program Tuning


## Abstract Screening Example


## 1. Define the Goal: Screening abstracts for inclusion.

• Task Declaration Inputs follow a fixed schema {title, abstract, keywords}. The label space is {Include, Exclude, Unsure}. Unsure is treated as Include for safety or routed to human review, and

this policy is fixed in the spec. • Context Engineering A versioned context file states the PICO criteria, study designs in scope, and the review questions.


## 2. Codify the Standard Define a machine-testable target.

• Gold-Standard Examples Curate N expert-labeled abstracts not part of the study, representing each possible classification outcome. • Evaluation Metric Primary metric is accuracy.


## 3. Compile the Program Run controlled search over prompts and exemplars.

• The compiler explores instruction templates and up to k few-shot exemplars under a pinned model build with temperature=0, fixed seed, and a set budget B evaluations. All runs log hashes of data, prompts, model ID, and decoding parameters.


## 4. Package the Artefact Emit a shareable, auditable bundle.

• The bundle contains config.yaml (task spec and run controls), prompt.txt and exemplars.json, metrics.json with the test-set results, and a run log. A short mapping lists which PRISMA items the bundle supports, such as protocol transparency and decision traceability. Results are verifiable and recomputable under a pinned environment.

3

Compiling Prompts, Not Crafting Them A Preprint


> **Figure 1: Four Components of the Declarative Language Model-program Tuning Framework**

The conceptual blueprint detailed in Box 1 can be directly implemented using modern programmatic LLM frameworks. To further demonstrate how this can be operationalised, a functional Python implementation of the above illustrated abstract screening module using the DSPy (MIPROv2) library is provided in Appendix A. A MIPROv2 example and an equivalent example using the latest GEPA implementation are made available on Google Colab. The code example in the Appendix A demonstrates a declarative goal definition, a gold-standard dataset and a metric function to codify the standard, an optimiser that compiles the LM-program, as well as how the verifiable artefact is packaged and used to make classifications on new abstracts. This automated compilation process is analogous to the “hyperparameter tuning” in machine learning, in that it uses a validation dataset and a metric to systematically search for an optimal configuration. However, instead of tuning architectural parameters, this framework tunes NL artefacts which comprise the instructions and few-shot examples that guide a fixed, pre-trained model. This positions the method as a rigorous, data-driven alternative to manual prompt engineering, meeting the high scientific standards required for evidence synthesis. This process is can be seen as analogous to the “hyperparameter tuning” process in machine learning that ensures that “near”-optimal parameters are derived for a given model and dataset prior to use; thus, this approach is rigorous and

meets high scientific requirements that manual prompt engineering does not. This probing study calls on researchers in the SLR automation field to empirically investigate this approach and available supporting framework implementations, and thus provide a tangible pathway for researchers to adopt this rigorous and reproducible methodology for fully automating SLRs in a PRISMA-compliant manner.

4 Conclusion

LLMs offer a compelling opportunity to streamline the labour-intensive processes involved in systematic literature reviews, but the current reliance on brittle prompt engineering introduces unacceptable risks to reproducibility and scientific rigour. This exploratory study proposes an alternative: a declarative framework for SLR automation that adapts recent advances in prompt optimisation into a structured, testable, and version-controlled workflow. The contribution here lies in applying declarative prompt tuning approaches, originally developed for general LLM tasks—to the domain of SLR automation, and demonstrating their utility through a proof-of-concept, reproducible implementation. To the best of current knowledge, this represents the first application of such declarative techniques to evidence synthesis workflows. The contribution here lies in adapting emerging declarative prompt optimisation techniques to SLR automation and demonstrating their utility through a reproducible implementation. This prototyping work provides both a conceptual blueprint and a working implementation, illustrating how LLM-assisted evidence synthesis can evolve from fragile, ad hoc prompting into verifiable, auditable, and modular pipelines. Future work should fully test and expand this

4

Compiling Prompts, Not Crafting Them A Preprint

approach to other SLR stages, integrate it into standard reporting frameworks, and foster a community-driven ecosystem of reusable components for transparent, AI-enabled reviews.


## References

[1] Judith-Lisa Lieberum, Markus Töws, Maria-Inti Metzendorf, Felix Heilmeyer, Waldemar Siemens, Christian

Haverkamp, Daniel Böhringer, JoergJ. Meerpohl, and Angelika Eisele-Metzger. Large language models for conducting systematic reviews: on the rise, but not yet ready for use—a scoping review. Journal of Clinical Epidemiology, 181:111746, 2025. doi:10.1016/j.jclinepi.2025.111746.

[2] Teo Susnjak, Peter Hwang, Napoleon Reyes, Andre L. C. Barczak, Timothy McIntosh, and Surangika Ranathunga.

Automating research synthesis with domain-specific large language model fine-tuning. ACM Trans. Knowl. Discov. Data, 19(3), March 2025. ISSN 1556-4681. doi:10.1145/3715964. URL https://doi.org/10.1145/3715964.

[3] Melanie Sclar, Yejin Choi, Yulia Tsvetkov, and Alane Suhr. Quantifying language models’ sensitivity to

spurious features in prompt design or: How i learned to start worrying about prompt formatting. arXiv preprint arXiv:2310.11324, 2023.

[4] Lingbo Li, Anuradha Mathrani, and Teo Susnjak. What level of automation is "good enough"? a benchmark of

large language models for meta-analysis data extraction, 2025. URL https://arxiv.org/abs/2507.15152.

[5] Michael Kearns. Responsible ai in the generative era, May 2023. URL https://www.amazon.science/blog/

responsible-ai-in-the-generative-era. Accessed: 2025-08-01.

[6] Amirhossein Razavi, Mina Soltangheis, Negar Arabzadeh, Sara Salamat, Morteza Zihayat, and Ebrahim Bagheri.

Benchmarking prompt sensitivity in large language models. In European Conference on Information Retrieval, pages 303–313. Springer, 2025.

[7] Moritz Staudinger, Wojciech Kusa, Florina Piroi, Aldo Lipani, and Allan Hanbury. A reproducibility and

generalizability study of large language models for query generation. In Proceedings of the 2024 Annual International ACM SIGIR Conference on Research and Development in Information Retrieval in the Asia Pacific Region, pages 186–196, 2024.

[8] Aaditya Shah, Shridhar Mehendale, and Siddha Kanthi. Efficacy of large language models for systematic reviews.

In 2024 2nd International Conference on Foundation and Large Language Models (FLLM), pages 29–35. IEEE, 2024.

[9] Fabio Dennstädt, Johannes Zink, Paul Martin Putora, Janna Hastings, and Nikola Cihoric. Title and abstract

screening for literature reviews using large language models: an exploratory study in the biomedical domain. Systematic reviews, 13(1):158, 2024.

[10] Christian Cao, Jason Sang, Rohit Arora, Robbie Kloosterman, Matt Cecere, Jaswanth Gorla, Richard Saleh, David

Chen, Ian Drennan, Bĳan Teja, et al. Prompting is all you need: Llms for systematic review screening. medRxiv, pages 2024–06, 2024.

[11] Fouad Trad, Ryan Yammine, Jana Charafeddine, Marlene Chakhtoura, Maya Rahme, Ghada El-Hajj Fuleihan, and

Ali Chehab. Streamlining systematic reviews with large language models using prompt engineering and retrieval augmented generation. BMC medical research methodology, 25(1):130, 2025.

[12] Christian Cao, Jason Sang, Rohit Arora, David Chen, Robert Kloosterman, Matthew Cecere, Jaswanth Gorla,

Richard Saleh, Ian Drennan, Bĳan Teja, et al. Development of prompt templates for large language model-driven screening in systematic reviews. Annals of Internal Medicine, 178(3):389–401, 2025.

[13] Christian Cao, Rohit Arora, Paul Cento, Katherine Manta, Elina Farahani, Matthew Cecere, Anabel Selemon,

Jason Sang, Ling Xi Gong, Robert Kloosterman, et al. Automation of systematic reviews with large language models. medRxiv, pages 2025–06, 2025.

[14] Honghao Lai, Jiayi Liu, Chunyang Bai, Hui Liu, Bei Pan, Xufei Luo, Liangying Hou, Weilong Zhao, Danni Xia,

Jinhui Tian, et al. Language models for data extraction and risk of bias assessment in complementary medicine. npj Digital Medicine, 8(1):74, 2025.

[15] Qusai Khraisha, Sophie Put, Johanna Kappenberg, Azza Warraitch, and Kristin Hadfield. Can large language

models replace humans in systematic reviews? evaluating gpt-4’s efficacy in screening and extracting data from peer-reviewed and grey literature in multiple languages. Research Synthesis Methods, 15(4):616–626, 2024.

[16] Li Wang, Xi Chen, XiangWen Deng, Hao Wen, MingKe You, WeiZhi Liu, Qi Li, and Jian Li. Prompt engineering

in consistency and reliability with the evidence-based guideline for llms. NPJ digital medicine, 7(1):41, 2024.

5

Compiling Prompts, Not Crafting Them A Preprint

[17] Honghao Lai, Long Ge, Mingyao Sun, Bei Pan, Jiajie Huang, Liangying Hou, Qiuyu Yang, Jiayi Liu, Jianing

Liu, Ziying Ye, Danni Xia, Weilong Zhao, Xiaoman Wang, Ming Liu, Jhalok Ronjan Talukdar, Jinhui Tian, Kehu Yang, and Janne Estill. Assessing the risk of bias in randomized clinical trials with large language models. JAMA Network Open, 7(5):e2412687–e2412687, 05 2024. ISSN 2574-3805. doi:10.1001/jamanetworkopen.2024.12687. URL https://doi.org/10.1001/jamanetworkopen.2024.12687. [18] Angelika Eisele-Metzger, Judith-Lisa Lieberum, Markus Toews, Waldemar Siemens, Felix Heilmeyer, Christian

Haverkamp, Daniel Boehringer, and Joerg J Meerpohl. Exploring the potential of claude 2 for risk of bias assessment: Using a large language model to assess randomized controlled trials with rob 2. Research Synthesis Methods, pages 1–18, 2024. [19] Krista Opsahl-Ong, Michael J Ryan, Josh Purtell, David Broman, Christopher Potts, Matei Zaharia, and Omar

Khattab. Optimizing instructions and demonstrations for multi-stage language model programs. In 2024 Conference on Empirical Methods in Natural Language Processing, EMNLP 2024, Hybrid, Miami, United States of America, Nov 12 2024-Nov 16 2024, pages 9340–9366. Association for Computational Linguistics (ACL), 2024. [20] Zhihong Shao, Peiyi Wang, Qihao Zhu, Runxin Xu, Junxiao Song, Xiao Bi, Haowei Zhang, Mingchuan Zhang,

YK Li, Yang Wu, et al. Deepseekmath: Pushing the limits of mathematical reasoning in open language models.

arXiv preprint arXiv:2402.03300, 2024. [21] Lakshya A Agrawal, Shangyin Tan, Dilara Soylu, Noah Ziems, Rishi Khare, Krista Opsahl-Ong, Arnav Singhvi,

Herumb Shandilya, Michael J Ryan, Meng Jiang, Christopher Potts, Koushik Sen, Alexandros G. Dimakis, Ion Stoica, Dan Klein, Matei Zaharia, and Omar Khattab. Gepa: Reflective prompt evolution can outperform reinforcement learning, 2025. URL https://arxiv.org/abs/2507.19457.

Appendix A: Technical Example of a Screening Module for Prompt Optimisation

The conceptual blueprint described in Box 1 can be implemented using programmatic LLM tools like DSPy. The following Python code provides a minimal functional example of how an AbstractScreening module would be structured, tested, and compiled into a verifiable, reproducible digital artefact, translating the declarative framework to the corresponding components of the underlying tool. A more complete example of the code below can be found on a Google Colab notebook.


## 1 import dspy

2 from typing import Literal
3
4 # Define the parameters you want to pass to the chosen LLM
5 # Fix parameters to maximise determnistic responses
6 model_params = {
7
"temperature": 0.0,
8
"top_p": 1.0,
9
"seed": 42,
10
"max_tokens": 1024
11 }
12
13 # LLM and DSPy configuration
14 # Pass the parameters by unpacking the dictionary using **
15 lm = dspy.LM(
16
"openai/gpt-4o-mini",
17
api_key="<YOUR_API_KEY >",
18
**model_params
19 )
20
21 # LLM and DSPy configuration (e.g., dspy.configure) is assumed.
22 dspy.settings.configure(lm=lm)
23
24 ## --- COMPONENT 1: Define the Goal --- ##
25 # This includes both the Task Declaration (the Signature) and the Context Engineering (the specific criteria for this review).
26
27 # 1a: Task Declaration
28 class ScreenAbstract(dspy.Signature):
29
"""Screens an abstract based on predefined research context and criteria."""
30
31
# Input fields for context and the item to be screened.
32
criteria: str = dspy.InputField(desc="Fixed PICOS criteria for the review")
33
study_aims: str = dspy.InputField(desc="The primary objective of the study")
34
research_question: str = dspy.InputField(desc="The research question guiding the review")
35
abstract: str = dspy.InputField(desc="The abstract text to be screened")
36
37
# Output fields with structured constraints.
38
decision: Literal["Include", "Exclude", "Unsure"] = dspy.OutputField()
39
reasoning: str = dspy.OutputField(desc="Brief justification for the decision , referencing the criteria")
40
confidence: float = dspy.OutputField(desc="A score from 0.0 to 1.0 indicating the model’s confidence")
41
42 # 1b: Context Engineering
43 CRITERIA = (
44
"Population: adults 18-65 with major depressive disorder. "

6

Compiling Prompts, Not Crafting Them A Preprint

45 "Intervention: digital CBT via app or web. " 46 "Design: RCTs or non-inferiority trials. " 47 "Outcome: validated depressive symptom scale." 48 ) 49 STUDY_AIMS = "To determine if digital CBT reduces depressive symptoms in adults with MDD." 50 RESEARCH_QUESTION = ( 51 "In adults aged 18-65 with MDD, does digital CBT, compared with usual care, " 52 "reduce depressive symptoms measured using validated scales?" 53 ) 54 55 ## --- COMPONENT 2: Codify the Standard --- ## 56 # This establishes the quality bar with gold-standard examples and a success metric. 57 58 # 2a: Gold-Standard Examples 59 gold_standard = [ 60 dspy.Example( 61 criteria=CRITERIA , study_aims=STUDY_AIMS , research_question=RESEARCH_QUESTION , 62 abstract="An RCT randomized 120 adults 25-60 with DSM-5 MDD to digital CBT vs usual care; 63 PHQ-9 reported at 12 weeks...", 64 decision="Include", 65 reasoning="The abstract describes an RCT in the correct population using digital CBT and a valid 66 outcome measure." 67 ).with_inputs("criteria", "study_aims", "research_question", "abstract"), 68 dspy.Example( 69 criteria=CRITERIA , study_aims=STUDY_AIMS , research_question=RESEARCH_QUESTION , 70 abstract="A cohort study of a web-based CBT tool among teenagers aged 13-17; no control group...", 71 decision="Exclude", 72 reasoning="This is not an RCT and the population (teenagers) is incorrect." 73 ).with_inputs("criteria", "study_aims", "research_question", "abstract"), 74 dspy.Example( 75 criteria=CRITERIA , study_aims=STUDY_AIMS , research_question=RESEARCH_QUESTION , 76 abstract="Participants described as adults with depressive symptoms were assigned to a web program 77 combining CBT content with mindfulness and peer support versus usual care with PHQ-9 at 10 weeks. 78 Formal MDD diagnosis and randomization are not stated and the upper age bound is not clear.", 79 decision="Unsure", 80 reasoning="Intervention fidelity to CBT and confirmation of MDD are uncertain and allocation and age 81 bounds are unclear which prevents a confident decision." 82 ).with_inputs("criteria","study_aims","research_question","abstract"), 83 84 # A real-world set would contain 10-50 high-quality examples. 85 # ... 86 ] 87 88 # 2b: Evaluation Metric 89 def screening_accuracy_metric(gold: dspy.Example , pred: dspy.Prediction , trace=None) -> bool: 90 """A simple metric: the predicted decision must match the gold-standard decision.""" 91 return gold.decision == pred.decision 92 93 ## --- COMPONENT 3: Compile the Program --- ## 94 # An optimizer tunes a program (e.g., a ChainOfThought module) to maximize the chosen metric. 95 # This is declarative LM-program tuning. 96 97 98 optimizer = dspy.MIPROv2(metric=screening_accuracy_metric , num_threads=4) 99 compiled_screener = optimizer.compile( 100 valset=gold_standard[:10], # validation set with a simple approach assuming one has 10 samples 101 trainset=gold_standard[10:], # training set assuming one has more than 10 samples 102 student=dspy.ChainOfThought(ScreenAbstract), 103 max_bootstrapped_demos=0, 104 max_labeled_demos=1, 105 minibatch=False, 106 requires_permission_to_run=False 107 ) 108 109 ## --- COMPONENT 4: Package the Artefact --- ## 110 # The compiled program’s state is saved to a file, creating a reproducible artefact. 111 112 compiled_screener.save(path="screen_abstract_v1.json") 113 114 # --- Usage Example of the Artefact --- 115 # A collaborator can load the artefact and achieve identical performance. 116 loaded_screener = dspy.ChainOfThought(ScreenAbstract) 117 loaded_screener.load("screen_abstract_v1.json") 118 119 new_abstract = ( 120 "This randomized controlled trial enrolled 180 adults aged 28-62 diagnosed with major depressive disorder. 121 Participants received app-based CBT vs wait-list control. Depressive symptoms were measured using PHQ-9 at 8 weeks." 122 ) 123 124 # Run prediction with the loaded, optimized program. 125 prediction = loaded_screener( 126 criteria=CRITERIA , 127 study_aims=STUDY_AIMS , 128 research_question=RESEARCH_QUESTION , 129 abstract=new_abstract 130 ) 131 print("Decision:", prediction.decision) 132 print("Reasoning:", prediction.reasoning) 133 print("Confidence:", prediction.confidence) 134 135 # --- Output Example --- 136 Decision: Include

7

Compiling Prompts, Not Crafting Them A Preprint

137 Reasoning: The study meets all the PICOS criteria: it involves adults with major depressive disorder (Population), uses digital CBT via an app (Intervention), is a randomized controlled trial (Design), and measures outcomes using a validated depressive

symptom scale (Outcome). The study also aligns with the study aims as it investigates the effect of digital CBT on depressive symptoms in adults with MDD. 138 Confidence: 1.0

Listing 1: Python implementation of the proposed framework for an abstract screening module, structured into the four core components: Goal Definition, Standard Codification, Program Compilation, and Artefact Packaging

8
