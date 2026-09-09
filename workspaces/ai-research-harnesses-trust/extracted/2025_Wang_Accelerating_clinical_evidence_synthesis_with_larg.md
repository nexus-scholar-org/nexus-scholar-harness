---
workspace_id: "SCI-000109"
doi: "10.1038/s41746-025-01840-7"
title: "Accelerating clinical evidence synthesis with large language models"
year: 2025
extraction_engine: "pymupdf"
---
# 2025 Wang Accelerating clinical evidence synthesis with larg

npj | digital medicine Article

Published in partnership with Seoul National University Bundang Hospital

https://doi.org/10.1038/s41746-025-01840-7 Accelerating clinical evidence synthesis with large language models

Check for updates

Zifeng Wang1,4, Lang Cao1, Benjamin Danek1,4, Qiao Jin2, Zhiyong Lu2 & Jimeng Sun1,3,4

Clinical evidence synthesis largely relies on systematic reviews (SR) of clinical studies from medical literature. Here, we propose a generative artiﬁcial intelligence (AI) pipeline named TrialMind to streamline study search, study screening, and data extraction tasks in SR. We chose published SRs to build TrialReviewBench, which contains 100 SRs and 2,220 clinical studies. For study search, it achieves high recall rates (Ours 0.711–0.834 v.s. Human baseline 0.138–0.232). For study screening, TrialMind beats previous document ranking methods in a 1.5–2.6 fold change. For data extraction, it outperforms a GPT-4’s accuracy by 16–32%. In a pilot study, human-AI collaboration with TrialMind improved recall by 71.4% and reduced screening time by 44.2%, while in data extraction, accuracy increased by 23.5% with a 63.4% time reduction. Medical experts preferred TrialMind’s synthesized evidence over GPT-4’s in 62.5%-100% of cases. These ﬁndings show the promise of accelerating clinical evidence synthesis driven by human-AI collaboration.

1234567890():,;

1234567890():,;

100 published systematic literature reviews with 2220 associated clinical studies. To align with key steps in the PRISMA statement, we built testing tasks forstudy search,citationscreening,and data extraction.It also consists of manual annotations of 1334 study characteristics and 1049 study results.

Clinical evidence is crucial for supporting clinical practices and advancing new drug development and needs to be updated regularly1. It is primarily gathered through retrospective analysis of real-world data or through prospective clinical trials that assess new interventions on humans. Researchers usually conduct systematic reviews to consolidate evidence from various clinical studies in the literature2,3. However, this process is expensiveandtime-consuming,requiringanaverageofﬁveexpertsand67.3 weeks based on an analysis of 195 systematic reviews4. Moreover, the fast growth of clinical study databases means that the information in these published clinicalreviewsbecomesoutdated rapidly5.Forinstance,PubMed has indexed over 35M citations and gets over 1M new citations annually6. This situation underscores the urgent need to streamline the systematic review processes to document systematic and timely clinical evidence from the extensive medical literature1,7.

This study aims to further ﬁll the gap in adapting LLMs to evidence synthesis tasks, primarily overcoming LLM’s limitations in (1) hallucina- tions, (2) weakness in reasoning with numerical data, (3) overly generic outputs, and (4) lack of transparency and reliability26. Speciﬁcally, we developed an AI-driven pipeline named TrialMind, which is optimized for (1) generating boolean queries to search citations from the literature; (2) building eligibility criteria and screening through the found citations; and (3) extracting data, including study protocols, methods, participant base- lines, study results, etc., from publications and reports. More importantly, TrialMind breaks down into subtasks that adhere to the established practice of systematic reviews23, which facilitates experts in the loop to monitor, edit, and verify intermediate outputs. It also has the ﬂexibility to allow experts to begin at any intermediate step as needed.

Large language models (LLMs) excel at instruction following: they can perform target tasks with the task deﬁnition and examples as the text inputs (namely “prompts”)8. Recent works have hence adopted LLMs for various systematic review and meta-analysis tasks, such as generating searching queries9,10, extracting studies’ attributes11–14, screening citations15–17, and summarizing ﬁndings from multiple studies18–21. However, few have investigated LLMs’ effectiveness across the evidence synthesis process as outlined by standard practice such as PRISMA statement22–25. An under- standing of the strengths and limitations of LLMs in practical systematic literaturereviewand meta-analysistasksiscrucialfortheirdevelopment.To ﬁll this gap, we created a testing dataset TrialReviewBenchbased on

Inthisstudy,weshowthattheTrialMindcan(1)retrieveacomplete list of target studies from the literature, (2) follow the speciﬁed eligibility criteria to rank the most relevant studies at the top, and (3) achieve high accuracyinextractinginformationandclinicaloutcomesfromunstructured documents based on user requests. Beyond providing descriptive evidence, TrialMind can extract numerical clinical outcomes to be standardized as input for meta-analysis (e.g., forest plots). A human evaluation was con- ducted to assess the synthesized evidence. Finally, to validate the practical

1Siebel School of Computing and Data Science, University of Illinois Urbana-Champaign, Urbana, IL, USA. 2Division of Intramural Research, National Library of Medicine, National Institutes of Health, Bethesda, MD, USA. 3Carle Illinois College of Medicine, University of Illinois Urbana-Champaign, Urbana, IL, USA. 4Present address: Keiji.AI Inc, Seattle, USA. e-mail: jimeng@illinois.edu

npj Digital Medicine | (2025) 8:509  1

https://doi.org/10.1038/s41746-025-01840-7 Article

beneﬁts, we developed an accessible web application based on TrialMind and conducted a user study comparing two approaches: AI-assisted experts versus standalone experts. We measured the time savings and evaluated the output quality of each approach. The results show that TrialMind sig- niﬁcantlyreduced the timerequired for studysearch,citationscreening,and data extraction, while maintaining or improving the quality of the output compared to experts working alone.

while aggregating study outcomes via meta-analysis. This design enhances efﬁciency in systematic literature reviews while supporting human-AI col- laboration (Fig. 1 and Methods).

TrialMind can make a comprehensive retrieval of studies from the literature Finding relevant studies from medical literature like PubMed, which con- tains over 35 million entries, can be challenging. Typically, this requires the research expertise to craft complex queries that comprehensively cover pertinent studies. The challenge lies in balancing the speciﬁcity of queries: too stringent, and the search may miss relevant studies; too broad, and it becomes impractical to manually screen the overwhelming number of results. Previous approaches propose to prompt LLMs to generate the searching query directly9, which can induce incomplete searching results duetothelimitedknowledgeofLLMs.Incontrast, TrialMindisdesigned to produce comprehensive queries through a pipeline that includes query generation, augmentation, and reﬁnement. It also provides users with the ability to make further adjustments (Fig. 2b).


## Results

Creating TrialReviewBench from medical literature
In this study, we aim to create a practical benchmark using published
systematic reviews. Given a review paper, the included studies are
extracted as target studies for identiﬁcation and screening, while data
from the study characteristics tables serve as ground truth for data
extraction. This setup ensures evaluation accuracy and alignment with
PRISMA practices. An illustration of this process is in Supplementary
Fig. 1b. Speciﬁcally, we retrieved a list of cancer treatments from the
National Cancer Institute’s introductory page as the keywords to search
medical systematic reviews27. To ensure data quality, we crafted com-
prehensive queries with automatic ﬁltering and manual screening. For
each review, we obtained the list of studies with their PubMed IDs,
retrieved their full content, and extracted study characteristics and
clinical outcomes. We followed PubMed’s usage policy and guidelines
during retrieval. Further manual checks were performed to correct
inaccuracies, eliminate invalid and duplicate papers, and reﬁne the text
for clarity (“Methods”). The ﬁnal TrialReviewBenchdataset consists
of 2220 studies involved in 100 reviews (Fig. 2a), covering four major
therapy topics: Immunotherapy, Radiation/Chemotherapy, Hormone
Therapy, and Hyperthermia. We manually created three major evalua-
tion tasks based on these reviews: study search, study screening, and data
extraction.

The dataset involving clinical studies spanning ten cancer treatment areas was used for evaluation (Fig. 2a). For each review, we collected the involved studies’ PubMed IDs as the ground truth and measured the Recall, i.e., how many ground truth studies are found in the search results. We created two baselines as the comparison: GPT-4 and Human. The GPT-4 baseline makes a prompt for LLMs to generate the boolean queries9. It represents the common way of prompting LLMs for literature search query generation. The Human baseline representsa waywhere the key terms from PICO elements are extracted manually and expanded, referring to UMLS28, to construct the search queries.

Overall, TrialMind achieved a Recall of 0.782 on average for all reviews, meaning it can capture most of the target studies. By contrast, the GPT-4 baseline yielded Recall = 0.073, and the Human baseline yielded Recall = 0.187. We divided the search results across four topics determined by the treatments studied in each review (Fig. 2c). Our analysis showed that TrialMind can identify many more studies than the baselines. For instance, TrialMind achieved Recall = 0.797 with identiﬁed studies N = 22,084 for Immunotherapy-related reviews, while the GPT-4 baseline got Recall = 0.094 (N studies = 27), and the Human baseline got Recall = 0.154 (N studies = 958), respectively. In Radiation/Chemotherapy, TrialMind achieved Recall = 0.780, the GPT-4 baseline got Recall = 0.020, and the Human baseline got Recall = 0.138. In Hormone Therapy, TrialMind achieved Recall = 0.711, the GPT-4 baseline got Recall = 0.067, and the Human baseline got Recall = 0.232. In Hyperthermia, TrialMind achieved Recall = 0.834, the GPT-4 baseline got Recall = 0.106, and the Human baseline got Recall = 0.202. These results demonstrate that regardless of the search task’s complexity, as indicated by the variability in the Human baseline, TrialMind consistently retrieves nearly all target studies from the PubMed database. We have also tested TrialMind in broad therapeutic areas other than oncology. The results can be found in Supplementary Fig. 2.

The study search task begins with the PICO (Population, Intervention, Comparison, Outcome) elements deﬁned by the selected systematic review, which serve as the formal deﬁnition of the research question. The model being tested is tasked with generating keywords for the treatment and condition terms, as depicted in Fig. 2e. These keywords are then used to form Boolean queries, which are submitted to search citations in the PubMed database. The Recall performance of the model is evaluated by checking whether the retrieved studies include those that were actually involved in the systematic review.

For the citation screening task, we mixed the ground truth studies into thesearchresultstocreateacandidatesetof2000citations.Themodelbeing tested ranks these citations based on the likelihood that each citation should be included in the systematic review. To assess the model’s performance, we computeRecall@k:the recallvalueindicatinghow manyofthegroundtruth studies appear in the top k ranked candidates.

The data extraction test set was built based on the study characteristics table from each systematic review, which typically details study character- istics such as study design, population demographics, and outcome mea- surements (Supplementary Fig. 1). We manually extracted the values to create 1334 study characteristic annotations. Additionally, we extract individual study results from the review’s reported analysis, often presented in forest plots, capturing metrics such as overall response and event rates, resulting in 1049 study result annotations. We evaluate model accuracy by manually checking the extracted values against the ground truth values extracted from the systematic reviews for each involved study.

Furthermore, we generated scatter plots of Recall versus the number of target studies for each review (Fig. 2d). The rationale behind this is that a higher number of ground truth studies to identify generally makes the task more challenging, as it becomes more difﬁcult to construct a perfect search query that captures all relevant studies. The results reveal that TrialMind consistently maintained a high Recall, signiﬁcantly outperforming the best baselinesacrossall100reviews.AtrendofdecliningRecallwithanincreasing number of target studies was conﬁrmed through regression analysis. It was found that the GPT-4 baseline struggled, showing Recall close to 0, and the Human baseline results varied, with most reviews below 0.5. As the number of target studies increased, the Human and GPT-4 baselines’ Recall decreased to nearly zero. In contrast, TrialMind demonstrated remark- able resilience, showing minimal variation in performance despite the increasing number of target studies. For instance, in a review involving 141 studies,TrialMindachievedaRecallof0.99,whiletheGPT-4andHuman baselines obtained a Recall of 0.02 and 0, respectively.

Build an LLM-driven system for clinical evidence synthesis We develop TrialMind to seamlessly integrate into the PRISMA work- ﬂow for systematic literature reviews in medicine. According to the PRISMA ﬂowchart, the process consists of three main stages: (1) identiﬁ- cation, (2) screening, and (3) inclusion. As illustrated in Supplementary Fig. 1a, TrialMind aligns with PRISMA by streamlining these stages- generating search terms from PICO elements, applying inclusion and exclusion criteria for eligibility assessment, and extracting target data ﬁelds

npj Digital Medicine | (2025) 8:509  2

https://doi.org/10.1038/s41746-025-01840-7 Article

a

Literature screening

Data extraction

Evidence synthesis

Literature search

• Eligibility criteria  generation • Eligibility prediction • Study relevance ranking

• Clinical outcome  extraction • Clinical evidence  synthesis

• Query generation • Query augmentation

• Information extraction • Links to the sources

Identiﬁed studies

Ranked studies

Study characteristics

Clinical evidence

b

Literature search

Data extraction

1

3

Tables

CAR-T,  Immunotherapy,  T-cell transfer, …

Doc parsing and  extraction

1

Population

Treatment terms

Identiﬁed  studies

Intervention

Texts Figures

×

Lymphoma,  Leukemia,  Multiple  Myeloma, …

Content of the involved studies

Generate  and  augment

Retrieve

Identiﬁed  studies 1 3

Comparison

[     {         "name":"n",          "desc":"Number of samples",         "value":100,         "src": [0, 1]     },     ... ]

Condition terms

Refer to the

Outcome

2 3

source

Overall response,  complete  response, …

Extraction

Check, edit, and add  2

Outcome terms (optional)

Extracted ﬁelds

4 Literature screening

Evidence extraction and synthesis

2

Study #1 Study #2 Study #3

Check,  edit, and  add

• Is a clinical study • Report on safety  outcomes include  neurotoxicity, … • Report on eicacy  outcomes include  overall response, …

Extract the results  of target clinical  endpoints

PICO  elements

1

Eligibility criteria  generation 1

Generate

#Overall Survival #Overall Response

…

#Complete Remission #Objective Response Rate

List of eligibility criteria

…

…

C#1 C#2 C#3

Standardize the  results and make  aggregated analysis

Blood tumor Solid tumor

2

S1

Eligibility prediction 2

Scan and  predict

S2

#Overall Response

#Overall Survival

Identiﬁed  studies

…

Criterion-level eligibility predictions

Studies after

Studies ranked

Studies  identiﬁed  (n = 1000)


## Conclusion: Our study

suggests that CAR-T 
therapy has demonstrated 
eicacy and safety in blood 
cancer …

Study selection &  ranking 3


## Results: 20 studies (1000

patients) were included. 
The pooled overall survival 
and overall response were 
…

ﬁrst-round

at the top

Qualitative analysis  and result  summarization

screening

(n = 20)

Aggregate  criterion- level  predictions

(n = 200)

3

Studies excluded (n = 800) • Not eligible to C#1 • Not eligible to C#2 • …

Fig. 1 | The overview of TrialMind pipeline. a It has four main steps: literature search, literature screening, data extraction, and evidence synthesis. b (1) Utilizing input PICO as the review objective, TrialMind generates search terms to identify studies from literature databases. (2) TrialMind suggests the inclusion and exclusion criteria for users to check and edit. Then, TrialMind scans all the identiﬁed studies and assesses each individual’s eligibility for each criterion. Last, the user decides on the ﬁnal strategy to aggregate the criterion-level assessments into an

overall eligibility score to rank the eligibility of all identiﬁed studies. (3) Given the deﬁned data ﬁeld, TrialMind processes the content of the involved studies and produces the structured outputs for each data ﬁeld, grounded on the source indices for user inspection. (4) TrialMind takes the extracted data to create the stan- dardized trial outcomes and works with users to aggregate all involved trial outcomes with a meta-analysis to create new clinical evidence.

TrialMind enhances citation screening and ranking As in the PRISMA statement for systematic literature review23, researchers needtomanuallycreateasetofinclusionandexclusioncriteria,andthensift through hundreds to thousands of identiﬁed studies to assess individual studies’eligibilitytobeincludedinthereview.TrialMindstreamlinesthis task through a three-step approach: (1) it generates a set of eligibility criteria basedontheresearchquestioninPICOformat;(2) itappliesthesecriteria to evaluate the study’s eligibility, denoted by {−1, 0, 1} where −1 and 1 represent eligible and non-eligible, and 0 represents unknown/uncertain, respectively; and (3) it ranks the studies by aggregating the eligibility pre- dictions (Fig. 3a). We took a summation of the criteria-level eligibility predictions as the study-level relevance prediction scores for ranking.

and the encoded study’s abstracts. We also set a Random baseline that randomly samples from candidates. For each review, we mixed the target studies with the other found studies to build a candidate set of 2,000 studies for ranking. Discriminating the target studies from the other candidates is challenging since all candidates meet the search queries, meaning they most probably investigate the relevant therapies or conditions. We evaluated the ranking performance using the Recall@20 and Recall@50 metrics.

We found that TrialMind greatly improved ranking performances, with the fold changes over the best baselines ranging from 1.3 to 2.6 across four topics (Fig. 3c). For instance, for the Hormone Therapy topic, TrialMind obtained Recall@20 = 0.431 and Recall@50 = 0.674. In the Hyperthermia topic, TrialMind obtained Recall@20 = 0.518 and Recall@50 = 0.710. In the Immunotherapy topic, TrialMind obtained Recall@20 = 0.567 and Recall@50 = 0.713. In the Radiation/Chemotherapy topic, TrialMind obtained Recall@20 = 0.416 and Recall@50 = 0.654. In

We chose MPNet29 and MedCPT30 as the general domain and medical domain ranking baselines, respectively. These methods compute study relevance by the semantic similarity between the encoded PICO elements

npj Digital Medicine | (2025) 8:509  3

https://doi.org/10.1038/s41746-025-01840-7 Article

List of generated terms  subject to add, remove, or edit

a

b

c

Call to expand to more terms Combine the terms to build search queries

d

e

GPT-4 TrialMind

Systematic review

{

{

"Conditions": [     "advanced breast cancer",     "progressive breast cancer",     "HER2- breast cancer",     "hormone receptor-positive breast cancer",     "HER2-negative breast cancer",     "HR-positive breast cancer",     "locally advanced breast cancer",     "stage IV breast cancer",     "metastatic breast cancer",     "relapsed breast cancer"],

"Condition": [     "metastatic breast cancer",     "HR-positive breast cancer",     "HER2-negative breast cancer",     "hormone receptor positive breast cancer",     "visceral metastases",     "metastatic sites",     "treatment-free interval",     "aromatase inhibitor-sensitive",     "AI-sensitive",     "AI-resistant"],

Title: Progression-Free Survival and Overall Survival of CDK 4/6 Inhibitors Plus Endocrine Therapy in Metastatic Breast Cancer: A Systematic Review and Meta-Analysis


## Abstract: The introduction of CDK4/6 inhibitors in

combination with endocrine therapy (ET) represents 
the most relevant advance in the management of
hormone receptor (HR) positive, HER2-negative
metastatic breast cancer over the last few years.

[…]

"Treatments": [     "palbociclib",     "Verzenio",     "Ibrance",     "Kisqali",     "endocrine therapy",     "hormonal therapy",     "abemaciclib",     "ribociclib",     "cyclin-dependent kinase 4/6 inhibitors",     "CDK4/6 inhibitors"], }

"Treatment": [     "CDK4/6 inhibitors",     "endocrine therapy",     "palbociclib",     "ribociclib",     "abemaciclib",     "progression-free survival",     "overall survival",     "objective response rate",     "aromatase inhibitors",     "hormonal therapy"] }

Manual

{

"Condition": ["HR-positive", "HER2-negative", "metastatic breast cancer"],

"Treatment": ["CDK4/6 inhibitors", "endocrine therapy", "hormone therapy", "hormone receptors"], }

70–80% of ground truth studies, whereas other methods miss most of them. d Scatter plots of the Recall against the number of ground truth studies. It is assumed that the more ground truth studies there are, the harder it is to cover all of them via one attempted search query. Each scatter indicates the results of one review. Regression estimates are displayed with the 95% CIs in blue or purple. TrialMind shows a consistent superiority over the other methods while maintaining invariance to the increasing complexity of the searching task. e Example cases comparing the outputs of three methods. The manually crafted terms are usually precise while not diverse enough to cover all the variants in the literature studies. A vanilla GPT-4 approach can introduce terms that are either too broad or irrelevant to the research objective.

Fig. 2 | Literature search experiment results. a The distribution of systematic literature reviews and clinical studies in the evaluation dataset categorized by the primary types of investigated interventions. b The TrialMind interface for lit- erature search allows users to reﬁne search terms efﬁciently. TrialMind suggests an initial set of treatment and condition terms, which users can modify by adding, editing, or removing terms. A sampling button enables users to explore additional terms generated by TrialMind. Once the term set is ﬁnalized, users can click the “Search Studies” button to construct the search query and retrieve relevant studies from the literature. c The recall of search results for reviews across four topics. The left y-axis represents the average recall achieved by different methods, while the right y-axis shows the number of identiﬁed studies. TrialMind successfully captures

npj Digital Medicine | (2025) 8:509  4

https://doi.org/10.1038/s41746-025-01840-7 Article

a b

List of eligibility criteria subject to add, remove, or edit Eligibility prediction: ineligible

Eligibility prediction

Eligibility prediction: eligible

Eligibility prediction: unknown

c

d

Fold Change* Random MedCPT MPNet TrialMind Metric Topic

1.7 0.010 0.229 0.258 0.431 Recall@20 Hormone Therapy

1.5 0.025 0.456 0.460 0.674 Recall@50

1.4 0.010 0.358 0.317 0.518 Recall@20 Hyperthermia

1.3 0.025 0.542 0.463 0.710 Recall@50

2.6 0.010 0.219 0.193 0.567 Recall@20 Immunotherapy

2.1 0.025 0.321 0.336 0.713 Recall@50

1.8 0.010 0.202 0.226 0.416 Recall@20 Radiation/Chemother

apy 1.5 0.025 0.425 0.440 0.654 Recall@50

*TrialMind versus the best baseline (MPNet, MedCPT, or Random) across the row

Fold change compared to random performances Fold change compared to the best baseline 0 >20 5 10 15 0 0.5 1 1.5 2 >2.5

e

TrialMind's performance against the best baseline across that row. c Recall@20 and Recall@50 for TrialMind and selected baselines. d Effect of individual criteria on ranking results. To assess this effect, we remove one criterion at a time from the criteria set, re-rank the results, and measure the change in recall, reﬂecting the criterion’s impact on ranking quality. Most criteria positively inﬂuence the ranking, while a small portion has a negative effect. e Ranking performance for Recall@K with varying K in four topics. Shaded areas are 95% conﬁdence interval.

Fig. 3 | Literature screen experiment results. a Streamline study screening using TrialMind with human in the loop. The left panel shows the list of eligibility criteria suggested by TrialMind and is subject to the user’s edits. The right panel shows the TrialMind assessments for the criterion-level eligibility of all identiﬁed studies. Red, green, and gray ﬁelds indicate the assessment “ineligible”, “eligible”, and “unknown”, respectively. b Ranking performances for Recall@20/50 within across therapeutic areas. The bars on the right show the numbers of the fold

Despitethechallengeof selectingfroma largepoolofcandidates(n=2,000) where candidates were very similar, TrialMind identiﬁed an average of 43% of target studies within the top 50. We compared TrialMind to MedCPT and MPNet for Recall@K (K in 10 to 200) to gain insight into how K inﬂuences the performances (Fig. 3e). We found TrialMind can cap- ture most of the target studies (over 80%) when K = 100.

contrast,otherbaselinesexhibitsigniﬁcantvariabilityacrossdifferenttopics. The general domain baseline MPNetwas the worst as it performed similarly to the Random baseline in Recall@20. MedCPT showed marginal improvement over MPNet in the last three topics, while both failed to captureenoughtargetstudiesinalltopics.WehavealsotestedTrialMind in 16 broad therapeutic areas other than oncology. The results can be found in Supplementary Fig. 2.

To thoroughly assess the quality of these criteria and their impact on ranking performance, we conducted a leave-one-out analysis to calculate ΔRecall@200 for eachcriterion (Fig. 3d). The ΔRecall@200 metric measures the difference in ranking performance with and without a speciﬁc criterion, with a larger value indicating superior criterion quality. Our ﬁndings revealed that most criteria positively inﬂuenced ranking performances, as the negative inﬂuence criteria are n = 1 in Hormone Therapy, n = 1 in

Furthermore, TrialMind demonstrated signiﬁcant improvements over the baselines across various therapeutic areas (Fig. 3b). For example, in “Cancer Vaccines” and “Hormone Therapy,” TrialMind substantially increased Recall@50, achieving 33.33-fold and 10.53-fold improvements, respectively, compared to the best-performing baseline. TrialMind generally attained a fold change greater than 2 (ranging from 1.57 to 33.33).

npj Digital Medicine | (2025) 8:509  5

https://doi.org/10.1038/s41746-025-01840-7 Article

Hyperthermia, n = 5 in Radiation/Chemotherapy, and n = 7 in Immu- notherapy. Additionally, we identiﬁed redundancies among the generated criteria, as those with ΔRecall@200 = 0 were the most frequently observed. This redundancy likely stems from some criteria covering similar eligibility aspects, thus not impacting performance when one is omitted.

specialized pipeline for result extraction (Fig. 4g), where users provide the interested outcome and the cohort deﬁnition. TrialMind offers a trans- parent extraction workﬂow, documenting the sources of results along with the intermediate reasoning and calculations.

We compared TrialMind against two generalist LLM baselines, GPT-4 and Sonnet, which were prompted to extract the target outcomes from the full content of the study documents. Since the baselines can only make text extractions, we manually convert them into numbers suitable for meta-analysis31. This made very strong baselines since they combined LLM extractionwith humanpost-processing.Weassessedtheperformanceusing the Accuracy metric.

TrialMind scales data and result extraction from publications TrialMind streamlines data extraction, such as target therapies, study arm design, and participants’ baseline information from involved studies. Speciﬁcally, TrialMind refers to the ﬁeld names and the descriptions from users and use the full content of the study documents in PDF or XML formats as inputs (Fig. 4a). When the free full content is unavailable, TrialMindacceptstheuser-uploadedcontentastheinput.Wedeveloped an evaluation dataset by converting the study characteristic tables from each review paper into data points. Our dataset comprises 1,334 target data points, including 696 on study design, 353 on population features, and 285 on results. We assessed the data extraction performance using the Accuracy metric.

The evaluation conducted across four topics demonstrated the superiority of TrialMind (Fig. 4d). Speciﬁcally, in Immunotherapy, TrialMind achieved an accuracy of ACC = 0.70 (95% CI 0.62–0.77), while GPT-4 scored ACC = 0.54 (95% CI 0.45–0.62). In Radiation/Che- motherapy, TrialMind reached ACC = 0.65 (95% CI 0.51–0.76), com- pared to GPT-4’s ACC = 0.52 (95% CI 0.39–0.65). For Hormone Therapy, TrialMind achieved ACC = 0.80 (95% CI 0.58–0.92), outperforming GPT-4, which scored ACC = 0.50 (95% CI 0.30–0.70). In Hyperthermia, TrialMind obtained an accuracy of ACC = 0.84 (95% CI 0.71–0.92), signiﬁcantly higher than GPT-4’s ACC = 0.52 (95% CI 0.39–0.65). The breakdowns of evaluation results by the most frequent types of clinical outcomes (Fig. 4e) showed TrialMind got fold changes in accuracy ranging from 1.05 to 2.83 and a median of 1.50 over the best baselines. This enhanced effectiveness is largely attributable to TrialMind’s ability to accurately identify the correct data locations and apply logical reasoning, while the baselines often produced erroneous initial extractions.

TrialMind demonstrated strong extraction performance across various topics (Fig. 4b): it achieved an accuracy of ACC = 0.78 (95% con- ﬁdence interval (CI) = 0.75–0.81) in the Immunotherapy topic, ACC = 0.77 (95% CI = 0.72–0.82) in the Radiation/Chemotherapy topic, ACC = 0.72 (95% CI = 0.63–0.80) in the Hormone Therapy topic, and ACC = 0.83 (95% CI = 0.74–0.90) in the Hyperthermia topic. These results indicate that TrialMind can provide a solid initial data extraction, which human experts can reﬁne. Importantly, each output can be cross-checked by the linked original sources, facilitating veriﬁcation and further investigation.

Diving deeper into the accuracy across different types of ﬁelds, we observed varying performance levels. It performed best in extracting study design information, followed by population details, and showed the lowest accuracy in extracting results (Fig. 4b). For example, in the Immunotherapy topic, TrialMind achieved an accuracy of ACC = 0.95 (95% CI = 0.92–0.96) for study design, ACC = 0.74 (95% CI = 0.67–0.80) for popu- lation data, and ACC = 0.42 (95% CI = 0.36–0.49) for results. This variance can be attributed to the prevalence of numerical data in the ﬁelds: ﬁelds with more numerical data are typically harder to extract accurately. Study design is mostly described in textual format and is directly presented in the documents, whereas population and results often include numerical data such as the number of patients or gender ratios. Results extraction is par- ticularly challenging, often requiring reasoning and transformation to capture values accurately. Given these complexities, it is advisable to scru- tinize the extracted numerical data more carefully.

We analyzed the error cases in our result extraction experiments and identiﬁed four primary error types (Fig. 4f). The most common error was ‘Inaccurate’ extraction (n=36), followed by ‘Extraction failure’ (n = 27), “Unavailable data” (n = 10), and ‘Hallucinations’ (n = 3). ‘Inaccurate’ extractions often occurred due to multiple sections ambiguously describing thesameﬁeld.Forexample,aclinicalstudymightreportthetotalnumberof participants receiving CAR-T therapy early in the document and later provide outcomes for a subset with non-small cell lung cancer (NSCLC). The speciﬁc results for NSCLC patients are crucial for reviews focused on this subgroup, yet the presence of general data can lead to confusion and inaccuracies in extraction. ‘Extraction failure’ and ‘Unavailable data’ both illustrate scenarios where TrialMind could not retrieve the information. The latter case particularly showcases TrialMind’s robustness against hallucinations, as it failed to extract data outside the study’s main content, such as in appendices, which were not included in the inputs. Furthermore, errors caused by hallucinations were minor. The outputs were easy to identify and correct through manual inspection since no references were provided.

We also evaluated the robustness of TrialMind against halluci- nations and missing information (Fig. 4c). We constructed a confusion matrix detailing instances of hallucinations: false positives (FP) where TrialMind generated data not present in the input document, and false negatives (FN) where it failed to extract available target ﬁeld information. We observed that TrialMind achieved a precision of Precision = 0.994 for study design, Precision = 0.966 for population, and Precision = 0.862 for study results. Missing information was slightly more common than hallucinations, with TrialMind achieving recall rates of Recall = 0.946 for study design, Recall = 0.889 for population, and Recall = 0.930 for study results. The incidence of both hallucinations and missing information was generally low. However, hallucinations were notably more frequent in study results; this often occurred because LLMs could confuse deﬁnitions of clinical outcomes, for example, mistaking ‘overall response’ for ‘complete response.’ Nevertheless, such hallucina- tions are typically manageable, as human experts can identify and correct them while reviewing the referenced material.

TrialMind facilitates clinical evidence synthesis via human-AI collaboration Weselectedﬁvesystematicreviewstudiesasbenchmarksandreferencedthe clinical evidence reported in the target studies. The baseline used GPT-4 with a simple prompting to extract the relevant text pieces that report the targetoutcomeofinterest(Methods).Manualcalculationswerenecessaryto standardizethedataformeta-analysis.Incontrast,TrialMindautomated the extraction and standardization (Fig. 5a by (1) extracting the raw result description from the input document and (2) standardizing the results by generating a Python program to assist the calculation. The standardized results from all involved studies are then fed into the R program by human experts to make the aggregated evidence in a forest plot.

We engaged with eight annotators (ﬁve medical doctors and three computer scientists) to assess the quality of synthesized clinical evidence presented in forest plots. Each annotator was asked to evaluate the evidence quality by comparing it against the evidence reported in the target review and deciding which method, TrialMind or the baseline, produced superior results (Supplementary Fig. 3). Additionally, they rated the quality ofthesynthesizedclinicalevidenceonascaleof1to5.Theassignmentofour

The challenges in extracting study results primarily stem from (1) identifying the locations that describe the desired outcomes from lengthy papers, (2) accurately extracting relevant numerical values such as patient numbers, event counts, durations, and ratios from the appropriate patient groups, and (3) performing the correct calculations to standardize these values for meta-analysis. In response to these complexities, we developed a

npj Digital Medicine | (2025) 8:509  6

https://doi.org/10.1038/s41746-025-01840-7 Article

81.2%, respectively. The baseline’s primary shortcoming stemmed from the initial extraction step, where GPT-4 often failed to identify the relevant sources without well-crafted prompting. Therefore, the subsequent manual post-processing was unable to rectify these initial errors.

method and the baseline was randomized to ensure objectivity. The results highlighted TrialMind’s superior performance compared to the direct use of GPT-4 for clinical evidence synthesis (Fig. 5b). We calculated the winning rate of TrialMind versus the baseline across the ﬁve studies. The results indicate a consistent preference by annotators for the evidence synthesized by TrialMind over that of the baseline. Speciﬁcally, TrialMind achieved winning rates of 87.5%, 100%, 62.5%, 62.5%, and

In addition, we illustrated the ratings of TrialMind and the baseline across studies (Fig. 5c).We foundTrialMind was competent as the GPT- 4+Human baseline and outperformed the baseline in many scenarios. For

npj Digital Medicine | (2025) 8:509  7

https://doi.org/10.1038/s41746-025-01840-7 Article

e Comparison of trial result extraction accuracy between TrialMind and baselines across the most frequent clinical endpoint types. f, Error analysis of result extraction: Inaccurate—incorrect data extraction; Extraction Failure—TrialMind failed to extract data and returned null; Unavailable Data - target data was absent in the input document, resulting in null output; Hallucination—TrialMind generated data that did not exist in the input document. g In TrialMind's result extraction step, users can deﬁne the target clinical endpoint and cohort based on conditions and treatments. Clicking the extraction button triggers the extraction process for all selected studies, with results exportable in tabular format for further analysis.

Fig. 4 | Data extraction experiment results. a In the TrialMind platform, users can deﬁne the name and description of target data ﬁelds and create a structured list. Upon clicking the “Extraction” button, TrialMind processes the selected studies and populates the study table with new columns representing the speciﬁed ﬁelds. Users can also click on extracted values to view the source text referenced by TrialMind. b Accuracy of data extraction across four therapy topics, with results further stratiﬁed by data type. c Confusion matrix illustrating hallucination and missing rates in data extraction across three data types. d Comparison of trial result extraction accuracy between TrialMind and baseline methods across four topics.

example,TrialMindobtained themeanratingof4.25(95%CI3.93–4.57) inStudy#1whilethebaselineobtained3.50(95%CI3.13–3.87).InStudy#2, TrialMind yielded 3.50 (95% CI 3.13–3.87) while the baseline yielded 1.25 (95% CI 0.93–1.57). The performance of the two methods was com- parable in the remaining three studies. These results highlight TrialMind as a highly effective approach for streamlining data extraction and proces- sing while maintaining the critical beneﬁt of human oversight.

main content, which can sometimes make it challenging for human readers to locate the correct information.


## Discussion

Clinical evidence forms the bedrock of evidence-based medicine, crucial for
enhancing healthcare decisions and guiding the discovery and development
of new therapies. It often comes from a systematic review of diverse studies
found in the literature, encompassing clinical trials and retrospective ana-
lyses of real-world data. Yet, the burgeoning expansion of literature data-
basespresentsformidablechallengesinefﬁcientlyidentifying,summarizing,
and maintaining the currency of this evidence. For instance, a study by the
US Agency for Healthcare Research and Quality (AHRQ) found that half of
17 clinical guidelines became outdated within a couple of years32.
The rapid development of large language models (LLMs) and AI
technologies has generated considerable interest in their potential applica-
tions in clinical research33,34. However, most of them focused on an indivi-
dual aspect of the clinical evidence synthesis process, such as literature
search35,36,citationscreening37–39,qualityassessment40,ordataextraction41,42.
In addition, implementing these models in a manner that is collaborative,
transparent, and trustworthy poses signiﬁcant challenges, especially in cri-
tical areas such as medicine43. For instance, when utilizing LLMs to sum-
marize evidence from multiple studies, the descriptive summaries often
usually merely echo the ﬁndings verbatim, omit crucial details, and fail to
adhere to established best practices18. Besides, when given a set of studies
that are irrelevant to the research question, LLMs are prone to produce
hallucinations and hence cause misleading evidence44. This challenge
highlights the need for an integrated pipeline that is aligned with standard
practice, such as PRISMA for systematic literature reviews to strategically
pick the target studies for analysis45,46, or enhanced with human-AI
collaboration47.

We requested that annotators self-assess their expertise level in clinical studies, classifying themselves into three categories: “Basic”, “Familiar”, and “Advanced”. The typical proﬁle ranges from computer scientists at the basic level to medical doctors at the advanced level. We then analyzed the ratings given to both methods across these varying expertise levels (Fig. 5d). We consistently observed higher ratings for TrialMind than the baseline across all groups. Annotators with basic knowledge tended to provide more conservative ratings, while those with more advanced expertise offered a widerrange of evaluations. Forinstance, the “Basic”group provided average ratings of 3.67 (95% CI 3.34–3.39) for TrialMind compared to 3.22 (95% CI2.79–3.66) forthe baseline. The “Advanced”group ratedTrialMind at an average of 3.40 (95% CI 3.16–3.64) and the baseline at 3.07 (95% CI 2.75–3.39). We conducted user studies to compare the quality and time efﬁciency between purely manual efforts and human-AI collaboration using TrialMind. Two participants were involved in both study screening and data extraction tasks. For the screening task, each participant was assigned 4 systematic review papers, with 100 candidate citations identiﬁed for each review. The participants were asked to select the 10 most likely relevant citations from the candidate pool. Each participant was provided with 2 candidate sets pre-ranked by TrialMind and 2 unranked sets. The par- ticipants also recorded the time taken to complete the screening process for each set. For the data extraction task, each participant was given 10 clinical studies. They manually extracted the target information for 5 of these stu- dies. For the other 5, TrialMind was ﬁrst used to perform an initial extraction, and the participants were required to verify and correct the extracted results. The time taken for the extraction process was reported for each study.

This study introduces a clinical evidence synthesis pipeline enhanced by LLMs, named TrialMind. This pipeline is structured in accordance with established medical systematic review protocols such as PRISMA, involving steps such as study searching, screening, data/result extraction, and evidence synthesis. At each stage, human experts have the capability to access, monitor, and modify intermediate outputs. This human oversight helps to eliminate errors and prevents their propagation through sub- sequent stages. Unlike approaches that solely depend on the knowledge of LLMs, TrialMind integrates human expertise through in-context learning and chain-of-thought prompting. Additionally, TrialMind extends external knowledge sources to its outputs through retrieval- augmented generation and leveraging external computational tools to enhance the LLM’s reasoning and analytical capabilities. Comparative evaluations of TrialMind and traditional LLM approaches have demonstrated the advantages of this system design in LLM-driven appli- cations within the medical ﬁeld.

In Fig. 5e, we present the average performance and time cost for the AI +HumanandHuman-onlyapproachesacrossboththestudyscreeningand data extraction tasks. The results demonstrate that the AI+Human approach consistently outperforms the Human-only approach. For the screening tasks, AI+Human achieved a 71.4% relative improvement in Recall while reducing time by 44.2% compared to the Human-only arm. This underscores the signiﬁcant advantage of TrialMind in accelerating the study screening process while also improving its quality. Similarly, for the data extraction tasks, the AI + Human approach improved extraction accuracy by 23.5% on average, with a 63.4% reduction in time required.

Detailed results of screening time and performance are shown in Fig. 5f, where two reviewsshowedthe AI+Human approach achievingthe same Recall as the Human-only arm with notable time savings, and in two other reviews, AI + Human achieved higher Recall with less time. From Fig. 5g, we see that the AI+Human approach delivered better or comparable accuracy across all three types of data, with the smallest gap in “Study design”. This is likely because study design information is often readily available in the study abstract, making it relatively easier for humans to extract.Incontrast,theothertwodatatypesareembeddeddeeperwithinthe

This study also has several limitations. First, despite incorporating multiple techniques, LLMs may still make errors at any stage. Therefore, human oversight and veriﬁcation remain crucial when implementing TrialMind in practical settings. Second, while TrialMind demon- strated effectiveness in study search, screening, and data extraction, the dataset used was limited in size due to the high costs associated with human labeling. Speciﬁcally, TrialMind was evaluated on clinical trials and observational studies primarily in oncology and focused on therapeutic

npj Digital Medicine | (2025) 8:509  8

https://doi.org/10.1038/s41746-025-01840-7 Article

a

Result extraction Result standardization Scale to all involved studies

{   "Group": "Patients with  refractory or relapsed  hematologic or solid  malignancies treated by  CAR-T therapy",   "N": 9,   "Complete Response  Rate": 0.22 }

{   "Group": "Patients with  refractory or relapsed  hematologic or solid  malignancies treated by  CAR-T therapy",   "N": 9,   "Results": "6/9 patients  showed objective clinical  response; 2/9 achieved  complete response" }

Aggregated evidence  in forest plot Clinical studies

Generate Python program  to do the calculation

b c d

e

f

Recall@10 Time spent (seconds)

P1* P2* ΔRecall P1* P2* Time saving (%)

Review1 1.000 0.000 1.00 258 594 56.6%

Review2 0.600 0.600 0.00 1299 423 67.4%

71.4% 44.2%

Review3 0.429 0.429 0.00 619 635 2.5%

Review4 0.667 0.833 0.17 731 519 29.0%

*P1,P2: short for participant 1 and 2

AI+Human Human

g

23.5%

63.4%

Fig. 5 | Results of human evaluation and user study. a TrialMind's systematic result extraction pipeline. The process begins with an input study document, from which TrialMind generates a focused summary of the target group’s main results. It then systematically extracts key numerical data and performs programmatic calculations to standardize the results. b A comparative evaluation where eight expert annotators assessed the quality of meta-analysis results between Trial- Mind and a baseline consisting of GPT-4 extraction with human post-processing. The analysis presents TrialMind's winning rate relative to the baseline across ﬁve selected systematic reviews. c Violin plots illustrating annotator ratings distribution for meta-analysis results, comparing TrialMind against the GPT-4 baseline across ﬁve systematic reviews. Each plot displays the mean ratings with 95% con- ﬁdence intervals derived from all annotator assessments. d, Violin plots showing

rating distributions stratiﬁed by annotators' self-reported expertise levels. Each plot indicates the mean ratings with 95% conﬁdence intervals aggregated across all evaluated studies. e Comparative analysis of two experimental arms: Human (manual effort) versus AI+Human (TrialMind-assisted). The upper panel pre- sents the overall Recall achieved by two human participants when screening 100 identiﬁed studies, alongside time duration. The lower panel displays the overall Accuracy achieved in data extraction tasks, with corresponding time measurements for both arms. f Detailed breakdown of screening performance metrics across dif- ferent systematic reviews and participants, comparing AI+Human and Human arms. g Comprehensive comparison of data extraction accuracy between AI +Human and Human arms, analyzed across different participants and data types.

relevant studies are either not available on PubMed or are in formats that entail OCR algorithms as preprocessing, indicating a need for further engineering to incorporate broader data sources. Fourth, although TrialMind illustrated the potential of using advanced LLMs like GPT-4

outcomes, its generalizability to broader domains, such as preventive interventions, diagnostics, or non-oncology topics, remains to be estab- lished. Third, the study coverage was restricted to publicly available sources from PubMed Central, which provides structured PDFs and XMLs. Many

npj Digital Medicine | (2025) 8:509  9

https://doi.org/10.1038/s41746-025-01840-7 Article

organized these papers by their citation count to gauge their impact and relevanceintheﬁeld.Ourselectioncriteriaaimedtoenhancethequalityand relevance of our ﬁnal dataset. We prioritized papers that focused on the study of treatment effects, such as safety and efﬁcacy, of various cancer interventions. We preferred studies that compared individual treatments against a control group, as opposed to those examining the effects of combined therapies (e.g., Therapy A + B vs. A only). To build a list of representative meta-analyses, we needed to ensure diversity in the target conditions under each treatment category.

to streamline clinical evidence synthesis, it is not yet an end-to-end solution for all steps in systematic literature reviews. Future development for several othersteps,suchasstudyqualityassessmentandreportdrafting,canfurther increase its value. Last, while the use of LLMs like GPT-4 can accelerate study screening and data extraction, the associated costs and processing times maypresentbottlenecksin somescenarios.Future enhancementsthat improve efﬁciency or utilize localized, specialized models could increase practical utility.

LLMs have made signiﬁcant strides in AI applications. TrialMind exempliﬁes a crucial aspect of system engineering in LLM-driven pipelines, facilitating the practical, robust, and transparent use of LLMs. We anticipate that TrialMind will beneﬁt the medical AI community by fostering the development of LLM-driven medical applications and emphasizing the importance of human-AI collaboration.

Further, we favored studiesthat involved a largernumber of individual studies, providing a broader base of evidence. However, we excluded net- work analysis studies and meta-analyses that focused solely on prognostic and predictive effects, as they did not align with our primary research focus. To maintain a balanced representation, we limited our selection to a max- imum of three papers per treatment category. This process culminated in a ﬁnal dataset comprising 100 systematic review papers.


## Methods

Description of the TrialReviewBench dataset
We present the overall ﬂow in building the TrialReviewBenchdata in
Supplementary Fig. 4.

Prompt engineering Prompting steers LLMs to conduct the target task without training the underlying LLMs. TrialMind proceeds clinical evidence synthesis in multiple steps associated with a series of prompting techniques.

Fordatabasesearchandinitialﬁltering,weundertookacomprehensive search on the PubMed database for meta-analysis papers related to cancer. The Boolean search terms were speciﬁcally chosen to encompass a broad spectrum of cancer-related topics. These terms included “cancer”, “oncol- ogy”, “neoplasm”, “carcinoma”, “melanoma”, “leukemia”, “lymphoma”, and “sarcoma”. Additionally, we incorporated terms related to various treatment modalities such as “therapy”, “treatment”, “chemotherapy”, “radiation therapy”, “immunotherapy”, “targeted therapy”, “surgical treat- ment”, and “hormone therapy”. To ensure that our search was exhaustive yet precise, we also included terms like “meta-analysis” and “systematic review” in our search criteria.

The fundamental concept of in-context learning (ICL) is to enable LLMs to learn from examples and task instructions within a given context at inference time8. Formally, for a speciﬁc task, we deﬁne T as the task prompt, which includes the task deﬁnition, input format, and desired output format. During a single inference session with input X, the LLM is prompted with P(T, X), where P( ⋅) is a transformation function that restructures the task deﬁnition T and input X into the prompt format. The output ^X is then generated as ^X ¼ LLM ðPðT; XÞÞ.

LLMs can produce hallucinations without high-quality evidence in their context. This issue can be mitigated through retrieval-augmented generation (RAG), which enhances LLMs by dynamically incorporating external knowledge into their prompts duringgeneration48. We denote RK( ⋅ ) as the retriever that utilizes the input X to source relevant contextual information through semantic search. RK( ⋅) enables the dynamic infusion of tailored knowledge into LLMs at inference time.

This initial search yielded an extensive pool of 46,192 results, reﬂecting the vast research conducted in these areas. We applied speciﬁc ﬁlters to reﬁne these results and ensure relevance and quality. We focused on articles wherePMCFulltextwasavailableandspeciﬁcallycategorizedunder“Meta- Analysis”. Further reﬁnement was done by restricting the time frame of publications to those betweenJanuary 1, 2020, and January 1, 2023. We also narrowed our focus to studies conducted on humans and those available in English. This ﬁltration process leads to an initial collection of 2691 reviews.

Chain-of-though (CoT) guides LLMs in solving a target task in a step- by-step manner in one inference, hence handling complex or ambiguous tasks better and inducing more accurate outputs49. CoT employs the func- tion PCoT( ⋅) to structure the task T into a series of chain-of-thought steps {S1, S2, …, ST}. As a result, we obtain f^X

Building upon our initial search, we employed further reﬁnement techniquesusingbothMeSHtermsandspeciﬁckeywords.TheMeSHterms were carefully selected to target papers precisely relevant to various forms of cancer.These termsincluded“cancer”,“tumor”,“neoplasms”, “carcinoma”, “myeloma”, and “leukemia”. This focused approach using MeSH terms effectively reduced our selection to 1967 reviews.

T S g ¼ LLMðPCoTðT; XÞÞ, all produced in a single inference session. This is rather critical when we aim to elicit the thinking process of LLM and urge it in self-reﬂection to improve its response. For instance, we may ask LLM to draft the initial response in the ﬁrst step and reﬁne it in the second.

1 S; .. . ; ^X

To further dive in on papers investigating cancer therapies, we utilized many keywords derived from the National Cancer Institute’s “Types of Cancer Treatment” list. This approach was multi-faceted, with each set of keywords targeting a speciﬁc category of cancer therapy. For chemotherapy, we included terms like “chemotherapy”, “chemo”, and related variations. In the realm of hormone therapy, we searched for phrases such as “hormone therapy”, “hormonal therapy”, and similar terms. The keyword group for hyperthermia encompassed terms like “hyperthermia”, “microwave”, “radiofrequency”, and related technologies. For cancer vaccines, we inclu- ded keywords such as “cancer vaccines”, “cancer vaccine”, and other related terms. The search for immune checkpoint inhibitors and immune system modulators was comprehensive, including terms like “immune checkpoint inhibitors”, “immunomodulators”, and various cytokines and growth fac- tors. Lastly, our search for monoclonal antibodies and T-cell transfer therapy included relevant terms like “monoclonal antibodies”, “T-cell therapy”, “CAR-T”, and other related phrases. This keyword ﬁltering leads to a pool of 352 reviews.

Clinical evidence synthesis involves a multi-step workﬂow as outlined in the PRISMA statement23. It can be generally outlined as identifying and screening studies from databases, extracting characteristics and results from individual studies, and synthesizing the evidence. To enhance each step’s performance, task-speciﬁc prompts can be designed for an LLM to create an LLM-based module. This results in a chain of prompts that effectively addresses a complex problem, which we call LLM-driven workﬂow. Spe- ciﬁcally, this approach breaks down the entire meta-analysis process into a sequence of N tasks, denoted as T ¼ fT1; .. . ; TNg. In the workﬂow, the output from one task, ^Xn, serves as the input for the next, ^Xnþ1 ¼ LLM ðPðTn; ^XnÞÞ. This modular decomposition improves LLM performance by dividing the workﬂow into more manageable segments, increases transparency, and facilitates user interaction at various stages.

Incorporating these techniques, the formulation of TrialMind for any subtask can be represented as:

^Xnþ1 ¼ LLM ðPðTn; XnÞ; RKðXnÞÞ; 8n ¼ 1; .. . ; N; ð1Þ

Then, we manually screened titles and abstracts, applying a rigorous classiﬁcation and sorting methodology. The remaining papers were ﬁrst categorized based on the type of cancer treatment they explored. We then

where RK( ⋅) are optional.

npj Digital Medicine | (2025) 8:509  10

https://doi.org/10.1038/s41746-025-01840-7 Article

Based on ^XEC, TrialMind embarks the parallel processing for the candidate studies. For i-th studyFi, the eligibility prediction is made by LLM as (Prompt in Supplementary Fig. 9)

Implementation of TrialMind: study search All experiments were run in Python v.3.9. Detailed software versions are: pandasv2.2.2;numpyv1.26.4;scipyv1.13.0;scikit-learnv1.4.1.post1;openai v1.23.6; langchain v0.1.16; boto3 v1.34.94; pypdf v4.2.0; lxml v5.2.1 and chromadb v0.5.0 with Python v.3.9.

i g ¼ LLMðPðFi; X; TSC; ^XECÞÞ; ð4Þ

i ; . .. ; IM

fI1

We included GPT-4 and Sonnet in our experiments. GPT-450 is regarded as a state-of-the-art LLM and has demonstrated strong perfor- mance in many natural language processing tasks (version: gpt-4-0125- preview). Sonnet51 is an LLM developed by Anthropic, representing a more lightweight but also very capable LLM (version: anthropic.claude-3-sonnet- 20240229-v1:0 on AWS Bedrock). Both models support long context lengths (128K and 200K), enabling them to process the full content of a typical PubMed paper in a single inference session.

where TSC is the task deﬁnition of study screening; Fi is the study i’s content; Im

i 2 f1; 0; 1g; 8m ¼ 1; . .. ; M is the prediction of study i’s eligibility to the m-th criterion. Here, −1 and 1 mean ineligible and eligible, 0 means uncertain,respectively.Thesepredictionsoffera convenientwayforusersto inspect the eligibility and select the target studies by altering the aggregation strategies. Im

i can be aggregated to offer an overall relevance of each study, such as ^Ii ¼ P

mIm

i . Users are also encouraged to extend the criteria set or block the predictions of some criteria to make customized rankings during the screening phase.

TrialMind processes research question inputs using the PICO (Population, Intervention, Comparison, Outcome) framework to deﬁne the study’s research question. In our experiments, the title of the target review paper served as the general description. Subsequently, we extracted the PICO elements from the paper’s abstract to detail the speciﬁc aspects of the research question.

Implementation of TrialMind: data extraction Study data extraction is an open information extraction task that requires the model to extract speciﬁc information based on user inputs and handle long inputs, such as the full content of a paper. LLMs are particularly well- suited for this task because (1) they can be prompted for information extraction out of the box, and (2) they can take the whole publication content as input.

TrialMind is tailored to adhere to the established guidelines23 in conducting literature searches and screening for clinical evidence synthesis. In the literature search stage, the key is formulating Boolean queries to retrieve a comprehensive set of candidate studies from databases. These queries, in general, are a combination of treatment and condition terms. However, direct prompting can yield low recall queries due to the narrow range of user inputs and the LLMs’ tendency to produce incorrect queries, such as generating erroneous MeSH (Medical Subject Headings) terms9. To address these limitations, TrialMind incorporates RAG to enrich the context with knowledge sourced from PubMed and employs CoT processing to facilitate a more exhaustive generation of relevant terms.

For the speciﬁed data ﬁelds to be extracted, TrialMind prompts LLMs to locate and extract the relevant information (Prompt in Supple- mentary Fig. 10). These data ﬁelds include (1) study characteristics such as study design, sample size, study type, and treatment arms; (2) population baselines; and (3) study ﬁndings. In general, the extraction process can be described as

K EXg ¼ LLMðPðF; C; TEXÞÞ; ð5Þ

1 EX; . .. ; ^X

f^X

Speciﬁcally, the study search component has two main steps: initial query generation and then query reﬁnement. In the ﬁrst step, TrialMind prompts LLM to create the initial boolean queries derived from the input PICO to retrieve a group of studies (Prompt in Supplementary Fig. 6). The abstracts of these studies then enrich the context for reﬁning the initial queries, working as RAG. In addition, we used CoT to enhance the reﬁnement by urging LLMs to conduct multi-step reasoning for self- reﬂection enhancement (Prompt in Supplementary Fig. 7). This process can be described as

where F represents the full content of a study; TEX deﬁnes the task of data extraction; and C = {C1, C2, …, CK} comprises the series of data ﬁelds targeted for extraction. Ck is the user input natural language description of the target ﬁeld, e.g., “the number of participants in the study". The input content F is segmented into distinct chunks, each marked by a unique identiﬁer. The outputs, denoted as ^X

k

EX ¼ fVk; Bkg, include the extracted values V and the indices B that link back to their respective locations in the source content. Hence, it is convenient to check and correct mistakes made in the extraction by sourcing the origin. The extraction can also be easily scaled by making paralleled calls of LLMs.

1 S; ^X

2 S; ^X

3 Sg ¼ LLMðPCoTðTLS; X; RKðXÞÞÞ; ð2Þ

f^X

where X denotes the input PICO; RK(X) is the set of abstracts of the found studies;TLSisthedeﬁnitionofthequerygenerationtaskforliteraturesearch.

Implementation of TrialMind: result extraction Our analysis indicates that data extraction generally performs well for study design and population-related ﬁelds; however, extracting study results presentschallenges.Errorsfrequentlyariseduetothediversepresentationof resultswithinstudiesandsubtlediscrepanciesbetweenthetargetpopulation and outcomes versus those reported. For instance, the target outcome is the risk ratios (treatment versus control) regarding the incidence of adverse events (AEs), while the study reports AEs among many groups separately. Or, the target outcome is the incidence of severe AEs, which implicitly corresponds to those with grade III and more, while the study reports all grade AEs. To overcome these challenges, we have reﬁned our data extraction process to create a specialized result extraction pipeline that improves clinical evidence synthesis. This enhanced pipeline consists of three crucial steps: (1) identifying the relevant content within the study (Prompt in Supplementary Fig. 11), (2) extracting and logically processing this content to obtain numerical values (Prompt in Supplementary Fig. 12), and (3) converting these values into a standardized tabular format (Prompt in Supplementary Fig. 13).

1 S indicates a complete set of terms

For the output, the ﬁrst sub-step ^X

2 S indicates the subset of ^X

1 S by

identiﬁed in the found studies; the second ^X

2 S by self-reﬂection and adding more augmentations. In this process, LLM will produce the outputs for all three substeps in one pass, and TrialMind

3 S indicates the extension of ^X

ﬁltering out the irrelevant; and the third ^X

3 S as the ﬁnal queries to fetch the candidate studies.

takes ^X

Implementation of TrialMind: study screening TrialMind follows PRISMA to take a transparent approach to study screening. It creates a set of eligibility criteria based on the input PICOas the basis for study selection (Prompt in Supplementary Fig. 8), produced by

^XEC ¼ LLMðPðTEC; XÞÞ; ð3Þ

where ^XEC ¼ fE1; E2; . .. ; EMgistheMgeneratedeligibilitycriteria;Xisthe input PICO; and TEC is the task deﬁnition of criteria generation. Users are giventheopportunitytomodifythesegeneratedcriteria,furtheradjustingto their needs.

Steps (1) and (2) are conducted in one pass using CoT reasoning as

1 RE ;S; ^X

2 RE ;Sg ¼ LLMðPCoTðX; O; F; TREÞÞ; ð6Þ

f^X

npj Digital Medicine | (2025) 8:509  11

https://doi.org/10.1038/s41746-025-01840-7 Article

standardized result values. This is for both TrialMind and the baselines. Nonetheless, for the baseline, the annotators also need to manually extract the result values and standardize the values to make them ready for meta- analysis, which forms the GPT-4+Human baseline in the experiments.

where O is the natural language description of the clinical endpoint of interest, and TRE is the task deﬁnition of result extraction. In the outputs,

1 RE ;S represents the raw content captured from the input content F regarding the clinical outcomes; ^X

^X

2 RE ;S represents the elicited numerical valuesfromtherawcontent,suchasthenumberofpatientsinthegroup,the ratioofpatientsencounteringoverallresponse,etc.Instep(3),TrialMind writes Python code to make the ﬁnal calculation to convert ^X

We engaged two groups of annotators for our evaluation: (1) three computer scientists with expertise in AI applications for medicine, and (2) ﬁve medical doctors to assess the generated forest plots. Each annotator was asked to evaluate ﬁve review studies. For each review, we randomly pre- sented forest plots generated by both the baseline and TrialMind. The annotators were required to determine how closely each generated plot aligned with a reference forest plot taken from the target review paper. Additionally, they were asked to judge which method, the baseline or TrialMind, produced better results in a win/lose assessment. Supple- mentary Fig. 3 demonstrates the user interface for this study, which was created with Google Forms.

2 RE ;S to the standard tabular format.

2 RE ;SÞÞ; ^X

2 RE ;SÞ: ð7Þ

^XRE ¼ execð LLMðPðX; O; TPY; ^X

In this process, TrialMind adheres to the instructions in TPY to generate code fordata processing.Thiscode isthenexecuted,using ^X

2 RE ;S as input, to produce the standardized result ^XRE. An example code snippet made to do this transformation is shown in Supplementary Fig. 5. This approach facilitates veriﬁcation of the extracted results by allowing for easy back- tracking to ^X

1 RE ;S. Additionally, it ensures that the calculation process remains transparent, enhancing the reliability and reproducibility of the synthesized evidence.

Data availability The TrialReviewBench dataset for study search, citation screening, and data extractiontaskscanbeaccessedathttps://huggingface.co/datasets/zifeng-ai/ TrialReviewBench.

Experimental setup In study search experiments, we assessed performance using the overall Recall, aiming to evaluate the effectiveness of different methods in identi- fying all relevant studies from the PubMed database using APIs52. For citation screening, we measured the performance using Recall@20 and Recall@50,whichgaugehowwellthemethodscanprioritizetargetstudiesat the top of the list, thereby facilitating quicker decisions about which studies to include in evidence synthesis. We constructed the ranking candidate set for each review paper by initially retrieving studies through TrialMind, then reﬁning this list by ranking the relevance of these studies to the target review’s PICO elements using OpenAI embeddings. The top 2000 relevant studies were kept. We then ensured all target papers were included in the candidate set to maintain the integrity of our ground truth data. The ﬁnal candidate set was then deduplicated to be ranked by the selected methods.

Code availability TrialMind can be accessed at https://github.com/RyanWangZf/ TrialMind-SLR, including the source code for implementing Trial- Mind’s study search, study screening, data extraction, and result extraction components. The interactive web-based demo of TrialMind is hosted at https://www.trialmindapis. com/api/systematic-literature-review. Access is available upon request by contacting the corresponding author.

Received: 31 October 2024; Accepted: 24 June 2025;


## References

1.
Elliott, J. et al. Decision makers need constantly updated evidence
synthesis. Nature 600, 383–385 (2021).
2.
Field, A. P. & Gillett, R. How to do a meta-analysis. Br. J. Math. Stat.
Psychol. 63, 665–694 (2010).
3.
Concato, J., Shah, N. & Horwitz, R. I. Randomized, controlled trials,
observational studies, and the hierarchy of research designs. In
Research Ethics, 207–212 (Routledge, 2017).
4.
Borah, R., Brown, A. W., Capers, P. L. & Kaiser, K. A. Analysis of the
time and workers needed to conduct systematic reviews of medical
interventions using data from the Prospero registry. BMJ Open 7,
e012545 (2017).
5.
Hoffmeyer, B. D., Andersen, M. Z., Fonnes, S. & Rosenberg, J. Most
Cochrane reviews have not been updated for more than 5 years. J.
Evid. Based Med. 14, 181–184 (2021).
6.
Medline PubMed production statistics. https://www.nlm.nih.gov/bsd/
medline_pubmed_production_stats.html. Accessed: 2024-09-11.
7.
Marshall, I. J. & Wallace, B. C. Toward systematic review automation:
a practical guide to using machine learning tools in research
synthesis. Syst. Rev. 8, 1–10 (2019).
8.
Brown, T. et al. Language models are few-shot learners. Adv. Neural
Inf. Process. Syst. 33, 1877–1901 (2020).
9.
Wang, S., Scells, H., Koopman, B. & Zuccon, G. Can chatgpt write a
good boolean query for systematic review literature search? In
Proceedings of the 46th International ACM SIGIR Conference on
Research and Development in Information Retrieval, 1426–1436
(2023).
10. Adam, G. P. et al. Literature search sandbox: a large language model
that generates search queries for systematic reviews. JAMIA open 7,
ooae098 (2024).
11. Wadhwa, S., DeYoung, J., Nye, B., Amir, S. & Wallace, B. C. Jointly
extracting interventions, outcomes, and ﬁndings from RCT reports

In the criteria analysis experiment, we utilized Recall@200 to assess the impact of each criterion. This was done by ﬁrst computing the relevance prediction using all eligibility predictions and then recalculating it without the eligibility prediction for the speciﬁc criterion in question. The difference in Recall@200 between these two relevance predictions, denoted as ΔRecall, indicates the criterion’s effect. A larger ΔRecall suggests that the criterion plays a more signiﬁcant role in inﬂuencing the ranking results.

To evaluate the performance of data extraction, we measured the accuracy of the values extracted by TrialMind against the ground truth. Weusedthestudycharacteristictables fromthereviewpapersasourtestset. Each table’s column names served as input ﬁeld descriptions for Trial- Mind.We manually downloadedthe full content for the studieslisted in the characteristic table. To verify the accuracy of the extracted values, we enlisted three annotators who manually compared them against the data reported in the original tables.

We also measured the performance of result extraction using accuracy. The annotators were asked to carefully read the extracted results and compare them to the results reported in the original review paper. For the error analysis of TrialMind, the annotators were asked to check the sources to categorize the errors for one of the reasons: inaccurate, extraction failure, unavailable data, or hallucination. We designed a vanilla prompting strategy for GPT-4 and Sonnet models to set the baselines for the result extraction. Speciﬁcally, the prompt was kept minimal, as “Based on the {paper}, tell me the {outcome} from the input study for the population {cohort}", where {paper} is the placeholder for the paper’s content; {out- come} is the for the target endpoint; {cohort} is the for the target popula- tion’s descriptions, including conditions and characteristics. The responses from these prompts were typically in free text, from which annotators manually extracted result values to evaluate the baselines’ performance.

In evidence synthesis, we processed the input data using R and the meta package to make the forest plots and the pooled results based on the

npj Digital Medicine | (2025) 8:509  12

https://doi.org/10.1038/s41746-025-01840-7 Article

with LLMs. In Machine Learning for Healthcare Conference, 754–771 (PMLR, 2023). 12. Zhang, G. et al. A span-based model for extracting overlapping pico entities from randomized controlled trial publications. J. Am. Med. Inform. Assoc. 31, 1163–1171 (2024). 13. Gartlehner, G. et al. Data extraction for evidence synthesis using a large language model: A proof-of-concept study. Res. Synth. Methods 15, 576–589 (2024). 14. Konet, A. et al. Performance of two large language models for data extractioninevidencesynthesis.Res.Synth.Methods15,818–824(2024). 15. Syriani, E., David, I. & Kumar, G. Screening articles for systematic reviews with ChatGPT. Journal of Computer Languages, 80, 101287 (2024). 16. Sanghera, R. et al. High-performance automated abstract screening with large language model ensembles. J. Am. Med. Inform. Assoc. 32, 893–904 (2025). 17. Trad, F. et al. Streamlining systematic reviews with large language models using prompt engineering and retrieval augmented generation. BMC Med. Res. Methodol. 25, 1–9 (2025). 18. Shaib, C. et al. Summarizing, simplifying, and synthesizing medical evidence using GPT-3 (with varying success). In The 61st Annual Meeting Of The Association For Computational Linguistics (2023). 19. Wallace, B. C., Saha, S., Soboczenski, F. & Marshall, I. J. Generating (factual?) narrative summaries of RCTs: experiments with neural multi-document summarization. AMIA Summits Transl. Sci. Proc. 2021, 605 (2021). 20. Zhang,G. et al. Closing thegapbetween opensource and commercial large language models for medical evidence summarization. npj Digit. Med. 7, 239 (2024). 21. Peng, Y., Rousseau, J. F., Shortliffe, E. H. & Weng, C. AI-generated text may have a role in evidence-based medicine. Nat. Med. 29, 1593–1594 (2023). 22. Christopoulou, S. C. Towards automated meta-analysis of clinical trials: an overview. BioMedInformatics 3, 115–140 (2023). 23. Page, M. J. et al. The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. Bmj 372, n71 (2021). 24. Luo, X. et al. Potential roles of large language models in the production of systematic reviews and meta-analyses. J. Med. Internet Res. 26, e56780 (2024). 25. Lieberum, J.-L. et al. Large language models for conducting systematic reviews: on the rise, but not yet ready for use–a scoping review. J. Clin. Epidemiol. 181, 111746 (2025). 26. Yun, H., Marshall, I., Trikalinos, T. & Wallace, B. C. Appraising the potential uses and harms of LLMs for medical systematic reviews. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing, 10122–10139 (2023). 27. National Cancer Institute. Types of cancer treatment. https://www. cancer.gov/about-cancer/treatment/types. Accessed: 2024-04-24. 28. Bodenreider, O. The uniﬁed medical language system (UMLS): integrating biomedical terminology. Nucleic Acids Res. 32, D267–D270 (2004). 29. Song, K., Tan, X., Qin, T., Lu, J. & Liu, T.-Y. Mpnet: Masked and permuted pre-training for language understanding 2004.09297 (2020). 30. Jin, Q. et al. Medcpt: Contrastive pre-trained transformers with large- scale PubMed search logs for zero-shot biomedical information retrieval. Bioinformatics 39, btad651 (2023). 31. Deeks, J. J. & Higgins, J. P. Statistical algorithms in review manager 5. Statistical Methods Group of the Cochrane Collaboration. vol. 1 (2010). 32. Shekelle, P. G. et al. Validity of the agency for healthcare research and quality clinical practice guidelines: How quickly do guidelines become outdated? JAMA 286, 1461–1467 (2001). 33. Hutson, M. How AI is being used to accelerate clinical trials. Nature 627, S2–S5 (2024).

34. Wang, Z., Theodorou, B., Fu, T., Xiao, C. & Sun, J. Pytrial: Machine learning software and benchmark for clinical trial applications. arXiv preprint arXiv:2306.04018 (2023). 35. Jin, Q., Leaman, R. & Lu, Z. Pubmed and beyond: biomedical literature search in the age of artiﬁcial intelligence. Ebiomedicine100 (2024). 36. Scells, H. et al. A test collection for evaluating retrieval of studies for inclusion in systematic reviews. In Proc. of the 40th International ACM SIGIR Conference on Research and Development in Information Retrieval, 1237–1240 (2017). 37. Wallace, B. C., Trikalinos, T. A., Lau, J., Brodley, C. & Schmid, C. H. Semi-automated screening of biomedical citations for systematic reviews. BMC Bioinforma. 11, 1–11 (2010). 38. Kanoulas, E., Li, D., Azzopardi, L. & Spijker, R. Clef 2018 technologically assisted reviews in empirical medicine overview. In CEUR workshop proceedings, vol. 2125 (2018). 39. Trikalinos, T. et al. Large scale empirical evaluation of machine learningforsemi-automating citationscreeninginsystematicreviews. In 41st Annual Meeting of the Society for Medical Decision Making (SMDM, 2019). 40. Šuster, S. et al. Automating quality assessment of medical evidence in systematic reviews: model development and validation study. J. Med. Internet Res. 25, e35568 (2023). 41. Yun, H. S., Pogrebitskiy, D., Marshall, I. J. & Wallace, B. C. Automatically extracting numerical results from randomized controlled trials with large language models. In Machine Learning for Healthcare Conference. PMLR. (2024). 42. Schmidt,L. et al. Dataextractionmethodsfor systematicreview(semi) automation: update of a living systematic review. F1000Research 10, 401 (2021). 43. Zhang, G. et al. Leveraging generative AI for clinical evidence synthesis needs to ensure trustworthiness. J. Biomed. Inform. 153, 104640 (2024). 44. Joseph, S. A. et al. Factpico: Factuality evaluation for plain language summarization of medical evidence. In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers) (pp. 8437-8464) (2024). 45. Ramprasad, S., Mcinerney, J., Marshall, I. & Wallace, B. C. Automatically summarizing evidence from clinical trials: A prototype highlighting current challenges. In Proc. of the 17th Conference of the European Chapter of the Association for Computational Linguistics: System Demonstrations, 236–247 (2023). 46. Chelli,M.et al.Hallucinationratesandreferenceaccuracyof ChatGPT and Bard for systematic reviews: comparative analysis. J. Med. Internet Res. 26, e53164 (2024). 47. Spillias, S. et al. Human-AI collaboration to identify literature for evidence synthesis. Cell Rep. Sustain. 1, 100132 (2023). 48. Lewis, P. et al. Retrieval-augmented generation for knowledge- intensive NLP tasks. Adv. Neural Inf. Process. Syst. 33, 9459–9474 (2020). 49. Wei, J. et al. Chain-of-thought prompting elicits reasoning in large language models. Adv. Neural Inf. Process. Syst. 35, 24824–24837 (2022). 50. OpenAI. Gpt-4 technical report 2303.08774 (2024). 51. Anthropic. Introducing the Claude 3 family. https://www.anthropic. com/news/claude-3-family Accessed: 2024-04-24 (2023). 52. National Center for Biotechnology Information (NCBI). Entrez programming utilities help. https://www.ncbi.nlm.nih.gov/books/ NBK25501/ Accessed: 2024-04-24 (2008).

Acknowledgements Q.J. and Z.L. were supported in part by the Division of Intramural Research (DIR) of the National Library of Medicine (NLM), National Institutes of Health. J.S. was partially supported by NSF award SCH-2205289, SCH-2014438, and IIS-2034479.

npj Digital Medicine | (2025) 8:509  13

https://doi.org/10.1038/s41746-025-01840-7 Article

Author contributions Z.W. and J.S. designed the study and developed the methodology. Z.W., L.C., and B.D. carried out data collection and analysis. Z.W., Q.J., and Z.L. conducted user studies and manual evaluations. Z.L. and J.S. supervised the overall project, providing critical feedback and direction throughout the research process. Z.W. was responsible for drafting the initial manuscript, and Q.J., Z.L., and J.S. contributed to revisions and ﬁnal edits. All authors read and approved the ﬁnal manuscript.

Publisher’s note Springer Nature remains neutral with regard to jurisdictional claims in published maps and institutional afﬁliations.

Open Access This article is licensed under a Creative Commons Attribution 4.0 International License, which permits use, sharing, adaptation, distribution and reproduction in any medium or format, as long as you give appropriate credit to the original author(s) and the source, provide a link to the Creative Commons licence, and indicate if changes were made. The images or other third party material in this article are included in the article’s Creative Commons licence, unless indicated otherwise in a credit line to the material. If material is not included in the article’s Creative Commons licence and your intended use is not permitted by statutory regulation or exceeds the permitted use, you will need to obtain permission directly from the copyright holder. To view a copy of this licence, visit http://creativecommons.org/licenses/by/4.0/.

Competing interests The authors declare no competing interests.

Additional information Supplementary information The online version contains supplementary material available at https://doi.org/10.1038/s41746-025-01840-7.

© The Author(s) 2025

Correspondence and requests for materials should be addressed to Jimeng Sun.

Reprints and permissions information is available at http://www.nature.com/reprints

npj Digital Medicine | (2025) 8:509  14
