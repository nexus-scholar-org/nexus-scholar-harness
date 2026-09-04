---
workspace_id: SCI-000007
doi: 10.48550/arxiv.2602.23677
title: Vision-Language Semantic Grounding for Multi-Domain Crop-Weed Segmentation
authors:
- family_name: Hossain
  given_name: Nazia
  orcid: null
- family_name: Jiang
  given_name: Xintong
  orcid: null
- family_name: Tian
  given_name: Yu
  orcid: null
- family_name: Seguin
  given_name: Philippe
  orcid: null
- family_name: Clark
  given_name: O. Grant
  orcid: null
- family_name: Sun
  given_name: Shangpeng
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:28:04.095422+00:00'
---

# Vision-Language Semantic Grounding for Multi-Domain Crop-Weed Segmentation

Vision-Language Semantic Grounding for Multi-Domain Crop-Weed Segmentation

Nazia Hossaina, Xintong Jianga, Yu Tiana, Philippe Seguinb, O. Grant Clarka and Shangpeng Suna

aDepartment of Bioresource Engineering, McGill University, Sainte-Anne-de-Bellevue, QC, Canada bDepartment of Plant Science, McGill University, Sainte-Anne-de-Bellevue, QC, Canada

A R T I C L E I N F O

A B S T R A C T

Keywords: Vision-language models Weed segmentation Multi-domain learning Semantic segmentation Precision agriculture Feature modulation

Fine-grained crop-weed segmentation is essential for enabling targeted herbicide application in precision agriculture. However, existing deep learning models struggle to generalize across hetero- geneous agricultural environments due to reliance on dataset-specific visual features. We propose Vision-Language Weed Segmentation (VL-WS), a novel framework that addresses this limitation by grounding pixel-level segmentation in semantically aligned, domain-invariant representations. Our architecture employs a dual-encoder design, where frozen Contrastive Language-Image Pretraining (CLIP) embeddings and task-specific spatial features are fused and modulated via Feature-wise Linear Modulation (FiLM) layers conditioned on natural language captions. This design enables image level textual descriptions to guide channel-wise feature refinement while preserving fine- grained spatial localization. Unlike prior works restricted to training and evaluation on single-source datasets, VL-WS is trained on a unified corpus that includes close-range ground imagery (robotic platforms) and high-altitude unmanned aerial vehicle (UAV) imagery, covering diverse crop types, weed species, growth stages, and sensing conditions. Experimental results across four benchmark datasets demonstrate the effectiveness of our framework, with VL-WS achieving a mean Dice score of 91.64% and outperforming the strongest Convolutional Neural Network (CNN) baseline by 4.98%. The largest gains occur on the most challenging weed class, where VL-WS attains 80.45% Dice score compared to 65.03% for the best baseline, representing a 15.42% improvement. VL-WS further maintains stable weed segmentation performance under limited target-domain supervision, indicating improved generalization and data efficiency. These findings highlight the potential of vision-language alignment to enable scalable, label-efficient segmentation models deployable across diverse real-world agricultural domains.

arXiv:2602.23677v1  [cs.CV]  27 Feb 2026

vegetation (Li et al., 2025). For maize, DeepLabV3+ has en- abled real-time weed segmentation, demonstrating effective- ness under high inter-row variability and dense weed popu- lations (Guo et al., 2025b). With increasing use of unmanned aerial vehicle (UAV) imagery, convolutional neural network (CNN) and hybrid CNN-transformer architectures have been implemented for rice and soybean fields, where large-scale spatial context and variable lighting conditions pose chal- lenges (Guo et al., 2025a; Xu et al., 2023). Transformer- based models and ConvNeXt-based backbones have shown improved robustness under changing weather, illumination, and weed density, while CycleGAN-based domain adapta- tion has been used to address seasonal and environmental shifts (Xu et al., 2025). To reduce annotation costs, semi- supervised approaches have been applied to UAV imagery, achieving competitive performance using limited labeled data (Guo et al., 2025b). Cross-domain transfer learning between ground-based and aerial platforms has further im- proved generalization across sensing modalities in the con- text of weed detection (Gao et al., 2024).


## 1. Introduction

The objective of precision weed control is to minimize the impact of weed competition on the crop while reducing the amount of herbicide use through site-specific management. Central to this approach is accurate weed detection and localization, which enables targeted herbicide application that reduces chemical usage compared to broadcast spraying. Conventional blanket herbicide treatments not only increase costs but also accelerate environmental degradation, raise herbicide resistance, and deteriorate soil health (Jiang et al., 2020; You et al., 2020). Pixel-level crop-weed segmentation offers the spatial accuracy required for localized spraying systems, making weed management economically viable and environmentally sustainable.

Modern crop-weed segmentation approaches predomi- nantly rely on deep learning (DL) architectures that facilitate hierarchical representation learning and dense prediction in visually complex agricultural scenes. Encoder-decoder architectures such as U-Net and DeepLab variants have been widely applied to row-crop segmentation, demonstrating strong performance under complex field conditions with di- verse weed species. Attention enhanced U-Net models have been used for sugar beet and sunflower fields, improving boundary delineation in cluttered scenes with overlapping

Despite recent advances, a critical limitation restricts the real-world deployment of existing crop-weed segmentation models. Most models are trained and evaluated on a single dataset collected under specific field conditions, crop types, and sensing platforms. When applied to new agricultural en- vironments where crop species, weed composition, growth stages, soil appearance, and imaging modalities vary sub- stantially, these models often fail to generalize (Asad et al.,

shangpeng.sun@mcgill.ca (S. Sun) ORCID(s): 0000-0001-7095-8626 (S. Sun)

Page 1 of 16

Vision-Language Model for Crop-Weed Segmentation

2024). This limited generalization stems from a reliance on dataset-specific low-level visual cues related to plant mor- phology, such as texture, shape, and appearance patterns, rather than on higher-level semantic concepts of crops and weeds and, therefore, fails to transfer across agricultural domains. Creating a single dataset that captures the full diversity of real-world agricultural conditions is not prac- tical. Comprehensive data collection would need to span entire growing seasons to capture phenological variation over time, while pixel-level annotation would become pro- hibitively expensive due to overlapping vegetation, micro- scale morphology, and ambiguous crop-weed boundaries. A more realistic solution is to leverage existing public datasets alongside limited domain-specific data, exposing the model to a broader range of crops, weed species, growth stages, and sensing conditions. Such multi-dataset training should enable the development of a single model that generalizes across diverse agricultural settings. However, naive aggrega- tion of datasets often degrades performance due to semantic inconsistencies (Lambert et al., 2020). Shared labels such as “weed” group a broad range of morphologically distinct species under the same class, creating conflicting supervi- sion signals that confuse models.

heterogeneity. At the same time, a trainable segmentation- specific visual encoder and spatial decoder capture fine- grained spatial structure, enabling accurate delineation of crop-weed boundaries. In summary, we make the following contributions.


## 1. We identify the limitations of standard CNN-based

models in multi-dataset crop-weed segmentation and
empirically show how inconsistent semantic labels de-
grade performance.
2. We propose Vision-Language Weed Segmentation (VL-
WS), a novel framework that integrates frozen Con-
trastive Language-Image Pretraining (CLIP) represen-
tations with a trainable spatial encoder, where Feature-
wise Linear Modulation (FiLM)-based caption condi-
tioning modulates fused features to achieve semantic
stability across heterogeneous datasets varying in crop
and weed species as well as ground sampling distance
(GSD), while preserving precise boundary delineation.
3. We validate the proposed approach on four diverse agri-
cultural datasets, demonstrating improved performance
in both cross-dataset generalization and data efficiency.

Recent advances in vision-language models show that integrating natural language with visual representations im- proves model robustness and generalization in complex vi- sual tasks. In agricultural settings, vision-based models of- ten struggle to generalize due to spatiotemporal variabil- ity, phenological changes, and environmental heterogene- ity, which cause large appearance shifts across datasets (Wu et al., 2025). Language provides semantic priors that capture high-level concepts, such as spatial organization, growth stages, and contextual relationships that remain more consistent across environments than low-level visual cues. Prior work in agricultural vision-language studies show that language-guided models can effectively adapt to specialized tasks, such as plant stress phenotyping, disease diagnosis, and weed identification, even under limited supervision by facilitating the transfer of semantic knowledge across di- verse agricultural conditions (Arshad et al., 2025). Simi- larly, image-text paired agricultural datasets have shown that structured, domain-aware textual descriptions improve fine- grained classification by helping models distinguish between visually similar classes (Yu et al., 2025). These findings motivate the exploration of semantic grounding in vision- language models to mitigate generalization challenges in crop-weed segmentation.


## 2. Related work

2.1. Challenges of Multi-Dataset Training with Shared Labels Recent research has explored multi-dataset training as a means of building more general and robust visual percep- tion systems. Zhou et al. (2022) demonstrates that labels with identical linguistic names may correspond to visually distinct concepts across datasets, and that naive dataset merging often leads to suboptimal performance. Their anal- ysis further shows that effective multi-dataset learning re- quires dataset-aware training strategies to mitigate semantic conflicts and avoid performance degradation. Consistent with these findings, we observe a similar phenomenon in our crop-weed semantic segmentation experiments. Training standard CNNs jointly on multiple datasets degrades perfor- mance compared to dataset-specific training. This degrada- tion persists despite the increased volume of training data, indicating that multi-dataset supervision introduces conflict- ing signals rather than providing complementary informa- tion. This behavior can be attributed to label-level semantic heterogeneity and negative transfer. As formalized by Wang et al. (2019), negative transfer arises when the divergence between source and target joint distributions is substantial and when learning algorithms fail to suppress incompatible source information. In our setting, the shared weed label aggregates approximately 12-14 distinct weed species across datasets, each exhibiting different morphology, texture, and growth characteristics. As shown by Zhou et al. (2022) merg- ing visually distinct concepts under a single semantic label causes label collisions that increase intra-class variability and destabilize feature learning. This semantic mismatch induces a conditional distribution shift between image fea- tures and labels, weakening discriminative representations

In this work, we explore vision-language semantic ground- ing to enable robust crop-weed segmentation across multiple datasets. We demonstrate that pretrained vision-language representations, organized around natural-language-aligned semantic concepts, provide a stable feature space that main- tains semantic consistency across visually heterogeneous agricultural datasets. By grounding visual features in such language-aligned representations, the proposed approach reduces reliance on dataset-specific appearance patterns and mitigates negative transfer caused by semantic label

Page 2 of 16

Vision-Language Model for Crop-Weed Segmentation


> **Figure 1: Image-text cosine similarity scores produced by a**

> frozen CLIP model for soybean field images with different
levels of weed presence. For crop-dominant scenes, image
embeddings show higher similarity to the soybean prompt,
while weed-dense scenes exhibit higher similarity to the weed
prompt. This shift in similarity demonstrates that CLIP implic-
itly captures agronomic scene semantics without task-specific
fine-tuning.


> **Figure 2: Overview of the proposed Vision-Language Weed**

> Segmentation (VL-WS) framework. Dense spatial features
extracted by a task-specific visual backbone are concatenated
with global image embeddings from a pretrained CLIP encoder.
The fused features are modulated by natural-language captions
through Feature-wise Linear Modulation (FiLM), enabling
text-conditioned channel adaptation for pixel-level crop-weed
segmentation.

and leading to consistent performance degradation in multi- dataset training.

grounded representations without requiring parameter adap- tation. This semantic grounding is reflected in strong em- pirical performance, with frozen CLIP embeddings achiev- ing 85-95% of state-of-the-art accuracy on discriminative tasks without fine-tuning (Bourigault and Bourigault, 2025). However, CLIP embeddings remain inherently coarse and lack precise spatial localization, limiting their suitability for dense prediction tasks such as weed segmentation.

2.2. CLIP for Semantic Robustness in Multi-Dataset Learning

To address semantic conflicts and negative transfer in multi-dataset training, recent work has increasingly ex- plored frozen pretrained encoder backbones (Bhattacharjee et al., 2023). In particular, Contrastive Language-Image Pre- training (CLIP) has emerged as a prominent foundation model learning semantically structured visual representa- tions through large-scale alignment of images and natural language descriptions (Radford et al., 2021). Empirical studies show that language supervision enables CLIP to preserve meaningful intra-class feature variability, avoiding excessive feature collapse and improving robustness under heterogeneous data distributions (Wen et al., 2024). By grounding visual representations in language rather than dataset-specific labels, CLIP induces a semantically struc- tured feature space in which high-level concepts remain stable across domains and acquisition conditions (Bhalla et al., 2024). This property is particularly advantageous in multi-dataset settings, where visually dissimilar instances may share a common label but differ substantially in ap- pearance. As illustrated in Fig. 1, pretrained CLIP image embeddings assign higher similarity to soybean prompts in crop-dominant scenes and to weed prompts in weed- dense images, demonstrating zero-shot semantic sensitivity to agricultural content. Unlike conventional CNN encoders trained under closed-vocabulary supervision, CLIP repre- sentations are open-vocabulary and less tied to dataset- specific visual statistics, reducing sensitivity to label noise and domain-specific shortcuts (Bourigault and Bourigault, 2025). Language supervision further encourages CLIP to organize features around semantic identity rather than low- level visual similarity, preserving meaningful intra-class variation under heterogeneous data distributions. As a result, frozen CLIP encoders mitigate negative transfer in multi- dataset training by enforcing domain-invariant, semantically


## 3. Materials and Methods

To address the aforementioned limitations, we adopt a dual-encoder architecture (Fig. 2) that combines frozen CLIP embeddings with a task-specific spatial encoder, which captures fine-grained texture, shape, and boundary infor- mation required for dense pixel-level segmentation across heterogeneous agricultural datasets. The high-level spatial features produced by the spatial encoder are fused with global CLIP image embeddings to form a multimodal rep- resentation. This fused feature map is then modulated by the caption embedding through FiLM (Perez et al., 2018), allowing semantic cues to selectively emphasize or suppress feature channels. The resulting FiLM-modulated features are fused with low-level spatial representations to recover fine boundaries and generate the final segmentation output. We validate our method using four heterogeneous agricultural datasets.

3.1. Datasets and Annotations The study utilizes both a novel UAV soybean dataset and multiple publicly available agricultural benchmarks. This heterogeneous multi-dataset setting provides substan- tial variability in crop types and weed species, enabling robust performance analysis. In the following section, we provide detailed descriptions of data acquisition, annotation procedures, and characteristics for all datasets used in this study.

Page 3 of 16

Vision-Language Model for Crop-Weed Segmentation


> **Figure 3: Study area and UAV orthomosaic of the experimental field. The figure illustrates the geographic context of the study**

> site. The top-left panel shows the location of Sainte-Anne-de-Bellevue within the Province of Quebec, Canada, where the study
area is located. The top-right panel presents an aerial view of the surrounding agricultural landscape, highlighting the specific
experimental plot (outlined in red; 88 m × 18 m). The bottom panel displays the high-resolution UAV orthomosaic acquired using
a DJI Mavic 3 Multispectral (M3M) at 5 m altitude, with a spatial scale bar provided for reference.

3.1.2. Phenobench Dataset

3.1.1. UAV Soybean Dataset

PhenoBench is a large, publicly available dataset and benchmark suite for plant perception under real agricultural field conditions (Weyler et al., 2024). The dataset comprises 2872 high-resolution RGB image tiles (1024 × 1024 pixels) acquired using a UAV at a flight height of 21 m over sugar beet fields, resulting in a GSD of approximately 1 mm/pixel. Images were collected across multiple acquisition dates dur- ing a growing season, capturing substantial variability in plant growth stages and illumination conditions. Of the total dataset, 1407 images are designated for training and 772 images for validation and are publicly available, while the remaining data form a hidden test set used for stan- dardized benchmarking. PhenoBench provides dense pixel- wise annotations for semantic segmentation, including soil, crop, weed, and partial-visibility classes, as well as instance segmentation of plants and leaves. Crop instances are tem- porally linked across acquisition dates, enabling longitudinal analysis of individual plant development. In addition to the labeled data, approximately 129000 unlabeled images are released to support research on self-supervised learning and domain adaptation in agricultural vision systems.

We collected data from an actively managed soybean field at the Emile A. Lods Agronomy Research Centre of McGill University (Sainte-Anne-de-Bellevue, QC, Canada). We selected soybean as the target crop as it is a major field crop in Canada and soybean fields can often exhibit a high weed prevalence, presenting a representative scenario for crop-weed segmentation. An overview of the study area and the UAV-acquired orthomosaic of the experimental field are shown in Fig. 3. We acquired UAV RGB imagery using a DJI Mavic 3 Multispectral (M3M) drone at an altitude of 5 m, covering an approximate area of 88 m × 18 m with a GSD of 1.4 mm/pixel. The acquired images were processed to generate a georeferenced orthomosaic with uniform spatial resolution. We then partitioned the high-resolution orthomo- saic into 7606 tiles of 512 × 512 pixel with 25% overlap to preserve the spatial continuity of crop and weed boundaries. Tiles containing more than 50% non-informative pixels were discarded, and 293 images from the resulting set were man- ually annotated using LabelMe for semantic segmentation with three classes: background (soil), crop (soybean), and weed. For semantic segmentation, soybean plants were la- beled as the crop class, while all other vegetation was labeled as weed. The resulting UAV Soybean-VL dataset builds upon the UAV Soybean dataset originally introduced in our prior work (Hossain et al., 2025). For this study, we apply a slightly revised data split by merging the original test set into the training set and reconstructing the validation set to emphasize more challenging weed density cases, while keeping the overall dataset composition unchanged. Under this protocol, the dataset comprises 262 training images and 30 validation images.

3.1.3. GrowingSoy Dataset

GrowingSoy is an instance-segmentation dataset for soy- bean and weed detection, consisting of 1000 manually an- notated RGB images resized to 640 × 640 pixels (Steinmetz et al., 2024). The images are extracted from 4K videos acquired in a dedicated soybean research field and span the full crop growth cycle, from early emergence to harvest. Data were collected at an experimental soybean plantation of the Universidade Federal de Santa Maria (Santa Maria,

Page 4 of 16

Vision-Language Model for Crop-Weed Segmentation


> **Figure 4: Representative RGB image tiles and corresponding ground-truth segmentation masks from the four weed segmentation**

> datasets used in this study: UAV Soybean, PhenoBench, GrowingSoy, and ROSE. For each dataset, paired image-mask examples
are shown, with RGB images on the left and manually annotated masks on the right. Mask colors denote background (black),
crop (green), and weed (red). The datasets span diverse crop types, weed densities, and imaging conditions„ including aerial and
ground-based imagery.

3.2. Image Captions for Vision-Language Segmentation To enable vision-language learning, we pair each im- age tile from all datasets with an image-level, agronomy- aware caption. Captions are generated using a large language model (LLM) (GPT-4o-mini (OpenAI, 2024)) with a fixed prompt template that enforces a consistent structure across samples. Each caption describes the presence of crops and weeds, their coarse spatial arrangement, and salient visual characteristics observable in the image. This caption design is inspired by AgroGPT, which demonstrated that struc- tured, domain-aware image descriptions with dataset spe- cific attributes synthesized by LLMs for agricultural datasets can effectively inject expert knowledge into vision-language learning pipelines (Awais et al., 2025). Representative ex- amples of the generated captions are shown in Fig. 5. These image-caption pairs serve as multi-modal training inputs for the proposed VL-WS framework, ensuring semantic align- ment between textual descriptions and visual content.

Brazil) using a 4K camera mounted on an all-terrain four- wheeled vehicle. The dataset includes soybean plants and common weed species, such as caruru and grassy weeds.

3.1.4. ROSE Dataset

The ROSE (RObotics and Sensors at the Service of Eco- phyto) dataset is a multi-robot agricultural benchmark de- signed for weed segmentation, with a particular emphasis on robustness to environmental variability and domain shift (Avrin et al., 2020). It comprises images of maize (Zea mays) and bean fields (Phaseolus vulgaris) acquired by four differ- ent agricultural robots, introducing substantial variation in sensing modalities, camera configurations, and acquisition conditions. The dataset provides pixel-wise segmentation masks for crop and weed classes, with annotations covering multiple weed species that are merged into a single weed class for evaluation. ROSE is widely used to assess the generalization capability of segmentation models, including few-shot and domain-robust approaches, by training on data from multiple robots and evaluating on previously unseen robotic platforms. In our experiments, we used a subset of the dataset consisting of 250 images of bean crops and weeds. Representative image tiles and annotations from the UAV Soybean, PhenoBench, GrowingSoy, and ROSE datasets are shown in Fig. 4, highlighting the diversity in crop species, weed species, and acquisition conditions across datasets.

3.3. Proposed Network Architecture 3.3.1. Overview The proposed framework, VL-WS, addresses the fun- damental challenges of multi-dataset weed segmentation, including high intra-class variance due to morphologically diverse species and visual ambiguity between crops and weeds. Unlike conventional segmentation models that rely solely on visual features, VL-WS leverages frozen CLIP embeddings to ground pixel-level predictions in seman- tically meaningful concepts. As illustrated in Fig. 6, the

Page 5 of 16

Vision-Language Model for Crop-Weed Segmentation

The encoder outputs a hierarchical set of feature maps at

different scales. A low-level feature map 𝐹𝐿∈ℝ256× 𝐻


## 4 × 𝑊

4 ,
extracted from early convolutional layers, retains fine spatial
detail essential for boundary refinement. In contrast, the


## 8 × 𝑊

8 , produced after
stage 4, captures high-level semantic context. This high-
level representation is then passed through the Atrous Spatial
Pyramid Pooling (ASPP) module, which aggregates multi-
scale context through parallel atrous convolutions with dila-
tion rates of 12, 24, and 36. The ASPP module also includes a
1 × 1 convolution branch and an image-level pooling branch
that performs global average pooling followed by a 1 × 1
convolution and bilinear upsampling. The outputs from all
ASPP branches are concatenated and projected through a

deepest feature map 𝐹𝐷∈ℝ2048× 𝐻


## 8 × 𝑊

8 .

final 1 × 1 convolution, yielding 𝐹ASPP ∈ℝ256× 𝐻

3.3.3. Language and Image Embeddings via CLIP CLIP is a large-scale vision-language model trained on paired image-text data to learn a shared embedding space that aligns visual content with linguistic semantics. This joint training provides CLIP with strong semantic priors that are transferable across domains and robust to appearance variation. We leverage these properties to inject high-level semantic context into pixel-level segmentation using CLIP- derived global features and text embeddings.


> **Figure 5: Example RGB image tiles paired with agronomy-**

> aware natural language captions generated for each dataset
(UAV Soybean, PhenoBench, GrowingSoy, and ROSE). Cap-
tions are produced using a standardized template and describe
crop and weed presence, coarse spatial layout, and salient visual
attributes. These image-caption pairs serve as multimodal
inputs for training and evaluating the proposed vision-language
segmentation framework.

Global Image Encoding. The input image is resized to 224 × 224 and passed through the CLIP image encoder to obtain a 512-dimensional global embedding. This em- bedding is linearly projected to 256 dimensions, yielding 𝐸vis ∈ℝ256, which captures scene-level semantics that are less sensitive to local texture variation or sensor noise. To preserve the pretrained vision-language alignment, the CLIP image encoder is kept fully frozen during training, with only the projection layer being optimized.


## architecture consists of two complementary visual encod-

ing streams. A spatial backbone with atrous convolutions
extracts multi-scale features while preserving fine-grained
boundary details, whereas a frozen CLIP image encoder
provides global semantic representations that remain stable
across diverse agricultural domains. These visual features
are subsequently fused and conditioned using agronomy-
aware captions through FiLM. Text embeddings modulate
feature channels to emphasize semantically relevant patterns
and reduce sensitivity to domain-specific variation.

Text Encoding. In parallel with global image encoding, the corresponding natural language caption (e.g., “Soybean center with scattered weeds”) is tokenized and processed by the CLIP text encoder to produce a 512-dimensional embedding. This embedding is then projected to 256 dimen- sions, producing 𝐸txt ∈ℝ256. To adapt the representation to domain-specific agricultural terminology while retaining general language understanding, the final two transformer layers of the text encoder are fine-tuned during training.

3.3.2. Visual Encoder Backbone The spatial encoder in the VL-WS model is built on the DeepLabv3+ architecture. We adopt a ResNet-101 back- bone with atrous convolutions configured for an output stride of 8 for preserving fine spatial detail while capturing rich semantic context. This higher-resolution representation is important for distinguishing morphologically similar crop and weed structures in agricultural images. In its standard form, ResNet-101 reduces spatial resolution by a factor of 32 through successive pooling and strided convolutions. Such aggressive downsampling eliminates fine details es- sential for boundary delineation in dense prediction tasks. To mitigate this limitation, DeepLabv3+ replaces strided convolutions in the last two residual blocks with atrous (dilated) convolutions, resulting in effective dilation rates of 2 and 4 in the final encoder stages. This design maintains a large receptive field while preserving feature maps at one- eighth of the input resolution.

3.3.4. Multimodal Fusion and FiLM Modulation This module fuses dense spatial features with global vi- sual embeddings and applies caption-conditioned modula- tion to guide segmentation. The ASPP feature map 𝐹ASPP ∈


## 8 × 𝑊

8
is concatenated channel-wise with the CLIP
image embedding 𝐸vis ∈ℝ256, which is spatially broadcast
to match the ASPP resolution, yielding the fused representa-

ℝ256× 𝐻

tion 𝐹fused ∈ℝ512× 𝐻


## 8 × 𝑊

8 . Feature-wise Linear Modulation
(FiLM) is then applied to dynamically condition the fused
features on the input caption. The text embedding 𝐸txt ∈

Page 6 of 16

Vision-Language Model for Crop-Weed Segmentation


> **Figure 6: Detailed architecture of the proposed vision-language weed segmentation framework.**

ℝ256, obtained by linearly projecting the CLIP text encoder output, is used to generate element-wise scaling 𝛾(𝐸txt) and shifting 𝛽(𝐸txt) parameters for the FiLM operation, which modulate the fused features as̃

seg = 𝜆Dice ⋅Dice + 𝜆CE ⋅CE, (2)

where we set 𝜆Dice = 0.6 and 𝜆CE = 0.4. Both loss components operate over class probabilities obtained via softmax.

𝐹= 𝛾(𝐸txt) ⊙𝐹fused + 𝛽(𝐸txt). (1)

This caption-conditioned modulation selectively empha- sizes feature channels aligned with the semantic content of the caption and guides the decoder toward semantically consistent segmentation across heterogeneous datasets.

Dice Loss. Dice Loss encourages region-level agreement, especially useful in imbalanced datasets (e.g., weed vs. background):

3.3.5. Decoder The modulated features are refined using a DeepLabv3+ style decoder to recover precise object boundaries. First,̃ 𝐹is bilinearly upsampled by a factor of 2 and concatenated with low-level features from the backbone, which are compressed to 48 channels via a 1×1 convolution. This fusion produces a 304-channel representation that is processed by two succes- sive 3×3 convolutions, reducing the channel dimensionality to 256. A final 1×1 convolution generates logits for the three semantic classes: background, crop, and weed.


## 2 ∑𝑁

𝑖=1 𝑝𝑖𝑐𝑦𝑖𝑐
∑𝑁

𝐶 ∑

Dice = 1 −1

. (3)

𝑖=1 𝑝𝑖𝑐+ ∑𝑁

𝐶

𝑖=1 𝑦𝑖𝑐+ 𝜀

𝑐=1

Here, 𝐶denotes the number of semantic classes, and 𝑁 is the total number of pixels. For each pixel 𝑖and class 𝑐, 𝑝𝑖𝑐represents the predicted softmax probability, while 𝑦𝑖𝑐∈{0, 1} is the corresponding one-hot ground-truth label. A small constant 𝜀is added for numerical stability.

Cross-Entropy Loss. Cross-Entropy Loss penalizes pixel- wise misclassifications by comparing the predicted class masks against the one-hot encoded ground-truth labels. For a multi-class segmentation task with 𝐶classes and 𝑁pixels, the weighted categorical cross-entropy loss is defined as:

3.4. Loss Function VL-WS is trained using a composite loss that combines a weighted segmentation loss with a vision-language con- trastive loss, enabling accurate pixel-level predictions while enforcing alignment between spatial features and textual semantics.

𝑁 ∑

𝐶 ∑

CE(𝑦, 𝑝) = −1

𝑤𝑐𝑦𝑖,𝑐log(𝑝𝑖,𝑐), (4)

3.4.1. Segmentation Loss To supervise per-pixel classification, we adopt a hybrid Dice + Cross-Entropy loss to balance region-level overlap and pixel-wise correctness. The total segmentation loss is defined as:

𝑁

𝑖=1

𝑐=1

where 𝑦𝑖,𝑐denotes the one-hot ground-truth label for pixel 𝑖 and class 𝑐, and 𝑝𝑖,𝑐is the predicted probability for that class obtained from the softmax output. The class-specific weight

Page 7 of 16

Vision-Language Model for Crop-Weed Segmentation

𝑤𝑐is used to mitigate class imbalance by assigning a larger penalty to minority classes.


> **Table 1**

> Aggregated segmentation performance (Dice %) across all
datasets.

3.4.2. Vision-Language Contrastive Loss To reinforce semantic alignment between textual labels and global image features, we incorporate a symmetric In- foNCE loss following Radford et al. (2021) and Zhang et al. (2022). Given a batch of 𝑁paired image-text embeddings {(𝑣𝑖, 𝑡𝑖)}𝑁

Method Weed Crop Bg Avg

UNet 61.45 95.73 99.56 85.58 PSPNet 63.47 93.04 99.08 85.19 DeepLabv3+ 65.03 95.48 99.47 86.66 VL-WS 80.45 95.23 99.24 91.64

𝑖=1, where 𝑣𝑖and 𝑡𝑖denote the visual and textual representations, we first normalize both embeddings:̂

where 𝑃𝑐and 𝐺𝑐denote the sets of pixels predicted as and labeled as class 𝑐, respectively. Dice is computed globally per class across the validation set and then averaged over classes. This metric is particularly well suited for crop-weed segmentation due to its robustness to class imbalance and its emphasis on accurate region-level overlap.

𝑖 )), (visual embedding)

𝑣𝑖= normalize(mean(𝑓img

(5)̂

𝑡𝑖= normalize(𝑓text

𝑖 ), (text embedding)

(6)

The image-to-text and text-to-image contrastive objec- tives are defined as:

Training details. All experiments were conducted on a workstation equipped with an NVIDIA RTX 3080 GPU (10 GB). Input images are resized to 512 × 512 pixels, and the model is implemented in PyTorch using PyTorch Lightning. We employ the AdamW optimizer with an initial learning rate of 3×10−5 for the visual encoder and 3×10−6 for the text encoder. Training is performed for 200 epochs using a cosine annealing learning rate schedule with a minimum learning rate of 1 × 10−7, a batch size of 8 and early stopping with a patience of 30 epochs.

𝑖 = −log exp(⟨̂𝑣𝑖,̂ 𝑡𝑖⟩∕𝜏) ∑𝑁

𝓁(𝑣→𝑡)

, (7)

𝑘=1 exp(⟨̂𝑣𝑖,̂ 𝑡𝑘⟩∕𝜏)

𝑖 = −log exp(⟨̂𝑡𝑖,̂ 𝑣𝑖⟩∕𝜏) ∑𝑁

𝓁(𝑡→𝑣)

, (8)

𝑘=1 exp(⟨̂𝑡𝑖,̂ 𝑣𝑘⟩∕𝜏)

where ⟨̂𝑣,̂ 𝑡⟩=̂ 𝑣⊤̂𝑡denotes cosine similarity and 𝜏is a temperature hyper-parameter set to 0.07.

The final symmetric contrastive loss is averaged across both modalities:

Baselines. We evaluate our approach against three widely used semantic segmentation baselines including DeepLabv3+ (Chen et al., 2018), U-Net (Ronneberger et al., 2015), and PSPNet (Zhao et al., 2017). DeepLabv3+ is selected as the primary baseline due to its strong ability to capture multi- scale context, while U-Net and PSPNet provide represen- tative encoder-decoder and pyramid pooling architectures. These baselines are chosen to represent strong unimodal CNN-based methods commonly used in agricultural seman- tic segmentation.

𝑁 ∑

). (9)

(𝓁(𝑣→𝑡)

VL = 1 2𝑁

𝑖 + 𝓁(𝑡→𝑣)

𝑖

𝑖=1

This bidirectional InfoNCE objective encourages each image embedding to be most similar to its corresponding textual description while remaining dissimilar to other texts within the batch, promoting semantically aligned feature representations.

3.4.3. Total Loss The final loss function combines segmentation and vision- language components:


## 4. Results and Discussion

4.1. Comparative Analysis with Standard Baselines All models were trained and evaluated in a multi-dataset setting comprising UAV Soybean, PhenoBench, Growing- Soy, and ROSE. This experimental setup reflects a realistic deployment scenario characterized by substantial domain variability in crop types, weed species, imaging conditions, and sensing platforms.

total = seg + 𝜆VL ⋅VL, 𝜆VL = 0.02 (10)

The contrastive term acts as an auxiliary supervision signal that enhances the semantic expressiveness of the visual encoder and improves model generalization across heterogeneous domains.

3.5. Implementation Details Evaluation Metric. Segmentation performance is primar- ily evaluated using the Dice coefficient, which measures the spatial overlap between predicted and ground-truth regions. For a given class 𝑐, the Dice score is defined as

4.1.1. Aggregated Performance Analysis The aggregated quantitative results across the multi- domain test set are reported in Table 1. VL-WS achieves competitive performance relative to state-of-the-art seg- mentation models under multi-dataset training conditions, attaining a mean Dice score of 91.64% across the weed, crop, and background classes. VL-WS outperforms the strongest

Dice𝑐= 2|𝑃𝑐∩𝐺𝑐|

|𝑃𝑐| + |𝐺𝑐|, (11)

Page 8 of 16

Vision-Language Model for Crop-Weed Segmentation


> **Table 2**

> Dataset-wise segmentation performance (Dice %) of the proposed model and baseline methods across four agricultural datasets.

Method UAV Soybean PhenoBench GrowingSoy ROSE

Weed Crop Bg Weed Crop Bg Weed Crop Bg Weed Crop Bg

UNet 79.02 98.12 96.73 58.27 96.57 99.70 75.84 92.62 98.80 43.97 88.25 97.11 PSPNet 69.34 97.28 93.98 59.07 93.29 99.22 76.42 91.22 98.35 62.53 90.69 96.75 Deeplabv3+ 74.48 98.12 95.53 60.33 96.10 99.62 75.30 92.51 98.65 65.19 90.92 96.85 VL-WS 80.40 98.21 96.47 77.57 95.84 99.49 86.09 92.98 98.66 75.66 92.49 97.30

the generalization challenge. The pronounced performance gap between the VL-WS and standard CNN baselines sug- gests that conventional architectures suffer from negative transfer when trained jointly on heterogeneous multi-domain datasets. These models overfit superficial domain-specific cues (e.g. texture or sensor noise) instead of learning seman- tically grounded, generalizable plant representations.

unimodal baseline, DeepLabv3+, which achieves an average Dice score of 86.66%, yielding an absolute improvement of 4.98%. Other CNN-based architectures exhibit notably lower performance, with U-Net achieving 85.58% and PSPNet achieving 85.19% mean Dice scores. These results highlight the limitations of purely visual encoders in multi-domain agricultural settings, where domain shift and high intra-class variability present significant challenges.

Crop Class Performance. All models achieve strong and comparable performance in the crop class. U-Net achieves a Dice score of 95.73%, DeepLabv3+ achieves 95.48%, VL- WS achieves 95.23%, and PSPNet achieves 93.04%. The marginal performance differences among the top-performing models indicate that crop segmentation has largely saturated under current evaluation settings, offering minimal scope for further improvement.

CNN-based segmentation models, such as DeepLabv3+ and PSPNet, incorporate architectural mechanisms for con- textual reasoning, ASPP and pyramid pooling modules, re- spectively. However, these purely visual mechanisms prove to be insufficient for robust cross-domain generalization. Models that rely exclusively on spatial features and low- level visual patterns struggle to distinguish fine-grained similarities between morphologically diverse weed species and young crop plants. This limitation is most evident in the performance of the weed class.

Background Class Performance. All models achieve near-ceiling performance on the background class, with Dice scores of 99.56% (U-Net), 99.47% (DeepLabv3+), 99.24% (VL-SM), and 99.08% (PSPNet). This suggests that background-vegetation discrimination has saturated under current segmentation architectures. Consequently, the substantial performance gains of the proposed VL-WS over baseline methods arise primarily from improved weed segmentation, rather than marginal improvements in crop or background classification.

4.1.2. Class-Wise Performance Analysis A class-wise analysis provides deeper insight into the sources of performance improvement, revealing that the gains of VL-WS are concentrated in the most challenging semantic category.

Weed Class Performance. The weed class exhibits the largest performance disparity between VL-SM and baseline methods, reflecting the inherent difficulty of weed segmen- tation in precision agriculture. VL-WS achieves an average of weed Dice score of 80.45%, substantially outperform- ing DeepLabv3+ (65.03%), PSPNet (63.47%), and U-Net (61.45%) across the four datasets (Table 1). This corre- sponds to a 15.42% improvement over DeepLabv3+. The difficulty of weed segmentation stems from multiple com- pounding factors. During early growth stages, crops and weeds exhibit highly similar spectral and morphological characteristics, limiting discriminative visual cues and in- creasing pixel-level ambiguity. Moreover, the weed class exhibits substantially higher intra-class variance than crop. Although the crop class typically corresponds to a single species per dataset (e.g. soybean in UAV Soybean or com- mon bean in ROSE), the weed class aggregates multiple distinct species even within a single dataset. Across the combined dataset benchmark, weed class encompasses ap- proximately 12-14 morphologically and spectrally distinct weed types. This high intra-class heterogeneity exacerbates

4.1.3. Dataset-Wise Weed Segmentation Performance Across all four benchmark datasets (UAV Soybean, Phe- noBench, GrowingSoy, and ROSE), the VL-WS model con- sistently outperforms all baseline methods on weed seg- mentation, as summarized in Table 2. On UAV Soybean, VL-WS achieves a weed Dice score of 80.40%, exceeding DeepLabv3+, PSPNet, and U-Net by margins of 5.92%, 11.06% and 1.38%, respectively. The performance gap is more pronounced on PhenoBench, where VL-WS attains a weed Dice score of 77.57%, substantially outperforming all comparison models. VL-WS achieves its highest weed Dice score on GrowingSoy (86.09%), surpassing DeepLabv3+ by 10.79%. On the ROSE dataset, VL-WS maintains robust performance with a weed Dice score of 75.66%, outperform- ing all baselines. Moreover, VL-WS exhibits the smallest variance in weed segmentation performance across datasets (75.66%-86.09%) compared to DeepLabv3+, U-Net, and PSPNet, demonstrating superior cross-domain consistency.

Page 9 of 16

Vision-Language Model for Crop-Weed Segmentation


> **Table 3**

> Domain adaptation performance under limited target-domain supervision. Class-wise Dice (%) scores obtained by training on
three full source datasets and varying fractions of labeled target-domain data.

Target Dataset Source Datasets Class Target-Domain Training Data 10% 20% 50% 100%

Weed 68.63 74.63 79.95 80.40 Crop 96.92 97.31 98.06 98.21 Background 94.80 95.95 96.37 96.47 Mean 86.78 89.29 91.46 91.69

UAV Soybean PhenoBench + GrowingSoy

+ ROSE

Weed 69.94 73.66 75.71 77.57 Crop 94.18 95.26 95.59 95.84 Background 99.30 99.43 99.46 99.49 Mean 87.80 89.45 90.25 90.96

PhenoBench UAV Soybean + GrowingSoy

+ ROSE

Weed 78.21 81.20 84.37 86.09 Crop 90.99 91.74 92.14 92.98 Background 98.40 98.49 98.53 98.66 Mean 89.20 90.47 91.68 92.57

GrowingSoy UAV Soybean + PhenoBench

+ ROSE

Weed 61.89 70.78 72.42 75.66 Crop 87.15 91.54 92.14 92.49 Background 95.99 97.09 97.27 97.30 Mean 81.67 86.47 87.27 88.48

ROSE UAV Soybean + PhenoBench

+ GrowingSoy

4.2. Domain Adaptation and Sample Efficiency To assess the data efficiency of the VL-WS model, we evaluate its performance under varying levels of target- domain supervision. For each target dataset, the model is trained using the full training sets of the three remaining datasets together with different fractions of labeled data from the target domain (10%, 20%, 50%, and 100%). The validation split of the target dataset is kept fixed through- out. This evaluation protocol reflects realistic deployment scenarios in which models pre-trained on auxiliary domains must adapt to new environments under limited annotation budgets. Table 3 reports class-wise Dice scores across all four target datasets under different data availability regimes. VL-WS maintains strong performance even under minimal supervision. In particular, weed segmentation accuracy re- mains close to the full-data setting when trained with 50% of the target-domain annotations and then degrades gradually as the amount of target-domain data is further reduced. Background and crop classes show minimal sensitivity to data availability, with Dice scores consistently exceeding 90% across most settings. Overall, these results demonstrate the data efficiency and cross-domain generalization capa- bility of the proposed framework, highlighting its practical applicability in agricultural scenarios where labeled data are limited.


> **Table 4**

> Ablation study on the vision-language contrastive loss weight
(𝜆VL). Class-wise and mean Dice (%) scores are reported across
the multi-dataset benchmark.

𝜆VL Weed Crop Bg Average

0.01 79.93 95.11 99.22 91.42 0.02 80.45 95.23 99.24 91.64 0.03 80.00 95.23 99.25 91.49 0.05 80.41 95.33 99.25 91.66 0.10 80.16 95.26 99.25 91.55

4.4. Visual Analysis of Results Fig.7 presents qualitative comparisons with two repre- sentative sample images from each dataset, showing ground truth annotations alongside predictions from baseline meth- ods and our model. Our model produces predictions that closely align with ground truth in spatial extent and bound- ary delineation. In densely interwoven crop-weed regions, baselines generate fragmented predictions with blurred bound- aries and class leakage, while our approach produces sharper, more coherent segmentation. While baselines struggle with visually similar early-stage crops and weeds, our model effectively distinguishes between classes and maintains consistent performance across diverse crop types, weed species, and imaging conditions. Additional results in Fig. 8 illustrate robustness to data heterogeneity through pre- diction overlays. Examples span varied lighting conditions, background types, growth stages, and platforms (UAV and ground-based), with stable performance despite signifi- cant variation in GSD. Fig.9 shows field-scale weed maps generated by stitching predictions from individual image tiles. These maps reveal spatial weed distribution patterns

4.3. Ablation Study on Vision–Language Loss Table 4 reports segmentation performance under different values of the vision-language contrastive loss weight 𝜆VL. Weed Dice improves as 𝜆VL increases from 0.01 to 0.02, reaching its peak at 𝜆VL = 0.02, after which performance plateaus or slightly declines. Crop segmentation exhibits marginal but consistent improvements with increasing 𝜆VL, while background Dice remains stable across all settings.

Page 10 of 16

Vision-Language Model for Crop-Weed Segmentation


> **Figure 7: Qualitative comparison of segmentation results across datasets for the proposed model and baseline methods.**

> Segmentation masks show crop in green, weed in red, and background in black.

across the entire field, identifying heavily infested regions and clean areas. Such spatially continuous representations enable targeted weed management for precision agriculture applications.

as crop in the ground truth but predicted as background by the model. Visual inspection of the input image indicates that this region corresponds to bare soil visible between leaf gaps, suggesting that the model prediction is more consistent with the actual image. Similarly, in (d), the model predicts weed pixels in a region labeled as background in the ground truth, while the input image shows clear weed pres- ence, indicating a potential labeling error. These cases high- light a common challenge in crop-weed datasets. Fine-scale plant morphology, overlapping vegetation, and complex leaf structures make precise pixel-level annotation difficult and

Error Analysis. Fig. 10 presents a qualitative error analy- sis across four challenging cases. For each example, the input image, ground-truth annotation, and VL-WS model predic- tion are shown, with yellow boxes highlighting regions of discrepancy between prediction and ground truth. Examples (a) and (d) reveal annotation inconsistencies in the ground- truth labels. In (a), one of the highlighted regions is labeled

Page 11 of 16

Vision-Language Model for Crop-Weed Segmentation


> **Figure 8: Qualitative segmentation results of the proposed VL-WS model across four agricultural datasets, demonstrating robust**

> weed detection under varying lighting conditions, background textures, crop growth stages, and sensing platforms, including
UAV and ground-based imagery. Predictions are overlaid on input images with green indicating crop, red indicating weed, and
semi-transparent regions showing background.

4.5. Discussion

can introduce label noise. Examples (a), (b), and (c) illus- trate actual error cases driven by visual ambiguity. In these regions, crops and weeds exhibit highly similar appearance with overlapping foliage and poorly defined boundaries. As a result, the model struggles in ambiguous transition zones where discriminative visual cues are limited.

Experimental results demonstrate that, in the multi-dataset setting, the proposed VL-WS model consistently outper- forms standard CNN-based architectures for weed segmen- tation, highlighting the effectiveness of vision-language semantic grounding over purely visual feature learning in

Page 12 of 16

Vision-Language Model for Crop-Weed Segmentation


> **Figure 9: Field-scale weed segmentation results and zoomed predictions. (a) RGB orthomosaic of the soybean field. (b) Predicted**

> weed distribution map with green indicating crop, red indicating weed, and black indicating background. (c)—(f) Zoomed
predictions from four field regions (top row) with corresponding RGB imagery (bottom row).

efficiency. Additionally, FiLM-based modulation enables context-aware adaptation by selectively enhancing semanti- cally relevant features while preserving the shared semantic knowledge from vision-language pretraining, allowing the model to accommodate dataset-specific variation without compromising cross-domain transferability.


> **Figure 10: Qualitative error analysis of crop-weed segmen-**

> tation predictions. Predicted segmentation masks are shown,
with yellow boxes highlighting regions of inconsistency between
model predictions and the ground truth, illustrating common
failure cases under challenging field conditions.

Beyond comparisons with standard CNN baselines in the multi-dataset setting, the proposed framework further demonstrates competitive performance when compared to prior state-of-the-art methods evaluated on single-dataset agricultural benchmarks. In the PhenoBench dataset, which provides standardized benchmarks for semantic segmenta- tion alongside other plant perception tasks (Weyler et al., 2024), existing results are reported for DeepLabV3+ and ERFNet. DeepLabV3+ achieves IoU scores of 64.59% (weed), 94.07% (crop), and 99.25% (soil), while a Bayesian DeepLabV3 variant with Monte Carlo dropout reports IoU values of 63.37% (weed), 94.60% (crop), and 99.33% (back- ground) on the validation set (Celikkan et al., 2023). In com- parison, VL-WS achieves Dice scores of 77.57% (weed), 95.84% (crop), and 99.49% (background). After conversion from Dice to IoU, these correspond to 63.35% (weed), 92.01% (crop), and 98.98% (background), demonstrating

agricultural segmentation tasks. Several factors contribute to this advantage, most notably the use of a frozen CLIP encoder, which stabilizes optimization by preventing the rep- resentation space from drifting as heterogeneous gradients are applied. This design decouples semantic understanding from spatial localization, allowing the model to rely on pre- trained vision-language semantics for identifying crop and weed concepts while learning precise boundaries through task-specific layers. As a result, the model reduces its depen- dence on costly pixel-level annotations and improves data

Page 13 of 16

Vision-Language Model for Crop-Weed Segmentation

performance comparable to established state-of-the-art meth- ods. Importantly, this performance is achieved under a multi- dataset training setting, whereas the reported benchmarks are obtained under single-dataset training.

A comparable trend is observed on the ROSE dataset, which is commonly used to evaluate robustness under en- vironmental variability and domain shift. Prior work by Catalano et al. (2024) reports a weed IoU of 60.39% in bean fields when trained on the full ROSE dataset. In our experi- ments, VL-WS is evaluated on a bean subset containing four weed species, split into training, validation, and test sets. On the validation set, VL-WS achieves a weed Dice score of 75.66%, corresponding to an IoU of 60.84%, which is closely aligned with the reported benchmark. For the Grow- ingSoy dataset, most prior studies focus on instance seg- mentation using YOLOv5 and YOLOv8 variants (Steinmetz et al., 2024), limiting direct comparison with semantic seg- mentation approaches. Nevertheless, the strong performance of VL-WS on GrowingSoy further supports its robustness across datasets with differing acquisition conditions. Collec- tively, these comparisons show that the proposed language- guided approach maintains competitive performance across both single and multi-domain benchmarks, matching single- dataset performance even under joint training on heteroge- neous datasets, unlike purely visual models that suffer from negative transfer.


> **Figure 11: Cross-dataset cosine similarity of deep feature**

> embeddings from pretrained CLIP and ResNet encoders.
Heatmaps showing pairwise cosine similarity between feature
embeddings of image tiles drawn from four weed segmentation
datasets: UAV Soybean, Phenobench, GrowingSoy, and ROSE.
(Left) CLIP encoder features exhibit high within-dataset and
substantial cross-dataset similarity, reflecting semantically rich
and more dataset-invariant representations. (Right) Features
extracted from a ResNet encoder (pretrained on ImageNet)
display strong clustering within datasets but markedly lower
similarity across datasets, indicating limited generalizability.
The cross-dataset feature alignment achieved by the CLIP
encoder supports improved robustness in multi-domain weed
segmentation tasks.

cues. By integrating semantically grounded features, VL- WS achieves domain-agnostic segmentation and reduced sensitivity to dataset-specific appearance shifts. Conse- quently, this design minimizes reliance on exhaustive, site- specific annotations and enables robust learning across heterogeneous agricultural environments.

As shown in Fig. 11, CLIP features exhibit strong similar- ity both within and across datasets, indicating a semantically consistent representation space. In contrast, features from an ImageNet-pretrained ResNet show strong within-dataset similarity but substantially lower cross-dataset similarity, reflecting sensitivity to dataset-specific visual characteris- tics. This contrast suggests that CLIP representations en- code higher-level semantics that generalize across crops, weed species, and imaging conditions, whereas purely visual features remain more tightly coupled to domain-specific appearance. This behavior is consistent with prior studies showing that image-only encoders tend to rely on low-level cues such as texture and color, while language supervision encourages representations organized around semantic con- cepts that are more robust to appearance variation.


## 5. Conclusion

We demonstrate that vision-language semantic grounding effectively addresses negative transfer and label heterogene- ity in multi-dataset agricultural segmentation. By combin- ing frozen CLIP representations with a learnable spatial encoder and caption-conditioned feature modulation, VL- WS decouples semantic understanding from spatial local- ization and substantially outperforms standard CNN base- lines in weed segmentation, while maintaining strong per- formance under limited supervision. These results highlight vision-language alignment as a promising foundation for ro- bust and generalizable segmentation across diverse agricul- tural environments. While the proposed architecture reduces performance degradation arising from intra-class variation across heterogeneous datasets, it does not fully eliminate negative transfer, as the trainable spatial encoder and de- coder remain susceptible to conflicting visual patterns from morphologically diverse weed species and varying imaging conditions during joint training. In addition, reliance on global image-level vision-language embeddings may limit the capture of fine-grained, spatially localized semantic dis- tinctions in densely interwoven crop-weed regions. Build- ing on the proposed framework, future work could further mitigate residual negative transfer by introducing stronger semantic regularization within the spatial encoder, as well

Overall, these results, together with quantitative com- parisons to prior work and the embedding space analysis, demonstrate that incorporating linguistic priors encourages a more semantically structured organization of the represen- tation space, reducing reliance on low-level visual cues. By shifting toward semantically grounded representations, the VL-WS framework supports more domain-agnostic segmen- tation behavior and mitigates sensitivity to dataset-specific appearance variations. This design reduces dependence on exhaustive, site-specific pixel-level annotations and facili- tates more effective learning under heterogeneous agricul- tural conditions.

Overall, these quantitative and qualitative analyzes demon- strate that linguistic priors induce a more structured repre- sentation space, reducing the reliance on low-level visual

Page 14 of 16

Vision-Language Model for Crop-Weed Segmentation

as spatially adaptive vision-language conditioning to better align semantic cues with visual features. The framework could also be extended to temporal learning settings, where multi-stage growth supervision captures morphological di- vergence between crops and weeds. Incorporating temporal cues together with multispectral or multi-modal inputs may further improve robustness under phenological variation and challenging field conditions.

Bhattacharjee, D., Süsstrunk, S., Salzmann, M., 2023. Vision transformer

adapters for generalizable multitask learning, in: Proceedings of the IEEE/CVF International Conference on Computer Vision, pp. 19015– 19026. Bourigault, E., Bourigault, P., 2025. Frevl: Leveraging frozen pretrained

embeddings for efficient vision-language understanding, in: Proceedings of the IEEE/CVF International Conference on Computer Vision, pp. 2327–2336. Catalano, N., Leone, M., Matteucci, M., 2024. Tackling environmental vari-

ability: Few shot segmentation for domain-adaptive weed segmentation in agricultural robotics, in: 2024 IEEE 20th International Conference on Automation Science and Engineering (CASE), IEEE. pp. 583–588. Celikkan, E., Saberioon, M., Herold, M., Klein, N., 2023. Semantic segmentation of crops and weeds with probabilistic modeling and un- certainty quantification, in: Proceedings of the IEEE/CVF International Conference on Computer Vision, pp. 582–592. Chen, L.C., Zhu, Y., Papandreou, G., Schroff, F., Adam, H., 2018. Encoder-

CRediT authorship contribution statement

Nazia Hossain: Data curation, Investigation, Methodol- ogy, Visualization, Formal analysis, Writing - original draft, Writing - review & editing. Xintong Jiang: Data curation, Investigation, Writing - review & editing. Yu Tian: Writing – review & editing. Philippe Seguin: Resources, Writing - review & editing. O. Grant Clark: Writing - review & editing. Shangpeng Sun: Conceptualization, Resources, Writing - review & editing, Supervision, Project administra- tion, Funding acquisition.

decoder with atrous separable convolution for semantic image segmen- tation, in: Proceedings of the European conference on computer vision (ECCV), pp. 801–818. Gao, J., Liao, W., Nuyttens, D., Lootens, P., Xue, W., Alexandersson, E.,

Pieters, J., 2024. Cross-domain transfer learning for weed segmentation and mapping in precision farming using ground and uav images. Expert Systems with applications 246, 122980. Guo, Z., Cai, D., Jin, Z., Xu, T., Yu, F., 2025a. Research on unmanned

aerial vehicle (uav) rice field weed sensing image segmentation method based on cnn-transformer. Computers and Electronics in Agriculture 229, 109719. Guo, Z., Xue, Y., Wang, C., Geng, Y., Lu, R., Li, H., Sun, D., Lou, Z., Chen,

Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

T., Shi, J., et al., 2025b. Efficient weed segmentation in maize fields: A semi-supervised approach for precision weed management with reduced annotation overhead. Computers and Electronics in Agriculture 229, 109707. Hossain, N., Rahman, S.T., Sun, S., 2025. An end-to-end deep learning

Acknowledgments

This research is supported by funding from the FRQNT & MAPAQ Partnership Research Program-Sustainable Agri- culture (Grant No. 259806), the McGill Collaborative for AI and Society Interdisciplinary Research Program (Grant No. 173165), and the RQRAD Emerging Project (Grant No. 265224). We thank Dr.Huong Nguyen for critically proofreading the manuscript.

framework for multi-scale cross-domain weed segmentation, in: 2025 ASABE Annual International Meeting, American Society of Agricul- tural and Biological Engineers. p. 1. Jiang, H., Zhang, C., Qiao, Y., Zhang, Z., Zhang, W., Song, C., 2020. Cnn

feature based graph convolutional network for weed and crop recognition in smart farming. Computers and electronics in agriculture 174, 105450. Lambert, J., Liu, Z., Sener, O., Hays, J., Koltun, V., 2020. Mseg: A compos-

ite dataset for multi-domain semantic segmentation, in: Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pp. 2879–2888. Li, Y., Guo, R., Li, R., Ji, R., Wu, M., Chen, D., Han, C., Han, R., Liu, Y.,

Data availability

Ruan, Y., et al., 2025. An improved u-net and attention mechanism-based model for sugar beet and weed segmentation. Frontiers in Plant Science 15, 1449514. OpenAI, 2024. Gpt-4o-mini: advancing cost-efficient intelligence. URL: https://openai.com/index/ gpt-4o-mini-advancing-cost-efficient-intelligence/. accessed: February 9, 2026. Perez, E., Strub, F., De Vries, H., Dumoulin, V., Courville, A., 2018. Film:

Data will be made available on request.


## References

Arshad, M.A., Jubery, T.Z., Roy, T., Nassiri, R., Singh, A.K., Singh, A.,

Hegde, C., Ganapathysubramanian, B., Balu, A., Krishnamurthy, A., et al., 2025. Leveraging vision language models for specialized agri- cultural tasks, in: 2025 IEEE/CVF Winter Conference on Applications of Computer Vision (WACV), IEEE. pp. 6320–6329. Asad, M.H., Anwar, S., Bais, A., 2024. Improved crop and weed detection

Visual reasoning with a general conditioning layer, in: Proceedings of the AAAI conference on artificial intelligence. Radford, A., Kim, J.W., Hallacy, C., Ramesh, A., Goh, G., Agarwal, S.,

with diverse data ensemble learning, in: Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 5336– 5345. Avrin, G., Boffety, D., Lardy-Fontan, S., Régnier, R., Rescoussié, R.,

Sastry, G., Askell, A., Mishkin, P., Clark, J., et al., 2021. Learning transferable visual models from natural language supervision, in: Inter- national conference on machine learning, PmLR. pp. 8748–8763. Ronneberger, O., Fischer, P., Brox, T., 2015. U-net: Convolutional networks

Barbosa, V., 2020. Design and validation of testing facilities for weeding robots as part of rose challenge, in: Evaluating Progress in IA (EPAI). Awais, M., Alharthi, A.H.S.A., Kumar, A., Cholakkal, H., Anwer, R.M.,

for biomedical image segmentation, in: International Conference on Medical image computing and computer-assisted intervention, Springer. pp. 234–241. Steinmetz, R., Kich, V.A., Krever, H., Mazzarolo, J.D.R., Grando, R.B.,

2025. Agrogpt: Efficient agricultural vision-language model with expert tuning, in: 2025 IEEE/CVF Winter Conference on Applications of Computer Vision (WACV), IEEE. pp. 5687–5696. Bhalla, U., Oesterling, A., Srinivas, S., Calmon, F., Lakkaraju, H., 2024. In-

Marini, V., Trois, C., Nieuwenhuizen, A., 2024. From seedling to har- vest: The growingsoy dataset for weed detection in soy crops via instance segmentation, in: 2024 IEEE International Conference on Cybernetics and Intelligent Systems (CIS) and IEEE International Conference on

terpreting clip with sparse linear concept embeddings (splice). Advances in Neural Information Processing Systems 37, 84298–84328.

Page 15 of 16

Vision-Language Model for Crop-Weed Segmentation

Robotics, Automation and Mechatronics (RAM), IEEE. pp. 502–507. Wang, Z., Dai, Z., Póczos, B., Carbonell, J., 2019. Characterizing and avoiding negative transfer, in: Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pp. 11293–11302. Wen, X., Zhao, B., Chen, Y., Pang, J., Qi, X., 2024. What makes clip more

robust to long-tailed pre-training data? a controlled study for transferable insights. Advances in Neural Information Processing Systems 37, 36567–36601. Weyler, J., Magistri, F., Marks, E., Chong, Y.L., Sodano, M., Roggiolani,

G., Chebrolu, N., Stachniss, C., Behley, J., 2024. Phenobench: A large dataset and benchmarks for semantic image interpretation in the agri- cultural domain. IEEE Transactions on Pattern Analysis and Machine Intelligence 46, 9583–9594. doi:10.1109/TPAMI.2024.3419548. Wu, H., Du, Z., Zhong, D., Wang, Y., Tao, C., 2025. Fsvlm: A vision-

language model for remote sensing farmland segmentation. IEEE Transactions on Geoscience and Remote Sensing . Xu, B., Fan, J., Chao, J., Arsenijevic, N., Werle, R., Zhang, Z., 2023.

Instance segmentation method for weed detection using uav imagery in soybean fields. Computers and Electronics in Agriculture 211, 107994. Xu, B., Werle, R., Chudzik, G., Zhang, Z., 2025. Enhancing weed detec-

tion using uav imagery and deep learning with weather-driven domain adaptation. Computers and Electronics in Agriculture 237, 110673. You, J., Liu, W., Lee, J., 2020. A dnn-based semantic segmentation for

detecting weed and crop. Computers and Electronics in Agriculture 178, 105750. Yu, G.H., Anh, L.H., Vu, D.T., Lee, J., Rahman, Z.U., Lee, H.Z., Jo, J.A.,

Kim, J.Y., 2025. Vl-paw: A vision–language dataset for pear, apple and weed. Electronics 14, 2087. Zhang, Y., Jiang, H., Miura, Y., Manning, C.D., Langlotz, C.P., 2022. Con-

trastive learning of medical visual representations from paired images and text, in: Machine learning for healthcare conference, PMLR. pp. 2– 25. Zhao, H., Shi, J., Qi, X., Wang, X., Jia, J., 2017. Pyramid scene parsing

network, in: Proceedings of the IEEE conference on computer vision and pattern recognition, pp. 2881–2890. Zhou, X., Koltun, V., Krähenbühl, P., 2022. Simple multi-dataset detection,

in: Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pp. 7571–7580.

Page 16 of 16
