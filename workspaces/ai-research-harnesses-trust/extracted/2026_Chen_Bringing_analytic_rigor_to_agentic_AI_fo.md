---
workspace_id: "SCI-000140"
doi: null
title: "Bringing analytic rigor to agentic AI for science: The Brain Researcher platform for neuroimaging data analysis"
year: 2026
extraction_engine: "pymupdf"
---
# 2026 Chen Bringing analytic rigor to agentic AI fo

Bringing analytic rigor to agentic AI for science: The

Brain Researcher platform for neuroimaging data

analysis

Zijiao Chen1, Nicholas Lu1, Xinhui Li2, Jocelyn A. Ricard1, Ce Ju3, Huan H. Wang1,

Christian Kindermann1, Jeanette A. Mumford1, Steven Dillmann1, James Kent4, Alejandro de la Vega4, Sanmi Koyejo1, Vince D. Calhoun2, Joshua W. Buckholtz1,

Juan Helen Zhou5, Steffen Bollmann1,6, Russell A. Poldrack1

Correspondence: russpold@stanford.edu

1Stanford University, Stanford, CA, USA 2Tri-institutional Center for Translational Research in Neuroimaging and Data Science (TReNDS), Georgia State University, Georgia Institute of Technology, Emory University, Atlanta, GA, USA

arXiv:2608.19902v1  [cs.AI]  20 Aug 2026

3Inria, CEA, Universit´e Paris-Saclay, Palaiseau, France 4The University of Texas at Austin, Austin, TX, USA 5National University of Singapore, Singapore 6The University of Queensland, Brisbane, QLD, Australia


## Abstract

AI agents can execute scientific analyses, but an analytic output becomes a defensible claim only after alternatives are weighed and the claim is limited to what the evidence supports. Agents may reproduce failures including selective analysis, premature declarations of success and optimization of imperfect criteria. We present Brain Researcher, an agentic research harness operating in a neuroimaging researcher’s computational environment under rules for admissible analyses, required checks and claim scope. In benchmarks, Brain Researcher increased first-choice tool-selection ac- curacy across seven models by 70.2 percentage points (23.3% without it versus 93.6% with it) and verifiable grounding from 4.6% to 22.0%. In collaborator-led and self-evolving studies, multiverse analyses exposed analytic-choice sensitivity, and scientific review classified claims as accepted, qual- ified, revised, blocked, rejected or deferred. By linking decisions to evidence and provenance, Brain Researcher embeds methodological judgment within the workflow, not after it.

Keywords: neuroimaging; scientific agents; reproducibility; research infrastructure; analytic flex- ibility

Science often advances by absorbing its former frontiers into infrastructure: what once marked the edge of scientific practice, such as sequencing a genome or preprocessing a brain scan, becomes a routine step in a larger workflow. AI agents may represent the next phase of this progression. They increasingly interpret goals, call external tools, observe intermediate results, and choose subsequent actions [5, 27, 30, 41, 52]. Yet scientific research is not only a sequence of procedures, and executing an analysis is not the same as establishing a claim. This distinction is especially consequential in neuroimaging, where large, heterogeneous datasets enter long analysis pipelines with multiple defensible choices. Decisions about preprocessing, parcellation, confound adjustment, and model specification can materially reshape results [9, 20, 36, 45]; when seventy teams analyzed the same neuroimaging dataset, no two used the same workflow and their conclusions differed substantially [6].

Neuroimaging has also developed one of the most mature open-science ecosystems for compu- tational automation. BIDS and OpenNeuro standardize data organization and sharing [39, 46]; fMRIPrep automates functional MRI preprocessing [21]; and Nipype integrates software packages

1

into reproducible workflows [26]. BIDS Statistical Models and FitLins extend this standardization to machine-readable statistical models and their execution [12, 40], while guided multiverse analysis makes alternative workflows more navigable [13]. Together, these tools make procedures, and in- creasingly their alternatives, reusable and comparable. They do not, however, bind a selected route to the evidence and methodological conditions required for the claim it is used to support. The challenge is therefore not simply to automate neuroimaging analysis, but to ensure that automation does not obscure the methodological conditions under which an analysis may support a claim.

Tool-using agents create both an opportunity and a risk. They can connect fragmented stages of an analysis and adapt after observing intermediate outcomes, but successful command execution does not guarantee a scientifically valid analysis. An agent may select an inappropriate tool, overlook a data or model incompatibility, stop prematurely, or optimize a criterion that is misaligned with the intended claim. These failures parallel questionable research practices in human-executed science [32, 48], and are compounded by premature declarations of task completion [29, 33] and reward hacking [22, 50]. Scientific agents therefore need more than access to tools: they need reliable routing, evidence linked to its methodological conditions, explicit exposure of alternative specifications, and a visible boundary between formalizable checks and judgments that remain with the researcher.

Here we present Brain Researcher, a researcher-governed, domain-specific agentic harness that operates inside a neuroimaging researcher’s existing computational environment. Brain Researcher is designed to preserve rather than replace scientific judgment: it operationalizes the parts that researchers can state in advance and records the rest for inspection. For prospectively governed analyses, the researcher specifies the question, admissible analyses, required checks, and scope of any resulting claim. A tool registry and the Brain Researcher Knowledge Graph connect analysis routes to evidence and method conditions; a Model Context Protocol server mediates model ac- tions; and execution and review layers return an audit bundle linking the committed plan, tool calls, artifacts, evidence, and claim verdicts (Fig. 1; Supplementary Methods S1). Multiverse analyses expose sensitivity to defensible specifications [51], while commitment and claim cards preserve what was decided before and after results were observed. In self-evolving research, intermediate evidence can redirect the trajectory only within a researcher-defined action space specifying the admissi- ble analyses, datasets, and evaluation budget; each successor analysis is frozen before execution. Judgments that resist formalization remain with the researcher.

We evaluated Brain Researcher in three settings. First, a paired seven-model tool-calling bench- mark and a separate evidence-citation benchmark tested whether the harness improves upstream tool selection and evidence citation. Second, three collaborator-led studies tested whether mul- tiverse analyses and explicit constraints make claim sensitivity and status visible. Third, two self-evolving research episodes tested whether evidence from one stage could be carried into a frozen successor analysis. Together, these evaluations ask whether AI assistance becomes more ca- pable and more defensible when methodological commitments, evidence, and claim scope are made explicit and auditable.


## Results

Brain Researcher converts research questions into auditable claim records

At the center of Brain Researcher is a complete, auditable record of a single run: a persistent episode linking the question to its assembled evidence, the analyses the researcher deemed admissible, the committed plan, the execution, the review, and a condition-tagged conclusion (Supplementary Methods S2). Two dated records can anchor it. A commitment card, written before any analysis

2


> **Figure 1: Brain Researcher: workspace-centric infrastructure for auditable neuroimag-**

> ing research. Brain Researcher runs inside the researcher’s existing computational environment
and exposes neuroimaging analyses as structured, auditable operations: every choice, check, and
input is recorded as it happens, so that a frozen record of the completed analysis can be read
and audited by someone other than the person who ran it, without re-executing it. (a) The tool
ecosystem: established neuroimaging software for preprocessing, modeling, meta-analysis, machine
learning, quality control, and reporting, each represented by a machine-readable specification and
executed in a version-pinned container. (b) Each specification declares its inputs, outputs, param-
eters, version, evidence anchors, and validation rules; the rule checker tests every proposed call
against these clauses before it runs, and records which clauses passed or failed. (c) The episode
workflow: the researcher frames a question and approves the plan at the commitment gate, valid
actions are dispatched to version-pinned executors, and the resulting audit bundle, containing the
committed plan, tool versions, evidence consulted, artifacts, logs, provenance, and the checks each
claim passed, feeds the review layer, which writes condition-tagged claims back to memory. This
audit bundle is what makes an analysis auditable: a completed run is a fully inspectable research
object rather than a one-off result, exported as a compact claim card a reviewer can reopen field by
field. Methodological judgment remains the researcher’s; the system makes it visible at each stage.

3


> **Figure 2: BR-KG: provenance-linked semantic integration for grounded, auditable neu-**

> roimaging reasoning. BR-KG integrates existing ontologies, repositories, data resources, and
literature into a single graph (745,949 nodes, 2,461,469 edges; 2026-07-07 release snapshot) aligned
to the OpenNeuro Vocabulary (ONVOC) [44], which normalizes heterogeneous terms to shared
identifiers so a query resolves consistently across sources. The central graph links neuroimaging
concepts (tasks, contrasts, cognitive constructs), neural representations (brain regions, statistical
maps), and research resources (datasets, tools) through typed relationships, with literature evidence
attached. Crucially, source-backed facts carry explicit provenance (their source, and where available
a verbatim supporting quote and grounding label), so a retrieved claim can be traced back to the
study and passage that support it rather than taken on trust; coverage is partial and tracked, and
this is what makes retrieval here auditable. Downstream panels show the payoff: grounded query
answering and multi-hop reasoning over concept-task-map paths, each hop inspectable down to its
underlying nodes, edges, and cited evidence, which lets the review layer attach a recommendation’s
method-condition checks (cohort, paradigm, preprocessing, statistical model) before it is accepted.

4

runs, fixes the question, the allowed alternatives, and the success and failure criteria, and is sealed with a content hash so that any later change to the plan is detectable. A claim card, written afterward by the review layer, records the resulting claim, its assigned state, scope, and the checks it passed and failed; the supplement includes a specific worked example, built on public Neurosynth data, that a reader can open and inspect field by field (Supplementary Methods S8.5.1; Appendix G). A reviewer can then reopen and audit the record without re-executing the analysis. Across the collaborator-led and self-evolving evaluations reported below, every evaluated claim is assigned one of six states (accepted, qualified, revised, blocked, rejected, or deferred), each defined by an explicit adjudication rule. For example, when a researcher asks whether two groups differ on a functional-connectivity measure, the commitment card records the cohort, the subject groups, and the estimator (either entered by the researcher or resolved from the dataset) and fixes the checks that must pass before anything runs (aligned subject groups, a full-rank design matrix, no feature leakage across folds). If the difference then holds in only some admissible specifications, the claim is recorded as qualified, with its conditions attached. These methodological decisions are the researcher’s; Brain Researcher records each one and enforces the checks it implies.

Brain Researcher improves tool calling and evidence citation

We first isolated the infrastructure’s effect on two decisions that precede scientific review: choosing the correct analysis tool and citing checkable evidence. The tool-calling benchmark pairs each re- quest with a hidden scoring target and reports Correct route/tool@k (all-or-nothing match of the analysis family and required capabilities), Capability@k (graded capability coverage), and Handoff score@k (whether the proposed route is specified completely enough to execute, with the required inputs present, so it can be handed to a downstream executor and run without gaps) (Supple- mentary Methods S11.1.1); three condition-blind LLM judges credit any response that reaches the required capabilities, whether through a Brain Researcher call or an equivalent executable route, so the measured gain reflects reaching those capabilities rather than credit for naming Brain Re- searcher’s specific tools. Both conditions used the same seven frontier models [1, 3, 15, 25, 42, 43, 54] and general-purpose tools, the without-BR condition lacking only Brain Researcher’s registry (Sup- plementary Methods S5), knowledge graph, and constraint layer. Across 60 tool-calling tasks and seven models, scores without versus with Brain Researcher were 23.3% versus 93.6% for first-action correct route/tool selection (with-BR 95% CI 88.8–97.1, task-clustered), 49.8% versus 94.5% for mean Capability@1, and 47.4% versus 76.1% for handoff sufficiency. The reference route for each task was fixed before either condition ran and curated with a co-author who does not develop the Brain Researcher system; equivalent non-BR routes were set by two model reviewers and one human (Supplementary Methods S11.1.2). All seven models improved on all three tool-calling metrics (7/7 positive paired differences; exact two-sided Wilcoxon signed-rank p = 0.016 for each), with mean gains of 70.2 percentage points for Correct route/tool@1, 44.7 points for Capability@1, and 28.7 points for Handoff score@1. In a routing ablation across 60 tasks and seven models, Brain Researcher without direct KG calls selected an acceptable exact top-1 route in 362 of 420 episodes (86.2%; model range, 81.7–90.0%; details in Supplementary Methods S11.1.5). A sepa- rate 50-question benchmark counted a claim as grounded only when its cited evidence could be located and judged supportive; under a three-judge majority vote, the descriptive question-level verified-groundedness rate rose from 4.6% to 22.0% (95% CI 16.8–27.2, question-clustered), a 4.8- fold increase, though most evidence rows still failed, so grounding improved substantially without being solved. Among the 444 non-verified with-BR rows present in all three judge outputs, 65% received an exact-label majority of real but off-topic and 28% of partial support; the remaining 7% lacked an exact-label majority or could not be judged, and none had a fabricated or malformed

5

majority (Supplementary Methods S11.1.1). Inter-judge reliability and its dependence on judge strictness are reported in Supplementary Methods S11.1.2. Secondary single-judge safeguards con- firmed that the gain was not accompanied by more unrelated citations or lower answer correctness (Supplementary Methods S11.1.1; Appendix J; Fig. 3). Because the without-BR condition removes Brain Researcher’s registry, knowledge graph, and constraint layer together, this contrast measures the harness as a whole rather than isolating any single component; and because the reference routes were curated with a co-author, target construction may share vocabulary with the registry.


> **Figure 3: Summary of Brain Researcher effects across quantitative benchmark tasks.**

> Without-BR (gray) and with-BR (blue) benchmark performance. Capability@k is mean coverage of
required task capabilities after the first k non-neutral actions. The left column reports Capability@1
and @3 across the seven model variants (Claude Opus 4.8, Codex GPT-5.5, Gemini 3.1 Pro, GLM-
5.1, DeepSeek-V4-Pro, Kimi K2.5, Qwen3.6-Plus). Upper-right panels break Capability@1 down
by task domain. Lower panels report Handoff score@1 and @3 (whether the first route carries
enough information for another agent to continue) and a Gemini 2.5 Flash single-judge safeguard:
precision among claims marked grounded (fraction whose cited evidence was both locatable and
judged supportive). Correct route/tool@1, the first-action selection accuracy reported in the text
(23.3% to 93.6%), is detailed in Supplementary Methods S11.1.1. Metrics are interpreted within
panel, as denominators and scoring rules differ across benchmarks.

6

Brain Researcher runs multiverse analyses to expose claim sensitivity

We next evaluated Brain Researcher on three active neuroimaging research questions from collab- orating scientists (schizophrenia NeuroMark connectivity, cocaine-use-disorder connectivity, and cross-cultural social-cognition meta-analysis), chosen for heterogeneity in evidence structure with- out regard to the specific outcomes (Fig. 4). Every reported analysis case was run by a coding agent on the local system, which called Brain Researcher for grounding, logging, and review (Supplemen- tary Methods S11.2). The NeuroMark case starts from a single, well-established pipeline that its developers use as their standard, giving the audit one clearly defined baseline to build the multi- verse around; the other two cases have no such established single pipeline, and test whether the workflow extends to that more difficult setting. The collaborators’ hypotheses were pre-specified in their own protocols rather than sealed as commitment cards, so the NeuroMark record is a post-hoc audit of the completed multiverse.

A collaborator studying schizophrenia functional network connectivity using the NeuroMark framework [17, 31] brought three pre-specified hypotheses for robustness audit: latent connectivity factors outperform individual edges for patient-versus-control classification (NM-H1); between- domain connections show larger group differences than within-domain ones (NM-H2); and latent factors concentrate loading mass on between-domain edges (NM-H3). We evaluated these hy- potheses in the FBIRN cohort [34] (N = 363; 181 controls, 182 patients), parcellated through NeuroMark 2.2 template-based independent component analysis into 5,460 edges per subject. In the collaborator’s workspace, Brain Researcher expanded the analysis into a 480-specification multi- verse spanning connectivity, confound, dimensionality-reduction, classifier, and domain-granularity choices, and recorded and reviewed the resulting runs.

None of the three hypotheses was supported uniformly across specifications; all were recorded as qualified, but for different patterns of conditional support. Under the corrected sign-aware cri- terion (p < 0.05 and ∆mean|d| > 0), 12 of 24 unique connectivity–confound–domain contrasts favored NM-H2. This pooled fraction obscured a complete estimator split: 100% of contrasts were favorable under Pearson and Spearman and 0% under partial correlation and mutual information. NM-H2 is therefore an estimator-regime–dependent finding rather than a generally robust effect. Because partial correlation and mutual information alter the dependence measure in non-equivalent ways, distinguishing shared covariance from estimator scale, power, or nonlinearity requires targeted follow-up. NM-H1 and NM-H3 were also weak: edges outperformed latent factors in aggregate (me- dian ∆AUC = −0.032; only 18.8% of specifications favored latent features), and only 26.0% favored between-domain loading mass. These claims were qualified rather than rejected because support persisted within identifiable analytic subfamilies (Supplementary Methods S11.2.1; Fig. 4A–C); a claim with no supporting subfamily is rejected instead (Supplementary Methods S8.4).

NM-H2 also supplied the audit’s governance lesson: automated review missed an error that a human caught. After a server-side fault triggered fallback to a general-purpose coding agent, the agent scored any specification with permutation p < 0.05 as favorable regardless of sign, inflating apparent support for a directional hypothesis to near-universal levels. The review layer did not flag the error; a human reviewer detected it by inspecting the code, outputs, and specification curve, leading to the corrected rescoring above. Two checks were then added to the Brain Researcher skillset: a directionality test requiring the statistic and acceptance rule to match the hypothesized sign, and a warning whenever execution falls back to a general-purpose agent. The review missed this error. The record nevertheless provided value by binding each claim to its hypothesis, statistic, and conditions, thereby turning a one-off correction into an enforced check.

In the other two episodes, prespecified checks in the scientific review layer determined whether a result could receive confirmatory status. The SUDMEX CONN (OpenNeuro ds003346; N = 138)

7


> **Figure 4: Multiverse sensitivity and claim-review outcomes across three collaborator**

> episodes. (A–C) Schizophrenia NeuroMark audit: (A) group-mean functional connectivity for
controls (HC, N = 181), patients (SZ, N = 182), and their difference across four estimators; (B)
NM-H2 (between- versus within-domain) specification curve over the 480-specification multiverse;
after sign-aware rescoring, its estimand comprises 24 unique connectivity–confound–domain con-
trasts, with favorable support at 100% for Pearson and Spearman and 0% for partial correlation
and mutual information. This complete estimator partition, rather than the pooled 12-of-24 frac-
tion, is the informative result: NM-H2 is measure-dependent, and the mechanism underlying the
partition remains unresolved. (C) Marginal influence of each analytic choice on NM-H2. (D, E)
Cocaine-use-disorder episode: (D) multiverse stability of systemic-segregation associations across
36 specifications with SDMA-GLS consensus; (E) single-specification versus multiverse SDMA-GLS
maps for five network–outcome pairs. (F) Cross-cultural social cognition: culture-stratified ALE
maps contrasting Euro-American trust networks with East Asian social-cognition networks.

8

[2, 23] example assessed associations between brain connectivity and behavior; a 36-specification multiverse rejected all five pre-specified connectivity–behavior associations under same-dataset meta-analysis (SDMA-GLS) [35] (all Z < 1.24, false discovery rate [FDR] q > 0.58), and an exploratory screen over 70 combinations surfaced no FDR-surviving effect, so the system blocked it from confirmatory promotion and converted the null into a replication plan (Fig. 4D,E). In another test case that applied coordinate-based neuroimaging meta-analysis to a small cross-cultural neu- roscience literature, subgroup activation-likelihood estimation (ALE) on 21 studies [16, 18, 19, 47] produced a medial prefrontal cortex (mPFC)-topology interpretation, but the system blocked it as exploratory: the subgroups held only k = 6–8 entries (below the recommended k ≥17), paradigm composition was imbalanced, and centroid shifts alone cannot establish non-overlapping distri- butions. The case ended in a paradigm-matched follow-up with no settled claim (Fig. 4F). Full statistics are in Supplementary Methods S11.2.1 and Appendix J.

Across the three episodes, the multiverse exposed which findings were sensitive to analytic choices, while scientific review determined what each result could support. Prespecified review checks withheld confirmatory status from the SUDMEX exploratory screen and the underpowered cross-cultural ALE; in the post-hoc NeuroMark audit, a human reviewer identified the sign-blind scoring error.

Brain Researcher converts adaptive searches into frozen successor analyses in two self-evolving episodes

We next asked whether Brain Researcher could transform open-ended exploration into frozen, auditable successor analyses. We examined two extended research episodes that differed in what was searched. Using the Human connectome Project (HCP) data, Brain Researcher searched over candidate analysis workflows for a fixed question about connectivity-based prediction of behavioural variation. Using the TRIBE foundation model, it searched over candidate scientific questions about a model’s internal representations and then converted one question into a frozen test on newly sampled stimuli (Supplementary Methods S11.3).

In the HCP episode, we began with a published study with openly available code and shared analysis materials [37]. Brain Researcher allocated 116 candidate prediction-pipeline evaluations for Cognition, of which 104 returned scored results in the parent runs. Following a selector audit, the researcher designated a frozen selected workflow. In 10 repeated same-cohort nested-cross- validation splits, the frozen selected workflow achieved a higher pooled out-of-fold correlation than a matched local reconstruction of the published procedure (median ∆r = .098; conditional one-sided p = .006). When the frozen selected workflow was refit to four additional behavioural outcomes, it again produced higher correlations in 37 of 40 comparisons, giving the same direction in 47 of 50 comparisons across all five outcomes. Median out-of-sample R2 was positive only for two vari- ables (Cognition and Tobacco Use), and multiplicity-aware transfer inference remained inconclusive (Fig. 5; Supplementary Methods S11.3.1).

TRIBE v2 [14] is a tri-modal foundation model that predicts human fMRI responses from video, audio, and language inputs. We asked how natural-sound category geometry changes across its internal audio layers. Brain Researcher screened category contrasts without choosing one in advance and ranked them by changes in source-held-out discrimination (Fig. 6A). Tools–voice showed the largest change but varied across sound collections. Brain Researcher instead proposed speech–tools for follow-up because early layers strongly separated the categories, whereas later layers brought them closer while largely preserving the same representational direction. This contrast could also be tested prospectively using new recordings sampled from multiple collections and matched on seven prespecified acoustic measurements. The researcher approved this direction and froze the

9

B matched reference

A

frozen selected workflow

Highest discovery score

5×3 nested CV · 10 seeds

Initial 20-candidate best covariance + SVR  ·  r = .373

coherence + ridge

r = .487

r = .126 r = .242

0.5

Tobacco use

96-candidate expansion

higher in 10/10 seeds

precision + CPM

r = .386 precision + ridge r = .454

Mean cross-validated

Pearson r (Cognition)

0.4

r = .006 r = .075

Personality / emotion

matched evaluation frozen workflow r = .332

0.3

higher in 9/10 seeds

0.2

r = .008 r = .122

Illicit drug use

higher in 10/10 seeds

0.1

one completed connectivity–prediction pipeline

r = -.062 r = .001

0.0

Mental health

Did not complete (12)

higher in 8/10 seeds

1 20 40 60 80 100 116 Candidate evaluation order

−.05 0 .10 .20 Median cross-validated r


> **Figure 5: Brain Researcher searches 116 HCP prediction pipelines and identifies a**

> workflow that consistently exceeds a matched reference. A. Brain Researcher first evalu-
ated 20 candidate pipelines for Cognition prediction, reaching a best discovery score of r = .373.
Brain researcher then launched a 96-candidate expansion; 84 candidates returned scores and 12
ended in transport failure. Within the expanded episode, Brain Researcher adapted its proposals
to the accumulating results: 27 candidates exceeded the initial search maximum, and the highest
discovery score was r = .487, obtained with whole-band coherence and ridge regression. Following
a selector audit, the researcher froze a related coherence-based workflow for matched evaluation.
Across 10 repeated family-grouped 5×3 nested-cross-validation runs, this workflow achieved median
r = .332, compared with .235 for the matched reference (median ∆r = .098; conditional one-sided
p = .006), and was higher in all 10 runs. B. The same frozen selected workflow was then refit for
each of four additional behavioural outcomes without target-specific retuning. It produced a higher
median correlation for every outcome and exceeded the matched reference in 37 of 40 repeat-level
comparisons, giving 47 of 50 directional wins across all five outcomes.

10

hypothesis and analysis before the new stimuli were evaluated.

Brain Researcher then evaluated three successive, non-overlapping 48-item panels. The nor- malized speech–tools separation became smaller in later layers in 11 of 12 collection-by-panel com- parisons, and all three panels met the prespecified directional criterion. In most collections, later TRIBE layers preserved the representational direction separating speech from tools while bringing the categories closer together. The result was a direction-preserving contraction of speech–tools geometry. After the pattern recurred across all three panels, Brain Researcher extended the test to four previously unused sound collections. Three showed the same geometry, although the corrected collection-level test remained inconclusive (Holm-adjusted p = .396; Fig. 6B,C; Supplementary Methods S11.3.2).

Both episodes converted adaptive searches into frozen follow-up analyses. In separately initi- ated sessions without Brain Researcher, the same coding agent completed substantial analyses, but neither session generated and froze a follow-up study. Because these sessions were not matched con- trols, this contrast is descriptive and does not establish that Brain Researcher caused the transition from an initial result to a frozen follow-up (Supplementary Methods S11.3.3).


## Discussion

Our central contribution is to treat the unit of AI-assisted research as a governed research trajectory rather than a model output. The paired benchmarks tested whether models could reach relevant tools and evidence. The collaborator studies showed how multiverse analysis and explicit constraints change what can be claimed from a completed analysis. The HCP and TRIBE episodes went one step further: a result from one stage became an input to the next. Taken together, these evaluations support a view of scientific agents not as systems that generate a final answer, but as infrastructure that augments human judgments by keeping questions, decisions, evidence, and claim states connected as a project evolves.

This is the sense in which the research episodes were self-evolving. In HCP, Brain Researcher searched over candidate workflows for a fixed question; following a selector audit, the researcher designated the frozen selected workflow and carried it into a matched comparison and four additional behavioural outcomes. In TRIBE, Brain Researcher did not simply promote the contrast with the largest change. It set aside an unstable lead, proposed a more coherent speech–tools question and, after the researcher froze it, carried that question into newly sampled panels. In both cases, intermediate evidence changed the next analysis without rewriting the analysis already under test. The research trajectory evolved, but the evidentiary standard did not.

This trajectory-level view also changes the role of verification. Formal criteria can operate prospectively when they are specified in advance; multiverse analysis can show how a result depends on the enumerated defensible choices [7, 13, 36, 49, 51]; and judgments that resist formalization remain with the researcher (Supplementary Methods S6.1). Relative to systems evaluated primarily for task execution or output correctness [4, 5, 10, 11, 24, 27, 30, 52, 53], Brain Researcher makes the relationship among the estimator, comparison, evidence base, and claim part of the persistent research record. The NeuroMark example illustrates the limit of this formal layer: automated review missed sign-blind scoring, and a human reviewer found the error. Brain Researcher therefore makes formalizable conditions visible and auditable; it does not make expert inspection unnecessary.

Once decisions and claim states persist, qualified, negative, and failed results need not be termi- nal outputs. They can narrow the next question, retire an unproductive branch, or define a frozen successor analysis. This is the broader infrastructure implication of self-evolving research: progress can accumulate across successive episodes instead of restarting from an unstructured prompt each

11

A  Open discovery and exploratory selection

Tools–Voice · ranked #1

1.0

2

Tools–Voice

Music–Speech

0.5

Speech–Tools

0.0

Animal–Speech

3 4

Late directional alignment, C

Speech–Voice

-0.5

1

Animal–Music

-1.0

Music–Voice

Animal–Tools

3 4 Speech–Tools · adopted target

Nature–Speech

1.0

Music–Tools

2

Nature–Voice

0.5

Music–Nature

0.0

Nature–Tools

1

Animal–Nature

-0.5

Animal–Voice

-1.0

-0.4 -0.2 0.0 0.2 Change in category distinguishability

-1.0 -0.5 0.0 Normalized separation change, ΔS

(late − early)

B  Prospective new-item geometry

STARSS23 C  Four-new-collection extension

1.0

1.0

PANEL MEANS

DCASE

-0.694

Set 1

4/4

SINGA:PURA

Late directional alignment, C

0.5

0.5

-0.447

SMALLER SEPARATION · SAME DIRECTION

SMALLER SEPARATION · SAME DIRECTION

0.0

0.0

Set 2

4/4

AudioSet BBC

FreeSound SoundBible

-0.547

-0.5

-0.5

SONYC-UST

Set 3

3/4

Set 1 Set 2 Set 3

-1.0

-1.0

-1.0 -0.5 0.0 Normalized separation change, ΔS

-1.0 -0.5 0.0 Mean separation change, ΔS

-1.0 -0.5 0.0 Normalized separation change, ΔS


> **Figure 6: Brain Researcher turns an open question about TRIBE into successive tests**

> with new sounds and collections. A. Brain Researcher began by asking how TRIBE changes
natural-sound representations from early to late layers. It screened category contrasts by their
change in held-out distinguishability (AUC), without choosing a target in advance. Tools–voice
changed most, but the pattern varied across collections. Rather than simply following the top-
ranked result, Brain Researcher identified speech–tools as a clearer lead: the categories moved closer
in later layers while usually keeping the same representational direction. The contrast could also be
retested with new, acoustically matched sounds from several collections. The researcher approved
this direction and froze the prediction and analysis. B. Brain Researcher then evaluated three
non-overlapping 48-item panels. All three showed a smaller speech–tools separation on average in
later layers. In 11 of 12 collection-by-panel comparisons, the categories became less separated while
retaining the prespecified direction. C. After the pattern recurred across all three panels, Brain
Researcher extended the test to four previously unused sound collections. Three of four showed
the same geometry, and the late-layer separation was again smaller on average (∆S = −0.198). In
all geometry plots, horizontal position shows the late-minus-early change in normalized separation
(∆S), and vertical position shows late directional alignment (C); the upper-left quadrant therefore
marks smaller separation with retained direction. A uses fold-specific references, whereas B and C
use the frozen speech–tools reference.

12

time. The mechanism is not unconstrained model autonomy, but the combination of an adap- tive trajectory with researcher-defined scope, explicit evidence standards, and durable records of what was tried and why it changed. Researchers retain authority to define the action space, select and freeze successor questions, interpret the evidence, and decide whether the trajectory should continue.

This work has several important limitations (Supplementary Methods S12). Brain Researcher produces auditable evidence but leaves interpretation and writing to the researcher. Its foundation- model and retrieval priors reflect the literature, datasets, and instrumented tools, which may favor well-represented, operationalized questions over negative results, low-resource populations, and unusual paradigms [28]. Several episodes rely primarily on same-dataset multiverse or internal validation; these improve auditability but do not replace independent replication or constitute ex- ternal confirmation [8, 38]. Several of these datasets are public (HCP, OpenNeuro), so a frontier model may have encountered the associated published findings during training; we cannot rule out memorization, which is a further reason not to treat these results as novel detections. Evidence grounding was scored by condition-blind LLM judges (three frontier models that are also among the seven evaluated, a potential source of self-preference). A reproducible human audit of 20% of scored results (272 of roughly 1,360 items) agreed with 96% of verdicts (Cohen’s κ = 0.94); dis- crepancies were one-step severity differences, never reversals between supported and unsupported, and the judges erred strictly (Supplementary Methods S11.1.3). Runtime and researcher effort were not measured. Review-layer error was estimated against a 60-case calibration library (16 invalid, 5 valid controls, 39 warn), which produced no false-accepts (0 of 16; rule-of-three 95% upper bound 19%) and no false-blocks (0 of 5, a loose bound); this library was assembled after the sign-direction check identified through the NeuroMark case and is not an independent, field-scale estimate (Appendix G; Supplementary Methods S11.3.4). The calibration therefore measures in- ternal consistency on canonical scenarios, not how often flawed claims escape review in deployed research workflows. Independent replication and field-scale adjudication remain separate tests of scientific validity, which will require labeled real analyses. Finally, claim records are exportable files, but their value as shared, contestable infrastructure across laboratories remains a future objective. AI assistance should make the conditions under which results become reproducible knowledge easier to see, test, and share.

Online Methods

Detailed methods, including the runtime stack, the BR-KG substrate and sources, the operation registry, execution backends, benchmark scoring contracts, multiverse and validation-gated search protocols, and all per-case statistics, are provided in the Supplementary Information (Supple- mentary Methods S1–S12; Appendices A–K, with the per-case episode reports and the item-level benchmark audit sheet released as extended-data Appendices L and M; Supplementary Figures).

Supplementary information

Supplementary Information accompanies this manuscript.

Funding

JAR is supported by Stanford University Knight-Hennessy Scholars Program, National Academies of Sciences, Engineering, and Medicine’s Ford Foundation Predoctoral Fellowship, Institute of International Education Quad Fellowship, the National Science Foundation’s Graduate Research

13

Fellowship Program, the Center for Mind, Brain, Computation and Technology, and the Wu Tsai Neurosciences Institute. V.D.C. received support from NSF 2112455 and NIH R01MH123610. A.d.l.V., R.P. and J.K. were supported by the National Institute of Mental Health under award R01MH096906. Z.C. and R.P. received cloud-computing credits through the 2025 HAI-Google Cloud Credits Grant Program to support Brain Researcher API development and computation.

Competing interests

S.K. reports part-time employment with Meta, which began recently and after most of the work reported here. The other authors declare no competing interests.

Ethics, consent and materials availability

Not applicable: this work analyzed only previously collected, publicly available or collaborator- provided de-identified neuroimaging data under their original ethics approvals and consents, and generated no new human- or animal-subjects data or materials.

Data availability

BR-KG is archived at Zenodo (https://doi.org/10.5281/zenodo.21966011) and linked from the public project site (https://brain-researcher.com/). The release includes graph snapshots, node and edge schemas, provenance fields, registry links, benchmark manifests, scoring tables, ag- gregate outputs, figure source data, run-bundle schemas, a worked auditable claim-record example (an exported claim card with its evidence verdicts, on public Neurosynth data), and deployment notes. Users can access the public MCP interface and released Brain Researcher skills from the project site, which describes how users can suggest additions or corrections to BR-KG. Source neuroimaging datasets remain under their original terms: public resources are cited and linked in Supplementary Methods S4 and Appendix C, and controlled-access, collaborator-provided, or license-restricted human-subject data are not redistributed. Artifact and provenance records are described in Supplementary Methods S7.4 and Appendix F; benchmark records in Supplementary Methods S11.1 and Appendix J. To keep the Supplementary Information self-contained, the full au- dit ledgers it condenses are released in the same archival repository as an extended-data package: the complete BR-KG, evidence-bundle, dataset, tool-registry, constraint, execution–provenance, and memory data cards (Appendices A–F and H), the full per-rule review registry (Appendix G9.1–G9.4 and G9.6), the automatically generated per-case episode reports (Appendix L), the cur- rent HCP and TRIBE research-line reports and their supporting run bundles, and the item-level benchmark human-audit sheet (Appendix M); a crosswalk maps each condensed Supplementary section to its archived file.

Code availability

The Brain Researcher system (Python package, CLI, agent runtime, MCP server with versioned tool contracts, orchestrator, web UI, and deployment recipes) is available under the MIT license at https://github.com/brain-researcher/brain-researcher-public, with the companion agent layer (skills, agent templates, MCP adapters, and AutoResearch evaluation rubrics) at https: //github.com/brain-researcher/brain-researcher-agent-kit; both are linked from the project site (https://brain-researcher.com/), and the v0.3.0 release is archived at Zenodo (https://doi.org/10.5281/zenodo.21966011). Analysis code and per-specification outputs for the NeuroMark collaborator case are available at https://github.com/XinhuiLi/BR-NeuroMark.

14

Author contributions

Z.C. and R.P. initiated and conceived the project. Z.C. designed and implemented the Brain Re- searcher system, ran the experiments and analyses, generated the main results, and drafted the manuscript. R.P. supervised the project and contributed to conceptual framing, study design, hands-on system testing, evaluation feedback, interpretation, and manuscript revision. J.H.Z. provided early supervision and initial computational resources for the project. N.L. gathered background information, including dataset lists and literature-review materials, helped design the benchmark questions, evaluated system outputs, and tested performance for the quantitative bench- mark section. X.L. and V.D.C. designed and ran the NeuroMark schizophrenia functional-network- connectivity case. J.R. and R.P. designed and ran the cocaine-use-disorder connectivity case. H.W. designed and ran the cross-cultural social cognition case. C.K., J.K., and A.d.l.V. provided feedback on knowledge-graph design and contributed data and design requirements for the knowledge-graph and source-integration components. S.B. provided feedback on agent design, MCP infrastructure, backend integration, and execution design. J.M. provided feedback on the scientific-review layer. S.D. contributed suggestions and ideas on the agent harness and validation-gated research design, including the bounded-validation framing; S.K. provided feedback on the agent harness. C.J. con- tributed to system testing. J.W.B. provided feedback on the manuscript. All authors reviewed and approved the manuscript.


## References

[1] Alibaba Cloud. Qwen3.6-Plus: Towards real world agents, 2026. URL https://www.alibab

acloud.com/blog/603005. Accessed 21 May 2026.

[2] Diego Angeles-Valdez, Jalil Rasgado-Toledo, Victor Issa-Garcia, Thania Balducci, Viviana

Villica˜na, Alely Valencia, Jorge Julio Gonzalez-Olvera, Ernesto Reyes-Zamorano, Eduardo A. Garza-Villarreal, et al. The Mexican magnetic resonance imaging dataset of patients with cocaine use disorder: SUDMEX CONN. Scientific Data, 9(1):133, 2022. doi: 10.1038/s41597 -022-01251-3.

[3] Anthropic. Introducing Claude Opus 4.8, 2026. URL https://www.anthropic.com/news/c

laude-opus-4-8. Accessed 5 June 2026.

[4] Anthropic. Claude Science, an AI workbench for scientists, is now available. https://ww

w.anthropic.com/news/claude-science-ai-workbench, June 2026. Anthropic news announcement, 30 June 2026.

[5] D. A. Boiko, R. MacKnight, B. Kline, and G. Gomes. Autonomous chemical research with

large language models. Nature, 624:570–578, 2023. doi: 10.1038/s41586-023-06792-0. URL https://doi.org/10.1038/s41586-023-06792-0.

[6] R. Botvinik-Nezer, F. Holzmeister, C. F. Camerer, et al. Variability in the analysis of a single

neuroimaging dataset by many teams. Nature, 582:84–88, 2020. doi: 10.1038/s41586-020-231 4-9. URL https://doi.org/10.1038/s41586-020-2314-9.

[7] M. Burkhardt and C. Giessing. The Comet Toolbox: Improving robustness in network neu-

roscience through multiverse analysis. Imaging Neuroscience, 4:IMAG.a.1122, 2026. doi: 10.1162/IMAG.a.1122. URL https://doi.org/10.1162/IMAG.a.1122.

15

[8] K. S. Button, J. P. A. Ioannidis, C. Mokrysz, B. A. Nosek, J. Flint, E. S. J. Robinson, and

M. R. Munafo. Power failure: Why small sample size undermines the reliability of neuroscience. Nature Reviews Neuroscience, 14:365–376, 2013. doi: 10.1038/nrn3475. URL https://doi. org/10.1038/nrn3475.

[9] J. Carp. The secret lives of experiments: Methods reporting in the fMRI literature. Neu-

roImage, 63(1):289–300, 2012. doi: 10.1016/j.neuroimage.2012.07.004. URL https: //doi.org/10.1016/j.neuroimage.2012.07.004.

[10] Jun Shern Chan, Neil Chowdhury, Oliver Jaffe, James Aung, Dane Sherburn, Evan Mays,

Giulio Starace, et al. MLE-bench: Evaluating machine learning agents on machine learning engineering, 2024. URL https://doi.org/10.48550/arXiv.2410.07095. Publication Title: arXiv.

[11] Ziru Chen, Shijie Chen, Yuting Ning, Qianheng Zhang, Boshi Wang, Botao Yu, Yifei Li,

et al. ScienceAgentBench: Toward rigorous assessment of language agents for data-driven scientific discovery, 2025. URL https://doi.org/10.48550/arXiv.2410.05080. ICLR 2025; Publication Title: arXiv.

[12] BIDS Community. BIDS Stats Models Specification, 2024. URL https://bids-standard.

github.io/stats-models/.

[13] J. Dafflon, P. F. Costa, F. Vasa, et al. A guided multiverse study of neuroimaging analyses.

Nature Communications, 13:3758, 2022. doi: 10.1038/s41467-022-31347-8. URL https: //doi.org/10.1038/s41467-022-31347-8.

[14] Stephane d’Ascoli, Jeremy Rapin, Yohann Benchetrit, Teon Brooks, Katelyn Begany,

Josephine Raugel, Hubert Banville, and Jean-Remi King. A foundation model of vision, audi- tion, and language for in-silico neuroscience, 2026. URL https://doi.org/10.48550/arXiv .2605.04326. Publication Title: arXiv.

[15] DeepSeek. DeepSeek V4 preview release, 2026. URL https://api-docs.deepseek.com/new

s/news260424. Accessed 21 May 2026.

[16] J. Dockes, R. A. Poldrack, R. Primet, H. Gozukan, T. Yarkoni, F. Suchanek, B. Thirion, and

G. Varoquaux. NeuroQuery, comprehensive meta-analysis of human brain mapping. eLife, 9: e53385, 2020. doi: 10.7554/eLife.53385. URL https://doi.org/10.7554/eLife.53385.

[17] Yuhui Du, Zening Fu, Jing Sui, Shuang Gao, Ying Xing, Dongdong Lin, Mustafa Salman,

Anees Abrol, Md Abdur Rahaman, Jiayu Chen, L. Elliot Hong, Peter Kochunov, Elizabeth A. Osuch, and Vince D. Calhoun. NeuroMark: An automated and adaptive ICA-based pipeline to identify reproducible fMRI markers of brain disorders. NeuroImage: Clinical, 28:102375, 2020. doi: 10.1016/j.nicl.2020.102375.

[18] S. B. Eickhoff, A. R. Laird, C. Grefkes, L. E. Wang, K. Zilles, and P. T. Fox. Coordinate-

based activation likelihood estimation meta-analysis of neuroimaging data: A random-effects approach based on empirical estimates of spatial uncertainty. Human Brain Mapping, 30(9): 2907–2926, 2009. doi: 10.1002/hbm.20718. URL https://doi.org/10.1002/hbm.20718.

[19] S. B. Eickhoff, T. E. Nichols, A. R. Laird, et al. Behavior, sensitivity, and power of activation

likelihood estimation characterized by massive empirical simulation. NeuroImage, 137:70–85, 2016. doi: 10.1016/j.neuroimage.2016.04.072. URL https://doi.org/10.1016/j.neuroima ge.2016.04.072.

16

[20] A. Eklund, T. E. Nichols, and H. Knutsson. Cluster failure: Why fMRI inferences for spatial

extent have inflated false-positive rates. Proceedings of the National Academy of Sciences, 113 (28):7900–7905, 2016. doi: 10.1073/pnas.1602413113. URL https://doi.org/10.1073/pnas .1602413113.

[21] O. Esteban, C. J. Markiewicz, R. W. Blair, et al. fMRIPrep: A robust preprocessing pipeline

for functional MRI. Nature Methods, 16:111–116, 2019. doi: 10.1038/s41592-018-0235-4. URL https://doi.org/10.1038/s41592-018-0235-4.

[22] Leo Gao, John Schulman, and Jacob Hilton. Scaling laws for reward model overoptimiza-

tion. In Proceedings of the 40th International Conference on Machine Learning, volume 202 of Proceedings of Machine Learning Research, pages 10835–10866. PMLR, 2023. URL https://proceedings.mlr.press/v202/gao23h.html.

[23] Eduardo A. Garza-Villarreal, Jorge Julio Gonzalez Olvera, Thania Balducci, Diego Ange-

les Valdez, Alely Valencia, and Jalil Rasgado. SUDMEX CONN: The Mexican dataset of cocaine use disorder patients. OpenNeuro dataset, 2026. URL https://doi.org/10.18112 /openneuro.ds003346.v1.1.3.

[24] Ali Essam Ghareeb, Benjamin Chang, Ludovico Mitchener, Angela Yiu, Caralyn J. Szostkiewicz, Dmytro Shved, Gavin J. Gyimesi, Jon M. Laurent, Samantha M. Wright, Muhammed T. Razzak, Andrew D. White, Silvia C. Finnemann, Michaela M. Hinks, and Samuel G. Rodriques. A multi-agent system for automating scientific discovery. Nature, 2026. doi: 10.1038/s41586-026-10652-y. URL https://www.nature.com/articles/s41586-026-1 0652-y.

[25] Google DeepMind. Gemini 3.1 Pro: Model card, 2026. URL https://deepmind.google/mo

dels/model-cards/gemini-3-1-pro/. Accessed 21 May 2026.

[26] K. Gorgolewski, C. D. Burns, C. Madison, D. Clark, Y. O. Halchenko, M. L. Waskom, and S. S.

Ghosh. Nipype: A flexible, lightweight and extensible neuroimaging data processing framework in Python. Frontiers in Neuroinformatics, 5:13, 2011. doi: 10.3389/fninf.2011.00013. URL https://doi.org/10.3389/fninf.2011.00013.

[27] Juraj Gottweis, Wei-Hung Weng, Alexander Daryin, Tao Tu, Petar Sirkovic, Artiom

Myaskovsky, Grzegorz Glowaty, Felix Weissenberger, Alessio Orlandi, Dan Popovici, Anil Palepu, Keran Rong, Ryutaro Tanno, Khaled Saab, Fan Zhang, Jacob Blum, Andrew Car- roll, Kavita Kulkarni, Nenad Tomaˇsev, Dina Zverinski, Ivor Rendulic, Elahe Vedadi, Florian Hasler, Luka Rimanic, Marina Boia, Ivan Budiselic, Ben Feinstein, Mathias Bellaiche, Tom Sheffer, Jan Freyberg, Jeremy Ratcliff, Ottavia Bertolli, Katherine Chou, Avinatan Hassidim, Burak Gokturk, Amin Vahdat, Yuan Guan, Vikram Dhillon, Eeshit Dhaval Vaishnav, Byron Lee, Tiago R. D. Costa, Jos´e R. Penad´es, Gary Peltz, Yossi Matias, James Manyika, Demis Hassabis, Yunhan Xu, Pushmeet Kohli, Annalisa Pawlosky, Alan Karthikesalingam, and Vivek Natarajan. Accelerating scientific discovery with Co-Scientist. Nature, 2026. doi: 10.1038/s4 1586-026-10644-y. URL https://www.nature.com/articles/s41586-026-10644-y.

[28] Q. Hao, F. Xu, Y. Li, et al. Artificial intelligence tools expand scientists’ impact but contract

science’s focus. Nature, 649:1237–1243, 2026. doi: 10.1038/s41586-025-09922-y. URL https://doi.org/10.1038/s41586-025-09922-y.

[29] Alif Al Hasan and Sumon Biswas. What breaks when LLMs code? characterizing operational

safety failures of agentic code assistants, 2026. URL https://arxiv.org/abs/2605.30777.

17

[30] K. Huang, S. Zhang, H. Wang, Y. Qu, Y. Lu, Y. Roohani, et al. Biomni: A general-purpose

biomedical AI agent, 2025. URL https://doi.org/10.1101/2025.05.30.656746. Publica- tion Title: bioRxiv.

[31] A. Iraji, Z. Fu, A. Faghiri, M. Duda, J. Chen, S. Rachakonda, T. DeRamus, P. Kochunov,

B. M. Adhikari, A. Belger, J. M. Ford, D. H. Mathalon, G. D. Pearlson, S. G. Potkin, A. Preda, J. A. Turner, T. G. M. van Erp, J. R. Bustillo, K. Yang, K. Ishizuka, A. Faria, A. Sawa, K. Hutchison, E. A. Osuch, J. Theberge, C. Abbott, B. A. Mueller, D. Zhi, C. Zhuo, S. Liu, Y. Xu, M. Salman, J. Liu, Y. Du, J. Sui, T. Adali, and V. D. Calhoun. Identifying canonical and replicable multi-scale intrinsic connectivity networks in 100k+ resting-state fmri datasets. Human Brain Mapping, 44(17):5729–5748, 2023. doi: https://doi.org/10.1002/hbm.26472. URL https://onlinelibrary.wiley.com/doi/abs/10.1002/hbm.26472.

[32] Leslie K. John, George Loewenstein, and Drazen Prelec. Measuring the prevalence of question-

able research practices with incentives for truth telling. Psychological Science, 23(5):524–532, 2012. doi: 10.1177/0956797611430953.

[33] Jean Kaddour, Srijan Patel, Gb`etondji Dovonon, Leo Richter, Pasquale Minervini, and Matt J.

Kusner. Agentic uncertainty reveals agentic overconfidence, 2026. URL https://arxiv.org/ abs/2602.06948.

[34] David B. Keator, Theo G.M. van Erp, Jessica A. Turner, Gary H. Glover, Bryon A. Mueller,

Thomas T. Liu, James T. Voyvodic, Jerod Rasmussen, Vince D. Calhoun, Hyo Jong Lee, Arthur W. Toga, Sarah McEwen, Judith M. Ford, Daniel H. Mathalon, Michele Diaz, Daniel S. O’Leary, H. Jeremy Bockholt, Syam Gadde, Adrian Preda, Cynthia G. Wible, Hal S. Stern, Aysenil Belger, Gregory McCarthy, Burak Ozyurt, and Steven G. Potkin. The function biomedical informatics research network data repository. NeuroImage, 124: 1074–1079, 2016. ISSN 1053-8119. doi: 10.1016/j.neuroimage.2015.09.003. URL https://www.sciencedirect.com/science/article/pii/S1053811915007995.

[35] J. Lefort-Besnard, T. E. Nichols, and C. Maumet. Statistical inference for neuroimaging multiverse analyses with the same-data meta-analysis. Imaging Neuroscience, 2025. doi: 10.1162/imag a 00513. URL https://doi.org/10.1162/imag_a_00513.

[36] Xinhui Li, Nathalia Bianchini Esper, Lei Ai, Steve Giavasis, Hecheng Jin, Eric Feczko, Ting Xu,

et al. Moving beyond processing- and analysis-related variation in resting-state functional brain imaging. Nature Human Behaviour, 8:2003–2017, 2024. doi: 10.1038/s41562-024-01942-4. URL https://doi.org/10.1038/s41562-024-01942-4.

[37] Zhen-Qi Liu, Andrea I. Luppi, Justine Y. Hansen, Ye Ella Tian, Andrew Zalesky, B. T. Thomas

Yeo, Ben D. Fulcher, and Bratislav Misic. Benchmarking methods for mapping functional connectivity in the brain. Nature Methods, 22(7):1593–1602, 2025. doi: 10.1038/s41592-025-0 2704-4. URL https://doi.org/10.1038/s41592-025-02704-4.

[38] S. Marek, B. Tervo-Clemmens, F. J. Calabro, et al. Reproducible brain-wide association studies

require thousands of individuals. Nature, 603:654–660, 2022. doi: 10.1038/s41586-022-04492-9. URL https://doi.org/10.1038/s41586-022-04492-9.

[39] C. J. Markiewicz, K. J. Gorgolewski, F. Feingold, et al. The OpenNeuro resource for sharing

of neuroscience data. eLife, 10:e71774, 2021. doi: 10.7554/eLife.71774. URL https: //doi.org/10.7554/eLife.71774.

18

[40] Christopher J. Markiewicz, Alejandro De La Vega, Adina Wagner, Yaroslav O. Halchenko,

Karolina Finc, Rastko Ciric, Mathias Goncalves, Dylan M. Nielson, James D. Kent, John A. Lee, Shashank Bansal, Russell A. Poldrack, and Krzysztof J. Gorgolewski. poldracklab/fitlins: 0.11.0. Zenodo, 2022. URL https://doi.org/10.5281/zenodo.7217447. Version 0.11.0.

[41] L. Mitchener, A. Yiu, B. Chang, et al. Kosmos: An AI Scientist for Autonomous Discovery,

2025. URL https://doi.org/10.48550/arXiv.2511.02824. Publication Title: arXiv.

[42] Moonshot AI. Kimi K2.5, 2026. URL https://platform.kimi.ai/docs/guide/kimi-k2-5

-quickstart. Accessed 21 May 2026.

[43] OpenAI. Introducing GPT-5.5, 2026. URL https://openai.com/index/introducing-gpt

-5-5/. Accessed 21 May 2026.

[44] OpenNeuro. OpenNeuro Vocabulary (ONVOC). BioPortal, National Center for Biomedical

Ontology, 2026. URL https://bioportal.bioontology.org/ontologies/ONVOC. Accessed 2026.

[45] R. A. Poldrack, C. I. Baker, J. Durnez, et al. Scanning the horizon: Towards transparent

and reproducible neuroimaging research. Nature Reviews Neuroscience, 18:115–126, 2017. doi: 10.1038/nrn.2016.167. URL https://doi.org/10.1038/nrn.2016.167.

[46] R. A. Poldrack, C. J. Markiewicz, S. Appelhoff, et al. The past, present, and future of the

Brain Imaging Data Structure (BIDS). Imaging Neuroscience, 2:1–19, 2024. doi: 10.1162/im ag a 00103. URL https://doi.org/10.1162/imag_a_00103.

[47] T. Salo, T. Yarkoni, T. E. Nichols, J.-B. Poline, M. Bilgel, K. L. Bottenhorn, et al. NiMARE:

Neuroimaging Meta-Analysis Research Environment. Aperture Neuro, 3:1–32, 2023. doi: 10.5 2294/001c.87681. URL https://doi.org/10.52294/001c.87681.

[48] Joseph P. Simmons, Leif D. Nelson, and Uri Simonsohn. False-positive psychology: Undisclosed

flexibility in data collection and analysis allows presenting anything as significant. Psychological Science, 22(11):1359–1366, 2011. doi: 10.1177/0956797611417632.

[49] U. Simonsohn, J. P. Simmons, and L. D. Nelson. Specification curve analysis. Nature Human

Behaviour, 4:1208–1214, 2020. doi: 10.1038/s41562-020-0912-z. URL https://doi.org/10 .1038/s41562-020-0912-z.

[50] Joar Skalse, Nikolaus Howe, Dmitrii Krasheninnikov, and David Krueger. Defining and char-

acterizing reward gaming. In Advances in Neural Information Processing Systems, volume 35, pages 9460–9471, 2022. URL https://proceedings.neurips.cc/paper_files/paper/202 2/hash/3d719fee332caa23d5038b8a90e81796-Abstract-Conference.html.

[51] S. Steegen, F. Tuerlinckx, A. Gelman, and W. Vanpaemel. Increasing transparency through a

multiverse analysis. Perspectives on Psychological Science, 11(5):702–712, 2016. doi: 10.1177/ 1745691616658637. URL https://doi.org/10.1177/1745691616658637.

[52] K. Swanson, W. Wu, N. L. Bulaong, J. E. Pak, and J. Zou. The Virtual Lab of AI agents designs

new SARS-CoV-2 nanobodies. Nature, 646:716–723, 2025. doi: 10.1038/s41586-025-09442-9. URL https://doi.org/10.1038/s41586-025-09442-9.

19

[53] Cheng Wang, Zhibin He, Zhihao Peng, Shengyuan Liu, Yufan Hu, Carl Yang, Lifang He,

Lichao Sun, Xiang Li, and Yixuan Yuan. NeuroClaw Technical Report, 2026. URL https: //arxiv.org/abs/2604.24696. Publication Title: arXiv (2604.24696).

[54] Z.AI. GLM-5.1, 2026. URL https://docs.z.ai/guides/llm/glm-5.1. Accessed 21 May

2026.

20

Supplementary Information for “Bringing analytic rigor

to agentic AI for science: The Brain Researcher

platform for neuroimaging data analysis”

Zijiao Chen1, Nicholas Lu1, Xinhui Li2, Jocelyn A. Ricard1, Ce Ju3, Huan H. Wang1,

Christian Kindermann1, Jeanette A. Mumford1, Steven Dillmann1, James Kent4, Alejandro de la Vega4, Sanmi Koyejo1, Vince D. Calhoun2, Joshua W. Buckholtz1, Juan

Helen Zhou5, Steffen Bollmann1,6, Russell A. Poldrack1

Correspondence: russpold@stanford.edu

1Stanford University, Stanford, CA, USA 2Tri-institutional Center for Translational Research in Neuroimaging and Data Science (TReNDS), Georgia State University, Georgia Institute of Technology, Emory University, Atlanta, GA, USA

3Inria, CEA, Universit´e Paris-Saclay, Palaiseau, France 4The University of Texas at Austin, Austin, TX, USA 5National University of Singapore, Singapore 6The University of Queensland, Brisbane, QLD, Australia

Supplementary Methods

Organization of supplement

The Supplementary Methods follow the life cycle of a Brain Researcher episode. The main Methods define the conceptual machinery: what a research episode is, why MCP separates the language model from scientific infrastructure, how tools and datasets are selected, how execution is observed, and how claims are reviewed before memory writeback. This supplement makes that machinery reproducible by specifying the records, checks, gates, artifacts, and evaluation rules used during implementation.

The sections are organized in the order in which an episode runs. S1 defines the system boundary and MCP interface. S2 defines the episode object, state machine, and a running predictive-modeling example. S3 describes BR-KG, ONVOC normalization, and evidence assembly. S4 describes dataset and resource resolution. S5 defines the typed tool registry and action space. S6 defines the constraint compiler and commitment gate. S7 defines execution, preflight, and provenance. S8 defines the six terminal claim states used for the reported collaborator and bounded-autonomous evaluations and routes unresolved decisions for human escalation. S9 defines memory writeback, conflict detection, and BR-KG promotion. S10 defines bounded self-evolving episodes and Harbor-based validation. S11 defines the evaluation protocol. S12 states limitations and reporting boundaries. Appendix/Data Cards A–J contain concrete episode identifiers, snapshot identifiers, schema excerpts, run-bundle excerpts, review rules, claim cards, and evaluation ledgers. Appendix K presents a representative generated-code excerpt for a collaborator case; the full per-case reports for the three collaborator cases and two bounded self-evolving campaigns are released with the repository and described in Appendix L.

Public release and reuse

The public release includes BR-KG itself. It provides graph snapshots, node and edge schemas, ontology-normalization records, public evidence and provenance fields, registry links, and ex-

1

ample graph paths for the material described in S3 and Appendix B. The project site, https: //brain-researcher.com/, provides access to the public MCP interface, the released Brain Re-

searcher skills, and deployment notes: environment setup, graph loading, registry initialization, and example queries.

Source datasets are handled separately. Public resources are cited and linked, but not re- hosted unless their licenses permit redistribution. S4 and Appendices B and C record the datasets, derivatives, metadata, and access checks used by Brain Researcher. Controlled-access, collaborator- provided, or license-restricted human-subject data remain with the original data custodians or contributing groups.

The release includes the records needed to check the reported results without redistributing restricted raw data. S7 and Appendix F define the run-bundle schema, provenance fields, artifact manifests, logs, parameters, and observed outputs. Derived summaries, aggregate tables, figure source data, task manifests, scoring sheets, and run-bundle metadata are included in the public package.

S11 and Appendix J define the benchmark release: task manifests, model conditions, with-BR/ without-BR comparisons, scoring rules, metric denominators, exclusions, and aggregate outputs. Private paths, provider keys, human-subject identifiers, and license-restricted source material are excluded from the public release. Code-release details are tied to the registry and execution records: S5 describes the callable tool cards, S7 describes execution provenance, and Appendices D and F give the corresponding registry and artifact-manifest records.

We welcome community extensions to BR-KG. The public site explains how to propose new nodes, edges, evidence records, registry links, and deployment recipes. Contributions must include source provenance, license information, schema-valid records, and review status, so additions remain traceable as the graph grows.

2

Key operational terms

Term Meaning in this supplement Research episode Persistent runtime unit containing the question, evidence, selected plan, resources, constraints, execution artifacts, review verdicts, and memory status for one investigation. MCP operation Typed endpoint exposed by BR-MCP, for example tool discovery, dataset resolution, recipe generation, artifact inspection, or review. Registry specification Machine-readable record used for discovery, compatibility checking, parameter validation, and recipe generation. Workflow specification Planning-level description of a family of analyses and its expected inputs, outputs, constraints, and backend recipes. Executable wrapper Actual callable Python tool, command-line wrapper, Neurodesk module, container command, or scheduler script. Resource ledger Episode-specific record of datasets, derivatives, covariates, masks, target variables, fold manifests, and readiness status. Constraint compiler Component that converts method-condition records, tool-contract clauses, and validators into hard or soft checks. Run bundle Immutable provenance record containing event trace, trajectory document, observation record, analysis bundle, and run card. Scientific verification layer Acceptance gate that checks run bundles, artifacts, and candidate claims against validity rules before claim communication or mem- ory writeback. Review card Structured verification verdict, including rule triggers, risk tags, required fixes, and claim eligibility. Claim card Reviewed memory object derived from a run bundle; it stores a claim with scope, evidence level, caveats, and provenance pointers. Harbor verifier Task-level execution checker used in bounded autonomous episodes. It can verify files, schemas, tests, and required statistics, but it is not the scientific reviewer.

S1. System architecture and MCP interface

S1.1. Overall architecture

Brain Researcher is organized around a research episode rather than a single prompt-response exchange. Each episode enters through an MCP-compatible client or coding-agent harness [3, 28], is mediated by the Brain Researcher MCP control plane, and is grounded by domain backends. The outer layer receives the researcher’s goal, writes or runs code when needed, interacts with the user, and presents results. The middle layer, BR-MCP, exposes typed operations for each stage of the episode lifecycle: planning, discovery, execution, review, and memory writeback. The full operation surface is enumerated in S1.3. The inner layer consists of domain backends: BR-KG, dataset and BIDS resolvers [14, 24], the tool registry, execution backends, storage services, review-rule registries, memory stores, and governance records.

A typical predictive-modeling request traverses the layers as follows. The user asks whether a behavioral score can be predicted from a resolved neuroimaging feature matrix. The outer client converts the request into a typed intent: prediction, fMRI/connectivity features, target variable, covariates, and required folds. BR-MCP retrieves candidate datasets, workflows, and tool families from the registry and BR-KG. The resource resolver checks whether the feature matrix, target

3

Supplementary Figure S1: Detailed Brain Researcher system architecture. The architecture separates the researcher-facing coding-agent harness, the BR-MCP control plane, and the domain execution substrate. The episode flow runs from question intake and typed intent resolution through BR-KG and registry lookup, resource checks, constraint compilation, commitment, execution, review, and memory writeback. The control-plane boxes indicate where typed MCP operations expose admissible actions, while the backend boxes indicate where Python, container, Neurodesk, Slurm/HPC, storage, and provenance services produce environment-observed artifacts. Dataset readiness, tool admissibility, execution success, and claim eligibility are returned by typed system state; the language model interprets, requests, and explains those states.

4

vector, covariates, and fold manifest are reachable and authorized. If the resolver returns pass or warn, BR-MCP packages an execution recipe with expected artifacts; if it returns block, the plan returns to revision before execution. After execution, the scientific verification layer inspects the run bundle and candidate claims before memory writeback.

This separation is intentional. The language model may interpret a natural-language request, compare MCP-returned options, ask for recipes, and explain observed outputs. It cannot certify that a registry ID exists, override a resolver block, mark a run as successful without artifacts, or accept a scientific claim without a verification verdict. Tool availability, dataset readiness, policy permission, execution success, and claim eligibility are supplied by MCP, BR-KG, the registry, resolvers, execution backends, and the scientific verification layer.

S1.2. Model routing and reproducibility

Language-model routing affects generation and interpretation, not certification. Coding-oriented tasks such as script generation, debugging, and file manipulation may be routed to code-specialized models. Scientific planning, evidence interpretation, review, and claim calibration may be routed to analytical models. The run card records the task type, selected provider, prompt-template version, policy context, registry snapshot, BR-KG snapshot, and memory namespace.

Example run-card excerpt:

run_card:

episode_id: ep_hcp_predict_001 mode: benchmark model_route:

task_type: code_generation provider: fixed_provider_id prompt_template: planning_v3 fixed_snapshots:

registry: registry_2026_05_15 brkg: brkg_snapshot_2026_05_10 policy_context: benchmark_locked memory_namespace: benchmark_isolated

For reported evaluations, the full configuration is fixed before launch and recorded in the run card: model identity, prompt-template and run-card schema versions, registry and BR-KG snapshots, policy flags, execution roots, backend settings, and memory namespace. Provider fallback may be used during development, but benchmark, collaborator-case, and bounded autonomous claims are reported only from fixed model versions, fixed prompt templates, fixed registry snapshots, fixed BR-KG snapshots, and fixed evaluation partitions.


> **Table 1 lists the resolved model identifiers and the coding-agent surface used for each of the seven**

> agents in the paired benchmarks. All agents were driven through their coding-agent command-line
surfaces (not direct chat or completion APIs), so decoding parameters follow each surface’s defaults;
we did not override temperature for the agent rollouts. The benchmark runs reported here were
executed in May–June 2026 (the 60-task tool-routing condition was run on 2026-06-05). The three
evidence-support judges were run deterministically at temperature 0 with a fixed random seed (7).

S1.3. MCP operation surface and registry boundary

The MCP surface is the public control plane, not the complete neuroimaging software catalog. The checked implementation contains 87 decorated MCP operations and 3 decorated MCP resources. These operations span five functional families: discovery and resolution (tools, workflows, datasets, BR-KG, literature); planning and recipe generation; execution observability and artifact inspection;

5


> **Table 1: Resolved model identifiers and coding-agent surfaces for the seven benchmarked agents.**

Paper label Resolved model identifier Coding-agent surface Claude Opus 4.8 claude-opus-4-8 Claude Code (claude -p) Codex GPT-5.5 gpt-5.5 Codex CLI (codex exec) Gemini 3.1 Pro google/gemini-3.1-pro-preview OpenCode (opencode run) GLM-5.1 zai-coding-plan/glm-5.1 OpenCode (opencode run) DeepSeek-V4-Pro deepseek/deepseek-v4-pro OpenCode (opencode run) Kimi K2.5 opencode/kimi-k2.5 OpenCode (opencode run) Qwen3.6-Plus opencode/qwen3.6-plus OpenCode (opencode run)

grounding and scientific review; and memory access and report generation. Slurm/HPC scheduling is exposed as a separate operation family. The resources expose structured tools, datasets, and workflow lookups. Full capability-family tables, implementation evidence sources, compute-graph diagrams, safety-gate tables, and access-mode tables are reported in Appendices A, D, F, and I rather than repeated in the main Supplementary Methods.

The broader registry stores the objects MCP searches, validates, packages, and observes. The distinction is important because an MCP operation is not the same as a workflow specification, registry specification, or executable wrapper.

Object Example Used for MCP operation resolve dataset Ask the control plane whether a dataset and required assets are usable. MCP resource workflow lookup Retrieve structured workflow or dataset summaries. Workflow specification predictive modeling workflow Generate a plan and expected artifact list. Registry specification fsl randomise contract Validate parameters, compatibility, and backend requirements. Executable wrapper AFNI/FSL/Workbench com- mand wrapper [6, 16, 27]

Run a backend command through an approved execution substrate.

Inventory counts are reported once in S5.1 so that reader attention stays on the control boundary here.

S1.4. LLM/MCP decision boundary

The LLM/MCP boundary separates interpretation from certification.

6

Step LLM or outer client does

MCP/backends do Output

Intent Interprets the user request and proposes modalities, datasets, methods, and constraints.

Receives typed query argu- ments.

Typed planning query.

Discovery Asks for candidate datasets, tools, workflows, or evidence.

Searches BR-KG, registry, dataset catalog, and litera- ture connectors.

Ranked candidate cards.

Resolution Chooses among returned options.

Canonicalizes dataset/tool IDs and returns metadata, schemas, and readiness status.

Resolved resource/ tool record.

Feasibility Requests feasibility checks. Validates roots, permis- sions, assets, tool con- tracts, and active con- straints.

pass / warn / block verdicts.

Recipe Requests backend-specific instructions.

Packages Python, Neu- rodesk, container, or Slurm recipe with expected out- puts.

Execution recipe and artifact contract.

Execution Delegates computation to allowed backend or coding harness.

Produces logs, artifacts, metrics, and environment observations.

Run bundle.

Verification Proposes candidate claims or report language.

Checks artifacts, con- straints, scorecards, QC outputs, and claim scope.

Review card and memory eligibility.

The LLM may choose among MCP-returned options, but it cannot invent a registry ID, override a resolver block, bypass a policy gate, or promote a claim to accepted memory without a verification verdict.

S1.5. Orchestration, subagents, and policy gates

The orchestration service manages run creation, polling, cancellation, retry, progress tracking, streaming logs, event updates, and durable state. Generated artifacts are stored under run-specific roots with manifests and checksums. The implementation may use specialized subagents, but each has a bounded role.

7

Supplementary Figure S2: Human-agent authority boundary in Brain Researcher. The diagram separates researcher authority, language-model assistance, MCP-mediated system authority, and scientific verification across the episode lifecycle. Brain Researcher can search evidence, compare options, prepare recipes, observe execution, assemble review inputs, and record memory candidates. The researcher retains authority over question framing, admissible tradeoffs, commitment-gate approval, interpretation, authorship, and final claim language. System gates prevent the model from inventing registry identifiers, overriding resource blocks, accepting missing artifacts, or promoting claims without a review verdict.

8

Component Input Output Boundary Critic Candidate plan, review find- ings, cycle record.

Cannot certify artifacts without run-bundle evidence. Recovery agent Failure logs, missing outputs, backend errors.

approve / revise / block / terminate.

Cannot erase the origi- nal failure record. Provenance tracker Decisions, tool calls, parame- ter bindings.

Retry or substitution proposal.

Records actions; does not judge scientific validity. Router Task type and policy con- text.

Event trace and trajec- tory entries.

Routing is recorded in the run card. Supervisor Open caveats, validation progress, budget.

Model/backend/subagent route.

Next branch proposal. Cannot expand beyond the declared design space.

Execution is controlled by allowed filesystem roots, network flags, dangerous-tool flags, direct- execution flags, timeout budgets, authentication checks, and approval phrases for pipeline execution. Heavy neuroimaging work is normally performed outside the MCP service by local Python, Neurodesk, a generic container runtime, Slurm/HPC, Kubernetes, AWS Batch, or another configured backend. Direct MCP execution exists only as a gated administrative path and is disabled by default in the evaluated configuration. Adaptive optimization surfaces such as contextual bandits, offline reinforcement learning, and drift detection are engineering surfaces only; they are not treated as evaluated capabilities unless explicitly declared in the evaluation card.

S2. Research episode runtime and run states

S2.1. Episode object and persisted state

The research episode is the core runtime unit. It persists the scientific question, planning state, evidence state, candidate alternatives, selected plan, selected tools, parameter bindings, resource- resolution results, execution outputs, QC artifacts, review verdicts, recovery attempts, limitation notes, and memory-writeback state. This prevents the system from treating later turns as isolated prompts: later decisions can depend on prior evidence, failed attempts, unresolved caveats, resource blockers, and review outcomes.

Episode record fields are grouped by role:

Group Fields Question state input question, normalized entities, scientific scope, intended output type. Resource state data requirements, candidate datasets, resolved resources, missing assets, access class. Planning state evidence bundle, candidate workflows, candidate tools, active con- straints, selected plan. Execution state backend recipe, expected artifacts, produced artifacts, logs, QC out- puts, recovery attempts. Review state review cards, rule findings, claim candidates, caveats, verdicts. Memory state memory eligibility, claim-card status, relation events, final comple- tion status.

Example episode-record excerpt:

9

episode_id: ep_hcp_predict_001 state: planning_blocked question_type: prediction selected_dataset: HCP-YA candidate_workflow: predictive_modeling required_assets:

- feature_matrix - target_variable - covariate_table - fold_manifest resource_verdict: block blocker: fold_manifest_missing next_action: resolve_asset_or_choose_alternative_workflow

S2.2. Scientific stages

At the scientific level, an episode moves through stages that each produce a concrete object.

Stage What happens Concrete output Question framing Natural-language goal is converted into typed scientific entities and admissible outputs.

Typed question record. Evidence assembly BR-KG, literature, dataset catalogues, tool reg- istries, and meta-analysis stores are queried.

Evidence bundle.

Option-set formation Candidate datasets, tools, workflows, and parame- terizations are identified.

Candidate ledger.

Constraint compilation Method-condition records and tool contracts are turned into active checks.

Active constraint set.

Commitment Human researcher, critic, or evaluation harness approves/revises/blocks the plan.

Commitment-gate record. Execution Approved recipe is run under the selected backend. Run bundle and arti- fact manifest. Verification Artifacts, logs, QC, scorecards, and candidate claims are checked.

Review card.

Claim card or no- write decision.

Memory writeback Accepted or qualified claims are stored with prove- nance; rejected claims remain in the run bundle.

S2.3. Running example: one predictive-modeling episode

The running example used throughout this supplement is an HCP-YA predictive-modeling replay [30, 34]. The question is whether a behavioral target can be predicted from Schaefer-100 x 7 features [26] using a fixed subject intersection. The resource card specifies N = 326, five Liu components [19], a pyspi statistic catalogue, feature matrices, candidate target variables, subject-intersection logic, missingness rules, and backend reachability. A valid run requires a feature matrix, target vector, covariates, and a fold manifest. During resolution, the dataset can pass dataset-level readiness while failing asset-level readiness if the fold manifest or target variable is missing. The constraint compiler then creates a hard fold-manifest check and soft warnings for confound specification or controversial preprocessing choices. If the fold manifest is absent, the commitment gate returns block before execution. If all required assets pass, BR-MCP packages a recipe and expected artifacts: predictions, scorecard, model metadata, fold manifest, and artifact manifest. Review then checks leakage, grouped cross-validation, permutation or null controls, robustness probes, and claim language. Only an accepted or explicitly qualified result can become a claim card.

10

S2.4. Runtime states, checkpointing, and recovery

Scientific stages are conceptual. Runtime states are the system state machine used to resume or audit the episode.

Runtime state Meaning initialization Create episode record, run root, policy context, and memory names- pace. planning Populate candidates, evidence, constraints, and recipe drafts. execution Dispatch or delegate computation. review Inspect artifacts, logs, QC outputs, scorecards, and claims. recovery Handle missing outputs, failed commands, invalid artifacts, or blocked constraints. completion Record accepted, qualified, or non-acceptance endpoint. blocked A known hard constraint or missing resource prevents valid progress. terminated Budget, user action, critic decision, or unrecovered infrastructure failure stops the episode.

A missing fold manifest is a blocked state: the reason is known and can be addressed by resolving the asset or changing workflow. Budget exhaustion after repeated unresolved failures is a terminated state. Checkpoints store the current state, selected candidates, active constraints, resource-resolution outputs, branch history, and run-bundle pointers. Recovery attempts are appended rather than overwritten, so a repaired run still preserves the original failure and repair path.

S3. BR-KG construction, ONVOC normalization, and evidence assembly

S3.1. BR-KG role and snapshot metadata

BR-KG is a Neo4j knowledge graph that links scientific records (publications, activation coordinates, statistical maps), cognitive structure (tasks, concepts, brain regions), resources (datasets, tools), embeddings, and operational records (review verdicts, governance entries, run objects). Its role is retrieval and provenance-aware traversal, not scientific proof. It provides source linking, coverage awareness, negative knowledge, method-condition records, and graph paths that can be inspected by planners and reviewers.

In the checked release snapshot (2026-07-07), BR-KG contains 745,949 nodes and 2,461,469 relationships. The manuscript-facing schema defines 27 primary node labels and 34 primary rela- tionship types. Production snapshots may contain additional compatibility, migration, enrichment, operational, or retrieval labels (this snapshot carries 108 active node labels and 125 active rela- tionship types), so primary-schema counts and all-active-label counts are reported separately in the Appendix/Data Cards. Deployment metadata such as Neo4j 5.20.0 Community, one ready K3s BR-KG pod, 139 indexes, and 48 constraints is release-readiness metadata, not evidence for scientific correctness.

Example traversal role:

query: "N-back working memory activation" normalized_task: ONVOC:N_BACK linked_concepts:

- working_memory

11

retrieved_records:

- publications - task contrasts - activation coordinates - brain regions - method constraints used_by:

- evidence_bundle - planner - reviewer

S3.2. Source governance, ingestion, and validation

Graph ingestion separates accepted records from candidate records. Accepted records are source- backed objects such as publications, coordinates, maps, task records, dataset records, tool descriptors, anatomical regions, and curated method-condition records. Candidate records may come from automated extraction, KGGEN, GABRIEL, or real-time retrieval. They remain in candidate lanes until they pass schema validation, source marking, provenance recording, license/citation checks, and acceptance rules.

Record type Example Status before use as graph fact Accepted record Publication with DOI, source loader, snapshot date, and citation.

Usable as graph evidence.

Candidate record Extracted task-region relation from KGGEN.

Candidate only until vali- dated and accepted. Held or rejected record Unsupported generated relation or source-incomplete extraction.

Not promoted to graph fact.

Each releasable source row records snapshot date, source URL, license, required citation, loader path, loader version, command line, configuration hash, input artifact path, output manifest, artifact path, and release disposition. Source aliases are normalized, source-like missing values are backfilled or removed, and source-specific licenses and citations are pinned before manuscript claims are made.

Manual record-quality audit. We manually reviewed 400 randomly sampled BR-KG records: 200 nodes and 200 directed edges. We classified 280 as correct, 45 as incomplete or uncertain, 53 as pre-existing source-integration errors, and 22 as BR-side errors. The three non-correct categories comprised:

• Incomplete or uncertain (n = 45): coordinate-space metadata was incomplete for 23 map nodes: 14 FitLins statistical maps had a known template but stored space=unknown; five Neu- roVault maps lacked a materialized canonical space despite GenericMNI target-template metadata; and four additional NeuroVault maps did not canonicalize target template image=GenericMNI into the KG space field. Available evidence was insufficient to assess 21 records: nine HAS COORDINATE edges had an unresolved source coordinate frame; seven Neurosynth coor- dinate nodes had source metadata marked UNKNOWN while the loader assigned MNI; three EvidenceSpan nodes had insufficient frozen content and live-source snapshot drift; and two GABRIEL MeasurementRun nodes lacked a matching fixed upstream run record. One Neurobagel Dataset node had a name containing an unresolved literal backslash-n formatting artifact.

• Pre-existing source-integration errors (n = 53): 37 Neurosynth records in which TAL coordinates were materialized as MNI, and 16 NeuroStore records in which StudyObjective

12

was materialized in publication or collection title fields. These failures arose in pre-existing source-specific integration paths and do not imply that the raw Neurosynth or NeuroStore records were incorrect.

• BR-side errors (n = 22): five NiCLIP index-offset errors; five dataset-to-contrast crosswalk over-propagations; three configuration-derived target mismatches; five GABRIEL/BR claim, evi- dence, or cohort-extraction errors; one unsupported manual contrast mapping; two tool/package registry default errors; and one mixed duplicate-DOI/BR merge error.

We are extending this audit into a systematic review across the full BR-KG and will iteratively repair and re-audit the ingestion and normalization issues it identifies; the counts above describe the audited snapshot rather than a completed post-remediation release.

S3.3. Entity resolution, relationship strength, and semantic linking

Entities are reconciled through exact identifiers, multi-attribute matching, fuzzy string matching, embedding-based alignment, and curated aliases. Matching is applied across publications, datasets, regions, concepts, paradigms, institutions, and researchers. Matched records are linked with deduplication edges that retain matching method and confidence.

Example entity-resolution excerpt:

raw_labels:

- "N-back" - "WM_BACK" - "verbal working memory" resolved_task_family: N_BACK non_equivalent_fields:

- contrast_definition - modality - stimulus_type - population resolution_note: same task family, not interchangeable experimental objects

Relationship strength may combine literature count, coordinate evidence, spatial overlap, em- bedding similarity, spatial distance, and optional user feedback. These scores affect retrieval ranking and path prioritization only. They are not review acceptance criteria and cannot by themselves establish a scientific claim.

S3.4. ONVOC ontology-linker layer

ONVOC normalizes heterogeneous source vocabulary before graph traversal. Free-text task names, contrast labels, cognitive constructs, anatomical labels, dataset-specific aliases, and source-specific terms are mapped to typed ONVOC records. OnvocClass nodes represent normalized vocabulary classes; OntologyConcept nodes represent linked external or internal concepts; IN ONVOC edges connect graph entities to normalized vocabulary entries.

Example ONVOC output:

input_terms:

- "N-back" - "WM_BACK" - "verbal working memory" onvoc_task_family: N_BACK linked_concepts:

- working_memory linked_graph_nodes:

13

- CognitiveTask:N_BACK - CognitiveConcept:working_memory non_equivalent_fields:

- contrast - modality - coordinate_space - population

ONVOC may link terms to the same task family, but it does not collapse contrast definitions, modalities, populations, or coordinate systems. When direct higher-tier graph evidence is sparse, ONVOC still provides an entity-typing and literature-query backbone. The evidence bundle records whether a decision was supported by accepted graph evidence, validated batch extraction, candidate evidence, or real-time retrieval.

S3.5. Evidence aggregation and connector-failure reporting

Evidence assembly produces an evidence bundle for each episode. A single bundle may include BR-KG paths, literature results, dataset metadata, tool-registry hits, known failure modes, and review-checklist triggers. Connector failures are stored rather than silently discarded. Figure S3 shows how a recommendation’s validity conditions become applicability checks and then admissible plans, caveats, or blockers, so that it arrives with its limits attached.

Example evidence-bundle excerpt:

evidence_bundle:

input_query: "predict behavior from HCP-YA Schaefer-100 x 7 features" resolved_entities:

dataset: HCP-YA feature_space: Schaefer100x7 task_family: null graph_evidence:

tier: accepted_graph_records paths: [dataset_to_feature_record, method_to_constraint] real_time_retrieval:

tier: literature_gap_fill status: completed connector_failures:

- source: PubMed

reason: timeout downstream_effect: evidence_coverage_caveat tool_registry_hits:

- predictive_modeling_family method_condition_records:

- fold_manifest_required - leakage_standardization_inside_cv

A missing connector result is treated as reduced evidence coverage. It may trigger a caveat or reviewer warning, but it is not treated as evidence that no relevant literature or resource exists.

S3.6. Embedding lanes

Brain Researcher uses separate embedding lanes for different retrieval surfaces. Tool retrieval uses titles, descriptions, command names, and tags. Brain-text retrieval uses task, construct, region, and claim-memory text. BR-KG may also store source-specific embeddings as graph nodes or node properties for selected ingestion lanes. Lane name, model identity, vector dimension, input fields, usage surface, snapshot, and index state are recorded in Appendices B and D.

14

Supplementary Figure S3: Condition-tagged evidence for scoped planning. The workflow begins with an underspecified scientific request and expands it into entities, methods, datasets, assumptions, and validity conditions that can be checked before execution. BR-KG links literature evidence to those conditions with provenance, while resource and tool resolvers determine which conditions are satisfied, missing, controversial, or incompatible in the current episode. Applicability checks convert the resulting condition set into admissible plans, required sensitivity analyses, caveats, or blockers. The purpose is to expose methodological scope before a run is committed and before a positive or negative result can anchor the narrative.

15

Embedding similarity retrieves and ranks candidates. It cannot by itself support a scientific claim. The current system operates in text-only concept-matching and retrieval modes. Cross-modal alignment between fMRI activation patterns and ontology concepts is a planned extension and is not used in reported results.

S3.7. KG extension pipelines and views

Automated extension pipelines maintain BR-KG as a living graph. KGGEN processes full-text publications into typed candidate triples with provenance. GABRIEL converts qualitative domain corpora such as review articles, textbook descriptions, and clinical practice guidelines into schema- compliant quantitative or semi-structured records. On-the-fly retrieval fills query-time coverage gaps when graph evidence is sparse. In all channels, generated records remain candidate or comparison records until explicitly validated, source-marked, and accepted.

Focused task-family or disease-cohort views are subgraph projections over the same underlying records, not separate graphs. They may organize working memory, attention, executive function, language, perception, ADHD, MDD, schizophrenia, healthy aging, and related records for retrieval. View membership supports navigation; it does not change the acceptance status of a finding.

S3.8. BR-KG visual atlas and release snapshot.

The BR-KG snapshot used in this work is summarized in the Appendix/Data Cards. The atlas reports graph composition, dominant relationship families, schema topology, representative literature/ map/task paths, source coverage, and release-readiness checks. These figures are used to document the retrieval substrate available to Brain Researcher; they are not treated as evidence that any scientific claim is true. During an episode, BR-KG supports source-backed retrieval, task/construct normalization, dataset/tool linking, method-condition lookup, and provenance inspection. Detailed counts, figure panels, source-like values, orphan-node rates, edge-confidence coverage, and release blockers are reported in Appendix B rather than repeated in the main Supplementary Methods.

S4. Dataset and resource resolution

S4.1. Dataset-level and asset-level resolution

Dataset and resource resolution converts abstract dataset references into executable resources. Dataset-level resolution maps identifiers, aliases, catalogue entries, local paths, BIDS roots, derivative directories, remote URLs, access class, phenotype availability, license/governance notes, and backend reachability. Asset-level discovery locates the concrete files needed by a workflow: derivatives, covariate files, target files, masks, matrices, parcellations, connectivity matrices, score files, fold manifests, and QC outputs.

A dataset can be known, accessible, and BIDS-valid while still blocking a predictive workflow because the target variable, covariates, or fold manifest are missing. Resource resolution is therefore a precondition for plan commitment, not a background annotation.

Example resolver output:

resolver_output:

dataset_id: HCP-YA dataset_readiness: pass access_class: authorized_local_or_cached backend_reachable: true workflow: predictive_modeling

16

Supplementary Figure S4: BR-KG node-type composition. Node composition summarizes the object families present in the BR-KG snapshot used for retrieval, normalization, and planning support. The chart separates scientific entities such as publications, coordinates, statistical maps, tasks, contrasts, concepts, and brain regions from resource and workflow entities such as datasets, tools, methods, governance records, and prior reviewed claims. Large node families indicate coverage available for traversal and grounding, not evidentiary weight for any individual claim. Detailed counts, release metadata, and source-quality checks are reported in Appendix B.

17

Supplementary Figure S5: BR-KG relationship-type composition. Relationship composition summarizes the edge families that connect publications, coordinates, maps, tasks, contrasts, concepts, regions, datasets, tools, constraints, and provenance records in the BR-KG snapshot. High-count relationship classes define the main traversal surfaces used for evidence assembly, task-to-construct normalization, map lookup, dataset discovery, and tool compatibility checks. Edge frequencies document graph structure and retrieval affordances; support strength for a scientific claim requires source provenance and review context. Appendix B provides the expanded relationship inventory and release-readiness checks.

18

Supplementary Figure S6: BR-KG schema topology and provenance flow. The atlas view summarizes how major node classes are connected, which relationship-label pairs dominate the schema, and how source records feed derived graph objects. Dense schema paths identify the routes most often available for structured retrieval, such as publication-to-coordinate-to-region, task-to- construct-to-map, and dataset-to-tool-to-workflow traversals. Provenance flow indicates where source systems, loaders, and curation records enter the graph. The figure documents the substrate available for multi-hop planning and evidence lookup; inferential claims require episode-level review.

19

Supplementary Figure S7: Representative BR-KG evidence and workflow paths. Example paths illustrate the kinds of traversals available during an episode. Literature peaks can be linked through coordinates, brain regions, task contrasts, and cognitive constructs; saved maps and NeuroVault assets can be linked to provenance and reuse constraints; datasets can be linked to derivative readiness, phenotype availability, and compatible tool or workflow contracts. These paths show how BR-KG turns text-level mentions into typed objects that can be queried, checked, and passed to the registry or review layer. Scientific acceptance occurs later, after execution evidence and review are available.

20

asset_readiness: block missing_assets:

- fold_manifest warnings:

- confound_specification_incomplete commitment_verdict: block

Resolver verdicts are reported as pass, warn, block, inaccessible, or incomplete. Pass allows planning to proceed. Warn allows planning but requires caveats or sensitivity actions. Block prevents commitment. Inaccessible and incomplete identify access or missingness states that must be resolved or reported as non-executable outcomes.

S4.2. BIDS, OpenNeuro, and derivative discovery

BIDS and OpenNeuro discovery [14, 20, 24] proceeds as a concrete resolution chain:

Step Resolution action 1 Resolve the dataset identifier, alias, or catalogue entry. 2 Check local BIDS root, derivative root, access class, license, and governance notes. 3 If direct file listing is unavailable, query BIDS entities and dataset metadata. 4 Parse OpenNeuro GLM specification files when present, including task names, con- trasts, condition weights, and contrast-to-concept mappings. 5 Discover workflow-specific assets such as derivatives, phenotype columns, target variables, masks, parcellations, matrices, and fold manifests. 6 If resources are remote-only, mark download-required or non-executable according to policy. 7 Return dataset-level and asset-level readiness separately.

Manual contrast-to-concept mappings link common GLM contrasts to cognitive concepts with confidence annotations. These mappings support evidence assembly and ONVOC normalization but remain separate from review acceptance.

S5. Typed tool registry and hierarchical action space

S5.1. Inventory levels and registry objects

The Brain Researcher action space is larger than the MCP surface. MCP exposes controlled operations, while the registry behind MCP stores executable components, workflow specifications, parameter schemas, compatibility clauses, backend recipes, and family cards. The checked inventory distinguishes four levels.

21

Level Count Object type Example role MCP surface 87 operations Public typed endpoints and structured lookups.

Search tools, resolve datasets, inspect arti- facts, request review. Exposed workflow layer

Plan and package a predictive-modeling recipe. Broader neuroimag- ing registry

177 exposed-plus- workflow specifications

MCP-facing and work- flow specs.

Validate that a tool ac- cepts the resolved input and produces expected outputs. Executable-wrapper inventory

2,089 registry specifica- tions

Compatibility, parameter, backend, and resource records.

approx. 196 Python- native tools + approx. 2,100 command-line wrappers

Callable tools, com- mands, modules, or scripts.

Run AFNI, ANTs, C3D, dcm2niix, FastSurfer, FreeSurfer, FSL, Greedy, MRtrix, MRtrix3Tissue, NiftyReg, or Workbench commands through an approved backend [4, 6, 12, 15, 16, 29].

Throughout this supplement, MCP operations refer to endpoints exposed by the MCP server. Executable components refer to Python tools, command-line wrappers, Neurodesk modules, container commands, or scheduler scripts. Registry specifications refer to machine-readable records used for discovery, compatibility checking, parameter validation, and recipe generation.

S5.2. Intent extraction and resource categories

Intent extraction maps a user request into planning fields: analysis intent, modality, expected output type, required resource types, and candidate method family.

Example intent record:

user_request: "Can we predict cognition from resting-state connectivity?" intent: prediction modality: fMRI_connectivity required_resources:

- connectivity_matrix - target_vector - covariate_table - fold_manifest expected_outputs:

- predictions - scorecard - model_metadata candidate_family: predictive_modeling

The system defines approximately sixty resource categories, including BIDS roots, 3D volumes, 4D time series, masks, event files, covariate tables, matrices, connectivity matrices, coordinates, statistical maps, QC reports, and rendered figures. A candidate tool is compatible only if it accepts the resolved input resource types, produces the expected artifacts, satisfies parameter schemas, is reachable through an allowed backend, and passes applicable tool-contract and method-condition constraints.

22

S5.3. Family-card retrieval and typed compatibility ranking

Tool retrieval uses a hierarchical action space. The planner first maps the request to intent, modality, required resource type, output type, and possible method family. It then retrieves precomputed family cards. Fifteen family cards are available in the checked registry, each storing a summary, typical use cases, member tools, supported inputs and outputs, common constraints, backend availability, and an embedding vector.

Example family-card excerpt:

family_card: predictive_modeling inputs:

- feature_matrix - target_vector - fold_manifest outputs:

- prediction_scorecard - trained_model_or_coefficients - heldout_predictions common_constraints:

- leakage_check - grouped_or_nested_cv - permutation_or_null_control backends:

- local_python - slurm

Expanded candidates are ranked by typed-contract compatibility, input/output resource match, backend requirements, runtime availability, policy scope, method-condition constraints, and task fit.

Ranking factor Example Input compatibility Candidate accepts a connectivity or feature matrix. Output compatibility Candidate produces predictions and scorecard artifacts. Backend availability Local Python or Slurm route is available under current policy. Constraint compatibility Candidate supports grouped CV or nested CV. Policy scope Candidate is allowed under the active allowlist mode.

S5.4. Canonical identity, Neurodesk mapping, and NiWrap descriptors

Canonical tool IDs are consumed by the planner, execution recipes, runtime registry, provenance records, and review rules. Backend mapping translates a canonical ID into a local Python entry point, Neurodesk module name, container command, shell command, or Slurm script. This prevents the same method from being represented differently across planning, execution, provenance, and review.

Example backend mapping:

canonical_tool_id: fsl_randomise registry_spec: fsl_randomise_contract backend: Neurodesk module: fsl/\allowbreak{}6.0 command_template: randomise -i {input_4d} -o {output_prefix} -d {design_mat} -t {design_con} expected_outputs:

- corrected_statistical_map - command_log

NiWrap-generated machine-readable descriptors serve as metadata and compatibility records. They support discovery, parameter schemas, and compatibility checks, but execution is routed

23

through Neurodesk recipes or other backend recipes rather than through NiWrap’s own execution path.

S5.5. Allowlists, cross-stage context, and operational cache

Tool allowlists support researcher-facing and diagnostic modes. Curated interactive-safe mode is used for routine researcher-facing sessions and excludes unsafe or irrelevant actions. Diagnostic mode broadens access for routing analysis, benchmark evaluation, registry testing, and controlled internal checks. The active allowlist determines which tools can be retrieved and is recorded in the run card.

Cross-stage context propagates structured constraints between planning rounds. Example:

cross_stage_context:

controversial_choice: GSR required_sensitivity:

- rerun_with_GSR - rerun_without_GSR claim_caveat_required: true reviewer_attention: controversial_choice

Operational caches reduce repeated BR-KG and registry lookups during long episodes. These caches are separate from reviewed memory: cached retrieval facts can speed up planning, but they are not accepted claims and do not replace run-bundle provenance.

S6. Constraint taxonomy, compiler, and commitment gate

S6.1. Hard and soft constraints

Hard constraints are validity boundaries. If a hard constraint is violated, the analysis is not accepted as valid. Soft constraints are consequential methodological choices that may be defensible but require documentation, sensitivity analysis, qualification, or caveats.

Constraint Type Example consequence Missing fold manifest for predictive model- ing

Hard Block commitment or execution.

Feature selection, standardization, or harmo- nization outside CV [31]

Hard Revise pipeline before acceptance.

Invalid exchangeability for permutation testing [32, 33]

Hard Block inference claim.

GSR without sensitivity analysis [5, 21, 23] Soft Warn; require with/without-GSR reporting or caveat. Dynamic-FC window choice without robust- ness check

Soft Warn; require window-length sensi- tivity or null comparison. Missing software version or random seed Soft Warn; require reproducibility comple- tion.

BR-KG negative-knowledge records encode known failure conditions even when the software can technically run.

negative_knowledge_record:

edge: KNOWN_TO_FAIL_WHEN

24

method: predictive_modeling condition: feature_selection_outside_cv severity: hard action: block_or_revise

Hard constraints are derived from tool contracts, method-condition records, and community validators. Soft constraints are derived from conditional-knowledge records, community-practice annotations, and tool-contract clauses.

S6.2. Constraint edge vocabulary and compiler algorithm

Hard constraints are compiled from KNOWN TO FAIL WHEN and VIOLATES ASSUMPTION edges, tool-contract clauses, and community validators. Soft constraints are compiled from HOLDS UNDER, SENSITIVE TO, and DEPENDS ON edges. The same vocabulary is used in planning, preflight, review, and claim calibration.

Compiler algorithm:

Step Compiler action 1 Retrieve method-condition records for each candidate workflow or tool. 2 Retrieve relevant tool-contract clauses and community-validator requirements. 3 Bind abstract conditions to the current dataset, resource ledger, parameters, and analysis state. 4 Generate executable or inspectable checks. 5 Classify each check as hard or soft. 6 Store the active constraint set in the run bundle. 7 Feed hard checks to filters or blockers and soft checks to ranking, warnings, sensitiv- ity requirements, or caveat language. 8 Re-run the compiler whenever the candidate tool set, resource ledger, specification ledger, or analysis plan changes.

Binding means converting an abstract rule into a concrete field or path. For example, ”fold manifest required” becomes a check against the fold-manifest field in the HCP-YA resource ledger.

Example compiler output:

active_constraints:

- id: grouped_cv_required

type: hard bound_field: resource_ledger.fold_manifest status: missing verdict: block - id: gsr_sensitivity_required

type: soft bound_field: preprocessing.global_signal_regression status: unresolved verdict: warn required_action: run_with_and_without_GSR_or_add_caveat

S6.3. Commitment gate

The commitment gate is the boundary between planning and execution. In interactive mode, the researcher approves, modifies, or rejects the proposed plan. In bounded autonomous mode, the gate is exercised by a critic or supervisor under a predeclared policy. In benchmark pass-through mode,

25

human approval may be disabled for evaluation-only runs, but the evidence, tool discovery, preflight, recipe, artifact-observation, and review pathway is unchanged.

Mode Gate authority Possible decisions Interactive Human researcher approve / modify / reject. Bounded autonomous Critic or supervisor policy approve / approve with warnings / re- vise / block / terminate.

Example commitment-gate record:

commitment_gate:

episode_id: ep_hcp_predict_001 authority: human_researcher decision: revise reason: missing_fold_manifest active_hard_blocks:

- grouped_cv_required allowed_next_actions:

- resolve_fold_manifest - choose_non_predictive_workflow - terminate_as_non_executable

Supplementary Figure S8: Systematic multiverse and robustness workflow. A candidate claim is expanded into an admissible specification space through evidence assembly, tool-card constraints, resource checks, and researcher commitment. Each branch is either executed, blocked, or rejected under the active constraint vocabulary, preserving both successful artifacts and non- executed alternatives in the run bundle. The resulting landscape is summarized by specification curves, robustness tables, branch-level caveats, and claim-family verdicts. The workflow turns analytic multiplicity into a reviewable robustness boundary with the specification space fixed before claim calibration.

26

S7. Execution substrate, preflight, and provenance

Supplementary Figure S9: Cross-modal, multi-stage neuroimaging execution substrate. Brain Researcher routes heterogeneous neuroimaging workflows through a shared execution layer that coordinates modality-specific tools, analysis stages, provenance capture, and backend selection. The figure summarizes the execution surface covered by Supplementary Methods S7: supported modalities, stable tooling and pipeline families, execution backends, and the shared planner-review- provenance logic that links a selected workflow to observed artifacts.

S7.1. Execution backends and backend selection

Brain Researcher supports local Python, Neurodesk, generic containers, Slurm/HPC, Kubernetes, AWS Batch, and other configured execution substrates. Backend selection is based on resource requirements, software availability, queue status, runtime policy, cost, health, and compatibility with the selected recipe. The selected backend and routing rationale are recorded in the run card.

Example backend-selection excerpt:

backend_selection:

selected_backend: slurm rationale:

- expected_runtime_high - local_python_route_unavailable - container_available

27

- queue_policy_allows_batch fallback_backend: Neurodesk_container

The scheduler records dependency resolution, retries, state transitions, and emitted events. Detailed scheduler strategies such as eager, lazy, batch execution, checkpoint persistence, and deadlock detection are implementation details recorded in Appendix F.

S7.2. Operational and scientific preflight

Operational preflight asks: can this run in the current environment? Scientific preflight asks: would this run be valid for the intended claim?

Operational checks include container image or CVMFS availability, module importability, Python entry-point availability, backend health, filesystem access, network policy, allowed roots, authen- tication state, and timeout budgets. Scientific checks include design-matrix rank, BIDS validity, coordinate-space consistency, resource-type compatibility, sample alignment, statistical prerequisites, fold-manifest integrity, and tool-contract requirements.

Example preflight result:

preflight:

operational:

filesystem_access: pass container_available: pass backend_health: pass scientific:

fold_manifest: block confound_specification: warn feature_target_alignment: pass final_verdict: block

Hard failures detected during preflight block execution. Soft warnings may allow execution but require caveats, sensitivity checks, or reviewer attention.

S7.3. Runtime isolation and real-time boundaries

Runtime isolation uses container-level sandboxing, restricted environments, path checks, ephemeral writable layers, and network isolation. Tools requiring broader filesystem access are executed only under a tracked relaxed mode with additional logging. In the evaluated configuration, MCP returns recipes, policy verdicts, and observation tools; the external coding agent, shell, container runtime, Neurodesk environment, or scheduler performs mutation or computation unless gated MCP administrative execution is explicitly enabled.

Real-time paths such as neurofeedback and online two-photon pipelines operate as continuous closed-loop processes outside the standard batch scheduler. They currently receive weaker provenance and post hoc review coverage than batch workflows and are reported as limitations in S12 rather than treated as fully evaluated execution pathways.

S7.4. Run bundle and authoritative provenance

Each run emits a run bundle (in agent-executed mode its completeness reflects the typed tools the agent invoked, and for a fully external analysis such as NeuroMark it is a post-hoc reconstruction). The run bundle is immutable and authoritative: memory cards, claim cards, and summaries are derived projections and do not replace the full record. If a claim card conflicts with the run bundle, the run bundle is authoritative.

Example run-bundle manifest:

28

run_bundle:

event_trace: events.jsonl trajectory_document: trajectory.yaml observation_record: observations.yaml analysis_bundle: analysis/\allowbreak{} run_card: run_card.yaml artifact_manifest: manifest.json checksums: sha256_manifest.txt review_cards: review/\allowbreak{} recovery_events: recovery.jsonl

The event trace stores sequence numbers, timestamps, event types, session IDs, and phase markers. The trajectory document records planning decisions, tool invocations, parameter bindings, and constraint verdicts. The observation record stores intermediate results, QC outputs, diagnostics, and environment-observed state. The analysis bundle stores final artifacts, metadata, checksums, and provenance chains.

S8. Scientific verification layer and claim calibration

The scientific verification layer is the main post-execution acceptance gate in Brain Researcher. Execution can show that a workflow ran, Harbor can show that a bounded task produced required files or statistics, and a language model can explain an output, but none of these events by itself accepts a neuroimaging claim. For the reported collaborator and bounded-autonomous evaluations, S8 defines the layer that consumes the run bundle, applies validity rules, assigns BLOCK or WARN findings, calibrates claim language, records one of six reportable claim states (accepted, qualified, revised, blocked, rejected, or deferred), routes unresolved decisions for human escalation, and determines memory-writeback eligibility. In this paper, “verification” means structured artifact- and claim-level challenge against declared scientific rules; it does not mean formal proof that a claim is true.

S8.1. Verification inputs and validity layers

Scientific verification consumes the run bundle, not the model transcript alone. It checks the selected plan, active constraints, execution trace, artifact manifest, logs, QC outputs, scorecards, candidate claims, and prior evidence. This prevents fluent explanations from substituting for observed artifacts.

Validity layer Example checks Statistical validity Design-model match, degrees of freedom, multiple comparisons, exchangeability, inference framework. Measurement validity Motion, distortion, registration, CIFTI/surface/volume consistency, QC, reliability. Construct validity Task-to-construct mapping, reverse-inference risk, contrast inter- pretation. Generalization validity Cross-validation integrity, leakage, sample size, site effects, stimu- lus effects, out-of-sample support. Claim validity Whether causal, mechanistic, clinical, external-validity, or biomarker language exceeds evidence.

29

S8.2. Rule severity, lifecycle, and reason tags

Verification rules are organized by severity, validity layer, reason tags, detection fields, and default action. BLOCK rules indicate high-confidence validity failures requiring revision before acceptance. WARN rules identify risks that may be addressed by sensitivity analysis, supplementary reporting,

alternative modeling, or claim revision.

Example review-rule card:

rule_id: leakage_standardization_outside_cv severity: BLOCK validity_layer: generalization reason_tag: leakage detection_field: pipeline_dag trigger: scaler_fit_before_cv_split default_action: revise required_fix: fit_scaler_inside_each_training_fold

Rule lifecycle status is defined in Appendix G, with the full rule registry, implementation-priority queue, calibration case library, review-context schema extensions, and sensitivity templates reported in the extended registry there. The main text distinguishes deterministic implemented checks from candidate or calibration-only rules when it affects the interpretation of a verification verdict: only implemented checks are treated as enforced, whereas deterministic, schema-dependent, NLP/LLM, and calibration-only candidates are reported as protocol or reviewer-facing constraints unless an episode records their enforcement. Reason tags include leakage, circularity, confound, null mismatch, low reliability, claim inflation, prior conflict, and controversial choice. Prior conflict is an audit trigger rather than a veto. Novelty cannot override a hard method error.

S8.3. BLOCK and WARN rule families

Representative BLOCK families include split/CV/leakage integrity, design-model mismatch, multiple- comparison and inference-framework errors, circular analysis, and hard confound failures. Examples include feature selection outside CV, standardization outside CV, harmonization outside CV, confound regression outside CV, test-set model selection, uncorrected whole-brain inference, invalid permutation exchangeability, brain-map correlation without spatial nulls, same-data ROI definition with effect testing, and demographic confounds omitted from group models.

Representative WARN families include measurement-quality gaps, soft multiple-comparison issues, multivariate/RSA/predictive-modeling risks, reliability and sample-size concerns, claim inflation, controversial choices, prior conflict, and reporting gaps. Examples include missing MRIQC or visual QA [11], multiple ROI tests without correction, RSA model comparison without correction [17], above-chance classification without permutation or confidence intervals, small-sample biomarker claims, reverse inference, correlation-as-prediction, fit-as-mechanism, GSR without sensitivity analysis [21], dynamic FC without null or window sensitivity [1], graph thresholding without multi-threshold checks, missing random seed, missing software versions, and failed BIDS validation [14].

BLOCK returns the episode to revision or termination. WARN can allow execution or acceptance only if the required caveat, sensitivity analysis, or reporting completion is recorded.

30

S8.4. Verification verdicts and revision routing

Verdict Meaning Next action accept Artifacts and claims satisfy active constraints and review rules.

Eligible for memory write- back. accept with qualifica- tions

Claim is valid only under explicit caveats or condition tags.

Write qualified claim card.

revise Result is not yet acceptable but may become acceptable with specified evidence or repair.

Return to planning, execu- tion, or claim editing. block Hard validity failure prevents acceptance. Stop, redesign, or termi- nate as non-accepted. reject Candidate claim is unsupported or contra- dicted.

No accepted memory writeback. defer Candidate passes an internal gate but fails a predeclared eligibility rule for the next valida- tion tier.

Hold pending external replication or the required tier. escalate Human researcher or domain expert must resolve the issue.

Pause or route for expert judgment.

Each evaluated claim in the collaborator and bounded-autonomous cases is reported in exactly one of six states (accepted, qualified, revised, blocked, rejected, deferred; Table 2). These states correspond one-to-one to the accept, accept with qualifications, revise, block, reject, and defer verdicts above; escalate is a routing action that hands the decision to a human rather than a terminal claim state. Prospectively governed episodes apply rules committed before the confirmatory test, whereas post-hoc audits apply explicit adjudication criteria to completed artifacts. In either tier, the state reflects the applicable evidence rule rather than the strength of the headline number alone (S11.2–S11.3). A terminal state is not intended to replace the condition structure of the evidence.

When support divides along an identifiable analytic axis, the claim report pairs the state with a

support-partition annotation that names the axis, its levels, and support at each level: the state governs claim promotion, while the annotation preserves the scientific pattern.


> **Table 2: Claim states and their explicit adjudication criteria. Each evaluated claim in the**

> collaborator and bounded-autonomous cases is assigned exactly one state by the review layer. For
prospectively governed episodes, thresholds are committed before the confirmatory test; post-hoc
audits instead apply documented criteria to completed artifacts. This is the reporting-level projection
of the review verdicts in the table above.

State Decision rule or adjudication criterion Accepted Holds across the episode-defined majority of admissible analytic specifications, with no single defensible choice reversing it, and passes every check required for the stated claim language. Qualified Supported only under explicit, named conditions: support is confined to a subset of specifications or holds only with stated caveats; when an identifiable support partition exists, it is retained alongside the state. Revised The target, measurement, or validation plan is changed in response to a failed gate, and the redesigned successor passes the same rules. Blocked A resource, design, power, or validity constraint prevents promotion from exploratory to confirmatory, regardless of the point estimate. Rejected Fails the applicable null, replication, or support rule. Deferred Passes an internal gate but does not yet satisfy eligibility for the next validation tier (for example, while awaiting external replication).

31

Example revision-routing card:

review_verdict: revise triggering_rule: gsr_without_sensitivity hard_or_soft: soft required_evidence:

- rerun_with_GSR - rerun_without_GSR - report_effect_stability allowed_claim_language: qualified_only

The review context schema supplies optional fields for model specification, multiple-comparison correction, measurement/QC, pipeline DAG steps, leakage detection, ROI provenance, reproducibil- ity, software versions, random seeds, and BIDS validation status. Missing fields cause rules to skip or warn according to rule policy; missing review context fields do not automatically create scientific acceptance.

S8.5. Claim calibration and memory eligibility

Claim calibration is separate from computation. A statistically valid result cannot be reported as causal, mechanistic, externally validated, clinically predictive, or a biomarker unless the correspond- ing evidence exists.

Computed result Overclaim blocked Allowed claim language Association in one dataset Causal mechanism Exploratory or dataset-qualified association. Internal prediction signal Clinical biomarker Internally evaluated prediction result. Robustness across parcellations External validity Condition-qualified robustness. Leakage-controlled grouped CV Mechanistic explanation Validated internal predictive result, not mechanism.

Only accepted or explicitly qualified claims are eligible for memory writeback. Blocked, rejected, or speculative claims remain in the run bundle.

S8.5.1. The claim record as a concrete object

The auditable record an episode produces is a set of versioned JSON objects, not an informal log. A commitment card (commitment-card-v1) freezes the claim text, scope boundary, allowed alternatives,

same-null constraint, and success/failure criteria, and stores a content hash (commitment hash) computed before execution; re-deriving the hash later detects any post-hoc change to the committed plan. A claim card (claim-card-v1) records the final bounded status of the claim, the checks it survived and failed, the evidence it draws on, and the evidence still required, and points back to the commitment card. Both are written to disk (commitment card.json, claim card.json) alongside an append-only ledger and the run bundle, so the record is exportable and can be opened by another reader after the session without rerunning the analysis. The representative card below comes from an earlier HCP-YA aggregate-prediction campaign and is retained as an illustration of the record schema; it is not the result record for the current HCP iterative episode in Supplementary Methods S11.3.1. Its commitment hash was a version-control soft anchor committed alongside its validator rather than a third-party time-stamped pre-registration.

32

{

"schema_version": "claim-card-v1", "claim_id": "hcp_rsfc_aggregate_predictor", "claim_text": "A frozen ridge predictor on resting-state FC predicts the

five-component behavioral target in HCP-YA (fold-mean r = 0.190).", "status": "accepted", "scope_boundary": "HCP-YA; Schaefer-100x7 FC; no-GSR; 10-fold CV;

accepted with search correction, not covariate-robust; internal validation only", "commitment_card_ref": "commit:hcp_rsfc_aggregate_predictor", "commitment_hash": "b1e4...e7a9", "evidence_bundle_refs": ["eb_hcp_fc_features", "eb_liu_components"], "survived_checks": [

"family_aware_permutation_null (Family_ID block, 1000 perms, plus-one p)", "max_over_pipelines_null (38 replayable candidates)" ], "failed_checks": [

"covariate_retention_gate (>=70% of unadjusted effect retained after

demographic + IQ adjustment; aggregate retained 55%, r 0.190 -> 0.105, below the 0.133 floor) -> bounds scope to search-corrected, not covariate-robust" ], "falsification_budget_spent": {"null_models": 2, "permutations": 1000}, "next_required_evidence": ["external replication (HCP-Aging)"], "status_not_ground_truth": true }

This is the object the main text refers to as the auditable claim record; the review card (Appendix G) and the memory card (Appendix H) are its review-time and memory-time counterparts. A real exported example built on public Neurosynth coordinate evidence (a working-memory claim, final status weakened under the conservative evidence profile) is released with the code, so a reader can open an actual claim card.json and its evidence verdicts.json directly rather than relying on the listing above. This legacy artifact predates the six-state reporting vocabulary used for the collaborator and bounded-autonomous evaluations; we retain its literal weakened label and do not retroactively relabel the exported record. For the schizophrenia NeuroMark episode, by contrast, no sealed pre-analysis commitment card was created: the collaborator’s three hypotheses were prespecified in their own study protocol rather than sealed as a Brain Researcher commitment card before execution, so the audit bundle we provide for that case is a post-hoc reconstruction assembled from the completed multiverse artifacts. Its claim card accordingly records commitment card ref: null and pre run commitment card found: false rather than asserting a pre-run seal, and is labeled post-hoc by design rather than backfilled. The sealed-commitment-card mechanism is therefore demonstrated on the released Neurosynth example; the NeuroMark episode exercises the multiverse, claim-state, and directionality-audit machinery.

S9. Memory system, conflict detection, and BR-KG promotion

S9.1. Memory objects and writeback gate

The memory system stores reviewed knowledge derived from completed episodes. It is not a transcript archive and not a replacement for the run bundle. Its purpose is to retrieve condition-tagged claims, prior tactics, unresolved caveats, review outcomes, and relations among findings.

33

Supplementary Figure S10: From auditable run bundles to cumulative field memory. Completed episodes first produce run bundles containing the committed plan, executed actions, logs, artifacts, validation outcomes, review notes, failures, and caveats. The review layer determines which candidate claims are accepted or explicitly qualified for memory writeback; rejected, blocked, or failed candidates remain recoverable in the run bundle without becoming accepted graph facts. Eligible claims become condition-tagged claim cards with provenance pointers and relation events such as support, contradiction, refinement, conditioning, or supersession. Curated memory cards may later be promoted to BR-KG under a separate governance policy.

34

Memory object Purpose Claim card Stores reviewed claim text, polarity, scope, conditions, evidence level, caveats, and provenance pointers. Episodic run card Stores the question, plan, tool sequence, successful tactics, failed tactics, resource blockers, and resume hints. Review card Stores review level, verdict, risk tags, issues, fixes, and final eligibil- ity status. Claim-relation event Stores support, contradiction, refinement, conditioning, or superses- sion relations between claims.

Example claim card:

claim_card:

claim: "Model performance remained above chance under grouped CV." polarity: support scope: HCP-YA sample only evidence_level: L3_internal_validation review_status: accepted_with_qualifications caveats:

- no_external_dataset provenance_pointer: run_bundle/\allowbreak{}ep_hcp_predict_001

Memory writeback is gated by review. Failed, blocked, rejected, or speculative candidate claims remain searchable through the run bundle but are not promoted as accepted memory claims.

S9.2. Conflict detection and relation events

At writeback, the system encodes the new claim, retrieves similar prior claims above a configured threshold, and submits new/prior pairs to a critic for relation classification. The critic classifies apparent support, contradiction, refinement, conditioning, or supersession for retrieval and audit; it does not resolve scientific truth by itself. For contradictory or conditioning pairs, the system creates bidirectional claim-relation events and records the conditioning variable when available.

Example relation event:

relation_event:

new_claim: claim_042 prior_claim: claim_017 relation: conditioning conditioning_variable: preprocessing_pipeline confidence: medium logged_in: run_bundle/\allowbreak{}ep_hcp_predict_001

Memory is append-only. Claims may be superseded, conditioned, or contradicted, but they are not silently deleted.

S9.3. Memory partitioning and BR-KG promotion

During benchmark evaluation, memory namespaces are partitioned so evaluated tasks cannot retrieve target answers from prior benchmark or collaborator episodes. Training, development, benchmark, collaborator, and autonomous-campaign namespaces are separated. Any shared memory is explicitly declared in the evaluation card.

BR-KG promotion is a separate curation path:

35

Step Curation action 1 Reviewed claim card is created. 2 Candidate graph update is proposed. 3 Schema validation is performed. 4 Source and provenance checks are performed. 5 Curation approval is recorded. 6 Accepted BR-KG record is created.

This preserves the distinction between episode memory, candidate graph updates, and accepted BR-KG records.

S10. Bounded research episodes and validation contracts

Throughout, the terms “bounded autonomous” and “self-evolving” denote the same narrow process: validation-gated agentic search in which the system proposes, tests, and revises candidate claims strictly within a researcher-declared action space, budget, and validation ladder. They do not denote autonomous scientific self-improvement, open-ended goal setting, or any relaxation of the predeclared gates.

S10.1. Harbor task format and Brain Researcher mapping

Harbor provides a containerized task contract with an instruction file, environment definition, hidden verifier, metadata, and resource limits. In this work, Harbor bounds the rollout environment and returns task-level completion evidence. It is not the scientific reviewer.

For Brain Researcher benchmark rollouts, Harbor can realize a bounded episode as a task contract. The contract specifies the scientific objective, allowed resources, admissible action space, expected artifacts, execution budget, verifier logic, reward or partial-credit outputs, review rules, memory policy, and escalation conditions. The HCP and TRIBE research lines reported in S11.3 instead used prospective episode bundles and frozen successor contracts outside Harbor. BR-MCP remains the domain-control plane for tool discovery, dataset resolution, planning, recipe generation, policy checks, run observation, grounding, and scientific review.

Example Harbor verifier output:

harbor_verifier:

artifact_manifest_present: true required_statistic_present: true schema_valid: true command_completed: true trajectory_requirements_met: partial reward: 0.8

This verifier output can show that a task produced the required files and statistics while the Brain Researcher scientific verification layer still returns revise or block because of leakage, missing sensitivity analysis, invalid nulls, or claim inflation.

36

Supplementary Figure S11: In-silico experiment design and bounded hypothesis iteration. The bounded workflow starts from a declared research context, evidence state, allowed action vocabulary, budget, validation ladder, expected artifacts, and stopping rule. Candidate in-silico experiments are proposed, materialized, run through lower-resource validation tiers, and either rejected, revised, deferred, or advanced to stronger tests. Reward or search scores are kept separate from scientific acceptance, which requires the predeclared nulls, artifact checks, and review rules to pass. The loop returns reviewable follow-up hypotheses or memory candidates; acceptance remains with verification.

37

Component Checks Does not check Harbor verifier Files, schema, required statistic, command/ test success, trajectory requirements.

Scientific validity or claim scope. BR-MCP Tool/dataset resolution, policy constraints, recipe packaging, provenance capture.

Final biological truth.

Execution backend Logs, artifacts, metrics, environment- observed state.

Claim acceptability.

Scientific verification layer

Leakage, confounds, null controls, robust- ness, caveats, claim calibration.

Independent replication or complete scientific truth. Memory gate Accepted or qualified writeback. Unreviewed or rejected claims.

S10.2. Supervisor, critic, and bounded iteration

The bounded-loop architecture can use a supervisor–critic pair under fixed budgets and stopping criteria. The supervisor proposes the next analytic branch from the current episode state: open caveats, failed checks, memory conflicts, validation-ladder progress, and remaining compute/time budget. Candidate branches may vary a confound model, test an alternative parcellation, extend a sensitivity analysis, run a null-control analysis, investigate an anomaly, broaden the search, or abandon a target that cannot meet the contract. This subsection describes the available architecture, not an assertion that every reported episode used this exact controller.

Example branch-decision record:

branch_decision:

branch_type: sensitivity_analysis reason: unresolved_GSR_warning proposed_action: rerun_with_and_without_GSR expected_resolution: qualify_or_clear_controversial_choice_warning budget_cost: one_additional_run

After Harbor verification and review-layer inspection, the critic asks whether the previous cycle resolved a review finding, exposed a hard failure, improved validation level, revealed a method dependency, or merely repeated known work. It then returns a structured decision.

critic_decision:

decision: continue reason: sensitivity_analysis_resolves_open_warning remaining_budget_cycles: 2

Episodes terminate when the goal is reached, the validation ladder is satisfied, a hard review block cannot be resolved, progress stalls for the configured number of cycles, compute or wall-clock budgets are exhausted, the critic requests human escalation, or infrastructure recovery fails.

termination:

status: terminated_budget_exhausted unresolved_findings:

- external_validation_missing memory_writeback: qualified_claim_only

S10.3. Bounded autonomous episode contract

A bounded autonomous episode is evaluable only if it declares its target question, design space, budgets, stopping criteria, validation ladder, expected artifacts, review rules, memory-writeback

38

policy, and escalation conditions. Each cycle must produce a branch-decision record, Harbor verification record, artifact manifest, review card, and claim-status update.

Example contract excerpt:

bounded_episode_contract:

target_question: >

Evaluate whether HCP-YA features predict the selected behavioral target. admissible_design_space:

- predictive_modeling_family - grouped_cv - predeclared_covariates - parcellation_sensitivity cycle_budget: 3 validation_ladder: L0_to_L3 expected_artifacts:

- prediction_scorecard - artifact_manifest - review_card memory_policy: accepted_or_qualified_only escalation_conditions:

- unresolved_hard_block - out_of_design_space_request

The contract prevents open-ended optimization from being mistaken for autonomous scientific discovery. Follow-up branches remain inside the admissible design space and must pass the same commitment, execution, Harbor verification, review, and memory-writeback rules as interactive episodes.

S10.4. Validation ladder and claim strength

Bounded autonomous episodes use a validation ladder to prevent claim escalation from a single successful run.

Ladder level Purpose Example evidence Allowed claim strength L0 feasibility Required data, tools, and resources exist.

Analysis is exe- cutable. L1 minimal signal Initial effect or prediction signal appears.

Dataset/resource resolution and preflight pass.

First-pass held-out test, per- mutation, or preliminary association.

Exploratory sig- nal.

L2 robustness Signal survives method variation.

Parcellation, confound, threshold, model, or prepro- cessing sensitivity.

Condition- qualified result.

L3 leakage/null control Trivial validity failures are ruled out.

Grouped CV, nested CV, permutation, spatial null, or negative control.

Validated internal result.

Generalization tested beyond initial fit.

Held-out subjects, site, dataset, or independent benchmark.

Stronger general- ization claim.

L4 held-out or external support

L5 claim calibration Final language con- strained by evidence.

Review card, caveats, mem- ory relation events, claim governor.

Accepted or quali- fied claim.

For example, a first-pass held-out signal reaches L1. If the signal survives parcellation and confound sensitivity, it reaches L2. If grouped CV and permutation controls pass, it reaches L3.

39

Without external dataset support, the claim cannot exceed L3; it cannot be called externally validated. Without construct or causal evidence, it cannot be called mechanistic.

S10.5. Structured hypothesis triage and loop closure

Structured hypothesis triage is separate from bounded validation. Candidate questions, representa- tions, estimators, or follow-up tests may be proposed during exploration, but a successor analysis must re-enter the episode machinery with a frozen target, analysis definition, evidence boundary, and stopping rule. Loop closure therefore means that one episode’s result can determine the next bounded question; it does not permit the completed analysis to be rewritten after its outcome is known.

The two iterative episodes instantiated this mechanism in different ways. In HCP, a bounded development search supplied a fixed prediction configuration for a matched comparison and cross- outcome follow-up. In TRIBE, an open six-category screen supplied several candidate contrasts; a post-hoc geometry diagnostic and an explicit researcher decision selected speech versus tools, after which the estimand and evaluation rule were frozen before new stimuli were analysed. Complete episode accounting is reported in Supplementary Methods S11.3.

Supplementary Figure S12: Out-of-distribution hypothesis proposal and triage. Candidate hypotheses are generated near sparse, conflicting, or under-connected regions of the current knowledge space. Triage checks feasibility, novelty, evidentiary support, resource availability, and validation requirements before a candidate can enter an episode. Hypothesis generation can propose a direction, but promotion still requires evidence assembly, execution, review, and memory eligibility.

40

Supplementary Figure S13: Result-to-hypothesis loop closure. Completed outputs, residual uncertainty, failed branches, and condition-dependent findings can seed successor analyses. Every successor must pass the same commitment, execution, review, and memory-writeback path as a new episode.

41

S10.6. Freezing successor analyses

A successor analysis separates discovery from the next evaluation by freezing the scientific target, candidate or contrast, estimand, admissible inputs, and decision rule before the successor data are scored. Evidence may alter which successor is chosen, but it cannot alter the analysis already under evaluation. The HCP configuration was fixed and then refit separately for each behavioural target under the same evaluation procedure. The TRIBE speech–tools estimand was fixed before three non-overlapping recurring-source panels and, subsequently, before a score-blind panel drawn from four previously unused collections. Transport failures, excluded cells, and technical failures remain in the episode record rather than disappearing from denominators.

S10.7. Same-agent sessions without Brain Researcher

We also inspected separately initiated sessions in which the same coding agent received the research

goal but did not invoke Brain Researcher. These sessions provide qualitative process context, not a matched causal ablation: prompts, interaction histories, budgets, stopping decisions, and follow-up opportunities were not randomized or held identical. Their terminal states and the limits of this comparison are reported in Supplementary Methods S11.3.3.

S11. Evaluation protocol

Three classes of verification check. In conventional workflows verification is a check applied after an analysis is complete; in Brain Researcher it is the precondition for a methodological commitment to become infrastructure at all. Some checks admit unambiguous criteria, such as whether the required inputs exist, whether subject sets match, whether information has leaked across folds, or whether a null model is applied in the domain for which it was declared; these establish only that the stated analysis was carried out in a way that can support its claim, not which analysis is best. Other choices have no single correct answer but a set of defensible ones, such as the parcellation, confound model, or threshold, and here the system renders the navigation explicit rather than allowing a single pipeline to conceal it. A third class resists formalization altogether, including what question is worth asking, what should count as evidence, and how a result revises understanding; the system preserves commitments about this class but does not adjudicate them. That boundary is intentional, and everything beyond it remains with the researcher.

S11.1. Evaluation components

The evaluation protocol has four components.

Evaluation component What is measured or documented BR-KG characterization Graph snapshot, schema, source coverage, provenance cover- age, density, orphan rates, property coverage, and example traversal paths. Benchmark construction Controlled task manifests, scoring contracts, with-BR/ without-BR protocol, ablations, and evaluation partitions. Collaborator cases Real neuroimaging questions, dataset access, tool pathway, artifacts, robustness probes, review outcome, caveated con- clusion, and human/system responsibility split. Iterative research episode Whether evidence from one stage is converted into a frozen successor analysis with explicit denominators, stopping states, and claim boundaries.

42

S11.1.1. Benchmark surfaces

The quantitative Results use two benchmark surfaces. The first is a paired tool-calling benchmark: a correct response maps a natural-language neuroimaging request to an existing analysis tool or executable route, with required inputs available before execution. The technical metric family for this surface is routing capability. The second is an evidence-citation benchmark based on NeuroimageKnowledge: a claim is counted as grounded only when its cited evidence can be located and judged supportive for the stated claim. Support was evaluated by three LLM-based judges (Claude Opus 4.8, Codex GPT-5.5, and Gemini 3.1 Pro), each blind to benchmark condition. All

reference-bearing rows were sent to all three judges (with-BR, 814 of 1,673 generated rows; without- BR, 469 of 1,525). Each label entered a three-state vote as verified, not verified, or cannot judge, and a row counted as verified when at least two judges voted verified. Every generated evidence- basis row, including rows without a reference and rows without two verified votes, remained in the denominator. Both surfaces compare with-BR and without-BR conditions over runs drawn from seven provider-defined model variants: Claude Code / Claude Opus 4.8, Codex GPT-5.5, Gemini 3.1 Pro, GLM-5.1, DeepSeek-V4-Pro, Kimi K2.5, and Qwen3.6-Plus. The tool-calling surface is a complete seven-model paired matrix; the evidence-citation headline is a descriptive question-level aggregate over all generated evidence-basis rows rather than a paired model-level estimate.

Surface Primary denominator Reported metrics Tool calling 60 task manifests × seven models per condition (420 model-item trajectories).

Capability@k, Correct route/tool@k, and Handoff score@k. Capability@k is required-capability coverage after k non-neutral actions, not a binary route-reached indica- tor. Evidence citation 50 open-ended question sets; all generated evidence-basis rows per condition, with only rows receiving at least two verified votes con- tributing to the numerator.

verified groundedness rate, verified among claimed grounded, citation spam rate, and answer correctness rate.

What counts as verified grounding. For each claim a model supports with a citation, a judge blind to condition checks two things: whether the cited source can be located, and whether it supports the claim as stated. Only a full match is counted as verified. A source that supports a narrower version of the claim, or that is real but about a different point, is not counted. Each grounded item receives one label; Table 3 gives the three that occur here with a real example of each. Two further not-verified labels, for references that cannot be resolved or parsed, did not occur among the resolvable items. Because only full support is counted, many citations are not credited: a substantial share point to real sources that support only part of the claim (partial) or a different point (no unrelated). Judges also differ in how strictly they treat partial support, so the rate depends on the judge.

Among the 444 non-verified with-BR rows present in all three judge outputs, 289 (65%) received an exact-label majority of no unrelated and 124 (28%) an exact-label majority of partial. The remaining 31 (7%) had no exact-label majority or could not be judged; none had a fabricated or malformed exact-label majority. The two dominant failure modes suggest different remedies: off-topic citations call for stronger retrieval filtering and reranking, whereas partial-support citations call for a claim-to-evidence entailment check that constrains a claim to what its source actually states. Residual borderline cases, where the judges themselves disagree, are the ones a human reviewer or

43


> **Table 3: Grounding labels, with a representative with-BR item for each. Each model**

> claim is checked, blind to condition, against the source it cites. Only yes (the source fully supports
the claim) is counted as verified; partial (supports only a narrower version) and no unrelated (a real
source on a different topic) are not. Claims use the models’ own wording, lightly shortened; judge
rationales are condensed. Further not-verified labels (cannot judge, malformed, fabricated) apply to
references that cannot be resolved or parsed.

Label Model claim (cited to a retrieved source) Judge’s reason

yes (verified) Head motion, respiration, arterial CO2, blood pressure, autoregulation, and vasomotion can affect BOLD signals and therefore confound resting-state interpretation.

The source explicitly lists each of these factors and how they alter the BOLD signal; the claim is fully supported.

partial (not credited)

Head-motion artifacts are the most frequently reported issue in QC, and outliers should be de- tected in image-homogeneity and co-registration tests before group analysis.

The source supports the first clause (motion is the most frequent QC issue) but says nothing about the second (the outlier-detection proce- dure); only a weaker version is grounded. no unrelated (not cred- ited)

The spatial-normalization workflow should in- clude visual verification that functional contours align with anatomy before writing deformation fields.

The cited source is about time-series QC (frame- wise displacement, WM/CSF signals); it does not mention spatial normalization or deforma- tion fields at all.

the audit layer is best placed to resolve. Among all 814 with-BR rows present in the three judge outputs, 777 (95%) cited a retrieved document, of which 367 (47%) received a verified majority; 3 of 37 (8%) specific citations produced from the model’s own parameters were verified. The three-judge diagnostic therefore points chiefly to retrieval returning an off-topic or partially-supporting source rather than the model fabricating references.

S11.1.2. Benchmark construction and independence

Because the team that built Brain Researcher also assembled the benchmark, we took explicit steps to limit circularity. Benchmark questions were drafted from standard neuroimaging analysis requests and curated together with a co-author who is not a developer of Brain Researcher; this co-author also evaluated system outputs and ran the quantitative benchmark. For every item, the reference route and required capabilities were fixed before either condition (with-BR or without-BR) was run, so that targets could not be adjusted to favour the system. Scoring is capability-level: any response that covers an item’s required capabilities is credited whether through a Brain Researcher call or an equivalent executable route. For the grounding rate, all reference-bearing rows were scored by the three condition-blind judges. Their labels were reduced to verified, not verified, or cannot judge; a row entered the numerator when at least two judges voted verified, while every generated evidence-basis row remained in the denominator. Thus a single cannot judge label did not block verification when the other two judges voted verified. On the grounding surface, inter-judge reliability is moderate (three-judge Fleiss’ κ = 0.50 with-BR and 0.72 without-BR, binary verified versus not), and is set almost entirely by one lenient judge: Gemini 3.1 Pro and Claude Opus 4.8 agree closely (Cohen’s κ = 0.92, 96% raw agreement with-BR), whereas Codex GPT-5.5 credits full support more readily (per-judge verified rate 0.31 versus 0.21 and 0.22). Because most items are not verified, κ understates agreement under the skewed without-BR base rate (Gwet’s AC1 = 0.68 against κ = 0.48 for the Codex–Claude pair; raw agreement 0.80). The condition contrast does not depend on the choice of judge: each judge independently shows a large with-BR gain (with- versus without-BR verified rate 0.21/0.04 for Gemini, 0.31/0.04 for Codex, 0.22/0.08 for Claude). Gemini’s raw run recorded about 30% of grounding items as unjudged because the model emitted its verdict

44

inside an envelope the parser rejected; we recover each such verdict from the model’s own output (241 with-BR and 79 without-BR items) and release the recovery audit with the benchmark package.

The reference targets and scoring contracts are released (Appendix J) so that the benchmark can be re-scored independently. We did not commission a fully external benchmark, and we note this as a limitation (Supplementary Methods S12).

S11.1.3. Human audit of the automated judges

To validate the LLM judges, we drew a reproducible random 20% sample (seed 20260630) of the scored results across the reported benchmarks (272 items, one graded entry each) and adjudicated each by hand against the recorded automated verdict. Agreement was 96% (261 of 272; Cohen’s κ = 0.94, linear-weighted κ = 0.96 on the grounding items where all disagreements fall; Table 4). Tool-routing (12 of 12) and NIK answer-key (15 of 15) items were confirmed; the 11 discrepancies fell entirely in the grounding benchmark (234 of 245 confirmed) and were all one-step severity nuances (an item scored strictly that is arguably partial, or the reverse). None reversed a supported call

to unsupported or the reverse, and the judges erred strict (Table 5), so the reported grounding gains are conservative rather than inflated. The full graded sheet is reproduced in Appendix M and released with the benchmark package (Appendix J).


> **Table 4: Human audit of the automated benchmark judges. A reproducible random 20%**

> sample of the scored results across the reported benchmarks, adjudicated by hand against the
automated verdicts. Discrepancies were confined to the grounding benchmark and were all one-step
severity nuances that never reversed a supported/unsupported call, with the judges erring strict.

Benchmark Checked (20%) Confirmed To review Tool routing 12 12 0 NIK answer keys 15 15 0 Grounding judgments 245 234 11 Total 272 261 11

Metric numerators and denominator rules for main-text Fig. 3 are expanded in Appendix J. The two benchmark surfaces are not pooled because their item types, denominators, scoring rules, and ceilings differ.

S11.1.4. Effect sizes, uncertainty, and paired significance

For the tool-calling benchmark, the headline numbers are means across the seven model variants, so we treat the model as the unit of analysis (n = 7): each model contributes one with-BR and one without-BR score, itself a mean over the 60 tasks, and the contrast is the within-model paired difference. This is the conservative unit because the seven models are not independent draws from a population and their per-task outcomes are clustered; the paired design also controls for task difficulty, since the same items are scored under both conditions. Table 6 reports, for each tool-calling metric, the across-model mean under each condition, the mean paired improvement with a t-based 95% confidence interval across the seven models, a paired t test, and an exact two-sided Wilcoxon signed-rank test. All seven models improved on all three metrics (7/7 positive differences), which places the signed-rank statistic at its floor for n = 7 (p = 0.016). As a pooled descriptive check that does not assume model exchangeability, first-action correct route/tool selection over the 420 model-task trajectories rose from 0.233 (Wilson 95% CI 0.195–0.276) to 0.936 (0.908–0.955). On the evidence-citation surface, the main-text headline (0.046 to 0.220) is a descriptive three-judge-

45


> **Table 5: The 11 flagged grounding items from the human audit. All fell in the grounding**

> benchmark under the with-BR condition. Nine reflect the judge scoring an arguably partial item
as fully unrelated (too strict); one (NIK-BP-H-003) scored an arguably partial item as a full yes
(too generous); and one (NIK-BP-H-001) is a relabel within non-support (no versus no unrelated).

None moves directly between the opposite hard calls (yes and no unrelated), and the net tendency is strict, so with-BR grounding is if anything under-credited.

Item Judge Human Issue NIK-BP-H-003 yes partial Dead-salmon study and multiple-comparison correction ab- sent from the source; support real but incomplete. NIK-BP-H-001 no unrelated no Source contradicts the claim, so a negative rather than unrelated. NIK-BP-H-005 no unrelated partial Source states the exact “multiplicity of methodologic vari- ants” problem the claim describes. NIK-IN-H-004 no unrelated partial GSR-debate context bears on global-signal content. NIK-ME-H-004 no unrelated partial Covers subject motion and noise modeling; related but general. NIK-NK-E-003 no unrelated partial Measures FWER control with no true signal, i.e. false- positive territory. NIK-PP-H-006 no unrelated partial Discusses geometric distortion and its correction; “TOPUP”/susceptibility wording absent. NIK-ST-H-007 no unrelated partial Context is statistical power and effect-size uncertainty. NIK-ST-H-007 no unrelated partial Same power and significance topic as the claim (second item). NIK-ST-M-008 no unrelated partial Names permutation-based testing, the claim’s subject. NIK-ST-M-008 no unrelated partial Context explicitly names permutation-based testing (second item).

46

majority rate over all generated evidence-basis rows, with only rows receiving at least two verified votes contributing to the numerator, equal-weighted across the 50 questions rather than inferred from seven paired model scores. The reported question-clustered 95% interval for the with-BR rate (0.168–0.272) is the normal-approximation interval formed as the mean plus or minus 1.96 standard

errors across those 50 per-question rates, using the stored analysis’s population-standard-deviation convention. Judge-specific rates are reported in Appendix J, and the underlying artifacts are released with the benchmark package. With n = 7 the tool-calling confidence intervals remain wide and are reported as descriptive bounds on the paired effect, not as population estimates; a fully external, independently constructed benchmark remains the decisive next measurement (Supplementary Methods S12).


> **Table 6: Paired benchmark effect sizes with uncertainty and significance. Unit of analysis**

> is the model (n = 7); each entry is a mean across the seven model variants, and each model’s
score is itself a mean over the 60 tool-calling tasks. The improvement is the mean within-model
with-BR minus without-BR difference; the 95% confidence interval is t-based across the seven
models. Significance is a two-sided paired t test [t(6)] and an exact two-sided Wilcoxon signed-rank
test. All seven models improved on every metric.

Metric Without BR

With BR Mean ∆[95% CI] t(6) Wilcoxon p Correct route/tool@1 0.233 0.936 +0.702 [0.576, 0.829] 13.6 0.016 Capability@1 0.498 0.945 +0.447 [0.282, 0.612] 6.6 0.016 Handoff score@1 0.474 0.761 +0.287 [0.201, 0.373] 8.2 0.016

S11.1.5. Seven-model routing ablation without direct KG calls

This seven-model routing ablation used the same tasks.60 manifest, frozen labels, prompt template, model-facing route search→tool search surface, and exact-top-1 endpoint for all seven requested model routes. Exact top-1 is a match to one of the task’s frozen acceptable route labels. Across the 420 route–task episodes, 362 matched an acceptable top-1 label (86.2%; requested-route range, 81.7–90.0%). Direct KG-named calls were unavailable in this arm. A protocol violation counted as an error; only an infrastructure failure was recorded as missing.

The provenance column records how a requested route was run, not a different evaluation condition; all seven rows, including Kimi and Qwen, use the same no-direct-KG endpoint. This exact-label top-1 metric differs from the historical Correct route/tool@1 metric and is reported separately from the paired with-BR/without-BR benchmark.

S11.2. Collaborator cases

Collaborator cases are selected when they involve a concrete neuroimaging question, tractable scope, accessible data, and a meaningful analysis or review target. The cohort includes three collaborators across three neuroimaging subfields. Each case reports the collaborator-facing question, subfield, dataset access, tool pathway, execution artifacts, robustness probes, review outcome, caveated conclusion, attribution, and the boundary between system-generated artifacts and human decisions.

Case inclusion requires: a defined scientific question, available or resolvable data, an executable or reviewable analysis path, and a clear endpoint. Exclusion applies when data access is unresolved, the question is outside the supported modality/action space, or governance constraints prevent execution. Collaborator cases may be conducted through standard Claude Code, Codex, or Cursor

47


> **Table 7: Seven-model routing ablation without direct KG calls. All seven rows use the**

> same no-direct-KG exact-label top-1 endpoint; run provenance is shown separately.

Runner/requested route Exact top- 1 Protocol- compliant

Gold avail- able

Run provenance

Claude Code / claude-opus-4-8 54/60 (90.0%)

59/60 59/60 v1 tools-only run

Codex / gpt-5.5 51/60 (85.0%)

60/60 59/60 v1 tools-only run

OpenCode / google/gemini-3.1- pro-preview

54/60 (90.0%)

59/60 59/60 v1 tools-only run

OpenCode / opencode-go/glm- 5.1 52/60 (86.7%)

60/60 59/60 v2 tools-only single arm

OpenCode / opencode- go/deepseek-v4-pro

51/60 (85.0%)

58/60 59/60 v2 tools-only single arm

OpenCode / opencode/kimi-k2.5 51/60

60/60 59/60 v1 tools-only single arm

(85.0%)

49/60 (81.7%)

OpenCode / opencode/qwen3.6- plus

60/60 59/60 v1 tools-only single arm

interfaces depending on collaborator preference; all interfaces route through the same MCP pathway.

These cases were not selected on their outcomes. The inclusion and exclusion criteria above are properties of a case’s tractability—a defined question, resolvable data, an executable analysis path, and a clear endpoint—and were applied before any result was seen, never on whether a claim turned out favorable. This is visible directly in the reported cohort, which was assembled for heterogeneity in evidence structure and consequently spans a range of outcomes rather than a run of successes: the NeuroMark audit returned qualified claims alongside a caught sign-blind scoring failure; the cocaine-use-disorder episode returned a bounded null with its exploratory screen blocked from confirmatory promotion; and the cross-cultural social-cognition episode was blocked as underpowered and ended without a settled claim. Each case reports the states assigned by its applicable prospective gate or post-hoc audit—including the null and blocked outcomes—so the record shows the same accounting whether or not a case produced a publishable positive result. Because the collaborator cohort is small (n = 3) and deliberately heterogeneous, we present these as case studies of how the claim-record machinery behaves across different evidence structures (accepted, qualified, null, and blocked), and not as an estimate of a success rate or a benchmark of

positive findings.

Execution modes and per-case attribution. Brain Researcher runs in two execution modes that differ in where the analysis runs and therefore in what the audit record guarantees. In engine- executed mode (Fig. 1), the engine runs the analysis end to end and emits the full audit bundle—a hash-sealed commitment card written before observation, the recorded trajectory, provenance, and observations, and an adjudicated claim card with evidence verdicts—as a structural byproduct, with commit-before-observe and version-pinned execution enforced by the engine. In agent-executed mode, a coding agent (Claude Code, Codex, or Cursor) drives the analysis: it authors and runs the analysis code, invoking Brain Researcher through the MCP for knowledge-graph grounding, execution recipes, typed execution (for example cluster submission), artifact logging, and scientific review. Brain Researcher records the work through its typed tool surface and applies the review layer plus any applicable prospective commitment gate, but the analysis is authored and driven by the agent rather than emitted by the engine, so a full sealed pre-run bundle is not produced as

48

an automatic byproduct and the audit record is only as complete as the tools the agent invoked, carrying no engine-side execution stamp. This mode is also what makes Brain Researcher usable when the data are local or governed and cannot enter the cloud sandbox: in the NeuroMark case the analysis ran entirely in an external workspace with Brain Researcher recording and reviewing it, whereas in the other cases the agent drove the analysis within a Brain Researcher episode, so more of the run passed through its typed tools. Both modes share the same knowledge graph, tool contract, and review layer.

Pre-registration strength consequently falls into three tiers. A sealed pre-run commitment card (i.e. the full engine-executed protocol) is demonstrated on the public Neurosynth working-memory

example (Supplementary Methods S8.5.1). The iterative HCP and TRIBE lines (Supplementary Methods S11.3) combine adaptive discovery with later frozen successor contracts; their evidence strength is stated stage by stage rather than summarized as one pre-registration tier. The three collaborator cases carry no sealed Brain Researcher commitment card: their hypotheses were prespecified in the collaborators’ own protocols. For NeuroMark, whose analysis ran externally, the Brain Researcher record is a post-hoc audit of the completed multiverse; the cocaine and cross- cultural analyses instead ran within a Brain Researcher episode under prospective gate governance, so their decisions fell to a pre-committed gate rather than to a post-hoc review. Table 8 states, for every reported case, its execution mode, the model that drove it, whether Brain Researcher executed the analysis or only recorded and reviewed it, who wrote the analysis code, and the provenance of its audit files.


> **Table 8: Per-case attribution: execution mode, driving model, and the human/system**

> responsibility split. Every reported analysis case ran in agent-executed mode; the engine-executed
full-bundle protocol is demonstrated on the public Neurosynth example (final row). “BR” denotes
Brain Researcher.

Commitment / audit provenance NeuroMark schizophrenia (Li & Calhoun)

Case Mode Driving model

BR’s role Code author

agent- executed

Cursor / Claude Opus 4.6 (analysis); Codex (exter- nal review)

Recorded and reviewed only; analysis ran in an external workspace

X. Li (agent-

No sealed card; post-hoc audit (pre run commitment card found:

assisted)

false)

Cocaine-use- disorder (Ricard & Poldrack)

agent- executed

Claude Code (Claude Son-

Agent Not sealed (collaborator protocol); run bundle + review verdict

Commitment gate, MCP- mediated cluster ex- ecution, and review; bounded null

net 4.6)

Cross-cultural social cognition (Wang)

agent- executed

Claude Code Reviewed within the episode; gate-blocked as underpowered

Agent Not sealed; gate-blocked (run bundle + review

verdict) HCP workflow search and trans- fer

agent- executed

Claude Code / Codex

Bounded search account- ing, frozen successor analyses, run-bundle review, and claim- boundary enforcement

Agent Prospective episode bun- dles plus frozen successor contracts; retrospective same-cohort inference

TRIBE speech– tools geometry

agent- executed

Claude Code / Codex

Open contrast discovery, researcher-gated succes- sor choice, frozen panel evaluation, and reward- blind closeout

Agent Discovery record plus frozen recurring-source and new-source successor contracts

Neurosynth working-memory (public reference)

engine- executed

None (de- terministic engine)

Executed the sealed episode end to end

BR gener- ator

Sealed pre-run com- mitment card (hash 4871ea43. . . )

49

S11.2.1. Collaborator case results

The three collaborator episodes summarized in the main text are reported here in full; the complete automatically generated per-case reports are reproduced in Appendix L. Each evaluated claim is assigned one of the six review states defined in Supplementary Methods S8.4 (Table 2). The cocaine- use-disorder and cross-cultural episodes were governed by prospective gates, whereas NeuroMark was adjudicated by an explicit post-hoc audit of completed artifacts; in both tiers, the state reflects the applicable evidence criteria rather than the strength of the headline number alone.

NeuroMark: a multiverse separates accepted from qualified claims. A collaborator working on schizophrenia functional network connectivity (FNC) derived from the NeuroMark framework [8] brought three prespecified hypotheses to Brain Researcher for robustness audit: (NM-H1) latent connectivity factors outperform individual FNC edges for patient-versus-control

classification; (NM-H2) between-domain connections show larger group differences than within- domain ones; and (NM-H3) latent factors fitted to edge space concentrate loading mass on between- domain edges. The episode used data from the FBIRN cohort (N = 363; 181 controls, 182 patients) parcellated through NeuroMark 2.2 (a template-based independent-component-analysis framework for FNC estimation) into 5,460 FNC edges per subject. A conventional single-pipeline analysis had supported NM-H2, and the relevant question was whether the hypotheses would survive plausible analytic variation (Fig. 4). The analysis code, specification ledger, and per-hypothesis outputs (including the generated run report and figures) for this case are openly available at https://github.com/XinhuiLi/BR-NeuroMark.

The analysis was expanded into a 480-specification multiverse crossing four connectivity esti- mators, three confound strategies, five dimensionality-reduction methods, four classifiers, and two domain granularities (4 × 3 × 5 × 4 × 2) in the collaborator’s workspace, and Brain Researcher recorded and reviewed the run, which partitioned the hypotheses into distinct claim states. NM-H1 (latent superiority) was qualified: across the 384 latent-evaluable specifications (those that include a

dimensionality-reduction step, so a latent representation exists to compare against edges), edges outperformed latent factors in aggregate (median ∆AUC = −0.032) and only 72 (18.8%) favored latent features, with gains concentrated under ICA, ComBat harmonization, and partial-correlation connectivity. NM-H3 (loading-mass concentration) was qualified and weak overall: 100 of 384 latent specifications (26.0%) favored between-domain loading mass under the corrected direction-aware rule (median Wilcoxon p = 0.054), with factor analysis (45.8%) and PCA (33.3%) more favorable than ICA (12.5%) and NMF (12.5%) (Fig. 4A–C).

The NM-H2 step also exposed a failure mode that the claim record is built to make visible. A server-side fault caused Brain Researcher to fall back to a general-purpose coding agent, which scored a specification as favorable whenever the permutation p < 0.05, regardless of the sign of the effect. Because NM-H2 is directional (between-domain > within-domain), specifications in which within-domain differences were larger were still counted as favorable, so the unaudited multiverse inflated apparent NM-H2 support to near-universal acceptance. The mismatch was not caught automatically by the review layer; a human reviewer identified it by inspecting the code, the output files, and the specification curve directly. Binding the hypothesis statement to the executed statistic and its acceptance rule is what let the sign-blind acceptance criterion, once found, become a standing check rather than a one-off correction. The fallback to a general-purpose agent was the cause but was not itself flagged in the record. Re-running the audit with a sign-aware criterion (favorable when one-sided p < 0.05 and ∆mean|d| > 0) over the 24 unique connectivity–confound–

domain contrasts that actually vary the H2 estimand (after collapsing classifier and reduction duplicates) changed the result: NM-H2 was qualified, with 12 of 24 (50.0%) unique H2 contrasts

50

favorable (median ∆mean|d| = 0.0079). The pooled fraction records the adjudication but is not the informative scientific result: support partitioned completely by connectivity estimator, with Pearson and Spearman at 100% favorable and partial correlation and mutual information at 0%. NM-H2 is therefore estimator-regime–dependent rather than generally robust. The partition does not identify its mechanism because partial correlation and mutual information alter the dependence measure in non-equivalent ways; distinguishing shared covariance from estimator scale, power, or nonlinearity requires targeted follow-up analysis. The qualified state records promotion status, while the estimator support partition records where the evidence divides. This case motivates two checks now added to the review layer: a directionality test that the statistic and its acceptance rule agree with the sign asserted by the hypothesis, and a provenance warning whenever execution falls back from a Brain Researcher operation to a general-purpose agent. The unit of analysis shifted from a completed workflow to an auditable decision space with explicit, condition-tagged claim boundaries; the episode record tied each hypothesis to the analytic regime under which it holds, with review and memory cards in Appendices G–H.

Cocaine-use-disorder. The cocaine-use-disorder episode asked whether reported connectivity– behavior associations in a substance-use cohort remained credible under plausible choices of atlas, motion threshold, and confound strategy. This was a robustness question rather than a search for a new biomarker: the useful output was whether the apparent associations survived a defensible multiverse and, if not, what follow-up design would be needed. On SUDMEX CONN [2] (OpenNeuro ds003346 v1.1.3 [13]; N = 138), the analysis was expanded into a 36-specification multiverse over atlases, framewise-displacement thresholds, and confound strategies. Brain Researcher rejected all five prespecified network-systemic-segregation associations under SDMA-GLS, a procedure that combines same-dataset estimates across specifications [18] (all Z < 1.24, FDR q > 0.58). An exploratory screen over all 70 network-by-outcome combinations likewise yielded no FDR-surviving effects (max ZGLS = 2.18; 0/70 surviving). Brain Researcher blocked the exploratory screen from confirmatory promotion and converted the null result into a replication plan (Fig. 4D,E).

Cross-cultural social cognition. The cross-cultural episode asked whether a small coordinate- based literature could support a mechanistic claim about culture-specific social-cognition topography, or whether the evidence was too sparse and compositionally imbalanced for that interpretation. The agent ran cell-wise activation likelihood estimation [9, 10] on a corpus of 21 published studies (85 MNI peak coordinates, four culture-by-relationship cells) using NiMARE [25]. Some papers

contributed more than one eligible contrast, so the cell counts are cell-level study entries; the unique-paper count remains 21. The agent produced a mechanistic mPFC-topology interpretation (centroid shift 19.5 mm in strangers versus 3.8 mm in close others between Euro-American and East

Asian pools), which Brain Researcher’s review layer blocked as exploratory: cells had only k = 6–8 entries, below the recommended k ≥17 [10]; paradigm composition was imbalanced across cells (the East Asian close-other cell was dominated by self-referential trait-judgment paradigms); and

centroid shifts from aggregate coordinates do not establish non-overlapping activation distributions. The case ended with a paradigm-matched follow-up design and no settled claim (Fig. 4F).

Across the three episodes, Brain Researcher’s contribution was structural and case-general: structured tool specifications made each multiverse mechanical to enumerate and execute; the rule checker kept defensible alternatives inside the same review pass; BR-KG-derived design considerations entered plans as explicit analysis choices; and the episode record stored claims with the conditions under which they held. Fragile, null, or underpowered findings became bounded claims or follow-up designs rather than headline biomarkers.

51

S11.3. Iterative research episode evaluation

This section gives the complete numerical record underlying the two iterative episodes summarized in the main text. The unit of evaluation is the research trajectory: how an exploratory result was converted into a frozen successor analysis, what the successor returned, and where the trajectory stopped. The HCP and TRIBE episodes used different data and estimands and are therefore reported separately rather than reduced to a common success score.

S11.3.1. HCP workflow search and frozen selected workflow follow-up

Search accounting and frozen selected workflow. The HCP episode began from an HCP S1200 search cohort of 326 participants and locally reconstructed counterparts to the five behavioural components of Liu et al. [19]. Two staged search bundles allocated 20 and 96 candidate-evaluation slots, respectively, for a total denominator of 116. All 20 slots in the first bundle and 84 of 96 in the second returned scored results in their parent runs (104/116). The best result in the first bundle had mean cross-validated r = .373 and R2 = −.036; the best scored result in the expanded bundle had r = .487, R2 = .212, and MAE = .690. The remaining 12 slots ended in controller transport exhausted; consequently, the second parent episode was recorded as COMPLETED WITH PROTOCOL FAILURE, with episode valid=false. A separate recovery bundle later computed all 12 missing slots, but did not rewrite or retroactively validate the failed parent episode. The 116 allocated slots, 104 parent-run scored results, 12 transport failures, and separate recovery are therefore retained explicitly rather than collapsed into one clean search denominator.

The development procedure designated the term-116 whole-band coherence-magnitude repre- sentation (cohmag multitaper mean fs-1 fmin-0 fmax-0-5) with cosine-kernel ridge regression and α = 1 as the frozen selected workflow. The frozen selected workflow was chosen during development, not automatically identified as a global champion: the search artifact records automatic champion selected=false. It was frozen before the matched comparison described below.

Cognition comparison. The frozen selected workflow was compared with a locally matched reconstruction of the Liu-style nested prediction procedure, not a paper-exact reproduction or a test of general superiority over Liu et al. The comparison used 244 participants from 243 families and 10 repeated, overlapping, family-grouped 5 × 3 nested-cross-validation splits. Within each split, performance was computed from pooled out-of-fold predictions. The frozen selected workflow exceeded the matched comparator in all 10 splits for correlation and R2, and had lower mean absolute error in all 10. Its median values were r = .332, R2 = .107, and MAE = .768, compared with r = .235, R2 = .009, and MAE = .816 for the matched procedure. Median paired differences were ∆r = .098, ∆R2 = .099, and ∆MAE = −.051; a family-cluster pointwise bootstrap gave a 95% interval of [.011, .177] for ∆r, and the conditional one-sided plus-one test gave p = .006.

These inferential quantities are conditional sensitivity analyses. The frozen selected workflow was selected after Cognition search on the same cohort; the comparison was retrospective and not adjusted for the preceding search; repeated splits overlap and are not independent replications; and target residualization was performed outside the cross-validation folds, so the complete procedure is not strictly leakage-free. A predeclared calibration-repair decision aid also failed: its median held-out calibration slope was within the required range (.945 within [.8, 1.2]), but median ∆R2 = −.004 rather than ≥.02, ∆R2 was positive in 4/10 rather than at least 8/10 repeats, and median ∆MAE = +.004 rather than ≤0. The artifact therefore records scientific acceptance=false.

52

Frozen selected workflow transfer. The frozen selected workflow was then refit separately to four additional Liu component outcomes under the same repeated-split evaluation, without changing its representation, estimator family, or hyperparameter. Table 9 reports all five outcome summaries. The ∆r column is the median paired difference within repeats and therefore need not equal the difference between the two displayed marginal medians.


> **Table 9: HCP frozen selected workflow results across five behavioural outcomes. Values are medians**

> over 10 overlapping repeated splits. Matched denotes the locally matched Liu-style nested procedure;
wins count repeats in which the frozen selected workflow had the larger pooled out-of-fold correlation.
These repeats measure same-cohort stability, not independent replication.

Outcome Frozen selected workflow r Matched r Frozen selected workflow R2 Matched R2 Median ∆r r wins Cognition .332 .235 .107 .009 .098 10/10 Tobacco Use .242 .126 .057 −.029 .100 10/10 Personality–Emotion .075 .006 −.019 −.058 .068 9/10 Illicit Drug Use .122 .008 −.003 −.044 .117 10/10 Mental Health .001 −.062 −.047 −.046 .069 8/10

Across the four additional outcomes, the frozen selected workflow had the larger correlation in 37/40 repeated comparisons; including Cognition gave 47/50. The directional comparison was broader than absolute predictive utility: median R2 was positive only for Cognition and Tobacco Use. For the four transfer outcomes, the raw conditional p values for ∆r were .0004, .0556, .0091, and .1292 for Tobacco Use, Personality–Emotion, Illicit Drug Use, and Mental Health, respectively. The corresponding weak-familywise-error–corrected values were .3338, .6692, .2136, and .6580; none passed correction, and all simultaneous intervals crossed zero. In the wider multiplicity analysis over 20 outcome-by-configuration cells, 16 had positive median ∆r, two had pointwise intervals excluding zero, and none had a simultaneous or weak-FWER-supported effect. Thus the cross-outcome result supports a recurring relative direction under the frozen selected workflow, not a multiplicity-corrected claim of general transfer.

Separate internal holdout and terminal claim state. A later internal holdout used a different, separately frozen workflow on 81 participants and returned r = .232 (p = .0184), R2 = −.075, and MAE = .869. It had no matched comparator and negative R2, so it does not confirm the frozen selected workflow versus matched-procedure result. No external dataset or independent replication was completed. The strongest supported statement is therefore that, conditional on the same-cohort development path, the frozen selected workflow showed a stable relative advantage over the matched procedure across repeated splits, with positive absolute utility concentrated in Cognition and Tobacco Use. It is not an externally confirmed predictive model.

S11.3.2. TRIBE speech–tools discovery and frozen stimulus follow-up

Open six-category discovery. The TRIBE episode began with 48 sounds drawn from four source collections and balanced across six categories: animals, music, nature, speech, tools, and voice. For each of the 15 category pairs, a four-source-fold decoder compared early representations (encoder layers 0, 2, and 4) with later representations (layers 10, 12, and 14). Table 10 reports the

complete descriptive ranking by ∆AUC = AUClate −AUCearly. This was a full technical rerun of the same ordered 48-item panel previously exposed in the terminal run, not an independent new-data replication, and the ranking carried no inferential p value.

Exploratory selection and freezing. The rule-selected top pair, tools–voice, did not yield a coherent cross-collection geometry: later-layer separation was lower in only two of four source

53


> **Table 10: Complete TRIBE six-category discovery ranking. Negative ∆AUC denotes weaker category**

> decoding in later than early layers. Values are descriptive results from the same ordered 48-item
technical-rerun panel.

Rank Category pair Early AUC Late AUC ∆AUC 1 tools–voice .625 .250 −.375 2 music–speech .917 .563 −.354 3 speech–tools .979 .646 −.333 4 animal–speech .958 .792 −.167 5 speech–voice .917 .750 −.167 6 animal–music .271 .417 +.146 7 music–voice .542 .417 −.125 8 animal–tools .479 .583 +.104 9 nature–speech 1.000 .917 −.083 10 music–tools .625 .688 +.063 11 nature–voice .875 .813 −.063 12 music–nature .917 .875 −.042 13 nature–tools .750 .708 −.042 14 animal–nature .854 .833 −.021 15 animal–voice .479 .479 .000

folds, its late-layer contrast axis was not aligned with the frozen reference direction, and the diagnostic label was mixed or unresolved. Speech–tools, ranked third, showed non-negative early signed projection and lower late-layer separation in all four source folds and was la- belled aligned magnitude reduction. This was a post-hoc exploratory diagnostic, not the original screening winner. A researcher explicitly adopted speech–tools in a recorded decision (scientist reward order), after which the contrast, geometry estimand, and analysis rule were

frozen; confirmation and scientific acceptance remained unauthorized.

For the successor panels, ∆ref and ∆eval were the speech-minus-tools centroid vectors in the reference and evaluation panels, and D was the reference panel’s root-mean-square within-category residual dispersion. Normalized separation was S = ∥∆eval∥/D, orientation was C = cos(∆ref, ∆eval), signed projection was G = C S, and the primary change was ∆S = Slate −Searly, predicted to be negative. These are components of one geometric decomposition, not three independent pieces of evidence. The frozen decision also required positive early and late orientation in at least three of four sources and an early reference-decoding AUC above .5.

Three non-overlapping recurring-source panels. Three successor panels each contained 48 previously unused items, with six speech and six tool sounds from each of the same four collections (AudioSet Strong, BBC Sound Effects, FreeSound, and SoundBible). Item identifiers and source

paths had zero overlap across panels. Table 11 reports all 12 collection-by-panel values. All three aggregate ∆S values were negative and each panel met the frozen bounded support rule; 11/12 collection-level values were negative. These panels had no prespecified conventional confidence interval or p value, and the four recurring collections are stability units rather than independent draws from a population of sources.

An exploratory leave-one-item-out diagnostic on R5 clarified the exception. BBC, FreeSound, and SoundBible retained negative ∆S under every item deletion. AudioSet Strong had ∆S = +.0284, a leave-one-out range of [−.3536, +.3324], and six sign changes across 12 deletions. The recurring- source result is therefore best described as a mostly direction-preserving contraction of speech–tools separation with an explicit unstable counterexample, not as universal compression, loss of category

54


> **Table 11: TRIBE recurring-source successor panels. Each cell is late-minus-early normalized speech–**

> tools separation (∆S); negative values indicate contraction in later layers.

Panel Aggregate AudioSet Strong BBC FreeSound SoundBible Outcome R3 −.6937 −.7664 −.8625 −.7177 −.4284 bounded support R4 −.4467 −.5433 −.3985 −.2749 −.5701 bounded support R5 −.5471 +.0284 −.4885 −1.0059 −.7225 bounded support

information, semantic abstraction, or a neural mechanism.

Frozen four-new-source endpoint. The final extension used a score-blind minimax acoustic- balancing procedure to select 48 sounds from four collections not used earlier: DCASE 2013 Office Live, SINGA:PURA, SONYC-UST, and STARSS23. Each source contributed six speech and six tool sounds; the maximum observed absolute standardized acoustic mean difference was .383, below the frozen .5 bound. Table 12 reports the source-level primary results.


> **Table 12: TRIBE frozen new-source endpoint. Negative values are in the predicted direction.**

Collection ∆S ∆AUC DCASE Office Live −.5883 −.0741 SINGA:PURA −.2073 −.0278 SONYC-UST +.0856 +.0926 STARSS23 −.0820 −.0463 Aggregate −.1980 —

Three of four sources were directionally concordant, but the frozen H1 balanced-label permutation test (99,999 permutations) gave raw p = .13212 and Holm-adjusted p = .39636 at α = .025, so H1 was not supported. The three predeclared secondary families were also unsupported: H2 raw/adjusted p = .35200/.39636, H3 .16147/.39636, and H5 .05441/.21764. The inference pertains only to label permutations within this fixed four-source panel; it does not license population-level inference over sound collections. Reward-blind review closed the endpoint as inconclusive or conflicting, with confirmation authorized=false and scientific acceptance=false. The complete TRIBE trajectory therefore contains both results: three recurring-source panels showed repeated, mostly direction-preserving contraction, but the first frozen four-new-source inferential endpoint did not support the primary hypothesis after multiplicity correction.

S11.3.3. Separately initiated same-agent sessions and evidence boundaries

The sessions without Brain Researcher were run separately by the same coding agent and are reported as qualitative process observations, not as matched randomized ablations. The prompts, interaction histories, budgets, human interventions, stopping rules, and opportunities for follow-up were not held identical.

In HCP, the separately initiated session completed a substantial analysis and ended in a valid internally held-out null: adjusted partial r = .141 (p = .261, 95% CI [−.182, .409]), predictive r = .200, incremental R2 = .033, and overall R2 = −.013. It did not launch a frozen successor. In TRIBE, summary/PCA representations gave positive discovery and second-subset shifts (∆ρ = .112, 95% CI [.026, .198], familywise QAP p = .0163; and ∆ρ = .115, 95% CI [.019, .225], p = .00024), but the frozen primary spectrotemporal representation did not reproduce them (∆ρ = −.0036, 95% CI [−.046, .040], p = .7783; and ∆ρ = −.0162, 95% CI [−.063, .032], p = .2484). The prospective firewall and frozen-representation lock were not satisfied, and the authoritative terminal state was

55

TECHNICAL FAILURE, not a confirmed positive or a scientific null. That session also did not launch a successor.

Across both with-Brain-Researcher episodes, repeated splits or recurring collections are stability checks rather than independent replications. HCP remained retrospective, same-cohort, and search- conditional, with no external confirmation. TRIBE’s recurring-source pattern did not survive its first multiplicity-corrected new-source endpoint. Accordingly, self-evolving denotes a governed trajectory in which evidence changes the next frozen analysis; it does not denote autonomous model improvement or scientific confirmation.

S11.3.4. Review-layer calibration

To attach a number to how often the review layer’s triage errs, we scored its severity classification, blind, against the 60-case calibration library (C01–C60; Appendix G, G9.5), whose cases carry an expected verdict for common neuroimaging analysis situations (16 block, 39 warn, 5 allow). The layer’s classification arm produced no false accepts (0 of 16 invalid analyses were waved through as valid; 0%, rule-of-three 95% upper bound 19%; and 0 of the 55 cases warranting any flag were classed allow) and no false blocks (0 of 5 valid controls were blocked, although five controls provide only a loose upper bound). Exact three-way agreement with the expected verdict was 88% (53/60); the seven residual disagreements were all block-versus-warn severity differences. The library was assembled after the directionality check introduced in response to NM-H2 and shares provenance with the review policy. These values are therefore an internal-consistency ceiling over short canonical scenarios, not an independent field error rate or evidence that the pre-patch review layer would have caught NM-H2.

S11.4. Resource usage and user experience

We report token usage, derived cost, and interaction profile for one collaborator episode (a cocaine-

use-disorder resting-state case) as an illustrative reference. Transcripts were not captured for the other collaborator cases, so per-case token accounting is shown for this case only. This episode was run on Claude Sonnet 4.6 and comprised 2,350 assistant turns and 1,347 tool calls (902 Bash, 89 Edit, 64 Read, and 53 Write, plus Model-Context-Protocol calls that included 45 cluster (Slurm) submissions and 41 deep-research queries), spread over roughly six calendar days of interactive use rather than continuous compute.

Tokens are the primary reported quantity, and we present the components separately (Table 13). The episode consumed about 0.89M output tokens, 19.9M cache-creation (cache-write) input tokens, 180.2M cache-read input tokens, and under 0.03M non-cached input tokens. We do not headline the roughly 201M raw token sum: it is dominated by cache reads, an artifact of long-context caching across 2,350 turns, where the persisted episode context is re-read on each turn and billed at roughly one-tenth the standard input rate. The meaningful generation is therefore about 0.89M output tokens plus about 20M cache-creation tokens.

From these token counts we derive an approximate cost at standard Claude Sonnet 4.6 API list prices (input $3, output $15, cache write $3.75, and cache read $0.30 per 1M tokens): about $13 for output, about $75 for cache-creation, about $54 for cache-read, and under $1 for uncached input, for a total of approximately $140 for this single episode. Cost is driven mainly by cache-creation and output rather than by the large cache-read volume. This is an approximate API-list-equivalent figure: actual billing depends on the user’s plan and tier, and subscription plans differ from per-token API pricing.

56

Token component Tokens Approx. cost Output (generation) 0.89M $13 Cache-creation (cache write) 19.9M $75 Cache-read 180.2M $54 Uncached input 0.03M <$1 Total (single episode) ∼201M (raw sum) ∼$140


> **Table 13: Token usage and approximate API-list-equivalent cost for one collaborator episode**

> (cocaine-use-disorder resting-state case, Claude Sonnet 4.6). Components are reported separately;

the raw sum is dominated by cache reads (billed at roughly one-tenth the input rate) and is not the headline quantity. Costs are derived from the per-component token counts at standard list prices (input $3, output $15, cache write $3.75, cache read $0.30 per 1M tokens) and are approximate;

actual billing depends on the user’s plan and tier.

Usage scales with how much the user reviews generated code rather than only reading it, and it varies by model and tier. In practice the binding constraint is high token throughput rather than marginal cost: throughput alone can exhaust a standard plan, and one collaborator case accordingly required a higher-tier plan.

In this episode, the user supplied fMRIPrep-preprocessed SUDMEX resting-state data and asked, exploratorily, how to analyse individual functional networks given a limited cross-sectional sample. Brain Researcher resolved this request into a typed episode (dataset and target functional networks) and committed a 36-specification multiverse at the commitment gate; the agent executed it on a cluster backend through Brain Researcher’s submission tools, and Brain Researcher reviewed the resulting run bundle and returned a bounded null claim. In a post-hoc self-assessment, the collaborator on this case estimated that Brain Researcher saved on the order of three months of analysis time relative to assembling and running the equivalent multiverse by hand. The division of responsibility between the researcher and the system across this flow follows the human-agent authority boundary (Fig. S2).

S11.5. Analysis-level methods provenance (COBIDAS-style)

Brain Researcher did not acquire MRI data or run raw-image preprocessing for any reported case. It operates at the analysis and statistical-inference level, on already-preprocessed derivatives (functional- connectivity matrices, fMRIPrep outputs, minimally-preprocessed connectomes) or on published coordinates and reference maps. Acquisition and image-preprocessing provenance is therefore inherited from the cited source datasets and is not re-derived here; the acquisition/preprocessing column of Table 14 records the origin of each derivative rather than a pipeline Brain Researcher executed. What the system records for every case is the available analysis-level provenance: the estimator, statistical model, inference and multiple-comparison procedure, robustness or multiverse design, applicable prospective gates or post-hoc review criteria, and the resulting claim state. These fields are written to the case’s run or audit bundle (S7.4), including available software identity and versions, random seeds, and the specification ledger. Table 14 summarizes this analysis-relevant subset of the COBIDAS reporting standard [22] across the five reported episodes; per-case reports (Appendix L) and the specification ledgers (Appendix F) carry the complete records.

57


> **Table 14: Analysis-level methods provenance across the five**

> reported episodes (COBIDAS-style). Brain Researcher performs
no raw acquisition or image preprocessing; the acquisition/preprocessing
column records the origin of the derivatives or coordinates each episode
consumed. All remaining columns describe analysis-level choices that
Brain Researcher recorded and reviewed, with prospective commitment
gates applied where applicable (S7.4); the compute itself was executed
by the agent, except in the engine-executed Neurosynth reference. Full
per-case records are in Appendices F and L.

Episode (data, N)

Acquisition / preprocessing origin

Features & estima- tor

Statistical model, in- ference & correction

Claim state(s)

Robustness / review crite- ria

NeuroMark / schizophre-

NeuroMark 2.2 template-ICA FNC derivatives (framework/collaborator-

5,460 FNC edges, two domain gran- ularities; four con- nectivity estimators (Pearson, Spearman,

480- specification multiverse (4×3×5×4×2);

NM-H1 qual- ified; NM-H2 qualified; NM-H3 quali- fied

Patient-vs-control classifi- cation (AUC) and group- difference contrasts; one-sided permutation test with sign-aware acceptance (p < 0.05 and ∆mean|d| > 0); Wilcoxon test for loading mass

nia FNC (FBIRN;

N = 363, 181 control / 182 patient)

384 latent- evaluable; 24 unique sign- aware H2 con- trasts

provided) [8]

partial correlation, mutual information); five dimensionality- reduction methods; four classifiers

Cocaine-use- disorder connectiv- ity (SUD- MEX CONN, OpenNeuro ds003346 v1.1.3; N = 138)

fMRIPrep derivatives, collaborator- supplied [2]

Network segregation; atlas varied across specifications; same- data meta-analysis (SDMA-GLS) [18]

Connectivity–behavior associations; FDR correction (confirma- tory all Z < 1.24, q > 0.58; exploratory max ZGLS = 2.18, 0/70)

36- specification multiverse (atlas ×


## 5 confirma-

tory rejected;
exploratory
screen
blocked

framewise- displacement threshold × confound); 70- combination exploratory screen

Cross- cultural so- cial cognition (coordinate

Published MNI peak coordinates (no raw imaging

Cell-wise activation- likelihood estimation (ALE), NiMARE [25]

ALE with per-cell k = 6– 8 (below recommended k ≥17 [10]); centroid shift reported as descrip- tive only

Paradigm- composition imbalance check across four culture- by-relationship cells

mPFC- topology interpretation blocked as exploratory

data)

literature; 21 studies, 85 peaks)

58

Episode (data, N)

Acquisition / preprocessing origin

Features & estima- tor

Statistical model, in- ference & correction

Claim state(s)

Robustness / review crite- ria

HCP-YA be- havioural prediction (search cohort

The frozen selected work- flow exceeded the matched compara- tor in 10/10 Cognition splits; 47/50 directional wins across five out- comes, but no transfer cell passed weak-FWER; separate hold- out did not confirm; no external ac- ceptance TRIBE speech–tools representa- tion geometry (TRIBE v2;

HCP S1200 minimally- preprocessed connectomes and locally re- constructed Liu-component counterparts [19, 30]

116 allocated can- didate evaluations; frozen selected workflow using a coherence-magnitude representation with cosine-kernel ridge regression; locally matched Liu-style nested comparator

Ten repeated family- grouped 5 × 3 nested-CV splits with pooled out- of-fold metrics; family- cluster pointwise boot- strap and conditional one-sided test; weak- FWER transfer analysis

104/116 parent-run scores plus 12 recorded transport fail- ures and sepa- rate recovery; frozen selected workflow refits across out- comes; retro- spective same- cohort, search- unadjusted sensitivity

N = 326; matched comparison N = 244, 243 families; internal hold- out N = 81)

No subject-level BOLD; model- representation analysis over six sound categories, four recurring collections, and four previously unused collec- tions [7]

Early-versus-late encoder decoding and frozen geomet- ric decomposition of normalized separa- tion, orientation, and signed projection

Descriptive 15-pair discovery; three non- overlapping recurring- source panels; 99,999 balanced-label permu- tations and Holm cor- rection at the frozen four-new-source endpoint

Researcher- authorized post-hoc choice of speech–tools; frozen esti- mand; item non-overlap; score-blind acoustic balancing; collection- specific and leave-one-out diagnostics

Recurring- source bounded support in 3/3 panels (11/12 cells),

discovery and successor pan- els of natural sounds)

followed by unsupported new-source H1 (Holm p = .396); terminal outcome in- conclusive or conflicting; no scientific acceptance

S12. Limitations and reporting boundaries

Brain Researcher verifies whether an analysis package satisfies declared validity constraints, produces required artifacts, and calibrates claims to available evidence. It does not prove biological truth, replace expert scientific judgment, or replace independent replication.

59

Limitation domain What can go wrong Reporting boundary Knowledge graph Incomplete negative knowledge, uneven graph density, source-specific gaps, sparse higher-tier evidence.

Evidence tier and coverage caveats are reported.

Evidence connectors Slow or failed connectors reduce coverage. Failures are logged and may trigger caveats; they are not treated as absence of evidence. Planning and con- straints

Incomplete automated power analysis, lim- ited interactive replanning during execution, missing persistent rejection rationales in some workflows.

Constraint state and planning limitations are recorded.

Non-executable outcomes and backend failures are retained. Review Rule registry is heuristic, not formal verifi- cation. It may miss subtle domain errors or over-warn on unusual valid methods.

Execution Dataset-access constraints, missing derivatives, backend failures, and weaker provenance for real-time paths.

Review verdicts reduce obvious errors but do not prove truth. Benchmark construc- tion

Scoring contracts, refer- ence answers, and prove- nance files are released for independent re-scoring; benchmark results are re- ported as upstream-input gains rather than scientific conclusions and use three condition-blind judges combined by majority vote. Routing-ablation scope This seven-model ablation evaluates exact- label top-1 route selection with direct KG- named calls unavailable.

Tool-calling and evidence-citation items and their reference answers are internally curated and scored by LLM judges, so they may em- bed designer assumptions and LLM-judge bi- ases, including self-preference where the agent and a judge share a model family.

Report 362/420 sep- arately from Correct route/tool@1, which has a different scoring contract. Memory Similarity-based retrieval and critic relation classification can err; partition enforcement is required.

Memory is append-only and partitioned during evaluation. Bounded autonomy Harbor reward can reflect file/schema/statistic completion without scientific validity.

Scientific acceptance still requires Brain Researcher review and claim calibra- tion. Hypothesis triage Sparse-coverage domains can produce plausible but generic semantic permutations.

Used for expert-in-the- loop ideation, not au- tonomous novelty or truth claims. Governance IRB, DUA, licensing, and institutional compli- ance remain investigator responsibilities.

BR can record blockers but does not replace hu- man compliance review.

Four further boundaries are not fully captured by the table above. First, evidence-support judgments rely on LLM judges; we report inter-judge agreement (three-judge Fleiss’ κ = 0.50 with-BR, 0.72 without-BR; S11.1.2) and a reproducible 272-item hand audit (S11.1.3) but did not perform full-scale human-expert re-labeling of all judge outputs, so a residual gap between LLM and

60

human judgment cannot be ruled out. Second, the absolute level of verified groundedness remains low (0.22 with BR under a three-judge majority vote): the benchmark demonstrates a between-condition

improvement, not a solved grounding problem. Third, we did not run a randomized user study and did not directly measure runtime or researcher effort; statements about reduced workflow friction are expected consequences of absorbing the execution layer rather than measured outcomes. Fourth, the foundation models and provider APIs used are evolving, and although every reported claim is fixed to recorded model versions and snapshots (S1.2), exact behaviour may not be reproducible once providers retire or update those versions.

Review labels create a separate risk of automation complacency. A “BR-reviewed” status means only that the formalized conditions active for that review were checked; it is not expert endorsement or evidence that errors outside those conditions are absent. NM-H2 illustrates this boundary: automated review missed a sign-blind acceptance rule that direct inspection revealed. We did not measure whether the approving outcome reduced scrutiny, but treating such labels as conclusive could discourage the inspection needed to identify failures outside implemented checks. Human inspection therefore remains necessary, especially for claim–method alignment and other judgments not yet formalized.

Capabilities not evaluated in the reported protocol should not be used as evidence for the main claims. These include adaptive optimization modules, community contribution pathways, planned cross-modal fMRI-to-concept alignment, and autonomous scientific-discovery claims beyond the bounded validation contracts explicitly reported.

Appendix / Data Card Overview

Appendix A. Episode and control-plane card

The full episode/control-plane ledger is released in the archival repository (run-bundle schemas and

provenance fields; Data availability); the card below is the summary of its fields.

The episode/control-plane card records the fixed identity and configuration of an episode: episode ID, mode, scientific question, model version, prompt-template version, registry snapshot, BR-KG snapshot, policy flags, MCP operation summary, memory namespace, checkpoint events, recovery events, run state, and completion status.

Example excerpt:

episode_id: ep_hcp_predict_001 mode: benchmark state: completed_with_qualifications registry_snapshot: registry_2026_05_15 brkg_snapshot: brkg_2026_05_10 memory_namespace: benchmark_isolated

Appendix B. Evidence bundle / BR-KG card

The full BR-KG atlas and evidence-bundle ledger (graph snapshots, node/edge schemas, source-

coverage and provenance tables, and the atlas figure panels) is released in the archival repository (Data availability). The card below retains the evidence-bundle schema and one worked method-condition record, the object the main text points to for a source’s verbatim quote and grounding label.

The evidence bundle card records input query, resolved entities, ONVOC mappings, evidence tiers, graph paths, literature retrieval outputs, connector failures, dataset links, tool links, prior findings, method-condition records, coverage notes, and embedding-lane metadata.

Example excerpt:

61

resolved_entities:

dataset: HCP-YA feature_space: Schaefer100x7 evidence_tiers:

- accepted_graph_record - real_time_retrieval connector_failures:

- PubMed_timeout graph_path:

- Dataset:HCP-YA - HAS_FEATURE_SPACE:Schaefer100x7 - REQUIRES:fold_manifest method_condition_record: # one source-supported claim, field by field claim: "resting-state FC predicts a fluid-intelligence component" cohort_sample_size: "N=1003" task_paradigm: resting_state preprocessing: "ICA-FIX + 24-parameter motion regression" statistical_model: "ridge regression, family-aware cross-validation" grounding_label: br_kg_gabriel_cache_candidate verbatim_quote: "connectome-based models predicted a general

intelligence factor (r approx 0.29) with leave-one-family-out CV"

Appendix C. Dataset/resource card

The full per-dataset readiness ledger is released in the archival repository (dataset records and

provenance fields; Data availability); the card below is the summary of its fields.

The dataset/resource card records dataset identifier, aliases, access class, local or remote path, BIDS root, derivative root, phenotype manifest, target variables, covariates, missing derivatives, backend reachability, readiness status, and blocker status. It includes at least one pass example and one block example.

Appendix D. Tool registry and specification ledger card

The full tool-registry, candidate-ranking, and specification ledger is released in the archival repos-

itory (registry links and scoring tables; Data availability); the card below is the summary with a representative candidate-accounting excerpt.

The tool registry card records family cards, ranked tool candidates, rejected candidates, canonical IDs, backend recipes, parameter schemas, tool-contract clauses, compatibility checks, Neurodesk mappings, registry snapshot identifiers, allowlist mode, and embedding-lane metadata.

Example candidate accounting:

Candidate Decision Reason predictive modeling family accepted Input resources and expected outputs match. whole brain glm rejected Wrong output type for prediction target. dynamic fc family rejected Missing time-series asset.

Appendix E. Constraint and commitment card

The full constraint-compiler and commitment-gate record is released in the archival repository (Data

availability); the card below is the summary of its fields.

The constraint/commitment card records active constraints, hard checks, soft checks, rule provenance, pass/warn/block verdicts, required sensitivity analyses, gate authority, commitment decision, and benchmark pass-through flag.

62

Appendix F. Run bundle and provenance card

The full run-bundle and provenance ledger, including a worked claim-record example, is released in

the archival repository (run-bundle schemas and provenance fields; Data availability); the card below is the summary of its fields.

The run-bundle card records event trace, trajectory document, observation record, analysis bundle, run card, expected artifacts, produced artifacts, missing artifacts, checksums, backend versions, software versions, container or module identifiers, preflight results, failures, retries, recovery events, and final execution status.

Appendix G. Review card

The review card records verification inputs, deterministic checks, BLOCK findings, WARN findings, robustness checks, sensitivity checks, claim families, verdicts, caveat language, revision routing, claim eligibility, and artifact-completeness ratio. Each revise or block verdict identifies the triggering artifact or assumption, rule ID, hard/soft status, and evidence needed for resolution.

Appendix H. Memory card

The full memory, claim-relation, and BR-KG-promotion ledger is released in the archival repository (Data availability); the card below is the summary of its fields.

The memory card records claim text, polarity, condition vector, review verdict, caveats, prove- nance pointer, related prior claims, relation type, relation confidence, stable key, memory namespace, writeback eligibility, and BR-KG promotion status. Accepted, qualified, and rejected outcomes are shown separately so readers can see what does and does not enter accepted memory.

Appendix I. Operational-mode card

The operational-mode card records interactive gate records, bounded instruction file, action vo- cabulary, budget, stopping criteria, validation ladder, supervisor decisions, critic decisions, Harbor verifier outputs, reward or partial-credit metrics, escalation events, final termination status, and memory-writeback decision.

Appendix J. Evaluation card

The evaluation card records benchmark suite list, task manifests, scoring contracts, model list, with-BR/without-BR protocol, memory partition policy, collaborator case table, bounded campaign contract, metric denominators, secondary metrics, ablation protocols, and excluded or non-executable cases. The card states whether scoring used binary success, partial credit, or both.

Case-report skeleton for later appendix expansion

Each case report uses the same skeleton:

63

Step Case-report element 1 Question. 2 Dataset/resource status. 3 Tool pathway. 4 Constraints and commitment gate. 5 Execution artifacts. 6 Review verdict. 7 Final claim language. 8 Human/system responsibility split. 9 Memory writeback status.

This skeleton documents the reporting contract for the case-report appendices. Apart from the representative generated-code excerpt in Appendix K, the automatically generated reports released through Appendix L are frozen audit artifacts. The earlier HCP retention-gate and TRIBE language-alignment reports are historical records of separate campaigns and do not supply the current iterative-episode results. The operative current results are those in Supplementary Methods S11.2–S11.3 and Appendix J.

64

Appendix/Data Cards

Appendix G. Scientific review, BLOCK/WARN findings, and claim- calibration card

Appendix G is the scientific review ledger: it consumes the run bundle and decides whether artifacts and candidate claims are accepted, qualified, revised, blocked, rejected, or deferred, with unresolved cases escalated for expert judgment.

G1. Purpose and scope

This card records the scientific review outcome for an episode. It consumes the selected plan, active constraints, execution trace, artifact manifest, logs, QC outputs, scorecards, candidate claims, and prior evidence. It reports deterministic checks, BLOCK and WARN findings, robustness and sensitivity coverage, claim-calibration decisions, final verdicts, caveat language, revision routing, and claim eligibility.

G2. Review input manifest

Input Source appendix Status Selected plan Appendix D/E present Active constraints Appendix E present Run bundle Appendix F present Artifact manifest Appendix F present Logs/errors/warnings Appendix F present Scorecard and QC outputs Appendix F present Prior evidence / graph paths Appendix B present Dataset/resource ledger Appendix C present

Important boundary: review consumes the run bundle, not the model transcript alone.

G3. Validity-layer matrix

Validity layer Review question Example checks Statistical validity Is the inference valid? exchangeability; multiple compar- isons; permutation/null Measurement validity Are data and QC adequate? motion; registration; QC; reliability Construct validity Does the measure support the construct?

task/construct mapping; reverse inference risk Generalization validity Does the result generalize? leakage; grouped CV; held-out/ external support Claim validity Is language calibrated? no causal/biomarker/external claim without evidence

G4. Review rule registry excerpt and lifecycle status

The review registry separates rule severity from implementation lifecycle. Severity determines what a triggered rule does to a candidate claim. Lifecycle status records whether the rule is already

65

operational, can be implemented from structured metadata, requires additional review-context fields, requires text interpretation, or is used only for calibration and reviewer training.

Lifecycle status Meaning How it is reported Implemented The rule is operational in the review system for the required metadata fields.

May support an enforced BLOCK or WARN verdict. Deterministic candidate The rule can likely be implemented from structured metadata, manifests, or pipeline logs.

Reported as a candidate check unless the episode records enforcement. Schema-dependent candi- date

The rule requires additional review-context fields before deterministic enforcement.

Reported as a missing-field or protocol requirement. NLP/LLM candidate The rule requires text interpretation, claim extraction, or semantic comparison.

Reported as assisted review or calibration unless indepen- dently verified. Calibration-only The rule is used for examples, annotator training, or benchmark calibration.

Does not by itself produce an enforced verdict.

Rule ID Severity Validity layer / rea- son tag

Default action

feature selection outside cv BLOCK generalization / leakage revise or block uncorrected whole brain inference

BLOCK statistical / multiple comparisons

revise or block

same data roi definition BLOCK circularity block gsr without sensitivity WARN measurement / contro- versial choice

sensitivity or caveat

small sample biomarker claim WARN claim / claim inflation downgrade claim missing random seed WARN reproducibility / report- ing gap

report or fix

review rule: rule id: feature selection outside cv severity: BLOCK validity layer: generalization reason tags: - leakage

detection field: pipeline dag trigger: feature selection fit before cv split default action: revise or block required fix: ”Move feature selection inside the cross-validation loop.”

G5. BLOCK findings and WARN findings

Finding type Examples Consequence BLOCK leakage outside CV; invalid null; circular ROI; uncorrected whole- brain inference

Cannot accept until resolved.

WARN external validation missing; GSR unresolved; small sample; missing seed; partial QC

May accept with caveats, sensitiv- ity, or downgraded claim.

block findings: [] block status: none detected

66

warn findings: - rule id: external validation missing

validity layer: generalization reason tag: claim inflation status: unresolved required caveat: ”Internal validation only; no external generalization claim.”

G5.1 Common review failure modes and default actions

The review card is easier to interpret if the rule registry is read as a set of common failure modes. These rows are not additional rules; they translate frequent neuroimaging review problems into the evidence the reviewer expects, the default BLOCK or WARN action, and the claim-language change that follows.

Failure mode Evidence inspected Default action Claim-language effect Leakage outside cross- validation

Pipeline DAG, fit scope for feature selection, scaling, PCA, harmonization, or confound regression, and fold manifest.

BLOCK until the fitting step is moved inside the training fold.

No generaliza- tion, prediction, or biomarker claim.

Circular ROI or feature definition

ROI provenance, localizer source, contrast identity, dataset identity, and whether the same data also test the effect.

BLOCK unless an independent localizer, atlas, or non-circular provenance is sup- plied.

No confirmatory effect claim.

Invalid whole-brain or map-level inference

Correction method, correction domain, primary threshold, per- mutation or spatial-null frame- work, and file space.

BLOCK for uncor- rected whole-brain tests, spatial-domain mismatch, or missing spatial null.

Only descriptive or exploratory language remains.

Unresolved controversial preprocessing choice

Preprocessing record and sensitivity coverage for GSR, dynamic FC windows, graph thresholds, HRF model, or har- monization.

Claim is qualified to the tested preprocess- ing choices.

WARN with required sensitivity analysis.

WARN or DEFER, depending on whether internal support is sufficient.

No external general- ization or deployment claim.

Missing external or held- out validation

Validation ladder, held-out split, external dataset availability, post-selection correction, and resource-gate status.

Overstated interpreta- tion

Candidate claim text, evidence type, behavioral covariates, out- of-sample evidence, ablations, and alternatives considered.

WARN with claim downgrade.

Prediction, causal, mechanistic, or reverse-inference lan- guage is removed unless directly sup- ported.

G6. Robustness, sensitivity, and artifact review

Check Required by Claim effect with/without GSR controversial-choice rule qualified if not performed or unstable parcellation sensitivity validation ladder supports robustness level if stable confound model sensitivity review rule or soft constraint caveat if attenuated

67

Check Required by Claim effect permutation/null check hard statistical validity accept/block depending on result post-selection correction replayed configurations accept/block depending on result external dataset validation L4 ladder no external claim if deferred

Artifact class Required for review? Review consequence if miss- ing Scorecard yes review not ready or revise Predictions yes for prediction statistical review incomplete Null-test output yes if claimed revise/block Config manifest yes reproducibility warning or revise QC report yes or conditional measurement WARN

artifact review: expected artifacts: 6 produced artifacts: 6 artifact completeness ratio: 1.00 review ready: true

G7. Claim-family and claim-calibration table

Candidate claim Overclaim blocked Allowed language Model predicts behavior clinical biomarker internally validated predictive association FC is associated with score causal mechanism exploratory or condition-qualified association Result robust to parcellation external validity robustness under tested specifica- tions Null-control passed biological truth leakage/null-controlled internal result

G8. Final review verdict and revision routing

Verdict Meaning Next action accept Artifacts and claims satisfy active constraints.

Eligible for memory.

accept with qualifications Result usable only with caveats. Qualified memory claim. revise Fixable issue remains. Return to planning or execution. block Hard validity failure. Stop or redesign. reject Claim unsupported or contra- dicted.

No writeback.

escalate Human expert needed. Pause or route.

review card: episode id: ep hcp predict 001 run id: run hcp pathb 001 verdict: accept with qualifications

block findings: []

68

warn findings: - external validation missing

robustness checks: family block permutation: pass post selection correction: pass external validation: deferred

claim calibration: allowed claim strength: ”validated internal result” prohibited claims: - ”externally validated biomarker” - ”causal mechanism” - ”clinical prediction claim”

memory eligibility: qualified claim only

69

G9. Scientific review rule registry (release) and calibration library

This appendix gives the reader-facing view of the scientific review rule registry used to define, cali- brate, and prioritize Brain Researcher’s verification layer. The full per-rule registry, its organization fields, rule families, encoded policy decisions, implementation priority queue, and review-context fields and sensitivity templates, is released as a machine-readable file in the archival repository (Data availability), so it is not reprinted here. A rule’s presence in the released registry does not

mean that it is enforced in every episode; the lifecycle table in G4 distinguishes implemented rules, deterministic candidates, schema-dependent candidates, text-interpretation candidates, and calibration-only cases. Retained below is the calibration case library (G9.5), because the main text points to it for the first false-accept and false-block accounting.

G9.5 Calibration case library

The registry includes 60 calibration cases (C01–C60) for annotator training and regression testing. They are summarized by rule family here; the machine-readable release contains the case-level labels, severity, novelty flag, and rule identifiers.

Cases Scenarios covered Typical label C01–C06 Repeated-measures, mixed-design, longitu- dinal, and spatial-domain errors, plus valid paired-test and motor-task controls.

BLOCK for invalid design or spatial cor- rection; allow for valid controls. C07–C12 Extreme or unexpected effects, ordinary mor- phometry effects, motion-confounded small- sample FC, and expected task activation.

WARN for prior con- flict or confounding; allow for expected, well-scoped effects. C13–C24 Whole-brain correction, cluster-threshold, lo- calization, double-dipping, ROI multiplicity, analytic flexibility, pseudoreplication, fixed- effects population claims, exchangeability, and spatial-null examples.

BLOCK for hard in- ference errors; WARN for soft multiplicity or reporting issues.

C25–C36 Motion reporting, motion imbalance, global signal regression, dynamic FC, graph thresh- olding, task FC/PPI, EPI distortion, MRIQC, small sample, missing external validation, and multiband QC.

WARN except for high- confidence motion con- founds that block infer- ence.

C37–C41 Reverse inference, stimulus generalization, missing behavioral covariates, ICV/TIV omis- sion, and multi-site site confounding.

WARN with claim nar- rowing or added covari- ates/sensitivity. C42–C55 Harmonization, feature selection, standardiza- tion, test-set selection, split grouping, permu- tation, fold-wise error, prediction language, temporal splits, post-hoc layer selection, RSA multiplicity and hierarchy, and missing ICC.

BLOCK for leak- age and test-set use; WARN for missing reli-

ability, uncertainty, or permutation support.

70

C56–C60 Extreme effects, single-pipeline significance, COBIDAS fields, BIDS validation, and BIDS Stats Models reporting.

WARN for incomplete robustness or report- ing; allow/positive modifier for structured reporting.

71

Appendix I. Operational-mode, bounded-episode, and Harbor-based validation card

Appendix I is the operational control trace: it records how an episode or campaign was bounded, budgeted, advanced, verified, stopped, escalated, and permitted or denied memory writeback. The bounded self-evolving and loop-closure schematics are summarized in Supplementary Figs. S11–S13.

I1. Purpose and scope

This card records the operational mode and control contract for interactive, benchmark, collaborator- facing, and bounded autonomous episodes. It is especially important for Harbor-based validation and supervisor/critic cycles. Harbor verification is recorded as task-level execution evidence, not scientific acceptance.

I2. Operational-mode identity

Field Recommended entry Episode or campaign ID ep hcp predict 001 / campaign autonomous 001 Mode interactive / benchmark / collaborator / bounded autonomous Gate authority human researcher / evaluation harness / critic / super- visor Instruction or task contract instruction.md / bounded episode contract.yaml Allowed resources dataset/resource IDs and approved roots Action vocabulary search, plan, run, inspect, review, branch, stop Budget cycle, compute, wall-clock, retry, or token budget Stopping criteria success, unresolved block, no progress, budget ex- hausted, escalation

I3. Bounded episode contract

Contract field What it records Target question The scientific objective for the bounded episode. Admissible design space Which analyses and branches are allowed. Cycle budget Maximum number of supervisor/critic cycles. Expected artifacts Files and records required for verification/review. Validation ladder Target and achieved L0-L5 level. Review rules BLOCK/WARN rules required for acceptance. Memory policy accepted only / qualified only / no write. Escalation conditions When to route to a human researcher.

operational mode card: episode id: ep hcp predict 001 mode: bounded autonomous gate authority: critic action vocabulary: - resolve dataset - select workflow

72

- run analysis - inspect artifacts - request review - branch sensitivity - terminate

budgets: cycle budget: 3 wall clock budget: fixed compute budget: fixed

stopping criteria: - validation ladder reached - hard review block unresolved - no progress after cycle limit - compute budget exhausted - human escalation required

I4. Supervisor/critic decisions and Harbor verifier output

Record Recommended fields Branch-decision record branch type; reason; proposed action; expected resolution; budget cost Critic decision continue / investigate anomaly / broaden / revise / escalate / terminate Harbor verifier output artifact manifest present; required statistic present; schema valid; command completed; reward or partial credit Validation-ladder status highest achieved level and unmet next gate Termination status completed / blocked / budget exhausted / escalated / terminated

harbor verifier: artifact manifest present: true required statistic present: true schema valid: true command completed: true partial credit: 0.8

critic decision: decision: terminate with qualified claim reason: ”L3 internal validation reached; external validation deferred.”

final status: completed with qualifications memory writeback allowed: qualified claim only

73

Appendix J. Evaluation protocol, scoring contracts, and metric ledger

Appendix J records the evaluation protocol used for the quantitative benchmarks, collaborator cases, and bounded self-evolving campaigns reported in the main text. It defines the evaluated surfaces, condition comparisons, metric denominators, and aggregate values used in main-text Fig. 3. The benchmark surfaces are reported separately because tool calling and evidence citation have different item types, denominators, scoring rules, and ceilings.

J1. Evaluation surfaces

Surface Unit What is evaluated Tool-calling benchmark 60 neuroimaging task manifests; seven models per condition; 420 model-item trajectories per condi- tion.

Whether a model maps a natural- language neuroimaging request to the correct analysis tool or executable route before execution. Routing ablation without direct KG calls

Same 60-task manifest; seven model routes; 420 route–task episodes.

Exact-label top-1 route selection when direct KG-named calls are unavailable.

Evidence-citation bench- mark

Whether model-generated neuroimag- ing claims cite evidence that can be located and judged supportive by three condition-blind LLM judges (Claude Opus 4.8, Codex GPT-5.5, and Gemini 3.1 Pro). All reference-bearing rows were sent to all three judges; a row entered the numerator when at least two judges voted verified, while every generated evidence-basis row remained in the denominator. Collaborator cases Three active scientific questions from collaborating researchers.

76-item open-ended Neuroimage- Knowledge manifest; descriptive Results aggregate reported on a 50-question analysis set over all generated evidence-basis rows.

Whether Brain Researcher returns bounded claim records rather than unqualified findings. Bounded self-evolving cam- paigns

Two predeclared episode contracts. Whether fixed validation gates re- ject, defer, or revise claims during exploratory search.

J2. Benchmark conditions and model matrix

Both quantitative benchmarks compare with-BR and without-BR conditions on the same task or question set. The tool-calling benchmark is paired at the model–item level. The evidence-citation headline is instead a descriptive question-level aggregate over all generated evidence-basis rows; only rows receiving at least two verified votes contribute to the numerator, and it is not treated as a seven- model paired estimate. Benchmark memory was isolated from collaborator and bounded-campaign memory, and no benchmark item was promoted as a scientific claim.

Field Entry Conditions Without-BR baseline; with-BR condition. Model variants Claude Code / Claude Opus 4.8; Codex GPT-5.5; Gemini 3.1 Pro; GLM- 5.1; DeepSeek-V4-Pro; Kimi K2.5; Qwen3.6-Plus.

74

Field Entry Tool-calling items Natural-language neuroimaging requests requiring an analysis tool call or executable route with the required inputs available before execution. Evidence-citation item fami- lies

Open-ended neuroimaging review questions covering preprocessing, statisti- cal inference, functional connectivity, multivariate decoding, meta-analysis, and reproducibility. Isolation policy Benchmark runs use fixed task manifests, fixed scoring contracts, and isolated memory partitions.

J2a. Tool-calling benchmark scoring summary

The tool-calling benchmark is retained as an aggregate routing surface, but the prompt manifest is not reproduced in the appendix. Each item supplied the agent with a short routing request; the reference route and capabilities were held out for scoring. The scoring contract credits any response that covers the required capabilities, whether through a Brain Researcher call or an equivalent executable route. The release bundle records the exact prompt surfaces and provenance files for independent re-scoring.

J2b. NeuroimageKnowledge benchmark manifests (released)

The full NeuroimageKnowledge groundable item manifest (the open-ended scenarios passed to the benchmark harness), representative paired with-BR/without-BR answers, the unified benchmark- bundle artifact inventory, and representative benchmark cases are released as machine-readable manifests in the benchmark package (Data availability), so they are not reprinted here. These manifests document the paired prompts used to elicit answers and evidence-basis rows under both conditions; they are not used for automatic correctness scoring, and the reported 50-question aggregate is defined by the scoring contracts below. Representative paired examples illustrate the interpretation used in the Results: strong models often answer canonical methods questions well without BR, while BR changes the evidence boundary by adding resolvable, source-supported rows, including cases where the without-BR answer wins the paired judgment because a memory-based citation resolves and supports the claim.

J3. Scoring contracts and denominators

Metric Numerator Denominator Capability@k Fraction of required task capabilities covered by the selected call or route after the first k non-neutral actions.

Model-item trajectories in the tool-calling benchmark; values are averaged as cover- age scores. Correct route/tool@k Tasks that reach exact task success under the capability scorer after the first k non-neutral actions.

All tool-calling model-item trajectories.

Restricted-interface exact-label top-1

All 60 task-route episodes; gold candidate availability is reported separately as an oracle-coverage diagnostic. Handoff score@k Selected call or route contains enough information for a receiving agent to continue the analysis after the first k non-neutral actions.

Requested routes with an ex- act top-1 label match under route search→tool search; proto- col violations count as errors.

Tool-calling trajectories with parsed actions.

75

Metric Numerator Denominator verified groundedness rate Evidence items whose cited evidence is both locatable and judged supportive.

All evidence-basis rows gen- erated for each question, followed by an equal-weight mean across the 50 ques- tions. verified among claimed grounded Model-claimed grounded items whose cited evidence is both locatable and judged supportive.

Model-claimed grounded items.

citation spam rate Model-claimed grounded items whose cited evidence is judged unrelated to the claim.

Model-claimed grounded items.

answer correctness rate Answers passing the rubric-based source sanity check.

Scored NeuroimageKnowl- edge outputs with parseable answer fields.

J4. Aggregate benchmark values reported in Fig. 3

Metric Without BR With BR Direction Capability@1 (all tool-calling trajecto- ries)

0.498 0.945 Higher

Correct route/tool@1 0.233 0.936 Higher Handoff score@1 0.474 0.761 Higher verified groundedness rate (three- judge majority; 50-question mean)

0.046 0.220 Higher

verified groundedness rate (Gemini 3.1 Pro recovered judge; 50-question mean)

0.0435 0.2097 Higher

verified groundedness rate (Codex GPT-5.5 judge; 50-question mean)

0.0389 0.3088 Higher

verified groundedness rate (Claude Opus 4.8 judge; 50-question mean)

0.0796 0.2187 Higher

0.273 0.583 Higher

verified among claimed grounded (Gemini 2.5 Flash single-judge safeguard;

by-model mean)

citation spam rate (Gemini 2.5 Flash single-judge safeguard; by-model mean)

0.317 0.249 Lower

answer correctness rate (rubric-based safeguard; by-model mean)

0.749 0.789 Higher

Tool-calling action-budget metrics are trajectory-level quantities over 420 model-item trajectories per condition. The grounding headline and judge-specific rates are equal-weight means of the per-question fractions over all generated evidence-basis rows; only rows receiving at least two verified votes contribute to the headline numerator, while all other rows add no verified count. A separate exact-label diagnostic among the 444 non-verified with-BR rows present in all three judge outputs assigned a no unrelated majority to 289 (65%), a partial majority to 124 (28%), and no exact-label majority or cannot judge majority to the remaining 31 (7%); no row had a fabricated or malformed exact-label majority. The precision and citation-spam safeguards use the earlier Gemini 2.5 Flash single-judge scoring and are not three-judge-majority estimates. Evidence-citation metrics use evidence-item, claimed-grounded-item, or answer-output denominators as specified above and are not pooled with tool-calling metrics.

76

J5. Collaborator-case ledger

Case Evaluation object Reported outcome boundary NeuroMark schizophrenia FNC

FBIRN cohort, N = 363; 480-specification multiverse over connectivity, confound, dimensionality-reduction, clas- sifier, and domain granularity.

NM-H1, NM-H2, and NM-H3 all recorded as qualified (NM-H2 favorable in 12 of 24 contrasts after sign-aware rescoring); support depended on analytic regime.

SUDMEX CONN / Open- Neuro ds003346, N = 138; 36- specification multiverse over atlases, framewise-displacement thresholds, and confound strate- gies.

Five prespecified network-systemic-segregation associations rejected under SDMA-GLS (all Z < 1.24, FDR q > 0.58); exploratory 70- combination screen yielded no FDR-surviving effects (max ZGLS = 2.18; 0/70 surviving).

Cocaine-use-disorder connectivity

Cross-cultural social cognition

21 published studies, 85 MNI coordinates, four culture-by- relationship ALE cells with k = 6–8 cell-level entries.

Mechanistic mPFC-topology interpretation blocked as exploratory because cell counts were below recommended ALE stability thresholds and paradigm composition was imbalanced.

J6. Bounded self-evolving campaign ledger

Campaign Predeclared controls Claim-status outcome HCP-YA workflow search and transfer

Two staged search bundles with all 116 slots retained in the denomina- tor (104 scored in parent runs; 12 transport failures); frozen selected workflow designated before a lo- cally matched comparison; repeated family-grouped nested CV; frozen selected workflow refits across four additional outcomes; separate inter- nal holdout.

The frozen selected workflow exceeded the matched comparator in 10/10 Cognition splits and in 37/40 additional-outcome splits, but the result remained retrospective and same-cohort, no transfer cell survived weak-FWER correction, and the separate holdout did not confirm the comparator claim. No external scientific acceptance.

TRIBE speech–tools geometry

Complete 15-pair six-category discovery; researcher-authorized post-hoc contrast choice; frozen geometry estimand; three non- overlapping recurring-source panels; score-blind acoustic balancing and Holm-corrected permutation in- ference on four previously unused collections.

Three recurring-source panels met bounded support (11/12 collection cells in the pre- dicted direction), but the frozen four-new- source H1 was not supported after correc- tion (Holm p = .396). Terminal outcome inconclusive or conflicting; no scientific acceptance.

J7. Exclusions and denominator handling

Non-executable or blocked cases are retained in the relevant denominator unless the scoring contract explicitly defines a successful-run subset, as in the first-correct budget. Resource failures, failed preflight checks, missing required artifacts, governance blocks, and invalid tool routes are recorded as outcomes rather than silently removed. For evidence citation, claims without locatable evidence remain in the all-claims denominator for verified groundedness.

77

Appendix K. Cocaine-use-disorder case: representative generated code

The listing below is representative analysis code that Brain Researcher generated and executed for the cocaine-use-disorder case, a resting-state functional-connectivity multiverse on the SUDMEX cohort (CUD versus HC). The excerpt captures the multiverse specification: a header describing the design (cortical and subcortical atlas configurations crossed with framewise-displacement thresholds, aggregated by SDMA-GLS; this representative excerpt shows the atlas-by-FD grid, while the full 36-specification multiverse additionally crosses confound strategies), the 10-network definitions, the atlas-configuration grid, and a representative core function signature. Templated project tokens (a dollar-brace project-directory variable) are shown verbatim, and concrete filesystem locations

are written as the generic placeholder <DATA ROOT>. The complete code is released per the Code availability statement.

""" Multiverse Functional Connectivity Analysis -- SUDMEX CUD vs HC =============================================================== Specifications = atlas configs x FD motion thresholds (SDMA-GLS aggregated)

Atlas configs:

Sch200_Tian3 : Schaefer-200 + Tian Scale III (250 parcels) Sch400_Tian3 : Schaefer-400 + Tian Scale III (450 parcels) <- primary Sch600_Tian3 : Schaefer-600 + Tian Scale III (650 parcels) Sch400_HCP : Schaefer-400 + HCP subcortical (419 parcels) Gordon_Tian3 : Gordon-333 + Tian Scale III (383 parcels) Glasser_Tian3 : Glasser-360 + Tian Scale III (410 parcels)

FD motion thresholds: post-hoc re-censoring of XCP-D timeseries. XCP-D originally censored at FD=0.5; stricter thresholds drop more frames. Aggregation: SDMA-GLS (Lefort-Besnard et al., 2025, Imaging Neuroscience). """ # Project-relative paths use a templated project-directory token. XCPD = Path('${PROJ_DIR}/derivatives/xcpd') # e.g. <DATA_ROOT>/derivatives/xcpd PHENO = Path('${PROJ_DIR}/work/analysis_ready_surface.tsv')

# Network definitions: Yeo-7 cortical + 3 subcortical systems (10 total). YEO7 = ['Vis', 'SomMot', 'DorsAttn', 'SalVentAttn', 'Limbic', 'Cont', 'Default'] SUBCORT_GROUPS = {'Striatum': ['PUT-', 'CAU-', 'NAc-', 'GP'],

'Thalamus': ['THA-'], 'HippAmyg': ['HIP-', 'AMY']} ALL_NETWORKS = YEO7 + list(SUBCORT_GROUPS.keys()) FD_THRESHOLDS = [0.3, 0.5]

ATLAS_CONFIGS = [

{'id': 'Sch400_Tian3', 'ctx_seg': '4S456Parcels', 'n_ctx': 400, 'assign': 'schaefer'}, {'id': 'Glasser_Tian3', 'ctx_seg': 'Glasser', 'n_ctx': None, 'assign': 'glasser'}, # ... remaining atlas configurations crossed with FD_THRESHOLDS ... ]

def compute_network_fc(mat, parcel_network):

"""Mean within- and between-network FC (Fisher-z averaged) per spec.""" # core loop: for net in ALL_NETWORKS -> within_{net}; # for n1,n2 in combinations(ALL_NETWORKS,2) -> between_{n1}_{n2}

78

Appendix L. Per-case reports (released in the repository)

The automatically generated reports released with the repository are frozen episode snapshots. They preserve the system output, figures, tables, statistics, and provenance available when each report was closed, and they are not silently rewritten when a later episode supersedes the scientific trajectory. The NeuroMark report reflects the corrected, direction-aware re-audit described in Supplementary Methods S11.2.1. The earlier HCP retention-gate and TRIBE language-alignment reports are historical records of separate campaigns; they are not the evidentiary source for the current HCP workflow-search and TRIBE speech–tools episodes. The complete current numerical results and claim boundaries are given in S11.3.1–S11.3.3, with the underlying run bundles and current research-line reports identified through the Data availability statement.

79

Appendix M. Benchmark human-audit sheet (released in the repos- itory)

The graded sheet from the human audit of the automated benchmark judges (Supplementary Methods S11.1) is released with the benchmark package (Data availability; Appendix J). It records a reproducible random 20% sample (seed 20260630) of the scored results across the reported benchmarks (272 items across tool routing, NIK answer keys, and grounding judgments), each adjudicated by hand against the recorded automated verdict, with a per-item grade and, for the 11 flagged grounding items, the reason the verdict is debatable. The summary and the flagged-item accounting are given in Tables 4 and 5.


## References

[1] Elena A. Allen, Eswar Damaraju, Sergey M. Plis, Erik B. Erhardt, Tom Eichele, and Vince D.

Calhoun. Tracking whole-brain connectivity dynamics in the resting state. Cerebral Cortex, 24 (3):663–676, 2014. doi: 10.1093/cercor/bhs352.

[2] Diego Angeles-Valdez, Jalil Rasgado-Toledo, Victor Issa-Garcia, Thania Balducci, Viviana

Villica˜na, Alely Valencia, Jorge Julio Gonzalez-Olvera, Ernesto Reyes-Zamorano, Eduardo A. Garza-Villarreal, et al. The Mexican magnetic resonance imaging dataset of patients with cocaine use disorder: SUDMEX CONN. Scientific Data, 9(1):133, 2022. doi: 10.1038/ s41597-022-01251-3.

[3] Anthropic. Introducing the Model Context Protocol, 2024. URL https://www.anthropic.

com/news/model-context-protocol. Pages: 2024 Publication Title: Anthropic News Volume: November 25.

[4] B. B. Avants, N. J. Tustison, G. Song, P. A. Cook, A. Klein, and J. C. Gee. A reproducible

evaluation of ANTs similarity metric performance in brain image registration. NeuroImage, 54(3):2033–2044, 2011. doi: 10.1016/j.neuroimage.2010.09.025. URL https://doi.org/10. 1016/j.neuroimage.2010.09.025.

[5] R. Ciric, D. H. Wolf, J. D. Power, D. R. Roalf, G. L. Baum, K. Ruparel, R. T. Shinohara,

M. A. Elliott, S. B. Eickhoff, C. Davatzikos, R. C. Gur, R. E. Gur, D. S. Bassett, and T. D. Satterthwaite. Benchmarking confound regression strategies for the control of motion artifact in studies of functional connectivity. NeuroImage, 154:174–187, 2017. doi: 10.1016/j.neuroimage. 2017.03.020. URL https://doi.org/10.1016/j.neuroimage.2017.03.020.

[6] R. W. Cox. AFNI: Software for analysis and visualization of functional magnetic resonance

neuroimages. Computers and Biomedical Research, 29(3):162–173, 1996. doi: 10.1006/cbmr. 1996.0014. URL https://doi.org/10.1006/cbmr.1996.0014.

[7] Stephane d’Ascoli, Jeremy Rapin, Yohann Benchetrit, Teon Brooks, Katelyn Begany, Josephine

Raugel, Hubert Banville, and Jean-Remi King. A foundation model of vision, audition, and language for in-silico neuroscience, 2026. URL https://doi.org/10.48550/arXiv.2605. 04326. Publication Title: arXiv.

[8] Yuhui Du, Zening Fu, Jing Sui, Shuang Gao, Ying Xing, Dongdong Lin, Mustafa Salman,

Anees Abrol, Md Abdur Rahaman, Jiayu Chen, L. Elliot Hong, Peter Kochunov, Elizabeth A.

80

Osuch, and Vince D. Calhoun. NeuroMark: An automated and adaptive ICA-based pipeline to identify reproducible fMRI markers of brain disorders. NeuroImage: Clinical, 28:102375, 2020. doi: 10.1016/j.nicl.2020.102375.

[9] S. B. Eickhoff, A. R. Laird, C. Grefkes, L. E. Wang, K. Zilles, and P. T. Fox. Coordinate-based

activation likelihood estimation meta-analysis of neuroimaging data: A random-effects approach based on empirical estimates of spatial uncertainty. Human Brain Mapping, 30(9):2907–2926, 2009. doi: 10.1002/hbm.20718. URL https://doi.org/10.1002/hbm.20718.

[10] S. B. Eickhoff, T. E. Nichols, A. R. Laird, et al. Behavior, sensitivity, and power of activation

likelihood estimation characterized by massive empirical simulation. NeuroImage, 137:70–85, 2016. doi: 10.1016/j.neuroimage.2016.04.072. URL https://doi.org/10.1016/j.neuroimage. 2016.04.072.

[11] O. Esteban, D. Birman, M. Schaer, O. O. Koyejo, R. A. Poldrack, and K. J. Gorgolewski.

MRIQC: Advancing the automatic prediction of image quality in MRI from unseen sites. PLOS ONE, 12(9):e0184661, 2017. doi: 10.1371/journal.pone.0184661. URL https://doi.org/10.

1371/journal.pone.0184661.

[12] B. Fischl. FreeSurfer. NeuroImage, 62(2):774–781, 2012. doi: 10.1016/j.neuroimage.2012.01.021.

URL https://doi.org/10.1016/j.neuroimage.2012.01.021.

[13] Eduardo A. Garza-Villarreal, Jorge Julio Gonzalez Olvera, Thania Balducci, Diego Ange-

les Valdez, Alely Valencia, and Jalil Rasgado. SUDMEX CONN: The Mexican dataset of cocaine use disorder patients. OpenNeuro dataset, 2026. URL https://doi.org/10.18112/ openneuro.ds003346.v1.1.3.

[14] K. J. Gorgolewski, T. Auer, V. D. Calhoun, et al. The Brain Imaging Data Structure, a format

for organizing and describing outputs of neuroimaging experiments. Scientific Data, 3:160044, 2016. doi: 10.1038/sdata.2016.44. URL https://doi.org/10.1038/sdata.2016.44.

[15] L. Henschel, S. Conjeti, S. Estrada, K. Diers, B. Fischl, and M. Reuter. FastSurfer–A fast and ac-

curate deep learning based neuroimaging pipeline. NeuroImage, 219:117012, 2020. doi: 10.1016/ j.neuroimage.2020.117012. URL https://doi.org/10.1016/j.neuroimage.2020.117012.

[16] M. Jenkinson, C. F. Beckmann, T. E. J. Behrens, M. W. Woolrich, and S. M. Smith. FSL.

NeuroImage, 62(2):782–790, 2012. doi: 10.1016/j.neuroimage.2011.09.015. URL https://doi.

org/10.1016/j.neuroimage.2011.09.015.

[17] N. Kriegeskorte, M. Mur, and P. A. Bandettini. Representational similarity analysis–connecting

the branches of systems neuroscience. Frontiers in Systems Neuroscience, 2:4, 2008. doi: 10.3389/neuro.06.004.2008. URL https://doi.org/10.3389/neuro.06.004.2008.

[18] J. Lefort-Besnard, T. E. Nichols, and C. Maumet. Statistical inference for neuroimaging

multiverse analyses with the same-data meta-analysis. Imaging Neuroscience, 2025. doi: 10.1162/imag a 00513. URL https://doi.org/10.1162/imag_a_00513.

[19] Zhen-Qi Liu, Andrea I. Luppi, Justine Y. Hansen, Ye Ella Tian, Andrew Zalesky, B. T. Thomas

Yeo, Ben D. Fulcher, and Bratislav Misic. Benchmarking methods for mapping functional con- nectivity in the brain. Nature Methods, 22(7):1593–1602, 2025. doi: 10.1038/s41592-025-02704-4. URL https://doi.org/10.1038/s41592-025-02704-4.

81

[20] C. J. Markiewicz, K. J. Gorgolewski, F. Feingold, et al. The OpenNeuro resource for sharing of

neuroscience data. eLife, 10:e71774, 2021. doi: 10.7554/eLife.71774. URL https://doi.org/ 10.7554/eLife.71774.

[21] K. Murphy, R. M. Birn, D. A. Handwerker, T. B. Jones, and P. A. Bandettini. The impact of

global signal regression on resting state correlations: Are anti-correlated networks introduced? NeuroImage, 44(3):893–905, 2009. doi: 10.1016/j.neuroimage.2008.09.036. URL https://doi.

org/10.1016/j.neuroimage.2008.09.036.

[22] T. E. Nichols, S. Das, S. B. Eickhoff, et al. Best practices in data analysis and sharing in

neuroimaging using MRI. Nature Neuroscience, 20:299–303, 2017. doi: 10.1038/nn.4500. URL https://doi.org/10.1038/nn.4500.

[23] L. Parkes, B. Fulcher, M. Yucel, and A. Fornito. An evaluation of the efficacy, reliability, and

sensitivity of motion correction strategies for resting-state functional MRI. NeuroImage, 171: 415–436, 2018. doi: 10.1016/j.neuroimage.2017.12.073. URL https://doi.org/10.1016/j. neuroimage.2017.12.073.

[24] R. A. Poldrack, C. J. Markiewicz, S. Appelhoff, et al. The past, present, and future of the

Brain Imaging Data Structure (BIDS). Imaging Neuroscience, 2:1–19, 2024. doi: 10.1162/ imag a 00103. URL https://doi.org/10.1162/imag_a_00103.

[25] T. Salo, T. Yarkoni, T. E. Nichols, J.-B. Poline, M. Bilgel, K. L. Bottenhorn, et al. NiMARE:

Neuroimaging Meta-Analysis Research Environment. Aperture Neuro, 3:1–32, 2023. doi: 10.52294/001c.87681. URL https://doi.org/10.52294/001c.87681.

[26] A. Schaefer, R. Kong, E. M. Gordon, et al. Local-global parcellation of the human cerebral

cortex from intrinsic functional connectivity MRI. Cerebral Cortex, 28(9):3095–3114, 2018. doi: 10.1093/cercor/bhx179. URL https://doi.org/10.1093/cercor/bhx179.

[27] Stephen M. Smith, Mark Jenkinson, Mark W. Woolrich, Christian F. Beckmann, Timothy E. J.

Behrens, Heidi Johansen-Berg, Peter R. Bannister, Marilena De Luca, Ivana Drobnjak, David E. Flitney, Rami K. Niazy, James Saunders, John Vickers, Yongyue Zhang, Nicola De Stefano, J. Michael Brady, and Paul M. Matthews. Advances in functional and structural MR image analysis and implementation as FSL. NeuroImage, 23(Suppl. 1):S208–S219, 2004. doi: 10.1016/ j.neuroimage.2004.07.051. URL https://doi.org/10.1016/j.neuroimage.2004.07.051.

[28] Model Context Protocol Specification. Specification, protocol revision 2024-11-05, 2024. URL

https://modelcontextprotocol.io/specification/2024-11-05/.

[29] J.-D. Tournier, R. Smith, D. Raffelt, et al. MRtrix3: A fast, flexible and open software framework

for medical image processing and visualisation. NeuroImage, 202:116137, 2019. doi: 10.1016/j. neuroimage.2019.116137. URL https://doi.org/10.1016/j.neuroimage.2019.116137.

[30] D. C. Van Essen, S. M. Smith, D. M. Barch, et al. The WU-Minn Human Connectome Project:

An overview. NeuroImage, 80:62–79, 2013. doi: 10.1016/j.neuroimage.2013.05.041. URL https://doi.org/10.1016/j.neuroimage.2013.05.041.

[31] G. Varoquaux. Cross-validation failure: Small sample sizes lead to large error bars. NeuroImage,

180:68–77, 2018. doi: 10.1016/j.neuroimage.2017.06.061. URL https://doi.org/10.1016/j. neuroimage.2017.06.061.

82

[32] A. M. Winkler, G. R. Ridgway, M. A. Webster, S. M. Smith, and T. E. Nichols. Permutation

inference for the general linear model. NeuroImage, 92:381–397, 2014. doi: 10.1016/j.neuroimage. 2014.01.060. URL https://doi.org/10.1016/j.neuroimage.2014.01.060.

[33] Anderson M. Winkler, Matthew A. Webster, Diego Vidaurre, Thomas E. Nichols, and Stephen M.

Smith. Multi-level block permutation. NeuroImage, 123:253–268, 2015. doi: 10.1016/j. neuroimage.2015.05.092.

[34] WU-Minn Human Connectome Project Consortium. HCP Young Adult 1200 Subjects Data Re-

lease, 2017. URL https://www.humanconnectome.org/study/hcp-young-adult/document/ 1200-subjects-data-release. Published: Human Connectome Project data release page.

83
