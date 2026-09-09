---
workspace_id: "SCI-000152"
doi: "10.1109/cinti67731.2025.11311831"
title: "Large Language Models for Title/Abstract Screening in Systematic Literature Reviews: A Case Study in Precision Livestock Farming"
year: 2025
extraction_engine: "pymupdf"
---
# 2025 Zrubka Large Language Models for TitleAbstract Screening

CINTI 2025 • IEEE  25th International Symposium on Computational Intelligence and Informatics • November 18–19, 2025 • Budapest, Hungary

Large Language Models for Title/Abstract  Screening in Systematic Literature Reviews: A Case

Study in Precision Livestock Farming

2025 IEEE 25th International Symposium on Computational Intelligence and Informatics (CINTI) | 979-8-3315-5291-6/25/$31.00 ©2025 IEEE | DOI: 10.1109/CINTI67731.2025.11311831

2nd Márta Alexy  Institute of Cyberphysical Systems,

3rd Katalin Takácsné György  Department of Economics       Kodolányi János University

1st Márk Zrubka    Doctoral School of Innovation

John von Neumann Faculty of

Management  Obuda University  Budapest, Hungary  mark.zrubka@stud.uni-obuda.hu  https://orcid.org/0000-0003-4810-8400

Informatics  Obuda Unversity  Budapest, Hungary  alexy.marta@uni-obuda.hu

Székesfehérvár, Hungary

tgyk1959@outlook.hu

4th Zsombor Zrubka  University Research and Innovation

Center  Obuda University  Budapest, Hungary  zrubka.zsombor@uni-obuda.hu


## Abstract — Large language models (LLMs) are gaining

popularity in systematic literature review automation, and they 
are even acknowledged as second reviewers along humans by 
the Cochrane Handbook. In this study, we tested the 
performance of two LLMs in the title/abstract screening process 
in a systematic review on precision livestock farming cost-
benefit analyses. We assessed the screening accuracy, sensitivity 
and specificity of the GPT-4o Mini and Claude 3.5 Sonnet 
models, as well as a human rater. We also compared the time 
and costs of completing the title/abstract screening by two 
human raters versus one human assisted by LLMs. LLM-
assisted screening required less time and money than two 
human raters, but it was also less accurate, resulting in extra 
work to rescreen discrepancies. Nevertheless, combining LLMs 
with the human ratings improved the quality of the screening 
output. Our results suggest that the tested LLMs are not as 
reliable as expert humans, however, they can assist in the 
title/abstract screening process and improve the quality of work 
with very low extra resources.

on title/abstract screening, as this is the most popular research  topic in SLR automation [3].    The classic automation tools for title/abstract selection are  based on ML methods such as support vector machines or  random forests [6], which require a large and diverse set of  training data in the form of categorized articles [7,8]. In  contrast to classic ML review tools, large language models  (LLMs) do not require additional training on a categorized  subset of articles [7], as they come out of the box pre-trained  on large datasets [8]. This difference gives LLMs the  potential to be more time-efficient than other ML methods.  Furthermore, classic ML tools like Rayyan AI [9] typically  assign a ranking or probability score to articles based on title  and abstract. Inclusion and exclusion of articles is decided  based on arbitrary cutoff points that can significantly change  the results and amount of work in the full text screening phase  [2]. LLMs can categorize articles in a black box manner,  without having to define cutoff points. However, LLMs are  also capable of assigning probability scores to articles, and  even justifying the inclusion-exclusion reasons [7].     Evidence-based medicine is the flagship scientific field when  it comes to SLR methodology development. Research on  review automation tools, including LLMs, are mainly found  in the field of medical sciences. However, LLMs as title and  abstract screening tools have been tested in scientific fields  that have less standardized reporting criteria, notably  engineering [7], environmental science [10], and social  science [11]. To our knowledge, no SLR has been automated  using LLMs in precision livestock farming. Our goal was to  test LLMs as title/abstract selection tools for an ongoing SLR  on the cost-benefit analyses of precision livestock farming  technologies aimed at poultry farming.

Keywords — large language models, systematic literature  review, precision livestock farming, cost-benefit analysis

I. INTRODUCTION

A. Large language models (LLMs) in systematic literature

reviews (SLRs)  Systematic literature reviews (SLRs) are a standardized  method to identify all available evidence on a scientific topic  [1]. SLRs are essential for evidence-based policy making and  guideline development [2,3]. Conducting SLRs is a highly  labor-intensive process, especially the screening of abstracts  and full texts, and data extraction [4]. Due to the constantly  growing literature base, staying up to date in a scientific field  requires speeding up the systematic review process [2].  Hiring multiple expert reviewers can often be inaccessible or  too costly. Machine learning (ML)-based tools are becoming  increasingly popular in assisting the SLR process, and even  the Cochrane Handbook acknowledges these tools as second  reviewers along humans [5]. In the following, we will focus

B. Rationale for the systematic literature review  Precision livestock farming (PLF) is an interdisciplinary  science, where sensors, big data methods and machine  learning are used to monitor the health, wellbeing and  behavior of farm animals, and to provide timely feedback to  farmers [12,13]. PLF research is becoming increasingly

979-8-3315-5291-6/25/$31.00 ©2025 IEEE 000661

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 08,2026 at 23:11:00 UTC from IEEE Xplore.  Restrictions apply.

M. Zrubka et al. • Large Language Models for Title/Abstract Screening in Systematic Literature Reviews…

popular and plays a role in creating successful innovation  ecosystems (e.g., [14]). PLF development focuses on two  main outcomes: improving the welfare of animals and creating  more profit for farmers by optimizing production [15]. A key  issue of PLF is that farmers are reluctant to adopt these  technologies due to uncertain return on investment [16].  Rejection of PLF due to economic reasons will also take away  its potential benefits for animal welfare and sustainable  farming, therefore it is essential to study the cost-benefit  analyses in this field. A recent systematic review has already  been conducted on the economic benefits of precision  livestock farming [17], however, the scope of this review did  not cover poultry, which is one of the main animal protein  sources in the world [18]. Another limitation of [17] is that the  results only focused on production indices and were not  expressed in currency. The goal of our systematic review is to  find all cost-benefit studies on poultry PLF, which reported  their results in monetary terms.

products before the early 2010s [20]. The keywords and their  explanations are available in Supplementary Tables I. and II.  on the project’s Open Science Framework page [21].

We downloaded the search results of both databases in RIS  file format to the Zotero reference manager to obtain a pooled  list of the articles. We removed duplicates in Zotero and  exported the results to MS Excel, where we screened articles  for relevance. Author 1 completed the screening in two  phases. Article titles were first inspected to exclude obviously  irrelevant studies. Abstracts of the remaining articles were  then screened to decide if the full texts should be read for data  extraction. We assigned articles to three categories based on  their abstract. Articles that were categorized as “irrelevant”  were excluded from our study. “Relevant” articles were  included with high certainty, that the full text will contain  economic analyses on poultry PLF. Finally, articles were  categorized as “uncertain” where the abstract did not provide  sufficient information to make a clear decision. We also  included uncertain studies for full text screening. Inclusion  and exclusion criteria are shown in Supplementary Table III  [21]. In the current stage of the study, we have completed title  and abstract screening, and the full texts will be evaluated in  a later phase.

C. Research questions  In this study, we are interested in how well LLMs perform in  title/abstract screening for a systematic review in a scientific  field with less standardized reporting criteria, namely, the  cost-benefit analyses of poultry PLF technologies. The goal  of this study is to compare LLMs to human performance and  to assess their benefits. We have formulated the following  research questions to act as guidelines:

B. Title and abstract screening using LLMs  To validate the human title/abstract screening results, we  have used two large language models to independently  complete the screening procedure: Open AI’s GPT-4o Mini  and Anthropic’s Claude 3.5 Sonnet. These models were  selected because they are budget-friendly versions of popular  LLMs. We have used the application programming interface  (API) of both models in Python to evaluate each article title  and abstract. Default settings were used for both models with  a temperature of 1. Both models were given the same prompt  that describes the key points of the human screening  procedure. Full prompt, with explanations is provided in  Supplementary Table III on the project’s Open Science  Framework page [21]. We provided the context of the study,  gave the models the role of a researcher and used a chain-of- thought prompting method, which results in better LLM  performance [22]. Articles were given three categories  (relevant,  irrelevant,  uncertain),  resembling  human  screening.

  Research question 1: How well do LLMs perform  compared to a human rater in title/abstract screening  accuracy, sensitivity and specificity?

  Research question 2: How fast are the LLMs in  title/abstract screening compared to humans?

  Research question 3: How much does it cost to  perform a title/abstract screening task for two  human expert raters, compared to one human  accompanied by 2 LLMs?

II. METHODS

A. Systematic literature review: Title and abstract screening

For our review, we were looking for journal articles and  conference papers in English, on the cost-benefit analyses of  PLF technologies in the poultry sector. We have searched for  articles in the Scopus and Web of Science databases. For our  search phrases, we have used three categories of keywords:

C. Evaluating screening results  To evaluate the accuracy of LLMs and the human rater  (Author 1), we created a benchmark rating, which served as  the ground truth. If both LLMs and the human rater  categorized an article as “relevant”, it would be automatically  categorized as “relevant” in the benchmark too. The same  principle applied to uncertain and irrelevant articles. If there  was any disagreement between ratings, the human rater  would re-screen the title and abstract and make a final  decision considering the three ratings. Some disagreements  were easier to resolve, for example, if the human and one  LLM included an article and another LLM marked it as  uncertain, it was most likely categorized as “relevant” in the  benchmark. Sometimes the human rater included an article  by overlooking an exclusion criterion and LLMs marked it as  “irrelevant”. The decision about the benchmark rating was  ultimately made by the human reviewer. LLM ratings were

  precision livestock farming (PLF)    poultry    cost-benefit analyses

The PLF and poultry keywords were adapted from [19], but  were extended with the keywords “Internet of Things” and  “Computer Vision”, which are often present in PLF studies  after 2019. We have searched for cost-benefit analyses using  the vague keywords “econom*” and “cost*”, so we can  include a large scope of studies in the field. We have searched  for articles in the last 10 closed years, from 2015 to 2024,  since there were virtually no commercially available PLF

000662

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 08,2026 at 23:11:00 UTC from IEEE Xplore.  Restrictions apply.

CINTI 2025 • IEEE  25th International Symposium on Computational Intelligence and Informatics • November 18–19, 2025 • Budapest, Hungary

3) Research question 3: Screening costs

considered as a suggestion, and they could not change the  rating without the approval of the human reviewer.

For LLMs, we calculated the cost (CLLM) of the screening task  by multiplying input and output tokens by their current prices,  based on the pricing lists of OpenAI [25] and Anthropic [26].  For human raters, we estimated a junior researcher net hourly  salary (cost of human rater, CH) based on the European  Commission’s salary table for research fellows [27]. We used  the lowest paygrade (function group II, Grade4) without any  correction or allowances, which returned a net monthly salary  of 2 074 EUR = 2 235 USD. We used the European Central  Bank’s average EUR-USD conversion rate for 2024. We  divided the monthly salary by 168 working hours, resulting  in a net hourly salary of 13.3 USD.

1) Research question 1: Screening accuracy

To evaluate the results, we converted the three-level rating  into a binary ‘included’ or ‘excluded’ rating. Irrelevant  articles were excluded, relevant and uncertain articles were  included for full text screening. We compared the human and  LLM ratings to the benchmark rating using several metrics.  We used accuracy to check how well the ratings overlap with  the benchmark. We calculated sensitivity as a measure of how  well the raters included relevant articles. Specificity was also  calculated as a measure of how good raters were at excluding  irrelevant articles [23].

The cost of LLM-assisted screening (Scenario 1, CS1) was  calculated using (3). The cost of human labor (CH) is  calculated by multiplying screening time by the hourly salary.  The token-based cost of LLMs (CLLM) is independent of  screening time.

2) Research question 2: Screening time

We estimated the time it took for a human and two LLMs to  complete the title/abstract screening task. For the LLMs, we  timed the entire task in Python. We estimated the human  rater’s time by dividing the total number of words in the  title/abstract list by the average reading speed of 238 words  per minute, which applies for non-fiction text [24]. We also  added an estimated time of 10 seconds decision time for  humans per article. In practice, we did a two-round screening  by excluding articles based on titles first and only screening  the remaining abstracts. However, for our calculations, we  assumed that human raters had to screen all titles and  abstracts once, as this is a more generalizable method for  other studies.

CS1 = CLLM + CH(TH + RLLM(TH))   

The cost of two human raters (Scenario 2, CS2) was calculated  in (4), by multiplying the screening time in (2) by the hourly  salary.

CS2 = CH(2TH + RH(TH)) 	



III. RESULTS

We simulated two scenarios for the screening procedure. In  Scenario 1, one human rater is assisted by two LLMs. The  total review time of Scenario 1 (TS1) is calculated in (1). TH is  the time required by the human rater to screen all titles and  abstracts, including a 10 second decision time for every  article. TLLM is the time it took the two LLMs to complete the  screening task. TH and TLLM are expressed in hours. RLLM is  the percentage of rescreened articles due to discrepancy  between human and LLM ratings.

A. Article selection  The Scopus and Web of Science searches returned a total of  1234 articles. After removing 347 duplicates, 887 articles  were left for title and abstract screening. 578 articles were  excluded based on title, and 309 abstracts were reviewed.  After screening the abstracts, 80 articles were selected for full  text screening by the human rater. The results of the human  rater and two LLMs were compared and discrepancies in  ratings were found for 152 articles. This means the  rescreening rate was RLLM = 17.14% (152/887).  After  resolving mismatched ratings, 61 articles were included for  final full text screening as the benchmark. The human rater  made 35 errors in total, 27 false positives and 8 false  negatives. The PRISMA flowchart for the title/abstract  screening process is shown in Fig. 1.

TS1 = TH + TLLM + RLLM(TH) 

In Scenario 2, we simulated how long it would take two  human raters with the same performance to complete the  screening task. The total screening time for Scenario 2 (TS2)  is calculated in (2).  For the first screening, we multiplied TH  by 2, assuming both raters have the same speed. RH is the  rescreening rate due to discrepancies between the 2 human  raters. We estimated this rate by doubling the measured false  positive and false negative ratings for the human rater.  Similarly to the LLM-assisted scenario, only one human rater  is rescreening the articles. We estimated the aggregate time  required to complete the task. For the sake of simplicity, we  did not assume that the two human raters would work in  parallel and we also did not convert hours into working days.

B. Comparing human and LLM performance

1) Research question 1: Screening accuracy  Compared to the benchmark ratings, accuracy and specificity  were above 90% for the human rater and both LLMs, and  sensitivity was considerably lower for all raters. GPT-4o  Mini (94.31%) has slightly outperformed Claude 3.5 Sonnet  (92.25%) in specificity. However, the Claude Sonnet model  had remarkably higher sensitivity at 80.33% than the GPT  model at 59.02%. The accuracy metrics are displayed in  Table I.

TS2 = 2TH + RH(TH) 



000663

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 08,2026 at 23:11:00 UTC from IEEE Xplore.  Restrictions apply.

M. Zrubka et al. • Large Language Models for Title/Abstract Screening in Systematic Literature Reviews…

3) Research question 3: Screening costs

TABLE I.   SCREENING ACCURACY COMPARISON

The cost of LLM screening (CLLM) was 3.26 USD, calculated  using input and output tokens. The number of tokens and  prices for both models are shown in Table II. Using (3) and  (4), the total screening cost of LLM-assisted screening was  CS1 = 280.48 USD, and the estimated total cost of two human  raters was CS2 = 492.18 USD. We compare the LLM-assisted  screening and two human raters by rescreening rate, total  screening time and cost of work in Table III.

Rater  Accuracy  Sensitivity  Specificity

Human  96.05%  86.89%  96.73%

GPT-4o

Mini  91.88%  59.02%  94.31%

Claude 3.5

Sonnet  91.43%  80.33%  92.25%

TABLE II.   LLM COSTS

LLMs  Tokens  USD/  1M tokens  Cost (USD)

GPT-4o Mini

input  720296  1.10  0.79

GPT-4o Mini

output  887  4.4  0.004

Claude 3.5

Sonnet

803868  3  2.41

input

Claude 3.5

Sonnet

3792  15  0.057

output

Total  1528843  -  3.26

TABLE III.   SCREENING SIMULATION RESULT COMPARISON

Aggregated

Scenario  Rescreened  articles (N)

working  time (hours)

Cost (USD)

1)Human &  LLM  152 (17.1%)  21.59  280.48

2) 2 Human  raters  70 (7.9%)  37.01  492.18

IV. DISCUSSION

Fig. 1. PRISMA flowchart of the screening process. Each stage shows  the initial results of the human rater and the revised results after cross- checking with LLMs.

A. Research question 1: Screening accuracy  Compared to the benchmark ratings, the human rater and both  LLMs performed above 90% in both accuracy and  specificity. Even though this accuracy and specificity seem  high, combining three different ratings revealed that 17.1%  of the articles had to be rescreened due to discrepancies. This  rescreening rate is high, especially for SLRs where thousands  of articles are screened. The human rater and both LLMs  performed poorly in sensitivity, especially GPT-4o Mini,  meaning that they failed to include all relevant articles. For  SLRs, low specificity means more rescreening time due to  including potentially irrelevant studies in the screening. On  the other hand, low sensitivity means excluding relevant  articles, which is more problematic, as the main goal of SLRs  is to include all available research results on a topic [1]. While  LLMs were not trustworthy as independent reviewers, they  improved the human results by reducing the number of false  negatives and false positives after rescreening was  completed.

2) Research question 2: Screening time  The titles and abstracts of the 887 articles contained 219 117  words in total. Dividing by the reading speed of 238 words  per minute, we get 921 minutes of pure screening time. The  decision time of 10 seconds for 887 articles equals 147  minutes. Adding pure screening time and decision time, we  get 1068 minutes, TH = 17.8 hours. The combined run time of  the LLM screening was 45 minutes, TLLM = 0.75 hours. Using  (1) with the rescreening rate RLLM = 17.14%, the total  screening time for LLM-assisted human screening was TS1 =  21.59 hours. In comparison, the estimated total screening  time for the two human raters was TS2 = 37.01 hours based on  (2). The rescreening rate was RH = 7.89%, assuming both  human raters made 35 screening mistakes without  overlapping.

B. Research questions 2&3: Screening time and costs  Two LLMs completed the same screening task almost 25  times faster than the human rater. Due to inaccuracies in the

000664

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 08,2026 at 23:11:00 UTC from IEEE Xplore.  Restrictions apply.

CINTI 2025 • IEEE  25th International Symposium on Computational Intelligence and Informatics • November 18–19, 2025 • Budapest, Hungary

LLM ratings, 152 articles had to be rescreened, which  extended the whole screening process. Nevertheless, taking  all factors into account, LLM-assisted screening took 21  hours to complete, whereas the combined time of two human  raters was 37 hours. The same pattern was observed in the  costs of labor. The combined cost of two LLMs was 3.26  USD. Despite more rescreening time to inaccuracies, LLM- assisted screening cost almost half as much as two human  raters.


## results. Measuring human performance had challenges too.

Our current study gives a close estimation of performance, 
but timing the entire process for two raters would have 
provided more reliable results. A well-planned screening 
process where two human raters are working in parallel might 
have taken almost the same time as one rater using LLMs, 
which was not reflected in our study.

C. Next steps  In the next stage of our study, we will extend the current  search results with the AgEcon Search database. This  database was not searched for this study because it does not  allow complex search phrases like Scopus and Web of  Science. We will continue to download and screen full texts  from the final list of articles with the help of LLMs. Extracted  data will include the effects of PLF technology on costs and  profit, as well as poultry sample sizes and farm parameters.

V. CONCLUSIONS

A. Summary  In this study, we tested the performance of two budget- friendly LLMs (GPT-4o Mini and Claude 3.5 Sonnet) in the  title/abstract screening process of an SLR. The topic of the  systematic review is the cost-benefit analyses of PLF in the  poultry industry.  The reporting standards of PLF studies are  less well defined than of medical sciences, making our study  a good test case for the generalizability of LLMs in the SLR  process. We combined the title/abstract ratings of the human  rater and both LLMs to create a benchmark. We evaluated the  accuracy, sensitivity and specificity of the human rater and  LLMs against the benchmark. Accuracy and specificity  appeared high, however, comparing the ratings revealed that  results of the human rater and LLMs did not overlap well,  resulting in extra work due to rescreening. Most importantly,  the sensitivity of the human rater and both LLMs was subpar,  but combining the results improved the human rater’s  performance. We created two scenarios using the obtained  data to simulate the results of an LLM-assisted screening  procedure and two human raters. The LLM-assisted  screening required almost half of the time and costs than the  screening completed by two human raters. However, the two  human raters outperformed the LLM-assisted rater in the  rescreening rate even when a worst-case scenario was  simulated.    In conclusion, our study shows that using LLMs to assist the  title/abstract screening process of SLRs can improve human  performance in a cost-effective manner, but LLMs are not  reliable enough to substitute human experts. The inaccuracy  of the LLMs caused a considerable amount of extra  rescreening work due to high discrepancy rates between  ratings. We recommend conducting the title/abstract  screening task with two human raters if the budget and time  constraints allow for it, accompanied by LLMs to correct for  mistakes.


## REFERENCES

[1] M. Péntek, Z. Zrubka, L. Gulácsi, M. Weszl, J. Tibor Czere, and T.

Haidegger, “10 Pragmatic Points to Consider When Performing a  Systematic Literature Review of Clinical Evidence on Digital Medical  Devices,” ACTA POLYTECH HUNG, vol. 20, no. 8, pp. 281–303,  2023, doi: 10.12700/APH.20.8.2023.8.15.  [2] F. Trad et al., “Streamlining systematic reviews with large language

models using prompt engineering and retrieval augmented generation,”  BMC Med Res Methodol, vol. 25, no. 1, p. 130, May 2025, doi:  10.1186/s12874-025-02583-5.  [3] B. Tóth, L. Berek, L. Gulácsi, M. Péntek, and Z. Zrubka, “Automation

of systematic reviews of biomedical literature: a scoping review of  studies indexed in PubMed,” Syst Rev, vol. 13, no. 1, p. 174, July 2024,  doi: 10.1186/s13643-024-02592-3.  [4] J. Clark, P. Glasziou, C. Del Mar, A. Bannach-Brown, P. Stehlik, and

A. M. Scott, “A full systematic review was completed in 2 weeks using  automation tools: a case study,” J Clin Epidemiol, vol. 121, pp. 81–90,  May 2020, doi: 10.1016/j.jclinepi.2020.01.008.  [5] M. Cumpston et al., “Updated guidance for trusted systematic reviews:

a new edition of the Cochrane Handbook for Systematic Reviews of  Interventions,” Cochrane Database Syst Rev, vol. 2019, no. 10, p.  ED000142, Oct. 2019, doi: 10.1002/14651858.ED000142.  [6] J. K. Kim et al., “Evaluating large language models for title/abstract

screening: a systematic review and meta-analysis & development of  new tool,” Journal of Medical Artificial Intelligence, vol. 8, no. 0, Art.  no. 0, Dec. 2025, doi: 10.21037/jmai-24-408.  [7] B. Nykvist, B. Macura, M. Xylia, and E. Olsson, “Testing the utility of

GPT for title and abstract screening in environmental systematic  evidence synthesis,” Environ Evid, vol. 14, no. 1, p. 7, Apr. 2025, doi:  10.1186/s13750-025-00360-x.  [8] R. Qureshi, D. Shaughnessy, K. A. R. Gill, K. A. Robinson, T. Li, and

E. Agai, “Are ChatGPT and large language models ‘the answer’ to  bringing us closer to systematic review automation?,” Syst Rev, vol. 12,  no. 1, p. 72, Apr. 2023, doi: 10.1186/s13643-023-02243-z.  [9] “Rayyan: AI-Powered Systematic Review Management Platform.”

B. Limitations  The main limitation of our study is that we used default  parameters for the LLMs, where temperature is set to 1. This  means that results may vary across replications. It is unsure  how significantly temperature changes the consistency of  LLMs in title/abstract selection. This question should be  explored in a future study. Another major limitation is that  we tested budget-friendly LLMs that might not reflect the  performance of state-of-the-art models. Furthermore, the  prompt used in this study did not explicitly mention cost- benefit analysis, which might have significantly impacted the

Accessed: Aug. 02, 2025. [Online]. Available: https://www.rayyan.ai/  [10] K. Nguyen-Trung, A. K. Saeri, and S. Kaufman, “Applying ChatGPT

and AI-Powered Tools to Accelerate Evidence Reviews,” Human  Behavior and Emerging Technologies, vol. 2024, no. 1, p. 8815424,  2024, doi: 10.1155/2024/8815424.  [11] Q. Khraisha, S. Put, J. Kappenberg, A. Warraitch, and K. Hadfield,

“Can large language models replace humans in systematic reviews?  Evaluating GPT-4’s efficacy in screening and extracting data from  peer-reviewed and grey literature in multiple languages,” Research  Synthesis Methods, vol. 15, no. 4, pp. 616–626, 2024, doi:  10.1002/jrsm.1715.  [12] D. Berckmans, “General introduction to precision livestock farming,”

Animal Frontiers, vol. 7, no. 1, pp. 6–11, Jan. 2017, doi:  10.2527/af.2017.0102.

000665

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 08,2026 at 23:11:00 UTC from IEEE Xplore.  Restrictions apply.

M. Zrubka et al. • Large Language Models for Title/Abstract Screening in Systematic Literature Reviews…

[13] S. Neethirajan, “The role of sensors, big data and machine learning in

[20] T. M. Banhazi et al., “Precision Livestock Farming: An international

modern animal farming,” Sensing and Bio-Sensing Research, vol. 29,  p. 100367, Aug. 2020, doi: 10.1016/j.sbsr.2020.100367.  [14] T. P. Haidegger et al., “Strategies and Outcomes of Building a

review of scientific and commercial aspects,” International Journal of  Agricultural and Biological Engineering, vol. 5, no. 3, 2012.  [21]  “Open Science Framework - Cost-benefit analyses of poultry precision

Successful University Research and Innovation Ecosystem,” ACTA  POLYTECH HUNG, vol. 21, no. 10, pp. 13–35, 2024, doi:  10.12700/APH.21.10.2024.10.2.  [15] S. Neethirajan, S. Scott, C. Mancini, X. Boivin, and E. Strand,

livestock farming: A systematic review,” Aug. 2025, [Online].  Available: https://osf.io/tr39s   [22] J. Wei et al., “Chain-of-Thought Prompting Elicits Reasoning in Large

Language Models,” Adv. Neural. Inf. Process. Syst., no. 35, pp. 24824- -24837, 2022.  [23] J. Shreffler and M. R. Huecker, “Diagnostic Testing Accuracy:

“Human-computer interactions with farm animals—enhancing welfare  through precision livestock farming and artificial intelligence,” Front.  Vet. Sci., vol. 11, Nov. 2024, doi: 10.3389/fvets.2024.1490851.  [16] I. Kopler et al., “Farmers’ Perspectives of the Benefits and Risks in

Sensitivity, Specificity, Predictive Values and Likelihood Ratios,” in  StatPearls, Treasure Island (FL): StatPearls Publishing, 2025.  Accessed:  July  31,  2025.  [Online].  Available:  http://www.ncbi.nlm.nih.gov/books/NBK557491/  [24] M. Brysbaert, “How many words do we read per minute? A review and

Precision Livestock Farming in the EU Pig and Poultry Sectors,”  Animals, vol. 13, no. 18, Art. no. 18, Jan. 2023, doi:  10.3390/ani13182868.  [17] G. Papadopoulos et al., “Economic and environmental benefits of

meta-analysis of reading rate,” Journal of Memory and Language, vol.  109, p. 104047, Dec. 2019, doi: 10.1016/j.jml.2019.104047.  [25] “Pricing” OpenAI. Accessed: Aug. 03, 2025. [Online]. Available:

digital agricultural technological solutions in livestock farming: A  review,” Smart Agricultural Technology, vol. 10, p. 100783, Mar.  2025, doi: 10.1016/j.atech.2025.100783.  [18] “Poultry production | Gateway to poultry production and products |

https://openai.com/api/pricing/  [26] “Pricing” Anthropic. Accessed: Aug. 03, 2025. [Online]. Available:

FAO,” PoultryProduction. Accessed: Aug. 02, 2025. [Online].  Available:  https://www.fao.org/poultry-production- products/production/poultry-production/en  [19] E. Rowe, M. S. Dawkins, and S. G. Gebhardt-Henrich, “A Systematic

https://docs.anthropic.com/en/docs/about-claude/pricing  [27] “Job Opportunities for Research Fellows at the European Commission

- European Commission.” Accessed: Aug. 03, 2025. [Online].  Available:  https://joint-research-centre.ec.europa.eu/jobs-jrc/job- opportunities-research-fellows-european-commission_en

Review of Precision Livestock Farming in the Poultry Sector: Is  Technology Focussed on Improving Bird Welfare?,” Animals, vol. 9,  no. 9, Art. no. 9, Sept. 2019, doi: 10.3390/ani9090614.

000666

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 08,2026 at 23:11:00 UTC from IEEE Xplore.  Restrictions apply.
