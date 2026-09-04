---
workspace_id: SCI-000074
doi: 10.1109/icssit69151.2026.11656575
title: 'WeedFormer: Transformer-based Crop-Weed Segmentation for UAV Imagery'
authors:
- family_name: Krishna
  given_name: Boggarapu Vamsi
  orcid: null
- family_name: Roshan
  given_name: Mohammad
  orcid: null
- family_name: Babu
  given_name: E. Akhil
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:40.559685+00:00'
---

# WeedFormer: Transformer-based Crop-Weed Segmentation for UAV Imagery

Proceedings of the 7th International Conference on Smart Systems and Inventive Technology (ICSSIT-2026) IEEE Xplore Part Number: CFP26P17-ART; ISBN: 979-8-3315-8087-2

WeedFormer: Transformer-based Crop-Weed

Segmentation for UAV Imagery

2026 7th International Conference on Smart Systems and Inventive Technology (ICSSIT) | 979-8-3315-8087-2/26/$31.00 ©2026 IEEE | DOI: 10.1109/ICSSIT69151.2026.11656575

E. Akhil Babu  Department of Computer Science

Boggarapu Vamsi Krishna  Department of Computer Science

Mohammad Roshan  Department of Computer Science

and Engineering  Vignan’s Foundation for Science,

and Engineering  Vignan’s Foundation for Science,

and Engineering  Vignan’s Foundation for Science,

Technology and Research

Technology and Research

Technology and Research

Guntur, 522213 India  akhil.edara85@gmail.com

Guntur, 522213 India  vamsikrishnaboggarapu@gmail.com

Guntur, 522213 India  mohdroshan985@gmail.com

tures improve global context modeling, their application to  crop–weed segmentation remains relatively underexplored.


## Abstract— Accurate crop–weed segmentation from unmanned

aerial vehicle (UAV) imagery is essential for precision 
agriculture and site-specific weed management. How-ever, 
distinguishing weeds from crops remains challenging due to 
visual 
similarities, 
overlapping 
vegetation, 
complex 
field 
backgrounds, and varying illumination conditions. This paper 
presents WeedFormer, a transformer-based semantic segmentation 
framework for robust crop–weed discrimination in UAV imagery. 
The proposed architecture combines a SegFormer-B2 backbone 
with a Convolutional Block Attention Module (CBAM) and 
Atrous Spatial Pyramid Pooling (ASPP) to capture both global 
contextual information and fine-grained plant features. The 
transformer encoder models long-range spatial dependencies, 
while CBAM enhances discriminative feature representations and 
ASPP aggregates multi-scale contextual information. Experiments 
conducted on the WeedsGalore benchmark demonstrate that 
WeedFormer achieves 80.27% mean Intersection-over-Union 
(mIoU) and 98.81% pixel accuracy, outperforming DeepLabv3+, 
SegFormer-B1, SegFormer-B2, and previously reported multi-
spectral baselines. The proposed framework effectively segments 
small, densely clustered, and visually ambiguous weed regions 
using only RGB imagery, demonstrating its potential for practical 
precision agriculture applications.

To address these limitations, this paper proposes Weed- Former, a transformer-based semantic segmentation framework  for UAV imagery. The proposed architecture integrates a  SegFormer-B2 encoder, CBAM attention refinement, and ASPP  multi-scale feature aggregation. Transformer self-attention  captures long-range spatial dependencies between crops, weeds,  and surrounding field structures, while CBAM emphasizes  discriminative vegetation features and suppresses background  noise. ASPP further enhances segmentation performance by  aggregating contextual information at multiple scales.

The remainder of the paper is organized as follows. Section  II reviews related work, Section III presents the proposed  methodology, Section IV discusses experimental results,  and Section V concludes the paper.

II. RELATED WORKS

Keywords - Precision Agriculture, Crop–Weed Segmentation,  Unmanned Aerial Vehicle (UAV), Semantic Segmentation, Vision  Transformer, SegFormer, Convolutional Block Attention Module  (CBAM), Atrous Spatial Pyramid Pooling (ASPP), RGB Imagery,  Deep Learning.

Recent advances in precision agriculture have increasingly  adopted deep learning-based semantic segmentation techniques to  improve crop and weed discrimination from UAV imagery.  Celikkan et al. [1] introduced the WeedsGalore dataset, a large- scale multispectral and multitemporal UAV benchmark for crop  and weed segmentation in maize fields. The dataset provides  challenging scenarios with varying illumination, dense vegetation,  and visually similar crop and weed classes, making it an important  benchmark for evaluating semantic segmentation algorithms.  Similarly, Weyler et al. [2] proposed the PhenoBench dataset,  which provides comprehensive benchmarks for semantic image  interpretation in agricultural environments and facilitates the  development of robust segmentation models.  Dataset development has also played a significant role in  advancing agricultural computer vision. Olsen et al. [3] presented  the DeepWeeds dataset containing multiple weed species for deep  learning-based classification, enabling robust weed recognition  under diverse environmental conditions. Although primarily  designed for classification rather than semantic segmentation, the  dataset established an important foundation for applying deep  learning techniques in weed management.  Several  encoder-decoder  architectures  have  demonstrated  remarkable performance in semantic segmentation tasks. Chen et  al. [4] proposed DeepLabv3+, which employs atrous separable

I. INTRODUCTION

Weed infestation during the early growth stages of maize  significantly reduces crop productivity by competing for  nutrients, water, and sunlight. Precision agriculture addresses  this challenge through targeted weed management; however,  accurate weed localization is required for effective site-specific  treatment. UAVs equipped with RGB cameras provide high- resolution imagery at low operational cost, making them a  practical solution for large-scale crop monitoring.

Despite recent advances in crop–weed segmentation, several  challenges remain. Crop seedlings and juvenile weeds often  exhibit similar visual characteristics, making discrimination  difficult. Furthermore, overlapping vegetation, heterogeneous  soil backgrounds, shadows, and severe class imbalance reduce  segmentation accuracy, particularly for small and densely  clustered weed regions. Existing CNN-based methods such  as DeepLabv3+ and UNet++ are effective for local feature  extraction but have limited capability to capture long-range  contextual relationships. Although transformer-based

architec-

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:37:45 UTC from IEEE Xplore.  Restrictions apply.

979-8-3315-8087-2/26/$31.00 ©2026 IEEE 546

Proceedings of the 7th International Conference on Smart Systems and Inventive Technology (ICSSIT-2026) IEEE Xplore Part Number: CFP26P17-ART; ISBN: 979-8-3315-8087-2

and multi-scale context aggregation within a unified framework.  Therefore, this work proposes WeedFormer, a transformer- based semantic segmentation framework that integrates  SegFormer-B2, CBAM, and Atrous Spatial Pyramid Pooling  (ASPP) to achieve robust crop–weed discrimination from RGB  UAV imagery, improving segmentation accuracy under  complex agricultural field conditions.

convolution and encoder-decoder refinement to improve object  boundary delineation and multi-scale feature extraction.  Likewise, Zhou et al. [5] introduced UNet++, a nested encoder- decoder architecture with dense skip connections that enhances  feature fusion and segmentation accuracy. Although originally  developed for medical image segmentation, UNet++ has been  successfully adapted to agricultural image analysis.

Deep learning has also been extensively applied to weed  detection using aerial imagery. Sa et al. [6] developed  WeedNet, which combines multispectral UAV imagery with  convolutional neural networks for dense semantic weed  classification in smart farming applications. Similarly, Milioto  et al. [7] proposed a fully convolutional network for real-time  crop  and  weed  segmentation  in  agricultural  robots,  demonstrating efficient semantic segmentation suitable for  autonomous field operations.

III. PROPOSED METHODOLOGY

WeedFormer is a transformer-based semantic segmentation  framework for UAV crop–weed mapping. As illustrated in  Fig. 1, the architecture consists of five stages: image  preprocessing, patch tokenization, SegFormer-B2 encoding,  CBAM attention refinement, ASPP multi-scale context  aggregation, and MLP decoding. The WeedsGalore dataset  contains six semantic classes: background, maize, Amaranth,  Barnyard Grass, Quickweed, and Weed Other.

Transformer-based vision models have recently emerged  as powerful alternatives to conventional CNN architectures.  Dosovitskiy et al. [8] introduced the Vision Transformer  (ViT), demonstrating that transformer architectures effectively  capture long-range spatial dependencies for image recognition  tasks. Building upon this concept, Xie et al. [9] proposed  SegFormer,  an  efficient  transformer-based  semantic  segmentation  framework  that  combines  hierarchical  transformer encoders with lightweight decoding, achieving  state-of-the-art segmentation performance while maintaining  computational efficiency.

A. Input Preprocessing and Patch Tokenization

×

Input images are resized to 512 512 pixels and normalized  to the range [0, 1]. Data augmentation, including random  flipping, color jittering, and random cropping, is applied during  training to improve generalization. Each image is divided  into overlapping patches and projected into token embeddings  represented as

T = t1, t2, . . . , tK  (1)

Hybrid architectures integrating CNNs and transformers  have further improved agricultural image analysis. Zhang et  al. [10] presented a hybrid CNN-Transformer framework for  weed  recognition  under  complex  field  conditions,  demonstrating  improved  robustness  against  varying  illumination and background clutter. To further enhance  feature representation, Woo et al. [11] introduced the  Convolutional Block Attention Module (CBAM), which  adaptively emphasizes informative spatial and channel  features, significantly improving feature discrimination in  convolutional networks. Zhao et al. [12] proposed the  Pyramid Scene Parsing Network (PSPNet), which utilizes  pyramid  pooling  to  aggregate  multi-scale  contextual  information and improve segmentation accuracy in complex  scenes.

where K denotes the number of image patches. These tokens  serve as input to the transformer encoder, enabling the model to  capture long-range contextual relationships across agricultural  scenes.

B. SegFormer-B2 Encoder

C. SegFormer-B2 Transformer Encoder

The SegFormer-B2 backbone serves as the feature  extraction module of WeedFormer. Unlike conventional CNNs,  the transformer encoder captures long-range spatial relation- ships through self-attention, enabling improved discrimination  between crops and weeds in complex agricultural scenes.  Input image patches are converted into token embeddings and  processed through hierarchical transformer stages to generate  multi-scale feature representations.

Large-scale  aerial  weed  mapping  has  also  been  investigated by Sa et al. [13], who proposed the WeedMap  framework using multispectral UAV imagery and deep neural  networks for precision herbicide application. Their work  demonstrated the effectiveness of semantic weed mapping for  site-specific weed management. Furthermore, Shahi et al. [14]  provided a comprehensive review of recent deep learning  techniques for agricultural image classification, highlighting  the increasing adoption of transformer-based models and  attention mechanisms in precision agriculture. Cheng et al.  [15] introduced the Masked-Attention Mask Transformer  (Mask2Former)  for  universal  image  segmentation,  demonstrating highly accurate segmentation across diverse  vision tasks through masked attention mechanisms.

Although these studies have significantly advanced crop  and weed segmentation, most existing approaches rely on  multispectral imagery, conventional CNN architectures, or  standard transformer models without effectively combining  global contextual learning, attention-based feature refinement,

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:37:45 UTC from IEEE Xplore.  Restrictions apply.

979-8-3315-8087-2/26/$31.00 ©2026 IEEE 547

Proceedings of the 7th International Conference on Smart Systems and Inventive Technology (ICSSIT-2026) IEEE Xplore Part Number: CFP26P17-ART; ISBN: 979-8-3315-8087-2

structures, crop rows, and surrounding vegetation, improving  segmentation performance in visually ambiguous regions.

D. CBAM Attention Enhancement

The deepest encoder features are refined using the CBAM  attention module [11], which sequentially applies channel and  spatial attention. Channel attention is computed as

Mc(F ) = σ! W1(ReLU(W0Favg)) + W1(ReLU(W0Fmax))

(3)  while spatial attention is defined as

(4)

Ms(F ) = σ! f 7×7[AvgPool(F ); MaxPool(F )]

These operations emphasize discriminative vegetation fea- tures while suppressing background responses caused by  soil, shadows, and illumination variations. The combined  transformer and CBAM mechanisms improve segmentation  near overlapping crop–weed boundaries.

E. ASPP Multi-Scale Context Aggregation

Fig. 1.  Proposed architecture.    For each token, Query (Q), Key (K), and Value (V)  representations are computed, and attention is calculated as    QKT  Attention(Q, K, V ) = Softmax √d  V  (2)

To capture contextual information at multiple scales, CBAM- refined features are processed using Atrous Spatial Pyramid  Pooling (ASPP) [4]. Parallel convolution branches with differ- ent dilation rates aggregate local and global context according  to

Conv ∗ r(F ∗ cbam)  (5)

M

FASPP =

r∈1,6,12,18,GAP

This enables accurate segmentation of both small weed  seedlings and large vegetation clusters.

F. Decoder and Loss Function

k

The ASPP output is fused with multi-scale encoder features  through the SegFormer decoder [9] to generate pixel-wise  predictions:

where dk denotes the key dimension. This mechanism allows  the network to model contextual relationships between plant

Yˆ = softmax(Wd  · FASPP )  (6)

To address class imbalance, the model is optimized using a  combination of cross-entropy and Dice loss:

L = L ∗ CE + L ∗ Dice  (7)


## 2 Σp YˆpYp + ε

LDice = 1 −

(8)  + ε  Σ

p Yˆp + Σp Yp

979-8-3315-8087-2/26/$31.00 ©2026 IEEE 548 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:37:45 UTC from IEEE Xplore.  Restrictions apply.

Proceedings of the 7th International Conference on Smart Systems and Inventive Technology (ICSSIT-2026) IEEE Xplore Part Number: CFP26P17-ART; ISBN: 979-8-3315-8087-2

G. Optimisation and Training Setup

TABLE I  PERFORMANCE EVALUATION ON WEEDSGALORE VALIDATION SET

The model is trained for 80 epochs using AdamW with  learning rates of 5  10−5 for the SegFormer encoder and  5 10−4 for the CBAM and ASPP modules. Cosine annealing,  mixed-precision training, and gradient clipping are employed  to improve optimization stability. Images are processed in  mini-batches of four.

×

Model  mIoU(%)  PA(%)  Prec.(%)  F1(%)

×

SegFormer-B1  77.80  98.73  85.95  87.11  SegFormer-B2  78.46  98.79  87.77  87.56  DeepLabv3+ (RN-50)  35.74  97.45  56.97  43.63  UNet++ (EB-4)  48.82  99.13  68.85  59.15  Enhanced DLv3+  29.99  91.73  38.66  38.92  SFB2-Enh. (Ours)  80.27  98.81  87.93  88.77  DLv3+ RGB [1]  50.81  88.90  48.30  49.10  DLv3+ MSI [1]  55.52  90.10  52.30  53.40

The overall WeedFormer pipeline consists of three stages:  hierarchical feature extraction using SegFormer-B2, attention- based refinement through CBAM, and multi-scale context ag- gregation using ASPP. The enhanced features are subsequently  decoded to generate pixel-level crop–weed segmentation maps.

PA=Pixel Accuracy; RN-50=ResNet-50; EB-4=EfficientNet-B4  SFB2-Enh.=SegFormer-B2+CBAM+ASPP (Proposed)

IV. RESULTS AND DISCUSSION

All models are evaluated on the WeedsGalore validation  split, which contains 26 images drawn from two geographically  distinct spatial patches. Mean Intersection-over-Union (mIoU)  serves as the primary ranking metric, with Pixel Accuracy (PA),  macro-averaged Precision, Recall, and F1-Score reported along- side it. The IoU per class is analyzed in detail; otherwise, the  overall IoU might indicate the failure in the underrepresented  classes Recall is additionally considered to evaluate the model’s  ability to correctly identify weed pixels, particularly in highly  imbalanced scenarios where minority weed classes occupy  only a small fraction of the image area. Together, these metrics  provide a detailed assessment of segmentation accuracy, class  discrimination capability, and robustness across different weed  categories.

suppression, and the ASPP multi-scale pooling stacked on an  already well-optimized pre-trained encoder.

The CNN-based models perform much worse. While the best- performing variant, DeepLabv3+ with a ResNet-50 backbone,  attains a poor 35.74% mIoU and the UNet++ 48.82%, the  other variant using the same backbone but adding the CBAM  and ASPP modules actually performs worse (29.99%) than the  original version. This is a clear case of a different optimization  process, where the additional modules increase the parameter  space too much for the ResNet-50 backbone, pre-trained on  only 104 images. Again, we see the consistent effect of the  same modules when stacked on the more powerful transformer  encoder, pre-trained on the much larger ADE20K dataset.

The biggest gap in performance is to the original multi- spectral DeepLabv3+ variant [1] using four-band imagery and  attaining 55.52% mIoU. However, the WeedFormer outper- forms it by a large margin of 24.75 mIoU using only the  standard three-band RGB imagery. This would indicate that  the expressiveness of the architecture plays a more deciding  factor in the quality of the segmentation result

A. Overall Performance Comparison


> **Table I shows the segmentation performance summary over**

> all the architectures. The highest-scoring model is the Weed-
Former (SFB2-Enhanced), which achieves the highest scores 
in all the metrics. It achieves the highest mIoU of 80.27%, 
PA of 98.81%, Precision of 87.93%, and F1-Score of 88.77%. 
To provide a comprehensive evaluation, multiple performance 
metrics are reported, including mean Intersection-over-Union 
(mIoU), Pixel Accuracy (PA), Precision, Recall, and F1-Score. 
While pixel accuracy measures overall classification correctness, 
mIoU provides a stricter assessment of segmentation quality 
by accounting for both false positives and false negatives. 
Precision and F1-Score further quantify the reliability of 
weed identification, particularly for minority classes. Reporting 
multiple complementary metrics ensures a more rigorous and 
balanced evaluation of model performance. The proposed 
WeedFormer model is benchmarked against both convolutional 
and transformer-based state-of-the-art architectures, including 
DeepLabv3+, UNet++, SegFormer-B1, and SegFormer-B2. In 
addition, comparisons are provided against previously published 
RGB and multispectral DeepLabv3+ baselines reported on the 
WeedsGalore dataset. This benchmarking strategy enables a 
comprehensive assessment of the proposed architecture across 
different segmentation paradigms and sensing modalities. 
The next best model, plain SegFormer-B2, lags by 1.81 mIoU. 
This gap is due to the effect of the CBAM channel and spatial

B. Per-Class IoU Analysis


> **Table II breaks down per-class IoU for all evaluated models.**

> WeedFormer achieves the highest IoU on every class without 
exception, with scores ranging from 72.24% on Quickweed to 
98.74% on the Background class. 
The segmentation accuracy for small and densely clustered 
weed regions is particularly demonstrated by the performance 
on the Quickweed class. Quickweed instances frequently appear 
as small vegetation patches surrounded by crops and exhibit 
strong visual similarity to neighboring plants, making their 
identification challenging. Despite these difficulties, Weed-
Former achieved an IoU of 72.24 for Quickweed segmentation. 
This performance can be attributed to the transformer-based 
attention mechanism, which captures contextual relationships 
beyond local neighborhoods, and the CBAM-ASPP modules 
that enhance fine-scale feature representation and multi-scale 
context aggregation. Consequently, the proposed framework 
effectively distinguishes small weed regions and densely packed 
vegetation structures, resulting in more accurate segmentation 
masks compared with conventional CNN-based approaches.

979-8-3315-8087-2/26/$31.00 ©2026 IEEE 549 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:37:45 UTC from IEEE Xplore.  Restrictions apply.

Proceedings of the 7th International Conference on Smart Systems and Inventive Technology (ICSSIT-2026) IEEE Xplore Part Number: CFP26P17-ART; ISBN: 979-8-3315-8087-2

TABLE II  PER-CLASS IOU (%) ON WEEDSGALORE VALIDATION SET

Model  BG  Maize Amar. Barn. Quick. W.Oth.  SegFormer-B1  98.65 72.44  68.28  73.41  68.59  85.41  SegFormer-B2  98.72 74.52  69.84  72.40  69.58  85.71  DLv3+ (RN-50)  97.43 19.39  12.80  5.58  7.33  71.91  UNet++ (EB-4)  99.22 35.79  32.22  21.40  13.15  91.13  Enh. DLv3+  91.27 17.96  10.77  3.16  10.20  46.57  SFB2-Enh.  98.74 76.93  73.27  74.45  72.24  86.01  DLv3+ RGB   97.94 71.46  74.32  45.95  6.26  8.92   DLv3+ MSI    98.37  73.03  76.17  53.55  21.11  10.86   BG = Background; Amar. = Amaranth; Barn. = Barnyard Grass  Quick. = Quickweed; W.Oth. = Weed Other

Fig. 3. Training and validation loss curves demonstrating stable convergence  of the proposed WeedFormer framework during optimization.

Fig. 2. Performance Comparison of Crop–Weed Segmentation Models.

The most diagnostically informative class is Quickweed,  which has only 249 labeled instances across the entire dataset  and bears strong visual resemblance to juvenile Amaranth  plants. WeedFormer reaches 72.24% Quickweed IoU, compared  to 21.11% for the best multispectral baseline and values  below 14% for all CNN-based models. This margin of over  51 percentage points cannot be explained by data volume  alone; it reflects the combined effect of CBAM channel- and-spatial recalibration amplifying discriminative feature  responses, and ASPP context pooling providing field-of-view  diversity sufficient to resolve locally ambiguous textures. CNN  architectures struggle uniformly on minority weed classes  Enhanced DeepLabv3+ reaches only 10.20% on Quickweed  and 3.16% on Barnyard Grass.

Fig. 4. Qualitative crop–weed segmentation results showing ground-truth  annotations,  WeedFormer  predictions,  error  maps,  and  uncertainty  distributions for representative UAV field images.

plateaus in the loss. The training and validation loss curves are  tightly coupled throughout the training process. This shows  that the model generalizes well instead of overfitting the small  training set of 104 images. The 5-epoch linear warm-up and the  subsequent cosine annealing schedule prevent large gradients  in the early epochs from destabilizing the pre-trained encoder  weights. The maximum validation mIoU of 80.27% occurs at  Epoch 72. From then on, the model weights are frozen for all  the subsequent evaluations.

Fig. 2 presents a visual summary of mIoU across all  architectures. From CNN-based to transformer-based models,  mIoU increases monotonically. The steepest single jump in  mIoU happens from the CNN to the transformer backbone ar- chitecture, validating the hypothesis that global self-attention is  the key architectural component accounting for the performance  gains.

D. Qualitative Results

Fig. 4 presents side-by-side qualitative comparisons on UAV  maize field images. Across all three example rows, WeedFormer  predictions closely track the ground-truth class boundaries.  The pixel-wise error map confirms that residual mistakes are  concentrated at thin plant edges and the most spectrally similar  weed pairs. The prediction-entropy map shows low uncertainty  over correctly labeled regions, with elevated uncertainty only  at class boundaries exactly where visual ambiguity is expected.

C. Training Dynamics

Fig. 3 traces the composite training and validation loss of  the WeedFormer model over 80 epochs. The loss decreases  smoothly from 2.73 at Epoch 1 to approximately 0.197 by  Epoch 80. There are no signs of instability or prolonged

E. Discussion

The experimental results demonstrate the effectiveness of  combining transformer-based contextual modeling, CBAM

979-8-3315-8087-2/26/$31.00 ©2026 IEEE 550 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:37:45 UTC from IEEE Xplore.  Restrictions apply.

Proceedings of the 7th International Conference on Smart Systems and Inventive Technology (ICSSIT-2026) IEEE Xplore Part Number: CFP26P17-ART; ISBN: 979-8-3315-8087-2

attention refinement, and ASPP multi-scale feature aggregation.  WeedFormer achieved an mIoU of 80.27

to autonomous weeding, where false negative errors would be  costly.

Error analysis reveals that most misclassifications occur near  overlapping crop–weed boundaries, dense vegetation clusters,  and shadowed regions where visual differences between crops  and weeds are limited. Uncertainty maps further show that  prediction ambiguity is concentrated around class boundaries,  suggesting that the model successfully learns meaningful  feature representations but remains challenged by inherently  ambiguous pixels.


## REFERENCES

[1]  E. Celikkan, T. Kunzmann, Y. Yeskaliyev, S. Itzerott, N. Klein, and M.

Herold, “WeedsGalore: A multispectral and multitemporal UAV-based  dataset for crop and weed segmentation in agricultural maize fields,” in  Proc. IEEE/CVF Winter Conf. Applications of Computer Vision (WACV),  2025.  [2] J. Weyler et al., “PhenoBench: A large dataset and benchmarks for seman-

tic image interpretation in the field,” arXiv preprint arXiv:2306.04557,  2024.  [3] M. Olsen, D. Konovalov, B. Philippa, P. Ridd, J. C. Wood, J. Johns, C.

The WeedsGalore dataset [1] contains images acquired under  varying illumination conditions, weed densities, and growth  stages, supporting robust model training. However, since the  dataset is primarily focused on maize fields, further evaluation  on additional datasets such as PhenoBench [2] is necessary to  establish broader generalization capability across crop species  and agricultural environments.

Banks, and R. White, “DeepWeeds: A multiclass weed species image  dataset for deep learning,” Scientific Reports, vol. 9, no. 1, pp. 1–12,  2019.  [4] L.-C. Chen, Y. Zhu, G. Papandreou, F. Schroff, and H. Adam, “Encoder-

decoder with atrous separable convolution for semantic image segmenta- tion,” in Proc. European Conf. Computer Vision (ECCV), 2018, pp. 833– 851.  [5] Z. Zhou, M. M. R. Siddiquee, N. Tajbakhsh, and J. Liang, “UNet++:

A nested U-Net architecture for medical image segmentation,” in Deep  Learning in Medical Image Analysis, 2018, pp. 3–11.  [6] I. Sa, Z. Chen, M. Popovic, R. Khanna, F. Liebisch, J. Nieto, and

From a practical perspective, WeedFormer enables accurate  crop–weed segmentation using only RGB UAV imagery,  eliminating the need for expensive multispectral sensors. This  makes the framework suitable for cost-effective precision  agriculture applications, including site-specific herbicide  application and early weed management.

R. Siegwart, “WeedNet: Dense semantic weed classification using  multispectral images and MAV for smart farming,” IEEE Robotics and  Automation Letters, vol. 3, no. 1, pp. 588–595, 2018.  [7] A. Milioto, P. Lottes, and C. Stachniss, “Real-time semantic segmentation

of crop and weed for precision agriculture robots using a fully convo- lutional network,” in Proc. IEEE Int. Conf. Robotics and Automation  (ICRA), 2018, pp. 5020–5027.  [8] A. Dosovitskiy et al., “An image is worth 16×16 words: Transformers for

The proposed WeedFormer achieved an IoU of 72.24%  for the Quickweed class, demonstrating strong segmentation  performance on small and densely clustered weed regions.

image recognition at scale,” in Proc. Int. Conf. Learning Representations  (ICLR), 2021.  [9] E. Xie, W. Wang, Z. Yu, A. Anandkumar, J. M. Alvarez, and P. Luo,

V. CONCLUSION

“SegFormer: Simple and efficient design for semantic segmentation with  transformers,” in Proc. Advances in Neural Information Processing  Systems (NeurIPS), 2021, pp. 12077–12090.

This paper introduced WeedFormer, a transformer-based  semantic segmentation framework for multi-class crop-weed  mapping from UAV imagery over maize fields. The architecture  pairs a pre-trained SegFormer-B2 backbone with CBAM  attention recalibration and ASPP multi-scale context pooling,  trained with a composite cross-entropy and Dice loss to handle  the severe class imbalance inherent to weed-mapping tasks. On  the WeedsGalore benchmark, WeedFormer achieves 80.27%  mIoU and 98.81% pixel accuracy state-of-the-art over all  CNN and transformer baselines, and 24.75 mIoU points above  the best published multispectral method despite using only  standard RGB input. The Quickweed class result alone 72.24%  IoU versus 21.11% for the prior best demonstrates robust  generalization to severely underrepresented weed classes with  strong visual similarity to neighboring crops. Three directions  are worth pursuing in future work. First, incorporating NIR  and Red Edge spectral bands into the SegFormer input stream  could provide additional vegetation indices that help separate  species with similar RGB appearances. Secondly, the  extension of WeedFormer to instance segmentation, for  example, via the model named Mask2Former would enable the  use of plant-level counting and localization, which would be  used in variable rate prescription maps for herbicides. Finally,  utilizing the capabilities of uncertainty estimation via Monte  Carlo dropout or deep ensembles would allow for the  integration of confidence maps into the prediction. This would  be useful in the safe human-in-the-loop approach

[10] J. Zhang et al., “Hybrid CNN-Transformer architecture for weed

recognition in field conditions,” Computers and Electronics in Agriculture,  vol. 212, 2023.  [11] S. Woo, J. Park, J.-Y. Lee, and I. S. Kweon, “CBAM: Convolutional block

attention module,” in Proc. European Conf. Computer Vision (ECCV),  2018, pp. 3–19.  [12] H. Zhao, J. Shi, X. Qi, X. Wang, and J. Jia, “Pyramid scene parsing

network,” in Proc. IEEE Conf. Computer Vision and Pattern Recognition  (CVPR), 2017, pp. 2881–2890.  [13] I. Sa et al., “WeedMap: A large-scale semantic weed mapping framework

using aerial multispectral imaging and deep neural network for precision  herbicide application,” Remote Sensing, vol. 10, no. 9, p. 1423, 2018.  [14] T. B. Shahi, C.-Y. Xu, A. Neupane, and W. Guo, “Recent advances

in deep learning methods for agricultural image classification,” Drones,  vol. 7, no. 8, p. 540, 2023.  [15] B. Cheng, A. Schwing, and A. Kirillov, “Masked-attention Mask

Transformer for universal image segmentation,” in Proc. IEEE/CVF  Conf. Computer Vision and Pattern Recognition (CVPR), 2022.

979-8-3315-8087-2/26/$31.00 ©2026 IEEE 551 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:37:45 UTC from IEEE Xplore.  Restrictions apply.
