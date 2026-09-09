---
workspace_id: "SCI-000128"
doi: null
title: "BioInsight: Multi-Agent Orchestration for Interactive Biomedical Knowledge Discovery"
year: 2026
extraction_engine: "pymupdf"
---
# 2026 Wang BioInsight Multi-Agent Orchestration fo

BioInsight: Multi-Agent Orchestration for Interactive Biomedical Knowledge Discovery

Jieyi Wang1, Bingxuan Li2,3, Nanyi Jiang3, Desong Meng1, Zirui Fan3, Yuxin Guo4, Jiayu Liu2, Kunlun Zhu2, Eddie Yang3, Xiusi Chen2, Pan Lu5, Bingxin Zhao3*

1Peking University, 2University of Illinois at Urbana-Champaign 3University of Pennsylvania 4Purdue University 5Stanford University

joysw@stu.pku.edu.cn, bxzhao@wharton.upenn.edu


## Abstract

be contextualized with pathway annotations, pro- tein–protein interaction networks, relevant liter- ature, and drug–target evidence (Menche et al., 2015; Yildirim et al., 2007). Researchers therefore need to interrogate how a conclusion was produced, which evidence supports it, where competing inter- pretations remain plausible, and how claims link back to source proteins and papers (Gao et al., 2024; Gierend et al., 2024). Existing search-augmented LLMs and deep research agents can retrieve evidence, browse the literature, and generate citation-grounded an- swers (Jin et al., 2025; Li et al., 2026c; Liu et al., 2025b; Shao et al., 2025). Biomedical agents such as Biomni further demonstrate that language mod- els can coordinate tools, databases, and code execu- tion to perform complex biomedical tasks (Huang et al., 2025). However, their outputs are typically delivered as static textual reports, making it diffi- cult for researchers to navigate the evidence under- lying individual claims. To present in a form that researchers can actively inspect, interactive inter- faces can make evidence, uncertainty, and prove- nance visible, but it’s harder to ensure the accuracy of the claim. For biomedical decision-making, it requires an evidence representation that remains co- herent and traceable throughout retrieval, synthesis, and user interaction (Wong et al., 2025; Leviathan et al., 2026).

Biomedical deep-research systems increasingly retrieve and synthesize scientific evidence, but their outputs typically collapse heterogeneous evidence into static text, making provenance difficult to inspect and reuse. We formulate evidence-centered biomedical knowledge dis- covery, where disease-associated protein sig- nals are transformed into a structured evidence state connecting proteins, pathways, publica- tions, interactions, claims, and uncertainty. We introduce BIOINSIGHT, a provenance- preserving multi-agent orchestration frame- work built around typed artifact contracts and an independent Search Agent that decouples evidence acquisition from downstream mech- anistic reasoning, supporting both the citation- grounded report and an interactive evidence workspace, without independently regenerating evidence for visualization. We evaluate BioIn- sight on standardized biomedical QA, chal- lenging protein-function reasoning, and end- to-end biomedical evidence synthesis. The re- sults demonstrate that BioInsight achieves bet- ter traceability and ranking performance than standard search-augmented baselines, and sug- gest that biomedical AI systems should move toward provenance-preserving, interactive evi- dence artifacts.

arXiv:2606.20997v2  [cs.AI]  2 Aug 2026

1 Introduction Biomedical researchers increasingly use AI- generated analyses and reports to support research interpretation and decision-making (Barabási et al., 2011; Wang et al., 2024; Zhang et al., 2024). In disease biology, this process often starts from protein-level signals, where cohort studies or ex- perimental screens identify disease-associated pro- teins and researchers must decide which pathways, mechanisms, and follow-up hypotheses warrant further investigation. Such interpretation requires more than ranking proteins: protein signals must

We argue that a persistent evidence layer shared across retrieval, reasoning, and presentation by agent harness enginerring can help. The layer should use explicit schemas to represent proteins, pathways, publications, and their relations. It should preserve provenance by linking every down- stream claim to the entities, analytical results, and source documents from which it is derived. Each reasoning, writing, and visualization agent is re- suable to operate over shared evidence objects rather than reconstructing information from free- form text. For inspection, intermediate evidence

*Corresponding author.

Prioritization Which proteins or pathways are

Multi-hop How do proteins, and drug

Hierarchy How should broad pathways be organized

Grounding What evidence supports  each mechanistic claim?

Biomedical  Research Questions

most disease-relevant?

targets connect?

into specific disease mechanisms?

Text-based Deep Research BioInsight: Multi-Agent Harness Decompose by function for accuracy, transparency, and usability

One model searching and reasoning end-to-end

Iterative refinement

Query Planning

Evidence Layer Synthesis Layer Interface Layer

Search Agent

Reasoning Agent

Summarization

Visualization

Agent

Agent

Search / Retrieval

Retrieve & Rank desease-relevant

Evaluate mechan-

Interactive Dashboard

isms, prioritize  proteins & path-

Generate  Interactive  dashboards for

Text Synthesis

Citation- grounded  interpretations

evidence

ways, generate

hypotheses

- Evidence traceable; - Drug Exploration; - Rapid visual- ization, easy to  explore and  understand; explorable decision-

exploration

Static Text Report

Knowledge Base PubMed, OpenTarget,  UniProt, STRING(PPI), ...

- Hard to inspect intermediate  evidence; - Hard to update; - Hard to read (for multi-hop  links, ranking rationale, ...);

Citation-grounded Report  with Structured Data & Evidence Schema

support artifacts


> **Figure 1: BioInsight converts disease-centered protein evidence into an interactive evidence interface. The system**

> uses agent-produced artifacts for search, reasoning, report writing, and dashboard construction, so users can move
from high-level hypotheses to the proteins, pathways, publications, and interaction evidence behind them.

can be examined independently of any particular report or interface.

best QA performance, the highest expert score on BioInsight-100, and stronger expert ratings for traceability, ranking quality, and dashboard usabil- ity in disease-level interpretation. To summarize, our contributions are threefold:

We therefore formulate disease-centered protein interpretation as an evidence-centered biomedical knowledge discovery task (Agrawal et al., 2017; Koscielny et al., 2017). Given a disease name, a table of disease-associated proteins, and optional cohort metadata, the system must retrieve, organize, and synthesize heterogeneous biomedical evidence while preserving the lineage from observed protein signals to downstream mechanisms, claims, and supporting sources. Relative to search agents, deep research systems, and biomedical agents (Table ??), the primary object is this structured evidence state rather than any single presentation format.

• We formulate disease-centered protein inter- pretation as an evidence-centered biomedical knowledge discovery task in which heteroge- neous evidence is organized into a provenance- preserving state that supports continued syn- thesis and inspection. • We propose BioInsight, a harness-centered multi-agent architecture that uses typed ar- tifact contracts and an Independent Search Agent to decouple evidence acquisition from mechanistic reasoning while maintaining provenance across retrieval, reasoning, report- ing, and visualization. • We evaluate whether the proposed orchestra- tion preserves biomedical capability while improving evidence synthesis and prove- nance. Our evaluation combines standardized biomedical QA, the BioInsight-1k protein- function reasoning benchmark, controlled same-base-model and ablation comparisons, a dedicated faithfulness analysis of evidence preservation, and expert assessment of end-to- end disease interpretation.

We propose BioInsight, a harness-centered multi-agent system that realizes this formulation (Fig. 1). An Independent Search Agent acquires, ranks, and normalizes heterogeneous biomedi- cal evidence; typed artifact contracts maintain the resulting shared evidence state across stages; and a Reasoning Agent synthesizes mechanisms over these structured artifacts. A Writing Agent and Visualization Agent subsequently render a citation-grounded report and an interactive dash- board as two synchronized views over the same evidence state rather than independently gener- ated endpoints. We hypothese that biomedical deep-research systems benefit from preserving ev- idence as structured, provenance-linked artifacts across stages rather than free-form generation. We test this through standardized biomedical QA,

2 Related Work

2.1 Search and Deep Research Agents Recent language agents support multi-step search and long-form research writing (Yao et al., 2022; Wu et al., 2024; Li et al., 2025; Liu et al., 2026;

protein-function reasoning, and end-to-end evalua- tion of generated reports and dashboards. Across these settings, BioInsight achieves the best or tied-

Li et al., 2026b,a). Search-R1 and ASearcher train

typed, provenance-linked, and reusable across rea- soning and presentation.

Design Aspect Search Deep Res. Bio. Agent Ours

Evidence retrieval ! ! ! ! Tool integration Partial Partial ! ! Typed artifacts × × Partial ! Cross-stage provenance × Partial Partial ! Interface state × × × !

2.3 Interactive Scientific Interfaces Visual analytics and generative interface systems explore how scientific information can be inspected beyond static text (Sosa et al., 2019). PaperVoy- ager converts papers into executable interactive sys- tems (Dai et al., 2026), and recent generative UI work shows that LLMs can produce task-specific interfaces (Leviathan et al., 2026; Google A2UI Team, 2026). Biomedical settings impose a stricter constraint: visual elements must remain tied to het- erogeneous evidence such as proteins, pathways, publications, interactions, and drug context (Ehlers et al., 2025). BioInsight therefore does not treat the interface as an independent generative endpoint. The dashboard is a synchronized view of the same typed evidence state used to write the report, so interactivity inherits provenance from the orches- tration layer rather than compensating for missing structure after generation.


> **Table 1: Architecture comparison of BioInsight with**

> search agents (e.g., Search-R1(Jin et al., 2025)), deep
research systems (e.g., DR-Tulu(Shao et al., 2025), Web-
Thinker(Li et al., 2026c)), and biomedical agents (e.g.,
Biomni(Huang et al., 2025)).

models to interleave reasoning with search (Jin et al., 2025; Gao et al., 2025), while WebThinker, WebExplorer, Tongyi DeepResearch, and DR-Tulu

focus on well-attributed answers or reports over re- trieved evidence (Li et al., 2026c; Liu et al., 2025b; Team et al., 2025; Shao et al., 2025). Evaluation work on RAG and self-reflective retrieval further emphasizes grounding and evidence use, not only final text quality (Es et al., 2024; Asai et al., 2024; Yan et al., 2024; Zhu et al., 2025; Yu et al., 2025). These systems typically couple retrieval and reason- ing through free-form context: search is an action within an end-to-end generation loop, and interme- diate evidence is not retained as a typed, reusable state across stages. BioInsight instead treats evi- dence acquisition as an independent stage whose outputs are normalized into inspectable artifacts before downstream reasoning.

3 Method We present BioInsight, a harness-centered multi-

agent system for wide biomedical evidence synthesis in disease-centered protein interpreta- tion. BioInsight decomposes disease-centered pro- tein evidence into an interactive decision-support workspace. The report is one artifact in this pro- cess, not the endpoint. The system first builds struc- tured evidence objects from protein associations, pathway enrichment, literature retrieval, and inter- action data; it then uses those objects to generate both a citation-grounded narrative and a dashboard schema. The rendered dashboard exposes the same evidence chain used by the report, allowing users to inspect claims, proteins, citations, and uncertainty from multiple views.

2.2 Biomedical Agents for Evidence Synthesis Biomedical LLM agents connect language models with literature, databases, tools, and code execu- tion environments (Sokolova et al., 2025). Biomni demonstrates broad biomedical task automation through tool use and planning (Huang et al., 2025); biomedical RAG and search systems improve ac- cess to PubMed and domain knowledge bases be- fore generation (Bi et al., 2025; Liu et al., 2025a). These systems provide strong tool and database integration, but retrieved evidence is still often treated as transient context for question answering or task completion. BioInsight targets a narrower setting—disease-centered protein interpretation— where protein association signals must be con- nected to pathways, publications, PPI modules, drug–target context, and uncertainty (Koscielny et al., 2017; Agrawal et al., 2017). As summa- rized in Table 1, the distinguishing design is not broader tool coverage alone, but an explicit evi- dence layer that keeps these heterogeneous sources

3.1 Task Formulation

We define its task as evidence-centered interac-

tive interface generation: given disease-associated protein signals, multiple agents iteratively re- trieve, rank, reason over, write about, and visu- alize biomedical evidence to produce explorable decision-support artifacts. The harness coordinates these agents through typed artifact contracts, so each refinement step can reuse, revise, or expose upstream evidence without losing provenance. An input instance is

x = (d, P, M, K),

where d is a disease name, P is a disease-associated protein table, M is optional cohort metadata, and K denotes external biomedical knowledge re- sources. The protein table contains protein symbols and statistical association fields such as hazard ra- tios, confidence intervals, and P values.

Near-duplicate pathway names are removed with BioBERT embedding similarity after generic path- way phrases are stripped. The remaining pathways are ranked by combining enrichment strength with disease-specific literature support.

For pathway t, let p(t) denote its enrichment P value and L(t) denote the literature relevance score returned by the Search Agent. We normalize these values across candidate pathways to obtain Pnorm(t) and Lnorm(t), where lower Pnorm(t) in- dicates stronger enrichment and higher Lnorm(t) indicates stronger disease-specific literature sup- port. The pathway score is

The system produces

Y = (T, E, N, R, S, H),

where T is a ranked pathway table, E is a set of evidence packets, N contains pathway- and protein- level reasoning notes, R is a citation-grounded re- port, S is a dashboard schema, and H is the ren- dered interactive dashboard. Search and planning agents construct T and E; reasoning and writing agents refine them into N and R; the visualiza- tion agent converts the same evidence base into S and H. H is the primary user-facing artifact, while T, E, N, R, and S provide its provenance. Each downstream artifact keeps references to the upstream proteins, pathways, statistics, evidence packets, and citations from which it was derived.

Spath(t) = 0.4 · Pnorm(t) + 0.6 · (1 −Lnorm(t)).

Lower scores are prioritized. This favors path- ways that are both statistically supported by the input protein set and grounded in disease-relevant literature.

Publication Retrieval and Scoring For each candidate pathway, the Search Agent builds disease-pathway queries from the disease name and pathway name. It retrieves publications from PubMed and Semantic Scholar, then normalizes them into evidence packets. Each publication is scored using lexical relevance, semantic relevance, citation impact, and journal weight. For query q = (d, t) and article a, the raw score is

3.2 Multi-Agent Harness Design 3.2.1 Overview BioInsight has three layers. The evidence layer per- forms pathway planning and publication retrieval. The synthesis layer produces structured reasoning notes and a citation-grounded report. The interface layer converts the same evidence objects into an interactive dashboard. A central harness sched- ules these stages, validates required fields, and passes only typed artifacts between agents. Given a disease name, protein table, and cohort meta- data, the system sequentially plans pathway-level hypotheses, retrieves biomedical evidence, synthe- sizes structured mechanisms, formats citations, and renders the final report and interactive dashboard. All LLM agents use GPT-4o as the base model.

Sraw(q, a) = 0.45K(q, a) + 0.35E(q, a)

+ 0.20C(a),

where K(q, a) measures disease-pathway keyword matches, E(q, a) is BioBERT semantic similarity between the query and title-abstract text, and C(a) is a log-scaled citation-count score. The final score applies a bounded journal weight:

Spub(q, a) = clip (Sraw(q, a) · J(a), 0, 2.2) ,

This organization keeps generated interactive in- terface tied to evidence. The Visualization Agent does not invent new nodes or claims. It receives structured outputs from earlier stages and renders them as an evidence workspace. If a pathway, pro- tein, or publication is missing from the artifacts, it cannot appear as a supported item in the dashboard.

where J(a) is derived from the publication venue. Publications with Spub ≥0.25 are retained as vali- dated evidence. Each retained item stores the query, metadata, relevance score, PMID when available, and the pathway for which it was retrieved.

3.2.3 Evidence Synthesis For each selected pathway, the Reasoning Agent receives the disease name, pathway identifier, path- way description, intersecting proteins, original as- sociation statistics, validated publication packets, protein function records, and PPI records when

3.2.2 Evidence Planning and Retrieval Pathway Planning The Planning Agent identi- fies candidate biological mechanisms from the in- put protein set. It maps disease-associated pro- teins to enriched biological terms using g:Profiler.

available. It returns structured reasoning notes in- stead of final prose. Each note contains a pathway interpretation, disease relevance, key protein sum- maries, PPI-module explanations, uncertainty state- ments, and citation links. The full reasoning-note schema is provided in Appendix A.

capabilities required for downstream evidence synthesis? • RQ2 (Cross-source reasoning). Can BioIn- sight integrate heterogeneous evidence for challenging protein-centered reasoning? • RQ3 (Orchestration contribution). Does artifact-centered orchestration improve evi- dence synthesis independently of the underly- ing foundation model? • RQ4 (Provenance / faithfulness). Does the typed-artifact contract preserve evidence across report and interface generation?

Protein–protein interactions are represented as graph evidence. For proteins intersecting a path- way, BioInsight builds an undirected weighted graph from retrieved PPI edges, identifies con- nected components, and ranks components by in- ternal edge weight and size. The top components are used for cluster-level reasoning; disconnected proteins are analyzed individually using protein function annotations. This separates isolated pro- tein evidence from coherent interaction modules within a disease-relevant pathway.

4.1 Baselines and Setup

We use task-specific controls. For RQ1 and RQ2, we compare BioInsight with GPT-5.5, DR-Tulu- 8B, Gemma-4-31B, and Qwen3.5-9B, covering general-purpose, biomedical/domain-aligned, and open-weight systems. For RQ3, the primary com- parison is same-base-model: GPT-4o+Search vs. BioInsight (GPT-4o), GPT-5.5 vs. BioInsight (GPT- 5.5), and BioInsight without the Independent Search Agent (w/o ISA). We additionally report ex- ternal comparisons against strong search-enabled systems (GPT-5.5+Search, Gemini Deep Research) and open-weight baselines on five disease cases (Appendix B.4). For RQ4, we compare BioInsight dashboards with report-first GPT-5.5 pipelines un- der matched evidence access, including a typed- input-package control that receives the same re- trieved evidence without BioInsight orchestration. All systems use the same disease names, protein association tables, and task instructions where ap- plicable. Additional model settings and retrieval budgets are in Appendix B.

3.2.4 Evidence-Centered Interactive Interface Generation

The Writing Agent organizes reasoning notes into a scientific report. The report includes a disease intro- duction, cohort and protein summary, ranked path- way table, pathway-level analyses, protein-level ex- planations, PPI summaries and links, optional drug or target context, and citation identifiers. Then, the Visualization Agent converts the organized insights, original protein table, and cached evidence artifacts into a dashboard schema. Pathways, proteins, publi- cations, PPI edges, and optional drug-related edges are extracted according to predefined schemas. Op- tional language-model summarization is used only to shorten long display text; it does not create new evidence objects.

The dashboard contains a pathway ranking panel, a graph linking pathways, proteins, publications, PPI edges, and optional drug-related evidence, and detail panels for selected nodes or edges. Users can inspect enriched proteins for a pathway, view original association statistics for a protein, open PMID-linked publication evidence, and filter the graph by edge type. The output is therefore an explorable decision-support artifact built from the same evidence that supports the generated report.

4.2 Grounding Accuracy in Standardized Biomedical QA Before a multi-agent workflow can maintain a reusable evidence state, it must preserve exact biomedical answering, entity normalization, and evidence-supported item selection. We therefore treat BioASQ Phase B (yes/no, factoid, and list) as a prerequisite grounding check.


> **Figure 2 shows that BioInsight maintains com-**

> petitive exact-answer performance without sacri-
ficing QA ability. Confidence intervals are wide,
so point-estimate gaps should be interpreted cau-
tiously.
The most consistent signal is on List
F-measure (51.10 vs. 40.49 for GPT-5.5), which
aligns with the Independent Search Agent’s role in
multi-entity retrieval and evidence aggregation.

4 Experiments and Results

We evaluate BioInsight along the properties intro-

duced by artifact-centered orchestration. We ask four research questions:

• RQ1 (Grounding). Does BioInsight preserve the biomedical retrieval and entity-selection


> **Figure 2: Results on BioASQ Phase B Exact Answer task, Batch 1. All five metrics are higher-is-better. BioInsight**

> achieves the best performance across all five exact-answer metrics.

4.3 Cross-Source Protein Reasoning Disease-centered protein interpretation further re- quires integrating functional annotations, PPIs, pathway context, disease mechanisms, and ranked explanations across heterogeneous sources. We construct BioInsight-1k from UniProt and STRING evidence, use GPT-5.5 to propose candidate ques- tions, and have biomedical experts select 100 chal- lenging cross-evidence items to form BioInsight- 100. The benchmark is not a factual lookup test: questions require cross-source reasoning and pri- oritization, as verified by two biomedical experts. All systems access the same underlying resources under the same protocol.

tative systems from the automatic study: GPT-5.5 + Search, Gemini Deep Research, DR-Tulu-8B, and BioInsight. Experts assess five dimensions, with an addition of readability. The evaluation results of Atrial fibrillation and flutter are shown in Figure 4, and that of other diseases are listed in Table 2.

As an external check, Figure 41 and Table 2 compare BioInsight with strong search-enabled and open-weight systems across five diseases (Ap- pendix B.4), covering different biomedical decision regimes, including Alzheimer’s disease (AD), de- pression (MDD), atrial fibrillation and flutter (AF), chronic kidney disease (CKD), and rheumatoid arthritis (RA).. BioInsight w/o ISA sits between the search-only baseline and full BioInsight, showing that freezing and normalizing evidence before rea- soning contributes to the gain—not merely using a stronger model. BioInsight remains competitive on coverage and validity and strongest on auto- matic traceability and ranking; the separate w/o ISA rows show consistent drops when evidence acquisition is not decoupled. Biomedical validity is less separated among frontier systems, consistent with validity depending more on the base model, while traceability depends more on workflow struc- ture. Expert ratings likewise favor BioInsight on traceable synthesis, ranking, and usability. These external results support practical utility.


> **Figure 3 reports expert scores. BioInsight ob-**

> tains the highest mean score of 8.62, with an-
swers concentrated in the high-score range, indi-
cating more stable protein-centered reasoning and
evidence ranking than general-purpose and open-
weight baselines.

4.4 Orchestration Contribution

To evaluate whether typed artifacts and the Inde- pendent Search Agent improve evidence synthesis independently of the foundation model, we evalu- ate end-to-end disease-centered synthesis on cover- age, biomedical validity, evidence traceability, and ranking/research depth (Page et al., 2021; Clark et al., 2025; Flemyng et al., 2025)(rubric details in Appendix C).

4.5 Provenance and Faithfulness To test whether typed artifact contracts preserve ev- idence across report and interface generation. For each of five diseases, we construct a gold reference of grounded proteins, pathway overlaps, PMIDs, STRING PPIs, and DGIdb drug links. We evaluate unsupported entities (M1↓), unsupported relations

For automatic evaluation, we score all six sys- tems on four dimensions twice: coverage, biomed- ical validity, evidence grounding and traceability, and prioritization and research depth. To control the result not influenced by searching ability, all "+ Search" means that the generation is based on the literature searched by BioInsight. For human evalu- ation, we select the four strongest or most represen-

1An anonymized demo is available at http://3.148.244. 109:5000/.


> **Table 2: Automatic and human evaluation of end-to-end biomedical evidence synthesis reports (except AF).**

Disease Models Automatic Evaluation Human Evaluation Cov. Val. Trac. Rank. Cov. Val. Trac. Rank. Read. AD GPT5.5 + Web 4.0 4.0 3.0 3.5 4.00 4.75 4.50 4.25 4.50 Gemini Deep Search 4.0 3.0 3.0 3.5 4.50 3.50 4.00 4.00 4.50 DR-Tulu-8B 3.0 2.5 2.0 2.5 3.00 4.00 3.67 3.33 3.67 Qwen3.5-9B 3.0 2.5 2.0 2.5 - - - - - BioInsight (w/o Search) 4.0 (3.5) 4.0 (3.0) 3.5 (3.0) 4.0 (3.0) 3.75 4.00 4.50 4.00 4.50 CKD GPT5.5 + Web 3.5 4.0 3.5 3.5 4.33 5.00 4.33 3.67 4.00 Gemini Deep Search 4.0 4.0 2.5 3.5 5.00 4.50 3.50 4.00 4.50 DR-Tulu-8B 3.0 2.5 1.5 2.5 2.33 3.00 2.00 2.33 2.33 Qwen3.5-9B 3.0 3.0 2.5 3.0 BioInsight (w/o Search) 3.5 (3.5) 4.0 (3.0) 3.5 (3.0) 3.5 (3.0) 4.67 4.00 3.67 4.00 4.50 MDD GPT5.5 + Web 3.5 4.0 3.5 4.0 4.33 4.67 4.33 3.67 4.33 Gemini Deep Search 4.0 3.0 2.5 3.5 4.50 4.50 3.50 4.50 4.50 DR-Tulu-8B 2.5 2.5 1.5 2.0 3.00 2.33 3.33 2.33 2.00 Qwen3.5-9B 3.0 3.0 2.5 3.0 - - - - - BioInsight (w/o Search) 4.0 (3.5) 4.0 (3.0) 3.5 (2.5) 4.0 (3.0) 3.67 3.00 3.00 3.33 4.50 RA GPT5.5 + Web 4.0 4.0 3.0 3.5 4.67 4.67 4.33 3.67 4.67 Gemini Deep Search 3.5 3.0 2.5 3.0 4.50 4.50 3.50 3.50 4.50 DR-Tulu-8B 3.0 2.0 1.5 2.5 2.33 3.33 2.33 3.00 2.33 Qwen3.5-9B 3.0 2.5 2.0 2.5 - - - - BioInsight (w/o Search) 4.0 (3.5) 4.5 (3.0) 3.5 (3.0) 4.0 (3.0) 3.33 3.50 3.33 3.67 4.83

(M2↓), pathway omission (M3↓), and citation cov- erage (M4↑).

than visual presentation alone. Besides, as infor- mation passes through retrieval, reasoning, writing, and visualization stages, some coverage can be lost or compressed. In our results, this did not pre- vent BioInsight from producing useful reports, but it points to an important open question for future deep research: more retrieved information is not always better if it cannot be ranked, grounded, and presented in a form that researchers can inspect.


> **Table 3 yields a precise conclusion. Raw re-**

> port/dashboard pipelines fabricate many unsup-
ported entities and relations and lose most pathway
and citation evidence. Giving GPT-5.5 the same
typed evidence package already nearly eliminates
unsupported entities and relations (M1/M2≈0),
showing that hallucination reduction alone is not
BioInsight’s distinctive contribution. Relative to
this strong typed-input control, BioInsight still
substantially lowers pathway omission (0.11 vs.
0.27) and raises citation coverage (0.33 vs. 0.25),
while keeping unsupported entities and relations
at zero. Thus, typed artifacts primarily improve
evidence preservation across stages, not merely
hallucination reduction—exactly the property pre-
dicted by the shared evidence state and containment
invariant.

Overall, the three evaluations show complemen- tary strengths. BioInsight improves exact biomedi- cal answering on BioASQ, achieves stronger cross- evidence protein-function reasoning on BioInsight- 100, and produces more traceable and usable end-to-end biomedical evidence synthesis reports. These results support the central claim that harness- centered artifact contracts can improve biomedical evidence synthesis beyond single-step search or fluent long-form generation. 5 Case Study We use Alzheimer’s disease (AD) to illustrate

Furthermore, BioInsight receives the strongest expert ratings for traceable synthesis, ranking, and usability. Expert comments further indicate that BioInsight is the only system that consistently sur- faces disease-association evidence, which gives re- searchers concrete hints for disease–protein analy- sis rather than only a general biological summary. The interactive interface is also recognized as use- ful for checking pathways, proteins, and citations. At the same time, experts are willing to use clear and well-organized Markdown reports, suggesting that the value of the interactive interface comes from evidence traceability and navigation rather

BioInsight as an evidence-centered interface, not a single-step report generator. AD is a suitable case because protein signals must be interpreted across synaptic dysfunction, lipid metabolism, glial activa- tion, axonal injury, and neurodegeneration instead of one dominant pathway.

Given the disease name, cohort metadata, and 10 significant plasma proteins, BioInsight builds an artifact chain from protein statistics to pathways, publications, reasoning notes, and the dashboard in Figure 5. The Planning Agent identifies enriched


> **Table 3: Faithfulness evaluation with 95% confidence intervals. Once strong models receive clean typed artifacts,**

> unsupported entities/relations are already rare; BioInsight’s main advantage is reducing evidence loss (pathway
omission, citation coverage) across downstream generation.

System M1 Ent.↓ M2 Rel.↓ M3 Path.↓ M4 Cite.↑

BioInsight (dashboard) 0.000 [0.00,0.00] 0.000 [0.00,0.00] 0.110 [0.05,0.14] 0.334 [0.17,0.56] GPT-5.5 (typed package) report 0.001 [0.00,0.00] 0.002 [0.00,0.01] 0.268 [0.16,0.30] 0.245 [0.15,0.39] GPT-5.5 (raw) report 0.345 [0.22,0.49] 0.842 [0.75,0.93] 0.879 [0.85,0.91] 0.088 [0.02,0.18] GPT-5.5 (raw) dashboard 0.399 [0.29,0.52] 0.458 [0.20,0.70] 0.947 [0.92,0.98] 0.039 [0.01,0.07]


> **Figure 4: Automatic and human evaluation of end-to-**

> end biomedical evidence synthesis reports on Atrial fib-
rillation and flutter. Cov., Val., Trac., Rank. and Read.
respectively means coverage, biomedical validity, evi-
dence traceability, ranking and research depth, and user
usability. Higher scores indicate better performance.

with weaker pathway or literature support remain visible but are treated as exploratory.

This case highlights the role of the interactive artifact. A pathway can be statistically enriched but weakly supported by AD-specific literature, while another may have moderate enrichment but clearer disease relevance. By combining enrichment evi- dence with publication support and making both visible, BioInsight turns a static disease report into an auditable path from proteins to pathways, cita- tions, mechanisms, and follow-up hypotheses.


> **Figure 3:**

> Evaluation score distributions on the
BioInsight-100 benchmark, a challenging subset of
protein-function analysis questions from BioInsight-1k.
Box plots with individual data points (a) and violin plots
(b) show the distribution of 0–10 scores.

6 Conclusion We introduced BIOINSIGHT, a harness-centered

candidate pathways, the Search Agent retrieves disease-specific literature, the Reasoning Agent integrates pathway, protein, PPI, and drug-related evidence, and the Visualization Agent exposes the resulting evidence structure for inspection.

multi-agent system for disease-centered protein in- terpretation. By enforcing artifact contracts be- tween retrieval, reasoning, writing, and dashboard construction, BioInsight exposes protein, pathway, publication, and citation links that are usually hidden in end-to-end biomedical agents. Across BioASQ, BioInsight-100, and report-level expert evaluation, the system improves exact answering, protein-function reasoning, and traceable report synthesis. These results suggest that more biomed- ical evidence synthesis benefits from structured, auditable intermediate artifacts rather than fluent generation alone.

The resulting workspace keeps the interpretation grounded in the observed protein signals. APOE appears as a cross-pathway driver linking lipid re- ceptor biology, vesicle organization, synaptic pro- cesses, and axon-related hypotheses. GFAP and NEFL support glial and axonal-injury interpreta- tions, while SNAP25 and SYT1 form a presynaptic vesicle and chemical synapse module. Proteins


> **Figure 5: Case study on Alzheimer’s Disease.**

Limitations

In International conference on learning representa- tions, volume 2024, pages 9112–9141.

BioInsight is designed to support biomedical re- search interpretation and hypothesis generation, not clinical diagnosis, treatment selection, or other forms of clinical decision-making. A primary eth- ical risk is that users may overinterpret automat- ically generated pathway, protein, or drug–target explanations as validated biological mechanisms or therapeutic conclusions. Although BioInsight grounds its outputs in retrieved publications and ex- poses intermediate evidence through structured arti- facts and dashboards, the underlying evidence may still be incomplete or noisy. Retrieval can miss rele- vant studies, select papers that are topically related but mechanistically weak, or suffer from protein synonym ambiguity, incomplete database coverage, and noisy input protein associations. As a result, BioInsight may produce incomplete evidence sum- maries, uncertain mechanistic links, or hypotheses that require further validation.

Albert-László Barabási, Natali Gulbahce, and Joseph

Loscalzo. 2011. Network medicine: a network-based approach to human disease. Nature reviews genetics, 12(1):56–68.

Manlian Bi, Zhijie Bao, Dongna Xie, Xiaohan Xie,

Changxiao Yang, Tao Wang, Yongtian Wang, and Jia- jie Peng. 2025. Bioragent: natural language biomed- ical querying with retrieval-augmented multiagent systems. Briefings in Bioinformatics, 26(5):bbaf539.

Justin Clark, Belinda L Barton, Loai Albarqouni, Oyuka

Byambasuren, Tanisha Jowsey, Justin WL Keogh, Tian Liang, Christian Moro, Hayley M O’Neill, and Mark A Jones. 2025. Generative artificial intelli- gence use in evidence synthesis: A systematic review. Research Synthesis Methods, 16(4):601–619.

Dasen Dai, Biao Wu, Meng Fang, and Wenhao Wang.

2026. Papervoyager: Building interactive web with visual language models.

Henry Ehlers, Nicolas Brich, Michael Krone, Martin

Nöllenburg, Jiacheng Yu, Hiroaki Natsukawa, Xiaoru Yuan, and Hsiang-Yun Wu. 2025. An introduction

To mitigate these risks, BioInsight preserves ci- tation links, protein-level statistics, intermediate artifacts, uncertainty notes, and failure-handling be- haviors, allowing users to inspect how each claim is supported. However, these mechanisms are in- tended to support expert review rather than replace it. All outputs should be reviewed by domain ex- perts and validated through independent biomedi- cal analysis before being used to guide downstream experimental, translational, or clinical decisions.

to and survey of biological network visualization. Computers & Graphics, 126:104115.

Shahul Es, Jithin James, Luis Espinosa Anke, and

Steven Schockaert. 2024. Ragas: Automated evalua- tion of retrieval augmented generation. In Proceed- ings of the 18th conference of the european chapter of the association for computational linguistics: system demonstrations, pages 150–158.

Ella Flemyng, Anna Noel-Storr, Biljana Macura, Gerald

Gartlehner, James Thomas, Joerg J Meerpohl, Zoe Jordan, Jan Minx, Angelika Eisele-Metzger, Candyce Hamel, and 1 others. 2025. Position statement on artificial intelligence (ai) use in evidence synthesis across cochrane, the campbell collaboration, jbi and the collaboration for environmental evidence 2025. Cochrane Database of Systematic Reviews, (10).


## References

Monica Agrawal, Marinka Zitnik, and Jure Leskovec.

2017. Large-scale analysis of disease pathways in the human interactome. page 189787. Cold Spring Harbor Laboratory.

Jiaxuan Gao, Wei Fu, Minyang Xie, Shusheng Xu,

Akari Asai, Zeqiu Wu, Yizhong Wang, Avi Sil, and

Chuyi He, Zhiyu Mei, Banghua Zhu, and Yi Wu. 2025. Beyond ten turns: Unlocking long-horizon agentic search with large-scale asynchronous rl.

Hannaneh Hajishirzi. 2024. Self-rag: Learning to re- trieve, generate, and critique through self-reflection.

Shanghua Gao, Ada Fang, Yepeng Huang, Valentina

Congying Liu, Xingyuan Wei, Peipei Liu, Yiqing Shen,

Giunchiglia, Ayush Noori, Jonathan Richard Schwarz, Yasha Ektefaie, Jovana Kondic, and Marinka Zitnik. 2024. Empowering biomedical dis- covery with ai agents. Cell, 187(22):6125–6151.

Yanxu Mao, and Tiehan Cui. 2025a. Biomedsearch: A multi-source biomedical retrieval framework based on llms.

Jiateng Liu, Zhenhailong Wang, Rushi Wang, Bingx-

Kerstin Gierend, Frank Krüger, Sascha Genehr, Fran-

uan Li, Jeonghwan Kim, Aditi Tiwari, Pengfei Yu, Denghui Zhang, and Heng Ji. 2026. Osexpert: Computer-use agents learning professional skills via exploration. arXiv preprint arXiv:2603.07978.

cisca Hartmann, Fabian Siegel, Dagmar Waltemath, Thomas Ganslandt, and Atinkut Alamirrew Zeleke. 2024. Provenance information for biomedical data and workflows: scoping review. Journal of medical Internet research, 26:e51297.

Junteng Liu, Yunji Li, Chi Zhang, Jingyang Li, Aili

Chen, Ke Ji, Weiyu Cheng, Zijia Wu, Chengyu Du, Qidi Xu, and 1 others. 2025b. Webexplorer: Explore and evolve for training long-horizon web agents.

Google A2UI Team. 2026. A2ui v0.9: The new stan-

dard for portable, framework-agnostic generative ui. Google Developers Blog. Published April 17, 2026.

Kexin Huang, Serena Zhang, Hanchen Wang, Yuanhao

Jörg Menche, Amitabh Sharma, Maksim Kitsak, Su-

Qu, Yingzhou Lu, Yusuf Roohani, Ryan Li, Lin Qiu, Gavin Li, Junze Zhang, and 1 others. 2025. Biomni: A general-purpose biomedical ai agent. biorxiv.

san Dina Ghiassian, Marc Vidal, Joseph Loscalzo, and Albert-László Barabási. 2015. Uncovering disease-disease relationships through the incomplete interactome. Science, 347(6224):1257601.

Bowen Jin, Hansi Zeng, Zhenrui Yue, Jinsung Yoon,

Sercan Arik, Dong Wang, Hamed Zamani, and Jiawei Han. 2025. Search-r1: Training llms to reason and leverage search engines with reinforcement learning.

Matthew J Page, Joanne E McKenzie, Patrick M

Bossuyt, Isabelle Boutron, Tammy C Hoffmann, Cyn- thia D Mulrow, Larissa Shamseer, Jennifer M Tet- zlaff, Elie A Akl, Sue E Brennan, and 1 others. 2021. The prisma 2020 statement: an updated guideline for reporting systematic reviews. bmj, 372.

Gautier Koscielny, Peter An, Denise Carvalho-Silva,

Jennifer A Cham, Luca Fumis, Rippa Gasparyan, Samiul Hasan, Nikiforos Karamanis, Michael Maguire, Eliseo Papa, and 1 others. 2017. Open targets: a platform for therapeutic target identi- fication and validation. Nucleic acids research, 45(D1):D985–D994.

Rulin Shao, Akari Asai, Shannon Zejiang Shen, Hamish

Ivison, Varsha Kishore, Jingming Zhuo, Xinran Zhao, Molly Park, Samuel G Finlayson, David Sontag, and 1 others. 2025. Dr tulu: Reinforcement learning with evolving rubrics for deep research. arXiv preprint arXiv:2511.19399.

Yaniv Leviathan, Dani Valevski, Matan Kalman, Danny

Lumen, Eyal Segalis, Eyal Molad, Shlomi Pasternak, Vishnu Natchu, Valerie Nygaard, James Manyika, and 1 others. 2026. Generative ui: Llms are effective ui generators.

Ksenia Sokolova, Dmitri Kosenkov, Keerthana Nal-

lamotu, Sanketh Vedula, Daniil Sokolov, Guillermo Sapiro, and Olga G Troyanskaya. 2025. An evidence- grounded research assistant for functional genomics and drug target assessment. bioRxiv, pages 2025–12.

Bingxuan Li, Yiming Cui, Yicheng He, Yiwei Wang,

Shu Zhang, Longyin Wen, and Yulei Niu. 2026a. Echofoley: Event-centric hierarchical control for video grounded creative sound generation. In Pro- ceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pages 27229–

Daniel N Sosa, Alexander Derry, Margaret Guo, Eric

Wei, Connor Brinton, and Russ B Altman. 2019. A literature-based knowledge graph embedding method for identifying drug repurposing opportunities in rare diseases. In Pacific Symposium on Biocomputing 2020, pages 463–474. World Scientific.

27238.

Bingxuan Li, Jeonghwan Kim, Cheng Qian, Xiusi Chen,

Eitan Anzenberg, Niran Kundapur, and Heng Ji. 2026b. Pearl: Self-evolving assistant for time man- agement with reinforcement learning. arXiv preprint arXiv:2601.11957.

Tongyi DeepResearch Team, Baixuan Li, Bo Zhang,

Dingchu Zhang, Fei Huang, Guangyu Li, Guoxin Chen, Huifeng Yin, Jialong Wu, Jingren Zhou, and 1 others. 2025. Tongyi deepresearch technical report.

Bingxuan Li, Yiwei Wang, Jiuxiang Gu, Kai-Wei Chang,

and Nanyun Peng. 2025. Metal: A multi-agent frame- work for chart generation with test-time scaling. In Proceedings of the 63rd Annual Meeting of the As- sociation for Computational Linguistics (Volume 1: Long Papers), pages 30054–30069.

Zifeng Wang, Lang Cao, Benjamin Danek, Qiao Jin,

Zhiyong Lu, and Jimeng Sun. 2024. Accelerating clinical evidence synthesis with large language mod- els. arXiv preprint arXiv:2406.17755.

Xiaoxi Li, Jiajie Jin, Guanting Dong, Hongjin Qian,

Yongkang Wu, Ji-Rong Wen, Yutao Zhu, and

Ryan Wong, Jiawei Wang, Junjie Zhao, Li Chen, Yan

Zhicheng Dou. 2026c. Webthinker: Empowering large reasoning models with deep research capability. volume 38, pages 120091–120131.

Gao, Long Zhang, Xuan Zhou, Zuo Wang, Kai Xi- ang, Ge Zhang, and 1 others. 2025. Widesearch: Benchmarking agentic broad info-seeking.

A.2 Intermediate Artifacts and Reasoning Notes

Qingyun Wu, Gagan Bansal, Jieyu Zhang, Yiran Wu,

Beibin Li, Erkang Zhu, Li Jiang, Xiaoyun Zhang, Shaokun Zhang, Jiale Liu, and 1 others. 2024. Au- togen: Enabling next-gen llm applications via multi- agent conversations. In First conference on language modeling.

BioInsight stores pathway rankings, evidence pack- ets, reasoning notes, citation-linked drafts, net- work views, dashboard schemas, and rendered dashboards as separate artifacts. These artifacts make the system inspectable at several points: re- searchers can examine enriched pathways before reading the final narrative, trace report claims back to proteins and publications, and check whether the dashboard represents the same evidence used in the report.

Shi-Qi Yan, Jia-Chen Gu, Yun Zhu, and Zhen-Hua Ling.

2024. Corrective retrieval augmented generation.

Shunyu Yao, Jeffrey Zhao, Dian Yu, Izhak Shafran,

Karthik R Narasimhan, and Yuan Cao. 2022. React: Synergizing reasoning and acting in language models. In NeurIPS 2022 Foundation Models for Decision Making Workshop.

The reasoning-note schema used by the Reason- ing Agent is shown below. Each note contains pathway-level interpretation, disease relevance, key proteins, PPI module explanations, uncertainty, and citations.

Muhammed A Yildirim, Kwang-Il Goh, Michael E

Cusick, Albert-Laszlo Barabasi, and Marc Vidal. 2007. Drug–target network. Nature biotechnology, 25(10):1119.

{

Haofei Yu, Keyang Xuan, Fenghai Li, Kunlun Zhu, Zi-

"pathway_id": "REAC:R-HSA-166658", "pathway_name": "Complement cascade", "disease_explanation": "...", "key_proteins": [

jie Lei, Jiaxun Zhang, Ziheng Qi, Kyle Richardson, and Jiaxuan You. 2025. Tinyscientist: An interactive, extensible, and controllable framework for building research agents. In Proceedings of the 2025 Con- ference on Empirical Methods in Natural Language Processing: System Demonstrations, pages 558–590.

{

"symbol": "C3", "function_note": "...", "association": {"hr_95ci": "...", "p_value

": "..."}, "citations": ["12345678"] } ], "ppi_clusters": [

Gongbo Zhang, Qiao Jin, Denis Jered McInerney, Yong

Chen, Fei Wang, Curtis L Cole, Qian Yang, Yanshan Wang, Bradley A Malin, Mor Peleg, and 1 others. 2024. Leveraging generative ai for clinical evidence synthesis needs to ensure trustworthiness. Journal of biomedical informatics, 153:104640.

{

"proteins": ["C3", "CFH", "C4A"], "cluster_explanation": "...", "citations": ["12345678"] } ], "uncertainty": "...", "citations": ["12345678"] }

Kunlun Zhu, Jiaxun Zhang, Ziheng Qi, Nuoxing Shang,

Zijia Liu, Peixuan Han, Yue Su, Haofei Yu, and Jiax- uan You. 2025. Safescientist: Enhancing ai scientist safety for risk-aware scientific discovery. In Proceed- ings of the 2025 Conference on Empirical Methods in Natural Language Processing, pages 2289–2317.

This schema gives the Reasoning Agent a nar- row and inspectable output channel. It must state what the pathway does, why it may matter for the disease, which input proteins drive the interpreta- tion, which interaction modules support the mecha- nism, and where evidence is weak or indirect. If no relevant publications are available, citation fields remain empty and the explanation is marked as exploratory.

A Implementation and Artifact Details

This appendix expands the implementation details behind the BioInsight harness. It is organized around the same artifact chain used in the method section: external resources, typed intermediate arti- facts, implementation parameters, and failure han- dling.

A.1 External Biomedical Knowledge Resources

A.3 Implementation Parameters

The harness exposes model choices as configura- tion parameters for the Planning, Search, Reason- ing, Writing, and Visualization Agents. Prompt templates are fixed across diseases; disease speci- ficity enters through the disease name, protein ta- ble, cohort metadata, pathway terms, and retrieved

BioInsight consumes external biomedical knowl- edge through resource-specific modules. Each re- source has a defined role, which prevents heteroge- neous evidence from being merged into an opaque retrieval result.


> **Table 4: External biomedical knowledge resources and their roles in the harness.**

Resource Role in harness Used by

g:Profiler Pathway enrichment over the input protein set Planning Agent PubMed Disease-pathway evidence retrieval and reference normalization

Planning Agent, Reasoning Agent, Citation Formatter Semantic Scholar Literature ranking, citation-count support, and optional snippet-level evidence retrieval

Planning Agent, Query Agent

STRING Protein-protein interaction networks, figures, and external links

Reasoning Agent, Visualization Agent

UniProt-derived knowledge base

Protein function descriptions Query Agent, Reasoning Agent

Open Targets Target descriptions, drug context, bibliography, and associated diseases

Query Agent, Visualization Agent

DGIdb Pharmacogenetic drug-protein edges Visualization Agent


> **Figure 6: Typed artifact flow in BioInsight. Evidence retrieval, reasoning, writing, and visualization exchange**

> structured objects rather than only free-form text.

function annotations are missing for a protein, the protein-level explanation is omitted or marked un- available. If no protein-protein interaction edges are found, the system avoids cluster-level interpre- tation and instead treats proteins individually.

evidence packets. Table 5 summarizes the key non- prompt parameters used in the current configura- tion.

Artifacts are stored under a disease-specific re- sult directory. The cache directory stores ranked pathway tables, selected top pathways, pathway overview drafts, iterative report drafts, citation- formatted reports, dashboard schemas, and ren- dered dashboard pages. External fetches are cached as JSON files so repeated runs can reuse STRING and DGIdb responses subject to each resource’s licensing terms.

External translational resources are also handled conservatively. If Open Targets or DGIdb returns no records for a protein, the system does not infer therapeutic relevance from absence of evidence. If STRING fails to return an interactive link, the re- port can still retain the generated network image, or omit the STRING link if no network is available. If a PubMed metadata lookup fails during citation for- matting, the PubMed link is retained and missing metadata is surfaced rather than silently dropping the citation.

A.4 Quality Control and Failure Handling

The harness is designed to expose evidence insuffi- ciency rather than hide it behind fluent text. Table 6 summarizes common failure modes and the corre- sponding graceful degradation behavior.

Language-model failures are handled at artifact boundaries. If the Reasoning Agent returns mal- formed JSON, the raw response is preserved as an inspectable artifact and can be retried or ex- cluded from final report assembly. If a coherence revision damages tables, links, or image syntax, downstream parsing and manual inspection can identify the failure because the pre-revision and post-revision drafts are both stored.

If pathway enrichment returns no significant pathways, the system should report that the input protein set does not support a pathway-level inter- pretation rather than hallucinating mechanisms. If a pathway is statistically enriched but has little or no PubMed support, it can remain in the ranked table, but its narrative interpretation should be marked as literature-weak or exploratory. If UniProt-derived


> **Table 5: Key implementation parameters used in the current BioInsight harness.**

Component Parameter Value

Pathway enrichment Organism hsapiens Pathway enrichment Significance threshold user_threshold = 0.05 Pathway enrichment Correction method significance_threshold_method = "fdr" Pathway enrichment IEA annotations no_iea = True Pathway enrichment Ordered query ordered = False Pathway enrichment Highlighted terms highlight = True Pathway filtering Term size range 10 < term_size < 500 Duplicate removal BioBERT cosine threshold 0.98 Pathway selection Per-source retained pathways k = 2 Report generation Maximum analyzed pathways 12 PubMed retrieval Maximum records per query 50 records with abstracts Semantic Scholar retrieval Maximum records per query 30 records Publication validation Score threshold Spub ≥0.25 Publication storage Validated publications per pathway Top 20 Reasoning clusters Retained PPI components Top 2 connected components STRING dashboard retrieval Confidence threshold 0.4 STRING dashboard retrieval Maximum fetched proteins Top 80 proteins by literature and pathway evidence STRING dashboard retrieval Maximum stored edges 60 edges per query DGIdb retrieval Queried genes Top 8 ranked genes LLM generation Temperature 0.7 LLM retry Default retry setting 5 retries


> **Table 6: Failure modes and graceful degradation behavior.**

Failure mode System behavior

No significant enriched pathways

Report evidence insufficiency instead of generating unsupported pathway mechanisms.

Enriched pathway with weak literature support

Retain the pathway in the ranked table when appropriate, but mark the interpretation as literature-weak or exploratory. Missing protein function annotation

Omit the protein-level explanation or mark function evidence unavailable.

No protein-protein interaction edges

Skip cluster-level interpretation and analyze proteins individually.

STRING link unavailable Retain the generated network image when available or omit the link if no network can be produced. Open Targets or DGIdb returns no records

Do not infer therapeutic relevance from absence of records.

PubMed metadata lookup fails Retain the PubMed link and surface missing metadata rather than dropping the citation. Malformed Reasoning Agent JSON

Preserve the raw response for inspection, retry, or exclusion from final report assembly.

Writing revision damages tables, links, or image syntax

Use stored pre-revision and post-revision drafts for inspection and correction.

External API unavailable Fall back to cached responses or narrower retrieval behavior when possible.

B Experimental Setup Details

An example from BioInsight-100 is shown be- low. The question requires the model to integrate protein-function annotations with interaction evi- dence and to recognize when the interaction context is weak or absent.

This appendix provides reproducibility details for the three experimental settings described in Experi- ment Section and the surrounding experiments.

B.1 Baseline and Input Matching

{

"type": "function_ppi_integration", "question": "How do known interactions inform

All systems receive the same disease names, pro- tein association tables, and task instructions within each evaluation setting. Search-enabled baselines are given the same evidence-seeking objective and a comparable retrieval budget when applica- ble. BioInsight uses fixed agent prompts, pathway- ranking weights, retrieval parameters, citation- formatting rules, and dashboard-generation rules across all disease cases. Automatic metrics are computed from raw model outputs without manual correction.

CEND1’s role in neuronal differentiation ?", "answer": "Integration is limited because no

high-confidence STRING associations are available; UniProt notes homodimerization,

aligning with a membrane role in promoting neuronal differentiation.", "evidence": [

{

"source": "STRING", "confidence": "high", "field": "No high-confidence associations

for Q8N111 in provided STRING context" }, {

For RQ1 and RQ2, we compare BioInsight with GPT-5.5, DR-Tulu-8B, Gemma-4-31B, and Qwen3.5-9B. For RQ3, we evaluate Claude Son- net 4.6, GPT-5.5 + Search, Gemini Deep Research, Gemma-4-31B + Search, Qwen3.5-9B + Search, DR-Tulu-8B, BioInsight, and BioInsight without search decomposition. The ablated BioInsight vari- ant keeps the report-generation stage but removes the full explicit search and reasoning decompo- sition, allowing us to test the contribution of the harnessed evidence workflow.

"source": "UniProt", "confidence": "high", "field": "FUNCTION; SUBUNIT (

homodimerization)" } ] }

B.4 Disease Cases for Report Evaluation


> **Table 7 summarizes the five disease cases used in**

> end-to-end report and dashboard evaluation. The
set covers neurodegenerative, psychiatric, cardio-
vascular, renal/metabolic, and autoimmune/inflam-
matory disease contexts.

B.2 BioASQ Phase B

BioASQ Phase B is used as a standardized exact- answer test for yes/no, factoid, and list questions. We evaluate Batch 1 and report yes/no accuracy, yes/no macro F1, factoid strict accuracy, factoid mean reciprocal rank, and list F-measure. This setting checks whether each system can select con- cise biomedical entities and evidence-supported answers before those entities are expanded into longer reports and dashboards.

C Human Evaluation Protocol

This appendix describes the human evaluation protocol used for report-level expert assessment. The goal of the evaluation is to assess whether BioInsight produces biomedical synthesis outputs that are complete, scientifically valid, evidence- integrative, well-prioritized, and usable for biomed- ical researchers.

B.3 BioInsight-100

Evaluation setup. We evaluate system outputs on the five disease–protein interpretation cases in Table 7. For each disease case, evaluators are shown anonymized outputs from four systems: GPT-5.5 + Search, Gemini Deep Research, DR- Tulu-8B, and BioInsight. Each output consists of the generated biomedical interpretation report and, when available, the associated dashboard or evi- dence views. System names are hidden from eval- uators, and outputs are presented in randomized

BioInsight-100 is constructed from UniProt- derived function records and STRING interac- tion evidence. GPT-5.5 is used to generate can- didate protein-function questions that require cross- evidence reasoning, and biomedical experts select 100 challenging questions to form BioInsight-100. Each answer is scored on a 0–10 scale according to biomedical correctness, evidence use, protein- function specificity, pathway or interaction reason- ing, and clarity.


> **Table 7: Disease categories and evaluation rationale for end-to-end report and dashboard evaluation.**

Disease Type Key mechanistic features Evaluation value for BioInsight AD / Alzheimer’s disease Neurodegenerative dis- ease

Tests integration of complex neurological mechanisms and long-term disease pro- gression evidence. Depression Psychiatric disorder Neurotransmitters, inflammation, endocrine regulation, gene– environment interactions

Protein aggregation, neuroinflamma- tion, synaptic degeneration, aging

Tests interpretation under heterogeneous mechanisms and uncertain disease biol- ogy. Atrial fibrillation and flut- ter

Cardiac rhythm disorder Electrophysiological remodeling, cardiac structural remodeling, inflammation, coagulation risk

Tests integration of clinical risk, biomarker, and proteomic evidence.

Tests interpretation of chronic progres- sion, organ damage, and multi-pathway protein evidence. Rheumatoid arthritis Autoimmune/inflammatory disease

Inflammation, fibrosis, oxidative stress, tubular injury

Chronic kidney disease Chronic metabolic/renal disease

Immune-cell activation, cytokines, synovial inflammation, tissue de- struction

Tests interpretation of immune pathways and target-relevant protein evidence.

order to reduce ordering and model-identity bias. Evaluators assign a score from 1 to 5 for each eval- uation dimension and provide a brief justification for each score. We invited four domain experts for human evaluation.

biologically plausible, disease-relevant, and sup- ported by evidence.

Evidence grounding and traceability measures whether conclusions are explicitly grounded in vis- ible evidence from the report, dashboard, and in- termediate artifacts. Evaluators check whether the output preserves an auditable chain from raw or intermediate evidence to interpretation, such as pro- tein statistics, mapped genes, enriched pathways, pathway rankings, PPI edges, literature records, database identifiers, drug records, and citation- linked claims. Strong outputs keep evidence close to the relevant claim, expose evidence fields such as p-values, enrichment scores, hit counts, confi- dence scores, literature counts, PubMed references, or drug–target records, and disclose weak, miss- ing, indirect, or uncertain evidence. Outputs are penalized when plausible claims are untraceable, citations are only loosely connected to claims, ev- idence provenance is mixed or unclear, or mecha- nistic conclusions exceed the strength of the cited evidence.

Evaluation dimensions. Following our report- level expert evaluation guideline, each output is rated along five dimensions: comprehensiveness, biomedical validity, evidence grounding and trace- ability, prioritization and research depth, and read- ability/dashboard usability.

Comprehensiveness measures whether the sys- tem provides a complete end-to-end interpretation of the input protein list. This includes pathway enrichment, key proteins, molecular functions, dis- ease relevance, molecular mechanisms, PPI or net- work context, therapeutic associations when rel- evant, citations, dashboard evidence views, and cross-links among proteins, pathways, mechanisms, and translational findings. Reports are penalized when they cover only isolated proteins or pathways, omit important disease-protein interpretation mod- ules, or include modules only as shallow labels.

Prioritization and research depth measures whether the system identifies which proteins, path- ways, mechanisms, PPI modules, biomarkers, drug links, or translational findings deserve deeper anal- ysis using evidence-weighted biomedical reason- ing. Evaluators consider whether rankings are sup- ported by visible quantitative and qualitative ev- idence, including enrichment statistics, pathway scores, mapped genes, protein hit counts, literature support, hazard ratios, PPI confidence, database ev- idence, druggability, and disease specificity. Strong outputs distinguish core data-supported findings from supporting proteins, peripheral associations, uncertain hits, indirect evidence, and speculative hypotheses. Outputs are penalized for arbitrary ordering, significance-only ranking without biolog-

Biomedical validity measures whether the bi- ological statements, disease interpretations, path- way explanations, protein annotations, mechanism chains, drug associations, and network interpreta- tions are factually correct, scientifically plausible, and appropriately qualified. Evaluators penalize hallucinated mechanisms, incorrect protein func- tions, generic disease associations, unsupported causal language, overextended clinical inference, fabricated or loosely related citations, and context errors such as tissue, stage, species, or biomarker- versus-causality mismatch. Rare or non-obvious pathways are not penalized merely for being un- common; they receive positive credit when they are

Score General interpretation 1 Very poor. The output is incomplete, misleading, unsupported, or difficult to use. 2 Weak. Some relevant information is present, but im- portant components are missing, shallow, inaccurate, or poorly connected. 3 Moderate. The output covers major components and is mostly understandable, but evidence integration, validity, ranking transparency, or usability remains limited. 4 Strong. The output is largely complete, disease- relevant, evidence-supported, and useful, with only minor issues. 5 Excellent. The output is comprehensive, scientifi- cally reliable, deeply synthesized, well-prioritized, and easy to inspect through the report and dashboard.


## 1 indicates no meaningful synthesis beyond lists of

facts, while a score of 5 indicates a disease-specific,
evidence-weighted, uncertainty-aware mechanis-
tic model with clear therapeutic implications. For
ranking quality, a score of 1 indicates arbitrary or
misleading rankings, while a score of 5 indicates
highly interpretable, evidence-weighted, disease-
specific, uncertainty-aware, and actionable priori-
tization. For readability and dashboard usability,
a score of 1 indicates that the report is difficult to
follow or the dashboard is confusing, while a score
of 5 indicates a coherent disease story and intuitive,
accurate, source-traceable evidence exploration.


> **Table 8: General five-point rating scale used in expert**

> evaluation. Dimension-specific scoring instructions are
provided to evaluators.

Qualitative analysis and Bias control. In ad- dition to numerical scores, we analyze evaluator justifications to identify recurring strengths and failure modes. We group comments into categories such as incomplete evidence coverage, generic dis- ease interpretation, unsupported causal language, weak protein-to-pathway linkage, shallow ranking explanation, citation misalignment, dashboard in- consistency, and poor evidence traceability. These qualitative findings are used to interpret the quanti- tative results above.

ical interpretation, literature-only ranking without enrichment context, shallow lists, generic pathway discussion, or over-prioritized translational claims without traceable support.

Readability and dashboard usability measures whether the report and dashboard are understand- able, well-structured, visually clear, and useful for biomedical evidence exploration. For reports, eval- uators consider disease-story coherence, logical flow, terminology control, citation placement, and clarity of uncertainty. For dashboards, evaluators consider whether users can move from overview to detail, trace visual elements to evidence sources, drill down from pathways to proteins and citations, compare mechanisms or evidence strength, and in- teract with the interface without excessive cognitive load.

The evaluation is blinded with respect to system identity, but it is still limited by the number of dis- ease cases and expert evaluators. Biomedical inter- pretation is also inherently judgment-dependent: experts may differ in how they weigh disease specificity, mechanistic plausibility, and evidence strength. To reduce bias, all systems are evaluated on the same disease cases, using the same scoring rubric, randomized output order, and identical eval- uation forms. Nevertheless, the human evaluation should be interpreted as expert assessment of re- search utility and evidence quality, rather than as a definitive biomedical validation of every generated claim.

Rating scale. All dimensions are scored on a five- point Likert scale. Although each dimension has dimension-specific criteria, the general interpreta- tion of the scale is as follows:

Dimension-specific scoring guidelines. For cov- erage, a score of 1 indicates that the system only lists proteins or pathways with little interpretation, while a score of 5 indicates comprehensive cover- age of pathway enrichment, protein function, dis- ease relevance, mechanisms, PPI or interaction clusters, therapeutic associations, citations, and dashboard evidence exploration. For biomedical validity, a score of 1 indicates severe biomedical errors or hallucinated mechanisms, while a score of 5 indicates highly accurate, disease-specific, mech- anistically rigorous, and uncertainty-aware inter- pretation. For evidence synthesis depth, a score of

D The Use of Large Language Models (LLMs)

In order to reduce typos during the writing process and to optimize complex sentence structures so that the article becomes simpler and easier to read, we use mainstream large language models to refine certain paragraphs. For example, we use prompts such as “Help me correct the typos and grammati- cal errors in the above text, and streamline the logic to make it clear and easy to understand.”
