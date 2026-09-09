---
workspace_id: "SCI-000019"
doi: "10.21203/rs.3.rs-10090015/v1"
title: "From Generative AI to Agentic AI in Higher Education: A Structured Literature Synthesis of Instructional, Human Agency, and Governance Tensions"
year: 2026
extraction_engine: "pymupdf"
---
# 2026 Nirban From Generative AI to Agentic AI in Higher Educati

From Generative AI to Agentic AI in Higher Education: A Structured Literature Synthesis of Instructional, Human Agency, and Governance Tensions

Harshvardhan Singh Nirban

Birla Institute of Technology and Science, Pilani

Ritika Bhatia

Manipal University Jaipur

Bhaskar Mangal

Birla Institute of Technology and Science, Pilani

Ashutosh Bhatia

Birla Institute of Technology and Science, Pilani

Systematic Review

Keywords: Agentic AI, generative AI, higher education, AI agents, adaptive learning, instructional validity, human agency, cognitive offloading, academic integrity, AI governance

Posted Date: July 7th, 2026

DOI: https://doi.org/10.21203/rs.3.rs-10090015/v1

License:   This work is licensed under a Creative Commons Attribution 4.0 International License.   Read Full License

Additional Declarations: No competing interests reported.

From Generative AI to Agentic AI in Higher Education: A Structured Literature Synthesis of

Instructional, Human Agency, and Governance

Tensions

Harshvardhan Singh Nirban1 , Ritika Bhatia2∗,

Bhaskar Mangal1 , Ashutosh Bhatia1

1Generative AI Research (GAIR) Lab, Department of CSIS, BITS Pilani,

Pilani Campus, Rajasthan, India

2TAPMI School of Business, Manipal University Jaipur, Jaipur, Rajasthan, India

p20230097@pilani.bits-pilani.ac.in

ritika.bhatia@jaipur.manipal.edu

p20210473@pilani.bits-pilani.ac.in

ashutosh.bhatiap@pilani.bits-pilani.ac.in


## Abstract

Generative artiﬁcial intelligence (GenAI) tools have rapidly emerged in higher education as ready-to-use supports for writing, feedback/tutoring, coding, assessment, and academic decision-making. An accelerating shift from these reactive, prompt-driven GenAI tools to proactive, autonomous (or agentic) AI systems represents a qualitatively new challenge for universities. Agentic AI can autonomously plan, coordinate, personalize, retrieve, recommend, assess and otherwise act in institutional workﬂows. This soon-to-be ubiquitous capability shifts artiﬁcial intelligence from a classroom-support tool into a distributed actor in the higher education ecosystem. Highly relevant literature exists on topics including, but not limited to, AI agents, adaptive learning, self-directed learning, educational assessment, cognitive oﬄoading, teacher agency, student agency, academic integrity, educational governance/administration, AI ethics, dataﬁcation, and educational technology security risks. However, these literatures remain fragmented and is currently studied in relative isolation from one another. With an initial resource pool of 77 bibliographic citations, this paper provides a structured narrative review and framework-oriented synthesis, updated through duplicate checking, relevance screening, and framework ﬁt, resulting in a ﬁnal analytical corpus of 65 papers. Authors highlight how the GenAI-to-transition tensions are being applied to higher education across four lenses: 1) A shift from conceptualizing AI as reactive/use-speciﬁc tool into distributed educational actor, 2) Emerging necessity to link AI-powered personalization with evidence of instructional validity/integrity of assessments; 3) AI’s simultaneous facilitation of learner autonomy and enablement of cognitive oﬄoading/learniﬁcation dependence, and 4) Expansion of AI risk/failure surface from siloed, output-level vulnerabilities into entire-ecosystem liability/governance gaps. We use these tensions to develop AIRA-G, a descriptive and actionable Agentic AI Institutional Readiness and Accountability-Governance Framework for higher education stakeholders to

1

translate into four diagnostic lenses, three autonomy-risk zones, and multi-level governance responses to inform institutional decision-making. This study clariﬁes how Agentic AI presents a speciﬁcally educational challenge, integrates otherwise disparate literatures, and oﬀers educators a practical starting point for thinking through agentic systems prior to their adoption at scale.

Keywords: Agentic AI, generative AI, higher education, AI agents, adaptive learning, instruc- tional validity, human agency, cognitive oﬄoading, academic integrity, AI governance

1 Introduction

Generative artiﬁcial intelligence (GenAI) technology has recently transitioned from experimental uses to mainstream relevance for higher education. Zawacki-Richter et al. [77] provide an overview of artiﬁcial intelligence (AI) in higher education, building upon prior calls for AI as education to incorporate AI as a curricular, ethical, and interdisciplinary consideration rather than solely a technical one [18]. Recent review articles discuss GenAI speciﬁcally and AI more generally as used in education across writing support, student tutoring, code generation, automated feedback, assessment design, learning analytics, student counseling and advising, academic advising, and subject-speciﬁc research assistance [29, 82, 76]. For instance, Bearman and Luckin [11] center assessment redesign for an era with AI while other researchers consider access, academic integrity, student adoption, and faculty preparedness [81, 33]. These initial phases of AI in higher education are typiﬁed by reactive AI tools that generate text, explanations/answers, summaries, or code in response to user prompts. A second phase is emerging that will also require universities to address challenges related to academic literacies, human–machine interaction norms, and philosophical questions about the meaning of artiﬁcial agency within learning systems [49, 66, 67]. Speciﬁcally, Kremantzis et al. [40] discuss how AI is moving beyond the current generation of prompt dependent tools into agentic AI systems, while complementary research introduces agentic workﬂows and suggests directions for future educational applications of agentic AI [35, 39].

Sapkota et al. [59] diﬀerentiate AI agents from agentic AI, further Goyal [26] provides a review of agentic AI including core technologies, opportunities, applications, ethical considerations, and opportunities for future research. In regards to education, English [20] explore AI used for tutoring and as teaching assistants. Outside of these categories, previous research details adaptive learning agents and academic advising agents. Literature also discusses learning analytics agents, intelligent campus knowledge interfaces, and human-centered AI learning frameworks. Newer research studies focus on agentic retrieval-augmented generation (RAG) AI systems integrated into learning management systems [9, 32, 69, 80].

The adoption of agentic AI into higher education is signiﬁcant because it changes how AI is used within higher education. Reactive GenAI tools are used primarily as initiated support tool by users. Agentic AI is diﬀerent because it can operate as a partial agent within educational activities. It can break down a goal into muntiple steps and invoke tools to complete each sub-goal, retrieve knowledge from institutional sources, adjust learning pathways, manage feedback, and integrate into decision-making processes to accomplish the assigned task. AI acting as a partial agent in these ways can aﬀect academic integrity at the core of higher education and create tensions. The problem is no longer if students or teachers use AI, but how should universities evaluate AI systems which begin to autonomously take part in teaching, learning, assessment, advising, and university support processes.

2

Agentic AI introduces new tensions that higher education institutions are not currently organized to address. Prior technological shifts in higher education allowed universities to focus on topics like tool usage guidelines, plagiarism implications, assessment design, or technology acceptable use policies. Agentic AI raises new considerations about autonomy, instructional validity, learner and teacher agency, and institutional risks. Apoki et al. [5] discussed relevant work on adaptive learning which details personalized education. With AI added to education, there is risk of student overreliance which could hurt critical thinking skills. Lepage and Collin [43] discuss how learners and teachers should stay engaged with decision-making when using AI. On an institutional level, Williamson et al. [70] discusses dataﬁcation of teaching in higher education. Another study investigates risks that come with using increasingly agentic algorithmic systems [13]. Because of these changes, universities should examine themselves by asking questions about ethical AI use.

• What level of AI autonomy is acceptable for academic processes?

• How do we ensure that AI personalized learning pathways remain aligned with learning objectives, academic standards, and assessment fairness?

• Does AI support enhance or hinder learner and teacher agency?

• How can universities protect student and faculty data if we allow AI systems to access course materials, student information, institutional knowledge banks, or assessment activities and results?

These questions become increasingly important as beneﬁts of agentic AI such as personalization, scalability, responsiveness, and eﬃciency may also present risks to higher education including cognitive oﬄoading, overdependence, decreased productive struggle, loss of transparency in decision-making, privacy infringements, bias, prompt injection attacks, and loss of accountability [68, 31, 17, 42].

There are numerous existing research articles that provide useful background on these questions. One line of research investigates AI agents, intelligent tutoring systems, and agentic methods in education [72, 73, 39]. Another stream of research explores adaptive learning and person- alized education. For example, Apoki et al. [5] review how pedagogical agents are used for adaptive personalized learning. Related articles discuss AI powered learning assistants and learning analytics [57, 3, 28]. A third research area discusses self-directed learning, learner autonomy, artiﬁcial intelligence competency, student motivation, and learner engagement. One study speciﬁcally looks at agentic AI for self-eﬃcacy, autonomy support, and self-learning motivation [4]. Other research explores AI and self-directed learning, AI competency, and AI autonomy [65, 16, 54]. Lastly, a fourth body of literature focuses on education assessment. Work discusses constructive alignment, portfolio assessment, use of AI as a rubric, academic integrity, and validity of digitally supported assessments. Bearman and Luckin [11] help establish context for how learning assessments operate in digital learning environments. Later research builds on this work by discussing AI rubric graded assessment and GenAI supported portfolio assignments. Another article looks at how constructive alignment applies when AI is integrated into the assessment process [7, 55, 63]. Other related bodies of research review teacher agency and student agency, dataﬁcation of education, sociotechnical changes, ethical AI use, governance of AI in education, and AI security considerations [43, 70, 12, 45, 25]. Although these studies contribute to the overall discussion of AI in education, individually they do not provide a structured view of how agentic AI will impact higher education. Speciﬁcally, additional research is needed to understand how agentic AI will impact the relationship between instructional design, human agency, and university governance.

3

We focus on this problem because universities have already received general AI guidance from

researchers and news articles. Colleges need practical advice for how AI speciﬁcally introduces tensions into learning design, pedagogy, student development, and university governance. AI personalization, for instance, is often described as a beneﬁt of AI in education. However, automated personalization is not ideal for learning if it is not pedagogically aligned with course objectives, assessment standards, disciplinary expectations, or positive cognitive engagement [21, 58, 55]. Similarly, AI could potentially assist students with becoming self-directed learners and support autonomy, but AI assistance could just as easily lead to cognitive oﬄoading if learners use AI to avoid thinking critically, reﬂecting on concepts, or verifying accuracy. Wang and Zhang [68] look at how GenAI can create pedagogical partnerships within education focusing on transformative learning and cognitive awareness. Another article reviews how use of GenAI creates a shared metacognition and leads to cognitive oﬄoading by students Iqbal et al. [31]. Related research makes the connection between GAI assisted learning activities and behavioral constructs along with learning outcomes [78]. At the institutional level, education is framed through dataﬁcation by Williamson et al. [70]. Complementary work suggests that agentic AI introduces new tensions by shifting risks from output-level consequences (e.g. faulty AI explanations) to system-level concerns about security, accountability, governance, and trust [13, 17, 42].

To respond to this issue, our study leverages the structured narrative review and framework- oriented synthesis methods to investigate how GenAI can lead to agentic AI in higher education. Speciﬁcally, our review integrates literature related to GenAI, agentic AI, AI agents, adaptive and personalized learning, self-directed learning, assessment in education, cognitive oﬄoading, teacher agency and student agency, AI governance, dataﬁcation of education, and AI security concerns. Instead of discussing diﬀerent literature streams separately, our study presents four interconnected framework-driving tensions illustrated in Figure: 1. The ﬁrst tension discusses the shift from AI’s reactive role to its proactive role as an educational actor. The second tension centers around bridging AI-powered personalization with instructional validity and assessment integrity. The third tension underscores AI’s dual capability to empower human agency and amplify cognitive and professional dependency. The fourth tension expands AI-associated risks from micro-level tool-use vulnerabilities to macro-level ecosystem governance weaknesses.

Accordingly, the review is guided by the following research questions:

RQ1: How does the transition from GenAI to Agentic AI change the role of AI in higher

education?

RQ2: What instructional, human-agency, and governance tensions emerge when AI systems

become personalized, proactive, and institutionally embedded?

RQ3: How can these tensions inform the development of a practical university-facing framework

for evaluating Agentic AI adoption?

This paper makes three contributions. First, it clariﬁes the educational signiﬁcance of the shift from reactive GenAI tools to proactive agentic AI systems. This distinction is important because agentic AI alters not only the functionality of educational technologies, but also the distribution of agency across students, teachers, AI systems, curricula, and institutions. Second, it synthesizes fragmented literature into four actionable tensions concerning AI autonomy, instructional validity, human agency, and governance vulnerability. This synthesis provides a focused alternative to broad beneﬁt-risk reviews by identifying the speciﬁc issues universities

4


> **Figure 1: Interrelated Tensions in AI-Enabled Education**

must evaluate before deploying agentic AI at scale. Third, it establishes the conceptual foundation for a university-facing readiness and risk-governance framework that can help stakeholders assess whether agentic AI systems are pedagogically valid, agency-preserving, secure, accountable, and institutionally appropriate.

To preclude ambiguity in the synthesis that follows and framework development, the paper provides working deﬁnitions of key constructs employed throughout the review. Table 1 lists the working deﬁnitions and operational indicators of the constructs included in this paper. These deﬁnitions do not aim to deﬁnitively establish terminology in a quickly-moving ﬁeld; these deﬁnitions aim to provide conceptual and operational clarity for the purposes of this review and resulting AIRA-G Framework.

The deﬁnitions in Table 1 guide the subsequent synthesis. In particular, they clarify why the paper treats agentic AI not merely as a more capable version of GenAI, but as a class of systems that can redistribute educational agency, alter assessment evidence, and create new institutional governance obligations. The remainder of the paper is organized as follows. Section 2 describes the structured narrative review and framework-oriented synthesis methodology. Section 3 presents an overview of the review corpus and its thematic coverage. Section 4 reports and discusses the synthesis results across the four identiﬁed tensions and explains how they motivate the development of a practical agentic AI readiness and risk-governance framework.

5


> **Table 1: Operational deﬁnitions of core constructs used in the review**

Construct Working deﬁnition in this paper Operational indicators

Agentic AI AI systems that can pursue user- or institution-deﬁned goals across multiple steps by planning, retrieving information, using tools, adapting to context, or initiating bounded actions within educational or administrative workﬂows.

Multi-step planning; tool use; contextual adaptation; workﬂow participation; bounded autonomy; action initiation or recommendation.

AI agent A speciﬁc software entity within an agentic AI system that performs a deﬁned role, such as tutoring, recommending, retrieving, monitoring, reasoning, or coordinating tasks.

Role-speciﬁc function; deﬁned input–output boundary; interaction with users, tools, data sources, or other agents.

Instructional validity The extent to which AI-supported learning activities, feedback, personalization, and assessment remain aligned with intended learning outcomes, disciplinary standards, and valid evidence of student competence.

Outcome alignment; constructive alignment; preservation of intended cognitive work; feedback relevance; assessment evidence; faculty inspectability.

Assessment integrity The extent to which assessment processes continue to provide trustworthy evidence of what students know, understand, and can independently do when AI assistance is available.

Authorship clarity; AI-use disclosure; task authenticity; independent veriﬁcation; viva/code walkthrough; process evidence.

Calibrated human–AI agency

A mode of AI use in which students and faculty strategically use AI support while retaining responsibility for reasoning, veriﬁcation, judgement, reﬂection, and ﬁnal academic decisions.

Veriﬁcation behaviour; metacognitive reﬂection; human approval; AI-use explanation; balanced on-AI/oﬀ-AI task design; resistance to blind reliance.

Governance vulnerability Institutional exposure created when AI systems interact with educational data, platforms, workﬂows, or decisions in ways that may generate privacy, security, bias, auditability, accountability, or trust risks.

Sensitive data access; weak audit logs; prompt-injection exposure; unclear accountability; biased recommendations; limited appeal or contestability.

Risk–readiness zone A classiﬁcation of an agentic AI use case based on the level of educational consequence, autonomy, data access, and institutional capacity to govern the system.

Low-risk assistive use; guided adoption; controlled pilot; restricted/not-ready deployment.

Note. These deﬁnitions guide the coding, synthesis, and operationalization of the AIRA-G Framework. They are intended as working deﬁnitions for higher-education contexts rather than universal deﬁnitions of AI systems.

2 Research Methodology

This paper follows a structured narrative review and framework-oriented synthesis methodology. The decision to take this approach was driven by the relative diversity and rapid expansion of literature on GenAI and agentic AI in higher education. Research in this area spans numerous lines of inquiry, often focusing on distinct facets of AI in education. Relevant studies can be found in the broader literature focused on AI in education, educational assessment, adaptive learning, human–AI interaction, learning analytics, as well as exploratory work in academic integrity, AI governance, sociotechnical/systems integration, and AI security. With this in mind, our review required an integrative approach that could consolidate insights from across these research traditions in order to establish an aligned understanding of the space. Meta-analysis was unsuitable for this eﬀort as the studies covered in our review do not measure a single intervention, outcome variable, or loosely comparable eﬀect size. Rather, this review synthesizes conceptual, empirical, review-oriented, technical, and governance literature with the goal of deﬁning salient tensions to consider during university-level evaluation of agentic AI.

Rather than taking the form of a general descriptive review, this review was intended to serve as a framework-oriented synthesis of literature. While descriptive reviews are useful for summarizing what we know about a topic of research, framework syntheses aim to extract and deﬁne the ongoing conceptual debates embedded in a research space. This approach was selected because AI in HE is an emerging domain which has generated suﬃcient literature for synthesis and knowledge development, but not enough for the literature to converge on a single explanatory

6

theory or standardised model of evaluation. For this reason, this review synthesizes available literature with the intention of developing a practical readiness/risk governance framework to support university decision-makers.

2.1 Corpus Identiﬁcation and Selection

The review corpus was compiled iteratively using methods of targeted searching, relevance screening, metadata annotation, and theme saturation. Papers focusing on GenAI in higher ed, agentic AI, AI agents, adaptive/personalized learning, self-directed learning and AI, assessment redesign, teacher agency or student agency, academic integrity, AI governance, dataﬁcation, AI-related security vulnerabilities were included to form the initial corpus. Other papers were included to expand and ﬁll conceptual holes that became apparent in the developing thematic schema, such as instructional validity, cognitive oﬄoading, prompt injection, sociotechnical framing of AI governance issues, and security vulnerabilities in AI governance. Searches were conducted using combinations of terms such as “generative AI in higher education”, “agentic AI in education”, “AI agents in education”, “adaptive learning”, “personalized learning”, “self- directed learning and AI”, “AI and assessment validity”, “generative AI and academic integrity”, “cognitive oﬄoading and GenAI”, “teacher agency and AI”, “learning analytics ethics”, “AI

governance in higher education”, “prompt injection”, “RAG security”, and “sociotechnical systems and AI governance”. Searches were supplemented by citation chaining and selective inclusion of review papers, conceptual papers, and technical papers that aided conceptual clarity. Following deduplication, the enriched bibliography contained 65 bibliographic entries representing approximately 76 unique papers. Articles included were peer-reviewed journal articles, conference papers, review articles, conceptual pieces, technical reports, and selected works that took a policy- or governance-leaning approach to topics relevant to the review. Heterogenous source types were included because the topic of agentic AI in higher education is itself multidisciplinary: emergent GenAI technology inﬂuences not just pedagogical practices, but also institutional infrastructure, human agency, assessment integrity, technical security, data governance, and accountability procedures. To maintain transparency throughout corpus creation, we screened papers against explicit inclusion and exclusion criteria. Criteria were intentionally kept broad in areas where relevant literature may exist outside of our central focus on the GenAI to Agentic- AI transition in higher education, such as AI governance, security, and sociotechnical systems. Table 2 provides these.


> **Table 2: Inclusion and exclusion criteria used for corpus selection**

Criterion Included Excluded

Topical focus GenAI, agentic AI, AI agents, adaptive learning, assessment, human agency, AI governance, dataﬁcation, and AI security in education

General AI papers without relevance to education, agency, learning, governance, or institutional risk

Educational relevance Studies linked to higher education, teaching, learning, assessment, student support, faculty work, or educational governance

Papers focused only on unrelated domains such as medical diagnosis, autonomous vehicles, robotics, blockchain, or smart contracts

Conceptual relevance Papers contributing to AI autonomy, instructional validity, human agency, cognitive engagement, or governance vulnerability

Papers oﬀering only generic claims about AI without conceptual or practical relevance to the review objective

Publication type Empirical studies, review articles, conceptual papers, technical papers, and governance-oriented studies

Non-scholarly or unrelated materials not contributing to the synthesis

Note. The screening prioritized conceptual relevance to the GenAI-to-agentic-AI transition in higher education rather than disciplinary narrowness.

7

2.2 Inclusion and Exclusion Criteria

Papers were included if they directly discussed one or more of the following topics: GenAI use in higher education; agentic AI or AI agents more generally; intelligent tutoring sys- tems; adaptive/personalized learning; self-directed learning; learner/student agency/selves- direction; faculty/teacher agency; instructional design or education assessment; academic integrity tools/solutions; cognitive oﬄoading; learning analytics/dataﬁcation; AI ethics; AI governance; sociotechnical AI adoption processes; prompt injection attacks; multi-agent system security; or institutional risk from AI.

Papers were excluded if their primary focus fell outside of higher education and made no meaningful contribution to knowledge of agentic AI adoption. Papers were excluded if they discussed medical/AI applications, robotics, self-driving cars, blockchain technology or smart contracts, or general-purpose AI use that did not link back to education, learning, assessment, agency, AI governance, or institutional risk. Papers were excluded if relevance to this review was limited to broad, non-committal statements about artiﬁcial intelligence with little or no conceptual or applied value for understanding the transition from GenAI to agentic AI in universities.

The screening process therefore excluded papers by virtue of disciplinary siloing. Papers focused exclusively on education and higher education made up the majority of papers in our corpus. We did, however, keep certain papers outside of education if they discussed agentic systems, prompt injection, AI governance, human agency, or sociotechnical risk in education-speciﬁc contexts.

2.3 Coding Strategy

The synthesis followed a deductive-inductive coding process. Deductively, papers were ﬁrst mapped to four framework-oriented dimensions derived from the purpose of the study and the emerging literature gap. These dimensions were:

D1. Agency transition and AI autonomy: papers addressing the shift from reactive AI tools

to proactive, agentic, semi-autonomous, or workﬂow-participating AI systems.

D2. Instructional validity and learning design: papers addressing adaptive learning,

personalization, assessment validity, constructive alignment, feedback, learning outcomes, and pedagogically meaningful use of AI.

D3. Human agency and cognitive engagement: papers addressing learner autonomy, self-

directed learning, teacher agency, metacognition, cognitive oﬄoading, overreliance, and human judgment.

D4. Governance vulnerability and institutional risk: papers addressing ethics, academic

integrity, dataﬁcation, privacy, bias, prompt injection, security, accountability, auditability, and institutional governance.

Inductively, frequent subthemes were identiﬁed within and across the four dimensions by skimming titles, abstracts, keywords, and bibliographic metadata. These included agentic workﬂows, AI tutors, adaptive learning paths, personalized feedback, AI-enabled assessment, rubric-based scoring, portfolio-based assessment, self-eﬃcacy, autonomy support, cognitive watchfulness, cognitive load reduction, teacher workload, teacher agency, dataﬁcation, prompt injection attacks, campus knowledge bases, auditability, and governance readiness.

Each paper was given a primary dimension and, when relevant, one or two secondary dimensions. Doing so was crucial because several papers spanned multiple dimensions conceptually. For instance, a paper on AI-enabled assessment could impact instructional validity, human agency,

8

and governance vulnerability. A paper on campus knowledge bases could speak to agency anxiety/institutional risk and governance readiness. The mapping therefore conceptualized the four dimensions as overlapping lenses rather than distinct buckets.

2.4 Framework-Oriented Synthesis Procedure

The synthesis was completed in ﬁve phases. Initially, papers were screened at title-abstract level for relevance to the scope of this study. Bibliographic records were then annotated and cleaned in Second phase to facilitate consistent citation and author-year referencing in the report. Third, each paper was qualitatively mapped to the four deductive dimensions introduced above. Fourth, inductive subthemes were coded within each dimension to extract commonalities, conceptual overlaps, and open points of tension. Fifth, cross-theme commonalities were thematically synthesized into four higher-level tensions that organize the ﬁndings of this review.

The four synthesized tensions were not applied deductively. Instead, each tension emerged from an inductive process of repeatedly comparing papers against the mapped literature. For example, papers contributing to the theme of AI agents and agentic workﬂows described a shift from AI-as-tool to AI-as-partner; similarly, papers that focused on adaptive learning, personalized feedback, and assessment described personalization as an unstated objective rather than suﬃcient guarantee of instructional validity, assessment integrity, or deep learning. The broad theme of self-directed learning, autonomy, metacognition, teacher agency, and cognitive oﬄoading was concerned with AI as a scaﬀold for human agency and intentionality, but also as a potential source of dependency. The theme of ethics, dataﬁcation, prompt injection, learning analytics, academic integrity, and institutional governance was concerned with how agentic AI transformed local risks (errors at the level of student outputs) to systemic risks (vulnerabilities at the level of the entire AI-mediated educational ecosystem).

The result of this process was a move from code-level analysis of individual papers to dimension- level clustering of common themes, and then to tension-level synthesis of review-wide insights. Rather than providing a simple list of opportunities and threats, the review therefore oﬀers a structured description of the practical tensions universities will need to navigate before using agentic AI systems at scale.

2.5 Analytical Logic

The evaluation of agentic AI in higher education should encompass both its technical capabilities and its impact as an educational and institutional phenomenon. The synthesis therefore frames adoption of agentic AI as involving four interrelated questions:


## 1. What degree of autonomy does or should the AI system have?

2. Does the AI enable instructionally valid learning design and assessment?
3. Does the AI enhance or undermine student and faculty agency?
4. What governance vulnerabilities are introduced when the system is integrated into institutional
practices?

These questions help bridge the literature review with the later framework development. The four dimensions included in this paper are not intended to simply categorize descriptions of agentic AI. Rather, they should be used as diagnostic categories to help universities assess potential agentic AI tools. An AI tutor may be desirable from a personalization standpoint but detrimental if it eliminates productive struggle or scales incorrect feedback. Similarly, AI-enabled assessment may be desirable for eﬃciency reasons but needs careful governance if it inﬂuences grading

9

policies, fairness, transparency, or accountability. The purpose of this methodology is therefore to connect literature synthesis to institutional decision-making.

2.6 Scope and Methodological Limitations

This paper does not provide a meta-analysis or otherwise statistically generalizable estimate of eﬀective- ness of agentic AI deployed in higher education. The corpus was heterogeneous with respect to method, context, and maturity. Many papers studied nascent technologies still realizing their ultimate educational eﬀects. Review was also conducted at the level of title, abstract, and metadata augmented with close reading as needed for classiﬁcation and interpretation. This approach yields conclusions that are best viewed as a literature-grounded conceptual synthesis rather than an empirically validated causal model.

A second limitation is temporality. Agentic AI systems and workﬂows, AI agents, agentic retrieval- augmented generation, and institutional AI governance practices are emerging technologies that evolve rapidly. The resultant framework should be viewed less as a ﬁnished or comprehensive model and more as a reasoned foundation for future reﬁnement. Researchers should study the dimensions proposed in this framework with empirical populations of students, faculty, administrators, instructional designers, and institutional technology teams.

With these limitations in mind, our approach of structured narrative review oriented toward

framework building is suitable for the aims of this paper. It allowed us to weave together scattered literature streams to formulate a practical conceptual foundation for examining agentic AI adoption.

3 Corpus Overview

A structured narrative review approach underpinned by framework-oriented synthesis was used to guide this review. Owing to the need to synthesize literature from education, artiﬁcial intelligence agents, assessment, governance, human agency, and artiﬁcial intelligence security literatures to meet our aims, the search strategy was broader than what is typically employed for a single database systematic review. We triangulated database searching, focused Google Scholar searching, citation chaining, and purposive inclusion of papers from related ﬁelds that were explicitly relevant to agentic AI adoption in postsecondary education.

The initial literature pool was developed using combinations of search terms related to generative AI, agentic AI, AI agents, adaptive learning, educational assessment, human agency, AI governance, and AI security. Representative search strings included: “generative AI” AND “higher education”, “agentic AI” AND “education”, “AI agents” AND “higher education”, “adaptive learning” AND “artiﬁcial intelligence”, “generative AI” AND “assessment”, “AI”

AND “student agency”, “AI governance” AND “higher education”, “prompt injection” AND “large language models”, and “sociotechnical systems” AND “AI” AND “higher education”.

Searches were conducted across multidisciplinary and technical literature sources, including Google Scholar, Scopus-indexed literature, Web of Science-indexed literature, ERIC-oriented education literature, ACM Digital Library, IEEE Xplore, SpringerLink, ScienceDirect, MDPI, Frontiers, and selected publisher platforms where relevant papers were identiﬁed.

Search terms were not limited to education-only journals because the research question sought an institutional- and governance-focused understanding of agentic AI. Papers from related disciplines including AI safety, prompt injection, algorithmic harms, sociotechnical systems, and AI governance were kept if they addressed one of the synthesis dimensions directly. This

10


> **Table 3: Corpus reﬁnement from initial resource pool to ﬁnal analytical corpus**

Stage Number of records Description

Initial resource pool 77 Bibliographic entries collected from the resource directory and targeted searches on GenAI, agentic AI, AI agents, adaptive learning, assessment, human agency, governance, ethics, dataﬁcation, prompt injection, and security.

Duplicate removal 1 One duplicate record was identiﬁed and removed from the enriched bibliography.

Records screened for relevance 76 Records were screened for relevance to higher education, the GenAI-to-Agentic-AI transition, instructional validity, human agency, governance, and institutional risk.

Records removed or deprioritized 11 Records were excluded or retained only as background when they were peripheral, weakly aligned with the review objective, focused on unrelated domains, or not directly useful for synthesis and framework development.

Final analytical corpus 65 Papers retained for direct citation, thematic synthesis, and development of the AIRA-G Framework.

Note. The ﬁnal analytical corpus refers to the 65 papers directly used in the synthesis and framework development. The broader resource pool informed screening and contextual understanding.

is because agentic AI in higher education is not solely a pedagogical phenomenon; it also relates to workﬂow autonomy, data accessibility, institutional decision-making, security, and accountability.

After duplicates were screened out from the initial enriched bibliography (n=77 records), 76 bibliographic records were screened for relevance against the research objective regarding GenAI-transition-to-Agentic-AI in higher education context. The ﬁnal corpus of papers included after relevance screening and ﬁt to research framework assessment consisted of 65 articles. The remaining bibliographic records were either removed or deprioritized due to duplication, lack of relevancy to review objective, tenuous connection to higher education, focused on non-related domains or lack of direct helpfulness toward development of synthesis tensions and AIRA-G Framework. Table 3 provides summary statistics of corpus reﬁnement steps.

The ﬁnal corpus included diﬀerent types of literature because the review objective was not limited to measuring the eﬀect of AI on learning outcomes. Instead, the study required evidence for pedagogical use, agentic capability, human agency, assessment validity, governance, and security. To avoid treating all sources as equivalent, the synthesis distinguished between evidence types and used them for diﬀerent analytical purposes. Table 4 summarizes how diﬀerent categories of literature contributed to the framework-oriented synthesis.

This evidence-type distinction was important for maintaining proportionality in the synthesis. Claims about learning eﬀectiveness, motivation, or student behaviour were not inferred solely from conceptual papers. Similarly, claims about institutional vulnerability and security risk were not derived only from pedagogy-focused studies, but were supported by technical and governance-oriented literature. The AIRA-Gen Framework therefore integrates diﬀerent evidence streams while using each stream for the type of claim it is best suited to support.

The ﬁnal analytical corpus was intentionally heterogeneous because the transition from GenAI to Agentic AI in higher education cannot be understood through a single disciplinary lens. Education-speciﬁc papers formed the core of the review, but selected work from adjacent areas such as AI governance, sociotechnical systems, prompt injection, dataﬁcation, and agent security was retained when it directly contributed to understanding institutional AI adoption.

11


> **Table 4: Evidence-type mapping used in the framework-oriented synthesis**

Evidence type Primary role in the review Type of claim supported Use in AIRA-G Framework

Empirical studies Provided evidence on student perceptions, AI use, self-eﬃcacy, learning behaviour, assessment practices, and faculty experience.

Informed human agency, cognitive calibration, instructional validity, and adoption-readiness dimensions.

Used cautiously to support claims about observed educational eﬀects, learner behaviour, and institutional practice.

Systematic and narrative reviews

Supported ﬁeld-level claims about dominant themes, recurring challenges, and research gaps.

Helped identify the four synthesis tensions and thematic clusters.

Synthesized broader trends in AI in education, adaptive learning, assessment, and GenAI adoption.

Conceptual and theoretical papers

Informed the deﬁnitions, autonomy taxonomy, and agency-calibration lens.

Clariﬁed constructs such as agency, artiﬁcial agency, human–AI interaction, academic literacies, and sociotechnical adoption.

Supported conceptual interpretation rather than direct claims of eﬀectiveness.

Technical and security papers Examined prompt injection,

Supported claims about institutional risk, security exposure, and governance vulnerability.

Informed governance, security, access-control, auditability, and risk-zone classiﬁcation.

multi-agent risk, tool access, RAG vulnerabilities, auditability, and secure AI architectures.

Governance and policy-oriented papers

Addressed institutional policy, responsible AI, dataﬁcation, ethics, accountability, and regulatory alignment.

Informed governance responses, deployment safeguards, and leadership-facing decision criteria.

Supported claims about governance readiness, policy gaps, and institutional accountability.

Note. Evidence types were not treated as interchangeable. Empirical studies were used primarily for observed educational and behavioural claims, while conceptual, technical, and governance papers were used mainly for framework development, risk identiﬁcation, and institutional decision criteria.

The corpus spans empirical studies, conceptual papers, systematic and narrative reviews, technical papers, and governance-oriented studies. This diversity was important because agentic AI in higher education involves more than classroom- level tool use. It raises questions about AI autonomy, learning design, assessment validity, student and faculty agency, learning analytics, institutional knowledge systems, privacy, security, accountability, and governance readiness. Accordingly, the corpus was organized into thematic clusters that reﬂect both the education-facing and institution-facing dimensions of agentic AI adoption.


> **Table 5 summarizes the thematic coverage of the ﬁnal analytical corpus using a matrix format.**

> The purpose of the table is not to classify papers into mutually exclusive categories, but to show
how diﬀerent literature clusters contribute to the major synthesis concerns that motivate the
AIRA-G Framework.

While Table 5 summarizes the thematic coverage of the corpus in tabular form, Figure 2 provides

a visual representation of how the major literature streams connect to the four AIRA-G synthesis dimensions. The ﬁgure highlights that the reviewed literature does not map onto the framework dimensions in a one-to-one manner. Instead, several streams contribute simultaneously to multiple dimensions, supporting the need for an integrative framework-oriented synthesis.

Literature cluster distributions indicate that strongest bodies of work supporting the ﬁnal corpus center on GenAI and LLM use in higher education settings, agentic AI/AI agents, adaptive/personalized learning, assessment and instructional validity, human agency, and governance/vulnerability or ethics. Supplementing bodies of work cover human–AI learning architectures, academic literacies, AI supported guidance, adult AI competence perceptions, and workforce readiness [37, 49, 69, 71, 76, 34]. Collectively these clusters allow enough conceptual territory to frame agentic AI adoption and use as institutional and sociotechnical challenge

12


> **Table 5: Thematic coverage of the ﬁnal analytical corpus**

Literature cluster GenAI

Agentic

Pers. learn.

Assess. validity

Human

Gov.

risk Main contribution to synthesis

base

AI

agency

✓ ✓ ✓ ✓ Establishes the baseline for understanding the shift from prompt-driven tools to agentic systems.

GenAI and LLMs in higher education

Agentic AI and AI agents ✓ ✓ ✓ ✓ Supports the agency-transition tension and deﬁnes AI as a workﬂow participant.

✓ ✓ ✓ Grounds personalization, scaﬀolding, adaptive pathways, and learner support.

Adaptive and personalized learning

✓ ✓ ✓ ✓ Establishes why AI-supported learning must remain aligned with assessment integrity.

Assessment and instructional validity

✓ ✓ Supports the tension between AI assistance, autonomy, cognitive oﬄoading, and calibration.

Human agency, autonomy, and cognition

✓ ✓ ✓ ✓ ✓ Frames AI adoption as an institutional accountability and policy-readiness problem.

Governance, ethics, and dataﬁcation

✓ ✓ Supports the argument that agentic systems expand the university risk surface.

Security, prompt injection, and institutional vulnerability

✓ ✓ ✓ Connects AI use with literacy, interpretation, role understanding, and agency calibration.

Human–AI learning architecture and academic literacies

✓ ✓ ✓ ✓ Supports use-case-sensitive evaluation of advising agents, AI competence development, and readiness planning.

AI-supported academic guidance and workforce readiness

✓ ✓ ✓ Positions agentic AI adoption as an institutional ecosystem issue rather than only a tool-use issue.

Sociotechnical and ecological framing

Note. A check mark indicates that the cluster makes a direct contribution to the corresponding synthesis concern. The clusters are overlapping rather than mutually exclusive.

instead of simply pedagogical or technical. The resulting corpus also supports the scope of this review. This paper does not seek to oﬀer a comprehensive review of AI and education writ-large. Rather it synthesizes literature germane to a single, timely transition: from reactive GenAI tools to proactive Agentic AI systems being adopted for use in higher education settings. Thematically, the coverage of literature in this corpus allows the review to analyze said transition across four interdependent areas of concern: autonomy in AI, instructional validity, human agency, and governance vulnerability. Each concern will produce synthesis results in the following section.

4 Synthesis Results and Discussion

Analysis of the chosen articles shows that discussions around AI for higher education teaching and learning have now progressed past discussions of utility (Can AI tools be leveraged to teach/learn?). The more relevant discussion centers around how agentic, adaptive, and data- intensive AI systems reshape learner-teacher-institution assessment-regulation relations. Four tensions kept arising across the corpus analyzed. These tensions are not necessarily discrete themes. Taken together, they characterize the space in which agentic AI for higher education gets situated today. They also form the basis for the stakeholder-driven framework introduced below to responsibly design, adopt, and govern AI-enabled systems.

13

Literature streams AIRA-G synthesis dimensions

GenAI and LLMs in HE

Autonomy and

Agentic AI and AI agents

role boundary

Adaptive/personalized learning

Instructional and assessment validity

Assessment & validity

Human agency & cognition

Governance/ethics/datafication

Human agency and cognitive calibration

Security & institutional vulnerability

Human AI learning architecture

Institutional governance

and security

AI academic guidance/readiness

Sociotechnical/ecological framing

Line color indicates the target AIRA-G dimension; line thickness indicates contribution strength: 1 = supporting, 2 = moderate, 3 = strong

Autonomy and role boundary

Human agency and cognitive calibration

Instructional and assessment validity

Institutional governance and security


> **Figure 2: Bipartite mapping of literature streams to the four AIRA-G synthesis dimensions. Line**

> color indicates the target AIRA-G dimension, while line thickness indicates relative contribution
strength.


> **Table 6 summarizes the four synthesis tensions and links each tension to the corresponding**

> university-level concern.

4.1 From AI as a Reactive Tool to AI as a Distributed Educational Actor

The ﬁrst major shift in the reviewed literature is away from modeling AI as a reactive tool and towards modeling AI as a distributed actor in teaching and learning workﬂows. The earliest education-focused AI work conceptualizes AI systems as learner-facing reactive tools which complete assigned tasks in response to user input (tools that recommend content, complete automated teaching tasks, or automate tedious instructional processes). The newer work on agentic AI, intelligent digital agents, and autonomous agents conceptualizes AI systems which can ﬂexibly respond to learners, act autonomously, plan sequences of actions to support learners, track learner progress, and embed in longer pedagogical workﬂows [2, 23, 72, 9].

The conceptual importance of this shift is that agency is not inherently granted to actors by virtue of computational capability. Floridi [25] explicitly frames recent developments in generative AI as the construction of agency without intelligence. Reviewing related work, Van Lier [66] and Van Lier [67] develop broad lenses for making sense of artiﬁcial agency. Relatedly, Chan et al. [13] review conceptualizations of harm in light of increasingly agentic algorithmic systems. Taken together and applied to the context of higher education, these works suggest that AI systems may not simply produce answers to student queries. Agentic AI might steer learners towards particular topics, shape approaches to assessment preparation, encourage particular interpretations of feedback, and inﬂuence academic decisions. As such, investigation into agentic

14


> **Table 6: Synthesis tensions emerging from the review corpus**

Synthesis tension Core issue University-level concern

AI as tool vs AI as distributed educational actor

What level of autonomy should AI systems be allowed to exercise in academic processes?

Agentic AI shifts AI from prompt-response assistance to proactive participation in teaching, learning, assessment, and institutional workﬂows

Personalization vs pedagogical and assessment alignment

Does AI-supported personalization strengthen learning quality or merely increase convenience and eﬃciency?

AI-enabled personalization is valuable only when aligned with learning outcomes, assessment validity, and disciplinary standards

AI assistance vs calibrated human–AI agency

AI can support self-directed learning and faculty work, but may also encourage cognitive oﬄoading, overreliance, and weakened judgment

Does AI augment student and faculty agency, or does it substitute for human reasoning and professional decision-making?

Innovation vs governance vulnerability

Institutionally embedded AI expands risk from output-level error to privacy, security, bias, accountability, and governance vulnerabilities

What safeguards are required before agentic AI systems are deployed at scale in universities?

Note. The tensions are synthesized from overlapping literature clusters and are intended to support framework development rather than function as mutually exclusive categories.

AI in higher education should not focus exclusively on student perceptions of performance or usability. We also need to understand how agentic AI shifts the distribution of educational action across human and non-human learners, instructors, and support systems.

The education-focused literature reviewed here helps to illustrate why. Drawing clear distinctions between traditional AI, agentic AI, and agentic RAG for online education, English [20] argue that agentic systems are particularly well-suited to support dialogic workﬂows by planning, verifying, and executing grounded knowledge tasks. A similarly situated work by Jayaram and Bhat [32] conceptualizes autonomous AI agents to populate campus-wide knowledge hubs with proactive, context-aware, adaptive knowledge services that support teaching, research, and administrative decision-making. Both works suggest that the shift from GenAI to agentic AI should not be framed (solely) as a technological upgrade to existing AI systems. The arrival of agentic AI in education has implications for the distribution of agency between students, teachers, AI systems, curriculum, and institutions.

Research on human–AI learning architectures supports the view that AI is becoming an active participant in educational processes rather than merely a tool. In these environments, AI works alongside teachers and students to support teaching and learning activities. In particular, Williams [69] frame learning as something that takes place between human students and agentic AI systems, not simply something that students receive from AI tools. By positioning students in

15

concert with AI systems, this work helps to validate the argument that agentic AI needs to be understood in distribution terms.

Pulling these threads together, the review therefore situates the ﬁrst major tension as the re- conceptualization of AI from a user-initiated educational tool into a distributed educational actor. Reactive GenAI presents questions of output quality, hallucination, plagiarism, and student use. Agentic AI presents questions of autonomy, educational workﬂow participation, accountability, and decision authority. At the practical level of university decision-making, we are thus led to ask: what academic work can be handed to AI, what academic work can be granted power over students by AI, and what academic work should be reserved for direct human control?

4.2 From Personalization to Pedagogically and Assessment-Aligned Personalization

A second tension relates to the deﬁnition of personalization. The AI-in-education literature commonly discusses personalization as one of AI-enabled systems’ core beneﬁts. Reviews and meta-studies on AI in education repeatedly list adaptive feedback, learner-speciﬁc recommenda- tions, ﬂexible pacing, individualized scaﬀolding, or AI-driven learning-path recommendation as outcomes that can be leveraged to improve engagement and learning [5, 57, 28, 50, 19, 60, 64]. Apoki et al. [5] review pedagogical agents within the context of personalized adaptive learning and Sajja et al. [57] present an intelligent assistant for personalized and adaptive learning within higher education. Taken together, these publications establish personalization as one of AI-supported education’s major promises.

Intelligent tutoring research and earlier online education scholarship also show that agent-based systems have long been framed as contributors to learner support and tutoring capacity [15]. The debate on agentic AI therefore builds upon rather than replaces decades of work on adaptive learning and intelligent educational agents.

However, this corpus also shows that personalization cannot be considered inherently positive. Its eﬀectiveness will depend on how well personalization systems align with pedagogical intent, disciplinary norms, and valid assessment practices. For example, Stokkink [63] argues AI and large language models require us to reconsider existing assessment practices. Are current forms of testing and performance evaluation still valid when students interact with genAI tools during assignment completion? Yet another recent systematic review of GenAI and educational assessment is worth reading. The authors identify several AI risks and considerations by focusing on how to assess AI use along dimensions of assessment design, validity, and academic misconduct [81]. The takeaway from both of these publications is that questions about how AI personalizes learning are ultimately questions about how technology gets aligned to education.

This matters because AI-enabled personalization could allow learners to take the path of least resistance. It may not optimize for comprehension. Or content generation. Or expose learners to diﬀerent viewpoints. By making everything feel too easy, personalization also runs the risk of diminishing some of higher education’s developmental purposes. But AI can also be used to foster reﬂection and formative feedback. If used correctly, personalize learning has the potential to increase learner autonomy and self-eﬃcacy. Trying to ban AI from personalization doesn’t work. Instead, we should consider how personalized learning experiences can remain aligned with teaching.

Assessment is one area where this is useful to consider. AI can personalize learning by guiding learners through feedback, portfolio-based review, rubric interpretation, and learner analytics. But there is also risk when learners use AI to ﬁnish assignments. How much AI-generated work

16

can be submitted before it is no longer representative of student knowledge? At what point does AI support infringe on ideas of authorship, authenticity, transparency, and evidence? If we cannot tell what a learner learned after they receive a highly personalized AI-supported learning experience, then the experience is hurting the validity of our assessment. Personalization isn’t about technology. It’s about pedagogy and assessment alignment.

4.3 From AI Assistance to Calibrated Human–AI Agency

A third tension relates to calibrated human–AI agency. The literature shows AI can support learners’ conﬁdence, motivation, self-regulation, and task engagement if used to provide timely support or remove unnecessary learning barriers. Alqurni [4] study agentic AI within higher education and report that students’ perceived levels of agentic AI positively predict perceived usefulness, perceived ease of use, and perceived autonomy support. Furthermore, self-eﬃcacy and autonomy support positively inﬂuence self-learning motivation and self-learning behavior. Alqurni et al. therefore provide empirical support for the argument that AI can enhance certain aspects of motivational and self-directed learning.

Similar conclusions can be drawn from research on learner readiness, academic literacies, and self-directed learning. Delcker et al. [16] study ﬁrst-year students’ AI competence to predict the intended and actual use of AI-tools for learning in higher education. Kim et al. [37] center adult learners’ expectations about AI learning and human–AI interaction, and Murekian and Sudarshan [49] argues academic literacies should be reimagined in light of agentic AI. Research on lifelong learning further positions AI as a tool for enabling adaptive, continuous, and self-directed learning [75, 6, 24, 48]. Taken together, these publications suggest AI can scaﬀold learner agency to the extent that it promotes reﬂection, conﬁdence, access, and autonomy in self-regulation.

However, this corpus also shows that AI use can create undesirable dependency. Huo and Siau [30] discuss opportunities and challenges of GenAI in business higher education. In addition to reviewing literature on knowledge acquisition, supportive augmentation, and personalized learning, they discuss challenges related to AI trustworthiness, cognitive dependency on technology, assessment integrity, and institutional policy. These ﬁndings are especially notable because they demonstrate how technologies that enable learning might also inhibit human judgment should students consume AI outputs without proper scrutiny. As such, the problem is less AI-use per se but uncalibrated use.

Similar concerns apply to how faculty use AI. While AI can lighten instructor workload, support task analysis, help plan instruction, or generate scaﬀolded learning resources [10, 8], there is a risk that faculty will become supervisors of AI-generated content rather than pedagogical designers. During both instruction and assessment, teachers face the challenge of ensuring AI tools support rather than replace meaningful educational experiences.

The human-ai dependency tension is particularly salient for adult learners and lifelong learning. On the one hand, AI could support autonomy, continuous competence development, and expert learning [71]. On the other hand, AI could modify how learners understand autonomy, responsibility, or expertise [37]. Calibrated human-AI agency is therefore discussed in the framework as both a student-centered and instructor-centered outcome.

The third tension implies that the construct of interest is not AI dependence but calibrated human–AI agency. Human–AI calibration requires learners to understand when to rely on AI, when to critique AI suggestions, when to independently verify AI-generated information, and when to accept full responsibility for their reasoning. It also requires teachers to sequence

17

learning activities such that AI use does not circumvent learning activities’ cognitive objectives. Calibration, therefore, emerges as a design consideration that applies to students and instructors alike.

4.4 From Isolated AI-Use Concerns to Ecosystem-Level Governance Vulnerability

The fourth tension scales up from previous discussions about AI in the classroom to issues of institutional governance. Several chapters included in this review explore ways in which the adoption of AI in higher education impacts individuals beyond students or instructors. In many cases AI dependencies are entrenched into larger data ecosystems, platform economies, institutional policies, commercial products, and regulatory structures. Leal Filho et al. [41] approaches AI in higher education institutions from a sociotechnical perspective and outlines how eﬀects of AI are mutually constituted through interactions between what actors can do with digital technology, institutional mediation, and governance. The existence of these examples supports treating AI adoption as an institutional ecosystem challenge rather than something that can be siloed to on-course technology use.

Needless to say this concern is magniﬁed when applied to agentive and LLM-infused systems. As tools gain the ability to connect to outside data sources, institutional systems, learning management systems, assessment software, communication pipelines, and the broader constellation of information technology (IT) there are more opportunities for things to go wrong. Beyond toxic outputs or misaligned stakeholder incentives there is privacy leakage, prompt injection attacks, data harvesting, biased automation, blackbox proﬁling, security breaches, and accountability voids. It is encouraging to see some contributors to this topic begin to address these topics. Jayaram and Bhat [32] discuss methods for constructing trustworthy autonomous AI agents that can operate within campus knowledge bases with features like identity and access management, agent-agent messaging security, audit logging, and privacy preservation.

Support for this tension can also be found in security-focused research. Recent work by Duarte et al. [17] demonstrates how LLM-integrated applications can be compromised through direct and indirect prompt injection attacks–especially when models call tools, connect to external data, participate in multi-stage workﬂows, or parse multimodal inputs. The stakes are high for universities that adopt AI-enabled tutoring, advising, assessment, or administrative systems because agentic systems will likely retrieve information about learners from institutional databases, communicate with learning management systems, and make decisions that inﬂuence academic outcomes. Expanding on this idea, Chan et al. [13] argues that we should treat increasingly agentic systems as sources of novel algorithmic harms–rather than simply treat them as more competent software tools.

Literature focusing on policy also highlights that institutions themselves may not be prepared to govern AI. Another study by Joshi et al. [33] ﬁnds that existing GenAI guidance in higher education contexts remains in its relative infancy. While many universities have published statements on GenAI and academic integrity, broader topics such as pedagogy, responsible use, legal guidance, privacy, security, and ethical use frameworks require further discussion. This research thread is important because agentic AI cannot be governed by acceptable-use statements. Institutions of higher education need policies and procedures that consider transparency, auditability, human oversight, data protection impacts, security vetting, contestability, and accountability impacts.

One could argue that readiness also includes institutional capacity to understand and prepare learners, faculty, and professional staﬀto engage with agentic AI systems. Although not speciﬁc to higher education–Joshi [34] is beneﬁcial for this review because it approaches agentic AI as a

18

workforce-readiness and institutional capacity-building challenge rather than simply a technology adoption concern. A comparable argument can be made for AI-informed academic guidance systems [76]. Depending on the level of autonomy they possess, these systems raise important governance questions about who or what can inﬂuence learner pathways, progression decisions, and institutional support programs [76]. For this reason, the included literature supports the idea that institutions will need use-case-sensitive governance and policies rather than one-size-ﬁts-all AI statements.

Synthesizing these ideas leads to the conclusion that governance considerations cannot be retroﬁtted as a separate policy layer once AI tools have been introduced. Institutions will need processes for governing AI at every stage of the lifecycle from design to decommission. The guiding questions for university leadership should not only be whether a new AI tool is pedagogically useful–but whether the institution is ready to govern the new risks introduced when that tool becomes agentic and integrated into university IT systems.

4.5 Integrative Interpretation

Overall, however, these four tensions point toward viewing agentic AI systems in higher education as a sociotechnical transformation, not a bounded instructional innovation. Neither an unchecked nor a wholly prohibitive stance toward agentic AI in higher education is supported by the literature reviewed. On the one hand, agentic AI should not be embraced uncritically simply because it might improve eﬃciency or scale access, personalization, or other desirable educational outcomes. On the other hand, agentic AI should not be rejected outright because it might challenge traditional notions of academic integrity or human agency. Rather, both the promises and risks associated with agentic AI in higher education call for intentional calibration across four stakeholder-impacting domains: agency, alignment, cognition, and governance. Higher education as an actor in learner workﬂows (tension 1). AI must be aligned with pedagogical and assessment design principles (tension 2). Human oversight of AI assistants is required to preserve learner and teacher agency (tension 3). AI use at the classroom level is conditioned by institutions’ data, security, and governance decisions (tension 4). These four insights from the literature review lend support for the development of a stakeholder-oriented framework to guide responsible and scalable AI integration in higher education. Ideally, such a framework could help higher education institutions shift AI adoption from case-by-case improvisation toward purposeful and governable approaches. We therefore propose organizing the framework around the following question, which emerges from synthesizing each tension’s guidance above: In what ways can colleges and universities design and govern agentic AI tools to enhance learning while still preserving human judgment, assessment integrity, learner agency, and institutional accountability?

5 Proposed AIRA-G Framework

Based on these synthesis results, this section proposes the AIRA-G Framework: Agentic AI Institutional Readiness and Accountability- Governance Framework for higher education. This framework aims to enable universities to know whether an agentic AI use case is pedagogically sound, agency-preserving, and institutionally governable before universities adopt the use case at scale. The framework presents an action-oriented model of institutional evaluation. It is not merely a descriptive catalog of areas of concern related to agentic AI. Rather, the framework incorporates the four synthesis tensions and converts them into an operational process to guide use-case identiﬁcation, diagnostic evaluation, risk– readiness categorization, and governance

19


> **Figure 3: AIRA-G Framework: Agentic AI Institutional Readiness and Accountability-**

> Governance Framework for higher education. The framework translates the four synthesis
tensions into diagnostic dimensions for evaluating whether an agentic AI system is educationally
valid, agency-preserving, and institutionally governable.

response.

This framework is needed because agentic AI systems diﬀer from traditional educational technologies in three key respects. First, they can operate at various levels of agency by performing initiated actions, fetching information, suggesting pathways, generating feedback, or sequencing workﬂows. Second, agentic AI may be integrated into teaching systems, assessment ecosystems, academic advising, learning analytics, and administrative operations. Third, unlike tools that are experienced only at the level of the individual user, agentic AI can rewrite the distribution of agency, responsibility, and accountability among students, teachers, institutions, and machines. Universities should not attempt to assess agentic AI technologies using only conventional technology- adoption heuristics like usefulness, perceived ease of use, eﬃciency, or user satisfaction. These heuristics will continue to be important, but they are inadequate for agentic systems that automate decisions about learning pathways, assessment practices, institutional workﬂows, and data governance.

AIRA-G Framework attempts to overcome this deﬁcit by centering institutional assessment around four diagnostic areas. The logic of AIRA-G stems from not only the above-referenced literature on agentic AI, adaptive learning, and AI governance, but also the larger literature

20


> **Table 7: Autonomy-level taxonomy for agentic AI use cases in higher education**

Level Autonomy role Description Higher-education example Minimum governance requirement

L0 Inform Responds to user prompts using approved or general information; does not recommend, decide, or initiate action.

Course FAQ bot; concept explanation assistant; syllabus query assistant.

Disclosure, content review, and basic user guidance.

L1 Recommend Suggests resources, learning paths, practice tasks, or next steps, but does not execute actions or make decisions.

Faculty oversight, recommendation transparency, and periodic review.

AI tutor recommending revision material; coding practice recommender; study-plan assistant.

L2 Act with approval Drafts feedback, interventions, messages, or advising suggestions that require explicit human approval before use.

AI-generated formative feedback for instructor review; draft advising note for faculty approval.

Human approval gate, audit log, role boundary, and accountability assignment.

L3 Act with audit Executes bounded, pre-approved workﬂows under monitoring, logging, and reversibility conditions.

Audit trail, access control, rollback option, incident response, and periodic review.

LMS-integrated agent sending approved reminders; adaptive practice release based on deﬁned rules.

L4 Autonomous consequential action

Autonomous grading system; automatic at-risk classiﬁcation; independent academic progression recommendation.

Restricted unless formal validation, appeal mechanisms, strong auditability, security review, and institutional approval exist.

Makes or executes decisions that aﬀect grading, student proﬁling, progression, advising outcomes, or institutional records without prior human approval.

Note. The taxonomy is intended for institutional evaluation of agentic AI use cases. Higher autonomy levels require stronger evidence of instructional validity, human oversight, security, auditability, and accountability.

on artiﬁcial agency more generally, human–AI learning architectures, academic literacies, and institutional readiness [66, 66, 67, 69, 49, 34]. The former works informed the framework because when building a university-facing framework it is essential to consider how AI systems are interpreted, trusted, contested, governed, and woven into institutional praxis.

5.1 Autonomy Levels for Agentic AI Use Cases

An underlying assumption of the AIRA-G Framework is that agentic AI is not one monolithic thing that we can measure and assess. To a great extent, the institutional risk presented by an AI system is proportional to how free the AI system is to act within academic workﬂows. Table 7 thus oﬀers a ﬁve-level taxonomy of autonomy with respect to higher-ed workﬂows. The oﬀered typology splits AI systems into informational, recommender, assistive but only- with-human-consent, audited autonomous workﬂow executor, and autonomous decision-maker categories.

We draw this distinction because many AI systems with wide-swath implications for academic

institutions look very similar to end users. A taxonomy of autonomy allows universities to better understand how much delegation is implied before determining an appropriate risk–readiness zone or governance response.

The autonomy taxonomy from Table 7 will be leveraged within the AIRA-G Framework as a ﬁrst-stage diagnostic ﬁlter. Broadly speaking, L0 and L1 systems may be acceptable for low-risk assistive or guided adoption use cases assuming disclosure, faculty oversight, and content review are present. L2 systems will likely need explicit human override/approval workﬂows, given outputs directly impact teaching, feedback, or advising. L3 systems will need stronger technical and governance controls in place given they take action inside bounded workﬂows

21

within institutional systems. L4 systems should be considered restricted/not ready for use in most higher-ed settings unless institution can evidentially demonstrate validity, appealability, auditability, and strong accountability measures.


> **Figure 3 presents the AIRA-G Framework’s architectural components. The AIRA-G diagnostic**

> categories are framed around four primary evaluative axes: autonomy/role boundary, instructional
and assessment validity, human agency and cognitive calibration, and institutional governance
and security. Note how these axes map directly to the four synthesis tensions we identiﬁed
previously. In aggregate, these categories help to delimit the minimum evaluative space that
universities should traverse before deploying agentic AI systems in educational or administrative
settings.


> **Figure 3 details the conceptual structure of the AIRA-G Framework. As shown in Figure 4,**

> the AIRA-G Framework can be rendered operationally as a decision architecture. The process
begins with deﬁning the agentic AI deployment context (e.g. AI tutor, digital teaching assistant,
assessment assistant, academic advising agent, campus knowledge agent, learning analytics
agent, or retrieval-augmented generation agent). Next, the use case is evaluated against each
of the four diagnostic lenses. Once all assessments are complete the system is placed into a
risk–readiness zone which subsequently prescribes a governance response. The four zones are
low- risk assistive use, guided adoption, controlled pilot, and restricted/not ready.

The two ﬁgures therefore have two complementary purposes. Figure 3 depicts the framework’s conceptual contribution by describing the four dimensions that together deﬁne institutional readiness and accountability-governance. On the other hand, Figure 4 depicts the framework’s practical contribution by describing how universities can leverage those four dimensions for a concrete use case in order to translate their assessment into an adoption decision. This distinction between conceptual contribution and practical contribution is crucial to understanding the purpose of the AIRA-G Framework, which serves both as a conceptual synthesis of the literature *and* as a practical tool for institutional decision-making.

5.2 Expected Outputs of the AIRA-G Framework

Actionable guidance is a core goal of the AIRA-G Framework. It seeks to facilitate concrete institutional outputs in addition to conceptual reﬂection. Evaluating an agentic AI use case through the framework should allow a university to produce a recorded evaluation artefact associated with that use case. Table 8 summarizes what outputs should be produced at each stage of the framework and how each output can inform decision-making.


> **Table 8 helps to explain how the AIRA-G Framework can facilitate institutional decision-**

> making. An example AI tutor that only verbally explains concepts from already-approved
course material may produce a low- autonomy classiﬁcation as well as a Zone A or Zone B
decision recommendation. However, an advising agent that reads student records and makes
recommendations for academic intervention may yield a higher autonomy classiﬁcation, Zone C
decision, and requirement for audit logs, data minimization practices, human approval, and appeal
options. The framework thus allows for granular governance as opposed to ﬂat institution-wide
approval or rejection of AI tools.

5.3 Layer 1: Agentic AI Use-Case Identiﬁcation

Layer one demands that the university articulate what agentic AI use-case they seek to implement prior to risk- or value-assessment. This is because agentic AI is not monolithic technology

22

Agentic AI Use Case (AI tutor, digital TA,

assessment assistant,

advising agent, campus

knowledge agent, Agentic

RAG)

AIRA-G Diagnostic

Evaluation

Lens 1: Autonomy and Role

Lens 2: Instructional and  Assessment Validity

Lens 3: Human Agency and  Cognitive Calibration

Lens 4: Institutional Governance

Boundary

and Security

What can the AI do?

Does the AI preserve educational purpose?

Does AI augment or replace

Can the university govern

Where does human

human judgment?

the system responsibly?

authority begin?

Risk--Readiness

Classification

Zone B: Guided Adoption

Zone C: Controlled Pilot

Zone D: Restricted / Not Ready

Zone A: Low-risk Assistive Use

Permit with faculty

Require audit logs,

Restrict until safeguards

Permit with disclosure

oversight

human approval, and

and accountability are

and basic AI literacy

and periodic review

impact review

strengthened

Governance Response

Responsible Agentic AI

Adoption in Higher Education


> **Figure 4: AIRA-G decision architecture for evaluating agentic AI use cases in higher education.**

> The framework begins with a speciﬁc deployment context, evaluates it through four diagnostic
lenses, classiﬁes it into a risk–readiness zone, and then determines the appropriate governance
response.

across education. An AI tutor meant for low stakes questioning on generic concepts, an AI assistant to help faculty prepare formative feedback, an advising agent that makes suggestions for course-taking pathways, and an AI technology that factors into summative assessment are not equivalent at an institutional level. They have varying levels of autonomy, access to data, pedagogical weight, impact on assessment, and accountability standards.

Accordingly, use-case determination should outline the intended educational role of the system (e.g. tutor, teaching assistant, instructor, mentor), the group(s) of users it supports (e.g. learners, instructors, administrators, stakeholders), the level to which it may inﬂuence decisions, what data it can access, and where it will be deployed. For instance, one AI tutor system may specialize in helping learners explain and practice concepts; one digital teaching assistant may aim to help with content generation, feedback, and discussion facilitation; one assessment assistant may inﬂuence grading or determination of learning; one advising agent may nudge student pathways; one academic-guidance agent may help faculty or students align with Education 5.0 principles; one campus knowledge agent may pull information about the institution from siloed databases [76, 32]. The risks introduced by each of these cases will vary based on how they intersect with pedagogy, cognition, and governance.

23


> **Table 8: Expected outputs generated by the AIRA-G Framework**

Framework stage Tangible output Purpose of the output Decision use

Determines whether the system should enter review and which stakeholders are aﬀected.

Use-case identiﬁcation Agentic AI use-case speciﬁcation sheet Deﬁnes system purpose, users, functions, data access, workﬂow role, and decision inﬂuence.

Autonomy assessment Autonomy-level classiﬁcation Classiﬁes the AI system from low-autonomy information support to high-autonomy consequential action.

Determines minimum oversight, approval gates, and restrictions.

Diagnostic evaluation Four-lens diagnostic proﬁle Assesses autonomy, instructional validity, human agency, and governance/security readiness.

Identiﬁes strengths, weaknesses, and missing safeguards.

Risk–readiness classiﬁcation

Zone assignment: A, B, C, or D Classiﬁes the use case as low-risk assistive use, guided adoption, controlled pilot, or restricted/not ready.

Determines whether to permit, pilot, restrict, or redesign the system.

Governance response Deployment-control plan Speciﬁes required safeguards such as disclosure, faculty oversight, audit logs, data-access limits, security testing, and appeal mechanisms.

Converts evaluation into implementation conditions.

Monitoring and review Post-deployment monitoring protocol Deﬁnes indicators for learning quality, dependency, security, assessment integrity, equity, and governance ﬁt.

Supports periodic review, reclassiﬁcation, and continuous improvement.

Note. These outputs are intended to make the AIRA-G Framework usable by academic leaders, teaching committees, instructional designers, and institutional AI governance bodies.

Layer one mitigates universities from taking extremely permissive or extreme prohibitive stances on AI. It is insuﬃcient to state that “AI is allowed” or “AI is banned” on campus because use cases have diﬀerent contextual considerations. The question is not whether agentic AI should be allowed at university X, but rather what the speciﬁc system is being used for and what decisions it can inﬂuence.

5.4 Layer 2: Diagnostic Readiness Lenses

The second layer considers the identiﬁed use case through four lenses of diagnostic readiness. These lenses represent the operationalization of the four synthesis tensions introduced earlier in the paper. Each lens should guide universities in their interrogation of whether the agentic AI system is bounded, instructionally meaningful, preserves agency, and can be governed.

5.4.1 Lens 1: Autonomy and Role Boundary

The ﬁrst lens focuses on what the AI system is permitted to do and where human authority starts and ends. This lens relates to the synthesis tension between AI as reactive tool vs AI as distributed educational actor. In typical GenAI use, the system reacts to user prompts. In agentic AI use, the system might take the initiative to perform actions on its own accord. Examples include monitoring user progress, accessing institutional systems for information lookup, recommending course of action, orchestrating actions, or communicating with external systems. Because of this, questions around role boundary are at the heart of institutional concerns.

Autonomy and role-boundary lens questions ask if the system is purely assistive, advisory, decision-supportive, or decision-making. Can the system initiate actions on its own without human prompts? Can the system access institutional systems? Can the system make recommendations

24

that impact academic decisions? Can the system take actions on behalf of users? A system that explains a concept when asked diﬀers greatly from a system that can identify at-risk students, recommend interventions, or produce assessment judgments. The greater autonomy and decision-making inﬂuence a system has, the more required ethical safeguards there should be to ensure human approval, auditability, and accountability.

This lens is conceptually grounded in literature that diﬀerentiates ever-autonomous AI systems from conventional AI tools. Research into agentic AI and intelligent digital agents introduce notions of autonomy, goal-orientation, adaptivity, and workﬂow agency [2, 23, 26]. Research in educational settings including intelligent agents, agentic AI, and campus knowledge hubs have shown how systems can participate in pedagogical and institutional workﬂows beyond static forms of support [72, 9, 20, 32]. For these reasons, institutional evaluation should start by deﬁning the boundary for what an AI system is permitted to do.

5.4.2 Lens 2: Instructional and Assessment Validity

The second lens asks whether the AI system maintains the educational intent of the task in which it is deployed. This lens derives from the synthesis tension between Personalization and Pedagogically Meaningful Personalization. While AI systems can customize feedback, tailor content, suggest resources, and individualize scaﬀolding, personalization becomes educationally meaningful when it aligns with learning outcomes, discipline-based expectations, and valid assessment.

Questions of instructional validity center on the AI system’s role in supporting target learning outcomes and preserving the cognitive work that the learning task is intended to elicit. Questions of assessment validity center on the AI system’s impact on the evidentiary guarantees of student performance. If students can leverage an AI system to avoid reasoning, writing, problem-solving, or otherwise practicing the skills of a discipline, the technology may diminish the instructional purpose of that task even if it improves speed or satisfaction. Similarly, if an AI-integrated assessment process clouds what the learner knows or can do independently, the technology may undermine the validity of that assessment.

This lens builds on literature related to adaptive learning, personalized learning, and educational assessment. Literature on pedagogical agents and AI-enabled intelligent tutors positions AI as a tool for personalized and adaptive instruction [5, 57, 28, 50]. Meanwhile, scholarship focused on GenAI and assessment emphasizes that universities will need to reconsider assessment validity, academic integrity, and evidence of learning in AI-mediated learning contexts [81, 63]. Informed by these threads, the framework asks universities to consider not only if AI enables personalized learning, but how personalized learning remains aligned with pedagogy and assessment.

5.4.3 Lens 3: Human Agency and Cognitive Calibration

Lens three: Does AI support or undermine human agency? Lens three is derived from the tension between two opposing user desires: users want AI to help but do not want to become reliant on AI. AI that supports student agency can promote learner autonomy, self-eﬃcacy, self-regulated learning, faculty productivity, etc. However, AI can introduce dangers if users become too reliant on it. Cognitive oﬄoading, overdependence, automation bias, and devaluation of professional expertise can occur if users blindly accept AI decisions. Finding a healthy middle ground, the framework deﬁnes students’ and faculty’s capacity to beneﬁt from AI tools while retaining authority over the underlying reasoning, fact checking, and judgment processes as cognitive calibration. Cognitive calibration recognizes that not all instances of cognitive

25

oﬄoading are harmful or unnecessary. Cognitive oﬄoading can beneﬁt learning when AI is used to take notes or automate low-level tasks allowing students to focus on high-level thinking. Cognitive calibration is threatened when AI usage begins to substitute for the cognitive work it is meant to support. This could involve students using AI to write essays, work through problems, or complete assignments they don’t fully understand. It could also include faculty members outsourcing pedagogical decisions, feedback interpretation, or grading decisions to AI. There are examples of both eﬀective AI support and overdependence in the literature. Alqurni [4] found that user perceptions of AI agency had positive impacts on perceived usefulness, perceived ease of use, autonomy support, self-eﬃcacy, motivation to self-directed learning, and self-directed learning behavior. Delcker et al. [16] found students who believed AI tools were competent were more likely to use AI tools to support their learning. However, Huo and Siau [30] identiﬁes cognitive dependency as a primary concern for GenAI in education among issues like trustworthiness, assessment integrity, and policy. Similar discussions have been made in the faculty literature by noting AI can serve as an instructional “exoskeleton” that enhances but does not replace teacher expertise or pedagogical decision-making [8, 10]. For this reason, universities should consider if a system supports or undermines human agency.

5.4.4 Lens 4: Institutional Governance and Security

The fourth lens looks at whether the university is able to appropriately govern and manage the system. It naturally arises out of the synthesis tension from innovation vs vulnerability to poor governance. Highly agentic AI systems may plug into learning management systems, institutional repositories, advising systems, assessment engines, communication platforms, student data infrastructure and other systems around campus. When AI is woven into our environments, inaccurate outputs and student cheating represent just a slice of the potential risk proﬁle. Privacy leakage, unfair recommendations, prompt injection attacks, insecure third-party tools, unintelligible decisions, brittle auditability, and vague accountability represent further concerns.

Lens 4 questions whether the university has appropriate policies, technical controls, human supervision, incident response procedures, and avenues for accountability. Does the system have access to more data than it needs to function? Are all AI augmented actions logged? Can people challenge high stakes decisions made with AI support? Can the university trace who is accountable when the system causes harm or outputs a bad recommendation?

Lens 4 is derived from sociotechnical and security-focused scholarship. Leal Filho et al. [41] discuss how AI outcomes at higher education institutions are shaped by the interplay between digital capacities, institutions, and governance. Jayaram and Bhat [32] discuss identity/access management, agent credentialing and trust negotiation, secure agent messaging, audit logs, privacy, and policy enforcement as foundational concerns for autonomous knowledge agents on campus. Duarte et al. [17] discusses how prompt injection attacks create new vulnerabilities that manifest when LLMs call tools, access outside data, and execute in multi-stage reasoning workﬂows. Chan et al. [13] discusses additional harms that arise when we enable increasingly agentic algorithmic systems. These works support why we might treat governance and security as design priorities instead of post-deployment regulatory compliance.

5.5 Layer 3: Risk–Readiness Classiﬁcation

After the use case passes through the four diagnostic lenses, the third layer places it in a risk–readiness zone determined by two interacting qualitative judgments: How risky is this AI

26

use case? And how ready is this institution to govern that risk? Risk level goes up with more autonomy for the system, access to sensitive data, inﬂuence over learners’ pathways, role in assessment, and weight of recommended decisions in academic outcomes. Readiness level goes up with clarity of policy, human oversight, auditability, security review, stakeholder training, and accountability structures.

AIRA-G suggests four risk–readiness zones.

Zone A: Low-risk assistive use. These are uses of AI that provide contextual support with low stakes; do not access sensitive institutional systems or data; and do not impact learner assessment or academic progression. Examples might include widely available course FAQ assistants, general concept-explanation tools, or AI-enabled brainstorming tools being used for formative purposes. Recommended governance response: permission with disclosure, workforce/student AI literacy education, and minimal monitoring.

Zone B: Guided adoption. These are uses of AI that provide support for teaching, learning, or faculty workﬂows but are not used to make consequential decisions. Examples might include AI-enabled formative feedback tools, AI-assisted instructional planning systems, or automated learning support used under faculty guidance. Recommended governance response: permission with faculty oversight, documented usage guidelines, periodic review, and faculty/user training.

Zone C: Controlled pilot. These are uses of AI that inform learning pathways, academic advising, student success proﬁling, assessment support tools, or triggered institutional interventions. These uses may allow the AI to inform but not make ﬁnal decisions that aﬀect learners. However, by shaping options and recommendations the system could alter students’ educational opportunities. Recommended governance response: controlled pilot with audit logs, mandatory human review and approval, impact reporting, security review, and stakeholder communication.

Zone D: Restricted or not ready. These are uses of Al that incorporate high degrees of autonomy, access sensitive data, impact summative assessment, have weak transparency, lack clear accountability, or lack key institutional review structures. Recommended response is to restrict the use until transparency, governance, accountability, and human oversight policies are improved.

Agentic educational technology should not be automatically banned or accepted wholesale. Education institutions should think critically about which use cases they are prepared to adopt, as well as which ones they are not ready for. Risk–readiness zoning translates a conceptual analysis of a use case into a menu of governance options. Instead of trying to answer whether agentic AI is good or bad, permissible or impossible, educators can ask: Is this AI use case well-bounded, pedagogically sound, preserving of learner agency, and governable in our context?

5.6 Layer 4: Governance Response

Layer four determines the governance response warranted for each risk—readiness zone. Responses should be commensurate with a system’s level of autonomy, educational consequence, and institutional risk. Low-risk systems might only need to provide disclosure and AI literacy. Medium-risk systems warrant faculty oversight and recurring review. High-risk systems demand controlled piloting, audit trails, approval workﬂows, security testing, and documented impact assessment. Finally, systems that fall into the category of high consequence and low readiness should not be used until the institution’s safeguards can be improved.

This governance response should also be iterative. Agentic AI systems can evolve over time with

27

model updates, integration with other tools, changes in user behavior, or expansion into new academic workﬂows. A system that was once low-risk could increase in risk if granted access to student records, tasked with making recommendations, or used as part of assessment procedures. As a result, this framework demands regular reclassiﬁcation instead of one-time approval.

Universities can take several measures to actualize this fourth layer. This can include institutional AI review committees, AI-use declarations, procurement checklists, technical security review, teaching and learning committees, and regular post-deployment audits. Including academic, technical, legal, ethical, and student voices in the governance response is crucial as agentic AI adoption will impact many stakeholders at once.

5.7 Using the AIRA-G Framework in Higher Education Institutions

Use of the AIRA-G Framework can happen pre-, during, and post-deployment. Prior to system launch, universities can assess proposed AI uses cases and determine whether they should be allowed, piloted, restricted, or redesigned. During system deployment, universities can use it to frame ongoing monitoring around performance, user experience, learning outcomes, assessment impact, or security incidents. After launch, universities can use it as part of periodic review, policy updates, or revision.

To conduct a use case evaluation, an institution would follow these steps. Deﬁne the use case. Determine who will be aﬀected by the technology. Assess the system across the four lenses. Place the use case into a risk–readiness zone. Administer recommended governance response. Continuously monitor new technology over time, reassessing the use case classiﬁcation if its autonomy, access, impact, or risk factors change.

Finally, it should be noted that AIRA-G can help universities recognize when AI systems that appear similar on the surface should be treated diﬀerently. An optional AI tutor used for formative practice may fall into Zone A or B, but baked into a course with student performance tracking and intervention suggestion functionality may be better suited for Zone C treatment. An AI writing assistant used for brainstorming may pose little risk, while AI used to score student essays for summative assessment may pose signiﬁcant risks. A campus knowledge agent that provides information by fetching documents on public policy may pose little risk, while knowledge agents that access student records or internal governance information systems will require additional scrutiny and controls.

AIRA-G thus provides university decision-makers with a way to translate insights from the conceptual framework into institutional policy. It moves the paper’s contribution past highlighting tensions within the literature and into demonstrating how institutions can operationalize resolution of those tensions through a deliberative decision-making process. Rather than choosing sides in the AI deployment conversation, this framework allows universities to have their cake and eat it too.

5.8 Operationalizing the AIRA-G Framework

The AIRA-G Framework becomes practically useful when its diagnostic lenses are translated into evaluation questions, evidence requirements, and governance actions. Table 10 presents an operationalization template that universities can adapt for institutional review, pilot approval, procurement decisions, and post-deployment monitoring. The table is not intended as a ﬁxed checklist; rather, it provides a structured evaluation mechanism for connecting conceptual concerns with actionable institutional evidence.

28


> **Table 9: Operationalization of the AIRA-G Framework for institutional evaluation**

Diagnostic lens Key evaluation questions Evidence required Governance action

Autonomy and role boundary

System role description; autonomy level; task boundary; human approval points; decision inﬂuence map

Deﬁne permissible tasks; require approval for consequential actions; restrict unclear high-autonomy functions

What can the AI system do? Can it initiate actions, access systems, recommend decisions, or inﬂuence academic workﬂows?

Instructional and assessment validity

Learning-outcome mapping; assessment-use policy; feedback validation; faculty review records

Permit formative use; require assessment redesign; restrict summative use until validity is established

Does the AI system support intended learning outcomes? Does it preserve assessment integrity and evidence of student learning?

Human agency and cognitive calibration

Does the AI system strengthen student and faculty agency, or does it encourage overreliance and cognitive oﬄoading?

Require reﬂective AI-use statements; embed veriﬁcation tasks; provide faculty and student AI-literacy support

AI-use disclosure; student reﬂection records; veriﬁcation protocol; faculty oversight plan; AI literacy and academic-literacy support

Institutional governance and security

Approve with safeguards; run controlled pilot; require audit logs; restrict deployment until governance controls exist

Can the institution govern the system responsibly? Are privacy, prompt-injection risk, auditability, and accountability addressed?

Data-access review; security testing; audit logs; vendor review; accountability pathway; incident-response plan

Note. The table translates the four diagnostic lenses into institutional evaluation questions, evidence requirements, and governance actions. It may be used before deployment, during pilot testing, and during periodic post-deployment review.

This operationalization strengthens the framework in two ways. First, it makes the framework use-case sensitive. The same AI system may be low risk in one context and high risk in another depending on its autonomy, data access, assessment impact, and institutional consequence. For example, a chatbot that answers general course queries may require basic disclosure and monitoring, whereas an advising agent that accesses student records and recommends progression pathways requires stronger oversight, auditability, and accountability.

Second, the operationalization connects conceptual concerns to actionable evidence. A claim that an AI system preserves assessment validity should be supported by learning-outcome mapping, faculty review, and evidence that the system does not obscure student performance. Similarly, a claim that an agentic AI system is secure should be supported by data-access review, audit logs, prompt-injection testing, vendor assessment, and incident-response procedures. This is particularly important because the risks of agentic AI are not always visible at the interface level. A system that appears to be a helpful tutor may also collect learner data, shape learning pathways, or generate recommendations that inﬂuence academic behaviour.

The AIRA-G Framework therefore moves beyond general principles of responsible AI. It requires universities to justify adoption decisions through evidence and to calibrate governance responses according to the speciﬁc use case. In this sense, the framework provides a bridge between literature synthesis and institutional implementation.

The AIRA-G Framework becomes practically useful only when its diagnostic lenses are translated into evaluation questions, evidence requirements, and governance actions. Table 10 presents one way to operationalize the framework for institutional use. The table is not intended as a ﬁxed checklist; rather, it provides a structured evaluation template that universities can adapt according to local policies, disciplinary contexts, regulatory requirements, and risk tolerance.

This operationalization strengthens the framework in two ways. First, it makes the framework use-case sensitive. The same AI system may be low risk in one context and high risk in another

29


> **Table 10: Operationalization of the AIRA-G Framework for institutional evaluation**

Diagnostic lens Key evaluation questions Evidence required Possible governance action

Autonomy and role boundary

System role description; autonomy level; task boundary; human approval points; decision inﬂuence map

Deﬁne permissible tasks; require human approval for consequential actions; restrict high-autonomy functions if unclear

What can the AI system do? Can it initiate actions, access systems, recommend decisions, or inﬂuence academic workﬂows?

Instructional and assessment validity

Learning outcome mapping; assessment-use policy; feedback validation; faculty review records

Permit for formative use; require assessment redesign; prohibit use in summative contexts until validity is established

Does the AI system support intended learning outcomes? Does it preserve assessment integrity and evidence of student learning?

Human agency and cognitive calibration

Require reﬂective AI-use statements; embed veriﬁcation tasks; provide faculty and student AI literacy support; redesign academic-literacy expectations for AI-mediated work

Does the AI system strengthen student and faculty agency, or does it encourage overreliance and cognitive oﬄoading?

AI-use disclosure; student reﬂection records; veriﬁcation protocol; faculty oversight plan; AI literacy and academic-literacy support

Institutional governance and security

Can the institution govern the system responsibly? Are privacy, prompt-injection risk, auditability, and accountability addressed?

Approve with safeguards; run controlled pilot; require audit logs; restrict deployment until governance controls exist

Data access review; security testing; audit logs; vendor review; accountability pathway; incident response plan

Note. The table translates the four diagnostic lenses into institutional evaluation questions, evidence requirements, and governance actions. It can be used before deployment, during pilot testing, and during periodic post-deployment review.

depending on its autonomy, data access, assessment impact, and institutional consequence. Second, it connects conceptual concerns to actionable institutional evidence. For example, a claim that an AI system preserves assessment validity should be supported by learning outcome mapping, faculty review, and evidence that the system does not obscure student performance. Similarly, a claim that an AI system is secure should be supported by data access review, audit logs, prompt-injection testing, and accountability procedures.

The framework therefore moves beyond general principles of responsible AI. It requires universities to justify adoption decisions through evidence. This is particularly important for agentic AI because the risks are not always visible at the interface level. A system that appears to be a helpful tutor may also collect learner data, inﬂuence study pathways, or generate recommendations that shape academic behaviour. A campus knowledge agent may improve information access while also creating privacy, security, and accountability concerns. The operationalization table helps institutions surface these hidden dependencies before deployment.

6 Implications

The synthesis and the proposed AIRA-G Framework have implications for universities, faculty members, students, instructional designers, technology teams, and policy-makers. The central implication is that agentic AI should not be treated as a generic educational technology. Because agentic AI systems can act with varying degrees of autonomy, access institutional data, inﬂuence learning pathways, and participate in assessment or advising workﬂows, their adoption requires use-case-sensitive evaluation. This section discusses the implications of the review across four levels: institutional governance, teaching and assessment, student learning and agency, and system design.

30

6.1 Alignment with Existing AI Governance Frameworks

The AIRA-G Framework does not seek to replace existing AI governance standards or forthcoming regulations. Rather, it seeks to map their high-level governance logic onto a decision-making process intended speciﬁcally for higher education use cases. This matters because educators need a framework that links general responsible- AI principles to day-to-day academic workﬂows like tutoring, assessment, advising, learning analytics, or campus knowledge systems. AIRA-G’s underlying logic tracks well with risk-based approaches to AI governance. Identifying the AI use case, for example, generally aligns with articulating an AI system’s context, purpose, stakeholders, and potential harms. Diagnosing the use case via the Framework’s lenses aligns with measuring how those risks manifest with respect to validity, reliability, human oversight, privacy and security, transparency, and accountability. Categorizing a use case into a risk– readiness level and associating that level with a recommended governance response also aligns with the central principle that AI systems presenting higher potential risk to humans should be subject to stronger safeguards, monitoring, and institutional accountability. We therefore view the framework as something like a higher-ed adaptation of existing governance logics. The National Institute of Standards and Technology’s AI Risk Management Framework, for example, outlines responsible AI use principles around governing, mapping, measuring, and managing AI risks; AIRA-G puts this logic into practice by identifying a use case, evaluating it via diagnostic lenses, categorizing its risk–readiness level, and then suggesting governance responses to that level. Similarly, forthcoming risk-based regulatory approaches like the EU AI Act are aligned with AIRA-G’s distinction between low-risk assistive uses, guided adoption, controlled pilot-stage deployment, and restricted or not-yet use cases. Standards like ISO/IEC 42001 will also play a role, as universities that implement agentic AI at scale will need to develop an institutional AI management system to clarify responsible parties, monitoring procedures, documentation practices, and continuous improvement practices. Aligning AIRA-G with these standards matters for higher education speciﬁcally because it allows universities to use the Framework as a translation layer between abstract governance standards and academic decision-making. While a voluntary governance standard may state that risk management, human oversight, transparency, and accountability are important, it will rarely articulate how those principles apply to tutors, assessmens tools, advising systems, or LMS integrations. AIRA-G seeks to ﬁll that gap by rephrasing broad responsible- AI principles into concrete questions about educational technology: How autonomous is the system? Does it uphold or undermine instructional and assessment validity? How does it impact student and faculty agency? Can my university successfully audit, secure, contest, and govern the system? Universities can and should use outside AI governance standards to evaluate their AI purchasing decisions. Where those standards fall short of providing clear implementation guidance, however, educators can use AIRA-G to bridge the gap between external expectations and internal academic decision-making.

6.2 Implications for Institutional Governance

For institutions of higher education, the key takeaway is that artiﬁcial intelligence governance should extend well beyond acceptable-use policies and academic integrity statements. While these are still relevant, they do not adequately cover agentic AI systems that may write into learning management systems, student information systems, assessment repositories, student advising platforms, or campus knowledge bases. Institutions thus have a dual AI governance challenge: Regulating students’ uses of AI and specifying how the institution itself will select, deploy, monitor, and audit AI systems. Considerations for developing AI governance at universities

31

One starting point, oﬀered by the AIRA-G framework, is to classify uses of AI. Institutions should diﬀerentiate between low-stakes AI tools that are used to provide students with formative support and high-impact systems that are tied to assessment, advising, progression, or student proﬁling. These use cases are not equally risky and so should be governed diﬀerently. A LLM plugged into a public course FAQ bot may only need clear disclosure to students along with some lightweight monitoring. An advising agent plugged into student records likely needs stronger data governance, plus human oversight, audit trails, and ability to challenge automated decisions.

AI review mechanisms

Relatedly, institutions should develop formal internal mechanisms to review AI systems. These include: creating AI review boards at the institutional level, requiring checklist reviews prior to procurement of AI systems, incorporating data-access and security reviews, routing projects through teaching and learning committees, establishing red-teaming practices for security testing, and scheduling periodic review of AI systems post-deployment. Universities should consider academic, technical, ethical, legal, and student perspectives in these review processes. Without this level of internal AI review, universities may inadvertently adopt systems that oﬀer eﬃciencies at the user interface while creating obscured costs in data governance, accountability, and public trust.

6.3 Alignment with Existing AI Governance Frameworks

AIRA-G does not replace general AI governance standards or regulatory frameworks. Instead it instantiates their general risk-governance logic in a higher-education-speciﬁc decision pro- cess. This is necessary because universities lack a decision framework connecting high-level responsible-AI principles to academic use cases like tutoring, assessment, advising, learning analytics, campus knowledge systems, and agentically enhanced LMS workﬂows.

AIRA-G’s logic broadly follows the NIST Artiﬁcial Intelligence Risk Management Framework (AI RMF), which frames AI risk management around the functions: govern, map, measure, manage [51]. AIRA-G operationalizes a comparable sequence for higher education purposes: (1) identity the agentic AI use case being considered; (2) assess that use case through diagnostic lenses; (3) assign that use case system to a risk–readiness zone; and (4) tie risk–readiness level to a governance response. It thereby customizes NIST-style risk-management logic for academic use cases where educational validity, assessment integrity, student agency, faculty judgement, privacy, and auditability are primary risk considerations. The NIST Generative AI Proﬁle likewise merits consideration because it describes risks concentrated in generative AI systems: information integrity and dissemination; misuse; data privacy; security; and human-AI interaction considerations [52]. Most of these risks increase when GenAI systems are made agentically-available with tool access, workﬂow roles, and connections to institution-wide data sources.

AIRA-G’s logic is consistent with risk-based regulatory approaches encoded in the European Union Artiﬁcial Intelligence Act. The EU AI Act sorts AI uses into risk categories and marks some edtech uses as high risk if they relate to access to education, education progession, grading, or certiﬁcations [22]. This directly impacts universities because agentically-enhanced AI systems used for grading, student-risk classiﬁcation, academic advising, or progression recommendations can substantially impact students. AIRA-G’s separation of low-risk assistive use, guided adoption, carefully monitored pilot use, and restricted/not- ready use therefore translates risk-based regulation into higher-education-speciﬁc concepts. For instance, natural language AI bot may be considered low-risk assistive functionality while an LMS-integrated

32

advising agent that draws on student records to propose pathway interventions would trigger higher oversight standards, activity logging, human gatekeeping, and student appeals.

Finally ISO/IEC 4 2001: 20 23 prescribes expectations for AI management systems within organizations [1]. This standard relates to AIRA-G’s institutional scope because it deﬁnes requirements for establishing, implementing, maintenance, and continual improvement of an Artiﬁcial Intelligence Management System. Universities need this management-system mindset because agentically-enhanced AI systems cannot be responsibly governed by point-course policies or one-time tool approvals. Universities need assigned responsibilities, documented procedures, monitoring plans, supplier review processes, risk treatment strategies, and improve- ment mechanisms. AIRA-G supports this management- perspective by mapping to academic questions that should precede, inform, and follow deployment: what is the system allowed to do? Does it preserve instructional validity? Assessment validity? Strengthen student and faculty agency? Can it be audited and overseen responsibly?

AIRA-G bridges responsible AI governance standards and university decision-making about agentic technologies. Principles like risk management, transparency, human oversight, docu- mentation, accountability, and continuous improvement all exist in AI governance frameworks. However, those general principles must be translated into speciﬁc evaluation bins and governance actions. Translation is required because risks do not line up perfectly across academic use cases. Chatbots, AI tutors, assessment support technologies, advising agents, andampus knowledge agents vary on autonomy, data access, educational impact, and accountability. AIRA-G ties responsible AI principles to decisions by connecting external expectations to internal use-case classiﬁcation.

6.4 Implications for Teaching, Learning Design, and Assessment

For faculty members and instructional designers, one takeaway from the review is that AI use must be considered and adopted in service of instructional validity. The question is not whether AI can individualize learning or produce automated feedback. The question is whether AI support can stay aligned with learning objectives, disciplinary norms, and assessment quality. Agentic AI raises this concern with particular urgency, because it can make learning look easier while masking the cognitive struggle necessary for deeper learning.

Guided by AIRA-G, faculty can begin to redesign learning activities to privilege visible reasoning, process documentation, source vetting, reﬂection, and justiﬁcation. As AI-mediated learning environments become more prevalent, assessment should shift toward determining how students reason through, evaluate, fact-check, and incorporate AI-generated information rather than if students produce a desired end product. This doesn’t mean banning all uses of AI in assessment. It does mean that when faculty allow AI assistance for an assignment, they must clearly articulate when and what kind of assistance is allowed and how students will independently demonstrate their learning.

Another implication of the framework is that formative and summative contexts may need to be treated diﬀerently. The review makes clear that AI supports can be beneﬁcial for formative learning when the objective is feedback, practice, or exploration. But in summative assessments, faculty will need to more carefully circumspect AI involvement, as it poses unique challenges to authentic authorship, demonstrated competence, and evidence of learning. Faculty should not simply be posting AI usage policies on their syllabi for existing assignments. Faculty should be questioning whether existing assessments will hold up under the conditions of ubiquitous AI.

33

6.5 Implications for Student Agency and AI Literacy

According to the review, agentic AI may facilitate autonomy, self-eﬃcacy and self-directed learning. However, this is contingent on students critically using AI. The question is not if students will use AI, but rather if they know how AI ﬁts into their learning process. Agentic AI can enable learners to generate explanations, plan their study time, provide feedback, and seek alternative viewpoints. However, AI can also promote cognitive oﬄoading when students rely on it to avoid reading, reasoning, writing, or double-checking work. As such, the AIRA-G Framework positions AI literacy as central to higher education. Learners must know when to critically consider or distrust AI-generated content, how to avoid hallucination and bias, where to verify AI-generated content, and what conduct is unethical when using AI for academics. They should also know how to report when and how AI helped them learn, and where their own thoughts begin and end. This moves past surface-level policies around plagiarism to requiring transparent instruction on how to collaborate with AI systems responsibly. A practical takeaway is that higher education institutions should integrate AI literacy into coursework rather than leaving it up to students to learn on their own or attend an optional seminar. Students should know how to ask better questions, judge output, cite or disclose AI contributions when necessary, maintain academic integrity, and learn how to use AI as a tool for thinking – not a substitute for it. This is especially crucial when interacting with agentic AI that may seem more authoritative, proactive, or personalized.

6.6 Implications for System Design and Technical Implementation

For system designers and technical teams more broadly, the review suggests that educational AI systems should be built with pedagogical, cognitive, and governance considerations in mind from inception. Agentic AI systems should not be optimized solely for engagement metrics, response quality, or computational eﬃciency. They should also be designed to enable transparency, human oversight, inspectability of feedback loops, role awareness, data minimization, auditability, and overall system security. According to The AIRA-G Framework, design teams should establish AI system role from the outset with users. Students and faculty should understand whether the agentic system is serving in the role of a tutor, recommender, evaluator, personal assistant, workﬂow agent, or some combination thereof. Design teams should also make it clear whether the agentic system’s output is advisory in nature or can be automatically executed. Or whether such output will be reviewed by a human collaborator. Organizations will need to consider role and intent when agentic AI systems are built into learning management systems, student advising systems, or university knowledgebases. Technical teams will also need to consider implementation strategies around key security risks found with LLM- integrated and agentic systems speciﬁcally. These include prompt injection, illicit data access, leakage from institutional knowledgebases, insecure tool calls, and poor logging. As such, agentic AI systems deployed on university campuses should include access controls, audit trails, prompts for injection testing, incident response plans, and responsible disclosure chains of accountability. In education, questions of security and privacy are not purely technical—they are questions of student privacy, institutional trustworthiness, and academic equity.

6.7 Implications for Policy and Future Institutional Practice

At an institutional policy level, the review recommends universities shift from tool-speciﬁc AI policies to capability- sensitive AI governance. Tool-speciﬁc policies will likely become obsolete as AI systems proliferate. Capability-sensitive governance asks what a system can

34

do: act autonomously? access sensitive data? inﬂuence assessment? recommend high stakes decisions? auto-initiate workﬂows? This model has staying power because it vets AI systems across dimensions of function, consequence, and governance need.

Guided by the AIRA-G Framework, institutions can tag AI use cases to risk–readiness zones and assign proportionate responses to governance. Universities can thus avoid false polarities of either carte blanche adoption (due to unquestioned eﬃciency claims) or blanket prohibition (due to misguided fears of mission corruption). Rather, institutions can assume a middle ground in which low-risk uses are enabled, moderate-risk uses are guided, high-risk uses are controlled through piloting, and ungovernable uses are prohibited until safeguards can be developed.

In general, this study illuminates a need to shift how institutions conceptualize agentic AI. It should be governed not merely as a technology, but as an actor in education. Questions about its use should therefore involve considerations of educational purpose, human agency, assessment validity, data governance, security, and accountability. The AIRA-G Framework is one method institutions can use to systemically review these issues.

7 Conclusion

Generative AI tools have been mostly treated as context-blind support tools that run on prompts. Agentic AI shifts that notion towards educational systems that operate with more autonomy, can adapt to learner context, draw upon institutional knowledge, recommend next steps, and actively participate in academic workﬂows. Put succinctly, educational institutions are moving from a problem of “how do we use AI tools?” to a problem of “how ready is our institution? How valid is our instruction? How are we preserving human agency? And who will be held accountable to govern these systems?”

Instead of conducting new empirical research, this paper presented a narrative review of literature and framework-oriented synthesis across research on GenAI, agentic AI, AI agents, adaptive learning technology, assessment, student agency, faculty agency, cognitive oﬄoading, dataﬁcation, educational technology governance, and AI security. The resulting conceptual synthesis revealed four major tensions that recurred across these literatures. First, AI is moving from being a reactive support tool to being a collaborative, if not distributed, educational actor. Second, AI-facilitated personalization must be considered alongside validity in instruction and alignment in assessment. Third, AI assistance can enable student self-direction and alleviate faculty work, but may also create new anxieties around dependency and cognitive oﬄoading. Fourth, agentic AI surfaces institutional risk tensions from output-level problems to ecosystem-level problems involving privacy, security, auditability, and accountability.

Responding to these tensions required a call to action, leading this paper to propose the AIRA-G Framework: An Agentic AI Institutional Readiness and Accountability-Governance Framework for Higher Education. The framework builds on the prior synthesis by translating four major tensions into a decision- and institution-oriented evaluation model. The AIRA-G Framework starts with an agentic AI use case, prompts the institution to review it through four diagnostic lenses, categorises it into a risk-readiness zone, and associates that classiﬁcation with a proportionate governance response. In doing so, it moves beyond aspirational AI policy statements and towards a decision tree that helps universities test whether agentic AI systems are: educationally valid, agency-preserving, and institutionally governable.

The argument this paper hopes to make is that the responsible adoption of agentic AI is impossible through either unlimited acceptance or overregulation. Universities need calibrated, use-case-

35

sensitive governance. Low-risk applications of AI can likely be approved with appropriate disclosure to students and support for students to understand AI literacy. If an agentic AI system directly impacts college decisions related to assessment, academic advising, student proﬁling, or institutional decisions, that system should be held to a higher bar of oversight, auditability, security testing, and accountability. The AIRA-G Framework is one tool that universities can utilize to make calibrated decisions.

This literature-grounded exploration is limited by the emergent nature of agentic AI in higher education. Many of the systems described in the literature are not actually built or only exist at the conceptual or experimentation stage. As such, this study is best understood as a conceptual synthesis grounded in research literature rather than an empirical validation of the proposed framework. Future studies should aim to test and adapt the AIRA-G Framework through institutional case studies, subject-matter expert (higher education leaders, technologists, developers) validation exercises, student and faculty consultations, and pilot programs that deploy agentic AI systems at scale in educational settings. Empirical studies should also be leveraged to understand how agentic AI impacts learning outcomes, assessment validity, student agency, faculty judgment, and institutional trust longitudinally.

Even in light of these limitations, this paper makes several contributions to the literature. By examining the transition from GenAI to agentic AI through a lens of educational signiﬁcance, this paper deﬁnes why universities should care about agentic AI technologies. Through a review of disparate research areas, this paper pulls together fragmented conversations about agentic AI in education into a single conceptual review. By building the AIRA-G Framework, this paper moves beyond mere conceptual conversation to oﬀer educators a potential path forward that connects conceptual synthesis to institutional action. Agentic AI is rapidly becoming a part of higher education. As such, higher education will need tools to govern that adoption. Tools that preserve human judgment. Tools that protect educational integrity. And tools that enable innovation rather than restrain it. The AIRA-G Framework is one attempt to start that conversation.

Declaration

Funding: No direct funding was received for this study.

Ethics approval: Not applicable.

Consent to participate: Not applicable.

Consent for publication: Not applicable.

Availability of data and materials: No primary data were collected for the study.

Competing interests: Bhaskar Mangal is aﬃliated with C.E. Info Systems Ltd. (MapmyIndia) and is pursuing a Ph.D. at BITS Pilani under an industry-sponsored programme. He is additionally a co-founder and director of SKPLT Pvt. Ltd. (Skillplot), the industry partner of the GAIR Lab. This work is an independent academic contribution and does not utilize proprietary data, models, or use cases from MapmyIndia or Skillplot. The views expressed are solely those of the authors and do not necessarily reﬂect those of the aﬃliated organizations. All remaining authors declare no competing interests.

Authors’ contributions: Ritika Bhatia conceptualized the study and led manuscript preparation. Harshvardhan Singh Nirban, Bhaskar Mangal, and Ashutosh Bhatia conducted the literature review and contributed to writing and revisions. All authors approved the ﬁnal manuscript.

36

Acknowledgements: The authors acknowledge the Generative AI Research Lab (GAIR Lab), Department of CSIS, BITS Pilani, established in collaboration with SKPLT Pvt. Ltd. (Skillplot), for institutional support. All outputs appropriately recognize GAIR Lab and Skillplot® (https: //gairlab.skillplot.org) as per collaborative research guidelines.


## References

[1] (2023). Iso/iec 42001:2023: Information technology — artiﬁcial intelligence — management

system.

[2] Acharya, D. B., Kuppan, K., and Divya, B. (2025). Agentic ai: Autonomous intelligence for

complex goals—a comprehensive survey. IEEe Access, 13:18912–18936.

[3] Alifah, N. and Hidayat, A. R. (2025). Eﬀectiveness of artiﬁcial intelligence-based learning

analytics tool in supporting personalized learning in higher education. Jurnal Pendidikan Progresif, 15(1):74–84.

[4] Alqurni, J. (2026). Exploring the role of agentic ai in fostering self-eﬃcacy, autonomy

support, and self-learning motivation in higher education. Frontiers in Artiﬁcial Intelligence, 9:1738774.

[5] Apoki, U. C., Hussein, A. M. A., Al-Chalabi, H. K. M., Badica, C., and Mocanu, M. L. (2022).

The role of pedagogical agents in personalised adaptive learning: A review. Sustainability, 14(11):6442.

[6] Arias, J., Salas, J. I., Chiappe, A., and Sáez Delgado, F. (2025). The extended education 4.0:

Lifelong learning in times of artiﬁcial intelligence. Applied Sciences, 15(17):9352.

[7] Askari, M. (2026). Reliable but supervised: evaluating a generative ai-rubric model for

consistent and fair assessment in postgraduate education. Assessment & Evaluation in Higher Education, 51(2):213–230.

[8] August, S. E. and Tsaima, A. (2021). Artiﬁcial intelligence and machine learning: an

instructor’s exoskeleton in the future of education. In Innovative learning environments in STEM higher education: Opportunities, challenges, and looking forward, pages 79–105. Springer.

[9] Babar, P. A. (2025). Agentic ai for personalized education and adaptive learning environments.

International Journal of Computing and Engineering, 7(12):1–10.

[10] Balikci, S., Terzioglu, N. K., and Rakap, S. (2026). Chatgpt-assisted task analysis for

special education teachers: An exploratory study of alignment, readability, eﬃciency, and acceptability. Future Internet, 18(3):158.

[11] Bearman, M. and Luckin, R. (2020). Preparing university assessment for a world with ai:

Tasks for human intelligence. In Bearman, M., Dawson, P., Ajjawi, R., Tai, J., and Boud, D., editors, Re-imagining University Assessment in a Digital World, volume 7 of The Enabling Power of Assessment, pages 49–63. Springer, Cham.

[12] Bouakaz, L. and Khalid, S. (2025). Ai in education: a sociological exploration of technology

in learning environments. In Frontiers in Education, volume 10, page 1700876. Frontiers Media SA.

37

[13] Chan, A., Salganik, R., Markelius, A., Pang, C., Rajkumar, N., Krasheninnikov, D.,

Langosco, L., He, Z., Duan, Y., Carroll, M., et al. (2023). Harms from increasingly agentic algorithmic systems. In Proceedings of the 2023 ACM conference on fairness, accountability, and transparency, pages 651–666.

[14] Chen, L., Chen, P., and Lin, Z. (2020). Artiﬁcial intelligence in education: A review. IEEE

access, 8:75264–75278.

[15] Cheung, B., Hui, L., Zhang, J., and Yiu, S.-M. (2003). Smarttutor: An intelligent tutoring

system in web-based adult education. Journal of Systems and Software, 68(1):11–25.

[16] Delcker, J., Heil, J., Ifenthaler, D., Seufert, S., and Spirgi, L. (2024). First-year students

ai-competence as a predictor for intended and de facto use of ai-tools for supporting learning processes in higher education. International Journal of Educational Technology in Higher Education, 21(1):18.

[17] Duarte, J. D., Cândido, G. D., De Britto Filho, J. R. A., Neto, J. S., Costa, E. J., Da Costa,

J. P. J., and De Melo, L. P. (2026). A systematic review of prompt injection attacks on large language models: Trends, taxonomy, evaluation, defenses and opportunities. IEEE Access.

[18] Eaton, E., Koenig, S., Schulz, C., Maurelli, F., Lee, J., Eckroth, J., Crowley, M., Freedman,

R. G., Cardona-Rivera, R. E., Machado, T., et al. (2018). Blue sky ideas in artiﬁcial intelligence education from the eaai 2017 new and future ai educator program. AI Matters, 3(4):23–31.

[19] El Fazazi, H., Elgarej, M., Qbadou, M., and Mansouri, K. (2021). Design of an adaptive

e-learning system based on multi-agent approach and reinforcement learning. Engineering, Technology & Applied Science Research, 11(1):6637–6644.

[20] English, V. (2025). Comparing traditional ai, agentic ai and agentic rag for dialogic online

education. Asian Journal of Education and Training, 11(4):198–210.

[21] Eti, N., Mosia, M., and Egara, F. O. (2026). The role of ai-driven personalised learning in

enhancing mathematics problem-solving skills: a systematic review. Frontiers in Computer Science, 8:1813431.

[22] European Parliament and Council of the European Union (2024). Regulation (eu) 2024/1689

of the european parliament and of the council of 13 june 2024 laying down harmonised rules on artiﬁcial intelligence. Oﬃcial Journal of the European Union. Artiﬁcial Intelligence Act.

[23] Faught, B., Lu, H., Marshall, T., Sikka, H., Guruprasad, P., and Gauri15, B. (2024).

Intelligent digital agents in the era of large language models.

[24] Fidalgo, P. and Thormann, J. (2024). The future of lifelong learning: The role of artiﬁcial

intelligence and distance education.

[25] Floridi, L. (2023). Ai as agency without intelligence: on chatgpt, large language models,

and other generative models: Floridi l. Philosophy & technology, 36(1):15.

[26] Goyal, S. (2025). A critical review of agentic ai: Core technologies, applications, ethical

implications, and future research directions. Jurnal Masyarakat Informatika, 16(2):268–283.

[27] Hadad, Y., Keren, B., and Naveh, G. (2020). The relative importance of teaching evaluation

criteria from the points of view of students and faculty. Assessment & Evaluation in Higher Education, 45(3):447–459.

38

[28] Hariyanto, Kristianingsih, F. X. D., and Maharani, R. (2025). Artiﬁcial intelligence in

adaptive education: a systematic review of techniques for personalized learning. Discover Education, 4(1):458.

[29] Huo, X. and Siau, K. L. (2024a). Generative artiﬁcial intelligence in business higher

education: A focus group study. Journal of Global Information Management (JGIM), 32(1):1–21.

[30] Huo, X. and Siau, K. L. (2024b). Generative Artiﬁcial Intelligence in Business Higher

Education: A Focus Group Study. Journal of Global Information Management, 32(1):1–21.

[31] Iqbal, J., Hashmi, Z. F., Asghar, M. Z., and Abid, M. N. (2025). Generative ai tool use

enhances academic achievement in sustainable education through shared metacognition and cognitive oﬄoading among preservice teachers. Scientiﬁc Reports, 15(1):16610.

[32] Jayaram, Y. and Bhat, J. (2025). Autonomous ai agents for campus knowledge hubs: A

secure and intelligent system architecture. International Journal of Artiﬁcial Intelligence, Data Science, and Machine Learning, 6(4):150–161.

[33] Joshi, A., McGoldrick, B., Mittal, N., Roy, S., Zeba, Z., Ofori, M. A., Dockery, S., Jha,

N., Auerbach, J., Cadet, J., et al. (2026). Investigating the use of generative ai policies among aspph member schools and programs of public health. Frontiers in Public Health, 14:1796810.

[34] Joshi, S. (2025). Transforming us military education for the agentic ai era: A national

framework for reskilling and workforce development.

[35] Kamalov, F., Calonge, D. S., Smail, L., Azizov, D., Thadani, D. R., Kwong, T., and Atif, A.

(2025). Evolution of ai in education: Agentic workﬂows. arXiv preprint arXiv:2504.20082.

[36] Katsarou, E., Wild, F., Sougari, A.-M., and Chatzipanagiotou, P. (2023). A systematic

review of voice-based intelligent virtual agents in eﬂeducation. International Journal of Emerging Technologies in Learning (iJET), 18(10):65–85.

[37] Kim, J., Yu, S., Detrick, R., Lin, X., and Li, N. (2025). Designing ai-powered learning:

Adult learners’ expectations for curriculum and human-ai interaction. Educational technology research and development, 73(6):3397–3421.

[38] Kishor, I., Mamodiya, U., Almaayah, M., Alqutaish, A., Shehab, R., and Aldhyani, T. H.

(2025). Agentic ai-enhanced virtual reality for adaptive immersive learning environments. Mesopotamian Journal of Computer Science, 2025:398–416.

[39] Kostopoulos, G., Gkamas, V., Rigou, M., and Kotsiantis, S. (2025). Agentic ai in education:

State of the art and future directions. IEEE Access.

[40] Kremantzis, M., Essien, A., Pantano, E., and Lythreatis, S. (2025). Uncovering the

generative ai (genai) to agentic ai (agai) shift for business school education. Journal of Global Information Management (JGIM), 33(1):1–21.

[41] Leal Filho, W., Sigahi, T. F., Skouloudis, A., Rampasso, I. S., and Anholon, R. (2026).

Beyond the hype: A sociotechnical perspective on ai’s potentials and constraints in bridging the gap to basic-needs sustainability in higher education institutions. Technological Forecasting and Social Change, 228:124681.

39

[42] Lee, D., Tiwari, M., and Miranda, B. (2025). Prompt infection: Llm-to-llm prompt

injection within multi-agent systems. In European Symposium on Research in Computer Security, pages 511–520. Springer.

[43] Lepage, A. and Collin, S. (2024). Preserving teacher and student agency: Insights from a

literature review. Creative applications of artiﬁcial intelligence in education, pages 17–34.

[44] Li, R. (2021). An artiﬁcial intelligence agent technology based web distance education

system. Journal of Intelligent & Fuzzy Systems, 40(2):3289–3299.

[45] Madleňák, R., Madleňáková, L., Cvacho, V., and Gachulinec, D. (2026). Ethical challenges

of artiﬁcial intelligence in higher education: A four-pillar student-activity framework for institutional governance. Education Sciences, 16(4):555.

[46] Masrek, M. N., Susantari, T., Mutia, F., Yuwinanto, H. P., and Atmi, R. T. (2024). Enabling

education everywhere: How artiﬁcial intelligence empowers ubiquitous and lifelong learning. Environment-Behaviour Proceedings Journal, 9(SI18):57–63.

[47] Misawa, T., Koizumi, A., Tamura, R., and Yoshimi, K. (2025). Exploring utilization

of generative ai for research and education in data-driven materials science. Science and Technology of Advanced Materials: Methods, 5(1):2535956.

[48] Mncube, D. W., Maphalala, M. C., and Mkhasibe, R. G. (2026). Artiﬁcial intelligence in

higher education: Supporting self-directed learning and student autonomy. Turkish Online Journal of Distance Education, 27(1):275–290.

[49] Murekian, O. and Sudarshan, S. (2026). Navigating agentic ai: a call for reimagined

academic literacies. Journal of Learning Development in Higher Education (JLDHE).

[50] Mustafa, G., Urooj, T., and Aslam, M. (2024). Role of artiﬁcial intelligence for adaptive

learning environments in higher education by 2030. Journal of Social Research Development, 5(3).

[51] National Institute of Standards and Technology (2023). Artiﬁcial intelligence risk man-

agement framework (ai rmf 1.0). Technical Report NIST AI 100-1, National Institute of Standards and Technology.

[52] National Institute of Standards and Technology (2024). Artiﬁcial intelligence risk manage-

ment framework: Generative artiﬁcial intelligence proﬁle. Technical Report NIST AI 600-1, National Institute of Standards and Technology.

[53] Nguyen, A., Gul, F., Dang, B., Huynh, L., and Tuunanen, T. (2025). Designing embodied

generative artiﬁcial intelligence in mixed reality for active learning in higher education. Innovations in Education and Teaching International, 62(5):1632–1647.

[54] Niu, W., Zhang, W., Zhang, C., and Chen, X. (2024). The role of artiﬁcial intelligence

autonomy in higher education: A uses and gratiﬁcation perspective. Sustainability, 16(3):1276.

[55] Portuguez-Castro, M. and Castillo-Martínez, I. M. (2026). GenAI-supported portfolio

assessment for complex thinking: a GPT-based innovation in business education. Front. Educ., 11:1729156.

[56] Rahman, P. and Mehnaz, S. (2024). International Journal for Multidisciplinary Research

(IJFMR). SSRN Journal.

40

[57] Sajja, R., Sermet, Y., Cikmaz, M., Cwiertny, D., and Demir, I. (2024). Artiﬁcial intelligence-enabled intelligent assistant for personalized and adaptive learning in higher education. Information, 15(10):596.

[58] Sajja, R., Sermet, Y., Cwiertny, D., and Demir, I. (2025). Integrating ai and learning

analytics for data-driven pedagogical decisions and personalized interventions in education. Technology, knowledge and learning, pages 1–31.

[59] Sapkota, R., Roumeliotis, K. I., and Karkee, M. (2026). AI Agents vs. Agentic AI:

A Conceptual Taxonomy, Applications and Challenges. Information Fusion, 126:103599. arXiv:2505.10468 [cs].

[60] Sari, H. E., Tumanggor, B., and Efron, D. (2024). Improving educational outcomes through

adaptive learning systems using ai. International Transactions on Artiﬁcial Intelligence, 3(1):21–31.

[61] Senowarsito, S. and Ardini, S. N. (2023). The Use of Artiﬁcial Intelligence to Promote

Autonomous Pronunciation Learning: Segmental and Suprasegmental Features Perspective. ijeltal, 8(2):133.

[62] Shi, L. (2026). Exploring students’ emotion recognition and teachers’ teaching feedback in

college foreign language classroom based on AFCNN model. Sci Rep, 16(1):5657.

[63] Stokkink, P. (nd). Educational assessment.

[64] Strielkowski, W., Grebennikova, V., Lisovskiy, A., Rakhimova, G., and Vasileva, T.

(2025). Ai-driven adaptive learning for sustainable educational transformation. Sustainable development, 33(2):1921–1947.

[65] Umar, U. and Purwanto, M. B. (2025). Ai and decision assistance for enhancing self-directed

learning. ETERNAL (English Teaching Journal), 16(2):457–465.

[66] Van Lier, M. (2023a). Introducing a four-fold way to conceptualize artiﬁcial agency.

Synthese, 201(3):85.

[67] Van Lier, M. (2023b). Understanding Large Language Models through the Lens of Artiﬁcial

Agency. pages 79–84.

[68] Wang, S. and Zhang, H. (2026). Pedagogical partnerships with generative ai in higher

education: how dual cognitive pathways paradoxically enable transformative learning. International Journal of Educational Technology in Higher Education, 23(1):11.

[69] Williams, P. (2025). Human–AI Learning: Architecture of a Human–AgenticAI Learning

System. Information, 16(12):1101.

[70] Williamson, B., Bayne, S., and Shay, S. (2020). The dataﬁcation of teaching in Higher

Education: critical issues and perspectives. Teaching in Higher Education, 25(4):351–365.

[71] Xiao, S. and Jin, M. (2025). Research on Educational AI Agents for Adult AIGC Competence Development. In Proceedings of the 2025 2nd International Symposium on Artiﬁcial Intelligence for Education, pages 390–397, Changsha China. ACM.

[72] Xu, D. and Wang, H. (2006). Intelligent agent supported personalization for virtual learning

environments. Decision Support Systems, 42(2):825–843.

41

[73] Yang, J., Shi, G., Zhu, W., and Sun, Y. (2025). Intelligent technologies in smart education:

a comprehensive review of transformative pillars and their impact on teaching and learning methods. Humanities and Social Sciences Communications, 12(1):1–15.

[74] Yang, S. and Evans, C. (2019). Opportunities and challenges in using ai chatbots in

higher education. In Proceedings of the 2019 3rd International Conference on Education and E-Learning, pages 79–83.

[75] Yekollu, R. K., Bhimraj Ghuge, T., Sunil Biradar, S., Haldikar, S. V., and Farook Mohideen

Abdul Kader, O. (2024). Ai-driven personalized learning paths: Enhancing education through adaptive systems. In International Conference on Smart data intelligence, pages 507–517. Springer.

[76] Yiting, Q., Khan, M. H., Shuqing, Z., SiYuan, C., and Choonkit, C. (2024). Enhancing

Sustainability in Academic Guidance: Develop an AI-DrivenAgent for Education 5.0. intij, 2024(1).

[77] Zawacki-Richter, O., Marín, V. I., Bond, M., and Gouverneur, F. (2019). Systematic

review of research on artiﬁcial intelligence applications in higher education – where are the educators? Int J Educ Technol High Educ, 16(1):39.

[78] Zeng, Y., Kang, J., and Piaw, C. Y. (2026). Behavioral mechanisms and learning outcomes

of University Students’ GAI-assisted learning in human-AI collaboration. PLoS One, 21(4):e0346696.

[79] Zhang, C. and Lu, Y. (2021). Study on artiﬁcial intelligence: The state of the art and future

prospects. Journal of Industrial Information Integration, 23:100224.

[80] Zhang, J. (nd). AI Agents in Education: Four Trends and a Practical Workﬂow.

[81] Zhao, J., Chapman, E., and Sabet, P. G. (2024). Generative ai and educational assessments:

A systematic review. Education Research and Perspectives, 51:124–155.

[82] Zhu, S. and Li, H. (2026). The application of large language models in meteorology

graduate research: current status, impact, and prospects. PLoS One, 21(4):e0347933.

A Paper-to-Dimension Mapping for the AIRA-G Synthesis

This appendix provides a transparent mapping between the papers included in the ﬁnal analytical corpus and the four synthesis dimensions used to develop the AIRA-G Framework. The purpose of this mapping is to make explicit how the reviewed literature supports the framework-oriented synthesis. It also responds to the methodological need to show that the proposed dimensions were derived from, and are traceable to, the reviewed literature rather than being introduced as standalone conceptual categories.

The mapping is organized around the four diagnostic dimensions of the AIRA-G Framework: autonomy and role boundary, instructional and assessment validity, human agency and cognitive calibration, and institutional governance and security. These dimensions correspond to the four tensions identiﬁed in the synthesis section. Because the reviewed literature is interdisciplinary, papers were not assigned to mutually exclusive categories. A single paper could contribute to more than one dimension, for example by addressing both adaptive learning and learner agency, or by connecting agentic AI with governance and security concerns.

42

The table also identiﬁes the evidence type associated with each paper. This distinction is important because empirical, conceptual, technical, review, and governance-oriented papers do not support the same type of claim. Empirical studies were used primarily to support claims about observed educational practices, student behaviour, faculty experience, or learning-related outcomes. Conceptual and theoretical papers were used to clarify constructs such as artiﬁcial agency, academic literacies, and sociotechnical adoption. Technical and security-oriented papers were used to identify risks related to prompt injection, tool access, auditability, and agentic system vulnerabilities. Governance and policy-oriented papers were used to support claims about institutional readiness, accountability, and responsible deployment.


> **Table 11 presents the paper-to-dimension mapping. A check mark indicates that a paper makes a**

> direct contribution to the corresponding AIRA-G dimension. The ﬁnal column brieﬂy states
the primary role of the paper in the synthesis. The mapping is intended as a methodological
transparency device rather than a full annotation of each source. It shows how the ﬁnal corpus
supports the development of the AIRA-G diagnostic lenses, autonomy taxonomy, risk–readiness
zones, and governance responses.

43

Note. A check mark indicates that the paper contributes directly to the corresponding AIRA-G synthesis dimension. The mapping is non-exclusive because several papers contribute to more than one dimension.

Van Lier [67] Conceptual / LLM agency ✓ ✓ Supports the interpretation of large language models

intelligence and responsible interpretation of GenAI

✓ ✓ ✓ Supports the GenAI baseline, cognitive-dependency

agency ✓ ✓ Supports the theoretical framing of artiﬁcial agency

education ✓ ✓ ✓ Supports the shift from reactive AI to agentic AI in

Floridi [25] Conceptual / ethics ✓ ✓ ✓ Provides conceptual grounding for agency without

systems create distinctive institutional and societal

education study ✓ Demonstrates discipline-speciﬁc use of LLMs in

harms ✓ ✓ Supports the argument that increasingly agentic

Zawacki-Richter et al. [77] Review ✓ ✓ Establishes the broader AI-in-higher-education


## architecture

✓
✓
✓
Supports agentic RAG and workﬂow-based AI

education-focused ✓ ✓ Supports discussion of GenAI use in teaching,

system ✓ ✓ Supports campus knowledge-agent use cases,

baseline and identiﬁes recurring educational

concern, assessment-integrity concern, and

graduate research and academic practice.

tutoring/teaching-assistant architectures.

institutional data access, secure agent

personalized and adaptive education.

through the lens of artiﬁcial agency.

communication, and auditability.

learning, and academic support.

and role-boundary analysis.

security Primary role in synthesis

policy-readiness gap.

application areas.

agency.

harms.


> **Table 11: Mapping of reviewed papers to AIRA-G synthesis dimensions**

Governance

and

agency and

calibration

Human

and assessment

Instructional

validity

Paper / citation key Evidence type Autonomy

boundary

and role

Jayaram and Bhat [32] Technical / institutional AI

Babar [9] Conceptual / agentic AI in

Chan et al. [13] Conceptual / algorithmic

Van Lier [66] Conceptual / artiﬁcial

English [20] Technical / education

education-focused

Zhu and Li [82] Domain-speciﬁc

Yang and Evans [74] Conceptual /

synthesis

Huo and Siau [30] Review /

The table continues in subsequent panels.

44

Note. A check mark indicates that the paper contributes directly to the corresponding AIRA-G synthesis dimension. The mapping is non-exclusive because several papers contribute to more than one dimension.

learning ✓ ✓ ✓ Supports AI-driven adaptive learning and sustainable

assistant ✓ ✓ Supports personalized and adaptive learning through

e-learning ✓ ✓ Supports earlier agent-based and adaptive e-learning

AI-enabled intelligent assistants in higher education.

Mustafa et al. [50] Education-focused study ✓ Supports the role of AI in personalized learning and

Hariyanto et al. [28] Education-focused study ✓ ✓ Supports adaptive and personalized learning claims

agents ✓ ✓ Grounds the personalization and adaptive-learning

dimension through pedagogical agents and learner

Cheung et al. [15] Education / tutoring agents ✓ ✓ ✓ Supports intelligent tutoring and agent-supported

conceptual paper ✓ ✓ Supports concerns about assessment validity and

AI-mediated evaluation of student competence.

agents ✓ ✓ Supports intelligent agent roles in educational

Zhao et al. [81] Review / assessment ✓ ✓ Supports GenAI and educational-assessment

improving educational support and learning

adaptive learning ✓ ✓ Supports adaptive learning as a pathway for

concerns, including academic integrity and

support, adaptive learning, and workﬂow

educational transformation.

in AI-supported education.

security Primary role in synthesis

instructional support.

assessment design.

online education.


> **Table 11: Mapping of reviewed papers to AIRA-G synthesis dimensions (continued)**


## architectures.

participation.

outcomes.

support.

Governance

and

agency and

calibration

Human

and assessment

Instructional

validity

Paper / citation key Evidence type Autonomy

boundary

and role

Strielkowski et al. [64] Conceptual / adaptive

Xu and Wang [72] Technical / intelligent

Apoki et al. [5] Review / pedagogical

Stokkink [63] Assessment-focused

Sajja et al. [57] Applied / intelligent

Sari et al. [60] Education-focused /

El Fazazi et al. [19] Technical / adaptive

The table continues in subsequent panels.

45

Note. A check mark indicates that the paper contributes directly to the corresponding AIRA-G synthesis dimension. The mapping is non-exclusive because several papers contribute to more than one dimension.

literacies ✓ ✓ Supports the claim that agentic AI requires rethinking

Delcker et al. [16] Empirical study ✓ Supports AI competence as a predictor of AI-tool use

expectations ✓ ✓ Supports adult learners’ expectations for AI-powered

Education 5.0 ✓ ✓ ✓ ✓ Supports AI-driven academic guidance and the need

agency, usefulness, autonomy support, self-eﬃcacy,

competence development ✓ ✓ Supports adult AIGC competence development and

human–agentic-AI interaction rather than one-way

support ✓ ✓ Supports the idea of AI as an instructor-support or

workload support while preserving human review.

institutional study ✓ ✓ ✓ Supports the sociotechnical interpretation of AI

Alqurni [4] Empirical study ✓ ✓ Supports the relationship between perceived AI

conceptual paper ✓ Supports AI-enabled self-directed learning and

Balikci et al. [10] Applied education study ✓ ✓ Supports AI-assisted task analysis and faculty

for governance in advising-related systems.

learning and human–AI interaction design.

adoption in higher-education institutions.

learning architecture ✓ ✓ ✓ Supports the interpretation of learning as

academic literacies and student agency.

AI-supported learning readiness.

instructor-exoskeleton system.

and self-learning behaviour.

security Primary role in synthesis

in learning processes.

student autonomy.

content delivery.


> **Table 11: Mapping of reviewed papers to AIRA-G synthesis dimensions (continued)**

Governance

and

agency and

calibration

Human

and assessment

Instructional

validity

Paper / citation key Evidence type Autonomy

boundary

and role

Williams [69] Conceptual / human–AI

Murekian and Sudarshan [49] Conceptual / academic

Yiting et al. [76] Academic guidance /

August and Tsaima [8] Education / faculty

Kim et al. [37] Empirical / learner

Mncube et al. [48] Education-focused

Leal Filho et al. [41] Sociotechnical /

Xiao and Jin [71] Education / AI

The table continues in subsequent panels.

46

Note. A check mark indicates that the paper contributes directly to the corresponding AIRA-G synthesis dimension. The mapping is non-exclusive because several papers contribute to more than one dimension.

application vulnerability, and security governance for

digital agents ✓ ✓ Supports the discussion of intelligent digital agents as

education remains institutionally underdeveloped and

Acharya et al. [2] Conceptual / AI evolution ✓ ✓ Supports the transition from conventional AI systems

education futures ✓ ✓ Supports AI-enabled future learning models, lifelong

adoption ✓ ✓ Supports the role of AI in extended, continuous, and

education ✓ ✓ Supports AI-enabled lifelong learning, self-directed

reskilling, and institutional capacity-building issue.

Zhang [80] Technical / AI agents ✓ ✓ ✓ Supports the discussion of AI agents in education,

Joshi et al. [33] Policy / governance study ✓ Supports the claim that GenAI guidance in higher

including system roles, workﬂow integration, and

review ✓ ✓ ✓ ✓ Supports the broader interpretation of agentic AI

capabilities, opportunities, risks, and governance

workﬂow-participating systems with educational

Duarte et al. [17] Technical / security review ✓ ✓ Supports prompt-injection risk, LLM-integrated

learning, and self-directed learner development.

policy ✓ ✓ ✓ Supports agentic AI as a workforce-readiness,

governance-vulnerability argument in higher

dataﬁcation ✓ ✓ ✓ Supports the institutional dataﬁcation and

learning, and learner autonomy concerns.

toward more agentic and autonomous AI

requires more mature governance.

adaptive learning environments.

security Primary role in synthesis

institutional use cases.

agentic systems.


> **Table 11: Mapping of reviewed papers to AIRA-G synthesis dimensions (continued)**

conﬁgurations.

education.

needs.

roles.

Governance

and

agency and

calibration

Human

and assessment

Instructional

validity

Paper / citation key Evidence type Autonomy

boundary

and role

Goyal [26] Conceptual / agentic AI

Arias et al. [6] Lifelong learning / AI

Yekollu et al. [75] Lifelong learning / AI

Joshi [34] Workforce readiness /

Faught et al. [23] Technical / intelligent

Fidalgo and Thormann [24] Lifelong learning /

Williamson et al. [70] Sociotechnical /

The table continues in subsequent panels.

47

Note. A check mark indicates that the paper contributes directly to the corresponding AIRA-G synthesis dimension. The mapping is non-exclusive because several papers contribute to more than one dimension.

learning ✓ ✓ Supports AI-enabled ubiquitous and lifelong learning,

analytics, and the need to govern learner-related data.

Eaton et al. [18] Conceptual / AI education ✓ ✓ ✓ Provides early grounding for treating AI education as

teaching-evaluation criteria and instructional-quality

GenAI ✓ ✓ ✓ Supports embodied and active-learning applications

Senowarsito and Ardini [61] Education-focused study ✓ ✓ Supports the use of AI for autonomous learning and

education study ✓ ✓ Demonstrates GenAI use in research and education

especially access-oriented and continuous-learning

analytics ✓ ✓ ✓ Supports AI-enabled classroom feedback, aﬀective

a curricular, ethical, and interdisciplinary concern.

agentic AI ✓ ✓ ✓ ✓ Supports the extension of agentic AI into adaptive

systems ✓ ✓ ✓ Supports the role of intelligent agents in distance

immersive learning environments and associated

language-learning contexts and learner-support

agents ✓ ✓ ✓ Supports the use of intelligent virtual agents in

education and AI-supported learning systems.

of generative AI in higher education contexts.

learning ✓ ✓ Supports the role of AI in lifelong learning,

continuous skill development, and adaptive

within data-driven scientiﬁc domains.

evaluation ✓ Provides background for considering

learner-centred skill development.

concerns in higher education.

security Primary role in synthesis

governance concerns.

educational support.


> **Table 11: Mapping of reviewed papers to AIRA-G synthesis dimensions (continued)**

environments.

use cases.

Governance

and

agency and

calibration

Human

and assessment

Instructional

validity

Paper / citation key Evidence type Autonomy

boundary

and role

Katsarou et al. [36] Systematic review / virtual

Nguyen et al. [53] Technical / mixed-reality

Masrek et al. [46] Conceptual / ubiquitous

Li [44] Conceptual / intelligent

Kishor et al. [38] Technical / immersive

Shi [62] Empirical / classroom

Zhang and Lu [79] Conceptual / lifelong

Hadad et al. [27] Empirical / teaching

Misawa et al. [47] Domain-speciﬁc

The table continues in subsequent panels.

48

Note. A check mark indicates that the paper contributes directly to the corresponding AIRA-G synthesis dimension. The mapping is non-exclusive because several papers contribute to more than one dimension.

documentation, responsibility allocation, monitoring,

Technology [51] Governance framework ✓ Provides external governance grounding through the

education and supports the historical transition from

governance ✓ ✓ Supports risk-based classiﬁcation of AI systems and

information integrity, misuse, data privacy, security,

proﬁle ✓ ✓ ✓ Supports GenAI-speciﬁc risk concerns, including

educational transformation and learner-support

govern–map–measure–manage logic of AI risk

multidisciplinary ✓ ✓ Supports the broader discussion of AI-enabled

tool use to system-level educational change.

education ✓ ✓ Provides background on the arrival of AI in

reinforces the need for stronger controls in

education-related high-impact use cases.

standard ✓ Supports institutional AI management,

and continuous improvement.

and human–AI interaction.

security Primary role in synthesis


> **Table 11: Mapping of reviewed papers to AIRA-G synthesis dimensions (continued)**

management.

possibilities.

Governance

and

agency and

calibration

Human

and assessment

Instructional

validity

Paper / citation key Evidence type Autonomy

boundary

and role

Technology [52] Governance / GenAI risk

iso [1] AI management-system

European Union [22] Regulatory / risk-based

Rahman and Mehnaz [56] Education-focused /

Chen et al. [14] Conceptual / AI in

This panel completes the paper-to-dimension mapping.

European Parliament and Council of the

National Institute of Standards and

National Institute of Standards and

49

B Outcome-Oriented Tier-Based Application of the AIRA-G Framework in Indian Higher Education

This appendix demonstrates how the AIRA-G Framework can be used as a practical decision- support mechanism for higher-education leadership. The illustration is situated in the Indian higher-education context and uses a Computer Science programme as the common deployment setting. The purpose is not to report an empirical implementation, but to show how the proposed framework can generate concrete decision outputs for institutional leaders, department heads, teaching committees, instructional designers, and AI governance bodies.

Terms like Tier 1, Tier 2 and Tier 3 are heuristic categories borrowed from Indian higher- education discourse. They are not indicative of a sanctioned ranking, or regulatory category, or formal banding. These tiers loosely describe institutional proﬁles that may vary in students’ preparedness, faculty capacity, digital readiness, research ecosystem, teaching-support systems, assessment culture and governance maturity. I use this weak tier-based illustration simply to argue that agentic AI integration will not look the same across institutions. The right degree of agentive AI might mean the same AI system’s controlled advanced deployment at one institution, guided pilot deployment at another, and merely low-autonomy support at a third.

Our agentic AI use case is an AI teaching and advising assistant for Computer Science programmes. Capabilities include answering course queries, supporting students in programming practice, oﬀering debugging hints, recommending learning resources, helping faculty teachers author formative material, advising on projects, and, in high-end conﬁgurations, integrating with learning management systems or student-performance dashboards. Computer Science programmes were chosen as the use case for illustrating AIRA-G because they will likely see both high usefulness and high risk from agentic AI. Students will likely beneﬁt from AI-enabled coding, explanation, debugging, and self-paced learning but might also use AI to circumvent thinking, plug in full code, outsource homework, or obfuscate authorship.

B.1 Decision Logic and Expected Outputs

The AIRA-G Framework is designed to produce tangible institutional outputs rather than only conceptual reﬂection. In this appendix, the framework is applied as a staged decision workﬂow. Each stage produces an intermediate output that informs the next stage and ultimately leads to a ﬁnal deployment judgement. Table 12 summarizes the output logic.

The key point is that AIRA-G does not produce a single yes/no answer. It produces a structured institutional judgement. The ﬁnal decision depends on the speciﬁc use case, autonomy level, data access, assessment consequence, student and faculty readiness, and governance capacity.

B.2 Use-Case Speciﬁcation and Autonomy Scope

The ﬁrst output of the framework is a use-case speciﬁcation sheet. For the present illustration, the proposed system is an agentic AI teaching and advising assistant for Computer Science programmes. Table 13 deﬁnes the possible scope of the system.

The use-case speciﬁcation shows that a single AI assistant can range from a low-risk course FAQ tool to a high-risk academic decision-support system. Therefore, AIRA-G evaluates the enabled conﬁguration, not the product label.

50


> **Table 12: Outcome-oriented application of the AIRA-G Framework**

AIRA-G stage Evaluation focus Tangible output Leadership use

Use-case deﬁnition What is the AI system expected to do, who will use it, and which academic processes will it aﬀect?

Use-case speciﬁcation sheet Deﬁnes the scope of review and prevents generic approval or rejection.

Autonomy classiﬁcation What level of autonomy does the

Autonomy-level classiﬁcation Determines minimum oversight, approval gates, and restrictions.

system exercise within academic workﬂows?

Diagnostic evaluation How does the system perform across autonomy, instructional validity, human agency, and governance/security lenses?

Four-lens diagnostic proﬁle Identiﬁes strengths, risks, missing safeguards, and required evidence.

Risk–readiness classiﬁcation

What is the system’s risk level and is the institution ready to govern it?

Zone assignment: A, B, C, or D Determines whether to permit, pilot, restrict, or redesign the system.

Governance response What safeguards, responsibilities, approvals, and controls are required?

Governance action plan Converts evaluation into deployment conditions.

Monitoring and review What indicators will be monitored after deployment and when should reclassiﬁcation occur?

Monitoring and review protocol Supports continuous improvement, reclassiﬁcation, and accountability.

Note. The table shows how AIRA-G produces decision outputs that can be used by institutional leadership and academic governance bodies.

B.3 Tier-Based Institutional Readiness Proﬁle

The second step is to identify how institutional context aﬀects the usefulness and risk of the AI system. Table 14 provides a heuristic characterization of Tier 1, Tier 2, and Tier 3 institutions in the Indian higher-education context.

It is important to note that this proﬁle does not imply that higher readiness equates to lower risk. While tier 1 institutions may be more ready to implement more advanced agentic AI systems,

this readiness can come with both increased likelihood and capability of misuse, as well as more nuanced requirements for governance. Conversely, while tier 3 institutions may not have the readiness necessary for use cases requiring deep integration into the learning environment, less autonomous AI tools may still be useful for remedial learning, explaining concepts, and supporting faculty.

B.4 AIRA-G Diagnostic Proﬁle by Tier

The third deliverable is a diagnostic proﬁle assessing each tier against the four lenses of AIRA-G. Table 15 highlights the results of this comparative analysis.

Simply put, this diagnostic proﬁle makes it clear that the AIRA-G Framework is more than just a risk registry. It can guide institutions in determining how deeply embedded agentic AI should be utilized, what safety mechanisms need to be implemented, and where certain functionalities should be curtailed.

B.5 Risk–Readiness Classiﬁcation and Deployment Strategy

The fourth output is a risk–readiness classiﬁcation. Table 16 converts the diagnostic proﬁle into a deployment strategy. The table identiﬁes suitable initial use cases, required safeguards, functions to avoid, and suggested AIRA-G zones for each tier.

The deployment strategy shows that leadership should not ask only whether the institution

51


> **Table 13: Use-case speciﬁcation for an agentic AI teaching and advising assistant**

Use-case attribute Illustrative speciﬁcation

System type Agentic AI teaching and advising assistant for Computer Science programmes.

Target courses Programming, data structures, algorithms, databases, machine learning, cybersecurity, software engineering, and project-based courses.

Low-autonomy functions Course FAQ answering, concept explanation, syllabus queries, approved resource recommendation, and formative practice-question generation.

Moderate-autonomy functions Debugging hints, personalized study-plan suggestions, formative feedback drafting, learning-path recommendation, and common-doubt analytics.

High-autonomy functions LMS-integrated performance tracking, student-risk ﬂagging, academic advising recommendations, automated feedback analytics, and assessment support.

Restricted functions Autonomous grading, automatic student classiﬁcation, academic progression decisions, disciplinary recommendations, and unsupervised access to student records.

Main expected beneﬁts Timely student support, scalable formative guidance, faculty workload reduction, improved feedback availability, and personalized learning support.

Main expected risks Cognitive oﬄoading, code substitution, academic-integrity violations, inaccurate advice, privacy leakage, prompt injection, weak accountability, and reduced human judgement.

Output. This use-case speciﬁcation deﬁnes what is being evaluated. The same system may receive diﬀerent AIRA-G classiﬁcations depending on which functions are enabled.

wants agentic AI. It should ask which level of integration is appropriate for the institution’s current readiness. For Tier 1 institutions, the primary challenge is controlling sophisticated and high-impact use cases. For Tier 2 institutions, the primary challenge is phased adoption with faculty training and policy consistency. For Tier 3 institutions, the primary challenge is building basic readiness before introducing deeper agentic capabilities.

B.6 Governance and Monitoring Outputs

The ﬁfth output is a governance and monitoring plan. This output is important because agentic AI risk is not static. A system initially deployed as a low-risk formative assistant may become higher risk if it gains access to student records, begins recommending interventions, or becomes embedded in assessment workﬂows. Table 17 summarizes governance and monitoring requirements across tiers.

This stage converts the AIRA-G classiﬁcation into operational controls. It also prevents one-time approval from becoming permanent authorization. Any expansion of autonomy, data access, assessment inﬂuence, or advising inﬂuence should trigger reclassiﬁcation.

B.7 Leadership Decision Matrix

The ﬁnal output is a leadership-facing decision matrix. Table 18 summarizes the recommended adoption depth, primary beneﬁt, main risk, governance priority, and ﬁnal judgement for each tier.

This matrix is the principal practical output of the appendix. It demonstrates how the AIRA-G Framework converts institutional context into diﬀerentiated deployment decisions.

B.8 Illustrative Final Report for Leadership

A leadership-facing report generated through the AIRA-G Framework may contain the following structured judgement.

52


> **Table 14: Heuristic characterization of institutional tiers for agentic AI readiness**

Institutional factor Tier 1 proﬁle Tier 2 proﬁle Tier 3 proﬁle

Student proﬁle Highly competitive students with strong digital ﬂuency, programming exposure, and self-learning capacity

Mixed preparedness; moderate digital ﬂuency; variable programming conﬁdence

Highly heterogeneous preparedness; limited digital ﬂuency for some students; stronger need for guided support

Faculty ecosystem Research-active faculty; stronger exposure to advanced AI tools; project and research culture

Teaching-focused or mixed teaching–research faculty; variable AI adoption

Heavy teaching loads; limited exposure to AI-enabled pedagogy; greater need for faculty development

Teaching support structure Availability of teaching assistants, PhD scholars, research labs, and project mentors

Limited or uneven teaching-assistant support

Minimal TA/PhD support; faculty often manage teaching, support, and evaluation directly

Weak or inconsistent LMS use, constrained labs, limited IT support, and possible connectivity issues

Digital infrastructure Stronger LMS use, coding platforms, labs, institutional IT, and technical support

Functional but uneven LMS and lab infrastructure

Often exam-centric; limited ﬂexibility for viva, project review, or process-based assessment

Mix of exams, labs, assignments, and projects; moderate redesign capacity

Assessment culture Multiple assessment modes: assignments, labs, projects, vivas, open-ended tasks, and exams

Governance maturity Existing academic committees, technical capacity, and stronger ability to pilot and audit systems

Emerging governance structures; policies may be reactive or unevenly implemented

Low governance capacity; requires simple templates, external support, and low-risk adoption

Agentic AI opportunity Advanced learning support, research assistance, coding labs, and course-speciﬁc agents

Remedial support, access improvement, language support, and faculty assistance

Faculty support, formative learning, guided student assistance, and workload reduction

Agentic AI risk Sophisticated misuse, hidden AI use, over-automation, and complex governance burden

Uneven AI literacy, copying, overreliance, and inconsistent policy enforcement

Blind dependence, hallucination acceptance, weak veriﬁcation, limited oversight, and data-protection gaps

Note. The tier typology is heuristic and intended only to illustrate how institutional context aﬀects agentic AI deployment strategy.

The ﬁnal report demonstrates the practical value of the AIRA-G Framework. It does not simply state that agentic AI is beneﬁcial or risky. Instead, it identiﬁes where adoption is appropriate, what level of integration is suitable, what safeguards are required, and which use cases should remain restricted.

53


> **Table 15: Tier-wise AIRA-G diagnostic proﬁle for agentic AI integration**

AIRA-G lens Tier 1 diagnostic judgement Tier 2 diagnostic judgement Tier 3 diagnostic judgement

Should begin with low to moderate autonomy; human approval must remain central

Autonomy and role boundary

Can support moderate to advanced autonomy if roles are clearly bounded, reversible, and auditable

Should begin with low autonomy only; avoid proactive decision-making and system integration

Moderate capacity; requires templates and faculty training for AI-aware assessment

Stronger capacity for assessment redesign, viva, code walkthroughs, and process-based evaluation

Low to emerging capacity; avoid AI involvement in graded assessment initially

Instructional and assessment validity

Human agency and cognitive calibration

Students can use advanced AI productively, but sophisticated misuse may be diﬃcult to detect

Uneven AI literacy creates risk of dependency, copying, and inconsistent use

High risk of blind reliance; AI literacy and guided use must precede broader adoption

Low capacity; require simple, low-risk tools and minimal data access

Emerging capacity; governance procedures need standardization before deeper integration

Institutional governance and security

Moderate to high capacity for access control, pilots, audits, and technical review

Overall diagnostic judgement

Ready for controlled advanced integration

Ready for guided phased adoption

Ready only for low-autonomy assistive use initially

Output. The diagnostic proﬁle identiﬁes the likely usefulness, risk, and governance requirements of agentic AI deployment across tiers.


> **Table 16: Tier-speciﬁc risk–readiness classiﬁcation and deployment strategy**

Tier Recommended initial use cases Required governance controls Avoid initially Suggested AIRA-G zone

Tier 1 Course-speciﬁc agentic RAG assistant; programming lab assistant; project/research support; faculty-approved formative feedback analytics

Autonomous grading, unreviewed student proﬁling, automatic academic progression advice

Zone B–C

Audit logs, prompt-injection testing, role-based access, faculty-approved knowledge base, AI-use disclosure, viva/code walkthrough, periodic review

Zone A–B; limited Zone C

Automated advising, summative assessment support, unrestricted code generation for graded tasks

Tier 2 Course FAQ assistant; formative teaching assistant; lab doubt-resolution assistant; faculty productivity support; controlled assignment-support bot

Faculty oversight, standard AI-use guidelines, limited LMS integration, AI-literacy training, human review of outputs

Tier 3 Concept explanation bot; remedial-learning assistant; language-support assistant; faculty lesson-planning support; basic academic helpdesk

LMS-data integration, grading, proﬁling, advising automation, high-autonomy agents

Zone A initially

Approved content only, no sensitive data access, simple disclosure, faculty-supervised use, basic AI-literacy orientation

Output. The suggested zone indicates the recommended level of deployment permission. A higher zone requires stronger governance and should not be interpreted as inherently more desirable.

54


> **Table 17: Governance and monitoring outputs for tier-wise deployment**

Tier Governance action plan Monitoring indicators Reclassiﬁcation trigger

Tier 1 Establish course-level and institutional approval, audit logs, access control, security testing, faculty oversight, and AI-use disclosure

AI-use patterns, assignment similarity, code-explanation quality, prompt-injection attempts, faculty review burden, student complaints

Reclassify to stricter control if the system accesses new data sources, inﬂuences assessment, or generates academic interventions

Tier 2 Use limited pilots, faculty-approved content, standard acceptable-use policy, student orientation, and periodic review

Student dependence, misuse incidents, faculty workload, quality of AI feedback, uneven adoption across courses

Reclassify before LMS integration, advising support, or personalized intervention recommendations

Tier 3 Restrict to approved content, low-autonomy use, faculty-supervised access, simple disclosure, and AI-literacy support

Access issues, hallucination acceptance, student overreliance, faculty readiness, infrastructure constraints

Do not move beyond Zone A until basic governance, faculty training, and student AI literacy are established

Output. The governance and monitoring plan supports periodic review, reclassiﬁcation, and continuous improvement.


> **Table 18: Leadership decision matrix generated through the AIRA-G Framework**

Decision aspect Tier 1 judgement Tier 2 judgement Tier 3 judgement

Overall readiness High readiness, but governance complexity is also high

Moderate readiness with uneven implementation capacity

Low to emerging readiness; requires foundational preparation

Recommended adoption depth Advanced but controlled integration

Guided and phased adoption Low-autonomy assistive adoption

Best initial use case Agentic RAG teaching assistant, coding lab assistant, project/research support

Course FAQ bot, formative support assistant, faculty-approved teaching assistant

Remedial learning bot, concept explanation assistant, language-support assistant

Most valuable beneﬁt Scalable personalization, advanced learning support, research/project productivity

Faculty workload reduction, student support, standardization of routine guidance

Access improvement, remedial support, basic academic assistance

Main risk Sophisticated misuse, hidden AI use, over-automation, high governance burden

Uneven AI literacy, policy inconsistency, overreliance, copying

Blind dependence, hallucination acceptance, weak veriﬁcation, limited oversight

Faculty training, standard guidelines, limited integration, human review

AI literacy, approved content, no sensitive data access, simple governance templates

Governance priority Auditability, security testing, role-based access, assessment redesign, appeal mechanisms

Final deployment judgement Deploy under controlled governance with strong audit and human oversight

Pilot before scaling; expand only after faculty and governance capacity improve

Start with low-risk support only; build capacity before deeper integration

Output. The matrix converts AIRA-G evaluation into leadership-facing deployment guidance.

55


> **Table 19: Illustrative ﬁnal report for leadership decision-making**

Report component Illustrative judgement

Proposed system Agentic AI teaching and advising assistant for Computer Science programmes.

Institutional sensitivity Deployment eﬀectiveness depends strongly on student capability, faculty readiness, digital infrastructure, assessment culture, and governance maturity.

Tier 1 decision Permit controlled advanced integration under Zone B–C with audit logs, role-based access, assessment redesign, and human approval for consequential actions.

Tier 2 decision Begin with guided pilots under Zone A–B; expand only after faculty training, policy standardization, and governance controls are established.

Tier 3 decision Limit initial deployment to Zone A low-autonomy support; focus on remedial learning, faculty assistance, and AI literacy before deeper integration.

Cross-tier restriction Do not permit autonomous grading, unreviewed student proﬁling, academic progression decisions, or high-stakes advising automation without strong validity, auditability, and appeal mechanisms.

Required safeguards AI-use disclosure, faculty oversight, data minimization, security review, prompt-injection testing where relevant, audit logs, and periodic review.

Final leadership judgement Agentic AI adoption should be tier-sensitive, use-case-speciﬁc, and governance-calibrated. The same AI system may be appropriate as a formative assistant in one context and inappropriate as an autonomous decision system in another.

Output. A concise leadership report that converts AIRA-G evaluation into institutional decision guidance.

56
