---
workspace_id: "SCI-000089"
doi: "10.1093/ofid/ofag401"
title: "Efficacy of a Large Language Model Data Extraction System in Evidence Reviews for Emerging Infectious Diseases: A Randomized Crossover Trial"
year: 2026
extraction_engine: "pymupdf"
---
# 2026 Ishikane Efficacy of a Large Language Model Data Extraction

Open Forum Infectious Diseases

M A J O R A R T I C L E

Efficacy of a Large Language Model Data Extraction System  in Evidence Reviews for Emerging Infectious Diseases:  A Randomized Crossover Trial

Masahiro. Ishikane,1, Yuki Kataoka,2,3,4,5,6,7, Yasushi Tsujimoto,4,8,9,10, Yuki Moriyama,1 Yukimasa Matsuzawa,1 and Norio Ohmagari1

1Disease Control and Prevention Center, National Centre for Global Health and Medicine, Japan Institute for Health Security, Shinjuku, Tokyo, Japan, 2Center for Postgraduate Clinical Training and  Career Development, Nagoya University Hospital, Nagoya, Aichi, Japan, 3Center for Medical Education, Graduate School of Medicine, Nagoya University, Nagoya, Aichi, Japan, 4Scientific Research  Works Peer Support Group (SRWS-PSG), Osaka, Japan, 5Department of Internal Medicine, Kyoto Min-Iren Asukai Hospital, Kyoto, Japan, 6Department of Healthcare Epidemiology, Kyoto University  Graduate School of Medicine/School of Public Health, Kyoto, Japan, 7Department of International and Community Oral Health, Tohoku University Graduate School of Dentistry, Sendai, Miyagi, Japan,  8Oku Medical Clinic, Osaka, Japan, 9Department of Health Promotion and Human Behavior, Kyoto University Graduate School of Medicine/School of Public Health, Kyoto University, Kyoto, Japan,  and 10Division of Rheumatology, Department of Internal Medicine, Showa University School of Medicine, Shinagawa, Tokyo, Japan

Downloaded from academic.oup.com/ofid/article/13/7/ofag401/8736362 by guest on 08 September 2026

Background. Rapid evidence synthesis during emerging infectious and re-emerging disease outbreaks is critical, yet traditional  systematic reviews rarely meet urgent timelines. Large language models (LLMs) may accelerate evidence synthesis by extracting data  from publications. We compared an LLM-assisted data extraction system with manual extraction.

Methods. We conducted a 1:1, open-label, 2-period, randomized crossover trial at the National Center for Global Health and  Medicine, a national reference center for emerging infectious diseases in Japan (2025). Five experienced reviewers extracted  predefined items from mpox-related articles under 2 conditions: (i) LLM-assisted extraction using OpenAI’s o3 model to  generate structured summaries and (ii) manual review of PDF files. The primary outcome was task completion time; secondary  outcomes were extraction accuracy and adverse events. Mixed-effects models included condition as a fixed effect and  participant and paper IDs as random effects. The protocol, source code, and data are available at https://github.com/SRWS-  PSG/emerging_infection_24K13518_open

Results. Five evaluators (4 physicians and 1 pharmacist; 6–10 years postgraduation) completed 20 task-level evaluations (LLM,  n = 9; no LLM, n = 11). Mean completion time was 27.5 minutes with LLM assistance versus 34.5 minutes without. The LLM-  assisted condition was 7.9 minutes faster on average (95% CI −1.5 to 17.3; P = .099). Extraction accuracy was 100% in both  conditions, and no adverse events were reported.

Conclusions. LLM assistance might reduce data extraction time by ∼23% (7.9 minutes per article; 95% CI −1.5 to 17.3 minutes)  with no observed loss of accuracy. Although statistical uncertainty remains, LLM integration may offer practical value for rapid  evidence synthesis during public health emergencies as tools and prompting strategies mature.

Keywords. artificial intelligence; emerging infections; large language model; randomized crossover trial.

Rapid and accurate information, evidence collection, and anal­ ysis are critical for public health decision-making during  emerging infectious disease outbreaks. In emergency situations  such as the COVID-19 and mpox pandemics, there is an urgent  need to provide evidence expeditiously; however, traditional  systematic review methodologies often fail to meet these  time constraints [1]. Rapid evidence synthesis is essential to en­ able policymakers to make the necessary decisions such as

notification, contact tracing, strengthening testing and medical  systems, and securing medical countermeasures within short  timeframes, and the development of tools that can swiftly col­ lect and synthesize data has become imperative [2].

The application of automated technologies, particularly large  language models (LLMs), has demonstrated the potential to ad­ dress efficiency challenges in emergent evidence synthesis.  Automated data extraction that leverages LLM is expected to  enhance both the speed and accuracy of the review process  [3, 4]. Implementing these technologies may enable the rapid  synthesis and delivery of evidence while minimizing human re­ source requirements, potentially facilitating timely information  provision to decision makers.

Received 17 January 2026; accepted 22 June 2026; published online 23 July 2026 Correspondence: Masahiro Ishikane, MD, PhD, Disease Control and Prevention Center,  National Center for Global Health and Medicine, Japan Institute for Health Security, 1-21-1  Toyama, Shinjuku-ku, Tokyo 162-8655, Japan (ishikanemasahiro@gmail.com).

Open Forum Infectious Diseases®

However, empirical data demonstrating the extent to which  these tools reduce the actual burden of evidence synthesis are  lacking. We developed an LLM-based application that extract­ ed structured data from articles in PDF format [5–8]. The ob­ jective of this randomized crossover trial was to evaluate

© The Author(s) 2026. Published by Oxford University Press on behalf of Infectious Diseases  Society of America. This is an Open Access article distributed under the terms of the  Creative Commons Attribution License (https://creativecommons.org/licenses/by/4.0/), which  permits unrestricted reuse, distribution, and reproduction in any medium, provided the original  work is properly cited.  https://doi.org/10.1093/ofid/ofag401

LLM data extraction in randomized trial • OFID • 1

Downloaded from academic.oup.com/ofid/article/13/7/ofag401/8736362 by guest on 08 September 2026


> **Figure 1. Enrollment Process. This study was a 1:1 open-label, 2-period, 2-group, randomized crossover trial with a superiority framework designed to evaluate the efficacy**

> of a LLM-based data extraction system.

whether the use of an LLM-based system improves the time effi­ ciency of extracting data from articles on emerging infectious dis­ eases compared with manual extraction without such a system.

CONSORT guidelines [9]. Details are presented in Figure 1 and Supplementary Table 1.

Study Populations This study was conducted at the National Center for Global  Health and Medicine (NCGM), a national reference center  for emerging infectious diseases in Japan. We recruited re­ searchers and healthcare professionals whose native language  is Japanese from the center through internal emails, research  meeting announcements, and personal invitations. Eligible  participants had experience in evidence reviews and special­ ization in infectious diseases, possessed basic computer skills,  and provided informed consent. We excluded individuals  with unstable internet connections. The sample size was cal­ culated to detect an expected 10-minute difference in task  completion time with 80% power and a 5% significance level,  requiring 20 participant-paper evaluations. We recruited 5  participants, each assigned to evaluate 4 papers in August  2025.


## METHODS

Patient Consent Statement The study was registered in the UMIN Clinical Trials Registry  (UMIN000058346). The research protocol was exempted from  review by the Institutional Review Board for Clinical Research  of the Japan Institute for Health Security because the study  evaluated professional efficiency and involved no medical in­ terventions or patient health outcomes.

Trial Design This study was a 1:1 open-label, 2-period, 2-group, random­ ized crossover trial with a superiority framework designed  to evaluate the efficacy of a LLM-based data extraction  system. This study was conducted in accordance with the


## 2 • OFID • Ishikane et al

articles and is not used for making assessments or proposed ac­ tion. In the non-LLM group, the use of translation software was  permitted, but the use of artificial intelligence (AI) tools was  not. The system automatically recorded the time from the start  of data entry to submission. Each participant repeated this pro­ cess for all 4 assigned papers, according to their randomized  sequences.

Intervention and Control The intervention group used an LLM-based system to automat­ ically extract and summarize structured data from research pa­ per PDFs using OpenAI’s o3 model (OpenAI, San Francisco,  CA; accessed 14 October 2025) via OpenAI Application  Programming Interface (API). The participants reviewed the  system-generated summary to complete the data entry web  form. The control group did not use the LLM system; instead,  they read the paper PDFs directly and manually extracted the  information to complete the same web form.

Outcomes The prespecified primary outcome was the task completion  time, measured in minutes from the start of data entry to  form submission. Task completion time was selected as the  primary outcome because the fundamental challenge driving  this study is the urgent need for rapid evidence synthesis dur­ ing emerging infectious disease outbreaks, where time effi­ ciency is the primary determinant of practical utility. This  approach is consistent with recent LLM-assisted evidence  synthesis studies that have similarly prioritized time efficien­ cy as a key evaluative dimension [3, 10]. Prespecified second­ ary outcomes were data extraction accuracy and harm. Data  extraction accuracy was defined as the proportion of correct  answers as assessed by an expert reviewer. A single infectious  disease specialist (the first author) evaluated the content of  the article summaries. The evaluation focused on verifying  the accuracy of the intended meaning of the articles, rather  than the verbatim translation. The evaluator was unaware  of group allocation. Also, we developed the AI-assisted  English translations for detailed inspection of the original re­ sponses in the Supplementary Table 3. Harms were defined as  nonmedical adverse events, such as excessive psychological  stress or significant task difficulty, and they were monitored  through voluntary participant reporting.

Randomization The study statistician randomized the participants into 2  sequences using a computer-generated random number table.  We used block randomization with a block size of 2 to ensure a  1:1 allocation ratio. Allocation was concealed because the statisti­ cian had no contact with the participants, and the web application  assigned the intervention immediately before the task, preventing  participants or enrolling staff from predicting the sequence.

Downloaded from academic.oup.com/ofid/article/13/7/ofag401/8736362 by guest on 08 September 2026

Procedure After obtaining electronic informed consent and confirming el­ igibility, each participant was assigned a paper. The web appli­ cation then assigned the participants to either the intervention  or control condition for that task. The intervention group re­ ceived the LLM-generated summary, whereas the control group  received only the paper PDF about mpox-related articles [5–8].  For the intervention materials, PDF text was extracted with  pdfminer.six and submitted to the OpenAI o3 model via the  API. The first 10 000 characters of each PDF text were used as  input. The system prompt instructed the model to act as an ex­ pert in extracting structured data from research papers, and the  user prompt asked the model to extract structured information  from the provided paper text. Responses were constrained using  a strict JSON schema requiring filename, theme, category, time,  place, person, and a 3–5 item Japanese plain-language bullet-  point summary. No task-specific training, fine-tuning, or few-  shot examples were used. The temperature parameter was not  set because it was not supported by the o3 model in our imple­ mentation. Each paper was processed once before the trial, and  the resulting summaries were stored as fixed intervention mate­ rials. We have completed TRIPOD-LLM checklist as reporting  checklists (Supplementary Table 2).

Statistical Analysis We analyzed the primary outcome using a linear mixed-effects  model, with the intervention as a fixed effect and the participant  and paper IDs as random effects. We analyzed the accuracy  of data extraction using a generalized linear mixed model.  Secondary outcomes were summarized descriptively. All analyses  followed the intention-to-treat principle and included all ran­ domized participants. Statistical analyses were performed using  Python (version 3.11.0). The source code is available at https://  github.com/SRWS-PSG/emerging_infection_24K13518_open

Limiting the scope to peer-reviewed English-language arti­ cles, the first author selected key literature that the 5 reviewers  were not expected to have read in detail previously. Both  groups completed a data entry form with fields for paper sum­ maries, assessments, and proposed clinical actions. The data ex­ traction process consists of 5 steps: downloading the article,  summarizing the paper (with optional LLM assistance), assess­ ing the article, proposing a clinical action, and submitting com­ pleted information. The LLM is used only for summarizing


## RESULTS

Background Information on Evaluators and Articles The mean number of postgraduate years among the 5 evalua­ tors (4 medical doctors and 1 pharmacist) was 7.8 years (range:  6–10 years). Six papers (3 epidemiology, 2 laboratory, and 1  vaccine study) contained a mean of 3365 words per paper ex­ cluding references (range: 2155–5588 words).

LLM data extraction in randomized trial • OFID • 3

in extraction time. However, this difference did not reach statisti­ cal significance (95% CI: −1.5 to 17.3 minutes; P = .099). Notably,  the data extraction accuracy was perfect in both conditions  (100%), and no adverse events or participant burden was reported  throughout the study, suggesting that LLM implementation is safe  and maintains data quality standards.

Automation, including LLM, is being increasingly explored  to reduce the time and effort involved in evidence synthesis;  however, its adoption and reporting practices remain limited.  Based on a study conducted between 2017 and 2024 [11],  only ∼5% of the studies explicitly reported using ML, with  most applications limited to screening tasks among the 2271 ar­ ticles. In this study, we evaluated the effectiveness of summari­ zation using an LLM-based system. AI-assisted tools show  promise in improving workflow efficiency in clinical documen­ tation. One study evaluated the impact of an AI scribe on clini­ cian documentation efficiency and observed modest but  significant improvements [12]. In pre–post comparisons  among 125 users, median electronic health records time per en­ counter decreased by 2.0 minutes, note-writing time by  0.5 minutes, and time to close notes by 7.1 hours. In the adjust­ ed between-group analyses, AI scribe users had 8.5% less elec­ tronic health record time (2.4 minutes per encounter) and  15.9% less note-writing time (1.8 minutes) than nonusers.  These results indicate that AI scribes can meaningfully reduce  the documentation burden, even though the effects on  after-hours work and visit volumes are minimal. In our study,  although LLM support did not demonstrate a statistically  significant difference, the average task completion time was re­ duced by 7.9 minutes (27.5 minutes vs 34.5 minutes).

Downloaded from academic.oup.com/ofid/article/13/7/ofag401/8736362 by guest on 08 September 2026


> **Figure 2. Task completion time using LLM versus without LLM. Figure 2 shows**

> the task completion time by condition. Boxplots summarize task-level completion 
times for the LLM and no LLM conditions (n = 9 and n = 11 task evaluations, re­
spectively). Boxes show the interquartile range (IQR), horizontal lines denote medi­
ans, and whiskers indicate the range of observed values. Green diamonds mark 
means. Gray points represent individual task observations with small horizontal jit­
ter for visibility. The y-axis is in minutes.

Primary Outcomes Across 20 task-level evaluations (LLM: n = 9; no LLM: n = 11),  the mean time to complete the data extraction task was  27.5 minutes with LLM assistance and 34.5 minutes without  LLM assistance. In a linear mixed-effects model with partici­ pant and paper as random effects, the LLM condition was, on  an average, 7.9 minutes faster than the no LLM condition  (95% CI for the reduction, −1.5 to 17.3; P = .099). Although  the point estimate favored LLM use, the confidence interval in­ cluded zero (Figure 2).

Although the application of LLMs to automate systematic re­ view processes has gained considerable attention, research on  LLM-assisted data extraction, specifically in living systematic  reviews, remains limited [13]. Collaborative LLM approaches  can achieve high accuracy (94%) in extracting data from clinical  trial publications [13]; however, these investigations have pre­ dominantly focused on oncology trials rather than infectious  diseases. Notably, to the best of our knowledge, no prior ran­ domized controlled trial has evaluated the time efficiency of  LLM-assisted data extraction in the context of emerging infec­ tious diseases where rapid evidence synthesis is critical [10].  Our study addresses this gap by directly measuring the time  savings achieved through LLM implementation and assessing  the data accuracy in real-time extraction scenarios relevant to  public health emergencies.

Secondary Outcomes Supplementary Table 3 provides the raw extraction data and  their AI-assisted English translations for detailed inspection  of the original responses. Based on expert review of the intend­ ed meaning of each extracted item, accuracy was 100% in both  conditions (LLM 9/9; no LLM 11/11). Comparative modeling  was not estimable because there was no between-group vari­ ability. No harm or adverse events, as prespecified (eg, excessive  psychological stress or significant task difficulty), were reported  by participants in either condition during the study.


## DISCUSSION

The findings of this study have important implications  for future evidence synthesis of emerging infectious diseases.  The 7.9 minutes reduction in task completion time suggests  meaningful practical benefits. Importantly, the developed  LLM-assisted system is fully accessible, the source code is open­ ly available, and implementation requires only a Google ac­ count and API access, making it potentially deployable by

This randomized crossover trial evaluated the time efficiency  and accuracy of LLM-assisted data extraction from literature  on emerging infectious diseases compared with manual extrac­ tion. Our findings demonstrated that LLM assistance reduced  the mean task completion time by 7.9 minutes (27.5 minutes  vs 34.5 minutes), representing an approximately 23% reduction


## 4 • OFID • Ishikane et al

observed time reduction. The study population was limited to  individuals with expertise in literature review methodologies  and data extraction, potentially limiting the generalizability of  our findings to less experienced users or those without  domain-specific knowledge of infectious diseases. Second, our  LLM-assisted system requires the manual downloading of  PDF files, indicating that full automation of the evidence syn­ thesis workflow has not yet been achieved. This intermediate  step requires human intervention and may limit the scalability  of this approach in high-throughput scenarios. Third, the cur­ rent study focused exclusively on data extraction and did not  evaluate the performance of the LLM system in upstream pro­ cesses such as literature search, screening, or article selection.  These critical components of systematic reviews remain outside  the scope of our validation, and their automation requires fur­ ther investigation. Fourth, the study was powered to detect a  10-minute difference; however, the observed difference was  7.9 minutes with greater within-group variability than as­ sumed, suggesting the study may have been underpowered to  detect an effect of this magnitude. The result should therefore  be interpreted with caution. Finally, we did not formally assess  output stability under repeated prompting. However, potential  run-to-run variability did not affect the trial exposure because  all LLM summaries were generated before participant sessions  and stored as fixed materials. Future studies should evaluate  repeated-prompt stability and report model-version-specific  reproducibility.

research teams worldwide. However, practical adoption should  be considered in light of technical barriers because successful  implementation requires proficiency in programming, API in­ tegration, and prompt engineering. Despite these skill require­ ments, the 100% accuracy maintained across both conditions  and the absence of adverse events suggest that, when properly  implemented, LLM-assisted extraction can serve as a safe and  reliable tool to accelerate evidence synthesis without compro­ mising data quality. This is particularly valuable in pandemic  settings, where even modest time savings can expedite critical  public health decision-making.

Several directions for future research have emerged from this  study. First, the applicability of this approach to fields other  than emerging infectious diseases requires further investiga­ tion. The workflow we developed may be adapted for rapid ev­ idence synthesis in other rapidly evolving medical domains,  such as oncology clinical trials or novel therapeutic interven­ tions. Second, our study was conducted with participants  who were familiar with the literature review methodologies  and possessed baseline expertise in data extraction. Since the  evaluators for this study were recruited from the NCGM, na­ tional center for emerging infectious diseases in Japan, it is  possible that relatively experienced evaluators were selected  in this study. Such experienced evaluators are likely already  skilled at quickly identifying and extracting key information  from articles, which may have diminished the relative advan­ tage offered by the prestructured summaries generated by  LLM. On the other hand, if less experienced evaluators had par­ ticipated in this study, they might have benefited more from the  support of the LLM, as reported in previous literature [10, 14],  which could have led to an underestimation of the LLM’s po­ tential time-saving benefit. Future studies should evaluate the  performance of this LLM system among users who lack  domain-specific knowledge of infectious diseases and experi­ ence with systematic literature extraction. Such research would  clarify whether LLM assistance can democratize evidence syn­ thesis by enabling less experienced researchers or nonspecial­ ists to conduct high-quality data extraction or whether  technical and domain expertise remain prerequisites for effec­ tive implementation. By enabling system construction with  fewer experts, experts can focus only on tasks they can  perform, such as clinical management. Moreover, relevant  examples outside medicine include LLM-supported data ex­ traction in software engineering systematic mapping studies  [15], hypothesis-evidence classification in the social sciences  [16], and structured extraction from educational and  materials-science literature [17]. These studies suggest that  LLMs may support semi-automated evidence synthesis work­ flows, although human verification remains essential.

Downloaded from academic.oup.com/ofid/article/13/7/ofag401/8736362 by guest on 08 September 2026

In conclusion, this randomized controlled trial demonstrat­ ed that infectious disease specialists sing an LLM-assisted data  extraction system achieved a modest reduction in task comple­ tion time while maintaining perfect data accuracy. Although  statistical uncertainty remains, the combination of time effi­ ciency and preserved data quality suggests that LLM-assisted  systems may offer practical value to infectious disease special­ ists for conducting rapid evidence synthesis during public  health emergencies. As technology continues to evolve and re­ searchers gain experience with prompt engineering and system  optimization, LLM-assisted data extraction may become an  increasingly valuable component of the infectious disease evi­ dence synthesis toolkit, particularly in time-sensitive scenarios  where even modest efficiency gains can meaningfully impact  public health responses.

Supplementary Data

Supplementary materials are available at Open Forum Infectious Diseases online. Consisting of data provided by the authors to benefit the reader, the  posted materials are not copyedited and are the sole responsibility of the  authors, so questions or comments should be addressed to the correspond­ ing author.

This study had several limitations. First, our sample size was  relatively small (n = 20 task-level evaluations), which may have  contributed to the lack of statistical significance, despite the

Notes

Acknowledgments. We thank the clinical staff at our hospital for their  dedication to patient care and Dr Yusuke Hidaka, Dr Nayuta Seto, Dr

LLM data extraction in randomized trial • OFID • 5

Yusuke Shirai, Dr Kazuki Yokoi, and Mr Ryuji Koizumi for their participa­ tion in this trial as evaluators for the articles.

7. Dalton AF, Diallo AO, Chard AN, et al. Estimated effectiveness of JYNNEOS vac­ cine in preventing mpox: a multijurisdictional case-control study—United States,  August 19, 2022-march 31, 2023. MMWR Morb Mortal Wkly Rep 2023; 72:  553–8. 8. Beeson A, Styczynski A, Hutson CL, et al. Mpox respiratory transmission: the  state of the evidence. Lancet Microbe 2023; 4:e277–83. 9. Equator network. CONSORT reporting guideline for writing clinical trial re­ search articles. Available at: https://resources.equator-network.org/reporting-  guidelines/consort/. Accessed 31 December 2025. 10. Gartlehner G, Kugley S, Crotty K, et al. Artificial intelligence-assisted data extrac­ tion with a large language model: a study within reviews. Ann Intern Med 2025;  178:1763–71. 11. Scotti KL, Young S, Gainey MA, Lan H. Artificial intelligence and automation in  evidence synthesis: an investigation of methods employed in Cochrane, Campbell  Collaboration, and Environmental Evidence Reviews. Cochrane Evid Synth  Methods 2025; 3:e70046. 12. Pearlman K, Wan W, Shah S, Laiteerapong N. Use of an AI scribe and electronic  health record efficiency. JAMA Netw Open 2025; 8:e2537000. 13. Gartlehner G, Kahwati L, Hilscher R, et al. Data extraction for evidence synthesis  using a large language model: a proof-of-concept study. Res Synth Methods 2024;  15:576–89. 14. Khan MA, Ayub U, Naqvi SAA, et al. Collaborative large language models for au­ tomated data extraction in living systematic reviews. J Am Med Inform Assoc  2025; 32:638–47. 15. Felizardo KR, Lima MS, Deizepe A, et al. Data extraction for systematic mapping  study using a large language model: a proof-of-concept study in software engi­ neering. ESEM; 2024. 16. Koneru S, Wu J, Rajtmajer S. Can large language models discern evidence for sci­ entific hypotheses? Case studies in the social sciences. In: Proceedings of the 2024  Joint International Conference on Computational Linguistics, Language Resources  and Evaluation (LREC-COLING 2024), Torino, Italia. ELRA and ICCL;  2024:2787–97. 17. Yoo J, Mahowald C, Li M, et al. Extracting research instruments from educational  literature using LLMs. arXiv 2025.

Data Availability Statements. The data underlying this article will be  shared on reasonable request to the corresponding author.

Financial support. This work was supported by JSPS KAKENHI (grant  number JP24K13518, JP25K13585 and JP25K13447). The funders played  no role in the study design; collection, analysis, and interpretation of  data; writing of the report; or decision to submit the article for publication.

Potential conflicts of interest. The authors have no conflicts of interest to  declare.

Authorship Statement. M. I., Y. K., and Y. T. designed the study  and wrote the manuscript. Y. K. and Y. T. conducted statistical  analyses. Y. Mo., Y. Ma., and N. O. reviewed the study design and manu­ script. All members contributed to the management and administration  of the trials. All the authors met the ICMJE authorship criteria.

Downloaded from academic.oup.com/ofid/article/13/7/ofag401/8736362 by guest on 08 September 2026


## References

1. Peters MDJ, Marnie C, Tricco AC, et al. Updated methodological guidance for the  conduct of scoping reviews. JBI Evid Synth 2020; 18:2119–26. 2. Ziam S, Lanoue S, McSween-Cadieux E, et al. A scoping review of theories, models  and frameworks used or proposed to evaluate knowledge mobilization strategies.  Health Res Policy Syst 2024; 22:8. 3. Kataoka Y, Takayama T, Yoshimura K, et al. Automating the data extraction process  for systematic reviews using GPT-4o and o3. Res Synth Methods 2026; 17:42–62. 4. Tercero-Hidalgo JR, Khan KS, Bueno-Cavanillas A, et al. Artificial intelligence in  COVID-19 evidence syntheses was underutilized, but impactful: a methodologi­ cal study. J Clin Epidemiol 2022; 148:124–34. 5. Smith TG, Gigante CM, Wynn NT, et al. Tecovirimat resistance in mpox patients,  United States, 2022-2023. Emerg Infect Dis 2023; 29:2426–32. 6. Gessain A, Nakoune E, Yazdanpanah Y. Monkeypox. N Engl J Med 2022; 387:  1783–93.


## 6 • OFID • Ishikane et al
