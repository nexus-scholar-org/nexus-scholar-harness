# RQ2 claim briefing (n=132)

- [SCI-000056/fulltext] (POSITIVE) Human error accounted for a larger proportion of discrepancies (61.5%) than TrialScout error across all 200 reviewed cases, suggesting the tool may be more accurate than manual search in practice.
  QUOTE: Overall, across all 200 cases with discrepancies, human error accounted for a larger proportion (123/200, 61.5%, 95% CI, 54.4–68.3%) than TrialScout error.
  TOK: [SCI-000056#results-validation-of-trialscout-against#FULLTEXT-003] | SEC: Results > Validation of TrialScout Against Human Assessment
- [SCI-000056/fulltext] (POSITIVE) Manual review of 200 discrepant cases showed that 79% of initially classified false positives were in fact true positives missed by the original manual search, and 44% of false negatives were true negatives, suggesting TrialScout's true performance is higher than metrics suggest.
  QUOTE: Of 100 false positive cases, 79 (79.0%, 95% CI, 69.7–86.5%) were in fact true positives missed by the original manual search. Of 100 false negative cases, 44 (44.0%, 95% CI, 34.1–54.3%) were found to be true negatives up
  TOK: [SCI-000056#results-validation-of-trialscout-against#FULLTEXT-004] | SEC: Results > Validation of TrialScout Against Human Assessment
- [SCI-000056/fulltext] (NEGATIVE) TrialScout's classifications are not deterministic; repeating a run can produce different results and this variability was not quantified, representing a reproducibility limitation.
  QUOTE: TrialScout has further limitations. Its classifications are not deterministic. Repeating a run can produce different results, and we did not quantify this variability.
  TOK: [SCI-000056#discussion-limitations#FULLTEXT-005] | SEC: Discussion > Limitations
- [SCI-000082/fulltext] (POSITIVE) Each hypothesis was independently evaluated against a randomized baseline of 1,000 XGBoost models trained on random gene sets, guarding against spurious gene-set signal.
  QUOTE: Each hypothesis was independently evaluated against a randomized baseline consisting of 1,000 XGBoost models trained on random gene sets containing up to 100 genes.
  TOK: [SCI-000082#body#FULLTEXT-018] | SEC: body
- [SCI-000082/fulltext] (POSITIVE) Integration with public biological knowledge graphs grounds analyses in established biological knowledge, reducing the risk of hallucinations and implausible results.
  QUOTE: A key feature is EcoXAI's integration with public biological knowledge graphs, which grounds analyses in established biological knowledge within the graph, reducing the risk of hallucinations and implausible results
  TOK: [SCI-000082#body#FULLTEXT-019] | SEC: body
- [SCI-000082/fulltext] (POSITIVE) To mitigate susceptibility to planning errors and cascading failures, EcoXAI enforces strict isolation across pipeline stages and persists intermediate code and experimental logic for human inspection and reproduction.
  QUOTE: Like other autonomous AI systems, EcoXAI is susceptible to planning errors and cascading failures. To mitigate this, the framework enforces strict isolation across its pipeline stages, persisting intermediate code execut
  TOK: [SCI-000082#body#FULLTEXT-020] | SEC: body
- [SCI-000088/fulltext] (NEUTRAL) The review applies PROBAST + AI and QUADAS-2 to rate the methodological quality and risk of bias of the included LLM screening studies; most studies demonstrated low risk of bias, and agreement of screening decisions with human-defined reference standards was the evaluation backbone.
  QUOTE: To evaluate the methodological quality and risk of bias of the included models and studies, we applied the Prediction Model Risk of Bias Assessment Tool + AI tool (PROBAST + AI) and the Quality Assessment of Diagnostic A
  TOK: [SCI-000088#methods-risk-of-bias-and-applicability-a#FULLTEXT-026] | SEC: Methods > Risk of Bias and Applicability Assessment
- [SCI-000088/fulltext] (NEUTRAL) The review finds that LLMs are positioned as assistive, high-sensitivity tools that prioritize potentially relevant studies for human verification rather than replacements for human reviewers.
  QUOTE: LLMs are not intended to replace human reviewers. Instead, they function as assistive tools within the screening framework to streamline systematic review processes
  TOK: [SCI-000088#discussion#FULLTEXT-027] | SEC: Discussion
- [SCI-000089/fulltext] (POSITIVE) Data extraction accuracy was 100% in both LLM and manual conditions as assessed by an independent evaluator who was unaware of group allocation, with no adverse events or participant burden reported.
  QUOTE: Based on expert review of the intended meaning of each extracted item, accuracy was 100% in both conditions (LLM 9/9; no LLM 11/11). Comparative modeling was not estimable because there was no between-group variability. 
  TOK: [SCI-000089#results-secondary-outcomes#FULLTEXT-037] | SEC: Results > Secondary Outcomes
- [SCI-000090/fulltext] (supportive) On the ketamine/neuroimaging benchmark, the pipeline achieved 100% recall, 97.9% precision, 99.4% accuracy, and 98.9% F1 — the best performance across all three benchmarks.
  QUOTE: Recall/Precision/Accuracy/F1 (%) 100.0/97.9/99.4/98.9
  TOK: [SCI-000090#table-2-pooled-performance-summary#FULLTEXT-045] | SEC: Table 2 (Pooled performance summary)
- [SCI-000090/fulltext] (supportive) Performance tracked the density and explicitness of source text: when constructs were explicitly encoded in abstracts, maximal sensitivity was achieved; when outcomes were inconsistently reported, screening was rate-limited by missing or underspecified inputs.
  QUOTE: performance tracked the density and explicitness of the source text: when the construct of interest was explicitly encoded in abstracts (ketamine-neuroimaging), the pipeline achieved maximal sensitivity with high precisi
  TOK: [SCI-000090#discussion#FULLTEXT-046] | SEC: Discussion
- [SCI-000090/fulltext] (supportive) Schema enforcement and conservative missingness handling were specifically designed to minimize hallucination risk, and performed well in audited fields — residual hallucination risk remains but is addressed through structural constraints.
  QUOTE: Residual hallucination risk also remains [25,26], although schema enforcement (constrained enumerations rather than free generation) and conservative missingness handling (returning 'NR') were designed to minimize fabric
  TOK: [SCI-000090#discussion-limitations#FULLTEXT-047] | SEC: Discussion (Limitations)
- [SCI-000096/fulltext] (supportive) The TitleAbstractReviewer uses a 5-point Likert scale for article assessment (1 = absolutely exclude, 5 = absolutely include), with hierarchical decision-making: when junior reviewers disagree, a senior reviewer's assessment becomes definitive.
  QUOTE: The TitleAbstractReviewer agents in our workflow employ a 5-point Likert scale for article assessment ... when the junior reviewers' scores differ or both assign a score of 3, the senior reviewer's assessment is sought a
  TOK: [SCI-000096#section-4-evaluation#FULLTEXT-055] | SEC: Section 4 (Evaluation)
- [SCI-000096/fulltext] (supportive) The framework encourages human oversight, recommending researchers break reviews into stages with manual review checkpoints rather than pursuing fully automated end-to-end processes.
  QUOTE: it's crucial to design your LatteReview workflows with human oversight in mind. Rather than aiming for a fully automated end-to-end process, consider breaking your review into stages punctuated by manual review.
  TOK: [SCI-000096#section-5-8-integrate-human-oversight#FULLTEXT-056] | SEC: Section 5.8 (Integrate Human Oversight)
- [SCI-000099/fulltext] (NEUTRAL) A Critical Reviewer agent performs adversarial analysis focusing on bias detection and identification of unsupported claims, running in parallel with a Content Validator and a Relevance Validator under a three-reviewer unanimous-consensus approval rule.
  QUOTE: CriticalReviewer: Provides adversarial analysis, focusing on bias detection, identification of unsupported claims, and suggesting alternative interpretations. This agent plays a key role in challenging assumptions and en
  TOK: [SCI-000099#3-2-1-overview-and-workflow#FULLTEXT-065] | SEC: 3.2.1 Overview and Workflow
- [SCI-000099/fulltext] (NEUTRAL) All M-Reason agent prompts include explicit anti-hallucination instructions requiring agents to refrain from introducing any information not directly present in the supplied evidence, and a Content Validator additionally ensures no information outside the provided evidence is introduced.
  QUOTE: All agent prompts include explicit anti-hallucination instructions, requiring agents to refrain from introducing any information not directly present in the supplied evidence.
  TOK: [SCI-000099#3-3-prompt-engineering-and-message-struc#FULLTEXT-066] | SEC: 3.3 Prompt Engineering and Message Structures
- [SCI-000099/fulltext] (POSITIVE) All synthesized outputs are fully traceable to their source evidence with explicit citations (including direct links when available), which the authors state lets users independently verify findings and directly addresses concerns about LLM hallucinations.
  QUOTE: All synthesized outputs are fully traceable to their source evidence, with explicit ci- tations (including direct links when available). This enhances transparency, user trust, and allows users to independently verify fi
  TOK: [SCI-000099#3-4-design-principles-and-rationale#FULLTEXT-067] | SEC: 3.4 Design Principles and Rationale
- [SCI-000099/fulltext] (NEUTRAL) M-Reason integrates deterministic code for validation alongside LLM reasoning; the authors report that combining LLM-driven analysis with deterministic code offers greater confidence but at the expense of speed and flexibility.
  QUOTE: Similarly, combining LLM-driven analysis with deterministic code offers greater confidence, but at the expense of speed and flexibility—a tradeoff that remains central in system design.
  TOK: [SCI-000099#6-conclusions#FULLTEXT-068] | SEC: 6 Conclusions
- [SCI-000100/fulltext] (POSITIVE) A multi-agent validation loop uses a generator LLM to draft cited answers and a secondary QA agent LLM to audit factual accuracy, logical consistency, and adherence to citation protocols.
  QUOTE: It implements a multi-agent system where a primary “generator” LLM drafts a cited answer, and a secondary “QA agent” LLM audits that output for factual accuracy, logical consistency, and adherence to citation protocols.
  TOK: [SCI-000100#body#FULLTEXT-076] | SEC: body
- [SCI-000100/fulltext] (POSITIVE) HySemRAG performs post-hoc citation verification in combination with an agentic self-correction framework with iterative quality assurance, ensuring complete traceability.
  QUOTE: The system addresses limitations in existing RAG architectures through a multi-layered approach: hybrid retrieval combining semantic search, keyword filtering, and knowledge graph traversal; an agentic self-correction fr
  TOK: [SCI-000100#abstract#FULLTEXT-077] | SEC: abstract
- [SCI-000100/fulltext] (POSITIVE) The system enforces single-source observations and rejects mixed-source citations to prevent hallucination in generated responses.
  QUOTE: The system enforces single-source observations and rejects mixed-source citations to prevent hallucination.
  TOK: [SCI-000100#body#FULLTEXT-078] | SEC: body
- [SCI-000102/fulltext] (POSITIVE) Blinded expert evaluation masks system identities and assigns responses for review to the author who contributed the corresponding questions, designed to support fair, domain-informed, and unbiased assessment of evidence quality.
  QUOTE: a Streamlit-based assessment workflow that masks system identities and assigns responses for review to the author who contributed the corresponding questions. This blinded annotation strategy is designed to support fair,
  TOK: [SCI-000102#methods-answer-generation#FULLTEXT-086] | SEC: Methods > Answer generation
- [SCI-000102/fulltext] (POSITIVE) Domain experts and LLM judgment jointly validate correctness and evidence grounding of each reference answer; if either assessment identifies deficiencies the answer is returned for revision until consensus is reached.
  QUOTE: domain experts assess factual accuracy, logical coherence, and evidence alignment, while GPT-5.2-pro provides sentence-level judgements of consistency and evidentiary support using predefined criteria. If both expert rev
  TOK: [SCI-000102#methods-reference-answer-curation#FULLTEXT-087] | SEC: Methods > Reference answer curation
- [SCI-000102/fulltext] (POSITIVE) Hallucinated or unverifiable references are detected during expert evaluation and the corresponding response is excluded and replaced with an alternative exhibiting high accuracy and reliable citation.
  QUOTE: In cases where hallucinated or unverifiable references are detected, the corresponding response is excluded and replaced with an alternative response exhibiting high accuracy and reliable citation.
  TOK: [SCI-000102#methods-answer-evaluation#FULLTEXT-088] | SEC: Methods > Answer evaluation
- [SCI-000102/fulltext] (POSITIVE) The Gemini-3-pro LLM response component is activated only when no high-quality evidence is available, and its generated content is retained only if subsequently supported by evidence retrieved from source databases.
  QUOTE: The LLM response component (Gemini-3-pro in our implementation) is activated only when no high-quality evidence is available. Its generated content is retained only if it is subsequently supported by evidence retrieved f
  TOK: [SCI-000102#methods-director-layer-processing-strate#FULLTEXT-089] | SEC: Methods > Director layer processing strategy
- [SCI-000106/fulltext] (POSITIVE) The technical example fixes parameters to maximise deterministic responses, setting temperature 0.0 and seed 42 within a DSPy-based AbstractScreening module, translating the declarative framework into a verifiable, reproducible digital artefact.
  QUOTE: The conceptual blueprint described in Box 1 can be implemented using programmatic LLM tools like DSPy. The following Python code provides a minimal functional example of how an AbstractScreening module would be structure
  TOK: [SCI-000106#susnjak-et-al-example-implementation#FULLTEXT-100] | SEC: Susnjak et al. > Example implementation
- [SCI-000107/fulltext] (NEGATIVE) ADVISE identifies a trust risk in human-AI screening teams: the cold-start problem, where the AI agent must rank documents before knowing the domain, can lead to distrust if initial rankings are incorrect, and model output quality is bounded by the consistency of human-provided training labels.
  QUOTE: This challenge, while common, can lead to distrust in AI from the human team, if they find the initial rankings to be incorrect. Additionally, the training data for our models are labels from people, which can be noisy. 
  TOK: [SCI-000107#discussion-trust-in-ai#FULLTEXT-106] | SEC: Discussion > Trust in AI
- [SCI-000108/fulltext] (NEGATIVE) Causal inference methods and study design were the data extraction items with the most errors, identifying the items most vulnerable to incorrect extraction and raising reliability concerns for downstream synthesis.
  QUOTE: Causal inference methods and study design were the data extraction items with the most errors.
  TOK: [SCI-000108#abstract#FULLTEXT-116] | SEC: ABSTRACT
- [SCI-000108/fulltext] (NEUTRAL) In the PICO prediction study participants and intervention/control showed high accuracy (greater than 80%), while outcomes were more challenging to extract, evidencing variable reliability across data items.
  QUOTE: The results shown in Figure 4 show a similar trend to the human clinical studies in figure 2. The quality of automatic participant and intervention/control entity extraction was high, with over 80% rated as 'Complete'. A
  TOK: [SCI-000108#results#FULLTEXT-117] | SEC: RESULTS
- [SCI-000108/fulltext] (NEGATIVE) The language model found it particularly difficult to name the type of study being reported; in the extraction results study design was rated complete only 47% of the time with 27% incorrect, identifying it as the most error-prone data extraction item.
  QUOTE: The language model found it particularly difficult to name the type of study being reported, though there was considerable variation on performance across the three domains of study in response to this question.
  TOK: [SCI-000108#results#FULLTEXT-118] | SEC: RESULTS
- [SCI-000108/fulltext] (NEGATIVE) The study reports a case where the LLM hallucinated the study design, labeling an abstract as a 'Randomized controlled trial' when there was no mention of random allocation, evidencing a factual-extraction hallucination risk in SLR automation.
  QUOTE: instance, the LLM "hallucinated" the study design, indicating that the abstract described a "Randomized controlled trial", when there was no mention of random allocation.
  TOK: [SCI-000108#results#FULLTEXT-119] | SEC: RESULTS
- [SCI-000109/fulltext] (POSITIVE) Extracted values include indices that link back to their locations in the source content, enabling easy checking and correction by sourcing the origin.
  QUOTE: Hence, it is convenient to check and correct mistakes made in the extraction by sourcing the origin.
  TOK: [SCI-000109#body#FULLTEXT-128] | SEC: body
- [SCI-000109/fulltext] (POSITIVE) TrialMind generates and executes Python code for result standardization, keeping the calculation process transparent and enhancing the reliability and reproducibility of synthesized evidence.
  QUOTE: Additionally, it ensures that the calculation process remains transparent, enhancing the reliability and reproducibility of the synthesized evidence.
  TOK: [SCI-000109#body#FULLTEXT-129] | SEC: body
- [SCI-000109/fulltext] (POSITIVE) TrialMind's source code for study search, study screening, data extraction, and result extraction is publicly released on GitHub, supporting reproducibility.
  QUOTE: TrialMind can be accessed at https://github.com/RyanWangZf/ TrialMind-SLR, including the source code for implementing Trial- Mind's study search, study screening, data extraction, and result extraction components
  TOK: [SCI-000109#body#FULLTEXT-130] | SEC: body
- [SCI-000110/fulltext] (NEUTRAL) A Bi-LSTM model trained on an extended PubMed-PICO dataset identifies whether an abstract conforms to PICOS standards, and LLM-based hierarchical classification of study designs is stored in PostgreSQL for later query-based filtering — a methodological-quality screen before inclusion.
  QUOTE: PICO Compliance: A Bi-LSTM model, trained on an extended PubMed-PICO dataset [10], identifies whether a given abstract conforms to PICOS standards.
  TOK: [SCI-000110#2-3-automated-pico-compliance-detection-#FULLTEXT-139] | SEC: 2.3 Automated PICO Compliance Detection and Study Design Classification
- [SCI-000110/fulltext] (NEGATIVE) Named trust limitation: verifying the trustworthiness of newly incorporated studies in the live database demands structured pipelines or human oversight — a gap the authors explicitly acknowledge.
  QUOTE: Verification Overheads: While continuous updates ensure currency, verifying the trustworthiness of new studies demands structured pipelines or human oversight.
  TOK: [SCI-000110#5-limitations-and-future-directions#FULLTEXT-140] | SEC: 5 Limitations and Future Directions
- [SCI-000110/fulltext] (POSITIVE) The LangGraph module minimized hallucination by mapping retrieved texts back to the original user queries, drastically reducing irrelevant or fabricated outputs common in standalone LLM-generated answers.
  QUOTE: The LangGraph module proved successful at minimizing off-target references. By mapping retrieved texts back to original user queries, the system drastically reduced irrelevant or fabricated outputs commonly seen in stand
  TOK: [SCI-000110#3-3-document-relevance-and-hallucination#FULLTEXT-141] | SEC: 3.3 Document Relevance and Hallucination Prevention
- [SCI-000111/fulltext] (NEGATIVE) ChatGPT performance varies greatly across review topics, drawing into question its generality and requiring assessment of model blind spots prior to real-world endorsement.
  QUOTE: Our models perform consistently across review topics whereas ChatGPT performance varies greatly. For ”Genetic Disorders” ChatGPT results are significantly below other models; for ”Heart & Circulation” and ”Infectious Dis
  TOK: [SCI-000111#body#FULLTEXT-152] | SEC: body
- [SCI-000111/fulltext] (NEGATIVE) Multi-task training harms include/exclude classification performance, with hallucinations hypothesized because exclusion reasoning and PICO information often relied on information from full-text screening not present in abstracts.
  QUOTE: We generally find that for multi-task models, cross-task transfer between PIO, Exclusion reasoning and Include/Exclude classification harms performance. We speculate two reasons for this 1) Dataset Imbalance: PIO data wa
  TOK: [SCI-000111#body#FULLTEXT-153] | SEC: body
- [SCI-000111/fulltext] (NEGATIVE) The overall quality of model-generated exclusion reasons remains poor, with ChatGPT generating subpar or incorrect reasons for 83% of samples.
  QUOTE: Overall, the quality of exclusion reasons remains poor: ChatGPT generated subpar or incorrect reasons for 83% of samples.
  TOK: [SCI-000111#body#FULLTEXT-154] | SEC: body
- [SCI-000114/fulltext] (NEGATIVE) A documented hallucination episode shows the raw LLM citing a paper absent from the corpus, and — when asked for additional relevant papers within the corpus — returning fabricated titles found neither in the database nor via Google Scholar.
  QUOTE: when asking for additional relevant papers on the topic of grounded theory (implying that they come from the VITALITY 2 corpus), the LLM responded with some paper titles that were nei- ther contained in the VITALITY 2 da
  TOK: [SCI-000114#6-discussion-limitations-future-work#FULLTEXT-163] | SEC: 6 Discussion, Limitations, & Future Work
- [SCI-000114/fulltext] (POSITIVE) The RAG architecture is positioned as a hallucination-mitigation mechanism: retrieving only relevant information from the local corpus reduces prompt size and minimizes the risk of hallucination.
  QUOTE: RAG. RAG semantically processes the user's input query to only retrieve relevant information from within the data corpus, thereby reducing the subsequent prompt size and also minimizing the risk of hallucination.
  TOK: [SCI-000114#4-vitality-2#FULLTEXT-164] | SEC: 4 VITALITY 2
- [SCI-000114/fulltext] (POSITIVE) To mitigate erroneous outputs stemming from training-data biases, the authors propose adding a user-facing prompt in vitaLITy 2 that explicitly warns users about the limitations of generated content.
  QUOTE: To mitigate this problem, we suggest adding a user prompt in VITALITY 2 to explicitly warn users about the lim- itations of content generated by VITALITY 2, thereby reminding and cautioning users to use this tool with ca
  TOK: [SCI-000114#6-discussion-limitations-future-work#FULLTEXT-165] | SEC: 6 Discussion, Limitations, & Future Work
- [SCI-000115/fulltext] (POSITIVE) A contamination check on documents published after the model providers' training cutoffs showed no evidence that prior exposure inflated the reported extraction results.
  QUOTE: A contamination check on post-cutoff documents showed no evidence that prior exposure inflated results.
  TOK: [SCI-000115#abstract#FULLTEXT-174] | SEC: Abstract
- [SCI-000115/fulltext] (POSITIVE) Post-cutoff (unseen) extraction accuracy showed no decline for any system (GPT-5 86.7%, Claude 88.9%, Gemini 85.2%), all exceeding the full-corpus values of 80.0%, 80.3%, and 74.5%, respectively.
  QUOTE: Post-cutoff accuracy showed no decline for any system. Total post-cutoff accuracy was 86.7 percent for GPT-5, 88.9 percent for Claude, and 85.2 percent for Gemini, against full-corpus values of 80.0, 80.3, and 74.5 perce
  TOK: [SCI-000115#3-results-3-1-1-robustness-to-training-d#FULLTEXT-175] | SEC: 3 Results > 3.1.1 Robustness to training data contamination
- [SCI-000117/fulltext] (NEUTRAL) DeepWeaver evaluates citation grounding via three metrics (Citation Count, Relevant Count, Relevant Ratio) that measure whether a system actively uses evidence and avoids citing or integrating irrelevant evidence.
  QUOTE: We compute three citation metrics: (1) Citation Count (CC): |C|, (2) Relevant Count (RC): |C ∩ER|, and (3) Relevant Ratio (RR): |C ∩ER|/|C|. These metrics measure whether the system actively uses evidence and properly av
  TOK: [SCI-000117#2-2-2-the-loqa-benchmark#FULLTEXT-188] | SEC: 2 > 2.2 The LoQA Benchmark
- [SCI-000117/fulltext] (POSITIVE) On LoQA, DeepWeaver improves citation grounding and evidence synthesis quality relative to the retrieval-augmented generation baseline, surpassing E-RAG by 15.5% in Argument Sufficiency, +14.7 in Relevant Citations, 14.5% in Relevant Citation Ratio, and 16.6% in Detail Preservation on Qwen3-30B-A3B-Instruct-2507.
  QUOTE: With Qwen3-30B-A3B-Instruct-2507, DeepWeaver surpasses E-RAG by 15.5% in Argument Sufficiency, +14.7 Relevant Citations, 14.5% in Relevant Citation Ratio, and 16.6% in Detail Preservation.
  TOK: [SCI-000117#4-experiments-4-4-main-results#FULLTEXT-189] | SEC: 4 Experiments > 4.4 Main Results
- [SCI-000117/fulltext] (POSITIVE) On the web-based DeepResearch Bench, DeepWeaver substantially improves effective citation and citation accuracy over the WebWeaver baseline on the FACT split, organizing web evidence into reliable support for answer claims.
  QUOTE: Notably, our method also substantially improves effective citation and citation accuracy over WebWeaver on FACT, indicating that it organizes web evidence into reliable support for answer claims.
  TOK: [SCI-000117#4-experiments-4-7-extension-to-web-based#FULLTEXT-190] | SEC: 4 Experiments > 4.7 Extension to Web-Based Deep Research
- [SCI-000118/fulltext] (NEGATIVE) Screening benchmark results demonstrate that model ranking is domain-dependent and not transferable across review topics.
  QUOTE: A two-dataset screening benchmark demonstrates that model ranking is domain-dependent and not transferable across review topics.
  TOK: [SCI-000118#abstract#FULLTEXT-200] | SEC: abstract
- [SCI-000118/fulltext] (POSITIVE) Title-abstarct screening employs a dual-screener mechanism with two independent models scoring on a five-point scale and an arbiter applying a lean-toward-inclusion policy for disagreements.
  QUOTE: Phase 3.1 (Title–Abstract Screening) employs a dual-screener mechanism: two independent models (Gemini 3.1 Pro and GPT-4.1 Mini) each assign a five-point relevance score using identical static-plus-dynamic prompts, and C
  TOK: [SCI-000118#body#FULLTEXT-201] | SEC: body
- [SCI-000120/fulltext] (NEGATIVE) On the high-expertise depth-of-adaptation-response task, GPT-4o exhibited a systematically more optimistic view than human annotators, often overestimating the impact of adaptation responses, and in 10.4% of cases produced per-response instead of aggregate assessments requiring evaluation isolation.
  QUOTE: the model, in some cases (10.4% of the time), provides indi- vidual assessments for each adaptation response rather than an aggregate assessment of the impact of a set of responses. This behavior complicated the evaluati
  TOK: [SCI-000120#4-results-high-expertise-tasks#FULLTEXT-210] | SEC: 4 Results > High Expertise Tasks
- [SCI-000120/fulltext] (NEUTRAL) The authors motivate the work by the need for a reliable model that ensures factual accuracy during the evidence-extraction phase for decision-making, and they position the assessment of model factuality as contingent on a system that keeps humans in the loop, concluding that a human-in-the-loop system is extremely beneficial for ensuring the integrity and effectiveness of the process.
  QUOTE: However, it is important to emphasize that these models cannot completely replace the expert-driven process, rather a human-in-the loop system would be extremely beneficial for ensuring the integrity and effectiveness of
  TOK: [SCI-000120#6-conclusion#FULLTEXT-211] | SEC: 6 Conclusion
- [SCI-000122/fulltext] (NEUTRAL) FDA approval status — an inherently dynamic filtering criterion — is validated through an agentic retrieval module querying Drugs.com as a curated, versioned reference, rather than trusting model or registry knowledge.
  QUOTE: FDA approval status, a common filtering criterion, is inherently dynamic and requires validation against reliable external sources. We address this through an agentic retrieval module (Supplementary Section A.3) that que
  TOK: [SCI-000122#2-1-trial-selection-and-structuring#FULLTEXT-223] | SEC: 2.1 Trial Selection and Structuring
- [SCI-000122/fulltext] (POSITIVE) The hybrid architecture is argued to reduce hallucination risk while allowing LLM integration in high-stakes biomedical applications without sacrificing reliability.
  QUOTE: This design reduces hallucination risk while maintaining flexibility in handling complex clinical queries, enabling integration of language models into high-stakes biomedical applications without sacrificing reliability.
  TOK: [SCI-000122#4-discussion#FULLTEXT-224] | SEC: 4 Discussion
- [SCI-000123/abstract_only] (POSITIVE) AutoConfidenceScore is an advanced automated framework for predicting preprint publication, aimed at improving quality assessment of preprint articles for evidence inclusion in systematic reviews.
  QUOTE: We developed AutoConfidenceScore (automated confidence score assessment), an advanced framework for predicting preprint publication, which reduces reli
  TOK: [SCI-000123#abstract#FULLTEXT-231] | SEC: ABSTRACT
- [SCI-000124/fulltext] (NEGATIVE) Errors commonly resulted from superficial linguistic cues, with models frequently misinterpreting keywords like longitudinal or sensitivity as automatic evidence of rigorous methodological approaches.
  QUOTE: Errors commonly resulted from superficial linguistic cues—for instance, models frequently misinterpreted keywords like “longitudinal” or “sensitivity” as automatic evidence of rigorous methodological approaches—leading t
  TOK: [SCI-000124#abstract#FULLTEXT-234] | SEC: abstract
- [SCI-000124/fulltext] (POSITIVE) Gold-standard labels rest on expert consensus, with each article independently evaluated by two reviewers who engaged in written, evidence-based reconciliation on disagreement.
  QUOTE: Whenever reviewers disagreed on the answer, they engaged in a structured reconciliation process: each reviewer provided written, evidence-based justifications, followed by detailed discussions to determine whether disagr
  TOK: [SCI-000124#body#FULLTEXT-235] | SEC: body
- [SCI-000124/fulltext] (NEGATIVE) Identifying post-exposure controls proved particularly challenging, with LLM precision (0.15–0.30) far below the best human reviewer (0.89).
  QUOTE: Identifying whether the model included post- exposure controls proved particularly challenging: despite high accuracy (>0.86), F1 scores were low (<0.37) due to poor precision (LLMs: 0.15–0.30 vs. the best human reviewer
  TOK: [SCI-000124#body#FULLTEXT-236] | SEC: body
- [SCI-000125/fulltext] (NEUTRAL) All LLMs demonstrated a significant increase in reference precision when generating references within the Review Composition task compared to the standalone Reference Generation task.
  QUOTE: compared to the Reference Generation task, all LLMs demonstrate a significant increase in precision when generating references within the Review Composition task.
  TOK: [SCI-000125#4-experiments-4-2-main-results#FULLTEXT-241] | SEC: 4 Experiments > 4.2 Main Results
- [SCI-000125/fulltext] (NEGATIVE) Experimental results show that even the most advanced evaluated LLMs still generate hallucinated references despite recent progress.
  QUOTE: The experimental results reveal that even the most advanced models still generate hallucinated references, despite recent progress.
  TOK: [SCI-000125#abstract#FULLTEXT-242] | SEC: Abstract
- [SCI-000125/fulltext] (NEGATIVE) Generating complete and accurate author lists remains a major challenge for LLMs; applying a first-author-only matching criterion raised precision by only 1-3% across all models.
  QUOTE: Applying this criterion results in a 1-3% increase in precision scores across all models. This suggests that generating complete and accurate author lists remains a major challenge for LLMs.
  TOK: [SCI-000125#4-experiments-4-2-main-results#FULLTEXT-243] | SEC: 4 Experiments > 4.2 Main Results
- [SCI-000125/fulltext] (POSITIVE) Grounding generated text with real external citations reduces hallucination: when LLMs generate references alongside the review text, reference accuracy improves markedly, suggesting a mutual constraint between references and review text that enhances reliability.
  QUOTE: our experiments reveal that when LLMs generate references alongside the literature review, the accuracy of these references improves markedly. This suggests a mutual constraint between the generated references and the re
  TOK: [SCI-000125#4-experiments-4-2-main-results#FULLTEXT-244] | SEC: 4 Experiments > 4.2 Main Results
- [SCI-000125/fulltext] (NEUTRAL) In reference generation, Claude-3.5-Sonnet achieved the highest title search rate (St 64.82) and precision (51.59), while Llama-3.2-3B performed worst across all three metrics.
  QUOTE: In Table 1, Claude-3.5-Sonnet achieves the highest precision, overlap rate, and St, while Llama-3.2-3B performs the worst on three metrics.
  TOK: [SCI-000125#4-experiments-4-2-main-results#FULLTEXT-245] | SEC: 4 Experiments > 4.2 Main Results
- [SCI-000125/fulltext] (POSITIVE) The automatic hallucination-assessment method was validated against human judgments: kappa agreement of 0.71 and 86% accuracy with human assessment as the gold standard, using three annotators and majority vote on 100 generated references.
  QUOTE: The results demonstrated a kappa agreement of 0.71 between the automatic and human assessments, signifying a relatively high level of consistency and supporting the reliability of our method. Furthermore, when using huma
  TOK: [SCI-000125#4-experiments-4-5-human-evaluation#FULLTEXT-246] | SEC: 4 Experiments > 4.5 Human Evaluation
- [SCI-000125/fulltext] (NEUTRAL) The framework's hallucination metric defines precision such that a higher precision indicates a lower hallucination rate, and also computes the overlap rate with human-cited references and a title search rate per LLM.
  QUOTE: In this section, we introduce the calculation process of the reference precision Precision, reference overlap rate with human-cited references Overlap rate, and title search rate St for each LLM. A higher precision metri
  TOK: [SCI-000125#3-methodology-3-3-evaluation-metrics#FULLTEXT-247] | SEC: 3 Methodology > 3.3 Evaluation Metrics
- [SCI-000127/fulltext] (NEGATIVE) A universal vulnerability is documented: every tested model, when fed systematically negated (factually inverted) abstracts in the N-RAG workflow, synthesized the false claims into coherent but false conclusions scoring below even the parametric zero-shot baseline.
  QUOTE: Despite being provided with factually inverted and contradictory information, every model proceeded to synthesize these incorrect claims into a coherent but false conclusion. The resulting scores are significantly lower 
  TOK: [SCI-000127#4-results-vulnerability-to-misinformatio#FULLTEXT-266] | SEC: 4 Results > Vulnerability to Misinformation
- [SCI-000127/fulltext] (NEGATIVE) The RAG paradigm's susceptibility to noisy or factually incorrect retrievals is flagged: models often uncritically synthesize such context, failing to cross-check against parametric knowledge or detect internal contradictions.
  QUOTE: A further limitation of the RAG paradigm is its susceptibility to noisy or factually incorrect retrievals Zhang & Gao (2024); Fang et al. (2024). Current models often uncritically synthesize such context, failing to cros
  TOK: [SCI-000127#2-1-retrieval-augmented-generation-and-m#FULLTEXT-267] | SEC: 2.1 Retrieval-Augmented Generation and Medical Applications
- [SCI-000127/fulltext] (NEGATIVE) The authors conclude that current models act as 'obedient synthesizers rather than critical reasoners', lacking the ability to detect and reject misinformation based on internal knowledge or logical inconsistency.
  QUOTE: This finding empirically confirms the vulnerability of RAG systems to faulty evidence and demonstrates that current models act as obedient synthesizers rather than critical reasoners, lacking the capability to identify a
  TOK: [SCI-000127#4-results-vulnerability-to-misinformatio#FULLTEXT-268] | SEC: 4 Results > Vulnerability to Misinformation
- [SCI-000128/fulltext] (POSITIVE) BioInsight preserves citation links, protein-level statistics, intermediate artifacts, uncertainty notes, and failure-handling behaviors, allowing users to inspect how each claim is supported, though these mechanisms are intended to support expert review rather than replace it.
  QUOTE: To mitigate these risks, BioInsight preserves citation links, protein-level statistics, intermediate artifacts, uncertainty notes, and failure-handling behaviors, allowing users to inspect how each claim is supported. Ho
  TOK: [SCI-000128#limitations#FULLTEXT-279] | SEC: Limitations
- [SCI-000128/fulltext] (POSITIVE) If the Reasoning Agent returns malformed JSON the raw response is preserved as an inspectable artifact and can be retried or excluded from final report assembly; if a coherence revision damages tables both pre-revision and post-revision drafts are stored.
  QUOTE: If the Reasoning Agent returns malformed JSON, the raw response is preserved as an inspectable artifact and can be retried or excluded from final report assembly. If a coherence revision damages tables, links, or image s
  TOK: [SCI-000128#appendix-a-4-quality-control-and-failure#FULLTEXT-280] | SEC: Appendix A.4 > Quality Control and Failure Handling
- [SCI-000128/fulltext] (POSITIVE) When no protein-protein interaction edges are found the system avoids cluster-level interpretation and instead treats proteins individually; if an enriched pathway has weak literature support its narrative interpretation is marked as literature-weak or exploratory.
  QUOTE: If no protein-protein interaction edges are found, the system avoids cluster-level interpretation and instead treats proteins individually. If a pathway is statistically enriched but has little or no PubMed support, it c
  TOK: [SCI-000128#appendix-a-4-quality-control-and-failure#FULLTEXT-281] | SEC: Appendix A.4 > Quality Control and Failure Handling
- [SCI-000129/fulltext] (supportive) Hybrid workflows are essential: LLMs should be embedded in workflows combining partial automation with targeted human supervision — complete delegation risks loss of methodological rigor.
  QUOTE: LLMs should be integrated cautiously and deliberately, as complementary tools within human-centered workflows. Their value lies in supporting efficiency in operational stages, while preserving direct engagement with the 
  TOK: [SCI-000129#section-5-discussion#FULLTEXT-287] | SEC: Section 5 (Discussion)
- [SCI-000129/fulltext] (supportive) LLM achieved approximately 95% accuracy in screening (208/219 correct) but 11 hallucination cases were identified where the model answered with information from other works; extraction accuracy was 92.3% (12/13 correct) with 1 error.
  QUOTE: the LLM achieved approximately 95.0% accuracy (208 correct out of 219 studies), with 11 hallucination cases in which it began answering the questionnaire with information from other works. In the data extraction stage, t
  TOK: [SCI-000129#section-4-1-comparison-of-time-and-accur#FULLTEXT-288] | SEC: Section 4.1 (Comparison of Time and Accuracy)
- [SCI-000129/fulltext] (supportive) Prompt design sensitivity was demonstrated: the screening prompt was refined 4 times and extraction prompt refined 6 times to improve precision and reduce ambiguity, showing LLM performance is highly sensitive to prompt wording.
  QUOTE: the screening prompt was refined four times and the extraction prompt six times to improve precision and reduce ambiguity, demonstrating the sensitivity of LLM performance to prompt wording.
  TOK: [SCI-000129#section-4-2-adjustments-during-conductio#FULLTEXT-289] | SEC: Section 4.2 (Adjustments During Conduction) / Lesson 2
- [SCI-000131/fulltext] (NEGATIVE) Aris cannot guarantee that any output is correct, novel, or scientifically sound; cross-model review reduces some failure modes without eliminating them, and citation grounding via DBLP and CrossRef reduces but does not eliminate bibliography fabrication.
  QUOTE: Aris cannot guarantee that any output is correct, novel, or scientifically sound. LLM outputs can include factual hallucinations and methodological gaps; cross-model review reduces some failure modes without eliminating 
  TOK: [SCI-000131#discussion-limitations-and-responsible-u#FULLTEXT-297] | SEC: Discussion > Limitations and Responsible Use
- [SCI-000131/fulltext] (POSITIVE) Aris defaults to pairing executor and reviewer from different model families because single-model self-refinement loops share inductive biases, whereas heterogeneous multi-agent debate has been reported to elicit more diverse critiques.
  QUOTE: Single-model self-refinement loops (Madaan et al., 2023; Shinn et al., 2024) have generator and validator that share inductive biases; heterogeneous multi-agent debate has been reported to elicit more diverse critiques t
  TOK: [SCI-000131#methods-design-principles#FULLTEXT-298] | SEC: Methods > Design Principles
- [SCI-000131/fulltext] (POSITIVE) The experiment-audit stage detects five integrity failure modes: model-derived reference labels, self-normalized scores, phantom results, dead-code or unused-metric inflation, and scope inflation.
  QUOTE: A cross-model reviewer audits the evaluation code and outputs against the following integrity failure modes: (1) model-derived reference labels—reference targets are synthesized from model outputs rather than obtained fr
  TOK: [SCI-000131#methods-stage-1-experiment-integrity-aud#FULLTEXT-299] | SEC: Methods > Stage 1: Experiment-integrity audit
- [SCI-000131/fulltext] (NEGATIVE) The review loop can amplify reviewer biases: if the reviewer consistently demands a particular methodology, the loop may overfit to the reviewer model's preferences rather than improve broader scientific quality.
  QUOTE: The review loop can amplify reviewer biases: if the reviewer consistently demands a particular methodology, the loop may overfit to the reviewer model's preferences rather than improve broader scientific quality. Over-it
  TOK: [SCI-000131#discussion-limitations-and-responsible-u#FULLTEXT-300] | SEC: Discussion > Limitations and Responsible Use
- [SCI-000135/fulltext] (POSITIVE) AutoSynthesis performs study-level risk-of-bias assessment following ROBINS-I, covering bias from confounding through selection of the reported result.
  QUOTE: Study-level risk-of-bias assessment following ROINS-I [32], where the assessment is varies from low to high concern.
  TOK: [SCI-000135#body#FULLTEXT-307] | SEC: body
- [SCI-000135/fulltext] (POSITIVE) AutoSynthesis produces PRISMA 2020 flow diagrams, forest plots, and funnel plots to assess small-study effects and potential publication bias.
  QUOTE: As a result, AUTOSYNTHESIS produces the following output: b, PRISMA 2020 [2] flow diagram summarizing the screening process and the final study inclusion. c, The forest plot shows the study-level effects (in terms of Hed
  TOK: [SCI-000135#body#FULLTEXT-308] | SEC: body
- [SCI-000135/fulltext] (POSITIVE) Automated heterogeneity diagnostics and publication bias tests were broadly comparable to the human benchmark, finding substantial between-study heterogeneity and small-study effects.
  QUOTE: both the between-study heterogeneity analysis and the publication bias diagnostics were also broadly comparable between the automated and human syntheses: both found substantial between-study heterogeneity (I2 = 88.3% vs
  TOK: [SCI-000135#body#FULLTEXT-309] | SEC: body
- [SCI-000137/fulltext] (NEGATIVE) A central implication is that the model name is an insufficient description of an LLM-based decision system; the implemented workflow also comprises input preparation, prompt instructions, uncertainty handling, processing configuration, interaction structure, output generation, integrity checks, and post-processing.
  QUOTE: A central implication is that the model name is an insufficient description of an LLM-based decision system. The implemented workflow also comprises input preparation, prompt instructions, uncertainty handling, processin
  TOK: [SCI-000137#discussion-implications-for-llm-workflow#FULLTEXT-319] | SEC: Discussion > Implications for LLM workflow evaluation
- [SCI-000137/fulltext] (NEGATIVE) Full-text eligibility was assessed by a single reviewer rather than multiple independent assessors, and the review lead had previously completed the single-reviewer title-and-abstract screen, so the verified eligible set is an operational reference standard rather than an independent consensus gold standard.
  QUOTE: Full-text eligibility was assessed by the review lead rather than by multiple independent assessors. Although workflow-specific title-and-abstract decisions were not displayed during full-text assessment, the review lead
  TOK: [SCI-000137#discussion-strengths-and-limitations#FULLTEXT-320] | SEC: Discussion > Strengths and limitations
- [SCI-000137/fulltext] (NEGATIVE) Re-execution of proprietary hosted LLM workflows cannot be guaranteed to reproduce original outputs because the underlying models and web interfaces are externally controlled and may change over time.
  QUOTE: Re-execution of the proprietary hosted LLM workflows cannot be guaranteed to reproduce the original outputs because the underlying models and web interfaces are externally controlled and may change over time.
  TOK: [SCI-000137#methods-software-and-computational-repro#FULLTEXT-321] | SEC: Methods > Software and computational reproducibility
- [SCI-000137/fulltext] (NEGATIVE) Two nominally identical GPT-5.4 file-batch runs agreed on 91.7% of records but disagreed on 94 individual records including 29 verified eligible records retained by only one run, showing that aggregate similarity concealed meaningful item-level instability.
  QUOTE: The two GPT-5.4 file-batch runs conducted under nominally identical conditions produced closely similar aggregate performance but differed at the record level. Across the 1,131 benchmark records, the runs agreed on 1,037
  TOK: [SCI-000137#results-rq4-run-to-run-consistency#FULLTEXT-322] | SEC: Results > RQ4: Run-to-run consistency
- [SCI-000138/fulltext] (POSITIVE) All 26 false positives produced by the Cochrane classifier corresponded to maybe judgments in both expert annotations and Kernel's ternary output, where Kernel preserved calibrated uncertainty by highlighting textual cues of randomization without confirming them.
  QUOTE: Detailed error analysis showed that all 26 false positives produced by the Cochrane classifier corresponded to maybe judgments in both expert annotations and Kernel's ternary output (true, false, maybe). In these borderl
  TOK: [SCI-000138#results#FULLTEXT-331] | SEC: RESULTS
- [SCI-000138/fulltext] (NEUTRAL) In study design classification, the Cochrane classifier achieved perfect sensitivity (100%) for identifying RCTs but low specificity (42%) with 26 false positives, whereas Kernel's deployed domain-adapted configuration achieved perfect sensitivity and specificity on the same expert-annotated benchmark.
  QUOTE: the Cochrane classifier achieved perfect sensitivity (100%) for identifying randomized controlled trials (RCTs) but low specificity (42%). This imbalance resulted from 26 false positives, indicating a tendency to overcla
  TOK: [SCI-000138#results#FULLTEXT-332] | SEC: RESULTS
- [SCI-000138/fulltext] (NEUTRAL) Machine-human discord in screening was largely attributable to missing or weakly articulated PICOS elements rather than definitional conflicts, indicating that disagreement reflected borderline eligibility rather than systematic model error.
  QUOTE: Most disagreements were concentrated in abstracts with underspecified PICOS elements, where experts themselves expressed uncertainty, indicating that discordance primarily reflected borderline eligibility rather than sys
  TOK: [SCI-000138#results#FULLTEXT-333] | SEC: RESULTS
- [SCI-000138/fulltext] (POSITIVE) On the NCD corpus, Kernel achieved 95% agreement with expert inclusion/exclusion judgments and three-way concordance among Kernel, the LLM, and the human assessor reached 91%, with Cohen's Kappa of 0.70 for Kernel versus human annotations, evidencing inter-rater reliability.
  QUOTE: Kernel and the prompted LLM each achieved 95% agreement with expert judgments, and three-way concordance among Kernel, the LLM, and the human assessor reached 91%. Agreement beyond chance was moderate, with Cohen's Kappa
  TOK: [SCI-000138#results#FULLTEXT-334] | SEC: RESULTS
- [SCI-000140/fulltext] (POSITIVE) A reproducible human audit of a 20% random sample (272 of roughly 1,360 items) of the scored benchmark results agreed with 96% of automated judge verdicts (Cohen’s κ = 0.94), with all 11 discrepancies confined to one-step severity nuances in the grounding benchmark and none reversing a supported/unsupported call.
  QUOTE: A reproducible human audit of 20% of scored results (272 of roughly 1,360 items) agreed with 96% of verdicts (Cohen’s κ = 0.94); dis- crepancies were one-step severity differences, never reversals between supported and u
  TOK: [SCI-000140#discussion-limitations#FULLTEXT-345] | SEC: Discussion > Limitations
- [SCI-000140/fulltext] (NEUTRAL) BR-KG attaches explicit provenance to source-backed facts, including a verbatim supporting quote and grounding label wherever available, so a retrieved claim can be traced to the study and passage that support it, and coverage is partial and tracked.
  QUOTE: Crucially, source-backed facts carry explicit provenance (their source, and where available a verbatim supporting quote and grounding label), so a retrieved claim can be traced back to the study and passage that support 
  TOK: [SCI-000140#results-figure-2-caption-br-kg#FULLTEXT-346] | SEC: Results > Figure 2 caption: BR-KG
- [SCI-000140/fulltext] (POSITIVE) In the evidence-citation benchmark, Brain Researcher raised verifiable grounding from 4.6% to 22.0%: a claim is counted grounded only when its cited evidence can be located and judged supportive, and the dominant with-BR failure modes were off-topic or partially-supporting retrieved sources rather than fabricated references.
  QUOTE: Among all 814 with-BR rows present in the three judge outputs, 777 (95%) cited a retrieved document, of which 367 (47%) received a verified majority; 3 of 37 (8%) specific citations produced from the model’s own paramete
  TOK: [SCI-000140#supplementary-methods-s11-1-2-evidence-c#FULLTEXT-347] | SEC: Supplementary Methods > S11.1.2: Evidence-citation benchmark
- [SCI-000141/fulltext] (NEGATIVE) The paper identifies the unclear accuracy of Generative AI in research as one of the challenges for effectively integrating AI into research workflows.
  QUOTE: effectively integrating AI into research remains a challenge due to varying domain requirements, limited AI literacy, the complexity of coordinating tools and agents, and the unclear accuracy of Generative AI in research
  TOK: [SCI-000141#abstract#FULLTEXT-358] | SEC: Abstract
- [SCI-000141/fulltext] (POSITIVE) The provenance-recording design is motivated in part by integrity verification: recording provenance data and publishing it will help users verify the accuracy and originality of AI-generated content.
  QUOTE: These aspects will also help users verify the accuracy and originality of the generated content.
  TOK: [SCI-000141#4-framework-for-ai-assisted-research-4-2#FULLTEXT-359] | SEC: 4 Framework for AI-Assisted Research > 4.2 Design Principles > Transparency and Trustworthiness
- [SCI-000142/fulltext] (POSITIVE) Automated overclaim detection scans generated manuscript text for 12 predefined patterns including causal language for non-randomized data, overgeneralization, recommendations without evidence level, and absence of evidence as evidence of absence.
  QUOTE: The automated overclaim detection system (Stage 09) scans generated manuscript text for the following 12 patterns: 1 Causal language for non-randomized data Causal verbs (caused, led to, resulted in) used for observation
  TOK: [SCI-000142#meta-pipe-s4-overclaim-detection-pattern#FULLTEXT-366] | SEC: meta-pipe > S4 Overclaim Detection Patterns
- [SCI-000142/fulltext] (NEUTRAL) Title and abstract screening uses a test-retest reliability approach with two independent LLM screening passes at temperature 0.3, quantified using Cohen's kappa, with a minimum threshold of 0.60 below Cochrane's 0.80 for dual review.
  QUOTE: Title and abstract screening employs a test-retest reliability approach: the LLM performs two independent screening passes at temperature 0.3, and agreement is quantified using Cohen's kappa. The minimum kappa threshold 
  TOK: [SCI-000142#methods-search-and-screening#FULLTEXT-367] | SEC: Methods > Search and Screening
- [SCI-000144/fulltext] (NEGATIVE) Across 17,443 generated citations, no model exceeds a citation-level existence rate of 0.475, with Temporal and Combo conditions producing the steepest drops while outputs remain format-compliant.
  QUOTE: Across 17,443 generated citations, no model exceeds a citation-level existence rate of 0.475; Temporal and Combo conditions produce the steepest drops while outputs remain format-compliant (well-formed bibliographic fiel
  TOK: [SCI-000144#abstract#FULLTEXT-373] | SEC: Abstract
- [SCI-000144/fulltext] (NEUTRAL) Manual validation of the pipeline on a stratified sample of 100 citations gave overall agreement of 75% and Cohen's kappa 0.63, with precision 0.97 for Existing, 0.88 for Fabricated but only 0.43 for Unresolved; the dominant error was Unresolved-to-Fabricated (16 cases).
  QUOTE: Overall agreement was 75% and Cohen's 𝜅 (pipeline vs. human) was 0.63. Precision was 0.97 for Existing and 0.88 for Fabricated, but only 0.43 for Unresolved. The dominant error was Unresolved →Fabricated (16 cases), so o
  TOK: [SCI-000144#4-verification-pipeline-pipeline-validat#FULLTEXT-374] | SEC: 4 Verification Pipeline > Pipeline validation
- [SCI-000144/fulltext] (NEUTRAL) Non-Disclosure instructions redistribute rather than eliminate errors: DOI completeness drops (most pronounced for LLaMA, -11.4 percentage points) and, because DOI is the strongest verification signal, citations shift from Existing into Unresolved — moving errors from 'obviously wrong' into 'hard to tell.'
  QUOTE: DOI completeness drops under Non-Disclosure (most pronounced for LLaMA, 11.4 percentage points), and because DOI is the strongest verification signal, its suppression pushes citations from Existing into Unresolved
  TOK: [SCI-000144#zhao-et-al-non-disclosure-ablated-analys#FULLTEXT-375] | SEC: Zhao et al. > Non-Disclosure ablated analysis
- [SCI-000144/fulltext] (NEGATIVE) The manual audit of fabricated/unresolved citations reveals four recurring failure modes that format-level checks miss: venue laundering, author bricolage, identifier fabrication and omission, and title drift.
  QUOTE: Manual inspection of fabricated and unresolved citations reveals four recurring failure modes that format-level checks would not catch: · Venue laundering. A plausible venue name (e.g., IEEE TSE, ICSE) is paired with a t
  TOK: [SCI-000144#6-discussion-6-1-qualitative-error-patte#FULLTEXT-376] | SEC: 6 Discussion > 6.1 Qualitative Error Patterns
- [SCI-000144/fulltext] (POSITIVE) The paper recommends that systems surfacing LLM-generated references run post-hoc verification against multiple databases and treat Unresolved citations as high risk.
  QUOTE: Systems surfacing LLM-generated references should run post-hoc verification against multiple databases and treat Unresolved as high risk.
  TOK: [SCI-000144#6-discussion-6-2-implications-for-practi#FULLTEXT-377] | SEC: 6 Discussion > 6.2 Implications for Practice
- [SCI-000144/fulltext] (NEUTRAL) The verification pipeline assigns a three-way label (Existing, Unresolved, Fabricated) and was audited against human labels with Cohen's kappa = 0.63.
  QUOTE: Our contributions are (1) a curated dataset of 144 claims spanning six academic domains (including 24 in SE & CS), (2) an automated verification pipeline with an audited three-way label taxonomy (Cohen's 𝜅=0.63 vs. human
  TOK: [SCI-000144#abstract-contributions#FULLTEXT-378] | SEC: Abstract > Contributions
- [SCI-000144/fulltext] (NEGATIVE) Under the Temporal condition every model produces well-formed bibliographic entries respecting the requested year window, yet GPT-4o's existence rate drops from 0.235 to 0.019, so format compliance masks a near-complete loss of verifiability ('compliance without substance').
  QUOTE: First, compliance without substance: under the Temporal condition every model produces well-formed bibliographic entries that respect the requested year window, yet existence rates fall sharply—GPT-4o drops from 0.235 to
  TOK: [SCI-000144#6-discussion#FULLTEXT-379] | SEC: 6 Discussion
- [SCI-000146/abstract_only] (NEGATIVE) LLMs do not always perform well in mathematical reasoning tasks, which raises questions about whether their probability outputs for screening decisions are meaningful.
  QUOTE: LLMs do not always perform well in mathematical reasoning tasks, which raises the question whether their probability outputs are meaningful.
  TOK: [SCI-000146#abstract#FULLTEXT-384] | SEC: ABSTRACT
- [SCI-000151/fulltext] (NEGATIVE) Consumer LLM interfaces such as ChatGPT are reported to face significant challenges in output reliability and consistency, adherence to systematic-review methodology, and academic-integrity ethics.
  QUOTE: Yet, various consumer LLM interfaces such as ChatGPT encountered significant challenges in ensuring reliability and consistency of outputs, adhering to rigorous systematic review methodologies, and addressing ethical con
  TOK: [SCI-000151#1-introduction#FULLTEXT-390] | SEC: 1 Introduction
- [SCI-000151/fulltext] (NEUTRAL) LLAssist requires its LLMs to output reasoning for every relevance/contribution judgment, which doubles as a cognitive forcing function acting as a checkpoint before downstream processing.
  QUOTE: The LLMs have to output their reasoning to help the researchers in manually discriminating the articles [Vasconcelos et al., 2023] and can be also part of cognitive forcing functions to be the checkpoint before downstrea
  TOK: [SCI-000151#4-1-4-reasoning-quality#FULLTEXT-391] | SEC: 4.1.4 Reasoning Quality
- [SCI-000151/fulltext] (NEGATIVE) The authors argue that reliance on closed, proprietary AI systems compromises reproducibility, and position LLAssist as a transparent, freely-modifiable open-source alternative.
  QUOTE: Without transparent, open-source tools for AI-assisted literature review, researchers face potential limita- tions in research transparency and replicability that potentially perpetuate biases. These challenges include o
  TOK: [SCI-000151#1-introduction#FULLTEXT-392] | SEC: 1 Introduction
- [SCI-000152/fulltext] (NEGATIVE) The authors conclude that while LLMs were not trustworthy as independent reviewers, they improved the human results by reducing the number of false negatives and false positives after rescreening was completed.
  QUOTE: While LLMs were not trustworthy as independent reviewers, they improved the human results by reducing the number of false negatives and false positives after rescreening was completed.
  TOK: [SCI-000152#discussion#FULLTEXT-401] | SEC: DISCUSSION
- [SCI-000152/fulltext] (NEGATIVE) The study finds that the human rater and both LLMs performed poorly in sensitivity, especially GPT-4o Mini, meaning they failed to include all relevant articles, which is problematic because the main goal of SLRs is to include all available research results on a topic.
  QUOTE: The human rater and both LLMs performed poorly in sensitivity, especially GPT-4o Mini, meaning that they failed to include all relevant articles. For SLRs, low specificity means more rescreening time due to including pot
  TOK: [SCI-000152#discussion#FULLTEXT-402] | SEC: DISCUSSION
- [SCI-000152/fulltext] (NEUTRAL) The study uses a benchmark constructed by combining the title/abstract ratings of the human rater and both LLMs as the ground truth, which the authors acknowledge has limitations in measuring human performance reliably.
  QUOTE: We combined the title/abstract ratings of the human rater and both LLMs to create a benchmark. We evaluated the accuracy, sensitivity and specificity of the human rater and LLMs against the benchmark.
  TOK: [SCI-000152#conclusions#FULLTEXT-403] | SEC: CONCLUSIONS
- [SCI-000154/fulltext] (NEGATIVE) In experiments, GPT-4o fabricated citations in 78-90% of cases when asked to cite recent literature across fields such as computer science and biomedicine, whereas OpenScholar achieved citation accuracy on par with human experts, addressing a key hallucination/verifiability risk.
  QUOTE: LLMs can assist but suffer from hallucinations2,3, outdated pre-training data4 and limited attribution. In our experiments, GPT-4o fabricated citations in 78-90% of cases when asked to cite recent literature across field
  TOK: [SCI-000154#introduction#FULLTEXT-414] | SEC: INTRODUCTION
- [SCI-000154/fulltext] (POSITIVE) OpenScholar produces citation-backed, retrievable responses by identifying relevant passages from the open-access corpus and synthesizing citation-backed answers, giving users a verifiable provenance chain from answer to source passage.
  QUOTE: a specialized retrieval-augmented language model (LM)1 that answers scientific queries by identifying relevant passages from 45 million open-access papers and synthesizing citation-backed responses.
  TOK: [SCI-000154#abstract#FULLTEXT-415] | SEC: ABSTRACT
- [SCI-000154/fulltext] (POSITIVE) ScholarQABench introduces a rigorous evaluation protocol combining automatic metrics such as citation accuracy with human rubric-based assessments of coverage, coherence, writing quality and factual correctness, enabling reliable assessment of long-form answers.
  QUOTE: ScholarQABench introduces a rigorous evaluation pro-tocol combining automatic metrics (for example, citation accuracy) with human rubric-based assessments of coverage, coherence, writing quality and factual correctness t
  TOK: [SCI-000154#evaluation#FULLTEXT-416] | SEC: EVALUATION
- [SCI-000156/fulltext] (POSITIVE) Generated summaries are required to mention the first author's name and paper title, providing basic attribution grounding.
  QUOTE: Please mention the first author’s name and paper title.
  TOK: [SCI-000156#body#FULLTEXT-424] | SEC: body
- [SCI-000156/fulltext] (NEGATIVE) The pipeline merges assistant responses per paper into a final review segment without any described verification or cross-checking of the generated content against sources.
  QUOTE: Then the response from the assistant is retrieved and the outputs of each paper are merged for the final literature review segment.
  TOK: [SCI-000156#body#FULLTEXT-425] | SEC: body
- [SCI-000158/fulltext] (supportive) The system's standardization of the SLR process can potentially lead to more consistent and replicable research outcomes, though it requires human oversight in guiding and interpreting results.
  QUOTE: the system's standardization of the SLR process can potentially lead to more consistent and replicable research outcomes, a cornerstone in scientific research. ... it is important to acknowledge the role of human oversig
  TOK: [SCI-000158#section-5-discussion-section-8-conclusio#FULLTEXT-433] | SEC: Section 5 (Discussion) / Section 8 (Conclusions)
- [SCI-000159/fulltext] (supportive) Non-retrieval augmented LLMs fabricate 78–98% of cited papers, with the problem exacerbated in biomedical domains; even when citations refer to real papers, the majority are not substantiated by corresponding abstracts, resulting in near-zero citation accuracy.
  QUOTE: the proportion of cited papers that actually exist is strikingly low. In particular, while models such as GPT4o and Llama can generate plausible reference lists, we find that 78-98% of the cited papers are fabricated, an
  TOK: [SCI-000159#section-4-2-results-limitations-of-param#FULLTEXT-442] | SEC: Section 4.2 (Results) / Limitations of parametric LMs
- [SCI-000159/fulltext] (supportive) OpenScholar-8B achieves zero hallucinated papers in both computer science and biomedicine, in stark contrast to baseline LLMs (Llama 3.1 8B: 92.1% CS, 97.6% Bio hallucination ratios).
  QUOTE: OS-8B 9.65 0.0 0.0 6.25 0.0 0.0 Llama 3.1 8B 5.20 4.79 92.1% 5.58 5.46 97.6%
  TOK: [SCI-000159#table-3-statistics-of-hallucinated-paper#FULLTEXT-443] | SEC: Table 3 (Statistics of hallucinated papers)
- [SCI-000159/fulltext] (supportive) The self-feedback mechanism iteratively refines outputs: the LM generates an initial response, self-feedback, and incorporates feedback to produce an updated response, addressing unsupported claims and incomplete outputs.
  QUOTE: this one-step generation can lead to unsupported claims (Liu et al., 2023) or incomplete output due to missing information (Asai et al., 2024; Jiang et al., 2023). To address these challenges, in OPENSCHOLAR, we introduc
  TOK: [SCI-000159#section-2-2-inference-iterative-generati#FULLTEXT-444] | SEC: Section 2.2 (Inference: Iterative Generation with Retrieval-Augmented Self-Feedback)
- [SCI-000164/fulltext] (NEGATIVE) The authors report a trust risk: since LLMs can perpetuate and amplify training-data biases, LGAR may inadvertently reinforce these biases when ranking abstracts, potentially skewing SLR outcomes.
  QUOTE: Furthermore, since LLMs can perpetuate and amplify biases present in the training data, LGAR may inadvertently reinforce these biases when rank- ing abstracts. This could lead to certain research being unfairly prioritiz
  TOK: [SCI-000164#6-limitations#FULLTEXT-452] | SEC: 6 Limitations
- [SCI-000164/fulltext] (NEGATIVE) The evaluation cannot exclude data contamination because many benchmark SLRs were published years ago and their data may already have been exposed to LLMs during pre-training.
  QUOTE: In addition, since many of these SLRs were pub- lished several years ago, some of their data may have already been exposed to the LLMs in their training. Hence, we can not exclude the possibility of data contamination.
  TOK: [SCI-000164#6-limitations#FULLTEXT-453] | SEC: 6 Limitations
- [SCI-000172/fulltext] (supportive) Feeding curated data via Azure AI Search to the LLM is described as the first step for avoiding hallucinations; the LLM is instructed to return citations linked to response, pointing to original documents — a decisive factor for raising trust.
  QUOTE: feeding curated data via Azure AI Search to an LLM is the first step. The LLM model will receive a specific context, a specific prompt and it will respond only with information from the private data to queries. In will a
  TOK: [SCI-000172#methodology-avoiding-hallucinations#FULLTEXT-464] | SEC: Methodology (avoiding hallucinations)
- [SCI-000172/fulltext] (supportive) Temperature was decreased to 0.1 (from default 0.7) and Top P set to 0.95 to maximize precision and restrict the model to high-probability tokens, with the Assistant instructed to answer only from custom indexed information.
  QUOTE: The standard Temperature value of 0.7, was decreased to 0.1, since the intention of the solution is to deliver very precise answers, based only on the information indexed into Azure AI. In the same direction, Top P value
  TOK: [SCI-000172#methodology#FULLTEXT-465] | SEC: Methodology
- [SCI-000177/abstract_only] (NEGATIVE) Systematic reviews guided by PRISMA frameworks are acknowledged as thorough but labor-intensive and prone to human bias, motivating the need for AI-assisted evidence synthesis.
  QUOTE: Systematic reviews, guided by frameworks like PRISMA [3], can be thorough but also labor-intensive and prone to human bias [4,5]
  TOK: [SCI-000177#abstract#FULLTEXT-471] | SEC: ABSTRACT
- [SCI-000179/fulltext] (NEGATIVE) The current implementation has no formal mechanism for detecting misinformation or verifying the factual correctness of AI-generated outputs, a limitation the authors flag for future development.
  QUOTE: the current implementation does not include a formal mechanism for detecting misinformation or verifying the factual correctness of AI-generated outputs.
  TOK: [SCI-000179#results-and-discussion-limitations-and-f#FULLTEXT-478] | SEC: Results and Discussion > Limitations and Future Directions
- [SCI-000179/fulltext] (POSITIVE) When abstracts were unavailable, the AI module explicitly documented the limitation and generated context-aware summaries from available bibliographic information rather than silently fabricating content.
  QUOTE: When abstracts were unavailable, the AI module explicitly documented this limitation and generated context-aware summaries based on available bibliographic information.
  TOK: [SCI-000179#results-and-discussion-ai-assisted-abstr#FULLTEXT-479] | SEC: Results and Discussion > AI-Assisted Abstract Review Performance
- [SCI-000181/fulltext] (POSITIVE) Automated fact-checking processes that verify claims against retrieved evidence improved response accuracy, and comprehensive citation tracking that links specific claims to source documents achieved high traceability, allowing users to directly verify information sources.
  QUOTE: Implementation of automated fact-checking processes that verify claims against retrieved evidence improved response accuracy in controlled evaluations. Additionally, comprehensive citation tracking that links specific cl
  TOK: [SCI-000181#llm-integration#FULLTEXT-490] | SEC: LLM INTEGRATION
- [SCI-000181/fulltext] (POSITIVE) Citation accuracy evaluation found that the vast majority of system-generated citations directly supported the associated claims, with a small percentage providing partial support and only a tiny fraction being irrelevant or misleading, described as approaching human literature reviews.
  QUOTE: Detailed analysis of system-generated citations found that the vast majority of provided citations directly supported the associated claims, with a small percentage providing partial support, and only a tiny fraction bei
  TOK: [SCI-000181#evaluation#FULLTEXT-491] | SEC: EVALUATION
- [SCI-000181/fulltext] (POSITIVE) Experimental comparisons revealed that prompts incorporating domain guidance, explicitly requesting scientific rigor, and specifying citation requirements reduced hallucination compared to general-purpose prompts.
  QUOTE: Experimental comparisons of different prompting strategies revealed that prompts incorporating domain guidance, explicitly requesting scientific rigor, and specifying citation requirements reduced hallucination compared 
  TOK: [SCI-000181#llm-integration#FULLTEXT-492] | SEC: LLM INTEGRATION
- [SCI-000181/fulltext] (POSITIVE) The citation accuracy result is described as providing the verification capability essential for scientific work, directly addressing answer-to-source verifiability.
  QUOTE: This level of citation accuracy approaches that of human literature reviews and provides the verification capability essential for scientific work.
  TOK: [SCI-000181#evaluation#FULLTEXT-493] | SEC: EVALUATION
- [SCI-000186/fulltext] (NEGATIVE) Peer-review feedback on EvoScientist-generated manuscripts exposed protocol-level issues (ambiguities in stability gating, metric reporting, and baseline fairness), leading the authors to conclude that strict consistency auditing and reproducibility-complete reporting are required in end-to-end discovery systems.
  QUOTE: Reviewer feedback also identified several internal- consistency and protocol-level issues, including ambiguities in stabil- ity gating, metric reporting, and baseline fairness. These critiques underscore the importance o
  TOK: [SCI-000186#appendix-e-case-studies-peer-review-feed#FULLTEXT-503] | SEC: Appendix E (Case Studies / Peer Review Feedback)
- [SCI-000186/fulltext] (NEGATIVE) The authors flag that EvoScientist, because it learns from existing literature, may reproduce biases in data and writing and therefore should be monitored and audited — an acknowledgment that its self-evolution mechanism carries academic-integrity risk.
  QUOTE: Since the system learns from existing literature, it may reproduce biases in data and writing [27, 28, 32], and should be monitored and audited accordingly.
  TOK: [SCI-000186#7-limitations-and-ethical-considerations#FULLTEXT-504] | SEC: 7 Limitations and Ethical Considerations
