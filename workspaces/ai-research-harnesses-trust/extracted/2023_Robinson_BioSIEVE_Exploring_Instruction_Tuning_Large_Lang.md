---
workspace_id: "SCI-000111"
doi: "10.48550/arxiv.2308.06610"
title: "Bio-SIEVE: Exploring Instruction Tuning Large Language Models for Systematic Review Automation"
year: 2023
extraction_engine: "pymupdf"
---
# 2023 Robinson BioSIEVE Exploring Instruction Tuning Large Lang

Bio-SIEVE: Exploring Instruction Tuning Large Language Models for Systematic

Review Automation

Ambrose Robinson,1 William Thorne,1 Ben Wu,1 Abdullah Pandor,2 Munira Essat,2 Mark

Stevenson,1 Xingyi Song1

Department of Computer Science1/School of Health and Related Research2, The University of Sheffield ambroser53@gmail.com, {arobinson10, wthorne1, bpwu1, a.pandor, m.essat, mark.stevenson, x.song}@sheffield.ac.uk

arXiv:2308.06610v1  [cs.CL]  12 Aug 2023


## Abstract

before satisfactory performance is achieved (Przybyła et al. 2018). Language models like BERT (Devlin et al. 2019) and T5 (Raffel et al. 2019) have been applied to screening priori- tisation (Sadri and Cormack 2022; Yang et al. 2022; Wang et al. 2022) and classification (Moreno-Garcia et al. 2023; Qin et al. 2021). However, model input size has been a com- mon limitation and zero-shot performance severely lacked compared to basic trained models like Support Vector Ma- chines (SVM) or traditional methods such as Query Likeli- hood Modelling (QLM). Given the general-purpose capabil- ity of LLMs like GPT-3.5-turbo (hence referred to as Chat- GPT), studies have attempted to evaluate the ability to assist in screening classification using a zero-shot approach with promising yet varied results, evoking the need for a spe- cialised solution.

Medical systematic reviews can be very costly and resource intensive. We explore how Large Language Models (LLMs) can support and be trained to perform literature screening when provided with a detailed set of selection criteria. Specif- ically, we instruction tune LLaMA and Guanaco models to perform abstract screening for medical systematic reviews. Our best model, Bio-SIEVE, outperforms both ChatGPT and trained traditional approaches, and generalises better across medical domains. However, there remains the challenge of adapting the model to safety-first scenarios. We also explore the impact of multi-task training with Bio-SIEVE-Multi, in- cluding tasks such as PICO extraction and exclusion rea- soning, but find that it is unable to match single-task Bio- SIEVE’s performance. We see Bio-SIEVE as an important step towards specialising LLMs for the biomedical system- atic review process and explore its future developmental op- portunities. We release our models, code and a list of DOIs to reconstruct our dataset for reproducibility.

Reviewers must also provide reasons for excluding po- tentially relevant articles. Automating this task could reduce workload as a qualitative filtering mechanism - where sensi- tivity (recall) is essential, excluded reviews could be briefly inspected to validate their exclusion. Exclusion reasons can also provide reviewers using these tools with an insight into the model’s decision process.

1 Introduction Systematic reviews (SR) are widely used in fields such as medicine, public health and software engineering where they help to ensure that decisions are based on the best available evidence. However, they are time-consuming and expensive to create. Expensive specialist time must be spent evaluat- ing natural language documents. This is becoming infea- sible due to the exponentially increasing release of litera- ture, especially in the biomedical domain (Zhao et al. 2021). Michelson and Reuter (2019) estimated that the average SR cost $141,194 and takes a single scientist an average of 1.72 years to complete.

Our contribution is a family of instruction fine-tuned Large Language Models, Bio-SIEVE (Biomedical System- atic Include/Exclude reViewer with Explanations), that at- tempts to assist in the SR process via classification. By in- corporating the existing and expansive Cochrane Review knowledge base via instruction tuning, Bio-SIEVE estab- lishes a strong baseline for inclusion or exclusion classifi- cation screening of potential eligible studies given their ab- stract for unseen SRs. Bio-SIEVE is highly flexible and able to consider specific details of a review’s objectives and se- lection criteria without the need to retrain.

Automation approaches have been introduced to assist in alleviating these issues, targeting different stages of the pro- cess. The most targeted stages are searching, screening and data extraction. It is standard practice for screening solutions to utilise an active learning approach. A human is ”in the loop” labelling the model’s least certain samples and rank- ing articles by relevance (Sadri and Cormack 2022; Wallace et al. 2012; Wang et al. 2022). However, stopping criteria is a common insufficiency, often being left to the end user and risking missed relevancy. Regardless, this does not lead to an out-the-box solution and requires significant screening

The task we explore is more challenging than existing work as it requires filtering of more subtly irrelevant arti- cles. Previous work has mainly comprised of screening for simple topics or single selection criterion (Syriani, David, and Kumar 2023; Moreno-Garcia et al. 2023). We filter by an arbitrary set of selection criteria and objectives and ex- tend this problem by introducing the novel, challenging task of exclusion reasoning.

We investigate the efficacy of different instruction tuning methods on our data with an ablation study. Following the

Preprint. Under review.

and Welsh 2014; Kloda, Boruff, and Cavalcante 2020). This, along with a preliminary search, helps to establish the re- views inclusion and exclusion criteria.

Once the parameters of the study are sufficiently defined, a Boolean query is constructed for use in the searching of large databases in order maximise the recall of as many rele- vant articles as possible and is refined in an iterative process (Wang et al. 2023). In the next stage, the relevance of each study to the review is assessed via evaluation of the study’s title and abstract. The recall from Boolean queries can lead to massive amounts of documents and the time and cost of this stage can be further exacerbated by ”double-screening” and ”safety-first” approaches that require multiple review- ers independently carrying out the same relevance screening (Shemilt et al. 2016). The following stage is full-text screen- ing where it is hoped that the majority of irrelevant studies have been discarded since, compared to title and abstract, obtaining the full-text of studies is not necessarily trivial (Tawfik et al. 2019).


> **Figure 1: A simple representation of the systematic review**

> process depicting the stage which Bio-SIEVE aims to assist.
The black funnels are the monotonous and highly resource
intensive bottlenecks of the process.

The final stages consist of: adding included reviews based on manual searching; data extraction of relevant info and quality checking; data checking and double checking; anal- ysis, and writing.

work of Vu et al. (2020); Sanh et al. (2022), we train a set of models on the multi-task paradigm of PICO extraction and exclusion justification in an attempt to leverage benefi- cial cross-task transfer. As Longpre et al. (2023) found that treating generalised instruction tuning as pretraining led to pareto improvements, we fine-tune on top of Guanaco in ad- dition to LLaMA. We find that multi-task transfer is limited but instruction tuned pretraining caused marginal improve- ments. We also find that training on our dataset leads to highly accurate exclusion of inappropriate studies, e.g. ex- cluding muscle trauma studies from oral health reviews. Fi- nally, Bio-SIEVE-Multi shows promise for the task of inclu- sion reasoning but fails to match the performance of Chat- GPT in preference rankings.

As depicted in Figure 1, Bio-SIEVE targets the title and abstract screening phase given the objectives and selection criteria of the study established by the review team earlier in the process and the abstract of the study being screened. This phase is the most appropriate given the current capability of LLMs as full-text screening requires longer context lengths.

3 Related Work There have been a number of approaches to automating the SR process. These works are delineated into classification techniques, which provide a distinct inclusion or exclusion label, and prioritisation techniques, which assist in screen- ing by ranking reviews by relevance. Where classifiers aim to directly reduce the number of manually screened studies, ranking strategies aim to allow the reviewer to stop screen- ing early by considering the top-k returned documents.

We believe that Bio-SIEVE lays the foundation for LLMs specialised for the SR process, paving the way for future developments for generative approaches to SR automation. We open-source our codebase1 and the means with which to recreate our datasets. We also release our adapter weights on HuggingFace2 for reuse and further development.

Basic screening techniques have matured, for example Marshall et al. (2018) and Wallace et al. (2017), which are n- gram classifiers for randomised control trials, with the latter being integrated into Cochrane Reviews’ Evidence Pipeline (How 2017). These methods excel at single, easily general- isable tasks but far more difficult is evaluating articles based on topic and review-specific inclusion criteria.

2 The Systematic Review Process The systematic review process is a series of steps mapping a comprehensive plan for the study of a specific research field. This results in an effective summarisation of research mate- rial in a particular area or to answer a particular question within a domain.

Other early classifier techniques utilise ensemble SVMs (Wallace et al. 2010), Random Forest (RF) (Khabsa et al. 2016) or Latent Dirichlet Allocation (Miwa et al. 2014) al- gorithms with active learning strategies to combat the heavy ”exclude” class imbalance that naturally occurs. Many more recent approaches such as Abstrackr (Wallace et al. 2012), Rayyan (Olofsson et al. 2017) and RobotAnalyst (Przybyła et al. 2018) simply take this regime and streamline its usabil- ity. However, there are some clear issues with this approach. For example, Przybyła et al. (2018) found that RobotAna- lyst required anywhere between 29.26% to 93.11% of their study collection pool to be manually screened before 95% recall relevance was achieved.

Initially the reviewer establishes a research question from which a selection criteria is developed that defines the scope of the project and therein the criteria for study rele- vance. The Population, Intervention, Comparison, Outcome (PICO) framework is a tool that can be used to define the parameters of a study. Other frameworks also exist such as PICOS and SPIDER (Methley et al. 2014; Cates, Stovold,

1https://github.com/ambroser53/Bio-SIEVE 2https://huggingface.co/Ambroser53/Bio-SIEVE

RLHF to improve the response quality of LLMs and was expanded upon to create ChatGPT which has become the benchmark for zero-shot performance.

Qin et al. (2021) was first to apply transformers to classifi- cation in the context of SRs, yet found fine-tuned BERT was outperformed by their Light Gradient Boosting Machine. Active learning with transformers was applied to Technol- ogy Assisted Review tasks (Sadri and Cormack 2022) with Yang et al. (2022) finding that the amount of pretraining be- fore active learning is crucial. Wang et al. (2022) evaluated a variety of BERT models for relevance ranking both fine- tuned and zero-shot, but disregarded the models zero-shot capability after poor results. Most recently, Moreno-Garcia et al. (2023) applied BART ”zero-shot” with input embed- dings on sets of abstracts queried with short questions over a specific selection criterion but saw poor performance un- less combined with an RF or SVM.

Since ChatGPT, many open-source instruction tuned LLMs have emerged to try to match its performance. Gua- naco (Dettmers et al. 2023) is a family of LLaMA-based LLMs trained using 4-bit quantization and LoRA. The zero- shot performance of Guanaco-65B on the Vicuna bench- mark (Chiang et al. 2023) achieves 99.3% the performance of ChatGPT.

Instruction tuning is a method of fine-tuning where tasks are phrased as natural language prompts and has been shown to improve LLM performance on zero-shot tasks. (Wei et al. 2022) The detailed ablation study carried out by Longpre et al. (2023) found that treating instruction tuning as pre- training before downstream task fine-tuning caused faster convergence and often provided better performance overall. Vu et al. (2020) found that transfer learning with multiple tasks in the same domain could improve the performance of the tasks individually.

The recent widespread adoption of ChatGPT has invig- orated attempts to utilise LMs for classification, especially in the medical domain. Qureshi et al. (2023) comments that ChatGPT selected articles when used for relevance screen- ing ”could serve as a starting point for refinement depending on the complexity of the question”. Wang et al. (2023) quan- titatively explored ChatGPTs ability to assist in the search- ing process by constructing Boolean queries but found that although precision was promising, recall was disappointing and variability from minor prompt changes and even same prompt use brought the reproducibility of its use into ques- tion. Methodical studies evaluating ChatGPT’s effectiveness in classification have started to emerge. Guo et al. (2023) reported 91% exclusion recall but only 76% recall of in- cluded articles when screening a dataset of 24k+ total ab- stracts where only 538 were inclusion samples. They also remarked on ChatGPT’s ability to generate reasoning for ex- clusions and it’s potential for improving SR screening qual- ity. Syriani, David, and Kumar (2023) placed a strong em- phasis on reproducibility, setting a temperature of zero to ensure a higher level of consistency and found that, when prompted to be more lenient with inclusions, ChatGPT could be more conservative and sustain high recall of eligible ex- amples given the general topic of the study and the abstract of the potential reference. They concluded that ChatGPT is a viable option.

Full fine-tuning of LLMs is prohibitively expensive to non-commercial entities; as such, techniques have been de- veloped to minimise computational requirements and train- ing time while maintaining high performance. Based on the hypothesis that parameter updates have a low intrin- sic rank (Aghajanyan, Zettlemoyer, and Gupta 2020), Low Rank Adaptation (LoRA) (Hu et al. 2021) applies a rank decomposition of specified weight matrices while freezing the original network to reduce the trainable parameter count whilst delivering comparable performance to full-finetuning. Combined with 8- or even 4-bit quantization, it is possible to fine-tune 65B parameter models on a single 48GB GPU (Dettmers et al. 2021, 2023).

4 Methods

Instruct Cochrane Dataset We gathered a total of 7,330 medical SRs from all possible topic areas available on the Cochrane Reviews3 website. Each review contained the ob- jectives and selection criteria along with all considered stud- ies and whether they were included or excluded from the review. Excluded studies were accompanied by a reason for exclusion. Out of these 7,330 reviews were derived a train- ing split of 6,963 and an evaluation split of 367. Each study is treated as an individual data point. The distributions of the separate splits are displayed in Table 1.

We argue the use of ChatGPT unavoidably compromises reproducibility. The alteration and retraining of ChatGPT over time is opaque as Chen, Zaharia, and Zou (2023) found that its performance on certain tasks had changed dramati- cally between March and June of 2023. Furthermore, Chat- GPT’s size and consumption costs are similarly opaque but, as a generalised model, it can be assumed to be larger than any specialised approach. This elicits the demand for a smaller language model specialised for this task, where the exact model can be referenced and computational resources disclosed.

Cochrane was selected for review gathering as the review format is standardised. The delineated objectives and selec- tion criteria were suitably informative for review specifica- tion and the exhaustive references were clearly categorised into included and excluded. In addition, reviews provided justification for exclusion and descriptions of the population, intervention and outcome of considered reviews created a basis for a multi-task dataset. Comparison data was difficult to retrieve and were not included thus these tasks will hence be referred to as PIO extraction tasks. Topic distribution of the train and test sets can be found in Figure 2.

LLaMA (Touvron et al. 2023) has become a popular foundational model for causal generation as it was made open for non-commercial use in contrast to the GPT family (Brown et al. 2020; OpenAI 2023) which has been closed- source since GPT3. Reinforcement-Learning with Human- Feedback (RLHF) (Christiano et al. 2017) has become a popular technique for controlling generated outputs from language models. InstructGPT (Ouyang et al. 2022) applied

3www.cochranelibrary.com

Instruction Given the abstract, selection criteria and ob- jectives should the study be included or excluded?

Input Abstract: This paper describes the study design, methodological considerations, and baseline characteristics of a clinical trial to determine if intense 48 weeks, twice per week Tai Chi practice can reduce the frequency of falls among older adults transitioning to frailty compared to a wellness education program. ... Secondary outcome mea- surements include ... Objectives: To assess the effects benefits and harms of exer- cise interventions for preventing falls in older people living in the community. Selection Criteria: We included randomised controlled trials RCTs evaluating the effects of any form of exercise as a sin- gle intervention on falls in people aged 60 years living in the community. We excluded trials focused on particular condi- tions, such as stroke.


> **Figure 2: The topic distribution of the inclusion/exclusion**

> classification samples in the train and test splits of the In-
struct Cochrane dataset.

Task Train Test Subset S-1st Irre. Inclusion 43,221 576 784 79 - Exclusion 44,879 425 927 29 780 Inc/Exc 88,100 1,001 1,711 108 780 Population 15,501 - - - - Intervention 15,386 - - - - Outcome 15,518 - - - - Exc. Reason 11,204 - - - - Total 168,842 1,001 1,711 108 780

Response Included


> **Figure 3: Example Instruct Cochrane sample used in instruc-**

> tion tuning. Wolf et al. (2001) is the study being being eval-
uated for inclusion in Gillespie et al. (2012).


> **Table 1: Number of samples in each split of the Instruct**

> Cochrane dataset.

treated as exclude. This results in a benchmark that rewards cautious models with high include recall.

Annotation was performed by professional medical sys- tematic reviewers, who were instructed to choose from 3 la- bels: ’Include’, ’Exclude’, or ’Insufficient Information’. For evaluation purposes, we treat ’Insufficient Information’ as ’Include’, since these would be samples that should proceed to full-text screening phase, in keeping with a safety-first ap- proach.

Due to size of the test split and the fact that we are eval- uating many models on many different test sets, we instead chose to use a truncated subset of the full test split that max- imised the diversity of topics. This allowed the test set to remain the basis of evaluation for the model’s generalisation across topics.

Overall, there were 11 disagreements between our labels and the labels provided by the original reviewers. Our an- notators labelled 3 samples as ”Include” and 8 samples as ”Insufficient Information”. In the Instruct Cochrane dataset, these samples were all labelled, after full-text screening, as exclude.

Instruction Tuning Method Following the work of Chung et al. (2022), we utilised instruction fine-tuning in order to bolster the efficacy of the fine-tuning process. In- put data was formatted with natural language instructions for the tasks of inclusion or exclusion classification, PICO extraction, and exclusion reason generation. To minimise in- formation loss from truncation, the inputted sections were tokenised and scaled down proportional to their length until they fit within the max input token length of 2048. We utilise the Alpaca instruction format (Taori et al. 2023) with all our models to match Guanaco and to maintain consistency be- tween the Guanaco and base LLaMA models. (See Figure 3 for an example instruction). Full details on our preprocess- ing methods can be found in Appendix C.

This issue of label mismatch extends to the larger test set and the training set. However, applying this manual re- annotation procedure to training data and more testing data was infeasible due to costs, especially since professional medical reviewers were used as annotators.

Review Subsets In order to compare to classifier tech- niques trained for a specific review, a subset of reviews with a sufficient number of abstracts is required to train and eval- uate with k-fold cross validation. For this we took the 13 re- views from the evaluation set that have over 100 associated abstracts resulting in a total of 1711 individual samples.

Safety-First Test Set Since samples could potentially have been excluded during full-text screening with infor- mation unavailable in the abstract, the test split labels may not reflect the appropriate decisions at an abstract screening stage. We curated a safety-first test set by manually annotat- ing include/exclude decisions for a small subset of 108 sam- ples from the test split, with each sample consisting of the objectives and selection criteria for the review and the ab- stract of the prospective study. The resulting safety-first set was biased toward include with 79 samples and 29 samples

Irrelevancy Test Set To ensure that the model is able to exclude wildly irrelevant submissions, we constructed a evaluation set of selection criteria paired with abstracts from a completely distinct topic. Starting from the 13 reviews in the Review Subset, we paired each review with 5 ran- dom abstracts from the other reviews. Since each review in this subset is from a different topic area, each instruction

prompt formed from this set is guaranteed to be irrelevant (i.e. should be classified as ’exclude’).

the large review subset. We also fine-tuned and evaluated Bio-BERT-MSM in the same manner.

We applied a standard data pre-processing methodology for logistic regression. Each abstract was lowercased, had stopwords removed, and was lemmatized using NLTK (Bird, Klein, and Loper 2009). A new tokenizer was trained for each review based on TF.IDF. All training and tokeniza- tion was performed using Scikit-Learn (Pedregosa et al. 2011). For Bio-BERT-MSM, only the abstract was provided when fine-tuning. However, when evaluating zero-shot per- formance the review’s objectives and selection criteria were also provided utilising the Huggingface Zero-shot Classifi- cation Pipeline as in Moreno-Garcia et al. (2023).

5 Experimental Setup 5.1 Bio-SIEVE Model Description To evaluate the suitability of multi-task transfer learning (Vu et al. 2020; Sanh et al. 2022) and instruction tuning as pre- training (Longpre et al. 2023) we conduct an ablation, train- ing four Bio-SIEVE models: single-task/multi-task, Guana- co/LLaMA.

We used QLoRA fine-tuning to train LLaMA7b and Gua- naco7B on the Instruct Cochrane Train split. For the multi- task versions, 4 A100 80GB cards were used for 40 hours with an effective batch size of 16, whereas the single task versions were trained in the same setup for 24 hours.

Exclusion Reasoning We evaluate the multi-task model variants’ exclusion reasons via 5-star ranking. 81 exclusion tasks are taken from 3 reviews out of the 13 review subset. These are selected to best fit our expertise to speed up the process. All samples are validated to ensure that the justifi- cation could be derived from only the objectives, selection criteria and abstract. Outputs with significant generation ar- tifacts are penalised 1 star with a minimum score of zero. A rating of 5 represents a perfect match with the original reviewer’s justification.

In order to maintain consistency with Guanaco (Dettmers et al. 2023), we fix the hyperparameters during QLora fine- tuning: 4-bit double quantisation to the NF-4 datatype, 0.1 LoRA dropout, LoRA alpha of 16, LoRA rank 64, LoRA adapters on all layers but without biases and a learning rate of 2e-4 with no warmup or learning rate decay. LLaMA base model LoRA weights were randomly initialised with seed 0. Each model was trained for 8 epochs and the best model on the safety-first set was selected for comparison.

6 Results Results for the classification task for each dataset is pre- sented in Table 2. Preference results for exclusion reason generation ranking is provided in Figure 4. Agreement via Pearson’s correlation coefficient between our two indepen- dent experts was r=.84 for our Guanaco7B variant, r=.42 for our LLaMA7b variant and r=.62 for ChatGPT generations and p¡.001.

5.2 Evaluation Methodology We evaluate inclusion and exclusion performance through accuracy for an overview of model understanding, and pre- cision and recall for the inclusion class as a more direct eval- uation of the model’s real world applicability to SR automa- tion. We compare the different permutations of Bio-SIEVE to a series of zero-shot baselines and trained models using the standard approach on the review subset. Each experiment was ran once with a temperature of 0 and no sampling.

Our trained models achieve better accuracy scores than ChatGPT on the Test and Subset Eval sets Our best performing model, Guanaco7B (Single), achieved 0.82 ac- curacy on the Test Set. By comparison, ChatGPT achieved 0.6 accuracy. Similarly, for the Subset, Guanaco7b (Single) achieved accuracy 0.26 higher than ChatGPT whilst only re- ducing inclusion recall by 0.01.

Zero-shot comparisons To establish a baseline for our task, we query three generic, instruction tuned models: Chat- GPT, Guanaco7B, and Guanaco13B. We test Guanaco7B as it represents the baseline performance of the Guanaco7B versions of Bio-SIEVE, prior to finetuning. ChatGPT is used as the state-of-the-art comparison and Guanaco13B to ob- serve how model scale affects zero-shot performance. To al- ter the tasks for evaluation with ChatGPT, we use the prompt designed by Syriani, David, and Kumar (2023). We include additional information on the objectives and selection crite- ria of the SR for additional context since our regular test set is more challenging (See Figure 6 in Appendix B).

Our trained models slightly outperform active- learning style models specialised for a single review Gua- naco7B (Single) achieves 0.81 accuracy on the Subset eval set. The next best model is the Logistic Regression Base- line, which achieved 0.8. We highlight that this LR baseline had a data advantage over our generalised models: separate Logistic Regression models were trained for each individ- ual review in the Subset whereas our trained models relied on only one single fine-tuned LLM for entire Subset. Addi- tionally, the logistic regression models used 80% of samples per Subset review for training data (5 fold cross-validation). By contrast, our trained models had never seen any of the re- views or studies in the Subset Evaluation set during training.

In order to compare against the zero-shot method defined in Wang et al. (2022), we use Bio-BERT (Lee et al. 2019) finetuned on the MS MARCO dataset4 (hence Bio-BERT- MSM) (Gao, Dai, and Callan 2021; Nguyen et al. 2016) and evaluate performance on our Test, Safety-first and Subset data zero-shot.

ChatGPT is able to be more lenient, allowing it to per- form well on the safety-first dataset ChatGPT tended to include reviews rather than exclude, leading to high recall at the expense of precision. (Note: this was due to an ex- plicit prompt instruction to ’be lenient’) This means that it performed strongly on the safety-first set with an accuracy of 0.73. Our best model on this subset, LLaMA7B Single

Inclusion Exclusion Baselines To simulate the active learning approach standard to the field, we applied 5-fold cross validation using a logistic regression model to deter- mine the average performance across the 13 reviews within

4https://huggingface.co/nboost/pt-biobert-base-msmarco

Test Subset Safety-first Irre. Model Pre. Rec. Acc. Pre. Rec. Acc. Pre. Rec. Acc. Acc. Logistic Regression* - - - 0.79 0.78 0.80 - - - - Bio-BERT-MSM* - - - 0.43 0.30 0.50 - - - - ChatGPT † (ZS) 0.59 0.96 0.60 0.50 0.86 0.55 0.79 0.86 0.73 0.98 Guanaco13B (ZS) 0.58 0.95 0.56 0.47 0.96 0.47 0.71 0.90 0.67 0.03 Guanaco7B (ZS) 0.57 0.95 0.56 0.46 0.95 0.46 0.73 0.96 0.72 0.02 Bio-BERT-MSM (ZS) 0.69 0.14 0.54 0.46 0.93 0.47 0.66 0.93 0.64 0.09 LLaMA7B (Single) 0.77 0.79 0.74 0.65 0.83 0.71 0.88 0.72 0.72 0.96 LLaMA7B (Multi) 0.88 0.64 0.74 0.85 0.70 0.80 0.91 0.38 0.52 0.97 Guanaco7B (Single) 0.85 0.82 0.82 0.76 0.85 0.81 0.88 0.62 0.66 0.98 Guanaco7B (Multi) 0.90 0.64 0.75 0.81 0.69 0.78 0.95 0.46 0.58 0.99


> **Table 2: Results of inclusion/exclusion classification for a logistic regression baseline, the zero-shot (L)LMs and the Bio-SIEVE**

> variants. Test, Subset and Safety-first metrics are precision, recall and accuracy. Single variants were only trained on the task
of include/exclude classification. Multi models were also trained on PIO extraction and exclusion reasoning. * indicates results
when trained/fine-tuned with 5-fold cross validation on the Review Subset. †ChatGPT version as of 27/07/23

achieved higher precision (0.88) but slightly lower accuracy (0.72). We did not experiment with leniency prompting or thresholding for our trained models but anticipate that this would further improve results.

parison to 2.4 and 2.0 for the Guanaco7B and LLaMA7B Bio-SIEVE-Multi variants and we therefore treat ChatGPT as the current state-of-the-art for this exclusion reasoning task. Bio-SIEVE-Multi variants managed to match the qual- ity of ChatGPT for 45% of samples but there were minimal examples of Bio-SIEVE exceeding its quality (6-7%). Over- all, the quality of exclusion reasons remains poor: ChatGPT generated subpar or incorrect reasons for 83% of samples.

Single-task training was more effective than multi- task training The single-task models tended to be include recall oriented and higher performing with the Guanaco7B- Single variant outperforming all our other models by at least 0.07 accuracy whilst preserving the highest inclusion recall of 0.82 and 0.85 on Test and Subset respectively.

7 Discussion Model Comparison Bio-SIEVE takes a more balanced ap- proach to classification as shown by its consistently higher precision but relatively small decrease in recall. This sug- gests a greater ability to reason over the selection criteria. In contrast, ChatGPT, using the prompt format of (Syriani, David, and Kumar 2023), tends to be overly lenient and overly inclusive. This is demonstrated when evaluating per- formance broken down per topic, as shown in Figure 5.

Irrelevancy test: open-source LLMs must be fine- tuned in order to be effective systematic reviewers Both ChatGPT and our trained models perform very well on the irrelevancy test, demonstrating that these models are able to effectively exclude off-topic abstracts. However, other zero- shot models perform very poorly (Guanaco7B achieves only 0.02), revealing that these open-source models are unsuit- able for use in the zero-shot setting as they include many highly irrelevant abstracts.

Our models perform consistently across review topics whereas ChatGPT performance varies greatly. For ”Genetic Disorders” ChatGPT results are significantly below other models; for ”Heart & Circulation” and ”Infectious Disease” topics, it predicted ”Include” for all samples and never ”Ex- clude”. This draws into question the extent of ChatGPT’s generality and underscores the necessity to assess model blind spots prior to their endorsement for real world appli- cation.

Other zero shot model suffer this problem to an even greater extent. They tend to include everything, even ab- stracts from unrelated topics, as shown in the Irrelevancy column of 4. Therefore, despite high include recall per- formance on all three evaluation sets, they do not serve any practical benefit to reviewers. This shows that, de- spite claims of performance matching ChatGPT on chatbot benchmarks like Vicuna (Chiang et al. 2023), open-source models (when they are not fine-tuned to a task) are still a long way off reaching similar zero-shot capabilities.


> **Figure 4: Statistics for model generated exclusion reasons**

> when scored by two experts independently given the original
author’s exclusion justification.

Bio-SIEVE outperforming the active learning style Logis- tic Regression models is also an achievement. This validates that LLMs can facilitate reasoning of SR criteria with lan-

ChatGPT provides the best exclusion reasons ChatGPT managed an average score of 3.4 in our rankings in com-


> **Figure 5: Performance measured by F1-score for each metric for all models compared to ChatGPT on different medical domain**

> topics within the test set. ChatGPT excluded no samples for topics where no exclude bar is present.

is in addition to reproducibility concerns arising from the opacity of closed-source models.

guage, a far more accessible and cost effective method of automation when compared to the training of models that learn the criterion of individual SRs which has been the de facto approach for over a decade.

Bio-SIEVE also outperforms traditional active-learning models that are specialised for an individual review. This demonstrates the promising capability of LLMs to assist in the SR process: a single model can be widely deployed for an entire SR domain, without the need for re-training per re- view task. Though we focused on biomedical applications of this technology, our models and training process could be applied to other domains such as software engineering or scientific systematic reviews. Our model is a first step to- wards this objective and we set a benchmark for generative language model solutions.

Effect of Training Data Training data topic imbalance had no noticeable effect on generalisation. For example,over half the training samples were in the ”Child Health” topic yet Bio-SIEVE obtained similar if not better results on ”Heart & Circulation” samples, which made up only 4.5% of the training data. ”Genetic Disorder” topic performance is strong despite only making up 1.2% of the training data.

We generally find that for multi-task models, cross-task transfer between PIO, Exclusion reasoning and Include/Ex- clude classification harms performance. We speculate two reasons for this 1) Dataset Imbalance: PIO data was only available for included studies which may have resulted in tasks concentrated around a smaller subset of topics with reduced variation 2) Hallucinations - exclusion reasons and PIO information often relied on information from full-text screening. Training the model to extract this information from the abstract when not present may have encouraged it to hallucinate and/or overfit to the training data.

The performance of Bio-SIEVE could be further im- proved by including few-shot prompting: both in training data as well as during inference. We did not experiment with few-shot prompts due to the limitations of model context window: the length of each sample makes it difficult to in- clude additional examples in the prompt. However, using a mix of zero-shot and appropriately selected few-shot exam- ples is likely to lead to improved performance, as discussed in (Longpre et al. 2023).

Finally, we highlight the current shortcomings of our ap- proach. Namely, that the exclusion reasons generated by our Bio-SIEVE-Multi variants were outperformed by ChatGPT. In our case, multi-task training was necessary to enable ex- clusion reasoning capability, but this worsened inclusion- exclusion performance. For future work, we plan to ex- plore better methods of achieving multi-task capability in Bio-SIEVE, such as using a Mixture-of-Experts architecture (Shazeer et al. 2017). We hope that adding a greater variety of tasks will eventually improve the model’s reasoning ca- pabilities and extend its functionality to form an effective generalised assistant for every stage of the SR process.

8 Conclusion and Further Work

In this paper, we demonstrate the effectiveness of train- ing open-source LLMs to perform biomedical title/abstract screening. Our trained models achieve significant accuracy improvements over ChatGPT, and are specialised for the healthcare domain. Our results also reveal the dangers of relying on ChatGPT’s zero-shot performance: its accuracy is very uneven across healthcare topics, performing partic- ularly poorly on Genetic Disorders and being excessively lenient for Infectious Disease and Heart & Circulation. This

Acknowledgements

for Computational Linguistics: Human Language Technolo- gies, Volume 1 (Long and Short Papers), 4171–4186. Min- neapolis, Minnesota: Association for Computational Lin- guistics. Gao, L.; Dai, Z.; and Callan, J. 2021. Rethink Train- ing of BERT Rerankers in Multi-Stage Retrieval Pipeline. arxiv:2101.08751. Gillespie, L. D.; Robertson, M. C.; Gillespie, W. J.; Sher- rington, C.; Gates, S.; Clemson, L.; and Lamb, S. E. 2012. Interventions for Preventing Falls in Older People Living in the Community. Cochrane Database of Systematic Reviews, (9). Guo, E.; Gupta, M.; Deng, J.; Park, Y.-J.; Paget, M.; and Naugler, C. 2023. Automated Paper Screening for Clinical Reviews Using Large Language Models. arxiv:2305.00844. Hu, E. J.; Shen, Y.; Wallis, P.; Allen-Zhu, Z.; Li, Y.; Wang, S.; Wang, L.; and Chen, W. 2021. LoRA: Low-Rank Adap- tation of Large Language Models. arXiv:2106.09685. Khabsa, M.; Elmagarmid, A.; Ilyas, I.; Hammady, H.; and Ouzzani, M. 2016. Learning to Identify Relevant Studies for Systematic Reviews Using Random Forest and External Information. Machine Learning, 102(3): 465–482. Kloda, L. A.; Boruff, J. T.; and Cavalcante, A. S. 2020. A Comparison of Patient, Intervention, Comparison, Outcome (PICO) to a New, Alternative Clinical Question Framework for Search Skills, Search Results, and Self-Efficacy: A Ran- domized Controlled Trial. Journal of the Medical Library Association : JMLA, 108(2): 185–194. Lee, J.; Yoon, W.; Kim, S.; Kim, D.; Kim, S.; So, C. H.; and Kang, J. 2019. BioBERT: a pre-trained biomedical language representation model for biomedical text mining. Bioinfor- matics, 36(4): 1234–1240. Longpre, S.; Hou, L.; Vu, T.; Webson, A.; Chung, H. W.; Tay, Y.; Zhou, D.; Le, Q. V.; Zoph, B.; Wei, J.; and Roberts, A. 2023. The Flan Collection: Designing Data and Methods for Effective Instruction Tuning. arxiv:2301.13688. Marshall, I. J.; Noel-Storr, A.; Kuiper, J.; Thomas, J.; and Wallace, B. C. 2018. Machine Learning for Identifying Ran- domized Controlled Trials: An Evaluation and Practitioner’s Guide. Research Synthesis Methods, 9(4): 602–614. Methley, A. M.; Campbell, S.; Chew-Graham, C.; McNally, R.; and Cheraghi-Sohi, S. 2014. PICO, PICOS and SPI- DER: A Comparison Study of Specificity and Sensitivity in Three Search Tools for Qualitative Systematic Reviews. BMC Health Services Research, 14: 579. Michelson, M.; and Reuter, K. 2019. The Significant Cost of Systematic Reviews and Meta-Analyses: A Call for Greater Involvement of Machine Learning to Assess the Promise of Clinical Trials. Contemporary Clinical Trials Communica- tions, 16: 100443. Miwa, M.; Thomas, J.; O’Mara-Eves, A.; and Ananiadou, S. 2014. Reducing Systematic Review Workload through Certainty-Based Screening. Journal of Biomedical Infor- matics, 51: 242–253. Moreno-Garcia, C. F.; Jayne, C.; Elyan, E.; and Aceves- Martins, M. 2023. A Novel Application of Machine Learn- ing and Zero-Shot Classification Methods for Automated

We’d like to thank Ruth Wong at ScHARR for their input and facilitating the invaluable collaboration with ScHARR.


## References

2017.
How Cochrane Is Using Microsoft Technology
to Improve the Efficiency of Systematic Review Produc-
tion. https://www.cochrane.org/news/how-cochrane-using-
microsoft-technology-improve-efficiency-systematic-
review-production. Accessed: 2023-05-07.
Aghajanyan, A.; Zettlemoyer, L.; and Gupta, S. 2020. Intrin-
sic Dimensionality Explains the Effectiveness of Language
Model Fine-Tuning. arXiv:2012.13255.
Bird, S.; Klein, E.; and Loper, E. 2009. Natural language
processing with Python: analyzing text with the natural lan-
guage toolkit. ” O’Reilly Media, Inc.”.
Brown, T. B.; Mann, B.; Ryder, N.; Subbiah, M.; Kaplan, J.;
Dhariwal, P.; Neelakantan, A.; Shyam, P.; Sastry, G.; Askell,
A.; Agarwal, S.; Herbert-Voss, A.; Krueger, G.; Henighan,
T.; Child, R.; Ramesh, A.; Ziegler, D. M.; Wu, J.; Winter,
C.; Hesse, C.; Chen, M.; Sigler, E.; Litwin, M.; Gray, S.;
Chess, B.; Clark, J.; Berner, C.; McCandlish, S.; Radford,
A.; Sutskever, I.; and Amodei, D. 2020. Language Models
are Few-Shot Learners. arXiv:2005.14165.
Cates, C. J.; Stovold, E.; and Welsh, E. J. 2014. How to
Make Sense of a Cochrane Systematic Review.
Breathe,
10(2): 134–144.
Chen, L.; Zaharia, M.; and Zou, J. 2023. How Is ChatGPT’s
Behavior Changing over Time? arxiv:2307.09009.
Chiang, W.-L.; Li, Z.; Lin, Z.; Sheng, Y.; Wu, Z.; Zhang, H.;
Zheng, L.; Zhuang, S.; Zhuang, Y.; Gonzalez, J. E.; Stoica,
I.; and Xing, E. P. 2023. Vicuna: An Open-Source Chatbot
Impressing GPT-4 with 90%* ChatGPT Quality.
Christiano, P. F.; Leike, J.; Brown, T.; Martic, M.; Legg, S.;
and Amodei, D. 2017. Deep reinforcement learning from
human preferences.
Advances in neural information pro-
cessing systems, 30.
Chung, H. W.; Hou, L.; Longpre, S.; Zoph, B.; Tay, Y.; Fe-
dus, W.; Li, Y.; Wang, X.; Dehghani, M.; Brahma, S.; Web-
son, A.; Gu, S. S.; Dai, Z.; Suzgun, M.; Chen, X.; Chowd-
hery, A.; Castro-Ros, A.; Pellat, M.; Robinson, K.; Valter,
D.; Narang, S.; Mishra, G.; Yu, A.; Zhao, V.; Huang, Y.;
Dai, A.; Yu, H.; Petrov, S.; Chi, E. H.; Dean, J.; Devlin, J.;
Roberts, A.; Zhou, D.; Le, Q. V.; and Wei, J. 2022. Scaling
Instruction-Finetuned Language Models. arxiv:2210.11416.
Dettmers, T.; Lewis, M.; Shleifer, S.; and Zettlemoyer, L.
2021. 8-bit optimizers via block-wise quantization. arXiv
preprint arXiv:2110.02861.
Dettmers, T.; Pagnoni, A.; Holtzman, A.; and Zettlemoyer,
L. 2023. QLoRA: Efficient Finetuning of Quantized LLMs.
ArXiv:2305.14314 [cs].
Devlin, J.; Chang, M.-W.; Lee, K.; and Toutanova, K. 2019.
BERT: Pre-training of Deep Bidirectional Transformers for
Language Understanding. In Proceedings of the 2019 Con-
ference of the North American Chapter of the Association

Layer. In 5th International Conference on Learning Repre- sentations, ICLR 2017, Toulon, France, April 24-26, 2017, Conference Track Proceedings. OpenReview.net. Shemilt, I.; Khan, N.; Park, S.; and Thomas, J. 2016. Use of Cost-Effectiveness Analysis to Compare the Efficiency of Study Identification Methods in Systematic Reviews. Sys- tematic Reviews, 5(1): 140. Syriani, E.; David, I.; and Kumar, G. 2023. Assessing the Ability of ChatGPT to Screen Articles for Systematic Re- views. Taori, R.; Gulrajani, I.; Zhang, T.; Dubois, Y.; Li, X.; Guestrin, C.; Liang, P.; and Hashimoto, T. B. 2023. Stanford Alpaca: An Instruction-following LLaMA model. https: //github.com/tatsu-lab/stanford alpaca. Tawfik, G. M.; Dila, K. A. S.; Mohamed, M. Y. F.; Tam, D. N. H.; Kien, N. D.; Ahmed, A. M.; and Huy, N. T. 2019. A Step by Step Guide for Conducting a Systematic Review and Meta-Analysis with Simulation Data. Tropical Medicine and Health, 47(1): 46. Touvron, H.; Lavril, T.; Izacard, G.; Martinet, X.; Lachaux, M.-A.; Lacroix, T.; Rozi`ere, B.; Goyal, N.; Hambro, E.; Azhar, F.; et al. 2023. Llama: Open and efficient founda- tion language models. arXiv preprint arXiv:2302.13971. Vu, T.; Wang, T.; Munkhdalai, T.; Sordoni, A.; Trischler, A.; Mattarella-Micke, A.; Maji, S.; and Iyyer, M. 2020. Ex- ploring and Predicting Transferability across NLP Tasks. In Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP), 7882–7926. On- line: Association for Computational Linguistics. Wallace, B. C.; Noel-Storr, A.; Marshall, I. J.; Cohen, A. M.; Smalheiser, N. R.; and Thomas, J. 2017. Identifying Re- ports of Randomized Controlled Trials (RCTs) via a Hy- brid Machine Learning and Crowdsourcing Approach. Jour- nal of the American Medical Informatics Association, 24(6): 1165–1168. Wallace, B. C.; Small, K.; Brodley, C. E.; Lau, J.; and Trikalinos, T. A. 2012. Deploying an Interactive Machine Learning System in an Evidence-Based Practice Center: Ab- strackr. Wallace, B. C.; Trikalinos, T. A.; Lau, J.; Brodley, C.; and Schmid, C. H. 2010. Semi-Automated Screening of Biomedical Citations for Systematic Reviews. BMC Bioin- formatics, 11(1): 55. Wang, S.; Scells, H.; Koopman, B.; and Zuccon, G. 2022. Neural Rankers for Effective Screening Prioritisation in Medical Systematic Review Literature Search. In Proceed- ings of the 26th Australasian Document Computing Sympo- sium, 1–10. Wang, S.; Scells, H.; Koopman, B.; and Zuccon, G. 2023. Can ChatGPT Write a Good Boolean Query for Systematic Review Literature Search? arxiv:2302.03495. Wei, J.; Bosma, M.; Zhao, V. Y.; Guu, K.; Yu, A. W.; Lester, B.; Du, N.; Dai, A. M.; and Le, Q. V. 2022. FINETUNED LANGUAGE MODELS ARE ZERO-SHOT LEARNERS. Wolf, S. L.; Sattin, R. W.; O’Grady, M.; Freret, N.; Ricci, L.; Greenspan, A. I.; Xu, T.; and Kutner, M. 2001. A Study


## Abstract Screening in Systematic Reviews. Decision Ana-

lytics Journal, 6: 100162.
Nguyen, T.; Rosenberg, M.; Song, X.; Gao, J.; Tiwary, S.;
Majumder, R.; and Deng, L. 2016. MS MARCO: A Hu-
man Generated MAchine Reading COmprehension Dataset.
CoRR, abs/1611.09268.
Olofsson, H.; Brolund, A.; Hellberg, C.; Silverstein, R.;
Stenstr¨om, K.; ¨Osterberg, M.; and Dagerhamn, J. 2017. Can
Abstract Screening Workload Be Reduced Using Text Min-
ing? User Experiences of the Tool Rayyan. Research Syn-
thesis Methods, 8(3): 275–280.
OpenAI. 2023. GPT-4 Technical Report. arXiv:2303.08774.
Ouyang, L.; Wu, J.; Jiang, X.; Almeida, D.; Wainwright, C.;
Mishkin, P.; Zhang, C.; Agarwal, S.; Slama, K.; Ray, A.;
et al. 2022. Training language models to follow instructions
with human feedback. Advances in Neural Information Pro-
cessing Systems, 35: 27730–27744.
Pedregosa, F.; Varoquaux, G.; Gramfort, A.; Michel, V.;
Thirion, B.; Grisel, O.; Blondel, M.; Prettenhofer, P.; Weiss,
R.; Dubourg, V.; et al. 2011. Scikit-learn: Machine learning
in Python. Journal of machine learning research, 12(Oct):
2825–2830.
Przybyła, P.; Brockmeier, A. J.; Kontonatsios, G.; Le Pogam,
M.-A.; McNaught, J.; von Elm, E.; Nolan, K.; and Anani-
adou, S. 2018. Prioritising References for Systematic Re-
views with RobotAnalyst: A User Study. Research Synthesis
Methods, 9(3): 470–488.
Qin, X.; Liu, J.; Wang, Y.; Liu, Y.; Deng, K.; Ma, Y.; Zou,
K.; Li, L.; and Sun, X. 2021. Natural Language Processing
Was Effective in Assisting Rapid Title and Abstract Screen-
ing When Updating Systematic Reviews. Journal of Clinical
Epidemiology, 133: 121–129.
Qureshi, R.; Shaughnessy, D.; Gill, K. A. R.; Robinson,
K. A.; Li, T.; and Agai, E. 2023. Are ChatGPT and Large
Language Models “the Answer” to Bringing Us Closer to
Systematic Review Automation? Systematic Reviews, 12(1):
72.
Raffel, C.; Shazeer, N.; Roberts, A.; Lee, K.; Narang, S.;
Matena, M.; Zhou, Y.; Li, W.; and Liu, P. J. 2019. Exploring
the Limits of Transfer Learning with a Unified Text-to-Text
Transformer. CoRR, abs/1910.10683.
Sadri, N.; and Cormack, G. V. 2022.
Continuous Active
Learning Using Pretrained Transformers. arxiv:2208.06955.
Sanh, V.; Webson, A.; Raffel, C.; Bach, S. H.; Sutawika, L.;
Alyafeai, Z.; Chaffin, A.; Stiegler, A.; Scao, T. L.; Raja, A.;
Dey, M.; Bari, M. S.; Xu, C.; Thakker, U.; Sharma, S. S.;
Szczechla, E.; Kim, T.; Chhablani, G.; Nayak, N.; Datta, D.;
Chang, J.; Jiang, M. T.-J.; Wang, H.; Manica, M.; Shen, S.;
Yong, Z. X.; Pandey, H.; Bawden, R.; Wang, T.; Neeraj, T.;
Rozen, J.; Sharma, A.; Santilli, A.; Fevry, T.; Fries, J. A.;
Teehan, R.; Bers, T.; Biderman, S.; Gao, L.; Wolf, T.; and
Rush, A. M. 2022. Multitask Prompted Training Enables
Zero-Shot Task Generalization. arxiv:2110.08207.
Shazeer, N.; Mirhoseini, A.; Maziarz, K.; Davis, A.; Le,
Q. V.; Hinton, G. E.; and Dean, J. 2017. Outrageously Large
Neural Networks: The Sparsely-Gated Mixture-of-Experts

Design to Investigate the Effect of Intense Tai Chi in Re- ducing Falls among Older Adults Transitioning to Frailty. Controlled Clinical Trials, 22(6): 689–704.

I am screening papers for a systematic literature review. The topic of the systematic review is {TOPIC}. The objectives of the systematic review are {OBJECTIVES} The selection criteria of the review is {SELECTION CRITERIA} The study should focus exclusively on this topic. Decide if the article should be included or excluded from the systematic review. I give the title and abstract of the article as input. Only answer Included or Excluded. Be lenient. I prefer including papers by mistake rather than excluding them by mistake. Title: {TITLE} Abstract: {ABSTRACT}

Yang, E.; MacAvaney, S.; Lewis, D. D.; and Frieder, O. 2022. Goldilocks: Just-Right Tuning of BERT for Technology-Assisted Review. arxiv:2105.01044.

Zhao, S.; Su, C.; Lu, Z.; and Wang, F. 2021. Recent Ad- vances in Biomedical Literature Mining. Briefings in Bioin- formatics, 22(3): bbaa057.

A Runtime Inference Analysis


> **Figure 6: Prompt used to query ChatGPT as defined in Syr-**

> iani, David, and Kumar (2023). To fit the specificity of our
task we also provide the additional information of the Ob-
jectives and Selection Criteria for the systematic review.

Batch Size Memory Usage (GB) Time/Sample (s) 1 12.8 1.39 2 18.0 1.39 3 23.1 1.13


> **Table 3: Metrics for runtime efficiency of our instruction**

> pretrained, single task model with multiple batch sizes, av-
eraged across 100 samples. All tests were carried out on the
same RTX 3090.

I am screening papers for a systematic literature review. The topic of the systematic review is {TOPIC}. The objectives of the systematic review are {OBJECTIVES} The selection criteria of the review is {SELECTION CRITERIA} The study should focus exclusively on this topic and be within this selection criteria. The following article has been excluded. Please provide the reason why it has been excluded as best you can. I give the abstract of the article as input. Only answer Included or Excluded. Be concise and only provide a single reason. Abstract: {ABSTRACT}

Bio-SIEVE is not useful if it is not easily accessible and efficient for reviewers to utilise. We ran performance anal- ysis for our most promising model, the Guanaco7b Single variant, on an RTX 3090. As all models have the same num- ber of parameters and architecture, this evaluation will trans- fer to all variants. Inference was carried out with 1 beam, no sampling and a temperature of 0 with each sample using the entire 2048 tokens in the LLaMA context length, therefore representing the worst case scenario. We measured maxi- mum memory usage and time taken per sample for a batch size of 1, 2 and 3, averaging for each over 100 samples. Note that x-formers was also installed which improves per- formance of the attention mechanism. Results can be found in Table 3.


> **Figure 7: Prompt used to query ChatGPT for exclusion rea-**

> soning.

We find that the model performs with satisfactory speeds to apply on the scale of SR, with only minimal improve- ments with increased batch size. Memory usage shows that Bio-SIEVE will fit onto the memory of mid-end cards such as the RTX 2080ti but will need a reduced context length to ensure it does not go over 12GB memory usage. For higher- end consumer cards this should not become a problem.

C Data Preprocessing

Refer to Algorithm 1 for the strategy for tokenisation and preprocessing of prompts for the Instruct Cochrane dataset.

D Prompt-Section Token Length Analysis

See Table 4 for a detailed break down of the minimum, max- imum and average token length for each different section rel- evant and obtainable from the cochrane library for each re- view. We ultimately utilised Objectives Short, Selection Cri- teria Short and Study Abstract but the analysis of other sec- tions in the prompt could potentially improve performance, especially with greater crossover with PICOS. However, we chose not to use them as they were generally noisier and in- volved more truncation.

B ChatGPT Prompts

Refer to Figure 6 for the prompt used for querying Chat- GPT for the inclusion/exclusion classification task. Also see Figure 7 for exclusion reasoning. Both prompts are adapted from Syriani, David, and Kumar (2023).

Algorithm 1: Instruct Cochrane Preprocessing Input: Review with associated Included & Excluded studies Parameter: Max token length m, Prompt template token length p, Instruction template token length l, Tokeniser T Output: list of Instructions, Inputs & Outputs sets

1: Set S to EMPTY LIST 2: Assume valid Objectives o & Selection Criteria s 3: for all studies do 4: Assume valid Abstract a 5: Remove colons 6: Tokenise o, s and a with T 7: Concatenate o, s and a into x 8: while |x| + p + l > m do 9: z := max(|o|, |s|, |a|) 10: if the last third of z contains a full stop then 11: Truncate on full stop 12: else 13: Naively truncate 14: end if 15: end while 16: Construct input i from prompt template 17: Construct task specific output y 18: Append instruction, i and y to S 19: end for 20: return S

E Detailed Topic Distributions Refer to Table 5 for an exact breakdown of the number of samples in each topic on the Cochrane Library for both the Train and Test splits. Table 6 shows the more fine-grained topic of each of the 13 reviews within Subset.

F Training Analysis Training Analysis Following the work in Yang et al. (2022), we carried out an analysis of the models performance across epochs in order to select ”just right” fine-tuning amount to sustain generalisation. Figure 8 depicts the performance of each of the model variants over all 8 epochs for the Test set whilst Figure 9 shows similar performance on the Safety- first set. Trends are consistent between sets but notable is the generally higher variance between include and exclude on the Safety-first set. Also the third epoch of the Guanaco7B single variant showing a sacrifice in Test set performance increasing leniency and improving Safety-first performance.

We used this method to pick our ”just right” tuning for each model based on safety-first performance. This meant we chose epoch 8 for LLaMA7B Multi and Guanaco7B Multi, epoch 3 for LLaMA7B Single and epoch 7 for Guanaco7B Single. Interestingly we found that single task training overfit without instruction pretraining but did not with instruction pretraining. Additionally, multi-task train- ing tended to result in larger fluctuation in performance be- tween epochs which we hypothesis to be the model changing priority between tasks.

Objectives Selection Criteria Study Title Short Long Short Studies Pop. Intervention Outcome Title Abstract Mean 20.83 56.41 93.49 80.20 102.03 145.75 271.12 224.12 31.76 447.21 Max 77 481 3,227 394 1,624 2,474 4,351 9,956 151 68,340 Min 5 13 12 8 0 0 0 0 2 1


> **Table 4: Length of dataset fields according to tokenized length using the LLaMA tokenizer. The final prompt only utilised the**

> short Objectives and Selection Criteria plus the study’s Abstract. We leave utilisation of the other fields in the extension and
alteration of the prompt to further work.

Topic Train Test Child Health 45488 267 Cancer 10184 155 Lungs & Airways 4968 93 Heart & Circulation 3915 74 Infectious Disease 3487 59 Gynaecology 2592 38 Allergy & Intolerance 1792 13 Tobacco, Drugs & Alcohol 1497 66 Genetic Disorders 1401 44 Endocrine & Metabolic 1145 6 Dentistry & Oral Health 1108 4 Gastroenterology & Hepatology 1073 24 Pain & Anaesthesia 785 - Mental Health 759 8 Effective Practice & Health Systems 728 20 Pregnancy & Childbirth 699 5 Consumer & Communication Strategies 680 19 Developmental, Psychosocial & Learning Problems 634 35 Eyes & Vision 577 10 Neurology 507 - Ear, Nose & Throat 443 5 Complementary & Alternative Medicine 421 5 Neonatal Care 328 1 Insurance Medicine 325 1 Orthopaedics & Trauma 261 24 Rheumatology 232 5 Skin Disorders 216 1 Urology 199 5 Reproductive & Sexual Health 190 - Public Health 178 - Kidney Disease 160 1 Diagnosis 140 15 Wounds 119 4 Health & Safety at Work 82 - Health Professional Education 40 - Methodology 12 - Blood Disorders 10 -


> **Table 5: Number of samples for each topic in the train and test sets.**

No. Specific Topic DOI 0 Oral Health https://doi.org/10.1002/14651858.CD012213.pub2 1 Public Health https://doi.org/10.1002/14651858.CD011677.pub2 2 Developmental, Psychosocial and Learning Problems https://doi.org/10.1002/14651858.CD012955.pub2 3 Bone, Joint and Muscle Trauma https://doi.org/10.1002/14651858.CD012424.pub2 4 Urology https://doi.org/10.1002/14651858.CD011673.pub2 5 Developmental, Psychosocial and Learning Problems https://doi.org/10.1002/14651858.CD008524.pub4 6 Gynaecology and Fertility https://doi.org/10.1002/14651858.CD012165 7 Gynaecological, Neuro-oncology and Orphan Cancer https://doi.org/10.1002/14651858.CD013261.pub2 8 Haematology https://doi.org/10.1002/14651858.CD010981.pub2 9 Effective Practice and Organisation of Care https://doi.org/10.1002/14651858.CD009149.pub3 10 Drugs and Alcohol https://doi.org/10.1002/14651858.CD003020.pub3 11 Cystic Fibrosis and Genetic Disorders https://doi.org/10.1002/14651858.CD002008.pub5 12 Stroke/Heart https://doi.org/10.1002/14651858.CD013650.pub2


> **Table 6: List of Reviews within the Review Subset with their Specific Topic areas and DOIs**


> **Figure 8: The f1-score performance for different metrics of the different model training regimes across epochs on the Test set.**


> **Figure 9: The f1-score performance for different metrics of the different model training regimes across epochs on the Safety-**

> first set.
