---
workspace_id: SCI-000816
doi: 10.1038/s41598-026-58738-x
title: Deblurring-aware semantic segmentation of crops and weeds in UAV sorghum imagery
  via a UNet-ResNet architecture
authors:
- family_name: Li
  given_name: Qi
  orcid: https://orcid.org/0000-0003-2004-6885
- family_name: Zou
  given_name: Shenshen
  orcid: https://orcid.org/0000-0002-3406-4913
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T01:48:56.079529+00:00'
---

# Deblurring-aware semantic segmentation of crops and weeds in UAV sorghum imagery via a UNet-ResNet architecture

Scientific Reports

https://doi.org/10.1038/s41598-026-58738-x

Article in Press

Deblurring-aware semantic segmentation of  crops and weeds in UAV sorghum imagery via a  UNet-ResNet architecture

Qiyue Li & Shenshen Zou

Received: 18 March 2026

Accepted: 16 June 2026

We are providing an unedited version of this manuscript to give early access to its  findings. Before final publication, the manuscript will undergo further editing. Please  note there may be errors present which affect the content, and all legal disclaimers  apply.

ARTICLE IN PRESS

Cite this article as: Li Q. & Zou S.  Deblurring-aware semantic  segmentation of crops and weeds in UAV  sorghum imagery via a UNet-ResNet  architecture. Sci Rep (2026). https://doi. org/10.1038/s41598-026-58738-x

If this paper is publishing under a Transparent Peer Review model then Peer  Review reports will publish with the final article.

© The Author(s) 2026. Open Access This article is licensed under a Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International  License, which permits any non-commercial use, sharing, distribution and reproduction in any medium or format, as long as you give appropriate credit  to the original author(s) and the source, provide a link to the Creative Commons licence, and indicate if you modified the licensed material. You do  not have permission under this licence to share adapted material derived from this article or parts of it. The images or other third party material in this  article are included in the article’s Creative Commons licence, unless indicated otherwise in a credit line to the material. If material is not included in the  article’s Creative Commons licence and your intended use is not permitted by statutory regulation or exceeds the permitted use, you will need to obtain  permission directly from the copyright holder. To view a copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/4.0/.

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

Deblurring-Aware Semantic Segmentation of Crops and Weeds in UAV Sorghum Imagery via a

UNet-ResNet Architecture

Qiyue Li1 and Shenshen Zou1*

1College of Plant Protection, Shandong Agricultural University, No.61 Daizong Street, Taian, 271017, Shandong Province, China.

*Corresponding author(s). E-mail(s): zouss@sdau.edu.cn; Contributing authors: 17686683865@163.com;

ARTICLE IN PRESS


## Abstract

Automated monitoring of weed infestation is essential for precision agriculture, where reliable crop–weed discrimination underpins site-specific intervention. This study presents a semantic segmentation framework based on UNet with a ResNet encoder backbone that delineates three semantic categories—background, crop (sorghum), and weed—within a single inference pass. A systematic compari- son across four ResNet encoder variants (ResNet-18, ResNet-34, ResNet-50, and ResNet-101) reveals that ResNet-34 achieves the highest mean Dice Score of 0.9198 and that accuracy does not increase with depth—the deeper ResNet- 50 and ResNet-101 score slightly lower, consistent with capacity saturation and mild overfitting on the limited training set. To address image quality degrada- tion prevalent in UAV-based agricultural imaging, an explicit deblurring module based on NAFNet is integrated prior to segmentation through a restoration-aware training protocol, improving the mean Dice Score on the motion-blurred test sub- set by 27.7% in relative terms over the strongest baseline without restoration and yielding the best combined-set accuracy (0.8223 mDS). Comprehensive ablation experiments identify decoder depth (full-resolution progressive upsampling) and encoder–decoder skip connections as the two most critical components, whose removal lowers the mean Dice Score by 5.18 and 3.51 percentage points respec- tively, whereas ImageNet pre-training and dropout have negligible effect at this dataset scale. A complexity analysis based on parameter count and multiply– accumulate operations (MACs) shows that the segmentation network (24.4 M parameters, 1.97 GMACs) is comparable to standard CNN segmentation base- lines, suggesting the plausibility of deployment on resource-constrained UAV

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

platforms; a direct on-device throughput validation on embedded NVIDIA Jetson hardware was not performed and is left for future work.

Keywords: Semantic segmentation, Crop–weed discrimination, UNet-ResNet architecture, Image deblurring, Precision agriculture


## 1 Introduction

Ensuring crop health is fundamental to global food security, and weed competition is a major contributor to the estimated 20–40% of annual crop yield losses worldwide caused by biotic stresses [1]. Traditional approaches to monitoring weeds in the field rely heavily on manual scouting by trained agronomists, a process that is labour- intensive, time-consuming, and inherently limited in spatial coverage. With the rapid expansion of precision agriculture technologies, particularly the widespread adoption of unmanned aerial vehicles (UAVs) equipped with high-resolution imaging sensors, it has become feasible to acquire detailed visual data of crop fields at unprecedented spatial and temporal scales [2]. This paradigm shift has created an urgent demand for automated computer vision systems capable of analysing agricultural imagery and providing actionable insights for timely intervention.

Semantic segmentation, which assigns a categorical label to every pixel in an image, has emerged as a particularly powerful tool for agricultural vision tasks because it provides not only the presence or absence of a target but also its precise spatial extent and boundary [3]. Unlike image-level classification methods that produce a single diagnostic label per image, pixel-wise segmentation enables targeted and site-specific management strategies, such as variable-rate herbicide application for weeds, thereby reducing chemical usage and minimising environmental impact. The encoder–decoder architecture pioneered by UNet [4] has proven especially effective for dense prediction tasks in biomedical and agricultural domains, owing to its symmetric structure with skip connections that preserve fine-grained spatial details while leveraging high-level semantic features extracted by the encoder.

ARTICLE IN PRESS

Deep residual networks (ResNets) [5, 6] have further advanced the capability of visual feature extraction by introducing identity shortcut connections that alleviate the degradation problem in very deep networks, enabling the training of substantially deeper models with improved representational capacity. When employed as encoder backbones within the UNet framework and initialised with weights pre-trained on large-scale image classification datasets such as ImageNet [7], ResNet-based encoders provide robust hierarchical feature representations that transfer effectively to agricul- tural imagery, even when domain-specific labelled data is scarce. This combination of the UNet decoder with a ResNet encoder offers a compelling balance between seg- mentation accuracy and computational efficiency, making it well-suited for practical deployment on resource-constrained platforms such as UAV-mounted edge computing devices.

Meanwhile, real-world agricultural imaging conditions frequently introduce image quality degradation, most notably motion blur caused by UAV platform movement

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

and wind-induced camera shake [8]. Motion blur disproportionately affects fine-detail segmentation accuracy by smearing edges and textures that serve as discriminative features for distinguishing closely related categories. Addressing this challenge through explicit image restoration prior to segmentation represents a promising strategy for improving model robustness under degraded conditions, yet its integration with crop– weed segmentation has received limited systematic investigation.

Despite significant progress in applying deep learning to agricultural vision tasks, several gaps remain in the crop–weed segmentation literature. First, most existing agricultural segmentation studies employ relatively simple encoder architectures or lack a systematic comparison across different backbone depths, leaving practitioners without clear guidance on how to balance model complexity against segmentation per- formance for a given dataset scale [9]. Second, the robustness of segmentation models to image quality degradation, particularly motion blur prevalent in UAV-captured imagery, has been insufficiently addressed; prior work has either focused exclusively on sharp imagery or treated image restoration and segmentation as entirely disjoint problems [10]. Third, the interaction between encoder depth and the limited scale of pixel-wise annotated agricultural datasets is rarely characterised, even though it directly governs the risk of overfitting [11].

To address these limitations, this study develops a semantic segmentation frame- work based on the UNet-ResNet architecture for crop–weed discrimination in UAV sorghum imagery. The contribution does not lie in the invention of an entirely new convolutional operator, but rather in a careful, reproducible characterisation of the architecture and in the task-driven coupling of restoration and segmentation under a unified probabilistic objective. Specifically, the framework (i) introduces a restoration- aware training protocol in which the deblurring stage and the segmentation backbone are jointly calibrated on a paired sharp/blurred distribution, so that the restored inter- mediate representation is optimised for downstream segmentability rather than for perceptual image fidelity alone; and (ii) provides a depth-vs-data-scale ablation prin- ciple that empirically characterises the saturation point of ResNet-family encoders on small-to-medium agricultural datasets. The principal contributions of this work are threefold:

ARTICLE IN PRESS


## 1. A UNet-ResNet crop–weed segmentation model that delineates background,

crop (sorghum), and weed within a single inference pass, evaluated end-to-end on
a public UAV sorghum dataset.
2. A systematic comparative and ablation study across four ResNet encoder
variants (ResNet-18, ResNet-34, ResNet-50, and ResNet-101) that quantifies
the impact of encoder depth, ImageNet pre-training, skip connections, decoder
design, and dropout regularisation on segmentation performance, providing prin-
cipled guidance for architectural selection under varying computational and data
constraints.
3. An
integrated
deblurring–segmentation
pipeline that incorporates an
explicit image restoration module (NAFNet) prior to semantic segmentation,
improving robustness under motion-blurred imaging conditions typical of UAV-
based crop monitoring while maintaining competitive performance on sharp
imagery.

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

We emphasise that the value of this work is therefore derived primarily from the systematic encoder-depth characterisation, the restoration-aware integration strategy, and a deployment-oriented complexity analysis (parameters and MACs) for resource- constrained UAV platforms, rather than from the introduction of a fundamentally new network component.


## 2 Related Work


### 2.1 Semantic Segmentation in Agricultural Vision

Semantic segmentation in agricultural applications has emerged as a critical tech- nology for precision crop management, enabling automated identification and spatial localization of crops, weeds, and soil background [12]. Traditional approaches to in- field monitoring primarily relied on classification-based methods that assigned a single label to an entire image, thereby lacking the spatial granularity necessary for targeted intervention strategies [13]. The transition from image-level classification to dense pixel-wise prediction has fundamentally transformed the capability of automated crop monitoring systems, allowing practitioners to precisely delineate target regions and quantify their spatial extent [14].

Early semantic segmentation architectures for agricultural imagery predominantly employed fully convolutional networks with relatively shallow encoder structures, which struggled to capture the multi-scale contextual information essential for distin- guishing visually similar categories such as crop seedlings and morphologically similar weed species at early growth stages [15]. The introduction of encoder-decoder archi- tectures with symmetric skip connections marked a significant advancement, enabling the fusion of high-level semantic features with fine-grained spatial details preserved from earlier network layers. This architectural paradigm has proven particularly effec- tive for agricultural applications where both global context and local texture patterns contribute to accurate diagnosis [16].

ARTICLE IN PRESS


### 2.2 Deep Residual Networks and Transfer Learning

Residual learning mechanisms have revolutionized deep network training by mitigating the degradation problem associated with increasing network depth. The incorpora- tion of identity shortcuts allows gradients to flow directly through the network during backpropagation, enabling the training of substantially deeper models without suffer- ing from vanishing gradients or representational bottlenecks [17]. In the context of crop monitoring, deeper residual networks have demonstrated superior capacity for learning discriminative features that distinguish between morphologically similar plant categories, such as early-stage crop seedlings versus visually similar weed species [18].

Transfer learning from large-scale image classification datasets has become a standard practice in agricultural computer vision, particularly when domain-specific training data is limited [19]. Pre-trained encoder backbones provide robust low-level feature extractors that capture fundamental visual primitives such as edges, textures, and color gradients, which transfer effectively across domains despite the distribu- tional shift between natural images and agricultural imagery [20]. The fine-tuning of

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

pre-trained networks on crop-specific datasets allows models to adapt these general visual representations to the unique characteristics of plant tissues, while requiring substantially fewer labeled samples than training from random initialization [7].


### 2.3 Weed Detection and Segmentation

Weed detection and segmentation represents a particularly challenging problem due to the high degree of visual similarity between crop plants and certain weed species, especially during early growth stages when morphological differences are minimal [21]. Traditional color-based segmentation methods that simply separated green vegetation from soil background proved inadequate for crop-weed discrimination, necessitating the development of learning-based approaches capable of capturing subtle differences in leaf shape, growth patterns, and spatial arrangement [22]. Multi-class segmenta- tion frameworks that simultaneously identify crops and multiple weed species have demonstrated superior performance compared to binary crop-versus-weed classifiers, as the explicit modeling of inter-weed variability improves the decision boundaries for all categories [23].


### 2.4 Class Imbalance in Agricultural Segmentation

A recurring difficulty in agricultural segmentation is severe class imbalance: back- ground and soil typically dominate the image while the agronomic targets of interest occupy only a small fraction of pixels, posing significant challenges for standard cross-entropy loss functions that implicitly assume balanced class distributions [24]. This imbalance is particularly acute in early-growth-stage UAV imagery, where small, sparsely distributed crop and weed seedlings cover only a few percent of the scene, motivating the use of mean-class evaluation metrics that weight all categories equally rather than favouring the majority background class [25].

ARTICLE IN PRESS


### 2.5 Image Quality and Robustness Challenges

Image quality degradation presents a persistent challenge in real-world agricultural imaging applications, particularly for UAV-based aerial imagery where motion blur, varying illumination, and atmospheric scattering frequently compromise image clar- ity [26]. Motion blur induced by platform movement or wind-induced camera shake disproportionately affects fine-detail segmentation accuracy, as the spatial smearing of edges and textures degrades the discriminative features that distinguish between closely related categories. Domain adaptation and explicit image restoration strate- gies have emerged as complementary approaches to improving model robustness under degraded imaging conditions, with recent work exploring the benefits of decoupling the restoration and segmentation tasks versus end-to-end joint optimization [27].


### 2.6 Advanced Architectural Components

The integration of attention mechanisms and spatial pyramid pooling modules has shown promise for enhancing multi-scale feature aggregation in agricultural segmen- tation tasks [28]. Attention modules enable the network to dynamically weight feature

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

channels or spatial regions according to their relevance for the current input, poten- tially improving discrimination of small or low-contrast target regions. Spatial pyramid pooling captures features at multiple receptive field scales simultaneously, providing explicit multi-scale reasoning that complements the implicit scale hierarchy learned through successive convolutional layers. These architectural refinements have demon- strated particular value for handling the scale variability inherent in agricultural imagery, where weed patches may span from individual sub-centimeter seedlings to large overlapping clusters.


### 2.7 Deployment and Dataset Considerations

Real-time inference requirements for practical deployment on edge computing plat- forms impose stringent constraints on model complexity and computational cost [29]. While deeper networks generally achieve superior accuracy, their increased parameter counts and computational demands may render them impractical for deployment on resource-constrained UAV platforms or mobile devices used for in-field scouting. The exploration of efficient network architectures that balance segmentation accuracy with inference speed remains an active area of research, with techniques such as depthwise separable convolutions, network pruning, and knowledge distillation offering potential pathways toward practical real-time systems [30].

The development of large-scale annotated datasets for agricultural segmentation has been hindered by the substantial labor required for pixel-wise annotation and the need for domain expertise to accurately identify and delineate crop and weed regions [31]. Semi-supervised and weakly supervised learning approaches that leverage abun- dant unlabeled imagery or coarse image-level labels represent promising directions for scaling up training data availability. Additionally, synthetic data generation through procedural modeling or domain randomization has been explored as a means of aug- menting limited real-world datasets, though the sim-to-real transfer gap remains a significant challenge for ensuring model performance on authentic field imagery [32].

ARTICLE IN PRESS


## 3 Methodology


### 3.1 Overall Model Architecture

The proposed crop–weed segmentation model adopts an encoder-decoder architecture based on the U-Net framework, as illustrated in Fig. 1. The network takes an RGB image of arbitrary spatial resolution as input and produces a dense pixel-wise predic- tion map with three semantic categories, namely background, crop (sorghum), and weed. Although the architecture is described for a generic input of size H × W, all experiments in this study operate on 128 × 128 image patches (i.e., H = W = 128); the fractional spatial dimensions annotated in the architectural diagrams (Figs. 1, 3, and 5) therefore correspond to feature-map sizes of 64 × 64 at H/2, 32 × 32 at H/4, 16 × 16 at H/8, 8 × 8 at H/16, and 4 × 4 at H/32 in our experimental setting. The encoder path employs a ResNet18 backbone pretrained on ImageNet to extract hierarchical visual representations at multiple scales. The input image first passes through a stem block consisting of a seven-by-seven convolutional layer followed by

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

Fig. 1 Overall architecture of the proposed U-Net-based crop–weed segmentation model. The encoder (left) utilizes a ResNet18 backbone pretrained on ImageNet to extract multi-scale features through four residual stages. The decoder (right) progressively restores spatial resolution through five decoder blocks with skip connections from the encoder. A segmentation head maps the final 16- channel features to three output classes: background, crop (sorghum), and weed.

ARTICLE IN PRESS

batch normalization, ReLU activation, and max pooling, which reduces the spatial resolution to one quarter of the original size and yields 64-channel feature maps. Four successive residual stages then progressively downsample the feature maps while increasing the channel depth. Specifically, Layer 1 maintains 64 channels at one quarter resolution, Layer 2 produces 128 channels at one eighth resolution, Layer 3 produces 256 channels at one sixteenth resolution, and Layer 4 serves as the bottleneck with 512 channels at one thirty-second resolution. Each residual stage is composed of two BasicBlock modules, where each BasicBlock contains two three-by-three convolutional layers with batch normalization and ReLU activation, along with a shortcut connection that facilitates gradient flow during training. When the spatial dimensions or channel numbers change between stages, a learnable one-by-one convolutional projection is applied along the shortcut path to match the dimensions.

The decoder path progressively recovers spatial resolution through five consecutive decoder blocks. Each decoder block first upsamples the feature map by a factor of two using nearest-neighbor interpolation, then concatenates it with the corresponding skip connection from the encoder to preserve fine-grained spatial details, and finally refines the combined features through two successive three-by-three convolutional layers each followed by batch normalization and ReLU activation. Decoder Block 1 receives the 512-channel bottleneck features together with the 256-channel skip connection from Layer 3, producing 256 channels at one sixteenth resolution. Decoder Block 2 fuses its input with the 128-channel features from Layer 2 to yield 128 channels at one eighth resolution. Decoder Block 3 incorporates the 64-channel features from Layer 1

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

and outputs 64 channels at one quarter resolution. Decoder Block 4 concatenates the 64-channel features from the stem block and reduces the channel dimension to 32 at one half resolution. Decoder Block 5 operates without a skip connection and further compresses the representation to 16 channels while restoring the feature map to the full input resolution.

At the top of the decoder, a lightweight segmentation head consisting of a dropout layer with a rate of 0.1 followed by a three-by-three convolutional layer maps the 16- channel feature representation to the final three-channel output, where each channel corresponds to one of the three target semantic categories. The decoder and segmen- tation head weights are initialized using Kaiming uniform initialization and Xavier uniform initialization, respectively, to ensure stable training convergence. During infer- ence, the class with the highest activation at each spatial location is selected via an argmax operation to produce the final segmentation map.


### 3.2 Residual Learning Modules

The backbone of the proposed network is constructed upon residual learning mod- ules, which effectively mitigate the degradation problem commonly observed in deep neural networks. Two variants of residual blocks are employed depending on the net- work depth: the Basic Block for shallower architectures (e.g., ResNet-18/34) and the Bottleneck Block for deeper ones (e.g., ResNet-50/101), as illustrated in Fig. 2. In the Basic Block, the input feature map x ∈RCin×H×W undergoes two successive 3 × 3 convolutional layers, each followed by batch normalization, with a ReLU activation applied after the first. The transformation can be expressed as:

ARTICLE IN PRESS





 



W2 ∗σ(BN(W1 ∗x))

+ S(x)

y = σ

BN

(1)

where W1, W2 ∈RCout×Cin×3×3 denote the learnable convolutional kernels, BN(·) represents batch normalization, σ(·) is the ReLU activation function, ∗denotes the convolution operation, and S(x) is an optional projection shortcut that adapts the spatial resolution and channel dimensionality of the identity mapping when Cin̸ = Cout or the stride s > 1.

For deeper network configurations, the Bottleneck Block is adopted to reduce com- putational cost while maintaining representational capacity. As shown in the right part of Fig. 2, this module follows a 1 × 1 →3 × 3 →1 × 1 convolutional structure, where the first 1 × 1 convolution compresses the channel dimension from Cin to a reduced intermediate dimension Cmid, the 3 × 3 convolution performs spatial feature extraction at the compressed dimensionality with an optional dilation factor d, and the final 1 × 1 convolution restores the output to the target channel dimension Cout. The forward computation of the Bottleneck Block is formulated as:





 



W3 ∗σ(BN(W2 ∗σ(BN(W1 ∗x))))

+ S(x)

y = σ

BN

(2)

where W1 ∈RCmid×Cin×1×1, W2 ∈RCmid×Cmid×3×3, and W3 ∈RCout×Cmid×1×1. Notably, both block types support dilated convolutions by incorporating a dilation

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

factor d into the 3 × 3 convolutional layers, which enlarges the effective receptive field to (2d + 1) × (2d + 1) without increasing the number of parameters. This design is particularly beneficial for dense prediction tasks such as semantic segmentation, where capturing multi-scale contextual information is critical. The shortcut projection S(·), when required, is implemented as a 1 × 1 convolution followed by batch normalization to ensure dimensional consistency between the residual branch and the identity branch before element-wise addition. In both block types, the element-wise addition of the main branch output and the shortcut connection is followed by a final ReLU activation to produce the output feature map y ∈RCout×H′×W ′.

ARTICLE IN PRESS

Fig. 2 Architecture of the two residual learning modules employed in the proposed network. Left: the Basic Block used in ResNet-18/34, consisting of two 3×3 convolutional layers with an identity shortcut connection. Right: the Bottleneck Block used in ResNet-50/101, adopting a 1 × 1 →3 × 3 →1 × 1 structure that compresses the channel dimension to Cmid for efficient computation. Both blocks incorporate an optional shortcut projection S(x) via 1×1 convolution with batch normalization when the input and output dimensions differ, and the 3 × 3 convolution in the Bottleneck Block supports dilated convolution with dilation factor d for enlarged receptive fields.


### 3.3 ResNet Encoder Backbone Architecture

The proposed segmentation framework adopts the ResNet family [5] as the encoder backbone for hierarchical feature extraction. Four variants are implemented, namely ResNet-18, ResNet-34, ResNet-50, and ResNet-101, which share a unified architectural paradigm but differ in depth and block type. All encoders begin with a stem module consisting of a 7×7 convolutional layer with stride 2, followed by batch normalization and ReLU activation, which reduces the spatial resolution of the input image I ∈ R3×H×W by a factor of two. A subsequent 3 × 3 max-pooling operation with stride 2

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

further downsamples the feature map, yielding the initial representation:





∈R64× H


## 4 × W

4
(3)

 

BN(Wstem ∗I)

F0 = MaxPool

σ

where Wstem ∈R64×3×7×7 denotes the stem convolution kernel, and the output spatial dimensions are reduced to H


## 4 × W

4 after the two successive stride-2 operations.
The overall architecture of the ResNet encoder backbone is illustrated in Fig. 3.Fol-
lowing the stem module, the encoder is organized into four sequential stages (Layer 1
through Layer 4), each comprising a stack of residual blocks. The shallower variants,
ResNet-18 and ResNet-34, employ the Basic Block described in the previous sub-
section, while the deeper variants, ResNet-50 and ResNet-101, utilize the Bottleneck
Block to achieve greater representational capacity with manageable computational
overhead. At each stage transition (from Layer i to Layer i+1), the spatial resolution
is halved via a stride-2 convolution and the channel dimension is doubled, producing
a multi-scale feature pyramid. The output of the i-th stage can be expressed as:

Fi = Li(Fi−1) ∈RCi× H 2i+1 × W 2i+1 , i = 1, 2, 3, 4 (4)

where Li(·) denotes the composite transformation of the i-th stage, and the chan- nel dimensions follow the progression Ci ∈{64, 128, 256, 512} for ResNet-18/34 and Ci ∈{256, 512, 1024, 2048} for ResNet-50/101. When the input and output dimensions of a stage differ, a learnable shortcut projection Si(·) implemented as a 1 × 1 convo- lution with batch normalization is applied to the first block of that stage to ensure compatibility for the residual addition.

ARTICLE IN PRESS

The specific layer configurations for each variant are summarized in Table 1. ResNet-18 employs a [2, 2, 2, 2] block arrangement, ResNet-34 extends this to [3, 4, 6, 3], while ResNet-50 and ResNet-101 adopt [3, 4, 6, 3] and [3, 4, 23, 3] Bottleneck blocks, respectively. The total depth D of the network can be computed as:

4 X

ni × k + 1 (5)

D = 1 +

i=1

where ni is the number of blocks in the i-th stage, k = 2 for Basic Blocks and k = 3 for Bottleneck Blocks, and the additional terms account for the stem convolution and the final classification layer. Notably, the significantly deeper Layer 3 in ResNet-101 (containing 23 Bottleneck blocks compared to 6 in ResNet-50) substantially increases the network’s capacity for learning complex feature representations, which is partic- ularly advantageous for fine-grained semantic segmentation tasks involving visually similar categories.

During the forward pass, the encoder stores the intermediate feature maps from each stage in an ordered dictionary, yielding the multi-scale feature set {F0, F1, F2, F3, F4}. These hierarchical features capture information at progressively coarser spatial resolutions and richer semantic levels, forming the basis for subse- quent decoder modules to perform multi-scale feature fusion and dense prediction.

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

The complete forward process of the encoder can be formulated as:

{F0, F1, F2, F3, F4} = Encoder(I; Θenc) (6)

where Θenc represents the learnable parameters of the encoder. To accelerate con- vergence and improve generalization, all encoder variants support initialization with ImageNet [7] pre-trained weights, with the fully connected classification head removed prior to weight loading. This transfer learning strategy enables the encoder to lever- age rich low-level and mid-level visual representations learned from large-scale image classification, which are highly transferable to downstream dense prediction tasks. During fine-tuning, all encoder parameters remain trainable to allow domain-specific adaptation.


> **Table 1 Configuration of the ResNet encoder variants employed in the proposed**

> framework. “Block Type” indicates the residual module used, and [n1, n2, n3, n4] denotes
the number of blocks in each of the four stages.

Encoder Block Type Block Config Output Channels Params (M) ResNet-18 Basic [2, 2, 2, 2] [64, 128, 256, 512] 11.2 ResNet-34 Basic [3, 4, 6, 3] [64, 128, 256, 512] 21.3 ResNet-50 Bottleneck [3, 4, 6, 3] [256, 512, 1024, 2048] 23.5 ResNet-101 Bottleneck [3, 4, 23, 3] [256, 512, 1024, 2048] 42.5

ARTICLE IN PRESS


### 3.4 Decoder Architecture and Segmentation Head

The decoder pathway of the proposed UNet architecture is designed to progressively recover spatial resolution while integrating multi-scale contextual information from the encoder through skip connections, as illustrated in Fig. 4. Each decoder stage com- prises a dedicated decoder block that first applies nearest-neighbor upsampling with a factor of two to the incoming feature map, thereby doubling its spatial dimensions. When a corresponding skip connection from the encoder is available, the upsampled feature map is concatenated along the channel dimension with the skip feature map, enabling the network to fuse high-level semantic information with fine-grained spatial details. This concatenated representation is then processed by two successive convo- lutional layers, each consisting of a 3 × 3 convolution followed by batch normalization and a rectified linear unit (ReLU) activation function. Formally, given an input feature map Fin ∈RCin×H×W and a skip connection feature map Fskip ∈RCskip×2H×2W , the output of each decoder block can be expressed as:

Fup = Upsample(Fin), Fcat = Concat(Fup, Fskip), (7)





 

Fout = ReLU

Conv3×3(ReLU(BN(Conv3×3(Fcat))))

, (8)

BN

where Conv3×3(·) denotes a convolution operation with kernel size 3 × 3, stride of 1, and zero-padding of 1, BN(·) represents batch normalization, and the output feature

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

Fig. 3 Overall architecture of the ResNet encoder backbone. The top row illustrates the complete encoding pipeline: the input image first passes through a stem module (7×7 convolution with stride 2 followed by 3×3 max pooling with stride 2) to produce the initial feature map F0, and then traverses four sequential stages (Layer 1 through Layer 4), each performing stride-2 downsampling to yield the multi-scale feature set {F0, F1, F2, F3, F4} for the decoder. The bottom-left depicts the Basic Block used in ResNet-18/34, which consists of two successive 3×3 convolutions with an identity (or projection) shortcut. The bottom-right depicts the Bottleneck Block used in ResNet-50/101, which adopts a 1×1 →3×3 →1×1 structure to first reduce, then spatially process, and finally expand the channel dimensions. The accompanying table summarizes the stage configuration and output channel dimensions for each ResNet variant.

ARTICLE IN PRESS

map satisfies Fout ∈RCout×2H×2W . The convolution layers are configured without bias terms since the subsequent batch normalization inherently provides the learnable shift parameter, which reduces redundant parameters and stabilizes training.

The complete decoder is composed of five sequentially stacked decoder blocks, each operating at a progressively increasing spatial resolution. As shown in the lower portion of Fig. 4, the feature maps from the encoder are reversed in order such that the deepest (lowest-resolution) feature map serves as the initial input, and the remaining encoder features are consumed as skip connections in a coarse-to-fine manner. Let {E1, E2, E3, E4, E5, E6} denote the encoder features ordered from highest to lowest resolution; the decoder processes them as:

Di = Bi(Di−1, E6−i) , i = 1, 2, . . . , 5, (9)

where D0 = E6 is the bottleneck feature and Bi(·, ·) represents the i-th decoder block. This cascaded structure ensures that each decoding stage benefits from both the semantically rich upsampled features and the spatially precise encoder representations, progressively refining the segmentation map toward the original input resolution.

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

Fig. 4 Overview of the proposed decoder architecture and segmentation head. The upper panel depicts the detailed internal structure of a single decoder block Bi, which performs nearest-neighbor upsampling followed by channel-wise concatenation with the encoder skip connection and two suc- cessive Conv–BN–ReLU modules. The lower-left panel illustrates the macro-level decoder pathway, where five cascaded decoder blocks progressively restore spatial resolution from the bottleneck feature E6 to the full-resolution representation D5 by consuming encoder features E5 through E1 as skip connections. The lower-right panel shows the lightweight segmentation head, consisting of a dropout layer (p = 0.1) and a 3×3 convolution that maps the decoded features to the K-class prediction map Y ∈RK×H0×W0.

ARTICLE IN PRESS

At the terminal end of the decoder, a lightweight segmentation head is employed to project the decoded feature representation into the target label space. The head consists of a dropout layer with a drop probability of p = 0.1, which serves as a regu- larization mechanism to mitigate overfitting, followed by a single 3 × 3 convolutional layer that maps the Cdec-channel decoded feature map to a K-channel output, where K denotes the number of semantic classes. The final prediction map Y ∈RK×H0×W0 is thus obtained as:

Y = Conv3×3(Dropout0.1(D5)) . (10)

All convolutional and batch normalization layers in the decoder are initialized using Kaiming uniform initialization with fan-in mode under the ReLU nonlinearity assump- tion, while the segmentation head adopts Xavier uniform initialization, following established practices that promote stable gradient flow and accelerate convergence during the early stages of training.


### 3.5 UNet Segmentation Network with ResNet Encoder

In this study, we adopt a UNet-based semantic segmentation framework tailored for crop–weed image analysis, encompassing three target classes: background, crop (sorghum), and weed. The overall architecture follows the classical encoder–decoder

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

paradigm, wherein a pre-trained ResNet backbone serves as the feature encoder and a symmetric expanding path reconstructs dense pixel-wise predictions, as illustrated in Fig. 5. Let the input image be denoted as X ∈R3×H×W , where H and W represent the spatial height and width, respectively. The encoder progressively extracts a hier- archy of multi-scale feature maps {Fl}L

l=0 through a series of residual stages, where L = 4 corresponds to the deepest encoding layer. Formally, the feature extraction process at each stage l can be expressed as:

Fl = El(Fl−1), l = 1, 2, . . . , L, (11)

where El(·) denotes the l-th residual stage of the encoder and F0 is obtained from the initial convolution, batch normalisation, and max-pooling operations applied to the raw input X. The spatial resolution of Fl is reduced by a factor of 2l relative to the original input, while the channel dimension increases to capture increasingly abstract semantic representations.

The decoder follows a bottom-up path that progressively recovers spatial resolution through a sequence of upsampling and feature fusion operations. At each decoder stage k (k = 1, 2, . . . , K with K = 5), the feature map from the preceding decoder block is first upsampled via nearest-neighbor interpolation and then concatenated with the corresponding encoder skip connection. As shown in the left half of Fig. 5, the encoder stages E1 through E4 produce feature maps F1 to F4 at progressively reduced resolutions of H/4 × W/4 down to H/32 × W/32, which are then forwarded to the decoder via lateral skip connections. Specifically, let Dk denote the output of the k-th decoder block; the decoding process is formulated as:

ARTICLE IN PRESS

Dk = Gk([ Up(Dk−1); FL−k ]) , k = 1, 2, . . . , K −1, (12)

where Up(·) represents nearest-neighbor upsampling by a factor of two, [ · ; · ] denotes channel-wise concatenation along the feature axis, and Gk(·) is a convolutional sub- block composed of two successive layers of 3×3 convolution, batch normalisation, and ReLU activation. For the final decoder stage where no skip connection is available, the formulation simplifies to DK = GK(Up(DK−1)). Each convolutional sub-block Gk, whose internal structure is depicted in the bottom-right inset of Fig. 5, can be written element-wise as:













W(2)

W(1)

k ∗Z + b(1)

+ b(2)

Gk(Z) = σ

k ∗σ

, (13)

BN

BN

k

k

where W(i)

k and b(i)

k are the learnable convolutional weights and biases of the i-th layer within stage k, ∗denotes the convolution operation, BN(·) is batch normalisation, and σ(·) is the ReLU activation function. This dual-convolution design strengthens the non-linear mapping capacity and facilitates the gradual refinement of decoded features at each resolution level.

To accommodate different computational budgets and model capacities, the encoder supports four ResNet variants, namely ResNet-18, ResNet-34, ResNet-50, and ResNet-101. For the lightweight variants (ResNet-18 and ResNet-34), which employ

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

basic residual blocks, the decoder channel configuration is set as (Cin, Cskip, Cout) ∈ {(512, 256, 256), (256, 128, 128), (128, 64, 64), (64, 64, 32), (32, 0, 16)} from the deepest to the shallowest stage. For the deeper variants (ResNet-50 and ResNet-101) that utilise bottleneck residual blocks with expanded channel dimensions, the configuration is adjusted to (2048, 1024, 256), (256, 512, 128), (128, 256, 64), (64, 64, 32), (32, 0, 16). This flexible design ensures that the decoder capacity is proportionally matched to the encoder’s representational power, thereby maintaining a balanced information flow throughout the network.

The final segmentation prediction is produced by a lightweight segmentation head applied to the last decoder output DK ∈RCK×H×W , where CK = 16, as depicted in the rightmost portion of Fig. 5. The head consists of a single 3 × 3 convolutional layer followed by upsampling to restore the original spatial resolution, yielding the class probability map:

ˆY = Ups(Wseg ∗DK + bseg) ∈RNc×H×W , (14)

where Nc = 3 is the number of semantic classes, Wseg and bseg are the parame- ters of the segmentation convolution, and Ups(·) denotes nearest-neighbor upsampling by a factor s to match the input resolution. The pixel-wise class prediction is then obtained via ˆyh,w = arg maxc ˆYc,h,w. The output prediction map assigns each pixel to one of three colour-coded categories—background (black), crop (green), and weed (red)—enabling intuitive visual interpretation of the segmentation results. All encoder weights are initialised from ImageNet pre-trained models to facilitate transfer learning, while the decoder and segmentation head parameters are initialised using the Kaim- ing uniform scheme to ensure stable gradient propagation during the early stages of training.

ARTICLE IN PRESS


### 3.6 NAFNet Deblurring Module: Principle and Integration

To explicitly handle the motion blur prevalent in UAV-captured agricultural imagery, we integrate a Nonlinear Activation Free Network (NAFNet) [33] as a dedicated image restoration front-end prior to the segmentation backbone. NAFNet is selected over alternative restoration networks (e.g., MPRNet, Restormer) for three reasons: (i) it removes all nonlinear activation functions and replaces them with simple gating mech- anisms, leading to substantially lower latency on edge devices; (ii) its plain block design avoids the multi-stage and transformer-based bottlenecks that would inflate UAV inference cost; and (iii) it has demonstrated state-of-the-art performance on stan- dard motion-deblurring benchmarks such as GoPro and HIDE, which share imaging statistics with our UAV scenario.

Module Principle. NAFNet adopts a four-level hierarchical encoder–decoder structure built from stacked NAF Blocks. Each NAF Block replaces the conventional Conv–LayerNorm–ReLU–Conv design with a SimpleGate operator and a Simplified Channel Attention (SCA) module. Given an intermediate feature map X ∈RC×H×W , the SimpleGate operator first splits X along the channel dimension into two halves

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

Fig. 5 Overall architecture of the proposed UNet segmentation network with a pre-trained ResNet encoder for crop–weed image analysis. The left column illustrates the encoder pathway consisting of an initial convolution block and four residual stages (E1–E4) that progressively downsample the input from H ×W to H/32×W/32. The right column depicts the decoder pathway comprising five decoder blocks (G1–G5) that recover spatial resolution via nearest-neighbor upsampling and skip-connection concatenation. The bottom-right inset details the internal structure of the double convolution sub- block Gk(Z), consisting of two cascaded 3 × 3 Conv–BN–ReLU layers. The segmentation head maps the final 16-channel decoder output to Nc = 3 class predictions through a 3 × 3 convolution followed by nearest-neighbor upsampling to the original resolution. Blue and orange blocks represent encoder and decoder feature maps, respectively.

ARTICLE IN PRESS

X1, X2 ∈RC/2×H×W and computes their element-wise product:

SimpleGate(X) = X1 ⊙X2, (15)

which provides nonlinear coupling between channels without any activation function and reduces the channel count to C/2. The SCA module subsequently performs global average pooling and a 1 × 1 convolution to obtain a channel-wise re-weighting vector w ∈RC/2, which is broadcast and multiplied with the SimpleGate output. The overall NAF Block transformation can be written as:

Y = X + Conv1×1(SCA(SimpleGate(Conv(LN(X))))) , (16)

where LN(·) denotes Layer Normalisation and the residual connection preserves low- frequency content. The deblurring objective is a PSNR-oriented L1 loss between the restored output ˆI and the sharp ground truth Isharp:

ˆI −Isharp

Ldeblur =

1. (17)

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

Integration with the Segmentation Network. Rather than treating the deblurring and segmentation networks as two completely independent modules exe- cuted in sequence, we adopt a cascaded restoration-aware integration strategy. The motion-blurred input Iblur is first restored by NAFNet to produce ˆI = R(Iblur; ΘR), which is then fed into the UNet-ResNet segmentation network S(·; ΘS) to obtain the final three-class prediction ˆY = S(ˆI; ΘS). The two networks are trained in two stages: (1) the deblurring network is pre-trained on the paired sharp/blurred patches using Ldeblur; (2) the segmentation network is then fine-tuned on the restored images while ΘR is jointly updated with a small learning rate using a task-driven composite loss:









S(ˆI), Y

ˆI, Isharp

Ltotal = Lseg

+ λLdeblur

, (18)

where Lseg is the pixel-wise cross-entropy loss and λ = 0.1 balances the two terms. This restoration-aware fine-tuning ensures that the restored representation is optimised not only for perceptual fidelity but also for downstream segmentation discriminability. Relative to the strongest baseline without the restoration front-end, this integration improves the combined-test-set mDS by 1.15 percentage points and the motion- blurred subset by 27.7% in relative terms (Table 4), while introducing only a marginal additional inference cost.


## 4 Experiments

ARTICLE IN PRESS


### 4.1 Dataset Introduction

The dataset used in this study is sourced from the publicly available DeBlurWeedSeg dataset [34], distributed via the Mendeley Data repository, which was developed to support the research on weed segmentation in UAV imagery of sorghum fields. The dataset was collected at an experimental agricultural sorghum field located in South- ern Germany using a DJI Mavic 2 Pro consumer-grade drone. At the time of image acquisition, sorghum was at the BBCH 13 growth stage. The primary weed species observed in the field was Chenopodium album L., with minor occurrences of Cirsium arvense L. (Scop.). The dataset comprises 1,300 pairs of 128×128 pixel image patches, each consisting of a motion-blurred image and its corresponding sharp counterpart.

The DeBlurWeedSeg annotations define three semantic classes: background, crop (sorghum), and weed. We use these classes as released, without modifying or extending the public label space; all experiments in this study are therefore conducted on the original three-class annotations.

To provide a quantitative overview of the dataset composition, Table 2 reports the pixel-level class distribution across the entire dataset. The three semantic cate- gories exhibit a pronounced long-tailed distribution typical of early-growth-stage UAV imagery: because the sorghum was at the BBCH 13 stage, plants and weeds are small and sparse, so the background dominates the scene (over 97% of all pixels), while crop and weed together occupy well under 3% of the total pixel budget. This severe class imbalance is one of the central practical challenges addressed in this study and moti- vates the use of mean-class evaluation metrics that do not over-weight the majority background class.

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS


> **Table 2 Pixel-level class distribution of the DeBlurWeedSeg dataset across**

> all 1,300 image patches (128×128 resolution), computed directly from the
released sharp-patch masks. The imbalance ratio refers to the ratio between
the most frequent class (background) and the corresponding class.

Class Pixel Count Proportion (%) Imbalance Ratio

Background 20,729,505 97.33 1.00× Crop (sorghum) 307,988 1.45 67.31× Weed 261,707 1.23 79.21×

Total 21,299,200 100.00 —

The compact size of the dataset (1,300 paired image patches) reflects the high cost of expert pixel-wise annotation of UAV field imagery. To mitigate concerns regarding overfitting and the robustness of the reported performance, two measures were taken. First, the dataset is split into training, validation, and test subsets in a stratified 70%/15%/15% ratio at the patch level, ensuring that the class distribution is preserved across all splits. Second, all reported results were obtained under a single fixed ran- dom seed (seed 0) with deterministic data splits, so that every reported value can be reproduced exactly; accordingly, as detailed in Section 4.3, small inter-configuration differences of a few tenths of a percentage point in mDS are treated as run-to-run noise rather than definitive rankings, and a full multi-seed variance analysis is left for future work.

ARTICLE IN PRESS


### 4.2 Evaluation Metrics

To quantitatively assess segmentation performance, we adopt the Dice Score (DS), also known as the Dice–Sørensen coefficient, as the primary evaluation metric. For a given class c, the Dice Score measures the overlap between the predicted segmentation mask ˆ Mc and the ground-truth mask Mc, and is defined as:

2  ˆ Mc ∩Mc

ˆ Mc

, (19)

DSc =

+ |Mc|

where |·| denotes the number of pixels belonging to the respective set. The Dice Score ranges from 0 (no overlap) to 1 (perfect agreement). To obtain an overall performance measure across all K semantic categories, we compute the mean Dice Score (mDS) as:

K X

mDS = 1

DSc, (20)

K

c=1

where K = 3 in this study, corresponding to background, crop (sorghum), and weed. In addition to per-class scores, we report the mDS as the primary metric for com- parative and ablation experiments, as it equally weights all categories regardless of

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

their pixel-level frequency, thereby providing a balanced assessment that reflects model performance on both majority and minority classes.

Considering the severe class imbalance and the multi-class nature of the seg- mentation task, the Dice Score alone is not sufficient to fully characterise model performance. We therefore additionally adopt three complementary metrics: the Intersection-over-Union (IoU), Precision, and Recall, all computed in a per-class manner and subsequently averaged to obtain their mean values (mIoU, mPrecision, mRecall). For a given class c, these metrics are defined as:

ˆ Mc ∩Mc

ˆ Mc ∪Mc

ˆ Mc ∩Mc

ˆ Mc

ˆ Mc ∩Mc

, Precisionc =

, Recallc =

|Mc| , (21)

IoUc =

and the corresponding mean values are computed by averaging over all K classes. The mIoU is particularly sensitive to under-segmentation and over-segmentation errors on minority classes, providing a stricter assessment than mDS, while Precision and Recall enable diagnosis of whether errors stem from false positives or missed detections. In conjunction with mDS, these metrics jointly furnish a comprehensive and class- imbalance-aware evaluation of the proposed framework.


### 4.3 Implementation Details and Training Settings

ARTICLE IN PRESS

All models were implemented in PyTorch 2.1.0 using the segmentation models pytorch library, with the ResNet encoders initialised from torchvision ImageNet-pretrained weights [7]. Training and evaluation were performed on a single NVIDIA GeForce RTX 3090 GPU with 24 GB of memory.

Data preparation. All patches are of fixed resolution 128 × 128 and were split at the patch level into stratified 70%/15%/15% training/validation/test subsets (Section 4.1). During training we applied on-line data augmentation comprising ran- dom horizontal and vertical flips, random 90◦rotations, and mild brightness/contrast jitter (within ±20%); the identical augmentation pipeline was applied to the pro- posed model and to every baseline in Section 4.5 to ensure a fair comparison. No augmentation was used at validation or test time.

Segmentation training. The segmentation network was optimised with the Adam optimiser (β1 = 0.9, β2 = 0.999), an initial learning rate of 1 × 10−3, and a weight decay of 1×10−4; the learning rate followed a cosine-annealing schedule decay- ing to 1 × 10−6 over training. Models were trained for 100 epochs with a mini-batch size of 16, and the checkpoint achieving the highest validation mean Dice Score was retained for testing. The training objective was the standard pixel-wise multi-class cross-entropy loss over the three semantic categories; no explicit class-balancing or focal weighting was applied, a choice revisited in Section 5.

Restoration-aware training. The NAFNet front-end and the segmentation backbone were trained with the two-stage protocol described in Section 3. In Stage 1, NAFNet was pre-trained for 150 epochs on the paired sharp/blurred patches using the L1 deblurring loss, with the Adam optimiser and an initial learning rate of 1 × 10−3. In Stage 2, the segmentation network was fine-tuned on the restored images using the

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

composite objective with λ = 0.1; the restoration parameters ΘR were jointly updated with a reduced learning rate of 1×10−5 so that the restored representation is adapted for downstream segmentability without overwriting the deblurring prior.

Reproducibility. All results reported in Tables 3, 5 and 6 were obtained with a single fixed random seed (seed 0) under identical hyper-parameters across encoder variants and baselines; the deterministic data splits and seed are released with the code so that every number can be reproduced exactly. Because a single seed cannot establish the statistical significance of small inter-configuration gaps, we treat differences of a few tenths of a percentage point in mDS (e.g. among the top encoders, or the removal of dropout) as within run-to-run noise rather than as definitive rankings; a full multi- seed variance analysis is left for future work. The complete training and evaluation code, the exact software versions, and the random seed are released to support full reproducibility (see Code Availability).

To evaluate the effectiveness of the proposed UNet-ResNet segmentation frame- work, we conduct comparative experiments using four ResNet encoder variants on the sorghum field dataset. Table 3 reports the per-class and overall Dice Score (DS) achieved by each encoder backbone on the hold-out test set. All models are trained on sharp image patches only and evaluated on both sharp and motion-blurred subsets.


> **Table 3 Per-class and mean Dice Score (DS) on the**

> hold-out test set for different ResNet encoder
backbones. “BG” denotes background, “Crop”
denotes crop (sorghum), and “Weed” denotes weed.
The best result in each column is shown in bold.

ARTICLE IN PRESS

Encoder BG Crop Weed mDS

ResNet-18 0.9974 0.9000 0.8527 0.9167 ResNet-34 0.9975 0.9047 0.8570 0.9198 ResNet-50 0.9975 0.8996 0.8492 0.9154 ResNet-101 0.9975 0.8987 0.8460 0.9141

To provide a more intuitive comparison, the per-class and mean Dice Scores for each encoder variant are visualized as a grouped bar chart in Fig. 6. The four encoders per- form comparably (mDS 0.9141–0.9198), with ResNet-34 attaining the highest scores, most clearly on the weed and crop classes. Notably, accuracy does not increase with encoder depth: the deeper ResNet-50 and ResNet-101 score slightly below ResNet-34, indicating that representational capacity saturates at moderate depth on a dataset of this scale and that the deeper backbones begin to overfit.

Furthermore, we compare the segmentation performance of the best-performing encoder (ResNet-34) under different image quality conditions, as summarized in Table 4. Following the experimental protocol of Genze et al. [34], three settings are considered: WeedSeg trained on both sharp and blurred patches (Scenario 1), WeedSeg trained on sharp patches only (Scenario 2), and the proposed model with an integrated deblurring module (DeBlurWeedSeg).

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

Fig. 6 Per-class and mean Dice Score comparison across four ResNet encoder backbones (ResNet- 18, ResNet-34, ResNet-50, and ResNet-101) on the hold-out test set. Each group of bars corresponds to one of the three semantic categories (BG, Crop, Weed) and the overall mean Dice Score (mDS). ResNet-34 attains the best overall performance, while the weed class remains the most challenging owing to its small spatial extent and fine, fragmented boundaries.

ARTICLE IN PRESS


> **Table 4 Mean Dice Score (mDS) under different image conditions**

> and training strategies. “Sharp” and “Motion Blurred” denote
subsets of the test set, and “Combined” reports the weighted average.
The best result in each column is shown in bold.

Method Sharp Motion Blurred Combined

WeedSeg (Scenario 1)1 0.8920 0.7295 0.8108 WeedSeg (Scenario 2)2 0.9198 0.5961 0.7579 Proposed + DeBlur3 0.8924 0.7614 0.8223

1Trained on both sharp and motion-blurred image patches with three- class labels (background, sorghum, weed).

2Trained on sharp image patches only with three-class labels.

3Proposed three-class UNet-ResNet34 model with NAFNet deblurring module, trained on sharp patches only.

As shown in Table 3 and Fig. 6, ResNet-34 achieves the highest mean Dice Score of 0.9198 across the three semantic categories, marginally ahead of ResNet-18 (0.9167) and the deeper ResNet-50 (0.9154) and ResNet-101 (0.9141). The four encoders are closely comparable—the spread of 0.0057 mDS is small and, under our single-seed protocol (Section 4.3), should be read as run-to-run noise rather than a definitive ranking—and accuracy does not improve with depth, consistent with capacity satu- ration and mild overfitting of the deeper backbones on this small training set. We

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

therefore adopt ResNet-34 as the backbone for the subsequent component and compar- ison studies, as it is both the nominally most accurate and the lighter of the mid-depth variants. Notably, the background class consistently achieves the highest per-class scores (>0.99) due to its dominant pixel proportion, while the weed class presents the greatest challenge owing to its small spatial extent and fine, fragmented boundaries.


> **Table 4 compares the proposed model against the WeedSeg model of Genze et**

> al. [34] under different image-quality conditions; all three settings operate on the same
three-class label space (background, sorghum, weed), so the comparison is strictly
like-for-like. Three observations stand out. First, the sharp-only WeedSeg baseline
(Scenario 2) is the best on sharp patches (0.9198) but collapses on motion-blurred
patches (0.5961), confirming that motion blur is the dominant failure mode. Sec-
ond, the proposed restoration-aware pipeline achieves the highest motion-blurred score
(0.7614) and the highest combined score (0.8223), improving the combined mDS by
+6.44 percentage points over the sharp-only baseline and by +1.15 percentage points
over the stronger Scenario 1 baseline that is itself trained on blurred data. On the
motion-blurred subset this corresponds to a relative improvement of 27.7% over the
sharp-only baseline. Third, on sharp patches the proposed model (0.8924) is marginally
below the sharp-specialist baseline, a small and expected trade-off for its substantially
greater robustness to blur. These results confirm that inserting an explicit image-
restoration step before segmentation mitigates the domain shift caused by motion blur
in UAV imagery.

ARTICLE IN PRESS


### 4.4 Ablation Experiment

To systematically evaluate the contribution of each key component in the proposed framework, we conduct a series of ablation experiments using the ResNet-34 encoder on the sorghum field dataset. All ablation models are trained under the same hyper- parameter settings and evaluated on the hold-out test set using the mean Dice Score (mDS) as the primary metric. The results are summarized in Table 5 and visualized in Fig. 7.


> **Table 5 Ablation study results on the hold-out test set using**

> ResNet-34 as the encoder backbone. Each row removes or modifies
one component from the full model. “∆” indicates the absolute
change in mDS relative to the full model. The effect of the deblurring
module is reported separately in Table 4.

Configuration BG Crop Weed mDS (∆)

Full Model 0.9975 0.9047 0.8570 0.9198 (–) w/o ImageNet Pretrain 0.9975 0.9046 0.8558 0.9193 (−0.05) w/o Skip Connections 0.9962 0.8624 0.7953 0.8847 (−3.51) w/o Dropout (p = 0) 0.9976 0.9072 0.8591 0.9213 (+0.15) Single Conv Decoder 0.9975 0.8980 0.8524 0.9160 (−0.38) 3 Decoder Blocks 0.9957 0.8402 0.7681 0.8680 (−5.18)

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

Fig. 7 Per-class and mean Dice Score comparison across six ablation configurations on the hold-out test set using ResNet-34 as the encoder backbone. Each group of bars corresponds to one of the three semantic categories (BG, Crop, Weed) and the overall mean Dice Score (mDS). Reducing the decoder to three blocks or removing skip connections causes the most substantial degradation, particularly for the minority classes (Crop and Weed), whereas removing ImageNet pre-training or dropout has negligible effect on this dataset.

ARTICLE IN PRESS

As shown in Table 5 and Fig. 7, the components differ markedly in their impor- tance. The performance gap between the full model and the ablated variants is negligible for the dominant background class but becomes pronounced for the minority crop and weed classes, where decoder capacity and feature fusion matter most.

Effect of Decoder Depth. Reducing the number of decoder blocks from five to three—skipping the two highest-resolution stages—causes by far the largest drop, 5.18 percentage points in mDS, with the weed Dice falling from 0.8570 to 0.7681. This demonstrates that progressive upsampling all the way to the full input resolution is essential for delineating the small, spatially dispersed weed and crop regions that dominate the minority classes. Replacing the dual-convolution decoder sub-blocks Gk with single-convolution blocks has a much smaller effect (−0.38 percentage points), indicating that decoder depth (resolution stages) matters far more than the per-stage convolution count.

Effect of Skip Connections. Removing all encoder–decoder skip connections is the second most damaging ablation, reducing mDS by 3.51 percentage points (weed Dice 0.8570→0.7953). Without skip connections the decoder must reconstruct spatial detail from the coarse bottleneck features alone, blurring boundaries and missing fine structures; the weed and crop classes, with their intricate boundaries, suffer most. This confirms that the encoder–decoder feature-fusion mechanism is indispensable for spatial precision.

Effect of ImageNet Pre-training and Dropout. In contrast, two components that are often assumed to be important have negligible effect on this dataset. Train- ing the encoder from random initialisation rather than ImageNet-pretrained weights

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

changes mDS by only −0.05 percentage points, and removing the segmentation-head dropout actually raises mDS by 0.15 percentage points—both well within the seed-to- seed variation (Section 4.3). We attribute this to the relatively long 100-epoch schedule and the strong on-line augmentation, which together allow the model to converge well even from scratch and make additional regularisation largely redundant at this dataset scale. We retain ImageNet initialisation (it does no harm and speeds early conver- gence) and a light dropout of 0.1, but do not claim either as a critical design choice on this data.

Overall, the ablation results identify decoder depth (full-resolution progressive upsampling) and encoder–decoder skip connections as the two components that gen- uinely drive segmentation quality on this dataset, whereas ImageNet pre-training and dropout are, at best, marginal. The effect of the NAFNet restoration front-end is examined separately under motion blur in Table 4.


### 4.5 Comparison with State-of-the-Art Agricultural

Segmentation Models

To further situate the proposed UNet-ResNet34 framework, we benchmark it against three representative standard CNN segmentation architectures that are widely used in agricultural and remote-sensing segmentation: DeepLabV3+ [35], U-Net++ [36], and FPN (Feature Pyramid Network). To ensure a fair comparison, every baseline uses the same ResNet-34 encoder as the proposed model and is retrained on the DeBlur- WeedSeg dataset under the identical three-class label space, training/validation/test split, and data-augmentation strategy. To isolate the contribution of the segmenta- tion backbone from that of the restoration front-end, each baseline is evaluated in two configurations on the combined (sharp + blurred) test set: (a) directly (w/o NAF), and (b) preceded by the same pre-trained NAFNet restoration module used in the proposed framework (w/ NAF).

ARTICLE IN PRESS


> **Table 6 Comparison with SOTA agricultural segmentation models on the hold-out test**

> set (three-class label space). w/o NAF denotes direct training without the deblurring
front-end; w/ NAF denotes the same backbone preceded by the shared pre-trained
NAFNet restoration module. Best result in each column is in bold.

Method mDS mIoU mPrecision mRecall

DeepLabV3+ (w/o NAF) 0.7715 0.6587 0.7564 0.7880 U-Net++ (w/o NAF) 0.7829 0.6705 0.7639 0.8215 FPN (w/o NAF) 0.7811 0.6689 0.7554 0.8108

DeepLabV3+ (w/ NAF) 0.6108 0.5057 0.7357 0.5461 U-Net++ (w/ NAF) 0.6226 0.5163 0.7520 0.5593 FPN (w/ NAF) 0.6572 0.5445 0.7634 0.5938

Proposed (UNet-ResNet34 + NAF) 0.8223 0.7185 0.8424 0.8067

As shown in Table 6, the proposed UNet–ResNet34 with the restoration-aware NAFNet front-end attains the highest mDS (0.8223), mIoU (0.7185) and mPrecision

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

(0.8424) on the combined test set, exceeding the strongest standard baseline (U- Net++, mDS 0.7829) by 3.94 percentage points in mDS; U-Net++ retains a slightly higher mean recall (0.8215 vs. 0.8067). Two findings are noteworthy. First, despite a comparable parameter and MAC budget (Table 7), the proposed framework out- performs the standard CNN architectures, indicating that on this small dataset the advantage stems from the architecture–data match and the restoration-aware coupling rather than from raw model capacity. Second, and more revealing, naively prepend- ing the same pre-trained NAFNet module to the baselines at inference time degrades them substantially (e.g. DeepLabV3+ drops from 0.7715 to 0.6108 mDS), because those backbones were trained on sharp images and the restored inputs constitute an unseen distribution. Only the proposed model, in which the segmentation network is trained on the restored representation, benefits from the front-end. This contrast indi- cates that the gain arises from restoration-aware training, not from merely bolting a deblurring network onto an existing model—the central methodological point of this work. We note that all numbers are single-seed (Section 4.3); the recall gap with U- Net++ is well within run-to-run variation and we therefore claim a clear advantage in mDS/mIoU/precision rather than a uniform improvement on every metric.


### 4.6 Computational Complexity Analysis

To assess the computational feasibility of deployment on resource-constrained UAV platforms, we report the parameter count and multiply–accumulate operations (MACs) of the proposed framework and all SOTA baselines. Both metrics are com- puted with the thop library at the standard input resolution of 128 × 128; they are independent of any specific runtime and are therefore directly reproducible. We deliberately restrict this deployment analysis to architecture-level complexity metrics, because an empirical on-device throughput measurement on embedded NVIDIA Jet- son hardware requires a physical edge platform that was not available in this study and is therefore left for future work.

ARTICLE IN PRESS


> **Table 7 Computational complexity comparison. Params**

> denotes the total parameter count in millions and MACs
denotes multiply–accumulate operations in giga-units, both
measured at 128 × 128 input with the thop library. The
proposed pipeline is reported as Deblur + Seg, with the
segmentation-only model also listed for reference.

Method Params (M) MACs (G)

DeepLabV3+ (R34) 22.4 1.98 U-Net++ (R34) 26.1 4.62 FPN (R34) 23.2 1.72

NAFNet (deblur only) 17.0 2.98 Proposed Seg (UNet-R34) 24.4 1.97 Proposed (Deblur + Seg) 41.4 4.95

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS


> **Table 7 shows that the segmentation network alone (24.4 M parameters,**

> 1.97 GMACs) is comparable in complexity to the standard CNN baselines—marginally
heavier than DeepLabV3+ (22.4 M, 1.98 GMACs) and FPN (23.2 M, 1.72 GMACs)
and lighter than U-Net++ (26.1 M, 4.62 GMACs)—so the proposed backbone does
not rely on excessive model capacity to reach its accuracy. The NAFNet restoration
front-end is the dominant additional cost: it adds 17.0 M parameters and 2.98 GMACs,
so the full pipeline (41.4 M, 4.95 GMACs) is roughly twice the size of the segmenta-
tion network alone. Because the restoration branch is a separable front-end, it can be
bypassed on sharp imagery to recover the lightweight 24.4 M/1.97 GMACs configura-
tion and enabled only when motion blur is expected. These architecture-level figures
suggest the framework is plausibly deployable on resource-constrained embedded hard-
ware; a direct on-device throughput measurement, however, was not performed in this
study and remains future work.

For clarity, the intended on-board deployment configuration corresponding to this complexity analysis is summarised schematically in Fig. 8.

On-board edge device (NVIDIA Jetson)

UAV image

NAFNet deblurring

UNet–ResNet34

Three-class segmentation map

acquisition (motion-blurred)

segmentation

front-end

ARTICLE IN PRESS

Fig. 8 Schematic of the proposed on-board deployment pipeline (a conceptual diagram, not a field photograph). A UAV-captured, potentially motion-blurred frame is restored by the NAFNet front- end and then segmented by the UNet–ResNet34 network on an embedded NVIDIA Jetson device to produce the three-class map. The computational feasibility of this configuration was assessed through the parameter-count and MACs analysis reported in Table 7; an on-device throughput measurement on embedded NVIDIA Jetson hardware and a physical in-field flight test were not performed in this study and are left for future work.


### 4.7 Qualitative Analysis

As shown in Fig. 9, following our strategy of performing explicit image restoration (deblurring) before semantic segmentation, we provide a qualitative comparison on motion-blurred samples: the motion-blurred input is first processed by a deblurring module to recover texture and edge information, and then fed into the segmentation network to produce a predicted mask, which is compared against the human-annotated ground-truth (GT) mask. The motivation is to introduce an explicit restoration step prior to segmentation to mitigate the domain shift caused by motion blur, thereby improving segmentation robustness under blurred conditions.


## 5 Discussion

Dataset scope and generalizability. The quantitative findings reported above should be interpreted within the scope of the evaluation dataset. All experiments were

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

Fig. 9 Qualitative visualization of the “deblurring→segmentation” pipeline under motion blur, on two hold-out test patches (one per row). From left to right: the motion-blurred input, the NAFNet- deblurred restoration, the human-annotated ground-truth (GT) mask, and the mask predicted by the proposed model (Pred). Masks are colour-coded as background (black), crop (green), and weed (red). The deblurred restoration recovers leaf edges and texture lost to motion blur, and the predicted masks closely follow the ground truth, illustrating that inserting an explicit restoration step before segmentation alleviates motion-blur-induced domain shift and improves segmentation robustness.

ARTICLE IN PRESS

conducted on the publicly available DeBlurWeedSeg dataset, which comprises 1,300 paired 128×128 patches acquired from a single sorghum field in Southern Germany at the BBCH 13 growth stage, with Chenopodium album as the dominant weed species. Consequently, the absolute Dice Scores presented here characterise the proposed framework under one crop type, one phenological stage, and a relatively narrow range of illumination, soil background, and flight conditions. Different crops, weed floras, growth stages, imaging sensors, and acquisition altitudes will introduce domain shift that may degrade performance, and we therefore refrain from claiming crop-agnostic generality. Encouragingly, the architectural conclusions of this study—the importance of decoder depth and encoder–decoder skip connections, the depth-versus-data-scale saturation of ResNet encoders, and the value of restoration-aware coupling—are mech- anistic in nature and are expected to transfer more readily than the absolute accuracy values. Validating this expectation on multi-crop, multi-season datasets, together with domain-adaptation and self-supervised pre-training on large unlabelled agricultural corpora, is an important direction for future work.

Class imbalance and minority-class segmentation. As quantified in Table 2, the dataset exhibits a pronounced long-tailed distribution: the background alone occu- pies more than 97% of all pixels, whereas crop and weed account for only 1.45% and 1.23%, corresponding to imbalance ratios of 67.3× and 79.2× relative to the back- ground class. This imbalance is directly reflected in the per-class results of Table 3, where the two minority categories attain lower Dice Scores (0.8996 for crop and 0.8492

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

for weed with ResNet-50) than the dominant background class and, as the preci- sion/recall analysis indicates, are the most susceptible to missed detections of small structures. In the present framework, imbalance is mitigated only implicitly—through ImageNet pre-training, dropout regularisation, and the use of mean-class metrics that weight all categories equally—without any explicit imbalance-aware loss. Future work could target minority-class performance more directly through class-balanced or focal/Tversky-style losses that up-weight minority pixels, copy-paste and oversam- pling augmentation, hard-example mining, and boundary-aware objectives. Leveraging abundant unlabelled field imagery via semi- or self-supervised learning is a further promising avenue for reducing false negatives in these agronomically critical categories.

Relation to object detection and instance segmentation paradigms. The choice of a dense semantic segmentation formulation, rather than a lightweight object detector (e.g., the YOLO family) or an instance segmentation network (e.g., Mask R-CNN, YOLACT), is dictated by the nature of the targets and the intended down- stream action. Object and instance detectors are well suited to enumerating discrete, well-delineated objects—such as individual fruits or insects—and typically offer very high throughput. Weeds in early-stage UAV imagery, however, frequently manifest as amorphous, fragmented, and ill-bounded regions: overlapping weed patches and seedlings intermixed with crop rows that do not decompose naturally into countable instances. Moreover, the agronomic objective targeted here—variable-rate, site-specific herbicide application—requires the precise pixel-level spatial extent of each category rather than a bounding box, which a dense three-class semantic map provides directly. Detection and instance frameworks remain complementary for tasks dominated by discrete-object counting, and unifying both views through panoptic segmentation is an interesting direction; for the pixel-extent estimation problem addressed in this work, semantic segmentation is the more appropriate paradigm.

ARTICLE IN PRESS

Deployment trade-offs of the restoration front-end. The NAFNet restora- tion module is not without cost: it adds 17.0 M parameters and 2.98 GMACs to the pipeline (Table 7), roughly doubling the size of the segmentation network alone. In return, it raises the combined-test mean Dice Score by 1.15 percentage points over the strongest no-restoration baseline and, most importantly, improves the motion-blurred subset by 27.7% in relative terms (Table 4). Because the restoration branch is applied as a separable front-end, this trade-off can be made adaptive at inference time: when the captured imagery is sharp—for example, during low-wind hover acquisition—the deblurring branch can be bypassed to recover the lower-cost segmentation-only config- uration, whereas it can be enabled whenever motion blur is anticipated. This tunable accuracy–complexity balance is a practical advantage for deployment decisions on resource-constrained platforms; quantifying the resulting on-device frame rates is part of the planned hardware validation.


## 6 Conclusion

This study presents a semantic segmentation framework for crop–weed discrimina- tion based on a UNet-ResNet architecture with an integrated deblurring front-end. Experimental results demonstrate that ResNet-34 achieves the highest mean Dice

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

Score of 0.9198 across the three semantic categories (background, crop, weed), with accuracy saturating at moderate depth so that the deeper ResNet-50 and ResNet-101 perform slightly worse. The integration of a deblurring module improves robust- ness under motion blur conditions while maintaining competitive performance on sharp inputs. Ablation studies identify decoder depth (full-resolution progressive upsampling) and encoder–decoder skip connections as the most critical architectural components, while ImageNet pre-training and dropout have negligible effect at this dataset scale. The value of the present work resides in the systematic encoder-depth characterisation, the restoration-aware integration of deblurring and segmentation, and a deployment-oriented complexity analysis for embedded UAV hardware, rather than in the introduction of a fundamentally new network primitive.

The proposed framework performs crop–weed segmentation within a single infer- ence pass. A complexity analysis based on parameter count and MACs further indicates that the segmentation network is comparable to standard CNN segmentation baselines and that the optional restoration front-end can be bypassed on sharp imagery, supporting its plausibility for deployment on resource-constrained UAV platforms; an empirical on-device validation on embedded NVIDIA Jetson hardware is left for future work. By explicitly incorporating image restoration prior to segmentation, the model demonstrates enhanced robustness to real-world imaging conditions characterized by motion blur and variable image quality. The multi-scale feature fusion mechanism and residual learning backbone collectively provide robust spatial localization and seman- tic discrimination, offering practical value for automated crop monitoring systems that require accurate pixel-wise identification of crop and weed in the studied agricul- tural setting. We note, however, that the present evaluation is based on a single-crop sorghum dataset, and that broader validation across crops, growth stages, and field conditions (Section 5) is required before strong claims of cross-domain generality can be made.

ARTICLE IN PRESS

Future work will extend the framework to incorporate temporal information from sequential UAV imagery, enabling earlier and more reliable detection of weed emer- gence dynamics. We will also investigate domain adaptation techniques to improve cross-crop generalization, allowing the model trained on one crop species to transfer effectively to others without extensive retraining. Additionally, we plan to integrate attention mechanisms and transformer-based encoders to further enhance the model’s ability to capture long-range dependencies and subtle visual patterns that distin- guish crop from weed at early growth stages. In particular, we plan to conduct an on-device benchmarking and on-UAV in-field deployment study—including TensorRT throughput measurement on embedded NVIDIA Jetson hardware, hardware-in-the- loop flight tests, and the corresponding field documentation—to empirically validate the computational-feasibility analysis presented in this paper.

Code Availability. The complete training and evaluation code for the UNet– ResNet segmentation framework and the NAFNet restoration-aware pipeline— including the model definitions, the two-stage training scripts, the evaluation metrics, the complexity-analysis utilities, the stratified 70/15/15 data splits, the exact software versions, and the fixed random seed (seed 0) used for all reported results—is released under the MIT License and permanently archived in

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

a Zenodo repository at https://doi.org/10.5281/zenodo.20680100. The same code is additionally hosted on GitHub at https://github.com/happyeveryday8882026/ deblurring-aware-crop-weed-segmentation, where the pre-trained model weights for the NAFNet deblurring front-end and the proposed UNet–ResNet34 segmentation network are provided as release assets.

Data Availability. The imagery (paired sharp/blurred patches with three-class masks: background, crop/sorghum, and weed) is the publicly available DeBlurWeedSeg dataset of Genze et al. [34], openly accessible via the Mendeley Data reposi- tory at https://doi.org/10.17632/k4gvsjv4t3.1 and at https://github.com/grimmlab/ DeBlurWeedSeg. The train/validation/test splits used in this study are released together with the source code in the Zenodo repository listed under Code Availability.

Acknowledgements. During the preparation of this manuscript, the authors used ChatGPT (OpenAI, GPT-5) for the purposes of language refinement and format- ting suggestions. The authors have reviewed and edited the output and take full responsibility for the content of this publication.

Conflict of interest. The authors declare that they have no conflict of interest.

Ethics Approval and Consent to Participate. Not applicable.

Consent for publication. Not applicable. This study does not contain any individual person’s data in any form (including individual details, images, or videos).

ARTICLE IN PRESS

Funding. The authors received no funding for this work.

Author contribution. Q.L. was responsible for conceptualisation, methodology, software, formal analysis, investigation, data curation, and writing (original draft). S.Z. was responsible for conceptualisation, supervision and writing (review and editing). All authors read and approved the final manuscript.


## References

[1] Hussain, S.: Advancing plant health management: challenges, strategies, and

implications for global agriculture. International Journal of Agriculture and Sustainable Development 6(2), 73–89 (2024)

[2] Zhang, Z., Zhu, L.: A review on unmanned aerial vehicle remote sensing: Plat-

forms, sensors, data processing methods, and applications. Drones 7(6), 398 (2023)

[3] Wu, B., Zhang, M., Zeng, H., et al.: Challenges and opportunities in remote

sensing-based crop monitoring: A review. National Science Review 10(4), 290 (2023)

[4] Ronneberger, O., Fischer, P., Brox, T.: U-Net: Convolutional networks for

biomedical image segmentation. In: Medical Image Computing and Computer- Assisted Intervention (MICCAI), pp. 234–241 (2015)

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

[5] He, K., Zhang, X., Ren, S., Sun, J.: Deep residual learning for image recogni-

tion. In: Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), pp. 770–778 (2016)

[6] Shafiq, M., Gu, Z.: Deep residual learning for image recognition: A survey. Applied

Sciences 12(18), 8972 (2022)

[7] Deng, J., Dong, W., Socher, R., Li, L.-J., Li, K., Fei-Fei, L.: ImageNet: A large-

scale hierarchical image database. In: Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), pp. 248–255 (2009)

[8] Lee, J.H., Gwon, G.H., Kim, I.H., et al.: A motion deblurring network for

enhancing uav image quality in bridge inspection. Drones 7(11), 657 (2023)

[9] Urrea, C., V´elez, M.: Advances in deep learning for semantic segmentation of

low-contrast images: A systematic review of methods, challenges, and future directions. Sensors 25(7), 2043 (2025)

[10] Lei, L., Yang, Q., Yang, L., et al.: Deep learning implementation of image segmen-

tation in agricultural applications: a comprehensive review. Artificial Intelligence Review 57(6), 149 (2024)

[11] Umirzakova, S., Muksimova, S., Buriboev, A. Shavkatovich, et al.: A unified trans-

ARTICLE IN PRESS

former model for simultaneous cotton boll detection, pest damage segmentation, and phenological stage classification from uav imagery. Drones 9(8), 555 (2025)

[12] Luo, Z., Yang, W., Yuan, Y., et al.: Semantic segmentation of agricultural images:

A survey. Information Processing in Agriculture 11(2), 172–186 (2024)

[13] Gupta, S.K., Yadav, S.K., Soni, S.K., et al.: Multiclass weed identification

using semantic segmentation: An automated approach for precision agriculture. Ecological Informatics 78, 102366 (2023)

[14] Sharma, K., Shivandu, S.K.: Integrating artificial intelligence and internet of

things (iot) for enhanced crop monitoring and management in precision agricul- ture. Sensors International 5, 100292 (2024)

[15] Wang, D., Cao, W., Zhang, F., et al.: A review of deep learning in multiscale

agricultural sensing. Remote Sensing 14(3), 559 (2022)

[16] Ajith, S., Vijayakumar, S., Elakkiya, N.: Yield prediction, pest and disease diag-

nosis, soil fertility mapping, precision irrigation scheduling, and food quality assessment using machine learning and deep learning algorithms. Discover Food 5(1), 1–23 (2025)

[17] Momeni, A., Rahmani, B., Mall´ejac, M., et al.: Backpropagation-free training of

deep physical neural networks. Science 382(6676), 1297–1303 (2023)

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

[18] Della Mura, M., Sorino, J., Colagrande, A., et al.: Artificial intelligence in the

histopathological assessment of non-neoplastic skin disorders: A narrative review with future perspectives. Medical Sciences 13(2), 70 (2025)

[19] Hossen, M.I., Awrangjeb, M., Pan, S., et al.: Transfer learning in agriculture: a

review. Artificial Intelligence Review 58(4), 97 (2025)

[20] Scabini, L., Sacilotti, A., Zielinski, K.M., et al.: A comparative survey of vision

transformers for feature extraction in texture analysis. Journal of Imaging 11(9), 304 (2025)

[21] Coleman, G.R.Y., Bender, A., Hu, K., et al.: Weed detection to weed recognition:

reviewing 50 years of research to identify constraints and opportunities for large- scale cropping systems. Weed Technology 36(6), 741–757 (2022)

[22] Shoaib, M., Khan, S.U., AbdelHameed, H., et al.: Plant stress detection using

multimodal imaging and machine learning: from leaf spectra to smartphone applications. Frontiers in Plant Science 16, 1670593 (2025)

[23] Swindell, J., Popovi´c, M., Polvara, R.: Active Informative Planning for UAV-

based Weed Mapping using Discrete Gaussian Process Representations. arXiv preprint arXiv:2601.13196 (2026)

ARTICLE IN PRESS

[24] Yu, C., Pei, H.: Dynamic weighting translation transfer learning for imbalanced

medical image classification. Entropy 26(5), 400 (2024)

[25] Sharief, F., Ijaz, H., Shojafar, M., et al.: Multi-class imbalanced data handling

with concept drift in fog computing: A taxonomy, review, and future directions. ACM Computing Surveys 57(1), 1–48 (2024)

[26] Li, Z., Wang, R., Ding, R.: A review of crop attribute monitoring technologies

for general agricultural scenarios. AgriEngineering 7(11), 365 (2025)

[27] He, Z.: Customizable restoration in multi-degradation scenarios: Joint deraining

and low-light image enhancement via perceptual decoupling. IEEE Access (2024)

[28] Lu, R., Wang, N., Zhang, Y., et al.: Extraction of agricultural fields via dasfnet

with dual attention mechanism and multi-scale feature fusion in south xinjiang, china. Remote Sensing 14(9), 2253 (2022)

[29] Zhang, R., Jiang, H., Wang, W., et al.: Optimization methods, challenges, and

opportunities for edge inference: A comprehensive survey. Electronics 14(7), 1345 (2025)

[30] Wang, Y., Wang, Y., Rohra, A., et al.: End-to-end model compression via prun-

ing and knowledge distillation for lightweight image super resolution. Pattern Analysis and Applications 28(2), 94 (2025)

ACCEPTED MANUSCRIPT

ARTICLE IN PRESS

[31] Mamat, N., Othman, M.F., Abdoulghafor, R., et al.: Advanced technology in agri-

culture industry by implementing image annotation technique and deep learning approach: A review. Agriculture 12(7), 1033 (2022)

[32] Da, L., Turnau, J., Kutralingam, T.P., et al.: A survey of sim-to-real methods in

RL: Progress, prospects and challenges with foundation models. arXiv preprint arXiv:2502.13187 (2025)

[33] Chen, L., Chu, X., Zhang, X., Sun, J.: Simple baselines for image restoration. In:

Proceedings of the European Conference on Computer Vision (ECCV) (2022). arXiv:2204.04676

[34] Genze, N., Wirth, M., Schreiner, C., Ajekwe, R., Grieb, M., Grimm, D.G.:

Improved weed segmentation in UAV imagery of sorghum fields with a com- bined deblurring segmentation model. Plant Methods 19(1), 87 (2023) https: //doi.org/10.1186/s13007-023-01060-8

[35] Chen, L.-C., Zhu, Y., Papandreou, G., Schroff, F., Adam, H.: Encoder-decoder

with atrous separable convolution for semantic image segmentation. In: Proceed- ings of the European Conference on Computer Vision (ECCV), pp. 801–818 (2018)

[36] Zhou, Z., Rahman Siddiquee, M.M., Tajbakhsh, N., Liang, J.: UNet++: A nested

ARTICLE IN PRESS

U-Net architecture for medical image segmentation. In: Deep Learning in Medical Image Analysis and Multimodal Learning for Clinical Decision Support (DLMIA), pp. 3–11 (2018)
