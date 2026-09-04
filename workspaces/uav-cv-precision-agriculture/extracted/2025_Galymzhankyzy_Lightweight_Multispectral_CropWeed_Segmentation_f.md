---
workspace_id: SCI-000001
doi: 10.48550/arxiv.2505.07444
title: Lightweight Multispectral Crop-Weed Segmentation for Precision Agriculture
authors:
- family_name: Galymzhankyzy
  given_name: Zeynep
  orcid: null
- family_name: Martinson
  given_name: Eric
  orcid: null
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T01:48:54.007240+00:00'
---

# Lightweight Multispectral Crop-Weed Segmentation for Precision Agriculture

Lightweight Multispectral Crop-Weed Segmentation

for Precision Agriculture

Zeynep Galymzhankyzy Department of Math and Computer Science

Eric Martinson Department of Math and Computer Science

Lawrence Technological University

Lawrence Technological University

Southfield, MI, USA

Southfield, MI, USA

zgalymzha@ltu.edu

emartinso@ltu.edu

arXiv:2505.07444v1  [cs.CV]  12 May 2025

inference on UAVs, offering high accuracy and computational efficiency.


## Abstract—Efficient crop-weed segmentation is critical for site-

specific weed control in precision agriculture. Conventional CNN-
based methods struggle to generalize and rely on RGB imagery,
limiting performance under complex field conditions. To address
these challenges, we propose a lightweight transformer-CNN
hybrid. It processes RGB, Near-Infrared (NIR), and Red-Edge
(RE) bands using specialized encoders and dynamic modality
integration. Evaluated on the WeedsGalore dataset [5], the
model achieves a segmentation accuracy (mean IoU) of 78.88%,
outperforming RGB-only models by 15.8 percentage points. With
only 8.7 million parameters, the model offers high accuracy,
computational efficiency, and potential for real-time deployment
on Unmanned Aerial Vehicles (UAVs) and edge devices, advancing
precision weed management.

II. RELATED WORK

A. Deep Learning Methods for Weed Segmentation

Early approaches relied on handcrafted features and clas- sifiers like Random Forests [1]. While computationally effi- cient, these methods lacked robustness to field variability and required manual feature engineering.

Convolutional Neural Networks (CNNs) significantly im- proved segmentation accuracy. For WeedMap, Sa et al. [2] used a modified SegNet, achieving strong performance for background and crop classes but lower accuracy for weeds. Celikkan et al. [5] evaluated DeepLabv3+ and MaskFormer on WeedsGalore, achieving mean Intersection over Union (mIoU) scores above 82% with multispectral inputs. However, CNNs often require deep architectures to model long-range dependencies, increasing computational demands and limiting efficiency on UAV platforms [13].

Index Terms—Crop–Weed Segmentation, Multispectral Im- agery, UAV, Transformer, Semantic Segmentation, Precision Agri- culture, Dynamic Fusion

I. INTRODUCTION

Weed management is a critical challenge in precision agri- culture, where accurate and timely identification of weeds enables site-specific control, reducing herbicide use and boost- ing crop yields. Recent advances in deep learning, particu- larly convolutional neural networks (CNNs), have improved crop–weed segmentation by analyzing field imagery. However, existing methods face significant limitations. Many rely solely on RGB imagery, which struggles to generalize across diverse vegetation types and lighting conditions, such as shadows or overcast skies. Additionally, static fusion strategies for com- bining multiple data types, like RGB and infrared, lack robust- ness to sensor noise or missing data, limiting their reliability in real-world settings. Transformer models, while effective at capturing complex patterns, are often too computationally intensive for deployment on resource-constrained Unmanned Aerial Vehicles (UAVs). Real-time performance, essential for practical UAV-based applications, remains underexplored in models using multispectral data, such as Near-Infrared (NIR) and Red-Edge (RE) bands.

Vision Transformers (ViTs) have recently gained traction for weed segmentation. Castellano et al. [6] proposed lightweight variants, Lawin and DoubleLawin, outperforming DeepLabv3 on WeedMap. Reedha et al. [7] and Wang et al. [9] showed that transformers excel at capturing global shape and context, crucial for distinguishing overlapping or visually similar vege- tation. However, many ViTs remain computationally intensive, hindering real-time deployment.

B. Multispectral Fusion Strategies

Multispectral imagery provides spectral cues beyond RGB. NIR reflects plant health by capturing canopy structure, while RE detects chlorophyll variations, aiding crop–weed differen- tiation. Common fusion methods, such as channel stacking or concatenation, treat modalities equally, ignoring variations in quality or relevance.

WeedsGalore [5] demonstrated that combining RGB, NIR, and RE improves segmentation over RGB-only models, partic- ularly for rare weed classes. However, most fusion methods are static and cannot adapt to modality noise or dropouts. There is a need for adaptive fusion mechanisms that dynamically prior- itize modalities based on their relevance or quality, enhancing robustness to environmental variability.

To address these challenges, we propose a lightweight transformer–CNN hybrid model for efficient crop–weed seg- mentation. Our approach uses multispectral imagery (RGB, NIR, RE) through specialized encoders and a dynamic fusion mechanism that adapts to varying field conditions. With only 8.7 million parameters, the model is optimized for real-time

Accepted to the Novel Approaches for Precision Agriculture and Forestry with Autonomous Robots IEEE ICRA Workshop - 2025

Fig. 1. WeedsGalore dataset: acquisition and annotation workflow. Reprinted from [5].

C. UAVs and Real-Time Constraints

Fig. 2. WeedsGalore dataset: example tile with RGB, NIR, and Red-Edge channels, alongside the remapped 3-class segmentation mask.

UAVs are increasingly used to collect high-resolution, geo- referenced multispectral data. Orthomosaic generation and pixel-level annotations enable large-scale field analysis, but real-time deployment remains challenging. CNNs and trans- formers often incur high memory and latency costs, limiting their use on resource-constrained UAV platforms.

• High annotation density: Over 10,081 plant polygons, with an average of 78 instances per tile, offer a challeng- ing benchmark for small-object segmentation, surpassing datasets like CWFID.

Lightweight transformer–CNN hybrids offer a promising solution, balancing efficiency and performance with multi- spectral inputs, as demonstrated in tasks like image super- resolution [17]. Our proposed architecture addresses these challenges through modular spectral encoding, adaptive gated fusion, and efficient pyramid-based decoding, optimized for UAV-based precision agriculture.

• Public baselines: Performance scores for DeepLabv3+ and MaskFormer, using both RGB and Multispectral Input (MSI), provide robust baselines for comparison. For multimodal segmentation, each tile is processed into a 5- channel array (RGB, NIR, Red-Edge) and resized to 600×600 pixels. Semantic masks are remapped into three categories: background, crop, and weed. On-the-fly augmentations, in- cluding random flips and rotations, are applied during train- ing to improve generalization. This combination of spectral diversity, dense annotations, and temporal variation makes WeedsGalore ideal for evaluating dynamic modality weighting and Transformer-based segmentation models.

III. MULTISPECTRAL AND MULTITEMPORAL DATA

The WeedsGalore dataset [5] is a publicly available bench- mark for semantic and instance-level segmentation in maize fields, collected using an Unmanned Aerial Vehicle (UAV). Data was acquired over a 1,840 m2 agricultural plot in Marquardt, Germany, with a DJI Phantom P4 Multispectral UAV. Four flights, conducted between May and June 2023, captured high-resolution imagery at a 5 m altitude, achieving a ground sampling distance (GSD) of 2.5 mm.

With its high-resolution 2.5 mm GSD, multispectral rich- ness, and multitemporal coverage, WeedsGalore is well- suited for developing site-specific weed management algo- rithms. By benchmarking on this dataset, we demonstrate that Transformer-driven multimodal fusion enhances segmentation accuracy while remaining efficient for real-time UAV infer- ence.

Each flight produced approximately 1,150 raw frames, from which 156 image tiles of 600×600 pixels were manually cropped and annotated. The tiles are labeled across five seman- tic categories: maize, amaranth, barnyard grass, quickweed, and other weeds, representing common crops and weed species in Central European maize farming. The dataset is spatially split into 109 training (70%), 23 validation (15%), and 24 test (15%) tiles, ensuring no spatial overlap between splits.

IV. PROPOSED METHODOLOGY

A. Model Architecture

The proposed lightweight transformer–CNN hybrid is de- signed for multispectral crop–weed segmentation using Un- manned Aerial Vehicle (UAV) imagery. It processes five- channel inputs—RGB, Near-Infrared (NIR), and Red-Edge (RE)—through modality-specific convolutional encoders that extract low-level spatial features. Each modality stream is refined by dedicated Transformer blocks to capture long-range spatial dependencies.

WeedsGalore stands out due to several key features:

• Multispectral coverage: RGB, Red-Edge (730 nm), and Near-Infrared (NIR, 840 nm) bands provide rich spectral information, enhancing crop–weed separability compared to RGB-only datasets.

• Multitemporal sampling: Four flights capture distinct plant growth stages, enabling models to learn robustly across temporal variations.

A key component, the Gated Fusion Module, dynami- cally weighs each spectral modality using learned weights,

Accepted to the Novel Approaches for Precision Agriculture and Forestry with Autonomous Robots IEEE ICRA Workshop - 2025

Fig. 3. Architecture of the lightweight transformer–CNN hybrid, showing modality-specific encoding, Transformer refinement, gated fusion, and pyramid-based decoding.

prioritizing the most informative inputs under varying field conditions, such as sensor noise or lighting changes. The fused representation is processed by a Pyramid Pooling Module, which captures global context at multiple scales and integrates skip connections to refine fine-grained boundaries.

The final output is a high-resolution segmentation map distinguishing background, crop, and weed classes. With a compact footprint of 8.7 million parameters, the model is optimized for efficiency and suitable for real-time inference on embedded platforms, such as UAV-mounted NVIDIA Jetson devices. This balance of accuracy and computational efficiency makes it a strong candidate for site-specific weed management in precision agriculture. The full architecture is illustrated in Fig. 3.

Fig. 4. Segmentation by the MSI model: RGB input (left), ground truth (cen- ter), predicted mask (right). Note the accurate delineation of crop boundaries.

B. Training and Evaluation

To implement the model for crop–weed segmentation, we trained it on the WeedsGalore dataset [5], using 109 training and 23 validation tiles, each resized to 600 × 600 pixels. A combination of Cross-Entropy Loss and Class-Balanced Focal Loss addressed weed class imbalance. The AdamW optimizer was employed with an initial learning rate of 1e−4, cosine annealing, and a batch size of 8. Data augmentations, including random flips and rotations, were applied, and training ran for 100 epochs with mixed precision. To evaluate performance, we assessed the model using mean Intersection-over-Union (mIoU), per-class IoU, and overall accuracy on a held-out test set of 24 images. All experiments maintained consistent preprocessing, augmentation, and class remapping into three categories: background, crop, and weed. The Multispectral Input (MSI) model, using RGB, NIR, and RE, achieved an mIoU of 78.88%, demonstrating robust segmentation of crop and weed regions. In contrast, the RGB- only variant yielded a lower mIoU of 63.08%, often misclas- sifying visually similar crop clusters as weeds, underscoring the importance of spectral diversity.

Fig. 5. Segmentation by the RGB-only model: limited differentiation of dense weeds from crops.

grained weed structures and maintains sharp boundaries. Con- versely, the RGB-only model (Fig. 5) struggles in low-contrast scenes, reinforcing the value of multispectral features for reliable performance under real-world field conditions.

C. Comparison with Baselines

To contextualize the model’s performance, we compared it with two baselines from [5]: DeepLabv3+ and MaskFormer. DeepLabv3+ achieves a higher mIoU of 82.90% with mul- tispectral input but relies on static early fusion and has a larger footprint of 41.2M parameters. Similarly, MaskFormer attains 79.55% mIoU but is transformer-heavy, with 43.1M

Qualitative analysis further highlights these findings. As shown in Fig. 4, the MSI model accurately captures fine-

Accepted to the Novel Approaches for Precision Agriculture and Forestry with Autonomous Robots IEEE ICRA Workshop - 2025

[3] J. Weyler et al., “PhenoBench: A large dataset and benchmarks for

TABLE I PERFORMANCE COMPARISON WITH BASELINES (MULTISPECTRAL INPUT)

semantic image interpretation in the agricultural domain,” IEEE Trans. Pattern Anal. Mach. Intell., vol. 46, no. 12, pp. 9583–9594, 2024. [4] D. Steininger et al., “The CropAndWeed Dataset: A multi-modal

Model mIoU (%) Params (M) Edge-Ready DeepLabv3+ [5] 82.90 41.2 No MaskFormer [5] 79.55 43.1 No Ours 78.88 8.7 Yes

learning approach for efficient crop and weed manipulation,” in Proc. IEEE/CVF WACV, pp. 3729–3738, 2023. [5] E. Celikkan et al., “WeedsGalore: A multispectral and multitemporal

UAV-based dataset for crop and weed segmentation in agricultural maize fields,” in Proc. IEEE/CVF WACV, pp. 4767–4777, 2025. [6] G. Castellano, P. D. Marinis, and G. Vessio, “Weed mapping in

multispectral drone imagery using lightweight vision transformers,” Neurocomputing, vol. 562, p. 126914, 2023. [7] R. Reedha et al., “Transformer neural network for weed and crop

parameters, making it unsuitable for real-time UAV inference. In contrast, our model achieves 78.88% mIoU with only 8.7M parameters, offering an efficient, modular alternative that dynamically fuses spectral cues. This trade-off between accuracy and efficiency positions the model as well-suited for embedded weed segmentation systems.

classification of high resolution UAV images,” Remote Sensing, vol. 14, no. 3, p. 592, 2022. [8] N. Genze et al., “Deep learning-based early weed segmentation using

motion blurred UAV images of sorghum fields,” Comput. Electron. Agric., vol. 202, p. 107388, 2022. [9] Y. Wang, S. Zhang, B. Dai, S. Yang, and H. Song, “Fine-grained weed

recognition using Swin Transformer and two-stage transfer learning,” Front. Plant Sci., vol. 14, p. 1134932, 2023. [10] J. You, W. Liu, and J. Lee, “A DNN-based semantic segmentation for

V. CONCLUSION

This work has proposed a lightweight transformer-CNN hy- brid architecture to conduct multispectral crop–weed segmen- tation for precision agriculture. Using an adaptive gated fusion mechanism that dynamically weights spectral channels, it demonstrates enhanced robustness to environmental variations on the WeedsGalore dataset [5], achieving 78.88% mIoU. This exceeds RGB-only models by 15.8 percentage points through the effective use of RGB, NIR, and RE bands for superior vegetation differentiation. With 8.7 million parameters, the architecture is also optimized for efficient inference to make it suitable for resource-constrained UAV platforms. Together, accuracy and efficiency make it a compelling solution for site-specific weed management, with potential for future edge deployment.

detecting weed and crop,” Comput. Electron. Agric., vol. 178, p. 105750, 2020. [11] A. Olsen et al., “DeepWeeds: A multiclass weed species image dataset

for deep learning,” Sci. Rep., vol. 9, no. 1, p. 2058, 2019. [12] Y. Zheng et al., “CropDeep: The crop vision dataset for deep-learning-

based classification and detection in precision agriculture,” Sensors, vol. 19, no. 5, p. 1058, 2019. [13] X. Wu et al., “Robotic weed control using automated weed and crop

classification,” J. Field Robotics, vol. 37, no. 2, pp. 322–340, 2020. [14] A. Milioto, P. Lottes, and C. Stachniss, “Real-time semantic segmen-

tation of crop and weed for precision agriculture robots leveraging background knowledge in CNNs,” in Proc. IEEE Int. Conf. Robotics and Automation (ICRA), pp. 2229–2235, 2018. [15] F. Magistri et al., “From one field to another—Unsupervised domain

adaptation for semantic segmentation in agricultural robotics,” Comput. Electron. Agric., vol. 212, p. 108114, 2023. [16] M. Fawakherji et al., “Crop and weed classification using pixel-wise

segmentation on ground and aerial images,” Int. J. Robotic Comput., vol. 2, no. 1, pp. 39–57, 2020. [17] J. Fang, H. Lin, X. Chen, and K. Zeng, “A hybrid network of CNN

Proposed future work in this domain are twofold. First, the current training process is fully supervised training with dense, pixel-level annotations, making generalization to new crops or conditions laborious. These setup costs can be reduced by leveraging domain adaptation, few-shot learning, and/or self- supervised pre-training on unlabeled UAV data. Additional training with modality dropout and redundancy-aware fusion should further enhance reliability under sensor failures.

and transformer for lightweight image super-resolution,” in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. Workshops (CVPRW), 2022, pp. 1103–1112.

The second goal is to deploy the architecture to edge devices as part of a precision agriculture solution. Model prun- ing and hardware-aware Neural Architecture Search (NAS) should further reduce computational demands. Integrating the model into autonomous weed-control robots is also being investigated, combining segmentation with navigation and multi-sensor fusion like Light Detection and Ranging (Li- DAR). Ultimately, long-term field trials under diverse con- ditions—varying weather, soil types, or farm scales—will be critical to enabling scalable, site-specific weed control.


## REFERENCES

[1] S. Haug and J. Ostermann, “A crop/weed field image dataset for the

evaluation of computer vision based precision agriculture tasks,” in ECCV Workshops, Zurich, Switzerland, 2014, pp. 105–116. Springer, 2015. [2] I. Sa et al., “WeedMap: A large-scale semantic weed mapping framework

using aerial multispectral imaging and deep neural network for precision farming,” Remote Sensing, vol. 10, no. 9, p. 1423, 2018.

Accepted to the Novel Approaches for Precision Agriculture and Forestry with Autonomous Robots IEEE ICRA Workshop - 2025
