---
workspace_id: SCI-001413
doi: 10.3390/agriculture15242575
title: 'EDM-UNet: An Edge-Enhanced and Attention-Guided Model for UAV-Based Weed Segmentation
  in Soybean Fields'
authors:
- family_name: Gao
  given_name: Jiaxin
  orcid: null
- family_name: Tan
  given_name: Feng
  orcid: null
- family_name: Li
  given_name: Xiaohui
  orcid: null
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:35:05.545163+00:00'
---

# EDM-UNet: An Edge-Enhanced and Attention-Guided Model for UAV-Based Weed Segmentation in Soybean Fields

Article EDM-UNet: An Edge-Enhanced and Attention-Guided Model for UAV-Based Weed Segmentation in Soybean Fields

Jiaxin Gao 1, Feng Tan 2,* and Xiaohui Li 3

1 College of Engineering, Heilongjiang Bayi Agricultural University, Daqing 163319, China; gaojx@byau.edu.cn 2 College of Information and Electrical Engineering, Heilongjiang Bayi Agricultural University, Daqing 163319, China 3 College of Information Engineering, Shandong Vocational and Technical University of Engineering, Jinan 250200, China; sdgc_lxh@suet.edu.cn * Correspondence: bayitf@byau.edu.cn


## Abstract

Weeds will compete with soybeans for resources such as light, water and nutrients, inhibit the growth of soybeans, and reduce their yield and quality. Aiming at the problems of low efficiency, high environmental risk and insufficient weed identification accuracy in complex farmland scenarios of traditional weed management methods, this study proposes a weed segmentation method for soybean fields based on unmanned aerial vehicle remote sensing. This method enhances the channel feature selection capability by introducing a lightweight ECA module, improves the target boundary recognition by combining Canny edge detection, and designs directional consistency filtering and morphological post- processing to optimize the spatial structure of the segmentation results. The experimental results show that the EDM-UNet method achieves the best performance effect on the self-built dataset, and the MIoU, Recall and Precision on the test set reach 89.45%, 93.53% and 94.78% respectively. In terms of model inference speed, EDM-UNet also performs well, with an FPS of 40.36, which can meet the requirements of real-time detection models. Compared with the baseline network model, the MIoU, Recall and Precision of EDM-UNet increased by 6.71%, 5.67% and 3.03% respectively, and the FPS decreased by 11.25. In addition, performance evaluation experiments were conducted under different degrees of weed interference conditions. The models all showed good detection effects, verifying that the model proposed in this study can accurately segment weeds in soybean fields. This research provides an efficient solution for weed segmentation in complex farmland environments that takes into account both computational efficiency and segmentation accuracy, and has significant practical value for promoting the development of smart agricultural technology.

Academic Editor: Maciej Zaborowicz

Received: 12 November 2025

Revised: 8 December 2025

Accepted: 10 December 2025

Published: 12 December 2025

Citation: Gao, J.; Tan, F.; Li, X.

EDM-UNet: An Edge-Enhanced and

Keywords: soybean; weed segmentation; UAV; attention mechanism; U-Net

Attention-Guided Model for

UAV-Based Weed Segmentation in

Soybean Fields. Agriculture 2025, 15,

2575. https://doi.org/10.3390/


## 1. Introduction

agriculture15242575

Weeds represent a significant challenge to the productivity and quality of soybean production systems [1]. The effective management of weeds is of critical importance in reducing competition between crops and weeds for essential resources such as light, water, and nutrients [2,3]. Conventional control methodologies, predominantly those based on chemical herbicides and manual weeding—are frequently deemed to be inefficient, costly, and susceptible to environmental contamination. Such challenges underscore the necessity for more precise and sustainable weed management strategies. The advent of precision

Copyright: © 2025 by the authors.

Licensee MDPI, Basel, Switzerland.

This article is an open access article

distributed under the terms and

conditions of the Creative Commons

Attribution (CC BY) license

(https://creativecommons.org/

licenses/by/4.0/).

Agriculture 2025, 15, 2575 https://doi.org/10.3390/agriculture15242575

Agriculture 2025, 15, 2575 2 of 19

agriculture and intelligent technologies has precipitated a paradigm shift in the realm of weed identification. Automated approaches, underpinned by computer vision and machine learning, have emerged as a pivotal area of research. By analysing in-field images, these techniques can rapidly and accurately determine weed species and spatial distribution, thereby providing scientific guidance for precision spraying and mechanical weeding. In this study, a novel framework tailored to soybean fields for weed identification is proposed. The proposed approach integrates state-of-the-art image processing methods with machine learning algorithms to improve the accuracy and efficiency of weed detection in soybean plots. This approach offers a solid technical foundation for precision weed management. This work contributes to the advancement of smart agriculture and addresses the urgent demand for sustainable, high-efficiency agricultural production.

In the study conducted by Liu et al. [4], a novel methodology was proposed that integrates semantic segmentation and image processing for weed detection. Their ex- periments demonstrated that, after applying knowledge distillation to the DeepLabV3+ model, the average accuracy across all classes exceeded 99.5%, and the MIoU for all classes surpassed 95.5%. Building on similar encoder–decoder paradigms, Qi et al. [5] presented a semantic segmentation method known as PF-UperNet, which is rooted in an encoder– decoder architecture and achieved an MIoU of 87.45% and an MPA of 96.82%, with a total of 46.16 million parameters. Genze et al. [6] proposed DeBlurWeedSeg, a methodology that integrates deblurring and segmentation models to facilitate the analysis of motion-blurred images; their experiments demonstrated that combining deblurring and segmentation enabled accurate separation of weeds from sorghum and background in both clear and motion-blurred UAV-captured images. Zou et al. [7] presented a semantic-segmentation- based methodology for the evaluation of weed species and density, where the coefficient of determination (R2) between algorithm-computed and manually assessed weed density reached 0.90, with a root mean square error of 0.05, indicating effective density estimation in complex environments. Guo et al. [8] developed a semi-supervised deep learning model capable of learning semantic segmentation from both annotated and unannotated images, which reached 85.5% MIoU on test data even under conditions of intense weed infestation. In the broader field of agricultural computer vision, Ma et al. [9] presented a SegNet-based fully convolutional network for paddy-field semantic segmentation, achieving a mean accuracy of 92.7% and effectively classifying pixels of rice seedlings, background and weeds, while Janneh et al. [10] proposed a refined DCNN algorithm for pixel-wise semantic segmentation of crops and weeds, obtaining average MIoU scores of 0.8646, 0.9164 and 0.8459 on the CWFID carrot dataset, the BoniRob sugar beet dataset and a rice seedling dataset, respectively. Nong et al. [11] further advanced semi-supervised segmentation with SemiWeedNet, a weed–crop segmentation method designed for complex environments to reduce reliance on extensive labelled data; comparative experiments on public datasets showed that SemiWeedNet outperformed several state-of-the-art approaches. In addition, You et al. [12] proposed a weed/crop segmentation network capable of enhancing perfor- mance for the precise identification of weeds of arbitrary shape under complex conditions, thereby supporting autonomous robots in effectively reducing weed density.

In parallel with these high-accuracy segmentation models, a substantial body of work has focused on lightweight and real-time architectures that are suitable for deployment in the field. Han et al. [13] proposed a fast weed segmentation approach based on a Crop De- tection Model (CDM) and the Excess Green (ExG) index, which expedited the segmentation process while maintaining accuracy; the model achieved a precision of 92.50%, an IoU of 76.14%, and an overall accuracy of 98.10%, thereby providing real-time and accurate weed segmentation. Kong et al. [14] developed a new segmentation network based on the YOLO architecture and showed that the insertion of cross-attention significantly enhanced per-

Agriculture 2025, 15, 2575 3 of 19

formance: the improved model achieved an average MIoU@50 of 90.9%, alongside a 5.9% improvement in precision and a 15.56% reduction in GFLOPs, suggesting suitability for resource-constrained environments. Yu et al. [15] proposed DCSAnet, a lightweight weed segmentation network designed for mobile weed-control equipment; with a parameter count of only 0.57 million, DCSAnet achieved an MIoU of 85.95% together with the highest segmentation precision among the compared methods, demonstrating its effectiveness for practical weed-related tasks. Kong et al. [16] and colleagues developed an indirect approach that first segments crops and then classifies remaining green objects as weeds, achieving an MIoU of 97.9%, a recall of 93.4%, and a precision of 97.6%, while also improving inference speed. Gao et al. [17] reported that their EPAnet increased overall accuracy by 0.65%, MIoU by 1.91%, and frequency-weighted IoU by 1.19%; compared with state-of-the-art methods, EPAnet delivered superior segmentation under uneven illumination, leaf interference and shadows in natural environments. Lan et al. [18] presented two enhanced recognition models, MobileNetV2-UNet and FFB-BiSeNetV2, which attained higher segmentation precision than BiSeNetV2, with peak pixel accuracy and MIoU of 93.09% and 80.28%, respectively; on embedded hardware with FP16 weights, their inference speeds reached 45.05 FPS and 40.16 FPS per image. The improved U-Net model based on a MaxViT encoder and CBAM attention fusion proposed by Yadong Li et al. [19] further demonstrated that attention-enhanced encoder–decoder architectures can significantly improve the efficiency and generalisation ability of beet–weed segmentation while ensuring high accuracy, with most misclassifications occurring only at plant boundaries.

In parallel, classical and hybrid approaches that incorporate hand-crafted features and traditional image processing remain important. Bakhshipour et al. [20] investigated two approaches for distinguishing weeds from main crops and used principal component analysis to select 14 texture features from an initial set of 52. Their results demonstrated that wavelet texture features were effective in differentiating weeds within crops even in the presence of heavy occlusion and leaf overlap. Xu et al. [21] also exemplified a hybrid strategy, in which visible colour indices were combined with an encoder–decoder instance segmentation model to improve robustness and accuracy. These studies highlight the value of spectral and texture descriptors, particularly when integrated with modern deep learning architectures. Despite notable advances in semantic segmentation, lightweight design and semi-supervised learning, current weed identification methods still face key challenges that limit their deployment in the field. Complex agricultural conditions, such as variable lighting, occlusion, soil heterogeneity and motion blur, reduce the stability of feature extraction. The high visual similarity between crops and weeds also leads to boundary ambiguity and misclassification. Furthermore, most models rely heavily on large annotated datasets, yet generalise poorly across regions or growth stages. Lightweight networks improve efficiency, but often sacrifice fine-grained accuracy; heavier models, meanwhile, are unsuitable for embedded platforms. Furthermore, the limited use of agronomic priors restricts robustness in dense or irregular weed scenarios. Taken together, these limitations underscore the need for weed segmentation models that are more accurate, robust and scalable.

In this study, an EDM-UNet–based method for weed segmentation in soybean fields is proposed, which demonstrates strong robustness across varying weed densities while meet- ing real-time detection requirements. The model architecture integrates an efficient channel attention (ECA) mechanism with an edge-assisted guidance module: The ECA modules are embedded in the skip connections, and Canny-derived edge information is introduced at each decoder stage to guide the network’s focus towards both key semantic channels and boundary structures. This process significantly improves the accuracy of weed–soybean boundary delineation. In the post-processing stage, a direction-consistency enhancement

Agriculture 2025, 15, 2575 4 of 19

module employs multi-orientation Gabor filters to reinforce directional texture features characteristic of ridge-aligned planting patterns, thereby effectively suppressing false re- sponses from weeds with ambiguous textures. Finally, we leverage geometric priors of field crops to design a morphology-constrained aspect-ratio filtering mechanism. This mechanism further eliminates non-target regions and enhances the structural plausibility and agricultural relevance of the segmentation output. The experimental findings, obtained under natural field conditions, corroborate the efficacy of the proposed model for soybean weed segmentation. Beyond the advancement of automation and precision in soybean weed detection, the objective of this work is to drive agricultural modernisation, thereby improving overall production efficiency and economic returns. Furthermore, the techniques developed in this study have the potential to serve as a valuable reference and be extended to precision-management tasks in other crop systems.

The remainder of this paper is structured as follows: Section 2 details the structure and implementation of the algorithm, Section 3 presents experimental results and analysis, Section 4 discusses the findings, and Section 5 concludes the study.


## 2. Materials and Methods

2.1. Dataset Creation 2.1.1. Data Collection

UAV imagery was acquired daily between 10:00 and 13:00 local time from 12 to 20 June 2024 at the Agricultural Science Park of Heilongjiang Bayi Agricultural University, located in Anda, Suihua City, Heilongjiang Province, China, with central coordinates 46◦49′ N and 124◦26′ E, and an elevation of approximately 147 ft. During the data collection period, soybean crops were in the V2 to V3 stage. The study focused on soybean seedlings and associated weeds within a high-yield demonstration area featuring four cultivars: Qingken 32, Longken 324, Dongnong Dou 252, and Hekennong 18. The soybean field was infested mainly with grass and broadleaf weed species, including Digitaria sanguinalis, Echinochloa crus galli, Setaria viridis, Portulaca oleracea and Cirsium spp., which were predominantly in the two to five leaf stage.

A DJI Phantom 3P UAV equipped with a 1/2.3-inch CMOS sensor with an effective resolution of 12.4 MP and total pixels of 12.76 MP, and a lens with a 35 mm equivalent focal length of 20 mm, a field of view of 94◦, and an aperture of f/2.8 was deployed for data collection. All flights maintained a nadir camera orientation at altitudes of 2–5 m above the canopy. To minimize texture loss from cloud occlusion, operations were restricted to days with minimal cloud cover under stable solar radiation conditions. Flight missions were planned using Pix4Dcapture software (Version 4.4.10) with 80% forward overlap and 70% side overlap. Figure 1 illustrates the experimental field configuration and UAV setup.


> **Figure 1. Test site and acquisition equipment.**

Agriculture 2025, 15, 2575 5 of 19

2.1.2. Data Enhancement

The initial dataset comprised 800 raw UAV images acquired in soybean fields. For precise instance-level annotation, the open-source labeling tool LabelMe [22] was used to delineate individual weed regions. During the annotation process, all pixels belonging to weeds were assigned to the “weed” class, while all other regions were uniformly labeled as “background”. Annotation examples are shown in Figure 2, and the annotation metadata

were stored in JSON format to ensure readability and future extensibility.

(A)  (B)


> **Figure 2. Data annotation. (A) Original image; (B) Labeled image.**

To avoid data leakage and overly optimistic performance estimates, the annotated images were first partitioned into training, validation and test sets at the image level, with an 8:1:1 ratio. Specifically, 80 images were randomly selected as the validation set and a further 80 images as the test set, with no enhancement applied. Data augmentation was then applied exclusively to the remaining training set to increase diversity and robustness of the data under complex field conditions. These operations included the injection of random noise, random brightness adjustment and random rotation, to simulate variations in illumination conditions and environmental noise commonly encountered in real-world scenarios. Examples of the augmented images are shown in Figure 3. Based on visual quality and data diversity, the combination of the original and enhanced training samples was retained to form the final dataset used in this study. This dataset includes 1040 training images, 80 validation images and 80 testing images, totalling 1200 images. In total, the dataset contained 11,403 weed instances. The number of weed instances per image varied substantially, ranging from a minimum of three to a maximum of 48, thereby providing rich feature information for learning. This design ensures that augmented images do not leak into the validation set, thereby improving the model’s ability to generalise in complex field environments.

(A)  (B)  (C)  (D)


> **Figure 3. Data enhancement examples. (A) Original image; (B) Random brightness; (C) Random**

> noise; (D) Random rotation.

2.2. Improved U-Net Model

Olaf et al. [23] introduced the U-Net model, drawing inspiration from the fully convo- lutional network (FCN) [24]. The architecture of the U-Net model is illustrated in Figure 4. U-Net maintains high segmentation accuracy even with limited training data. Its U-shaped architecture consists of a context-capturing encoder and a decoder that merges features via transposed convolutions and skip connections. To enhance feature extraction, we replaced

Agriculture 2025, 15, 2575 6 of 19

the original U-Net encoder with a ResNet50 [25] backbone. The residual connections in ResNet50 have been demonstrated to alleviate issues related to vanishing gradients in deep networks, thereby enhancing the network’s capacity to capture intricate image features. Consequently, all subsequent experiments utilise ResNet50-UNet as the baseline model. To improve boundary precision and robustness, we embedded an ECA module into the ResNet50-UNet to recalibrate channel features, along with Canny edge detection [26] for boundary extraction, directional Gabor filtering [27] for enhancing ridge-aligned texture features, and morphology-based post-processing for removing small false-positive regions, thereby optimizing the final segmentation results.


> **Figure 4. U-Net model architecture diagram.**

2.2.1. Edge Detection Module

In order to enhance the model’s ability to discriminate boundaries between soy- bean plants and weeds under complex field backgrounds, a Canny-based edge-detection auxiliary module has been introduced into the U-Net decoder. Field images frequently demonstrate blurred boundaries and a high degree of morphological similarity between crops and weeds. This phenomenon often results in conventional U-Net losing edge infor- mation during the process of feature fusion, thereby producing segmentation borders that are not clearly delineated.

Accordingly, the Canny algorithm is initially implemented on the original input image I(x, y) to extract salient edge maps. The gradient magnitude M(x, y) and orientation Θ(x, y) are computed using Sobel operators as:

q

G2

x + G2

M(x, y) =

y, (1)

Gy



Θ(x, y) = arctan

(2)

Gx

where Gx and Gy denote the horizontal and vertical gradients, respectively. After non- maximum suppression and double thresholding, a binary edge map E(x, y) is obtained to highlight structural contours.

These edge maps function as guiding cues that are integrated into the upsampled features at each decoder stage. During each skip connection, the upsampled deep features are concatenated not only with the corresponding encoder-side shallow features but also

Agriculture 2025, 15, 2575 7 of 19

with the Canny-derived edge map. This process forms a multi-dimensional representation that encodes semantic, spatial, and structural information. These concatenated features are then merged through two successive convolutional layers, followed by an ECA mod- ule to strengthen inter-channel interactions and boost the network’s responsiveness to critical regions. This strategy preserves U-Net’s strength in multi-scale feature modelling while explicitly integrating edge information to improve structural awareness, particularly along soybean–weed boundaries. The enhanced EDM-UNet model has been developed to achieve clearer and more accurate delineation in challenging boundary areas by guiding feature fusion with Canny edges and reinforcing key channel features via ECA. The overall architecture of EDM-UNet, illustrating the integration of the Canny-assisted edge module and ECA within the decoder, is presented in Figure 5.


> **Figure 5. EDM-UNet model architecture diagram.**

2.2.2. ECA Attention Mechanism

In order to address the challenges of segmentation in complex field environments, where soybean plants and co-occurring weeds exhibit high visual similarity and significant background interference, a U-Net–based model augmented with an ECA [28] mechanism is proposed. Despite the evident strengths of the classic U-Net architecture in semantic segmentation, particularly through its encoder–decoder structure and skip connections, which are effective in fusing multi-scale features to handle ambiguous boundaries, the equal-weight treatment of all feature channels may insufficiently emphasise the most informative channel dimensions for weed discrimination in highly heterogeneous farmland scenes. This may limit the model’s ability to capture subtle differences. In order to surmount this limitation, a lightweight ECA module is integrated into the skip connection paths of U- Net. The ECA mechanism employs a local cross-channel interaction strategy to adaptively learn channel-wise weight coefficients without reducing dimensionality, thereby enabling dynamic calibration and enhancement of key channel features. This design facilitates the network’s capacity to effectively suppress background noise and amplify discriminative channel information related to weeds. This enhancement in feature selectivity and fusion quality is achieved through the network’s ability to fuse multi-scale features extracted by the encoder. Furthermore, the lightweight nature of ECA ensures that computational efficiency is maintained. As illustrated in Figure 6, a schematic representation of the ECA module is provided for reference.

Agriculture 2025, 15, 2575 8 of 19


> **Figure 6. ECA Attention Mechanism.**

The basic process of ECA is as follows: Firstly, the input feature map is compressed in the spatial dimension through global average pooling to obtain a channel description vector of size 1 × 1 × C; Subsequently, Conv1D is utilized to conduct channel feature learning on this vector to capture the importance relationships among different channels. Compared with the traditional fully connected layer, Conv1D can significantly reduce the number of parameters, but it can only model local channel dependencies. To enhance the modelling ability of features at different scales, ECA introduces a dynamic convolution kernel mechanism, which adaptively adjusts the size of the convolution kernel based on the input features, thereby achieving efficient interaction and selective enhancement of information between different channels. Ultimately, the obtained channel attention weights are multiplied channel by channel with the original feature map to generate the output feature map with channel attention enhancement. Convolution and adaptive functions are defined as follows:

log2(C)

γ + b

k = ψ(C) =

, (3)

γ

odd

where k represents the size of the convolution kernel; C represents the number of channels;

||odd indicates that k can only take odd numbers. γ and b are adjustable hyperparameters, typically set to 2 and 1, used to change the ratio between the number of channels C and the size of the convolution kernels.

2.2.3. The Designed Post-Processing Module

In order to enhance the spatial-structural accuracy and field-adaptability of weed segmentation results, a lightweight yet effective structure-prior–guided post-processing module is proposed. This module is built upon the ResNet50-UNet predicted masks. The objective of this module is to rectify prediction errors arising in complex field scenarios, in- cluding blurred boundaries, object adhesion, and morphological distortions. The proposed methodology consists of two fundamental components: direction-consistency filtering and morphology-driven aspect-ratio selection. These components leverage domain knowledge of crop planting patterns and weed distribution, with the aim of reinforcing the structural plausibility and practical utility of segmentation outputs.

Firstly, in order to address the prevalent issues of texture confusion and edge drift in field images, a direction-consistency enhancement stage is introduced, based on a Gabor filter bank. Gabor filters are linear filters that exhibit high responsiveness to texture oriented along specific directions. These filters are widely used in texture analysis and biological vision modelling. It is notable that soybean plants cultivated in ridge-row arrangements demonstrate robust texture consistency along the primary planting direction. In contrast, weeds exhibit greater dispersion and weaker directional texture. To this end, a set of Gabor

Agriculture 2025, 15, 2575 9 of 19

kernels is constructed, encompassing four primary orientations: 0◦, 45◦, 90◦, and 135◦. The Gabor kernel Gθ(x, y) for an orientation θ is defined as:

−x′2 + γ2y′2

2πx′









λ + ψ

Gθ(x, y) = exp

cos

(4)

2σ2

where x′ = xcos θ + ysin θ, y′ = −xsin θ + ycos θ, λ denotes the wavelength, σ is the standard deviation, γ the spatial aspect ratio, and ψ the phase offset.

These filters are then applied to the preliminary binary segmentation mask. For each pixel region, the response is computed across the four orientations and the maximum direction-response map is extracted. Regions demonstrating significant directional consis- tency are retained as candidate target areas, while those lacking a clear directional signature are suppressed, thereby reducing mis-segmentation noise. As illustrated in Figure 7, the configuration of the four-orientation Gabor filter bank is presented schematically.

(A)  (B)  (C)  (D)


> **Figure 7. Gabor kernel filter bank. (A) Gabor 0◦; (B) Gabor 45◦; (C) Gabor 90◦; (D) Gabor 135◦.**

Secondly, in order to eliminate residual false positives and structurally anomalous regions, a geometry-based selection mechanism grounded in morphological constraints is designed. Following direction-consistency filtering, the identification of connected components is undertaken in the mask. For each candidate region, the minimum enclosing rectangle is computed, and the aspect ratio is derived. The methodology employed in this study is predicated on the analysis of geometric statistics ascertained from field-collected images of soybean and typical weed shapes. The establishment of morphological thresholds is then undertaken in order to discard regions whose aspect ratios deviate markedly from those expected of legitimate weeds. This filtration stage serves two primary functions: firstly, it eliminates false responses caused by shadows, soil fissures, or other non-target disturbances; and secondly, it enforces a geometric consistency constraint on the retained regions. This enhances the reliability of boundary structures in the final segmentation.

The proposed post-processing module integrates directional texture priors and morphology-based geometric filtering. This refinement of initial model predictions yields segmentation outputs with heightened spatial coherence and greater applicability to real- world agricultural scenarios.


## 3. Results and Analysis

3.1. Experimental Environment

The experiments were conducted using the PyTorch (version 1.10.0) framework, and the details of the experimental environment are provided in Table 1. The input image size was set to 512 × 512 pixels. The model hyperparameters were configured as follows: the batch size was 16, the optimizer leveraged stochastic gradient descent with an initial learning rate of 0.01, and the momentum parameter was set to 0.937. The learning rate was adjusted using the cosine annealing decay algorithm, with a decay coefficient of 0.0005.

Agriculture 2025, 15, 2575 10 of 19


> **Table 1. Test environment.**

Configuration Argument

CPU Intel(R) Xeon(R) Silver 4214R CPU @ 2.40GHz GPU NVIDIA GeForce RTX 3080 Ti 12G Operating system Ubuntu 20.04 Accelerating environment Cuda11.3 CUDNN 8.2.0 Development platform PyCharm Other Numpy1.17.0 Opencv4.1.0

Training comprised 300 epochs, with weight files saved every 50 epochs. A log file was also generated to record the loss values for the training and validation sets. These hyperparameters were carefully selected to ensure faster convergence, minimize overfitting, and prevent the model from becoming stuck in local minima. To ensure fairness, all comparative models in this study were trained and evaluated under identical hardware conditions and hyperparameter settings. The FPS values reported in this paper were obtained in PyTorch by repeatedly running 100 forward passes and computing the average inference speed.

3.2. Model Evaluation Index

The evaluation metrics for semantic segmentation models primarily include accu- racy indicators such as recall and precision, semantic segmentation performance metrics represented by MIoU, computational efficiency measured by FPS, and model complexity indicators represented by the number of parameters and floating point operations.

Accuracy metrics can be defined using a confusion matrix. For the soybean weed segmentation task, we designate weed features as the positive class and non-weed regions as the negative class, thereby distinguishing four categories: true negative (TN), false positive (FP), false negative (FN), and true positive (TP).

Based on the confusion matrix, the following evaluation metrics can be calculated: Recall represents the proportion of actual positive samples that are correctly identified as positive, as shown in Equation (5). Precision indicates the proportion of correctly predicted positive samples among all samples predicted as positive, as expressed in Equation (6).

Recall = TP TP + FN (5)

Precision = TP TP + FP (6)

The IoU measures the overlap between the predicted segmentation region and the ground-truth label region, defined as the ratio of the area of their intersection to the area of their union. The MIoU is computed as the arithmetic mean of the IoU values over all classes, as shown in Equation (7).

k ∑ i=0

MIoU = 1 k + 1

TP FN + FP + TP (7)

In the formula: k represents the number of categories, and k + 1 represents the number of categories containing background classes.

Furthermore, FPS is introduced as an indicator to measure the processing speed of the semantic segmentation network. In addition, Params denotes the number of trainable parameters in millions, and FLOPs denotes the number of floating-point operations per forward pass in billions. These two indicators are used to characterise the model’s com-

Agriculture 2025, 15, 2575 11 of 19

plexity and computational cost, which are critical for deployment in resource-constrained agricultural environments.

3.3. Ablation Test Results

In the soybean–weed segmentation task, in order to verify the effect of the proposed modules on the overall model performance, this study conducted a series of ablation exper- iments based on EDM-UNet, with the specific results shown in Table 2. The experiments progressively combined modules from three aspects—ECA attention mechanism, edge en- hancement, and morphological post-processing—to explore the impact of each module on the model’s MIoU, recall, precision, and FPS. Figure 8 shows the performance comparison of different combinations


> **Table 2. Ablation test.**

Test Baseline ECA Edge Detection Post-Processing MIoU (%) Recall (%) Precision (%) FPS

1 √ 82.74 87.86 91.75 51.61 2 √ √ 88.08 91.58 95.15 45.50 3 √ √ √ 88.37 92.23 94.80 39.46 4 √ √ 83.30 87.48 93.12 40.66 5 √ √ 87.79 92.14 94.11 48.70 6 √ √ √ 89.05 93.01 94.83 39.97 7 √ √ √ 87.78 91.59 94.72 49.19 8 √ √ √ √ 89.45 93.53 94.78 40.36

Note: A tick indicates the use of the improvement.


> **Figure 8. Ablation test performance of EDM-UNet with different component combinations.**

As demonstrated in Experiment 1, the initial ResNet50-UNet model exhibits an MIoU of 82.74%, a recall of 87.86%, a precision of 91.75%, and an FPS of 51.61, thereby estab- lishing a benchmark for comparison. In Experiment 2, following the incorporation of the lightweight ECA module, the FPS decreased to 45.50. However, the Recall and MIoU increased to 91.58% and 88.08%, respectively, while Precision reached its maximum value of 95.15%. The third experiment, which is based on the second experiment, introduces edge detection, thereby further enhancing feature representation. In comparison with Experiment 2, MIoU increased by 0.29 percentage points to 88.37%, Recall increased by 0.65 percentage points to 92.23%, Precision decreased slightly to 94.80%, and FPS dropped to 39.46. This finding indicates that the model exhibits enhanced recall capability and

Agriculture 2025, 15, 2575 12 of 19

improved segmentation accuracy. However, it is noteworthy that the implementation of the attention module may lead to a marginal increase in high-confidence background misclassi- fication probability, which in turn causes a modest decline in precision. In Experiment 4, the edge-detection module is introduced in addition to the module employed in Experiment 1. This is done with the objective of enhancing the quality of segmentation in regions adjacent to the boundary. The findings indicate an MIoU of 83.30%, a Recall of 87.48%, and a Precision of 93.12%, with FPS decreasing to 40.66. With the exception of a decline in FPS, MIoU and Precision demonstrate consistent improvements, while Recall remains at a comparable level, suggesting that this module can effectively mitigate boundary blurring issues and enhance the model’s capacity to detect pixels at target edges. Experiment 5, a development of Experiment 1, incorporates the morphological post-processing module, resulting in an augmentation of MIoU, Recall, and Precision by 5.05%, 4.28%, and 2.36%, respectively, accompanied by a decline in FPS by 2.91%. Despite a slight decline in FPS, there is a substantial enhancement in all the accuracy metrics of the model. This finding suggests that the application of morphological operations during post-processing of the model output is effective in the removal of small false-response regions, thereby enhancing the overall accuracy of segmentation. Notably, this module does not affect the backbone network structure, which results in minimal impact on computational complexity. In Ex- periment 6, the methodologies of Experiments 4 and 5 are amalgamated; that is to say, the implementation of morphological post-processing is undertaken on the basis of introducing edge enhancement, thereby effecting a further improvement in the model’s overall perfor- mance. The model demonstrates an MIoU of 89.05%, with Recall and Precision reaching 93.01% and 94.83%, respectively. These accuracy metrics exceed those achieved by edge enhancement or morphological post-processing alone, thus indicating that the combina- tion of both approaches results in enhanced segmentation outcomes, thereby validating the efficacy of the model improvements. Furthermore, the frame rate is 39.97, which is within the acceptable range. In Experiment 7, the ECA attention mechanism is integrated with the morphological post-processing module. This results in the achievement of good performance without the addition of structural complexity. The MIoU is 87.78%, the recall is 91.59%, and the precision reaches 94.72%. The FPS score of 49.19 is the highest among all groups, with the exception of the original model. Despite the fact that the metrics do not reach their optimum, this combination has been demonstrated to exhibit good balance, which renders it suitable for deployment in scenarios with high efficiency requirements. The final Experiment 8 is the comprehensive model, i.e., introducing ECA attention, edge enhancement, and morphological post-processing on the basis of the aforementioned mod- ules. The system’s overall performance has been found to reach an optimal level, with metrics such as MIoU, Recall and Precision all demonstrating satisfactory results within the acceptable range. The MIoU score attained was 89.45%, while the Recall and Precision metrics registered 93.53% and 94.78%, respectively. The system’s frame rate was found to be 40.36 FPS. A comparative analysis of the baseline model reveals that MIoU, Recall, and Precision exhibit an increase of 6.71%, 5.67%, and 3.03%, respectively. Notably, MIoU and Recall attain their maximum values among all combination models, while FPS experiences a decline of 11.25%. The comprehensive model demonstrates significant advantages in terms of accuracy, recall, and segmentation consistency, thus fully demonstrating the important role of collaborative fusion of modules in improving model performance.

The findings of the present study demonstrate that distinct modules have discernible impacts on diverse aspects of model performance enhancement. The ECA attention mecha- nism has been demonstrated to enhance the model’s responsiveness to key channel features, thereby improving both recall and MIoU. The edge enhancement module has been shown to improve the boundary quality of targets, thus enhancing the model’s overall detection

Agriculture 2025, 15, 2575 13 of 19

robustness. Finally, the morphological post-processing has been evidenced to effectively improve segmentation cleanliness and accuracy by optimising model outputs. The final combined improved model demonstrates both high accuracy and relatively low com- putational cost, rendering it suitable for practical soybean–weed segmentation tasks in agricultural environments.

3.4. Simulation Test

In the evaluation of deep learning models, the confusion matrix [29] is a pivotal tool for assessing classification performance. The model is presented as a matrix in which rows represent the true labels and columns represent the predicted labels. Each element of the matrix reflects the proportion or count of instances of a given true class being predicted as a particular class. Diagonal entries in the matrix indicate the proportion of correct classifications, while off-diagonal entries represent misclassifications. Perusal of the confusion matrix facilitates intuitive comprehension of the model’s false negatives and false positives for each class, thereby providing a framework for guiding improvements.

In the context of the binary segmentation task of soybean-field weed detection, the pri- mary focus is typically on the model’s capacity to differentiate between pixels categorised as either “background” or “weeds”. As demonstrated in Figure 9A, the normalized confusion matrix for the original model on the test set indicates that true background pixels are pre- dicted as background with a proportion of 1.00 and as weeds with 0.00, suggesting that the original model exhibits a high degree of accuracy in background recognition with no false positives. However, among true weed pixels, only 0.76 are correctly predicted as weeds and 0.24 are misclassified as background, indicating a high rate of false negatives. This phenomenon may be attributed to the similarity in colour, texture, or morphology between weeds and surrounding crop leaves, soil, or other vegetation. Additionally, boundary blurring or small-scale targets that are difficult to capture may also be contributing factors.

(A)  (B)


> **Figure 9. Confusion matrix. (A) Original model; (B) EDM-UNet.**

As demonstrated in Figure 9B, the confusion matrix for the enhanced EDM-UNet on the test set continues to predict 100% of true background pixels as background, with no additional background false positives. Among pixels classified as true weed pixels, the cor- rect prediction proportion increases to 0.87, while the misclassification rate as background decreases to 0.13. A comparison of the original model with the new model reveals a signifi- cant reduction in the false negative rate, from 24% to 13%. This represents an improvement of 11 percentage points. These results provide validation for the synergistic effect of the multiple improvement modules: EDM-UNet has been demonstrated to maintain high-

Agriculture 2025, 15, 2575 14 of 19

precision background recognition while significantly enhancing weed detection, especially in conditions of blurred boundaries, complex textures, and background interference.

The enhanced EDM-UNet model, while not resulting in a significant escalation in parameter count or inference cost, has been demonstrated to enhance the accuracy of weed segmentation in soybean fields and reduce the occurrence of false negatives. This enhancement is achieved through mechanisms such as ECA attention, edge detection, and morphological post-processing.

3.5. Detection Model Comparison Test

In the soybean–weed segmentation task, in order to validate the effectiveness of the proposed EDM-UNet model, a comparison was made against current mainstream semantic segmentation architectures—DeepLabv3+, U-Net, PSPNet, and ResNet50-UNet—under the same experimental settings; the detailed results are presented in Table 3. In order to further analyse the behaviour of the model, radar charts were plotted for MIoU, recall and precision across the five models (Figure 10).


> **Table 3. Comparison of weed detection results of soybeans in different models.**

Model MIoU (%) Recall (%) Precision (%) FPS Params (M) FLOPs (G)

DeepLabv3+ 81.83 93.15 85.73 77.34 5.813 52.867 U-Net 82.09 87.04 91.73 38.79 24.891 451.672 PSPNet 70.87 75.24 86.96 94.45 2.376 6.031 ResNet50-UNet 82.74 87.86 91.75 51.61 43.933 184.100 EDM-UNet 89.45 93.53 94.78 40.36 43.942 184.257


> **Figure 10. Radar charts of the performance of five different models.**

As demonstrated in Table 3 and Figure 10, EDM-UNet attains superior overall per- formance. Specifically, it attains an MIoU of 89.45%, a recall of 93.53%, and a precision of 94.78%. In comparison with DeepLabv3+, the following enhancements have been ob- served: an increase of 7.62% in MIoU, 0.38% in Recall, and 9.05% in Precision. In contrast with U-Net, enhancements of 7.36% in MIoU, 6.49% in Recall, and 3% in Precision have been identified. When compared with PSPNet, EDM-UNet improves MIoU, Recall, and Precision by 18.58, 18.29, and 7.82 percentage points, respectively. Additionally, when contrasted with the baseline ResNet50-UNet model, significant advancements of 6.71% in MIoU, 5.67% in recall, and 3.03% in precision were observed. These gains demonstrate the advantages of EDM-UNet in terms of pixel-level classification accuracy and detection capability, indicating a marked enhancement in region-wise segmentation precision.

Agriculture 2025, 15, 2575 15 of 19

In terms of computational complexity, EDM-UNet reaches 40.36 FPS, which is 11.25 FPS lower than the baseline ResNet50-UNet. The parameter count and FLOPs of EDM-UNet are very close to those of ResNet50-UNet: EDM-UNet has 43.942 million parameters and 184.257 GFLOPs, while the baseline has 43.933 million parameters and 184.100 GFLOPs. Although DeepLabv3+ and PSPNet run faster than EDM-UNet and re- quire fewer parameters and operations, with 5.813 million parameters and 52.867 GFLOPs for DeepLabv3+ and 2.376 million parameters and 6.031 GFLOPs for PSPNet, the substan- tial improvements in accuracy and segmentation quality achieved by EDM-UNet make this computational cost acceptable. In addition, compared with U-Net, EDM-UNet not only achieves better performance on all evaluation metrics, but also reduces the FLOPs from 451.672 G to 184.257 G while maintaining a reasonable parameter scale and inference speed. In summary, the proposed EDM-UNet model significantly enhances the accuracy and robustness of soybean–weed segmentation without incurring excessive complexity or computational cost. The device’s superior comprehensive performance and practical infer- ence speed make it well suited for deployment in agricultural scenarios where resources are limited.

3.6. Detection Performance in Complex Natural Scenes

The present study evaluates the performance of various models in three different scenarios relating to weed density: sparse weeds, moderate weeds and dense weeds. The aim is to compare the segmentation results of DeepLabv3+, U-Net, PSPNet, ResNet50-U- Net and EDM-UNet on images of soybeans and weeds. The collated dataset encompasses imagery of soybean plants exhibiting diverse weed conditions. The segmentation outcomes for sparse-weed cases by EDM-UNet and the other four networks are shown in Figure 11. As demonstrated in Figure 11, U-Net, ResNet50-UNet, and EDM-UNet achieve high detection rates in the presence of sparse weeds. In contrast, the DeepLabv3+ and PSPNet models exhibited a high rate of false positives, with the PSPNet model in particular misclassifying a significant number of soybean plants as weeds.

(A)  (B)  (C)  (D)  (E)  (F)  (G)


> **Figure 11. Examples of the detection effects of five different models on soybean seedlings with**

> different degrees of weeds. (A) Original image; (B) Labeled image; (C) DeepLabv3+; (D) U-Net;
(E) PSPNet; (F) ResNet50-UNet; (G) EDM-UNet.

In scenarios involving moderate weed levels, the PSPNet system frequently misidenti- fies soybean plants as weeds, while also failing to detect a significant number of weeds. Despite the absence of false positives in U-Net and ResNet50-UNet, their capacity for weed segmentation remains limited, consequently yielding low segmentation accuracy. It was observed that both the DeepLabv3+ and EDM-UNet models exhibited a tendency to overlook diminutive weeds located on the right-hand side of the images. These diminutive

Agriculture 2025, 15, 2575 16 of 19

targets presented a considerable challenge in terms of capture, a consequence of the flight altitude constraints imposed on the UAV.

In conditions of dense vegetation, the performance of PSPNet, U-Net, and ResNet50- UNet is characterised by a persistent propensity to generate false positives and false negatives. DeepLabv3+ has been observed to occasionally merge multiple instances of weeds into a single region. Conversely, EDM-UNet attains the highest detection rate, with a low false negative rate, but misses only extremely small weed instances.

EDM-UNet demonstrates a significant enhancement in segmentation performance in comparison with the original ResNet50-UNet. In contrast to the performance of PSPNet, which exhibits severe false positives by misclassifying soybeans as weeds, and in contrast to the performance of U-Net and ResNet50-UNet, which suffer from pronounced false negatives and low accuracy across weed scenarios, EDM-UNet—with its ECA attention mechanism—precisely focuses on critical features and effectively avoids misclassifying soybeans as weeds. In comparison with DeepLabv3+, which has the capacity to merge adjacent weed regions in cases of dense conditions, EDM-UNet’s integrated edge-detection module enhances boundary recognition, and its innovative post-processing function sup- presses noisy misclassifications arising from irregular weed orientations while removing geometrically implausible false positives. Consequently, EDM-UNet maintains a high weed detection rate and, in both moderate and dense weed scenarios, yields segmentation results with superior accuracy, purity, and shape conformity relative to U-Net, ResNet50-UNet, PSPNet, and DeepLabv3+. The capture of weeds at high altitudes by means of UAVs is a challenging process, with only extremely small weeds proving difficult to capture.

In conclusion, EDM-UNet has been demonstrated to exhibit both robust and effective soybean–weed segmentation capabilities across a range of weed densities. This renders it well suited for deployment in complex field environments.


## 4. Discussion

4.1. Model Performance Discussion

In order to validate the performance of the enhanced soybean–weed segmentation model in field environments, a series of comparative experiments, ablation studies and visualisation analyses were conducted. The findings of the comparative experiments demonstrate that EDM-UNet achieves the highest mean intersection over union, precision, and recall; although its frames per second is not the highest, the reduction in inference speed remains acceptable, and its accuracy markedly exceeds that of other models while still satisfying real-time requirements. In the present experiments, the proposed method attains an MIoU of 89.45% for soybean weed detection in field conditions, representing a 16.65 percentage-point improvement over the CNN–Transformer–based UAV rice-field weed segmentation approach by Guo et al. [30]. In comparison with the MobileNetV4- Seg model proposed by Md Didarul et al. [31]—which achieved 76.8% Intersection Over Union (IoU), 83.8% Precision, and 90.2% Recall on a self-collected dataset—EDM-UNet improves IoU, Precision, and Recall by 12.65, 10.98, and 3.33 percentage points, respectively. The findings substantiate the hypothesis that the proposed EDM-UNet model offers a substantial advantage for the identification of soybean weeds in real-world field settings.

It should be noted that although EDM-UNet does not achieve the optimal performance in terms of FPS, Params, and FLOPs compared with some lightweight models, this is mainly due to the integration of multiple enhancement components, including the ECA attention mechanism, edge detection module, and the post-processing module. These modules inevitably increase computational overhead but are deliberately introduced to enhance boundary discrimination, suppress background interference, and enforce geometric consis- tency in complex field environments. This reflects a conscious design trade-off in which

Agriculture 2025, 15, 2575 17 of 19

segmentation reliability and agricultural applicability are prioritized over maximal com- putational throughput. In practice, EDM-UNet achieves an inference speed of 40.36 FPS, with 43.942 million parameters and 184.257 GFLOPs, which sufficiently satisfies real-time deployment requirements in UAV-based precision agriculture. Although these indicators are not the lowest among all compared models, the achieved processing speed remains fully adequate to support real-time agronomic intervention. Overall, EDM-UNet provides a favorable balance between segmentation accuracy and computational efficiency, making it well suited for integration into UAV-enabled intelligent weed management systems.

4.2. Limitations and Solutions

The proposed enhanced EDM-UNet model has been shown to exhibit high levels of accuracy and robustness in the context of soybean–weed image segmentation. The integration of lightweight attention mechanisms, edge detection, and morphological post- processing modules within the model has been demonstrated to result in substantial enhancements in MIoU, Precision, and Recall. This integration serves to effectively mitigate the adverse effects of complex field backgrounds on segmentation accuracy. Nevertheless, despite its overall strong performance, certain limitations remain, as outlined below:

1. The present study explores the issue of suboptimal segmentation of small weed targets. The results of the visualisation and quantitative metrics demonstrate that there is still potential for enhancement of the model’s performance with regard to small weeds. It has been demonstrated that minor targets are susceptible to being either disregarded or overlooked in high-level semantic feature maps. Furthermore, during the process of feature fusion, the model may be incapable of adequately preserving their information, which can result in missed detections or incomplete segmentation. In order to address this issue, it is recommended that future research endeavours involve the exploration of the incorporation of a dedicated small-object detection head or local enhancement mechanisms that are specifically designed to bolster features in small regions. Furthermore, the incorporation of fine-grained attention modules within lower-level feature maps has the potential to enhance the model’s sensitivity to edge details and subtle texture variations. 2. The absence of a transfer learning strategy during the training process is a key issue that should be addressed. In this study, training was performed from the beginning, which limits the model’s initial feature-extraction capability. Training from the be- ginning typically necessitates substantial amounts of annotated data for the purpose of acquiring robust low-level visual features, such as edges, textures, and shapes. However, the soybean–weed dataset under consideration is comparatively limited in scope. Consequently, the model may encounter difficulties in the early training stage in terms of effectively learning generalizable visual primitives. This may result in increased convergence difficulty and potentially unstable performance in complex backgrounds or on unseen samples. It is suggested that future work should involve the following: Initially, pretraining on large-scale general segmentation datasets or plant phenotyping image collections. Subsequently, the transfer of these pretrained weights to the soybean–weed segmentation task via transfer learning. This approach has the potential to enhance learning efficiency and robustness in circumstances where data is limited, to reduce the time required for training, and to improve adaptability to a range of field scenarios. 3. While the present study demonstrates the strong performance of EDM-UNet in a single soybean production system at one experimental site, the robustness of the model across diverse agroecological conditions and cropping systems has not yet been explicitly verified. To address this, a multi-location, multi-crop validation campaign

Agriculture 2025, 15, 2575 18 of 19

will be designed for future work, incorporating fields from different regions with varying climates, soil types and management practices. The application will also be extended to other major crops, such as maize and wheat. Additionally, domain adaptation and transfer learning strategies will be explored to improve the method’s generalisation across sites and crops on these heterogeneous datasets. These multi-site, multi-crop experiments will enable a more systematic evaluation of the robustness of the proposed method and demonstrate its potential for deployment in agriculture on a broader scale than the current single-location, single-crop scenario.


## 5. Conclusions

In this study, we employed UAV-based remote sensing to collect images of soybean fields containing weeds. We then constructed a soybean–weed segmentation dataset and developed the EDM-UNet model for precise weed segmentation.

We integrated a lightweight ECA attention module, Canny-based edge guidance in the decoder, and a dual-constraint post-processing stage to strengthen boundary recognition and suppress non-target artefacts. The experimental findings on the test set demonstrate that the proposed EDM-UNet attains a MIoU of 89.45%, a recall of 93.53%, and a precision of 94.78%. With regard to the speed of inference, the system achieves 40.36 FPS, thus meeting the real-time detection requirements. EDM-UNet has been shown to enhance MIoU, Recall, and Precision by 6.71%, 5.67%, and 3.03%, respectively, while demonstrating an acceptable FPS reduction of 11.25% when compared with the baseline ResNet50-UNet. Visualisation analyses confirm that the model exhibits high efficiency in segmenting weeds in soybean fields and is therefore suitable for practical deployment. The proposed method has the potential to reduce the financial burden of manual inspection and to provide essential decision support for variable-rate spraying systems. To broaden applicability, future work will pursue transfer learning and domain-adaptation to improve cross-site and cross-crop generalization, and will investigate model compression and edge-deployment for true onboard, real-time UAV operation.

Author Contributions: J.G.: Writing—Original draft, Software, Methodology, Formal analysis, Validation, Data curation. F.T.: Project administration, Funding acquisition, Resources. X.L.: Data curation. All authors have read and agreed to the published version of the manuscript.

Funding: This research was funded by the National Key R&D Program of China (2023YFD2301605), the Heilongjiang Natural Science Foundation Project (LH2023F043).

Data Availability Statement: The original contributions presented in this study are included in the article; further inquiries can be directed to the corresponding author.

Conflicts of Interest: The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.


## References

1. Chhokar, R.S.; Balyan, R.S. Competition and control of weeds in soybean. Weed Sci. 1999, 47, 107–111. [CrossRef] 2. Horneburg, B.; Seiffert, S.; Schmidt, J.; Messmer, M.M.; Wilbois, K.-P. Weed tolerance in soybean: A direct selection system. Plant Breed. 2017, 136, 372–378. [CrossRef] 3. Harre, N.T.; Young, B.G. Early-season nutrient competition between weeds and soybean. J. Plant Nutr. 2020, 43, 1887–1906. [CrossRef] 4. Liu, T.; Jin, X.; Han, K.; He, F.; Wang, J.; Chen, X.; Kong, X.; Yu, J. Semantic segmentation for weed detection in corn. Pest Manag. Sci. 2025, 81, 1512–1528. [CrossRef] 5. Qi, M.; Gao, H.; Wang, T.; Du, B.; Li, H.; Zhong, W.; Tang, Y. Method for Segmentation of Bean Crop and Weeds Based on Improved UperNet. IEEE Access 2023, 11, 143804–143814. [CrossRef] 6. Genze, N.; Wirth, M.; Schreiner, C.; Ajekwe, R.; Grieb, M.; Grimm, D.G. Improved weed segmentation in UAV imagery of sorghum fields with a combined deblurring segmentation model. Plant Methods 2023, 19, 87. [CrossRef] [PubMed]

Agriculture 2025, 15, 2575 19 of 19

7. Zou, K.; Wang, H.; Yuan, T.; Zhang, C. Multi-species weed density assessment based on semantic segmentation neural network. Precis. Agric. 2022, 24, 458–481. [CrossRef] 8. Guo, Z.; Xue, Y.; Wang, C.; Geng, Y.; Lu, R.; Li, H.; Sun, D.; Lou, Z.; Chen, T.; Shi, J.; et al. Efficient weed segmentation in maize fields: A semi-supervised approach for precision weed management with reduced annotation overhead. Comput. Electron. Agric. 2024, 229, 109707. [CrossRef] 9. Ma, X.; Deng, X.; Qi, L.; Jiang, Y.; Li, H.; Wang, Y.; Xing, X. Fully convolutional network for rice seedling and weed image segmentation at the seedling stage in paddy fields. PLoS ONE 2019, 14, e0215676. [CrossRef] 10. Janneh, L.L.; Zhang, Y.; Cui, Z.; Yang, Y. Multi-Level Feature Re-weighted fusion for the Semantic Segmentation of Crops and weeds. J. King Saud Univ. Comput. Inf. Sci. 2023, 35, 101545. [CrossRef] 11. Nong, C.; Fan, X.; Wang, J. Semi-supervised Learning for Weed and Crop Segmentation Using UAV Imagery. Front. Plant Sci. 2022, 13, 927368. [CrossRef] 12. You, J.; Liu, W.; Lee, J. A DNN-based semantic segmentation for detecting weed and crop. Comput. Electron. Agric. 2020, 178, 105750. [CrossRef] 13. Han, X.; Wang, H.; Yuan, T.; Zou, K.; Liao, Q.; Deng, K.; Zhang, Z.; Zhang, C.; Li, W. A rapid segmentation method for weed based on CDM and ExG index. Crop. Prot. 2023, 172, 106321. [CrossRef] 14. Kong, X.; Liu, T.; Chen, X.; Jin, X.; Li, A.; Yu, J. Efficient crop segmentation net and novel weed detection method. Eur. J. Agron. 2024, 161, 127367. [CrossRef] 15. Yu, H.; Che, M.; Yu, H.; Ma, Y. Research on weed identification in soybean fields based on the lightweight segmentation model DCSAnet. Front. Plant Sci. 2023, 14, 1268218. [CrossRef] [PubMed] 16. Kong, X.; Li, A.; Liu, T.; Han, K.; Jin, X.; Chen, X.; Yu, J. Lightweight cabbage segmentation network and improved weed detection method. Comput. Electron. Agric. 2024, 226, 109403. [CrossRef] 17. Gao, H.; Qi, M.; Du, B.; Yang, S.; Li, H.; Wang, T.; Zhong, W.; Tang, Y. An accurate semantic segmentation model for bean seedlings and weeds identification based on improved ERFnet. Sci. Rep. 2024, 14, 12288. [CrossRef] [PubMed] 18. Lan, Y.; Huang, K.; Yang, C.; Lei, L.; Ye, J.; Zhang, J.; Zeng, W.; Zhang, Y.; Deng, J. Real-Time Identification of Rice Weeds by UAV Low-Altitude Remote Sensing Based on Improved Semantic Segmentation Model. Remote Sens. 2021, 13, 4370. [CrossRef] 19. Li, Y.; Guo, R.; Li, R.; Ji, R.; Wu, M.; Chen, D.; Han, C.; Han, R.; Liu, Y.; Ruan, Y.; et al. An improved U-net and attention mechanism-based model for sugar beet and weed segmentation. Front. Plant Sci. 2025, 15, 1449514. [CrossRef] 20. Bakhshipour, A.; Jafari, A.; Nassiri, S.M.; Zare, D. Weed segmentation using texture features extracted from wavelet sub-images. Biosyst. Eng. 2017, 157, 1–12. [CrossRef] 21. Xu, B.; Fan, J.; Chao, J.; Arsenijevic, N.; Werle, R.; Zhang, Z. Instance segmentation method for weed detection using UAV imagery in soybean fields. Comput. Electron. Agric. 2023, 211, 107994. [CrossRef] 22. Torralba, A.; Russell, B.C.; Yuen, J. LabelMe: Online Image Annotation and Applications. Proc. IEEE 2010, 98, 1467–1484. [CrossRef] 23. Olaf, R.; Philipp, F.; Thomas, B. U-Net: Convolutional Networks for Biomedical Image Segmentation. arXiv 2015, arXiv:1505.04597. [CrossRef] 24. Shelhamer, E.; Long, J.; Darrell, T. Fully Convolutional Networks for Semantic Segmentation. IEEE Trans. Pattern Anal. Mach. Intell. 2016, 39, 640–651. [CrossRef] [PubMed] 25. Kaiming, H.; Xiangyu, Z.; Shaoqing, R.; Jian, S. Deep Residual Learning for Image Recognition. arXiv 2015, arXiv:1512.03385. [CrossRef] 26. Canny, J. A computational approach to edge detection. IEEE Trans. Pattern Anal. Mach. Intell. 1986, PAMI-8, 679–698. [CrossRef] 27. Gabor, D. Theory of communication. Part 1: The analysis of information. J. Inst. Electr. Eng. 1946, 93, 429–441. [CrossRef] 28. Qilong, W.; Banggu, W.; Pengfei, Z.; Peihua, L.; Wangmeng, Z.; Qinghua, H. ECA-Net: Efficient Channel Attention for Deep Convolutional Neural Networks. arXiv 2019, arXiv:1910.03151. 29. Sokolova, M.; Lapalme, G. A systematic analysis of performance measures for classification tasks. Inf. Process. Manag. 2009, 45, 427–437. [CrossRef] 30. Guo, Z.; Cai, D.; Jin, Z.; Xu, T.; Yu, F. Research on unmanned aerial vehicle (UAV) rice field weed sensing image segmentation method based on CNN-transformer. Comput. Electron. Agric. 2024, 229, 109719. [CrossRef] 31. Md Didarul, I.; Wenxin, L.; Pascal, I.; Puranjit, S.; Chong, Y.; Benjamin, R.; Kuan, Z.; Amit, J.J.; Stevan, K.; Yufeng, G.; et al. Towards real-time weed detection and segmentation with lightweight CNN models on edge devices. Comput. Electron. Agric. 2025, 237, 110600. [CrossRef]

Disclaimer/Publisher’s Note: The statements, opinions and data contained in all publications are solely those of the individual author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to people or property resulting from any ideas, methods, instructions or products referred to in the content.
