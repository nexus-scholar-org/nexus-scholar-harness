---
workspace_id: "SCI-000136"
doi: null
title: "Investigating Novice Researchers' Perceptions of Research Privacy Within LLM-Assisted Workflows"
year: 2026
extraction_engine: "pymupdf"
---
# 2026 Zhang Investigating Novice Researchers' Percep

Investigating Novice Researchers’ Perceptions of Research

Privacy Within LLM-Assisted Workflows

Shuning Zhang zsn23@mails.tsinghua.edu.cn

Changxi Wen wcx24@mails.tsinghua.edu.cn

Eve He eve.he@wisc.edu University of Wisconsin-Madison

Tsinghua University

Tsinghua University

Beijing, China

Beijing, China

Madison, Wisconsin, U.S.

Xin Yi yixin@tsinghua.edu.cn

Ying Ma ying.ma1@student.unimelb.edu.au

Robert Xiao brx@cs.ubc.ca University of British Columbia Vancouver, British Columbia, Canada

Tsinghua University

The University of Melbourne

Beijing, China

Melbourne, Australia

arXiv:2606.03248v1  [cs.HC]  2 Jun 2026

Hewu Li lihewu@cernet.edu.cn

Tsinghua University

Beijing, China


## Abstract

ACM Reference Format: Shuning Zhang, Changxi Wen, Eve He, Ying Ma, Robert Xiao, Xin Yi, and Hewu Li. 2018. Investigating Novice Researchers’ Perceptions of Re- search Privacy Within LLM-Assisted Workflows. In Proceedings of Make sure to enter the correct conference title from your rights confirmation emai (Conference acronym ’XX). ACM, New York, NY, USA, 19 pages. https: //doi.org/XXXXXXX.XXXXXXX

Large Language Model (LLMs)-assisted scholarly workflows intro- duce critical privacy and intellectual property risks. As a uniquely vulnerable cohort driven by publication pressure and a lack of in- stitutional support, novice researchers rely heavily on public LLMs, compelling them to navigate high-stakes privacy-publication trade- offs. To investigate these concerns, we conducted semi-structured interviews with 44 researchers across diverse disciplines. Our find- ings reveal that the fear of idea leakage paradoxically accelerates, rather than deters, reliance on LLMs, as researchers utilize them to expedite publication. They also held misconceptions that their ideas lacked the unique value to attract targeted attacks, and that their inputs would be safely diluted within massive datasets, pre- venting reconstruction. From interviews, we identified five types of mitigations including input fragmentation and adversarial probing, though we found that participants largely perceived these mea- sures as ineffective. We outline implications including implement- ing institution-level sandboxed isolation, scenario-based privacy pedagogy, and verifiable data-deletion audits for transparency.

1 Introduction

The rapid integration of Large Language Model (LLM)-based tech- niques into academic workflows has substantially improved the effi- ciency and scope of scholarly activities [27, 92]. However, this trans- formation has also introduced critical challenges. Specifically, the processing of unpublished ideas and proprietary datasets through third-party LLM systems can expose research materials not only to model providers but also to tool-mediated or third-party app ecosystems, where data collection and disclosure practices may be difficult for users to inspect [97]. This risk is widely discussed across the global scientific community [63].

Previous research efforts have examined privacy concerns in human-LLM interactions for general end-users [61, 111, 117], and built tools to help redact and sanitize content to preserve pri- vacy [62, 114]. Researchers have also examined privacy violations and potential harms within educational contexts [34, 45]. However, these efforts often center around general personal privacy and fail to address research privacy, a distinct domain involving specialized research ideas and contextual proprietary data. Furthermore, the human factors contributing to these security and privacy (S&P) risks remain largely unexamined. We specifically focus on novice researchers, defined as individuals with limited publication experi- ence [78], typically graduate students [24]. They represent a critical demographic for three reasons: (1) as the primary authors respon- sible for drafting manuscripts and managing data, they handle the most sensitive intellectual property during the research process, (2) they are often active, “early-adopters” of AI tools and may more readily use AI tools to create new workflows, and (3) since they are still learning formal research norms, they may use these tools

CCS Concepts

• Security and privacy →Usability in security and privacy.

Keywords

Research privacy, Research integrity, Large Language Models, Novice researcher

Permission to make digital or hard copies of all or part of this work for personal or classroom use is granted without fee provided that copies are not made or distributed for profit or commercial advantage and that copies bear this notice and the full citation on the first page. Copyrights for components of this work owned by others than ACM must be honored. Abstracting with credit is permitted. To copy otherwise, or republish, to post on servers or to redistribute to lists, requires prior specific permission and/or a fee. Request permissions from permissions@acm.org. Conference acronym ’XX, Woodstock, NY © 2018 ACM. ACM ISBN 978-1-4503-XXXX-X/18/06 https://doi.org/XXXXXXX.XXXXXXX

Conference acronym ’XX, June 03–05, 2018, Woodstock, NY Trovato and Tobin, et al.

2 Background and Related Work 2.1 Research Lifecycle and Risks

without fully recognizing the long-term privacy implications for their scholarly work. To address their challenges, we answer the following research questions (RQs):

Standard scholarly workflows, encompassing ideation, literature re- view, experimental design, execution, data analysis, and manuscript preparation [20], face diverse privacy risks when integrated with LLMs. These stage-specific vulnerabilities, summarized in Table 1, highlight a critical tension between these tools’ utility and research privacy. Recent literature further quantifies these challenges, identi- fying issues such as confidential data exposure, intellectual property leakage, and insufficient transparency regarding data flows [80]. Beyond technical leaks, researchers face ethical concerns such as bias, censorship, and fabrication, all of which require mindful en- gagement with generative tools [11].

• RQ1: What are novice researchers’ mental models and privacy perceptions of LLM-assisted research workflows?

• RQ2: What privacy protection practices do novice researchers adopt in LLM-assisted research workflows, and how do they per- ceive their effectiveness?

• RQ3: What challenges hinder novice researchers from effec- tively protecting research privacy within LLM-assisted research workflows?

To answer these RQs, we conducted semi-structured interviews with 44 novice researchers across a range of disciplines.

For RQ1, we identified that researchers valued the privacy of unpublished ideas and data. Specifically, they noted that ideas are more vague and can leak indirectly. Moreover, they hold misun- derstandings around research privacy risks. They worried about the theft of unpublished ideas by service providers and other peers, causing professional consequences that hindered progress. Simul- taneously, they underestimated the risks of model memorization and training, generally assuming that their data would be diluted within LLM training sets, or assuming that model refusals to output their sensitive data would protect their privacy.


> **Table 1: Categorization of privacy risks across different re-**

> search stages.

Research stage Privacy risks

Leaked confidential ideas [11] Systemic algorithmic bias [11] Restricted academic freedom [11]

Ideation

Copyright infringement [11] Confidential document exposure [36]

For RQ2, we found that novice researchers, operating without in- stitutional sandboxes, employed ad-hoc mitigation strategies. They fragmented proprietary ideas or frameworks into different sessions or models to prevent data leakage, and used adversarial probing techniques such as asking whether LLMs memorize their data to empirically test the boundaries of profiling. However, they per- ceived these practices as mostly ineffective, and had to sacrifice effective assistance for privacy.

Literature review

Research direction inference [48]

Extraction inaccuracy [11]

Research protocol exposure [11]

Experimental design

Biased instrument design [11] Inaccurate informed consent [11]

Participant privacy breach [11] Regulatory non-compliance [11]

Data collection

Excessive data collection [81] Demographic quality disparity [11]

For RQ3, we identified multi-faceted constraints. First, their anx- iety about publication outweighs privacy needs, and the fear of idea leakage paradoxically leads them to use LLMs more. Second, infrastructure-wise, they lack private institutional sandboxes, hav- ing to rely on public LLMs with weaker privacy guarantees. Third, they lacked techniques for privacy management, such as data san- itation tools or formal AI privacy training. Finally, they lacked accountability, with little to no formal regulations on privacy, and limited ability to verify or audit the privacy protections offered by service providers, particularly for abstract ideas whose leakage is hard to track. These challenges call for actions such as institu- tional automated screening and separated tools, transparent risk visualization, and interactive privacy training.

Raw data exposure [75] Individual re-identification risk [65]

Data analysis

Data integrity compromise [11] Model reverse engineering [79]

Unpublished result leakage [58] Participant privacy violations [75] Intellectual property ambiguity [11]

Manuscript preparation

Author identity leakage [9] Cybersecurity vulnerabilities [75]

These vulnerabilities are particularly acute in interactive chat- bot deployments. Such environments amplify threats including the generation of fabricated content [49], operational vulnerabilities such as prompt injection [22], and privacy risks involving intellec- tual property [15]. Besides, while AI assistance dramatically boosts individual outputs by enabling researchers to publish 3.02 times more papers and receive 4.84 times more citations [29], this reliance exacerbates S&P vulnerabilities. Therefore, researchers widely dis- cuss S&P and safety risks of scientific tools despite acknowledging their transformative potentials [91, 92, 94].

Collectively, this paper’s contributions are threefold: • We characterized novice researchers’ privacy perceptions, such as their emphasis on unpublished ideas and assumptions of privacy risks.

• We categorize five classes of privacy mitigation strategies such as data fragmentation and adversarial probing, and find that researchers largely perceive these mitigations as ineffective.

• We provide implications such as institutional automated screen- ing and separated tools, transparent risk visualization, and interac- tive privacy training.

To better support this human-AI collaboration, methodological innovations rapidly evolved from single-phase, multi-agent ideation systems [6] to adaptive writing assistants [66] and end-to-end au- tonomous research agents (e.g., InternAgent) [85]. This progres- sion reflects an escalating taxonomy of LLM autonomy [105, 112],

Investigating Novice Researchers’ Perceptions of Research Privacy Within LLM-Assisted Workflows Conference acronym ’XX, June 03–05, 2018, Woodstock, NY

prompting the academic community to establish strict ethical frame- works that mandate rigorous human vetting and transparent ac- knowledgment [68].

Conversely, despite operating under strict regulatory frame- works, software developers frequently lack formal Privacy by De- sign (PbD) education and actionable guidelines [47, 76]. Relying heavily on informal learning rather than standardized methodolo- gies like anonymization [70], developers often treat privacy as a reactive, policy-driven compliance task rather than proactive engi- neering [46, 51]. Although usable security principles [1], technol- ogy acceptance models [77], and internal “privacy champions” [83] can promote structural privacy adoption, S&P awareness and prac- tices are still insufficient. Crucially, existing literature largely lacks research-specific privacy contexts. Established threat models for users and developers fail to capture the unique vulnerabilities of novice researchers, who protect unpublished conceptual frame- works, interpretive logic, and sensitive human-subject data against LLM memorization and leakage.

2.2 Research Privacy and Integrity

While educational privacy primarily focuses on safeguarding stu- dent data and mitigating surveillance risks [45], research privacy involves protecting unpublished ideas, proprietary methodologies, and data integrity. Despite these distinct objectives, vulnerabilities observed in educational contexts can serve as a base for under- standing the threats faced by researchers. Institutional hurdles, such as unprepared infrastructure and lack of standardized proto- cols, remain the primary barriers to data protection [25]. Resource constraints and limited internal expertise frequently force institu- tions to bypass rigorous security assessments [14], relying instead on trust-based vendor self-certifications [42]. This lack of oversight exacerbates accountability challenges, as educational institutions remain liable for vendor data mishandling, but have limited re- sources for contractual monitoring [71]. Even with established Data Protection Agreements, inconsistent enforcement and insecure configurations persist [18], ultimately driving educators to adopt unsanctioned tools to meet professional demands despite acknowl- edging the associated privacy risks [41].

2.4 Privacy-preserving LLM-powered Chatbots

Recent studies identify a critical privacy-utility tension in LLM- powered chatbots. While users recognize data sensitivity, they often neglect proactive safeguards, exposing themselves to vulnerabilities such as insecure code generation [67, 87]. To mitigate these risks, contemporary research and product deployments develop various countermeasures. These solutions broadly follow two lines: archi- tectural frameworks, such as localized and cloud-edge computing, and algorithmic safeguards, including cryptographic protocols and collaborative learning.

Misaligned risk perceptions further complicate the educational privacy landscape. Parents often delegate privacy responsibilities to schools as they trust these institutions, creating a disconnect between perceived and actual data protection [119]. Conversely, students report heightened privacy concerns regarding surveil- lance, like online proctoring, which undermine trust and provoke defensive behaviors [8]. Furthermore, research indicates that stu- dents frequently overlook implicit data disclosure risks of assistive technologies, even when they remain highly cognizant of physical privacy threats [59].

Architectural strategies reduce the attack surface by retaining sensitive data within local trust boundaries. Localized computing and on-device LLM inference minimize remote server transmis- sion [28, 38, 100], while specialized tools reinforce this defense by enforcing transparent, on-device data minimization [120]. For computationally intensive tasks, cloud-edge collaborative systems dynamically route non-sensitive queries to the cloud while pro- cessing sensitive data locally [104]. Furthermore, hardware-backed Trusted Execution Environments (TEEs), such as Apple’s Private Cloud Compute, extends these strict on-device privacy guarantees to cloud-assisted workflows [5].

Finally, evaluating educational technologies increasingly relies on nuanced risk assessments. As traditional privacy policies often obscure practical harms, studies used longitudinal user review anal- yses [102] and structured frameworks like the Analytic Hierarchy Process to prioritize vulnerabilities such as algorithmic opacity and technical reliability [72]. While these methods evaluate general ed- ucational and institutional risks from GenAI systems, they overlook facets unique to researchers, such as threats to unpublished ideas and data.

Researchers also proposed algorithmic protections. Crypto- graphic approaches, such as homomorphic encryption, secure data during processing [116]. In collaborative settings, federated learn- ing enables distributed model training across edge devices [118], supported by secure aggregation protocols that merge updates without exposing raw data [101]. Differential Privacy (DP) remains central to these frameworks, injecting calibrated noise into model updates and commercial workflows to protect individual records while maintaining model utility [53, 55, 99]. Despite these advance- ments, deploying GenAI in research contexts introduces unique socio-technical complexities [69]. Literature lacks an understand- ing of how novice researchers navigate privacy risks, warranting investigation into their privacy needs and practices.

2.3 Privacy Perceptions and Thoughts

We summarize existing work on S&P perceptions towards LLM- assisted tools from end users and developers. We compare those with novice researchers, which have a hybrid role: they navigate the privacy landscape as end-users while managing data such as interview scripts within institutions.

For end users, privacy concerns span the entire data lifecycle. They navigate a privacy-utility paradox with LLM chatbots [110, 113, 117], actively seeking regulatory compliance and granular data control to establish trust dynamics across diverse platform ecosys- tems [3, 54]. Furthermore, users increasingly fear unauthorized extraction of their proprietary knowledge and configurations from AI agent creators [57, 107, 108].

3 Methodology 3.1 Participants

We recruited 44 participants (17 males, 27 females) with a mean age of 26.9 (SD=3.5, ranging from 22 to 38) through a mixture of personal contact networks (1 participant) and posting recruitment

Conference acronym ’XX, June 03–05, 2018, Woodstock, NY Trovato and Tobin, et al.

messages through LinkedIn (2 participants), RedBook (23 partici- pants) and WeChat Moment (6 participants), and dedicated WeChat groups of different campuses (11 participants). Our participants included 3 assistant professors, 1 corporate researcher, 28 PhD candidates and 12 Master’s students. Although the non-student participants had begun full-time research roles, they were still in the early stage of developing independent research trajectories, placing them within the novice researcher stage [4, 96] (commonly referred to as “recent graduate/postdoc” or “early-career” stages). Participants represented a wide range of academic disciplines: 11 were from computer science, engineering, or related technical fields (e.g., Mechanical Engineering), 28 were from social sciences and humanities (e.g., Linguistics, Education), and 5 were from natural or life sciences. All participants reported having prior experience with LLM-based chatbots (e.g., ChatGPT, Claude, Gemini) for research- related tasks such as ideation and literature review. The interviews were approved by our university’s Institutional Review Board (IRB), and participants were compensated 100 CNY each according to the local wage standard. Participants’ demographics are shown in Appendix Table 4.

verified for accuracy by one primary author. Following that, four authors independently reviewed an initial subset of four randomly selected transcripts to generate initial codes. They then met to compare their codes, discuss discrepancies, and establish a unified codebook. After reaching consensus, the four authors applied the codebook to the remaining transcripts, iteratively updating the codebook, with each author coding 10 each. During this process, they intermittently discussed to resolve discrepancies. Finally, the authors collaboratively synthesized the codes into overarching themes and sub-themes. The final codebook is shown in Appendix C. Given the inductive and exploratory nature of our analysis, we chose not to calculate or report inter-rater reliability (as suggested by prior guidelines [60]). We calculated code frequency post-coding. Below, participants are denoted using P1–P44. The original Chinese quotes were manually translated by one primary author fluent in both English and Chinese, and then checked by the other three primary authors, who were fluent in both English and Chinese for correctness.

4 RQ1: Privacy Perceptions and Mental Models in LLM-Assisted Research

3.2 Interview Design and Procedure

Overall, we found participants primarily integrate AI into their workflows to support text and image-based manuscript preparation (5/44 participants, e.g., P28), conceptual ideation (21/44 participants, e.g., P30-31), and technical execution, such as data analysis and cod- ing (25/44 participants, e.g., P39-42). Additionally, they leveraged AI for information retrieval, including literature synthesis (19/44 participants, e.g., P12-13) and addressing specific queries (6/44 par- ticipants, e.g., P23-24), as well as for evaluative tasks like generating peer-review comments (3/44 participants, e.g., P26).

We designed semi-structured interviews to explore researchers’ pri- vacy concerns and mitigation strategies when using LLM-assisted research tools. The interview guide consisted of five sequential parts. (1) Background and tool usage: after introducing the inter- view, ensuring confidentiality, and obtaining consent, we asked participants about their experiences with LLM-assisted research tools (e.g., generative AI, cloud platforms, and code repositories). We gathered details on their usage history, primary use cases and examples. (2) Privacy perceptions and concerns: we explored par- ticipants’ overall concerns when sharing research data with those tools. We asked them to define “research privacy”, identify what information they consider sensitive, and explain how they devel- oped these privacy concepts. They also discussed their experiences sharing research content with AI tools, and their comparative views on platforms provided by different countries. (3) Specific experience exploration: We guided participants to share experiences related to account linkage, unwanted identification, concerns about being observed, fears of research content leakage, from prior work in Sec 2.1. (4) Coping strategies: We asked participants to describe behaviors and strategies they adopt to mitigate these privacy risks, explicitly noting how they balance privacy concerns with research needs. (5) Finally, we asked participants for suggestions on how these tools could improve privacy protections. Interview scripts are shown in Appendix B.

4.1 Understanding of LLM Data Handling

Opacity and complexity. 9/44 participants viewed LLMs as opaque “black boxes”, citing a lack of transparency in internal data pro-

cessing. This complexity makes the system’s logic inaccessible to users. P28 expressed concern over this opacity, noting that “I do not understand the internal mechanics of this black box, yet its learning capacity appears remarkably potent.” Similarly, P8 argued that, “it is impossible to know how submitted data is processed within the database or what conclusions are derived from it.”

The perceived invisibility of AI operations diminishes user agency and fosters skepticism regarding privacy controls. Par- ticipants often viewed opt-out mechanisms or safety regulations as superficial, because the underlying data handling is intangible. P20 highlighted the resulting anxiety, noting, “when you lack sufficient confidence in the unknown, you experience anxiety and fear.” P28 added that the elusiveness of the technology makes it hard to verify if restrictive settings are effective.

We conducted interviews remotely via Tencent Meetings and Zoom. Session lasted between 31 and 58 minutes, averaging 40 minutes. Before starting, we explained the interview’s purpose, ensured confidentiality, and obtained informed consent for both participation and audio recording. The interviews were recorded and automatically transcribed before analysis.

5/44 participants also pointed out that these tools lack adequate privacy policies, hindering their understanding. Information asym- metry between corporations and users fostered distrust regarding data persistence and profiling. P7 observed that this complexity often leads to “blind consent”, “everyone basically just scrolls to the bottom and clicks ‘Agree and Confirm’ ... the algorithm is somewhat like a ‘black box’.”

3.3 Data Analysis

We analyzed the interview data using thematic analysis [17]. All audio recordings were first automatically transcribed and then

Investigating Novice Researchers’ Perceptions of Research Privacy Within LLM-Assisted Workflows Conference acronym ’XX, June 03–05, 2018, Woodstock, NY

Finally, 4/44 participants expressed concerns about the AI “mem- ory” and the permanence of data in cloud infrastructure. The inabil- ity to verify data deletion lead to fears of commercial exploitation or profiling. P10 questioned the potential of entities to profit from the system’s memory, noting “If someone were to buy its ‘memory’ function ... could they profit from that?” For non-technical users like P24, the continuous aggregation of data (e.g. via training) made it difficult to predict future risks.

by abstracting and fragmenting data. Participants thought that such abstraction detaches specific ideas from their owners rather than reproducing sensitive information, especially finding that the system also provides fragmented viewpoints than reproductions of user projects (P23). P25 described this as a form of protection, noting that “AI receives and re-interprets information, which prevents the intentional leaks associated with human handlers”.

Furthermore, participants believed that automated data pipelines minimize privacy risks by removing human intervention (P9). The institutional division of labor suggests that no single group can aggregate or access comprehensive profiles. P9 argued that, “pro- grammers lack the ability to scrape information across disparate departments.”

Unavoidable knowledge leakage. 4/44 researchers believed that sharing data with AI models inevitably leads to leaks, rendering absolute confidentiality impossible. Distrusting corporate promises, many adopted a defensive mindset. As P6 remarked, “I haven’t read their specific fine print ... I tend to assume the worst-case scenario regarding their intentions.”

Finally, 2/44 participants perceived the model’s refusal mecha- nisms as the primary system-level mitigation strategies. P12 noted that “these guardrails allow the model to piece together a puzzle based on the information provided, than actively pry into others’ privacy.” This structural vagueness was perceived as a protective layer that ensures anonymity while delivering detailed insights.

Unlike general data breaches, 8/44 researchers feared that the model will learn and reuse unpublished work. Participants viewed this as a form of intellectual theft. P25 argued that submitted in- formation inevitably resurfaces, while P4 expressed concern that “ideas, thought processes, or the most basic research data could be

grafted onto someone else’s framework,”

Finally, 7/44 researchers felt that these AI tools prioritize external interests over academic confidentiality. P24 observed that corporate policies are “likely influenced by factors like government regulation ... therefore, it isn’t completely confidential.” Therefore, users like P21 concluded that completely avoiding these tools was their only safe option.

4.2 Perceived Privacy Risks

Valuable information. Participants enumerated various types of important information. First, participants fear that unique inquiries could lead to academic scooping (P1,P9-10,P13,P19-20,P27,P36). P28 observed, “sometimes the thinking or logic this AI speaks of is so consistent and similar to what my labmates say.” Second, uploading unpublished manuscripts for proofreading creates a tension be- tween editing utility and data retention risks (P7,P26,P35,P42). P23 admitted, “you can use this advice to revise ... where I would upload my entire, completely unpublished first draft.” Third, raw empirical data like field notes and medical records are viewed as non-replicable competitive advantages (P4,P6,P31). P8 stated, “the valuable things are ... the exclusive empirical materials I have gathered.” Fourth, risks include biometric leakage and the exposure of human subject iden- tities due to improper de-identification (P3,P12,P20,P31,P35). P27 confessed, “I don’t perform pre-processing on the transcripts or handle de-identification.” Finally, researchers also view iterative prompting strategies and restricted institutional materials as private intellec- tual assets (P6,P10).

Iterative optimization. 8/44 participants perceived their data as a functional asset essential for model refinement and personal- ized experiences. This data-for-service exchange is considered a necessity to drive model optimization and enhance system memory regarding user preferences. For some, the benefits of rapid feedback and improved performance outweighed privacy costs. P6 noted, “Their using it for training doesn’t conflict with my interests. My goal

is to get quick feedback.” Consequently, users recognized that the utility brought by LLM-assisted tools is linked to the learning pro- cess where the system enriches its understanding through inputs (P24).

On the contrary, 3/44 participants held the belief that individ- ual contributions are anonymized when aggregated into massive training corpora, mitigating their perceived privacy risks. Partici- pants frequently suggested that the scale of data synthesis grants them a form of collective invisibility. P6 expressed comfort in this anonymity, stating, “I find it acceptable because I feel I am linked with a larger collective ... I become invisible within that group, so I am not worried.” This view is further echoed by participants’ as- sumption that LLMs primarily rely on public information rather than ongoing research or unpublished ideas for training (P36).

Unauthorized disclosure of intellectual property. 21/44 par- ticipants worried about the unauthorized disclosure or external acquisition of novel concepts and unpublished manuscripts, which could lead to scooping and loss of academic standing. They feared that submitting core assets to AI models might expose their ideas to competitors, thereby causing idea convergence. Users also per- ceive a misalignment between research value and corporate profit motives, exacerbating the risk of intellectual property leakage by service providers.

Despite the benefits, 21/44 participants expressed concerns re- garding IP leakage or unintended knowledge transfer during the model optimization process. 14/44 participants expressed anxiety that unique insights provided by one user can be inadvertently retrieved and presented to others as synthesized output (P7). P4 questioned “whether our proprietary ideas might eventually become one of the data source it masters and be provided as feedback to others during interactions.”

Empirical data exposure. 4/44 participants highlighted the risks of uploading raw primary data, such as medical records and interview transcripts, which often lack confidentiality guarantees when processed by LLMs. Beyond raw data, participants worried that their unique interpretive frameworks could be exposed. Addi- tionally, participants noted that the highly specific prompts used for literature reviews could inadvertently reveal sensitive, unpublished research directions and specialized knowledge.

Obfuscation by AIs. Participants viewed privacy protection as a process of semantic transformation, where the AI serves as a buffer

Conference acronym ’XX, June 03–05, 2018, Woodstock, NY Trovato and Tobin, et al.

Deanonymization and profiling. 10/44 participants reported concerns regarding AI models’ ability to reconstruct personal iden- tities by synthesizing fragmented data points. This process acts as a narrowing mechanism where various clues are combined to uniquely identify an individual within a large population. P24 com- pared this to a statistical approach that “narrows the potential iden- tity range until the user is exposed within that correct interval.” An- other participant recounted an instance where the model inferred their real name through semantic comparison, based on the pro- vided conversation history (P27).

habits and domain-specific knowledge could compromise intellec- tual property (P31). They viewed the longitudinal memory of AI systems with deep suspicion, fearing the commercial exploitation and unauthorized monetization of their profiles. P10 expressed this apprehension by stating, “if someone bought its memory function or something, could they also profit from it?” They also recounted in- stances where the model proactively referenced past research ideas in entirely new dialogue windows, even months after the original session was supposedly deleted, and personalization settings were disabled (P36). Illustrating this illusion of user control, P10 noted, “I would delete it, but I feel that after deletion, it still remembers these

2/44 participants thought that the system’s capacity to process multimodal inputs and search themes amplified the risk of spa- tial and professional deanonymization. By analyzing visual clues in images or unique professional characteristics, AI tools can pin- point residential addresses or locate specific scholars within narrow research fields. P24 described how the AI identified a specific apart- ment building and unit number from visual clues in a screenshot. Similarly, P31 noted that researchers in highly specialized domains are easily targeted by the system, due to the limited number of active practitioners.

things.” (P10)

Security vulnerabilities. 4/44 participants thought there are multiple technical and operational vulnerabilities that facilitate unintended data exposure, including API key leakage, breaches in third-party integrations, and accidental privacy triggers. They feared about improper access management, particularly within shared account environments or on multiple devices (P6,P12). Users noted that failing to terminate sessions allows unauthorized indi- viduals to invisibly retrieve historical queries and misuse sensitive information (P12). Highlighting this physical access risk, one par- ticipant warned, “if we forget to log out, and someone else uses my computer, they could also see these private things.” (P12)

Furthermore, 4/44 participants thought that continuous interac- tion enables AI systems to implicitly accumulate data and construct detailed user personas encompassing sensitive behavioral and psy- chological traits. P20 expressed discomfort with this covert profiling, noting that the AI accurately inferred their age range despite never being explicitly provided with demographic details. Models are re- ported to also deduce their hobbies, research focus and personality traits (P3-4). This inferential capability creates a tension between the utility of personalized assistance and the necessity of session isolation, where context retention may introduce privacy degrada- tion and cross-session bias risks (P3,P35). Capturing this discomfort with profiling, P4 reflected, “it told me a lot, what I like, what my hobbies are, what my focus is, what kind of personality I roughly have, so I think it is like an observer.”

Research vs. daily privacy risks. While participants detailed privacy risks of LLM-assisted research tools, 8/44 participants ex- pressed no concerns for data leakage, and believed that the risks for research privacy were lower than for everyday interaction. They mentioned that AI-induced risks are minimal compared to existing digital threats or academic norm violations (P4,P42). They explained that most ideas are largely similar, and they do not think they pos- sess unique ideas that others could not come up with. Furthermore, they felt that LLMs were generally not capable of providing help detailed enough to support their specific ideas, and instead re- stricted their inquiries to their broader research aims (P25,P42). Stepping back, they thought that LLMs are usually trained on mas- sive datasets. They therefore believed that it is hard for LLMs to memorize specific user-inputted content (P4,P6,P39). Still, partici- pants believed the reduction of privacy risks relied on contractual behavior (P20,P25).

Finally, 2/44 participants thought cross-platform data synchro- nization within corporate ecosystems brings additional risks. Inte- grating LLM conversational logs with broad e-commerce or social media networks create a pervasive targeted advertising environ- ment. P8 feared that conversational data could be repurposed for shopping predictions within a large corporate network. This cross- device profiling leaves users feeling personally located and granu- larly annotated (P6).

18/44 participants drew a clear distinction between the institu- tional governance of research data and the perceived degradation of personal privacy in daily lives. They noted that research privacy is strictly regulated by ethical mandates and institutional review boards, whereas daily personal data is increasingly viewed as be- yond individual control (P13,P29). Due to the frequency of data breaches, many participants adopted a fatalistic perspective regard- ing their everyday data, concluding that individual defensive mea- sures are often futile against data collection (P29). As P13 noted, “In research context, privacy considerations are primarily framed within the scope of ethical standards and institutional review boards.” (P13)

Memorization and data deletion. 12/44 participants expressed concerns that sensitive research inputs might be permanently inte- grated into the model training corpus or internal memory, leading to involuntary data reuse (P20,P36). They feared that the retained sensitive information might be invisibly abused (P27,P35), and AI systems could directly learn from uploaded images or other per- sonal content without proper anonymization (P40,P42). Some noted that AI’s strong learning capabilities amplify these threats (P3-4). P31 questioned, “there will always be a memory, right? So then you worry about whether this memory will become public.”

Conversely, 8/44 participants argued that the repercussions of re- search privacy failures are more severe than those occurring in daily lives. They suggested that while daily privacy leaks are concerning, they lack the immediate impact on professional survival that re- search leaks entail. As P26 explained, “the consequences of research data leakage are immediate and severe. It involves either substantial

4/44 participants held distrust regarding data deletion mecha- nisms, frequently observing cross-session memory retention (P7,P10, P36). Many users discovered that clearing a conversation thread from the user interface did not erase corresponding memories from the backend (P7,P10). Users feared that the synthesis of professional

Investigating Novice Researchers’ Perceptions of Research Privacy Within LLM-Assisted Workflows Conference acronym ’XX, June 03–05, 2018, Woodstock, NY

legal penalties or losing the priority of discovery.” Consequently, par- ticipants reported employing selective disclosure strategies because their professional lives are based on the confidentiality of their research findings (P20).

regarding privacy remain relatively sparse, with discourse instead centering on pragmatic security measures such as account protec- tion. This focus is particularly relevant in collaborative settings where, as P25 noted, “multiple users may inadvertently gain visibility into sensitive logs.”

2/44 participants explicitly prioritized daily privacy, citing its direct implications for physical and financial risks. They noted while a research idea’s value remains speculative prior to publication, exposure of personal identifiers, especially those of participants, yields concrete harms (P6,P23). P23 stated, “these data points are inextricably linked to physical safety, financial security, and property rights.”

Scholars and media. 11/44 participants gained knowledge around risks by synthesizing information from academic literature, public reporting, and social media platforms (P4,P7). P6 and P37 identified persistent concerns regarding intellectual property rights and the impersonation of users on social media to solicit funds (P6,P37). For others, awareness was reinforced by specific case studies involving data leakage during AI interactions (P7,P20). As P20 remarked, “A query regarding a specific assignment reportedly prompted AI to output an entire completed document, including sen- sitive personal identifiers.” (P20). P4 further emphasized that this perspective is informed by a synthesis of diverse sources including specialized social media channels and scholarly articles.

Despite these contextual differences, 6/44 participants expressed a reluctance toward unauthorized information disclosure. They perceived that privacy is defined by an individual’s choice to with- hold information, regardless of whether that information relates to professional output or personal habits (P4,P31). P31 observed, “in a research context, one is naturally reluctant to disclose a nascent

idea.” (P31) P4 concluded that “unauthorized disclosure of private information is universally undesirable because privacy ultimately implies information that I explicitly chose not to share.” (P4)

5 RQ2: Research Privacy Protection Practices and Perceived Efficacy

Participants took different ad-hoc practices to protect their privacy, as shown in Table 2, which they often perceive as ineffective.

4.3 Knowledge Sources

Formal pedagogical and institutional instruction. 6/44 partici- pants reported lacking organized mentorship. While some partici- pants received guidance from advisors or online, most participants rarely acquired privacy knowledge through formal pedagogical sources, often finding institutional instructions inadequate or inac- cessible. Furthermore, existing educational courses were frequently criticized as flawed. They noted that online assessments could be easily bypassed through manual guessing (P31). “Ultimately, partici- pants can pass by memorizing the correct answers revealed after initial correct attempts.” (P31) While a minority of participants encoun- tered rigorous data privacy coursework within their institutions, such resources were typically restricted to computer science disci- plines and inaccessible to the broad researcher community (P31).

5.1 Architectural Isolation and Access Control

9/44 participants prioritize environmental isolation to prevent data from leaving private boundaries, often shifting from cloud-based infrastructures to localized deployments. 6/44 participants employ technical controls, most notably by disabling model training and data-sharing functionalities. These efforts are complemented by revoking unnecessary system permissions (P7-8,P23,P27,P36-37) and using session-specific controls, such as incognito windows, to ensure immediate data deletion (P28,P36). For highly sensitive workflows, participants adopt hybrid models, using localized mod- els for prototyping/analysis, and remote models for other tasks to mitigate external exposure (P29). In stances of extreme concerns, however, researchers may avoid using AIs at all to guarantee data integrity (P37).

Empirical engagement and experiential discovery. 9/44 par- ticipants developed their understanding through empirical discov- ery. This includes direct interaction with LLM-assisted systems, where they employ trial-and-error and self-directed inquiry to navigate technical complexities. For instance, P39 acquired direct insights into data confidentiality protocols through extensive ex- perimental work. Similarly, P3 cultivated privacy awareness by manually exploring settings and meticulously reviewing service agreements. Professional research and external context also play a role in their discovery. P26’s perspective on AI governance was informed by professional research and engagement with related lit- erature (P26), while P4 gained insights into the competitive nature of the field by observing research publication cycles and risks of preemptive publication. For others, industry experience and media analysis fostered their awareness (P20). As P20 noted, “my concerns were shaped by firsthand experience during an internship at a LLM company” (P20).

3/44 participants manage privacy through identity isolation. They avoid credential sharing to maintain individual account in- tegrity (P10,P25,P28). However, they also intermittently engage in informal sharing practices, which complicates governance and com- promises security (P25). Furthermore, premium subscriptions and platform reputation serve as proxies for trust. They perceive paid accounts to offer protections for high-stakes manuscripts (P36,P42), which lead users to favor reputable first-party providers with estab- lished infrastructures (P25). They actively avoid platforms known to use user interactions for model training (P8).

Despite these measures, participants emphasized various barriers. In particular, novice researchers lack the resources for localized deployments. They also mentioned constraints like high capital costs (P36), inferior performance compared to frontier cloud models (P8), and fragmented user experience (P23). These behaviors are also different across disciplines, with researchers in STEM fields having more privacy-preservation attempts and practices than those in the humanities (P24). Finally, many researchers remain doubtful

Peer-mediated and collaborative discourse. 8/44 participants favored peer-mediated communications, where knowledge is dis- seminated through informal professional networks and interper- sonal exchanges. P25 observed that direct scholarly discussions

Conference acronym ’XX, June 03–05, 2018, Woodstock, NY Trovato and Tobin, et al.


> **Table 2: Map of researchers’ privacy risks (RQ1) to mitigation practices (RQ2) and challenges (RQ3), according to participants’**

> own mentions. Filled circles indicate associations mentioned by participants, while open circles indicate no association.

Practices & Mitigation (RQ2) Challenges (RQ3)

Intransparency and informational asymmetry

Human-centric verification and awareness

Architectural isolation and access control

Fragmentation and decoupled processing

Adversarial testing, probing and deletion

Ineffectiveness of current mitigation

Data sanitation and obfuscation

Privacy-publication trade-off

Accountability deficit

Lack of control

Privacy Risks (RQ1)

Unauthorized disclosure of intellectual property # #     # #     # # Algorithmic memorization #   # # #   #   #   Empirical data exposure #   # #   # # #     Deanonymization and profiling #     #   # # #     Security vulnerabilities   #   # # #     # # Risk assessment skepticism and negligibility # # # #       # #

as to whether their data is truly excluded from backend databases, regardless of the localized settings or controls applied (P7,P36).

prior to submission (7/44 participants), using multiple AIs for frag- mented tasks (7/44 participants), and performing core work manu- ally while reserving AI for final polishing (9/44 participants). P26 noted that “they only provide data fragments rather than the full dataset to avoid that the model access whole research idea.” For highly sensitive inquiries, researchers also used locally deployed tools to process fragmented questions, aiming to mitigate exposure risks (P36).

5.2 Data Sanitation and Obfuscation

15/44 participants sanitized their data prior to input. Some exercised data minimization, deliberately restricting the volume and sensitiv- ity of their inputs to reduce potential exposure (P28,P31). Others used strategic prompting to extract analytical insights, concealing sensitive context to avoid full data uploads (P42).

Participants distributed these fragmented tasks across multiple chat sessions to reduce risks (P35). By dispersing their prompts, they ensured that no single system retained a comprehensive overview of their work (P7). Additionally, users put prompts on multiple LLM- assisted research tools to mitigate identity reconstruction and avoid verbatim replication (P35). They submitted identical prompts to various models and manually synthesized diverse outputs, creating composite texts with minimal similarity.

Beyond volume reduction, participants employed specific ob- fuscation techniques to alter the data. Some have well-defined de- identification “strategies”, such as redacting personal identifiers and geographical locations before transmission (P26). They noted that properly anonymized data makes it technically infeasible for the system to reconstruct respondent profiles (P13). To balance anonymization with the contextual integrity for accurate AI out- puts (P7), users replaced specific data with generalized placeholders and rephrased their inquiries (P4,P8). They also routinely withhold key details from their prompts (P4).

5.4 Adversarial Testing, Probing and Deletion

4/44 participants conducted adversarial probing, role-playing, or testing. Some adopted an exploratory stance, trying adversarial probing against AI models to assess system boundaries. They in- structed the AI to analyze their historical conversational data, to determine its automated profiling capabilities. P12 observed that the system initially exhibited built-in constraints against soliciting private data. With a similar method letting LLMs to summarize themselves, P36 conducted a comprehensive adversarial probe that yielded an alarmingly granular report. The generated profile ac- curately inferred their university affiliation, doctoral cohort, resi- dential location, and recent psychological states entirely from prior dialogues. However, P36 noted that subsequent system updates ap- pear to have strengthened privacy guardrails against such profiling.

Despite these measures, participants mentioned the limitations of manual obfuscation. They felt that maintaining data control re- quires substantial cognitive effort, which makes some give way to complacency (P26). Furthermore, users expressed concerns regard- ing model capabilities, fearing that AI’s cross-session memories could aggregate fragmented inputs over time (P20).

5.3 Fragmentation and Decoupled Processing

7/44 participants employed fragmentation strategies to prevent models from reconstructing sensitive intellectual data. By decou- pling complex tasks into isolated and non-contextual units, they thought that these methods obscured the scope of their research. Common approach include segmenting datasets and manuscripts

Other participants employed deception or role-play to obscure risks. By constructing hypothetical scenarios based on real events, participants fed the AIs with synthetic data (P25). P25 thought “this

Investigating Novice Researchers’ Perceptions of Research Privacy Within LLM-Assisted Workflows Conference acronym ’XX, June 03–05, 2018, Woodstock, NY

5.6 Ineffectiveness of Current Mitigation

ensures that the model cannot distinguish between factual data and hypothetical constructs.” (P25) Additionally, participants also chose to manually rewrote the final outputs than adopting AI-generated text (P8).

8/44 participants expressed skepticism regarding the efficacy of existing privacy mitigation strategies. Participants viewed these protective actions as mere psychological comfort than robust se- curity measures (P7-9,P12,P36). This skepticism is driven by their perceived inevitability of data harvesting and mistrust towards AI service providers. They held distrust towards the technological corporations operating these platforms, and expressed anxiety re- garding the opacity of backend operations, and the potential for unauthorized surveillance. They argued that profit-driven entities lack the motivation to permanently erase valuable training data. As P4 explained, “my distrust is rooted in the unknowability and opacity of these systems.” Participants felt entirely disempowered, lacking the technical resources to audit backend practices, and the legal standing to hold corporations accountable. As P29 noted, “I have a lack of trust in tech giants. They possess the capability to act as they please regardless of their public assurances.”

Participants also requested data deletion, routinely deleting chat logs, specific keyword queries, and uploaded media immediately upon task completion, to minimize exposure windows and prevent risks associated with shared accounts (P6-7,P35,P39). This proto- col was enforced most strictly when they inadvertently processed sensitive third party data (P20). While some users viewed UI-level deletion as a necessary security measure that provided psycholog- ical closure (P9), the majority remained skeptical of its technical efficacy. They empirically found that retroactive deletion cannot erase information already integrated into the global training corpus (P12), and strongly suspected that “deleted logs likely persist in the system background architecture.” (P8) Furthermore, users expressed lingering uncertainty regarding the invisible retention of ambient background data captured during voice interactions (P20).

They also expressed concerns towaeds the discrepancy between user interface modifications and actual backend data persistence. They perceived user-side controls as superficial features that fail to prevent backend data retention (P10,P12,P31,P36), and therefore restricted their mitigations to the data entry point. As P25 noted, “I remain uncertain as to how these algorithms actually process my

5.5 Human-centric Verification and Awareness

20/44 participants adopted human-centric practices to reduce pri- vacy risks, ranging from avoiding AI use altogether and manually abstracting sensitive data to auditing model outputs, using step-by- step interaction protocols, and reverting to human-only workflows for sensitive tasks. 6/44 participants relied on themselves to think out ideas, avoiding AIs entirely. Instead of inputting raw or sensi- tive datasets into generative models, 12/44 participants manually abstracted the data prior to analysis (P31,P42). They meticulously audited AI outputs to ensure the models were not outputting per- sonal arguments or unauthorized testimony, often through requir- ing explicit citations for cross verification (P12). Furthermore, 3/44 participants adopted granular, step-by-step interaction protocols. P4 described evaluating the model feedback at each incremental step, terminating the session if there are inaccuracies or privacy risks. They also retroactively reviewed their interaction histories to confirm that no personal identifiers or lifestyle data had been inadvertently disclosed to the system (P25).

data or resolve the underlying challenges of privacy protection.” Some suspected that deleting chat logs or disabling training permissions merely removes client-side visibility, while the underlying infras- tructure retains the information (P10). As P7 noted, “the act of deleting or regenerating a dialogue may merely remove the informa- tion from the user interface. It remains highly probable that the data persists within the system.” They argued that discarded inputs are actively integrated into the system’s latent memory, similar to data recovery in hardware components (P12).

Furthermore, participants viewed data leakage as an unavoidable consequence of modern research workflows. As generative models have become indispensable, users felt compelled to accept the asso- ciated privacy risks with no viable alternatives (P37). Researchers adopted a dual-sided stance toward privacy loss, as P31 commented, “despite the risks, the utility of these tools necessitates their continued

Beyond output auditing, 3/44 participants frequently reverted to traditional human processes for highly sensitive tasks. To evade AI- generated text detectors, they manually restructured sentences to retain human writing patterns (P35). In collaborations, researchers noted that peers often explicitly stipulated that manuscripts un- dergo human-only editing without AI involvement (P19). For high- stakes discussions, participants preferred consulting senior mentors over using LLMs. They emphasized that established interpersonal trust and professional ethics provide a level of security against intellectual property theft that automated digital platforms cannot guarantee (P28).

use.”

To manage the lack of protection, individuals frequently ratio- nalized their exposure by downplaying the value of their own in- tellectual property. They assumed that their routine research ideas or personal details lack sufficient value to incentivize corporate misappropriation. P12 stated, “I sometimes rationalize that as an or- dinary individual without highly sensitive information, such stringent measures might not be strictly necessary.”

6 RQ3: Challenges to Protecting Privacy 6.1 Privacy-Publication Trade-off

4/44 participants highlighted the need for education and aware- ness. They thought that understanding underlying technical mech- anisms, such as context windows and architecture limitations, was essential for formulating safe queries (P20,P28). However, P7 sug- gested that constant exposure to data harvesting in daily digital applications has eroded their privacy awareness. Consequently, par- ticipants stressed that “individuals must cultivate active vigilance, as one cannot rely solely on legislation for privacy protection.” (P36)

8/44 participants highlighted the tension between the operational necessity of LLMs and the inherent anxiety regarding data expo- sure. Their primary concern was the potential for models to in- advertently leak unpublished research ideas, which paradoxically pressured users to accelerate their publication cycles to preempt AI-driven plagiarism (P20). Despite acknowledging the persistent

Conference acronym ’XX, June 03–05, 2018, Woodstock, NY Trovato and Tobin, et al.

threat of unauthorized data usage in model training (P36), partici- pants overwhelmingly prioritized efficiency over strict data privacy, like using LLMs for labor-intensive tasks such as document transla- tion, literature summarization, and image generation. Highlighting this dilemma, P20 explicitly noted, “between this productivity and anxiety, I still choose productivity.” Consequently, users routinely ac- cepted privacy compromises for utility, such as retaining sensitive chat logs for ongoing tasks (P35) or rationalizing data exposure as an unavoidable cost of operational convenience (P23). Ultimately, the competitive disadvantage of abstaining from AI tools was per- ceived as a far greater threat than the associated privacy risks (P36). As P23 stated, “despite knowing AI might leak my data ... the need to improve efficiency makes its use necessary.”

or high-profile figures (P20,P42). They also valued clean frontend interfaces and proactive prompts for explicit consent regarding data learning (P8). As P28 argued, “The interface should offer more than just a simplified output. It should reveal the underlying reasoning process. Platforms should proactively solicit consent.”

Finally, 4/44 participants highlighted the role of effective educa- tion. Effective training should include practical modules that culti- vate awareness of proper engagement and data discretion (P31,P34). They also requested comprehensive manuals detailing the compu- tational processing of sensitive information (P4). Highlighting the need for genuine educational value, P31 stated, “We need practical training modules rather than performative or superficial instructions.”

This emphasis on productivity is driven by a competitive re- search environment that prioritizes execution speed over ideas’ nov- elty. Although participants feared idea leakage, this concern para- doxically motivated them to use AI to accelerate their work, aiming to publish before their concepts could be exposed (P6,P8,P20). As P6 noted, “ideas are not precious now. The key is to quickly transform the idea into a paper through hard work. Speed is key ...” Consequently, speed in the publication pipeline is deemed more critical than pro- tecting concepts from AI scraping (P8). Reliance on AI efficiency has increased the risk tolerance, which is reflected in the fact that, users often bypass privacy protocols. For example, participants admitted to inputting confidential documents into unapproved models to prioritize speed over compliance (P6).

6.3 Lack of Control

13/44 participants complained about lacking granular control in data management, often facing a binary choice between system util- ity and privacy. Users emphasized the necessity for session-specific controls, such as per-interaction toggles to withhold consent for model training (P7,P23). They desired selectable operational modes to maintain agency over sensitive research identifiers, without com- promising tool functionality (P10,P41). To navigate these trade-offs, participants needed compartmentalized interfaces that separate persistent memory for ideation from ephemeral sessions for iso- lated tasks (P3). Highlighting this demand for granular autonomy, P23 stated, “for every new session, there should be a dedicated toggle to withhold consent for data disclosure or uploading.”

Deep skepticism persists regarding current data retention poli- cies, with users viewing frontend deletions as largely performative (P1,P20). Participants argued that once information is transmitted, its influence on the model is set, making superficial removals in- effective for protecting high-stakes intellectual property (P1,P42). Consequently, users advocated for verifiable and permanent dele- tion mechanisms, ensuring that purged data enters an irrecoverable state across all central databases (P10,P24).

6.2 Opacity and Informational Asymmetry

13/44 participants reported informational asymmetry regarding data collection and processing, leading to a demand for accessible privacy governance. Vague privacy agreements cause user anxiety concerning whether inputs are extracted verbatim or analyzed only as keywords (P23). Users criticized speculative terminology like “us- ing data” and requested explicitly defined rights and responsibilities (P8). For non-technical users, ambiguous communication increases apprehension because trust requires demonstrated privacy (P36). As P23 summarized, “privacy policies need to be accessible to non- experts. We need to know exactly how our dialogues and documents will be stored or shared.”

Finally, participants advocated for data minimization and se- curity protocol integration directly into AI models’ architectures. Intrusive permission requests were viewed as irrelevant to core functionality and a violation of privacy prioritization (P38). Users insisted that systems should exclusively retain authorized informa- tion, demanding rigorous non-disclosure protocols and end-to-end encryption for confidential data sharing (P1,P38). Due to system opacity, researchers often opted for zero-retention modes featur- ing immediate session expiration to preempt unauthorized data resurfacing (P34,P39). Emphasizing developer responsibility, P42 argued, “it is imperative that platforms protect the data and intel- lectual property shared within the chat interface through enabling advanced security features.”

Beyond textual policies, 13/44 participants advocated for opera- tional transparency and engineering safeguards to demystify LLM logic. They proposed governance measures such as compartmental- izing database management from frontend algorithms to prevent unauthorized cross-departmental data extraction (P9). Despite lack- ing technical expertise, they expected protections against inadver- tent third-party disclosure and continuous background learning (P24,P26). Platforms capable of proving intellectual property pro- tection were viewed as viable for professional adoption (P24). Re- flecting this need, P9 stated, “I advocate for operational transparency. For instance, I hope for a workflow where functional terms are strictly compartmentalized.”

6.4 Accountability Deficit

9/44 participants expressed a sense of powerlessness regarding their inputs, noting a lack of mechanisms to hold AI corporations accountable for data misuse. They viewed corporate S&P disclo- sures as unreliable and opaque, which increased their anxiety about how information is processed. This lack of transparency creates an accountability gap, as they found it nearly impossible to seek legal recourse or organize collective action (P20). Despite recognizing

The participants thought interface design is important for real- time risk disclosure and granular consent. They suggested compre- hensive disclosure frameworks spanning onboarding, active usage, and post-usage phases (P4,P19). This includes safety assurances near input fields and specific protective options for sensitive topics

Investigating Novice Researchers’ Perceptions of Research Privacy Within LLM-Assisted Workflows Conference acronym ’XX, June 03–05, 2018, Woodstock, NY

these vulnerabilities, they remained highly dependent on these tools, leaving them in a compromised position.

protection [43]. In contrast, research privacy centers on the mis- appropriation of IP by external actors and the leakage of novel concepts.

To mitigate this vulnerability, researchers advocated for state- level legislation and regulatory oversight, alongside practical re- mediation frameworks. For example, they prioritized institutional remediation, such as securing publishing rights following a leak, over monetary compensation (P19). However, others cautioned that aggressive regulation could stifle innovation (P28,P36).

Despite the difference, both domains suffer from a deficit in privacy education. Beyond rudimentary compliance, such as signing consent forms for review boards, students and researchers both receive minimal training on modern cryptographic or technical data protection methods [43, 45]. This vulnerability is exacerbated by a lack of GenAI literacy even among faculty, particularly in non- CS disciplines, where advisors lack the technical expertise required to guide novice researchers through GenAI risks [12, 35].

Furthermore, users called for redefining legal privacy boundaries and mandating explicit consent for all data access. They argued that interaction logs should be treated with the same confiden- tiality as sensitive personal data, such as national IDs or financial records (P42). They criticized the unauthorized sharing of personal content and intellectual property, noting that automated systems often bypass consent and undermine user agency (P24,P35). P35 highlighted this loss of agency, “[The system] didn’t respect me. It didn’t ask. It didn’t ask if I agreed to send my photos to others.” As a result, they expected comprehensive regulations to govern data access and sharing.

Research privacy vs. corporate privacy. Research privacy is similar to corporate environments in the necessity of shielding sensitive data from competitors [2]. In industry, privacy is often treated as either a competitive advantage or a bottleneck to product development [51, 83]. However, disparities exist in the underlying management infrastructure. Corporate entities may leverage en- terprise contracts with LLM providers and the resources to deploy localized models to prevent leakage [88]. Conversely, researchers lack the bargaining power to negotiate privacy agreements and the computational resource necessary for deployment.

The traceability of breaches also varies. While corporate leaks involving customer databases are generally well-defined and de- tectable via audit trails, leakages of research ideas are hard to trace and verify. Furthermore, the power dynamics of these environ- ments lead to different privacy trade-offs. Corporate security pro- tocols often achieve protection through invasive employee surveil- lance [82, 95]. In contrast, the researchers we interviewed typically bear the privacy management burden themselves.

7 Discussion 7.1 Research Privacy

Our findings suggest that research privacy is different from daily, academic or corporate privacy. We contextualize these differences to highlight the unique vulnerabilities of the research lifecycle.

Research privacy vs. daily privacy. Research privacy diverges from daily personal privacy through its professional stakes and the complex nature of the underlying data. While daily privacy breaches often result in leakage harms or targeted advertising, the exposure of research data carries professional consequences, in- cluding the loss of research priority (i.e., scooping), and legal or ethical penalties. Unlike personal data, which users often perceive as having low utility for external adversaries, research data, com- prising interpretive frameworks, unpublished manuscripts, and raw datasets, constitutes a high-value competitive advantage. This data is uniquely susceptible to involuntary memorization by LLMs and subsequent malicious reuse.

7.2 Perceived Risks, Mitigation and Realities

Perceived risks vs. realities. Researchers often underestimate their research privacy risks due to a dilution fallacy. Believing their individual ideas are safely hidden within massive datasets, they largely rely on manually removing identifiers. However, tech- nical evidence contradicts this perception. Increasing a model’s parameter size increases data memorization capacity [50] even de- spite corresponding increases in dataset size, making LLMs highly vulnerable to targeted data extraction [13]. Furthermore, for high- stakes information, attackers may also force models to leak mem- orized data (e.g., IP-protected documents) using specific inducing techniques [19, 23, 40]. Even manual obfuscation is structurally flawed: after partial redaction, structured data patterns still per- sist [109, 115], allowing for reconstruction and even deanonymiza- tion [84].

Furthermore, research privacy is highly time-sensitive. Partici- pants typically prioritize protection within the fixed window before publication. Unlike daily privacy, where removing explicit Per- sonally Identifiable Information (PII) is often deemed sufficient for de-identification, standard masking is inadequate for research contexts. As research ideation relies on interconnected logic and unique methodologies, data remains attributable even after heavy obfuscation. These logical fingerprints allow LLMs to reconstruct intellectual contributions or perform granular profiling, render- ing traditional data sanitation methods ineffective [120]. Therefore, while many users adopt a fatalistic view toward daily privacy due to pervasive tracking [98], researchers maintain a high-anxiety stance toward their research privacy.

Mitigation vs. realities. To protect their data, users often adopt surface-level strategies like UI-level deletion, input fragmentation, and adversarial probing. Yet, these practices may fail to mitigate the risk. Deleting chat logs may provide a false sense of privacy. Because user inputs are algorithmically integrated into the model via training and memory mechanisms, frontend deletions cannot reliably reverse backend retention [52]. Research on under-learning confirms that supposedly deleted data may leave exploitable resid- ual traces [16, 64, 93]. Such sensitive data may expose models to membership inference attacks [106]. Similarly, input fragmenta- tion is ineffective because network-level metadata can still expose

Research privacy vs. academic privacy. Academic privacy typically focuses on institutional surveillance and unconsented collection of educational data, such as coursework and student records [45]. In this domain, the privacy-utility trade-off usually centers on balancing personalized learning benefits against data

Conference acronym ’XX, June 03–05, 2018, Woodstock, NY Trovato and Tobin, et al.

hidden prompts and semantic intent [39]. Finally, when a model refuses to disclose information, users often mistake this for data absence or effective privacy control. In reality, refusals typically re- flect safety filters [26], and attackers can still use prompt injections to extract sensitive research context [37].

entirely within the institution. This could be paired with customized interfaces, with one secure side for sensitive data, and another side with low-stakes tasks like literature reviews. This separation pro- tects important research data from being stored by external service providers.

Regulatory misalignment. Institutional regulations, such as IRB protocols, are not all compatible with AI-assisted research prac- tices. As some universities rely on static compliance checklists, users find the guidance superficial and disconnected from their actual workflows. Additionally, institutions’ research-related reg- ulations are frequently fragmented: IRB protocols manage risks related to studies, IT departments oversee tool security and data leakage, PIs dictate workflow norms, and research offices govern IP ownership. In practice, novice researchers need to manually synthesize these rules to determine if a specific AI interaction is compliant. Without a unified guidance framework, users form ad- hoc mental models to navigate the system’s opacity [57]. This gap between technical reality and lay mental models renders exist- ing policy communication highly ineffective [90] and undermines privacy-preserving behavior [103]. This failure stems from the mis- match where governance bodies assume deterministic data flows, while LLMs operate non-deterministically, especially when using AI agents and tool calls [56], and furthermore from the difficulties that many governing bodies face with trying to regulate this fast- moving and dynamic new research paradigm. Faced with a lack of clear guidance and regulation, many researchers opt to use AI tools heavily – and sometimes irresponsibly – in order to gain a competitive advantage.

Automated data screening. IRBs could use automated screening tools beyond mere checklists, similar to the privacy-compliance monitoring tools in corporations [74]. These tools monitor and flag sensitive research data in user prompts or uploaded files before they are sent to chatbots. However, designers must carefully balance these protections to respect academic freedom and avoid creating invasive academic surveillance [45, 82].

Interface Transparency Data usage transparency. Systems should provide real-time visual signs showing exactly how specific inputs are handled, which clearly separate data kept for model training, temporarily saved data, and completely unlogged chats. This transparency reduces the efforts needed to manually hide sen- sitive data and helps researchers make informed privacy-preserving choices.

Socio-technical Aspects Interactive privacy training. Static rule checklists are often difficult to apply on LLMs, whose data flow is opaque and dynamic [33]. Institutions should clearly distinguish between educational usage and research usage. Research-oriented training should adopt interactive, scenario-based tutorials. By vi- sually showing how adversarial prompts or other attacks can ac- cidentally leak a researcher’s core ideas, systems can explain how institution-provided tools mitigate these risks [30, 89].

Dedicated channel for AI risks. Novice researchers should have a dedicated channel for AI-related research risks, which unite dif- ferent perspectives such as IRB, IT and IP offices and provide com- prehensive, actionable plans. This entry points should have clear guidance for varying data types, such as diverse information levels, and mappings to AI usage restrictions, like those in the Harvard’s models [31, 33].

7.3 Privacy-utility Trade-off

The intense “publish-or-perish” culture creates a severe conflict between strict institutional regulations, such as IRB protocols, and the competitive advantages of AI tools. To secure data, university policies typically mandate localized models or rely on user restraint. However, these approaches fail by ignoring researchers’ extreme productivity pressures and the limitations of self-hosted architec- tures. Consequently, expecting user restraint is an unsustainable security posture. The high functional payoff of AI forces researchers to accept privacy risks to maintain research output [86]. Abstaining from AI creates such a severe competitive disadvantage that users routinely rationalize data exposure as an unavoidable operational cost. This prioritization of efficiency over compliance is universal: even experienced privacy analysts processing hyper-sensitive data prefer LLM assistance to reduce effort [44]. Therefore, institutional mandates that simply prohibit cloud-based AI may be bypassed in everyday research practices.

Promoting academic privacy champions. Learning from successful corporate examples [83], universities should identify and support privacy champions among novice researchers. Tools could include community reporting or template sharing to encourage peer-led privacy-preserving habits. However, these programs must be ap- plied carefully to avoid adding administrative burdens that reduce researchers’ motivation [73].

8 Limitations and Future Work

We acknowledge several limitations in this paper. First, the reliance on convenience sampling via online platforms introduces selection bias. While we recruited a diverse pool spanning multiple countries and backgrounds, the findings, especially code frequencies, may not fully generalize to the global research population. Future research should use large-scale longitudinal studies to observe the evolution of user mental models. Second, as with most qualitative studies, our data is subject to self-reporting biases, such as recall bias and social desirability bias. To mitigate this, future work should include empirical technical audits to objectively measure the discrepancy between user-perceived mitigations and actual usage. Third, our paper focuses on novice researchers, whose workflows and risk per- ceptions may differ from established scholars. Comparative studies

7.4 Implications

To address the aforementioned vulnerabilities, we propose implica- tions across three levels: data control, interface transparency, and socio-technical aspects.

Data Control Separated conversational workspaces. To balance data privacy with system usefulness, architectures could separate memory-based and unlogged interactions. Institutions could pro- vide tools similar to Harvard’s “AI sandbox” [32] or NUS’s “AI- Know” [21], which offers educational environments that keep data

Investigating Novice Researchers’ Perceptions of Research Privacy Within LLM-Assisted Workflows Conference acronym ’XX, June 03–05, 2018, Woodstock, NY

involving senior researchers could reveal how career stages and institutional responsibilities influence research risk assessments.

security challenges in K-12 schools. In Proceedings of the 2023 CHI conference on human factors in computing systems. 1–28. [15] Kang Chen, Xiuze Zhou, Yuanguo Lin, Shibo Feng, Li Shen, and Pengcheng

Wu. 2025. A survey on privacy risks and protection in large language models. Journal of King Saud University Computer and Information Sciences 37, 7 (2025), 163. [16] Zhaoyang Chu, Yao Wan, Zhikun Zhang, Di Wang, Zhou Yang, Hongyu Zhang,

9 Conclusion

This paper examines novice researchers’ privacy perceptions re- garding LLM-assisted research workflows through semi-structured interviews (N=44). Findings reveal a prioritization of productivity over ideas’ protection. Users rely on ad-hoc mitigation strategies, such as data fragmentation, but feel that they serve merely as psy- chological placebos against backend retention. A critical discrep- ancy exists between users’ mental models, which falsely assume input dilution prevents memorization, and actual technical risks. We therefore recommend actions such as institutional automated screening and separated tools, transparent risk visualization, and interactive privacy training..

Pan Zhou, Xuanhua Shi, Hai Jin, and David Lo. 2025. Scrub It Out! Erasing Sensitive Memorization in Code Language Models via Machine Unlearning. arXiv preprint arXiv:2509.13755 (2025). [17] Victoria Clarke and Virginia Braun. 2017. Thematic analysis. The journal of

positive psychology 12, 3 (2017), 297–298. [18] Shaanan Cohney, Ross Teixeira, Anne Kohlbrenner, Arvind Narayanan, Mihir

Kshirsagar, Yan Shvartzshnaider, and Madelyn Sanfilippo. 2021. Virtual class- rooms and real harms: Remote learning at {US}. universities. In Seventeenth Symposium on Usable Privacy and Security (SOUPS 2021). 653–674. [19] A Feder Cooper, Aaron Gokaslan, Ahmed M Ahmed, Amy B Cyphert, Christo-

pher De Sa, Mark Lemley, Daniel E Ho, and Percy Liang. 2025. Extracting memorized pieces of (copyrighted) books from open-weight language models. In ICML 2025 Workshop on Reliable and Responsible Foundation Models. [20] John W Creswell and Timothy C Guetterman. 2019. Educational Research:

Planning, Conducting, and Evaluating Quantitative and Qualitative Research. Pearson (2019). [21] Department of History, National University of Singapore. 2025. Guiding Principles on Generative AI Use AY2025–2026. https://fass.nus.edu.sg/hist/wp- content/uploads/sites/7/2025/08/HY_Guide-to-Use-of-AI-Tools_Aug2025.pdf. Accessed: 2026-04-29. [22] Yi Dong, Ronghui Mu, Yanghao Zhang, Siqi Sun, Tianle Zhang, Changshun Wu,

Acknowledgments

We acknowledge the use of Gemini 3.1 Pro and ChatGPT strictly for minor editing, specifically grammar and style polishing. Authors retain full responsibility for the accuracy, originality, and integrity of this paper.

Gaojie Jin, Yi Qi, Jinwei Hu, Jie Meng, et al. 2025. Safeguarding large language models: A survey. Artificial intelligence review 58, 12 (2025), 382. [23] André Vicente Duarte, Xuandong Zhao, Arlindo L Oliveira, and Lei Li. 2024.

DE-COP: Detecting Copyrighted Content in Language Models Training Data. In International Conference on Machine Learning. PMLR, 11940–11956. [24] Timothy J Ellis and Yair Levy. 2009. Towards a Guide for Novice Researchers


## References

[1] Yasemin Acar, Sascha Fahl, and Michelle L Mazurek. 2016. You are not your

developer, either: A research agenda for usable security and privacy research beyond end users. 2016 IEEE Cybersecurity Development (SecDev) (2016), 3–8. [2] Atif Ahmad, Rachelle Bosua, and Rens Scheepers. 2014. Protecting organiza-

on Research Methodology: Review and Proposed Methods. Issues in Informing Science & Information Technology 6 (2009). [25] Thomais Gkrimpizi, Vassilios Peristeras, and Ioannis Magnisalis. 2023. Classi-

tional competitive advantage: A knowledge leakage perspective. Computers & Security 42 (2014), 27–39. [3] Mutahar Ali, Arjun Arunasalam, and Habiba Farrukh. 2025. Understanding

fication of barriers to digital transformation in higher education institutions: Systematic literature review. Education sciences 13, 7 (2023), 746. [26] Yichen Gong, Delong Ran, Xinlei He, Tianshuo Cong, Anyu Wang, and Xiaoyun

users’ security and privacy concerns and attitudes towards conversational ai platforms. In 2025 IEEE Symposium on Security and Privacy (SP). IEEE, 298–316. [4] American Geophysical Union. 2026. Honors Career Stages and Other Defi-

Wang. 2025. Safety Misalignment Against Large Language Models.. In NDSS. [27] Igor Grossmann, Matthew Feinberg, Dawn C Parker, Nicholas A Christakis,

Philip E Tetlock, and William A Cunningham. 2023. AI and the transformation of social science research. Science 380, 6650 (2023), 1108–1109. [28] Tom Gunter, Zirui Wang, Chong Wang, Ruoming Pang, Andy Narayanan, Aonan

nitions. https://www.agu.org/Honor-and-Recognize/Honors/Nomination- resources/Career-Stages [Accessed: 2026-04-29]. [5] Apple Security Engineering and Architecture (SEAR). 2024. Private Cloud

Zhang, Bowen Zhang, Chen Chen, Chung-Cheng Chiu, David Qiu, et al. 2024. Apple intelligence foundation language models. arXiv preprint arXiv:2407.21075 (2024). [29] Qianyue Hao, Fengli Xu, Yong Li, and James Evans. 2026. Artificial intelligence

Compute: A new frontier for AI privacy in the cloud. Apple Security Research Blog. https://security.apple.com/blog/private-cloud-compute/ [Accessed: 2026- 04-29]. [6] Jinheon Baek, Sujay Kumar Jauhar, Silviu Cucerzan, and Sung Ju Hwang. 2025.

tools expand scientists’ impact but contract science’s focus. Nature (2026), 1–7. [30] Harvard Catalyst Regulatory Foundations, Ethics, and Law Program.

Researchagent: Iterative research idea generation over scientific literature with large language models. In Proceedings of the 2025 Conference of the Nations of the Americas Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers). 6709–6738. [7] Michael Bailey, David Dittrich, Erin Kenneally, and Doug Maughan. 2012. The

2026. Artificial Intelligence and Human Participant Research: Educational Resources. https://catalyst.harvard.edu/regulatory/ai-human-participant- research/educational-resources/. [Accessed: 2026-04-29]. [31] Harvard Catalyst Regulatory Foundations, Ethics, and Law Program. n.d.. Emerg-

menlo report. IEEE Security & Privacy 10, 2 (2012), 71–75. [8] David G Balash, Dongkun Kim, Darika Shaibekova, Rahel A Fainchtein, Micah

ing Technologies, Ethics, and Research Data. https://catalyst.harvard.edu/ regulatory/emerging-technologies/. [Accessed: 2026-04-29]. [32] Harvard Gazette. 2023. Harvard designs AI sandbox that enables exploration, interaction without compromising security. https: //news.harvard.edu/gazette/story/newsplus/harvard-designs-ai-sandbox- that-enables-exploration-interaction-without-compromising-security/. Accessed: 2026-04-29. [33] Harvard Medical School Information Technology. n.d.. Generative AI. https:

Sherr, and Adam J Aviv. 2021. Examining the examiners: Students’ privacy and security perceptions of online proctoring services. In Seventeenth symposium on usable privacy and security (SOUPS 2021). 633–652. [9] Leonard Bauersfeld, Angel Romero, Manasi Muglikar, and Davide Scaramuzza.

2023. Cracking double-blind review: authorship attribution with deep learning. Plos one 18, 6 (2023), e0287611. [10] Tom L Beauchamp et al. 2008. The belmont report. The Oxford textbook of

//it.hms.harvard.edu/about/policies-and-guidelines/generative-ai. [Accessed: 2026-04-29]. [34] Emma Harvey, Allison Koenecke, and Rene F Kizilcec. 2025. " Don’t Forget the

clinical research ethics (2008), 149–155. [11] Sonja Bjelobaba, Lorna Waddington, Mike Perkins, Tomáš Folt`ynek, Sabuj Bhat-

tacharyya, and Debora Weber-Wulff. 2025. Maintaining research integrity in the age of GenAI: an analysis of ethical challenges and recommendations to researchers. International Journal for Educational Integrity 21, 1 (2025), 18. [12] Ramazan Bulut. 2026. Mapping teachers’ awareness of artificial intelligence

Teachers": Towards an Educator-Centered Understanding of Harms from Large Language Models in Education. In Proceedings of the 2025 CHI Conference on Human Factors in Computing Systems. 1–19. [35] Aslinda Hassan, Mas Nida Md Khambari, Najwan Khambari, Nurul Azma Za-

in the changing education paradigm: insights from a mixed methods inquiry. Frontiers in Psychology 17 (2026), 1687155. [13] Nicholas Carlini, Florian Tramer, Eric Wallace, Matthew Jagielski, Ariel Herbert-

karia, Taqwan Thamrin, and Wan Mohd Yaakob Wan Bejuri. 2025. Awareness and Misconceptions of AI Among Educators. International Journal of Research and Innovation in Social Science (IJRISS) 9, 11 (2025). [36] Amanda Heidt. 2024. Intellectual property and data privacy: the hidden risks of

Voss, Katherine Lee, Adam Roberts, Tom Brown, Dawn Song, Ulfar Erlingsson,

et al. 2021. Extracting training data from large language models. In 30th USENIX security symposium (USENIX Security 21). 2633–2650. [14] Jake Chanenson, Brandon Sloane, Navaneeth Rajan, Amy Morril, Jason Chee,

AI. Nature (2024). [37] Bo Hui, Haolin Yuan, Neil Gong, Philippe Burlina, and Yinzhi Cao. 2024. Pleak:

Prompt leaking attacks against large language model applications. In Proceed- ings of the 2024 on ACM SIGSAC Conference on Computer and Communications

Danny Yuxing Huang, and Marshini Chetty. 2023. Uncovering privacy and

Conference acronym ’XX, June 03–05, 2018, Woodstock, NY Trovato and Tobin, et al.

Security. 3600–3614. [38] Sangeeta Jadhav, Jayshree Lavhare, Ritik Kumar, Soumyadip Roy, Ankit Kumar

[56] Yupei Liu, Yuqi Jia, Runpeng Geng, Jinyuan Jia, and Neil Zhenqiang Gong. 2024.

Formalizing and benchmarking prompt injection attacks and defenses. In 33rd USENIX Security Symposium (USENIX Security 24). 1831–1847. [57] Rongjun Ma, Caterina Maidhof, Juan Carlos Carrillo, Janne Lindqvist, and

Singh, and Kavya Chauhan. 2025. Edge-AI Multimodal RAG Chat bot with Personalized Knowledge Graph for Offline Privacy-Preserving Information Retrieval. In 2025 5th Asian Conference on Innovation in Technology (ASIANCON). IEEE, 1–4. [39] Hyejun Jeong, Mohammadreza Teymoorianfard, Abhinav Kumar, Amir

Jose Such. 2025. Privacy perceptions of custom gpts by users and creators. In Proceedings of the 2025 CHI Conference on Human Factors in Computing Systems. 1–18. [58] Sebastian Porsdam Mann, Mateo Aboy, Joel Jiehao Seah, Zhicheng Lin, Xufei Luo,

Houmansadr, and Eugene Bagdasarian. 2025. Network-Level Prompt and Trait Leakage in Local Research Agents. arXiv preprint arXiv:2508.20282 (2025). [40] Antonia Karamolegkou, Jiaang Li, Li Zhou, and Anders Søgaard. 2023. Copyright

Daniel Rodger, Hazem Zohny, Timo Minssen, Julian Savulescu, and Brian D Earp. 2025. AI and the Future of Academic Peer Review. arXiv preprint arXiv:2509.14189 (2025). [59] Abigail Marsh and Lauren R Milne. 2025. I Don’t Want to Sound Rude, but It’s

violations and large language models. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing. 7403–7412. [41] Easton Kelso, Ananta Soneji, Syed Zami-Ul-Haque Navid, Yan Shoshitaishvili,

None of Their Business: Exploring Security and Privacy Concerns around As- sistive Technology Use in Educational Settings. ACM Transactions on Accessible Computing 17, 2 (2025), 1–30. [60] Nora McDonald, Sarita Schoenebeck, and Andrea Forte. 2019. Reliability and

Sazzadur Rahaman, and Rakibul Hasan. 2025. Investigating the Security & Privacy Risks from Unsanctioned Technology Use by Educators. In Proceedings of the Extended Abstracts of the CHI Conference on Human Factors in Computing Systems. 1–6. [42] Easton Kelso, Ananta Soneji, Sazzadur Rahaman, Yan Shoshitaishvili, and Rak-

inter-rater reliability in qualitative research: Norms and guidelines for CSCW and HCI practice. Proceedings of the ACM on human-computer interaction 3, CSCW (2019), 1–23. [61] Niloofar Mireshghallah, Maria Antoniak, Yash More, Yejin Choi, and Golnoosh

ibul Hasan. 2024. Trust, Because You Can’t Verify: Privacy and Security Hurdles in Education Technology Acquisition Practices. In Proceedings of the 2024 on ACM SIGSAC Conference on Computer and Communications Security. 1656–1670. [43] Sushmita Khan, Mehtab Iqbal, Oluwafemi Osho, Khushbu Singh, Kyra Derrick,

Farnadi. 2024. Trust No Bot: Discovering Personal Disclosures in Human-LLM Conversations in the Wild. In First Conference on Language Modeling. [62] Kyzyl Monteiro, Yuchen Wu, and Sauvik Das. 2025. Imago Obscura: An Im-

Philip Nelson, Lingyuan Li, Emily Sidnam-Mauch, Nicole Bannister, Kelly Caine, et al. 2024. Teaching middle schoolers about the privacy threats of tracking and pervasive personalization: A classroom intervention using design-based re- search. In Proceedings of the 2024 CHI Conference on Human Factors in Computing Systems. 1–26. [44] Diana Kramer, Lambert Rosique, Ajay Narotam, Elie Bursztein, Patrick Gage

age Privacy AI Co-pilot to Enable Identification and Mitigation of Risks. In Proceedings of the 38th Annual ACM Symposium on User Interface Software and Technology. 1–26. [63] Miryam Naddaf. 2025. AI is transforming peer review—and many scientists are

worried. Nature 639, 8056 (2025), 852–854. [64] Nima Naderloui, Shenao Yan, Binghui Wang, Jie Fu, Wendy Hui Wang, Weiran

Kelley, Kurt Thomas, and Allison Woodruff. 2025. Integrating large language models into security incident response. In Twenty-First Symposium on Usable Privacy and Security (SOUPS 2025). 133–148. [45] Monika Blue Kwapisz, Avanya Kohli, and Prashanth Rajivan. 2024. Privacy

Liu, and Yuan Hong. 2025. Rectifying privacy and efficacy measurements in machine unlearning: A new inference attack perspective. In 34th USENIX Security Symposium (USENIX Security 25). 5545–5564. [65] Bei Yi Ng, Jiarui Li, Xinyuan Tong, Kevin Ye, Gauthami Yenne, Varun Chan-

concerns of student data shared with instructors in an online learning manage- ment system. In Proceedings of the 2024 CHI Conference on Human Factors in Computing Systems. 1–16. [46] Hao-Ping Lee, Yu-Ju Yang, Matthew Bilik, Isadora Krsek, Thomas Serban von

drasekaran, and Jingjie Li. 2025. Analyzing security and privacy chal- lenges in generative ai usage guidelines for higher education. arXiv preprint arXiv:2506.20463 (2025). [66] Andy Nguyen, Yvonne Hong, Belle Dang, and Xiaoshan Huang. 2024. Human-

Davier, Kyzyl Monteiro, Jason Lin, Shivani Agarwal, Jodi Forlizzi, and Sauvik Das. 2026. Privy: Envisioning and Mitigating Privacy Risks for Consumer-facing AI Product Concepts. In Proceedings of the 2026 CHI Conference on Human Factors in Computing Systems. 1–30. [47] Hao-Ping Hank Lee, Lan Gao, Stephanie Yang, Jodi Forlizzi, and Sauvik Das.

AI collaboration patterns in AI-assisted academic writing. Studies in Higher

Education 49, 5 (2024), 847–864. [67] Sanghak Oh, Kiho Lee, Seonhye Park, Doowon Kim, and Hyoungshick Kim.

2024. Poisoned chatgpt finds work for idle hands: Exploring developers’ coding practices with insecure suggestions from poisoned ai models. In 2024 IEEE Symposium on Security and Privacy (SP). IEEE, 1141–1159. [68] Sebastian Porsdam Mann, Anuraag A Vazirani, Mateo Aboy, Brian D Earp, Timo

2024. " I Don’t Know If We’re Doing Good. I Don’t Know If We’re Doing Bad": Investigating How Practitioners Scope, Motivate, and Conduct Privacy Work When Developing {AI} Products. In 33rd USENIX Security Symposium (USENIX Security 24). 4873–4890. [48] Yoonjoo Lee, Hyeonsu B Kang, Matt Latzke, Juho Kim, Jonathan Bragg,

Minssen, I Glenn Cohen, and Julian Savulescu. 2024. Guidelines for ethical use and acknowledgement of large language models in academic writing. Nature Machine Intelligence 6, 11 (2024), 1272–1274. [69] James Prather, Juho Leinonen, Natalie Kiesler, Jamie Gorson Benario, Sam Lau,

Joseph Chee Chang, and Pao Siangliulue. 2024. Paperweaver: Enriching topical paper alerts by contextualizing recommended papers with user-collected pa- pers. In Proceedings of the 2024 CHI Conference on Human Factors in Computing Systems. 1–19. [49] Junyi Li, Jie Chen, Ruiyang Ren, Xiaoxue Cheng, Wayne Xin Zhao, Jian-Yun

Stephen MacNeil, Narges Norouzi, Simone Opel, Vee Pettit, Leo Porter, et al. 2025. Beyond the hype: A comprehensive review of current trends in generative ai research, teaching practices, and tools. 2024 Working Group Reports on Innovation and Technology in Computer Science Education (2025), 300–338. [70] Maxwell Prybylo, Sara Haghighi, Sai Teja Peddinti, and Sepideh Ghanavati.

Nie, and Ji-Rong Wen. 2024. The dawn after the dark: An empirical study on factuality hallucination in large language models. In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). 10879–10899. [50] Qinbin Li, Junyuan Hong, Chulin Xie, Jeffrey Tan, Rachel Xin, Junyi Hou, Xavier

2024. Evaluating privacy perceptions, experience, and behavior of software development teams. In Twentieth Symposium on Usable Privacy and Security (SOUPS 2024). 101–120. [71] Gregory C Rasner. 2021. Cybersecurity and third-party risk: Third party threat

Yin, Zhun Wang, Dan Hendrycks, Zhangyang Wang, et al. 2024. LLM-PBE: Assessing Data Privacy in Large Language Models. Proceedings of the VLDB Endowment 17, 11 (2024), 3201–3214. [51] Tianshi Li, Elizabeth Louie, Laura Dabbish, and Jason I Hong. 2021. How

hunting. John Wiley & Sons. [72] Ankita Priti Roy, Kerena Anand, N Elangovan, and D Halaswamy. 2024. Priori-

tizing Risks in AI-Enabled EdTech Platforms: An Analytic Hierarchy Process Approach. In International Conference on Artificial Intelligence on Textile and Apparel. Springer, 549–564. [73] Rutgers Office for Research. n.d.. Human Research Protection Program Toolkit. https://research.rutgers.edu/faculty-staff/compliance/human-research- protection/toolkit. [Accessed: 2026-04-29]. [74] Rutgers Office for Research. n.d.. Interactive IRB Tools. https://research. rutgers.edu/faculty-staff/compliance/human-research-protection/interactive- irb-tools. Accessed: 2026-04-29. [75] Giles R Scuderi, Michael J Taunton, James A Browne, and Michael A Mont. 2026.

developers talk about personal data and what it means for user privacy: A case study of a developer forum on reddit. Proceedings of the ACM on Human- Computer Interaction 4, CSCW3 (2021), 1–28. [52] Zhuoyang Li, Yanlai Wu, Yao Li, Xinning Gui, and Yuhan Luo. 2026. Privacy

Control in Conversational LLM Platforms: A Walkthrough Study. In Proceedings of the 2026 CHI Conference on Human Factors in Computing Systems. 1–26. [53] Daogao Liu, Edith Cohen, Badih Ghazi, Peter Kairouz, Pritish Kamath, Alexander

Knop, Ravi Kumar, Pasin Manurangsi, Adam Sealfon, Da Yu, et al. 2025. URANIA: Differentially Private Insights into AI Use. In Second Conference on Language Modeling. [54] Lanjing Liu, Xinran Adeline Li, Allen Yilun Lin, and Yaxing Yao. 2026. Designing

The Challenges With Artificial Intelligence in Scientific Writing. The Journal of Arthroplasty 41, 2 (2026), 299–303. [76] Awanthika Senarath and Nalin AG Arachchilage. 2018. Why developers cannot

Privacy Choice in Generative AI Chatbot Ecosystems. In Proceedings of the 2026 CHI Conference on Human Factors in Computing Systems. 1–20. [55] Xiao-Yang Liu, Rongyi Zhu, Daochen Zha, Jiechao Gao, Shan Zhong, Matt White,

embed privacy into software systems? An empirical investigation. In Proceedings of the 22nd International Conference on Evaluation and Assessment in Software Engineering 2018. 211–216. [77] Awanthika Senarath, Marthie Grobler, and Nalin Asanka Gamagedara Arachchi-

and Meikang Qiu. 2025. Differentially private low-rank adaptation of large language model using federated learning. ACM Transactions on Management Information Systems 16, 2 (2025), 1–24.

lage. 2019. Will they use it or not? Investigating software developers’ intention to follow privacy engineering methodologies. ACM Transactions on Privacy and

Investigating Novice Researchers’ Perceptions of Research Privacy Within LLM-Assisted Workflows Conference acronym ’XX, June 03–05, 2018, Woodstock, NY

Security (TOPS) 22, 4 (2019), 1–30. [78] Jatin Shah, Anand Shah, and Ricardo Pietrobon. 2009. Scientific writing of

& Information Technology 38, 7 (2019), 742–759. [99] Honghui Xu, Shiva Shrestha, Wei Chen, Zhiyuan Li, and Zhipeng Cai. 2025.

novice researchers: what difficulties and encouragements do they encounter? Academic Medicine 84, 4 (2009), 511–516. [79] Yashothara Shanmugarasa, Ming Ding, Chamikara Mahawaga Arachchige, and

DP-FedLoRA: Privacy-Enhanced Federated Fine-Tuning for On-Device Large Language Models. arXiv preprint arXiv:2509.09097 (2025). [100] Jiajun Xu, Zhiyuan Li, Wei Chen, Qun Wang, Xin Gao, Qi Cai, and Ziyuan Ling.

Thierry Rakotoarivelo. 2025. Sok: The privacy paradox of large language models: Advancements, privacy risks, and mitigation. In Proceedings of the 20th ACM Asia Conference on Computer and Communications Security. 425–441. [80] Yashothara Shanmugarasa, Shidong Pan, Ming Ding, Dehai Zhao, and Thierry

2024. On-device language models: A comprehensive review. arXiv preprint arXiv:2409.00088 (2024). [101] Biwei Yan, Kun Li, Minghui Xu, Yueyan Dong, Yue Zhang, Zhaochun Ren, and

Xiuzhen Cheng. 2024. On protecting the data privacy of large language models (llms): A survey. In 2024 International Conference on Meta Computing (ICMC). IEEE, 1–12. [102] Tianyi Yang and Rakibul Hasan. 2023. Discovering privacy harms from education

Rakotoarivelo. 2025. Privacy meets explainability: Managing confidential data and transparency policies in llm-empowered science. In Proceedings of the Ex- tended Abstracts of the CHI Conference on Human Factors in Computing Systems. 1–8. [81] Tanusree Sharma, Lin Kyi, Yang Wang, and Asia J Biega. 2024. " I’m not con-

technology by analyzing user reviews. In Proceedings of the 23rd Workshop on Privacy in the Electronic Society. 186–192. [103] Yuting Yang, Zixin Wang, and Florian Schaub. 2025. Privacy Perceptions in the

vinced that they don’t collect more than is necessary":{User-Controlled} Data Minimization Design in Search Engines. In 33rd USENIX Security Symposium (USENIX Security 24). 2797–2812. [82] Jonah Stegman, Patrick J Trottier, Caroline Hillier, Hassan Khan, and Mohammad

Use of ChatGPT Across Different Contexts: A Survey Study of Commercial vs. University-specific Implementations. (2025). [104] Junfei Zhan, Haoxun Shen, Zheng Lin, and Tengjiao He. 2026. PRISM: Privacy-

Mannan. 2023. " My Privacy for their Security": Employees’ Privacy Perspectives and Expectations when using Enterprise Security Software. In 32nd USENIX Security Symposium (USENIX Security 23). 3583–3600. [83] Mohammad Tahaei, Alisa Frik, and Kami Vaniea. 2021. Privacy champions in

Aware Routing for Adaptive Cloud–Edge LLM Inference via Semantic Sketch

Collaboration. In Proceedings of the AAAI Conference on Artificial Intelligence, Vol. 40. 28150–28158. [105] Haoxuan Zhang, Ruochi Li, Yang Zhang, Ting Xiao, Jiangping Chen, Junhua

software teams: Understanding their motivations, strategies, and challenges. In Proceedings of the 2021 CHI conference on human factors in computing systems. 1–15. [84] Henry Tari and Adriana Iamnitchi. 2026. Measuring Privacy vs. Fidelity in

Ding, and Haihua Chen. 2025. The evolving role of large language models in scientific innovation: Evaluator, collaborator, and scientist. arXiv preprint arXiv:2507.11810 (2025). [106] Kaiyuan Zhang, Siyuan Cheng, Hanxi Guo, Yuetian Chen, Zian Su, Shengwei

Synthetic Social Media Datasets. arXiv preprint arXiv:2603.03906 (2026). [85] InternAgent Team, Bo Zhang, Shiyang Feng, Xiangchao Yan, Jiakang Yuan,

An, Yuntao Du, Charles Fleming, Ashish Kundu, Xiangyu Zhang, et al. 2025.

{SOFT}: Selective Data Obfuscation for Protecting {LLM} Fine-tuning against Membership Inference Attacks. In 34th USENIX Security Symposium (USENIX Security 25). 8135–8154. [107] Shuning Zhang, Jingruo Chen, Zhiqi Gao, Jiajing Gao, Xin Yi, and Hewu Li. 2026.

Runmin Ma, Yusong Hu, Zhiyin Yu, Xiaohan He, Songtao Huang, et al. 2025. InternAgent: When Agent Becomes the Scientist–Building Closed-Loop System from Hypothesis to Verification. arXiv preprint arXiv:2505.16938 (2025). [86] Jan Tolsdorf, Alan F Luo, Monica Kodwani, Junho Eum, Mahmood Sharif,

Characterizing Unintended Consequences of GUI Agents For Web Browsing. In Proceedings of the 2026 CHI Conference on Human Factors in Computing Systems. 1–19. [108] Shuning Zhang, Yutong Jiang, Rongjun Ma, Yuting Yang, Mingyao Xu, Zhixin

Michelle L Mazurek, and Adam J Aviv. 2025. Safety Perceptions of Genera- tive {AI} Conversational Agents: Uncovering Perceptual Differences in Trust, Risk, and Fairness. In Twenty-First Symposium on Usable Privacy and Security (SOUPS 2025). 93–112. [87] Sarah Tran, Hongfan Lu, Isaac Slaughter, Bernease Herman, Aayushi Dangol,

Huang, Xin Yi, and Hewu Li. 2026. Privweb: unobtrusive and content-aware privacy protection for web agents. In Proceedings of the 2026 CHI Conference on Human Factors in Computing Systems. 1–29. [109] Shuning Zhang, Zhaoxin Li, Changxi Wen, Ying Ma, Simin Li, Gengrui Zhang,

Yue Fu, Lufei Chen, Biniyam Gebreyohannes, Bill Howe, Alexis Hiniker, et al. 2025. Understanding Privacy Norms Around LLM-Based Chatbots: A Contextual Integrity Perspective. In Proceedings of the AAAI/ACM Conference on AI, Ethics, and Society, Vol. 8. 2522–2534. [88] Vikranth Udandarao and Nipun Misra. 2025. Democratizing AI Development:

Ziyi Zhang, Yibo Meng, Hantao Zhao, Xin Yi, et al. 2025. The Pervasive Blind Spot: Benchmarking VLM Inference Risks on Everyday Personal Videos. arXiv preprint arXiv:2511.02367 (2025). [110] Shuning Zhang, Rongjun Ma, Ying Ma, Shixuan Li, Yiqun Xu, Xin Yi, and Hewu

Local LLM Deployment for India’s Developer Ecosystem in the Era of Tokenized APIs. arXiv preprint arXiv:2508.16684 (2025). [89] University of Oxford. 2025. FAQs for the Policy on Generative AI in Re- search. https://www.ox.ac.uk/research/support/governance-and-committees/ research-policies/policy-for-using-generative-ai-in/faqs. [Accessed: 2026-04- 29]. [90] Jan-Philip Van Acken, Floris Jansen, Slinger Jansen, and Katsiaryna Labunets.

Li. 2025. Understanding Users’ Privacy Perceptions Towards LLM’s RAG-based Memory. In Proceedings of the 2025 Workshop on Human-Centered AI Privacy and Security. 10–19. [111] Shuning Zhang, Ying Ma, Jingruo Chen, Simin Li, Xin Yi, and Hewu Li. 2025.

Towards Aligning Personalized AI Agents with Users’ Privacy Preference. In Proceedings of the 2025 Workshop on Human-Centered AI Privacy and Security. 33–42. [112] Shuning Zhang, Hui Wang, and Xin Yi. 2025. Exploring collaboration patterns

2024. Who is the {IT} Department Anyway: An Evaluative Case Study of Shadow {IT} Mindsets Among Corporate Employees. In Twentieth Symposium on Usable Privacy and Security (SOUPS 2024). 527–545. [91] Eva AM Van Dis, Johan Bollen, Willem Zuidema, Robert Van Rooij, and Claudi L

and strategies in human-ai co-creation through the lens of agency: A scoping review of the top-tier hci literature. Proceedings of the ACM on Human-Computer Interaction 9, 7 (2025), 1–43. [113] Shuning Zhang, Lyumanshan Ye, Xin Yi, Jingyu Tang, Bo Shui, Haobin Xing,

Bockting. 2023. ChatGPT: five priorities for research. Nature 614, 7947 (2023), 224–226. [92] Richard Van Noorden and Jeffrey M Perkel. 2023. AI and science: what 1,600

Pengfei Liu, and Hewu Li. 2024. " Ghost of the past": identifying and resolving privacy leakage from LLM’s memory through proactive user interaction. arXiv preprint arXiv:2410.14931 (2024). [114] Shuning Zhang, Xin Yi, Haobin Xing, Lyumanshan Ye, Yongquan Hu, and Hewu

researchers think. Nature 621, 7980 (2023), 672–675. [93] Cheng-Long Wang, Qi Li, Zihang Xiang, Yinzhi Cao, and Di Wang. 2025. To-

wards lifecycle unlearning commitment management: Measuring sample-level unlearning completeness. In 34th USENIX Security Symposium (USENIX Security 25). 6481–6500. [94] Hanchen Wang, Tianfan Fu, Yuanqi Du, Wenhao Gao, Kexin Huang, Ziming

Li. 2024. Adanonymizer: Interactively Navigating and Balancing the Duality of Privacy and Output Performance in Human-LLM Interaction. arXiv preprint arXiv:2410.15044 (2024). [115] Shuning Zhang, Gengrui Zhang, Yibo Meng, Ziyi Zhang, Hantao Zhao, Xin Yi,

Liu, Payal Chandak, Shengchao Liu, Peter Van Katwyk, Andreea Deac, et al. 2023. Scientific discovery in the age of artificial intelligence. Nature 620, 7972 (2023), 47–60. [95] Roosevelt Wilmot. 2026. Enterprise AI Adoption: Privacy-Driven Barriers, Risk

and Hewu Li. 2025. Through their eyes: User perceptions on sensitive attribute inference of social media videos by visual language models. In Proceedings of the 2025 Workshop on Human-Centered AI Privacy and Security. 20–32. [116] Xinyu Zhang, Huiyu Xu, Zhongjie Ba, Zhibo Wang, Yuan Hong, Jian Liu, Zhan

Trade-Offs, and a Governance Framework. Risk Trade-Offs, and a Governance Framework (February 15, 2026) (2026). [96] Sue Wilson and Jennifer Cutri. 2021. Novice Academic Roles: The Value of

Qin, and Kui Ren. 2024. Privacyasst: Safeguarding user privacy in tool-using large language model agents. IEEE Transactions on Dependable and Secure Computing 21, 6 (2024), 5242–5258. [117] Zhiping Zhang, Michelle Jia, Hao-Ping Lee, Bingsheng Yao, Sauvik Das, Ada

Collegiate, Attendee-Driven Writing Networks. International Journal of Doctoral Studies 16 (2021), 149–170. https://doi.org/10.28945/4700 [97] Yuhao Wu, Evin Jaff, Ke Yang, Ning Zhang, and Umar Iqbal. 2025. An In-Depth

Lerner, Dakuo Wang, and Tianshi Li. 2024. “It’s a Fair Game”, or Is It? Examining How Users Navigate Disclosure Risks and Benefits When Using LLM-Based Conversational Agents. In Proceedings of the 2024 CHI Conference on Human Factors in Computing Systems. 1–26. [118] Guoshenghui Zhao and Eric Song. 2024. Privacy-preserving large language

Investigation of Data Collection in LLM App Ecosystems. In Proceedings of the 2025 ACM Internet Measurement Conference (USA) (IMC ’25). Association for Computing Machinery, New York, NY, USA, 150–170. https://doi.org/10.1145/ 3730567.3732912 [98] Wenjing Xie, Amy Fowler-Dawson, and Anita Tvauri. 2019. Revealing the

models: Mechanisms, applications, and future directions. arXiv preprint arXiv:2412.06113 (2024).

relationship between rational fatalism and the online privacy paradox. Behaviour

Conference acronym ’XX, June 03–05, 2018, Woodstock, NY Trovato and Tobin, et al.

[119] Victoria Zhong, Susan McGregor, and Rachel Greenstadt. 2023. " I’m going to

trust this until it burns me" Parents’ Privacy Concerns and Delegation of Trust in K-8 Educational Technology. In 32nd USENIX Security Symposium (USENIX Security 23). 5073–5090. [120] Jijie Zhou, Eryue Xu, Yaoyao Wu, and Tianshi Li. 2025. Rescriber: Smaller-LLM-

powered user-led data minimization for LLM-based chatbots. In Proceedings of the 2025 CHI Conference on Human Factors in Computing Systems. 1–28.

Investigating Novice Researchers’ Perceptions of Research Privacy Within LLM-Assisted Workflows Conference acronym ’XX, June 03–05, 2018, Woodstock, NY

A Ethical Considerations


## 5. What is your understanding of the data retention policies of

the tools you used? (explain if needed, e.g., do you believe the data
is permanently stored, used for secondary purposes, or deleted)

We acknowledged that our paper has ethical concerns. We adhered to the Menlo report [7] and the Belmont report [10] in mitigating the ethical concerns, and all interviews in our paper acquired the approval of our university’s Institutional Review Board (IRB).


## 6. Are you aware of any built-in privacy controls offered by these

platforms? (If yes: how, if at all, do you use them?)


## 7. How do you perceive the privacy of the research data you

share with these platforms?

Following the principle of Respect for Persons, we obtained in- formed consent from all researchers participating in our interviews. Participants were briefed on the study’s objectives, and retained the right to withdraw or delete their data at any time without any reasons. We prioritized the mitigation of risks associated with the disclosure of sensitive research workflows and potential institu- tional non-compliance. Given that novice researchers often operate within highly competitive research environments, revealing their reliance on commercial LLMs carries inherent professional risks. To protect participants from potential institutional retribution or academic scooping, we rigorously anonymized all PIIs, detailed research topics, and proprietary methodologies. Furthermore, we highlighted that the observed practices and perceptions originate from multiple constraints rather than individual negligence, under- scoring the need for multi-stakeholder interventions to mitigate these risks.


## 8. Are there specific categories of research data or tasks you

withhold from AI platforms? If so, what are they and why?

9. Where do your privacy perceptions originate?

B.3 Specific Experience Exploration

10. Could you share a specific instance where you felt the privacy risk was highest, or that left the deepest impressions on you?

11. (If applicable) What exactly happened? (What did you input? What was the AI’s response?)

12. (If applicable) Why did it feel “risky” at that moment? 13. (If applicable) How did you handle it afterward? (Deleted the chat? Took remedial actions?)

14. (If applicable) Did this experience change how you use AI later on?

15. How do you perceive the risks that your inputs might be used to train the model, potentially leaking your research ideas to other users?

To uphold the principles of Beneficence and minimize risks asso- ciated with the exposure of sensitive data, we strictly anonymized all PII and sensitive research workflows shared by the participants.

16. When using AI for peer review, how do you perceive that AIs might identify the author or leak your identity as a reviewer?

Furthermore, because our interview explicitly investigates the acceptability of inputting research ideas into LLMs, we applied the Menlo Report’s guidelines, regarding responsible data management in information communication technology research. Consequently, to prevent any potential reverse-engineering or exploitation of our participants’ specific research privacy vulnerabilities, we deliber- ately chose not to open-source the original interview transcripts. This decision ensures that we protect the participants’ professional safety and intellectual property while still sharing our interview questions and codebooks to facilitate reproducibility.

17. Does the geographical origin (e.g., domestic vs. international) affect your trust in these tools? Why?

B.4 Coping Strategies

18. What strategies,if any, do you employ to protect research data before or during interaction with LLM-assisted tools?

19. How would you perceive the privacy communication of LLM- assisted tools (e.g., privacy policy)?

B.5 Suggestions & Expectations

B Interview Scripts

20. If you could design a chatbot specifically for researchers, what privacy features would it have?

The following is the interview scripts. We used Chinese or English to interview participants according to participants’ preference. A primary author who is fluent in both English and Chinese translated the script to Chinese, and the other authors checked the interview script to ensure its correctness.

21. Who do you believe should bear the primary responsibility for safeguarding research data?

22. Is there anything else regarding LLM-assisted research and privacy that you want to share?

C Codebook

B.1 Basic Usage Experience

Drawing upon the thematic analysis, we developed a codebook to systematically analyze novice researchers’ concerns regarding LLM-based research assistants. Table 3 presents the finalized code- book, structured by themes, corresponding codes, and operational descriptions.


## 1. Which generative AI tools or LLMs do you primarily use in your

research flow?


## 2. Could you describe your primary use cases for these tools?

(prompt if needed, e.g., data analysis, drafting, coding)


## 3. How do you typically input your data into these systems?

(prompt id needed, e.g., direct text entry, file uploads) What drives
this preference?

B.2 Privacy Perceptions & Concerns


## 4. What do you believe happens to your data after you submit a

prompt. Where does the input go, and how is it processed?

Conference acronym ’XX, June 03–05, 2018, Woodstock, NY Trovato and Tobin, et al.


> **Table 3: Codebook of researchers’ privacy concerns, mitigation and challenges.**

Theme Code Description

Opacity & complexity Perception of LLM data pipelines as intransparent, hindering re- searchers’ ability to understand backend storage mechanisms. Unavoidable knowledge leakage The fatalistic assumption that interacting with cloud-based models inevitably results in the exposure of submitted proprietary data. Iterative optimization The belief that user prompts and proprietary data are used to contin- uously train and refine the underlying models. Obfuscation by AIs The perception that AI platforms deliberately mask their data har- vesting practices through convoluted interfaces and vague policy language.

Understanding of LLM Data Handling

Information categories that matter Differentiation of risk severity based on data types, with strict con- cerns on unpublished manuscripts and raw datasets. Unauthorized disclosure of intellectual property

Anxiety over the exposure of novel hypotheses and core research ideas to competing users or the public. Empirical data exposure Fears concerning the leakage of primary datasets, including sensitive human-subject information or proprietary experimental metrics. Deanonymization and profiling Risks of models aggregating query histories to infer researchers’ identities, institutional affiliations, or distinct behavioral profiles. Memorization and data deletion Apprehensions that LLMs permanently retain inputs in their weights, rendering user-initiated data deletion requests ineffective. Security vulnerabilities Concerns regarding centralized data breaches or unauthorized access by third-party actors exploiting AI platform weaknesses. Negligible risks Users perceive the utility of the LLM to outweigh the potential privacy implications. Research vs. daily privacy risks The contextual distinction between the rigorous safeguarding of high- stakes academic assets versus relaxed attitudes toward routine, non- sensitive interactions.

Perceived Privacy Risks

Privacy mental models shaped by university guidelines, ethical com- pliance training, and official organizational policies. Empirical engagement and experiential discovery

Formal pedagogical and institutional instruction

Knowledge Sources

Understanding derived from direct, hands-on interaction with LLMs and longitudinal observation of their output behaviors. Peer-mediated and collaborative discourse

Informal discussions, shared workflows, and warnings among aca- demic colleagues. Scholars and medias Published security research, expert commentary, and public media reports.

Using localized, offline models or enterprise-tier accounts to ensure data and access boundaries. Data sanitation and obfuscation Manually redacting identifiable metrics, substituting sensitive termi- nology, or applying masking techniques prior to input. Fragmentation and decoupled processing

Architectural isolation and access control

Privacy Protection Practices

Deconstructing complex queries into disjointed, context-free seg- ments to prevent the model from comprehending the holistic idea. Adversarial testing, probing and deletion

Actively testing the model’s memorization limits and routinely purg- ing chat histories to minimize persistent exposure windows. Human-centric verification and awareness

Maintaining vigilant oversight of AI outputs and cross-referencing generated content to detect potential privacy anomalies. Ineffectiveness of current mitigation

The recognition that existing user-side privacy strategies are often insufficient.

Privacy-publication trade-off Tension between utilizing AI to accelerate publication and risk of exposing novel findings. Intransparency and informational asymmetry

Challenges

The imbalance of knowledge where AI providers conceal data prac- tices and retention policies from user. Lack of control Absence of mechanisms for users to actively manage, restrict, or revoke access to their submitted data. Accountability deficit Difficulty in assigning liability or tracing when research is inadver- tently leaked.

Investigating Novice Researchers’ Perceptions of Research Privacy Within LLM-Assisted Workflows Conference acronym ’XX, June 03–05, 2018, Woodstock, NY

D Participants’ Demographics


> **Table 4 showed the participants demographics.**


> **Table 4: Participants’ demographics. For position, if the participants are currently pursuing PhD or master, we denoted PhD or**

> master, or if they already became faculties or are currently research assistants, we denoted correspondingly.

ID Age Gender Channel Position Nationality Country of Current Study Research direction 1 27 F WeChat PhD Mainland China Mainland China Architecture 2 22 F WeChat PhD Mainland China Mainland China Life Sciences 3 23 F Contact Master Mainland China Mainland China Human-Computer Interaction 4 31 F WeChat PhD Mainland China Mainland China Business Administration 5 28 F WeChat PhD Mainland China Mainland China Biological Science, Bioengineering 6 30 M RedBook PhD Mainland China Mainland China Information Management 7 25 F RedBook PhD Mainland China Netherlands Sociology 8 28 M RedBook PhD Mainland China UK Computational Social Science 9 24 F RedBook PhD Mainland China USA Human-Computer Interaction 10 25 F RedBook Master Mainland China USA Materials Science 11 23 F RedBook Master Mainland China Hong Kong Literature 12 26 F RedBook PhD Mainland China Canada Finance and Economics 13 27 F RedBook PhD Mainland China Netherlands Psychology 14 25 M RedBook Master Mainland China UK Artificial Intelligence 15 26 F RedBook PhD Mainland China USA Educational Psychology 16 30 F RedBook Professor Mainland China Mainland China Toxicology 17 22 M RedBook Master Mainland China USA Statistics 18 25 M RedBook PhD Mainland China Germany Linguistics 19 26 F RedBook PhD Mainland China USA Psycholinguistics 20 25 F RedBook PhD Mainland China USA Economics and Management 21 25 M RedBook PhD Mainland China USA Mechanical Engineering 22 28 M RedBook Postdoc/Faculty Mainland China Mainland China Social Sciences 23 29 F RedBook PhD Mainland China Mainland China Humanities and Social Sciences 24 28 F LinkedIn PhD Sri Lanka Australia HCI 25 28 M RedBook PhD Mainland China Germany Law 26 28 M RedBook PhD Mainland China Mainland China Public Administration 27 26 M RedBook PhD Mainland China Mainland China Education 28 27 F RedBook PhD Mainland China UK Education 29 28 M RedBook Corporate Re- searcher

Mainland China USA Biological Sequencing

30 25 F RedBook PhD Mainland China USA Media Arts 31 26 F Campus PhD Malaysia Mainland China Medical Image Processing 32 37 F Campus PhD India Mainland China Chinese Linguistics 33 38 M LinkedIn Lecturer Indonesia Indonesia Human-Computer Interaction 34 24 F Campus PhD Ghana Mainland China Chinese Literature 35 28 F Campus Master Bangladesh Mainland China Teaching Chinese to Speakers of Other Languages 36 27 M Campus PhD Mainland China Finland Auditing 37 24 M Campus Master Pakistan Mainland China Chinese Education 38 23 M WeChat PhD Singapore Singapore Chinese Language 39 31 F Campus Master Malaysia Mainland China Linguistics 40 28 F Campus Master Sri Lanka Mainland China Economics and Management 41 27 F Campus Master/RA Pakistan Mainland China Artificial Intelligence 42 28 M Campus PhD Pakistan Mainland China AI-driven Origami Structures 43 23 M Campus Master Uzbekistan Mainland China Chinese Language 44 27 F Campus Master Indonesia Mainland China Teaching Chinese as a Second Lan- guage
