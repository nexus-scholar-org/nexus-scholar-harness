---
workspace_id: SCI-001084
doi: 10.15625/vap.2026.0019
title: A Preliminary Study on U-Net for Crop Monitoring Using Low-Altitude Drone Imagery
authors:
- family_name: Thang
  given_name: Pham Manh
  orcid: null
- family_name: Truong
  given_name: Hoang-Vu
  orcid: null
- family_name: Manh
  given_name: Hoang Van
  orcid: null
- family_name: Nam
  given_name: Do
  orcid: null
- family_name: Viet
  given_name: D.
  orcid: null
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T01:48:54.305342+00:00'
---

# A Preliminary Study on U-Net for Crop Monitoring Using Low-Altitude Drone Imagery

The 8th International Conference on                       Engineering Mechanics and Automation (ICEMA 2025)

Hanoi, November 14-15, 2025

DOI: 10.15625/vap.2026.0019

A Preliminary Study on U-Net for Crop  Monitoring Using Low-Altitude Drone Imagery

Pham Manh Thang   Faculty of Engineering   Mechanics and Automation,  VNU University of Engineering and

Ho Quang Truong*  Faculty of Engineering   Mechanics and Automation,  VNU University of Engineering and

Hoang Van Manh   Faculty of Engineering   Mechanics and Automation,  VNU University of Engineering and

Technology   Hanoi, Viet Nam  thangpm@vnu.edu.vn

Technology  Hanoi, Viet Nam  truongho@vnu.edu.vn

Technology  Hanoi, Viet Nam  manhhv87@vnu.edu.vn

Do Nam   Faculty of Engineering   Mechanics and Automation,  VNU University of Engineering and

Dang Anh Viet   Faculty of Electronics and  Communications. VNU University of

Engineering and Technology

Technology  Hanoi, Viet Nam  namd@vnu.edu.vn

Hanoi, Viet Nam  vietda@vnu.edu.vn

Abstract—Crop growth monitoring is crucial for precision agriculture, yet traditional methods lack scalability and accuracy.  This study develops and evaluates lightweight deep learning architectures for semantic segmentation of weeds, crops, and bare  soil from low-altitude multispectral UAV imagery. We systematically compared four U-Net based variants: standard U-Net,  Attention enhanced, ResNet augmented, and a proposed SCSE embedded version, against the DeepLabV3+ benchmark on the  standardized WeedsGalore dataset. The central hypothesis was that optimized U-Net architectures could match the accuracy  of DeepLabV3+ while being substantially more efficient. Results support this: enhanced variants achieved mean Intersection- over-Union (mIoU) values close to DeepLabV3+, with the attention-based model reducing parameter size by 21.1% and  maintaining nearly equivalent accuracy. The developed ResUNet SCSE performed best in weed segmentation, reaching an IoU  of 77.49% for the weed class. Both improved models also showed the lowest Expected Calibration Error (0.0019),  demonstrating improved reliability in uncertainty estimation. Overall, the findings highlight the viability of optimized U-Net  architectures for deployment on resource-constrained UAV platforms, offering an favorable trade-off between segmentation  accuracy and computational efficiency for automated agricultural monitoring.

Keywords—U-Net, Drone Imagery, Crop Growth Monitoring, Precision Agriculture, Deep Learning, Automation.

This study focuses on the development and evaluation  of several U-Net-based architectures [7] for the precise  segmentation of field components including crop canopy,  weeds, and bare soil from low-altitude UAV imagery. The  main objective is to compare the performance of these U- Net variants against the benchmark DeepLabV3+ model  [12]. All training and evaluation procedures were  conducted using the public WeedsGalore dataset [6],  strictly adhering to its original train/validation/test split to  ensure fair comparison and reproducibility.

I. INTRODUCTION

Crop growth monitoring is a core component of  Agriculture 4.0. Traditional approaches based on ground  sensors or manual field assessments are often labor- intensive, inconsistent, and limited in spatial coverage [1].  Although these methods can provide detailed point-based  measurements [2], they fail to scale effectively and to  capture spatial variability across large agricultural fields [3].

Among the key factors influencing crop development,  particularly in maize, is competition from weeds, which is  especially critical during the early growth stages. Timely  detection and distinction of weeds from young crops at this  stage are essential for ensuring yield, yet remain highly  challenging when performed manually on a large scale.

The central hypothesis of this work is that enhancing  the  baseline  U-Net  with  advanced  architectural  mechanisms can improve segmentation accuracy across  crop, weed, and soil regions. It is further hypothesized that  a well-optimized U-Net variant can achieve performance  comparable to larger benchmark models such as  DeepLabV3+, while being significantly lighter and more  deployment-friendly  for  large-scale  agricultural  monitoring.

Recent advances in Unmanned Aerial Vehicles  (UAVs) and Artificial Intelligence (AI) have enabled  automated crop monitoring through aerial imagery [4],  [5]. In particular, semantic segmentation models allow  accurate differentiation between objects in agricultural  scenes, automating tasks that were previously manual and  error-prone.

The main contributions of this study are summarized as  follows: (i) Training and evaluation of four U-Net variants  U-Net, Attention U-Net, ResUNet and ResUNet SCSE on

112

A Preliminary Study on U-Net for Crop Monitoring Using Low-Altitude Drone Imagery

the standardized dataset [6], following the official  train/val/test splits. (ii) Quantitative comparison of the  segmentation performance (e.g., mIoU) of the proposed U- Net variants against the published benchmark results of the  DeepLabV3+ model on the same test set. (iii) Analysis of  generalization capability and inference efficiency to  validate the feasibility of lightweight, high-performance U- Net architectures for automated agricultural monitoring  applications.

III. PROPOSED METHODOLOGY

This section presents the research methodology in  detail, including hardware simulation settings, dataset  description, AI architectures under investigation, and the  implementation details of the training and evaluation  process.

3.1. Hardware System

As this study is conducted at a preliminary feasibility  stage, no real UAV hardware was deployed. All  experiments used the public WeedsGalore multispectral  UAV dataset released by Helmholtz GFZ (2025), which  includes drone imagery of maize fields captured with  commercial UAVs equipped with RGB and five-channel  multispectral cameras flown at 10–20 m altitudes.

II. RELATED WORKS

Traditionally, crop monitoring relied on vegetation  indices (VIs) such as the NDVI (Normalized Difference  Vegetation Index) [13] and NDRE (Normalized Difference  Red Edge) [14], which use spectral reflectance differences  between the Red–NIR or Red-Edge–NIR bands to estimate  plant health and canopy density. While simple and  popular, these indices often saturate in dense canopies and  cannot distinguish between crops and weeds when both  appear healthy and green, showing limited semantic  differentiation [15][16].

Thus, this study adopts strictly the real-world UAV  acquisition  conditions  defined  by  the  dataset  documentation to ensure practical applicability. All inputs,  both raw images and labeled segmentation masks, were  taken directly from the dataset. The preprocessing pipeline  substitutes real data collection and ensures model  generalization to future UAV imagery. A field validation  using actual UAV imaging is planned for Phase 2 (2026)  once the models achieve stable performance and optimized  inference settings.

To overcome these limitations, deep learning–based  semantic segmentation methods have been adopted to  classify each pixel rather than summarize an image with a  single index. High-performing architectures such as  DeepLabV3+ [12], PSPNet [18], and SegNet [19] achieve  excellent accuracy by capturing multi-scale contextual  information through mechanisms like Atrous Spatial  Pyramid Pooling (ASPP) and Pyramid Pooling Modules,  but they are computationally heavy and resource- demanding.

3.2. Data Processing

This study employs the open-source “WeedsGalore”  dataset [6], which consists of 5-channel multispectral UAV  imagery of maize fields. The dataset was designed for  semantic segmentation of weeds, with the goal of  advancing precision agriculture through early weed  detection.

In contrast, the U-Net architecture [7] is known for  being lightweight and flexible. Its symmetric encoder– decoder structure with skip connections allows the network  to combine semantic (deep) and spatial (shallow)  information effectively, preserving fine boundary details, a  crucial feature for low-altitude UAV imagery, and  performing well even with moderate-sized datasets. From  the original U-Net, many variants have been proposed to  address specific limitations: Attention U-Net [8] introduces  attention gates to focus on relevant regions; ResUNet [9]  replaces standard convolutional blocks with residual ones  to enable deeper training; U-Net++ [17] uses dense skip  connections to improve feature fusion; and hybrid designs  integrate SCSE modules [11] or ASPP for enhanced multi- scale representation.

A key characteristic of WeedsGalore is its focus on  maize fields at the early growth stage, which is the most  critical period for applying weed control measures,  precisely aligning with the objective of this study.

`To ensure the integrity and comparability of experimental  results,  we  strictly  adhere  to  the  official  train/validation/test splits provided by the dataset authors.  All input images are standardized to a spatial resolution of  600×600 pixels.

3.3. AI Model Architectures

Four main variants of the U-Net architecture were  trained and evaluated in this research:

However, most prior works only compare their  proposed variants with the original U-Net, lacking  systematic, head-to-head evaluations across multiple U- Net variants on the same benchmark dataset. The  WeedsGalore dataset [6] provides a public multispectral  UAV benchmark (RGB, Red-Edge, NIR) with strong  baselines such as DeepLabV3+ and MaskFormer, yet no  comprehensive  assessment  of  lightweight  U-Net  architectures has been conducted on it. This study fills that  gap by systematically comparing several U-Net variants  (Attention, Residual, SCSE, etc.) against the DeepLabV3+  baseline on WeedsGalore, aiming to identify the best  balance between accuracy and computational efficiency for  multispectral crop monitoring.

- U-Net: The original U-Net [7] serves as the baseline  model. It is a classic encoder–decoder architecture with  skip connections, originally proposed for medical image  segmentation.

- Attention U-Net: The Attention U-Net [8] improves  upon U-Net by incorporating attention gates into skip  connections, allowing the network to emphasize salient  regions and suppress irrelevant background noise.

- ResUNet (Residual U-Net): ResUNet [9] replaces  the standard convolutional blocks in U-Net with residual  blocks, addressing gradient degradation and enabling  deeper networks.

113

Pham Manh Thang et al.

- ResUNet-SCSE (Integrated Architecture): The  primary architecture under investigation is ResUNet- SCSE, which combines several powerful design elements:  a residual backbone (ResUNet) for efficient deep feature  learning, an Atrous Spatial Pyramid Pooling (ASPP)  module [10] at the bottleneck for multi-scale contextual  feature extraction, and a Spatial-Channel Squeeze &  Excitation (scSE) module [11] applied to skip connections,  enabling simultaneous refinement of both channel-wise  and spatial attention.

For the U-Net and its variants, the batch size was set to  2 due to GPU memory constraints, and Group  Normalization (GN) was applied to ensure stable  optimization. In contrast, the DeepLabV3+ baseline  retained its original configuration with a batch size of 8  and Batch Normalization (BN) as specified in the official  implementation. These controlled settings ensure that all  models were trained under equivalent conditions for an  objective performance comparison.

IV. RESULT AND DISCUSSION

Additionally, DeepLabV3+ [12] with a ResNet-50  backbone was included as a reference baseline. To ensure a  fair comparison, we utilized the 5-channel (MSI)  pretrained checkpoint released by the WeedsGalore dataset  authors [6].

Following the training process described in Section 4,  the performance of the models was evaluated on the test  set of the WeedsGalore dataset.


> **Table 2. Quantitative segmentation performance of the**

evaluated models on the WeedsGalore test set

3.4. Evaluation Metrics

Model  IoU  (bg)

IoU  (crop)

IoU  (weed)

mIoU

Params

(M)  ECE

To enable a comprehensive evaluation of model  performance, this study employs a combination of standard  and advanced metrics.

(%)

U-Net   98.54  66.96  73.59  79.70  31.0  0.0020  Attention U-Net  98.55  72.53  77.39  82.82  31.4  0.0019  ResUNet  98.56  70.52  76.41  81.83  32.4  0.0029  ResUNet-SCSE  98.58  71.99  77.49  82.69  38.3  0.0019  DeepLabV3+   98.45  72.93  77.31  82.90  39.8  0.0046

The segmentation accuracy is primarily assessed using  the Intersection over Union (IoU) metric. IoU is computed  separately for each class: background (bg), crop, and weed,  allowing for a detailed analysis of how well each model  distinguishes between individual object categories. The  Mean Intersection over Union (mIoU), calculated as the  average IoU across all three classes, serves as the principal  measure for comparing overall segmentation performance  among the evaluated architectures.

The quantitative evaluation results of segmentation  performance on the test dataset are summarized in Table 2.  This table compares several U-Net variants (Baseline U- Net, Attention U-Net, and ResUNet-SCSE) with the state- of-the-art (SOTA) model DeepLabV3+, based on key  performance indicators including mIoU, class-wise IoU for  crop and weed, model complexity (Params), and  calibration quality measured by the Expected Calibration  Error (ECE).

Beyond  accuracy,  two  additional  aspects  are  considered: efficiency and reliability. The number of  parameters (Params, measured in millions) reflects the  complexity and size of each model, providing insights into  computational efficiency. Furthermore, the Expected  Calibration Error (ECE) is adopted as an advanced metric  to evaluate the confidence calibration of model  predictions. ECE quantifies the discrepancy between a  model‟s predicted confidence and its actual accuracy. A  lower ECE value indicates better calibration, meaning the  model‟s confidence aligns more closely with reality and it  is more reliable, capable of recognizing when its  predictions are uncertain.

Among all evaluated architectures, DeepLabV3+  achieved the highest overall performance with an mIoU of  82.90%. However, the leading U-Net variants exhibited  highly competitive results: Attention U-Net reached  82.82% mIoU, only 0.08% lower than DeepLabV3+,  followed closely by ResUNet-SCSE with 82.69% mIoU.  In contrast, the baseline U-Net showed a considerably  lower performance, achieving 79.70% mIoU.

A closer look at class-wise segmentation reveals that  ResUNet-SCSE achieved the highest IoU-Weed (77.49%),  indicating superior capability in detecting weed regions.  In terms of computational efficiency, the SOTA  DeepLabV3+  was  the  most  complex  architecture,  containing 39.8 million parameters. By comparison, U-Net  variants were substantially lighter: Attention U-Net (31.4M  parameters) and Baseline U-Net (31.0M parameters).

3.5. Implementation Details

All models were implemented using the official  training pipeline and codebase provided with the dataset,  ensuring consistency and reproducibility. The common  training configurations were as follows:


> **Table 1. Training configuration of the evaluated models.**

Relative to DeepLabV3+, Attention U-Net reduced  model size by 21.1% (≈8.4 million parameters) while  maintaining nearly identical accuracy.

Parameter  Setting

Optimizer  Adam

Regarding model reliability, DeepLabV3+ recorded the  highest ECE value (0.0046), reflecting overconfidence in  predictions. In contrast, both Attention U-Net and  ResUNet-SCSE achieved the lowest ECE value (0.0019),  suggesting better calibration and more reliable uncertainty  estimation.

Learning Rate  0.001

Epochs  25

Data Augmentation  Random rotation, flipping enabled

and Gaussian noise jitter

Loss Function  Cross-Entropy Loss

To complement the quantitative analysis presented in  Table 2, this section provides qualitative evaluation results.  Fig. 1 contains two representative examples: the top row

The main differences among models lie in the batch  size and normalization strategy.

114

A Preliminary Study on U-Net for Crop Monitoring Using Low-Altitude Drone Imagery

illustrates a challenging case with a high density of  overlapping weeds (hard example), while the bottom row  shows an easier scene with a clearer separation between  crops and weeds (easy example). This figure provides a  visual comparison of model performance under two  different difficulty levels, where crop regions (green) and  weed regions (blue) are interwoven.

Quantitative results supported the study‟s main  hypothesis: optimized U-Net variants can achieve  competitive performance compared to DeepLabV3+.  Specifically,  Attention  U-Net  and  ResUNet-SCSE  performed only marginally lower in terms of mean  Intersection-over-Union  (mIoU),  demonstrating  the  effectiveness of architectural enhancements. In contrast,  the  baseline  U-Net  showed  significantly  lower  performance, underscoring the importance of advanced  design components.

The most evident observation is the poor performance  of the baseline U-Net (Fig. 1c), which misses a large  portion of weed areas and misclassifies several crop pixels  as weeds in the upper-right region. This “noisy”  segmentation outcome is consistent with its lowest overall  mIoU (79.70%). The ResUNet (Fig. 1e) exhibits a slight  improvement by capturing small weed patches on the left  side, but still fails to segment them accurately. A clear  improvement is observed in the Attention U-Net (Fig. 1d),  where the integration of attention gates enables the model  to recover almost all weed regions missed by U-Net and  ResUNet. This explains its +3.12% mIoU increase (Table  2), achieved with only an additional 0.4M parameters.

In terms of computational efficiency, the U-Net family  exhibited a clear advantage. Attention U-Net reduced  model size by approximately 21.1% compared to  DeepLabV3+  while  maintaining  nearly  equivalent  accuracy. Notably, ResUNet-SCSE excelled in weed  segmentation, achieving the highest IoU for weed class  (77.49%) among all tested architectures. This success was  attributed to the combination of residual blocks for deeper  feature learning, an Atrous Spatial Pyramid Pooling  (ASPP) module at the bottleneck for multi-scale context  aggregation, and a Spatial and Channel Squeeze-and- Excitation (SCSE) module to enhance attention both  spatially and across feature channels.

More advanced architectures, such as ResUNet-SCSE  (Fig. 1f) and DeepLabV3+ (Fig .1g), produce the most  accurate segmentations, closely matching the ground-truth  labels (Fig .1b). Notably, ResUNet-SCSE demonstrates  sharper boundary preservation, consistent with its highest  IoU-Weed score (77.49%).

Another significant finding relates to model calibration.  While DeepLabV3+ reported the highest Expected  Calibration Error (ECE), both Attention U-Net and  ResUNet-SCSE achieved the lowest ECE values,  suggesting that these optimized U-Net models are better  calibrated and provide more reliable uncertainty estimates,  a key factor in automated decision-making for precision  agriculture.

However, Fig. 1 also reveals a common limitation  shared across all models. In regions with dense weed  coverage, where weeds and crops are highly intertwined  and partially occluded, even the state-of-the-art models  tend to merge weeds into crop regions. This limitation  highlights an open challenge for future research aimed at  improving segmentation robustness under high-density  occlusion conditions.

In summary, the study confirms the viability of  lightweight U-Net-based architectures. When enhanced  with components like residual connections and attention  mechanisms, these models deliver high performance on  complex multispectral datasets, and are better suited for  deployment  on  UAV  platforms  with  constrained  computational  resources  in  automated  agricultural  monitoring applications. Nonetheless, a shared challenge  remains: even the most advanced models struggle to  segment vegetation accurately under dense canopy  occlusion. Improving segmentation performance in such  conditions will be a focal point for future research.

V. CONCLUSION

This study conducted a systematic evaluation, directly  comparing four variants of the U-Net architecture, namely  U-Net, Attention U-Net, ResUNet, and ResUNet-SCSE,  against the DeepLabV3+ model, which served as a  benchmark. The evaluation was carried out using the  publicly available WeedsGalore multispectral UAV  dataset, aiming to identify lightweight architectures that  offer the best trade-off between segmentation accuracy and  computational efficiency for aerial crop monitoring.

a. RGB  b. Ground Truth  c. U-Net  d. Attention U-Net  e. ResUNet  f. ResUNet-SCSE  g. DeepLabV3+

Fig. 1. Qualitative comparison of model performance in challenging scenarios (top row) and typical scenarios (bottom row).

115

Pham Manh Thang et al.

[11] A. G. Roy, N. Navab, and C. Wachinger, “Concurrent

ACKNOWLEDGEMENT

Spatial and Channel „Squeeze & Excitation‟ in Fully  Convolutional Networks,” in Proc. Int. Conf. Med. Image  Comput. Comput.-Assist. Interv. (MICCAI), vol. 11070,  2018, pp. 421–429.  [12] L.-C. Chen, Y. Zhu, G. Papandreou, F. Schroff, and H.

This research has been supported/partly supported by  the research project QG.24.83 of Vietnam National  University, Hanoi and project CN25.06 by VNU  University of Engineering and Technology.

Adam,  “Encoder–Decoder  with  Atrous  Separable  Convolution for Semantic Image Segmentation,” in Proc.  Eur. Conf. Comput. Vis. (ECCV), 2018, pp. 833–851.  [13] C. J. Tucker, “Red and photographic infrared linear


## REFERENCES

[1] M. Weiss, F. Jacob, and G. Duveiller, “Remote sensing for

agricultural applications: A meta-review,” Remote Sensing  of Environment, vol. 236, p. 111402, Jan. 2020.  [2] H. G. Jones, “Irrigation scheduling: advantages and pitfalls

combinations for monitoring vegetation,” Remote Sensing  of Environment, vol. 8, no. 2, pp. 127–150, May 1979  [14] E. M. Barnes et al., “Coincident detection of crop water

of plant-based methods,” Journal of Experimental Botany,  vol. 55, no. 407, pp. 2427–2436, 2004.  [3] C. Zhang and J. M. Kovacs, “The application of small

stress, nitrogen status and canopy density using ground- based multispectral data,” in Proc. 5th Int. Conf. Precision  Agriculture, 2000.  [15] C. Yancho-Brune et al., “Demystifying NDVI for public

unmanned aerial systems for precision agriculture: A  review,” Precision Agriculture, vol. 13, no. 6, pp. 693–712,  2012.  [4] A. Kamilaris and F. X. Prenafeta-Boldú, “Deep learning in

health and ecology,” Environmental Research, vol. 208,  2022, Art. no. 112685.  [16] Q. Liu et al., “Evaluating the saturation effect of vegetation

agriculture: A survey,” Computers and Electronics in  Agriculture, vol. 147, pp. 70–90, 2018.  [5] T. Kattenborn, J. Eicher, and F. E. Fassnacht, “A critical

indices in forests,” Remote Sensing of Environment, vol.  294, 2023, Art. no. 113651.  [17] Z. Zhou, M. M. R. Siddiquee, N. Tajbakhsh, and J. Liang,

review of remote sensing data products for precision  agriculture,” European Journal of Remote Sensing, vol. 54,  suppl. 2, pp. 119–147, 2021.  [6] E. Celikkan, T. Kunzmann, Y. Yeskaliyev, S. Itzerott, N.

“U-Net++: A Nested U-Net Architecture for Medical Image  Segmentation,” in Deep Learning in Medical Image  Analysis and Multimodal Learning for Clinical Decision  Support (DLMIA 2018), Lecture Notes in Computer  Science, vol. 11045. Cham, Switzerland: Springer, 2018,  pp. 3–11.  [18] H. Zhao et al., “Pyramid Scene Parsing Network,” in Proc.

Klein, and M. Herold, “WeedsGalore: A Multispectral and  Multitemporal UAV-Based Dataset for Crop and Weed  Segmentation in Agricultural Maize Fields,” in Proc.  IEEE/CVF Winter Conf. Appl. Comput. Vis. (WACV), 2025,  pp. 4767–4777.  [7] O. Ronneberger, P. Fischer, and T. Brox, “U-Net:

IEEE Conf. on Computer Vision and Pattern Recognition  (CVPR), 2017, pp. 2881–2890.  [19] V. Badrinarayanan, A. Kendall, and R. Cipolla, “SegNet: A

Convolutional  Networks  for  Biomedical  Image  Segmentation,” in Proc. Int. Conf. Med. Image Comput.  Comput.-Assist. Interv. (MICCAI), 2015, pp. 234–241.  [8] O. Oktay, J. Schlemper, L. Le Folgoc, et al., “Attention U-

Deep Convolutional Encoder–Decoder Architecture for  Image Segmentation,” IEEE Trans. Pattern Anal. Mach.  Intell., vol. 39, no. 12, pp. 2481–2495, 2017.

Net: Learning Where to Look for the Pancreas,” arXiv  preprint arXiv:1804.03999, 2018.  [9] Z. Zhang, Q. Liu, and Y. Wang, “Road Extraction by Deep

Residual U-Net,” IEEE Geosci. Remote Sens. Lett., vol. 15,  no. 5, pp. 749–753, 2018. (Originally arXiv preprint  arXiv:1711.10684, 2017.)  [10] L.-C. Chen, G. Papandreou, F. Schroff, and H. Adam,

“Rethinking Atrous Convolution for Semantic Image  Segmentation,”  arXiv preprint arXiv:1706.05587, 2017.

116
