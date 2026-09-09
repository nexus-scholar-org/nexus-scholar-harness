# Consensus Cartographer Report

- **High-Consensus Clusters**: 16
- **Active Debates**: 7

## High-Consensus Findings

### C18 — LLAssist implements Chain-of-Thought as a two-step pipeline — key-semantics extraction followed by self-consistency-based filtering of the most consistent reasoning path.

- **Consensus score**: 0.75
- **Supporting studies (4)**: SCI-000096, SCI-000099, SCI-000128, SCI-000151
- **Stance distribution (per study)**: NEGATIVE: 3, NEUTRAL: 1, POSITIVE: 0

**Supporting claims:**

- `NEGATIVE` Reasoning transparency is built into the TitleAbstractReviewer agent, which provides either brief or chain-of-thought (CoT) reasoning for its inclusion/exclusion decisions — reasoning cannot be None. — [[SCI-000096#lattereview-title-and-abstract-reviews-r#FULLTEXT-053]]
- `NEGATIVE` M-Reason organizes evidence analysis into three agent roles - Orchestrator, BioExpert, and Evaluator - where the Orchestrator sequences the workflow and returns status without touching an LLM, giving a clear separation of responsibilities that the authors state facilitates reproducibility. — [[SCI-000099#3-1-evidence-analysis#FULLTEXT-062]]
- `NEGATIVE` The authors position M-Reason as improving predictability and reproducibility but note it operates more as a deterministic workflow than a fully autonomous agent, which restricts adaptive decision-making. — [[SCI-000099#limitations#FULLTEXT-064]]
- `NEGATIVE` All M-Reason agent prompts include explicit anti-hallucination instructions requiring agents to refrain from introducing any information not directly present in the supplied evidence, and a Content Validator additionally ensures no information outside the provided evidence is introduced. — [[SCI-000099#3-3-prompt-engineering-and-message-struc#FULLTEXT-066]]
- `NEGATIVE` An independent Search Agent decouples evidence acquisition from downstream mechanistic reasoning, so the reasoning and visualization agents operate over shared evidence objects rather than reconstructing information from free-form text. — [[SCI-000128#abstract#FULLTEXT-276]]
- `NEUTRAL` LLAssist implements Chain-of-Thought as a two-step pipeline — key-semantics extraction followed by self-consistency-based filtering of the most consistent reasoning path. — [[SCI-000151#3-technical-implementation#FULLTEXT-388]]

### C32 — No validation data are reported; this is a system description not a validation study, and formal validation reproducing published Cochrane reviews is described as essential before routine use.

- **Consensus score**: 0.67
- **Supporting studies (3)**: SCI-000102, SCI-000122, SCI-000142
- **Stance distribution (per study)**: NEGATIVE: 2, NEUTRAL: 1, POSITIVE: 0

**Supporting claims:**

- `NEGATIVE` Clinician assessment of 8 clinical cases found the system could generate conclusions consistent with tumor board recommendations with complete evidence reliability, though case-level evaluation was limited in scope. — [[SCI-000102#methods-clinician-s-assessment-for-case-#FULLTEXT-091]]
- `NEUTRAL` All intermediate outputs — rule sets, function plans, parsed field values, and trial-level filtering outcomes — are logged, providing a complete audit trail from the original clinical query to the final selected studies. — [[SCI-000122#2-1-trial-selection-and-structuring#FULLTEXT-218]]
- `NEGATIVE` No validation data are reported; this is a system description not a validation study, and formal validation reproducing published Cochrane reviews is described as essential before routine use. — [[SCI-000142#abstract-results-and-conclusion#FULLTEXT-368]]

### C51 — The evaluation cannot exclude data contamination because many benchmark SLRs were published years ago and their data may already have been exposed to LLMs during pre-training.

- **Consensus score**: 0.67
- **Supporting studies (3)**: SCI-000115, SCI-000137, SCI-000164
- **Stance distribution (per study)**: NEGATIVE: 2, NEUTRAL: 1, POSITIVE: 0

**Supporting claims:**

- `NEGATIVE` To limit evaluator bias, all LLM outputs in the KSR benchmark were anonymized and randomized before evaluation so that evaluators could not identify which system produced a given output. — [[SCI-000115#2-methods-2-2-1-human-in-the-loop-benchm#FULLTEXT-173]]
- `NEGATIVE` LLM outputs were saved before being linked to human decisions or full-text outcomes, and manual post-processing was restricted to identifier-based merging with no LLM screening decision changed on substantive grounds. — [[SCI-000137#methods-integrity-checks-and-safeguard-p#FULLTEXT-315]]
- `NEUTRAL` The authors report a trust risk: since LLMs can perpetuate and amplify training-data biases, LGAR may inadvertently reinforce these biases when ranking abstracts, potentially skewing SLR outcomes. — [[SCI-000164#6-limitations#FULLTEXT-452]]
- `NEGATIVE` The evaluation cannot exclude data contamination because many benchmark SLRs were published years ago and their data may already have been exposed to LLMs during pre-training. — [[SCI-000164#6-limitations#FULLTEXT-453]]

### C72 — On the Dementia-Sport dataset the Bi-LSTM baseline achieved 87% accuracy for identifying PICOS-compliant abstracts, illustrating the utility of automated screening for filtering clearly non-compliant studies early in the pipeline.

- **Consensus score**: 0.67
- **Supporting studies (3)**: SCI-000138, SCI-000140, SCI-000181
- **Stance distribution (per study)**: NEGATIVE: 0, NEUTRAL: 1, POSITIVE: 2

**Supporting claims:**

- `NEUTRAL` On the Dementia-Sport dataset the Bi-LSTM baseline achieved 87% accuracy for identifying PICOS-compliant abstracts, illustrating the utility of automated screening for filtering clearly non-compliant studies early in the pipeline. — [[SCI-000138#results#FULLTEXT-335]]
- `NEUTRAL` The transformer-based multi-task classifier achieved study design classification accuracy of 95.7%, while the Bi-LSTM baseline reached 87% accuracy for PICOS compliance detection, evidencing robust automated screening performance. — [[SCI-000138#abstract#FULLTEXT-336]]
- `POSITIVE` In the HCP self-evolving episode, Brain Researcher evaluated 116 candidate prediction-pipeline configurations for Cognition (104 returned scored results), and the researcher-frozen selected workflow achieved a higher pooled out-of-fold correlation than a matched reconstruction of the published procedure across 10 repeated same-cohort nested-cross-validation splits (median Δr = .098; conditional one-sided p = .006), higher in all 10 runs. — [[SCI-000140#results-self-evolving-research-episodes#FULLTEXT-349]]
- `POSITIVE` Benchmark testing against standardized datasets including BioASQ shows the integrated LLM+RAG approach achieves good accuracy on factoid, list and yes/no questions, representing an improvement over previous state-of-the-art approaches. — [[SCI-000181#evaluation#FULLTEXT-494]]

### C78 — Across 17,443 generated citations, no model exceeds a citation-level existence rate of 0.475, with Temporal and Combo conditions producing the steepest drops while outputs remain format-compliant.

- **Consensus score**: 0.67
- **Supporting studies (3)**: SCI-000144, SCI-000154, SCI-000159
- **Stance distribution (per study)**: NEGATIVE: 2, NEUTRAL: 1, POSITIVE: 0

**Supporting claims:**

- `NEGATIVE` Across 17,443 generated citations, no model exceeds a citation-level existence rate of 0.475, with Temporal and Combo conditions producing the steepest drops while outputs remain format-compliant. — [[SCI-000144#abstract#FULLTEXT-373]]
- `NEGATIVE` Manual validation of the pipeline on a stratified sample of 100 citations gave overall agreement of 75% and Cohen's kappa 0.63, with precision 0.97 for Existing, 0.88 for Fabricated but only 0.43 for Unresolved; the dominant error was Unresolved-to-Fabricated (16 cases). — [[SCI-000144#4-verification-pipeline-pipeline-validat#FULLTEXT-374]]
- `NEGATIVE` Under the Temporal condition every model produces well-formed bibliographic entries respecting the requested year window, yet GPT-4o's existence rate drops from 0.235 to 0.019, so format compliance masks a near-complete loss of verifiability ('compliance without substance'). — [[SCI-000144#6-discussion#FULLTEXT-379]]
- `NEGATIVE` In the audit, only 15 of 35 'Unresolved' citations were truly unresolved; 16 of 35 were fabricated and 4 of 35 were existing — so the category should not be read as 'nearly correct,' and reported fabricated rates are likely underestimates. — [[SCI-000144#5-results-sensitivity-to-reclassifying-u#FULLTEXT-381]]
- `NEUTRAL` The proprietary-open-weight gap in citation existence rate is large and statistically clear (delta = +0.229 at Baseline, up to +0.310 under Survey prompting), persistent across all conditions and across every domain group. — [[SCI-000144#5-results#FULLTEXT-383]]
- `NEUTRAL` In experiments, GPT-4o fabricated citations in 78-90% of cases when asked to cite recent literature across fields such as computer science and biomedicine, whereas OpenScholar achieved citation accuracy on par with human experts, addressing a key hallucination/verifiability risk. — [[SCI-000154#introduction#FULLTEXT-414]]
- `NEGATIVE` Limitation: OpenScholar does not consistently retrieve the most representative or relevant papers for certain queries; expert annotators noted citations were occasionally outdated or less relevant. — [[SCI-000159#limitations#FULLTEXT-446]]

### C46 — Single-task models were higher performing, with Guanaco7B-Single outperforming all other models by at least 0.07 accuracy while preserving the highest inclusion recall.

- **Consensus score**: 0.60
- **Supporting studies (5)**: SCI-000111, SCI-000115, SCI-000121, SCI-000127, SCI-000137
- **Stance distribution (per study)**: NEGATIVE: 3, NEUTRAL: 2, POSITIVE: 0

**Supporting claims:**

- `NEUTRAL` Open-source zero-shot models are unsuitable for screening after performing very poorly on the irrelevancy test (Guanaco7B achieving only 0.02), confirming fine-tuning is necessary. — [[SCI-000111#body#FULLTEXT-156]]
- `POSITIVE` Single-task models were higher performing, with Guanaco7B-Single outperforming all other models by at least 0.07 accuracy while preserving the highest inclusion recall. — [[SCI-000111#body#FULLTEXT-157]]
- `NEGATIVE` A contamination check on documents published after the model providers' training cutoffs showed no evidence that prior exposure inflated the reported extraction results. — [[SCI-000115#abstract#FULLTEXT-174]]
- `NEUTRAL` LLMs (GPT-3.5 Turbo, GPT-4 Turbo, GPT-4o, Llama 3 70B, Gemini 1.5 Pro, and Claude Sonnet 3.5) were trialed across 23 Cochrane Library systematic reviews to evaluate their accuracy in zero-shot binary classification for abstract screening. — [[SCI-000121#abstract#FULLTEXT-217]]
- `NEGATIVE` A universal vulnerability is documented: every tested model, when fed systematically negated (factually inverted) abstracts in the N-RAG workflow, synthesized the false claims into coherent but false conclusions scoring below even the parametric zero-shot baseline. — [[SCI-000127#4-results-vulnerability-to-misinformatio#FULLTEXT-266]]
- `NEGATIVE` No individual screening output recovered all 316 verified eligible records, and greater retention of benchmark records did not consistently correspond to greater recovery. — [[SCI-000137#results-rq1-recovery-of-verified-eligibl#FULLTEXT-323]]

### C22 — Named evaluation gap: despite 57 SLRs, LGAR was only reliably tested in the medical domain because other domains in the SYNERGY dataset have too few SLRs to assess performance equivalence.

- **Consensus score**: 0.50
- **Supporting studies (2)**: SCI-000096, SCI-000164
- **Stance distribution (per study)**: NEGATIVE: 1, NEUTRAL: 1, POSITIVE: 0

**Supporting claims:**

- `NEUTRAL` Evaluation on six SYNERGY datasets showed AUC values ranging from 0.77 to 0.95, with performance varying significantly across datasets due to task heterogeneity, dataset characteristics, and threshold sensitivity. — [[SCI-000096#section-4-1-evaluation-on-synergy-datase#FULLTEXT-058]]
- `NEUTRAL` Limitation: Performance variability across datasets is attributed to task heterogeneity, dataset size differences, varying inclusion rates (from <1% to 12.36%), and threshold sensitivity — the choice of decision threshold significantly impacts performance. — [[SCI-000096#lattereview-evaluation-performance-varia#FULLTEXT-060]]
- `NEGATIVE` Named evaluation gap: despite 57 SLRs, LGAR was only reliably tested in the medical domain because other domains in the SYNERGY dataset have too few SLRs to assess performance equivalence. — [[SCI-000164#6-limitations#FULLTEXT-457]]

### C30 — The system exhibited temporal instability with performance declining at -1.9% per day over the evaluation period, an architectural reliability gap.

- **Consensus score**: 0.50
- **Supporting studies (2)**: SCI-000100, SCI-000102
- **Stance distribution (per study)**: NEGATIVE: 1, NEUTRAL: 1, POSITIVE: 0

**Supporting claims:**

- `NEUTRAL` The system exhibited temporal instability with performance declining at -1.9% per day over the evaluation period, an architectural reliability gap. — [[SCI-000100#body#FULLTEXT-082]]
- `NEGATIVE` Error analysis reveals three failure types: low logical coherence from assembling fragmented pieces, misalignment with question intent, and inclusion of outdated conclusions, demonstrating that the system does not fully eliminate quality issues. — [[SCI-000102#wang-et-al-deeper-med-expert-evaluation-#FULLTEXT-092]]

### C33 — All experimental conditions used deterministic decoding (temperature 0) with no retrieval augmentation, and the design produced 2,880 runs yielding 17,443 individual citations.

- **Consensus score**: 0.50
- **Supporting studies (2)**: SCI-000106, SCI-000144
- **Stance distribution (per study)**: NEGATIVE: 1, NEUTRAL: 1, POSITIVE: 0

**Supporting claims:**

- `NEUTRAL` The technical example fixes parameters to maximise deterministic responses, setting temperature 0.0 and seed 42 within a DSPy-based AbstractScreening module, translating the declarative framework into a verifiable, reproducible digital artefact. — [[SCI-000106#susnjak-et-al-example-implementation#FULLTEXT-100]]
- `NEGATIVE` All experimental conditions used deterministic decoding (temperature 0) with no retrieval augmentation, and the design produced 2,880 runs yielding 17,443 individual citations. — [[SCI-000144#3-experimental-design#FULLTEXT-371]]

### C34 — The platform centers on human-machine collaboration in which the human researcher primarily orchestrates, directs, and reviews AI-supported processes and retains control at all times, rather than aiming for full automation.

- **Consensus score**: 0.50
- **Supporting studies (2)**: SCI-000107, SCI-000141
- **Stance distribution (per study)**: NEGATIVE: 1, NEUTRAL: 1, POSITIVE: 0

**Supporting claims:**

- `NEUTRAL` ADVISE embeds a fine-tuned BERT AI agent in the human title-and-abstract screening workflow with a screen-update-predict-sample active learning loop, where a priority score PS(p) = softmax(Pred(p))[1] ranks unscreened papers by predicted relevance probability and the human team screens prioritized papers in batches. — [[SCI-000107#methodology-active-learning-query-strate#FULLTEXT-102]]
- `NEUTRAL` ADVISE preserves human verification of all relevant papers by design: because 'for evidence synthesis, all relevant papers need to be verified by a human agent', the highest-priority papers are sampled first, and the workflow stops screening when ranking similarity or the real-time inclusion rate crosses a threshold. — [[SCI-000107#methodology-active-learning-query-strate#FULLTEXT-103]]
- `NEUTRAL` The practical interaction cost of the human-AI team is acknowledged as a concrete barrier: time needed to exchange information, label updates, dataset merging, and time lags between human labeling and model updates can mean one team operates with incomplete data. — [[SCI-000107#discussion-the-cost-of-communication#FULLTEXT-105]]
- `NEUTRAL` ADVISE identifies a trust risk in human-AI screening teams: the cold-start problem, where the AI agent must rank documents before knowing the domain, can lead to distrust if initial rankings are incorrect, and model output quality is bounded by the consistency of human-provided training labels. — [[SCI-000107#discussion-trust-in-ai#FULLTEXT-106]]
- `NEUTRAL` ADVISE was restricted to title-and-abstract screening because copyright and subscription issues make downloading and using full-text documents infeasible across institutions; full-text screening would require training another BERT model on a new human-generated training dataset. — [[SCI-000107#discussion-automation-of-full-text-scree#FULLTEXT-108]]
- `NEGATIVE` In the simulated case on a fully labeled 68,539-document dataset targeting an inclusion rate of 80%, the hybrid team achieves the highest efficiency with a training size of 5,000, where human agents need to screen only 25.2% of papers versus 80% without AI guidance, saving 54.8% of human screening effort. — [[SCI-000107#results-simulated-egm-design#FULLTEXT-109]]
- `NEGATIVE` Incorporating the BERT-based AI agent into the human team reduces human screening effort by 68.5% compared to no AI assistance, and the highest-priority (HP) active-learning sampling strategy reduces human effort further to 78.3% for identifying 80% of all relevant documents. — [[SCI-000107#abstract#FULLTEXT-110]]
- `POSITIVE` On the three deployed EGMs (Agriculture 221k, Nutrition 117k, Resilience 60k documents), the BERT agent needed 47%, 17%, and 75% less human effort, respectively, than the EPPI-Reviewer SVM baseline to reach an 80% inclusion rate, and BERT achieved higher classification accuracy than SVM for all three EGMs. — [[SCI-000107#results-saved-effort#FULLTEXT-111]]
- `NEGATIVE` Using records from twelve human screeners (averaging 38.6 papers per hour, SE=1.00) on an agriculture development EGM, the AL-enhanced AI agent saves 1,111.5 hours of title-and-abstract screening versus no AI agent and 229.1 hours versus the EPPI-Reviewer SVM. — [[SCI-000107#results-active-learning-training-size-an#FULLTEXT-112]]
- `POSITIVE` Using the least-confidence (LC) active-learning strategy produced better classification models (higher F1 score) than random sampling, because sampling the most uncertain papers lets the model learn more efficiently from human labeling. — [[SCI-000107#results-active-learning-training-size-an#FULLTEXT-113]]
- `NEGATIVE` The platform centers on human-machine collaboration in which the human researcher primarily orchestrates, directs, and reviews AI-supported processes and retains control at all times, rather than aiming for full automation. — [[SCI-000141#4-framework-for-ai-assisted-research-4-2#FULLTEXT-357]]

### C62 — BERTScore fails as a reliability proxy for conclusion quality: it gives nearly identical F1 scores across workflows and rates false N-RAG conclusions as semantically equivalent to correct G-RAG ones.

- **Consensus score**: 0.50
- **Supporting studies (2)**: SCI-000127, SCI-000181
- **Stance distribution (per study)**: NEGATIVE: 1, NEUTRAL: 1, POSITIVE: 0

**Supporting claims:**

- `NEUTRAL` The RAG paradigm's susceptibility to noisy or factually incorrect retrievals is flagged: models often uncritically synthesize such context, failing to cross-check against parametric knowledge or detect internal contradictions. — [[SCI-000127#2-1-retrieval-augmented-generation-and-m#FULLTEXT-267]]
- `NEGATIVE` The authors conclude that current models act as 'obedient synthesizers rather than critical reasoners', lacking the ability to detect and reject misinformation based on internal knowledge or logical inconsistency. — [[SCI-000127#4-results-vulnerability-to-misinformatio#FULLTEXT-268]]
- `NEGATIVE` BERTScore fails as a reliability proxy for conclusion quality: it gives nearly identical F1 scores across workflows and rates false N-RAG conclusions as semantically equivalent to correct G-RAG ones. — [[SCI-000127#6-insufficiency-of-bertscore-similarity-#FULLTEXT-269]]
- `NEUTRAL` Expert validation through blind testing with domain experts found the system provided answers rated as 'equally or more comprehensive' than manual search in most cases while requiring substantially less researcher time, and identified relevant papers missed by experts in many test cases. — [[SCI-000181#evaluation#FULLTEXT-495]]

### C69 — Re-execution of proprietary hosted LLM workflows cannot be guaranteed to reproduce original outputs because the underlying models and web interfaces are externally controlled and may change over time.

- **Consensus score**: 0.50
- **Supporting studies (2)**: SCI-000137, SCI-000141
- **Stance distribution (per study)**: NEGATIVE: 1, NEUTRAL: 1, POSITIVE: 0

**Supporting claims:**

- `NEGATIVE` A central implication is that the model name is an insufficient description of an LLM-based decision system; the implemented workflow also comprises input preparation, prompt instructions, uncertainty handling, processing configuration, interaction structure, output generation, integrity checks, and post-processing. — [[SCI-000137#discussion-implications-for-llm-workflow#FULLTEXT-319]]
- `NEGATIVE` Re-execution of proprietary hosted LLM workflows cannot be guaranteed to reproduce original outputs because the underlying models and web interfaces are externally controlled and may change over time. — [[SCI-000137#methods-software-and-computational-repro#FULLTEXT-321]]
- `NEUTRAL` An error-tolerant interface lets users see which data is provided as input when the LLM calls a tool, helping determine whether the tool was called as expected, and allows modification of all messages and generated data. — [[SCI-000141#4-framework-for-ai-assisted-research-4-2#FULLTEXT-352]]

### C79 — Cost evaluation: GPT-4o costs approximately $3.16 per 100 articles, GPT-3.5 about $0.22 per 100 articles, while locally-run Gemma 2 and Llama 3 have no cloud cost.

- **Consensus score**: 0.50
- **Supporting studies (2)**: SCI-000151, SCI-000154
- **Stance distribution (per study)**: NEGATIVE: 0, NEUTRAL: 1, POSITIVE: 1

**Supporting claims:**

- `NEUTRAL` LLAssist supports both local models provisioned via Ollama (Llama 3, Gemma 2) and cloud models (GPT-3.5, GPT-4), letting researchers trade off processing speed, accuracy, and data-privacy concerns. — [[SCI-000151#3-technical-implementation#FULLTEXT-389]]
- `NEGATIVE` Cost evaluation: GPT-4o costs approximately $3.16 per 100 articles, GPT-3.5 about $0.22 per 100 articles, while locally-run Gemma 2 and Llama 3 have no cloud cost. — [[SCI-000151#5-2-time-and-cost-efficiency#FULLTEXT-393]]
- `NEUTRAL` Throughput evaluation: LLAssist processes 17–37 articles in under 10 minutes, 115 in 20–50 minutes, and 2,576 in 10–11 hours; GPT-4o is slowest at 24–29 s/article, Llama 3 fastest at 10–11 s/article, Gemma 2 and GPT-3.5 at 12–14 s/article. — [[SCI-000151#5-2-time-and-cost-efficiency#FULLTEXT-399]]
- `POSITIVE` OpenScholar can enhance off-the-shelf LMs: when GPT-4o is used as the underlying model, OpenScholar-GPT-4o achieves a 12% improvement in correctness compared with GPT-4o alone, demonstrating a pipeline-level boost independent of model weights. — [[SCI-000154#evaluation#FULLTEXT-410]]

### C89 — Manual synthesis of 30 articles is estimated at 50+ hours; the same task was completed in 1 minute 24 seconds using the RAG architecture, demonstrating orders-of-magnitude time reduction.

- **Consensus score**: 0.50
- **Supporting studies (2)**: SCI-000172, SCI-000179
- **Stance distribution (per study)**: NEGATIVE: 1, NEUTRAL: 1, POSITIVE: 0

**Supporting claims:**

- `NEUTRAL` Manual synthesis of 30 articles is estimated at 50+ hours; the same task was completed in 1 minute 24 seconds using the RAG architecture, demonstrating orders-of-magnitude time reduction. — [[SCI-000172#results-and-discussions#FULLTEXT-468]]
- `NEGATIVE` In the observed execution, retrieval and preparation stages (S1-S4) processed 20 papers in 21.38 s total, while AI-assisted abstract analysis (S5) required 25.02 s per paper — reported as descriptive rather than comparative performance evidence. — [[SCI-000179#abstract#FULLTEXT-482]]

### C3 — On human clinical studies the domain had the highest accuracy of the three at 82%, attributed to it being the most homogenous domain with all abstracts reporting randomized clinical trials.

- **Consensus score**: 0.50
- **Supporting studies (6)**: SCI-000056, SCI-000088, SCI-000108, SCI-000115, SCI-000122, SCI-000128
- **Stance distribution (per study)**: NEGATIVE: 3, NEUTRAL: 2, POSITIVE: 1

**Supporting claims:**

- `NEGATIVE` Performance was lowest for the DRKS registry where negative predictive value was 63.4% compared to 82.8% for ClinicalTrials.gov, attributed to fewer registry-side publication links and publication in non-PubMed-indexed journals. — [[SCI-000056#discussion-limitations#FULLTEXT-006]]
- `NEGATIVE` Deeks' funnel plot asymmetry tests found no evidence of publication bias in either the title/abstract meta-analysis (bias coefficient -1.16, P=0.97) or the full-text meta-analysis (bias coefficient -17.74, P=0.17). — [[SCI-000088#results-meta-analysis#FULLTEXT-029]]
- `NEUTRAL` On human clinical studies the domain had the highest accuracy of the three at 82%, attributed to it being the most homogenous domain with all abstracts reporting randomized clinical trials. — [[SCI-000108#results#FULLTEXT-121]]
- `NEUTRAL` Performance declined most on interpretive tasks: forward-looking 'future directions' averaged only 2.9-3.5 out of 5.0, with NotebookLM scoring as low as 1.53 on policy briefs, suggesting models struggle with critical appraisal. — [[SCI-000115#3-results-3-1-model-performance-varies-s#FULLTEXT-179]]
- `NEGATIVE` FDA approval status — an inherently dynamic filtering criterion — is validated through an agentic retrieval module querying Drugs.com as a curated, versioned reference, rather than trusting model or registry knowledge. — [[SCI-000122#2-1-trial-selection-and-structuring#FULLTEXT-223]]
- `POSITIVE` BioInsight achieves best QA performance, the highest expert score on BioInsight-100, and stronger expert ratings for traceability, ranking quality, and dashboard usability in disease-level interpretation compared to search-augmented baselines. — [[SCI-000128#introduction-contributions#FULLTEXT-282]]

### C9 — Model selection for LGAR is constrained to open-weights LLMs explicitly to enhance the reproducibility of the results.

- **Consensus score**: 0.47
- **Supporting studies (17)**: SCI-000088, SCI-000089, SCI-000099, SCI-000106, SCI-000108, SCI-000117, SCI-000122, SCI-000124, SCI-000125, SCI-000126, SCI-000129, SCI-000137, SCI-000146, SCI-000151, SCI-000152, SCI-000156, SCI-000164
- **Stance distribution (per study)**: NEGATIVE: 8, NEUTRAL: 7, POSITIVE: 2

**Supporting claims:**

- `NEGATIVE` The majority of the included studies used off-the-shelf LLMs without task-specific fine-tuning and instead emphasized prompt engineering as the primary optimization strategy, meaning general-purpose LLMs achieved strong screening performance with minimal adaptation. — [[SCI-000088#results-methodological-characteristics-o#FULLTEXT-024]]
- `NEUTRAL` The review applies PROBAST + AI and QUADAS-2 to rate the methodological quality and risk of bias of the included LLM screening studies; most studies demonstrated low risk of bias, and agreement of screening decisions with human-defined reference standards was the evaluation backbone. — [[SCI-000088#methods-risk-of-bias-and-applicability-a#FULLTEXT-026]]
- `NEGATIVE` The review finds that LLMs are positioned as assistive, high-sensitivity tools that prioritize potentially relevant studies for human verification rather than replacements for human reviewers. — [[SCI-000088#discussion#FULLTEXT-027]]
- `NEUTRAL` In 18 included studies, LLMs in title-and-abstract screening achieved pooled sensitivity of 0.92 (95% CI 0.81-0.96, I²=95.82), pooled specificity of 0.94 (95% CI 0.90-0.97, I²=99.90), an SROC AUC of 0.98, and a diagnostic odds ratio of 185, with substantial cross-study heterogeneity. — [[SCI-000088#results-meta-analysis#FULLTEXT-031]]
- `POSITIVE` Reported efficiency gains for LLM-assisted screening workflows include screening and decision-making time commonly reduced by three-to-five-fold (in some cases by an order of magnitude) and deployment cost often below one tenth of the cost of manual screening. — [[SCI-000088#discussion#FULLTEXT-033]]
- `NEGATIVE` No task-specific training, fine-tuning, or few-shot examples were used, and the LLM is used only for summarizing articles not for making assessments or proposed action. — [[SCI-000089#methods-procedure#FULLTEXT-035]]
- `NEGATIVE` Data extraction accuracy was 100% in both LLM and manual conditions as assessed by an independent evaluator who was unaware of group allocation, with no adverse events or participant burden reported. — [[SCI-000089#results-secondary-outcomes#FULLTEXT-037]]
- `NEGATIVE` Formal output stability under repeated prompting was not assessed, though potential run-to-run variability did not affect trial exposure because all LLM summaries were generated before participant sessions and stored as fixed materials. — [[SCI-000089#discussion-limitations#FULLTEXT-038]]
- `NEGATIVE` LLM assistance reduced mean task completion time by 7.9 minutes (27.5 vs 34.5 minutes), representing approximately 23% reduction, but the 95% CI included zero (-1.5 to 17.3 minutes; P=0.099) and the study may have been underpowered. — [[SCI-000089#results-primary-outcomes#FULLTEXT-039]]
- `NEGATIVE` M-Reason integrates deterministic code for validation alongside LLM reasoning; the authors report that combining LLM-driven analysis with deterministic code offers greater confidence but at the expense of speed and flexibility. — [[SCI-000099#6-conclusions#FULLTEXT-068]]
- `NEUTRAL` The framework adapts recent advances in declarative prompt optimisation, developed for general-purpose LLM applications, and demonstrates their applicability to the domain of SLR automation, described as a novel application of such approaches to SLR pipelines. — [[SCI-000106#abstract#FULLTEXT-093]]
- `NEUTRAL` The paper argues that current LLM-assisted SLR approaches rely on brittle, manually crafted prompts that compromise reliability and reproducibility, and that this prompt fragility undermines scientific confidence in LLM-assisted evidence synthesis. — [[SCI-000106#abstract#FULLTEXT-095]]
- `NEUTRAL` The paper notes that LLM performance is highly sensitive to the phrasing of input prompts, making LLM-assisted workflows unreliable, difficult to reproduce, and raising concerns about their scientific validity. — [[SCI-000106#introduction#FULLTEXT-097]]
- `NEUTRAL` The paper reports that subtle variations in prompt formats can result in differences as large as 76 accuracy points on tasks from the Super-NaturalInstructions benchmark, quantifying prompt fragility and its impact on reliability. — [[SCI-000106#introduction#FULLTEXT-101]]
- `NEGATIVE` The study reports a case where the LLM hallucinated the study design, labeling an abstract as a 'Randomized controlled trial' when there was no mention of random allocation, evidencing a factual-extraction hallucination risk in SLR automation. — [[SCI-000108#results#FULLTEXT-119]]
- `NEGATIVE` Evaluation on LoQA uses DeepSeek-V3.2 as the LLM judge for Argument Sufficiency and Detail Preservation (temperature 0), and DeepResearch Bench uses Gemini-2.5-Pro for RACE and Gemini-2.5-Flash for FACT — evidence that the reported metrics are LLM-judged rather than human-scored. — [[SCI-000117#4-experiments-4-3-implementation-details#FULLTEXT-194]]
- `NEUTRAL` EligMeta separates LLM-based reasoning/orchestration from deterministic, version-controlled execution of numerically critical operations (trial selection, eligibility-weight computation, statistical estimation) to guarantee reproducibility and transparency. — [[SCI-000122#1-introduction#FULLTEXT-220]]
- `NEGATIVE` The hybrid architecture is argued to reduce hallucination risk while allowing LLM integration in high-stakes biomedical applications without sacrificing reliability. — [[SCI-000122#4-discussion#FULLTEXT-224]]
- `NEUTRAL` Performance was strongest for explicitly stated criteria, moderate for structural requirements, and weakest for inference-heavy tasks such as linearity and sensitivity analyses. — [[SCI-000124#body#FULLTEXT-240]]
- `NEGATIVE` Experimental results show that even the most advanced evaluated LLMs still generate hallucinated references despite recent progress. — [[SCI-000125#abstract#FULLTEXT-242]]
- `NEUTRAL` BIORESEARCHER is not uniformly dominant at every layer: CellType achieves a higher L2 pass rate (77.48% vs 68.47-74.77%) on qualitative-synthesis questions, and frontier LLMs plateau near a 68% L1 ceiling, showing specialized systems can match or exceed a broader orchestrator for narrow fact retrieval. — [[SCI-000126#evaluation#FULLTEXT-258]]
- `POSITIVE` Prompt design sensitivity was demonstrated: the screening prompt was refined 4 times and extraction prompt refined 6 times to improve precision and reduce ambiguity, showing LLM performance is highly sensitive to prompt wording. — [[SCI-000129#section-4-2-adjustments-during-conductio#FULLTEXT-289]]
- `NEGATIVE` LLM effectiveness is task-dependent: Gemini PRO achieved 90% in extraction and screening, Manus 98% in screening but only 40% in extraction, and Copilot 60% in both — model selection should be treated as a methodological decision. — [[SCI-000129#section-4-3-tests-with-other-models-sect#FULLTEXT-291]]
- `NEUTRAL` Time reduction was substantial: manual screening took ~23 days, LLM-assisted screening took ~9 hours (98% reduction); manual extraction took ~7 days, LLM-assisted took ~1 hour (99% reduction). — [[SCI-000129#section-4-1-comparison-of-time-and-accur#FULLTEXT-293]]
- `NEUTRAL` The analysis code, benchmark input data, LLM prompts, screening outputs, and comprehensive analytical results are archived in open supplementary materials, allowing reported comparisons to be reconstructed. — [[SCI-000137#methods-software-and-computational-repro#FULLTEXT-318]]
- `NEGATIVE` The study supports using LLMs as documented, auditable, and human-supervised components of evidence-synthesis workflows rather than as autonomous replacements for human screening judgement. — [[SCI-000137#conclusion#FULLTEXT-326]]
- `NEGATIVE` LLMs do not always perform well in mathematical reasoning tasks, which raises questions about whether their probability outputs for screening decisions are meaningful. — [[SCI-000146#abstract#FULLTEXT-384]]
- `NEGATIVE` Four LLMs were evaluated for their accuracy in title/abstract screening based on their probability outputs, motivated by the concern that LLM probability scores may not be meaningful. — [[SCI-000146#abstract#FULLTEXT-385]]
- `NEUTRAL` LLAssist requires its LLMs to output reasoning for every relevance/contribution judgment, which doubles as a cognitive forcing function acting as a checkpoint before downstream processing. — [[SCI-000151#4-1-4-reasoning-quality#FULLTEXT-391]]
- `NEUTRAL` The authors concede the accuracy assessment was conducted in an uncontrolled environment and position LLAssist as a lightweight filtering aid to be used alongside established methodologies such as PRISMA. — [[SCI-000151#2-2-5-preliminary-nature-of-evaluation#FULLTEXT-398]]
- `NEUTRAL` The authors conclude that while LLMs were not trustworthy as independent reviewers, they improved the human results by reducing the number of false negatives and false positives after rescreening was completed. — [[SCI-000152#discussion#FULLTEXT-401]]
- `POSITIVE` The LLM-assisted screening required almost half of the time and costs than the screening completed by two human raters, yet the two human raters outperformed the LLM-assisted rater in rescreening rate even in a worst-case scenario. — [[SCI-000152#conclusions#FULLTEXT-406]]
- `NEUTRAL` The two LLMs completed the same screening task almost 25 times faster than the human rater, and LLM-assisted screening took 21 hours versus 37 hours for two human raters, with the combined cost of two LLMs being 3.26 USD versus an estimated 492.18 USD for two human raters. — [[SCI-000152#discussion#FULLTEXT-409]]
- `NEGATIVE` User evaluation of the LLM-based UI used only four research articles as input, with no quantitative metrics or inter-rater reliability reported. — [[SCI-000156#body#FULLTEXT-430]]
- `POSITIVE` Model selection for LGAR is constrained to open-weights LLMs explicitly to enhance the reproducibility of the results. — [[SCI-000164#5-1-model-selection-and-experimental-set#FULLTEXT-451]]
- `NEGATIVE` Named risk of the approach: applying LGAR to define a cut-off in the ranked list could cause a relevant paper to be overlooked — the primary failure mode identified for LLM-based abstract screening. — [[SCI-000164#6-limitations#FULLTEXT-458]]

## Active Debates

### C13 — Structured field extraction achieved 35.1% higher semantic similarity than PDF chunking, statistically significant at p < 0.000001, across 643 observations from 60 testing sessions.

- **Consensus score**: 0.25
- **Supporting studies (4)**: SCI-000090, SCI-000100, SCI-000110, SCI-000128
- **Stance distribution (per study)**: NEGATIVE: 1, NEUTRAL: 2, POSITIVE: 1

**Supporting claims:**

- `NEGATIVE` Schema-constrained extraction uses fixed prompts and structured enumerations rather than free generation, with conservative missingness handling (returning 'NR') to minimize fabrication and ensure deterministic outputs. — [[SCI-000090#discussion-limitations#FULLTEXT-042]]
- `POSITIVE` Structured field extraction achieved 35.1% higher semantic similarity than PDF chunking, statistically significant at p < 0.000001, across 643 observations from 60 testing sessions. — [[SCI-000100#abstract#FULLTEXT-080]]
- `NEUTRAL` The LangGraph module minimized hallucination by mapping retrieved texts back to the original user queries, drastically reducing irrelevant or fabricated outputs common in standalone LLM-generated answers. — [[SCI-000110#3-3-document-relevance-and-hallucination#FULLTEXT-141]]
- `NEUTRAL` The reasoning-note schema requires the Reasoning Agent to state what the pathway does, why it matters for the disease, which input proteins drive the interpretation, which interaction modules support the mechanism, and where evidence is weak or indirect. — [[SCI-000128#appendix-a-2-intermediate-artifacts-and-#FULLTEXT-278]]

### C90 — The AI-assisted abstract review (including abstract verification, bilingual Thai/English summarization, and structured output parsing) took 25.02 s per paper, inclusive of a 2-second intentional delay for API rate regulation.

- **Consensus score**: 0.33
- **Supporting studies (3)**: SCI-000172, SCI-000179, SCI-000186
- **Stance distribution (per study)**: NEGATIVE: 1, NEUTRAL: 1, POSITIVE: 1

**Supporting claims:**

- `NEGATIVE` Validation results ranged from 76% (Romanian, Exp #1) to 94% (AI-generated English, Exp #4), with Romanian consistently performing worse than English (~90-95% gap); cross-document synthesis questions yielded slightly lower results. — [[SCI-000172#table-6-study-results-results-and-discus#FULLTEXT-469]]
- `NEUTRAL` The AI-assisted abstract review (including abstract verification, bilingual Thai/English summarization, and structured output parsing) took 25.02 s per paper, inclusive of a 2-second intentional delay for API rate regulation. — [[SCI-000179#results-and-discussion-ai-assisted-abstr#FULLTEXT-484]]
- `POSITIVE` In an end-to-end evaluation, all six EvoScientist-authored manuscripts submitted to ICAIS 2025 were accepted against a track-wide acceptance rate of 31.71% (26 of 82 submissions), with one Best Paper and one AI Reviewer's Appraisal Award. — [[SCI-000186#5-3-end-to-end-scientific-discovery-perf#FULLTEXT-507]]

### C10 — To support repeatability, the study fixed conservative generation parameters for GPT-4 - temperature=0, frequency_penalty=0, presence_penalty=0, top_p=0.95 - aiming for maximum repeatability across repeated requests.

- **Consensus score**: 0.40
- **Supporting studies (5)**: SCI-000088, SCI-000108, SCI-000110, SCI-000120, SCI-000127
- **Stance distribution (per study)**: NEGATIVE: 1, NEUTRAL: 2, POSITIVE: 2

**Supporting claims:**

- `NEGATIVE` Comparing GPT-4T and GPT-4o (4 and 5 studies respectively), pooled sensitivity was numerically higher for GPT-4o (0.88 vs 0.81, not significant, p=0.45) while GPT-4T's pooled specificity (0.99) was significantly higher than GPT-4o's (0.94, p < 0.01), and no model-level covariate effect was significant in the joint model. — [[SCI-000088#results-subgroup-analysis-and-meta-regre#FULLTEXT-028]]
- `NEGATIVE` For full-text screening (4 studies), the pooled sensitivity and specificity both reached 0.99 (95% CI 0.95-1.00) with an SROC AUC of 0.99, no heterogeneity in sensitivity (I²=0) but considerable heterogeneity in specificity (I²=92.65). — [[SCI-000088#results-meta-analysis#FULLTEXT-030]]
- `NEUTRAL` Prompt strategies incorporating examples or chain-of-thought reasoning significantly improved sensitivity: pooled sensitivity was 0.95 (95% CI 0.92-0.99) in the example/chain-of-thought group versus 0.86 (95% CI 0.78-0.94) in the group without them (p < 0.01). — [[SCI-000088#results-subgroup-analysis-and-meta-regre#FULLTEXT-032]]
- `NEUTRAL` To support repeatability, the study fixed conservative generation parameters for GPT-4 - temperature=0, frequency_penalty=0, presence_penalty=0, top_p=0.95 - aiming for maximum repeatability across repeated requests. — [[SCI-000108#methods#FULLTEXT-115]]
- `NEUTRAL` In the RAG-vs-GPT-4 comparison breakdown, RAG-based GPT-3.5 excelled on 25% of queries (especially relationship-centric Neo4j queries), GPT-4's broader capacity won on 20%, and 25% of responses still required further optimization due to multi-layer synthesis complexity. — [[SCI-000110#3-1-performance-of-rag-vs-gpt-4#FULLTEXT-145]]
- `POSITIVE` For high-expertise depth-of-adaptation-response classification, GPT-4o achieved accuracy of 22.7% and micro-averaged F1 of 0.22 (macro F1 0.17), with agreement with human annotators collapsing as task complexity increases (precision/recall/F1: low 0.88/0.90/0.89, medium 0.40/0.83/0.54, high 0.22/0.22/0.22). — [[SCI-000120#4-results-high-expertise-tasks#FULLTEXT-212]]
- `POSITIVE` Information-grounding hypothesis (H2) was confirmed: G-RAG conclusions were rated significantly superior to P-CoT across all comparisons (p < 0.04; Cohen's d = 0.48–0.74), with the general-purpose Gemma model rated over a full point higher by humans (Mean Diff = 1.025). — [[SCI-000127#5-2-the-role-of-information-grounding-h2#FULLTEXT-272]]

### C60 — Identifying post-exposure controls proved particularly challenging, with LLM precision (0.15–0.30) far below the best human reviewer (0.89).

- **Consensus score**: 0.50
- **Supporting studies (2)**: SCI-000124, SCI-000129
- **Stance distribution (per study)**: NEGATIVE: 1, NEUTRAL: 0, POSITIVE: 1

**Supporting claims:**

- `POSITIVE` Identifying post-exposure controls proved particularly challenging, with LLM precision (0.15–0.30) far below the best human reviewer (0.89). — [[SCI-000124#body#FULLTEXT-236]]
- `NEGATIVE` LLM achieved approximately 95% accuracy in screening (208/219 correct) but 11 hallucination cases were identified where the model answered with information from other works; extraction accuracy was 92.3% (12/13 correct) with 1 error. — [[SCI-000129#section-4-1-comparison-of-time-and-accur#FULLTEXT-288]]

### C14 — On the ketamine/neuroimaging benchmark, the pipeline achieved 100% recall, 97.9% precision, 99.4% accuracy, and 98.9% F1 — the best performance across all three benchmarks.

- **Consensus score**: 0.50
- **Supporting studies (4)**: SCI-000090, SCI-000115, SCI-000126, SCI-000140
- **Stance distribution (per study)**: NEGATIVE: 1, NEUTRAL: 1, POSITIVE: 2

**Supporting claims:**

- `POSITIVE` On the ketamine/neuroimaging benchmark, the pipeline achieved 100% recall, 97.9% precision, 99.4% accuracy, and 98.9% F1 — the best performance across all three benchmarks. — [[SCI-000090#table-2-pooled-performance-summary#FULLTEXT-045]]
- `NEGATIVE` In screening, Claude Sonnet 4 achieved the highest accuracy (82.8%) while GPT-5 achieved the highest recall (91.8%) but with specificity collapsing in policy briefs (53.3%); no system led on all tasks. — [[SCI-000115#3-results-3-1-model-performance-varies-s#FULLTEXT-178]]
- `POSITIVE` BIORESEARCHER obtains the best overall single-step pass rate (83.49%) and average judge score (0.892) on the 109-question suite, surpassing the specialized CellType agent (67.80%, 0.731) and the strongest frontier baseline GPT-5.5 (45.09%, 0.591). — [[SCI-000126#evaluation#FULLTEXT-259]]
- `NEUTRAL` On open-ended analysis benchmarks, BIORESEARCHER reaches 89.33% accuracy on BixBench and a mean score of 0.758 +/- 0.005 on BaisBench Scientific Discovery, matching Claude Code (0.759 +/- 0.012) and exceeding CellType (0.641 +/- 0.082). — [[SCI-000126#evaluation#FULLTEXT-260]]
- `NEGATIVE` On the 30-query clinical end-to-end benchmark, BIORESEARCHER achieves the highest positive hit rate (74.7% +/- 3.3%) and the highest negative clear rate (96.8% +/- 0.2%), exceeding CellType, Medea and OpenAI Deep Research on both axes. — [[SCI-000126#evaluation#FULLTEXT-261]]
- `NEUTRAL` In the NeuroMark collaborator case, Brain Researcher expanded a single pre-specified pipeline into a 480-specification multiverse covering connectivity, confound, dimensionality-reduction, classifier, and domain-granularity choices, recorded and reviewed all resulting runs, and automated review missed a sign-blind scoring error that a human reviewer caught by inspecting code and outputs. — [[SCI-000140#results-brain-researcher-runs-multiverse#FULLTEXT-342]]
- `POSITIVE` Across 60 tool-calling tasks and seven frontier models, Brain Researcher improved first-action correct route/tool selection from 23.3% to 93.6% (with-BR 95% CI 88.8-97.1), mean Capability@1 from 49.8% to 94.5%, and handoff sufficiency from 47.4% to 76.1%, with all seven models showing positive paired differences (exact two-sided Wilcoxon signed-rank p = 0.016 for each metric). — [[SCI-000140#results-brain-researcher-improves-tool-c#FULLTEXT-348]]

### C16 — Applied to the full 1,893-document corpus, the routed KSR workflow surfaced cross-source asymmetries and blind spots (worker well-being, small firms, and the Global South) that single-source synthesis would have missed.

- **Consensus score**: 0.50
- **Supporting studies (4)**: SCI-000090, SCI-000115, SCI-000127, SCI-000154
- **Stance distribution (per study)**: NEGATIVE: 2, NEUTRAL: 1, POSITIVE: 1

**Supporting claims:**

- `NEGATIVE` The central trade-off is reduced mechanistic resolution relative to full-text synthesis; abstract-only processing entails partial information loss but yields major gains in feasibility, governance, and scalability beyond human limits. — [[SCI-000090#discussion#FULLTEXT-050]]
- `NEUTRAL` Applied to the full 1,893-document corpus, the routed KSR workflow surfaced cross-source asymmetries and blind spots (worker well-being, small firms, and the Global South) that single-source synthesis would have missed. — [[SCI-000115#abstract#FULLTEXT-176]]
- `POSITIVE` The benchmark defines six distinct synthesis workflows varying input type (parametric vs. retrieved), reasoning strategy (zero-shot vs. CoT), and retrieval fidelity (oracle, noisy, negated) to enable fine-grained evaluation of synthesis behavior. — [[SCI-000127#3-1-figure-2-caption#FULLTEXT-265]]
- `NEGATIVE` The self-feedback inference loop, reranking and retrieval are core components that evaluation demonstrates as important to OpenScholar's performance, indicating that the orchestrated pipeline itself, not just the base LM, drives literature synthesis quality. — [[SCI-000154#evaluation#FULLTEXT-413]]

### C66 — Topic modeling using BERTopic identified thematic structure, redundancy, and evidence gaps, revealing substantial thematic redundancy and underexplored research areas in the corpora.

- **Consensus score**: 0.50
- **Supporting studies (4)**: SCI-000128, SCI-000138, SCI-000179, SCI-000181
- **Stance distribution (per study)**: NEGATIVE: 2, NEUTRAL: 1, POSITIVE: 1

**Supporting claims:**

- `NEGATIVE` When no protein-protein interaction edges are found the system avoids cluster-level interpretation and instead treats proteins individually; if an enriched pathway has weak literature support its narrative interpretation is marked as literature-weak or exploratory. — [[SCI-000128#appendix-a-4-quality-control-and-failure#FULLTEXT-281]]
- `NEGATIVE` Retrieval can miss relevant studies, select papers that are topically related but mechanistically weak, or suffer from protein synonym ambiguity, incomplete database coverage, and noisy input protein associations. — [[SCI-000128#limitations#FULLTEXT-284]]
- `NEUTRAL` Topic modeling using BERTopic identified thematic structure, redundancy, and evidence gaps, revealing substantial thematic redundancy and underexplored research areas in the corpora. — [[SCI-000138#abstract#FULLTEXT-337]]
- `NEGATIVE` When abstracts were unavailable, the AI module explicitly documented the limitation and generated context-aware summaries from available bibliographic information rather than silently fabricating content. — [[SCI-000179#results-and-discussion-ai-assisted-abstr#FULLTEXT-479]]
- `POSITIVE` Domain-specific optimizations such as biomedical entity recognition, relationship extraction and specialized embeddings further enhance performance across diverse research scenarios. — [[SCI-000181#abstract#FULLTEXT-486]]
