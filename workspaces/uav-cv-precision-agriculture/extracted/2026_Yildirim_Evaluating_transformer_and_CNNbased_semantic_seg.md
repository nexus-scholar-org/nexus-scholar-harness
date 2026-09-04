---
workspace_id: SCI-000134
doi: 10.1007/s11119-026-10362-5
title: Evaluating transformer- and CNN-based semantic segmentation models for sunflower
  inflorescence identification using a UAV RGB orthomosaic
authors:
- family_name: Yildirim
  given_name: Esra
  orcid: https://orcid.org/0000-0002-4951-0488
- family_name: Colkesen
  given_name: Ismail
  orcid: https://orcid.org/0000-0001-9670-3023
- family_name: Sefercik
  given_name: Umut Gunes
  orcid: https://orcid.org/0000-0003-2403-5956
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:26:14.852855+00:00'
---

# Evaluating transformer- and CNN-based semantic segmentation models for sunflower inflorescence identification using a UAV RGB orthomosaic

Precision Agriculture           (2026) 27:56  https://doi.org/10.1007/s11119-026-10362-5

Evaluating transformer- and CNN-based semantic  segmentation models for sunflower inflorescence  identification using a UAV RGB orthomosaic

Esra Yildirim1  · Ismail Colkesen1  · Umut Gunes Sefercik1

Received: 2 June 2025 / Accepted: 9 April 2026 © The Author(s) 2026, modified publication 2026


## Abstract

Purpose  Monitoring sunflower inflorescence development is critical for yield assessment 
and precision crop management. While convolutional neural networks (CNNs) have shown 
promise in UAV-based crop segmentation, the behavior and practical implications of recent 
vision transformer architectures for inflorescence-level identification and spatial pattern 
analysis remain insufficiently explored. This study aims to systematically evaluate trans­
former-based and CNN-based models for sunflower inflorescence detection and to assess 
their capability for field-scale spatial characterization.
Methods  A high-resolution UAV orthomosaic was used to evaluate state-of-the-art trans­
former-based models (SegFormer, Dense Prediction Transformer (DPT), and UPerNet) and 
CNN-based models (U-Net, DeepLabv3+, and PSPNet). A controlled experimental frame­
work was adopted, in which spatially disjoint training and testing subsets were extracted 
from the same production field to capture realistic within-field heterogeneity. All models 
were evaluated using standard performance metrics, including accuracy, precision, recall, 
F-score, and IoU. Beyond model-level performance comparison, targeted ablation analyses 
were conducted to examine the influence of key methodological choices, including loss 
function selection, patch overlap, and data augmentation strategies. In addition, explainable 
AI analysis (Grad-CAM) and computational cost assessments were performed.
Results  Among the 15 evaluated model configurations, the DPT model with the Twins-
PCPVT-Base encoder achieved the highest segmentation performance (F-score: 0.946, IoU: 
0.897) and demonstrated the most stable behavior across validation and spatially disjoint 
testing subsets. Explainable AI analysis using Grad-CAM revealed distinct attention pat­
terns between transformer- and CNN-based models, while computational cost analysis high­
lighted trade-offs between segmentation accuracy and efficiency. To enhance agronomic 
relevance, object-based segmentation outputs were aggregated into field-scale spatial repre­
sentations using complementary inflorescence-derived indicators describing inflorescence 
abundance and size. In addition, a weighted head area index (WHAI) was further introduced 
to integrate count- and area-based information, providing a balanced, image-derived spatial 
descriptor of within-field variability in inflorescence development.
Conclusions  Taken together, the results indicate that transformer-based semantic segmen­
tation, when integrated with object-level spatial indicators, enables consistent and inter­

Extended author information available on the last page of the article

56    Page 2 of 41 Precision Agriculture           (2026) 27:56

pretable field-scale characterization of within-field variability in sunflower inflorescence  development, thereby enhancing the agronomic relevance of UAV-based image analysis for  precision agriculture applications.

Keywords  Sunflower Detection · UAV Remote Sensing · Deep Learning · Vision  Transformers · CNN


## Introduction

Agricultural production and productivity are critical for sustaining crop yields under increas­ ing production pressures. Ensuring stable yields in major crops requires timely and accu­ rate monitoring of crop development and reproductive structures, which directly influence  yield-related characteristics. Accurate detection and quantification of crop heads (inflores­ cences or capitula), such as tassels in maize, spikes in wheat, inflorescences in rapeseed, and  capitula in sunflowers, play a key role in understanding spatial variability and supporting  agronomic decision-making (Jia et al., 2024; Li et al., 2023; Zhou et al., 2022; Jing et al.,  2024). In this context, spatial patterns of inflorescence abundance and size are increasingly  recognized as informative proxies for assessing within-field heterogeneity in reproductive  development, particularly in heterogeneous production fields characterized by spatial vari­ ability in plant density and head development.

Among oilseed crops, sunflower is particularly important due to its widespread cultiva­ tion and its dominant role in vegetable oil production in many regions. Beyond its economic  relevance, the sunflower provides a suitable model crop for studying spatial variability in  reproductive structures due to its distinct and visually discernible inflorescences. Accurate  characterization of sunflower inflorescences is therefore relevant for both agronomic moni­ toring and spatial analysis of reproductive development. According to recent agricultural  statistics, sunflowers account for a substantial proportion of total oilseed production in Tür­ kiye, which motivates the selection of sunflower as a representative case for field-scale  analysis (FAO, 2023; TUIK, 2024).

Remote sensing technologies have become an essential component for precision agri­ culture by enabling large-scale crop monitoring and analysis. While satellite-based obser­ vations have been widely used for crop classification, phenological analysis, and yield  estimation, their application at fine spatial scales is often constrained by spatial resolution,  cloud cover, and limited acquisition flexibility. Numerous studies have demonstrated the use  of multispectral satellite imagery and vegetation indices such as the normalized difference  vegetation index for crop monitoring and yield-related analyses (e.g., Zang et al., 2020;  Soriano-González et al., 2022; Cheng et al., 2022; Narin & Abdikan, 2022). However, these  approaches are less suitable for resolving fine-scale crop structures such as individual sun­ flower inflorescences, which require very high spatial-resolution imagery.

Unmanned Aerial Vehicles (UAVs) offer a flexible platform for agricultural monitoring,  enabling centimeter-level spatial resolution and user-defined acquisition timing. The ability  of UAV platforms to capture very-high-resolution RGB imagery has made them particu­ larly suitable for the identification and relative spatial characterization of individual crop  organs at the field scale. UAV-based studies have been applied to various precision agri­ culture tasks, including weed mapping, crop stand assessment, and yield-related analyses


## 1 3

Page 3 of 41     56  Precision Agriculture           (2026) 27:56

(Pérez-Ortiz et al., 2015; Vega et al., 2015; Bai et al., 2022; Liu et al., 2023). Recent UAV- based studies have reported promising results for crop organ detection under controlled and  relatively homogeneous experimental conditions; however, their generalizability to more  complex and heterogeneous field environments remains uncertain (Iamchuen et al., 2026).

Traditional approaches for crop organ detection relied on handcrafted features and clas­ sical machine learning or image processing techniques, which often struggle under variable  illumination, background complexity, and plant density. Recent advances in deep learn­ ing (DL), particularly convolutional neural networks (CNNs), have improved the reliability  of the detection and segmentation of crop structures from high-resolution UAV imagery.  By learning hierarchical and spatially adaptive feature representations, CNN-based models  enable more robust discrimination of crop organs from complex backgrounds. Accordingly,  architectures such as U-Net, DeepLab, and PSPNet have demonstrated strong performance  in sunflower-related applications, including capitula detection and growth stage recogni­ tion, under controlled and field-scale UAV conditions (Song et al. 2023a; Jing et al. 2024;  Yildirim et al. 2024).

Recent UAV-based studies have investigated sunflower inflorescence detection using  diverse deep learning paradigms under very-high-resolution imaging conditions. Bai et  al. (2023) employed a CNN-based semantic segmentation approach using an improved  U-Net architecture to segment and count sunflower heads, demonstrating the feasibility of  pixel-level segmentation, while focusing on a single CNN architecture. In contrast, object  detection-based strategies have been explored to enable more efficient and lightweight  implementations, with Jing et al. (2024) proposing a YOLO-derived architecture optimized  for rapid sunflower head detection from UAV imagery. More recently, Dong et al. (2025)  developed a dual-branch YOLOv10-based framework that integrates RGB imagery and  DEM-derived features, enabling accurate detection of sunflower heads while also support­ ing object-level geometric characterization through point cloud analysis. More recently,  Iamchuen et al. (2026) demonstrated the effectiveness of YOLO-based detection using UAV  imagery in a controlled experimental setting, while highlighting the potential challenges  associated with illumination variability, background complexity, and field heterogeneity  for real-world applications. Beyond head-level detection, Volpato et al. (2025 ) framed  UAV-based deep learning as a remote phenotyping tool for assessing sunflower flowering  dynamics, emphasizing the value of spatially explicit, inflorescence-driven indicators for  characterizing within-field variability. While these studies demonstrate the potential of UAV- based deep learning for sunflower analysis, most existing work focuses on a single model  family or detection paradigm, and systematic comparative evaluations of transformer-based  semantic segmentation models for sunflower inflorescence identification remain limited.

More recently, transformer-based architectures have emerged as increasingly explored  alternatives to CNNs in computer vision and remote sensing tasks. Introduced by Vaswani  et al. (2017), transformers leverage self-attention mechanisms to capture long-range spa­ tial dependencies, which can be advantageous for complex spatial patterns. Several stud­ ies have shown that transformer-based or hybrid CNN-transformer models can achieve  competitive or superior performance in agricultural applications, including crop mapping,  weed segmentation, and organ detection (Niu et al., 2022; Guo et al., 2025; Yildirim et  al., 2025). Despite these advances, the relative performance of transformer-based semantic  segmentation models for sunflower inflorescence identification from UAV imagery remains


## 1 3

56    Page 4 of 41 Precision Agriculture           (2026) 27:56

insufficiently explored in a systematic and comparative manner, particularly with respect to  segmentation accuracy, interpretability, and computational efficiency.

Accordingly, this study evaluates the performance of advanced transformer-based  semantic segmentation architectures, including SegFormer, DPT, and UPerNet with differ­ ent transformer backbones, for the identification and field-scale spatial characterization of  sunflower inflorescences using very-high-resolution UAV orthomosaic. The study adopts  a systematic and controlled comparative evaluation of transformer-based and widely used  CNN-based semantic segmentation models under consistent experimental settings, with a  focus on methodological consistency and robust cross-model performance comparisons. In  addition, model interpretability is examined using Grad-CAM visualizations, and computa­ tional efficiency is evaluated in light of operational considerations for UAV-based applica­ tions. Furthermore, the study extends object-level segmentation outputs to the within-field  scale by deriving grid-based, inflorescence-driven spatial indicators that summarize relative  within-field variability in sunflower inflorescence abundance and size. The specific objec­ tives are to:

(1) investigate the performance of SegFormer, DPT, and UPerNet models with multiple  transformer backbones,

(2) compare transformer-based approaches with state-of-the-art CNN-based semantic  segmentation models (U-Net, DeepLabv3+, PSPNet),

(3) evaluate model behavior across different training and testing subsets derived from  the same UAV orthomosaic to assess relative model robustness under consistent acquisition  conditions,

(4) analyze model decision-making mechanisms using Grad-CAM, and. (5) derive within-field spatial representations using complementary inflorescence- derived indicators to support the agronomic interpretation of deep learning-based segmen­ tation outputs.


## Methodology

This study investigates the integration of transformer- and CNN-based semantic segmenta­ tion models with UAV imagery to identify sunflower inflorescences. The performance of  the SegFormer, DPT, UPerNet, U-Net, DeepLabv3+, and PSPNet models was evaluated  using an RGB UAV orthomosaic as the primary input. As illustrated in Fig. 1, the overall  workflow was organized into three main stages. The first stage comprises UAV data acquisi­ tion and preprocessing, including orthomosaic generation and dataset preparation. The sec­ ond stage involves the implementation and evaluation of deep learning models, including  training, quantitative performance assessment, Grad-CAM-based model interpretation, and  computational efficiency analysis. The final stage consists of field-scale sunflower inflores­ cence mapping and spatial analysis. In this stage, the best-performing model is applied to  the full orthomosaic to generate field-scale inflorescence maps, followed by spatial indicator  analysis (IC, ICD, TIA, TIAD, and WHAI) and grid-level spatial analysis.


## 1 3

Page 5 of 41     56  Precision Agriculture           (2026) 27:56

Fig. 1  Simplified schematic of the three-stage methodological workflow adopted in this study

Study area and dataset

Study area

The study was conducted in a single experimental sunflower field managed by the Sakarya  Maize Research Institute, located in the Arifiye district of Sakarya province, Türkiye  (Fig. 2a). The experimental field is part of the Kirazca Agricultural Research Area, which is  routinely used for controlled crop experiments, including sunflower, maize, and wheat cul­ tivation (Fig. 2b). The field was cultivated with the sunflower (Helianthus annuus L.) hybrid  SUN 2259 CL during the 2022 growing season. Sowing was performed on 15 May 2022  using a precision pneumatic seeder to ensure uniform plant distribution, with a standard row  spacing of 70 cm and an intra-row spacing of 30–35 cm, resulting in an approximate seed­ ing rate of 300–400 g/da. Sunflower phenological development follows the scale proposed  by Schneiter and Miller (1981), which distinguishes vegetative (V) and reproductive (R)  growth stages. UAV data acquisition was conducted on August 29, 2022 (106 days after  planting), after the completion of flowering, during the seed-filling phase, and approaching  physiological maturity. At this stage, sunflower inflorescences exhibited a stable and fully  developed morphological size and structure, and were clearly distinguishable in RGB imag­ ery, enabling reliable manual annotation and model-based segmentation.

Two experimental plots within this area were designated as spatially non-overlapping  training and testing subsets, as illustrated in Fig. 2c. These subsets originate from the same  continuous production field and were spatially separated to reduce spatial autocorrelation  between training and testing samples, while maintaining consistent crop type, cultivar, man­ agement practices, and acquisition conditions. Although this experimental design does not


## 1 3

56    Page 6 of 41 Precision Agriculture           (2026) 27:56

Fig. 2  Location of the a) study area, (b) sunflower parcel in the Kirazca Agricultural Research Area, and  c) designed experimental plots for training and testing the models

enable cross-site or cross-condition generalization, it provides a controlled framework for  evaluating relative model robustness and segmentation performance under realistic within- field heterogeneity, including variability in plant spacing, inflorescence density, and local­ ized developmental conditions.

UAV image acquisition and orthomosaic production

UAV imagery was acquired during a single flight campaign conducted on 29 August 2022,  using a DJI Phantom 4 Pro V2, equipped with a 20 MP Sony Exmor RGB camera (8.8 mm  focal length). The flights were performed at an altitude of 50 m, with 80% front and 60%  side overlap, resulting in an average ground sampling distance (GSD) of approximately  1.47 cm. To enhance the geometric reconstruction of the sunflower canopy, the flight mis­ sion was planned in double-grid mode using the Pix4D Capture application, incorporating  north–south and east–west flight paths with a 70° oblique viewing angle. Under these flight  parameters, each section of the modeled area was described with at least nine overlapping  images.

Photogrammetric processing was performed using Agisoft Metashape software. For  image matching, structure from motion (SfM), a low-cost and robust technique for the  high-resolution image matching and generation of 3D geometry from a series of overlap­ ping aerial images, was utilized (Westoby et al., 2012). For absolute orientation, 14 poly­ carbonate mobile ground control points (GCPs) established in the field before the flight  were employed. The root mean square error (RMSE) of the GCPs used was determined as  ± 1.5 cm, which corresponds to one image pixel. After the completion of geometric correc­ tion processes, a dense point cloud was produced, and the detected noises were filtered. By  using filtered point clouds, a digital surface model (DSM) was generated and used for the  production of an RGB true orthomosaic at 1.4 cm GSD.


## 1 3

Page 7 of 41     56  Precision Agriculture           (2026) 27:56

Dataset preparation

The robustness and generalizability of deep learning-based semantic segmentation mod­ els depend strongly on the availability of an accurately labeled (annotated) dataset. In this  study, a sunflower inflorescence dataset was constructed by manually delineating individual  inflorescences on the high-resolution UAV orthomosaic through visual interpretation using  ArcGIS Pro (v.3.0.3). The resulting vector annotations were converted into raster format  to generate binary masks compatible with the requirements of the semantic segmentation  models.

Due to the high spatial resolution of the UAV orthomosaic and associated computational  constraints, the imagery and corresponding mask were subdivided into 256 × 256 pixel image  patches. A 50% spatial overlap (128 × 128 pixels) between adjacent patches was applied to  reduce boundary artifacts and preserve object continuity at patch edges. The influence of  patch overlap on model performance was further examined through an ablation analysis, as  reported in Sect. "Ablation analysis: Loss function, patch overlap, and data augmentation" .  Representative examples of image-mask pairs from the training subset are shown in Fig. 3.

To increase the diversity of training samples and improve model robustness under  within-field variability, data augmentation techniques were applied to the training data.  These included horizontal and vertical flipping, random cropping, brightness and contrast  adjustment, Gaussian noise addition, hue-saturation-value modification, and rotations of  90°, 180⁰, and 270⁰. The contribution of data augmentation to segmentation performance  was quantitatively evaluated through a dedicated ablation experiment (Sect. "Ablation anal­ ysis: Loss function, patch overlap, and data augmentation"). As a result, the final dataset  comprised 492 image patches with corresponding binary masks, containing a total of 24,912  annotated sunflower inflorescence instances.

The dataset was partitioned into training (70%), validation (20%), and testing (10%)  subsets for model development and evaluation. In addition, a spatially separated testing  subset was extracted from a different non-overlapping area of the same experimental field  to assess model behaviour under unseen spatial conditions within the field. Following the  same annotation and processing workflow, this subset consisted of 176 image patches and  9,900 labelled inflorescence instances. Although this experimental design does not represent  an independent site in an agronomic or acquisition sense, it enables a controlled evaluation

Fig. 3  Representative examples of images (a, c, e) and corresponding masks from the UAV sunflower  dataset (b, d, f)


## 1 3

56    Page 8 of 41 Precision Agriculture           (2026) 27:56

of model performance and sensitivity to spatial variability within a single, heterogeneous  production field.

Semantic segmentation models

In this work, several state-of-the-art deep learning-based semantic segmentation mod­ els were evaluated to identify sunflower inflorescences from very-high-resolution UAV  orthomosaic. Although transformer-based architectures have been increasingly adopted in  agricultural remote sensing, their systematic evaluation for sunflower inflorescence segmen­ tation in consistent experimental settings remains limited. Accordingly, this study examines  the performance and robustness of models, including SegFormer, Dense Prediction Trans­ former (DPT), and UPerNet with various transformer encoders. These architectures have  demonstrated strong performance in various agricultural object detection and segmentation  tasks (Garibaldi-Márquez et al., 2025; Martins et al., 2024; Gibril et al., 2023). For com­ parative reference, widely used CNN-based architectures, namely U-Net, DeepLabv3+, and  PSPNet, were also included to enable a direct comparison between transformer-based and  convolutional approaches. Furthermore, model performance was analyzed using a range  of ImageNet-pretrained encoder backbones, including ResNet-50, MobileNet-v2, MiT-B1,  MiT-B2, MiT-B3, EfficientViT-B3, Twins-PCPVT-Base, Twins-PCPVT-Small, and Fast­ ViT-S36. Detailed descriptions of the evaluated models and their configurations are pro­ vided in the following subsections.

SegFormer

SegFormer (Xie et al., 2021) is a transformer-based semantic segmentation framework  designed to achieve a favorable balance between segmentation accuracy and computational  efficiency. The model adopts an encoder-decoder architecture consisting of a hierarchical  transformer-based encoder and a lightweight multilayer perceptron (MLP) decoder (Fig. 4).

The encoder employs a Mix Transformer (MiT) backbone that extracts multi-scale fea­ ture representations at four spatial resolutions (1/4, 1/8, 1/16, and 1/32 of the input image  size). This hierarchical design enables SegFormer to capture both local spatial details and  broader contextual information, which is particularly relevant for detecting sunflower inflo­ rescences exhibiting variability in size, density, and spatial arrangement. The extracted  multi-level features are subsequently integrated by the All-MLP decoder to generate the  final semantic segmentation map at 1/4 resolution.

Each encoder block consists of an efficient self-attention mechanism, a Mix feed-forward  network (Mix-FFN), and overlap patch merging layers. To reduce the computational cost  associated with self-attention, SegFormer applies a sequence reduction strategy within the  encoder (Wang et al., 2021). Unlike conventional vision Transformers (ViTs) that rely on  fixed-resolution positional encodings, SegFormer implicitly encodes positional information  through convolutional operations within the Mix-FFN, allowing spatial relationships to be  learned in a data-driven manner (Islam et al., 2020). Overlap patch merging further pre­ serves spatial continuity while progressively reducing feature resolution.

The computational complexity of SegFormer depends primarily on the selected MiT  encoder variant. In this study, different MiT backbones were evaluated to analyze the trade-


## 1 3

Page 9 of 41     56  Precision Agriculture           (2026) 27:56

Fig. 4  Architecture of the SegFormer

off between segmentation performance and computational efficiency, ranging from light­ weight configurations optimized for fast inference to larger variants designed to maximize  accuracy.

Dense prediction transformer (DPT)

Dense Prediction Transformers (DPT), introduced by Ranftl et al. (2021), are encoder- decoder architectures that employ vision transformers as the primary backbone for dense  prediction tasks, including semantic segmentation and monocular depth estimation. By  leveraging transformer-based representations in a vision-oriented encoder-decoder design,  the DPT model improves accuracy in pixel-wise predictions. While the basic transformer  module and self-attention mechanism are maintained, the model adopts a hierarchical pro­ cessing strategy that extracts features at multiple scales, enabling the capture of both high- level semantic context and finer-grained image details (Bolcek et al., 2025).

The encoder of the DPT is structured as a sequence of transformer blocks, with each  block comprising multiple transformer layers. The decoder consists of two primary mod­ ules, namely the reassemble and fusion blocks. According to the general architecture of the  model, as illustrated in Fig. 5(a), the input image is transformed into tokens (depicted in  cream). Augmentation of the image embedding is performed using positional embedding,  and a readout token (represented in red), independent from patches, is presented. Then,  the tokens are processed through various stages of the transformer, and outputs from these  stages are reassembled into image-like representations at different resolutions. During the  reassemble operation (Fig. 5b), tokens are assembled into feature maps at a spatial resolu­ tion that is 1 of the input image’s original resolution. These feature maps are progressively  fused and upsampled by fusion modules (Fig. 5(c)), which employ residual convolutional  units to produce high-resolution, finer-grained predictions.

The original paper introduces three DPT model variants, namely DPT-Base, DPT-Large,  and DPT-Hybrid. DPT-Base is characterized by a patch-based embedding scheme and 12  transformer layers. DPT-Large extends to 24 transformer layers with wider feature sizes


## 1 3

56    Page 10 of 41 Precision Agriculture           (2026) 27:56

Fig. 5  General overview of the (a) DPT architecture, (b) Reassembles operation, and (c) Fusion block

Fig. 6  UPerNet network structure

compared to DPT-Base. On the other hand, DPT-Hybrid leverages a ResNet-50 convolu­ tional backbone to generate image embeddings before processing by 12 transformer layers  (Thisanke et al., 2023).

UPerNet

The Unified Perceptual Parsing Network (UPerNet) (Xiao et al., 2018) is a semantic seg­ mentation framework designed to effectively integrate multi-scale contextual information  and fine spatial details. UPerNet is built upon a Feature Pyramid Network (FPN) archi­ tecture (Lin et al., 2017), which combines bottom-up and top-down pathways with lateral  connections to fuse hierarchical feature representations extracted by the backbone network  (Fig. 6).

At the deepest feature level, a Pyramid Pooling Module (PPM) is employed to capture  global contextual information before propagating features through the top-down pathway.  This design enables the effective fusion of high-level semantic features and low-level spatial  details, which is particularly beneficial for precise object-level segmentation tasks such as  sunflower inflorescence detection. Although UPerNet was originally proposed for multi- task visual recognition, its feature fusion strategy is well-suited to semantic segmentation  applications. In this study, UPerNet is therefore employed exclusively for sunflower inflo­


## 1 3

Page 11 of 41     56  Precision Agriculture           (2026) 27:56

rescence segmentation, leveraging its multi-scale representation capability rather than its  multi-task formulation.

U-Net

The U-Net architecture (Ronneberger et al., 2015), which features a symmetric U-shaped  structure and was originally introduced for semantic segmentation in biomedical applica­ tions, has become a baseline model for remote sensing image analysis due to its superiority  on image segmentation tasks in various fields, including precise agriculture (Lin et al., 2025;  Zou et al., 2021; Xu et al., 2024; Machidon et al., 2025). The model architecture, as shown  in Fig. 7, features a symmetrical shape with a contracting path (the encoder on the left) and  an expansive path (the decoder on the right). In the network, given image tiles are processed  by the encoder, where an increasing number of down-sampled feature maps are generated  according to the network’s depth. Then, the decoder progressively recovers spatial localiza­ tion and fine-grained details from the encoded features to generate the final segmentation  output (Gibril et al., 2021).

The contracting path of the U-Net architecture is structured according to the conventional  design of convolutional networks, in which two 3 × 3 unpadded convolutions are applied  repeatedly, each followed by a Rectified Linear Unit (ReLU) activation function and a 2 × 2  maximum pooling layer to perform downsampling (Fig. 7). Each downsampling stage dou­ bles the number of feature channels. In the expansive path, feature maps are upsampled,  followed by a 2 × 2 up-convolution that reduces the number of feature channels by half.  These are concatenated with appropriately cropped feature maps from the contracting path,  after which two 3 × 3 convolution layers with ReLU activations are applied. Cropping is car­ ried out to address the border information loss inherent in convolution operations. The final  output is produced by a 1 × 1 convolution layer that reduces the number of channels of each  feature map to the required number of categories.

Fig. 7  U-Net network structure


## 1 3

56    Page 12 of 41 Precision Agriculture           (2026) 27:56

DeepLabv3+

Introduced by the Google research group, the family of DeepLab has evolved over sev­ eral versions, namely DeepLabv1, DeepLabv2, DeepLabv3, and DeepLabv3+, each incor­ porating architectural innovations to enhance segmentation accuracy. These segmentation  architectures leverage multiscale atrous convolutions to effectively address the challenge  of segmenting objects at various scales. In contrast to conventional convolution operations,  atrous convolution enlarges the receptive field while preserving feature resolution, without  increasing the number of learnable parameters (Jiang et al., 2021). The initial architecture,  DeepLabv1, proposed by Chen et al. (2014), combines DCNNs with probabilistic graphical  models to enhance the localization of segment boundaries. The improved version, Deep­ Labv2, uses the Atrous Spatial Pyramid Pooling (ASPP) mechanism, which applies convo­ lutional filters with varying dilation rates, enabling the model to capture both object details  and contextual information across multiple scales (Chen et al., 2016). The next develop­ ment in the DeepLab series, DeepLabv3, incorporates advanced modifications to the ASPP  mechanism (Chen et al., 2017). As the most advanced version, DeepLabv3 + introduces a  decoder structure to the architecture, refining segmentation maps and producing more accu­ rate object boundaries (Chen et al., 2018). The DeepLabv3 + framework comprises three  core components: an encoder, an ASPP module, and a decoder, as illustrated in Fig. 8. The  encoder part of the model is responsible for extracting rich semantic information and reduc­ ing feature maps, with its design dependent on the selected backbone network architecture.  To address the challenge of multiscale object segmentation, the ASPP module captures fea­ tures across different scales from the input image. Subsequently, the decoder progressively  recovers spatial information, producing segmentation maps with sharper object boundaries.

Fig. 8  DeepLabv3 + network structure


## 1 3

Page 13 of 41     56  Precision Agriculture           (2026) 27:56

PSPNet

The Pyramid Scene Parsing Network (PSPNet) is an encoder-decoder-based semantic seg­ mentation network introduced by Zhao et al. (2017). At the core of the architecture lies the  pyramid pooling module, which aggregates contextual information across multiple scales,  thereby enhancing the model’s capability to capture multiscale features. The detailed struc­ ture of PSPNet is illustrated in Fig. 9. Feature extraction is first performed using an adopted  CNN encoder architecture, such as ResNet-50 and VGG-16, producing high-level feature  maps. The size of the resulting feature map is 1/8 of the input. Contextual information is  subsequently aggregated using the pyramid pooling module. A four-level pyramid structure  is employed, with pooling kernels covering the entire image, half the image, and smaller  regions. These pooled features are fused to form a global prior, which is then concatenated  with the original feature map. Finally, a convolutional layer is applied to produce the output  prediction map.

The pyramid pooling module, the purple dotted line in Fig. 9, is the core part of the net­ work and performs feature fusion over four distinct scales. At the coarsest level (in pink),  global pooling produces a single output bin. The subsequent level divides the feature map  into multiple sub-regions, where pooled representations are generated for distinct locations.  As a result, the outputs at diverse pyramid scales of the module include feature maps of  varying sizes. A 1 × 1 convolution is subsequently applied after each scale to compress the  feature dimensions to 1/N of the original, where N corresponds to the total number of pyra­ mid scales. The resulting low-dimensional maps are upsampled to the original map size  using bilinear interpolation. The final global feature representation is obtained by concat­ enating features from all pyramid levels (Zhao et al., 2017).

Evaluation metrics and statistical analysis

In this study, various accuracy assessment metrics were utilized to evaluate the performance  of the implemented deep learning models. These metrics include precision, recall, F-score,  accuracy, and intersection over union (IoU), which are widely used in deep learning-based  semantic segmentation applications. To derive these metrics, a confusion matrix was first  generated, and true positives (TP), false positives (FP), true negatives (TN), and false nega­ tives (FN) were computed from it. TP corresponds to correctly identified positive cases,  whereas FP represents negative instances misidentified as positive. TN indicates the accu­

Fig. 9  Architecture of the PSPNet


## 1 3

56    Page 14 of 41 Precision Agriculture           (2026) 27:56

rate identification of negative cases, and FN arises when positive cases are misidentified as  negative. Utilizing these metrics, accuracy, precision, recall, and IoU are calculated. Preci­ sion reflects the model’s accuracy in predicting the positive class, calculated as the propor­ tion of TPs among all positive predictions. Recall measures the model’s capacity to detect  all actual positives by computing the ratio of TPs to the sum of TPs and FNs. The F-score  combines precision and recall through their harmonic mean, providing a balanced evalua­ tion of segmentation performance (Luoni et al., 2024). Pixel-wise accuracy, also referred to  as overall accuracy or percent correct classification, is defined as the proportion of correctly  classified pixels to the total number of pixels (Maxwell et al. 2021a). Another commonly  used evaluation metric is IoU, defined as the ratio of the intersection to the union areas of the  predicted mask and the ground-truth mask (Maxwell et al. 2021b). These accuracy metrics  can be mathematically expressed by Eqs. (1)-(5).

display-e q -E qu 1  (1)

displa y -e q- E qu2 (2)

d i splay - e q -Equ3  (3)

display- e q- E qu 4  (4)

dis p la y- e q- E qu5 (5)

In addition to descriptive accuracy metrics, statistical analysis was conducted to assess  whether performance differences between selected models were statistically significant. A  paired-samples t-test was employed because performance metrics were computed on the  same set of selected test image patches, enabling matched comparisons and controlling  inter-sample variability (Japkowicz & Shah, 2011). Similar statistical validation strategies  have been widely adopted in recent deep learning-based semantic segmentation studies to  ensure the robustness of comparative performance analysis (e.g., Tran et al., 2025). The  analysis was applied to accuracy, precision, recall, F-score, and IoU at a 95% confidence  level (α = 0.05). The results of the statistical analysis are presented in Sect. "Within-field  robustness evaluation of transformer- and CNN-based models".

Experimental setup

All training and evaluation procedures for the transformer- and CNN-based semantic seg­ mentation models were conducted in Python using the PyTorch deep learning framework  and the Segmentation Models PyTorch (SMP) library (Iakubovskii, 2019). All experiments  were executed in the Google Colab Pro cloud environment, which provides access to an  NVIDIA A100 GPU for accelerated computation.


## 1 3

Page 15 of 41     56  Precision Agriculture           (2026) 27:56

A comprehensive experimental comparison was conducted across multiple architectures  and encoder configurations to identify the best-performing encoder-decoder combina­ tions. In total, nine experiments were performed with transformer-based models, includ­ ing SegFormer-MiT-B1, SegFormer-MiT-B2, SegFormer-MiT-B3, UPerNet-MiT-B2,  UPerNet-Twins-PCPVT-Base, UPerNet-EfficientViT-B3, DPT-FastViT-S36, DPT-Twins- PCPVT-Base, and DPT-Twins-PCPVT-Small. Six CNN-based experiments were also con­ ducted using U-Net, DeepLabv3+, and PSPNet with ResNet-50 and MobileNet-v2 encoders.

All models were initialized with ImageNet-pretrained weights to accelerate conver­ gence and enhance performance. The Adam (Kingma, 2014) optimizer was used across all  experiments, with an initial learning rate of 0.001 and a training duration of 500 epochs.  The batch size was set to 8 for U-Net and PSPNet models and 16 for DeepLabv3+, Seg­ Former, UPerNet, and DPT architectures. Dice loss was employed for CNN-based models,  while binary cross-entropy loss was adopted for transformer-based architectures, following  common practices reported in the literature. To assess the potential impact of loss function  choice on model comparison, additional loss function-specific experiments were conducted  for the best-performing CNN- and transformer-based models, as reported in Sect. "Ablation  analysis: Loss function, patch overlap, and data augmentation". The hyperparameter set­ tings utilized for each model are presented in Table 1.

Object-based spatial indicators derived from sunflower inflorescences

DL-based sunflower inflorescences (heads, capitula) segmentation provides detailed object- level information beyond pixel-wise classification, enabling the derivation of agronomi­ cally meaningful spatial indicators. However, raw detection outputs alone (e.g., individual  inflorescence masks) are often insufficient for practical agricultural applications unless  they are spatially aggregated and interpreted at the field scale. To address this limitation,  a set of object-based, inflorescence-derived spatial indicators was developed to summarize  sunflower inflorescence abundance, size, and spatial distribution within fixed spatial units,  thereby bridging the gap between DL segmentation outputs and field-scale spatial informa­ tion relevant for agronomic interpretation.

All indicators were computed using the inflorescence segmentation outputs of the  selected DL model identified as optimal based on the comparative analysis, ensuring consis­ tent object delineation and aggregation across the study area. The study area was subdivided  into non-overlapping grid cells of 256 × 256 pixels (approximately 3.58 m × 3.58 m on the


> **Table 1  Hyperparameter settings**

> used for the training of semantic 
segmentation models

Hyperparameters Models U-Net,  PSPNet

DeepLabv3+ SegFormer,  UPerNet,  DPT Optimization Adam Adam Adam Initial Learning  Rate

0.001 0.001 0.001

Epoch 500 500 500 Batch Size 8 16 16 Loss Function Dice Dice Binary cross  entropy Pretrained  Weights

ImageNet ImageNet ImageNet


## 1 3

56    Page 16 of 41 Precision Agriculture           (2026) 27:56

ground), which were treated as spatial analysis units. This grid size was selected to balance  spatial detail and statistical robustness, allowing stable estimation of both count- and area- based metrics while preserving intra-field variability relevant for spatial interpretation and  zone-based field assessment, particularly under heterogeneous field conditions.

Inflorescence abundance and size were initially characterized using a set of general object- based indicators, including Inflorescence Count (IC), Inflorescence Count Density (ICD),  Total Inflorescence Area (TIA), and Total Inflorescence Area Density (TIAD) (Table 2).  Count-based indicators (IC and ICD) quantify the numerical abundance of inflorescences  within each grid cell and primarily reflect plant stand density and the occurrence of miss­ ing or poorly developed plants. In contrast, area-based indicators (TIA and TIAD) empha­ size the cumulative size and spatial dominance of inflorescences within the grid, serving as  proxies for variability in reproductive organ development. Specifically, TIA is computed as  the cumulative area of pixels classified as inflorescence by the segmentation model within  each grid cell. This measure reflects the spatial extent of model-predicted inflorescence  regions and should be interpreted as a relative, image-derived descriptor of inflorescence  size dominance, not as a direct physical or biophysical measurement. Although these indica­ tors provide complementary information, separately representing inflorescence abundance  and size can lead to contrasting spatial patterns in areas where the two diverge, potentially  complicating the interpretation of crop condition indicators.

To integrate inflorescence abundance and relative size within a single spatial descriptor,  the Weighted Head Area Index (WHAI) was defined as a composite, object-based indicator  derived exclusively from model-predicted inflorescence regions (Table 2). Unlike count- based metrics, which ignore size variability, or area-based metrics, which may be domi­ nated by a few large inflorescences, WHAI provides a relative, image-derived descriptor  that jointly reflects these two components. Importantly, WHAI does not represent a direct  estimate of yield, biomass, or any biophysical variable observed in the field. Instead, it  should be interpreted as a spatial indicator of within-field variability in predicted inflores­ cence characteristics, intended for comparative and exploratory field-scale analyses, with­ out implying agronomic quantification.

The computation of WHAI involves three steps. First, the area of each detected inflores­ cence is normalized relative to the maximum observed inflorescence area across the field:


> **Table 2  Definition and formula­**

> tion of object-based inflores­
cence-derived spatial indicators

Indicator Symbol Formulation Primary  information Inflorescence  Count

IC inl i ne-eq-IEq2 Inflorescence  abundance Inflores­ cence Count  Density

ICD inli n e-

Spatial  density

eq-IEq3

TIA inli n e

Total In­ florescence  Area

-IEq4 Cumulative  size

inline-eq-IEq7denotes the number of  inflorescences within grid  cell g,inline-eq-IEq8is the area of the i-th  inflorescence,inline-eq-IEq9represents  the grid cell area, andinline-eq-IEq10is a  sub-linear weighting exponent  controlling the contribution of  the inflorescence size (set to 0.3  in this study)

-eq

-

Total In­ florescence  Area Density

TIAD

Relative  dominance

IE

inlin e

eq-

q5

I Eq 6 Integrated  abundance– size

WHAI inlin e -

Weighted  Head Area  Index

eq-


## 1 3

Page 17 of 41     56  Precision Agriculture           (2026) 27:56

dis p la y-e q-Equ6 (6)

where inline-eq-IEq11 denotes the normalized area of inflorescence i, and inl ine-eq-IEq12 represents the maxi­ mum detected inflorescence area. This normalization ensures scale invariance and reduces  sensitivity to acquisition-specific factors such as spatial resolution and imaging conditions.  Second, a sub-linear size-based weighting function is applied to moderate the contribution  of large inflorescences:

di s pla

y-eq-Equ7  (7)

where inline-eq-IEq13 is the weight assigned to inflorescence i, and inline-eq-IEq14 is a scaling exponent controlling  the relative contribution of inflorescence size. In this study, λ was set to 0.3 based on a sen­ sitivity analysis conducted across a range of λ values (0.10–0.95), with the objective of bal­ ancing count- and area-based contributions within WHAI. The selected value corresponds  to the minimum absolute difference between the Spearman correlation coefficients of WHAI  with IC and TIA. Details of the λ sensitivity analysis are provided in the Supplementary  Material (Fig. S1). Finally, WHAI is computed for each grid cell by spatial aggregation:

y

displ a

-Equ8 (8)

-eq

The resulting WHAI values are assigned to their corresponding grid cells to generate a con­ tinuous, field-scale WHAI map, facilitating the identification of spatial clusters and within- field anomalies that may require further agronomic inspection or targeted analysis.


## Results and discussions

Comparative evaluation of transformer- and CNN-based models for sunflower  segmentation

This study comprehensively evaluated fifteen state-of-the-art transformer- and CNN-based  semantic segmentation models for identifying sunflower inflorescences using a custom  UAV-derived dataset. The performance comparison of trained models on the validation data­ set, based on standard accuracy assessment metrics, is presented in Table 3. Metrics with  the highest scores are indicated in bold. According to the results, transformer-based models  demonstrated overall higher segmentation performance, achieving accuracy, F-score, and  IoU values exceeding 0.97, 0.91, and 0.84, respectively, while CNN-based models attained  values above 0.96, 0.86, and 0.76, respectively.

Given the impact of vision transformer encoders on transformer model performance,  SegFormer and UPerNet achieved the highest scores when combined with the MiT-B2  encoder, whereas DPT achieved its best performance with the Twins-PCPVT-Base encoder.  The ResNet-50 encoder consistently outperformed MobileNet-v2 across all model architec­ tures in the CNN category. Among the six top-performing encoder-decoder combinations  (DPT–Twins-PCPVT-Base, UPerNet–MiT-B2, SegFormer–MiT-B2, U-Net–ResNet-50,


## 1 3

56    Page 18 of 41 Precision Agriculture           (2026) 27:56


> **Table 3  Performance metrics of CNN- and transformer-based models evaluated on the validation dataset**

Model Encoder Accuracy F-Score IoU Precision Recall CNN- based  networks

U-Net ResNet-50 0.9863 0.9459 0.8975 0.9463 0.9457 MobileNet-v2 0.9858 0.9441 0.8943 0.9426 0.9460 DeepLabv3+ ResNet-50 0.9827 0.9316 0.8720 0.9330 0.9303 MobileNet-v2 0.9795 0.9170 0.8470 0.9398 0.8957 PSPNet ResNet-50 0.9698 0.8790 0.7843 0.8861 0.8723 MobileNet-v2 0.9666 0.8682 0.7673 0.8634 0.8734 Trans­ former- based  networks

SegFormer MiT-B1 0.9783 0.9143 0.8423 0.9160 0.9130 MiT-B2 0.9847 0.9392 0.8855 0.9415 0.9371 MiT-B3 0.9837 0.9350 0.8781 0.9379 0.9322 UPerNet EfficientViT-B3 0.9835 0.9350 0.8780 0.9322 0.9378 MiT-B2 0.9852 0.9413 0.8893 0.9421 0.9407 Twins-PCPVT- Base

0.9845 0.9391 0.8853 0.9330 0.9454

DPT FastViT-S36 0.9837 0.9347 0.8776 0.9427 0.9270 Twins-PCPVT- Small

0.9850 0.9405 0.8877 0.9375 0.9435

0.9864 0.9459 0.8974 0.9456 0.9462

Twins-PCPVT- Base

DeepLabv3+–ResNet-50, and PSPNet–ResNet-50), transformer-based models generally  achieved higher performance. However, the U-Net with the ResNet-50 encoder demon­ strated competitive results, in some cases comparable to those of transformer-based archi­ tectures. In summary, the performance analysis revealed that DPT-Twins-PCPVT-Base and  U-Net-ResNet-50 achieved the most accurate segmentation results for sunflower inflores­ cence identification, each with an F-score of 0.9459, with minimal differences in accu­ racy and IoU metrics. These models were followed by UPerNet-MiT-B2 (F-score: 0.9413),  SegFormer-MiT-B2 (F-score: 0.9392), DeepLabv3+-ResNet-50 (F-score: 0.9316), and  PSPNet-ResNet-50 (F-score: 0.8790) models. Among all models, PSPNet-MobileNet-v2  exhibited the weakest performance, with the lowest values across all metrics.


> **Figure 10 illustrates the evolution of training and validation losses over 500 epochs for**

> the six best-performing models. It was clear from the graphs that both the training and 
validation losses of all models gradually decreased with increasing epochs. By the end of 
500 epochs, the training and validation loss curves reached their minimum values without 
evident signs of severe overfitting or unstable training behavior. Notably, transformer-based 
models, including DPT-Twins-PCPVT-Base, UPerNet-MiT-B2, and SegFormer-MiT-B2, 
exhibited smoother and more stable convergence patterns compared to CNN-based mod­
els, including U-Net-ResNet-50, DeepLabv3+-ResNet-50, and PSPNet-ResNet-50. These 
results indicate that transformer architectures are optimized more effectively during train­
ing, demonstrating more stable optimization behavior and learning dynamics under the 
given experimental conditions.

The progression of the accuracy, F-score, and IoU metrics during the training and vali­ dation is shown in Fig. 11. CNN models achieved rapid metric improvement in the ini­ tial epochs, stabilizing between epochs 100 and 150, which indicates early saturation. This  behaviour reflects faster convergence but limited long-term learning capacity. On the other  hand, the training and validation metrics of transformer-based models exhibited gradual,  sustained improvement over all 500 epochs, suggesting a deeper, more progressive learning


## 1 3

Page 19 of 41     56  Precision Agriculture           (2026) 27:56

Fig. 10  Loss graphs of the best performing encoder-decoder combinations estimated for (a) training data,  (b) validation data during the training and validation process

trajectory. This trend indicates a more gradual and progressive learning process, albeit at the  cost of higher computational demand due to architectural complexity.

Within-field robustness evaluation of transformer- and CNN-based models

In addition to evaluating sunflower inflorescence segmentation performance on the training,  validation, and test datasets, the models were further assessed using a spatially disjoint test  subset extracted from a non-overlapping area of the same production field. This evaluation  was designed to examine the relative robustness of transformer- and CNN-based models  under spatially disjoint within-field conditions, while maintaining identical acquisition set­ tings, crop type, phenological stage, and management practices. Although this experimental  design does not represent cross-field or cross-season generalization, it provides a controlled  framework for analyzing model sensitivity to within-field spatial heterogeneity. For this pur­ pose, the trained transformer- and CNN-based models were tested on an unseen test site, and  the standard accuracy metrics were computed. Table 4 summarizes the relative robustness  performance of all evaluated models on this within-field test subset. Some important con­ clusions can be drawn from the results. First, among the CNN-based architectures, U-Net  and DeepLabv3 + models, particularly those employing the ResNet-50 encoder, achieved  the highest overall performance. U-Net (ResNet-50) recorded an F-score of 0.8876, an IoU  of 0.7979, and a recall of 0.9365, indicating high segmentation accuracy and strong sensitiv­ ity. DeepLabv3+ (ResNet-50) exhibited similar performance, with slightly higher precision  (0.8471) and accuracy (0.9691), suggesting sharper object boundaries and reduced false  positives. Conversely, PSPNet, especially with the MobileNet-v2 encoder, yielded the low­ est robustness performance among CNNs (F-score: 0.8407, IoU: 0.7253), highlighting its  limited ability to segment under within-field spatial variability.

On the other hand, transformer-based models displayed competitive or superior per­ formance compared to CNN-based models. SegFormer configurations using MiT-B2 and  MiT-B3 encoders achieved F-scores of 0.8879 and 0.8880, respectively, and IoU values of  approximately 0.799, demonstrating effective pixel-level segmentation. UPerNet models,


## 1 3

56    Page 20 of 41 Precision Agriculture           (2026) 27:56

Fig. 11  The evolution of the evaluation metrics during the training and validation process of the best- performing models, (a) accuracy, (b) F-score, (c) IoU


## 1 3

Page 21 of 41     56  Precision Agriculture           (2026) 27:56


> **Table 4  Robustness performance of transformer- and CNN-based models on the spatially disjoint within-**

> field test subset

Model Encoder Accuracy F-Score IoU Precision Recall CNN- based  networks

U-Net ResNet-50 0.9688 0.8876 0.7979 0.8446 0.9365 MobileNet-v2 0.9686 0.8872 0.7974 0.8427 0.9381 DeepLabv3+ ResNet-50 0.9691 0.8884 0.7994 0.8471 0.9353 MobileNet-v2 0.9684 0.8843 0.7928 0.8558 0.9164 PSPNet ResNet-50 0.9593 0.8524 0.7429 0.8159 0.8938 MobileNet-v2 0.9554 0.8407 0.7253 0.7935 0.8954 Trans­ former- based  networks

SegFormer MiT-B1 0.9642 0.8707 0.7712 0.8320 0.9150 MiT-B2 0.9689 0.8879 0.7986 0.8466 0.9346 MiT-B3 0.9691 0.8880 0.7987 0.8500 0.9306 UPerNet EfficientViT-B3 0.9677 0.8845 0.7930 0.8376 0.9380 MiT-B2 0.9687 0.8878 0.7984 0.8426 0.9392 Twins-PCPVT- Base

0.9681 0.8863 0.7959 0.8358 0.9442

DPT FastViT-S36 0.9688 0.8865 0.7962 0.8524 0.9245 Twins-PCPVT- Small

0.9676 0.8847 0.7933 0.8332 0.9439

0.9698 0.8907 0.8030 0.8512 0.9349

Twins-PCPVT- Base

particularly with the Twins-PCPVT-Base and MiT-B2 encoders, also achieved strong, bal­ anced precision and recall. Among all models evaluated, DPT with the Twins-PCPVT-Base  encoder achieved the highest overall performance, with an F-score of 0.8907, an IoU of  0.8030, and an accuracy of 0.9698. This result indicates more consistent performance on  the spatially disjoint test subset under identical acquisition conditions. In contrast, DPT- Twins-PCPVT-Small showed slightly lower performance (F-score: 0.8847, IoU: 0.7933),  highlighting the role of model capacity and depth in transformer performance.

These findings indicate that transformer-based architectures, particularly the DPT model  with the Twins-PCPVT-Base encoder, exhibited more stable and consistent performance  on the spatially disjoint test subset compared to CNN-based models. Higher F-scores and  IoU values reflect a more balanced trade-off between recall and precision, which is particu­ larly important for accurately delineating small and overlapping objects in UAV imagery  under varying field conditions. These improvements can be attributed to the global attention  mechanisms of transformers, which enhance spatial context modeling and boundary preci­ sion under variable conditions. A direct comparison between U-Net (ResNet-50) and DPT  (Twins-PCPVT-Base) highlights nuanced differences. DPT outperformed U-Net in accu­ racy (0.9698 vs. 0.9688), F-score (0.8907 vs. 0.8876), IoU (0.8030 vs. 0.7979), and preci­ sion (0.8512 vs. 0.8446), while U-Net exhibited slightly higher recall (0.9365 vs. 0.9349).  Although these differences were small, they consistently favored the DPT model, particu­ larly in precision and IoU, key metrics for reducing false positives and improving boundary  accuracy.

To assess whether these differences were statistically significant, a paired-samples t-test  was conducted. The analysis was based on selected test image patches (n = 176), with per­ formance metrics computed per patch. The paired t-test results, summarized in Table 5,


## 1 3

56    Page 22 of 41 Precision Agriculture           (2026) 27:56

indicated that DPT significantly outperformed U-Net in IoU, accuracy, F-score, and preci­ sion, with all associated p-values below 0.001. For example, the mean difference in F-score  (− 0.0031) was statistically significant (t(175) = − 6.583, p < 0.001), supporting the conclu­ sion that DPT achieved slightly but consistently higher segmentation performance than  U-Net on the spatially disjoint test subset. Precision and accuracy also showed significant  differences (t(175) = − 7.575 and − 7.305, respectively; p < 0.001), while U-Net exhibited a  marginal but statistically significant advantage in recall (t(175) = 2.084, p = 0.039), indicat­ ing slightly higher sensitivity at the cost of precision.

In the context of sunflower capitula detection, accuracy measures and statistical test  results underscore the DPT model’s advantages in achieving precise and accurate segmen­ tation, with fewer false positives, a desirable trait in practical applications where over-seg­ mentation may reduce downstream reliability. Although the U-Net demonstrated slightly  higher recall, this came at the cost of precision. The statistical analysis supports the conclu­ sion that the DPT model with the Twins-PCPVT-Base encoder provides more consistent  and balanced performance for sunflower capitula detection, making it a strong candidate for  further evaluation in operational agricultural image analysis workflows. DPT’s performance  advantage is particularly relevant in practical applications where minimizing false positives  is critical, such as precision agriculture.

The results of this analysis are consistent with recent studies that report superior per­ formance of transformer models over CNNs in agricultural image segmentation tasks.  For instance, Tao et al. (2025) evaluated transformer-, mamba-, and CNN-based models  combining various encoder architectures to identify tobacco plants from UAV images.  They highlighted the robust performance of transformer-based models, particularly the  DPT model combined with the DINOv2 encoder, which achieved the best results among  27 evaluated architectures. Martins et al. (2024) compared FCN, SegFormer, and Deep­ Labv3 + for corn segmentation using UAV data and found that SegFormer outperformed  the CNNs, particularly at varying growth stages. Xu et al. (2023) employed Swin Trans­ former, U-Net, and DeepLabv3 to segment rice using Sentinel-2 imagery and reported the  highest accuracy and best boundary detection using Swin Transformer. In addition, Song  et al. (2023b) demonstrated that SegFormer outperformed other models, including Swin  Transformer and classical CNNs, in mapping rice and wheat with high edge precision.  Moreover, Pu et al. (2025) found that SegFormer and Mask2Former surpassed CNNs in  woody species detection, with SegFormer (MiT-B5) achieving the highest accuracy. In a  recent study, Zhou et al. (2025) showed that DPT consistently outperformed SegFormer,  SETR, and FCN-8s in road network segmentation across three benchmark remote sensing  datasets.


> **Table 5  Paired-sample T-test results comparing U-Net and DPT performance**

> Metric
Mean Difference 
(U-Net − DPT)

Std. Deviation t (df = 175) p-value 95% CI of Dif­ ference (Lower,  Upper) IoU −0.0050 0.0101 −6.597 < 0.001 [− 0.0065, − 0.0035] Accuracy −0.0010 0.0019 −7.305 < 0.001 [− 0.0013, − 0.0007] F-score −0.0031 0.0062 −6.583 < 0.001 [− 0.0040, − 0.0022] Precision −0.0067 0.0117 −7.575 < 0.001 [− 0.0084, − 0.0049] Recall + 0.0016 0.0100 + 2.084 0.039 [+ 0.0001, + 0.0031]


## 1 3

Page 23 of 41     56  Precision Agriculture           (2026) 27:56

Visual evaluation of model predictions

To visually evaluate the sunflower inflorescence segmentation results of the transformer-  and CNN-based models, the outputs of the top-performing architectures on the spatially  disjoint test subset extracted from the UAV orthomosaic were compared qualitatively, as  illustrated in Fig. 12. This visual assessment complements the quantitative evaluation by  highlighting typical success cases and failure modes under challenging conditions. Across  all models, densely populated regions with overlapping sunflower heads and the presence  of small objects remained challenging, reflecting well-known limitations of deep learning- based segmentation approaches. For example, in the region highlighted with red shapes in  image sample (d), where numerous medium-sized heads overlap, transformer-based mod­ els and U-Net-ResNet-50 were able to separate individual objects more clearly, whereas  DeepLabv3+-ResNet-50 and PSPNet-ResNet-50 tended to produce merged segmenta­ tions. On the other hand, in the highlighted regions in images (b) and (e), a small sunflower  instance adjacent to a larger one was missed by all models, resulting in false negatives. This  observation underscores the persistent difficulty of small-object detection across all evalu­ ated architectures.

In scene (a), where heads overlapped, DPT-Twins-PCPVT-Base, UPerNet-MiT-B2, and  U-Net-ResNet-50 produced segmentation outputs that closely aligned with the ground-truth  masks. In contrast, in image (c), which contained many small, densely packed sunflower  heads, the DPT-Twins-PCPVT-Base model yielded visually more consistent delineation of  individual sunflower heads and their boundaries, whereas the predictions of the other mod­ els exhibited issues such as missed detections and less precise object boundaries.

Explainable analyses of model predictions with Grad-CAM

Exploring the decision-making mechanisms of deep learning models provides deeper  insight into their predictive performance. To compare the sunflower inflorescence identifi­ cation capabilities of the DPT-Twins-PCPVT-Base and U-Net-ResNet-50 models, Gradient- weighted Class Activation Mapping (Grad-CAM) was used, as suggested by Selvaraju et  al. (2017), a widely adopted technique in explainable artificial intelligence. This method  utilizes gradient information to generate heatmaps indicating the regions within an image  that influence the model’s decision-making process.


> **Figure 13 illustrates the Grad-CAM visualizations of the model predictions using exam­**

> ples from the test subset. In these visualizations, red regions denote high-attention areas 
strongly influencing the prediction, while blue regions correspond to areas with minimal 
model attention. The color gradient from blue to red reflects increasing attention intensity. 
The analysis of Grad-CAM outputs revealed that the CNN-based model primarily focused 
on the boundaries of the sunflower inflorescences, whereas the transformer-based model 
concentrated on the central regions of the sunflower inflorescences. This indicates that the 
CNN model focused on object shape and edge features, whereas the transformer model 
concentrated on central semantic content. CNNs are known to capture local features, such 
as edges and shapes, due to their convolutional operations. In contrast, transformers process 
global context by linking each pixel to all others via self-attention mechanisms, thereby 
enabling a holistic understanding of the image. In line with these observations, the Grad-
CAM analysis suggests that the CNN-based U-Net-ResNet-50 model tends to rely more


## 1 3

56    Page 24 of 41 Precision Agriculture           (2026) 27:56

Fig. 12  Qualitative comparison of the best-performing models’ prediction results on the test subset


## 1 3

Page 25 of 41     56  Precision Agriculture           (2026) 27:56

Fig. 13  Grad-CAM visualization for DPT-Twins-PCPVT-Base and U-Net-ResNet-50 models on the test  subset

strongly on boundary-related features, whereas transformer-based models appear to place  greater emphasis on broader contextual information.

When examining Fig. 13(a), it becomes evident that the U-Net-ResNet-50 model failed  to detect one of three overlapping sunflower heads within the red-highlighted region. In  other words, since the model learned the object shape and boundaries, it could not extract  boundary information in overlapping object examples. This behavior appears to be related to  the model’s stronger reliance on boundary cues, which became ambiguous due to the over­ lap. In Fig. 13(b), the transformer model could not identify a sunflower head whose center  resembled the background, underscoring its reliance on central visual features. Similarly,  in the same image, it was noticed that both models also encountered difficulty in a region  marked by a red rectangle, where neither clear boundaries nor distinct centers were pres­ ent. Moreover, in Fig. 13(c), the U-Net-ResNet-50 model missed a small sunflower sample,  likely due to distortion caused by insufficient point density during UAV orthomosaic gen­ eration. Such imaging artifacts hindered boundary detection and led to segmentation failure.

Ablation analysis: Loss function, patch overlap, and data augmentation

To ensure a fair and interpretable comparison between CNN- and transformer-based archi­ tectures, and to assess the robustness of the main methodological choices adopted in this


## 1 3

56    Page 26 of 41 Precision Agriculture           (2026) 27:56


> **Table 6  Results of loss function analyses on the validation and test datasets**

> Dataset
Model
Loss 
Function

Accuracy F-Score IoU Precision Recall

Valida­ tion  Dataset

U-Net – ResNet-50 Dice 0.9863 0.9459 0.8975 0.9463 0.9457 BCE 0.9863 0.9457 0.8972 0.9437 0.9480 DPT  – Twins-PCPVT-Base

Dice 0.9833 0.9340 0.8763 0.9350 0.9332 BCE 0.9864 0.9459 0.8974 0.9456 0.9462 Test  Dataset

U-Net – ResNet-50 Dice 0.9688 0.8876 0.7979 0.8446 0.9365 BCE 0.9680 0.8854 0.7945 0.8382 0.9397 DPT  – Twins-PCPVT-Base

Dice 0.9693 0.8892 0.8006 0.8469 0.9370 BCE 0.9698 0.8907 0.8030 0.8512 0.9349


> **Table 7  Comparison of the impact of different patch overlap ratios on the performance of**

> DPT–Twins-PCPVT-Base
Patch Overlap
(%)

Accuracy F-Score IoU Validation Test Validation Test Validation Test 0 0.9761 0.9580 0.9097 0.8570 0.8345 0.7500 25 (64 px) 0.9811 0.9654 0.9270 0.8743 0.8640 0.7768 50 (128 px) 0.9942 0.9693 0.9782 0.8889 0.9578 0.8002

study, a set of targeted ablation experiments was conducted. These analyses focus on three  key aspects that directly influence segmentation performance and within-field robustness:  loss function selection, patch overlap ratio during dataset construction, and the use of data  augmentation. Previous studies have shown that loss function selection can substantially  influence segmentation performance, with Dice loss often preferred for imbalanced object  segmentation tasks characterized by extreme class distribution differences (Vadhera &  Sharma, 2026), while transformer-based dense prediction models typically rely on cross- entropy-based formulations (Elharrouss et al., 2025).

First, Dice and binary cross-entropy (BCE) losses were cross-applied to the best-per­ forming CNN (U-Net-ResNet-50) and transformer-based (DPT-Twins-PCPVT-Base) mod­ els to evaluate whether the observed performance hierarchy was sensitive to the choice of  objective function. The combined validation and test results are summarized in Table 6.  For the U-Net architecture, both loss functions yielded nearly identical performance, with  Dice loss providing marginally higher F-score and IoU values. In contrast, the transformer- based DPT model consistently achieved superior results with BCE loss across both datasets.  Importantly, regardless of the loss function used, the relative ranking between CNN and  transformer models remained unchanged, indicating that the observed performance differ­ ences are not primarily driven by loss function selection, but are instead consistent with  architectural characteristics.

Second, the effect of the patch overlap during dataset generation was evaluated using  overlap ratios of 0%, 25%, and 50% while keeping all other parameters fixed. As shown  in Table 7, increasing overlap led to a monotonic improvement in test performance, with  test IoU increasing from 0.75 (0% overlap) to 0.80 (50% overlap). Although higher overlap  increased training performance more strongly, the consistent gains observed on the test set  indicate that overlap enhances model robustness under within-field spatial variability by  exposing the models to a more diverse set of spatial contexts for the same objects, rather


## 1 3

Page 27 of 41     56  Precision Agriculture           (2026) 27:56

than merely inflating training accuracy. In this regard, the image tiling with a 50% overlap  approach is commonly employed by researchers in UAV-based agricultural applications  (Weng et al., 2026; Nikolova et al., 2025; Shiu et al., 2023; Hao et al., 2021). Moreover,  Wang et al. (2023) further investigated the impact of overlapping area ratio on the per­ formance of CNN models for weed mapping in UAV images and reported that increasing  overlap ratios (%0, %25, %50, %75) improved performance.

Finally, the effect of data augmentation was examined under the 50% overlap configura­ tion (Table 8). The inclusion of data augmentation led to a noticeable reduction in validation  performance, while yielding marginal improvements in test accuracy, F-score, and IoU.  This behavior is consistent with the expected regularization effect of augmentation, indicat­ ing reduced overfitting and improved generalization to spatially disjoint within-field test  data. Notably, the reduced gap between validation and test performance further supports the  stabilizing effect of augmentation. Taken together, these findings support the robustness of  the adopted training strategy and suggest that the reported results are not driven by artificial  performance inflation.

Evaluation of computational efficiency of the models

Considering the importance of computational efficiency in deploying deep learning algo­ rithms, it is essential to evaluate model accuracy and the trade-off between speed and per­ formance. This consideration is particularly relevant for real-world applications, where the  most practical model balances inference speed and predictive strength. Figure 14 compares  the training times of various transformer- and CNN-based models. The comparison of the  training durations of all models revealed that CNN-based models (i.e., U-Net, DeepLabv3+,  and PSPNet) required significantly less training time than transformer-based models. While  conventional CNNs completed training in approximately one hour, transformer-based  models required training durations of up to two hours, primarily due to their structural  complexity.

To further analyze the impact of model complexity on the performance, the number of  trainable parameters and GFLOPs (giga floating-point operations per second) for all evalu­ ated models are demonstrated in Fig. 15. A strong correlation was observed between train­ ing time, parameter count, and computational complexity (measured in GFLOPs). Notably,  the DPT-Twins-PCPVT-Base model, which exhibited the highest robustness performance  on the spatially disjoint within-field test subset, also had the longest training time and  the highest values for both parameters and GFLOPs. The SegFormer-MiT-B3 and Seg­ Former-MiT-B2 models also demonstrated strong and consistent performance under the  same evaluation setting with comparatively fewer parameters and GFLOPs. On the other  hand, CNN-based models, including PSPNet, U-Net, and DeepLabv3+ (with MobileNet- v2 encoder), offered the lowest training times and computational demands. These findings  confirm that transformer-based models impose a higher computational burden due to their  architectural complexity. However, CNN-based models remain advantageous for applica­


> **Table 8  Effect of data augmentation on the performance of DPT–Twins-PCPVT-Base**

> Augmentation
Accuracy
F-Score
IoU
Validation
Test
Validation
Test
Validation
Test
No
0.9942
0.9693
0.9782
0.8889
0.9578
0.8002
Yes
0.9864
0.9698
0.9459
0.8907
0.8974
0.8030


## 1 3

56    Page 28 of 41 Precision Agriculture           (2026) 27:56

Fig. 14  Comparison of the training time of the CNN and transformer models

Fig. 15  Number of trainable parameters (in millions) and GFLOPs of the models

tions requiring low training overhead and efficient resource usage. Ultimately, model selec­ tion should align with the constraints of the target application, hardware availability, and  performance requirements.


## 1 3

Page 29 of 41     56  Precision Agriculture           (2026) 27:56

Field-scale sunflower inflorescence mapping

Following the identification of the best-performing DL model, the resulting predictions  were integrated to generate a field-scale sunflower inflorescence map. This field-scale rep­ resentation provides a basis for examining the spatial distribution of sunflower plants and  the heterogeneity of plant development within the field. While patch-based predictions yield  reliable results at the local scale, aggregating them is essential to produce a spatially consis­ tent and interpretable map at the field level, which is essential for downstream agricultural  analysis.

For this purpose, the best-performing DPT-Twins-PCPVT-Base model was applied to  map the sunflower inflorescences across the entire UAV orthomosaic in the study area. The  generated orthomosaic was divided into 256 × 256 pixel patches with 50% overlap in both  horizontal and vertical directions, using the same configuration as during model training.  Object continuity at patch boundaries was preserved through overlapping, ensuring that  inflorescences located at patch edges were included in at least one prediction window. Each  patch was processed sequentially by the DPT model to generate a probability map. These  patch-level predictions were then merged by averaging pixel-wise probabilities in overlap­ ping regions, resulting in a continuous probability map for the entire field. The final map  was thresholded to obtain a binary mask and subsequently converted into vector format in  ArcGIS Pro to produce a field-scale sunflower inflorescence coverage map. The resulting  map, containing over 75,000 sunflower inflorescences for approximately 2.33 ha of sun­ flower fields in the study area, is shown in Fig. 16.

The experimental sunflower field (~ 2.33 ha) is a large-scale heterogeneous plot repre­ senting variability in plant spacing, inflorescence size and density, and local developmen­ tal conditions. In addition, distortions arising from insufficient point density during UAV  orthomosaic generation may affect detection performance. Sample scenarios of these het­ erogeneities are clearly shown in the image patches presented in Fig. 17. For example,  Fig. 17(a) shows a sample image from the training site, representing typical training condi­ tions characterized by high plant density, large and well-developed flower heads, and a rela­ tively homogeneous background. Figure 17(b) illustrates an area with less-developed and,  smaller sunflower heads, where reduced target size and contrast pose additional challenges,  revealing the model’s performance under these conditions. In contrast, Fig. 17(c) illustrates  variability in field plant density, representing areas with sparser plant distribution, irregular  spacing, and a more visible background. Figure 17(d) shows areas where the soil surface is  more dominant, contrast is reduced, and plant development is weaker, reflecting localized  differences in growth conditions. Figure 17(e) provides an example of image distortion;  abrupt height drops and rises between the boundary pixels of the sunflower heads and the  subsequent ground pixels cause the distorting effect of interpolation to be maximized in  the production of the DSM from the point cloud. This reduces the geometric representation  potential of the sunflower heads in the final orthomosaic. Figure 17(f) depicts a particularly  challenging scene with image blurring due to the interpolation effect and a complex back­ ground, including vegetation, weeds, and soil. Although such distortions are often excluded  in recent studies by retaining only distortion-free regions to improve detection accuracy  (Dong et al., 2025), they were intentionally retained here to enable a more realistic and  conservative evaluation of model performance. Taken together, these examples demonstrate  the high spatial and visual heterogeneity of the study area and indicate that the DPT model


## 1 3

56    Page 30 of 41 Precision Agriculture           (2026) 27:56

Fig. 16  Sunflower inflorescences map predicted with DPT-Twins-PCPVT-Base model for ~ 2.33 ha field

was evaluated under a wide range of realistic field conditions. Despite these challenges, the  model produced stable and coherent predictions across most scenarios, indicating strong  robustness under within-field spatial and visual heterogeneity. Evaluating model perfor­ mance not only in ideal conditions but also in the presence of such distortions is essential for  developing robust models suitable for operational agricultural applications.

Spatial patterns of inflorescence-derived indicators

To characterize field-scale spatial variability in sunflower inflorescence characteristics, a set  of inflorescence-derived indicators was computed and mapped at the grid level. These indi­ cators summarize complementary aspects of inflorescence abundance and size derived from  the object-based segmentation outputs described in Sect. "Object-based spatial indicators  derived from sunflower inflorescences". Figure 18 presents the field-scale spatial distribu­ tions of five inflorescence-derived indicators, reconstructed from object-based segmentation  outputs using a regular grid framework. All maps reveal pronounced intra-field variabil­ ity, indicating heterogeneous spatial patterns of sunflower inflorescences across the study  area. However, each indicator emphasizes distinct components of this variability. Previous  UAV-based studies have demonstrated the usefulness of grid-based capitulum density maps  derived solely from object counts for monitoring flowering intensity and image-observed  phenological dynamics (Jing et al., 2024). However, count-based density representations do  not explicitly capture variability in capitulum size or relative dominance, which may lead  to ambiguous interpretations in heterogeneous production fields. Unlike studies conducted  in controlled and relatively homogeneous plots (Iamchuen et al., 2026), the present study  explicitly addresses spatial heterogeneity by reconstructing full-field inflorescence maps  and introducing grid-based object-derived indicators that facilitate comparative field-scale  spatial interpretation.


## 1 3

Page 31 of 41     56  Precision Agriculture           (2026) 27:56

Fig. 17  Representative image patches illustrating field-scale heterogeneity within the experimental sun­ flower field

The IC and ICD maps exhibit similar spatial patterns, highlighting zones of high and low  inflorescence abundance, with inflorescence counts per grid cell ranging from 1 to 66. These  indicators primarily reflect variations in plant density, including missing or underdeveloped  plants, but do not explicitly capture differences in inflorescence size.


## 1 3

56    Page 32 of 41 Precision Agriculture           (2026) 27:56

Fig. 18  Spatial distribution of inflorescence-derived indicators at the grid level


## 1 3

Page 33 of 41     56  Precision Agriculture           (2026) 27:56

In contrast, the TIA and its density form TIAD emphasize spatial variations in inflores­ cence size. According to the TIA map, the cumulative inflorescence area within individual  grid cells reaches up to 2.66 m², while TIAD indicates that sunflower inflorescences may  occupy approximately 21% of the grid area in areas characterized by larger predicted inflo­ rescences. These patterns reveal regions where a limited number of large inflorescences  dominate the spatial signal, as well as areas where high inflorescence counts correspond  to relatively small cumulative areas. While TIA and TIAD effectively highlight size-dom­ inated regions, their spatial response remains susceptible to skewing by extreme inflores­ cence sizes.

This sensitivity motivates the introduction of WHAI as a composite indicator that jointly  accounts for both inflorescence abundance and size. By integrating information on both  inflorescence density and relative area, WHAI provides a more coherent spatial representa­ tion of reproductive development than indicators based on a single component. Compared  with IC/ICD and TIA/TIAD, WHAI reduces the dominance of extreme values and high­ lights transitional zones where inflorescence number and size exhibit contrasting behavior.

Whereas IC/ICD primarily reflects numerical abundance and TIA/TIAD emphasizes  cumulative size effects, WHAI captures their combined spatial response. High WHAI val­ ues are associated with grid cells characterized by dense and/or relatively large inflores­ cences, while low values indicate sparse or smaller inflorescences. Consequently, WHAI  offers an integrated perspective on within-field variability in inflorescence characteristics,  serving as a relative, image-derived spatial descriptor and not as a direct proxy for yield or  agronomic performance.

To further clarify the complementary behavior of the proposed inflorescence-derived  indicators and to illustrate the added value of WHAI, three representative grid cells were  selected as examples and analyzed in detail (Fig. 19). These examples were chosen to rep­ resent contrasting combinations of inflorescence abundance and cumulative area, resulting  in distinct WHAI responses. Figure 19 presents, for each selected grid cell, the original  RGB image along with the corresponding inflorescence masks and centroid distributions,  enabling visual inspection of both the number of inflorescences and their spatial extent. Key  indicator values are directly annotated on the figure to support quantitative interpretation.

In the first example, the Grid-A contains a moderate number of inflorescences, yet their  cumulative area remains limited. Although inflorescence count alone suggests a relatively  dense inflorescence configuration, the detected inflorescences are predominantly small,  resulting in a low total inflorescence area and, consequently, a reduced WHAI value. This  comparison demonstrates that grids with similar inflorescence counts may represent sub­ stantially different inflorescence size-abundance configurations once inflorescence size is  taken into account.

In the second example, the Grid-B exhibits a similar inflorescence count to the first  example; however, the cumulative inflorescence area is noticeably smaller, indicating a  higher proportion of smaller detected inflorescences. Despite comparable inflorescence  abundance, the reduced total inflorescence area results in a lower WHAI value. This con­ trast demonstrates that inflorescence count alone is insufficient to characterize within-field  spatial variability in inflorescence characteristics, as grids with similar counts may represent  substantially different image-derived configurations when inflorescence size is considered.

In the third example, Grid-C, both inflorescence abundance and cumulative inflorescence  area are substantially higher. The grid is characterized by a dense distribution of relatively


## 1 3

56    Page 34 of 41 Precision Agriculture           (2026) 27:56

Fig. 19  Visual comparison of representative grid cells with different WHAI values, illustrating the  complementary and conflicting behavior of count-based and area-based inflorescence indicators and the  resulting WHAI response. For each grid cell, the RGB image, inflorescence segmentation results, and  centroid distributions are shown

large inflorescences, leading to an elevated total inflorescence area and, consequently, a  higher WHAI value. This example visually and quantitatively represents zones where inflo­ rescence number and size jointly indicate producing elevated WHAI responses.

Across these examples, IC emphasizes numerical abundance, while TIA highlights cumu­ lative size effects. However, neither indicator alone consistently distinguishes grid cells, as  inflorescence number and size exhibit conflicting or complementary behavior. In contrast,  WHAI integrates both components through weighted aggregation, providing a more bal­ anced spatial indicator of inflorescence-derived variability. This capability is particularly  relevant for comparative agricultural analysis, where the identification of zones with con­ trasting image-derived spatial patterns may not be apparent when using only count-based or  area-based indicators. These example-based observations reinforce the field-scale patterns  identified in the general indicator maps (Fig. 18) and demonstrate how WHAI supports spa­ tially explicit interpretation of DL-derived inflorescence detection results within a precision


## 1 3

Page 35 of 41     56  Precision Agriculture           (2026) 27:56

Fig. 20  Structural and inflorescence-derived spatial representations at the grid level used for interpreta­ tive comparison. (a) UAV RGB–derived nDSM at 5 cm spatial resolution, (b) grid-based aggregation of  canopy height (Inflorescence Height Density), and (c) WHAI, illustrating the balanced response of WHAI  relative to structural height variability

agriculture framework, where spatially explicit and interpretable indicators are essential for  targeted field management.

To provide additional structural context, without implying direct validation or biophysi­ cal equivalence, an nDSM derived from UAV RGB imagery was analyzed using the same  grid framework (Fig. 20). The original high-resolution nDSM captures fine-scale height  variability across the field, while the grid-aggregated representation highlights dominant  structural trends at a management-relevant scale.

A broad spatial consistency can be observed between zones of elevated canopy height  and areas characterized by higher WHAI values. However, the correspondence is not one- to-one. Several grid cells exhibiting relatively high nDSM values display moderate WHAI  responses, whereas some areas with moderate structural height are associated with higher  WHAI values. This divergence reflects the fact that WHAI integrates both inflorescence


## 1 3

56    Page 36 of 41 Precision Agriculture           (2026) 27:56

abundance and relative size, rather than merely serving as a proxy for canopy height or bio­ mass. This observation suggests that canopy structure alone is insufficient to fully explain  inflorescence-related spatial variability, particularly when extrapolating from relatively  homogeneous experimental plots to heterogeneous production fields.

Compared to the grid-based height representation, WHAI provides a more balanced  spatial depiction of inflorescence-derived spatial variability by reducing the dominance  of extreme structural values and highlighting zones where inflorescence number and size  jointly contribute to spatial variability. In this sense, the nDSM-based analysis does not vali­ date WHAI, but instead provides complementary structural context that supports the spatial  interpretability of the proposed indicator.

Limitations and future work

Despite the strong segmentation performance and the consistent spatial patterns observed  across models and inflorescence-derived indicators, several limitations of the present study  should be acknowledged, which also point to relevant directions for future research. First,  the analysis is based on UAV RGB imagery acquired over a single production field within a  limited phenological window of sunflower development. Although substantial within-field  spatial heterogeneity is addressed, the study does not evaluate model transferability across  different sites, seasons, or environmental conditions. Extending the proposed framework to  multiple fields and diverse management scenarios remains a necessary step toward assess­ ing its broader robustness. Second, reliance on RGB imagery alone imposes constraints  related to illumination variability, shadow effects, and the absence of spectral information  beyond the visible range. While this choice reflects a practical and widely accessible UAV  configuration, future work could investigate the integration of multispectral, hyperspectral,  or 3D structural data to enhance target discrimination in dense or partially occluded canopy  environments. Third, inflorescence annotation is subject to boundary ambiguity, particu­ larly in areas with overlapping or irregularly shaped inflorescences. Such ambiguities may  introduce uncertainty into pixel-level segmentation metrics and downstream object-derived  indicators. Exploring semi-automatic or uncertainty-aware annotation strategies could help  reduce subjectivity in ground-truth generation.

With respect to the proposed inflorescence-derived indicators, including WHAI, the cur­ rent implementation relies on a fixed grid resolution and predefined weighting schemes.  Although these choices enable consistent field-scale comparisons, indicator behavior may  vary as a function of grid size or normalization strategy. Consequently, sensitivity analyses  and adaptive, scale-aware formulations represent important avenues for future research to  optimize indicator performance across different crop geometries.

Finally, while inflorescence-derived indicators provide spatially interpretable representa­ tions of inflorescence-related variability, no direct linkage to yield or other biophysical vari­ ables is implied. The present work establishes the spatial framework; however, establishing  quantitative relationships with yield or other biophysical variables through multi-year field  measurements and complementary data sources is required to fully realize the agronomic  relevance of the proposed framework for predictive applications. However, the absence of  harvest yield data for the study field limits the ability to directly evaluate the relationship  between the proposed indicators and yield variability.


## 1 3

Page 37 of 41     56  Precision Agriculture           (2026) 27:56


## Conclusions

In this study, the performance and robustness of six state-of-the-art transformer- and CNN- based semantic segmentation models were systematically evaluated for sunflower inflo­ rescence identification using high-resolution UAV RGB imagery. A total of fifteen model  configurations with different encoder backbones were assessed within a controlled experi­ mental framework designed to capture realistic within-field spatial heterogeneity. Beyond  conventional accuracy benchmarking, the analysis included spatially disjoint testing, abla­ tion experiments, and interpretability assessment. It also demonstrated how object-based  segmentation outputs can be translated into spatially interpretable, field-scale indicators.

Across all experiments, transformer-based architectures exhibited consistently strong  segmentation performance and more stable behavior under within-field spatial variability  compared to CNN-based models. Among the evaluated configurations, the DPT model with  the Twins-PCPVT-Base backbone achieved the most balanced performance, particularly in  terms of precision and IoU, while maintaining comparable recall. Interpretability analysis  further indicated that CNN-based models predominantly relied on localized, boundary-ori­ ented features, whereas the transformer-based model leveraged broader contextual informa­ tion through global attention mechanisms. These differences in attention behaviour provide  a plausible explanation for the improved robustness of transformer-based models in hetero­ geneous agricultural scenes, albeit at the cost of increased computational complexity.

Beyond model-level evaluation, the study demonstrated the reconstruction of field-scale  spatial patterns using object-based, inflorescence-derived indicators. While count-based and  area-based metrics captured complementary aspects of inflorescence abundance and size,  the proposed WHAI provided a more balanced spatial representation by integrating both  components and reducing sensitivity to extreme values. Taken together, the results indicate  that combining transformer-based segmentation with object-level spatial aggregation pro­ vides a consistent and image-derived, interpretable framework for characterizing within- field variability in sunflower inflorescence patterns from UAV RGB imagery.

Supplementary Information  The online version contains supplementary material available at ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​ /​1​0​.​1​0​0​7​/​s​1​1​1​1​9​-​0​2​6​-​1​0​3​6​2​-​5​.​

Acknowledgements  This research was conducted as part of the thesis study by Esra Yildirim to meet the  requirements of a doctoral degree in the Department of Geomatics Engineering at Gebze Technical Univer­ sity. Author Esra Yildirim would like to express her gratitude to TÜBİTAK for its generous support within  the scope of the 2211/A Domestic General Doctorate Scholarship Program. Special thanks to the Republic  of Türkiye Ministry of Agriculture and Forestry, Maize Research Institute, for their valuable contributions  to the study.

Authors contribution  All authors contributed to the study’s conception and design. Esra Yildirim: Concep­ tualization, Data curation, Methodology, Investigation, Supervision, Validation, Software implementation,  writing-original draft; Ismail Colkesen: Conceptualization, Data curation, Methodology, Investigation,  Supervision, Validation, writing-original draft; Umut Gunes Sefercik: Conceptualization, Data curation,  Investigation, Validation, Software implementation, Visualization, writing-original draft; All authors read  and approved the final manuscript.

Funding  Open access funding provided by the Scientific and Technological Research Council of Türkiye  (TÜBİTAK).

Data availability  The data that support the findings of this study are available from the corresponding author  upon reasonable request.


## 1 3

56    Page 38 of 41 Precision Agriculture           (2026) 27:56

Declarations

Competing interests  No potential conflict of interest.

Open Access  This article is licensed under a Creative Commons Attribution 4.0 International License,  which permits use, sharing, adaptation, distribution and reproduction in any medium or format, as long as  you give appropriate credit to the original author(s) and the source, provide a link to the Creative Commons  licence, and indicate if changes were made. The images or other third party material in this article are  included in the article’s Creative Commons licence, unless indicated otherwise in a credit line to the material.  If material is not included in the article’s Creative Commons licence and your intended use is not permitted  by statutory regulation or exceeds the permitted use, you will need to obtain permission directly from the  copyright holder. To view a copy of this licence, visit http://creativecommons.org/licenses/by/4.0/.


## References

Bai, Y., Nie, C., Wang, H., Cheng, M., Liu, S., Yu, X., Shao, M., Wang, Z., Wang, S., Tuohuti, N., Shi, L.,

Ming, B., & Jin, X. (2022). A fast and robust method for plant count in sunflower and maize at different  seedling stages using high-resolution UAV RGB imagery. Precision Agriculture, 23(5), 1720–1742.  https://doi.org/10.1007/s11119-022-09907-1 Bolcek, J., Gibril, M. B. A., Al-Ruzouq, R., Shanableh, A., Jena, R., Hammouri, N., Sachit, M. S., & Ghor­

banzadeh, O. (2025). A comprehensive evaluation of deep vision transformers for road extraction from  very-high-resolution satellite data. Science of Remote Sensing, 11, 100190. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​1​0​1​6​/​j​.​s​r​ s​.​2​0​2​4​.​1​0​0​1​9​0​ Chen, L. C., Papandreou, G., Kokkinos, I., Murphy, K., & Yuille, A. L. (2014). Semantic image segmentation

with deep convolutional nets, and fully connected CRFs. arXiv preprint arXiv, 14127062. ​h​t​t​p​s​:​/​/​d​o​i​.​o​ r​g​/​1​0​.​4​8​5​5​0​/​a​r​X​i​v​.​1​4​1​2​.​7​0​6​2​ Chen, L. C., Papandreou, G., Kokkinos, I., Murphy, K., & Yuille, A. L. (2016). DeepLab: Semantic image

segmentation with deep convolutional nets, atrous convolution, and fully connected CRFs. arXiv pre­ print. https://doi.org/10.48550/arXiv.1606.00915. arXiv:1606.00915. Chen, L. C., Papandreou, G., Schroff, F., & Adam, H. (2017). Rethinking atrous convolution for semantic

image segmentation. arXiv preprint. https://doi.org/10.48550/arXiv.1706.05587. arXiv:1706.05587. Chen, L. C., Zhu, Y., Papandreou, G., Schroff, F., & Adam, H. (2018). Encoder-decoder with atrous separable

convolution for semantic image segmentation. arXiv preprint. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​4​8​5​5​0​/​a​r​X​i​v​.​1​8​0​2​.​0​2​ 6​1​1​. arXiv:1802.02611. Cheng, E., Zhang, B., Peng, D., Zhong, L., Yu, L., Liu, Y., Xiao, C., Li, C., Li, X., Chen, Y., Ye, H., Wang, H.,

Yu, R., Hu, J., & Yang, S. (2022). Wheat yield estimation using remote sensing data based on machine  learning approaches. Frontiers in Plant Science, 13, 1090970. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​3​3​8​9​/​f​p​l​s​.​2​0​2​2​.​1​0​9​0​ 9​7​0​ Dong, Y., Zhang, Y., Du, X., Wang, H., Li, Q., Shen, Y., Gong, S., Yan, S., Hu, H., Xiao, J., Xu, J., Zhang, Z.,

Hu, J., & Zhao, Y. (2025). Field-scale single-plant sunflower head detection and geometric parameters  measurement integrating multi-modal UAV data, deep learning and point cloud analysis. Industrial  Crops and Products, 237, 122225. https://doi​.org/10.101​6/j.indcrop​.2025.12​2225 Elharrouss, O., Mahmood, Y., Bechqito, Y., Serhani, M. A., Badidi, E., Riffi, J., & Tairi, H. (2025). Loss

functions in deep learning: A comprehensive review. arXiv preprint arXiv, 250404242. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​ 1​0​.​4​8​5​5​0​/​a​r​X​i​v​.​2​5​0​4​.​0​4​2​4​2​ FAO (2023). Agricultural production statistics 2000–2022. FAOSTAT Analytical Briefs, No. 79. Rome.

https://doi.org/10.4060/cc9205en Garibaldi-Márquez, F., Martínez-Barba, D. A., Montañez-Franco, L. E., Flores, G., & Valentín-Coronado, L.

M. (2025). Enhancing site-specific weed detection using deep learning transformer architectures. Crop  Protection, 190, 107075. https://doi.org/10.1016/j.cropro.2024.107075 Gibril, M. B. A., Shafri, H. Z. M., Shanableh, A., Al-Ruzouq, R., Wayayok, A., & Hashim, S. J. (2021). Deep

convolutional neural network for large-scale date palm tree mapping from UAV-based images. Remote  Sensing, 13(14), 2787. https://doi.org/10.3390/rs13142787 Gibril, M. B. A., Shafri, H. Z. M., Al-Ruzouq, R., Shanableh, A., Nahas, F., & Mansoori, A., S (2023). Large-

scale date palm tree segmentation from multiscale UAV-based and aerial images using deep vision  transformers. Drones, 7(2), 93. https://doi.org/10.3390/drones7020093


## 1 3

Page 39 of 41     56  Precision Agriculture           (2026) 27:56

Guo, Z., Cai, D., Jin, Z., Xu, T., & Yu, F. (2025). Research on unmanned aerial vehicle (UAV) rice field weed

sensing image segmentation method based on CNN-transformer. Computers and Electronics in Agricul­ ture, 229, 109719. https://doi.org/10.1016/j.compag.2024.109719 Hao, Z., Lin, L., Post, C. J., Mikhailova, E. A., Li, M., Chen, Y., Yu, K., & Liu, J. (2021). Automated tree-

crown and height detection in a young forest plantation using Mask Region-Based Convolutional Neu­ ral Network (Mask R-CNN). ISPRS Journal of Photogrammetry and Remote Sensing, 178, 112–123.  https://doi​.org/10.101​6/j.isprsjp​rs.2021.​06.003 Iakubovskii, P. (2019). Segmentation Models Pytorch. GitHub Repository Available at: ​h​t​t​p​s​:​/​/​g​i​t​h​u​b​.​c​o​m​/​q​

u​b​v​e​l​/​s​e​g​m​e​n​t​a​t​i​o​n​_​m​o​d​e​l​s​.​p​y​t​o​r​c​h​ Iamchuen, N., Hongpradit, P., Puttinaovarat, S., & Anucharn, T. (2026). Automated sunflower head detec­

tion and yield estimation from high-resolution UAV imagery using YOLOv11 for precision agriculture.  Sustainability, 18(2), 1026. https://doi.org/10.3390/su18021026 Islam, M. A., Jia, S., & Bruce, N. D. (2020). How much position information do convolutional neural net­

works encode? arXiv preprint arXiv:2001.08248. https://doi.org/10.48550/arXiv.2001.08248 Japkowicz, N., & Shah, M. (2011). Evaluating learning algorithms. Cambridge University Press. Jia, Y., Fu, K., Lan, H., Wang, X., & Su, Z. (2024). Maize tassel detection with CA-YOLO for UAV images

in complex field environments. Computers and Electronics in Agriculture, 217, 108562. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​ /​1​0​.​1​0​1​6​/​j​.​c​o​m​p​a​g​.​2​0​2​3​.​1​0​8​5​6​2​ Jiang, Y., Liu, W., Wu, C., & Yao, H. (2021). Multi-scale and multi-branch convolutional neural network for

retinal image segmentation. Symmetry, 13(3), 365. https://doi.org/10.3390/sym13030365 Jing, R., Niu, Q., Tian, Y., Zhang, H., Zhao, Q., Li, Z., Zhou, X., & Li, D. (2024). Sunflower-YOLO: Detec­

tion of sunflower capitula in UAV remote sensing images. European Journal of Agronomy, 160, 127332.  https://doi.org/10.1016/j.eja.2024.127332 Kingma, D. P. (2014). Adam: A method for stochastic optimization. arXiv preprint. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​4​8​5​5​0​

/​a​r​X​i​v​.​1​4​1​2​.​6​9​8​0​. arXiv:1412.6980. Li, J., Li, Y., Qiao, J., Li, L., Wang, X., Yao, J., & Liao, G. (2023). Automatic counting of rapeseed inflores­

cences using deep learning method and UAV RGB imagery. Frontiers in Plant Science, 14, 1101143.  https://doi.org/10.3389/fpls.2023.1101143 Lin, T. Y., Dollár, P., Girshick, R., He, K., Hariharan, B., Belongie, S. Feature pyramid networks for object

detection. Proceedings of the IEEE Conference on Computer Vision and, & Recognition, P. (2017).  Honolulu, HI, USA, 21–26 July, 2117–2125. https://doi.org/10.1109/CVPR.2017.106 Lin, J., Zhang, X., Qin, Y., Yang, S., Wen, X., Cernava, T., & Chen, X. (2025). FG-UNet: fine‐grained feature‐

guided UNet for segmentation of weeds and crops in UAV images. Pest Management Science, 81(2),  856–866. https://doi.org/10.1002/ps.8489 Liu, X., Wu, X., Peng, Y., Mo, J., Fang, S., Gong, Y., Zhu, R., Wang, J., & Zhang, C. (2023). Application of

UAV-retrieved canopy spectra for remote evaluation of rice full heading date. Science of Remote Sens­ ing, 7, 100090. https://doi.org/10.1016/j.srs.2023.100090 Luoni, S. A. B., Ricci, R., Corzo, M. A., Hoxha, G., Melgani, F., & Fernandez, P. (2024). Sunpheno: A deep

neural network for phenological classification of sunflower images. Plants, 13(14), 1998. ​h​t​t​p​s​:​/​/​d​o​i​.​o​ r​g​/​1​0​.​3​3​9​0​/​p​l​a​n​t​s​1​3​1​4​1​9​9​8​ Machidon, A. L., Krašovec, A., Pejović, V., & Machidon, O. M. (2025). SqueezeSlimU-Net: An adaptive and

efficient segmentation architecture for real-time UAV weed detection. IEEE Journal of Selected Topics  in Applied Earth Observations and Remote Sensing, 18, 5749–5794. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​1​1​0​9​/​J​S​T​A​R​S​.​ 2​0​2​5​.​3​5​3​6​1​7​5​ Martins, J. A. C., Higuti, A. Y. H., Pellegrin, A. O., Juliano, R. S., de Araújo, A. M., Pellegrin, L. A., Liesen­

berg, V., Ramos, A. P. M., Gonçalves, W. N., Sant’Ana, D. A., Pistori, H., & Junior, J. M. (2024).  Assessment of UAV-based deep learning for corn crop analysis in Midwest Brazil. Agriculture, 14(11),  2029. https://doi.org/10.3390/agriculture14112029 Maxwell, A. E., Warner, T. A., & Guillén, L. A. (2021a). Accuracy assessment in convolutional neural net­

work-based deep learning remote sensing studies—Part 1: Literature review. Remote Sensing, 13(13),  2450. https://doi.org/10.3390/rs13132450 Maxwell, A. E., Warner, T. A., & Guillén, L. A. (2021b). Accuracy assessment in convolutional neural

network-based deep learning remote sensing studies—Part 2: Recommendations and best practices.  Remote Sensing, 13(13), 2591. https://doi.org/10.3390/rs13132591 Narin, O. G., & Abdikan, S. (2022). Monitoring of phenological stage and yield estimation of sunflower plant

using Sentinel-2 satellite images. Geocarto International, 37(5), 1378–1392. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​1​0​8​0​/​1​ 0​1​0​6​0​4​9​.​2​0​2​0​.​1​7​6​5​8​8​6​ Nikolova, P. D., Evstatiev, B. I., Atanasov, A. Z., & Atanasov, A. I. (2025). Evaluation of weed infestations

in row crops using aerial RGB imaging and deep learning. Agriculture, 15(4), 418. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​3​ 3​9​0​/​a​g​r​i​c​u​l​t​u​r​e​1​5​0​4​0​4​1​8​


## 1 3

56    Page 40 of 41 Precision Agriculture           (2026) 27:56

Niu, B., Feng, Q., Chen, B., Ou, C., Liu, Y., & Yang, J. (2022). HSI-TransUNet: A transformer based semantic

segmentation model for crop mapping from UAV hyperspectral imagery. Computers and Electronics in  Agriculture, 201, 107297. https://doi.org/10.1016/j.compag.2022.107297 Pérez-Ortiz, M., Peña, J. M., Gutiérrez, P. A., Torres-Sánchez, J., Hervás-Martínez, C., & López-Granados, F.

(2015). A semi-supervised system for weed mapping in sunflower crops using unmanned aerial vehicles  and a crop row detection method. Applied Soft Computing, 37, 533–544. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​1​0​1​6​/​j​.​a​s​o​ c​.​2​0​1​5​.​0​8​.​0​2​7​ Pu, Y., Lu, X., Soubry, I., & Guo, X. (2025). Early detection of woody plant expansion in Canadian prairie

based on drone imagery and deep learning. Available at SSRN: https://doi.org/10.2139/ssrn.5217080 Ranftl, R., Bochkovskiy, A., & Koltun, V. (2021). Vision transformers for dense prediction. Proceedings of

the IEEE/CVF International Conference on Computer Vision, Montreal, QC, Canada, 10–17 October,  12179–12188. https://doi.org/10.1109/ICCV48922.2021.01196 Ronneberger, O., Fischer, P., & Brox, T. (2015). U-Net: Convolutional networks for biomedical image seg­

mentation. In Medical image computing and computer-assisted intervention–MICCAI 2015: 18th inter­ national conference, Munich, Germany, October 5–9, 2015, proceedings, part III 18 (pp. 234–241).  Springer International Publishing. https://doi.org/10.1007/978-3-319-24574-4_28 Schneiter, A. A., & Miller, J. F. (1981). Description of sunflower growth stages. Crop Science, 21(6), 901–903. Selvaraju, R. R., Cogswell, M., Das, A., Vedantam, R., Parikh, D., & Batra, D. (2017). Grad-CAM: Visual

explanations from deep networks via gradient-based localization. Proceedings of the IEEE International  Conference on Computer Vision, Venice, Italy, 22–29 October, 618–626. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​1​1​0​9​/​I​C​C​ V​.​2​0​1​7​.​7​4​ Shiu, Y. S., Lee, R. Y., & Chang, Y. C. (2023). Pineapples’ detection and segmentation based on Faster and

Mask R-CNN in UAV imagery. Remote Sensing, 15(3), 814. https://doi.org/10.3390/rs15030814 Song, Z., Wang, P., Zhang, Z., Yang, S., & Ning, J. (2023a). Recognition of sunflower growth period based

on deep learning from UAV remote sensing images. Precision Agriculture, 24(4), 1417–1438. ​h​t​t​p​s​:​/​/​d​ o​i​.​o​r​g​/​1​0​.​1​0​0​7​/​s​1​1​1​1​9​-​0​2​3​-​0​9​9​9​6​-​6​ Song, W., Feng, A., Wang, G., Zhang, Q., Dai, W., Wei, X., Hu, Y., Amankwah, S. O. Y., Zhou, F., & Liu, Y.

(2023b). Bi-objective crop mapping from Sentinel-2 images based on multiple deep learning networks.  Remote Sensing, 15(13), 3417. https://doi.org/10.3390/rs15133417 Soriano-González, J., Angelats, E., Martínez-Eixarch, M., & Alcaraz, C. (2022). Monitoring rice crop and

yield estimation with Sentinel-2 data. Field Crops Research, 281, 108507. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​1​0​1​6​/​j​.​f​c​ r​.​2​0​2​2​.​1​0​8​5​0​7​ Tao, J., Qiao, Q., Song, J., Sun, S., Chen, Y., Wu, Q., Liu, Y., Xue, F., Wu, H., & Zhao, F. (2025). Deep learn­

ing-driven automatic segmentation of weeds and crops in UAV imagery. Sensors (Basel, Switzerland),  25(21), 6576. https://doi.org/10.3390/s25216576 Thisanke, H., Deshan, C., Chamith, K., Seneviratne, S., Vidanaarachchi, R., & Herath, D. (2023). Semantic

segmentation using Vision Transformers: A survey. Engineering Applications of Artificial Intelligence,  126, 106669. https://doi​.org/10.101​6/j.engappa​i.2023.1​06669 Tran, L. A., Lee, J., & Hong, S. K. (2025). Improved U-Net with identity transformer encoder for efficient

UAV semantic segmentation. Ieee Access : Practical Innovations, Open Solutions, 13, 208962–208972.  https://doi.org/10.1109/ACCESS.2025.3638695 TUIK (2024). Central Dissemination System. https://biruni.tuik.gov.tr/medas/?locale=tr Vadhera, R., & Sharma, M. (2026). A comparative study of loss functions for pulmonary embolism segmen­

tation. International Journal of Information Technology. https://doi.org/10.1007/s41870-025-03028-4 Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I.

(2017). Attention is all you need. Proceedings of the 31st International Conference on Neural Informa­ tion Processing Systems (NeurIPS 2017), Long Beach, California, 4–9 December, 5998–6008. Vega, F. A., Ramirez, F. C., Saiz, M. P., & Rosua, F. O. (2015). Multi-temporal imaging using an unmanned

aerial vehicle for monitoring a sunflower crop. Biosystems Engineering, 132, 19–27. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​ .​1​0​1​6​/​j​.​b​i​o​s​y​s​t​e​m​s​e​n​g​.​2​0​1​5​.​0​1​.​0​0​8​ Volpato, L., Tirado Tolosa, S., Potnuru, C., Jaacks, J., & Layton, J. (2025). Remote phenotyping strategies

for sunflower flowering assessments using deep learning approaches. bioRxiv, 2025-04. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​ /​1​0​.​1​1​0​1​/​2​0​2​5​.​0​4​.​0​3​.​6​4​6​6​6​4​ Wang, W., Xie, E., Li, X., Fan, D. P., Song, K., Liang, D., Lu, T., Luo, P., & Shao, L. (2021). Pyramid

vision transformer: A versatile backbone for dense prediction without convolutions. Proceedings of the  IEEE/CVF International Conference on Computer Vision (ICCV), Montreal, Canada, 10–17 October,  568–578. https://doi.org/10.1109/ICCV48922.2021.00061 Wang, Y., Ha, T., Aldridge, K., Duddu, H., Shirtliffe, S., & Stavness, I. (2023). Weed mapping with convo­

lutional neural networks on high resolution whole-field images. Proceedings of the IEEE/CVF Inter­ national Conference on Computer Vision Workshops (ICCVW), Paris, France, 2–6 October, 505–514.  https://doi​.org/10.110​9/ICCVW6079​3.2023.0​0057


## 1 3

Page 41 of 41     56  Precision Agriculture           (2026) 27:56

Weng, H., Luo, H., Su, L., Zhang, B., Sun, D., Jia, L., & Ye, D. (2026). Time-series UAV multispectral imag­

ing for HLB detection via improved U-Net under dynamic orchard environment. Journal of Agriculture  and Food Research, 102643. https://doi.org/10.1016/j.jafr.2026.102643 Westoby, M. J., Brasington, J., Glasser, N. F., Hambrey, M. J., & Reynolds, J. M. (2012). Structure-from-

Motion’photogrammetry: A low-cost, effective tool for geoscience applications. Geomorphology, 179,  300–314. https://doi​.org/10.101​6/j.geomorp​h.2012.0​8.021 Xiao, T., Liu, Y., Zhou, B., Jiang, Y., & Sun, J. (2018). Unified perceptual parsing for scene understand­

ing. Proceedings of the European Conference on Computer Vision (ECCV), Munich, 8–14 September,  418–434. Xie, E., Wang, W., Yu, Z., Anandkumar, A., Alvarez, J. M., & Luo, P. (2021). SegFormer: Simple and effi­

cient design for semantic segmentation with transformers. Advances in Neural Information Processing  Systems, 34, 12077–12090. Xu, H., Song, J., & Zhu, Y. (2023). Evaluation and comparison of semantic segmentation networks for rice

identification based on Sentinel-2 imagery. Remote Sensing, 15(6), 1499. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​3​3​9​0​/​r​s​1​5​ 0​6​1​4​9​9​ Xu, X., Gao, Y., Fu, C., Qiu, J., & Zhang, W. (2024). Research on the corn stover image segmentation method

via an unmanned aerial vehicle (UAV) and improved U-Net network. Agriculture, 14(2), 217. ​h​t​t​p​s​:​/​/​d​ o​i​.​o​r​g​/​1​0​.​3​3​9​0​/​a​g​r​i​c​u​l​t​u​r​e​1​4​0​2​0​2​1​7​ Yildirim, E., Colkesen, I., & Sefercik, U. G. (2024). Identification of sunflowers (Helianthus annuus L.)

from multi-temporal UAV orthomosaics using deep learning models. Proceedings of the 9th Advanced  Engineering Days, Tabriz, Iran, 9–10 July, 782–785. Yildirim, E., Colkesen, I., & Sefercik, U. G. (2025). Transformer-based sunflower (Helianthus annuus L.)

recognition from multi-temporal UAV orthomosaics. International Archives of the Photogrammetry  Remote Sensing and Spatial Information Sciences, XLVIII-M-6-2025, 309–315. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​5​1​9​4​ /​i​s​p​r​s​-​a​r​c​h​i​v​e​s​-​X​L​V​I​I​I​-​M​-​6​-​2​0​2​5​-​3​0​9​-​2​0​2​5​ Zang, Y., Chen, X., Chen, J., Tian, Y., Shi, Y., Cao, X., & Cui, X. (2020). Remote sensing index for mapping

canola flowers using MODIS data. Remote Sensing, 12(23), 3912. https://doi.org/10.3390/rs12233912 Zhao, H., Shi, J., Qi, X., Wang, X., & Jia, J. (2017). Pyramid scene parsing network. Proceedings of the IEEE

Conference on Computer Vision and Pattern Recognition (CVPR), Honolulu, HI, USA, 21–26 July,  6230–6239. https://doi.org/10.1109/CVPR.2017.660 Zhou, Q., Huang, Z., Zheng, S., Jiao, L., Wang, L., & Wang, R. (2022). A wheat spike detection method based

on Transformer. Frontiers in Plant Science, 13, 1023924. https://doi.org/10.3389/fpls.2022.1023924 Zhou, H., He, H., Xu, L., Ma, L., Zhang, D., Chen, N., Chapman, M. A., & Li, J. (2025). A comparative study

of deep learning methods for automated road network extraction from high-spatial-resolution remotely  sensed imagery. Photogrammetric Engineering & Remote Sensing, 91(3), 163–174. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​ 1​4​3​5​8​/​P​E​R​S​.​2​4​-​0​0​1​0​0​R​2​ Zou, K., Chen, X., Zhang, F., Zhou, H., & Zhang, C. (2021). A field weed density evaluation method based

on UAV imaging and modified U-Net. Remote Sensing, 13(2), 310. https://doi.org/10.3390/rs13020310

Publisher’s note  Springer Nature remains neutral with regard to jurisdictional claims in published maps and  institutional affiliations.

Authors and Affiliations

Esra Yildirim1  · Ismail Colkesen1  · Umut Gunes Sefercik1

Ismail Colkesen

icolkesen@gtu.edu.tr

Esra Yildirim esrayildirim@gtu.edu.tr

Umut Gunes Sefercik sefercik@gtu.edu.tr

1	 Department of Geomatics Engineering, Gebze Technical University, Gebze-Kocaeli  41400, Turkey


## 1 3
