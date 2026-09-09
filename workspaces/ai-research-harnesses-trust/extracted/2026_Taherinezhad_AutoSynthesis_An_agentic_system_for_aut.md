---
workspace_id: "SCI-000135"
doi: null
title: "AutoSynthesis: An agentic system for automated meta-analysis"
year: 2026
extraction_engine: "pymupdf"
---
# 2026 Taherinezhad AutoSynthesis An agentic system for aut

AUTOSYNTHESIS: An agentic system for automated

meta-analysis

Moein Taherinezhad1, Sebastian Maier2,3, Gerardo Vitagliano4, Francesco

Pierri†1, and Stefan Feuerriegel†2,3

1Politecnico di Milano

2LMU Munich, Munich, Germany

arXiv:2607.15247v1  [cs.AI]  16 Jul 2026

3Munich Center for Machine Learning, Munich, Germany

4MIT CSAIL

†Joint supervision and corresponding authors: francesco.pierri@polimi.it, feuerriegel@lmu.de

1


## Abstract

Evidence synthesis is crucial for turning primary research into reliable knowledge for science,

medicine, education, and policy. Yet, quantitative evidence synthesis remains largely manual

and difficult to scale. Here, we introduce AUTOSYNTHESIS, an end-to-end multi-agent sys-

tem for automated meta-analysis. Given a research question in natural language, AUTOSYN-

THESIS formulates a search strategy, retrieves scientific literature, screens candidate studies,

assesses full-text eligibility, extracts quantitative statistics, computes standardized effect sizes,

and finally performs random-effects meta-analysis. AUTOSYNTHESIS further supports het-

erogeneity analysis to examine how effect sizes vary across moderators, as well as risk-of-bias

assessment. As output, AUTOSYNTHESIS produces a transparent report aligned with PRISMA

guidelines. In our application, AUTOSYNTHESIS screened over 28 studies and extracted more

than 20 quantitative claims. The pooled effect estimates produced by AUTOSYNTHESIS are

similar to Hedges’ g of expert-conducted meta-analyses, indicating close agreement with man-

ual evidence synthesis. Together, these results show that AUTOSYNTHESIS can make quan-

titative evidence synthesis more scalable, thereby supporting evidence-based decision-making

across disciplines.

1 Introduction

Systematic meta-analyses play a central role in evidence-based research by synthesizing findings

from multiple independent studies into quantitative conclusions [1, 2]. By integrating evidence

across diverse studies, they increase statistical power, improve the precision of effect estimates,

and enable researchers to identify sources of heterogeneity that may not be apparent in individual

studies. As a result, meta-analyses are used widely across disciplines, including clinical medicine

(e.g., for developing evidence-based treatment guidelines [3]), psychology (e.g. for evaluating

behavioral and mental health interventions [4–6]), education (e.g., for assessing the effectiveness

of learning interventions [7–9]), public health (e.g., for informing health policy and preventive

interventions [10,11]), and computer science (e.g., for synthesizing the effect of human–computer

interaction technologies on user behavior [12]). Meta-analyses therefore play an important role in

building the evidence base to inform policy decisions.

However, producing a high-quality meta-analysis is a manual process that is expensive and

time-consuming. A typical meta-analysis requires extensive effort to formulate search strategies,

retrieve literature from multiple databases, screen hundreds or thousands of candidate studies,

assess eligibility, extract quantitative data, compute standardized effect sizes, perform statistical

synthesis, and prepare reporting according to guidelines such as PRISMA [2]. Previous studies

estimate that the systematic review alone often requires more than one thousand person-hours and

may take more than a year to complete [13,14], creating a substantial lag between the publication

of primary studies and the availability of synthesized evidence. Here, we present an agentic frame-

work for automatic meta-analysis to synthesize evidence in a reproducible, scalable, near real-time

manner.

Recent advances in large language models (LLMs) have substantially expanded the scope of

AI-assisted scientific research. Owing to their ability to reason over unstructured scientific doc-

uments, generate executable code, and synthesize information across diverse sources [15], LLMs

3

have recently been applied to a wide range of scientific workflows, including hypothesis genera-

tion, scientific discovery, software engineering, automated reproducibility assessments, and data

analysis [16–18]. Existing research on LLM-assisted evidence synthesis broadly falls into two cat-

egories. The first uses LLMs for literature retrieval, screening, and eligibility assessment, in order

to identify studies and research questions relevant to a user query. [19–21]. The second uses LLMs

for structured information extraction, such as extracting the outcomes or other measures [22–27].

Some of these systems can even perform systematic reviews [28]. In contrast, end-to-end sys-

tems that move beyond screening and extraction to compute standardized effect sizes and perform

complete statistical meta-analysis remain missing.

In this paper, we present AUTOSYNTHESIS, an end-to-end multi-agent system for automated

meta-analysis (Fig. 1). AUTOSYNTHESIS takes a research question in natural language as input.

Then, AUTOSYNTHESIS autonomously formulates a search strategy, retrieves the literature from

dedicated scientific databases, screens the retrieved papers, assesses the eligibility based on the

full text, extracts quantitative data (in addition to study metadata), computes standardized effect

sizes (such as Cohen’s d and Hedges’ g), and performs a random-effects meta-analysis. As part of

this workflow, AUTOSYNTHESIS estimates and reports between-study heterogeneity using stan-

dard statistics such as I2 and τ 2. When specified by the user, AUTOSYNTHESIS can also perform

heterogeneity analysis to understand how the effect sizes vary across different moderators of inter-

est. In addition, AUTOSYNTHESIS conducts a principled reporting bias assessment according to

the best practice (e.g., trim-and-fill [29] procedure, checks for small-study effects such as through

funnel plot analyses [30] to test for potential publication bias), as well as a risk of bias in in-

cluded studies analysis (e.g., RoB 2 for randomized trials [31] and ROBINS-I for non-randomized

studies of interventions [32]). The output is a complete report following PRISMA guidelines [2].

For this, AUTOSYNTHESIS combines several specialized LLM agents within a rigorous statistical

workflow to support complex reasoning over scientific evidence. AUTOSYNTHESIS records the

complete agent traces and intermediate decisions during the workflow, which enables end-users

4

to inspect and audit each step of the evidence synthesis process (e.g., by inspecting the reasons

for inclusion/exclusion of a specific study). In sum, AUTOSYNTHESIS provides a transparent,

reproducible, and scalable approach for evidence synthesis.

We demonstrate the capabilities of AUTOSYNTHESIS by performing several automated meta-

analyses across different scientific domains, including human–AI interaction, education, and psy-

chology. To benchmark automated evidence synthesis, we compare the results produced by AU-

TOSYNTHESIS against established expert-conducted meta-analyses used as reference cases [7,12].

Across these applications, AUTOSYNTHESIS retrieved 28 candidate records, screened 19 papers

for inclusion, and extracted quantitative evidence from 8 eligible studies. We empirically assess

performance across multiple stages of the evidence synthesis process, including the overlap with

expert-conducted reviews in literature retrieval and research questions selection, the accuracy of

quantitative data extraction, and the agreement of the final effect sizes. Across all reference cases,

the pooled effect estimates produced by AUTOSYNTHESIS were within ±0.12 Hedges’ g of the

corresponding expert-conducted meta-analyses, indicating strong agreement with manual evidence

synthesis across domains.

More broadly, automated meta-analysis through AUTOSYNTHESIS can expand how quanti-

tative evidence synthesis is produced and used. First, AUTOSYNTHESIS can make meta-analysis

cheaper and more scalable, lowering the barrier to quantitative evidence synthesis in settings where

manual evidence synthesis would be too costly or time-consuming, thereby promoting evidence-

based decision-making at scale in placed that would otherwise be guided by ad hoc judgment. Sec-

ond, AUTOSYNTHESIS may enable near-real-time synthesis of evidence. In this way, it extends

the idea of “living” systematic reviews [33] to “living” meta-analyses, which can continuously

integrate new evidence as studies appear. Third, automated workflows can make it easier to con-

sistently apply established best practices (e.g., such as risk-of-bias assessment [3] and PRISMA-

aligned reporting [2]). Hence, AUTOSYNTHESIS may help improve methodological rigor, espe-

cially for researchers without specialized expertise in meta-analysis. Together, these capabilities

5

can support evidence-based decision-making in areas where timely and reliable summaries of the

literature are needed, including clinical practice, education, and public policy [34].

a b c d

Planning and literature retrieval

Eligibility and study mapping

Analysis and report preparation

Statistical extraction and validation

Turns the user's research question into a structured plan, control labels, inclusion/exclusion criteria, and moderators

Computes Hedges' g and Cohen's d per study from whatever statistics are available.

Fetches PDF full text; papers with no full text, or irrelevant ones, are excluded.

Extracts numerical statistics from each paper

Planning agent

Statistical result extractor agent

Paper reading agent

Analysis agent

Rephrasing the user query and looking for papers on the Web

Verifies each extracted row against the paper text

Detects publication bias and classifies bias risk

Filters papers by full-text eligibility

Query reformulation

Eligibility agent

Statistical result checker agent

Bias agent

Queries databases per plan query, dedupes by title.

Detects the independent studies/RQs

Selects the most relevant outcome for each study; dropping redundant ones

Writes the final PRISMA compliant Markdown report covering all results

Research question identification agent

Automatic search agent

Relevance filter agent

Report agent


> **Figure 1: Overview of the AUTOSYNTHESIS framework. A multi-agent framework includ-**

> ing: a, The workflow begins by transforming the user’s research question into a structured review
protocol and retrieving candidate studies from multiple scientific databases using LLM-generated
search queries. b, Retrieved articles undergo full-text retrieval, eligibility assessment, and study
mapping, where independent studies and research questions are identified within each paper. c,
Statistical evidence is extracted, validated against the source article, and filtered to retain only the
results relevant to the target meta-analysis before being standardized into a common representa-
tion. d, Standardized effect sizes are synthesized using a random-effects meta-analysis, followed
by publication-bias assessment and automatic generation of a PRISMA-compliant report together
with visualizations and complete audit records. The modular architecture enables every stage of
the evidence-synthesis process to be independently inspected, verified, and compared with expert-
conducted meta-analysis.

2 Results

2.1 AUTOSYNTHESIS can perform an end-to-end meta-analysis

To demonstrate the capabilities of AUTOSYNTHESIS, we tasked the system with a meta-analytic

research question on whether LLMs are more persuasive than humans. Evidence for this research

question is contested [35–38], but increasingly relevant in light of ongoing debates about the per-

suasive power of generative AI with implications for psychology, communication, and society. A

6

recent meta-analysis by Hölbling et al. (2025) [12] provides a useful reference point (k = 11

effect sizes, 17,422 participants, which allows us to later compare the automated synthesis from

AUTOSYNTHESIS against a human benchmark.

The input to AUTOSYNTHESIS was the following research question (see Fig. 2a): “What is

the effect of large language model (LLM)-generated persuasive messages on persuasive outcomes

compared with non-LLM or human-authored control messages?” We did not specify a start or end

date for exclusion. Using this input, AUTOSYNTHESIS performed a complete evidence synthe-

sis: AUTOSYNTHESIS first produced a structured review protocol, retrieved and screened eligible

studies, extracted statistical results, computed standardized effect sizes, and performed a random-

effects meta-analysis. The final output is a structured report, which includes a PRISMA 2020

flow diagram, a forest plot, the pooled meta-analytic effect estimate in terms of Hedges’ g with

accompanying statistics (e.g., such as I2, τ 2, and Cochran’s Q), a funnel plot for publication bias

diagnostics, and risk-of-bias assessments (Fig. 2b–i). In addition, AUTOSYNTHESIS produces a

narrative Markdown report and a study-level overview table summarizing the included studies,

relevant metadata, and the extracted effect sizes (see Supplementary Table S4).

For this research question, AUTOSYNTHESIS retrieved 28 candidate records, retained 25 after

title and abstract screening, identified 19 eligible studies based on the full text, and ultimately in-

cluded 8 studies with overall k = 20 effect size estimates (Fig. 2b). The resulting random-effects

meta-analysis estimated a pooled effect of Hedges’ g = 0.143 (95% CI [0.059, 0.226], p < 0.001;

Fig. 2c), which suggests that LLM-generated persuasive messages were, on average, more persua-

sive than the control conditions. At the same time, the analysis indicated substantial between-study

heterogeneity (I2 = 88.3%; Fig. 2h). Additional diagnostics generated by AUTOSYNTHESIS sup-

ported this interpretation: the funnel plot indicated potential small-study effects (Fig. 2d). To

better inspect small-study effects, AUTOSYNTHESIS also produced plots comparing the effect size

against sample size to show how study-level estimates relate to statistical power (Fig. 2e). A leave-

one-out sensitivity analysis further confirms that the overall pooled effect remained largely robust

7

to the exclusion of an individual study (Fig. S1). Further, AUTOSYNTHESIS produced a cumula-

tive meta-analysis showing how the pooled estimate evolved as evidence accumulated over time

Fig. 2f). This provides insights into how the persuasive power of LLMs increased as the LLM

capabilities improved over different years. Moderator analysis further showed that effect sizes dif-

fered across application domains (Fig. 2g). Finally, the risk-of-bias assessment highlighted that

some studies may require cautious interpretation, for example, because of small samples or design

limitations (Fig. 2i).

8

a

What is the effect of large language model (LLM)-generated persuasive messages on persuasive outcomes compared with non-LLM or human-authored control messages?

PRISMA flow diagram b

e

Pooled Hedges' g = 0.143 d

0.00

Identification of studies via databases and registers

Pooled Hedges' g = 0.143

Identification Screening Included

0.02

0.4

Records removed before screening:     Duplicate records removed (n = 0)

Records identified from:    AI web search (n = 28)

0.6

Total (n = 28)

0.04

0.4

Effect size (Hedges' g)

0.2

Standard error

Records excluded:    Non-empirical or review-       like record (n = 3)

Records screened (n = 28)

0.06

0.2

Hedges' g

Total (n = 3)

0.08

0.0

0.0

0.10

0.2

Reports sought for retrieval (n = 25)

Reports not retrieved:    No full text available       from any retrieval       strategy (n = 4)

0.2

0.4

0.12

Total (n = 4)

0.14

0.4

Reports assessed for eligibility (n = 21)

Reports excluded:    Irrelevant intervention (n = 1)    No persuasive outcome       measured (n = 1)

0 1000 2000 3000 4000 5000 6000 7000 8000 Total sample size (N)

0.4 0.2 0.0 0.2 0.4 Observed outcome (Hedges' g)

Total (n = 2)

Studies eligible for synthesis (n = 19)

CI 90% CI 95% CI g

Studies excluded:    No convertible statistic       for effect size (n = 6)    No quantitative outcomes       extractable from full text (n = 5)

f

Moderator: Domain

2023 2024 2025

Total (n = 11)

0.3

Cumulative effect size (Hedges' g)

Politics (k = 7)

Studies included in synthesis k = 8 studies 20 effect sizes

0.2

Final: g = 0.143

0.1

Health (k = 8)

0.0

c

0.1

3.3%

Study 1

General persuasion (k = 5)

0.2

Study 1

Study 3

Study 7

Study 7

Study 8

Study 8

Study 9

Study 19

Study 19

Study 19

Study 20

Study 20

Study 20

Study 26

Study 10

Study 21

Study 22

Study 23

Study 24

Study 11

5.3%

Study 2

Number of studies included

5.3%

Study 3

0.1 0.0 0.1 0.2 0.3 0.4 Hedges' g with CIs

Study year 2023 2024 2025

5.3%

Study 4

4.8%

Study 5

5.4%

Study 6

i

5.4%

Study 7

h

D1 D2 D3 D4 D5 D6 D7 Overall

5.0%

Study 8

High heterogeneity

5.6%

Study 9

Pooled Hedges' g 0.143  [0.059, 0.226]

Study 1

5.0%

Study 10

p-value 0.0008

Study 2

4.8%

Study 11

Studies (k) 20

5.2%

Study 12

Study 3

Total N 29382

88.3%

5.0%

Study 13

Cochran's Q 162.09  (df=19, p=0.0000)

Study 4

I2 (heterogeneity)

5.2%

Study 14

I2 88.3%

5.3%

Study 15


## 2 /

0.0317 / 0.1780

5.3%

Study 16

Low Some concerns High

H2 8.53

4.8%

Study 17

Note: D1: Bias due to confounding  D2: Bias due to selection of participants into the study  D3: Bias in classification of interventions  D4: Bias due to deviations from intended interventions  D5: Bias due to missing data  D6: Bias in measurement of outcomes  D7: Bias in selection of the reported result

Between-study heterogeneity Sampling error

4.9%

Study 18

5.0%

Study 19

4.5% Pooled Hedges' g = 0.143 95% CI [0.059, 0.226]

Study 20

0.8 0.6 0.4 0.2 0.0 0.2 0.4 0.6 0.8 Effect size (Hedges' g)


> **Figure 2: Demonstration of automated evidence synthesis using AUTOSYNTHESIS. To demonstrate the capa-**

> bilities of AUTOSYNTHESIS, we tasked the framework with synthesizing evidence on the persuasive power of large
language models, for which evidence is contested following the research question of the recent meta-analysis by
Hölbling et al. (2025) [12]. a, The input to AUTOSYNTHESIS is a user-provided research question to initiate the
automated evidence synthesis workflow. As a result, AUTOSYNTHESIS produces the following output: b, PRISMA
2020 [2] flow diagram summarizing the screening process and the final study inclusion. c, The forest plot shows
the study-level effects (in terms of Hedges’ g) and the pooled random-effects estimate with 95% confidence inter-
vals (CIs). d, Funnel plot to assess small-study effects and potential publication bias. e, Scatter plot as a diagnostic
tool to inspect the relationship between effect sizes and sample sizes. f, The cumulative plot shows how the pooled
random-effects estimate evolves as studies accumulate. g, The moderator analysis shows the pooled effect sizes across
predefined study-level characteristics (here: the domain of the underlying persuasion study). h, Heterogeneity statistics
summarizing the between-study variability (including I2, τ 2, and Cochran’s Q). i, Study-level risk-of-bias assessment
following ROINS-I [32], where the assessment is varies from low to high concern. AUTOSYNTHESIS further produces
a study-level overview with metadata and extracted effect sizes in a tabular format; see (Table. S4, S5)

2.2 AUTOSYNTHESIS can construct a relevant evidence base for meta-analyses

To assess the literature retrieval process, we evaluated whether AUTOSYNTHESIS constructed an

appropriate evidence base for the meta-analysis. Here, our evaluation focuses on the intermediate

steps of evidence synthesis, namely, study retrieval, screening, full-text eligibility assessment, and

inclusion in the final quantitative synthesis.

The study selection through AUTOSYNTHESIS was as follows (Fig. 3a). AUTOSYNTHESIS

retrieved 28 candidate records, retained 25, after screening title and abstract, and identified 19 to

satisfy the predefined eligibility criteria. Of these, 8 studies ultimately contributed to the quantita-

tive synthesis after excluding papers that lacked sufficient quantitative information for effect size

computation or statistical extraction. The resulting evidence base from AUTOSYNTHESIS showed

substantial agreement with the human benchmark (Fig. 3b); five of the seven studies included in

the human meta-analysis were also included by AUTOSYNTHESIS, corresponding to a recall of

71.4%. At the same time, AUTOSYNTHESIS included three additional studies that were not part of

the benchmark evidence base, corresponding to a precision of 62.5%.

Upon qualitative inspection, the differences between the benchmark evidence base and the evi-

dence base constructed by AUTOSYNTHESIS were mainly due to retrieval and eligibility decisions.

Of the two studies included in the benchmark meta-analysis but not recovered by AUTOSYNTHE-

SIS, one was not identified during the search process, whereas the other could not be processed

because its full-text PDF was not readily accessible for automated retrieval. Conversely, AU-

TOSYNTHESIS included three studies that were not part of the benchmark. One of these studies

was published after the search cut-off date of Hölbling et al. (2025) [12], and one was available as

a ResearchGate preprint, which was not included among the search sources used in the benchmark

review. The third study focused on preferences for LLM-generated messages rather than persua-

sive outcomes; a qualitative review by the lead author of the benchmark meta-analysis indicated

that this study was not directly relevant to the target research question. We therefore interpret this

10

case as an error in the eligibility assessment by AUTOSYNTHESIS, likely because the article used

an extensive framing around persuasion. After accounting for these qualitative differences, the

corrected overlap with the benchmark was higher: AUTOSYNTHESIS recovered six of the seven

benchmark studies, corresponding to a corrected recall of 85.7%, and seven of the eight studies

included by AUTOSYNTHESIS were judged relevant, corresponding to a corrected precision of

87.5%.

b

a

Benchmark included

AutoSynthesis included

(k = 7)

(k = 8)

28

(100%) 25

(89%) 19

(68%)

2 5

8

Number of papers


## 4 included

1 excluded
3

(29%)

Retrieved Screened Eligible Included


> **Figure 3: Evaluation of the literature retrieval and study selection. a, The funnel summarizing**

> study selection process by reporting the number of studies retrieved, screened, eligible, and finally
included. b, Agreement between the studies included by AUTOSYNTHESIS and those included in
the benchmark meta-analysis.

2.3 AUTOSYNTHESIS recovers accurate meta-analytic effect size estimates

We next evaluated whether AUTOSYNTHESIS reproduces the quantitative conclusions of published

manual meta-analyses.

At the meta-analysis level, the pooled effect estimate produced by AUTOSYNTHESIS remained

close to the published benchmark, especially when accounting for the corresponding confidence

intervals (Fig. 4b). For example, for the benchmark, AUTOSYNTHESIS estimated a positive pooled

11

effect of Hedges’ g = 0.143, while the original published estimate was g = 0.020 (∆g = 0.123;


> **Table S2); however, both estimates overlapped to a large extent, thus suggesting broadly similar**

quantitative conclusions. Importantly, the difference is within a ±0.20 tolerance region in terms of

the standardized effect size estimate, which is a tolerance region that was used previously to assess

whether deviations in reanalyses should be interpreted as broadly similar conclusions [39]. Both

the between-study heterogeneity analysis and the publication bias diagnostics were also broadly

comparable between the automated and human syntheses: both found substantial between-study

heterogeneity (I2 = 88.3% vs. 75.97%) and evidence of small-study effects based on Egger’s test

(p = 0.006 vs. p = 0.018; Table S2).

At the study level, seven effect sizes could be matched between AUTOSYNTHESIS and the

human benchmark. For these matched estimates, the standardized effect sizes extracted by AU-

TOSYNTHESIS showed a moderate-to-strong, positive association with the corresponding estimates

from the human benchmark (Pearson’s correlation coefficient r = 0.69, two-sided p = 0.085; ordi-

nary least squares (OLS) slope β = 1.62; Fig. 4a). This suggests that AUTOSYNTHESIS recovered

broadly similar study-level evidence. Some effect sizes were included only in one of the two

evidence bases (Fig. 4b) left and bottom inset, which reflects differences in study retrieval and

eligibility assessment rather than effect size computation. For the actual quantitative synthesis, the

computed effect size estimates and the resulting meta-analytic conclusions were largely similar

across the automated and human evidence synthesis.

12

a

b

0.30

Pooled effect size of baseline (Hedges' g)

0.25

0.20

No benchmark match (n=13)

0.15

0.4

No AutoSynthesis match (n=5)

Identity Regression Matched study

N = 7

r = 0.69

0.3

0.10

Effect size of benchmark (Hedges' g)

0.2

0.05

= 1.62

0.1

0.00

0.0

0.05

0.1

Identity Baseline: LLM persuasion (Hölbling, 2025)

0.2

0.05 0.00 0.05 0.10 0.15 0.20 0.25 0.30 Pooled effect size of AutoSynthesis (Hedges' g)

0.2 0.1 0.0 0.1 0.2 0.3 0.4 Effect size of AutoSynthesis (Hedges' g)


> **Figure 4: Agreement between the meta-analytics estimates produced by AUTOSYNTHESIS**

> and the manual benchmark. a, Comparison of study-level standardized effect sizes (Hedges’
g) extracted by AUTOSYNTHESIS and those reported in the published human benchmark (gray
points). The diagonal line indicates perfect agreement. Reported is the Pearson’s correlation co-
efficient (r) and the slope of the ordinary least squares (OLS) trend line (β). The separate scatter
plots at the top and left show studies that were not matched and thus included in only one of the
two evidence bases. The density plots above and on the right show the distribution of the effect
sizes across the full evidence base used by AUTOSYNTHESIS and the human benchmark, respec-
tively. b, Comparison of the pooled random-effects effect size estimated by AUTOSYNTHESIS and
the published human benchmark from Hölbling et al. (2025) [12]. The point estimate is shown
together with the corresponding 95% confidence interval (CI).

13

3 Discussion

In this work, we introduced AUTOSYNTHESIS, an end-to-end multi-agent framework that auto-

mates the complete meta-analysis workflow, from literature retrieval and study screening to quan-

titative data extraction, effect size computation, and statistical synthesis. In our evaluation, AU-

TOSYNTHESIS successfully recovered 71.4% of the studies included in the corresponding human-

conducted benchmark. Furthermore, the pooled effect estimate deviated by only 0.12 Hedges’ g

from the published human benchmark, demonstrating that AUTOSYNTHESIS can closely approx-

imate expert-conducted meta-analyses. This degree of deviation is broadly consistent with human

reanalysis efforts, where deviations from the original estimate are assessed using tolerance regions

and where a tolerance region of ±0.20 in terms of Cohen’s d is still considered as broadly ac-

ceptable [39]. The observed differences between AUTOSYNTHESIS and the published benchmark

primarily originated from literature retrieval rather than downstream statistical analysis. In partic-

ular, the largest discrepancies are because some relevant studies were not included for screening or

because their full-text articles were unavailable for subsequent analysis.

Our work also contributes to the emerging field of AI-assisted scientific research. Previous

LLM-based systems have demonstrated promising capabilities for literature retrieval, screening,

and eligibility assessment [19–21], systematic review automation [28], and structured information

extraction from scientific articles or other documents [22–27]. However, existing systems stop

before computing and substantially pooling standardized effect sizes across the evidence base and

therefore do not offer a quantitative synthesis. In contrast, AUTOSYNTHESIS focuses explicitly

on the steps that are specific to meta-analysis, namely, extracting statistical measures, computing

standardized effect sizes (including multiple effect sizes per study where applicable), performing

meta-analytic regression, conducting publication bias diagnostics and risk-of-bias assessment, and

generating reports aligned with common reporting standards.

Importantly, we do not view AUTOSYNTHESIS as a replacement for expert reviewers. The hu-

14

man element remains integral to many stages of the meta-analysis workflow, such as formulating

the research question, specifying inclusion and exclusion criteria, selecting relevant moderators for

analysis, and interpreting findings in light of study quality and existing domain knowledge. Many

of these steps require substantive expert judgment, and they can be challenging even for trained

human reviewers. AUTOSYNTHESIS should therefore not be used to shortcut expert judgment but

rather to support systematic checking and to refine intermediate decisions. As such, a particularly

promising application is to perform continuous updates of existing high-quality meta-analyses,

where the methodological framework has already been defined, successfully implemented, and

validated through peer review, so that newly published studies can be incorporated with substan-

tially reduced manual effort. This extends the broader idea of “living” systematic reviews [33] to

“living” meta-analysis, in which evidence is continuously synthesized.

The proposed AUTOSYNTHESIS framework has several strengths. First, AUTOSYNTHESIS

covers the entire meta-analysis workflow and includes several analyses that are not always per-

formed by default, such as publication bias diagnostics, risk-of-bias assessment, heterogeneity

analyses, etc. Importantly, many studies report more than one effect size (e.g., from multiple

experiments, or mixed-method approaches); AUTOSYNTHESIS is designed to handle this feature

common to meta-analyses by identifying and extracting multiple effect sizes from the same study

where applicable. Second, AUTOSYNTHESIS combines LLM-based reasoning with principled

statistical procedures. Hence, the framework preserves methodological rigor while improving re-

producibility and transparency. This may be especially useful for researchers with less specialized

expertise in meta-analytic methods. Third, the design is modular, and, because of this, AUTOSYN-

THESIS can be used to update meta-analyses, where parts of the review protocol or evidence base

may already be available. Fourth, AUTOSYNTHESIS records traceable audit logs and interme-

diate outputs, including screening decisions, eligibility judgments, extracted statistics, and effect

size calculations. Fifth, AUTOSYNTHESIS is flexible with respect to the underlying LLMs. Our

evaluations indicate that the framework can operate across different LLM backbones, including

15

open-weight models, which can help improve transparency and reproducibility [40].

Nevertheless, several limitations remain. First, our evaluation is limited by the number of

benchmark meta-analyses. Hence, although the results demonstrate the feasibility of automated

meta-analysis, they cannot establish robust performance across all potential settings, including

further scientific domains, study designs, outcome types, and reporting conventions. This lim-

itation is common for agentic systems that support scientific workflows, where comprehensive

evaluation across diverse task settings is often constrained by the cost and availability of suitable

benchmarks [17, 41–43]. It is therefore likely that performance may be lower in especially com-

plex domains, for poorly reported studies, or for tasks requiring substantial field-specific judgment.

Second, automated literature retrieval is constrained by the accessibility of scientific articles and

the availability of machine-readable full text (e.g., relevant studies may be missed when full texts

are behind paywalls, when PDFs cannot be reliably parsed, or when relevant statistics are reported

only in figures, appendices, or other formats that are difficult to extract). Similar constraints also af-

fect human reviewers, although humans can sometimes overcome them through institutional access

or by contacting authors directly. This limitation further highlights the importance of open-access

publishing and machine-readable reporting practices for scalable evidence synthesis. Third, some

studies do not report sufficient quantitative information to compute standardized effect sizes. This

is again a challenge shared with human meta-analysis, where reviewers must often contact authors

or exclude otherwise relevant studies because necessary statistics are unavailable. Fourth, the per-

formance of AUTOSYNTHESIS may depend on modeling choices, including the underlying LLM

and prompting strategy. Nevertheless, the modular design of AUTOSYNTHESIS allows to com-

pare different LLM backbones, and our evaluations further suggest that the main results are robust

across different backbones, including open-weight LLMs. Fifth, training data contamination is a

potential concern when evaluating LLM-based systems on published scientific studies. Because

some benchmark articles may have been used for LLM training, prior exposure could, in princi-

ple, improve document interpretation, statistical extraction, or reasoning over reported results. In

16

our setting, the risk that training data exposure directly determines the final meta-analytic result is

small and mitigated in part by the sequential workflow, where effect sizes are computed through

deterministic statistical procedures. Finally, AUTOSYNTHESIS covers many standard use cases

in quantitative evidence synthesis; still, extensions may be necessary to account for field-specific

differences in meta-analytic workflows.

Overall, agentic LLM systems can accelerate quantitative evidence synthesis, which is a cor-

nerstone of scientific knowledge production and policy-making [1–3, 34]. To this end, systems

such as AUTOSYNTHESIS can help researchers, clinicians, policy-makers, and other stakeholders

access reliable summaries of the rapidly growing scientific literature and thereby broaden access

to rigorous evidence-based decisions.

4 Methods

4.1 AUTOSYNTHESIS

Overview. AUTOSYNTHESIS is an end-to-end multi-agent framework for automated meta-

analysis (Fig. 1). The framework is designed to translate established best-practice principles in

evidence synthesis into a structured computational workflow by mapping individual steps of a

meta-analysis [2] to specialized agents. Starting from a research question in natural language,

AUTOSYNTHESIS first uses a planning agent to define the meta-analysis objective, treatment and

control conditions, eligibility criteria, target outcomes, candidate moderators, search strategy, and

expected effect direction (using human input where needed or desired). This gives a protocol for

the downstream agents that serves as a shared reference point and ensures that each stage of the

workflow remains aligned with the intended meta-analysis. Based on this plan, AUTOSYNTHESIS

executes the complete evidence synthesis process, including literature retrieval (search agent), full-

text retrieval and parsing (paper reading agent), full-text eligibility assessment (eligibility agent),

study and outcome identification (research question identification agent), statistical data extrac-

17

tion (statistical result extractor agent), statistical validation (statistical validation agent), effect

size computation (analysis agent), random-effects meta-analysis (random-effects meta-analysis

agent), publication-bias assessment (bias assessment agent), and report generation (report agent).

An overview of the different agents inside AUTOSYNTHESIS is provided in TableS3.

We implemented the LLM agents in AUTOSYNTHESIS using the LangGraph [44] framework,

which executes a ReAct-style [45] loop of reasoning, tool use, and observation. Here, LLM-based

agents handle reasoning-intensive tasks such as document understanding and structured extraction,

while deterministic computational modules perform statistical calculations, the meta-analytic re-

gression estimation, and all visualizations. This was done to improve the methodological rigor by

ensuring that statistical procedures follow established meta-analytic practice, while also making it

easier to generate standardized, publication-quality visualizations with a consistent design across

analyses. The prompts for the LLM-based agents are reported in the Supplementary Materials. The

modular, multi-agentic design also allows users to start the workflow at later stages, for example,

when updating an existing meta-analysis for which parts of the review process have already been

completed, or to override specific design choices of AUTOSYNTHESIS. All intermediate decisions

and outputs are stored in a shared workflow state, which yields an auditable record of the complete

meta-analysis process.

Protocol. The planning agent translates a research question in natural language into a struc-

tured meta-analysis protocol that guides the entire evidence synthesis workflow and serves as a

shared representation for downstream agents. In line with established best-practice recommen-

dations for systematic reviews and meta-analyses [2, 3], the agent is prompted to prospectively

specify the review objective, treatment and control conditions, eligibility criteria, target outcomes,

and analysis plan. The agent also suggests the search scope, including a sensible start where ap-

plicable (e.g., to exclude studies published before a technological, clinical, or policy milestone are

unlikely to be relevant, such as research on COVID-19 interventions before 2020). In addition,

the agent proposes relevant search terms and candidate moderators that may be used for subgroup

18

and heterogeneity analyses. Finally, the agent specifies the expected direction of the intervention

effect, which supports downstream interpretation and helps ensure that effect sizes are coded with

comparable signs across studies.

Of note, several of the above decisions made when formulating the protocol are inherently

expert-driven and may require substantial domain knowledge. AUTOSYNTHESIS therefore allows

users to refine the automatically suggested protocol elements (e.g., search query, moderators, start

date, databases) through a human-in-the-loop approach. For the empirical applications in this

paper, we use the default protocol generated by the planning agent to demonstrate the end-to-end

automated workflow.

Literature retrieval. Literature retrieval and full-text acquisition are handled by two agents as

follows.

The search agent receives the structured meta-analysis protocol and uses an LLM to gener-

ate a search query using Boolean operators tailored to the research question. Following common

practice in systematic reviews, the query is designed around the core elements of the target com-

parison, including the treatment or intervention, comparator or control condition, and outcome of

interest [3]. Where applicable, the search agent also applies exclusion criteria to remove records

that are unlikely to support quantitative synthesis, such as opinion pieces, editorials, non-empirical

articles, studies without a comparison or control group, or papers that do not report quantitative

outcomes.

The resulting query is then used to retrieve relevant papers from multiple scientific databases

and open-access repositories (i.e., arXiv, Semantic Scholar, CrossRef, OSF Preprints, and

PubMed). The databases are accessed through corresponding API calls. The retrieval pipeline

is modular, so additional proprietary databases (e.g., Web of Science, Scopus, and IEEE Xplore)

can be integrated where access is available. For each candidate paper, the search returns structured

metadata, including the title, abstract, authors, publication year, DOI, source URL, and, when

available, a direct PDF link. Retrieved records are aggregated and deduplicated using normalized

19

publication titles. In the implementation, the number of records retrieved from each source is

capped to limit cost, although this limit is configurable and can be increased for more exhaustive

searches. These papers then undergo an initial rule-based screening based on the title and abstract

using simple regular-expression filters to remove records that are clearly outside the scope of the

review.

The paper reading agent then attempts to retrieve the full text of each candidate paper from

multiple scientific sources (e.g., arXiv, Semantic Scholar, CrossRef, OSF Preprints, and PubMed).

When the full text cannot be obtained from these sources, additional retrieval strategies are applied,

such as access the PDF via the direct PDF link from the search agent, DOI-based resolution, and

web search as a fallback.

The retrieved PDF documents are converted into structured Markdown using a cascading

document-parsing pipeline. The framework first applies MinerU [46], which we found empiri-

cally to yield the best extraction quality on a sample of papers from our corpus. Because no single

tool reliably parses every PDF (e.g., scanned pages from historical databases, non-standard layouts,

or transient API failures), the framework falls back in turn to LlamaParse [47], Mistral OCR [48],

and conventional PDF text extraction whenever the preceding method fails. Tables and document

structure are preserved whenever possible, thereby enabling downstream agents to reason over both

narrative text as well as statistical information embedded in tables. Papers for which the full text

cannot be retrieved are logged and excluded from the subsequent steps.

Eligibility assessment. The eligibility assessment agent performs a full-text eligibility as-

sessment for candidate studies. It reviews each complete full-text of each study to determine

whether the study satisfies the predefined inclusion and exclusion criteria. In particular, the el-

igibility assessment agent is instructed to check whether the study is an empirical study, has a

treatment–control comparison, the availability of quantitative outcome measures, and is relevant to

the research question. Exclusion reasons are logged so that decisions for each retained or discarded

study can be traced during the final audit, which is also used to generate the PRISMA flowchart

20

later.

Study component identification. Scientific papers may report more than one independent em-

pirical component, such as multiple experiments, separate samples, or mixed-method studies. The

study identification agent therefore compiles a list of different components for each paper based on

the experimental design, participants, data collection procedure, and reported comparisons, so that

an effect size is retrieved for each component. Specifically, for each component, the agent identi-

fies the treatment and control groups, the relevant outcome variable, and the section of the article

where the supporting statistical evidence is reported. The result is a structured representation that

serves as an intermediate output (hereafter called “map”) for the subsequent extraction stage. This

further helps to ensure that statistical quantities are only collected only for effect sizes that are

relevant to the objective of meta-analysis, while avoiding that irrelevant analyses, manipulation

checks, or secondary results are extracted.

Extraction of statistical information. To improve the reliability, AUTOSYNTHESIS employs

a structured approach to extract information. The reason is that directly asking an LLM to extract

statistical results from a scientific article often leads to incomplete or incorrect outputs, as papers

frequently contain multiple studies, hypotheses, outcome measures, and secondary analyses. To

address this challenge, the statistical result extraction agent is composed of two sequential stages.

The two stages essentially separate document understanding from numerical extraction, which

reduces the likelihood that irrelevant statistics are extracted.

First, the framework constructs a structured representation of the paper as a set of linked JSON

records. The JSON records capture the experimental design, the separate study components, out-

come variables, and the relationships between hypotheses and reported results via explicit cross-

references between studies, effect sizes, and paper sections. This intermediate representation pro-

vides the contextual information required to accurately interpret the statistical evidence reported

throughout the article, especially when the experimental design and the corresponding results are

reported within different sections.

21

Second, statistical information is extracted only for the outcomes identified as relevant during

the previous stage. For each selected result, the system records the treatment and control groups,

sample sizes, descriptive statistics, test statistics, effect size information, and additional metadata

required for subsequent quantitative synthesis.

Statistical validation and relevance filtering. Following statistical extraction, all extracted re-

sults undergo a validation stage before quantitative synthesis. The validation agent double-checks

each extracted statistical value against the source article. The corresponding prompt instructs the

agent to verify that the corresponding information can be found verbatim, or within rounding, in

the relevant results section, table, or figure caption. A result is marked as “hallucinated” when core

statistics (i.e., test statistic, p-value, or means) cannot be located anywhere in the paper text. Values

that are incorrect but locatable elsewhere in the text are corrected; values that cannot be verified

at all are removed. As a result, the verification step reduces hallucinated statistics and prevents

incorrect values from propagating to the meta-analysis stage.

Scientific articles often report multiple statistical results for the same study, including pri-

mary outcomes, secondary analyses, subgroup analyses, and manipulation checks. To ensure that

only the most relevant result contributes to the meta-analysis, AUTOSYNTHESIS further applies a

relevance filtering after statistical validation. Each extracted result is classified according to the

outcome type and relevance to the research question, after which only the appropriate statistical


## results for quantitative synthesis are selected.

Analysis agent. The analysis agent first computes standardized effect sizes for each study

component from the extracted statistical information. Here, multiple reporting formats commonly

encountered in empirical studies, including hypothesis tests, regression coefficients, standardized

effect measures, and odds ratios, are supported. Whenever possible, these statistics are converted

into Cohen’s d and subsequently corrected to Hedges’ g [49], providing a common effect size

metric across included studies. If sufficient information is unavailable to compute a valid effect

size, the corresponding result is excluded from the quantitative synthesis, and the decision is logged

22

for traceability.

The analysis agent then follows a deterministic procedure to synthesize the standardized effect

sizes obtained from the previous stages. Specifically, the analysis agent estimates random-effects

meta-analytic models [3] to account for the fact that the underlying studies can span different

populations, interventions, outcome measures, and experimental settings and thus to account for

the between-study heterogeneity. Restricted Maximum Likelihood (REML) [50]. Pooled effects

are reported as Hedges’ g [49] with corresponding 95% confidence intervals (CIs). The random-

effects meta-analytic models are estimated using a custom REML implementation.

The analysis agent further generates publication-quality visualizations, namely, (i) forest plots

and (ii) cumulative forest plots across years to analyze how the pooled effect size changes as new

evidence is accumulated over time. In addition, the analysis agent computes standard heterogene-

ity statistics, including Cochran’s Q [51], I2, and τ 2, to quantify variability across studies [52].

Where sufficient information is available, the agent also conducts moderator analyses to exam-

ine whether effect sizes vary systematically across predefined moderators such as specific study

characteristics (e.g., the choice of the treatment).

Bias assessment. The bias assessment agent evaluates potential publication bias and study-

level risk of bias. For publication bias, the agent applies established methods when a sufficient

number of studies are available. Specifically, it assesses potential bias using three complemen-

tary analyses: (i) Egger’s regression test [30] to test for small-study effects; (ii) the trim-and-fill

procedure [29] to estimate the potential impact of missing studies on the pooled effect size; (iii)

leave-one-out sensitivity analysis to examine whether the pooled estimate depends strongly on

any individual study; and (iv) a scatter plot of effect sizes against sample size as an exploratory

diagnostic for small-study effects and potential publication bias. The final report includes (i)–

(iv). The agent also generates funnel plots to support visual inspection of small-study effects.

Random-effects meta-analytic models were estimated using a custom implementation of Restricted

Maximum Likelihood (REML) in Python (NumPy/SciPy), following the iterative algorithm of

23

Viechtbauer [50]. The DerSimonian–Laird estimator [53] was used to initialize the between-

study variance (τ 2) before REML optimization. Small-study effects and potential publication

bias were assessed using custom implementations of Egger’s regression test [30] and the trim-

and-fill procedure [29]. Rather than relying on external meta-analysis libraries (e.g., metafor or

statsmodels), all statistical routines were implemented directly in Python to ensure full control

over the analysis pipeline and facilitate integration with the multi-agent framework.

For study-level risk of bias, the Bias assessment agent uses the assessment framework ap-

propriate to the study design, such as RoB 2 for randomized trials [31] and ROBINS-I for non-

randomized studies of interventions [32]. The resulting risk-of-bias judgments are reported in

structured tabular form.

Report. Upon completion of the workflow, the report agent automatically generates a struc-

tured report that summarizes the full evidence synthesis. The report includes the literature re-

trieval process, study selection decisions, extracted quantitative information, effect size calcula-

tions, random-effects meta-analysis, moderator analyses to assess heterogeneity, publication bias

assessments, risk-of-bias assessment, and all corresponding visualizations. The report agent also

produces a PRISMA 2020 flow diagram [2] that reports the number of study records in each stage

of the review, including exclusion reasons and the final number of effect sizes. In addition, it gen-

erates a structured summary table containing all included studies and key metadata, such as study

identifier, sample size, intervention or exposure, outcome, and the extracted effect size. All plots

are generated using the matplotlib plotting library and exported as static PNG/PDF figures.

To improve transparency, AUTOSYNTHESIS records the outputs of every framework stage,

including screening decisions, extracted statistics, effect size calculations, etc. These records allow

users to trace and audit each included or excluded study throughout the workflow and facilitate

a human-in-the-loop use of AUTOSYNTHESIS to refine, audit, extend, or update existing meta-

analyses.

24

4.2 Evaluation

To evaluate the performance of AUTOSYNTHESIS, we benchmark our framework against pub-

lished manual meta-analyses. Here, we use the meta-analysis by Hölbling et al. (2025) [12]

with k = 12 effect sizes from N = 17, 422 participants as our main benchmark. First, it is a

peer-reviewed and recent meta-analysis, making it a timely reference case for which the under-

lying publications are available online, so that future work has a transparent basis to benchmark

AUTOSYNTHESIS. Second, it includes a broad range of analyses expected in a principled, state-

of-the-art meta-analysis to test the full capability spectrum of AUTOSYNTHESIS. For example, it

includes multiple heterogeneity analyses to demonstrate how AUTOSYNTHESIS can analyze mod-

erators. Third, key information of the meta-analysis workflow in [12] is public, including the

structured extraction tables. For example, it also reports risk-of-bias assessments in structured

numerical tabular form to facilitate quantitative comparisons across human approaches and AU-

TOSYNTHESIS. Finally, because one author of the present study overlaps with the original lead

of the review team, we can complement the quantitative benchmark with a qualitative assessment

of where AUTOSYNTHESIS agrees with, diverges from, or misses decisions made in the human

benchmark.

The input to AUTOSYNTHESIS was the following research question (see Fig. 2a): “What is

the effect of large language model (LLM)-generated persuasive messages on persuasive outcomes

compared with non-LLM or human-authored control messages?” The corresponding search query

generated by AUTOSYNTHESIS is shown in (Fig. 2a). We did not specify a start or end date for

the search; the search was performed in July 2026, so all studies up to this date were included as

knowledge cut-off.

We evaluate AUTOSYNTHESIS in two ways. First, we assess the intermediate performance by

validating different steps of the evidence synthesis workflow by comparing the outputs of individ-

ual agents with the human benchmark. (i) For the search agent, we evaluate literature retrieval

25

using overlap, precision, and recall between studies automatically retrieved by AUTOSYNTHESIS

vs. the studies retrieved or included in the benchmark. (ii) For the eligibility agents, we compare

inclusion and exclusion decisions using confusion matrices. (iii) For the statistical extraction agent

and validation agent, we compare the extracted quantitative information, including effect sizes and

standard errors, against the human benchmark.

Second, we evaluate the final quantitative synthesis produced by AUTOSYNTHESIS. We com-

pare the pooled random-effects Hedges’ g estimate and the confidence interval with the correspond-

ing estimate reported in the human benchmark. Effect size agreement is summarized graphically

using scatter plots of benchmark against AUTOSYNTHESIS estimates. We report Pearson’s corre-

lation coefficient r to quantify the association between the two sets of effect sizes. In addition, to

quantify the calibration, we estimate the slope β from an ordinary least squares (OLS) regression

with an intercept, where we regress the benchmark effect size on the corresponding AUTOSYN-

THESIS effect size.

4.3 Implementation details

AUTOSYNTHESIS is implemented in Python 3.11 and uses LangGraph [44] to orchestrate the dif-

ferent agents. All LLM-based agents (i.e., the planning agent, search agent, eligibility agent, re-

search question identification agent, statistical result extractor agent, statistical validation agent,

relevance filter agent, and report agent) use (openai/gpt-5.4-mini) through the Open-

Router API [54].

Reporting of the LLM configuration follows best-practice recommendations for LLM-based

research [55]; further details, prompts, and configuration files are provided in the repository. We

set the native reasoning effort to medium, we limited web tool use for retrieval to 40 papers ex-

tracted/database, and we left all other decoding parameters at their provider defaults. We do not

use persistent conversational memory between agent calls; each agent receives only the relevant

workflow state and source material required for its task. Structured outputs using JSON format are

26

used where required, for example, for eligibility decisions, extracted statistical quantities, and the

statistical validation.

A complete end-to-end run of main analysis using the Hölbling et al. benchmark [12] took

∼0.5 hours and used approximately 1M input tokens and 100K output tokens across 200 LLM

calls. This corresponded to a cost of around $1.5 under the model pricing at the time of access.

During the early development of AUTOSYNTHESIS, we explored simpler alternatives, includ-

ing a single-agent workflow and an integrated commercial agentic system for scientific workflows

(i.e., Claude Science [56]). These approaches were useful for isolated subtasks but did not reliably

complete the full evidence synthesis workflow; failures often appeared during long-running exe-

cutions such as study retrieval and quantitative extraction. As a result, the end-to-end performance

was not sufficiently stable for a meaningful benchmark, and we thus used the experiments primar-

ily to motivate the proposed multi-agent framework, which maps the manual steps of literature

reviews and meta-analyses onto a combination of specialized agents with deterministic statistical

processing.

Data availability

All data needed to replicate our analyses will be made available via a dedicated, public GitHub

repository.

Code availability

AUTOSYNTHESIS will be made publicly available under an open-source license.

27


## References

[1] Gurevitch, J., Koricheva, J., Nakagawa, S. & Stewart, G. Meta-analysis and the science of

research synthesis. Nature 555, 175–182 (2018).

[2] Page, M. J. et al. The prisma 2020 statement: An updated guideline for reporting systematic

reviews. BMJ 372 (2021). https://www.bmj.com/content/372/bmj.n71.full.pdf.

[3] Higgins, J. P. T., Thomas, J., Chandler, J. et al. Cochrane Handbook for Systematic Reviews

of Interventions (Cochrane, 2024), version 6.5 edn.

[4] Collaboration, O. S. Estimating the reproducibility of psychological science. Science 349,

aac4716 (2015). https://www.science.org/doi/pdf/10.1126/science.aac4716.

[5] Flake, J. K., Davidson, I. J., Wong, O. & Pek, J. Construct validity and the validity of

replication studies: A systematic review. American Psychologist 77, 576–588 (2022).

[6] Chen, L., Yan, R. & Hu, Y. City walk or nature walk? Evidence-based psychological and

physiological outcomes – a systematic review and meta-analysis. Urban Forestry & Urban

Greening 106, 128726 (2025).

[7] Holzner, N., Maier, S. & Feuerriegel, S. Generative AI and creativity: A systematic literature

review and meta-analysis (2025). URL https://arxiv.org/abs/2505.17241.

[8] Arifin, Z., Sukarmin, S., Saputro, S. & Kamari, A. The effect of inquiry-based learning on

students’ critical thinking skills in science education: A systematic review and meta-analysis.

Eurasia Journal of Mathematics, Science and Technology Education 21, em2592 (2025).

[9] Tlili, A., Saqer, K., Salha, S. & Huang, R. Investigating the effect of artificial intelligence in

education (AIEd) on learning achievement: A meta-analysis and research synthesis. Infor-

mation Development 41, 825–842 (2025).

28

[10] Bayat, K., Pooyan, P., Chhablani, J., Kanavi, M. R. & Ahmadieh, H. Retinal and choroidal

alterations in heart failure: A systematic review and meta-analysis of oct and oct-a findings

with emphasis on HFrEF. Ophthalmology and Therapy 14, 2631–2651 (2025).

[11] O’Mahoney, L. L. et al. The risk of long covid symptoms: a systematic review and meta-

analysis of controlled studies. Nature Communications 16 (2025).

[12] Hölbling, L., Maier, S. & Feuerriegel, S. A meta-analysis of the persuasive power of large

language models. Scientific Reports 15 (2025).

[13] Borah, R., Brown, A. W., Capers, P. L. & Kaiser, K. A. Analysis of the time and workers

needed to conduct systematic reviews of medical interventions using data from the prospero

registry. BMJ Open 7, e012545 (2017).

[14] Bastian, H., Glasziou, P. & Chalmers, I. Seventy-five trials and eleven systematic reviews a

day: How will we ever keep up? PLoS Medicine 7, e1000326 (2010).

[15] Feuerriegel, S., Hartmann, J., Janiesch, C. & Zschech, P. Generative AI. Business & Infor-

mation Systems Engineering 66, 111–126 (2023).

[16] Gottweis, J. et al. Accelerating scientific discovery with co-scientist. Nature (2026).

[17] Holtdirk, T. et al. Automated reproducibility assessments in the social and behavioral sci-

ences using large language models (2026). URL https://arxiv.org/abs/2606.13670. 2606.

13670.

[18] Yamada, Y. et al. The AI scientist-v2: Workshop-level automated scientific discovery via

agentic tree search (2025). URL https://arxiv.org/abs/2504.08066. 2504.08066.

[19] Syriani, E., David, I. & Kumar, G. Screening articles for systematic reviews with chatgpt.

Journal of Computer Languages 80, 101287 (2024).

29

[20] Guo, E. et al. Automated paper screening for clinical reviews using large language models:

Data analysis study. Journal of Medical Internet Research 26, e48996 (2024).

[21] Ofori-Boateng, R., Aceves-Martins, M., Wiratunga, N. & Moreno-Garcia, C. F. Towards

the automation of systematic reviews using natural language processing, machine learning,

and deep learning: a comprehensive review. Artificial Intelligence Review 57 (2024).

[22] Forster, K. et al. Assessing corporate sustainability with large language models: evidence

from europe. Nature Communications 17 (2026).

[23] Ahad, J. I. et al. Empowering meta-analysis: Leveraging large language models for scientific

synthesis (2024). URL https://arxiv.org/abs/2411.10878. 2411.10878.

[24] Li, L., Mathrani, A. & Susnjak, T. What level of automation is “good enough”? a benchmark

of large language models for meta-analysis data extraction. Research Synthesis Methods 17,

671–692 (2026).

[25] Rouzrokh, P., Khosravi, B., Rouzrokh, P. & Shariatnia, M. Lattereview: A multi-agent

framework for systematic review automation using large language models (2025). URL

https://arxiv.org/abs/2501.05468.

[26] Xu, W. et al. Manalyzer: End-to-end automated meta-analysis with multi-agent system

(2025). URL https://arxiv.org/abs/2505.20310.

[27] Padarha, S. et al. Evaluating AI-based scientific knowledge synthesis with epidemiological

systematic reviews (2026). URL https://arxiv.org/abs/2603.22327.

[28] Chen, S. F. et al. LLM-assisted systematic review of large language models in clinical

medicine. Nature Medicine 32, 1152–1159 (2026).

[29] Duval, S. & Tweedie, R. Trim and Fill: A simple funnel-plot–based method of testing and

adjusting for publication bias in meta-analysis. Biometrics 56, 455–463 (2000).

30

[30] Egger, M., Smith, G. D., Schneider, M. & Minder, C. Bias in meta-analysis detected by a

simple, graphical test. BMJ 315, 629–634 (1997).

[31] Sterne, J. A. C. et al. RoB 2: A revised tool for assessing risk of bias in randomised trials.

BMJ l4898 (2019).

[32] Sterne, J. A. et al. ROBINS-I: A tool for assessing risk of bias in non-randomised studies of

interventions. BMJ i4919 (2016).

[33] Iversen, I. A. & Quintana, D. S. The value of living systematic reviews. Nature Human

Behaviour 10, 647–649 (2026).

[34] Tyler, C. et al. AI tools as science policy advisers? the potential and the pitfalls. Nature 622,

27–30 (2023).

[35] Salvi, F., Horta Ribeiro, M., Gallotti, R. & West, R. On the conversational persuasiveness of

gpt-4. Nature Human Behaviour 9, 1645–1653 (2025).

[36] Bai, H., Voelkel, J. G., Muldowney, S., Eichstaedt, J. C. & Willer, R. Llm-generated messages

can persuade humans on policy issues. Nature Communications 16 (2025).

[37] Matz, S. C. et al. The potential of generative ai for personalized persuasion at scale. Scientific

Reports 14 (2024).

[38] Hackenburg, K. & Margetts, H. Evaluating the persuasive influence of political microtar-

geting with large language models. Proceedings of the National Academy of Sciences 121

(2024).

[39] Aczel, B. et al. Investigating the analytical robustness of the social and behavioural sciences.

Nature 652, 135–142 (2026).

31

[40] Shrestha, Y. R., von Krogh, G. & Feuerriegel, S. Building open-source ai. Nature Computa-

tional Science 3, 908–911 (2023).

[41] Brodeur, A. et al. Ai-assisted teams outperform ai-led teams but not human-only teams in

assessing research reproducibility in quantitative social science. Proceedings of the National

Academy of Sciences 123 (2026).

[42] Miao, J., Pritchard, J. K. & Zou, J. The agentic garden of forking paths (2026). URL

https://arxiv.org/abs/2607.01507.

[43] Bertran, M., Fogliato, R. & Wu, Z. S. Many ai analysts, one dataset: Navigating the agentic

data science multiverse. Proceedings of the National Academy of Sciences 123 (2026).

[44] Chase, H. Langchain. https://github.com/langchain-ai/langchain (2022).

[45] Yao, S. et al. React: Synergizing reasoning and acting in language models (2022). URL

https://arxiv.org/abs/2210.03629.

[46] Wang, B. et al. Mineru: An open-source solution for precise document content extraction

(2024). URL https://arxiv.org/abs/2409.18839.

[47] Liu, J. LlamaIndex (2022). URL https://github.com/jerryjliu/llama_index.

[48] Mistral AI. Introducing mistral ocr 3. https://mistral.ai/news/mistral-ocr-3/ (2025). Accessed:

2026-07-12.

[49] Hedges, L. V. Distribution theory for glass’s estimator of effect size and related estimators.

Journal of Educational Statistics 6, 107–128 (1981).

[50] Viechtbauer, W. Bias and efficiency of meta-analytic variance estimators in the random-

effects model. Journal of Educational and Behavioral Statistics 30, 261–293 (2005).

32

[51] Deeks, J. J., Higgins, J. P., Altman, D. G. & on behalf of the Cochrane Statistical Meth-

ods Group. Analysing data and undertaking meta-analyses (2019). URL http://dx.doi.org/10.

1002/9781119536604.ch10.

[52] Borenstein, M., Hedges, L. V., Higgins, J. P. T. & Rothstein, H. R. Introduction to Meta-

Analysis (Wiley, 2009).

[53] Jackson, D., Bowden, J. & Baker, R. How does the dersimonian and laird procedure for

random effects meta-analysis compare with its more efficient but harder to compute counter-

parts? Journal of Statistical Planning and Inference 140, 961–970 (2010).

[54] OpenRouter.ai. Openrouter. https://openrouter.ai (2026). Accessed: 2026-07-16.

[55] Feuerriegel, S. et al. A reporting checklist for large language models in behavioural science.

Nature Human Behaviour (2026).

[56] Anthropic. Claude for science: An AI workbench for scientific research. https://www.

anthropic.com/news/claude-science-ai-workbench (2025). Accessed: 2026-07-13.

33

Acknowledgments

Funding by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under the

National Research Data Infrastructure – NFDI 27/1-2026, project number 460037581 is acknowl-

edged.

Author contributions

All authors contributed to conceptualization, manuscript writing, and approved the manuscript.

Competing interests

The authors declare no competing interests.

34

Supplementary Figures

0.160

0.155

Pooled estimate (Hedges' g)

0.150

0.145

0.140

0.135

0.130

0.125

3 6 9 12 15 18 Omitted study

Fig. S1: Leave-one-out sensitivity analysis. The pooled random-effects estimate (Hedges’ g) was recomputed k times, each time omitting one study, to assess whether any single study dis- proportionately drives the overall result. Each point shows the recomputed pooled estimate with that study excluded, plotted against the omitted study’s index; the estimate remains stable across omissions (range g ≈0.13–0.16), indicating that no single study is unduly influential.

35

Supplementary Tables

Moderator analysis


> **Table S1: Subgroup (moderator) analyses of the pooled effect size (Hedges’ g). Subgroups with**

> fewer than two studies were not pooled; these include Country (Canada, United Kingdom), LLM
model (Bloom, GPT-3 davinci, GPT-4o, GPT-4-0613), and Publication status (Working paper).

Moderator Subgroup k Hedges’ g 95% CI I2 (%) QM p

Between subjects 15 0.147 [0.054, 0.239] 89.4 0.87 .646 Mixed 2 −0.043 [−0.796, 0.709] 95.4 Within subjects 3 0.184 [0.088, 0.280] 66.0

Study design

Country United States 19 0.147 [0.060, 0.234] 88.8 0.22 .642

Claude 3.5 Sonnet 2 0.393 [0.198, 0.589] 64.0

13.16 .068 DeepSeek v3 2 0.282 [0.110, 0.454] 66.6 GPT-3 8 0.067 [−0.055, 0.189] 89.6 GPT-3.5 4 0.173 [0.076, 0.269] 76.8

LLM model

General persuasion 5 0.331 [0.243, 0.418] 44.2 10.88 .004 Health 8 −0.018 [−0.153, 0.116] 85.9 Politics 7 0.182 [0.128, 0.236] 59.0

Domain

Publication status Published 19 0.133 [0.048, 0.219] 88.3 1.00 .318

36


> **Table S2: Comparison of quantitative evidence synthesis for AUTOSYNTHESIS and the hu-**

> man bechmark. Results are based on the LLM persuasion task from Hölbling et al. (2025) [12].

Manual benchmark AUTOSYNTHESIS

Included studies 7 8 Effect size estimates (k) 12 20

Pooled hedges’ g 0.020 0.143 95% CI [-0.048, 0.093] [0.059, 0.226] p-value 0.530 < 0.0008

I2 (%) 75.97 88.3 Egger’s test (p-value) 0.018 0.006

37

Overview of Multi-Agent Architecture


> **Table S3: Overview of the different agents within AUTOSYNTHESIS.**

Agent Purpose Input Output Prompt

Planning Translates the natural-language research question into a structured review protocol

Research question Meta-analysis plan, search queries, inclu- sion criteria, modera- tors

4.3

Search Generates and reformulates search queries, retrieves and deduplicates candidate stud- ies, applies title/abstract screening

Meta-analysis plan List of candidate papers (with metadata)

4.3

Paper reading Retrieves and parses full text via a docu- ment extraction pipeline

Candidate paper metadata / PDFs

Full-text papers (struc- tured Markdown)

N/A

Eligibility Assesses full-text eligibility against inclu- sion/exclusion criteria

Full-text papers Eligible papers, exclu- sion reasons

4.3

Eligible full-text pa- pers

Studies and their rel- evance to the search queries

4.3

Research ques- tion identification

Identifies independent research questions within each paper and maps relevant re- search questions/outcomes

Structured paper rep- resentation, full text

Extracted statistical re- sults

4.3

Statistical result extractor

Builds a structural map of the paper, then extracts quantitative results for each rele- vant outcome

Extracted statistical results, full text

Validated statistical re- sults

4.3

Statistical valida- tion

Validates extracted values against the source text; corrects or removes unsup- ported quantitative evidence

Relevance filter Classifies extracted rows and selects a sin- gle winning result per study–outcome group

Verified result rows Filtered rows (one per outcome)

4.3

Filtered, coded results Pooled effect size, heterogeneity (I2, τ 2), plots

N/A

Analysis agent Computes standardized effect sizes (Hedges’ g, Cohen’s d) and synthesizes them via a random-effects model

N/A

Validated statistical results

Pooled effect size, heterogeneity statistics (Q, I2, τ 2), confidence intervals, and meta- analysis visualizations

Random-effects meta-analysis

Computes standardized effect sizes (Hedges’ g), estimates between-study heterogeneity using REML, and synthe- sizes evidence using a random-effects meta-analysis

Bias assessment Assesses publication bias and study-level risk of bias using established meta-analysis methods

Included studies, ex- tracted statistical re- sults, pooled effect sizes

RoB assessment, Eg- ger’s test, trim-and-fill analysis, funnel plot

4.3

Report Synthesizes all prior outputs into a PRISMA-compliant narrative report

All prior-stage out- puts

Final meta-analysis re- port

4.3

38

Supplementary Materials

Prompts

Planning agent

Planning agent: System prompt

You are an expert meta-analyst and systematic review methodologist. A user has given you a research question. Your job is to design a complete meta-analysis plan for that question following PRISMA 2020 guidelines.

You must call ‘create_plan‘ with ALL fields filled in. Be specific:

- treatment_label / control_label: the two conditions being compared

(e.g. ’LLM-generated persuasive text’ vs ’human-written persuasive text’). - search_queries: 2-3 short keyword strings optimised for academic

database search (not Boolean syntax -- just keyword phrases). Each query should include the intervention/topic plus empirical intent words when natural, such as ’experiment’, ’trial’, ’controlled’, ’comparison’, ’quantitative’, ’outcome’, or ’effect’. Avoid queries that mainly retrieve reviews or meta-analyses. - inclusion_criteria: 2-3 BROAD, permissive criteria. Keep them

general -- err heavily on the side of inclusion. A paper only needs to be broadly related to the topic and report some quantitative outcome. Do NOT add strict design, sample-size, or journal-quality requirements. - exclusion_criteria: 3-4 exclusion reasons that MUST include:

(1) not an original empirical study (systematic reviews,

meta-analyses, editorials, opinion pieces, and theoretical papers are excluded); (2) no comparison between a treatment and a control condition; (3) no quantitative outcome data that can produce an effect size

(means+SDs, t/F-values, proportions, or odds ratios required); (4) completely unrelated to the research topic. - moderators_to_extract: 3-6 study-level variables that could explain

heterogeneity (e.g. ’study design’, ’topic domain’, ’sample size category’). - positive_direction: what a POSITIVE Hedges g means in plain

language. - search_start_year: sensible earliest year (e.g. 2015 for LLM

topics, 1990 for clinical trials).

39

Search agent

Search agent: Query generation prompt

You are helping run a systematic literature search for a meta-analysis. Rewrite the planned research question into concise academic database search queries. Return exactly {max_variants} query string(s), unless fewer are truly appropriate.

Research question: {research_question} Treatment/intervention: {treatment_label} Control/comparator: {control_label} Outcome: {outcome_description} Existing draft queries: {existing_draft_queries}

Guidelines: - Use short keyword phrases, not long sentences. - Include empirical intent words when natural, such as experiment,

trial, controlled, comparison, quantitative, outcome, or effect. - Avoid phrases that mainly retrieve reviews, systematic reviews,

meta-analyses, editorials, protocols, or opinion pieces. - Do not use Boolean operators unless they are essential.

Return only JSON in this schema: {"queries": ["query one", "query two"]}

Eligibility agent

Eligibility agent: System prompt (templated per plan)

You are a systematic review methodologist assessing papers for inclusion in a quantitative meta-analysis.

Research question: {research_question}

Inclusion criteria: {inclusion_criteria}

Exclusion criteria: {exclusion_criteria}

Only EXCLUDE the paper when the evidence is clear. Do not infer exclusion from missing snippets, sparse abstracts, or uncertain terminology.

EXCLUDE the paper if ANY of the following is clearly true:

A) It is NOT an original empirical study -- it is a systematic

review, meta-analysis, editorial, commentary, opinion piece, or purely theoretical paper.

40

B) It has NO comparison between at least two groups or conditions

(no treatment vs. control, intervention vs. baseline, or equivalent contrast). C) It clearly has NO quantitative outcome data -- no means, SDs,

t-values, F-values, proportions, or odds ratios that could support an effect size computation. D) It is completely unrelated to the research question.

INCLUDE if none of the above clearly apply. When in doubt about design, topic fit, or quantitative data availability, INCLUDE -- the extractor and deterministic statistical checks will verify this downstream.

Call ‘eligibility_decision‘ for every paper. Always provide a short reason (<=8 words), e.g. ’systematic review’, ’no control condition’, ’no quantitative outcome data’, ’meets all criteria’.

Research question identification agent

Study identification agent: System prompt

You are a scientific-paper structure analyst specialised in identifying independent studies within a single paper.

A paper may report one study or several (Study 1 / Study 2, Experiment 1 / Experiment 2, Wave 1 / Wave 2, etc.). Your job is to detect every independent study and record its sample size, design, treatment/control groups, primary outcome variables, and where its results appear in the paper.

Rules: - A ’study’ is an independent data-collection episode with its own sample. Separate conditions within ONE dataset are NOT separate studies. - Do not invent studies. If the paper has one study, record only one. - Every study record must cite where in the paper its results appear. - Call ‘record_study‘ once per study.

Research question identification agent: System prompt

You are a scientific meta-analysis extraction specialist.

Your task is NOT to extract every statistical analysis or every hypothesis in the paper.

Your task is to extract ONLY the experimentally tested effects that are directly relevant to the synthesis objective provided by the user.

The synthesis objective defines:

41

* which constructs are relevant, * which outcomes are primary, * and which analyses should be ignored.

-------------------------------------- GENERAL EXTRACTION RULES -------------------------------------- Extract:

* primary experimentally tested effects * preregistered or central outcomes * statistically evaluated comparisons directly relevant to the synthesis objective

Do NOT extract:

* manipulation checks * robustness checks * mediation analyses * moderation analyses unless central * exploratory analyses * manipulation validation * linguistic/process variables * descriptive-only statistics * supplementary analyses * subgroup analyses unless central to the paper’s main claim

-------------------------------------- UNIT OF EXTRACTION -------------------------------------- The unit of extraction is: ONE DISTINCT EFFECT RELEVANT TO THE SYNTHESIS OBJECTIVE

NOT:

* every table row * every regression * every statistical test

If multiple analyses test the same construct: extract only the primary/preferred/main analysis.

-------------------------------------- PRIORITIZATION -------------------------------------- Prioritize:


## 1. Primary outcomes

2. Preregistered outcomes
3. Main experimental contrasts
4. Central claims in abstract/results/discussion

If uncertain whether an effect is central: prefer inclusion -- it is better to over-extract than to miss a relevant

42

effect.

-------------------------------------- OUTPUT PHILOSOPHY -------------------------------------- You are building a CLEAN SYNTHESIS DATASET, not a complete theory map.

Fewer highly relevant effects are preferred over many weakly related analyses.

Statistical result extractor agent

Statistical result extractor agent: System prompt

You are a precise research-paper analyst and statistical extractor. You work in two mandatory phases:

PHASE 1 -- Paper Understanding (ALWAYS FIRST)

Call ‘record_paper_map‘ ONCE before anything else. Build a complete structural map: paper type, study design, comparison type, studies, outcome variables, hypotheses (H1/H2/RQ1/...), and the sections where statistics appear. For each hypothesis record: hypothesis_id, hypothesis_text, linked_outcome (the outcome variable it tests), study_label, and predicted direction.

PHASE 2 -- Statistical Extraction

Use the paper map from Phase 1 as your mental model. When a user query is provided, use the hypotheses list to identify ALL hypotheses whose linked_outcome directly or closely measures the construct in the user query -- then extract the statistical result for EACH relevant hypothesis in EACH independent study. Extract ONLY from this paper’s own Results sections -- never from Introduction, Related Work, Background, or Discussion sections that describe OTHER papers’ statistics.

Phase 1 must always complete before Phase 2 begins. Never skip the paper map. Never invent experiments or statistics.

43

Statistical validation agent

Statistical validation agent: System prompt

You are a rigorous statistical fact-checker for meta-analysis.

You are given the full text of a research paper and a list of statistical results that were automatically extracted from it. Your job is to verify each result by locating the exact numbers in the paper text.

Rules: 1. Only accept a number as verified if it appears VERBATIM (or within rounding) in the paper text -- in the Results section, tables, or figure captions. 2. Do NOT accept numbers from Introduction, Related Work, or Discussion sections that describe OTHER studies. 3. If a value is wrong but the correct value is in the text, issue a ’corrected’ verdict and provide the corrected value. 4. If a value cannot be located anywhere in the text, mark it in failed_stats. 5. Mark the result ’hallucinated’ only if the CORE numbers (test statistic, p-value, or means) are absent from the paper text entirely. 6. Call ‘record_validation‘ once per extracted result row. 7. Be precise: 3.77 and 3.78 are NOT the same.

Relevance filter agent

Relevance filter agent: System prompt

You are a meta-analysis outcome classifier. Your ONLY job is to classify each row -- you do NOT decide which rows to keep. A separate algorithm will select winners based on your classifications.

For EVERY row call classify_and_select with accurate values for:


## 1. OUTCOME CLASS

primary | secondary | manipulation_check | process_variable |
exploratory | robustness_check | descriptive


## 2. CONSTRUCT FAMILY

A normalised label for the underlying construct being measured.
CRITICAL -- PARENTHETICAL QUALIFIER RULE:
Outcome names that share the same base name but differ only by a
parenthetical qualifier are sub-conditions of the SAME construct.
Strip the qualifier.
Examples:

’Compliance rate (overall)’, ’Compliance rate (truthful)’,

44

’Compliance rate (deceptive)’ -> all three: construct_family = ’compliance_rate’ ’Accuracy (truthful persuasion)’, ’Accuracy (deceptive persuasion)’ -> both: construct_family = ’accuracy’ ’Attitude change (immediate)’, ’Attitude change (delayed)’ -> both: construct_family = ’attitude_change’ The qualifier NEVER creates a new construct_family.


## 3. GRANULARITY LEVEL

Within the construct_family group, is this row:
- ’aggregate’
-- covers all conditions/full sample (keyword:
’overall’, ’total’, ’combined’, or no qualifier)
- ’sub_condition’ -- splits by condition, content type, time point,

sub-scale (keywords: ’truthful’, ’deceptive’, ’immediate’, ’delayed’, etc.) - ’standalone’ -- neither (single unique measure)


## 4. COMPARISON ARM

From group_1_label / group_2_label, classify the comparison arm:
- ’target_arm’
-- treatment is the LLM / AI intervention of
interest
- ’non_target_arm’ -- treatment is a human or other non-AI

comparator - ’primary’ -- only one arm exists


## 5. IS SYNTHESIS RELEVANT

True if the construct directly answers the synthesis objective.
False for manipulation checks, process variables unrelated to the
main outcome, etc.


## 6. PRIORITY RANK (1 = highest)

1=behavior, 2=compliance/persuasion, 3=attitude, 4=intention,
5=resistance, 6=experiential, 7=mechanism, 8=descriptive

Call classify_and_select once for EVERY row. Do not skip any. Set is_winner=True for all rows -- the selection algorithm overrides this.

Analysis agent

Analysis agent: Interpretation prompt (templated per result)

You are a meta-analysis expert. Summarise these results in 3-4 sentences suitable for a systematic review paper:

Pooled Hedges’ g = {pooled_g}, 95% CI [{ci_lower}, {ci_upper}], p = {p_value}, I^2 = {i_squared}%, tau = {tau}, k = {k} studies. Focus on effect magnitude, direction, and heterogeneity.

45

Bias assessment agent

Bias agent: Interpretation prompt (templated per result)

Interpret this publication bias assessment in 2-3 sentences: Egger’s test p={eggers_p_value}, trim-and-fill k0={trim_fill_k0}, risk={bias_risk}.

Report agent

Report agent: System prompt (templated per plan)

You are an academic writer specialising in systematic reviews and meta-analyses. Write a comprehensive, publication-quality meta-analysis report.

Research question: {research_question} Treatment: {treatment_label} Control: {control_label} Outcome: {outcome_description} Effect direction: {positive_direction}

Structure: Abstract -> Search/Screening -> Included Studies -> Effect Sizes -> Meta-Analytic Result -> Heterogeneity -> Moderators -> Publication Bias -> Discussion -> Limitations -> Conclusion. Call ‘finalise_report‘ with the complete Markdown text.

46


> **Table S4: Study-level metadata for the studies included in the meta-analysis, as extracted by AUTOSYNTHESIS.**

Salvi 2024 gpt-4-0613 (GPT-4)

Schoenegger et al. 2025 Claude 3.5 Sonnet

Schoenegger et al. 2025 Claude 3.5 Sonnet

propaganda? Gulati 2024 GPT-3 davinci

Schoenegger et al. 2025 DeepSeek v3

Schoenegger et al. 2025 DeepSeek v3

Study Report Title Author Year LLM model

humans on policy issues Bai 2025 GPT-3.5

humans on policy issues Bai 2025 GPT-3.5

humans on policy issues Bai 2025 GPT-3

Karinshak et al. 2023 GPT-3

Karinshak et al. 2023 GPT-3

Karinshak et al. 2023 GPT-3

Karinshak et al. 2023 GPT-3

Karinshak et al. 2023 GPT-3

Karinshak et al. 2023 GPT-3

S19 R1 Working with AI to persuade: Examining

S19 R2 Working with AI to persuade: Examining

S19 R3 Working with AI to persuade: Examining

S20 R1 Working with AI to persuade: Examining

S20 R2 Working with AI to persuade: Examining

S20 R3 Working with AI to persuade: Examining

Large Language Models: A Randomized

S1 R1 On the Conversational Persuasiveness of

S9 R1 LLM-generated messages can persuade

S10 R1 LLM-generated messages can persuade

S11 R1 LLM-generated messages can persuade

Persuasive Than Incentivized Human

Persuasive Than Incentivized Human

Persuasive Than Incentivized Human

Persuasive Than Incentivized Human

S7 R1 Large Language Models Are More

S7 R2 Large Language Models Are More

S8 R1 Large Language Models Are More

S8 R2 Large Language Models Are More

generate pro-vaccination messages

generate pro-vaccination messages

generate pro-vaccination messages

generate pro-vaccination messages

generate pro-vaccination messages

generate pro-vaccination messages

a large language model’s ability to

a large language model’s ability to

a large language model’s ability to

a large language model’s ability to

a large language model’s ability to

a large language model’s ability to

S3 R1 How persuasive is AI-generated

Controlled Trial

Persuaders

Persuaders

Persuaders

Persuaders

47

persuasion Prolific behavioral persuasion/compliance average compliance rate across persuasion

CloudResearch attitude change policy support for an assault weapons ban

persuasion Prolific behavioral persuasion/compliance average compliance rate across deceptive

argument_strength; attitude toward

policy attitudes message exposure Prolific.com attitude change policy support across policy topics

one-on-one debate Prolific ordinal 1–5 Likert transformed agreement outcome analyzed with partial

S19 public health messaging message exposure Amazon Mechanical Turk continuous scale perceived_message_effectiveness;

propaganda one-shot article exposure Lucid quota sample percent agreement percentage agreement with thesis

policy attitudes message exposure Prolific.com attitude change policy support for a smoking ban

persuasion Prolific behavioral accuracy percentage of correct answers

persuasion Prolific behavioral accuracy percentage of correct answers

proportional odds model

Study Domain Interaction type Recruitment source Outcome type Outcome measurement

persuasion questions

vaccination

statements

questions


> **Table S5: Study and outcome characteristics for the same meta-analytic corpus.**

Study Report Title Author Year LLM model

Persuade Humans on Policy Issues Bai. 2025 GPT-3.5

Persuade Humans on Policy Issues Bai. 2025 GPT-3.5

Sehgal 2025 GPT-4o

Lim 2023 Bloom

Persuade Humans on Policy Issues Bai. 2025 GPT-3

policy attitudes message exposure Prolific.com and

S21 R1 Conversations with AI Chatbots Increase

S22 R1 AI-Generated Messages Can Be Used to

S23 R1 AI-Generated Messages Can Be Used to

S24 R1 AI-Generated Messages Can Be Used to

evaluation of AI-generated messages: A

Not Outperform Standard Public Health

Short-Term Vaccine Intentions But Do

decision-making interactive conversational

decision-making interactive conversational

decision-making interactive conversational

decision-making interactive conversational

S26 R1 The effect of source disclosure on

two-part study

Messaging

S9 political persuasion /

S11 political persuasion /

S3 political persuasion /

S10 political persuasion /

persuasion / online

S1 conversational

S8 persuasion /

S7 persuasion /

S7 persuasion /

S8 persuasion /

debates

48

S23 political persuasion exposure to a persuasive message Prolific and CloudResearch attitude/policy support policy support for an assault weapons ban

study pool and Prolific) attitude/evaluation effects perception (EP) under moderation

Connect continuous intention Immediate HPV vaccine likelihood

argument_strength; attitude toward

S24 political persuasion exposure to a persuasive message Prolific attitude/policy support policy support across four policies

label Amazon Mechanical Turk continuous scale perceived_message_effectiveness;

S22 political persuasion exposure to a persuasive message Prolific attitude/policy support policy support for a smoking ban

by negative attitudes toward AI

Study Domain Interaction type Recruitment source Outcome type Outcome measurement

vaccination

(0–100)

S26 health communication source disclosure labels two study pools (University

vaccine persuasion multi-turn conversation Prolific and CloudResearch

S20 public health messaging message exposure with no source

S21 health communication /

49
