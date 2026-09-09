---
workspace_id: "SCI-000179"
doi: "10.3844/jcssp.2026.2082.2091"
title: "An AI-Assisted Research Automation System for Scholarly Paper Retrieval and Review With Workflow Orchestration"
year: 2026
extraction_engine: "pymupdf"
---
# 2026 Tongnamtiang An AIAssisted Research Automation System for Scho

Journal of Computer Science

Research Article  An AI-Assisted Research Automation System for Scholarly  Paper Retrieval and Review With Workflow Orchestration

Sompoch Tongnamtiang, Manirath Wongsim and Natarpha Satchawatee

Mahasarakham Business School, Mahasarakham University, Mahasarakham, Thailand

Article history  Received: 28-12-2025   Revised: 17-03-2026  Accepted: 09-06-2026    Corresponding Author:  Natarpha Satchawatee  Mahasarakham Business  School, Mahasarakham  University, Mahasarakham,  Thailand  Email: natarpha.s@msu.ac.th


## Abstract: The rapid growth of scholarly publications has increased the

complexity of conducting rigorous and reproducible literature reviews, while 
traditional manual review processes are increasingly constrained by 
information overload, time consumption, and inconsistencies in screening 
decisions. This study proposes an AI-assisted research automation system 
that integrates workflow orchestration with literature retrieval and review 
support mechanisms to address these challenges. The workflow supports 
multiple stages of the literature review process, including paper retrieval, 
preliminary screening, and review management, while maintaining human 
oversight and methodological control. Artificial intelligence, particularly 
natural language processing through a large language model, is employed as 
a supportive component to enhance efficiency and consistency rather than to 
replace the researcher's judgment. Implemented as a workflow-driven 
process, the system enhances transparency, traceability, and reproducibility 
in review activities. In the observed execution, the retrieval and preparation 
stages processed 20 papers in 21.38 seconds, while AI-assisted abstract 
analysis required 25.02 seconds per paper. These results indicate that 
workflow orchestration can reduce operational workload and support 
systematic literature review practices while preserving research integrity and 
human decision authority.  
 
Keywords: Artificial Intelligence, Workflow-Based Automation, Literature 
Retrieval, Literature Review Framework, Research Automation System 
 
Introduction

screening decisions, and the significant time and cognitive  effort required to conduct rigorous reviews, underscoring  the need for more scalable and transparent review  methodologies (Chen et al., 2020; Wagner et al., 2022;  Zawacki-Richter et al., 2019).

The exponential growth of scholarly publications  across scientific and technological domains has  fundamentally  transformed  academic  knowledge  production. While this expansion has accelerated  innovation and interdisciplinary collaboration, it has also  substantially increased the complexity of conducting  rigorous  and  comprehensive  literature  reviews.  Researchers must navigate vast volumes of heterogeneous  and rapidly evolving information, making it increasingly  difficult  to  ensure  comprehensive  coverage,  methodological consistency, and transparency. As a  result, traditional manual review approaches are  becoming progressively unsustainable, particularly in  multidisciplinary  contexts  characterized  by  terminological diversity and fragmented knowledge  structures (Wagner et al., 2022; Zawacki-Richter et al.,  2019). Empirical evidence  from systematic  and  technology-assisted reviews further highlights persistent  challenges related to information overload, inconsistent

A substantial body of research has therefore explored  the use of artificial intelligence to support and partially  automate systematic literature reviews. Prior studies report  that AI techniques particularly machine learning and  natural language processing can reduce manual workload  and improve consistency in early-stage screening tasks  such as literature searching, relevance classification, and  clustering (Bolaños et al., 2024; Chen et al., 2020; De la  Torre-López et al., 2023; Vargas-Murillo et al., 2023;  Wagner et al., 2022; Zawacki-Richter et al., 2019). More  recent work demonstrates a transition from rule-based  approaches toward learning-based and hybrid human AI  pipelines, including active learning and prioritized  screening, which improve recall and reduce the likelihood  of missing relevant studies (De la Torre-López et al., 2023;  Malik and Terzidis, 2025; Tomczyk, 2025). Nevertheless,

© 2026 Sompoch Tongnamtiang, Manirath Wongsim and Natarpha Satchawatee. This open-access article is distributed

under a Creative Commons Attribution (CC002DBY) 4.0 license.

Sompoch Tongnamtiang et al. / Journal of Computer Science 2026, 22 (7): 2082.2091  DOI: 10.3844/jcssp.2026.2082.2091

this literature consistently emphasizes that AI performs  most effectively when embedded within human-in-the-loop  workflows, as human judgment remains essential for  defining inclusion criteria, validating AI outputs, and  mitigating risks related to  bias and contextual  misinterpretation (Anthuvan et al, 2025; Chen et al., 2020;  Purba et al., 2025; van de Schoot et al., 2025). Collectively,  existing studies reveal that AI-assisted literature review  remains a maturing domain, with most approaches focusing  on isolated tasks rather than integrated, end-to-end review  workflows (Vargas-Murillo et al., 2023; Tomczyk et al.,  2026; Zawacki-Richter et al., 2019).  Beyond literature review automation, multidisciplinary  research on AI-supported decision-making highlights  broader challenges associated with delegating authority to  automated  systems.  Studies  across  healthcare,  management, and education consistently report that while  AI can enhance analytical capacity and efficiency,  excessive reliance on autonomous systems introduces risks  related to accountability, trust erosion, and diffused  responsibility (Alzubaidi et al., 2023; Bleher and Braun,  2022; Dwivedi et  al., 2021). Human-in-the-loop  mechanisms  are  therefore  critical  for  ensuring  transparency,  contextual  judgement,  and  ethical  responsibility, particularly in high-stakes or complex  decision environments (Alzubaidi et al., 2023; Dwivedi et  al., 2021; Kovari, 2024). Although recent frameworks for  trustworthy AI formalize explainability and controllability  as core principles, existing research remains largely  conceptual or domain-specific, offering limited guidance  on how human oversight is operationalized within  integrated research workflows (Akbar et al., 2024; Bleher  and Braun, 2022; Labkoff et al., 2024; Mora-Cantallops et  al,. 2024; Sakowski and Parks, 2025).

in complex research activities (Cuevas-Vicenttín et al.,  2012; Kanwal et al., 2017), existing AI-assisted literature  review systems remain largely task-centric or phase- specific (Demchenko et al., 2023; Przemysław, 2025).  Limited attention has been given to coordinating AI- assisted tools across the full review lifecycle while  preserving provenance tracking and methodological  accountability. In response to this gap, this study proposes  an AI-assisted research automation framework that  integrates workflow-oriented orchestration with literature  retrieval, review management, and human-in-the-loop  decision control. The framework supports the entire  literature review lifecycle within a unified and auditable  workflow environment, offering a system-level approach to  transparent, reproducible, and ethically grounded AI- assisted literature review practices.

Materials and Methods

System Architecture and Design

The proposed research automation system was  developed to support end-to-end scholarly information  retrieval, analysis, and organization through a workflow- based architecture. The architecture integrates several  functional components, including data acquisition,  processing, AI-assisted analysis, and storage, into a  unified pipeline.

At the core of the architecture is a workflow  orchestration engine implemented using n8n, enabling  sequential and conditional execution across multiple  heterogeneous  data  sources.  This  orchestration  mechanism enables the automation of tasks typically  performed manually, such as retrieving research articles,  filtering redundant records, and extracting key insights  from unstructured textual data.

Concurrently, a growing body of literature has  examined the ethical and integrity-related implications of  AI-assisted research practices. Recent studies caution that  generative and assistive AI systems introduce risks such as  opaque content generation, hallucinated references, and  blurred authorship boundaries, which challenge traditional  norms of academic integrity (Chauhan and Currie, 2024;  Cheng et al., 2025; Dahal, 2024; Dwivedi et al., 2023; Hsu  et al., 2025; Lund et al., 2025; Luomala et al., 2025; Qadhi  et al., 2024). These concerns are exacerbated by tool- centric research practices, where AI applications optimize  isolated tasks such as writing assistance or screening  support without providing systematic workflow integration  or traceability (Kesgin and Ozer, 2025; Motahari et al.,  2025; Silva et al., 2025). As a result, scholars argue that  ethical challenges cannot be addressed solely through usage  guidelines, but instead require system-level designs that  embed  accountability, documentation, and human  oversight throughout the research lifecycle (Hsu et al.,  2025; Qadhi et al., 2024; Silva et al., 2025).  While workflow-oriented automation has long been  recognized as essential for reproducibility and transparency

As illustrated in Figure 1, the architecture is organized  into four main layers:

1) User Interface Layer  2) Data Acquisition Layer  3) Processing and AI Layer   4) Storage and Output Layer

User queries are first processed by the data acquisition  layer to retrieve information from multiple sources. The  retrieved data are subsequently processed through  normalization and deduplication before being analyzed  using AI techniques and stored for further use.

The overall architecture follows a modular design, in  which each component performs a distinct function within  the workflow. The data acquisition layer retrieves scholarly  information from multiple sources, while subsequent  processing ensures data consistency through normalization  and deduplication. AI-assisted analysis applies natural  language processing techniques to interpret, summarize, and  structure the retrieved content. The processed data are then  stored for further analysis and reporting.

2083

Sompoch Tongnamtiang et al. / Journal of Computer Science 2026, 22 (7): 2082.2091  DOI: 10.3844/jcssp.2026.2082.2091

Subsequently, AI-assisted analysis is applied to extract  meaningful insights, summarize content, and structure the  information. The processed data is then stored in a  database for further use, including reporting and  visualization. The workflow is illustrated in Figure 3.

For clarity, the overall workflow can be decomposed  into six sequential stages, as illustrated in Figure 3.

Stage S1 – Request Intake and Validation

As shown in Figure 3 (Stage S1), the workflow begins  with a controlled research request intake and validation  process. Literature search requests are submitted through  a structured input mechanism and undergo authorization  and integrity checks. Invalid or unauthorized requests are  rejected to prevent unintended workflow execution.  Validated requests are logged and assigned unique  identifiers to ensure idempotent behavior, thereby  preventing duplicate processing. This stage establishes a  secure and traceable entry point for the research  automation pipeline.

Fig. 1: Layered architecture of the proposed research

Stage S2 – Multi-Source Data Retrieval

automation system

In Stage S2 (Figure 3), validated research queries are  transformed into standardized search expressions and  dispatched to multiple scholarly data sources. A Google  Scholar-based search interface and open academic  repositories  are integrated to  retrieve candidate  publications. Search operations are executed in parallel  across heterogeneous sources to enhance coverage and  reduce dependency on a single bibliographic database.  Retrieved records are forwarded as raw metadata for  downstream processing.

To enhance flexibility and scalability, a loosely  coupled architecture is adopted, allowing individual  components to be updated or extended without affecting  overall operation. This design is well-suited to dynamic  research environments where data sources and analytical  requirements frequently evolve.

In addition, the workflow-driven approach reduces  repetitive manual tasks and improves operational  efficiency, supporting continuous and reproducible  processing of scholarly data. As a result, large volumes of  information can be managed in a structured and  systematic manner.

Stage S3 – Integration and Deduplication

In Stage S3 (Figure 3), literature records retrieved  from multiple sources are integrated, and redundancies  are eliminated. Metadata from heterogeneous sources is  normalized into a unified internal schema and merged into  a consolidated dataset. Duplicate detection is primarily  performed using DOI-based identifiers. When DOI  information is  unavailable, normalized title–year  combinations are applied as secondary identifiers. This  stage ensures data integrity and prevents redundant  downstream analysis.

Workflow Design

The proposed research automation system consists of  two primary workflows that operate sequentially to  support the overall process of scholarly data retrieval and  analysis.

The first workflow focuses on data acquisition and  retrieval. It begins with user query submission through a  webhook interface, which triggers workflow execution.  Multi-source retrieval is then performed to collect  relevant scholarly information from external platforms  and APIs. This workflow is responsible for gathering raw  research data and preparing it for subsequent processing.  The workflow is illustrated in Figure 2.

Stage S4 – Metadata Validation

In Stage S4 (Figure 3), retrieved records undergo  metadata  validation  and  classification.  Core  bibliographic attributes including title, publication  year, journal or publisher, and abstract availability are  examined and standardized to ensure consistency.  Publisher detection and source classification are  applied to support analytical grouping and filtering.  Only validated records are retained in the master  dataset for subsequent analysis.

The second workflow is dedicated to data processing  and analysis. After the initial data is collected, it  undergoes normalization to ensure consistency in format  and structure. Duplicate records are then removed through  a deduplication process to improve data quality.

2084

Sompoch Tongnamtiang et al. / Journal of Computer Science 2026, 22 (7): 2082.2091  DOI: 10.3844/jcssp.2026.2082.2091

Stage S5 – AI-Assisted Analysis

Data Processing Pipeline

In Stage S5 (Figure 3), the AI-assisted analysis  component of the workflow is implemented. Records  that have not yet been analyzed and that contain valid  DOI information are selected for processing. Abstracts  are retrieved and normalized prior to AI processing. A  large language model is employed to generate  structured analytical outputs, including concise  summaries, thematic keywords, and methodological  descriptors. At this stage, AI-generated outputs  function strictly as decision-support artifacts and do  not constitute final research conclusions.

The data processing pipeline represents a high-level  abstraction of the end-to-end transformation of scholarly  data, beginning with user query submission and  concluding with structured data storage and status  tracking. As illustrated in Figure 4, the pipeline comprises  a sequence of interconnected stages, including multi- source  data  retrieval,  metadata  normalization,  deduplication, metadata validation, AI-assisted analysis,  and persistent storage.

This pipeline provides an abstract, process-oriented  view of how raw scholarly data are progressively refined  into structured analytical records. Unlike the workflow  implementation diagrams presented in Figures 2 and 3,  which depict system-level execution in n8n, Figure 4  highlights the logical flow of data across the core  processing components of the framework.

Stage S6 – Persistence and Status Tracking

In Stage S6 (Figure 3), persistent storage and  workflow state tracking are managed. Validated  metadata and AI-generated analytical outputs are  stored in structured data repositories, and explicit  processing status indicators are updated for each  record. This design enables incremental execution and  workflow  resumption, ensuring that previously  processed records are not reanalyzed. The separation of  AI-assisted analysis (S5) from persistence and status  management  (S6)  reinforces  transparency,  accountability, and responsible use of AI.

This abstraction aligns with the stage-based workflow  (S1–S6) and provides a unified view of how scholarly data  are progressively transformed across the entire pipeline.

Implementation Details

The workflow orchestration engine was implemented  using n8n, a low-code automation platform that supports  event-driven execution and integration with external  services.

For clarity, the stage-based structure of the proposed  research automation workflow is summarized in Table 1.

At the core, a workflow orchestration engine  coordinates sequential and conditional operations across  multiple stages. This engine supports event-driven  execution through webhook-based triggers, allowing user  queries to initiate the workflow in real time.    Table 1: Overview of Processing Stages in the Workflow

Together, these stages illustrate how the framework  systematically integrates workflow orchestration and AI- assisted analysis while preserving transparency and  reproducibility.

Stage  Stage Name  Primary Function  S1  Request Intake and Validation  Validates and logs research requests and prevents duplicate execution  S2  Multi-Source Data Retrieval  Retrieves candidate publications from multiple academic data sources  S3  Integration and Deduplication  Normalizes, merges, and removes duplicate records  S4  Metadata Validation  Cleans and classifies bibliographic metadata  S5  AI-Assisted Analysis  Generates AI-supported summaries and analytical attributes  S6  Persistence and Status Tracking  Stores validated data and tracks processing states for reproducibility

Fig. 2: Data acquisition and retrieval workflow implemented using n8n

2085

Sompoch Tongnamtiang et al. / Journal of Computer Science 2026, 22 (7): 2082.2091  DOI: 10.3844/jcssp.2026.2082.2091

Fig. 3: Data processing and AI-assisted analysis workflow implemented using n8n

The data processing component performs normalization  and deduplication to ensure consistency and data quality.  Metadata from different sources is mapped into a unified  schema, and duplicate records are identified primarily using  DOI-based matching. In cases where DOI information is  unavailable, alternative matching strategies based on title and  publication year are applied.

The AI-assisted analysis component leverages a large  language model  to  process  textual information,  particularly abstracts. Prior to analysis, textual data are  normalized and validated to ensure input quality. The  model is then used to generate structured outputs,  including summaries, keywords, and methodological  descriptors. These outputs are intended to support  research analysis and are not treated as definitive  conclusions.

For data storage and management, structured data  repositories are used to persist both raw and processed  information, with each record linked to processing status  indicators for incremental tracking. Each record is  associated with processing status indicators, enabling  incremental execution and preventing redundant analysis.  This design supports workflow resumption and enhances  system reliability.

Fig. 4: Abstract data processing pipeline of the research

automation system

Overall, the implementation emphasizes modularity,  scalability, and reproducibility. The integration of  workflow orchestration with AI-assisted analysis enables  the automation of complex research tasks while  maintaining transparency and explicit control over each  processing stage.

The orchestration mechanism enables modular design,  where individual components can be independently  configured, monitored, and extended.

For data acquisition, multiple scholarly sources are  integrated through web-based search interfaces and open  metadata repositories. Queries are programmatically  transformed into standardized search expressions and  dispatched to these sources. Retrieved data are collected  in structured formats to facilitate downstream processing.


## Results and Discussion

This section reports the observed results of the  implemented workflow and discusses their implications

2086

Sompoch Tongnamtiang et al. / Journal of Computer Science 2026, 22 (7): 2082.2091  DOI: 10.3844/jcssp.2026.2082.2091

for AI-assisted literature review practice. The discussion  focuses on system behavior, workflow effectiveness, and  methodological contributions rather than domain-specific  research findings, as the primary objective of this study is  to evaluate the performance and design of the research  automation framework.

coverage diversity. The retrieval and normalization  processes were completed within approximately 15  seconds, demonstrating the effectiveness of workflow- based orchestration for scalable and repeatable literature  discovery.

Deduplication and Metadata Validation

Workflow Execution and System Outputs

Following retrieval, the workflow integrated results  from  multiple  sources  and  applied  DOI-based  deduplication in Stage S3. In the observed execution, no  duplicate records were detected, resulting in a clean  dataset of 20 unique publications. This outcome reflects  the robustness of DOI-based key generation and the  effectiveness of pre-filtering mechanisms.

The stage-based workflow was successfully executed  across all processing stages (S1–S6), demonstrating the  feasibility of the end-to-end literature review pipeline.  The workflow execution consistently handled structured  research requests, multi-source retrieval, metadata  processing, AI-assisted analysis, and persistent storage  without redundant execution.

Subsequently, metadata validation and classification  were conducted in Stage S4. Bibliographic attributes,  including publication year, journal or publisher name, and  abstract availability, were standardized and verified. The  validated records were stored in a master dataset, forming  a reliable foundation for downstream AI-assisted analysis  and ensuring data consistency and integrity.

Using the query keywords “Artificial Intelligence”  and “Internet of Things,” the workflow retrieved and  processed 20 scholarly records during the retrieval and  preparation stages (S1–S4). These stages required a total  execution time of 21.38 seconds. A summary of execution  outcomes and stage-level processing times is presented in  Table 2.

AI-Assisted Abstract Review Performance

Overall, the results show that the workflow can  reliably automate core literature review tasks while  maintaining transparency and explicit control across  processing stages.

Stage S5 evaluated the AI-assisted abstract analysis  module using a representative paper. The AI review  process,  including abstract verification,  bilingual  summarization (Thai and English), and structured output  parsing, required 25.02 seconds per paper, inclusive of a  2-second intentional delay for API rate regulation.  Robust handling of incomplete metadata was  observed. When abstracts were unavailable, the AI  module explicitly documented this limitation and  generated context-aware summaries based on available  bibliographic information. Key characteristics of the AI- assisted abstract analysis are summarized in Table 3.

Multi-Source Retrieval and Coverage

During Stage S2, the workflow performed a multi- source scholarly search by querying Google Scholar and  OpenAlex. This design enabled the retrieval of  heterogeneous publication records spanning different  publishers, venues, and publication years. In the observed  execution, a total of 20 candidate papers were retrieved  and normalized into a unified data schema.

These observations suggest that AI-assisted analysis  can support qualitative literature review, although its  effectiveness  remains  dependent  on  metadata  completeness and input quality.

The integration of multiple scholarly sources reduced  reliance on a single bibliographic repository and enhanced


> **Table 2: Observed execution outcomes and processing time across workflow stages (S1–S6)**

Stage  Description  No. of Records  Execution Time (Observed)  S1  Research request intake and validation  1 request  < 1 s  S2  Multi-source scholarly search  20  ~15 s  S3  Result integration and deduplication  20 → 20  ~3 s  S4  Metadata validation and classification  20  ~2 s  S5  AI-assisted abstract analysis  1  ~25.0 s  S6  Knowledge persistence and status tracking  1  < 1 s  Total (S1–S4)  Retrieval and preparation  20 papers  21.38 s  Total (S5–S6)  AI review pipeline  1 paper  25.02 s


> **Table 3: Characteristics of AI-assisted abstract analysis**

Aspect  Observation  Input type  Abstract text (or metadata-only if abstract unavailable)  Output languages  Thai and English  Handling of the missing abstract  Explicitly documented by AI  Average processing time  ~25 s per paper  Execution mode  Incremental, per-record

2087

Sompoch Tongnamtiang et al. / Journal of Computer Science 2026, 22 (7): 2082.2091  DOI: 10.3844/jcssp.2026.2082.2091

While the workflow demonstrates stable execution, its  current design prioritizes process transparency over  analytical depth, which may limit its effectiveness in  complex domain-specific reviews.

requests. These results indicate that AI-assisted analysis  is the dominant factor in overall processing time and  should be interpreted as descriptive rather than  comparative performance evidence.

Third, the AI-assisted analysis was performed on a  limited number of records in the current experiment.  Although the workflow supports incremental and  resumable execution, the cumulative processing time of  AI-intensive stages is expected to increase proportionally  with dataset size. This suggests that scalability may  become a constraint in large-scale applications unless  optimization strategies such as batching, parallel  processing, or adaptive scheduling are introduced.

Incremental Processing and Knowledge Persistence

Upon completion of AI-assisted analysis, processed  records were persistently stored with explicit status  indicators in the knowledge base. Stage S6 recorded each  paper’s processing state, enabling incremental execution  and preventing redundant reprocessing in subsequent  workflow runs.

The separation between retrieval-intensive stages (S1– S4) and AI-intensive stages (S5–S6) allows selective re- execution of AI analysis without repeating earlier  retrieval steps. This design supports iterative literature  review workflows and facilitates continuous monitoring  of newly retrieved publications.

Fourth, the effectiveness of the analysis is inherently  dependent on the completeness and consistency of  metadata across data sources. Variations in abstract  structure, missing fields, and inconsistencies between  sources were observed during system execution. While  the workflow includes mechanisms to handle missing  data, the analytical depth and consistency of AI-generated  outputs may still be affected. Future extensions may  incorporate full-text analysis, citation context extraction,  or structured knowledge integration to address these  limitations.

Overall,  the  workflow  supports  transparent  processing, enables traceability of analytical states, and  facilitates efficient management of repeated executions.

In practice, variations in metadata quality and abstract  structure across different data sources occasionally  resulted in inconsistent AI-generated outputs. For  example, records with incomplete abstracts or ambiguous  terminology led to summaries that required manual  verification before being used in further analysis. This  observation indicates that, while the workflow can  automate large portions of the review process, certain  edge cases still require human intervention to ensure  analytical reliability.

Finally, this study focuses on system design and  operational feasibility rather than comparative evaluation.  The absence of controlled benchmarking against manual  review processes or alternative automation approaches  limits the ability to generalize the observed performance  advantages. Future research should include comparative  experiments to assess time efficiency, consistency, and  reviewer workload across different review methods. In  addition, broader validation across diverse research  domains and larger datasets would provide stronger  evidence of the generalizability and practical applicability  of the approach.

Limitations and Future Directions

Although the workflow was successfully implemented  and demonstrated stable end-to-end execution, several  limitations should be acknowledged.

First, the current implementation does not include a  formal mechanism for detecting misinformation or  verifying the factual correctness of AI-generated outputs.  The analysis is constrained by the availability and quality  of input metadata, particularly abstracts. This dependency  introduces a risk of incomplete or potentially misleading  interpretations when source information is limited. This  limitation indicates that the current workflow lacks an  explicit mechanism for verifying factual correctness,  which may affect analytical reliability in real-world  review settings.


## Conclusion

This study proposes and demonstrates a stage-based  AI-assisted research automation workflow designed to  support transparent, reproducible, and systematically  controlled literature review processes. By integrating  workflow orchestration with multi-source literature  retrieval, AI-assisted abstract analysis, and persistent state  tracking, the framework positions artificial intelligence as  a structured decision-support mechanism rather than an  autonomous replacement for human researchers.

Second, the evaluation conducted in this study is  primarily feasibility-oriented. The reported execution  times reflect observed system behavior under a specific  configuration rather than optimized or benchmarked  performance.  For  example,  the  retrieval  and  preprocessing stages (S1–S4) processed 20 papers in  approximately 21.38 seconds, while the AI-assisted  analysis stage (S5) required approximately 25.02 seconds  per paper, including an intentional delay to regulate API

The empirical results confirm the feasibility of  executing an end-to-end literature review pipeline within  a workflow-oriented environment. Specifically, the  retrieval and preparation stages (S1–S4) processed 20  scholarly records within 21.38 seconds, while the AI- assisted analysis stage (S5) required approximately 25.02  seconds per paper. These findings highlight that, although  AI-assisted analysis introduces additional computational

2088

Sompoch Tongnamtiang et al. / Journal of Computer Science 2026, 22 (7): 2082.2091  DOI: 10.3844/jcssp.2026.2082.2091

overhead, it provides structured analytical outputs that  enhance consistency and reduce manual effort in early- stage review activities.

Funding Information

This research was funded by Mahasarakham Business  School, Mahasarakham University, Thailand.

From a methodological perspective, the stage-based  architecture represents a deliberate design choice aimed at  improving traceability and controllability across the  research workflow. The explicit separation between  retrieval-intensive stages and AI-intensive stages enables  incremental execution and prevents redundant processing,  while also allowing human intervention at critical  decision points. However, this modular design introduces  trade-offs, particularly in terms of increased orchestration  complexity and processing latency in AI-dependent  stages.

Author’s Contributions

Sompoch Tongnamtiang: initiated the study and led  the  overall  system  development,  including  the  architectural design of the stage-based AI-assisted  research automation workflow. He implemented the  workflow, performed system execution and operational  analysis, synthesized the findings, and drafted the  manuscript with all associated figures and tables.

Manirath  Wongsim:  Offered  theoretical  and  methodological insights related to research automation  and AI-supported review processes, supported the  interpretation  of  system-level  implications  and  limitations, and critically reviewed the manuscript to  enhance clarity, structure, and completeness.

Furthermore, the study acknowledges that the  effectiveness of AI-assisted analysis is inherently  constrained by the availability and quality of metadata,  especially abstracts. In cases of incomplete data, the depth  of AI-generated insights may be limited, reinforcing the  importance  of  maintaining  human  oversight.  Additionally, the absence of automated mechanisms for  validating the factual correctness of AI-generated outputs  highlights an important area for future development.

Natarpha Satchawatee: Contributed to shaping the  research direction and methodological alignment,  examined the coherence and validity of the design, and  provided substantive editorial revisions to strengthen the  analytical depth and scholarly presentation of the  manuscript.

Compared with existing approaches that focus on  isolated tools or task-level automation, the framework  contributes a system-level perspective by embedding AI  within a structured, auditable, and reproducible workflow.  This approach supports iterative literature review,  continuous data integration, and long-term research  monitoring while preserving methodological rigor.

Ethics

This study does not involve human participants or  personal data. All analyses are based on publicly available  bibliographic metadata and scholarly abstracts, and  artificial intelligence is used solely as a decision-support  tool under human oversight.

In conclusion, this work demonstrates that workflow- based orchestration provides a practical foundation for  integrating AI into scholarly review processes in a  responsible and  controlled manner.  Rather  than  maximizing automation autonomy, this work emphasizes  transparency, accountability, and human-in-the-loop  decision-making as core design principles. Future  research may further explore optimization strategies, full- text analysis, and validation mechanisms to strengthen  both the efficiency and reliability of AI-assisted research  workflows.

Conflicts of Interest

The authors declare that there are no conflicts of  interest associated with this research.


## References

Akbar, M. A., Khan, A. A., Mahmood, S., Rafi, S., &

Demi, S. (2024). Trustworthy artificial intelligence:  A decision-making taxonomy of potential challenges.  Software: Practice and Experience, 54(9), 1621– 1650.   https://doi.org/10.1002/spe.3216  Alzubaidi, L., Al-Sabaawi, A., Bai, J., Dukhan, A.,

Acknowledgment

The authors would like to express their sincere  appreciation to colleagues and peers who provided  valuable feedback during the development and refinement  of the proposed AI-assisted research automation  workflow. Their insights contributed to improving the  clarity,  methodological  rigor,  and  system-level  articulation of this study.

Alkenani, A. H., Al-Asadi, A., Alwzwazy, H. A.,  Manoufali, M., Fadhel, M. A., Albahri, A. S.,  Moreira, C., Ouyang, C., Zhang, J., Santamaría, J.,  Salhi, A., Hollman, F., Gupta, A., Duan, Y., Rabczuk,  T., … Gu, Y. (2023). Towards Risk‐Free  Trustworthy Artificial Intelligence: Significance and  Requirements. International Journal of Intelligent  Systems, 2023(1), 4459198.  https://doi.org/10.1155/2023/4459198

The authors also acknowledge the constructive  comments and suggestions from anonymous reviewers,  which significantly enhanced the organization, technical  depth, and presentation quality of the manuscript.

2089

Sompoch Tongnamtiang et al. / Journal of Computer Science 2026, 22 (7): 2082.2091  DOI: 10.3844/jcssp.2026.2082.2091

Dwivedi, Y. K., Hughes, L., Ismagilova, E., Aarts, G.,

Anthuvan, T., Prabhuram, S., Maheshwari, K., & Rathi,

Coombs, C., Crick, T., Duan, Y., Dwivedi, R.,  Edwards, J., Eirug, A., Galanos, V., Ilavarasan, P. V.,  Janssen, M., Jones, P., Kar, A. K., Kizgin, H.,  Kronemann, B., Lal, B., Lucini, B., … Williams, M.  D.  (2021).  Artificial  Intelligence  (AI):  Multidisciplinary  perspectives  on  emerging  challenges, opportunities, and agenda for research,  practice  and  policy. International  Journal  of  Information Management, 57, 101994.   https://doi.org/10.1016/j.ijinfomgt.2019.08.002  Dwivedi, Y. K., Kshetri, N., Hughes, L., Slade, E. L.,

S. (2025). SLRAI: A Systematic Review and  Methodological Framework for AI-Augmented  Evidence  Synthesis  with  Human-in-the-Loop  Integration. SSRN Electronic Journal, 39.  https://doi.org/http://10.2139/ssrn.5394910  Bleher, H., & Braun, M. (2022). Diffused responsibility:

attributions of responsibility in the use of AI-driven  clinical  decision  support  systems. AI  and  Ethics, 2(4), 747–761.   https://doi.org/10.1007/s43681-022-00135-x  Bolaños, F., Salatino, A., Osborne, F., & Motta, E. (2024).

Jeyaraj, A., Kar, A. K., Baabdullah, A. M., Koohang,  A., Raghavan, V., Ahuja, M., Albanna, H.,  Albashrawi, M. A., Al-Busaidi, A. S., Balakrishnan,  J., Barlette, Y., Basu, S., Bose, I., Brooks, L., Buhalis,  D., … Wright, R. (2023). Opinion Paper: “So what if  ChatGPT wrote it?” Multidisciplinary perspectives  on opportunities, challenges and implications of  generative conversational AI for research, practice  and policy. International Journal of Information  Management, 71, 102642.   https://doi.org/10.1016/j.ijinfomgt.2023.102642  Hsu, H.-Y., Hakouz, A., & Fotouhi, G. (2025). Towards

Artificial  intelligence  for  literature  reviews:  opportunities and challenges. Artificial Intelligence  Review, 57(10), 259.   https://doi.org/10.1007/s10462-024-10902-3  Chauhan, C., & Currie, G. (2024). The Impact of

Generative Artificial Intelligence on Research  Integrity in Scholarly Publishing. The American  Journal of Pathology, 194(12), 2234–2238.   https://doi.org/10.1016/j.ajpath.2024.10.001  Chen, L., Chen, P., & Lin, Z. (2020). Artificial

responsible generative AI in academia: a synthesis of  AI policies on academic writing in the field of  educational research. AI and Ethics, 5(5), 5467– 5484. https://doi.org/10.1007/s43681-025-00794-6  Kanwal, S., Khan, F. Z., Lonie, A., & Sinnott, R. O.

Intelligence  in  Education:  A  Review. IEEE  Access, 8, 75264–75278.   https://doi.org/10.1109/access.2020.2988510  Cheng, A., Calhoun, A., & Reedy, G. (2025). Artificial

intelligence-assisted  academic  writing:  recommendations for ethical use. Advances in  Simulation, 10(1), 22.   https://doi.org/10.1186/s41077-025-00350-6  Cuevas-Vicenttín, V., Dey, S., Köhler, S., Riddle, S., &

(2017). Investigating reproducibility and tracking  provenance – A genomic workflow case study. BMC  Bioinformatics, 18(1), 337.   https://doi.org/10.1186/s12859-017-1747-0  Kesgin, K., & Ozer, D. Z. (2025). BiBLoX realtime

Ludäscher, B. (2012). Scientific Workflows and  Provenance: Introduction and Research Opportunities.  Datenbank-Spektrum, 12(3), 193–203.   https://doi.org/10.1007/s13222-012-0100-z  Dahal, N. (2024). Ethics’ and ‘Integrity’ in Research in

science trend mapping MLdriven forecasting.  Discover  Artificial  Intelligence,  5(1),  422.  https://doi.org/10.1007/s44163-025-00693-z  Kovari, A. (2024). AI for Decision Support: Balancing

Accuracy, Transparency, and Trust Across Sectors.  Information, 15(11), 725.   https://doi.org/10.3390/info15110725  Labkoff, S., Oladimeji, B., Kannry, J., Solomonides, A.,

the Era of Generative AI—Are We Ready to  Contribute to Scientific Inquiries? GS Spark: Journal  of Applied Academic Discourse, 2(1), 1–6.  https://doi.org/10.5281/zenodo.14828619  De la Torre-López, J., Ramírez, A., & Romero, J. R.

Leftwich, R., Koski, E., Joseph, A. L., Lopez- Gonzalez, M., Fleisher, L. A., Nolen, K., Dutta, S.,  Levy, D. R., Price, A., Barr, P. J., Hron, J. D., Lin, B.,  Srivastava, G., Pastor, N., Luque, U. S., … Quintana,  Y.  (2024).  Toward  a  responsible  future:  recommendations for AI-enabled clinical decision  support. Journal  of  the  American  Medical  Informatics Association, 31(11), 2730–2739.  https://doi.org/10.1093/jamia/ocae209  Lund, B., Mannuru, N. R., Teel, Z. A., Lee, T. H., Ortega,

(2023). Artificial intelligence to automate the  systematic review of scientific literature. Computing,  105(10), 2171–2194.   https://doi.org/10.1007/s00607-023-01181-x  Demchenko, Y., Gallenmuller, S., Fdida, S., Andreou, P.,

Crettaz, C., & Kirkeng, M. (2023). Experimental  Research Reproducibility and Experiment Workflow  Management. 2023 15th International Conference on  COMmunication  Systems  &  NETworkS  (COMSNETS), 835–840.   https://doi.org/10.1109/comsnets56262.2023.10041 378

N. J., Simmons, S., & Ward, E. (2025). Student  Perceptions of AI-Assisted Writing and Academic  Integrity: Ethical Concerns, Academic Misconduct,  and Use of Generative AI in Higher Education. AI in  Education, 1(1), 2.   https://doi.org/https://doi.org/10.3390/aieduc1010002

2090

Sompoch Tongnamtiang et al. / Journal of Computer Science 2026, 22 (7): 2082.2091  DOI: 10.3844/jcssp.2026.2082.2091

Luomala, M., Naarmala, J., & Tuomi, V. (2025).

Sakowski, J. A., & Parks, A. (2025). AI-assisted

Technology-Assisted  Literature  Reviews  with  Technology of Artificial Intelligence: Ethical and  Credibility Challenges. Procedia Computer Science,  256, 378–387.   https://doi.org/10.1016/j.procs.2025.02.133  Malik, F. S., & Terzidis, O. (2025). A hybrid framework

Literature Reviews in Graduate Student Research:  How  Good  Are  They? Journal  of  Health  Administration Education, 41(2), 333–350.  Tomczyk, P. (2025). Automating the Systematic

Literature Review Process in Management Science  Using Artificial Intelligence. Marketing of Scientific  and Research Organizations, 56(2), 25–42.   https://doi.org/10.2478/minib-2025-0007  Tomczyk, P., Brüggemann, P., & Vrontis, D. (2026). AI

for  creating  artificial  intelligence-augmented  systematic literature reviews. Management Review  Quarterly, 76, 2031–2057.   https://doi.org/10.1007/s11301-025-00522-8  Mora-Cantallops, M., García-Barriocanal, E., & Sicilia,

meets academia: transforming systematic literature  reviews. EuroMed Journal of Business, 21(1), 345– 369. https://doi.org/10.1108/emjb-03-2024-0055  van de Schoot, R., Messina Coimbra, B., Evenhuis, T.,

M.-Á. (2024). Trustworthy AI Guidelines in  Biomedical  Decision-Making  Applications:  A  Scoping  Review.  Big  Data  and  Cognitive  Computing, 8(7), 73.   https://doi.org/10.3390/bdcc8070073  Motahari, H. N., & CheshmehSohrabi, M. (2025).

Lombaers, P., Weijdema, F., de Bruin, L., Neeleman,  R., Grandfield, E., Sijbrandij, M., Teijema, J. J.,  Jalsovec, E., Bron, M. P., Winter, S., de Bruin, J., &  van Zuiden, M. (2025). The hunt for the last relevant  paper: blending the best of humans and AI. European  Journal of Psychotraumatology, 16(1), 2546214.   https://doi.org/10.1080/20008066.2025.2546214  Vargas-Murillo, A. R., Pari-Bedoya, I. N. M. de la A., &

SPECTRUM SRA: An R Shiny Application to  Automate Systematic Reviews Using Artificial  Intelligence and Large Language Models. Research  Square, 41(1–2), 100–115.   https://doi.org/https://doi.org/10.21203/rs.3.rs- 7265470/v1  Purba, S. W. D., Silitonga, B. N., & Yang, J. J. (2025).

Guevara-Soto, F. de J. (2023). Challenges and  Opportunities of AI-Assisted Learning: A Systematic  Literature Review on the Impact of ChatGPT Usage  in Higher Education. International Journal of  Learning, Teaching and Educational Research,  22(7), 122–135.   https://doi.org/10.26803/ijlter.22.7.7  Wagner, G., Lukyanenko, R., & Paré, G. (2022). Artificial

AI-Assisted Learning Systematic Reviews. Turkish  Online Journal of Distance Education, 26(4), 77–93.   https://doi.org/10.17718/tojde.1591404  Qadhi, S. M., Alduais, A., Chaaban, Y., & Khraisheh, M.

(2024). Generative AI, Research Ethics, and Higher  Education Research: Insights from a Scientometric  Analysis. Information, 15(6), 325.   https://doi.org/10.3390/info15060325  Silva, J. C. M. C., Gouveia, R. P., Zielinski, K. M. C.,

intelligence and the conduct of literature reviews.  Journal of Information Technology, 37(2), 209–226.   https://doi.org/10.1177/02683962211048201  Zawacki-Richter, O., Marín, V. I., Bond, M., &

Oliveira, M. C. F., Amancio, D. R., Bruno, O. M., &  Oliveira, O. N. (2025). AI-Assisted Tools for  Scientific Review Writing: Opportunities and  Cautions. ACS Applied Materials & Interfaces,  17(34), 47795–47805.   https://doi.org/10.1021/acsami.5c08837

Gouverneur, F. (2019). Systematic review of research  on artificial intelligence applications in higher  education – where are the educators? International  Journal of Educational Technology in Higher  Education, 16(1), 39.   https://doi.org/10.1186/s41239-019-0171-0

2091
