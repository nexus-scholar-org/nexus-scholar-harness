---
workspace_id: "SCI-000129"
doi: "10.1145/3786149.3788298"
title: "On the Use of a Large Language Model to Support the Conduction of a Systematic Mapping Study: A Brief Report from a Practitioner’s View"
year: 2026
extraction_engine: "pymupdf"
---
# 2026 Barros On the Use of a Large Language Model to Support th

On the Use of a Large Language Model to Support the Conduction of a Systematic Mapping Study: A Brief Report from

a Practitioner’s View

Cauã Ferreira Barros

Marcos Kalinowski Pontifical Catholic University of Rio de Janeiro (PUC-Rio)

Informatics Institute Federal University of Goiás

Rio de Janeiro, Rio de Janeiro, Brazil

Goiânia, Goiás, Brazil

kalinowski@inf.puc-rio.br

cauabarros@ufg.br

Mohamad Kassab Associate Professor in CS at Boston University and

Valdemar Vicente Graciano Neto

Federal University of Goiás

Visiting Professor in CS at NYUAD

Goiânia, Goiás, Brazil valdemarneto@ufg.br

Boston, Massachusetts, USA

mkassab@bu.edu


## Abstract

ACM Reference Format: Cauã Ferreira Barros, Marcos Kalinowski, Mohamad Kassab, and Valdemar Vicente Graciano Neto. 2026. On the Use of a Large Language Model to Support the Conduction of a Systematic Mapping Study: A Brief Report from a Practitioner’s View. In 3rd International Workshop on Methodological Issues with Empirical Studies in Software Engineering (WSESE ’26), April 12–18, 2026, Rio de Janeiro, Brazil. ACM, New York, NY, USA, 6 pages. https://doi.org/10.1145/3786149.3788298

The use of Large Language Models (LLMs) has drawn growing interest within the scientific community. LLMs can handle large volumes of textual data and support methods for evidence syn- thesis. Although recent studies highlight the potential of LLMs to accelerate screening and data extraction steps in systematic re- views, detailed reports of their practical application throughout the entire process remain scarce. This paper presents an experi- ence report on the conduction of a systematic mapping study with the support of LLMs, describing the steps followed, the necessary adjustments, and the main challenges faced. Positive aspects are discussed, such as (i) the significant reduction of time in repetitive tasks and (ii) greater standardization in data extraction, as well as negative aspects, including (i) considerable effort to build reli- able well-structured prompts, especially for less experienced users, since achieving effective prompts may require several iterations and testing, which can partially offset the expected time savings, (ii) the occurrence of hallucinations, and (iii) the need for constant manual verification. As a contribution, this work offers lessons learned and practical recommendations for researchers interested in adopting LLMs in systematic mappings and reviews, highlighting both efficiency gains and methodological risks and limitations to be considered.

1 Introduction

Systematic mappings and reviews can be considered rigorous meth- ods for consolidating scientific knowledge, especially in the field of Software Engineering. However, the conduction of such efforts involves long and laborious steps, such as screening a large number of studies, carefully reading full texts, and performing structured data extraction. These processes, in addition to requiring weeks or even months of dedication, are also subject to inconsistencies among reviewers and the impact of cognitive fatigue [8, 16].

In this context, Large Language Models (LLMs) emerge as alter- natives capable of supporting the repetitive and intensive stages of these methods. Recent studies have demonstrated that LLMs (i) can accelerate the initial screening of articles, (ii) assist in extracting relevant information, and even (iii) improve consistency among reviewers [14, 15]. Despite these advances, the literature still fo- cuses on feasibility analyses or experiments restricted to specific stages, leaving open questions regarding the practical application of these models throughout the entire cycle of a systematic review or mapping [1, 13].

CCS Concepts

• Software and its engineering →Software notations and tools.

Keywords

The systematic mapping study discussed in this experience re- port originally investigated the use of Large Language Models to support qualitative research and qualitative analysis tasks. This mapping aimed at identifying how LLMs have been applied in qual- itative studies, as well as their reported benefits and challenges. In the present work, we revisit the same set of primary studies and focus on reporting the experience of automating and comparing key stages of that mapping—specifically study selection and data extraction—using LLMs. Therefore, this article does not introduce new domain findings, but rather analyzes the practical implications

Large Language Models; LLMs; Systematic Review; Systematic Map- ping; Experience Report.

This work is licensed under a Creative Commons Attribution 4.0 International License. WSESE ’26, Rio de Janeiro, Brazil © 2026 Copyright held by the owner/author(s). ACM ISBN 979-8-4007-2382-7/26/04 https://doi.org/10.1145/3786149.3788298

77

WSESE ’26, April 12–18, 2026, Rio de Janeiro, Brazil Barros et al.

of LLM-supported execution in an existing systematic mapping study (SMS).

on task definition and inclusion/exclusion clarity, requiring human oversight.

The main contribution of this paper is an experience report on the execution of a systematic mapping study (SMS) with the support of LLMs. It describes the points where the application proved to be advantageous, the challenges faced during execution, and the adjustments necessary to ensure accuracy. The report aims to provide practical contributions to the community by offering time comparisons, accuracy analyses, and critical reflections on risks and verification, as well as proposing recommendations for researchers intending to integrate LLMs into their own systematic studies.

Focusing on domain-specific applications, López-Pineda et al. [10] assessed LLaMA-3 and ChatGPT-4o mini for title and abstract screening in biomedical reviews, reporting high precision and re- duced human effort, though limited to a single domain. In Software Engineering, Huotala et al. [6] compared GPT-3.5 and GPT-4 using different prompting strategies and found that GPT-4 and Few-shot prompting improved accuracy, but full automation remained infea- sible without expert supervision.

Beyond screening performance, reproducibility and methodolog- ical transparency have been identified as key challenges. Felizardo et al. [5] highlighted inconsistencies across model versions and insufficient prompt reporting as major threats to replicability. Com- plementing this perspective, Chen et al. [3] compared fully auto- mated and semi-automated LLM-based selection pipelines, showing that semi-automated approaches achieved higher accuracy (82.7% correct inclusions and 92.2% correct exclusions), reinforcing that human-in-the-loop strategies currently offer the most reliable bal- ance between efficiency and rigor.

2 Background

LLMs are artificial intelligence architectures trained on large vol- umes of textual data with the goal of recognizing complex patterns and generating linguistic outputs similar to human production [9, 12]. Models such as ChatGPT1, LLaMA2, Copilot3, Claude4, and Gemini5 have been applied to tasks ranging from machine translation and text summarization to sentiment analysis and pro- gramming support [2].

Our contribution compared to the related work. Although these works demonstrate important advances, they mainly address specific aspects of LLM usage in reviews (screening, data extraction, or replication challenges), but they do not present an integrated account of the end-to-end experience of conducting an SMS. None of them provide detailed comparisons of execution time with and without LLMs, quantitative accuracy assessments across all stages, reports of errors encountered during practice, or descriptions of the real-time adjustments required. The present study seeks to fill this gap by providing a complete empirical ac- count, combining quantitative and qualitative evidence on the use of LLMs in a systematic mapping study, in addition to proposing practical recommendations for researchers interested in applying this approach.

LLMs offer the potential to accelerate time to fulfill some research stages, reduce individual biases, and enhance the scalability of analysis, as demonstrated in applications in the health domain [11] and education [15]. Nevertheless, the literature recognizes that the use of these models does not replace human interpretation but rather serves as complementary support for more consistent and reproducible analyses [1].

In the specific context of Software Engineering, systematic re- views and mappings are characterized by their structured and evidence-based procedures, designed to ensure methodological rigor and transparency in knowledge synthesis [8, 16]. However, these methods face challenges related to large-scale screening and data extraction, which opens space for the adoption of LLMs. Recent studies, such as those by Syriani et al. [15] and Polak and Morgan [14], have already pointed out the feasibility of employing models like ChatGPT in critical stages of systematic reviews, presenting gains in efficiency and accuracy. Other studies, however, highlight risks such as dependence on prompt engineering, inconsistency across model versions, and the possibility of hallucinations [13]. Therefore, there is a clear need to explore empirical reports that evaluate the use of LLMs in systematic mappings, identifying effec- tive practices and remaining limitations.

3 Method and Experience Conduction

This section presents the methodological approach adopted for con- ducting the SMS with LLM support.

Disclaimer. We need to clarify that when we mention the manual extraction in a first step of this study, this actually refers to the manual extraction performed by us and reported in a prior study of ours [2]. Now, we revisited the same studies of prior published work, since we are extending it; then, the same studies were ex- tracted, but now using LLM. The same 219 studies used for first selection in Barros et al. [2] was also used for screening with LLM. The SMS is not published, yet; then, only its conduction is reported here. The SMS is an extension of Barros et al. [2]. The manual procedures reported in Barros et al. [2] were conducted between November 2024 and January 2025, whereas the new LLM-based conduction occurred between July and October 2025. Because of this temporal gap, the reported estimates of manual execution time may not be perfectly precise, as some degree of recall bias or loss of reference regarding the exact duration of manual activities may have occurred.


## Related Work. Several studies have investigated the use of LLMs

to support screening and data extraction in systematic reviews.
Khraisha et al. [7] showed that GPT-4 can achieve performance
comparable to human reviewers under well-structured prompts,
but highlighted strong sensitivity to prompt design and data imbal-
ance. Similarly, Delgado-Chaves et al. [4] evaluated 18 LLMs across
biomedical reviews and reported workload reductions ranging from
33% to 93%, while emphasizing that performance depends heavily

1https://chat.openai.com 2https://ai.meta.com/llama/ 3https://copilot.microsoft.com/ 4https://claude.ai/ 5https://gemini.google.com

78

Large Language Model to Support a Systematic Mapping Study: A Practitioner’s View WSESE ’26, April 12–18, 2026, Rio de Janeiro, Brazil

execution, highlighting the time savings, accuracy rates, and verifi- cation approaches adopted.

Protocol Definition. The starting point was the development of a protocol following the guidelines of Kitchenham and Charters [8] and Wohlin et al. [16]. The research questions, the databases to be consulted, the inclusion and exclusion criteria, and the data extraction procedure were defined. This protocol was essential to ensure methodological rigor and comparability of results, serving as a guide for both the manual application and the application with LLM support. Search and Selection Strategy: The searches were carried out in widely recognized digital databases (Scopus6, IEEE Xplore7, ACM Digital Library 8, among others). In a first moment, the screening of titles and abstracts was conducted manually, following the es- tablished criteria. Subsequently, the same process was performed with the support of ChatGPT-4, using a carefully structured prompt that explicitly stated the inclusion and exclusion criteria. This ap- proach made it possible to compare the efficiency of the manual and automated processes, identifying both gains and limitations. Data Extraction: The data extraction stage was conducted under two fully executed conditions across the entire study scope: (i) manually, using standardized forms completed by human reviewers, and (ii) automatically, with LLM support, using extraction templates in questionnaire format. For each selected article, both procedures were independently performed in full, allowing direct comparison between manual and automated results. The model outputs were then manually reviewed to validate consistency and accuracy. Verification and Risk Mitigation: Acknowledging the risks of hallucination and bias in LLMs, a double-checking strategy was adopted. First, each piece of data automatically extracted was re- viewed by at least one human reviewer. Second, discrepancies be- tween the two approaches (manual and automated) were recorded and discussed after full-text reading, in order to understand the limits of the model’s contribution. This verification was essential to mitigate factual errors and inconsistencies.


> **Table 1: Comparison between Manual Execution and LLM-**

> Assisted Execution.

Aspect Manual Execu- tion

LLM-Assisted Execu- tion (ChatGPT-4)

Screening Time

Approximately 9 hours (reduction of 98%) Extraction Time

Approximately 23 days (219 studies)

Approximately 1 hour (reduction of 99%) Screening Accuracy

Approximately 7 days (13 studies)

Approximately 95% agreement (208 correct out of 219 studies; 11 hallucinations identi- fied) Extraction Accuracy

Defined by consen- sus among review- ers

Approximately 92.3% agreement (12 correct out of 13 studies; 1 error identified) Main Risks Human reading er- rors or fatigue

High, but subject to inconsistencies among reviewers

Hallucinations, depen- dence on prompt engi- neering, inconsistency across model versions Verification Applied

Cross-checking among human reviewers

Double-checking: com- parison with manual re- sults + review of dis- crepancies

Regarding accuracy, the agreement between human reviewers was considered the reference standard. In the screening stage (title and abstract reading), the LLM achieved approximately 95.0% ac- curacy (208 correct out of 219 studies), with 11 hallucination cases in which it began answering the questionnaire with information from other works. In the data extraction stage, the LLM reached approximately 92% accuracy (12 correct out of 13 studies), with 1 error identified. These results indicate the potential to accelerate repetitive stages but remain insufficient to eliminate the need for rigorous human supervision, especially to detect hallucinations and inconsistencies.

4 Experience Report

This section reports the empirical results of the LLM-supported SMS execution, focusing on time, accuracy, prompt adjustments, and exploratory tests with other LLMs.

4.1 Comparison of Time and Accuracy

One of the central objectives was to compare the performance be- tween the two methods. The complete manual process of screening and data extraction required approximately 23 days for the screen- ing of 219 studies and 7 days for the data extraction of 13 studies, totaling around 30 days of work conducted by two researchers [2]. In contrast, the process supported by the LLM was completed in approximately 9 hours for screening the 219 studies and 1 hour for extracting data from 13 studies, representing a significant reduc- tion in the required time. It is important to note that the manual execution did not occur continuously over the 30 days, as it would be unfeasible to maintain this activity without breaks. Table 1 sum- marizes the comparison between the manual and LLM-assisted

In this report, LLM-supported activities refer only to execut- ing study selection and data extraction using previously defined prompts. Prompt design and iterative refinement were performed prior to execution and were not included in the reported LLM time.

4.2 Adjustments During Conduction

Throughout the screening and extraction processes, it was neces- sary to adjust the prompts four times and six times, respectively, mainly to address ambiguities and improve the standardization of outputs. Furthermore, some stages, such as the analysis of the extracted data, proved to be unfeasible to automate reliably, since in more than half of the cases the model retrieved information from sources other than the target study. This reinforces the importance of human judgment in ensuring the accurate analysis of the data obtained.

6https://www.scopus.com/ 7https://ieeexplore.ieee.org/ 8https://dl.acm.org/

79

WSESE ’26, April 12–18, 2026, Rio de Janeiro, Brazil Barros et al.

4.3 Tests with Other Models

(50 studies for screening and 10 for extraction), which constrains the generalizability of the observed results.

With the aim of comparing performance and identifying promising LLMs, additional tests were conducted after validating the outputs obtained by ChatGPT. The models Gemini PRO, Manus, and Copi- lot were evaluated using subsets of studies previously classified correctly by ChatGPT. In the screening process, 50 studies were analyzed: Manus correctly classified 49 (98%), Gemini PRO 45 (90%), and Copilot 30 (60%). In the data extraction process, 10 studies were considered: Manus achieved 4 correct (40%), Gemini PRO 9 (90%), and Copilot 6 (60%). Table 2 presents the performance results for each model in both the screening and data extraction tasks.

These sample sizes are sufficient for an experience report focused on practical feasibility, observed behavior, and methodological im- plications. However, they do not support strong statistical claims or broad generalizations regarding model performance. Future studies with larger datasets and multiple domains are required to validate the trends identified in this work.

5.3 Interpretive Nature of SMS and Implications for LLM Support

Systematic mapping studies in software engineering combine in- terpretive activities with operational and repetitive tasks. While judgments about relevance, meaning, and synthesis require contex- tual understanding and critical reading, other stages—such as large- scale screening and structured data extraction—involve substantial mechanical effort. In this context, the time reductions reported in this study should not be interpreted as a proxy for methodological quality, but rather as evidence that LLMs can selectively support low-level and repetitive activities without replacing human inter- pretation.


> **Table 2: Accuracy of other LLM models.**

Model Screening (50 studies)

Extraction (10 studies)

Manus 49 (98%) 4 (40%) Gemini PRO 45 (90%) 9 (90%) Copilot 30 (60%) 6 (60%)

The purpose of this work, and particularly of this section, is not to compare other models to determine whether their performance is superior or inferior to ChatGPT. Rather, the objective is to explore models with potential for future investigation. That said, the results reveal a significant variation in performance among the models, with Gemini PRO standing out for its robustness in data extraction and Manus in screening, while Copilot showed inferior performance in both scenarios.

Nevertheless, reliance on LLM outputs—even when followed by human verification—introduces important risks. Verification presupposes that researchers possess sufficient familiarity with the primary studies to recognize omissions, misinterpretations, or oversimplifications. If engagement is limited to model-generated outputs, relevant information that was not extracted may remain unnoticed, potentially weakening later interpretive stages. This concern is particularly relevant from a training perspective, as systematic mappings also function as a learning process through which researchers develop domain understanding and methodolog- ical rigor.

5 Discussion

This section discusses the empirical findings reported in the previ- ous section, focusing on their implications for the use of LLMs in systematic mapping studies.

Taken together, these observations reinforce that LLMs should be integrated cautiously and deliberately, as complementary tools within human-centered workflows. Their value lies in supporting efficiency in operational stages, while preserving direct engage- ment with the source material as a prerequisite for trustworthy interpretation and synthesis.

5.1 Model Variability and Task Dependency

The comparative evaluation of different LLMs revealed substan- tial variability in performance across tasks. Gemini PRO achieved stronger results in data extraction, Manus performed best in the screening stage, and Copilot showed inferior performance in both tasks. These results indicate that LLM effectiveness is task-dependent and cannot be assumed to be consistent across different stages of a systematic mapping study.

6 Lessons Learned

Based on the reported experience, some recommendations can guide researchers interested in adopting LLMs in systematic re- views and mappings. First, it is essential to document prompts in detail and keep them consistent in order to ensure reproducibil- ity. Second, a manual verification strategy should be adopted in all critical stages, especially in screening and data extraction, to mitigate hallucinations and interpretation errors. In addition, the use of structured templates for data extraction is recommended to increase the standardization of results. It also proved important to continually remind the model of the task’s objective, thereby reduc- ing context drift and maintaining coherence in responses. Finally, it is crucial to restrict the use of LLMs to mechanical and repeti- tive tasks, preserving human judgment in interpretive and creative stages, thus ensuring methodological rigor without compromising efficiency.

As shown in Table 2, the models exhibited task-dependent per- formance, reinforcing that LLM adoption should be preceded by task-specific empirical validation.

Rather than identifying a universally superior model, these find- ings emphasize that model selection should be treated as a method- ological decision, grounded in empirical validation and aligned with the specific objectives of each stage of the mapping process.

5.2 Sample Size and Scope Limitations

This experience report is subject to limitations related to sample size and scope. While the screening stage involved 219 studies, the data extraction phase was conducted on a smaller subset of 13 studies. In addition, the evaluation of other LLMs relied on reduced samples

80

Large Language Model to Support a Systematic Mapping Study: A Practitioner’s View WSESE ’26, April 12–18, 2026, Rio de Janeiro, Brazil

In this study, structured templates refer to predefined extraction prompts designed as fixed questionnaires. These templates define, in advance, the exact set of questions to be answered for each pri- mary study, ensuring that the same information is systematically extracted across all articles.

Although LLMs proved effective in supporting repetitive exe- cution tasks, human oversight remained essential throughout the study. Interpretive activities, such as synthesizing findings and categorizing contributions, require contextual and methodological judgment that the model could not reliably demonstrate. In addition, human verification was necessary to identify hallucinations and in- consistencies in both screening and data extraction outputs. These observations reinforce that automation can support execution, but cannot replace human responsibility in ensuring analytical rigor and factual correctness.

Take away Lessons. The conduction of an SMS with LLM support allowed us to identify a set of relevant lessons that can be used by the research community, as follows.

Lesson 1: Time Efficiency is Significant but Contextual

Evidence note. Eleven hallucinations were identified during the screening of 219 studies, and one incorrect extraction was detected among 13 analyzed papers, confirming the need for continuous human verification and interpretive control.

LLMs can drastically reduce execution time in screening and extraction, but these gains are context-dependent and still re- quire human supervision.

Lesson 4: Hybrid Workflows are the Way Forward

The main advantage observed was the significant reduction in execution time during the screening and extraction stages. The LLM accelerated repetitive and low-complexity tasks, allowing re- searchers to focus on higher-value analytical activities. However, these efficiency gains do not eliminate the need for human super- vision and should be interpreted in context. The magnitude of the observed reduction depends on factors such as task characteristics, data quality, and prompt design. In addition, the manual and LLM- assisted executions were conducted in different periods, which may introduce minor imprecision in the reported time estimates. There- fore, while the reduction in execution time is substantial, it should be understood as a context-dependent improvement rather than a universal outcome.

LLMs are valuable support tools, but not self-sufficient replace- ments.

From a scientific perspective, the experience revealed that the use of LLMs in systematic mappings is feasible but not self-sufficient. These models can serve as valuable support tools, provided they are embedded in workflows that combine partial automation with targeted human supervision. Complete delegation to the model still entails risks of losing methodological rigor.

Evidence note. Accuracy levels of approximately 95% in screen- ing and 92% in data extraction were achieved only after manual verification, indicating that a hybrid human-in-the-loop workflow was necessary to ensure reliable results.

Evidence note. Manual screening and extraction required approxi- mately 23 days and 7 days respectively, whereas the LLM completed the same activities in about 9 hours and 1 hour, corresponding to a reduction of approximately 98–99%. These estimates are indicative, as the manual (Nov 2024–Jan 2025) and LLM-assisted (Jul–Oct 2025) executions were performed in different time periods.

Lesson 5: Gemini PRO Shows Promise Gemini PRO demonstrated robust accuracy and deserves atten- tion in future research.

Gemini PRO showed promising results in the tests with other models, approaching the performance of ChatGPT and surpassing other models tested. This indicates that Gemini PRO is a model worth monitoring in future research, as it may represent a viable alternative for systematic mappings and reviews.

Lesson 2: Prompt Design is Critical

Small changes in prompts can produce large variations in accu- racy.

Evidence note. In comparative tests, Gemini PRO achieved 90% accuracy in data extraction (9 correct out of 10 studies) and 90% accuracy in screening (45 correct out of 50 studies), outperform- ing Copilot and closely matching the performance observed with ChatGPT.

The dependency on well-structured prompts proved critical: small variations in formulation resulted in notable changes in re- sponse accuracy. In addition, hallucinations and inaccurate extrac- tions occurred. This reinforces the need for manual verification and clear documentation of the prompts used, in order to ensure reproducibility.

7 Limitations and Threats to Validity

For instance, open-ended questions tended to yield verbose an- swers and occasional unsupported additions, whereas option-based answers produced more consistent outputs and fewer hallucina- tions.

This experience report has limitations regarding generalizability. The procedures, challenges, and outcomes reflect the experience of a single researcher conducting a systematic mapping study with LLM support. Results may vary for other researchers depending on factors such as expertise, application domain, prompt design, and in- terpretation strategy. Therefore, the findings should be interpreted as context-dependent rather than universal.

Evidence note. During the study, the screening prompt was re- fined four times and the extraction prompt six times to improve precision and reduce ambiguity, demonstrating the sensitivity of LLM performance to prompt wording.

A second limitation concerns the comparison of execution time between manual and LLM-assisted processes. The manual proce- dure was conducted first, followed by the LLM-assisted execution, which extended the overall duration of the study. This sequential execution may affect the reported time estimates, as parallel or

Lesson 3: Human Oversight Remains Essential

Automation supports execution, but interpretation and verifica- tion must remain under human control.

81

WSESE ’26, April 12–18, 2026, Rio de Janeiro, Brazil Barros et al.

controlled executions could lead to different results. Thus, the time comparisons should be considered indicative rather than absolute.

with Empirical Studies in Software Engineering (WSESE). IEEE/ACM, Ottawa, ON, Canada, 48–55. doi:10.1109/WSESE66602.2025.00015 [3] Yuying Chen, Jie Zhou, Lijun Liu, Qiang Hu, Wei Zhang, and Hong Li. 2025.

Despite these limitations, the study provides empirical evidence on the practical use of LLMs in systematic mappings and offers insights to support future research and methodological refinement.

Can large language models fully automate or partially assist paper selection in systematic reviews? British Journal of Ophthalmology 109, 2 (2025), 145–151. doi:10.1136/bjo-2024-325878 [4] Sofia Delgado-Chaves, Daniel González-García, Andreas Henningsen, Miguel A.

Navarro, and Enrique Alfonseca. 2025. Transforming Literature Screening: The Emerging Role of Large Language Models in Systematic Reviews. Proceedings of the National Academy of Sciences (PNAS) 122, 4 (2025), 962–974. doi:10.1073/pnas. 2404768122 [5] Kleinner R. Felizardo, Anderson Deizepe, Douglas Coutinho, Guilherme Gomes,

8 Conclusion

This experience report has shown that the use of LLMs in conduct- ing a systematic mapping study can yield significant gains in terms of efficiency and initial consistency, particularly in the screening and data extraction stages. At the same time, it demonstrated that these gains are accompanied by risks and limitations that cannot be overlooked, such as dependence on prompts, the occurrence of hallucinations, and the need for continuous human verification.

Matheus Meireles, Marco Gerosa, and Igor Steinmacher. 2025. On the difficulties of conducting and replicating systematic literature reviews studies using LLMs in software engineering. In Proceedings of the 2025 IEEE/ACM International Workshop on Methodological Issues with Empirical Studies in Software Engineering (WSESE). IEEE, 20–23. doi:10.1109/WSESE62711.2025.00012 [6] Satu Huotala, Mika V. Mäntylä, Umer Farooq, and Uolevi Nikula. 2024. The

Promise and Challenges of Using LLMs to Accelerate the Screening Process of Systematic Reviews. In Proceedings of the International Conference on Evaluation and Assessment in Software Engineering (EASE 2024). ACM, 110–120. doi:10.1145/ 3661167.3661172 [7] Qusai Khraisha, Elie A. Akl, Nadav Barda, Daniel Blanco, Igor J. Borges do

Unlike related works that evaluated isolated stages or discussed general challenges, this study provided an integrated end-to-end account, presenting comparisons of time, accuracy, and necessary adjustments during practical conduction. As a scientific contribu- tion, the article demonstrates that LLMs are promising tools to support systematic reviews, but they must be embedded in hybrid workflows, where partial automation and critical supervision go hand in hand.

Nascimento, Anna Chaimani, and Gabriel Tsafnat. 2024. Can large language models replace humans in the systematic review process? Evaluating GPT-4’s efficacy across screening, data extraction, and risk-of-bias assessment. Research Synthesis Methods (2024). doi:10.1002/jrsm.1778 Advance online publication. [8] Barbara Kitchenham and Stuart Charters. 2007. Guidelines for performing system-

atic literature reviews in software engineering. Technical Report EBSE Technical Report 2007-001. Keele University and Durham University. [9] Pankaj Kumar. 2024. Large language models (LLMs): survey, technical frame-

Thus, the main message is clear: LLMs do not replace the role of researchers in systematic mappings, but they can enhance execution capacity and accelerate processes when used judiciously. Future progress will depend not only on technological improvements in the models but also on the development of solid methodological protocols that guide their responsible integration into empirical studies.

works, and future challenges. Artificial Intelligence Review (2024). doi:10.1007/ s10462-024-10888-y [10] Ana López-Pineda, Ángel Gómez-García, Alberto Esteban-Gil, and Carlos Álvarez

Pérez. 2025. Validation of large language models LLaMA 3 and ChatGPT-4o mini for title and abstract screening in biomedical systematic reviews. Research Synthesis Methods (2025). doi:10.1002/jrsm.1844 Advance online publication. [11] William S. Mathis, Siyuan Zhao, Nicole Pratt, Jordan Weleff, and Stefano De

Paoli. 2024. Inductive thematic analysis of healthcare qualitative interviews using open-source large language models: How does it compare to traditional methods? Computer Methods and Programs in Biomedicine 255 (2024), 108356. doi:10.1016/j.cmpb.2024.108356 [12] Bonan Min, Heather Ross, Elior Sulem, Arman Cohan, Trung H. Nguyen, Oier

Acknowledgments

ChatGPT was also employed for text translation into English, with all versions subsequently revised manually to ensure precision, clarity, and consistency. All translations were further verified by human reviewers regarding spelling, grammar, and methodological integrity. This study was financed in part by the Coordenação de Aperfeiçoamento de Pessoal de Nível Superior – Brazil (CAPES) – Finance Code 001. This work has also been partially funded by the project Research and Development of Computational Techniques for Security and Privacy of Second-Generation Multimodal Data, supported by the Advanced Knowledge Center in Immersive Tech- nologies (AKCIT), with financial resources from the PPI IoT of the MCTI grant number 057/2023, signed with EMBRAPII. The support provided by these funding sources was fundamental for both the execution and publication of this research.

Sainz, Eneko Agirre, Iz Beltagy, and Dan Roth. 2023. Recent Advances in Natural Language Processing via Large Pre-Trained Language Models: A Survey. Comput. Surveys 56, 2 (2023), 30:1–30:40. doi:10.1145/3605943 [13] Stefano De Paoli. 2024. Performing an inductive thematic analysis of semi-

structured interviews with a large language model: An exploration and provoca- tion on the limits of the approach. Social Science Computer Review 42, 4 (2024), 997–1019. doi:10.1177/08944393231203023 [14] Michal P. Polak and David Morgan. 2024. Extracting accurate materials data from

research papers with conversational language models and prompt engineering. Nature Communications 15 (2024), 1569. doi:10.1038/s41467-024-45914-8 [15] Eugene Syriani, Istvan David, and Gauransh Kumar. 2024. Screening articles

for systematic reviews with ChatGPT. Journal of Computer Languages 80 (2024), 101287. doi:10.1016/j.cola.2024.101287 [16] Claes Wohlin, Marcos Kalinowski, Kleinner R. Felizardo, and Emilia Mendes. 2022.

Successful combination of database search and snowballing for identification of primary studies in systematic literature studies. Information and Software Technology 147 (2022), 106908. doi:10.1016/j.infsof.2022.106908

Data Availability Statement. All prompts and LLM outputs used in this study are publicly available on Zenodo for reproducibility purposes at: https://doi.org/10.5281/zenodo.14177022.


## References

[1] Muneera Bano, Rashina Hoda, Didar Zowghi, and Christoph Treude. 2024. Large

language models for qualitative research in software engineering: Exploring opportunities and challenges. Automated Software Engineering 31, 1 (2024), 8. doi:10.1007/s10515-023-00393-0 [2] Cauã F. Barros, Bruna B. Azevedo, Valdemar V. G. Neto, Marcos Kalinowski, Mo-

hamad Kassab, Hugo A. D. do Nascimento, and Michelle C. G. S. P. Bandeira. 2025. Large Language Model for Qualitative Research: A Systematic Mapping Study. In Proceedings of the 2025 IEEE/ACM International Workshop on Methodological Issues

82
