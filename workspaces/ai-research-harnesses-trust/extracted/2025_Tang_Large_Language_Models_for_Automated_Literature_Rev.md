---
workspace_id: "SCI-000125"
doi: "10.18653/v1/2025.emnlp-main.83"
title: "Large Language Models for Automated Literature Review: An Evaluation of Reference Generation, Abstract Writing, and Review Composition"
year: 2025
extraction_engine: "pymupdf"
---
# 2025 Tang Large Language Models for Automated Literature Rev

Large Language Models for Automated Literature Review: An Evaluation

of Reference Generation, Abstract Writing, and Review Composition

Xuemei Tang1 Xufeng Duan3* Zhenguang G. Cai2,3*

1The Department of Language Science and Technology, The Hong Kong Polytechnic University 2Department of Linguistics and Modern Languages, The Chinese University of Hong Kong 3Brain and Mind Institute, The Chinese University of Hong Kong xuemeitang00@gmail.com {xufengduan, zhenguangcai}@cuhk.edu.hk


## Abstract

complex and time-consuming process, especially in well-established fields where the number of rele- vant references can range from dozens to hundreds. To alleviate this burden, researchers have recently turned to advanced deep learning models as a po- tential tool to aid in the automated generation of literature reviews (Aliyu et al., 2018; Kontonatsios et al., 2020).

Large language models (LLMs) have emerged as a potential solution to automate the complex processes involved in writing literature reviews, such as literature collection, organization, and summarization. However, it is yet unclear how good LLMs are at automating comprehensive and reliable literature reviews. This study in- troduces a framework to automatically evaluate the performance of LLMs in three key tasks of literature review writing: reference generation, abstract writing, and literature review compo- sition. We introduce multidimensional evalua- tion metrics that assess the hallucination rates in generated references and measure the seman- tic coverage and factual consistency of the lit- erature summaries and compositions against human-written counterparts. The experimen- tal results reveal that even the most advanced models still generate hallucinated references, despite recent progress. Moreover, we observe that the performance of different models varies across disciplines when it comes to writing lit- erature reviews. These findings highlight the need for further research and development to improve the reliability of LLMs in automating academic literature reviews. The dataset and code used in this study are publicly available in our GitHub repository 1.

The emergence of LLMs has introduced a promising avenue for automating key aspects of literature review writing, including identifying rele- vant sources, summarizing findings, and generating coherent syntheses (Wang et al., 2024b; Agarwal et al., 2024; Hsu et al., 2024).

While techniques such as Retrieval-Augmented Generation (RAG) can enhance the domain- specific knowledge of LLMs—by providing ac- cess to real literature databases and helping gen- erate more accurate content—in practice, most re- searchers still rely on vanilla LLMs, such as Chat- GPT, for literature review writing without the use of RAG (Wang et al., 2024a). Consequently, it is crucial to evaluate the performance of these naive LLMs in the context of literature review writing to determine their effectiveness and limitations.

Therefore, in this paper, we propose a frame- work for automatically assessing the literature re- view writing ability of LLMs, using human-written literature reviews as the gold standard and design- ing metrics for a comprehensive evaluation. We first collect a dataset of human-written literature reviews to serve as a benchmark for evaluating the performance of LLMs. We then ask LLMs to complete three tasks based on the collected dataset: generating references, writing an abstract, and writ- ing a complete literature review based on a given topic. Finally, we evaluate the generated results from several dimensions, including the presence of hallucinations in the references, as well as the semantic coverage and factual consistency of the generated abstract and literature review compared

1 Introduction

The literature review is a critical component of academic writing that aims to synthesize, critique, and assess the current state of knowledge in a par- ticular field. It involves a comprehensive exami- nation of published research articles, theoretical frameworks, and research methodologies related to a specific topic. Conducting a thorough litera- ture review often necessitates extensive reading and summarizing of pertinent literature, which can be a

*Corresponding Author 1https://github.com/tangxuemei1995/Eval_LLM_ Literature_Review

1602

Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing, pages 1602–1617

November 4-9, 2025 ©2025 Association for Computational Linguistics

to the human-written context. By assessing the performance of LLMs across these tasks and evalu- ating their output using our proposed metrics, we aim to provide a comprehensive understanding of their capabilities and limitations in writing litera- ture reviews.

citations. For instance, Chelli et al. (2024) ana- lyzed hallucination rates in 11 systematic reviews on shoulder rotator cuff pathology generated by ChatGPT, GPT-4, and Bard, finding Bard exhib- ited significantly higher hallucination rates. Simi- larly, Agrawal et al. (2024) evaluated hallucinations across 200 computer science topics by generating reference titles with LLMs and verifying their ex- istence via the BING Search API, further probing whether LLMs could detect hallucinated references through direct and indirect queries. Athaluri et al. (2023) examined hallucinations in 50 ChatGPT- generated research proposals, manually validating references and DOIs using Scopus, Google, and PubMed, reporting 109 valid DOIs among 178 ref- erences. Additionally, Aljamaan et al. (2024) in- troduced the Reference Hallucination Score (RHS) by generating references for five medical topics across multiple LLMs, assigning weighted halluci- nation scores to citation components such as title and publication date. While these studies provide valuable insights, they are generally limited to spe- cific domains and rely heavily on manual evalua- tion, lacking a comprehensive, scalable assessment framework for LLM reference hallucinations.

Our contribution can be summarized as follows.

• First, we propose a framework for automati- cally evaluating the literature review writing ability of LLMs, without requiring any human involvement. This framework encompasses multiple stages, including the compilation of a literature review dataset construction, the collection of LLM-generated output, and the evaluation of LLM performance.

• Second, we collect 1,105 literature reviews from 51 journals across six disciplines as the ground truth. We then design three tasks for accessing LLMs in literature writing: refer- ence generation, abstract writing, and litera- ture composition on a given topic.

• Then, we evaluate the generated results of LLMs from multiple perspectives, including the hallucination rate in generated references, factual consistency, and semantic coverage compared to human-written content.

3 Methodology

In this section, we propose a framework for evalu- ating LLMs’ literature review writing ability. The framework, as shown in Figure 1, consists of three main stages: dataset construction and task design for evaluation, collection LLM-generated output, and assessment of the generated output.

• Finally, we assess five LLMs using the pro- posed framework. By analyzing the experi- mental results, we find that hallucinated ref- erences remain a prevalent issue for current LLMs. Furthermore, the performance of LLMs in writing literature reviews varies across different disciplines.

3.1 Dataset Construction

Assessing the ability to write literature reviews is a challenging task, as evaluating the quality of con- tent is inherently complex. In this paper, we use human-written reviews as the gold standard, which simplifies the evaluation process to some extent. As illustrated in Figure 1, we first collect publicly available information of literature reviews (i.e., the title, authors, abstract, keywords, and content) from the Annual Reviews website 2. Annual Reviews, an independent nonprofit publisher, produces 51 review journals spanning various scientific disci- plines. Invited experts write comprehensive, au- thoritative reviews that synthesize and summarize the most significant primary research literature in their field, providing a valuable resource for re-

2 Related Work

Recent studies have explored LLMs for litera- ture review generation. For example, Wang et al. (2024b) proposed AutoSurvey, which incorporates up-to-date papers via retrieval-augmented gener- ation. Agarwal et al. (2024) examined zero-shot LLM review generation using a two-step retrieval and outlining process. More recently, Liang et al. (2025) presented SurveyX, an efficient system that optimizes retrieval, extraction, and outline genera- tion, supporting multimodal outputs such as figures and tables.

Additionally, recent efforts to evaluate litera- ture review generation by LLMs have increasingly focused on assessing hallucinations in reference

2https://www.annualreviews.org/

1603

Task Design

Metric Design

Task1: Reference Generation

• Hallucination rate • Factual consistency • Semantic coverage

Task2: Abstract Writing

Task3: Review Composition

... ...

Data Collection

LLMs Generated Text Leaderboard

Evaluator


> **Figure 1: Illustration of the evaluation framework.**

searchers to stay current with the latest develop- ments. We crawl all articles published in 2023, including their title, keywords, abstracts, contents, and references, and then clean them to create the experimental dataset.

covered subtopics—which are also critical in structuring comprehensive literature reviews. By evaluating the model’s ability to generate coherent and topic-relevant abstracts, we as- sess its potential to assist researchers in the early planning stages of literature review writ- ing.

Then, the dataset D is the article set from 51 journals, D = {p0, ..., pi, ..., pM}, where M rep- resents the number of articles. Each article pi = {ti, wi, ai, ci, Ri}, where ti, wi, ai, ci, Ri repre- sent the title, keywords, abstract, context, and ref- erence set Ri = {r1, ..., rk, ..., rK}, and K repre- sents the length of the reference set.

• Review Composition: Given the article ti and keywords wi, and abstract ai, ask LLMs to write a short literature review cg

i according to the research topic provided in the title, key- words, and abstract. To facilitate evaluation and accommodate computational budget con- straints, the length of each literature review is limited to approximately 1000 words. LLMs also need to back up claims by citing relevent studies Rg

3.2 Task Design

Since literature review writing primarily involves the collection and synthesis of relevant research, we design three independent tasks as follows to evaluate LLMs’ capabilities in different aspects of literature review writing.

1, ..., rg n, ..., rg

i = {rg

N} (with a total of N citations in the literature review). These citations are newly generated to support the content of the review. In this task, we eval- uate whether LLMs can write a high-quality literature review and cite truth studies.

• Reference Generation: Given the article title ti and keywords wi, ask LLMs to find the N most relevant studies Rg

i = {rg

1, ..., rg n, ..., rg

N} to the research topic. Each citation study must include 7 metadata el- ements: title, authors, journal, year, vol- umes, first page, and last page, rg

We designed the three tasks as independent tasks for two main reasons: a. Each task has a differ- ent goal. Task 1 (Reference Generation) aims to evaluate the LLMs’ ability to recommend relevant papers, which is a common practical use case — re- trieving relevant literature based on a specific topic. Task 2 (Abstract Writing) evaluates the LLMs’ abil- ity to outline and plan a literature review through abstract writing. Task 3 (Review Composition) as- sesses whether LLMs can organize and synthesize multiple sources into a coherent review while also providing verifiable references. b. We intentionally separated the tasks to avoid cross-task interference, which would make it difficult to isolate and evalu- ate specific capabilities of LLMs.

n = {T, A, J, Y, V, FP, LP}. In this task, we evaluate whether LLMs can recommend reli- able references based on the given topic. Note that these references are not reused in later tasks.

• Abstract Writing: Given an article title ti and its associated keywords wi, the LLMs are prompted to generate an abstract ag

i that aligns with the research topic. The length of the generated abstract is constrained to match that of the original. This task serves as a proxy for literature review planning, as ab- stracts often outline the key components of a study—such as its objectives, methods, and

Three task prompts are shown in Appendix Ta- ble 5.

1604

3.3 Evaluation Metrics

nor variations, we consider the title to be correct if it achieves a match rate of at least 80% with the ground-truth title—a threshold determined through human evaluation.

Based on the type of generated text, we divide the evaluation of the model’s results into two parts: first, the hallucination rate of the references gen- erated by LLMs, and second, a comparison of the generated context with human-written results, in- cluding two dimensions: factual consistency and semantic coverage.

Metadata-based matching: If the title T is in- correct (i.e., e0 = 0), we still consider the reference reliable if at least three of the remaining metadata elements (author, journal, year, volume, first page, last page) match those of a real article. This allows us to identify true references even when the title is noisy or incomplete.

Reference hallucination evaluation metrics. Given that LLMs are trained on vast corpora, in- cluding academic sources, we aim to evaluate whether they can generate true references. In this section, we introduce the calculation process of the reference precision Precision, reference overlap rate with human-cited references Overlap rate, and title search rate St for each LLM. A higher preci- sion metric indicates a lower hallucination rate. A higher overlap indicates that the LLM-generated references cover more of the ground-truth citations used by human authors, reflecting a better ability to identify key prior work relevant to the topic.

  

 



e0 = 1 and P6

1 if

i=1 ei ≥1

 



e0 = 0 and P6

True(rg

(1)

or

i=1 ei ≥3

n) =

 

0 otherwise

For each paper pi in the dataset, we compute the ref- erence precision of the LLM-generated references, denoted as Precision(pi), as defined in Eq. 2. We then obtain the overall Precision score for each LLM by averaging Precision(pi) across all papers in the dataset, as shown in Eq. 3.

For each article pi ∈D, each LLM generates N references Rg

N X

Precision(pi) = 1

True(rg

n) (2)

1, ..., rg n, ..., rg

i = {rg

N} in both Ref- erence Generation and Review Composition tasks, each rg

N

n=0

M X

n and includes 7 elements. Each element corresponding to a state label represents whether it is accurate or not {ed}6

Preicison = 1

Precison(pi) (3)

M

i=0

d=0, ed = 1 or 0. Next, we describe how to obtain {ed}6

Precision is measured by comparing the LLM- generated references with external academic databases. We also evaluate Overlap rate by com- paring the references generated by the LLM with those cited in the human-written original articles. The key difference between precision and overlap rate in our setting lies in the candidate set Z: for precision, Z is constructed from external academic search results, whereas for overlap rate, Z con- sists of the references actually cited in the human- written articles.

d=0. First, we use the generated titles T and the first author in A as the queries and search them separately from external academic search engines. This re- sults in two sets of candidate articles, Zt and Za respectively, We then merge the two sets and re- move duplicates to obtain the final candidate set Z = {z1, ..., zj, ..., zJ}. Subsequently, we com- pare the generated rg

n with the article zj from can- didate sets Z. For example, if the title of a candi- date article zj matches the title of rg

n, then e0 = 1. Finally, we find the best candidate article based on the sum of {ed}6

Additionally, the title is intuitively the most crit- ical element in determining the faithfulness of a generated reference. In the work of Agrawal et al. (2024), ground-truth labels were assigned based on results returned by the Bing Search API. In- spired by their approach, we also calculate the title search score for each LLM to estimate how many generated titles correspond to real publications.

d=0, and the one with the largest sum is the best candidate article zj of rg

n. Then, we compare the alignment degree between the generated reference rg

n and the best-matching candidate article zj to determine whether rg

n cor- responds to a real article (as shown in Eq. 1). We consider rg

n to be reliable under either of the fol- lowing two conditions:

X

X

St = 1 MN

s(n)

pi (4)

Title-based matching: If the title T is correct (i.e., e0 = 1), and at least one other metadata ele- ment (e.g., author, journal, year, etc.) also matches, the reference is deemed reliable. To allow for mi-

M

N

  

1 if the T ∈rg

n has return value from external Scholar API, 0 otherwise

X

s(n)

(5)

pi =

 

rg

n∈Rg

i

1605

where cg

Here, s(n)

i denotes the literature review generated by LLMs.

pi indicates whether the generated title in reference rg

n for paper pi can be found using an external academic search engine. This metric helps estimate the proportion of references with verifi- able titles among the total generated references.

Finally, we also concatenate key points and com- pute the ROUGE metric between the key points and cg

i .

Context evaluation metrics. In our study, we use the human-written article as the gold truth and then evaluate LLM-generated context from factual consistency and semantic coverage aspects. The resemblance of natural language inference (NLI) to factual consistency evaluation has led to utilizing NLI models for measuring factual consistency (Gao et al., 2023). Encouraged by previous works, we also use the NLI method to evaluate the factual consistency between LLMs generated and human- written text. For example, we calculate the NLI score Entailpi between the original article abstract ai and the LLM-generated abstract ag

4 Experiments

4.1 Experimental Settings

Dataset. We collect 1,105 literature review articles published in 2023 from the Annual Reviews web- site. The distribution of articles across journals is shown in Appendix B, Figure 5.

LLMs Selection. We evaluate five LLMs: Claude-3.5-Sonnet-20240620, GPT-4o-2024-08- 16, Qwen-2.5-72B-Instruct, DeepSeek-V3, and Llama-3.2-3B-Instruct. All model outputs were generated via their official APIs with temperature set to 0 for consistency.

i as follows.

(

1 if ag

i entails ai, 0 otherwise (6)

In Reference Generation and Review Composi- tion tasks, we set N as 10, each model generates 10 references. For the generated reference evalu- ation, we use Semantic Scholar as the external database. Recently, LLMs-as-judges has become more common (Chen et al., 2024; Zheng et al., 2023; Shangyu et al., 2024). So, for the Abstract Writing task, we employ TRUE (Honovich et al.,

Entailpi = θNLI(ag

i , ai) =

where θNLI denotes the NLI model. Finally, we obtain the NLI score Entail for each model ac- cording to Eq 7.

M X

Entail = 1

Entailpi (7)

M

i=0

Additionally, we use commonly employed se- mantic similarity metrics and Key Point Recall (KPR) to calculate the semantic coverage between the context generated by LLMs and human-written context. Specifically, for the Abstract Writing task, we apply cosine similarity and the ROUGE metric for semantic coverage evaluation. For the Review Composition task, we use the ROUGE metric and KPR to measure the semantic coverage of the lit- erature review generated by the LLMs relative to human-written content.

2022), along with GPT-4o as NLI models for evalu- ating factual consistency in context; to compute se- mantic similarity, we use text-embedding-3-large to convert texts into embeddings. For the Review Composition task, we employ GPT-4o as the NLI model in Eq 8, and set q as 10.

4.2 Main Results

We present the results for the three tasks in Ta-

ble 1, 2, and 3. The performance of different mod- els on each task is analyzed as follows.

KPR, first proposed by Qi et al. (2024), is a met- ric designed to evaluate the effectiveness of LLMs in utilizing RAG for long documents. Since human- written literature reviews are lengthy and difficult to compare directly, we adopt the KPR method to measure the extent to which LLM-generated con- tent covers the key points in human-written liter- ature reviews. Specifically, we first use GPT-4 to extract q key points Xi = [xi1, xi2, ..., xiq] from the human-written literature review ci, and then calculate the coverage of these key points by the model-generated literature review as Eq. 8.


## Results for Reference Generation. As shown

in Table 1, Claude-3.5-Sonnet achieves the highest
precision, overlap rate, and St, while Llama-3.2-3B
performs the worst on three metrics. When evalu-
ating the author dimension of LLM-generated ref-
erences, we consider the reference to match in this
dimension if the first author is correctly matched.
Applying this criterion results in a 1–3% increase
in precision scores across all models. This suggests
that generating complete and accurate author lists
remains a major challenge for LLMs.

We further conduct a year-wise analysis of the correctly generated references, as illustrated in Fig- ure 2. The results reveal that the majority of accu-

P

x∈Xi θNLI(cg

M X

i , x)

KPR = 1

|Xi| (8)

M

i=0

1606

rate citations produced by the models are concen- trated in the period between 2010 and 2020, a trend consistent across nearly all LLMs evaluated in this task.


## Results for Abstract Writing. As shown in Ta-

ble 2, Claude-3.5-Sonnet achieves the best overall
performance across most evaluation metrics. It
generates abstracts with the highest average se-
mantic similarity to human-written ones (81.17%)
and shows strong factual consistency, achieving a
TRUE score of 78.10%. DeepSeek-V3 also per-
forms well in factual consistency, with the highest
GPT-4o-based assessment score (96.84%). In con-
trast, Llama-3.2-3B obtains the highest ROUGE-L
score but does not show clear advantages on other
metrics. These results highlight the importance of
using multiple evaluation metrics to comprehen-
sively assess the diverse outputs of LLMs.


> **Figure 2: Distribution of LLM-generated true references**

> over years.


## Results for Review Composition. As shown

in Table 3, compared to the Reference Generation
task, all LLMs demonstrate a significant increase
in precision when generating references within the
Review Composition task.
Prior research indi-
cates that grounding generated text with real ex-
ternal citations can effectively reduce hallucina-
tion rates (Gao et al., 2023). Consistently, our
experiments reveal that when LLMs generate refer-
ences alongside the literature review, the accuracy
of these references improves markedly. This sug-
gests a mutual constraint between the generated
references and the review text, leading to enhanced
overall reliability.

(a) Reference Generation (b) Review Composition


> **Figure 3: Radar chart of the accuracy of LLM-generated**

> references across various dimensions.

task. Additionally, the accuracy of reference gener- ation in the Reference Generation task for Claude- 3.5-Sonnet, GPT-4o, and Qwen-2.5-72B follows a consistent trend across all dimensions, with the highest accuracy observed in the title dimension. Accuracy for journal name, page, and author is also relatively high. However, DeepSeek-V3 performs worse in the author dimension compared to the other dimensions. In contrast, Llama-3.2 demon- strates higher accuracy in the page and author di- mensions than in other dimensions. However, over- all, Llama-3.2-3B does not exhibit a competitive advantage in reference generation accuracy.

On the other hand, Claude-3.5-Sonnet achieves the highest performance on the KPR metric, indi- cating that its generated literature reviews recall the greatest number of claims from the human-written versions. Meanwhile, the literature reviews pro- duced by DeepSeek-V3 excel on the ROUGE met- rics, demonstrating stronger overlap with reference texts in terms of lexical similarity.

Next, we examine the accuracy of LLM- generated references across various dimensions in Review Composition, as shown in Figure 3(b), and comparing it with Figure 3(a), we observe improve- ments across all dimensions for Claude-3.5-Sonnet, DeepSeek-V3, GPT-4o, and Qwen-2.5-72B, with particularly obvious gains in the author dimension. The possible reason is that, in the generated text, the LLMs tend to cite the first author’s name, which may lead the models to place more emphasis on this dimension. Notably, the accuracy of DeepSeek- V3 and GPT-4o in certain dimensions approaches or even exceeds that of Claude-3.5-Sonnet. How- ever, the performance of LLaMA-3.2-3B remains

4.3 Analyze LLM-Generated References from Different Dimensions

In both Reference Generation and Review Compo- sition tasks, we ask LLMs to generate references. The overall performance was discussed in the pre- vious section. In this section, we provide a detailed comparison of the accuracy of LLM-generated ref- erences across various dimensions, as shown in Fig- ure 3. As seen in Figure 3(a), Claude-3.5-Sonnet demonstrates a clear advantage over other models across all dimensions in the Reference Generation

1607

Models Reference Generation St↑ P Overlap P (first author) Overlap (first author) Qwen-2.5-72B 21.80 12.25 12.60 17.58 13.27 Llama-3.2-3B 16.62 3.45 8.48 6.95 8.67 DeepSeek-V3 56.04 46.33 19.72 50.66 20.50 GPT-4o 32.07 21.65 18.76 24.65 19.50 Claude-3.5-Sonnet 64.82 51.59 24.34 55.77 25.21


> **Table 1: The experimental results of the five LLMs in Reference Generation. “St” refers to the title search rate as**

> defined in Eq 4, while “P” represents the Precision, “Overlap” denotes the Overlap rate. “first author” refers to
when evaluating the accuracy of references, the author dimension only comparing the first author.

Models Abstract Writing Similarity↑Entail(TRUE)↑Entail(GPT-4o)↑ROUGE-1↑ROUGE-2↑ROUGE-L↑ Qwen-2.5-72B 80.22 69.52 95.02 40.61 8.78 20.12 Llama-3.2-3B 79.28 62.39 92.14 40.35 8.96 20.52 DeepSeek-V3 80.96 78.55 96.84 41.13 8.98 20.33 GPT-4o 80.96 77.91 96.50 40.70 8.56 19.86 Claude-3.5-Sonnet 81.17 78.90 96.77 41.13 8.99 20.00


> **Table 2: Compare the performance of four LLMs on Abstract Writing.**

Review Composition References Literature Review St↑ P Overlap P(first author) Overlap(first author) KPR↑ROUGE-1↑ROUGE-2↑ROUGE-L↑ Qwen-2.5-72B 40.02 28.91 17.36 33.64 18.31 38.82 29.95 9.01 15.14 Llama-3.2-3B 21.78 4.86 8.28 7.28 8.44 29.07 28.07 7.77 15.46 DeepSeek-V3 62.29 52.81 26.79 55.38 27.30 56.02 35.65 10.40 17.46 GPT-4o 60.05 50.62 27.88 54.16 28.86 59.18 30.78 9.72 15.54 Claude-3.5-Sonnet 66.43 59.06 31.90 63.06 33.25 62.32 28.59 8.90 14.41

Models


> **Table 3: The experimental results of the four LLMs in Review Composition. “St” refers to the title retrieval rate**

> as defined in Eq 4. While “P” represents the Precision, “Overlap” denotes the Overlap rate. “KPR” means the
Key Point Recall rate.“first author” refers to when evaluating the accuracy of references, the author dimension only
comparing the first author.

Discipline Citation Count Precision DeepSeek Claude DeepSeek Claude Biology 763 678 55.55 58.00 Mathematics 2288 1984 60.00 62.22 Physics 894 652 47.62 56.19 Chemistry 1334 1079 43.14 43.80 Social Science 1321 1151 46.80 56.70 Technology 904 748 44.88 49.01

various tasks and disciplines.

First, we observe that in the Reference Gen- eration task, as shown in Figure 4(a), almost all models exhibit the highest precision in the Math- ematics discipline and the lowest precision in the Chemistry discipline. To validate these differences, we conduct one-way ANOVA tests for each LLM across five disciplines. Significant differences are found for all models except Llama-3.2-3B. De- tailed ANOVA results are reported in Appendix I.


> **Table 4: Average citation counts and reference precision**

> across disciplines.

suboptimal.

Secondly, as shown in Figure 4(b), the NLI scores evaluated by TRUE in the Abstract Writing task indicate that all models perform the worst in Social Science. GPT-4o performs best in Technol- ogy, while Claude 3.5-Sonnet achieves the highest performance in Biology. One-way ANOVA tests reveal significant differences across disciplines for all models. See Appendix I for detailed results.

4.4 Cross-Disciplinary Analysis

In this section, we compare the performance of LLMs across different disciplines. First, based on Dewey’s Decimal Classification, we categorize 51 journals into six disciplines: Biology, Chemistry, Mathematics, Physics, Social Science, and Technol- ogy. After categorization, there are 460 articles in the Biology category, 90 in Chemistry, 50 in Math- ematics, 113 in Physics, 299 in Social Science, and 94 in Technology. We then present bar charts in Figures 4, which il- lustrate the performance of different models across

Thirdly, we examine the references precision of each model across five disciplines in the Review Composition task, as illustrated in Figure 4(c). It is evident that the precision of Claude 3.5 Sonnet, DeepSeek-V3, and GPT-4o is significantly higher

1608

(a) Reference Generation: Precision ↑ (b) Abstract Writing: NLI scores (TRUE)↑

(c) Review Composition: Precision ↑ (d) Review Composition: KPR scores ↑


> **Figure 4: Three tasks evaluation scores across different disciplines.**

than that of Qwen-2.5-72B and LLaMA-3.2-3B across all disciplines. Furthermore, Claude 3.5 Sonnet, DeepSeek-V3, and Qwen-2.5-72B exhibit the highest precision in Mathematics, while GPT- 4o performs best in Social Science. ANOVA tests confirm significant differences across disciplines for all models (see Appendix I).

has the highest precision, and the relevant refer- ences generated for Mathematics also have the highest citation count. We compute the correla- tion between citation precision and average citation counts, finding that the correlation coefficient for Claude-3.5 is 0.4, and for DeepSeek-V3 it is 0.51, indicating a positive relationship between the two.

Finally, we observe the KPR metric across differ- ent disciplines in Review Composition, as shown in Figure 4(d). The results from the figure indi- cate that the differences between models—Claude- 3.5-Sonnet, DeepSeek-V3, GPT-4o, and Qwen-2.5- 72B—are not significant across various disciplines, a finding that is also supported by statistical tests (see Appendix I).

4.5 Human Evaluation

To evaluate the reliability of our automatic assess- ment method for identifying hallucinated refer- ences, we conduct a comparative analysis involving 100 LLM-generated references. These references were assessed by three annotators and the final man- ual results were obtained by majority vote. The results demonstrated a kappa agreement of 0.71 be- tween the automatic and human assessments, sig- nifying a relatively high level of consistency and supporting the reliability of our method. Further- more, when using human assessment results as the gold standard, the automatic assessment method achieved an accuracy of 86%, further validating its effectiveness.

Citation Frequency and Precision Across Dis- ciplines. Additionally, we report statistics on the citation frequency of correctly generated references by LLMs in the Reference Generation task, as shown in Table 4, using Claude-3.5 and DeepSeek- V3 as examples. The data indicates that the ref- erences generated by the LLMs are highly cited, which might be due to their frequent presence in on- line sources, making them more likely to appear in the LLMs training datasets. As a result, LLMs tend to generate more accurate metadata (e.g., author, year) for these well-known references.

5 Conclusion

In this paper, we present a framework to assess the literature review writing abilities of LLMs. This framework includes three tasks designed to evaluate LLMs’ literature review writing capabil-

Furthermore, when analyzing different disci- plines, we observe that the Mathematics discipline

1609

ities. The generated outputs are then evaluated from multiple dimensions using various tools, such as Semantic Scholar and NLI models, focusing on aspects like hallucination rate, semantic cover- age, and factual consistency compared to human- written texts. Finally, we analyze the performance of LLMs in writing literature reviews from the per- spective of different academic disciplines.

names and journal titles. Although these issues have been carefully addressed (see Appendix F), minor discrepancies may remain.

Finally, to verify the precision of LLM- generated references, we primarily used Semantic Scholar as our auxiliary tool. Although we also experimented with Google Scholar, its lack of an accessible API led us to rely on the freely available Semantic Scholar API for consistency and ease of access. However, this may have resulted in incom- plete reference retrieval.

Limitations

In this paper, we evaluate the ability of LLMs to write literature reviews. However, several limita- tions remain:

Ethics Statement

The human evaluations conducted in this study were carried out by members of the research team. No personal or sensitive information was collected, and all participants were fully informed of the pur- pose of the evaluation. Therefore, the study does not raise any ethical concerns.

First, instead of evaluating the generated reviews from conventional perspectives such as fluency or topic coverage, we primarily compare LLM- generated results with human-written ones. As such, our current evaluation metrics may not be comprehensive. In the future, we plan to incorpo- rate additional aspects of review quality to improve the completeness of our evaluation. These may in- clude the coverage of cited works (i.e., whether the review offers a comprehensive overview of the rele- vant field) and the coherence of the overall structure (i.e., whether the review is organized in a way that facilitates information-seeking).

Acknowledgements

The research was supported by a direct grant from the Faculty of Arts, the Chinese University of Hong Kong. We thank Yicheng Li for his valuable assis- tance with data collection.

Second, there is a possibility that our test data overlaps with the training data of the LLMs. When we initiated this study in August 2024, the dataset from the Annual Reviews website had not yet been updated to include 2024 articles, so we relied on the complete 2023 dataset. To further address potential data contamination, we also conducted an addi- tional evaluation using 2025 data to test GPT-5 (as shown in Appendix E), whose knowledge cutoff is September 2024. To mitigate potential data leakage more broadly, we plan to deploy a leaderboard on Hugging Face to continuously evaluate the perfor- mance of various LLMs in literature review writing, with real-time updates to the test dataset. However, due to the rapid iteration of LLMs, data leakage cannot be completely ruled out. That said, our experimental results—particularly those related to reference generation—show that all models still perform poorly. If data contamination were present, the actual scores would likely be lower than those reported. This reinforces, rather than undermines, our conclusion that significant challenges remain in using LLMs for literature review generation.


## References

Shubham Agarwal, Gaurav Sahu, Abhay Puri, Is-

sam H. Laradji, Krishnamurthy DJ Dvijotham, Ja- son Stanley, Laurent Charlin, and Christopher Pal. 2024. Llms for literature review: Are we there yet? (arXiv:2412.15249). ArXiv:2412.15249 [cs].

Ayush Agrawal, Mirac Suzgun, Lester Mackey, and

Adam Tauman Kalai. 2024. Do language models know when they’re hallucinating references?

Muhammad Bello Aliyu, Rahat Iqbal, and Anne James.

2018. The canonical model of structure for data extraction in systematic reviews of scientific research articles. In 2018 Fifth International Conference on Social Networks Analysis, Management and Security (SNAMS), page 264–271.

Fadi Aljamaan, Mohamad-Hani Temsah, Ibraheem Al-

tamimi, Ayman Al-Eyadhy, Amr Jamal, Khalid Al- hasan, Tamer A. Mesallam, Mohamed Farahat, and Khalid H. Malki. 2024. Reference hallucination score for medical artificial intelligence chatbots: De- velopment and usability study. JMIR Medical In- formatics, 12(1):e54345. Company: JMIR Medical Informatics Distributor: JMIR Medical Informatics Institution: JMIR Medical Informatics Label: JMIR Medical Informatics publisher: JMIR Publications Inc., Toronto, Canada.

Additionally, when processing LLM-generated outputs, we often encountered abbreviated author

1610

Sai Anirudh Athaluri, Sandeep Varma Manthena, V S

Linguistics: EMNLP 2024, page 4852–4872, Miami, Florida, USA. Association for Computational Linguistics.

R Krishna Manoj Kesapragada, Vineel Yarlagadda, Tirth Dave, and Rama Tulasi Siri Duddumpudi. 2023. Exploring the boundaries of reality: Investigating the phenomenon of artificial intelligence hallucination in scientific writing through chatgpt references. Cureus, 15(4):e37432.

Xing Shangyu, Zhao Fei, Wu Zhen, An Tuo, Chen Wei-

hao, Li Chunhui, Zhang Jianbing, and Dai Xinyu. 2024. Efuf: Efficient fine-grained unlearning frame- work for mitigating hallucinations in multimodal large language models. page 1167–1181.

Mikaël Chelli, Jules Descamps, Vincent Lavoué,

Christophe Trojani, Michel Azar, Marcel Deckert, Jean-Luc Raynier, Gilles Clowez, Pascal Boileau, and Caroline Ruetsch-Chelli. 2024. Hallucination rates and reference accuracy of chatgpt and bard for systematic reviews: Comparative analysis. Journal of Medical Internet Research, 26:e53164.

Jiyao Wang, Haolong Hu, Zuyuan Wang, Song Yan,

Youyu Sheng, and Dengbo He. 2024a. Evaluating

large language models on academic literature un- derstanding and review: An empirical study among early-stage scholars. In Proceedings of the CHI Con- ference on Human Factors in Computing Systems, page 1–18, Honolulu HI USA. ACM.

Guiming Hardy Chen, Shunian Chen, Ziche Liu,

Feng Jiang, and Benyou Wang. 2024. Humans or llms as the judge? a study on judgement biases. (arXiv:2402.10669). ArXiv:2402.10669 [cs].

Yidong Wang, Qi Guo, Wenjin Yao, Hongbo Zhang,

Xin Zhang, Zhen Wu, Meishan Zhang, Xinyu Dai, Min Zhang, Qingsong Wen, Wei Ye, Shikun Zhang, and Yue Zhang. 2024b. Autosurvey: Large language models can automatically write surveys. (arXiv:2406.10252). ArXiv:2406.10252.

Tianyu Gao, Howard Yen, Jiatong Yu, and Danqi

Chen. 2023. Enabling large language models to generate text with citations. (arXiv:2305.14627). ArXiv:2305.14627 [cs].

Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Siyuan

Zhuang, Zhanghao Wu, Yonghao Zhuang, Zi Lin, Zhuohan Li, Dacheng Li, Eric P. Xing, Hao Zhang, Joseph E. Gonzalez, and Ion Stoica. 2023. Judg- ing llm-as-a-judge with mt-bench and chatbot arena. (arXiv:2306.05685). ArXiv:2306.05685 [cs].

Or Honovich, Roee Aharoni, Jonathan Herzig, Hagai

Taitelbaum, Doron Kukliansy, Vered Cohen, Thomas Scialom, Idan Szpektor, Avinatan Hassidim, and Yossi Matias. 2022. TRUE: Re-evaluating factual

consistency evaluation. In Proceedings of the 2022 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, pages 3905–3920, Seattle, United States. Association for Computational Lin- guistics.

Chao-Chun Hsu, Erin Bransom, Jenna Sparks, Bailey

Kuehl, Chenhao Tan, David Wadden, Lucy Wang, and Aakanksha Naik. 2024. CHIME: LLM-assisted hierarchical organization of scientific studies for liter- ature review support. In Findings of the Association for Computational Linguistics: ACL 2024, pages 118–132, Bangkok, Thailand. Association for Com- putational Linguistics.

Georgios Kontonatsios, Sally Spencer, Peter Matthew,

and Ioannis Korkontzelos. 2020. Using a neural network-based feature extraction method to facili- tate citation screening for systematic reviews. Expert Systems with Applications: X, 6:100030.

Xun Liang, Jiawei Yang, Yezhaohui Wang, Chen Tang,

Zifan Zheng, Shichao Song, Zehao Lin, Yebin Yang, Simin Niu, Hanyu Wang, Bo Tang, Feiyu Xiong, Keming Mao, and Zhiyu li. 2025. Surveyx: Aca- demic survey automation via large language models. (arXiv:2502.14776). ArXiv:2502.14776 [cs].

Zehan Qi, Rongwu Xu, Zhijiang Guo, Cunx- iang Wang, Hao Zhang, and Wei Xu. 2024. Long2rag : Evaluatinglong − contextlong − formretrieval − augmentedgenerationwithkeypointrecall. In Findings of the Association for Computational

1611

A Prompts for Tasks

Prompt Content Prompt 1 Imagine you are an experienced academic researcher with access to a vast library of scientific literature. I would like you to find the 10 studies that are most relevant to the research topic provided in the "Title" and the "Keywords" below. Please cite the studies according to the following JSON format. There is no need to provide any explanation before or after the JSON output. Ensure that the "authors" field lists the names of all authors and not exceeding 10 authors, and that there are no duplicate author names nor abbreviations such as "et al.". { "References": [ { "title": "", "authors": "", "journal": "", "year": "", "volumes": "", "first page": "", "last page": "", } ] } Title: title Keywords: keywords Prompt 2 Imagine you are an experienced academic researcher with access to a vast library of scientific literature. I would like you to write an abstract according to the research topic provided in the "Title" and the "Keywords" below. Please write the abstract for about xx words, according to the JSON format as follows. There is no need to provide any explanation before or after the JSON output. {"Abstract": ""}

Title: title Keywords: keywords Prompt 3 Imagine you are an experienced academic researcher with access to a vast library of scientific literature. I would like you to write a literature review according to the research topic provided in the "Title", “Abstract” and "Keywords" below. The literature review should be about 1000 words long. I would like you to back up claims by citing previous studies (with a total of 10 citations in the literature review). The output should be in JSON format as follows: { "Literature Review": "xxx", "References": [ { "title": "", "authors": "", "journal": "", "year": "", "volumes": "", "first page": "", "last page": "", } ] } The "Literature Review" field should be about 1000 words. The "References" field is a list of 10 references, and ensures that the "authors" field lists the names of all authors and not exceeding 10 authors, and that there are no duplicate author names nor abbreviations such as "et al.". Title: title Keywords: keywords Abstract: abstract


> **Table 5: Prompts for tasks.**


> **Figure 5: Statistics of dataset.**

1612

B Data Distribution

When comparing the references generated by the models in Reference Generation and Review Composition, we find that in Review Composition, nearly all models generate more accurate refer- ences. This suggests that LLMs cite references during the writing process, which improves the authenticity of the references. Moreover, the in- clusion of the first author’s name in the generated context also enhances the accuracy of the author dimension.

Statistics of the dataset are shown in Figure 5.

C Comparison of LLM-Cited and Human-cited References from Different Dimensions

We provide a more detailed comparison of the

LLM-cited and human-cited references across vari- ous dimensions. As shown in Figure 6, for Refer- ence Generation, we observe that the overlap rate is higher in the “Title” and other numerical dimen- sions, while the overlap rates for the “Journal” and “Author” dimensions are relatively lower. For Re-

E Mitigating Potential Data Contamination

To address potential data contamination, we up- dated the dataset by crawling articles from the An- nual Reviews website between January 1, 2025, and August 13, 2025, resulting in a total of 651 articles. Based on these newly collected articles, we evaluate gpt-5-2025-08-07 (knowledge cutoff: September 2024) on three tasks. The experimental results are presented in Table 6, 7, and 8. The results indicate that even GPT-5 exhibits a substan- tial hallucination rate when generating references, further confirming that large language models con- tinue to face significant challenges in literature gen- eration tasks.

view Composition, Claude-3.5-Sonnet and GPT-4o exhibit a higher overlap rate on the “Author” di- mension compared to Reference Generation. This trend is consistent with the findings in Figure 6, as the citation of author names in the literature for Re- view Composition leads to the generation of more accurate author information.

F Data Processing Strategy

Author name and journal title variations often pose challenges when aligning LLM-generated refer- ences with articles from Semantic Scholar. To ad- dress this, we adopt the following normalization strategies:

(a) Task1 (b) Task3


> **Figure 6: Radar chart of the accuracy of LLM-generated**

> references with human-written references in the original
article.

Author names. When comparing author names between LLM-generated references and candidate articles, if an exact match is not found (e.g., “John Smith”), we consider common variants such as “Smith, John”, “Smith, J.”, or “J. Smith” to account

D Discussion

We select five LLMs for task evaluation and find

that Claude-3.5-Sonnet outperforms DeepSeek-V3, GPT-4o, Qwen-2.5-72B, and Llama-3.2-3B across all three tasks, particularly excelling in the task of generating accurate references. This advantage is likely influenced by the training data of each model. Additionally, we observed that each model has different strengths across disciplines. Over- all, for the reference generation task, nearly all models perform better in Mathematics, while their performance is weaker in Chemistry and Technol- ogy. However, when writing abstracts, all models exhibit the lowest factual consistency in Social Sci- ence, as indicated by the entailment scores, com- pared to human-written texts.

for different citation formats.

Journal titles. For journal names like Journal of Chemical Physics, we incorporate standard ab- breviation forms (e.g., J. Chem. Phys.) based on widely used abbreviation conventions. Nonethe- less, certain non-standard or ambiguous cases may still be unmatched.

G Significance Testing for Abstract Writing Metrics

We conduct statistical significance tests to rigor-

ously examine whether ROUGE and similarity met-

1613

Models Reference Generation St↑ P Overlap P(first author) Overlap(first author) GPT-5 26.91 20.62 19.88 21.79 19.75


> **Table 6: The experimental results of the GPT-5 in Reference Generation.**

Models Abstract Writing Similarity↑Entail(TRUE)↑Entail(GPT-4o)↑ROUGE-1↑ROUGE-2↑ROUGE-L↑ GPT-5 74.13 79.82 81.65 30.55 4.77 14.92


> **Table 7: The performance of GPT-5 on Abstract Writing.**

Review Composition References Literature Review St↑ P Overlap P(first author) Overlap(first author) KPR↑ROUGE-1↑ROUGE-2↑ROUGE-L↑ GPT-5 40.92 26.38 20.36 29.72 20.93 80.80 19.42 4.88 9.19

Models


> **Table 8: The experimental results of the GPT-5 in Review Composition.**

rics can meaningfully differentiate model perfor- mance in Abstract Writing.

of these metrics for evaluating abstract writing per- formance across LLMs.

We apply the Friedman test followed by Ne- menyi post-hoc comparisons on four automatic metrics (ROUGE-1, ROUGE-2, ROUGE-L, and similarity) across five LLMs (GPT-4o, Claude, Qwen, LLaMA, and Deepseek).

H LLM Output Example

Here is one example of the output generated by Claude-3.5-Sonnet for the literature review compo- sition task.

The results demonstrate that all four metrics re- veal statistically significant differences across mod- els (p < 0.001 for all Friedman tests).

{"Literature Review": "CRISPR-Cas systems have emerged as a powerful tool in the field of biosensing, offering unprecedented capabilities for detecting nucleic acids, proteins, and small molecules. This review explores the technical de- velopments and application prospects of CRISPR- based biosensing strategies, highlighting their po- tential to revolutionize diagnostics and molecu- lar detection.The core biochemical properties of CRISPR-Cas systems provide the foundation for their application in biosensing. These proper- ties include diverse reaction temperatures, pro- grammability in design, high reaction efficiency, and recognition specificity. Chen et al. (2018) demonstrated the versatility of CRISPR-Cas9 in detecting DNA targets across a wide temperature range, from 20°C to 60°C, enabling its use in var- ious environmental conditions. The programma- bility of CRISPR systems allows for the easy de- sign of guide RNAs (gRNAs) to target specific se- quences, as shown by Gootenberg et al. (2017) in their development of the SHERLOCK (Specific High-sensitivity Enzymatic Reporter unLOCKing) platform for nucleic acid detection.The high reac- tion efficiency of CRISPR-Cas systems contributes to their sensitivity in biosensing applications. Li et al. (2019) reported a CRISPR-Cas12a-based assay capable of detecting attomolar concentrations of DNA targets, demonstrating the potential for ultra-

• GPT-4o consistently outperforms other mod- els on all metrics, with significant pairwise differences (e.g., p < 0.01 vs. Claude and Qwen).

• Claude, despite relatively high average scores, exhibits larger variance and does not differ significantly from Qwen or LLaMA in some comparisons.

• The similarity metric effectively differenti- ates GPT-4o and Claude from the remain- ing models (p < 1e-12 vs. Qwen, LLaMA, and Deepseek), confirming its discriminative power.

These results confirm that ROUGE and similar- ity scores can capture meaningful and statistically significant differences in model performance, be- yond what is apparent from mean values alone.

Tables 9–12 present the pairwise significance test results (p-values) for each metric using the Nemenyi test.

These results confirm that the differences in ROUGE and similarity metrics are statistically meaningful, validating the discriminative power

1614

GPT-4o Claude Qwen LLaMA Deepseek GPT-4o 1.0000 0.0200 0.9888 0.5536 0.0033 Claude 0.0200 1.0000 0.0039 0.0001 0.9849 Qwen 0.9888 0.0039 1.0000 0.8419 0.0005 LLaMA 0.5536 0.0001 0.8419 1.0000 0.0000 Deepseek 0.0033 0.9849 0.0005 0.0000 1.0000


> **Table 9: Pairwise significance test (p-values) for ROUGE-1 scores across five models using Nemenyi test.**

GPT-4o Claude Qwen LLaMA Deepseek GPT-4o 1.0000 0.0000 0.0246 0.0000 0.0000 Claude 0.0000 1.0000 0.2415 0.9998 0.9963 Qwen 0.0246 0.2415 1.0000 0.3225 0.4411 LLaMA 0.0000 0.9998 0.3225 1.0000 0.9996 Deepseek 0.0000 0.9963 0.4411 0.9996 1.0000


> **Table 10: Pairwise significance test (p-values) for ROUGE-2 scores across five models using Nemenyi test.**

GPT-4o Claude Qwen LLaMA Deepseek GPT-4o 1.0000 0.1650 0.0089 4.22e-15 2.29e-10 Claude 0.1650 1.0000 0.8322 3.80e-08 8.54e-05 Qwen 0.0089 0.8322 1.0000 1.26e-05 0.0061 LLaMA 4.22e-15 3.80e-08 1.26e-05 1.0000 0.5980 Deepseek 2.29e-10 8.54e-05 0.0061 0.5980 1.0000


> **Table 11: Pairwise significance test (p-values) for ROUGE-L scores across five models using Nemenyi test.**

GPT-4o Claude Qwen LLaMA Deepseek GPT-4o 1.0 0.9156 4.88e-14 0.0 0.9783 Claude 0.9156 1.0 1.11e-16 0.0 0.6107 Qwen 4.88e-14 1.11e-16 1.0 3.87e-11 4.12e-12 LLaMA 0.0 0.0 3.87e-11 1.0 0.0 Deepseek 0.9783 0.6107 4.12e-12 0.0 1.0


> **Table 12: Pairwise significance test (p-values) for Similarity scores across five models using Nemenyi test.**

sensitive detection. The recognition specificity of CRISPR systems allows for precise discrimination between closely related sequences, as evidenced by the work of Myhrvold et al. (2018), who devel- oped a CRISPR-based diagnostic platform capable of distinguishing between Zika and Dengue virus strains with single-base resolution.Recent efforts have focused on improving these core properties to enhance the performance of CRISPR-based biosen- sors. For example, Harrington et al. (2018) en- gineered Cas12a variants with improved activity and specificity, expanding the range of targetable sequences and reducing off-target effects. Similarly, Gootenberg et al. (2018) developed an enhanced version of the SHERLOCK system, incorporating

lateral flow readouts and multiplexing capabili- ties, further improving its utility in point-of-care diagnostics.One of the key areas of technical devel- opment in CRISPR-based biosensing is improving sensitivity and quantification capabilities. Wang et al. (2020) introduced a CRISPR-Cas12a-based digital PCR method that achieved attomolar sen- sitivity and precise quantification of target nucleic acids. This approach combines the specificity of CRISPR recognition with the quantitative power of digital PCR, opening new avenues for highly sensi- tive and accurate molecular diagnostics.Multiplex detection is another important aspect of CRISPR biosensing development. Ackerman et al. (2020) demonstrated a CRISPR-Cas13-based multiplexed

1615

assay capable of simultaneously detecting and dis- tinguishing multiple SARS-CoV-2 variants, show- casing the potential of CRISPR technology in rapid and accurate pathogen identification. The abil- ity to detect multiple targets in a single reaction not only saves time and resources but also provides more comprehensive diagnostic information.Efforts to develop convenient one-pot assays have led to simplified and more user-friendly CRISPR-based detection methods. Joung et al. (2020) reported a one-pot, CRISPR-Cas12-based assay for SARS- CoV-2 detection that could be performed at a sin- gle temperature, eliminating the need for complex thermal cycling equipment. This advancement brings CRISPR-based diagnostics closer to point- of-care applications, where simplicity and ease of use are crucial.The creation of advanced sensors has further expanded the capabilities of CRISPR- based biosensing. Bruch et al. (2019) developed a CRISPR-Cas13a-based electrochemical sensor for nucleic acid detection, demonstrating the potential for integrating CRISPR technology with electronic readout systems. This approach offers the possi- bility of developing portable, electronic CRISPR- based diagnostic devices for rapid and sensitive de- tection in resource-limited settings.While CRISPR- based biosensing has shown great promise, there are still obstacles to its widespread commercial application. These include challenges in sample preparation, the need for standardization across different CRISPR systems and assay formats, and regulatory considerations for diagnostic use. Ad- dressing these issues will be crucial for the suc- cessful translation of CRISPR biosensing technol- ogy from the laboratory to real-world applica- tions.Looking ahead, the future of CRISPR-based biosensing appears bright, with numerous op- portunities for further development and applica- tion. Potential directions include the integration of CRISPR biosensors with microfluidic devices for automated sample processing and analysis, the development of CRISPR-based wearable sensors for continuous health monitoring, and the appli- cation of machine learning algorithms to improve the design and performance of CRISPR biosensing systems.In conclusion, CRISPR-based biosensing strategies represent a rapidly evolving field with immense potential to transform molecular detec- tion and diagnostics. As researchers continue to refine and expand upon the core capabilities of CRISPR systems, we can expect to see increasingly sensitive, specific, and versatile biosensing ap-

plications emerge, with far-reaching implications for healthcare, environmental monitoring, and be- yond.", "References": [{"title": "CRISPR–Cas12a target binding unleashes indiscriminate single- stranded DNase activity", "authors": "Chen, Jan- ice S., Ma, Enbo, Harrington, Lucas B., Da Costa, Maria, Tian, Xiang, Palefsky, Joel M., Doudna, Jennifer A.", "journal": "Science", "year": "2018", "volumes": "360", "first page": "436", "last page": "439"},{"title": "Nucleic acid de- tection with CRISPR-Cas13a/C2c2", "authors": "Gootenberg, Jonathan S., Abudayyeh, Omar O., Lee, Jeong Wook, Essletzbichler, Patrick, Dy, Aaron J., Joung, Julia, Verdine, Vanessa, Donghia, Nina, Daringer, Nichole M., Freije, Catherine A.", "journal": "Science", "year": "2017", "vol-

umes": "356", "first page": "438", "last page": "442", "DOI": "10.1126/science.aam9321"}, {"ti- tle": "CRISPR-Cas12a-assisted nucleic acid de- tection", "authors": "Li, Suwei, Cheng, Qingmei, Wang, Jianming, Li, Xiaoyu, Zhang, Zhiwei, Gao,

Shan, Cao, Rong, Zhao, Guoping, Wang, Jin", "journal": "Cell Discovery", "year": "2019", "vol- umes": "5", "first page": "1", "last page": "4"}, {"title": "Field-deployable viral diagnostics using

CRISPR-Cas13", "authors": "Myhrvold, Cameron, Freije, Catherine A., Gootenberg, Jonathan S., Abu-

dayyeh, Omar O., Metsky, Hayden C., Durbin, Ann F., Kellner, Max J., Tan, Amanda L., Paul, Lau-

ren M., Parham, Leda A.", "journal": "Science", "year": "2018", "volumes": "360", "first page": "444", "last page": "448"}, {"title": "Enhanced proofreading governs CRISPR–Cas9 targeting ac- curacy", "authors": "Harrington, Lucas B., Paez- Espino, David, Staahl, Brett T., Chen, Janice S., Ma, Enbo, Kyrpides, Nikos C., Doudna, Jennifer A.", "journal": "Nature", "year": "2018", "vol-

umes": "563", "first page": "621", "last page": "625"}, {"title": "Multiplexed and portable nu- cleic acid detection platform with Cas13, Cas12a, and Csm6", "authors": "Gootenberg, Jonathan S., Abudayyeh, Omar O., Kellner, Max J., Joung, Ju-

lia, Collins, James J., Zhang, Feng", "journal": "Science", "year": "2018", "volumes": "360", "first page": "439", "last page": "444"}, {"ti- tle": "Ultrasensitive and visual detection of SARS- CoV-2 using all-in-one dual CRISPR-Cas12a as- say", "authors": "Wang, Xiaoxia, Zhong, Minjie, Liu, Yue, Ma, Pengfei, Dang, Lei, Meng, Qing, Wan, Wanying, Ma, Xiaowei, Liu, Jing, Yang,

Guohua", "journal": "Nature Communications", "year": "2020", "volumes": "11", "first page":

1616

"4711", "last page": "4711"}, {"title": "Detection of SARS-CoV-2 with SHERLOCK One-Pot Test- ing", "authors": "Joung, Julia, Ladha, Alim, Saito, Makoto, Kim, Nam-Gyun, Woolley, Ann E., Segel, Michael, Barretto, Robert P. J., Ranu, Antonija, Macrae, Rhiannon K., Faure, Guilhem", "jour- nal": "New England Journal of Medicine", "year": "2020", "volumes": "383", "first page": "1492", "last page": "1494"}, {"title": "CRISPR-Cas13- based electrochemical biosensing of viral RNA: Ap- plication to detection of SARS-CoV-2", "authors": "Bruch, Richard, Baaske, Johannes, Chatelle, Claire, Meirich, Maren, Madlener, Sibylle, We- ber, Wilfried, Dincer, Can, Urban, Gerald A.", "journal": "Angewandte Chemie International Edi- tion", "year": "2019", "volumes": "58", "first page": "17571", "last page": "17575"}, {"ti- tle": "Scalable and robust SARS-CoV-2 testing in an academic center", "authors": "Ackerman, Cheri M., Myhrvold, Cameron, Thakku, Shiv G., Freije, Catherine A., Metsky, Hayden C., Yang, David K., Ye, Simon H., Boehm, Chloe K., Kosoko- Thoroddsen, Tinna-Solveig F., Kehe, Jared", "jour-

nal": "Nature Biotechnology", "year": "2020", "volumes": "38", "first page": "927", "last page": "931"}]}

I ANOVA Test Results

We report the p-values from one-way ANOVA tests

across disciplines for each model and task:

• Reference Generation task: Claude-3.5- Sonnet (p<.0001), DeepSeek-V3(p<.0001), GPT-4o(p<.0001), Qwen-2.5-72B (p<.0001), Llama-3.2-3B (p=0.065).

• Abstract Writing task (NLI scores): Claude- 3.5-Sonnet(p<.0001), DeepSeek-V3(p<0.05), GPT-4o(p<.01), Qwen2.5-72B (p<.001), Llama-3.2-3B (p<.0001).

• Review Composition (Reference accuracy): Claude-3.5-Sonnet(p<.0001), DeepSeek- V3(p<.0001), GPT-4o(p<.0001), Qwen-2.5- 72B(p<.0001), Llama-3.2-3B(p<.001).

• Review Composition (KPR metric): Claude- 3.5-Sonnet (p=0.46), DeepSeek-V3 (p=0.23), GPT-4o (p=0.18), Qwen-2.5-72B (p=0.10), and Llama-3.2-3B (p<0.001).

1617
