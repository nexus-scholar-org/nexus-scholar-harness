---
workspace_id: SCI-001292
doi: 10.1109/tgrs.2026.3690653
title: 'RPD: Learning Efficient Crops and Weeds for Field Semantic Segmentation in
  Drone Images'
authors:
- family_name: Chen
  given_name: Fanghui
  orcid: null
- family_name: Yang
  given_name: Zhenchao
  orcid: null
- family_name: Ren
  given_name: Fengyuan
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:41.814033+00:00'
---

# RPD: Learning Efficient Crops and Weeds for Field Semantic Segmentation in Drone Images

IEEE TRANSACTIONS ON GEOSCIENCE AND REMOTE SENSING, VOL. 64, 2026 4408613

RPD: Learning Eﬃcient Crops and Weeds for Field

Semantic Segmentation in Drone Images

Fanghui Chen , Zhen Yang , and Fengyuan Ren

plays a pivotal role as it provides rich ﬁeld information. However, the task faces substantial challenges in complex ﬁeld environments, where crops and weeds exhibit similar visual characteristics during growth stages and often undergo mutual occlusion [2]. In particular, the natural illumination variations compound the complexity, especially for small weeds whose appearance becomes ambiguous under drone observation, severely hindering accurate crop-weed segmentation [3].


## Abstract—Eﬃcient crop-weed segmentation is crucial for the

perception needs of agricultural drones. However, natural illu-
mination variations signiﬁcantly alter the visual appearance
of plants and pose major challenges for accurate crop-weed
segmentation in ﬁeld environments, particularly for small weeds.
Existing deep learning (DL)-based methods mainly emphasize
high-level semantic representations and may struggle to capture
ﬁne-grained structural cues essential for distinguishing weeds
from crops. Meanwhile, these methods often demand high
computational resources, limiting their practicality in resource-
constrained ﬁeld environments. To this end, we propose an
eﬃcient crop-weed semantic segmentation method based on a
lightweight reparameterized pixel diﬀerence (RPD) block. The
RPD block integrates pixel diﬀerence convolutions (PDCs) in a
parallel multibranch structure to capture local structural diﬀer-
ences that are robust to illumination variations, while utilizing
reparameterization techniques to improve inference eﬃciency.
Built upon this block, RPD-Net is an end-to-end network with
strong modeling capacity and a lightweight structure for in-ﬁeld
crop-weed segmentation. Extensive experiments on the drone-
acquired public datasets validate the eﬀectiveness of our method.
Trained from scratch, our method achieves approximately 70
intersection-over-union (IoU) on the challenging weed segmenta-
tion task of the Phenobench dataset. Latency evaluations across
multiple hardware platforms show that RPD-Net runs 42 FPS
on an RTX 3090 and 7 FPS on a Jetson TX2. Compared to
state-of-the-art (SOTA) methods, RPD-Net oﬀers a better tradeoﬀ
between segmentation accuracy and computational eﬃciency.
Additional experiments on the CoFly dataset further validate
the generalization ability of RPD-Net. The code is available at
https://github.com/chenfh21/RPD-Net

Although traditional image-processing methods are sim- ple and eﬃcient for speciﬁc task-oriented scenarios, their reliance on handcrafted features limits their adaptability to crop-weed segmentation in complex ﬁeld environments com- pared with deep learning (DL)-based methods [2], [4], [5], [6], [7], [8], [9], [10], [11], [12]. DL-based methods have gained popularity due to their streamlined architectures, which seamlessly integrate feature extraction and fusion. How- ever, existing DL-based methods for crop-weed segmentation predominantly emphasize high-level semantic representations and often overlook ﬁne-grained structural cues, which are essential for crop-weed discrimination under varying illu- mination conditions in agricultural environments [3], [13]. Moreover, their computationally intensive nature poses chal- lenges for deployment on drone-based platforms for precision agriculture [14].

In this work, we design a lightweight reparameterized pixel diﬀerence (RPD) block. The block integrates pixel diﬀerence convolutions (PDCs) [15] to enhance robustness against illu- mination variations and utilizes reparameterization techniques [16], [17] to improve inference eﬃciency. Speciﬁcally, PDC is a set of gradient-based convolution operators that integrate gradient and intensity information to capture local struc- tural diﬀerences, which are resilient to natural illumination variations [18] in real-world environments. The RPD block organizes these operators in a parallel multibranch structure implemented with depthwise convolutions, followed by point- wise convolutions for information exchange. The block can merge these branches via structural reparameterization (SR) to accelerate inference. We further explore a variant of the RPD block, i.e., the D-RPD block, which incorporates dilated convolutions to enhance feature extraction while preserving the advantages of SR. Built upon the RPD blocks, we pro- pose RPD-Net, an encoder–decoder architecture designed for crop-weed segmentation in practical agricultural scenarios. This architecture adaptively learns the intrinsic characteristics of ﬁeld crops and weeds in an end-to-end manner, ensur- ing robustness under natural illumination variations. Then, RPD-Net is reparameterized into a lightweight form with a

Index Terms—Eﬃcient inference, ﬁne-grained identiﬁca- tion, lightweight network, semantic segmentation, weed-crop segmentation.

I. INTRODUCTION V

ISION-BASED perception systems are critical for drone- based ﬁeld management in precision agriculture. They enable timely monitoring and automated site-speciﬁc spraying, reducing labor and agrochemical costs through accurate crop- weed discrimination [1]. Pixel-level semantic segmentation

Received 16 December 2025; revised 11 March 2026; accepted 28 April 2026. Date of publication 5 May 2026; date of current version 13 May 2026. This work was supported in part by the National Natural Science Foundation of China (NSFC) under Grant 62132007 and Grant 62221003. (Corresponding authors: Fengyuan Ren; Zhen Yang.)

Fanghui Chen and Zhen Yang are with the School of Information Sci- ence and Engineering, Lanzhou University, Lanzhou 730000, China (e-mail: chenfh21@lzu.edu.cn; zhenyang@lzu.edu.cn).

Fengyuan Ren is with the School of Information Science and Engineering, Lanzhou University, Lanzhou 730000, China, and also with the Department of Computer Science and Technology, Tsinghua University, Beijing 100084, China (e-mail: renfy@tsinghua.edu.cn).

Digital Object Identiﬁer 10.1109/TGRS.2026.3690653

1558-0644 © 2026 IEEE. All rights reserved, including rights for text and data mining, and training of artiﬁcial intelligence and similar technologies. Personal use is permitted, but republication/redistribution requires IEEE permission.

See https://www.ieee.org/publications/rights/index.html for more information.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:31 UTC from IEEE Xplore.  Restrictions apply.

4408613 IEEE TRANSACTIONS ON GEOSCIENCE AND REMOTE SENSING, VOL. 64, 2026

2) We propose RPD-Net, an end-to-end segmentation net- work that adaptively learns to distinguish crops and weeds from drone imagery. Its lightweight design eﬀectively balances segmentation accuracy and compu- tational eﬃciency. 3) Trained entirely from scratch, RPD-Net can achieve eﬃcient crop-weed segmentation in drone imagery. Our extensive experiments demonstrate the accuracy and eﬃ- ciency of our designs in demanding agricultural vision scenarios.

II. RELATED WORKS

A. Crop-Weed Semantic Segmentation

Substantial works [2], [4], [5], [6], [7], [8], [9], [10], [11], [12] have been devoted to advancing crop-weed segmentation over the past years. Among these works, Bakhshipour and Jafari [5] combined multiple shape features to characterize individual plants. They then utilized support vector machines (SVMs) and artiﬁcial neural networks (ANNs) to detect weeds through these features. Parra et al. [7] tested up to twelve edge operators to identify the weeds in ornamental lawns and sports turf. They found that a sharpening (I) ﬁlter, combined with the minimum aggregation technique and a 10-pixel cell size, oﬀered the best performance. The results achieved with this methodology indicated a slight inconsis- tency between ornamental and sports turf. Although traditional image-processing methods achieved good results, they mainly rely on handcrafted features such as texture, color, and shape, which are designed for speciﬁc tasks based on strong prior knowledge. Additionally, these methods typically involve mul- tistage pipelines using conventional machine learning methods. As a result, they struggle to generalize eﬀectively to complex in-ﬁeld environments.

Fig. 1. Visualization analysis. (a) Input sample and its corresponding target semantic map. (b) CAM Image. (c) Guided Grad-CAM. (Top) Corresponds to the ﬁnal layer of ResNet-50, and (bottom) corresponds to the ﬁnal layer of the RPD-Net encoder. For the ResNet-50, the weeds in the bottom left corner of (b) and (c) completely disappear. The edge features of some crop leaves appear blurry in the top portion of (c). RPD-Net eﬀectively focuses on the weed on the left side of the example. Its attention [as shown in (b)] consistently falls on the target. The details at the bottom of (c) are more discernible than those at the top.

single path for eﬃcient inference. With Grad-CAM++ [19] visualization, we obtain an intuitive glimpse of the feature extraction behavior of RPD-Net and compare it with ResNet- 50 [20]. As shown in Fig. 1, RPD-Net exhibits stronger responses to small weeds and captures clearer edge features of crop leaves compared to ResNet-50. These visualization results indicate that RPD-Net is able to highlight ﬁne-grained structural cues in complex ﬁeld scenes, enabling more reliable identiﬁcation of small weeds commonly encountered in real ﬁeld environments.

Extensive experiments on drone-acquired public datasets validate the eﬀectiveness of our method. Trained entirely from scratch, our method achieves approximately 70 intersection- over-union (IoU) on the challenging weed segmentation task, outperforming other state-of-the-art (SOTA) methods on the Phenobench dataset [3]. In terms of inference eﬃciency, latency evaluations across multiple hardware platforms show that RPD-Net achieves 42 FPS on the RTX 3090 and 7 FPS on the Jetson TX2. RPD-Net oﬀers a better tradeoﬀ between segmentation accuracy and computational eﬃciency. Furthermore, experiments on the CoFly dataset [21] demon- strate the generalization ability of our method to diverse real-world agricultural scenarios. These results collectively demonstrate the potential of our approach for real-world agri- cultural applications, such as drone-based intelligent remote sensing, autonomous weeding robots, and precision herbicide spraying.

With the rapid development of DL technology, DL-based methods have been widely adopted to improve crop-weed segmentation precision and generalization. McCool et al. [4] proposed a three-stage approach involving pretrained model adaptation, model compression, and ensemble learning to balance eﬃciency and accuracy. Celikkan et al. [2] introduced a probabilistic segmentation framework that not only generated segmentation masks but also quantiﬁed uncertainty to distin- guish between weeds and crops in ﬁelds. Zhang et al. [9] improved Swin-Unet [22] for maize seedlings segmentation, relying heavily on Drop Block [23] to enhance performance. Roggiolani et al. [10] jointly segmented semantic classes, plant instances, and leaf instances using RGB images, leveraging the hierarchical structure of agricultural scenes and resolving spatial overlaps through postprocessing. Rai and Sun [11] pro- posed a one-stage segmentation architecture that integrates C3 and C3x [24] modules in the backbone. They also employed diverse data augmentation strategies. Lin et al. [12] designed a dual-branch FG-UNet. They utilize ﬁne feature-aware and con- textual feature fusion (CFF) modules to improve segmentation quality. Although these DL-based methods have demonstrated impressive results through adaptive feature extraction, their emphasis on high-level semantic features limits the discrim- ination ability of crops and weeds in complex real-world

The main contributions in this work are as follows.

1) We design a lightweight RPD block suitable for in- ﬁeld crop-weed segmentation, providing strong feature representation and eﬃcient inference. Additionally, we explore a variant of this block, the D-RPD block, which integrates dilated convolution to enhance feature extrac- tion while maintaining inference eﬃciency.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:31 UTC from IEEE Xplore.  Restrictions apply.

CHEN et al.: RPD: LEARNING EFFICIENT CROPS AND WEEDS 4408613

model with improved runtime eﬃciency [14], [17], [28], [29], [30]. Beneﬁting from the above reparameterization approaches, the RPD block is formulated as a reparameterizable multi- branch structure that enables enhanced feature representation during training and collapses into a simpliﬁed form for inference.

farmland, especially small weeds in drone imagery under natural illumination variations.

Diﬀerent from prior works on crop-weed semantic seg- mentation, RPD-Net, an end-to-end lightweight segmentation network that adaptively captures multidirectional ﬁne-grained features of locals to enhance robustness under natural illumi- nation variations. It aims to preserve intrinsic characteristics between crops and weeds while accounting for the eﬃciency of in-ﬁeld applications.

III. METHODOLOGY

In this section, we introduce our end-to-end lightweight segmentation network, RPD-Net. The network adopts an encoder–decoder architecture, where stacked RPD blocks serve as the core components for learning ﬁne-grained crop- weed features. We ﬁrst detail the RPD block in Section III-A, followed by the overall RPD-Net architecture in Section III-B.

B. Diverse Convolutional Operations

Convolutional operations in deep convolutional neural net- works (DCNNs) form the foundation of feature extraction. Various extensions [13], [15], [25], [26] have been proposed to enhance their representational capabilities. For instance, Gabor convolutions [26] apply Gabor ﬁlters to convolution ker- nels, improving robustness to orientation and scale variations. However, their ﬂexibility and ability to capture ﬁne-grained details under complex conditions remain limited [13], [18]. Based on central diﬀerence convolution (CDC) [13], PDC [15] incorporates both intensity and gradient information via learnable ﬁlters. It extends the sampling pattern beyond the central pixel to corners and “X”-junctions, thus better captur- ing intricate patterns in diverse environments [27]. In parallel, dilated convolutions [25] have been employed to expand the receptive ﬁeld for improved contextual aggregation.

A. RPD Block Architecture

Our RPD block, as shown in Fig. 2(a), primarily consists of depthwise convolutions followed by pointwise convolutions. In the depthwise part, we integrate diverse PDC operators [15] in parallel, including central (CPDC), angular (APDC), and radial (RPDC) [Fig. 2(b)]. PDC operators capture diverse gradient information by selecting pixel pairs from diﬀerent directions within local patches. For instance, the CPDC operator selects eight pixel pairs along the center direction within a 3 × 3 kernel. Instead of computing explicit pixel diﬀerences, the operator leverages weight reparameterization (WR) to convert them into learnable kernel-weight diﬀerences for eﬃcient computation. Then it can perform a dot product with the kernel to generate the corresponding feature map values. To clarify, the formulations of vanilla convolution and PDC are as follows:

Considering the strength of PDC, we integrate it into our RPD block to supplement the capacity of vanilla convolutions for adaptively capturing detailed patterns, which are crucial for crop-weed segmentation [7]. Furthermore, we explore the use of dilated convolutions within our RPD block design to enhance contextual understanding.

k2 X

C. Reparameterization

wi · pi (1)

F (pi, wi) =

Reparameterization is a technique that equivalently converts model parameters through algebraic transforms, oﬀering a tradeoﬀbetween training ﬂexibility and inference eﬃciency [14], [16], [17], [18], [28], [29], [30]. During training, it introduces overparameterization structures to enhance feature extraction. At inference, these structures are simpliﬁed for acceleration. Speciﬁcally, it can be classiﬁed as follows.

i=1

X

F (△pi, wi) =

wi · (pi −ˆpi) (2)

(pi, ˆpi)∈R

where pi and wi represent input in window of k × k and corresponding kernel weights, respectively. R = (p1, ˆp1), (p2, ˆp2), . . . , (pm, ˆpm) denotes the set of directional pixel pairs selected from the local patch, and m ≤k2. Further, the generalized PDC operators are deﬁned by a combination of vanilla convolution and PDC as follows:

1) Weight Reparameterization: This strategy reparameter- izes convolutional weights for eﬃcient training. For instance, PDC [18] replaces explicit pixel-diﬀerence calculations with learnable kernel-wise operations. After training, the learned weights can be remapped to a vanilla convolution without information loss, thus bridg- ing performance and eﬃciency. 2) Structural Reparameterization: This approach modiﬁes the network structure during training to facilitate struc- tural simpliﬁcation at inference. One line of work fuses a convolution–batch normalization (BN)–activation func- tion pipeline into a convolutional layer with ﬁxed parameters and activation function [16]. Another line of work merges multiple branches into a single-path structure during inference via equivalent transforma- tions that yield identical outputs, leading to a compact

X

F (pi, wi, θ) = θ ·

wi · (pi −ˆpi)

(pi, ˆpi)∈R

„ ƒ‚ … pixel diﬀerence convolution

k2 X

+ (1 −θ) ·

wi · pi

i=1

„ ƒ‚ … vanilla convolution

k2 X

X

wi · pi

+θ · (−ˆpi·)

=

wi

(3)

(pi, ˆpi)∈R

i=1

„ ƒ‚ … vanilla convolution

„ ƒ‚ … pixel diﬀerence term

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:31 UTC from IEEE Xplore.  Restrictions apply.

4408613 IEEE TRANSACTIONS ON GEOSCIENCE AND REMOTE SENSING, VOL. 64, 2026

Fig. 2. RPD block design. (a) RPD Block. The RPD block decouples the structure at training and inference time. (Left) With multibranches during training time, while (right) is at inference, where the branches are reparameterized. “DWConv” denotes depthwise convolution. “BN” denotes batch normalization. ReLU is used as an activation. (b) PDC convolution [15]. Pixel diﬀerences are converted into kernel weights to achieve eﬃcient learning. (c) D-RPDC. The D-RPDC is a radial PDC (RPDC) operator implemented using dilated convolution.

where hyperparameter θ ∈[0, 1] in (3) trades oﬀthe contri- bution between intensity-level and gradient-level information. The higher value of θ indicates more importance of gradient- based information. Unlike vanilla convolutions that rely solely on intensity patterns, PDC operators are inspired by classical gradient-based techniques, enabling direction-aware model- ing of local structures [18]. By integrating pixel diﬀerence operators from multiple directions, our method explicitly encodes local structural cues, leading to more consistent feature representations while adaptively enhancing robustness to illumination variations. This design inherits the strength of PDC by unifying handcrafted directional priors with the adaptive learning capability of modern convolutions. During training, the pixel diﬀerences are transformed into kernel- weight diﬀerences in the RPD block. After training, these convolutions become equivalent to vanilla convolutions. This WR ensures that the RPD block remains both learnable and eﬃcient. The parallel 3 × 3 and 1 × 1 depthwise convolution branches of the part primarily supplement intensity informa- tion. Subsequently, four parallel pointwise convolutions fuse the features extracted by the depthwise part, similar to the prior work [14]. Both parts include skip connections with BN [17] to ensure stable gradient propagation.

where d = 2 is the dilation factor and K defaults to 3. Thus, K′ = 5 matches the receptive ﬁeld of the original RPDC while enabling D-RPDC to be implemented using a 3 × 3 kernel. This implementation supports seamless reparameteri- zation into standard 3 × 3 convolutions, facilitating eﬃcient execution on hardware optimized for 3 × 3 operations during inference. Accordingly, the RPD block variant incorporating D-RPDC, termed D-RPD, exhibits enhanced feature extraction performance, as demonstrated in Section IV-B.

The structure of the RPD block is diﬀerent during training and inference, similar to previous works [14], [16], [17], [30]. For eﬃcient inference, the BN layers in each branch of the RPD block are ﬁrst fused into their preceding convolutional layers. These fused branches are then merged into a single path

0

1

k2 X

k2 X

M X

A =

ˆwm,i · pi + ˆbm

ˆwi · pi + ˆb (5)

F (pi, ˆwi) =

@

m=1

i=1

i=1

where ˆwm,i and ˆbm denote the equivalent kernel weights and bias of the mth branch after fusing the convolution and BN layers, and ˆwi together with ˆb represent the merged equiva- lent parameters. Through these equivalent transformations, we can obtain an eﬃcient architecture during inference without information loss.

Additionally, drawing inspiration from the dilated convolu- tion principle [25] and our receptive ﬁeld analysis of the RPDC operator, we propose using dilated convolution to implement the RPDC, resulting in a variant termed D-RPDC [as illus- trated in Fig. 2(c)]. Unlike the original RPDC, which models pixel diﬀerences solely among peripheral (outer-ring) positions while excluding the central pixel, the D-RPDC establishes direct diﬀerential dependencies between each outer pixel and the center. This design incorporates the central response into the gradient modeling process, thereby enabling more focused and informative feature extraction. The kernel size relationship between the D-RPDC convolution kernel (K′) and vanilla convolution kernel (K) can be deﬁned as follows:

B. RPD-Net

Fig. 3 illustrates our RPD-Net, which adopts an encoder–decoder architecture for end-to-end semantic segmen- tation [31], [32]. The initial stage comprises two stacked 3 × 3 convolutional layers, each followed by BN and an activation function. This stage helps eliminate low-level redundant infor- mation and reduces memory footprint in later stages [14], [32]. Subsequent stages are constructed with RPD blocks to enhance feature representation. Symmetric skip connections between the encoder and decoder promote multiscale feature fusion, enabling the network to better accommodate scale variations of crop-weed targets across diﬀerent growth stages.

K′ = K + (K −1) (d −1) (4)

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:31 UTC from IEEE Xplore.  Restrictions apply.

CHEN et al.: RPD: LEARNING EFFICIENT CROPS AND WEEDS 4408613

Fig. 3. RPD-Net architecture. It is mainly built upon the RPD blocks and establishes a lightweight encoder–decoder network. Further, the downsampler uses max-pooling, as well as upsampler uses bilinear interpolation. “XC * 2” indicates that the module has X channels and repeats twice.

well with our objective to provide a robust and eﬃcient method for drone-based, on-site applications in agriculture, especially considering that small weeds appear visually diminished due to the drone’s aerial perspective. The dataset oﬀers suﬃ- cient plant-level samples with interclass/intraclass diversity for training. We follow the oﬃcial data split provided by the dataset (details in Table I), where the training and validation samples originate from diﬀerent ﬁeld plots. This oﬃcial split reﬂects the natural spatial heterogeneity of agricultural ﬁelds and enables evaluation consistent with real-world data distri- butions. We train our models from scratch on the training set and evaluate them on the validation set, using this dataset as the primary benchmark due to its diversity and complexity.

TABLE I DETAILED DATASET INFORMATION. THE PHENOBENCH PROVIDES PIXEL-

LEVEL ANNOTATIONS FOR THREE SEMANTIC CLASSES: CROPS, WEEDS, AND SOIL. THE COFLY INCLUDES ANNOTATIONS FOR

THREE DISTINCT WEED TYPES AND BACKGROUND

To ensure eﬃciency, max-pooling is used for down-sampling, and bilinear interpolation is employed for upsampling, both of which contain no learnable parameters. All the activation functions adopt lightweight rectiﬁed linear units (ReLUs) [14]. During inference, RPD-Net leverages reparameterization to convert its multibranch training-time structure into a compact single-path architecture. It alternates between 3 × 3 depthwise convolutions and 1 × 1 pointwise convolutions with activa- tions, resulting in a lightweight and eﬃcient inference form. Correspondingly, we construct a variant of RPD-Net, termed D-RPD-Net, in which each RPD block is replaced by the proposed D-RPD block while keeping all other architectural conﬁgurations unchanged.

The CoFly dataset is a small-scale cotton ﬁeld weed dataset collected by a drone at a 5 m ﬂight height during a single planned mission. It has a GSD of approximately 1.4–1.6 mm/pixel and contains images of cotton at early growth stages. The dataset provides coarse-grained polygon annotations for three weed categories: Johnson grass, purslane, and ﬁeld bindweed (shown in Table I). We evaluated the generalization of our method on this dataset.

2) Performance Metrics: To evaluate the performance of semantic segmentation, we adopt the following metrics: IoU, precision, F1-score (F1), recall, and accuracy. Further, we report the averaged values of these metrics. Among them, mean IoU (mIoU) is the main criterion, widely used in semantic segmentation tasks.

IV. EXPERIMENTS

3) Implementation Details: Our implementation adopts the Pytorch [34] library. To ensure suﬃcient training, we set a maximum of 4096 epochs with a batch size of 4. The weighted cross-entropy loss is adopted due to the pervasive class imbalance in agricultural images, assigning weights inversely proportional to pixel-level class frequencies. We use Adam optimizer [35] with weight decay set to 2 · 10−4. At the initial 16 epochs, we linearly increase the learning rate to 1 · 10−4 and subsequently apply a polynomial learning rate decay (1 −e/4096)3, where e is the current epoch. For data augmentation, we use color space augmentations and geometric transformations, speciﬁcally including random adjustments of brightness (range 0.6–1.4), contrast (range

A. Datasets and Implementation

1) Datasets: We evaluate our method on two public datasets: Phenobench [3] and CoFly [21]. They consist of RGB imagery, which is cost-eﬀective and widely adopted in drone- based practice [3], [33], making them appropriate benchmarks for crop-weed segmentation. The Phenobench dataset com- prises sugarbeet images captured by a drone equipped with a high-resolution camera at a ﬂight height of approximately 21 m, corresponding to a ground sampling distance (GSD) of 1 mm/pixel. It was collected on multiple dates across diﬀer- ent growth stages, encompassing diverse illumination (sunny versus overcast) and phenotype changes. As a result, it aligns

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:31 UTC from IEEE Xplore.  Restrictions apply.

4408613 IEEE TRANSACTIONS ON GEOSCIENCE AND REMOTE SENSING, VOL. 64, 2026

TABLE II

ABLATION STUDY OF RPD BLOCK DESIGNS. “/” SPLITS THE RESULTS OF

THE TRAINING AND VALIDATION SET. THE LAST COLUMN REPORTS

THE PARAMETER QUANTITY OF THE CORRESPONDING ARCHITEC-

TURE. “V,” “C,” AND “A” DENOTE VANILLA CONVOLUTION,

CPDC, AND APDC, RESPECTIVELY. PARAMS DENOTES THE

NUMBER OF PARAMETERS (M)

Fig. 4. Eﬀect of θ in RPD-Net. Larger θ values increase the contribution of gradient-based information.

block exist by default. Subsequently, we incorporate PDC operators to assess their contribution. The details and results are summarized in Table II.

Compared to the baseline, the network with simpliﬁed RPD blocks ([“VVV”]) achieves comparable overall seg- mentation performance while using only 17.2% of the parameters (0.189M versus 1.10M). This result indicates that the parallel structure eﬀectively reduces parameter count but remains insuﬃcient for crop-weed segmentation, particularly for weeds (IoU: 71.56 versus 68.90). Next, we examine the contribution of individual PDC operators by replacing the vanilla depthwise convolution in the simpliﬁed blocks with CPDC, APDC, and RPDC, respectively. Among them, the RPDC operator ([’VVR’]) yields the highest performance (88.34 mIoU). We then progressively incorporate multiple PDC operators to recover the complete RPD conﬁguration. Overall, the performance improves, while the gains from individual PDC operators are not strictly monotonic. The com- plete RPD ([“CAR”]) conﬁguration delivers the best training performance (90.77 mIoU), whereas validation performance is slightly inferior among variants. This discrepancy suggests that the PDC branches of RPD blocks enhance the network’s ability to ﬁne-grained feature modeling but also amplify sen- sitivity to local variations, weakening generalization.

0.6–1.4), hue (±0.0125), and saturation (range 0.8–1.2), as well as random horizontal and vertical ﬂipping (each with 50% probability), and random scaling (range 1.0–1.1). We feed randomly cropped patches of resized 768 pixel × 768 pixel from the input image to the network during training, while evaluation is performed on the original image resolution of 1024 pixel × 1024 pixel. All the above settings are kept fully consistent with the Phenobench semantic segmentation task1 to enable a fair evaluation of our methods. Addition- ally, we incorporate an early stopping mechanism after three consecutive validations with a loss ≤0.1, validating every 200 epochs. These settings are adopted as a uniﬁed training protocol to ensure that all models are suﬃciently trained under consistent conditions. Checkpoints of models achieving the highest validation mIoU during training are saved and used as the ﬁnal evaluation models. We implement all methods on a computer equipped with two NVIDIA GeForce RTX 3090 GPUs, while conducting evaluations on a single GPU. Unless otherwise speciﬁed, all models are trained and evaluated under the same experimental settings described above.

As deﬁned in (3), the hyperparameter θ governs the con- tribution of local gradient information in the PDC operators. In our default setting, θ is ﬁxed to 1 across all RPD blocks, maximizing the contribution of gradient-based cues. To assess its eﬀect on RPD-Net, we sweep θ over the range [0, 1] with a step size of 0.1. As shown in Fig. 4, RPD-Net consistently outperforms the vanilla convolution baseline (θ = 0). The model achieves its optimal performance at θ = 0.5 (mIoU: 88.89). Beyond this point, the performance exhibits a gradual decline, yet remains higher than that at θ = 0. These results indicate that introducing gradient information (θ > 0) is generally beneﬁcial for crop-weed segmentation. However, larger θ values increase the model’s sensitivity to ﬁne-grained details, leading to weakened generalization.

B. Ablation Study

We conduct all ablations on the Phenobench validation dataset to evaluate the eﬀectiveness of our method.

1) Parallel Structure and Fine-Grained: In this set of experiments, we evaluate the contribution of the parallel and ﬁne-grained diﬀerence operators in the RPD block. For reproducibility, a ﬁxed random seed is used for all ablation experiments. We begin by constructing a plain baseline net- work, where all RPD blocks in RPD-Net are replaced with vanilla convolutions. To examine the eﬀect of the parallel structure, we introduce simpliﬁed RPD blocks. Speciﬁcally, in these blocks, the parallel branches within the depthwise part that originally host PDC operators are replaced with vanilla depthwise convolutions (denoted as [“VVV”] in Table II). Note that the 3 × 3 and 1 × 1 depthwise branches of the

Additionally, we assess the eﬀectiveness of D-RPD block (Table II: D-RPD versus RPD). The D-RPD variant delivers a notable improvement over the original RPD conﬁguration, with gains of 0.55 mIoU and 1.4 IoU on the weed class. This performance gain can be attributed to the enhanced spatial correlation introduced by directly modeling diﬀerential

1The oﬃcial implementation is available at: https://github.com/PRBonn/ phenobench-baselines/tree/main/semantic segmentation

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:31 UTC from IEEE Xplore.  Restrictions apply.

CHEN et al.: RPD: LEARNING EFFICIENT CROPS AND WEEDS 4408613

TABLE III

REPARAMETERIZATION COMPARISON. SPECIFICALLY, WE CONDUCT MODELS IN MULTIPLATFORMS TO EVALUATE THE LATENCY. “REP” INDICATES

REPARAMETERIZATION. IN PARTICULAR, TENSORRT ON JETSON DOES NOT SUPPORT THE BILINEAR INTERPOLATION AS UTILIZED IN RPD-

NET. THIS LIMITATION MAY ACCOUNT FOR THE SLIGHTLY SLOWER PERFORMANCE OF RPD-NET COMPARED TO ERFNET IN THE FINAL

EXPERIMENTAL RESULTS

dependencies between each outer pixel and the central position within the D-RPD operator.

TABLE IV

CONTROLLED STUDY ON PHOTOMETRIC AUGMENTATION

2) Reparameterization: We evaluate the inference time before and after reparameterization on the Phenobench val- idation set across input resolutions of 512 × 512, 768 × 768, and 1024 × 1024, to compare with other methods. Table III reports the measured inference time (forward pass) on diﬀerent hardware environments, including a single Tegra TX2 (Jetson TX2), a single NVIDIA GeForce RTX 3090, and a CPU.

For all evaluated methods, we conduct ﬁve inference runs and report the average for reliability. Since the reparame- terization is an oﬄine algebraic transformation, it does not cause performance degradation. After reparameterization, the parameter counts of RPD-Net decrease from 0.189M to 0.14M, and the MACs reduce from 13.45G to 4.71G at a 768 × 768 input resolution. This reduction in model complexity lowers the computational cost and enables faster inference across all tested platforms, yielding better or comparable inference performance compared with the baselines [36], [37] in Phe- nobench. The 42.05 frames/s on RTX 3090 and the 7.0 fps on Jetson provide a promising reference for eﬃcient inference in agricultural applications. The proposed model achieves 42.05 FPS on RTX 3090 and 7.0 FPS on Jetson TX2, demon- strating its computational eﬃciency on both high-performance GPUs and embedded platforms. The results of our approach are also better than those of others on CPU. It is noted that we do not explore additional optimization on Jetson for acceleration. Additionally, we analyze the power consumption and operating temperature on the Jetson TX2 platform in the Appendix.

TABLE V

COMPARISON RESULTS OF SEMANTIC SEGMENTATION ON THE PHE- NOBENCH VALIDATION SET. ACCURACY IS REPORTED USING IOU,

AND EFFICIENCY IS EVALUATED USING PARAMS (NUMBER OF PARAMETERS), MACS (MULTIPLY-ACCUMULATE OPERA-

TIONS), AND PER-FRAME INFERENCE LATENCY

removed, both models exhibit slight performance degradation in mIoU. The baseline decreases by 1.38 points, whereas RPD-Net drops by 0.48 points. The degradation of weed is more pronounced for the baseline compared with RPD-Net (−4.02 versus −1.21). These results indicate that the per- formance of RPD-Net is less dependent on photometric augmentation and beneﬁts more from the modeling capacity of the RPD block.

3) Photometric Augmentation Controlled Study: We con- duct a controlled ablation study to isolate the eﬀect of photometric augmentation. Speciﬁcally, we compare RPD- Net and the baseline network by removing all photometric augmentations (i.e., color adjustments including brightness, contrast, hue, and saturation), while keeping all other training settings identical.

C. Comparison With the SOTA Methods

1) Quantitative Results: Table V presents the compar- ison results of RPD-Net with other SOTA methods on


> **Table IV reports the segmentation results with and with-**

> out photometric augmentations. When the augmentations are

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:31 UTC from IEEE Xplore.  Restrictions apply.

4408613 IEEE TRANSACTIONS ON GEOSCIENCE AND REMOTE SENSING, VOL. 64, 2026

TABLE VI

COMPREHENSIVE PERFORMANCE METRICS OF DIFFERENT MODELS ON THE PHENOBENCH VALIDATION SET. “MP,” “MR,” AND “MF1” DENOTE MACRO

PRECISION, RECALL, AND F1-SCORE, AND “MACC” DENOTES MICRO ACCURACY. “P,” “R.” AND “F1” REFER TO PER-CLASS PRECISION,

RECALL, AND F1-SCORE

TABLE VII


## RESULTS ON THE PHENOBENCH VALIDATION SET, GROUPED BY ILLUMI-

NATION CONDITIONS (CORRESPONDING TO THE COLLECTED DATES)

Fig. 5. Confusion matrices. (a) Confusion matrices on the Phenobench validation set. (Top left) to (Bottom right) ERFNet, DeepLabV3+, SegNeXt- T, Segformer-B0, RPD-Net, and D-RPD-Net. Confusion matrices for the three illumination condition subsets. Rows correspond to true labels, while columns correspond to predicted classes. (b) Confusion matrix on the Sunny I subset. (c) Confusion matrix on the Sunny II subset, respectively. (d) Confusion matrix on the overcast subset.

the Phenobench [3] validation set. Among these methods, DeeplabV3 + [37] adopts ResNet-50 [20] as the backbone to ensure strong feature extraction. ERFNet [36] is a real- time semantic segmentation network that employs residual connections and asymmetric convolutions to balance accu- racy and computational eﬃciency. The two methods are provided by Phenobench. Bayesian Deeplabv3 [2] integrates uncertainty modeling to improve robustness for crop-weed segmentation. Additionally, Transformer-based architectures have been widely studied in semantic segmentation [40] and have also been applied to agricultural crop-weed segmentation [41]. We therefore include the lightweight SegFormer-B0 [38] and EﬃcientViT-B0 [39] as representative baselines for comparison. SegNeXt-T [32] is a recent lightweight attention- based semantic segmentation network, and FG-UNet [12] is a

dual-branch segmentation network specially designed for crop- weed discrimination using the Phenobench dataset. Despite their respective strengths, these methods often fail to balance accuracy and eﬃciency for crop-weed segmentation in drone imagery. In contrast, RPD-Net achieves a better tradeoﬀ.

Speciﬁcally, we run all networks ﬁve times with diﬀerent random seeds and report the mean and standard deviation. RPD-Net achieves an mIoU of 87.47(±0.75), higher than the lightweight ERFNet (85.19) while using only 38% of

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:31 UTC from IEEE Xplore.  Restrictions apply.

CHEN et al.: RPD: LEARNING EFFICIENT CROPS AND WEEDS 4408613

Fig. 6. Qualitative results on the Phenobench validation set. Colors denote semantic classes, with crop pixels in green and weed pixels in red. Colored boxes highlight representative cases: white indicates segmentation errors, blue indicates missed detections, and yellow denotes correct segmentation. These examples cover diﬀerent illumination conditions: rows 1–2 correspond to Sunny I, rows 3–4 to Sunny II, and row 5 to Overcast. (a) Input. (b) Ground truth. (c) Baseline. (d) RPD-Net (e) D-RPD-Net. (f) SegNeXt-T. (g) SegFormer-B0.

its parameters and fewer MACs (13.45G versus 33.05G). Compared to other lightweight baselines such as ERFNet and EﬃcientViT-B0, RPD-Net consistently delivers higher seg- mentation accuracy. To ensure these improvements are not due to random variation, we also conduct a paired t-test over the ﬁve independent runs. The result (t = 7.13, p = 0.0021 < 0.05) conﬁrms a statistically signiﬁcant improvement of RPD-Net over SegFormer-B0, with similar signiﬁcance observed for other lightweight baselines (SegNeXt-T [32], EﬃcientVit-B0 [39], and FG-UNet [12]). The variants RPD-Net (θ = 0.5) and D-RPD-Net reach mIoU of 88.26(±0.77) and 87.54(±0.67), respectively. Both variants achieve above 70 IoU for the weed class. In terms of eﬃciency, our method attains a latency of 23.8 ms, oﬀering a better tradeoﬀbetween accuracy and eﬃciency compared with other methods. Further, Table VI provides additional metrics for a comprehensive assessment. Compared with other methods, RPD-Net and its variant maintain superior performance advantages. This performance improvement is particularly evident for the challenging weed class, which is small and visually similar to crops.

Furthermore, we assess performance under diverse illumi- nation conditions. The Phenobench images were collected on diﬀerent days under varying weather conditions, resulting in diﬀerent natural illumination conditions. Table VII presents the results obtained by grouping the Phenobench validation set by acquisition date, corresponding to Sunny I, Sunny II, and Overcast illumination conditions. The two sunny subsets exhibit perceptible diﬀerences in illumination intensity, as shown in the ﬁrst column of Fig. 6. Our RPD-Net and its variant D-RPD-Net achieve mIoU values above 80 across all subsets, indicating strong robustness to illumination variation. Under Sunny I, overall performance is lower than in the other two cases. This subset corresponds to the early growth stage, where crops and weeds appear small and visually similar against a darker soil background (compared to the Sunny II). This condition reduces the visual clarity of plants, making weed identiﬁcation particularly diﬃcult. Under Sunny II, all methods exhibit better mIoU and weed IoU than in Sunny I. This condition is characterized by stronger illumina- tion and larger plant size due to later collection. Our method

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:31 UTC from IEEE Xplore.  Restrictions apply.

4408613 IEEE TRANSACTIONS ON GEOSCIENCE AND REMOTE SENSING, VOL. 64, 2026

consistently outperforms other methods in both sunny cases. The Overcast condition provides clear plant-background con- trast, facilitating accurate target identiﬁcation. All methods exceed 86 mIoU, with more than 68 IoU for weeds under this condition. Our method performs slightly worse than ERFNet and DeepLabV3 + for crops and soil, yet achieves markedly higher IoU for weeds (RPD-Net versus SegFormer- B0: 76.53 versus 68.01). An interesting observation is that our method obtains superior weed IoU across all subsets, while the performance gap between our method and the weakest baseline gradually narrows (20.23 → 14.14 → 8.52). The largest margin is observed under Sunny I, where there is strong sunlight and smaller weeds compared to the other subsets. RPD-Net and its variant achieve 53.11 IoU and 50.94 IoU for the weed class, respectively. These results demonstrate the eﬀectiveness of our method in distinguishing small weeds under challenging illumination conditions.

TABLE VIII

EXTENSION OF THE COFLY DATASET. THE PATCH-BASED STRAT- EGY YIELDS 787 PATCHES, AND DATA AUGMENTATION FURTHER

INCREASES THE TRAINING SAMPLES TO 1878

D. Generalization on CoFly Dataset

We further explore the generalization capacity of our method on the CoFly dataset, which diﬀers signiﬁcantly from Phenobench in terms of scale, scene complexity, ﬂight altitude, GSD, and annotation granularity. Due to the limited number of samples in the dataset, we adopt a patch-based generation strategy to expand the training samples. Specif- ically, the original dataset of 201 images is randomly split into training and validation sets with a ratio of 8:2 using a ﬁxed random seed, resulting in 161 training images and 40 validation images. Fixed-size patches (i.e., 256 × 256) are then cropped independently within each set [42], [43]. To avoid ineﬀective optimization caused by nearly empty patches, a threshold-based selection strategy discards patches containing more than 97% background pixels, thereby retaining patches with valid target regions. The training set is further augmented with random ﬂipping (probability 0.5), 90◦rotations, and grid distortion [44], resulting in 1878 training samples (as detailed in Table VIII). These extension operations in the generation strategy follow the CoFly data preparation used in [45], providing a reliable data foundation for subsequent evaluation.

Fig. 5 plots the confusion matrices on the Phenobench validation set and the three illumination condition subsets. As shown in Fig. 5(a), RPD-Net and its variant exhibit consistent crop-weed discrimination capability, particularly for the weed class, where they show an observable advantage over other baselines. We further assess the impact of illumi- nation conditions, comparing the better-performing RPD-Net with SegFormer-B0, a strong baseline. As illustrated in Fig. 5(b)–(d), RPD-Net consistently achieves high true positive rates across soil, crop, and weed, demonstrating stable per- formance under all three illumination conditions. In the more challenging Sunny I subset, where there is strong sunlight and small weeds, RPD-Net achieves 0.9973 for soil, 0.9803 for crop, and 0.8468 for weed, accompanied by notably lower interclass confusion than SegFormer-B0. These results collectively conﬁrm that RPD-Net provides eﬀective crop- weed discrimination and maintains robust performance under diverse illumination conditions.

To comprehensively evaluate the discriminative capacity of our method and ensure a fair comparison, we follow the evaluation protocol described in [45] and conduct two segmentation settings: one for binary segmentation (weeds versus background) and the other for multiclass segmentation (three weed species versus background). We compare our method against the best-performing models [20], [31], [46], [47], [48] mentioned in each setting from [45]. For our method, we run ﬁve trials and report the mean and standard deviation. The quantitative results are reported in Tables IX and X, with all other implementation settings kept consistent with those used in the Phenobench experiments.

2) Qualitative Analysis: To better reveal segmentation per- formance on crop-weed targets, we present the qualitative results of the diﬀerent methods in Fig. 6. The examples cover diﬀerent illumination conditions and growth stages on the Phenobench validation set. Class predictions are color- coded: crops in green and weeds in red. As the results suggest, our RPD-Net eﬀectively segments crops and weeds at the pixel level, clearly delineating individual plants without producing blob-like artifacts. It maintains high segmentation accuracy even when the targets are smaller and visually subtle. For instance, in the ﬁrst two rows, where crop-weed targets are smaller, RPD-Net correctly discriminates crops and weeds. While most methods exhibit diﬀerent degrees of missed detections under this strong illumination condition, RPD-Net remains more precise in capturing weed contours. Additionally, we observe that D-RPD-Net yields improved results compared to RPD-Net in certain ﬁne-grained regions. This improvement further validates the design of the D-RPDC operator, which directly establishes tighter diﬀerence depen- dencies between the central pixel and spatially distant ones. These qualitative results further corroborate the eﬀectiveness of our method in focusing on intrinsic features of crop-weed targets.

In the binary setting, RPD-Net and D-RPD-Net both achieve competitive segmentation performance while main- taining extremely compact model complexity, with only 0.189M parameters and 0.52G MACs. Notably, D-RPD-Net attains a higher weed IoU (43.03) than RPD-Net (42.06) and improves the overall mIoU from 59.89 to 60.84, suggesting the beneﬁt of the proposed D-RPDC operator. Compared to SegNet [46] with an EﬃcientNetB0 [48] backbone, both RPD- Net and D-RPD-Net achieve superior weed IoU (42.06 and 43.03 versus 37.48) with only 1.86% of the parameters. A similar trend is observed when compared with SegNeXt-T and SegFormer-B0. In the multiclass setting, RPD-Net achieves strong overall performance while obtaining the best IoU

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:31 UTC from IEEE Xplore.  Restrictions apply.

CHEN et al.: RPD: LEARNING EFFICIENT CROPS AND WEEDS 4408613

TABLE IX

BINARY RESULTS ON THE COFLY DATASET. SEGNET VARIANTS USE DENSENET121 AND EFFICIENTNETB0 AS BACKBONES, RESPECTIVELY

TABLE X

MULTICLASS RESULTS ON THE COFLY DATASET. UNET VARIANTS USE EFFICIENTNETB0 AND RESNET50 AS BACKBONES, RESPECTIVELY

that our method can eﬀectively distinguish between weed and nonweed regions compared with competitive methods such as SegNeXt-T and SegFormer-B0. In the top two rows in Fig. 7, our proposed RPD-Net tends to exclude pixels that do not belong to weed regions, while other methods fail to do so. For multiclass segmentation, the results further indicate that our method can identify diﬀerent weed categories. In the bottom two rows of Fig. 7, RPD-Net remains robust even under coarse polygon annotations. For instance, in the third row of the second column in Fig. 7, RPD-Net successfully identiﬁes ﬁeld bindweed growing on wet soil. In the fourth row of the same column, RPD-Net correctly detects purslane, whereas the other methods could not do so. These observations suggest good class separation even under inaccurate or ambiguous label- ing. Such robustness under coarse annotations may provide useful insights for future eﬀorts in semisupervised or weakly supervised learning, especially in agricultural scenarios where high-quality annotations are often costly or diﬃcult to obtain.

Fig. 7. Qualitative results on the CoFly dataset. (Top) Two rows show binary segmentation results, where weed regions are highlighted in yellow. (Bottom) Two rows present multiclass segmentation results, where Johnson grass, purslane, and ﬁeld bindweed are highlighted in red, blue, and yellow, respectively. (a) Input. (b) Ground truth. (c) RPD-Net. (d) SegNeXt-T. (e) SegFormer-B0.

E. Limitations and Future Work

Although our method achieves a favorable tradeoﬀbetween segmentation accuracy and inference latency on the employed datasets, several practical factors may aﬀect its transferabil- ity to real-world applications. First, available drone-based crop-weed datasets are scarce and cover a limited diversity of weed species, leaving few large-scale benchmarks for comprehensive evaluation across diverse farmland scenarios. Second, illumination conditions are restricted. The datasets mainly capture interday illumination variations, while intraday changes, such as shifts in sun position and color temperature from morning to evening, are not represented. Such variations can alter plant appearance and potentially inﬂuence model generalization. Third, ﬂight altitude and camera geometry of the drone can inﬂuence image quality, which in turn impacts segmentation performance.

scores on purslane (2.17). D-RPD-Net maintains competitive performance across weed categories, achieving IoU scores of 21.67, 1.67, and 34.21 on Johnson grass, purslane, and ﬁeld bindweed, respectively. The relatively low IoU on purslane across all models is likely due to its limited presence and coarse-grained annotations in the dataset. Compared with baseline models such as UNet [31] with an EﬃcientNetB0 [48] backbone and SegFormer-B0, the proposed method achieves competitive or superior segmentation performance while using substantially fewer parameters, suggesting a more balanced performance across categories under tight model constraints.

In future work, several directions merit further investigation. These include evaluations on datasets that cover a wider

Similarly, we visualize the qualitative results on the CoFly dataset in Fig. 7. The binary segmentation results indicate

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:31 UTC from IEEE Xplore.  Restrictions apply.

4408613 IEEE TRANSACTIONS ON GEOSCIENCE AND REMOTE SENSING, VOL. 64, 2026

[5] A. Bakhshipour and A. Jafari, “Evaluation of support vector machine and artiﬁcial neural networks in weed detection using shape features,” Comput. Electron. Agricult., vol. 145, pp. 153–160, Mar. 2018. [6] A. Milioto, P. Lottes, and C. Stachniss, “Real-time semantic segmen- tation of crop and weed for precision agriculture robots leveraging background knowledge in CNNs,” in Proc. IEEE Int. Conf. Robot. Autom. (ICRA), May 2018, pp. 2229–2235. [7] L. Parra, J. Marin, S. Yousﬁ, G. Rinc´on, P. V. Mauri, and J. Lloret, “Edge detection for weed recognition in lawns,” Comput. Electron. Agricult., vol. 176, Sep. 2020, Art. no. 105684. [8] V. N. T. Le, S. Ahderom, and K. Alameh, “Performances of the LBP based algorithm over CNN models for detecting crops and weeds with similar morphologies,” Sensors, vol. 20, no. 8, p. 2193, Apr. 2020. [9] J. Zhang, J. Gong, Y. Zhang, K. Mostafa, and G. Yuan, “Weed iden- tiﬁcation in maize ﬁelds based on improved Swin-UNet,” Agronomy, vol. 13, no. 7, p. 1846, Jul. 2023. [10] G. Roggiolani, M. Sodano, T. Guadagnino, F. Magistri, J. Behley, and

TABLE XI

ANALYSIS OF POWER CONSUMPTION AND TEMPERATURE METRICS FOR

MODELS ON THE JETSON TX2 PLATFORM. POWER CONSUMPTION

IS EXPRESSED IN WATTS PER FRAME (W/FRAME), DEFINED AS

THE AVERAGE DEVICE POWER MEASUREMENT DIVIDED BY

THE ACHIEVED FRAME RATE. TEMPERATURE IS REPORTED

IN C BASED ON THE DEVICE’S ONBOARD THERMAL

SENSORS

C. Stachniss, “Hierarchical approach for joint semantic, plant instance, and leaf instance segmentation in the agricultural domain,” in Proc. IEEE Int. Conf. Robot. Autom. (ICRA), May 2023, pp. 9601–9607. [11] N. Rai and X. Sun, “WeedVision: A single-stage deep learning architec-

variety of crop ﬁelds, incorporating more diverse illumination conditions, and varied drone ﬂight setups.

ture to perform weed detection and segmentation using drone-acquired images,” Comput. Electron. Agricult., vol. 219, Apr. 2024, Art. no. 108792. [12] J. Lin et al., “FG-UNet: Fine-grained feature-guided unet for segmen-

V. CONCLUSION

In this work, we design a lightweight RPD block that balances accuracy and eﬃciency for crop-weed segmentation in drone imagery. The block integrates PDC operators to enhance feature representation and utilizes reparameterization techniques to improve inference eﬃciency. Built upon this block, RPD-Net serves as an eﬃcient semantic segmentation network for crop-weed discrimination. Extensive evaluations on two public drone-acquired datasets demonstrate the eﬀec- tiveness of our method. The results show our method achieves superior performance in both segmentation accuracy and infer- ence eﬃciency.

tation of weeds and crops in uav images,” Pest Manage. Sci., vol. 81, no. 2, pp. 856–866, 2024. [13] Z. Yu et al., “Searching central diﬀerence convolutional networks for

face anti-spooﬁng,” in Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR), Jun. 2020, pp. 5295–5305. [14] P. K. A. Vasu, J. Gabriel, J. Zhu, O. Tuzel, and A. Ranjan, “Mobileone:

An improved one millisecond mobile backbone,” in Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit., Jun. 2023, pp. 7907–7917. [15] Z. Su et al., “Pixel diﬀerence networks for eﬃcient edge detection,”

in Proc. IEEE/CVF Int. Conf. Comput. Vis. (ICCV), Oct. 2021, pp. 5097–5107. [16] S. Zagoruyko and N. Komodakis, “DiracNets: Training very deep neural

networks without skip-connections,” 2017, arXiv:1706.00388. [17] X. Ding, X. Zhang, N. Ma, J. Han, G. Ding, and J. Sun, “RepVGG:

Making VGG-style ConvNets great again,” in Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR), Jun. 2021, pp. 13733–13742. [18] Z. Su et al., “Lightweight pixel diﬀerence networks for eﬃcient

ACKNOWLEDGMENT

The authors would like to express their appreciation to the creators of the Phenobench and CoFly datasets.

visual representation learning,” IEEE Trans. Pattern Anal. Mach. Intell., vol. 45, no. 12, pp. 14956–14974, Dec. 2023. [19] A. Chattopadhay, A. Sarkar, P. Howlader, and V. N. Balasubramanian,

APPENDIX SUPPLEMENTARY POWER AND THERMAL PROFILING

“Grad-CAM++: Generalized gradient-based visual explanations for deep convolutional networks,” in Proc. IEEE Winter Conf. Appl. Comput. Vis. (WACV), Mar. 2018, pp. 839–847. [20] K. He, X. Zhang, S. Ren, and J. Sun, “Deep residual learning for

Here, we provide measurements of power consumption and temperature behavior to provide additional insight into the energy behavior of the proposed lightweight model, with the Jetson TX2 serving as the test platform. All values are averaged over ﬁve independent runs. As summarized in Table XI, RPD-Net exhibits slightly lower power usage and stable thermal behavior relative to other baselines. After repa- rameterization, power consumption shows a modest decrease, further supporting the eﬃciency of the RPD block design.

image recognition,” in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), Jun. 2016, pp. 770–778. [21] M. Krestenitis et al., “CoFly-WeedDB: A UAV image dataset for weed

detection and species identiﬁcation,” Data Brief, vol. 45, Dec. 2022, Art. no. 108575. [22] H. Cao et al., “Swin-UNet: UNet-like pure transformer for medical

image segmentation,” in Proc. Eur. Conf. Comput. Vis. Cham, Switzer- land: Springer, 2022, pp. 205–218. [23] G. Ghiasi, T.-Y. Lin, and Q. V. Le, “DropBlock: A regularization method

for convolutional networks,” in Proc. Adv. Neural Inf. Process. Syst., vol. 31, 2018, pp. 10727–10737. [24] H. Park, Y. Yoo, G. Seo, D. Han, S. Yun, and N. Kwak, “C3:

Concentrated-comprehensive convolution and its application to semantic segmentation,” 2018, arXiv:1812.04920. [25] F. Yu and V. Koltun, “Multi-scale context aggregation by dilated


## REFERENCES

[1] M. T. Linaza et al., “Data-driven artiﬁcial intelligence applications for sustainable precision agriculture,” Agronomy, vol. 11, no. 6, p. 1227, Jun. 2021. [2] E. Celikkan, M. Saberioon, M. Herold, and N. Klein, “Semantic segmen- tation of crops and weeds with probabilistic modeling and uncertainty quantiﬁcation,” in Proc. IEEE/CVF Int. Conf. Comput. Vis. Workshops (ICCVW), Oct. 2023, pp. 582–592. [3] J. Weyler et al., “PhenoBench: A large dataset and benchmarks for semantic image interpretation in the agricultural domain,” IEEE Trans. Pattern Anal. Mach. Intell., vol. 46, no. 12, pp. 9583–9594, Dec. 2024. [4] C. McCool, T. Perez, and B. Upcroft, “Mixtures of lightweight deep convolutional neural networks: Applied to agricultural robotics,” IEEE Robot. Autom. Lett., vol. 2, no. 3, pp. 1344–1351, Jul. 2017.

convolutions,” in Proc. Int. Conf. Learn. Represent., May 2015. [26] S. Luan, C. Chen, B. Zhang, J. Han, and J. Liu, “Gabor convolutional

networks,” IEEE Trans. Image Process., vol. 27, no. 9, pp. 4357–4366, Sep. 2018. [27] D. R. Martin, C. C. Fowlkes, and J. Malik, “Learning to detect natural

image boundaries using local brightness, color, and texture cues,” IEEE Trans. Pattern Anal. Mach. Intell., vol. 26, no. 5, pp. 530–549, May 2004. [28] X. Ding, Y. Guo, G. Ding, and J. Han, “ACNet: Strengthening

the kernel skeletons for powerful CNN via asymmetric convolution blocks,” in Proc. IEEE/CVF Int. Conf. Comput. Vis. (ICCV), Oct. 2019, pp. 1911–1920.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:31 UTC from IEEE Xplore.  Restrictions apply.

CHEN et al.: RPD: LEARNING EFFICIENT CROPS AND WEEDS 4408613

Fanghui Chen received the M.S. degree from Lanzhou Jiaotong University, Lanzhou, China, in 2017. She is currently pursuing the Ph.D. degree with the School of Information Science and Engi- neering, Lanzhou University, Lanzhou.

[29] S. Guo, J. M. Alvarez, and M. Salzmann, “ExpandNets: Linear over-

parameterization to train compact convolutional networks,” in Proc. NIPS, 2020, pp. 1298–1310. [30] X. Ding, X. Zhang, J. Han, and G. Ding, “Scaling up your kernels to

31x31: Revisiting large kernel design in CNNs,” in Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit., Jun. 2022, pp. 11963–11975. [31] O. Ronneberger, P. Fischer, and T. Brox, “U-Net: Convolutional net-

Her research interests include drone remote sens- ing and agricultural vision.

works for biomedical image segmentation,” in Proc. 18th Int. Conf. Med. Image Comput. Comput.-Assist. Intervent., vol. 9351. Cham, Switzer- land: Springer, 2015, pp. 234–241. [32] M.-H. Guo, C.-Z. Lu, Q. Hou, Z. Liu, M. Cheng, and S. Hu, “SegNeXt:

Rethinking convolutional attention design for semantic segmentation,” in Proc. Adv. Neural Inf. Process. Syst., 2022, pp. 1140–1156. [33] E. Celikkan, T. Kunzmann, Y. Yeskaliyev, S. Itzerott, N. Klein, and

M. Herold, “WeedsGalore: A multispectral and multitemporal UAV- based dataset for crop and weed segmentation in agricultural maize ﬁelds,” in Proc. IEEE/CVF Winter Conf. Appl. Comput. Vis. (WACV), Feb. 2025, pp. 4767–4777. [34] A. Paszke et al., “PyTorch: An imperative style, high-performance deep

learning library,” in Proc. Adv. Neural Inf. Process. Syst., vol. 32, 2019, pp. 8026–8037. [35] D. P. Kingma and J. Ba, “Adam: A method for stochastic optimization,”

Zhen Yang received the B.E. degree from the Department of Automation, Beijing Forestry Univer- sity, Beijing, China, in 2010, and the Ph.D. degree in radio physics from the School of Information Sci- ence and Engineering, Lanzhou University, Lanzhou, Gansu, China, in 2019.

2014, arXiv:1412.6980. [36] E. Romera, J. M. Alvarez, L. M. Bergasa, and R. Arroyo, “ERFNet: Eﬃ-

cient residual factorized ConvNet for real-time semantic segmentation,” IEEE Trans. Intell. Transp. Syst., vol. 19, no. 1, pp. 263–272, Jan. 2018. [37] L.-C. Chen, Y. Zhu, G. Papandreou, F. Schroﬀ, and H. Adam,

“Encoder–decoder with Atrous separable convolution for semantic image segmentation,” in Proc. Eur. Conf. Comput. Vis. (ECCV), 2018, pp. 801–818. [38] E. Xie et al., “SegFormer: Simple and eﬃcient design for semantic

He is an Associate Professor with the School of Information Science and Engineering, Lanzhou University. His research interests include nonlinear circuits, random number generators, cognitive visual processing, and compressive sensing.

segmentation with transformers,” in Proc. Adv. Neural Inf. Process. Sys. (NIPS), vol. 34, Dec. 2021, pp. 12077–12090. [39] H. Cai, J. Li, M. Hu, C. Gan, and S. Han, “EﬃcientViT: Lightweight

multi-scale attention for high-resolution dense prediction,” in Proc. IEEE/CVF Int. Conf. Comput. Vis., Oct. 2023, pp. 17302–17313. [40] X. Li et al., “Transformer-based visual segmentation: A survey,” IEEE

Trans. Pattern Anal. Mach. Intell., vol. 46, no. 12, pp. 10138–10163, Dec. 2024. [41] K. Jiang, U. Afzaal, and J. Lee, “Transformer-based weed segmentation

for grass management,” Sensors, vol. 23, no. 1, p. 65, Dec. 2022. [42] K. Hu, G. Coleman, S. Zeng, Z. Wang, and M. Walsh, “Graph weeds net:

A graph-based deep learning method for weed recognition,” Comput. Electron. Agricult., vol. 174, Jul. 2020, Art. no. 105520. [43] A. S. M. M. Hasan, D. Diepeveen, H. Laga, M. G. K. Jones, and

F. Sohel, “Image patch-based deep learning approach for crop and weed recognition,” Ecol. Informat., vol. 78, Dec. 2023, Art. no. 102361. [44] A. Buslaev, V. I. Iglovikov, E. Khvedchenya, A. Parinov, M. Druzhinin,

Fengyuan Ren received the B.A. and M.Sc. degrees in automatic control and the Ph.D. degree in computer science from Northwestern Polytechnic University, Xi’an, China, in 1993, 1996, and 1999, respectively.

and A. A. Kalinin, “Albumentations: Fast and ﬂexible image augmentations,” Information, vol. 11, no. 2, p. 125, Feb. 2020. [45] T. B. Shahi, S. Dahal, C. Sitaula, A. Neupane, and W. Guo, “Deep

learning-based weed detection using UAV images: A comparative study,” Drones, vol. 7, no. 10, p. 624, Oct. 2023. [46] V. Badrinarayanan, A. Kendall, and R. Cipolla, “SegNet: A deep

He is a Professor with the Department of Com- puter Science and Technology, Tsinghua University, Beijing, China. From 2000 to 2001, he worked at the Electronic Engineering Department, Tsinghua University as a Post-Doctoral Researcher. In Jan- uary 2002, he moved to the Computer Science and Technology Department, Tsinghua University. He co-authored more than 80 international journal and conference papers. His research interests include network traﬃc management and control, control in/over computer networks, wireless networks, and wireless sensor networks.

convolutional encoder–decoder architecture for image segmentation,” IEEE Trans. Pattern Anal. Mach. Intell., vol. 39, no. 12, pp. 2481–2495, Dec. 2017. [47] G. Huang, Z. Liu, L. Van Der Maaten, and K. Q. Weinberger, “Densely

connected convolutional networks,” in Proc. IEEE Conf. Comput. Vis. Pattern Recognit., Jun. 2017, pp. 4700–4708. [48] M. Tan and Q. Le, “EﬃcientNet: Rethinking model scaling for con-

volutional neural networks,” in Proc. Int. Conf. Mach. Learn., 2019, pp. 6105–6114.

Dr. Ren has served as a technical program committee member and local arrangement chair for various IEEE and ACM international conferences.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:31 UTC from IEEE Xplore.  Restrictions apply.
