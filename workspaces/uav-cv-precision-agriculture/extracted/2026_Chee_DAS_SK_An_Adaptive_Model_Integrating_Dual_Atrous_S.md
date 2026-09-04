---
workspace_id: SCI-000040
doi: 10.48550/arxiv.2602.08168
title: 'DAS-SK: An Adaptive Model Integrating Dual Atrous Separable and Selective
  Kernel CNN for Agriculture Semantic Segmentation'
authors:
- family_name: Chee
  given_name: Mei Ling
  orcid: null
- family_name: Akilan
  given_name: Thangarajah
  orcid: null
- family_name: Phalke
  given_name: Aparna Ravindra
  orcid: null
- family_name: Keisham
  given_name: Kanchan
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:28:06.658293+00:00'
---

# DAS-SK: An Adaptive Model Integrating Dual Atrous Separable and Selective Kernel CNN for Agriculture Semantic Segmentation

DAS-SK: AN ADAPTIVE MODEL INTEGRATING DUAL ATROUS SEPARABLE AND SELECTIVE KERNEL CNN FOR AGRICULTURE SEMANTIC SEGMENTATION (PREPRINT)1

DAS-SK: An Adaptive Model Integrating Dual Atrous Separable and Selective Kernel CNN for

Agriculture Semantic Segmentation

Mei Ling Chee, Thangarajah Akilan SMIEEE, Aparna Ravindra Phalke IEEE, Kanchan Keisham

[3], [4], [5]. These outputs are critical for applications such as land type identification, weed detection, crop classification, and yield estimation. Nevertheless, agricultural images differ significantly from urban or natural scenes, with challenges including high intra-class variability from crop phenology and management practices, seasonal variability, illumination changes, occlusions, and the heavy computational demands of very high-resolution data [6], [7]. Traditional thresholding and machine learning approaches offered early solutions but were heavily dependent on handcrafted features, limiting their adaptability to diverse conditions [8]. The introduction of deep learning, particularly convolutional neural networks (CNNs), brought major improvements. Architectures such as U-Net [9], DeepLab [10], and SegNet [11] became widely used, demon- strating strong capabilities in capturing spatial structures and delineating object boundaries in agricultural scenes.


## Abstract—Semantic segmentation in high-resolution agricul-

tural imagery demands models that strike a careful balance
between accuracy and computational efficiency to enable de-
ployment in practical systems. In this work, we propose DAS-
SK, a novel lightweight architecture that retrofits selective
kernel convolution (SK-Conv) into the dual atrous separable
convolution (DAS-Conv) module to strengthen multi-scale feature
learning. The model further enhances the atrous spatial pyramid
pooling (ASPP) module, enabling the capture of fine-grained
local structures alongside global contextual information. Built
upon a modified DeepLabV3 framework with two complementary
backbones—MobileNetV3-Large and EfficientNet-B3, the DAS-
SK model mitigates limitations associated with large dataset
requirements, limited spectral generalization, and the high com-
putational cost that typically restricts deployment on UAVs and
other edge devices. Comprehensive experiments across three
benchmarks: LandCover.ai, VDD, and PhenoBench, demonstrate
that DAS-SK consistently achieves state-of-the-art performance,
while being more efficient than CNN-, transformer-, and hybrid-
based competitors. Notably, DAS-SK requires up to 21× fewer
parameters and 19× fewer GFLOPs than top-performing trans-
former models. These findings establish DAS-SK as a robust,
efficient, and scalable solution for real-time agricultural robotics
and high-resolution remote sensing, with strong potential for
broader deployment in other vision domains. Code is available
at https://github.com/irene7c/DAS-SK.git.

arXiv:2602.08168v1  [cs.CV]  9 Feb 2026

More recently, transformer-based models [12], [13] have attracted attention for their ability to model long-range depen- dencies and global context. While these models outperform CNNs in contextual reasoning, their computational complex- ity makes real-time deployment on UAVs and edge devices impractical [1]. Hybrid CNN–Transformer architectures have been proposed to balance local and global feature modeling, but finding an optimal trade-off between accuracy, efficiency, and scalability remains an open challenge [14].

Index Terms—Deep learning, precision agriculture, remote sensing, semantic segmentation.

Many existing models perform well in controlled condi- tions but generalize poorly across diverse agricultural scenes. Furthermore, the high computational cost of state-of-the-art architectures restricts their deployment in precision agriculture systems, which require lightweight, energy-efficient, and real- time solutions [15]. These challenges highlight the need for innovative segmentation models that strike a balance between high accuracy and improved efficiency and adaptability. In this direction, this work delivers a significant contribution by har- nessing the complementary strengths of DAS-Conv and SK- Conv within a dual-stream architecture built on MobileNetV3- Large [16] and EfficientNet-B3 [17]. This design not only boosts segmentation accuracy but also achieves remarkable computational efficiency, paving the way for scalable and real-time semantic segmentation on resource-constrained edge devices. Thus, the main contributions of DAS-SK can be summarized as follows:

I. INTRODUCTION T

HE rapid development of remote sensing technologies has transformed smart agriculture by enabling large- scale and precise monitoring of farmlands. High-resolution imagery from satellites and unmanned aerial vehicles (UAVs) now provides unprecedented opportunities for assessing crop growth, monitoring field health, and supporting precision farming practices. Extracting actionable information from such imagery, however, remains challenging due to the need for accurate interpretation of complex spatial and spectral patterns.

Semantic segmentation has emerged as a powerful solution by providing pixel-level classification that generates fine- grained maps of crop and land cover distributions [1], [2],

ML. Chee is a graduate with the Electrical & Computer Engineering Department of Lakehead University, Thunder Bay, ON, Canada.

T. Akilan is with the Faculty of Software Engineering of Lakehead University, Thunder Bay, ON, Canada.

1) A lightweight segmentation architecture with multi-scale feature representation and adaptive receptive fields for robust crop/non-crop discrimination. 2) Introduction of an efficient context aggregation mech-

AR. Phalke is with the Faculty of Applied Science of the University of Alabama, Huntsville, AL, USA.

K. Keisham is with the School of Computer Science Engineering and Information Systems, Vellore Institute of Technology, Tamil Nadu, India.

DAS-SK: AN ADAPTIVE MODEL INTEGRATING DUAL ATROUS SEPARABLE AND SELECTIVE KERNEL CNN FOR AGRICULTURE SEMANTIC SEGMENTATION (PREPRINT)2

TABLE I A COMPARISON OF KEY SEMANTIC SEGMENTATION RELATED WORKS IN THE AGRICULTURAL FIELD

Model Application Approach Limitations

U-Net MobileVit-S [18] Downy mildew detection in grapevines Transfer learning, data augmentation Small dataset; lighting/symptom variability Residual U-Net (ResNet101) [19]

Corn crop, weed segmentation Transfer learning, data augmentation Large datasets needed; narrow-leaf weeds

confused with soil; high computation DeepLabV3 MobileNetV3 [20]

CNN

Farmland anomaly detection Dual atrous separable convolutions, optimized dilation, skip connections

Limited experimental study on a single dataset

SegFormer (MiT-B0/B3/B5) [21]

Limited dataset diversity; environment-sensitive MiT-B3 [22] Farmland anomaly detection Boundary map fusion in encoder Minor improvement; needs boundary maps SegFormer + MiT-B5 [23] Agricultural aerial image segmentation Adaptive sampling, augmentation

Strawberry disease segmentation Data augmentation, SAM-assisted annotation

Transformer

Small-class pixel imbalance reduces efficiency

invariance

TinySegformer [6] Pest detection on edge devices Sparse attention, pruning Dataset diversity; device resource limits FireViTNet (MobileViT) [24] Wildland fire detection CBAM, Dense ASPP, spatial pooling GPU/memory constraints; fixed resolution CNN–ViT hybrid [25] Crop and weed detection on embedded devices

Hybrid

Encoder-decoder fusion, global-local semantic fusion

Balancing accuracy and efficiency in complex fields

Fig. 1. The overall architecture. The backbones extract multi-scale features from the input, which are then fused and refined via the enhanced ASPP with DAS-SKConv (cf. Fig. 2). The decoder then progressively upsamples and refines the fused features with skip connections to produce accurate segmentation.

framework, the model improves efficiency and generalization, though it still struggles with anomaly classes in complex datasets [20]. Collectively, these studies confirm that CNNs remain the backbone of agricultural semantic segmentation, while trade-offs between efficiency and accuracy persist.

anism that captures both fine local details and global structure without heavy computation. 3) Evaluation on multiple benchmark datasets to demon- strate superior balance between accuracy and efficiency of the proposed model compared to existing approaches. The organization of the rest of the paper is as follows: Section II reviews the relevant literature, providing context for this work. Section III outlines the proposed approach and its novelty. Section IV describes the experimental setup, presents the results, and analyzes the model’s performance. Section V summarizes the findings and offers ideas for future research.

Transformer-based Approaches: Transformers have ad- vanced agricultural vision tasks by capturing long-range de- pendencies and global context. Elmessery et al. [21] showed that MiT-B3/B5 outperform MiT-B0, though performance remains dataset- and condition-sensitive. Shen et al. [22] introduced AAFormer, combining MiT and SE modules with boundary-aware decoding, improving feature extraction but increasing input complexity. Tavera et al. [23] tackled class imbalance using adaptive sampling, which enhanced seg- mentation for major classes but reduced accuracy for rare ones. Despite the strengths, transformers are computationally demanding and data hungry, limiting practical deployment.

II. RELATED WORKS

The key studies in agricultural semantic segmentation can be grouped into three: CNN-based, transformer-based, and hybrid models. Table I summarizes the main details of these studies.

CNN-based Approaches: Semantic segmentation in agri- cultural and remote sensing tasks demands models bal- ancing accuracy and computational efficiency. CNNs re- main practical for UAV and edge deployment due to their lightweight nature and real-time capability [26], [27], [28]. Hern´andez et al. [18] used U-Net with a MobileViT-S en- coder for early vineyard disease detection, achieving strong performance via transfer learning and tailored augmentations. Garibaldi-M´arquez et al. [19] applied a residual U-Net with ResNet backbones for corn–weed segmentation, outperform- ing Mask R-CNN but struggling with thin weed structures in dense canopies. By integrating optimized skip connections and atrous separable convolutions within a DeepLabV3-based

Hybrid Approaches: Some models merge CNNs’ ef- ficiency with transformers’ contextual reasoning [29]. For instance, Zhang et al. [6] proposed TinySegFormer, a sparse-attention framework enabling real-time pest detec- tion. Wang et al. [24] combined MobileViT, CBAM, Dense ASPP, and SP pooling for forest fire detection, achieving strong accuracy but with high memory demands. Meanwhile, Wei et al. [25] developed a lightweight hybrid network for weeding robots, reaching high accuracy, illustrating the po- tential of efficient design.

In short, CNNs remain the practical choice for real-time systems, with low computational cost and adaptability to UAV-

DAS-SK: AN ADAPTIVE MODEL INTEGRATING DUAL ATROUS SEPARABLE AND SELECTIVE KERNEL CNN FOR AGRICULTURE SEMANTIC SEGMENTATION (PREPRINT)3

TABLE II DETAILS OF THE PRIMARY BACKBONE (MOBILENETV3-LARGE)

TABLE III DETAILS OF THE AUXILIARY BACKBONE (EFFICIENTNET-B3)

Input (H×W×C) f(k, s, a) Output (H×W×C)

Input (H×W×C) f(k, l) Output (H×W×C)

512×512×3 Conv(3,2,HardSwish) 256×256×16 256×256×16 Bneck(3,1,ReLU) 256×256×16 [b2] 256×256×16 Bneck(3,2,ReLU) 128×128×24 128×128×24 Bneck(3,1,ReLU) 128×128×24 [b4] 128×128×24 Bneck(5,2,ReLU) 64×64×40 64×64×40 Bneck(5,1,ReLU) 64×64×40 64×64×40 Bneck(5,1,ReLU) 64×64×40 [b7] 64×64×40 Bneck(3,2,HardSwish) 32×32×80 32×32×80 Bneck(3,1,HardSwish) 32×32×80 32×32×80 Bneck(3,1,HardSwish) 32×32×80 32×32×80 Bneck(3,1,HardSwish) 32×32×80 32×32×80 Bneck(3,1,HardSwish) 32×32×112 32×32×112 Bneck(3,1,HardSwish) 32×32×112 32×32×112 Bneck(5,2,HardSwish) 32×32×160 32×32×160 Bneck(5,1,HardSwish) 32×32×160 32×32×160 Bneck(5,1,HardSwish) 32×32×160 32×32×160 Conv(1,1,HardSwish) 32×32×480 [b17]

512 × 512 × 3 Conv(3,1) 256 × 256 × 40 256 × 256 × 40 MBConv1(3,2) 256 × 256 × 24 256 × 256 × 24 MBConv6(3,3) 128 × 128 × 32 [a3] 128 × 128 × 32 MBConv6(5,3) 64 × 64 × 48 [a4] 64 × 64 × 48 MBConv6(3,5) 32 × 32 × 96 32 × 32 × 96 MBConv6(5,5) 32 × 32 × 136 32 × 32 × 136 Conv(1,1) 32 × 32 × 480 [a7]

Total # of trainable parameters: 2.256 M; f(k, l), where f(·) - block type, k - kernel size, l - Number of time this Conv appears in sequence, annotations in the output column refer to the residual block output utilized in the decoder, as illustrated in Fig. 1.

then refined through SK attention. This attention mechanism adaptively reweights channels across multiple receptive fields, enabling dynamic emphasis on the most informative spatial scales. By integrating multiscale spatial sampling with adap- tive channel attention, DAS-SKConv produces context-aware representations that improve both local detail preservation and global consistency in semantic segmentation tasks.

Total # of trainable parameters: 2.894 M; f(k, s, a), where f(·) - block type, k - kernel size, s - stride, a - activation function, and Bneck - bottleneck block, annotations in the output column refer to the residual block output utilized in the decoder, as illustrated in Fig. 1.

based platforms. Transformers show superior global reasoning but require substantial resources, while hybrid models balance both with moderate complexity. Building on these insights, the proposed DAS-SK enhances multi-scale feature representation and adaptability, addressing the persistent trade-off between accuracy and efficiency in agricultural semantic segmentation.

C. Enhanced ASPP module

Fig. 3 depicts the enhanced ASPP. It enriches feature representations by capturing multi-scale contextual informa- tion from high-dimensional backbone features. It employs parallel branches consisting of a 1 × 1 Conv for channel reduction, six DAS-SKConv layers with varying dilation rates {4, 8, 12, 18, 22, 26} for multi-scale receptive fields, and a strip pooling branch to model long-range dependencies along hori- zontal and vertical directions—effective for structured agricul- tural patterns. The outputs are concatenated and compressed via a 1×1 Conv followed by batch normalization, ReLU, and dropout. This design effectively integrates local detail, global structure, and adaptive scale awareness, producing compact yet context-rich features optimized for semantic segmentation.

III. METHODOLOGY

Fig. 1 depicts the proposed model adopting a dual-backbone encoder–decoder architecture composed of 3 key components: dual backbone, an enhanced ASPP module, and a hierarchical decoder network. Their detailed mathematical expressions are presented in the Supplementary Materials.

A. The Dual Backbone

MobileNetV3-Large (cf. Table II) is used as the main back- bone, which consists of a series of convolution (Conv) and inverted residual blocks that progressively reduce the spatial resolution of the input while increasing the number of learned feature maps. The backbone’s early layers focus on low-level details, such as edges and textures, while the deeper layers encode high-level semantic concepts and object boundaries. The auxiliary backbone is a truncated version of EfficientNet- B3, used to extract complementary cues. It is devised by taking the first six blocks of EfficientNet-B3’s layers and then adding a Conv layer to adjust the output channels (cf. Table III).

D. Decoder

The decoder, as shown in Fig. 1, fuses high-level features (a7 and b17) from both backbones into X ∈R960×H×W , which is refined through the Enhanced ASPP module to pro- duce X0 ∈R256×H×W . Two parallel branches—a separable Conv and a standard 3 × 3 Conv—extract complementary spatial information, and their outputs are concatenated, nor- malized, and activated. The refined features are progressively upsampled and fused with corresponding intermediate back- bone outputs (a4, b7, a3, b4, b2) to recover spatial detail through hierarchical skip connections. Each fusion stage is followed by separable Conv, batch normalization, and ReLU activation for feature refinement. Finally, a 1×1 Conv projects the representation into C class channels, and an upsampling operation restores full spatial resolution. Applying Softmax and argmax yields the final pixel-level segmentation map.

B. The DAS-SKConv Module

It is designed to enhance feature extraction by combining DAS convolutions with SK attention, as shown in Fig. 2. The DAS block employs two parallel convolutional paths: a separable atrous branch for efficient channel mixing and a standard atrous branch for spatial context expansion. Their outputs are concatenated to form rich multi-scale features, which are

DAS-SK: AN ADAPTIVE MODEL INTEGRATING DUAL ATROUS SEPARABLE AND SELECTIVE KERNEL CNN FOR AGRICULTURE SEMANTIC SEGMENTATION (PREPRINT)4

Fig. 2. The proposed DAS-SKConv module. The DAS block combines atrous separable and standard atrous convolutions to capture both fine and broad spatial features. The SK attention mechanism adaptively weights multi-branch features through channel-wise attention, producing context-aware representations.

mentation accuracy, efficiency provides a unified assessment that balances predictive performance with computational com- plexity.

mIoU is defined as:

k X

mIoU = 1

Pii Pi· + P·i −Pii

, (1)

k

i=1

where k is the number of classes, Pii is the number of correctly predicted pixels for class i, and Pi· and P·i denote the total true and predicted pixels for class i, respectively.

Hence, the model efficiency is defined as:

D - dilation rates of the

Efficiency = DiffmIoU log(Params) · GFLOPs × 100%, (2)

DAS-SKConv in Fig. 2.

Fig. 3. The enhanced ASPP module. High-dimensional backbone features are processed via parallel branches, including a 1 × 1 Conv, six DAS-SKConv with varying dilation rates, and a strip pooling branch.

where DiffmIoU, Params, and GFLOPs represent the mIoU difference from the baseline, the number of parameters, and the computational cost, respectively. Logarithmic scaling of parameter count normalizes exponential growth in model complexity, preventing large architectures from dominating the efficiency metric. This captures the diminishing performance gains with increasing size, yielding a fair and interpretable measure of how segmentation accuracy (DiffmIoU) scales with computational compactness.

TABLE IV SUMMARY OF THE BENCHMARK DATASETS USED IN THIS STUDY

Dataset Res. Seman. Image Total Train/Validation/ (cm/px) Classes Size Samples Test samples

LandCover.ai 25, 50 5 512 × 512 10674 7470/ 1602/ 1602 VDD 1.75, 4.2 7 4000 × 3000 400 280/ 80/ 40 PhenoBench 0.1 3 1024 × 1024 2872 1407/ 772/ 693*


> **Table V summarizes the implementation details of the**

> proposed DAS-SK, while Fig. 4 shows the model training
progress on the benchmark datasets.

* Predictions to be submitted to https://codalab.lisn.upsaclay.fr/competitions/13654.

IV. EXPERIMENTS AND DISCUSSION

A. Datasets

As summarised in Table IV, this study uses three publicly available benchmark data sets for experimental analysis. The Land Cover from Aerial Imagery (LandCover.ai) [30], is a high-resolution aerial imagery dataset annotated with build- ings, woodlands, water, and roads. The Varied Drone Dataset (VDD) [31] is a diverse UAV dataset covering multiple envi- ronments and conditions with seven semantic classes, and the PhenoBench [32] focuses on crop–weed discrimination and plant phenotyping under realistic field conditions.

C. Quantitative Analysis

A comprehensive summary of class-wise IoU scores and model performance bubble charts for all three datasets can be found in the Supplementary Materials. Table VI-VIII re- sults demonstrate that DAS-SK achieves an optimal balance between segmentation accuracy, computational efficiency, and inference speed. On Landcover.ai, DAS-SK attains 86.25% mIoU, second only to the ensemble UNet, while requiring only 10.7M parameters and 11.25 GFLOPs, resulting in the highest efficiency and excellent real-time FPS. Similarly, on VDD, DAS-SK achieves 79.45% mIoU with the highest efficiency and second-best FPS. On PhenoBench, DAS-SK reaches the best mIoU while remaining the most compact and efficient

B. Evaluation Metrics and Training Strategy

The model performances are evaluated on model efficiency. While mean Intersection over Union (mIoU) measures seg-

DAS-SK: AN ADAPTIVE MODEL INTEGRATING DUAL ATROUS SEPARABLE AND SELECTIVE KERNEL CNN FOR AGRICULTURE SEMANTIC SEGMENTATION (PREPRINT)5

(a) LandCover.ai (b) VDD (c) PhenoBench

Fig. 4. Training progress of the proposed model using the configurations given in Table V on LandCover.ai, VDD, and PhenoBench benchmark datasets.

TABLE V IMPLEMENTATION DETAILS

Component Configuration Environment A100-40GB GPU (Alliance Canada, Narval cluster). NVIDIA GeForce RTX 3050 Ti GPU (to obtain FPS) Framework PyTorch 2.1 with CUDA 12.1 Optimizer SGD with learning rate = 0.001, momentum = 0.9, weight decay = 0.0005. Scheduler Cosine annealing with minimum learning rate 10−5. Batch Size 8 for input resolution of 512 × 512 4 for larger input resolution Early Stop Patience of 30 epochs. Loss Function Ltotal = LCE + LDice + LFocal + LLovasz. Loss Summary

Cross Entropy (CE) – pixel accuracy; Dice – region over- lap; Focal – hard samples; Lov´asz – mIoU optimization. Data Augmentation

Random horizontal and vertical flips, Random 90-degree rotation, ShiftScaleRotate, and color jitter.

model, demonstrating strong generalization to fine-grained crop/weed segmentation.

Fig. 5. Four prediction samples on LandCover.ai’s test set.

Model selection under practical constraints further high- lights the advantage of DAS-SK. In memory-limited scenar- ios (about 10–12M parameters), DAS-SK provides the best trade-off between accuracy and resource usage, outperform- ing lightweight alternatives such as BiSeNet or SegFormer MiT-B0, which either compromise accuracy or achieve only marginal gains in FPS. Larger transformers, hybrid or ensem- bles, while slightly improving mIoU, require ≥30M parame- ters and achieve <5 FPS, making them unsuitable for real-time deployment on UAVs or edge devices.

D. Qualitative analysis

Across the three datasets (See Fig. 5 to 7), the proposed DAS- SK model consistently delivers accurate and visually reliable segmentation results. On LandCover.ai, it produces sharper building boundaries and smoother vegetation compared to Ensemble UNet. An additional quantitative visualization is provided in the Supplementary Materials. On the VDD dataset, DAS-SK demonstrates strong alignment with ground-truth labels, effectively delineating complex urban scenes and main- taining robustness under varying perspectives and lighting conditions. Similarly, on PhenoBench, the model accurately distinguishes crops, weeds, and partial vegetation classes even in cluttered or occluded environments, showing high preci- sion in separating visually similar regions. Overall, DAS-SK achieves consistent, detailed, and context-aware segmentation across diverse scenes, confirming its generalization capability.

Fig. 6. Four predication samples on VDD’s test set.

V. CONCLUSION

In conclusion, this study presented DAS-SK, a lightweight and efficient semantic segmentation framework for high- resolution agricultural imagery. By integrating DAS and SK convolutions within a modified DeepLabV3 architecture fea- turing context-aware attention and multi-scale fusion, DAS-SK achieves an optimal precision-efficiency balance. Evaluations on LandCover.ai, VDD, and PhenoBench datasets show that DAS-SK consistently outperforms CNN-, transformer-, and

DAS-SK: AN ADAPTIVE MODEL INTEGRATING DUAL ATROUS SEPARABLE AND SELECTIVE KERNEL CNN FOR AGRICULTURE SEMANTIC SEGMENTATION (PREPRINT)6

TABLE VI MODEL EFFICIENCY ON THE LANDCOVER DATASET

Type Model mIoU (%) ↑ Param. (M) ↓ GFLOPs ↓ Diffmiou ↑ log(Param.) ↓ Efficiency (%) ↑ FPS ↑

CNN Our model (DAS-SK) 86.25 10.678 11.25 5.75 1.028 49.70 40.05 CNN HRNet [33] 82.80 11.458 20.39 2.30 1.059 10.65 25.46 CNN UNet [33] 83.40 24.436 31.41 2.90 1.388 6.65 54.34 Transformer SegFormer MiT-B2 [33] 84.40 27.461 43.18 3.90 1.439 6.28 23.54 CNN Diff-HRNet [34] 84.22 68.867 86.25 3.72 1.838 2.35 16.33 Hybrid Ensemble UNet [35] 88.02 193.539 141.26 7.52 2.287 2.33 5.04 Hybrid TransUNet [33] 82.90 91.404 165.14 2.40 1.961 0.74 8.16 CNN DeepLabV3 ResNet101 [33] 83.00 58.626 241.14 2.50 1.768 0.59 9.59 Hybrid MA-DBFAN [33] 85.30 34.595 853.30 4.80 1.539 0.37 0.23 CNN BiSeNet [33] 80.50 11.878 12.46 Baseline 1.075 Baseline 126.65

Note: The Ensemble UNet consists of UNet MaxVIT-S, UNet ConvFormer-M36, and UNet EfficientNet-B7. GFLOPs and FPS are estimated for an input image size of 512 × 512. ↑– higher is better; ↓– lower is better; Boldface indicates the best result; underline indicates the 2nd-best.

TABLE VII MODEL EFFICIENCY ON THE VDD DATASET

Type Model mIoU (%) ↑ Param. (M) ↓ GFLOPs ↓ Diffmiou ↑ log(Param.) ↓ Efficiency (%) ↑ FPS ↑

CNN Our model (DAS-SK) 79.45 10.678 43.52 4.08 1.028 9.12 10.33 Transformer SegFormer MiT-B2 [31] 85.75 27.461 164.70 10.38 1.439 4.38 2.82 Hybrid Mask2Former ResNet50 [31] 83.21 45.517 133.70 7.84 1.658 3.54 3.48 Transformer Mask2Former SwinT [31] 77.85 47.439 45.74 2.48 1.676 3.23 3.04 Transformer SegFormer MiT-B5 [31] 82.11 84.708 180.53 6.74 1.928 1.94 1.53 Hybrid UperNet SwinT [31] 84.73 59.941 811.59 9.36 1.778 0.65 0.10 Hybrid UperNet SwinL [31] 85.63 233.962 825.92 10.26 2.369 0.52 0.08 Transformer SegFormer MiT-B0 [31] 75.37 3.752 20.89 Baseline 0.574 Baseline 13.62

Note: Input image size - 1000 × 1000. ↑– higher is better; ↓– lower is better; Boldface indicates the best result; underline indicates the 2nd-best.

TABLE VIII MODEL EFFICIENCY ON THE PHENOBENCH DATASET

Type Model mIoU (%) ↑ Param. (M) ↓ GFLOPs ↓ Diffmiou ↑ log(Param.) ↓ Efficiency (%) ↑ FPS ↑

CNN Our model (DAS-SK) 85.55 10.678 45.00 4.67 1.028 10.09 10.33 CNN UNet ResNet34 [9] 85.48 24.436 125.63 4.60 1.388 2.64 15.19 CNN DeepLabV3+ ResNet101 [16] 85.52 45.670 233.89 4.64 1.660 1.25 7.75 CNN DeepLabV3 ResNet101 [16] 84.98 58.626 964.56 4.10 1.768 0.24 2.42 CNN PSPNet ResNet50 [36] 80.88 24.314 46.87 Baseline 1.386 Baseline 22.05

Note: Input image size - 1024 × 1024. ↑– higher is better; ↓– lower is better; Boldface indicates the best result; underline indicates the 2nd-best.

remote sensing applications. Future work will extend DAS- SK toward self-supervised and domain-adaptive segmentation under limited labels of agricultural imagery.

VI. APPENDIX

This section provides additional technical details, imple- mentation insights, and analyses that complement the main manuscript. Section VI-A presents the ablation studies, includ- ing training and validation performance analyses to evaluate convergence stability and the model’s overall learning behav- ior. Section VI-B details the mathematical formulations of the proposed DAS-SKConv module, the enhanced Atrous Spatial Pyramid Pooling (ASPP) module, and the modified decoder structure. Section VI-E provides a comprehensive quantitative evaluation across multiple datasets, while Section VI-E1 offers an additional qualitative analysis to visually assess segmen- tation consistency and robustness. Together, these sections aim to provide an understanding of the model’s architectural design, ablation decisions, and performance of the proposed framework across the benchmark datasets.

Fig. 7. Four predication samples on PhenoBench’s validation set.

hybrid-based baselines, demonstrating strong generalization and scalability while preserving a compact design, offering a practical and high-performing solution for agricultural and

DAS-SK: AN ADAPTIVE MODEL INTEGRATING DUAL ATROUS SEPARABLE AND SELECTIVE KERNEL CNN FOR AGRICULTURE SEMANTIC SEGMENTATION (PREPRINT)7

TABLE IX SUMMARY OF ABLATION STUDIES

Stage Description mIoU (%) Param. (M) GFLOPs Memory (MB)

1 Baseline model (MobileNetV3-Large DeepLabV3) 82.77 11.025 9.84 514.77 2 Replace all standard convolutions with dilation in the ASPP module with DAS-Conv of dilation rates of 4, 8, 12 and 24 and add skip connection (b7) from backbone.

83.08 7.589 6.31 533.34

3 Add dilation rates of 18 and 26 and replace dilation rate of 24 with 22 83.23 7.606 6.33 533.34 4 Replace Global Average Pooling with Strip Pooling in ASPP 83.34 7.852 6.83 554.31 5 Add a skip connection from base backbone to decoder (b4) 83.58 7.898 7.03 574.39 6 Add auxiliary backbone (EfficientNet-B3) 84.57 10.077 10.16 1549.56 7 Add a skip connection from auxiliary backbone (a4) 84.90 10.084 10.19 1551.17 8 Replace DAS-Conv with DAS-SKConv in ASPP 85.18 10.383 10.42 1577.54 9 Add a skip connection from base backbone (b2) 85.23 10.411 10.90 1640.96 10 Add a skip connection from auxiliary backbone (clone(a3)) 85.30 10.415 10.98 1645.17 11 Replace first separable conv right after Enhanced ASPP with a parallel conv 85.79 10.678 11.25 1646.22 12 Add additional data augmentation of ShiftScaleRotate 86.25 10.678 11.25 1646.22

(a) LandCover.ai (b) VDD (c) PhenoBench

Fig. 8. Training and validation performance curves for LandCover.ai, VDD, and PhenoBench datasets.

A. Additional ablation studies

guidance to the ASPP, contributing to improved feature consis- tency and better boundary delineation. Together, these changes delivered a highly favorable impact-to-cost ratio, showing that structural efficiency can coexist with accuracy improvements.

As PhenoBench requires submitting model predictions for its test set to obtain results, the LandCover.ai dataset was instead used as a trial platform to improve the DAS model. Numerous experiments were conducted to modify the model architecture and enhance performance; however, only those that led to significant improvements are detailed in Table IX.

Stage 3 involved adjustment of the dilation configuration, which yielded an additional +0.15% mIoU gain with negligi- ble cost increase, suggesting optimal receptive field tuning. Substituting global average pooling with strip pooling in Stage 4 improved spatial context aggregation, resulting in an mIoU gain of +0.11% at a small cost increase of 0.25M parameters and 0.5 GFLOPs. In Stage 5, adding backbone skip connections from deeper layers further enhanced feature fusion, achieving an mIoU gain of +0.24% with minimal overhead. To accommodate these additional inputs from the backbones to the decoder at this and subsequent stages in the ablation studies, channel-wise concatenation followed by a separable convolution, ReLU activation, batch normalization, and bilinear upsampling was implemented.

Starting from the baseline MobileNetV3-Large DeepLabV3, which achieves an mIoU of 82.77% with 11.0M parameters and 9.84 GFLOPs, successive modifications demonstrate a careful balance between accuracy gains and resource costs.

Replacing standard convolutions with DAS-Conv and adding a skip connection from backbone (b7) in Stage 2 significantly reduced computational cost—parameters dropped by 31% and GFLOPs by 36% while improving mIoU by +0.31%. The integration of multi-dilation receptive fields through DAS-Conv enhanced contextual understanding with lower computation, while the added skip connection from the backbone (b7) further strengthened high-level semantic

Incorporating an auxiliary EfficientNet-B3 backbone in

DAS-SK: AN ADAPTIVE MODEL INTEGRATING DUAL ATROUS SEPARABLE AND SELECTIVE KERNEL CNN FOR AGRICULTURE SEMANTIC SEGMENTATION (PREPRINT)8

Stage 6 led to a substantial mIoU gain of +0.99%, albeit with increases in parameters (+27%) and memory usage (about 3× higher). Despite the higher cost, this step provided one of the most notable gains, highlighting the auxiliary encoder’s com- plementary feature representation. The subsequent addition of a skip connection (a4) from this auxiliary path in Stage 7 added marginal cost but yielded a further +0.33% mIoU gain, confirming the benefit of cross-scale fusion.

best validation mIoU of 0.8269 recorded at epoch 139. For PhenoBench, early stopping was applied at epoch 271, with the best validation mIoU of 0.7016 attained at epoch 241.

Across all datasets, the training losses exhibit smooth con- vergence, while validation losses stabilize early, indicating effective and consistent learning. Accuracy and mIoU curves demonstrate steady improvement and close alignment between training and validation phases, reflecting stable optimization behavior and minimal overfitting throughout training.

Replacing DAS-Conv with DAS-SKConv in Stage 8 brought another meaningful +0.28% mIoU gain with moderate com- putational growth (+3% parameters, +2% GFLOPs), under- scoring the SK module’s adaptivity to multi-scale feature variation. Additional skip connections (b2 and clone(a3)) from both main and auxiliary backbones in Stages 9-10 provided smaller incremental improvements of +0.05% and +0.07% mIoU gains, respectively, at slight cost increases, suggesting diminishing returns at this point. Initial experiment with a direct skip connection from a3 to the decoder resulted in lower performance due to backpropagation affecting the weights of the auxiliary backbone via a3. To prevent unintended weight updates in the auxiliary backbone, a copy of the a3 feature maps was used instead, ensuring that the auxiliary backbone from a3 backwards remained unchanged during training.

B. Mathematical expressions

1) DAS-SKConv module: The DAS-SKConv module in Fig.9 is designed to enhance feature extraction by combining multiscale spatial context with adaptive channel attention. It begins with a DAS block that processes the input feature maps through two parallel convolution paths, which are as follows:

In the atrous separable branch, the input x ∈RCin×H×W

first undergoes a depthwise atrous convolution:

3,d(x) ∈RCin×H×W , (3)

Oda = Convdw

where each input channel is convolved independently with a 3 × 3 kernel, dilation d, and padding d. This is followed by a pointwise convolution for channel mixing and reduction:

In Stage 11, replacing the post-ASPP separable convo- lution with a parallel convolution yielded a larger +0.49% mIoU gain for a modest 2.5% increase in computational cost, indicating an efficient trade-off. Finally, the application of ShiftScaleRotate data augmentation in Stage 12 enhanced the final performance with an mIoU gain of +0.46% without adding computational or parameter burden, emphasizing the crucial role of data diversity in generalization.

Op = Conv1×1(Oda) ∈R[Cout/2]×H×W , (4)

and then batch normalization with ReLU activation:

Op = ReLU(BN(Op)). (5)

In the standard atrous branch, a regular dilated convolution is applied:

In summary, the progression illustrates that early architec- tural redesigns (Stages 2–5) achieved high efficiency gains with minimal resource increase, while later stages (6–11) focused on refined multi-scale and multi-backbone feature fusion to maximize accuracy. The final configuration balances strong performance with acceptable efficiency, demonstrating the effectiveness of the DAS-SK architecture in optimizing the impact-to-cost ratio across design stages.

Oa = Conv3,d(x) ∈R[Cout/2]×H×W , (6)

with kernel size 3 × 3, dilation d, and padding d, followed again by batch normalization and ReLU:

Oa = ReLU(BN(Oa)). (7)

The final output of the DAS block is obtained by concate- nating the two feature maps along the channel dimension:

It is worth noting that the above architectural refinements are based on a 512×512 image input. For larger input sizes, such as those in the VDD and PhenoBench datasets, the number of DAS-SKConv and their dilation rates can be further fine- tuned to achieve broader receptive fields and potentially better performance—an aspect that will be explored in future work. For simplicity, the model refined on the LandCover.ai dataset is utilized for both VDD and PhenoBench in this study.

Odas = Concat(Op, Oa) ∈RCout×H×W . (8)

These concatenated features are then passed through an SK attention mechanism, which adaptively recalibrates the channel-wise feature responses. The SK attention module learns to selectively emphasize or suppress features from different receptive fields, allowing the network to dynamically focus on the most informative spatial scales for each input. Each SK branch convolution produces

1) Training and Validation Performance Curves: To as- sess the training stability and generalization behavior of the proposed model, Fig. 8 presents the training and validation curves for loss, accuracy, and mean Intersection-over-Union (mIoU) across the three evaluated datasets. These curves provide insight into the convergence dynamics and the model’s ability to maintain consistent performance between training and validation phases.

Fm = Convm(Odas) ∈RC×H×W , m = 1, . . . , M. (9)

which are stacked as

F = stack(F1, . . . , FM) ∈RM×C×H×W . (10)

The fused representation is obtained by summation,

For LandCover.ai, early stopping was triggered at epoch 222, with the best validation mIoU of 0.8602 achieved at epoch 192. For VDD, early stopping occurred at epoch 169, with the

M X

Fm ∈RC×H×W . (11)

U =

m=1

DAS-SK: AN ADAPTIVE MODEL INTEGRATING DUAL ATROUS SEPARABLE AND SELECTIVE KERNEL CNN FOR AGRICULTURE SEMANTIC SEGMENTATION (PREPRINT)9

Fig. 9. The proposed DAS-SKConv module. The DAS block combines atrous separable and standard atrous convolutions to capture both fine and broad spatial features. The SK attention mechanism adaptively weights multi-branch features through channel-wise attention, producing context-aware representations.

A global average pooling is applied,

S = GAP(U) ∈RC×1×1, (12)

followed by channel reduction and nonlinearity,

Z = ReLU(BN(Conv1×1(S))) ∈Rd×1×1, (13)

d = max(C/r, L). (14)

Branch-channel attention logits are generated as

Alogits = Conv1×1(Z) ∈RM·C×1×1, (15)

D - dilation rates of the

reshaped to A ∈RM×C×1×1 and normalized with a softmax across the branch dimension:

DAS-SKConv in Fig. 9.

Fig. 10. The enhanced ASPP module. High-dimensional backbone features are processed via parallel branches, including a 1×1 Conv, six DAS-SKConv with varying dilation rates, and a strip pooling branch.

αm,c = exp(Am,c) PM

. (16)

m′=1 exp(Am′,c)

In parallel, six DAS SK convolutions with kernel size 3×3 and dilation rates d ∈{4, 8, 12, 18, 22, 26} are applied:

The final output is then the attention-weighted sum of branch features,

M X

Bi = DAS SKConv3×3,di(X), (19)

αm,c · Fm,c,h,w, (17)

outc,h,w =

where Bi ∈R128×H×W for i = 1, . . . , 6.

m=1

To further improve the module’s ability to model long- range dependencies, a strip pooling branch is included. Unlike standard pooling, strip pooling captures context along hori- zontal and vertical strips, which is efficient for structured and elongated objects such as vegetation rows.

yielding an output features ∈RC×H×W .

This combination of dual atrous convolutional sampling and adaptive selective-kernel attention enables DAS-SKConv to provide rich, context-aware feature representations, making it effective for semantic segmentation and other dense prediction tasks where both local detail and global context are crucial.

Bs = StripPool(X) ∈R256×H×W . (20)

All branch outputs are concatenated along the channel dimension, resulting in a fused feature map:

C. Enhanced ASPP module

F = Concat(B0, B1, . . . , B6, Bs) ∈R1280×H×W . (21)

The Enhanced ASPP module, as shown in Fig.10, is de- signed to enrich feature representations by capturing con- textual information at multiple scales. It begins by taking a high-dimensional feature map from both primary and aux- iliary backbone networks, denoted as X ∈R960×H×W . To capture diverse contextual information, this module processes X through multiple parallel branches.

Finally, to make this representation compact and more efficient for subsequent processing, a 1 × 1 convolution is applied to reduce the dimensionality back to 256 channels. This is followed by batch normalization, ReLU activation, and dropout to stabilize training and prevent overfitting.

First, a 1 × 1 convolution reduces the channel dimension:

Y = Dropout(ReLU(BN(Conv1×1(F)))) (22)

Bo = Conv1×1(X) ∈R256×H×W . (18)

yielding an output features ∈R256×H×W .

DAS-SK: AN ADAPTIVE MODEL INTEGRATING DUAL ATROUS SEPARABLE AND SELECTIVE KERNEL CNN FOR AGRICULTURE SEMANTIC SEGMENTATION (PREPRINT)10

Fig. 11. The overall architecture. The backbones extract multi-scale features from the input, which are then fused and refined via the enhanced ASPP with DAS-SKConv (cf. Fig. 9). The decoder then progressively upsamples and refines the fused features with skip connections to produce accurate segmentation.

Overall, the Enhanced ASPP module improves the repre- sentational power of the backbone features by combining local details, multi-scale context, and global structural information. The resulting output feature map is compact and context-rich, making it highly efficient for downstream segmentation tasks.

The resulting feature map is upsampled, fused with back- bone outputs of a3 and b4, and refined again:

2, scale = 2) ∈148×4H×4W , (30)

Xup

2 = Upsample(X′


## 2 , clone(a3), b4) ∈R204×4H×4W ,

(31)

X3 = Concat(Xup


## 3 = ϕ(X3) ∈R148×4H×4W .

(32)

X′

D. Decoder

Finally, the decoder upsamples the output feature represen- tation once more, concatenates with the shallowest primary backbone output (b2), and refines it using separable convolu- tion, batch normalization, and ReLU.

The decoder, illustrated in Fig. 11, begins by concatenating the high-level feature maps a7 and b17 from the backbones channel-wise to form X ∈R960×H×W . It is then enriched with contextual information using the Enhanced ASPP mod- ule, resulting in X0 ∈R256×H×W .

3, scale = 2) ∈148×8H×8W , (33)

Xup

3 = Upsample(X′

To further refine these local and multi-scale contextual fea- tures, X0 is passed through two parallel operations: a separable convolution (SConv) and a standard 3 × 3 convolution.


## 3 , b2) ∈R164×8H×8W ,

(34)

X4 = Concat(Xup


## 4 = ϕ(X4) ∈R164×8H×8W .

(35)

X′

S = SConv(X0) ∈R128×H×W , (23)

A final 1 × 1 convolution projects the features into C channels, which corresponds to the number of target classes, and it is then resized into class logits:

C = Conv3×3(X0) ∈R128×H×W . (24)

4) ∈RC×8H×8W , (36)

Y = Conv1×1(X′

The results are concatenated along the channel dimension, producing a strong combined representation:

Ylogits = Upsample(Y, scale = 2) ∈RC×16H×16W . (37)

X1 = Concat(S, C) ∈R256×H×W (25)

The segmentation map can be obtained by applying the Softmax activation function and argmax to Ylogits.

Next, the learned features undergo batch normalization and ReLU activation.

E. Quantitative analysis

X′


## 1 = ReLU(BN(X1))

(26)


> **Table X–XII present the quantitative comparison of the pro-**

> posed DAS-SK model against several state-of-the-art segmen-
tation methods across three benchmark datasets: LandCover.ai,
PhenoBench, and VDD. Overall, DAS-SK consistently demon-
strates strong generalization and competitive accuracy while
maintaining a lightweight and efficient architecture.

Next, the decoder progressively upsamples the features to recover spatial detail and aligns them with lower-level features from the backbone and auxiliary backbone. The first upsampling step doubles the spatial resolution:

1, scale = 2) ∈R256×2H×2W . (27)

Xup

1 = Upsample(X′

On the LandCover.ai dataset, DAS-SK achieves an overall mIoU of 86.25%, ranking second only to the Ensemble-UNet, which relies on multi-model aggregation for performance gain. Despite this, DAS-SK surpasses most transformer- and CNN-based models such as SegFormer, Diff-HRNet, and DeepLabV3, highlighting the efficiency of the SK-enhanced convolutional design and refined decoder structure. The model performs particularly well in the Background, Building, and Water classes, indicating its robustness in delineating high- contrast and structurally diverse regions.

This upsampled feature map is concatenated with the corre- sponding feature map from the backbones (a4 and b7), forming a richer representation:


## 1 , a4, b7) ∈R344×2H×2W .

(28)

X2 = Concat(Xup

A separable convolution followed by batch normalization and ReLU activation, denoted as ϕ(.), then refines this merged feature set:

For the PhenoBench dataset, which contains fine-grained agricultural field imagery, DAS-SK attains the highest mIoU


## 2 = ϕ(X2) ∈R148×2H×2W .

(29)

X′

DAS-SK: AN ADAPTIVE MODEL INTEGRATING DUAL ATROUS SEPARABLE AND SELECTIVE KERNEL CNN FOR AGRICULTURE SEMANTIC SEGMENTATION (PREPRINT)11

TABLE X PERFORMANCE ANALYSIS ON LANDCOVER’S TEST SET

TABLE XI PERFORMANCE ANALYSIS ON PHENOBENCH’ TEST SET

Model mIoU ↑ Class-wise IoU (%) ↑ (%) BG Build WoodLnd. Water Rd.

Model mIoU ↑ Class-wise IoU (%) ↑ (%) Soil Crop Weed

Ensemble UNet 88.02 94.30 85.33 92.43 95.42 72.62 Our model (DAS-SK) 86.25 93.42 82.16 91.29 94.72 69.68 MA-DBFAN 85.30 94.30 79.20 91.30 94.70 67.20 SegFormer MiT-B2 84.40 93.20 76.90 91.20 94.40 66.30 Diff-HRNet 84.22 93.00 79.10 90.10 93.10 65.80 UNet 83.40 92.40 77.80 90.10 93.50 63.40 DeepLabV3 83.00 92.30 76.70 90.10 92.40 63.60 TransUNet 82.90 92.10 77.90 89.90 92.50 62.40 HRNet 82.80 92.10 76.50 89.90 92.70 62.60 BiSeNet 80.50 91.00 71.80 88.60 91.20 59.60

Our model (DAS-SK) 85.55 99.34 94.16 63.15 DeepLabV3+ ResNet101 85.52 99.29 94.00 63.28 UNet ResNet34 85.48 99.31 93.97 63.14 DeepLabV3 ResNet101 84.98 99.13 93.00 62.81 PSPNet ResNet50 80.88 99.04 91.81 51.80

TABLE XII PERFORMANCE ANALYSIS ON VDD’S TEST SET

Model mIoU ↑ Class-wise IoU (%) ↑ (%) Other Wall Rd. Veg. Vehicle Roof Water

Mask2Former 83.21 75.76 69.01 79.07 93.11 74.25 94.27 97.02 Ours: DAS-SK 79.45 66.51 71.77 73.81 90.09 74.94 86.81 92.22

↑- higher is better, ↓- lower is better, Boldface - the best, underline - 2nd-best results. BG- Background, Build- Buildings, WoodLnd.- Woodland, Rd.- Road, Veg.- Vegetation.

classes—ranging from vegetative regions to man-made struc- tures—underscores its adaptability to complex urban scenes, suggesting strong generalization beyond the training domain.

Across the three datasets, DAS-SK consistently demon- strates competitive performance, frequently achieving top two positions in mIoU and class-wise IoU metrics. Its performance profile suggests strong versatility: it handles both natural and urban scenes effectively while remaining computationally efficient. The results validate the effectiveness of integrating dual atrous separable convolutions with selective kernel mech- anisms for capturing multi-scale contextual information and fine-grained details across diverse segmentation tasks.

Fig. 13 illustrates the efficiency of different segmenta- tion models across the three datasets. The x-axis denotes GFLOPs and the y-axis the logarithm of parameters, with more lightweight models positioned toward the lower left. Bubble sizes reflect overall efficiency, and each is labeled with its mIoU (%) to show the accuracy–efficiency trade-off. Across all subfigures, DAS-SK consistently appears near the lower-left corner while maintaining high mIoU, underscoring its strong balance between efficiency and segmentation quality—ideal for resource-constrained agricultural applications.

1) Additional qualitative results: Fig. 12 presents a quali- tative comparison between MA-DBFAN and our model across diverse remote sensing scenes in the LandCover.ai’s test set. While MA-DBFAN captures the overall structure, it often struggles with fine boundaries and small objects. In contrast, our model demonstrates superior delineation of buildings, roads, and water bodies, while maintaining consistency in large homogeneous regions such as woodland and farmland. These results highlight the reliability of our approach in accurately segmenting both large-scale and detailed features in complex aerial imagery.

Fig. 12. Predication samples on LandCover.ai’s test set.

of 85.55%, marginally outperforming DeepLabV3+and UNet ResNet34. The model achieves the best IoU scores for the Soil and Crop classes and a competitive score for Weed, demon- strating improved class discrimination and resilience against inter-class similarity. The superior performance here validates the model’s capacity to handle challenging agricultural scenes characterized by subtle texture and illumination variations.


## REFERENCES

[1] X. Ma, X. Zhang, M.-O. Pun, and M. Liu, “A multilevel multimodal

fusion transformer for remote sensing semantic segmentation,” IEEE Transactions on Geoscience and Remote Sensing, vol. 62, pp. 1–15, 2024. [2] X. Ma, X. Zhang, M.-O. Pun, and B. Huang, “A unified framework

On the VDD dataset, DAS-SK achieves an mIoU of 79.45%, second only to Mask2Former. It excels in specific classes such as wall and vehicle, outperforming Mask2Former in these categories. Its consistently high IoU across heterogeneous

with multimodal fine-tuning for remote sensing semantic segmentation,” IEEE Transactions on Geoscience and Remote Sensing, 2025.

DAS-SK: AN ADAPTIVE MODEL INTEGRATING DUAL ATROUS SEPARABLE AND SELECTIVE KERNEL CNN FOR AGRICULTURE SEMANTIC SEGMENTATION (PREPRINT)12

(a) LandCover.ai (b) VDD (c) PhenoBench

Fig. 13. Bubble chart of model performance, with bubble size representing efficiency (%) and values next to the bubble indicating mIoU (%). Refer to Table VI-VIII in the main text; a few models are not included in these plots, either due to being a baseline or an outlier to the plot range.

[17] M. Tan and Q. Le, “Efficientnet: Rethinking model scaling for con-

[3] L. Li, J. Yi, H. Fan, and H. Lin, “A lightweight semantic segmentation

volutional neural networks,” in International conference on machine learning. PMLR, 2019, pp. 6105–6114. [18] I. Hern´andez, R. Silva, P. Melo-Pinto, S. Guti´errez, and J. Tardaguila,

network based on self-attention mechanism and state space model for efficient urban scene segmentation,” IEEE Transactions on Geoscience and Remote Sensing, 2025. [4] X. He, Y. Zhou, J. Zhao, D. Zhang, R. Yao, and Y. Xue, “Swin

“Early detection of downy mildew in vineyards using deep neural networks for semantic segmentation,” Biosystems Engineering, vol. 252, pp. 15–31, 2025. [Online]. Available: https://www.sciencedirect. com/science/article/pii/S1537511025000339 [19] F. Garibaldi-M´arquez, G. Flores, L. M. Valent´ın-Coronado et al., “Lever-

transformer embedding unet for remote sensing image semantic segmen- tation,” IEEE transactions on geoscience and remote sensing, vol. 60, pp. 1–15, 2022. [5] T. Suresh, H. Sundaralingam, T. Akilan, and S. B. Ahmed, “Ss-deepseg:

aging deep semantic segmentation for assisted weed detection,” Journal of Agricultural Engineering, vol. 56, no. 2, 2025. [20] C. M. Ling, T. Akilan, and A. R. Phalke, “Dual atrous separable

An efficient deeplab with smart scaling for robust semantic segmen- tation,” in 2025 IEEE 34th International Symposium on Industrial Electronics (ISIE). IEEE, 2025, pp. 1–6. [6] Y. Zhang and C. Lv, “Tinysegformer: A lightweight visual segmenta-

convolution for improving agricultural semantic segmentation,” arXiv preprint arXiv:2506.22570, 2025. [21] W. M. Elmessery, D. V. Maklakov, T. M. El-Messery, D. A. Baranenko,

tion model for real-time agricultural pest detection,” Computers and Electronics in Agriculture, vol. 218, p. 108740, 2024. [7] Y. Wu, L. Tang, and S. Yuan, “Semantic segmentation model of multi-

J. Guti´errez, M. Y. Shams, T. A. El-Hafeez, S. Elsayed, S. K. Alhag, F. S. Moghanm et al., “Semantic segmentation of microbial alterations based on segformer,” Frontiers in Plant Science, vol. 15, p. 1352935, 2024. [22] Y. Shen, L. Wang, and Y. Jin, “Aaformer: A multi-modal transformer

source remote sensing images was used to extract winter wheat at tillering stage,” Scientific reports, vol. 15, no. 1, pp. 1–14, 2025. [8] M. Campos-Taberner, F. J. Garc´ıa-Haro, G. Camps-Valls, G. Grau-

Muedra, F. Nutini, A. Crema, and M. Boschetti, “Multitemporal and multiresolution leaf area index retrieval for operational local rice crop monitoring,” Remote Sensing of Environment, vol. 187, pp. 102–118, 2016. [9] O. Ronneberger, P. Fischer, and T. Brox, “U-net: Convolutional networks

network for aerial agricultural images,” in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2022, pp. 1705–1711. [23] A. Tavera, E. Arnaudo, C. Masone, and B. Caputo, “Augmentation

invariance and adaptive sampling in semantic segmentation of agricul- tural aerial images,” in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2022, pp. 1656–1665. [24] G. Wang, D. Bai, H. Lin, H. Zhou, and J. Qian, “Firevitnet: A hybrid

for biomedical image segmentation,” in International Conference on Medical image computing and computer-assisted intervention. Springer, 2015, pp. 234–241. [10] L.-C. Chen, G. Papandreou, I. Kokkinos, K. Murphy, and A. L. Yuille,

model integrating vit and cnns for forest fire segmentation,” Computers and Electronics in Agriculture, vol. 218, p. 108722, 2024. [25] Y. Wei, Y. Feng, D. Zu, and X. Zhang, “A hybrid cnn-transformer

“Deeplab: Semantic image segmentation with deep convolutional nets, atrous convolution, and fully connected crfs,” IEEE transactions on pattern analysis and machine intelligence, vol. 40, no. 4, pp. 834–848, 2017. [11] V. Badrinarayanan, A. Kendall, and R. Cipolla, “Segnet: A deep con-

network: Accurate and efficient semantic segmentation of crops and weeds on resource-constrained embedded devices,” Crop Protection, vol. 188, p. 107018, 2025. [26] J. Zhang, T. Wu, J. Luo, X. Hu, L. Wang, M. Li, X. Lu, and

volutional encoder-decoder architecture for image segmentation,” IEEE transactions on pattern analysis and machine intelligence, vol. 39, no. 12, pp. 2481–2495, 2017. [12] A. Dosovitskiy, L. Beyer, A. Kolesnikov, D. Weissenborn, X. Zhai,

Z. Li, “Toward agricultural cultivation parcels extraction in the complex mountainous areas using prior information and deep learning,” IEEE Transactions on Geoscience and Remote Sensing, vol. 63, pp. 1–14, 2025. [27] I. Tsardanidis, D. Bormpoudakis, I. Tsoumas, D. A. Loka, C. Noulas,

T. Unterthiner, M. Dehghani, M. Minderer, G. Heigold, S. Gelly et al., “An image is worth 16x16 words: Transformers for image recognition at scale,” arXiv preprint arXiv:2010.11929, 2020. [13] S. Zheng, J. Lu, H. Zhao, X. Zhu, Z. Luo, Y. Wang, Y. Fu, J. Feng,

A. Tsitouras, and C. Kontoes, “Estimation of agricultural intensification through semisupervised deep learning on sentinel-2 imagery,” IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing, vol. 18, pp. 21 077–21 089, 2025. [28] Y. Pan, X. Wang, Y. Wang, and Y. Zhong, “Rbp-mtl: Agricultural parcel

T. Xiang, P. H. Torr et al., “Rethinking semantic segmentation from a sequence-to-sequence perspective with transformers,” in Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, 2021, pp. 6881–6890. [14] M. M. N. Abid, N. Mehta, Z. Wu, and R. Timofte, “Con- textformer: Redefining efficiency in semantic segmentation,” arXiv preprint arXiv:2501.19255, 2025. [15] B. Niu, Q. Feng, B. Chen, C. Ou, Y. Liu, and J. Yang, “Hsi-transunet: A

vectorization via region-boundary-parcel decoupled multitask learning,” IEEE Transactions on Geoscience and Remote Sensing, vol. 62, pp. 1– 15, 2024. [29] T. Akilan, N. Jahan, and W. Zhang, “Self-supervised learning for image segmentation: A comprehensive survey,” arXiv preprint arXiv:2505.13584, 2025. [30] A. Boguszewski, D. Batorski, N. Ziemba-Jankowska, T. Dziedzic, and

transformer based semantic segmentation model for crop mapping from uav hyperspectral imagery,” Computers and Electronics in Agriculture, vol. 201, p. 107297, 2022. [16] L.-C. Chen, G. Papandreou, F. Schroff, and H. Adam, “Rethinking

A. Zambrzycka, “Landcover.ai: Dataset for automatic mapping of build- ings, woodlands, water and roads from aerial imagery,” in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) Workshops, June 2021, pp. 1102–1110.

atrous convolution for semantic image segmentation,” arXiv preprint arXiv:1706.05587, 2017.

DAS-SK: AN ADAPTIVE MODEL INTEGRATING DUAL ATROUS SEPARABLE AND SELECTIVE KERNEL CNN FOR AGRICULTURE SEMANTIC SEGMENTATION (PREPRINT)13

[31] W. Cai, K. Jin, J. Hou, C. Guo, L. Wu, and W. Yang, “Vdd:

Varied drone dataset for semantic segmentation,” Journal of Visual Communication and Image Representation, vol. 109, p. 104429, 2025. [Online]. Available: https://www.sciencedirect.com/science/article/pii/ S1047320325000434 [32] J. Weyler, F. Magistri, E. Marks, Y. L. Chong, M. Sodano, G. Roggiolani,

N. Chebrolu, C. Stachniss, and J. Behley, “Phenobench: A large dataset and benchmarks for semantic image interpretation in the agricultural do- main,” IEEE transactions on pattern analysis and machine intelligence, vol. 46, no. 12, pp. 9583–9594, 2024. [33] H. Yue, J. Yue, X. Guo, Y. Wang, and L. Jiang, “Ma-dbfan: multiple-

attention-based dual branch feature aggregation network for aerial image semantic segmentation,” Signal, Image and Video Processing, vol. 18, no. 5, pp. 4687–4701, 2024. [34] Z. Wu, C. Liu, B. Song, H. Pei, P. Li, and M. Chen, “Diff-hrnet:

A diffusion model-based high-resolution network for remote sensing semantic segmentation,” IEEE Geoscience and Remote Sensing Letters, vol. 22, pp. 1–5, 2025. [35] I. Dimitrovski, V. Spasev, S. Loshkovska, and I. Kitanovski, “U-

net ensemble for enhanced semantic segmentation in remote sensing imagery,” Remote Sensing, vol. 16, no. 12, p. 2077, 2024. [36] H. Zhao, J. Shi, X. Qi, X. Wang, and J. Jia, “Pyramid scene parsing

network,” in Proceedings of the IEEE conference on computer vision and pattern recognition, 2017, pp. 2881–2890.
