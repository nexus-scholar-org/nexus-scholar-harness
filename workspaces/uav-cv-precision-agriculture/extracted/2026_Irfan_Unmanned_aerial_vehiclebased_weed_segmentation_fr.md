---
workspace_id: SCI-000346
doi: 10.1016/j.eswa.2026.132842
title: Unmanned aerial vehicle-based weed segmentation from multispectral imagery
  in an edge computing environment
authors:
- family_name: Irfan
  given_name: Muhammad
  orcid: https://orcid.org/0009-0000-6013-7496
- family_name: Kim
  given_name: Jung Soo
  orcid: https://orcid.org/0000-0003-2929-9942
- family_name: Jeong
  given_name: Seong In
  orcid: null
- family_name: Akram
  given_name: Rehan
  orcid: https://orcid.org/0000-0003-3089-7210
- family_name: Gondal
  given_name: Hafiz Ali Hamza
  orcid: null
- family_name: Tariq
  given_name: Muhammad Hamza
  orcid: https://orcid.org/0009-0006-6939-1507
- family_name: Park
  given_name: Kang Ryoung
  orcid: https://orcid.org/0000-0002-1214-9510
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:21:24.824723+00:00'
---

# Unmanned aerial vehicle-based weed segmentation from multispectral imagery in an edge computing environment

Expert Systems With Applications 326 (2026) 132842

Contents lists available at ScienceDirect

Expert Systems With Applications

journal homepage: www.elsevier.com/locate/eswa

Unmanned aerial vehicle-based weed segmentation from multispectral  imagery in an edge computing environment

Muhammad Irfan , Jung Soo Kim , Seong In Jeong , Rehan Akram ,   Hafiz Ali Hamza Gondal , Muhammad Hamza Tariq , Kang Ryoung Park *

Division of Electronics and Electrical Engineering, Dongguk University, 30 Pildong-ro 1-gil, Jung-gu, Seoul 04620, Republic of Korea

A R T I C L E I N F O

A B S T R A C T

Keywords: Semantic segmentation of crop and weed Unmanned aerial vehicles Feature fusion Progressive receptive-field context-aware  network

Unmanned aerial vehicles (UAVs) equipped with computer vision techniques offer a practical and scalable so­ lution for large-scale weed mapping in agricultural fields. Accurate pixel-level discrimination of soil, crops, and  weeds from UAV imagery remains challenging due to severe class imbalance and the high visual similarity be­ tween crop and weed structures. Many existing segmentation approaches are either computationally demanding  or depend on ensemble strategies, which restrict their applicability on edge or real-time platforms. To address  these limitations, this study introduces a progressive receptive-field context-aware network (PRC-Net) designed  for efficient deployment under constrained computational resources. The proposed progressive receptive-field  fusion (PRF) module incrementally enlarges the receptive field across multiple scales, enabling improved  identification of small crop and weed regions within predominantly soil backgrounds. A channel synergy-focused  attention (CSA) mechanism is incorporated to selectively enhance informative spectral bands and their inter-  channel relationships in multispectral data, thereby improving class separability. Furthermore, a lightweight  context-aware feature extraction (LCFE) module establishes a compact encoder–decoder bottleneck that facili­ tates effective contextual refinement while reducing parameter redundancy and overfitting risk. Collectively,  these components retain discriminative features of minority classes and enhance spectral segmentation quality  with minimal computational overhead. PRC-Net is validated on the publicly available WeedMap (RedEdge-M,  Sequoia) and Sesame Aerial datasets, achieving mean intersection over union (MIOU) values of 0.8397, 0.6520,  and 0.6961, respectively. Experimental performance highlights that PRC-Net achieves superior performance and  efficiency compared to existing methods, confirming its suitability for UAV-based weed detection in precision  farming.


## 1. Introduction

which have been demonstrated to exert detrimental impacts on soil, the  environment, and human health (Fishkis et al., 2024). Mechanical  methods of weed control include tilling, mowing, hand weeding, and  mulching. These methods involve physical intervention and may be  effective for small-scale agricultural land use. However, the costs and  equipment required render these methods inefficient and impractical for  large farms. Furthermore, conventional mechanical methods produce  100%–150% more greenhouse gases than conventional broadcast  spraying of herbicides (Fishkis et al., 2024).

Agriculture sustains the majority of the human food supply while  confronting mounting pressure due to the swift growth of the global  population (Li et al., 2024). Agricultural yield is susceptible to numerous  human-made and natural disasters, including climate change. The  reduction in farmland and the presence of pests, diseases, and weeds  pose major challenges in achieving optimal yields. The most significant  of these issues is the generation of weeds, which reduces the availability  of resources for crop plants, ultimately affecting the overall yield.  Consequently, weed management is a pivotal concern for agricultural  land, necessitating the allocation of resources and labor. The specific  resources and labor required are determined by the methods employed  for weed control. Conventional techniques involve the use of herbicides,

Considering the shortcomings associated with conventional chemical  and mechanical weed control methods, there is a clear need to develop  solutions that are both resource-efficient and cost-effective. Advanced  agricultural practices are characterized by the integration of precision  agriculture techniques and leverage autonomous, AI-driven decision-

* Corresponding author. E-mail address: parkgr@dongguk.edu (K.R. Park).

https://doi.org/10.1016/j.eswa.2026.132842 Received 14 January 2026; Received in revised form 28 April 2026; Accepted 9 May 2026

Available online 10 May 2026  0957-4174/© 2026 The Author(s). Published by Elsevier Ltd. This is an open access article under the CC BY license ( http://creativecommons.org/licenses/by/4.0/ ).

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

making systems to optimize resource use and operational efficiency  (Haloui et al., 2024). Computer vision is at the vanguard of this AI-  powered revolution, with extensive ongoing research offering solu­ tions to the issues encountered by the agricultural sector. The rise of  high-speed internet and advanced edge devices has accelerated the  adoption of UAVs in agriculture. This is based on their versatility, cost-  effective management, capacity to cover vast areas quickly, and their  swarm configuration (Danilchenko and Segal, 2021), resulting in ap­ plications of UAVs for soil monitoring (Luo and Pu, 2024), stress  detection (Wang et al., 2022), disease detection (Chin et al., 2023), yield  estimation (Duan et al., 2021), and weed detection (Sa et al., 2018).

reliability (Machidon et al., 2025). Therefore, the practical realization of  onboard weed segmentation requires an effective balance between  segmentation accuracy and computational efficiency under changing  field conditions (Menshchikov et al., 2021).

To address the aforementioned challenges, we present a progressive  receptive-field context-aware network (PRC-Net). Our experimental  code with trained model weights is publicly accessible on GitHub (Irfan,  2025) for a fair comparison. The key contributions of the study are:

- Owing to the limitations of conventional convolutional neural

network (CNN) encoders, which cannot retain information pertain­ ing to minority classes such as weeds, a three-layered progressive  receptive-field fusion (PRF) module is introduced. This module  progressively expands the receptive field of the convolution opera­ tions of various sizes, enabling the acquisition of neighboring pixel  differences and local features through the feature fusion from earlier  layers. This ensures smooth enlargement of the receptive field of  convolution operations and preservation of minority class  information. - To enable the optimal utilization of multi-spectral imagery, we

The accurate performance of computer-vision-aided weed detection  in multispectral UAV imagery is hindered by several significant chal­ lenges. First, the background class (soil) is substantially more prevalent  than the crop and weed classes. This results in severe class imbalance. In  addition, UAV-based MSI often captures crop and weed instances that  occupy only a few pixels, while soil dominates large portions of the  scene (Sa et al., 2018). Second, multispectral imagery (MSI) in­ corporates additional bands such as near-infrared (NIR) and red-edge to  enhance vegetation discrimination. However, crops and weed plants still  exhibit strong spectral, structural, and textural similarities. These simi­ larities are intensified by inter-channel redundancy and the requirement  for radiometric calibration and precise orthomosaic alignment (Sa et al.,  2018). Variations in illumination, soil moisture conditions, and over­ lapping vegetation structures further increase the difficulty of discrim­ ination (Imran Moazzam et al., 2022). This requires that the models be  able to handle the issue of class imbalance and distinguish between  classes of crops and weeds that are highly similar.

propose a second-order statistics-based channel synergy-focused  attention (CSA) module that captures spatial information within  each channel, while simultaneously accounting for variations across  channels through channel covariances. These spatial and inter-  channel features are fused to enable the model to discern the sig­ nificance of individual channels and their interdependencies,  thereby optimizing the use of spectral feature cues. - To maximize the transfer of information from the encoder to the

decoder while avoiding any risk of compromising the generalization  ability and model complexity, a lightweight context-aware feature  extraction (LCFE) bottleneck module is proposed as a solution that  utilizes a parallel branch architecture. One branch captures contex­ tual features, effectively enlarging the receptive field with minimal  computational complexity to model multiscale contextual cues vital  for the majority (soil) and minority class objects (crops and weeds).  The second branch facilitates progressive feature reuse and efficient  multi-level representation refinement while substantially reducing  computational overhead. This provides a lightweight yet effective  pathway that prevents overfitting and makes it suitable for high-  precision segmentation tasks in resource-constrained applications. - The crop and weed pixels exhibited high texture and structural

Recent research efforts have sought to overcome these challenges by  developing classification and detection methods. Pixel-wise detection,  also known as semantic segmentation, is a more desirable approach than  classification or bounding box detection because it provides exact object  boundaries without covering any unwanted regions, allowing for precise  and efficient weed control (Janneh et al., 2023). The ability of UAVs to  facilitate extensive coverage in an efficient and effective manner in  terms of resources has led to their use in semantic-segmentation-based  weed detection. However, previous studies on UAV-based weed seg­ mentation have employed one of two approaches. The first is focused on  the application of general-purpose segmentation models (Ramirez et al.,  2020). In contrast, the second entails the development of deep learning  models that prioritize overall segmentation performance without  focusing on class-wise performance, as in (Castellano et al., 2023a).  Consequently, it is imperative to prioritize class-wise segmentation  performance to prevent false positives for the weed class, which can  encompass the crop class owing to the presence of textual similarities.

similarity; therefore, PRC-Net was trained using categorical focal loss  and Dice loss functions in a weighted combination. Categorical focal  loss was employed to enhance class-wise pixel classification, down­ weighing the loss contribution of well-classified pixels and empha­ sizing misclassified pixels. Additionally, Dice loss prioritizes  maximization of the overlap between the model’s output mask and  ground-truth mask, which results in enhanced overall segmentation,  especially in capturing precise boundaries. By combining these losses  with empirically determined weights, the model achieves optimal  performance by balancing accurate pixel-wise classification with  refined segmentation. Moreover, PRC-Net demonstrated notable  computational efficiency on the Jetson TX2, thereby substantiating  its suitability for edge-device-based weed control applications.

From an application perspective, onboard weed segmentation can  extend the role of UAV-based multispectral monitoring beyond passive  image acquisition to active in-field decision support. By enabling weed  distributions to be interpreted during flight, such systems can support  site-specific weed management and more timely precision spraying  operations (Deng et al., 2020). This is particularly important in dynamic  agricultural environments where delays between image capture and  treatment can reduce the practical value of UAV observations  (Machidon et al., 2025). In this context, onboard processing can improve  the operational relevance of UAVs for rapid intervention, localized  herbicide application, and future coordination with autonomous treat­ ment platforms (Menshchikov et al., 2021). However, these application  prospects remain constrained by several practical challenges. Onboard  deployment must operate under strict limitations in computation,  memory, energy consumption, and inference speed. UAV-mounted  embedded devices cannot easily execute large segmentation networks  in real time (Deng et al., 2020). At the same time, weed segmentation  requires fine-grained pixel-level discrimination of small and visually  similar targets. This increases the difficulty of maintaining reliable  segmentation performance under onboard resource constraints. Conse­ quently, excessive network simplification may reduce segmentation

The paper proceeds as follows: Section 2 presents a review of existing  crops and weed detection methodologies. Section 3 introduces the  proposed methodology and offers an in-depth description of the archi­ tecture and modules of the PRC-Net. Section 4 presents the experimental  dataset and results, including a detailed ablation study to assess the  performance contribution of the proposed modules. Section 5 provides a  detailed analysis of the feature-extraction capabilities of the proposed  model at different stages and a statistical analysis of the superior per­ formance of PRC-Net. Finally, Section 6 concludes the paper, highlights  its main contributions, and potential avenues for future research.

2

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

Fig. 1. Overall conceptual diagram of UAV-based solution for smart weed mapping.


## 2. Related work

spectral channels as the input for the model and established that the  segmentation performance was enhanced when multispectral channels  were used for model training compared to RGB channels. Building upon  this dataset, another study (Ramirez et al., 2020) assessed the perfor­ mance of prominently used segmentation models, such as UNet  (Ronneberger et al., 2015), SegNet (Badrinarayanan et al., 2017), and  DeepLabv3 (Chen et al., 2017), on the RedEdge-M dataset of WeedMap.  Although DeepLabv3 benefited from multi-scale contextual modeling,  evaluation was limited to a single sensor configuration, thereby  restricting conclusions regarding cross-sensor generalization. Moreover,  Castellano et al. (Castellano et al., 2023a) introduced three models  based on the Lawin-transformer (Yan et al., 2022) for the detection of  crops and weeds through semantic segmentation using the WeedMap  dataset. The proposed models were developed in two variants: one uti­ lizing the MiT-B0 (Xie et al., 2021) encoder and the other employing the  MiT-B1 (Xie et al., 2021) encoder. The experiment demonstrated that  the developed model exhibited superior performance compared with  SegNet and DeepLabv3. However, no single model demonstrated  consistently strong performance across both the RedEdge-M and Sequoia  datasets. Achieving satisfactory segmentation accuracy therefore  required separate model configurations for each dataset, which limits  practical deployment in resource-constrained edge computing environ­ ments. These findings underscore persistent domain sensitivity and  insufficient cross-sensor generalization in existing approaches.

The emergence of deep-learning-driven computer vision techniques  has sparked a transformative revolution in the agricultural sector. These  methods have greatly enhanced the ability to gather data, monitor  conditions, analyze information, and make informed decisions in pre­ cision agriculture, thereby addressing a multitude of challenges faced by  farmers. These methods include soil monitoring (Azadnia et al., 2022),  stress detection (Butte et al., 2021), disease detection (Ritharson et al.,  2024), pest detection (Zhu et al., 2024), yield estimation (Osman et al.,  2021), and weed detection (Hu et al., 2022). The implementation of  precision agriculture practices enabled by these techniques has led to  optimized resource efficiency and enhanced productivity.

2.1. Advantages of UAV-based weed detection

Although conventional ground-based computer vision techniques for  weed detection are typically reliable, they are constrained by their  limited scalability and reduced coverage area per image. This renders  them ineffective in monitoring extensive agricultural fields. Frequent  platform repositioning and the narrow field-of-view of proximal imaging  restrict operational range and delay decision making (Imran Moazzam  et al., 2022). In contrast, the use of UAVs enables the coverage of  extensive areas of agricultural land, facilitating the rapid collection of  data and timely decision-making processes. UAVs are also better suited  for gathering data from locations that are difficult to access. They can  also revisit these locations more quickly, with higher spatial resolution  (Saiz-Rubio and Rovira-M´as, 2020), without disrupting the soil and  plants. Furthermore, UAV imaging can achieve centimeter-level spatial  resolution and operation below cloud cover, which supports timely and  high-quality monitoring for precision interventions (Shahi et al., 2023).  These advantages, coupled with their ability to operate autonomously  and with minimal human intervention, have led to the increased  deployment of UAVs for smart weed control in precision agriculture  (Castellano et al., 2023b).

Beyond WeedMap, Shahi et al. conducted a comparative analysis on  the UAV imagery of cotton field, evaluating SegNet, U-Net, and Deep­ LabV3+ with multiple backbones (Shahi et al., 2023). Their results  showed that U-Net with EfficientNetB0 achieved superior overall per­ formance. Another study (Seiche et al., 2024) investigated U-Net with  ResNet50 for early-season weed segmentation using both high-end and  low-cost multispectral sensors. While low-cost systems demonstrated  practical feasibility for spot spraying, radiometric inconsistencies and  calibration challenges were reported, affecting segmentation robust­ ness. Similarly, study (Silva et al., 2024) implemented a U-Net model  with a ResNet50 backbone for UAV-based weed segmentation in soy­ bean and bean fields using RGB imagery. However, mask generation for  U-Net training was partially automated through color-based processing,  which may introduce labeling bias and reduce boundary precision in  complex scenes. The research work (Moazzam et al., 2021) introduced a  UAV-based patch-wise weed detection framework for sesame crops  using a newly collected NIR, G, and B (NGB) multispectral dataset.  Vegetation was extracted via a lightweight U-Net, and 31 × 31 patches  were classified using model ensembling. Despite high reported accuracy,  the method produces coarse and block-level outputs unsuitable for  precise boundary delineation. Collectively, these studies demonstrate  steady improvements in segmentation accuracy, yet persistent chal­ lenges remain in boundary precision, domain robustness, and compu­ tational efficiency.

2.2. UAV-based semantic segmentation of crops and weeds

Accurate site-specific weed management requires pixel-level  boundary delineation between crops and weeds rather than coarse ob­ ject localization (Janneh et al., 2023). Accordingly, prior research has  primarily concentrated on the evaluation of established semantic seg­ mentation architectures and the development of advanced models to  enhance boundary precision and class-level discrimination in UAV  imagery.

To address this requirement, research work in (Sa et al., 2018) pro­ duced a multispectral imagery dataset, designated WeedMap, captured  using a UAV in sugar beet fields in Germany and Switzerland. In addi­ tion, the authors assessed the performance of SegNet utilizing varying

Despite notable progress in UAV-based crop–weed semantic

3

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

Fig. 2. Detailed architecture of the PRC-Net segmentation model.

segmentation, critical challenges remain unresolved. Field imagery  often presents severe class imbalance due to dominant soil regions.  Crops and weeds exhibit high structural and textural similarity, espe­ cially during early growth stages. This similarity complicates fine-  grained discrimination. Many existing studies evaluate performance  on a single dataset or crop type. Such evaluation provides limited evi­ dence of cross-domain robustness. To address these issues, this study  proposes PRC-Net, a segmentation framework designed to enhance  minority-class representation under severe soil-dominant imbalance and  to improve discriminative capability in scenarios where crops and weeds  exhibit high structural and textural similarity. The proposed method  further emphasizes robustness validation across multiple datasets rep­ resenting different crop types, thereby ensuring generalization under  diverse agronomic conditions while maintaining computational effi­ ciency suitable for practical UAV deployment in edge computing  environment.

are provided in Tables A1 and A2, respectively.

The encoder comprises four stages, each integrating a PRF module  for multi-scale feature extraction, a CSA module for channel synergy  acquisition, and a rectified linear unit (ReLU). The PRF module expands  the receptive field from smaller to larger with feature fusion from each  previous convolution. This smooth receptive field expansion ensures  that the local and global feature activations in the input tensor are  adequately processed and preserved, which is essential for minority  classes, such as crops and weeds. This is followed by the CSA module,  which generates channel attention to highlight discriminative features  by capturing inter- and intra-channel dependencies. This dual mecha­ nism enables PRC-Net to achieve a superior balance between feature  enrichment and refinement, thus tackling the issues caused by class  imbalance and subtle distinctions in crop and weed patterns.

The bottleneck of the proposed method employs the LCFE module, a  parallel-branch mechanism that processes the feature map to capture  broader contextual and fine-grained features without increasing  computational complexity. Subsequently, it fuses the output from each  branch before passing the result to the decoder. To preserve essential  spatial details, skip connections are employed to link each encoder stage  with its corresponding decoder stage, ensuring that fine-grained infor­ mation is retained during upsampling. Except for the final stage, each  encoder stage utilizes max pooling to reduce the spatial resolution by  half, thereby efficiently compressing information for downstream pro­ cessing while maintaining computational efficiency. This combination  of progressive feature fusion, selective attention mechanisms, and  multiscale feature extraction ensures that PRC-Net delivers highly ac­ curate and resource-efficient segmentation, rendering it well-suited for  precision agriculture applications.


## 3. Materials and methods

3.1. Overall workflow of the proposed approach

Fig. 1 illustrates conceptual framework of the proposed UAV-based  edge computing methodology. A high-resolution multispectral camera  is mounted on a UAV to capture multispectral imagery of agricultural  fields. The camera captures high-resolution images of the crop field,  which are partitioned into smaller and more manageable patches that  serve as input for our PRC-Net. This patching step serves two purposes: it  reduces the memory demands for processing and ensures input patch  size is compatible with the model, thereby enhancing the segmentation  efficiency. The segmentation model then processes these tiles to produce  the corresponding pixel-wise segmentation masks, effectively differen­ tiating between soil, crop, and weed classes. These segmented masks are  subsequently aggregated to construct a segmentation map for the high-  resolution input image. In practical deployment scenarios, the generated  segmentation maps can be directly integrated into site-specific weed  management systems. The spatial distribution of weed pixels can be  converted into georeferenced prescription maps to enable variable-rate  herbicide spraying, targeted spot treatment, or mechanical weed  removal. By estimating weed density at patch or grid level, the system  can support decision-making for selective intervention, thereby  reducing chemical usage and operational cost.

PRC-Net uses CNN-based decoder architecture to decode processed  features. The first decoder stage accepts the output from the LCFE  module and processes it through two convolution layers, followed by  ReLU activation layers. The output is then upsampled using a transposed  convolutional layer. Unlike bilinear upsampling, this approach learns to  upsample by capturing the spatial patterns through training. This  approach facilitates a more precise upsampling process than conven­ tional interpolation methods, thereby progressively restoring the spatial  resolution in a learnable manner. The output is then concatenated with  the skip connection from the encoder and fed to the subsequent decoder  stage. Finally, at the end of the last decoder stage, the output crop and  weed semantic segmentation mask is generated using softmax  activation.

The mathematical formulation of the PRC-Net workflow is presented  in Eqs. (1)–(5). Each function represents a specific operation in the  encoder, bottleneck, and decoder layers.

3.2. Architectural overview of PRC-Net

The proposed PRC-Net model utilizes an encoder-decoder framework  utilizing skip connections to facilitate an uninterrupted knowledge  transfer between encoder and decoder stages, as illustrated in Fig. 2.  This design leverages a meticulously crafted combination of PRF mod­ ules and CSA attention mechanisms, providing a highly efficient and  robust solution for detecting weeds. Detailed specifications of different  model stages, including the input and output feature map dimensions,

) )))

(

(

(

(

⎧ ⎪ ⎪ ⎨

, i = 1

DownSample

ReLU

CSA

PRF

Iinput

(

(

(

(

) )))

DownSample

ReLU

CSA

PRF

fen stage(i−1)

, i = 2, 3

fen stagei =

(

(

(

) ))

⎪ ⎪ ⎩

i = 4

ReLU

CSA

PRF

fen stage(i−1)

(1)

4

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

Fig. 3. Structural layout of PRF module (on left) and CSA module (on right). Ki denotes the convolutional kernels at the ith encoder stage, where Ki ∈{24, 48, 128, 256}.

degrees of texture and color similarities in the visible bands. However,  multispectral non-visible bands with a red-edge (RE) wavelength of 717  nm and near-infrared (NIR) wavelength of 840 nm on the electromag­ netic spectrum provide additional information about plants because of  their different reflectance properties (Sa et al., 2018). However, these  spectral cues can be attenuated during hierarchical feature abstraction if  not carefully preserved. Therefore, progressive receptive-field expan­ sion with intermediate feature fusion is essential to retain both spatial  detail and discriminative spectral responses across encoder stages.

)

(

(2)

fbottleneck = LCFE

fen stage4

fde stage1 = Conv2DB(fbottleneck) (3)

{

(

)

Conv2DB

Concat(fde stage(j−1), fen stagei)

, j = 2, 3, 4, i = 3, 2, 1 TransposedConv(Conv2DB(...) )

fde stagej =

(4)

) )

(

(

Conventional multiscale modules such as pyramid pooling (Zhao  et al., 2017) or atrous spatial pyramid pooling (ASPP) (Chen et al., 2018)  aggregate features in parallel and merge them at a single stage. This  design increases receptive field diversity but often mixes fine and coarse  features abruptly. Such aggregation can dilute weak minority-class sig­ nals. This effect is more severe in multispectral UAV imagery, where  crop and weed regions are small and easily suppressed. In contrast, the  PRF module expands the receptive field progressively. It integrates  features stage by stage rather than in parallel. This gradual fusion pre­ serves fine spectral and spatial details. It also stabilizes minority-class  representations during encoding. As a result, PRF maintains discrimi­ native spectral cues more effectively than conventional parallel multi­ scale frameworks. The PRF module employs a three-layered design, with  each layer progressively expanding the receptive field, while meticu­ lously integrating local and global cues across both channel and spatial  domains. The initial layer of the PRF module employs pointwise  convolution to enhance channel-wise distinctions and integrates spec­ tral information across channels to capture inter-channel variations. By  performing fine-grained channel fusion, the model can leverage subtle  differences in the spectral properties that may otherwise go unnoticed in  spatial convolution alone. This step ensures that the foundational  feature map is informed by detailed spectral distinctions, thereby  enabling the model to better discern crops from weeds before consid­ ering spatial features. The input feature is merged with the output of the  point-wise convolution and forwarded to the second layer of the PRF  module.

(5)

fseg mask = Softmax

Conv2D

fde stage4

where Iinput is the input image to be segmented, fen stagei(i = 1) is the  output of the PRF module passed through the CSA module, and ReLU  activation applied on the Iinput image and finally halved using the max  pooling layer. fen stagei(i = 2, 3) is the output of the subsequent stages of  the encoder, and fen stagei(i = 4) is the feature map input to the LCFE  bottleneck module. fen stage(i)(i = 1, 2, 3) also serves as the skip connec­ tions for the corresponding decoder stages. fbottleneck denotes the output of  the LCFE bottleneck module. fde stage1 is the output of the first stage of the  decoder part in PRC-Net; here, Conv2DB is comprised of two convolution  layers using ReLU as an activation function and finally upsampled using  the  transposed  convolution  layer.  Similarly,  the  output  fde stagej(j = 2, 3, 4) is obtained, except that the input for each is a feature  map obtained via channel-wise concatenation of the skip connection  from the encoder, that is, fen stagei(i = 1, 2, 3) and the last decoder stage.  Finally, fseg mask is the output segmentation mask obtained using a  convolution layer with a Softmax function to generate per-class  probabilities.

The encoder part of the proposed PRC-Net comprises an encoder-  building PRF module, a CSA module, downsampling layers, and a  dual-branch LCFE bottleneck module. The specifications of each module  are outlined in the following subsections.

3.2.1. PRF module The PRF module represents a pivotal element of PRC-Net and is  primarily conceptualized to address the inherent constraints of con­ ventional encoders in retaining minority class information, such as that  of crops and weeds, throughout the encoding process. Conventional  architectures frequently encounter difficulties when confronted with  segmentation tasks characterized by imbalanced datasets. In such sce­ narios, the successive application of convolutions and pooling opera­ tions may substantially degrade the representational quality of the  minority classes. This is particularly important in the scenario of crop  and weed segmentation, where crops and weeds often exhibit high

The second layer comprises a 3 × 3 convolutional kernel that en­ larges the receptive field, thereby facilitating the capture of nuanced  spatial relationships among neighboring pixels. The 3 × 3 convolution  enables the PRF module to capture small-scale structural differences,  thereby enriching the feature map with the local texture characteristics  of each class. By focusing on interactions at the neighborhood level, the  second layer creates a refined spatial context that emphasizes bound­ aries and minor transitions between crops and weeds. This spatially  localized processing enhances the capability of the model to differen­ tiate these classes, supporting the precise delineation of plant structures

5

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

and providing a detailed map of the features that the final layer syn­ thesizes into a global context. Analogous to the first layer, the output of  the second layer is channel-wise concatenated with the input and  transmitted to the third layer to reinforce the spatial features from the  preceding layer.

interactions between bands.

The CSA module introduces a more nuanced approach that captures  both intra- and inter-channel relationships. This enables PRC-Net to  prioritize channel synergies and enhance the overall performance of  crop-weed region segmentation in multispectral imagery. The CSA  module specifically employs global average pooling (GAP) and global  max pooling (GMP) to extract mean intensity and peak activation values  across each channel, thereby facilitating the collection of insights into  dominant spectral features and general trends across the spatial domain.  Furthermore, the module extends beyond the scope of conventional  single-channel analysis by incorporating channel covariances to eluci­ date inter-channel relationships. This cross-channel covariance matrix  facilitates the identification of dependencies across spectral bands,  which is pivotal in multispectral imagery where adjacent channels may  capture subtle yet distinctive variations in reflectance that can differ­ entiate crops from weeds. A combination of pooling and covariance  analyses establishes a dual focus mechanism within the CSA module.  The model is capable of not only learning the relative importance of  individual channels but also understanding how information from  different spectral bands interacts.

The final layer employs a 5 × 5 convolutional kernel to achieve a  broader receptive field, thereby synthesizing a global context that is  essential for all classes (soil, crops, and weeds). A higher receptive field  enables the model to recognize broad structural patterns and relative  spatial placements that are necessary for accurately capturing context  and enhancing continuity in feature representations. This layer ensures  that even minority-class features, such as crops and weeds, are  embedded within a spatial reference frame, thereby reducing the risk of  misclassification caused by dominant soil regions. The resulting feature  map and the input are concatenated in the channel domain, and then  passed to the final layer, which applies a pointwise convolution to  consolidate the concatenated feature maps into a unified representation.  In addition, this pointwise convolution modifies the output channel  dimensions of the PRF module, serving as a mechanism to reduce  dimensionality, hence reducing the computational overhead while  preserving essential information. The PRF module is shown in Fig. 3, and  Table A3 provides a comprehensive overview of the layer specifications  for the PRF module at the initial stage of the encoder.

Fig. 3 shows an architectural representation of the CSA module. For  an input fin with shape (H, W, C), where H and W are the feature map  height and width, respectively, and C represents channels, the complete  process of the CSA module is defined by Eqs. (13)–(23): For each channel  c, a mean µc is computed in the spatial dimension and the feature map is  centered:

The detailed feature map transformation process of the PRF module  is presented in Eqs. (6)–(12).

flayer1 = ReLU(Conv2D1×1(fin) ) (6)

∑ H

∑ W

μc = 1 H × W

)

(

fin(i, j, c) (13)

fc1 = Concat

(7)

flayer1, fin

i=1

j=1

(

))

(

fin(i, j, c) = fin(i, j, c) −μc (14)

flayer2 = ReLU

fc1

(8)

Conv2D3×3

here, fin is the mean-centered feature map. The covariance matrix for  each pair of channels c and d is calculated as

)

(

(9)

fc2 = Concat

flayer2, fc1

(

))

(

∑ H

∑ W

cd = 1 H × W

∑

flayer3 = ReLU

fc2

(10)

Conv2D5×5

fin(i, j, c) ⋅fin(i, j, d) (15)

i=1

j=1

)

(

fc3 = Concat

(11)

flayer3, fc2

where fin(i, j, c) and fin(i, j, d) are the centered feature maps for channels c  and d, respectively. Covariance computed for each pair of channels of fin  results in a covariance matrix map f∑of dimensions (C, C).

(

)

fout= ReLU(Conv2D1×1

fc3

(12)

⎤

∑

11 ∑

12 ∑

∑

⎡

where fin represents the input to the PRF block; for the first stage of the  encoder, Iinput is the input image. flayer1, flayer2, and flayer3 are the outputs of  each of the three layers of the PRF block, and fc1, fc2, and fc3 represent the  channel concatenations for the input and output feature maps flayer1,  flayer2 and flayer3, respectively. Finally, fout is the final feature map of the  PRF block obtained by applying a point-wise convolution to fc3.

13 ⋯

⎥⎥⎥⎥⎥⎥⎥⎥⎥⎦

1C ∑

21 ∑

22 ∑

∑

⎢⎢⎢⎢⎢⎢⎢⎣

23 ⋯

2C ∑

31 ∑

32 ∑

∑

f∑=

(16)

33 ⋯

3C ⋮ ⋮ ⋮ ⋱ ⋮ ∑

∑

∑

∑

C3 ⋯

C1

C2

CC

3.2.2. CSA module The CSA module was designed to enhance feature representation in  multispectral imagery. Its effectiveness in crop–weed segmentation  stems from the strong inter-channel variability present in multispectral  data. Different spectral bands capture distinct reflectance responses of  vegetation, which provide valuable spectral cues for discrimination.  However, these bands are often correlated and exhibit inter-channel  redundancy. Subtle reflectance differences across adjacent bands may  distinguish crops from weeds, particularly in high-resolution UAV im­ agery. Conventional attention mechanisms such as SE and CBAM (Woo  et al., 2018) primarily rely on first-order statistics. SE employs global  average pooling to generate channel weights. CBAM combines average  and max pooling but still processes channels independently. These ap­ proaches summarize channels separately and do not explicitly model  cross-channel dependencies. In multispectral imagery, this limitation  may restrict the ability to capture spectral synergies that arise from

The (C, C) feature map is transformed into a one-dimensional (1D)  feature map to be added to the outputs of GAP and GMP using a 1D  convolution layer, followed by GAP in 1D. This transformation consol­ idates covariance information and adjusts the dimensions of the feature  tensor.

f∑

1D = GAP1D(Conv1D(f∑)) (17)

The input feature map undergoes GAP and GMP layers to extract the  mean and peak activations from each channel axis as follows:

fglob avg. = GAP(fin) (18)

fglob max. = GMP(fin) (19)

The rest of the attention formulation is as follows:

6

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

Fig. 4. Structural layout of the LCFE bottleneck module.

illustrated in Fig. 4, with detailed layer specifications provided in  Table A4.

fsqueeze = f∑

1D + fglob avg. + fglob max. (20)

) )

(

(

The first branch is the channel and context-aware branch (CCB),  which focuses on extracting multiscale contextual features, and the  second branch is the lightweight smooth feature-refinement branch  (LSFB), which focuses on extracting smooth fine-grained features. The  CCB is structured around parallel atrous convolutions (Yu and Koltun,  2016), each with a distinct dilation rate that captures the multiscale  contextual representation. This approach effectively enlarges the  receptive field without a corresponding increase in the parameter count,  thereby enabling the model to capture essential spatial variations in the  soil, crop, and weed regions. The results of these atrous convolutional  operations are merged along the channel axis and subsequently trans­ mitted through the CSA module. The CSA module is essential for  enhancing the feature map by assigning higher weights to more infor­ mative channels, thereby enhancing the feature representation. This  branch’s expanded receptive field and channel-aware attention mech­ anism provide rich multiscale contextual information that is vital for  distinguishing between majority and minority class pixels within com­ plex agricultural imagery. The LSFB employs depthwise separable  convolution (Chollet, 2017) in a densely connected setup, a design that  captures fine-grained features while maintaining computational effi­ ciency (Huang et al., 2017). It incorporates depthwise separable con­ volutions within a localized dense connectivity scheme to enhance  gradient propagation and fine-grained feature preservation, rather than  forming a full DenseNet-style architecture. Depthwise separable con­ volutions perform spatial filtering for each channel independently,  thereby maintaining computational efficiency while capturing spatial  details. When integrated with dense connections, this setup enhances  the pathway for gradient flow and minimizes the loss of critical features  by allowing the model to capture subtle distinctions in various feature  hierarchies, which are particularly valuable for distinguishing visually  similar plant species. Additionally, this dense configuration employs a  Gaussian error linear unit (GeLU) activation operation (Hendrycks and  Gimpel, 2023), characterized by smoothly adjusting the weight of the  inputs according to their value, allowing small negative values to  contribute rather than being completely discarded, as in the case of the  ReLU activation function. This refined approach minimizes the likeli­ hood of dead neurons, which is a common issue with ReLU, and serves as  a form of regularization. The combination of CCB and LSFB provides the  LCFE with the capacity to act as a lightweight yet highly effective  bottleneck, capable of capturing multiscale spatial dependencies,  emphasizing interchannel relations, and preserving fine-grained details.  This makes it an appropriate solution for UAV-based crop and weed  segmentation tasks, in which both precision and computational effi­ ciency are critical, thus supporting high-resolution crop and weed

(21)

fexcit = ReLU

Conv1D

fsqueeze

fatt = Sigmoid(Conv1D(fexcit) ) (22)

finp atten = fin ⨂fatt (23)

where fglob avg. and fglob max. show the feature maps obtained after  applying GAP and GMP, respectively. fsqueeze refers to the output of the  squeeze part of the CSA module, fexcit is the feature map of the excitation  part of the CSA, and fatt is the final attention map. finp atten denotes the  attention-applied input feature map with dimensions (H, W, C). ⨂  represents the element-wise multiplication.

Conventional channel attention mechanisms primarily rely on global  pooling followed by lightweight projection layers. Their dominant  computational complexity scales approximately as O(HW • C), with an  additional lower-order channel projection term. The CSA module ex­ tends this formulation by introducing a covariance computation with  dominant cost scaling as O(HW • C2). Although this introduces a  quadratic dependency on the channel dimension, it is important to  contextualize this cost within the overall network. A standard convo­ lution layer with kernel size K × K, input channels Cin, and output  channels Cout has time complexity O(HW • Cin • Cout • K2). For the  common case of a 3 × 3 convolution with comparable input and output  channel dimensions, this scales as O(HW • C2 • K2). Therefore, the  computational order of CSA is comparable to that of a conventional 3 × 3 convolutional layer. Since CSA is applied at progressively reduced  spatial resolutions within the encoder, its runtime overhead remains  moderate relative to the dominant convolutional operations. In terms of  memory, the intermediate covariance matrix requires O(C2) storage. For  C = 256, which is the maximum channel dimension in PRC-Net, the  memory required per batch item for inference is ~0.26 MB (256 × 256  × 4 bytes, for float32). This overhead is negligible compared to the  overall model footprint and remains suitable for deployment in light­ weight edge computing environments.

3.2.3. LCFE bottleneck module The LCFE bottleneck was developed with the specific objective of  enabling efficient information transfer from the encoder to the decoder  during the delineation of the crop and weed regions. Furthermore,  controlling model complexity is essential for mitigating overfitting and  improving generalization capability. To this end the LCFE incorporates a  parallel branch architecture that maximizes feature extraction while  minimizing computational demands. The structural configuration is

7

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

Fig. 5. Example images of the WeedMap and Sesame Aerial datasets with corresponding ground-truth masks. (a) RedEdge-M dataset, (b) Sequoia dataset, and (c)  Sesame Aerial dataset where the image is NGB (NIR, G, B), and that is why the vegetation appears orange. Black, green, and yellow colors in the ground-truth mask  represent background, crop, and weed pixels, respectively.

monitoring within the constraints of resource-limited aerial platforms.

Therefore, to handle the significant imbalance between the foreground  (crop plants and weed plants) and background (soil), categorical focal  loss (CFL) is used, as proposed in (Lin et al., 2018) and presented in Eq.  (30).

The overall feature transformation in LCFE module is formulated in  Eqs. (24)–(29).

(

)

fi = AtrousConv2Di

fen stage4

(i = 1, 2, 3) (24)

∑ C

∑ B×H×W

α(1 −̂ yic)γyiclog(̂yic) (30)

LossCFL = −

))))

(

(

(

(

fCCB = ReLU

(25)

CSA

Conv2D

Concat

f1, f2, f3

c=1

i=0

)

(

yic is the one-hot encoded true reference, and ̂yic is the model-predicted  probability for ith pixel and class c. α ∈[0, 1] denotes the weighting  factor, γ ≥0 is the focusing parameter, and the whole term α

(26)

fmax = MaxPooling2D

fen stage4


## 1 −̂ yic

)γ is 
the modulation factor, which reduces weights for easily classified sam­
ples, thus focusing on the hard-to-classify samples pertaining to the 
minority class. In this study, the focusing factor γ is set to 2.0, and the 
weighting factor α to 0.25 as suggested by the study (Lin et al., 2018). To 
alleviate the influence of class-related disparities and improve the seg­
mentation performance, the Dice loss is integrated as an auxiliary loss. 
Dice loss is particularly effective in addressing foreground-background 
imbalances by emphasizing the intersection of the model-predicted 
and actual segments, making it suitable for accurate minority class 
segmentation. Dice loss shifts the model’s attention from the back­
ground to the foreground minority class (Milletari et al., 2016), an 
essential need to improve the performance of crop and weed segmen­
tation task. Eq. (31) presents the Dice loss:

(

fdep dense = DepthwiseSep DenseBlock(fmax) (27)

)

(

fLSFB = TransposedConv

(28)

fdeps dense

)

(

fLCFE = Concat

(29)

fCCB, fLSFB

where f1, f2 and f3 are the outputs of the convolution operations with  dilation rates of 1, 2, and 3, respectively. fCCB denotes the final output of  the first branch (CCB) obtained after applying pointwise convolution,  followed by the CSA module and ReLU activation on the concatenated  feature map of the dilated convolution layers. fmax represents the halved  feature map to be used for the second branch of the LCFE bottleneck  module, and fdep dense denotes the output feature map of the depth-wise  separable convolution layers applied in a dense manner with the GeLU  activation function. fLSFB represents the final output of the second branch  obtained by upscaling the fdep dense using transpose convolution, and fLCFE  is the final output of the LCFE bottleneck module.

( ∑B×H×W

)

i=0 (yiĉyic)

Lossdice = 1 −2

∑C

(31) ̂

∑B×H×W

C

i=0 (yic+̂yic)

c=1

yi and yi denote the model prediction and actual label for the ith pixel  and class c, respectively. B, H, and W represent the batch size, height,  and width of the image, respectively. C indicates the class count for the  detection task. This hybrid loss function ensures robust segmentation of  soil, crop, and weed classes, particularly addressing the challenges  posed by extreme class imbalances. By combining these loss functions,  PRC-Net strikes an effective balance between pixel-wise accuracy and  minority class representation, thereby achieving superior segmentation  performance. The final semantic segmentation loss function used to  train PRC-Net is formulated in Eq. (32). The optimal value for parameter  λ was empirically determined as 0.7 on the training data, based on the

3.2.4. Loss functions Categorical cross-entropy (CCE) loss is widely utilized for semantic  segmentation problems. CCE is equivalent to a negative log-likelihood  loss aimed at maximizing the probability of pixel being assigned to the  correct class label by minimizing the log of that probability. Although  CCE loss minimizes the pixel-wise error, it is inherently biased toward  the majority class because of its reliance on equal weighting for all  pixels. This bias can degrade the segmentation quality of minority class  objects (Yeung et al., 2022) such as crops and weeds, which are often  overshadowed by the background class (soil) in UAV imagery.

8

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

heterogeneous vegetation density across patches. These variations  introduce significant challenges in discriminating visually similar crop  and weed classes under dynamic field conditions, making the dataset  both complex and representative of practical deployment scenarios. The  images were captured using Agrocam NDVI with Phantom 3 UAV. The  dataset comprised three bands: G, B, and NIR, providing NGB composite  images. In our experiment, we used the raw spectral bands directly,  without applying any further preprocessing to generate additional  channels. The collected images were divided into non-overlapping  patched images. The train split contains 1,200 images, and the test  split consists of 720 images. The same default splits were used for  training and evaluation purposes in our experiments. During training, a  10% training split was used as the validation set. Example images with  the corresponding ground-truth masks are shown in Fig. 5.


> **Table 1**

> Hyperparameters for training PRC-Net.

Database Initial  learning  rate

Minimum  learning rate

β1 β2 Batch  size

Epochs

10-3 10-6 0.9 0.999 6 150

RedEdge-

M

Sequoia 12 Sesame

10

Aerial

highest achieved segmentation accuracy.

Loss = λ(LossCFL) + (1 −λ)(Lossdice) (32)

The experimentation was performed on a desktop workstation  running Ubuntu 20.04 and equipped with an Intel® Core™ i7-3770 K @  3.50 GHz (4 cores) central processing unit (CPU), 32 GB of RAM, and an  NVIDIA GeForce GTX 1070 graphics processing unit (GPU) with 8 GB of  virtual RAM (VRAM). The experiments were performed using Python  3.10.12 and PyTorch 2.6.0.


## 4. Experimental setup and result analysis

4.1. Datasets and experimental setup

The experimentation was conducted using publicly available UAV-  captured imagery datasets, WeedMap (Sa et al., 2018) and Sesame  Aerial dataset (Imran Moazzam et al., 2022). The WeedMap dataset  comprises two sub-datasets. It was captured during two campaigns in  the sugar beet fields of Eschikon, Switzerland, and Rheinbach, Germany.  Multispectral sensors Sequoia, mounted on a DJI Mavic drone, and  RedEdge-M, mounted on a DJI Inspire 2 drone, were used in the first and  second campaigns, respectively.

4.2. Training of PRC-Net

The original datasets comprise patches with a resolution of 480 × 360 pixels, which were resized to 320 × 320 pixels. Data augmentation,  including horizontal and vertical flips, was applied in all experiments to  enlarge the effective training set. The PRC-Net model was trained using  carefully chosen hyperparameters that were optimized for segmentation  performance. The adaptive moment estimation (Adam) (Kingma and Ba,  2017) optimizer was employed for stable training convergence. The  hyperparameter settings used for the training of PRC-Net are provided in  Table 1.

In the first campaign, the Sequoia dataset was collected using four  spectral bands: red (R), green (G), red edge (RE), and near-infrared  (NIR). In the second campaign, the RedEdge-M dataset included an  additional blue (B) band along with R, G, RE, and NIR. The data were  divided into smaller patches and grouped by the dataset providers into  two datasets, consisting of subsets 000, 001, 002 (for training), and 003  (for testing) for RedEdge-M, and 005 (for testing), 006, and 007 (for  training) for the Sequoia dataset. The Sesame dataset covers substantial  real-world variability, including changes in illumination (early morning,  sunny, cloudy, and near-sunset conditions), diverse soil states (dry, wet,  and semi-wet after rainfall), and varying crop growth stages ranging  from 16 to 45 days. It also captures high weed pressure, overlapping  crop–weed regions, crop shadows at different orientations, and

The model training process was monitored using a validation-set loss  metric to identify the optimal version of the model. Early stopping was  applied to mitigate overfitting, and training was halted if the model  began to capture noise or irrelevant features. Additionally, early stop­ ping halts model training in the absence of further improvement and  when the model reaches a performance plateau. This configuration  enabled the model to prioritize segmentation and lower computational  overhead. As presented in Fig. 6, the loss and IOU curves for the training

Fig. 6. Curves of training and validation loss and IOU for PRC-Net.

9

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842


> **Table 2**

> Ablation studies of the contribution of each of the proposed modules.

Cases PRF CSA LCFE Loss Bg IOU Crop IOU Weed IOU MIOU Precision Recall F1

1 ​​​​0.9582 0.785 0.594 0.7791 0.828 0.756 0.7904 2 ​​​✓ 0.968 0.8025 0.62 0.7968 0.821 0.77 0.7947 3 ​​✓ ​0.9692 0.807 0.625 0.8004 0.843 0.78 0.8103 4 ​✓ ​​0.9725 0.812 0.63 0.8048 0.851 0.782 0.8150 5 ✓ ​​​0.9738 0.82 0.638 0.8106 0.873 0.796 0.8327 6 ✓ ​​✓ 0.9778 0.8235 0.641 0.8141 0.875 0.797 0.8342 7 ✓ ​✓ ​0.9791 0.8202 0.6365 0.8119 0.87 0.795 0.8308 8 ✓ ✓ ​​0.9788 0.8238 0.643 0.8152 0.878 0.797 0.8355 9 ✓ ​✓ ✓ 0.9795 0.8289 0.674 0.8275 0.903 0.821 0.8600 10 ✓ ✓ ​✓ 0.982 0.831 0.681 0.8313 0.91 0.841 0.8741 11 ✓ ✓ ✓ ​0.9831 0.8315 0.6845 0.8330 0.911 0.843 0.8757 12 (Proposed) ✓ ✓ ✓ ✓ 0.9845 0.8321 0.7025 0.8397 0.9239 0.8603 0.8910


> **Table 3**

> Ablation studies for the placement of the PRF module.

Number of PRF Placement in Encoder Bg IOU Crop IOU Weed IOU MIOU Precision Recall F1

0 − 0.9655 0.7998 0.6302 0.7985 0.846 0.819 0.8323 1 4 0.9758 0.8162 0.6514 0.8145 0.8875 0.857 0.8720 2 3,4 0.9779 0.821 0.654 0.8176 0.889 0.858 0.8732 3 2,3,4 0.9804 0.8248 0.659 0.8214 0.893 0.859 0.8757 4 (proposed) 1,2,3,4 0.9845 0.8321 0.7025 0.8397 0.9239 0.8603 0.8910

of the proposed PRC-Net exhibit a gradual and uniform reduction during  training process. This outcome highlights that the proposed model  benefits from the training samples, learns sufficiently using the training  data, and effectively learns the underlying features essential for the task  at hand. Furthermore, the convergence of the validation loss curve  confirms that PRC-Net avoids overfitting and demonstrates strong  generalization to unseen data. This behavior validates the efficacy of the  training framework and model design in achieving reliable feature  extraction and segmentation accuracy.

4.3.2. Evaluation on the RedEdge-M dataset

4.3.2.1. Ablation studies. In this subsection, detailed ablation studies  are presented to assess the effectiveness of each proposed module and  the overall efficiency of PRC-Net. Table 2 reports the initial ablation  studies, evaluating the individual and combined contributions of the  proposed modules to the segmentation performance. Case 1 served as  the baseline, comprising an encoder-decoder UNet with simple con­ volutional layers and a CFL. Cases 2–5 demonstrate the impact of indi­ vidual modules, each leading to noticeable improvements in  segmentation accuracy. Specifically, in Case 2, the utilization of the  proposed weighted loss function for base model training resulted in a  1.77% improvement in the MIOU. In Case 3, the inclusion of the LCFE  bottleneck significantly enhanced the feature extraction and trans­ formation between the encoder and decoder, yielding improved seg­ mentation results and affirming the effectiveness of the bottleneck over  the baseline. Similarly, the addition of the CSA module to the encoder  (Case 4) resulted in a 2.57% improvement in the MIOU over the base­ line, highlighting the benefits of leveraging inter-channel and intra-  channel feature embeddings for segmentation accuracy. In Case 5, the  introduction of the PRF module within the encoder delivered a  remarkable 3.15% improvement in the MIOU over the baseline,  demonstrating its ability to generate robust feature representations for  both minority classes. Cases 6–11 explore combinations of the proposed  modules while maintaining the PRF module as a constant component  because the PRF module shows the highest accuracy enhancement over  the baseline, as shown in Cases 2–5. Among these, configurations  involving three-module combinations outperformed those involving  two-module combinations, further validating the synergy among the  modules. Case 12 achieved the highest performance for all three classes,  as reflected by the evaluation metrics. These results underscore the ef­ ficacy of the proposed method in meeting the primary objectives of this  study. Consequently, Case 12 was identified as the optimal configuration  with the highest accuracy, and represented the proposed methodology  for this study.

4.3. Evaluation of PRC-Net

4.3.1. Performance assessment metrics To evaluate PRC-Net and facilitate a comparative analysis using  state-of-the-art (SOTA) segmentation methods, we report, intersection  of union (IOU) for each class, mean intersection over union (MIOU),  Precision, Recall, and harmonic mean of precision and recall (F1 Score),  mathematically defined in Eqs. (33)–(36).

IOUc = |Pc ∩Gc|

|Pc ∪Gc| (33)

∑ K

MIOU = 1

IOUc (34)

K

c

Recall = TP TP + FN (34)

Precision = TP TP + FP (35)

F1 Score = 2 × Precision × Recall

Precision + Recall (36)

here, Pc denotes the set of pixels predicted as belonging to class c, Gc  represents the corresponding ground-truth pixels, and K is the total  number of semantic classes in the segmentation task. TP, FN, and FP  denote the numbers of pixels classified as true positives, false negatives,  and false positives, respectively.


> **Table 3 lists the ablation studies for the number of PRF modules**

> utilized in the encoder component of PRC-Net, along with their 
respective placements. The absence of a PRF module resulted in the 
lowest segmentation performance. The introduction of the PRF module 
in Stage 4 in Case 2 results in a performance boost, which confirms its 
ability to robustly extract and preserve minority class information that is

10

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842


> **Table 4**

> Ablation studies according to the variations of the PRF module.

Cases PRF Variation Bg IOU Crop IOU Weed IOU MIOU Precision Recall F1

1 No Concatenation 0.9723 0.8065 0.624 0.8009 0.8582 0.84 0.8490 2 3 × 3 kernels 0.9765 0.8172 0.6451 0.8129 0.8714 0.8475 0.8593 3 5 × 5 kernels 0.9732 0.811 0.6357 0.8066 0.8625 0.8382 0.8502 4 (proposed) Concatenation with progressive kernels 0.9845 0.8321 0.7025 0.8397 0.9239 0.8603 0.8910


> **Table 5**

> Ablation studies for the placement of the CSA module.

Number of CSA Placement in Encoder Bg IOU Crop IOU Weed IOU MIOU Precision Recall F1

0 − 0.9795 0.8289 0.674 0.8275 0.903 0.821 0.8600 1 4 0.9745 0.818 0.6502 0.8142 0.8853 0.8567 0.8708 2 3,4 0.9782 0.8235 0.653 0.8182 0.8857 0.8571 0.8712 3 2,3,4 0.9811 0.8268 0.6601 0.8227 0.8934 0.8600 0.8764 4 (proposed) 1,2,3,4 0.9845 0.8321 0.7025 0.8397 0.9239 0.8603 0.8910


> **Table 6**

> Ablation studies according to the variations of the CSA module.

Cases CSA Variation Bg IOU Crop IOU Weed IOU MIOU Precision Recall F1

1 SE(GAP) 0.9712 0.8117 0.6403 0.8077 0.8754 0.844 0.8594 2 SE (GAP, GMP) 0.9730 0.8160 0.6485 0.8125 0.8812 0.8510 0.8658 3 SE (GAP. GMP, GCP) 0.9794 0.8303 0.6980 0.8359 0.9211 0.8614 0.8903 4 (proposed) CSA 0.9845 0.8321 0.7025 0.8397 0.9239 0.8603 0.8910


> **Table 7**

> Ablation studies according to variations of the LCFE module.

Cases LCFE Variation Bg IOU Crop IOU Weed IOU MIOU Precision Recall F1

1 No LCFE 0.982 0.831 0.681 0.8313 0.91 0.841 0.8741 2 CCB + CNN 0.9886 0.8305 0.6895 0.8362 0.9091 0.8408 0.8736 3 Skip + LSFB 0.981 0.8264 0.687 0.8315 0.9108 0.8536 0.8813 4 (proposed) CCB + LSFB 0.9845 0.8321 0.7025 0.8397 0.9239 0.8603 0.8910


> **Table 8**

> Ablation studies according to the loss function weight used.

Cases Loss Function Weights λ of Eq (32) Bg IOU Crop IOU Weed IOU MIOU Precision Recall F1

1 Dice Loss(λ = 0) 0.9631 0.7854 0.611 0.7865 0.8428 0.792 0.8166 2 Focal Loss(λ = 1) 0.9831 0.8315 0.6845 0.8330 0.911 0.843 0.8757 3 0.5 0.98 0.825 0.685 0.8300 0.918 0.855 0.8854 4 0.4 0.9701 0.821 0.685 0.8254 0.9198 0.8508 0.8840 5 0.3 0.981 0.8265 0.6901 0.8325 0.922 0.8551 0.8873 6 0.6 0.9839 0.8262 0.689 0.8330 0.92 0.8591 0.8885 7 (proposed) 0.7 0.9845 0.8321 0.7025 0.8397 0.9239 0.8603 0.8910 8 0.8 0.9744 0.8013 0.6254 0.8004 0.8714 0.8254 0.8478


> **Table 9**

> Comparisons of PRC-Net and SOTA models on the RedEdge-M database (Bg means background).


## Methods

Bg IOU
Crop IOU
Weed IOU
MIOU
Precision
Recall
F1

SegNet (Sa et al., 2018) 0.8124 0.5885 0.5023 0.6344 0.7423 0.6731 0.7060 UNet++ (Hu et al., 2022) 0.8427 0.6719 0.5165 0.6770 0.7813 0.7265 0.7529 UNet-EfficientNetB0 (Shahi et al., 2023) 0.8615 0.7132 0.5384 0.7044 0.8068 0.7496 0.7771 UNet-ResNet50 (Seiche et al., 2024) 0.8729 0.7428 0.5479 0.7212 0.8215 0.7683 0.7940 R2U-Net (Zhang et al., 2021) 0.8891 0.7762 0.5569 0.7407 0.846 0.7974 0.8210 TransUnet (Yu and Qin, 2023) 0.9038 0.7884 0.5734 0.7552 0.8517 0.8001 0.8251 Swin-Unet (Yu and Qin, 2023) 0.9212 0.8073 0.6198 0.7828 0.8662 0.8123 0.8384 SegFormer-B0 (Jiang et al., 2022) 0.9347 0.8234 0.6412 0.7998 0.8743 0.8205 0.8465 DeepLabv3 (Ramirez et al., 2020) 0.8744 0.7981 0.6921 0.7882 0.8611 0.813 0.8364 U-Mamba (Ma et al., 2024) 0.9456 0.7812 0.6489 0.7919 0.8775 0.8226 0.8492 Lawin-B1 (Castellano et al., 2023a) 0.951 0.7879 0.6537 0.7975 0.8799 0.8244 0.8512 SplitLawin-B1 (Castellano et al., 2023a) 0.9688 0.8016 0.6612 0.8105 0.8841 0.847 0.8652 UNet3+ (Huang et al., 2020) 0.9621 0.8030 0.6712 0.8121 0.8927 0.8411 0.8661 PRC-Net (Proposed) 0.9845 0.8321 0.7025 0.8397 0.9239 0.8603 0.8910

11

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

Fig. 7. Comparisons of PRC-Net and SOTA methods on the RedEdge-M database. The TPs for background, crop, and weed are marked as black, green, and yellow,  respectively. Purple is FP for weeds, where the model incorrectly classifies background pixels as weed. Red is FP for weeds, where the model incorrectly classifies  crop pixels as weed. Blue is FP for crop, where the model incorrectly classifies background pixels as crop. Orange is FP for crop, where the model incorrectly classifies  weed pixels as crop. White is FP for background, where the model incorrectly classifies background pixels as crop or weed. (a) Input image, (b) ground-truth mask,  segmentation images by (c) SegNet, (d) UNet++, (e) UNet-EfficientNetB0, (f) UNet-ResNet50, (g) R2Unet, (h) TransUnet (i) SwinUnet, (j) SegFormer-B0, (k)  DeepLabv3, (l) U-Mamba (m) Lawin-B1 (n) SplitLawin-B1 (o) UNet3+, and (p) PRC-Net.

lost in the deep stages of the encoders. Furthermore, the incorporation of  the PRF module in all four stages of the encoder led to optimal seg­ mentation performance, thus establishing the configuration proposed in  this study. This illustrates that the deployment of the PRF throughout  the encoder facilitates the capture of more intricate contextual details  and refined information, which is vital for effective crop and weed  segmentation. Moreover, the transfer of this information to the corre­ sponding decoder stages enables the reuse of features, ultimately leading

to enhanced segmentation performance.


> **Table 4 summarizes the ablation studies conducted to assess internal**

> variations within the PRF module. In Case 1, the output of each 
convolution layer was not merged with its input in the channel dimen­
sion, leading to the lowest performance observed across all configura­
tions. In Case 2, the computed feature map of each convolutional 
operation was merged in the channel dimension with its input, with each 
convolutional layer employing 3 × 3 kernels. This approach resulted in

12

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

extraction techniques that not only capture features effectively but  also preserve minority class information as the network progresses in  depth, which aligns with the central objective of this study. Notably,  optimal segmentation performance was achieved when CSA modules  were utilized across all four encoder stages of PRC-Net. This configu­ ration emphasizes the importance of the critical channels and enhances  the feature-extraction process within the encoder. Furthermore, the  channel-enhanced feature maps produced by the CSA modules signifi­ cantly improve the transfer of features to the corresponding decoder  stages, leading to superior crop and weed segmentation performance in  the generated masks.


> **Table 6 represents the ablation study that evaluated different vari­**

> ations of the CSA modules used in the encoder of PRC-Net. In Case 1, the 
squeeze-and-excitation (SE) module employed a GAP in the squeeze 
operation, with the excitation part comprising two fully connected 
layers. Serving as the baseline, this configuration yielded the lowest 
performance among all the cases. In Case 2, the squeeze operation is 
enhanced by incorporating GMP in parallel with GAP. The addition of 
GMP enabled the capture of the maximum activations from the feature 
map, thus improving the overall representation of feature significance. 
However, the most significant performance improvement is observed in 
Case 3, where global covariance pooling (GCP) is introduced alongside 
GAP and GMP. This addition allows the module to capture inter-channel 
relationships through covariance information, leading to more effective 
feature representation. Finally, Case 4 represents the proposed CSA 
module, which integrates a three-branch squeeze module (global 
average, maximum, and covariance pooling) and replaces the densely 
connected layers in the excitation module with two 1D convolutional 
layers. This modification further consolidates the information extracted 
during the squeeze phase, resulting in the highest segmentation per­
formance across all cases and classes.

Fig. 8. Confusion matrix of PRC-Net on RedEdge-M dataset.

improved segmentation performance, particularly for the crop and weed  classes. The concatenation mechanism effectively preserved information  related to minority classes that might otherwise have been suppressed  owing to repeated convolutions. In Case 3, all three layers of the PRF  module utilized 5 × 5 kernels for feature extraction, which led to a  decline in the segmentation performance of the minority classes, namely  crops and weeds. Finally, in Case 4, the proposed PRF configuration was  applied, incorporating the convolution operations with filter sizes of 1 × 1, 3 × 3, and 5 × 5 combined with the concatenation mechanism. As  demonstrated in Cases 1–3, the segmentation performance for the ma­ jority class (soil) remained relatively stable. However, the proposed  configuration in Case 4 significantly improves the segmentation out­ comes for the weed class, which has the least pixel representation. This  improvement highlights the capability of the PRF module to learn  discriminative feature representations from the early stages of the  encoder and maintain these features through deeper stages of  architecture.

The proposed LCFE module demonstrates exceptional efficacy in  improving segmentation performance, as is evident from the ablation  studies reported in Table 7. In the absence of the LCFE bottleneck (Case  1), the model exhibits suboptimal performance, particularly for the  weed class, underscoring the need for an effective bottleneck that can  facilitate robust feature extraction and efficient transformation between  the encoder and decoder. In Case 2, the CCB is coupled with a simple  CNN branch comprising two convolutional layers. This configuration  yielded slight improvements in the segmentation scores, particularly in  weed detection, by introducing a modest increase in feature richness.  Case 3 integrates a simple skip connection in parallel with the LSFB,  resulting in further enhancement. The notable performance gains  highlight the capability of the LSFB branch to provide an efficient  feature-extraction pathway, benefiting both the majority and minority  classes. The full integration of the LCFE module in Case 4, which fused  features from the CCB and LSFB branches, achieved the highest seg­ mentation performance. In encoder-decoder architectures, the bottle­ neck plays a critical role because it acts as a bridge, consolidating


> **Table 5 reports the ablation studies of examining the effect of**

> incorporating varying numbers of CSA modules into the encoder of PRC- 
Net. The results reveal that omitting the CSA modules entirely across the 
encoder stages yields the lowest segmentation performance for all 
classes. However, a performance restoration pattern resembling that 
observed in the PRF module experiments shown in Table 3 was evident. 
This pattern supports the hypothesis that critical information related to 
minority classes (crops and weeds) is increasingly prone to loss as the 
network grows deeper and the spatial resolution decreases. These find­
ings underscore the necessity of employing mechanisms and feature-


> **Table 10**

> Comparisons of the PRC-Net and SOTA models on the Sequoia database (Bg means background).


## Methods

Bg IOU
Crop IOU
Weed IOU
MIOU
Precision
Recall
F1

Deeplabv3 (Ramirez et al., 2020) 0.9002 0.2248 0.0312 0.3854 0.4942 0.3597 0.4164 R2U-Net (Zhang et al., 2021) 0.9284 0.5696 0.0915 0.5298 0.6301 0.5511 0.5880 UNet-EfficientNetB0 (Shahi et al., 2023) 0.9308 0.5854 0.0946 0.5369 0.6372 0.5578 0.5949 TransUnet (Yu and Qin, 2023) 0.9311 0.5496 0.0817 0.5208 0.6204 0.5546 0.5857 Swin-Unet (Yu and Qin, 2023) 0.9442 0.5599 0.101 0.5350 0.6323 0.5538 0.5905 UNet-ResNet50 (Seiche et al., 2024) 0.9498 0.5752 0.0978 0.5409 0.6365 0.5613 0.5965 SegNet (Sa et al., 2018) 0.958 0.5887 0.083 0.5432 0.6187 0.5532 0.5841 SegFormer-B0 (Jiang et al., 2022) 0.9615 0.6124 0.1087 0.5609 0.6468 0.5629 0.6019 UNet++ (Hu et al., 2022) 0.9425 0.6183 0.1023 0.5544 0.6408 0.548 0.5908 UNet3+ (Huang et al., 2020) 0.9603 0.7256 0.1059 0.5973 0.6634 0.5883 0.6236 SplitLawin-B1 (Castellano et al., 2023a) 0.9731 0.7276 0.1143 0.6050 0.7165 0.5983 0.6521 U-Mamba (Ma et al., 2024) 0.9748 0.7369 0.1281 0.6133 0.7244 0.6237 0.6703 Lawin-B1 (Castellano et al., 2023a) 0.9762 0.7465 0.1392 0.6206 0.735 0.6409 0.6847 PRC-Net (Proposed) 0.9804 0.7893 0.1863 0.6520 0.7454 0.6618 0.7011

13

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

Fig. 9. Comparisons of the PRC-Net and SOTA methods on the Sequoia database. The TPs for background, crop, and weed are marked as black, green, and yellow,  respectively. Purple is FP for weeds, where the model incorrectly classifies background pixels as weed. Red is FP for weeds, where the model incorrectly classifies  crop pixels as weed. Blue is FP for crop, where the model incorrectly classifies background pixels as crop. Orange is FP for crop, where the model incorrectly classifies  weed pixels as crop. White is FP for background, where the model incorrectly classifies background pixels as crop or weed. (a) Input image, (b) ground-truth mask,  segmentation images by (c) DeepLabv3, (d) R2Unet, (e) UNet-EfficientNetB0, (f) TransUnet, (g) SwinUnet, (h) UNet-ResNet50, (i) SegNet, (j) SegFormer-B0, (k)  UNet++, (l) UNet3+, (m) SplitLawin-B1, (n) U-Mamba, (o) Lawin-B1 and (p) PRC-Net.

information from the encoder and preparing it for reconstruction in the  decoder. An effective bottleneck is essential to ensure that salient fea­ tures are preserved, particularly for minority classes that are often  overshadowed during the feature compression process. The LCFE mod­ ule effectively fulfills this role by incorporating specialized parallel  pathways that balance feature diversity and retention. The substantial  improvement in weed class segmentation illustrates the ability of the  LCFE module to capture intricate inter-class distinctions and effectively  preserve minority class features.

optimizing PRC-Net was evaluated through ablation studies, as listed in  Table 8. These experiments assessed the impact of combining CFL and  Dice loss in varying proportions to attain an optimal balance between  class sensitivity and spatial accuracy, particularly for minority classes. In  Case 1, only Dice loss was utilized as the loss function, which resulted in  suboptimal segmentation performance, particularly for the weed class.  In Case 2, only CFL was employed, resulting in improved segmentation  results compared to Dice loss. Cases 3–6 explored different weighted  combinations of the CFL and Dice loss. In Case 3, equal weights of CFL  and Dice loss provided noticeable improvements, particularly for the

The effectiveness of different loss function configurations in

14

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

transformer-based SplitLawin-B1, which is specifically designed for crop  and weed segmentation (Castellano et al., 2023a). Although SplitLawin-  B1 leverages the MiT-B1 (Xie et al., 2021) backbone to effectively cap­ ture global contextual cues, it falls short in enriching features for mi­ nority classes. Similarly, UNet3+ employs full-scale feature fusion  across encoder and decoder stages. However, this dense fusion dispro­ portionately emphasizes dominant spatial patterns, exacerbating  misclassification in spectrally ambiguous regions. In contrast, the task-  specific architectural choices of PRC-Net enable it to overcome these  limitations by capturing and preserving minority-class information  through its spatial and spectral aware modules. PRC-Net achieves 2.91%  and 3.13% higher IoU for the crop and weed classes, respectively,  compared with the second-best performing model UNet3+. Further­ more, Fig. 7 demonstrates PRC-Net’s capability to detect weeds occur­ ring both in clusters and within intra-row crop spaces, including those in  close proximity to crop regions. This performance is attributed to the  model’s high precision, which results from its notably low false-positive  counts across all classes. Consequently, PRC-Net produces substantially  sharper and more coherent segmentation boundaries compared with  existing SOTA methods. Row-normalized confusion matrix of PRC-Net  on the RedEdge-M dataset is shown in Fig. 8. Rows correspond to  ground-truth classes (Soil, Crop, and Weed) and are normalized to sum  to one to illustrate class-wise prediction distribution. PRC-Net achieves  strong discrimination of the soil class (99.57% correct predictions),  while maintaining robust performance on crop (88.55%) and weed  (79.69%). The primary misclassification occurs between crop and weed,  indicating residual spectral and structural similarity between vegetation  classes in the RedEdge-M imagery.

Fig. 10. Comfusion matrix of PRC-Net on Sequoia dataset.

crop and weed classes. The proposed configuration in Case 7 achieved  the highest segmentation performance, with substantial gains observed  for the IOU of the weed class and overall F1 Score. This optimal com­ bination underscores the efficacy of emphasizing the strengths of the  CFL in mitigating class imbalance while leveraging Dice loss to improve  spatial consistency in segmentation masks. Finally, Case 8 demonstrated  a decline in performance compared to the proposed configuration,  reaffirming that an excessive reliance on CFL alone may compromise the  segmentation accuracy for minority classes. These results emphasize the  importance of effective loss function to ensure a balanced optimization  process that caters to both class-specific and spatial requirements,  thereby achieving robust segmentation performance across all classes.

4.3.3. Evaluation on the Sequoia dataset The results in Table 10 and the visual comparisons in Fig. 9 clearly  indicate that PRC-Net achieves superior performance over existing  SOTA models on the Sequoia dataset. This dataset is extremely chal­ lenging due to its very small proportion of weed pixels, which often  leads to minority-class suppression. DeepLabv3, although generally  effective in conventional segmentation tasks, ranks lowest on this  dataset because its atrous-convolution backbone emphasizes broad  contextual cues while failing to capture fine minority-class structures.  Compared with Lawin-B1, the second-best model, PRC-Net gains 4.2%  and 4.7% IOU improvements for the crop and weed classes, respectively.  Although Lawin-B1 attains a high background IOU, similar to  SplitLawin-B1, it struggles to maintain reliable discrimination of crop  and weed plants. This issue is evident in its higher false-positive count  for the background class. Its reliance on global attention causes small  and fine-scale crop structures to be absorbed into the background, as  seen in Fig. 9(o), where small crop plants are misclassified. In contrast,  Fig. 9(p) shows that PRC-Net retains boundary fidelity even for small  and sparsely distributed crop plants. These improvements stem from  PRC-Net’s recursive feature reuse in the encoder and its multi-scale

4.3.2.2. Comparison of PRC-Net and state-of-the-art methods. The pro­ posed PRC-Net model is compared with SOTA models to conduct  quantitative and qualitative analyses of the segmentation results. All  competing methods evaluated in this study were reproduced and  retrained on the same datasets using consistent input resolutions and  spectral band configurations to ensure fair comparison. The training  protocols described in the respective original publications were care­ fully followed and adapted to maintain consistency across models. This  ensures that performance differences arise from architectural charac­ teristics rather than discrepancies in experimental settings. Table 9 presents the quantitative metrics for the RedEdge-M dataset, while Fig. 7 provides a qualitative comparison between PRC-Net and competing  SOTA approaches. The proposed model outperforms well-established  architectures such as UNet3+, as well as the more advanced


> **Table 11**

> Comparisons of the PRC-Net and SOTA models on the Sesame Aerial database (Bg means background).


## Methods

Bg IOU
Crop IOU
Weed IOU
MIOU
Precision
Recall
F1

UNet-EfficientNetB0 (Shahi et al., 2023) 0.8396 0.6124 0.1983 0.5501 0.7068 0.5142 0.5953 TransUnet (Yu and Qin, 2023) 0.8451 0.6232 0.2135 0.5606 0.7144 0.5267 0.6064 R2U-Net (Zhang et al., 2021) 0.8479 0.6301 0.2467 0.5749 0.7205 0.5503 0.6240 UNet++ (Hu et al., 2022) 0.8667 0.6545 0.3102 0.6105 0.7428 0.5736 0.6473 UNet-ResNet50 (Seiche et al., 2024) 0.8649 0.6613 0.3147 0.6136 0.7435 0.5782 0.6505 Swin-Unet (Yu and Qin, 2023) 0.8628 0.6717 0.3188 0.6178 0.7455 0.5841 0.6550 SplitLawin-B1 (Castellano et al., 2023a) 0.8598 0.6789 0.3348 0.6245 0.7431 0.6001 0.6640 SegNet (Sa et al., 2018) 0.8631 0.6801 0.3521 0.6318 0.7512 0.5921 0.6622 SegFormer-B0 (Jiang et al., 2022) 0.8672 0.6814 0.3685 0.6390 0.7538 0.6034 0.6703 Lawin-B1 (Castellano et al., 2023a) 0.8689 0.6685 0.3963 0.6446 0.7582 0.5939 0.6661 UNet3+ (Huang et al., 2020) 0.8634 0.6821 0.4127 0.6527 0.7611 0.6023 0.6725 Deeplabv3 (Ramirez et al., 2020) 0.8665 0.6729 0.4836 0.6743 0.7629 0.6149 0.6810 U-Mamba (Ma et al., 2024) 0.8688 0.6941 0.4975 0.6868 0.7636 0.6335 0.6925 PRC-Net (Proposed) 0.8702 0.7036 0.5144 0.6961 0.7643 0.6598 0.7082

15

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

Fig. 11. Comparisons of the PRC-Net and SOTA methods on the Sesame Aerial database. The TPs for background, crop, and weed are marked as black, green, and  yellow, respectively. Purple is FP for weeds, where the model incorrectly classifies background pixels as weed. Red is FP for weeds, where the model incorrectly  classifies crop pixels as weed. Blue is FP for crop, where the model incorrectly classifies background pixels as crop. Orange is FP for crop, where the model incorrectly  classifies weed pixels as crop. White is FP for background, where the model incorrectly classifies background pixels as crop or weed. (a) Input image, (b) ground-truth  mask, segmentation images by (c) UNet-EfficientNetB0, (d) TransUnet, (e) R2Unet, (f) UNet++, (g) UNet-ResNet50, (h) SwinUnet, (i) SplitLawin-B1, (j) SegNet, (k)  SegFormer-B0 (l) Lawin-B1, (m) UNet3+, (n) DeepLabv3, (o) U-Mamba, and (p) PRC-Net.

feature extraction strategy, which together promote the consistent  preservation of minority-class information, an essential requirement for  this study. Its higher IOU scores for both crops and weeds, along with  improved F1 performance (0.7011 vs. 0.6847 for Lawin-B1), confirm  PRC-Net’s more reliable feature representation across varying plant  sizes and complex spatial arrangements. As illustrated in Fig. 10, PRC-  Net achieves near-perfect recognition of the soil class (99.78%), while  maintaining strong crop classification performance (87.60%). However,  substantial confusion is observed for the weed class, with 53.45% of  weed pixels misclassified as soil and 22.28% as crop, indicating signif­ icant spectral overlap and reduced separability in the Sequoia imagery.

visually illustrated in Fig. 11. Unlike the RedEdge-M and Sequoia  datasets, the Sesame Aerial dataset contains relatively larger crop and  weed plants, yet it remains highly challenging due to its limited spectral  bands (G, B, and NIR) and the variability introduced by environmental  conditions such as soil moisture and plant shadows. These factors  contribute to increased false positives, particularly around plant  boundaries, which complicate accurate segmentation. Across all evalu­ ated models, PRC-Net consistently demonstrates superior performance.  TransUnet struggles with the spectral and spatial complexities of the  dataset, lacking mechanisms to suppress texture-induced noise or  effectively capture discriminative channel relationships. Consequently,  it produces fragmented weed predictions, as depicted in Fig. 11(d).  Despite its poor performance on RedEdge-M and Sequoia, Deeplabv3  achieves third-best performance on this dataset. PRC-Net, however,  surpasses all competitors by effectively leveraging domain-aware design

4.3.4. Evaluation on the Sesame Aerial dataset The performance of the PRC-Net on the Sesame Aerial database, in  comparison with several SOTA methods, is summarized in Table 11 and

16

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

assessment for all the models. An evaluation on the Jetson TX2 was  conducted to assess the computational efficiency of PRC-Net in  embedded system environments, which are critical for edge-device  deployment of real-time crop and weed segmentation models. The Jet­ son TX2 (“Jetson TX2 Module,” 2025) is an embedded system featuring  an NVIDIA Pascal™-family GPU with 256 CUDA cores and a power  consumption of under 7.5 W. It is equipped with 8 GB of shared memory  accessible by both the GPU and CPU. Jetson TX2 has been employed in  prior studies to evaluate the feasibility of weed detection methods in  edge-device environments (Deng et al., 2020). The hardware configu­ ration of the desktop computer used for the experiment is detailed in  Subsection 4.1.

On the desktop system, PRC-Net requires 10.53 ms per image and  achieves 94.97 FPS, whereas on the Jetson TX2 it requires 58.65 ms and  achieves 17.05 FPS, which satisfies the real-time requirement for on­ board UAV deployment (Menshchikov et al., 2021). As summarized in  Table 12, the proposed model contains 13.30 M parameters, requires  0.58 GB of GPU memory, and incurs 41.46 GFLOPs. These values indi­ cate that PRC-Net maintains a compact computational profile while  preserving sufficient representational capacity for accurate crop and  weed segmentation. A broader comparison with the competing methods  shows that PRC-Net achieves a more favorable complexity and perfor­ mance balance than both heavy-weight and lightweight alternatives.  PRC-Net is substantially more efficient than SegNet, TransUnet,  UNet++, UNet3+, Lawin-B1, SplitLawin-B1, U-Mamba, UNet-  ResNet50, R2U-Net, Swin-Unet, and DeepLabv3, all of which require  noticeably higher latency, larger parameter budgets, or greater memory  consumption. Although some of these methods achieve competitive  segmentation accuracy, they do so at the cost of increased computa­ tional burden, which limits their practicality for embedded deployment.

Fig. 12. Confusion matrix of PRC-Net on Sesame Aerial dataset.

principles to capture both spatial and channel-wise discriminative fea­ tures. It achieves a crop IOU of 0.7036 and a weed IOU of 0.5144,  corresponding to improvements of 3.07% and 3.08%, respectively, over  Deeplabv3. The enhanced ability of the model to discriminate subtle  textural cues allows it to maintain robust segmentation even with  limited spectral information. While false positives are observed pri­ marily at plant edges due to wet and dry soil transitions and shadow  effects, PRC-Net maintains superior precision, recall, and F1 scores,  underscoring its robustness. As shown in Fig. 12, PRC-Net maintains  strong soil recognition (94.40%) and satisfactory weed detection  (67.34%) on the Sesame Aerial dataset. The primary confusion occurs  between crop and soil (21.03%) and weed and soil (30.78%), suggesting  increased spectral similarity and background interference under aerial  imaging conditions. Overall, both quantitative metrics and visual results  confirm that PRC-Net provides a reliable solution for weed segmentation  on the challenging Sesame Aerial dataset.

The comparison with lightweight models is particularly important.  SegFormer-B0 and UNet-EfficientNetB0 are both designed to reduce  complexity through efficient backbone construction. SegFormer-B0  employs a hierarchical transformer encoder with lightweight multi­ layer perceptron decoding, which reduces model size and FLOPs by  avoiding heavy decoder operations. Similarly, UNet-EfficientNetB0 uses  EfficientNet-B0 as an encoder backbone, relying on compound scaling  and depthwise separable convolutions to reduce computational cost.  These architectural choices explain their lower parameter counts,  memory demands, and FLOPs. However, the segmentation results in  Tables 9–11 with Figs. 7, 9, and 11 show that this lower computational  cost is accompanied by reduced segmentation accuracy. This trade-off is  also illustrated in Fig. 13(a) and (b), where MIOU values from Table 9 are plotted against inference time and parameter count represented by  bubble size. PRC-Net occupies the most favorable region in the MIOU vs  inference time plot, appearing near the upper-left corner on the plots of  both the desktop and Jetson TX2 embedded system. This position in­ dicates that the proposed model achieves the highest MIOU while

4.3.5. Computational complexity and inference time analysis In this subsection, we evaluate and compare the computational ef­ ficiency of PRC-Net with SOTA methods by presenting the number of  parameters (in millions), GPU memory requirement (in GB), floating-  point operations (FLOPs), inference time per sample, and frames per  second (FPS), as summarized in Table 12. The input resolution adopted  for computational analysis is identical to that used for experimental  training and evaluation (i.e., 320 × 320 pixels). This ensures consistency  between computational complexity analysis and practical performance


> **Table 12**

> Computational efficiency comparison of PRC-Net against state-of-the-art methods.


## Methods

Parameters (M)
GPU Memory (GB)
FLOPs 
(G)

Desktop System Jetson TX2

Latency (ms) FPS Latency (ms) FPS

SegNet (Sa et al., 2018) 29.81 1.12 60.90 17.65 56.65 113.92 8.78 UNet++ (Hu et al., 2022) 55.28 1.93 120.71 45.09 22.17 420.04 2.38 R2U-Net (Zhang et al., 2021) 46.48 1.64 105.33 34.87 28.68 290.09 3.45 TransUnet (Yu and Qin, 2023) 105.12 3.43 250.85 85.22 11.73 801.94 1.25 Swin-Unet (Yu and Qin, 2023) 41.44 2.72 180.42 64.59 15.48 562.78 1.78 DeepLabv3 (Ramirez et al., 2020) 47.61 2.24 92.96 57.21 17.48 353.56 2.83 UNet3+ (Huang et al., 2020) 26.08 1.31 70.81 42.78 23.38 287.53 3.48 Lawin-B1 (Castellano et al., 2023a) 16.53 0.84 25.12 30.84 32.43 220.34 4.54 SplitLawin-B1(Castellano et al., 2023a) 20.52 1.18 29.32 44.86 22.29 318.83 3.14 UNet-ResNet50 (Seiche et al., 2024) 43.81 0.99 62.75 19.21 52.06 120.32 8.31 SegFormer-B0 (Jiang et al., 2022) 4.63 0.46 22.55 29.11 34.35 180.56 5.54 U-Mamba (Ma et al., 2024) 66.80 0.87 48.90 19.38 51.60 136.89 7.31 UNet-EfficientNetB0 (Shahi et al., 2023) 10.82 0.52 28.09 9.96 100.40 52.63 19.00 PRC-Net (Proposed) 13.30 0.58 41.46 10.53 94.97 58.65 17.05

17

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

Fig. 13. Comparison of proposed model and SOTA models with respect to MIOU (from Table 9), inference time, and parameter count. (a) Desktop system. (b) Jetson  TX2 embedded system.

retaining small inference latency, which remains practical for real-time  deployment. Although UNet-EfficientNetB0 achieve lower latency than  PRC-Net, it remains below PRC-Net in segmentation accuracy. This in­ dicates that their lightweight design improves efficiency but does not  provide the same level of fine-grained class discrimination required for  reliable crop and weed segmentation.

accuracy among all evaluated methods.


## 5. Discussion

5.1. Visual analysis with class activation map

This result suggests that the effectiveness of PRC-Net is not solely due  to reduced complexity. Rather, it arises from achieving a more suitable  balance between representational capacity and computational cost.  PRC-Net appears better aligned with the requirements of weed seg­ mentation environments where both local detail preservation and effi­ cient computation are essential. Therefore, the proposed model provides  a more favorable operating point than both heavier high capacity  models and lighter efficiency driven networks. As a result, it maintains  real-time onboard feasibility while delivering the highest segmentation

The performance of encoder-decoder-based architectures for se­ mantic segmentation relies on their capability to capture abstract fea­ tures in the early stages of the encoder, fine-grained features at later  stages, and effectively reconstruct the semantic segmentation map in the  final stage. To evaluate the capability of PRC-Net in achieving these  objectives and the proficiency of the proposed modules, we conducted  gradient-weighted  class  activation  mapping  (Grad-CAM)++ (Chattopadhay et al., 2018) analysis at various stages of the architec­ ture. Grad-CAM++ generates heat maps for all occurrences of each

18

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

Fig. 14. Grad-CAM visualization for PRC-Net at various stages. (a) Input image, (b) ground-truth mask, (c) predicted semantic segmentation mask. Black, green, and  yellow colors represent the TP pixels of background, crop, and weed, respectively. Grad-CAMs with respect to weed class (d), (e), and (f) at the first stage of the  encoder, middle stage (i.e., output of LCEF module), and last stage of the decoder, respectively. Grad-CAMs with respect to crop class (g), (h), and (i) at the first stage  of the encoder, middle stage (i.e., output of LCEF module), and of the decoder, respectively.

5.2. Analysis of edge cases


> **Table 13**

> Imbalance Ratio (IR) values for the experimental datasets (lower the better).

To characterize the degree of class imbalance across datasets, we  report the imbalance ratio (IR), defined as the ratio of majority-class  pixels to minority-class pixels. Understanding these IR values is essen­ tial for interpreting model behavior and for drawing fair comparisons  with SOTA methods. As shown in Table 13, both the training and test  splits of the Sequoia dataset exhibit extreme class imbalance, with IR  values of 405.54 and 380.19, respectively. Such a severe imbalance  directly impacts the learnability of the weed class. The minimal presence  of weed pixels in the training set limits the model’s ability to capture  discriminative spatial and textural cues necessary for robust general­ ization. Consequently, all evaluated models, including the proposed  method, demonstrate reduced segmentation performance for the weed  class on this dataset. This phenomenon underscores that the suboptimal  performance is driven not by architectural deficiencies, but by the  inherently low representation of the minority class in the data.

RedEdge-M Sequoia Sesame Aerial Train  split

Test  split

Train  split

Test  split

Train  split

Test  split

Imbalance

29.26 43.79 405.54 380.19 6.57 3.01

ratio (IR)

class, whether scattered or clustered, providing an intuitive under­ standing of model behavior (Chattopadhay et al., 2018). Given the  scattered nature of crops and weeds in UAV-captured images, Grad-  CAM++ offers a more reasonable visualization of the feature-extraction  process of the model. Fig. 14 illustrates Grad-CAM++ in three stages:  the first stage of the encoder, after the bottleneck module (middle stage),  and the last decoder stage. The input image, ground-truth mask, and  predicted semantic segmentation mask are provided as references. In the  first stage, Grad-CAM++ demonstrated that PRC-Net effectively  captured high-level feature representations from the input images.  Because both crop and weed plants share similar high-level features, the  attention of the model is directed similarly toward both plants. How­ ever, as the feature extraction progresses through the encoder-decoder  framework, the focus of the PRC-Net becomes more distinct for each  class.

The ability of PRC-Net to distinguish between crops and weed plants  under different scenarios is illustrated in Fig. 15. Weed plants appear in  various sizes and distributions across croplands. Fig. 15(a) demonstrates  the capability of PRC-Net to accurately identify weed pixels that occur in  scattered and spatially discontinuous clusters. In contrast, Fig. 15(b)  highlights PRC-Net’s effectiveness in segmenting densely clustered weed  regions with accurate boundary delineation. Together, these results

19

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

Fig. 15. Illustration of PRC-Net efficacy in the segmentation of minority classes in different scenarios. (a) Weed pixels appear in scattered formation. (b) Weed pixels  appear in dense formation (c) Crop rows with varying plant sizes. (d) Small weed plants in between crop rows. The TPs for background, crop, and weed are marked  black, green, and yellow, respectively. Purple is FP for weeds, where the model incorrectly classifies background pixels as weed. Red is FP for weeds, where the model  incorrectly classifies crop pixels as weed. Blue is FP for the crop, where the model incorrectly classifies background pixels as crop. Orange is FP for the crop, where the  model incorrectly classifies weed pixels as crop. White is FP for the background, where the model incorrectly classifies background pixels as crop or weed.

is more pronounced under extreme class imbalance and high crop–weed  similarity. Environmental factors such as illumination variation and  plant occlusion further increase segmentation uncertainty. Therefore,  while PRC-Net demonstrates robust performance across challenging  edge cases, careful integration with geospatial alignment and actuation  control  systems  remains  essential  for  reliable  field-level  implementation.

5.3. Statistical analysis

To statistically evaluate the segmentation performance difference  between the proposed PRC-Net and the second-best SOTA method,  UNet3+, based on the results in Table 9, we conducted a t-test. (Mishra  et al., 2019) and measured Cohen’s d-value (Cohen, 1992). The p-value  from the t-test represents the probability of obtaining an observed per­ formance difference between the two models under the null hypothesis.  A p-value below 0.05 is typically interpreted as evidence of a statistically  significant difference at the 95% confidence level. Whereas a p-value  below 0.01 indicates significance at the 99% confidence level. Unlike  the p-value, Cohen’s d quantifies the magnitude of the difference in  standard deviation units with common thresholds: 0.2 (small), 0.5  (medium), and 0.8 (large) effect sizes. As shown in Fig. 16, the p-value  for the F1 score on the RedEdge-M dataset is 0.025, indicating statistical  significance at the 95% confidence level. Similarly, Cohen’s d value was  3.37, indicating a large effect size and further validating the substantial  performance improvement of PRC-Net over the second-best method.

Fig. 16. T-test results comparing the F1 Scores of the proposed method and the  second-best method.

indicate that the model robustly distinguishes minority-class weed  pixels across varying spatial distributions and scales. Similarly, Fig. 15 (c) highlights the crop rows with sugar beet plants of varying sizes,  showcasing the capability of PRC-Net to accurately classify these  minority-class pixels despite size variations. Fig. 15(d) presents the most  challenging scenario, in which weed plants grow both between and  within crop rows. Although PRC-Net successfully detects most weed  regions, the detection boundaries require further refinement, particu­ larly in the squared regions, where red pixels indicate crop pixels mis­ classified as weeds and orange pixels indicate weed pixels misclassified  as crops. These misclassifications likely stem from the close proximity or  overlap between crops and weeds, which makes precise segmentation  more challenging.

5.4. Cross-domain robustness analysis

Domain shifts across UAV datasets arise from variations in spectral  dimensionality, sensor characteristics, illumination conditions, crop  types, and soil backgrounds. In this study, the three evaluated datasets  contain different numbers of spectral channels (5, 4, and 3), which  prevents direct cross-dataset training and testing due to architectural  input constraints. Nevertheless, the proposed PRC-Net is explicitly

From a practical deployment perspective, such boundary ambiguities  may influence downstream precision agriculture operations. In variable-  rate spraying systems, minor boundary errors can lead to localized over-  application or under-application of herbicide. The impact of these errors

20

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

designed to mitigate domain sensitivity at the feature-representation  level. The PRF module enhances multi-scale contextual aggregation,  allowing the network to capture spatial structures under varing spectral  configurations. The CSA module models inter-channel dependencies and  spatial correlations, which improves robustness under varying spectral  compositions. In addition, the class-balanced weighted loss reduces bias  toward dominant background pixels, thereby improving stability under  dataset-specific imbalance characteristics.

efficacy of PRC-Net for both desktop and edge device environments,  such as the Jetson TX2. PRC-Net can be used solely on the embedded  system, as evidenced by the inference analysis.

Although PRC-Net outperforms SOTA methods, there remains room  for improvement, particularly in cases where crop and weed plants are  in close proximity or overlap. Although the model accurately delineates  the detection boundaries for larger crops and weed plants in such sce­ narios, smaller weed plants pose a greater challenge because of their  intricate spatial arrangements. To tackle this limitation, further research  will examine the implementation of preprocessing methodologies to  enhance the distinction in reflectance between crops and weeds in  multispectral imagery. Furthermore, expanding the database to cover a  more extensive array of crops and weeds, along with environmental  factors, can enhance the generalizability of the model.

Importantly, the consistent performance gains of PRC-Net over SOTA  methods across all three datasets indicate that the proposed design  generalizes effectively under heterogeneous acquisition settings. This  suggests that lightweight architectures are not inherently limited in  cross-domain generalization, provided that discriminative multi-scale  and channel-adaptive mechanisms are properly integrated.


## 6. Conclusion

CRediT authorship contribution statement

This study proposes a methodology for enhancing crop and weed  segmentation using multispectral imagery captured via UAVs. The  proposed approach entailed the design and implementation of task-  specific modules to mitigate the challenges associated with imbal­ anced class distributions in soil, crops, weeds, and crop-weed similarity  pixels. The proposed PRC-Net is an encoder-decoder-based architecture  designed for the segmentation of multispectral crop and weed imagery.  The encoder component consists of four stages, each comprising a PRF  module and a CSA module. These modules extract feature representa­ tions for the subsequent encoder and corresponding decoder stages,  facilitating feature map reconstruction. The LCFE module connects the  encoder to the decoder through a parallel branch mechanism, thereby  providing a lightweight yet effective pathway for information flow. The  PRC-Net is trained using CFL and Dice loss with empirically determined  weights. The effectiveness of the proposed method has been validated by  extensive experimentation in ablation studies (subsection 4.3.2), as well  as through empirical and perceptual comparisons with SOTA methods.  Furthermore, a computational complexity analysis underscores the

Muhammad Irfan: Conceptualization, Methodology, Writing –  original draft. Jung Soo Kim: Validation. Seong In Jeong: Validation.  Rehan Akram: Data curation. Hafiz Ali Hamza Gondal: Software.  Muhammad Hamza Tariq: Software. Kang Ryoung Park: Supervision,  Writing – review & editing.

Declaration of competing interest

The authors declare that they have no known competing financial  interests or personal relationships that could have appeared to influence  the work reported in this paper.

Acknowledgments

This work was supported by the National Research Foundation of  Korea (NRF) grant funded by the Korea government (Ministry of Science  and ICT (MSIT)) (RS-2026-25470264).

Appendix A. Feature map transformations in the proposed network

..


> **Table A1**

> Detailed feature transformation description of the encoder stage of PRC-Net.

Layer Filter(Number of filters, size, and stride) Padding Dilation Rate Input Output

Input layer − − ‒ 320 × 320 × 5 320 × 320 × 5 1st PRF ⎡

⎤

⎡

⎤

‒ 320 × 320 × 5 320 × 320 × 24

24, 1 × 1, 1 24, 3 × 3, 1 24, 5 × 5, 1

− 1 × 1 2 × 2

⎣

⎦

⎣

⎦

1st CSA ⎡

⎤

⎡

⎤

‒ 320 × 320 × 24 320 × 320 × 24

24, 1 × 1, 1 3, 3 × 3, 1 24, 1 × 1, 1

− 1 × 1 −

⎣

⎦

⎣

⎦

Max pooling − − ‒ 320 × 320 × 24 160 × 160 × 24 2nd PRF ⎡

⎤

⎡

⎤

‒ 160 × 160 × 24 160 × 160 × 48

48, 1 × 1, 1 48, 3 × 3, 1 48, 5 × 5, 1

− 1 × 1 2 × 2

⎣

⎦

⎣

⎦

2nd CSA ⎡

⎤

⎡

⎤

‒ 160 × 160 × 48 160 × 160 × 48

48, 1 × 1, 1 6, 3 × 3, 1 48, 1 × 1, 1

− 1 × 1 −

⎣

⎦

⎣

⎦

Max pooling − − ‒ 160 × 160 × 48 80 × 80 × 48 3rd PRF ⎡

⎤

⎡

⎤

‒ 80 × 80 × 48 80 × 80 × 128

128, 1 × 1, 1 128, 3 × 3, 1 128, 5 × 5, 1

− 1 × 1 2 × 2

⎣

⎦

⎣

⎦

3rd CSA ⎡

⎤

⎡

⎤

‒ 80 × 80 × 128 80 × 80 × 128

128, 1 × 1, 1 16, 3 × 3, 1 128, 1 × 1, 1

− 1 × 1 −

⎣

⎦

⎣

⎦

Max pooling − − ‒ 80 × 80 × 128 40 × 40 × 128

(continued on next page)

21

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842


> **Table A1 (continued)**

Layer  Filter(Number of filters, size, and stride)  Padding  Dilation Rate  Input  Output

4th PRF ⎡

⎤

⎡

⎤

‒ 40 × 40 × 128 40 × 40 × 256

256, 1 × 1, 1 256, 3 × 3, 1 256, 5 × 5, 1

− 1 × 1 2 × 2

⎣

⎦

⎣

⎦

4th CSA ⎡

⎤

⎡

⎤

‒ 40 × 40 × 256 40 × 40 × 256

256, 1 × 1, 1 32, 3 × 3, 1 256, 1 × 1, 1

− 1 × 1 −

⎣

⎦

⎣

⎦

LCFE ⎡

⎤

⎡

⎤

⎡

⎤

40 × 40 × 256 40 × 40 × 32

32, 3 × 3, 1 32, 3 × 3, 1 32, 3 × 3, 1 32, 1 × 1, 1 32, 1 × 1, 1 4, 3 × 3, 1 32, 1 × 1, 1


## 1 × 1

1 × 1
1 × 1
−
−
1 × 1
−

1 2 3 −

⎢⎢⎢⎢⎢⎢⎢⎢⎣

⎥⎥⎥⎥⎥⎥⎥⎥⎦

⎢⎢⎢⎢⎢⎢⎢⎢⎣

⎥⎥⎥⎥⎥⎥⎥⎥⎦

⎢⎢⎣

⎥⎥⎦

⎡

⎤

⎡

⎤

‒ 40 × 40 × 3240 × 40 × 256 40 × 40 × 288

256, 3 × 3, 1 256, 1 × 1, 1 256, 3 × 3, 1 256, 1 × 1, 1 256, 3 × 3, 1 256, 1 × 1, 1


## 1 × 1

−
1 × 1
−
1 × 1
−

⎢⎢⎢⎢⎢⎢⎣

⎥⎥⎥⎥⎥⎥⎦

⎢⎢⎢⎢⎢⎢⎣

⎥⎥⎥⎥⎥⎥⎦


> **Table A2**

> Detailed feature transformation description of the decoder stage of PRC-Net.

Layer Filter  (Number of filters, size, and stride)

Padding Input Output

Conv. layers 2 × [256,3 × 3,1] [1 × 1] 40 × 40 × 288 40 × 40 × 256 Transposed conv − − 40 × 40 × 256 80 × 80 × 128 Concatenation (f skip, f prev.) − − 80 × 80 × 128 (f prev.)  80 × 80 × 128 (f skip) 80 × 80 × 256

Conv. layer 2 × [128,3 × 3,1] [1 × 1] 80 × 80 × 256 80 × 80 × 128 Transposed conv − − 80 × 80 × 128 160 × 160 × 48 Concatenation

− − 160 × 160 × 48 (f prev.)  160 × 160 × 48 (f skip) 160 × 160 × 96

(f 2, f prev.)

Conv. layer 2 × [48,3 × 3,1] [1 × 1] 160 × 160 × 96 160 × 160 × 48 Transposed conv − − 160 × 160 × 48 320 × 320 × 24 Concatenation

− − 320 × 320 × 24 (f prev.)  320 × 320 × 24 (f skip) 320 × 320 × 48

(f 1, f prev.)

Conv. layer 2 × [24,3 × 3,1] [1 × 1] 320 × 320 × 48 320 × 320 × 24 Conv. layer 3,1 × 1,1 − 320 × 320 × 48 320 × 320 × 3


> **Table A3**

> Detailed feature transformation description of PRF modules.

Layer Filter (Number of filters, size, and stride) Padding Input Output

Input layer − − 320 × 320 × 5 320 × 320 × 5 Conv layer (ReLU) 24,1 × 1,1 − 320 × 320 × 5 320 × 320 × 24 Concatenation

− − 320 × 320 × 24 (f 1×1),  320 × 320 × 5 (Iin) 320 × 320 × 29

(f 1×1, Iin)

Conv layer (ReLU) 24,3 × 3,1 [1 × 1] 320 × 320 × 29 320 × 320 × 24 Concatenation

− − 320 × 320 × 24 (f 3×3),  320 × 320 × 29 (fc1 ) 320 × 320 × 53

(f 3×3, fc1 )

Conv layer (ReLU) 24,5 × 5,1 [2 × 2] 320 × 320 × 53 320 × 320 × 24 Concatenation

− − 320 × 320 × 24 (f 5×5),  320 × 320 × 53 (fc2 ) 320 × 320 × 77

(f 5×5, fc2 )

Conv layer (ReLU) 24,1 × 1,1 − 320 × 320 × 77 320 × 320 × 24 Iin represents the input image, f n×n represents the output after convolution with n × n kernel, and f cn denotes the output feature map of nth concatenation layer in PRF  module.


> **Table A4**

> Detailed feature transformation description of LCFE module.

Layer Filter (Number of filters, size, and stride) Padding Dilation rate Input Output

CCB Dilated Convolution 3 × [32,3 × 3,1] [1 × 1] [1,2,3] 40 × 40 × 256 3 × [40 × 40 × 32] Concatenation (f1,f2,f3) − − − 3 × [40 × 40 × 32] 40 × 40 × 96 Convolution Layer [32,1 × 1,1] − − 40 × 40 × 96 40 × 40 × 32 CSAB(ReLU) ⎡

⎤

⎡

⎤

− 40 × 40 × 32 40 × 40 × 32

32, 1 × 1, 1 4, 3 × 3, 1 32, 1 × 1, 1

− 1 × 1 −

⎣

⎦

⎣

⎦

LSFB Max pooling − − − 40 × 40 × 256 20 × 20 × 256

(continued on next page)

22

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842


> **Table A4 (continued)**

Layer  Filter (Number of filters, size, and stride)  Padding  Dilation rate  Input  Output

⎡

⎤

⎡

⎤

Dense-Depthwise Separable Convolution  (GeLU)

− 40 × 40 × 256 40 × 40 × 1024

256, 3 × 3, 1 256, 1 × 1, 1 256, 3 × 3, 1 256, 1 × 1, 1 256, 3 × 3, 1 256, 1 × 1, 1


## 1 × 1

−
1 × 1
−
1 × 1
−

⎢⎢⎢⎢⎢⎢⎣

⎥⎥⎥⎥⎥⎥⎦

⎢⎢⎢⎢⎢⎢⎣

⎥⎥⎥⎥⎥⎥⎦

Transposed Conv Layer − − − 40 × 40 × 1024 40 × 40 × 256 Concatenation (fccab,ftr) − − − 40 × 40 × 3240 × 40 × 256 40 × 40 × 288

Data availability

Hu, X.-Z., Jeon, W.-S., Rhee, S.-Y., 2022. Sugar Beets and Weed Detection using Semantic

Segmentation, in: 2022 International Conference on Fuzzy Theory and Its  Applications (iFUZZY). Presented at the 2022 International Conference on Fuzzy  Theory and Its Applications (iFUZZY), pp. 1–4. https://doi.org/10.1109/  iFUZZY55320.2022.9985222. Huang, G., Liu, Z., Van Der Maaten, L., & Weinberger, K. Q. (2017). Densely Connected

The data supporting the findings of this study are available from the  GitHub Repository (https://github.com/MuhammadIrfan92/PRC_Net).

Convolutional Networks. In 2017 IEEE Conference on Computer Vision and Pattern  Recognition (CVPR). Presented at the 2017 IEEE Conference on Computer Vision and  Pattern Recognition (CVPR), IEEE (pp. 2261–2269). https://doi.org/10.1109/  CVPR.2017.243 Huang, H., Lin, L., Tong, R., Hu, H., Zhang, Q., Iwamoto, Y., Han, X., Chen, Y.-W., &


## References

Azadnia, R., Jahanbakhshi, A., Rashidi, S., Khajehzadeh, M., & Bazyar, P. (2022).

Developing an automated monitoring system for fast and accurate prediction of soil  texture using an image-based deep learning network and machine vision system.  Measurement, 190, Article 110669. https://doi.org/10.1016/j.  measurement.2021.110669 Badrinarayanan, V., Kendall, A., & Cipolla, R. (2017). SegNet: A deep convolutional

Wu, J. (2020). UNet 3+: A full-scale connected UNet for medical image  segmentation. In ICASSP 2020–2020 IEEE International Conference on Acoustics,  Speech and Signal Processing (ICASSP) (pp. 1055–1059). https://doi.org/10.1109/  ICASSP40776.2020.9053405 Imran Moazzam, S., Khan, U. S., Qureshi, W. S., Tiwana, M. I., Rashid, N., Hamza, A.,

encoder-decoder architecture for image segmentation. IEEE Transactions on Pattern  Analysis and Machine Intelligence, 39, 2481–2495. https://doi.org/10.1109/  TPAMI.2016.2644615 Butte, S., Vakanski, A., Duellman, K., Wang, H., & Mirkouei, A. (2021). Potato crop stress

Kunwar, F., & Nawaz, T. (2022). Patch-wise weed coarse segmentation mask from  aerial imagery of sesame crop. Computers and Electronics in Agriculture, 203, Article  107458. https://doi.org/10.1016/j.compag.2022.107458 Irfan, M., 2025. MuhammadIrfan92/PRC_Net. Janneh, L. L., Zhang, Y., Cui, Z., & Yang, Y. (2023). Multi-level feature re-weighted fusion

identification in aerial images using deep learning-based object detection. Agronomy  Journal, 113, 3991–4002. https://doi.org/10.1002/agj2.20841 Castellano, G., De Marinis, P., & Vessio, G. (2023a). Weed mapping in multispectral

for the semantic segmentation of crops and weeds. Journal of King Saud University -  Computer and Information Sciences, 35, Article 101545. https://doi.org/10.1016/j.  jksuci.2023.03.023 Jetson TX2 Module [WWW Document], n.d. . NVIDIA Developer. URL https://developer.

drone imagery using lightweight vision transformers. Neurocomputing, 562, Article  126914. https://doi.org/10.1016/j.neucom.2023.126914 Castellano, G., De Marinis, P., & Vessio, G. (2023b). Applying Knowledge Distillation to

nvidia.com/embedded/jetson-tx2 (accessed 1.13.25). Jiang, K., Afzaal, U., Lee, J., Jiang, K., Afzaal, U., & Lee, J. (2022). Transformer-based

Improve Weed Mapping with Drones. In Conference on Computer Science and  Intelligence Systems (FedCSIS). Presented at the 2023 18th Conference on Computer  Science and Intelligence Systems (FedCSIS) (pp. 393–400). Chattopadhay, A., Sarkar, A., Howlader, P., & Balasubramanian, V. N. (2018). Grad-CAM

weed segmentation for grass management. Sensors, 23. https://doi.org/10.3390/  s23010065 Kingma, D.P., & Ba, J., 2017. Adam: A Method for Stochastic Optimization. https://doi.

++: Generalized Gradient-based Visual Explanations for Deep Convolutional  Networks. In 2018 IEEE Winter Conference on Applications of Computer Vision  (WACV). Presented at the 2018 IEEE Winter Conference on Applications of Computer  Vision (WACV) (pp. 839–847). https://doi.org/10.1109/WACV.2018.00097 Chen, L.-C., Papandreou, G., Kokkinos, I., Murphy, K., & Yuille, A. L. (2018). DeepLab:

org/10.48550/arXiv.1412.6980. Li, T., Asai, M., Kato, Y., Fukano, Y., & Guo, W. (2024). Channel attention GAN-based

synthetic weed generation for precise weed identification. Plant Phenomics, 6, 0122.  https://doi.org/10.34133/plantphenomics.0122 Lin, T.-Y., Goyal, P., Girshick, R., He, K., & Doll´ar, P., 2018. Focal Loss for Dense Object

Semantic image segmentation with deep convolutional nets, atrous convolution, and  fully connected CRFs. IEEE Transactions on Pattern Analysis and Machine Intelligence,  40, 834–848. https://doi.org/10.1109/TPAMI.2017.2699184 Chen, L.-C., Papandreou, G., Schroff, F., Adam, H., 2017. Rethinking Atrous Convolution

Detection. https://doi.org/10.48550/arXiv.1708.02002. Luo, Y., & Pu, L. (2024). UAV remotely-powered underground IoT for soil monitoring.

IEEE Transactions on Industrial Informatics, 20, 972–983. https://doi.org/10.1109/  TII.2023.3272016 Ma, J., Li, F., & Wang, B., 2024. U-Mamba: Enhancing Long-range Dependency for

for Semantic Image Segmentation. https://doi.org/10.48550/arXiv.1706.05587. Chin, R., Catal, C., & Kassahun, A. (2023). Plant disease detection using drones in

Biomedical Image Segmentation. https://doi.org/10.48550/arXiv.2401.04722. Machidon, A. L., Kraˇsovec, A., Pejovi´c, V., & Machidon, O. M. (2025). SqueezeSlimU-Net:

precision agriculture. Precision Agriculture, 24, 1663–1682. https://doi.org/10.1007/  s11119-023-10014-y Chollet, F. (2017). Xception: Deep learning with depthwise separable convolutions. In

An adaptive and efficient segmentation architecture for real-time UAV weed  detection. IEEE Journal of Selected Topics in Applied Earth Observations and Remote  Sensing, 18, 5749–5764. https://doi.org/10.1109/JSTARS.2025.3536175 Menshchikov, A., Shadrin, D., Prutyanov, V., Lopatkin, D., Sosnin, S., Tsykunov, E.,

2017 IEEE Conference on Computer Vision and Pattern Recognition (CVPR). Presented at  the 2017 IEEE Conference on Computer Vision and Pattern Recognition (CVPR), IEEE  (pp. 1800–1807). https://doi.org/10.1109/CVPR.2017.195 Cohen, J. (1992). A power primer. Psychological Bulletin, 112, 155–159. https://doi.org/

Iakovlev, E., & Somov, A. (2021). Real-time detection of hogweed: UAV platform  empowered by deep learning. IEEE Transactions on Computers, 70, 1175–1188.  https://doi.org/10.1109/TC.2021.3059819 Milletari, F., Navab, N., & Ahmadi, S.-A., 2016. V-Net: Fully Convolutional Neural

10.1037//0033-2909.112.1.155 Danilchenko, K., & Segal, M. (2021). An Efficient Connected Swarm Deployment via

Deep Learning, in: Annals of Computer Science and Information Systems. In  Presented at the Proceedings of the 16th Conference on Computer Science and Intelligence  Systems (pp. 1–7). Deng, J., Zhong, Z., Huang, H., Lan, Y., Han, Y., Zhang, Y., Deng, J., Zhong, Z.,

Networks for Volumetric Medical Image Segmentation. https://doi.org/10.48550/  arXiv.1606.04797. Mishra, P., Singh, U., Pandey, C. M., Mishra, P., & Pandey, G. (2019). Application of

student’s t-test, analysis of variance, and covariance. Annals of Cardiac Anaesthesia,  22, 407–411. https://doi.org/10.4103/aca.ACA_94_19 Moazzam, S. I., Khan, U. S., Qureshi, W. S., Tiwana, M. I., Rashid, N., Alasmary, W. S.,

Huang, H., Lan, Y., Han, Y., & Zhang, Y. (2020). Lightweight semantic segmentation  network for real-time weed mapping using unmanned aerial vehicles. Applied  Sciences, 10. https://doi.org/10.3390/app10207132 Duan, B., Fang, S., Gong, Y., Peng, Y., Wu, X., & Zhu, R. (2021). Remote estimation of

Iqbal, J., & Hamza, A. (2021). A patch-image based classification approach for  detection of weeds in sugar beet crop. IEEE Access, 9, 121698–121715. https://doi.  org/10.1109/ACCESS.2021.3109015 Osman, Y., Dennis, R., & Elgazzar, K. (2021). Yield estimation and visualization solution

grain yield based on UAV data in different rice cultivars under contrasting climatic  zone. Field Crops Research, 267, Article 108148. https://doi.org/10.1016/j.  fcr.2021.108148 Fishkis, O., Weller, J., Lehmhus, J., P¨ollinger, F., Strassemeyer, J., & Koch, H.-J. (2024).

for precision agriculture. Sensors, 21, 6657. https://doi.org/10.3390/s21196657 Ramirez, W., Achanccaray, P., Mendoza, L. F., & Pacheco, M. A. C. (2020). Deep

Ecological and economic evaluation of conventional and new weed control  techniques in row crops. Agriculture, Ecosystems & Environment, 360, Article 108786.  https://doi.org/10.1016/j.agee.2023.108786 Haloui, D., Oufaska, K., Oudani, M., & El Yassini, K. (2024). Bridging Industry 5.0 and

convolutional neural networks for weed detection in agricultural crops using optical  aerial images. In 2020 IEEE Latin American GRSS & ISPRS Remote Sensing Conference  (LAGIRS). Presented at the 2020 IEEE Latin American GRSS & ISPRS Remote Sensing  Conference (LAGIRS) (pp. 133–137). https://doi.org/10.1109/  LAGIRS48042.2020.9165562 Ritharson, P. I., Raimond, K., Mary, X. A., & Robert, J. E. (2024). DeepRice: A deep

Agriculture 5.0: Historical Perspectives. Opportunities, and Future Perspectives.  Sustainability, 16, 3507. https://doi.org/10.3390/su16093507 Hendrycks, D., & Gimpel, K., 2023. Gaussian Error Linear Units (GELUs). https://doi.

learning and deep feature based classification of Rice leaf disease subtypes. Artificial  Intelligence in Agriculture, 11, 34–49. https://doi.org/10.1016/j.aiia.2023.11.001

org/10.48550/arXiv.1606.08415.

23

M. Irfan et al.                                                                                                                                                                                                                                    Expert Systems With Applications 326 (2026) 132842

Ronneberger, O., Fischer, P., & Brox, T. (2015). U-Net: Convolutional networks for

Vision – ECCV 2018. Springer International Publishing, Cham, pp. 3–19. https://doi.  org/10.1007/978-3-030-01234-2_1. Xie, E., Wang, W., Yu, Z., Anandkumar, A., Alvarez, J.M., & Luo, P., 2021. SegFormer:

biomedical image segmentation. In N. Navab, J. Hornegger, W. M. Wells, &  A. F. Frangi (Eds.), Medical Image Computing and Computer-Assisted Intervention –  MICCAI 2015 (pp. 234–241). Cham: Springer International Publishing. https://doi.  org/10.1007/978-3-319-24574-4_28.  Sa, I., Popovi´c, M., Khanna, R., Chen, Z., Lottes, P., Liebisch, F., Nieto, J., Stachniss, C.,

Simple and Efficient Design for Semantic Segmentation with Transformers, in:  Advances in Neural Information Processing Systems. Curran Associates, Inc., pp.  12077–12090. Yan, H., Zhang, C., & Wu, M., 2022. Lawin Transformer: Improving Semantic

Walter, A., & Siegwart, R. (2018). WeedMap: A large-scale semantic weed mapping  framework using aerial multispectral imaging and deep neural network for precision  farming. Remote Sensing, 10, 1423. https://doi.org/10.3390/rs10091423 Saiz-Rubio, V., & Rovira-M´as, F. (2020). From smart farming towards agriculture 5.0: A

Segmentation Transformer with Multi-Scale Representations via Large Window  Attention. ArXiv. Yeung, M., Sala, E., Sch¨onlieb, C.-B., & Rundo, L. (2022). Unified Focal loss: Generalising

review on crop data management. Agronomy, 10, 207. https://doi.org/10.3390/  agronomy10020207 Seiche, A. T., Wittstruck, L., Jarmer, T., Seiche, A. T., Wittstruck, L., & Jarmer, T. (2024).

Dice and cross entropy-based losses to handle class imbalanced medical image  segmentation. Computerized Medical Imaging and Graphics, 95, Article 102026.  https://doi.org/10.1016/j.compmedimag.2021.102026 Yu, F., & Koltun, V., 2016. Multi-Scale Context Aggregation by Dilated Convolutions.

Weed Detection from unmanned aerial vehicle imagery using deep learning—a  comparison between high-end and low-cost multispectral sensors. Sensors, 24.  https://doi.org/10.3390/s24051544 Shahi, T. B., Dahal, S., Sitaula, C., Neupane, A., & Guo, W. (2023). Deep Learning-based

https://doi.org/10.48550/arXiv.1511.07122. Yu, M., & Qin, F. (2023). Research on the applicability of transformer model in remote-

sensing image segmentation. Applied Sciences, 13, 2261. https://doi.org/10.3390/  app13042261 Zhang, H., Liu, M., Wang, Y., Shang, J., Liu, X., Li, B., Song, A., & Li, Q. (2021).

weed detection using UAV images: A comparative study. Drones, 7, 624. https://doi.  org/10.3390/drones7100624 Silva, J. A. O. S., de Siqueira, V. S., Mesquita, M., Vale, L. S. R., Marques, T. do N. B.,

Automated delineation of agricultural field boundaries from Sentinel-2 images using  recurrent residual U-Net. International Journal of Applied Earth Observation and  Geoinformation, 105, Article 102557. https://doi.org/10.1016/j.jag.2021.102557 Zhao, H., Shi, J., Qi, X., Wang, X., & Jia, J. (2017). Pyramid Scene Parsing Network. In

Silva, J. L. B. da, Silva, M. V. da, Lacerda, L. N., Oliveira-Júnior, J. F. de,  Lima, J. L. M. P. de, & Oliveira, H. F. E. de (2024). Deep learning for weed detection  and segmentation in agricultural crops using images captured by an unmanned  aerial vehicle. Remote Sensing, 16. https://doi.org/10.3390/rs16234394 Wang, N., Clevers, J. G. P. W., Wieneke, S., Bartholomeus, H., & Kooistra, L. (2022).

2017 IEEE Conference on Computer Vision and Pattern Recognition (CVPR). Presented at  the 2017 IEEE Conference on Computer Vision and Pattern Recognition (CVPR) (pp.  6230–6239). https://doi.org/10.1109/CVPR.2017.660 Zhu, L., Li, X., Sun, H., & Han, Y. (2024). Research on CBF-YOLO detection model for

Potential of UAV-based sun-induced chlorophyll fluorescence to detect water stress  in sugar beet. Agricultural and Forest Meteorology, 323, Article 109033. https://doi.  org/10.1016/j.agrformet.2022.109033 Woo, S., Park, J., Lee, J.-Y., & Kweon, I.S., 2018. CBAM: Convolutional Block Attention

common soybean pests in complex environment. Computers and Electronics in  Agriculture, 216, Article 108515. https://doi.org/10.1016/j.compag.2023.108515

Module, in: Ferrari, V., Hebert, M., Sminchisescu, C., Weiss, Y. (Eds.), Computer

24
