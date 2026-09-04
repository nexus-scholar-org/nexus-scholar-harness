---
workspace_id: SCI-001023
doi: 10.3390/agriengineering7110388
title: "AgriFusion: Multiscale RGB\u2013NIR Fusion for Semantic Segmentation in Airborne\
  \ Agricultural Imagery"
authors:
- family_name: Li
  given_name: Xuechen
  orcid: null
- family_name: Qiao
  given_name: Lang
  orcid: null
- family_name: Yang
  given_name: Ce
  orcid: null
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:35:02.171721+00:00'
---

# AgriFusion: Multiscale RGB–NIR Fusion for Semantic Segmentation in Airborne Agricultural Imagery

Article AgriFusion: Multiscale RGB–NIR Fusion for Semantic

Segmentation in Airborne Agricultural Imagery

Xuechen Li , Lang Qiao * and Ce Yang *

Department of Bioproducts and Biosystems Engineering, University of Minnesota, Saint Paul, MN 55108, USA * Correspondence: lqiao@umn.edu (L.Q.); ceyang@umn.edu (C.Y.)


## Abstract

The rapid development of unmanned aerial vehicles (UAVs) and deep learning has ac- celerated the application of semantic segmentation in precision agriculture (SSPA). A key driver of this progress lies in multimodal fusion, which leverages complementary struc- tural, spectral, and physiological information to enhance the representation of complex agricultural scenes. Despite advancements, the efficacy of multimodal fusion in SSPA is limited by modality heterogeneity and the difficulty of simultaneously retaining fine details and capturing global context. To address these challenges, we propose AgriFusion, a dual- encoder framework based on convolutional and transformer architectures for SSPA tasks. Specifically, convolutional and transformer encoders are first used to extract crop-related local structural details and global contextual features from multimodal inputs. Then, an attention-based fusion module adaptively integrates these complementary features in a modality-aware manner. Finally, a MLP-based decoder aggregates multi-scale representa- tions to generate accurate segmentation results efficiently. Experiments conducted on the Agriculture-Vision dataset demonstrate that AgriFusion achieves a mean Intersection over Union (mIoU) of 49.31%, Pixel Accuracy (PA) of 81.72%, and F1 score of 67.85%, outperform- ing competitive baselines including SegFormer, DeepLab, and AAFormer. Ablation studies further reveal that unimodal or shallow fusion strategies suffer from limited discriminative capacity, whereas AgriFusion adaptively integrates complementary multimodal features and balances fine-grained local detail with global contextual information, yielding consis- tent improvements in identifying planting anomalies and crop stresses. These findings validate our central claims that modality-aware spectral fusion and balanced multi-scale representation are critical to advancing agricultural semantic segmentation, and establish AgriFusion as a principled framework for enhancing remote sensing-based monitoring with practical implications for sustainable crop management and precision farming.

Academic Editor: Ray E. Sheriff

Received: 7 October 2025

Revised: 28 October 2025

Accepted: 30 October 2025

Published: 15 November 2025

Citation: Li, X.; Qiao, L.; Yang, C.

Keywords: remote sensing; precision agriculture; multi-modal fusion; multispectral image; modality aware

AgriFusion: Multiscale RGB–NIR

Fusion for Semantic Segmentation in

Airborne Agricultural Imagery.

AgriEngineering 2025, 7, 388.

https://doi.org/10.3390/


## 1. Introduction

agriengineering7110388

In modern precision agriculture, timely and accurate monitoring of farmland is cru- cial for ensuring food security and enhancing agricultural sustainability [1]. In recent years, deep learning has become the dominant paradigm for analyzing agricultural remote sensing imagery, particularly for tasks such as semantic segmentation of crops and field structures. However, most existing studies rely primarily on RGB imagery, which, although widely accessible and low cost, is inherently limited in capturing crop physiological and spectral information beyond the visible range. In contrast, near-infrared (NIR) and other

Copyright: © 2025 by the authors.

Licensee MDPI, Basel, Switzerland.

This article is an open access article

distributed under the terms and

conditions of the Creative Commons

Attribution (CC BY) license

(https://creativecommons.org/

licenses/by/4.0/).

AgriEngineering 2025, 7, 388 https://doi.org/10.3390/agriengineering7110388

AgriEngineering 2025, 7, 388 2 of 20

multispectral bands provide complementary cues related to vegetation health and struc- tural patterns, enabling deep learning models to extract richer and more discriminative features [2]. Nevertheless, differences between modalities, as well as the design of effective fusion strategies, remain significant challenges; how to align heterogeneous feature spaces, exploit complementary information, and mitigate redundancy or noise continues to be a bottleneck restricting the full potential of multi-modal fusion in agricultural semantic segmentation. In this study, we focus on the fusion of two complementary modalities, RGB and NIR imagery. RGB provides structural and textural information such as canopy geometry and field patterns, while NIR captures spectral and physiological signals related to vegetation vigor and stress. Their combination enriches the representation of agricul- tural scenes and enhances the detection of anomalies that are difficult to identify with a single modality.

Within deep learning-based approaches for remote sensing semantic segmentation, two dominant paradigms have emerged: convolutional neural networks (CNNs) and Transformers. CNN-based methods remain the backbone of current research due to their strong capability in capturing local textures and hierarchical spatial features. A number of remote sensing-specific CNN variants have been proposed to adapt to the challenges of high-resolution aerial imagery. For example, Hi-ResNet enhances boundary and detail extraction through multi-branch aggregation and edge-aware loss [3], while IARU-Net integrates Inception modules and attention gates into a U-shaped CNN to better capture multi-scale context [4]. Further refinements include adaptations of DeepLab architectures that reduce model parameters while maintaining accuracy in land-cover segmentation [5], as well as HRNet-based approaches that enhance building and land-cover extraction via high-resolution multi-branch aggregation [6] or dynamic feature selection to mitigate class imbalance and scale variation [7]. Despite these advances, CNN-based methods are inherently limited by their restricted receptive field, which hampers their ability to capture long-range dependencies and effectively model cross-modal interactions, thereby motivating exploration of alternative architectures such as Transformers.

Transformer-based models have recently shown strong capabilities in capturing global context and aggregating multi-scale information for remote sensing semantic segmenta- tion. For instance, UNetFormer combines a CNN encoder with a Transformer decoder to efficiently capture global dependencies for real-time aerial scene segmentation [8,9], while AMTNet enhances multi-scale attention to integrate long-range context with local structural cues [10]. At the application level, Swin-UNet [11] combined with UPerNet [12] improves coastal vegetation and mangrove delineation in complex shoreline environments [13], and hybrid diffusion with SegFormer [14] strengthens land-use segmentation by producing sharper boundaries and stronger priors [15]. In the agricultural domain, HSI-TransUNet demonstrates the benefits of coupling spatial and spectral modeling to improve crop plot extraction from UAV-based hyperspectral imagery [16]. A recent survey further highlights how Transformers are reshaping optical, SAR, and hyperspectral image interpretation, while also noting practical challenges related to training data and computational costs [17].

Despite the progress of both CNN- and Transformer-based models, most existing approaches still rely on single-modality inputs, typically RGB imagery. However, RGB alone is inherently limited in capturing the full range of information critical for agricultural monitoring, particularly missing spectral cues beyond the visible range. This limitation has motivated increasing interest in spectral–spatial fusion, where complementary data such as NIR, multispectral, or hyperspectral imagery are integrated with RGB to enrich feature representation. Early fusion strategies often relied on simply stacking multi-band images as multi-channel inputs for convolutional networks [18,19], yet this naive approach is insufficient for leveraging the distinctive characteristics of spectral and spatial domains.

AgriEngineering 2025, 7, 388 3 of 20

More recent research has therefore explored mid- and late-fusion schemes, which assign dedicated modality-specific branches and perform fusion at the feature or decision level, generally achieving more robust results [20]. For instance, dual-branch RGB–NIR networks with cross-modal feature fusion, such as CMFNet, significantly improve weed delineation compared to RGB-only or simple concatenation [21]. Attention-based designs like YOLACT- Fusion further demonstrate that hierarchical attention mechanisms can effectively merge RGB spatial detail with NIR spectral cues, boosting segmentation of small structures in agricultural scenes [22]. Empirical evidence also supports the benefit of spectral–spatial fusion; combining visible and multispectral UAV data yields consistent accuracy gains of 1–4 percentage points in crop classification [23], while crop classification and field delin- eation using RGB and NIR fusion [24] and field-scale phenotyping frameworks integrating multimodal UAV imagery [25] further demonstrate the effectiveness of this approach across different agricultural scenarios. Recent hybrid CNN–Transformer architectures extend this direction by coupling modality-specific encoders with dynamic or attention-based fusion modules that adaptively weight RGB, NIR, and red-edge information, showing promising results in crop and weed segmentation [26].

Nevertheless, despite the progress of spectral–spatial fusion, most existing methods still suffer from inadequate integration of heterogeneous features and limited ability to aggregate multi-scale information. Simple concatenation or late-fusion designs often fail to fully exploit the complementary properties of RGB and NIR modalities, while attention- based fusion modules are typically applied only at a single scale, overlooking the hierarchi- cal nature of feature representations. These limitations restrict the discriminative power of current models in complex agricultural environments, where fine-grained boundaries and subtle spectral–spatial variations are critical. To simultaneously address the challenges of insufficient heterogeneous feature fusion, this paper proposes a novel Asymmetric Dual- Encoder Network, named AgriFusion. Specifically, we design an asymmetric dual-encoder architecture where a Transformer model (Mix Transformer (MiT)) captures the global con- text from RGB images while a CNN model (ResNet) extracts features from single-channel NIR images, enabling targeted modeling of heterogeneous data. In addition, a multi-level Attention Fusion Feature (AFF) module with local and global attention mechanisms is introduced to selectively and synergistically combine complementary features from the CNN and Transformer backbones. Furthermore, a MLP-based decoder is employed to efficiently aggregate the fused multi-scale features and generate fine-grained segmentation maps while reducing computational complexity. By organically integrating these three innovations, AgriFusion produces more discriminative feature representations, leading to more accurate and robust semantic segmentation in complex agricultural environments.


## 2. Method

2.1. Dataset

To rigorously evaluate the effectiveness of the proposed AgriFusion model, we em- ployed the Agriculture-Vision dataset [27], which has become a widely used benchmark for semantic segmentation in agricultural remote sensing. This dataset was curated to ac- celerate methodological advances in precision agriculture by providing a standardized and challenging evaluation platform. It consists of 94,986 high-quality aerial images collected from 3432 agricultural fields across the United States, with a ground sampling distance of up to 10 cm/pixel that enables fine-grained observation of crop conditions at the parcel level. A notable strength of Agriculture-Vision lies in its multi-spectral composition: unlike many traditional agricultural datasets that provide only RGB imagery, it includes both RGB and Near-Infrared (NIR) channels. The RGB channels contain visible light information (red, green, and blue), which captures fine structural details of farmland such as planting

AgriEngineering 2025, 7, 388 4 of 20

rows, field boundaries, and texture patterns. The NIR channel reflects physiological and spectral variations related to plant health, allowing the detection of vegetation vigor and stress conditions that are not visible in the RGB spectrum. Combining these two modalities provides both geometric accuracy and sensitivity to crop physiological status, which is es- sential for robust detection of diverse agricultural anomalies such as planter skips, nutrient deficiencies, and weed clusters. The NIR band is particularly sensitive to vegetation vigor and stress, offering critical physiological information that complements the structural and textural cues captured by RGB imagery [28]. By jointly exploiting these two modalities, the dataset supports more comprehensive semantic segmentation and provides a robust benchmark for evaluating fusion-based methods such as our AgriFusion network.

As illustrated in Figure 1, expert annotators manually labeled nine anomaly categories that are highly relevant to crop growth and field management: double plant (DP), dry down (DD), end row (DR), nutrient deficiency (ND), planter skip (PS), storm damage (SD), water (WT), waterway (WW), and weed cluster (WC). These categories encompass the most common anomalies and stressors encountered during the agricultural cycle, ensuring that the dataset reflects realistic and diverse farming scenarios. In our study, however, we adopted eight categories for training, validation, and testing because the storm damage class suffers from incomplete and inconsistent annotations, which may compromise fair evaluation. Following the official protocol, the dataset is divided into training (70%), validation (15%), and test (15%) subsets, a partition that ensures sufficient data for model optimization while preserving separate sets for hyperparameter tuning and unbiased evaluation.


> **Figure 1. Representative examples of anomaly categories in the Agriculture-Vision dataset. RGB and**

> NIR images are shown for each class. Colored regions indicate the annotated anomaly areas.

2.2. The Proposed Model

Our proposed framework, AgriFusion, addresses two major challenges in agricultural remote sensing segmentation: (1) the heterogeneous nature of multi-spectral data, particu- larly the complementary yet distinct characteristics of RGB–NIR bands, and (2) the need for robust multi-scale feature aggregation to handle targets ranging from fine-grained weeds to large-scale canopy damage. As shown in Figure 2, AgriFusion integrates three key com- ponents: an Asymmetric Dual-Encoder, which uses MiT-B1 (RGB) with ResNet-18 (NIR) to extract modality-specific features; Attention Fusion Feature (AFF) modules, inserted at multiple stages to selectively integrate both modalities through local–global attention; and an MLP-based Decoder, inspired by SegFormer, which aggregates fused multi-scale features via MLP projection plus bilinear upsampling to generate high-resolution segmentation with minimal computational cost. This modular design ensures efficiency while enhancing the discriminative power of the model for complex farmland damage segmentation tasks.

AgriEngineering 2025, 7, 388 5 of 20


> **Figure 2. Overall architecture of the proposed AgriFusion network.**

2.2.1. Encoder

AgriFusion employs an asymmetric dual-encoder that processes RGB and NIR inputs in parallel and produces multi-scale features for subsequent fusion and decoding. Let Xrgb ∈RH×W×3 and Xnir ∈RH×W×1. The RGB branch adopts a hierarchical MiT whose overlapped patch embedding and stagewise self-attention are effective at modeling long- range dependencies with competitive efficiency, which is important for large homogeneous regions and elongated structures in aerial scenes [29]. The NIR branch is a compact residual network that begins with a 7 × 7 convolution and a pooling layer followed by four residual stages. This choice reflects the fact that NIR is a single-channel modality with highly concentrated physiological signals [30]; assigning a lightweight CNN avoids over- allocating capacity while preserving strong local inductive biases [31,32]. The two encoders produce feature tuples

Rs}4

Ns}4





s=1 at strides {4, 8, 16, 32} with spatial sizes {Hs × Ws}. Prior to fusion we align channels with 1 × 1 projections and use bilinear resizing if minor stride mismatches occur:

s=1 and

∼ Rs,

∼ Ns ∈RHs×Ws×C′s (1)

∼ Rs = ϕs(Rs),

∼ Ns = ψs(Ns),

where ϕs(·) and ψs(·) denote modality-specific 1 × 1 convolutional projections used for channel alignment, {Hs, Ws} are the spatial dimensions at stage s, and C′

s is the unified channel width after projection. As shown in Equation (1), this operation ensures that both modalities are projected into a unified feature space with compatible resolutions and channel dimensions, preparing them for subsequent fusion.

Default widths follow MiT-B1 on the RGB branch and a reduced setting on the NIR branch, which allocates computation in proportion to modality bandwidth. The asymmetric design departs from early concatenation pipelines that stack RGB and NIR at the input and pass them through a single shared backbone. Such homogeneous processing has been

AgriEngineering 2025, 7, 388 6 of 20

shown to under-utilize modality-specific semantics and to blur the complementary roles of appearance and physiology in multi-spectral imagery [33]. By contrast, separate encoders enable tailored capacity and inductive biases for each modality while keeping their output scales compatible for fusion.

2.2.2. Attention Fusion Feature Module

The Attention-based Fusion Feature (AFF) module integrates RGB and NIR represen- tations at several resolutions while learning where local detail or global context should

∼ Ns and produce a fused output ˆFs. Different from AAFormer [34], which employs a squeeze-and-excitation at- tention mechanism [35] to optimize the decoder but often suffers from limited cross-modal interaction and an overemphasis on channel reweighting, our AFF module is explicitly designed to address heterogeneous fusion. As shown in Figure 3, it contains a local atten- tion branch, a global attention branch, and a gated modality mixer, enabling the model to simultaneously capture fine-grained spatial cues, long-range contextual dependencies, and adaptive modality weighting.

∼ Rs and

dominate. For each stage s ∈{2, 3, 4} we take the aligned features


> **Figure 3. Overall architecture of AFF module.**

∼ Ns ∈RHs×Ws×C′s, AFF module first initializes a shared representation through element-wise addition:

∼ Rs,

Formally, given modality-specific features

∼ Rs +

∼ Ns (2)

Xs =

∼ Rs and

∼ Ns denote the projected RGB and NIR features at stride s, and C′

where

s is the aligned channel dimension.

AgriEngineering 2025, 7, 388 7 of 20

The local attention branch applies two sequential 1 × 1 convolutions with batch normalization and ReLU activation to generate pixel-wise channel-sensitive responses, as formulated in Equation (3). This branch emphasizes spatially fine structures such as thin weed patches, irregular field boundaries, and planter skips [36].

Ls = BN2(Wl2δ(BN1(Wl1Xs))) (3)

where Wl1,Wl2 are learnable kernels, δ(·) is ReLU, and BN1, BN2 are batch normalization layers.

In parallel, the global attention branch aggregates context using global average pooling followed by two 1 × 1 convolutions with LayerNorm and ReLU activation, as expressed in Equation (4). The resulting descriptor reweights channels, improving robustness to illumination variability and class-level bias. This design is inspired by the success of squeeze-and-excitation (SE) attention in highlighting channel dependencies [35], and by subsequent evidence that global context enhances semantic segmentation in remote sensing imagery [37].



 

 

 

Gs = LN2

Wg1GAP(Xs)

Wg2δ

LN1

(4)

where GAP(·) denotes global average pooling, Wg1, Wg2 are convolution kernels, and LN1, LN2 are LayerNorm layers.

The outputs of the local and global branches are first aggregated and normalized through a sigmoid activation, which produces an adaptive fusion weight map:

Ws = σ(Ls + Gs) (5)

where Ws ∈[0, 1]Hs×Ws×C′s denotes the learned attention weights, σ(·) is the element-wise sigmoid function. Intuitively, Ws acts as a modality gate at every spatial location and channel. When Ws →1, the gate favors RGB features, which are typically more reliable for structural patterns such as row boundaries, tillage marks, and man-made objects [14]. When Ws →0, the gate emphasizes NIR features, which are more sensitive to vegetation vigor, stress, and other physiological signals [38,39]. For intermediate values, the model adaptively blends the two inputs, yielding a data-driven balance between geometric texture and spectral physiology. Building on this interpretation, the fused representation ˆFs is then computed as

∼ Ns (6)

ˆFs = 2Ws ⊙Rs + 2(1 −Ws) ⊙

where σ(·) denotes the element-wise sigmoid, ⊙indicates element-wise multiplication,

∼ Ns ∈RHs×Ws×C′s are the aligned RGB and NIR features at stride sss, and Ls ∈RHs×Ws×C′s, Gs ∈R1×1×C′s are the local and global attention responses, with Gs broadcast along the spatial dimensions before addition in Equation (5). The map Ws ∈[0, 1]Hs×Ws×C′s provides per-pixel, per-channel weights, and the factor 2 stabilizes gradient magnitudes so that both modalities retain sufficient contribution during optimization [40,41]. In practice, In practice, Equations (5) and (6) can be viewed as a gated residual blend between the two modality streams. RGB dominates where structural evidence is decisive, while NIR takes precedence in vegetation-sensitive regions. This balance allows the AFF module to perform robust fusion across heterogeneous agricultural patterns, consistent with recent multimodal fusion strategies in remote sensing and medical imaging [42,43].

∼ Rs,

In summary, the AFF module provides a compact yet powerful mechanism for modality-aware feature integration. By explicitly combining local spatial attention with global contextual reweighting, it enables the network to dynamically adjust the relative im- portance of RGB and NIR signals in a category- and region-specific manner. Unlike simple concatenation or channel recalibration approaches, AFF learns fine-grained gating maps that preserve boundary precision while simultaneously enhancing vegetation sensitivity.

AgriEngineering 2025, 7, 388 8 of 20

This design ensures that spectral and structural cues are not treated uniformly but rather fused adaptively according to scene content, thereby strengthening the model’s ability to detect heterogeneous agricultural anomalies. As demonstrated in later experiments, this fusion strategy consistently improves segmentation performance across both struc- tural and physiological categories, underscoring the central role of AFF in the AgriFusion architecture [44].

2.2.3. Decoder

The decoder aggregates fused features from multiple scales and produces dense predictions with minimal overhead. We do not adopt an FPN- or UPerNet-style feature pyramid. Instead, we use a progressive upsampling-and-concatenation strategy with a lightweight MLP projection to effectively integrate multi-scale representations from the dual encoders. For each stage s ∈{2, 3, 4} we first project ˆFs to a common embedding width E using a linear layer implemented as a 1 × 1 convolution:

 ∈RHs×Ws×E (7)

  ˆFs

∼ Fs = MLPE

where MLPE(·) denotes a 1 × 1 convolution (optionally followed by normalization and a nonlinearity, depending on implementation), Hs × Ws are the spatial dimensions at stride

∼ F4 to the stride-4 resolution H1 × W1, concatenate them along the channel axis, and compress the concatenated tensor back to width E with another 1 × 1 convolution:

∼ F2,

∼ F3,

s. We then upsample

 ∼





∈RH1×W1×E (8)

∥s∈(2,3,4) UP×( H1

Z = Γ

Fs

Hs , W1 Ws )

where Up×(·)(·) is bilinear interpolation to the stride-4 spatial size H1 × W1, ∥denotes channel-wise concatenation, and Γ(·) is a 1 × 1 convolution that re-compresses the con- catenated features back to width E. The stride-4 reference grid H1 × W1 corresponds to the highest-resolution encoder output used by the decoder. A final 1 × 1 classifier maps Z to class logits, which are bilinearly upsampled to the input size to obtain the segmentation:

logits = Wcls ∗Z ∈RH1×W1×K, ˆY = Softmax(UP·→H × W(logits)) (9)

where Wcls is a 1 × 1 convolution producing K channels, K is the number of semantic classes, Softmax is applied along the channel dimension, and UP·→H × W (·) resizes the logits to the input resolution H × W. This MLP-style head follows the observation that, given strong multi-scale encoder features, heavy deconvolutions and pyramid pooling are not necessary. Lightweight projections and simple upsampling suffice to achieve strong accuracy with low overhead, in line with prior designs such as SegFormer’s decoder. In contrast with classical decoder heads such as FPN [36] and ASPP [45] that provide strong context aggregation at higher computational cost, our decoder keeps floating-point operations and memory usage low while preserving multi-scale information provided by the encoders and AFF module.

2.3. Experiment 2.3.1. Implementation Details

All experiments were conducted on a workstation equipped with an NVIDIA RTX 2080Ti GPU (22 GB memory). To initialize the encoders, we adopted pre-trained weights to accelerate convergence: ResNet-18 was used for the NIR branch, and MiT-B1 was used for the RGB branch. During training, we set the batch size to 64 and trained the model for 100 epochs to ensure convergence. The optimizer was Adam with an initial learning rate of 0.001. For supervision, we employed a composite loss function that combines cross-entropy

AgriEngineering 2025, 7, 388 9 of 20

loss with a Dice loss term, following common practice in semantic segmentation [46], which helps balance class distribution and improves boundary delineation. Standard data augmentation techniques, including random flipping and rotation, were applied to improve generalization.

2.3.2. Evaluation Metrics

To comprehensively evaluate the performance of the proposed model, we adopt the mean Intersection over Union (mIoU) as the primary metric. mIoU is widely used in semantic segmentation as it measures the average overlap between the predicted regions and ground truth across all classes (Everingham et al., 2010) [47]. In addition to mIoU, we also report Pixel Accuracy (PA) and F1-score to provide a more comprehensive eval- uation. PA measures the proportion of correctly classified pixels across the entire image, reflecting the overall segmentation correctness, while the F1-score balances precision and recall for each class, offering deeper insights into class-level performance, especially for minority categories such as planter skips or storm damage. By jointly considering mIoU, PA, and F1-score, we ensure a robust and fair assessment of both global accuracy and per-class discriminability.

N ∑ i=1

TP TP + FP + FN (10)

mIoU = 1

N

Pixel Accuracy = TP + TN TP + TN + FP + FN (11)

F1 = 2 × Precision × Recall

Precision + Recall (12)

where N is the number of classes, and TP, FP, and FN denote the true positives, false positives, and false negatives for class i, respectively.


## 3. Result

3.1. Comprehensive Performance Comparison

To comprehensively evaluate the effectiveness of the proposed AgriFusion frame- work, we first compared AgriFusion against representative segmentation models from three architectural families: CNN-based methods (DeepLabV3 [48], DeepLabV3+ [49]), Transformer-based methods (SegFormer [14] with MiT-B1 and MiT-B3 backbones), and Hybrid methods (AAFormer [34]). The quantitative results are summarized in Table 1.


> **Table 1. Comparison of AgriFusion with CNN-, Transformer-, and Hybrid-Based Methods.**

Model Category mIoU/% PA/% F1 Score

SegFormer (MiT-B1) Transformer 40.60 76.73 55.14 SegFormer (MiT-B3) Transformer 44.88 79.27 59.21 DeepLabV3 CNN 35.50 73.40 50.18 DeepLabV3+ CNN 43.43 77.27 57.35 AAFormer Hybrid 45.46 78.65 60.19 AgriFusion (MiT_B1) Hybrid 49.31 81.72 67.85

Bold values indicate the highest performance in each column.

Overall, AgriFusion achieves the best performance across all evaluation metrics, with an mIoU of 49.31%, PA of 81.72%, and F1 score of 67.85%. Compared with SegFormer (MiT-B3), one of the strongest Transformer baselines, AgriFusion improves mIoU by +4.43% and F1 score by +8.64%. Against the Hybrid AAFormer, AgriFusion achieves +3.85% mIoU and +7.66% F1, indicating the superiority of the proposed dual-encoder fusion design.

AgriEngineering 2025, 7, 388 10 of 20

CNN-based approaches lag significantly behind, with DeepLabV3+ reaching 43.43% mIoU and 57.35% F1, highlighting their limited capacity to model complex agricultural scenes.

To further ensure the reliability of these results and verify that the observed improve- ments are not caused by random fluctuations, each experiment was repeated five times with different random seeds. Table 2 reports the mean and standard deviation of mIoU and F1 for each method, as well as the results of paired two-sided t-tests comparing each baseline with AgriFusion.


> **Table 2. Statistical analysis over 5 runs (mean ± std) and significance testing against AgriFusion.**

p-Value

p-Value

Model mIoU (%) mean ± std

F1 (%) mean ± std

(F1) Cohen’s d

(mIoU)

SegFormer

(MiT-B1) 40.60 ± 0.33 55.14 ± 0.41 6.56 × 10−11 7.38 × 10−12 28.46

SegFormer

(MiT-B3) 44.88 ± 0.35 59.21 ± 0.42 1.86 × 10−8 1.85 × 10−10 13.98

DeepLabV3 35.50 ± 0.40 50.18 ± 0.45 4.34 × 10−12 9.25 × 10−13 40.00 DeepLabV3+ 43.43 ± 0.30 57.35 ± 0.36 9.81 × 10−10 1.64 × 10−11 20.26 AAFormer 45.46 ± 0.31 60.19 ± 0.37 3.22 × 10−8 2.34 × 10−10 13.03 AgriFusion

(MiT-B1) 49.31 ± 0.28 67.85 ± 0.25 — — —

The standard deviation of each model is below 0.5%, indicating stable training dy- namics across different initializations. More importantly, the performance improvements of AgriFusion over all baselines are statistically significant (p < 0.001) for both mIoU and F1. The large effect sizes (Cohen’s d > 10) further confirm the practical significance of the improvements. These results demonstrate that AgriFusion consistently and significantly outperforms CNN-, Transformer-, and hybrid-based approaches, providing a more robust and reliable multimodal fusion strategy for agricultural semantic segmentation.

Class-wise comparisons are provided in Table 3. AgriFusion consistently outperforms baseline methods across most anomaly categories. For planter skip, AgriFusion achieves 55.36% IoU, which is nearly +10% higher than SegFormerB3 (45.35%) and substantially higher than AAFormer (41.35%). For waterway, AgriFusion obtains 41.46% IoU, signifi- cantly outperforming AAFormer (26.89%), demonstrating its strength in detecting narrow, irregular structures. Similarly, in water, AgriFusion achieves 75.05% IoU, improving over AAFormer (69.19%) and SegFormerB3 (62.08%). These results confirm that AgriFusion effectively integrates both spectral cues and multi-scale contextual information, enabling robust segmentation of both fine-grained and large-scale anomalies.


> **Table 3. Per-Class IoU Comparison Between AgriFusion and Baseline Models.**

Model mIoU/% BG DP DD ER ND PS WT WW WC

SegFormer (MiT-B1) 40.60 76.73 19.30 60.38 22.30 30.33 35.34 61.32 20.40 39.27 SegFormer (MiT-B3) 44.88 79.27 28.65 66.18 22.78 35.47 45.35 62.08 21.97 42.15 DeepLabV3 35.50 78.64 21.07 53.37 16.88 28.51 25.99 45.30 21.07 28.64 DeepLabV3+ 43.43 77.27 19.65 65.78 23.30 31.33 44.80 66.49 20.65 41.60 AAFormer 45.46 76.85 37.06 60.93 24.45 42.52 41.35 69.19 26.89 29.89 AgriFusion 49.31 78.39 27.40 68.92 26.15 39.69 55.36 75.05 41.46 31.41

Bold values indicate the highest performance in each column.

The qualitative comparisons in Figure 4 further corroborate these findings. CNN-based models (DeepLabV3/+) often miss subtle vegetation stress regions and fail to delineate boundaries in classes such as end row and planter skip. Transformer-based SegFormer pro- duces smoother predictions but struggles with fragmented small objects, while AAFormer

AgriEngineering 2025, 7, 388 11 of 20

partially alleviates this issue yet still produces noisy masks in challenging cases such as weed cluster. In contrast, AgriFusion generates predictions that are both spatially coherent and semantically precise, capturing fine row structures as well as large-area vegetation anomalies. These consistent improvements across metrics, categories, and qualitative outputs demonstrate the overall effectiveness of the proposed approach.


> **Figure 4. Qualitative comparison of segmentation results. White boxes highlight important local**

> details, and the colors represent different anomaly categories.

3.2. Comparison with Early, Late, and Advanced Fusion Strategies

To further verify the effectiveness of the proposed adaptive fusion mechanism, we additionally compared AgriFusion with three representative multimodal fusion strategies: Early Fusion, Late Fusion, and the advanced CMX framework [50]. In the Early Fusion configuration, RGB and NIR channels are concatenated along the channel dimension to form a 4-channel input, which is then fed directly into a single encoder–decoder network without any modality-specific processing. This represents the most straightforward multimodal strategy, relying on the backbone to implicitly learn cross-modal interactions from the input level. In contrast, the Late Fusion configuration employs two independent encoders for the RGB and NIR modalities, and the feature maps extracted from both streams are concatenated at the final encoding stage before being passed to the decoder. No adaptive

AgriEngineering 2025, 7, 388 12 of 20

weighting or attention is applied during the fusion, making this setting equivalent to the “W/O AFF” variant used in the ablation study. Finally, CMX serves as a strong representative of state-of-the-art multimodal fusion approaches. Originally designed for RGB–Depth/Thermal tasks, CMX employs cross-modal interaction modules to enhance representation learning. Given that NIR provides dense spectral information similar to Depth and Thermal, CMX offers a competitive and relevant baseline for our task.


> **Table 4 presents the comparison results. Early Fusion and Late Fusion yield only**

> modest improvements compared with single-modality baselines, confirming that simple
concatenation strategies are insufficient to fully exploit multimodal complementarity. Late
Fusion performs slightly better than Early Fusion due to its ability to preserve modality-
specific representations through separate encoders, but it still lacks explicit interaction
mechanisms. CMX achieves stronger results through its dedicated cross-modal fusion
modules, while AgriFusion further improves mIoU by 5.19% over Early Fusion, 4.43%
over Late Fusion, and 0.75% over CMX, demonstrating the effectiveness of the proposed
adaptive fusion strategy.


> **Table 4. Comparison with early, late, and advanced fusion strategies.**

Model Fusion Strategy mIoU/% PA/% F1 Score

Early Fusion Input concatenation 44.12 76.05 58.62

Late Fusion Feature concatenation

(W/O AFF) 44.88 79.27 59.57

CMX SOTA multimodal fusion 48.56 81.10 65.72 AgriFusion Adaptive Fusion Module 49.31 81.72 67.85

Bold values indicate the highest performance in each column.

3.3. Ablation Study

The results of the first ablation study (Table 5) provide strong evidence for the neces- sity of heterogeneous spectral fusion. The unimodal baselines, RGB-only and NIR-only, achieved 40.60% mIoU, 76.73% PA, and 55.13% F1 and 37.64% mIoU, 73.20% PA, and 50.14% F1, respectively. These results indicate that, while RGB imagery provides rich structural and textural information, it lacks sensitivity to vegetation vigor and physiological stress. Conversely, the NIR modality excels at capturing crop health indicators but suffers from reduced discriminative power in the absence of structural context.


> **Table 5. Ablation study of AgriFusion on spectral fusion and multi-scale feature balance.**

Experimental

Setting Model Configuration mIoU/% PA/% F1 Score

1st Ablation RGB-only 40.60 76.73 55.13 NIR-only 37.64 73.20 50.14 W/O AFF module 44.88 79.27 59.57

2nd Ablation Local-only 46.12 79.35 65.32 Global-only 46.58 80.04 65.41

- AgriFusion (Full) 49.31 81.72 67.85

Bold values indicate the highest performance in each column.

When the attention-based fusion module was removed (W/O AFF), performance reached 44.88% mIoU, 79.27% PA, and 59.57% F1, which, although better than unimodal inputs, still lags behind the full model. In contrast, the complete AgriFusion (Full) model that integrates the asymmetric dual-encoder with attention-based feature fusion achieved 49.31% mIoU, 81.72% PA, and 67.85% F1. Relative to the baselines, AgriFusion improves

AgriEngineering 2025, 7, 388 13 of 20

over RGB-only by +8.71 mIoU, +4.99 PA, and +12.72 F1; over NIR-only by +11.67 mIoU, +8.52 PA, and +17.71 F1; and over W/O AFF by +4.43 mIoU, +2.45 PA, and +8.28 F1. These

gains across all metrics strongly support our first claim that modality-aware attention fusion is indispensable for leveraging the complementary properties of RGB and NIR imagery in agricultural semantic segmentation.

The second ablation study further highlights the importance of balancing local detail preservation with global contextual modeling. The Local-only configuration, where only the local attention branch of AFF is activated, achieved 46.12% mIoU, 79.35% PA, and 65.32% F1. This setting favors fine structures such as weed clusters and boundaries but lacks long-range contextual reasoning. The Global-only configuration, where the local branch is removed and only the global attention branch is retained, yielded 46.58% mIoU, 80.04% PA, and 65.41% F1. This variant provides stronger scene-level coherence by aggregating global context and channel importance, yet it is less effective at capturing small or irregular targets that require fine spatial sensitivity.

The complete AgriFusion (Full) model attained 49.31% mIoU, 81.72% PA, and 67.85% F1, outperforming Local-only by +3.19 mIoU, +2.37 PA, and +2.53 F1; and Global-only by +2.73 mIoU, +1.68 PA, and +2.44 F1. These consistent improvements confirm that joint local

and global feature aggregation provides a more balanced representation, simultaneously enhancing the segmentation of small objects and maintaining large-scale consistency. In addition, the decoder design ensures these gains are achieved without unnecessary archi- tectural complexity. This evidence reinforces our second claim that adaptive multi-scale fusion combined with efficient decoding is a critical mechanism for advancing agricultural semantic segmentation.


## 4. Discussion

4.1. Spectral–Spatial Fusion and Modality Complementarity

The ablation study, detailed in Table 5, highlights the critical role of heterogeneous spectral fusion in agricultural semantic segmentation. To further analyze modality con- tributions, Table 6 presents the per-class IoU comparison across different variants. The RGB-only baseline achieves a mIoU of 40.60%. It shows relative strength in categories where geometric texture and row alignment are prominent, such as Dry Down (60.33%), Planter Skip (48.21%), and Waterway (60.25%). Performance is notably weaker for targets defined by vegetation stress or small irregularities, including Nutrient Deficiency (30.12%) and Weed Cluster (16.85%). These observations are consistent with prior studies [51], indicating that RGB imagery captures geometric detail well but is less sensitive to subtle physiological stress signals.


> **Table 6. Per-Class IoU Comparison Between AgriFusion and Its Variants (RGB-only, NIR-only, and**

> W/O AFF).

Model mIoU/% BG DP DD ER ND PS WT WW WC

RGB-only 40.60 75.12 20.45 60.33 28.95 30.12 48.21 60.25 16.85 25.12 NIR-only 37.64 77.45 18.01 58.97 19.30 28.99 41.54 61.64 13.32 19.52 W/O AFF module 44.88 76.83 25.64 64.72 22.14 36.75 42.10 72.16 31.87 31.71 AgriFusion (Full) 49.31 78.39 27.40 68.92 26.15 39.69 55.36 75.05 41.46 31.41

Bold values indicate the highest performance in each column.

By contrast, the NIR-only variant shows a decline in overall performance, achieving an mIoU of 37.64%. This model struggles with structure-dependent anomalies, with scores for Planter Skip (41.54%) and End Row (19.30%) falling below the RGB-only baseline.

AgriEngineering 2025, 7, 388 14 of 20

This indicates that the NIR signal alone cannot provide sufficient geometric context for all segmentation tasks.

The model without the attention fusion (W/O AFF) module, which relies on a more basic spectral combination, achieves an mIoU of 44.88%. This result is a significant improve- ment over both single-modality baselines, demonstrating that even a simple fusion strategy is highly beneficial. For instance, the IoU for Weed Cluster improves to 31.87%, substantially outperforming both the RGB-only (16.85%) and NIR-only (13.32%) models. This confirms that integrating heterogeneous spectral data is a crucial step toward robust performance.

AgriFusion (Full) achieves the highest accuracy (49.31% mIoU), consistently outper- forming unimodal baselines across nearly all categories. The most notable gains appear in categories requiring both structural and spectral cues, such as weed cluster (41.46%, compared to 16.85% in RGB-only and 31.87% in NIR-only) and planter skip (55.36%). These results, further corroborated by the qualitative comparisons in Figure 5, validate that the attention-based fusion mechanism can dynamically exploit modality complementarity, en- hancing both local detail and physiological sensitivity [52]. Together, these findings strongly support the hypothesis that effective spectral fusion is essential for robust agricultural anomaly detection.


> **Figure 5. Qualitative Segmentation Results of AgriFusion and Its Variants (RGB-only, NIR-only, and**

> W/O AFF). Colors represent different anomaly categories.

Qualitative comparisons (Figure 5) further confirm this conclusion. While RGB-only predictions preserve field boundaries but fail to detect stressed vegetation, and NIR-only predictions highlight stressed regions but neglect structural alignment, the AgriFusion outputs exhibit both geometric consistency and physiological sensitivity. Taken together, these results affirm that attention-guided spectral fusion provides a synergistic, rather than additive, benefit, validating our first scientific claim: effective integration of RGB and NIR modalities is essential for robust agricultural anomaly detection.

AgriEngineering 2025, 7, 388 15 of 20

4.2. Multi-Scale Representation and Feature Balance

The ablation study on multi-scale feature processing, summarized in Table 5, demon- strates that accurate segmentation of agricultural anomalies requires a careful balance between local detail preservation and global contextual understanding. To more clearly isolate the contributions of local and global representations, Table 7 reports the per-class IoU comparison between the Local-only and Global-only variants. The Local-only configuration achieved an mIoU of 46.12 percent, with relatively strong performance in categories where fine-grained boundary information is critical. For example, the model performed well on weed cluster with 35.14 percent and waterway with 29.65 percent, both of which involve small and irregular structures that benefit from high-resolution spatial detail. However, per- formance was less satisfactory on large-scale conditions such as dry down at 66.04 percent and nutrient deficiency at 37.10 percent. This indicates that an exclusive reliance on local filters cannot fully capture long-range dependencies, a limitation consistent with prior stud- ies [53] showing that convolutional networks without explicit global aggregation struggle in large and heterogeneous scenes.


> **Table 7.**

> Per-Class IoU Comparison Between AgriFusion and Its Variants (Local-only and
Global-only).

Model mIoU/% BG DP DD ER ND PS WT WW WC

Local-only 46.12 75.37 25.12 66.04 24.86 37.10 51.22 70.58 35.14 29.65 Global-only 46.58 76.30 26.82 63.29 25.10 38.56 52.64 71.38 36.41 28.72 AgriFusion 49.31 78.39 27.40 68.92 26.15 39.69 55.36 75.05 41.46 31.41

Bold values indicate the highest performance in each column.

The Global-only configuration slightly improved the overall mean IoU to 46.58 percent, providing better results in spatially coherent anomalies. For example, dry down improved to 63.29 percent and nutrient deficiency to 38.56 percent, highlighting the advantage of long-range dependencies in modeling extensive field-level conditions. At the same time, performance declined for classes requiring fine spatial resolution, such as weed cluster at 36.41 percent and waterway at 28.72 percent. These results support findings from transformer-based segmentation methods that global attention enhances scene-level reasoning but risks losing sharpness at class boundaries when not combined with localized feature representations [9].

The complete AgriFusion delivered the best performance with a mean IoU of 49.31 percent, surpassing all ablated variants across nearly every category. It achieved notable improvements in weed cluster with 41.46 percent and nutrient deficiency with 39.69 percent, while also achieving higher accuracy in large-scale categories such as dry down with 68.92 percent. These results, supported by qualitative examples in Figure 6, demonstrate that AgriFusion effectively integrates both local and global attention path- ways within a lightweight decoder. The outcome is a representation that preserves fine structural boundaries while maintaining holistic contextual consistency. This design prin- ciple resonates with the rationale behind feature pyramid networks and atrous spatial pyramid pooling, yet the proposed model achieves a more adaptive balance by explicitly learning to combine complementary receptive fields [54,55]. Collectively, the evidence substantiates our second claim: balanced multi-scale representation is indispensable for robust segmentation of diverse agricultural anomalies.

AgriEngineering 2025, 7, 388 16 of 20


> **Figure 6. Qualitative Segmentation Results of AgriFusion and Its Variants (Local-only and**

Global-only).

4.3. Limitations and Future Work

Although AgriFusion demonstrates promising results, several limitations remain. First, the current design only fuses RGB and NIR imagery; while effective, other modalities such as hyperspectral [56], thermal [57], or LiDAR [58] can capture biochemical and structural attributes beyond RGB–NIR, yet integrating such heterogeneous sources poses challenges in alignment and adaptive weighting. Second, the framework is primarily data-driven, and agricultural monitoring could benefit from embedding external knowledge such as crop growth models, soil properties, and weather dynamics, in line with recent calls for physics- or theory-guided machine learning [59]. Third, the current dataset only covers farmland in the United States, which may limit the model’s generalizability to other regions with different crop types, planting structures, and environmental conditions [60]. Domain shifts across regions, for example, when applying the model to farmlands in China, may lead to performance degradation. This highlights the need for multi-regional data and domain adaptation strategies in future work. Focusing on modality extension and knowledge integration will further enhance the robustness and scientific impact of AgriFusion and accelerate its deployment in sustainable agriculture.

In addition, since the Agriculture-Vision dataset is derived from airborne imagery, the proposed AgriFusion framework is inherently suitable for UAV-based agricultural monitoring. Although the network is not explicitly designed as a lightweight model, its relatively efficient architecture and reliance on only two spectral modalities (RGB and NIR) reduce sensor payload requirements and facilitate deployment on UAV platforms equipped with multispectral cameras. This aligns with recent advances demonstrating the feasibility of deep-learning inference on UAVs and the integration of multi-modal sensing in precision agriculture [61–63]. Future work will focus on validating the model’s performance in UAV-based operational scenarios and exploring strategies to integrate additional sensor modalities such as hyperspectral, thermal, or LiDAR imagery to improve adaptability under diverse field conditions.

AgriEngineering 2025, 7, 388 17 of 20


## 5. Conclusions

This study introduced AgriFusion, a novel semantic segmentation framework de- signed to address two key challenges in agricultural remote sensing: effective spectral– spatial fusion and balanced multi-scale representation of complex field structures. By employing an asymmetric dual-encoder architecture that separately processes RGB and NIR imagery, coupled with an attention-based fusion mechanism and a MLP-based decoder, the model effectively integrates complementary spectral feature while maintaining a robust balance between local detail and global context.

Extensive experiments on the Agriculture-Vision public benchmark, including five repeated runs with different random seeds, confirmed the advantages of the proposed approach and demonstrated the stability and statistical significance of the improvements. Compared with unimodal baselines, AgriFusion significantly improved segmentation accuracy in categories requiring both structural patterns and physiological signals, such as planter skips and waterway, thereby validating the necessity of modality-aware spectral fusion. Furthermore, comparative studies with early, late, and advanced fusion strategies (e.g., CMX) further verified the effectiveness of the proposed adaptive fusion mechanism. Ablation studies also demonstrated that neither local nor global representations alone were sufficient to capture the heterogeneity of agricultural anomalies. Instead, the joint modeling of fine-scale details and long-range dependencies produced the highest overall performance, substantiating the importance of multi-scale feature balance.

Beyond quantitative gains, qualitative analysis highlighted that AgriFusion generates segmentation maps that are both structurally coherent and sensitive to vegetation stress signals. These improvements directly address practical needs in precision agriculture, where early detection of anomalies such as nutrient deficiency, water stress, and weed invasion can support timely intervention and enhance crop management strategies.

In summary, AgriFusion provides a principled solution to two long-standing scientific challenges in agricultural semantic segmentation. By advancing both spectral fusion and multi-scale modeling, the framework establishes a foundation for more accurate and reliable monitoring of crop conditions using remote sensing imagery. While several limitations remain, including the need for validation on diverse datasets, integration of additional sensing modalities, and further efficiency optimization, the findings presented here demonstrate the potential of fusion-based models to contribute meaningfully to sustainable agriculture.

Author Contributions: X.L.: Data curation, Methodology, Formal analysis, Investigation, Visualiza- tion, Writing—original draft, and Writing—review & editing. L.Q.: Conceptualization, Methodology, Supervision, and Writing—review & editing. C.Y.: Conceptualization, Methodology, Supervision, Funding acquisition, and Writing—review & editing. All authors have read and agreed to the published version of the manuscript.

Funding: This research received no external funding.

Data Availability Statement: The data that support the findings of this study are available from the corresponding author upon reasonable request.

Acknowledgments: The authors acknowledge the Minnesota Supercomputing Institute (MSI) at the University of Minnesota for providing resources that contributed to the research results reported within this paper. URL: http://www.msi.umn.edu (accessed on 6 October 2025).

Conflicts of Interest: The authors declare that they have no known competing financial interest or personal relationships that could have appeared to influence the work reported in this study.

AgriEngineering 2025, 7, 388 18 of 20


## References

1. Wang, J.; Zhang, S.; Lizaga, I.; Zhang, Y.; Ge, X.; Zhang, Z.; Zhang, W.; Huang, Q.; Hu, Z. UAS-based remote sensing for agricultural Monitoring: Current status and perspectives. Comput. Electron. Agric. 2024, 227, 109501. [CrossRef] 2. Paul, N.; Sunil, G.; Horvath, D.; Sun, X. Deep learning for plant stress detection: A comprehensive review of technologies, challenges, and future directions. Comput. Electron. Agric. 2025, 229, 109734. [CrossRef] 3. Chen, Y.; Fang, P.; Zhong, X.; Yu, J.; Zhang, X.; Li, T. Hi-ResNet: Edge detail enhancement for high-resolution remote sensing segmentation. IEEE J. Sel. Top. Appl. Earth Obs. Remote Sens. 2024, 17, 15024–15040. [CrossRef] 4. Gonthina, N.; Narasimha Prasad, L. An enhanced convolutional neural network architecture for semantic segmentation in high-resolution remote sensing images. Discov. Comput. 2025, 28, 91. [CrossRef] 5. Wang, Y.; Yang, L.; Liu, X.; Yan, P. An improved semantic segmentation algorithm for high-resolution remote sensing images based on DeepLabv3+. Sci. Rep. 2024, 14, 9716. [CrossRef] [PubMed] 6. Che, Z.; Shen, L.; Huo, L.; Hu, C.; Wang, Y.; Lu, Y.; Bi, F. MAFF-HRNet: Multi-attention feature fusion HRNet for building segmentation in remote sensing images. Remote Sens. 2023, 15, 1382. [CrossRef] 7. Guo, S.; Yang, Q.; Xiang, S.; Wang, P.; Wang, X. Dynamic high-resolution network for semantic segmentation in remote-sensing images. Remote Sens. 2023, 15, 2293. [CrossRef] 8. Li, X.; Li, X.; Zhang, M.; Dong, Q.; Zhang, G.; Wang, Z.; Wei, P. SugarcaneGAN: A novel dataset generating approach for sugarcane leaf diseases based on lightweight hybrid CNN-Transformer network. Comput. Electron. Agric. 2024, 219, 108762. [CrossRef] 9. Wang, L.; Li, R.; Zhang, C.; Fang, S.; Duan, C.; Meng, X.; Atkinson, P.M. UNetFormer: A UNet-like transformer for efficient semantic segmentation of remote sensing urban scene imagery. ISPRS J. Photogramm. Remote Sens. 2022, 190, 196–214. [CrossRef] 10. Liu, W.; Lin, Y.; Liu, W.; Yu, Y.; Li, J. An attention-based multiscale transformer network for remote sensing image change detection. ISPRS J. Photogramm. Remote Sens. 2023, 202, 599–609. [CrossRef] 11. Cao, H.; Wang, Y.; Chen, J.; Jiang, D.; Zhang, X.; Tian, Q.; Wang, M. segmentation. In European Conference on Computer Vision; Springer Nature: Cham, Switzerland, 2022; pp. 205–218. 12. Xiao, T.; Liu, Y.; Zhou, B.; Jiang, Y.; Sun, J. Unified perceptual parsing for scene understanding. In Proceedings of the European Conference on Computer Vision (ECCV), Munich, Germany, 8–14 September 2018; pp. 418–434. 13. Wang, Z.; Li, J.; Tan, Z.; Liu, X.; Li, M. Swin-upernet: A semantic segmentation model for mangroves and spartina alterniflora loisel based on upernet. Electronics 2023, 12, 1111. [CrossRef] 14. Xie, E.; Wang, W.; Yu, Z.; Anandkumar, A.; Alvarez, J.M.; Luo, P. SegFormer: Simple and efficient design for semantic segmentation with transformers. Adv. Neural Inf. Process. Syst. 2021, 34, 12077–12090. 15. Fan, J.; Shi, Z.; Ren, Z.; Zhou, Y.; Ji, M. DDPM-SegFormer: Highly refined feature land use and land cover segmentation with a fused denoising diffusion probabilistic model and transformer. Int. J. Appl. Earth Obs. Geoinf. 2024, 133, 104093. [CrossRef] 16. Niu, B.; Feng, Q.; Chen, B.; Ou, C.; Liu, Y.; Yang, J. HSI-TransUNet: A transformer based semantic segmentation model for crop mapping from UAV hyperspectral imagery. Comput. Electron. Agric. 2022, 201, 107297. [CrossRef] 17. Aleissaee, A.A.; Kumar, A.; Anwer, R.M.; Khan, S.; Cholakkal, H.; Xia, G.-S.; Khan, F.S. Transformers in remote sensing: A survey. Remote Sens. 2023, 15, 1860. [CrossRef] 18. Cheng, X.; Li, B.; Deng, Y.; Tang, J.; Shi, Y.; Zhao, J. Mmdl-net: Multi-band multi-label remote sensing image classification model. Appl. Sci. 2024, 14, 2226. [CrossRef] 19. Zhao, R.; Zhang, C.; Xue, D. A multi-scale multi-channel CNN introducing a channel-spatial attention mechanism hyperspectral remote sensing image classification method. Eur. J. Remote Sens. 2024, 57, 2353290. [CrossRef] 20. Cunha, N.; Barros, T.; Reis, M.; Marta, T.; Premebida, C.; Nunes, U.J. Multispectral image segmentation in agriculture: A comprehensive study on fusion approaches. In Iberian Robotics Conference; Springer Nature: Cham, Switzerland, 2023; pp. 311–323. 21. Fan, X.; Ge, C.; Yang, X.; Wang, W. Cross-modal feature fusion for field weed mapping using RGB and near-infrared imagery. Agriculture 2024, 14, 2331. [CrossRef] 22. Liu, C.; Feng, Q.; Sun, Y.; Li, Y.; Ru, M.; Xu, L. YOLACTFusion: An instance segmentation method for RGB-NIR multimodal image fusion based on an attention mechanism. Comput. Electron. Agric. 2023, 213, 108186. [CrossRef] 23. Zheng, Z.; Yuan, J.; Yao, W.; Kwan, P.; Yao, H.; Liu, Q.; Guo, L. Fusion of uav-acquired visible images and multispectral data by applying machine-learning methods in crop classification. Agronomy 2024, 14, 2670. [CrossRef] 24. Zhao, L.; Zhang, J.; Yang, H.; Xiao, C.; Wei, Y. A Multi-Branch Deep Learning Network for Crop Classification Based on GF-2 Remote Sensing. Remote Sens. 2025, 17, 2852. [CrossRef] 25. Li, Y.; Li, T.; Zhao, Y.; Jiang, K.; Ye, Y.; Wang, S.; Zhou, Z.; Wei, Q.; Zhu, R.; Chen, Q.; et al. Multimodal fusion of UAV-based computer vision and plant water content dynamics for high-throughput soybean maturity classification. Crop Environ. 2025. [CrossRef] 26. Hruška, A.; Hamouz, P.; Lev, J.; Pavlíˇcek, J.; Kroulík, M.; Hamouzová, K.; Košnarová, P.; Holec, J.; Kouˇrím, P. Weed detection in cabbage fields using RGB and NIR images. Smart Agric. Technol. 2025, 12, 101232. [CrossRef]

AgriEngineering 2025, 7, 388 19 of 20

27. Chiu, M.T.; Xu, X.; Wei, Y.; Huang, Z.; Schwing, A.G.; Brunner, R.; Khachatrian, H.; Karapetyan, H.; Dozier, I.; Rose, G.; et al. Agriculture-vision: A large aerial image database for agricultural pattern analysis. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, Seattle, WA, USA, 14–19 June 2020; pp. 2828–2838. 28. Berger, K.; Machwitz, M.; Kycko, M.; Kefauver, S.C.; Van Wittenberghe, S.; Gerhards, M.; Verrelst, J.; Atzberger, C.; Van der Tol, C.; Damm, A.; et al. Multi-sensor spectral synergies for crop stress detection and monitoring in the optical domain: A review. Remote Sens. Environ. 2022, 280, 113198. [CrossRef] 29. Vaswani, A.; Shazeer, N.; Parmar, N.; Uszkoreit, J.; Jones, L.; Gomez, A.N.; Kaiser, Ł.; Polosukhin, I. Attention is all you need. Adv. Neural Inf. Process. Syst. 2017, 30, 5998–6008. 30. Chen, H.-Y.; Sang, I.-C.; Norris, W.R.; Soylemezoglu, A.; Nottage, D. Terrain classification method using an NIR or RGB camera with a CNN-based fusion of vision and a reduced-order proprioception model. Comput. Electron. Agric. 2024, 227, 109539. [CrossRef] 31. He, K.; Zhang, X.; Ren, S.; Sun, J. Deep Residual Learning for Image Recognition. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), Las Vegas, NV, USA, 27–30 June 2016. 32. Khan, U.; Khan, M.K.; Latif, M.A.; Naveed, M.; Alam, M.M.; Khan, S.A.; Su’ud, M.M. A Systematic Literature Review of Machine Learning and Deep Learning Approaches for Spectral Image Classification in Agricultural Applications Using Aerial Photography. Comput. Mater. Contin. 2024, 78, 2967. [CrossRef] 33. Zhao, F.; Zhang, C.; Geng, B. Deep multimodal data fusion. ACM Comput. Surv. 2024, 56, 1–36. [CrossRef] 34. Shen, Y.; Wang, L.; Jin, Y. AAFormer: A multi-modal transformer network for aerial agricultural images. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, New Orleans, LA, USA, 18–24 June 2022; pp. 1705–1711. 35. Hu, J.; Shen, L.; Sun, G. Squeeze-and-excitation networks. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, Salt Lake City, UT, USA, 18–22 June 2018; pp. 7132–7141. 36. Long, J.; Shelhamer, E.; Darrell, T. Fully convolutional networks for semantic segmentation. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, Boston, MA, USA, 7–12 June 2015; pp. 3431–3440. 37. Zhang, J.; Lin, S.; Ding, L.; Bruzzone, L. Multi-scale context aggregation for semantic segmentation of remote sensing images. Remote Sens. 2020, 12, 701. [CrossRef] 38. Li, K.; Qiang, Z.; Lin, H.; Wang, X. A Multi-Branch Attention Fusion Method for Semantic Segmentation of Remote Sensing Images. Remote Sens. 2025, 17, 1898. [CrossRef] 39. Li, X.; Li, X.; Zhang, S.; Zhang, G.; Zhang, M.; Shang, H. SLViT: Shuffle-convolution-based lightweight Vision transformer for effective diagnosis of sugarcane leaf diseases. J. King Saud Univ.-Comput. Inf. Sci. 2023, 35, 101401. [CrossRef] 40. Howard, A.G.; Zhu, M.; Chen, B.; Kalenichenko, D.; Wang, W.; Weyand, T.; Andreetto, M.; Adam, H. MobileNets: Efficient Convolutional Neural Networks for Mobile Vision Applications. arXiv 2017, arXiv:1704.04861. [CrossRef] 41. Woo, S.; Park, J.; Lee, J.-Y.; Kweon, I.S. Cbam: Convolutional block attention module. In Proceedings of the European Conference on Computer Vision (ECCV), Munich, Germany, 8–14 September 2018; pp. 3–19. 42. Cai, Z.; Fang, H.; Jiang, F.; Yang, J.; Ji, T.; Hu, Y.; Wang, X. AMFFNet: Asymmetric Multi-Scale Feature Fusion Network of RGB-NIR for Solid Waste Detection. IEEE Trans. Instrum. Meas. 2023, 72, 2522610. [CrossRef] 43. Hong, D.; Han, Z.; Yao, J.; Gao, L.; Zhang, B.; Plaza, A.; Chanussot, J. SpectralFormer: Rethinking hyperspectral image classification with transformers. IEEE Trans. Geosci. Remote Sens. 2021, 60, 5518615. [CrossRef] 44. Dai, Y.; Gieseke, F.; Oehmcke, S.; Wu, Y.; Barnard, K. Attentional feature fusion. In Proceedings of the IEEE/CVF Winter Conference on Applications of Computer Vision, Virtual, 5–9 January 2021; pp. 3560–3569. 45. Chen, L.-C.; Papandreou, G.; Kokkinos, I.; Murphy, K.; Yuille, A.L. Deeplab: Semantic image segmentation with deep convolu- tional nets, atrous convolution, and fully connected crfs. IEEE Trans. Pattern Anal. Mach. Intell. 2017, 40, 834–848. [CrossRef] [PubMed] 46. Milletari, F.; Navab, N.; Ahmadi, S.-A. V-net: Fully convolutional neural networks for volumetric medical image segmentation. In Proceedings of the 2016 Fourth International Conference on 3D Vision (3DV), Stanford, CA, USA, 25–28 October 2016; pp. 565–571. 47. Everingham, M.; Van Gool, L.; Williams, C.K.; Winn, J.; Zisserman, A. The pascal visual object classes (voc) challenge. Int. J. Comput. Vis. 2010, 88, 303–338. [CrossRef] 48. Chen, L.-C.; Papandreou, G.; Schroff, F.; Adam, H. Rethinking atrous convolution for semantic image segmentation. arXiv 2017, arXiv:1706.05587. [CrossRef] 49. Chen, L.-C.; Zhu, Y.; Papandreou, G.; Schroff, F.; Adam, H. Encoder-decoder with atrous separable convolution for semantic image segmentation. In Proceedings of the European Conference on Computer Vision (ECCV), Munich, Germany, 8–14 September 2018; pp. 801–818. 50. Zhang, J.; Liu, H.; Yang, K.; Hu, X.; Liu, R.; Stiefelhagen, R. CMX: Cross-modal fusion for RGB-X semantic segmentation with transformers. IEEE Trans. Intell. Transp. Syst. 2023, 24, 14679–14694. [CrossRef] 51. Kior, A.; Yudina, L.; Zolin, Y.; Sukhov, V.; Sukhova, E. RGB imaging as a tool for remote sensing of characteristics of terrestrial plants: A review. Plants 2024, 13, 1262. [CrossRef]

AgriEngineering 2025, 7, 388 20 of 20

52. Li, H.; Wu, X.-J. CrossFuse: A novel cross attention mechanism based infrared and visible image fusion approach. Inf. Fusion 2024, 103, 102147. [CrossRef] 53. Zhang, Y.; Liu, H.; Hu, Q. Transfuse: Fusing transformers and cnns for medical image segmentation. In Proceedings of the International Conference on Medical Image Computing and Computer-Assisted Intervention, Strasbourg, France, 27 September–1 October 2021; pp. 14–24. 54. Deng, Y.; Cao, Y.; Chen, S.; Cheng, X. Residual Attention Network with Atrous Spatial Pyramid Pooling for Soil Element Estimation in LUCAS Hyperspectral Data. Appl. Sci. 2025, 15, 7457. [CrossRef] 55. Lei, J.; Shu, C.; Xu, Q.; Yu, Y.; Yang, S. FCPFNet: Feature complementation network with pyramid fusion for semantic segmentation. Neural Process. Lett. 2024, 56, 60. [CrossRef] 56. Lu, B.; Dao, P.D.; Liu, J.; He, Y.; Shang, J. Recent advances of hyperspectral imaging technology and applications in agriculture. Remote Sens. 2020, 12, 2659. [CrossRef] 57. Wooster, M.J.; Roberts, G.; Smith, A.M.; Johnston, J.; Freeborn, P.; Amici, S.; Hudak, A.T. Thermal remote sensing of active vegetation fires and biomass burning events. In Thermal Infrared Remote Sensing: Sensors, Methods, Applications; Springer: Dordrecht, The Netherlands, 2013; pp. 347–390. 58. Goodwin, N.R.; Coops, N.C.; Culvenor, D.S. Assessment of forest structure with airborne LiDAR and the effects of platform altitude. Remote Sens. Environ. 2006, 103, 140–152. [CrossRef] 59. Reichstein, M.; Camps-Valls, G.; Stevens, B.; Jung, M.; Denzler, J.; Carvalhais, N.; Prabhat, F. Deep learning and process understanding for data-driven Earth system science. Nature 2019, 566, 195–204. [CrossRef] [PubMed] 60. Csurka, G. Domain adaptation for visual applications: A comprehensive survey. arXiv 2017, arXiv:1702.05374. [CrossRef] 61. Liu, J.; Wang, F.; Argaman, E.; Zhao, Z.; Shi, P.; Shi, S.; Han, J.; Ge, W.; Chen, H. Application of UAV Multimodal Data and Deep Learning for Estimating Soil Salt Content at the Small Catchment Scale. Int. Soil Water Conserv. Res. 2025. [CrossRef] 62. Pengpeng, Y.; Teng, F.; Zhu, W.; Shen, C.; Chen, Z.; Song, J. Cloud–edge–device collaborative computing in smart agriculture: Architectures, applications, and future perspectives. Front. Plant Sci. 2025, 16, 1668545. 63. Zhang, S.; Wang, X.; Lin, H.; Qiang, Z. A Review of the Application of UAV Multispectral Remote Sensing Technology in Precision Agriculture. Smart Agric. Technol. 2025, 12, 101406. [CrossRef]

Disclaimer/Publisher’s Note: The statements, opinions and data contained in all publications are solely those of the individual author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to people or property resulting from any ideas, methods, instructions or products referred to in the content.
