---
workspace_id: "SCI-000134"
doi: null
title: "How Software Engineering Students Use LLMs to Write Research Papers: An Experience Report"
year: 2026
extraction_engine: "pymupdf"
---
# 2026 Santos How Software Engineering Students Use LL

How Software Engineering Students Use LLMs to

Write Research Papers: An Experience Report

Ronnie de Souza Santos1,2, Maria Teresa Baldassarre3, Cleyton Magalhães4,

and Italo Santos5


## 1 University of Calgary, Canada

2 CESAR School, Brazil
3 University of Bari, Italy
4 Universidade Federal Rural de Pernambuco (UFRPE), Brazil
5 University of Hawai‘i at M¯anoa, USA
ronniedesouzasantos@ucalgary.ca, ress@cesar.school,
mariateresa.baldassarre@uniba.it, cleyton.vanut@ufrpe.br,

arXiv:2606.05114v2  [cs.SE]  5 Jun 2026

isantos3@hawaii.edu


## Abstract. Large language models are now part of software engineering

education, including activities involving empirical software engineering
and evidence synthesis. This paper reports an educational experience in-
volving the integration of reflective LLM use into an empirical methods
assignment in a third-year software architecture course. Students were
asked to develop a short research paper using either a rapid review or
a gray literature review methodology and to disclose how LLMs were
used throughout the assignment. We analyzed 146 student disclosure
statements using a cross-analysis process combining LLM-assisted cat-
egorization with manual verification and refinement by the researchers.
The reflections describe how students incorporated LLMs during activi-
ties such as brainstorming, methodological clarification, organization of
findings, and writing refinement, while also reporting concerns regarding
inaccuracies and verification of generated content. This experience report
discusses lessons learned and educational implications for integrating AI-
assisted technologies into empirical software engineering education.

Keywords: Large Language Models · Empirical Software Engineering · Undergraduate Students

1 Introduction

Large language models (LLMs) are increasingly present in educational settings, supporting activities such as tutoring, feedback generation, content creation, and writing assistance [7, 13, 14]. In software engineering education, these tools are now part of students’ everyday academic workflows, including programming activities, brainstorming, information synthesis, and academic writing [2, 1, 6]. At the same time, their growing adoption has raised questions regarding authorship, reliability, critical thinking, academic integrity, and the role of AI in learning processes [16, 3, 11, 8].

2 R. de Souza Santos et al.

Current discussions in software engineering education increasingly argue that LLMs should not be treated solely as coding assistants or productivity tools, but rather as technologies that require critical and reflective engagement [5, 9, 2]. In this context, educators are beginning to rethink how assignments are designed, how students are encouraged to interact with AI systems, and how responsible use can be incorporated into teaching practices. These discussions become par- ticularly relevant in empirical software engineering education, where students are expected to develop skills related to evidence synthesis, methodological rea- soning, critical analysis, and communication [4, 15, 10, 12].

This paper reports our experience integrating reflective and transparent LLM use into an empirical methods assignment in a third-year software architecture course. Students were allowed to use LLMs throughout the process of developing a short research paper, provided that they disclosed how the tools were used. The activity aimed not only to support students during the writing process but also to encourage reflection on the role of AI tools in academic work. To bet- ter understand how students interacted with LLMs in this educational setting, we analyzed 146 disclosure statements written after completion of the assign- ment. These statements described how students used LLMs, which aspects of the writing process were supported by the tools, and which benefits and limi- tations they perceived. Rather than evaluating the effectiveness of LLMs, our goal was to understand how students appropriated these technologies during an empirical writing activity and what this experience suggests for software engi- neering education. The observations presented in this paper provide practical insights for educators interested in incorporating LLMs into empirical software engineering assignments. In particular, our experience suggests the importance of transparency, critical verification, and explicit guidance when integrating AI- assisted technologies into academic work.

From this introduction, this paper is organized as follows. Section 2 discusses empirical methods teaching in software engineering education. Section 3 presents the educational context and the assignment structure. Section 4 reports the main observations from student disclosures. Section 5 discusses lessons learned and implications for education. Finally, Section 6 concludes the paper.

2 Teaching Empirical Methods

Teaching empirical methods in software engineering is widely recognized as im- portant for helping students understand how to evaluate technologies and prac- tices systematically and using evidence rather than intuition alone [4, 15]. As empirical research has become an established component of software engineering, students are increasingly expected to understand how to design studies, collect and analyze data, and interpret findings in order to support decision making [4, 10]. Methods such as controlled experiments, case studies, surveys, and evidence synthesis approaches provide opportunities for students to develop these com- petencies while strengthening their understanding of software engineering prac- tice [10]. Beyond methodological knowledge, empirical methods education seeks

How Software Engineering Students Use LLMs to Write Research Papers 3

to cultivate an evidence based mindset in future software engineers. Students are expected not only to understand how empirical studies are conducted, but also how empirical evidence can be used to evaluate technologies, compare alter- natives, justify decisions, and critically assess claims reported in both research and practice [15, 10]. This objective has become increasingly relevant as software engineering continues to evolve rapidly and practitioners are frequently required to assess new tools, development approaches, and emerging technologies.

To support these learning objectives, educators have adopted a variety of ped- agogical approaches, including dedicated empirical software engineering courses, the integration of empirical assignments into broader software engineering cur- ricula, and project based activities that expose students to different stages of the research process [15, 12]. Such activities commonly involve study design, data analysis, interpretation of findings, and reflection on threats to validity [4, 10]. Through these experiences, students engage with both the theoretical and practical dimensions of empirical research [12]. A recurring recommendation in the literature is that empirical methods should be taught through authentic experiences rather than through lectures alone [4, 15, 10]. Students benefit from participating in the complete empirical cycle, including identifying research ques- tions, selecting appropriate methods, collecting and analyzing data, interpreting results, and communicating findings. Project based assignments allow students to experience the challenges associated with conducting empirical investigations while developing practical skills that are difficult to acquire through theoretical instruction alone [4, 10].

Another important aspect concerns the development of critical thinking and reflection skills. Empirical software engineering requires students to evaluate the quality of evidence, identify limitations in study designs, recognize threats to va- lidity, and understand the contextual nature of software engineering findings [15, 12]. Consequently, educational activities often encourage students to critically examine published studies, compare alternative methodological approaches, and reflect on the implications of empirical results for practice [10]. Recent discus- sions have also emphasized the importance of active learning approaches when teaching empirical software engineering [12]. Rather than positioning students as passive recipients of methodological concepts, these approaches encourage partic- ipation through discussions, collaborative activities, peer learning, and practical exercises. Such strategies provide opportunities for students to connect method- ological concepts with realistic software engineering problems and support a deeper understanding of empirical reasoning.

Despite their educational value, empirical methods courses present several challenges. Students often enter these courses with varying levels of methodolog- ical and software engineering knowledge, requiring instructors to balance con- ceptual foundations with practical application [12]. In addition, educators must design activities that promote learning while maintaining realistic expectations regarding research outcomes and project scope [15]. Balancing methodological rigor with accessibility can be particularly challenging when students have lim- ited prior experience with research methods, statistics, or academic writing [10].

4 R. de Souza Santos et al.

Nevertheless, empirical activities have generally been reported as valuable learn- ing experiences and remain an important component of software engineering education [4, 10]. By combining methodological instruction with hands on in- vestigation and critical reflection, empirical methods courses can help students develop the skills needed to evaluate evidence, reason about software engineering practices, and make informed decisions throughout their professional careers.

3 Educational Context and Experience Report

This paper reports our experience incorporating reflective and transparent LLM use into an empirical methods assignment in a third-year undergraduate soft- ware architecture course. Rather than evaluating the effectiveness of LLMs them- selves, our goal was to better understand how students appropriated these tools while developing academic work and what this experience suggests for software engineering education.

3.1 Educational Context

The experience was conducted in a third-year undergraduate software archi- tecture course within a software engineering program. As part of the course activities, students were asked to write a short 2–3-page paper investigating a topic related to software architecture or software design. Students were required to define a research question and apply either a Rapid Review or a Grey Litera- ture Review methodology following structured instructional guidelines provided during the course. The assignment was designed to expose students to forms of evidence that software engineers commonly encounter when investigating tech- nologies, practices, and design decisions. Rather than conducting original empir- ical studies, students worked with existing evidence sources and were asked to identify patterns, compare perspectives, and construct evidence-informed con- clusions. This approach allowed students to experience key stages of empirical inquiry while keeping the activity feasible within the scope of a regular under- graduate course.

Students could choose between a Rapid Review and a Grey Literature Review depending on their interests and the nature of their research question. The Rapid Review option exposed students to peer-reviewed research and encouraged en- gagement with how software engineering knowledge is reported, evaluated, and synthesized. The Grey Literature Review option focused on practitioner discus- sions and enabled students to investigate industry experiences, challenges, and opinions that are often not represented in academic publications. Providing both options allowed students to explore different forms of evidence while recogniz- ing that software engineering knowledge is produced by both researchers and practitioners. For the Rapid Review, students were instructed to systematically identify and analyze at least 15 peer-reviewed studies published in reputable software engineering venues within the last 10 years. In the Grey Literature Review, students were asked to analyze at least 30 practitioner-oriented online

How Software Engineering Students Use LLMs to Write Research Papers 5

posts from sources such as StackExchange, Quora, and Dev.to. In both activities, students were expected to synthesize findings, organize evidence into categories or themes, and communicate their results using an academic structure. The assignment therefore required students to move beyond summarization by iden- tifying recurring observations, contrasting viewpoints, and broader implications emerging from the collected evidence.

Students were explicitly allowed to use LLMs throughout the assignment development process. This included support for brainstorming, refining research questions, improving writing clarity, organizing findings, and understanding method- ological concepts. However, students were instructed that the papers should re- flect their own reasoning and synthesis rather than fully AI-generated content. To encourage transparency and reflection, students were required to include a short disclosure statement describing whether and how LLMs were used during the assignment. These disclosures were not graded and were included as part of broader course guidelines regarding AI use across assignments.

3.2 Reflection Collection

The disclosure statements were collected only after the course had concluded and final grades had been released. This procedure ensured that no academic consequences could be associated with the disclosures and that students could reflect on their experiences without affecting evaluation outcomes. To preserve anonymity, two Teaching Assistants extracted the disclosure statements from the submitted assignments, removed identifying information, and organized the material into a shared spreadsheet. The statements were inserted in randomized order to reduce the possibility of associating disclosures with specific students. In total, 146 anonymized statements were compiled for reflection and analysis.

3.3 Cross Analysis of Student Reflections

To characterize how students described their use of LLMs, we conducted a cross- analysis combining LLM-assisted categorization with manual verification and refinement by the researchers. The process was intentionally designed as a re- flective educational analysis rather than a fully automated classification process. The analysis was conducted in four phases.

Phase 1: Familiarization with the Reflections. Initially, the researchers inde- pendently read the full set of 146 disclosure statements multiple times to become familiar with the reflections and identify recurring patterns related to how stu- dents used LLMs during the assignment. During this stage, attention was given to recurring descriptions of writing support, methodological assistance, brain- storming activities, perceived benefits, and reported challenges.

Phase 2: Initial LLM-Assisted Categorization. To support the organization of recurring patterns across the disclosures, ChatGPT-4.0 was used to assist with excerpt identification and preliminary categorization tasks. The prompts

6 R. de Souza Santos et al.

focused on dimensions commonly emphasized in reviewer guidelines from ma- jor software engineering venues such as ICSE, ICSME, ESEM, EASE, and the Empirical Software Engineering journal. These venues frequently instruct re- viewers to evaluate aspects such as novelty, rigor, relevance, transparency, and presentation quality when assessing research papers.

Based on these recurring dimensions, the analysis was organized around the following categories:

– Novelty: uses related to brainstorming, topic exploration, research question

definition, and understanding unfamiliar concepts; – Rigor: uses associated with methodological clarification, organization of re-

search procedures, identification of evidence sources, and support for empir- ical research activities; – Relevance: uses focused on improving the communication, interpretation,

coherence, and significance of findings and conclusions; – Transparency: uses related to improving explanations of research proce-

dures, clarity of reporting, traceability of information, and communication of how findings were obtained or analyzed; – Presentation: uses associated with grammar correction, writing refinement,

formatting, readability, sentence structure, and overall presentation quality.

ChatGPT-4.0 was used to identify excerpts potentially associated with these categories and to flag explicit mentions of perceived benefits and challenges re- lated to LLM use. An illustrative example of the prompt structure used during the categorization process is presented below.

¡ Illustrative Analysis Prompt

Instruction: Analyze the following student disclosure statements and identify excerpts where students explicitly describe how LLMs supported academic writing activities. Categorize the excerpts according to the follow- ing dimensions commonly considered in software engineering peer review: Novelty, Rigor, Relevance, Transparency, and Presentation.

Guidelines: Only classify excerpts when the student explicitly de- scribes the use or perceived impact of the tool. Do not infer meanings that are not directly stated in the disclosure statements.

Output: Return the identified category together with the correspond- ing excerpt from the disclosure statement.

Phase 3: Manual Verification and Refinement. After the initial AI-assisted categorization, the researchers manually reviewed all classifications and extracted quotations. During this verification process, the researchers checked whether the excerpts accurately reflected the assigned category, removed ambiguous classi- fications, adjusted labels when necessary, and refined the interpretation of the disclosures to preserve contextual meaning.

How Software Engineering Students Use LLMs to Write Research Papers 7

Particular attention was given to avoiding overinterpretation. Only disclo- sures in which students explicitly described a use, challenge, or perception re- lated to LLMs were retained in the final categorization. Statements considered vague, indirect, or unsupported were excluded from the analysis. The researchers also compared classifications collaboratively and discussed disagreements until consensus was reached.

Phase 4: Consolidation of Educational Observations. Finally, the refined cat- egories and excerpts were consolidated into broader educational observations regarding how students integrated LLMs into empirical writing activities. At this stage, the researchers focused on recurring educational patterns, including how students perceived LLMs as writing assistants, methodological aids, brain- storming partners, and sources of concern related to hallucinations, inaccuracies, and meaning distortion. This iterative interaction between AI-assisted support and researcher interpretation allowed the organization of recurring educational observations while preserving the contextual richness of the student reflections.

3.4 Ethics

All procedures followed institutional ethical guidelines for research involving human participants. Disclosure statements were analyzed only after final grades had been released, ensuring that participation had no influence on academic evaluation. The research team had access only to anonymized disclosures and did not interact with identifiable student data during the analysis process.

Due to the nature of the disclosures and the educational setting, the complete dataset cannot be publicly shared. However, anonymized excerpts are included throughout the paper to illustrate the observations discussed.

4 Educational Observations

Across the 146 student disclosure statements collected after the assignment, several recurring patterns emerged regarding how students incorporated LLMs into their academic writing activities. Most students described using LLMs to support presentation and writing quality, while smaller groups reported using the tools for idea generation, methodological support, articulation of findings, and transparency-related tasks. A small number of students also explicitly stated that they chose not to use LLMs during the assignment.

Most students reported using ChatGPT as their primary LLM during the as- signment. A smaller number mentioned other tools, including Claude, Gemini, GitHub Copilot, Bing AI, and Deepseek. In some cases, students described com- bining multiple LLMs depending on the activity being performed, particularly for brainstorming, writing refinement, or summarization tasks. These observa- tions suggest that while ChatGPT dominated usage patterns, students were also experimenting with different AI tools throughout the assignment process.

8 R. de Souza Santos et al.


> **Table 1: Illustrative Student Disclosures by Type of LLM Use**

Category Illustrative Quotes Presentation “This paper leveraged ChatGPT and Google Gemini for the improvement of sentence structure, spelling, grammar, and Latex formatting.” (D001)

“ChatGPT, a generative AI tool, was used in the writing pro- cess of this paper for grammatical checks and proper sentence phrasing.” (D005)

“In this paper, ChatGPT and Grammarly AI were tools used for grammar, spelling/thesaurus, checking if content was in accordance with IEEE standard.” (D006) Novelty “In the early brainstorming stages of this paper, ChatGPT was used to gain a broad understanding (...)” (D013)

“The author of this paper used ChatGPT-4o to generate ideas for the topic of this paper.” (D053)

“I used ChatGPT to understand the key concepts of the pa- pers.” (D120) Relevance “(...) it helped me word and phrase my findings and thoughts in a more cohesive and clear manner.” (D016)

“It helped me break down complicated ideas, explain difficult terms, and ensure that my explanations made sense.” (D111)

“In this paper, ChatGPT was used to (...) refining clarity in written explanations.” (D134) Rigor “(...) to create a step-by-step guide for conducting research using the prompt ‘can you devise a plan to research and write the paper based on that question?’” (D024)

“In this paper, the DeepSeekR1 LLM served as a research partner, providing a second perspective during the study screening process by evaluating inclusion criteria that I orig- inally created.” (D099)

“Furthermore, I used it to give me key bullet points from some of the papers I researched.” (D133) Transparency “A blueprint of the structure of this paper was provided, to which the tool identified areas where additional material could enhance the explanation.” (D083)

“In this paper, ChatGPT was used to enhance the reader’s comprehension (...) making the paper more transparent and effective.” (D093)

4.1 LLMs as Writing and Research Support Tools

The most frequently reported use of LLMs involved Presentation. Students commonly described using the tools to revise grammar, improve sentence structure, increase clar- ity, and adapt the tone of their papers to a more academic style. Several students characterized the LLM as a “final editor” used before submission to polish the text and improve readability. Students also reported using LLMs to support citation formatting,

How Software Engineering Students Use LLMs to Write Research Papers 9

particularly in BibTeX and LATEX, and to help reorganize sections to better align with the assignment template. These observations suggest that students frequently relied on LLMs to navigate academic writing conventions and improve the overall presentation of their work.

Another recurring pattern involved the use of LLMs for Novelty. Students de- scribed using the tools to explore possible research topics, narrow broad themes, iden- tify potential research questions, and better understand unfamiliar concepts related to software architecture and software design. Some students reported iterating over multiple prompts to compare possible directions for their papers or to better define the scope of their investigations. In several disclosures, students described the tools as interactive brainstorming partners that helped initiate early-stage academic reasoning and topic exploration.

A smaller group of students described using LLMs to support Relevance. In these cases, students reported asking the tools for assistance in explaining the relevance of their observations, synthesizing conclusions, or improving the communication of implications identified during the assignment. Rather than generating findings directly, the tools were often used to help students organize and phrase their interpretations more clearly. These reflections suggest that some students perceived LLMs as support mechanisms for strengthening coherence and improving how results and implications were communicated in their papers.

Some students also described using LLMs to support Rigor. These uses included asking for clarification about rapid reviews and gray literature reviews, obtaining sug- gestions for structuring research procedures, and improving descriptions of data orga- nization and analysis activities. A few students also reported using the tools to help identify possible evidence sources and organize categories or themes across collected materials. From an educational perspective, these observations indicate that students may perceive LLMs not only as writing assistants, but also as tools capable of support- ing understanding of empirical software engineering practices and research organization activities.

Finally, a small number of students reported using LLMs to support Transparency. In these cases, students described using the tools to improve explanations regarding how information was collected, categorized, or analyzed. Some students also used LLMs to review whether their descriptions of research procedures were sufficiently under- standable and reproducible. Although less frequent, these observations suggest that some students were already reflecting on how AI tools could support communication of research processes, methodological clarity, and transparency during academic writing activities.

4.2 Student Reflections on Benefits and Challenges

Students reported a wide range of experiences regarding the incorporation of LLMs into academic writing activities. While some disclosures were brief and technical, oth- ers provided detailed reflections about how these tools affected writing organization, comprehension, confidence, and learning processes throughout the assignment. Many students described LLMs as useful companions during the writing process. Commonly reported benefits included improved grammar, better organization of ideas, assistance with summarization, and support for understanding complex concepts. Several stu- dents also emphasized that LLMs helped make academic writing feel more manageable, particularly when dealing with unfamiliar terminology, empirical methods, or formal academic structures.

10 R. de Souza Santos et al.

For example, student D138 stated: “AI did help improve my writing process by helping me to avoid repeating the same ideas again and again.” Similarly, student D109 explained: “Additionally, it provided support in understanding complex concepts and rephrasing them in simpler terms so I could grasp them better.” These reflections suggest that many students perceived LLMs as tools capable of supporting both communication and comprehension during empirical writing activities. In particular, several disclosures associated AI support with increased clarity, confidence, organization, and reduced difficulty during the writing process.

At the same time, students also expressed concerns regarding limitations and risks associated with LLM use. Several disclosures mentioned hallucinations, inaccuracies, lack of contextual understanding, and the possibility that AI-generated suggestions could unintentionally distort the intended meaning of the text. Some students also de- scribed difficulties determining whether generated outputs were reliable or sufficiently aligned with their intended arguments. These concerns indicate that, despite the per- ceived usefulness of the tools, students remained aware of practical limitations and risks associated with relying on AI-generated content during academic work.

For example, participant D026 stated: “A key challenge being that the AI-assisted refinements altered the intended meaning or introduce unintended biases.” Another stu- dent, D018, reported: “However, hallucinations were an issue as in certain cases it made up fake information in terms of certain topics.” These disclosures suggest that students were not simply accepting generated outputs without reflection. Instead, many students described the need to verify information, critically evaluate generated sugges- tions, and preserve authorship and meaning during the writing process. Considering the reflections as a whole, the statements revealed a combination of perceived benefits and challenges associated with the use of LLMs in academic writing activities.

5 Lessons Learned and Educational Implications

Prior literature on teaching empirical software engineering emphasizes exposing stu- dents to authentic research activities while developing skills related to study design, evidence evaluation, critical reasoning, and communication of findings [4, 15, 10, 12]. Existing educational approaches commonly encourage students to engage with empir- ical methods through project-based activities, evidence synthesis exercises, and struc- tured reflection on methodological decisions. Our experience suggests that the growing presence of LLMs does not fundamentally alter these educational objectives. Instead, it changes the environment in which students perform these activities. Rather than acting solely as writing assistants, students frequently used LLMs as interactive companions during brainstorming, methodological clarification, organization of findings, and refine- ment of explanations. Based on these observations, we identified the following lessons learned:

– Allow and regulate rather than prohibit. Students integrated LLMs into

multiple stages of the assignment process. Educational strategies may therefore be more effective when they focus on responsible use and accountability rather than attempting to eliminate the use of these tools altogether. – Require explicit disclosure of AI use. Asking students to document how LLMs

contributed to their work encouraged reflection regarding benefits, limitations, ver- ification practices, and decision-making. Disclosure activities can promote trans- parency while providing instructors with insights into emerging usage patterns.

How Software Engineering Students Use LLMs to Write Research Papers 11

– Teach verification as a core empirical skill. Students frequently reported con-

cerns regarding hallucinations, inaccuracies, and unintended changes in meaning. Assignments should explicitly emphasize validation of AI-generated information against original sources and empirical evidence. – Design assignments that assess reasoning rather than text production

alone. While LLMs often supported writing quality and organization, students remained responsible for interpreting evidence, making methodological decisions, and justifying conclusions. Assessment strategies should place greater emphasis on these higher-order activities. – Provide guidance on acceptable and unacceptable uses of LLMs. Stu-

dents reported a broad spectrum of uses, ranging from grammar correction to methodological support and idea generation. Clear expectations can help students distinguish between legitimate assistance and uses that may compromise learning objectives. – Incorporate discussions about AI limitations into empirical methods

training. Concerns regarding reliability, bias, and factual correctness emerged repeatedly in the disclosures. These limitations can be used as opportunities to re- inforce concepts such as validity, evidence quality, critical evaluation, and research rigor. – Use LLMs as opportunities to strengthen methodological reflection.

Some students relied on LLMs to better understand empirical procedures and evidence synthesis approaches. Encouraging students to critically evaluate and jus- tify AI-generated methodological suggestions may support deeper engagement with empirical concepts.

More broadly, we suggest that software engineering education may need to move beyond discussions centered on whether students should use LLMs and instead focus on how such tools can be incorporated without compromising learning objectives. Em- pirical software engineering courses are intended to develop critical thinking, evidence evaluation, methodological reasoning, and communication skills. Our findings suggest that these competencies remain essential in AI-enabled educational environments and may become even more important as students gain access to increasingly capable gen- erative tools. Consequently, future educational practices may benefit from integrating transparency, verification, and responsible AI use as explicit learning outcomes along- side traditional empirical software engineering competencies.

6 Conclusions

This paper reports an educational experience involving the integration of reflective LLM use into an empirical software engineering assignment in an undergraduate soft- ware engineering course. Through the analysis of 146 student disclosure statements, we explored how students described the incorporation of LLMs while conducting activities related to rapid reviews and gray literature reviews. The analysis focused on five recur- ring dimensions of use: Presentation, Novelty, Relevance, Rigor, and Transparency. The reflections showed that students used LLMs not only for writing refinement activities, but also for brainstorming, methodological clarification, organization of findings, and communication of empirical results. At the same time, students frequently reported concerns involving hallucinations, inaccuracies, meaning distortion, and the need to verify generated outputs. These observations suggest that students are already incor- porating AI tools into empirical software engineering workflows while negotiating issues

12 R. de Souza Santos et al.

related to authorship, reliability, and critical evaluation. For future work, we plan to conduct additional empirical studies involving different software engineering courses, instructional strategies, and evidence synthesis activities, such as systematic literature reviews and multivocal literature reviews, to better understand how students incorpo- rate AI-assisted technologies into empirical software engineering workflows and learning processes.

Disclosure of Interests. The authors have no competing interests to declare that are relevant to the content of this article.


## References

1. Arora, U., Garg, A., Gupta, A., Jain, S., Mehta, R., Oberoi, R., Prachi, Raina, A., Saini, M., Sharma, S., et al.: Analyzing llm usage in an advanced computing class in india. In: Proceedings of the 27th Australasian Computing Education Conference. pp. 154–163 (2025) 2. Filippi, S., Motyl, B.: Large language models (llms) in engineering education: A systematic review and suggestions for practical adoption. Information 15(6), 345 (2024) 3. Grande, V., Kiesler, N., Francisco R, M.A.: Student perspectives on using a large language model (llm) for an assignment on professional ethics. In: Proceedings of the 2024 on Innovation and Technology in Computer Science Education V. 1, pp. 478–484. ACM (2024) 4. Host, M.: Introducing empirical software engineering methods in education. In: Proceedings 15th Conference on Software Engineering Education and Training (CSEE&T 2002). pp. 170–179. IEEE (2002) 5. Kirova, V.D., Ku, C.S., Laracy, J.R., Marlowe, T.J.: Software engineering education must adapt and evolve for an llm environment. In: Proceedings of the 55th ACM Technical Symposium on Computer Science Education V. 1. pp. 666–672 (2024) 6. Liu, Y.: Integrating conversational large language models into student learning: A case study of chatgpt in software engineering education. In: 2024 IEEE Frontiers in Education Conference (FIE). pp. 1–8. IEEE (2024) 7. Moore, S., Tong, R., Singh, A., Liu, Z., Hu, X., Lu, Y., Liang, J., Cao, C., Khos- ravi, H., Denny, P., et al.: Empowering education with llms-the next-gen interface and content generation. In: International Conference on Artificial Intelligence in Education. pp. 32–37. Springer (2023) 8. Peláez-Sánchez, I.C., Velarde-Camaqui, D., Glasserman-Morales, L.D.: The impact of large language models on higher education: exploring the connection between ai and education 4.0. In: Frontiers in Education. vol. 9, p. 1392091. Frontiers Media SA (2024) 9. Pereira, J., López, J.M., Garmendia, X., Azanza, M.: Leveraging open source llms for software engineering education and training. In: 2024 36th International Con- ference on Software Engineering Education and Training (CSEE&T). pp. 1–10. IEEE (2024) 10. Pizard, S., Acerenza, F., Otegui, X., Moreno, S., Vallespir, D., Kitchenham, B.: Training students in evidence-based software engineering and systematic reviews: a systematic review and empirical study. Empirical Software Engineering 26, 1–53 (2021)

How Software Engineering Students Use LLMs to Write Research Papers 13

11. Razafinirina, M.A., Dimbisoa, W.G., Mahatody, T.: Pedagogical alignment of large language models (llm) for personalized learning: a survey, trends and challenges. Journal of Intelligent Learning Systems and Applications 16(4), 448–480 (2024) 12. Serebrenik, A., Cassee, N.: Teaching empirical methods at eindhoven university of technology. In: Handbook on Teaching Empirical Software Engineering, pp. 179– 207. Springer (2024) 13. Wen, Q., Liang, J., Sierra, C., Luckin, R., Tong, R., Liu, Z., Cui, P., Tang, J.: Ai for education (ai4edu): Advancing personalized education with llm and adaptive learning. In: Proceedings of the 30th ACM SIGKDD Conference on Knowledge Discovery and Data Mining. pp. 6743–6744 (2024) 14. Wiktor, S., Dorodchi, M., Wiktor, N.: Ai can help instructors help students: An llm-supported approach to generating customized student reflection responses. In: 2024 IEEE Frontiers in Education Conference (FIE). pp. 1–9. IEEE (2024) 15. Wohlin, C.: Empirical software engineering: Teaching methods and conducting studies. In: Empirical Software Engineering Issues. Critical Assessment and Fu- ture Directions: International Workshop, Dagstuhl Castle, Germany, June 26-30, 2006. Revised Papers. pp. 135–142. Springer (2007) 16. Yan, L., Sha, L., Zhao, L., Li, Y., Martinez-Maldonado, R., Chen, G., Li, X., Jin, Y., Gašević, D.: Practical and ethical challenges of large language models in education: A systematic scoping review. British Journal of Educational Technology 55(1), 90–112 (2024)
