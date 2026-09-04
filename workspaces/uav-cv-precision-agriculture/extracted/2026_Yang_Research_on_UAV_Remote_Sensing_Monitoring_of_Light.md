---
workspace_id: SCI-001316
doi: 10.1109/cvidl70130.2026.11637617
title: Research on UAV Remote Sensing Monitoring of Lightweight Wheat Lodging Segmentation
  Network Using Multimodal Fusion (RGB+DSM)
authors:
- family_name: Yang
  given_name: Chenchen
  orcid: null
- family_name: Wang
  given_name: Qang
  orcid: null
- family_name: Duan
  given_name: Xiaohong
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:41.999541+00:00'
---

# Research on UAV Remote Sensing Monitoring of Lightweight Wheat Lodging Segmentation Network Using Multimodal Fusion (RGB+DSM)

2026 7th International Conference on Computer Vision, Image and Deep Learning (CVIDL)

Research on UAV Remote Sensing Monitoring of  Lightweight Wheat Lodging Segmentation Network

Using Multimodal Fusion (RGB+DSM)

Xiaohong Duan  School of Information Engineering  Shandong Huayu University of Technology

Chenchen Yang  School of Information Engineering  Shandong Huayu University of Technology

Qang Wang*  College of Information and Management

2026 7th International Conference on Computer Vision, Image and Deep Learning (CVIDL) | 979-8-3195-4465-0/26/$31.00 ©2026 IEEE | DOI: 10.1109/CVIDL70130.2026.11637617

Science  Henan Agricultural University

Dezhou, Shandong, China

Dezhou, Shandong, China

Zhengzhou, Henan, China  *17863943627@163.com

designs a dual-branch lightweight encoder as well as a cross- modal dynamic gating fusion module[6]. On this basis, we  construct  ML-LodgingNet,  a  specialized  segmentation  network for wheat lodging that achieves a good balance  among high accuracy, lightweight architecture, and real-time  inference, providing a novel technical solution for rapid UAV- based monitoring of wheat lodging.


## Abstract: UAV remote sensing combined with deep learning–

based semantic segmentation has become a mainstream 
technique for the intelligent monitoring of wheat lodging. 
Nevertheless, current approaches are prone to interference from 
field shadows, weeds, and ridges, leading to blurred segmentation 
boundaries, frequent false and missed detections, excessive model 
parameters, and difficulty in real-time deployment on airborne 
platforms. To tackle these issues, this study proposes a 
lightweight 
wheat 
lodging 
segmentation 
network, 
ML-
LodgingNet, using RGB images and DSM data synchronously 
collected by UAVs at the wheat maturity stage. Experimental 
results demonstrate that the proposed network achieves 
Intersection over Union (IoU) values of 89.42% and 70.65% on 
simple and complex test subsets, respectively, with corresponding 
segmentation accuracies of 95.61% and 90.13%. The model 
contains only 1.26 M parameters and delivers a real-time 
inference speed of 19.3 FPS on edge devices. Compared with the 
single RGB modality, the RGB+DSM multimodal fusion strategy 
improves key evaluation indicators by 4.2%–9.1% on average, 
significantly enhancing lodging segmentation accuracy and 
boundary integrity in complex field environments. This work 
provides an effective algorithmic support for real-time UAV-
borne monitoring of wheat lodging.

II. MATERIALS AND METHODSTITLE

A. Study Area and Data Acquisition

The study area is located in the wheat cultivation region of  Qingfeng County, Puyang City, Henan Province. It has a  northern  subtropical  monsoon  climate  featured  by  synchronous rainfall and heat as well as sufficient sunshine,  which makes it a typical large-scale and standardized wheat  production area. Data collection was carried out during the  wheat maturity stage. Images were acquired between 11:00  and 14:00 under clear and calm weather conditions with stable  illumination. A DJI Mavic Air drone was used to collect RGB  visible images and DSM elevation data synchronously,  ensuring high imaging quality and stable flight attitude. The  partially acquired images are shown in Figure 1.

Keywords: wheat lodging; multimodal fusion; RGB; DSM;  lightweight network; semantic segmentation; UAV remote sensing

I.  INTRODUCTION

Wheat is highly prone to lodging during the middle and  late growth stages, mainly caused by adverse weather  conditions, unreasonable planting density, and improper water  and fertilizer management. Under normal climatic conditions,  wheat lodging can lead to a yield loss of 10%–30%, and this  loss can exceed 50% in severe lodging cases[1-2]. Moreover,  lodging can easily induce crop diseases, reduce grain quality,  and lower the efficiency of mechanical harvesting. Unmanned  aerial vehicle (UAV) remote sensing has become a core data  acquisition approach for crop disaster monitoring owing to its  merits of high flexibility, efficiency, spatial resolution, low  cost, and weak terrain constraints[3]. Combining UAV data  with deep learning-based semantic segmentation enables  pixel-level automatic extraction of lodged wheat regions[4][5].  Nevertheless, existing methods still suffer from obvious  limitations. This study exploits the complementary properties  of RGB texture features and DSM elevation features, and


> **Figure 1. Sample image data of some lodged wheat**

B. Data Preprocessing and Dataset Construction

To ensure the quality of raw multimodal data, eliminate  errors caused by UAV flight attitude and imaging distortion,  achieve precise alignment between RGB and DSM data, and  provide standardized, high-quality data for model training, this  study conducts systematic and standardized preprocessing on  raw RGB imagery and DSM elevation data collected by UAVs.  The core preprocessing workflow comprises five key stages:  panoramic image stitching and geometric correction, pixel- level precise registration of multimodal data, uniform image

979-8-3195-4465-0/26/$31.00 ©2026 IEEE 1252

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:44:14 UTC from IEEE Xplore.  Restrictions apply.


> **Figure 2 shows a detailed structural diagram of the gating**

> fusion module.

cropping, removal of invalid samples, and sample data  augmentation.

Following preprocessing, a specialized multimodal dataset  (RGB+DSM) for wheat lodging detection was constructed  using the validated paired data. An efficient annotation  strategy—involving uniform image cropping followed by  precise sample annotation—was adopted to significantly  reduce the workload and labor costs associated with large- scale,  fine-grained,  pixel-level  field  annotation.  The  professional image annotation tool LabelMe was utilized to  perform precise pixel-level binary annotation, strictly  categorizing areas into "wheat lodging target regions" and  "non-lodging background regions"; specifically, red-annotated  areas represent the core wheat lodging targets, while black- annotated areas represent non-lodging wheat and irrelevant  background elements such as soil, weeds, and field ridges.


> **Figure 2.Detailed Structure Diagram of the Gated Fusion Module.The**

> heatmap displays normalized gating weights, where values closer to 1 indicate 
greater reliance on Input Modality A, and values closer to 0 indicate 
preference for Modality B.This confirmsthe module’sability to adaptively 
selectthe optimalmodality.

The final multimodal dataset contains a total of 10,460  valid samples, all consisting of paired RGB and DSM images.  These samples were randomly split into training and testing  sets at a standard 8:2 ratio. The training set comprises 8,000  samples, used primarily for iterative model training,  optimization of network weights, and fine-tuning for model  convergence; the testing set contains 2,460 samples, dedicated  to the quantitative evaluation and performance testing of the  model's segmentation capabilities.

1.The dual-branch lightweight encoder comprises an RGB  texture branch and a DSM elevation branch with a symmetric  structure and independent parameter updates. It adopts  depthwise separable convolutions in the whole network, which  reduces the number of parameters by more than 75%  compared with standard convolutions. A lightweight cross- attention module is embedded at each downsampling stage to  enhance lodging target features and suppress background noise.

C. ML-LodgingNet Network Architecture

The network adopts an encoder – decoder architecture,  which consists of a dual-branch lightweight encoder, a cross- modal dynamic gating fusion module, and a lightweight  decoder. This module firstly standardizes the channel  dimensions and normalizes the semantic distribution of multi- scale feature maps output from the dual-branch encoder, which  effectively eliminates fusion biases induced by the inconsistent  channel numbers and feature value distributions between RGB  and DSM modal features. Subsequently, a gated weight  generation sub-network is constructed to generate adaptive  fusion weight coefficients for RGB texture features and DSM  elevation features, respectively. The two sets of weight  coefficients are constrained to a sum of 1, which guarantees  the balance and stability of multimodal feature fusion. Finally,  the gated weighted multimodal features are deeply fused  through channel concatenation. This operation significantly  enhances the feature response intensity of texture and  elevation information in wheat lodging regions, while  suppressing the interference responses from irrelevant  background features including field shadows, weeds, and field  ridges. The mathematical formulation of the proposed cross- modal dynamic gating fusion strategy is defined as follows:

2.The cross-modal dynamic gating fusion module performs  channel unification and standardization for multi-scale  features.

3.The lightweight decoder adopts bilinear interpolation  upsampling and 1×1 convolutions to reduce computational  cost. It fuses shallow detailed features via skip connections to  alleviate  edge  blurring.  Finally,  pixel-level  binary  classification segmentation results are generated after the  Sigmoid activation function..

D. Loss Function and Evaluation Metrics

In this study, a weighted composite loss function that  combines Focal Loss and Dice Loss is designed according to  the specific requirements of multimodal lightweight wheat  lodging segmentation, so as to balance sample distribution and  improve segmentation overlap accuracy[7]. The composite  loss function is formulated as follows:

Ltotal = λLfocal + (1 −λ)Ldice  (2)

Where: Ltotal denotes the total composite loss; Lfocal is the  focal loss; Ldice is the Dice loss; and λ is the balancing  coefficient between the two loss terms, which is set to 0.5 in  all experiments. The proposed composite loss function  integrates the merits of both loss functions, which effectively  improves the segmentation performance of the model in  complex field scenarios, accelerates training convergence, and  promotes the optimization of network parameters[8].

𝐅𝐅𝑓𝑓𝑓𝑓𝑓𝑓𝑓𝑓= 𝛼𝛼⋅𝐅𝐅𝑟𝑟𝑟𝑟𝑟𝑟+ (1 −𝛼𝛼) ⋅𝐅𝐅𝑑𝑑𝑑𝑑𝑑𝑑  (1)

where𝐅𝐅𝑓𝑓𝑓𝑓𝑓𝑓𝑓𝑓denotes the final fused multimodal feature map,  𝐅𝐅𝑟𝑟𝑟𝑟𝑟𝑟 represents the texture feature map extracted from the  RGB branch, 𝐅𝐅𝑑𝑑𝑑𝑑𝑑𝑑 refers to the elevation structural feature  map obtained from the DSM branch, and 𝛼𝛼 is the adaptive  gating weight coefficient learned end-to-end by the network,  which is constrained within the range of [0, 1].

To comprehensively, objectively, and quantitatively  evaluate the segmentation accuracy, lightweight feasibility,  and real-time inference performance of the proposed ML-

1253 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:44:14 UTC from IEEE Xplore.  Restrictions apply.

segmentation accuracy, lightweight performance, and real- time inference speed. Its advantages are especially significant  in complex field scenarios, fully satisfying the requirements  for edge deployment on UAV platforms.

LodgingNet network, three widely used metrics are adopted  for segmentation accuracy: overall accuracy, F1-score, and  Intersection over Union (IoU)[9]. Higher values of these three  metrics reflect better segmentation precision and integrity. For  lightweight and real-time performance evaluation, the number  of parameters (Million) and edge inference frame rate (FPS)  are utilized. A smaller parameter size indicates stronger model  compression ability and less storage occupation, while a  higher FPS represents faster inference speed and better  adaptability for real-time monitoring on edge devices.[10] All  metrics are evaluated in concert to comprehensively verify the  model's overall application performance.

C. Ablation Test of Core Module

To quantitatively verify the effectiveness and performance  contributions of the three core innovations, namely DSM  elevation modality supplementation, multimodal fusion  strategy, and cross-modal dynamic gating fusion module, three  groups of controlled ablation experiments were conducted in  this study. Following the single-variable principle, core  modules were sequentially removed for comparative testing to  accurately quantify the performance improvement brought by  each module. The ablation results are presented in Table 2.

III. RESULTS AND ANALYSIS

A. Test Environment

All experiments were implemented on the Windows Server  2022 operating system. The PyTorch deep learning framework  (open-source) and Python 3.10 were employed for model  development and training. Uniform standard hyperparameters  were used throughout training: the batch size was set to 8, the  initial learning rate to 0.001, the weight decay coefficient to  0.0001, and the total training epochs to 80[11]. The AdamW  optimizer was adopted, and all hyperparameters were fixed  during training to ensure consistent experimental settings,  reliable results, and valid comparisons[12].

TABLE 2. ABLATION TEST RESULTS OF CORE MODULE

Dynamic

Test

Model  parameter

Ablation  experimental

RGB  modal

DSM  Modal

Gating  Fusion  Module

set  IoU/%

count / M

group

input

Input

Experimental  Group 1 (Single  RGB mode only)

√  ×  ×  81.62  1.22

Experimental  Group 2 (Simple  splicing and fusion

√  √  ×  84.92  1.24

of RGB+DSM)

B. Comparative Experiments of Different Models

Experimental  Group 3 (Complete

√  √  √  89.42  1.26

To comprehensively quantify and validate the superior  performance  and  suitability  of  the  proposed  ML- LodgingNet—a  multimodal  lightweight  segmentation  network—for wheat lodging segmentation, four mainstream  semantic segmentation models (UNet, DeepLabv3+, U2NetP,  and SegNet) were selected as benchmarks. All models utilized  the same RGB+DSM multimodal dataset, unified training  hyperparameters, and identical experimental hardware and  software environments. Iterative training and performance  testing were conducted concurrently, with comprehensive  comparative experiments performed on both simple and  complex test subsets to quantitatively evaluate segmentation  accuracy, model lightweightness, and real-time inference  performance.[13]  The  comparison  results  regarding  segmentation performance and lightweightness metrics for the  different models are presented in Table 1.

Model in this

Paper)

Quantitative results of the ablation study verify that all  three core innovative modules are indispensable and contribute  substantially to boosting the segmentation performance of the  proposed model. When only RGB imagery is fed into the  network, the model achieves the minimal IoU of merely  81.62%, accompanied by severe segmentation artifacts on  complex and ambiguous field samples. Such a performance  degradation reveals that unimodal RGB texture features  exhibit poor anti-interference capability and fail to support  accurate segmentation of lodged wheat under complex  farmland scenarios, which highlights the necessity of  introducing DSM elevation information as complementary  modal data.Simple fixed-weight concatenation fusion that  incorporates RGB and DSM features yields a 3.3% IoU  improvement, which validates the superiority of multimodal  information complementarity for segmentation accuracy, yet  this straightforward fusion strategy still suffers from limited  representation capacity. By embedding the cross-modal  dynamic gated fusion module proposed in this work, the IoU  metric is further elevated by 4.5%, delivering the optimal  segmentation performance across all ablation variants. This  substantial gain demonstrates that the presented adaptive  dynamic gating mechanism mitigates the semantic discrepancy  between  different  modalities,  generating  far  more  discriminative fused features compared with conventional  naive concatenation fusion schemes.

TABLE 1. COMPARISON OF SEGMENTATION PERFORMANCE AND LIGHTWEIGHT

METRICS OF DIFFERENT MODELS

Simpl

Edge  inferenc

Comple

Model  paramete

e test

Network

Segmentatio

x test

set  IoU/

e frame  rate/FP

model

n accuracy

set  IoU/%

r count /

name

/ %

M

S  UNet  82.15  62.37  92.04  29.44  6.2  DeepLabv3

%

+  83.57  64.12  92.87  36.72  4.8

U2NetP  85.23  66.89  93.45  1.13  15.6  SegNet  81.06  61.54  91.62  31.03  5.4  ML- LodgingNet  (This paper)

89.42  70.65  95.61  1.26  19.3

D. Robustness Test

The quantitative experimental results demonstrate that  ML-LodgingNet  outperforms  all  baseline  models  in

To fully verify the anti-interference capability and  operational stability of the ML-LodgingNet network in

1254 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:44:14 UTC from IEEE Xplore.  Restrictions apply.

and provides a feasible technical approach for disaster  monitoring in smart agriculture.

complex UAV field scenarios, and to reflect real-world  conditions including varying illumination, crop occlusion, and  image blurring, this study conducted dedicated robustness tests  under three typical field disturbances: light intensity variation,  crop occlusion, and image motion blur. These tests  quantitatively evaluate the segmentation performance of the  model under complex interference. The robustness test results  are presented in Table 3.

ACKNOWLEDGMENT

This work was supported by Dezhou Big Data and  Intelligent Sensing Technology Engineering Research Center  under the projects No. PT2025KJX002.


## REFERENCES

TABLE 3. ROBUSTNESS TEST RESULTS OF THE MODEL IN COMPLEX SCENARIOS

[1] Azizi, A., Zhang, Z., Rui, Z., Li, Y., Igathinathane, C., Flores, P., ... &

Zhang, M. (2024). Comprehensive wheat lodging detection after initial  lodging using UAV RGB images.Expert Systems with Applications,238,  121788,https://doi.org/10.1016/j.eswa.2023.121788.  [2] C.J. Baker, P.M. Berry, J.H. Spink, R. Sylvester-Bradley, J.M. Griffin,

Types of field interference conditions  Model segmentation accuracy

/ %  Normal standard operating conditions  95.61  Light intensity disturbance conditions  86.12  Field crop shading conditions  94.35  Image motion blur condition  90.07    Experimental data from robustness tests indicate that,  although the segmentation accuracy of the proposed model  drops slightly under various complex field interference  conditions, it maintains a high overall level of precision with  minimal performance fluctuation; the model demonstrates  stable and reliable operation, making it suitable for actual field  missions involving unmanned aerial vehicles.

R.K. Scott, R.W. Clare,A Method for the Assessment of the Risk of  Wheat Lodging,Journal of Theoretical Biology,Volume 194, Issue  4,1998,Pages 587-603,https://doi.org/10.1006/jtbi.1998.0778.  [3] Guo, Y., Zhou, W., Fu, Y. H., Hao, F., Zhang, X., Xu, L., ... & He, Y.

(2025). SegNeXt-RCMSCA: An improved SegNeXt network for  detecting winter wheat lodging from UAS RGB images.Smart  Agricultural Technology, 101230.  https://doi.org/10.1016/j.smartag.2025.101230.  [4] Yu, J., Cheng, T., Cai, N., Zhou, X. G., Diao, Z., Wang, T., ... & Zhang,

D. (2023). Wheat lodging segmentation based on Lstm_PSPNet deep  learning network.Drones,7(2), 143..  https://doi.org/10.3390/drones7020143.  [5] Biswal, S., Chatterjee, C., & Mailapalli, D. R. (2023). Damage

IV. CONCLUSION

assessment due to wheat lodging using UAV-based multispectral and  thermal imageries.Journal of the Indian society of remote sensing,51(5),  935-948..https://doi.org/10.1007/s12524-023-01680-6.  [6] Celik, M. F., Nagarajan, P., Nelson, A., Unnisa, Z., Ogutu, B., Dash,

In this study, a multimodal dataset dedicated to wheat  lodging is constructed using RGB images and DSM elevation  data synchronously collected by UAVs. A lightweight  semantic segmentation network with dual-branch encoding  and dynamic gating fusion, namely ML-LodgingNet, is  innovatively proposed. The segmentation performance,  effectiveness of key modules, and field applicability of the  model are comprehensively verified through comparative  experiments, ablation experiments, and robustness tests. The  core conclusions are drawn as follows

J., ... & Darvishzadeh, R. (2026). Hyperspectral assessment of wheat  lodging: From field to EnMAP satellite observations. International  Journal of Applied Earth Observation and Geoinformation,149,  105289..https://doi.org/10.1016/j.jag.2026.105289.  [7] Long, J., Zhang, Z., Zhang, Q., Zhao, X., Igathinathane, C., Xing, J., ...

& Zhang, M. (2025). Comprehensive wheat lodging detection under  different UAV heights using machine/deep learning models. Computers  and Electronics in Agriculture,231, 109972.   https://doi.org/10.1016/j.compag.2025.109972.  [8] Feng, G., Wang, C., Wang, A., Gao, Y., Zhou, Y., Huang, S., & Luo, B.

(1)RGB texture features and DSM elevation features are  highly complementary. The RGB4DSM multimodal fusion  strategy can effectively suppress interferences such as  shadows and weeds, improving the core indicators of lodging  segmentation by 4.2-9.1% on average, with more significant  improvements observed in complex scenarios

(2024). Segmentation of wheat lodging areas from UAV imagery using  an ultra-lightweight network.Agriculture,14(2), 244.  https://doi.org/10.3390/agriculture14020244.  [9] Fan, X., Zhi, S., Tjahjadi, T., Liu, J., Bai, Z., Ye, Q., & Huan, H. (2026).

Integrating UAV-acquired RGB and LiDAR point cloud data using  multimodal  learning  for  wheat  lodging  mapping  and  area  estimation.IEEE  Journal  of  Selected  Topics  in  Signal  Processing.https://doi.org/10.1109/JSTSP.2026.3156789.  [10] Zhang, P., Zhang, S., Wang, J., & Sun, X. (2024). Identifying rice

(2)The cross-modal dynamic gating fusion module is able  to adaptively bridge the semantic gap and dynamically assign  feature weights. Its fusion performance is significantly  superior to the traditional simple concatenation method, which  constitutes the key to enhancing segmentation accuracy,

lodging based on semantic segmentation architecture optimization with  UAV  remote  sensing  imaging.Computers  and  Electronics  in  Agriculture,227, 109570.https://doi.org/10.1016/j.compag.2024.109570.  [11] Rabieyan, E., Darvishzadeh, R., & Alipour, H. (2024). Correction:

(3)ML-LodgingNet has only 1.26 M parameters and  achieves an edge inference speed of 19.3 FPS. The IoU values  on the simple and complex test sets reach 89.42%and 7065%,  respectively. The model realizes a favorable balance between  high precision and lightweight characteristics, making it  suitable for real-time UAV-borne deployment

Identifcation and estimation of lodging in bread wheat genotypes using  machine  learning  predictive  algorithms.Plant  Methods,20(1),  86.https://doi.org/10.1186/s13007-024-01203-5.  [12] Tang, Z., Zhu, Y., Huang, M., & Zhu, J. (2024), December). A study on

a wheat image recognition system based on transformer and mamba  networks with light enhancement. In2024 5th International Conference  on Computers and Artificial Intelligence Technology (CAIT)(pp. 111- 115). IEEE.https://doi.org/10.1109/CAIT63228.2024.10876542.  [13] Sun, Q., Chen, L., Xu, X., Gu, X., Hu, X., Yang, F., & Pan, Y. (2022). A

(4)The  model  exhibits  strong  robustness  against  illumination variations, crop occlusion, and motion blur, as  well as satisfactory generalization ability. It can satisfy the  demand for real-time UAV monitoring of field wheat lodging

new comprehensive index for monitoring maize lodging severity using  UAV-based multi-spectral imagery. Computers and Electronics in  Agriculture,202, 107362.https://doi.org/10.1016/j.compag.2022.107362.

1255 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:44:14 UTC from IEEE Xplore.  Restrictions apply.
