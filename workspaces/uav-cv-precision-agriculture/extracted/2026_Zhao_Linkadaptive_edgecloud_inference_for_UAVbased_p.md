---
workspace_id: SCI-000323
doi: 10.1038/s41598-026-65658-3
title: Link-adaptive edge-cloud inference for UAV-based plastic mulch residue assessment
authors:
- family_name: Zhao
  given_name: Xinmiao
  orcid: null
- family_name: Zhang
  given_name: Jingjing
  orcid: null
- family_name: Dolkun
  given_name: Dilxat
  orcid: null
- family_name: Xu
  given_name: Jin
  orcid: null
- family_name: An
  given_name: Si
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T01:48:56.479716+00:00'
---

# Link-adaptive edge-cloud inference for UAV-based plastic mulch residue assessment

Scientific Reports

https://doi.org/10.1038/s41598-026-65658-3

Article in Press

Link-adaptive edge-cloud inference for UAV- based plastic mulch residue assessment

Xinmiao Zhao, Jingjing Zhang, Dilxat Dolkun, Jin Xu & Si An

Received: 8 June 2026

Accepted: 3 August 2026

We are providing an unedited version of this manuscript to give early access to its  findings. Before final publication, the manuscript will undergo further editing. Please  note there may be errors present which affect the content, and all legal disclaimers  apply.

Cite this article as: Zhao X., Zhang J.,  Dolkun D. et al. Link-adaptive edge- cloud inference for UAV-based plastic  mulch residue assessment. Sci Rep  (2026). https://doi.org/10.1038/ s41598-026-65658-3

ARTICLE IN PRESS

If this paper is publishing under a Transparent Peer Review model then Peer  Review reports will publish with the final article.

© The Author(s) 2026. Open Access This article is licensed under a Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International  License, which permits any non-commercial use, sharing, distribution and reproduction in any medium or format, as long as you give appropriate credit  to the original author(s) and the source, provide a link to the Creative Commons licence, and indicate if you modified the licensed material. You do  not have permission under this licence to share adapted material derived from this article or parts of it. The images or other third party material in this  article are included in the article’s Creative Commons licence, unless indicated otherwise in a credit line to the material. If material is not included in the  article’s Creative Commons licence and your intended use is not permitted by statutory regulation or exceeds the permitted use, you will need to obtain  permission directly from the copyright holder. To view a copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/4.0/.

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

Link-adaptive edge-cloud inference for UAV-based plastic mulch residue  assessment

Xinmiao Zhao123* , Jingjing Zhang123, Dilxat Dolqun123 , Jin Xu123 , Si An123 1.College of Computer and Information Engineering, Xinjiang Agricultural University, Urumqi, Xinjiang,  830052, China 2.Engineering Research Center of Smart Agriculture, Ministry of Education, Urumqi, Xinjiang, 830052, China 3.Xinjiang Engineering Research Center for Agricultural Informatization, Urumqi, Xinjiang, 830052, China Corresponding author: Xinmiao Zhao

Abstract. Plastic mulch residue assessment from UAV imagery is jointly constrained by  segmentation accuracy, end-to-end latency and uplink bandwidth, since onboard inference loses  boundary fidelity on fragmented film while cloud inference is throttled by the link, and these  constraints have been treated separately in prior work. This study develops a link-adaptive edge- cloud inference framework combining a three-factor decision module that fuses EWMA-smoothed  bandwidth, entropy-derived confidence and motion-compensated residual into a single score  assigning each frame to local termination, region-of-interest offloading or full-frame offloading; a  plastic-mulch-aware student-teacher architecture transferring representations across a two- thousand-fold scale gap from Sentinel-2 imagery to sub-centimetre UAV imagery; and NSGA-II  optimisation recovering the latency-accuracy Pareto front rather than a scalar compromise.  Evaluated on a self-collected UAV residue dataset under emulated 4G-LTE, 5G-NR and Wi-Fi 6  links, the balanced operating point attains an IoU of 0.826, recovering 97.1% of the cloud-only  SegFormer-B3 accuracy at a median end-to-end latency of 72 ms, and responds to abrupt link  transitions 3.4 times faster than fixed-threshold offloading. Accuracy degrades on fragments below  200 pixels, corresponding to about 50 cm2 at the acquisition scale, which bounds the operational  value of the framework to residue within the range that mechanised collection engages.

ARTICLE IN PRESS

Keywords. Plastic mulch residue; Edge-cloud collaborative inference; UAV remote sensing;  Semantic segmentation; Knowledge distillation; Pareto optimization


## 1. Introduction

Plastic film mulching in northern China for more than three decades on crops such as cotton, corn,  and vegetables has highlighted the formation of residues as one of the main drivers of microplastics  in agriculture. In addition, the continued existence of small-sized plastic film fragments causes  serious damage to the soil’s pore structure and root growth as well as lowering the yield of cotton  plants as a result of long-term use of the film mulching technique 1. With respect to the continuous  problem and the inefficiency of existing recovery techniques, high-resolution, scalable monitoring  of residues is needed 2.

High-altitude remote sensing has emerged as the most promising approach after the manual  surveying. In fact, sub-centimetre images that resolve individual pieces of residue can be acquired  by UAVs through low-altitude aerial remote sensing 3,4. Furthermore, with the use of Sentinel-2  satellites, it becomes possible to map regions using the semantic segmentation technique to  identify farmlands containing plastic-mulched lands 5,6. Specific neural network models using  spatial-channel attention 7 and multi-scale fusion from the frequency domain 8 have improved  detection precision significantly.

When applied in the field, however, these methods encounter a triplet of constraints that the  reviewed literature does not address together. On-board inference, running on typical edge devices

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

for the purpose of inference, is subject to memory constraints and shows a loss in boundary fidelity  on small image fragments. Cloud inference alone is constrained by bandwidth availability through  either cellular or meshed connections, and fixed thresholds for offloading cause a bimodal  distribution of latency and destabilize flight control operations. These constraints have been  addressed separately rather than jointly.

Task-offloading frameworks for multi-UAV cooperative edge computing have been developed  across priority-aware allocation, 5G-advanced resource scheduling, dynamic platform-side  dispatching, URLLC-grade latency minimisation and deep-learning-enabled target tracking 9-13.  These formulations treat the computational task as opaque, optimising scalar indicators such as  completion time, energy consumption or task drop rate while leaving the internal state of the  perception model unobserved. Such abstraction is appropriate for task-agnostic workloads but  discards the very signals that distinguish frames warranting cloud refinement from those resolvable  on board, namely prediction confidence and inter-frame motion, neither of which appears as a  decision variable in the cited works.

Adaptive configuration selection and bandwidth allocation under fluctuating wireless conditions  has been shown to materially improve edge-based video analytics through elastic configuration  switching 14, while NSGA-II-based and learning-based scheduling has been advanced across  vehicular fog computing, UAV-swarm remote sensing, internet-of-vehicles offloading, privacy- aware DNN partition, multi-agent reinforcement learning and delay-aware cooperative offloading  15-20. Decision variables in these works centre on partition points, compression levels and  computational placement, with the reported Pareto fronts densely sampling latency-energy or  latency-throughput axes but only sparsely populating the latency-segmentation-accuracy axis that  ultimately governs deployable performance in fragmented-target perception.

ARTICLE IN PRESS

Transformer-based segmentation backbones such as SegFormer 21 have established new accuracy  ceilings for dense prediction, while lightweight contemporaries including STDC and small-object- tuned aerial detectors 22,23 push inference latency below the real-time threshold at the cost of  boundary fidelity on sub-resolution structures. Boundary-aware UNetFormer extensions and  framework-level improvements for aerial imagery 24,25 have progressively closed the accuracy gap  between lightweight and heavy architectures, yet the evaluation protocols underlying these  advances assume a fixed compute budget and treat segmentation as a self-contained benchmark,  leaving the joint design of architecture, compression and offloading underexplored for fragmented- target tasks where residue area below 200 pixels dominates the error budget.

Across these three lines of work the omission is consistent. Offloading is optimised without  reference to the internal state of the perception model, segmentation is optimised under a fixed  compute budget, and the multi-objective formulations that would reconcile the two populate  latency-energy space rather than latency-accuracy space. No existing formulation makes the  accuracy attainable at a given latency an explicit decision outcome for a fragmented-target task,  and this coupling is what the present study addresses.

This work introduces an edge-cloud collaborative inference framework that addresses the three- way constraint through three coupled innovations: a three-factor offloading decision module that  combines EWMA-smoothed bandwidth, entropy-derived confidence and motion-compensated  residual into a single composite score, a plastic-mulch-aware student-teacher segmentation  architecture with cross-scale satellite-to-UAV transfer pretraining, and an NSGA-II-based bi-

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

objective Pareto optimisation that recovers the full latency-accuracy trade-off curve rather than a  single scalar compromise.

The contribution of this study lies in the coupling rather than in the individual components. A  frame-level decision rule is formulated in which link state, perceptual difficulty and temporal  redundancy enter a single normalised score, allowing a confidently segmented frame over  previously inspected ground to be retained on board even when bandwidth is abundant, a case that  bandwidth-driven schemes offload without benefit. A segmentation pair is designed around the  appearance of weathered residual film, with a Sobel-guided boundary branch in the student and  staged pretraining that admits satellite imagery as a representation prior rather than as an evaluation  domain. The configuration space spanning keyframe density, crop ratio, compression and the two  offloading thresholds is treated as an explicit bi-objective problem, so that the deployment choice  is made on a recovered front rather than on a preselected weighting. The objectives are to quantify  the accuracy retained relative to a cloud-only transformer teacher, to characterise the latency  distribution under realistic link dynamics, and to establish the fragment scale at which the  framework ceases to inform remediation planning.


## 2. Experiments and Results

ARTICLE IN PRESS


### 2.1 Experimental setup

The proposed framework was deployed on an NVIDIA Jetson Xavier NX onboard processor  coupled with a cloud server equipped with an NVIDIA A100-40GB GPU, integrated into a DJI  Matrice 300 RTK quadrotor carrying a Zenmuse P1 4/3-inch CMOS sensor that captured 4K  imagery at 30 Hz over plastic-mulched cotton fields in the Manas River basin of Xinjiang during  the 2024 pre-sowing residue assessment campaign, conducted before spring tillage when residual  film fragments remain exposed on bare soil. The wireless link was emulated through a Spirent  Landslide channel emulator that injected reproducible bandwidth profiles spanning 8 to 540 Mbps  and round-trip latencies between 18 and 240 ms, covering the operating envelope of 4G-LTE, 5G- NR and Wi-Fi 6. The satellite branch of the student–teacher framework was pretrained on the  China-PMF-10  dataset  26  (Niu  et  al.,  2026;  Figshare,  https://doi.org/10.6084/m9.figshare.28528919), a national-scale 10 m resolution plastic-mulched  farmland product derived from Sentinel-2 imagery, and its cross-region generalization was  independently verified on the PMF-LP dataset (Zenodo record 13369426), covering the Chinese  Loess Plateau across 2019–2021. The UAV-scale model was trained and evaluated on a self- collected residue dataset of 4,287 manually annotated tiles at 512 × 512 px and approximately 0.5  cm/px ground sampling distance, divided into 80/10/10 partitions for training, validation and  testing. Quantitative comparisons were drawn against four reference baselines comprising fixed- threshold offloading at τ = 0.5, EWMA-only adaptation, confidence-only adaptation and cloud- only inference with SegFormer-B3, together with three published dynamic offloading frameworks  reimplemented on the present hardware and dataset, namely the privacy-aware DNN partitioning  of Cheng et al.18, the multi-agent reinforcement learning policy of Zhao et al.19 and the adaptive  configuration selection of Zhang et al.14, each retrained or retuned on the UAV residue training  partition with hyperparameters taken from the original reports where applicable. All figures are  reported as mean ± 95% confidence interval over five independent trials.

Segmentation accuracy is reported as intersection-over-union of the residue class against manual  annotation on the held-out test partition, with F1 and Boundary IoU evaluated on a five-pixel  dilation kernel, computed on the mask the framework finally emits, that is, after cloud refinement

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

and temporal fusion where these occur, so that the figure reflects the output available to a  downstream user rather than the output of any single branch. End-to-end latency is measured from  completion of frame acquisition on the onboard processor to availability of the fused mask in  onboard memory, and comprises coarse segmentation, decision evaluation, JPEG encoding, uplink  transmission, cloud inference, downlink return and fusion. Clocks on the onboard processor and  the cloud server were synchronised by the precision time protocol to within 1 ms, and transmission  time was recovered from timestamps rather than inferred from bandwidth. All compared methods  were executed on the same hardware, over the same emulated profiles, on the same test partition  and under the same instrumentation.

Onboard inference was executed under JetPack 5.1.2 with TensorRT 8.5.2 at half precision, and  training was performed in PyTorch 1.13 with CUDA 11.4 using AdamW at an initial learning rate  of 5 × 10-5 decayed to 5 × 10-6 over one hundred epochs at batch size 8, the five trials differing  only in random seed. Flights were flown at 5 to 8 m s-1 with 80% forward and 60% side overlap.  Annotation followed a common protocol applied by three trained interpreters, with 10% of tiles  independently double-annotated yielding an inter-annotator agreement of κ = 0.94. Ambient air  temperature across the six sessions ranged from 6 to 21 °C, so the thermal behaviour characterises  early-spring operation in the Manas River basin rather than a general property of the platform, and  the cooling requirement should be reassessed for campaigns conducted later in the season, when  surface temperatures over bare soil in this region substantially exceed the present range.

ARTICLE IN PRESS


> **Table 1. Experimental configuration.**

Component Specification

Onboard processor NVIDIA Jetson Xavier NX (8-core Carmel Arm v8.2, 384-core Volta  GPU, 8 GB LPDDR4x)

Cloud server NVIDIA A100-40GB, AMD EPYC 7763 64-core, 256 GB RAM

UAV platform DJI Matrice 300 RTK + Zenmuse P1, 4K @ 30 Hz

Flight altitude 25–40 m above ground level

Link emulation Spirent Landslide 5G-NR / 4G-LTE / Wi-Fi 6

Bandwidth range 8–540 Mbps

Round-trip time range 18–240 ms

Satellite pretraining set China-PMF-10, Sentinel-2 (10 m/px), national 2020

Satellite  cross-region  test

PMF-LP, Sentinel-2 (10 m/px), Loess Plateau 2019–2021

UAV training set Self-collected, 4,287 tiles, 512 × 512 px, ~0.5 cm/px

Train / validation / test  split

80 / 10 / 10

Reported uncertainty mean ± 95% CI, 5 independent trials

Flight sessions 6, each spanning a full battery endurance cycle, pre-sowing window  2024

Ground speed 5–8 m s-1

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

Image overlap 80% forward, 60% side

Ambient  air  temperature

6–21 °C across the six sessions

Clock synchronisation Precision time protocol, onboard-to-cloud offset < 1 ms

Onboard runtime JetPack 5.1.2, TensorRT 8.5.2, FP16

Training framework PyTorch 1.13, CUDA 11.4

Optimiser AdamW, lr 5 × 10-5 → 5 × 10-6, 100 epochs, batch size 8

Annotation 3 trained interpreters, 10% of tiles double-annotated, inter-annotator  κ = 0.94

Trials 5 independent runs differing only in random seed


### 2.2 Decision module validation

The three-factor offloading module was evaluated across 180 frames sampled uniformly along  three representative flight segments, each characterised by its normalised bandwidth, confidence  and motion-compensated residual factors under the Pareto-balanced operating point with

ARTICLE IN PRESS

( , , ) (0.45,0.35,0.20) B C R w w w =  and bi-threshold pair  1 2 ( , ) (0.36,0.62) t t =  obtained from the  Pareto optimisation of Section 4.4 and reported in Section 2.3.


> **Figure 4. Empirical validation of the three-factor offloading decision module. a, Three-**

> dimensional decision space spanned by the normalised factors B%, C and R , with iso-surfaces

1 0.36 D t = =  and  2 0.62 D t = =  overlaid on 180 measured frames coloured by decision  category. b, Offloading response across a normalised sequence of link regimes comprising a 4G  phase, a handover to 5G, a bandwidth-drop phase and a recovery phase, with uplink bandwidth on  the left axis and cloud-offloading ratio on the right axis; settled ratios are annotated per phase. c,  Distribution of event-response delay across seven decision policies for the three engineered event

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

types. Markers denote Bonferroni-corrected paired t-tests against the proposed module: *** padj <  0.001, ** padj < 0.01, * padj < 0.05.


> **Figure 4a shows the empirical scatter conforming to the three decision regions, with the 5.6%**

> boundary mislabels arising from EWMA-induced phase lag near threshold crossings. Figure 4b 
reveals smooth offloading-ratio adjustment between regimes, settling at 0.78 in 4G, 0.32 in 5G, 
0.75 during the bandwidth drop and 0.51 during recovery, with each transition completing within 
roughly 1.0 s. Figure 4c yields a median response delay of 0.74
0.22
±
 s against the fixed-
threshold baseline at 2.51 0.84
±
 s, a 3.4-fold improvement, significant against all baselines 
under paired t-tests over the 180 sampled frames with Bonferroni correction across the six 
comparisons (padj < 0.001 in each case).


### 2.3 Pareto optimisation and operating-point selection

The bi-objective NSGA-II procedure was executed with a population of 100 individuals over 200  generations using simulated binary crossover at  20 c h =  and polynomial mutation at probability  1/ 0.2 m p d = = , initialising the search through Latin hypercube sampling within the five- dimensional decision space  dense roi jpeg 1 2 ( , , , , ) k r q t t = x . Convergence was monitored through the

ARTICLE IN PRESS

normalised hypervolume indicator computed against the reference point (1.0,1.0) in the (latency,  1 IoU - ) plane, with knee selection on the post-convergence front performed through the  maximum discrete-curvature criterion. The fronts recovered under the three link profiles are  compared in Figure 5b. Knee configurations agree closely in keyframe density and crop ratio and  diverge principally in compression factor and upper threshold, the 4G profile selecting q = 64 and  τ₂ = 0.71 against q = 72 and τ₂ = 0.62 under 5G, and q = 78 and τ₂ = 0.58 under Wi-Fi 6. The  balanced point reported throughout is the knee of the 5G-NR front, and adopting it under the 4G  and Wi-Fi 6 profiles costs 1.1 and 0.4 percentage points of IoU respectively. The operating point  is therefore profile-specific, and channel variation encountered during flight is absorbed by the  online decision module rather than by the offline front.

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

ARTICLE IN PRESS


> **Figure 5. NSGA-II Pareto optimisation of the latency-accuracy trade-off. a, Normalised**

> hypervolume convergence across 200 generations for each link-emulation profile, averaged over 
five seeds, shaded bands denoting 95% confidence intervals. b, Non-dominated fronts in the end-
to-end latency versus IoU plane for the three profiles, with profile-specific knees marked by 
diamonds and the three operating points selected on the reference 5G-NR front marked by stars. 
c, Radar chart contrasting the five decision components across the three operating points of the 
5G-NR front after axis-wise normalisation. d, Pareto front coverage achieved by NSGA-II on the 
5G-NR profile versus ten independent runs of weighted-sum scalarisation.


> **Figure 5a shows the normalised hypervolume under the 5G-NR profile rising from 0.412 ± 0.018**

> to 0.847 ± 0.011 over 200 generations, with the 4G-LTE and Wi-Fi 6 profiles converging to 0.821 
± 0.013 and 0.859 ± 0.010 respectively; all three saturate before the hundred-and-fiftieth 
generation. Figure 5b yields 78 non-dominated solutions, with the three selected points at latency-
priority (38
3
± ms, IoU 0.794), balanced (72
5
±
 ms, IoU 0.826) and accuracy-priority (198 11
±
 
ms, IoU 0.848). Figure 5c reveals systematic workload reallocation across operating points, while 
Figure 5d shows weighted-sum scalarisation recovering only a narrow central cluster and failing 
to reach either extreme of the front.


> **Table 2. Selected Pareto operating points and their performance under each link-emulation profile.**

Link profile Operating point dense k roi r jpeg q 1t 2 t L (ms) IoU 5G-NR Latency-priority 24 0.09 56 0.48 0.74 38 ± 3 0.794 ± 0.017 5G-NR Balanced (default) 14 0.22 72 0.36 0.62 72 ± 5 0.826 ± 0.013 5G-NR Accuracy-priority 6 0.41 88 0.27 0.51 198 ± 11 0.848 ± 0.011 4G-LTE Balanced (knee) 13 0.20 64 0.38 0.71 96 ± 7 0.815 ± 0.014

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

Wi-Fi 6 Balanced (knee) 15 0.23 78 0.35 0.58 61 ± 4 0.830 ± 0.012

The balanced operating point is adopted as the default in all subsequent evaluations, as the  maximum-curvature criterion places it at the geometric knee and its 2.2 percentage-point IoU  sacrifice relative to the accuracy-priority extreme is compensated by a 2.75´ latency reduction.


### 2.4 Segmentation accuracy and cross-domain transfer

Segmentation performance was evaluated on the held-out UAV residue test partition under the  balanced operating point against four reference models comprising the local-only STDC2-Tiny  student and the cloud-only SegFormer-B0, SegFormer-B1 and SegFormer-B3 teachers, with mean  intersection-over-union, F1 score and Boundary IoU evaluated on a 5-pixel dilation kernel.

ARTICLE IN PRESS


> **Figure 6. Segmentation accuracy on the UAV residue test set. a, Qualitative comparison across**

> three representative tiles showing the original image, manual annotation, STDC2-Tiny local-only 
prediction, SegFormer-B3 cloud-only prediction, the proposed framework, and per-pixel error 
map. b, Confusion matrix aggregated over 429 test tiles for the proposed framework, with 
agreement on sub-200-pixel fragments reported alongside the aggregate statistics. c, Mean IoU 
achieved under three pretraining protocols at fixed architecture; brackets report Bonferroni-
corrected paired t-tests. d, Per-class Boundary IoU distribution across the five compared models, 
the dashed line marking the SegFormer-B3 median, with markers denoting Bonferroni-corrected 
comparisons against the proposed framework: *** padj < 0.001, ** padj < 0.01, n.s. not significant.


> **Figure 6a shows the proposed framework recovering fine-grained residue fragments missed by the**

> local student and improving boundary delineation over the cloud-only teacher. Figure 6b yields 
per-pixel accuracy of 0.918 and Cohen's 
0.821
k =
, dropping to 0.687 for fragments below 200 
pixels. Figure 6c quantifies a 1.4 ± 0.5 percentage-point IoU gain of the three-stage ImageNet →

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

China-PMF-10 → UAV pipeline over training the same architecture on UAV imagery alone, and  Figure 6d places the proposed framework at a median Boundary IoU of 0.712, within 0.018 of the  SegFormer-B3 ceiling. Independent evaluation of the satellite branch on PMF-LP returned a  producer's accuracy of 64.9 2.1% ±  against 78.5% on the source domain, a 17.3% relative drop  within the 15–25% band typical of cross-region Sentinel-2 plastic-film transfer.

The pretraining strategies compared in Figure 6c are evaluated at fixed architecture, so that the  bars isolate the transfer protocol, whereas the rows of Table 4 accumulate architectural and training  components and are pretrained under the three-stage protocol only from the row at which that  protocol is introduced.

Differences between the proposed framework and each reference model were assessed by paired  t-tests across trials with Bonferroni correction over the eight comparisons reported in Tables 3 and  4, with effect sizes expressed as Cohen's d. The margin over the local-only student is significant  (d = 6.3, padj = 0.0012), as is the margin over SegFormer-B0 (d = 3.1, padj = 0.018), whereas the  margin over SegFormer-B1 does not reach significance at this sample size (d = 0.7, padj = 1.00).  The deficit of 0.025 IoU against SegFormer-B3 is itself significant (d = 4.2, padj = 0.0059), so the  recovery of 97.1% of the reference accuracy is to be read as a quantified shortfall obtained at a  favourable latency ratio rather than as statistical equivalence. Within the ablation, the gains from  attention-guided distillation and from Sobel boundary attention are significant (d = 4.1 and 2.6,  padj = 0.0031 and 0.021), while the increment attributable to the satellite stage remains below the  corrected threshold (d = 1.2, padj = 0.48). Wilcoxon signed-rank tests were computed in parallel  and preserve the ordering of these outcomes, though at five trials the smallest attainable two-sided  p value of 0.0625 lies above the corrected threshold, so the parametric tests are reported as primary  and the rank-based results are given in Supplementary Table S1.

ARTICLE IN PRESS


> **Table 3. Segmentation performance on the UAV residue test set (mean ± 95% CI, 5 trials).**

Model Params  (M)

Latency  (ms) IoU F1 Boundary  IoU d padj

STDC2-Tiny  (local) 7.2 31 ± 2 0.776  ±  0.014 0.831  ±  0.012 0.638 ± 0.018 6.3 0.0012

SegFormer-B0  (cloud) 3.8 142 ± 8 0.804  ±  0.011 0.852  ±  0.010 0.671 ± 0.015 3.1 0.018

SegFormer-B1  (cloud) 14.0 178 ± 9 0.821  ±  0.010 0.864  ±  0.009 0.689 ± 0.014 0.7 1.00

SegFormer-B3  (cloud) 47.3 245 ± 12 0.851  ±  0.008 0.882  ±  0.008 0.730 ± 0.011 4.2 0.0059

Proposed  (balanced) 7.2 + 47.3 72 ± 5 0.826  ±  0.013 0.868  ±  0.011 0.712 ± 0.014 — —

Effect size d and corrected significance padj refer to the paired t-test of IoU between the proposed  framework and the model in that row, Bonferroni-corrected over the eight comparisons of Tables  3 and 4. Rank-based counterparts are given in Supplementary Table S1.


> **Table 4. Ablation of architectural and training components (mean over 5 trials, percentage-point**

> gap to full pipeline).

d (vs  preceding  row)

Configuration IoU F1 Boundary  IoU

Δ vs  full

padj (vs

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

preceding  row)

Student backbone only 0.776 0.831 0.638 −5.0  pp — —

+  Attention-guided  distillation 0.799 0.846 0.668 −2.7  pp 4.1 0.0031

+ Sobel boundary attention 0.812 0.857 0.694 −1.4  pp 2.6 0.021

+ Two-stage ImageNet →  UAV pretraining 0.819 0.862 0.703 −0.7  pp 1.6 0.14

Full three-stage pipeline 0.826 0.868 0.712 0.0  pp 1.2 0.48

The proposed framework attains 97.1% of the SegFormer-B3 IoU and 97.5% of its Boundary IoU  at 29.4% of its latency, with the 5.0 percentage-point ablation gap distributed across attention- guided distillation (2.3 pp), Sobel boundary attention (1.3 pp) and the two pretraining stages (1.4  pp combined).

ARTICLE IN PRESS


### 2.5 System-level performance

System-level behaviour was characterised under the balanced operating point and aggregated over  six flight sessions conducted under field conditions during the pre-sowing window of 2024, when  residual film fragments are most accessible to UAV imaging on bare cotton soils.


> **Figure 7. System-level performance. a, Empirical cumulative distribution function of end-to-end**

> latency for the proposed framework against eight baselines, evaluated over 12,000 frames. b, 
Sustained throughput as a function of emulated uplink bandwidth between 10 and 500 Mbps. c, 
Sustained per-frame inference rate under passive and active cooling, with session progress 
expressed as a fraction of total duration.


> **Figure 7a yields a median end-to-end latency of 72 ms for the proposed framework with 95th and**

> 99th percentiles of 138 ms and 186 ms, against 245 ms median and 412 ms 99th percentile for 
cloud-only SegFormer-B3. Figure 7b shows sustained throughput above 26 fps across the full 
bandwidth range, with sensitivity to the uplink quantified by the dimensionless ratio r of fractional 
bandwidth change to the fractional change in sustained throughput it induces, regressed over the 5 
to 100 Mbps band; the value of 5.7 ± 0.4 indicates that throughput responds sub-linearly to 
bandwidth in the regime where cellular agricultural links typically operate. Figure 7c records

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

thermal throttling degrading sustained inference by 11.8% under passive cooling and by 3.4% with  active cooling over the full course of a session.


> **Table 5. End-to-end latency statistics across compared methods (mean ± 95% CI over 12,000**

> frames).

Method Median (ms) p95 (ms) p99 (ms) Throughput (fps) STDC2-Tiny (local) 31 ± 2 38 ± 2 45 ± 3 31.4 ± 0.6 Fixed-threshold offloading 156 ± 8 271 ± 14 318 ± 17 11.2 ± 0.5 EWMA-only 124 ± 7 218 ± 11 268 ± 13 14.6 ± 0.6 Confidence-only 142 ± 8 242 ± 13 295 ± 15 13.1 ± 0.5 Adaptive  configuration  selection14 106 ± 7 197 ± 12 254 ± 14 19.3 ± 0.6

Privacy-aware  DNN  partitioning18 98 ± 6 181 ± 10 231 ± 12 21.0 ± 0.5

Multi-agent RL offloading19 89 ± 6 164 ± 9 208 ± 11 23.1 ± 0.6 SegFormer-B3 (cloud) 245 ± 12 356 ± 18 412 ± 21 7.8 ± 0.4 Proposed (balanced) 72 ± 5 138 ± 9 186 ± 11 27.4 ± 0.7

ARTICLE IN PRESS

The proposed framework achieves a median latency more than threefold lower than the cloud-only  baseline while sustaining throughput within 13% of the local-only ceiling.


> **Table 6 sets the framework against the three published offloading frameworks on the axes that**

> distinguish them, namely the signals admitted into the decision and the accuracy attained at the 
resulting latency. The reinforcement-learning policy approaches the present latency by scheduling 
on queue length and residual energy, yet its decision remains blind to the state of the perception 
model, so frames that the student resolves confidently are transmitted and frames over previously 
inspected ground are treated as novel. Admitting confidence and motion residual alongside 
bandwidth reduces median latency by a further 19% and shortens event-response delay by 37% 
relative to that policy, at a marginally higher IoU. Comparisons against published offloading 
frameworks are corrected separately over the three tests reported in Table 6.


> **Table 6. Comparison against published dynamic offloading frameworks under identical hardware,**

> link profiles and test partition.

Framework Signals entering the  decision

IoU Median  latency  (ms)

Throughput  (fps)

Event- response  delay (s)

Adaptive  configuration  selection

Uplink  bandwidth,  configuration set

0.813 ±  0.012 106 ± 7 19.3 ± 0.6 1.62 ± 0.41

Privacy-aware  DNN partitioning

Partition point, privacy  budget, link rate

0.818 ±  0.011 98 ± 6 21.0 ± 0.5 1.44 ± 0.36

Multi-agent  RL  offloading

Bandwidth,  queue  length, residual energy

0.821 ±  0.013 89 ± 6 23.1 ± 0.6 1.18 ± 0.33

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

Proposed  (balanced)

Bandwidth, prediction  confidence,  motion  residual

0.826 ±  0.013 72 ± 5 27.4 ± 0.7 0.74 ± 0.22

Event-response delay is the interval between an engineered link transition and settling of the  offloading ratio, measured over the three engineered event types of Figure 4c. Differences in  median latency between the proposed framework and each of the three frameworks are significant  under paired t-tests with Bonferroni correction over these three comparisons (padj = 0.0023, 0.0041  and 0.014 respectively).

Computational and communication cost enters the framework at three points. The student executes  4.1 GFLOPs per 512 × 512 tile against 79.0 GFLOPs for the teacher at the same input size, so  onboard cost is fixed per frame and independent of the decision, whereas cloud cost is incurred  only on offloaded frames and falls to approximately 17.4 GFLOPs on a region-of-interest crop at  a ratio of 0.22. The decision module requires one homography estimate, one entropy reduction  over candidate regions and three scalar updates, together 1.8 ms per frame on the onboard  processor, below 6% of local inference time and therefore small relative to the workload it  schedules. Uplink volume is 52 kB per full frame at a quality factor of 72 and 14 kB per region- of-interest crop at the same factor, with the refined mask returned run-length encoded at 4 kB,  giving a mean uplink demand of 0.40 MB s-1, or 3.2 Mbps, at the balanced operating point. That  this demand falls below the 8 Mbps floor of the emulated envelope accounts for the sub-linear  bandwidth sensitivity reported above, since the link ceases to bind before the lower end of the  tested range is reached. Aggregate figures are given in Table 7.

ARTICLE IN PRESS


> **Table 7. Computational cost and communication overhead per frame at the balanced operating**

> point.

Stage Execution  site

Params  (M)

GFLOPs per  invocation

Invocation  rate

Measured  time (ms)

Payload  (kB)

Coarse  segmentation,  STDC2-Tiny

Onboard 7.2 4.1 1.00 31.0 —

Three-factor  decision evaluation

Onboard — 0.02 1.00 1.8 —

JPEG  encoding,  ROI crop (r = 0.22,  q = 72)

Onboard — — 0.31 2.4 14

JPEG  encoding,  full frame (q = 72)

Onboard — — 0.20 6.1 52

Uplink  transmission

Link — — 0.51 18.0 —

Teacher  refinement,  ROI  crop

Cloud 47.3 17.4 0.31 12.0 —

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

Teacher  refinement,  full  frame

Cloud 47.3 79.0 0.20 41.0 —

Mask  downlink,  run-length encoded

Link — — 0.51 6.0 4

Temporal fusion Onboard — 0.05 0.07 0.9 —

Invocation rate is the fraction of frames reaching that stage, measured over 12,000 frames; the  three decision regimes account for 0.49 local termination, 0.31 region-of-interest offloading and  0.20 full-frame offloading. Teacher cost on a crop scales with the crop ratio, 79.0 × 0.22 GFLOPs  at r = 0.22. Temporal fusion is invoked once per keyframe interval, 1/kdense at kdense = 14. Mean  uplink demand is 0.40 MB s⁻¹, equivalently 3.2 Mbps, at a sustained 27.4 fps, and mean downlink  demand is 0.06 MB s⁻¹. Onboard cost is invariant to the decision, so the decision module consumes  5.8% of local inference time irrespective of the regime selected.


## 3. Discussion

Boundary-aware distillation contests the dominant view that small-capacity student backbones fall  short of large-capacity transformer teachers for fragmented target segmentation. A mere 0.018  Boundary IoU deficit compared to SegFormer-B3 21, despite being at 29.4% of its total inference  runtime and 6.6 times fewer parameters, proves competitive against the CBAM-DBNet  performance reported by Xiong et al.7 for equally challenging cotton-field scenes and even  approximates the DeepLabv3+ model proposed by Wang et al. 27. Agreement nonetheless falls to  κ = 0.687 on fragments below 200 pixels, and the ablation locates this shortfall in what distillation  transfers rather than in student capacity, since the same backbone gains 5.6 percentage points of  Boundary IoU from the attention-guided and boundary-supervised terms alone while the teacher  retains a measurable margin at the same scale. Comparable residual error on high-frequency edges  is reported for attention-guided distillation 28 and for multi-scale frequency fusion 8 , which points  to a limit in the supervision available at the boundary rather than in the architectures compared.

ARTICLE IN PRESS

At an acquisition scale of 0.5 cm per pixel a 200-pixel fragment corresponds to an area near 50  cm², approximately a 7 cm square, which places the degradation of the framework at the lower  margin of the size range that mechanised film collection engages. Tine and drum implements  recover sheet and large-fragment residue efficiently but leave fragments of this order within the  plough layer, where they contribute to the microplastic burden rather than to recoverable mass.  The maps produced here therefore support the targeting of remediation passes and the estimation  of recoverable residue, while the fraction below this scale is better treated as a stock to be  monitored than as a target to be collected, and closing the accuracy gap at that scale carries  monitoring rather than operational value.

Staged transfer across heterogeneous remote-sensing modalities preserves spectral priors that  monolithic fine-tuning typically discards. A 17.3% cross-region degradation when the satellite  branch is evaluated on a held-out Loess Plateau partition falls within the 15–25% envelope  reported for Sentinel-2 plastic-mulch mapping across heterogeneous Chinese agro-ecological  zones 5. The staged pipeline recovers 1.4 percentage points of IoU relative to training on UAV  imagery alone, of which 0.7 points are attributable to the satellite stage once ImageNet  initialisation is in place, indicating that the two-thousand-fold gap between 10 m and 0.5 cm  imagery is traversable when transfer proceeds in stages, though the marginal contribution of the

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

satellite prior does not reach significance at the present sample size and is modest beside that of  generic natural-image pretraining. Zhou et al. 29 reported analogous gains from prior-knowledge  injection on Sentinel-1/2 greenhouse extraction within a single sensor regime, and the present  cross-modal evidence narrows the conditions under which such priors generalise.

Objectives for scalar offloading do not adequately represent the trade-offs between latency and  accuracy in agriculture edge-cloud inference. The latency median value of 72 ms at a bandwidth  sensitivity of r = 5.7 across the 5-100 Mbps range demonstrates a better result than latency values  presented under similar circumstances by Suganya et al. 11, and the decision delay proposed by  Wei et al. 17 based on NSGA-II. The advantage does not arise from parameter tuning but from  admitting link variability, model uncertainty and motion residue jointly into the decision statistic,  which exposes non-dominated configurations that a scalar criterion over any one of these signals  cannot reach.


## 4. Methods


### 4.1 Overall framework and problem formulation

The proposed framework operates as a closed-loop perception pipeline distributed between an  onboard processor mounted on the UAV and a remote cloud inference service connected through  a heterogeneous wireless link. Captured RGB frames undergo lightweight coarse segmentation on  the onboard processor to produce an initial mulch-residue probability map, a per-frame confidence  estimate, and a temporal residual signal against the prior keyframe; the link-adaptive three-factor  decision module then determines whether the frame is terminated locally, partially offloaded as a  region-of-interest crop, or fully offloaded for refinement by a heavier segmentation model, with  refined masks returning from the cloud fused with onboard predictions through a temporal  consistency operator that stabilises segmentation output along the flight trajectory.

ARTICLE IN PRESS

The joint optimisation problem treats segmentation accuracy and end-to-end latency as competing  objectives over a five-dimensional decision space comprising keyframe density, region-of-interest  crop ratio, JPEG quality factor, and the lower and upper offloading thresholds:

  1 2 E2E max ( ) mIoU( ), min ( ) ; ( ) f f b t Î Î = = x x x x x x X X L  (1)

The first objective is the mean intersection-over-union attained on the emitted mask and the second  the end-to-end latency, both evaluated at the configuration x; the two are treated as competing  rather than combined, since no scalarisation is available that is valid across the deployment  scenarios and link conditions considered here. The feasible set X is bounded by onboard  compute budget, instantaneous uplink bandwidth  ( ) b t , and battery availability. The latency  objective decomposes as    E2E onboard tx cloud fuse ( ) b t = + + + L L L L L , in which the transmission term's

explicit bandwidth dependence renders any static configuration suboptimal across realistic  deployments. Decoupling the online decision module from the offline Pareto optimisation  reconciles long-horizon scheduling preferences with short-horizon link dynamics without  entangling the two timescales.

The data and control flow are depicted in Figure 1.

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

Edge / Onboard Wireless Link & Decision Cloud

Uplink bandwidth b(t)

5G Wi-Fi 4G

ROI offload – 14 kB/frame (rroi = 0.22,qjpeg = 72), 31% of frames

Captured RGB frame (Zenmuse P1, 4K @ 30 Hz,

~0.5 cm/px GSD)

Teacher Segmentation Model (SegFormer-B3, 47.3 M params,

Lcloud

79.0 GFLOPs full frame / 17.4 GFLOPs on ROI crop)

Onboard Processor (Jetson Xavier NX)

Lonboard

Full-frame offload -- 52 kB/frame (qjpeg = 72), 20% of frames

STDC2-Tiny student forward (7.2 M params,

Three-Factor Decision D(t)

Coarse probability

Tile & resize

(512 x 512)

map


### 4.1 GFLOPs,

FP16 / TensorRT)

τ 1 = 0.36,τ 2 = 0.62

Ltx (uplink + downlink)

Refined Segmentation Mask

evaluated on the onboard

processor, 1.8 ms per

frame

Temporal residual R(t) -- homography-

Confidence C(t) --

per-pixel entropy

Local termination - - 49% of frames, no transmission

compensated  change vs previous

over candidate

regions

keyframe

Downlink -- refined mask, 4 kB run-length encoded

ARTICLE IN PRESS

Temporal Fusion

Lfuse

Path Type

End-to-end latency L = Lonboard + Ltx(b(t)) + Lcloud + Lfuse, measured from completion of frame acquisition to  availability of the fused mask in onboard memory

Compulsory forward path

Conditional offloading path

Refined mask write-back


> **Figure 1. Overall architecture of the link-adaptive edge–cloud collaborative framework for UAV-**

> based plastic mulch residue assessment.


> **Figure 1 traces a complete frame from onboard acquisition through coarse segmentation, three-**

> factor decision branching, optional cloud refinement, and temporal fusion, with solid arrows 
marking compulsory paths and dashed arrows marking conditional offloading paths that activate 
only when the decision module triggers cloud assistance. The separation between onboard and 
cloud regions corresponds to the two execution domains over which the Pareto optimisation 
allocates computational load, while the temporal fusion block on the return path permits recovery 
from intermittent link degradation without restarting the inference pipeline.


### 4.2 Link-adaptive three-factor offloading decision module

The decision module constituting the principal contribution of this work evaluates three factors  capturing network conditions, perceptual difficulty, and temporal redundancy. The bandwidth  factor  ( ) B t % is an exponentially weighted moving average of measured uplink throughput with  smoothing parameter  0.3 a = , attenuating radio-level noise while preserving sub-second  responsiveness. The temporal residual factor quantifies pixel-wise change against the previous  keyframe after homography-based motion compensation,

  1 1 1 ( ) ( ) ( ) | |

t t p R t I p I p - ÎW = - W å‖ ‖ W  (2)

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

The warp operator maps the previous keyframe onto the current frame through a homography  estimated from sparse feature correspondences, so that R(t) registers scene change net of platform  motion; the norm is taken per pixel and averaged over the image domain, yielding a statistic  bounded by the dynamic range of the sensor and insensitive to isolated outliers, which triggers  early termination over previously inspected ground. The confidence factor aggregates the per-pixel  predictive entropy of the onboard segmentation model over candidate residue regions R ,

é ù = - ê ú ë û å å R R  (3)

1 ( ) ( )log ( ) | |

p p p c C t P c P c

Î Î

0,1

The inner sum is the Shannon entropy of the per-pixel class posterior, maximal where the student  assigns comparable probability to residue and to soil, and the outer average is restricted to  candidate residue regions so that the extensive uniform areas of bare soil dominating a typical  frame do not dilute the measure, biasing the decision towards cloud assistance when onboard  predictions approach the decision boundary. After min–max normalisation onto a common range,  a scalar decision variable combines the three factors as

t B t C t R D w B w C w R ¬ + + %  (4)

ARTICLE IN PRESS

Each factor is min-max normalised over a trailing window before combination, so that the weights  express relative influence on a common scale rather than absolute magnitudes in the native units  of throughput, nats and intensity. with the weight triple ( , , ) B C R w w w  predetermined via a separate  offline grid search over the simplex  1 B C R w w w + + = at resolution 0.05 and fixed at  (0.45,0.35,0.20) for all downstream evaluations, decoupling weight selection from the NSGA-II  Pareto optimisation over x .

The grid search minimises the median event-response delay measured over a held-out validation  sequence containing engineered link transitions, subject to the constraint that mean IoU on the  validation partition remains within one percentage point of the value obtained under uniform  weighting, with candidate triples enumerated on the simplex at a resolution of 0.05 and each triple  evaluated over three seeds. The triple is held fixed rather than admitted as a decision variable  because it governs the sensitivity of the online rule to signals measured continuously in flight,  whereas the Pareto vector governs configuration quantities set once per deployment; combining  the two would confound a control-gain calibration with an operating-point selection and would  enlarge the search space without extending the attainable front. Displacement of any single weight  by ±0.10 alters the offloading ratio by less than 0.04 and leaves the ordering of the three decision  regimes unchanged, as reported in Supplementary Figure S1.

Because the residual factor is evaluated after homography-based compensation, it responds to  scene change rather than to platform motion, and a change in ground speed alters its distribution  only through the parallax that a planar homography does not absorb. Over the acquisition envelope  of this campaign, 5 to 8 m s-1 ground speed and 25 to 40 m altitude, the normalised mean of R(t)  varied by less than 0.05 and the resulting offloading ratio by less than 0.03, as reported in  Supplementary Figure S2. The argument does not extend beyond this envelope, since at lower  altitude the planar assumption degrades over uneven ground and R(t) inflates, biasing the rule  towards unnecessary offloading, so redetermination of the triple is advisable when the acquisition  geometry departs materially from the calibration conditions.

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

In contrast to cloud–edge collaborative video offloading schemes that achieve accuracy–latency  trade-offs through compression-oriented or budget-constrained scalarisation at the stream level 30,  the present module integrates perceptual difficulty and temporal redundancy at the frame level,  permitting a frame to be retained locally even under abundant bandwidth when the onboard  estimate is confident and inter-frame change is minimal. This granularity avoids the over- offloading observed in bandwidth-only schemes without sacrificing recovery capability when  difficult frames appear. The trigger logic is formalised in Algorithm 1, which selects among local  termination, region-of-interest offloading and full-frame offloading by thresholding  ( ) D t against  two cut-off levels. These levels are not set by inspection but are carried as decision variables in  the Pareto optimisation of Section 4.4 and inherited from the selected operating point, so that the  boundary between local termination and region-of-interest offloading is placed by the criterion  that also fixes crop ratio and compression. Their influence is monotone and asymmetric. Lowering  the lower threshold moves marginal frames from local termination into offloading and raises  accuracy at the cost of uplink occupancy, raising the upper threshold suppresses full-frame transfer  and truncates the latency tail, and the interval between them governs the share of traffic carried as  region-of-interest crops.

ARTICLE IN PRESS

Algorithm 1. Edge-cloud collaborative inference for real-time plastic mulch  residue assessment

# Pseudocode 1 Input: Frame stream  1 { }

T

t t I = ; onboard student  Sf ; cloud teacher  Tf ; Pareto  operating point  1 2 roi jpeg dense , , , , r q k t t Q =  from Section 4.4; weight triple

( , , ) B C R w w w  from the offline grid search of Section 4.2; EWMA factor a 2 Output: Segmentation masks  1 { }T t t M = 3 1 0 0 0.5; 1, , B M I I - ¬ - ¬ Æ %

4 for  1, , t T = ¼  do 5 ( ) ( ) t S S t M f I ¬   > student forward pass on edge 6  ◆ Three-factor measurement  7 1 ( / max) (1 ), t t Bt b B B a a - ¬ × + - % %

8 ( ) 1 ( ) ( )

t t S p C H M p t Î ¬ å

R R 9 $ 1 1 1 ( ;, ) t t t t t R I I I

t

- ¬ - v ‖ ‖ W

10 t B t C t R t D w B w C w R ¬ + + %

11  ◆ Three-regime decision  12  if  1 t D t <  then  ( )t t S M M ¬   > local termination 13  else if  2 t D t <  then  ( )

roi jpeg ROI-Fuse , ; , ( ) t t S T M M f r q ¬   > ROI

offload 14  else  jpeg Cloud-Refine , ; ( ) t t T M I f q ¬   > full-frame offload

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

15  if  dense mod 0 t k =  then  1 TemporalFusion( , ) t t t M M M - ¬ 16 1 1 ; ; t t t t M M I I - - ¬ ¬  emit  t M 17 end for

The behaviour of the module under varying conditions is summarised in Figure 2.

Residual factor R(t) (motion-compensated inter-

Bandwidth factor B(t) (EWMA of uplink throughput)

Confidence factor C(t) (per-pixel entropy on R)

frame change)

Min-max  normalization

Min-max  normalization

Min-max  normalization

Weighted Sum D(t) = wBB̃ + wC·C + wRR̃

Weights {wB, wC, wR} = (0.45, 0.35, 0.20)

from offline grid search (Δ = 0.05 on

simplex)

D(t)

Yes

Local termination

D(t) < τ₁ = 0.36 ?

Thresholds τ₁, τ₂ carried as decision variables in the

ARTICLE IN PRESS

No

NSGA-II Pareto optimisation

Yes

ROI offload

D(t) < τ₂ = 0.62 ?

No

Full-frame offload


> **Figure 2. Link-adaptive three-factor offloading decision module.**

4.3 Plastic mulch-aware student–teacher segmentation with cross-scale transfer pretraining

The segmentation subsystem follows a teacher–student configuration in which a heavyweight  teacher is invoked on the cloud for offloaded regions while a lightweight student executes  continuously onboard for every frame. The teacher is built on a hierarchical transformer encoder  paired with a multilayer perceptron decoder producing high-resolution segmentation logits (47.3  M parameters), and the student adopts a short-term dense concatenation backbone augmented with  a Sobel-guided boundary attention branch that compensates for the feathered edges and partial- burial conditions of weathered residual film (7.2 M parameters). Knowledge transfer proceeds  through joint distillation of output logits and intermediate feature maps, building on transformer- to-CNN distillation principles shown to preserve the global context modelling capacity of  attention-based teachers while respecting the receptive-field constraints of convolutional students  31. The composite training objective combines pixel-wise cross-entropy, Dice loss on the residue  class, a boundary-IoU term, and an attention-guided distillation term,

   

Î = + + + - å F F P P

2 seg CE D Dice B B-IoU KD 2 T S l l l l l l l l f

S L L L L A  (5)

with  D B KD , , 1.0,0.3,0.5 l l l = ,  l A a channel- and spatial-attention refinement on teacher

T

lF at distillation stages S , and  lf a linear projector aligning student feature  dimensionality. The first term is the pixel-wise cross-entropy over the two classes, the second the  Dice loss computed on the residue class alone so that the extreme foreground-background  imbalance of a typical tile does not drive the optimisation towards the trivial solution, and the third

features

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

a boundary-IoU term evaluated on a dilated band around the annotated contour, which penalises  displacement of the predicted boundary without rewarding agreement in the interior. The final  term matches attention-refined teacher features to projected student features in squared Euclidean  distance, summed over the distillation stages, so that supervision reaches the student at  intermediate depths rather than only at the output. The coefficient on the Dice term is retained at  unity following established practice for class-imbalanced segmentation, while the boundary and  distillation coefficients were selected by a coarse search over {0.1, 0.3, 0.5, 1.0} on the validation  partition, the reported pair maximising Boundary IoU without degrading region IoU. Performance  was insensitive to variation of the boundary coefficient within ±0.2, whereas distillation  coefficients above 0.5 suppressed the supervised terms and reduced IoU on the residue class. The  attention-refined term follows evidence that attention-guided supervision sharpens the student  response in regions of high boundary curvature 28, where mulch boundaries dissolve into soil  texture.

The pretraining strategy bridges a two-thousand-fold scale gap between Sentinel-2 imagery at ten- metre resolution and UAV imagery at sub-centimetre ground sampling distance through a three- stage protocol: ImageNet classification weights, thirty epochs of refinement on weakly labelled  China-PMF-10 tiles injecting plastic-specific spectral and textural priors, and one hundred epochs  of fine-tuning on the self-collected UAV residue dataset. Self-supervised pretraining on satellite  imagery has been shown to recover transferable representations even when the downstream task  operates at substantially finer spatial resolution 32, motivating the retention of the satellite stage;  the boundary-IoU term is activated only at the third stage, since coarse satellite labels lack the  boundary fidelity required for boundary-supervised refinement.

ARTICLE IN PRESS

The architectural arrangement and the staged pretraining pipeline are illustrated in Figure 3.

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

a

Teacher branch (Cloud, SegFormer-B3, 47.3 M params)

Teacher forward path Student forward path Attention-guided distillation

Mask write-back

Stage1 (H/4 × W/4 ×

Stage4 (H/32 × W/32

Stage2 (H/8 × W/8 ×

Stage3 (H/16 × W/16

All-MLP  decoder

Refined

ROI crop

mask

64)

× 512)

128)

× 320)

Attention-guided distillation:  ) ( ) ( S l l T l l F F A   Mask write-

back

Student branch (Onboard, STDC2-Tiny, 7.2 M params)

STDC-2

STDC-3

Full frame STDC-1 (64 ch)

Sobel-guided boundary attention

Coarse

Composite training loss Lseg=LCE+λ D · LDice+λ B · L(B-IoU)+λ KD·

(dense  concat)

(dense  concat)

mask

attn KD L

{λ D，Λ b,λ KD}={1.0,0.3,0.5}

λD fixed at unity following practice for class-imbalanced segmentation;

λB, λKD selected by coarse search on the validation partition

b

ARTICLE IN PRESS


> **Figure 3. Plastic mulch-aware student–teacher segmentation with cross-scale transfer pretraining.**


> **Figure 3a depicts the cooperative student–teacher architecture with the boundary-aware loss**

> pathway and the cloud-to-onboard mask write-back channel, while Figure 3b lays out the three-
stage cross-scale pretraining pipeline. The asymmetry between the heavy teacher branch and the 
compact student branch in Figure 3a mirrors the two-tier execution model of the overall framework, 
while the directionality of the arrows in Figure 3b clarifies that satellite imagery serves as a 
representation prior rather than a downstream evaluation target, preventing the scale gap from 
contaminating in-domain evaluation.


### 4.4 NSGA-II-based bi-objective Pareto optimisation

Selecting an operating configuration that balances segmentation accuracy against end-to-end  latency requires explicit treatment of the trade-off rather than scalar collapse, since the relative  valuation depends on deployment scenario and link conditions. The non-dominated sorting genetic

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

algorithm of the second generation, whose elitist selection and crowding-distance preservation  remain widely adopted for problems with two to three objectives 33, is therefore employed to  recover the full Pareto frontier. The decision variable vector  dense roi jpeg 1 2 ( , , , , ) k r q t t = x • spans

keyframe  density  dense [1,30] k Î   frames  per  second,  region-of-interest  crop  ratio

roi [0.05,0.50] r Î , JPEG quality factor  jpeg [40,95] q Î , and the lower/upper offloading thresholds

1 [0.10,0.50] t Î ,  2 [0.50,0.90] t Î  subject to  1 2 t t < . Each candidate is evaluated under a link- emulation profile held fixed for the duration of a run so that solutions are compared under identical  channel conditions, and the optimisation is executed independently on three profiles corresponding  to 4G-LTE, 5G-NR and Wi-Fi 6, which are swept as discrete configurations rather than drawn at  random. Population size is fixed at one hundred and evolution proceeds for two hundred  generations using simulated binary crossover with distribution index twenty and polynomial  mutation at per-variable rate 1/ d .

Three representative operating points are extracted from the converged front: an accuracy-priority  point selecting the highest-mIoU non-dominated solution subject to a latency ceiling of fifteen  hundred milliseconds, a latency-priority point selecting the lowest-latency solution subject to an  mIoU floor of 0.65, and a balanced point located at the knee of the front. The knee is identified by  maximising the discrete curvature

ARTICLE IN PRESS

- + + - + =

* * * * *

*

2 2 ( )

f f f f f f i

- + - +

1, 1 1, 1, 1 2, 1 2, 2, 1

i i i i i i

f f f f k

(6)

     

3/2 * 2 2

+ - + -

* * * , 1 , 1

1

+ - + -

1 2

, 1 1, 1 2

i i i i

evaluated on the normalised front, where  ,*

,j i f  is the normalised value of objective j at the i -

th solution ordered by  1f . The expression is the discrete curvature of the front at the i-th solution,  formed from the first and second differences of the normalised objectives along the ordering  induced by  1f ; the knee is the point of maximal curvature, at which further reduction in latency  begins to cost disproportionately more accuracy. The deterministic rule replaces manual point- picking and ensures reproducibility from the raw front.

The empirical convergence behaviour, the recovered non-dominated front, and the comparison  against weighted-sum scalarisation are reported as part of the experimental evaluation in Section  2.3.


## 5. Conclusion

This work addressed a three-way constraint coupling segmentation accuracy, end-to-end latency  and uplink bandwidth in UAV-based plastic mulch residue assessment through an edge-cloud  collaborative inference framework integrating three coupled components. A composite three- factor decision module weighting EWMA-smoothed bandwidth, entropy-derived confidence and  motion-compensated residual achieved a median response delay of 0.74 s under abrupt link  transitions, representing a 3.4-fold reduction relative to fixed-threshold offloading. A plastic- mulch-aware student-teacher segmentation architecture with staged ImageNet → China-PMF-10  → UAV transfer pretraining attained IoU 0.826 and Boundary IoU 0.712 on the held-out UAV  residue partition, recovering 97.1% of the reference accuracy of cloud-only SegFormer-B3 at 29.4%  of its end-to-end latency. NSGA-II-based bi-objective Pareto optimisation over a five-dimensional

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

decision space yielded 78 non-dominated solutions on the 5G-NR profile across the explored  latency–accuracy trade-off region, with the balanced operating point providing 72 ms median  latency and sustained throughput above 26 fps across 10 to 500 Mbps uplink bandwidth, while  active cooling limited sustained-rate thermal degradation to 3.4% across full-length flight sessions.  Agreement of κ = 0.687 on sub-200-pixel fragments, corresponding to residue near 50 cm2, marks  the scale at which the framework ceases to inform collection planning and identifies boundary- aware distillation as the component with the clearest remaining margin.

The scope of these findings is bounded in several respects. The link was reproduced by a channel  emulator rather than measured over a live cellular network, so interference, contention and  handover behaviour in operational deployment may depart from the profiles used here. Evaluation  was confined to pre-sowing bare-soil conditions within a single basin, where residue is maximally  exposed, and performance under crop cover or following tillage remains unquantified. The satellite  branch was verified across regions but within a single sensor, leaving transfer to other  constellations open, and the operating point was selected per profile rather than adapted online.  Introducing an explicit energy term into the decision statistic, replacing the fixed weight triple with  an online estimator responsive to acquisition geometry, and strengthening boundary supervision  at the sub-200-pixel scale are the directions these limits indicate.

ARTICLE IN PRESS

Acknowledgement

This work was sponsored in part by Assessment of Residual Plastic Film in Farmland Using Image  Semantic Segmentation (XJEDU2023P058)

Conflict of Interest Disclosure

The authors declare no conflicts of interest.

Author contributions

X.Z. conceived the study and designed the edge–cloud collaborative framework. X.Z. and J.Z.  developed the methodology for the joint optimization of image segmentation accuracy and UAV  transmission latency. D.D. and J.X. implemented the semantic segmentation model and the edge- side deployment, and conducted the UAV data acquisition and field experiments. S.A. performed  data curation and statistical analysis of the residual plastic film assessment results. X.Z. and J.Z.  interpreted the experimental results and prepared the figures. X.Z. wrote the original draft, and  J.Z., D.D., J.X. and S.A. reviewed and edited the manuscript. X.Z. supervised the project and  acquired funding. All authors read and approved the final manuscript.

Data availability

The China-PMF-10 satellite dataset used for the satellite-stage pretraining is publicly available on  Figshare (https://doi.org/10.6084/m9.figshare.28528919). The PMF-LP cross-region test set used  for the generalisation evaluation in Section 2.4 is publicly available on Zenodo  (https://zenodo.org/record/13369426). The UAV residue dataset self-collected by the authors  (4,287 tiles at 512 × 512 pixels, 0.5 cm/pixel ground sampling distance) is not publicly deposited  and is available from the corresponding author on reasonable request.

Code availability

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

The source code implementing the three-factor offloading decision module, the student-teacher  segmentation architecture with attention-guided distillation, and the NSGA-II bi-objective Pareto  optimisation is archived at Zenodo (https://doi.org/10.5281/zenodo.21635293).

Reference

1 Liu, B., Li, W., Pan, X. & Zhang, D. The persistently breaking trade-offs of three-decade plastic film mulching:  Microplastic pollution, soil degradation and reduced cotton yield. Journal of Hazardous Materials 439,  129586, doi:10.1016/j.jhazmat.2022.129586 (2022). 2 Yang, X. Hazards of residual plastic film pollution in Xinjiang cotton fields and strategies for sustainable control:  A review. Sustainable Horizons, 100282, doi:10.1016/j.horiz.2025.100282 (2025). 3 Zhai, Z. et al. Evaluation of residual plastic film pollution in pre-sowing cotton field using UAV imaging and  semantic segmentation. Frontiers in Plant Science 13, 991191, doi:10.3389/fpls.2022.991191 (2022). 4 Qiu, F. et al. UAV imaging and deep learning based method for predicting residual film in cotton field plough layer.  Frontiers in Plant Science 13, 1010474, doi:10.3389/fpls.2022.1010474 (2022). 5 Lu, L., Xu, Y., Huang, X., Zhang, H. K. & Du, Y. Large-scale mapping of plastic-mulched land from Sentinel-2  using an index-feature-spatial-attention fused deep learning model. Science of Remote Sensing 11, 100188,  doi:10.1016/j.srs.2025.100188 (2025). 6 Dong, X. et al. A novel phenology-based index for plastic-mulched farmland extraction and its application in a  typical agricultural region of China using Sentinel-2 imagery and Google Earth Engine. Land 13, 1825,  doi:10.3390/land13111825 (2024). 7 Xiong, L. et al. Detection and threshold-adaptive segmentation of farmland residual plastic film images based on  CBAM-DBNet. International Journal of Agricultural and Biological Engineering 17, 231-238,  doi:10.25165/j.ijabe.20241705.8069 (2024). 8 Zhang, M., Zhang, J., Peng, Y. & Wang, Y. FreqDyn-YOLO: A high-performance multi-scale feature fusion  algorithm for detecting plastic film residues in farmland. Sensors 25, 4888, doi:10.3390/s25164888 (2025). 9 Hao, H., Xu, C., Zhang, W., Yang, S. & Muntean, G.-M. Joint task offloading, resource allocation, and trajectory  design for multi-UAV cooperative edge computing with task priority. IEEE Transactions on Mobile  Computing 23, 8649-8663, doi:10.1109/TMC.2024.3350078 (2024). 10 Guo, H., Wang, Y., Liu, J. & Liu, C. Multi-UAV cooperative task offloading and resource allocation in 5G  advanced  and  beyond.  IEEE  Transactions  on  Wireless  Communications  23,  347-359,  doi:10.1109/TWC.2023.3265329 (2024). 11 Suganya, B., Gopi, R., Ranjith Kumar, A. & Singh, G. Dynamic task offloading edge-aware optimization  framework for enhanced UAV operations on edge computing platform. Scientific Reports 14, 16710,  doi:10.1038/s41598-024-67285-2 (2024). 12 Ren, H. et al. Latency minimization for UAV-enabled URLLC-based mobile edge computing systems. IEEE  Transactions on Wireless Communications 23, 3298-3311, doi:10.1109/TWC.2023.3307154 (2024). 13 Yang, B., Cao, X., Yuen, C. & Qian, L. Offloading optimization in edge computing for deep learning-enabled  target  tracking  by  internet  of  UAVs.  IEEE  Internet  of  Things  Journal  8,  9878-9893,  doi:10.1109/JIOT.2020.3016694 (2022). 14 Zhang, S. et al. Adaptive configuration selection and bandwidth allocation for edge-based video analytics.  IEEE/ACM Transactions on Networking 30, 285-298, doi:10.1109/TNET.2021.3106937 (2022). 15 Sukkar, M. et al. Dynamic multi-objective optimization in vehicular fog computing with NSGA-II+. Transactions  on Emerging Telecommunications Technologies 36, e70260, doi:10.1002/ett.70260 (2025). 16 Zhang, J. et al. Learning enhanced scheduling and resource allocation for heterogeneous UAV swarms in edge  assisted remote sensing. Scientific Reports 15, 26889, doi:10.1038/s41598-025-34497-z (2025). 17 Wei, P., Liu, M., Cai, Z., Yu, Y. & Wei, L. Improved NSGA-II algorithm-based task offloading decision in the  internet of vehicles edge computing scenario. Multimedia Systems 30, 372, doi:10.1007/s00530-024-01598- 0 (2024). 18 Cheng, Z. et al. Privacy-aware joint DNN model deployment and partition optimization for delay-efficient  collaborative  edge  inference.  IEEE  Transactions  on  Services  Computing  18,  1547-1562,  doi:10.1109/TSC.2025.3536791 (2025). 19 Zhao, N., Ye, Z., Pei, Y., Liang, Y.-C. & Niyato, D. Multi-agent deep reinforcement learning for task offloading  in UAV-assisted mobile edge computing. IEEE Transactions on Wireless Communications 21, 6949-6960,  doi:10.1109/TWC.2022.3153316 (2022). 20 Bai, Z., Lin, Y., Cao, Y. & Wang, W. Delay-aware cooperative task offloading for multi-UAV enabled edge-cloud

ARTICLE IN PRESS

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

computing. IEEE Transactions on Mobile Computing 23, 1034-1049, doi:10.1109/TMC.2022.3232525  (2024). 21 Xie, E. et al. in Advances in Neural Information Processing Systems (NeurIPS). 12077-12090. 22 Fan, M. et al. in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR).  9716-9725. 23 Luo, J. et al. Efficient small object detection you only look once: A small object detection algorithm for aerial  images. Sensors 24, 7067, doi:10.3390/s24217067 (2024). 24 Wang, J. et al. A multi-scale remote sensing semantic segmentation model with boundary enhancement based on  UNetFormer. Scientific Reports 15, 14737, doi:10.1038/s41598-025-99663-9 (2025). 25 He, S. et al. A new framework for improving semantic segmentation in aerial imagery. Frontiers in Remote Sensing  5, 1370697, doi:10.3389/frsen.2024.1370697 (2024). 26 Niu, B. et al. National-scale mapping of plastic-mulched farmlands in China based on deep semantic segmentation  and Sentinel-2 imagery. Remote Sensing of Environment 338, 115368, doi:10.1016/j.rse.2026.115368 (2026). 27 Wang, Y., Yang, L., Liu, X. & Yan, P. An improved semantic segmentation algorithm for high-resolution remote  sensing images based on DeepLabv3+. Scientific Reports 14, 9716, doi:10.1038/s41598-024-60375-1 (2024). 28 Mansourian, A. M. et al. in Proceedings of the AAAI Conference on Artificial Intelligence.13 edn 4203-4211. 29 Zhou, C., Huang, J., Xiao, Y., Du, M. & Li, S. A novel approach: Coupling prior knowledge and deep learning  methods for large-scale plastic greenhouse extraction using Sentinel-1/2 data. International Journal of  Applied Earth Observation and Geoinformation 132, 104073, doi:10.1016/j.jag.2024.104073 (2024). 30 Cui, L. et al. CREAT: Blockchain-assisted compression algorithm of federated learning for content caching in edge  computing. IEEE Internet of Things Journal 10, 14151-14161, doi:10.1109/JIOT.2022.3163700 (2023). 31 Liu, R. et al. TransKD: Transformer knowledge distillation for efficient semantic segmentation. IEEE Transactions  on Intelligent Transportation Systems 25, 15933-15946, doi:10.1109/TITS.2024.3455416 (2024). 32 Chopra, M., Chhipa, P. C., Mengi, G., Gupta, V. & Liwicki, M. in Proceedings of the International Joint  Conference on Neural Networks (IJCNN). 1-8. 33 Deb, K., Pratap, A., Agarwal, S. & Meyarivan, T. A fast and elitist multiobjective genetic algorithm: NSGA-II.  IEEE Transactions on Evolutionary Computation 6, 182-197, doi:10.1109/4235.996017 (2002).

ARTICLE IN PRESS
