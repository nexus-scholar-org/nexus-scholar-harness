---
workspace_id: SCI-000129
doi: 10.1007/s10707-026-00564-4
title: Multispectral image fusion and attention-driven deep learning for precision
  weed segmentation and classification in UAV-based agricultural monitoring
authors:
- family_name: Dhanalakshmi
  given_name: Narra
  orcid: null
- family_name: Padma sree
  given_name: Lam
  orcid: null
- family_name: Mathura
  given_name: Bai B.
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:26:14.585494+00:00'
---

# Multispectral image fusion and attention-driven deep learning for precision weed segmentation and classification in UAV-based agricultural monitoring

GeoInformatica (2026) 30:10 https://doi.org/10.1007/s10707-026-00564-4

RESEARCH

Multispectral image fusion and attention-driven deep  learning for precision weed segmentation and classification  in UAV-based agricultural monitoring

Narra Dhanalakshmi1 · Lam Padma sree1 · Bai B. Mathura2

Received: 25 July 2025 / Revised: 19 November 2025 / Accepted: 19 January 2026 /  Published online: 11 March 2026 © The Author(s), under exclusive licence to Springer Science+Business Media, LLC, part of Springer Nature 2026


## Abstract

Accurate weed segmentation and classification are critical for precision agriculture to re­
duce herbicide usage and enhance crop yield. Traditional approaches like manual scouting 
and simple image processing are inefficient and unreliable in large-scale farming. More­
over, challenges such as visual similarities between crops and weeds, varying lighting 
conditions, soil interference, and motion blur hinder accuracy and robustness of automated 
systems. To address these limitations, this research proposes an innovative deep learn­
ing framework for semantic weed segmentation and classification using UAV-captured 
field images. The proposed model, called Patches Convolution Catkin Sheaf Attention 
Network (PCCSAN)-based Densenet121 U-Net, combines multi-scale patch learning 
with hierarchical attention mechanisms for effective feature extraction and segmentation. 
Sparse Nonnegative Shearlet Feature Decomposition (SNSFD) is employed to enhance 
feature representation under noisy or blurred conditions. Further, the Willow Catkin Opti­
mization (WCO) algorithm is utilized to fine-tune model training and boost performance. 
Experiments are conducted on sorghum weed-crop field imagery, and the framework dem­
onstrates high accuracy and generalization capability. Quantitatively, it achieves 98.9% 
precision, 99.5% recall, 98.76% F1-score, and 96.56% mean IoU, outperforming state-of-
the-art models in both accuracy and boundary delineation. Visual results confirm model’s 
superior segmentation under challenging circumstances. The proposed system offers ro­
bust, scalable solution for real-time weed detection and classification, paving the way for 
its integration into smart agricultural practices and automated field management systems.

Keywords  Segmentation · Classification · Sorghum field · Precision agriculture · Deep  learning · Agricultural monitoring

Extended author information available on the last page of the article


## 1 3

10  Page 2 of 33

GeoInformatica (2026) 30:10


## 1  Introduction

Agriculture is basically transforming to higher efficiency so as to satisfy the mounting  global food demands, even though it is constrained by limited resources like land, water,  and fertilizers [1]. Precision Agriculture (PA) offers a promising solution by embracing a  systems-based approach aimed at pushing farming practices that are low in input, high in  efficiency, and sustainable [2]. It leverages advanced information technologies to automate  field management by integrating data from diverse sources. It applies the latest information  technologies in such a way that field management is automated through data integration  from various sources. This makes it possible for the resource to be supplied only where and  according to the inconsistency of the area in the field. By recognizing soil differences, mois­ ture levels, areas of good crop yield, and the presence of nutrients, pests and diseases [3, 4],  PA gives rise to site-specific management practices that seek to cut down on input, increase  crop output, and at same time, maintain the health of the environment.

Unmanned Aerial Vehicles (UAVs), drones, are an integral part of modern agricultural  practices, enable high-resolution spatial data collection, enhancing precision crop monitor­ ing and resource optimization [5]. Equipped with specialized cameras and intelligent algo­ rithms, UAVs collect detailed data across large areas efficiently [6]. Remote Sensing (RS)  activities rely on both satellites and UAVs to enable high-altitude monitoring of farmland,  an essential feature given the vast scale of many farming operations [7]. UAVs are oper­ ated from a distance and are equipped with range of imaging sensors, such as multispectral  and hyperspectral cameras [8, 9]. The captured images from the air are subsequently ana­ lyzed in order to calculate vegetation indices, thus empowering farmers to keep track of  crops, detect any stress situations, and decide which areas to intervene in and apply the right  interventions.

Deep Learning (DL)-based image processing significantly advanced classification, object  detection, and segmentation tasks. Unlike traditional machine learning, that depends on  manually selected features, DL automatically extracts relevant patterns from large labelled  datasets, improving generalization in complex agricultural analyses. As a result, UAVs  increasingly use DL for agricultural scene recognition, particularly in weed detection from  low-altitude RS images. This approach shown remarkable success, enabling efficient, non- destructive evaluation in various farming stages [10]. The proper management of weeds  is a must in sustainable agriculture since it brings crop and quality production up, and at  same time, it shrinks the need for chemical herbicides. Besides, Artificial Intelligence (AI)- proficient UAV weed detection provides a highly accurate and scalable way, thus improv­ ing the overall environmental sustainability and intervention strategies. Yet, accurate weed  recognition in real farm conditions is still quite challenging due to various factors like high  density of plants, occlusion, and overlap between crops and weeds. Recent research tack­ led these problems in dense canopy situations with the help of convolutional–transformer  models and vegetation index–based soft classification to deal with spectral overlap and field  heterogeneity; however, performance is still affected negatively in cases of severe occlusion  and shadowing [11–13]. Pointed out that the traditional and single-view DL models with a  hard time identifying the mixed vegetation areas, and that advanced multispectral attention- based frameworks are needed, as it provide both spatial precision and the necessary spectral  discrimination even in cases of high-density fields.


## 1 3

Page 3 of 33  10

GeoInformatica (2026) 30:10


### 1.1  Motivation and contribution

Traditional manual weeding methods are exhausting and prolonged, and often impracti­ cal for large-scale farming. Precision weed management strategies are essential to address  these issues, enabling site-specific treatment and minimizing chemical usage. Effective  weed management is a serious constituent of modern agriculture, as weeds significantly  compete with crops for vital resources, leading to severe reductions in yield if not properly  controlled. Traditional chemical herbicide applications are widely used, yet pose long-term  threats, including herbicide resistance, environmental pollution, and increased operational  costs. While organic solutions exist, their high cost and limited scalability make less viable  for extensive farming operations. The visual similarity between crops and weeds, particu­ larly during initial growth stages, makes manual identification inefficient and error-prone.  Advances in remote sensing and UAV technology opened new avenues for large-scale field  monitoring, offering rich spatial and spectral data for detailed analysis. However, extracting  meaningful insights from this data under varying field conditions remains a challenge. This  research is inspired by the need to develop a highly accurate and robust weed segmentation  model that operates effectively in complex field environments. The key contributions of the  research are;

● A novel image fusion strategy is proposed using a U-shaped Multi-scale Attention Fu­ sion Transformer (U-MAFT) that integrates green, red, red-edge, and Near-InfraRed  (NIR) spectral bands captured by UAVs. This fusion enriches both spatial and spectral  details, enhancing the precision of object-level segmentation and addressing the chal­ lenges posed by spectral ambiguity between weeds and crops. 	 ● A unique DL architecture, PCCSAN-based DenseNet121-U-Net, is designed for fine- grained weed segmentation and classification. This hybrid architecture improves feature  learning from fused images, enabling accurate detection of weed species amidst similar  crop structures under complex backgrounds. 	 ● To improve classification performance and reduce computational overhead, a newly  proposed WCO algorithm is introduced. WCO effectively fine-tunes model parameters,  resulting in higher classification precision, reduced time complexity, and improved seg­ mentation accuracy compared to existing methods.

The organization of research is given as, Sect. 2 illustrates prior research with the summari­ zation of merits, demerits, and its research gaps. Section 3 provides proposed methodology  and its process, Sect. 4 illustrates empirical results and comparative analysis, and Sect. 5  concludes with summary of proposed methods with future scope.


## 2  Overview of prior research

Weed identification from UAV imagery drawn considerable attention in recent years, moti­ vating diverse DL architectures that aim to improve detection accuracy under real-world  field variability. Research is broadly categorized into four directions: (i) convolution-based  classification and feature-fusion models, (ii) lightweight and adaptive networks for on-field


## 1 3

10  Page 4 of 33

GeoInformatica (2026) 30:10

deployment, (iii) segmentation-based weed–crop discrimination, and (iv) transformer- driven or hybrid spectral–spatial frameworks.


### 2.1  Convolutional and feature-fusion architectures

Dense convolutional networks have been widely adopted for UAV-based weed mapping  because of their capacity to extract hierarchical spatial features. Ajay et al. [14] introduced  a DenseNet-169-based model for sorghum weed classification, enhanced with Dimensional  Convolutional Feature Fusion (DCFF) and Deformable Multi-Kernel Channel Fusion  (DMKCF) for improved multi-scale feature extraction. Triplet attention refined features,  while Gradient-weighted Class Activation Mapping (Grad-CAM) and Local Interpretable  Model-Agnostic Explanations (LIME) provided interpretability, offering bottomless visions  into the model’s classification decisions. Similarly, Aqil M et al. [15] developed a DL- based stacking ensemble for sorghum seed classification. Conducted across two sites, the  SqueezeNet-Logistic Regression (LR) model with Bayesian tuning achieved 97.8% accu­ racy, demonstrating the potential of compact convolutional ensembles in agricultural con­ texts. Table 1 summarizes the merits and demerits of the existing methods.


### 2.2  Lightweight and adaptive deep networks

To balance accuracy with computational feasibility in UAV deployments, Machidon AL et  al. [16] introduced SqueezeSlimUNet (SSU-Net), an adaptive DL model combining U-Net,  SqueezeNet, and slimmable neural networks. SSU-Net dynamically adjusted network width  to optimize inference speed on edge devices. Madanan M et al. [17] enhanced You-Only- Look-Once version 3 (YOLOv3) using the Reptile Search Algorithm (RSA) for fine-tuning  hyperparameters, implementation of adaptive median and high-boost filtering for detection  that is invariant to lighting changes. These designs underline the possibility of field deploy­ ment along with the accuracy of the results.


### 2.3  Segmentation-based crop–weed discrimination

It is important to attain fine segmentations for individual pixels and regions, since this is  necessary for any accurate delimitation of weed crop-parties. Bhatti MA et al. [18] pre­ sented a Convolution Neural Network (CNN)-U-Net-on pre-processed satellite imagery  with Adam optimization and early-stopping strategies to ensure stability. Singh V et al. [19]  created a tuned Deep Neural Network (DNN) method that took advantage of colour and tex­ ture features to achieve pixel-level detection, specifically in the case of camouflaged weed  plants in sugarcane fields. Sahin HM et al. [20] applied a multispectral U-Net for sunflower  fields, demonstrating temporal generalization from early to late growth stages.

Moazzam SI et al. [21] developed a two-step segmentation framework that first isolated  vegetation and then classified weeds, crops, and soil, while Genze et al. [22] developed a  model combining DeBlurring and Weed Segmentation (DeBlurWeedSeg), a joint de-blur­ ring and segmentation model that improved Dice scores by 13.4%.


## 1 3

Page 5 of 33  10

GeoInformatica (2026) 30:10


> **Table 1  Summary of representative models on weed detection**

> Ref.
Method
Function
Merits
Demerits
 [14]
DenseNet-169 with DCFF and 
DMKCF

Classification Advanced feature fu­ sion, model interpret­ ability, and enhanced  relevant feature  learning.

High computational  complexity and lim­ ited generalization.

[15] SqueezeNet–Logistic Regression  (Stacked Ensemble)

Misclassification  among visu­ ally similar varieties;  lacks temporal data  integration.  [16] SSU-Net Segmentation U-Net backbone  enables effective se­ mantic segmentation.

Classification Optimized hyperpa­ rameter tuning and  diverse DL model  integration.

Limited scalability to  higher-resolution or  large-scale datasets.  [17] Improved YOLOv3 with RSA Object  Detection

Preprocessing  dependence reduces  adaptability across  conditions.  [18] CNN–U-Net Segmentation Stable convergence  via early stopping and  snapshot optimization.

Advanced preprocess­ ing enhances detection  efficiency.

Restricted to satel­ lite images; lacks  UAV-level evalua­ tion and attention  mechanisms.  [19] DNN Classification Effectively addresses  spectral similarity and  camouflage issues.

High-resolution  UAV data requires  greater computation  and storage.  [20] Multispectral U-Net Segmentation Utilizes multi­ spectral data for  improved crop–weed  discrimination.

Performance de­ clines under lighting  variation; limited  generalization.  [21] Two-step Segmentation  Framework

Dependent on high- quality annotations;  may misclassify  dense vegetation.  [22] DeBlurWeedSeg Segmentation Enhances robust­ ness to motion blur  and image quality  variations.

Segmentation Efficient vegetation– crop–weed classifica­ tion with improved  accuracy.

Joint deblurring–seg­ mentation increases  computational load.

[23] RMS-DETR Detection Combines high-level  semantic and low- level spatial features  effectively.

Computationally  demanding; potential  overfitting to specific  conditions.  [24] MPCM + SAVI/MSAVI/MCARI Soft  Classification

Lacks spatial–con­ textual feature learn­ ing and hierarchical  modelling.  [25] YOLOv8 + Grounding  DINO + SAM

Handles spectral  ambiguity and fuzzy  boundaries through  soft classification.

Temporal  Segmentation

Automates temporal  growth segmentation  via transformer-based  annotation.

Limited to single- crop monitoring;  lacks weed-specific  generalization.


## 1 3

10  Page 6 of 33

GeoInformatica (2026) 30:10


### 2.4  Attention-driven and multispectral integration frameworks

Recent advances increasingly focused on attention mechanisms and multispectral feature  integration to enhance weed discrimination under variable field conditions. Guo et al. [23]  presented Rice field Multi-Scale DEtection TRansformer (RMS-DETR), multi-scale fea­ ture enhanced DEtection TRansformer (DETR) which fuses CNN-derived local features  with transformer-based contextual reasoning via partial convolutions, efficiently detecting  small or occluded weeds. Complementary research explores spectral–spatial soft classifica­ tion and automated annotation. Rana S et al. [24] applied Modified Possibilistic C-Means  (MPCM) clustering combined with vegetation indices (SAVI, MSAVI, MCARI) to perform  soft classification over mixed crop–weed regions, effectively addressing spectral overlap  and uncertain boundary zones under heterogeneous field conditions. Rana S et al. [25] inte­ grated YOLOv8, Grounding Detection transformer with Improved deNoising anchor bOxes  (DINO), and Segment Anything Model (SAM) to create multi-date cauliflower growth  masks automatically, indicating the incremental crop monitoring and labeling efficiency  through transformer-based annotation pipelines.

Despite notable progress, the majority of current techniques are still specific to particular  crops or datasets, thus limiting application of these techniques to mixed and dense farms.  The problem of spectral overlap between plants and weeds still requires pixel-level separa­ bility, which is rarely achieved in practice due to the temporal growth variations not being  modelled. Much research focuses on either spectral indices or spatial features, but lacks a  unified approach to spectral–spatial learning. Moreover, transformer-based models improve  precision yet demand high computation and annotation effort. These limitations underscore  the need for a compact multispectral attention framework that is robust to field variability  and density.


## 3  Proposed methodology for precision weed segmentation and

classification

An advanced framework for precision weed segmentation and classification in sorghum  fields using multispectral images captured by UAVs is shown in Fig. 1. Leveraging a DJI  Phantom 3 Pro fortified with a MicaSense RedEdge camera, multispectral data spanning  green, red, red-edge, and NIR bands are fused using U-shaped MAFT to enhance spatial  and spectral detail.

The fused images go through SNSFD to get important features that reveal the differences  in structures, and then a custom DL architecture that merges PCCSAN-based DenseNet121  U-Net is used for accurate segregation of crops and weed species. In order to achieve best  model parameters, improve classification and at same time reduce computation cost, pro­ posed WCO is used. This combined method not only allows for precise weed identification  down to the species level but also makes it possible to apply herbicides only to the affected  areas, thus decreasing the amount of chemicals used, cutting costs, and making farming  more eco-friendly, just like PAs.


## 1 3

Page 7 of 33  10

GeoInformatica (2026) 30:10

Fig. 1  Proposed structure of precision weed segmentation and classification


### 3.1  Data acquisition

The dataset used in this research is entirely author-collected; all UAV flights, multispec­ tral image acquisitions, and ground-truth annotations were conducted exclusively by the  research team, and no publicly available datasets were used.

Data gathering is done using a DJI Phantom 3 Pro UAV with a MicaSense RedEdge  multispectral camera attached, capable of taking photographs of five spectral bands: blue  (440 nm), green (560 nm), red (680 nm), red-edge (750 nm), and NIR (710 nm) [26]. Flights  were directed at an altitude of 2 m AGL and ground speed of 1 m s⁻¹, providing a ground  sampling distance of around 1.2 cm pixel⁻¹. The GNSS built into the UAV guaranteed exact  geotagging and proper positioning of the images taken one after another.

A total of 1,240 multispectral images taken at the research plots of maize and sorghum in  the University of Queensland Gatton Research Farm (27.56° S, 152.34° E). This location red- loamy soil, uniform ridge–furrow spacing, and naturally occurring weed mixtures that are  standard for subtropical agro-ecosystems. It was always a clear and near-solar-noon condi­ tion during the flights, that is the most favorable condition for atmospheric scattering to be at  its least during and atmospheric interference being totally of no effect, hence the dataset still  portrays the variability in canopy structure, weed density, and soil reflectance that is seen in  practical field conditions. The maneuvers were made to have 80% forward overlap and 70%  side overlap each time to provide full exposure and precise mosaicking. The acquired imag­ ery was split into 70% training 868 images, 15% validation 186 images, and 15% testing 186  images subsets using a spatially stratified policy that prevented field overlap between splits.  During training, standard data augmentation techniques, with random rotations (± 20°), hori­ zontal and vertical flipping, spectral channel jittering (± 3%), and random cropping, were  applied to improve generalization across variable illumination and canopy orientations.


## 1 3

10  Page 8 of 33

GeoInformatica (2026) 30:10

The data was classified into three semantic categories, i.e., background, crop, and weed,  through the use of the Computer Vision Annotation Tool (CVAT) annotation tool, by three  expert agronomists. The application of polygons to mark the areas was done according to  the plant canopy, and the undecided areas were solved by group voting. The pixel distribu­ tion of the annotated dataset is composed of about 55% background, 28% crop, and 17%  weed, which is a suitable representation of the minority weed regions. Annotation reliability  was verified on a subset of 150 images, achieving an inter-annotator agreement of κ = 0.87,  confirming consistent labelling quality.

The representative RGB and multispectral samples derived from the acquired imagery  are observed in Fig. 2, shedding light on canopy variability, soil background differences and  spectral diversity. Radiometric calibration was conducted pre- and post every flight through  the MicaSense DLS 2 light sensor and a calibrated reflectance panel, eliminating factors  of illumination differences and sensor drift to provide consistency between flights. RGB  composites are for the sake of interpretability only; nevertheless, the five-band multispectral  data covering NIR and Red-Edge channels were applied to all experiments and model train­ ing. The addition of these bands has resulted in an increase of approximately 4–5% in mean  Intersection-over-Union (IoU) when compared to the input of RGB only, thus pointing out  the importance of vegetation discrimination.


### 3.2  Preprocessing by total wiener variation filter technique

The high-resolution multispectral images obtained from aerial drones usually with different  noise types that negatively impact the performance of any further feature extraction and  segmentation tasks. The uniformity of the light in the images and the low level of noise in  the atmosphere make it possible to use the Total Wiener Variation Filter (TWVF) effectively,  which in turn permits the detection of weeds with great accuracy because of noise reduction  and the spectral detail preservation for fertilization/herbicide application. The Total Varia­ tion (TV) filtering technique is an edge-preserving nonlinear filtering method for image

Fig. 2  Visual representation of field images across different spectral bands


## 1 3

Page 9 of 33  10

GeoInformatica (2026) 30:10

enhancement that causes noise [27]. It does this by decreasing the TV of the image, which  results in a smoothing of the homogeneous areas while the edges remain intact. Considering  a noisy image in Eq. (1).

Im (u, v) = x (u, v) + y (u, v) (1)

where, x (u, v) is clean image and y (u, v) is Gaussian noise ∼M (

0, σ 2) , the objective is  to recover x by minimizing Eq. (2).





√

x2u + x2vdudv + η

ˆ


## 2 ∥x −Im∥2

2

ET V (x) = min



 (2)

Ψ

where xu and xv denote the horizontal and vertical spatial derivatives of image x, respec­ tively; Ψ represents image domain, and Im is observed noisy image. The initial integral  term refers to the total variation regularizer that demands the smoothness of the pieces and,  at the same time, preserves the discontinuities at edges. The second term, weighted by η is  automatically tuned via the Stein’s Unbiased Risk Estimate (SURE) between 0.01 and 0.1,  depending on the estimated noise level, ensuring fidelity to the original noisy image. The  minimization is performed over the discrete gradient domain using finite differences for du and dv.

The Wiener Filter (WF) is employed as a linear denoising technique that aims to mini­ malize the Mean Square Error (MSE) between detected UAV-acquired image and under­ lying clean image [28]. This filtering approach assumes the image degradation model is  composed of an original signal corrupted by additive white Gaussian noise. Mathematically,  the observed image Im (u, v) is represented as convolution of filter function h (u, v) with  the sum of the true signal t (u, v) and the noise component nc (u, v) defined in Eq. (3).

Im (u, v) = h (u, v) * (t (u, v) + nc (u, v)) (3)

The primary objective of WF is to estimate the original signal t (u, v) by minimizing the  measurement error between the ideal and observed signal. Error term is defined in Eq. (4).

Er (u, v) = t (u, v) −t (u, v) (4)

where, t (u, v) is the estimated signal obtained after Wiener filtering. The term Er (u, v) denotes residual error spectrum between original and reconstructed signals. The noise vari­ ance σ 2 required by the WF is estimated using the Median Absolute Deviation (MAD) on  the high-frequency sub-band of a discrete wavelet transform using Eq. (5). The Wiener gain  function is computed in Eq. (6).

σ = MAD

0.6745 (5)

G (u, v) = Sxx (u, v) Sxx (u, v) + σ 2  (6)


## 1 3

10  Page 10 of 33

GeoInformatica (2026) 30:10

where Sxx (u, v) denotes local signal power spectrum. This adaptive formulation enables  the Wiener filter to dynamically adjust its noise reduction power in line with the estimated  noise level of each spectral band, thus achieving solid noise reduction and at same time  preventing any excessive blurring. The WF, by tuning its response according to the local  signal statistics, successfully suppresses noise and gives out the impression of fine spatial  details, a feature that is very important for UAV-based remote sensing of vegetation and  weed boundaries. Nevertheless, the WF technique has the advantage of preserving texture,  but at same time, it does not effectively eliminate high-frequency noise. On the contrary, the  TV denoising method brings about excellent noise suppression and edge preservation, but it  sometimes smoothes too fine structures if used in isolation. To achieve a balanced enhance­ ment, a linear fusion model is introduced that leverages a weighting parameter w, where

w ∈(0, 1), to regulate the contribution of both filters shown in Eq. (7)

Imfuse = w · Wf (Im) + (1 + w) · TV (Im) (7)

where Wf (Im) and TV (Im) represent the outputs of WF and TV denoising applied to  the noisy input image Im, respectively. It was empirically tuned at the band level using a  10-image validation subset, maximizing PSNR for each spectral band. Optimal values were  w = 0.65 for visible RGB bands and w = 0.55 for Red-Edge and NIR bands. This band- wise weighting balances texture preservation with spectral smoothness.


### 3.3  U-shaped multi-scale attention fusion transformer for image fusion

The proposed U-MAFT is designed to dynamically capture both subtle and prominent fea­ tures in multispectral UAV imagery, thus optimizing weed segmentation [29]. The entire  hierarchical encoder-decoder architecture with skip connections and dual-branch Multi- Scale Attention Fusion (MAF) modules at the early encoder stages is shown in Fig. 3. Dur­ ing the encoding process, the spatial resolution is gradually decreased while the feature  dimensionality is increased to capture both local and global contexts. Each encoder stage  consists of patch embedding or merging, followed by either MAF modules or standard  transformer blocks, while decoder stages upsample feature maps and fuse skip connections  to restore spatial details for segmentation outputs.

The MAF block contains two main branches running in parallel: (i) a local branch that  employs window-based multi-head self-attention to obtain very detailed spatial information  and (ii) a global branch, Global Learning with Down-Sampling (GLD), that reduces and  combines features to represent long-distance connections. The output of local and the output  of the other branch are joined together with the use of attention in such a way that local- global feature interactions are further enhanced. Scaled dot-product attention allows every  token to, in a way, be online with the global context that is relevant to it, thus the feature  representation becomes richer. In Table 2, a detailed per-stage configuration of the U-MAFT  is provided that includes patch size, embedding dimension, number of blocks, attention  heads, MLP ratio, and window size.

The encoder design of U-MAFT follows the hierarchical structure of Swin Transformer  [30] and the lightweight decoder principle of SegFormer [31], while integrating dual-branch  MAF modules for enhanced local–global feature coupling. Unlike earlier hybrid approaches  that combine convolutional networks with transformers, often leading to feature mismatch,


## 1 3

Page 11 of 33  10

GeoInformatica (2026) 30:10

Fig. 3  Overview of the proposed U-MAFT architecture showing hierarchical encoder–decoder stages  with MAF modules in the early encoder


> **Table 2  Per-stage configuration of U-MAFT**

> Stage
Input
Patch / Stride
Embed Dim
Blocks
Heads
MLP Ratio
Window Size
Patch Embed
H × W
4 × 4
64
–
–
–
–
Enc-1
H/4 × W/4
–
64
2
2
4
7
Enc-2
H/8 × W/8
2 × 2 Merge
128
2
4
4
7
Enc-3
H/16 × W/16
2 × 2 Merge
256
2
8
4
7
Enc-4
H/32 × W/32
2 × 2 Merge
512
2
8
4
7
Dec-1
H/16 × W/16
Upsample × 2
256
2 Conv
–
–
–
Dec-2
H/8 × W/8
Upsample × 2
128
2 Conv
–
–
–
Head
H × W
–
64
1 Conv
–
–
–

ensure attention compatibility by fully adopting window-based attention within the trans­ former architecture. Given an input Y ∈RH× W × C local accumulation is defined in  Eqs. (8) and (9).

L = LWA (

LN (

Y n−1))

+ Y n−1 (8)

Y n

L = MLP (Y n

L ) + Y n

L  (9)

Y n

where Y n

L is local branch output at nth transformer layer. While local attention excels at  intra-window relationships, it struggles to capture global dependencies. To address this,  GLD branch performs global feature abstraction by downsampling the input features via  a fully connected layer. The input Y ∈RH× W × C is first flattened to YG ∈RC× M,


## 1 3

10  Page 12 of 33

GeoInformatica (2026) 30:10

M = H × W. A linear projection then compresses YG using a scaling ratio P, empiri­ cally set to 0.5 for optimal performance. The downsampled global features are enriched  with positional embeddings via layer-wise bilinear interpolation by Eq. (10).

)

+ FC (

)

G = Pos (

Y n−1

Y n−1

 (10)

Y n

G

G

where Y n

G is the global output at the nth transformer layer, and Pos, FC refers to the  positional encoding operation and the fully connected layer, respectively. Specifically, given  local features YL ∈RC× Mloc and the global features YL ∈RC× Mglo​, the fusion atten­ tion is computed as expressed in Eqs. (11), (12) and (13).

PL = YLW loc

P  (11)

J = YGW glo

J  (12)

UG = YLW glo

U  (13)

where W loc

U global​ are trainable projection matrices. The MAF is then calcu­ lated using scaled dot-product attention defined in Eq. (14).

P , W glo

J , W glo

(PLJT

)

MAF (PL, JG, UG) = softmax

UG (14)

G √

d

This mechanism enables fine-grained local features to dynamically attend to global context,  effectively enriching the representation power of each token within the U-MAFT model.  The U-MAFT fusion operates on a per-frame basis; each multispectral frame captured  by the UAV is independently fused without temporal aggregation. To avoid discontinui­ ties when reconstructing large field mosaics, image tiling with a 32-pixel overlap between  adjacent tiles is employed during fusion. Overlapping regions are blended using Gauss­ ian weighting, which ensures smooth spectral transitions and prevents visible seams at tile  boundaries. This overlap-aware fusion strategy preserves spatial continuity across the entire  scene while maintaining fine local detail within each tile.

3.4  Sparse nonnegative shearlet feature decomposition for feature extraction in  fused multispectral images

The shearlet transform is a highly effective multiscale geometric analysis tool with strong  directional sensitivity and optimal approximation properties for images containing edges  and patterns, or structures in images [32]. It satisfies the parabolic scaling law, ensuring  that fine directional details are preserved illustrated in Fig. 4. Mathematically, for a function

γ ∈K2 (

R2)

, the continuous shearlet system is defined as in Eq. (15), where the affine  composite dilation matrix Nas is given in Eq. (16).

1 2 γ ( N −1

as y −t)

: t ∈R2, Nas ∈Φ  (15)

{γ ast (y)} = |detNas|


## 1 3

Page 13 of 33  10

GeoInformatica (2026) 30:10

Fig. 4  Process of Shearlet transform

(

)

a √as 0 √a

for a > 0, s ∈R, t ∈R2 (16)

Nas =

where, a is a multi-resolution constraint, s is the direction constraint and t is the spatial  location. Equation (15) is equivalent to decomposing into Eq. (17), where, Cs is shear  matrix and Da is parabolic grading matrix defined in Eq. (18). The continuous shearlet  transform of function is defined in Eq. (19).

Nas = CsDa (17)

( 1 s 0 1

( a 0 0 √a

)

)

Cs =

, Da =

 (18)

ShearTm (a, s, t) = ⟨f, γ ast⟩ (19)

To achieve optimal sparse approximation of both geometric and textural components non- subsampled shearlet transform is useful for the fused multispectral image Im ∈RH× W to  produce a set of sub-bands using Eq. (20).

NSST (Im) = {

}K

i=1, dir = 1, . . . Di (20)

Lp, Hpi,dir

where Lp is the low-pass approximation and Hpi,dir is the high-frequency directional  components at scale i and direction dir. After the non-subsampled shearlet transform  decomposition, constructing sparse matrix Z ∈Rm× n by vectorizing the shearlet sub- bands, representing the structured image features [33].

For any pixel or patch feature y ∈Rm seeking a sparse, nonnegative coefficient vector  χ described in Eq. (21).

y ≈Zχ , subject toχ ≥0 (21)


## 1 3

10  Page 14 of 33

GeoInformatica (2026) 30:10

This problem of finding the sparsest nonnegative solution is originally non-deterministic  polynomial-time hard due to the use of l0-norm by Eq. (22). To obtain a tractable solution,  the nonnegative l1 ​-minimization is used in Eq. (23).

min∥χ ∥0subject toy = Zχ , χ ≥0 (22)

min∥χ ∥1subject toy = Zχ , χ ≥0 (23)

This approach ensures that the learned features are sparse, nonnegative, and interpreta­ ble, making it highly suitable for tasks like segmentation, classification, and recognition.  SNSFD is implemented using a non-subsampled shearlet transform with three decomposi­ tion scales and directional partitions of {8, 8, 16} at successive scales. This configuration  ensures fine directional selectivity for small weed textures while maintaining global field  structures. The resulting low-pass and high-frequency sub-bands are normalized to [0, 1],  and the top-k (k = 20%) high-energy coefficients are retained per band to suppress redun­ dant or noise-induced activations. The sparse coefficient maps from all scales and orienta­ tions are concatenated along channel dimension with fused U-MAFT feature maps, thereby  forming an enriched spatial–spectral tensor input to the segmentation backbone. During the  learning process, these concatenated channels are optimized together within the encoder  of the DenseNet121-U-Net, which gives the network the advantage of multi-scale shearlet  responses for boundary enhancement and vegetation texture discrimination. The proposed  method retains full spatial detail by adding the shearlet coefficient maps as extra channels to  the fused U-MAFT features, while pooled statistical representations summarize each sub- band through mean or variance descriptors only.


### 3.5  Patches convolution catkin sheaf attention network based Densenet121 U-Net

A patch-based convolution is employed as a robust spatial-spectral feature extractor [34].  In contrast to the classic pixel-wise classification methods, this technique uses the spatial  context of every pixel by drawing out local patches, thus elevating the accuracy of clas­ sification and decreasing the confusion that isolated pixel noise causes. Each remote sens­ ing image, structured as a three-dimensional tensor of size U × V × S, where U and V denote spatial dimensions, and S denotes the number of spectral bands, that is partitioned  into overlapping patches. A patch of size 5 × 5 × S is extracted around every valid pixel,  with the centre pixel representing the class label for that patch. This sampling strategy cap­ tures the spatial neighbourhood of each pixel, enhancing the convolutional layers’ ability to  distinguish between weed and crop regions. The proposed structure comprises a sequential  feature extractor with five convolutional stages feeding into a dense classifier with softmax  normalization. All convolutional operations use a stride of 1 with zero-padding to maintain  consistent feature map dimensions, and no pooling layers are used to preserve full spatial  resolution throughout the network.

The Patch-based Convolution and Sheaf Attention Network (SheafAN) are integrated in  a serial processing pathway that precedes the DenseNet121 encoder of the U-Net decoder  shown in Fig. 5. The output feature tensor from the patch-based convolution block is passed  directly into SheafAN for relational refinement, and the resulting attention-enhanced repre­ sentation is then supplied to the DenseNet121 encoder.


## 1 3

Page 15 of 33  10

GeoInformatica (2026) 30:10

Fig. 5  Structure of patches convolution sheaf attention network based Densenet121 U-Net

Each convolutional and feedforward layer utilizes the rectified linear unit function,  ensuring nonlinear representation learning. The softmax layer at the end of the patch-based  convolution block performs feature normalization rather than final classification. Each  patch output Fp ∈RB× p× p× d flattened into a d-dimensional embedding vector. The col­ lection of these patch embeddings forms the node feature matrix E ∈RN× d, where each  node represents a spatial patch. This matrix is used as the input to the SheafAN, which  constructs a sheaf-based graph across neighboring patches. Through attention-weighted  message passing, SheafAN refines these embeddings into which are then reshaped to

Fs ∈RB× H/p× W/p× d supplied to the DenseNet121 encoder. This connection allows  locally learned spectral–spatial features from the patch-based CNN to propagate through  the sheaf topology, enhancing relational context before hierarchical decoding.


### 3.5.1  Sheaf attention network for feature enhancement

SheafAN is inserted after the patch-based convolution encoder and before the DenseNet121  U-Net decoder. For an input of size 512 × 512 × 4 fused multispectral image, patch extrac­ tion yields 32 × 32 spatial tokens (N = 1024 nodes). Each node feature has a dimensionality  of 64. The SheafAN output preserves the same size 1024 × 64 and is reshaped back into a


## 1 3

10  Page 16 of 33

GeoInformatica (2026) 30:10

32 × 32 × 64 feature map before entering the DenseNet121-U-Net decoder. The final seg­ mentation output is 512 × 512 × 3 representing background, crop, and weed classes. Unlike  traditional attention mechanisms that operate over scalar or vector-valued graphs, SheafAN  operates over higher-dimensional sheaves, enabling a richer and more flexible representa­ tion of feature interactions [35]. The sheaf graph is constructed over patch centres using an  8-connected neighbourhood, where each node connects to its adjacent patches in horizontal,  vertical, and diagonal directions. Additionally, multi-scale skip edges link nodes separated  by two patch intervals, ensuring balanced modelling of fine local details and broader spatial  context illustrated in Fig. 6.

A core component of SheafAN is the attention matrix Γ , a row-stochastic matrix, every  entry  Γ nm captures the attention weight among features  yn and  ym using a shared atten­ tion function defined in Eq. (24).

Γ nm = atn (yn, ym) = exp (LeakyReLu (α [wyn∥wym])) ∑

p∈Nnexp (

LeakyReLu (

α [

])) (24)

wyn∥wyp

where, α  is the weight vector and w is a learnable transformation matrix and ∥ denotes  concatenation. To generalize this to d-dimensional sheaves, the Kronecker product is  employed: Γ = Γ ⊗1d, 1d is a d × d matrix of ones. Each edge ( n, m) in the sheaf graph  is associated with an attention coefficient ( Γ nm) and a transport matrix ( Pnm), which align  and propagate features between connected nodes. The transport matrices are parameter­ ized as small learnable linear projections, initialized near orthogonal to maintain numerical  stability. The attention coefficients are row-normalized (softmax) to ensure stable diffusion,  while residual connections, layer normalization, and spectral constraints (| Pnm|≤ 1) are  employed to prevent gradient explosion and over-smoothing during propagation. The trans­

port mappings Pnm are incorporated within the sheaf attention operator Γ (F), enabling

aligned feature propagation across the sheaf graph. The sheaf-based attention mechanism  governs feature diffusion using the partial differential equation defined in Eq. (25).

Fig. 6  Schematic representation of the SheafAN integrated within the proposed weed segmentation  framework


## 1 3

Page 17 of 33  10

GeoInformatica (2026) 30:10

∂ ∂tY (t) =

Γ (F) · hat : Am −I

Y (t) (25)

where ˆ Am is the sheaf adjacency matrix with self-loops, and denotes element-wise multipli­ cation. Discretizing this Eqn. using Euler’s method with a unit time-step leads to Eq. (26).

· hat : Am 

Γ

Y t

Y t+1 =

Y t (26)

To further refine expressive power, learnable weight matrices wt


## 1 ∈Rd× d and

wt

2 ∈Rft× ft+1 are integrated with non-linearity ρ , resulting in the SheafAN layer is  defined in Eq. (27).

· hat : Am 

1 

Γ

Y t

Y t+1 = ρ

2 (27)

Y twt

wt

A residual connection is introduced gt+1 = gt + F (gt, ϕ t), that preserves gradient flow  and prevents over-smoothing across multiple layers. The inclusion of SheafAN in the pro­ posed framework allows the network to act as both a high-pass and low-pass filter, ensuring  that both fine-grained, like weed boundary details, and global contextual features like crop- row consistency are retained.


### 3.5.2  DenseNet121-UNet for weed segmentation

The sheaf-refined feature tensor Fs Fs is then supplied to the DenseNet121 encoder, form­ ing the input to the hierarchical segmentation pipeline. The DenseNet121-U-Net architec­ ture integrates the feature reuse and deep supervision capabilities of DenseNet121 with the  localization strength of the U-Net decoder [36]. The pre-trained DenseNet121, originally  designed for classification, is repurposed as the encoder by removing its fully connected  layers while retaining convolutional and pooling stages to preserve hierarchical features.

The U-Net-based decoder is appended to DenseNet121, consisting of sequential upsam­ pling layers that gradually reconstruct high-resolution spatial details. Skip connections are  employed between each encoder and corresponding decoder layer to bridge low-level spa­ tial features with high-level contextual information, minimizing semantic information loss  during downsampling.

Each decoder block carries out upsampling as the first step and then concatenates with  encoder features followed by a set of convolutional layers with 3 × 3 filters, batch normaliza­ tion, and ReLU activation. The outputs of last decoder layer are forwarded to a 1 × 1 convo­ lution and a sigmoid initiation to produce the accurate segmentation masks. This combined  DenseNet121-U-Net model effectively obtains the global semantics and the excellent weed  limits even in difficult field conditions, resulting in better discriminability, convergence, and  generalization, especially in the case of agricultural data-scarce situations.


## 1 3

10  Page 18 of 33

GeoInformatica (2026) 30:10


### 3.5.3  Willow catkin optimization for hyperparameter tuning

WCO algorithm is used as the sole optimization strategy for updating network weights  and tuning hyperparameters. No gradient-based optimizers such as Adam or SGD were  employed. WCO operates as a population-based evolutionary optimizer, where each candi­ date solution encodes the full set of network weights along with key hyperparameters [37].  During each epoch, the population is updated through the drift-and-adhesion mechanism,  and the fitness of each candidate is evaluated using the validation loss. The best-performing  candidate provides the updated network weights for the next training epoch. This approach  replaces conventional gradient backpropagation with population-driven search, making the  optimizer robust to vanishing gradients and local minima. Additionally, WCO simultane­ ously adapts the learning rate, SheafAN attention coefficients, and patch-extraction param­ eters, eliminating the need for a predefined learning-rate schedule or separate regularization  strategies. Because WCO adaptively adjusts its search behaviour each epoch, no external  learning-rate scheduling is required. The algorithm begins by arbitrarily initializing popula­ tion of particles (solutions) uniformly distributed across the search space using Eq. (28).

yi = rand × (Ub −Lb) + Lb, i = 1,2, . . . M (28)

where, rand is an arbitrary number between [0,1]. yi represents a solution of D. The upper  and lower limits of solution space are UB and LB. In search phase, each particle simulates  a willow catkin drifting in wind, influenced by wind speed  ws and direction  wd. These  are decomposed into Cartesian components defined in Eq. (29). The particle’s position is  updated by Eq. (30)

u = −ws × cos (wd) , v = −ws × sin (wd) (29)

i + p × (v × u) + 2 (−p) (

)

yt+1

i = yt

 (30)

Og −yt

i

where yt

i current position Og is the global best solution, and p controls the exploration-to- exploitation transition using Eq. (31).

p = 2 × e−( t 1000)2 (31)

with t being the current repetition, T maximum number of repetitions. Initially, a  large  p facilitates exploration; as iterations progress, p decreases, shifting the algorithm  toward exploitation. To avoid premature convergence and enhance local search, an adhe­ sion mechanism is introduced. The distance dis = ∥yi −Og∥ determines whether two cat­ kins are likely to stick together. If dis > R random movement enhances exploration, using  Eq. (32).

ws = rand × R, wd = rand × 2π  (32)

If dis ≤R controlled drift toward the global best is activated. Directional weights DW are  computed using Eq. (33). The refined speed and direction are then defined in Eq. (34).


## 1 3

Page 19 of 33  10

GeoInformatica (2026) 30:10

DW = 1 − |Og −yi| ∥yi −Og ∥, G = DW ∑D

 (33)

i=1DW i

 

(∑D

)

ws = ω ×

+ (1 −ω ) × rand × R

i=1Gi |Og −yi|

(

)

8  (34)

+ rand × π

wd = prandcos



yiOg ∥yi∥× ∥Og∥

where, ω ∈[0.4, 0.6] are stochastic parameters ensuring adaptive refinement in the exploi­ tation phase. WCO enhances important factors in the segmentation and classification pipe­ line because its wind-driven adaptive update and adhesion-aware local refinement allow for  effective escape from local optima, improving convergence speed and classification perfor­ mance even in drastically changing agricultural field conditions.


## 4  Empirical evaluation and comparative analysis

An in-depth empirical evaluation of the proposed PCCSAN-based DenseNet121 U-Net  model for weed segmentation and classification.

The experiments were accomplished on a robust hardware and software setup as speci­ fied in Table 3 that summarizes the major experimental parameters. The experiments aim  to evaluate the model’s performance through application of strict training configurations,  validation strategies, and benchmarks for comparison.

To quantitatively assess segmentation and classification performance, standard metrics  were employed: Accuracy (A), Precision (P), Recall (R), F1-score (F1), IoU, Boundary IoU,  and Boundary Dice. The definitions are as follows: Eqs. (35–40).

Accuracy = TP + TN TP + TN + FP + FN  (35)

Precision = TP TP + FP  (36)


> **Table 3  Experimental parameter**

> settings for model training

Parameter Values Framework PyTorch Hardware NVIDIA GeForce RTX 4090 GPU Number of Epochs 100 Optimizer WCO Batch Size 2 Learning Rate 0.0001 Loss Function Cross-entropy Input Image Type Multispectral Image Spectral Bands Used Blue, Green, Red, Red-Edge, NIR Flight Altitude & Speed 2 m, 1 m/s Weight Decay 0.00001 Dropout Rate 0.3 Regularization Validation-loss-based early stopping


## 1 3

10  Page 20 of 33

GeoInformatica (2026) 30:10

Recall = TP TP + FN  (37)

F1 −score = 2 × Precision × Recall

Precision + Recall  (38)

IoU = TP TP + FP + FN  (39)

BoundaryIoU = |Bp ∩Bg| | Bp ∪Bg | , Boundary Dice = 2 |Bp ∩Bg|

|Bp| + |Bg|  (40)

where TP, FP, TN, and FN refer to the terms true positives, false positives, true negatives,  and false negatives, respectively, and Bp and Bg represent predicted and ground-truth  boundary pixels. The metrics mentioned here are combined to measure the pixel-wise accu­ racy, spatial overlap, and boundary preservation, which in turn guarantees a strong evalua­ tion of the segmentation quality under different field conditions that are not the same.


### 4.1  Accuracy and loss curve analysis

The accuracy curves disclose classification performance of proposed model, while loss  curves show stability of learning and the convergence of error. Thus, it assists in evaluating  the strength and the capability to generalize of the model.

Figure 7 illustrates the accuracy of proposed model during training and testing through­ out the 100 epochs. The training accuracy is very good all the time, nearly perfect at the

Fig. 7  Accuracy analysis


## 1 3

Page 21 of 33  10

GeoInformatica (2026) 30:10

end, that the model learned well from training data. On the other hand, testing accuracy is  variable, but it is mostly an upward trend; it stays above 85% for most of the epochs. This  confirms the robustness of PCCSAN with the WCO algorithm in differentiating between  weed and non-weed regions.

Figure 8 shows the loss analysis conducted over 100 epochs for both training and testing  stages of learning model. The model’s learning process across the epochs is presented on  x-axis, while y-axis provides the metric of loss, indicating the size of the prediction errors.  The Training loss, shown in the graph as being quite stable and low, which is a sign of good  learning, while indicating the testing loss is bumpy with infrequent peaks, meaning the  model is having issues with generalization that might come from overfitting or the presence  of noise in the data.


### 4.2  Visual analysis and results of vegetation segmentation and classification

The proposed framework’s effectiveness through the different stages, intensity histogram  analysis, vegetation index segmentation, and multiclass classification, was revealed by an  extensive visual evaluation. Thus, the framework is capable of differentiating among crops  and weeds across lighting and soil variations.

Figure 9 illustrates the intensity histogram of the RB-GB pixel RGB image, where the  distributions of red, green, and blue channels are shown. The near-Gaussian color spread  that encompasses the mid-intensity ranges (100–150) reveals that the lighting and contrast  are balanced, thus making it easier for features to be extracted and accurate weed-crop seg­ mentation to be done.

Fig. 8  Loss analysis curve


## 1 3

10  Page 22 of 33

GeoInformatica (2026) 30:10

Fig. 9  Color spread of Red Green Blue (RGB) image

Figure 10 depicts the procedure of segmentation of vegetation utilizing Normalized Dif­ ference Vegetation Index (NDVI) alongside image processing methods. The first step-pro­ cess mentioned is shown in input image Fig. 10 (a) which depicts a raw RGB aerial view  of a crop field mixed with both crop rows and parts of vegetation. NDVI is calculated as  shown in Fig. 10 (b) to segregate vegetation from non-vegetative areas like soil or shadows.  NDVI is based on the reflection values of the NIR and red channels that are computed using  the formula NDVI = (NIR − RED) / (NIR + RED). The NDVI output has been normalized  to the [0, 1] range instead of the conventional [-1, 1] range. Within this normalized scale,  values closer to 1.0 represent dense and healthy vegetation, while values approaching 0.0  correspond to soil, shadows, or non-vegetative regions, thereby improving class separation.  A segmentation algorithm is implemented in Fig. 10 (c) on the NDVI output to separate the  green patches from the background, thus giving a binary segmented image. The next step  shown in Fig. 10 (d) involves the overlying of the segmented areas on the NDVI map, thus  confirming that the segments detected correspond precisely to the regions of high NDVI.

In Fig. 11, the proposed model’s segmentation performance is visually compared, and  thus, the figure depicts the results of the performance. The input UAV image captured over  a sorghum field in Fig. 11 (a) exhibits the natural field environment comprising crops along  with weed patches. The ground truth mask in Fig. 11 (b), which is manually annotated to  distinguish between background, crops and weeds, is represented. Figure 11 (c) displays the  proposed model’s segmented output, where regions of plants correctly identified are marked  in green, and the background is shown in black. The comparison indicates that the output of  segmentation correlates highly with the ground truth to the extent that model’s capability to  accurately detect and localize vegetation areas is demonstrated, even if challenged by fac­ tors like motion blur and complicated textures of the field.


## 1 3

Page 23 of 33  10

GeoInformatica (2026) 30:10

Fig. 10  Illustration of vegetation segmentation using NDVI

Fig. 11  Visual comparison of input image, ground truth, and predicted segmentation results


## 1 3

10  Page 24 of 33

GeoInformatica (2026) 30:10

Figure 12 shows segmentation results of the recommended model under a multi-class  classification setting, where the classes are crop, weed, and background. Figure  12 (a)  shows the original input image of a plant in a field environment. Figure 12 (b) displays the  corresponding ground truth mask, which has been manually annotated to separate different  classes. Figure 12 (c) presents the output produced by the proposed segmentation frame­ work. The segmentation result in Fig. 12 (c) is color-coded to demonstrate the classification  accuracy: true positives are shown in green, meaning that the classification of crop or weed  areas is correct; false positives are represented in red, indicating that there are parts of the  background or other classes that wrongly classified; and false negatives are shown in blue,  revealing the areas where the model did not identify. The suggested model that combines  SNSFD, DenseNet121-U-Net, and PCCSAN demonstrates extremely high accuracy in dis­ tinguishing between object classes.

The results of the multiclass semantic segmentation performed by the suggested weed  segmentation and classification system in images of the sorghum field are shown in Fig. 13.  Each row consists of a pair of images where the left column displays the original input images  that were taken in different lighting and shadow conditions, while right column shows corre­ sponding segmentation maps produced by model. The output shown visually classifies every  pixel as belonging to one of the three classes: sorghum plants, soil, and shadows. The system  suggested, SNSFD, PCCSAN-based DenseNet121 U-Net, precisely differentiate between  the plants’ fine structures, complex backgrounds, and changes in illumination.

The stepwise method of gathering sorghum-specific vegetation information through  RGB images by applying the suggested framework is shown in Fig. 14. The original RGB  input is depicted in Fig. 14 (a), while Fig. 14 (b) illustrates the VI computed from it which  gives an insight into the plant regions. The output of the classified segmentation is shown  in Fig. 14 (c) with sorghum (green), shadows (black), and soil (brown) being identified.  As a result of this classification, Fig. 14 (d) mutes the VI data linked to sorghum regions  only, toughening feature extraction for subsequent processing tasks, viz., segmentation and  analysis, with no background interference.


### 4.3  Cross-validation performance evaluation

The proposed weed segmentation model was assessed using a five-fold cross-validation  approach based on the UAV imagery from the sorghum fields to check the robustness and  generalization capability of the model.

Fig. 12  Visual Segmentation performance of a proposed model


## 1 3

Page 25 of 33  10

GeoInformatica (2026) 30:10

Fig. 13  Multiclass semantic segmentation of sorghum fields

To rigorously evaluate generalization performance of proposed model, a five-fold cross- validation approach is employed on UAV images of sorghum fields demonstrated in Table 4.  The data is equally divided into five subsets, and every subset is employed once as a test set  while the four remaining subsets are combined to form training set.

By doing so, it is guaranteed that each data point goes through both the processes of  training and validation, thereby allowing more consistent evaluation of the model’s effec­ tiveness. The scores indicate that the model delivers outstanding and reliable performance  throughout all five folds. The proposed method received an average Mean IoU of 96.56%,  which is a high-level indication of precise intersection between predicted and actual weed  segments. Besides that, the model had a Precision of 98.86%, meaning its small number of  false positives reflects its accuracy in identifying weed areas. Meanwhile, Recall reached  99.44%, which signifies that the model almost uncovered every single relevant weed pixel.  The F1 score, the composite measure of precision and recall, was 98.76%, thus showing that  the model was very proficient in both detecting and segmenting the weeds.


### 4.4  Comparative performance analysis

In order to assess usefulness of suggested weed segmentation and classification framework,  a thorough comparison of the performance is carried out with different state-of-the-art DL  models.

Based on evaluation presented in Fig. 15, the proposed weed segmentation and clas­ sification framework shows a marked superiority over current models, with the overall  accuracy of 98.8% being a notable achievement. The integration of high-end components  like SNSFD, PCCSAN-based DenseNet121 U-Net architecture is credited for this higher


## 1 3

10  Page 26 of 33

GeoInformatica (2026) 30:10

Fig. 14  Sorghum segmentation and vegetation index mapping from RGB Imagery


> **Table 4  Five-fold cross-valida­**

> tion performance of the proposed 
model

Fold Mean IoU (%) Precision (%) Recall (%) F1-Score (%) Fold-1 96.41 98.91 99.42 98.72 Fold-2 96.68 98.85 99.56 98.81 Fold-3 96.59 98.92 99.63 98.77 Fold-4 96.73 98.88 99.52 98.76 Fold-5 96.40 98.91 99.49 98.74 CI 96.56 ± 0.13 98.89 ± 0.03 99.52 ± 0.07 98.76 ± 0.03

efficiency. It even surpassed other models, such as ResNet101_v (97.2%), DenseNet-169  (98.56%), and SqueezeNet in terms of robustness, especially when it comes to revealing  slight disparities between crop and weed regions. On the other hand, models such as SSU- Net (90.47%), Tunned-DNN (90.5%), and YoLo-V5 (64.8%) are unable to cope with the  variations of complex backgrounds and dense vegetation patterns, where the proposed  framework resolves these issues successfully with context-aware feature extraction and  hierarchical representation learning. Therefore, the proposed system gets the latest accu­ racy, and thus, it ensures that it is suitable for real-time agricultural field monitoring and  precision farming applications.


## 1 3

Page 27 of 33  10

GeoInformatica (2026) 30:10

Fig. 15  Accuracy comparison with existing methods

The results of comparative performance illustrated in Fig. 16 reveal that the proposed  method is, to a great extent, superior to many existing DL-based models regarding preci­ sion, recall, and F1-score. The model, as displayed, delivers precision of 98.9%, a recall of  99.5%, and an F1-score of 98.76%, which denotes its extraordinary capacity to tell apart  sorghum crops from weeds and soil. On the other hand, other models like SSU-Net and  ResNet50 with notable weaknesses, especially in recall area showing cannot recognize all  relevant instances. Nevertheless, ViT B-16 is the one falling behind with an F1-score of  only 97.1%.

In Table 5, IoU scores for background, crop, and weed classes are compared and evalu­ ated in terms of various segmentation models along with the overall Mean IoU. A proposed  method is the one that demonstrates the best and most accurate segmentation performance;  therefore, it was able to achieve the highest IoU scores of 99.55% for the background, 91.8%  for the crops, and 93.32% for the weeds, leading to a Mean IoU of 96.56%. These outcomes  are of major significance and say better than MESA-Net (Mean IoU: 87.42%), U-net-CRF  (Mean IoU: 88.1%) and the advanced SegFormer architecture as well. The accuracy of  weed segmentation was greatly improved thanks to the newly proposed and highly efficient  approach that involved patch-based convolution encoding, use of SheafAN, DenseNet121  U-Net decoding and the WCO optimization.


### 4.5  Computational complexity analysis

To evaluate efficiency and applicability of proposed model, a computational complexity  analysis was conducted and compared against several state-of-the-art architectures.

The analysis of the computational complexity of proposed model, as shown in Table 6, is  compared with several existing architectures, taking into account the number of parameters


## 1 3

10  Page 28 of 33

GeoInformatica (2026) 30:10

Fig. 16  Performance comparison with other existing methods


> **Table 5  Comparative Analysis of**

> IoU for Semantic Segmentation


## Methods

IoU (%) 
(Bg)

MeanI­ oU  (%) MESA-Net [38] 99.19 84 79.08 87.42 ResNet101-v [39] 97.2 - 90.5 0.939 SegFormer [40] 99.44 82.57 91.77 - U-net-CRF [20] 98.4 90.8 75.3 0.881 Proposed 99.55 91.8 93.32 96.56

IoU (%)  (Crop)

IoU (%)  (Weed)

(in millions) and inference time (in seconds). The proposed model proves to be very effi­ cient, as it only takes 2.1 million parameters, and the inference time is 0.000621 s per image  per instance, which is faster and more compact than all models compared. For example,  MESA-Net and SSU-Net have moderate parameter counts of 6.74 million and 2.5 million,  respectively, but the inference times of 0.002 and 0.24 s are dramatically longer. MaxViT,  with a parameter count of 22.08 million, has the highest inference time of 0.0559 s, which  shows that it with the largest computational burden.

Table 7 shows that adding SNSFD to U-MAFT slightly increases parameters (1.25 to  1.35 M), FLOPs (33 to 36.5 G), model size (14 to 14.8 MB), and inference time (0.50 to  0.52 ms). Modules, like other ones, with a small effect on the cost. Total, the complete base­ line model is very efficient in computation and segmentation to the point that it just takes a  minor overhead for SNSFD to achieve significant performance improvements.

To validate the effectiveness of WCO, we compared it against commonly used gradient- based and evolutionary optimizers under identical training conditions. As shown in Table 8,


## 1 3

Page 29 of 33  10

GeoInformatica (2026) 30:10


> **Table 6  Computational complex­**

> ity comparison


## Methods

Param(M)
Inference Time (s)
MESA-Net [38]
6.74
0.002
Densenet-169 [14]
-
0.000765
SSU-Net [16]
2.5
0.24
MaxViT [41]
22.08
0.0559
Proposed
2.1
0.000621


> **Table 7  Module-wise param­**

> eters, FLOPs, model size, and 
inference time for the proposed 
model

Module / Variant Params  (M)

Infer­ ence  (ms) U-MAFT only 1.25 33 14 0.5 U-MAFT + SNSFD 1.35 36.5 14.8 0.52 Patch-based Convolution 0.3 8.7 3 0.05 DenseNet121 Encoder 0.6 12.2 4.8 0.15 U-Net Decoder 0.25 6.1 2 0.08 SheafAN 0.1 3 0.9 0.04 TWVF 0.01 0.2 0.3 0.05 Proposed 2.1 55.6 18.5 0.62

FLOPs  (G)

Model  Size  (MB)


> **Table 8  Comparison of Different**

> Optimizers on Weed Segmenta­
tion Performance

Optimizer Mean IoU (%) F1-Score (%) Conver­ gence  Epoch SGD [42] 91.85 94.72 92 Adam [42] 94.78 97.21 78 PSO [43] 93.92 96.48 85 ACO [44] 94.10 96.72 82 WCO (Proposed) 96.56 98.76 52

the proposed WCO achieves the highest Mean IoU (96.56%) and F1-score (98.76%), while  also converging significantly faster (52 epochs). Gradient-based optimizers such as Adam  and SGD required more epochs and showed mild instability on multispectral data, whereas  PSO and ACO exhibited slower population-based convergence. These results confirm  that WCO provides superior optimization stability and efficiency for multispectral weed  segmentation.


### 4.6  Ablation study

In order to measure the impact of each part of the suggested segmentation model, an arrange­ ment of ablation experiments was carried out. The experiments methodically assess the  architectural modules, loss functions, and preprocessing techniques and rank them accord­ ing to influence on the performance of both overall and boundary segmentation.

In order to assess the significance of the multispectral data, spectral ablation was per­ formed, and the results are depicted in Table 9. The use of only RGB input leads to a  decrease in the IoU and boundary metrics for both crops and weeds. A basic 1 × 1 learned  spectral mixing increases the performance but is still lower than the complete U-MAFT.


## 1 3

10  Page 30 of 33

GeoInformatica (2026) 30:10


> **Table 9  Spectral input ablation: class-wise metrics**

> Variant
IoU 
(Bg)

Bound­ ary  Dice RGB only 99.1 88 89.2 92.77 96 97 96.5 84.5 85.7 1 × 1 Learned Spec­ tral Mixing

IoU  (Crop)

IoU  (Weed)

mIoU Preci­ sion  (%)

Re­ call  (%)

F1  (%)

Bound­ ary IoU

99.2 90 91.2 96.13 97.5 98 97.8 87 88.3

Full U-MAFT 99.55 91.8 93.3 96.56 98.9 99.5 98.8 91.2 92.4


> **Table 10  Performance ablation of the proposed approach**

> Variant
IoU 
(Bg)

Bound­ ary Dice Proposed (Full) 99.55 91.8 93.32 96.56 98.8 91.2 92.4 U-MAFT only Seg Head 99.2 90.2 90.8 96.07 98 88 89.4 U-MAFT 99.1 90 90.4 95.84 97.8 87.5 88.7 MAF 99.4 90.6 91 96.33 98.2 89 90.3 SNSFD 99.35 90.4 90.7 96.15 97.9 88.5 89.7 PatchConv 99.4 91.4 91.8 96.87 98.5 89.5 90.7 SheafAN 99.35 90.5 90.9 96.25 98 88.7 89.8 Using Standard Attention 99.3 90.4 90.8 96.17 97.9 88.5 89.6 Using Graph Attention 99.32 90.5 91 96.27 98 88.8 89.9 WCO 99.4 90.2 90.6 96.07 97.6 87.8 88.9 TWVF 99.35 90.8 91.2 96.45 98.1 88.5 89.6 Loss: Dice 99.5 91.6 92.8 97.3 98.8 90.8 91.9 Loss: CE + Boundary 99.52 91.7 93 97.4 98.9 91 92.1

IoU  (Crop)

IoU  (Weed)

mIoU F1 (%) Boundary

IoU

Full U-MAFT with the highest class-wise IoU and boundary accuracy, which indicates the  necessity of multi-scale multispectral feature fusion for accurate crop–weed segmentation.

Table 10 shows the effect of every ablation on the performance of the segmentation.  The exclusion of U-MAFT, MAF, SNSFD, PatchConv, or SheafAN lessens the metrics of  mIoU, F1, and boundary, confirming role in the extraction of multi-scale, edge-preserving  features. Modifying the loss function with an impact on performance as well. The applica­ tion of TWVF preprocessing results in an even better boundary accuracy, thereby signifying  its necessity for the segmentation of fine details.


## 5  Conclusion

An advanced weed segmentation and classification model designed for UAV-captured imag­ ery in field conditions. The approach combines the strength of patch-based convolution  encoding, attention-enhanced feature refinement through the sheaf attention mechanism,  and deep hierarchical feature decoding using DenseNet121 U-Net. The optimization pro­ cess is guided by the WCO algorithm, ensuring improved convergence and parameter tun­ ing. Experimental evaluations show that proposed model significantly outperforms existing  architectures in terms of IoU of 93.32, with inference time of 0.000621s, especially in chal­ lenging conditions with shadows, soil noise, and motion blur. The precise separation of crop  and weed regions in multi-class segmentation scenarios validates effectiveness of proposed


## 1 3

Page 31 of 33  10

GeoInformatica (2026) 30:10

method. The current approach depends on a fixed set of spectral bands and may underper­ form when faced with highly similar crop and weed species or while subjected to diverse  environmental conditions. Additionally, the dataset is limited to sorghum fields, restricts the  generalizability of the model across different crops or geographical regions. Future research  will expand dataset to include a wider variety of crop and weed types, incorporate adap­ tive spectral selection mechanisms, and explore lightweight model architectures suitable for  real-time inference on UAVs, further enhancing the applicability of the framework.

Author contributions  Narra Dhanalakshmi: Conceptualization, Methodology, Validation. Lam Padma sree:  Project administration, Supervision, Investigation. Bai B. Mathura: Writing – original draft, Writing – review  & editing.

Funding  This research did not receive any specific grant from funding agencies in the public, commercial,  or not-for-profit sectors.

Data availability  The dataset used in this research is author-collected. Due to field-site restrictions, it cannot  be made publicly available, but it can be shared upon reasonable request to the corresponding author.

Declarations

Ethical approval  All applicable institutional and/or national guidelines for the care and use of animals were  followed.

Informed consent  For this type of analysis formal consent is not needed.

Competing interests  The authors declare no competing interests.


## References

1.	 Parra-López C, Ben Abdallah S, Garcia-Garcia G, Hassoun A, Sánchez-Zamora P, Trollman H, Jagtap  S, Carmona-Torres C (2024) Integrating Digital Technologies in agriculture for climate change adapta­ tion and mitigation: State of the Art and Future Perspectives. Comput Electron Agric 226:109412 2.	 Sabir RM, Mehmood K, Sarwar A et al (2024) Remote sensing and precision agriculture: a sustainable  future. transforming agricultural management for a sustainable future: climate change and machine  learning perspectives 75–103 3.	 Mehedi IM, Hanif MS, Bilal M, Vellingiri MT, Palaniswamy T (2024) Remote Sensing and deci­ sion support system applications in Precision Agriculture: Challenges and Possibilities. IEEE Access  12:44786–44798 4.	 Farid HU, Mustafa B, Khan ZM, Anjum MN, Ahmad I, Mubeen M, Shahzad H (2023) An overview of  precision agricultural technologies for crop yield enhancement and environmental sustainability. Clim  Change Impacts Agric 239–257 5.	 Awais M, Li W, Cheema MJ et al (2022) UAV-based remote sensing in plant stress imagine using high- resolution thermal sensor for Digital Agriculture Practices: A meta-review. Int J Environ Sci Technol  20:1135–1152 6.	 Tahir MN, Lan Y, Zhang Y, Wenjiang H, Wang Y, Syed Muhammad Zaigham Abbas Naqvi (2023)  Application of unmanned aerial vehicles in Precision Agriculture. Precision Agric 55–70 7.	 Dhaked MK, Saryam M, Tomar DS, Bhargava M (2025) Strategies and challenges of remote sensing,  GIS, and IOT Tools for Disease Control operations for future needs of Indian farmers. Smart Agric  143–165 8.	 Barjaktarovic M, Santoni M, Bruzzone L (2024) Design and verification of a low-cost multispec­ tral camera for Precision Agriculture Application. IEEE J Sel Top Appl Earth Observ Remote Sens  17:6945–6957


## 1 3

10  Page 32 of 33

GeoInformatica (2026) 30:10

9.	 Surendran U, Nagakumar KCh, Samuel MP (2024) Remote Sensing in precision agriculture. Digit  Agric 201–223 10.	 Bouguettaya A, Zarzour H, Kechida A, Taberkit AM (2022) Deep learning techniques to classify agri­ cultural crops through UAV imagery: A Review. Neural Comput Appl 34:9511–9536 11.	 Garibaldi-Márquez F, Valentín-Coronado LM, Díaz-Ponce A, Servín-Palestina M, García-Hernández  RV, Ramos-Cantú L (2025) Advances on deep learning for proximal image-based weed recognition and  control under authentic farmlands: a state-of-the-art review. Smart Agric Technol 11:101405 12.	 Garibaldi-Márquez F, Flores G, Valentín-Coronado LM (2025) Leveraging deep semantic segmentation  for assisted weed detection. J Agric Eng 56 13.	 Adamiak M, Będkowski K, Nalej M, Ożadowicz P, Pietruk J, Wójcik S (2026) Bi-temporal change  detection for topographic map updates using panoptic segmentation of VNIR orthophotos and LiDAR  data. GeoInformatica 30:1–41 14.	 Ajay A, Sandosh S, Saji A, Agarwal H (2025) An explainable deep learning framework for sorghum  weed classification using multi-scale feature enhanced DenseNet. IEEE Access 13:26973–26990 15.	 Aqil M, Azrai M, Efendi R et al (2025) Deep learning based stacking ensembles for tropical sorghum  classification. J Agric Food Res 21:101931 16.	 Machidon AL, Krašovec A, Pejović V, Machidon OM (2025) Squeezeslimu-net: An adaptive and effi­ cient segmentation architecture for real-time UAV weed detection. IEEE J Sel Top Appl Earth Observ  Remote Sens 18:5749–5764 17.	 Madanan M, Muthukumaran N, Tiwari S, Vijay A, Saha I (2024) RSA based improved Yolov3 Network  for segmentation and detection of weed species. Multimed Tools Appl 83:34913–34942 18.	 Bhatti MA, Syam MS, Chen H, Hu Y, Keung LW, Zeeshan Z, Ali YA, Sarhan N (2024) Utilizing con­ volutional neural networks (CNN) and U-Net architecture for precise crop and weed segmentation in  agricultural imagery: A deep learning approach. Big Data Res 36:100465 19.	 Singh V, Singh D, Kumar H (2024) Efficient application of deep neural networks for identifying small  and multiple weed patches using drone images. IEEE Access 12:71982–71996 20.	 Sahin HM, Miftahushudur T, Grieve B, Yin H (2023) Segmentation of weeds and crops using multi­ spectral imaging and CRF-enhanced U-net. Comput Electron Agric 211:107956 21.	 Moazzam SI, Khan US, Qureshi WS, Nawaz T, Kunwar F (2023) Towards automated weed detection  through two-stage semantic segmentation of tobacco and weed pixels in aerial imagery. Smart Agric  Technol 4:100142 22.	 Genze N, Wirth M, Schreiner C, Ajekwe R, Grieb M, Grimm DG (2023) Improved weed segmentation  in UAV imagery of sorghum fields with a combined deblurring segmentation model. Plant Methods  19:87 23.	 Guo Z, Cai D, Zhou Y, Xu T, Yu F (2024) Identifying rice field weeds from unmanned aerial vehicle  remote sensing imagery using Deep Learning. Plant Methods 20:105 24.	 Rana S, Gerbino S, Carillo P (2025) Study of spectral overlap and heterogeneity in agriculture based on  soft classification techniques. MethodsX 14:103114 25.	 Rana S, Gerbino S, Akbari Sekehravani E, Russo MB, Carillo P (2024) Crop growth analysis using  automatic annotations and transfer learning in multi-date aerial images and ortho-mosaics. Agronomy  14:2052 26.	 Che’Ya NN, Dunwoody E, Gupta M (2021) Assessment of Weed Classification using hyperspectral  reflectance and optimal multispectral UAV imagery. Agronomy 11:1435 27.	 Beck A, Teboulle M (2009) Fast gradient-based algorithms for constrained total variation image denois­ ing and Deblurring problems. IEEE Trans Image Process 18:2419–2434 28.	 Chen J, Benesty J, Yiteng Huang, Doclo S (2006) New insights into the noise reduction wiener filter.  IEEE Trans Audio Speech Lang Process 14:1218–1234 29.	 Sun H, Wang Y, Wang X, Zhang B, Xin Y, Zhang B, Cao X, Ding E, Han S (2024) Maformer: A Trans­ former network with multi-scale attention fusion for visual recognition. Neurocomput 595:127828 30.	 Pacal I (2024) A novel Swin transformer approach utilizing residual multi-layer perceptron for diagnos­ ing brain tumors in MRI images. Int J Mach Learn Cybern 15:3579–3597 31.	 Elmessery WM, Maklakov DV, El-Messery TM, Baranenko DA, Gutiérrez J, Shams MY, El-Hafeez  TA, Elsayed S, Alhag SK, Moghanm FS, Mulyukin MA (2024) Semantic segmentation of microbial  alterations based on SegFormer. Front Plant Sci 15:1352935 32.	 Khare A, Khare M, Srivastava R (2021) Shearlet transform based technique for image fusion using  median fusion rule. Multimed Tools Appl 80:11491–11522 33.	 He R, Zheng W-S, Hu B-G, Xiang-Wei Kong (2012) Two-stage nonnegative sparse representation for  large-scale face recognition. IEEE Trans Neural Networks Learn Syst 24:35–46 34.	 Sharma A, Liu X, Yang X, Shi D (2017) A patch-based convolutional neural network for Remote Sens­ ing Image Classification. Neural Netw 95:19–28


## 1 3

Page 33 of 33  10

GeoInformatica (2026) 30:10

35.	 Barbero F, Cristian B, de Ocáriz Borde HS, Lio P (2022) Sheaf attention networks. In NeurIPS 2022  Workshop on Symmetry and Geometry in Neural Representations 36.	 Cinar N, Ozcan A, Kaya M (2022) A hybrid DenseNet121-UNET model for Brain tumor segmentation  from Mr Images. Biomed Signal Process Control 76:103647 37.	 Pan JS, Zhang SQ, Chu SC, Yang HM, Yan B (2023) Willow catkin optimization algorithm applied in  the tdoa-fdoa joint location problem. Entropy 25(1):171 38.	 Syed A, Chen B, Abbasi AA, Butt SA, Fang X (2025) MSEA-net: Multi-scale and edge-aware network  for weed segmentation. AgriEng 7:103 39.	 Mesías-Ruiz GA, Borra-Serrano I, Peña JM, de Castro AI, Fernández-Quintanilla C, Dorado J (2024)  Weed species classification with UAV imagery and standard CNN models: Assessing the frontiers of  training and Inference Phases. Crop Protect 182:106721 40.	 Garibaldi-Márquez F, Martínez-Barba DA, Montañez-Franco LE, Flores G, Valentín-Coronado LM  (2025) Enhancing site-specific weed detection using deep learning transformer architectures. Crop Pro­ tect 190:107075 41.	 Li Y, Guo R, Li R et al (2025) An improved U-net and attention mechanism-based model for sugar beet  and weed segmentation. Front Plant Sci 15:1449514 42.	 Yang J, Bagavathiannan M, Wang Y, Chen Y, Yu J (2022) A comparative evaluation of convolutional  neural networks, training image sizes, and deep learning optimizers for weed detection in alfalfa. Weed  Technol 36:512–522 43.	 Kaur G, Bharany S, Elkamchouchi DH, Kim S (2025) Optimized ensemble learning for semantic seg­ mentation of satellite imagery using DeepLabV3 + and UNet with PSO and cross-dataset evaluation.  IEEE Access 44.	 Agarwal S, Dohare AK, Saxena P, Singh J, Singh I, Sahu UK (2025) HDL-ACO hybrid deep learning  and ant colony optimization for ocular optical coherence tomography image classification. Sci Rep  15:5888

Publisher’s note  Springer Nature remains neutral with regard to jurisdictional claims in published maps and  institutional affiliations.

Springer Nature or its licensor (e.g. a society or other partner) holds exclusive rights to this article under a  publishing agreement with the author(s) or other rightsholder(s); author self-archiving of the accepted manu­ script version of this article is solely governed by the terms of such publishing agreement and applicable law.

Authors and Affiliations

Narra Dhanalakshmi1 · Lam Padma sree1 · Bai B. Mathura2

Narra Dhanalakshmi

dhanalakshmi_n@vnrvjiet.in

Lam Padma sree padmasree_l@vnrvjiet.in

Bai B. Mathura mathurabai_b@vnrvjiet.in

1	 Department of Electronics and Communication Engineering, VNR Vignana Jyothi Institute of  Engineering & Technology, Hyderabad 500090, Telangana, India

2	 Department of Information Technology, VNR Vignana Jyothi Institute of Engineering &  Technology, Hyderabad, Telangana 500090, India


## 1 3
