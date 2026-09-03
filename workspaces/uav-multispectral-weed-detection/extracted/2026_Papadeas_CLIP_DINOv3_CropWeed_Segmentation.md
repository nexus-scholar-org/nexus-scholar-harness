---
title: "CLIP Meets DINOv3 for Effective Crop and Weed Multispectral Semantic Segmentation"
doi: "10.1007/978-3-032-26214-1_21"
authors: "Ilias Papadeas, Georgios Sandalis, Georgios Zamanakos, Ioannis Pratikakis"
extraction_engine: pymupdf (per-page, from proceedings volume)
tags: [RQ1, RQ3, WeedsGalore, CLIP, DINOv3, semantic-segmentation]
---

CLIP Meets DINOv3 for Eﬀective Crop 
and Weed Multisp ectral Semantic 
Segmen tation
Ilias Papadeas(B), Georgios Sandalis, Georgios Zamanakos, 
and Ioannis Pratik akis
Visual Computing Group, Department of Electrical and Computer Engineering, 
Democritus University of Thrace, X anthi, Greece
{ipapadea,gsandali,gzamanak,ipratika}@ee.duth.gr 
Abstract. Precision agriculture relies increasingly on accurate seman-
tic segmentation of crops and weeds to enable targeted interventions 
such as selective weeding and yield optimization. However, conventional 
deep learning models struggle to generalize across diverse ﬁeld conditions, 
especially when limited to RGB imagery. This work aims to develop a 
robust multispectral segmentation framework that eﬀectively incorpo-
rates vision-language modeling to improve crop and weed segmentation. 
To this end, we propose a hybrid semantic segmentation architecture 
that integrates multispectral sensing with foundational model features. 
Our model combines low-level spatial representations from a ResNet50 
backbone adapted for 5-channel input (R-G-B, Near-Infrared, Red-Edge) 
with high-level semantic features extracted from DINOv3’s backbone. A 
multi-scale attention fusion module merges these representations, while 
a cross-attention decoder incorporates CLIP-derived text embeddings to 
provide semantic guidance through class-speciﬁc language prompts. We 
validate our method on the “WeedsGalore” dataset, achieving 85.42% 
mIoU on the 3-class task (background, crop, weed) and 60.0% mIoU 
on the challenging 6-class task (species-level weeds) outperforming the 
state-of-the-art. T hese results demonstrate the value of combining mul-
tispectral inputs with self-supervised and vision-language foundational
models for robust, high-resolution segmentation in real-world agricul-
tural environments.
Keywords: Precision agriculture · Multispectral imagery · Semantic 
segmentation · Crop and weed segmentation · WeedsGalore
1
Introduction 
Weeds are a major limiting factor in global crop yield, competing with cultivated 
plants for water, nutrients and light. As food demand rises and climate variabil-
ity increases, precision agriculture oﬀers a scalable and sustainable solution— 
minimizing herbicide usage, while maximizing p roductivity. A key component of
c The Author(s), under exclusive license to Springer Nature Switzerland AG 2026 
K. Arai and P. Lorenz (Eds.): CVC 2026, LNNS 1974, pp. 346–364, 2026. 
https://doi.org/10.1007/978-3-032-26214-1_21


CLIP Meets DINOv3 for Eﬀective Crop and Weed
347
this approach is site-speciﬁc weed management (SSWM), which requires high-
resolution, temporally accurate weed detection. Among remote sensing tools, 
Unmanned Aerial Vehicles (UAVs) equipped with multispectral sensors (e.g., 
RGB, Near-Infrared, Red-Edge) have emerged as a ﬂexible and non-invasive 
platform for large-scale monitoring. Howev er, most existing models are either 
limited to RGB data or fail to generalize across div erse growth stages, crop
types and weed species.
To address these limitations, we propose a hybrid semantic segmentation 
architecture that integrates deep convolutional and transformer-based f ounda-
tional models. Our model combines spatial features from a ResNet50 [1] encoder 
(modiﬁed for 5-band multispectral input) with high-level semantic represen-
tations from a pretrained Vision Transformer of DINOv2 [2]/DINOv3 [3]. A 
multi-scale attention fusion module merges these c omplementary cues, while 
frozen CLIP’s [4] text embeddings oﬀer semantic guidance via class-leve l prompts 
through c ross-attention.
We evaluate our model on the “WeedsGalore” [5] dataset, the ﬁrst UAV-based 
multispectral benchmark for semantic and instance segmentation in maize ﬁelds. 
This dataset was selected for its 5-band spectral richness (RGB, Red-edge, NIR) 
and coverage of diverse growth stages, providing a challenging benchmark for 
aligning language-guided semantics with modality-speciﬁc spectral features in 
agricultural scenes. Our method sets a new state-of-the-art on both 3-class and 
6-class tasks, showing strong generalization to rare species and diverse pheno-
logical stages, demonstrating the value of combining multispectral inputs with 
foundational models for agricultural scene understanding. To the best of our 
knowledge, this is the ﬁrst architecture to combine DINOv3 visual features and 
CLIP-based language embeddings f or ﬁne-grained multispectral weed segmenta-
tion, bridging visual and semantic modalities in a uniﬁed framework.
In summary, our con tributions a re:
1. We propose a novel semantic segmentation architecture that comprises foun-
dational models (DINOv3 & CLIP) in a v ision-language modeling context on 
multispectral imagery for precision agriculture.
2. We integrate an eﬀective multi-scale attention fusion mechanism between 
low-level C NN features and high-level DINOv3 semantic priors.
3. We employ a CLIP-guided cross-atten tion deco der.
4. We conduct an extensive evaluation on the “WeedsGalore” dataset for both 
3-class and 6-class segmentation, achieving results that compare f avorably to 
the state-of-the-art with signiﬁcant gains i n rare class IoU.
The remainder of this study is structured as follows: Sect. 2 reviews related work 
in crop–weed segmentation and foundational models for precision agriculture.
Section 3 describes the proposed hybrid architecture, detailing the multispectral 
encoder, multi-scale attention fusion and CLIP-guided cross-atten tion along with 
the overall training strategy. Section 4 outlines the experimental setup including 
the dataset and evaluation metrics and presents both quantitative and qual-
itative results for the 3-class and 6-class segmentation tasks. Finally, Sect. 5 
concludes the study and outlines directions for future work.


348
I. Papadeas et al.
2
Related Wo rk 
2.1
Deep Learning-Based Approaches for Crop-Weed Segmentation 
Early approaches relied on handcrafted features and traditional machine learning 
algorithms, such as Random Forests [6], which demonstrated degraded perfor-
mance and poor generalization across diverse ﬁeld conditions. With the rise of 
CNNs, architectures like SegNet [7,8] and DeepLabv3+ [5,9] showed marked 
improvements in segmentation accuracy, particularly when combined with mul-
tispectral data. Deep learning has become the dominant approach for crop and 
weed segmentation in precision agriculture. However, most CNN-based mod-
els rely on deep architectures to capture long-range dependencies, increasing 
their computational demands and limiting their s calability in large-scale UAV
deployments [10]. Furthermore, while these models perform well in general crop– 
weed segmentation, their eﬀectiveness often drops when facing rare or visually 
ambiguous weed species, where ﬁne-grained discrimination under class imbal-
ance requires both strong local spatial detail and high-level semantic context. 
Recent eﬀorts have begun leveraging transformer-based architectures, such as
MaskFormer [5,11] in the ﬁeld of c rop-weed segmen tation.
2.2
Fusion of Multispectral Modalities in Semantic Segmentation 
Multispectral imagery enhances weed segmentation by providing spectral cues 
beyond the visible spectrum. Near-Infrared (NIR) and Red-Edge (RE) bands 
are especially useful, as they reﬂect diﬀerences in plant health and chlorophy ll 
content. Simple fusion strategies, such as stacking RGB with NIR a nd RE chan-
nels, are commonly used [5,12], but fail to account for modality-speciﬁc noise, 
relevance, or temporal dynamics. Static fusion mechanisms can be fragile when 
spectral quality varies due to lighting, occlusions, or sensor artifacts. More recent 
approac hes advocate for adaptive or dynamic fusion modules that prioritize 
informative spectral bands depending on context [13,14]. Such methods are par-
ticularly important for ﬁeld-based applications where environmental variability 
is high. Despite these advances, foundational models t rained on RGB imagery 
are rarely extended to multispectral domains [15,16], creating a gap this study 
addresses.
2.3
DINO-Family of Vision Transformers 
The DINO-family of vision transformers has demonstrated strong performance in 
self-supervised representation learning. DINOv1 [17] introduced a self-distillation 
framework without labels, enabling vision transformers to learn highly semantic 
representations and exhibit emergen t object segmentation via patch-level atten-
tion. DINOv2 [2] scaled this paradigm to curated large-scale datasets, deeper 
ViT [18] architectures and improved training stability, resulting in universal 
visual features competitive with weakly supervised methods a cross both image-
level and pixel-level tasks. DINOv3 [3] builds upon this by rethinking patch-level


CLIP Meets DINOv3 for Eﬀective Crop and Weed
349
pretraining objectives. It introduces masked self-distillation with reconstruction 
and localization tasks, optimized for dense prediction scenarios such as segmen-
tation and object detection. These enhancements result in stronger spatial local-
ization, improved mid-level features and better generalization for downstream 
dense tasks. In this work, we leverage DINOv3 as a high-level seman tic encoder 
to complement the spatial detail captured by CNN backbones. To our knowl-
edge, this represents one of the earliest applications of DINOv3 in multispectral
crop–weed segmentation.
2.4
CLIP for Semantic Guidance in Segmentation 
Contrastive Language–Image Pretraining (CLIP) [4] has enabled vision– 
language models to align visual inputs with natural language descriptions via 
large-scale contrastive training. While originally developed for zero-shot classiﬁ-
cation, CLIP h as since been adopted in dense prediction tasks such as seman tic
segmentation and object detection [19–21]. These approaches leverage CLIP’s 
pretrained text and image encoders to i nject semantic priors or g uide visual
feature learning.
In the proposed method, CLIP is used to encode class-level semantics via 
frozen text embeddings that describe each class (e.g., “crop plant leaf”). These 
embeddings g uide the segmentation decoder through cross-attention mecha-
nisms, enhancing semantic alignment during prediction [22]. This work presents 
a novel combination of CLIP-based guidance with the robust features of DINOv3 
for crop and weed segmentation.
2.5
UAV-Based Monitoring and Dataset Challenges 
Unmanned Aerial Vehicles (UAVs) are increasingly employed in precision agri-
culture due to their non-invasive nature and ability to capture high-resolution 
imagery across large and irregular terrains. Compared to ground-based plat-
forms, UAVs oﬀer superior spatial coverage, rapid deployment and adaptability 
to variable ﬁeld conditions—traits particularly beneﬁcial for monitoring crop–
weed dynamics.
However, semantic segmentation using UAV imagery presents distinct chal-
lenges: non-uniform lighting, scale variation, occlusions, cluttered backgrounds 
and the small size of weed instances relative to the scene. These factors com-
plicate both annotation and model generalization. Furthermore, publicly avail-
able datasets tailored to UAV-based weed monitoring remain limited—especially 
those oﬀering dense pixel-wise annotations, mu ltispectral bands and temporal
diversity.
The “WeedsGalore” [5] dataset addresses these gaps by providing 5-band 
(RGB, NIR, RE) UAV imagery over maize ﬁelds, with both 3-class (background, 
crop, weed) and species-level semantic labels. Its multitemporal structure (cap-
turing diﬀerent crop growth stages), combined with detailed annotations, makes


350
I. Papadeas et al.
it well-suited for benchmarking segmentation models under realistic ﬁeld vari-
ability. In this work, we leverage “WeedsGalore” to explore the in tegration of 
foundational models into high-precision w eed segmentation pipelines.
3
Proposed Metho d 
In this section, we present a detailed description of the proposed method. Unlike 
traditional DeepLabV3-based models that rely solely on spatial convolutions, our 
approach introduces a novel fusion of CNN, vision transformer and frozen lan-
guage priors to enable richer semantic segmentation under class imbalance. Our 
architecture adopts a hybrid CNN–Transformer design, combining a multispec-
tral ResNet encoder with powerful visual and language priors from foundational 
models to enhance segmentation in multispectral agricultural imagery. Specif-
ically, a ResNet50 backbone extracts low-level multisp ectral features, DINOv3 
(and DINOv2 variation) provides high-level visual representations and CLIP con-
tributes semantic guidance via frozen text embeddings. This strategy enables the 
model to jointly capture ﬁne-grained spatial detail, global con text and semantic
class cues. Details about the training strategy and the loss function used are
discussed in the sequel.
3.1
Overall Architecture 
We propose a hybrid CNN-Transformer architecture that combines multi-scale 
convolutional features with self-supervised vision representations and language-
guided semantic understanding for crop and weed semantic segmentation. As 
shown in Fig. 1, our method integrates four complementary components: 1) a 
ResNet50 backbone with DeepLabV3+ decoder for hierarchical feature extrac-
tion from multispectral imagery, 2) a DINOv3 vision transformer for learn-
ing rich, self-supervised visual representations, 3) a multi-scale attention fusion 
mechanism and 4) a CLIP-guided cross-attention decoder for incorporating 
semantic class understanding through natural language supervision. This uni-
ﬁed framework enables eﬀective exploitation of both low-level spatial details 
and high-level semantic cont ext while addressing the domain-speciﬁc challenges
of agricultural scene understanding.
Baseline Semantic Segmentation Network. We adopt ResNet50 backbone 
as our base segmentation architecture due to its proven eﬀectiveness in dense 
prediction tasks. The ResNet50 encoder extracts multi-scale features at diﬀerent 
spatial resolutions: layer1 ( H 
4 × W 
4 ), layer2 ( H 
8 × W 
8 ), layer3 ( H 
16 × W 
16 ) and layer4 
( H 
32 × W 
32 ). To support multispectral input (5 channels: R, G, B, NIR, RE), we 
modify the ﬁrst convolutional layer from 3 to 5 input channels while preserving
pre-trained ImageNet weights for the RGB channels.


CLIP Meets DINOv3 for Eﬀective Crop and Weed
351
Fig. 1. Overview of the proposed crop and weed multispectral seman tic segmentation 
arc hitecture.
DINOv3 Vision Transformer Integration. We incorporate DINOv3 (ViT-
B/16 backbone) as a parallel branch for feature extraction. Compared to super-
vised p retraining, DINOv3 oﬀers the following signiﬁcan t advantages:
1. Self-supervised learning: Trained on large-scale unlabeled data, enabling 
the extraction of general visual patterns without reliance on man ual annota-
tions.
2. Semantic richness: DINOv3’s hierarchical feature representations capture 
both ﬁne-grained texture patterns and high-level semantic context, enabling 
robust d iscrimination between visually similar crop and weed species.
Given an input image of size H × W , DINOv3 outputs a feature grid of size 
H 
16 × W 
16 × 768. For a 616 × 616 input (zero-padded from 600 × 600), this yields 
a 38 × 38 × 768 feature map, which is bilinearly int erpolated to align spatially
with ResNet features at multiple scales.
Multi-scale Attention Fusion. To eﬀectively combine CNN and Transformer 
features, we design a multi-scale attention fusion mechanism operating at two 
hierarchical levels, which is shown in Fig. 2. 
For a given scale with ResNet features R ∈ RCr×H×W and DINOv3 features 
D ∈ RCd×H ×W , the fusion proceeds as follows: 
First, DINOv3 features are interpolated to match ResNet spatial dimensions: 
Dinterp = Interpolate(D) ∈ RCd×H×W
(1) 
Both features are projected to a common 256-channel space: 
Rproj = ReLU(BN(Conv1×1(R))) ∈ R256×H×W
(2) 
Dproj = ReLU(BN(Conv1×1(Dinterp))) ∈ R256×H×W
(3)


352
I. Papadeas et al.
Fig. 2. Overview of the multi-scale attention fusion mech anism.
The projected features are concatenated and fused: 
C = Concat(Rproj, Dproj) ∈ R512×H×W
(4) 
F = Conv1×1(ReLU(BN(Conv3×3(C)))) ∈ R256×H×W
(5) 
Channel attention is applied to adaptively weight feature contributions: 
A = σ(Conv1×1(ReLU(Conv1×1(GAP(F))))) ∈ R256×1×1
(6) 
Ffused = F
A ∈ R256×H×W
(7)


CLIP Meets DINOv3 for Eﬀective Crop and Weed
353
where, σ is the sigmoid activation function, GAP denotes global average pool-
ing and the channel attention uses a bottleneck with reduction ratio of 16 
(256→16→256). This fusion is instantiated at two scales: 
Low-level fusion (H = Hinput 
4 
, W = Winput 
4
): 
combines ResNet layer1 (Cr = 256) with upsampled DINOv3 features. 
High-level fusion (H = Hinput 
32 
, W = Winput 
32 
): 
combines ResNet la yer4 (Cr = 2048) with downsampled DINOv3 features.
This dual-pathway fusion preserves ﬁne-grained spatial details from early 
CNN layers while incorporating high-level semantic understanding from deep 
layers, while the t ransformer branch of DINOv2/v3 injects global context and 
semantic priors from large-scale pretraining.
ASPP Decoder. The high-level fused features are processed by an Atrous 
Spatial Pyramid Pooling (ASPP) of DeepLabv3+ module to capture multi-scale 
contextual information: 
FASPP = ASPP(Fhigh) ∈ R 
H 
32 × W 
32 ×256
(8) 
where, ASPP applies parallel Atrous convolutions with dilation rates {6, 12, 18}, 
a 1 × 1 convolution and global average pooling, concatenating the results before 
projecting to 256 channels.
The ASPP output is upsampled by 4× and concatenated with a projected 
version of the low-level features: 
Flow-proj = Conv1×1(Flow) ∈ R 
H 
4 × W 
4 ×48
(9) 
Fdec = Concat(Upsample4×(FASPP), Flow-proj) ∈ R 
H 
4 × W 
4 ×304
(10) 
This combined feature map is then processed by the CLIP-guided cross-attention 
decoder, as described in the sequel.
CLIP-Guided Cross-Attention Decoder. We enhance semantic segmenta-
tion by integrating textual class knowledge via a frozen CLIP (ViT-B/16) text 
encoder, as shown in Fig. 3. 
Class-speciﬁc prompts are deﬁned as follows: for the 3-class task, we use “back-
ground soil”, “crop plant leaf” and “weed plant”; for the 6-class task, we adopt 
“background soil”, “crop plant leaf” and species-speciﬁc prompts: “amaranthus 
retroﬂexus weed”, “echinochloa crus-galli weed”, “falgalinsoga parviﬂora weed” 
and “other weed species”. CLIP encodes these prompts into ﬁxed textual embed-
dings T ∈ RC×512, which are ﬁrst projected to match the visual feature dimen-
sion: 
T = ReLU(LayerNorm(WtextT)) ∈RC×256
(11) 
The projected text features then guide the decoder via cross-attention: 
Q = WQFlatten(Fdec) ∈ RB×HW ×256
(12)


354
I. Papadeas et al.
Fig. 3. Illustration of the CLIP-Guided cross-attention decoder. 
K = WKT ∈ R1×C×256
(13) 
V = WV T ∈ R1×C×256
(14) 
Attn = softmax QK
√
256 
∈ RB×HW ×C
(15)


CLIP Meets DINOv3 for Eﬀective Crop and Weed
355
Table 1. Learning rates and parameter breakdown for e ach mo dule
Component
Params LR
Rationale 
ResNet50 backbone
25.6M 
1 × 10− 3 Standard supervised LR 
DINOv3 (frozen blocks 1–10)
71.8M 
—
Preserve pre-trained representations 
DINOv3 (unfrozen blocks 11–12)
14.2M 
1 × 10− 5 Conservative ﬁne-tuning 
Multiscale attention fusion
3.5M
5 × 10− 4 Moderate rate for cross-modal alignment 
ASPP decoder
2.2M
5 × 10− 4 Spatial pyramid pooling 
CLIP-guided cross-attention decoder 1.6M
5 × 10− 4 Semantic guidance integration 
CLIP text encoder
63.4M 
—
Frozen for semantic guidance 
Fattended = Reshape(Attn · V) ∈ RB×256×H×W
(16) 
Fenhanced = Fdec + Fattended
(17) 
where, the attended features are added to the decoder features via a residual 
connection. This cross-attention mechanism enables the decoder to attend to 
class-speciﬁc semantic cues, improving discrimination of rare species and resolv-
ing visually am biguous crop & weed boundaries.
Training Strategy. To balance eﬃciency and domain adaptation, we adopt a 
partial ﬁne-tuning approach: only the ﬁnal two transformer blocks (11–12) of the 
DINOv3 backbone are unfrozen, while earlier layers remain frozen to preserve 
general representations learned during self-supervised pre-training. This strat-
egy facilitates adaptation to the agricultural multispectral domain with reduced
computational cost.
As shown in Table 1, learning rates (LR) are tuned per module based on 
their stability needs. The full model contains 182.3M parameters, with only 
25.9% being trainable (the rest remaining frozen), reﬂecting the eﬃciency of 
our adaptation strategy. DINOv3’s unfrozen layers are ﬁne-tuned conservatively 
using a learning rate of 1 × 10−5 to mitigate overﬁtting and avoid catastrophic 
forgetting. The ResNet50 backbone uses a standard supervised rate of 1 × 10− 3, 
while task-speciﬁc components including the multi-scale fusion modules, ASPP, 
and CLIP-guided cross-attention decoder adopt a moderate rate of 5 × 10−4 to 
support c ross-modal alignment and decoder learning. The CLIP text encoder
remains frozen, acting as a semantic prior.
All trainable components follow a cosine annealing learning rate schedule as 
follows: 
ηt = ηmin + 1 
2 (ηmax − ηmin) 1 + cos 
Tcur 
Tmax
π
(18) 
where, ηmax denotes the initial rate for each component, ηmin = 0, Tcur is the 
current epoch and Tmax = 200.


356
I. Papadeas et al.
4
Experiments 
4.1
Dataset and Implementation Details 
Dataset. The “WeedsGalore” dataset [5] was used for training and evaluation 
of the proposed model. It is a publicly available multispectral benchmark for 
semantic weed segmentation in maize ﬁelds, collected using a UAV platform. 
The dataset consists of 156 image tiles of size 600 × 600 pixels with pixel-level 
annotations, acquired over four ﬂights under varying growth stages and ﬁeld 
conditions. Each image contains ﬁve spectral bands (R-G-B, Red-Edge and Near-
Infrared), enabling robust crop & weed discrimination. The dataset is split into 
104 training, 26 validation and 26 test samples following the oﬃcial protocol, 
ensuring no spatial overlap between splits. We evaluate on two segmentation 
tasks: a 3-class task (background, crop, weed) and a 6-class task (background, 
crop and four weed classes: Amaranthus retroﬂexus (amaranth), Echinochloa 
crusgall (barnyard g rass), Galinsoga parviﬂora (quickweed) and all the rest are
merged as other weeds.
Implementation Details. All models are implemented using the PyTo rch 
framework [23]. Training is conducted for 200 epochs with a batch size of 8. All 
experiments a re executed on a single NVIDIA L40s GPU with 46 GB memory.
We use the AdamW optimizer with a weight decay of λ = 1 × 10−4 and 
employ the standard cross-entropy loss for multi-class segmentation. The cross-
entropy loss f or a single observation o is deﬁned as: 
LCross-Entropy = − 
M 
c=1
yo,c log(po,c)
(19) 
where, M is the total number of classes, yo,c ∈ {0, 1} is the binary indicator 
denoting whether class c is the correct class for observation o and po,c is the 
predicted probability of class c for observation o.
To improve generalization, we apply standard data augmentations during 
training, including random 90-degree rotations (0◦, 90◦, 180◦, 270◦), horizontal 
and vertical ﬂips and additive Gaussian noise sampled from a normal distribution 
with standard deviation σ = 1/25. No scaling, cropping, or color jittering is 
applied to preserve pixel-wise alignment across multispectral channels.
Model Initialization. We adopt a modular weight initialization scheme. The 
ResNet50 encoder is initialized with ImageNet-pretrained weights for the RGB 
channels. The DINOv3 ViT-B/16 backbone is initialized from the oﬃcial self-
supervised pretrained weights. For the CLIP text encoder, we use the oﬃcial
pretrained ViT-B/16 model weights.
4.2
Ablation Studies 
DINOv2 vs. DINOv3 Backbone Comparison. We ﬁrst analyze the impact 
of the vision backbone by comparing DINOv2 and DINOv3 under diﬀerent patch


CLIP Meets DINOv3 for Eﬀective Crop and Weed
357
sizes and learning rate schedulers, as reported in Table 2. When trained with 
a polynomial decay schedule, DINOv2 (14 × 14 patches) slightly outperforms 
DINOv3 (16 × 16), achieving 85.35% mIoU compared to 85.30%. However, this 
trend reverses when cosine annealing is employed. While DINOv2 experiences a 
noticeable performance drop under cosine scheduling, DINOv3 beneﬁts from it, 
achieving the best overall performance of 85.42% mIoU. Based on these results, 
we adopt DINOv3 with a c osine annealing scheduler for all subsequent experi-
ments.
Table 2. Comparison of DINOv2 vs. DINOv3 backbones with diﬀerent patc h sizes and 
learning rate schedulers.
Backbone
Patch Size Scheduler
mIoU (Test) Δ 
DINOv2 ViT-B
14 × 14
Polynomial 85.35%
— 
DINOv2 ViT-B
14 × 14
Cosine
84.91%
−0.44% 
DINOv3 ViT-B
16 × 16
Polynomial 85.30%
−0.05% 
DINOv3 ViT-B 16 × 16
Cosine
85.42%
+0.07% 
Partial Unfreezing Strategy. We study the impact of unfreezing diﬀerent 
numbers of transformer blocks in the DINOv3 backbone i n both validation and 
test set, as summarized in Table 3. Fully freezing the backbone yields a com-
petitive baseline of 83.99% mIoU on the test set. Unfreezing the last two blocks 
improves generalization signiﬁcantly, achieving the best performance (85.42%) 
with a positive generalization gap of +1.50%. On the contrary, unfreezing four 
blocks further increases the number of trainable parameters, but leads to over-
ﬁtting: although v alidation accuracy remains high (83.99%), test performance 
degrades to 84.52%. These results conﬁrm that partial ﬁne-tuning of the upper-
most layers pro vides an eﬀective balance between adaptation and preservation
of pre-trained representations.
Table 3. Eﬀect of partial unfreezing on p erformance and g eneralization
Conﬁguration
Trainable Params Val mIoU Test mIoU Gap 
All frozen (baseline) 41.0M (15.4%)
83.49%
83.99%
+0.50% 
Unfreeze 2 blocks
45.1M (16.9%)
83.92%
85.42%
+1.50% 
Unfreeze 4 blocks
59.2M (22.2%)
83.99%
84.52%
+0.53% 
Learning Rate Sensitivity. We further investigate the sensitivity of the pro-
posed method to diﬀerent learning rate combinations for the ResNet encoder and 
the partially unfrozen DINOv3 backbone, as shown in Table 4. Starting with a 
conservative approach, using 5 × 10−4 for ResNet and 1 × 10−5 for DINOv3


358
I. Papadeas et al.
achieves 84.98% test mIoU with a val-test gap of +1.03%, demonstrating sta-
ble generalization but suboptimal convergence. Increasing the ResNet learning 
rate to 1 × 10−3, while maintaining 1 × 10−5 for DINOv3 yields the best perfor-
mance (85.42% test mIoU) with an improved val-test gap of +1.50%. However, 
increasing the DINOv3 learning rate to 2 × 10−5 leads to overﬁtting: validation 
performance improves to 84.18% mIoU, but test accuracy degrades to 83.75% 
with a negative val-test gap of −0.43%. These results highlight the importance of 
employing very low learning rates when ﬁne-tuning large self-supervised vision
transformers, in order to prevent catastrophic forgetting while maintaining gen-
eralization.
Table 4. Impact of learning rate combinations on pe rformance.
ResNet LR DINOv3 LR Val mIoU Test mIoU Gap 
5 × 10−4
1 × 10−5
83.95%
84.98%
+1.03% 
1 × 10−3
1 × 10−5
83.92%
85.42%
+1.50% 
1 × 10−3
2 × 10−5
84.18%
83.75%
−0.43% 
4.3
Comparison with the State-of-the-Art 
“WeedsGalore” 3-Class Results. Table 5 presents a comprehensive compar-
ison of our proposed method against state-of-the-art baselines and intermediate 
mo del ablations on the “WeedsGalore” 3-class segmentation task.
Table 5. Comparison with the state-of-the-art methods on the test s et of “WeedsGa-
lore” 3 -class task.
Method
Input mIoU
IoU bg
IoU crop IoU weed Δ vs. B est 
MaskFormer [5]
MSI 80.27% 97.99% 69.49% 73.33% −5.15% 
DeepLabV3+ [5]
MSI 82.90% 98.45% 72.93% 77.31% −2.52% 
+ DINOv2 (frozen)
MSI 83.88% 98.45% 76.38% 76.82% −1.54% 
+ CLIP (frozen)
MSI 82.27% 98.48% 72.82% 75.51% −3.15% 
+ DINOv2 + CLIP (frozen)
MSI 83.99% 98.50% 76.03% 77.44% −1.43% 
+ DINOv2 + CLIP (unfreeze 2) MSI 85.35% 98.51% 79.02% 78.53% −0.07% 
+ DINOv3 (frozen)
MSI 84.80% 98.33% 78.12% 77.95% −0.62% 
+ DINOv3 + CLIP (poly)
MSI 85.30% 98.53% 79.00% 78.37% −0.12% 
+ DINOv3 + CLIP (cosine) MSI 85.42% 98.55% 79.09% 78.63% — 
MaskFormer performs at 80.27%, while the baseline DeepLabV3+ using mul-
tispectral (MSI) input achieves 82.90% in terms of mIoU. Introducing frozen 
DINOv2 features leads to a noticeable gain, improving mIoU to 83.88%, partic-
ularly beneﬁting crop segmentation. When CLIP embeddings are added alone


CLIP Meets DINOv3 for Eﬀective Crop and Weed
359
(frozen), the performance drops slightly (82.27%), suggesting that CLIP alone 
does not suﬃce. However, their combination (+ DINOv2 + CLIP) restores 
and surpasses baseline performance, reaching 83.99% mIoU. Further gains are 
achieved when partially unfreezing the DINOv2 + CLIP branch, boosting per-
formance to 85.35%, with large improvemen ts in crop and weed classes.
Transitioning to frozen DINOv3 features results to a mIoU of 84.80%. Com-
bining DINOv3 with CLIP and using a polynomial decay schedule results in a 
comparable mIoU of 85.30%, while adopting cosine learning rate scheduling pro-
vides the highest performance overall. The ﬁnal conﬁguration, DINOv3 + CLIP 
(cosine), sets a new state-of-the-art on this benchmark, achieving a n mIoU of 
85.42%—a +2.52% improvement over the strongest baseline. This includes sub-
stantial gains in crop segmentation (+6.16%) and weed segmentation (+1.32%),
while background performance remains consistently high (98.55%).
It is important to highlight the contribution of incorporating CLIP-guided 
cross-attention. More speciﬁcally, the mIoU is increased by +0.11% in DINOv2 
and +0.62% in DINOv3. Notably, in DINOv3 the gains are particularly pro-
nounced in the crop and weed categories, which see IoU improvements of +0.97% 
and +0.68%, respectively. These ﬁndings suggest that CLIP’s semantic priors 
enhance the model’s ability to disambiguate visually similar regions, especially 
between crops and weeds. Thus, the proposed CLIP-guided cross-attention is 
particularly eﬀective under class imbalance, as language embeddings provide 
stable class-level semantic cues in ch allenging visual conditions, highlighting the
value of joint multi-modal representation learning.
Figure 4 showcases qualitative segmentation results across four test scenar-
ios. In the ﬁrst row, dense mixed vegetation under occlusion poses a strong 
challenge. DeepLabV3+ fails to capture plant boundaries, misclassifying large 
weed regions as background. While DINOv2 + CLIP improves segmentation 
detail, DINOv3 + CLIP demonstrates sharper separation and accurate delin-
eation of both crops and weeds, even under clutter. The second row illustrates 
patchy crop development with dense weed invasion along furrows. DeepLabV3+ 
yields inconsistent weed boundaries and undersegments crops, whereas DINOv2 
+ CLIP adds structure but suﬀers from false positives. DINOv3 + CLIP oﬀers 
the most coherent weed patches and maintains crop continuity, aligning best 
with the ground truth. The third row contains low-contrast textures and mini-
mal v egetation. All models struggle with background noise, with DeepLabV3+ 
particularly failing to isolate crop rows. DINOv3 + CLIP maintains alignment 
and minimizes false detections, showing robustness in low-texture conditions. 
Lastly, an early-stage crop scene with bare soil highlights the models’ sensitiv-
ity to sparse v egetation. DeepLabV3+ heavily oversegments, while DINOv2 +
CLIP reduces noise. DINOv3 + CLIP achieves the most stable segmentation,
eﬀectively preserving spatial structure with minimal hallucinations.
“WeedsGalore” 6-Class Multi-species Results. To assess the robustness 
of our method in ﬁne-grained and class-imbalanced scenarios, we evaluate the 
variations of the proposed method on the 6-class “WeedsGalore” benchmark. As


360
I. Papadeas et al.
Fig. 4. Qualitative results on the 3-class “W eedsGalore” segmentation task.
shown in Table 6, our best-performing model, DINOv3 + CLIP (cosine), achieves 
an mIoU of 59.97%, surpassing all previous baselines. Compared to DeepLabV3+ 
with MSI input (55.52%) and MaskFormer (50.65%), our model yields relative 
gains of + 4.45% and +9.32%, respectively.
Performance improves consistently across all species, with background and 
crop classes remaining strong (98.46% and 78.66% IoU). At the species level, 
DINOv3 + CLIP signiﬁcantly enhances segmentation for both common and 
rare classes. Notably, for other weed, the IoU improves from 10.86% to 23.63%, 
indicating a substantial gain under extreme class imbalance. Other species also 
beneﬁt: Amaranthus retroﬂexus (+4.47%), Echinochloa crusgall (+2.54%) and
Galinsoga parviﬂora (+1.22%).
It is worth examining the contribution of CLIP-guided cross-attention which 
is also present on the 6-class “WeedsGalore” task. While the ResNet + DINOv3 
conﬁguration already achieves strong performance (59.23% mIoU), the addition 
of frozen CLIP embeddings consistently improves segmentation quality across 
all classes, yielding a gain of +0.74% mIoU without any task-speciﬁc ﬁne-tuning 
of the text encoder. These improvements are most pronounced for minority and 
visually ambiguous species, such as Other weed and Galinsoga parviﬂora (quick-
weed), where CLIP-driven semantic priors help disambiguate class boundaries 
under severe class imbalance. More speciﬁcally, incorporating CLIP-guided cross-
attention outperforms the baseline by +12.77% for Other weed and +1.22% for


CLIP Meets DINOv3 for Eﬀective Crop and Weed
361
Table 6. Comparison with the state-of-the-art on the test set of “WeedsGalore” 6-class 
task. Am, gr, qw and wo correspond to amaranth, barnyard grass, quickweed and weed 
other, respe ctively.
Method
Input mIoU
IoU bg
IoU crop IoU am 
IoU gr
IoU qw
IoU wo
Δ vs. B est 
MaskFormer [5]
MSI 50.65% 97.90% 68.04% 73.11% 45.34% 8.66%
10.86% −9.32% 
DeepLabV3+ [5]
MSI 55.52% 98.37% 73.03% 76.17% 53.55% 21.11% 10.86% −4.45% 
+DINOv2 (no CLIP)
MSI 59.79% 98.42% 76.54% 79.37% 55.16% 27.12% 22.13% −0.18% 
+DINOv3 (no CLIP)
MSI 59.23% 98.50% 78.06% 79.91% 55.63% 22.55% 20.75% −0.74% 
+DINOv2 + CLIP
MSI 58.90% 98.50% 77.55% 80.96% 56.30% 21.71% 18.38% −1.07% 
+DINOv3 + CLIP (poly)
MSI 58.16% 98.39% 78.59% 79.32% 54.84% 22.34% 15.49% −1.81% 
+DINOv3 + CLIP (cosine) MSI 59.97% 98.46% 78.66% 80.64% 56.09% 22.33% 23.63% — 
Fig. 5. Qualitative results on the 6-class “W eedsGalore” segmentation task.
Galinsoga parviﬂora. This behavior suggests that CLIP complements DINOv3 
by injecting high-level semantic context rather than low-level visual cues, lead-
ing to more robust multi-species segmentation without degrading performance 
on dominant classes.
Figure 5 illustrates qualitative results on the 6-class segmentation task of the 
“WeedsGalore” dataset, showcasing performance under increasing complexity. 
In the ﬁrst two rows—characterized by sparse and low-contrast vegetation—all 
methods struggle to detect minority classes, with DeepLabV3+ and DINOv2 + 
CLIP often missing ﬁne weed instances. DINOv3 models preserve crop alignment


362
I. Papadeas et al.
and show fewer false positives, with CLIP further improving class separation. 
In the third and fourth rows, dense and diverse instances of weed make both 
boundary precision and inter-class discrimination challenging. Here, DINOv3 + 
CLIP achieves the clearest segmentation, capturing both broadleaf and grass 
weed structures more accurately than other variants. Notably, DINOv2 + CLIP 
maintains structural continuity, but suﬀers from class confusion, while DINOv3
alone yields cluttered predictions with more fragmented boundaries.
5
Conclusion 
In this study, a multi-modal approach for crop–weed segmentation is proposed 
that combines foundational models (DINOv3), language-guided semantic pri-
ors (CLIP) and convolutional features (DeepLabV3+) within a uniﬁed multi-
branch architecture. The proposed method achieves state-of-the-art results on 
the “WeedsGalore” dataset, with 85.42% mIoU for 3-class segmentation (+2.52% 
over baseline) and 60.0% for 6-class species classiﬁcation (+4.48%), including 
signiﬁcant gains on rare classes (e.g., Other weed: 10.86% →23.63%).
A partial unfreezing strategy with diﬀerentiated learning rates enables eﬃ-
cient adaptation, retaining 83.1% of parameters frozen. Ablation studies conﬁrm 
the importance of cosine learning rate schedules for DINOv3 and the impact of 
CLIP guidance in improving detection of rare species.
Future work includes knowledge distillation to lightweight models for real-
time inference, extension to temporal multispectral sequences for weed stage 
modeling and cross-dataset validation across dive rse crops and regions.
Beyond architectural quantitative improvements, these ﬁndings have direct 
implications for precision agriculture. Improved robustness under class imbalance 
and visual ambiguity enables more reliable site-speciﬁc weed management and 
reduces unnecessary herbicide use. The combination of multispectral sensing 
with foundational vision and language models oﬀers a scalable pathway toward 
deploying advanced perception systems in real-world agricultural settings. 
Acknowledgment. This research was funded by the European Union – NextGener-
ationEU and national resources through the Recovery and Resilience Facility (RRF) 
under the “Clusters of Research Excellence – CREs” Action of the National Recovery
and Resilience Plan “Greece 2.0” (project code: ΥΠ3TA-0559722).
References 
1. He, K., Zhang, X., Ren, S., Sun, J.: Deep residual learning for image recognition. In: 
Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition
(CVPR), pp. 770–778. IEEE (2016). https://doi.org/10.1109/CVPR.2016.90 
2. Oquab, M., et al.: DINOv2: learning robust visual features without supervision. 
Trans. Mach. Learn. Res. (2024). https://openreview.net/forum?id=a68SUt6zFt 
3. Sim´eoni, O., et al.: DINOv3. arXiv preprin t arXiv:2508.10104 (2025). https://doi. 
org/10.48550/arXiv.2508.10104
