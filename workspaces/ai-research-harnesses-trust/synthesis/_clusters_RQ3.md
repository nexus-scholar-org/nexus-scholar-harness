# Consensus clusters touching RQ3 (70 total)


## [C32] verdict=HIGH_CONSENSUS bucket=high_consensus score=0.667 claims=3
### No validation data are reported; this is a system description not a validation study, and formal validation reproducing published Cochrane reviews is described as essential before routine use.
Supporting studies: SCI-000102, SCI-000122, SCI-000142
Member claims:
- (RQ3|NEGATIVE) Clinician assessment of 8 clinical cases found the system could generate conclusions consistent with tumor board recommendations with complete evidence reliability, though case-level evaluation was limited in scope. -- [SCI-000102#methods-clinician-s-assessment-for-case-#FULLTEXT-091]
- (RQ1|NEUTRAL) All intermediate outputs — rule sets, function plans, parsed field values, and trial-level filtering outcomes — are logged, providing a complete audit trail from the original clinical query to the final selected studies. -- [SCI-000122#2-1-trial-selection-and-structuring#FULLTEXT-218]
- (RQ3|NEGATIVE) No validation data are reported; this is a system description not a validation study, and formal validation reproducing published Cochrane reviews is described as essential before routine use. -- [SCI-000142#abstract-results-and-conclusion#FULLTEXT-368]

## [C72] verdict=HIGH_CONSENSUS bucket=high_consensus score=0.667 claims=4
### On the Dementia-Sport dataset the Bi-LSTM baseline achieved 87% accuracy for identifying PICOS-compliant abstracts, illustrating the utility of automated screening for filtering clearly non-compliant studies early in the pipeline.
Supporting studies: SCI-000138, SCI-000140, SCI-000181
Member claims:
- (RQ3|NEUTRAL) On the Dementia-Sport dataset the Bi-LSTM baseline achieved 87% accuracy for identifying PICOS-compliant abstracts, illustrating the utility of automated screening for filtering clearly non-compliant studies early in the pipeline. -- [SCI-000138#results#FULLTEXT-335]
- (RQ3|NEUTRAL) The transformer-based multi-task classifier achieved study design classification accuracy of 95.7%, while the Bi-LSTM baseline reached 87% accuracy for PICOS compliance detection, evidencing robust automated screening performance. -- [SCI-000138#abstract#FULLTEXT-336]
- (RQ3|POSITIVE) In the HCP self-evolving episode, Brain Researcher evaluated 116 candidate prediction-pipeline configurations for Cognition (104 returned scored results), and the researcher-frozen selected workflow achieved a higher pooled out-of-fold correlation than a matched reconstruction of the published procedure across 10 repeated same-cohort nested-cross-validation splits (median Δr = .098; conditional one-sided p = .006), higher in all 10 runs. -- [SCI-000140#results-self-evolving-research-episodes#FULLTEXT-349]
- (RQ3|POSITIVE) Benchmark testing against standardized datasets including BioASQ shows the integrated LLM+RAG approach achieves good accuracy on factoid, list and yes/no questions, representing an improvement over previous state-of-the-art approaches. -- [SCI-000181#evaluation#FULLTEXT-494]

## [C78] verdict=HIGH_CONSENSUS bucket=high_consensus score=0.667 claims=7
### Across 17,443 generated citations, no model exceeds a citation-level existence rate of 0.475, with Temporal and Combo conditions producing the steepest drops while outputs remain format-compliant.
Supporting studies: SCI-000144, SCI-000154, SCI-000159
Member claims:
- (RQ2|NEGATIVE) Across 17,443 generated citations, no model exceeds a citation-level existence rate of 0.475, with Temporal and Combo conditions producing the steepest drops while outputs remain format-compliant. -- [SCI-000144#abstract#FULLTEXT-373]
- (RQ2|NEGATIVE) Manual validation of the pipeline on a stratified sample of 100 citations gave overall agreement of 75% and Cohen's kappa 0.63, with precision 0.97 for Existing, 0.88 for Fabricated but only 0.43 for Unresolved; the dominant error was Unresolved-to-Fabricated (16 cases). -- [SCI-000144#4-verification-pipeline-pipeline-validat#FULLTEXT-374]
- (RQ2|NEGATIVE) Under the Temporal condition every model produces well-formed bibliographic entries respecting the requested year window, yet GPT-4o's existence rate drops from 0.235 to 0.019, so format compliance masks a near-complete loss of verifiability ('compliance without substance'). -- [SCI-000144#6-discussion#FULLTEXT-379]
- (RQ3|NEGATIVE) In the audit, only 15 of 35 'Unresolved' citations were truly unresolved; 16 of 35 were fabricated and 4 of 35 were existing — so the category should not be read as 'nearly correct,' and reported fabricated rates are likely underestimates. -- [SCI-000144#5-results-sensitivity-to-reclassifying-u#FULLTEXT-381]
- (RQ3|NEUTRAL) The proprietary-open-weight gap in citation existence rate is large and statistically clear (delta = +0.229 at Baseline, up to +0.310 under Survey prompting), persistent across all conditions and across every domain group. -- [SCI-000144#5-results#FULLTEXT-383]
- (RQ2|NEUTRAL) In experiments, GPT-4o fabricated citations in 78-90% of cases when asked to cite recent literature across fields such as computer science and biomedicine, whereas OpenScholar achieved citation accuracy on par with human experts, addressing a key hallucination/verifiability risk. -- [SCI-000154#introduction#FULLTEXT-414]
- (RQ3|NEGATIVE) Limitation: OpenScholar does not consistently retrieve the most representative or relevant papers for certain queries; expert annotators noted citations were occasionally outdated or less relevant. -- [SCI-000159#limitations#FULLTEXT-446]

## [C46] verdict=HIGH_CONSENSUS bucket=high_consensus score=0.6 claims=6
### Single-task models were higher performing, with Guanaco7B-Single outperforming all other models by at least 0.07 accuracy while preserving the highest inclusion recall.
Supporting studies: SCI-000111, SCI-000115, SCI-000121, SCI-000127, SCI-000137
Member claims:
- (RQ3|NEUTRAL) Open-source zero-shot models are unsuitable for screening after performing very poorly on the irrelevancy test (Guanaco7B achieving only 0.02), confirming fine-tuning is necessary. -- [SCI-000111#body#FULLTEXT-156]
- (RQ3|POSITIVE) Single-task models were higher performing, with Guanaco7B-Single outperforming all other models by at least 0.07 accuracy while preserving the highest inclusion recall. -- [SCI-000111#body#FULLTEXT-157]
- (RQ2|NEGATIVE) A contamination check on documents published after the model providers' training cutoffs showed no evidence that prior exposure inflated the reported extraction results. -- [SCI-000115#abstract#FULLTEXT-174]
- (RQ3|NEUTRAL) LLMs (GPT-3.5 Turbo, GPT-4 Turbo, GPT-4o, Llama 3 70B, Gemini 1.5 Pro, and Claude Sonnet 3.5) were trialed across 23 Cochrane Library systematic reviews to evaluate their accuracy in zero-shot binary classification for abstract screening. -- [SCI-000121#abstract#FULLTEXT-217]
- (RQ2|NEGATIVE) A universal vulnerability is documented: every tested model, when fed systematically negated (factually inverted) abstracts in the N-RAG workflow, synthesized the false claims into coherent but false conclusions scoring below even the parametric zero-shot baseline. -- [SCI-000127#4-results-vulnerability-to-misinformatio#FULLTEXT-266]
- (RQ3|NEGATIVE) No individual screening output recovered all 316 verified eligible records, and greater retention of benchmark records did not consistently correspond to greater recovery. -- [SCI-000137#results-rq1-recovery-of-verified-eligibl#FULLTEXT-323]

## [C22] verdict=HIGH_CONSENSUS bucket=high_consensus score=0.5 claims=3
### Named evaluation gap: despite 57 SLRs, LGAR was only reliably tested in the medical domain because other domains in the SYNERGY dataset have too few SLRs to assess performance equivalence.
Supporting studies: SCI-000096, SCI-000164
Member claims:
- (RQ3|NEUTRAL) Evaluation on six SYNERGY datasets showed AUC values ranging from 0.77 to 0.95, with performance varying significantly across datasets due to task heterogeneity, dataset characteristics, and threshold sensitivity. -- [SCI-000096#section-4-1-evaluation-on-synergy-datase#FULLTEXT-058]
- (RQ3|NEUTRAL) Limitation: Performance variability across datasets is attributed to task heterogeneity, dataset size differences, varying inclusion rates (from <1% to 12.36%), and threshold sensitivity — the choice of decision threshold significantly impacts performance. -- [SCI-000096#lattereview-evaluation-performance-varia#FULLTEXT-060]
- (RQ3|NEGATIVE) Named evaluation gap: despite 57 SLRs, LGAR was only reliably tested in the medical domain because other domains in the SYNERGY dataset have too few SLRs to assess performance equivalence. -- [SCI-000164#6-limitations#FULLTEXT-457]

## [C30] verdict=HIGH_CONSENSUS bucket=high_consensus score=0.5 claims=2
### The system exhibited temporal instability with performance declining at -1.9% per day over the evaluation period, an architectural reliability gap.
Supporting studies: SCI-000100, SCI-000102
Member claims:
- (RQ3|NEUTRAL) The system exhibited temporal instability with performance declining at -1.9% per day over the evaluation period, an architectural reliability gap. -- [SCI-000100#body#FULLTEXT-082]
- (RQ3|NEGATIVE) Error analysis reveals three failure types: low logical coherence from assembling fragmented pieces, misalignment with question intent, and inclusion of outdated conclusions, demonstrating that the system does not fully eliminate quality issues. -- [SCI-000102#wang-et-al-deeper-med-expert-evaluation-#FULLTEXT-092]

## [C34] verdict=HIGH_CONSENSUS bucket=high_consensus score=0.5 claims=11
### The platform centers on human-machine collaboration in which the human researcher primarily orchestrates, directs, and reviews AI-supported processes and retains control at all times, rather than aiming for full automation.
Supporting studies: SCI-000107, SCI-000141
Member claims:
- (RQ1|NEUTRAL) ADVISE embeds a fine-tuned BERT AI agent in the human title-and-abstract screening workflow with a screen-update-predict-sample active learning loop, where a priority score PS(p) = softmax(Pred(p))[1] ranks unscreened papers by predicted relevance probability and the human team screens prioritized papers in batches. -- [SCI-000107#methodology-active-learning-query-strate#FULLTEXT-102]
- (RQ1|NEUTRAL) ADVISE preserves human verification of all relevant papers by design: because 'for evidence synthesis, all relevant papers need to be verified by a human agent', the highest-priority papers are sampled first, and the workflow stops screening when ranking similarity or the real-time inclusion rate crosses a threshold. -- [SCI-000107#methodology-active-learning-query-strate#FULLTEXT-103]
- (RQ1|NEUTRAL) The practical interaction cost of the human-AI team is acknowledged as a concrete barrier: time needed to exchange information, label updates, dataset merging, and time lags between human labeling and model updates can mean one team operates with incomplete data. -- [SCI-000107#discussion-the-cost-of-communication#FULLTEXT-105]
- (RQ2|NEUTRAL) ADVISE identifies a trust risk in human-AI screening teams: the cold-start problem, where the AI agent must rank documents before knowing the domain, can lead to distrust if initial rankings are incorrect, and model output quality is bounded by the consistency of human-provided training labels. -- [SCI-000107#discussion-trust-in-ai#FULLTEXT-106]
- (RQ3|NEUTRAL) ADVISE was restricted to title-and-abstract screening because copyright and subscription issues make downloading and using full-text documents infeasible across institutions; full-text screening would require training another BERT model on a new human-generated training dataset. -- [SCI-000107#discussion-automation-of-full-text-scree#FULLTEXT-108]
- (RQ3|NEGATIVE) In the simulated case on a fully labeled 68,539-document dataset targeting an inclusion rate of 80%, the hybrid team achieves the highest efficiency with a training size of 5,000, where human agents need to screen only 25.2% of papers versus 80% without AI guidance, saving 54.8% of human screening effort. -- [SCI-000107#results-simulated-egm-design#FULLTEXT-109]
- (RQ3|NEGATIVE) Incorporating the BERT-based AI agent into the human team reduces human screening effort by 68.5% compared to no AI assistance, and the highest-priority (HP) active-learning sampling strategy reduces human effort further to 78.3% for identifying 80% of all relevant documents. -- [SCI-000107#abstract#FULLTEXT-110]
- (RQ3|POSITIVE) On the three deployed EGMs (Agriculture 221k, Nutrition 117k, Resilience 60k documents), the BERT agent needed 47%, 17%, and 75% less human effort, respectively, than the EPPI-Reviewer SVM baseline to reach an 80% inclusion rate, and BERT achieved higher classification accuracy than SVM for all three EGMs. -- [SCI-000107#results-saved-effort#FULLTEXT-111]
- (RQ3|NEGATIVE) Using records from twelve human screeners (averaging 38.6 papers per hour, SE=1.00) on an agriculture development EGM, the AL-enhanced AI agent saves 1,111.5 hours of title-and-abstract screening versus no AI agent and 229.1 hours versus the EPPI-Reviewer SVM. -- [SCI-000107#results-active-learning-training-size-an#FULLTEXT-112]
- (RQ3|POSITIVE) Using the least-confidence (LC) active-learning strategy produced better classification models (higher F1 score) than random sampling, because sampling the most uncertain papers lets the model learn more efficiently from human labeling. -- [SCI-000107#results-active-learning-training-size-an#FULLTEXT-113]
- (RQ1|NEGATIVE) The platform centers on human-machine collaboration in which the human researcher primarily orchestrates, directs, and reviews AI-supported processes and retains control at all times, rather than aiming for full automation. -- [SCI-000141#4-framework-for-ai-assisted-research-4-2#FULLTEXT-357]

## [C62] verdict=HIGH_CONSENSUS bucket=high_consensus score=0.5 claims=4
### BERTScore fails as a reliability proxy for conclusion quality: it gives nearly identical F1 scores across workflows and rates false N-RAG conclusions as semantically equivalent to correct G-RAG ones.
Supporting studies: SCI-000127, SCI-000181
Member claims:
- (RQ2|NEUTRAL) The RAG paradigm's susceptibility to noisy or factually incorrect retrievals is flagged: models often uncritically synthesize such context, failing to cross-check against parametric knowledge or detect internal contradictions. -- [SCI-000127#2-1-retrieval-augmented-generation-and-m#FULLTEXT-267]
- (RQ2|NEGATIVE) The authors conclude that current models act as 'obedient synthesizers rather than critical reasoners', lacking the ability to detect and reject misinformation based on internal knowledge or logical inconsistency. -- [SCI-000127#4-results-vulnerability-to-misinformatio#FULLTEXT-268]
- (RQ3|NEGATIVE) BERTScore fails as a reliability proxy for conclusion quality: it gives nearly identical F1 scores across workflows and rates false N-RAG conclusions as semantically equivalent to correct G-RAG ones. -- [SCI-000127#6-insufficiency-of-bertscore-similarity-#FULLTEXT-269]
- (RQ3|NEUTRAL) Expert validation through blind testing with domain experts found the system provided answers rated as 'equally or more comprehensive' than manual search in most cases while requiring substantially less researcher time, and identified relevant papers missed by experts in many test cases. -- [SCI-000181#evaluation#FULLTEXT-495]

## [C79] verdict=HIGH_CONSENSUS bucket=high_consensus score=0.5 claims=4
### Cost evaluation: GPT-4o costs approximately $3.16 per 100 articles, GPT-3.5 about $0.22 per 100 articles, while locally-run Gemma 2 and Llama 3 have no cloud cost.
Supporting studies: SCI-000151, SCI-000154
Member claims:
- (RQ1|NEUTRAL) LLAssist supports both local models provisioned via Ollama (Llama 3, Gemma 2) and cloud models (GPT-3.5, GPT-4), letting researchers trade off processing speed, accuracy, and data-privacy concerns. -- [SCI-000151#3-technical-implementation#FULLTEXT-389]
- (RQ3|NEGATIVE) Cost evaluation: GPT-4o costs approximately $3.16 per 100 articles, GPT-3.5 about $0.22 per 100 articles, while locally-run Gemma 2 and Llama 3 have no cloud cost. -- [SCI-000151#5-2-time-and-cost-efficiency#FULLTEXT-393]
- (RQ3|NEUTRAL) Throughput evaluation: LLAssist processes 17–37 articles in under 10 minutes, 115 in 20–50 minutes, and 2,576 in 10–11 hours; GPT-4o is slowest at 24–29 s/article, Llama 3 fastest at 10–11 s/article, Gemma 2 and GPT-3.5 at 12–14 s/article. -- [SCI-000151#5-2-time-and-cost-efficiency#FULLTEXT-399]
- (RQ1|POSITIVE) OpenScholar can enhance off-the-shelf LMs: when GPT-4o is used as the underlying model, OpenScholar-GPT-4o achieves a 12% improvement in correctness compared with GPT-4o alone, demonstrating a pipeline-level boost independent of model weights. -- [SCI-000154#evaluation#FULLTEXT-410]

## [C89] verdict=HIGH_CONSENSUS bucket=high_consensus score=0.5 claims=2
### Manual synthesis of 30 articles is estimated at 50+ hours; the same task was completed in 1 minute 24 seconds using the RAG architecture, demonstrating orders-of-magnitude time reduction.
Supporting studies: SCI-000172, SCI-000179
Member claims:
- (RQ3|NEUTRAL) Manual synthesis of 30 articles is estimated at 50+ hours; the same task was completed in 1 minute 24 seconds using the RAG architecture, demonstrating orders-of-magnitude time reduction. -- [SCI-000172#results-and-discussions#FULLTEXT-468]
- (RQ3|NEGATIVE) In the observed execution, retrieval and preparation stages (S1-S4) processed 20 papers in 21.38 s total, while AI-assisted abstract analysis (S5) required 25.02 s per paper — reported as descriptive rather than comparative performance evidence. -- [SCI-000179#abstract#FULLTEXT-482]

## [C3] verdict=HIGH_CONSENSUS bucket=high_consensus score=0.5 claims=6
### On human clinical studies the domain had the highest accuracy of the three at 82%, attributed to it being the most homogenous domain with all abstracts reporting randomized clinical trials.
Supporting studies: SCI-000056, SCI-000088, SCI-000108, SCI-000115, SCI-000122, SCI-000128
Member claims:
- (RQ3|NEGATIVE) Performance was lowest for the DRKS registry where negative predictive value was 63.4% compared to 82.8% for ClinicalTrials.gov, attributed to fewer registry-side publication links and publication in non-PubMed-indexed journals. -- [SCI-000056#discussion-limitations#FULLTEXT-006]
- (RQ3|NEGATIVE) Deeks' funnel plot asymmetry tests found no evidence of publication bias in either the title/abstract meta-analysis (bias coefficient -1.16, P=0.97) or the full-text meta-analysis (bias coefficient -17.74, P=0.17). -- [SCI-000088#results-meta-analysis#FULLTEXT-029]
- (RQ3|NEUTRAL) On human clinical studies the domain had the highest accuracy of the three at 82%, attributed to it being the most homogenous domain with all abstracts reporting randomized clinical trials. -- [SCI-000108#results#FULLTEXT-121]
- (RQ3|NEUTRAL) Performance declined most on interpretive tasks: forward-looking 'future directions' averaged only 2.9-3.5 out of 5.0, with NotebookLM scoring as low as 1.53 on policy briefs, suggesting models struggle with critical appraisal. -- [SCI-000115#3-results-3-1-model-performance-varies-s#FULLTEXT-179]
- (RQ2|NEGATIVE) FDA approval status — an inherently dynamic filtering criterion — is validated through an agentic retrieval module querying Drugs.com as a curated, versioned reference, rather than trusting model or registry knowledge. -- [SCI-000122#2-1-trial-selection-and-structuring#FULLTEXT-223]
- (RQ3|POSITIVE) BioInsight achieves best QA performance, the highest expert score on BioInsight-100, and stronger expert ratings for traceability, ranking quality, and dashboard usability in disease-level interpretation compared to search-augmented baselines. -- [SCI-000128#introduction-contributions#FULLTEXT-282]

## [C9] verdict=HIGH_CONSENSUS bucket=high_consensus score=0.471 claims=36
### Model selection for LGAR is constrained to open-weights LLMs explicitly to enhance the reproducibility of the results.
Supporting studies: SCI-000088, SCI-000089, SCI-000099, SCI-000106, SCI-000108, SCI-000117, SCI-000122, SCI-000124, SCI-000125, SCI-000126, SCI-000129, SCI-000137, SCI-000146, SCI-000151, SCI-000152, SCI-000156, SCI-000164
Member claims:
- (RQ1|NEGATIVE) The majority of the included studies used off-the-shelf LLMs without task-specific fine-tuning and instead emphasized prompt engineering as the primary optimization strategy, meaning general-purpose LLMs achieved strong screening performance with minimal adaptation. -- [SCI-000088#results-methodological-characteristics-o#FULLTEXT-024]
- (RQ2|NEUTRAL) The review applies PROBAST + AI and QUADAS-2 to rate the methodological quality and risk of bias of the included LLM screening studies; most studies demonstrated low risk of bias, and agreement of screening decisions with human-defined reference standards was the evaluation backbone. -- [SCI-000088#methods-risk-of-bias-and-applicability-a#FULLTEXT-026]
- (RQ2|NEGATIVE) The review finds that LLMs are positioned as assistive, high-sensitivity tools that prioritize potentially relevant studies for human verification rather than replacements for human reviewers. -- [SCI-000088#discussion#FULLTEXT-027]
- (RQ3|NEUTRAL) In 18 included studies, LLMs in title-and-abstract screening achieved pooled sensitivity of 0.92 (95% CI 0.81-0.96, I²=95.82), pooled specificity of 0.94 (95% CI 0.90-0.97, I²=99.90), an SROC AUC of 0.98, and a diagnostic odds ratio of 185, with substantial cross-study heterogeneity. -- [SCI-000088#results-meta-analysis#FULLTEXT-031]
- (RQ3|POSITIVE) Reported efficiency gains for LLM-assisted screening workflows include screening and decision-making time commonly reduced by three-to-five-fold (in some cases by an order of magnitude) and deployment cost often below one tenth of the cost of manual screening. -- [SCI-000088#discussion#FULLTEXT-033]
- (RQ1|NEGATIVE) No task-specific training, fine-tuning, or few-shot examples were used, and the LLM is used only for summarizing articles not for making assessments or proposed action. -- [SCI-000089#methods-procedure#FULLTEXT-035]
- (RQ2|NEGATIVE) Data extraction accuracy was 100% in both LLM and manual conditions as assessed by an independent evaluator who was unaware of group allocation, with no adverse events or participant burden reported. -- [SCI-000089#results-secondary-outcomes#FULLTEXT-037]
- (RQ3|NEGATIVE) Formal output stability under repeated prompting was not assessed, though potential run-to-run variability did not affect trial exposure because all LLM summaries were generated before participant sessions and stored as fixed materials. -- [SCI-000089#discussion-limitations#FULLTEXT-038]
- (RQ3|NEGATIVE) LLM assistance reduced mean task completion time by 7.9 minutes (27.5 vs 34.5 minutes), representing approximately 23% reduction, but the 95% CI included zero (-1.5 to 17.3 minutes; P=0.099) and the study may have been underpowered. -- [SCI-000089#results-primary-outcomes#FULLTEXT-039]
- (RQ2|NEGATIVE) M-Reason integrates deterministic code for validation alongside LLM reasoning; the authors report that combining LLM-driven analysis with deterministic code offers greater confidence but at the expense of speed and flexibility. -- [SCI-000099#6-conclusions#FULLTEXT-068]
- (RQ1|NEUTRAL) The framework adapts recent advances in declarative prompt optimisation, developed for general-purpose LLM applications, and demonstrates their applicability to the domain of SLR automation, described as a novel application of such approaches to SLR pipelines. -- [SCI-000106#abstract#FULLTEXT-093]
- (RQ1|NEUTRAL) The paper argues that current LLM-assisted SLR approaches rely on brittle, manually crafted prompts that compromise reliability and reproducibility, and that this prompt fragility undermines scientific confidence in LLM-assisted evidence synthesis. -- [SCI-000106#abstract#FULLTEXT-095]
- (RQ1|NEUTRAL) The paper notes that LLM performance is highly sensitive to the phrasing of input prompts, making LLM-assisted workflows unreliable, difficult to reproduce, and raising concerns about their scientific validity. -- [SCI-000106#introduction#FULLTEXT-097]
- (RQ3|NEUTRAL) The paper reports that subtle variations in prompt formats can result in differences as large as 76 accuracy points on tasks from the Super-NaturalInstructions benchmark, quantifying prompt fragility and its impact on reliability. -- [SCI-000106#introduction#FULLTEXT-101]
- (RQ2|NEGATIVE) The study reports a case where the LLM hallucinated the study design, labeling an abstract as a 'Randomized controlled trial' when there was no mention of random allocation, evidencing a factual-extraction hallucination risk in SLR automation. -- [SCI-000108#results#FULLTEXT-119]
- (RQ3|NEGATIVE) Evaluation on LoQA uses DeepSeek-V3.2 as the LLM judge for Argument Sufficiency and Detail Preservation (temperature 0), and DeepResearch Bench uses Gemini-2.5-Pro for RACE and Gemini-2.5-Flash for FACT — evidence that the reported metrics are LLM-judged rather than human-scored. -- [SCI-000117#4-experiments-4-3-implementation-details#FULLTEXT-194]
- (RQ1|NEUTRAL) EligMeta separates LLM-based reasoning/orchestration from deterministic, version-controlled execution of numerically critical operations (trial selection, eligibility-weight computation, statistical estimation) to guarantee reproducibility and transparency. -- [SCI-000122#1-introduction#FULLTEXT-220]
- (RQ2|NEGATIVE) The hybrid architecture is argued to reduce hallucination risk while allowing LLM integration in high-stakes biomedical applications without sacrificing reliability. -- [SCI-000122#4-discussion#FULLTEXT-224]
- (RQ3|NEUTRAL) Performance was strongest for explicitly stated criteria, moderate for structural requirements, and weakest for inference-heavy tasks such as linearity and sensitivity analyses. -- [SCI-000124#body#FULLTEXT-240]
- (RQ2|NEGATIVE) Experimental results show that even the most advanced evaluated LLMs still generate hallucinated references despite recent progress. -- [SCI-000125#abstract#FULLTEXT-242]
- (RQ3|NEUTRAL) BIORESEARCHER is not uniformly dominant at every layer: CellType achieves a higher L2 pass rate (77.48% vs 68.47-74.77%) on qualitative-synthesis questions, and frontier LLMs plateau near a 68% L1 ceiling, showing specialized systems can match or exceed a broader orchestrator for narrow fact retrieval. -- [SCI-000126#evaluation#FULLTEXT-258]
- (RQ2|POSITIVE) Prompt design sensitivity was demonstrated: the screening prompt was refined 4 times and extraction prompt refined 6 times to improve precision and reduce ambiguity, showing LLM performance is highly sensitive to prompt wording. -- [SCI-000129#section-4-2-adjustments-during-conductio#FULLTEXT-289]
- (RQ3|NEGATIVE) LLM effectiveness is task-dependent: Gemini PRO achieved 90% in extraction and screening, Manus 98% in screening but only 40% in extraction, and Copilot 60% in both — model selection should be treated as a methodological decision. -- [SCI-000129#section-4-3-tests-with-other-models-sect#FULLTEXT-291]
- (RQ3|NEUTRAL) Time reduction was substantial: manual screening took ~23 days, LLM-assisted screening took ~9 hours (98% reduction); manual extraction took ~7 days, LLM-assisted took ~1 hour (99% reduction). -- [SCI-000129#section-4-1-comparison-of-time-and-accur#FULLTEXT-293]
- (RQ1|NEUTRAL) The analysis code, benchmark input data, LLM prompts, screening outputs, and comprehensive analytical results are archived in open supplementary materials, allowing reported comparisons to be reconstructed. -- [SCI-000137#methods-software-and-computational-repro#FULLTEXT-318]
- (RQ3|NEGATIVE) The study supports using LLMs as documented, auditable, and human-supervised components of evidence-synthesis workflows rather than as autonomous replacements for human screening judgement. -- [SCI-000137#conclusion#FULLTEXT-326]
- (RQ2|NEGATIVE) LLMs do not always perform well in mathematical reasoning tasks, which raises questions about whether their probability outputs for screening decisions are meaningful. -- [SCI-000146#abstract#FULLTEXT-384]
- (RQ3|NEGATIVE) Four LLMs were evaluated for their accuracy in title/abstract screening based on their probability outputs, motivated by the concern that LLM probability scores may not be meaningful. -- [SCI-000146#abstract#FULLTEXT-385]
- (RQ2|NEUTRAL) LLAssist requires its LLMs to output reasoning for every relevance/contribution judgment, which doubles as a cognitive forcing function acting as a checkpoint before downstream processing. -- [SCI-000151#4-1-4-reasoning-quality#FULLTEXT-391]
- (RQ3|NEUTRAL) The authors concede the accuracy assessment was conducted in an uncontrolled environment and position LLAssist as a lightweight filtering aid to be used alongside established methodologies such as PRISMA. -- [SCI-000151#2-2-5-preliminary-nature-of-evaluation#FULLTEXT-398]
- (RQ2|NEUTRAL) The authors conclude that while LLMs were not trustworthy as independent reviewers, they improved the human results by reducing the number of false negatives and false positives after rescreening was completed. -- [SCI-000152#discussion#FULLTEXT-401]
- (RQ3|POSITIVE) The LLM-assisted screening required almost half of the time and costs than the screening completed by two human raters, yet the two human raters outperformed the LLM-assisted rater in rescreening rate even in a worst-case scenario. -- [SCI-000152#conclusions#FULLTEXT-406]
- (RQ3|NEUTRAL) The two LLMs completed the same screening task almost 25 times faster than the human rater, and LLM-assisted screening took 21 hours versus 37 hours for two human raters, with the combined cost of two LLMs being 3.26 USD versus an estimated 492.18 USD for two human raters. -- [SCI-000152#discussion#FULLTEXT-409]
- (RQ3|NEGATIVE) User evaluation of the LLM-based UI used only four research articles as input, with no quantitative metrics or inter-rater reliability reported. -- [SCI-000156#body#FULLTEXT-430]
- (RQ1|POSITIVE) Model selection for LGAR is constrained to open-weights LLMs explicitly to enhance the reproducibility of the results. -- [SCI-000164#5-1-model-selection-and-experimental-set#FULLTEXT-451]
- (RQ3|NEGATIVE) Named risk of the approach: applying LGAR to define a cut-off in the ranked list could cause a relevant paper to be overlooked — the primary failure mode identified for LLM-based abstract screening. -- [SCI-000164#6-limitations#FULLTEXT-458]

## [C13] verdict=ACTIVE_DEBATE bucket=active_debates score=0.25 claims=4
### Structured field extraction achieved 35.1% higher semantic similarity than PDF chunking, statistically significant at p < 0.000001, across 643 observations from 60 testing sessions.
Supporting studies: SCI-000090, SCI-000100, SCI-000110, SCI-000128
Member claims:
- (RQ1|NEGATIVE) Schema-constrained extraction uses fixed prompts and structured enumerations rather than free generation, with conservative missingness handling (returning 'NR') to minimize fabrication and ensure deterministic outputs. -- [SCI-000090#discussion-limitations#FULLTEXT-042]
- (RQ3|POSITIVE) Structured field extraction achieved 35.1% higher semantic similarity than PDF chunking, statistically significant at p < 0.000001, across 643 observations from 60 testing sessions. -- [SCI-000100#abstract#FULLTEXT-080]
- (RQ2|NEUTRAL) The LangGraph module minimized hallucination by mapping retrieved texts back to the original user queries, drastically reducing irrelevant or fabricated outputs common in standalone LLM-generated answers. -- [SCI-000110#3-3-document-relevance-and-hallucination#FULLTEXT-141]
- (RQ1|NEUTRAL) The reasoning-note schema requires the Reasoning Agent to state what the pathway does, why it matters for the disease, which input proteins drive the interpretation, which interaction modules support the mechanism, and where evidence is weak or indirect. -- [SCI-000128#appendix-a-2-intermediate-artifacts-and-#FULLTEXT-278]

## [C90] verdict=ACTIVE_DEBATE bucket=active_debates score=0.333 claims=3
### The AI-assisted abstract review (including abstract verification, bilingual Thai/English summarization, and structured output parsing) took 25.02 s per paper, inclusive of a 2-second intentional delay for API rate regulation.
Supporting studies: SCI-000172, SCI-000179, SCI-000186
Member claims:
- (RQ3|NEGATIVE) Validation results ranged from 76% (Romanian, Exp #1) to 94% (AI-generated English, Exp #4), with Romanian consistently performing worse than English (~90-95% gap); cross-document synthesis questions yielded slightly lower results. -- [SCI-000172#table-6-study-results-results-and-discus#FULLTEXT-469]
- (RQ3|NEUTRAL) The AI-assisted abstract review (including abstract verification, bilingual Thai/English summarization, and structured output parsing) took 25.02 s per paper, inclusive of a 2-second intentional delay for API rate regulation. -- [SCI-000179#results-and-discussion-ai-assisted-abstr#FULLTEXT-484]
- (RQ3|POSITIVE) In an end-to-end evaluation, all six EvoScientist-authored manuscripts submitted to ICAIS 2025 were accepted against a track-wide acceptance rate of 31.71% (26 of 82 submissions), with one Best Paper and one AI Reviewer's Appraisal Award. -- [SCI-000186#5-3-end-to-end-scientific-discovery-perf#FULLTEXT-507]

## [C10] verdict=ACTIVE_DEBATE bucket=active_debates score=0.4 claims=7
### To support repeatability, the study fixed conservative generation parameters for GPT-4 - temperature=0, frequency_penalty=0, presence_penalty=0, top_p=0.95 - aiming for maximum repeatability across repeated requests.
Supporting studies: SCI-000088, SCI-000108, SCI-000110, SCI-000120, SCI-000127
Member claims:
- (RQ3|NEGATIVE) Comparing GPT-4T and GPT-4o (4 and 5 studies respectively), pooled sensitivity was numerically higher for GPT-4o (0.88 vs 0.81, not significant, p=0.45) while GPT-4T's pooled specificity (0.99) was significantly higher than GPT-4o's (0.94, p < 0.01), and no model-level covariate effect was significant in the joint model. -- [SCI-000088#results-subgroup-analysis-and-meta-regre#FULLTEXT-028]
- (RQ3|NEGATIVE) For full-text screening (4 studies), the pooled sensitivity and specificity both reached 0.99 (95% CI 0.95-1.00) with an SROC AUC of 0.99, no heterogeneity in sensitivity (I²=0) but considerable heterogeneity in specificity (I²=92.65). -- [SCI-000088#results-meta-analysis#FULLTEXT-030]
- (RQ3|NEUTRAL) Prompt strategies incorporating examples or chain-of-thought reasoning significantly improved sensitivity: pooled sensitivity was 0.95 (95% CI 0.92-0.99) in the example/chain-of-thought group versus 0.86 (95% CI 0.78-0.94) in the group without them (p < 0.01). -- [SCI-000088#results-subgroup-analysis-and-meta-regre#FULLTEXT-032]
- (RQ1|NEUTRAL) To support repeatability, the study fixed conservative generation parameters for GPT-4 - temperature=0, frequency_penalty=0, presence_penalty=0, top_p=0.95 - aiming for maximum repeatability across repeated requests. -- [SCI-000108#methods#FULLTEXT-115]
- (RQ3|NEUTRAL) In the RAG-vs-GPT-4 comparison breakdown, RAG-based GPT-3.5 excelled on 25% of queries (especially relationship-centric Neo4j queries), GPT-4's broader capacity won on 20%, and 25% of responses still required further optimization due to multi-layer synthesis complexity. -- [SCI-000110#3-1-performance-of-rag-vs-gpt-4#FULLTEXT-145]
- (RQ3|POSITIVE) For high-expertise depth-of-adaptation-response classification, GPT-4o achieved accuracy of 22.7% and micro-averaged F1 of 0.22 (macro F1 0.17), with agreement with human annotators collapsing as task complexity increases (precision/recall/F1: low 0.88/0.90/0.89, medium 0.40/0.83/0.54, high 0.22/0.22/0.22). -- [SCI-000120#4-results-high-expertise-tasks#FULLTEXT-212]
- (RQ3|POSITIVE) Information-grounding hypothesis (H2) was confirmed: G-RAG conclusions were rated significantly superior to P-CoT across all comparisons (p < 0.04; Cohen's d = 0.48–0.74), with the general-purpose Gemma model rated over a full point higher by humans (Mean Diff = 1.025). -- [SCI-000127#5-2-the-role-of-information-grounding-h2#FULLTEXT-272]

## [C14] verdict=ACTIVE_DEBATE bucket=active_debates score=0.5 claims=7
### On the ketamine/neuroimaging benchmark, the pipeline achieved 100% recall, 97.9% precision, 99.4% accuracy, and 98.9% F1 — the best performance across all three benchmarks.
Supporting studies: SCI-000090, SCI-000115, SCI-000126, SCI-000140
Member claims:
- (RQ2|POSITIVE) On the ketamine/neuroimaging benchmark, the pipeline achieved 100% recall, 97.9% precision, 99.4% accuracy, and 98.9% F1 — the best performance across all three benchmarks. -- [SCI-000090#table-2-pooled-performance-summary#FULLTEXT-045]
- (RQ3|NEGATIVE) In screening, Claude Sonnet 4 achieved the highest accuracy (82.8%) while GPT-5 achieved the highest recall (91.8%) but with specificity collapsing in policy briefs (53.3%); no system led on all tasks. -- [SCI-000115#3-results-3-1-model-performance-varies-s#FULLTEXT-178]
- (RQ3|POSITIVE) BIORESEARCHER obtains the best overall single-step pass rate (83.49%) and average judge score (0.892) on the 109-question suite, surpassing the specialized CellType agent (67.80%, 0.731) and the strongest frontier baseline GPT-5.5 (45.09%, 0.591). -- [SCI-000126#evaluation#FULLTEXT-259]
- (RQ3|NEUTRAL) On open-ended analysis benchmarks, BIORESEARCHER reaches 89.33% accuracy on BixBench and a mean score of 0.758 +/- 0.005 on BaisBench Scientific Discovery, matching Claude Code (0.759 +/- 0.012) and exceeding CellType (0.641 +/- 0.082). -- [SCI-000126#evaluation#FULLTEXT-260]
- (RQ3|NEGATIVE) On the 30-query clinical end-to-end benchmark, BIORESEARCHER achieves the highest positive hit rate (74.7% +/- 3.3%) and the highest negative clear rate (96.8% +/- 0.2%), exceeding CellType, Medea and OpenAI Deep Research on both axes. -- [SCI-000126#evaluation#FULLTEXT-261]
- (RQ1|NEUTRAL) In the NeuroMark collaborator case, Brain Researcher expanded a single pre-specified pipeline into a 480-specification multiverse covering connectivity, confound, dimensionality-reduction, classifier, and domain-granularity choices, recorded and reviewed all resulting runs, and automated review missed a sign-blind scoring error that a human reviewer caught by inspecting code and outputs. -- [SCI-000140#results-brain-researcher-runs-multiverse#FULLTEXT-342]
- (RQ3|POSITIVE) Across 60 tool-calling tasks and seven frontier models, Brain Researcher improved first-action correct route/tool selection from 23.3% to 93.6% (with-BR 95% CI 88.8-97.1), mean Capability@1 from 49.8% to 94.5%, and handoff sufficiency from 47.4% to 76.1%, with all seven models showing positive paired differences (exact two-sided Wilcoxon signed-rank p = 0.016 for each metric). -- [SCI-000140#results-brain-researcher-improves-tool-c#FULLTEXT-348]

## [C16] verdict=ACTIVE_DEBATE bucket=active_debates score=0.5 claims=4
### Applied to the full 1,893-document corpus, the routed KSR workflow surfaced cross-source asymmetries and blind spots (worker well-being, small firms, and the Global South) that single-source synthesis would have missed.
Supporting studies: SCI-000090, SCI-000115, SCI-000127, SCI-000154
Member claims:
- (RQ3|NEGATIVE) The central trade-off is reduced mechanistic resolution relative to full-text synthesis; abstract-only processing entails partial information loss but yields major gains in feasibility, governance, and scalability beyond human limits. -- [SCI-000090#discussion#FULLTEXT-050]
- (RQ3|NEUTRAL) Applied to the full 1,893-document corpus, the routed KSR workflow surfaced cross-source asymmetries and blind spots (worker well-being, small firms, and the Global South) that single-source synthesis would have missed. -- [SCI-000115#abstract#FULLTEXT-176]
- (RQ1|POSITIVE) The benchmark defines six distinct synthesis workflows varying input type (parametric vs. retrieved), reasoning strategy (zero-shot vs. CoT), and retrieval fidelity (oracle, noisy, negated) to enable fine-grained evaluation of synthesis behavior. -- [SCI-000127#3-1-figure-2-caption#FULLTEXT-265]
- (RQ1|NEGATIVE) The self-feedback inference loop, reranking and retrieval are core components that evaluation demonstrates as important to OpenScholar's performance, indicating that the orchestrated pipeline itself, not just the base LM, drives literature synthesis quality. -- [SCI-000154#evaluation#FULLTEXT-413]

## [C66] verdict=ACTIVE_DEBATE bucket=active_debates score=0.5 claims=5
### Topic modeling using BERTopic identified thematic structure, redundancy, and evidence gaps, revealing substantial thematic redundancy and underexplored research areas in the corpora.
Supporting studies: SCI-000128, SCI-000138, SCI-000179, SCI-000181
Member claims:
- (RQ2|NEGATIVE) When no protein-protein interaction edges are found the system avoids cluster-level interpretation and instead treats proteins individually; if an enriched pathway has weak literature support its narrative interpretation is marked as literature-weak or exploratory. -- [SCI-000128#appendix-a-4-quality-control-and-failure#FULLTEXT-281]
- (RQ3|NEGATIVE) Retrieval can miss relevant studies, select papers that are topically related but mechanistically weak, or suffer from protein synonym ambiguity, incomplete database coverage, and noisy input protein associations. -- [SCI-000128#limitations#FULLTEXT-284]
- (RQ3|NEUTRAL) Topic modeling using BERTopic identified thematic structure, redundancy, and evidence gaps, revealing substantial thematic redundancy and underexplored research areas in the corpora. -- [SCI-000138#abstract#FULLTEXT-337]
- (RQ2|NEGATIVE) When abstracts were unavailable, the AI module explicitly documented the limitation and generated context-aware summaries from available bibliographic information rather than silently fabricating content. -- [SCI-000179#results-and-discussion-ai-assisted-abstr#FULLTEXT-479]
- (RQ1|POSITIVE) Domain-specific optimizations such as biomedical entity recognition, relationship extraction and specialized embeddings further enhance performance across diverse research scenarios. -- [SCI-000181#abstract#FULLTEXT-486]

## [C6] verdict=UNRESOLVED bucket=unresolved score=0.0 claims=4
### Each hypothesis was independently evaluated against a randomized baseline of 1,000 XGBoost models trained on random gene sets, guarding against spurious gene-set signal.
Supporting studies: SCI-000082, SCI-000099
Member claims:
- (RQ2|NEUTRAL) Each hypothesis was independently evaluated against a randomized baseline of 1,000 XGBoost models trained on random gene sets, guarding against spurious gene-set signal. -- [SCI-000082#body#FULLTEXT-018]
- (RQ3|NEUTRAL) The Maraviroc hypothesis achieved a cross-validated XGBoost AUC of 0.6013 on the 20% test split, explicitly excluding all AD-associated genes during knowledge graph construction. -- [SCI-000082#body#FULLTEXT-023]
- (RQ3|NEUTRAL) Across four scenarios with increasing gene-list sizes (S1: 13, S2: 28, S3: 52, S4: 82 genes), M-Reason consistently preserved all critical findings regardless of evidence size, and five independent executions per scenario with the same context, question, and gene list were confirmed by human experts and an LLM to reliably highlight the same novel and well-known genes. -- [SCI-000099#5-m-reason-evaluation#FULLTEXT-069]
- (RQ3|NEUTRAL) In the largest evaluation scenario (S4, 82 genes, evidence sets up to 81,627 words), M-Reason generated a comprehensive report approximately 135 times faster than the estimated human reading time baselined at 200 words per minute. -- [SCI-000099#5-m-reason-evaluation#FULLTEXT-070]

## [C21] verdict=UNRESOLVED bucket=unresolved score=0.0 claims=2
### A review workflow of two junior reviewers (Gemini-1.5-flash and GPT-4O-mini) reviewing 1,000 title/abstract pairs took approximately one minute at a cost of $1.20.
Supporting studies: SCI-000096, SCI-000131
Member claims:
- (RQ3|NEUTRAL) A review workflow of two junior reviewers (Gemini-1.5-flash and GPT-4O-mini) reviewing 1,000 title/abstract pairs took approximately one minute at a cost of $1.20. -- [SCI-000096#section-4-2-evaluation-on-custom-dataset#FULLTEXT-057]
- (RQ3|NEUTRAL) One documented overnight auto-review-loop run completed four review-revise rounds over approximately eight hours, increasing the internal reviewer score from 5.0 to 7.5/10, launching more than 20 GPU experiments, and removing claims unsupported by available evidence. -- [SCI-000131#deployment-evidence-overnight-run#FULLTEXT-301]

## [C58] verdict=UNRESOLVED bucket=unresolved score=0.0 claims=3
### AutoSynthesis records traceable audit logs and intermediate outputs, including screening decisions, eligibility judgments, extracted statistics, and effect size calculations.
Supporting studies: SCI-000122, SCI-000135
Member claims:
- (RQ1|NEUTRAL) All steps of eligibility-aware weighting — penalty evaluation, score transformation, and weighted estimation — are executed deterministically and fully logged in the framework. -- [SCI-000122#2-2-eligibility-aware-meta-analysis#FULLTEXT-219]
- (RQ3|NEUTRAL) Eligibility-aware reweighting increased Golan 2019's contribution from 13.6% to 34.6% (best population alignment) while Moore 2018 decreased from 31.7% to 20.5% due to substantial eligibility mismatch. -- [SCI-000122#3-2-eligibility-aware-meta-analysis-olap#FULLTEXT-226]
- (RQ1|NEUTRAL) AutoSynthesis records traceable audit logs and intermediate outputs, including screening decisions, eligibility judgments, extracted statistics, and effect size calculations. -- [SCI-000135#body#FULLTEXT-305]

## [C42] verdict=UNRESOLVED bucket=unresolved score=0.333 claims=4
### A validation study of 164 references was used to measure the study-design classification performance via a confusion matrix.
Supporting studies: SCI-000110, SCI-000115, SCI-000138
Member claims:
- (RQ3|NEUTRAL) A validation study of 164 references was used to measure the study-design classification performance via a confusion matrix. -- [SCI-000110#3-5-study-design-classification#FULLTEXT-142]
- (RQ3|NEUTRAL) On a validation study of 164 references, the hierarchical study-design classifier achieved precision 91.4%, recall 100%, specificity 92.2%, and overall accuracy 95.7%. -- [SCI-000110#3-5-study-design-classification-table-3#FULLTEXT-147]
- (RQ1|NEUTRAL) The Knowledge Synthesis Review (KSR) framework decomposes evidence synthesis into four cognitive tasks (screening, extraction, analysis, synthesis), benchmarks LLM-based systems on each against expert reference standards, and routes each task to the best-performing system under continuous expert validation. -- [SCI-000115#abstract#FULLTEXT-172]
- (RQ2|NEGATIVE) In study design classification, the Cochrane classifier achieved perfect sensitivity (100%) for identifying RCTs but low specificity (42%) with 26 false positives, whereas Kernel's deployed domain-adapted configuration achieved perfect sensitivity and specificity on the same expert-annotated benchmark. -- [SCI-000138#results#FULLTEXT-332]

## [C49] verdict=UNRESOLVED bucket=unresolved score=0.333 claims=3
### The RAG approach builds a custom OpenAI Assistant with the SciTLDR dataset as the LLM knowledge base with retrieval enabled.
Supporting studies: SCI-000114, SCI-000156, SCI-000164
Member claims:
- (RQ3|POSITIVE) Based on own testing consistent with prior benchmarks, OpenAI ADA embeddings performed better than GloVe and SPECTER on vitaLITy 2's similarity-search features. -- [SCI-000114#4-vitality-2#FULLTEXT-166]
- (RQ1|NEUTRAL) The RAG approach builds a custom OpenAI Assistant with the SciTLDR dataset as the LLM knowledge base with retrieval enabled. -- [SCI-000156#body#FULLTEXT-421]
- (RQ1|NEUTRAL) For fair comparison, the authors replicate the QA-based baseline with open-weights embeddings and a temperature of 0 instead of 0.2, deliberately increasing reproducibility over the original work. -- [SCI-000164#5-3-baselines#FULLTEXT-449]

## [C50] verdict=UNRESOLVED bucket=unresolved score=0.333 claims=4
### The system's core is a workflow orchestration engine implemented using n8n that enables sequential and conditional execution across multiple heterogeneous data sources.
Supporting studies: SCI-000115, SCI-000179, SCI-000182
Member claims:
- (RQ1|NEUTRAL) KSR's Phase III is a model-agnostic orchestration layer that routes each task to the model with the strongest demonstrated performance for that task over shared retrieval infrastructure while maintaining expert validation throughout. -- [SCI-000115#1-introduction#FULLTEXT-171]
- (RQ3|NEGATIVE) The KSR routing strategy was not validated end-to-end against a single-system baseline on held-out documents, and the efficiency claim was not quantified in time or cost — both declared priorities for future work. -- [SCI-000115#4-discussion#FULLTEXT-180]
- (RQ1|POSITIVE) The system's core is a workflow orchestration engine implemented using n8n that enables sequential and conditional execution across multiple heterogeneous data sources. -- [SCI-000179#materials-and-methods-system-architectur#FULLTEXT-476]
- (RQ1|NEUTRAL) An AI-assisted, multi-phase framework leverages LLMs to automate major stages of the SLR workflow through an end-to-end modular approach supporting data processing, analysis, and visualization. -- [SCI-000182#abstract#FULLTEXT-496]

## [C55] verdict=UNRESOLVED bucket=unresolved score=0.0 claims=5
### LUMEN automates six SR/MA phases end-to-end with automated RoB-2/ROBINS-I and GRADE assessment in addition to statistical synthesis and manuscript drafting.
Supporting studies: SCI-000118, SCI-000142, SCI-000154
Member claims:
- (RQ1|NEUTRAL) LUMEN automates six SR/MA phases end-to-end with automated RoB-2/ROBINS-I and GRADE assessment in addition to statistical synthesis and manuscript drafting. -- [SCI-000118#body#FULLTEXT-197]
- (RQ1|NEUTRAL) LUMEN uses 11 specialized agents with deliberate model routing, assigning cheaper models to high-volume phases, Claude Sonnet to high-judgment phases, and GPT-5.4 to verification. -- [SCI-000118#abstract#FULLTEXT-198]
- (RQ3|NEUTRAL) Across 13 ground-truth-comparable outcomes LUMEN achieved 100% directional agreement with published meta-analyses, with effect sizes within 1% for homogeneous study designs. -- [SCI-000118#body#FULLTEXT-203]
- (RQ1|NEUTRAL) Manuscript assembly reads effect estimates directly from R output files to prevent hallucination of statistical results, a capability unique among current SR automation tools. -- [SCI-000142#methods-manuscript-generation-and-qualit#FULLTEXT-364]
- (RQ3|NEUTRAL) Despite being a smaller open model, OpenScholar-8B outperforms GPT-4o by 6.1% and PaperQA2 by 5.5% in correctness on a challenging multi-paper synthesis task from the new ScholarQABench benchmark. -- [SCI-000154#abstract#FULLTEXT-417]

## [C28] verdict=UNRESOLVED bucket=unresolved score=0.25 claims=5
### The system creates dual data products, a Neo4j knowledge graph and Qdrant vector collections, serving as structural infrastructure for verifiable information synthesis.
Supporting studies: SCI-000100, SCI-000138, SCI-000158, SCI-000181
Member claims:
- (RQ1|NEUTRAL) The framework creates a chain of custody for every piece of information, combining semantic search (Qdrant), keyword search, and structured graph traversals (Neo4j) with Reciprocal Rank Fusion. -- [SCI-000100#body#FULLTEXT-074]
- (RQ1|NEUTRAL) The system creates dual data products, a Neo4j knowledge graph and Qdrant vector collections, serving as structural infrastructure for verifiable information synthesis. -- [SCI-000100#abstract#FULLTEXT-075]
- (RQ1|NEUTRAL) The AI co-scientist is designed as a multi-representational platform integrating relational databases, vector-based semantic retrieval, and a Neo4j knowledge graph, and is described as domain-agnostic with a practical framework for reducing research waste across biomedical disciplines. -- [SCI-000138#abstract#FULLTEXT-329]
- (RQ3|NEUTRAL) Limitation: The initial search strategy was suboptimal due to absence of comprehensive Boolean operators (lack of 'AND' in search strings), potentially compromising specificity and thoroughness of the literature search. -- [SCI-000158#section-6-limitation#FULLTEXT-436]
- (RQ1|NEGATIVE) Traditional keyword-based search tools like PubMed lack the semantic understanding to answer nuanced questions or summarize findings across multiple sources, with traditional search engines relying primarily on lexical matching and statistical term weighting achieving limited precision and recall on complex biomedical queries. -- [SCI-000181#introduction#FULLTEXT-489]

## [C35] verdict=UNRESOLVED bucket=unresolved score=0.25 claims=6
### In expert review, 75% of RAG-augmented responses met or exceeded expert expectations for relevance, accuracy, and sufficiency for guiding decisions.
Supporting studies: SCI-000107, SCI-000108, SCI-000110, SCI-000111
Member claims:
- (RQ1|POSITIVE) Reproducibility in ADVISE is handled by repeating every experiment five times and averaging predicted uncertainties and priority scores across the five runs to improve repeatability of the results. -- [SCI-000107#methodology-implementation-details#FULLTEXT-104]
- (RQ3|NEGATIVE) ADVISE acknowledges it lacks true counterfactual analysis of the EGM process without AI assistance, because it was infeasible for human raters to build each EGM three separate times; comparisons were standardized through retrospective experiments on a labeled subset and a fully labeled 68,539-document simulated dataset. -- [SCI-000107#discussion-counterfactual-analysis#FULLTEXT-107]
- (RQ2|NEUTRAL) In the PICO prediction study participants and intervention/control showed high accuracy (greater than 80%), while outcomes were more challenging to extract, evidencing variable reliability across data items. -- [SCI-000108#results#FULLTEXT-117]
- (RQ3|NEUTRAL) The study observed variability in the LLM's predictions and changes in response quality, indicating instability in output across repeated attempts for the same data-extraction task. -- [SCI-000108#results#FULLTEXT-124]
- (RQ3|NEUTRAL) In expert review, 75% of RAG-augmented responses met or exceeded expert expectations for relevance, accuracy, and sufficiency for guiding decisions. -- [SCI-000110#3-1-performance-of-rag-vs-gpt-4#FULLTEXT-144]
- (RQ1|NEUTRAL) The evaluation benchmark is safety-first, rewarding cautious models with high include recall and using professional systematic reviewers for annotation. -- [SCI-000111#body#FULLTEXT-150]

## [C38] verdict=UNRESOLVED bucket=unresolved score=0.25 claims=7
### TrialMind follows PRISMA for transparent screening, creating eligibility criteria based on the input PICO as the basis for study selection.
Supporting studies: SCI-000109, SCI-000111, SCI-000122, SCI-000142
Member claims:
- (RQ1|NEUTRAL) TrialMind follows PRISMA for transparent screening, creating eligibility criteria based on the input PICO as the basis for study selection. -- [SCI-000109#body#FULLTEXT-126]
- (RQ2|NEUTRAL) TrialMind generates and executes Python code for result standardization, keeping the calculation process transparent and enhancing the reliability and reproducibility of synthesized evidence. -- [SCI-000109#body#FULLTEXT-129]
- (RQ2|NEUTRAL) TrialMind's source code for study search, study screening, data extraction, and result extraction is publicly released on GitHub, supporting reproducibility. -- [SCI-000109#body#FULLTEXT-130]
- (RQ2|NEGATIVE) Multi-task training harms include/exclude classification performance, with hallucinations hypothesized because exclusion reasoning and PICO information often relied on information from full-text screening not present in abstracts. -- [SCI-000111#body#FULLTEXT-153]
- (RQ3|NEUTRAL) For the gastric cancer query, EligMeta reduced 4,044 ClinicalTrials.gov trials to 700 after generic pre-filtering and then to 39 eligible studies via deterministic sequential evaluation of six inclusion/exclusion rules. -- [SCI-000122#3-1-illustrative-example-trial-selection#FULLTEXT-228]
- (RQ3|NEUTRAL) In a head-to-head landscape analysis, the agentic coding system Codex returned 28 trials (only 7 NCCN-covered) and violated the predefined inclusion criterion by including the non-FDA-approved FLX475 trial, while GPT-5.4 identified only 11 trials (8 NCCN-covered) — both missing guideline-cited studies such as KEYNOTE-059. -- [SCI-000122#3-1-illustrative-example-trial-selection#FULLTEXT-229]
- (RQ1|NEUTRAL) Five mandatory human decision points enforce oversight at PICO definition, screening disagreement resolution, analysis type selection, GRADE quality assessment, and interpretation and clinical implications. -- [SCI-000142#methods-pipeline-architecture#FULLTEXT-363]

## [C45] verdict=UNRESOLVED bucket=unresolved score=0.25 claims=7
### Screening benchmark results demonstrate that model ranking is domain-dependent and not transferable across review topics.
Supporting studies: SCI-000111, SCI-000118, SCI-000151, SCI-000154
Member claims:
- (RQ2|NEUTRAL) ChatGPT performance varies greatly across review topics, drawing into question its generality and requiring assessment of model blind spots prior to real-world endorsement. -- [SCI-000111#body#FULLTEXT-152]
- (RQ2|NEUTRAL) The overall quality of model-generated exclusion reasons remains poor, with ChatGPT generating subpar or incorrect reasons for 83% of samples. -- [SCI-000111#body#FULLTEXT-154]
- (RQ3|NEUTRAL) Inter-rater agreement between two independent experts ranking exclusion reasons reached r=.84 for the Guanaco7B variant versus r=.62 for ChatGPT. -- [SCI-000111#body#FULLTEXT-155]
- (RQ3|POSITIVE) The best performing model, Guanaco7B (Single), achieved 0.82 accuracy on the test set while ChatGPT achieved 0.6 accuracy. -- [SCI-000111#body#FULLTEXT-158]
- (RQ2|NEGATIVE) Screening benchmark results demonstrate that model ranking is domain-dependent and not transferable across review topics. -- [SCI-000118#abstract#FULLTEXT-200]
- (RQ2|NEUTRAL) Consumer LLM interfaces such as ChatGPT are reported to face significant challenges in output reliability and consistency, adherence to systematic-review methodology, and academic-integrity ethics. -- [SCI-000151#1-introduction#FULLTEXT-390]
- (RQ3|NEUTRAL) In human evaluations, experts preferred OpenScholar-8B and OpenScholar-GPT-4o responses over expert-written ones 51% and 70% of the time respectively, compared with 32% for GPT-4o, evidencing perceived output quality. -- [SCI-000154#abstract#FULLTEXT-418]

## [C57] verdict=UNRESOLVED bucket=unresolved score=0.25 claims=6
### GPT-3.5-turbo showed the least discrimination across research questions, consistently overestimating relevance and risking a high false-positive rate in article selection.
Supporting studies: SCI-000120, SCI-000151, SCI-000154, SCI-000159
Member claims:
- (RQ3|NEUTRAL) For intermediate-expertise stakeholder identification, GPT-4o reached micro F1 0.54 (macro 0.30), precision 0.40 (macro 0.27), and recall 0.83 (macro 0.33), extracting extraneous stakeholders from introductory sections and occasionally misclassifying taxonomy categories. -- [SCI-000120#4-results-intermediate-expertise-tasks#FULLTEXT-213]
- (RQ3|NEUTRAL) GPT-4o achieved precision 0.88 and recall 0.90 on low-expertise geographic-location extraction (F1 0.89), and in disagreements it often provided more specific information by extracting exact countries where human annotators grouped countries together. -- [SCI-000120#4-results-low-expertise-tasks#FULLTEXT-214]
- (RQ3|NEUTRAL) The authors recommend prompting methods that elicit reasoning and verification capabilities to improve stakeholder-identification performance, and state they did not explore complex prompting techniques such as Chain of Verification that could enhance accuracy and reliability. -- [SCI-000120#4-results-intermediate-expertise-tasks#FULLTEXT-216]
- (RQ3|NEUTRAL) GPT-3.5-turbo showed the least discrimination across research questions, consistently overestimating relevance and risking a high false-positive rate in article selection. -- [SCI-000151#4-1-2-binary-relevance-decision-and-scor#FULLTEXT-394]
- (RQ3|NEGATIVE) OpenScholar systems match or surpass expert humans in both answer correctness and citation accuracy, despite expert human performance exceeding GPT-4o and other competitive baselines. -- [SCI-000154#evaluation#FULLTEXT-419]
- (RQ3|NEUTRAL) Human evaluation involved 16 Ph.D.-level expert annotators across three scientific disciplines, producing over 400 fine-grained evaluations; OS-GPT4o was rated Useful in 80% of queries and preferred over human answers in 70% of cases. -- [SCI-000159#section-5-expert-evaluation#FULLTEXT-445]

## [C61] verdict=UNRESOLVED bucket=unresolved score=0.25 claims=8
### GPT-3.5-turbo achieved the highest ROUGE-1 score of 0.364 versus 0.268 for T5 and 0.257 for spaCy, showing better unigram and bigram overlap with human summaries.
Supporting studies: SCI-000125, SCI-000151, SCI-000152, SCI-000156
Member claims:
- (RQ2|NEUTRAL) In reference generation, Claude-3.5-Sonnet achieved the highest title search rate (St 64.82) and precision (51.59), while Llama-3.2-3B performed worst across all three metrics. -- [SCI-000125#4-experiments-4-2-main-results#FULLTEXT-245]
- (RQ2|NEUTRAL) The framework's hallucination metric defines precision such that a higher precision indicates a lower hallucination rate, and also computes the overlap rate with human-cited references and a title search rate per LLM. -- [SCI-000125#3-methodology-3-3-evaluation-metrics#FULLTEXT-247]
- (RQ3|NEUTRAL) In abstract writing, Claude-3.5-Sonnet generated abstracts with the highest average semantic similarity to human-written ones (81.17%) and the highest TRUE factual-consistency score (78.10%). -- [SCI-000125#4-experiments-4-2-main-results#FULLTEXT-248]
- (RQ3|NEUTRAL) Reference generation performance varied significantly across disciplines: almost all models exhibited the highest precision in Mathematics and the lowest in Chemistry, with one-way ANOVA tests confirming significant differences for all models except Llama-3.2-3B. -- [SCI-000125#4-experiments-4-4-cross-disciplinary-ana#FULLTEXT-249]
- (RQ3|NEUTRAL) The five evaluated LLMs (Claude-3.5-Sonnet, GPT-4o, Qwen-2.5-72B, DeepSeek-V3, Llama-3.2-3B) were generated via official APIs with temperature set to 0 for consistency, and reference veracity was checked against Semantic Scholar. -- [SCI-000125#4-experiments-4-1-experimental-settings#FULLTEXT-253]
- (RQ3|NEUTRAL) Llama 3:8B displayed significant inconsistency between relevance scores and binary classifications, leading the authors to exclude its binary relevance decisions from the screening performance analysis. -- [SCI-000151#4-1-2-binary-relevance-decision-and-scor#FULLTEXT-395]
- (RQ3|NEUTRAL) Compared to the benchmark ratings, accuracy and specificity were above 90% for the human rater and both LLMs, while sensitivity was considerably lower for all raters; GPT-4o Mini (94.31%) slightly outperformed Claude 3.5 Sonnet (92.25%) in specificity, but Claude Sonnet had remarkably higher sensitivity at 80.33% than GPT-4o Mini at 59.02%. -- [SCI-000152#results#FULLTEXT-405]
- (RQ3|POSITIVE) GPT-3.5-turbo achieved the highest ROUGE-1 score of 0.364 versus 0.268 for T5 and 0.257 for spaCy, showing better unigram and bigram overlap with human summaries. -- [SCI-000156#body#FULLTEXT-427]

## [C15] verdict=UNRESOLVED bucket=unresolved score=0.2 claims=6
### The platform embeds explicit PICOS formalization and explainable NLP into evidence synthesis workflows to improve scalability, transparency and efficiency, framing structured formalization as a route to auditable synthesis.
Supporting studies: SCI-000090, SCI-000102, SCI-000106, SCI-000110, SCI-000138
Member claims:
- (RQ3|NEUTRAL) A pragmatic deployment model is recommended: high-throughput abstract-level mapping for coverage, paired with periodic human audits and targeted full-text deep dives where abstract informativeness is low or clinical stakes are high. -- [SCI-000090#discussion#FULLTEXT-048]
- (RQ1|NEUTRAL) A three-layer hierarchical agentic network (worker, manager, director) preserves traceability and transparency, with 13 worker-layer APIs accessing domain-specific resources including a medical knowledge graph, literature repositories, and clinical records. -- [SCI-000102#methods-agentic-collaboration-module#FULLTEXT-083]
- (RQ1|NEUTRAL) DeepER-Med structures evidence-based medical research as an explicit and inspectable workflow comprising three stages—research intent investigation, evidence retrieval and interpretation, and structured knowledge synthesis—implemented through research planning, agentic collaboration, and evidence synthesis modules. -- [SCI-000102#methods-framework-of-deeper-med#FULLTEXT-085]
- (RQ1|NEUTRAL) The framework replaces manual, ad-hoc 'prompt alchemy' with a rigorous, four-step programmatic process: formally defining the research goal, codifying the quality standard with data, automatically compiling an optimal prompt, and packaging the result as a verifiable digital artefact. -- [SCI-000106#introduction#FULLTEXT-094]
- (RQ1|NEUTRAL) The framework follows a standard four-phase systematic-review pipeline — Define and Search, Screen and Assess, Extract and Synthesize, Interpret and Update — with each phase automated (PICOS guidance, study-design classification, BERTopic clustering, and living-database updates). -- [SCI-000110#1-2-overall-workflow-in-systematic-revie#FULLTEXT-137]
- (RQ1|POSITIVE) The platform embeds explicit PICOS formalization and explainable NLP into evidence synthesis workflows to improve scalability, transparency and efficiency, framing structured formalization as a route to auditable synthesis. -- [SCI-000138#abstract#FULLTEXT-330]

## [C20] verdict=UNRESOLVED bucket=unresolved score=0.4 claims=5
### Title-abstarct screening employs a dual-screener mechanism with two independent models scoring on a five-point scale and an arbiter applying a lean-toward-inclusion policy for disagreements.
Supporting studies: SCI-000096, SCI-000118, SCI-000120, SCI-000128, SCI-000137
Member claims:
- (RQ2|NEUTRAL) The TitleAbstractReviewer uses a 5-point Likert scale for article assessment (1 = absolutely exclude, 5 = absolutely include), with hierarchical decision-making: when junior reviewers disagree, a senior reviewer's assessment becomes definitive. -- [SCI-000096#section-4-evaluation#FULLTEXT-055]
- (RQ2|NEUTRAL) Title-abstarct screening employs a dual-screener mechanism with two independent models scoring on a five-point scale and an arbiter applying a lean-toward-inclusion policy for disagreements. -- [SCI-000118#body#FULLTEXT-201]
- (RQ1|NEUTRAL) The evaluation corpus is a 586-document sample from the GAMI database (food sector focus group) of 1,682 peer-reviewed articles, where each original article was labeled by two human experts with conflicts resolved by a senior expert, providing the human reference standard. -- [SCI-000120#3-1-dataset#FULLTEXT-208]
- (RQ3|NEGATIVE) Human evaluation used four domain experts scoring five dimensions (comprehensiveness, biomedical validity, evidence traceability, ranking, readability) on a 1-5 Likert scale with blinded system identity, though limited by number of disease cases and evaluators. -- [SCI-000128#appendix-c-qualitative-analysis-and-bias#FULLTEXT-283]
- (RQ2|NEGATIVE) Full-text eligibility was assessed by a single reviewer rather than multiple independent assessors, and the review lead had previously completed the single-reviewer title-and-abstract screen, so the verified eligible set is an operational reference standard rather than an independent consensus gold standard. -- [SCI-000137#discussion-strengths-and-limitations#FULLTEXT-320]

## [C23] verdict=UNRESOLVED bucket=unresolved score=0.4 claims=5
### Future work is scoped to extending the GUI and adding more models such as BERT, Gemini, and LLaMA rather than adding verification or evaluation pipelines.
Supporting studies: SCI-000096, SCI-000106, SCI-000129, SCI-000131, SCI-000156
Member claims:
- (RQ3|NEUTRAL) Future development priorities include supporting a broader range of language models, enhancing memory and context management, creating a no-code interface, and providing more advanced validation tools. -- [SCI-000096#section-6-conclusions-and-future-directi#FULLTEXT-059]
- (RQ1|NEUTRAL) The work proposes a structured, domain-specific framework that embeds task declarations, test suites and automated prompt tuning into a reproducible SLR workflow, translated into a concrete blueprint with working code examples enabling researchers to construct verifiable LLM pipelines aligned with transparency and rigour principles. -- [SCI-000106#abstract#FULLTEXT-099]
- (RQ3|NEGATIVE) Five lessons learned: (1) time efficiency is significant but contextual, (2) prompt design is critical, (3) human oversight remains essential, (4) hybrid workflows are the way forward, (5) Gemini PRO shows promise. -- [SCI-000129#barros-et-al-lessons-learned#FULLTEXT-290]
- (RQ1|NEUTRAL) Each research capability is defined by a SKILL.md file containing YAML frontmatter followed by a natural-language workflow specification with inputs, outputs, step-by-step procedures, quality gates, and failure-handling instructions. -- [SCI-000131#methods-skills-layer#FULLTEXT-296]
- (RQ3|NEGATIVE) Future work is scoped to extending the GUI and adding more models such as BERT, Gemini, and LLaMA rather than adding verification or evaluation pipelines. -- [SCI-000156#body#FULLTEXT-426]

## [C31] verdict=UNRESOLVED bucket=unresolved score=0.2 claims=6
### Scale-size ablation found that increasing the graded relevance scale improves performance up to scale 0-14, with 0-19 only slightly worse; the authors therefore selected scale 0-19 for the main evaluation.
Supporting studies: SCI-000102, SCI-000117, SCI-000159, SCI-000164, SCI-000186
Member claims:
- (RQ3|NEGATIVE) Ablation analysis shows removal of the knowledge graph query expansion component results in performance decreases of approximately 11.3% and 5.2% on two QA datasets, indicating its importance for model precision. -- [SCI-000102#extended-figure-3-caption#FULLTEXT-090]
- (RQ3|NEUTRAL) Ablation results show that removing TBC subordination hurts all three dimensions of evidence synthesis quality, while removing the commit operation produces more blocks with overlapping and redundant claims (AS 83.5 vs 84.4, RC 23.5 vs 22.3, blocks 6.63 vs 10.2). -- [SCI-000117#4-experiments-4-5-ablation-study#FULLTEXT-191]
- (RQ3|NEUTRAL) SCHOLARQABENCH introduces a multifaceted automatic evaluation pipeline measuring Correctness, Citation accuracy (precision/recall/F1), and content quality (Relevance, Coverage, Organization) across 2,967 queries in 4 scientific disciplines. -- [SCI-000159#section-3-2-metrics-and-evaluation-proto#FULLTEXT-448]
- (RQ3|NEUTRAL) Ablation shows the dense re-ranker (monoT5) contributes workload savings by rescuing articles the LLM scored too low, yielding a ~7–12% increase in True Negative Rate at recall; removing it leaves MAP nearly unchanged. -- [SCI-000164#5-4-main-results-and-findings#FULLTEXT-454]
- (RQ3|POSITIVE) Scale-size ablation found that increasing the graded relevance scale improves performance up to scale 0-14, with 0-19 only slightly worse; the authors therefore selected scale 0-19 for the main evaluation. -- [SCI-000164#appendix-a-1-preliminary-experiments#FULLTEXT-460]
- (RQ3|NEUTRAL) Ablation shows that removing all idea evolution mechanisms degrades idea quality substantially on novelty (loses in 80.00% of comparisons) and feasibility (loses in 83.33%), while relevance and clarity are less affected (46.67% ties on both). -- [SCI-000186#5-4-ablation-studies-rq4#FULLTEXT-505]

## [C37] verdict=UNRESOLVED bucket=unresolved score=0.4 claims=8
### ROUGE scores are used for evaluation on the test data of the selected SciTLDR dataset.
Supporting studies: SCI-000108, SCI-000109, SCI-000115, SCI-000118, SCI-000156
Member claims:
- (RQ3|NEGATIVE) Evaluation of the extraction was done manually, and automatic scoring methods such as BLEU and ROUGE showed limited value, identified as a limitation of the automated evaluation approach. -- [SCI-000108#results#FULLTEXT-120]
- (RQ3|NEUTRAL) Overall results indicated extraction accuracy of around 80%, with variability across domains: 82% for human clinical, 80% for animal, and 72% for studies of human social sciences. -- [SCI-000108#results#FULLTEXT-122]
- (RQ3|NEGATIVE) The automated data extraction never reached 100% accuracy in any area or study across the three domains, with the highest accuracy achieved for extracting the country field, correctly extracted and mapped against the ISO Alpha-3 code 90% of the time. -- [SCI-000108#results#FULLTEXT-123]
- (RQ1|NEUTRAL) Result extraction uses a specialized three-step pipeline: identifying relevant content, extracting and logically processing numerical values, and converting values into a standardized tabular format. -- [SCI-000109#body#FULLTEXT-125]
- (RQ2|NEUTRAL) Extracted values include indices that link back to their locations in the source content, enabling easy checking and correction by sourcing the origin. -- [SCI-000109#body#FULLTEXT-128]
- (RQ2|NEGATIVE) Post-cutoff (unseen) extraction accuracy showed no decline for any system (GPT-5 86.7%, Claude 88.9%, Gemini 85.2%), all exceeding the full-corpus values of 80.0%, 80.3%, and 74.5%, respectively. -- [SCI-000115#3-results-3-1-1-robustness-to-training-d#FULLTEXT-175]
- (RQ3|NEUTRAL) Screening and extraction together dominate expenditure, with screening consuming 74-86% of cost in high-yield domains and extraction 47-49% in low-yield domains. -- [SCI-000118#body#FULLTEXT-204]
- (RQ3|NEUTRAL) ROUGE scores are used for evaluation on the test data of the selected SciTLDR dataset. -- [SCI-000156#body#FULLTEXT-428]

## [C39] verdict=UNRESOLVED bucket=unresolved score=0.0 claims=6
### A vanilla prompting strategy with GPT-4 and Sonnet models served as the baseline for result extraction, with baseline outputs manually parsed by annotators.
Supporting studies: SCI-000109, SCI-000120, SCI-000124, SCI-000141, SCI-000164
Member claims:
- (RQ3|NEUTRAL) A vanilla prompting strategy with GPT-4 and Sonnet models served as the baseline for result extraction, with baseline outputs manually parsed by annotators. -- [SCI-000109#body#FULLTEXT-131]
- (RQ1|NEUTRAL) The study embeds GPT-4o in an evidence-extraction workflow that first converts PDF files to markdown with LlamaParse, includes an intermediate verification step (the model must first identify the adaptation response before listing stakeholders), and asks the model to supply excerpts justifying each extraction to analyze divergence from human annotations. -- [SCI-000120#3-3-experiments#FULLTEXT-209]
- (RQ2|NEUTRAL) On the high-expertise depth-of-adaptation-response task, GPT-4o exhibited a systematically more optimistic view than human annotators, often overestimating the impact of adaptation responses, and in 10.4% of cases produced per-response instead of aggregate assessments requiring evaluation isolation. -- [SCI-000120#4-results-high-expertise-tasks#FULLTEXT-210]
- (RQ1|NEUTRAL) Two complementary prompting strategies were used: BASIC prompts requesting direct binary responses, and DETAILED prompts including explanations and illustrative examples of each criterion. -- [SCI-000124#body#FULLTEXT-233]
- (RQ3|NEUTRAL) Only domain-agnostic assistants (ideation, research questions, state-of-the-art, paper writing) are implemented in the early prototype; outputs from one assistant are reused by other assistants, demonstrating feasibility of the core modules. -- [SCI-000141#5-conclusion-and-outlook#FULLTEXT-360]
- (RQ1|NEUTRAL) LGAR's output parsing is engineered for determinism and reproducibility: temperature 0, regular-expression extraction of scale-verified scores, up to three retry attempts on malformed responses, and a fallback assignment of the average of generated relevance scores. -- [SCI-000164#5-1-model-selection-and-experimental-set#FULLTEXT-450]

## [C53] verdict=UNRESOLVED bucket=unresolved score=0.0 claims=14
### Generated summaries are required to mention the first author's name and paper title, providing basic attribution grounding.
Supporting studies: SCI-000117, SCI-000140, SCI-000154, SCI-000156, SCI-000159
Member claims:
- (RQ1|POSITIVE) DeepWeaver generates final answers block-by-block from the refined TBC, a strategy that decomposes context pressure into claim-level generation and improves citation grounding by generating each section from a smaller, more relevant evidence subset. -- [SCI-000117#3-method-3-3-evidence-grounded-answer-ge#FULLTEXT-183]
- (RQ1|NEUTRAL) DeepWeaver maintains thought block chains (TBCs), an explicit data structure that decomposes open-ended answers into sequences of thought blocks bridging retrieved evidence and final generation. -- [SCI-000117#3-method-3-1-thought-block-chain#FULLTEXT-184]
- (RQ1|NEUTRAL) The core evidence-weaving mechanism of DeepWeaver iterates over three ordered stages for refining its main TBC: Draft, Subordinate, and Commit. -- [SCI-000117#3-method-3-2-evidence-weaving#FULLTEXT-185]
- (RQ1|NEUTRAL) To control context burden during TBC construction, the draft and subordinate stages randomly sample subsets of evidence fragments from the full evidence pool and the residual evidence set at each refinement turn. -- [SCI-000117#3-method-3-2-evidence-weaving#FULLTEXT-186]
- (RQ1|NEUTRAL) Two refinement rounds over the initial TBC are sufficient to produce large answer-quality gains, and the paper sets n = 2 as default for a cost-performance trade-off. -- [SCI-000117#4-experiments-4-6-cross-model-generaliza#FULLTEXT-187]
- (RQ2|NEUTRAL) DeepWeaver evaluates citation grounding via three metrics (Citation Count, Relevant Count, Relevant Ratio) that measure whether a system actively uses evidence and avoids citing or integrating irrelevant evidence. -- [SCI-000117#2-2-2-the-loqa-benchmark#FULLTEXT-188]
- (RQ2|POSITIVE) On LoQA, DeepWeaver improves citation grounding and evidence synthesis quality relative to the retrieval-augmented generation baseline, surpassing E-RAG by 15.5% in Argument Sufficiency, +14.7 in Relevant Citations, 14.5% in Relevant Citation Ratio, and 16.6% in Detail Preservation on Qwen3-30B-A3B-Instruct-2507. -- [SCI-000117#4-experiments-4-4-main-results#FULLTEXT-189]
- (RQ2|POSITIVE) On the web-based DeepResearch Bench, DeepWeaver substantially improves effective citation and citation accuracy over the WebWeaver baseline on the FACT split, organizing web evidence into reliable support for answer claims. -- [SCI-000117#4-experiments-4-7-extension-to-web-based#FULLTEXT-190]
- (RQ3|NEGATIVE) DeepWeaver is limited to text-only evidence and its authors acknowledge that model-generated content still requires careful verification, leaving multimodal/structured evidence weaving and answer verification as open problems. -- [SCI-000117#7-limitations#FULLTEXT-193]
- (RQ2|NEUTRAL) BR-KG attaches explicit provenance to source-backed facts, including a verbatim supporting quote and grounding label wherever available, so a retrieved claim can be traced to the study and passage that support it, and coverage is partial and tracked. -- [SCI-000140#results-figure-2-caption-br-kg#FULLTEXT-346]
- (RQ2|NEGATIVE) In the evidence-citation benchmark, Brain Researcher raised verifiable grounding from 4.6% to 22.0%: a claim is counted grounded only when its cited evidence can be located and judged supportive, and the dominant with-BR failure modes were off-topic or partially-supporting retrieved sources rather than fabricated references. -- [SCI-000140#supplementary-methods-s11-1-2-evidence-c#FULLTEXT-347]
- (RQ2|NEUTRAL) OpenScholar produces citation-backed, retrievable responses by identifying relevant passages from the open-access corpus and synthesizing citation-backed answers, giving users a verifiable provenance chain from answer to source passage. -- [SCI-000154#abstract#FULLTEXT-415]
- (RQ2|NEUTRAL) Generated summaries are required to mention the first author's name and paper title, providing basic attribution grounding. -- [SCI-000156#body#FULLTEXT-424]
- (RQ1|NEUTRAL) OpenScholar's iterative self-feedback retrieval-augmented inference pipeline generates outputs with inline citations linked to specific passages from scientific literature, enabling researchers to trace output back to original literature and ensuring transparency and verifiability. -- [SCI-000159#section-2-overview-of-openscholar#FULLTEXT-439]

## [C29] verdict=UNRESOLVED bucket=unresolved score=0.0 claims=16
### Field-level citation accuracy was imperfect across all components, with DOI matching at 74.4% and in-text citations at 73.9%.
Supporting studies: SCI-000100, SCI-000102, SCI-000144, SCI-000154, SCI-000159, SCI-000181
Member claims:
- (RQ2|NEUTRAL) HySemRAG performs post-hoc citation verification in combination with an agentic self-correction framework with iterative quality assurance, ensuring complete traceability. -- [SCI-000100#abstract#FULLTEXT-077]
- (RQ2|NEUTRAL) The system enforces single-source observations and rejects mixed-source citations to prevent hallucination in generated responses. -- [SCI-000100#body#FULLTEXT-078]
- (RQ3|NEUTRAL) Field-level citation accuracy was imperfect across all components, with DOI matching at 74.4% and in-text citations at 73.9%. -- [SCI-000100#body#FULLTEXT-079]
- (RQ3|NEUTRAL) The agentic quality assurance mechanism achieves 68.3% single-pass success rates with 99.0% citation accuracy in validated responses. -- [SCI-000100#abstract#FULLTEXT-081]
- (RQ1|NEUTRAL) All cited sources are listed in the reference section in order of appearance, enabling efficient review, verification, and downstream analysis by researchers. -- [SCI-000102#methods-evidence-synthesis-module#FULLTEXT-084]
- (RQ2|NEUTRAL) Hallucinated or unverifiable references are detected during expert evaluation and the corresponding response is excluded and replaced with an alternative exhibiting high accuracy and reliable citation. -- [SCI-000102#methods-answer-evaluation#FULLTEXT-088]
- (RQ1|NEUTRAL) The study uses a deterministic verification pipeline that parses each generated citation and checks it against Crossref and Semantic Scholar, running identically on every model and condition, with code publicly available. -- [SCI-000144#4-verification-pipeline#FULLTEXT-372]
- (RQ2|NEGATIVE) Non-Disclosure instructions redistribute rather than eliminate errors: DOI completeness drops (most pronounced for LLaMA, -11.4 percentage points) and, because DOI is the strongest verification signal, citations shift from Existing into Unresolved — moving errors from 'obviously wrong' into 'hard to tell.' -- [SCI-000144#zhao-et-al-non-disclosure-ablated-analys#FULLTEXT-375]
- (RQ2|NEGATIVE) The manual audit of fabricated/unresolved citations reveals four recurring failure modes that format-level checks miss: venue laundering, author bricolage, identifier fabrication and omission, and title drift. -- [SCI-000144#6-discussion-6-1-qualitative-error-patte#FULLTEXT-376]
- (RQ2|NEUTRAL) The paper recommends that systems surfacing LLM-generated references run post-hoc verification against multiple databases and treat Unresolved citations as high risk. -- [SCI-000144#6-discussion-6-2-implications-for-practi#FULLTEXT-377]
- (RQ3|NEUTRAL) The paper concludes that prompt engineering alone is unlikely to solve citation hallucination and that reliable generation will require retrieval-augmented architectures, built-in verification, or both. -- [SCI-000144#7-conclusion#FULLTEXT-382]
- (RQ2|NEUTRAL) ScholarQABench introduces a rigorous evaluation protocol combining automatic metrics such as citation accuracy with human rubric-based assessments of coverage, coherence, writing quality and factual correctness, enabling reliable assessment of long-form answers. -- [SCI-000154#evaluation#FULLTEXT-416]
- (RQ1|NEUTRAL) OpenScholar includes a citation verification step where the generator LM ensures all citation-worthy statements are supported by references from retrieved passages, performing post hoc insertion for unsupported claims. -- [SCI-000159#section-2-2-inference-iterative-generati#FULLTEXT-438]
- (RQ2|POSITIVE) Automated fact-checking processes that verify claims against retrieved evidence improved response accuracy, and comprehensive citation tracking that links specific claims to source documents achieved high traceability, allowing users to directly verify information sources. -- [SCI-000181#llm-integration#FULLTEXT-490]
- (RQ2|NEUTRAL) Citation accuracy evaluation found that the vast majority of system-generated citations directly supported the associated claims, with a small percentage providing partial support and only a tiny fraction being irrelevant or misleading, described as approaching human literature reviews. -- [SCI-000181#evaluation#FULLTEXT-491]
- (RQ2|NEUTRAL) The citation accuracy result is described as providing the verification capability essential for scientific work, directly addressing answer-to-source verifiability. -- [SCI-000181#evaluation#FULLTEXT-493]

## [C7] verdict=UNRESOLVED bucket=unresolved score=0.143 claims=9
### Integration with public biological knowledge graphs grounds analyses in established biological knowledge, reducing the risk of hallucinations and implausible results.
Supporting studies: SCI-000082, SCI-000090, SCI-000099, SCI-000125, SCI-000128, SCI-000177, SCI-000181
Member claims:
- (RQ2|NEUTRAL) Integration with public biological knowledge graphs grounds analyses in established biological knowledge, reducing the risk of hallucinations and implausible results. -- [SCI-000082#body#FULLTEXT-019]
- (RQ3|NEUTRAL) Of 103 candidate drugs evaluated, 79 produced models exceeding the randomized baseline AUC of 0.582, indicating knowledge-graph-derived gene networks carried predictive information beyond random genomic features. -- [SCI-000082#body#FULLTEXT-022]
- (RQ2|NEGATIVE) Schema enforcement and conservative missingness handling were specifically designed to minimize hallucination risk, and performed well in audited fields — residual hallucination risk remains but is addressed through structural constraints. -- [SCI-000090#discussion-limitations#FULLTEXT-047]
- (RQ2|NEUTRAL) All synthesized outputs are fully traceable to their source evidence with explicit citations (including direct links when available), which the authors state lets users independently verify findings and directly addresses concerns about LLM hallucinations. -- [SCI-000099#3-4-design-principles-and-rationale#FULLTEXT-067]
- (RQ2|NEUTRAL) The automatic hallucination-assessment method was validated against human judgments: kappa agreement of 0.71 and 86% accuracy with human assessment as the gold standard, using three annotators and majority vote on 100 generated references. -- [SCI-000125#4-experiments-4-5-human-evaluation#FULLTEXT-246]
- (RQ1|NEUTRAL) BioInsight uses typed artifact contracts between retrieval, reasoning, writing, and dashboard construction agents, exposing protein, pathway, publication, and citation links that are usually hidden in end-to-end biomedical agents. -- [SCI-000128#conclusion#FULLTEXT-277]
- (RQ2|NEGATIVE) BioInsight preserves citation links, protein-level statistics, intermediate artifacts, uncertainty notes, and failure-handling behaviors, allowing users to inspect how each claim is supported, though these mechanisms are intended to support expert review rather than replace it. -- [SCI-000128#limitations#FULLTEXT-279]
- (RQ1|POSITIVE) The work demonstrates an AI system for synthesizing knowledge from scientific literature and curated databases to enable network-based drug repurposing, addressing challenges in evidence synthesis. -- [SCI-000177#abstract#FULLTEXT-470]
- (RQ2|NEUTRAL) Experimental comparisons revealed that prompts incorporating domain guidance, explicitly requesting scientific rigor, and specifying citation requirements reduced hallucination compared to general-purpose prompts. -- [SCI-000181#llm-integration#FULLTEXT-492]

## [C25] verdict=UNRESOLVED bucket=unresolved score=0.286 claims=10
### Systematic reviews guided by PRISMA frameworks are acknowledged as thorough but labor-intensive and prone to human bias, motivating the need for AI-assisted evidence synthesis.
Supporting studies: SCI-000099, SCI-000102, SCI-000106, SCI-000123, SCI-000131, SCI-000140, SCI-000177
Member claims:
- (RQ2|NEUTRAL) A Critical Reviewer agent performs adversarial analysis focusing on bias detection and identification of unsupported claims, running in parallel with a Content Validator and a Relevance Validator under a three-reviewer unanimous-consensus approval rule. -- [SCI-000099#3-2-1-overview-and-workflow#FULLTEXT-065]
- (RQ2|NEUTRAL) Blinded expert evaluation masks system identities and assigns responses for review to the author who contributed the corresponding questions, designed to support fair, domain-informed, and unbiased assessment of evidence quality. -- [SCI-000102#methods-answer-generation#FULLTEXT-086]
- (RQ2|NEUTRAL) Domain experts and LLM judgment jointly validate correctness and evidence grounding of each reference answer; if either assessment identifies deficiencies the answer is returned for revision until consensus is reached. -- [SCI-000102#methods-reference-answer-curation#FULLTEXT-087]
- (RQ1|NEUTRAL) The proposed framework offers a path toward establishing new standards for transparency and auditability in AI-assisted reviews, allowing others to verify and replicate automated steps with precision. -- [SCI-000106#introduction#FULLTEXT-098]
- (RQ2|NEUTRAL) AutoConfidenceScore is an advanced automated framework for predicting preprint publication, aimed at improving quality assessment of preprint articles for evidence inclusion in systematic reviews. -- [SCI-000123#abstract#FULLTEXT-231]
- (RQ2|NEUTRAL) Aris defaults to pairing executor and reviewer from different model families because single-model self-refinement loops share inductive biases, whereas heterogeneous multi-agent debate has been reported to elicit more diverse critiques. -- [SCI-000131#methods-design-principles#FULLTEXT-298]
- (RQ2|NEUTRAL) The review loop can amplify reviewer biases: if the reviewer consistently demands a particular methodology, the loop may overfit to the reviewer model's preferences rather than improve broader scientific quality. -- [SCI-000131#discussion-limitations-and-responsible-u#FULLTEXT-300]
- (RQ3|NEGATIVE) The paper-claim-audit uses a zero-context fresh reviewer (new thread with no prior conversation history) to cross-check the manuscript's quantitative claims against raw result files, assigning structured audit statuses such as exact_match, number_mismatch, or missing_evidence. -- [SCI-000131#methods-stage-3-paper-claim-audit#FULLTEXT-303]
- (RQ1|NEGATIVE) Brain Researcher exposes the limit of its formal audit layer in the NeuroMark episode: automated review failed to detect sign-blind scoring (after a server fault triggered fallback to a general-purpose agent that scored permutation p < 0.05 as favorable regardless of sign), and a human reviewer found the error, after which two checks were added to the skillset. -- [SCI-000140#results-brain-researcher-runs-multiverse#FULLTEXT-340]
- (RQ2|NEGATIVE) Systematic reviews guided by PRISMA frameworks are acknowledged as thorough but labor-intensive and prone to human bias, motivating the need for AI-assisted evidence synthesis. -- [SCI-000177#abstract#FULLTEXT-471]

## [C26] verdict=UNRESOLVED bucket=unresolved score=0.143 claims=7
### The modular, multi-agentic design allows users to start the workflow at later stages, for example when updating an existing meta-analysis, or to override specific design choices.
Supporting studies: SCI-000099, SCI-000127, SCI-000135, SCI-000141, SCI-000172, SCI-000179, SCI-000186
Member claims:
- (RQ3|NEUTRAL) The authors report that increasing agent specialization can enhance accuracy but comes with higher operational and maintenance costs, a core architectural tradeoff identified in the evaluation. -- [SCI-000099#6-conclusions#FULLTEXT-072]
- (RQ1|NEUTRAL) MedMeta's synthesis workflows are orchestrated with LangGraph, open-weights inference is optimized with vLLM, and closed-weights models are accessed via APIs — a concrete agentic pipeline architecture. -- [SCI-000127#3-2-llm-workflows-for-conclusion-generat#FULLTEXT-263]
- (RQ1|NEUTRAL) The modular, multi-agentic design allows users to start the workflow at later stages, for example when updating an existing meta-analysis, or to override specific design choices. -- [SCI-000135#body#FULLTEXT-306]
- (RQ1|POSITIVE) The TIB AIssistant enables agent communication through a centralized data store, which the authors argue makes the context-window constraint less problematic and keeps agents self-contained and independently usable. -- [SCI-000141#4-framework-for-ai-assisted-research-4-1#FULLTEXT-356]
- (RQ3|NEUTRAL) Future work should prioritize designing sophisticated testing frameworks to reconfirm reliability; Agentic AI is anticipated as an evolution that will independently orchestrate crawling and RAG analysis but will face navigation drifts, hallucinations, increased costs, and security concerns. -- [SCI-000172#results-and-discussions-future-direction#FULLTEXT-466]
- (RQ3|NEUTRAL) The authors acknowledge the absence of controlled benchmarking against manual review or alternative automation approaches, which limits generalization of the observed performance advantages. -- [SCI-000179#results-and-discussion-limitations-and-f#FULLTEXT-485]
- (RQ1|NEUTRAL) A dedicated Evolution Manager Agent (EMA) implements three self-evolution mechanisms — idea direction, idea validation, and experiment strategy evolution — that distill prior outcomes and failures into reusable strategies. -- [SCI-000186#3-5-evolution-manager-agent#FULLTEXT-498]

## [C36] verdict=UNRESOLVED bucket=unresolved score=0.286 claims=8
### Limitation: No clearly defined criteria for primary and secondary exclusion, and the data extraction reliability is questionable due to lack of a robust analytical algorithm.
Supporting studies: SCI-000108, SCI-000109, SCI-000115, SCI-000120, SCI-000124, SCI-000126, SCI-000158
Member claims:
- (RQ2|NEUTRAL) Causal inference methods and study design were the data extraction items with the most errors, identifying the items most vulnerable to incorrect extraction and raising reliability concerns for downstream synthesis. -- [SCI-000108#abstract#FULLTEXT-116]
- (RQ2|NEUTRAL) The language model found it particularly difficult to name the type of study being reported; in the extraction results study design was rated complete only 47% of the time with 27% incorrect, identifying it as the most error-prone data extraction item. -- [SCI-000108#results#FULLTEXT-118]
- (RQ3|NEGATIVE) Data extraction performs well for study design and population-related fields but extracting study results presents challenges due to diverse result presentation and subtle population/outcome discrepancies. -- [SCI-000109#body#FULLTEXT-133]
- (RQ1|NEUTRAL) Human oversight in KSR is embedded at every review stage (not only final synthesis) to prevent error propagation, since screening and extraction inaccuracies can systematically distort downstream analysis and synthesis. -- [SCI-000115#2-methods-2-2-1-human-in-the-loop-benchm#FULLTEXT-169]
- (RQ2|NEUTRAL) The authors motivate the work by the need for a reliable model that ensures factual accuracy during the evidence-extraction phase for decision-making, and they position the assessment of model factuality as contingent on a system that keeps humans in the loop, concluding that a human-in-the-loop system is extremely beneficial for ensuring the integrity and effectiveness of the process. -- [SCI-000120#6-conclusion#FULLTEXT-211]
- (RQ3|NEUTRAL) Detailed prompting significantly improved identification of causal mediation methods (GPT-5: F1 +0.30; GPT-o3: F1 +0.35) but had minimal effect on assumption discussion or sensitivity analyses. -- [SCI-000124#body#FULLTEXT-237]
- (RQ1|NEUTRAL) The system applies claim-level multi-model reconciliation before editorial assembly, using claim extraction, cross-model grouping, multi-round argumentation and quantitative consensus detection for auditable long-form biomedical report synthesis. -- [SCI-000126#introduction#FULLTEXT-257]
- (RQ3|NEGATIVE) Limitation: No clearly defined criteria for primary and secondary exclusion, and the data extraction reliability is questionable due to lack of a robust analytical algorithm. -- [SCI-000158#section-6-limitation#FULLTEXT-435]

## [C41] verdict=UNRESOLVED bucket=unresolved score=0.143 claims=10
### The verification pipeline assigns a three-way label (Existing, Unresolved, Fabricated) and was audited against human labels with Cohen's kappa = 0.63.
Supporting studies: SCI-000110, SCI-000131, SCI-000137, SCI-000140, SCI-000144, SCI-000158, SCI-000186
Member claims:
- (RQ2|NEUTRAL) Named trust limitation: verifying the trustworthiness of newly incorporated studies in the live database demands structured pipelines or human oversight — a gap the authors explicitly acknowledge. -- [SCI-000110#5-limitations-and-future-directions#FULLTEXT-140]
- (RQ1|NEUTRAL) A three-stage evidence-to-claim audit cascade (experiment-audit, result-to-claim, paper-claim-audit) provides code-level integrity checking, evidence-to-claim mapping, and independent manuscript-level verification against raw evidence files. -- [SCI-000131#methods-evidence-to-claim-audit-cascade#FULLTEXT-294]
- (RQ2|NEGATIVE) The experiment-audit stage detects five integrity failure modes: model-derived reference labels, self-normalized scores, phantom results, dead-code or unused-metric inflation, and scope inflation. -- [SCI-000131#methods-stage-1-experiment-integrity-aud#FULLTEXT-299]
- (RQ1|NEGATIVE) Safeguards against outcome leakage included disabling memory, processing file-batch inputs in separate conversations, retaining stable identifiers, and instructing models to assign Unclear rather than confident exclusion for ambiguous records. -- [SCI-000137#methods-integrity-checks-and-safeguard-p#FULLTEXT-316]
- (RQ1|NEUTRAL) Brain Researcher anchors each auditable episode in a commitment card written before any analysis, sealed with a content hash so that any later change to the plan is detectable, and a claim card written afterward by the review layer recording the resulting claim, its assigned state, scope, and the checks it passed and failed. -- [SCI-000140#results-brain-researcher-converts-resear#FULLTEXT-338]
- (RQ2|NEUTRAL) The verification pipeline assigns a three-way label (Existing, Unresolved, Fabricated) and was audited against human labels with Cohen's kappa = 0.63. -- [SCI-000144#abstract-contributions#FULLTEXT-378]
- (RQ3|NEUTRAL) As a construct-validity threat, the pipeline relies on Crossref and Semantic Scholar, neither of which indexes everything, so some 'fabricated' labels may be false positives (e.g., preprints, workshop papers, or regional-venue articles absent from both databases). -- [SCI-000144#6-discussion-6-3-threats-to-validity#FULLTEXT-380]
- (RQ2|NEUTRAL) The system's standardization of the SLR process can potentially lead to more consistent and replicable research outcomes, though it requires human oversight in guiding and interpreting results. -- [SCI-000158#section-5-discussion-section-8-conclusio#FULLTEXT-433]
- (RQ2|NEUTRAL) Peer-review feedback on EvoScientist-generated manuscripts exposed protocol-level issues (ambiguities in stability gating, metric reporting, and baseline fairness), leading the authors to conclude that strict consistency auditing and reproducibility-complete reporting are required in end-to-end discovery systems. -- [SCI-000186#appendix-e-case-studies-peer-review-feed#FULLTEXT-503]
- (RQ2|NEUTRAL) The authors flag that EvoScientist, because it learns from existing literature, may reproduce biases in data and writing and therefore should be monitored and audited — an acknowledgment that its self-evolution mechanism carries academic-integrity risk. -- [SCI-000186#7-limitations-and-ethical-considerations#FULLTEXT-504]

## [C1] verdict=UNRESOLVED bucket=unresolved score=0.111 claims=15
### The paper identifies the unclear accuracy of Generative AI in research as one of the challenges for effectively integrating AI into research workflows.
Supporting studies: SCI-000007, SCI-000066, SCI-000089, SCI-000126, SCI-000135, SCI-000141, SCI-000156, SCI-000158, SCI-000186
Member claims:
- (RQ1|NEUTRAL) DIVE is a multi-agent extraction framework that transforms figure-centric scientific content into structured, machine-actionable data, demonstrating that multi-agent workflows can convert heterogeneous literature into AI-ready formats. -- [SCI-000007#abstract#FULLTEXT-001]
- (RQ1|NEUTRAL) A locally executed agentic AI framework for deduplication, screening, and structured data extraction in systematic reviews was developed and validated, reported following PRISMA-trAIce guidelines, indicating design emphasis on transparent reporting of AI use in evidence synthesis. -- [SCI-000066#abstract#FULLTEXT-009]
- (RQ1|NEUTRAL) The framework consists of a multiagent pipeline of specialized agents for deduplication, title/abstract screening, structured data extraction, and verification, executed entirely locally. -- [SCI-000066#abstract#FULLTEXT-010]
- (RQ1|NEUTRAL) The LLM-based system automatically extracted and summarized structured data from research paper PDFs using OpenAI's o3 model via API, with a strict JSON schema requiring filename, theme, category, time, place, person, and a 3-5 item Japanese plain-language bullet-point summary. -- [SCI-000089#methods-intervention-and-control#FULLTEXT-036]
- (RQ3|NEGATIVE) The system requires manual downloading of PDF files meaning full automation of the evidence synthesis workflow has not yet been achieved, and the study focused exclusively on data extraction without evaluating upstream processes such as literature search, screening, or article selection. -- [SCI-000089#discussion-limitations#FULLTEXT-041]
- (RQ1|NEUTRAL) BIORESEARCHER is a scenario-guided multi-agent system in which a master orchestrator selects a versioned scenario playbook, decomposes the query, and delegates to specialized, state-isolated subagents that publish provenanced artifacts, targeting auditable workflows for heterogeneous biomedical sources. -- [SCI-000126#system-architecture#FULLTEXT-254]
- (RQ1|NEUTRAL) The paper states that general-purpose foundation models and off-the-shelf tool-augmented or multi-agent systems fall short on the auditable, scenario-specific workflows that heterogeneous biomedical sources demand, motivating the architecture. -- [SCI-000126#introduction#FULLTEXT-256]
- (RQ3|NEGATIVE) The authors state that these results do not imply orchestration alone solves autonomous biological discovery, but that a translational agent can retain competitive data-analysis ability while adding the surrounding machinery of entity grounding, scenario-specific methodology, source separation and final dossier construction. -- [SCI-000126#evaluation#FULLTEXT-262]
- (RQ1|NEUTRAL) AutoSynthesis is an end-to-end multi-agent framework that automates the complete meta-analysis workflow from literature retrieval and study screening to quantitative data extraction, effect size computation, and statistical synthesis. -- [SCI-000135#body#FULLTEXT-304]
- (RQ2|NEUTRAL) The paper identifies the unclear accuracy of Generative AI in research as one of the challenges for effectively integrating AI into research workflows. -- [SCI-000141#abstract#FULLTEXT-358]
- (RQ3|NEUTRAL) The paper contrasts full-automation frameworks such as The AI Scientist with its own approach, arguing that fully autonomous, rigid pipeline-driven processes limit the role of the researcher and fall short of the goal of a customizable, human-orchestrated platform. -- [SCI-000141#3-related-work-3-2-multi-task-assistants#FULLTEXT-361]
- (RQ3|NEUTRAL) The paper identifies four research challenges for AI-assisted research — lacking domain-specific AI literacy, prompt-engineering skill, integrating existing tools into AI workflows, and orchestrating multiple AI agents to accomplish a single task — which its modular framework is designed to address. -- [SCI-000141#1-introduction#FULLTEXT-362]
- (RQ1|NEUTRAL) The primary objective is a system that automatically generates the literature review segment of a research paper using only the PDF files of related papers as input. -- [SCI-000156#body#FULLTEXT-422]
- (RQ1|NEUTRAL) The multi-agent system operates through four sequential agents: (1) search string generation agent, (2) paper selection agent, (3) data extraction agent, and (4) data compilation agent — each with a defined role and handoff. -- [SCI-000158#sami-et-al-results-search-string-and-rqs#FULLTEXT-431]
- (RQ1|NEGATIVE) EvoScientist formulates multi-agent evolution as a core requirement for end-to-end scientific discovery, explicitly treating accumulated interaction histories as a first-class resource for reuse rather than discarding them after execution. -- [SCI-000186#1-introduction#FULLTEXT-499]

## [C47] verdict=UNRESOLVED bucket=unresolved score=0.222 claims=14
### vitaLITy 2 is released as open-source software alongside its paper corpus to support reproducible, re-usable literature review methods.
Supporting studies: SCI-000114, SCI-000115, SCI-000125, SCI-000151, SCI-000154, SCI-000156, SCI-000158, SCI-000179, SCI-000181
Member claims:
- (RQ1|NEUTRAL) The corpus was augmented with a scraper to extract recent papers (2021–2023), yielding an augmented dataset of 66,692 papers searchable via three embedding models. -- [SCI-000114#4-1-dataset-of-academic-articles#FULLTEXT-159]
- (RQ1|NEUTRAL) vitaLITy 2 is released as open-source software alongside its paper corpus to support reproducible, re-usable literature review methods. -- [SCI-000114#7-conclusion#FULLTEXT-161]
- (RQ3|NEGATIVE) Named limitation: LLM-generated literature summaries are 'far from sufficient' for direct paper inclusion because the corpus contains only metadata, not full text — motivating future work to chunk full texts and embed them in the vector database. -- [SCI-000114#6-discussion-limitations-future-work#FULLTEXT-168]
- (RQ3|NEGATIVE) In extraction, all models exceeded 90% match rates for titles and publishing sources, but author attribution and reference identification remained error prone with up to 40% of attempts yielding partial matches or failures. -- [SCI-000115#3-results-3-1-model-performance-varies-s#FULLTEXT-177]
- (RQ3|NEUTRAL) The evaluation benchmark collected 1,105 human-written literature reviews from 51 journals across six disciplines (Annual Reviews) as ground truth, and evaluates five LLMs across three writing tasks. -- [SCI-000125#1-introduction#FULLTEXT-251]
- (RQ3|NEGATIVE) The evaluation relies on Semantic Scholar (chosen over Google Scholar due to the latter's lack of an accessible API), which may result in incomplete reference retrieval. -- [SCI-000125#5-conclusion#FULLTEXT-252]
- (RQ3|NEGATIVE) On the large Scopus dataset (2,576 articles), LLAssist flagged 324 articles (12.6%) as must-read but only 100 (3.9%) as potentially contributing, reflecting a highly selective relevance filter. -- [SCI-000151#4-2-large-dataset-test#FULLTEXT-397]
- (RQ1|NEUTRAL) OpenScholar introduces the OpenScholar DataStore (OSDS), a fully open, up-to-date corpus of 45 million scientific papers and 236 million passage embeddings, explicitly positioned as a reproducible foundation for training and inference in literature synthesis. -- [SCI-000154#introduction#FULLTEXT-411]
- (RQ3|NEUTRAL) ScholarQABench is the first large-scale multi-domain benchmark for literature search, comprising 2,967 expert-written queries and 208 long-form answers across computer science, physics, neuroscience and biomedicine. -- [SCI-000154#abstract#FULLTEXT-420]
- (RQ1|NEUTRAL) The system pipeline takes DOIs and PDFs of multiple papers as input, using PYPDF2 and Regular Expression libraries to collect each PDF's abstract, introduction, and conclusion before summarization. -- [SCI-000156#body#FULLTEXT-423]
- (RQ1|NEUTRAL) The paper selection agent applies inclusive and exclusive filtering criteria based on titles to refine search results, ensuring only the most pertinent literature is considered. -- [SCI-000158#section-4-1-llm-based-multi-agent-system#FULLTEXT-432]
- (RQ3|NEUTRAL) Stage S2 performed multi-source retrieval by querying Google Scholar and OpenAlex, retrieving and normalizing 20 candidate papers into a unified data schema spanning different publishers, venues, and publication years. -- [SCI-000179#results-and-discussion-multi-source-retr#FULLTEXT-483]
- (RQ1|NEUTRAL) The proposed LLM+RAG architecture features specialized document processing for scientific papers, biomedical-specific vector embeddings, advanced retrieval strategies, and integrates with PubMed and other biomedical databases with natural language interfaces. -- [SCI-000181#abstract#FULLTEXT-487]
- (RQ1|POSITIVE) The system uses biomedical-specific vector embeddings trained on massive corpora of biomedical text, with comparative evaluations documenting that specialized biomedical embeddings improve retrieval performance compared to general-purpose embeddings on domain-specific information retrieval tasks. -- [SCI-000181#vector-database#FULLTEXT-488]

## [C52] verdict=UNRESOLVED bucket=unresolved score=0.222 claims=16
### Individual human reviewers averaged 88.8% accuracy and 57.1% F1, while advanced reasoning LLMs achieved 87.5% accuracy and 64.0% F1 against gold-standard labels.
Supporting studies: SCI-000115, SCI-000124, SCI-000127, SCI-000131, SCI-000138, SCI-000140, SCI-000142, SCI-000152, SCI-000164
Member claims:
- (RQ3|NEUTRAL) The screening gold standard showed high inter-rater reliability: across 244 screened documents the two expert reviewers agreed on 92.2% of decisions (kappa = 0.804), with kappa per source type of 0.718 (PB), 0.831 (IR), 0.818 (RP), and 0.812 (NMB). -- [SCI-000115#2-methods-2-2-1-human-in-the-loop-benchm#FULLTEXT-181]
- (RQ3|NEGATIVE) While screening reliability was high (kappa = 0.80), reliability statistics were not computed for the analysis and synthesis rubric scores, which were reconciled through consensus and remain sensitive to reviewer expertise and rubric design. -- [SCI-000115#4-discussion#FULLTEXT-182]
- (RQ2|NEUTRAL) Gold-standard labels rest on expert consensus, with each article independently evaluated by two reviewers who engaged in written, evidence-based reconciliation on disagreement. -- [SCI-000124#body#FULLTEXT-235]
- (RQ3|NEUTRAL) Individual human reviewers averaged 88.8% accuracy and 57.1% F1, while advanced reasoning LLMs achieved 87.5% accuracy and 64.0% F1 against gold-standard labels. -- [SCI-000124#body#FULLTEXT-238]
- (RQ3|NEUTRAL) The LLM-as-a-Judge protocol was validated against human medical experts, yielding strong Pearson correlations (r = 0.65–0.81, p < 0.01) across models and workflows. -- [SCI-000127#5-1-validation-of-the-llm-j-protocol-h1#FULLTEXT-275]
- (RQ2|NEGATIVE) Aris cannot guarantee that any output is correct, novel, or scientifically sound; cross-model review reduces some failure modes without eliminating them, and citation grounding via DBLP and CrossRef reduces but does not eliminate bibliography fabrication. -- [SCI-000131#discussion-limitations-and-responsible-u#FULLTEXT-297]
- (RQ2|NEUTRAL) On the NCD corpus, Kernel achieved 95% agreement with expert inclusion/exclusion judgments and three-way concordance among Kernel, the LLM, and the human assessor reached 91%, with Cohen's Kappa of 0.70 for Kernel versus human annotations, evidencing inter-rater reliability. -- [SCI-000138#results#FULLTEXT-334]
- (RQ2|NEGATIVE) A reproducible human audit of a 20% random sample (272 of roughly 1,360 items) of the scored benchmark results agreed with 96% of automated judge verdicts (Cohen’s κ = 0.94), with all 11 discrepancies confined to one-step severity nuances in the grounding benchmark and none reversing a supported/unsupported call. -- [SCI-000140#discussion-limitations#FULLTEXT-345]
- (RQ3|POSITIVE) On the grounding benchmark, inter-judge reliability is moderate (three-judge Fleiss’ κ = 0.50 with-BR and 0.72 without-BR), mostly driven by a single lenient judge (Codex GPT-5.5 per-judge verified rate 0.31 versus 0.21 and 0.22), and each judge independently shows a large with-BR grounding gain (0.21/0.04 for Gemini, 0.31/0.04 for Codex, 0.22/0.08 for Claude). -- [SCI-000140#supplementary-methods-s11-1-benchmark-co#FULLTEXT-351]
- (RQ2|NEUTRAL) Title and abstract screening uses a test-retest reliability approach with two independent LLM screening passes at temperature 0.3, quantified using Cohen's kappa, with a minimum threshold of 0.60 below Cochrane's 0.80 for dual review. -- [SCI-000142#methods-search-and-screening#FULLTEXT-367]
- (RQ1|NEGATIVE) A limitation noted is that timing the entire screening process for two raters would have provided more reliable results, as a well-planned parallel two-human-rater process might have taken almost the same time as one rater using LLMs, which was not reflected in the study. -- [SCI-000152#results#FULLTEXT-400]
- (RQ2|NEGATIVE) The study finds that the human rater and both LLMs performed poorly in sensitivity, especially GPT-4o Mini, meaning they failed to include all relevant articles, which is problematic because the main goal of SLRs is to include all available research results on a topic. -- [SCI-000152#discussion#FULLTEXT-402]
- (RQ2|NEUTRAL) The study uses a benchmark constructed by combining the title/abstract ratings of the human rater and both LLMs as the ground truth, which the authors acknowledge has limitations in measuring human performance reliably. -- [SCI-000152#conclusions#FULLTEXT-403]
- (RQ3|NEUTRAL) Combining the three different ratings revealed that 17.1% of the articles had to be rescreened due to discrepancies (152/887), a rescreening rate that is high especially for SLRs where thousands of articles are screened. -- [SCI-000152#results#FULLTEXT-404]
- (RQ3|NEUTRAL) The human rater achieved accuracy of 96.05%, sensitivity of 86.89% and specificity of 96.73%, compared with GPT-4o Mini at 91.88% accuracy, 59.02% sensitivity and 94.31% specificity. -- [SCI-000152#results#FULLTEXT-408]
- (RQ3|NEUTRAL) The manual extraction of inclusion/exclusion criteria and research questions for the benchmark was validated with a second author on 15 SLRs: all 23 extracted research questions matched exactly, and 97 of 99 inclusion/exclusion criteria matched, evidencing high inter-rater reliability. -- [SCI-000164#3-1-extension-with-inclusion-exclusion-c#FULLTEXT-461]

## [C5] verdict=UNRESOLVED bucket=unresolved score=0.1 claims=16
### The full pipeline, including all code, cost logs, and prompts, is publicly released on GitHub.
Supporting studies: SCI-000082, SCI-000090, SCI-000106, SCI-000110, SCI-000118, SCI-000122, SCI-000137, SCI-000142, SCI-000179, SCI-000186
Member claims:
- (RQ1|NEUTRAL) Each pipeline step is auditable with its own logging of agent behavior, scripts, images, and reports. -- [SCI-000082#body#FULLTEXT-016]
- (RQ1|NEGATIVE) EcoXAI is organized around discrete, auditable pipelines rather than a single monolithic agent, spanning ingestion, EDA, normalization, predictive analysis, and hypothesis generation. -- [SCI-000082#body#FULLTEXT-017]
- (RQ2|NEUTRAL) To mitigate susceptibility to planning errors and cascading failures, EcoXAI enforces strict isolation across pipeline stages and persists intermediate code and experimental logic for human inspection and reproduction. -- [SCI-000082#body#FULLTEXT-020]
- (RQ1|NEGATIVE) The pipeline couples screening with structured abstract-level extraction and high-level synthesis using fixed prompts and schemas, operationalizing a local-first workflow that does not depend on proprietary cloud models. -- [SCI-000090#discussion#FULLTEXT-043]
- (RQ1|NEGATIVE) The pipeline is fully local and zero-shot, running on consumer-grade hardware (Apple M1 Max) with the gpt-oss-20b model via Ollama, requiring no cloud APIs or proprietary models — enabling full reproducibility. -- [SCI-000090#discussion#FULLTEXT-044]
- (RQ1|NEUTRAL) The paper identifies that model updates can invalidate previously crafted prompts and break reliable pipelines, while cross-model behaviour and accuracy diverges significantly using identical prompts, eroding trust and widening the reproducibility gap in SLRs. -- [SCI-000106#introduction#FULLTEXT-096]
- (RQ1|NEUTRAL) The system orchestrates data flow across multiple backends: LangGraph routes multi-step queries to the appropriate data store, and the LiteralAI API logs all user interactions to promote transparency and accountability — a concrete audit-trail mechanism. -- [SCI-000110#2-5-modular-integration-and-front-end-in#FULLTEXT-138]
- (RQ1|NEUTRAL) The full pipeline, including all code, cost logs, and prompts, is publicly released on GitHub. -- [SCI-000118#body#FULLTEXT-199]
- (RQ3|NEUTRAL) Total pipeline cost ranged from $19.51 to $29.04 across five domain reviews with a median of $22.65, establishing the first empirical cost characterization of an end-to-end pipeline. -- [SCI-000118#body#FULLTEXT-205]
- (RQ1|NEUTRAL) The generated rule set is surfaced for expert review before execution, allowing conditions to be inspected and refined so the pipeline can be audited and corrected prior to running selection. -- [SCI-000122#2-1-trial-selection-and-structuring#FULLTEXT-222]
- (RQ1|NEUTRAL) Stable record identifiers were preserved throughout the entire input, model-output, merging, and analysis pipeline, enabling traceability of each screening decision back to its source record. -- [SCI-000137#methods-integrity-checks-and-safeguard-p#FULLTEXT-317]
- (RQ3|NEUTRAL) Reporting should describe enough of the complete pipeline to make the evaluated system interpretable: model and interface version, prompts, input preparation, processing configuration, interaction structure, human involvement, output handling, advancement rules, recovery, missed cases, downstream workload, agreement, and repeated-run consistency. -- [SCI-000137#discussion-implications-for-llm-workflow#FULLTEXT-325]
- (RQ1|NEUTRAL) meta-pipe comprises 10 sequential stages each implemented as a self-contained skill module with defined inputs, outputs, and quality thresholds, with inter-stage data contracts specifying file schemas at each boundary. -- [SCI-000142#methods-pipeline-architecture#FULLTEXT-365]
- (RQ1|NEUTRAL) Stage S1 (request intake) logs validated requests and assigns unique identifiers to guarantee idempotent behavior, preventing duplicate processing and establishing a secure, traceable entry point for the pipeline. -- [SCI-000179#materials-and-methods-stage-s1-request-i#FULLTEXT-472]
- (RQ1|POSITIVE) The authors state the workflow supports transparent processing, enables traceability of analytical states, and facilitates efficient management of repeated executions. -- [SCI-000179#results-and-discussion-incremental-proce#FULLTEXT-474]
- (RQ1|NEUTRAL) The engineer agent's experiment tree search stores a structured execution record per attempt that includes run status, logs, and evaluation metrics, providing per-stage execution provenance. -- [SCI-000186#3-4-engineer-agent-for-experiment-tree-s#FULLTEXT-502]

## [C11] verdict=UNRESOLVED bucket=unresolved score=0.438 claims=19
### Evaluation is limited by the number of benchmark meta-analyses and cannot establish robust performance across all potential settings, domains, and study designs.
Supporting studies: SCI-000088, SCI-000090, SCI-000099, SCI-000110, SCI-000114, SCI-000120, SCI-000122, SCI-000124, SCI-000127, SCI-000131, SCI-000135, SCI-000140, SCI-000151, SCI-000152, SCI-000158, SCI-000159
Member claims:
- (RQ3|NEGATIVE) Stated limitations include unexplained residual heterogeneity (particularly for specificity in title/abstract screening), most studies being methodological rather than real-world evaluations, a small number of full-text screening studies, and performance estimates depending on human-defined reference standards that are themselves subject to error. -- [SCI-000088#discussion-limitations#FULLTEXT-034]
- (RQ2|NEUTRAL) Performance tracked the density and explicitness of source text: when constructs were explicitly encoded in abstracts, maximal sensitivity was achieved; when outcomes were inconsistently reported, screening was rate-limited by missing or underspecified inputs. -- [SCI-000090#discussion#FULLTEXT-046]
- (RQ3|NEGATIVE) Limitation: The evaluation was proof-of-concept benchmarking against three published systematic reviews rather than fully independent external validation against a prospective gold standard; single-author adjudication was used without blinded dual review. -- [SCI-000090#discussion#FULLTEXT-049]
- (RQ3|NEGATIVE) Reported evaluation limitations include only a small number of test cases that may not capture robustness or generalizability, evidence integration currently limited to three sources (CIViC, PharmGKB, Gene Enrichment), and all evaluations conducted using the single GPT-4.1-mini model. -- [SCI-000099#limitations#FULLTEXT-071]
- (RQ3|NEUTRAL) Named limitations include dependence of classification/clustering accuracy on training-data quality (with diminished performance in underrepresented BHI subdomains) and the absence of formal user-adoption studies. -- [SCI-000110#5-limitations-and-future-directions#FULLTEXT-146]
- (RQ3|NEUTRAL) Context-window limits are identified as a design constraint: token limits (e.g., 16K tokens for GPT-3.5) can restrict analyses over large corpora, motivating the RAG + prompt-chaining architecture. -- [SCI-000114#3-llm-limitations-motivation#FULLTEXT-167]
- (RQ3|NEGATIVE) Stated limitations include findings specific to climate change adaptation literature in the food sector, evaluation conducted exclusively on GPT-4o without testing other LLMs, and the recommendation of a human-in-the-loop system because models cannot completely replace the expert-driven process. -- [SCI-000120#5-limitations#FULLTEXT-215]
- (RQ3|NEUTRAL) Named limitation: the framework depends on accurate extraction/structuring of eligibility criteria (bounded by trial reporting quality) and currently relies on curated registries such as ClinicalTrials.gov, missing information often found only in the literature. -- [SCI-000122#4-discussion-limitations-and-future-dire#FULLTEXT-230]
- (RQ2|NEUTRAL) Errors commonly resulted from superficial linguistic cues, with models frequently misinterpreting keywords like longitudinal or sensitivity as automatic evidence of rigorous methodological approaches. -- [SCI-000124#abstract#FULLTEXT-234]
- (RQ3|NEUTRAL) Named limitations: abstracts are used as a proxy for full texts (missing study nuances), human validation involved only 9 expert annotators on a subset of models/settings, and the benchmark covers just 81 meta-analyses and 24 specialties. -- [SCI-000127#7-conclusion-limitations#FULLTEXT-273]
- (RQ3|NEUTRAL) The main limitations are the absence of controlled evaluation and reliance on observational deployment evidence; future work includes compute-matched comparisons to estimate the contribution of cross-model heterogeneity. -- [SCI-000131#conclusion#FULLTEXT-302]
- (RQ2|NEUTRAL) Automated heterogeneity diagnostics and publication bias tests were broadly comparable to the human benchmark, finding substantial between-study heterogeneity and small-study effects. -- [SCI-000135#body#FULLTEXT-309]
- (RQ3|NEGATIVE) Evaluation is limited by the number of benchmark meta-analyses and cannot establish robust performance across all potential settings, domains, and study designs. -- [SCI-000135#body#FULLTEXT-313]
- (RQ3|NEGATIVE) The observed differences from the benchmark primarily originated from literature retrieval rather than downstream statistical analysis, largely because relevant studies were missed or full-texts were unavailable. -- [SCI-000135#body#FULLTEXT-314]
- (RQ3|NEGATIVE) Limitations reported for Brain Researcher include same-dataset multiverse or internal validation that does not replace independent replication or constitute external confirmation; possible memorization because datasets such as HCP and OpenNeuro are public; unmeasured runtime and researcher effort; and a review-layer calibration library that is not an independent, field-scale estimate (no false-accepts in 16 invalid cases and no false-blocks in 5 valid controls, with a rule-of-three 95% upper bound of 19%). -- [SCI-000140#discussion-limitations#FULLTEXT-350]
- (RQ3|NEGATIVE) Named limitation: relevance assessment did not use available metadata (e.g., publication year, citation counts), different LLM backends require per-model prompt tuning, and analysis was limited to titles and abstracts, missing full-text information. -- [SCI-000151#5-1-overall-performance#FULLTEXT-396]
- (RQ3|NEGATIVE) The authors recommend conducting title/abstract screening with two human raters if budget and time constraints allow, accompanied by LLMs to correct for mistakes, concluding that LLMs are not reliable enough to substitute human experts. -- [SCI-000152#conclusions#FULLTEXT-407]
- (RQ3|NEUTRAL) Future work will address search strategy refinement, explicit inclusion/exclusion criteria, advanced data extraction algorithms (ML/NLP), robust analytical frameworks, broader literature scope, and stakeholder engagement. -- [SCI-000158#sami-et-al-limitations-and-future-work#FULLTEXT-434]
- (RQ3|NEUTRAL) Limitation: The evaluation dataset with human-written answers is relatively small (110 for CS-LFQA, 108 for expert-written answers), potentially introducing statistical variance; SCHOLARQABENCH focuses only on CS, biomedicine, and physics. -- [SCI-000159#limitations#FULLTEXT-447]

## [C17] verdict=UNRESOLVED bucket=unresolved score=0.118 claims=23
### The paper highlights reproducibility concerns arising from the opacity of closed-source models in systematic review automation.
Supporting studies: SCI-000096, SCI-000108, SCI-000110, SCI-000111, SCI-000114, SCI-000115, SCI-000119, SCI-000125, SCI-000129, SCI-000131, SCI-000138, SCI-000141, SCI-000151, SCI-000156, SCI-000172, SCI-000179, SCI-000186
Member claims:
- (RQ1|NEUTRAL) LatteReview integrates Retrieval-Augmented Generation (RAG) workflows, allowing reviewers to dynamically fetch relevant information and incorporate retrieved data into the review process for grounding. -- [SCI-000096#section-3-6-retrieval-augmented-generati#FULLTEXT-051]
- (RQ1|NEUTRAL) LatteReview's ReviewWorkflow class orchestrates multi-stage review processes with sequential rounds, parallel reviews, conditional filtering, and output aggregation — providing structured provenance for each decision. -- [SCI-000096#section-3-4-multi-reviewer-workflows#FULLTEXT-052]
- (RQ2|NEGATIVE) The framework encourages human oversight, recommending researchers break reviews into stages with manual review checkpoints rather than pursuing fully automated end-to-end processes. -- [SCI-000096#section-5-8-integrate-human-oversight#FULLTEXT-056]
- (RQ1|NEUTRAL) This paper presents a template for future evaluations of LLMs in the context of data extraction for systematic review automation, and the authors advise caution when integrating models such as GPT-4 into tools, calling for further research on stability and reliability. -- [SCI-000108#abstract#FULLTEXT-114]
- (RQ1|NEUTRAL) A continuously updated 'living' database structure lets the review reflect near real-time shifts in the evidence base, addressing the lag of conventional reviews. -- [SCI-000110#4-3-dynamic-integration-and-timely-evide#FULLTEXT-136]
- (RQ1|NEUTRAL) The paper highlights reproducibility concerns arising from the opacity of closed-source models in systematic review automation. -- [SCI-000111#body#FULLTEXT-151]
- (RQ1|NEUTRAL) The tool combines RAG with prompt chaining, implemented with the LangChain open-source library, breaking complex literature-review tasks into a series of smaller LLM steps. -- [SCI-000114#4-vitality-2#FULLTEXT-160]
- (RQ2|NEUTRAL) The RAG architecture is positioned as a hallucination-mitigation mechanism: retrieving only relevant information from the local corpus reduces prompt size and minimizes the risk of hallucination. -- [SCI-000114#4-vitality-2#FULLTEXT-164]
- (RQ1|NEUTRAL) KSR argues that oversight in LLM-assisted synthesis must be operationalized as auditable workflows with transparent prompt and model documentation, explicit evaluation criteria, and mechanisms for preserving disagreement across sources. -- [SCI-000115#4-discussion#FULLTEXT-170]
- (RQ1|NEUTRAL) LLMs have the potential to assist researchers in generating Boolean queries for systematic reviews, with the paper reproducing and extending prior work on LLM-based query generation. -- [SCI-000119#abstract#FULLTEXT-206]
- (RQ3|NEUTRAL) The paper reports an extensive study of Boolean query generation using LLMs for systematic reviews, reproducing and extending prior work to assess reproducibility and generalizability. -- [SCI-000119#abstract#FULLTEXT-207]
- (RQ2|POSITIVE) All LLMs demonstrated a significant increase in reference precision when generating references within the Review Composition task compared to the standalone Reference Generation task. -- [SCI-000125#4-experiments-4-2-main-results#FULLTEXT-241]
- (RQ2|POSITIVE) Grounding generated text with real external citations reduces hallucination: when LLMs generate references alongside the review text, reference accuracy improves markedly, suggesting a mutual constraint between references and review text that enhances reliability. -- [SCI-000125#4-experiments-4-2-main-results#FULLTEXT-244]
- (RQ1|NEUTRAL) Verification was applied through cross-checking among human reviewers (manual) and double-checking via comparison with manual results plus review of discrepancies (LLM-assisted). -- [SCI-000129#barros-et-al-verification-and-risk-mitig#FULLTEXT-286]
- (RQ2|NEUTRAL) Hybrid workflows are essential: LLMs should be embedded in workflows combining partial automation with targeted human supervision — complete delegation risks loss of methodological rigor. -- [SCI-000129#section-5-discussion#FULLTEXT-287]
- (RQ1|NEUTRAL) ARIS decomposes the research workflow into five end-to-end workflows chained through plain-text artifact contracts, with a per-project research wiki providing persistent cross-session memory of papers, ideas, experiments, and tracked claims. -- [SCI-000131#methods-workflow-library-overview#FULLTEXT-295]
- (RQ1|POSITIVE) Full-text synthesis employs retrieval-augmented generation (RAG) with hybrid vector and graph-based retrieval, and RAG outperformed non-retrieval generation for queries requiring structured constraints, cross-study integration, and graph-based reasoning, while non-RAG remained competitive for high-level summaries. -- [SCI-000138#abstract#FULLTEXT-327]
- (RQ1|NEUTRAL) External tools (Crossref, ORCID, Semantic Scholar, ORKG) are integrated into a Tool Library, called automatically by the LLM and made dynamically addable via the Model Context Protocol (MCP), including support for users to set up MCP servers for REST-endpoint tools. -- [SCI-000141#4-framework-for-ai-assisted-research-4-1#FULLTEXT-353]
- (RQ1|NEUTRAL) LLAssist emits structured JSON and CSV outputs containing extracted semantics, relevance scores, and reasoning, deliberately requiring downstream analysis to enforce a human-in-the-loop workflow with process visibility. -- [SCI-000151#2-1-5-output-generation#FULLTEXT-387]
- (RQ2|NEGATIVE) The pipeline merges assistant responses per paper into a final review segment without any described verification or cross-checking of the generated content against sources. -- [SCI-000156#body#FULLTEXT-425]
- (RQ1|NEUTRAL) A progressive five-step testing methodology was implemented, scaling from 1 article with 10 manual questions (Experiment #1) to 30 articles with 10 AI-generated cross-document synthesis questions (Experiment #5). -- [SCI-000172#methodology#FULLTEXT-462]
- (RQ1|NEGATIVE) The workflow supports multiple literature-review stages (paper retrieval, preliminary screening, review management) while maintaining human oversight and methodological control, with AI employed as a supportive component rather than a replacement for researcher judgment. -- [SCI-000179#abstract#FULLTEXT-477]
- (RQ1|NEUTRAL) EvoScientist's pipeline integrates external retrieval infrastructure via the Semantic Scholar API for the initial literature review phase, alongside Gemini-based idea generation and Claude-based code generation. -- [SCI-000186#4-5-implementation-details#FULLTEXT-500]

## [C2] verdict=UNRESOLVED bucket=unresolved score=0.25 claims=32
### In Stage S3, DOI-based deduplication detected no duplicate records, yielding a clean dataset of 20 unique publications.
Supporting studies: SCI-000056, SCI-000068, SCI-000071, SCI-000082, SCI-000088, SCI-000100, SCI-000102, SCI-000109, SCI-000110, SCI-000114, SCI-000122, SCI-000124, SCI-000125, SCI-000126, SCI-000129, SCI-000148, SCI-000154, SCI-000156, SCI-000159, SCI-000179
Member claims:
- (RQ1|NEGATIVE) TrialScout uses an LLM to classify publications based on the text of abstracts rather than relying on NCT-ID searches or metadata matching, allowing it to use information not present in metadata alone and distinguish true result publications from protocols, secondary analyses, and reviews. -- [SCI-000056#discussion-comparison-to-previous-resear#FULLTEXT-002]
- (RQ2|NEUTRAL) Human error accounted for a larger proportion of discrepancies (61.5%) than TrialScout error across all 200 reviewed cases, suggesting the tool may be more accurate than manual search in practice. -- [SCI-000056#results-validation-of-trialscout-against#FULLTEXT-003]
- (RQ2|POSITIVE) Manual review of 200 discrepant cases showed that 79% of initially classified false positives were in fact true positives missed by the original manual search, and 44% of false negatives were true negatives, suggesting TrialScout's true performance is higher than metrics suggest. -- [SCI-000056#results-validation-of-trialscout-against#FULLTEXT-004]
- (RQ2|NEGATIVE) TrialScout's classifications are not deterministic; repeating a run can produce different results and this variability was not quantified, representing a reproducibility limitation. -- [SCI-000056#discussion-limitations#FULLTEXT-005]
- (RQ3|NEUTRAL) TrialScout achieved an F-score of 92.7% against the human reference standard across 5,774 trials, with sensitivity of 92.5% and specificity of 81.2%. -- [SCI-000056#results-validation-of-trialscout-against#FULLTEXT-007]
- (RQ3|POSITIVE) TrialScout detected published results for 63.6% of 9,600 randomly sampled trials, higher than the 53% estimated in a recent meta-analysis, with 72.9% having any reported results including summary results. -- [SCI-000056#results-identification-of-results-from-r#FULLTEXT-008]
- (RQ3|NEUTRAL) The study explores the capability of LLMs to accurately extract explicit data from academic papers, contributing to advancing SLR automation. -- [SCI-000068#abstract#FULLTEXT-011]
- (RQ1|NEUTRAL) ENTGPT is a GPT-4o-based screening system that implements the novel STARR (screening of title and abstracts, reevaluation, and full-text review) protocol for systematic review screening. -- [SCI-000071#abstract#FULLTEXT-012]
- (RQ3|NEUTRAL) In this proof-of-concept study, ENTGPT (based on GPT-4o) was compared to two human reviewers for article inclusion/exclusion decisions in systematic review screening. -- [SCI-000071#abstract#FULLTEXT-013]
- (RQ1|NEUTRAL) Discovery memory stores prior hypotheses and validation outcomes in semantic vector format, enabling RAG-based similarity search to avoid redundant hypothesis generation. -- [SCI-000082#body#FULLTEXT-015]
- (RQ1|NEUTRAL) This systematic review and meta-analysis of 18 studies (2023-2025) evaluates LLM-assisted medical literature screening as a workflow stage in evidence synthesis, following PRISMA-DTA guidance and searching PubMed, Web of Science, Embase, Cochrane Library, and Google Scholar from 1 January 2022 to 17 November 2025. -- [SCI-000088#abstract-methods#FULLTEXT-025]
- (RQ2|NEUTRAL) A multi-agent validation loop uses a generator LLM to draft cited answers and a secondary QA agent LLM to audit factual accuracy, logical consistency, and adherence to citation protocols. -- [SCI-000100#body#FULLTEXT-076]
- (RQ2|NEGATIVE) The Gemini-3-pro LLM response component is activated only when no high-quality evidence is available, and its generated content is retained only if subsequently supported by evidence retrieved from source databases. -- [SCI-000102#methods-director-layer-processing-strate#FULLTEXT-089]
- (RQ1|NEUTRAL) TrialMind incorporates RAG to enrich context with knowledge sourced from PubMed and employs chain-of-thought processing to generate more exhaustive literature-search terms. -- [SCI-000109#body#FULLTEXT-127]
- (RQ3|POSITIVE) Citation screening is evaluated with Recall@20 and Recall@50, where TrialMind greatly improved ranking performances over the best baselines (fold changes from 1.3 to 2.6 across four topics). -- [SCI-000109#body#FULLTEXT-132]
- (RQ3|NEUTRAL) Study search performance is assessed using overall Recall to evaluate effectiveness in identifying all relevant studies from the PubMed database. -- [SCI-000109#body#FULLTEXT-135]
- (RQ2|NEUTRAL) A Bi-LSTM model trained on an extended PubMed-PICO dataset identifies whether an abstract conforms to PICOS standards, and LLM-based hierarchical classification of study designs is stored in PostgreSQL for later query-based filtering — a methodological-quality screen before inclusion. -- [SCI-000110#2-3-automated-pico-compliance-detection-#FULLTEXT-139]
- (RQ3|NEUTRAL) The Bi-LSTM PICOS-compliance model achieved 87% accuracy in identifying PICOS-compliant abstracts, helping curators avoid downstream inclusion of substandard studies. -- [SCI-000110#3-4-pico-compliance-detection#FULLTEXT-148]
- (RQ2|NEUTRAL) A documented hallucination episode shows the raw LLM citing a paper absent from the corpus, and — when asked for additional relevant papers within the corpus — returning fabricated titles found neither in the database nor via Google Scholar. -- [SCI-000114#6-discussion-limitations-future-work#FULLTEXT-163]
- (RQ1|NEUTRAL) In the meta-analysis stage, LLM usage is restricted to penalty-rule specification and schema-constrained parsing, while penalty evaluation, score transformation, and statistical estimation are executed deterministically and auditable. -- [SCI-000122#2-2-eligibility-aware-meta-analysis-figu#FULLTEXT-221]
- (RQ3|NEUTRAL) Among the 39 selected gastric-cancer trials, 13 are explicitly cited in the NCCN guideline's targeted therapy / immunotherapy sections, indicating the pipeline recovers guideline-level evidence from registry data using only a free-text query. -- [SCI-000122#3-1-illustrative-example-trial-selection#FULLTEXT-225]
- (RQ1|NEUTRAL) Four state-of-the-art LLMs as of September 2025 (GPT-4o, GPT-4o-mini, GPT-o3, GPT-5) were evaluated on 14 binary methodological criteria across 180 full-text articles. -- [SCI-000124#body#FULLTEXT-232]
- (RQ3|NEUTRAL) LLM accuracy declined with article length: top-accuracy articles averaged 623 words versus 3,089 words for the bottom quintile (p<0.001). -- [SCI-000124#body#FULLTEXT-239]
- (RQ2|NEGATIVE) Generating complete and accurate author lists remains a major challenge for LLMs; applying a first-author-only matching criterion raised precision by only 1-3% across all models. -- [SCI-000125#4-experiments-4-2-main-results#FULLTEXT-243]
- (RQ3|NEGATIVE) The authors acknowledge possible test-data/training-data overlap (2023 Annual Reviews articles) and note that metrics comparing LLM output to human-written reviews may not be comprehensive, omitting aspects like coverage of cited works and structural coherence. -- [SCI-000125#5-conclusion-limitations#FULLTEXT-250]
- (RQ1|NEUTRAL) Outputs of BIORESEARCHER are auditable dossiers with normalized entities, heterogeneous evidence, ranked hypotheses, mechanistic links and retrievable provenance such as PMIDs, NCT IDs and patent numbers, preserving identifiers, uncertainty and retrievable provenance. -- [SCI-000126#system-architecture#FULLTEXT-255]
- (RQ3|NEUTRAL) Limitation: The study reflects the experience of a single researcher; sample size for data extraction was small (13 studies); manual and LLM-assisted executions were conducted in different periods, limiting generalizability. -- [SCI-000129#section-5-2-sample-size-and-scope-limita#FULLTEXT-292]
- (RQ1|NEUTRAL) An LLM-based ranking approach is proposed to select initial studies for literature review automation, addressing the bottleneck of manual data extraction from the scientific literature. -- [SCI-000148#abstract#FULLTEXT-386]
- (RQ1|NEUTRAL) OpenScholar is described as the first fully open, retrieval-augmented LM specifically designed for scientific research tasks, and all artefacts including code, models, data store, datasets and a public demo are open-sourced, supporting reproducibility. -- [SCI-000154#introduction#FULLTEXT-412]
- (RQ3|NEUTRAL) The LLM-based approach is proven to be the best-performing one based on ROUGE-N scores across all compared NLP techniques. -- [SCI-000156#body#FULLTEXT-429]
- (RQ2|NEGATIVE) Non-retrieval augmented LLMs fabricate 78–98% of cited papers, with the problem exacerbated in biomedical domains; even when citations refer to real papers, the majority are not substantiated by corresponding abstracts, resulting in near-zero citation accuracy. -- [SCI-000159#section-4-2-results-limitations-of-param#FULLTEXT-442]
- (RQ3|NEGATIVE) In Stage S3, DOI-based deduplication detected no duplicate records, yielding a clean dataset of 20 unique publications. -- [SCI-000179#results-and-discussion-deduplication-and#FULLTEXT-481]

## [C8] verdict=PROVISIONAL bucket=provisional score=0.0 claims=1
### A local Qwen 3.6 27B model running continuously for two days generated and evaluated 103 hypotheses, avoiding an estimated $300+ in Anthropic Sonnet 4.6 token pricing.
Supporting studies: SCI-000082
Member claims:
- (RQ3|NEUTRAL) A local Qwen 3.6 27B model running continuously for two days generated and evaluated 103 hypotheses, avoiding an estimated $300+ in Anthropic Sonnet 4.6 token pricing. -- [SCI-000082#body#FULLTEXT-021]

## [C12] verdict=PROVISIONAL bucket=provisional score=1.0 claims=1
### The study was powered to detect a 10-minute difference but the observed difference was 7.9 minutes with greater within-group variability than assumed, suggesting it may have been underpowered to detect an effect of this magnitude.
Supporting studies: SCI-000089
Member claims:
- (RQ3|NEGATIVE) The study was powered to detect a 10-minute difference but the observed difference was 7.9 minutes with greater within-group variability than assumed, suggesting it may have been underpowered to detect an effect of this magnitude. -- [SCI-000089#discussion-limitations#FULLTEXT-040]

## [C40] verdict=PROVISIONAL bucket=provisional score=1.0 claims=1
### Human annotators evaluated forest plots in a win/lose assessment, determining how closely each generated plot aligned with the reference and which method produced better results.
Supporting studies: SCI-000109
Member claims:
- (RQ3|POSITIVE) Human annotators evaluated forest plots in a win/lose assessment, determining how closely each generated plot aligned with the reference and which method produced better results. -- [SCI-000109#body#FULLTEXT-134]

## [C43] verdict=PROVISIONAL bucket=provisional score=0.0 claims=1
### Formal usability assessments are called essential before the system's real-world utility can be established — a clear evaluation gap.
Supporting studies: SCI-000110
Member claims:
- (RQ3|NEUTRAL) Formal usability assessments are called essential before the system's real-world utility can be established — a clear evaluation gap. -- [SCI-000110#5-limitations-and-future-directions#FULLTEXT-143]

## [C54] verdict=PROVISIONAL bucket=provisional score=1.0 claims=2
### As a benchmark limitation, LoQA focuses exclusively on Chinese water-environment questions and, per the authors, does not cover all languages, domains, or document types.
Supporting studies: SCI-000117
Member claims:
- (RQ3|NEGATIVE) As a benchmark limitation, LoQA focuses exclusively on Chinese water-environment questions and, per the authors, does not cover all languages, domains, or document types. -- [SCI-000117#7-limitations#FULLTEXT-192]
- (RQ3|NEUTRAL) The LoQA benchmark consists of 100 water-environment research questions, each paired with evidence retrieved from a Chinese expert knowledge base comprising 500 books and over 100M characters, and adds 100 random evidence fragments per question to simulate noisy context. -- [SCI-000117#2-2-1-definition-2-2-the-loqa-benchmark#FULLTEXT-195]

## [C56] verdict=PROVISIONAL bucket=provisional score=1.0 claims=1
### A three-arm extraction ablation reveals a phase-dependent architecture reversal: multi-agent design hurts screening but is essential for extraction, producing 5.7x more poolable analyses while eliminating clinically dangerous direction errors.
Supporting studies: SCI-000118
Member claims:
- (RQ3|NEGATIVE) A three-arm extraction ablation reveals a phase-dependent architecture reversal: multi-agent design hurts screening but is essential for extraction, producing 5.7x more poolable analyses while eliminating clinically dangerous direction errors. -- [SCI-000118#abstract#FULLTEXT-202]

## [C59] verdict=PROVISIONAL bucket=provisional score=0.0 claims=1
### Eligibility-aware weighting shifted the pooled risk ratio for olaparib-related all-grade vomiting from 2.18 (95% CI 1.71–2.79) under conventional Mantel–Haenszel estimation to 1.97 (95% CI 1.76–2.20), demonstrating quantifiable impact on pooled estimates.
Supporting studies: SCI-000122
Member claims:
- (RQ3|NEUTRAL) Eligibility-aware weighting shifted the pooled risk ratio for olaparib-related all-grade vomiting from 2.18 (95% CI 1.71–2.79) under conventional Mantel–Haenszel estimation to 1.97 (95% CI 1.76–2.20), demonstrating quantifiable impact on pooled estimates. -- [SCI-000122#eligmeta-results-olaparib-case-study#FULLTEXT-227]

## [C63] verdict=PROVISIONAL bucket=provisional score=0.0 claims=1
### Domain adaptation (H3) shows no statistically significant advantage for domain-fine-tuned MedGemma over Gemma when RAG provides external material (p > 0.05, Cohen's d ≤ 0.25), indicating retrieval investment may beat model specialization.
Supporting studies: SCI-000127
Member claims:
- (RQ3|NEUTRAL) Domain adaptation (H3) shows no statistically significant advantage for domain-fine-tuned MedGemma over Gemma when RAG provides external material (p > 0.05, Cohen's d ≤ 0.25), indicating retrieval investment may beat model specialization. -- [SCI-000127#5-3-the-benefits-of-domain-adaptation-h3#FULLTEXT-270]

## [C64] verdict=PROVISIONAL bucket=provisional score=0.0 claims=2
### RAG grounding improves synthesis quality across all models: the uplift over Parametric-CoT ranges from ~9% for Gemini Flash 2.5 to over 40% for the Gemma models.
Supporting studies: SCI-000127
Member claims:
- (RQ3|NEUTRAL) Even under ideal oracle retrieval (G-RAG), the top-performing model Gemini Flash 2.5 reaches only 3.16 on a 0–5 scale (3.17 with K=10 retrieval), and all models drop to ~1.0 under N-RAG — demonstrating moderate absolute capabilities. -- [SCI-000127#4-results-table-2#FULLTEXT-271]
- (RQ3|POSITIVE) RAG grounding improves synthesis quality across all models: the uplift over Parametric-CoT ranges from ~9% for Gemini Flash 2.5 to over 40% for the Gemma models. -- [SCI-000127#4-results-the-impact-of-retrieval#FULLTEXT-274]

## [C68] verdict=PROVISIONAL bucket=provisional score=0.0 claims=5
### AutoSynthesis's random-effects meta-analysis produced a pooled effect of Hedges' g = 0.143 (95% CI [0.059, 0.226], p < 0.001; Fig. 2c).
Supporting studies: SCI-000135
Member claims:
- (RQ2|NEUTRAL) AutoSynthesis performs study-level risk-of-bias assessment following ROBINS-I, covering bias from confounding through selection of the reported result. -- [SCI-000135#body#FULLTEXT-307]
- (RQ2|NEUTRAL) AutoSynthesis produces PRISMA 2020 flow diagrams, forest plots, and funnel plots to assess small-study effects and potential publication bias. -- [SCI-000135#body#FULLTEXT-308]
- (RQ3|NEGATIVE) AutoSynthesis is not positioned as a replacement for expert reviewers; the human element remains integral to formulating research questions, specifying criteria, and interpreting findings. -- [SCI-000135#body#FULLTEXT-310]
- (RQ3|NEUTRAL) AutoSynthesis's evidence base showed substantial agreement with the human benchmark, with recall of 71.4% and precision of 62.5% against studies included in the published meta-analysis. -- [SCI-000135#body#FULLTEXT-311]
- (RQ3|NEUTRAL) AutoSynthesis's random-effects meta-analysis produced a pooled effect of Hedges' g = 0.143 (95% CI [0.059, 0.226], p < 0.001; Fig. 2c). -- [SCI-000135#body#FULLTEXT-312]

## [C70] verdict=PROVISIONAL bucket=provisional score=1.0 claims=2
### Record-level consistency is a separate property from aggregate predictive performance, and repeated-run evaluations should report the number and characteristics of discordant cases rather than relying solely on differences between aggregate estimates.
Supporting studies: SCI-000137
Member claims:
- (RQ2|NEGATIVE) Two nominally identical GPT-5.4 file-batch runs agreed on 91.7% of records but disagreed on 94 individual records including 29 verified eligible records retained by only one run, showing that aggregate similarity concealed meaningful item-level instability. -- [SCI-000137#results-rq4-run-to-run-consistency#FULLTEXT-322]
- (RQ3|NEGATIVE) Record-level consistency is a separate property from aggregate predictive performance, and repeated-run evaluations should report the number and characteristics of discordant cases rather than relying solely on differences between aggregate estimates. -- [SCI-000137#discussion-implications-for-llm-workflow#FULLTEXT-324]

## [C77] verdict=PROVISIONAL bucket=provisional score=1.0 claims=2
### The pipeline deviates from PRISMA 2020 Item 11d which recommends at least two independent extractors, and the default search does not include CENTRAL or Embase which are standard requirements for Cochrane-compliant reviews.
Supporting studies: SCI-000142
Member claims:
- (RQ3|NEGATIVE) The pipeline deviates from PRISMA 2020 Item 11d which recommends at least two independent extractors, and the default search does not include CENTRAL or Embase which are standard requirements for Cochrane-compliant reviews. -- [SCI-000142#methods-data-extraction-and-risk-of-bias#FULLTEXT-369]
- (RQ3|NEGATIVE) meta-pipe offers four capabilities not available in any single existing tool: automated manuscript generation, semi-automated GRADE assessment, overclaim detection, and dual-paradigm network meta-analysis, at an estimated API cost of $15-30 per typical review. -- [SCI-000142#abstract-results#FULLTEXT-370]

## [C85] verdict=PROVISIONAL bucket=provisional score=1.0 claims=2
### Chain-of-thought prompting did not improve LGAR's ranking performance, suggesting graded relevance generation without step-by-step reasoning is sufficient for this task.
Supporting studies: SCI-000164
Member claims:
- (RQ3|NEGATIVE) Chain-of-thought prompting did not improve LGAR's ranking performance, suggesting graded relevance generation without step-by-step reasoning is sufficient for this task. -- [SCI-000164#5-4-main-results-and-findings#FULLTEXT-455]
- (RQ3|POSITIVE) LGAR outperforms the state-of-the-art QA-based ranking system (Akinseloyin et al., 2024) by 5–10 percentage points in mean average precision using recent open-weights models under the same criteria. -- [SCI-000164#1-introduction#FULLTEXT-456]

## [C86] verdict=PROVISIONAL bucket=provisional score=0.0 claims=1
### On the TAR2019 dataset, LGAR (T+R, monoT5) achieves MAP 50.6 versus 45.1 for the replicated QA-based baseline (Akinseloyin et al., ours), a ~5.5-point gain, with LGAR (T, monoT5) at 48.4.
Supporting studies: SCI-000164
Member claims:
- (RQ3|NEUTRAL) On the TAR2019 dataset, LGAR (T+R, monoT5) achieves MAP 50.6 versus 45.1 for the replicated QA-based baseline (Akinseloyin et al., ours), a ~5.5-point gain, with LGAR (T, monoT5) at 48.4. -- [SCI-000164#5-4-main-results-and-findings-table-2#FULLTEXT-459]

## [C87] verdict=PROVISIONAL bucket=provisional score=0.0 claims=3
### Feeding curated data via Azure AI Search to the LLM is described as the first step for avoiding hallucinations; the LLM is instructed to return citations linked to response, pointing to original documents — a decisive factor for raising trust.
Supporting studies: SCI-000172
Member claims:
- (RQ1|NEUTRAL) The proposed RAG architecture integrates Azure Blob Storage (crawling/storage), Azure AI Search (embedding/indexing), and Azure OpenAI (LLM generation) with custom Python automation tools, forming an end-to-end pipeline from data acquisition to aggregated responses. -- [SCI-000172#methodology-figure-5#FULLTEXT-463]
- (RQ2|NEUTRAL) Feeding curated data via Azure AI Search to the LLM is described as the first step for avoiding hallucinations; the LLM is instructed to return citations linked to response, pointing to original documents — a decisive factor for raising trust. -- [SCI-000172#methodology-avoiding-hallucinations#FULLTEXT-464]
- (RQ3|NEGATIVE) Limitation: All cloud services carry associated costs (Azure AI Search, Azure OpenAI, Blob Storage, Compute) that must be assessed before implementation; data privacy concerns require that research data remain logically isolated and not used for model training by the cloud provider. -- [SCI-000172#results-and-discussions-challenges#FULLTEXT-467]

## [C91] verdict=PROVISIONAL bucket=provisional score=0.0 claims=1
### AI-intensive stage latency is expected to scale proportionally with dataset size, so scalability may become a constraint in large-scale applications unless batching, parallel processing, or adaptive scheduling are introduced.
Supporting studies: SCI-000179
Member claims:
- (RQ3|NEUTRAL) AI-intensive stage latency is expected to scale proportionally with dataset size, so scalability may become a constraint in large-scale applications unless batching, parallel processing, or adaptive scheduling are introduced. -- [SCI-000179#results-and-discussion-limitations-and-f#FULLTEXT-480]

## [C93] verdict=PROVISIONAL bucket=provisional score=0.0 claims=2
### Experiment strategy evolution raised EvoScientist's mean code execution success rate across the four experiment stages from 34.39 before evolution to 44.56 after evolution.
Supporting studies: SCI-000186
Member claims:
- (RQ3|NEUTRAL) Experiment strategy evolution raised EvoScientist's mean code execution success rate across the four experiment stages from 34.39 before evolution to 44.56 after evolution. -- [SCI-000186#5-2-code-generation-performance#FULLTEXT-506]
- (RQ3|NEUTRAL) Under human expert evaluation, EvoScientist achieved a Novelty win rate of 82.50% and a Feasibility win rate of 64.17% averaged across four representative baselines (InternAgent, AI Scientist-v2, Novix, K-Dense). -- [SCI-000186#5-1-idea-generation-performance#FULLTEXT-510]

## [C94] verdict=PROVISIONAL bucket=provisional score=0.0 claims=1
### Named limitation: EvoScientist is only evaluated on computational research tasks; generalization to domains requiring physical experimentation (e.g., materials science and drug discovery) remains open and would need laboratory workflow integration.
Supporting studies: SCI-000186
Member claims:
- (RQ3|NEUTRAL) Named limitation: EvoScientist is only evaluated on computational research tasks; generalization to domains requiring physical experimentation (e.g., materials science and drug discovery) remains open and would need laboratory workflow integration. -- [SCI-000186#7-limitations-and-ethical-considerations#FULLTEXT-508]

## [C95] verdict=PROVISIONAL bucket=provisional score=0.0 claims=1
### The LLM-based automatic evaluation framework for idea generation was validated against human experts on 120 idea pairs, reaching 90.0% (108/120) overall agreement and 87.3% (524/600) average agreement across the four dimensions.
Supporting studies: SCI-000186
Member claims:
- (RQ3|NEUTRAL) The LLM-based automatic evaluation framework for idea generation was validated against human experts on 120 idea pairs, reaching 90.0% (108/120) overall agreement and 87.3% (524/600) average agreement across the four dimensions. -- [SCI-000186#appendix-c-3-agreement-between-llm-evalu#FULLTEXT-509]
