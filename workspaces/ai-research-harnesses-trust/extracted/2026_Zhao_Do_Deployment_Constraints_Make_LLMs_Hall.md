---
workspace_id: "SCI-000144"
doi: null
title: "Do Deployment Constraints Make LLMs Hallucinate Citations? An Empirical Study across Four Models and Five Prompting Regimes"
year: 2026
extraction_engine: "pymupdf"
---
# 2026 Zhao Do Deployment Constraints Make LLMs Hall

Do Deployment Constraints Make LLMs Hallucinate Citations?

An Empirical Study across Four Models and Five Prompting

Regimes

Chen Zhao cz1296@nyu.edu New York University

Yuan Tang yuantang@alumni.cmu.edu Carnegie Mellon University

Yitian Qian qyt024@bu.edu Boston University

United States

United States

United States


## Abstract

to assisting with literature surveys [5, 7]—unreliable citations can propagate through evidence synthesis pipelines that the SE commu- nity relies on. Understanding how deployment constraints affect citation quality is therefore a prerequisite for responsibly adopting LLM-assisted writing tools in SE practice.

LLMs are increasingly used to draft academic text and to support software engineering (SE) evidence synthesis, but they often hallu- cinate bibliographic references that look legitimate. We study how deployment-motivated prompting constraints affect citation verifia- bility in a closed-book setting. Using 144 claims (24 in SE & CS) and a deterministic verification pipeline (Crossref + Semantic Scholar), we evaluate two proprietary models (Claude Sonnet, GPT-4o) and two open-weight models (LLaMA 3.1–8B, Qwen 2.5–14B) across five regimes: Baseline, Temporal (publication-year window), Survey- style breadth, Non-Disclosure policy, and their combination. Across 17,443 generated citations, no model exceeds a citation-level exis- tence rate of 0.475; Temporal and Combo conditions produce the steepest drops while outputs remain format-compliant (well-formed bibliographic fields). Unresolved outcomes dominate (36–61%); a 100-citation audit indicates that a substantial fraction of Unresolved cases are fabricated. Results motivate post-hoc citation verification before LLM outputs enter SE literature reviews or tooling pipelines.

arXiv:2603.07287v1  [cs.IR]  7 Mar 2026

We address this gap with an automated verification framework that parses each citation, queries Crossref and Semantic Scholar, and assigns one of three labels: Existing, Unresolved, or Fabricated. We evaluate four LLMs under five prompting conditions with determin- istic decoding and find that temporal constraints are associated with the steepest drop in verifiability even as models maintain format compliance; survey-style prompting widens the proprietary–open- weight gap in verifiability; and unresolved outcomes constitute 36–61% of citations, forming the largest category in the majority of model–condition cells.

We structure our investigation around three research questions: RQ1 How do deployment constraints (temporal, survey-style, non-

disclosure) affect citation verifiability? RQ2 How do these effects differ between proprietary and open-

weight models? RQ3 How does combining all three constraints compare to apply-

CCS Concepts

• General and reference →Empirical studies; • Computing methodologies →Natural language processing.

ing each individually?

Our contributions are (1) a curated dataset of 144 claims spanning six academic domains (including 24 in SE & CS), (2) an automated verification pipeline with an audited three-way label taxonomy (Cohen’s 𝜅=0.63 vs. human labels), and (3) an empirical analysis of how deployment constraints and the proprietary–open-weight distinction affect citation verifiability.

Keywords

LLM hallucination, citation hallucination, large language models, empirical evaluation, AI for software engineering, systematic liter- ature reviews, automated verification, LLM reliability

1 Introduction

2 Related Work

Large language models (LLMs) have demonstrated strong capa- bilities in generating fluent academic prose, leading to their in- creasing use in scholarly writing and evidence synthesis. Yet they continue to exhibit citation hallucination [2, 19]: the generation of bibliographic references that look complete (authors, venues, DOIs) but do not correspond to verifiable works. These errors are often attributed to next-token prediction objectives and distributional shifts [13]. However, how citation reliability behaves under real- istic deployment constraints—temporal restrictions, survey-style breadth pressure, and non-disclosure policies that forbid claims of training-data access—remains poorly understood.

Hallucination in language models. LLM hallucination has been widely studied across summarization and knowledge-intensive gen- eration [3, 8, 12, 18]. McKenna et al. [13] trace many failures to distributional gaps between training and deployment, while Kalai et al. [9] argue that next-token prediction can incentivize plausible completion over calibrated uncertainty. We study an audit-friendly manifestation: hallucinated bibliographic citations, where outputs can be checked against external scholarly indexes.

Citation hallucination and verifiable generation. Prior work au- dits LLM-generated references but often adopts a binary real-or- fabricated label under a single prompting setup. Walters and Wilder [19] reported high rates of non-existent citations from ChatGPT, and Agrawal et al. [2] showed that hallucinated references often contain internally inconsistent metadata. Complementary work

This problem is especially relevant to software engineering (SE) research, where systematic literature reviews (SLRs), mapping studies, and related-work sections are core methodological activi- ties [10]. As LLMs are increasingly integrated into SE workflows— from drafting technical reports and architecture decision records

Conference’17, July 2017, Washington, DC, USA Chen Zhao, Yuan Tang, and Yitian Qian

evaluates cited generation more broadly: ALCE benchmarks end-to- end generation with citations [6], and Liu et al. [11] audit citation precision and recall in generative search engines. Our work sys- tematically varies deployment constraints (Temporal, Survey-style breadth, Non-Disclosure, and Combo) in a closed-book reference- list setting and uses a three-way taxonomy (Existing, Unresolved, Fabricated) that distinguishes clearly fabricated references from cases that cannot be reliably verified.

paragraph with exactly 5 citations. Temporal adds a strict publication- year window (5 citations); all 144 windows end at 2025 with a me- dian span of five years, targeting recent literature where parametric knowledge is weakest. Survey asks for a related-work synthesis organized into 3–4 approach categories with 8 citations, reflecting breadth pressure in evidence-synthesis writing. Survey/Combo re- quest 8 citations (vs. 5 for the other conditions) because a 5-citation budget yields fewer than two references per category, which is atypical for survey-style writing; since our primary outcomes are citation-level proportions, the differing budgets change observation counts rather than outcome definitions, and we additionally report per-claim verification fractions (Figure 2) for a claim-equal view. Non-Disclosure instructs the model not to claim access to mem- orized training documents (5 citations), simulating deployment policies in commercial writing assistants. Combo combines all three constraints (8 citations). All conditions use deterministic decoding (temperature 0) with no retrieval augmentation. The full design yields 144×5×4 = 2,880 runs producing 17,443 individual citations.

LLMs for scientific writing. Retrieval-augmented pipelines with structured planning can reduce hallucination in literature review generation [1], yet hallucinated references remain common even with explicit grounding instructions [17]. These issues are particu- larly salient for evidence-synthesis workflows (e.g., SLRs) that are common in SE research [10] and for emerging LLM-assisted SE tooling surveyed in recent work [5, 7]. Our work is complemen- tary: rather than proposing a new generation pipeline, we present a deterministic verification framework and use it to quantify how citation reliability changes under deployment-motivated prompting constraints in a closed-book setting.

4 Verification Pipeline

Our pipeline checks every generated citation against two scholarly databases—Crossref and Semantic Scholar—which together cover most of the indexed literature. The same pipeline runs identically on every model and condition. The code is publicly available.2

3 Experimental Design

Task formulation. We study citation reliability in LLM-generated academic-style writing. Each model receives a question-style prompt and generates a concise academic paragraph followed by a struc- tured reference list with fixed bibliographic fields (title, authors, venue, year, DOI, and URL when available), enabling determinis- tic parsing and automated verification. Prompts request exactly 𝑘citations (5 for Baseline/Temporal/Non-Disclosure; 8 for Sur- vey/Combo), but we do not enforce count compliance: all references in the output are verified and the realized count is recorded. Verifi- cation uses a weighted metadata similarity score (Eq. 1); details are in Section 4.

Parsing. The pipeline extracts the citation list from each model output and breaks every reference into structured fields: title, au- thors, venue, year, and DOI. As in the task formulation, all refer- ences present in the output are extracted (no truncation, padding, or retries). We use rule-based heuristics and regular expressions; references that cannot be parsed are carried forward as unresolved.

Candidate retrieval. For each parsed citation, we run up to three lookups: (1) if the model supplied a DOI, we check it directly via Crossref; (2) we search Semantic Scholar by title (returning up to 𝑘=5 candidates); (3) we search Crossref by title (again up to 𝑘=5). All retrieved records are normalized into a common format.

Claim dataset. Our dataset contains 144 question-style prompts (e.g., “What evidence supports...”) spanning six domain groups: SE & CS (24 claims covering software engineering, AI/ML, data/HCI, security, and systems), Natural Sciences (24), Medicine & Health (24), Social Sciences (24), Humanities (24), and Interdisciplinary (24). Each record includes a domain label, an optional temporal window, and optional seed anchors (keyword-only topic hints that orient the model without naming specific papers). When present, the same anchors are provided across all conditions for a given claim. The 144 prompts were randomly sampled (fixed seed) from a candidate pool of 240 items sourced from publicly accessible academic materials, pre-screened for suitability, and stratified by domain.

Scoring. Each candidate is scored against the parsed citation using a weighted combination:

𝑠= 0.60 · 𝑡+ 0.20 · 𝑎+ 0.15 · 𝑦+ 0.05 · 𝑣 (1)

where 𝑡is fuzzy title similarity (token-set ratio), 𝑎is author last- name overlap, 𝑦is year agreement (1.0 if exact, 0.5 if off by one, 0 otherwise), and 𝑣is venue similarity (partial ratio). Title receives the heaviest weight because it is the most discriminative field in practice.

Models. We evaluate two proprietary models—Claude Sonnet (Anthropic) and GPT-4o (OpenAI)—and two open-weight models— Qwen 2.5–14B (Alibaba) and LLaMA 3.1–8B (Meta) [4, 14, 15, 20].1

Labeling. Each citation receives one of three labels: Existing (score ≥0.85), Unresolved (0.60 ≤score < 0.85), or Fabricated (score < 0.60 or no candidate found). For temporal conditions, citations outside the stated publication-year window are additionally flagged. We set 0.85 as the match threshold: above this score, candidates con- sistently correspond to the correct paper despite minor metadata drift (e.g., abbreviated venues, missing middle initials). The 0.60 boundary separates weak, likely spurious matches from partially plausible ones; below 0.60, candidates typically share only generic

Because the proprietary models are presumably larger, our design cannot fully disentangle model scale from the proprietary–open- weight distinction (Section 6).

Prompting conditions. Each claim is evaluated under five condi- tions via fixed prompt templates. Baseline requests one academic

1Exact model identifiers are listed in the replication package.

2See the replication package at https://github.com/Zerichen/Citation-Hallucination.

Do Deployment Constraints Make LLMs Hallucinate Citations? Conference’17, July 2017, Washington, DC, USA


> **Table 1: Pipeline vs. human labels on a stratified sample of**

> 100 citations. Overall agreement: 75%; Cohen’s 𝜅=0.63.

0.235, while LLaMA 3.1–8B and Qwen 2.5–14B reach only 0.068 and 0.090. The proprietary–open-weight gap is large and statistically clear (Δ = +0.229, 95% CI [0.191, 0.266]; Table 3), not explained by citation volume (≈5 per claim for all models) and confirmed across the full per-claim distribution (Figure 2). This difference persists and is often larger under stress, which may reflect differences in training data coverage and model scale, though we cannot isolate these factors with the current study design.

Human label

Pipeline label Exist. Unres. Fabric.

Existing 31 1 0 Unresolved 4 15 16 Fabricated 2 2 29

Temporal constraints produce the steepest decline (RQ1). Tempo- ral constraints reduce citation quality more than any other single condition. Claude Sonnet falls from 0.381 to 0.119 (Δ = −0.261, 95% CI [−0.317, −0.207]); GPT-4o drops comparably (Δ = −0.216, CI [−0.266, −0.168]); the open-weight models, already near zero, decline further (Δ = −0.076 for Qwen and −0.057 for LLaMA; Table 3). Critically, direct temporal violations are extremely rare (0.001–0.026): the models obey the temporal constraint but cannot produce verifiable references within it, a failure mode that format- level compliance checks would miss entirely.

tokens. Unresolved is intentionally a triage bucket: it includes (i) real papers the pipeline cannot fully confirm due to incomplete or discordant metadata, and (ii) fabricated citations that partially overlap with unrelated records. We therefore report it separately rather than force a binary decision.

Aggregation and metrics. Rates of Existing, Fabricated, and Unre- solved (summing to 1) are averaged over all citations in a model– condition cell, with 95% cluster-bootstrap CIs (1,000 resamples over 144 claims) to account for within-claim correlation. For key pairwise comparisons, we report the bootstrap CI of the difference (Δ) in ex- istence rate [16]; a difference is statistically meaningful when its CI excludes zero. We complement citation-weighted rates with the per- claim verification fraction (Figure 2), 𝑓𝑖= #Existing𝑖/#TotalParsed𝑖, which weights each claim equally regardless of citation count.

Survey prompting is associated with a larger proprietary–open- weight gap (RQ1, RQ2). Under the Survey condition, the proprietary– open-weight gap increases to its largest observed value (Δ = +0.310, 95% CI [0.274, 0.349]; Table 3). Models slightly under-produce rel- ative to the requested 8 citations (Avg. #Cit. 7.28–8.00; Table 2), but the pattern persists. Claude Sonnet improves—existence rises from 0.381 to 0.475 (Δ = +0.094, CI [0.028, 0.162]) with compara- ble fabrication (0.157→0.161)—suggesting it draws on a sufficient stock of real references. GPT-4o’s decline under Survey is not sta- tistically significant (Δ = −0.032, CI [−0.092, 0.029]). Open-weight models show the opposite trend: Qwen 2.5–14B drops significantly (Δ = −0.070, CI [−0.101, −0.041]) and reaches 0.547 fabrication, the highest in the study.

Pipeline validation. We manually verified a stratified sample of 100 citations against Google Scholar and DBLP (Table 1). Overall agreement was 75% and Cohen’s 𝜅(pipeline vs. human) was 0.63. Precision was 0.97 for Existing and 0.88 for Fabricated, but only 0.43 for Unresolved. The dominant error was Unresolved →Fabricated (16 cases), so our reported fabrication rates are likely conservative; we therefore treat Unresolved as high-risk and report a reclassification sensitivity analysis in Section 5.

5 Results

Non-Disclosure instructions redistribute rather than eliminate er- rors (RQ1). Non-Disclosure prompting has a subtler effect: existence- rate declines are small, with marginal decreases for GPT-4o (Δ = −0.060, CI [−0.119, −0.001]) and LLaMA (Δ = −0.023, CI [−0.045, −0.001]), while Claude Sonnet and Qwen show no significant change (Table 3). What changes is the error balance: some verified citations shift into the unresolved bin (e.g., Claude Sonnet existence 0.381→0.349, unresolved 0.462→0.487). DOI completeness drops under Non- Disclosure (most pronounced for LLaMA, −11.4 percentage points3), and because DOI is the strongest verification signal, its suppres- sion pushes citations from Existing into Unresolved—shifting errors from “obviously wrong” into “hard to tell.”


> **Table 2 reports citation-weighted verification metrics; Figure 1**

> visualizes the outcome distribution; Figure 2 summarizes per-claim
verification fractions (weighting each claim equally regardless of
citation count). Figure 3 breaks down existence rate by domain;
Table 3 provides bootstrap CIs of the difference (Δ) in existence
rate for key pairwise comparisons.

No model verifies a majority of its citations. No model, under any condition, achieves an existence rate above 0.50 (the peak is 0.475 for Claude Sonnet under Survey). Under the strictest interpretation— counting a claim as verified only if every citation passes—very few claims qualify even for the best model. Different constraints produce different failure signatures, not just uniform degradation.

Combining constraints produces the worst outcomes (RQ3). The Combo condition produces the most severe degradation (Fig- ure 1). Three of four models show existence rates near zero; only Claude Sonnet retains a non-trivial 0.106 (Δ=−0.275, CI [−0.329, −0.220]). GPT-4o drops comparably (Δ = −0.230, CI [−0.274, −0.185]); both open-weight models collapse (Table 3). For pro- prietary models, the combined decline exceeds the largest single- constraint drop; open-weight models exhibit a floor effect. Critically,

Per-claim distributions reveal partial verification. Figure 2 shows the per-claim verification fraction. Even when aggregate rates are low, some claims receive partially verified sets: Claude Sonnet at Baseline has a median per-claim fraction of 0.40 (IQR 0.20–0.60), while for open-weight models the median is zero in most conditions. Low aggregates do not mean every claim is entirely unverified, but many claims receive no verified citations at all.

Proprietary models do better, but not well (RQ2). At baseline, Claude Sonnet and GPT-4o achieve existence rates of 0.381 and

3DOI completeness rates by model and condition are reported in the replication package.

Conference’17, July 2017, Washington, DC, USA Chen Zhao, Yuan Tang, and Yitian Qian


> **Table 2: Citation-level verification metrics with 95% bootstrap CIs (𝑁=144 claims per cell). Conditions: Base = Baseline, Temp =**

> Temporal, Surv = Survey, Non-Disc. = Non-Disclosure. T. Viol. = temporal violation rate.

Model Cond. N Existing ↑ Fabricated ↓ Unresolved T. Viol. Avg. #Cit.

Claude Sonnet Base 144 .381 [.335,.426] .157 [.126,.190] .462 [.382,.549] .000 5.00 GPT-4o Base 144 .235 [.189,.281] .281 [.239,.327] .484 [.403,.569] .000 4.97 LLaMA 3.1–8B Base 144 .068 [.049,.090] .369 [.327,.411] .563 [.479,.646] .000 4.98 Qwen 2.5–14B Base 144 .090 [.065,.118] .442 [.398,.486] .468 [.382,.549] .000 4.98

Claude Sonnet Temp 144 .119 [.089,.151] .347 [.306,.392] .533 [.451,.618] .015 5.00 GPT-4o Temp 144 .019 [.008,.033] .451 [.412,.493] .529 [.444,.611] .001 5.00 LLaMA 3.1–8B Temp 144 .011 [.004,.019] .394 [.351,.440] .595 [.514,.674] .026 5.01 Qwen 2.5–14B Temp 144 .014 [.004,.025] .455 [.408,.499] .531 [.444,.611] .015 4.99

Claude Sonnet Surv 144 .475 [.425,.523] .161 [.133,.189] .364 [.285,.444] .000 8.00 GPT-4o Surv 144 .203 [.165,.246] .302 [.262,.345] .495 [.410,.576] .000 7.59 LLaMA 3.1–8B Surv 144 .038 [.025,.053] .436 [.392,.475] .526 [.444,.611] .000 7.95 Qwen 2.5–14B Surv 144 .020 [.009,.032] .547 [.509,.584] .433 [.347,.514] .000 7.28

Claude Sonnet Non-Disc. 144 .349 [.302,.397] .165 [.129,.201] .487 [.403,.569] .000 4.90 GPT-4o Non-Disc. 144 .175 [.142,.210] .317 [.271,.360] .508 [.424,.590] .000 5.00 LLaMA 3.1–8B Non-Disc. 144 .045 [.029,.066] .398 [.357,.435] .557 [.472,.639] .000 4.97 Qwen 2.5–14B Non-Disc. 144 .078 [.054,.104] .410 [.368,.453] .512 [.431,.597] .000 4.99

Claude Sonnet Combo 144 .106 [.078,.142] .359 [.318,.399] .536 [.451,.618] .027 7.61 GPT-4o Combo 144 .005 [.000,.012] .452 [.418,.489] .543 [.465,.625] .000 7.38 LLaMA 3.1–8B Combo 144 .008 [.003,.014] .386 [.343,.423] .606 [.521,.681] .000 7.99 Qwen 2.5–14B Combo 144 .001 [.000,.003] .507 [.468,.543] .492 [.410,.576] .000 7.56


> **Figure 1: Citation-level outcome distribution (Existing, Unresolved, Fabricated) for each model under all five conditions, shown**

> as stacked proportions summing to one. “Non-Disc.” denotes the non-disclosure condition.


> **Figure 2: Per-claim verification fraction by model and condition (boxes show IQR with median; whiskers follow the 1.5 × IQR**

> convention). “Non-Disc.” denotes the non-disclosure condition.

cell’s Unresolved mass using these rates, fabricated rates increase to 0.33–0.75 and existence rates to 0.06–0.52, while the direction of all constraint effects and the proprietary–open-weight gap remain unchanged. This suggests our main conclusions are robust but that absolute fabrication rates are likely underestimates.

citation volume goes up (7.4–8.0 per claim): models keep generating references even as verifiability erodes.

A large fraction of citations remain automatically unresolvable. Unresolved outcomes account for 36–61% of citations across nearly all cells. Manual validation shows that nearly half of sampled unre- solved citations are fabricated (16 of 35; Table 1), so this category should not be read as “nearly correct.” This validates the three-way classification: collapsing into a binary scheme would hide the large pool of genuinely uncertain citations.

Domain-stratified analysis highlights SE relevance. Figure 3 breaks down the existence rate by domain group and model, aggregated across all five conditions; domain-level differences should be inter- preted descriptively. The SE & CS group (24 claims, 2,926 citations) exhibits an existence rate of 0.132, comparable to the cross-domain average (0.120). Social Sciences achieves the highest rate (0.187),

Sensitivity to reclassifying Unresolved. In the audit, only 15/35 “Unresolved” citations were truly unresolved; 16/35 were fabricated

and 4/35 were existing (Table 1). If we proportionally reassign each

Do Deployment Constraints Make LLMs Hallucinate Citations? Conference’17, July 2017, Washington, DC, USA

loss of verifiability. Second, the unresolved-citation problem: 36–61% of citations across nearly all cells cannot be automatically confirmed or refuted, and our audit shows that roughly half of these are fabri- cated (Table 1). Any binary real-or-fabricated evaluation would hide this large, high-risk category. Third, the proprietary–open-weight gap (Δ up to +0.310; Table 3) persists across all conditions, suggest- ing that the proprietary–open-weight distinction may be a stronger predictor of citation quality than any single prompting constraint.

6.1 Qualitative Error Patterns

Manual inspection of fabricated and unresolved citations reveals four recurring failure modes that format-level checks would not catch:


> **Figure 3: Existence rate by domain (24 claims per group, ag-**

> gregated across conditions).

• Venue laundering. A plausible venue name (e.g., IEEE TSE, ICSE) is paired with a title that does not appear in that venue’s index—or in any index. • Author bricolage. Real-sounding surnames from the target field are recombined into author lists that do not correspond to any actual paper. • Identifier fabrication and omission. Under Non-Disclosure, DOI fields are frequently omitted or replaced with “n/a”; in other conditions, models occasionally generate syntactically plausible but invalid DOIs. • Title drift. Generated titles are near-paraphrases of real papers— close enough to seem familiar but too different to match any indexed record above the 0.85 threshold. These patterns explain why format compliance coexists with low verifiability: every field looks correct in isolation, but the com- bination does not resolve to a real publication.


> **Table 3: Bootstrap 95% CI of the difference (Δ) in existence**

> rate for key pairwise comparisons. Positive Δ favors the first
term. CIs excluding zero are bolded; (ns) = CI overlaps zero.

Comparison 𝚫 95% CI

Prop. vs. open-wt. (exist. rate) Prop. vs. Open-wt. (Base) +.229 [.191, .266] Prop. vs. Open-wt. (Temp) +.057 [.037, .078] Prop. vs. Open-wt. (Surv) +.310 [.274, .349] Prop. vs. Open-wt. (N-D) +.200 [.164, .234] Prop. vs. Open-wt. (Combo) +.051 [.035, .069]

Constraint vs. Base (Claude Sonnet) Temp −Base −.261 [−.317, −.207] Surv −Base +.094 [.028, .162] N-D −Base (ns) −.032 [−.095, .031] Combo −Base −.275 [−.329, −.220]

Constraint vs. Base (GPT-4o) Temp −Base −.216 [−.266, −.168] Surv −Base (ns) −.032 [−.092, .029] N-D −Base −.060 [−.119, −.001] Combo −Base −.230 [−.274, −.185]

6.2 Implications for Practice

For tool and pipeline developers. Constraint satisfaction alone is not a reliable quality signal. Systems surfacing LLM-generated ref- erences should run post-hoc verification against multiple databases and treat Unresolved as high risk.

Constraint vs. Base (LLaMA 3.1–8B) Temp −Base −.057 [−.078, −.038] Surv −Base −.030 [−.048, −.013] N-D −Base −.023 [−.045, −.001] Combo −Base −.060 [−.083, −.040]

Constraint vs. Base (Qwen 2.5–14B) Temp −Base −.076 [−.106, −.047] Surv −Base −.070 [−.101, −.041] N-D −Base (ns) −.012 [−.050, .025] Combo −Base −.089 [−.117, −.063]

For researchers using LLM writing assistance. Treat generated cita- tions as candidates: require persistent identifiers (DOI/arXiv), cross- check metadata (Crossref/Semantic Scholar, plus DBLP/OpenAlex for CS), and manually resolve remaining Unresolved before inclu- sion.

possibly reflecting stronger database coverage. The proprietary– open-weight gap reproduces within every domain group: Claude Sonnet reaches 0.349 in SE & CS while both open-weight models remain below 0.10. These results suggest that the hallucination patterns documented in this study apply directly to the kind of literature SE researchers produce and consume, though subdomain comparisons should be interpreted cautiously given sample size (Section 6).

For the SE community. SE & CS citations appear broadly compara- ble to other domains in our sample. Since Survey-style prompting— closest to SLR drafting [10]—is associated with a larger proprietary– open-weight gap, SE teams relying on open-weight models should be especially cautious.

6.3 Threats to Validity

6 Discussion

Internal validity. Our label boundaries (0.85/0.60) and scoring weights are design choices applied uniformly; alternative settings could move citations between categories. We mitigate this with a manual audit (75% agreement;𝜅=0.63) conducted by the authors. We tested at temperature zero with one prompt template per condition and one fixed phrasing per claim; results therefore characterize constraint types rather than paraphrase robustness, and citation outcomes may vary under alternative wordings of the same claim.

Citation hallucination is a systematic failure whose shape depends on the constraints placed on the model. Three themes emerge. First, compliance without substance: under the Temporal condition every model produces well-formed bibliographic entries that respect the requested year window, yet existence rates fall sharply—GPT-4o drops from 0.235 to 0.019, and both open-weight models reach ef- fectively zero. Format compliance therefore masks a near-complete

Conference’17, July 2017, Washington, DC, USA Chen Zhao, Yuan Tang, and Yitian Qian


## References

External validity. Our 144 English-language claims may lack power for fine-grained comparisons (e.g., individual subdomains), and findings may not generalize to non-English domains or discipline-specific citation norms. With 24 claims per domain group, the domain-stratified analysis (Figure 3) is descriptive; finer-grained breakdowns (e.g., SE subfields such as testing vs. requirements engi- neering) would require a substantially larger claim set. We evaluate four models at a single snapshot; the proprietary–open-weight gap could narrow as open-weight models scale up or incorporate re- trieval, and newer releases may shift absolute rates. Results should therefore be read as characterizing structural patterns (constraint effects, proprietary–open-weight gaps) rather than as fixed bench- marks for any model version.

[1] Shubham Agarwal, Gaurav Sahu, Abhay Puri, Issam H. Laradji, Krishnamurthy DJ

Dvijotham, Jason Stanley, Laurent Charlin, and Christopher Pal. 2024. LitLLM: A Toolkit for Scientific Literature Review. arXiv:2402.01788 [cs.CL] doi:10.48550/ arXiv.2402.01788 [2] Ayush Agrawal, Mirac Suzgun, Lester Mackey, and Adam Kalai. 2024. Do Lan-

guage Models Know When They’re Hallucinating References?. In Findings of the Association for Computational Linguistics: EACL 2024. Association for Compu- tational Linguistics, St. Julian’s, Malta, 912–928. doi:10.18653/v1/2024.findings- eacl.62 [3] Aisha Alansari and Hamzah Luqman. 2025. Large Language Models Hallucination:

A Comprehensive Survey. arXiv:2510.06265 [cs.CL] doi:10.48550/arXiv.2510.06265 [4] Anthropic. 2024. Claude Documentation. https://docs.anthropic.com/claude/docs [5] Angela Fan, Beliz Gokkaya, Mark Harman, Mitya Lyubarskiy, Shubho Sengupta,

Shin Yoo, and Jie M. Zhang. 2023. Large Language Models for Software Engi- neering: Survey and Open Problems. In 2023 IEEE/ACM International Confer- ence on Software Engineering: Future of Software Engineering (ICSE-FoSE). 31–53. doi:10.1109/ICSE-FoSE59343.2023.00008 [6] Tianyu Gao, Howard Yen, Jiatong Yu, and Danqi Chen. 2023. Enabling Large

Construct validity. Our pipeline relies on Crossref and Semantic Scholar; neither indexes everything, so some “fabricated” labels may be false positives (e.g., preprints, workshop papers, or regional- venue articles absent from both databases). Adding DBLP/OpenAlex would likely narrow the Unresolved category. We also do not check whether a verified citation supports the claim; citation–claim align- ment is an important next step.

Language Models to Generate Text with Citations. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing. Association for Computational Linguistics, Singapore, 6465–6488. doi:10.18653/v1/2023.emnlp- main.398 [7] Xinyi Hou, Yanjie Zhao, Yue Liu, Zhou Yang, Kailong Wang, Li Li, Xiapu Luo,

David Lo, John Grundy, and Haoyu Wang. 2024. Large Language Models for Software Engineering: A Systematic Literature Review. ACM Transactions on Software Engineering and Methodology 33, 8 (2024), 1–79. doi:10.1145/3695988 [8] Lei Huang, Weijiang Yu, Weitao Ma, Weihong Zhong, Zhangyin Feng, Haotian

Wang, Qianglong Chen, Weihua Peng, Xiaocheng Feng, Bing Qin, and Ting Liu. 2025. A Survey on Hallucination in Large Language Models: Principles, Taxonomy, Challenges, and Open Questions. ACM Transactions on Information Systems 43, 2 (2025). doi:10.1145/3703155 [9] Adam Tauman Kalai, Ofir Nachum, Santosh S. Vempala, and Edwin Zhang. 2025.

6.4 Future Work

Three directions extend this work beyond the limitations above. First, systematically varying claim phrasing (paraphrase robust- ness) would disentangle prompt sensitivity from constraint effects and clarify how much citation output depends on surface word- ing. Second, comparing closed-book generation against retrieval- augmented settings under the same constraint regimes would iso- late how much hallucination stems from lack of grounding versus policy pressure. Third, embedding the verification pipeline as a real-time post-generation filter—for example, an IDE plugin or a CI check for manuscript drafts—would test its practical utility in SE writing workflows.

Why Language Models Hallucinate. arXiv:2509.04664 [cs.CL] doi:10.48550/arXiv. 2509.04664 [10] Barbara Kitchenham and Stuart Charters. 2007. Guidelines for Per- forming Systematic Literature Reviews in Software Engineering. Tech- nical Report EBSE-2007-01. Keele University and Durham University. https://ebse.webspace.durham.ac.uk/resources/guidelines-for-performing- systematic-literature-reviews-in-software-engineering/ Version 2.3. [11] Nelson F. Liu, Tianyi Zhang, and Percy Liang. 2023. Evaluating Verifiability

in Generative Search Engines. In Findings of the Association for Computational Linguistics: EMNLP 2023. Association for Computational Linguistics, Singapore, 7001–7025. doi:10.18653/v1/2023.findings-emnlp.467 [12] Joshua Maynez, Shashi Narayan, Bernd Bohnet, and Ryan McDonald. 2020. On

Faithfulness and Factuality in Abstractive Summarization. In Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics. Association for Computational Linguistics, 1906–1919. doi:10.18653/v1/2020.acl-main.173 [13] Nick McKenna, Tianyi Li, Liang Cheng, Mohammad Hosseini, Mark Johnson,

7 Conclusion

and Mark Steedman. 2023. Sources of Hallucination by Large Language Models on Inference Tasks. In Findings of the Association for Computational Linguistics: EMNLP 2023. Association for Computational Linguistics, Singapore, 2758–2774. doi:10.18653/v1/2023.findings-emnlp.182 [14] Meta AI. 2024. Introducing Llama 3.1: Our most capable models to date. https:

Across four models and five conditions, deployment constraints consistently worsen citation hallucination—but in qualitatively dif- ferent ways. Temporal constraints sharply reduce verifiability while maintaining format compliance; Survey prompting widens the proprietary–open-weight gap; Non-Disclosure instructions shift errors from “obviously wrong” into “hard to tell”; and models keep citing at high volume even as verifiability erodes. These patterns suggest that prompt engineering alone is unlikely to solve citation hallucination; reliable generation will require retrieval-augmented architectures, built-in verification, or both. For SE researchers, the practical implication is clear: any LLM-generated reference list should be treated as a draft requiring independent verification against scholarly databases before inclusion in reviews, technical reports, or tooling pipelines. More broadly, our benchmark and pipeline provide a reusable foundation for tracking whether cita- tion reliability improves as new models and retrieval-augmented architectures emerge.

//ai.meta.com/blog/meta-llama-3-1/ [15] OpenAI. 2024. GPT-4o System Card. https://openai.com/index/gpt-4o-system-

card/ [16] Nathaniel Schenker and Jane F. Gentleman. 2001. On Judging the Significance

of Differences by Examining the Overlap Between Confidence Intervals. The American Statistician 55, 3 (2001), 182–186. doi:10.1198/000313001317097960 [17] Xuemei Tang, Xufeng Duan, and Zhenguang G. Cai. 2025. Large Language Models

for Automated Literature Review: An Evaluation of Reference Generation, Ab- stract Writing, and Review Composition. In Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing. Association for Computational Linguistics, Suzhou, China, 1602–1617. doi:10.18653/v1/2025.emnlp-main.83 [18] S.M Towhidul Islam Tonmoy, S M Mehedi Zaman, Vinija Jain, Anku Rani,

Vipula Rawte, Aman Chadha, and Amitava Das. 2024. A Comprehensive Survey of Hallucination Mitigation Techniques in Large Language Models. arXiv:2401.01313 [cs.CL] doi:10.48550/arXiv.2401.01313 [19] William H. Walters and Esther Isabelle Wilder. 2023. Fabrication and errors in

the bibliographic citations generated by ChatGPT. Scientific Reports 13, 1 (2023), 14045. doi:10.1038/s41598-023-41032-5 [20] An Yang et al. 2025. Qwen2.5 Technical Report. arXiv:2412.15115 [cs.CL] doi:10.

48550/arXiv.2412.15115

Data availability. A replication package (claim dataset, prompt templates, pipeline code, manual validation annotations, and raw re- sults) is available at https://github.com/Zerichen/Citation-Hallucination.
