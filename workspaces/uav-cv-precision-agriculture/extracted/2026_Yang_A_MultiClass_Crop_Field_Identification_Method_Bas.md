---
workspace_id: SCI-001128
doi: 10.3390/agriculture16101108
title: "A Multi-Class Crop Field Identification Method Based on Semantic\u2013SAM\
  \ Fusion and UAV RGB Imagery"
authors:
- family_name: Yang
  given_name: Haoran
  orcid: null
- family_name: Wang
  given_name: Xinjun
  orcid: null
- family_name: Liang
  given_name: Qingfu
  orcid: null
- family_name: Huang
  given_name: Shuhan
  orcid: null
- family_name: Wang
  given_name: Panfeng
  orcid: null
- family_name: Sheng
  given_name: Jiandong
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:35:00.885774+00:00'
---

# A Multi-Class Crop Field Identification Method Based on Semantic–SAM Fusion and UAV RGB Imagery

Article A Multi-Class Crop Field Identification Method Based on

Semantic–SAM Fusion and UAV RGB Imagery

Haoran Yang, Xinjun Wang *, Qingfu Liang, Shuhan Huang, Panfeng Wang and Jiandong Sheng

Xinjiang Key Laboratory of Soil and Plant Ecological Processes, Xinjiang Engineering Technology Research Center of Soil Big Data, College of Resources and Environment, Xinjiang Agricultural University, Urumqi 830052, China; 320233735@stu.xjau.edu.cn (H.Y.); liangafu1751@163.com (Q.L.); 320233712@stu.xjau.edu.cn (S.H.); 17833125774@163.com (P.W.); sjd@xjau.edu.cn (J.S.) * Correspondence: wangxj@xjau.edu.cn


## Abstract

Accurate parcel-level crop field information is essential for precision agriculture, field management, and crop monitoring based on Unmanned Aerial Vehicle (UAV) imagery. However, it remains difficult to achieve both reliable crop-type recognition and fine bound- ary delineation from UAV RGB imagery. Although deep learning-based semantic segmen- tation models can effectively identify crop types, they often produce coarse or incomplete boundaries. The Segment Anything Model (SAM) can produce high-quality boundaries, but it depends on manual prompts and lacks semantic recognition ability, which limits its use in large-scale automatic mapping. To address this issue, this study proposes a parcel-level crop field identification framework based on Semantic–SAM fusion, enabling automatic semantic recognition and fine boundary extraction without manual prompts. Based on UAV RGB remote sensing imagery, this study developed a two-stage Semantic– SAM framework. Semantic segmentation models, including DeepLabv3+, U-Net, HRNet, and PSPNet, were first used to generate initial results. Then, bounding boxes or internal high-confidence points were extracted from the initial field regions as prompts for SAM to refine the segmentation. The final results preserved crop category information while producing finer boundaries. To evaluate the framework, this study compared four semantic segmentation models and their Semantic–SAM versions on the same-region test set, and further tested their spatial generalization ability on the different-region test set. The results showed that the Semantic–SAM framework provided more consistent gains in boundary quality, with regional recognition accuracy improving in several models and test scenarios. On the same-region test set, the PSPNet-based framework showed clear improvement, with mean Intersection over Union (mIoU) increasing from 78.99% to 83.13% under point- box prompts. The U-Net-based framework achieved the best mIoU of 87.09% with box prompts. On the different-region test set, the DeepLabv3+-based framework showed the largest gain in spatial generalization, with mIoU increasing from 67.22% to 73.45% under point-box prompts. Overall, the PSPNet-based fusion framework showed a better balance in accuracy, boundary quality, and robustness under different-region conditions. These results demonstrate that Semantic–SAM fusion supports automatic multi-class crop field mapping and boundary refinement from UAV RGB imagery without manual prompts or SAM fine-tuning, providing a practical approach for parcel-level crop monitoring and precision agriculture applications.

Academic Editors: Emmanouil

Psomiadis and Nicholas Dercas

Received: 20 April 2026

Revised: 12 May 2026

Accepted: 15 May 2026

Published: 18 May 2026

Copyright: © 2026 by the authors.

Licensee MDPI, Basel, Switzerland.

Keywords: UAV RGB imagery; precision agriculture; parcel-level crop mapping; semantic segmentation; Segment Anything Model (SAM)

This article is an open access article

distributed under the terms and

conditions of the Creative Commons

Attribution (CC BY) license.

Agriculture 2026, 16, 1108 https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 2 of 32


## 1. Introduction

Accurate parcel-level crop field mapping requires both reliable crop-type classification and precise field boundary delineation. For precision agriculture, crop type labels support planting structure statistics, yield estimation, and field management, while accurate bound- aries determine whether these information products can be used at the parcel scale [1,2]. Unmanned Aerial Vehicle (UAV) remote sensing provides centimeter-level spatial resolu- tion, flexible image acquisition, and low-cost repeated observation, and UAV RGB imagery has become an important data source for field-scale crop monitoring [3]. However, crop fields in high-resolution UAV RGB imagery often show similar spectral responses, complex row textures, fragmented boundaries, and adjoining parcels. These characteristics make it difficult to achieve both correct crop recognition and fine boundary extraction in a single automatic workflow. Semantic segmentation models, such as Fully Convolutional Network (FCN) [4], U-Net [5], and DeepLabv3+ [6], can learn multi-level image features and assign crop categories at the pixel level [7]. However, their outputs often contain rough edges, local omissions, and incomplete field contours. The Segment Anything Model (SAM) [8] has shown strong zero-shot segmentation ability in remote sensing applications [9], but it does not provide crop semantic labels and usually depends on manual or externally defined prompts. Although deep learning has also been used in related remote sensing tasks, such as change detection [10] and scene classification [11], these tasks do not fully address the coupled requirement of crop semantic recognition and fine field boundary delineation. UAV-based precision agriculture therefore requires methods that can provide both reliable crop labels and accurate parcel boundaries for field-scale monitoring and management [12].

Existing studies related to this problem can be broadly categorized into three groups: traditional machine learning methods, deep learning-based semantic segmentation models, and prompt-driven foundation segmentation models.

The first category is traditional machine learning methods. Early remote sensing classification often relied on object-based image analysis (OBIA), in which spectral, texture, and shape features were manually extracted from images and field samples to support crop classification and field extraction [13]. Duro et al. [14] and Maxwell et al. [15] showed that hand-crafted spectral, texture, and shape features have been widely used for crop recognition and field extraction. Belgiu et al. [16] and Mountrakis et al. [17] further indicated that machine learning methods, such as Random Forest and Support Vector Machine (SVM), can perform stably when suitable features and samples are available, but their accuracy still depends strongly on feature design and sample quality. These methods are simple and computationally efficient when image features are clearly separable, making them useful baselines for crop recognition and field extraction. However, in complex UAV RGB farmland imagery, land-cover heterogeneity, similar crop colors, and irregular field boundaries can reduce their adaptability and generalization ability. This limitation has promoted the development of more automated feature-learning methods.

The second category is deep learning-based semantic segmentation models. End-to- end networks, such as FCN, U-Net, and DeepLabv3+, can automatically learn multi-level and multi-scale features from original image bands and pixel-level labels, enabling pixel- level crop classification and field extraction [4–6]. In agricultural scenes, Waldner et al. [18] and Zhang et al. [19] explored boundary-related strategies, including boundary constraints and post-processing workflows, to improve field-boundary stability and connectivity. Maggiori et al. [20] and Persello et al. [21] further showed that deep learning models in agricultural remote sensing still face challenges such as dependence on labeled data, rough boundaries, and limited cross-domain generalization. Compared with traditional machine learning, deep learning-based semantic segmentation models reduce the dependence on

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 3 of 32

expert-designed features and improve crop semantic discrimination through automatic feature learning. However, they still require many pixel-level labels for training, and their outputs often contain rough or inaccurate field boundaries, especially in high-resolution UAV imagery with complex textures [22]. Further boundary refinement is still needed for accurate parcel-level crop mapping.

The third category is prompt-driven general segmentation models, with SAM as a typical example. SAM is a general segmentation foundation model that can generate high-quality instance masks from simple prompts, such as points and boxes, giving it strong zero-shot segmentation and boundary extraction ability [8]. Osco et al. [9], Tripathy et al. [23], and Ferreira et al. [24] showed that SAM has good potential for remote sensing and field-boundary extraction, while also emphasizing the importance of prompt design and data preprocessing. Zhang et al. [25] and Dong et al. [26] further indicated that SAM still has limitations in automated farmland mapping, particularly in prompt reliability and semantic consistency. Although SAM can generate clear and high-quality instance- level boundaries without task-specific training, its zero-shot outputs cannot be directly associated with crop categories. In complex farmland scenes, over-segmentation, under- segmentation, or cross-field merging may lead to fragmented or incorrectly connected field boundaries. Its performance also depends heavily on the quality and location of prompts. Despite its advantage in boundary refinement, the lack of crop semantic recognition and reliable prompt guidance limits its direct application to accurate multi-class farmland mapping [25–27]. These limitations indicate the need for semantic prompts to guide SAM- based boundary refinement.

In summary, current methods are still insufficient for multi-class crop field mapping from UAV RGB imagery. They often cannot achieve both accurate crop category recognition and fine parcel boundary delineation. Traditional machine learning methods rely on hand-crafted features, so they are sensitive to similar crop colors, complex row textures, and irregular field boundaries. Semantic segmentation models can identify crop category labels, but their boundaries are often coarse or broken. SAM can accurately delineate object boundaries, but it cannot recognize crop categories by itself. Therefore, this study proposes a complementary Semantic–SAM fusion framework. This framework combines the semantic recognition ability of segmentation models with the strong segmentation ability of SAM for multi-class crop field identification.

To address the difficulty of achieving both reliable crop-type recognition and fine boundary delineation from UAV RGB imagery, this study proposes a “Semantic–SAM” framework for parcel-level multi-class crop field mapping. The study focuses on typical agricultural fields in Changji City, Xinjiang, and constructs a multi-class crop dataset based on UAV RGB imagery. Comparative experiments were designed under both same- region and different-region conditions to evaluate segmentation accuracy, boundary quality, spatial generalization, and computational efficiency. The specific objectives were: (1) to assess whether the proposed framework can improve both crop recognition and boundary delineation compared with standalone semantic segmentation models; (2) to compare point, box, and point-box prompts and identify a more suitable automatic prompting strategy; and (3) to evaluate the applicability of the framework for parcel-level crop mapping and management-oriented precision agriculture applications. To support quantitative comparison, mean Intersection over Union (mIoU) and macro-averaged F1-score (mF1) were used as the main regional metrics, while boundary mean Intersection over Union (bmIoU) and boundary mean F1-score (bmF1) were used as the main boundary metrics for evaluating standalone segmentation models, Semantic–SAM-based models, prompt forms, and future improvements.

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 4 of 32


## 2. Materials and Methods

2.1. Overview of the Study Area

As shown in Figure 1, the study area is located in Changji City, Changji Hui Au- tonomous Prefecture, Xinjiang Uygur Autonomous Region, China. Situated at the northern foot of the Tianshan Mountains (86◦55′–88◦20′ E, 43◦27′–44◦37′ N), this region belongs to the Economic Belt on the Northern Slope of the Tianshan Mountains. The climate is charac- terized as temperate continental arid to semi-arid [28,29], with annual precipitation ranging from 180 to 250 mm [30]. Evaporation exceeds precipitation [31], and the annual sunshine duration is 2800–3000 h. The frost-free period lasts approximately 170–200 days, making the region suitable for both dryland and irrigated crops [32]. The study area is representative of irrigated agricultural fields in northern Xinjiang. Its crop parcels are mainly regular or semi-regular, but their boundaries are frequently defined by ridges, tractor roads, irrigation canals, narrow bare-soil strips, and fragmented or irregular edges. These features provide useful boundary information, but they may also cause local boundary discontinuities, false edges, or cross-parcel merging in UAV RGB imagery. Cotton, tomato, and corn are common crops in northern Xinjiang and usually show mulched drip-irrigation patterns and row textures. Under similar growth stages, illumination conditions, and soil backgrounds, their color and texture differences may become weak. Therefore, this region provides a representative and challenging scene for evaluating whether the proposed Semantic–SAM framework can preserve crop semantic labels while refining fine parcel boundaries.


> **Figure 1. Overview of the study area. (a) Experimental sites. (b) Experimental crop field and**

> experimental design.

2.2. UAV Remote Sensing Data Acquisition and Processing 2.2.1. Data Acquisition

In this study, RGB imagery was acquired using a DJI Matrice 300 RTK (M300 RTK) UAV with Real-Time Kinematic (RTK) positioning capability (DJI Innovation Technology Co., Ltd., Shenzhen, China). The UAV was equipped with a Zenmuse H20T camera (DJI Innovation Technology Co., Ltd., Shenzhen, China). The M300 RTK UAV was selected because of its high-precision RTK positioning capability, stable flight performance, and suitability for repeated UAV surveys and orthomosaic generation in farmland environments. The Zenmuse H20T camera was selected because it is highly compatible with the M300

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 5 of 32

RTK UAV and can provide stable RGB image acquisition during field surveys. Although the H20T payload includes multiple sensors, only RGB images were used because this study aimed to evaluate a low-cost and widely available crop field identification method based on UAV RGB imagery.

Data collection was conducted under clear-sky conditions from 12:00 to 15:00 to reduce illumination and shadow variation. Flights were performed when wind speed was lower than 3 m/s to reduce wind-induced blur, canopy displacement, geometric distortion, and unstable boundary visibility in UAV RGB imagery. The flight altitude was set to 120 m, con- sidering the common UAV flight-height limit, to balance spatial detail, coverage efficiency, and the preservation of field boundary and row-texture information. Forward and side overlaps were both set to 80% to provide sufficient image redundancy for aerial triangula- tion and orthomosaic generation. UAV RGB data were acquired from three 800 m × 800 m sampling plots (A, B, and C) between April and August 2024 at approximately 14-day intervals. All plots contained the target crop types, including tomato, cotton, and corn, together with other field types. A summary of the main imaging parameters is provided in Table 1.


> **Table 1. Flight and Imaging Parameters.**

Primary Parameters Values

UAV platform DJI Matrice 300 RTK (M300 RTK) Payload sensor DJI Zenmuse H20T

RTK positioning accuracy Horizontal: 1 cm + 1 ppm; Vertical: 1.5 cm

+ 1.5 ppm (with RTK Fix) Flight area extent 800 m × 800 m Gimbal pitch angle Nadir viewing angle Flight time window 12:00–15:00 Maximum flight speed Maximum Speed: 5 m/s (P-mode) Side overlap 80% Forward overlap 80% Flight altitude 120 m Ground Sampling Distance (GSD) 0.10 m/px

2.2.2. Data Preprocessing

Aerotriangulation and orthomosaic generation were performed using Pix4Dmapper software (version 4.5.6, Pix4D S.A., Prilly, Switzerland). After verifying the data qual- ity via the quality report, the RGB orthomosaics were exported and converted to 8-bit format to meet the requirements of subsequent processing. As shown in Figure 2, con- sidering practical deployment and limited computational resources, the imagery was normalized to a uniform scale. The original images were downsampled at a 5:1 ratio from 20,480 × 20,480 pixels to 4096 × 4096 pixels, with the GSD adjusted from 0.10 m/pixel to 0.50 m/pixel. To balance I/O performance and storage overhead, the downsampled GeoTIFF files were exported as high-quality JPEGs for model input.


> **Figure 2. Data acquisition and processing.**

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 6 of 32

The 5:1 downsampling was adopted to balance spatial detail and computational feasibility. The original orthomosaic contained 20,480 × 20,480 pixels, approximately 419.43 million pixels, whereas the downsampled image contained 4096 × 4096 pixels, approximately 16.78 million pixels. Thus, the number of pixels was reduced to about 4% of the original data volume, which greatly reduced memory consumption, storage cost, I/O burden, and SAM inference time. Although the original 0.10 m GSD could preserve finer boundary details, directly processing full-resolution orthomosaics was difficult under the available computational resources. Therefore, 0.50 m GSD was selected as a practical compromise between boundary detail and computational efficiency.

The selected 0.50 m GSD remains within the sub-meter very-high-resolution range and is close to the spatial scale of commercial satellite products, such as Pléiades 50 cm imagery and WorldView-1 0.5 m panchromatic imagery [33,34]. This setting may also support future transfer of the proposed workflow to very-high-resolution satellite or pan-sharpened imagery.

The feasibility of original-resolution tiling is summarized in Table 2. At 0.50 m GSD, a 512 × 512 patch covers 256 m × 256 m, whereas at 0.10 m GSD it covers only 51.2 m × 51.2 m. Thus, covering the same ground area at the original resolution would require about 25 times more patches. Although this may retain finer boundary details, it would greatly increase memory use, storage cost, and SAM inference time. Therefore, original-resolution tiling was not adopted in this study and is considered a future option for coarse-to-fine boundary refinement.


> **Table 2. Computational Feasibility Analysis of Original-Resolution and Downsampled Imagery.**

Required Patches

GSD Setting Orthomosaic Size Ground Coverage of One 512 × 512 Patch

for Same Area Practical Implication

0.10 m 20,480 × 20,480 51.2 m × 51.2 m 25× Finer boundaries, but much

higher computational cost

0.50 m 4096 × 4096 256 m × 256 m 1× Balance between boundary

detail and efficiency

2.2.3. Dataset Construction

The method proposed in this study was applied to multi-class crop fields. Considering that different crops show different growth conditions at the same time, UAV RGB remote sensing imagery was collected from Areas A, B, and C of the study region during the time period when the three crop types were in their best growth stage, namely 22 June 2024 and 4 July 2024. Based on these data, the training set and validation set, the same-region independent test set, and the different-region independent test set were constructed. The dataset construction process is shown in Figure 3.

1. Training and validation sets for the same region.

During the training phase, remote sensing imagery from Areas A and B was used to construct the training and validation sets. A 512 × 512 pixel sliding window was first applied to crop 1000 candidate patches. From these candidates, 600 samples were selected to build the benchmark dataset according to three criteria: clear visibility of target crop parcels; coverage of different field shapes and boundary complexity; and exclusion of severely blurred, heavily shadowed, or poorly stitched patches. This sampling strategy reduced low-quality samples while maintaining scene diversity. The construction of the training and validation datasets is summarized in Table 3.

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 7 of 32


> **Figure 3. Workflow of dataset construction.**


> **Table 3. Statistics of Sample Sizes for Different Crop Field Categories.**

Category Number Description Benchmark Samples Augmented Samples Pixel Percentage

1 Tomato 224 1120 189,337,900 (37.20%) 2 Cotton 230 1150 195,190,128 (38.35%) 3 Corn 146 730 124,450,501 (24.45%) Total 600 3000 100%

The final benchmark dataset included 224 tomato samples, 230 cotton samples, and 146 corn samples. This distribution reflected the actual planting structure of the study area during the survey period, where corn parcels were less common than tomato and cotton parcels. Although the number of corn samples was smaller, corn still accounted for 24.45% of the labeled crop pixels. To reduce the influence of class imbalance, each benchmark sample was augmented using five strategies, resulting in a final dataset of 3000 image samples, and the training process used a combination of Cross-Entropy loss and Dice loss. Pixel-level semantic annotation was performed using Labelme (version 5.4.1, MIT CSAIL, Cambridge, MA, USA). After annotation, the labels were manually checked using the same criteria as sample selection, mainly including parcel visibility, field shape, boundary complexity, and the exclusion and correction of low-quality areas. Annotation and quality control in this study were conducted according to a unified interpretation criterion. To improve the consistency and reliability of the annotations, all labels were manually reviewed after annotation, and areas with ambiguous boundaries, shadow effects, or poor stitching quality were further checked and corrected with reference to the original UAV RGB orthomosaics. After annotation and augmentation, the dataset was divided into training and validation sets at a 9:1 ratio. The augmentation methods are summarized in Table 4.

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 8 of 32


> **Table 4. Data Augmentation Methods.**

Augmentation Method Description

Random 90◦Rotation Rotated by 90◦/180◦/270◦with a 50% probability to improve angle invariance. Brightness and Contrast Adjustment Randomly adjusted brightness and contrast to simulate varying illumination. RGB Channel Shift Applied minor perturbations to RGB channels to enhance color robustness. Gaussian Blur Simulated lens defocusing or motion blur via smoothing filters.

Elastic Deformation Applied small-magnitude deformation to simulate wind-induced canopy

displacement without altering field boundaries.

2. Independent test set for the same region.

To evaluate spatial generalization, which requires performance comparisons across various environments, a distinct independent test set was created from Areas A and B to function as a standard for the same-region conditions. To avoid data contamination, the images from Areas A and B were spatially separated to prevent overlap between the training and test sets. The same cropping protocol as that used in the training phase was applied to each input image from the held-out areas, producing 251 patches of 512 × 512 pixels. These patches formed the independent same-region test set.

3. Independent test set for a different region.

This study constructed an independent test set using remote sensing images from Area C to evaluate the model’s generalization performance across different regions. Ran- dom cropping was applied to each input image from Area C, producing 274 patches of 512 × 512 pixels. No augmentation was applied to the test images, ensuring fair and reproducible evaluation results.

2.3. Research Roadmap

This study proposes a multi-class farmland recognition framework based on Semantic– SAM integration. The overall workflow is illustrated in Figure 4.

First, the prompter performs pixel-level semantic segmentation on the input remote sensing imagery to generate probability maps for each category. Subsequently, thresh- olding is applied to these maps to generate class-specific candidate masks, from which minimum bounding boxes and high-confidence point prompts are automatically extracted. Finally, these prompts are fed into SAM without additional fine-tuning, using the Vi- sion Transformer-Huge (ViT-H) version, to perform zero-shot boundary refinement of the candidate crop regions. By applying post-processing gating and local constraints to suppress erroneous outputs, the framework generates coherent and closed multi-class segmentation results.

2.4. Construction of the Semantic–SAM Framework

The proposed framework focuses on a practical complementary strategy that combines the crop recognition ability of semantic segmentation models with the strong boundary delineation ability of SAM for UAV RGB crop field mapping. In this framework, the semantic segmentation model provides crop category priors and initial identification results, while SAM generates candidate masks with clearer boundaries based on the prompts. The main methodological design lies in converting semantic identification results into class-guided prompts and constraining the SAM segmentation process to preserve crop semantics while improving field boundaries. This fusion is expected to improve model quality by preserving crop semantic labels from the prompter while using SAM to refine coarse, broken, or locally shifted field boundaries. The main expected gain is

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 9 of 32

improved boundary quality and prediction stability, whereas changes in regional accuracy may depend on the initial segmentation quality and prompt type.


> **Figure 4. Research technical roadmap. (a) Framework construction. (b) Experimental design.**

> (c) Results and performance evaluation. ns indicates no significant difference (p > 0.05), * indicates a
significant difference (p ≤0.05), and ** indicates a highly significant difference (p ≤0.01).

2.4.1. Prompter Module

In this study, four representative semantic segmentation models—DeepLabv3+, U-Net, HRNet, and PSPNet—were selected as prompters. These models were used to identify crop categories and generate class-guided prompts for SAM. Given a UAV RGB image, the prompter first generated a multi-class probability map and an initial semantic prediction. For each detected crop class, a class-specific binary candidate mask was obtained from the

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 10 of 32

initial semantic prediction. Very small predicted regions were skipped during SAM prompt generation to avoid unstable prompts from noise or isolated pixels.

1. Pixel-level probability map for each category

P = fθ(I), Pc(x) ∈[0, 1] (1)

where P denotes the output multi-class probability map, fθ represents the prompter model,

I is the input image, and Pc(x) is the predicted probability of category c at pixel location x.

To extract candidate crop regions, a thresholding operation was performed on each category c:

Mp

c = {x | Pc(x) > τ} (2)

where Mp

c denotes the binary candidate mask of category c, and τ is the probability threshold. τ was set to 0.50 for generating class-specific candidate masks.

2. Minimum Bounding Rectangle

For each detected crop class in each input image, a class-specific binary mask was generated from the initial semantic prediction. The axis-aligned minimum bounding box was then calculated from all foreground pixels of this class-specific mask and used as the box prompt.

3. High-Confidence Point

High-confidence point prompts were sampled from the class-specific binary mask of each detected crop class. In this study, point prompts were sampled for each detected crop class within each input image. Pixels located inside the predicted crop region and with high class probabilities were regarded as candidate internal pixels. The confidence threshold for point selection, τ+, was set to 0.70. For each detected crop class in each input image, the high-confidence pixel set was defined as:

c = {x | Pc(x) > τ+} ∩Mp

Ω+

c (3)

where Ω+

c denotes the high-confidence pixel set of category c, Pc(x) is the predicted probability of category c at pixel location x, τ+ is the confidence threshold for point selection, and Mp

c is the class-specific binary mask generated from the initial semantic prediction. Three pixels with the highest class probabilities in Ω+

c were selected as point prompts. If fewer than three pixels satisfied τ+, the three pixels with the highest class probabilities inside Mp

c were used as fallback point prompts. This ensured that each detected crop region could provide valid point prompts for SAM.

According to the prompt mode, SAM received point prompts, box prompts, or point- box prompts for each detected crop class. The point prompt provided internal semantic location information, while the box prompt provided an external spatial constraint.

2.4.2. Segment Anything Model (SAM)

The SAM module consists of three core components: an image encoder EncI, a prompt encoder Encp, and a mask decoder DecM. In this study, the official pre-trained SAM with a ViT-H version is directly adopted and kept frozen. Given the input image I and prompts Sc,k, the SAM inference process is formulated as follows:

EI = EncI(I) (4)

Ep = Encp(Sc,k) (5) n

oK

Ms,j

c,k, ˆqj

 



j=1 = DecM

EI, Ep

(6)

c,k

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 11 of 32

In Equation (4), the input image I is fed into the image encoder EncI to extract the image feature embedding EI, which serves as the visual foundation for the subsequent mask decoder. Equation (5) feeds the class-guided prompts Sc,k into the prompt encoder Encp to obtain the corresponding prompt embeddings Ep, which are utilized to guide the target segmentation. Equation (6) simultaneously feeds the image embedding EI and prompt embedding Ep into the mask decoder DecM, which outputs a set of K candidate

masks along with their corresponding confidence scores. Here, M(s,j)

c,k denotes the j-th

candidate mask, and ˆqj

c,k represents its corresponding confidence score. The superscript (s, j) indicates that multiple valid masks can be generated from a specific prompt. This process achieves prompt-guided mask generation.

2.4.3. Post-Processing

Since SAM may exhibit over-expansion, mask misalignment, or cross-field merging in complex farmland scenes, this study introduces a category-preserving constrained segmentation strategy to improve the stability of the segmentation process. This strategy uses the initial semantic mask as a class prior, the minimum bounding box as a spatial prior, and the local boundary band as a segmentation constraint, allowing SAM to correct boundary errors while reducing category confusion and boundary leakage.

1. Candidate Mask Selection

For each prompt, SAM outputs K candidate masks (the default is K = 3) together with their corresponding predicted quality scores. The candidate mask with the highest overlap with the initial segmentation mask is then selected. The formula is as follows:

c,k = Ms,j∗





Ms,j

c,k, Mp

j∗= arg max

, Ms

j IoU

c,k (7)

c,k

Here, Mp

c,k denotes the initial segmentation mask generated by the prompter, and Ms,j

c,k denotes the (j)-th candidate mask generated by SAM.

2. Consistency Gating

The consistency between the SAM-refined mask and the initial prompter mask is quantified by calculating the Intersection over Union (IoU). The formula is as follows:



c,k, Mp

IoU(M s

(8)

c,k

where Mc,k denotes the gated refined mask, and δ represents the gating threshold. If the consistency score falls below the threshold δ, the refinement is considered unreliable, and the system falls back to the initial prompter mask. The formula is as follows:

Mp

(

c,k, IoU < δ Ms

Mc,k =

c,k, otherwise (9)

The overall stability of the final segmentation results is ensured by this gating mecha- nism, which suppresses any incorrect masks produced by SAM.

3. In-box Cropping Constraint

The minimum bounding box used for prompt generation strictly restricts the re- fined masks. This restriction prevents the refined regions from extending beyond the box boundary.

4. Local Band Constraint

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 12 of 32

This study only replaces masks within the prompter’s boundary zone to stop SAM from making large-scale offsets in semantically ambiguous areas. The following steps are used to build the boundary belt:









Mp

Mp

\Erode

B = Dilate

c,k, rb

c,k, rb

(10)

where rb denotes the radius of the boundary belt (or width parameter), while Dilate and

Erode represent the morphological dilation (expansion) and erosion (shrinkage) operations, respectively.

The refined boundary belt is integrated with the original prediction’s interior semantics to produce the final mask. The definition of the fusion process is:





Mp

M∗

c,k\B

∪(Mc,k ∩B) (11)

c,k =

where B represents the boundary belt region, and M∗

c,k denotes the final fused mask. This method enhances the boundary fitting quality while ensuring categorical consistency.

2.4.4. Geographic Information System (GIS)-Oriented Vectorization and Topology Checking

After obtaining the final raster semantic masks, a Geographic Information System (GIS)-oriented vectorization step was applied to generate parcel-level vector polygons. The patch-level predictions were first restored to their original geospatial positions and mosaicked according to the UAV orthomosaic coordinates. In overlapping areas, only one final class label was retained for each pixel to avoid class overlap.

The mosaicked raster masks were then converted into vector polygons for each crop class. Small isolated polygons were removed, invalid geometries were repaired, and small holes were filled. Topology checking was performed to ensure non-overlap among crop classes and field instances. If overlapping polygons occurred, the overlap was assigned to the polygon with higher raster support or higher prediction confidence. For cross-tile consistency, adjacent polygons from neighboring patches were merged when they belonged to the same crop class and shared a boundary along the tile edge. The final vector polygons were checked for invalid geometries, overlap areas, cross-tile seams, and consistency with the original raster masks. An example of the GIS-oriented vectorization result is shown in Figure 5.


> **Figure 5.**

> Example of GIS-oriented vectorization from raster masks to parcel-level polygons.
(a) Original UAV orthomosaic in GeoTIFF format. The black line in the original UAV image is
the shadow of a wooden stake, not a parcel boundary; (b) SAM prediction result as a gridded mask;
(c) Vectorized result saved in GeoPackage format.

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 13 of 32

2.5. Training Strategies and Parameter Settings

In order to evaluate how different prompters affect the performance of the ensuing refinement stage, this study independently implemented four semantic segmentation frameworks: DeepLabv3+, U-Net, HRNet, and PSPNet. The learning rate began at 1 × 10−4

and decreased over time using a Cosine Annealing strategy with the AdamW optimizer (implemented in the PyTorch deep learning framework, version 2.5.1, PyTorch Foundation, San Francisco, CA, USA). The models were trained for a total of 300 epochs, and the batch size was set to 8. The SAM module used the official pre-trained weights of the ViT-H version to set up the model. To speed up convergence during training, pre-trained ImageNet weights were used for the prompters. To ensure training stability, the encoders of the prompters were frozen during the first 50 epochs, followed by end-to-end fine-tuning after unfreezing. A combination of multi-class Cross-Entropy (CE) loss and Dice loss was employed as the objective function to enhance optimization for class imbalance and boundary regions. The aforementioned training parameters are summarized in Table 5.


> **Table 5. Hyperparameter Settings for Model Training.**

Main Parameters Settings

Optimizer AdamW Initial Learning Rate 1 × 10−4

LR Scheduler Cosine Annealing Batch Size 8 Epochs 300 Semantic Models DeepLabv3+, U-Net, PSPNet, HRNet Segment Anything Model (SAM) ViT-H version Freezing Strategy Encoder frozen for the first 50 epochs Training Phases Phase 1: Frozen (0–50); Phase 2: Unfrozen (50+) Loss Function Cross-Entropy Loss + Dice Loss Optimization Focus Category classification and boundary refinement

The dataset was organized in a Visual Object Classes (VOC)-style format for train- ing and evaluation. As shown in Table 6, the semantic segmentation models served as prompters to output class-specific candidate masks and generate both point and box prompts for SAM. For point prompts, three high-confidence points were selected for each detected crop class in each input image based on the initial semantic prediction. For box prompts, the minimum bounding rectangle was generated from all foreground pixels of each class-specific binary mask. Once SAM output candidate masks based on the prompts, the candidate with the highest IoU with the initial semantic mask was selected. A consis- tency gate was then applied for quality validation. At the same time, the candidate mask was limited to the minimum bounding rectangle to reduce over-segmentation. To preserve crop semantics, mask replacement was allowed only in the local transition zone around the initial predicted boundary. This design allowed both boundary expansion and shrinkage, enabling bidirectional correction of contour errors.

The parameters of the post-processing module were determined through validation experiments rather than optimized on the test set. To ensure fair comparison, the same parameter settings were used for all models and prompt types. A parameter sensitivity analysis was further conducted in Section 3.5 to evaluate the influence of key parameters on model performance.

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 14 of 32


> **Table 6. Key Parameter Settings.**

Parameter Variable Name Settings Description

Prompt Modality prompt_mode Point + box Hybrid Point + box Prompting for Dual-Constraint Guidance.

Three high-confidence internal

Number of points per

points were sampled for each

detected class points_per_class 3

detected crop class in each

input image.

Small area filtering sam_min_area 300 px Skip SAM for small objects to

reduce redundancy.

Boundary tolerance boundary_width 12 px Boundary width for bmIoU

and bmF1 evaluation.

Candidate mask selection best_mask_select iou Select candidate with the

maximum IoU score.

Consistency gating iou_accept_thresh (δ) 0.05 Discard refined masks if IoU is

below the threshold.

Constrain within the minimum bounding box to prevent boundary leakage.

Intra-box cropping constrain_to_box True

Local band update refine_radius 15 px Local band replacement to

preserve core regions.

Allow dilation/erosion allow_expand/allow_shrink True/True Allow dilation/erosion for boundary error correction.

Candidate mask threshold mask_threshold (τ) 0.5 Probability threshold for

generating class-specific

candidate masks

threshold point_threshold (τ+) 0.7 Probability threshold for

High-confidence point

selecting internal point

prompts SAM checkpoint sam_checkpoint sam_vit_h.pth ViT-H version

In all experiments involving point prompts, three high-confidence internal points were sampled for each detected crop class in each input image. If N valid crop classes were detected in one input image, the point-only setting generated 3 × N point prompts, the box-only setting generated N box prompts, and the point-box setting generated 3 × N point prompts together with N box prompts.

Across all evaluated test images, approximately 2–3 valid crop classes were detected per image on average, resulting in about 6–9 point prompts under the point-only set- ting, 2–3 box prompts under the box-only setting, and 8–12 total prompts under the point-box setting.

2.6. Ablation Study Configuration

In order to determine how much each component of SAM’s refinement stability and boundary quality influences the others, this study employs a series of leave-one-out ablation experiments. Starting with the full method (A0), only one component is removed at a time, with all other settings remaining unchanged. The macro-averaged mIoU and bmF1 for each crop category are displayed in the same-region independent test set. Table 7 summarizes the specific configurations.

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 15 of 32


> **Table 7. Experimental Configurations for Ablation Studies.**

ID Experiment Description

A0 Full Framework Integration of all proposed refinement and gating modules. A1 Without IoU Selection Candidate mask selection based on the highest IoU was removed. A2 Without Gating Consistency gating and fallback to the initial result were removed. A3 Without Box Cropping The spatial constraint within the minimum bounding box was removed. A4 Without Belt Fusion Local boundary-band fusion was removed. A5a Expansion Only Dilation-only refinement to fill missing areas without shrinkage. A5b Shrinkage Only Erosion-only refinement to remove redundant areas without expansion.

2.7. Evaluation Metrics

This study used both region-based and boundary-based metrics to evaluate multi- class crop field segmentation. Region-based metrics were used to assess crop classification consistency and regional overlap, while boundary-based metrics were used to evaluate field-edge alignment. This combination is necessary for parcel-level crop mapping because a model may achieve high regional accuracy while still producing coarse, shifted, or incomplete field boundaries. Therefore, this study formulated task-oriented evaluation requirements based on the selected metrics. For same-region evaluation, the proposed framework was expected to improve both regional metrics and boundary metrics compared with the corresponding standalone semantic segmentation models. The regional metrics included mIoU and mF1, and the boundary metrics included bmIoU and bmF1. For different-region evaluation, the main requirement was to improve mIoU and boundary quality over the corresponding standalone model.

2.7.1. Regional Accuracy Metrics

For each crop category c, the Intersection over Union (IoU) was calculated as:

1. Per-class Basic Metrics

The Intersection over Union (IoU) was calculated as follows:

IoUc = TPc TPc + FPc + FNc

(12)

where TPc, FPc, and FNc denote the numbers of true positive, false positive, and false negative pixels for category c, respectively.

2. Macro-average Metrics

The macro-averaged mIoU was calculated over the three foreground crop categories, excluding the background class:

mIoU = 1 |C| ∑

IoUc (13)

c∈C

where C denotes the number of foreground crop categories. In this study, C = 3, corre- sponding to cotton, tomato, and corn. Other region-based metrics, including mP, mR, and mF1, were also calculated as macro-averages over the same foreground categories and are reported in the result tables for supplementary comparison.

2.7.2. Boundary Accuracy Metrics

Boundary metrics were used to evaluate the alignment between predicted and ground- truth field edges, which is particularly important for parcel-level crop mapping. For each crop category c, let Pc and Gc denote the predicted and ground-truth binary masks, respec- tively. The corresponding boundaries were extracted using morphological operations:

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 16 of 32

1. Boundary Extraction

Morphological operations are employed to extract single-pixel width boundaries:

∂Pc = Dilate(Pc, 1)\Erode(Pc, 1) (14)

∂Gc = Dilate(Gc, 1)\Erode(Gc, 1) (15)

where Dilate and Erode denote morphological dilation and erosion operations, respectively.

2. Tolerance Band Construction

To reduce the influence of one-pixel boundary shifts, a tolerance band with width d was constructed around both predicted and ground-truth boundaries:

∼ Pc = {x| min

||x −y||≤d} (16)

y∈∂Pc

∼ Gc = {x| min

||x −y||≤d} (17)

y∈∂Gc

where ||x −y|| denotes the Euclidean distance between pixels x and y.

3. Boundary IoU

The Boundary IoU (bIoU) is defined as the ratio of the intersection to the union of the two tolerance regions:

∼ Gc |

∼ Pc ∩

bIoUc = |

(18)

∼ Gc |

∼ Pc ∪

|

4. Boundary F1-score

The Boundary F1-score (bF1) was calculated as:

bF1c = 2·bPrecisionc·bRecallc (bPrecisionc + bRecallc + ε) (19)

where ε is a small constant used to avoid division by zero and was set to 1 × 10−7 in this study. Finally, bmIoU and bmF1 were obtained by macro-averaging bIoU and bF1 over the three foreground crop categories, excluding the background class.


## 3. Results

3.1. Comparative Evaluation and Validation of the Semantic–SAM Framework Against Traditional Segmentation Models

To verify the effectiveness of the proposed Semantic–SAM framework, a comparative analysis was carried out on the same-region A + B test set using four semantic segmentation models, namely U-Net, DeepLabv3+, HRNet, and PSPNet, together with their correspond- ing SAM-refined results. According to Table 8, under the bounding box prompt setting, the performance changes after introducing SAM varied across different prompters. SAM improved boundary quality more consistently and also enhanced regional recognition in some models.

After SAM was introduced, changes in regional accuracy and boundary quality varied across models, although the overall trend remained positive. After being combined with SAM, U-Net still showed the best overall performance. Its mIoU increased from 86.19% to 87.09%, and its mF1 increased from 92.39% to 92.95%. At the same time, the boundary metrics, bmIoU and bmF1, also improved further. This shows that, even when the initial accuracy is high, SAM mainly refines boundaries and improves prediction stability. Both

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 17 of 32

HRNet and PSPNet showed clear boundary improvement after being combined with SAM, while the changes in regional metrics were relatively model-dependent. The increase in regional metrics was more obvious for PSPNet, while the boundary improvement was also clear for both HRNet and PSPNet. SAM is particularly beneficial for models with moderate initial accuracy or relatively rough boundaries. In contrast, after DeepLabv3+ was combined with SAM under the box prompt setting, its mIoU and mF1 decreased slightly. Although bmIoU improved, bmF1 dropped slightly, which indicates that its boundary refinement effect and regional recognition gain were not stable. Overall, the main benefit of SAM was boundary refinement. Regional accuracy changed across models, whereas boundary gains were more consistent.


> **Table 8. Overall Performance Comparison and Effectiveness Validation of the Proposed Method.**

Model mIoU

mP (%)

mR (%)

mF1

bmIoU

bmF1

(%)

(%)

(%)

(%)

U-Net 86.19 88.46 96.97 92.39 48.94 75.84 U-Net + SAM 87.09 98.57 88.14 92.95 51.33 79.46 DeepLabv3+ 80.45 88.4 89.77 89 54.25 69.06 DeepLabv3+ + SAM 78.74 86.61 89.5 87.92 56.41 68.13 HRNet 77.36 83.24 91.29 87.03 22.14 44.44 HRNet + SAM 78.12 83.11 92.55 87.53 27.41 50.78 PSPNet 78.99 83.44 93.07 87.89 53.24 74.02 PSPNet + SAM 80.91 85.06 93.78 89.10 63.41 78.04

Note: All metrics are macro-averaged over the cotton, tomato, and corn categories, excluding the background. All values are expressed in %. Here, m denotes macro-averaging, P for Precision, R for Recall, and b for boundary- specific metrics.


> **Figure 6 further shows that different prompters respond differently to SAM refinement.**

> For U-Net, the original segmentation already produced relatively complete field outlines, so
the role of SAM was mainly to smooth the edges, fill local gaps, and make the boundaries
more regular. For HRNet and PSPNet, SAM more clearly improved problems such as
broken boundaries, connected fields, and blurred outlines, showing a strong ability in
boundary repair. In contrast, for DeepLabv3+, under the current box prompt setting, SAM
did provide some compensation for boundary details, but the regional metrics did not
improve at the same time. This suggests that when only a single box prompt is used, the
automatically generated prompt information may not fully bring out the advantage of
combining this model with SAM.

To further evaluate the robustness of the performance changes after introducing SAM, each test image in the same-region test set was used as one statistical unit. The foreground mIoU was calculated for each standalone model and its corresponding Semantic–SAM version. The Wilcoxon signed-rank test was then used to analyze the significance of paired differences, and the error bars represent the standard deviation.

According to Figure 7, the effect of SAM on regional accuracy was model-dependent. U-Net and PSPNet showed significant improvements after SAM refinement, while HRNet showed no significant change. In contrast, DeepLabv3+ showed a significant decrease in mIoU under the box-prompt setting. This result indicates that SAM does not uniformly improve regional accuracy for all prompters. A possible reason is that box prompts mainly provide spatial constraints but lack internal semantic guidance; therefore, when the initial DeepLabv3+ prediction contains local shifts or fragmented regions, SAM may introduce local over-expansion or misalignment. Overall, these results suggest that the main advan- tage of Semantic–SAM lies in boundary refinement and prediction stabilization, whereas regional accuracy remains dependent on the initial segmentation quality.

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 18 of 32


> **Figure 6. Visual comparison of segmentation results across different models. (a) Original image.**

> (b) Ground-truth mask. (c) Recognition result. (d) Boundary result.


> **Figure 7. Significance analysis of segmentation performance between standalone models and**

> Semantic–SAM models on the same-region test set. The bar chart shows the mean foreground
mIoU of four baseline models before and after SAM refinement, and the error bars represent the
standard deviation. Using each test image in the same-region test set as one statistical unit, Wilcoxon
signed-rank tests were used to analyze the significance of differences between the standalone models
and their Semantic–SAM versions. ns indicates no significant difference (p > 0.05), * indicates a
significant difference (p ≤0.05), and ** indicates a highly significant difference (p ≤0.01).

3.2. Performance Comparison of Different Prompt Forms in the Semantic–SAM Framework

This section examines how different automatic prompt types affect fine field boundary recognition. On the same-region A + B test set, three strategies were compared: high- confidence point prompts, bounding box prompts, and point-box prompts. Table 9 shows that prompt type affected model performance, although the extent of this effect varied across models. Point-box prompts tended to show relatively stable performance.

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 19 of 32


> **Table 9. Comparison of Evaluation Metrics for Different Input Prompt Forms.**

Point Prompt +

Point Prompt +

Box Prompt

Point Prompt

Box Prompt

Point Prompt

Box Prompt

Box Prompt

bmF1

bmF1

mIoU

Models

mIoU

bmF1

mIoU

(%)

(%)

(%)

(%)

(%)

(%)

U-Net + SAM 85.12 87.09 86.76 78.43 79.46 77.72 DeepLabv3+ +

SAM 76.08 78.74 81.71 65.06 68.13 73.21

HRNet + SAM 77.03 78.12 78.07 52.14 50.78 53.69 PSPNet + SAM 78.45 80.91 83.13 77.77 78.04 79.48

Note: All metrics are macro-averaged over the cotton, tomato, and corn categories, excluding the background. All values are expressed in %. Here, m denotes macro-averaging, P for Precision, R for Recall, and b for boundary- specific metrics.

From the overall metrics, different prompt types had clear effects on both regional recognition accuracy and boundary refinement, but their effects varied across models. Point-box prompts generally delivered the most stable performance. In terms of regional metrics, point-box prompts achieved the highest mIoU for DeepLabv3+ and PSPNet, reaching 81.71% and 83.13%, respectively. This suggests that they can make use of both the spatial range constraint provided by box prompts and the internal semantic anchor provided by point prompts, thus improving the consistency of regional recognition. For HRNet, the results of point-box prompts were close to those of box prompts. For U- Net, the highest mIoU was obtained under box prompts, reaching 87.09%, which was slightly higher than the 86.76% obtained with point-box prompts. In terms of boundary metrics, U-Net achieved the highest bmF1 under box prompts, reaching 79.46%. HRNet, DeepLabv3+, and PSPNet, however, all achieved better bmF1 under point-box prompts, reaching 53.69%, 73.21%, and 79.48%, respectively. These results indicate that, compared with point prompts or box prompts alone, point-box prompts are usually more helpful for balancing regional completeness and boundary fitting. However, for models with already stable initial segmentation results, box prompts alone can sometimes still produce the best performance.

Quantitatively, the point-box prompt achieved the highest average performance across the four prompters, with an average mIoU of 82.42% and bmF1 of 71.03%. Compared with the point and box prompts, it improved mIoU by 3.25 and 1.20 percentage points, and bmF1 by 2.68 and 1.93 percentage points, respectively. According to the predefined task-oriented evaluation requirements, the point-box prompt generally met the same-region requirement, as it improved both mIoU and bmF1 in PSPNet + SAM from 78.99% to 83.13% and from 74.02% to 79.48%, respectively. Figure 8 shows the differences in refinement effects of different prompt types on typical samples more directly. When only point prompts were used, SAM relied more on a small number of internal semantic locations to generate masks. Although it could capture the target interior well in some samples, it provided relatively weak constraints on the outer contour, which could easily lead to unstable boundary fitting. When only box prompts were used, they could provide a clear spatial range constraint for the target, making the overall field outline more regular, but correction was still sometimes insufficient in local details and complex boundary areas. In contrast, point-box prompts incorporate both internal semantic information and external spatial constraints. As a result, they achieved a more balanced performance in field-edge continuity, corner delineation, and local gap repair. This is why they achieved better or more stable overall results in most models.

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 20 of 32


> **Figure 8. Comparison of results for different prompt forms: a case study using tomato. (a) Original**

> image. (b) Ground-truth mask. (c) Recognition result. (d) Boundary result.

To compare the effects of different prompt types on the recognition performance of the Semantic–SAM fusion model, this section used each test image in the same-region test set as one statistical unit and calculated the foreground mIoU under three prompt types: point prompts, box prompts, and point-box prompts. Friedman tests and Wilcoxon signed-rank tests were then used to analyze the significance of the differences, and the error bars represent the standard deviation.

According to Figure 9, different prompt types had a certain influence on model perfor- mance. Overall, point prompts were relatively weaker, while box prompts and point-box prompts usually gave better results. For U-Net + SAM, the foreground mIoU under the three prompt types was 0.848, 0.872, and 0.865, respectively, with box prompts giving the best result. For DeepLabv3+ + SAM, the values were 0.754, 0.782, and 0.811. For PSPNet + SAM, they were 0.779, 0.806, and 0.832. In both cases, point-box prompts per- formed best. For HRNet + SAM, the values were 0.761, 0.780, and 0.778, showing that box prompts and point-box prompts gave very similar results. On the whole, point-box prompts performed better for most models. This suggests that combined prompts can provide both target location information and spatial range information at the same time, which is more helpful for bringing out the boundary refinement advantage of SAM. Therefore, they can be regarded as a better prompt strategy in the Semantic–SAM framework used in this study. It should also be noted that the values reported in the main tables are summary results

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 21 of 32

for the whole test set, while the values in this section are mean values calculated image by image. Although the statistical criteria are different, the overall trend is consistent.


> **Figure 9. Significance analysis of segmentation performance under different prompt types. The**

> bar chart shows the mean foreground mIoU of four baseline models under different prompt types,
and the error bars represent the standard deviation. Using each test image in the same-region test
set as one statistical unit, Friedman tests and Wilcoxon signed-rank tests were used to analyze the
significance of differences among point prompts, box prompts, and point-box prompts. ns indicates
no significant difference (p > 0.05), * indicates a significant difference (p ≤0.05), and ** indicates a
highly significant difference (p ≤0.01).

3.3. Spatial Generalization Ability Analysis of the Semantic–SAM Framework and Traditional Semantic Segmentation Models

To evaluate the spatial generalization ability of the models, this study compared the performance of each prompter before and after combining with SAM on the same-region A + B test set and the different-region C test set. Point-box prompts were used as the prompt

type. The results in Table 10 show that, after SAM was introduced, boundary quality was improved more consistently in both same-region and different-region tests, while changes in regional accuracy varied across models. This indicates that the fusion framework is effective in same-region tests and remains adaptable in different-region scenes.

From the results, after SAM was introduced, all models showed improvements to different degrees in both same-region and different-region tests, but the gains were more obvious in the different-region setting. In the same-region test, PSPNet + SAM showed better overall performance, indicating that it achieved a good balance between regional con- sistency and boundary fitting. U-Net + SAM still maintained the highest accuracy, but its improvement was relatively small, which suggests that the role of SAM for high-accuracy models is mainly reflected in boundary refinement and improved result stability. The im- provements of DeepLabv3+ and HRNet were more obvious, indicating that this framework can provide good compensation for models with rough initial boundaries or less stable segmentation results. In the different-region test, SAM also clearly improved the general- ization ability of all models, with the most obvious improvement seen in DeepLabv3+. This

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 22 of 32

suggests that when scene changes are large, SAM can effectively reduce model performance degradation. Taken together, the Semantic–SAM framework improves boundary fitting in same-region tests and enhances robustness under different-region conditions.


> **Table 10. Comparison of Spatial Generalization Performance Metrics.**

Models Test Set mIoU

mP (%)

mR (%)

mF1

bmIoU

bmF1

(%)

(%)

(%)

(%)

U-Net A + B 86.19 88.46 96.97 92.39 48.94 75.84 U-Net + SAM 86.76 88.39 97.91 92.77 52.8 77.72 U-Net C 82.44 91.11 89.84 90.36 24.79 56.99 U-Net + SAM 84.16 91.96 92.61 91.37 27.54 57.41

DeepLabv3+ A + B 80.45 88.4 89.77 89 54.25 69.06 DeepLabv3+ + SAM 81.71 87.95 91.59 89.65 61.07 73.21 DeepLabv3+ C 67.22 91.62 71.06 79.73 47.95 66.47 DeepLabv3+ + SAM 73.45 92.16 77.66 84.12 52.95 69.18

HRNet A + B 77.36 83.24 91.29 87.03 22.14 44.44 HRNet + SAM 78.07 83.17 92.41 87.48 29.09 53.69 HRNet C 67.05 84.23 77.05 80.23 14.77 38.65 HRNet + SAM 70.58 82.27 84.11 82.74 18.75 41.71

PSPNet A + B 78.99 83.44 93.07 87.89 53.24 74.02 PSPNet + SAM 83.13 87.81 93.53 90.52 66.01 79.48 PSPNet C 72.64 88.94 79.52 83.74 40.89 64.43 PSPNet + SAM 76.34 90.49 82.72 86.24 51.01 69.81

Note: All metrics are macro-averaged over the cotton, tomato, and corn categories, excluding the background. All values are expressed in %. Here, m denotes macro-averaging, P for Precision, R for Recall, and b for boundary- specific metrics.


> **Figure 10 shows that, in the same-region test, each model already had a certain**

> recognition basis, so the gain brought by SAM was relatively moderate. In the different-
region test, however, the original results of all models generally declined to some extent, and
the bar values increased more clearly after SAM was introduced, especially for DeepLabv3+,
PSPNet, and HRNet. This indicates that the fusion framework has a stronger corrective
effect on performance degradation under different-region conditions. This result suggests
that the framework can improve robustness under the tested different-region condition.


> **Figure 10.**

> Comparison of different-region generalization performance. (a) Original image.
(b) Ground-truth mask. (c) Recognition result. (d) Boundary result.

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 23 of 32

To further verify the reliability of the cross-region results, each test image in the different-region test set was used as one statistical unit. The foreground mIoU was cal- culated for each standalone model and its corresponding Semantic–SAM version. The Wilcoxon signed-rank test was then used to analyze the significance of paired differences, and the error bars represent the standard deviation.

According to Figure 11, all four Semantic–SAM models achieved significant improve- ments in mIoU on the different-region test set. This indicates that the proposed framework can improve spatial generalization under cross-region conditions. The improvement was especially clear for DeepLabv3+, suggesting that SAM-based boundary refinement can partly compensate for weaker initial segmentation results in unfamiliar regions. Over- all, the statistical results support the conclusion that Semantic–SAM fusion improves the robustness and generalization ability of crop field mapping from UAV RGB imagery.


> **Figure 11. Significance analysis of segmentation performance between standalone models and**

> Semantic–SAM models on the different-region test set. The bar chart shows the mean foreground
mIoU of four baseline models before and after SAM refinement, and the error bars represent the stan-
dard deviation. Using each test image in the different-region test set as one statistical unit, Wilcoxon
signed-rank tests were used to analyze the significance of differences between the standalone models
and their Semantic–SAM versions. * indicates a significant difference (p ≤0.05), and ** indicates a
highly significant difference (p ≤0.01).

To provide a complete view of the different-region evaluation, Table A1 in Appendix A reports the per-class IoU and boundary F1-score, while Table A2 provides the complete prompt-wise comparison across all prompters under point, box, and point-box prompts.

3.4. Component-Wise Ablation Study of the Semantic–SAM Framework

To further explain the independent contribution of each component in the Semantic– SAM framework, while also considering model efficiency, the runtime of four Semantic + SAM combinations was first tested. The test was conducted on the same-region inde-

pendent test set, and the results are shown in Table 11. The results show that although U-Net + SAM achieved the highest accuracy, it also took the longest time, requiring 3.72 s to process one image. In comparison, PSPNet + SAM achieved a better balance between accuracy and efficiency. Its average runtime was 1071.17 ms/img, and its FPS was 0.93, while its mIoU and bmF1 reached 83.13% and 79.48%, respectively. Therefore, PSPNet +

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 24 of 32

SAM was used as the default model in the following ablation experiments, the prompt type was fixed as point-box prompts, and item-by-item ablation evaluation was carried out on the same-region test set.


> **Table 11. Comparison of Accuracy and Efficiency among Different Semantic–SAM Models.**

Models mIoU

mF1

bmIoU

bmF1

Inference Time

Frames per Second

(%)

(%)

(%)

(%)

(ms/img)

(FPS)

U-Net + SAM 86.76 92.77 52.8 77.72 3729.78 0.27 DeepLabv3+ + SAM 81.71 89.65 61.07 73.21 1092.76 0.92 HRNet + SAM 78.07 87.48 29.09 53.69 1137.08 0.88 PSPNet + SAM 83.13 90.52 66.01 79.48 1071.17 0.93

Note: All metrics are macro-averaged across the cotton, tomato, and corn categories, excluding the background. For point prompts, 3 points are used for each detected crop class in each input image. Units are in %. The abbreviation m denotes macro-averaging, and b represents boundary-specific metrics.

To further analyze the computational efficiency, an additional comparison was con- ducted with and without small-area filtering. In this test, 100 images were randomly selected from the same-region test set to evaluate the average number of SAM calls, infer- ence time, throughput, and peak GPU memory usage.

As shown in Table 12, small-area filtering reduced the average number of SAM calls per image from 1.45 to 1.38, resulting in a slight decrease in inference time and a corresponding improvement in throughput, while the memory usage remained nearly unchanged. This indicates that small-area filtering reduces unnecessary SAM calls by suppressing small noisy regions, thereby improving computational efficiency.


> **Table 12. Computational Cost with and without Small-Area Filtering.**

Setting Small-Area Threshold (px)

Avg. SAM Calls/Image

Time/Image

Throughput

Peak GPU Memory

(ms)

(images/s)

(GB)

Without small-area

filtering 0 1.45 1090.92 0.92 5.61

With small-area

filtering 300 1.38 1059.94 0.94 5.61

Note: The test was conducted using PSPNet + SAM under the same input image size and prompt settings. The throughput was calculated as the number of processed images divided by the total inference time. Peak GPU memory refers to the maximum allocated CUDA memory during inference. All experiments were conducted on a workstation equipped with an NVIDIA GeForce RTX 4060 GPU (NVIDIA Corporation, Santa Clara, CA, USA; 8 GB memory), using PyTorch 2.5.1 with CUDA support (NVIDIA Corporation, Santa Clara, CA, USA).

As shown in Table 13, the complete method A0 achieved an mIoU of 83.13% and a bmF1 of 79.48%. Removing the IoU-based mask selection strategy decreased mIoU by 0.41 percentage points and bmF1 by 1.54 percentage points, indicating that candidate mask selection contributed to stable refinement and boundary quality. Removing consistency gat- ing or box-cropping caused only very small changes in the average metrics, suggesting that these two modules mainly played a stabilizing role under the current test condition. After removing belt-fusion, mIoU decreased by 0.62 percentage points, while bmF1 increased slightly by 0.33 percentage points. This result suggests a trade-off between boundary flexibility and regional semantic consistency, because a larger editable boundary area may improve boundary matching in some samples but may also disturb correctly classified interior regions. In contrast, the expansion-only setting caused the largest decrease in both mIoU and bmF1, while the shrinkage-only setting also led to slight performance degra- dation, indicating that bidirectional boundary adjustment was more suitable for complex field boundary correction. Overall, IoU-based mask selection and bidirectional boundary

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 25 of 32

adjustment were the most beneficial components, whereas consistency gating and box- cropping had relatively limited effects on the average metrics and may be candidates for simplification in efficiency-oriented applications.


> **Table 13. Component-Wise Ablation Study of the Framework.**

ID Experimental Setting mIoU

Changes Relative to A0

bmF1

Changes Relative to A0

(%)

(%)

A0 Full Framework 83.13 — 79.48 — A1 Without IoU-Selection 82.72 −0.41 77.94 −1.54 A2 Without Gating 83.11 −0.02 79.47 −0.01 A3 Without Box-Cropping 83.10 −0.03 79.45 −0.03 A4 Without Belt-Fusion 82.51 −0.62 79.81 +0.33 A5a Expansion Only 79.58 −3.55 76.05 −3.43 A5b Shrinkage Only 82.49 −0.64 79.41 −0.07

Note: All metrics are macro-averaged across the cotton, tomato, and corn categories, excluding the background. For point prompts, 3 points are used for each detected crop class in each input image. Units are in %. The abbreviation m denotes macro-averaging, and b represents boundary-specific metrics. Symbols ‘+’ and ‘−’ indicate performance increase and decrease, respectively.

To further assess the statistical reliability of the ablation results, each test image in the same-region test set was used as one statistical unit. Paired Wilcoxon signed-rank tests with Holm-Bonferroni correction were used to compare each ablated setting with the full framework A0. The statistical results are shown in Table 14.


> **Table 14. Paired Statistical Comparison between the Full Framework and Ablated Settings.**

Comparison ∆mIoU

mIoU Significance ∆bmF1

p-Adj for

p-Adj for

bmF1 Significance

(%)

(%)

A0 vs. A1 Without IoU-Selection −0.41 0.082 ns −1.54 0.018 * A0 vs. A2 Without Gating −0.02 0.742 ns −0.01 0.861 ns A0 vs. A3 Without Box-Cropping −0.03 0.688 ns −0.03 0.724 ns A0 vs. A4 Without Belt-Fusion −0.62 0.048 * +0.33 0.376 ns A0 vs. A5a Expansion Only −3.55 <0.001 ** −3.43 <0.001 ** A0 vs. A5b Shrinkage Only −0.64 0.073 ns −0.07 0.648 ns

Note: ∆indicates the change relative to the full framework A0. p-adj denotes the p-value after Holm-Bonferroni correction. ns indicates no significant difference (p > 0.05), * indicates p ≤0.05, and ** indicates p ≤0.01.

As shown in Table 14, removing IoU-based mask selection significantly reduced bmF1, indicating that this step contributed to boundary refinement stability. Removing consis- tency gating and box-cropping did not cause significant changes in either mIoU or bmF1, suggesting that their effects on average metrics were limited under the current test condi- tion. Removing belt-fusion significantly reduced mIoU, while the slight increase in bmF1 was not statistically significant. This indicates that the apparent bmF1 improvement after removing belt-fusion should not be over-interpreted. The expansion-only setting caused significant decreases in both mIoU and bmF1, confirming that bidirectional boundary adjustment was important for maintaining both regional consistency and boundary quality. The shrinkage-only setting did not show significant changes, suggesting that its effect was weaker than that of expansion-only refinement.

3.5. Sensitivity Analysis of Key Prompt-Generation and Post-Processing Parameters

To evaluate the influence of key prompt-generation and post-processing parameters, a sensitivity analysis was conducted using PSPNet + SAM with point-box prompts on the validation set. The validation set contained 300 image samples, corresponding to 10% of the 3000 augmented training-validation samples. PSPNet + SAM was selected because it

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 26 of 32

showed balanced regional accuracy and boundary refinement in the main experiments. A one-factor-at-a-time strategy was used, with only one parameter changed and all others fixed at the default values listed in Table 6. The tested parameters included τ, τ+, δ, and refine_radius. The evaluation used mIoU and bmF1, and the accepted SAM mask ratio was additionally reported for δ.

As shown in Table 15, the default parameter setting achieved a stable balance between regional accuracy and boundary quality, with an mIoU of 86.67% and a bmF1 of 80.97%. Moderate changes in τ, τ+, and refine_radius caused only limited variations in mIoU and bmF1, indicating that the framework was not highly sensitive to a single parameter within the tested range. For the IoU acceptance threshold δ, increasing the threshold reduced the accepted SAM mask ratio from 92.16% to 83.94%, suggesting that stricter gating rejected more SAM-generated masks. The value δ = 0.05 was retained as a conservative gating setting to suppress clearly inconsistent SAM outputs while preserving most valid boundary segmentation results.


> **Table 15. Results of the Sensitivity Analysis for Key Prompt-Generation and Post-Processing Parameters.**

Parameter Value mIoU

bmF1

Accepted SAM

(%)

(%)

Masks (%)

τ = 0.5

86.67 80.97 92.16 τ+ = 0.7 δ = 0.05 radius = 15 px mask_threshold (τ) 0.4 85.42 79.13 — mask_threshold (τ) 0.6 86.01 79.84 — point_threshold (τ+) 0.6 86.31 80.64 — point_threshold (τ+) 0.8 85.72 79.42 — iou_accept_thresh (δ) 0 85.13 78.95 100 iou_accept_thresh (δ) 0.1 86.22 79.65 83.94 refine_radius 5 px 85.33 78.58 — refine_radius 25 px 85.84 79.67 —

Default setting

Note: For point prompts, 3 points are used for each detected crop class in each input image. Units are in %. The abbreviation m denotes macro-averaging, and b represents boundary-specific metrics. Only one parameter was changed at a time, while the remaining parameters were fixed at their default values in Table 6. The accepted SAM mask ratio was calculated only for the IoU acceptance threshold δ.


## 4. Discussion

4.1. Effectiveness and Advantages of the Fusion Framework

The Semantic–SAM fusion framework proposed in this study mainly improves the boundary quality and structural completeness of multi-class crop fields in UAV RGB im- agery, without requiring manual prompts or SAM fine-tuning. These results validate the feasibility of a modular division of labor between semantic discrimination tasks and general-purpose boundary refinement tasks. The key to this study lies in utilizing seman- tic segmentation models (prompters) to address the ‘semantic blindness’ of SAM, while simultaneously leveraging SAM’s strong boundary delineation ability without additional task-specific training to compensate for the coarse boundaries inherent in semantic models. This is consistent with the findings of Tripathy et al. [23], who showed that vanilla SAM struggles to distinguish different crop types without semantic guidance and is highly sensi- tive to prompt design. This study employs an automated prompt generation mechanism to convert semantic information into geometric prompts (point and box prompts) that SAM can interpret. This strategy effectively links semantic information with geometric prompts.

The proposed framework is also related to previous studies. Previous studies have shown that semantic segmentation models can provide crop-category recognition and

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 27 of 32

pixel-level field extraction, while SAM has strong object-boundary delineation ability when guided by suitable prompts [4–9]. These studies indicate that semantic recognition and boundary delineation are both important for accurate parcel-level crop field mapping. Compared with these methods, this study adopts a complementary framework. Semantic segmentation models provide crop category information and initial identification results, while SAM generates clearer candidate masks based on the prompts. This framework combines the crop recognition ability of semantic segmentation models with the boundary delineation ability of SAM. It also explains why the proposed framework mainly improves boundary quality and structural completeness, while region-based accuracy is still influ- enced by the initial semantic segmentation results. The prompt generation strategy in this study provides a practical way to connect semantic information with SAM-based boundary segmentation.

4.2. In-Depth Analysis of Spatial Generalization and Prompting Strategies

Results from different test areas show that the proposed framework effectively mit- igates performance degradation caused by regional differences. This effect was most prominent in DeepLabv3+, with an mIoU improvement of 6.23%. This result met the predefined different-region requirement by improving mIoU and boundary quality over the standalone DeepLabv3+ model. This finding has important practical implications. In agricultural remote sensing, traditional deep learning models often encounter difficulties because labeled data is only available for certain regions. This makes adaptation to new domains difficult [20,35]. The proposed framework strengthens the use of domain-invariant geometric cues by combining semantic predictions with SAM’s shape priors. This helps compensate for performance degradation caused by differences in spectral and textural characteristics across sites. This result is consistent with the expectation of Ferreira et al. [24] regarding SAM’s generalization ability in large-scale crop field extraction.

This study compared individual point, box, and hybrid point-box prompts to examine the effectiveness of various prompt types. According to the findings, the hybrid point- box approach typically achieves the best balance between boundary fidelity (bmF1) and regional consistency (mIoU). This finding further improves our understanding of how different prompt types affect SAM refinement. Box prompts provide a clear spatial extent and constrain the coarse localization of the segmentation results. This is consistent with the original design of SAM, which used boxes as powerful spatial cues [8]. High-confidence point prompts act as semantic anchors, which help SAM make better local decisions when handling adjacent objects or ambiguous local structures. When accurately placed, point prompts alone can also yield strong boundary performance. This suggests that improving the spatial reliability and accuracy of prompter-generated point prompts remains an important direction for further enhancement. Different prompters respond differently to different prompt types. This means that, in practical applications, the prompting strategy should be adjusted according to the characteristics of the semantic segmentation model.

These findings also indicate that the proposed framework has practical value beyond metric improvements. By generating parcel-level crop maps with both crop-type labels and refined field boundaries from UAV RGB imagery, it can support field inventory, crop type statistics, and the delineation of management units. This is particularly useful in fragmented or irregular agricultural landscapes, where boundary quality directly affects the reliability of parcel-based monitoring and subsequent management decisions. In addition, because the framework relies only on UAV RGB imagery and does not require manual prompting or SAM fine-tuning, it shows practical potential for routine crop mapping in small- to medium-scale agricultural areas. However, its two-stage inference process also means that computational efficiency should be considered in large-scale mapping tasks.

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 28 of 32

4.3. Limitations and Future Work

Although the proposed framework shows advantages in automation, boundary re- finement, and different-region testing, several limitations remain. Based on the obtained results, the final Semantic–SAM-based models can be considered suitable for parcel-level crop field identification under UAV RGB imaging conditions, especially for same-region applications and boundary refinement. However, further improvement is still needed in cross-region robustness, adaptive parameter tuning, and inference efficiency. First, prompt generation and post-processing still rely on fixed parameters that were empirically set on the validation set, and their adaptability to more complex scenes requires further study. Second, the proposed framework consists of two main parts, which may affect compu- tational efficiency in large-scale farmland mapping, so lightweight prompters and more efficient SAM variants, such as ViT-B, ViT-L, and SAM 2, should be explored. Third, the ex- periments were mainly based on UAV RGB imagery from one agricultural region, with only one additional region used for different-region testing. Therefore, the point-box prompt strategy and the overall framework still need to be validated on external datasets with different crops, regions, sensors, imaging dates, spatial resolutions, and imaging conditions. Although a basic GIS-oriented vectorization step was implemented in this study, the current analysis mainly focused on raster-to-vector conversion and basic topology consistency. More comprehensive validation under practical GIS management scenarios still requires further investigation.

The downsampled GeoTIFF orthomosaics were exported as high-quality JPEG images to reduce storage and I/O burden. This process may slightly affect color information and edge details. For areas with complex field boundaries, high-resolution local tiling or coarse-to-fine refinement should be further explored. Future work will also compare the proposed framework with representative boundary-aware and instance-segmentation methods, such as Boundary Loss, clDice, DenseCRF, and Mask2Former, to evaluate their trade-offs in retraining requirements, annotation cost, boundary accuracy, and inference efficiency. In addition, tests under cloudy weather, strong shadows, higher wind speed, variable illumination, and different spatial resolutions will be needed to better assess framework stability. Cross-region mIoU, bmF1, and inference time per image will be used as key indicators to guide further improvements in spatial generalization, boundary quality, and computational efficiency.

4.4. Main Contributions of the Research

The main contributions of this study are as follows. An automatic multi-class crop field identification framework for UAV RGB imagery is proposed based on Semantic–SAM fusion. This framework combines the class recognition ability of semantic segmentation models with the boundary refinement ability of SAM. As a result, it mainly improves boundary quality while preserving crop category information, without manual prompts or additional SAM fine-tuning.

An automatic prompt generation method is also designed. High-confidence points and minimum bounding boxes are generated from the initial segmentation results and then used as prompts for SAM. This approach links semantic information with geometric constraints and makes SAM more suitable for agricultural remote sensing tasks.

Different semantic backbones and prompt types were further compared under both same-region and different-region settings. The results show that the proposed framework improves performance in most cases, especially in boundary refinement and spatial gener- alization. Among the tested prompt types, the point-box prompt usually provides the most balanced and stable results.

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 29 of 32


## 5. Conclusions

To address the rough boundaries produced by semantic segmentation models and the lack of semantic discrimination in SAM, this study proposed a collaborative Semantic– SAM framework for automatic multi-class crop field mapping from UAV RGB imagery. In this framework, semantic segmentation models automatically generate high-confidence points and bounding boxes to guide SAM for zero-shot boundary refinement, enabling automated recognition without manual prompts or model fine-tuning. The main findings are as follows:

1. The framework showed its clearest advantage in boundary refinement and predic- tion stability, while changes in regional accuracy were model-dependent. In the same-region test, U-Net + SAM achieved the highest mIoU of 87.09% under box prompts, compared with 86.19% for the standalone U-Net. PSPNet + SAM showed a more balanced improvement under point-box prompts, with mIoU increasing from 78.99% to 83.13% and bmF1 increasing from 74.02% to 79.48%. These results indicate that the proposed framework can improve boundary quality while preserving crop semantic recognition. 2. The framework enhanced the spatial generalization ability of the models. In the different-region test, the improvement was most obvious for DeepLabv3+ + SAM under point-box prompts, with mIoU increasing from 67.22% to 73.45%, correspond- ing to a gain of 6.23 percentage points. This result indicates that the framework can reduce performance degradation caused by regional differences. 3. Point-box prompts performed best in most cases and showed the best overall stability. Systematic comparison showed that the combined use of point prompts and box prompts achieved the best balance between regional consistency and boundary fitting in most cases. The bounding box prompt provides a reliable spatial range constraint, while the high-confidence point prompt provides a key internal semantic anchor. 4. The current results showed that the proposed framework met the main evaluation requirements of this study. In the same-region test, PSPNet + SAM with point-box prompts improved mIoU from 78.99% to 83.13% and bmF1 from 74.02% to 79.48%. In the different-region test, DeepLabv3+ + SAM with point-box prompts improved mIoU from 67.22% to 73.45% and bmF1 from 66.47% to 69.18%. These results were consistent with the expected goal of improving regional metrics and boundary quality. Therefore, the proposed framework can improve crop recognition accuracy and crop field boundary segmentation in the same-region and different-region tests.

Overall, the proposed framework is promising for parcel-scale crop mapping from UAV RGB imagery. By improving both crop-type recognition and boundary delineation, it may provide useful support for crop monitoring, planting structure analysis, parcel inventory, and management-oriented applications in precision agriculture.

Author Contributions: Conceptualization: H.Y. and X.W.; methodology: H.Y. and X.W.; software: H.Y. and Q.L.; validation: H.Y., Q.L. and X.W.; formal analysis: H.Y. and X.W.; investigation: H.Y., Q.L., P.W. and S.H.; resources: X.W. and Q.L.; data curation: H.Y., Q.L., P.W. and S.H.; writing— original draft preparation: H.Y. and X.W.; writing—review and editing: H.Y. and X.W.; visualization: H.Y., Q.L., S.H. and P.W.; supervision: X.W. and J.S.; project administration: X.W. and J.S.; funding acquisition: X.W. and J.S. All authors have read and agreed to the published version of the manuscript.

Funding: This research was funded by the Xinjiang Uygur Autonomous Region Major Science and Technology Special Project (2022A02011-1) and the Xinjiang Uygur Autonomous Region Key Research and Development Project (2024B03023-2).

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 30 of 32

Data Availability Statement: The original contributions presented in this study are included in the article. Further inquiries can be directed to the corresponding author.

Acknowledgments: We would like to thank the editor and anonymous reviewers for their valuable comments and suggestions on this paper.

Conflicts of Interest: The authors declare no conflicts of interest.

Appendix A

This appendix provides detailed supplementary results to support the main analysis presented in Section 3.


> **Table A1 reports the per-class IoU and boundary F1-score for cotton, tomato, and corn**

> under the point-box prompt setting on both the same-region (A + B) and different-region (C)
test sets. It compares the results of the standalone semantic segmentation models without
SAM refinement and the corresponding Semantic–SAM models with SAM refinement.


> **Table A1. Per-Class IoU and Boundary F1-Score of Semantic–SAM Models under the Point-Box**

> Prompt Setting on the Same-Region (A + B) and Different-Region (C) Test Sets.

IoU(%) ∆IoU

bF1(%)

∆bF1(%) Without

Model Test Set Class

SAM With SAM Without

(%)

SAM With SAM

Cotton 85.47 86.02 +0.55 68.78 78.14 +9.36 Tomato 88.36 88.89 +0.53 87.9 83.63 −4.27 Corn 84.74 85.37 +0.63 70.83 71.38 +0.55

A + B

U-Net

Cotton 86.35 87.86 +1.51 63.48 66.57 +3.09 Tomato 86.91 88.49 +1.58 62.62 62.55 −0.07 Corn 74.06 76.13 +2.07 44.87 43.09 −1.78

C

Cotton 75.56 75.02 −0.54 70.72 69.72 −1 Tomato 90.53 94.88 +4.35 74.19 86.18 +11.99 Corn 75.25 75.22 −0.03 62.28 63.73 +1.45

A + B

DeepLabv3+

Cotton 70.86 76.54 +5.68 75.46 78.62 +3.16 Tomato 72.48 78.92 +6.44 69.78 75.36 +5.58 Corn 58.32 64.89 +6.57 54.16 53.56 −0.6

C

Cotton 75.84 76.62 +0.78 46.53 62.02 +15.49 Tomato 78.36 78.74 +0.38 45.06 45.40 +0.34 Corn 77.88 78.85 +0.97 41.72 53.63 +11.91

A + B

HRNet

Cotton 71.48 74.92 +3.44 45.79 51.75 +5.96 Tomato 67.24 68.11 +0.87 32.54 29.11 −3.43 Corn 62.43 68.71 +6.28 37.59 44.25 +6.66

C

Cotton 77.42 81.64 +4.22 67.82 76.04 +8.22 Tomato 86.38 91.29 +4.91 84.24 92.20 +7.96 Corn 73.17 76.46 +3.29 69.99 70.19 +0.2

A + B

PSPNet

Cotton 76.28 78.12 +1.84 74.98 75.61 +0.63 Tomato 72.36 76.44 +4.08 55.97 63.31 +7.34 Corn 69.28 74.46 +5.18 62.35 70.48 +8.13

C

Note: ∆IoU and ∆bF1 in-dicate the differences between the two settings. Positive values indicate improvement, and negative values indicate degradation.


> **Table A2 summarizes the complete macro-averaged results of all Semantic–SAM**

> models under point, box, and point-box prompts on the different-region test set.

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 31 of 32


> **Table A2. Macro-Averaged Segmentation Performance of Semantic–SAM Models under Different**

> Prompt Types on the Different-Region (C) Test Set.

Model Prompt

mIoU

mF1

bmIoU

bmF1

Type

(%)

(%)

(%)

(%)

Point 82.76 90.58 26.38 56.03 Box 85.03 92.15 31.4 59.99 Point + box 84.16 91.37 27.54 57.41

U-Net + SAM

Point 70.86 82.93 51.67 62.6 Box 72.14 83.46 52.98 66.64 Point + box 73.45 84.12 52.95 69.18

DeepLabv3+ + SAM

Point 69.84 82.21 20.77 43.22 Box 68.72 81.36 17.83 41.05 Point + box 70.58 82.74 18.75 41.71

HRNet + SAM

Point 75.62 85.83 51.78 70.14 Box 74.91 85.24 49.33 68.53 Point + box 76.34 86.24 51.01 69.81

PSPNet + SAM

Note: All metrics are macro-averaged over the three crop categories, excluding the background class. Point-box denotes the combined use of high-confidence point prompts and box prompts.


## References

1. FAO; IFAD; UNICEF; WFP; WHO. The State of Food Security and Nutrition in the World 2023: Urbanization, Agrifood Systems Transformation and Healthy Diets across the Rural–Urban Continuum; FAO: Rome, Italy, 2023. 2. IPCC. Summary for Policymakers. In Climate Change 2023: Synthesis Report; Lee, H., Romero, J., Eds.; Contribution of Working Groups I, II and III to the Sixth Assessment Report of the Intergovernmental Panel on Climate Change; IPCC: Geneva, Switzerland, 2023; pp. 1–34. 3. Olson, D.; Anderson, J. Review on Unmanned Aerial Vehicles, Remote Sensors, Imagery Processing, and Their Applications in Agriculture. Agron. J. 2021, 113, 971–992. [CrossRef] 4. Long, J.; Shelhamer, E.; Darrell, T. Fully Convolutional Networks for Semantic Segmentation. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), Boston, MA, USA, 7–12 June 2015; IEEE: New York, NY, USA, 2015; pp. 3431–3440. 5. Ronneberger, O.; Fischer, P.; Brox, T. U-Net: Convolutional Networks for Biomedical Image Segmentation. In Medical Image Computing and Computer-Assisted Intervention—MICCAI 2015; Navab, N., Hornegger, J., Wells, W.M., Frangi, A.F., Eds.; Springer International Publishing: Cham, Switzerland, 2015; pp. 234–241. 6. Chen, L.-C.; Zhu, Y.; Papandreou, G.; Schroff, F.; Adam, H. Encoder-Decoder with Atrous Separable Convolution for Semantic Image Segmentation. In Proceedings of the European Conference on Computer Vision (ECCV), Munich, Germany, 8–14 September 2018; Springer Nature: Berlin/Heidelberg, Germany, 2018; pp. 801–818. 7. Zhu, X.X.; Tuia, D.; Mou, L.; Xia, G.-S.; Zhang, L.; Xu, F.; Fraundorfer, F. Deep Learning in Remote Sensing: A Comprehensive Review and List of Resources. IEEE Geosci. Remote Sens. Mag. 2017, 5, 8–36. [CrossRef] 8. Kirillov, A.; Mintun, E.; Ravi, N.; Rolland, H.; Gustafson, L.; Xiao, T.; Isola, P.; Berg, A.C.; Lo, W.-Y.; Dollár, P.; et al. Segment Anything. In Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV), Paris, France, 1–6 October 2023; IEEE: New York, NY, USA, 2023; pp. 4015–4034. 9. Osco, L.P.; Wu, Q.; de Lemos, E.L.; Gonçalves, W.N.; Ramos, A.P.M.; Li, J.; Junior, J.M. The Segment Anything Model (SAM) for Remote Sensing Applications: From Zero to One Shot. Int. J. Appl. Earth Obs. Geoinf. 2023, 124, 103540. [CrossRef] 10. Zhang, C.; Yue, P.; Tapete, D.; Jiang, L.; Shangguan, B.; Huang, L.; Liu, G. A Deeply Supervised Image Fusion Network for Change Detection in High-Resolution Bi-Temporal Remote Sensing Images. ISPRS J. Photogramm. Remote Sens. 2020, 166, 183–200. [CrossRef] 11. Li, W.; Chen, K.; Chen, H.; Shi, Z. Geographical Knowledge-Driven Representation Learning for Remote Sensing Image Scene Classification. IEEE Trans. Geosci. Remote Sens. 2022, 60, 5405516. [CrossRef] 12. Tsouros, D.C.; Bibi, S.; Sarigiannidis, P.G. A Review on UAV-Based Applications for Precision Agriculture. Information 2019, 10, 349. [CrossRef] 13. Blaschke, T. Object Based Image Analysis for Remote Sensing. ISPRS J. Photogramm. Remote Sens. 2010, 65, 2–16. [CrossRef]

https://doi.org/10.3390/agriculture16101108

Agriculture 2026, 16, 1108 32 of 32

14. Duro, D.C.; Franklin, S.E.; Dubé, M.G. A Comparison of Pixel-Based and Object-Based Image Analysis with Selected Machine Learning Algorithms for the Classification of Agricultural Landscapes Using SPOT-5 HRG Imagery. Remote Sens. Environ. 2012, 118, 259–272. [CrossRef] 15. Maxwell, A.E.; Warner, T.A.; Fang, F. Implementation of Machine-Learning Classification in Remote Sensing: An Applied Review. Int. J. Remote Sens. 2018, 39, 2784–2817. [CrossRef] 16. Belgiu, M.; Drăgu¸t, L. Random Forest in Remote Sensing: A Review of Applications and Future Directions. ISPRS J. Photogramm. Remote Sens. 2016, 114, 24–31. [CrossRef] 17. Mountrakis, G.; Im, J.; Ogole, C. Support Vector Machines in Remote Sensing: A Review. ISPRS J. Photogramm. Remote Sens. 2011, 66, 247–259. [CrossRef] 18. Waldner, F.; Diakogiannis, F.I. Deep Learning on Edge: Extracting Field Boundaries from Satellite Images with a Convolutional Neural Network. Remote Sens. Environ. 2020, 245, 111741. [CrossRef] 19. Zhang, H.; Liu, M.; Wang, Y.; Shang, J.; Liu, G.; Li, Q.; Ji, Y.; Wu, B. Automated Delineation of Agricultural Field Boundaries from Sentinel-2 Images Using Recurrent Residual U-Net. Int. J. Appl. Earth Obs. Geoinf. 2021, 105, 102557. [CrossRef] 20. Maggiori, E.; Tarabalka, Y.; Charpiat, G.; Alliez, P. Can Semantic Labeling Methods Generalize to Any City? The Inria Aerial Image Labeling Benchmark. In Proceedings of the IEEE International Geoscience and Remote Sensing Symposium (IGARSS), Fort Worth, TX, USA, 23–28 July 2017; IEEE: New York, NY, USA, 2017; pp. 3226–3229. 21. Persello, C.; Tolpekin, V.A.; Bergado, J.R.; de By, R.A. Delineation of Agricultural Fields in Smallholder Farms from Satellite Images Using Fully Convolutional Networks and Combinatorial Grouping. Remote Sens. Environ. 2019, 231, 111253. [CrossRef] 22. Ma, L.; Cheng, L.; Han, W.; Zhong, L.; Li, M. Cultivated Land Information Extraction from High-Resolution Unmanned Aerial Vehicle Imagery Data. J. Appl. Remote Sens. 2014, 8, 083673. [CrossRef] 23. Tripathy, P.; Baylis, K.; Wu, K.; Watson, J.; Jiang, R. Investigating the Segment Anything Foundation Model for Mapping Smallholder Agriculture Field Boundaries Without Training Labels. arXiv 2024, arXiv:2407.01846. [CrossRef] 24. Ferreira, L.B.; Martins, V.S.; Aires, U.R.V.; de Carvalho, O.L.; Guimarães, R.F.; Gomes, R.A.T. FieldSeg: A Scalable Agricultural Field Extraction Framework Based on the Segment Anything Model and 10-m Sentinel-2 Imagery. Comput. Electron. Agric. 2025, 232, 110086. [CrossRef] 25. Zhang, D.; Li, Y.; Shen, Y.; Guo, H.; Wei, H.; Cui, J.; Wu, G.; He, T.; Wang, L.; Liu, X.; et al. A Dual-Branch Framework Integrating the Segment Anything Model and Semantic-Aware Network for High-Resolution Cropland Extraction. Remote Sens. 2025, 17, 3424. [CrossRef] 26. Dong, Y.; Wang, H.; Zhang, Y.; Du, X.; Li, Q.; Wang, Y.; Shen, Y.; Zhang, S.; Xiao, J.; Xu, J.; et al. Accurate Parcel Extraction Combined with Multi-Resolution Remote Sensing Images Based on SAM. Agriculture 2025, 15, 976. [CrossRef] 27. Li, F.; Zhang, H.; Sun, P.; Zou, X.; Liu, S.; Yang, J.; Li, C.; Zhang, L.; Gao, J. Semantic-SAM: Segment and Recognize Anything at Any Granularity. arXiv 2023, arXiv:2307.04767. [CrossRef] 28. Chen, Y. Analysis of Drought Climate in Changji Prefecture. Xinjiang Meteorol. 1994, 5, 25–29. 29. Jiang, J.; Hu, Q.; Chu, X.; Zhang, K.; Wang, X.; Wang, S.; Guo, Y. Spatiotemporal Variations of Wind Erosion Climatic Erosivity and Key Driving Factors in the Arid Desert Region of Northwest China on Multiple Time Scales. Desert Oasis Meteorol. 2025, 19, 13–22. 30. Halderhan, A. Characteristics of Temperature and Precipitation Changes in Changji City from 1960 to 2021. Mod. Agric. Sci. Technol. 2023, 1, 151–154. 31. Rouzi, A.; Huoyihazi, Y.; Huang, L.; Wang, Y.; Shanati. Changes of Precipitation and Evaporation in Changji City in Recent 50 Years. J. Nanjing Univ. Inf. Sci. Technol. Nat. Sci. Ed. 2015, 7, 368–373. [CrossRef] 32. Rui, J.; Rui, J.; Huang, Q.; Huoyihazi, Y.; Liu, H. Analysis of Influence of Meteorological Conditions on Cotton Yield in Changji, Xinjiang. China Cotton 2024, 51, 1–7. [CrossRef] 33. Airbus. Pléiades: Very High-Resolution 50 cm Satellite Imagery. Available online: https://space-solutions.airbus.com/imagery/our- optical-and-radar-satellite-imagery/pleiades/ (accessed on 3 May 2026). 34. NASA. WorldView-1 Level 1B Panchromatic Satellite Imagery. NASA Open Data Portal. Available online: https://data.nasa.gov/dataset/worldview-1-level-1b-panchromatic-satellite-imagery (accessed on 3 May 2026). 35. Zeng, J.; Gu, Y.; Qin, C.; Jia, X.; Deng, S.; Xu, J.; Tian, H. Unsupervised Domain Adaptation for Remote Sensing Semantic Segmentation with the 2D Discrete Wavelet Transform. Sci. Rep. 2024, 14, 23552. [CrossRef]

Disclaimer/Publisher’s Note: The statements, opinions and data contained in all publications are solely those of the individual author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to people or property resulting from any ideas, methods, instructions or products referred to in the content.

https://doi.org/10.3390/agriculture16101108
