---
workspace_id: SCI-000083
doi: 10.3390/s26102997
title: A U-Net Improved Version for Crop and Weed Segmentation from Aerial Images
authors:
- family_name: Bunica-Mihai
  given_name: Alexandru
  orcid: https://orcid.org/0009-0004-7948-0330
- family_name: Popescu
  given_name: Dan
  orcid: https://orcid.org/0000-0002-1883-0091
- family_name: Ichim
  given_name: Loretta
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:35:04.971098+00:00'
---

# A U-Net Improved Version for Crop and Weed Segmentation from Aerial Images

Article A U-Net Improved Version for Crop and Weed Segmentation

from Aerial Images

Alexandru Bunica-Mihai , Dan Popescu * and Loretta Ichim

Faculty of Automatic Control and Computers, National University of Science and Technology POLITEHNICA Bucharest, 060042 Bucharest, Romania; alexandru.bunica@stud.acs.upb.ro (A.B.-M.); loretta.ichim@upb.ro (L.I.) * Correspondence: dan.popescu@upb.ro; Tel.: +40-766218363


## Abstract

The optimization of herbicide application is one of the most important topics in Precision Agriculture, driven by both economic efficiency and ecological sustainability. Excessive herbicide use can lead to soil degradation, water contamination, and negative impacts on biodiversity, while also contributing to human health risks and climate-related con- cerns. Developing accurate, automated approaches for distinguishing crops from weeds is therefore essential to support sustainable agricultural practices. In this paper, a novel architecture for crops and weed segmentation in tobacco plantations is proposed: a U-Net variant which incorporates several specific design elements, including deep supervision, a Vegetation Global Context block, and a dual-headed output that separately predicts vegetation and crop masks. Weed regions are derived as the difference between vegetation and crop predictions, allowing the model to enforce logical consistency directly within a single framework, in contrast to other two-step approaches. The proposed architecture was evaluated using multiple modern encoder backbones (ConvNextV2, FastViT, RepViT, MambaVision). Experimental results demonstrate that this architecture not only improves segmentation accuracy compared to prior approaches, with best scores of 94.24% Dice for crop segmentation and 93.72% for weeds, but also significantly reduces inference time by avoiding multi-stage pipelines, making it well-suited for real-time deployment.

Keywords: artificial neural networks; ensemble of neural networks; image segmentation; crops; weed identification


## 1. Introduction

In the domains of Smart and Precision Agriculture, the detection and segmentation of weeds represent an important step in the adaptive application of pesticides, one of the most important tasks in an increasingly more pressing need for environmentally re- sponsible, resource-efficient, and economically sustainable agricultural practices. With the steady growth of the global population and the parallel intensification of agricultural practices, the indiscriminate use of herbicides has led to severe environmental, economic, and health-related concerns. Reports indicate a projected increase in global food demand by an estimated 50–60% between 2010 and 2050 to meet the needs of a larger and more affluent population, placing additional pressure on agricultural systems to produce more with limited resources while avoiding further ecosystem degradation [1]. Both rising global population and increasing per capita income significantly drive the demand for food—especially for calories and for higher-value food products such as meat and dairy, which require more crop calories as feed. Under a central scenario with a 39% population

Academic Editors: Yongwha Chung

and Alessandro Leone

Received: 20 February 2026

Revised: 22 April 2026

Accepted: 5 May 2026

Published: 9 May 2026

Copyright: © 2026 by the authors.

Licensee MDPI, Basel, Switzerland.

This article is an open access article

distributed under the terms and

conditions of the Creative Commons

Attribution (CC BY) license.

Sensors 2026, 26, 2997 https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 2 of 20

increase by 2050, total available food calories are projected to grow by about 44%, and crop calories by about 47% relative to 2011. Future increases in food demand will continue to exert pressure on cropland and agricultural systems. How this demand is met—as a func- tion of productivity growth, dietary change, and land use adjustment—affects food prices, resource use, and the size of the global agricultural footprint by mid-century [2]. While the agricultural land area has also consistently increased through the years, and agricultural productivity growth has reduced the use of natural and environmental resources, the total factor productivity growth has slowed down between 2011 and 2020, and this stagnation may affect food prices, the expansion of agriculture into more natural lands, and global food security [3]. The effects of climate change on agricultural activity and yields may further affect the capacity of food systems to meet rising demand, as increasing temperatures, altered precipitation patterns, and more frequent extreme weather events are projected to reduce average yields for major staple crops in many regions and place additional stress on production systems. Under severe climate scenarios and without effective adaptation, scientists indicate simulated losses in crop yields such as wheat, rice, and maize range from approximately 7% to 23%, highlighting the sensitivity of global agriculture to climatic shifts and water stress [4]. Widespread and repeated herbicide applications have been linked to contamination of soil and aquatic systems via runoff and leaching, reductions in plant, microbial, and animal biodiversity, and the proliferation of herbicide-resistant weed populations that complicate management and ecosystem function. These impacts include adverse effects on non-target organisms across trophic levels, alterations in community structure, and diminished habitat quality in agroecosystems [5]. Precision Agriculture ad- dresses these challenges by tailoring field treatments to local conditions, reducing chemical usage while maintaining or improving crop yields.

Within this framework, accurate weed detection and segmentation enable site-specific weed management strategies, such as variable-rate spraying [6,7], robotic herbicide applica- tion [8] and robotic mechanical removal [9,10]. These approaches rely heavily on computer vision and machine learning techniques capable of distinguishing crops from weeds under highly variable field conditions, including changes in illumination, soil background, crop growth stages, and weed morphology. Deep learning approaches, such as convolutional neural networks, vision Transformers, and hybrids, have revolutionized agricultural image analysis, making it possible to identify and map weeds in real time with high spatial accu- racy. By learning rich visual features directly from field images, these networks overcome the limitations of manually designed descriptors and remain robust to environmental vari- ability. Fully convolutional and attention-based architectures provide detailed, pixel-level segmentation, enabling precise weed localization and supporting downstream actions such as variable-rate spraying or robotic removal. These advances position deep learning as a key technology for efficient and scalable site-specific weed management [11].

Nevertheless, several challenges remain. The high intra-class variability of weeds, their visual similarity to crops at early growth stages, and the scarcity of well-annotated datasets limit the robustness and generalizability of existing models. Furthermore, deployment constraints such as computational efficiency, energy consumption, and real-time inference requirements must be considered for practical field applications [12]. Addressing these issues is crucial for the development of reliable, scalable, and environmentally responsible weed control systems, reinforcing the central role of weed detection and segmentation in the broader context of sustainable and intelligent agricultural practices.

The ultimate purpose of models capable of accurately distinguishing between crops and weeds, with precise localization and surface estimation, may be the integration of such architectures into broader, scalable monitoring platforms, where they will no longer be isolated tools, but components within a larger intelligent pipeline. Recent advancements

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 3 of 20

in areas like IoT, Big data, and Cloud computing have spurred an all-new interest in inte- grated, data-driven agricultural ecosystems, where real-time insights can be continuously collected, processed, and acted upon [13,14]. For example, the authors in [15] present a complex software solution that aims to support decision-making through real-time and predictive analytics by using a layered architecture, which goes from the IoT device layer, which collects data from multiple sensor sources, such as soil and weather sensors, or UAV-mounted optical sensors, to a cloud computing layer, for advanced analytics and storage. The platform includes an application marketplace, which supports the creation of an extensible, modular plugin system that allows users to create and add tools for specific tasks. CloudCropFuture [16] is another recently proposed scalable platform for greenhouse monitoring, which can integrate different models for different tasks, such as disease detec- tion, maturity assessment, and crop quality evaluation. Each of the subsystems for these tasks uses data that is collected through an acquisition and monitoring system, which includes high-precision sensors for environmental data and imaging. The sensor data is then used by the edge “Environmental Monitoring Host”, which communicates with the cloud-based server. Data-driven commands may be given by a human operator through a mobile app or web interface, or be automatically decided by the Host, which actuates different execution nodes, such as irrigators or ventilation systems. Another interesting direction is the creation of Digital Twin models, which may simulate agricultural activities to predict various outcomes, such as yields or diseases. In [17], an edge-cloud architecture is employed for creating a virtual model that simulates the scene of a tomato farm. An edge layer collects data from multiple sensors, such as cameras, and preprocesses them, while the cloud layer stores this information and runs object detection models and data transmission services. The application layer builds a virtual 3D farm model and allows the user to visualize and interact with the data.

It becomes evident that the importance of sensors in such platforms is critical. A wide variety of sensors may be employed, ranging from environmental sensors that monitor soil moisture, temperature, humidity, and light intensity, to imaging sensors such as RGB, multispectral, hyperspectral, or thermal infrared cameras, which provide detailed visual information about crop conditions [18]. Beyond direct visual observation, such imaging modalities also enable the extraction of biochemical and physiological indicators that are highly relevant for crop–weed discrimination. Vegetation indices, such as the Normalized Difference Vegetation Index (NDVI), exploit differences in spectral reflectance to capture variations in chlorophyll content and plant vigor. These differences can be leveraged to distinguish crops from weeds, as they often exhibit distinct growth patterns, stress responses, and biochemical signatures [19].

Tobacco (Nicotiana tabacum L.) is the principal species cultivated for commercial tobacco production worldwide, valued for its cured leaf used in smoking, chewing, and nicotine extraction. Though tropical in origin, cultivated tobacco is grown across a wide range of climates and requires a frost-free period following transplanting to reach maturity in the field, with seedlings typically raised in beds and later transplanted at defined spacings into prepared soil [20]. The crops’ establishment as transplants and relatively wide row spacings expose considerable bare soil early in the season, which can facilitate weed emergence that competes with young plants for light, water, and nutrients, making precise and timely weed management a key agronomic practice in tobacco systems.

Weed infestations in tobacco fields are diverse and highly variable, consisting of both annual and perennial species with growth patterns that often overlap with the crop during early phenological stages, leading to significant crop losses [21]. Many common tobacco weeds exhibit morphological similarities to young tobacco plants, complicating visual discrimination and increasing the risk of misapplication during control operations.

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 4 of 20

Additionally, tobacco is particularly sensitive to herbicide injury, which limits the range and dosage of chemical treatments that can be safely applied [22]. These factors make conventional blanket spraying inefficient and potentially damaging, highlighting the need for accurate weed detection and segmentation methods that enable selective interventions tailored to the specific weed pressure within tobacco fields.

In this context, the following paper presents a hierarchical semantic segmentation solution that accurately distinguishes crops from weeds in tobacco fields, leveraging multi-scale contextual information and spatially aware decoding to capture fine-grained structures while maintaining efficiency suitable for real-world field applications.

Numerous works on weed detection and segmentation expand on methods based on either encoder–decoder architectures or forms of Pyramid Pooling. Building on these foundations, recent research increasingly focuses on integrating multi-scale attention mech- anisms and lightweight backbones to balance precision with real-time performance in the field. Some approaches fuse spectral or depth cues with RGB imagery to mitigate occlusion and illumination variability, while others explore transformer-based designs that capture broader spatial context without sacrificing fine-grained boundary detail. Together, these di- rections reflect a shift toward models that can generalize across diverse crop types, growth stages, and environmental conditions while remaining efficient enough for deployment on edge devices in agricultural settings.

To enable deployment on edge devices and UAVs, significant effort has been di- rected toward reducing the computational burden of semantic segmentation models. Zuo and Li [23] proposed an improved U-Net by replacing the standard encoder with MobileNetV3 and integrating a Pyramid Pooling Module (PPM), achieving high ac- curacy with reduced parameters in weed segmentation in corn fields. Similarly, the authors in [24] introduced CWRepViT-Net, which utilizes RepViT blocks in the encoder and a modified U-Net decoder, leveraging transfer learning to balance speed and precision. Habib et al. [25] proposed DWUNet, which employs blocks centered around depth-wise separable convolutions to minimize inference time (8 ms per image).

Beyond CNNs, lightweight Transformers have also gained traction. Castellano et al. [26] adapted Lawin, a Transformer-based encoder–decoder semantic segmentation architecture, for weed mapping by adding NIR and RE bands capability through the addition of a second encoder and multiple feature fusion blocks. In [27], the authors propose an architecture with an encoder akin to Segformer’s Mix Transformer [28], with overlapped patch merging, efficient self-attention, and Mix-FFN. The decoder employs a two-branch approach: after the multi-scale encoder features are passed through a Spatial MLP block, the Dynamic Context Aggregation and Local Detail Enhancement branches model the global contextual information and the local details, respectively. The features from the two parallel branches are then fused and processed through multiple Spatial MLP blocks.

To address the limitations of CNNs in capturing global context and Transformers in capturing local details, recent works have increasingly adopted hybrid architec- tures. Jiang et al. proposed SWFormer [29], a scale-wise hybrid network that integrates Convolutional Modulation with Transformer blocks to capture multi-granularity in- formation. Sun et al. [30] developed a dual-branch architecture combining a CNN branch for local boundary enhancement and a Transformer branch for global modeling. Similarly, Madeshwar et al. [31] and Mei et al. [32] integrated attention mechanisms (AMFF—Adaptive Multispectral Feature Fusion—and AFMA—Across Feature Mapping Attention—, respectively) into U-Net-like structures to improve the segmentation of small, irregular weed targets. While these architectures improve accuracy, they process the entire image at high resolution or high complexity, which can be computationally wasteful, especially for images with large, simple background areas.

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 5 of 20

Recognizing that single-stage models often struggle with fine details, hierarchical approaches have been proposed to refine predictions. Awedat [33] introduced a dual-stage framework that first detects weeds using YOLOv8 (Object Detection) and then refines the bounding box regions using U-Net (Segmentation). This “detect-then-segment” approach restricts expensive segmentation to relevant areas but relies on the assumption that weeds fit neatly into bounding boxes, which is often not the case for amorphous weed patches.

Other hierarchical methods focus on resolution rather than selection. Zhao et al. [34] combined Super-Resolution Reconstruction (SRR) with semantic segmentation to en- hance low-resolution drone imagery before processing. A similar work was presented in [35]. Cheong et al. [36] addressed field-of-view limitations by using an “outpainting” teacher network to guide a student network. These methods generally apply refinement globally or based on spatial constraints, rather than model confidence. Uncertainty esti- mation has also been explored to increase the reliability of agricultural robotic systems. In [37], Celikkan et al. proposed a Bayesian DeepLabv3+ that outputs pixel-wise uncer- tainty estimates using Monte Carlo Dropout. Their work demonstrates that uncertainty maps can effectively highlight areas where the model is prone to error (e.g., boundaries and occlusions).

The authors in [38] propose a two-step approach that most closely resembles our method. Their work demonstrates that weed segmentation can be simplified by first addressing the easier task of segmenting overall vegetation. In the first stage, the model performs binary segmentation, classifying pixels as either vegetation or background, with background pixels set to zero. The resulting output is then used as input for a three-class segmentation task, distinguishing background, crop, and weed, with better scores than a traditional, one-stage U-Net. Our own past work [39] refined this concept using an EfficientNet-backed two-stage U-Net, in which both stages performed binary segmentation, achieving improved overall results, both in terms of accuracy and speed. While effective, the sequential nature of these approaches increases computational cost and latency.

Despite these advancements, a critical disconnect remains between architectural efficiency and hierarchical feature discrimination. Existing lightweight solutions (e.g., MobileNet-based U-Nets) achieve inference speed by significantly reducing network depth, often sacrificing the high-level semantic capacity required to distinguish morphologically similar crops and weeds. Conversely, heavier architectures or Transformer-based models offer superior segmentation fidelity but are computationally prohibitive for real-time edge deployment. Furthermore, current methodologies still struggle to handle the geometric irregularity of agricultural targets. Multi-stage approaches, often times slower, also tend to rely on object detection priors (bounding boxes), which are ill-suited for amorphous, sprawling weed patches. While attention mechanisms have been proposed to address this, they are rarely integrated effectively with modern hierarchical backbones in a way that enforces logical consistency across scales and are most often computationally expensive.

To address these limitations, we propose a single-stage segmentation network that in- tegrates multi-scale contextual reasoning, simple spatial attention, and a Vegetation Global Context module. By producing separate vegetation and crop predictions in one forward pass, the network derives the weed probability as the residual vegetation not explained by crops, enforcing logical consistency between classes. Multi-scale deep supervision guides intermediate features, enabling precise delineation of fine-grained structures while main- taining computational efficiency suitable for real-time deployment. We experiment with several modern backbones to illustrate how different architectures balance segmentation performance and inference speed.

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 6 of 20


## 2. Materials and Methods

2.1. Dataset

The dataset used for the experiments in this paper was introduced in [38], and is publicly available at [40]. It comprises 210 images, taken across eight campaigns in Mardan, Khyber, Pakhtunkwa, Pakistan, using a Mavic Mini drone, at an average altitude of 4 m and a resolution of 1920 × 1080. This drone employs a 1/2.3′′ CMOS sensor camera, which can shoot up to 2.7 K video and 12 MP photos, with an aperture of f/2.8. It also includes a 3-axis gimbal for stabilization [41]. The authors also provide 480 × 352 resolution patches extracted from the sensor data. The segmentation masks were drawn manually and included three classes: background (pixel value of 0), tobacco plant (value of 1) and weed (value of 2). An example of such a patch is presented in Figure 1. Unfortunately, the dataset presents two major issues. First, there are inconsistencies between the masks and the patches: files sharing the same name do not correspond to the same region of the original image. We have found that this is only a misnaming problem. A case like this is illustrated in Figure 2.

(a)  (b)  (c)


> **Figure 1. Example of a patch-mask pair in the dataset. (a) a 480 × 352 patch; (b) ground-truth**

> segmentation mask for the patch. The gray areas represent tobacco plants, and the white areas represent
weeds; (c) patch with the ground-truth mask’s edges overlaid (green for tobacco, red for weeds).

(a)  (b)  (c)


> **Figure 2. Example of a mismatched (a) patch image and (b) mask pair in the dataset (101.png**

> from Campaign no. 1), with (c) showing the patch with the overlaid mask edges to highlight the
misalignment (green for tobacco, red for weeds).

To address this issue, we extracted binary masks using an HSV-based green filter. For each image patch, the extracted mask was compared against the set of ground truth masks in the dataset using the k-nearest neighbors (k-NN) algorithm. The ground truth mask with the smallest distance to the extracted mask was identified as the corresponding match, and the masks were renamed to ensure correct correspondence. Figure 3 shows the correct

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 7 of 20

pair found in the same database for the mismatched image above. Note that this process did not in any way modify the ground-truth masks themselves.

(a)  (b)  (c)


> **Figure 3. (a) The same original image as in Figure 2; (b) its correct ground-truth mask, found using the**

> k-nearest neighbors HSV filter approach in the same dataset and (c) the patch with the ground-truth
mask’s edges overlaid (green for tobacco, red for weeds).

The second issue concerns the noise present in the masks from the second data acqui- sition campaign. Our preliminary experiments showed that these noisy samples negatively impact both the segmentation models and the evaluation process. Consequently, we decided to exclude this portion of the dataset from our experiments.

2.2. Neural Networks Used 2.2.1. U-Net Architecture

To effectively capture both semantic context and local textural details, we employ a U- Net architecture. The network follows a symmetric encoder–decoder design. The encoder (contracting path) progressively reduces the spatial resolution of the input while increasing feature dimensionality, enabling the extraction of abstract semantic representations. The decoder (expanding path) restores spatial resolution through successive upsampling stages, combining high-level features with corresponding encoder features via skip connections to preserve localization accuracy.

Building upon the standard U-Net formulation, we introduce multiple specialized modifications. These include a Vegetation Global Context block, designed to integrate global contextual cues relevant to vegetation structure, and a dual-headed output design that predicts vegetation and crop masks separately. This formulation allows weed regions to be computed hierarchically as the difference between vegetation and crop predictions, enforcing logical consistency directly within the network.

We also experimented with multiple modern encoder backbones within the same U-Net framework: ConvNeXt V2, FastViT, RepViT and MambaVision. These include convolutional, hybrid convolution–transformer, and state-space–inspired models.

2.2.2. ConvNeXt V2

Introduced in [42] as an attempt to apply Vision Transformer concepts in building a ConvNet architecture, ConvNeXt modernized standard ResNets, enabling them to compete with the emerging state-of-the-art transformer-based models. By adopting design princi- ples from transformers—such as larger kernel sizes, inverted bottlenecks, and simplified normalization—ConvNeXt retained the efficiency and inductive biases of convolutions while achieving improved accuracy.

The architecture employs a minimalistic design: it replaces the original ResNet stem and bottleneck blocks with streamlined convolutional blocks, uses LayerNorm instead of BatchNorm, and incorporates depthwise convolutions to capture long-range

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 8 of 20

dependencies more effectively. ConvNeXt has demonstrated strong performance on image classification benchmarks, rivaling that of Vision Transformers while maintaining lower computational complexity and better scalability for downstream tasks such as object detection and segmentation. The paper presents multiple variants—Tiny, Small, Base, and Large—which differ in the number of channels and layers per stage, scaling model capacity and computational cost.

An updated version of the architecture, ConvNeXt V2, was proposed in [43]. Building on the strengths of its predecessor, ConvNeXt V2 adopts an adapted version of the masked autoencoder self-supervised training strategy, in which random portions of the input image are masked, and the model is trained to reconstruct the missing content from the visible context using an encoder–decoder framework.

This pretraining approach encourages the network to learn richer and more gener- alizable visual representations, improving data efficiency and robustness. In addition, ConvNeXt V2 introduces architectural refinements such as Global Response Normalization (GRN), which enhances feature competition and stabilizes training at scale. Together, these changes allow ConvNeXt V2 to achieve state-of-the-art performance across both supervised and self-supervised settings, while preserving the simplicity and efficiency characteristic of convolutional networks.


> **Figure 4 illustrates the four stages of the ConvNeXt V2 Tiny architecture, including the**

> first stem convolution and the downsampling steps, which mark the transitions between
them. Each stage corresponds to a repetition of a block, which consists of a depthwise con-
volution and two pointwise convolutions (the red, yellow, and blue squares). The accolades
suggest that each block is repeated an ×k number of times before the downsampling. The
values below each convolution show the evolution of the number of channels.


> **Figure 4. The four stages of the ConvNeXt V2 Tiny architecture, including the initial stem and**

> intermediary downsampling steps.

2.2.3. FastViT

Designed to achieve very low latency while retaining strong representational capacity, FastViT [44] is a hybrid vision transformer model that combines re-parameterized convolu- tional blocks with lightweight token-mixing mechanisms. The architecture is based on the principle of structural re-parameterization, in which multi-branch training-time structures are merged into single convolutional layers at inference, eliminating the need for explicit skip connections. It comprises four hierarchical stages with progressively decreasing spa- tial resolution and increasing feature dimensionality. Within each stage, feature mixing

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 9 of 20

is achieved through depthwise convolutions that enable efficient re-parameterization of residual pathways. In the final stage, conventional self-attention is replaced by large- kernel convolutions, reducing computational complexity while retaining a wider, non-local receptive field.

The model also replaces all dense k × k convolutions with their factorized versions, akin to depthwise separable convolutions. While this leads to better efficiency, it also lowers the parameter count, which may reduce performance. To compensate, the architecture overparametrizes those replaced layers, found in the convolutional stem, patch embedding, and projection layers, at train-time.

2.2.4. RepViT

Proposed in [45] as a modernization of MobileNets by incorporating aspects of the Vision Transformer’s architectural design, RepViT also focuses on convolutional mixing and structural reparametrization. By moving the depthwise convolution up, in a separate branch to the 1 × 1 expansion convolution. This effectively separates, as in the case of ViT, token (spatial) and channel mixing. The formed skip connection is omitted at inference through reparametrization. The expansion ratio is fixed to 2 throughout the whole network, rather than the variable 2, 3, and 6 of MobileNetV3, and further optimizations are made for mobile devices, such as simplifying the early stem convolutions, deepening the downsampling block, simplifying the final classifier, redistributing the stage ratio for deeper late stages, and removing the 5 × 5 convolutions and repositioning squeeze-and- excitation modules to appear only once every two blocks. These modifications collectively reduce parameter count and computational cost while maintaining expressive power and a large effective receptive field.

2.2.5. MambaVision

Combining Conv-Transformer hybrids with Mamba state space models, the Mam- baVision architecture achieved SOTA performance on the ImageNet-1K dataset by intro- ducing the MambaMixer block in another four-stage network, which leverages structured state-space layers to model long-range spatial dependencies efficiently, integrates local convolutional processing for fine-grained feature extraction, and incorporates self-attention in deeper stages to capture global context. The original Mamba mixer specializes in vision tasks, replacing causal convolution with regular convolution and adding a parallel branch with no state-space modeling to capture spatial information.

All encoder backbones were initialized with ImageNet-pretrained weights and inte- grated without architectural modifications to the proposed decoder, ensuring that observed differences reflect encoder characteristics rather than changes in the segmentation architecture.

2.3. Proposed Architecture

The proposed architecture, with a ConvNeXt V2 encoder, is presented in Figure 5. The ConvBlocks consist of two consecutive 3 × 3 convolutional layers, each followed by a ReLU activation. The decoder comprises three upsampling blocks (UpBlock). Each block performs bilinear upsampling, applies Spatial Attention to the corresponding skip connection, concatenates the features, and refines them with a convolutional block. For supervision, both the auxiliary heads and the final heads produce logits at the spatial resolution of their respective decoder outputs. These logits are then bilinearly interpolated to match the input image dimensions before loss computation. This ensures that all predicted masks—whether intermediate or final—are directly comparable to the ground-truth annotations at full resolution, enabling coherent multi-scale learning.

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 10 of 20


> **Figure 5. The proposed U-Net segmentation architecture with a ConvNeXt V2 backbone.**

The model employs two separate output heads, one for vegetation and one for crops, each implemented as a simple 1 × 1 convolution, allowing the network to learn specialized features for each class. This separation facilitates hierarchical reasoning, as weeds can be derived from the difference between the vegetation and crop masks, and helps enforce logical consistency in the segmentation while improving overall accuracy.

2.3.1. Spatial Attention

In the U-Net decoder, encoder features are passed through skip connections to recover spatial details lost during downsampling. However, not all spatial locations in these features are equally informative for segmentation: background regions and weak textures can propagate noise into the decoding stages.

To mitigate this, we apply a simple, self-gated spatial attention mechanism on the skip features before concatenation. The module learns a per-pixel importance map di- rectly from the skip tensor itself, without conditioning decoder activations or introducing cross-scale gating.

Given a skip feature map xskip ∈RH×W×C, we compute a single-channel spatial weight map W ∈RH×W×1 using a 1 × 1 convolution followed by the sigmoid activation σ:





W = σ

Conv1×1 (xskip )

(1)

The skip features xskip are then modulated element-wise by this weight map, resulting in x′skip:

x′

skip = xskip ⊙W, (2)

where ⊙denotes element-wise multiplication.

This operation encourages the decoder to focus on spatially important regions—such as vegetation structures—while down-weighting less relevant areas.

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 11 of 20

2.3.2. Vegetation Global Context Block

To enhance feature representations in regions likely to contain vegetation, we integrate a Vegetation Global Context Block. This module computes a channel-wise attention vector that modulates features based on the estimated vegetation probability, providing a context- aware recalibration akin to Squeeze-and-Excitation networks [46].

Considering H and W, the spatial dimensions of the image, and C the number of channels, given a feature map F ∈RH×W×C obtained through the convolution of the final encoder features and a vegetation probability map V ∈RH×W with values in the interval [0, 1], calculated using a Sigmoid activated 1 × 1 convolution of the last encoder stage, the block first computes a soft Masked Global Pooling:

∑H

i=1 ∑W

j=1 F i,j,CV i,j

, ∀c ∈{1, 2, . . . , C}, (3)

wc =



∑H

∑W

j=1 V i,j + ϵ

i=1

where ϵ is a small constant to avoid division by zero, and w ∈R1×1×C is the resulting channel descriptor summarizing feature activations weighted by vegetation likelihood.

The excitation part follows [46]. A channel bottleneck reduces the dimensionality of this descriptor, applies a nonlinearity, and projects it back to the original number of channels to produce a gating vector for each channel g ∈R1×1×C:

g = σ(W2 ReLU (W1w)), (4)

C

r ×C and W2 ∈RC× C

where W1 ∈R

r are learned 1 × 1 convolutional weights implement- ing the dimensionality reduction, and subsequent expansion, by the reduction ratio r, chosen so as to divide C, and σ is the sigmoid function. In our case, we have used a reduction ratio of 4.

Finally, the original feature map is weighted channel-wise by the gating vector, obtaining F

′:

F′ = F ⊙g (5)

This operation emphasizes channels that are most relevant to vegetation regions while suppressing less relevant information, effectively conditioning the global feature representation on the predicted vegetation mask.

The Vegetation Global Context Block is lightweight, fully differentiable, and is inserted into the bottleneck layer of the encoder–decoder architecture to provide vegetation-aware global context. It is further illustrated in Figure 6.


> **Figure 6. The Vegetation Global Context Block, placed at the bottleneck of the network.**

2.3.3. Deep Supervision

Deep Supervision involves placing auxiliary classification heads at intermediate layers of the decoder. This combats the vanishing gradient problem and forces the intermediate

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 12 of 20

layers to learn semantically meaningful features early in the network. These auxiliary heads are discarded at inference time.

We attach auxiliary heads to the output of each upsampling stage. These output two channels: one for vegetation and the other for crops. This deep supervision serves two purposes. Firstly, it stabilizes optimization by providing direct gradient signals to intermediate decoder layers, mitigating vanishing gradients and accelerating con- vergence. Secondly, it encourages semantically meaningful representations at multiple spatial scales: coarse decoder stages are guided to capture global vegetation structure, while finer stages progressively refine crop localization. Since vegetation and crop form a hierarchical label structure, supervising both classes at each scale promotes consis- tent feature disentanglement throughout the decoder rather than deferring all semantic separation to the final layers.

2.4. Logical Constraints and Weed Class Inference

Another interesting aspect of our method is the enforcement of logical, hierarchical consistency. Since ideally a pixel cannot represent a crop if it is not part of the vegetation class, we scale the crop predictions by the vegetation probabilities during training. The predicted crop probability Pcrop is scaled by the vegetation prediction Pveg, resulting in bPcrop:

bPcrop = Pcrop · Pγ

veg (6)

where γ = 0.75. This softly suppresses crop predictions in non-vegetation-predicted areas, while leaving room for correction when the vegetation prediction is uncertain.

Subsequently, the Weed probability map Pweed is derived logically rather than pre- dicted independently:

(

Pveg −bPcrop, Pveg ≥bPcrop 0, otherwise (7)

Pweed =

Since the weed probability map is obtained through subtraction, its values tend to be lower in magnitude compared to directly predicted logits. For this reason, we apply a slightly lower decision threshold during binarization to recover the final weed mask. Operating in probability space allows uncertainty from both vegetation and crop predictions to be preserved, particularly around boundaries and ambiguous regions. In preliminary experiments, this soft formulation consistently outperformed a hard logical XOR between vegetation and crop masks, which enforces strict binary separation and proved more sensitive to misclassifications and boundary noise.

2.5. Loss Function

The total objective function, Ltotal, is a weighted sum of the primary head losses and the auxiliary deep supervision losses. In the following equations, we will consider P and G flattened maps of dimension N = HW (where H is the initial height, and W the width), with i indexing pixels.

We utilize the Dice Loss (LDice) to handle class imbalance by maximizing the overlap between the predicted probability map P and the ground truth G:

LDice(P, G) = 1 − 2 · ∑N i=1 PiGi ∑N

(8)

i=1 Pi + ∑HW

i=1 Gi

By weighting the contribution of each pixel relative to the sum of predicted and ground truth pixels, Dice Loss emphasizes overlap rather than absolute pixel counts, which makes it particularly effective when foreground regions are small compared to the background.

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 13 of 20

To penalize boundary inaccuracies, we incorporate a Boundary Dice Loss, Lbound. We compute edge maps for both the prediction and ground truth using convolution with a discrete Laplacian kernel K (approximate second-order derivative). The loss is computed as the Dice loss between these edge maps:

Lbound(P, G) = 1 −Dice(ReLU(P ∗K), ReLU(G ∗K)),





1 1 1 1 −8 1 1 1 1

 (9)

K =



The application of the Rectified Linear Unit (ReLU) function is essential because the Lapla- cian kernel naturally produces a zero-crossing at edges, resulting in both positive and negative values. Since the Dice coefficient is a set-similarity metric undefined for negative inputs, the ReLU operation eliminates the negative component—typically corresponding to the internal side of the boundary—and isolates the positive external contour. This ensures numerical stability and converts the raw derivative into a clean, non-negative edge mask, allowing the network to strictly enforce geometric alignment between the predicted and ground truth boundaries.

For the Crop head, we also utilize Binary Cross-Entropy (BCE) to strictly penalize pixel-level misclassifications, ensuring that all pixels within the object region, not just its boundaries, are predicted confidently. Unlike Dice, which considers the image as a set, BCE evaluates the confidence of each pixel independently and acts as a stabilizing term, ensuring that the model learns the general distribution of pixels early in training before fine-tuning the boundaries.

N ∑ i=1

LBCE(P, G) = −1

[Gi · log(Pi) + (1 −Gi) · log(1 −Pi)], (10)

N

To further enforce the logical consistency of the crop class and improve the recall of its prediction within vegetated areas, we have found it beneficial to also include an LCropRecall term, which represents the Dice loss computed exclusively over pixels labeled as vegetation, and encourages the network to recover all crop pixels within the broader vegetation mask:









bPcrop · Gveg, Gcrop · Gveg

= LDice

(11)

LCropRecall

bPcrop, Gcrop, Gveg

The final loss functions for the Vegetation and Crop heads combine Dice, Binary Cross Entropy (BCE), and Boundary Dice terms. The total loss is calculated as:

 + λbVLBound

 

 



Lveg = LDice

Pveg, Gveg

Pveg, Gveg

(12)













Lcrop = BCE

+ LDice

+ λbCLBound

+

bPcrop, Gcrop

bPcrop, Gcrop

bPcrop, Gcrop

 (13)


### 0.5 · LCropRecall



bPcrop, Gcrop, Gveg





Lweed = 0.7 · LDice(Pweed, Gweed) + λbWLBound

bPweed, Gweed

(14)

3 ∑ k=1

λauxL(k)

Ltotal = λVLveg + λCLcrop + λWLweed +

aux (15)

where λ terms are hyperparameters weighting the contribution of each component, and

L(k)

aux represents the Dice loss from the k-th deep supervision head.

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 14 of 20


## 3. Results

We have built our U-Net architecture with different ImageNet-pretrained encoders using the Pytorch 2.9.0 and timm libraries 1.0.22. As the patches were non-overlapping and the campaigns included different weather, soil conditions, and stages of growth, we chose to split the whole dataset for training, validation, and testing. After excluding the second campaign, the images were randomly divided into 80% training data (1267 patches), 10% validation data (158 patches), and 10% testing data (159 patches). Each image was standardized by the ImageNet dataset’s mean and standard deviation.

For every experiment, we used the AdamW optimizer, and a Cosine Annealing learning rate scheduler was also employed. Each model was trained for a total of 50 epochs, and only the checkpoint where the model obtained the best validation score was saved. Most hyperparameters were chosen after a grid search. We have grouped them in Table 1.


> **Table 1. Hyperparameters used for the training of the models, selected through a grid search.**

Hyperparameter Value

λbV 0.3 λbC 0.05 λbW 0.3 λaux 0.05 λV 1.3 λC 1.6 λW 1 Learning Rate 1 × 10−4

Weight Decay 1 × 10−4

The experiments have been performed on a personal computer with an i5-9300H CPU, a GTX 1660TI GPU, and 8 GB of RAM.

During model validation, we evaluated multiple binarization thresholds applied to the final probability maps produced by the model. The results have shown that better scores were consistently obtained with lower steps, something to be expected as the weeds class probabilities are obtained as a subtraction. This behavior can also be attributed to the characteristics of the segmentation task: crop and weed boundaries are often ambiguous, partially occluded, or affected by illumination variability, leading to moderately confident predictions in boundary and fine-structure regions. A higher binarization threshold tends to suppress these low- to mid-confidence activations, fragmenting predicted regions and increasing false negatives, particularly for thin or early-stage weeds. In contrast, a lower threshold preserves weaker but spatially coherent activations, resulting in more complete object representations and improved recall.

We chose to apply a 0.3 threshold for our final models, and we report the scores with this parameter in Table 2. The scores include the IoU, mIoU over the three classes, Dice, Overall Pixel Accuracy, and Overall Cohen’s Kappa coefficient. The inference speed was determined by measuring the total elapsed time of the batch-wise iteration loop over the test set, beginning immediately prior to the first data fetch and concluding after the final GPU synchronization, without any warm-up. By timing the complete execution cycle, the reported throughput accounts for the entire processing pipeline, including the initial reading of the image file, resizing and normalization, and the post-processing step of thresholding. For [38] we note the average scores reported in the paper across all the campaigns except for the second one, which we did not use. The inference time is also the one reported in the respective paper, so it has been measured on a different system than the other cases. For [27] we report their stated results on a split of 40 test images. The paper does not explicitly mention whether the metrics are measured on all three classes or just on

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 15 of 20

crops and weeds. The inference speed is calculated based on their reported time of 35 ms for an image, and it has not been measured on the same system as the others.


> **Table 2. Results obtained with the different backbones we experimented with in our architecture,**

> along with 2 other works on the same dataset. Bold was used for the best parameter values.

Inference

Backbone Resolution IoU Crops

IoU Weeds mIoU Dice Crops

Dice Weeds

Overall Accuracy

Overall

Speed

Kappa

(Im/s)

[38] 480 × 352 0.7460 0.7800 - - - - - 1.428 [39] 320 × 320 0.8894 0.8582 - 0.9374 0.9215 - - 10.79 [27] 480 × 352 - - 0.8648 - - 0.9208 - 28.57 ConvNeXt

480 × 352 0.8990 0.8843 0.9225 0.9424 0.9372 0.9790 0.9586 22.90 256 × 256 0.8971 0.8366 0.9002 0.9446 0.9086 0.9695 0.9400 35.46 Mamba Vision-T 480 × 352 0.8930 0.8498 0.9046 0.9392 0.9165 0.9718 0.9444 24.06

V2 Tiny

FastViT_S12 480 × 352 0.8919 0.8459 0.9031 0.9389 0.9141 0.9713 0.9434 44.52 256 × 256 0.8914 0.8197 0.8916 0.9412 0.8982 0.9665 0.9339 64.81 FastViT_SA24 480 × 352 0.8932 0.8536 0.9067 0.9392 0.9190 0.9728 0.9463 25.72 RepViT-M2 480 × 352 0.8942 0.8507 0.9058 0.9401 0.9171 0.9724 0.9454 47.77

To test our architecture against a heavyweight state-of-the-art segmentation model, we have also fine-tuned a pre-trained Mask2Former [47] model with a SwinTransformer-Tiny backbone in the same conditions, on the 480 × 352 patches, for 50 epochs. Mask2former is an architecture designed as a universal segmentation model, capable of addressing all segmentation tasks, and is based around a Transformer decoder with masked attention. It has a much higher parameter count and computational cost than our models. The results are presented in Table 3. The metrics show that our architecture achieves higher performance, with a much faster inference speed.


> **Table 3. Comparison of our best-performing model with a fine-tuned Mask2Former architecture.**

> Bold was used for the best parameter values.


## Architecture

No. Params
FLOPs
IoU
Crops

IoU Weeds

Dice Crops

Dice Weeds

Inference Speed

(Images/s)

Mask2former 47.40 M 46.05 G 0.8918 0.8686 0.9373 0.9281 4.47

Ours, with ConvNeXt V2 Tiny 32.52 M 17.93 G 0.8990 0.8851 0.9424 0.9376 22.90


## 4. Discussion

The quantitative results in Table 2 reveal consistent trends across backbone families and input resolutions. As expected, higher input resolutions generally lead to improved weed segmentation performance, reflected by both IoU and Dice scores, confirming that weeds, even though they are not directly predicted, due to their thin, fragmented, and irregular morphology, benefit more strongly from increased spatial detail than crops. This effect is visible for ConvNeXt V2 Tiny and FastViT variants, where downsampling to 256 × 256 results in a noticeable degradation of weed IoU and Dice. Interestingly, crop segmentation performance is greater for the lower resolution inputs. We believe this occurs because downsampling smooths the image, which aids the segmentation of the relatively uniform and regular shapes of the tobacco plants. Across all evaluated backbones, crop segmentation achieves higher IoU and Dice scores than weed segmentation. This gap is expected, given the greater visual variability and boundary ambiguity of weed regions. Importantly, the relatively strong weed performance observed even with lightweight backbones suggests that deriving weeds implicitly as vegetation excluding crops helps

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 16 of 20

stabilize predictions, reducing spurious weed activations in non-vegetated areas and improving boundary coherence.

From an efficiency standpoint, FastViT and RepViT architectures achieve substan- tially higher throughput, exceeding 40 images per second at higher resolutions and over 60 images per second at lower resolutions, making them well-suited for real-time deploy- ment. ConvNeXt V2 Tiny, while slower, consistently delivers the strongest weed segmenta- tion accuracy, indicating a trade-off between representational capacity and computational cost. MambaVision-T occupies an intermediate position, offering balanced performance across both accuracy and speed.

Overall, the results demonstrate that the proposed single-stage architecture, jointly predicting crop and vegetation masks and deriving weed regions as residual vegetation, generalizes well across diverse encoder designs. This flexibility allows the architecture to be paired with either accuracy-oriented or speed-oriented backbones, without sacrificing logi- cal consistency. Compared with the other two approaches on the same dataset, this method achieves at least more than double the inference speed while maintaining comparable—or in some cases superior—Dice and IoU scores, as demonstrated by the ConvNeXt V2 Tiny backbone at full patch resolution (see Table 2).


> **Figure 7 presents a few examples of predicted segmentation masks, along with the**

> original images overlaid with the ground-truth segmentation masks’ edges (Figure 7a) and
the ground-truth masks (Figure 7b), using both the most accurate backbone (ConvNeXt V2
Tiny at full patch resolution) (Figure 7c) and the fastest (FastViT S12 at 256 × 256 resolution)
(Figure 7d). Both models show great promise in their ability to distinguish between the two
classes of interest and to delineate their shapes.

Looking at the ground-truth masks, we may notice that some of them have shapes with rough, sharp angles that are not entirely consistent with the actual plants in the image. This inconsistency may affect the learning and evaluation of our models: while it is true and visibly clear that the ConvNeXt V2 model has the higher scores, since it resembles the ground-truth better, there are instances where the theoretically less precise FastViT model may actually be closer to reality, as is the case in the first sample (row 1 in Figure 7).

The last two examples (rows 3 and 4 in Figure 7), in contrast, highlight the limitations of the lower-resolution FastViT model in capturing very small weed structures. These observations underline that the reported quantitative performance should be interpreted in the context of the possible limitations of the ground-truth annotations.

While the proposed single-stage architecture prioritizes real-time execution and log- ical consistency for edge deployment, it is important to contextualize this approach alongside recent advancements in foundation models, such as the Segment Anything Model 3 (SAM3) [48]. As demonstrated by our benchmarking against Mask2Former (Table 3), heavy transformer-based segmentation models incur significant computational costs (46.05 GFLOPs) and reduced inference speed (4.47 images/second). SAM3, represent- ing a state-of-the-art paradigm in zero-shot, generalized segmentation, features a much larger parameter count and relies on iterative, prompt-driven interfaces. This results in even higher computational demands, which may limit its suitability for integration in resource- constrained agricultural platforms. Furthermore, our proposed hierarchical formulation produces stable predictions without the need for the manual visual or text prompts required by such foundational approaches. Therefore, while models such as SAM3 offer strong potential for large-scale offline agronomic analysis, particularly in scenarios with limited or no annotations, lightweight, task-specific and fully supervised architectures, such as the one proposed in this study, remain well-suited for practical agricultural applications like automated pesticide dispersion.

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 17 of 20

(a)  (b)  (c)  (d)


> **Figure 7. Examples of segmentation masks generated by the proposed architecture with two different**

> backbones at different input resolutions: (a) Original image with the ground-truth mask’s edges
overlaid (green for tobacco, red for weeds); (b) Ground-truth mask; (c) Predicted mask with the
Conv-NeXT V2 encoder (480 × 352 input resolution); (d) Predicted mask with the FastViT S12 encoder
(256 × 256 input resolution).


## 5. Conclusions

This paper has presented a U-Net architecture for the segmentation of tobacco crops and weeds. The architecture incorporated custom modules, such as the Vegetation Global Context Block, and a dual-headed output that separately predicts vegetation and crop masks. Logical constraints are enforced both during training and inference, with weed regions derived hierarchically as the difference between vegetation and crop predictions. Several modern backbones have been tested, and experimental results demonstrate that the proposed approach achieves improved segmentation accuracy while also reducing inference time compared to previous methods evaluated on the same dataset. Although prior work has explored similar differential formulations, these are typically implemented using multi-stage pipelines, which introduce additional complexity and latency. In contrast,

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 18 of 20

our approach integrates the full hierarchical reasoning within a single end-to-end model, enabling efficient inference without sacrificing performance.

Future work will focus on improving spatial feature selection through more expressive attention mechanisms, as well as extending the hierarchical segmentation framework to multi-crop or multi-weed species scenarios. Robustness across domains and acquisition conditions represents another important direction for further experimentation. The pro- posed methods should be systematically evaluated across diverse environments, including different crop types, growth stages, weed density, soil compositions, illumination condi- tions, and weather scenarios, to assess their generalization capabilities. Variations in sensor characteristics, image resolution, and acquisition platforms should also be considered, as they may significantly impact model performance. Techniques such as domain adaptation, data augmentation, and multi-domain training could be explored to mitigate these effects.

The ultimate objective is the integration of the proposed model into a real-time, au- tomated pesticide dispersion system, which may operate as part of a larger agricultural monitoring platform. In such a setting, the model must meet strict constraints in terms of inference speed, computational efficiency, and reliability, enabling precise, site-specific weed treatment. This would allow for targeted pesticide application, reducing chemical usage, minimizing environmental impact, and improving overall agricultural sustainability.

Author Contributions: Conceptualization, D.P. and A.B.-M.; methodology, D.P.; software, A.B.-M.; validation, D.P. and L.I.; formal analysis, L.I.; investigation, D.P.; resources, L.I.; writing—original draft preparation, A.B.-M.; writing—review and editing, L.I.; visualization, A.B.-M.; supervision, D.P.; project administration, D.P.; funding acquisition, L.I. All authors have read and agreed to the published version of the manuscript.

Funding: This research received no external funding.

Institutional Review Board Statement: Not applicable.

Data Availability Statement: The original contributions presented in this study are included in the article. The corrected dataset variant and the test split we used are available in Zenodo at 10.5281/zenodo.19422418. Further inquiries can be directed to the corresponding author.

Conflicts of Interest: The authors declare no conflicts of interest.


## References

1. van Dijk, M.; Morley, T.; Rau, M.L.; Saghai, Y. A meta-analysis of projected global food demand and population at risk of hunger for the period 2010–2050. Nat. Food 2021, 2, 494–501. [CrossRef] [PubMed] 2. Sands, R.; Meade, B.; Seale, J.L.J.; Robinson, S.; Seeger, R. Scenarios of Global Food Consumption: Implications for Agriculture; U.S. Department of Agriculture, Economic Research Service: Washington, DC, USA, 2023. 3. Fuglie, K.; Morgan, S.; Jelliffe, J. World Agricultural Production, Resource Use, and Productivity, 1961–2020; U.S. Department of Agriculture, Economic Research Service: Washington, DC, USA, 2024. 4. Rezaei, E.E.; Webber, H.; Asseng, S.; Boote, K.; Durand, J.L.; Ewert, F.; Martre, P.; MacCarthy, D.S. Climate change impacts on crop yields. Nat. Rev. Earth Environ. 2023, 4, 831–846. [CrossRef] 5. Ba´cmaga, M.; Wyszkowska, J.; Kucharski, J. Environmental Implication of Herbicide Use. Molecules 2024, 29, 5965. [CrossRef] 6. Jiao, Y.; Zhang, S.; Jin, Y.; Cui, L.; Chang, C.; Ding, S.; Sun, Z.; Xue, X. Research Progress on Intelligent Variable-Rate Spray Technology for Precision Agriculture. Agronomy 2025, 15, 1431. [CrossRef] 7. Conceição, L.A.; Silva, L.; Dias, S.; Maçãs, B.; Sousa, A.M.O.; Fiorentino, C.; D’Antonio, P.; Barbosa, S.; Faugno, S. Optimizing Herbicide Use in Fodder Crops with Low-Cost Remote Sensing and Variable Rate Technology. Appl. Sci. 2025, 15, 1979. [CrossRef] 8. Lippi, M.; Santilli, M.; Carpio, R.F.; Maiolini, J.; Garone, E.; Cristofori, V.; Gasparri, A. An autonomous spraying robot architecture for sucker management in large scale hazelnut orchards. J. Field Robot. 2023, 41, 2114–2132. [CrossRef] 9. Upadhyay, A.; Zhang, Y.; Koparan, C.; Rai, N.; Howatt, K.; Bajwa, S.; Sun, X. Advances in ground robotic technologies for site-specific weed management in precision agriculture: A review. Comput. Electron. Agric. 2024, 225, 109363. [CrossRef]

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 19 of 20

10. Sara, G.; Todde, G.; Pinna, D.; Waked, J.; Caria, M. Implementation and Assessment of an Autonomous Ground Vehicle (AGV) for On-Field Agricultural Operations. In Proceedings of the 15th International Congress on Agricultural Mechanization and Energy in Agriculture, Antalya, Türkiye, 29 October–1 November 2023; Springer Nature: Cham, Switzerland, 2024; pp. 340–348. 11. Zhao, H.; Wang, Y. Deep learning–based approaches for weed detection in crops. Front. Plant Sci. 2026, 16, 1746406. [CrossRef] 12. Sandoval-Pillajo, L.; García-Santillán, I.; Pusdá-Chulde, M.; Giret, A. Weed detection based on deep learning from UAV imagery: A review. Smart Agric. Technol. 2025, 12, 101147. [CrossRef] 13. Săcăleanu, D.-I.; Matache, M.-G.; Ros,u, S, .-G.; Florea, B.-C.; Manciu, I.-P.; Peris,oară, L.-A. Iot-Enhanced Decision Support System for Real-Time Greenhouse Microclimate Monitoring and Control. Technologies 2024, 12, 230. [CrossRef] 14. Kalaivani, T.S.; Kamireddy, T.; Govindakumar, S. IoT-Enabled Soil and Crop Monitoring System Using Low-Cost Smart Sensors for Precision Agriculture. Eng. Proc. 2025, 118, 77. [CrossRef] 15. Roukh, A.; Mahmoudi, S. Leveraging big data and cloud technology for scalable and interoperable smart farming. Future Gener. Comput. Syst. 2026, 179, 108324. [CrossRef] 16. Chen, R.; Zhu, Z.; Shen, B.; Zeng, J.; Yang, Z.; Yang, X.; Yao, L. CloudCropFuture: Intelligent Monitoring Platform for Greenhouse Crops with Enhanced Agricultural Vision Models. Appl. Sci. 2025, 15, 9767. [CrossRef] 17. Du, W.; Jin, P.; Jin, W. Smart farm digital twin model based on edge-cloud architecture for tomato monitoring and detection. Smart Agric. Technol. 2025, 12, 101254. [CrossRef] 18. Ł ˛agiewska, M.; Panek-Chwastyk, E. Integrating Remote Sensing and Autonomous Robotics in Precision Agriculture: Current Applications and Workflow Challenges. Agronomy 2025, 15, 2314. [CrossRef] 19. Wang, H.; Ibrahim, M.; Miao, Y.; Severtson, D.; Mansoor, A.; Mian, A.S. Multispectral Remote Sensing for Weed Detection in West Australian Agricultural Lands. In Proceedings of the 2024 International Conference on Digital Image Computing: Techniques and Applications (DICTA), Perth, Australia, 27–29 November 2024; pp. 624–631. 20. McMurtrey, J.E. Tobacco. Available online: https://www.britannica.com/plant/common-tobacco (accessed on 10 January 2026). 21. Khan, H.; Uslu, Ö.S.; Gedik, O. The Impact of Weeds on Tobacco and Their Management, with Special Emphasis on Broomrape (Orobanche sp.). In Proceedings of the 3rd International Conference on Engineering and Applied Natural Sciences, Erbil, Iraq, 25–27 October 2023. 22. Palmer, G.; Bailey, A.; Green, J.D. Dealing with Chemical Injury in Tobacco; University of Kentucky College of Agriculture, Food and Environment, Cooperative Extension Service: Lexington, KY, USA, 2006. 23. Zuo, Y.; Li, W. An Improved UNet Lightweight Network for Semantic Segmentation of Weed Images in Corn Fields. Comput. Mater. Contin. 2024, 79, 4413. [CrossRef] 24. Gomroki, M.; Benaragama, D.; Henry, C.J.; Badreldin, N.; Gulden, R. CWRepViT-Net: An encoder-decoder deep learning framework with RepViT blocks for crop weed semantic segmentation in soybean fields through their life journey. Smart Agric. Technol. 2025, 12, 101472. [CrossRef] 25. Habib, M.; Sekhra, S.; Tannouche, A.; Ounejjar, Y. New segmentation approach for effective weed management in agriculture. Smart Agric. Technol. 2024, 8, 100505. [CrossRef] 26. Castellano, G.; De Marinis, P.; Vessio, G. Weed mapping in multispectral drone imagery using lightweight vision transformers. Neurocomputing 2023, 562, 126914. [CrossRef] 27. She, X.; Tang, Z.; Pan, X.; Zhao, J.; Liu, W. DBFormer: A Dual-Branch Adaptive Remote Sensing Image Resolution Fine-Grained Weed Segmentation Network. Remote Sens. 2025, 17, 2203. [CrossRef] 28. Xie, E.; Wang, W.; Yu, Z.; Anandkumar, A.; Alvarez, J.M.; Luo, P. Segformer: Simple and Efficient Design for Semantic Segmentation with Transformers. arXiv 2021, arXiv:2105.15203. [CrossRef] 29. Jiang, H.; Chen, Q.; Wang, R.; Du, J.; Chen, T. SWFormer: A scale-wise hybrid CNN-Transformer network for multi-classes weed segmentation. J. King Saud Univ.-Comput. Inf. Sci. 2024, 36, 102144. [CrossRef] 30. Cuimin, S.; Jiang, Z.; Cai, Y.; Zou, C. Dual-branch CNN-transformer synergy with multi-scale striped convolution for sugarcane- weed segmentation. Comput. Electron. Agric. 2025, 239, 111059. [CrossRef] 31. Madeshwar, M.; Priyan Vishnu, M.; Manvizhi, N. Hybrid Vision Transformer and CNN-Based System for Real-Time Weed Detection in Precision Agriculture. In Proceedings of the 2025 International Conference on Emerging Technologies in Engineering Applications (ICETEA), Puducherry, India, 5–6 June 2025. 32. Mei, X.; Li, C.; Jiao, Y.; Zhang, G.; Zhou, L.; Wu, X.; Cai, T. SSMR-Net and Across Feature Mapping Attention are jointly applied to the UAV imagery semantic segmentation task of weeds in early-stage wheat fields. Smart Agric. Technol. 2025, 12, 101077. [CrossRef] 33. Awedat, K. A Dual-Stage Deep Learning Framework for Weed Detection. In Proceedings of the 2025 IEEE International Conference on Electro Information Technology (eIT), Valparaiso, Indiana, USA, 29–31 May 2025. 34. Zhao, F.; Huang, J.; Liu, Y.; Wang, J.; Chen, Y.; Shao, X.; Ma, B.; Xi, D.; Zhang, M.; Tu, Z.; et al. A Deep Learning Approach Combining Super-resolution and Segmentation to Identify Weed and Tobacco in UAV Imagery. In Proceedings of the 9th International Conference on Electronic Technology and Information Science (ICETIS), Hangzhou, China, 17–19 May 2024.

https://doi.org/10.3390/s26102997

Sensors 2026, 26, 2997 20 of 20

35. Tao, J.; Qiao, Q.; Song, J.; Sun, S.; Chen, Y.; Wu, Q.; Liu, Y.; Xue, F.; Wu, H.; Zhao, F. Deep Learning-Driven Automatic Segmentation of Weeds and Crops in UAV Imagery. Sensors 2025, 25, 6576. [CrossRef] 36. Cheong, S.H.; Lee, S.J.; Im, S.J.; Seo, J.; Park, K.R. KDOSS-net: Knowledge distillation-based outpainting and semantic segmenta- tion network for crop and weed images. Plant Phenomics 2025, 7, 100098. [CrossRef] 37. Celikkan, E.; Saberioon, M.; Herold, M.; Klein, N. Semantic Segmentation of Crops and Weeds with Probabilistic Modeling and Uncertainty Quantification. In Proceedings of the IEEE/CVF International Conference on Computer Vision Workshops, Paris, France, 4–6 October 2023. 38. Moazzam, I.S.; Khan, U.S.; Qureshi, W.S.; Nawaz, T.; Kunwar, F. Towards automated weed detection through two-stage semantic segmentation of tobacco and weed dpixels in aerial imagery. Smart Agric. Technol. 2023, 4, 100142. [CrossRef] 39. Bunica-Mihai, A.; Ichim, L.; Popescu, D. Tobacco and Weed Segmentation from Remote Images Using Artificial Intelligence. In Advances in Computational Intelligence, Proceedings of the 18th International Work-Conference on Artificial Neural Networks, IWANN 2025, A Coruña, Spain, 16–18 June 2025; Springer Nature: Berlin/Heidelberg, Germany, 2026; pp. 74–85. 40. Moazzam, I. Tobacco Aerial Dataset. Available online: https://data.mendeley.com/datasets/5dpc5gbgpz/2 (accessed on 3 April 2026). 41. DJI. Mavic Mini—User Manual v1.2. Available online: https://dl.djicdn.com/downloads/Mavic_Mini/20240103/Mavic_Mini_ User_Manual_v1.2_EN.pdf (accessed on 3 April 2026). 42. Liu, Z.; Mao, H.; Wu, C.-Y.; Feichtenhofer, C.; Darrell, T.; Xie, S. A ConvNet for the 2020s. arXiv 2022, arXiv:2201.03545. [CrossRef] 43. Woo, S.; Debnath, S.; Hu, R.; Chen, X.; Liu, Z.; Kweon, I.S.; Saining, X. ConvNeXt V2: Co-designing and Scaling ConvNets with Masked Autoencoders. arXiv 2023, arXiv:2301.00808. [CrossRef] 44. Vasu, P.K.A.; Gabriel, J.; Zhu, J.; Tuzel, O.; Ranjan, A. FastViT: A Fast Hybrid Vision Transformer using Structural Reparameteriza- tion. arXiv 2023, arXiv:2303.14189. [CrossRef] 45. Wang, A.; Chen, H.; Lin, Z.; Han, J.; Ding, G. RepViT: Revisiting Mobile CNN From ViT Perspective. arXiv 2023, arXiv:2307.09283. [CrossRef] 46. Hu, J.; Shen, L.; Sun, G. Squeeze-and-Excitation Networks. In Proceedings of the 2018 IEEE/CVF Conference on Computer Vision and Pattern Recognition, Salt Lake City, UT, USA, 18–22 June 2018; pp. 7132–7141. 47. Cheng, B.; Misra, I.; Schwing, A.G.; Kirillov, A.; Girdhar, R. Masked-attention Mask Transformer for Universal Image Segmentation. arXiv 2021, arXiv:2112.01527. [CrossRef] 48. Carion, N.; Gustafson, L.; Hu, Y.-T.; Debnath, S.; Hu, R.; Suris, D.; Ryali, C.; Alwala, K.V.; Khedr, H.; Huang, A.; et al. SAM 3: Segment Anything with Concepts. arXiv 2026, arXiv:2511.16719. [CrossRef]

Disclaimer/Publisher’s Note: The statements, opinions and data contained in all publications are solely those of the individual author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to people or property resulting from any ideas, methods, instructions or products referred to in the content.

https://doi.org/10.3390/s26102997
