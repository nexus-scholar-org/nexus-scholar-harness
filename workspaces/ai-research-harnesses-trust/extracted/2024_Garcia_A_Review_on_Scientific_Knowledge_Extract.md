---
workspace_id: "SCI-000105"
doi: null
title: "A Review on Scientific Knowledge Extraction using Large Language Models in Biomedical Sciences"
year: 2024
extraction_engine: "pymupdf"
---
# 2024 Garcia A Review on Scientific Knowledge Extract

A Review on Scientific Knowledge Extraction using Large Language

Models in Biomedical Sciences

Gabriel Lino Garcia1 a, Jo˜ao Renato Ribeiro Manesco1 b Pedro Henrique Paiola1 c, Lucas Miranda2, Maria Paola de Salvo2 and Jo˜ao Paulo Papa1 d

1School of Sciences, S˜ao Paulo State University (UNESP), Bauru - SP, Brazil 2EasyTelling, S˜ao Paulo - SP, Brazil {gabriel.lino, joao.r.manesco, pedro.paiola, joao.papa}@unesp.br

{lucas, paola}@easytelling.com

arXiv:2412.03531v1  [cs.CL]  4 Dec 2024

Keywords: evidence synthesis, large language models, LLMs, biomedical, healthcare, literature-based discovery, knowledge extraction


## Abstract:

The rapid advancement of large language models (LLMs) has opened new boundaries in the extraction and
synthesis of medical knowledge, particularly within evidence synthesis. This paper reviews the state-of-the-
art applications of LLMs in the biomedical domain, exploring their effectiveness in automating complex tasks
such as evidence synthesis and data extraction from a biomedical corpus of documents. While LLMs demon-
strate remarkable potential, significant challenges remain, including issues related to hallucinations, contextual
understanding, and the ability to generalize across diverse medical tasks. We highlight critical gaps in the cur-
rent research literature, particularly the need for unified benchmarks to standardize evaluations and ensure
reliability in real-world applications. In addition, we propose directions for future research, emphasizing the
integration of state-of-the-art techniques such as retrieval-augmented generation (RAG) to enhance LLM per-
formance in evidence synthesis. By addressing these challenges and utilizing the strengths of LLMs, we aim
to improve access to medical literature and facilitate meaningful discoveries in healthcare.

1 INTRODUCTION

ness of the literature. The medical field exemplifies this challenge, as impactful discoveries that could im- prove treatment outcomes or advance medical science may go unnoticed simply because they are buried be- neath a deluge of publications or presented in a highly technical manner.

In recent years, the number of studies published in various fields has grown exponentially, with a wide range of applications spanning multiple disci- plines (Bornmann et al., 2024). While this surge in scientific literature contributes to knowledge expan- sion, it poses a significant challenge for researchers and professionals attempting to stay informed of crit- ical developments (Beller et al., 2013). This trend is particularly important in fields such as medicine, where the implications of new findings can have di- rect and life-altering impacts on patients’ lives.

Systematic reviews have long been regarded as a solution, providing comprehensive and structured analyses of the available literature. While effective, these reviews are exhaustive and frequently very tech- nical, making them time-consuming to produce and difficult for non-experts to interpret. Consequently, they do not fully solve the issue of accessibility, espe- cially for those who lack the specialized knowledge to extract meaningful insights from the data.

However, despite the abundance of information, the practical use of many of these studies remains lim- ited (Meho, 2007). This is often due to barriers to ac- cessing relevant and impactful research, particularly when important findings are hidden within the vast-

The advent of large language models (LLMs) of- fers a promising avenue for addressing this challenge. LLMs, powered by advancements in artificial intelli- gence, have the potential to assist in the navigation and synthesis of vast amounts of scientific literature. Indeed, some research has already begun to explore the potential of these models to automate aspects of the systematic review process, highlighting the pos-

a https://orcid.org/0000-0003-1236-7929 b https://orcid.org/0000-0002-1617-5142 c https://orcid.org/0000-0001-9093-535X d https://orcid.org/0000-0002-6494-7514

evidence synthesis based on scientific literature. Sec- tion 4 discusses the main works found in scientific ev- idence synthesis. Section 5 discusses the state of the art and current limitations in the literature, and Sec- tion 6 concludes the paper.

sibility of their application in evidence synthesis and knowledge extraction (Alshami et al., 2023).

LLMs, such as GPT, are particularly well-suited to tasks involving knowledge extraction and summariza- tion. They can process and synthesize vast amounts of text, distilling complex ideas into more accessible formats (Ignat et al., 2023). This capability makes them powerful tools for navigating large datasets and filtering out the most relevant information. Moreover, the ability of LLMs to generate concise and coher- ent summaries from complex data sets is already be- ing harnessed in some preliminary applications within systematic review processes.

2 Review Methodology

This systematic review followed the Preferred Report- ing Items for Systematic Reviews and Meta-Analyses (PRISMA) guidelines to ensure a transparent and rig- orous approach to evaluating the role of LLMs in the biomedical field. The main objective of this review is to provide a comprehensive assessment of the ef- fectiveness, challenges, and methodologies of LLMs in the extraction and synthesis of medical knowledge. While knowledge extraction is a broader area of in- terest, this review specifically focuses on evidence synthesis, which aligns more closely with the com- plex task of integrating diverse medical information for clinical decision-making and research purposes.

While early applications of LLMs in systematic reviews are promising, synthesizing scientific evi- dence for decision-making requires more than mere automation of reviews. Managers, healthcare profes- sionals, and other non-technical stakeholders require tools to explore the literature and synthesize evidence meaningfully and effectively. This necessitates fur- ther investigation into how LLMs can be adapted as a tool for evidence synthesis for researchers and those involved in policy-making and management in fields like healthcare.

The guiding research question of this review is: “How effective are LLMs in extracting and synthe- sizing structured and relevant knowledge from med- ical texts, and what are the key challenges and out- comes associated with their application in the medi- cal field?” This question encompasses the exploration of the models most frequently used, how they are fine-tuned for biomedical applications, their perfor- mance compared to other knowledge extraction meth- ods, and the specific biomedical domains that benefit most from LLM-based approaches.

Given the potential of LLMs to address these chal- lenges, this paper aims to provide a comprehensive review of current research exploring the use of LLMs in evidence synthesis, with a particular focus on their application in the medical field. We will examine ex- isting methods, tools, and frameworks that leverage LLMs for scientific knowledge extraction and discuss how these approaches can help bridge the gap be- tween vast amounts of data and practical, actionable insights.

The review adopted a search strategy across sev- eral academic and preprint databases, including ACM Digital Library, IEEE Xplore, Scopus, SOLO (includ- ing arXiv), and ScienceDirect. The search string was designed to cover the breadth of LLM applications in medical knowledge extraction, focusing specifically on evidence synthesis tasks. Studies were included if they focused on applying LLMs in medical settings, provided quantitative evaluations, and were published in English over the past five years.

Thus, we have proposed a review of scientific evidence synthesis using LLMs, particularly for the healthcare case. Among the contributions of our work are:

• We provide a comprehensive evaluation of the state-of-the-art LLMs used for medical evidence synthesis, focusing on their performance and challenges in tasks like clinical decision support and knowledge extraction.

• We identify key limitations, including issues with hallucinations, contextual understanding, and scalability, offering insights into the research gaps that need to be addressed.

2.1 Screening of Relevant Works

To enhance the screening process’s efficiency, we used a ChatGPT-4 LLM to generate summaries and provide context for each selected study. This ap- proach allowed us to hasten the review of many ar- ticles while maintaining a high level of consistency in the analysis. The initial screening was guided by pre- defined inclusion and exclusion criteria, with priority given to studies that addressed LLM applications in

• We propose the need for unified benchmarks and highlight future directions to enhance the effec- tiveness of LLMs in biomedical applications.

The remainder of this paper is structured as fol- lows. In Section 2, we present the protocol used to conduct our review. Section 3 gives a background on

evidence synthesis. A diagram illustrating the screen- ing and selection process, following PRISMA guide- lines, is provided in Figure 1.

cal evidence regarding a certain area of knowledge in a way that reduces bias and allows for replicabil- ity (Lasserson et al., 2019).

The objective of such systems is to support decision-makers by providing a reliable summary of research findings in the scope of the literature. How- ever, constantly performing manual evidence synthe- sis whenever you need to make a decision can cause many constraints, especially since systematic reviews are highly complex and time-consuming, requiring strict adherence to rigorous protocols. This process often limits the decision maker’s ability to respond quickly to novel evidence (Singh, 2017).

Identification of studies via databases and registers

Records identified from*:

Identification  Screening  Included

ACM Digital Library  (n = 256)  IEEE Digital Library  (n = 164)  ISI Web of Science  (n = 6)  SOLO  (n = 25)  Science@Direct  (n = 4)  Scopus  (n = 217)

Records removed before  screening:

Duplicate records removed  (n = 23)

Records excluded**  (n = 602)

Records screened  (n = 649)

Many approaches have been proposed to accel- erate such processes using novel Natural Language Processing (NLP) techniques such as LLMs, mostly focusing on different aspects of the systematic re- view protocol, which can significantly reduce the manual burden and time required to complete a re- view (Bolanos et al., 2024). These tools, however, are still focused on specific parts of the review process, such as screening or data extraction. While they can still be relevant, preparing the complete review can still take time and hinder decision-makers productiv- ity.

Reports sought for retrieval  (n = 53)

Reports not retrieved  (n = 2)

Reports excluded:

Reports assessed for eligibility  (n = 51)

Secondary Works (n = 10)  Out of scope: extraction of  clinical relationships in  diagnosis (n = 14)  Out of scope: extraction of  information from electronic  health records (n = 13)

Studies included in review  (n = 14)


> **Figure 1: Illustration of the screening process, conducted in**

> accordance with the PRISMA protocol, used to identify and
select relevant studies for this review.

The use of LLMs to accelerate knowledge synthe- sis has been explored in other reviews (Bolanos et al., 2024; Burgard and Bittermann, 2023; de la Torre- L´opez et al., 2023). However, these reviews primar- ily concentrate on streamlining the systematic review process. In contrast, our work focuses on techniques that use LLMs to perform evidence synthesis directly. In other words, those methods focus on compiling rel- evant literature in a more flexible, less constrained manner to provide quick, up-to-date knowledge, par- ticularly within the healthcare domain, where timely access to synthesized evidence is crucial.

After the automated summarization phase, we manually validated the results to ensure that key insights, challenges, and contributions were accu- rately captured. This dual approach—combining au- tomation with manual oversight—provided a robust method for managing the complexity of the literature while preserving the depth and rigor expected in sys- tematic reviews.

For each included study, we extracted data on the type of LLM used, the medical task it was applied to, performance outcomes, and the challenges encoun- tered. Particular attention was paid to how LLMs were adapted for biomedical knowledge extraction, the domains where they performed most effectively, and how they compared to other knowledge extrac- tion techniques.

4 Results

This section synthesizes the selected studies that have applied various LLMs to medical evidence synthesis. The discussion is divided into two parts: first, we ex- amine the use of LLMs in evidence synthesis as a broader concept, and second, we focus specifically on their applications within the medical field as reported in the literature.

3 Background

Evidence synthesis refers to collecting, analyzing, and integrating information from the literature in a well-documented way to answer a pre-defined re- search question. One such form of evidence synthe- sis is through systematic reviews, which follow a rig- orous search protocol to obtain all possible empiri-

4.1 Evidence Synthesis

Regarding evidence Synthesis using LLMs, a few works have been proposed more broadly to solve spe- cific tasks in recent literature. One work (Khraisha

entail the key points based on their semantic simi- larity. Although the method was successful in a re- stricted scenario of anonymous comments, there is still a concern regarding bias in the employed dataset.

et al., 2024) evaluates the efficacy of GPT-4 in per- forming systematic review tasks such as title/abstract screening, full-text review, and data extraction from various literature types and languages without human intervention. The study employed a ”human-out-of- the-loop” approach, meaning that GPT-4 was tested independently without human intervention during ex- traction, focusing on the literature regarding parenting in protracted refugee situations. This work describes several challenges of current GPT models, indicating that the model’s performance is heavily biased by the distribution of relevant and irrelevant studies, display- ing a tendency of over-excluding studies.

Focusing more on the extraction of information in scientific texts, Dagdelen et al. (2024) focuses on joint-named entity recognition and relation ex- traction, allowing the models to identify entities and their relationships within materials science literature. The model architecture is based on a sequence-to- sequence framework, where GPT-3 and LLaMa-2 models are fine-tuned on a relatively small dataset of 400-650 annotated text-extraction pairs. Given the dataset’s limitations and the relationships’ complex- ity, the model still struggles to perform complete evi- dence synthesis.

In other words, this concept is expanded in less generic fields, such as government report genera- tion (Gupta et al., 2024), in which Google’s Gemini Pro and OpenAI’s GPT-3.5 Turbo are used to improve data extraction, analysis, and visualization processes by reading all existing reports to identify graphs and charts needing updates, extracting data points from these graphs and synthesizing information in their knowledge repositories to update their report graphs. Although the method does not exactly synthesize in- formation in textual form, it performs a Retrieval- Augmented Generation (RAG) method to synthesize information in graphic form.

4.2 Synthesis in Biomedical Sciences

In the healthcare domain, which is the primary fo- cus of our analysis, one study explores the applica- tion of LLMs, specifically GPT-3.5 and GPT-4, for Literature-Based Discovery to generate research hy- potheses Nedbaylo and Hristovski (2024). The au- thors employ a bifurcated prompt engineering tech- nique, where the original prompt is split into two parts and executed in separate chat windows. In the first segment, the model generates a list of disease char- acteristics without disclosing the disease name. In contrast, the second suggests potential interventions based on the factors identified in the initial segment. The study conducts a qualitative evaluation and con- cludes that GPT-based methods heavily depend on preexisting bibliographic databases, such as Medline, which restricts their applicability to fields with well- established datasets. Additionally, the study finds that outputs from GPT-4 often lack technical depth and novelty, and they frequently fail to provide adequate references for the generated information.

The work of Yu et al. (2023) focuses on enhancing the extraction of training data from language mod- els, specifically using the GPT-Neo 1.3B model in a two-stage pipeline: suffix generation, where vari- ous sampling strategies are employed, including top- k sampling, nucleus sampling, and typical sampling, to produce candidate suffixes based on a given pre- fix; and suffix ranking, in which perplexity and addi- tional metrics like Zlib entropy are used to evaluate and select the most likely suffixes from the generated candidates. Although interesting for several aspects of knowledge extraction, this technique is still depen- dent on a large number of candidates that are ranked to identify a single successful instance, only working in limited scenarios.

Tao et al. (2024) employs the OpenAI GPT-4 model to evaluate its performance in answering spe- cific questions related to HIV drug resistance from published scientific papers. The researchers designed an automated pipeline that transformed the text of 60 selected HIV drug resistance papers into mark- down format, excluding sections like the introduc- tion and discussion to focus on the methods and re- sults. By posing 60 questions in two modes, multiple- question mode (all questions presented simultane- ously) and single-question mode (one question at a time), with and without an instruction sheet contain- ing specialized knowledge, the authors were able to perform a quantitative evaluation of the task. Al- though the method obtained a fairly good mean ac-

In order to summarize the knowledge base, Dis- crete Text Summarization (DeTS) was proposed as a novel unsupervised method for discrete text summa- rization, in which grammatical sequence scoring and independent key points from large textual datasets are used for natural language inference. The technique consists of two main components: candidate extrac- tion and candidate matching. In the candidate ex- traction phase, the algorithm utilizes Semantic Role Labeling (SRL) to segment comments into smaller pieces. The candidate matching phase aligns these key points with sentences from the entire corpus using NLI algorithms, determining whether the sentences

curacy of 86.9%, some aspects of the technique could be improved, such as the fact that the instruction sheet was not effectively utilized by the model, by not im- proving the accuracy of the responses, in addition, the method struggled with specific queries that required making inferences, especially when dealing with im- plicit information in the texts. Worst of all, the GPT- 4 model was more likely to provide false positive answers when questions were submitted individually than when they were submitted together, indicating the presence of bias when dealing with certain aspects of the literature.

This trend of using encoder-based smaller lan- guage models was also observed in two other works in the literature. One of them works on a dataset of biomedical articles collected from PubMed, aiming to summarize biomedical literature by using an encoder- decoder model based on BioBERT Alambo et al. (2022) To achieve its purpose, the researchers cre- ated a framework based on two main components: an entity-driven knowledge retriever that extracts facts based on named entities identified in the source doc- uments, and a knowledge-guided abstractive summa- rizer that generates summaries by attending to both the source article and the retrieved facts.

Using the Claude 2 LLM, one study performs a proof-of-concept design to evaluate the performance of LLMs in interpreting randomized controlled trials (RCTs) Gartlehner et al. (2024). To do that, the re- searchers selected a convenience sample of 10 open- access RCTs and focused on extracting 16 distinct data elements, which included study identifiers, par- ticipant characteristics, and outcome data. The data extraction pipeline involves mostly prompt engineer- ing, where the crafted prompts were iteratively tested and refined to optimize the model’s output. Although the method obtains interesting results, several con- cerns should be considered, such as the fact that open RCTs were used, meaning they could be in the train- ing set of Claude 2. The authors also reported two cases of hallucinations from answers that the model did not know how to reply to.

The other work focuses on semi-automate data ex- traction for systematic literature using a BERT model pre-trained on a corpus of 100,000 open-access clin- ical publications, the main objective being extracting clinical relationships from the corpus in order to per- form literature filtering Panayi et al. (2023). Both works, although displaying interesting results, suf- fer from the difficulties of dealing with complex un- structured data; the BioBERT-based models, although displaying better results, still report hallucination, as there is an attempt to generate structured text.

Other works are more focused on extracting spe- cific information from the biomedical literature. One such work, named ChIP-GPT, fine-tuned a LLaMa architecture on Sequence Read Archive information obtained from biomedical database records by ex- tracting relevant sentences and summarizing biomed- ical records, intending to identify chromatin immuno- precipitation (ChIP) targets and cell lines in these records. A summarization step was implemented to manage the input length limitations of the model for longer records. This involved selecting informative sentences while discarding irrelevant details, ensur- ing the model could generate concise and accurate an- swers. The final results display good accuracy in the task even when compared with human experts. How- ever, it was observed that this summarization step still had a problem discarding relevant information for the model, which impacted the final results.

Focusing on information retrieval to support knowledge synthesis in biomedical documents, one work uses the RoBERTa language model to work with the COVID-19 Open Research Dataset Saxena et al. (2022). To do that, an architecture was de- veloped consisting of three main components that extract relevant information: Paragraph Retrieval, Triplet Retrieval from Knowledge Graphs, and Com- plex Question Answering. The Paragraph Retrieval employs a hybrid approach combining lexical meth- ods with semantic search for indexing and re-ranking results based on relevance. The Triplet Retrieval sys- tem extracts subject-relation-object triplets from the knowledge graph, allowing for faceted refinement of search results. Finally, the complex QA system uti- lizes a Multi-hop Dense Retriever to handle multi- hop questions, iteratively retrieving relevant passages and employing both extractive (RoBERTa) and gen- erative (Fusion-in-Decoder) readers to generate an- swers. The model relies on an older approach for language models, which, although smaller, has more difficulty when dealing with generative language an- swers; the authors also report difficulty in dealing with the amount of unstructured textual data reported in the medical literature.

Following the same concept, another work focuses on extracting relevant data from scientific literature for chemical risk assessment, focusing on Bisphe- nol A Sonnenburg et al. (2024). To achieve that, the authors created a dataset containing 78 selected publications, primarily extracting results sections to form prompt-completion pairs so that they could per- form fine-tuning on an LLM from the GPT-3 family named Curie model. The Curie model reported re- markable results, especially compared to other ready- to-use models that were not fine-tuned, even if the au- thors still have some concerns regarding treating stud-

a GPT-4 LLM, while Tao et al. (2024) employs the same LLM in a very distinct task and context: pro- cessing structured biomedical data for HIV drug re- sistance analysis. Although both methods use the same model and follow similar strategies, it is dif- ficult to conclude if the observed limitations come from the technique or the contextual data, as there is no shared information among them. Both stud- ies also highlight considerable limitations of current LLMs in dealing with insights from the data, espe- cially when the model needs to handle implicit infor- mation to generate connections and process novel in- formation.

ies with more complex experimental designs.

Finally, a study that focuses on using a Retriever- Augmented Generation (RAG) model to extract and deliver accurate medical knowledge about diabetes and diabetic foot care, specifically tailored for layper- sons with an eighth-grade literacy level, was pro- posed Mashatian et al. (2024). The authors use the GPT-4 model to formulate user-friendly responses based on the retrieved context, offering a zero-shot so- lution to the problem. A set of 295 articles was used to provide context and be evaluated across 175 questions on various diabetes-related topics. This work offers an interesting solution that does not require training the LLM and displays the results in natural language, even for people with lower literacy levels. Despite its advantages, the model is still evaluated on a very lim- ited set of data, so further experiments are required to see how it performs with new works being published in the literature.

Another current problem in the literature is that most methods focus on using pre-established datasets, such as Medline in the study by Nedbaylo and Hris- tovski (2024) or the curated HIV drug resistance liter- ature in Tao et al. (2024), to create a knowledge base for the LLM and fine-tune the model. In this case, it is difficult to establish the influence of each piece of data in the response, and it also makes dealing with the novel and growing literature even more difficult, as there is a need to re-train the model. As such, strategies based on RAG, such as the one proposed by Mashatian et al. (2024), appear as a more reliable solution to deal with new pieces of data and may pose the path forward for new techniques that may incor- porate modern RAG approaches at their core.

5 Comparison of Current Methods and Future Directions

In this section, we perform an aggregated analysis that compares datasets, performance metrics, identi- fied limitations, and future trends suggested by each method to understand the limitations of current tech- niques and the future trends in the literature. Al- though the area lacks a complete benchmark for eval- uating evidence synthesis, and each method does a different analysis, we still compare each technique by their main points and context in Table 1.

In the study of Gartlehner et al. (2024) that uses a Claude 2 model for the extraction of data from RCTs, the authors raise two main concerns regarding this area: the growing risks of hallucination caused by dif- ficulties in dealing with unstructured data in biomedi- cal research, and the potential bias coming from train- ing on open-access data, which the model may al- ready have seen during training. In addition, without a common benchmark, it is difficult to determine how these models would fare on more diverse datasets or in more complex, less predictable environments.

Existing methods that use language models for knowledge synthesis in biomedical tasks employ vari- ous strategies and applications, addressing several as- pects of knowledge extraction, including literature- based discovery, data extraction, and question- answering. One of the key challenges in this area is to perform a comprehensive evaluation capable of comparing the effectiveness of each method and LLM by themselves. Currently, each method follows its own protocol, with distinct datasets, evaluation crite- ria, and tasks, making it difficult to draw direct com- parisons between models or assess their generalizabil- ity to new problems.

Studies using smaller, encoder-based models like RoBERTa, BioBERT, and BERT also exhibit this challenge. While they are effective for specific tasks like entity extraction and information retrieval, their scalability and ability to generate new insights are limited. This is particularly evident in models de- signed for more specialized tasks, such as ChIP-GPT for chromatin immunoprecipitation data extraction and the fine-tuned Curie model for chemical risk as- sessment. These models achieve impressive results within their respective domains but lack the flexibil- ity to be easily compared or adapted across different biomedical tasks without a unified evaluation stan- dard.

In the reviewed studies, several models have been used for evidence syntheses, such as GPT-3.5, GPT- 4, Claude 2, and even encoder-based methods, such as RoBERTa and BioBERT, on a wide range of tasks ranging from generating research hypotheses to an- swering specific scientific queries and extracting clin- ical trial data. For example, Nedbaylo and Hristovski (2024) focuses on literature-based discovery through

The absence of a unified benchmark also extends


> **Table 1: Comparison of various methods used in biomedical literature for knowledge extraction and evidence synthesis.**

Paper Year Model Biomedical Context Reported Results Brief Summary

Alambo et al. (2022) 2022 BioBERT Biomedical articles and facts from biomedical knowledge bases.

Precision: 55.07%, Recall 7.97%

The method uses integrates named entities and facts from biomedical knowledge bases into transformer-based models to enhance the factual consistency of generated summaries in biomedical literature.

Precision: 81%, NDCG: 72%

A framework for complex information retrieval from biomedical documents is developed, utilizing paragraph retrieval, triplet retrieval from knowl- edge graphs, and complex question answering.

Saxena et al. (2022) 2022 RoBERTa + Fusion-in-Decoder

Unstructured text data from documents, articles, biomedical journals, and struc- tured data like tables and electronic health records.

F1-score: 73% A machine learning approach using pre-trained BERT and CRF models was employed to automate data extraction from systematic literature reviews by identifying biomedical entities and their rela- tions.

Panayi et al. (2023) 2023 BERT Metrics for progression-free survival, patient age, treatment arm dosage, and eGFR measurements extracted from systematic literature reviews in oncology and Fabry disease.

A fine-tuned version of GPT-3 was employed to ex- tract and structure data from scientific publications for risk assessment, specifically targeting toxico- logical properties of bisphenol A (BPA).

Precision: 25%, Re- call: 23%, F1-score: 50%.

Sonnenburg et al. (2024) 2024 GPT-3 NAM-based toxicity data on Bisphenol A (BPA) extracted from scientific pub- lications

A Literature-based discovery technique based on the generation of research hypotheses via bifur- cated prompt engineering.

Nedbaylo and Hristovski (2024)

2024 GPT-3.5 and GPT-4 Scientific papers and literature related to biomedical concepts

Only a qualitative evaluation was per- formed in this paper

Accuracy: 90% A LLaMA-based model is fine-tuned to extract metadata from biomedical database records, target- ing chromatin immunoprecipitation (ChIP) data.

Cinquin (2024) 2024 ChIP-GPT (LLaMa) Metadata from Chromatin Immunopre- cipitation Sequencing (ChIP-Seq) ex- periments.

Gartlehner et al. (2024) 2024 Claude 2 The research paper focuses on extract- ing several types of biomedical data el- ements from published studies, includ- ing study identifiers, characteristics of study participants, and outcome data.

Accuracy: 96.3%, F1-score: 98%

The study uses the Claude 2 LLM to extract sev- eral types of biomedical elements from published studies in medical literature.

Mashatian et al. (2024) 2024 GPT-4 Scientific papers related to diabetes and diabetic foot care.

Accuracy: 98% A RAG model was developed to extract accurate medical knowledge about diabetes and diabetic foot care for laypersons with an eighth-grade lit- eracy level, using prompt engineering.

Tao et al. (2024) 2024 GPT-4 HIV genetic sequence data, antiviral treatment histories, and the effects of mutations on susceptibility to antiviral drugs from papers on HIV drug resis- tance (HIVDR).

Accuracy: 86.9%, Recall 72.5%, Preci- sion 87.4%

An automated pipeline using GPT-4 was created to evaluate the accuracy of responses to queries about published papers on HIV drug resistance.

to the issue of hallucinations and false positives, which have been identified across multiple studies. For example, the GPT-4 model in Tao et al. (2024)’s study showed a higher tendency for false positives in single-question mode, raising concerns about the con- sistency and reliability of LLMs when applied to in- dividual biomedical queries. Likewise, the hallucina- tions observed in Claude 2’s responses in Gartlehner et al. (2024)’s work underlines the need for more ro- bust evaluation methods to assess generated content’s accuracy and factual correctness.

to evidence synthesis in a transparent and verifiable manner.

6 Conclusion

This review aims to highlight the increasing role of natural language processing and LLMs in biomed- ical research, particularly for automating tasks like literature-based discovery, clinical trial data extrac- tion, and answering complex scientific questions. Al- though these models show great promise, they also reveal significant shortcomings. Many rely on preex- isting datasets and struggle with more nuanced tasks such as making inferences, understanding context, and dealing with implicit information. Issues like hal- lucinations and false positives in several studies fur- ther underscore the need for stronger fact-checking and better handling of contextual information.

As we can observe from the current state of the field, developing a unified benchmark to standard- ize the evaluation of LLMs across evidence synthesis in diverse biomedical tasks is crucial to advance the field. This benchmark must evaluate the model’s ac- curacy, contextual comprehension, insights capabil- ity, generalizability, and the capacity to process un- structured data commonly found in this area. Fur- thermore, recent advancements in LLM retrieval tech- niques, such as RAG techniques, could significantly enhance evidence synthesis, as these techniques not only improve the quality of generated responses but also allow for the models to deal with the novel in- coming literature, on top of enabling the retrieval of the relevant sources, ensuring that LLMs contribute

A major challenge is the lack of a unified bench- mark across various tasks. The current variety of datasets and evaluation metrics makes it difficult to compare models directly or evaluate how well they generalize to new problems. Fine-tuned models like ChIP-GPT and Curie perform well in narrow areas but are less proven in broader contexts. Similarly,

older encoder-based models such as RoBERTa and BioBERT have scalability limitations and are difficult to manage the complexity of unstructured medical lit- erature.

Cinquin, O. (2024). Chip-gpt: a managed large lan- guage model for robust data extraction from biomed- ical database records. Briefings in bioinformatics, 25(2):bbad535.

Looking ahead, efforts should focus on improving models’ ability to grasp context, addressing the prob- lem of hallucinations, and creating unified bench- marks to standardize evaluation across tasks. Inte- grating techniques like knowledge graphs, multi-hop reasoning, and retrieval-augmented generation (RAG) could help close the current performance gaps, espe- cially for complex evidence synthesis. While LLMs hold great potential in healthcare, they still require improvements in architecture, evaluation methods, and unstructured data handling to fully realize their transformative potential in biomedical research and automated evidence synthesis.

Dagdelen, J., Dunn, A., Lee, S., Walker, N., Rosen, A. S.,

Ceder, G., Persson, K. A., and Jain, A. (2024). Structured information extraction from scientific text with large lan- guage models. Nature Communications, 15(1):1418.

de la Torre-L´opez, J., Ram´ırez, A., and Romero, J. R.

(2023). Artificial intelligence to automate the sys- tematic review of scientific literature. Computing, 105(10):2171–2194.

Gartlehner, G., Kahwati, L., Hilscher, R., Thomas, I., Kug-

ley, S., Crotty, K., Viswanathan, M., Nussbaumer-Streit, B., Booth, G., Erskine, N., et al. (2024). Data extraction for evidence synthesis using a large language model: A proof-of-concept study. Research Synthesis Methods.

Gupta, R., Pandey, G., and Pal, S. K. (2024). Automating

government report generation: A generative ai approach for efficient data extraction, analysis, and visualization. Digital Government: Research and Practice.

ACKNOWLEDGEMENTS

This study was funded by the S˜ao Paulo Re- search Foundation (FAPESP) grants 2013/07375−0, 2019/07665 −4, 2023/14427 −8, 2024/00789 −8, and 2024/01336 −7 as well as the National Council for Scientific and Technological Development grants 308529/2021−9 and 400756/2024−2.

Ignat, O., Jin, Z., Abzaliev, A., Biester, L., Castro, S.,

Deng, N., Gao, X., Gunal, A., He, J., Kazemi, A., et al. (2023). Has it all been solved? open nlp research ques- tions not solved by large language models. arXiv preprint arXiv:2305.12544.

Khraisha, Q., Put, S., Kappenberg, J., Warraitch, A., and

Hadfield, K. (2024). Can large language models replace humans in systematic reviews? evaluating gpt-4’s effi- cacy in screening and extracting data from peer-reviewed and grey literature in multiple languages. Research Syn- thesis Methods.


## REFERENCES

Alambo, A., Banerjee, T., Thirunarayan, K., and Raymer,

M. (2022). Entity-driven fact-aware abstractive summa- rization of biomedical literature. In 2022 26th Interna- tional Conference on Pattern Recognition (ICPR), pages 613–620. IEEE.

Lasserson, T. J., Thomas, J., and Higgins, J. P. (2019). Start-

ing a review. Cochrane handbook for systematic reviews of interventions, pages 1–12.

Mashatian, S., Armstrong, D. G., Ritter, A., Robbins, J.,

Alshami, A., Elsayed, M., Ali, E., Eltoukhy, A. E., and

Aziz, S., Alenabi, I., Huo, M., Anand, T., and Tavako- lian, K. (2024). Building trustworthy generative artificial intelligence for diabetes care and limb preservation: A medical knowledge extraction case. Journal of Diabetes Science and Technology, page 19322968241253568.

Zayed, T. (2023). Harnessing the power of chatgpt for automating systematic review process: Methodology, case study, limitations, and future directions. Systems, 11(7):351.

Beller, E. M., Chen, J. K.-H., Wang, U. L.-H., and Glasziou,

Meho, L. I. (2007). The rise and rise of citation analysis.

P. P. (2013). Are systematic reviews up-to-date at the time of publication? Systematic reviews, 2:1–6.

Physics World, 20(1):32.

Nedbaylo, A. and Hristovski, D. (2024). Implementing literature-based discovery (lbd) with chatgpt. In 2024 47th MIPRO ICT and Electronics Convention (MIPRO), pages 120–125. IEEE.

Bolanos, F., Salatino, A., Osborne, F., and Motta, E. (2024).

Artificial intelligence for literature reviews: Opportuni- ties and challenges. arXiv preprint arXiv:2402.08565.

Bornmann, L., Haunschild, R., and Mutz, R. (2024). Accel-

Panayi, A., Ward, K., Benhadji-Schaff, A., Ibanez-Lopez,

erating scientific progress with preprints. Nature Compu- tational Science, 4(5):311–311.

A. S., Xia, A., and Barzilay, R. (2023). Evaluation of a prototype machine learning tool to semi-automate data extraction for systematic literature reviews. Systematic Reviews, 12(1):187.

Burgard, T. and Bittermann, A. (2023). Reducing literature

screening workload with machine learning. Zeitschrift f¨ur Psychologie.

Saxena, S., Sangani, R., Prasad, S., Kumar, S., Athale, M.,

Awhad, R., and Vaddina, V. (2022). Large-scale knowl- edge synthesis and complex information retrieval from biomedical documents. In 2022 IEEE International Con- ference on Big Data (Big Data), pages 2364–2369. IEEE.

Singh, S. (2017). How to conduct and interpret systematic

reviews and meta-analyses. Clinical and translational gastroenterology, 8(5):e93.

Sonnenburg, A., van der Lugt, B., Rehn, J., Wittkowski,

P., Bech, K., Padberg, F., Eleftheriadou, D., Dobrikov, T., Bouwmeester, H., Mereu, C., et al. (2024). Artifi- cial intelligence-based data extraction for next genera- tion risk assessment: Is fine-tuning of a large language model worth the effort? Toxicology, 508:153933.

Tao, K., Osman, Z. A., Tzou, P. L., Rhee, S.-Y., Ahluwalia,

V., and Shafer, R. W. (2024). Gpt-4 performance on querying scientific publications: reproducibility, accu- racy, and impact of an instruction sheet. BMC Medical Research Methodology, 24(1):139.

Yu, W., Pang, T., Liu, Q., Du, C., Kang, B., Huang, Y.,

Lin, M., and Yan, S. (2023). Bag of tricks for training data extraction from language models. In International Conference on Machine Learning, pages 40306–40320. PMLR.
