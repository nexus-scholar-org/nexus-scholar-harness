---
workspace_id: "SCI-000075"
doi: "10.48550/arxiv.2506.23692"
title: "Agent4S: The Transformation of Research Paradigms from the Perspective of Large Language Models"
year: 2025
extraction_engine: "pymupdf"
---
# 2025 Zheng Agent4S The Transformation of Research Paradigms 

Agent4S: The Transformation of Research Paradigms from the

Perspective of Large Language Models

Boyuan Zheng1,2*†, Zerui Fang3,4†, Zhe Xu1,5†, Rui Wang3,1,2, Yiwen Chen1,2, Cunshi

Wang6,7, Mengwei Qu8,9, Lei Lei10, Zhen Feng11,12, Yan Liu13, Yuyang Li6,14*, Mingzhou Tan15*, Jiaji Wu16*, Jianwei Shuai17,12*, Jia Li4*, and Fangfu Ye1,18,12*

arXiv:2506.23692v1  [cs.AI]  30 Jun 2025

1Beijing National Laboratory for Condensed Matter Physics, Institute of Physics, Chinese Academy of

Sciences, Beijing, China

2Beijing Gongyu Zhiyan Technology Co., Ltd, Beijing, China

3School of Advanced Interdisciplinary Sciences, University of Chinese Academy of Science, Beijing, China

4Smart Sensing Chip and System R&D Center, Institute of Microelectronics of the Chinese Academy of

Sciences, Beijing, China

5Key Laboratory of Material Physics, Ministry of Education, School of Physics and Microelectronics,

Zhengzhou University, Zhengzhou, China

6Key Laboratory of Optical Astronomy, National Astronomical Observatories, Chinese Academy of

Sciences, Beijing, China

7College of Astronomy and Space Sciences, University of Chinese Academy of Sciences, Beijing, China

8State Key Laboratory of Isotope Geochemistry, Guangzhou Institute of Geochemistry, Chinese Academy

of Sciences, Guangzhou, Guangdong China

9College of Earth and Planetary Sciences, University of Chinese Academy of Sciences, Beijing, China

10Alibaba Cloud, Hangzhou, Zhejiang, China

11College of Information and Engineering, Wenzhou Medical University, Wenzhou, Zhejiang, China

12Wenzhou Institute, University of Chinese Academy of Sciences, Wenzhou, Zhejiang, China

13Department of science and development, Chinese academy of sciences, Beijing, China

14College of Astronomy and Space Sciences, University of Chinese Academy of Sciences, Beijing, China

15Emotion Machine (Beijing) Technology Co., Ltd., Beijing, China

16School of Electronic Engineering, Xidian University, Xi’an, Shaanxi, China

17Oujiang Laboratory (Zhejiang Lab for Regenerative Medicine, Vision and Brain Health), Wenzhou,

Zhejiang, China

18School of Physical Sciences, University of Chinese Academy of Sciences, Beijing, China

*Corresponding authors are as follows: Fangfu Ye(fye@iphy.ac.cn), Jia Li(lijia@ime.ac.cn), Yuyang

Li(liyuyang22@mails.ucas.ac.cn), Jianwei Shuai(jianweishuai@xmu.edu.cn), Mingzhou Tan(SwanLab.cn),

Jiaji Wu(wujj@mail.xidian.edu.cn), Boyuan Zheng(zhengboyuan17@mails.ucas.ac.cn)

†Contributed equally (Co-first authorship)

1


## Abstract

While AI for Science (AI4S) serves as an analytical tool in the current research paradigm, it

doesn’t solve its core inefficiency. We propose ”Agent for Science” (Agent4S)—the use of LLM-

driven agents to automate the entire research workflow—as the true Fifth Scientific Paradigm.

This paper introduces a five-level classification for Agent4S, outlining a clear roadmap from

simple task automation to fully autonomous, collaborative ”AI Scientists.” This framework

defines the next revolutionary step in scientific discovery.

1 The Basic Characteristics and Development History of Sci-

entific Research

The essence of scientific research is to establish a set of methods to discover laws from data (phe-

nomena), and then use these laws to guide production and transform the world.

The four scientific paradigm revolutions[1] shown in Table 1 are essentially transformations in


## methods of data acquisition and data processing.

The first scientific paradigm is the empirical paradigm, where the research paradigm of this stage

is characterized by observation and induction. Data acquisition mainly relied on naked-eye obser-

vation and measurements with simple tools, such as the experimental methodology systematically

expounded by Bacon in Novum Organum (1620)[2] and Galileo’s telescopic observations[3]. Data

processing involved manual recording and simple statistics, establishing causal relationships through

repeated observations and emphasizing the reproducibility and intuitiveness of experience.

The second scientific paradigm is the theoretical paradigm. With the development of precision

instruments and mathematical tools, scientific research achieved a leap from qualitative to quantita-

tive analysis. Data acquisition shifted from simple observation to controlled experiments and precise

measurements, such as Newton’s prism experiments on the dispersion of light spectra in 1665–1666[4]

and Cavendish’s torsion balance experiment to measure the gravitational constant in 1797–1798[5].

Mathematical formulas and equation solving were introduced into data processing, enabling the

derivation of universal laws from limited experimental data through mathematical abstraction and

establishing a ”mathematical” scientific language system.

The third scientific paradigm is the computational science paradigm. With the advent of elec-

tronic computers, scientific research broke through the physical limitations of traditional experi- ments. Data acquisition shifted from physical observation to computer-generated data, generating

massive simulated data through mathematical models—examples include nuclear weapons test sim-

ulations, weather forecasting models, and molecular dynamics simulations. Data processing under-

went a revolutionary shift from manual calculations to numerical computations: the introduction

of high-performance computing (HPC) techniques made simulation research on complex systems

feasible.

The fourth scientific paradigm is the data-intensive scientific paradigm[6]. With the development

of sensor networks, the internet, and artificial intelligence technologies, scientific research has entered

an era of ”big data-driven” inquiry. Data acquisition now enables massive, high-dimensional, real-

time collection through sensors, automated devices, and internet platforms—examples include gene

2


> **Table 1: Revolution of the four scientific paradigms**

Paradigm Key Characteristics Data Acquisition Methods

Data Processing Methods Empirical Paradigm Observation- Induction

Naked-Eye Observa- tion/Simple Instru- ments

Oral/Textual Records + Naive Induction Theoretical Paradigm Experimental- Quantitative Theory

Mathematical Ab- straction + Equation Solving Computational Paradigm Numerical Simula- tion

Controlled Experi- ments and Precision Instruments

Numerical + High- Performance Com- puting Data-Driven Paradigm Big Data Massive High- Dimensional Data from Sen- sors/Automated Devices

Computer- Generated Data

Machine Learn- ing/Deep Learning

sequencing, radio telescope arrays, and social network data streams. Data processing has evolved

from statistical learning to machine learning and now deep learning, endowing computers with the

ability to directly extract patterns from high-dimensional data spaces and achieving a fundamental

shift from hypothesis-driven to data-driven research.

Each transformation has brought about corresponding scientific research processes and gradually

improved the systematic methodologies of scientific research. The current scientific research pro-

cess primarily involves: formulation of scientific questions, definition of research content, design of

research plans, experimentation, and data processing with iteration.

With the continuous improvement of productivity, the rate of new data generation and the volume

of knowledge derived from existing data have been growing exponentially. Under the framework of

the fourth scientific research paradigm, a past contradiction was the mismatch between the increasing

data dimensionality and insufficient data analysis methods—the curse of dimensionality[7]. The

development of deep learning has alleviated this contradiction to some extent[8]. However, more

fundamentally, from the perspective of productivity, a deeper contradiction lies in the growing

volume of scientific research information and the inefficiency of existing research paradigms.

2 Understanding AI4S from the Perspective of Scientific Data

Processing

2.1 Definition of AI4S

For the first contradiction, namely the mismatch between increasing data dimensionality and insuf-

ficient data analysis methods, AI algorithms—especially deep neural networks—as computational

methods in the big data era that can handle higher-dimensional data compared to statistical learning

and classical machine learning (or ”high-order function fitting methods”), are capable of processing

3

higher-dimensional data and uncovering more patterns within them. Their application in scientific

research constitutes the classical definition of AI4S[9]. For example, AlphaFold leverages the Evo-

former algorithm to extract patterns from massive protein data on how amino acid interactions affect

their distances, while deep learning potentials (DPMD) use neural networks to learn the relationships

between molecular structures and potential energies.

2.2 Development History and Current Status of AI4S

Since expert systems first emerged in the 1980s and deep learning breakthroughs in image/speech

domains around 2010 were rapidly applied to scientific computing, AI4S has undergone three critical

leaps:

1. In the symbolism stage, relying on expert-defined rules, it faced limitations in modeling com-

plex systems;

2. The statistical machine learning stage focused on low-dimensional feature engineering (e.g.,

support vector machines, random forests)—while enabling automatic modeling, it struggled

with exponentially increasing data dimensions;

3. The deep representation learning stage introduced ”high-order function fitters” like convolu-

tional networks, attention mechanisms, and graph neural networks into research scenarios,

achieving breakthroughs in protein folding (AlphaFold 2/Evoformer), molecular potential en-

ergy surfaces (DPMD), inverse materials design (GraphGPT-Materials), etc.

3 Agent4S

3.1 Definition of Agent4S

Starting from the development of Agent technology and combined with the existing paradigms of

scientific research, we propose five levels of Agent4S, as shown in Table 2.

The earliest form of agents originated from the LLM + Prompt mechanism, supplemented by

Function Calling (FC) to map language outputs to API calls. This has been widely deployed in

industry for customer service Q&A and content generation; in scientific research, it manifests as the

intelligent encapsulation of single scientific tools, such as literature retrieval, database query, image

annotation, etc. (specific cases and references needed, note: the implementation must be a single

agent). We define this as Level 1 (L1) of Agent4S—Automation of a Single Scientific Tool—referring

to the automation of a simple task in research.

With the maturation of Task-/Workflow Orchestration frameworks (Airflow, Dagster, Ray Serve,

etc.), LLM Agents can now maintain state and dependency relationships across multi-step tasks.

Integrated ”instruction-execution-callback” loops have been widely deployed in industrial scenarios

such as robotic process automation (RPA), A/B testing, and advertising. The most typical sci-

entific research practice is the ”end-to-end data pipeline”—for example, integrating four steps of

sequencing quality control, alignment, quantification, and statistics into a single-trigger automated

4

Implementation

ware/Software

Tools and

Context En-

Data Trans-

(Laboratory)

Disciplinary

Digitization

Robustness

Laboratory

Integration

Challenges

Hardware

gineering

Breaking

Research

Enabled

Barriers

mission

MCP-

Hard-

Pattern Es-

Pattern Es-

Clear De-

No Clear

No Clear

Cases with

Applications

Preliminary

Trajectory

velopment

tablished

tablished

Research

Current

Partner for

Tools for

Fixed Pro-

for Cross-

Collaboration

Collaborative

Transforma-

Disciplinary

Automated

Innovative

tion Mode

Intelligent

Research Intelligent

Phase Paradigm

Processes

Network

cesses

tion/Acquisition

opment Interdisciplinary

sis/Processing

Data Analy-

Data Genera-

Mature Scientific

opment Scientific

nology Status Research


> **Table 2: Agent4S Hierarchy**

Early Devel-

to-Agent) Early Devel-

Agent Tech-

(AI Proxies) Prompt Engi-

neering + FC

+ Context

System A2A (Agent-

Agent Tech-

+ Workflow

Engineering

chy Underlying

Reasoning

+ MCP

nology

Level Definition Agent Hierar-

AI Agents

Agentic AI

Multi-Agent

(Intelligent

Agent AI)

of Multiple

of a Single

a Single Pro-

of Complex

(Single Labo-

L3 Intelligence of

L5 Collaboration

Laboratories)

L4 Full-Process

L1 Automation

L2 Automation

Intelligence

Intelligent

Processes

Processes

(Multiple

ratory)

Tool

cess

5


> **Figure 1: Technical framework**

task flow; or chaining structure generation, first-principles calculations, and database storage into

one-click scripts for high-throughput materials computation (specific cases and references needed,

note: implementation must be workflow-driven multi-agent, where workflows can be linear, parallel,

or autonomously planned). We define this as Level 2 (L2) of Agent4S—Automation of Complex Sci-

entific Pipelines—referring to orchestrating multiple L1 tools via workflow methods into reusable,

low-human-intervention research pipelines to automate a complex fixed process in scientific research.

Currently, with the development of Reasoning Frameworks (ReAct, Tree-of-Thought, Graph-of-

Thought) and Long-Context Memory Engineering, LLM Agents have evolved from ”pipeline ex-

ecutors” to master agents capable of chain reasoning, real-time decision-making, and self-reflection.

They achieve intelligent tool invocation through the Model-Context-Protocol (MCP), marking the transition from AI Agents to Agentic AI [10]. This paradigm has validated the feasibility of

”observation-planning-iteration” closed-loop decision-making in industrial scenarios like AIOps, real-

time risk control, and AI coding. Although AI-related technologies are newly developed and have

limited applications in scientific research, it is foreseeable that the next stage will involve an AI Sci-

entist with autonomous planning and long-term memory capabilities—capable of invoking various

L2 tools via MCP to realize a closed-loop of ”planning-tool usage-data analysis” for specific research

6

processes, enabling intelligent iteration. We define this as Level 3 (L3) of Agent4S—Intelligent

Single-Flow Research.

Looking ahead, as Agent capabilities in memory length, multi-step planning, and MCP invoca-

tion continue to advance—alongside the development of embodied intelligence and further integra-

tion/data connectivity across all hardware-software components in laboratory workflows—the L3- level AI Scientist will be able to participate in the full ”hypothesis-experiment-analysis” closed loop

of research projects and enable intelligent iteration. We define this as Level 4 (L4) of Agent4S—Lab-

Scale Closed-Loop Autonomy.

Ultimately, with the advancement of full-process intelligence in each laboratory and relying on

the A2A protocol, multiple super-agents will be able to communicate with each other, enabling the

formation of an intelligent network for cross-disciplinary collaboration driven by multi-agent systems

in scientific research. This constitutes the Level 5 (L5) stage of Agent4S and represents the final

form of the fifth scientific paradigm driven by artificial intelligence.

From the perspective of general research processes, AI4S represents a more advanced method

within the data analysis phase; L1 of Agent4S refers to the automation of a simple tool used in

a specific research sub-task (e.g., literature retrieval or data annotation), involving single-agent

operations without cross-component integration. L2 involves the automation of an entire research

sub-process (e.g., a data pipeline combining sequencing QC and statistical analysis), differing from

L1 in featuring a multi-agent-driven complete data closed loop orchestrated via workflow frameworks.

L3 denotes the intelligence of a specific research workflow, encompassing autonomous planning, tool

invocation, data processing, and result collation. Its key distinction from L2 lies in the presence

of a super-agent with context engineering capabilities that autonomously plans, orchestrates, and

iterates the workflow. L4 represents full-process intelligence in scientific research, covering the entire

lifecycle from scientific question formulation, research design, hypothesis generation, experimental

simulation, to data interpretation. It differs from L3 in enabling end-to-end participation across the

entire research process rather than individual workflows.

In terms of future human-computer interaction models, as illustrated in Figure 1: Levels L1

and L2 involve the automation of fixed processes, primarily applied to the historically machine-

driven data generation/acquisition stages. Fundamentally, they remain tools within the research

workflow. Levels L3 and L4 represent the intelligence of innovative processes with stochastic and

emergent characteristics, focusing on data analysis and interpretation. These constitute super-

agents analogous to scientists—i.e., AI Scientists—capable of autonomous reasoning. A plausible

future interaction model is scientists collaborating with AI Scientists as partners, jointly invoking various tools (L3/L4), which themselves may integrate numerous agents (L1/L2). Level L5 refers

to interactions among multiple AI Scientists, forming an intelligent network for cross-disciplinary

research.

In terms of research organizational forms, as shown in Figure 2: L1 and L2 represent the au-

tomation of tools used by scientists in specific research sub-tasks, where agents remain as passive

instruments within the workflow. L3 marks a shift: agents evolve from ”tools” to collaborative

assistants with defined roles, capable of participating in targeted workflow stages under human guid-

ance. L4 elevates agents to the role of central coordinators in full experimental cycles—analogous

7


> **Figure 2: Five levels of Agent4S**

to an AI project leader/laboratory director that oversees the entire research lifecycle, from proposal

development to completion, with full situational awareness and autonomous decision-making capa-

bilities. L5 enables cross-disciplinary collaboration across multiple laboratories, where information

flows through a network of super-agents, facilitating seamless interaction and knowledge exchange between distributed intelligent entities.

4 Significance

More than just a nominal definition: In AI4S, ”AI” denotes a data analysis methodology—specifically,

using AI algorithms to address high-dimensional data challenges in scientific research. In Agent4S,

”Agent” represents a new productivity tool—Agent4S signifies agent-driven automation and intelli-

gence in scientific research, emerging as a transformative productivity paradigm for data acquisition

and processing. The connection between AI4S and Agent4S in the entire scientific research process:

Classical AI4S serves as the fundamental building blocks of algorithmic agents in the data process-

ing stage within the Agent4S paradigm. Both fall under the category of applying AI to scientific

research. This analysis, from an AI technical perspective, provides concrete implementation and

development frameworks for intelligent scientific research—moving beyond mere macro-level visions

of the past. For AI practitioners, it clarifies how to advance AI technologies and integrate them with

scientific workflows; for domain scientists, it identifies clear entry points for AI integration in their

8

fields. Additionally, by outlining the scientific challenges at each developmental level of the Agent4S

hierarchy, it guides researchers on aligning their work with AI advancements to systematically elevate

the intelligence levels of research processes.

This work resolves the confusion between algorithms and intelligence: fundamentally, the tech-

nical essence of AlphaFold differs from that of cutting-edge intelligent laboratories. In terms of scope, the AI4S algorithms behind AlphaFold—at their core computational methods—represent

a single component within the scientific research workflow and constitute a subset of the future

Agent4S framework. Regarding the classification of the Fifth Scientific Paradigm, numerous prior

taxonomies existed but primarily focused on the degree of research automation, serving more as

automation ratings rather than providing actionable technical roadmaps or trend analyses. Our

classification innovatively integrates the technological evolution of Agents with the levels of research

automation/intelligence, clearly delineating future development trajectories and critical challenges.

This approach fundamentally advances the transformation toward the Fifth Scientific Paradigm by

bridging theoretical visions with practical implementation frameworks.

In fact, the concept of the Fifth Scientific Paradigm was proposed early on [11], which outlined

its characteristics:

1. Full integration of artificial intelligence into scientific, technological, and engineering research,

enabling knowledge automation and intelligence across the entire research process;

2. Human-machine symbiosis, where emergent machine intelligence becomes an integral part of

research, giving rise to tacit knowledge and machine-generated hypotheses;

3. Focus on complex systems as primary research objects, effectively addressing combinatorial

explosion problems with extremely high computational complexity;

4. Orientation toward non-deterministic problems, where probabilistic and statistical reasoning

play an expanded role in research;

5. Cross-disciplinary collaboration as the mainstream research mode, achieving integration of

the first four paradigms—especially the convergence of first-principles model-driven and data-

driven approaches;

6. Heavy reliance on large-scale platforms characterized by large models, with close integration

between scientific research and engineering implementation.

These characteristics are incisive, yet the paradigm lacked a strict definition at the time—due

to the underdevelopment of agent technologies, many past AI algorithms for data processing were

essentially refinements within the data-driven Fourth Scientific Paradigm but were erroneously cat-

egorized as part of the Fifth. From the Agent4S perspective, we can now naturally distinguish

between ”improvements within the data-driven paradigm” and ”scientific paradigm shifts brought

by new productivity tools.”

In summary, both AI4S and Agent4S represent applications of AI in scientific research—where

AI4S positions ”AI” as a data analysis methodology, using AI algorithms to address high-dimensional

9

data challenges and resolve the historical contradiction between data dimensionality and computa-

tional methods within the Fourth Scientific Paradigm. In contrast, Agent4S defines ”Agent” as a new

productivity tool, enabling agent-driven automation and intelligence in scientific research to tackle

the contradiction between information richness and the productivity limitations of past paradigms.

It refers to using Agent technology to drive automation and intelligent scientific research, ad- dressing the contradiction between information richness and productivity under past paradigms.

More than a nominal definition: In AI4S, ”AI” denotes a data analysis methodology—specifically,

using AI algorithms to address high-dimensional data challenges in scientific research. In Agent4S,

”Agent” represents a new productivity tool—Agent4S signifies agent-driven automation and intelli-

gence in research, emerging as a transformative paradigm for data acquisition and processing.


## References

1. Hey T, Tansley S, Tolle K, and Gray J. The Fourth Paradigm: Data-Intensive Scientific Dis-

covery. Microsoft Research, 2009. url: https://www.microsoft.com/en- us/research/

publication/fourth-paradigm-data-intensive-scientific-discovery/.

2. Bacon F. Instauratio Magna (Novum Organum). Publisher Unknown, 1620.

3. Taton R, Wilson C, and Hoskin M. Planetary Astronomy from the Renaissance to the Rise

of Astrophysics, Part A, Tycho Brahe to Newton. General History of Astronomy. Cambridge

University Press, 2003. url: https://books.google.com/books?id=hMgXh8jMSGgC.

4. Newton I. A letter of Mr. Isaac Newton, Professor of the Mathematicks in the University

of Cambridge; containing his new theory about light and colors: sent by the author to the

publisher from Cambridge, Febr. 6. 1671/72; in order to be communicated to the R. Society.

Philosophical Transactions of the Royal Society of London 1672;6:3075–87.

5. Cavendish H. XXI. Experiments to determine the density of the earth. Philosophical Transac-

tions of the Royal Society of London 1798;88:469–526.

6. Gray J and Szalay A. eScience-A transformed scientific method. Presentation to the Computer

Science and Technology Board of the National Research Council 2007.

7. Hammer P. Adaptive control processes: a guided tour (R. Bellman). 1962.

8. Bach F. Breaking the curse of dimensionality with convex neural networks. Journal of Machine

Learning Research 2017;18:1–53.

9. Wang H, Fu T, Du Y, et al. Scientific discovery in the age of artificial intelligence. Nature

2023;620:47–60.

10. Sapkota R, Roumeliotis KI, and Karkee M. Ai agents vs. agentic ai: A conceptual taxonomy,

applications and challenge. arXiv preprint arXiv:2505.10468 2025.

11. LI G. AI4R: The fifth scientific research paradigm. Bulletin of Chinese Academy of Sciences

(Chinese Version) 2024;39:1–9.

10
