---
title: "ASVLB‐Net: A lightweight network for multispectral weed segmentation with NDVI‐guided adaptive fusion"
doi: "10.1002/ps.70881"
extraction_engine: html2md (BeautifulSoup from PMC HTML)
source: PMC HTML scrape
---

# ASVLB‐Net: A lightweight network for multispectral weed segmentation with NDVI‐guided adaptive fusion
### Zhengtong Dong
### Zhenhua Mu
### Jie Ji
### Chuanming Song
### Jianjun Wang
### Zumin Wang
Author information
Article notes
Copyright and License information
Correspondence to: C Song, College of Information Engineering, Dalian University, Dalian, 116622, China, E‐mail: songchuanming@dlu.edu.cn ; or J Wang, Mesee Quick Technology (Dalian) Co., Ltd, Dalian, 116620, China. E‐mail: wangjianjun@meseequick.com
Corresponding author.
Revised 2026 Feb 19; Received 2025 Dec 24; Accepted 2026 Apr 17; Issue date 2026 Sep.
## Abstract
### BACKGROUND
Accurate crop‐weed segmentation is critical for precision spraying but is hindered by visual similarity and occlusion. This study aims to develop a lightweight yet high‐accuracy multispectral segmentation network to address these challenges.
### RESULTS
We propose ASVLB‐Net, a novel lightweight multiscale feature extraction network guided by normalized difference vegetation index (NDVI) priors for crop‐weed segmentation in multispectral imagery. First, we design the Adaptive Spectral‐Vegetation Fusion (ASVF) module at the input stage. It achieves adaptive allocation of spectral and spatial features, enhancing the discriminability of vegetation regions. Additionally, we adopt a U‐shaped architecture based on the Layer‐wise Concatenated Multi‐Scale Feature (LCMF) encoder. It efficiently extracts fine‐grained features and boundary information with low computational cost. Finally, we use the Bottleneck ‐SCSA (Spatial and Channel Synergistic Attention) module to capture long‐range dependencies, improving segmentation in overlapping areas. Experimental results demonstrate that ASVLB‐Net achieves a mean intersection over union (mIOU) of 86.5% and a mean precision of 91.89%, outperforming several state‐of‐the‐art (SOTA) models, while maintaining high efficiency with only 0.47 million parameters.
### CONCLUSION
The ASVLB‐Net significantly improves segmentation accuracy and robustness in unmanned aerial vehicle (UAV) multispectral imagery, offering a robust solution for precision weeding applications. © 2026 Society of Chemical Industry.
Keywords: crop and weed segmentation, multispectral imagery, vegetation index, multiscale feature extraction, deep learning
ASVLB‐Net enhances multispectral weed segmentation via NDVI‐guided adaptive fusion. It delivers 86.5% mIoU and 55.5 FPS with only 0.47 M parameters, ensuring robust field application.
## 1. INTRODUCTION
Weeds not only directly affect the normal growth and development of crops by competing for soil nutrients, water and sunlight, 1 , 2 but also may serve as vectors for pests and diseases, 3 thereby posing a serious threat to agricultural production. Hence, it is crucial to develop effective weeding strategies. Currently, chemical control is the primary method for farmland weeding. However, long‐term usage of herbicides inevitably leads to weed resistance and environmental residues, 4 , 5 posing potential hazards to human life and production. By contrast, the unmanned aerial vehicle (UAV) with real‐time algorithms and broad coverage can address the limitations of indiscriminate spraying in traditional chemical control. 6 , 7 It enables effective weeding while preventing herbicide overuse. Nevertheless, existing technologies face challenges in rapidly and accurately distinguishing crops and weeds with varying sizes, morphologies and mutual occlusions from aerial images. Thus, we need to design a technology to achieve crop‐weed segmentation. 8
Owing to their easy acquisition, RGB images have become the earliest and most widely employed data source for weed segmentation, serving as the foundational imagery in weed detection. Traditional machine learning‐based methods distinguish weeds from crops by analyzing manually selected features such as color, texture and shape. For instance, Kazmi et al . 9 integrated a combination of multiple color indices and utilized SVM and KNN classifiers to accomplish the recognition task. Rehman et al . 10 addressed pesticide pollution in wild blueberry fields. They extracted texture features via color co‐occurrence matrices and employed classifiers to enable site‐specific spraying. Although these methods effectively boost weed detection rates, they depend on handcrafted features and have poor real‐time performance. 11 , 12 The emergence of deep learning and convolutional neural networks (CNNs) has eliminated the need for complex handcrafted feature engineering, enabling models to automatically extract data features through iterative training and exhibit higher robustness. 13 You only look once (YOLO) models are commonly used for weed detection. Raza et al . 14 benchmarked YOLO models for cotton crop and weed detection, focusing on the balance of accuracy and efficiency for field edge applications. For precise spraying over weed regions, semantic segmentation is more suitable owing to its pixel‐level discriminability. 15 , 16 For instance, Khan et al . 17 proposed a dual‐module framework realizing accurate aerial farmland segmentation via feature fusion and context aggregation. Lin et al . 18 proposed the FG‐UNet dual‐branch model, which fully exploits a fine‐grained features branch to improve the segmentation performance of small targets in UAV RGB images. Liao et al . 19 developed SCNet, integrating strip convolutions with a UNet backbone. It accurately identifies rice and weeds sharing similar textures and sizes. Besides, to facilitate the real‐time detection capability of the UAV, Gao et al . 20 proposed using ConvNeXt as a backbone and integrating RepVgg to improve the model's inference speed.
Compared to RGB‐only models, multispectral data provide spectral cues that significantly improve the distinction of morphologically similar targets. 21 As shown in Fig. 1 , maize seedlings and gramineous weeds (e.g. barnyard grass) share similar slender leaf shapes, making differentiation via visible light texture difficult. Tang et al . 22 addressed this issue using CGS‐YOLO with multispectral inputs, demonstrating the superiority of spectral features under complex interference. Additionally, the introduction of additional spectral bands (e.g. near‐infrared, red‐edge) significantly expanded the diversity of available vegetation indices (VIs). Early studies utilized VIs such as a normalized difference vegetation index (NDVI) for threshold‐based segmentation, but manual threshold dependency often leads to instability under varying field illumination. 23 With the advancement of deep learning, Thomas et al . 24 utilized NDVI to generate coarse masks for subsequent refinement as a pre‐segmentation assistance. However, fundamental errors in the initial masks often propagated to the final output, limiting overall accuracy. Current trends favor static input‐level fusion. 25 However, Sa et al . 26 observed that stacking NDVI with raw bands yields no performance gain. This suggests that static concatenation suffers from feature redundancy, as NDVI is merely a derivative of Red (R) and Near‐Infrared (NIR) bands. Fixed weights cannot decouple this correlation. In recent years, attention mechanisms have exhibited notable efficacy in agricultural feature fusion. A notable example is the work by Khan et al . 27 which presented an efficient weed‐crop segmentation with a parallel channel‐spatial attention encoder‐decoder. Xu et al . 28 utilized such mechanisms to fuse RGB and depth features, substantially improving weed detection rates. However, existing approaches often lack a dynamic selection mechanism to adaptively determine the relative importance of raw spectral bands versus vegetation indices, as well as their nonlinear interaction, in characterizing specific regions. Therefore, specialized research on the adaptive fusion of spectra and indices remains insufficient. Additionally, standard CNNs face challenges in handling scale variations owing to fixed receptive fields and struggle to model long‐range dependencies in occluded areas. While transformers can address occlusion via self‐attention, their high computational cost poses constraints for deployment on UAV platforms.
### Figure 1.
_[Figure]_: Change in plant cover over the acquisition timeline. Examples from four different dates (25 May, 30 May, 6 June and 15 June) and semantic masks ( maize , amaranth , barnyard grass , quickweed , weed other ).
Change in plant cover over the acquisition timeline. Examples from four different dates (25 May, 30 May, 6 June and 15 June) and semantic masks ( maize , amaranth , barnyard grass , quickweed , weed other ).
Based on prior analysis, we propose a lightweight network, named ASVLB‐Net, guided by NDVI prior knowledge which significantly enhances the efficiency and accuracy of feature extraction. First, we design an Adaptive Spectral‐Vegetation Fusion (ASVF) module to adaptively calculate optimal features of vegetation and spectral information. This utilizes band combinations and mathematical transformations, thereby enabling the differentiation of morphologically similar crops and weeds. Second, a Layer‐wise Concatenated Multi‐Scale Feature (LCMF) module is developed within the encoder. It helps to capture the morphological characteristics of crops and weeds across different growth stages. Finally, the Bottleneck Spatial and Channel Synergistic Attention (Bottleneck‐SCSA) module is designed to enhance long‐range dependencies between pixels.
The main contributions of this paper are as follows:
The ASVF module implements an adaptive selection mechanism to decouple information redundancy. By shifting from passive stacking to active selection, it extracts key discriminative features, significantly enhancing crop‐weed separability.
We develop the LCMF encoder that addresses the limitation of a single receptive field and alleviates shallow spectral feature loss caused by channel reduction. It fuses multiscale features through cascaded convolutions to handle scale variations at low computational cost.
To improve segmentation accuracy in overlapping crop‐weed regions, we design a Bottleneck‐SCSA module to capture long‐range dependencies of features.
The paper is structured into four main sections. Following this introduction, Section 2 elaborates on the proposed ASVLB‐Net methodology, detailing the dataset and algorithmic workflow. Section 3 provides an in‐depth analysis of the experimental results using standard evaluation metrics and visual comparisons. Finally, Section 4 concludes the paper and discusses potential directions for future research.
## 2. MATERIALS AND METHODS
### 2.1. Dataset
We use a publicly available multispectral dataset, WeedsGalore, 29 which was collected at the Marquardt Agricultural Experimental Station in Potsdam, Germany. The data were acquired using a DJI Phantom P4 Multispectral UAV, capturing five spectral bands: Blue (B, 450 ± 16 nm), Green (G, 560 ± 16 nm), R (650 ± 16 nm), Red Edge (Re, 730 ± 16 nm), and NIR (840 ± 26 nm). It was necessary to maintain a flight altitude of 5 m to ensure the clear distinguishability of individual plants. Regarding annotation (Fig. 1 ), it is important to note that different weed species were consolidated into a single category to align with the primary objective of maize–weed segmentation. Consequently, the dataset is classified into three pixel classes: maize, weeds and soil. It contains 2169 maize plants and 10031 weed plants across diverse species.
In order to ensure rigorous evaluation and avoid data leakage, the dataset adopts a native spatially independent training, validation and test split with a ratio of 8:2:2. It comprises 12 distinct field patches, with 8, 2 and 2 patches allocated to the three sets, corresponding to 104, 26 and 26 images respectively. All images are standardized to 512 × 512 pixels. To alleviate overfitting under limited data, we apply multiple data augmentation approaches (random cropping, horizontal flipping, vertical flipping, rotation, random occlusion, horizontal translation and Gaussian noise addition) to the training set, expanding it to 832 images for stable model learning.
### 2.2. The proposed ASVLB‐net architecture
UNet 30 is selected as the foundational architecture as a consequence of its widely recognized efficiency and symmetric encoder‐decoder structure, which has become a standard in precision agriculture. 31 , 32 UNet demonstrates superior performance with limited sample sizes, yet it faces challenges when applied to complex agricultural environments. To this end, we propose an improved architecture based on UNet, named ASVLB‐Net. Figure 2 illustrates the overall structure of this proposed model.
#### Figure 2.
_[Figure]_: ASVLB‐Net overall architecture: a lightweight segmentation network guided by NDVI prior knowledge.
ASVLB‐Net overall architecture: a lightweight segmentation network guided by NDVI prior knowledge.
The specific workflow proceeds as follows. Input feature maps first undergo processing by the ASVF module; this integrates vegetation indices to enhance crop‐weed separability. Next, the LCMF encoder efficiently captures multiscale features and textures. Then, the Bottleneck‐SCSA module models long‐range dependencies at the bottleneck layer, enriching the feature maps with semantic information. Finally, the CMRF decoder fuses features from the encoder and decoder paths, restoring details to generate the output feature map. The following sections will elaborate on the specific design details of these components.
#### 2.2.1. 
ASVF module
In UAV multispectral imagery, the extreme spectral similarity between crops and weeds often leads to category confusion. Existing studies typically adopt a simple concatenation, where VIs are simply concatenated as extra channels. 25 , 26 However, this strategy is mathematically flawed: because NDVI is a nonlinear derivative of R and NIR bands, static stacking introduces severe feature redundancy and lacks the flexibility to adjust to varying field conditions.
In order to bridge this gap, we proposed the ASVF module, a novel architecture for adaptive feature fusion. Unlike generic attention modules (e.g. SE 33 ) that process all input channels uniformly, ASVF is specifically engineered to implement a dynamic selection mechanism between the multispectral branch and the vegetation index branch. As illustrated in Fig. 3 , the core innovation lies in its ability to adaptively allocate importance weights to raw spectral features and vegetation index cues. This mechanism enables the model to actively select the most discriminative information from different branches according to the specific scene context, effectively resolving feature redundancy.
##### Figure 3.
_[Figure]_: ASVF module.
ASVF module.
Specifically, the main branch first employs convolution to perform preliminary encoding on the input multispectral data 𝑋 ∈ ℝ 𝐵 × 𝐶 × 𝐻 × 𝑊 , where B , C , H and W denote the batch size, number of spectral channels, and spatial height and width of the input image, respectively. In this study, the multispectral input contains 𝐶 = 5 channels: B, G, R, Re and NIR. The convolution yields the primary feature map 𝑓 m a i n ∈ ℝ 𝐵 × 3 2 × 𝐻 × 𝑊 . Simultaneously, the auxiliary branch calculates NDVI based on the R and NIR bands:
| N D V I = 𝑁 𝐼 𝑅 − 𝑅 𝑁 𝐼 𝑅 + 𝑅 , N D V I ∈ [ − 1 , 1 ]
| (1)
The index values are normalized from the range [−1, 1] to [0, 1] to accommodate the input range of subsequent activation functions. Convolution is then applied to the NDVI features to extract prior information characterizing the physiological status of the vegetation, yielding a vegetation feature map 𝑓 𝑣 :
| 𝑓 𝑣 = C o n ⁢ v 1 × 1 ⁡ ( N D V I ) , 𝑓 𝑣 ∈ ℝ 𝐵 × 1 6 × 𝐻 × 𝑊
| (2)
Following extraction via distinct branches, it is observed that directly concatenating the main feature map 𝑓 m a i n with the vegetation feature map 𝑓 𝑣 can lead to information conflicts. To mitigate this, we employ a dual attention mechanism during the fusion stage, enabling the model to adaptively select informative features.
First, regarding the channel dimension, we optimized the SE module to suit multispectral imagery. Specifically, it replaces traditional fully connected layers with 1 × 1 convolutions for dimensionality reduction. This strategy preserves spatial topology while ensuring a lightweight computational footprint. Subsequently, a sigmoid function is applied following rectified linear unit (ReLU) activation to generate the channel weight vector 𝑀 𝑐 , The specific formula is shown below:
| 𝑀 𝑐 = 𝜎 ⁡ ( C o n ⁢ v 3 ⁢ 𝛿 ⁡ ( C o n ⁢ v 2 ⁢ G A P ⁡ ( [ 𝑓 m a i n , 𝑓 𝑣 ] ) ) )
| (3)
where GAP denotes global average pooling, 𝛿 indicates the ReLU activation, 𝜎 is the sigmoid function. The fused channel‐weighted features 𝑓 𝑐 are given by:
| 𝑓 𝑐 = [ 𝑓 m a i n , 𝑓 𝑣 ] ⊙ 𝑀 𝑐
| (4)
where ⊙ denotes the element‐wise multiplication operation.
Secondly, a dynamic weighting strategy is adopted in the spatial dimension. Spatial attention maps 𝑀 m a i n 𝑠 and 𝑀 𝑣 𝑠 are produced by applying a 1 × 1 convolution to 𝑓 m a i n and 𝑓 𝑣 , reducing the channel dimension to 1. Subsequently, these maps are integrated via a weighted combination using a learnable parameter α :
| 𝑀 𝑠 = 𝜎 ⁢ ( 𝛼 · 𝑀 m a i n 𝑠 + ( 1 − 𝛼 ) · 𝑀 𝑣 𝑠 )
| (5)
Then, we apply a 1 × 1 convolution for channel compression. Finally, a residual connection ensures training stability:
| 𝑓 o u t = C o n ⁢ v 1 × 1 ⁢ ( 𝑓 𝑐 ⊙ 𝑀 𝑠 ) + 𝑓 m a i n
| (6)
The ASVF module suppresses spectral redundancy via channel re‐calibration and optimizes a spatial parameter to fuse discriminative priors. This adaptive selection mechanism effectively distinguishes visually similar crops and weeds.
#### 2.2.2. 
LCMF module
Significant scale variations exist between maize and weeds across different growth stages. the encoder needs to extract multiscale and fine‐grained features. However, it is challenging for traditional UNet's encoder, which relies on a single receptive field, to capture both large and small targets simultaneously within the same layer. This limitation may lead to missing fine‐grained features.
Recent studies have employed improved encoder architectures to address this challenge. For instance, SCNet 19 employs the parallel multilevel convolution block (PMCB) to enhance multiscale representation. However, such methods typically incur high computational costs. Therefore, we adopt the Cascade Multi‐Receptive Fields (CMRF 34 ) module for lightweight multiscale feature extraction. It integrates lightweight concepts from Ghost 35 and PConv, 36 reducing redundancy via channel compression and parity splitting. By constructing multiscale receptive fields, the CMRF module can capture rich fine‐grained features at low computational cost.
However, the CMRF module reduces the number of intermediate channels during encoding. This leads to the over‐compression of shallow spectral details, hindering the distinction between maize leaves and gramineous weeds. To address this issue, we design the LCMF module, as shown in Fig. 4 .
##### Figure 4.
_[Figure]_: LCMF module.
LCMF module.
Specifically, input features 𝑓 i n ∈ ℝ 𝐶 × 𝐻 × 𝑊 , where C denotes the number of channels and H and W represent the spatial size of the current encoder layer, are first processed by a PWConv‐BN‐GELU block. This block applies a pointwise convolution (PWConv) with batch normalization (BN) and Gaussian error linear unit (GELU) activation. It outputs a compressed feature map 𝑓 ∈ ℝ 𝐶 ′ × 𝐻 × 𝑊 , 𝐶 ′ = 𝐶 4 .
Subsequently, the CMRF module splits the feature map f into odd ( 𝑓 𝑏 ) and even ( 𝑓 m ) channels. 𝑓 𝑏 undergoes linear mapping, whereas 𝑓 m employs cascaded Depthwise Separable Convolution (DWConv) blocks, where DWConv represents depthwise convolution with a convolutional kernel size of 3. To preserve the original feature information, 𝑓 𝑏 and 𝑓 m are fused via element‐wise addition. The CMRF module ultimately concatenates the feature maps generated from each DWConv block along the channel dimension:
| 𝑓 C M R F = C o n c a t ⁡ ( 𝑓 𝑏 ⊕ 𝑓 m , { 𝑓 ( 𝑖 ) 𝑚 } ) , 𝑓 C M R F ∈ ℝ 𝐶 × 𝐻 × 𝑊
| (7)
where 𝑓 ( 𝑖 ) 𝑚 denotes the output features of the i ‐th DWConv module ( i = 4), ‘Concat’ signifies the channel concatenation operation, and ⊕ indicates element‐wise addition.
We efficiently extract multiscale fine‐grained features via the CMRF module, which captures local details of small weeds and the slender structural features of maize leaves. It is noted that the CMRF module employs an additional convolution for post‐concatenation fusion. However, this convolution is unnecessary, as the subsequent encoder layer will perform the information fusion. Therefore, we remove the fusion convolution.
Leveraging UNet's channel expansion, we directly concatenate the original input ( 𝑓 i n ) with the CMRF module's output ( 𝑓 C M R F ) along the channel dimension:
| 𝑓 L C M F = C o n c a t ⁡ ( 𝑓 i n , 𝑓 C M R F ) , 𝑓 L C M F ∈ ℝ 2 ⁢ 𝐶 × 𝐻 × 𝑊
| (8)
The LCMF encoder solves this via a hierarchical multibranch structure combined with layer‐wise concatenation. This design captures multiscale features and, crucially, preserves shallow fine‐grained textures, ensuring the model can simultaneously detect microscale weeds (early stage) and large maize leaves (late stage).
#### 2.2.3. Bottleneck‐SCSA module
Traditional UNet loses global target structure during downsampling. Although it employs local convolutions at the bottleneck to extract high‐level semantics, these operations fail to model long‐range dependencies. Consequently, the UNet model struggles to capture global associations between crops and weeds, making it prone to mis‐segmentation in dense or occluded regions. Studies have utilized attention mechanisms to capture long‐range dependencies. For instance, the Global Attention Mechanism (GAM) module in CGS‐YOLO 22 fuses spatial and channel information to perceive global maize seedling layouts. Although this module enhances feature discrimination under weed interference, it fails to accurately isolate slender maize leaves in high‐coverage weed scenarios.
In order to address this limitation, we draw inspiration from the Spatial and Channel Synergistic Attention (SCSA 37 ) module, which models long‐range dependencies across spatial and channel dimensions. Furthermore, it maintains strong representation capabilities while reducing computation via grouping strategies and progressive compression. However, the number of high‐frequency channel at the bottleneck introduces feature redundancy, making it difficult for the SCSA module to focus on key regions. Therefore, we propose the Bottleneck‐SCSA module, as shown in Fig. 5 . By performing calculations in a compressed semantic space, it reduces the noise of high‐frequency channel at the bottleneck.
##### Figure 5.
_[Figure]_: Bottleneck‐SCSA module.
Bottleneck‐SCSA module.
Specifically, we employ a Conv‐BN‐ReLU block to compress bottleneck features 𝑓 i n ∈ ℝ 2 ⁢ 𝐶 × 𝐻 × 𝑊 , where 2 C denotes the number of channels in the bottleneck layer, with H and W being the spatial height and width of the bottleneck feature map, respectively. This strategy eliminates spectral redundancy, enabling the SCSA module to focus on discriminative crop‐weed features.
| 𝑓 c o n v = 𝛿 ⁡ ( B N ⁡ ( C o n ⁢ v 1 × 1 ⁡ ( 𝑓 i n ) ) ) ∈ ℝ 𝐶 × 𝐻 × 𝑊
| (9)
where C o n ⁢ v 1 × 1 , BN, and δ denote the point‐wise convolution, batch normalization, and ReLU activation, respectively.
Then, the compressed feature map 𝑓 c o n v ∈ ℝ 𝐶 × 𝐻 × 𝑊 is divided into four groups 𝑓 𝑙 , 𝑓 𝑠 , 𝑓 𝑚 , 𝑓 𝐿 ∈ ℝ 𝐶 4 × 𝐻 × 𝑊 along the channel dimension. Each group is processed by DWConv with kernel sizes of 3 × 3, 5 × 5, 7 × 7, and 9 × 9, respectively. The outputs of the four branches are concatenated and passed through a sigmoid activation to obtain the spatial attention weight W . Subsequently, W is combined with the compressed feature map 𝑓 c o n v to yield the spatial attention feature map 𝑆 𝐴 ∈ ℝ 𝐶 × 𝐻 × 𝑊 . Average pooling of SA yields the feature map 𝑌 ∈ ℝ 𝐶 × 𝐻 2 × 𝑊 2 . Next, applying channel‐wise self‐attention to Y produces the channel attention matrix 𝐶 𝐴 ∈ ℝ 𝐶 × 1 × 1 . Finally, feature fusion is performed through element‐wise multiplication:
| 𝑓 𝑆 𝐶 𝑆 𝐴 = ( 𝑊 ⊙ 𝑓 c o n v ) ⊙ 𝐶 𝐴 = ( 𝑆 𝐴 ⊙ 𝐶 𝐴 ) ∈ ℝ 𝐶 × 𝐻 × 𝑊
| (10)
| 𝑓 B o t t l e n e c k − S C S A = 𝛿 ⁡ ( B N ⁡ ( C o n ⁢ v 1 × 1 ⁡ ( 𝑓 S C S A ) ) ) ∈ ℝ 2 ⁢ 𝐶 × 𝐻 × 𝑊
| (11)
where ℝ denotes the element‐wise multiplication, and 𝑓 S C S A (output features of the SCSA module) retains the 𝐶 × 𝐻 × 𝑊 dimension.
Subsequently, a Conv‐BN‐ReLU block is applied to restore the original dimensionality, as shown in Eqn ( 11 ). The Bottleneck‐SCSA module solves this by modeling long‐range spatial dependencies. By capturing global context in a compressed semantic space, it enables the network to infer the complete shape of an object even when it is partially occluded.
## 3. RESULTS AND DISCUSSION
### 3.1. Experimental conditions and evaluation metrics
In order to ensure a fair and rigorous evaluation, we adjusted the input channels of all baseline models from 3 to 5 to support multispectral data. These models were then retrained from scratch using identical dataset splits and hyperparameters, utilizing official source codes to maintain their original architectural integrity. We train the model using the Adam optimizer for 250 epochs with a batch size of 4. We adopt a dynamic learning rate strategy with an initial value of 0.001, which decays gradually during training. We use cross‐entropy loss as the objective function and perform online data augmentation including random rotation, flipping and random jittering to improve the model's generalization and robustness. Table 1 lists the experimental setup, and model selection is based on validation set performance.
#### Table 1.
Experimental environment
| Component
| Parameter
| CPU
| Intel(R) Xeon(R) Platinum 8350C CPU
| GPU
| NVIDIA A10 GPU
| Programming language
| Python 3.11
| Deep learning framework
| PyTorch 2.4.0 Cuda12.1.1
We employ intersection over union (IoU), mean intersection over union (mIoU), Precision, Recall, mean Precision (mPrecision), mean Recall (mRecall), mean F1‐score (mF1), the number of parameters (Params, in M), giga floating point operations per second (GFLOPs), frames per second (FPS), model static memory footprint (MB) and inference memory usage (in MB). These metrics are defined as follows:
| I o U = T P T P + F P + F N
| (12)
| M I o U = 1 𝑛 ⁢ 𝑛 ∑ 𝑖 = 1 I o ⁢ U 𝑖
| (13)
| P r e c i s i o n = T P T P + F P
| (14)
| m P r e c i s i o n = 1 𝑛 ⁢ 𝑛 ∑ 𝑖 = 1 P r e c i s i o n 𝑖
| (15)
| R e c a l l = T P T P + F N
| (16)
| m R e c a l l = 1 𝑛 ⁢ 𝑛 ∑ 𝑖 = 1 R e c a l l 𝑖
| (17)
| m F ⁢ 1 = 1 𝑛 ⁢ 𝑛 ∑ 𝑖 = 1 2 P r e c i s i o n 𝑖 × R e c a l l 𝑖 P r e c i s i o n 𝑖 + R e c a l l 𝑖
| (18)
where TP is the number of true‐positive samples, FP is the number of false‐positive samples, FN is the number of false‐negative samples and TN is the number of true‐negative samples. n denotes the number of categories, where n is equal to 3, representing soil, crop and weed, respectively.
### 3.2. Ablation analysis
#### 3.2.1. Module ablation analysis
We conducted a stepwise ablation study to verify each module's contribution (see Table 2 and Fig. 6 ). In Table 2 , to provide a multidimensional comparison, the selected baselines represent two categories: Classic Baselines standard UNet (Row 1) to evaluate raw segmentation power, and Lightweight Baselines TinyUNet (Row 2) to assess performance under constrained parameter budgets. This dual‐track comparison highlights ASVLB‐Net's ability to maintain high accuracy while minimizing redundancy. TinyUNet is constructed by replacing the encoder and decoder of the baseline UNet with lightweight CMRF modules to reduce computational redundancy. However, owing to its compact design, TinyUNet suffers from the loss of fine‐grained features in shallow layers, leading to missed detections of microscale weeds, as illustrated in Fig. 6(c) . As an improvement for the CMRF architecture, our proposed LCMF encoder module is illustrated in the third row. It increases the mIoU by 3.72% compared to the baseline. By preserving critical fine‐grained features, LCMF significantly improves the capture of scattered small weeds, as evidenced by the white circles in Fig. 6(d) .
##### Table 2.
Experimental results on the test set
| UNet
| CMRF
| LCMF
| ASVF
| Bottleneck‐SCSA
| mIoU (%)
| mPrecision (%)
| mRecall (%)
| mF1 (%)
| Params (M)
| GFLOPs
| √
|
| 81.16
| 89.74
| 88.65
| 89.1
| 7.76
| 55.15
| 83.04
| 89.49
| 91.23
| 90.33
| 0.48
| 6.67
| 84.88
| 90.26
| 92.85
| 91.52
| 0.43
| 8.01
| 84.73
| 91.4
| 91.47
| 91.43
| 7.81
| 67.83
| 84.78
| 91.38
| 91.54
| 91.46
| 7.77
| 85.27
| 91.79
| 91.75
| 91.77
| 0.46
| 16.15
| 84.85
| 89.99
| 93.13
| 91.7
| 0.44
| 85.9
| 92.06
| 92.3
| 92.16
| 7.82
| 86.5
| 91.89
| 93.2
| 92.54
| 0.47
CMRF, Cascade Multi‐Receptive Fields module; LCMF, Layer‐wise Concatenated Multi‐Scale Feature module; ASVF, Adaptive Spectral‐Vegetation Fusion module; Bottleneck‐SCSA, Bottleneck Spatial and Channel Synergistic Attention module; mIoU, mean intersection over union; IoU, intersection over union; mPrecision, mean Precision; mRecall, mean Recall; mF1, mean F1.
##### Figure 6.
_[Figure]_: Visualization results of ablation study for ASVLB‐Net.
Visualization results of ablation study for ASVLB‐Net.
The fourth row of Table 2 integrates the ASVF module to address spectral redundancy, improving mPrecision to 91.40%. When combined with the LCMF encoder (row 6, 85.27% mIoU), it enhances the model's ability to discriminate between morphologically similar maize and weeds [marked by blue circles in Fig. 6(e) ] via adaptive spectral‐vegetation weighting, achieving 91.79% mPrecision. The fifth row adds the Bottleneck‐SCSA module at the bottleneck layer to model long‐range dependencies, raising the mIoU to 84.78%. Subsequent pairwise combinations were chosen to evaluate specific trade‐offs: ASVF + Bottleneck‐SCSA targets maximum precision (92.06%), while LCMF + Bottleneck‐SCSA balances accuracy and performance with a notable mRecall of 93.13%.
The final row of Table 2 represents the complete ASVLB‐Net. As visualized in Fig. 6(f) , the synergy of all modules effectively resolves heavy occlusion (marked by yellow circles) by reconstructing overlapping boundaries. The final model achieves an optimal mIoU of 86.5% and an mF1 of 92.54% with only 0.47 M parameters, striking an excellent balance between precision and efficiency for complex field environments.
#### 3.2.2. Ablation test on fusion strategies and vegetation indices
In order to systematically verify the effectiveness of the ASVF module and determine the optimal vegetation index prior, we conducted comparative experiments using different fusion strategies (static channel concatenation, ASVF) and vegetation indices (NDVI, NDRE, RENDVI). Detailed quantitative results are summarized in Table 3 .
##### Table 3.
Quantitative comparison of fusion strategies, VIs and ASVF performance
| NDVI
| NDRE
| RENDVI
| 85.73
| 91.67
| 92.48
| 92.07
| 85.95
| 91.59
| 92.83
| 92.2
| 86.07
| 92.77
| 92.28
ASVF, Adaptive Spectral‐Vegetation Fusion module; NDVI, normalized difference vegetation index; NDRE, normalized difference Red Edge index; Rendvi, Red Edge normalized difference vegetation index; mIoU, mean intersection over union; IoU, intersection over union; mPrecision, mean Precision; mRecall, mean Recall; mF1, mean F1.
First, with respect to fusion strategies, we compared the proposed adaptive fusion with the static channel concatenation approach, where NDVI is directly stacked as an additional input channel. As shown in Table 3 , the simple concatenation method achieves an mIoU of 85.73%. By contrast, integrating the ASVF module improves the mIoU to 86.5% and raises the mF1 score from 92.07% to 92.54%. This 0.77% mIoU gain confirms that the dynamic weight allocation mechanism in ASVF effectively alleviates feature redundancy caused by direct concatenation. The line chart in Fig. 7 can more intuitively demonstrate the superiority of our proposed method.
##### Figure 7.
_[Figure]_: Comparison of two fusion methods.
Comparison of two fusion methods.
Second, to determine the most effective index, we tested two additional indices within the ASVF framework: normalized difference Red Edge index (NDRE) and Red Edge normalized difference vegetation index (RENDVI). Although all indices contributed positively to segmentation, the NDVI‐based configuration yielded the highest performance (mIoU 86.5%), outperforming RENDVI (86.07%) and NDRE (85.95%). This indicates that NDVI provide the most discriminative physiological features for the current maize–weed segmentation task.
#### 3.2.3. Performance analysis in occluded scenarios
In order to quantitatively evaluate the effectiveness of the proposed Bottleneck‐SCSA module in handling complex occlusion, we constructed a challenging occlusion test subset. This subset consists of 18 images containing 177 maize plants and 1230 weed plants, specifically selected for their high degree of crop‐weed overlap. We evaluated the models (trained on the full training set as described in Section 3.1 ) on this subset, and the results are presented in Table 4 .
##### Table 4.
Performance evaluation under occlusion scenarios
| Model
| ×
| 84.97
| 91.6
| 91.65
| 91.61
| 86.82
| 92.34
| 93.19
| 92.75
× represents the model without the Bottleneck‐SCSA module; √ represents the model with the Bottleneck‐SCSA module; mIoU, mean intersection over union; IoU, intersection over union; mPrecision, mean Precision; mRecall, mean Recall; mF1, mean F1‐score.
As shown in Table 4 , the Bottleneck‐SCSA module significantly boosts performance, achieving 86.82% mIoU (+1.85%) and 92.75% mF1 (+1.14%). Visually, comparing Fig. 6(e) with (f) reveals that the inclusion of the Bottleneck‐SCSA module enables superior boundary separation and discrimination between overlapping leaves and weeds.
### 3.3. Comparison with the baseline UNet
As shown in Fig. 8 , ASVLB‐Net demonstrates rapid convergence compared to the original UNet, attaining peak IoU values much earlier in the training process. Upon stabilization, the proposed model achieves a higher validation mIoU of nearly 88%. Quantitative evaluation on the test set (Table 2 ) further confirms that ASVLB‐Net surpasses UNet across all metrics. Our model achieves 86.5% mIoU on the independent test set. The small performance gap between validation and test sets shows strong generalization and no overfitting.
#### Figure 8.
_[Figure]_: Validation set mIoU per epoch.
Validation set mIoU per epoch.
We used Grad‐CAM to address the black‐box nature of deep learning models. Grad‐CAM visualizes class activation regions, revealing the underlying decision‐making process and enabling an intuitive comparison of attention patterns between ASVLB‐Net and UNet. As shown in Fig. 9 , ASVLB‐Net accurately locates small and scattered weeds, focusing on edge contours and fine textures with clear boundary transitions, thereby improving weed segmentation precision. By contrast, UNet exposes limitations in feature learning. It struggles with small targets and blurred edges, often misclassifying weed regions as crops. Ultimately, the visualization confirms that the LCMF module enhances multiscale characterization, enabling clear delineation of crops and weeds.
#### Figure 9.
_[Figure]_: Visualization of Grad‐CAM activation maps for ASVLB‐Net and UNet.
Visualization of Grad‐CAM activation maps for ASVLB‐Net and UNet.
### 3.4. With other mainstream segmentation models
We conducted segmentation experiments with state‐of‐the‐art models on the crop‐weed dataset, whose segmentation performance is presented in Table 5 . The segmentation results of all models are illustrated in Fig. 10 , achieving a peak mIoU of 86.5%. During early seedling stages, classic architectures frequently miss microscale weeds (marked by white circles in Fig. 10 ) owing to low feature resolution. Conversely, our LCMF encoder preserves fine‐grained textures, enabling precise localization where others fail.
#### Table 5.
Comparison results with the mainstream segmentation models
| IoU (%)
| Precision (%)
| Recall (%)
| mIoU
| Crop
| Weed
| mPrecision
| mRecall
| mF1
| (%)
| UNet 30
| 70.18
| 74.78
| 80.1
| 90.08
| 85
| 81.49
| DeepLab V3+ 38
| 81.51
| 70.9
| 75.36
| 89.71
| 88.74
| 81.02
| 89.44
| 77.91
| 91.51
| 89.35
| AttU‐Net 39
| 82.44
| 72.4
| 76.35
| 90.25
| 81.31
| 90.3
| 89.82
| 86.86
| 83.17
| 89.95
| MFRWF‐CWF 40
| 82.74
| 72.09
| 77.58
| 85.28
| 86.43
| 89.98
| 82.34
| 88.35
| 90.14
| CAFE‐Net 41
| 83.65
| 74.94
| 77.55
| 91.57
| 87.61
| 87.95
| 89.97
| 83.83
| 86.77
| 90.75
| Rolling‐Unet 42
| 82.03
| 74.08
| 73.44
| 89.14
| 83.38
| 85.17
| 85.05
| 89.46
| TinyU‐Net 34
| 72.45
| 78.04
| 87.59
| 86.71
| 87.74
| HCF‐Net 43
| 85.44
| 77.84
| 79.91
| 90.93
| 86.24
| 87.12
| 92.88
| 88.88
| 90.61
| 91.88
| Mobile U‐ViT 44
| 82.48
| 72.18
| 76.79
| 90.64
| 85.79
| 86.96
| 81.98
| 86.78
| ASVLB‐Net (Ours)
| 79.66
| 81.18
| 87.54
| 88.72
| 89.85
| 90.52
mIoU, mean intersection over union; IoU, intersection over union; mPrecision, mean Precision; mRecall, mean Recall; mF1, mean F1.
#### Figure 10.
_[Figure]_: Predictions of different models.
Predictions of different models.
In the late growth stage, heavy occlusion leads to missegmentation in models like HCF‐Net, marked by yellow circles in Fig. 10 . By leveraging the Bottleneck‐SCSA module to capture long‐range dependencies, ASVLB‐Net successfully reconstructs boundaries in dense areas, outperforming HCF‐Net by 1.06% mIoU.
Additionally, the ASVF module adaptively weights multispectral and NDVI features to discriminate visually similar weeds and maize (see blue circles in Fig. 10 ), enhancing mPrecision to 91.89%. This sensitivity is substantiated by the meticulous edge focus in Grad‐CAM maps (Fig. 9 ) and the high diagonal values in the confusion matrix (Fig. 11 ). Ultimately, ASVLB‐Net achieves a superior mF1 of 92.54%, outperforming all baselines and providing a robust solution for complex challenges involving scale, similarity and occlusion.
#### Figure 11.
_[Figure]_: Confusion matrix.
Confusion matrix.
Figure 12 visualizes the trade‐offs between performance and efficiency. Figure 12(a) confirms that ASVLB‐Net achieves state‐of‐the‐art mIoU with minimal parameters (0.47 M) and low computational complexity (16.15 GFLOPs). Crucially, Fig. 12(b) highlights practical metrics including inference speed (FPS) and model static memory footprint. HCF‐Net suffers from low speed (<20 FPS) and TinyU‐Net compromises accuracy, yet ASVLB‐Net strikes the optimal balance. It achieves the highest mF1 score (92.54%) with 55.52 FPS. With a model static memory footprint of 1.8 MB, ASVLB‐Net demonstrates superior practicality compared to existing baselines.
#### Figure 12.
_[Figure]_: Comprehensive comparison of segmentation performance and efficiency. (a) Trade‐off between mIoU and parameters, where bubble color represents GFLOPs. (b) Trade‐off between mF1 and inference speed (FPS), where bubble color represents model static memory footprint.
Comprehensive comparison of segmentation performance and efficiency. (a) Trade‐off between mIoU and parameters, where bubble color represents GFLOPs. (b) Trade‐off between mF1 and inference speed (FPS), where bubble color represents model static memory footprint.
### 3.5. Impact of input resolution
Table 6 indicates that increasing resolution significantly enhances the model's ability to perceive details and improves segmentation performance. Specifically, increasing the input size from 224 × 224 to 640 × 640 improves mIoU by 1.9% owing to capturing finer details, but causes inference memory to surge from 246.84 to 1006.66 MB. Consequently, 512 × 512 is selected as the optimal balance between accuracy and efficiency. This resolution preserves necessary details for 5‐m flight altitudes while maintaining reasonable computational costs. Furthermore, attributed to the LCMF encoder, the model demonstrates robust performance across diverse resolutions that validates its adaptability to varying flight altitudes.
#### Table 6.
Metrics under different input resolutions
| Input size
| FPS
| Inference memory (MB)
| 224 × 224 × 5
| 84.75
| 3.09
| 117.94
| 246.84
| 512 × 512 × 5
| 55.52
| 694.93
| 640 × 640 × 5
| 86.65
| 25.24
| 34.21
| 1006.66
mIoU, mean intersection over union; GFLOPs, giga floating point operations per second; FPS, frames per second.
### 3.6. Supplementary validation of the proposed model's applicability and generalization to other datasets
In order to further verify model generalization and adaptability, we incorporated the WeedMap 45 dataset as supplementary validation. WeedMap is a large‐scale UAV multispectral dataset collected from sugar beet fields in Rhineland‐Palatinate, Germany. It is observed that individual weeds occupy only 5–10 pixels owing to sparse distribution and visual ambiguity. These characteristics pose significant challenges for distinguishing crops from the background, exceeding the difficulty of the WeedsGalore dataset.
We first screened the original samples to remove invalid images containing large black areas, ultimately selecting 300 images (512 × 512) depicting complete agricultural scenes. We extracted the five raw multispectral bands (B, G, R, Re, NIR) to ensure consistency with the input format of WeedsGalore. To align with our proposed method, we recalculated the NDVI channel using the raw R and NIR bands via Eqn ( 1 ). It is important to note that this experiment follows an independent training and testing process, rather than cross‐dataset transfer learning. The model was retrained from scratch on the WeedMap dataset to verify the architectural generalization of ASVLB‐Net across different crop types. Data splitting (training: validation: testing = 7: 1: 2) relied on spatially independent tiles to ensure integrity, with training protocols identical to WeedsGalore (details in Section 3.1 ).
Figure 13 presents the comprehensive benchmark using full metrics. The ASVLB‐Net demonstrates superior generalization with a top‐tier mIoU of 81.5%, outperforming HCF‐Net (77.5%) and classic models such as U‐Net (74.3%). Notably, our model consistently achieves the highest scores across mPrecision, mRecall and mF1, striking an optimal balance between accuracy and completeness where other models fluctuate. These results confirm the architecture's strong adaptability to different crop types and its robustness in large‐scale UAV imagery.
#### Figure 13.
_[Figure]_: Model test performance on WeedMap.
Model test performance on WeedMap.
## 4. CONCLUSION
This study presents ASVLB‐Net, a model designed to improve crop and weed segmentation across various growth stages in multispectral UAV imagery. We designed the ASVF module to address the specific characteristics of multispectral data and the widespread use of the NDVI index. It exploits the complementary value of these inputs by dynamically calculating channel and spatial weights, thereby effectively combining texture and spectral features. Additionally, we incorporated the LCMF encoder. It is tailored to handle scale variations between small weeds and maize seedlings, as well as the small target characteristics typical of UAV images. To address misclassification in occluded regions, we introduced the Bottleneck‐SCSA module. It captures long‐range dependencies across a global scope, enabling detailed modeling of the differences between weeds and the background.
Experiments on public datasets demonstrate that ASVLB‐Net overcomes the limitations of traditional U‐Net regarding occluded and similar targets. It achieves higher segmentation accuracy. Furthermore, we compared Params and GFLOPs against mainstream models. The results reveal that ASVLB‐Net achieves optimal accuracy with fewer parameters.
Future work will focus on variable spraying technology. We plan to deploy ASVLB‐Net on crop protection UAV platforms. This aims to achieve real‐time weed identification and generate precise prescription maps, ultimately supporting efficient and low‐input weed control.
## CONFLICT OF INTEREST
The authors declare no conflict of interest.
## ACKNOWLEDGEMENTS
This research has been funded by the Liaoning Provincial  Key Research and Development Program (Grant No. 2025JH2/102800026), and the Key Science and Technology R&D Program of Dalian (Grant No. 2025YF14GX009).
## Contributor Information
Chuanming Song, Email: songchuanming@dlu.edu.cn.
Jianjun Wang, Email: wangjianjun@meseequick.com.
## DATA AVAILABILITY STATEMENT
The data that support the findings of this study are openly available in github at https://github.com/GFZ/weedsg .
## REFERENCES
1. Hasan ASMM, Sohel F, Diepeveen D, Laga H and Jones MGK, A survey of deep learning techniques for weed detection from images. Comput Electron Agric
184:106067 (2021). [ Google Scholar ]
2. Hashemi‐Beni L, Gebrehiwot A, Karimoddini A, Shahbazi A and Dorbu F, Deep convolutional neural networks for weeds and crops discrimination from UAS imagery. Front Remote Sens
3:755939 (2022). [ Google Scholar ]
3. Su T and Zhang S, Object‐based crop classification in Hetao irrigation zone by using deep learning and region merging optimization. Comput Electron Agric
214:108284 (2023). [ Google Scholar ]
4. Powles S, Global Herbicide Resistance Challenge. Pest Manag Sci
70:1305 (2014). [ DOI ] [ PubMed ] [ Google Scholar ]
5. Li J‐L, Su W‐H, Hu R, Niu L‐T and Wang Q, Smart weeding system with multi‐sensor fusion for tomato plant detection and targeted micro‐spraying of intra‐row weeds. Comput Electron Agric
237:110598 (2025). [ Google Scholar ]
6. Xu B, Fan J, Chao J, Arsenijevic N, Werle R and Zhang Z, Instance segmentation method for weed detection using UAV imagery in soybean fields. Comput Electron Agric
211:107994 (2023). [ Google Scholar ]
7. Cui J, Tan F, Bai N and Fu Y, Improving U‐net network for semantic segmentation of corns and weeds during corn seedling stage in field. Front Plant Sci
15:1344958 (2024). [ DOI ] [ PMC free article ] [ PubMed ] [ Google Scholar ]
8. Liu T, Zhai D, He F and Yu J, Semi‐supervised learning methods for weed detection in turf. Pest Manag Sci
80:2552–2562 (2024). [ DOI ] [ PubMed ] [ Google Scholar ]
9. Kazmi W, Garcia‐Ruiz F, Nielsen J, Rasmussen J and Andersen HJ, Exploiting affine invariant regions and leaf edge shapes for weed detection. Comput Electron Agric
118:290–299 (2015). [ Google Scholar ]
10. Rehman TU, Zaman QU, Chang YK, Schumann AW and Corscadden KW, Development and field evaluation of a machine vision based in‐season weed detection system for wild blueberry. Comput Electron Agric
162:1–13 (2019). [ Google Scholar ]
11. Adhinata FD, Wahyono, and Sumiharto R, a comprehensive survey on weed and crop classification using machine learning and deep learning. Artif Intell Agric
13:45–63 (2024). [ Google Scholar ]
12. Al‐Badri AH, Ismail NA, Al‐Dulaimi K, Salman GA, Khan AR, Al‐Sabaawi A et al ., Classification of weed using machine learning techniques: a review—challenges, current and future potential techniques. J Plant Dis Prot
129:745–768 (2022). [ Google Scholar ]
13. Yang J, Chen Y and Yu J, Convolutional neural network based on the fusion of image classification and segmentation module for weed detection in alfalfa. Pest Manag Sci
80:2751–2760 (2024). [ DOI ] [ PubMed ] [ Google Scholar ]
14. Raza H, Abu Bakr M, Khan SD, Batool H, Ullah H and Ullah M, Benchmarking YOLO models for crop growth and weed detection in cotton fields. AgriEngineering
7:375 (2025). [ Google Scholar ]
15. Imran Moazzam S, Khan US, Qureshi WS, Tiwana MI, Rashid N, Hamza A et al ., Patch‐wise weed coarse segmentation mask from aerial imagery of sesame crop. Comput Electron Agric
203:107458 (2022). [ Google Scholar ]
16. Sivakumar S, Payyappilly AJ, Rajan A, Arumuga Arun R and Rampriya RS, A computer vision‐based crop and weed segmentation using federated ensemble learning in diverse multi‐crop fields. Eng Appl Artif Intel
159:111773 (2025). [ Google Scholar ]
17. Khan SD, Alarabi L and Basalamah S, Segmentation of farmlands in aerial images by deep learning framework with feature fusion and context aggregation modules. Multimed Tools Appl
82:42353–42372 (2023). [ Google Scholar ]
18. Lin J, Zhang X, Qin Y, Yang S, Wen X, Cernava T et al ., FG‐UNet: fine‐grained feature‐guided UNet for segmentation of weeds and crops in UAV images. Pest Manag Sci
81:856–866 (2025). [ DOI ] [ PubMed ] [ Google Scholar ]
19. Liao J, Chen M, Zhang K, Zhou H, Zou Y, Xiong W et al ., SC‐net: a new strip convolutional network model for rice seedling and weed segmentation in paddy field. Comput Electron Agric
220:108862 (2024). [ Google Scholar ]
20. Gao X, Wang G, Zhou Z, Li J, Song K and Qi J, Performance and speed optimization of DLV3‐CRSNet for semantic segmentation of Chinese cabbage (Brassica pekinensis Rupr.) and weeds. Crop Prot
195:107236 (2025). [ Google Scholar ]
21. Pott LP, Amado TJ, Schwalbert RA, Sebem E, Jugulam M and Ciampitti IA, Pre‐planting weed detection based on ground field spectral data. Pest Manag Sci
76:1173–1182 (2020). [ DOI ] [ PubMed ] [ Google Scholar ]
22. Tang B, Zhou J, Zhao C, Pan Y, Lu Y, Liu C et al ., Using UAV‐based multispectral images and CGS‐YOLO algorithm to distinguish maize seeding from weed. Artif Intell Agric
15:162–181 (2025). [ Google Scholar ]
23. Torres‐Sánchez J, López‐Granados F, De Castro AI and Peña‐Barragán JM, Configuration and specifications of an unmanned aerial vehicle (UAV) for early site specific weed management. PLoS One
8:e58210 (2013). [ DOI ] [ PMC free article ] [ PubMed ] [ Google Scholar ]
24. Thomas L‐F, Änäkkälä M and Lajunen A, Weakly supervised perennial weed detection in a barley field. Remote Sens
15:2877 (2023). [ Google Scholar ]
25. Sahin HM, Miftahushudur T, Grieve B and Yin H, Segmentation of weeds and crops using multispectral imaging and CRF‐enhanced U‐net. Comput Electron Agric
211:107956 (2023). [ Google Scholar ]
26. Sa I, Chen Z, Popovic M, Khanna R, Liebisch F, Nieto J et al ., weedNet: dense semantic weed classification using multispectral images and MAV for smart farming. IEEE Robot Autom Lett
3:588–595 (2018). [ Google Scholar ]
27. Khan SD, Basalamah S and Lbath A, Weed–crop segmentation in drone images with a novel encoder–decoder framework enhanced via attention modules. Remote Sens
15:5615 (2023). [ Google Scholar ]
28. Xu K, Xie Q, Zhu Y, Cao W and Ni J, Effective multi‐species weed detection in complex wheat fields using multi‐modal and multi‐view image fusion. Comput Electron Agric
230:109924 (2025). [ Google Scholar ]
29. Celikkan E, Kunzmann T, Yeskaliyev Y, Itzerott S, Klein N and Herold M, WeedsGalore: a multispectral and multitemporal UAV‐based dataset for crop and weed segmentation in agricultural maize fields. arXiv preprint arXiv:2502.13103 (2025).
30. Ronneberger O, Fischer P and Brox T, U‐Net: Convolutional Networks for Biomedical Image Segmentation, in Medical Image Computing and Computer Assisted Intervention–MICCAI 2015. Springer International Publishing, Munich, Germany, pp. 234–241 (2015). [ Google Scholar ]
31. Kailun J, Wenjiang H and Ping H, Dual‐task segmentation of oilseed rape and weeds in agricultural fields: a hybrid approach combining enhanced UNet and unsupervised clustering. Comput Electron Agric
238:110827 (2025). [ Google Scholar ]
32. Zuo Y and Li W, An improved UNet lightweight network for semantic segmentation of weed images in corn fields. CMC
79:4413–4431 (2024). [ Google Scholar ]
33. Hu J, Shen L and Sun G, Squeeze‐and‐Excitation Networks, in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. IEEE, Salt Lake City, UT, pp. 7132–7141 (2018). [ Google Scholar ]
34. Chen J, Chen R, Wang W, Cheng J, Zhang L and Chen L, TinyU‐Net: Lighter Yet Better U‐Net with Cascaded Multi‐Receptive Fields, in Medical Image Computing and Computer Assisted Intervention–MICCAI 2024. Springer International Publishing, Cham,Switzerland, pp. 626–635 (2024). [ Google Scholar ]
35. Han K, Wang Y, Tian Q, Guo J, Xu C and Xu C, GhostNet: More Features from Cheap Operations, in Proceedings of the 2020 IEEE/CVF Conference on Computer Vision and Pattern Recognition. IEEE, Seattle, WA, pp. 1577–1586 (2020). [ Google Scholar ]
36. Chen J, Kao S, He H, Zhuo W, Wen S, Lee C‐H et al ., Run, Don't Walk: Chasing Higher FLOPS for Faster Neural Networks, in Proceedings of the 2023 IEEE/CVF Conference on Computer Vision and Pattern Recognition. IEEE, Vancouver, BC, pp. 12021–12031 (2023). [ Google Scholar ]
37. Si Y, Xu H, Zhu X, Zhang W, Dong Y, Chen Y et al ., SCSA: exploring the synergistic effects between spatial and channel attention. arXiv preprint arXiv:2407.05128 (2024).
38. Chen LC, Zhu Y, Papandreou G, Schroff F and Adam H, Encoder‐Decoder with Atrous Separable Convolution for Semantic Image Segmentation, in Proceedings of the European Conference on Computer Vision (ECCV). Springer International Publishing, Munich, Germany, pp. 801–818 (2018). [ Google Scholar ]
39. Oktay O, Schlemper J, Folgoc LL, Lee M, Heinrich M, Misawa K et al ., Attention U‐net: learning where to look for the pancreas. arXiv preprint arXiv:1804.03999 (2018).
40. Janneh LL, Zhang Y, Cui Z and Yang Y, Multi‐level feature re‐weighted fusion for the semantic segmentation of crops and weeds. J King Saud Univ Sci
35:101545 (2023). [ Google Scholar ]
41. Liu G, Yao S, Liu D, Chang B, Chen Z, Wang J et al ., CAFE‐net: cross‐attention and feature exploration network for polyp segmentation. Expert Syst Appl
238:121754 (2024). [ Google Scholar ]
42. Liu Y, Zhu H, Liu M, Yu H, Chen Z and Gao J, Rolling‐Unet: revitalizing MLP's ability to efficiently extract long‐distance dependencies for medical image segmentation. AAAI
38:3819–3827 (2024). [ Google Scholar ]
43. Xu S, Zheng S, Xu W, Xu R, Wang C, Zhang J et al ., HCF‐net: hierarchical context fusion network for infrared small object detection. arXiv preprint arXiv:2403.10778 (2024).
44. Tang F, Nian B, Ding J, Ma W, Quan Q, Dong C et al ., Mobile U‐ViT: revisiting large kernel and U‐shaped ViT for efficient medical image segmentation. arXiv preprint arXiv:2508.01064 (2025).
45. Sa I, Popović M, Khanna R, Chen Z, Lottes P, Liebisch F et al ., WeedMap: a large‐scale semantic weed mapping framework using aerial multispectral imaging and deep neural network for precision farming. Remote Sens
10:1423 (2018). [ Google Scholar ]
## Associated Data
This section collects any data citations, data availability statements, or supplementary materials included in this article.
### Data Availability Statement

[TABLE]
| N D V I = 𝑁 𝐼 𝑅 − 𝑅 𝑁 𝐼 𝑅 + 𝑅 , N D V I ∈ [ − 1 , 1 ] | (1) |
[END TABLE]

[TABLE]
| 𝑓 𝑣 = C o n ⁢ v 1 × 1 ⁡ ( N D V I ) , 𝑓 𝑣 ∈ ℝ 𝐵 × 1 6 × 𝐻 × 𝑊 | (2) |
[END TABLE]

[TABLE]
| 𝑀 𝑐 = 𝜎 ⁡ ( C o n ⁢ v 3 ⁢ 𝛿 ⁡ ( C o n ⁢ v 2 ⁢ G A P ⁡ ( [ 𝑓 m a i n , 𝑓 𝑣 ] ) ) ) | (3) |
[END TABLE]

[TABLE]
| 𝑓 𝑐 = [ 𝑓 m a i n , 𝑓 𝑣 ] ⊙ 𝑀 𝑐 | (4) |
[END TABLE]

[TABLE]
| 𝑀 𝑠 = 𝜎 ⁢ ( 𝛼 · 𝑀 m a i n 𝑠 + ( 1 − 𝛼 ) · 𝑀 𝑣 𝑠 ) | (5) |
[END TABLE]

[TABLE]
| 𝑓 o u t = C o n ⁢ v 1 × 1 ⁢ ( 𝑓 𝑐 ⊙ 𝑀 𝑠 ) + 𝑓 m a i n | (6) |
[END TABLE]

[TABLE]
| 𝑓 C M R F = C o n c a t ⁡ ( 𝑓 𝑏 ⊕ 𝑓 m , { 𝑓 ( 𝑖 ) 𝑚 } ) , 𝑓 C M R F ∈ ℝ 𝐶 × 𝐻 × 𝑊 | (7) |
[END TABLE]

[TABLE]
| 𝑓 L C M F = C o n c a t ⁡ ( 𝑓 i n , 𝑓 C M R F ) , 𝑓 L C M F ∈ ℝ 2 ⁢ 𝐶 × 𝐻 × 𝑊 | (8) |
[END TABLE]

[TABLE]
| 𝑓 c o n v = 𝛿 ⁡ ( B N ⁡ ( C o n ⁢ v 1 × 1 ⁡ ( 𝑓 i n ) ) ) ∈ ℝ 𝐶 × 𝐻 × 𝑊 | (9) |
[END TABLE]

[TABLE]
| 𝑓 𝑆 𝐶 𝑆 𝐴 = ( 𝑊 ⊙ 𝑓 c o n v ) ⊙ 𝐶 𝐴 = ( 𝑆 𝐴 ⊙ 𝐶 𝐴 ) ∈ ℝ 𝐶 × 𝐻 × 𝑊 | (10) |
[END TABLE]

[TABLE]
| 𝑓 B o t t l e n e c k − S C S A = 𝛿 ⁡ ( B N ⁡ ( C o n ⁢ v 1 × 1 ⁡ ( 𝑓 S C S A ) ) ) ∈ ℝ 2 ⁢ 𝐶 × 𝐻 × 𝑊 | (11) |
[END TABLE]

[TABLE]
| Component | Parameter |
| CPU | Intel(R) Xeon(R) Platinum 8350C CPU |
| GPU | NVIDIA A10 GPU |
| Programming language | Python 3.11 |
| Deep learning framework | PyTorch 2.4.0 Cuda12.1.1 |
[END TABLE]

[TABLE]
| I o U = T P T P + F P + F N | (12) |
[END TABLE]

[TABLE]
| M I o U = 1 𝑛 ⁢ 𝑛 ∑ 𝑖 = 1 I o ⁢ U 𝑖 | (13) |
[END TABLE]

[TABLE]
| P r e c i s i o n = T P T P + F P | (14) |
[END TABLE]

[TABLE]
| m P r e c i s i o n = 1 𝑛 ⁢ 𝑛 ∑ 𝑖 = 1 P r e c i s i o n 𝑖 | (15) |
[END TABLE]

[TABLE]
| R e c a l l = T P T P + F N | (16) |
[END TABLE]

[TABLE]
| m R e c a l l = 1 𝑛 ⁢ 𝑛 ∑ 𝑖 = 1 R e c a l l 𝑖 | (17) |
[END TABLE]

[TABLE]
| m F ⁢ 1 = 1 𝑛 ⁢ 𝑛 ∑ 𝑖 = 1 2 P r e c i s i o n 𝑖 × R e c a l l 𝑖 P r e c i s i o n 𝑖 + R e c a l l 𝑖 | (18) |
[END TABLE]

[TABLE]
| UNet | CMRF | LCMF | ASVF | Bottleneck‐SCSA | mIoU (%) | mPrecision (%) | mRecall (%) | mF1 (%) | Params (M) | GFLOPs |
| √ |  |  |  |  | 81.16 | 89.74 | 88.65 | 89.1 | 7.76 | 55.15 |
|  | √ |  |  |  | 83.04 | 89.49 | 91.23 | 90.33 | 0.48 | 6.67 |
|  |  | √ |  |  | 84.88 | 90.26 | 92.85 | 91.52 | 0.43 | 8.01 |
|  |  |  | √ |  | 84.73 | 91.4 | 91.47 | 91.43 | 7.81 | 67.83 |
|  |  |  |  | √ | 84.78 | 91.38 | 91.54 | 91.46 | 7.77 | 55.15 |
|  |  | √ | √ |  | 85.27 | 91.79 | 91.75 | 91.77 | 0.46 | 16.15 |
|  |  | √ |  | √ | 84.85 | 89.99 | 93.13 | 91.7 | 0.44 | 8.01 |
|  |  |  | √ | √ | 85.9 | 92.06 | 92.3 | 92.16 | 7.82 | 67.83 |
|  |  | √ | √ | √ | 86.5 | 91.89 | 93.2 | 92.54 | 0.47 | 16.15 |
[END TABLE]

[TABLE]
| ASVF | NDVI | NDRE | RENDVI | mIoU (%) | mPrecision (%) | mRecall (%) | mF1 (%) |
|  | √ |  |  | 85.73 | 91.67 | 92.48 | 92.07 |
| √ | √ |  |  | 86.5 | 91.89 | 93.2 | 92.54 |
| √ |  | √ |  | 85.95 | 91.59 | 92.83 | 92.2 |
| √ |  |  | √ | 86.07 | 91.79 | 92.77 | 92.28 |
[END TABLE]

[TABLE]
| Model | mIoU (%) | mPrecision (%) | mRecall (%) | mF1 (%) |
| × | 84.97 | 91.6 | 91.65 | 91.61 |
| √ | 86.82 | 92.34 | 93.19 | 92.75 |
[END TABLE]

[TABLE]
|  |  | IoU (%) |  | Precision (%) |  | Recall (%) |  |
| Model | mIoU | Crop | Weed | mPrecision | Crop | Weed | mRecall | Crop | Weed | mF1 |
|  | (%) |  |  | (%) |  |  | (%) |  |  | (%) |
| UNet 30 | 81.16 | 70.18 | 74.78 | 89.74 | 80.1 | 90.08 | 88.65 | 85 | 81.49 | 89.1 |
| DeepLab V3+ 38 | 81.51 | 70.9 | 75.36 | 89.71 | 88.74 | 81.02 | 89.44 | 77.91 | 91.51 | 89.35 |
| AttU‐Net 39 | 82.44 | 72.4 | 76.35 | 90.25 | 81.31 | 90.3 | 89.82 | 86.86 | 83.17 | 89.95 |
| MFRWF‐CWF 40 | 82.74 | 72.09 | 77.58 | 90.33 | 85.28 | 86.43 | 89.98 | 82.34 | 88.35 | 90.14 |
| CAFE‐Net 41 | 83.65 | 74.94 | 77.55 | 91.57 | 87.61 | 87.95 | 89.97 | 83.83 | 86.77 | 90.75 |
| Rolling‐Unet 42 | 82.03 | 74.08 | 73.44 | 89.14 | 84.73 | 83.38 | 89.82 | 85.17 | 85.05 | 89.46 |
| TinyU‐Net 34 | 83.04 | 72.45 | 78.04 | 89.49 | 81.49 | 87.59 | 91.23 | 86.71 | 87.74 | 90.33 |
| HCF‐Net 43 | 85.44 | 77.84 | 79.91 | 90.93 | 86.24 | 87.12 | 92.88 | 88.88 | 90.61 | 91.88 |
| Mobile U‐ViT 44 | 82.48 | 72.18 | 76.79 | 90.64 | 85.79 | 86.96 | 89.35 | 81.98 | 86.78 | 89.98 |
| ASVLB‐Net (Ours) | 86.5 | 79.66 | 81.18 | 91.89 | 87.54 | 88.72 | 93.2 | 89.85 | 90.52 | 92.54 |
[END TABLE]

[TABLE]
| Input size | mIoU (%) | GFLOPs | FPS | Inference memory (MB) |
| 224 × 224 × 5 | 84.75 | 3.09 | 117.94 | 246.84 |
| 512 × 512 × 5 | 86.5 | 16.15 | 55.52 | 694.93 |
| 640 × 640 × 5 | 86.65 | 25.24 | 34.21 | 1006.66 |
[END TABLE]